---
id: 154
title: "Companion-Seat Brain Telemetry Ingestion — Understudy Self-Reports via the Watcher Bridge, Not the Native claude -p Collector"
status: accepted
date: 2026-07-01
deciders: ["Keith Avery", "Naomi Nagata (Architect)"]
supersedes: []
superseded-by: null
related: [131, 132, 90, 103, 31, 124, 105]
tags: [observability, transport-infrastructure]
implementation-status: deferred
implementation-pointer: null
---

# ADR-154: Companion-Seat Brain Telemetry Ingestion — Understudy Self-Reports via the Watcher Bridge, Not the Native claude -p Collector

## Context

The companion-seat framework (`sidequest-understudy/src/companion/`, driven by the
shared `seat_core` brain) runs the party's long-running NPC **entourage** — pets,
henchmen (peer), hirelings; the `seat_core` `Role` enum is `PET` / `PEER` /
`HIRELING` (`seat_core/persona/axis.py:26`). Each seat makes **one LLM decision per
turn** (`claude_p` / `anthropic` / `ollama`).

That brain work is **invisible to SideQuest**. The GM panel / Inspector shows the
server narrator's every mechanical decision (ADR-031 / ADR-090 / ADR-103), but for a
companion brain it shows nothing:

- `claude_p_model.py:60` parses only `envelope["result"]` and **discards the rest of
  the `claude -p` JSON envelope** — including `usage` (real tokens) and
  `total_cost_usd` — then hardcodes `input_tokens=0, output_tokens=0`.
- The companion run loop (`companion/run.py`) wraps `decide()` in a 30 s timeout but
  records **no duration, no outcome, no span**.

Per the OTEL Observability Principle, an unobserved subsystem is one you cannot tell
is *engaged* versus *improvising*. A pet whose brain silently times out and yields
every turn is exactly the failure this is meant to catch. Trigger: epic-160 dogfood,
owl Tolliver in MP `beneath_sunden` (2026-06-27) — a companion making Sonnet calls
with zero visibility into duration, cost, or YIELD-vs-act outcome.

Epic 161 framed the question as an **ingestion path** with three candidates: (A) read
the native `claude -p` OTEL at `:55801`; (B) stand up a SideQuest OTLP receiver; (C)
have understudy emit to the server's WatcherHub. Design (this ADR) uncovered four
facts that decide it:

1. **`:55801` is not SideQuest's.** It is the BikeRack collector (`pf.frame.app`),
   populated only when the ambient dev harness sets `CLAUDE_CODE_ENABLE_TELEMETRY`.
   Nothing in SideQuest or understudy code configures it — depending on it is a
   No-Silent-Fallbacks violation (works on one box, dead everywhere else).
2. **Native subprocess spans cannot carry the semantics we need.** Session slug,
   seat, role, and YIELD-vs-act are SideQuest concepts decided *at the understudy
   boundary*, around the subprocess — the native `claude -p` span measures an
   invocation and knows none of them. The data is unattributable by construction.
3. **The ingestion seam already exists.** The server exposes
   `POST /internal/watcher/emit` (`app.py:313`, ADR-131) — a cross-process bridge the
   daemon already uses (`watcher_bridge.py`) to inject watcher events. Understudy is
   also a separate process; it can reuse the same door.
4. **`claude -p` already returns real tokens and cost** in its JSON envelope. The
   backend just throws them away. No collector is needed to recover them.

The "how do we coordinate the two `claude -p` processes?" problem — the server's
`claude -p` jobs and the companion's `claude -p` both emitting to one native
collector, forcing a demux of whose-span-is-whose — is an **artifact of the
shared-read approach (A/B)**, not an inherent problem.

## Decision

**Companion-seat brain telemetry is produced at the understudy decision boundary and
self-reported to the server's existing watcher bridge. We do not read the native
`claude -p` collector and do not stand up an OTLP receiver.**

Each process reports its *own* decisions in-band. There is nothing to coordinate or
demux; the semantic fields live where we measure; and the ingestion path already
exists, so the server footprint is a small, backward-compatible contract extension.

Concretely, across three boundaries (each independently testable):

1. **`seat_core` brain layer** enriches `DecideResult` with `model`, real `tokens`,
   and `cost` — including parsing the `claude -p` envelope's `usage` /
   `total_cost_usd`. It stays session-agnostic.
2. **companion run loop** owns the context (`game_slug`, seat `name`, `role`,
   `species`) and the timing/outcome. It times the `decide()` await, derives
   `outcome` (YIELD vs act) and `degraded`/`timed_out`, assembles a
   `companion_brain_decide` record, and hands it to a thin emitter that POSTs to
   `/internal/watcher/emit` (fire-and-forget, fail-loud-non-fatal, mirroring
   `watcher_bridge.py`). Session is **not** threaded into `decide()`.
3. **server** forwards it through `publish_event` → WatcherHub → `/ws/watcher`
   (Inspector) and `turn_telemetry`, via a `session_slug` + `severity` passthrough
   added to `/internal/watcher/emit` and `publish_event`.
4. **UI** renders it in a new Inspector/Dashboard tab.

## Contracts / Invariants

### The `companion_brain_decide` event

