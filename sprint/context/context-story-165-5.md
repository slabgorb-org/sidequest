# Story 165-5 Context

## Title
Fate zone projection + binding zone state/legality + conflict-seating wiring (plan tasks 11–13)

## Metadata
- **Story ID:** 165-5
- **Type:** story
- **Points:** 5
- **Priority:** p1
- **Workflow:** superpowers → run as **spdd** (settled Keith decision, `sm-decisions.md`)
- **Repo:** server
- **Epic:** Mapping Track C — tactical mechanics (ADR-096 v2)

## Problem
Plan tasks 11–13: a pure zone projection (grid → contiguous cell clusters) in
`sidequest.game.tactical.zones`, the Fate binding consuming that projection to wire zone
state + zone-move legality + OTEL, and conflict-seating wiring (gated on
`isinstance(ruleset, FateRulesetModule)` so WN/dial packs are untouched).

## Technical Approach
_TEA/Dev refine per the plan. The C3 zone projection reuses the C1 primitives
(`parse_mask`, `is_floor`, `neighbors`) from `sidequest/game/tactical/adjudication.py`;
the Fate binding consumes `project_zones`/`ZoneProjection`._

## Scope
- In scope: Fate zone projection + binding + conflict-seating wiring (plan tasks 11–13).
- Out of scope: WN enforcement (165-3), protocol/UI math (165-4). Dogfight (ADR-153) untouched.

## Acceptance Criteria
_TEA to define during the RED phase from plan tasks 11–13._

## Carryover from 165-1 (C1 library — read before starting)
Full detail: `sprint/archive/165-1-session.md` + `context-epic-165.md` §Carryover + the
tea/dev/reviewer `*-gotchas.md` (tagged 165-1).
- **Reuses C1 primitives** (`parse_mask`/`is_floor`/`neighbors`) — same pure-library discipline
  (no IO, no clock, no random). Coordinate convention: `cell = (x, y)`, x=col, y=row, origin
  top-left.
- **The plan doc's embedded code has bugs** (two Task-2 defects fixed in 165-1's code but still
  in the doc). Task 11 ships its own embedded test — hand-evaluate every mask/coordinate
  assertion (a quick `python3 -c` reimplementing `parse_mask`/`is_floor` catches mask bugs fast).
- Per the plan, `ZoneMoveAdjudication(free, requires_overcome, from_zone, to_zone)` is already
  defined in `zones.py` (Task 11) — import it in Task 12, do not redefine.
- New spans must call `publish_event` + carry a `SPAN_ROUTES`/`FLAT_ONLY_SPANS` entry.
