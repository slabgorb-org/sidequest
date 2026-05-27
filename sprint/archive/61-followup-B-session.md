---
story_id: "61-followup-B"
jira_key: null
epic: "61"
workflow: "tdd"
---
# Story 61-followup-B: Promote narrator.sdk.usage log line to a watcher INFO event for continuous cost-trend on GM panel

## Story Details
- **ID:** 61-followup-B
- **Jira Key:** (pending)
- **Epic:** 61 — Bounded Narrator Prompt: Slim Snapshot + Wire RAG
- **Workflow:** tdd
- **Stack Parent:** none

## Story Summary

Promote the `narrator.sdk.usage` cost_usd log line (currently emitted at INFO level only) to a watcher event. The GM panel cannot display a per-turn cost trend without a stable watcher event. The new event carries:
- `input_tokens`
- `output_tokens`
- `cost_usd`
- `model`
- `cache_read_tokens`
- `cache_write_tokens`
- `severity=info`

The 61-4 alarm (which fires at warn/error) uses the rolling baseline that this continuous signal implicitly provides. This is a Keith/dev observability concern (OTEL-side, per CLAUDE.md), not a player-facing feature.

## Acceptance Criteria

- [ ] `narrator.sdk.usage` log line is promoted to a watcher event with `severity=info`
- [ ] Event payload includes: input_tokens, output_tokens, cost_usd, model, cache_read_tokens, cache_write_tokens
- [ ] The event fires once per narrator turn after the SDK call completes
- [ ] Watcher event is wired into the telemetry system and GM panel can consume it
- [ ] Regression test: construct a simple narration turn and assert the watcher event is emitted with correct payload
- [ ] OTEL span includes the cost fields as attributes for dashboard filtering

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-05-27T10:29:11Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-27 | 2026-05-27T09:54:09Z | 9h 54m |
| red | 2026-05-27T09:54:09Z | 2026-05-27T10:09:48Z | 15m 39s |
| green | 2026-05-27T10:09:48Z | 2026-05-27T10:12:00Z | 2m 12s |
| spec-check | 2026-05-27T10:12:00Z | 2026-05-27T10:13:00Z | 1m |
| verify | 2026-05-27T10:13:00Z | 2026-05-27T10:23:46Z | 10m 46s |
| review | 2026-05-27T10:23:46Z | 2026-05-27T10:28:34Z | 4m 48s |
| spec-reconcile | 2026-05-27T10:28:34Z | 2026-05-27T10:29:11Z | 37s |
| finish | 2026-05-27T10:29:11Z | - | - |

## Sm Assessment

Scoped 2-point, single-repo (server) observability story with no dependencies and no Jira key. The work is a promotion, not a new build: an existing `narrator.sdk.usage` INFO log line already carries the cost data — the task is to surface it as a stable watcher event so the GM panel gets a continuous per-turn cost trend, and so the 61-4 warn/error alarm has an explicit baseline to compare against.

Routing notes for TEA (RED):
- This is wiring-verification territory. The log line exists today; the test must prove the *watcher event* fires (not just that a log was written) and that it carries all six fields + severity=info. Include a wiring test that the event reaches the telemetry/watcher path, per CLAUDE.md's "every test suite needs a wiring test."
- Per the OTEL Observability Principle, the OTEL span should carry the cost fields as attributes for dashboard filtering (AC included).
- Framing guard (CLAUDE.md): this is a Keith/dev observability concern, OTEL-side. Do NOT frame it as a Sebastien player-facing feature.

No blockers. Phased TDD — handing to TEA for the failing test.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Behavior change — a new always-fire watcher event with a six-field payload contract.

**Test Files:**
- `sidequest-server/tests/agents/test_61_followup_B_sdk_usage_watcher_event.py` — 6 tests covering ACs 1–6.

**Tests Written:** 6 tests covering all 6 ACs.
**Status:** RED (5 failing as designed, 1 passing regression guard — ready for Dev)

**Per-test RED result** (verified via testing-runner, RUN_ID 61-followup-B-tea-red — no collection/import errors):

