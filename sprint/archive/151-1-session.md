---
story_id: "151-1"
jira_key: ""
epic: "151"
workflow: "tdd"
---
# Story 151-1: [NARRATOR] Cache-promote the narrator output contract — add narrator_output_only to STABLE_SECTION_NAMES (ADR-150 quick-win)

## Story Details
- **ID:** 151-1
- **Jira Key:** (skipped — no Jira configured)
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 2
- **Priority:** p2
- **Type:** refactor

## Story Summary

Promote `narrator_output_only` into the cached prefix by adding it to `STABLE_SECTION_NAMES` in `prompt_framework/bucket.py`. This is ADR-150 companion quick-win / Alternative A — independent, shippable first. Expected impact: removes ~4k uncached tokens/turn but does NOT address attention load (that's the rest of the epic).

### Key Constraint (Project Memory: project_adr112_promotion_breaks_test_60_6)

Adding a section to `STABLE_SECTION_NAMES` promotes it into the cached prefix and **BREAKS test_60_6_stable_prefix_live_drift**, which pins the old volatile invariant.

**Fix Strategy:**
1. Verify `narrator_output_only` is byte-identical per session (no runtime interpolation — validated in 2026-06-18 deep-dive).
2. Update `test_60_6` to the new stable invariant (make the field session-static).
3. Validate cache write/read deltas via existing `narration.turn.cached_input_*` OTEL spans.
4. **Full-suite gate required** (not just targeted canary).

## Sm Assessment

**Routing:** Phased TDD workflow. Setup complete → handing off to TEA (Fezzik) for the RED phase. Single repo (`sidequest-server`), 2 points, p2 refactor under epic 151 (ADR-150 sidecar accounting).

**Scope is small and well-bounded:** one symbol changes — add `narrator_output_only` to `STABLE_SECTION_NAMES` in `prompt_framework/bucket.py`. The risk is not the change; it's the blast radius on the cache-prefix invariant tests.

**The landmine is the story.** Project memory `project_adr112_promotion_breaks_test_60_6` is explicit and reproduced in the description: promoting a section into the cached prefix BREAKS `test_60_6_stable_prefix_live_drift`, which pins the OLD volatile invariant. This is NOT a regression to "fix back" — it is the expected consequence of the promotion. TEA's RED phase must:
1. Confirm `narrator_output_only` is byte-identical per session (no runtime interpolation — the 2026-06-18 deep-dive verified this; TEA should re-confirm in code before promoting, since the whole correctness argument rests on it).
2. Write the failing test that pins the NEW stable invariant (the field belongs in the cached/stable prefix), and update/replace `test_60_6_stable_prefix_live_drift` accordingly — don't just delete it.
3. Assert the cache write/read deltas through the existing `narration.turn.cached_input_*` OTEL spans (per the project's OTEL observability principle — promotion must be *observable*, not just asserted).

**Gate discipline:** FULL-SUITE gate required, not a targeted canary. Per project memory, the server suite carries a ~258–269 pre-existing failure baseline (unstubbed objective classifier + DB-url env). TEA/Dev must baseline first and treat only *new* failures as regressions; do NOT run repeated full-suite reruns in background subagents (that's the credit blowup). `SIDEQUEST_DATABASE_URL` and `SIDEQUEST_GENRE_PACKS` must be set or the failure count is a phantom.

**Out of scope (do not creep):** attention-load reduction, prompt re-zoning beyond this one promotion, and the rest of epic 151. This story is Alternative A only — independent and shippable on its own.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-18T20:41:43Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-18T20:12:14Z | 2026-06-18T20:15:09Z | 2m 55s |
| red | 2026-06-18T20:15:09Z | 2026-06-18T20:29:25Z | 14m 16s |
| green | 2026-06-18T20:29:25Z | 2026-06-18T20:35:15Z | 5m 50s |
| review | 2026-06-18T20:35:15Z | 2026-06-18T20:41:43Z | 6m 28s |
| finish | 2026-06-18T20:41:43Z | - | - |

## Delivery Findings

### TEA (test design)
- **Conflict** (non-blocking): The spec's named landmine `test_60_6_stable_prefix_live_drift.py` (and `test_cache_ttl_prefix_and_otel.py`) were **deleted in story 119-3** (commit f970091e, the claude-agent-sdk port). There is **no test_60_6 to "update"** and **no currently-passing test breaks** on this promotion. Affects the story spec / project memory `project_adr112_promotion_breaks_test_60_6` (now stale for narrator_output_only). *Found by TEA during test design — Dev should NOT spend time hunting for test_60_6.*
- **Conflict** (non-blocking): Post-119-3 the per-block `cache=True`/`cache=False` markers are **dead** for the narrator path — `AnthropicSdkClient.complete_with_tools` flattens every `system_blocks` entry into ONE plain `system_prompt` string (`anthropic_sdk_client.py:434`) and the `claude` CLI owns caching. The promotion still delivers the win on a *different* axis: System-bucket → the stable `system_prompt` (CLI-cached across turns) vs User-bucket → the per-turn user message (never cross-turn cached). Affects `prompt_framework/bucket.py` (the one-line add) + Reviewer's mental model. *Found by TEA during test design.*
- **Question/Improvement** (non-blocking): The spec's "validate cache write/read deltas via `narration.turn.cached_input_*` spans" is **not a fixture unit assertion** — those spans only populate from a LIVE SDK call, and fixtures use scripted token counts (a delta assertion would be vacuous). The unit-level proxy (this story's RED) is wire-payload placement (section rides `system_blocks[0]`/`system_prompt`, off the user message). Real ~4k-token/turn rebate should be confirmed by a 2-turn **playtest** measuring `narration.turn.cache_read_tokens` across turns. Affects epic-151 acceptance. *Found by TEA during test design.*

### Dev (implementation)
- No upstream findings. The implementation was the single-line allowlist add TEA scoped; the full suite confirmed zero regressions in the prompt-assembly blast radius. TEA's three findings (stale landmine, dead per-block markers, live-only cache-delta validation) are accurate and I echoed the mechanism in a code comment on `bucket.py` so the next reader isn't misled by the dead `cache=True` markers. *Confirmed by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): The new test file `tests/agents/test_151_1_output_only_cache_promotion.py` is not `ruff format`-clean — two generator expressions (lines ~183, ~212) would be collapsed to one line. Cosmetic; this project's gates run `ruff check` (passes) but NOT `ruff format --check`, so it does not block. Recommend a `ruff format` pass on a future touch. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The absence assertion in `test_output_contract_absent_from_per_turn_user_message` (and the `user_msg` assembly in the companion test) filters `isinstance(m.content, str)`. Non-vacuous TODAY (verified `Message.content` is a str at `orchestrator.py:4000`, and `user_msg` is a real non-empty string), but it would pass VACUOUSLY if the SDK message content ever becomes a content-block list. Add a `assert any(m.role == "user" for m in request.messages)` non-empty guard before the absence check to harden against that future shape change (matches the project's documented vacuous-absence-test anti-pattern). The companion positive assertion (`marker in cached`) is the bulletproof primary proof and is not vacuous. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The two `next(s for s in ... if s.name == SECTION)` calls have no default → raise `RuntimeError`/`StopIteration` (loud, NOT silent) if the section ever fails to register. A `next((...), None)` + explicit `assert section is not None` would turn an opaque PEP-479 message into a named failure. Diagnostic clarity only. *Found by Reviewer during code review.*

