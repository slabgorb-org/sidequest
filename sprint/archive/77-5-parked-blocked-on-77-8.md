---
story_id: "77-5"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 77-5: Quest/objective panel — render quest_log + quest_anchors + active_stakes (quests payload)

## Story Details
- **ID:** 77-5
- **Title:** Quest/objective panel — render quest_log + quest_anchors + active_stakes (quests payload)
- **Points:** 5
- **Jira Key:** (none — Jira not enabled)
- **Workflow:** tdd
- **Stack Parent:** none
- **Repos:** ui (sidequest-ui)

## Context
This is the UI fast-follow for ADR-137 (quest & stakes substrate). Design story 77-1 is DONE: engine now seeds quest_anchor + quest_log + active_stakes at character creation from PC drive/calling, via typed record_quest/set_stakes narrator tools (Option C). quest_anchors is a first-class WorldStatePatch field with a live consumer at orbital/course.py:157.

This story renders the player-facing panel showing the "quests" payload: quest_log + quest_anchors + active_stakes.

**Audience driver:** Sebastien & Jade are mechanics-first players who want mechanical resolution legible in PLAYER-FACING surfaces (this is a player-UI concern, NOT a dev/OTEL/GM-panel concern). The quest/objective panel is exactly that surface.

**Repo guidance:** sidequest-ui (React/TypeScript, Vite). Relevant areas: src/components/ (panels like PartyPanel), src/providers/GameState, src/types/ (WebSocket payload TS defs), useStateMirror / state reconciliation (ADR-133 full-replay mirror).

The state payload reaches the client via the reactive state mirror; the dev/tea will need to confirm the server emits quest_log/quest_anchors/active_stakes in the state snapshot and add the TS types + panel component + tests. Per CLAUDE.md "Verify Wiring, Not Just Existence": include an integration/wiring test proving the panel is mounted and reads live state, not just a unit test of the component in isolation.

## Workflow Tracking
**Workflow:** tdd
**Phase:** red
**Phase Started:** 2026-06-04T13:01:32Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-04T00:00:00Z | 2026-06-04T13:01:32Z | 13h 1m |
| red | 2026-06-04T13:01:32Z | - | - |

## Sm Assessment

Setup complete. Story 77-5 is the UI fast-follow for ADR-137 — render the quests payload (quest_log + quest_anchors + active_stakes) as a player-facing panel. The engine side (77-1) is DONE and seeds these at character creation, so the work here is purely client-side: TS types + panel component + state-mirror wiring.

**Scope for TEA (RED phase):**
- Confirm the server actually emits `quest_log` / `quest_anchors` / `active_stakes` in the reactive state snapshot before writing tests against the shape. If the payload isn't reaching the client, that's a Delivery Finding (Gap, blocking) — flag it, don't paper over it. (No Silent Fallbacks.)
- Write failing tests for the panel component rendering each of the three sub-payloads.
- **Mandatory wiring test:** per CLAUDE.md "Every Test Suite Needs a Wiring Test", include an integration test proving the panel is actually mounted in the live UI tree and reads from the state mirror (ADR-133 full-replay), not just a unit test of the component in isolation.

**Audience anchor:** Sebastien & Jade (mechanics-first) want the math legible in the *player* UI — this panel is that surface. Keep it player-facing; this is NOT a GM-panel/OTEL concern.

**Repo:** sidequest-ui only. Branch `feat/77-5-quest-objective-panel` on base `develop` (subrepo convention). No server changes expected — if one becomes necessary, that's a finding, since 77-1 claimed the payload already flows.

Routing to Amos (TEA) for the RED phase.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (blocking): The rich `quests` projection (quest_log + quest_anchors + active_stakes) that this story renders **does not reach the client**. The three fields are stored server-side and populated by 77-1's `seed_quest_spine()` and 77-2's `record_quest`/`set_stakes` tools, but they are **never serialized outbound**. `_shared_world_delta_to_state_delta()` projects only location/encounter_id/party_formation/magic_state. The legacy `StateDelta.quests` field is a `dict[str, str]` title→status map that is never even populated (and `test_wire_parity.py:75-78` asserts it is omitted from the wire when empty). UI side confirms: `quests?: Record<string, string>` (`sidequest-ui/src/types/payloads.ts:46`) — no `QuestsPayload`, no `quest_anchors`, no `active_stakes`, no `QUESTS` message type. Affects `sidequest-server/sidequest/server/session_state.py:63-99` (the projection must add quest_log/quest_anchors/active_stakes, analogous to the `relationships_emit.py` RELATIONSHIPS snapshot) **plus** a new typed UI payload in `sidequest-ui/src/types/payloads.ts`. **77-5 as scoped (repos: ui, render-only) is BLOCKED on a server projection story that does not exist in the backlog.** Per the story context Technical Guardrails, the shape must NOT be fabricated into the thin `Record<string,string>`. *Found by TEA during test design.*

## TEA Assessment

**Phase:** red
**Tests Required:** No — **STORY BLOCKED before test design.**
**Reason:** 77-5 is a render-only consumer (`repos: ui`) of a rich `quests` projection (quest_log + quest_anchors + active_stakes) that **does not reach the client**. The story context's "Projection-shape dependency (resolve before RED)" gate fired NEGATIVE. Writing RED tests would require fabricating the payload shape, which the Technical Guardrails explicitly forbid ("do not back-fill a fake shape into the thin `Record<string, string>`") and which violates No Silent Fallbacks.

**Investigation (TEA, RED):**
- Server: `quest_log` (rich `QuestEntry`), `quest_anchors`, `active_stakes` are stored (`game/session.py:790,861,867`), populated by 77-1 `seed_quest_spine()` (`game/quest_seed.py:36-89`) and mutated by 77-2 `record_quest`/`set_stakes` — but **never serialized outbound**. `_shared_world_delta_to_state_delta()` (`server/session_state.py:63-99`) projects only location/encounter_id/party_formation/magic_state. The legacy `StateDelta.quests: dict[str,str]` is never populated (`test_wire_parity.py:75-78` asserts it's omitted when empty).
- UI: `quests?: Record<string, string>` (`sidequest-ui/src/types/payloads.ts:46`) — legacy title→status only. No `QuestsPayload`, no `quest_anchors`/`active_stakes`, no `QUESTS` message type. The ADR-136 `RelationshipsPayload`/`RELATIONSHIPS` pattern this story must mirror is absent for quests.
- Backlog: 77-1…77-4 all DONE, but **none** shipped the client projection (the RELATIONSHIPS-snapshot analog). The outbound projection fell through the gap between "server maintains the spine" and "UI renders the spine."

**Decision (Bossmang, 2026-06-04):** Re-sequence — **add a server projection story first** (emit a rich quests projection mirroring the ADR-136 `relationships_emit.py` RELATIONSHIPS snapshot: a dedicated `QUESTS` message + `QuestsPayload`, or an enriched snapshot). Land + verify it, THEN 77-5 UI consumes it. 77-5 stays render-only per its guardrail; honors ADR-137's "server lands + OTEL-verified before the panel consumes" fast-follow sequencing.

**Status:** BLOCKED — no failing tests produced. **Handoff: back to SM (Camina Drummer)** to (1) park 77-5 (blocked on the new server story), (2) create the new `repos: server` quests-projection story in epic 77, (3) set it up. NOT handing to Dev.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec. The spec's "Projection-shape dependency (resolve before RED)" gate was honored exactly: the dependency was checked first, found absent, and surfaced as a blocking finding rather than fabricating the shape. No test design occurred.