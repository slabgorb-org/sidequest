---
story_id: "123-1"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 123-1: Triage and restore the server-test baseline — characterize the ~171 pre-existing full-suite failures

## Story Details
- **ID:** 123-1
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none
- **Type:** chore
- **Points:** 8
- **Priority:** p2

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-16T08:39:20Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-16T07:43:15Z | 2026-06-16T07:46:06Z | 2m 51s |
| red | 2026-06-16T07:46:06Z | 2026-06-16T07:52:14Z | 6m 8s |
| green | 2026-06-16T07:52:14Z | 2026-06-16T08:30:55Z | 38m 41s |
| review | 2026-06-16T08:30:55Z | 2026-06-16T08:39:20Z | 8m 25s |
| finish | 2026-06-16T08:39:20Z | - | - |

## Technical Approach

### Step 1: Root-Cause SDK Hermeticity (Priority: FIRST)
Determine whether the dominant failure bucket (~174 `LlmClientError` from `build_async_anthropic`) is a dev-env artifact or genuine regression:
1. Fresh `git fetch && git merge origin/develop` on both server + content repos
2. Set clean environment: `unset ANTHROPIC_API_KEY`
3. Run full test suite: `just server-test`
4. Compare failure pattern against cached baseline (if available)
5. Determine: is this a stale local tree artifact or a real develop regression?

**Outcome:** Documented root cause with evidence (test log snippet or reproduction steps)

### Step 2: Fix Snapshot-Field Governance Miss
- **Issue:** `pending_quest_offers` added in 117-3 never registered in ADR-110 session-helpers governance
- **Test:** `test_snapshot_field_governance::test_every_snapshot_field_is_categorized` fails
- **Fix:** Register the field in the governance snapshot model (~one-liner)

**Outcome:** Test passes without modifying test expectations

### Step 3: Triage DB-State Integration Failures
- Identify remaining failures after Steps 1-2
- Separate: legitimate DB-state issues vs pre-existing integration gaps
- For each: assess whether fix is in-scope (this story) or belongs to another epic
- Document decisions

**Outcome:** Categorized manifest of remaining failures with disposition (fix / defer / quarantine)

### Out of Scope (Deferred)
- **WWN class beat-pool loader PackErrors** — `class_filter` / `encounter_beat_choices` 'not in pool' on caverns_and_claudes / heavy_metal / elemental_harmony
  - These are deliberate in-flight, tied to epic-108 WWN de-nativization
  - Resolves when 108-3 lands
  - Quarantine in CI as XFAIL or document in manifest

## Acceptance Criteria
1. **Manifest artifact:** A categorized baseline-failure document (markdown or JSON) committed to the repo listing:
   - Failure category (e.g., SDK hermeticity, snapshot governance, DB-state, WWN defer)
   - Test name(s)
   - Root cause summary
   - Disposition (fixed, quarantined, or deferred epic)

2. **Non-Deliberate Fixes Applied:** Any non-WWN failures identified in Steps 1-2 are fixed and tests pass

3. **WWN Failures Quarantined:** Class beat-pool failures are marked as expected failures (XFAIL) in pytest or listed in the manifest with "epic-108 deferred" annotation

4. **CI Signal Restored:** Full test suite exits with:
   - All non-WWN tests passing (or XFAIL if unavoidable), OR
   - Manifest explicitly documents why specific tests remain failing and when they'll be resolved

5. **No Test Modifications for Failures:** Do not modify test expectations; fix the code or quarantine the test (not the assertion)

## Sm Assessment

**Routing rationale:** This is an 8pt p2 test-baseline triage story, server repo only, phased TDD. It pays down the ~171-failure CI debt that has been polluting review signal across recent stories (114-15, etc.). Setup is clean: session, context, and `feat/123-1-restore-server-test-baseline` branch (base `develop`) all verified.