Standard `WatcherEvent` envelope (ADR-132), no new plumbing:
`component = "companion_brain"`, `event_type = "companion_brain_decide"`,
`severity ∈ {info, warning}`, plus `session_slug` and `fields`:

- **Who:** `seat`, `role` (pet|peer|hireling), `species`, `owner`, `round`
- **Decision:** `outcome` (act|yield), `intent_kind`
  (ACT|ASIDE|ROLL|BEAT|DEFEND|YIELD), `degraded`, `timed_out`
- **Cost:** `backend`, `model`, `duration_ms`, `input_tokens`, `output_tokens`,
  `cache_read_tokens`, `cache_creation_tokens`, `cost_usd`

`fields` is `Record<string, unknown>` — later additions need no migration.

### The `session_slug` / `severity` passthrough (the one shared-contract change)

`WatcherEmitPayload` gains optional `session_slug: str | None = None` and
`severity: str = "info"`; `publish_event` gains an explicit `session_slug` override
that beats the per-connection ContextVar (`current_session_slug()`). Default `None`
preserves today's behavior for every in-process caller and the daemon bridge —
strictly additive.

### Invariants

- **Attribution:** a companion event MUST carry an explicit `session_slug` (source:
  `defn.game_slug`). An out-of-process emit without one resolves session-less/global;
  companion telemetry must never rely on that — the emitter always sets it. No silent
  globalization.
- **Liveness of degradation:** a timed-out or errored decision still emits, with
  `degraded=true` / `severity="warning"`. Silence is not an acceptable telemetry
  state for a lie-detector.
- **Non-fatal telemetry:** an emit failure is logged at WARNING and never breaks a
  companion's turn. Loud, not swallowed; visible, not fatal.
- **Cost honesty:** `cost_usd` is backend-honest, not uniform. `claude_p` reports a
  **notional plan-equivalent** (subscription-billed), `anthropic` a real metered
  charge. The render surface labels the difference so plan-equivalent cost is never
  double-counted against the Console bill.

### Perception firewall (ADR-105) note

A pet's perception scope is `owner_private`. That firewall governs **player-facing
perception** — what the seat's brain is *fed*. Brain telemetry is **dev-side
observation** (the GM/dev lie-detector), not player-visible content, so it does not
cross and is not governed by the perception firewall. The two must not be conflated.

## Observability

This ADR *is* an observability decision, so its own verification bar is explicit: the
new Inspector Companions tab is the verification surface, and — per the OTEL principle
— the fix is only real if the span fires. The wiring test drives a fake-brain
companion decision and asserts a `companion_brain_decide` event reaches WatcherHub
with the correct `session_slug` + seat + role (behavior/OTEL assertion, never a
source-text grep).

## Consequences

### Positive
- The "coordinate two `claude -p` processes" problem **dissolves** — each process
  self-reports; nothing shared to demux.
- **Reuse-first:** one existing endpoint (ADR-131) + a tiny additive contract change;
  no OTLP receiver, no BikeRack dependency, no ambient-env fragility.
- Real tokens/cost are **recovered from data already in hand** (the discarded
  `claude -p` envelope).
- **Generalizes for free** to every companion role, and — once story 159-2
  consolidates the naive-player bots onto `seat_core` — lights those up too.

### Negative
- A three-repo change (understudy emit, server passthrough, UI tab).
- A change to `publish_event`, a shared contract every subsystem touches — mitigated
  by the optional, default-`None`, backward-compatible signature.
- `claude_p` cost is plan-equivalent, not metered — must be labeled to avoid
  double-counting.

### Neutral
- Understudy stays an observer but becomes an **active reporter of its own decisions**
  in addition to its existing post-run Jaeger pull (`report/spans.py`).

## Alternatives considered

- **A — read the native `claude -p` :55801 OTEL.** Rejected: the collector is
  BikeRack-ambient (silent-fallback trap), the spans are unattributable to
  session/seat/role/outcome, and it forces the two-process demux.
- **B — new SideQuest OTLP receiver.** Rejected: brand-new ingestion infrastructure
  to catch the same unattributable spans. Fails reuse-first (ADR-131 already
  provides the seam).

## Reconciliation with ADR-131 / ADR-132 / ADR-103

- **ADR-131** (daemon↔server bridge): this is a **third producer** on the same
  `/internal/watcher/emit` seam (after in-process `publish_event` and the daemon).
  The `session_slug` extension is additive and leaves the daemon's calls unchanged.
- **ADR-132** (WatcherHub): companion events flow through the same singleton and
  per-session replay buffers; the explicit `session_slug` override is the
  cross-process analog of the ContextVar binding done at the `/ws` handshake.
- **ADR-103** (native OTEL via tool registry): we deliberately do **not** extend
  native OTEL passthrough to the companion. The native `claude -p` spans stay out of
  the Inspector because they cannot be attributed. This ADR is the
  "don't read the native collector" counterpart to 103.

## Implementation

Scheduled as epic 161: **161-2 (Produce)** — `seat_core` enrichment + companion
run-loop emit + server passthrough; **161-3 (Render)** — the corrected Inspector tab.
Full breakdown and per-story ACs: `sprint/context/context-story-161-1.md`. Flip this
ADR's `implementation-status` from `deferred` to `live` when 161-2 and 161-3 land.
