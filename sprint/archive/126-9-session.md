---
story_id: "126-9"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 126-9: [PERF] Narrator + intent_router_pass turn-latency ~3x regression landed Jun 17 (no router thrash) — bisect + fix

## Story Details
- **ID:** 126-9
- **Jira Key:** (not in use for this project)
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 5
- **Priority:** p1
- **Type:** bug

## Technical Context

### Root Cause (CONFIRMED via bisect, AC #1 satisfied)
The narrator now runs with EXTENDED THINKING ON by default — an accidental side-effect of the 119-3 port (commit f970091e, PR #908).

**Trigger:** Commit f970091e (PR #908, "feat(119-3): port narrator + 4 Haiku sites onto claude-agent-sdk over subscription auth", Jun 16 05:32 EDT) moved the narrator from the `anthropic` Messages SDK (thinking OFF by default) to the `claude-agent-sdk` query() loop (thinking defaults ON/adaptive).

**Consequence:** sonnet-4.6 now runs an adaptive thinking pass before EACH of up to 8 tool-loop iterations:
- Pre-fix: narrator agent_duration_ms ~16s → turn total ~20s
- Post-regression: narrator agent_duration_ms ~50-57s → turn total ~70s (same-world proof: wry_whimsy/oz 15.9s → 56.7s)

### Mechanism (file:line references)
**File:** `sidequest/agents/anthropic_sdk_client.py`

- Lines 438-444: the narrator's `complete_with_tools` call builds options via `build_agent_sdk_options` but passes neither `thinking` nor `output_format`
- Lines 262-263: the auto-disable logic fires ONLY when `output_format is not None and thinking is None` → narrator's `thinking` stays None
- Result: claude CLI adaptive default (ON) applies to the narrator tool-loop
- Max iterations: 8 (orchestrator.py:4089)

### The Fix (GREEN, one line, behavior-restore to pre-119-3 baseline)
Pass `thinking={"type":"disabled"}` on the narrator's `complete_with_tools` call (and the aside path if it shows the same cost).

**DO NOT use SIDEQUEST_NARRATOR_ITERATION_CAP** — that caps narration depth/quality and conflates two concerns.

### Separate Issue (OUT OF SCOPE — tracked in 126-10)
The intent_router_pass Fate spikes (37-81s on a single call) are NOT thinking; they are PROMPT BLOAT from `build_fate_projection`. Thinking-off does NOT fix them. This story's AC #5 excludes this.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-18T00:35:36Z
**Round-Trip Count:** 1
**Branch Strategy:** gitflow (feat/126-9-narrator-latency-restore)

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-18T00:04:18Z | - | - |
| red | - | 2026-06-18T00:17:08Z | unknown |
| green | 2026-06-18T00:17:08Z | 2026-06-18T00:20:40Z | 3m 32s |
| review | 2026-06-18T00:20:40Z | 2026-06-18T00:28:54Z | 8m 14s |
| green | 2026-06-18T00:28:54Z | 2026-06-18T00:32:04Z | 3m 10s |
| review | 2026-06-18T00:32:04Z | 2026-06-18T00:35:36Z | 3m 32s |
| finish | 2026-06-18T00:35:36Z | - | - |

## Acceptance Criteria

1. **Root cause confirmed:** narrator extended-thinking ON via the 119-3 agent-sdk port (f970091e). [SATISFIED by bisect]

2. **Narrator latency restored:** agent_duration_ms restored to ~baseline (~16s; non-Fate total ~20-25s) by passing `thinking={"type":"disabled"}` on the narrator's `complete_with_tools` call (and aside path if same).

3. **Regression guard added:** OTEL or unit test that fails if the narrator call enables thinking, or if narrator p95 exceeds a threshold — so this cannot silently regress again.
   - **RED phase approach:** a unit test asserting the narrator's `build_agent_sdk_options` call has `thinking` disabled (no running server needed).

4. **Verified before/after:** fresh non-Fate 2-seat understudy run shows agent_duration_ms drop.
   - **DB location:** Postgres `sidequest` → table `turn_telemetry`
   - **Query:** rows where `component='validator' AND event_type='turn_complete'`, extract `payload_json->>'agent_duration_ms'`

5. **Out of scope:** Fate-world intent_router_pass spike (build_fate_projection prompt bloat) is tracked in 126-10. Thinking-off does NOT fix it. DO NOT touch it here.

## Delivery Findings

No upstream findings at setup.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): the fix is the single unconditional `thinking={"type":"disabled"}` at the lone `build_agent_sdk_options` call inside `complete_with_tools` (`anthropic_sdk_client.py:438`). That one call site serves BOTH the narrator AND the narrator-aside (`aside_resolver.py:301`, `caller="aside"`, `tool_choice={"type":"none"}`), so it satisfies AC #2's "(and aside path if same)" with no second edit. Do NOT touch `llm_factory.build_aside_llm` — that Haiku aside is a *separate* call site / cheap single-shot model, is not the regression, and `test_119_3_haiku_port.py::test_aside_leaves_thinking_unset` must stay green. Affects `sidequest/agents/anthropic_sdk_client.py` (one line). *Found by TEA during test design.*
- **Improvement** (non-blocking): the story *description* prose still references a pre-split "SECONDARY / AC #3" for the Fate `intent_router_pass` bloat; the authoritative AC list (AC #5) marks that OUT OF SCOPE → 126-10. Trust the YAML `acceptance_criteria`, not the description prose. Affects story 126-9 metadata (cosmetic lag after the split). *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking for review; owed before story finish): AC #4 (live before/after `agent_duration_ms` on a fresh non-Fate 2-seat understudy run) is NOT performed in the green phase. It is a post-merge operational verification — it needs a server carrying the fix, and restarting the server pre-merge would kill the live playtest on the oq-3 checkout (`:8765`). Per the story's own cross-workspace note, the re-measure happens after merge (oq-3 pulls develop + restarts, or oq-1 takes the port). The code correctness is proven deterministically by the AC #3 unit guard (thinking is now `{"type":"disabled"}` in the options handed to `query()`); AC #4 is corroboration of the latency drop. Affects ops/verification, not code. *Found by Dev during implementation.*
- No other upstream findings during implementation.

### Reviewer (code review)
- **Improvement** (non-blocking): close the orchestrator→thinking-disabled chain end-to-end by adding `assert fake.last_options.thinking == {"type": "disabled"}` to the existing wiring test. Affects `sidequest-server/tests/agents/test_narrator_uses_sdk_client.py` (one-line addition to `test_orchestrator_routes_narration_through_sdk`). *Found by Reviewer during code review.*
- **Question** (non-blocking): AC #4's live before/after re-measure (Dev finding) remains owed post-merge — recommend SM/Keith run it after develop carries the fix before treating the story as fully closed. Affects ops/verification. *Found by Reviewer during code review.*
- **Re-review (round 1):** both round-1 blocking DOC findings resolved; recommended wiring assertion landed. No new upstream findings. *Found by Reviewer during re-review.*

## Impact Summary

**Upstream Effects:** 2 findings (0 Gap, 0 Conflict, 0 Question, 2 Improvement)
**Blocking:** None

- **Improvement:** the fix is the single unconditional `thinking={"type":"disabled"}` at the lone `build_agent_sdk_options` call inside `complete_with_tools` (`anthropic_sdk_client.py:438`). That one call site serves BOTH the narrator AND the narrator-aside (`aside_resolver.py:301`, `caller="aside"`, `tool_choice={"type":"none"}`), so it satisfies AC #2's "(and aside path if same)" with no second edit. Do NOT touch `llm_factory.build_aside_llm` — that Haiku aside is a *separate* call site / cheap single-shot model, is not the regression, and `test_119_3_haiku_port.py::test_aside_leaves_thinking_unset` must stay green. Affects `sidequest/agents/anthropic_sdk_client.py`.
- **Improvement:** close the orchestrator→thinking-disabled chain end-to-end by adding `assert fake.last_options.thinking == {"type": "disabled"}` to the existing wiring test. Affects `sidequest-server/tests/agents/test_narrator_uses_sdk_client.py`.

### Downstream Effects

Cross-module impact: 2 findings across 2 modules

- **`sidequest-server/tests/agents`** — 1 finding
- **`sidequest/agents`** — 1 finding

### Deviation Justifications

1 deviation

- **Behaviour assertion on produced options instead of a `build_agent_sdk_options` call-spy**
  - Rationale: CLAUDE.md "No Source-Text Wiring Tests" — an arg-spy couples to call shape; asserting the produced options is the behaviour the regression actually turns on, survives refactor, and still fails the instant thinking is re-enabled. Same guard, stronger form.
  - Severity: minor

## Design Deviations

No deviations at setup.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Behaviour assertion on produced options instead of a `build_agent_sdk_options` call-spy**
  - Spec source: context-story-126-9.md, AC #3 (RED approach)
  - Spec text: "a unit test asserting the narrator's `build_agent_sdk_options` call has `thinking` disabled (no running server needed)"
  - Implementation: the tests drive the real `complete_with_tools` with the `query()` seam faked and assert the `ClaudeAgentOptions` handed to `query()` carry `thinking={"type":"disabled"}`, rather than spying on `build_agent_sdk_options`'s call args.
  - Rationale: CLAUDE.md "No Source-Text Wiring Tests" — an arg-spy couples to call shape; asserting the produced options is the behaviour the regression actually turns on, survives refactor, and still fails the instant thinking is re-enabled. Same guard, stronger form.
  - Severity: minor
  - Forward impact: none

### Dev (implementation)
- No deviations from spec. Implemented exactly the spec'd one-line fix (`thinking={"type":"disabled"}`) at the spec'd call site (`anthropic_sdk_client.py`, the single `build_agent_sdk_options` call inside `complete_with_tools`). Did not use `SIDEQUEST_NARRATOR_ITERATION_CAP`; did not touch `build_fate_projection` / `intent_router_pass` (AC #5) or `llm_factory.build_aside_llm`. AC #4's live re-measure is deferred-by-design to post-merge per the story's cross-workspace note (recorded as a Delivery Finding, not a deviation).

## TEA Assessment

**Tests Required:** Yes
**Reason:** p1 latency regression with a confirmed root cause; AC #3 requires a regression guard so the narrator's accidental extended-thinking cannot silently return.

**Test Files:**
- `sidequest-server/tests/agents/test_126_9_narrator_thinking_disabled.py` — pins that the narrator tool-loop (and the narrator-aside caller) builds `ClaudeAgentOptions` with `thinking={"type":"disabled"}`.

**Tests Written:** 2 tests covering AC #3 (regression guard) and AC #2's aside parenthetical
**Status:** RED — both failing on the assertion (`got thinking=None`, expected `{"type":"disabled"}`), not on import/fixture/collection. Pre-existing `test_119_3_haiku_port.py::{test_aside_leaves_thinking_unset, test_build_options_thinking_invariant}` still PASS (separate Haiku/builder paths, no conflict).

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| CLAUDE.md "No Source-Text Wiring Tests" | both tests assert on the produced `ClaudeAgentOptions` via the faked `query()` seam — no source-text grep | failing (RED) |
| CLAUDE.md "Every Test Suite Needs a Wiring Test" | narrator-turn → `complete_with_tools` reachability held by `test_narrator_uses_sdk_client.py::test_orchestrator_routes_narration_through_sdk`; new tests exercise the real `complete_with_tools` | existing (green) |
| "Every test asserts something meaningful" | both use exact dict equality `== {"type":"disabled"}` with a diagnostic message | failing (RED) |

**Rules checked:** test-strategy rules (no source-text grep; meaningful assertions; wiring coverage) satisfied. The Rust-flavoured lang-review checklist (`non_exhaustive`, validated constructors, Deserialize bypass, private fields, tenant context) does not apply — this is a Python one-line call-site behaviour change, no new types/constructors/enums. NOTE: `.pennyfarthing/gates/lang-review/python.md` is not present in this checkout, so the checklist could not be read directly (infra absent here, not skipped to save time).
**Self-check:** 0 vacuous tests — both assert exact `== {"type":"disabled"}` equality, not `is_some`/`is_none` truthiness.

**Handoff:** To Dev (Naomi Nagata) for GREEN — pass `thinking={"type":"disabled"}` at `anthropic_sdk_client.py:438`. See `## Delivery Findings → TEA` for the do-NOT-touch scope (Haiku `build_aside_llm` stays as-is).

---

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/sidequest/agents/anthropic_sdk_client.py` — pass `thinking={"type":"disabled"}` on the narrator tool-loop's `build_agent_sdk_options` call (the single call site inside `complete_with_tools`). Restores the pre-119-3 thinking-off baseline so the `claude` CLI adaptive default no longer runs a thinking pass before each of up to 8 tool-loop iterations. Behaviour restore, not a quality cut.

**Tests:** GREEN — 2/2 new tests pass; 27/27 across the thinking + narrator-SDK suites (`test_119_3_haiku_port.py`, `test_119_3_narrator_behavior_on_agent_sdk.py`, `test_narrator_uses_sdk_client.py`) with no regression. The Haiku-aside guard `test_aside_leaves_thinking_unset` stays green, confirming the fix is scoped to `complete_with_tools` and does not touch `build_aside_llm`.
**Lint/format:** `ruff check` + `ruff format --check` clean on the changed file.
**Branch:** feat/126-9-narrator-latency-restore (pushed to origin/slabgorb-org).

**AC status:**
- AC #1 (root cause) — SATISFIED (bisect, pre-existing).
- AC #2 (latency restored via `thinking=disabled`) — code applied; deterministic proof via the AC #3 unit guard. Live latency confirmation is AC #4.
- AC #3 (regression guard) — DONE (`test_126_9_narrator_thinking_disabled.py`, GREEN).
- AC #4 (live before/after on a fresh non-Fate understudy run) — NOT done in this phase; post-merge operational verification owed (see `## Delivery Findings → Dev`).
- AC #5 (Fate `intent_router_pass` OUT OF SCOPE) — respected; `build_fate_projection` / `intent_router_pass` untouched.

**Handoff:** To Reviewer (Chrisjen Avasarala) for code review.

---

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (28 passed, lint+format clean) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 4 | confirmed 2 (non-blocking), dismissed 0, deferred 2 (low) |
| 5 | reviewer-comment-analyzer | Yes | findings | 2 | confirmed 2 (1 blocking-MED, 1 LOW) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | 0 (7 rules / 19 instances) | N/A |

**All received:** Yes (4 enabled returned; 5 disabled via `workflow.reviewer_subagents`)
**Total findings:** 2 confirmed blocking (1 MED docstring, 1 LOW line-ref), 2 confirmed non-blocking (MED test-hardening), 2 deferred low; 0 dismissed

## Rule Compliance

Project rules come from CLAUDE.md + SOUL.md (no `.claude/rules/*.md`; `.pennyfarthing/gates/lang-review/python.md` not present in this checkout — noted, not skipped to save effort). Rust-flavoured checks (non_exhaustive / validated constructors / serde bypass / private fields / tenant context) do not apply — Python, one-kwarg call-site change, no new types.

- **No Silent Fallbacks** — COMPLIANT. `thinking={"type":"disabled"}` (anthropic_sdk_client.py ~458) is an explicit unconditional literal, not a fallback. The builder auto-disable (262-263) is gated on `output_format is not None`, which is False at this call site, so there is no silent-substitution interaction. `assert_subscription_auth()` still fires.
- **No Stubbing** — COMPLIANT. No placeholders; both tests fully implemented with real assertions; no skips.
- **Don't Reinvent / Wire Up What Exists** — COMPLIANT. Reuses the pre-existing `thinking` param of `build_agent_sdk_options`; tests reuse `FakeQuery`/`converged_text_stream` and the OQ-9 `query` seam.
- **Every Test Suite Needs a Wiring Test / Verify Wiring** — COMPLIANT. New tests drive the real `complete_with_tools`; orchestrator→`complete_with_tools` reachability held by `test_narrator_uses_sdk_client.py::test_orchestrator_routes_narration_through_sdk` (verified present). See [TEST] MED below: that wiring test does not itself assert thinking-off (recommended, non-blocking).
- **No Source-Text Wiring Tests** — COMPLIANT. Both tests assert on the runtime `ClaudeAgentOptions` handed to the faked `query()`; no `read_text()`/regex against source.
- **OTEL Observability Principle** — COMPLIANT under the behaviour-restore exception. No new subsystem decision is introduced; existing `llm_request_span` + `narrator_tool_loop_span` already surface the latency/cost symptom, and AC #3 explicitly permits "OTEL OR unit test" (unit test chosen). A future `llm.thinking_disabled` attribute on the existing span would be the minimal enhancement if ever wanted — not required.
- **Bind the Ruleset, Don't Balance It** — N/A (no combat/ruleset code touched).

## Reviewer Assessment

**Verdict:** REJECTED (documentation incoherence introduced by the diff — code is correct; fixes are trivial)

The fix is correct, minimal, tested (28 green), lint/format-clean, and rule-clean. I am rejecting solely to keep the change self-consistent: the diff changes the narrator tool-loop's thinking behaviour but leaves a docstring in the *same function* asserting the opposite, and ships a wrong line reference. Both are ~1-line fixes; leaving them is a revert-hazard for a regression fix. Route is green rework (docs/quality), not red.

**Blocking:**

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [DOC][MEDIUM] | Stale docstring: `build_agent_sdk_options` still says "Non-structured callers (narrator tool-loop, aside) are untouched — `thinking` stays `None` for them." After this fix the narrator tool-loop (and narrator-aside) caller passes `thinking={"type":"disabled"}` explicitly, so that example is now false — and it sits in the very function whose call-site behaviour the story inverts (revert-hazard). | `sidequest/agents/anthropic_sdk_client.py:258-259` | Update the parenthetical: the builder still only *auto-*disables for `output_format` calls, but `complete_with_tools` (narrator + narrator-aside, Story 126-9) now passes `thinking` explicitly, so those callers no longer end up `None`. |
| [DOC][LOW] | Test module docstring line reference off by one: `aside_resolver.py:301` — the `caller="aside"` kwarg is at line 302. | `tests/agents/test_126_9_narrator_thinking_disabled.py:24` | Change `aside_resolver.py:301` → `:302`. |

**Recommended (non-blocking — Dev's discretion while reworking):**

- [TEST][MEDIUM] The existing wiring test `test_orchestrator_routes_narration_through_sdk` does not assert thinking-off, so no single test chains orchestrator→thinking-disabled end-to-end. Cheap to close: add `assert fake.last_options.thinking == {"type": "disabled"}` there. Regression is already adequately guarded by the two new unit tests, so this is hardening, not a gap. (`tests/agents/test_narrator_uses_sdk_client.py:77`)
- [TEST][LOW] Both new tests pass `tool_dispatch=None` (skips the `_build_narration_mcp` branch). The `thinking` kwarg is set unconditionally *after* the MCP build (rule-checker confirmed), so coverage is adequate; a non-None-dispatch variant would only harden against a future refactor moving the kwarg. Optional.

**Observations (5+):**
- [VERIFIED] Single call site, unconditional disable — evidence: `anthropic_sdk_client.py:438-459`, `thinking={"type":"disabled"}` appended to the lone `build_agent_sdk_options` call inside `complete_with_tools`, set after `_build_narration_mcp` (line 437). Complies with No Silent Fallbacks (explicit literal).
- [VERIFIED] Narrator + narrator-aside both covered by one site — `aside_resolver.py:302` calls `complete_with_tools(caller="aside")`; method has exactly one `build_agent_sdk_options` call. The Haiku `build_aside_llm` (separate llm_factory site) is correctly left untouched; `test_aside_leaves_thinking_unset` + `test_build_options_thinking_invariant` stay green.
- [RULE] rule-checker clean: 7 rules / 19 instances, 0 violations.
- [DOC][MEDIUM] stale docstring (blocking, above).
- [DOC][LOW] off-by-one line ref (blocking-trivial, above).
- [TEST][MEDIUM] wiring test lacks a thinking assertion (recommended, above).
- [TEST][LOW] `getattr(..., "MISSING")` sentinel + the `caller="aside"` stimulus not being load-bearing — test-analyzer confirmed both tests are structurally sound and non-vacuous; these are clarity nits only. Deferred (low).
- [SEC] No security surface touched — `thinking` is an internal SDK option; the subscription-auth assert is unchanged; no auth/input/secret/tenant change. (Subagent disabled; assessed directly.)
- [EDGE] Disabled — assessed directly: the only "edge" is thinking applied regardless of `caller`/iteration count, which is the intended unconditional restore.
- [SILENT] Disabled — assessed directly: no swallowed errors / empty catches / silent fallbacks introduced by a single kwarg.
- [TYPE] Disabled — assessed directly: `thinking: dict[str,Any]|None`; literal `{"type":"disabled"}` matches the existing 262-263 usage.
- [SIMPLE] Disabled — assessed directly: minimal one-kwarg change; no over-engineering or dead code.

**Data flow traced:** player action → orchestrator narration turn → `complete_with_tools(...)` → `build_agent_sdk_options(..., thinking={"type":"disabled"})` → `ClaudeAgentOptions` → `query(prompt, options)` → agent-sdk loop runs with no per-iteration adaptive thinking pass → terminal `ResultMessage` → `ToolingResult`. Safe: disabling thinking removes only the model's hidden scratchpad; the prescriptive narrator prompt and tool loop are unchanged.

**Tenant isolation:** N/A — single-tenant personal project; no tenant data on this path.

### Devil's Advocate

Argue the change is broken. First angle: quality regression. Disabling extended thinking could blunt the narrator that must be "good enough to fool a career GM." But the narrator ran *without* thinking from project inception until the accidental Jun-16 enablement — thinking-off is the long-playtested baseline, not untested territory. This restores known-good behaviour; it does not gamble. The recorded product decision is that any future thinking be a deliberate, bounded opt-in. Second angle: blast radius. Could the kwarg leak into structured/`output_format` calls and break the intent router or classifiers? No — it is applied only at the `complete_with_tools` call site, which never passes `output_format`; the Haiku/structured sites in `llm_factory` are untouched, proven by `test_build_options_thinking_invariant` and `test_aside_leaves_thinking_unset` staying green. Third angle: a malformed option. `{"type":"disabled"}` is the documented disable shape already used at 262-263 and live in production for output_format calls — not a novel payload. Fourth: concurrency/state. Options are built per call; no shared mutable state, no new race. Fifth, and the real residual risk: a future maintainer reads the now-false docstring ("narrator tool-loop … thinking stays None"), concludes the explicit kwarg is redundant, and deletes it — silently reintroducing the 3× regression. That is precisely why the stale docstring is blocking rather than a footnote: the regression's resurrection vector is the misleading comment, not the code. Fix the comment and the change is sound.

### Reviewer (audit)
- TEA deviation (behaviour assertion on produced options vs `build_agent_sdk_options` call-spy) → ✓ ACCEPTED by Reviewer: the behaviour assertion is the stronger form and is mandated by CLAUDE.md "No Source-Text Wiring Tests"; rule-checker confirmed compliant.
- Dev "No deviations from spec" → ✓ ACCEPTED by Reviewer: confirmed — the implementation is exactly the spec'd one-kwarg fix at the spec'd site; no use of `SIDEQUEST_NARRATOR_ITERATION_CAP`; `build_fate_projection`/`intent_router_pass` (AC #5) and `build_aside_llm` untouched.
- No undocumented deviations found.

**Handoff:** Back to Dev (Naomi Nagata) for green rework — fix the two blocking DOC items; the wiring-test assertion is recommended.

---

## Dev Assessment (Rework — Round 1)

**All Reviewer findings addressed:**
- [DOC][MEDIUM] blocking — **FIXED.** `build_agent_sdk_options` docstring (`anthropic_sdk_client.py:257-264`) reworded: the builder still only *auto*-disables for `output_format` calls, but `complete_with_tools` (narrator + narrator-aside) now passes `thinking={"type":"disabled"}` explicitly, so those callers are no longer `None`; the kwarg is called out as load-bearing (anti-revert).
- [DOC][LOW] blocking — **FIXED.** Test module docstring line refs `aside_resolver.py:301` → `:302` (both occurrences).
- [TEST][MEDIUM] recommended — **DONE.** Added `assert fake.last_options.thinking == {"type": "disabled"}` to `test_orchestrator_routes_narration_through_sdk` (`test_narrator_uses_sdk_client.py:170`). This closes the orchestrator→thinking chain end-to-end and, because that test drives the real `complete_with_tools` with a non-None `tool_dispatch`, also covers the MCP-present path (test-analyzer's tool_dispatch concern).

**Tests:** GREEN — 27 affected tests pass (incl. the new end-to-end assertion). **Lint/format:** clean on all 3 changed files.
**Commit:** fbcb958f (pushed). **Branch:** feat/126-9-narrator-latency-restore.
**No new deviations.** AC #4 (live re-measure) remains the owed post-merge step (unchanged).

**Handoff:** Back to Reviewer (Chrisjen Avasarala) for re-review (round-trip 1).

---

## Subagent Results

(Re-review — round-trip 1, on the reworked HEAD)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (27 passed, lint+format clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | clean | 0 (new assertion sound; MCP-path concern closed) | N/A |
| 5 | reviewer-comment-analyzer | Yes | clean | 0 (both prior DOC findings resolved; no new) | N/A |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | 0 (9 rules / 18 instances) | N/A |

**All received:** Yes (4 enabled returned clean; 5 disabled via `workflow.reviewer_subagents`)
**Total findings:** 0 — both round-1 blocking DOC findings verified resolved; recommended wiring assertion verified landed; no new issues.

## Reviewer Assessment

**Verdict:** APPROVED

Re-review of round-trip 1. Both round-1 blocking findings are fixed and independently re-verified; the recommended hardening landed; all four enabled specialists return clean; 27 tests green; lint/format clean.

- [DOC] Round-1 blocker (stale `build_agent_sdk_options` docstring) — **RESOLVED.** comment-analyzer confirms lines 257-265 now accurately state the builder only *auto*-disables for `output_format` calls and that `complete_with_tools` (narrator + narrator-aside) passes `thinking={"type":"disabled"}` explicitly; the kwarg is called out as load-bearing (anti-revert). Verified directly against lines 262-263 (gate) and the call site.
- [DOC] Round-1 blocker (off-by-one test docstring line ref) — **RESOLVED.** Now `aside_resolver.py:302`, matching the actual `caller="aside"` line (both occurrences).
- [TEST] Recommended hardening — **LANDED.** `test_narrator_uses_sdk_client.py:170` now asserts `fake.last_options.thinking == {"type":"disabled"}` end-to-end through the orchestrator. test-analyzer confirms it is non-vacuous (fails on revert) and rides a non-None `tool_dispatch`, closing the prior MCP-present-path coverage gap.
- [RULE] rule-checker clean: 9 rules / 18 instances, 0 violations (No Silent Fallbacks, No Stubbing, Don't Reinvent, wiring, No Source-Text Wiring Tests, OTEL behaviour-restore exception all compliant).
- [SEC] No security surface touched — `thinking` is an internal SDK option; subscription-auth assert unchanged. (Subagent disabled; assessed directly — no change since round 1.)
- [EDGE] Disabled — assessed directly: rework is docs + one runtime assertion; no new branches or boundaries.
- [SILENT] Disabled — assessed directly: no swallowed errors / silent fallbacks introduced.
- [TYPE] Disabled — assessed directly: no type/signature change in the rework.
- [SIMPLE] Disabled — assessed directly: minimal, no over-engineering; the added assertion is one line.

**Data flow traced (unchanged, re-confirmed):** player action → orchestrator narration turn → `complete_with_tools` → `build_agent_sdk_options(..., thinking={"type":"disabled"})` → `ClaudeAgentOptions` → `query(prompt, options)` → agent-sdk loop with no per-iteration adaptive thinking pass → `ToolingResult`. The end-to-end wiring test now asserts thinking-off on the options reaching the transport seam.

**Tenant isolation:** N/A — single-tenant personal project.

### Reviewer (audit) — re-review
- TEA deviation (behaviour assertion vs call-spy) → ✓ ACCEPTED (re-confirmed; rule-checker clean).
- Dev "No deviations from spec" (impl + rework) → ✓ ACCEPTED (re-confirmed; the rework was exactly the requested doc/test fixes, no scope creep).
- No undocumented deviations.

**Handoff:** To SM (Camina Drummer) for finish-story. NOTE for finish: AC #4 (live before/after re-measure) is an owed post-merge operational step (see Delivery Findings → Dev / Reviewer) — recommend running it once develop carries the fix.