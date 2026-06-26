---
story_id: "158-37"
jira_key: "158-37"
epic: "158"
workflow: "tdd"
---
# Story 158-37: Region theme can violate its own depth_band — theme pool gated by frontier spawn_depth_score while each region depth_score is assigned independently, so a node theme and its depth disagree

## Story Details
- **ID:** 158-37
- **Jira Key:** 158-37
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 2
- **Priority:** p3
- **Type:** bug

## Story Summary

Playtest finding from beneath_sunden multiplayer session (2026-06-23). A region node has a theme (bone_crypt) assigned based on the frontier edge's spawn_depth_score, but the node's final depth_score is computed independently, causing a mismatch: exp011.r2 has theme=bone_crypt at depth_score=8.216, but bone_crypt's depth_band is {min:30.0} — a 22-point violation.

**Root cause:** `_stage_design` builds the theme_pool from `palette.themes_for_depth(frontier_edge.spawn_depth_score)` (one value per expansion), but `assign_depth_scores` computes each node's final depth_score later and independently. A node theme and its own depth_score can disagree on which band they're in, breaking the depth→theme→difficulty gradient coherence.

Related but distinct from 158-19 (quest-pileup); shares the _deepest/depth-band machinery.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-26T04:32:35Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-26T03:54:46Z | 2026-06-26T03:56:42Z | 1m 56s |
| red | 2026-06-26T03:56:42Z | 2026-06-26T04:11:34Z | 14m 52s |
| green | 2026-06-26T04:11:34Z | 2026-06-26T04:25:09Z | 13m 35s |
| review | 2026-06-26T04:25:09Z | 2026-06-26T04:32:35Z | 7m 26s |
| finish | 2026-06-26T04:32:35Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

No upstream findings.

