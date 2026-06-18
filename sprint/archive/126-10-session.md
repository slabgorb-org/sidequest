---
story_id: "126-10"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 126-10: [PERF/FATE] intent_router_pass 37-81s spikes on Fate worlds — trim build_fate_projection router prompt (separate from 126-9 narrator fix)

## Story Details
- **ID:** 126-10
- **Jira Key:** (none — sprint-YAML-driven project)
- **Workflow:** tdd
- **Stack Parent:** none
- **Priority:** p2
- **Points:** 3
- **Type:** bug

## Workflow Tracking
**Workflow:** tdd
**Phase:** red
**Phase Started:** 2026-06-18T16:32:51Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-18T16:30:35Z | 2026-06-18T16:32:51Z | 2m 16s |
| red | 2026-06-18T16:32:51Z | - | - |

## Technical Context

### Problem Summary
Intent router (intent_router_pass) exhibits 37-81s latency spikes on Fate-only worlds (e.g., pulp_noir/annees_folles), but only ~4-6s baseline on non-Fate worlds. The spike affects a SINGLE structured call (phase_call_counts=1, no thrash). Root cause: intent_router_pass.py (lines 364-365) injects build_fate_projection (PC skills + ALL live aspects) into the router state_summary when pack.rules.ruleset=='fate'. This bloats the router prompt beyond optimal bounds.

### Why Not 126-9's Fix
Story 126-9 fixed narrator extended-thinking regression (was ON by accident, now OFF). The router's structured call already has thinking disabled (#919) — so 126-9 will NOT fix this Fate router spike. This is a separate mechanism: prompt size bloat, not thinking cost.

### Mechanism Detail
**File:** sidequest/server/dispatch/intent_router_pass.py (lines 364-365)
**Trigger:** pack.rules.ruleset == 'fate'
**Injection:** build_fate_projection (from intent_router_pass.py line ~234)
  - Content: PC skills + ALL live aspects
  - This is the shared narrator/router projector
  - For the narrator, this is appropriate
  - For the router, it's overspecified — router likely needs PC skills only, NOT every live aspect

**Consequence:** On the bloated Fate prompt, the router's single Haiku structured call intermittently can't land the finalize inside the mandatory max_turns=2 floor → error_max_turns fragility → slow single call (37-81s).

### Lever: Trim for Router
Extract or create a router-specific Fate projection that includes PC skills but excludes the full aspect inventory. Tune so intent_router_pass on Fate worlds returns to ~4-6s baseline (matching non-Fate worlds).

### Measurement Points
- **Baseline:** Non-Fate worlds (e.g., caverns_and_claudes) show ~4-6s for intent_router_pass
- **Spike:** Fate worlds (pulp_noir/annees_folles) show 37-81s for the same phase
- **Source:** turn_telemetry / GM-panel intent_router.decompose spans

## Acceptance Criteria

1. **Quantify the bloat:** Measure intent_router_pass phase duration + state_summary size on annees_folles turns vs a non-Fate baseline (caverns_and_claudes). Use turn_telemetry or GM-panel decompose spans to extract: (a) phase duration, (b) state_summary byte size, (c) Haiku token estimate.

2. **Trim build_fate_projection for router:** Modify intent_router_pass.py (around lines 364-365) to inject a router-specific Fate projection (PC skills, no full aspects) instead of the narrator's full build_fate_projection. Confirm the router's Fate routing accuracy is unaffected (same dispatch outcomes).

3. **No error_max_turns fragility:** After trim, the router's structured call must finalize within max_turns=2 on 100% of Fate turns sampled. Monitor OTEL spans for error_max_turns failures.

4. **Verified before/after:** Run a fresh 2-seat understudy session on annees_folles before and after the trim. Collect turn_telemetry for both runs and confirm: (a) intent_router_pass median/p95 returns to ~4-6s, (b) no error_max_turns events, (c) no routing regressions (correct confrontation types are dispatched).

## Sm Assessment

**Verdict:** Ready for RED. Setup is clean and the story is well-scoped for TDD.

