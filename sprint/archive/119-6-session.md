---
story_id: "119-6"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 119-6: 119-3 deferred reuse refactor: consolidate the four single-shot Haiku adapters now the transport has landed

## Story Details
- **ID:** 119-6
- **Jira Key:** (none — Jira not configured)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-18T11:43:50Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-18T11:09:15Z | 2026-06-18T11:11:30Z | 2m 15s |
| red | 2026-06-18T11:11:30Z | 2026-06-18T11:21:22Z | 9m 52s |
| green | 2026-06-18T11:21:22Z | 2026-06-18T11:30:39Z | 9m 17s |
| review | 2026-06-18T11:30:39Z | 2026-06-18T11:38:35Z | 7m 56s |
| green | 2026-06-18T11:38:35Z | 2026-06-18T11:40:38Z | 2m 3s |
| review | 2026-06-18T11:40:38Z | 2026-06-18T11:43:50Z | 3m 12s |
| finish | 2026-06-18T11:43:50Z | - | - |

## Sm Assessment

**Story:** 119-6 — structural-only reuse refactor in `sidequest-server` (`sidequest/agents/llm_factory.py`).

**Scope (weighed):** Four single-shot Haiku adapter sites — `_AsideLlm.complete`, `_IntentRouterLlm.emit_tool`, `_UnseededObjectiveClassifierLlm.emit_tool`, and `infer_archetype_from_freeform` — repeat the same skeleton: pre-flight ceiling check → `build_agent_sdk_options` → `llm_request_span` + `_consume_to_result` + `_record_usage_telemetry` → `record_call` → structured-output extract/raise. Extract a shared `_call_haiku_sdk(...)` + `_extract_structured_output_or_raise(...)`. This is a verify-phase simplify-reuse high-confidence finding deferred from 119-3 (~40 lines saved).

**Constraints the next agents must honor:**
- **STRUCTURAL-ONLY, no behavior change.** The existing agents suite (1993 passing) must stay green.
- Each call site keeps its **distinct caller tag, model selection, and loud error type** — the helper parameterizes these, it does not flatten them.
- Single repo: `server`. Base branch `develop`. Branch `feat/119-6-consolidate-haiku-sdk-adapters`.

**Routing:** TDD phased workflow → RED phase. TEA writes characterization/regression tests that pin the current behavior of all four sites (caller tags, model, error types, telemetry) BEFORE the refactor, so the green phase proves no behavior drift. Owner: Argus Panoptes (TEA).

**No upstream findings at setup.**

## TEA Assessment

### Red Phase (test writing)

**Tests Required:** Yes — but as a **refactor-regression net**, not a RED→GREEN feature.

**Reason / posture:** 119-6 is STRUCTURAL-ONLY (no behavior change), so there is no
new behavior to drive from RED. The honest TDD shape for a no-op refactor is a
characterization/golden-master net: pin current behavior, keep it green through the
refactor. The existing 119-3 (`test_119_3_haiku_port.py`, 17 tests) and 93-1
(`test_93_1_archetype_inference.py`, 23 tests) suites already pin most of each site's
behavior. My hundred eyes found **three holes nothing currently pins** that this exact
"extract a shared `_call_haiku_sdk`" refactor could slip through, and closed them.

**Test File (new):**
- `tests/agents/test_119_6_haiku_adapter_consolidation.py` — 6 test items closing the
  three gaps. Drives the hermetic fake `query` seam (OQ-9); no live subscription.

| Gap | What it pins | Why the refactor threatens it |
|-----|--------------|-------------------------------|
| **A** | `archetype_inference` caller tag on its `llm.request` span **and** session-ledger `record_call` | The 119-3 per-site caller-tag parametrize covers router/aside/classifier but **omits the 4th site**. The shared helper takes `caller` as a parameter → a crossed tag silently corrupts [COST-1] attribution with nothing failing. |
| **B** | archetype forced-extraction options surface: `max_turns=2`, `allowed_tools=[]`, `output_format` json_schema with per-axis `enum`, `thinking={"type":"disabled"}` | The 119-3 options/thinking parametrize also omits archetype. The helper centralizes options-building → a crossed param for this site is unpinned. |
| **C** | `session_id=None` ceiling **BYPASS** for all four sites — a sessionless call must NOT call `check_ceiling`/`record_call` | The biggest risk: the helper centralizes the `if session_id is not None:` guard. Drop it → every sessionless call mis-records under a `None` session (No-Silent-Fallbacks violation in cost accounting). Previously only return-values were asserted for `session_id=None`, never the ledger. |

