---
story_id: "158-48"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 158-48: WWN combat resolution (kill) turn crashes the narrator SDK loop (AnthropicSdkLoopExceeded max_turns=8) — victory NARRATION never persists; client falls back to the opening card (resolution-turn twin of #1086)

## Story Details
- **ID:** 158-48
- **Jira Key:** N/A
- **Type:** bug
- **Points:** 3
- **Priority:** p2
- **Workflow:** tdd
- **Repo:** sidequest-server
- **Branch:** feat/158-48-wwn-kill-turn-narrator-crash
- **Branch Strategy:** gitflow (feat/{STORY_ID}-{SLUG})
- **Stack Parent:** none

## Story Summary

On a WWN combat resolution (kill) turn, the narrator SDK tool loop hits max_turns=8 and raises AnthropicSdkLoopExceeded, so the victory NARRATION is never generated or persisted. This is the resolution-turn twin of #1086 (cold-seat fix). On the resolution turn, in_combat legitimately flips to False the instant the encounter resolves, so the A2 de-nativized WN zone (gated on context.in_combat) does NOT fire on the victory turn. The narrator is therefore never told "the throw already resolved; just narrate it; do NOT call dice/beat tools" — the start-a-confrontation menu fires instead → narrator flails past max_turns → crash → no NARRATION/SCRAPBOOK event for the kill turn.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-28T10:26:06Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-28T09:06:30+00:00 | 2026-06-28T09:08:56Z | 2m 26s |
| red | 2026-06-28T09:08:56Z | 2026-06-28T09:38:12Z | 29m 16s |
| green | 2026-06-28T09:38:12Z | 2026-06-28T10:13:10Z | 34m 58s |
| review | 2026-06-28T10:13:10Z | 2026-06-28T10:26:06Z | 12m 56s |
| finish | 2026-06-28T10:26:06Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->
- No upstream findings at setup.

### TEA (test design)
- **Gap** (blocking): The root cause is NOT the story's stated "A2 zone gated on `context.in_combat`" — verified by code probe. The `[ENCOUNTER RESOLVED]` zone is **dormant in production**: `snapshot.pending_resolution_signal` IS stamped on a WN kill (confirmed — `dispatch/dice.py` `_emit_player_beat_resolution_close` for `player_victory`) but is **never threaded** into `TurnContext.pending_resolution_signal`. The bridge was deleted with the module-level `run_narration_turn` wrapper in story 49-5 and the documented follow-up was never done (see the `pending_resolution_signal` field docstring at `sidequest/agents/orchestrator.py` ~line 909). Affects `sidequest/server/session_helpers.py` (`_build_turn_context` + `refresh_turn_context_post_dispatch` must copy `snapshot.pending_resolution_signal` → `turn_context.pending_resolution_signal`). *Found by TEA during test design.*
- **Gap** (blocking): **One-shot clearing is required and is NOT pinned by a test.** Per the `ResolutionSignal` docstring ("the narrator prompt assembler reads this slot on the next turn and clears it") and the 49-5 follow-up, after the resolution turn consumes the signal it MUST be cleared from `snapshot.pending_resolution_signal`, or the stale signal re-threads every subsequent turn and the `[ENCOUNTER RESOLVED]` zone re-fires forever (violates AC4 "non-resolution beat-commit turns unchanged"). I did NOT write a test because the clearing seam is Dev's choice (49-5 says "clear at the session-handler call site after the orchestrator returns", NOT read-and-clear in `_build_turn_context`); a brittle "call twice" test would wrongly dictate the seam. Dev MUST implement clearing AND add a green-phase regression test (e.g. a two-turn drive: resolution turn fires the zone, the following non-resolution turn does not). Affects the session-handler call site (`websocket_session_handler.py` / `_execute_narration_turn`). *Found by TEA during test design.*
- **Improvement** (non-blocking): The benign `yield_side=None` OTEL warning ("Invalid type NoneType for attribute 'yield_side'") originates in `Span.open` (`sidequest/telemetry/spans/span.py`), which sets `attributes=attrs or {}` VERBATIM with no None filter; `_build_resolution_signal` (and `_resolve_opponent_yield`) pass `yield_side=None` for non-yield outcomes (e.g. player_victory) straight through. Cleanest centralized fix: drop None-valued keys in `Span.open`. Story flagged it "worth a glance while in here." Affects `sidequest/telemetry/spans/span.py` (or the resolution-signal call sites). *Found by TEA during test design.*
- **Question** (non-blocking): AC2 ("victory NARRATION + SCRAPBOOK_ENTRY persists to the events log on the resolution turn") is covered by MECHANISM, not by a direct persistence assertion — the RED tests pin the threading + de-nativized directive that let the narrator converge, and persistence then flows through the existing path. A full persistence proof needs the handler + a fake-narrator-returning-NARRATION drive (integration weight). Dev/Reviewer should confirm an integration or green-phase test asserts the durable NARRATION row on the resolution turn. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): **Pre-existing develop test-debt surfaced by the broad green-phase sweep** (NOT caused by this story — proven by `git stash`-comparing the test-only RED commit: identical failure counts with and without the green source changes). In `tests/telemetry tests/agents tests/server` (`-n0`): 5734 passed / **51 failed** / 1125 skipped. The 51 break down as: (a) ~41 `tests/server/test_turn_record_wiring.py`-class failures — the `session_fixture` MagicMock pack's `effective_bestiary` returns a non-unpackable mock, crashing per-turn monster_manual injection (`monster_manual_inject.py:184`); (b) `tests/server/test_arc_embedding_*` (13 in isolation — arc-embedding seed spans not firing); (c) `tests/agents/test_orchestrator.py::test_run_narration_turn_emits_leak_audit_span_with_zero_leaks`; (d) `tests/server/test_snapshot_field_governance.py::test_every_snapshot_field_is_categorized` (`husk_reaped_this_turn` GameSnapshot field uncategorized); (e) `tests/server/test_space_opera_melee_e2e.py::test_melee_def_is_combat_hp_depletion_with_distinct_beats`. Affects those test files / fixtures (separate cleanup story). The dev-exit gate's full-suite run will show these — they are NOT regressions from 158-48. *Found by Dev during implementation.*
- **Improvement** (non-blocking): `tests/server/conftest.py::session_fixture` should pin `genre_pack.effective_bestiary` to a real empty return (the same real-defaults pattern it already applies to `progression`/`drama_thresholds`/`rules`) so the full `_execute_narration_turn` path is drivable; fixing it would un-break the ~41 turn-path tests above. Out of scope here (shared fixture, broad ripple); worked around locally in the clearing tests with `MagicMock(return_value=(None, "genre"))`. Affects `tests/server/conftest.py`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): Use direct attribute access `sig.encounter_type` / `sig.outcome` in `_thread_resolution_signal` instead of `getattr(sig, "...", None)`. The defaults are dead code (`sig` is always a `ResolutionSignal` inside the guard) and emitting null telemetry on a wrong-type signal is a (production-unreachable) soft violation of No-Silent-Fallbacks; direct access fails loud and matches `orchestrator.py:2261`. Affects `sidequest/server/session_helpers.py:697-698`. *Found by Reviewer during code review.* [SILENT, LOW]
- **Improvement** (non-blocking): `Span.open`'s global None-attribute filter removes the OTEL "Invalid type NoneType" diagnostic for ALL callers, not just the intentional `yield_side=None` case — an accidental upstream None now vanishes silently. Behavior-preserving (OTEL already dropped None) so LOW, but consider preserving the canary (debug-log dropped keys under a dev flag) or narrowing the fix to the resolution-signal call sites. Affects `sidequest/telemetry/spans/span.py:38`. *Found by Reviewer during code review.* [SILENT, LOW]

