---
story_id: "59-29"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 59-29: Co-locate witnessed_act precondition coverage into test_dispatch_precondition_gate.py

## Story Details
- **ID:** 59-29
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-02T23:54:51Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-02T00:00:00Z | 2026-06-02T23:29:54Z | 23h 29m |
| red | 2026-06-02T23:29:54Z | 2026-06-02T23:42:45Z | 12m 51s |
| green | 2026-06-02T23:42:45Z | 2026-06-02T23:44:35Z | 1m 50s |
| spec-check | 2026-06-02T23:44:35Z | 2026-06-02T23:46:54Z | 2m 19s |
| verify | 2026-06-02T23:46:54Z | 2026-06-02T23:50:19Z | 3m 25s |
| review | 2026-06-02T23:50:19Z | 2026-06-02T23:53:48Z | 3m 29s |
| spec-reconcile | 2026-06-02T23:53:48Z | 2026-06-02T23:54:51Z | 1m 3s |
| finish | 2026-06-02T23:54:51Z | - | - |

## Technical Approach

The goal of this story is to consolidate witnessed_act precondition test coverage. Currently, witnessed_act precondition tests are scattered across multiple test files. This story collocates all witnessed_act precondition coverage into a single, organized test module: `test_dispatch_precondition_gate.py`.

### Acceptance Criteria

1. **AC1: All witnessed_act precondition tests are migrated to test_dispatch_precondition_gate.py**
   - Tests should be organized by precondition type
   - No duplicate test cases
   - All edge cases covered (success, failure, boundary conditions)

2. **AC2: Test names follow convention and describe the precondition being tested**
   - Format: `test_witnessed_act_precondition_{case_name}`
   - Each test documents the precondition constraint being validated

3. **AC3: Existing test coverage is preserved**
   - All green tests remain green
   - No regression in dispatch coverage
   - OTEL watcher events fire correctly for each precondition path

4. **AC4: The new test file is wired into the test suite**
   - Test discovery works (pytest finds all tests)
   - CI gate passes (wiring-check gate verifies test is imported and reachable)
   - Lint and type-check pass

## Sm Assessment

Story 59-29 (1pt, tdd, p1) is a test-consolidation refactor within sidequest-server only — co-locating scattered witnessed_act precondition coverage into `test_dispatch_precondition_gate.py`. This is the highest-priority backlog item and rides epic-59 (Intent Router) momentum; 59-28 from the same epic landed in the prior sprint commit, so the precondition-gate territory is freshly touched.

**Scope is well-bounded:** single repo, no cross-repo coordination, no new production code expected — the deliverable is reorganized test coverage plus the AC4 wiring check (pytest discovery + reachability). The risk surface is regression (AC3: green stays green, OTEL precondition paths still fire), which TDD's red→green discipline handles directly.

**Routing:** phased tdd → RED phase next. The Architect (tea) writes the failing/relocated tests covering all four ACs, with particular attention to AC3 (no regression) and AC4 (the wiring test that proves the new module is imported and reachable from production test discovery). Jira is null — claim explicitly skipped.

## Delivery Findings

### TEA (test design)
- **Gap** (non-blocking): Pre-existing test failure on `develop`, unrelated to this story — `tests/handlers/test_aside_channel_wiring.py::test_aside_is_out_of_band_in_mp` fails on the clean baseline (verified by git-stashing 59-29 edits and re-running: still red). It is the ADR-107 out-of-band aside channel, not the dispatch precondition gate. Affects `tests/handlers/test_aside_channel_wiring.py` (the MP out-of-band assertion needs investigation under its own story). *Found by TEA during test design.*
- **Improvement** (non-blocking): `tests/agents/test_witnessed_act_subsystem.py` carries 5 pre-existing pyright errors (4× `political_state` Optional-member-access on `.premises`/`.blocs`/`.ledger`, 1× `dict` passed where `VisibilityTag` expected at line 44) — present at baseline, untouched by this story. Candidate for the 64-17 stale-test tidy. Affects `tests/agents/test_witnessed_act_subsystem.py` (narrow the `_snapshot()` return type or assert non-None before member access). *Found by TEA during test design.*

### Dev (implementation)
- No upstream findings during implementation. (GREEN was verification-only — no production code written; co-located tests pass against shipped 59-28 production.)

### Reviewer (code review)
- No upstream findings during code review. (Both enabled subagents clean; the pre-existing aside-channel failure and subsystem-file pyright debt were already captured by TEA above — no new issues.)

## TEA Assessment