**Tests Written:** 6 items (2 archetype gap-A/B + 3 parametrized adapter bypass + 1 archetype bypass) covering the 3 gaps.
**Status:** GREEN on current pre-refactor code (the correct precondition for a refactor net). Verified via testing-runner: **43/43 passing** across the new file + both sibling suites, no collateral breakage.

### Rule Coverage

| Rule (lang-review python.md) | Test(s) | Status |
|------|---------|--------|
| #1 No silent exception swallowing (loud-raise / No-Silent-Fallbacks in cost accounting) | `test_sessionless_*_never_touches_the_ledger` (×4) — a sessionless call must not silently mis-record | green-on-current |
| #6 Test quality (meaningful assertions, no vacuous asserts) | self-check below | pass |
| (existing) per-site structured-output dict-or-raise + loud error types | already pinned by `test_119_3_haiku_port.py` / `test_93_1_*` — NOT re-tested (no redundant tests) | green |

**Rules checked:** the two lang-review rules with refactor-relevant test surface (#1, #6) have coverage; the rest of python.md is a Dev self-review checklist with no new test surface for a no-op refactor.
**Self-check:** 0 vacuous assertions — every test asserts a concrete value (`== payload`, `caller == 'archetype_inference'`, `spy.checked == []`, schema enum membership), never a bare truthy/`is_none` on an always-None.

**Model axis note (deliberately NOT tested):** all four sites use the identical Haiku
constant (`claude-haiku-4-5-20251001`), so a per-site model cross would not change the
observed value — a model-on-span assertion cannot distinguish a regression here and would
be vacuous. Caller tag (Gap A) is the meaningful per-site distinguisher.

**Handoff:** To Dev (Hephaestus) for the GREEN/implement phase. **Contract for Dev:** the
extraction must keep ALL of `test_119_6_*`, `test_119_3_haiku_port.py`, and
`test_93_1_archetype_inference.py` green. The helper must (1) parameterize `caller`, model,
`system_prompt`, and `output_format` per site — never flatten them; (2) keep each site's
distinct loud error type (`IntentRouterEmptyResponse` for router, `LlmClientError` for
classifier/aside/archetype); (3) **preserve the `if session_id is not None:` guard inside
the shared helper** (Gap C). If any of these tests go red, the refactor drifted.

## Dev Assessment

**Implementation Complete:** Yes — structural-only consolidation, no behavior change.

**Files Changed:**
- `sidequest/agents/llm_factory.py` — extracted two shared helpers and rewired all four single-shot Haiku sites through them:
  - `_call_haiku_sdk(*, user, model, system_prompt, caller, session_id, ceiling_usd, output_format=None)` — the shared skeleton: pre-flight ADR-134 `check_ceiling` (guarded by `session_id`) → `build_agent_sdk_options(max_turns=2, allowed_tools=[], output_format=...)` → `llm_request_span` + `_consume_to_result` + `_record_usage_telemetry` → `record_call` (same guard) → returns the terminal `ResultMessage`.
  - `_extract_structured_output_or_raise(result_msg, *, error_cls, label)` — the dict-or-raise contract for the three `output_format` sites; `error_cls` keeps each site's distinct loud type, `label` keeps it identifiable in the raised message.
  - `_AsideLlm.complete` → `_call_haiku_sdk(output_format=None)` + its own `is_error`/prose handling (no structured extraction).
  - `_IntentRouterLlm.emit_tool` → `_call_haiku_sdk(...)` + `_extract_structured_output_or_raise(error_cls=IntentRouterEmptyResponse, label="agent-sdk")`.
  - `_UnseededObjectiveClassifierLlm.emit_tool` → `_call_haiku_sdk(...)` + `_extract(error_cls=LlmClientError, label="unseeded objective classifier")`.
  - `infer_archetype_from_freeform` → keeps its missing-axis/empty-freeform/truncation/enum-validation logic; the SDK section now goes through `_call_haiku_sdk(caller="archetype_inference")` + `_extract(error_cls=LlmClientError, label="archetype inference")`.

**Contract honored (TEA's three points):** (1) `caller`, model, `system_prompt`, `output_format` are all per-site parameters — not flattened; (2) each site keeps its distinct loud error type; (3) the `if session_id is not None:` ADR-134 bypass lives inside `_call_haiku_sdk`, so every site bypasses identically (Gap C).

**Line delta:** +140 / −127 (net **+13**), NOT the estimated "~40 saved" — see deviation. The *duplicated skeleton* (4× ceiling-check / build-options / span / record-usage / record-call) is eliminated into one home; the net count is up only because the two new shared helpers carry house-style docstrings (shorter than neighbors like `build_agent_sdk_options` / `_record_usage_telemetry`). The maintainability win the simplify-reuse finding targeted — one place to change cost-safety/telemetry instead of four — is achieved.

**Tests:** **2063 passing / 0 failed / 2 skipped (pre-existing)** — the 119-6 characterization net + `test_119_3_haiku_port.py` + `test_llm_factory.py` + `test_93_1_archetype_inference.py` + `test_45_6_chargen_archetype_gate.py` + aside/router consumer wiring, plus the full `tests/agents/` suite. `ruff check` + `ruff format --check` clean on the file.
**Branch:** `feat/119-6-consolidate-haiku-sdk-adapters` (pushed; commits `a6c433d9` test, `2f4fb337` refactor).

**Handoff:** To Reviewer (Hermes) for the review phase.

### Rework Round 1 — format (Reviewer REJECT)

Hermes REJECTED solely for a mechanical blocker: `tests/agents/test_119_6_haiku_adapter_consolidation.py` failed `ruff format --check` (two cosmetic line-joins). Fixed with `uv run ruff format` on that one file (whitespace-only, no logic change). Both files now format-clean; `ruff check` clean; net re-verified **43/43 green**. Commit `db05127b`. No new code deviations (a format fix is not a spec deviation). Handing back to Reviewer.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): The 119-3 per-site caller-tag parametrize
  (`test_haiku_site_emits_caller_tagged_span_and_records_cost`) and the options/thinking
  parametrizes silently omit the `archetype_inference` site, leaving its caller tag and
  forced-extraction options surface unpinned until now. Affects
  `tests/agents/test_119_3_haiku_port.py` (consider folding the 4th site into those
  parametrizes in a future cleanup; 119-6 closes the gap in a dedicated file rather than
  editing the sibling so its diff stays minimal/structural).
  *Found by TEA during test design.*

### Dev (implementation)
- No upstream findings during implementation. The refactor was self-contained to
  `llm_factory.py`; all four sites' contracts (caller tag, model, error type, cost-safety,
  telemetry) carried over verbatim into the shared helpers, confirmed by the full
  `tests/agents/` suite plus the cross-module aside/router/archetype consumers.