## Impact Summary

**Upstream Effects:** 1 findings (1 Gap, 0 Conflict, 0 Question, 0 Improvement)
**Blocking:** 1 BLOCKING items — see below

**BLOCKING:**
- **Gap:** The root cause is NOT the story's stated "A2 zone gated on `context.in_combat`" — verified by code probe. The `[ENCOUNTER RESOLVED]` zone is **dormant in production**: `snapshot.pending_resolution_signal` IS stamped on a WN kill (confirmed — `dispatch/dice.py` `_emit_player_beat_resolution_close` for `player_victory`) but is **never threaded** into `TurnContext.pending_resolution_signal`. The bridge was deleted with the module-level `run_narration_turn` wrapper in story 49-5 and the documented follow-up was never done (see the `pending_resolution_signal` field docstring at `sidequest/agents/orchestrator.py` ~line 909). Affects `sidequest/server/session_helpers.py`.


### Downstream Effects

- **`sidequest/server`** — 1 finding

### Deviation Justifications

5 deviations

- **Tests pin the dormant-signal bridge, not the story's stated `in_combat` gate**
  - Rationale: A code probe proved the signal is already stamped on the WN kill and already gates the de-nativized resolution zone + start-menu suppression — it simply never reaches the context (dormant since 49-5). Threading the existing signal is the minimal, genre-agnostic fix ("Don't Reinvent — Wire Up What Exists") and matches the documented 49-5 follow-up; inventing a parallel `encounter_resolved_this_turn` gate would duplicate the existing resolution-signal machinery.
  - Severity: minor (behaviour identical to the AC intent; the field/seam differs from the literal wording)
  - Forward impact: Dev implements the threading at both seams + one-shot clearing; the existing `pending_resolution_signal` consumer in `orchestrator.py` is unchanged.