**Tests Required:** Yes (the tests ARE the deliverable — a test co-location story)
**Reason:** n/a

**Test Files:**
- `tests/agents/test_dispatch_precondition_gate.py` — +5 co-located witnessed_act precondition tests (pure-function drop/keep + selective sibling preservation + OTEL gated-span emit/silence), mirroring the sibling scenario_clue blocks; +3 fixture helpers (`_oz_political_state`, `_political_snapshot`, `_witnessed_act_dispatch`).
- `tests/agents/test_witnessed_act_subsystem.py` — removed the now-duplicated `test_precondition_inert_without_political_state` (and its unused `_INERT_PRECONDITIONS` import); left a pointer NOTE to the new home.

**Tests Written:** 5 new tests covering all 4 ACs (AC1 drop+reason & sibling-preservation, AC2 keep-when-hydrated, AC3 OTEL span emit/silence, AC4 co-located+no-duplication verified by green suite).
**Status:** GREEN (pass against existing 59-28 production — see Design Deviation; no production change permitted by scope)

### Rule Coverage

| Rule (sidequest-server CLAUDE.md) | Test(s) | Status |
|------|---------|--------|
| No Source-Text Wiring Tests | behavior-driven drop/keep + span assertions; reflection over `_INERT_PRECONDITIONS` only (runtime object, not source grep) | pass |
| OTEL Observability Principle | `test_gate_emits_one_witnessed_act_gated_span_per_drop` / `..._no_span_..._present` | pass |
| Every test asserts something meaningful | keep-case asserts dispatch *survives* (subsystem present), not just no-raise | pass |
| No Silent Fallbacks | gated drop is loud (span carries subsystem + reason) | pass |

**Rules checked:** 4 of 4 applicable lang-review/CLAUDE.md rules have test coverage
**Self-check:** 0 vacuous tests written; 1 duplicate removed (co-located, not duplicated)

**Verification evidence:**
- Targeted: `17 passed` (both touched files)
- Full suite: `9710 passed, 361 skipped, 1 failed` — the 1 failure is the pre-existing unrelated aside-channel test (see Delivery Findings), red on baseline too.
- `ruff check` clean; `pyright` clean on the gate file (0 errors); the subsystem file's 5 pyright errors are pre-existing (see Delivery Findings).

**Handoff:** To Dev (Agent Smith) for GREEN — **verification only**, no production implementation work (the co-located tests already pass against shipped 59-28 production).

## Design Deviations

### TEA (test design)
- **RED phase produced green (not failing) tests — co-location of existing coverage**
  - Spec source: context-story-59-29.md, story description ("No production change")
  - Spec text: "currently covered indirectly via tests/agents/test_witnessed_act_subsystem.py. Co-locate dedicated precondition coverage … No production change."
  - Implementation: The witnessed_act precondition predicate + `_INERT_PRECONDITIONS` registration already shipped in 59-28, and the gate (`gate_inert_dispatches`/`run_dispatch_precondition_gate`) drives them generically. The five new co-located tests therefore pass green on first run; a genuine RED-fail is impossible without editing production, which the story forbids. Meaningfulness verified structurally (drop-vs-keep is genuinely conditioned on `political_state`) and by confirming the baseline was green before the change.
  - Rationale: This is a test-hygiene refactor (existing-coverage relocation), not new behavior. Forcing an artificial RED would require a production mutation that is explicitly out of scope.
  - Severity: minor
  - Forward impact: GREEN phase has no production implementation work — Dev's pass is a verification (confirm 17 pass, duplicate removed, lint/types clean), not an implementation.

### Dev (implementation)
- No deviations from spec. (Verification-only GREEN: no production code written — the story forbids production change and the co-located tests already pass against shipped 59-28 production. Writing any implementation would be scope creep, so per minimalist discipline none was added.)

### Reviewer (audit)
- **TEA's "RED produced green tests — co-location of existing coverage"** → ✓ ACCEPTED by Reviewer: sound and unavoidable. The behavior shipped in 59-28 and the story forbids production change, so a failing RED is structurally impossible; TEA correctly proved meaningfulness instead (predicate-driven, baseline-green-confirmed). Coverage strictly increased over the removed test.
- **Dev's "No deviations (verification-only GREEN)"** → ✓ ACCEPTED by Reviewer: correct — adding production code would have been scope creep on a test-only story.
- **Architect's spec-check naming mismatch (Trivial, Rec A)** → ✓ ACCEPTED by Reviewer: the sibling-mirroring names (`test_witnessed_act_dropped_when_...`) are the right choice for co-located consistency; the generic template format was lower-authority and prescribes nothing in the context doc.
- No undocumented deviations found by Reviewer.