### Reviewer (code review)
- No upstream findings during code review. The sole blocker (test-file `ruff format`) is a
  current-story mechanical fix captured in the Reviewer Assessment severity table, not an
  upstream/forward concern. The refactor itself is contained to `llm_factory.py` with no
  cross-subsystem ripples.

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

5 deviations

- **Refactor net is GREEN-on-current, not a failing RED suite**
  - Rationale: a no-behavior-change refactor has no new behavior to drive from RED; forcing a failing test would mean testing behavior that does not exist. The correct discipline is pin-current-behavior, keep-green-through-refactor. Verify-RED therefore shows the net passing — that IS the precondition.
  - Severity: minor
  - Forward impact: Dev's GREEN phase keeps the net green (no RED→GREEN flip to perform); a red result during/after the refactor signals drift.
- **Did NOT re-test behavior already pinned by sibling suites**
  - Rationale: redundant tests add maintenance cost without adding safety; the gap analysis showed those behaviors are already enforced.
  - Severity: minor
  - Forward impact: none — total coverage of the four sites is complete across the three files.
- **Net line count is +13, not the estimated "~40 saved"**
  - Rationale: the simplify-reuse finding's real goal is de-duplication / single-point-of-change, which is achieved. Stripping the helper docstrings below house style to hit an arbitrary line target would violate "match the surrounding code's comment density" and produce worse code. Code-logic lines went down; documentation lines offset the deletion.
  - Severity: minor
  - Forward impact: none — purely a metric-vs-estimate note; behavior and maintainability goal unaffected.
