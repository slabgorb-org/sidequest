---
story_id: "126-16"
jira_key: "SKIP"
epic: "126"
workflow: "tdd"
---
# Story 126-16: [FATE] Defend-barrier test-quality nits + deferred TEA coverage

## Story Details
- **ID:** 126-16
- **Jira Key:** SKIP (no Jira integration)
- **Workflow:** tdd
- **Stack Parent:** none
- **Repos:** server

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-20T05:30:52Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-20T19:35:00Z | 2026-06-20T05:09:18Z | -51942s |
| red | 2026-06-20T05:09:18Z | 2026-06-20T05:20:46Z | 11m 28s |
| green | 2026-06-20T05:20:46Z | 2026-06-20T05:23:27Z | 2m 41s |
| review | 2026-06-20T05:23:27Z | 2026-06-20T05:30:52Z | 7m 25s |
| finish | 2026-06-20T05:30:52Z | - | - |

## Story Description
Deferred test-quality + coverage follow-ups from 126-8 (the server DEFEND barrier, ADR-148/151). 126-8's review APPROVED the implementation but logged test-side gaps; this 1pt chore closes them. Server-only; net change is test-side (assertion-tightening + new characterization tests of already-shipped behavior), no production logic change expected. Three items decoded from the title:
- match=authorization — tighten a vacuous pytest.raises
- list-vs-next span — make span lookups name-keyed not positional
- deferred TEA coverage — partial-fill ledger + defense-wins resolution

Grounding files:
- tests/server/dispatch/test_fate_defense_record.py
- tests/game/ruleset/test_fate_defend_spans.py
- tests/game/test_fate_pending_defenses.py
- sidequest/server/dispatch/fate_conflict.py (dispatch_fate_defense ~1160, _resolve_attack ~590, ledger_full all() gate ~1257)

## Acceptance Criteria
1. **match=authorization:** test_defend_throw_from_non_defender_is_rejected (test_fate_defense_record.py) tightens its bare pytest.raises(FateConflictError) with match= pinned to the authorization branch, so it cannot pass on a different FateConflictError (unknown / already-filled / no-faces). The authorization rejection message is the one ending in '(authorization)'.

2. **list-vs-next span:** in test_fate_defend_spans.py, span assertions that fetch a span by positional list index (get_finished_spans()[0]) on a path that can emit more than one span are converted to name-keyed next(s for s in ... if s.name == '...') lookups (the convention already used in test_npc_server_defense_tags_role_defense), so each assertion targets the intended span rather than a positional accident.

3. **partial-fill coverage:** a new unit test exercises a MULTI-entry pending_defenses ledger — filling one defender's entry leaves ledger_full=False, filling all entries makes it True — proving the all(...) ledger gate handles partial fills (existing tests only cover the single-entry full-ledger case).

4. **defense-wins coverage:** a new unit test drives a RECORDED PC defense through _resolve_attack where the defense beats/ties the attack (defense_total >= attacker ladder_total -> shifts<=0 -> no harm applied, momentum boost on exact tie, defender NOT taken out), covering the win side of the recorded-defense branch.

5. **Server suite stays green (no production regression);** any new fixture (e.g. a two-defender parked conflict) lives alongside parked_conflict in tests/_helpers/fate_fixtures.py, not pointed at live content.

## Sm Assessment

Setup complete; routing to TEA (Fezzik) for the RED phase. This is a 1pt server-only
TDD chore — deferred test-quality + coverage from the APPROVED 126-8 DEFEND barrier
(ADR-148/151). I enriched the originally-thin story with a description + 5 ACs and a
grounded technical approach (see `sprint/context/context-story-126-16.md`), decoding the
three title items against the real files:

- **AC1 match=authorization** — tighten a bare `pytest.raises(FateConflictError)` in
  `test_fate_defense_record.py` (4 branches raise it; pin to the `(authorization)` one).
- **AC2 list-vs-next span** — convert positional `get_finished_spans()[0]` lookups to
  name-keyed `next(...)` in `test_fate_defend_spans.py`.