**Critical context for TEA/Dev (known environmental hazards):**
- **WWN content already breaks ~13 server fixtures on current develop** (WWN migration + seaboard promotion). These are pre-existing and unrelated to this story's deliverable — classify, don't fix. They overlap the deliberately-out-of-scope WWN beat-pool bucket (epic-108 / 108-3).
- **OTEL span-count deadlock:** a full parallel `tests/server/` run deadlocks ~18 OTEL span-count tests (pre-existing). Run affected files serially with `-n0` — a hang here is NOT a new regression, it's the known deadlock. This matters because the story's whole job is distinguishing real failures from environmental noise.
- **Ruff format drift:** never run bare `ruff format .` — it reforms ~167 files and displaces `noqa F811`. Format only branch-touched files.

**TDD framing note:** This is a triage/characterization story, not a feature build. The "RED" test surface is partly the existing failing suite itself. TEA should focus the failing-test contract on the *non-deliberate, fixable* buckets — chiefly Step 2's `test_snapshot_field_governance::test_every_snapshot_field_is_categorized` (the `pending_quest_offers` governance miss, a genuine in-scope one-liner) — plus a test asserting the categorized manifest exists. Step 1 (SDK-hermeticity root-cause) is investigation that gates the manifest categorization, not a unit-test target. The autouse guard lives at `conftest.py:539`.

## TEA Assessment

### Red Phase (test writing)

**Tests Required:** Yes
**Reason:** The story has a concrete, machine-checkable deliverable (AC-1: a categorized baseline-failure manifest). The fixable code bucket (Step 2) already has a failing gate in-tree, so the *new* RED surface is the manifest contract.

**Test Files:**
- `tests/server/test_123_1_baseline_manifest.py` — pins the AC-1 deliverable to a structured JSON manifest at `docs/test-baseline-manifest.json`. 6 tests: manifest exists+parses; every bucket carries `category`/`tests`/`root_cause`/`disposition`; dispositions use the constrained vocabulary (`fixed`/`quarantined`/`deferred`/`investigated`); and the three substantive buckets are characterized — snapshot-governance (`fixed`), WWN beat-pool (`deferred`, references epic-108), SDK-hermeticity (~174 `LlmClientError`).

**Step 2 RED (not duplicated):** `tests/server/test_snapshot_field_governance.py::test_every_snapshot_field_is_categorized` already FAILS on the uncategorized `pending_quest_offers` field. That pre-existing gate *is* the RED for Step 2 — Dev makes it green by placing the field in a bounding registry in `sidequest/server/session_helpers.py` (the registries are `_PHASE_B_DROP_FIELDS` / `_PHASE_C_PROJECTIONS` / `_BOUNDED_BY_CONSTRUCTION` / `_EXCLUDED_FROM_DUMP`). Writing a second test for the same field would be redundant RED, so I did not.

**Tests Written:** 6 new tests covering AC-1 (the deliverable contract). AC-2/AC-3/AC-4 are enforced through the manifest's required buckets + disposition vocabulary rather than a flaky whole-suite meta-test (see deviations).

**Status:** RED confirmed by `testing-runner` (run 123-1-tea-red, `-n0`):
- `test_123_1_baseline_manifest.py` — 6 failed / 0 passed (manifest absent).
- `test_snapshot_field_governance.py` — 1 failed (`pending_quest_offers` gate) / 6 passed.

### Rule Coverage

| Rule / Principle | Test(s) | Status |
|------------------|---------|--------|
| No vacuous assertions (TEA self-check) | all 6 manifest tests assert concrete structure/values | passing self-check |
| Fail-loud deliverable (CLAUDE.md: No Silent Fallbacks) | `test_manifest_exists_and_parses` (loud diagnostic naming the missing path) | failing (RED) |
| Deliberate out-of-scope documented, not dropped | `test_wwn_beatpool_bucket_is_present_and_deferred` | failing (RED) |
| Reflection/data over source-grep (CLAUDE.md: No Source-Text Wiring Tests) | manifest tests parse JSON data, not production source | passing self-check |

**Rules checked:** Python repo — no `.pennyfarthing/gates/lang-review/python.md` present; applied CLAUDE.md principles (No Silent Fallbacks, No Source-Text Wiring Tests) and TEA anti-vacuous self-check.
**Self-check:** 0 vacuous tests written; 0 found in touched files.

