---
story_id: "158-11"
jira_key: ""
epic: "158"
workflow: "trivial"
---
# Story 158-11: Harmund Fuel-Count seeds manual_origin=false/location=None while 3 camp siblings seed authored — reconcile 4th NPC

## Story Details
- **ID:** 158-11
- **Jira Key:** (none — Jira not enabled for this project)
- **Workflow:** trivial
- **Type:** bug
- **Points:** 1
- **Priority:** p3
- **Stack Parent:** none

## Repos and Branches
- **content:** feat/158-11-harmund-fuelcount-seed-reconcile (gitflow)
- **server:** feat/158-11-harmund-fuelcount-seed-reconcile (gitflow)

## Sm Assessment

**Routing:** `trivial` (phased) → **dev** (implement phase). 1pt p3 bug, repro is precise and pre-narrowed; no design phase needed.

**The bug (repro from `/Users/slabgorb/Projects/sq-playtest-pingpong.md` ~L368):** In world `caverns_and_claudes/beneath_sunden`, the four authored Ropefoot camp NPCs all seed (`pregen.authored_npcs_seeded … inserted=4 total_authored=4`), but tagging splits 3-vs-1. Three siblings seed `manual_origin=true` + a ropefoot `location`; **Harmund Fuel-Count (`harmund_fuel_count`), the 4th/last in the list, seeds `manual_origin=false` + `location=None`** despite being inserted.

