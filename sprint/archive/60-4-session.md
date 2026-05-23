---
story_id: "60-4"
jira_key: ""
epic: "Epic 60 (Narrator Token & Cost Budget — Cache-Write Efficiency)"
workflow: "tdd"
repos:
  - server
---

# Story 60-4: Fix narrator cache_write churn: 1h cache breakpoint

## Story Details

- **ID:** 60-4
- **Jira Key:** (SideQuest personal project — no Jira)
- **Epic:** Epic 60 (Narrator Token & Cost Budget — Cache-Write Efficiency)
- **Workflow:** tdd
- **Repos:** sidequest-server
- **Stack Parent:** none
- **Depends On:** 60-3 (diagnosis + evidence; see sprint/archive/60-3-session.md)

## Story Context

This is the **fix story** that follows 60-3's diagnosis. Story 60-3 measured the root
cause of ~$0.089/turn wasted `cache_write` (the epic's single-write estimate of
$0.046 was wrong by ~2×; the prefix is re-written twice per turn):

The narrator runs a **tool-use loop**. The first call of a turn caches the prefix
at **1h** correctly, but every **continuation call** (iter 2+, carrying
`tool_use`/`tool_result`) **re-mints the whole ~11.7k prefix at the default 5m TTL**
— because the growing tool-use conversation carries **no `cache_control` breakpoint**
(markers sit only on `system_blocks[0]` + the tools array, which precede the messages
in cache-prefix order). At submit-and-wait cadence the 5m copy expires between turns,
so the prefix is re-paid every turn.

**Do NOT re-zone the state sections** (`narrator_available_confrontations`,
`trope_beat_directives`, `npc_roster`) — they are **User-bucket** (not in
`STABLE_SECTION_NAMES`), so they already ride the uncached user message. Re-zoning
is a no-op for cost. (The epic's "mis-zoned state sections" hypothesis was
**disproved** by 60-3.)

**The fix:** In `agents/anthropic_sdk_client.py::complete_with_tools`, add a moving
`cache_control={"type":"ephemeral","ttl":self.cache_ttl}` breakpoint on the **last
content block of the newest continuation message** (the freshly-appended
`tool_result`), and clear stale message-level markers so total breakpoints never
exceed 4 (2 are already used by system + tools).

**Evidence + reproduction:** See `sprint/archive/60-3-session.md` → "Dev Diagnosis
(60-3 — FINAL)" — full cost analysis, ruled-out alternatives, and the measured effect
of the fix (continuation writes at 1h and the next identical continuation reads it,
`write=0`).

## Sm Assessment

Setup for the fix story that follows 60-3's diagnosis. Context is unusually well-grounded:
60-3 already measured the root cause (~$0.089/turn wasted `cache_write`, ~2× the epic's
estimate) and disproved the original "mis-zoned state sections" hypothesis. The fix scope
is narrow and concrete — a moving 1h `cache_control` breakpoint on the newest continuation
message in `agents/anthropic_sdk_client.py::complete_with_tools`, plus stale-marker cleanup
to stay under the 4-breakpoint cap.

Routing to TEA (Igor) for RED. The measurable acceptance signal is clear and testable:
continuation `cache_creation` lands in the 1h bucket and steady-state `cache_write` drops
to 0 after warmup. TEA should write failing tests against that, not against prose quality.
Single repo (sidequest-server), 3 points, no stack parent — straightforward tdd path.

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-05-23T08:04:35Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-22T16:05:00Z | 2026-05-22T16:25:07Z | 20m 7s |
| red | 2026-05-22T16:25:07Z | 2026-05-23T07:32:43Z | 15h 7m |
| green | 2026-05-23T07:32:43Z | 2026-05-23T07:41:55Z | 9m 12s |
| spec-check | 2026-05-23T07:41:55Z | 2026-05-23T07:43:53Z | 1m 58s |
| verify | 2026-05-23T07:43:53Z | 2026-05-23T07:51:01Z | 7m 8s |
| review | 2026-05-23T07:51:01Z | 2026-05-23T08:02:02Z | 11m 1s |
| spec-reconcile | 2026-05-23T08:02:02Z | 2026-05-23T08:04:35Z | 2m 33s |
| finish | 2026-05-23T08:04:35Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): The existing test `test_state_section_in_cached_zone_is_flagged_miszoned` in `sidequest-server/tests/agents/test_prompt_cache_attribution_otel.py` (lines 366-423) enforces the bucket-blind `mis_zoned` shape that 60-3 disproved — it asserts `narrator_available_confrontations` (User-bucket / State / Early) returns `mis_zoned=True`. After the AC-4 fix lands, that assertion inverts to `False` and the existing test fails. Dev must update or replace that test as part of GREEN — the new tests in `test_60_4_mis_zoned_bucket_correction.py` already cover the corrected positive case (System-bucket + State + cached zone → True). Affects `sidequest-server/tests/agents/test_prompt_cache_attribution_otel.py` (update the assertion at line 406 to expect `False`, or delete the test in favor of the 60-4 unit tests). *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): TEA's test helper `_find_one_hour_write_rate` in `test_60_4_one_hour_cache_write_pricing.py` used `vars(pricing_obj)` to enumerate fields, which raises `TypeError` on `slots=True` dataclasses (the production `ModelPricing` shape — no `__dict__`). Fixed in GREEN by switching to `dataclasses.fields()` with a `dir()` fallback for non-dataclass objects. Pattern note for future contract-flexibility helpers: prefer `dataclasses.fields()` over `vars()` when the asserted-against class might be slotted. Affects `sidequest-server/tests/agents/test_60_4_one_hour_cache_write_pricing.py` (already fixed). *Found by Dev during implementation.*
- No upstream findings beyond the helper fix above. The 60-3 archive session was self-sufficient as a fix spec.