### Architect (reconcile)

**Existing-entry verification:**
- TEA's "RED produced green tests" entry — all 6 fields present and accurate. Spec source `context-story-59-29.md` exists; quoted spec text ("currently covered indirectly via tests/agents/test_witnessed_act_subsystem.py. Co-locate dedicated precondition coverage … No production change.") matches the story description; Implementation accurately describes the 59-28-shipped predicate driving the co-located tests; Forward impact (GREEN is verification-only) held true (Dev wrote no production code). Confirmed accurate — no correction needed.
- Dev's "No deviations" and Reviewer's audit stamps — accurate.

**Missed deviation formalized (for the audit record):**
- **Test naming follows sibling `scenario_clue` convention, not the Story-Details template format**
  - Spec source: `.session/59-29-session.md` → ## Story Details → Acceptance Criteria, AC2
  - Spec text: "AC2: Test names follow convention and describe the precondition being tested — Format: `test_witnessed_act_precondition_{case_name}`"
  - Implementation: the five co-located tests are named to mirror the sibling scenario_clue tests in the same file — `test_witnessed_act_dropped_when_political_state_none`, `test_witnessed_act_kept_when_political_state_present`, `test_witnessed_act_dropped_but_sibling_dispatch_preserved`, `test_gate_emits_one_witnessed_act_gated_span_per_drop`, `test_gate_emits_no_span_for_witnessed_act_when_political_state_present` — rather than the `test_witnessed_act_precondition_{case_name}` template format.
  - Rationale: The story's load-bearing intent is co-location "alongside the other subsystems' precondition tests (e.g. scenario_clue)". The scenario_clue tests use the `{subsystem}_{condition}` descriptive style; matching it makes the co-located block read as one coherent family. The higher-authority `context-story-59-29.md` AC2 prescribes no naming format (only "documents the precondition constraint"), so this resolves under Architect spec-check Recommendation A (update spec to match the better implementation), not a code change.
  - Severity: trivial
  - Forward impact: none — no sibling story depends on witnessed_act test names; future precondition additions (e.g. 59-30) should follow the same sibling-mirroring style.

**AC deferrals:** None — all four ACs were completed (no DEFERRED/DESCOPED entries to verify).

## Dev Assessment

**Implementation Complete:** Yes (verification-only — no production change, per story scope)
**Files Changed:**
- None beyond TEA's RED-phase test commit (`9c646d7`). This is a test-co-location story; production was correctly left untouched.

**Tests:** 17/17 passing (GREEN) on both touched files; 5 witnessed_act tests confirmed co-located in `test_dispatch_precondition_gate.py`.
**Branch:** `feat/59-29-witnessed-act-precondition-test-colocation` (pushed to origin).

**Self-review:**
- Wired: the co-located tests drive the real production functions (`gate_inert_dispatches`, `run_dispatch_precondition_gate`) — behavior-level, not source-grep.
- Patterns: mirror the existing scenario_clue blocks in the same file.
- ACs: all 4 met (drop/keep/sibling-preservation, OTEL span emit/silence, co-located without duplication, suite green).
- Working tree clean; no debug code; correct feature branch.

**Handoff:** To Reviewer (The Merovingian) for code review.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned (one trivial naming note)
**Mismatches Found:** 1 (trivial)

AC-by-AC (against context-story-59-29.md):
- **AC1** (inert when `political_state` None — drop + reason; sibling preservation) — covered by `test_witnessed_act_dropped_when_political_state_none` (asserts removal + `GatedDispatch.subsystem`/`idempotency_key`/reason) and `test_witnessed_act_dropped_but_sibling_dispatch_preserved` (npc_agency survives). ✓
- **AC2** (kept when hydrated — pass-through) — `test_witnessed_act_kept_when_political_state_present` asserts the dispatch *survives* the filter (subsystem present), not merely no-raise. ✓
- **AC3** (OTEL span emit/silence) — `test_gate_emits_one_witnessed_act_gated_span_per_drop` + `test_gate_emits_no_span_for_witnessed_act_when_political_state_present` drive the real `run_dispatch_precondition_gate` with an in-memory exporter. ✓
- **AC4** (co-located, not duplicated; suite green) — duplicate removed from `test_witnessed_act_subsystem.py`; 17 pass on both files; full suite green save the pre-existing unrelated aside-channel failure. ✓

