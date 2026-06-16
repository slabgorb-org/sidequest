---
story_id: "120-5"
jira_key: ""
epic: "120"
workflow: "trivial"
---
# Story 120-5: 120-2 review fast-follows (3 non-blocking test-hardening findings, all sidequest-server, no production code)

## Story Details
- **ID:** 120-5
- **Jira Key:** (none)
- **Workflow:** trivial
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-16T02:01:53Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-16T01:44:30.924737Z | 2026-06-16T01:45:49Z | 1m 18s |
| implement | 2026-06-16T01:45:49Z | 2026-06-16T01:53:20Z | 7m 31s |
| review | 2026-06-16T01:53:20Z | 2026-06-16T02:01:53Z | 8m 33s |
| finish | 2026-06-16T02:01:53Z | - | - |

## Technical Approach

**Repository:** sidequest-server
**Branch Strategy:** gitflow (feat/120-5-120-2-review-fastfollows)
**Base Branch:** develop

### Acceptance Criteria

1. **ruff-format test_120_2_road_warrior_verbatim_baseline.py**
   - File: `tests/genre/test_120_2_road_warrior_verbatim_baseline.py`
   - Task: Run ruff format on the file; the parenthesized assert at line 146 reflows to a one-liner
   - No logic change; ungated by server-check

2. **Fix test_starting_mounted_weapons_fit_in_starting_rig_slots catalog resolution**
   - File: `tests/genre/test_road_warrior_vessel_calibration.py`
   - Test: `test_starting_mounted_weapons_fit_in_starting_rig_slots`
   - Problem: Currently builds catalog from world tier only, so repointed `cwn_*` kit IDs resolve to `{}` via silent `.get(i,{})`
   - Fix: Rebuild catalog from `resolve_inventory(pack, "the_circuit")` (merged genre+world) so genre-tier kit IDs are visible

3. **Add non-empty guard to test_road_warrior_circuit_kits_resolve_no_dangling_ids**
   - File: `tests/genre/test_120_2_road_warrior_verbatim_baseline.py`
   - Test: `test_road_warrior_circuit_kits_resolve_no_dangling_ids`
   - Problem: Loops `resolved.starting_equipment.items()` with no non-empty guard (vacuous if ever empty)
   - Fix: Add `assert resolved.starting_equipment` before the loop to ensure meaningful assertion

### Definition of Done
- All three test changes implemented
- All assertions remain meaningful
- Full test suite passes (`just server-check` green)
- No production code changes

## Delivery Findings

### Dev (implementation)
- No upstream findings. All three items were self-contained test-hardening; the underlying 120-2 content (genre-verbatim baseline + the_circuit world inventory) is correct — every kit id resolves in the merged catalog, the rig ladder matches `rig_composure_spec`, and mount weapons fit their slots.

### Reviewer (code review)
- **Improvement** (non-blocking): The docstring of `test_starting_mounted_weapons_fit_in_starting_rig_slots` — the function Dev edited — still opens with the stale "RED until mount_slots parses." line directly above the new accurate paragraph; the test is GREEN, so the marker now contradicts itself. Affects `tests/genre/test_road_warrior_vessel_calibration.py:216` (drop the stale "RED until" sentence). *Found by Reviewer during code review.* [DOC][LOW]
- **Improvement** (non-blocking): Three further stale "RED until / RED today" status markers survive in **untouched** parts of the same file — module docstring (`:17`), `test_every_vessel_item_parses_cleanly` (`:95`), `test_mounted_rig_weapons_carry_vehicle_damage` (`:195`) — all left over from 86-5/120-2 shipping the parser + damage content; those tests are now GREEN. Out of scope for 120-5; worth a one-shot doc-cleanup follow-up. Affects `tests/genre/test_road_warrior_vessel_calibration.py` (refresh the four "RED" markers to GREEN). *Found by Reviewer during code review.* [DOC][LOW]
- **Improvement** (non-blocking): `parse_vessel_tags(catalog[rig_ids[0]].model_dump())` couples the test to `parse_vessel_tags`'s `isinstance(item, dict)` contract. Sound today (no field aliases on `CatalogItem`), but if the parser ever accepts a typed item or `CatalogItem` gains aliases, the `.model_dump()` bridge could silently rename `id`/`tags`. Affects `tests/genre/test_road_warrior_vessel_calibration.py:240` + `sidequest/game/vessel_tags.py` (consider a `CatalogItem`-accepting overload / helper later). *Found by Reviewer during code review.* [TEST][LOW]

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