## Design Deviations

### TEA (test design)
- **Did not "update test_60_6" — it does not exist**
  - Spec source: story 151-1 description / `context-story-151-1.md` Problem
  - Spec text: "then update test_60_6 to the new stable invariant"
  - Implementation: Wrote a fresh test file (`tests/agents/test_151_1_output_only_cache_promotion.py`) pinning the NEW invariant via the Story 61-20 wire-payload pattern, because `test_60_6_stable_prefix_live_drift.py` was deleted in 119-3 (f970091e).
  - Rationale: Cannot update a deleted test; the new file pins the post-119-3 invariant (section rides the cached System prefix, off the per-turn user message) against the real production SDK path.
  - Severity: minor
  - Forward impact: none — the promotion is unblocked; no legacy test to reconcile.
- **Cache-delta validation tested as wire-payload placement, not span deltas**
  - Spec source: story 151-1 description / `context-story-151-1.md` Problem
  - Spec text: "Validate cache write/read deltas via the existing narration.turn.cached_input_* spans"
  - Implementation: AC3 tests assert the output-contract content lands in the cache-marked `system_blocks[0]` and is absent from the per-turn user message (a deterministic fixture probe). No fixture asserts `cached_input_read_tokens` deltas.
  - Rationale: The cached_input spans populate only on a live SDK call; a delta assertion against a scripted fake would be vacuous (per `feedback_measure_dont_assert`). Live delta validation is a playtest concern (logged as a Delivery Finding).
  - Severity: minor
  - Forward impact: epic-151 should include a playtest verification of the realized rebate.