- **Forced-extraction loud-raise message now uniformly includes `num_turns`**
  - Rationale: a single message shape is the natural consequence of one shared extractor; `num_turns` is strictly more diagnostic info, and no test asserts message text (only the exception type). The constraint is "distinct loud error TYPE", which is preserved.
  - Severity: minor
  - Forward impact: none — any log/OTEL consumer keying on the message gets a superset; type-based handling is unchanged.
- **Archetype pre-flight ceiling check now fires inside `_call_haiku_sdk` (a few lines later)**
  - Rationale: centralizing the pre-flight refusal is exactly the skeleton the story asked to extract; the "no spend for a killed session" invariant is preserved (the query is still never reached) and the test stays green.
  - Severity: minor
  - Forward impact: none — only a microscopic amount of wasted pure-Python work on the already-killed-session path; no observable behavior change.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Refactor net is GREEN-on-current, not a failing RED suite**
  - Spec source: context-story-119-6.md (Title/Scope) + SM Assessment
  - Spec text: "STRUCTURAL-ONLY, no behavior change … the existing agents suite (1993 passed) must stay green"
  - Implementation: TEA wrote characterization/golden-master tests that PASS against current pre-refactor code, rather than a failing RED→GREEN suite.
  - Rationale: a no-behavior-change refactor has no new behavior to drive from RED; forcing a failing test would mean testing behavior that does not exist. The correct discipline is pin-current-behavior, keep-green-through-refactor. Verify-RED therefore shows the net passing — that IS the precondition.
  - Severity: minor
  - Forward impact: Dev's GREEN phase keeps the net green (no RED→GREEN flip to perform); a red result during/after the refactor signals drift.
- **Did NOT re-test behavior already pinned by sibling suites**
  - Spec source: context-story-119-6.md, Scope
  - Spec text: "each site keeps its distinct caller tag, model, and loud error type"
  - Implementation: only the THREE unpinned gaps (A/B/C) got new tests; the structured-output dict-or-raise contracts, router/aside/classifier caller tags, and max_turns/output_format surface are left to the existing `test_119_3_haiku_port.py` / `test_93_1_archetype_inference.py` coverage (run as collateral checks).
  - Rationale: redundant tests add maintenance cost without adding safety; the gap analysis showed those behaviors are already enforced.
  - Severity: minor
  - Forward impact: none — total coverage of the four sites is complete across the three files.

### Dev (implementation)
- **Net line count is +13, not the estimated "~40 saved"**
  - Spec source: context-story-119-6.md, Title; sprint story 119-6 description
  - Spec text: "Extract a shared _call_haiku_sdk(...) + _extract_structured_output_or_raise(...) (… ~40 lines saved)"
  - Implementation: the duplicated skeleton (4×) IS eliminated into one home, but the diff is +140/−127 (net +13) because the two new shared helpers carry house-style docstrings (matching the heavy-comment density of neighbors like `build_agent_sdk_options` / `_record_usage_telemetry`).
  - Rationale: the simplify-reuse finding's real goal is de-duplication / single-point-of-change, which is achieved. Stripping the helper docstrings below house style to hit an arbitrary line target would violate "match the surrounding code's comment density" and produce worse code. Code-logic lines went down; documentation lines offset the deletion.
  - Severity: minor
  - Forward impact: none — purely a metric-vs-estimate note; behavior and maintainability goal unaffected.
- **Forced-extraction loud-raise message now uniformly includes `num_turns`**
  - Spec source: tests `test_*_raises_on_none_structured_output` (test_119_3_haiku_port.py); story scope "distinct … loud error type"
  - Spec text: pre-refactor the router message included `num_turns`; the classifier/archetype messages included only `subtype` + `is_error`.
  - Implementation: the shared `_extract_structured_output_or_raise` emits one uniform message `"{label} returned no structured_output (subtype=…, is_error=…, num_turns=…)"`, so the classifier/archetype messages GAIN `num_turns`. The error TYPE per site is unchanged (IntentRouterEmptyResponse for the router; LlmClientError for the others).
  - Rationale: a single message shape is the natural consequence of one shared extractor; `num_turns` is strictly more diagnostic info, and no test asserts message text (only the exception type). The constraint is "distinct loud error TYPE", which is preserved.
  - Severity: minor
  - Forward impact: none — any log/OTEL consumer keying on the message gets a superset; type-based handling is unchanged.
