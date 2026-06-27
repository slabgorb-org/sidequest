---
story_id: "158-41"
jira_key: null
epic: "158"
workflow: "tdd"
---
# Story 158-41: Narrator max_turns must degrade loudly (ADR-006), not crash+teardown

## Story Details
- **ID:** 158-41
- **Jira Key:** None (Jira not enabled for this project)
- **Workflow:** tdd
- **Type:** bug
- **Points:** 3
- **Priority:** p1
- **Stack Parent:** none
- **Repos:** sidequest-server
- **Branch:** feat/158-41-narrator-maxturns-graceful-degrade (off `develop`)

## Story Summary

GENERAL narrator robustness — NOT dogfight-specific (split out of 158-29). When the Anthropic SDK tool loop hits its turn cap (AnthropicSdkLoopExceeded, anthropic_sdk_client.py ~line 518), the turn currently HARD-CRASHES: session.disconnect_save -> room teardown -> forced reconnect. Per ADR-006 (graceful degradation) it must degrade loudly and observably and KEEP THE SESSION ALIVE — emit an OTEL span, surface a player-facing "the engine could not resolve that, try rephrasing", and continue the room rather than wedge it. Any subsystem that fails to seat can trigger this; the dogfight router-decline (158-29) was one trigger, but the fix is generic and lives in the narrator/SDK loop, not in the dogfight. Repro: coyote_star 2026-06-25 (a ship-combat verb that did not route).

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-27T17:27:36Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-27T16:27:33+00:00 | 2026-06-27T16:31:30Z | 3m 57s |
| red | 2026-06-27T16:31:30Z | 2026-06-27T16:47:55Z | 16m 25s |
| green | 2026-06-27T16:47:55Z | 2026-06-27T17:01:57Z | 14m 2s |
| review | 2026-06-27T17:01:57Z | 2026-06-27T17:13:29Z | 11m 32s |
| red | 2026-06-27T17:13:29Z | 2026-06-27T17:18:44Z | 5m 15s |
| green | 2026-06-27T17:18:44Z | 2026-06-27T17:21:19Z | 2m 35s |
| review | 2026-06-27T17:21:19Z | 2026-06-27T17:27:36Z | 6m 17s |
| finish | 2026-06-27T17:27:36Z | - | - |

## Technical Approach

**Symptom:** When the Anthropic SDK anthropic_sdk_client.py hits max_turns=8 (AnthropicSdkLoopExceeded), the session crashes hard: session.disconnect_save -> room teardown -> forced reconnect, wedging the player mid-turn.

**Root Cause:** Any subsystem that fails to seat (router declines dispatch, seater cannot find an opponent, etc.) leaves the narrator with no mechanical tools. The narrator falls back to tool-less generation and flails the SDK loop to exhaustion without ever degrading.

**Solution (ADR-006 Graceful Degradation):**
1. **Catch AnthropicSdkLoopExceeded** in the narrator/SDK loop handler (likely anthropic_sdk_client.py or the caller in narration orchestration)
2. **Emit an OTEL span** (e.g., `narrator.sdk_loop_exhausted` with span tags: max_turns, attempt_count, subsystem_name if available) — the GM panel lie-detector must see this
3. **Surface a player-facing degradation message** — "the engine could not resolve that, try rephrasing" or similar — NOT the technical exception
4. **Continue the room** — do NOT call session.disconnect_save, do NOT teardown. The session stays alive and accepts the next action.

**Acceptance Criteria:**
- When the SDK loop hits max_turns, an OTEL `narrator.sdk_loop_exhausted` span fires (not `watcher_crashed`)
- A player-visible narration message replaces the technical exception: "the engine could not resolve that, try rephrasing" or similar, styled consistently with other degradation messages
- Session remains connected; room state intact; player can submit the next action
- Verification: build a TEA test that triggers max_turns exhaustion, assert the span fires and the degradation message reaches the player without disconnect

**Related:**
- ADR-006 (Graceful Degradation) — principle and patterns
- 158-29 (Dogfight router→seater→lifecycle) — triggered by dogfight router decline, but fix is generic
- 158-28 (WWN combat seats) — also depends on smooth degradation if seating fails

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): `tests/server/test_turn_record_wiring.py` (3 tests) is RED in this
  workspace — the full-turn fixture path dies at `monster_manual_inject.py:184`
  (`ValueError: not enough values to unpack`) when `_execute_narration_turn` runs
  `ensure_loaded` against the `session_fixture` pack's auto-mock `effective_bestiary`.
  Pre-existing (I touched no server code); a broken window on the canonical narration-turn
  wiring fixture. Affects `tests/server/conftest.py::session_fixture` /
  `sidequest/server/dispatch/monster_manual_inject.py` (the unpack needs a defensive guard,
  or the fixture pack needs a real `effective_bestiary`). My 158-41 tests sidestep it by
  patching `ensure_loaded`→None; Dev/Reviewer should decide whether to fix the fixture here.