Mismatch:
- **Test naming convention** (Cosmetic — type Cosmetic, severity Trivial)
  - Spec: Story-Details (auto-generated) AC2 suggested `test_witnessed_act_precondition_{case_name}`.
  - Code: names mirror the sibling scenario_clue tests in the same file (`test_witnessed_act_dropped_when_political_state_none`, etc.).
  - Recommendation: **A — update spec.** The mirrored naming is the correct choice: the story's intent is co-location "alongside the other subsystems' precondition tests (e.g. scenario_clue)", and matching the siblings' descriptive `{subsystem}_{condition}` style is more consistent than the generic template format. The higher-authority context-story AC2 prescribes no naming format, so there is no real conflict — only the lower-authority auto-generated template differs.

**Decision:** Proceed to verify (TEA). No hand-back to Dev — the single mismatch is trivial and resolves as a spec note, not a code change.

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 2 (`tests/agents/test_dispatch_precondition_gate.py`, `tests/agents/test_witnessed_act_subsystem.py`)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 4 findings | `_oz_political_state`↔`_pack` fixture dup (high); `_fresh_tracer_and_exporter`→conftest (high); `_make_npc`→conftest (high); dispatch-builder factory (medium) |
| simplify-quality | 5 findings | missing return types + `dict`-vs-`VisibilityTag` — all in pre-existing `test_witnessed_act_subsystem.py` code (medium/low) |
| simplify-efficiency | 1 finding | `_pack`↔`_oz_political_state` dup — rated **low / intentional co-location** |

**Applied:** 0 fixes.
**Flagged for Review / Noted (not applied) — with rationale:**
- **Shared OZ-world fixture** (`_oz_political_state` ↔ `_pack` duplication): real but ~20 lines, test-only; proper fix is a `tests/agents/conftest.py`, which expands a 1pt co-location story and touches the pre-existing subsystem test. Cross-test-module helper imports are an anti-pattern, so a half-measure would be worse. Deferred. (efficiency lens concurred: low/intentional.)
- **`_fresh_tracer_and_exporter` → shared harness**: **already tracked as backlog story 71-34** ("Extract shared OTEL watcher-test harness"). Out of scope here by design.
- **`_make_npc` consolidation**: pre-existing, codebase-wide pattern (multiple test files); a dedicated conftest refactor, not this story.
- **Return-type annotations + `dict`-vs-`VisibilityTag` in `test_witnessed_act_subsystem.py`**: pre-existing in code this story did not author (already captured under Delivery Findings as the 5 pre-existing pyright errors; candidate for 64-17). Fixing them would be unrelated scope.

**Reverted:** 0.

**Overall:** simplify: clean (findings are pre-existing or scope-expanding; 0 applied, by deliberate scope discipline on a 1pt test-co-location story)