**Handoff:** To Dev (Hephaestus) for GREEN — build the manifest, apply the Step 2 one-liner, run Step 1's root-cause, and disposition the remaining buckets.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `tests/server/conftest.py` — added a 4th autouse hermeticity leg `_stub_unseeded_objective_classifier` (stubs `build_unseeded_objective_classifier_llm` at the handler import site). **The SDK-hermeticity fix — greens 169 server tests.**
- `sidequest/server/session_helpers.py` — categorized `pending_quest_offers` in `_BOUNDED_BY_CONSTRUCTION` (Step 2, governance gate).
- `docs/test-baseline-manifest.json` — the deliverable: 8 categorized buckets with dispositions, generated from the real census/recheck JUnit data.
- `.gitignore` — ignore the regenerable `artifacts/123-1/` census run logs (13MB).

**Steps:**
- **Step 1 (root-cause + FIX):** Census on fresh develop (`-n0`, clean env): 269 failing. Dominant bucket = 171 SDK-hermeticity `LlmClientError`. Root-caused to 117-6's `build_unseeded_objective_classifier_llm` eagerly constructing the SDK in `_execute_narration_turn` with no test-hermeticity leg. **Verdict: real develop regression, not a stale-tree/env artifact.** Fixed with the 4th autouse leg → 0 residue.
- **Step 2 (FIX):** `pending_quest_offers` categorized → `test_every_snapshot_field_is_categorized` passes.
- **Step 3 (triage):** Remaining failures bucketed in the manifest — 84 deferred (epic-108 WWN de-nativization), 8 investigated pre-existing (stale counts, integration-conftest hermeticity gap, clean-env key-required artifacts).

**Tests:**
- New: `tests/server/test_123_1_baseline_manifest.py` — 6/6 GREEN; `test_snapshot_field_governance.py` — 9/9 GREEN.
- Scale verification (`testing-runner`, run 123-1-dev-green, `tests/server/ -n0`): **3521 passed / 4 failed / 124 skipped**. Zero SDK-hermeticity failures. The 4 failures are all documented WWN/epic-108 residue (committed_blow / cast_spell / strike-beat / armor-catalog) — **no new regressions.**
- Recheck of all 269 census failures with the fix: 175 pass, 94 fail (all WWN/pre-existing buckets; 0 SDK residue).

**Branch:** `feat/123-1-restore-server-test-baseline` (pushed).

**Handoff:** To Reviewer (Hermes) — note AC-4 is satisfied via manifest dispositions + the SDK/governance fixes, not a literally-zero-failure suite (see Dev deviation).

## Delivery Findings

<!-- Append-only. Each agent writes under its own subheading. -->

### TEA (test design)
- **Gap** (non-blocking): The full `tests/server/` suite cannot be run in default parallel mode — it deadlocks on ~18 OTEL span-count tests (pre-existing, documented). Dev must run with `-n0` or shard to produce an honest full-suite failure census for the manifest. Affects the Step 1/Step 3 triage methodology (`docs/test-baseline-manifest.json` census source). *Found by TEA during test design.*
- **Question** (non-blocking): The ~174 `LlmClientError` bucket is raised by the autouse guard `_no_real_anthropic_sdk` at `tests/server/conftest.py:518` (story title says `conftest.py:539` — minor drift; the guard moved). Whether this is a stale-tree/env artifact or a genuine isolation gap (tests reaching `build_async_anthropic` without installing a fake) is Step 1's open question. Affects `tests/server/conftest.py` (guard) and the per-test fake-install sites. *Found by TEA during test design.*