- **Archetype pre-flight ceiling check now fires inside `_call_haiku_sdk` (a few lines later)**
  - Spec source: test_93_1_archetype_inference.py::test_inference_respects_hard_ceiling_preflight; story skeleton "pre-flight ceiling check"
  - Spec text: pre-refactor `infer_archetype_from_freeform` called `check_ceiling` BEFORE building `tool_schema`/`user`; the test asserts the SDK query is never called for a killed session (`len(fake_query.calls) == 0`).
  - Implementation: `check_ceiling` moved into the shared helper, so it now fires after the (cheap, pure-Python) `tool_schema`/`user` construction but still BEFORE `_consume_to_result` (the actual SDK query). The empty-freeform short-circuit still precedes everything.
  - Rationale: centralizing the pre-flight refusal is exactly the skeleton the story asked to extract; the "no spend for a killed session" invariant is preserved (the query is still never reached) and the test stays green.
  - Severity: minor
  - Forward impact: none — only a microscopic amount of wasted pure-Python work on the already-killed-session path; no observable behavior change.

### Reviewer (audit)
- **TEA: Refactor net is GREEN-on-current, not a failing RED suite** → ✓ ACCEPTED by Reviewer: correct discipline for a no-behavior-change refactor (characterization/golden-master). A forced-failing test would test nonexistent behavior. The net's green-before/green-after IS the proof of no drift.
- **TEA: Did NOT re-test behavior already pinned by sibling suites** → ✓ ACCEPTED by Reviewer: verified — `test_119_3_haiku_port.py` (17) + `test_93_1_archetype_inference.py` (23) pin the dict-or-raise contracts, router/aside/classifier caller tags, and options surface; re-testing would be redundant. The three new tests close the genuine gaps (A/B/C).
- **Dev: Net line count is +13, not "~40 saved"** → ✓ ACCEPTED by Reviewer: the de-duplication goal (single home for the skeleton) is achieved — confirmed by `[SIMPLE]`-style read: 4× inline skeleton → one `_call_haiku_sdk`. The +13 is house-style docstrings on the two new helpers, shorter than neighbors. Stripping them to hit a line target would violate "match surrounding comment density." Line count was an estimate, not an AC.
- **Dev: Forced-extraction loud-raise message now uniformly includes `num_turns`** → ✓ ACCEPTED by Reviewer: independently re-discovered by `[EDGE]` (high confidence). I VERIFIED nothing depends on the old text — zero production/test consumers of `"returned no structured_output"`; the only `match=` on `LlmClientError` (test_92_2:280) targets the unrelated `SIDEQUEST_CLASSIFICATION_BACKEND` env error. The error TYPE per site is preserved. Strictly additive diagnostic info → LOW, non-blocking.
- **Dev: Archetype pre-flight ceiling check now fires inside `_call_haiku_sdk` (a few lines later)** → ✓ ACCEPTED by Reviewer: independently re-discovered by `[EDGE]` (medium). I VERIFIED via `[SEC]` corroboration + own read (llm_factory.py:786-842) that `check_ceiling` still fires before `_consume_to_result` (the SDK query), so a killed session bills zero tokens — the load-bearing invariant. The only difference is a dict + f-string built before the refusal on the already-killed path: immaterial. `test_inference_respects_hard_ceiling_preflight` stays green (`fake_query.calls == 0`).

## Subagent Results (Round 1 — superseded)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 (format blocker) + GREEN tests/lint/types | confirmed 1, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | Yes | findings | 3 (1 reorder, 2 msg-divergence) | confirmed 3 (all LOW, non-blocking), dismissed 0 |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via `workflow.reviewer_subagents.silent_failure_hunter` |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via `workflow.reviewer_subagents.test_analyzer` |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via `workflow.reviewer_subagents.comment_analyzer` |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via `workflow.reviewer_subagents.type_design` |
| 7 | reviewer-security | Yes | clean | 0 | N/A (clean — all ADR-134/047/no-PAYG/no-silent rules verified preserved) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via `workflow.reviewer_subagents.simplifier` |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via `workflow.reviewer_subagents.rule_checker` |