### Dev (implementation)
- No deviations from spec. Implementation matches TEA's RED tests exactly (one entry added to `STABLE_SECTION_NAMES`); the section was already Primacy-zoned, so no zone change was needed. The stale-spec items (`test_60_6`, per-block cache markers, span-delta validation) are logged under the TEA subsections above and were not re-introduced.

### Reviewer (audit)
- TEA deviation **"Did not 'update test_60_6' — it does not exist"** → ✓ ACCEPTED by Reviewer: independently confirmed `test_60_6_stable_prefix_live_drift.py` was deleted in 119-3 (f970091e). The spec's instruction was un-followable; writing a fresh post-119-3 invariant test against the real SDK path is the correct substitute.
- TEA deviation **"Cache-delta validation tested as wire-payload placement, not span deltas"** → ✓ ACCEPTED by Reviewer: a `cached_input_*` delta assertion against a scripted fake would be vacuous (the fake returns 0/0). Wire-payload placement (marker in `system_blocks[0]`, off the user message) is the correct deterministic unit proxy; the real rebate is rightly a live/playtest measurement. The positive AC3 assertion is non-vacuous.
- Dev "No deviations" → ✓ ACCEPTED: the diff is exactly the one-line allowlist add + comment TEA scoped; no scope creep. No undocumented deviations found in the diff.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Behavioral change (prompt-section bucket placement) — must be pinned against the real SDK path, not just the bucket constant.

**Test File:**
- `sidequest-server/tests/agents/test_151_1_output_only_cache_promotion.py` — 5 tests for the `narrator_output_only` cache promotion.

**Tests Written:** 5 (4 RED, 1 green precondition guard) covering 3 ACs I defined (none were recorded in the sprint YAML).

| AC | Test | Status |
|----|------|--------|
| AC1 — on the allowlist | `test_narrator_output_only_in_stable_section_names` | RED |
| AC1 — resolves System bucket | `test_narrator_output_only_resolves_to_system_bucket` | RED |
| AC2 — byte-static precondition | `test_narrator_output_only_section_carries_no_per_turn_interpolation` | GREEN (guard) |
| AC3 — rides cached system prefix | `test_output_contract_rides_cached_system_prefix` | RED |
| AC3 — absent from per-turn user msg | `test_output_contract_absent_from_per_turn_user_message` | RED |

**RED verified:** 4 fail for the right reason (today `narrator_output_only` is User-bucket → rides the per-turn user message, not `system_blocks[0]`); 1 passes by design (byte-stability is the safety precondition). No collection/import errors.

### Rule Coverage (lang-review/python.md)
| Rule | Coverage |
|------|----------|
| Test quality — meaningful assertions, no vacuous `assert`/truthy | Every test asserts specific membership/equality; deliberately did NOT write a vacuous `cached_input > 0` assertion against the fake (see deviation) |
| Type annotations | All test fns annotated `-> None`; fixture params follow codebase convention (61-20) |
| No source-text wiring tests (server CLAUDE.md) | AC3 tests drive the real `Orchestrator.run_narration_turn` SDK path and inspect the captured wire payload — behavior, not `read_text()`/grep |
| Wiring test present | AC3 (the two SDK-path tests) is the integration/wiring test — the section reaches the production prompt assembly |

**Self-check:** 0 vacuous tests. The one green test (AC2) is a precondition guard, intentionally green; flagged as such.

**The implementation is one line for Dev (Inigo):** add `"narrator_output_only"` to `STABLE_SECTION_NAMES` in `sidequest/agents/prompt_framework/bucket.py` (it is already `AttentionZone.Primacy`-zoned, so System-bucket content rides `stable_text` → `system_blocks[0]`). Then run the FULL suite (baseline ~258–269 pre-existing failures; treat only NEW failures as regressions). Do NOT go looking for `test_60_6` — it's gone (see Delivery Findings).