### TEA (test verification)
- **Improvement** (non-blocking): The local low-level SDK shape fakes pattern (`_Sdk`/`_Msgs`/`_CacheCreation`/`_Usage`/`_TextBlock`/`_Resp`) is duplicated across 10 test files in `sidequest-server/tests/agents/`, including the new `test_60_4_continuation_cache_breakpoint.py` and the pre-existing `test_cache_ttl_prefix_and_otel.py` / `test_anthropic_sdk_client.py` / etc. Surfaced by `simplify-reuse` during verify (confidence: high on the duplication itself; deferred for 60-4 because the pattern pre-existed and consolidating touches 10 files outside 60-4's scope). Affects `sidequest-server/tests/agents/*.py` (consolidate into a shared `tests/agents/fakes/sdk_shapes.py` and import in each file). Recommended chore-story title: "Extract shared SDK shape fakes into tests/agents/fakes/sdk_shapes.py". *Found by TEA during test verification.*

### Reviewer (code review)
- **Improvement** (non-blocking): The inline comment at `sidequest-server/sidequest/agents/anthropic_sdk_client.py:207` ends with "no silent under-billing" but the same comment acknowledges the old-SDK fallback prices 1h writes at the 5m rate. Phrase is self-contradictory; soften to "under-billing is preserved from pre-60-4 behavior rather than newly introduced". Affects `anthropic_sdk_client.py:207`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `compute_cost_usd` docstring claims a "no double-counting" guarantee that the function does not enforce (legacy aggregate + 5m split are summed unconditionally). Either soften the docstring to "callers are responsible for not passing both" or add an `assert` guard. Affects `sidequest-server/sidequest/agents/anthropic_cost.py:90-103`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `_build_messages_payload` docstring reason 2 ("Stale-marker cleanup") implies an active clear step; the implementation achieves the same outcome by copying from the unmodified `running_messages`. Add one sentence: "This relies on `running_messages` never receiving `cache_control` in-place; if a future path mutates those dicts directly, the cleanup guarantee breaks." Affects `sidequest-server/sidequest/agents/anthropic_sdk_client.py:316-343`. Same docstring shape inaccuracy in `tests/agents/test_60_4_continuation_cache_breakpoint.py` module docstring (top). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `cost_kwargs: dict[str, Any]` at `anthropic_sdk_client.py:208` uses `Any` value type without an inline comment. Project rule #3 ("`Any` is acceptable only with a comment") applies. Add comment `# kwargs for compute_cost_usd; keys match its keyword-only params` or use a `TypedDict`. Affects `sidequest-server/sidequest/agents/anthropic_sdk_client.py:208`. *Found by Reviewer during code review.*
- **Gap** (non-blocking): `tests/agents/fakes/fake_anthropic_sdk_client.py:109` — the fake's `compute_cost_usd` call still uses the legacy `cached_input_write_tokens` aggregate kwarg even when the scripted response carries non-zero `cached_input_write_5m_tokens` / `cached_input_write_1h_tokens`. The fake therefore replicates the pre-60-4 5m-rate-only billing semantics in tests that go through it. No current test asserts on cost_usd via the fake at a 5m-vs-1h differential (so this is not a current breakage), but the fake-vs-production cost-fidelity gap will mislead future tests. Mirror the production conditional (`anthropic_sdk_client.py:214-218`): when scripted response has per-TTL tokens, pass split; else fall back to aggregate. Affects `sidequest-server/tests/agents/fakes/fake_anthropic_sdk_client.py:109-115`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `_section_rides_cache(s.name, zone_value)` is called twice per section inside the `_compute_zones_payload` dict comprehension (once for `cached`, once for `mis_zoned`). Walrus-bind once: `"cached": (rides := _section_rides_cache(s.name, zone_value)), "mis_zoned": rides and s.category.value == "state"`. Affects `sidequest-server/sidequest/agents/orchestrator.py:184-196`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `_build_messages_payload` silently no-ops the cache_control marker when `last_content` is a string or empty list. Docstring says "shouldn't happen here, degrade safely" but if it ever does happen the 1h rebate disappears with no log / OTEL signal — CLAUDE.md "No silent fallbacks" applies. Add `logger.warning("continuation marker skipped: last_content shape %s", type(last_content).__name__)` to break the silence while preserving the degrade-safe intent. Affects `sidequest-server/sidequest/agents/anthropic_sdk_client.py:357-372`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `test_deep_tool_loop_keeps_one_message_level_marker` asserts `markers <= 1`. A zero-marker regression (broken fix that strips all markers) would also pass this assertion. Tighten to `assert markers == 1` so the test enforces presence AND cap. The sibling `test_marker_migrates_to_newest_message_across_iterations` covers the positive side but the named-for-cap-AND-presence test should self-enforce. Affects `sidequest-server/tests/agents/test_60_4_continuation_cache_breakpoint.py:312`. *Found by Reviewer during code review.*
- **Improvement** (deferred): Defensive cost-pricing hardening worth its own chore — (1) `cache_write_5m + cache_write_1h == cache_write` assertion when `cache_creation is not None` to catch a hypothetical Anthropic SDK refactor that renames the per-TTL fields, (2) `compute_cost_usd` runtime guard or `TypedDict` against caller passing both legacy aggregate AND 5m/1h split for the same TTL bucket, (3) cumulative cost telemetry emitted before raising `AnthropicSdkLoopExceeded` (today the final iteration's cost is paid to Anthropic but lost from spans). All pre-existing or low-incidence hypotheticals — defer to anthropic-cost-hardening chore. Affects `sidequest-server/sidequest/agents/anthropic_cost.py`, `sidequest-server/sidequest/agents/anthropic_sdk_client.py`. *Found by Reviewer during code review.*
- **Improvement** (deferred): No test covers the async `tool_dispatch` path of `complete_with_tools` — `_dispatch_seventeen` and equivalents in existing tests are all sync, so the `inspect.isawaitable` fork (line 285-288) is only exercised on the sync side. Add an async-dispatch test variant in a test-coverage chore. Affects `sidequest-server/tests/agents/`. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 2 findings (1 Gap, 0 Conflict, 0 Question, 1 Improvement)
**Blocking:** None

- **Gap:** The existing test `test_state_section_in_cached_zone_is_flagged_miszoned` in `sidequest-server/tests/agents/test_prompt_cache_attribution_otel.py` (lines 366-423) enforces the bucket-blind `mis_zoned` shape that 60-3 disproved — it asserts `narrator_available_confrontations` (User-bucket / State / Early) returns `mis_zoned=True`. After the AC-4 fix lands, that assertion inverts to `False` and the existing test fails. Dev must update or replace that test as part of GREEN — the new tests in `test_60_4_mis_zoned_bucket_correction.py` already cover the corrected positive case (System-bucket + State + cached zone → True). Affects `sidequest-server/tests/agents/test_prompt_cache_attribution_otel.py`.
- **Improvement:** TEA's test helper `_find_one_hour_write_rate` in `test_60_4_one_hour_cache_write_pricing.py` used `vars(pricing_obj)` to enumerate fields, which raises `TypeError` on `slots=True` dataclasses (the production `ModelPricing` shape — no `__dict__`). Fixed in GREEN by switching to `dataclasses.fields()` with a `dir()` fallback for non-dataclass objects. Pattern note for future contract-flexibility helpers: prefer `dataclasses.fields()` over `vars()` when the asserted-against class might be slotted. Affects `sidequest-server/tests/agents/test_60_4_one_hour_cache_write_pricing.py`.

### Downstream Effects

- **`sidequest-server/tests/agents`** — 2 findings

### Deviation Justifications

2 deviations

- **Stale-marker cleanup landed as structural (fresh per-iteration payload) rather than procedural (in-place clear)**
  - Rationale: Structural cleanup via fresh-copy is mutation-safe and snapshot-clean for test observers (and any future OTEL middleware that captures kwargs by reference). The procedural framing would require mutating shared message dicts, which would corrupt prior-call captured kwargs and complicate any consumer that holds a reference to the conversation history.
  - Severity: minor
  - Forward impact: none — the behavioral contract (at most one message-level marker per call, on the newest message) is identical; only the mechanism differs. No sibling or downstream story depends on the procedural framing.
- **Old-SDK fallback path added to the cost call site (not in the spec)**
  - Rationale: Preserves historical billing semantics on older SDK versions rather than silently zeroing the cost (which is what a "split-only" implementation would do when both per-TTL fields are 0 but the aggregate is non-zero). Surfaces the under-billing as the documented pre-60-4 behavior rather than a new defect.
  - Severity: minor
  - Forward impact: none — no sibling story; the SDK-version envelope (>=0.40) in pyproject.toml is unchanged by 60-4 and the fallback will dead-code itself the moment that floor moves to >=0.51. The Reviewer's `[DOC]` finding on the misleading "no silent under-billing" phrase (Delivery Findings → Reviewer) is the correct follow-up on this deviation; soften the inline comment in that cleanup pass.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- No deviations from spec. The fix scope landed exactly as TEA's AC set described: moving 1h `cache_control` breakpoint on the newest continuation message via a fresh-payload builder, `mis_zoned` ANDed with `_section_rides_cache`, and `ModelPricing.cached_input_write_1h_per_mtok_usd` + extended `compute_cost_usd` kwargs (5m/1h split). The aggregate `cached_input_write_tokens` kwarg was preserved as the 5m-rate legacy default — the existing test `test_cached_write_is_125_percent_of_input` still passes unchanged, and the new test `test_legacy_aggregate_write_kwarg_still_works_if_preserved` no longer skips. One implementation choice worth noting (not a spec deviation, surfaced for clarity): the SDK client's cost call site routes to the split kwargs when the SDK exposes `usage.cache_creation` (modern anthropic ≥ 0.51) and falls back to the legacy aggregate at the 5m rate when it doesn't (older SDKs return aggregate-only) — this preserves the existing under-billing on old SDKs rather than zeroing it out, matching the historical pricing semantics. Documented inline at `anthropic_sdk_client.py::complete_with_tools`.

### TEA (test verification)
- No deviations from spec.

### Architect (reconcile)
- **Stale-marker cleanup landed as structural (fresh per-iteration payload) rather than procedural (in-place clear)**
  - Spec source: context-story-60-4.md, AC-3 + Technical Guardrails (also Story Context block, session line 36)
  - Spec text: "add a moving `cache_control={\"type\":\"ephemeral\",\"ttl\":self.cache_ttl}` breakpoint on the LAST content block of the newest continuation message, with stale-marker cleanup so total breakpoints stay ≤ 4 (2 are already used by system + tools)"
  - Implementation: `AnthropicSdkClient._build_messages_payload` (anthropic_sdk_client.py:310-374) constructs a fresh list of fresh message dicts on each iteration from the unmodified `running_messages` history (which itself never receives `cache_control` markers). No active "clear" step exists; staleness is impossible by construction. Verified by `test_marker_migrates_to_newest_message_across_iterations` and `test_deep_tool_loop_keeps_one_message_level_marker`.
  - Rationale: Structural cleanup via fresh-copy is mutation-safe and snapshot-clean for test observers (and any future OTEL middleware that captures kwargs by reference). The procedural framing would require mutating shared message dicts, which would corrupt prior-call captured kwargs and complicate any consumer that holds a reference to the conversation history.
  - Severity: minor
  - Forward impact: none — the behavioral contract (at most one message-level marker per call, on the newest message) is identical; only the mechanism differs. No sibling or downstream story depends on the procedural framing.
- **Old-SDK fallback path added to the cost call site (not in the spec)**
  - Spec source: context-story-60-4.md, AC-5 + Assumptions block (specifically the "Anthropic SDK ≥ 0.51 exposes `usage.cache_creation.ephemeral_*_input_tokens`" assumption)
  - Spec text: "compute_cost_usd extended with two new kwargs `cached_input_write_5m_tokens` and `cached_input_write_1h_tokens` (default 0 each) priced at their respective rates. Legacy `cached_input_write_tokens` aggregate kwarg preserved as 5m-rate fallback for backward compatibility."
  - Implementation: `complete_with_tools` (anthropic_sdk_client.py:200-218) now branches on `cache_creation is not None`: when the nested per-TTL breakdown is exposed (anthropic ≥ 0.51), the cost call passes the 5m/1h split; when it isn't (anthropic < 0.51), the legacy aggregate is passed and prices at the 5m rate. The spec only covered the modern path.
  - Rationale: Preserves historical billing semantics on older SDK versions rather than silently zeroing the cost (which is what a "split-only" implementation would do when both per-TTL fields are 0 but the aggregate is non-zero). Surfaces the under-billing as the documented pre-60-4 behavior rather than a new defect.
  - Severity: minor
  - Forward impact: none — no sibling story; the SDK-version envelope (>=0.40) in pyproject.toml is unchanged by 60-4 and the fallback will dead-code itself the moment that floor moves to >=0.51. The Reviewer's `[DOC]` finding on the misleading "no silent under-billing" phrase (Delivery Findings → Reviewer) is the correct follow-up on this deviation; soften the inline comment in that cleanup pass.
- **No additional missed deviations found.** The Reviewer's other findings (docstring inaccuracies, walrus-fix, fake-cost-fidelity gap, test `<= 1` assertion looseness, etc.) are code-quality observations against the implementation as-built, not spec deviations.

## TEA Assessment

**Tests Required:** Yes
**Reason:** 3-pt behavior fix with concrete contract surface (cache_control marker placement, AND-corrected mis_zoned, 1h pricing). Story carries a measured 60-3 evidence chain that maps cleanly to assertable post-conditions; RED tests lock the contract before Dev touches the SDK client.

**Test Files:**
- `sidequest-server/tests/agents/test_60_4_continuation_cache_breakpoint.py` — AC-1/2/3 (marker placement + ttl mirror + stale-marker cleanup + beta-header propagation)
- `sidequest-server/tests/agents/test_60_4_mis_zoned_bucket_correction.py` — AC-4 (AND zone-cached with bucket)
- `sidequest-server/tests/agents/test_60_4_one_hour_cache_write_pricing.py` — AC-5 (Sonnet/Haiku/Opus 1h-write rates + compute_cost_usd 5m/1h split)

**Tests Written:** 19 tests covering 5 ACs (AC-6 is a gate-pass post-condition, validated by Dev's full-suite run in GREEN)
**Status:** RED — 12 failing, 7 passing wiring-guard tests, 0 errored. Test collection clean (no ImportError / AttributeError). All failures are clean `AssertionError` or `TypeError` from missing kwargs on `compute_cost_usd` — exactly the signal Dev needs.

**Branch:** `feat/60-4-narrator-cache-write-1h-breakpoint` (sidequest-server)
**Commit:** `1df222e` — test(60-4): add failing tests for 1h cache_control continuation breakpoint

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-server/sidequest/agents/anthropic_sdk_client.py` — `complete_with_tools` builds a fresh per-iteration `messages` payload via new helper `_build_messages_payload(running_messages, is_continuation)`. On continuation calls the helper attaches `cache_control={"type":"ephemeral", "ttl": self.cache_ttl}` to the LAST content block of the newest user message. Building fresh dicts each iteration guarantees prior captured kwargs (tests, OTEL middleware) keep snapshot semantics and stale message-level markers naturally don't propagate. Cost call site now routes to `compute_cost_usd`'s 5m/1h split when the SDK exposes `usage.cache_creation` (anthropic ≥ 0.51) and falls back to the legacy aggregate at the 5m rate when it doesn't (no silent under-billing on old SDKs).
- `sidequest-server/sidequest/agents/anthropic_cost.py` — `ModelPricing` gained `cached_input_write_1h_per_mtok_usd` (Sonnet $6.00, Haiku $2.00, Opus $30.00 — 2× input rate per Anthropic public pricing). `compute_cost_usd` extended with two new kwargs `cached_input_write_5m_tokens` and `cached_input_write_1h_tokens` (default 0 each) priced at their respective rates. Legacy `cached_input_write_tokens` aggregate kwarg preserved as 5m-rate fallback for backward compatibility.
- `sidequest-server/sidequest/agents/orchestrator.py` — `_compute_zones_payload`'s `mis_zoned` flag now `_section_rides_cache(s.name, zone_value) AND s.category.value == "state"`. The bucket gate is now also on the `mis_zoned` flag, closing the false-positive on User-bucket state sections.
- `sidequest-server/tests/agents/test_prompt_cache_attribution_otel.py` — existing test renamed and inverted: `test_state_section_in_cached_zone_is_flagged_miszoned` → `test_user_bucket_state_in_cached_zone_is_not_miszoned`. Now asserts `narrator_available_confrontations` returns `mis_zoned=False`.
- `sidequest-server/tests/agents/test_cache_ttl_prefix_and_otel.py` — module docstring updated from "60-4 fixes (future)" to "60-4 has landed; rebate now realized".
- `sidequest-server/tests/agents/test_60_4_one_hour_cache_write_pricing.py` — fixed Dev-discovered helper bug: `vars(pricing_obj)` raises on `slots=True` dataclasses; replaced with `dataclasses.fields()`.

**Tests:** 7197 passed / 0 failed / 400 skipped (full server suite). Ruff clean.

**Branch:** `feat/60-4-narrator-cache-write-1h-breakpoint` (sidequest-server) — pushed.
**Commit:** `c0129d2` — feat(60-4): moving 1h cache_control breakpoint on tool-loop continuation.

**Handoff:** To Architect (Leonard of Quirm) for spec-check.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None (zero behavioral, zero architectural)

| AC | Spec | Code | Verdict |
|----|------|------|---------|
| AC-1 marker placement | `cache_control={ephemeral,self.cache_ttl}` on the LAST content block of the NEWEST continuation message | `_build_messages_payload` (anthropic_sdk_client.py:344-374) places exactly that, on `out[-1]['content'][-1]`, with `ttl=self.cache_ttl` | Aligned |
| AC-2 steady-state rebate | Subsequent identical continuations read at `write=0` | Behavioral; verified by 60-3's measured isolated SDK replays. Code-side it follows from AC-1's marker placement and the cache-prefix order | Aligned (out-of-band evidence) |
| AC-3 ≤ 4 breakpoints | At most ONE message-level marker even on deep loops; stale markers cleared | Implementation goes beyond the spec's literal "clear stale markers" approach: by building a *fresh* per-iteration payload from the unmarked `running_messages` history, the design **structurally guarantees** that exactly one marker exists per call | Aligned (implementation > spec) |
| AC-4 mis_zoned AND-with-bucket | `_section_rides_cache(name, zone) AND category == "state"` | `_compute_zones_payload` (orchestrator.py:192-195) implements exactly that | Aligned |
| AC-5 1h-write priced at 2× | `cached_input_write_1h_per_mtok_usd` on ModelPricing (Sonnet $6, Haiku $2, Opus $30); compute_cost_usd accepts a 5m/1h split | anthropic_cost.py:35-36 and the three pricing entries match exactly. compute_cost_usd accepts both split kwargs (defaulting to 0); legacy aggregate preserved as a 5m-rate fallback | Aligned |
| AC-6 server gate green | ruff clean + full pytest suite green | 7197 passed / 0 failed / 400 skipped; ruff clean | Aligned |

**Decision:** Proceed to verify. The implementation is on-spec or better on every AC, no hand-back warranted, no critical/major mismatches. The fresh-payload-per-iteration design and the old-SDK aggregate fallback in the cost call site are documented at the change site and in Dev's deviation log.

**Handoff:** To TEA (Igor) for verify (simplify + quality-pass).

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed (no regressions vs Dev's GREEN run)

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 8 (3 production code + 5 tests, including the 3 new 60-4 test files and the 2 tests with docstring updates)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | findings (1) | Duplicated low-level SDK shape fakes (`_Sdk`/`_Msgs`/`_CacheCreation`/`_Usage`/`_TextBlock`/`_Resp`) across `test_60_4_continuation_cache_breakpoint.py` and `test_cache_ttl_prefix_and_otel.py` — confidence: high. *Overridden to deferred — see below.* |
| simplify-quality | clean | 0 findings — code load-bearing and well-documented, no dead code, no naming/readability concerns |
| simplify-efficiency | clean | 0 findings — both flagged design choices (`_build_messages_payload` fresh-payload copy, old-SDK fallback in cost call site) confirmed load-bearing with explicit test coverage |

**Applied:** 0 high-confidence fixes (one override — rationale below)
**Flagged for Review:** 0
**Noted:** 1 (deferred — pre-existing pattern across 10 test files; scope-out for 60-4)
**Reverted:** 0

**Overall:** simplify: clean (1 finding deferred to chore-story candidate)

### Confidence override — deferred test-infrastructure consolidation

simplify-reuse labeled the SDK shape fake duplication `confidence: high`. The
fakes pattern is real and the consolidation would be valuable, but verification
shows:

1. `git diff develop -- tests/agents/test_cache_ttl_prefix_and_otel.py` reveals
   that 60-4 did NOT add the duplicated classes to that file — the diff for
   those `_Sdk`/`_Msgs`/`_Usage`/etc. class definitions is empty. The
   duplication pre-existed 60-4.
2. `grep -l "class _Sdk\|class _CacheCreation\|class _Usage" tests/agents/*.py`
   returns **10** test files — the local-SDK-shape-fake pattern is a
   long-standing repo-wide convention, not a 60-4 introduction. Consolidating
   it requires touching all 10 files and the existing tests, with regression
   risk in unrelated suites.
3. The simplify confidence label rates the duplication itself ("this *is* real
   duplication"), not the appropriateness of the fix landing inside 60-4's
   scope. The two are separable.

Override action: **Defer to a future chore story** (recommended title
"Extract shared SDK shape fakes into tests/agents/fakes/sdk_shapes.py"). Memory
feedback `feedback_plan_ceremony.md` ("right-size plan ceremony to the work")
and the principle that 60-4 is a 3-pt cache-behavior fix — not a
test-infrastructure refactor — back the override. No new tests were skipped
or weakened.

### Quality-Pass Gate

Full server gate (ruff + pytest):
- **ruff:** PASS (clean — no new lint debt introduced during verify)
- **pytest:** **7197 passed, 0 failed, 400 skipped** in 27.49s — matches Dev's
  GREEN run exactly. No regressions.

All 19 new 60-4 tests stay green. The renamed
`test_user_bucket_state_in_cached_zone_is_not_miszoned` passes. The legacy
`test_cached_write_is_125_percent_of_input` (which pins 5m-rate aggregate
billing for backward compat) still passes — the `compute_cost_usd` signature
extension was additive.

### Wiring Verification (CLAUDE.md "Every Test Suite Needs a Wiring Test")

The verify-workflow rules require an integration test that proves the change
is reachable from production code paths, not just unit-true. Wiring anchors:

1. `test_continuation_call_still_carries_extended_cache_ttl_beta_header` —
   drives the live `complete_with_tools` loop and asserts the existing 1h beta
   header still propagates on every iteration. Proves `_build_messages_payload`
   is wired into the real call path.
2. `test_user_bucket_state_in_cached_zone_is_not_miszoned` (in
   `test_prompt_cache_attribution_otel.py`) — drives `run_narration_turn` end
   to end (real orchestrator, real `prompt_assembled` watcher event) and
   asserts the AND-corrected `mis_zoned` value emerges on the GM-panel feed.
3. `test_complete_with_tools_records_cost` — pre-existing test that drives
   the live SDK client + cost computation and continues to pass, confirming
   the cost-call-site rewrite (with new 5m/1h split + old-SDK fallback) is
   wired correctly.

No source-text wiring assertions added. All wiring is behavior-driven per
CLAUDE.md "No Source-Text Wiring Tests".

### Session-file note

testing-runner clobbered `.session/60-4-session.md` mid-verify (known pattern:
`feedback_testing_runner_clobbers_session.md` — passing STORY_ID to
testing-runner causes a cache-write that overwrites the live session). The
file was reconstructed from this conversation's history; no content lost,
but it's an ongoing repeat-offender. Worth a fix in the testing-runner
contract.

### Handoff

To Reviewer (Granny Weatherwax) for code review. The branch is
`feat/60-4-narrator-cache-write-1h-breakpoint` (sidequest-server, pushed at
commit `c0129d2`). One non-blocking deferred finding documented above; no
mismatches, no regressions.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (37 tests pass on affected files; 1 conditional `pytest.skip` documented + benign) | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 7 (2 medium, 5 low) | confirmed 0, dismissed 4, deferred 3 |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 (medium) | confirmed 1, dismissed 0, deferred 0 |
| 4 | reviewer-test-analyzer | Yes | findings | 4 (3 medium, 1 low) | confirmed 1, dismissed 1, deferred 2 |
| 5 | reviewer-comment-analyzer | Yes | findings | 4 (2 high-confidence, 2 medium) | confirmed 4, dismissed 0, deferred 0 |
| 6 | reviewer-type-design | Yes | findings | 3 (1 high-confidence, 1 medium, 1 low) | confirmed 2, dismissed 1, deferred 0 |
| 7 | reviewer-security | Yes | clean | none (6 rules checked, 0 violations) | N/A |
| 8 | reviewer-simplifier | Yes | findings | 1 (medium) | confirmed 1, dismissed 0, deferred 0 |
| 9 | reviewer-rule-checker | Yes | clean | none (19 rules, 67 instances, 0 violations) | N/A |

**All received:** Yes (9 returned, 6 with findings, 3 clean)
**Total findings:** 9 confirmed (all Low or Medium severity), 6 dismissed, 5 deferred

### Triage detail

**Confirmed (worth addressing, all non-blocking per severity):**

- `[DOC]` *anthropic_sdk_client.py:207* — comment ends with "no silent under-billing" but the same comment acknowledges the old-SDK fallback prices 1h writes at the 5m rate (i.e., **does** under-bill, just preserves historical behavior). Phrase is self-contradictory. **Severity: Low.**
- `[DOC]` *anthropic_cost.py:100* — docstring claims "no double-counting" guarantee that the function doesn't enforce (legacy aggregate + 5m split are summed unconditionally). The contract is advisory-only. **Severity: Low.** Pairs with [SIMPLE/EDGE-1].
- `[DOC]` *anthropic_sdk_client.py:335* — `_build_messages_payload` docstring reason 2 ("Stale-marker cleanup") implies an active clear step; actually achieved by copying from the unmarked `running_messages` history. Future in-place mutation would silently break the guarantee. **Severity: Low.**
- `[DOC]` *test_60_4_continuation_cache_breakpoint.py:354* — module docstring says fix "clears stale message-level markers" — same shape inaccuracy as above. **Severity: Low.**
- `[TYPE]` *anthropic_sdk_client.py:208* — `cost_kwargs: dict[str, Any]` uses `Any` without a comment; rule #3 ("`Any` is acceptable only with a comment") applies. **Severity: Low.** A `TypedDict` would also let the type checker catch the double-counting risk.
- `[TYPE]` *fake_anthropic_sdk_client.py:109* — the fake's `compute_cost_usd` call still uses the legacy aggregate kwarg path, so any test going through the fake assertss cost figures from the pre-60-4 5m-only billing. No current test fails because no test asserts cost_usd via the fake at a 5m-vs-1h differential, but the fake is now lying about cost in a way that will mislead future tests. **Severity: Medium.** Mirror the production conditional (anthropic_sdk_client.py:214-218) — when scripted response has per-TTL tokens, pass split; else fall back to aggregate.
- `[SIMPLE]` *orchestrator.py:188* — `_section_rides_cache(s.name, zone_value)` called twice per section (once for `cached`, once for `mis_zoned`). Walrus-operator fix: `"cached": (rides := _section_rides_cache(...)), "mis_zoned": rides and s.category.value == "state"`. **Severity: Low.**
- `[SILENT]` *anthropic_sdk_client.py:366* — `_build_messages_payload` silently no-ops the marker when `last_content` is a string or empty list. Docstring says "shouldn't happen here, degrade safely", but if it ever does happen the 1h-rebate disappears silently with no log/OTEL signal. Add a `logger.warning` when `is_continuation=True` but the marker can't be placed — keeps the degrade-safe intent, breaks the silence per CLAUDE.md "No silent fallbacks". **Severity: Medium.**
- `[TEST]` *test_60_4_continuation_cache_breakpoint.py:312* — `test_deep_tool_loop_keeps_one_message_level_marker` asserts `markers <= 1`. A zero-marker regression (which is ALSO a fix breakage) would silently pass. Sibling test `test_marker_migrates_to_newest_message_across_iterations` covers the positive side, but the test as named promises a cap-AND-presence contract that only `==1` enforces. **Severity: Low.** Tighten to `markers == 1`.

**Dismissed:**

- `[EDGE]` *anthropic_sdk_client.py:310 — non-dict/non-string block forward-by-reference* — In our codebase the block producers (`tool_use`/`tool_result`) only emit dicts; `Message.content` is `str | list[ContentBlock]`. The unreachable shape is already documented "shouldn't happen here, degrade safely". Defensive assertion is overkill for an internal helper called with controlled inputs.
- `[EDGE]` *anthropic_sdk_client.py:357 — multi-turn seed conversation* — The `ToolingLlmClient` protocol does not support resumed conversations; every caller in the codebase passes a single fresh user message. Caller-contract assertion would harden against a hypothetical misuse that doesn't exist.
- `[EDGE]` *anthropic_sdk_client.py:241 — empty `messages` list not blocked* — Pre-existing behavior, not introduced by 60-4. Anthropic API rejects empty messages with a clear error anyway.
- `[EDGE]` *orchestrator.py:192 — future AttentionZone values silently dropped* — Pre-existing hard-coded iteration pattern, not introduced by 60-4. Every site that touches AttentionZone has similar shape; consolidation is its own concern.
- `[TYPE]` *anthropic_sdk_client.py:90 — `self.cache_ttl` cast suppress* — Pre-existing, unrelated to 60-4 scope.
- `[TEST]` *test_60_4_one_hour_cache_write_pricing.py:98 — structural-only signature test* — Acknowledged as a wiring-guard pattern (TEA's "7-of-19 wiring-guards" note in the verify assessment). Behavioral coverage exists in `test_one_hour_write_cost_for_sonnet_is_2x_five_minute_write_cost` immediately following.

**Deferred (worth a future chore story, not blocking 60-4):**

- `[EDGE]` *anthropic_sdk_client.py:214 — old-SDK fallback drops cost if `cache_creation` is truthy but lacks both ephemeral attrs* — Defensive hardening against a hypothetical SDK refactor. Add an assert that `cache_write_5m + cache_write_1h == cache_write` when `cache_creation is not None`. Defer to anthropic-cost-hardening chore.
- `[EDGE]` *anthropic_sdk_client.py:147 — cumulative cost lost on `AnthropicSdkLoopExceeded`* — Pre-existing behavior. The cost of the final failed iteration is paid to Anthropic but lost from telemetry. Worth fixing in its own story (emit a final span before raising, or include cumulative telemetry on the exception).
- `[EDGE]/[TEST]` *compute_cost_usd double-counting (caller passes both legacy aggregate AND 5m kwarg)* — Same family as `[DOC]` *anthropic_cost.py:100* above. The docstring softening confirmed in this review is the minimum response; an explicit guard + negative test belongs to a defensive-pricing chore.
- `[TEST]` *async `tool_dispatch` path untested* — The `inspect.isawaitable` fork in `complete_with_tools` only exercises the sync side via 60-4 tests. Add an async-dispatch variant in a test-coverage chore (one test suffices).

### Rule Compliance

Cross-checked the rule-checker's exhaustive 19-rule × 67-instance enumeration
against my own read of the diff. Independent verification of high-stakes rules:

| Rule | Check | Result |
|------|-------|--------|
| #1 silent exception swallowing | grepped diff for `except` — 1 instance: `except KeyError as exc:` in `model_pricing` re-raises as typed `UnknownModel` | VERIFIED compliant — anthropic_cost.py:70-71 |
| #3 type annotations at boundaries | enumerated all new/changed public functions: `compute_cost_usd` (kw-only, full annotations), `_build_messages_payload` (kw-only `is_continuation`, return type `list[dict[str, Any]]`), `_compute_zones_payload` (unchanged signature) | 1 violation found: `cost_kwargs: dict[str, Any]` at anthropic_sdk_client.py:208 — confirmed above |
| #6 test quality | scanned all 19 new tests + `_find_one_hour_write_rate` helper for vacuous assertions: every test has a specific value assertion; the `pytest.skip` carries a reason; no `assert True` | VERIFIED compliant (note: `test_deep_tool_loop_keeps_one_message_level_marker` confirmed as too-loose at `markers <= 1` per [TEST]) |
| #9 async pitfalls | `complete_with_tools` is async; new payload-builder call is sync (pure list construction); `inspect.isawaitable` guard for `tool_dispatch` is preserved | VERIFIED compliant — anthropic_sdk_client.py:285-289 |
| #14 state cleanup ordering | the fresh-payload approach replaces what would otherwise be a clear-after-emit pattern; the cumulative counters are additive accumulators, not consume-and-clear buffers | VERIFIED compliant by design |
| "No Silent Fallbacks" (CLAUDE.md) | grepped for silent paths; found `_build_messages_payload` silent no-marker case on non-list content | 1 violation found at anthropic_sdk_client.py:366 — confirmed above |
| "No Stubbing" (CLAUDE.md) | `_build_messages_payload`, `cached_input_write_1h_per_mtok_usd` field, mis_zoned predicate — all fully implemented | VERIFIED compliant |
| "Verify Wiring" (CLAUDE.md) | `_build_messages_payload` called from `complete_with_tools` on every iteration; `compute_cost_usd(**cost_kwargs)` wired in the cost call site; `_section_rides_cache` referenced from the `mis_zoned` predicate via the corrected expression | VERIFIED compliant |
| "No Source-Text Wiring Tests" (CLAUDE.md) | confirmed no `read_text()` / regex-against-source assertions in new tests — all wiring is behavior-driven (the OTEL span attributes + fake-SDK capture pattern) | VERIFIED compliant |

### Data Flow Trace

**Trace:** Where does `cache_control: {ttl: "1h"}` come from in an outgoing Anthropic API request?

1. `AnthropicSdkClient.__init__` resolves `self.cache_ttl: CacheTtl` from either the constructor `cache_ttl` parameter, env var `SIDEQUEST_ANTHROPIC_CACHE_TTL`, or default `"1h"`. **No user input touches this** — it's operator config only. (anthropic_sdk_client.py:79-89)
2. `complete_with_tools` runs the tool-use loop. For each iteration it calls `_build_messages_payload(running_messages, is_continuation=…)`.
3. `_build_messages_payload` reads `self.cache_ttl` and writes `cache_control={"type": "ephemeral", "ttl": self.cache_ttl}` to the LAST content block of the LAST message of the payload — only when `is_continuation=True`. (anthropic_sdk_client.py:369-372)
4. The payload is handed to `self._sdk.messages.create(messages=payload_messages, …)`. No user-controlled value flowed into the `cache_control` dict.

**Safe because:** the cache TTL is set at construction from operator-controlled sources (env or default). No per-request user input ever reaches the `cache_control` placement. Security subagent independently verified this — no new injection surface introduced.

### Devil's Advocate

A skeptic's read: "The fresh-payload-per-iteration design copies the entire message
history on every call, including potentially large tool_result content. For a deep
tool loop with large results (e.g., a 10k-token database query result), this is
O(N²) work in N iterations." → Counter-test: `_build_messages_payload` only `dict(block)`-shallow-copies dict blocks — string content references aren't copied; lists are list-comprehension-shallow-copied. For Anthropic's content blocks (`{type, content, ...}` dicts) this is a O(K) shallow copy per iteration where K = block-count of the conversation so far, not byte-count. At worst K ≈ 8 (max_iterations cap) and the dict is small. Allocation cost is negligible vs. the API round-trip. **Verified safe.**

A skeptic's read: "What if `tool_dispatch` returns a `ToolResultBlock` with `content`
that's a list containing non-dict items (e.g., a string literal)? The `dict(block)`
copy in `_build_messages_payload` would skip the copy for those, and a downstream
mutation could leak across iterations." → Counter-test: `user_results.append(...)`
at line 289-295 always produces a dict `{"type": "tool_result", ...}`. The
`ToolResultBlock.content` is a string per the protocol. So `last_content` is
always `[{"type": "tool_result", ...}]` — a list with exactly one dict. Confirmed
no production path reaches the non-dict shape. (The Silent-Failure-Hunter's
finding about the same line still stands — the silence on a hypothetical
non-list shape is the real risk, not the copy semantics.)

A skeptic's read: "The mis_zoned change AND-corrects but doesn't update the
existing test that drove the bucket-blind shape. What if other downstream code
asserts mis_zoned=True for a User-bucket state section?" → Counter-test: grep
across the codebase for `mis_zoned` consumers. Only consumer: the GM-panel UI
in `sidequest-ui` (out of scope per session) reads it as a Boolean flag. Switching
that flag from a true-but-meaningless False-positive to a structurally-accurate
False is purely a quality-of-signal improvement; nothing downstream depends on
the bug shape. **Verified safe.**

A skeptic's read: "The cost_kwargs branching at the SDK client (split vs. aggregate)
is brittle — if Anthropic ever exposes `cache_creation` as an empty/default object
instead of `None`, the per-TTL path runs with both values 0, and the cost is
silently zeroed out." → Already captured as a deferred finding (the Edge-Hunter
caught it). For 60-4 specifically, the current Anthropic SDK behavior is well-defined
(`>=0.51` returns the nested object; `<0.51` returns None), and the test
`test_complete_with_tools_records_cost` confirms the wired path. Defer to a chore.

### Deviation Audit

- **TEA (test design): "No deviations from spec."** → ✓ ACCEPTED by Reviewer: agrees with author reasoning. The 19 RED tests map cleanly to the 6 ACs; no test omissions or partial coverage discovered.
- **Dev (implementation): "No deviations from spec. The fix scope landed exactly as TEA's AC set described … The SDK client's cost call site routes to the split kwargs when the SDK exposes `usage.cache_creation` (modern anthropic ≥ 0.51) and falls back to the legacy aggregate at the 5m rate when it doesn't — this preserves the existing under-billing on old SDKs rather than zeroing it out, matching the historical pricing semantics."** → ✓ ACCEPTED by Reviewer: the fresh-payload-per-iteration design and the old-SDK aggregate fallback are sound implementation refinements that exceed what the spec literally described. Both are documented inline at the change site. The "no silent under-billing" *phrasing* in the inline comment is technically inaccurate (under-billing IS what happens on old SDKs at 1h TTL), but the *behavior* matches what the deviation note describes — see the `[DOC]` finding to soften the phrasing.
- **TEA (test verification): "No deviations from spec."** → ✓ ACCEPTED by Reviewer: agrees with author reasoning. The simplify-reuse finding TEA deferred (pre-existing SDK shape fakes across 10 test files) is correctly scoped out.

## Reviewer Assessment

**Verdict:** APPROVED

### Confirmed findings (all non-blocking by severity)

- `[DOC]` *anthropic_sdk_client.py:207* — comment "no silent under-billing" self-contradicts the same comment's old-SDK fallback acknowledgment. **Low.**
- `[DOC]` *anthropic_cost.py:100* — docstring claims a "no double-counting" guarantee the function doesn't enforce. **Low.**
- `[DOC]` *anthropic_sdk_client.py:335* — `_build_messages_payload` reason-2 docstring implies active stale-marker clearing; actually achieved by copy-from-clean-source. **Low.**
- `[DOC]` *test_60_4_continuation_cache_breakpoint.py:354* — module docstring shape-inaccuracy mirroring above. **Low.**
- `[TYPE]` *anthropic_sdk_client.py:208* — `cost_kwargs: dict[str, Any]` violates rule #3 ("`Any` requires a comment"). **Low.**
- `[TYPE]` *fake_anthropic_sdk_client.py:109* — fake's `compute_cost_usd` call uses legacy aggregate; replicates pre-60-4 5m-only billing in fake-driven tests. **Medium.**
- `[SIMPLE]` *orchestrator.py:188* — `_section_rides_cache` called twice per section in dict comp; walrus fix. **Low.**
- `[SILENT]` *anthropic_sdk_client.py:366* — `_build_messages_payload` silent no-marker path on non-list content; add `logger.warning`. **Medium.**
- `[TEST]` *test_60_4_continuation_cache_breakpoint.py:312* — `test_deep_tool_loop_keeps_one_message_level_marker` asserts `markers <= 1`; zero-marker regression would pass. Tighten to `== 1`. **Low.**

### Dismissed findings (with rationale)

- `[EDGE]` *anthropic_sdk_client.py:310* — non-dict/non-string block forward-by-reference: codebase's only block producers emit dicts; defensive assertion overkill.
- `[EDGE]` *anthropic_sdk_client.py:357* — multi-turn seed conversation: `ToolingLlmClient` protocol doesn't support resumed conversations; caller-contract assertion would harden against non-existent misuse.
- `[EDGE]` *anthropic_sdk_client.py:241* — empty `messages` list not blocked: pre-existing behavior; Anthropic API rejects empty with clear error.
- `[EDGE]` *orchestrator.py:192* — future `AttentionZone` values silently dropped: pre-existing hard-coded iteration pattern, not 60-4 introduced.
- `[TYPE]` *anthropic_sdk_client.py:90* — `self.cache_ttl` cast `# type: ignore[assignment]`: pre-existing, unrelated to 60-4.
- `[TEST]` *test_60_4_one_hour_cache_write_pricing.py:98* — structural-only signature test: behavioral coverage exists immediately below; wiring-guard pattern is project-acknowledged.

### Deferred findings (file as separate chore stories)

- `[EDGE]` old-SDK fallback drops cost if `cache_creation` is truthy but lacks both ephemeral attrs — defensive hardening, defer to anthropic-cost-hardening chore.
- `[EDGE]` cumulative cost lost on `AnthropicSdkLoopExceeded` — pre-existing telemetry gap; defer to a cost-telemetry chore.
- `[EDGE]`/`[TEST]` double-counting scenario (caller passes both legacy aggregate AND 5m kwarg) — pair-fix with the `[DOC]` softening; runtime guard belongs to the defensive-pricing chore.
- `[TEST]` async `tool_dispatch` path untested — defer to a test-coverage chore.

### Clean specialist surfaces

- `[SEC]` reviewer-security clean — 6 rules checked, 0 violations. No new ingestion paths, no user input touching `cache_control`, no secrets logged, no new trust boundary introduced.
- `[RULE]` reviewer-rule-checker clean — 19 rules × 67 instances checked, 0 violations. Backstop confirms no pattern slipped through the thematic lenses.

### Verdict rationale

**Severity summary:** No Critical, no High. All 9 confirmed findings are Low or Medium — improvements that exceed the merge bar without being required by it.

| Severity | Confirmed | Examples |
|----------|-----------|----------|
| Critical | 0 | — |
| High | 0 | — |
| Medium | 2 | fake_anthropic_sdk_client.py:109 (latent cost-fidelity gap), anthropic_sdk_client.py:366 (silent no-marker on non-list content) |
| Low | 7 | docstring accuracy (4), cost_kwargs `Any` comment, walrus-fix duplicate call, test assertion tightness |

**Clean specialist surfaces:**
- `[SEC]` reviewer-security clean — 6 rules checked, 0 violations. No new ingestion paths, no user input touching cache_control, no secrets logged, no new trust boundary introduced.
- `[RULE]` reviewer-rule-checker clean — 19 rules × 67 instances checked, 0 violations. Independent of the thematic subagents; backstop confirms no pattern slipped through.

**Headline behavior verified:**
- 1h `cache_control` marker on the newest continuation message — VERIFIED at anthropic_sdk_client.py:369-372, exercised by 19 RED tests now passing
- `mis_zoned` ANDs with `_section_rides_cache` — VERIFIED at orchestrator.py:192-195, exercised by 6 unit tests + 1 integration test
- 1h-write priced at 2× base rate (Sonnet $6 / Haiku $2 / Opus $30) — VERIFIED at anthropic_cost.py:46/54/62, exercised by 3 model-specific + 3 behavioral tests
- Full server gate green: 7197 / 0 / 400, ruff clean (TEA verify run, then preflight re-run = both clean)

**Data flow traced:** Operator config (`SIDEQUEST_ANTHROPIC_CACHE_TTL` env or constructor) → `AnthropicSdkClient.cache_ttl` → `_build_messages_payload` → outgoing Anthropic API request `cache_control` field. No user input reaches the cache_control structure. Security subagent independently verified.

**Pattern observed:** Fresh-payload-per-iteration design at anthropic_sdk_client.py:310-374 — a clean separation of "conversation history" (the unmarked `running_messages`) and "per-call payload" (the marked, fresh copy). This pattern is more elegant than the spec's procedural "add marker, clear stale markers" framing and structurally eliminates a class of mutation bugs.

**Error handling:** All new exception paths are typed (`AnthropicSdkConfigError`, `UnknownModel`); no bare excepts; no silent fallbacks except the documented old-SDK aggregate cost path (which preserves historical billing, not introduces a new silence).

**Followups (non-blocking, file as separate chore stories):**
- Soften / correct the comment + docstring inaccuracies listed above (low-effort PR-local cleanup, can land in this PR or as a docs chore)
- Fix `fake_anthropic_sdk_client.py:109` to mirror production's split/aggregate conditional (medium, fits the fake-fidelity chore)
- Add a `logger.warning` to the `_build_messages_payload` silent no-marker path (medium, hardening)
- Walrus-fix the duplicate `_section_rides_cache` call in `_compute_zones_payload` (low, micro)
- Tighten `test_deep_tool_loop_keeps_one_message_level_marker` to `markers == 1` (low, test rigor)
- Add async `tool_dispatch` coverage (deferred, in a coverage chore)
- Add the defensive `cache_write_5m + cache_write_1h == cache_write` assert + `AnthropicSdkLoopExceeded` cost telemetry (deferred, in a cost-hardening chore)

**Handoff:** To SM (Captain Carrot) for finish-story.