- **Gap** (non-blocking): `AnthropicSdkCostCeilingExceeded` (the sibling terminal-SDK
  condition) documents in its docstring that "the WS handler / broadcast layer can build the
  typed `session.cost_ceiling_exceeded` message" — but no `except` for it exists in
  `sidequest/server/` or `sidequest/handlers/` (it is only *raised* in `cost_safety.py`). So
  the cost-ceiling degrade is likely **also uncaught** and crashing the same way. Out of scope
  for 158-41 (loop-exhaustion only), but the fix Dev writes here is the natural template to
  extend to the cost-ceiling sibling — worth a follow-up. Affects
  `sidequest/server/websocket_session_handler.py` (the same catch seam, ~1075).
  *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): broader scope of TEA's first finding — **~76 server tests are RED
  in this workspace, pre-existing and unrelated to 158-41** (confirmed by an A/B baseline:
  restored the committed pre-fix handler, ran the failing-file set → 31 failed; restored my
  fix → identical 31 failed, so my change adds ZERO regressions). Almost all die at
  `monster_manual_inject.py:184` `ValueError: not enough values to unpack (expected 2, got 0)`
  — the `tests/server/conftest.py::session_fixture` pack is a `MagicMock` whose
  `effective_bestiary` auto-mock unpacks to 0 values when `_execute_narration_turn` runs
  `ensure_loaded`. A handful more are `pregen` bestiary baselines (`flickering_reach`).
  Affected suites include `test_turn_record_wiring`, `test_turn_span_wiring`,
  `test_45_20_trope_resolution_wire`, `test_tension_tracker_turn_wiring`,
  `test_lull_escalation_turn_wiring`, `test_scenario_bind`, `test_player_turn_author`,
  `test_59_30_region_transition_stamp`, `test_45_2_chargen_to_playing_wire`. **Fix is a
  one-liner** (give `session_fixture` a real `effective_bestiary` returning `(Bestiary(...),
  world)`, or guard the unpack in `monster_manual_inject.py:184`) but it is a broken-window
  story of its own — out of scope for a p1 narrator-degrade bug. Affects
  `sidequest-server/tests/server/conftest.py` / `sidequest/server/dispatch/monster_manual_inject.py`.
  *Found by Dev during implementation.*
- **Question** (non-blocking): the server now emits the degrade as an `ERROR` frame with
  `reconnect_required=False` (code `narrator_loop_exhausted`). The **server** session stays
  alive, but it's worth a UI check that the client renders a non-reconnect ERROR gracefully
  (inline notice, no `clearSession()`/teardown) rather than as a disruptive failure — cf. the
  ui #350 `error→clearSession()` reconnect bug. If the UI treats any ERROR as fatal, a small
  follow-up may be needed to render `reconnect_required=False` degrades inline. Affects
  `sidequest-ui` (error-frame handling) — verification/UX, not a server change.
  *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): the AC-3 watcher-fields assertion is too weak to verify the story's
  observability contract — it must lock the GM-panel keys. Affects
  `sidequest-server/tests/server/test_158_41_narrator_maxturns_degrade.py` (strengthen the
  fields assertion to require `genre_slug`/`player_id`/`turn`/`reason`/`recovery`).
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking): test docstrings overclaim ("doubles as the wiring test" /
  "the same entrypoint a live PLAYER_ACTION hits") and use stale "RED today" framing (test +
  fix land in one diff). Affects `sidequest-server/tests/server/test_158_41_narrator_maxturns_degrade.py`.
  *Found by Reviewer during code review.* → CLOSED in rework round 1 (docstrings de-overclaimed; no "RED today" remains; comment-analyzer + test-analyzer confirm).
- **Improvement** (non-blocking, re-review round 2): the `_bypass_pre_narrator_seams` helper
  docstring says "the live develop red at `monster_manual_inject.py:184`" — a CI-state phrase
  that is accurate today but goes stale once that pre-existing fixture rot is fixed. Bundle the
  one-line reword with the tracked `monster_manual_inject:184` broken-window fix (TEA/Dev
  findings above) — when that line stops failing, update this comment in the same pass. LOW;
  does not match a numbered rule; no AC/behavior impact; was present (unflagged) in round 1.
  Affects `sidequest-server/tests/server/test_158_41_narrator_maxturns_degrade.py`.
  *Found by Reviewer during re-review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Pinned a concrete watcher event name as the AC-3 contract**
  - Spec source: context-story-158-41.md / SM Assessment item 1 ("an OTEL watcher span fires … e.g. `narrator.sdk_loop_exhausted`")
  - Spec text: the story says "emit an OTEL span" without fixing a name
  - Implementation: the test asserts a `_watcher_publish` event of type **`narrator.sdk_loop_exhausted`** with a non-empty fields dict, captured by patching `websocket_session_handler._watcher_publish` (the GM-panel watcher channel, same as `session.cost_ceiling_exceeded`). NOT a raw OTEL tracer span — `publish_event` only mints an OTLP span when `SIDEQUEST_WATCHER_AS_SPANS=1` (tea-gotchas), so a span-exporter assertion would be flaky; the watcher channel is the deterministic, GM-panel-true surface.
  - Rationale: a behavior-test needs a concrete event name; the watcher channel is how the GM panel actually observes every other degrade (`intent_router.degraded_continue`, `confrontation_evaluation`).
  - Severity: minor
  - Forward impact: Dev may rename the event with a matching one-line test edit — it is a contract anchor, not a mandate.
- **Pinned the player-facing degrade phrase token "rephras"**
  - Spec source: context-story-158-41.md, the story-mandated message
  - Spec text: "surface a player-facing 'the engine could not resolve that, try rephrasing'"
  - Implementation: AC-2 asserts the serialized outbound contains `"rephras"` (covers rephrase/rephrasing) and that no message sets `reconnect_required` and that the raw exception class name does not leak. Message TYPE is left to Dev (NARRATION vs a non-reconnect ERROR) — only the player-visible guidance + no-forced-reconnect are pinned.
  - Rationale: the rephrase guidance is the story's literal contract; pinning the token (not the full sentence) lets Dev phrase naturally.
  - Severity: minor
  - Forward impact: none — wording latitude preserved.
- **Tests patch two pre-1075 seams (`monster_manual_inject.ensure_loaded`→None, `execute_intent_router_pre_narrator_pass`→(None,None))**
  - Spec source: SOUL / CLAUDE.md "drive the REAL production turn"
  - Spec text: wiring tests must drive the real method, not a unit shim
  - Implementation: the tests DO drive the real `_execute_narration_turn`; they only neutralize the two documented module-level LLM/IO seams that precede the orchestrator call (one is the live develop red at `monster_manual_inject.py:184`; the other would spawn a real Claude client). The subsystem under test (the SDK-loop catch at ~1075) runs for real.
  - Rationale: reach the orchestrator seam deterministically without a live narrator; mirrors the precedent in `test_dungeon_room_population_153_23.py`.
  - Severity: minor
  - Forward impact: if Dev moves the catch ABOVE the monster-manual/router seams, these patches can be dropped — re-evaluate at GREEN.