**Handoff:** To Dev (Inigo Montoya) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-server/sidequest/agents/prompt_framework/bucket.py` — added `"narrator_output_only"` to `STABLE_SECTION_NAMES` (one entry + a doc comment explaining the post-119-3 mechanism: System→`system_prompt` cached, the dead per-block markers, and the deleted `test_60_6`).

**Tests:** 5/5 passing (GREEN) — the 4 previously-RED + the 1 precondition guard.

**Full-suite gate:** `uv run pytest -q` (SIDEQUEST_GENRE_PACKS + DB url set) → 11,846 passed / 88 failed / 3 errors / 1,600 skipped in 84.8s.
- **No regressions.** Zero failures in `tests/agents/` — the entire blast radius of a `STABLE_SECTION_NAMES` change (prompt assembly, buckets, cache, `system_blocks`, `compose_split`). The 88+3 failures are all pre-existing baseline in unrelated subsystems: WWN combat integration (epic-108 in-flight — `tests/integration/test_*_wn_*`), genre loaders (`tests/genre/`), CLI encountergen (`tests/cli/`), barsoom live-content, and the unstubbed objective-classifier `LlmClientError` (`test_create_app_uses_build_llm_client_by_default`). All match the documented baseline categories; none touch prompt bucketing.
- Did not re-run on the prior commit to "prove pre-existing" (banned pattern) — relied on blast-radius reasoning (only `bucket.py` changed) + the failures matching known baseline categories.

**Branch:** `feat/151-1-cache-promote-narrator-output` (pushed to origin, tracking set).

**Self-review:** wired (the constant feeds production `compose_split`/`compose_split_by_zone` on every narrator turn — proven by the AC3 SDK-path tests), follows project patterns (Story 61-20 promotion precedent), all 3 ACs met, no error handling needed (pure data-set membership).

**Note for Reviewer (Westley):** real cache-rebate (~4k tok/turn) is a LIVE/playtest measurement, not a unit assertion (see Delivery Findings). The unit proof here is wire-payload placement. No new OTEL needed — the `narration.turn.cached_input_*` spans already exist and this rides them.

**Handoff:** To Reviewer for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 (format reflow) | confirmed 1 (LOW), dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — manually assessed: a frozenset-membership add has no boundary conditions |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 | confirmed 2 (both LOW after verification), dismissed 0, deferred 0 |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — manually assessed test quality (see Rule Compliance) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — manually assessed: the new `bucket.py` comment is accurate (verified against 119-3/anthropic_sdk_client.py:434) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — manually assessed: no new types; `frozenset[str]` membership only |
| 7 | reviewer-security | Yes | clean | none | N/A — confirmed clean (no ADR-105 concern) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — manually assessed: change is already minimal (one line) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — manual rule enumeration in Rule Compliance below |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`, manually assessed)
**Total findings:** 0 confirmed blocking, 3 confirmed non-blocking (LOW), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

The production change is a single additive entry to the `STABLE_SECTION_NAMES` frozenset plus an explanatory comment. It is correct, minimal, well-documented, and secure. All 5 tests pass; the primary proof (the output contract moves from the per-turn user message into the cached `system_blocks[0]` prefix) is a non-vacuous RED→GREEN behavioral assertion against the real SDK path. The full suite showed zero regressions in the entire blast radius (`tests/agents/`).

**Data flow traced:** `narrator_output_only` section (static `output_only.md` contract, no player data) → `default_bucket_for_section` returns `SectionBucket.System` (because the name is now on the allowlist) → `compose_split_by_zone` routes it into `zone_text[Primacy]` → `stable_text` → `system_blocks[0]` (`cache=True`) → `AnthropicSdkClient` flattens into the shared `system_prompt` (CLI-cached across turns). The per-player action remains in the per-turn user message (`messages`), unaffected. Safe: the relocated content is identical static instructions for every player.

**Observations (tagged by source):**
- `[VERIFIED]` The promotion is correct — `bucket.py:92` adds `"narrator_output_only"` to the frozenset; `default_bucket_for_section` (bucket.py:106) returns `System` for any allowlist member; the section is already `AttentionZone.Primacy` (narrator.py:295), so it rides `stable_text` per `_run_narration_turn_sdk` (orchestrator.py:3902-3919). Complies with the SOUL "Crunch in the Genre" / ADR-098 bucketing rules — this is the same lever Story 61-20 / 57-3 pulled for `world_context`/`genre_extraction`.
- `[SEC]` (reviewer-security) — **clean, confirmed.** The output contract contains zero per-player/perception-filtered data; the PERCEPTION FIREWALL text inside `output_only.md` is a static *instruction* to the narrator, not player-private content. No ADR-105 leakage from placing it in the shared system prefix. Verified: `output_only.md` is a static `_load(...)` with no interpolation.
- `[SILENT]` (silent-failure-hunter, LOW) — the `next()` calls without default raise loudly (not silent); the `isinstance(m.content, str)` absence-filter is non-vacuous today (verified `Message.content` is a str at orchestrator.py:4000) but is a future-vacuity risk worth a non-empty guard. Both recorded as non-blocking improvements.
- `[SIMPLE]` (preflight, LOW) — `ruff format` would reflow two test generator expressions; cosmetic, gate-ungated (`ruff check` passes). Recorded as non-blocking.
- `[TEST]` (subagent disabled — manually assessed) — 5 tests, all with meaningful assertions; AC2 is an intentional green precondition guard (flagged as such by TEA); the AC3 positive assertion is the load-bearing non-vacuous proof. No `assert True`, no truthy-only checks, no skips. One latent future-vacuity in the absence test (see `[SILENT]`), non-blocking. Wiring test present (drives the real `Orchestrator` SDK path — not a source grep, complies with CLAUDE.md "No Source-Text Wiring Tests").
- `[DOC]` (subagent disabled — manually assessed) — the new `bucket.py` comment is accurate: I verified the post-119-3 claim against `anthropic_sdk_client.py:434` (system_blocks flattened to one `system_prompt`) and the deleted-`test_60_6` claim against git (f970091e). No stale/misleading docs.
- `[TYPE]` (subagent disabled — manually assessed) — no new types; `frozenset[str]` membership only; `default_bucket_for_section` return type unchanged.
- `[EDGE]` (subagent disabled — manually assessed) — a frozenset add has no boundary conditions; the only "edge" is whether the section is always registered, which is unchanged by this diff (build_output_format fires every turn at orchestrator.py:1928).
- `[RULE]` (subagent disabled — manual enumeration below in Rule Compliance) — no violations.