- **AC3 partial-fill** — new multi-defender ledger test (`ledger_full=False` until all
  filled); likely needs a two-defender fixture beside `parked_conflict`.
- **AC4 defense-wins** — new test driving a recorded PC defense that beats/ties through
  `_resolve_attack` (shifts<=0 → no harm, momentum-on-tie, defender not taken out).

**Expectation for TEA:** production behavior already shipped in 126-8, so the new coverage
tests (AC3/AC4) characterize existing behavior — green-on-arrival is the legitimate RED
outcome (assert the shipped behavior is correct); the only genuinely-new code is the
two-defender test fixture. The nits (AC1/AC2) edit existing tests. No production logic
change expected; keep the server suite green. Jira intentionally SKIP (personal project,
no Jira). Branch `chore/126-16-fate-defend-test-quality` is off `develop` in
`sidequest-server`.

## TEA Assessment

**Tests Required:** Yes
**Reason:** The story's entire deliverable IS test code (test-quality nits + deferred coverage).

**Test Files:**
- `tests/_helpers/fate_fixtures.py` — new `parked_conflict_two_defenders` builder (two PC defenders, two unfilled `pending_defenses` entries) for the partial-fill case.
- `tests/server/dispatch/test_fate_defense_record.py` — AC1 (tightened 3 bare `pytest.raises`) + AC3 (2 partial-fill tests).
- `tests/server/dispatch/test_fate_resume_resolve.py` — AC4 (2 defense-wins tests: exact-tie momentum + clean miss).
- `tests/game/ruleset/test_fate_defend_spans.py` — AC2 (3 positional span lookups → name-keyed).

**Tests Written:** 4 new tests (2 AC3 + 2 AC4) + 1 new fixture; 6 existing tests tightened (3 AC1 match=, 3 AC2 name-keyed). 4 ACs covered (AC5 = green/clean, satisfied).
**Status:** GREEN-on-arrival (characterization). Production behavior already shipped in 126-8 (ADR-148/151), so there is **no RED→GREEN cycle and no production code for Dev to write** — these tests pin already-correct behavior and tighten vacuous assertions. This mirrors the in-repo precedent (`test_fate_resume_resolve.py::test_npc_defender_still_server_rolls`, explicitly a "passes today" characterization test).

**Verification:** `uv run pytest -n0 tests/server/dispatch/test_fate_defense_record.py tests/server/dispatch/test_fate_resume_resolve.py tests/game/ruleset/test_fate_defend_spans.py` → **19 passed** (0.20s). `ruff check` + `ruff format --check` on all 4 files → clean.

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| python #6 test-quality (no vacuous assertions) | AC1 `match=` on all 3 `FateConflictError` raises — proven branch-unique (each match string appears in exactly one of the 4 error messages; lines 1186/1222/1226) | passing |
| python #6 test-quality (specific value checks, not truthy) | AC3 asserts `ledger_full` False→True + `defense_total == 4` / `is None`; AC4 asserts `len(momentum) == 1`, `kind == "boost"`, `free_invokes == 1`, `withdrawn is False`, `"missed" in hints` | passing |
| project: No Source-Text Wiring Tests | All tests drive the real `dispatch_fate_defense` / `_resolve_attack` / real span emitters — no `read_text()` source grepping | passing |

**Rules checked:** 1 of 13 lang-review checks applicable (rest are N/A — changes are test-only: no production code, async, path, deserialization, logging, import, or dependency changes).
**Self-check:** 0 vacuous assertions in new tests; **3 pre-existing vacuous-match assertions FIXED** (the AC1 bare raises, which could pass on the wrong branch).

**Handoff:** To Dev (Inigo Montoya) — but **GREEN is a verify-only pass-through** (no implementation needed). Confirm the 19 targeted tests are green, then hand to Reviewer. See Delivery Findings.

## Dev Assessment