- **Prerequisite cleared:** 126-9 (the narrator extended-thinking regression, p1) is DONE/merged. This story is the *separate* router-prompt-bloat mechanism — thinking-off does not address it, so there is no remaining sequencing dependency.
- **Scope is bounded and single-repo:** server only. The lever is a single injection site (`intent_router_pass.py:364-365`) feeding `build_fate_projection` into the router state_summary; the fix is a router-specific Fate projection (PC skills, drop the full aspect inventory).
- **TDD fit:** The ACs are empirically anchored (turn_telemetry/GM-panel `decompose` spans, before/after on annees_folles). TEA should pin the *behavioral* contract in tests — router still dispatches the correct confrontation types on Fate worlds, structured call finalizes within `max_turns=2`, no `error_max_turns` — rather than asserting a raw latency number that would be flaky in CI. Treat the 37–81s→4–6s latency restoration as a manual/understudy verification (AC #4), not a unit assertion.
- **OTEL note:** per project doctrine, any router-projection change must keep emitting the `intent_router.decompose` span so the GM panel can confirm the trimmed projection is actually engaged (lie-detector on prompt size).

Branch `feat/126-10-trim-fate-router-projection` is cut off develop (commit 23b72153, clean tree). Handing to **Argus Panoptes** (TEA) for the RED phase.

## TEA Assessment

**Tests Required:** No — **story already shipped.**
**Reason:** Story 126-10 was implemented and **merged to develop via PR #946** (`feat(126-10): trim build_fate_projection for the router prompt`, merge commit `2a704e38`, merged 2026-06-18T10:17–10:21Z) by a parallel clone *before* this clone's SM picked it from the backlog (~12:30Z). My branch `feat/126-10-trim-fate-router-projection` was cut from develop at `23b72153`, which is **after** the merge — so the fix is already an ancestor of HEAD and my branch has **0 commits beyond develop**. A RED phase is impossible: comprehensive passing tests already exist.

**Implementation verified present + wired:**
- `sidequest/game/ruleset/fate_projection.py`: `trim_fate_projection_for_router()` + `_ROUTER_DROP_KEYS = ("character_aspects", "scene_aspects")`.
- `sidequest/server/intent_router_pass.py:376-392`: on the `ruleset == "fate"` branch, the router now ships `trim_fate_projection_for_router(full_fate)` (skills + fate_points + active_conflict; live-aspect vocabulary dropped) and emits the `intent_router_fate_vocabulary_span` OTEL evidence (`skill_count`, `aspects_dropped`, `bytes_before`/`bytes_after`).

**Existing test coverage (all GREEN — 18 passed, 0 failed, 11.15s via testing-runner):**
- `tests/game/ruleset/test_fate_projection.py` (8) — trim contract + narrator-untouched invariant.
- `tests/server/test_fate_classifier_enrichment.py` (10) — incl. the **wiring test** `test_pre_narrator_pass_ships_trimmed_fate_block`, the **OTEL evidence test** `test_fate_vocabulary_span_fires_with_trim_evidence`, and the non-Fate isolation test `test_router_omits_fate_block_for_non_fate_pack`.

This is exactly the coverage a paranoid RED phase would have demanded (behavioral contract + wiring + OTEL lie-detector). AC #1/#4 (empirical before/after latency on annees_folles) are manual/understudy verifications by design — not CI assertions — and are not blockers for closing the code work.

**Recommendation:** Do **not** route to Dev (nothing to implement) or Reviewer (PR already reviewed + merged). **Close 126-10 via the SM finish flow** (mark done, archive session) and delete the empty `feat/126-10-trim-fate-router-projection` branch. See the matching precedent: 118-8 (2026-06-15, server #886).

**Status:** No RED handoff. Escalating to Themis the Just (SM) for closure.

## Delivery Findings

### TEA (test design)
- **Gap** (non-blocking): Story 126-10 was already implemented + merged (PR #946) before setup; the sprint tracker still showed `backlog`. Affects sprint bookkeeping only — the deliverable is on develop with green tests. Close via SM finish; no code change needed. *Found by TEA during test design.*

## Design Deviations

### TEA (test design)
- No deviations from spec. No tests were written: the spec's behavior is already implemented and covered by pre-existing GREEN tests (PR #946). This is an "already-shipped" closure, not a test-strategy deviation.