**Quality Checks:** All passing — targeted `17 passed`; `ruff check` clean; `pyright` 0 errors on the gate file (the subsystem file's 5 pyright errors are pre-existing, see Delivery Findings); working tree clean.

**Handoff:** To Reviewer (The Merovingian) for code review.

### Delivery Findings Capture
See `### TEA (test design)` entries under `## Delivery Findings` — no *new* findings during verify (the simplify findings above are either pre-existing or already-tracked backlog, not new upstream issues).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | success | 0 smells; 17/17 green; ruff clean; gate-file pyright 0 | N/A (clean) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none (5 rules checked, 0 violations) | N/A (clean) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (2 enabled subagents returned; 7 disabled via `workflow.reviewer_subagents` settings)
**Total findings:** 0 confirmed, 0 dismissed, 0 deferred (both enabled subagents clean)

## Reviewer Assessment

**Verdict:** APPROVED

This is a test-only diff (2 files, +186/−17) in `sidequest-server`. No production code changed. Both enabled subagents returned clean; the seven disabled ones are recorded as Skipped per settings. I read the full diff and the project rules myself.

**Observations (≥5):**
- `[VERIFIED]` Tests are **non-tautological** — they are driven by the real `_INERT_PRECONDITIONS['witnessed_act']` predicate. Confirmed at runtime: registered=True; predicate returns `"...political_state is None..."` for a bare snapshot and `None` when hydrated. If the predicate were removed/broken the drop-test would fail. Evidence: `dispatch_precondition_gate.py:78-87`.
- `[VERIFIED]` Meaningful assertions, no vacuous passes — the keep-case asserts the dispatch **survives** (`_all_dispatch_subsystems(filtered) == ["witnessed_act"]`), not `is not None`; the drop-case asserts subsystem + idempotency_key + reason substring. Evidence: diff lines 123-134, 103-120.
- `[VERIFIED]` OTEL coverage honors the project's Observability Principle — `test_gate_emits_one_witnessed_act_gated_span_per_drop` drives the real `run_dispatch_precondition_gate` with an in-memory exporter and asserts exactly one `intent_router.dispatch.gated` span carrying `subsystem`+`reason`; the present-state case asserts zero spans. Evidence: diff lines 155-187.
- `[VERIFIED]` Co-location without duplication — the indirect predicate test was removed from `test_witnessed_act_subsystem.py` (diff lines 250-257) and its now-unused `_INERT_PRECONDITIONS` import dropped; a pointer NOTE replaces it. No double coverage remains.
- `[VERIFIED]` Pattern fidelity — the new fixtures/tests mirror the sibling `scenario_clue` blocks in the same file (keying on `political_state` vs `scenario_state`), which is exactly the story's "alongside the other subsystems' precondition tests" intent.
- `[LOW]` `_oz_political_state` duplicates the subsystem test's `_pack` premise/bloc fixture — real but ~20 lines, test-only; proper home is a shared `conftest.py`. Correctly deferred by TEA (cross-module test-helper imports are an anti-pattern; a conftest is its own change). Tracked alongside the already-existing backlog story 71-34 for the OTEL tracer harness.

**Data flow traced:** No external input exists anywhere in the diff — all values are hardcoded fixture literals (`"humbug"`, `"Dorothy"`, `"expose"`, ints). No path from any external source to a sensitive sink. (Corroborated by `[SEC]`.)

### Rule Compliance

| Rule (CLAUDE.md / SOUL) | Applies to | Verdict |
|---|---|---|
| No Source-Text Wiring Tests | the 5 new tests | Compliant — behavior-driven (drive `gate_inert_dispatches`/`run_dispatch_precondition_gate`); reflection over `_INERT_PRECONDITIONS` dict is a runtime object, not a source grep |
| OTEL Observability Principle | span emit/silence tests | Compliant — span presence/absence asserted via in-memory exporter |
| No Silent Fallbacks | `_oz_political_state` | Compliant — explicit `assert state is not None`, loud not swallowed |
| No Stubbing | all 5 tests | Compliant — full assertion bodies, no placeholders |
| Every test asserts meaningfully | all 5 tests | Compliant — see Observations |

### Devil's Advocate

Could this co-location be hiding a regression? The danger in a "move the tests" story is that the new tests are weaker than the coverage they replace, so a real break slips through. I checked: the removed test asserted the raw predicate's two outcomes (non-None reason when `political_state` is None; None when hydrated). The new gate-level tests assert a *superset* — not only the predicate outcomes (via reason substring) but the actual package mutation (dispatch dropped vs survives), the `GatedDispatch` record, and the OTEL span. So coverage strictly increased, not decreased. Could the keep-case pass spuriously if the gate silently kept *everything*? No — `test_witnessed_act_dropped_but_sibling_dispatch_preserved` proves selective filtering: in the same no-political-state snapshot, witnessed_act is dropped while npc_agency survives, so a "keep everything" bug would fail that test. Could a confused future editor think the precondition is still tested in the subsystem file? No — a NOTE points to the new home. Could the `assert state is not None` in `_oz_political_state` mask a `from_world` returning None for a valid world? It would surface loudly as an AssertionError in every keep-case test, not silently pass. What about the pre-existing aside-channel full-suite failure — is it being used to wave away a real break? No — verified red on the stashed baseline, different subsystem (ADR-107), logged as a finding. I could not construct a scenario where this diff introduces a defect. The change is additive test coverage with a clean removal of one duplicate.

**Dispatch tags:** `[SEC]` clean (reviewer-security, 0 violations). `[EDGE]`/`[SILENT]`/`[TEST]`/`[DOC]`/`[TYPE]`/`[SIMPLE]`/`[RULE]` — subagents disabled via settings; I covered test-quality, edge (sibling-preservation), type (gate-file pyright 0 errors), and rule compliance myself above.

**Pattern observed:** Sibling-mirroring test structure at `tests/agents/test_dispatch_precondition_gate.py` — witnessed_act block parallels the scenario_clue block.
**Error handling:** loud `assert` in `_oz_political_state` (`tests/agents/test_dispatch_precondition_gate.py`); no swallowed errors in the diff.

**Handoff:** To SM for finish-story.