| Test | AC(s) | Status | Note |
|------|-------|--------|------|
| `test_sdk_usage_event_reaches_watcher_transport_as_info` | 1, 4 (wiring) | FAIL (got 0 events) | mandatory wiring test |
| `test_sdk_usage_event_payload_carries_all_six_fields` | 2 | FAIL (no event) | enforces `cost_usd` name + float |
| `test_sdk_usage_event_includes_zero_cache_fields` | 2 (edge) | FAIL (no event) | cache-cold → 0s present |
| `test_sdk_usage_event_fires_once_per_tool_iteration` | 3 | FAIL (no event) | per-call cadence |
| `test_simple_turn_emits_usage_event_with_matching_payload` | 5 | FAIL (no event) | payload correctness |
| `test_llm_request_span_carries_cost_fields_for_filtering` | 6 | **PASS** | regression guard (span already carries fields) |

### Rule Coverage (server CLAUDE.md, not lang-review/*.md)

| Rule | Test(s) | Status |
|------|---------|--------|
| No Source-Text Wiring Tests | all 6 drive real `complete_with_tools` + capture at `watcher_hub` boundary | enforced |
| Every Test Suite Needs a Wiring Test | `test_sdk_usage_event_reaches_watcher_transport_as_info` (hub-boundary capture) | failing (RED) |
| OTEL Observability Principle | AC-6 span test + AC-1 watcher-event test | mixed (guard passes, event fails) |
| Field-name contract (`cost_usd` not `cost`) | `..._payload_carries_all_six_fields` asserts `"cost" not in fields` | failing (RED) |

**Rules checked:** 4 of 4 applicable server-CLAUDE.md test rules have coverage. (No `lang-review/python.md` checklist present in `.pennyfarthing/gates/lang-review/`.)
**Self-check:** 0 vacuous tests — every test asserts concrete event counts, field presence, exact token values, and computed cost.