- **One-shot clearing left untested (test omission)**
  - Rationale: The clearing seam is Dev's choice (handler call-site per 49-5, not `_build_turn_context`); any test I could write at the threading seam would dictate read-and-clear and be brittle/wrong. Dev owns the clearing regression test in green.
  - Severity: minor (companion behaviour, flagged blocking for Dev)
  - Forward impact: Dev MUST add clearing + its regression test or non-resolution turns re-fire the zone.
- **`yield_side=None` OTEL warning left untested (test omission)**
  - Rationale: Not an AC; a clean behavioral assertion can't be written without dictating the fix seam (centralized `Span.open` None-filter vs call-site coercion), and OTEL silently drops the None (warning only, no crash).
  - Severity: trivial
  - Forward impact: none (cosmetic log noise); Dev may fix opportunistically.
- **Fixed the `yield_side=None` warning centrally in `Span.open` (beyond the 4 ACs)**
  - Rationale: TEA left it untested/non-blocking, but the story explicitly asked for a glance and server CLAUDE.md says "fix it right." The centralized fix is provably safe (OTEL already rejects None attrs, so the key was never recorded — filtering only removes the warning, zero behavior change) and benefits all spans; falsy-but-valid values (0/False) are preserved (filter keys on `is None`).
  - Severity: minor (scope addition beyond the 4 ACs, but directly story-flagged and tested)
  - Forward impact: none — purely removes log noise across all span call sites.
- **One-shot clear placed in `_execute_narration_turn`'s `finally`, tested via the `session_fixture` harness**
  - Rationale: Honors the 49-5 "clear at the handler" guidance (not read-and-clear at the seam, which would break the dual-seam threading and lose the signal on retry). The clearing tests required working around the pre-existing broken `session_fixture` (see Delivery Findings) with `effective_bestiary=MagicMock(return_value=(None, "genre"))`.
  - Severity: minor (test-harness workaround for a pre-existing broken fixture)
  - Forward impact: none — local to the two clearing tests; the shared fixture is flagged for a separate fix.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Tests pin the dormant-signal bridge, not the story's stated `in_combat` gate**
  - Spec source: context-story-158-48.md, "PROPOSED FIX" + AC1/AC3
  - Spec text: "fire the A2 de-nativized WN zone on encounter_resolved_this_turn (the turn that resolves the encounter), not only when context.in_combat"
  - Implementation: Tests assert `_build_turn_context` / `refresh_turn_context_post_dispatch` thread `snapshot.pending_resolution_signal` → `TurnContext.pending_resolution_signal` (reviving the dormant `[ENCOUNTER RESOLVED]` zone), rather than adding a new `encounter_resolved_this_turn` flag onto the A2 `in_combat` gate.
  - Rationale: A code probe proved the signal is already stamped on the WN kill and already gates the de-nativized resolution zone + start-menu suppression — it simply never reaches the context (dormant since 49-5). Threading the existing signal is the minimal, genre-agnostic fix ("Don't Reinvent — Wire Up What Exists") and matches the documented 49-5 follow-up; inventing a parallel `encounter_resolved_this_turn` gate would duplicate the existing resolution-signal machinery.
  - Severity: minor (behaviour identical to the AC intent; the field/seam differs from the literal wording)
  - Forward impact: Dev implements the threading at both seams + one-shot clearing; the existing `pending_resolution_signal` consumer in `orchestrator.py` is unchanged.
- **One-shot clearing left untested (test omission)**
  - Spec source: AC4 + `ResolutionSignal` docstring
  - Spec text: "The cold-seat turn (#1086) and non-resolution beat-commit turns are unchanged" / "reads this slot on the next turn and clears it"
  - Implementation: No test pins that the consumed signal is cleared; captured as a BLOCKING Delivery Finding instead.
  - Rationale: The clearing seam is Dev's choice (handler call-site per 49-5, not `_build_turn_context`); any test I could write at the threading seam would dictate read-and-clear and be brittle/wrong. Dev owns the clearing regression test in green.
  - Severity: minor (companion behaviour, flagged blocking for Dev)
  - Forward impact: Dev MUST add clearing + its regression test or non-resolution turns re-fire the zone.
- **`yield_side=None` OTEL warning left untested (test omission)**
  - Spec source: context-story-158-48.md, "ALSO seen ... likely benign, worth a glance"
  - Spec text: "OTEL attribute error 'Invalid type NoneType for attribute yield_side'"
  - Implementation: No test; captured as a non-blocking Delivery Finding.
  - Rationale: Not an AC; a clean behavioral assertion can't be written without dictating the fix seam (centralized `Span.open` None-filter vs call-site coercion), and OTEL silently drops the None (warning only, no crash).
  - Severity: trivial
  - Forward impact: none (cosmetic log noise); Dev may fix opportunistically.