### Dev (implementation)
- **Question RESOLVED** (Step 1 verdict): The ~171 `LlmClientError` bucket is a **real develop regression, not a stale-tree/env artifact**. Root cause: Story 117-6 wired `build_unseeded_objective_classifier_llm` into `_execute_narration_turn`; it constructs the real SDK eagerly every narration turn, and the 93-1 hermeticity tripod had no leg for it. Fixed with a 4th autouse leg. 169 server tests → 0 residue. *Found by Dev during implementation.*
- **Improvement** (non-blocking): `tests/integration/` does NOT inherit the `tests/server/conftest.py` autouse hermeticity tripod (sibling dir), so two resume-path tests (`test_resources_wired_on_session_create`) reach the **live** Anthropic SDK (401 with a key set). A real billing/hermeticity leak, narrow and pre-existing. Recommend re-exporting the four autouse legs to `tests/integration/conftest.py` in a follow-up. Affects `tests/integration/conftest.py`. *Found by Dev during implementation.*
- **Gap** (non-blocking): Two stale hardcoded-count assertions remain (`test_message_type_complete_count` MessageType 57==56; `test_orchestrator_routes_narration_through_sdk` tools 41==40). Production code is correct; the literals are stale. Not bumped here (AC-5). Should be corrected alongside whatever grew the count, or quarantined in a follow-up. Affects `tests/protocol/test_enums.py`, `tests/agents/test_narrator_uses_sdk_client.py`. *Found by Dev during implementation.*
- **Improvement** (non-blocking): The parallel (`-n auto`) full-suite run still deadlocks on ~18 OTEL span-count tests, forcing `-n0` for any honest full census. Worth its own story so CI can run parallel. Affects the OTEL span-count test fixtures. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (non-blocking): **Required follow-up — integration-tree hermeticity/billing leak.** `tests/integration/conftest.py` does not inherit the tests/server autouse hermeticity tripod (sibling dir), so two resume-path tests (`tests/integration/test_resources_wired_on_session_create.py::test_light_current_preserved_on_resume`, `::test_light_pool_wired_on_resume_for_save_predating_pool`) reach the LIVE Anthropic SDK — a real billing exposure on a keyed machine. Pre-existing (not introduced by 123-1) and correctly documented in the manifest. Affects `tests/integration/conftest.py` (re-export the four autouse legs, or add a shared `tests/conftest.py`). *Found by Reviewer during code review (corroborated by reviewer-edge-hunter + reviewer-security, both HIGH).*
- **Improvement** (non-blocking): Tighten the new stub to `MagicMock(spec=ObjectiveClassifierLLM)` (or a minimal hand-rolled class) so unknown-attribute access fails loud and `await_count` works. Mirrors the same latent nit in `_stub_intent_router_factory`. Affects `tests/server/conftest.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Minor manifest-test robustness — include `owning_epic` in the WWN "108" traceability check and assert `disposition is not None` in `test_every_bucket_has_required_fields`. Affects `tests/server/test_123_1_baseline_manifest.py`. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 1 findings (1 Gap, 0 Conflict, 0 Question, 0 Improvement)
**Blocking:** None

- **Gap:** **Required follow-up — integration-tree hermeticity/billing leak.** `tests/integration/conftest.py` does not inherit the tests/server autouse hermeticity tripod (sibling dir), so two resume-path tests (`tests/integration/test_resources_wired_on_session_create.py::test_light_current_preserved_on_resume`, `::test_light_pool_wired_on_resume_for_save_predating_pool`) reach the LIVE Anthropic SDK — a real billing exposure on a keyed machine. Pre-existing (not introduced by 123-1) and correctly documented in the manifest. Affects `tests/integration/conftest.py`.

### Downstream Effects

- **`tests/integration`** — 1 finding

### Deviation Justifications

5 deviations

- **Manifest required as JSON, not markdown**
  - Rationale: AC-1's per-bucket fields + constrained disposition vocabulary are only completeness-checkable against a parsed object; a prose doc silently rots.
  - Severity: minor
  - Forward impact: none — Dev free to add a markdown rendering alongside.
- **No whole-suite "all green" meta-test for AC-4**
  - Rationale: Such a meta-test would itself be flaky (OTEL parallel deadlock + pre-existing WWN content failures) and would pollute the very CI signal this story restores — an anti-pattern.
  - Severity: minor
  - Forward impact: Reviewer should confirm AC-4 by inspecting manifest dispositions + a `-n0`/sharded run, not by expecting a single green-suite assertion.
- **No new test authored for Step 2 (reused the pre-existing gate)**
  - Rationale: The existing parametrized gate already fails on exactly `pending_quest_offers`; a duplicate would be redundant RED noise.
  - Severity: minor
  - Forward impact: none.
- **Deferred buckets documented in the manifest, NOT xfail-quarantined in code**
  - Rationale: The WWN clause explicitly permits "document in manifest." xfail-churning ~84 tests across many files that epic-108 will repair (un-xfail) creates merge noise and risks masking a real regression inside a quarantined file. The manifest is the honest, single-source CI-signal record this story exists to create.
  - Severity: minor
  - Forward impact: Reviewer should read AC-4 as satisfied by the manifest dispositions + the SDK/governance fixes, not by a literally-zero-failure suite. epic-108 owns the deferred buckets.
- **Step 1 exceeded "root-cause" into a full fix**
  - Rationale: The deliverable explicitly asks for "fixes for the non-deliberate buckets"; the SDK bucket is the dominant non-deliberate bucket and had a single-seam fix. Fixing it delivers the story's core value (honest CI signal) rather than deferring it.
  - Severity: none (positive scope — exceeds the minimum)
  - Forward impact: none.

## Design Deviations

### TEA (test design)
- **Manifest required as JSON, not markdown**
  - Spec source: story title (123-1), AC-1 ("a categorized baseline-failure document (markdown or JSON)")
  - Spec text: "Deliverable: a categorized baseline-failure manifest committed to the repo"
  - Implementation: Test requires a JSON object at `docs/test-baseline-manifest.json` as the source of truth; Dev MAY additionally commit a human-readable markdown rendering.
  - Rationale: AC-1's per-bucket fields + constrained disposition vocabulary are only completeness-checkable against a parsed object; a prose doc silently rots.
  - Severity: minor
  - Forward impact: none — Dev free to add a markdown rendering alongside.
- **No whole-suite "all green" meta-test for AC-4**
  - Spec source: context-story-123-1.md, AC-4 (CI signal restored)
  - Spec text: "a green-or-explicitly-quarantined suite so future stories get honest CI signal"
  - Implementation: AC-4 is enforced via the manifest's required buckets + disposition vocabulary, NOT a test that runs the whole suite and asserts zero failures.
  - Rationale: Such a meta-test would itself be flaky (OTEL parallel deadlock + pre-existing WWN content failures) and would pollute the very CI signal this story restores — an anti-pattern.
  - Severity: minor
  - Forward impact: Reviewer should confirm AC-4 by inspecting manifest dispositions + a `-n0`/sharded run, not by expecting a single green-suite assertion.
- **No new test authored for Step 2 (reused the pre-existing gate)**
  - Spec source: story title (123-1), Step 2
  - Spec text: "fix the snapshot-field governance miss ... test_snapshot_field_governance::test_every_snapshot_field_is_categorized"
  - Implementation: Relied on the already-failing `test_every_snapshot_field_is_categorized` as the Step 2 RED rather than writing a duplicate field-specific test.
  - Rationale: The existing parametrized gate already fails on exactly `pending_quest_offers`; a duplicate would be redundant RED noise.
  - Severity: minor
  - Forward impact: none.

### Dev (implementation)
- **Deferred buckets documented in the manifest, NOT xfail-quarantined in code**
  - Spec source: context-story-123-1.md, AC-4 ("a green-or-explicitly-quarantined suite") + the story's WWN out-of-scope clause ("Quarantine in CI as XFAIL **or** document in manifest")
  - Spec text: "a green-or-explicitly-quarantined suite so future stories get honest CI signal"
  - Implementation: The 84 epic-108 (WWN) failures and the 8 investigated pre-existing failures are documented as dispositioned buckets in `docs/test-baseline-manifest.json` rather than marked `xfail`/`skip` in code. `tests/server/` is now 3521 pass / 4 fail (all 4 documented WWN residue).
  - Rationale: The WWN clause explicitly permits "document in manifest." xfail-churning ~84 tests across many files that epic-108 will repair (un-xfail) creates merge noise and risks masking a real regression inside a quarantined file. The manifest is the honest, single-source CI-signal record this story exists to create.
  - Severity: minor
  - Forward impact: Reviewer should read AC-4 as satisfied by the manifest dispositions + the SDK/governance fixes, not by a literally-zero-failure suite. epic-108 owns the deferred buckets.
- **Step 1 exceeded "root-cause" into a full fix**
  - Spec source: story title (123-1), Step 1 ("root-cause, do FIRST")
  - Spec text: "determine whether the dominant bucket ... is a dev-env/stale-tree artifact or a real develop regression"
  - Implementation: Beyond root-causing, applied the fix (4th autouse tripod leg) that greens all 169 server SDK-hermeticity tests.
  - Rationale: The deliverable explicitly asks for "fixes for the non-deliberate buckets"; the SDK bucket is the dominant non-deliberate bucket and had a single-seam fix. Fixing it delivers the story's core value (honest CI signal) rather than deferring it.
  - Severity: none (positive scope — exceeds the minimum)
  - Forward impact: none.
### Reviewer (audit)
- **TEA: Manifest required as JSON, not markdown** → ✓ ACCEPTED by Reviewer: JSON is the correct machine-checkable form for a completeness-gated deliverable; agrees with author reasoning.
- **TEA: No whole-suite "all green" meta-test for AC-4** → ✓ ACCEPTED by Reviewer: a whole-suite assertion would be flaky against the OTEL parallel deadlock + WWN content failures and would itself pollute CI signal — sound.
- **TEA: No new test authored for Step 2 (reused the pre-existing gate)** → ✓ ACCEPTED by Reviewer: `test_every_snapshot_field_is_categorized` already fails on exactly `pending_quest_offers`; duplication would be redundant RED.
- **Dev: Deferred buckets documented in manifest, NOT xfail-quarantined in code** → ✓ ACCEPTED by Reviewer: the story's own WWN clause explicitly permits "document in manifest" as an alternative to XFAIL; xfail-churning ~84 epic-108-owned tests would create merge noise and mask regressions. AC-4 is satisfied via manifest dispositions + the SDK/governance fixes. AC-2 ("non-WWN failures identified in Steps 1-2 are fixed") is satisfied — Steps 1-2 are precisely the SDK + governance buckets, both fixed.
- **Dev: Step 1 exceeded "root-cause" into a full fix** → ✓ ACCEPTED by Reviewer: the deliverable explicitly asks for "fixes for the non-deliberate buckets"; fixing the dominant 169-test bucket at its single seam is the story's core value, not scope creep.
- **No undocumented deviations found.** The diff matches the logged deviations; no spec divergence slipped through.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 0 actionable (5 observations) | confirmed 0, dismissed 0, deferred 1 (traceability note) |
| 2 | reviewer-edge-hunter | Yes | findings | 6 | confirmed 2 (non-blocking), downgraded 2, dismissed 2 |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings; assessed domain myself (see [SILENT]) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings; assessed domain myself (see [TEST]) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings; assessed domain myself (see [DOC]) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings; assessed domain myself (see [TYPE]) |
| 7 | reviewer-security | Yes | findings | 2 | confirmed 1 (non-blocking, pre-existing), downgraded 1 |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings; assessed domain myself (see [SIMPLE]) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings; assessed domain myself (see [RULE]) |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`, assessed by Reviewer directly)
**Total findings:** 3 confirmed (all non-blocking), 3 downgraded, 2 dismissed, 1 deferred

