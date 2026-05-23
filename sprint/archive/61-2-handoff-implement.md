# Handoff: review-fix -> sm-finish
**Story:** 61-2  |  **Agent:** dev  |  **Timestamp:** 2026-05-23T22:30:00Z

## Summary

Applied Reviewer's two MUST-FIX items plus one SHOULD-FIX (gaslighting-doctrine) on the same `feat/61-2-snapshot-drop-list-seven-fields` branch as a single fix commit. Hoisted `current_room_id` resolution out of the per-NPC projection loop (1 OTEL span/turn instead of N+1), removed dead `isinstance` defenses + corrected the docstring that lied about "no silent fallbacks," and made the projection skip `room_states`/`npcs` (pass-through) when actor location is unresolvable so the projection itself doesn't gaslight the narrator into an empty world. Two new tests added in the same file cover the gaslighting-skip behavior.

## Deliverables

- `sidequest-server/sidequest/server/session_helpers.py`:
  - `_npc_in_scene(npc, snapshot, *, current_room: str | None)` — signature change: takes the pre-resolved current room, no longer calls `snapshot.party_location(...)` internally.
  - `_apply_phase_c_projections(snapshot, payload, *, current_room_id: str | None)` — signature change: takes pre-resolved location; noops on `room_states` and `npcs` when None/empty; runs `known_facts` and `discovered_clues` unconditionally. Dead `isinstance` guards removed in the load-bearing branches (kept on `scenario_state` since it's `Optional`). Docstring rewritten to match actual behavior.
  - `_build_turn_context` — resolves `current_room_id` once above the projection seam, fires the `actor_location_empty` warning BEFORE the projection runs (was previously after), passes the value into both the projection and the 45-13 room-state-injection block.
- `sidequest-server/tests/server/test_61_2_snapshot_seven_field_projection.py` — two new tests:
  - `test_projection_skips_room_states_and_npcs_when_actor_location_unresolvable` — caplog asserts `actor_location_empty` warning fires; payload assertions confirm room_states + npcs survive unprojected.
  - `test_projection_still_runs_known_facts_and_clues_when_actor_location_unresolvable` — PC/scenario projections still run despite unresolvable location.

## Key Decisions

- **Span-fan-out fix via callsite hoist, not span suppression.** The cleanest fix is to call `party_location` ONCE per turn and pass the result everywhere it's needed. This also coalesces with the existing 45-13 room-state-injection lookup which used to call `party_location` a second time — the new shape has exactly one call per turn instead of N+2.
- **Dead `isinstance` removal scoped to load-bearing branches.** Kept the `isinstance(scenario_payload, dict)` and `isinstance(clues, list)` checks because `scenario_state` is `Optional` (may be `None` or excluded by `exclude_defaults`) and `discovered_clues` is dumped from a `set` (not all serializer paths produce a list). Removed the four `isinstance` checks where pydantic v2 guarantees the shape (`room_states: dict`, `npcs: list[Npc]`, `characters: list[Character]`, and per-entry dict checks on those dumped lists).
- **Gaslighting-skip on `room_states`/`npcs` only, not on `known_facts`/`clues`.** Degraded actor location doesn't make a PC's known facts grow back or a clue cap irrelevant. Only the location-keyed projections noop on the no-location path; the cost-runaway pressure on the other two is still relieved.
- **Warning fires before projection.** TEA's prior `actor_location_empty` warning was triggered AFTER the projection ran (line 785 in the old shape). Moved it ABOVE the projection so the GM panel sees the degraded-location signal next to the projection-skip outcome, not after the strip would have already happened.
- **Did NOT touch out-of-scope items.** Left `npc: object` annotation and the cosmetic `payload["npcs"] = []` noise for 61-7. Probe fixture NIT deferred.

## Open Questions

- The `current_room_id` hoist means the variable now lives in `_build_turn_context` scope from earlier in the function — there's no risk of stale read because the snapshot is stable for the turn, but a future refactor that mutates `snapshot.character_locations` mid-turn (no current caller does) would need to re-resolve. Documented in the comment.

## Test Status

- 61-2 file in isolation: **17/17 passing** (15 prior + 2 new).
- Full server suite: **7261 passed, 400 skipped, 0 failed** (was 7259; +2 = the two new tests, no regressions).
- Lint (scoped to changed files): `ruff check` passed; `ruff format --check` reports both files already formatted.

## Branch + Commit

- Branch: `feat/61-2-snapshot-drop-list-seven-fields` (pushed)
- Fix commit: `6f589f9` — `fix(61-2): reviewer MUST-FIX + gaslighting-doctrine SHOULD-FIX`
- Branch tip on origin: `6f589f9` (also includes prior commits `0c043c8` GREEN, `fdf6578` probe, `85b9792` RED).

## Note for SM / Reviewer

- The `just server-fmt` recipe runs `ruff format .` repo-wide and reformatted 106 unrelated files on the post-fix pass. I reverted those — only the 2 intended files are in the commit. Future runs of the recipe will surface the same noise; consider a scoped `ruff format $(git diff --name-only)` invocation as a follow-up workflow improvement.
- Reviewer's framing of the three findings was tight and correct. Nothing surfaced during the fix that suggests the other two SHOULD-FIX items (annotation cleanup, payload noise) need to land here — they're genuinely 61-7-shaped.