**All received:** Yes (3 enabled returned: preflight, edge-hunter, security; 6 disabled via settings)
**Total findings:** 1 confirmed blocking (format), 4 confirmed non-blocking (LOW), 0 dismissed, 0 deferred

## Reviewer Assessment (Round 1 — REJECTED, superseded by Round 2 APPROVED below)

**Verdict:** REJECTED — single mechanical blocker (test-file format); the refactor itself is sound and approved on the merits.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [LOW] (rework trigger) | New test file fails `ruff format --check` (exit 1) — two cosmetic reformats (a `.append(...)` line-join and an assertion-string join). The Reviewer is read-only and cannot edit code; the project norm is formatted code, and `reviewer-preflight` flagged it as a pre-merge blocker. | `tests/agents/test_119_6_haiku_adapter_consolidation.py` | Run `uv run ruff format tests/agents/test_119_6_haiku_adapter_consolidation.py`, re-verify GREEN, commit. No logic change. |

**Why a LOW issue triggers rework, not approval:** Approval routes straight to SM finish (PR creation + merge). Merging a file that `ruff format` would rewrite ships unformatted code against project norm. Since the Reviewer cannot edit, the only correct path is a green-phase rework (one `ruff format` command). Everything else below is APPROVED — this is the *sole* change required.

### Observations (tagged by source)

- `[SEC]` **VERIFIED** — ADR-134 ceiling guard preserved: `_call_haiku_sdk` runs `if session_id is not None: check_ceiling(...)` (llm_factory.py:237) BEFORE `build_agent_sdk_options`/`_consume_to_result`, and `record_call` under the same guard (llm_factory.py:251). Security subagent: 0 violations across 4 sites. Complies with No-Silent-Fallbacks + ADR-134.
- `[SEC]` **VERIFIED** — per-site `caller` tags are literals with no crossing: `aside` / `intent_router` / `unseeded_objective_classifier` / `archetype_inference` ([COST-1] attribution intact). Pinned by the new Gap-A test for the archetype site.
- `[SEC]` **VERIFIED** — ADR-047 unchanged: the 4000-char truncation (llm_factory.py:784) and `<player_answers>` delimiter (llm_factory.py:817) still precede the `_call_haiku_sdk` call (829); `build_agent_sdk_options` remains the sole options path (no PAYG re-route).
- `[EDGE]` **CONFIRMED (LOW, non-blocking)** — forced-extraction loud-raise message now uniformly includes `num_turns` for the classifier/archetype sites. VERIFIED nothing depends on the old text: zero production/test consumers of `"returned no structured_output"`; the only `LlmClientError` `match=` (test_92_2:280) targets `SIDEQUEST_CLASSIFICATION_BACKEND`. Error TYPE preserved per site. Already logged as a Dev deviation → ACCEPTED.
- `[EDGE]` **CONFIRMED (LOW, non-blocking)** — archetype pre-flight `check_ceiling` now fires inside the helper (after `tool_schema`/`user` build, before the SDK query). Killed session bills zero tokens (query never reached); `test_inference_respects_hard_ceiling_preflight` green. Already logged as a Dev deviation → ACCEPTED.
- `[VERIFIED]` — aside behavior preserved: `_AsideLlm.complete` keeps its own `is_error` → raise and `result or ""` empty-string default after `_call_haiku_sdk(output_format=None)` (llm_factory.py:386-392). Loud-raise on failed query intact (No Silent Fallbacks).
- `[VERIFIED]` — error TYPE per site preserved: router → `IntentRouterEmptyResponse`, classifier/archetype → `LlmClientError`, passed via `error_cls` to the shared extractor — parameterized, not collapsed (llm_factory.py:476,668,844).
- `[SILENT]` — subagent disabled via settings; covered by my own + `[SEC]` analysis: every failure mode (None usage, None structured_output, is_error) raises loudly — no swallowed errors introduced.
- `[TEST]` — subagent disabled via settings; assessed by Reviewer + `reviewer-preflight`: the 3 new tests assert concrete values (`== payload`, `caller == 'archetype_inference'`, `spy.checked == []`, schema enum membership) — no vacuous assertions; 49/49 green.
- `[DOC]` — subagent disabled via settings; Reviewer read confirms the two new helpers carry accurate docstrings; the per-site inline comments correctly describe the 119-6 delegation; no stale comments left behind.
- `[TYPE]` — subagent disabled via settings; Reviewer + pyright (0 errors) confirm `_call_haiku_sdk` / `_extract_structured_output_or_raise` are fully annotated; `error_cls: type[LlmClientError]` correctly accepts `IntentRouterEmptyResponse` (a subclass).
- `[SIMPLE]` — subagent disabled via settings; Reviewer read confirms the de-duplication is the simplification: 4× inline skeleton → one helper. No over-engineering; the helper has exactly the parameters the four sites vary on.
- `[RULE]` — subagent disabled via settings; rule-by-rule compliance enumerated below.

