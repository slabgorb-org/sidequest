---
story_id: "158-39"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 158-39: Dogfight opponent brain — narrator-motivated maneuver selection + deterministic disposition fallback (ADR-153 Plan 3)

## Story Details
- **ID:** 158-39
- **Jira Key:** (none — YAML-only story)
- **Workflow:** tdd
- **Stack Parent:** none
- **Epic:** 158 — Playtest sweep follow-ups: WWN combat seating, narrator grounding, roster/map/MP polish

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-07-01T14:14:18Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-01T12:58:14Z | 2026-07-01T13:00:35Z | 2m 21s |
| red | 2026-07-01T13:00:35Z | 2026-07-01T13:20:30Z | 19m 55s |
| green | 2026-07-01T13:20:30Z | 2026-07-01T13:41:49Z | 21m 19s |
| review | 2026-07-01T13:41:49Z | 2026-07-01T13:56:55Z | 15m 6s |
| green | 2026-07-01T13:56:55Z | 2026-07-01T14:04:40Z | 7m 45s |
| review | 2026-07-01T14:04:40Z | 2026-07-01T14:14:18Z | 9m 38s |
| finish | 2026-07-01T14:14:18Z | - | - |

## Sm Assessment

**Routing:** tdd / phased → RED phase → **TEA (Fezzik)**. Setup complete; session, context, and branch (`feat/158-39-dogfight-opponent-brain` on sidequest-server) all verified.

