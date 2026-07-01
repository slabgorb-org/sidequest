# Story 161-1 Context

## Title
DESIGN/ADR: ingestion path for companion-seat brain telemetry into the SideQuest
Inspector.

## Metadata
- **Story ID:** 161-1
- **Type:** design / ADR
- **Points:** 3
- **Priority:** p2
- **Workflow:** spdd
- **Repos:** server, understudy, ui
- **Epic:** 161 — Companion-seat brain telemetry surfaces in the SideQuest Inspector

## Problem

Long-running companion NPCs that travel with the party — **pets, henchmen (peer),
hirelings** (the `seat_core` `Role` enum: `PET` / `PEER` / `HIRELING`,
`seat_core/persona/axis.py:26`) — are driven by the understudy `seat_core` brain,
one LLM decision per turn (`claude_p` / `anthropic` / `ollama`). That brain work
is **invisible to SideQuest today**:

- `claude_p_model.py:60` parses only `envelope["result"]` and **discards the rest
  of the `claude -p` JSON envelope** — including `usage` (real tokens) and
  `total_cost_usd` — then hardcodes `input_tokens=0, output_tokens=0`.
- The companion run loop (`companion/run.py`) wraps `decide()` in a 30s timeout but
  records **no duration, no outcome, no span**.
- The only related telemetry is the native Claude Code OTEL the `claude -p`
  subprocess *might* emit — but nothing in SideQuest/understudy code configures it.

Goal: surface per-decision brain telemetry (duration, model, tokens, cost,
YIELD-vs-act outcome) for the **whole entourage**, keyed by session slug + seat +
role, in a dedicated new **Inspector** tab — the same lie-detector visibility the
GM panel gives for the server narrator. Found during epic-160 dogfood (2026-06-27,
MP `beneath_sunden`, owl Tolliver).

## Decision — Approach C (understudy self-reports via the existing bridge)

Each process reports its **own** decisions in-band. The companion run loop measures
the decision where all the semantic data already lives and POSTs one event to the
server's **existing** `/internal/watcher/emit` bridge (`app.py:313`, ADR-131 — the
door the daemon already uses via `watcher_bridge.py`). The event rides
`WatcherHub → /ws/watcher → Inspector` and persists to `turn_telemetry`.

### Rejected alternatives
- **A — read the native `claude -p` :55801 OTEL.** That collector is **BikeRack's**
  (`pf.frame.app`), populated only if the dev harness set an ambient
  `CLAUDE_CODE_ENABLE_TELEMETRY` — a silent-fallback trap (works on one box, dead
  elsewhere). And native subprocess spans **cannot carry** session slug, seat, role,
  or YIELD-vs-act — those are SideQuest concepts that only exist at the understudy
  decision boundary.
- **B — new SideQuest OTLP receiver.** New infrastructure (none exists) to catch the
  same unattributable spans. Fails reuse-first.

### Why the "coordinate two `claude -p` processes" problem dissolves
The coordination problem is an artifact of the shared-collector read: the server's
`claude -p` spans and the companion's `claude -p` spans land in one bucket and must
be demuxed by resource attributes. Delete the shared-collector read (A/B) and there
is nothing to coordinate — the server already self-reports via `publish_event`, and
understudy self-reports via the bridge. Two producers, one hub, no demux.

## Architecture & data flow

```
COMPANION SEAT TURN  (understudy process)
  companion/run.py
    t0 = perf_counter()
    result = await decide(brain, ...)        # seat_core brain (pet/peer/hireling)
    duration_ms = perf_counter() - t0        # ENRICHED DecideResult: value+model+tokens+cost
    outcome = result.value.kind              # ACT/ASIDE/ROLL/BEAT/DEFEND/YIELD
    emit_seat_decision(session_slug=defn.game_slug, seat=defn.name,
                       role=defn.role, species=defn.species,
                       duration_ms, model, tokens, cost, outcome, degraded)
         │  HTTP POST  (fire-and-forget, fail-loud-non-fatal)
         ▼
SERVER  POST /internal/watcher/emit           # EXISTING bridge + session_slug passthrough
    publish_event(event_type="companion_brain_decide",
                  component="companion_brain", session_slug=..., fields=...)
         ├─► WatcherHub → /ws/watcher ──► Inspector (live)
         └─► turn_telemetry (Postgres)
UI  useLiveSource routes "companion_brain_decide" ──► new Companions tab
```

Three deliberate boundaries, each testable in isolation:
1. **`seat_core` brain layer** — grows by one job: return a `DecideResult` carrying
   `model`, real `tokens`, `cost` (stop discarding the `claude -p` envelope). Stays
   session-agnostic — pure.
2. **companion run loop** — owns the context (`game_slug`, `name`, `role`, `species`)
   and timing/outcome; assembles the record. We do **not** thread session into
   `decide()` (avoids a protocol change).
3. **understudy→server bridge module** — thin emitter mirroring `watcher_bridge.py`:
   stdlib POST, 2s timeout, failures logged WARNING and swallowed *for the turn only*.