### Rule Compliance

| Rule (source) | Scope checked | Verdict |
|---------------|---------------|---------|
| No Silent Fallbacks (CLAUDE.md/SOUL.md) | all 4 sites + 2 helpers: None usage → raise (`_record_usage_telemetry`); None structured_output → raise (`_extract_structured_output_or_raise`); aside is_error → raise | COMPLIANT |
| python.md #1 silent exception swallowing | full diff — no bare `except`, no swallow, no `suppress()` | COMPLIANT |
| python.md #3 type annotations at boundaries | both helpers fully annotated (private helpers are exempt anyway) | COMPLIANT |
| python.md #4 logging level/correctness | archetype truncation `logger.warning`, lazy `%s` args; no sensitive data | COMPLIANT |
| python.md #6 test quality | 3 new tests — concrete assertions, no vacuous, conditional content-skip is a valid guard | COMPLIANT |
| python.md #9 async/await | `_call_haiku_sdk` async, awaited at all 4 sites; no blocking calls inside | COMPLIANT |
| OTEL Observability (CLAUDE.md) | every site still opens an `llm.request` span via `llm_request_span` inside the helper; caller tag stamped | COMPLIANT |
| ADR-134 cost ceiling / bypass | `[SEC]` verified across 4 sites + Gap-C tests | COMPLIANT |
| ADR-047 prompt-injection | truncation + delimiter preserved before SDK call | COMPLIANT |
| **`ruff format` (project norm / `just server-fmt`)** | `llm_factory.py` clean; **`test_119_6_*.py` would be reformatted** | **VIOLATION → rework** |

### Devil's Advocate

Let me argue this refactor is broken. First attack: a centralizing helper is the classic place a guard silently disappears — if `_call_haiku_sdk` dropped the `if session_id is not None:` around `record_call`, every sessionless aside/router/classifier call would invoke `ledger().record_call(session_id=None, ...)`, mis-recording spend under a phantom session and possibly raising inside a path that previously couldn't. I checked: the guard is present at BOTH ledger ops (lines 237 and 251), and the new Gap-C tests (`test_sessionless_*_never_touches_the_ledger`) assert `spy.checked == []` and `spy.recorded == []` for all four sites with `session_id=None`. Refuted.

Second attack: the aside passes `output_format=None`; what if that's not equivalent to the old call that omitted the kwarg? If `build_agent_sdk_options` treated `None` differently it would flip the thinking-disable branch and change the aside's behavior. I read the builder: default is `None` and the branch is `if output_format is not None and thinking is None`, so `None` and omission are identical — `test_aside_leaves_thinking_unset` confirms thinking stays unset. Refuted.

Third attack: the archetype pre-flight moved later — could a killed session now bill a token? The check now fires after building `tool_schema`/`user`, but still before `_consume_to_result`; the fake-query test asserts `calls == 0` for a killed session. No token billed. Refuted.

Fourth attack: a confused maintainer reading the uniform error message might think `num_turns` was always there for the classifier and write a parser against it — but no consumer keys on the text today, and the addition is strictly more information. Low risk.

Fifth attack — the one that lands: the test file ships unformatted. A stressed CI or a teammate running `just server-fmt` would see a diff, and a reviewer who rubber-stamped it would have let non-conforming code merge. That is the real defect here, and it is why this is a REJECT. The logic is sound; the hygiene is not yet.

