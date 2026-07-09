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

## Carryover from 165-2 (BLOCKING findings — the facts you're about to wire are inert landmines)
Full detail: `sprint/archive/165-2-session.md` §Delivery Findings (`### Reviewer (code review)`) + the
reviewer/tea/dev `*-gotchas.md` (tagged 165-2). 165-2 shipped the WN tactical facts + adjudicators
**inert** (zero production callers). This story wires them — and three of them are broken the moment
you do. Resolve each BEFORE the dispatch gate calls the method, or ranged combat ships silently wrong.

- **BLOCKER 1 — `RANGE_BAND_CELLS` keys match NOTHING in real content.** The table is keyed on
  categorical bands (`rifle`/`pistol`/`thrown`/…), but `range_band` exists ONLY on `CatalogItem`
  (`sidequest/genre/models/inventory.py:214`) and every pack authors it as an `"N/N"` numeric string
  (`"10/100"`, `"100/600"` — 16 distinct values). There is **no `DamageSpec.range_band`** at all.
  So `weapon_range_cells(real_spec)` either returns melee (spec lacks the attr → `getattr`→None) or
  the rifle 40-cell cap (`.get("10/100", rifle)`) for EVERY ranged weapon. **Do NOT wire the
  reach/range gate to real weapon specs until an `"N/N"`→band translation exists** (it doesn't yet).
  The plan (~line 1704) understates this as "which field holds range_band" — it's a *format*
  mismatch, not field-selection. Decide: derive the band from the `"N/N"` numbers, or add a
  categorical band to `DamageSpec`, or map at the call site.
- **BLOCKER 2 — two silent fallbacks in `without_number.py` violate No-Silent-Fallbacks + the file's
  own fail-loud convention** (`_stat` raises KeyError, `save_params`/`apply_system_strain` raise
  ValueError). Fix both as you wire them: (a) `weapon_range_cells` (`:178`) does
  `.get(band, RANGE_BAND_CELLS["rifle"])` — an unknown band should fail loud (ValueError listing
  known bands), not cap at rifle. Note this is the SAME fix family as the 165-1 carryover's
  `adjudicate_reach(mode)` → `Literal` tightening. (b) `combat_move_cells` (`:168`) does
  `getattr(core,"move",None) or DEFAULT_MOVE_METERS` — an explicit `move=0` (immobilized stock;
  `mutation/stocks.py:218` would propagate it) silently becomes full default; use an `is None` check.
- **BLOCKER 3 — `seat_actor_cells` collides player-overflow with opponents (and mis-routes neutrals).**
  Reproduced: 2 players + 1 opponent → PlayerB and Opp1 both on `(3,1)`; neutral-side actors draw
  from the opponent/creature pool and can steal a monster's anchor. Single-player is clean, but
  Keith's playgroup is multiplayer. Task 8 (seat positions at encounter instantiation) MUST define
  multi-player/neutral seating semantics — a single shared anchor index across sides, or reserved
  pools — before this seeds real MP encounters (`sidequest/game/tactical/seating.py:36-51`).
- **Test-strengthening (non-blocking, do while you're here):** the 165-2 delegation test only checks
  return *type* (add a `mock.patch` on `adjudicate_move`/`adjudicate_reach` asserting the call), and
  the "authored once" test checks value-equality not provenance (add `"METERS_PER_CELL" not in
  Sibling.__dict__`). These pair naturally with C1's wiring test that THIS story owns.
