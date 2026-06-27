---
story_id: "158-49"
jira_key: ""
epic: "158"
workflow: "refactor"
---
# Story 158-49: WN attribute canonicalization — drop flavor stat names; space_opera/elemental_harmony/neon_dystopia use the shared canonical STR/DEX/CON/INT/WIS/CHA block

## Story Details
- **ID:** 158-49
- **Jira Key:** (none — Jira disabled)
- **Workflow:** refactor
- **Repos:** sidequest-content, sidequest-server

## Summary

Spun out of 158-47. The Without Number family (SWN/WWN/CWN/AWN) shares ONE
six-attribute block (STR/DEX/CON/INT/WIS/CHA). Three packs keyed character stats
by flavor names via `attribute_map` (space_opera Physique/Reflex…, elemental_harmony
Insight/Spirit…, neon_dystopia Brawn/Tech/Cool…). That relabel was cosmetic at the
mechanical-key level and crashed the WN throw-stat path (`without_number._stat`
looks up canonical keys, fails loud on a flavor-keyed stat block; the throw-modifier
path — unlike saves/initiative — does not apply `attribute_map`). The other four WN
packs already used canonical codes.

Keith's ruling (2026-06-27): drop the flavor relabeling; all WN packs use the
canonical codes. Flavor-as-display-only (render Reflex/Brawn on the sheet, engine
keys canonical) is a deferred follow-up.

## Delivered

- **sidequest-content #510** — canonicalized space_opera / elemental_harmony /
  neon_dystopia: `ability_score_names` (order preserved), `attribute_map` values,
  every `opponent_default_stats`, `prime_requisite`, archetype `stat_ranges`, beat
  `stat_check`. Prose/lore/element/class-name uses untouched.
- **sidequest-server #1096** — updated 19 tests that hardcoded flavor stat names;
  migrated the elemental_harmony cast proof onto the DICE_THROW seam.

## Verification

All 3 packs load; built characters have canonical stat keys. Full server suite
diffed vs clean-develop baseline: my migrations fixed the 3 WWN cast tests; I broke
exactly 40 flavor-hardcoded tests → all 40 fixed; re-diff = zero net-new failures.
Remaining suite reds are pre-existing/environmental (namegen/encountergen subprocess,
embedding/arc/tension wiring) + xdist-flaky chargen-commit tests (pass serially).
Ruff clean.

## Deferred

- Flavor-as-display-only layer (player-facing genre stat labels over canonical keys).
- Self-contained synthetic test fixtures (`tests/fixtures/packs/swn_test_pack`, the
  CWN block in `test_builder_seeds_strain`) still use flavor names — internally
  consistent, not content-coupled; left as-is.
