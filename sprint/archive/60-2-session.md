---
story_id: "60-2"
jira_key: ""
epic: "Epic 60 (Narrator Token & Cost Budget)"
workflow: "tdd"
repos:
  - server
  - ui
---

# Story 60-2: OTEL per-block cache attribution

## Story Details
- **ID:** 60-2
- **Jira Key:** (SideQuest personal project — no Jira)
- **Epic:** Epic 60 (Narrator Token & Cost Budget — Cache-Write Efficiency)
- **Workflow:** tdd
- **Repos:** server + ui
- **Stack Parent:** none

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-05-22T10:36:22Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-22 | 2026-05-22T09:33:08Z | 9h 33m |
| red | 2026-05-22T09:33:08Z | 2026-05-22T09:55:19Z | 22m 11s |
| green | 2026-05-22T09:55:19Z | 2026-05-22T10:17:02Z | 21m 43s |
| spec-check | 2026-05-22T10:17:02Z | 2026-05-22T10:18:44Z | 1m 42s |
| verify | 2026-05-22T10:18:44Z | 2026-05-22T10:22:49Z | 4m 5s |
| review | 2026-05-22T10:22:49Z | 2026-05-22T10:34:57Z | 12m 8s |
| spec-reconcile | 2026-05-22T10:34:57Z | 2026-05-22T10:36:22Z | 1m 25s |
| finish | 2026-05-22T10:36:22Z | - | - |

## SM Assessment

Story 60-2 builds the OTEL "eyes" for the Epic 60 cache-write bug. Per the corrected
root cause (2026-05-22), wasted cache_write is `system_blocks[0]` (Primacy+Early)
being re-written every turn because three `state`-category sections
(narrator_available_confrontations, trope_beat_directives, npc_roster) are mis-zoned
into the cached Early zone — not the game_state snapshot (which sits innocent in the
uncached Valley block).

**Scope:** server + ui. The context author explicitly flagged that the epic-default
`repos: server` is stale — the Prompt-tab display lives in `sidequest-ui`
(`PromptTab.tsx`, `types/watcher.ts`), so both repos are set up. Branches:
`feat/60-2-otel-per-block-cache-attribution` in both sidequest-server and
sidequest-ui (off develop).

**Key seam:** the event's cached/uncached partition MUST derive from the same
zone→CacheableBlock mapping the SDK path uses (`orchestrator.py:3199-3222`,
`prompt_framework/bucket.py`), not a recomputation — AC includes an accuracy-guarantee
test so the display cannot claim "stable" while the real prompt drifts. Reuse the
existing test `tests/agents/test_cache_ttl_prefix_and_otel.py`; extend the existing
`prompt_assembled` emission at `orchestrator.py:2228`. Extend, don't replace.

No Jira (SideQuest personal project). Next: TEA (Igor) writes failing tests for all
five acceptance criteria, including the server→ui end-to-end accuracy guarantee.

## TEA Assessment

**Tests Required:** Yes
**Status:** RED (failing — ready for Dev)

**Test Files:**
- `sidequest-server/tests/agents/test_prompt_cache_attribution_otel.py` — 9 tests, all failing.
- `sidequest-ui/src/components/Dashboard/__tests__/PromptTab-cache-attribution.test.tsx` — 9 tests,
  7 failing + 2 negative-case guards passing in RED by design (see deviations).

**Tests Written:** 18 tests covering all 6 ACs.

The new `prompt_assembled.fields` contract these tests pin down (Dev implements to satisfy):
```
zones: [{zone, total_tokens, cached: bool,
         sections: [{name, token_estimate, category, mis_zoned: bool}]}]
cache_blocks: [{label, digest(sha256[:8]), cached: bool}]   # label ∈ {stable,valley,recency,tools}
cache_usage: {cache_read, cache_write, cache_write_5m, cache_write_1h, cost_usd, cache_ttl} | None
```

