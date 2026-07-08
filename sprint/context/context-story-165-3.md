# Story 165-3 Context

## Title
Enforcement wiring: turn_telemetry spans, dispatch_dice_throw reach/range gate, seat positions (plan tasks 6–8)

## Metadata
- **Story ID:** 165-3
- **Type:** story
- **Points:** 5
- **Priority:** p1
- **Workflow:** superpowers → run as **spdd** (settled Keith decision, `sm-decisions.md`)
- **Repo:** server
- **Epic:** Mapping Track C — tactical mechanics (ADR-096 v2)

## Problem
Plan tasks 6–8: emit tactical OTEL spans that reach `turn_telemetry` via `publish_event`,
wire the reach/range gate into the confrontation-resolution chokepoint `dispatch_dice_throw`
(calling the C1 library from the WN binding), and seat per-actor positions at encounter
instantiation.

## Technical Approach
_TEA/Dev refine per the plan. This is the story that **binds C1 into production** — the WN
ruleset module imports `sidequest.game.tactical.adjudication` and calls `adjudicate_reach`
(and movement checks) from `dispatch_dice_throw`. Enforcement lives in the BINDING, not
native combat code (ADR-117/143)._

## Scope
- In scope: enforcement wiring (plan tasks 6–8) — spans, the dispatch gate, seat positions.
- Out of scope: protocol echoes/UI (165-4), Fate zones (165-5).

## Acceptance Criteria
_TEA to define during the RED phase from plan tasks 6–8._

## Carryover from 165-1 (C1 library — read before starting)
Full detail: `sprint/archive/165-1-session.md` + `context-epic-165.md` §Carryover + the
tea/dev/reviewer `*-gotchas.md` (tagged 165-1).
- **THIS STORY OWNS C1's WIRING TEST.** Plan Global Constraint line 18: "C1's wiring test
  lives in the C2 enforcement task." An AC MUST be an **integration/wiring test that reaches
  `game.tactical` from a real `dispatch_dice_throw` path** (fixture-driven behavior or OTEL-span,
  per CLAUDE.md "No Source-Text Wiring Tests") — not just more unit tests on `adjudication.py`.
- **Tighten `adjudicate_reach(mode: str)` to `Literal["melee","ranged"]`** (or validate + fail
  loud) as you wire it — it is currently unvalidated (unknown mode → silent "range" noun; a
  mild No-Silent-Fallbacks tension flagged by the 165-1 reviewer).
- **No-grid = no-grid rules:** the gate fires only when both actors carry
  `per_actor_state['cell']`; otherwise resolve as today and emit `tactical.enforcement.skipped`
  (reason `no_grid`). Scope boundary, NOT a silent fallback.
- **New spans must call `publish_event`** (reach `turn_telemetry`, not just Jaeger) and need a
  `SPAN_ROUTES`/`FLAT_ONLY_SPANS` entry or `tests/telemetry/test_routing_completeness.py` fails.
- **Close the 165-1 coverage gaps** as you consume the library: `movement_cost(difficult=…)`,
  `line_of_sight` endpoint-exclusion, `aoe_burst(require_los=False)` are all untested.
- **`ReachResult.cost` is a superset of `.reachable`** — gate on `.reachable`/the adjudication
  verdict, not `cost.keys()`.
- **Plan doc has bugs** in its embedded code — hand-verify before transcribing tasks 6–8.