## Reviewer Assessment

**Verdict:** APPROVED

A tightly-scoped, high-value triage story. The dominant 169-test SDK-hermeticity bucket is fixed at its single root seam; the snapshot-governance gate is fixed; and the deliverable manifest is generated from real census/recheck JUnit data, not improvised. Verified at scale: `tests/server/` 3521 pass / 4 fail (all 4 documented WWN/epic-108 residue), zero SDK failures, no regressions.

**Data flow traced:** player action → `_execute_narration_turn` (websocket_session_handler.py:1197) → `build_unseeded_objective_classifier_llm` → in tests/server, now intercepted by the autouse `_stub_unseeded_objective_classifier` returning `is_objective_given=False` (safe no-op). Production path unchanged — the only production edit is a governance-registry membership.

**Key observations:**
- [VERIFIED] The production change (`session_helpers.py:215`) has **zero runtime effect** — `_BOUNDED_BY_CONSTRUCTION` is a governance artefact consumed only by `test_snapshot_field_governance.py` (comment at session_helpers.py:100), and `pending_quest_offers` is NOT referenced in `_apply_phase_c_projections` (snapshot_slimming.py) — evidence: grep returned no match. The field already rode the dump in full before this change; categorization just records the bounding decision. Complies with ADR-110 / 61-5 gate.
- [VERIFIED] `pending_quest_offers` is correctly bounded-by-construction (category d): `dict[str, QuestSeed]` keyed by quest_id, and entries are popped on accept/decline — evidence: `quest_offer.py:80,119` `.pop(quest_id, None)`. Growth is bounded by finite authored openings.
- [VERIFIED] The autouse fixture patches the handler's **import-site** name — evidence: handler does `from ...llm_factory import build_unseeded_objective_classifier_llm` (websocket_session_handler.py:37-40), so patching `websocket_session_handler.build_unseeded_objective_classifier_llm` is the correct target. Mirrors the established `_stub_intent_router_factory` doctrine.
- [VERIFIED] The fixture does not mask the objective-classifier wiring tests — evidence: `test_unseeded_objective_classifier_wiring.py` install their own AsyncMock and pass (16 classifier tests green). LIFO shadowing preserved.
- [SEC] **[MEDIUM, non-blocking, pre-existing]** `tests/integration/conftest.py` does not inherit the tests/server autouse hermeticity tripod (sibling dir), so two resume-path tests (`test_resources_wired_on_session_create`) reach the live Anthropic SDK — a real billing exposure on a keyed machine. **Downgraded from the subagents' HIGH with rationale:** the diff does NOT touch `tests/integration/` (evidence: `git diff --name-only` has no integration path) — the gap is **pre-existing**, not introduced here; it is out of the story's declared tests/server-baseline scope; and Step 3's job is to "document decisions," which Dev did (manifest bucket "Integration-conftest hermeticity gap", disposition `investigated`, with the exact recommended follow-up). Confirmed as a real issue and a required follow-up — NOT dismissed. Captured as a delivery finding for the next story.
- [EDGE] **[LOW, non-blocking]** `stub_llm = MagicMock()` (not `AsyncMock`/`spec=`): `emit_tool.await_count` assertions against the stub would fail, and unknown-attribute access auto-vivifies silently (mild No-Silent-Fallbacks tension). Confirmed but non-blocking — it is an exact copy of the existing `_stub_intent_router_factory` shape (MagicMock + async method), so it is consistent with established code; tightening to `spec=ObjectiveClassifierLLM` is a nice-to-have.
- [EDGE] **[LOW, downgraded from MEDIUM]** `test_every_bucket_has_required_fields` would pass for a bucket with `"disposition": null` (key present, value None). Downgraded: the null case IS caught by `test_every_disposition_is_in_the_allowed_vocabulary` (None ∉ vocabulary), and the committed manifest has no null dispositions. Defense-in-depth only.
- [EDGE] **[LOW, downgraded from MEDIUM]** The WWN-bucket "108" traceability check reads `category + root_cause` but not `owning_epic`; fragile if a future edit moves the epic ref out of root_cause. Downgraded: currently passes (root_cause contains "epic-108 (108-3 / 108-7)"); a robustness nit, not a defect.
- [EDGE] **[deferred/dismissed]** fixture-doesn't-yield (observability) and pending_quest_offers theoretical unbounded growth: dismissed as non-issues — the fixture's purpose is purely hermetic, and growth is bounded by authored content + the pop-on-resolution lifecycle.
- [SILENT] (subagent disabled) Assessed myself: the fixture introduces no swallowed errors; the catch-all `_no_real_anthropic_sdk` guard still raises loud on any other unfaked SDK construction. No silent fallback introduced.
- [TEST] (subagent disabled) Assessed myself: the 6 manifest tests are non-vacuous (parse, required-keys, constrained disposition vocabulary, three named substantive buckets). Edge-hunter's two test-robustness nits noted above; neither is a vacuous-pass on the committed manifest.
- [DOC] (subagent disabled) Assessed myself: the fixture docstring and the session_helpers comment are accurate and trace origin stories (117-6 / 117-3); the manifest's `generated_from` correctly describes reproduction (no dangling committed-path claims after the gitignore). No stale comments.
- [TYPE] (subagent disabled) Assessed myself: no new types; the stub conforms to the `ObjectiveClassifierLLM` Protocol (single `emit_tool`); return dict matches `classify_unseeded_objective`'s `.get(...)` reads.
- [SIMPLE] (subagent disabled) Assessed myself: the fix is minimal — one registry entry + one fixture mirroring three siblings + a data file. No over-engineering. The manifest was generated, not hand-maintained.
- [RULE] (subagent disabled) Assessed myself — see Rule Compliance below.