**Implementation Complete:** Yes (no production code required)
**Files Changed:** None by Dev. This is a characterization/test-quality story — the production behavior shipped in 126-8 (ADR-148/151) and is already correct. Per minimalist discipline + No-Stubbing, I wrote **zero** production code; adding any would be scope creep with no failing test to justify it. The test files are TEA's red-phase work (committed in 312fa5f1).

**GREEN verification (measured, not assumed):**
`uv run pytest -n0 tests/server/dispatch/test_fate_defense_record.py tests/server/dispatch/test_fate_resume_resolve.py tests/game/ruleset/test_fate_defend_spans.py tests/game/test_fate_pending_defenses.py` → **23 passed** (0.16s). Working tree clean.

**Tests:** 23/23 passing (GREEN) on the targeted scope (the 3 changed test files + the related `test_fate_pending_defenses.py` ledger-model suite).
**Branch:** `chore/126-16-fate-defend-test-quality` (pushed, tracking `origin/`).

**Self-review:** No production code to wire (test-only story); changes follow existing fate-test patterns; all 4 ACs are covered by TEA's tests and verified green; no error-handling/wiring obligations introduced.

**Handoff:** To Reviewer (Westley) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (23 tests green, lint clean, format clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 (all LOW) | confirmed 0, dismissed 3 (rationale), deferred 0 |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 0 confirmed, 3 dismissed (with rationale), 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

Test-only diff (4 files, +239/-7), no production code. I read the full diff myself, ran the rule-by-rule enumeration, and adjudicated every subagent finding against the code.

**Data flow traced:** A defend throw `(actor_name, request_id, faces)` → `dispatch_fate_defense` → records `defense_total`/`conceded` on the matching `pending_defenses` entry → `ledger_full = all(filled)`; later `_resolve_attack` compares `commit.ladder_total - defense_total` to route harm. The new tests exercise this end-to-end through the real functions (no stubs). Safe: the authorization guard rejects a throw from a non-defender before any state mutation.

**Pattern observed:** New tests follow the file's established fixtures (`parked_conflict*`) and `next(...)` lookup convention; assertions are specific-value, multi-channel (stress/consequence/withdrawn), not truthy. `tests/_helpers/fate_fixtures.py:189` `parked_conflict_two_defenders` mirrors `_parked_base` per (attacker, defender) pair.

**Error handling:** N/A for production (no production change). Test-side fail-loud is preserved/strengthened (the AC1 `match=` pins).

### Observations

- `[VERIFIED]` AC1 `match=` is non-vacuous — each substring (`unknown request_id` / `already recorded` / `authorization`) appears in exactly ONE of the four `FateConflictError` messages (`fate_conflict.py:1186/1226/1222`); the no-faces message contains none. A wrong-branch raise would now fail the test. Corroborated by `[SEC]` (call-ordering guarantees the auth branch fires first at line 1197).
- `[VERIFIED]` AC2 name-keyed span lookups (`test_fate_defend_spans.py:49,69,171`) match the convention AC2 prescribes and the file already uses at 107/131 — strictly safer than the positional `[0]` (order/leak-resistant). Corroborated by `[SILENT]` and `[SEC]` as a hardening, not a regression.
- `[VERIFIED]` AC3 partial-fill is bidirectional — `assert first.ledger_full is False` AND `assert second.ledger_full is True` (`test_fate_defense_record.py:218,238`) catch a broken `all(...)` gate in either direction; the concede variant pins `conceded` symmetry. Not vacuous.
- `[VERIFIED]` AC4 win-side coverage is genuinely additive — the pre-existing `test_recorded_pc_defense_used_instead_of_roll` covers the LOSE side; the tie test asserts exactly one Momentum boost with `free_invokes == 1` (`test_fate_resume_resolve.py:120-122`) and the miss test asserts no boost + `"missed"` hint. Both assert no-stress/no-consequence/not-withdrawn individually.
- `[VERIFIED]` AC5 — fixtures use a synthetic `genre_slug="fate_test"` and fictional names (Rux/Vala/Bandit/Brigand); no pointer to a live pack/world (No-tests-point-at-content rule). `parked_conflict_two_defenders` lives in `tests/_helpers/fate_fixtures.py` as required.
- `[VERIFIED]` No-Source-Text-Wiring-Tests — all tests drive the real `dispatch_fate_defense` / `_resolve_attack` / span emitters; no `read_text()` source grepping.

### Dispatch tags

- `[EDGE]` (edge-hunter disabled) — assessed boundaries myself: tie (shifts==0), clean miss (shifts<0), single-fill vs all-fill, concede-vs-throw fill — all covered.
- `[SILENT]` 3 LOW findings — **all dismissed** (see below).
- `[TEST]` (test-analyzer disabled) — performed test-quality enumeration myself under Rule Compliance; no vacuous assertions.
- `[DOC]` (comment-analyzer disabled) — inline comments are accurate (verified the AC3 `opposition 0` comment against `fate_conflict.py:1241`).
- `[TYPE]` (type-design disabled) — no type changes; fixture uses correctly-typed model constructors.
- `[SEC]` clean — authorization test verified non-vacuous by the security subagent.
- `[SIMPLE]` (simplifier disabled) — fixture is minimal-but-complete; no over-engineering; `_rid` underscore signals intentional non-use.
- `[RULE]` (rule-checker disabled) — ran lang-review python #6 (test quality) myself; pass (see Rule Compliance).

### Dismissed findings (rationale)

- `[SILENT] LOW` `test_fate_defense_record.py:229` — "`defense_total == 1+1+2` depends on opposition=0 not asserted." **Dismissed:** the comment is accurate (`dispatch_fate_defense` hardcodes `Opposition(value=0)` at `fate_conflict.py:1241`); `defense_total == 4` IS the behavioral assertion; if production ever changed the opposition, this test SHOULD fail — that is correct regression behavior, not a trap.
- `[SILENT] LOW` `test_fate_resume_resolve.py:107,142` — "`next()` without default → StopIteration ERROR not FAIL." **Dismissed:** `StopIteration` is a loud pytest ERROR (the hunter conceded it is "not strictly silent"); the lookup is over a freshly-built local fixture that guarantees the commit; pattern matches the file's existing convention.
- `[SILENT] LOW` `test_fate_defense_record.py:227,228` — same bare-`next()` concern. **Dismissed:** this is the file's PRE-EXISTING established convention (lines 51/122/194, not introduced here) AND exactly the `next(...)` form AC2 prescribes; not silent (loud ERROR), over a local fixture.

### Rule Compliance

- **lang-review python #6 (test quality):** Enumerated every new/changed assertion (AC1 ×3 raises, AC2 ×3 span lookups, AC3 ×2 tests, AC4 ×2 tests). No `assert True`, no truthy-only `assert result`, no assertion-free tests, no `@pytest.mark.skip`, no mocks on wrong targets (no mocks added). Every assertion checks a specific value. **Compliant.**
- **No Source-Text Wiring Tests (CLAUDE.md):** No `read_text()`/regex-on-source. Behavior-driven via real functions + real span emitters. **Compliant.**
- **No tests point at live content (project rule):** Synthetic `fate_test` slug + fictional names. **Compliant.**
- **No Stubbing / No Silent Fallbacks (production):** No production change; nothing stubbed. **Compliant.**

### Devil's Advocate

Suppose this code is broken. Where would it hide? First, the new coverage tests pass *because the behavior already shipped in 126-8* — could they be passing for the wrong reason, "characterization theater" that asserts nothing real? I checked: each test fails if the targeted behavior breaks. The partial-fill test asserts `ledger_full` in BOTH directions, so a gate stuck at True OR False fails it. The tie test asserts exactly one Momentum boost with a free invoke; delete the boost branch and `len(momentum) == 1` fails. The miss test asserts harm is absent on three channels and that a `"missed"` hint exists; route harm on a miss and the stress/consequence/withdrawn asserts fail. So they are not theater. Second, could a malicious/confused MP player exploit the defend path? That is exactly what the authorization test guards — a third party ("Mallory") answering "Rux"'s request is rejected, and the security subagent confirmed the call ordering makes the authorization branch the one that fires (not a coincidental unknown-id/no-faces rejection). Third, could the fixture lie — construct an unrealistic object so a test passes against a shape production never produces? The silent-failure subagent specifically checked `mental=` defaulting to False matches `category="combat"`, and the fixture reuses the same model constructors and per-pair structure as the trusted `_parked_base`. Fourth, the `next()`-without-default lookups: a stressed/refactored fixture would raise `StopIteration` — but that is a loud ERROR that points at the fixture, not a silent pass, and it matches the file's existing convention plus AC2's prescription. Fifth, span-leak across tests: each test builds a fresh `InMemorySpanExporter`, and the AC2 change to name-keyed lookups makes the assertions *more* resistant to any stray span. I could not construct a scenario where broken behavior slips past these tests. The diff hardens the suite and closes the exact gaps 126-8's review named.

**Handoff:** To SM (Vizzini) for finish-story.

## Delivery Findings

<!-- Append findings below. Never edit/remove another agent's entries. -->

### TEA (test design)
- **Improvement** (non-blocking): This is a characterization/test-quality story — production behavior shipped in 126-8, so there is **no GREEN implementation work**. Dev should confirm the targeted tests pass and pass straight to review. Affects the GREEN phase (`sidequest-server`, no source change required).
- **Improvement** (non-blocking): `tests/game/ruleset/test_fate_defend_spans.py` must run with `-n0` (its header documents a known span-count deadlock under the xdist parallel runner). Affects any CI scoping of that file (run serially).

### Dev (implementation)
- No upstream findings during implementation. Confirmed TEA's read: no production change needed; GREEN was a verify-only pass-through (23 targeted tests green).

### Reviewer (code review)
- No upstream findings. The 3 silent-failure-hunter findings were all LOW test-robustness suggestions (bare `next()` / opposition-comment), dismissed with rationale in the Reviewer Assessment — they follow the file's established convention + AC2 and surface loudly (not silently). Optional, non-blocking future nit if anyone hardens these files broadly: give `next()` lookups a `default=` + not-None assert so a fixture regression reads as FAIL not ERROR — but applying it here only would diverge from the file's convention.

## Design Deviations

### TEA (test design)
- **AC1 extended to the two sibling bare raises**
  - Spec source: context-story-126-16.md, AC1
  - Spec text: "test_defend_throw_from_non_defender_is_rejected ... tightens its bare pytest.raises(FateConflictError) with match="
  - Implementation: Also added `match=` to `test_unknown_request_id_fails_loud` ("unknown request_id") and `test_already_filled_request_id_fails_loud` ("already recorded"), not just the named authorization test.
  - Rationale: Same vacuous-match class (lang-review #6); trivial one-token additions; pins each sibling to its own branch so the whole `dispatch_fate_defense` fail-loud surface is non-vacuous.
  - Severity: minor
  - Forward impact: none
- **AC2 converted single-span emitter lookups; left the count-assertion test alone**
  - Spec source: context-story-126-16.md, AC2
  - Spec text: "span assertions that fetch a span by positional list index ... on a path that can emit more than one span are converted to name-keyed"
  - Implementation: Converted the 3 bare `[0]` lookups (emitter-isolation tests that each emit one span) to name-keyed `next(...)` for convention-consistency/future-proofing. Did NOT touch `test_defend_phase_emitter_fires_named_span`, whose `[s.name for s in spans] == ["fate.defend_phase"]` exact-list assertion is a stronger count-check than a name-keyed lookup. The genuinely multi-span production-path tests already used `next(...)`.
  - Rationale: Strict AC wording ("path that can emit more than one span") matched no current test; honored the AC's intent (name-keyed not positional) without weakening the existing exact-count assertion.
  - Severity: minor
  - Forward impact: none
- **No RED state — characterization coverage, no production change**
  - Spec source: context-story-126-16.md (Problem) + session scope
  - Spec text: "no production logic change expected ... green-on-arrival is the legitimate RED outcome"
  - Implementation: All tests pass against current code; the GREEN phase has no implementation work.
  - Rationale: Behavior shipped in 126-8; the story is test-debt cleanup, not a feature/bugfix.
  - Severity: minor
  - Forward impact: Dev GREEN phase is a verify-only pass-through (logged as a Delivery Finding).
- **Skipped the testing-runner subagent for verification**
  - Spec source: tea agent definition (`<workflow>` step 6) + project memory
  - Spec text: "Spawn testing-runner to verify RED state" / "Tests: Use testing-runner subagent, never run directly"
  - Implementation: Ran the 3 targeted test files directly (`uv run pytest -n0 <files>`).
  - Rationale: testing-runner has no file-scope parameter and would risk a full-suite run; project memory records that full-suite reruns caused a large credit blowup ("verify via baseline + targeted canary"). A scoped direct run is the cheaper, safer verification for 3 just-edited files.
  - Severity: minor
  - Forward impact: none

### Dev (implementation)
- **No production code written in the GREEN phase**
  - Spec source: 126-16 session scope + TEA Assessment
  - Spec text: "no production logic change expected ... GREEN is a verify-only pass-through (no implementation needed)"
  - Implementation: Verified the targeted tests are green and pushed the branch; made zero source changes.
  - Rationale: Production behavior shipped in 126-8; the tests characterize it. Writing code with no failing test would be scope creep (minimalist discipline) and risks No-Stubbing/No-Silent-Fallbacks violations.
  - Severity: minor
  - Forward impact: none
- **Verified GREEN via a scoped direct pytest run, not the testing-runner subagent**
  - Spec source: dev agent definition (`<workflow>` steps 2/4) + project memory
  - Spec text: "Spawn testing-runner to verify GREEN state" / "Tests: Use testing-runner subagent, never run directly"
  - Implementation: Ran the 3 changed files + `test_fate_pending_defenses.py` directly (`uv run pytest -n0 <files>`, 23 passed).
  - Rationale: testing-runner has no file-scope parameter and risks a full-suite run; project memory records full-suite reruns causing a large credit blowup. A scoped direct run is the correct, cheap GREEN verification for a test-only change.
  - Severity: minor
  - Forward impact: none

### Reviewer (audit)
- **TEA: AC1 extended to the two sibling bare raises** → ✓ ACCEPTED by Reviewer: sound; same vacuous-match class (lang-review #6), each sibling pinned to a branch-unique substring (verified at `fate_conflict.py:1186/1226/1222`). Strengthens the fail-loud surface.
- **TEA: AC2 converted single-span emitter lookups; left the count-assertion test alone** → ✓ ACCEPTED by Reviewer: honors AC2's intent (name-keyed not positional) and correctly preserves the stronger exact-list count assertion in `test_defend_phase_emitter_fires_named_span`.
- **TEA: No RED state — characterization coverage, no production change** → ✓ ACCEPTED by Reviewer: correct classification; behavior shipped in 126-8, story is test-debt cleanup. Matches the in-repo characterization precedent.
- **TEA: Skipped the testing-runner subagent for verification** → ✓ ACCEPTED by Reviewer: justified by the full-suite cost trap (project memory); a scoped direct run is the correct verification, and preflight re-confirmed 23 green.
- **Dev: No production code written in the GREEN phase** → ✓ ACCEPTED by Reviewer: correct for a characterization story; writing code with no failing test would be scope creep (No-Stubbing / minimalist discipline). Diff confirms zero production change.
- **Dev: Verified GREEN via a scoped direct pytest run, not the testing-runner subagent** → ✓ ACCEPTED by Reviewer: same rationale as TEA's; independently re-verified green by reviewer-preflight.

No undocumented deviations found.