### Rule Compliance
- **CLAUDE.md "No Source-Text Wiring Tests":** COMPLIANT — AC3 tests drive `run_narration_turn` and inspect the wire payload (behavior), not file text.
- **CLAUDE.md OTEL Observability Principle:** COMPLIANT — no new subsystem *decision* is introduced (static routing change); the cache effect is already observable via the existing `narration.turn.cached_input_*`/`cache_read_tokens` spans (orchestrator.py:4193). CLAUDE.md exempts changes that don't add a decision; new OTEL is not required here.
- **CLAUDE.md "No Silent Fallbacks":** COMPLIANT — `default_bucket_for_section` has two explicit return branches, no swallowing; the addition creates no fallback.
- **lang-review/python #3 (type annotations):** COMPLIANT — all test fns `-> None`, helpers `-> str`/`-> ScriptedResponse`.
- **lang-review/python #6 (test quality):** COMPLIANT with one non-blocking note — no vacuous asserts today; future-vacuity guard recommended (see `[SILENT]`).
- **ADR-105 perception firewall:** COMPLIANT — confirmed by reviewer-security; no per-player data in the relocated section.

### Devil's Advocate
Let me argue this change is broken. First attack: *moving the output contract out of the user turn changes what the model attends to, degrading narration.* If the model previously keyed on the contract appearing late (recency) in the user message, relocating it to the system prefix could make it emit malformed `game_patch` blocks or skip tool calls. Rebuttal: the section was already `AttentionZone.Primacy` (the highest-attention zone) and its siblings — `narrator_constraints`, `narrator_agency`, `narrator_output_style` — are ALL already System-bucket; this change makes `narrator_output_only` *consistent* with them rather than an outlier stranded in the user turn. The contract's content and zone are unchanged; only the bucket (system vs user message) changed. No quality regression is plausible, and the full agents/ suite (which exercises prompt assembly and SDK-path emission) is green.

Second attack: *the cache win is illusory — maybe the CLI doesn't cache the system_prompt either, making this a no-op.* Rebuttal: even in the worst case it is a strict no-op, never a regression (the bytes move from one part of the prompt to another). The cache spans already populate from live usage, proving the CLI caches *something*; the system prompt is the stable part. TEA correctly deferred the real rebate measurement to a playtest — so we are not over-claiming in a unit test. The story still ships its mechanical change correctly.

Third attack: *the test passes vacuously.* Rebuttal: examined directly — the positive AC3 assertion (`marker in cached`) cannot pass vacuously (it requires the marker to actually be in `system_blocks[0]`, which it was NOT before the fix — that's the RED). The absence assertion is non-vacuous today (user_msg is a real non-empty string). The only latent vacuity is a future content-shape change, recorded as a non-blocking hardening finding.

Fourth attack: *a stressed/edge config breaks it.* Rebuttal: the change is pure data (a frozenset literal); there is no config, no I/O, no input parsing in the diff. The worst a malformed `output_only.md` could do is unchanged by this diff. Nothing here introduces a new failure mode. The devil finds only the three LOW polish items already recorded.

**Deviation audit:** complete — all TEA/Dev deviations stamped ACCEPTED (see Design Deviations → Reviewer (audit)).

**Handoff:** To SM (Vizzini) for finish-story.

## Branch & Repo Info
- **Repo:** sidequest-server
- **Branch Strategy:** gitflow (feat/151-1-cache-promote-narrator-output)
- **Base Branch:** develop
- **Session File:** .session/151-1-session.md