### TEA (test design)
- **Question** (non-blocking): Sibling story 158-19's test (`tests/dungeon/test_shallow_quest_template_variety.py`) embeds Keith's 2026-06-24 random-dungeon steer — "depth tunes ENCOUNTER difficulty ... NOT theme eligibility; every stratum offers a broad grab-bag of themes." Story 158-37's scope treats a theme that violates its own `depth_band` as the bug to fix (honor the band per-node). These reconcile if bounded bands are honored *when declared* while most themes stay wide (grab-bag); they conflict only if Keith wants declared `depth_band`s to be advisory/ignored. Affects `sidequest/dungeon/themes.py` (`theme_eligible_at_depth`) and the fix's direction. *Found by TEA during test design.*
- **Improvement** (non-blocking): Per the OTEL Observability Principle (CLAUDE.md), the theme/depth re-resolution decision must emit an OTEL watcher span so the GM panel can confirm the gradient is coherent (which node re-resolved, from→to theme, final depth). The RED tests live at the pure-engine altitude (no Postgres), so they do NOT assert the span; Reviewer should enforce it. Natural home: the `dungeon.materialize.attach` span path in `materializer._stage_attach`. Affects `sidequest/dungeon/materializer.py` + `sidequest/telemetry/spans/`. *Found by TEA during test design.*
- **Gap** (non-blocking): No acceptance criteria existed in the sprint YAML; TEA defined the invariant (every region's theme eligible at its own final `depth_score`) as the AC during RED. Affects the story's AC record. *Found by TEA during test design.*

### Dev (implementation)
- **Question** (non-blocking): The corrector raises loudly when a region's final depth has NO eligible theme in the palette (No Silent Fallbacks). For the live `beneath_sunden` palette this never fires today (`drowned_cavern` {0,60} blankets shallow depths), but a future world whose theme bands leave a depth-gap will now hard-fail materialization instead of silently mis-theming. That is intended (fail loud → fix content), but it makes per-world theme-band coverage a content invariant worth a pack-validator check. Affects `sidequest-content` theme palettes + the pack validator. *Found by Dev during implementation.*
- **Improvement** (non-blocking): The depth-probe recomputes attach+depth on a throwaway clone in `_stage_design`, then `_stage_attach` computes them again for real (deterministic, identical). Cheap (BFS on a small graph) and chosen to keep `_stage_attach`'s byte-pinned `depth_report` contract intact, but a future refactor that assigns depths once (early) and freezes them onto the expansion would remove the double pass. Affects `sidequest/dungeon/materializer.py`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): The depth-probe block in `_stage_design` (`attach_expansion` + `assign_depth_scores` on the clone) does not set the explicit `span.set_attribute("error"/"reason")` that the sibling `ExpansionGenerationError` handler sets, so a probe failure surfaces only as the design span's auto-recorded exception (loud, but missing the structured `error` extract field). The path is effectively unreachable (clone is byte-identical to the real graph; expansion is pre-validated), so non-blocking — but wrapping the probe in the same try/except-set-attr-reraise pattern would close the lie-detector gap. Affects `sidequest/dungeon/materializer.py` (`_stage_design`). *Found by Reviewer during code review.*
- **Improvement** (non-blocking, endorses Dev's finding): A world whose theme `depth_band`s leave a reachable depth uncovered will now hard-fail materialization (loud raise) instead of silently mis-theming — correct per doctrine, but it makes "every reachable depth has ≥1 eligible theme" a content invariant worth a pack-validator check (not a pytest). Affects `sidequest-content` palettes + the pack validator. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 1 findings (0 Gap, 0 Conflict, 0 Question, 1 Improvement)
**Blocking:** None

- **Improvement:** The depth-probe block in `_stage_design` (`attach_expansion` + `assign_depth_scores` on the clone) does not set the explicit `span.set_attribute("error"/"reason")` that the sibling `ExpansionGenerationError` handler sets, so a probe failure surfaces only as the design span's auto-recorded exception (loud, but missing the structured `error` extract field). The path is effectively unreachable (clone is byte-identical to the real graph; expansion is pre-validated), so non-blocking — but wrapping the probe in the same try/except-set-attr-reraise pattern would close the lie-detector gap. Affects `sidequest/dungeon/materializer.py`.

### Downstream Effects

- **`sidequest/dungeon`** — 1 finding

### Deviation Justifications

4 deviations

- **Tested at the pure-engine altitude, not the full async materialize() pipeline**
  - Rationale: `materialize()` / `_stage_attach` require a Postgres `DungeonTransaction` (skips without `SIDEQUEST_TEST_DATABASE_URL`) and exercise unrelated stages (fill/curate/commit). The bug lives entirely in the design↔depth seam; testing it there is deterministic and DB-free. The invariant assertion (not the call site) is the contract.
  - Severity: minor
  - Forward impact: If Dev implements the fix as a discrete re-resolution step (not folded into design/assign), Dev must invoke it within the design→attach→assign sequence these tests run AND add the call to both tests; otherwise the tests stay RED. Called out in the Test 2 docstring + TEA Assessment.
- **Defined the acceptance invariant myself (no AC in YAML)**
  - Rationale: directly encodes the story title/problem; framing-agnostic (holds trivially for wide-band grab-bag themes, bites only declared bounded bands — the exact production symptom).
  - Severity: minor
- **Fix landed as a discrete corrector wired into `_stage_design` via a depth-probe clone, not folded into `assign_depth_scores`**
  - Rationale: themes are consumed by the fill/curate stages BEFORE `_stage_attach` assigns depths, so the correction must happen in design (before fill) — it cannot live after `assign_depth_scores` in `_stage_attach`. The clone keeps the real graph and `_stage_attach`'s byte-pinned `depth_report` untouched; the real attach reproduces identical depths so the correction holds end-to-end.
  - Severity: minor
  - Forward impact: none — `resolve_themes_for_final_depth` is a public, reusable function; any future caller can run it after depths are known.
- **OTEL span placed on a dedicated `dungeon.materialize.theme_resolve` span, not on the `dungeon.materialize.attach` span**
  - Rationale: the span must nest where the decision is made; the attach span no longer touches theme resolution.
  - Severity: minor

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Tested at the pure-engine altitude, not the full async materialize() pipeline**
  - Spec source: context-story-158-37.md, Problem ("Engine fix"); SM Assessment guidance
  - Spec text: "re-resolve the theme against the final depth_score"
  - Implementation: RED tests drive the real `generate_expansion` + `attach_expansion` + `assign_depth_scores` (Test 1) and the real `materializer._stage_design` + those same calls (Test 2), NOT the full `materialize()` coordinator.
  - Rationale: `materialize()` / `_stage_attach` require a Postgres `DungeonTransaction` (skips without `SIDEQUEST_TEST_DATABASE_URL`) and exercise unrelated stages (fill/curate/commit). The bug lives entirely in the design↔depth seam; testing it there is deterministic and DB-free. The invariant assertion (not the call site) is the contract.
  - Severity: minor
  - Forward impact: If Dev implements the fix as a discrete re-resolution step (not folded into design/assign), Dev must invoke it within the design→attach→assign sequence these tests run AND add the call to both tests; otherwise the tests stay RED. Called out in the Test 2 docstring + TEA Assessment.
- **Defined the acceptance invariant myself (no AC in YAML)**
  - Spec source: context-story-158-37.md, Acceptance Criteria ("No acceptance criteria recorded ... TEA to define")
  - Spec text: (none recorded)
  - Implementation: AC = "after the design→attach→depth pipeline, every region node's theme is eligible at that node's own final `depth_score` (`theme_eligible_at_depth(palette.get(node.theme), node.depth_score)`)."
  - Rationale: directly encodes the story title/problem; framing-agnostic (holds trivially for wide-band grab-bag themes, bites only declared bounded bands — the exact production symptom).
  - Severity: minor
  - Forward impact: none

### Dev (implementation)
- **Fix landed as a discrete corrector wired into `_stage_design` via a depth-probe clone, not folded into `assign_depth_scores`**
  - Spec source: SM Assessment guidance; TEA Assessment "Guidance for Dev" #2
  - Spec text: "re-resolve the theme against the final depth_score ... invoke it inside that [design→attach→assign] sequence"
  - Implementation: new `sidequest/dungeon/theme_resolution.resolve_themes_for_final_depth`, called from `_stage_design` after a throwaway `RegionGraph.from_dict(graph.to_dict())` probe runs `attach_expansion` + `assign_depth_scores` to learn final depths. Test 1 calls the corrector directly; Test 2 exercises the production `_stage_design` wiring (so it did NOT need a test-side corrector call, contrary to TEA's "add to both tests" note).
  - Rationale: themes are consumed by the fill/curate stages BEFORE `_stage_attach` assigns depths, so the correction must happen in design (before fill) — it cannot live after `assign_depth_scores` in `_stage_attach`. The clone keeps the real graph and `_stage_attach`'s byte-pinned `depth_report` untouched; the real attach reproduces identical depths so the correction holds end-to-end.
  - Severity: minor
  - Forward impact: none — `resolve_themes_for_final_depth` is a public, reusable function; any future caller can run it after depths are known.
- **OTEL span placed on a dedicated `dungeon.materialize.theme_resolve` span, not on the `dungeon.materialize.attach` span**
  - Spec source: TEA Delivery Finding (Improvement) — "Natural home: the `dungeon.materialize.attach` span path in `materializer._stage_attach`."
  - Spec text: emit the re-resolution decision on the attach span
  - Implementation: emitted a new nested span under the DESIGN span instead, because the correction now happens in `_stage_design` (not `_stage_attach`). New constant + `SPAN_ROUTES` route + helper in `sidequest/telemetry/spans/dungeon_materialize.py`.
  - Rationale: the span must nest where the decision is made; the attach span no longer touches theme resolution.
  - Severity: minor
  - Forward impact: none

### Reviewer (audit)
- **TEA: Tested at the pure-engine altitude, not the full async materialize() pipeline** → ✓ ACCEPTED by Reviewer: sound — `materialize()`/`_stage_attach` are Postgres-bound and exercise unrelated stages; the bug lives entirely in the design↔depth seam. Test 2 still drives the production `_stage_design`, so the wiring is proven without the DB-bound coordinator.
- **TEA: Defined the acceptance invariant myself (no AC in YAML)** → ✓ ACCEPTED by Reviewer: the invariant ("every region's theme eligible at its own final depth_score") is the correct, framing-agnostic encoding of the story title/problem.
- **Dev: Fix landed as a discrete corrector wired into `_stage_design` via a depth-probe clone, not folded into `assign_depth_scores`** → ✓ ACCEPTED by Reviewer: necessary, not optional — fill/curate consume the theme BEFORE `_stage_attach` assigns depths, so the correction MUST precede fill; `assign_depth_scores` (a pure depth fn) is the wrong home. The clone keeps the byte-pinned `depth_report` contract intact. Verified the determinism that makes it correct.
- **Dev: OTEL span on a dedicated `dungeon.materialize.theme_resolve` span, not on the attach span** → ✓ ACCEPTED by Reviewer: the span must nest where the decision is made (design), which moved relative to TEA's "natural home: attach span" suggestion. Correct adjustment.

## Sm Assessment

**Story:** 158-37 — Region theme can violate its own depth_band (server engine fix, 2pts, p3, tdd).

**Scope:** Single repo (`sidequest-server`), single subsystem — the ADR-106 procedural megadungeon edge-expansion path. This is a self-contained coherence bug, not a feature: theme selection and final depth assignment are computed against two different depth values, so a node's theme can fall outside its own depth_band.

**Why this is well-bounded for TDD:**
- The bug is a deterministic invariant violation — "a node's assigned theme must be valid for that node's final depth_score" — which makes for a clean RED test. TEA can assert the invariant over generated regions (or a synthetic expansion fixture) and watch it fail on the current independent-assignment ordering.
- The reproduction is concrete: `_stage_design` reads `palette.themes_for_depth(frontier_edge.spawn_depth_score)`; `assign_depth_scores` overwrites the per-node depth later. The seam to test is the disagreement between those two stages.

**Guidance for TEA (RED):**
- Test the invariant in code with synthetic fixtures, NOT against real content packs (per project rule: content invariants belong in the pack validator, not pytest). Use a synthetic palette + frontier edge so the test owns its depth bands.
- Cover the gradient-coherence claim: after expansion + depth assignment, every node's theme must satisfy that theme's depth_band given the node's own depth_score.
- Watch out for the shared `_deepest`/depth-band machinery with 158-19 (quest-pileup) — touch only the theme/depth seam, don't entangle the quest path.

**Guidance for Dev (GREEN):**
- Per "No Silent Fallbacks": when theme and depth disagree, fail loudly or re-resolve the theme against the *final* depth_score — do not silently clamp or pick a default theme.
- Add an OTEL watcher event on the theme/depth resolution decision (per the OTEL Observability Principle) so the GM panel can verify the gradient is coherent.

**Routing:** TDD is phased → next agent is TEA for the RED phase. No blockers; merge gate clear (only open PR is an unrelated dependabot bump). Base branch for server is `develop`; feature branch `feat/158-37-region-theme-depth-band-coherence` created.

— Themis the Just

## TEA Assessment

**Tests Required:** Yes
**Reason:** Engine bug with a clean, deterministic invariant — ideal for TDD.

**Test Files:**
- `tests/dungeon/test_theme_depth_band_coherence.py` — three tests pinning the depth↔theme coherence invariant.

**Tests Written:** 3 tests covering 1 AC (the AC TEA defined — see Design Deviations).
**Status:** RED (2 failing as designed, 1 GREEN positive control — ready for Dev)

### The bug (root cause, confirmed by reading the code)
- `materializer._stage_design` (materializer.py:673/675/682) builds the candidate `theme_pool` from `palette.themes_for_depth(request.frontier_edge.spawn_depth_score)` — ONE depth value, the frontier edge we spawn from.
- `generate_expansion` then picks each new node's theme via `rng.choice(theme_pool)` (region_graph/generator.py:78) — before any final depth exists.
- Only later, in `_stage_attach`, does `assign_depth_scores` (materializer.py:1393 → region_graph/depth.py) compute each node's final `depth_score` by ordinary-route hop distance from the entrance — independently.
- Result: a node themed against a deep frontier can land shallow (a short stitch route to the surface) and end up wearing a theme its own `depth_band` excludes. The 2026-06-23 playtest's exp011.r2 = `bone_crypt` (band {min:30}) at depth 8.216.

### Test outcomes (verified twice via testing-runner, `-n0`)
| Test | State | Evidence |
|------|-------|----------|
| `test_every_region_theme_is_eligible_at_its_own_final_depth_score` | RED (assert) | 3 nodes themed `deep_theme` (band min 50) landed at depth 18.3 / 32.7 / 41.5 |
| `test_stage_design_themed_nodes_are_eligible_at_their_final_depth` | RED (assert) | same violations through the REAL `_stage_design` path (wiring proof) |
| `test_wide_band_palette_is_already_coherent` | GREEN | depth-agnostic {min:0,max:None} grab-bag never violates (positive control) |

Both RED failures are assertion failures (not collection/setup errors).

### Rule Coverage
| Rule (CLAUDE.md / project) | Test(s) | Status |
|----------------------------|---------|--------|
| No Silent Fallbacks (declared band must be honored, not silently violated/defaulted) | both invariant tests assert eligibility + `palette.get()` (real theme, no default) | RED |
| Every Test Suite Needs a Wiring Test (reachable from production path) | `test_stage_design_themed_nodes_...` drives the real `materializer._stage_design` | RED |
| No Source-Text Wiring Tests | wiring proved by behavior through `_stage_design`, not by grepping source | satisfied |
| No content in unit tests (synthetic fixtures only) | synthetic `ThemePalette` + `FrontierEdge` + graph; zero real-pack reads | satisfied |
| Don't entangle 158-19 quest path | tests touch only the theme/depth seam (no quest/`_deepest`) | satisfied |

**Rules checked:** 5 applicable rules have coverage.
**Self-check:** 1 inverted/vacuous test found and fixed during RED — the first draft of Test 2 asserted `assert violations` (green-now/red-after-fix); flipped to assert the post-fix invariant (`violations == []`).

### Guidance for Dev (GREEN)
1. **The fix is per-node depth, not frontier depth.** Make each region's theme eligible at that region's OWN final `depth_score`. SM's "re-resolve the theme against the final depth_score" is the right shape.
2. **Placement matters for these tests.** They run only `generate_expansion`/`_stage_design` → `attach_expansion` → `assign_depth_scores`. If you implement re-resolution as a discrete step, invoke it inside that sequence (and add the call to both invariant tests). If you fold it into the design/assign functions, the tests pass as-is.
3. **No Silent Fallbacks.** When re-resolving, pick a real palette theme eligible at the node's depth; never clamp the depth, never blank/default the theme. If no eligible theme exists for a node's depth, raise loudly (that's a content gap, surfaced — see the Question finding re: 158-19/Keith).
4. **OTEL.** Emit a watcher span on the re-resolution decision (per the OTEL principle) — see the Improvement delivery finding.
5. **Preserve the grab-bag.** `test_wide_band_palette_is_already_coherent` guards Keith's random-dungeon doctrine; do not over-narrow eligibility such that wide-band themes stop being selectable everywhere.

**Handoff:** To Hephaestus the Smith (Dev) for implementation.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/dungeon/theme_resolution.py` (NEW) — `resolve_themes_for_final_depth` + `ThemeResolutionReport`. After depths are known, re-themes any region whose theme's `depth_band` excludes its own final `depth_score`, picking deterministically (blake2b sub-seed) from `themes_for_depth(its own depth)`. Leaves already-eligible regions untouched (preserves the grab-bag); raises loudly on a depth with no eligible theme (No Silent Fallbacks).
- `sidequest/dungeon/materializer.py` — `_stage_design` now learns final depths on a throwaway clone (`RegionGraph.from_dict(graph.to_dict())` → `attach_expansion` → `assign_depth_scores`) and calls the corrector BEFORE returning, so corrected themes reach fill/curate. Real `_stage_attach` reproduces identical depths; its byte-pinned `depth_report` is untouched. Emits the new theme-resolve span.
- `sidequest/telemetry/spans/dungeon_materialize.py` — new `dungeon.materialize.theme_resolve` span constant + `SPAN_ROUTES` route + `dungeon_materialize_theme_resolve_span` helper (GM-panel lie-detector: `resolved_count` + per-region from/to/depth audit).
- `tests/dungeon/test_theme_depth_band_coherence.py` — added the corrector call to Test 1 (unit contract); refreshed Test 1 & Test 2 docstrings to post-fix reality (Test 2 now proves the production `_stage_design` wiring).

**The fix in one line:** the theme was gated by the frontier's single `spawn_depth_score`; now each region's theme is re-resolved against its OWN final `depth_score` before any stage consumes it.

**Tests:**
- Story tests: 3/3 GREEN (`test_theme_depth_band_coherence.py`).
- Dungeon regression: 534/534 GREEN (`tests/dungeon/ -n0`).
- Telemetry routing/registry: 54/54 GREEN (`-n0`; new span accepted by completeness checks).
- Lint/format: clean on all changed files. Pyright: the one error (`materializer.py:1506` `seed_expansion_quest`/`DungeonTransaction`) is PRE-EXISTING on `develop` (line 1476 there), unrelated to this change.

**Branch:** `feat/158-37-region-theme-depth-band-coherence` (pushed to origin).

**Notes for Reviewer:**
- Two deviations from TEA's letter (both logged): the corrector lives in `_stage_design` (not after `assign_depth_scores` in `_stage_attach`) because fill/curate consume the theme before attach assigns depth — so the correction MUST precede fill; and the OTEL span is a dedicated `theme_resolve` span nested under design (not on the attach span) for the same reason.
- The clone-probe computes depths twice (probe + real). Deterministic and cheap; chosen to keep the attach `depth_report` contract intact (logged as an Improvement finding).

**Handoff:** To next phase (verify / review).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (537 pass, lint+format clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 7 (3 medium, 4 low) | confirmed 1 (LOW), dismissed 4, deferred 0, downgraded 2→low |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none (6 rule classes checked, 0 violations) | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (3 enabled subagents returned; 6 disabled via `workflow.reviewer_subagents` and assessed by the Reviewer directly)
**Total findings:** 1 confirmed (LOW), 6 dismissed/downgraded (with rationale), 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

This is a correct, well-tested, production-wired fix for a real dungeon-generation coherence bug. No Critical or High findings. The single substantive theme raised by the edge-hunter (failure-path span coverage on the depth-probe) is a near-unreachable LOW observability nit, captured as a non-blocking follow-up.

**Data flow traced:** `request.frontier_edge.spawn_depth_score` → `_stage_design` builds `theme_pool` via `themes_for_depth(spawn_depth)` → `generate_expansion` themes each new region from that pool → **(new)** throwaway clone `RegionGraph.from_dict(graph.to_dict())` runs `attach_expansion` + `assign_depth_scores` to learn each region's FINAL depth → `resolve_themes_for_final_depth` re-themes any band-violating region against its own depth → corrected themes flow to fill/curate/attach → real `_stage_attach` reproduces identical depths (same topology + `campaign_seed`) so the correction holds in the persisted map. Safe because the clone is byte-identical to the real graph at design time and depth assignment is deterministic — I verified the determinism chain (`ordinary_route_dist` BFS + `depth_jitter(campaign_seed, region_id)`), and Test 2 exercises exactly this production path end-to-end (GREEN).

**Pattern observed:** Clone-not-mutate to preserve the byte-pinned `depth_report` contract — `sidequest/dungeon/materializer.py:721-723`. Good pattern: it computes depths on a throwaway so `_stage_attach` still scores the real regions and its span attributes are unchanged. `dataclasses.replace` on frozen `RegionNode` (theme_resolution.py:141-142) is the correct idiom for the frozen model.

**Error handling:** Fails loud on both real error paths — missing `depth_score` (theme_resolution.py:113-117) and a depth with NO eligible theme (theme_resolution.py:124-131, with a full band audit in the message). Honors CLAUDE.md No Silent Fallbacks: no clamp, no default theme, no skip.

### Observations
- [VERIFIED] Determinism of the clone vs real attach — `materializer.py:721-723` clones via `from_dict(to_dict())` (identical topology) and `assign_depth_scores` is a pure function of topology + `campaign_seed`; the corrected theme is therefore eligible at the identical real depth. Evidence: Test 2 (`_stage_design` → real `attach_expansion` → real `assign_depth_scores` → assert coherent) is GREEN.
- [VERIFIED] No Silent Fallbacks — `theme_resolution.py:113-117` and `:124-131` raise `ValueError` loudly; complies with CLAUDE.md. The empty-eligible message includes the full theme-band map for diagnosis.
- [VERIFIED] OTEL on the decision — new `dungeon.materialize.theme_resolve` span + `SPAN_ROUTES` route (`dungeon_materialize.py`) carries `resolved_count` + per-region from/to/depth JSON; `resolved_count==0` proves the corrector ran and found the generation already coherent. Complies with the OTEL Observability Principle.
- [VERIFIED] Grab-bag preserved (Keith 2026-06-24) — the corrector only re-themes ineligible regions (`theme_resolution.py:120` `continue` on eligible); `test_wide_band_palette_is_already_coherent` confirms `{min:0,max:None}` themes are untouched. Evidence: Test 3 GREEN.
- [VERIFIED] No regression — 534 dungeon tests + 54 telemetry routing/registry tests GREEN serially (`-n0`); the new span is accepted by `test_routing_completeness`.
- [SEC][VERIFIED] Security clean — reviewer-security checked 6 rule classes (No Silent Fallbacks, no bare except, no unsafe deserialization, boundary input validation, blake2b determinism, no PII logging) with 0 violations. Inputs are internal engine data (`campaign_seed:int`, `expansion_id:int`, `region_id:str`); the `blake2b` f-string is a hash input (no injection surface), `json.dumps` of resolutions is span-only, and `RegionGraph.from_dict` round-trips in-memory data through typed constructors (no untrusted deserialization). Evidence: theme_resolution.py:80-84, 113-131; materializer.py:721-737.
- [EDGE][LOW] Depth-probe failure path lacks the explicit `span.set_attribute("error"/"reason")` that `_stage_design`'s `ExpansionGenerationError` handler sets (`materializer.py:721-723`). Confirmed but downgraded from the edge-hunter's medium: the path is effectively unreachable (the clone is byte-identical to the real graph and the expansion is pre-validated by `generate_expansion`'s `check_invariants`, so a probe `attach_expansion` raise implies an identical real raise), AND `Span.open` uses `start_as_current_span` which records the exception on the `dungeon.materialize.design` span by default — so a failure is loud and span-recorded; only the structured `error` extract field is absent. Non-blocking; captured as an Improvement delivery finding.
- [EDGE→dismissed] `palette.get(scored.theme)` raising `KeyError` vs `ValueError` (theme_resolution.py:119): dismissed as unreachable for new nodes — their theme came from `themes_for_depth(...)` which only returns palette members, so the lookup always hits. Minor type-consistency nit at most.
- [EDGE→dismissed] mutation-during-iteration (theme_resolution.py:142): dismissed — `original` is bound by `enumerate` before the index write, list length is invariant, and CPython index assignment during index-based iteration is well-defined. Not a bug.
- [EDGE→dismissed] theme-id rename breaks determinism (theme_resolution.py / `_pick_index`): dismissed as a pre-existing, stated determinism constraint that already governs `generate_expansion`'s `rng.choice(theme_pool)` and `depth_jitter` — not introduced here.
- [EDGE→dismissed] empty `new_nodes` / zero-node expansion: dismissed — unreachable; `JaquaysConfig.validate` requires `new_regions_per_expansion` lo ≥ 1.

### Rule Compliance
- **No Silent Fallbacks (CLAUDE.md):** Compliant. `resolve_themes_for_final_depth` raises on missing depth and on no-eligible-theme; `_stage_design` uses the real palette, no default. Checked every branch in theme_resolution.py.
- **No Stubbing / half-wiring (CLAUDE.md):** Compliant. The corrector is fully wired into the production `_stage_design`; Test 2 is the wiring test proving the production path is active (not just a unit harness).
- **Every Test Suite Needs a Wiring Test (CLAUDE.md):** Compliant — Test 2 drives production `_stage_design`.
- **No content in unit tests (project rule):** Compliant — all three tests use synthetic `ThemePalette`/`FrontierEdge`/graph; zero real-pack reads.
- **OTEL Observability Principle (CLAUDE.md):** Compliant on the success path (new `theme_resolve` span). Minor gap on the unreachable probe-failure path (see LOW finding) — non-blocking because the exception is span-recorded by default.
- **Python checklist #1/#8/#11 (silent except / unsafe deser / input validation):** Compliant (security subagent confirmed: no except clauses, no pickle/yaml/eval/subprocess, inputs internal).
- **Determinism / no `seed ^ 0x5EED` fixed-point:** Compliant — `_pick_index` uses `blake2b` sub-seeding (theme_resolution.py:80-84), the sanctioned pattern.
- **`[SILENT]`/`[TEST]`/`[DOC]`/`[TYPE]`/`[SIMPLE]`/`[RULE]`:** subagents disabled via settings; Reviewer assessed each domain directly — no swallowed errors (all raises are loud), tests are non-vacuous with meaningful assertions + positive control, docstrings match post-fix behavior (Dev refreshed Test 1/2 docstrings), types use frozen-dataclass `replace` correctly, no over-engineering (the clone is the minimal production-correct option given fill-consumes-theme-before-depth), and the change matches the surrounding dungeon-stage + span-helper conventions.

### Devil's Advocate
Suppose I want this to be broken. The most dangerous claim is "the clone reproduces identical depths." If `assign_depth_scores` had ANY nondeterminism — wall-clock, set iteration order, dict ordering — the corrected theme (chosen against probe-depth) could mismatch the real depth, silently re-introducing the bug it claims to fix. I checked: depth = `ordinary_route_dist` (BFS over a dict whose insertion order is preserved and identical between clone and real, since `from_dict` replays `to_dict`'s order) + `depth_jitter(campaign_seed, region_id)` (blake2b, no RNG state). No wall-clock, no global RNG. The clone is built in the same call with no intervening mutation. So depths are identical — and Test 2 proves it through the real path. Next attack: a confused content author ships a world whose theme bands leave a depth uncovered. Old behavior: silently mis-theme. New behavior: `resolve_themes_for_final_depth` raises loudly, aborting materialization. Is loud-abort worse than silent-mis-theme? No — fail-loud is the doctrine, and the message names the gap; but it DOES mean a content gap now hard-fails a player connect instead of degrading. Dev already surfaced this as a Question finding and it argues for a pack-validator coverage check — correct call, not a blocker for this engine fix. Next: does the corrector churn the grab-bag and flatten variety? No — it only touches ineligible regions (`continue` on eligible), and Test 3 guards the wide-band case. Next: mutation-during-iteration corrupting `expansion.new_nodes`? No — index-based, length-invariant, `original` pre-bound. Next: the double depth computation as a DoS? No — BFS on a per-expansion graph bounded by `burst_magnitude`, microseconds. Last: does the fix desync fill/curate (which consume theme before attach)? This was the whole reason the fix lives in `_stage_design` before fill, not in `_stage_attach` after — verified the pipeline order (design→fill→curate→attach) and that correction precedes fill. The fix holds.

**Handoff:** To SM for finish-story