### Dev (implementation)
- **Surfaced the player degrade as a non-reconnect ERROR frame, not a NARRATION**
  - Spec source: context-story-158-41.md / TEA AC-2 (message TYPE left to Dev)
  - Spec text: "surface a player-facing 'the engine could not resolve that, try rephrasing'"
  - Implementation: `return [_error_msg("The engine could not resolve that action — please try rephrasing it.", reconnect_required=False, code="narrator_loop_exhausted")]` — an ERROR frame with `reconnect_required=False`, not a fabricated in-world NARRATION.
  - Rationale: an SDK-loop exhaustion is an engine failure, not in-world fiction — an honest system/error notice is truer than dressing it as narration, and it avoids the heavy `_emit_event` projection/MP path (minimalist). `reconnect_required=False` is the load-bearing "session stays alive" bit. Satisfies AC-2 (contains "rephras", no reconnect, no raw-exception leak).
  - Severity: minor
  - Forward impact: UI renders this as a non-reconnect error toast/line rather than an inline story beat — see the delivery finding below re: the UI's error handling.
- **Kept the catch BELOW the monster-manual/intent-router seams (at the orchestrator call ~1075), so TEA's two pre-1075 patches remain necessary**
  - Spec source: TEA deviation "if Dev moves the catch ABOVE … these patches can be dropped"
  - Spec text: the exhaustion is raised by `run_narration_turn` (1075); TEA suggested re-evaluating patch placement at GREEN
  - Implementation: caught precisely at the `await sd.orchestrator.run_narration_turn(...)` call (1075), mirroring the `IntentRouterFailure` degrade precedent (1025). The pre-1075 seams are unrelated to where the exhaustion arises, so I did not move the catch up.
  - Rationale: the exhaustion originates at the orchestrator call; catching it there is the minimal, locally-correct seam. Moving the catch higher would broaden the try over unrelated code.
  - Severity: minor
  - Forward impact: none — TEA's tests still pass with their pre-1075 patches in place (3/3 green).