**Handoff:** Back to Dev (Hephaestus) for a format-only green rework — `uv run ruff format tests/agents/test_119_6_haiku_adapter_consolidation.py`, re-verify, hand back to review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (format blocker RESOLVED; 43/43 green; lint+format clean) | confirmed 0 — prior blocker cleared |
| 2 | reviewer-edge-hunter | Yes | findings (carried from Round 1) | 3 (all LOW, non-blocking, accepted) | production `llm_factory.py` byte-identical since Round 1 (`git diff 2f4fb337..HEAD` empty on the source) → Round-1 analysis still valid |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via `workflow.reviewer_subagents.silent_failure_hunter` |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via `workflow.reviewer_subagents.test_analyzer` |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via `workflow.reviewer_subagents.comment_analyzer` |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via `workflow.reviewer_subagents.type_design` |
| 7 | reviewer-security | Yes | clean (carried from Round 1) | 0 | production code byte-identical since Round 1 → 0 violations still holds |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via `workflow.reviewer_subagents.simplifier` |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via `workflow.reviewer_subagents.rule_checker` |

**All received:** Yes (preflight re-run fresh this round; edge-hunter + security carried forward because the production diff since Round 1 is empty — only test-file whitespace changed; 6 disabled via settings)
**Total findings:** 0 blocking, 4 LOW non-blocking (all accepted, carried from Round 1), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

The Round-1 REJECT's sole blocker — `tests/agents/test_119_6_haiku_adapter_consolidation.py` failing `ruff format --check` — is resolved (commit `db05127b`, whitespace-only). I VERIFIED the rework is strictly a format change: `git diff 2f4fb337..HEAD` is **empty for `sidequest/agents/llm_factory.py`** (production code byte-identical to what I already cleared) and the test-file diff is two line-joins (the assertion string-join preserves the identical runtime message). `ruff format --check` now exits 0 on both files; lint clean; **43/43 tests green**.

**Data flow traced:** player `freeform_text` → `infer_archetype_from_freeform` (bounded to 4000 chars + wrapped in `<player_answers>` delimiter, ADR-047) → `_call_haiku_sdk(caller="archetype_inference", session_id, ceiling_usd, output_format=schema)` → pre-flight `check_ceiling` (guarded; fires before the SDK query) → `build_agent_sdk_options` → `_consume_to_result` → `_record_usage_telemetry` (raises on absent usage — No Silent Fallbacks) → `record_call` (guarded) → `_extract_structured_output_or_raise(error_cls=LlmClientError)` → enum validation. Safe: each hop preserves the per-site caller tag, the loud-raise contract, and the `session_id=None` ledger bypass. `[SEC]` confirmed 0 violations across all four sites.

**Pattern observed:** clean Extract-Method de-duplication — `sidequest/agents/llm_factory.py:201` (`_call_haiku_sdk`) + `:275` (`_extract_structured_output_or_raise`) collapse the 4× repeated skeleton into one home, parameterized on exactly what the sites vary (model, caller, system_prompt, output_format, error_cls, label). `[SIMPLE]`: no over-engineering. `[TYPE]`: both helpers fully annotated; `error_cls: type[LlmClientError]` correctly accepts the `IntentRouterEmptyResponse` subclass (pyright 0 errors).

**Error handling:** every failure mode still raises loudly — absent usage (`_record_usage_telemetry`), absent `structured_output` (`_extract_structured_output_or_raise`, per-site `error_cls`), aside `is_error` (`_AsideLlm.complete:386`). `[SILENT]`: no swallowed errors introduced. `[DOC]`: helper docstrings accurate; per-site delegation comments correct. `[TEST]`: 3 new tests assert concrete values, no vacuous assertions. `[EDGE]`: the two message-`num_turns` additions and the archetype pre-flight reorder are LOW/non-blocking (verified nothing depends on the old text; killed session still bills zero tokens). `[RULE]`: full Rule Compliance table in the Round-1 section — all COMPLIANT now that the `ruff format` row is resolved.

**Deviations:** all five (2 TEA + 3 Dev) audited and stamped ACCEPTED in `### Reviewer (audit)`. The rework introduced no new deviations (a format fix is not a spec deviation).

**Handoff:** To SM (Themis) for finish-story.