### Dev (implementation)
- **Fixed the `yield_side=None` warning centrally in `Span.open` (beyond the 4 ACs)**
  - Spec source: context-story-158-48.md, "ALSO seen ... likely benign, worth a glance" + TEA finding (non-blocking)
  - Spec text: "OTEL attribute error 'Invalid type NoneType for attribute yield_side'"
  - Implementation: Added a None-valued-attribute filter in `Span.open` (`sidequest/telemetry/spans/span.py`) + a unit test (`tests/telemetry/test_span_none_attr_filter.py`), rather than coercing at the resolution-signal call sites or leaving it.
  - Rationale: TEA left it untested/non-blocking, but the story explicitly asked for a glance and server CLAUDE.md says "fix it right." The centralized fix is provably safe (OTEL already rejects None attrs, so the key was never recorded — filtering only removes the warning, zero behavior change) and benefits all spans; falsy-but-valid values (0/False) are preserved (filter keys on `is None`).
  - Severity: minor (scope addition beyond the 4 ACs, but directly story-flagged and tested)
  - Forward impact: none — purely removes log noise across all span call sites.
- **One-shot clear placed in `_execute_narration_turn`'s `finally`, tested via the `session_fixture` harness**
  - Spec source: TEA finding (blocking) + `ResolutionSignal` docstring + 49-5 follow-up
  - Spec text: "clear it at the session-handler call site after the orchestrator returns"
  - Implementation: Clear `snapshot.pending_resolution_signal = None` in the `try/finally` around the `run_narration_turn` call (runs on success AND the `AnthropicSdkLoopExceeded` degrade path; before `state_apply`). Tested both paths by driving the real `_execute_narration_turn` (mirroring `test_turn_record_wiring.py`), verified non-vacuous by neutering the clear and confirming RED.
  - Rationale: Honors the 49-5 "clear at the handler" guidance (not read-and-clear at the seam, which would break the dual-seam threading and lose the signal on retry). The clearing tests required working around the pre-existing broken `session_fixture` (see Delivery Findings) with `effective_bestiary=MagicMock(return_value=(None, "genre"))`.
  - Severity: minor (test-harness workaround for a pre-existing broken fixture)
  - Forward impact: none — local to the two clearing tests; the shared fixture is flagged for a separate fix.

### Reviewer (audit)
- **TEA: tests pin the dormant-signal bridge, not the stated `in_combat` gate** → ✓ ACCEPTED by Reviewer: the code probe was correct — the signal was already stamped + already gates the de-nativized zone; threading the existing field is the minimal genre-agnostic fix (No-Reinvent) and matches the documented 49-5 follow-up. Inventing a parallel `encounter_resolved_this_turn` gate would have duplicated machinery.
- **TEA: one-shot clearing left untested (deferred to Dev)** → ✓ ACCEPTED by Reviewer: TEA correctly avoided dictating the clearing seam; Dev implemented it at the handler `finally` (per 49-5) and added both success + degrade tests, verified non-vacuous. The deferral resolved cleanly.
- **TEA: `yield_side=None` warning left untested** → ✓ ACCEPTED by Reviewer: a non-AC benign warning; reasonable to defer the test decision to Dev.
- **Dev: fixed `yield_side=None` centrally in `Span.open` (beyond the 4 ACs)** → ✓ ACCEPTED by Reviewer (with a noted caveat): the centralized None-filter is behavior-preserving (OTEL already rejects None attrs) and benefits all spans. The silent-failure-hunter's concern that it globally removes a diagnostic warning is valid but LOW (the warning was a noisy canary firing on intentional None); logged as a non-blocking fast-follow rather than a reversal.
- **Dev: one-shot clear in `_execute_narration_turn` `finally` + `session_fixture` workaround** → ✓ ACCEPTED by Reviewer: the handler-`finally` placement is correct (ordering vs `state_apply` verified); the local `effective_bestiary=(None, "genre")` workaround is appropriate given the pre-existing broken shared fixture (separately flagged).

## Sm Assessment

**Story setup complete; handing off to tea (red phase).**

- **Workflow:** tdd (phased) → red (tea) → green (dev) → review (reviewer) → finish (sm).
- **Repo:** sidequest-server only. Branch `feat/158-48-wwn-kill-turn-narrator-crash` off main (gitflow; this repo has no develop branch, main is the integration base).
- **Jira:** explicitly skipped — Jira is not configured in this environment (`pf jira` refuses to contact Jira). No JIRA_KEY, no claim/transition steps.