## `companion.brain.decide` taxonomy

Standard `WatcherEvent` envelope (no new plumbing):
`{ timestamp, component:"companion_brain", event_type:"companion_brain_decide",
severity:"info|warning", session_slug, fields }`

`fields`:
- **Who:** `seat`, `role` (pet|peer|hireling), `species`, `owner` (companion_of), `round`
- **Decision:** `outcome` (act|yield), `intent_kind` (ACT|ASIDE|ROLL|BEAT|DEFEND|YIELD),
  `degraded`, `timed_out`
- **Cost:** `backend` (claude_p|anthropic|ollama), `model`, `duration_ms`,
  `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_creation_tokens`, `cost_usd`

Honesty notes:
- `cost_usd` is **backend-honest, not uniform**: `claude_p` reports the envelope's
  `total_cost_usd` as a **notional plan-equivalent** (subscription-billed, not a real
  API charge); `anthropic` is a real metered charge. The tab labels the difference.
- `degraded` / `timed_out` are first-class — a pet whose brain times out and silently
  yields every turn is exactly what this tab exists to catch (emits as `warning`).
- `fields` is `Record<string, unknown>` — adding a field later needs no migration.

## Attribution & the server passthrough (the only server change)

Today `/internal/watcher/emit` forwards `{event_type, fields, component}` and
`publish_event` resolves `session_slug` from a **per-connection ContextVar** bound at
the `/ws` handshake. An HTTP POST has no bound slug → events land **session-less
(global)** and would show in every Inspector view. Fix:

```python
class WatcherEmitPayload(BaseModel):
    event_type: str
    fields: dict[str, Any]
    component: str
    session_slug: str | None = None    # NEW — explicit cross-process attribution
    severity: str = "info"             # NEW — mark degraded decisions

def publish_event(..., session_slug: str | None = None, severity: str = "info"):
    slug = session_slug if session_slug is not None else current_session_slug()
```

- Backward-compatible (`None` default preserves ContextVar behavior for all
  in-process callers and the daemon).
- Explicit beats implicit — an out-of-process emitter states its session; no silent
  fallback to "global."
- Slug source: `defn.game_slug` (`companion/manifest.py:31`).
- **Persistence corner (flag for 161-2):** `publish_event` persists out-of-frame
  events to `turn_telemetry`, which FKs `sessions` by slug. The companion is in a
  live session, so the row exists — but an emit for an **unknown** slug must fail
  loud / skip loud (WARNING), never a silent drop.

## New-tab contract (CORRECTED)

Inspector/Dashboard tabs are **not** `widgetRegistry` / `MobileTabView` (those are the
game-board player tabs — Character/Inventory/Map). They live at a numeric `activeTab`
index across three spots:

- `DashboardTabs.tsx` — add the "Companions" tab label.
- `DashboardApp.tsx` (:140–178) — `{ live.activeTab === 9 && <CompanionsTab decisions={view.companionDecisions} /> }`.
- `useLiveSource.ts` — reducer routes `companion_brain_decide` → `view.companionDecisions`, session-scoped via `inActiveSession()` like every other tab.
- `tabs/CompanionsTab.tsx` — NEW component: group by seat (role/species), per turn
  show duration · model · tokens/cost (plan-equivalent labeled) · outcome · degraded.

## Refined 161 breakdown

- **161-1** (this) — DESIGN/ADR + refined breakdown.
- **161-2 — Produce** (server + understudy): (a) `seat_core` `DecideResult`
  enrichment incl. parsing the `claude -p` envelope usage/cost; (b) companion
  run-loop timing/outcome + emit via new bridge module; (c) server session_slug +
  severity passthrough. Wiring test: fake-brain decision → event on the hub with
  correct slug + seat + role.
- **161-3 — Render** (ui): Companions Inspector tab on the corrected Dashboard
  surface (DashboardTabs + DashboardApp + useLiveSource + CompanionsTab).

161-2 owns the emit path end-to-end so "produce" is atomically testable; 161-3 renders
against the frozen taxonomy and can be built in parallel once 161-2 fixes the shape.

## Scope
- **In scope:** all understudy companion seats (role pet/peer/hireling); the
  end-to-end path emitter → bridge → hub → Inspector tab.
- **Out of scope:** the naive-player playtest bots (different purpose; may share
  `seat_core` after story 159-2 and light up for free, but not a goal); reading the
  native `claude -p` OTEL; any new OTLP receiver.

## Acceptance Criteria
1. Ingestion path resolved: Approach C; A and B rejected with rationale.
2. `companion_brain_decide` taxonomy defined (envelope + fields).
3. Attribution defined via the `session_slug`/`severity` passthrough contract.
4. New-tab contract defined and corrected to the Inspector/Dashboard surface.
5. 161 breakdown refined (161-2 Produce, 161-3 Render).
6. Scope generalized from the owl-pet example to all companion roles.

---
_Design captured by 161-1 brainstorm (Architect), 2026-07-01._