| AC | Server test | UI test |
|----|-------------|---------|
| 1 cache boundary | `test_zones_carry_cache_boundary_flag` | `labels each zone as cached or uncached` |
| 2 real usage + n/a | `test_cache_usage_carries_real_sdk_numbers_not_estimates`, `test_cache_usage_is_explicit_na_when_sdk_usage_unavailable` | `shows the real API cache usage numbers`, `shows an explicit n/a` |
| 3 digest + drift | `test_cache_blocks_carry_content_digest`, `test_stable_block_digest_stable_across_unchanging_turns` | `renders the per-block content digest`, `flags … as a wasted write`, `does not flag drift when unchanged` |
| 4 mis-zoned state | `test_state_section_in_cached_zone_is_flagged_miszoned`, `test_section_in_uncached_zone_is_never_miszoned` | `shows a mis-zoned chip`, `does not show a mis-zoned chip when …` |
| 5 accuracy (keystone) | `test_emitted_partition_matches_real_system_blocks` | — (server-side guarantee) |
| 6 wiring | `test_cache_attribution_wired_on_live_turn` (drives real `run_narration_turn`) | `consumes the enriched event end-to-end` |

### Rule Coverage

| Rule (python-review) | Test | Status |
|------|------|--------|
| #1 No silent fallbacks / "n/a loudly" | `test_cache_usage_is_explicit_na_when_sdk_usage_unavailable` | failing |
| #6 test quality (meaningful assertions) | self-check done; negative guards documented as deviation | n/a |

CLAUDE.md "No Source-Text Wiring Tests" honored — AC-6 server wiring drives the real
`run_narration_turn` and asserts the watcher event fired (behavior), never greps source. AC-5
asserts the emitted digest equals `sha256(fake.recorded_requests[0].system_blocks[0].text)[:8]` —
the display literally cannot claim "stable" while the real prompt drifted.

**Self-check:** No vacuous assertions in the failing tests (each asserts specific values, not
truthiness). The 2 RED-passing UI tests are intentional negative guards (documented).

**RED verified:** server 9/9 fail for the right reason (`cache_blocks` absent); existing
`test_prompt_zones_dashboard.py` + `test_cache_ttl_prefix_and_otel.py` still green (11 passed).
UI 7/9 fail (fields not rendered).