**Key RED signal for Dev:** the only watcher event firing at the emit site today is `session.cost_running_total` (followup-D's per-*turn* pulse). The new event is the per-*call* baseline — emit it next to the existing `narrator.sdk.usage` log line (~`anthropic_sdk_client.py:396`), mirroring the 60-7 `both_writes_fired` shape: keep the log line, add `_watcher_publish_event("narrator.sdk.usage", {…six fields…}, component="narrator.sdk", severity="info")`.

**Handoff:** To Dev (Major Winchester) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/sidequest/agents/anthropic_sdk_client.py` — added a `_watcher_publish_event("narrator.sdk.usage", {…6 fields…}, component="narrator.sdk", severity="info")` immediately after the existing `narrator.sdk.usage` log line (~L407). The log line is retained. 23 lines added (comment + emit).
- `sidequest-server/tests/agents/test_61_followup_B_sdk_usage_watcher_event.py` — `ruff format` whitespace/line-wrap only (no behavior change).

**Approach:** Minimal and additive. Mirrored the 60-7 `narrator.cache.both_writes_fired` emit shape exactly (same `_watcher_publish_event` helper already imported at L24, same `component="narrator.sdk"` grouping), differing only in event type, the six-field payload, and `severity="info"`. Mapped the local `cost` → contract key `cost_usd`, `response.model` → `model`, `cache_read`/`cache_write` → `cache_read_tokens`/`cache_write_tokens`. No change to the OTEL span (AC-6 already satisfied — TEA's finding confirmed; the `llm.request` span already carries `llm.model`/`llm.cost_usd`/token attrs).

**Tests:** 6/6 story tests passing (GREEN). Regression sweep: 60/60 sibling cost-telemetry tests still green (`test_61_4_cost_runaway_alarm`, `test_61_followup_D_session_cost_ceiling`, `test_anthropic_sdk_client`, `test_cache_ttl_prefix_and_otel`). Total 66/66. `ruff check` clean.
**Branch:** `feat/61-followup-B-promote-sdk-usage-watcher-event` (pushed to origin).

**AC coverage:** AC-1 (info event ✓), AC-2 (six fields + `cost_usd` name + float ✓), AC-3 (per-call cadence ✓), AC-4 (reaches watcher transport ✓), AC-5 (payload regression ✓), AC-6 (span attrs — pre-existing, guarded ✓).

**Handoff:** To Architect (Major Houlihan) for spec-check.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None

Reviewed the diff in `anthropic_sdk_client.py` against all six ACs and the story context. The implementation is minimal, additive, and reuses the existing `_watcher_publish_event` transport — exactly the reuse-first approach the design called for (no new infrastructure).

Substantive checks beyond the structural gate:
- **AC-3 cadence (per-call vs per-turn):** TEA's logged deviation is sound and I confirm it. The emit sits inside the tool-loop, so it fires per SDK call. This mirrors the log line being "promoted" (also per-call) and complements — does not duplicate — followup-D's per-turn `session.cost_running_total`. The literal "per turn" AC wording is satisfied for the common single-call turn. No further action.
- **Unconditional emit (no `session_id` guard):** Verified intentional and correct. The 61-4 alarm and followup-D ceiling are session-keyed because they maintain per-session rolling state; this event is a stateless per-call ledger and must fire on every call, matching the log line it promotes and the sibling 60-7 `both_writes_fired` event. Not a mismatch.
- **Emit ordering:** Fires after `compute_cost_usd` and before the followup-D ceiling check that may raise. Correct — the call already billed; reporting its cost before a subsequent refusal is consistent with followup-D's own "cannot un-bill the call that just landed" invariant.
- **AC-6:** No span change, as TEA predicted — the `llm.request` span already carries `llm.model`/`llm.cost_usd`/token attrs. The watcher field `cost_usd` vs span attr `llm.cost_usd` divergence is intentional (contract namespace vs OTEL namespace).

**Decision:** Proceed to review (TEA verify next).

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed for the story change; 24 PRE-EXISTING unrelated failures present in the broader suite (evidence below).

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 2 (`anthropic_sdk_client.py` diff + new test file)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 2 findings | (medium) SDK fake classes redefined across ~13 `tests/agents/` files — extraction candidate for a shared fakes module; (low) `_usage_events()` helper not applied to sibling tests |
| simplify-quality | clean | follows conventions, correct field names, proper fixture wiring |
| simplify-efficiency | clean | additive, no over-engineering, minimal fakes |

**Applied:** 0 high-confidence fixes (none were high-confidence).
**Flagged for Review:** 1 medium (shared SDK-fakes extraction) — pre-existing suite-wide pattern across 13 files; out of scope for a 2-pt additive story and would need its own refactor story.
**Noted:** 1 low (helper consistency) — not applied.
**Reverted:** 0.

**Overall:** simplify: clean (no fixes applied; 2 pre-existing-pattern observations flagged, not actioned)

### Quality-Pass / Regression Evidence

- **Story files:** `ruff check` clean, `ruff format --check` clean, 6/6 story tests green on a clean tree.
- **Full server suite:** 8201 passed, **24 failed**, 376 skipped (clean-tree run, RUN_ID `61-followup-B-tea-verify-clean`).
- **All 24 failures are PRE-EXISTING and unrelated to this story.** Proven, not assumed:
  - Reverted `anthropic_sdk_client.py` to develop's version (my change removed) and re-ran the only failures that exercise my code path (narrator SDK client): `test_dogfight_playtest_smoke`, `test_space_opera_swn_combat_e2e::{test_firefight_resolves_on_hp_depletion_vs_content_ac, test_world_loads_clean_under_swn[aureate_span], test_world_loads_clean_under_swn[coyote_star]}`, and `test_prompt_cache_attribution_otel::test_zones_carry_cache_boundary_flag` — **all still fail with my change reverted.** Therefore not caused by the new `narrator.sdk.usage` event.
  - The remaining failures are in domains a telemetry emit cannot touch: `test_61_12_output_format_compaction` (8, narrator output-format constant), `test_materialize_armor_class` (3), `test_space_opera_loads_swn` (1), `test_audit_namegen_corpora` (4), `test_pack_validator` (1).
  - Failure clusters map to other epics: space_opera/SWN combat (ADR-033/077), dogfight (epic 59), 61-12 output-format, content validation, namegen corpora.
- **Process note:** the first verify run's testing-runner subagent invoked a MUTATING ruff (`--fix`) across 67 files before pytest, corrupting the working tree. I discarded those changes (`git checkout -- .`), confirmed the tree clean, and re-ran pytest-only on the clean tree — the 24 failures reproduce identically, so they are real and not lint artifacts.

**My change introduces ZERO new failures.**

**Handoff:** To Reviewer (Colonel Potter) for code review. Flagging the 24 pre-existing failures and the stray docs commit as non-blocking findings below.

## Delivery Findings

<!-- Append-only. Each agent writes under its own subheading. -->

### TEA (test design)
- **Question** (non-blocking): AC-3 says "fires once per narrator turn," but the log line being promoted fires per tool-use iteration, and followup-D already owns the per-turn pulse (`session.cost_running_total`). I resolved this as **per-call/per-iteration** cadence (documented in context-story-61-followup-B.md, AC-3). If Dev or Reviewer reads AC-3 literally as per-turn, the emit point and test counts change — reconcile before GREEN. Affects `sidequest-server/sidequest/agents/anthropic_sdk_client.py` (emit-site placement).
- **Improvement** (non-blocking): AC-6 is effectively already satisfied — the `llm.request` span (`telemetry/spans/llm_request.py`) seeds `llm.model` and the call site already sets `llm.cost_usd`/token attrs. Dev likely needs **no span change**; the AC-6 test stands as a regression guard. Confirm `llm.model` filterability is sufficient for the dashboard.

### TEA (test verification)
- **Gap** (non-blocking): 24 pre-existing test failures in the server suite, unrelated to this story and present on `develop` (proven by reverting the story's only production file). Clusters: `test_61_12_output_format_compaction` (8), `test_space_opera_swn_combat_e2e` (5), `test_materialize_armor_class` (3), `test_audit_namegen_corpora` (4), `test_space_opera_loads_swn` (1), `test_dogfight_playtest_smoke` (1), `test_pack_validator` (1), `test_prompt_cache_attribution_otel` (1). These belong to other epics (space_opera/SWN combat, dogfight epic 59, 61-12 output-format, content validation, namegen) and should be triaged/storied separately. Affects multiple server modules; not this story's gate. *Found by TEA during test verification.*
- **Conflict** (non-blocking): The branch `feat/61-followup-B-promote-sdk-usage-watcher-event` carries an unrelated docs commit `335e4ab` ("docs: Postgres save substrate… ADR-115") that is NOT on `origin/develop` and would ride along in the PR, touching `CLAUDE.md` and `README.md`. Reviewer/SM should decide at merge whether to keep it in this PR or split it out. *Found by TEA during test verification.*

### Dev (implementation)
- **Improvement** (non-blocking): The new `narrator.sdk.usage` event is now emitted server-side, but nothing in `sidequest-ui` renders the per-call cost trend yet. A follow-up UI story is needed to plot it on the GM panel. Affects `sidequest-ui` (GM-panel/Subsystems consumer of `event_type=narrator.sdk.usage`). *Found by Dev during implementation.*
- **Improvement** (non-blocking): Confirmed TEA's AC-6 finding — no span change was required. The `narrator.sdk.usage` watcher event payload uses the contract key `cost_usd`, while the `llm.request` span uses `llm.cost_usd`; both are intentional (watcher field-name contract vs. OTEL attribute namespace). No reconciliation needed. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (non-blocking): `/ws/watcher` WebSocket endpoint (`sidequest/server/app.py:267`) has no server-side authentication; any client reaching :8765 can subscribe to the full watcher stream (2000-event ring buffer replay). PRE-EXISTING — not introduced by this story, and the same cost/token data class already broadcasts via `both_writes_fired`, `cost_runaway_suspected`, and `session.cost_running_total`. This diff modestly widens the value of unauthorized access by adding per-call USD cost. Trust model is currently localhost/Cloudflare-Zero-Trust (per `app.py:279`) but not enforced in code for this endpoint. A future story should gate `/ws/watcher` or document the trust boundary explicitly. Affects `sidequest-server/sidequest/server/app.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `response.model` flows verbatim into the watcher payload (`anthropic_sdk_client.py`). No current attack path (model is server-selected, not user-supplied), but if model routing ever threads user input, validate `response.model` against an allowlist before broadcasting. Forward-looking only. Affects `sidequest-server/sidequest/agents/anthropic_sdk_client.py`. *Found by Reviewer during code review.*

## Design Deviations

### TEA (test design)
- **AC-3 interpreted as per-call rather than per-turn cadence**
  - Spec source: context-story-61-followup-B.md, AC-3 / session ACs
  - Spec text: "The event fires once per narrator turn after the SDK call completes"
  - Implementation: Tests assert one event per SDK call / tool-use iteration (a 2-iter turn emits 2 events); single-call turns still emit exactly one, satisfying the literal AC for the common case.
  - Rationale: The log line being promoted is per-iteration; the per-turn cumulative pulse already exists separately (followup-D `session.cost_running_total`). A per-call baseline is what the 61-4 alarm (also per-call) compares against. Per-turn would duplicate followup-D.
  - Severity: minor
  - Forward impact: If overridden to per-turn, the emit site moves out of the tool-loop and `test_sdk_usage_event_fires_once_per_tool_iteration` must be rewritten.

### Dev (implementation)
- No deviations from spec. Implemented exactly to the test contract and TEA's per-call cadence resolution; AC-6 needed no code change (span already carried the attrs).

### Reviewer (audit)
- **TEA: AC-3 per-call rather than per-turn cadence** → ✓ ACCEPTED by Reviewer: the per-turn rollup already exists as `session.cost_running_total` (followup-D); a per-call baseline is the correct, non-duplicative reading and matches the per-call log line being promoted. Single-call turns satisfy the literal AC. Sound.
- **Dev: No deviations from spec** → ✓ ACCEPTED by Reviewer: confirmed against the diff — the implementation is exactly the test contract; no undocumented divergence found.
- No undocumented deviations found during review.
## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 smells; lint+format clean; 6/6 story tests green | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | findings | 2 (1 medium pre-existing auth gap, 1 low forward-looking) | confirmed 2 (both non-blocking, downgraded with rationale), dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings (Reviewer performed rule enumeration manually — see Rule Compliance) |

**All received:** Yes (2 enabled returned; 7 disabled via `workflow.reviewer_subagents`)
**Total findings:** 2 confirmed (both non-blocking), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** Anthropic SDK `response.usage` → local `input_tokens`/`output_tokens`/`cache_read`/`cache_write` + `compute_cost_usd(...)` → `cost` → `_watcher_publish_event("narrator.sdk.usage", {6 fields}, component="narrator.sdk", severity="info")` → `watcher_hub.publish` → GM-panel `/ws/watcher` subscribers. Safe: payload is aggregate numerics + model id only; no secrets, prompt text, player-private, or spoiler content (security subagent confirmed).

**Pattern observed:** Additive sibling of the established watcher-emit idiom at `anthropic_sdk_client.py` — mirrors the 60-7 `both_writes_fired` emit (same helper, same `component="narrator.sdk"` grouping). Correct reuse, no new infrastructure.

**Error handling:** `publish_event` is fire-and-forget with documented graceful degradation (drops if no bound loop / no subscribers) — intentional transport behavior, not a silent fallback in story code. The emit cannot raise into the narrator path. The existing `logger.info` line is retained (log-tail + GM-panel parity).

### Rule Compliance (python.md lang-review, 14 checks — manual enumeration, rule_checker disabled)

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Silent exception swallowing | PASS | No try/except added |
| 2 | Mutable default arguments | PASS | Dict is a call argument, not a default |
| 3 | Type annotation gaps | PASS | Emit sits in already-annotated `complete_with_tools`; no new public surface |
| 4 | Logging coverage/correctness | PASS | `severity="info"` correct for baseline signal; no sensitive data (token counts, float cost, model id) |
| 5 | Path handling | N/A | No paths |
| 6 | Test quality | PASS | Asserts check concrete counts/values/types; real `complete_with_tools` driven; hub-boundary capture (no mock-on-wrong-target); no `assert True`/skips |
| 7 | Resource leaks | PASS | No new resources; test `bound_hub` uses `async with` on the hub lock |
| 8 | Unsafe deserialization | N/A | None |
| 9 | Async/await pitfalls | PASS | Synchronous non-blocking `publish_event` inside async method — identical to 3 sibling emits already in this path |
| 10 | Import hygiene | PASS | No new prod imports (`_watcher_publish_event` already imported L24); explicit test imports |
| 11 | Input validation at boundaries | PASS | Payload sourced from SDK response, not user input; no injection surface |
| 12 | Dependency hygiene | N/A | No dependency changes |
| 13 | Fix-introduced regressions | N/A | No fixes applied during review |
| 14 | State-cleanup ordering w/ fallible side effects | PASS | Stateless per-call emit; no one-shot queue cleared after `publish` → no double-delivery risk |

**Verdict:** all applicable checks PASS.

### Observations (5+ required)

1. [VERIFIED] Field-name contract honored — `anthropic_sdk_client.py` emit dict keys are exactly the six required (`input_tokens`, `output_tokens`, `cost_usd`, `model`, `cache_read_tokens`, `cache_write_tokens`); local `cost` correctly mapped to `cost_usd`. Complies with the locked design in context-story-61-followup-B.md AC-2.
2. [VERIFIED] Severity is `info`, not `warn`/`error` — distinguishes this baseline signal from the 61-4 alarm; correct per python.md #4 log-level classification.
3. [VERIFIED] Emit cadence is per-call (inside tool-loop) — does not duplicate followup-D's per-turn `session.cost_running_total`; matches the per-call log line it promotes.
4. [VERIFIED] Existing `narrator.sdk.usage` log line retained — additive, preserves log-tail parity for operators who grep it.
5. [SEC] (medium, non-blocking) `/ws/watcher` lacks server-side auth — PRE-EXISTING infra gap, not this story's regression; same data class already broadcasts. Downgraded to non-blocking given personal-project localhost trust model; filed as follow-up delivery finding.
6. [SEC] (low, non-blocking) `response.model` forward-looking injection concern — no current path; noted for future model-routing work.
7. [VERIFIED] simplify/quality from verify phase — quality + efficiency clean; reuse's SDK-fake-duplication finding is a pre-existing suite-wide pattern (13 files), correctly out of scope for a 2-pt story.

### Devil's Advocate

Could this innocuous 23-line emit break production? Let me argue it does. First: it fires *unconditionally* inside the tool-loop, including for `session_id=None` (non-narrator) calls — could that flood the watcher with noise or fire during a path that has no event loop bound? Examined: `publish_event` drops silently when no loop is bound and the sibling `both_writes_fired` already emits unconditionally in the same spot, so the cadence is established and bounded by actual SDK calls; a runaway tool-loop is independently capped by `max_iterations` (raises `AnthropicSdkClientError`). No flood beyond what 60-7 already produces. Second: a malicious or confused operator on the GM panel — the security scan surfaced that `/ws/watcher` is unauthenticated, so anyone reaching :8765 sees per-call USD cost. Real, but pre-existing and the same channel already leaks token/cost data; this is a personal project bound to localhost/Cloudflare ZT. Third: could `cost` be `NaN`/`inf` and poison the dashboard plot? `compute_cost_usd` multiplies token counts (ints ≥ 0) by finite pricing constants from a static table; the only path to a bad value is an unknown model id, which raises `UnknownModelError` *before* the emit — so a poisoned cost can't reach the payload; the call would fail loudly first (correct, per No-Silent-Fallbacks). Fourth: ordering — the emit precedes followup-D's ceiling check that may raise; if it raised, would we double-emit on retry? No — the emit is stateless and there's no retry-from-here; the raise propagates out of the turn. Fifth: a stressed filesystem — `publish_event` also calls `_persist_turn_telemetry`; if that throws, does it abort the narrator? That persistence path is shared by all four sibling events and predates this diff; this story introduces no new persistence behavior. Conclusion: the adversarial pass surfaces only the pre-existing, network-layer-mitigated auth gap — nothing this diff newly breaks.

**Handoff:** To SM for finish-story. Two non-blocking security findings recorded for follow-up; the unrelated docs commit `335e4ab` and the 24 pre-existing suite failures are flagged for SM/triage at merge.
### Architect (reconcile)

Reviewed all in-flight deviation entries for accuracy against the actual code and spec sources:

- **TEA — AC-3 per-call cadence:** VERIFIED ACCURATE. Spec source `sprint/context/context-story-61-followup-B.md` exists and AC-3 reads as quoted ("The event fires once per narrator turn after the SDK call completes"). The implementation does emit per tool-loop iteration (`anthropic_sdk_client.py`, inside the `for` over SDK calls), matching the entry's "Implementation" field. All 6 fields present and substantive. Forward impact correctly identifies the rewrite cost if overridden. Reviewer stamped ACCEPTED — concur.
- **Dev — No deviations:** VERIFIED ACCURATE. The diff is exactly the test contract; no undocumented divergence.

**AC deferral check:** No ACs were deferred or descoped — all six (AC-1..AC-6) are DONE and test-covered. No-op.

**Missed deviations:** No additional deviations found. The single deviation (per-call vs per-turn cadence) is the only divergence from literal spec wording, and it is well-justified, documented, and accepted. The story is a clean additive telemetry promotion with no architectural drift.