**Why this is well-scoped for tdd:** This is a confirmed, single-repo bug with a precise root cause and a sibling fix to mirror (#1086 / commit a6dc7535, the cold-seat twin). The failure is deterministic in mechanism (resolution-turn `in_combat` flips False before the A2 de-nativized WN zone gate is evaluated), so a red test can assert the zone fires on `encounter_resolved_this_turn` and that the kill turn persists NARRATION without exceeding max_turns. ADR-143 ("bind don't balance") governs the direction of the fix — de-nativize, don't re-balance native beats.

**Guidance for tea (red phase):**
- Write a failing test proving the A2 de-nativized WN zone fires on a resolution/kill turn (`encounter_resolved_this_turn`), not only when `context.in_combat` is True. Target sits around orchestrator.py ~2226.
- Assert the kill turn persists a NARRATION/SCRAPBOOK event and does NOT raise AnthropicSdkLoopExceeded (max_turns=8).
- Assert the resolution-turn OTEL span is emitted (twin of `cold_seat_context_refreshed`) — the GM-panel lie-detector per the OTEL Observability Principle.
- Out of scope but note while in here: the benign OTEL attribute error "Invalid type NoneType for attribute 'yield_side'" — worth a glance, not the focus.
- Do NOT pursue the board's rejected ADR-051 round/seq-collapse hypothesis; root cause is the SDK loop crash, not the turn counter.

**No upstream findings at setup.**

## TEA Assessment

**Tests Required:** Yes
**Status:** RED (6 failing, ready for Dev) — verified by `testing-runner` (RUN_ID 158-48-tea-red): 6 fail / 18 pass, every failure is an unimplemented-feature assertion (no import/collection errors).

**Root cause (corrected from the story narrative, via code probe):** The story blamed "the A2 zone gated on `context.in_combat`." The actual, code-documented root cause is that the `[ENCOUNTER RESOLVED]` zone is **dormant in production**: `snapshot.pending_resolution_signal` is stamped on a WN kill (`dispatch/dice.py` `_emit_player_beat_resolution_close`, player_victory — confirmed by probe) but is never threaded into `TurnContext.pending_resolution_signal` (the bridge died with the 49-5 `run_narration_turn` wrapper deletion; see the field docstring at `orchestrator.py` ~909). So the field is None every turn → the resolution zone never renders AND the start-a-confrontation menu (gated on `pending_resolution_signal is None`) always fires → the narrator flails past max_turns → no victory NARRATION. Fix = revive the dormant bridge (thread the signal at both context-build seams) + emit the OTEL twin + clear it after consumption. This is the direct analogue of story 81-3 (`pacing_hint`), the same declared-and-consumed-but-never-populated TurnContext pattern.

**Test Files:**
- `tests/server/test_resolution_signal_turn_context_wiring.py` (NEW, 4 tests) — the DICE-path `_build_turn_context` seam (the kill-turn scenario). Threads the signal; emits the `resolution_context_refreshed` GM-panel watcher event; end-to-end `build_narrator_prompt` renders `[ENCOUNTER RESOLVED]` + "Do NOT emit beat_selections" and drops "AVAILABLE ENCOUNTER TYPES"; no-false-positive guard. Mirrors `test_pacing_hint_turn_context_wiring.py`.
- `tests/agents/test_wwn_combat_denativization.py` (+4 tests) — the `refresh_turn_context_post_dispatch` seam (AC3's literal "real refresh"; free-nav resolution path). Threads the signal; emits the watcher twin; refresh + `build_narrator_prompt` wiring fires the de-nativized resolution zone + drops the start-menu; no-false-positive guard. Mirrors the #1086 cold-seat `_FakeRefreshSessionData` tests.

**Tests Written:** 8 (6 RED + 2 no-false-positive guards). 16 pre-existing cold-seat / A1 / A2 / A3 tests remain green (AC4: #1086 cold-seat path unchanged).

**AC coverage:**
- AC1 (resolution turn fires de-nativized directive, converges, no AnthropicSdkLoopExceeded): the two end-to-end wiring tests pin the directive + start-menu suppression (the mechanism that lets the narrator converge). LLM convergence itself is not unit-testable; the directive is the lever.
- AC2 (victory NARRATION persists): covered by MECHANISM (threading + directive → narrator converges → existing persistence path runs). Flagged as a Question finding — a direct durable-row assertion needs handler/integration weight; recommended for Dev/green or integration.
- AC3 (OTEL twin span + wiring drives real refresh + build_narrator_prompt): fully covered — watcher-event tests at both seams + both wiring tests.
- AC4 (cold-seat + non-resolution turns unchanged): the 16 existing cold-seat tests stay green + two no-false-positive guards (no signal → context None, no watcher event). One-shot clearing (the other half of AC4) is a BLOCKING Delivery Finding for Dev (seam is Dev's choice; can't pin without dictating it).

### Rule Coverage (`.pennyfarthing/gates/lang-review/python.md`)

| Rule | Test(s) / Disposition | Status |
|------|-----------------------|--------|
| #4 Logging/OTEL coverage | `test_build_turn_context_emits_resolution_turn_watcher_event`, `test_refresh_resolution_turn_emits_gm_panel_watcher_event` — assert the GM-panel `resolution_context_refreshed` event fires (lie-detector) | failing (RED) |
| #6 Test quality | Self-checked all 8 — every test has a meaningful assertion on a concrete value (signal object/outcome, exact event op + component, prompt substrings); no `assert True`, no truthy-only checks, no assertion-free tests; `monkeypatch` targets `watcher_hub.publish_event` (where it is imported+called, not where defined) | pass |
| #1 Silent exceptions / #3 type annotations / #9 async pitfalls | Dev source-shape checks (not behavioral RED surfaces for this fix). The async path is exercised by the two `@pytest.mark.asyncio` `build_narrator_prompt` wiring tests; threading must not swallow — covered by the no-false-positive guards (a thread error would surface). | n/a (Dev self-review) |

**Rules checked:** 2 of 13 lang-review rules have direct test coverage (#4, #6); the rest are Dev source-shape self-review checks not applicable to RED behavioral tests for this fix.
**Self-check:** 0 vacuous tests (verified — the e2e prompt assertions were empirically confirmed to flip GREEN when the signal is threaded, so no test stays RED after the obvious fix).

**Handoff:** To Dev (Ponder Stibbons) for GREEN — implement the signal threading at both seams, the `resolution_context_refreshed` OTEL twin, AND the one-shot clearing (+ its regression test). Glance at the `yield_side=None` warning.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (sidequest-server):**
- `sidequest/server/session_helpers.py` — new `_thread_resolution_signal(turn_context, snapshot)` helper (threads `snapshot.pending_resolution_signal` → `TurnContext.pending_resolution_signal` + emits the `resolution_context_refreshed` GM-panel watcher event, twin of `cold_seat_context_refreshed`); called by BOTH `_build_turn_context` (dice-path seam) and `refresh_turn_context_post_dispatch` (free-nav seam) so they cannot drift. This revives the dormant `[ENCOUNTER RESOLVED]` zone — the root cause.
- `sidequest/server/websocket_session_handler.py` — `_execute_narration_turn` clears `snapshot.pending_resolution_signal` in a `try/finally` after the orchestrator call (one-shot; fires on success AND the `AnthropicSdkLoopExceeded` degrade path; before `state_apply`, which may stamp a fresh signal for the next turn). Completes the 49-5 follow-up.
- `sidequest/telemetry/spans/span.py` — `Span.open` filters None-valued attributes (the benign `yield_side=None` OTEL warning the story flagged).
- Tests: `tests/server/test_resolution_signal_turn_context_wiring.py` (+2 one-shot-clearing tests), `tests/telemetry/test_span_none_attr_filter.py` (new), `tests/agents/test_wwn_combat_denativization.py` (the 4 TEA RED tests now green, unchanged).

**Tests:** Story-specific suites GREEN — `test_resolution_signal_turn_context_wiring.py` (6) + `test_wwn_combat_denativization.py` (20) + `test_span_none_attr_filter.py` (2) = **28 passing**. The 6 TEA RED tests now pass; the 16 pre-existing cold-seat/A1/A2/A3 tests stay green (AC4). pyright clean on all 3 changed source files (the 28 handler errors are pre-existing, unchanged). ruff clean.

**AC status:**
- AC1 (resolution turn fires de-nativized directive; converges, no AnthropicSdkLoopExceeded): GREEN — both e2e wiring tests prove the `[ENCOUNTER RESOLVED]` directive renders + the start-menu is suppressed (the mechanism that lets the narrator converge).
- AC2 (victory NARRATION persists): mechanism in place (narrator now gets the right directive → converges → existing persistence path runs); direct durable-row assertion deferred to integration per the TEA finding.
- AC3 (OTEL twin + wiring): GREEN — `resolution_context_refreshed` event at both seams + both `build_narrator_prompt` wiring tests.
- AC4 (cold-seat + non-resolution turns unchanged): GREEN — 16 cold-seat tests still pass + the no-false-positive guards + the one-shot clearing (tested on success AND degrade) ensure a non-resolution turn does not re-fire the zone.

**Regression triage:** A broad sweep (`tests/telemetry tests/agents tests/server`) showed 51 failures; ALL are pre-existing develop test-debt (proven by `git stash`-comparing the test-only RED commit — identical counts with/without the green source changes). Itemized in the Delivery Findings. No regressions from 158-48.

**Branch:** `feat/158-48-wwn-kill-turn-narrator-crash` (pushed to origin).

**Handoff:** To Reviewer (Granny Weatherwax) for review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (28/28 story tests green, ruff clean, 0 new pyright, 0 actionable smells) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings (`workflow.reviewer_subagents.edge_hunter=false`); boundary paths assessed by reviewer |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 | confirmed 2 (both LOW severity), dismissed 0, deferred 0 |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings; test quality assessed by reviewer (wiring tests present, non-vacuous) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings; comments assessed by reviewer (docstrings accurate, no stale refs) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings; types assessed by reviewer (helper fully annotated) |
| 7 | reviewer-security | Yes | clean | none | N/A — MP race + PII + deserialization all explicitly cleared |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings; complexity assessed by reviewer (minimal, shared-helper DRY) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings; lang-review rules enumerated by reviewer (see Rule Compliance) |

**All received:** Yes (3 enabled returned; 6 disabled via settings)
**Total findings:** 2 confirmed (both LOW, non-blocking), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

The core fix is correct and minimal: it revives the dormant `[ENCOUNTER RESOLVED]` zone by threading the pre-existing shared-snapshot `pending_resolution_signal` into the narrator `TurnContext` at both context-build seams, clears it one-shot after consumption, and (opportunistically) silences the flagged `yield_side=None` OTEL warning. All 6 RED tests now pass; the #1086 cold-seat suite is unchanged. The two silent-failure findings are real but LOW-severity (one production-unreachable, one behavior-preserving) — neither meets the Critical/High blocking bar. Logged as non-blocking fast-follows.

**Data flow traced:** `dispatch_dice_throw` resolves a WN kill → `_emit_player_beat_resolution_close` stamps `snapshot.pending_resolution_signal` (a server-side `ResolutionSignal`) → `_thread_resolution_signal` copies it into `TurnContext.pending_resolution_signal` (dice path: in `_build_turn_context`; free-nav path: in `refresh_turn_context_post_dispatch`) → `build_narrator_prompt` renders the `[ENCOUNTER RESOLVED]` de-nativized directive + suppresses the start-menu → orchestrator consumes → `_execute_narration_turn` `finally` clears the snapshot field. No player input flows into this path; the signal is server-stamped mechanical state (safe).

**Observations:**
- `[VERIFIED]` Both seams thread via ONE shared helper `_thread_resolution_signal` — `session_helpers.py:661` — so the pre/post-dispatch context cannot drift (mirrors the #1086 `_project_encounter_fields` shared-helper pattern). Evidence: called at `session_helpers.py:773` (refresh) and `:1427` (build). Complies with No-Reinvent / DRY.
- `[VERIFIED]` One-shot clear ordering is correct — `websocket_session_handler.py:1130-1141` `finally` runs after the orchestrator consumes the context copy and BEFORE `state_apply` (~1181), which may stamp a fresh signal for the next turn. Confirmed by silent-failure-hunter (Q2) and the two clearing tests (success + degrade), which were verified non-vacuous by neutering the clear → RED.
- `[VERIFIED]` `Span.open` None-filter preserves falsy-but-valid values (`0`/`False`/`""`) — `span.py:38` keys on `is None`, not truthiness; `test_span_none_attr_filter.py` pins `kept_int=0` and `kept_false=False` survive. Behavior-preserving: OTEL already dropped None attrs (this only removes the warning).
- `[SEC]` `[VERIFIED]` No MP cross-seat leak — `pending_resolution_signal` is a PRE-EXISTING shared-snapshot field (`session.py:1102`, present on develop), not introduced here. The elected-dispatcher CAS in `dispatch_fired_barrier` (player_action.py:221-228, per reviewer-security) guarantees exactly one handler reaches `_execute_narration_turn` per interaction counter; the signal is read→consumed→cleared within that single handler. No PII in the `resolution_context_refreshed` event (encounter_type/outcome only). `ResolutionSignal` is pydantic `extra="forbid"`, server-constructed, never deserialized from WS input.
- `[TEST]` `[VERIFIED]` (test-analyzer disabled — assessed by reviewer) Both threading seams have explicit wiring tests: dice/pre-dispatch seam in `test_resolution_signal_turn_context_wiring.py` (real `_build_turn_context` → real `build_narrator_prompt`), free-nav/post-dispatch seam in `test_wwn_combat_denativization.py` (real `refresh_turn_context_post_dispatch` → real `build_narrator_prompt`). No vacuous assertions; concrete checks on signal object, exact OTEL op+component, and prompt substrings. Satisfies CLAUDE.md "Every Test Suite Needs a Wiring Test."
- `[SILENT]` `[LOW]` `getattr(sig, "encounter_type", None)` / `getattr(sig, "outcome", None)` at `session_helpers.py:697-698` — the defaults are dead code (inside `if sig is not None`, `sig` is always a `ResolutionSignal` with required fields; the real error fires loud at `orchestrator.py:2261`). Production-unreachable, but direct `sig.encounter_type` access would be doctrine-aligned (No Silent Fallbacks — never silently emit null telemetry) and consistent with the orchestrator's own access. Confirmed, non-blocking, logged as a fast-follow.
- `[SILENT]` `[LOW]` `Span.open` None-filter (`span.py:38`) globally suppresses the OTEL "Invalid type NoneType" warning for ALL callers — for an accidental upstream None (vs. the intentional `yield_side=None`) the dev loses a diagnostic. Behavior-preserving (OTEL dropped None anyway) and the warning was a noisy canary (fired on intentional None), so severity is LOW — but the diagnostic-fidelity tradeoff is real. Confirmed, non-blocking; logged a fast-follow recommendation (debug-log dropped keys, or narrow to the resolution-signal call sites).
- `[EDGE]`/`[TYPE]`/`[DOC]`/`[SIMPLE]`/`[RULE]` (subagents disabled — assessed by reviewer): no boundary, type, comment, complexity, or rule issues found in the diff. The helper is fully annotated; docstrings are accurate; the deferred `publish_event` import matches the existing telemetry-in-helpers circular-guard pattern.

### Rule Compliance (`.pennyfarthing/gates/lang-review/python.md`)

| Rule | Instances checked | Verdict |
|------|-------------------|---------|
| #1 Silent exception swallowing | `_thread_resolution_signal`, the `finally` clear, `Span.open` filter | compliant — no try/except added; the `finally` is unconditional (not a swallow); the two getattr/filter items are LOW silent-default findings above, not exception swallowing |
| #2 Mutable default args | `_thread_resolution_signal` (no defaults) | compliant |
| #3 Type annotations at boundaries | `_thread_resolution_signal(turn_context: TurnContext, snapshot: GameSnapshot) -> None` | compliant — fully annotated |
| #4 Logging/OTEL coverage | new `resolution_context_refreshed` watcher event | compliant (adds GM-panel observability per the OTEL principle) |
| #6 Test quality | all 3 test files | compliant — concrete assertions, wiring tests, non-vacuous (verified) |
| #9 Async pitfalls | the `finally` in async `_execute_narration_turn` | compliant — sync assignment, no blocking call, no missing await |
| #10 Import hygiene | deferred `from sidequest.telemetry.watcher_hub import publish_event` | compliant — matches existing same-file cold-seat circular-guard pattern |
| #5/#7/#8/#11/#12 | — | N/A (no path/resource/deser/input-boundary/dependency surface in the diff) |
| #13 Fix-introduced regressions | broad sweep | compliant — 51 failures all pre-existing develop debt (stash-compare verified), 0 new |

### Devil's Advocate

Suppose this code is broken. The most dangerous claim is the one-shot clear: what if it wipes a signal that should have survived? Walk the adversarial paths. (a) A non-AnthropicSdkLoopExceeded exception escapes `run_narration_turn` — the `finally` still clears, then the exception propagates to the method-level degraded-record finally. The victory narration is lost AND the signal is gone, so the next turn won't retry it. But that's an unexpected-crash edge; leaving the signal armed would instead re-narrate "the fight is over" on top of an unrelated next action (worse). The clear-always semantics is the lesser evil and matches the one-shot contract. (b) Could `state_apply` stamp a signal that the SAME turn's already-run `finally` wipes? No — `finally` runs before `state_apply`, so a freshly-stamped signal survives to the next turn (the documented ordering). (c) MP: could two seats' turns interleave and one clear the other's signal? The reviewer-security CAS analysis says no — one elected handler per interaction counter. (d) The narrator is told "do NOT emit beat_selections" on the resolution turn but the A1 tool filter (`exclude_combat_resolution`) keys on `is_live_wn_combat`, which is False for a resolved encounter — so on the resolution turn the narrator gets its combat tools BACK. Could it still flail? No: the `[ENCOUNTER RESOLVED]` zone short-circuits the prompt to "narrate the close," and there's no live encounter to drive beats against; this is the same converged state the dial/yield resolution path has used since 49-5's design. (e) A confused author emits a None span attribute expecting it to surface — now it silently vanishes. Real, but LOW (logged as a fast-follow). (f) Huge/empty inputs: the signal carries bounded mechanical strings; no unbounded growth. Conclusion: no correctness break found; the two LOW findings stand as fast-follows.

**Handoff:** To SM (Captain Carrot) for finish-story.