### Reviewer (audit)
- TEA "Pinned watcher event name `narrator.sdk_loop_exhausted`" → ✓ ACCEPTED by Reviewer: matches the implementation and the watcher channel the GM panel reads; the contract-anchor framing is correct.
- TEA "Pinned the phrase token `rephras`" → ✓ ACCEPTED by Reviewer: faithful to the story's literal guidance; pinning the token (not the sentence) is the right latitude.
- TEA "Tests patch two pre-1075 seams" → ✓ ACCEPTED by Reviewer: legitimate and well-justified; rule-checker confirmed both monkeypatches target where-used (no stale-import smell) and the tests still drive the real production method.
- Dev "Non-reconnect ERROR frame, not NARRATION" → ✓ ACCEPTED by Reviewer: honest (an engine failure is not in-world fiction); `reconnect_required=False` is the load-bearing session-alive invariant, correctly set.
- Dev "Kept the catch BELOW the seams at ~1075" → ✓ ACCEPTED by Reviewer: the exhaustion originates at the orchestrator call; catching it there is the minimal, locally-correct seam mirroring `IntentRouterFailure`.
- **No undocumented deviations.** The REJECT findings below are test-assertion-strength + docstring-accuracy gaps, not unlogged spec deviations.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/sidequest/server/websocket_session_handler.py` — import `AnthropicSdkLoopExceeded`; wrap the `run_narration_turn` call (~1075) in `try/except AnthropicSdkLoopExceeded`: emit `narrator.sdk_loop_exhausted` watcher event (component=narrator), log a warning, and `return` a non-reconnect `_error_msg` rephrase notice. The method-level `finally` still files the degraded `TurnRecord`. (+53/−1)

**How the fix maps to the ACs:**
- AC-1 (session alive): the exhaustion no longer propagates — `_execute_narration_turn` returns outbound, so the upstream `disconnect_save`/teardown trigger is gone.
- AC-2 (player message, no reconnect): `_error_msg(…rephrasing…, reconnect_required=False, code="narrator_loop_exhausted")`.
- AC-3 (GM-panel observability): `_watcher_publish("narrator.sdk_loop_exhausted", {genre,world,player_id,action_len,turn,reason,recovery}, component="narrator", severity="warning")`.

**Tests:** 3/3 passing (GREEN) — `tests/server/test_158_41_narrator_maxturns_degrade.py`.
**Regression check:** A/B baseline on the 13 affected-looking suites → 31 failed both before AND after my change (identical), i.e. **zero new regressions**. The pre-existing reds are fixture/content rot (`monster_manual_inject.py:184`), captured as a delivery finding. `ruff check` clean, `ruff format` clean, import sanity verified (no cycle).
**Branch:** `feat/158-41-narrator-maxturns-graceful-degrade` (pushed to origin, commit `cce453f4`).

**Self-review:** wired into the live turn path (the real `_execute_narration_turn`, the PLAYER_ACTION entrypoint); follows the `IntentRouterFailure` degrade pattern already in this method; narrow catch (only `AnthropicSdkLoopExceeded`, no bare except); no silent swallow (loud watcher event + log + player message); ADR-006 satisfied; dogfight untouched (SOUL "Bind the Ruleset").

**Handoff:** To Reviewer (Chrisjen Avasarala).

## Sm Assessment

**Setup verified (Camina Drummer, SM):**
- Repo tag was wrong in YAML (`pennyfarthing`); corrected to `sidequest-server` before setup (Keith confirmed). The description names `anthropic_sdk_client.py` and siblings 158-42/43 are `sidequest-server`. `pf sprint story field 158-41 repos` now returns `sidequest-server`.
- Branch `feat/158-41-narrator-maxturns-graceful-degrade` created in **sidequest-server** off `develop`. Orchestrator returned to `main` for sprint coordination.
- Session at orchestrator-root `.session/`, context at `sprint/context/context-story-158-41.md`. Status → `in_progress`.

**Scope for TEA (RED):** GENERAL narrator/SDK-loop robustness — NOT dogfight-specific. Write a failing test that drives the SDK tool loop to its `max_turns` cap (`AnthropicSdkLoopExceeded`, `anthropic_sdk_client.py` ~518) and asserts the **degrade-loudly** contract, not the crash:
1. An OTEL watcher span fires on the exhaustion path (e.g. `narrator.sdk_loop_exhausted`) — per the project OTEL principle, the GM panel must be able to see the degraded path engaged. This is the wiring test; assert the span, not a source-grep.
2. A **player-facing** degradation narration reaches the player ("the engine could not resolve that, try rephrasing"-style), not the raw exception.
3. The session **stays alive**: no `disconnect_save`, no room teardown, room accepts the next action.

**Guardrails:** Bind/degrade at the loop boundary — do NOT balance or re-route the dogfight here (that's 158-29/153; this fix is generic). No silent swallow — the span MUST emit. Keep `develop` as the base for sidequest-server (gitflow); never `main`.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Behavioral bug fix with an observable contract (no-crash + player message + watcher event). TDD RED.

**Test File:**
- `sidequest-server/tests/server/test_158_41_narrator_maxturns_degrade.py` — 3 failing tests, one per AC, all driving the REAL `_execute_narration_turn` production method (the live PLAYER_ACTION entrypoint → doubles as the wiring test).

**The bug (confirmed by reading the code):** the method-level `try:` at `websocket_session_handler.py:821` has only a `finally:` (2857) — NO `except`. So `AnthropicSdkLoopExceeded` raised by `sd.orchestrator.run_narration_turn` (1075) records a degraded `TurnRecord` in the finally, then **re-raises and escapes** → upstream forces `disconnect_save` (578) → room teardown → reconnect. `AnthropicSdkLoopExceeded` is caught **nowhere** in `sidequest/server/` or `sidequest/handlers/`.

**Tests Written:** 3 tests covering 3 ACs
| AC | Test | Asserts | Status |
|----|------|---------|--------|
| AC-1 no-crash (session alive) | `test_sdk_loop_exhaustion_does_not_crash_the_turn` | `_execute_narration_turn` returns a non-empty list, does not raise | RED (raises) |
| AC-2 player-facing degrade, no reconnect | `test_..._surfaces_player_rephrase_message_without_reconnect` | outbound contains `"rephras"`; no `reconnect_required`; raw exception class not leaked | RED (raises) |
| AC-3 GM-panel observability | `test_..._emits_watcher_degrade_event` | `narrator.sdk_loop_exhausted` watcher event fired with non-empty fields | RED (raises) |

**RED verification:** all 3 fail because `AnthropicSdkLoopExceeded` propagates out of the method (the exact bug) — the assertions are unreachable until the catch exists. A throwaway probe (since removed) confirmed the tests reach the orchestrator seam at 1075 and isolate the right failure.

### Rule Coverage
| Rule (CLAUDE.md / lang-review) | Test(s) | Status |
|------|---------|--------|
| No Source-Text Wiring Tests → use OTEL/watcher span assertions | `test_..._emits_watcher_degrade_event` (asserts the watcher event via the real turn, never a source-grep) | failing |
| Every test suite needs a wiring test (reachable from production path) | all 3 drive the real `_execute_narration_turn` | failing |
| No Silent Fallbacks (degrade must be LOUD) | AC-3 watcher event + AC-2 visible player message | failing |
| `python.md` type-design rules (validated ctors, non_exhaustive, Deserialize bypass, private fields, tenant ctx) | N/A — this is a control-flow/observability bug; no new types/constructors/fields introduced | n/a |

**Rules checked:** the applicable project rules are the wiring/observability ones (covered); the lang-review *type-design* checks don't apply to a degrade-path bug (no new type surface).
**Self-check:** 0 vacuous tests — every assertion is meaningful; ruff check clean, ruff format applied.

**Implementation pointer for Dev (Naomi):** mirror the in-method `IntentRouterFailure` degrade precedent (1025-1059) — catch `AnthropicSdkLoopExceeded` around the `run_narration_turn` call (1074-1075), emit `_watcher_publish("narrator.sdk_loop_exhausted", {...})`, build a player-facing NARRATION (or non-reconnect ERROR) carrying the rephrase guidance, and `return` that outbound (the `finally` already files the degraded TurnRecord). Do NOT add a silent swallow and do NOT touch the dogfight. See the two Delivery-Findings Gaps (pre-existing `test_turn_record_wiring` red; the cost-ceiling sibling is likely also uncaught — a natural follow-up using the same seam).

**Handoff:** To Dev (Naomi Nagata) for GREEN.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (6 confirming obs) | N/A — confirms 3/3 green, lint clean, format clean, 0 smells |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via `workflow.reviewer_subagents`; domain assessed by Reviewer (see [EDGE]) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings; domain assessed by Reviewer (see [SILENT]) |
| 4 | reviewer-test-analyzer | Yes | findings | 4 | confirmed 4 (1 → blocking HIGH, 3 → LOW hardening) |
| 5 | reviewer-comment-analyzer | Yes | findings | 5 | confirmed 5 (all LOW doc-accuracy) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings; domain assessed by Reviewer (see [TYPE]) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings; domain assessed by Reviewer (see [SEC]) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings; domain assessed by Reviewer (see [SIMPLE]) |
| 9 | reviewer-rule-checker | Yes | findings | 1 | confirmed 1 (Rule #6 — corroborates #4's AC-3 finding) |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 6 confirmed (1 blocking HIGH, 5 non-blocking LOW), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** REJECTED

The production fix is **correct, clean, and rule-compliant** — but the test suite does not actually verify the story's load-bearing AC-3 (GM-panel observability). Two independent subagents (test-analyzer HIGH, rule-checker HIGH) flag the same confirmed **Rule #6** violation: the watcher-fields assertion is a bare dict-truthiness check that passes with a placeholder payload. In a project whose central principle is "the GM panel is the lie detector," an observability AC verified only by `assert non-empty dict` leaves the most important claim of the story unbacked. I cannot dismiss a finding that matches a stated project rule, and the project forbids deferring review findings — so this goes back for a focused test-hardening pass. The production code does **not** need to change.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH][TEST][RULE] | AC-3 fields assertion `isinstance(fields, dict) and fields` is a bare truthiness check (Rule #6: "truthy check misses wrong values"). It passes with `{"x":1}` — it does NOT verify the GM-panel keys the production code emits, so the story's observability AC is effectively unverified. Corroborated by test-analyzer + rule-checker. | `tests/server/test_158_41_narrator_maxturns_degrade.py:187` | Assert the keys: `assert {"genre_slug","player_id","turn","reason","recovery"}.issubset(degrade_events[0]["fields"])` and pin `reason == "max_turns_exhausted"`, `recovery == "degraded_continue"`. |
| [LOW][TEST] | AC-3 does not assert `severity="warning"` — the GM panel routes by severity; a silent drop to "info" would pass. | test file (`_capture` + AC-3) | Capture the `severity` kwarg in `_capture` and `assert degrade_events[0]["severity"] == "warning"`. |
| [LOW][TEST] | AC-1 does not assert the degraded `TurnRecord` was filed; "session stays alive" includes the turn being recorded, not silently dropped. | test file (AC-1) | Add `handler._validator.submit.assert_called_once()`. |
| [LOW][TEST] | AC-2 checks only the exception CLASS name is absent, not the raw message; `str(exc)` ("…max_turns=8") could leak alongside "rephras" and still pass. | test file (AC-2) | Add `assert "max_turns" not in serialized`. |
| [LOW][DOC] | Test docstrings overclaim: "doubles as the wiring test" / "the same entrypoint a live PLAYER_ACTION hits" — the tests call `_execute_narration_turn` directly, bypassing `handle_message → handler dispatch`. (My own 107-1 precedent: overclaiming wiring docstrings don't stand.) | test file module docstring (~L24, L101) | Qualify: drives the real method body; not a full dispatch-chain wiring test. |
| [LOW][DOC] | Stale "RED today" framing in per-test docstrings — test + fix ship in one diff, so the tests are green at merge. | test file (per-test docstrings) | Reframe conditionally ("without the catch, this fails"). |

**Findings by dispatch tag (all 8 domains):**
- `[TEST]` (test-analyzer, ENABLED): the AC-3 fields weakness (HIGH) + 3 LOW hardening gaps (severity, TurnRecord-filed, raw-message-leak). Confirmed.
- `[RULE]` (rule-checker, ENABLED): production code passes all 13 lang-review rules + 5 additional (No Silent Fallbacks, OTEL, narrow-except, logging, no source-text-wiring) — **1 violation**, Rule #6, the same AC-3 fields truthiness check. Corroborates `[TEST]`. Confirmed.
- `[DOC]` (comment-analyzer, ENABLED): 5 doc-accuracy findings — the wiring-test overclaim + stale "RED today" (both confirmed LOW above); plus the prod comment's "reconnect" wording is slightly imprecise (the ws_endpoint sends `reconnect_required=False` then the socket still closes/tears down) and the "method-level try has only a finally" line could read ambiguously now that an inner try/except exists. The "reconnect" nuance is cosmetic — the player IS practically forced to reconnect because the socket closes; I rate it LOW and fold the wording tidy-up into the rework.
- `[EDGE]` (DISABLED — assessed by Reviewer): I traced the boundary paths. The early `return` from the except is inside the method-level `try`, so the `finally` (2857) runs and is None-safe (`result` is None → `getattr` chain yields "unspecified"). The return correctly skips `record_interaction` (1439) and `room.save` (1687) — proper for an unresolved turn; pre-narrator dispatch-bank mutations sit in the in-memory snapshot and persist on the next successful turn/disconnect (acceptable, noted). No unhandled boundary.
- `[SILENT]` (DISABLED — assessed by Reviewer): NOT a silent swallow — the except emits a watcher event + `logger.warning` + a player message. `_watcher_publish`/`publish_event` is fire-and-forget safe (drops silently if no loop/subscribers; won't raise). Complies with No Silent Fallbacks. (rule-checker A1 concurs.)
- `[TYPE]` (DISABLED — assessed by Reviewer): no new types/fields; reuses `_error_msg(str, bool, code=str)` and `_watcher_publish(str, dict, ...)` with correct types. No stringly-typed API introduced. Clean.
- `[SEC]` (DISABLED — assessed by Reviewer): no new input boundary; logs no PII — `action_len` (not `action`) and `player_id` (a session slug, logged elsewhere already), `exc` is an engine message with no secrets. No injection surface. (rule-checker #11 + A4 concur.)
- `[SIMPLE]` (DISABLED — assessed by Reviewer): minimal fix mirroring the `IntentRouterFailure` precedent; the ~15-line comment is justified for a load-bearing degrade decision in a lie-detector culture. No over-engineering, no dead code.

### Rule Compliance
Enumerated the changed lines against `python.md` (13 checks) + SOUL/CLAUDE additional rules. Production file (`websocket_session_handler.py`): **compliant on all** — #1 narrow `except AnthropicSdkLoopExceeded` (not bare); #4 `logger.warning` (correct level for a recoverable degrade), lazy `%s/%d` format, no PII; #9 the `await` is properly awaited and the early `return` from the async method needs no await; #10 the new import is correctly OUTSIDE `TYPE_CHECKING` (runtime use in the except) and adds no cycle (same module already imported elsewhere); A1 No Silent Fallbacks ✓; A2 OTEL watcher event with a rich payload ✓; A3 narrow except ✓; A5 no source-text wiring tests ✓. Test file: **one violation** — #6 test quality, the AC-3 fields truthiness check (line 187). All three monkeypatch targets are patched where-USED (`wsh._watcher_publish`, `wsh.execute_intent_router_pre_narrator_pass`, the `monster_manual_inject` module object) — correct per the mock-patch-where-used rule.

**Data flow traced:** player action string → `_handle_player_action` → `_execute_narration_turn(sd, action, tc)` → `sd.orchestrator.run_narration_turn(...)` raises `AnthropicSdkLoopExceeded` → caught at `wsh:1078` → `_watcher_publish("narrator.sdk_loop_exhausted", …)` (GM panel) + `logger.warning` + `return [_error_msg(reconnect_required=False, code="narrator_loop_exhausted")]` → returned to `_handle_player_action` → delivered on the **requesting** player's socket (same return path as the existing `_error_msg` at wsh:496 — NOT a broadcast, so no MP perception leak). Session stays bound: no `cleanup()`, no `disconnect_save`. Safe.

**Observations (≥5):**
1. `[VERIFIED]` Session stays alive — evidence: the except `return`s instead of propagating; `cleanup()`/`disconnect_save` (wsh:578) is only reached via the ws_endpoint teardown on an ESCAPED exception, which no longer happens. Complies with ADR-006.
2. `[VERIFIED]` `reconnect_required=False` — evidence: `_error_msg(..., reconnect_required=False)` at wsh:1124; `_error_msg` (session_helpers.py:1400) sets `ErrorPayload.reconnect_required` from the arg. This is the load-bearing session-alive bit and AC-2's no-forced-reconnect requirement.
3. `[VERIFIED]` GM-panel event emitted with a real payload — evidence: wsh:1106-1119 emits `narrator.sdk_loop_exhausted` with genre/world/player_id/action_len/turn/reason/recovery, `component="narrator"`, `severity="warning"`. The *production* observability is correct; only the *test* under-verifies it.
4. `[HIGH][TEST][RULE]` AC-3 fields assertion passes with a placeholder payload — test file:187. The story's observability AC is unverified. **Blocking.**
5. `[LOW][DOC]` "doubles as the wiring test" overclaims — the tests bypass `handle_message → player_action HANDLER`. (Note: `_execute_narration_turn` IS unconditionally on the production narration path via player_action.py:299/901 — so the catch is genuinely reachable; the docstring just overstates the test's scope.)
6. `[VERIFIED]` Narrow catch, no over-reach — evidence: `except AnthropicSdkLoopExceeded` (a leaf exception raised only at anthropic_sdk_client.py:518/676 on max_turns); does not swallow unrelated errors.

### Devil's Advocate
Suppose this code is broken. **Repeated degrade / soft-wedge:** if a subsystem is persistently broken, every turn exhausts and the player gets "try rephrasing" forever — a soft wedge. But that is strictly better than the crash/reconnect loop it replaces, and the player retains agency to try other actions; the root-cause subsystem bug is a separate concern. Not a defect of this fix. **MP leak:** `_error_msg` carries `player_id=""` — could the degrade notice broadcast to every seat, telling the whole table "the engine could not resolve that" when only one player's action exhausted? I traced the return path: it mirrors the existing `_error_msg` return at wsh:496, which goes to the requesting socket, not a broadcast — so no leak. **Lost engine state:** the early return skips persistence, so any pre-narrator dispatch-bank mutation this turn (an engine-first seat/move) is applied in-memory but un-narrated and not saved until a later turn — a possible narration/state desync on the retry. Acceptable for a degrade (don't persist an unresolved turn), but worth a watch. **`_watcher_publish` raising:** if the watcher hub bridge changed to raise, the degrade would itself crash — but `publish_event` is documented fire-and-forget and drops silently with no loop/subscribers, so this holds. **UI:** a non-reconnect ERROR could still be rendered as a fatal toast by a client that treats all ERRORs as fatal (cf. ui #350 `error→clearSession()`); Dev already filed this as a UI-verification finding. **The real hole** the devil finds is the one the subagents found: the AC-3 test would pass even if the watcher payload were `{}`-ish garbage — so a future refactor could silently gut the GM-panel signal and CI would stay green. That is precisely the failure mode this project's OTEL principle exists to prevent, which is why it blocks.

**Handoff:** Back to TEA (Amos Burton) for RED rework — strengthen the four test assertions (lock the AC-3 GM-panel keys + severity, assert the degraded TurnRecord filed, assert no raw-message leak) and fix the overclaiming/stale docstrings + the "reconnect" comment wording. The production code is correct and should not change.

## TEA Rework Assessment (Round 1)

**Reviewer findings addressed — all in the test file (`tests/server/test_158_41_narrator_maxturns_degrade.py`); production code UNCHANGED (it was already correct):**
- **[HIGH] AC-3 fields assertion** — replaced the `isinstance(dict) and fields` truthiness check with a key-lock: `required_keys = {genre_slug, world_slug, player_id, action_len, turn, reason, recovery}; assert required_keys.issubset(fields)`, plus `fields["reason"] == "max_turns_exhausted"` and `fields["recovery"] == "degraded_continue"`. A placeholder payload now FAILS the test.
- **[LOW] AC-3 severity + component** — `_capture` now stores `severity`; the test asserts `event["severity"] == "warning"` and `event["component"] == "narrator"`.
- **[LOW] AC-1 TurnRecord filed** — added `handler._validator.submit.assert_awaited_once()` (proves the degraded `TurnRecord` is filed by the finally, not silently dropped).
- **[LOW] AC-2 raw-message leak** — added `assert "max_turns" not in serialized` (the exception *message* carries `max_turns=8`; only the class name was checked before).
- **[LOW][DOC] overclaim** — the module docstring no longer says "doubles as the wiring test / same entrypoint a live PLAYER_ACTION hits"; it now states the tests drive the real method body (reachable from PLAYER_ACTION via `player_action.py:299`/`:901`) and that they are NOT a full dispatch-chain wiring test.
- **[LOW][DOC] stale "RED today"** — reframed to conditional "without the catch this fails" in AC-1 and AC-3.

**Verification:** strengthened suite is **3/3 GREEN** against the UNCHANGED production code — which itself is the proof the prod genuinely emits all 7 GM-panel keys, the correct reason/recovery, `severity="warning"`, `component="narrator"`, and files the degraded TurnRecord. `ruff check` clean, `ruff format` applied. (Had any strengthened assertion failed, it would have exposed a real prod gap — none did.)

**One Reviewer nit left to Dev (green):** the prod-file comment wording — `[DOC]` "reconnect" precision and the "method-level try has only a finally" phrasing at `websocket_session_handler.py:~1084`. These are PROD comments (outside TEA's tests-only lane) and LOW/cosmetic (the Reviewer agreed the player IS practically forced to reconnect since the socket closes). Optional tidy for Dev during green; not behavior-affecting.

**Handoff:** To Dev (Naomi Nagata) for GREEN re-verification (no prod change required; optional one-line comment tidy).

## Dev Rework Assessment (Round 1)

**Implementation Complete:** Yes (green re-verify + the optional comment tidy)
**Files Changed (this round):**
- `sidequest-server/sidequest/server/websocket_session_handler.py` — **comment-only** tidy of the degrade-block comment per the Reviewer's `[DOC]` nit: clarified that an escaped exception unwinds to `ws_endpoint`'s generic handler, which tears the socket down (`disconnect_save` → room teardown; the player must reconnect to keep playing) — the error frame itself carries `reconnect_required=False`; it's the socket close that wedges the player. Also reworded "method-level try … only a finally" → "only top-level clause is the finally" to disambiguate now that an inner try/except exists. Zero behavior change. (commit `cd831314`)

**Tests:** 3/3 passing (GREEN) — `tests/server/test_158_41_narrator_maxturns_degrade.py`, with TEA's strengthened assertions (locked GM-panel keys + reason/recovery + severity + component, degraded-TurnRecord-filed, raw-message-leak). `ruff check` clean, `ruff format` clean.
**Regression:** the only prod change this round is a comment — behaviorally inert; the earlier A/B baseline (zero new regressions) still holds.
**Branch:** `feat/158-41-narrator-maxturns-graceful-degrade` (pushed; HEAD `cd831314`).

**All Reviewer findings now closed:** [HIGH] AC-3 key-lock (TEA), [LOW] severity/TurnRecord/raw-message asserts (TEA), [LOW][DOC] test docstrings (TEA), [LOW][DOC] prod comment precision (Dev, this round).

**Handoff:** To Reviewer (Chrisjen Avasarala) for re-review.

## Subagent Results (Re-review — Round 2)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 3/3 green, lint/format pass, 0 new smells |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings; domain re-assessed by Reviewer (see [EDGE]) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings; domain re-assessed by Reviewer (see [SILENT]) |
| 4 | reviewer-test-analyzer | Yes | clean | 0 (all 4 prior CLOSED) | confirmed all prior findings closed; no over-coupling; no new vacuous asserts |
| 5 | reviewer-comment-analyzer | Yes | findings | 1 new LOW (3 prior CLOSED) | confirmed 3 closed; 1 new LOW ("live develop red" phrase) → non-blocking, bundled with the tracked monster_manual fix |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings; domain re-assessed by Reviewer (see [TYPE]) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings; domain re-assessed by Reviewer (see [SEC]) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings; domain re-assessed by Reviewer (see [SIMPLE]) |
| 9 | reviewer-rule-checker | Yes | clean | 0 (Rule #6 CLOSED) | confirmed Rule #6 closed; 0 violations across 13 + 3 additional rules |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 1 new LOW (non-blocking); all 6 round-1 findings confirmed CLOSED; 0 blocking

## Reviewer Assessment

**Verdict:** APPROVED

The rework cleanly closed every round-1 finding, confirmed by three independent subagents:
- **[HIGH] AC-3 fields** (the blocker) — now `required_keys.issubset(fields)` over the 7 GM-panel keys + exact `reason`/`recovery`/`severity`/`component` equality. A placeholder payload now FAILS. **rule-checker** confirms Rule #6 closed; **test-analyzer** confirms the assertion is discriminating and not over-coupled. This was the whole reason for the round-1 reject — it is genuinely fixed.
- **[LOW] severity / TurnRecord-filed / raw-message-leak** — all asserted now (`event["severity"]=="warning"`, `_validator.submit.assert_awaited_once()`, `"max_turns" not in serialized`). Confirmed by test-analyzer.
- **[LOW][DOC] overclaim + stale "RED today"** — gone; the new docstring accurately scopes the tests (real method body, reachable from PLAYER_ACTION via `player_action.py:299`/`:901`, NOT a full dispatch-chain wiring test). Confirmed by comment-analyzer with the line numbers verified live.
- **[LOW][DOC] prod comment** — the degrade comment now accurately describes the propagation (escapes to ws_endpoint's generic handler → socket teardown; the error frame carries `reconnect_required=False`, the player must physically reconnect). comment-analyzer cross-checked `websocket.py` and confirmed accuracy.

**One new non-blocking finding** (re-review): the `_bypass_pre_narrator_seams` docstring's "live develop red at `monster_manual_inject.py:184`" is a CI-state phrase that is accurate today but goes stale when that pre-existing fixture rot is fixed. LOW, no rule match, no AC/behavior impact, pre-existing (unflagged) since round 1. Captured as a delivery finding bundled with the already-tracked `monster_manual_inject:184` broken-window — NOT a reason to bounce a correct p1 fix.

**Findings by dispatch tag (all 8 domains):**
- `[TEST]` (ENABLED, test-analyzer): clean — 4 prior findings closed, assertions discriminating, no new vacuous assertions.
- `[RULE]` (ENABLED, rule-checker): clean — prior Rule #6 closed; 0 violations across all 13 python.md + 3 CLAUDE.md rules; the comment-only prod change introduces nothing.
- `[DOC]` (ENABLED, comment-analyzer): 3 prior doc findings closed + accuracy-verified; 1 new LOW (the "live develop red" phrase) — non-blocking, captured.
- `[EDGE]` (DISABLED — re-assessed): the rework added no new control-flow paths (test assertions + a prod comment). The degrade boundary behavior is unchanged from the round-1 [EDGE] assessment (None-safe finally, correct early-return, requesting-socket-only delivery). No new boundary.
- `[SILENT]` (DISABLED — re-assessed): no change to the error path; still a LOUD degrade (watcher event + warning + player message). No silent swallow introduced.
- `[TYPE]` (DISABLED — re-assessed): rework added no new types; the strengthened assertions use plain set/str equality. Clean.
- `[SEC]` (DISABLED — re-assessed): no new input boundary; the player message is a hardcoded literal with no user input interpolated (rule-checker #11 concurs). No PII.
- `[SIMPLE]` (DISABLED — re-assessed): the strengthened assertions are proportionate (lock exactly the GM-panel contract); the prod comment is comment-only. No over-engineering.

### Rule Compliance
Re-enumerated the changed lines against `python.md` (13) + SOUL/CLAUDE additional (No Silent Fallbacks, OTEL, No Source-Text Wiring Tests). **Production file:** compliant on all — narrow `except AnthropicSdkLoopExceeded`, `logger.warning` correct level + lazy `%s` format + no PII, runtime import outside `TYPE_CHECKING`, OTEL watcher event with full payload, no silent fallback; the round-2 change is comment-only. **Test file:** the prior Rule #6 violation is CLOSED (value-level assertions replace the truthiness check); all monkeypatch targets patch where-USED; no source-text wiring tests; three tests cover three distinct ACs. Zero violations.

**Data flow traced (unchanged, re-verified):** player action → `_handle_player_action` → `_execute_narration_turn` → `run_narration_turn` raises `AnthropicSdkLoopExceeded` → caught at wsh:1078 → watcher event + `logger.warning` + `return [_error_msg(reconnect_required=False)]` → delivered on the requesting player's socket (not a broadcast). Session stays bound. Safe.

**Observations (≥5):**
1. `[VERIFIED]` AC-3 now locks the GM-panel contract — evidence: test asserts `required_keys.issubset(fields)` + `reason/recovery/severity/component` equality; rule-checker confirms a placeholder payload fails. The round-1 blocker is closed.
2. `[VERIFIED]` Degraded TurnRecord filed — evidence: `_validator.submit.assert_awaited_once()`; the finally (wsh ~2887) awaits `submit` on the degrade path (submitted stays False). The turn is accounted for, not dropped.
3. `[VERIFIED]` No raw-exception leak — evidence: `"max_turns" not in serialized` + `"anthropicsdkloopexceeded" not in serialized`; the player message is a hardcoded literal.
4. `[VERIFIED]` Prod comment accuracy — evidence: comment-analyzer cross-checked `websocket.py:159` (`except Exception` → `_surface_unexpected` (reconnect_required=False) → finally → `cleanup()`/teardown); the "must reconnect" claim is physical-reconnect, accurate.
5. `[LOW][DOC]` "live develop red" CI-state phrase will go stale post-fix — non-blocking, bundled with the tracked monster_manual broken-window.
6. `[VERIFIED]` No regressions — evidence: preflight 3/3 green + lint/format clean; the round-2 prod change is comment-only; the earlier A/B baseline (zero new regressions) holds.

### Devil's Advocate
Could the rework have made things worse? The strengthened assertions could over-couple and break on a legitimate refactor — but test-analyzer confirmed they assert observable GM-panel semantics (keys + values + severity + component), not code structure; a method rename that preserves the watcher contract passes. Could `assert_awaited_once()` be a false-positive lock — e.g., pass even if the WRONG record were filed? It only proves submit was awaited once, not the record's content; but AC-1's job is "the turn is recorded, not dropped," and the record's degraded shape is the finally's existing, separately-exercised behavior — acceptable scope. Could the new `"max_turns" not in serialized` assertion be brittle if a future legitimate player message happened to contain "max_turns"? Unlikely for a player-facing rephrase notice, and the value is worth more than the risk. The one genuine smell — the "live develop red" phrase — is a forward-looking-staleness comment, not a present inaccuracy; it does not affect any assertion or AC. The hardest question: am I approving a story whose tests still bypass the full PLAYER_ACTION dispatch chain (the original "wiring" concern)? Yes — and that is now HONESTLY documented (the docstring no longer claims otherwise), and `_execute_narration_turn` is unconditionally on the production narration path (player_action.py:299/901), so the catch is genuinely reachable. A full handle_message-driven e2e is a reasonable future hardening, not a blocker for a p1 crash fix. Nothing here rises to Critical/High. APPROVED.

**Handoff:** To SM (Camina Drummer) for finish-story.