1 deviation

- **Replaced the silent `.get(i, {})` catalog default with an explicit missing-id assertion (finding #2)**
  - Rationale: The finding names the silent `.get(i, {})` as the defect; per the No Silent Fallbacks project rule, de-masking it with an explicit assert is the honest fix rather than swapping the source while leaving the silent default in place. Verified satisfied (0 missing) against the real pack.
  - Severity: minor
  - Forward impact: none — test-side guard only; no production code or sibling-story assumption changes.

## Design Deviations

### Dev (implementation)
- **Replaced the silent `.get(i, {})` catalog default with an explicit missing-id assertion (finding #2)**
  - Spec source: .session/120-5-session.md, finding #2
  - Spec text: "rebuild catalog from resolve_inventory(pack, \"the_circuit\") (merged genre+world) so genre-tier kit ids are visible"
  - Implementation: Rebuilt the catalog from the merged `resolve_inventory(pack, "the_circuit")` result as specified, AND added `assert not missing` to fail loud on any kit id absent from the merged catalog — replacing the silent `catalog.get(i, {})` default the finding itself flagged.
  - Rationale: The finding names the silent `.get(i, {})` as the defect; per the No Silent Fallbacks project rule, de-masking it with an explicit assert is the honest fix rather than swapping the source while leaving the silent default in place. Verified satisfied (0 missing) against the real pack.
  - Severity: minor
  - Forward impact: none — test-side guard only; no production code or sibling-story assumption changes.

### Reviewer (audit)
- **Dev deviation — explicit `assert not missing` replacing the silent `.get(i, {})`** → ✓ ACCEPTED by Reviewer: correct direction per the No Silent Fallbacks rule. Both reviewer-rule-checker (rule A1) and reviewer-test-analyzer confirm the de-masking is the intended fix, not scope creep; the guard is complementary to the sibling `test_road_warrior_circuit_kits_resolve_no_dangling_ids` (localized fail-fast message before the keyed access vs. the authoritative all-worlds dangling-id gate), and it is satisfied (0 missing) against the real pack. No undocumented deviations found in the diff.

## Sm Assessment

**Routing:** trivial workflow (phased) → handoff to **dev** for the `implement` phase. 1pt, p3.

**Scope is tightly bounded and test-only.** All three findings are 120-2 review fast-follows in `sidequest-server`, touching only `tests/genre/`. No production code. Two files:
- `tests/genre/test_120_2_road_warrior_verbatim_baseline.py` (findings 1 + 3)
- `tests/genre/test_road_warrior_vessel_calibration.py` (finding 2)

**The one finding with real teeth is #2** — the vessel-calibration test silently passes today because `cwn_*` kit ids resolve to `{}` via `.get(i,{})` when the catalog is built from the world tier alone. Rebuilding from `resolve_inventory(pack, "the_circuit")` (merged genre+world) makes the genre-tier kit ids visible; expect this to surface a *real* assertion the test was previously skipping. Dev should confirm the test still passes meaningfully after the fix, not just that it's green.

Findings #1 (ruff reflow) and #3 (non-empty guard) are mechanical hardening.

**DoD:** all three applied, assertions stay meaningful (no vacuous green), `just server-check` passes. Base branch is `develop` (gitflow) — not main.

**Jira:** none — internal fast-follow, no key. Claim explicitly skipped.

**No blockers.** Branch `feat/120-5-120-2-review-fastfollows` is cut from latest develop.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `tests/genre/test_120_2_road_warrior_verbatim_baseline.py` — finding #3: added `assert resolved.starting_equipment` before the per-class kit loop so the dangling-id check can't pass vacuously when a world resolves zero class kits. Finding #1: `ruff format` reflowed the parenthesized `assert resolved is not None, (...)` to a one-liner (no logic change).
- `tests/genre/test_road_warrior_vessel_calibration.py` — finding #2: `test_starting_mounted_weapons_fit_in_starting_rig_slots` now rebuilds its catalog from the merged `resolve_inventory(pack, "the_circuit")` (typed) instead of the world-tier raw dict. Added the `resolve_inventory` import; switched dict access to typed `CatalogItem` attributes (`.tags`/`.category`), feeding `parse_vessel_tags` via `.model_dump()`; replaced the silent `.get(i, {})` with an explicit missing-id assert.

**Verification of teeth (finding #2):** against the real pack, the_circuit's world-only catalog is 26 items; the merged catalog is 92. Four kit ids — `cwn_basic_tools_kit`, `cwn_binoculars`, `cwn_handheld_radio`, `cwn_medkit` — are genre-tier verbatim items the old world-only catalog silently dropped to `{}`. The test now resolves the real chargen catalog. Not cosmetic.

**Tests:** 12/12 passing (GREEN), **0 skipped** — both changed tests confirmed to run against real loader logic, not skip. Run: `uv run pytest tests/genre/test_120_2_road_warrior_verbatim_baseline.py tests/genre/test_road_warrior_vessel_calibration.py -v`. ruff check clean on both.

**Scope:** test-only, no production code touched. Diffstat: 2 files, +29/-12.

**Branch:** feat/120-5-120-2-review-fastfollows (sidequest-server, base develop) — pushed.

**Handoff:** To review (Chrisjen Avasarala / Reviewer).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 12/12 GREEN, ruff check + format clean, 0 smells |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 3 (low) | confirmed 1 non-blocking (model_dump coupling), dismissed 2 (informational — confirmed the guards are correct) |
| 5 | reviewer-comment-analyzer | Yes | findings | 4 (high) | confirmed 4 [DOC][LOW] non-blocking — 1 in-scope (`:216`), 3 deferred out-of-scope (`:17`,`:95`,`:195`) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | none (0 / 17 rules) | N/A — exhaustive, zero violations |

**All received:** Yes (4 enabled returned, 5 disabled skipped)
**Total findings:** 0 confirmed blocking, 5 confirmed non-blocking (4 [DOC][LOW], 1 [TEST][LOW]), 2 dismissed (informational), 3 of the [DOC] deferred as out-of-scope debt

## Reviewer Assessment

**Verdict:** APPROVED

Test-only hardening of three 120-2 review fast-follows. All three changes do exactly what the story asked, the suite is GREEN (12/12, 0 skipped), and the exhaustive rule check found zero violations across 17 rules. The only findings are low-severity documentation staleness — none meet the Critical/High blocking bar.

**Data flow traced:** genre-pack content (`road_warrior` genre baseline + `worlds/the_circuit/inventory.yaml`) → `resolve_inventory(pack, "the_circuit")` → merged catalog (`merge_inventory_catalog`, union by id; world-replaces-genre for `starting_equipment`, ADR-140/145 D3) → the test's rig-slot-fit check. Safe because the test now resolves the **same** merge path production chargen uses, instead of the world-only YAML subset it read before — the change strengthens fidelity, it does not bypass anything.

### Observations

- [VERIFIED] Finding #3 closes a real vacuous-loop: `assert resolved.starting_equipment` is inserted at the per-world level (inside `for world_slug in pack.worlds`) before the `.items()` loop — evidence `test_120_2_road_warrior_verbatim_baseline.py:151-154`. An empty kit dict can no longer pass silently. Complies with lang-review check #6 and CLAUDE.md "fail-loud, not vacuous".
- [VERIFIED] Finding #2 catalog source upgrade is strictly stronger — evidence `test_road_warrior_vessel_calibration.py:226-248`: catalog now `{it.id: it for it in resolve_inventory(pack,"the_circuit").item_catalog}` (92 items) vs the prior world-only dict (26). Dev's teeth check (4 recovered `cwn_*` ids) reproduced independently during implement.
- [RULE] reviewer-rule-checker: 0 violations / 17 rules. The new `from sidequest.server.dispatch.inventory_resolve import resolve_inventory` import (`:36`/`:49`) is a documented ADR-147 re-export shim over `sidequest.game.inventory_resolve` → `sidequest.genre.*`; test→production direction, no cycle.
- [SILENT] No silent failures introduced — the diff *removes* a silent fallback. The old `catalog.get(i, {}).get("tags")` swallowed genre-tier ids; the replacement `assert not missing` (`:233-237`) fails loud. (Dedicated silent-failure-hunter disabled via settings; covered here + by rule A1.)
- [TEST] reviewer-test-analyzer: the three changes are genuine improvements with no surviving vacuous assertions; one low note — `parse_vessel_tags(...model_dump())` (`:240`) couples to the parser's `dict` contract. Confirmed non-blocking (no aliases on `CatalogItem` today); logged as a delivery finding.
- [DOC] reviewer-comment-analyzer: 4 stale "RED until/today" markers. One (`:216`) is inside the docstring Dev edited and now self-contradicts the new GREEN paragraph — confirmed [LOW], in scope, logged. Three (`:17`,`:95`,`:195`) are untouched pre-existing 86-5/120-2 debt — deferred to a follow-up.
- [VERIFIED] `_circuit_inventory()` is **not** orphaned by finding #2 — evidence `:64-66`: still consumed by `_vessel_dicts()` feeding the three AC2 stat-block tests, which correctly want the raw world dict (no chargen merge needed). Leaving it is right.
- [TYPE] / [SEC] / [SIMPLE] / [EDGE] — specialists disabled via `workflow.reviewer_subagents`. Self-assessed: no type-invariant, security, or complexity surface in a two-assertion test diff with no user-input boundary; no over-engineering (the `missing` guard is the minimal honest replacement for the silent default).

### Rule Compliance

Checked the Python lang-review checklist (13) + CLAUDE.md additional rules (No Silent Fallbacks, Every Suite Needs a Wiring Test, No Source-Text Wiring Tests, fail-loud) against every applicable instance in both files (rule-checker corroborated):

- **#6 Test quality** — every modified test carries substantive, non-vacuous assertions; new guards (`:151`, `:233`) specifically remove vacuous-pass risk. No `@pytest.mark.skip`, no truthy-only asserts, no mock-target errors. PASS.
- **#10 Import hygiene** — new `resolve_inventory` import is non-circular (re-export shim, ADR-147); no star imports; test modules need no `__all__`. PASS.
- **#1 Silent exceptions** — `_load()`/`_load_typed()` catch `PackNotFound` specifically → `pytest.skip(str(exc))`; no bare/broad swallow. PASS.
- **#8 Unsafe deserialization** — `yaml.safe_load` in `_circuit_inventory()` (unchanged). PASS.
- **No Silent Fallbacks (CLAUDE.md)** — diff removes `.get(i, {})` masking, replaces with explicit `assert not missing`. PASS (improvement).
- **Wiring test (CLAUDE.md)** — both modified tests drive real production paths (`load_genre_pack`/`resolve_inventory` against the real pack). PASS.
- **No Source-Text Wiring Tests** — no `read_text()`/regex against production source as an assertion. PASS.
- #2 mutable defaults, #3 type annotations (public test fns all `-> None`; privates exempt), #4 logging, #5 path handling, #7 resource leaks, #9 async, #11 input validation, #12 deps, #13 fix-regressions — no applicable surface or compliant. PASS.

### Devil's Advocate

Let me try to break this. The most suspicious move is feeding `parse_vessel_tags` a `CatalogItem.model_dump()` instead of the raw YAML dict it used to get. Could the round-trip through pydantic mutate the shape the parser depends on? `parse_vessel_tags` only reads `item["id"]` and `item["tags"]` and parses the `tier-N`/`composure:N`/`mount_slots:N` colon-tags out of the `tags` list. `model_dump()` on `CatalogItem` emits `id: str` and `tags: list[str]` verbatim — no aliases, no serialization transform on those two fields — so the parser sees identical inputs. Preflight ran it: 12/12 green, the spec-table and slot-fit tests pass, proving the dumped dict parses to the same VesselTags. If a future dev adds a `Field(alias=...)` to `id` or `tags`, this silently breaks — but that's a *future* hazard, already logged as a non-blocking finding, not a present defect.

Next: does swapping to the merged catalog accidentally *weaken* the test? Could it now pass because the merged catalog contains so many items that every kit id resolves trivially? No — the test's assertions are about *counts and capacity* (exactly one rig per class; mounted weapons ≤ rig mount_slots), not mere presence. A bloated catalog can't fake a rig count or a slot overflow; if anything the larger catalog makes `rig_ids`/`mounted` classification *more* honest because genre-tier items are no longer invisible. The new `assert not missing` is the real teeth: if a kit referenced a typo'd id, the old `.get(i,{})` ate it; now it fails loud.

What about the empty/degenerate cases? If `the_circuit` had zero classes, `assert starting` (`:218`) fires. If `resolve_inventory` returned `None` (no inventory at either tier), `assert resolved is not None` (`:216`) fires. If a class kit had no rig, `assert len(rig_ids) == 1` fires. Every degenerate path is now a loud failure, not a vacuous pass — which is the entire point of the story.

The one thing a confused maintainer could genuinely misread is the docstring: "RED until mount_slots parses" sits above a paragraph explaining the test is doing merged-catalog resolution and is plainly green. A reader skimming the top line could believe the test is expected-failing. That is a real (if low) harm to comprehension — confirmed and logged. It does not affect behavior. Nothing here rises to High.

**Handoff:** To SM (Camina Drummer) for finish-story.