**Dependency cleared:** ADR-153 Plan 1 (firewall + seating) has landed — 158-31, 158-34, 158-49 all done (server #1097 surfaces sealed-letter SWN maneuvers). This story seats the opponent *brain* on that existing floor. Do not re-open or re-balance the firewall (SOUL: Bind the Ruleset, Don't Balance It).

**Setup correction:** the story arrived tagged `repos: pennyfarthing` — a data error for a server-side engine story. Corrected to `server` to match its Plan 1 siblings. All work lands in sidequest-server.

**Load-bearing invariants for the RED tests to guard:**
1. **The firewall.** Positioning layer never picks position or computes damage; SWN resolves the shot; engine only gates legality (energy + pilot tier) and resolves geometry. A test must fail if the positioning layer ever computes damage or selects a shot outcome.
2. **Narrator is the default, fallback is the floor.** Narrator-motivated selection drives normally; the deterministic disposition-derived fallback fires *only* when the narrator pass is skipped (ADR-006). Both must be exercised and distinguishable.
3. **OTEL `dogfight.maneuver_committed`** carries `maneuver_id` + `stance_source` (narrator vs fallback). This is the GM-panel lie-detector — a **Keith/dev observability tool**. Per CLAUDE.md, do NOT attribute this span to "Sebastien's lie-detector" in code or test comments (158-35 drew a review finding for exactly that mis-attribution — don't repeat it).
4. **Wiring test required** (project rule): a live dogfight turn must drive the real opponent-brain selection end-to-end and assert the span fires with the correct stance source — not a source-grep.

**No Jira:** YAML-only story; Jira integration is not enabled. Explicitly skipped, not overlooked.

## Technical Approach

### Narrator-Motivated Maneuver Selection (ADR-153 Section 4)
- The NPC ace picks its maneuver each turn from the legal menu, motivated by its goal/disposition (revenge, escape, protect convoy, prove itself) — the same authority the narrator already holds for any NPC beat.
- Routed through the same NPC-beat authority the narrator uses for other decisions.
- Default behavior: narrator pass determines maneuver selection based on disposition/goal.

### Positioning/Resolution Firewall (Load-Bearing — ADR-153)
- The engine gates legality (energy + pilot tier) and resolves geometry; SWN resolves the shot.
- The positioning layer NEVER picks position or computes damage.
- Firewall must remain intact: separation between positioning decisions and resolution.

### Deterministic Disposition-Derived Fallback (ADR-006 Graceful Degradation)
- Fallback fires only when narrator pass is skipped — it is the FLOOR, not the default.
- A deterministic fallback selects a legal maneuver from the energy + pilot-tier-gated menu.
- Fallback behavior must be distinguishable from narrator-driven selection in observability.

### OTEL Observability (Mandatory)
- Span: `dogfight.maneuver_committed`
- Must carry:
  - `maneuver_id` — the chosen maneuver
  - `stance_source` — "narrator" or "fallback" to distinguish the decision path
- GM panel lie-detector can confirm which path chose the maneuver.

## Acceptance Criteria

1. **Narrator-Motivated Selection:** The NPC ace selects its maneuver each turn from the legal (energy + pilot-tier-gated) menu, motivated by its disposition/goal — routed through the same NPC-beat authority the narrator already uses.

2. **Firewall Integrity:** The positioning/resolution firewall holds: the positioning layer never picks position or computes damage; SWN resolves the shot; the engine gates legality and resolves geometry.

3. **Fallback Determinism:** A deterministic disposition-derived fallback selects a legal maneuver when the narrator pass is skipped — it is the floor, and stance source is distinguishable from the narrator-driven path.

4. **OTEL Span Coverage:** `dogfight.maneuver_committed` fires carrying `maneuver_id` + stance source (narrator vs fallback); GM-panel lie-detector can confirm which path chose the maneuver.

5. **Wiring Test:** A live dogfight turn drives the real opponent-brain selection end-to-end (not a source-grep) and asserts the span fires with the correct stance source.

## Dependencies (Satisfied)
- **ADR-153 Plan 1** (firewall + seating) has LANDED — stories 158-31, 158-34, 158-49 complete.
- Build on that floor; do not re-open the firewall.
- Reference: `docs/superpowers/plans/2026-06-26-dogfight-rebuild-plan-1-firewall-seating.md`

## Delivery Findings

### TEA (test design)
- **Gap** (non-blocking): AC-4's "narrator" source half needs a stamp the Plan 3 doc omits. The plan's Task 3 snippet only stamps `source="fallback"` in the `if not narrator_legal` branch — but `test_narrator_committed_blue_is_sourced_narrator` requires the NORMAL (narrator-committed) blue `dogfight.maneuver_committed` span to carry `source="narrator"`. Dev must also stamp `source="narrator"` on the resolver/seam's narrator-path blue commit span. Affects `sidequest/server/dispatch/sealed_letter.py` (or the seam in `narration_apply.py` where the blue commit span fires). *Found by TEA during test design.*
- **Gap** (blocking for `test_maneuver_loading.py::test_loader_resolves_maneuvers_onto_dogfight_def`): the loader test loads the FIXTURE pack (`swn_test_pack`), not live content (project rule: server tests never depend on sidequest-content). The Plan 3 Task 1 wires the `maneuvers: {_from: dogfight/maneuvers_mvp.yaml}` pointer only into the live `space_opera/rules.yaml`. Dev must ALSO add that pointer to the fixture dogfight def at `sidequest-server/tests/fixtures/genre_packs/swn_test_pack/rules.yaml` (the `maneuvers_mvp.yaml` file already exists there). *Found by TEA during test design.*
- **Note** (non-blocking): `SPAN_DOGFIGHT_MANEUVER_COMMITTED` is already in `SPAN_ROUTES` under component=dogfight — the routing guard passes today. Dev only needs to add the `source`/`attitude` attrs at the call site; the span already reaches the GM panel. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): three pre-existing test failures surfaced by my dogfight regression sweep are NOT caused by this story — I confirmed all three fail on `develop` with my changes stashed. They are stale tests for behavior earlier sibling stories deliberately deleted: (1) `tests/genre/test_dogfight_content_loading.py::test_dogfight_has_dual_track_metrics` and (2) `::test_dogfight_beats_cover_every_consumed_maneuver` assert the space_opera dogfight's native dial + beats, which **158-31** (ADR-153 §2 firewall) removed (`player_metric` is now None, `beats` is `[]`); (3) `tests/server/test_encounter_lifecycle.py::test_sealed_letter_empty_npcs_present_raises_without_consuming_fallback` asserts empty-npcs seating RAISES, but **158-34** (ADR-153 §6) changed the contract to seat a default-from-frame ship. These should be updated/removed to match the post-firewall reality — out of scope for 158-39 (I did not touch them, and re-adding the dial to satisfy them would re-open the firewall). *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): the stance directive derives the opponent's disposition from the pre-seat `threat_name`, which is empty in the frame_default and `npcs_present`-nonempty seating paths, silently defaulting to "hostile" and ignoring the seated opponent's disposition. Affects `sidequest/agents/subsystems/dogfight.py` (185-186 — look up the opponent from the seated `snapshot.encounter.actors`, like `narration_apply.py`). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the engine floor's `blue_attitude` "neutral" default (`narration_apply.py:6074-6076`) and the stance directive's "hostile" default disagree for the same "opponent NPC not found" case, and neither emits a signal. Affects both files (add a `logger.warning`/OTEL attr when the opponent-NPC lookup misses, so a seeding-invariant break is visible). *Found by Reviewer during code review.*
- **Question** (non-blocking): `viewer_energy` defaults to 60 when absent (`narration_apply.py:6091`). Confirm every dogfight starting-state seeds `viewer_energy` (only `merge` is authored today) so the affordability gate is never silently fed a wrong full-energy assumption on a non-`merge` seat. *Found by Reviewer during code review.*
- **Resolved** (round-trip 1): the blocking F1 above is fixed in commit `89f30d44` (stance reads the seated opponent; default logged) and independently verified; F2 observability added to the floor. One remaining non-blocking **Improvement**: add a dedicated unit test asserting the `narration_apply.py` floor emits its "no NPC backs seated blue actor" warning on a genuine miss (currently covered only indirectly by the seeding invariant). Affects `tests/server/dispatch/test_opponent_brain_wiring.py`. *Found by Reviewer during re-review.*

## Impact Summary

**Upstream Effects:** 2 findings (2 Gap, 0 Conflict, 0 Question, 0 Improvement)
**Blocking:** 1 BLOCKING items — see below

**BLOCKING:**
- **Gap:** the stance directive derives the opponent's disposition from the pre-seat `threat_name`, which is empty in the frame_default and `npcs_present`-nonempty seating paths, silently defaulting to "hostile" and ignoring the seated opponent's disposition. Affects `sidequest/agents/subsystems/dogfight.py`.

- **Gap:** AC-4's "narrator" source half needs a stamp the Plan 3 doc omits. The plan's Task 3 snippet only stamps `source="fallback"` in the `if not narrator_legal` branch — but `test_narrator_committed_blue_is_sourced_narrator` requires the NORMAL (narrator-committed) blue `dogfight.maneuver_committed` span to carry `source="narrator"`. Dev must also stamp `source="narrator"` on the resolver/seam's narrator-path blue commit span. Affects `sidequest/server/dispatch/sealed_letter.py`.

### Downstream Effects

Cross-module impact: 2 findings across 2 modules

- **`sidequest/agents/subsystems`** — 1 finding
- **`sidequest/server/dispatch`** — 1 finding

### Deviation Justifications

5 deviations

- **Reused production fixtures instead of the plan's invented ones**
  - Rationale: Those helpers don't exist; the equivalents already do. Reusing them honors CLAUDE.md "Don't Reinvent" and targets the true production seam, so the RED fails on the real `missing 'blue' key` path.
  - Severity: minor
  - Forward impact: none — same seam, same behavior asserted.
- **Stance-directive test in a new story-owned file + a second (friendly) case**
  - Rationale: The 153-6 file is a DONE, green suite — appending 158-39 RED tests muddies story ownership and disturbs a passing file. The friendly case proves the stance is MOTIVATED by disposition (opposite attitude → opposite tendency), not a constant string.
  - Severity: minor
  - Forward impact: none — stronger AC-1 coverage, isolated ownership.
- **e2e folded into the wiring file, not a separate module**
  - Rationale: It shares the same fixtures/helpers as the single-turn wiring test; a separate module would duplicate the harness for one test.
  - Severity: minor
  - Forward impact: none.
- **Nothing-affordable branch returns the cheapest LEGAL maneuver, not a preference pick**
  - Rationale: TEA's test encodes the correct floor: if nothing is in budget, minimize the energy deficit; attitude preference is moot when no move can be afforded. The plan's snippet disagreed with its own test; the test (the contract) wins.
  - Severity: minor
  - Forward impact: none — only changes behavior in the all-unaffordable corner; the affordable path is unchanged.
- **OTEL source threaded through the resolver (single emitter), not stamped as a separate seam span**
  - Rationale: A separate seam-stamped span would double-emit blue commits and leave the resolver's own blue span sourceless — polluting the lie-detector. Threading through the single emitter makes BOTH the narrator path (`source="narrator"`) and the fallback path (`source="fallback"`) truthful, satisfying TEA's narrator-source finding.
  - Severity: minor
  - Forward impact: none — additive optional kwargs (default `narrator`); the one other resolver caller is unaffected.

## Design Deviations

### TEA (test design)
- **Reused production fixtures instead of the plan's invented ones**
  - Spec source: docs/superpowers/plans/2026-06-26-dogfight-rebuild-plan-3-opponent-brain.md, Task 3/5
  - Spec text: "from tests.fixtures.dogfight_playtest_encounter import make_seated_dogfight_snapshot" / "Build `_drive_sealed_letter_turn`"
  - Implementation: Tests drive the REAL existing fixtures (`make_dogfight_playtest_state`, `drive_dogfight_turn`) and call `_apply_narration_result_to_snapshot` directly with a red-only `BeatSelection`; no new `make_seated_dogfight_snapshot`/`_drive_sealed_letter_turn` helpers.
  - Rationale: Those helpers don't exist; the equivalents already do. Reusing them honors CLAUDE.md "Don't Reinvent" and targets the true production seam, so the RED fails on the real `missing 'blue' key` path.
  - Severity: minor
  - Forward impact: none — same seam, same behavior asserted.
- **Stance-directive test in a new story-owned file + a second (friendly) case**
  - Spec source: docs/superpowers/plans/...-plan-3-opponent-brain.md, Task 4
  - Spec text: "Extend `tests/agents/subsystems/test_dogfight_dispatch_wiring.py` with a test..."
  - Implementation: New file `tests/agents/subsystems/test_dogfight_opponent_stance.py`; added a friendly-disposition case alongside the hostile one.
  - Rationale: The 153-6 file is a DONE, green suite — appending 158-39 RED tests muddies story ownership and disturbs a passing file. The friendly case proves the stance is MOTIVATED by disposition (opposite attitude → opposite tendency), not a constant string.
  - Severity: minor
  - Forward impact: none — stronger AC-1 coverage, isolated ownership.
- **e2e folded into the wiring file, not a separate module**
  - Spec source: docs/superpowers/plans/...-plan-3-opponent-brain.md, Task 5
  - Spec text: "Create `tests/server/dispatch/test_opponent_brain_e2e.py`"
  - Implementation: The multi-turn "never wedges" e2e lives as `test_opponent_never_wedges_across_blue_omitted_turns` inside `test_opponent_brain_wiring.py`.
  - Rationale: It shares the same fixtures/helpers as the single-turn wiring test; a separate module would duplicate the harness for one test.
  - Severity: minor
  - Forward impact: none.

### Dev (implementation)
- **Nothing-affordable branch returns the cheapest LEGAL maneuver, not a preference pick**
  - Spec source: docs/superpowers/plans/2026-06-26-dogfight-rebuild-plan-3-opponent-brain.md, Task 2 (impl snippet) + `tests/game/test_dogfight_brain.py::test_nothing_affordable_at_all_returns_cheapest_legal`
  - Spec text: plan impl did `pool = affordable or maneuvers` then applied the attitude preference over the whole pool.
  - Implementation: When no maneuver is affordable, `select_opponent_maneuver` short-circuits to `min(maneuvers, key=(energy_cost, id))` — the cheapest legal move — instead of applying attitude preference (which would pick the priciest offensive move for a hostile ace).
  - Rationale: TEA's test encodes the correct floor: if nothing is in budget, minimize the energy deficit; attitude preference is moot when no move can be afforded. The plan's snippet disagreed with its own test; the test (the contract) wins.
  - Severity: minor
  - Forward impact: none — only changes behavior in the all-unaffordable corner; the affordable path is unchanged.
- **OTEL source threaded through the resolver (single emitter), not stamped as a separate seam span**
  - Spec source: docs/superpowers/plans/...-plan-3-opponent-brain.md, Task 3 + TEA Delivery Finding (narrator-path source)
  - Spec text: plan stamped a separate `dogfight_maneuver_committed_span(..., source="fallback")` at the seam ONLY in the `if not narrator_legal` branch.
  - Implementation: Added `commit_sources: dict[str,str]` + `blue_attitude: str` kwargs to `resolve_sealed_letter_lookup`; the resolver (the existing single emitter of the red/blue `maneuver_committed` spans) stamps `source` per role and `attitude` on blue. The seam computes source (`narrator`/`substituted`/`fallback`) + attitude and passes them in.
  - Rationale: A separate seam-stamped span would double-emit blue commits and leave the resolver's own blue span sourceless — polluting the lie-detector. Threading through the single emitter makes BOTH the narrator path (`source="narrator"`) and the fallback path (`source="fallback"`) truthful, satisfying TEA's narrator-source finding.
  - Severity: minor
  - Forward impact: none — additive optional kwargs (default `narrator`); the one other resolver caller is unaffected.

### Reviewer (audit)
- **TEA: Reused production fixtures instead of the plan's invented ones** → ✓ ACCEPTED by Reviewer: the real `make_dogfight_playtest_state`/`drive_dogfight_turn` + direct seam call target production code and honor "Don't Reinvent"; sound.
- **TEA: Stance-directive test in a new story-owned file + a friendly case** → ✓ ACCEPTED by Reviewer: isolates story ownership and the friendly/hostile pair strengthens AC-1 coverage. (Note: neither case exercises the F1 seating miss — that gap is captured as the rework's required test, not a deviation fault.)
- **TEA: e2e folded into the wiring file** → ✓ ACCEPTED by Reviewer: shared harness, no value in a separate module.
- **Dev: Nothing-affordable → cheapest legal maneuver** → ✓ ACCEPTED by Reviewer: the test is the contract; minimizing the deficit is the correct ADR-006 floor; verified against `test_nothing_affordable_at_all_returns_cheapest_legal`.
- **Dev: OTEL source threaded through the resolver (single emitter)** → ✓ ACCEPTED by Reviewer: avoids double-emission and sourceless blue spans; gives both narrator and fallback paths truthful `source`; additive optional kwargs, one caller. Sound.

## TEA Assessment

**Tests Required:** Yes
**Reason:** New engine behavior (opponent-brain maneuver selection + deterministic fallback + OTEL) across pure logic, model/loader, the sealed-letter seam, and the dispatch subsystem — all testable.

**Test Files:**
- `tests/game/test_dogfight_brain.py` — pure disposition-weighted policy: motivation (hostile→offensive, friendly→evasive), energy affordability gate, seeded determinism, always-legal firewall floor, fail-loud empty menu, input-purity. (Task 2)
- `tests/genre/test_maneuver_loading.py` — `ManeuverDef` model (class alias, energy_cost default/negative) + loader resolves `maneuvers` onto the dogfight `ConfrontationDef` (fixture pack). (Task 1)
- `tests/server/dispatch/test_opponent_brain_wiring.py` — the mandatory wiring test: missing-blue → disposition fallback (no `missing 'blue'` ValueError), OTEL `source=fallback`+`attitude`; narrator path `source=narrator`; multi-turn never-wedges e2e; committed span routed to the GM panel. (Tasks 3 + 5)
- `tests/agents/subsystems/test_dogfight_opponent_stance.py` — `run_dogfight_dispatch` emits a disposition-motivated opponent stance directive (hostile→press, friendly→disengage). (Task 4)

**Tests Written:** 24 tests covering 5 ACs
**Status:** RED (verified via testing-runner, serial `-n0`)
- 2 files fail at COLLECTION (intended): `ModuleNotFoundError: sidequest.game.dogfight_brain`, `ImportError: ManeuverDef` — the modules Dev creates.
- `test_opponent_brain_wiring.py`: 3 FAIL (`missing 'blue' key` ValueError ×2; narrator-source assertion), 1 PASS (span-routing regression guard — the lie-detector surface already exists).
- `test_dogfight_opponent_stance.py`: 2 FAIL (empty directives).
- Zero broken tests — all failures are legitimate missing-feature failures.

### AC → Test Coverage

| AC | Behavior | Test(s) | Status |
|----|----------|---------|--------|
| 1 | Narrator-motivated selection from the legal menu | `test_hostile_presses_offensive_when_affordable`, `test_friendly_disengages_never_presses_offense`, `test_hostile_opponent_emits_press_stance_directive`, `test_friendly_opponent_emits_disengage_stance_directive` | RED |
| 2 | Positioning/resolution firewall (brain outputs only a maneuver id) | `test_firewall_output_is_only_a_maneuver_id`, `test_always_returns_a_legal_maneuver`, `test_never_returns_an_unaffordable_maneuver_when_an_affordable_one_exists` | RED |
| 3 | Deterministic disposition fallback (floor, distinguishable) | `test_deterministic_for_same_inputs`, `test_seed_is_the_only_nondeterminism_source`, `test_missing_blue_maneuver_falls_back_to_disposition_pick` | RED |
| 4 | OTEL `dogfight.maneuver_committed` carries `maneuver_id`+stance source | `test_missing_blue_...` (source=fallback+attitude), `test_narrator_committed_blue_is_sourced_narrator`, `test_maneuver_committed_span_is_routed_for_gm_panel` | RED (routing guard green) |
| 5 | Wiring — live end-to-end, never wedges | `test_opponent_never_wedges_across_blue_omitted_turns`, `test_loader_resolves_maneuvers_onto_dogfight_def` | RED |

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| CLAUDE.md No Silent Fallbacks (python #1) | `test_empty_menu_raises_not_silent` (raise, not fabricate), `test_missing_blue_...` (loud fallback via OTEL, not silent default) | failing |
| OTEL Observability Principle (lie-detector) | `test_missing_blue_...` (source/attitude), `test_narrator_committed_...` (source=narrator), `test_maneuver_committed_span_is_routed_for_gm_panel` | failing (routing guard passing) |
| Every Test Suite Needs a Wiring Test | `test_missing_blue_...` (seam), `test_loader_resolves_maneuvers_...` (loader), stance tests (dispatch) | failing |
| No Source-Text Wiring Tests | all wiring proven via behavior + OTEL spans + real fixtures — zero source greps | compliant |
| Resume-safe randomness (ADR-128) | `test_deterministic_for_same_inputs`, `test_seed_is_the_only_nondeterminism_source` | failing |
| Purity / no shared-state mutation (python #2 adjacent) | `test_does_not_mutate_the_input_menu` | failing |
| Test quality — meaningful assertions (python #6) | self-check: every test asserts a specific value/membership; no `assert True`/bare-truthy/`let _ =` | pass |

**Rules checked:** 7 applicable rules have test coverage (path/resource/deserialization/input-validation/deps checks N/A for this pure-logic + directive story).
**Self-check:** 0 vacuous tests (every assertion checks a specific value, membership, exception type, or non-emptiness with content).

**Serial-run note for Dev:** the OTEL span tests need `-n0` (in-memory exporter + monkeypatched module tracer); run `uv run pytest tests/game/test_dogfight_brain.py tests/genre/test_maneuver_loading.py tests/server/dispatch/test_opponent_brain_wiring.py tests/agents/subsystems/test_dogfight_opponent_stance.py -n0 -v`.

**Handoff:** To Dev (Inigo Montoya) for implementation. Two delivery-finding gaps above are load-bearing: (1) stamp `source="narrator"` on the narrator-path blue span; (2) add the `maneuvers: {_from:}` pointer to the FIXTURE pack rules.yaml, not just live content.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (sidequest-server, branch `feat/158-39-dogfight-opponent-brain`, commit `17813969`, pushed):**
- `sidequest/game/dogfight_brain.py` (new) — pure `select_opponent_maneuver` policy: attitude→class preference, energy affordability gate, seeded resume-safe tie-break, always-legal floor (cheapest-legal when nothing affordable), fail-loud on empty menu.
- `sidequest/genre/models/rules.py` — `ManeuverDef` model (`class` alias, `energy_cost` default 0, `extra="ignore"`) + `ConfrontationDef.maneuvers` field.
- `sidequest/genre/loader.py` — resolve a `maneuvers: {_from:}` pointer, lifting the sub-file's inner `maneuvers` list onto the def (fail-loud if absent).
- `sidequest/server/dispatch/sealed_letter.py` — `resolve_sealed_letter_lookup` gains optional `commit_sources` + `blue_attitude`; the (single-emitter) `maneuver_committed` spans now stamp `source` per role + `attitude` on blue.
- `sidequest/server/narration_apply.py` — sealed-letter seam: substitute the disposition fallback for a missing/illegal blue commit before resolve (never wedges), threading `commit_sources`+`blue_attitude` into the resolver.
- `sidequest/agents/subsystems/dogfight.py` — `run_dogfight_dispatch` emits a disposition-motivated opponent stance directive on a successful seat.
- `tests/fixtures/packs/swn_test_pack/rules.yaml` — dogfight def gains the `maneuvers: {_from:}` pointer (symlinked as `tests/fixtures/genre_packs/...`).
- The 4 TEA test files — lint (Yoda-condition flip) + format only.

**Files Changed (sidequest-content, branch `feat/158-39-dogfight-opponent-brain`, commit `6be626d`, pushed):**
- `genre_packs/space_opera/rules.yaml` — live dogfight def gains the `maneuvers: {_from:}` pointer (production parity with the fixture).

**Tests:** 26/26 target tests passing (GREEN, verified `-n0`). Regression sweep `-k "dogfight or sealed_letter or maneuver"`: **184 passed, 3 failed, 2 skipped** — the 3 failures are PRE-EXISTING (confirmed failing on `develop` with my changes stashed; see Delivery Findings → Dev), zero new regressions. `ruff check` + `ruff format --check` clean on all changed files.

**All 5 ACs met:** narrator-motivated selection (stance directive + policy motivation) · firewall (brain returns only a maneuver id; SWN still resolves) · deterministic disposition fallback (seeded, distinguishable) · OTEL `dogfight.maneuver_committed` carries `source`+`attitude` · live wiring (seam fallback never wedges across turns + loader wiring).

**Two deviations from the plan** (logged above): the nothing-affordable→cheapest-legal fix (plan impl disagreed with its own test) and OTEL source threaded through the resolver (single emitter, both paths sourced) rather than a separate seam span.

**Handoff:** To Reviewer (Westley) for code review.

### Dev Rework — Review Round-Trip 1 (commit `89f30d44`, pushed)

**Addressed Reviewer F1 (HIGH, blocking):** the stance directive in `sidequest/agents/subsystems/dogfight.py` now resolves the opponent from the **seated** `encounter.actors` (`side=="opponent"`), mirroring the engine floor in `narration_apply.py`, instead of the pre-seat `threat_name` (empty in the frame_default / `npcs_present` paths). No more silent "hostile" default; when no NPC backs the seated opponent it logs a warning and defaults to "neutral" to agree with the floor.

**Addressed Reviewer F2 (MEDIUM, non-blocking):** added a `logger.warning` in the `narration_apply.py` engine floor when the opponent-NPC lookup misses, so a seeding-invariant break is observable rather than silently smoothed. Both defaults now agree ("neutral") and both log the miss.

**Left Reviewer F3 (LOW, Question):** `viewer_energy` default of 60 — confirmed the only authored dogfight starting-state (`merge`) seeds `viewer_energy: 60`, so the default matches the canonical fresh value and never papers over a real gap today. Noted, no change; carried as a Question for future non-`merge` starting states.

**New regression test:** `tests/agents/subsystems/test_dogfight_opponent_stance.py::test_stance_reflects_seated_opponent_when_router_did_not_name_it` — a friendly opponent seated via `npcs_present` (empty `threat_name`) must yield a disengage directive and never a blind "hostile". Fails on the old lookup, passes on the fix.

**Tests:** 27/27 target green (3 stance tests incl. the new F1 case). Regression sweep: 185 passed, the same 3 pre-existing failures, 0 new. Lint/format clean on all three changed files.

**Handoff:** Back to Reviewer (Westley) for re-review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (26/26 target green; 184 regression pass, only the 3 known pre-existing fails; ruff+pyright clean) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — edges covered by Reviewer (turn_seed modulo, energy default, nothing-affordable floor) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 (1 high, 1 medium, 1 low) | confirmed 1 (F1 HIGH), confirmed-noted 2 (F2/F3 non-blocking) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — test quality covered by Reviewer; noted the stance test's matching-name blind spot |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — comment accuracy covered by Reviewer; flagged the misleading "seated opponent" comment |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — type design covered by Reviewer (ManeuverDef alias/extra, optional kwargs) — clean |
| 7 | reviewer-security | Yes | clean | 0 (path-safe `_from` reuse, safe_load, no injection surface) | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — no over-engineering found by Reviewer |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — lang-review 1-13 enumerated by Reviewer (see Rule Compliance) |

**All received:** Yes (3 enabled returned; 6 disabled pre-filled)
**Total findings:** 1 confirmed blocking (HIGH), 2 confirmed non-blocking (MEDIUM/LOW), 0 dismissed

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] [SILENT] [RULE] [DOC] | The stance directive looks up the opponent NPC by the **pre-seat** `threat_name`, which is `""` in the common seating paths (`npcs_present` non-empty → guard `if threat and not actor_list` is False; frame_default seat → no `threat` named). The lookup misses, and `stance` silently defaults to `"hostile"` — ignoring the actually-seated opponent's disposition, with no log/OTEL noting the miss. This half-wires AC-1 ("narrator-motivated ... motivated by its disposition") for the common paths and violates CLAUDE.md **No Silent Fallbacks**. The engine floor in `narration_apply.py:6068-6076` does it correctly (looks up by the **seated** `blue_actor.name`). | `sidequest/agents/subsystems/dogfight.py:185-186` | Derive `opp` from the seated opponent actor (`snapshot.encounter.actors`, `side=="opponent"` / `role=="blue"`) after `instantiate_encounter_from_trigger` returns — mirror the `narration_apply.py` lookup. Then TEA adds a test seating an opponent whose name ≠ `threat_name` (frame_default or `npcs_present`-nonempty) asserting the directive reflects the seated disposition, not a blind "hostile". |

### Observations (subagent-tagged + own)

- `[SILENT]` **F1 (HIGH, CONFIRMED — see table):** stance directive silent "hostile" default at `dogfight.py:185-186`. Verified reachable: `threat_name` only set under `if threat and not actor_list` (`dogfight.py:131`); frame_default and `npcs_present`-nonempty paths leave it `""`.
- `[SILENT]` **F2 (MEDIUM, non-blocking):** `narration_apply.py:6074-6076` `blue_attitude` defaults to `"neutral"` when `opp_npc` is None. In practice `_seed_combat_hp_depletion_to_npcs` seeds a backing Npc for every opponent actor, so this resolves today — but a future seeding-invariant break would be silently smoothed to "neutral" with no signal. Recommend a `logger.warning`/OTEL attr on the miss. Also note the inconsistency: this defaults "neutral" while F1 defaults "hostile" for the same class of miss.
- `[SILENT]` **F3 (LOW, non-blocking):** `narration_apply.py:6091` `viewer_energy` defaults to 60 with no signal if the key is absent. Matches the canonical `merge` starting value (`descriptor_schema.yaml: viewer_energy: 60`) so it's unlikely to paper over a real gap, but a non-`merge` seat that omits it would silently assume full energy into the affordability gate. Noting only.
- `[DOC]` The `dogfight.py:180-184` comment claims the directive surfaces "the **seated** opponent ace's stance — derived from its disposition," but the code derives it from the pre-seat `threat_name` — the comment is misleading given F1. Fixing F1 makes the comment true.
- `[TEST]` **VERIFIED (with gap):** the 4 test files have meaningful assertions, no vacuous checks — evidence: `test_dogfight_brain.py` asserts specific ids/membership; `test_does_not_mutate_the_input_menu` (`:647-652`) genuinely catches in-place reordering. **Gap:** `test_dogfight_opponent_stance.py` seeds `Npc.core.name == opponent.name`, so it never exercises the F1 miss (frame_default / renamed / npcs_present seat). The rework test must cover that.
- `[SEC]` **VERIFIED:** the new `maneuvers: {_from:}` resolution reuses the path-safe `_resolve_from_pointer` (absolute-path/`..`/nested-`_from` rejects, `yaml.safe_load`) — `loader.py:328-333`. No new file-read surface, no injection reaching a shell/SQL/path. Complies with lang-review #8/#11.
- `[EDGE]` **VERIFIED:** `select_opponent_maneuver` `turn_seed % len(candidates)` is index-safe for any int (`turn_manager.interaction` ≥ 1); empty menu raises (`dogfight_brain.py:96`); nothing-affordable returns cheapest-legal (`:104`) — all legal ids. Evidence: `test_always_returns_a_legal_maneuver` sweeps energy −20..999.
- `[TYPE]` **VERIFIED:** `ManeuverDef` uses `extra="ignore"` + required `maneuver_class` (alias `class`, no default) — a typo'd `class:` key raises a pydantic `field required` (loud), not a silent drop. Optional kwargs `commit_sources=None`/`blue_attitude=""` avoid mutable defaults (lang-review #2). `rules.py:168-180`, `sealed_letter.py:98-99`.
- `[SIMPLE]` **VERIFIED:** the fallback seam and brain are minimal — data-driven preference/tendency dicts, no dead code, no over-engineering. `_sources = commit_sources or {}` single-emitter pattern is the simplest correct approach.
- `[RULE]` **Rule Compliance** (see section below): lang-review python #1-13 compliant EXCEPT #1-adjacent "No Silent Fallbacks" — F1 is a rule-matching violation, hence CONFIRMED and blocking.

### Rule Compliance (lang-review/python.md, enumerated)

1. Silent exception swallowing — **compliant** (no bare/`pass` excepts; loader/brain/seam raise loudly). BUT the broader "No Silent Fallbacks" principle → **F1 violation** (silent "hostile" default).
2. Mutable default arguments — compliant (`commit_sources=None`, `blue_attitude=""`; brain params no mutable default).
3. Type annotations — compliant (all new public fns/fields annotated).
4. Logging — compliant (no new error paths that need logging beyond raises; F2 recommends adding a warning — non-blocking).
5. Path handling — compliant (reuses `_resolve_from_pointer`; no new string paths).
6. Test quality — compliant on assertions; test-coverage gap for F1 (see [TEST]).
7. Resource leaks — N/A (no new file/conn handles in new code).
8. Unsafe deserialization — compliant (`yaml.safe_load` only; no eval/exec/pickle).
9. Async pitfalls — compliant (stance-directive code is sync, no blocking calls, no missing awaits in `run_dogfight_dispatch`).
10. Import hygiene — compliant (local import of `select_opponent_maneuver` avoids a cycle; no star imports).
11. Input validation — compliant (maneuver ids from authored YAML + structured beat_selections; brain filters to legal set).
12. Dependency hygiene — N/A (no dep changes).
13. Fix-introduced regressions — N/A.

### Devil's Advocate

Assume this code is broken. The load-bearing mechanic — the engine fallback in `narration_apply.py` — is actually solid: it uses the post-seat `blue_actor.name`, filters to the legal set, stamps a truthful OTEL `source`, and the multi-turn test proves it never wedges. The dangerous part is the part that *looks* like a feature but behaves like a constant. The stance directive advertises itself (in code comment and Dev assessment) as "motivated by the seated opponent's disposition," and a career GM reading the GM panel would trust it. But in the two most common ways a dogfight seats — a frame-default enemy fighter (no router-named opponent) and a scene where NPCs are already present (`actor_list` non-empty) — `threat_name` is the empty string, the NPC lookup returns nothing, and the narrator is handed an authoritative "the enemy ace presses the attack (disposition: hostile)" directive that was never checked against any actual disposition. A confused-but-worse case: a world author writes a *reluctant* or *conscripted* pilot (friendly/neutral disposition) as the dogfight opponent for a story beat; the engine floor would correctly steer that pilot to disengage, while the narrator directive simultaneously insists it "presses the attack." The two halves of AC-1 now contradict each other for the same opponent on the same turn — exactly the kind of convincing-prose-with-no-mechanical-backing the OTEL lie-detector exists to prevent, except here it's invisible because the stance lookup emits no span at all. What would a stressed system produce? Nothing louder — it degrades to "hostile" silently on every miss. The malicious/edge input isn't even adversarial; it's the ordinary frame-default path the sibling 153-6 test already exercises (`test_dogfight_no_scene_opponent_seats_frame_default`). This is a genuine half-wire of AC-1, cheaply fixed by copying the lookup pattern that already exists 40 lines away in the engine floor. F2/F3 are lower-stakes (defensive defaults that resolve in practice) but reinforce the pattern: the new code reaches for a plausible constant when a lookup misses instead of failing loud or logging. Fix F1; strongly consider F2's observability.

**Handoff:** Back to TEA (Fezzik) for a failing test on the F1 seating paths, then Dev fix.

---

## Subagent Results

*(Re-review — Round-Trip 1, on the rework delta `17813969..89f30d44`)*

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (27/27 target; regression = 3 known pre-existing only; ruff+format clean; pyright no new errors — verified same 37 on parent) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — edges re-checked by Reviewer (seated non-None guard, opp_actor None guard) |
| 3 | reviewer-silent-failure-hunter | Yes | clean | 0 (F1 verified FIXED — test empirically fails pre-fix, passes post-fix; residual default is logged; side==opponent≡role==blue for dogfight) | confirmed fix; 1 informational note (no dedicated unit test for the floor's F2 log branch) — non-blocking |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled — re-checked by Reviewer; new F1 test is a proven regression guard |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled — the reworded comment now matches the code (reads the seated actor) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled — pyright clean on the delta; no new type surface |
| 7 | reviewer-security | Yes | clean | 0 | Reviewer re-verified: the rework touches only opponent-resolution logic + two `logger.warning` lines + a test — no new file read / deserialization / input boundary / injection surface. Security posture unchanged from the first review's clean result. |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled — fix is minimal (mirrors the existing floor lookup); no over-engineering |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled — No Silent Fallbacks now satisfied (the default is logged); enumerated below |

**All received:** Yes (2 enabled subagents re-run on the rework delta; security re-verified by Reviewer as unaffected)
**Total findings:** 0 blocking; the sole prior blocker (F1) is resolved and independently verified; 1 informational (floor F2-log branch has no dedicated unit test — non-blocking)

## Reviewer Assessment

*(Re-review — Round-Trip 1)*

**Verdict:** APPROVED

The sole blocker (F1, HIGH) is resolved at its root and independently verified. The stance directive now resolves the opponent from the **seated** actor (`seated.actors`, `side=="opponent"`) and looks it up in `snapshot.npcs` by that post-seat name — mirroring the engine floor — instead of the pre-seat router `threat_name` that was empty in the frame_default and `npcs_present` paths. The residual "no opponent NPC" default is now `"neutral"` (agreeing with the floor) **and logged** (`logger.warning`), so it is loud, not silent. F2's floor lookup got the same warning. F3 (`viewer_energy=60`) was addressed with rationale (matches the only authored `merge` starting-state) and carried as a non-blocking Question.

- `[SILENT]` **F1 RESOLVED (VERIFIED):** `dogfight.py:200-206` reads the seated opponent; the miss is logged (`:207-214`), default `"neutral"`. Silent-failure-hunter empirically confirmed the fix (test fails on parent `17813969`, passes on `89f30d44`). No new silent fallbacks.
- `[SILENT]` **F2 addressed:** `narration_apply.py:6074-6079` now logs the "neutral" default miss. Informational (non-blocking): no dedicated unit test asserts this floor branch's warning — covered indirectly by the seeding invariant; acceptable, noted for a future hardening pass.
- `[TEST]` **VERIFIED:** `test_stance_reflects_seated_opponent_when_router_did_not_name_it` is a *proven* regression guard — the hunter reverted to pre-fix code and observed it FAIL, then pass on the fix. It exercises the real `npcs_present` F1 trigger (empty `threat_name`), not a hand-matched name.
- `[EDGE]` **VERIFIED:** `seated` is guaranteed non-None/typed at the stance code (guard `dogfight.py:169`); `seated.actors` defaults to `[]` (never None); `opp_actor.name if opp_actor is not None else None` avoids AttributeError. Evidence: preflight pyright 0-new; hunter's arity trace (`SealedLetterArityError` guarantees exactly one Other).
- `[TYPE]` **VERIFIED:** no new type errors (pyright 37 = same on parent, none in `dogfight.py`). Additive `logger.warning` + reworked lookup only.
- `[DOC]` **VERIFIED:** the `dogfight.py:180-191` comment now truthfully says the opponent is resolved from the seated actor — the misleading-comment finding from review 1 is cleared by the fix.
- `[SEC]` **VERIFIED (re-verified):** no security-relevant change in the rework; the maneuvers `_from` path-safety and safe_load posture are untouched.
- `[SIMPLE]` **VERIFIED:** the fix is the minimal correct change — it copies the floor's lookup shape; no dead code, no over-engineering.
- `[RULE]` **Rule Compliance:** the review-1 enumeration stands; the one rule-matching gap ("No Silent Fallbacks" via the silent "hostile" default) is now compliant — the default is logged and the lookup is correct. All lang-review python #1-13 compliant.

**Data flow traced:** a ship-combat intent → `run_dogfight_dispatch` seats the dogfight → the stance directive reads the SEATED opponent actor → its `snapshot.npcs` disposition → a `must_narrate` directive whose stance matches the engine floor's fallback attitude for the same opponent (no more contradiction). Safe.

**Deviation audit:** unchanged from review 1 — all five deviations remain ✓ ACCEPTED; the rework introduced no new spec deviations (the F1 fix aligns the code *with* AC-1).

**Handoff:** To SM (Vizzini) for finish-story.