**Handoff:** To Dev (Ponder Stibbons) for GREEN. See blocking Delivery Finding on the UI
`zones` type mismatch and the emission-seam Question.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-server/sidequest/agents/orchestrator.py` — module helpers
  `_content_digest`, `_section_rides_cache`, `_compute_zones_payload`,
  `_compute_cache_blocks`; new `Orchestrator._build_prompt_event_payload`;
  build-time `prompt_assembled` now carries per-zone+per-section `cached`,
  per-section `mis_zoned`, and `cache_usage: None`, and is suppressed on the
  SDK path; `_run_narration_turn_sdk` emits one enriched `prompt_assembled`
  post-call with `cache_blocks` digests + real `cache_usage`.
- `sidequest-ui/src/components/Dashboard/tabs/PromptTab.tsx` — fixed
  `PromptFields.zones` to the emitted list shape; added Cache Usage card
  (n/a loudly), Cache Blocks card (digest + cross-turn drift / "wasted write"),
  and per-zone cached/uncached + per-section mis-zoned chips in Zone Breakdown.
- Test doubles: added `registry()` to 5 `_FakeRegistry` stubs; refined AC-5/AC-1
  server tests to per-section accuracy; switched 2 UI assertions to
  `getAllByText` (see deviations).

**Tests:** server 9/9 + ui 9/9 (GREEN). Full suites: server 7156 passed / 0
failed, ui 1513 passed / 0 failed. Server ruff + ui tsc/eslint clean. (Pre-existing
pyright `send_stream` warning at orchestrator.py:2577 is unrelated to this change.)

**Branches (pushed):** `feat/60-2-otel-per-block-cache-attribution` in both
sidequest-server and sidequest-ui.

**Handoff:** To verify phase (Igor / TEA — simplify + quality pass).

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned (with documented deviations)
**Mismatches Found:** None requiring code change.

Verified each AC in `context-story-60-2.md` against the implementation
(`orchestrator.py` emission at 3478-3500 + helpers; `PromptTab.tsx`):

- **AC-1 cache boundary** — zones carry `cached`; sections carry per-section
  `cached`. Implementation EXCEEDS the spec (per-section bucket-aware accuracy,
  not just zone-level). Category: Extra-in-code (Behavioral, Trivial).
  Recommendation: **A — update spec interpretation** (already logged as Dev
  deviation). The single-source-of-truth guardrail demanded this.
- **AC-2 real usage + n/a** — `cache_usage` dict carries exactly the six
  required fields (cache_read, cache_write, 5m, 1h, cost_usd, cache_ttl) from
  the SDK result; `None` on the non-SDK build path. Aligned.
- **AC-3 digest + drift** — server emits per-block `sha256[:8]`; cross-turn
  drift computed in PromptTab. Category: Different-mechanism (Cosmetic, Minor).
  Recommendation: **C — clarify spec** (already logged as TEA deviation); the
  "vs previous turn" comparison is correctly a UI concern.
- **AC-4 mis-zoned state** — `mis_zoned = state-category AND cached zone`,
  exactly as the AC reads. Satisfied. NOTE: the Dev Delivery Finding reveals the
  three flagged sections are User-bucket (→ user message, `cached:false`), so
  the flag is a *zone-placement smell* (60-4 re-zone signal), not proof of cache
  churn. The per-section `cached:false` correctly surfaces that nuance, so the
  display does not lie. Category: Ambiguous-spec (Behavioral, Minor).
  Recommendation: **D — defer** the churn-source re-scope to 60-3 (finding
  already logged); no code change here.
- **AC-5 accuracy (keystone)** — emitted `stable` digest equals
  `sha256(real system_blocks[0].text)[:8]`; per-section partition checked
  against the real block. The accuracy test was strengthened from zone-level to
  per-section (Dev deviation). Aligned with the guardrail.
- **AC-6 wiring** — server emits on the live `run_narration_turn` (behavior
  test, no source grep); PromptTab consumes end-to-end. Aligned.

The `isinstance(ToolingLlmClient)` gate for suppressing the build-time emit
reuses the EXACT predicate `run_narration_turn` already uses to route to the
SDK path (orchestrator.py:2361) — no new branching concept introduced
(reuse-first satisfied). No new infrastructure; extends the existing
`prompt_assembled` event and `PromptTab`, per the story's "extend, don't
replace" guardrail.

**Decision:** Proceed to review (verify phase / TEA). No hand-back to Dev.

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed (server 9/9 + ui 9/9; full suites server 7156 / ui 1513, 0 failures).

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 3 (orchestrator.py, PromptTab.tsx, test_prompt_cache_attribution_otel.py)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 2 findings | test `sections_by_name` loop dup (medium); `system_chars`/`user_chars` two-loop (medium) |
| simplify-quality | 5 findings | local-bucket-import ×2 (high, DISMISSED); UI `cached?` optional ×2 (medium, flagged); line-161 "vacuous" (medium, DISMISSED) |
| simplify-efficiency | 2 findings | double `registry.registry()` (high, DISMISSED); `priorBlocksByLabel` rescan (low, dismissed) |

**Applied:** 0 high-confidence fixes.

**Dismissed (with rationale):**
- *Local `bucket` import is a convention violation* (quality, high ×2) — FALSE. `prompt_framework/core.py` imports `bucket` locally inside `compose_split` (line 165) and `compose_split_by_zone` (line 218); local import of `bucket` is the **established** codebase pattern. The new helpers follow it. Hoisting to module level would diverge from the convention.
- *Line 161 `assert isinstance(z["cached"], bool)` is a vacuous type-check* (quality, medium) — FALSE. It is a real `assert` that fails on a non-bool; it guards the contract that `cached` is a JSON bool, not a stringified value. Kept.
- *`registry.registry(agent_name)` called twice on the SDK path* (efficiency, high) — DISMISSED as premature optimization. The list is ~15–30 sections; the call sits on a path dominated by an LLM network round-trip. The suggested fix (return `sections` from `build_narrator_prompt`) would change a signature stubbed by 5 test doubles — risk far exceeds a list-copy saving. Not worth the churn.
- *`priorBlocksByLabel` O(n) backward scan per selection* (efficiency, low) — dismissed. GM dev tool; negligible at playtest scale (the analyst concurred it is not load-bearing).

**Flagged for Reviewer (medium — not auto-applied per verify policy):**
- UI `Zone.cached` / `ZoneSection.cached` are typed optional (`cached?: boolean`) but the server always emits them. Tightening to required is a reasonable type-honesty improvement; left optional for now as defensive tolerance of any pre-deploy/legacy `prompt_assembled` events. Granny may decide.
- Test-only: the `for z in zones → for s in z.sections → map[s.name]=s` pattern recurs ~4× in the new test file; a small `_sections_by_name(zones)` helper would DRY it. Cosmetic, test-only — deferred to avoid churn.

**Overall:** simplify: clean (0 fixes applied; highs dismissed with rationale, mediums flagged).

**Quality Checks:** server ruff + full pytest green; ui tsc + eslint + full vitest green. Working tree clean.

**Handoff:** To Reviewer (Granny Weatherwax) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A (server 7156/0, ui 1513/0, lint+tsc clean) |
| 2 | reviewer-edge-hunter | Yes | findings | 9 | confirmed 0, dismissed 7, deferred 2 |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 5 | confirmed 0, dismissed 5 |
| 4 | reviewer-test-analyzer | Yes | findings | 5 | confirmed 1, dismissed 4 |
| 5 | reviewer-comment-analyzer | Yes | findings | 5 | confirmed 2, dismissed 3 |
| 6 | reviewer-type-design | Yes | findings | 3 | confirmed 1, dismissed 2 (pre-existing) |
| 7 | reviewer-security | Yes | findings | 4 | confirmed 0, dismissed 2, deferred 2 (non-blocking) |
| 8 | reviewer-simplifier | Yes | findings | 3 | confirmed 0, dismissed 3 |
| 9 | reviewer-rule-checker | Yes | findings | 6 | confirmed 2, dismissed 4 |

**All received:** Yes (9 returned, 8 with findings)
**Total findings:** 6 confirmed (all Low/Medium, fixed in-phase), 30 dismissed (with rationale), 6 deferred (non-blocking)

## Reviewer Assessment

**Verdict:** APPROVED
**Data flow traced:** narrator turn → `_run_narration_turn_sdk` assembles `system_blocks` + gets `ToolingResult.usage` → `_compute_zones_payload`/`_compute_cache_blocks` (digest hashes the SAME `stable_text`/`tools_payload` that built the blocks) → `_pub_prompt("prompt_assembled", …)` → `watcher_hub` → `DashboardApp` appends to `promptEvents` → `PromptTab` renders cached/uncached, usage, digest+drift, mis-zoned chip. Safe: digest is computed from the real assembled block strings, so the panel cannot claim "stable" while the prompt drifted (AC-5 test enforces digest == sha256(recorded system_blocks[0])[:8]).

### Observations
- [VERIFIED] AC-5 accuracy gate is genuine — `test_emitted_partition_matches_real_system_blocks` asserts the emitted `stable` digest equals `sha256(fake.recorded_requests[0].system_blocks[0].text)[:8]` (test file) AND per-section `cached` matches substring membership in the real block. Not vacuous.
- [VERIFIED] No-Silent-Fallbacks honored — `cache_usage: None` on the non-SDK path renders an explicit "n/a" in `PromptTab` (no fabricated estimate); confirmed by `reviewer-silent-failure-hunter` (non-violation) and the dedicated n/a test.
- [TYPE] Confirmed + FIXED: `Zone.cached`/`ZoneSection.cached`/`mis_zoned` were typed optional but the server always emits them (high, corroborated by simplify-quality). Made required in `PromptTab.tsx`.
- [RULE] Confirmed + FIXED: `f.total_tokens || 0` → `?? 0` (TS-4); `asyncio.sleep(0.05)` settle sites now commented (PY-9).
- [TEST] Confirmed + FIXED: the no-drift negative test only blocked `/wasted/`; strengthened to `/wasted|changed/` (NOT `/drift/` — that is the column header, a false-match I caught and corrected).
- [DOC] Confirmed + FIXED: `_compute_cache_blocks` docstring no longer claims a call-site guarantee; `_build_prompt_event_payload` now enumerates returned keys.
- [SIMPLE] Dismissed: inline `_section_rides_cache` — kept as a named predicate documenting the load-bearing bucket+zone rule (the heart of the accuracy guarantee).
- [SEC] Dismissed: `cost_usd` exposure — **AC-2 explicitly requires** "cost_usd … shown alongside the breakdown"; "Keith debugging cost" is a named use case; the GM panel is intentionally table-visible (Sebastien). Also already on the `narration.turn` span pre-diff.
- [SEC] Deferred (non-blocking): full section `content` in the watcher payload is **pre-existing** (old zones_payload carried it); flagged for a future hardening if watcher subscribers ever expand beyond the GM panel.
- [TYPE]/[TS-1] Dismissed: `as unknown as PromptFields` double-cast is the **pre-existing** `WatcherEvent.fields: Record<string,unknown>` narrowing convention used by every Dashboard tab; eliminating it requires a discriminated-union refactor of `watcher.ts` (out of scope, noted as Improvement).
- [RULE TS-6] Dismissed: `key={i}` on dropdown options — `promptEvents` is append-only (never reordered/insertion-in-middle/deleted), the one case where index keys are safe; no stable unique id exists on `WatcherEvent`.
- [RULE PY-10] Dismissed: local `bucket` imports match the established `core.py` convention (lines 165, 218); the inline `publish_event` import carries a documented reason (avoids uvicorn logging reconfiguration).
- [EDGE]/[SILENT] Dismissed: empty `stable_text`/`tools_payload` guards — cannot occur on the SDK path (narrator_identity always in Primacy; 26 tool defs always present); new payload values are all JSON-native so the lossy-hub concern adds no new surface.
- [TEST] Dismissed: AC-5 content-substring check "fragility" — the digest equality is the load-bearing gate; content checks corroborate per-section attribution; real multi-line prose makes coincidental collisions negligible (currently green). The mis-zoned negative test DOES discriminate (its state-category sections carry `mis_zoned:false`, so a category-deriving component would over-render and fail).

### Rule Compliance
Checked against `.pennyfarthing/gates/lang-review/{python,typescript}.md`, SOUL.md, CLAUDE.md:
- **No Silent Fallbacks (CLAUDE.md):** COMPLIANT — `cache_usage: None`→explicit "n/a"; `cache_ttl` "n/a" sentinel is loud (string, not a fabricated number).
- **No Source-Text Wiring Tests (server CLAUDE.md):** COMPLIANT — AC-6 wiring drives real `run_narration_turn` + asserts the watcher event; no source grep.
- **Every Test Suite Needs a Wiring Test:** COMPLIANT — `test_cache_attribution_wired_on_live_turn` + UI `consumes the enriched event end-to-end`.
- **PY-3 type annotations:** COMPLIANT — all 5 new module helpers fully annotated.
- **PY-6 test quality:** COMPLIANT — every test asserts specific values; the line-161 `isinstance` is a harmless contract guard, not vacuous.
- **PY-14 state-cleanup ordering:** COMPLIANT — the post-call emit consumes no one-shot queue.
- **TS-4 `||` vs `??`:** COMPLIANT after fix.
- **TS-6 XSS / hooks / keys:** COMPLIANT — no `dangerouslySetInnerHTML`; stable keys on rows/chips; `key={i}` only on the append-only dropdown.
- **TS-1 casts:** pre-existing convention (see dismissal).

### Devil's Advocate
Suppose this is broken. The most dangerous failure mode for a *lie-detector* feature is a panel that lies — so I attacked the accuracy seam hardest. If `_compute_cache_blocks` were fed pre-SDK text while the SDK sent something else, the digest would be confidently wrong; but the call site passes `stable_text`/`valley_text`/`recency_text`/`tools_payload` — the exact variables used three lines earlier to build `system_blocks` and `tools` — and the AC-5 test hashes the *recorded* request, so a divergence fails CI. Could a malicious/confused state make `cached` lie? The per-section flag is `bucket==System AND zone∈{Primacy,Early}` — the same predicate `compose_split_by_zone` uses to route content into `system_blocks[0]`; a User-bucket section in Early correctly reads `cached:false` even though `mis_zoned:true`, which is the subtle truth the epic's mental model got wrong. What about a stressed runtime: empty prompt? narrator_identity is always registered, so `stable_text` is non-empty; a zero-section registry only happens in the stubbed `_FakeRegistry` (zones=[]), which is harmless. A 500-turn session? `priorBlocksByLabel` is O(n) per selection — flagged, dismissed as a dev-tool non-issue. A pre-deploy event lacking the new keys? The card guards (`fields?.cache_blocks &&`, `cache_usage !== undefined`) degrade to hiding the card rather than crashing — acceptable, noted. Confused user reading the panel: the one genuine ambiguity is that a non-SDK turn shows usage "n/a" but omits the Cache Blocks card entirely (undifferentiated absence) — Low severity, deferred. Nothing rises to Critical/High.

**Pattern observed:** clean reuse — extends the existing `prompt_assembled` event + `PromptTab` rather than standing up a parallel panel; the build-emit suppression reuses the exact `isinstance(ToolingLlmClient)` predicate `run_narration_turn` routes on (`orchestrator.py`).
**Error handling:** non-SDK path → `cache_usage: None` (loud n/a); missing fields → cards hide, no crash.
**Handoff:** To SM (Captain Carrot) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Conflict** (blocking): UI `PromptFields.zones` type is `Record<string, {token_count, content}>`
  but the server emits `zones` as a LIST of `{zone, total_tokens, sections}` (orchestrator.py:2246).
  The React Zone Breakdown therefore renders garbage today (`Object.entries(array)` → index keys,
  `data.token_count` undefined → "0/NaN%"). Confirmed live in the RED run output. Dev must
  reconcile the UI type+render to the list shape while adding the cache fields. Affects
  `sidequest-ui/src/components/Dashboard/tabs/PromptTab.tsx` (rewrite zones consumption) and the
  inline `PromptFields` interface. *Found by TEA during test design.*
- **Question** (non-blocking): real SDK `cache_usage` (read/write/cost/ttl) is not available at
  `build_narrator_prompt` emission time (orchestrator.py:2297) — those numbers only exist after
  `complete_with_tools` in `_run_narration_turn_sdk` (orchestrator.py:3319+). The tests require
  `cache_usage` on the SAME `prompt_assembled` event that carries `cache_blocks`. Cleanest seam:
  relocate/enrich the emission to the SDK path post-call (it already holds `registry`, `zone_text`,
  `system_blocks`, and `result.usage`). Existing build-time-only tests
  (`test_prompt_zones_dashboard.py`, `test_prompt_assembled_event_has_split_fields` — both call
  `build_narrator_prompt` directly) will then need to migrate to driving `run_narration_turn`, OR
  Dev keeps a build-time `prompt_assembled` for zones/estimates and emits the enriched one post-call
  (the `_enriched_event` helper tolerates either). Affects `agents/orchestrator.py`. *Found by TEA
  during test design.*
- **Improvement** (non-blocking): the single-source-of-truth guardrail (digest must hash the REAL
  `system_blocks[0].text`) is easiest to honor by computing the stable/valley/recency partition once
  in a shared helper used by BOTH the `system_blocks` assembly (3199-3222) and the emission. AC-5's
  accuracy test (`test_emitted_partition_matches_real_system_blocks`) will fail if Dev recomputes the
  boundary independently. *Found by TEA during test design.*

### Dev (implementation)
- **Conflict** (non-blocking, HIGH VALUE for 60-3): the epic's root-cause hypothesis is likely
  WRONG. The three "mis-zoned" state sections — `narrator_available_confrontations`,
  `trope_beat_directives`, and the NPC roster — are NOT in `STABLE_SECTION_NAMES`
  (`agents/prompt_framework/bucket.py`), so `default_bucket_for_section` returns **User** bucket.
  `compose_split_by_zone` routes User-bucket sections to the per-turn **user message**, NOT
  `system_blocks[0]`. So although they sit in the Early *zone*, they do **not** ride the cached
  prefix and cannot be the source of the block-0 `cache_write` churn. The new eyes confirm this:
  these sections render `mis_zoned: true` (Early-zone smell) but `cached: false` (actually in the
  user message). 60-3 should use this to re-scope: the real per-turn cache_write churn must come
  from a System-bucket section in Primacy/Early that mutates (candidates: `narrator_vocabulary`,
  `genre_transition_hints`, or a promoted genre-prose section whose text varies), OR from 5m-TTL
  expiry — not from these three. 60-4's "re-zone Early→Valley" fix would be a no-op for the cache
  if aimed at these three. Affects `agents/prompt_framework/bucket.py` + the 60-4 fix scope.
  *Found by Dev during implementation.*
- No other upstream findings during implementation.

### Reviewer (code review)
- **Improvement** (non-blocking): the watcher `prompt_assembled` payload carries full prompt
  section `content` (pre-existing — the old zones_payload already did). Harmless while
  `watcher_hub` subscribers are GM-panel-only, but a future spectator/player-facing subscriber
  would receive narrative spoilers. Affects `agents/orchestrator.py` `_compute_zones_payload`
  (consider stripping `content` and relying on the per-block digest, or debug-gating it) — defer
  until subscriber set expands. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `WatcherEvent.fields: Record<string, unknown>` forces every
  Dashboard tab to narrow via `as unknown as <Fields>` double-casts. A discriminated-union event
  type (e.g. `PromptAssembledEvent`) in `sidequest-ui/src/types/watcher.ts` would eliminate the
  casts repo-wide — a broader refactor beyond this story. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Drift detection (AC-3) split server/UI rather than wholly server-side**
  - Spec source: context-story-60-2.md, AC-3 / Technical Guardrails "Account for drift"
  - Spec text: "The display shows whether each cached block's digest changed vs the previous turn"
  - Implementation: server emits the per-block digest (tested server-side); the cross-turn
    *comparison* (drift = digest changed vs prior turn) is tested in PromptTab, which holds the
    list of turns. The server has no natural prior-turn memory per session in the emission path.
  - Rationale: "vs the previous turn" is inherently a UI concern (the panel owns the turn list);
    splitting keeps the server emission stateless and matches "the display shows DRIFT".
  - Severity: minor
  - Forward impact: Dev computes drift in PromptTab from consecutive `promptEvents`, not server-side.
- **Two UI negative-case tests pass in RED by design**
  - Spec source: python-review #6 (test quality) / general vacuous-assertion guard
  - Spec text: "Tests with no assertions / truthy checks that miss wrong values"
  - Implementation: `does not flag drift when unchanged` and `does not show a mis-zoned chip when
    miszoned:false` assert ABSENCE and so pass against the current (empty) PromptTab.
  - Rationale: they are the paired negative guards for the positive assertions; they become
    load-bearing once Dev renders the chips/drift (a future regression that over-fires the chip
    will trip them). Not vacuous post-GREEN.
  - Severity: minor
  - Forward impact: none — Dev should keep them green (don't over-render the flags).

### Dev (implementation)
- **`cached` is per-section bucket-aware, not zone-only; refined AC-5/AC-1 tests**
  - Spec source: tests TEA wrote (`test_emitted_partition_matches_real_system_blocks`,
    `test_zones_carry_cache_boundary_flag`); context-story-60-2.md AC-1/AC-5
  - Spec text: "each zone/section labeled cached (rides system_blocks[0]) ... the event's
    cached/uncached partition matches the actual system_blocks"
  - Implementation: a section rides `system_blocks[0]` iff `default_bucket_for_section(name)
    == System` (in STABLE_SECTION_NAMES) AND zone ∈ {Primacy, Early}. The original AC-5 test
    used a per-ZONE flag and asserted every section in a cached zone is inside `stable_text` AND
    every uncached-zone section is inside the uncached SYSTEM blocks. Real Primacy/Early zones mix
    System-bucket sections (→ block 0) with User-bucket guardrails (→ the user MESSAGE, not any
    system block), so the zone-level check was inaccurate. Refined AC-5 to a per-section `cached`
    check (cached ⇒ content in `stable_text`; not-cached ⇒ content NOT in `stable_text`; dropped
    the "in uncached system block" clause since User-bucket content lives in the user message).
    Added per-section assertions to AC-1 (`narrator_identity` cached True; `narrator_constraints`
    cached False — both in Primacy). Kept the zone-level `cached` rollup for the display.
  - Rationale: a zone-level "Early is cached" flag would itself be the lie the story kills (half
    of Early is in the user message). Per-section accuracy is the single source of truth.
  - Severity: minor (tests strengthened, not weakened)
  - Forward impact: 60-3/60-4 — see Delivery Finding below; the three "mis-zoned" sections are
    User-bucket so they do NOT currently churn block 0.
- **UI cached/uncached assertions use getAllByText, not body.textContent regex**
  - Spec source: tests TEA wrote (`labels each zone as cached or uncached`, wiring test)
  - Spec text: assert "cached" and "uncached" labels render
  - Implementation: `document.body.textContent` concatenates adjacent table cells
    ("Valleyuncached"), defeating a `\bword\b` regex. Switched the two assertions to
    `screen.getAllByText(/^cached$/i)` / `/^uncached$/i`, which match individual cell text nodes.
  - Rationale: more correct RTL; the DOM renders the labels as distinct cells.
  - Severity: trivial
  - Forward impact: none.
- **Build-time `prompt_assembled` suppressed on the SDK path via client type, not a kwarg**
  - Spec source: TEA Question finding (emission seam); CLAUDE.md "extend, don't replace"
  - Spec text: "emit ... on prompt_assembled (or a sibling event)"
  - Implementation: `build_narrator_prompt` skips its build-time emit when
    `isinstance(self._client, ToolingLlmClient)` (the SDK path), which then emits ONE enriched
    event post-call. Chosen over a new `emit_prompt_event` kwarg to avoid changing the signature
    that ~5 existing test doubles stub. Those doubles' `_FakeRegistry` gained a `registry()`
    returning `[]` (the post-call emit reads sections).
  - Rationale: single coherent event per turn (no duplicate GM-panel dropdown entry); minimal
    blast radius; `ToolingLlmClient` ⇔ SDK path is already how `run_narration_turn` routes.
  - Severity: minor
  - Forward impact: any future non-SDK ToolingLlmClient would also suppress the build-time emit
    (correct — it would route to the SDK path).

### Reviewer (audit)
- **TEA: Drift detection split server/UI** → ✓ ACCEPTED: "vs the previous turn" is correctly a
  UI concern (the panel owns the turn list); server emits the digest, UI compares. Sound.
- **TEA: Two UI negative-case tests pass in RED by design** → ✓ ACCEPTED: they are paired negative
  guards and are load-bearing post-GREEN (I strengthened one of them this phase to also block
  "changed", not just "wasted").
- **Dev: `cached` is per-section bucket-aware, not zone-only** → ✓ ACCEPTED: this is the correct,
  stronger reading of AC-1/AC-5. A zone-level flag would itself be the lie the story kills (Early
  mixes System-bucket → block 0 with User-bucket → user message). Verified against
  `compose_split_by_zone` and `bucket.STABLE_SECTION_NAMES`. Tests strengthened, not weakened.
- **Dev: UI assertions use getAllByText** → ✓ ACCEPTED: correct RTL; `body.textContent`
  concatenates adjacent cells. Trivial, sound.
- **Dev: build-time emit suppressed via `isinstance(ToolingLlmClient)`** → ✓ ACCEPTED: reuses the
  exact predicate `run_narration_turn` routes on; avoids a duplicate per-turn GM-panel entry and a
  signature change across 5 test doubles. The `_FakeRegistry.registry()→[]` additions are benign.
- **Undocumented deviations:** None found. The implementation matches the logged deviations and
  the story ACs; the only spec-vs-code gap (the epic's "these three sections churn block 0"
  hypothesis) is correctly captured as a Dev Delivery Finding for 60-3, not a code defect.

### Architect (reconcile)

**Deviation manifest — definitive audit for Story 60-2.**

Verified all in-flight deviation entries (TEA ×2, Dev ×3) against the code and spec sources:
- Spec sources resolve: `sprint/context/context-story-60-2.md` and `sprint/context/context-epic-60.md`
  both exist; `.pennyfarthing/gates/lang-review/python.md` #6 exists.
- Quoted spec text is accurate against the sprint-YAML ACs and the context document.
- Each entry carries all 6 fields (description, spec source, spec text, implementation, rationale,
  severity, forward impact) and the Reviewer stamped all five ACCEPTED.
- Implementation descriptions match the merged code (`orchestrator.py` helpers + dual emission;
  `PromptTab.tsx` list-shape + cards; `_FakeRegistry.registry()` stubs).

**AC accountability:** All 6 ACs DONE (Reviewer verified each against the YAML AC text). No ACs
deferred or descoped → AC-deferral verification is a no-op.

**Additional deviations found during reconcile:**
- No additional deviations found.

**Note for the audit reader:** the epic's stated root cause ("three `state` sections churn the
cached block 0") is contradicted by what these eyes now reveal — those sections are User-bucket
(`STABLE_SECTION_NAMES` excludes them), so they ride the per-turn user message, not
`system_blocks[0]`. This is **not** an implementation deviation (AC-4 only requires flagging
`state`-category sections in a cached *zone*, which the code does correctly); it is an upstream
discovery captured as a Dev Delivery Finding to re-scope 60-3/60-4. Logging it here so the manifest
reader does not mistake the epic-vs-reality gap for a code defect.