# Story 165-2 Context

## Title
Positions as combat state + WN SRD movement/reach/range facts on the binding (plan tasks 4–5)

## Metadata
- **Story ID:** 165-2
- **Type:** story
- **Points:** 3
- **Priority:** p1
- **Workflow:** superpowers → run as **spdd** (settled Keith decision, `sm-decisions.md`)
- **Repo:** server
- **Epic:** Mapping Track C — tactical mechanics (ADR-096 v2)

## Problem
Plan tasks 4–5 of `docs/superpowers/plans/2026-07-08-mapping-track-c-tactical-mechanics.md`:
seat durable per-actor cell positions in `EncounterActor.per_actor_state['cell']` (additive,
no new field), and author the WN SRD movement/reach/range facts **once** on
`WithoutNumberRulesetModule` (SRD-sourced, not re-derived per world — the flat-13 bug class).

## Technical Approach
_Approach hints to be refined by TEA/Dev per the plan. These facts (cell scale, per-actor
movement budget in cells, melee reach, ranged range) are the inputs the C1 library
(`sidequest/game/tactical/adjudication.py`) already consumes — `cells_reachable(budget=…)`,
`reach_cells(reach=…)`, `adjudicate_reach(max_cells=…)`._

## Scope
- In scope: the behavior described by the story title (plan tasks 4–5).
- Out of scope: enforcement wiring at `dispatch_dice_throw` (165-3), protocol/UI (165-4),
  Fate zones (165-5).

## Acceptance Criteria
_TEA to define during the RED phase from plan tasks 4–5._

## Carryover from 165-1 (C1 library — read before starting)
Full detail: `sprint/archive/165-1-session.md` + `context-epic-165.md` §Carryover + the
tea/dev/reviewer `*-gotchas.md` (tagged 165-1).
- **`ReachResult.cost` is a SUPERSET of `.reachable`** (includes origin at 0 + the immediate
  over-budget boundary). When consuming the flood, read `.reachable` for stoppable cells,
  never `cost.keys()`.
- **The plan doc's embedded code has bugs** (a mask mislabel + a `cells_reachable` cost gap,
  both fixed in 165-1's code but still in the doc). Hand-verify every mask/impl against its
  own test before transcribing tasks 4–5.
- **Difficult-terrain is charged on ENTERING a cell** (`cells_reachable`/`movement_cost` both
  do `2 if dest in difficult else 1`) — keep WN "difficult terrain" facts consistent with that.
- When you touch the library, consider closing the 165-1 coverage gap on
  `movement_cost(difficult=…)` (untested; independent impl from the flood's).