**SM narrowing (Dev to verify, don't take on faith):** `sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden/npcs.yaml` defines all four NPCs with **structurally identical shape** — Harmund (~L212) has the same `id`/`name`/OCEAN/`initial_disposition: 18`/`location_tags: ["ropefoot"]` as his siblings. A grep surfaced no content asymmetry. → Fix is **most likely server-side** seeding/tagging logic (a "first-N" cap or off-by-one that stamps `manual_origin`/`location` on 3 of 4 and drops the last). Story is tagged content,server, but the content branch may end up unused — that's fine.

**Acceptance criteria:**
- **AC1:** All four camp NPCs (`brecca_half_hand`, `ondre_drumhand`, `salla_who_came_back_thin`, `harmund_fuel_count`) seed with `manual_origin=true` and a non-None ropefoot `location` in the runtime snapshot.
- **AC2:** Root cause identified — trace the authored-NPC seed path that emits `pregen.authored_npcs_seeded` and stamps `manual_origin`/`location`; fix the logic that excludes the 4th NPC (or, if Dev finds a real content-field asymmetry the grep missed, fix the data instead and say so).
- **AC3:** Regression test pins all four Ropefoot NPCs seeded with `manual_origin=true` + a ropefoot location (guards against the 4th-NPC drop recurring).
- **AC4:** `just server-check` green; no regression in other NPC seeding.

**Jira:** none — project tracks via pf sprint; jira field null, claim explicitly skipped.

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-24T10:02:01Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-24T09:14:31.259048Z | 2026-06-24T09:18:06Z | 3m 34s |
| implement | 2026-06-24T09:18:06Z | 2026-06-24T09:46:09Z | 28m 3s |
| review | 2026-06-24T09:46:09Z | 2026-06-24T10:02:01Z | 15m 52s |
| finish | 2026-06-24T10:02:01Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Improvement** (non-blocking): The same inject-cap drop affected the wry_whimsy/oz road's 4 companions (named in the old test docstring as "surfaced 3, dropped 1") — that earlier work only made the drop *observable* (`available_placed_dropped` span) instead of fixing it. This fix resolves both at once; the oz case is now also corrected. No separate story needed.
- **Question** (non-blocking): `preload_authored_npcs` (`game/world_materialization.py:824`) still seeds authored NPCs with `manual_origin=False`/`location=None` and relies on the per-turn inject patch to upgrade them — semantically an authored NPC is `manual_origin=True` from birth. Harmund's siblings work the same way, so this is not a bug today, but seeding the authored origin marker at preload time would make authored NPCs correct *before* the first inject (relevant for any pre-inject projection). Out of scope for this 1pt fix.

### Reviewer (code review)
- **Improvement** (non-blocking): Unplaced walk-on drops are uninstrumented when an authored roster fills the budget (`len(placed) ≥ _AVAILABLE_NPC_INJECT_LIMIT` → `unplaced_budget=0`), and this change pins the one live drop-signal `available_placed_dropped` to constant-0. Affects `sidequest/server/dispatch/monster_manual_inject.py` (add an `available_unplaced_dropped` span attribute + a `logger.info` mirroring `active_inject_capped`, and refresh the now-stale span comment at ~714-728 that still cites "oz road: 4 eligible, 3 matched, 1 dropped"). Pre-existing drop behavior (counts unchanged by this diff) so non-blocking, but worth a follow-up to restore GM-panel drop visibility. *Found by Reviewer during code review (corroborated by silent-failure-hunter).*
- **Improvement** (non-blocking): If the genre-pack authoring surface ever opens to untrusted contributors, the now-uncapped `placed` partition would let a pack place arbitrarily many NPCs at one location (narrator-context bloat). Affects `sidequest/server/dispatch/monster_manual_inject.py` (a defensive upper bound like `placed[:32]` with a loud warning would be belt-and-suspenders). Not warranted under the current internal-author threat model. *Found by Reviewer during code review (from security subagent).*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Lifted the placed-NPC inject cap (changed a previously-tested invariant)**
  - Spec source: session AC2 — "fix the logic that excludes the 4th NPC"
  - Spec text: "trace the authored-NPC seed path that stamps manual_origin/location; fix the logic that excludes the 4th NPC"
  - Implementation: `_npc_patches_for_available_humans` now surfaces ALL placed (location_tagged) NPCs uncapped; `_AVAILABLE_NPC_INJECT_LIMIT` bounds only *unplaced* walk-ons. Previously `eligible_all[:3]` sliced the combined list and dropped placed NPCs beyond the cap. The existing `test_inject_span_reports_placed_dropped_by_cap` pinned that drop (4 eligible → 3 matched → 1 dropped) and was rewritten to assert the corrected invariant (all placed surface, `available_placed_dropped == 0`).
  - Rationale: a location-placed authored NPC is the scene's intended cast, not a generic walk-on; dropping it is the bug. AC1 requires all 4 to seed `manual_origin=true` + a location, which is only achievable by injecting all 4. Magic-number bumping the cap would be fragile (a 5-NPC camp re-breaks it) and per-world special-casing violates No Silent Fallbacks.
  - Severity: minor
  - Forward impact: any world with **more than 3 placed NPCs anchored to the same location** now surfaces all of them in `snapshot.npcs` every turn (previously capped at 3). This is the intended/desired behavior for authored rosters; the per-location count remains observable via the injection span (`available_placed_eligible`). Generic unplaced walk-ons stay bounded.
- **Content branch unused (server-only fix)**
  - Spec source: session **Repos:** content,server
  - Spec text: story tagged content,server
  - Implementation: no content change — `beneath_sunden/npcs.yaml` was already correct (all 4 NPCs structurally identical, ropefoot-tagged). The defect was entirely server-side (the inject cap). The `feat/158-11-…` content branch has zero commits.
  - Rationale: SM's setup pre-narrowed this ("the content branch may end up unused — that's fine"); measured DB ground truth (save 16097) confirmed Harmund was authored correctly and only the runtime injection dropped him.
  - Severity: minor
  - Forward impact: SM finish should create a PR for the **server** repo only; the content branch can be closed/ignored.

### Reviewer (audit)
- **Lifted the placed-NPC inject cap** → ✓ ACCEPTED by Reviewer: sound and the only fix that satisfies AC1 (all 4 must surface with `manual_origin=True` + location). Verified the partition preserves `available_at_location`'s placed-first order (monster_manual.py:408), avoids the negative-slice trap (`max(0, …)`, line 326), and keeps the walk-on cap (test + line 326-327). Behavior change (worlds with >3 placed NPCs at one location surface all) is intended and observable via the injection span. Magic-number bump and per-world special-casing were correctly rejected.
- **Content branch unused (server-only fix)** → ✓ ACCEPTED by Reviewer: confirmed against measured DB ground truth (save 16097) — Harmund's content is structurally identical to his siblings; the defect was the server cap. SM should PR the server repo only and close/ignore the content branch.

## Dev Assessment

**Implementation Complete:** Yes

**Root cause (measured, not asserted):** Queried the live save DB (session 16097, `2026-06-23-beneath_sunden-mp-…`) and read all 16 NPCs' stored fields. Every NPC carried `manual_origin=True` + a resolved location **except Harmund Fuel-Count** (`manual_origin=False`, `location=None`). Traced to `monster_manual_inject._npc_patches_for_available_humans`: the per-turn injection capped placed-NPC surfacing at `_AVAILABLE_NPC_INJECT_LIMIT=3` via `eligible_all[:3]`, dropping the 4th ropefoot-placed NPC (Harmund). Dropped NPCs never receive the `_human_patch(manual_origin=True, location=…)`, so Harmund stayed at `preload_authored_npcs`'s `False`/`None` default while his 3 siblings (injected) seeded authored.

**Fix:** Placed (location_tagged) NPCs now surface uncapped; the cap bounds only unplaced generic walk-ons. One function changed; docstrings updated to match.

**Files Changed (server only):**
- `sidequest/server/dispatch/monster_manual_inject.py` — partition eligible NPCs into placed (uncapped) + unplaced (capped); updated the two affected docstrings.
- `tests/server/dispatch/test_monster_manual_inject.py` — rewrote `test_inject_span_reports_placed_dropped_by_cap` → `test_inject_surfaces_all_placed_npcs_above_cap` (asserts all placed surface, `dropped==0`); added `test_inject_unplaced_walkons_still_capped_with_no_placed` (cap still bounds walk-ons) and `test_inject_full_camp_roster_all_seed_authored` (the 158-11 4-NPC Ropefoot regression: all four seed `manual_origin=True` + non-None location).

**Tests:** GREEN. Targeted files 76/76; full owning module `tests/server/dispatch/` 494/494 (0 fail). `ruff check` + `ruff format --check` clean on changed files.

**AC status:** AC1 ✅ (regression test pins all four seeding `manual_origin=True` + location) · AC2 ✅ (root cause = inject cap; fixed) · AC3 ✅ (regression test added) · AC4 ✅ (dispatch module green, no regression).

**OTEL:** No new span needed — the existing `monster_manual.injected` span already carries `available_placed_dropped`; the fix drives it to 0 and it now serves as a regression tripwire (a non-zero value = placed authored NPCs being dropped again).

**Branch:** `feat/158-11-harmund-fuelcount-seed-reconcile` (server, pushed). Content branch unused (no changes needed).

**Handoff:** To review (Westley).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (50/50 tests, ruff clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — edges assessed by Reviewer |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 (both confirmed, Medium/Low) | confirmed 2, dismissed 0, deferred 0 |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — tests assessed by Reviewer |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — comments assessed by Reviewer (corroborates [SILENT] finding 2) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — types assessed by Reviewer |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — simplicity assessed by Reviewer |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — rules checked by Reviewer (see Rule Compliance) |

**All received:** Yes (3 enabled returned: preflight clean, security clean, silent-failure-hunter 2 findings; 6 disabled, pre-filled)
**Total findings:** 2 confirmed (both non-blocking, Medium/Low), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** `current_location` (server-side `GameSnapshot`, engine-controlled — not raw player input) → `available_at_location()` filters Manual NPCs to AVAILABLE-and-tag-matching → partition placed/unplaced → `_human_patch(manual_origin=True, location=current_location)` → `apply_world_patch` materializes onto `snap.npcs`. Safe: NPC roster + `location_tags` come from authored genre-pack YAML loaded at bind, never reflected from client payloads ([SEC] confirmed clean).

**Pattern observed:** Partition-then-bound replaces a flat cap slice — `placed + unplaced[:max(0, LIMIT - len(placed))]` at monster_manual_inject.py:323-327. Correct and idiomatic.

### Observations (8 dispatch tags + VERIFIEDs)

- **[SILENT][MEDIUM, non-blocking]** When `len(placed) ≥ _AVAILABLE_NPC_INJECT_LIMIT`, `unplaced_budget` collapses to 0 and all unplaced walk-ons are dropped with no span attribute or log line — asymmetric with `active_inject_capped` (logs) and `available_placed_dropped` (span). **Confirmed but non-blocking:** the unplaced-drop *count* is mathematically identical before and after this diff (`eligible_all[:3]` was placed-first, so any location with ≥3 placed already surfaced 0 unplaced) — it is a *pre-existing* gap, not introduced here. The change's only observability effect is pinning `available_placed_dropped` to constant-0. → Recorded as a non-blocking Improvement (add `available_unplaced_dropped`).
- **[DOC][LOW-MEDIUM, non-blocking]** The span-emission comment at inject() ~714-728 ("matched = how many surfaced through the `_AVAILABLE_NPC_INJECT_LIMIT` slice"; "oz road: 4 eligible, 3 matched, 1 dropped") is now stale — post-change placed NPCs do NOT pass through the slice and that drop is impossible. Drift caused by this change (the lines are outside the diff hunk). → Recorded as a non-blocking Improvement (refresh alongside the span addition). Corroborates the disabled comment-analyzer's domain.
- **[SEC][VERIFIED clean]** No injection/auth/secret/path/DoS issues. The newly-uncapped `placed` partition is bounded by server-controlled authored YAML, not player input — `current_location` is engine-derived. Security subagent flagged a *non-security* content note (a 50+ NPC single-location pack would bloat narrator context); requires commit access to genre YAML, not warranted for the current internal-author threat model. Evidence: monster_manual.py:383-408, `_human_patch` at :320-356.
- **[EDGE][VERIFIED]** (edge-hunter disabled — assessed directly) Negative-slice trap avoided: `unplaced_budget = max(0, …)` at monster_manual_inject.py:326, so `unplaced[:0]` (not the `unplaced[:-1]` last-element drop) when placed ≥ cap. The `len(placed) > cap` case is exercised by `test_inject_surfaces_all_placed_npcs_above_cap` (4 placed, cap 3).
- **[TEST][VERIFIED]** (test-analyzer disabled — assessed directly) 3 tests, all non-vacuous with specific value assertions: `test_inject_full_camp_roster_all_seed_authored` pins AC1 (`manual_origin is True` + `location is not None` for all 4); `test_inject_surfaces_all_placed_npcs_above_cap` pins surfaced-count==n_placed AND span dropped==0; `test_inject_unplaced_walkons_still_capped_with_no_placed` guards the walk-on cap survives. Minor gap (non-blocking): no explicit mixed placed<cap+unplaced case, but it's bracketed by the boundary tests and the existing placement test.
- **[TYPE][VERIFIED]** (type-design disabled — assessed directly) `_npc_patches_for_available_humans` is an internal helper; return annotation `tuple[list[NpcPatch], int, int, int]` unchanged and still accurate. New locals (`placed`/`unplaced`/`unplaced_budget`) are list[ManualNpc]/int — correctly inferred, no annotation gap, no stringly-typed API.
- **[SIMPLE][LOW, non-blocking]** Post-change `available_placed_matched` (line 328) is always == `available_placed_eligible` by construction — mildly redundant — but intentionally retained to preserve the span schema (GM-panel reads it) and serve as the always-0 `available_placed_dropped` regression tripwire. Acceptable; not over-engineering.
- **[RULE][VERIFIED]** (rule-checker disabled — Rule Compliance done below) python.md 13-check pass; only the No-Silent-Fallbacks/OTEL consistency note ([SILENT] above), classified non-blocking.
- **[VERIFIED] Ordering preserved:** `available_at_location` returns `placed + unplaced` (monster_manual.py:408) — strictly placed-first — so the inject partition reproduces the original surfacing order exactly. Complies with the "authored roster NPCs win the surfacing race" intent.
- **[VERIFIED] No other callers affected:** `_npc_patches_for_available_humans` is called only from `inject()` (monster_manual_inject.py:670). Blast radius is one function; full dispatch module 494/494 green.

### Rule Compliance (python.md + CLAUDE.md/SOUL.md)

- **#1 Silent exceptions:** N/A — no try/except in diff. ✓
- **#2 Mutable defaults:** N/A — no new signatures. ✓
- **#3 Type annotations:** internal helper, return type intact; locals correctly typed. ✓
- **#4 Logging:** no new error path. The pre-existing `active_inject_capped` logger.info is unchanged. The unplaced-drop lacks a log — flagged [SILENT], non-blocking/pre-existing. ◑
- **#6 Test quality:** specific assertions, no vacuous truthy checks, correct fixtures. ✓
- **#7–#12 (resources/deserialization/async/imports/input-validation/deps):** N/A — none touched. ✓
- **CLAUDE.md No Silent Fallbacks / OTEL Observability Principle:** the fix's own verification IS observable (placed `eligible == matched`, snapshot npc count, `available_placed_dropped == 0`); the unplaced-drop instrumentation is a separately-scoped, pre-existing consistency improvement, not a gate on this fix. ◑ (recorded as follow-up)
- **SOUL "Bind the Ruleset":** N/A — not a ruleset/combat mechanic. ✓

### Devil's Advocate

Argue this code is broken. **Reordering attack:** if `available_at_location` ever returned unplaced *before* placed, my partition would silently reorder the surfaced NPCs versus the old `[:3]` slice — but I read monster_manual.py:408 and it returns `placed + unplaced`, so the invariant holds today; a future refactor that interleaves them would break the equivalence silently (there is no test pinning placed-first ordering at the `available_at_location` level — a latent risk, but out of this diff's scope). **Unbounded growth:** a malicious *content author* could tag 500 NPCs to one location and flood every turn's snapshot; confirmed by [SEC] as a content-authoring concern, not a player-reachable exploit — requires git write access. **Confused-author misread:** the now-stale span comment ("oz road: 4 eligible, 3 matched, 1 dropped") would mislead a future dev debugging why `available_placed_dropped` is always 0 — this is real and recorded [DOC]. **Stressed runtime:** `eligible_all` empty → both partitions empty → `available = []` → no patches, `inject` returns its other-source count; no crash, no div-by-zero. **`current_location` None/blank:** `available_at_location` gates placed out on blank loc (monster_manual.py docstring M6) so only unplaced surface — unchanged by this diff. **The genuinely missed thing:** the [SILENT] unplaced-drop is now the *steady state's* only drop, and the span went from "one live drop-signal (placed)" to "zero live drop-signals" — that's a real, if minor, reduction in the GM panel's lie-detecting power for this location, and it is the strongest argument for the follow-up. None of these rise to a correctness or security defect that blocks a 1pt fix whose core behavior is verified correct and green.

**Error handling:** empty/None inputs handled (no crash); walk-on bounding is deliberate, not a swallowed error.
**Handoff:** To SM for finish-story (server PR only; content branch unused).