### Rule Compliance

| Rule (CLAUDE.md / SOUL.md) | Applies to | Verdict |
|---|---|---|
| Server tests must be hermetic (no unfaked SDK construction) | new fixture; integration conftest | **tests/server: COMPLIANT** (gap closed). **tests/integration: PRE-EXISTING VIOLATION** — out of scope, documented + follow-up filed. |
| No Silent Fallbacks | fixture, categorization | COMPLIANT — `_no_real_anthropic_sdk` still fails loud; categorization is explicit, not a default. |
| No Stubbing (production) | session_helpers | COMPLIANT — no production stub; the stub is a test fixture (expected for hermeticity). |
| No Source-Text Wiring Tests | manifest tests | COMPLIANT — tests parse JSON data, not production source. |
| Every test suite needs a wiring test | manifest tests | N/A in the unit sense — the manifest is a data deliverable; the autouse fixture's wiring is exercised by the 3521-pass server run. |
| OTEL on subsystem fixes | the fix | N/A — the change is test-hermeticity + a governance-registry membership; no subsystem decision path altered (cosmetic per the OTEL "not needed for" clause). |

### Devil's Advocate

Suppose this code is broken. The most damning charge: *the autouse fixture is a blanket suppression that hides real failures.* If `_stub_unseeded_objective_classifier` silently swallows the objective-classifier everywhere, a future bug where the classifier SHOULD fire would never be caught — the suite would stay green over a broken subsystem, the exact "Claude wings it, OTEL is the lie detector" failure mode CLAUDE.md warns about. Examined: the fixture only intercepts the *handler's eager construction* of the classifier LLM; it does not touch `run_unseeded_objective_classifier_watcher` or `classify_unseeded_objective`, and the dedicated wiring tests install their own AsyncMock and assert `await_count` — so the subsystem's real behavior is still tested. The stub returns `is_objective_given=False`, the *conservative* verdict (no phantom objective beep), so it cannot manufacture a false positive. Verdict: not a suppression of signal, a targeted hermeticity fake consistent with three existing legs.

Second charge: *the manifest lets the team declare victory while 88 tests stay red.* A confused future reader could read "baseline restored" and assume green. Examined: the manifest is explicit — `census_failing: 269`, `still_failing_after_fix` enumerated per bucket with dispositions and owning epics; the summary note spells out that deferred ≠ fixed. This is more honest than a silently-xfail'd suite, not less.

Third charge: *the pre-existing integration billing leak is a live risk being waved through.* This is the sharpest point and I do not wave it through — it is confirmed, severity-justified, and filed as a required follow-up. But blocking THIS story (which neither introduced nor touches that code, and which discovered the leak) would punish honest triage and is out of its tests/server scope. A stressed CI with a valid key running the integration suite WILL bill two calls; that risk predates this branch and is now visible for the first time because of it.

Nothing in the devil's advocate pass uncovered a defect introduced by this diff that rises to blocking.

**Pattern observed:** Fourth leg of the hermeticity tripod, mirroring `_stub_intent_router_factory` at tests/server/conftest.py:483 — consistent, idiomatic.
**Error handling:** Stub returns a valid `ObjectiveClassifierLLM` dict; `classify_unseeded_objective` reads via `.get(...)` with defaults; reasoning=None is tolerated.
**Handoff:** To SM (Themis) for finish-story.