---
story_id: "153-6"
jira_key: ""
epic: "153"
workflow: "tdd"
---
# Story 153-6: [SWN-DOGFIGHT-UNREACHABLE] wire ADR-077 dogfight to IntentRouter dispatch

## Story Details
- **ID:** 153-6
- **Jira Key:** (none — Jira not configured)
- **Workflow:** tdd
- **Stack Parent:** none
- **Repo:** server

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-22T06:52:53Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-22T06:09:46+00:00 | 2026-06-22T06:09:46+00:00 | - |
| red | 2026-06-22T06:09:46+00:00 | 2026-06-22T06:29:30Z | 19m 44s |
| green | 2026-06-22T06:29:30Z | 2026-06-22T06:40:26Z | 10m 56s |
| review | 2026-06-22T06:40:26Z | 2026-06-22T06:52:53Z | 12m 27s |
| finish | 2026-06-22T06:52:53Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)

- **Improvement** (non-blocking): The dogfight handler must REUSE `instantiate_encounter_from_trigger(encounter_type="dogfight", …)` — the same seating primitive `run_confrontation_dispatch` already calls — rather than reinventing encounter seating (Don't Reinvent; SOUL "Crunch in the Genre"). A dogfight is simply a `ConfrontationDef` with `resolution_mode: sealed_letter_lookup`; the engine, the red/blue role tagging, frame_hp seeding, and `encounter.confrontation_initiated` span all already exist. Affects `sidequest/agents/subsystems/dogfight.py` (new handler should be a thin wrapper: resolve the dogfight type → materialize the `opponent` as the Other (ADR-116, like `confrontation.py`) → call the existing primitive → emit `dogfight.dispatch`; on `NoOpponentAvailableError`/seat failure emit `dogfight.dispatch.rejected` and return an error-coded `SubsystemOutput`). *Found by TEA during test design.*

- **Question** (non-blocking): How should the handler choose the dogfight `ConfrontationDef` when a pack has BOTH `dogfight` (sealed_letter_lookup, ADR-077) AND `ship_combat` (beat_selection, hp_depletion)? The swn_test_pack ships both. The tests pass `params["type"]="dogfight"` AND tolerate the handler resolving by `resolution_mode == sealed_letter_lookup` — either design passes. Dev/Architect should pick one deliberately (recommend: the subsystem owns the ADR-077 dogfight type so the router need not disambiguate). Affects `sidequest/agents/subsystems/dogfight.py` + the `intent_router.py` prompt. *Found by TEA during test design.*

- **Gap** (non-blocking): `intent_router_pass.TIME_ADVANCING_SUBSYSTEMS` is `{movement, confrontation}` — a `dogfight` dispatch will NOT tick the survival/environment clock. This is almost certainly correct (dogfights happen in space, not torch-lit dungeons), so it is explicitly OUT OF SCOPE for 153-6 and NOT tested — flagged only so the omission is a recorded decision, not an oversight. Affects `sidequest/server/intent_router_pass.py` (no change expected). *Found by TEA during test design.*

- **Gap** (non-blocking): `detect_improvised_combat` stands down only when the router dispatched `confrontation` (`_package_dispatched_confrontation`). A `dogfight` dispatch that seats an encounter is already covered (the "no live encounter" gate makes it stand down), so no change is required for the seated path — but if Dev wants belt-and-suspenders symmetry with the new subsystem, consider including `dogfight` in that stand-down check. Not tested (the seated-path gate already protects it). Affects `sidequest/agents/dispatch_engagement_watcher.py`. *Found by TEA during test design.*

### Dev (implementation)

- **Question** (non-blocking, RESOLVED): TEA asked how the handler picks the dogfight `ConfrontationDef` when a pack carries BOTH `dogfight` (`sealed_letter_lookup`) and `ship_combat` (`beat_selection`). Resolved in `_resolve_dogfight_type`: scan `pack.rules.confrontations` for `resolution_mode == ResolutionMode.sealed_letter_lookup and category == "combat"` (the ADR-077 dogfight), consulted only when `params["type"]` is absent. The subsystem owns the type so the router need only name the ship-combat intent + opponent. Affects `sidequest/agents/subsystems/dogfight.py`. *Found by Dev during implementation.*
- TEA's `detect_improvised_combat` symmetry suggestion was assessed and NOT taken: a seated dogfight already trips the "live encounter" stand-down, so the seated path is covered; adding `dogfight` to `_package_dispatched_confrontation` would be untested dead weight (minimalist discipline). Left for a future story if a dogfight-dispatch-but-no-seat + injury-prose case ever surfaces. *Found by Dev during implementation.*
- No other upstream findings during implementation.

### Reviewer (code review)

- **Improvement** (non-blocking): The handler honors `params["type"]` verbatim (`dispatch.params.get("type") or _resolve_dogfight_type(pack)`) without validating it names a `sealed_letter_lookup` type. Today this is safe — the `intent_router.py` prompt does NOT instruct the router to emit `type`, so production always takes the `_resolve_dogfight_type` discovery path. But if a future router edit (or another caller) ever emits `dogfight` with `type="ship_combat"` (the pack's `beat_selection` ship type), the handler would seat a non-dogfight encounter and still emit `dogfight.dispatch`. Affects `sidequest/agents/subsystems/dogfight.py` (consider validating the resolved type is `sealed_letter_lookup`, or drop the `params["type"]` honor since the router doesn't pass it). *Found by Reviewer during code review.*
- **Gap** (non-blocking): Test coverage gaps surfaced by `reviewer-test-analyzer` — none are code defects, the branches are exercised by inspection + sibling parity: (a) the `no_dogfight_type` rejection branch (a pack with no sealed-letter combat def) is untested; (b) the bare-string `opponent` materialization branch is untested (tests use only the dict form); (c) a dogfight dispatch against an already-active different-type encounter is untested. Affects `tests/agents/subsystems/test_dogfight_dispatch_wiring.py` (add these cases in a follow-up; the loud-reject AC-5 behavior IS covered via the no-opponent path). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `subsystems/__init__.py` module docstring carried a pre-existing stale count ("All eight subsystems") — the registry held 13 before this story (course/quest_offer/equip/environment_clock/fate_action were added without updating the prose). Reviewer de-numberized the claim and added the `dogfight` bullet, but the prose still omits those 5 prior additions. Affects `sidequest/agents/subsystems/__init__.py` (a future cleanup could restore the full prose list or generate it from `_register_defaults`). *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 4 findings (2 Gap, 0 Conflict, 0 Question, 2 Improvement)
**Blocking:** None

- **Gap:** `intent_router_pass.TIME_ADVANCING_SUBSYSTEMS` is `{movement, confrontation}` — a `dogfight` dispatch will NOT tick the survival/environment clock. This is almost certainly correct (dogfights happen in space, not torch-lit dungeons), so it is explicitly OUT OF SCOPE for 153-6 and NOT tested — flagged only so the omission is a recorded decision, not an oversight. Affects `sidequest/server/intent_router_pass.py`.
- **Improvement:** The handler honors `params["type"]` verbatim (`dispatch.params.get("type") or _resolve_dogfight_type(pack)`) without validating it names a `sealed_letter_lookup` type. Today this is safe — the `intent_router.py` prompt does NOT instruct the router to emit `type`, so production always takes the `_resolve_dogfight_type` discovery path. But if a future router edit (or another caller) ever emits `dogfight` with `type="ship_combat"` (the pack's `beat_selection` ship type), the handler would seat a non-dogfight encounter and still emit `dogfight.dispatch`. Affects `sidequest/agents/subsystems/dogfight.py`.
- **Gap:** Test coverage gaps surfaced by `reviewer-test-analyzer` — none are code defects, the branches are exercised by inspection + sibling parity: (a) the `no_dogfight_type` rejection branch (a pack with no sealed-letter combat def) is untested; (b) the bare-string `opponent` materialization branch is untested (tests use only the dict form); (c) a dogfight dispatch against an already-active different-type encounter is untested. Affects `tests/agents/subsystems/test_dogfight_dispatch_wiring.py`.
- **Improvement:** `subsystems/__init__.py` module docstring carried a pre-existing stale count ("All eight subsystems") — the registry held 13 before this story (course/quest_offer/equip/environment_clock/fate_action were added without updating the prose). Reviewer de-numberized the claim and added the `dogfight` bullet, but the prose still omits those 5 prior additions. Affects `sidequest/agents/subsystems/__init__.py`.

### Downstream Effects

Cross-module impact: 4 findings across 3 modules

- **`sidequest/agents/subsystems`** — 2 findings
- **`sidequest/server`** — 1 finding
- **`tests/agents/subsystems`** — 1 finding

### Deviation Justifications

3 deviations

- **AC-1 "in_conflict=True" asserted as a live dogfight StructuredEncounter, not a literal `in_conflict` field**
  - Rationale: `in_conflict` is a **Fate-only** concept (`server/dispatch/fate_conflict.py`, `fate_state_emit.py`); the ADR-077 dogfight is a `StructuredEncounter` whose live-state is `encounter` set + unresolved. Asserting a literal `in_conflict` field on a dogfight would test a field that does not exist on this code path. The dogfight-correct equivalent carries the same meaning ("a live ship-combat conflict is active").
  - Severity: minor
  - Forward impact: none — the behavioral intent (a real, live dogfight is seated) is fully covered.
- **Router-PROMPT classification (the `intent_router.py` registration naming `dogfight` as a dispatch key) is NOT unit-tested; the router is stubbed**
  - Rationale: exact 153-5 sibling precedent (`test_course_clock_dispatch_wiring.py` stubs the router and never asserts prompt text). A live LLM classification test is flaky and content-coupled (project lore `feedback_no_content_coupled_tests`); asserting the prompt string would be a forbidden source-text wiring test (CLAUDE.md "No Source-Text Wiring Tests"). "Real IntentRouter path" is satisfied by the real pre-pass + bank with a stubbed classifier — the same shape the sibling shipped. The prompt edit is verified by playtest.
  - Severity: minor
  - Forward impact: Dev MUST add the `dogfight` dispatch key (params: `opponent`, optional `type`) to the `intent_router.py` system prompt — see Delivery Findings. The pre-pass test catches the registration/reachability half; the classification half is a playtest gate, not a unit gate.
- **Dispatch span names fixed to `dogfight.dispatch` (accepted) + `dogfight.dispatch.rejected` (loud fail)**
  - Rationale: AC-2 grants "(or equivalent)"; this names the equivalent explicitly and mirrors the 153-5 `course.plot` / `course.plot.rejected` pair. A dedicated dispatch-level span is required anyway because the rejected path never reaches the engine's seating span, so AC-5's loud failure needs its own span.
  - Severity: minor
  - Forward impact: Dev adds two spans (+ `SPAN_ROUTES` entries) in `telemetry/spans/dogfight.py`.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)

- **AC-1 "in_conflict=True" asserted as a live dogfight StructuredEncounter, not a literal `in_conflict` field**
  - Spec source: context-story-153-6.md, AC-1
  - Spec text: "starts a structured dogfight encounter (encounter_events > 0, dogfight seated, in_conflict=True)"
  - Implementation: tests assert `snapshot.encounter is not None`, `encounter_type == "dogfight"`, `not encounter.resolved`, and the sealed-letter red+blue pairing — NOT a literal `in_conflict` attribute.
  - Rationale: `in_conflict` is a **Fate-only** concept (`server/dispatch/fate_conflict.py`, `fate_state_emit.py`); the ADR-077 dogfight is a `StructuredEncounter` whose live-state is `encounter` set + unresolved. Asserting a literal `in_conflict` field on a dogfight would test a field that does not exist on this code path. The dogfight-correct equivalent carries the same meaning ("a live ship-combat conflict is active").
  - Severity: minor
  - Forward impact: none — the behavioral intent (a real, live dogfight is seated) is fully covered.

- **Router-PROMPT classification (the `intent_router.py` registration naming `dogfight` as a dispatch key) is NOT unit-tested; the router is stubbed**
  - Spec source: context-story-153-6.md, Fix Direction §2 + AC-3
  - Spec text: "Register the subsystem in `agents/intent_router.py` so a matching intent routes…" / "A test drives a natural-language ship-combat intent through the real IntentRouter path"
  - Implementation: every test injects the router's classification deterministically (a constructed `SubsystemDispatch(subsystem="dogfight", …)`) and drives the REAL bank / REAL `execute_intent_router_pre_narrator_pass`. The Haiku `decompose` call is stubbed; no test asserts the system-prompt text contains "dogfight".
  - Rationale: exact 153-5 sibling precedent (`test_course_clock_dispatch_wiring.py` stubs the router and never asserts prompt text). A live LLM classification test is flaky and content-coupled (project lore `feedback_no_content_coupled_tests`); asserting the prompt string would be a forbidden source-text wiring test (CLAUDE.md "No Source-Text Wiring Tests"). "Real IntentRouter path" is satisfied by the real pre-pass + bank with a stubbed classifier — the same shape the sibling shipped. The prompt edit is verified by playtest.
  - Severity: minor
  - Forward impact: Dev MUST add the `dogfight` dispatch key (params: `opponent`, optional `type`) to the `intent_router.py` system prompt — see Delivery Findings. The pre-pass test catches the registration/reachability half; the classification half is a playtest gate, not a unit gate.

- **Dispatch span names fixed to `dogfight.dispatch` (accepted) + `dogfight.dispatch.rejected` (loud fail)**
  - Spec source: context-story-153-6.md, AC-2 + AC-5
  - Spec text: AC-2 "emits a `dogfight.dispatch` (or equivalent) watcher span"; AC-5 "fails loudly (logged event with reason)"
  - Implementation: tests assert a `dogfight.dispatch` span on success and a `dogfight.dispatch.rejected` span on an un-seatable dispatch — a handler-level pair distinct from the engine's `encounter.confrontation_initiated` (seating) and `dogfight.confrontation_started` (which fires later, at sealed-letter RESOLUTION, not at seating).
  - Rationale: AC-2 grants "(or equivalent)"; this names the equivalent explicitly and mirrors the 153-5 `course.plot` / `course.plot.rejected` pair. A dedicated dispatch-level span is required anyway because the rejected path never reaches the engine's seating span, so AC-5's loud failure needs its own span.
  - Severity: minor
  - Forward impact: Dev adds two spans (+ `SPAN_ROUTES` entries) in `telemetry/spans/dogfight.py`.

### Dev (implementation)

- No deviations from spec. All 5 Dev-Contract items implemented as TEA specified: the handler reuses `instantiate_encounter_from_trigger` (Don't Reinvent); `dogfight.dispatch` + `dogfight.dispatch.rejected` spans with `SPAN_ROUTES`; witness in `_WITNESSES` + `_DISPATCHED_TYPE_KEY` (key `"type"`); the `dogfight` dispatch key in the router prompt. The optional-`type` discovery fallback (`_resolve_dogfight_type`) is the implementation of TEA Deviation #2's forward-impact ("params: opponent, optional type"), not a new deviation.

### Reviewer (audit)

- **TEA Dev-1 (AC-1 "in_conflict=True" → live dogfight StructuredEncounter)** → ✓ ACCEPTED by Reviewer: verified `in_conflict` is a Fate-only field (`fate_conflict.py`, `fate_state_emit.py`); the dogfight is a `StructuredEncounter` whose live-state is `encounter` set + `not resolved`. The tests assert the dogfight-correct equivalent. Sound.
- **TEA Dev-2 (router-prompt classification not unit-tested; router stubbed)** → ✓ ACCEPTED by Reviewer: exact 153-5 precedent; a prompt-text assertion would be a forbidden source-text wiring test (CLAUDE.md). The prompt key IS added (`intent_router.py`), and the pre-pass test proves registration/reachability through the real bank. Live Haiku classification is correctly a playtest gate.
- **TEA Dev-3 (dispatch span names `dogfight.dispatch` / `dogfight.dispatch.rejected`)** → ✓ ACCEPTED by Reviewer: mirrors the 153-5 `course.plot` / `course.plot.rejected` handler-level pair; AC-2 grants "(or equivalent)". The rejected span is genuinely required — the loud-fail path never reaches the engine's `encounter.confrontation_initiated` seating span.
- **Dev (implementation) "No deviations from spec"** → ✓ ACCEPTED by Reviewer: confirmed — the implementation matches the TEA Dev-Contract item-for-item; `_resolve_dogfight_type` is the implementation of TEA Dev-2's "optional type", not a new deviation.
- **No UNDOCUMENTED deviations found.** The implementation faithfully tracks the story context, the AC set, and the TEA contract. (The latent `params["type"]` trust note is recorded as a non-blocking Delivery Finding, not a spec deviation — the TEA contract explicitly permitted honoring `params["type"]`.)

## TEA Assessment

**Tests Required:** Yes
**Reason:** 5-pt wiring bug; behavioral ACs (encounter seated, OTEL spans, watcher witness, loud reject) demand failing tests through the real dispatch path before Dev implements.

**Test Files:**
- `tests/agents/subsystems/test_dogfight_dispatch_wiring.py` — RED wiring tests for the new `dogfight` IntentRouter subsystem (mirrors the 153-5 `course` sibling, `test_course_clock_dispatch_wiring.py`).

**Tests Written:** 9 tests covering 5 ACs.
**Status:** RED (verified — `7 failed, 2 passed`, collection clean, no import/fixture errors).

### AC → Test Map

| AC | Test(s) | Status |
|----|---------|--------|
| AC-1 ship-combat seats a dogfight | `test_dogfight_intent_through_bank_seats_dogfight` (encounter_type=="dogfight", live, red+blue), `test_pre_pass_seats_dogfight_through_real_pass` | failing (right-reason) |
| AC-2 `dogfight.dispatch` watcher span | `test_dogfight_intent_through_bank_seats_dogfight`, `test_pre_pass_seats_dogfight_through_real_pass` | failing |
| AC-3 integration via REAL IntentRouter path | `test_dogfight_intent_through_bank_seats_dogfight` (real bank), `test_pre_pass_seats_dogfight_through_real_pass` (real pre-pass, router stubbed), `test_dogfight_handler_is_registered`, `test_dogfight_witness_registered` | failing |
| AC-4 orbital-course sibling not regressed | `test_dogfight_registration_does_not_displace_course_sibling` + the existing `test_course_clock_dispatch_wiring.py` staying green | failing (dogfight half) |
| AC-5 no silent fallback (loud reject) | `test_dogfight_no_opponent_rejects_loud` (`dogfight.dispatch.rejected` span, no phantom encounter) | failing |
| lie-detector witness (AC-2/AC-3 support) | `test_watcher_flags_dogfight_dispatch_that_did_not_seat`, `test_watcher_silent_when_dogfight_seated` | flags=failing / silent=passing |

### Rule Coverage

| Rule (python lang-review) | Test(s) | Status |
|---------------------------|---------|--------|
| #1 No silent exception swallowing / No Silent Fallbacks | `test_dogfight_no_opponent_rejects_loud` (un-seatable dogfight emits a loud `dogfight.dispatch.rejected` span, never a silent narrator handback) | failing |
| #6 Test quality (meaningful assertions, no vacuous) | self-check below | pass |

**Rules checked:** 2 of 8 python lang-review rules are test-relevant from the test side (the rest — mutable defaults, type annotations at boundaries, logging level correctness, path handling, resource leaks, unsafe deserialization — are Dev-side implementation checks for the new handler/spans, surfaced for the green/verify pass).
**Self-check:** 0 vacuous tests. Every test carries a meaningful assertion with a failure message. Two tests PASS in RED by design (not vacuously): `test_low_confidence_dogfight_degrades_and_does_not_engage` (the confidence gate is subsystem-agnostic and fires before the registry lookup — it correctly degrades a low-confidence dogfight today and must keep doing so post-GREEN) and `test_watcher_silent_when_dogfight_seated` (the inverse guard — must not false-flag a genuinely-seated dogfight). Both match the 153-5 sibling's RED profile exactly and remain meaningful regression guards after GREEN.

### Dev Contract (what GREEN must land)

1. `sidequest/agents/subsystems/dogfight.py` → `run_dogfight_dispatch(dispatch, *, snapshot, pack, player_name, npcs_present=None, additional_player_names=None)`. Thin wrapper over `instantiate_encounter_from_trigger(encounter_type="dogfight", …)` (Don't Reinvent — see Delivery Findings). Materialize `params["opponent"]` as the Other (ADR-116) exactly as `confrontation.py` does. Emit `dogfight.dispatch` on success; on `NoOpponentAvailableError`/seat failure emit `dogfight.dispatch.rejected` (reason) and return `SubsystemOutput(data={"error": …})`.
2. Register `"dogfight" → run_dogfight_dispatch` in `subsystems/__init__.py:_register_defaults()`.
3. Add `SPAN_DOGFIGHT_DISPATCH = "dogfight.dispatch"` + `SPAN_DOGFIGHT_DISPATCH_REJECTED = "dogfight.dispatch.rejected"` (with `SPAN_ROUTES` + context-manager emitters) in `telemetry/spans/dogfight.py`.
4. Add `dogfight` to `dispatch_engagement_watcher._WITNESSES` (a `_check_dogfight_engaged` that flags when no live `dogfight` encounter seated) AND `_DISPATCHED_TYPE_KEY` (key `"type"`).
5. Add the `dogfight` dispatch key (params: `opponent` `{name, description}`, optional `type`) to the `intent_router.py` system prompt so ship-combat prose routes here — **validated by playtest, not unit test** (see Deviation #2).

**Handoff:** To Dev (Naomi Nagata) for GREEN implementation.
## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/agents/subsystems/dogfight.py` (NEW) — `run_dogfight_dispatch`: resolves the ADR-077 sealed-letter dogfight type, materializes `params["opponent"]` as the Other (ADR-116), seats via the shared `instantiate_encounter_from_trigger` primitive (Don't Reinvent), emits `dogfight.dispatch` on a verified seat / `dogfight.dispatch.rejected` (with reason) on no-Other / no-type / not-seated.
- `sidequest/agents/subsystems/__init__.py` — registered `dogfight → run_dogfight_dispatch` in `_register_defaults()`.
- `sidequest/telemetry/spans/dogfight.py` — `dogfight.dispatch` + `dogfight.dispatch.rejected` spans (constants, `SPAN_ROUTES`, context-manager emitters).
- `sidequest/agents/dispatch_engagement_watcher.py` — `_check_dogfight_engaged` witness + `_WITNESSES` + `_DISPATCHED_TYPE_KEY["dogfight"]="type"`.
- `sidequest/agents/intent_router.py` — `dogfight` dispatch key in the system prompt (ship-vs-ship → dogfight w/ required opponent; personal combat stays `confrontation`).

**Tests:** 9/9 passing (GREEN) on `tests/agents/subsystems/test_dogfight_dispatch_wiring.py`. Regression net 85/85 (course sibling, confrontation dispatch, confidence gate, dogfight engine wiring + smoke + shot, intent_router + wiring). `ruff check` clean, `ruff format` clean, `pyright` 0 errors on all changed source files.

**Branch:** `feat/153-6-swn-dogfight-unreachable-wire-intentrouter` (pushed to origin).

**AC status:** AC-1 (ship-combat seats a live dogfight) ✓; AC-2 (`dogfight.dispatch` watcher span) ✓; AC-3 (integration via real bank + real pre-pass, router stubbed) ✓; AC-4 (course sibling not regressed — green) ✓; AC-5 (loud `dogfight.dispatch.rejected`, no silent fallback) ✓. Router-prompt classification is the one playtest-gated piece (see TEA Deviation #2) — the prompt key is added; live Haiku classification of ship-combat prose is verified at playtest, not unit-tested.

**Handoff:** To Reviewer (Chrisjen Avasarala) for code review.
## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean (green) | 3 obs | dismissed 3 (all non-defects) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — assessed by Reviewer |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — assessed by Reviewer + rule-checker #1 |
| 4 | reviewer-test-analyzer | Yes | findings | 6 | confirmed 3 (non-blocking gaps→deferred), dismissed 2, informational 1 |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 | confirmed 3 → FIXED inline (doc-only) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — assessed by Reviewer (pyright 0 errors) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings — assessed by Reviewer + rule-checker #11 |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — assessed by Reviewer |
| 9 | reviewer-rule-checker | Yes | findings | 1 | confirmed 1 (LOW, helper-exempt — informational) |

**All received:** Yes (4 enabled returned; 5 disabled via settings, their domains assessed by Reviewer directly)
**Total findings:** 3 confirmed-and-fixed (stale docstrings), 4 confirmed-non-blocking (deferred to Delivery Findings), 5 dismissed (with rationale), 1 informational

### Rule Compliance (python lang-review + project rules)

Exhaustive enumeration (corroborated by reviewer-rule-checker: 13 rules / 47 instances / 0 blocking violations):

- **#1 No silent exception swallowing / No Silent Fallbacks (SOUL/CLAUDE.md):** `run_dogfight_dispatch` has THREE explicit loud-fail branches — `no_dogfight_type` (dogfight.py guard), the `except (NoOpponentAvailableError, SealedLetterArityError)` catch (specific types, `logger.warning` + `dogfight.dispatch.rejected` span + error-coded `SubsystemOutput`), and the post-seat `not_seated` verification. No bare except, no pass-only swallow, no silent narrator hand-back. COMPLIANT (every instance).
- **#2 Mutable default args:** `npcs_present=None`, `additional_player_names=None` (None-sentinel, `list(npcs_present) if npcs_present else []`). `_dogfight_dispatch(opponent=None)`. COMPLIANT (all 4 instances).
- **#3 Type annotations at boundaries:** `run_dogfight_dispatch`, `_resolve_dogfight_type`, `_check_dogfight_engaged`, both span context managers — all fully annotated. Pyright 0 errors. One LOW: `_load_pack()` test helper lacks a return annotation — but the rule EXEMPTS private (underscore) helpers, so non-blocking. COMPLIANT (boundary functions); LOW-exempt (1 private test helper).
- **#4 Logging coverage AND correctness:** all 3 rejection logs use `logger.warning` (correct level — subsystem engagement gaps are not 5xx) with `%s` lazy-format args, not f-strings. COMPLIANT (all 3 instances).
- **#5 Path handling:** no file I/O / paths in the diff. N/A.
- **#6 Test quality:** all 9 tests carry specific behavioral assertions (registry key + `__name__`; engaged decision + span + real encounter state + seating span; gated decision; rejected span + absent accepted span + null encounter; witness membership; mismatch presence/absence; real-pre-pass seating; sibling-not-displaced). No `assert True`, no assertion-free tests, no unexplained skips. COMPLIANT.
- **#7 Resource leaks:** all spans are `@contextmanager` `with` blocks (closed on exit). No file/db/lock handles. COMPLIANT.
- **#8 Unsafe deserialization:** no pickle/yaml.load/eval/exec. N/A.
- **OTEL Observability Principle (CLAUDE.md):** every dispatch decision emits a span — `dogfight.dispatch` (engaged) / `dogfight.dispatch.rejected` (every fail path, with reason). The GM-panel lie-detector can verify the engine engaged vs the narrator improvising. COMPLIANT.
- **Don't Reinvent (SOUL/CLAUDE.md):** the handler reuses `instantiate_encounter_from_trigger` (the shared seating primitive `confrontation` uses) rather than reimplementing seating. COMPLIANT.
- **No Source-Text Wiring Tests (CLAUDE.md):** wiring is proven via the real `run_dispatch_bank` / real `execute_intent_router_pre_narrator_pass` + OTEL spans + the registry — never a `read_text()` grep. COMPLIANT.

### Devil's Advocate

Argue this code is broken. **(1) The router never actually emits `dogfight`.** The whole feature hinges on a system-prompt edit that is NOT unit-tested. If Haiku keeps classifying "weapons hot, engage" as `confrontation` (it already had a `confrontation` path with a `ship_combat`/`threat` alias from story 59-23), the dogfight subsystem is dead code in production and the playtest finding recurs. **Rebuttal:** this is real and is exactly why TEA Deviation #2 + the Dev contract flag the prompt as a playtest gate; the prompt block explicitly steers ship-vs-ship → `dogfight` and personal combat → `confrontation`, and the distinction is concrete (vehicle/contact vs corridor brawl). It cannot be unit-proven without a content-coupled LLM test (forbidden). Accepted as a playtest follow-up, not a code defect. **(2) A confused router emits `dogfight` with `type="ship_combat"`.** The handler would seat a `beat_selection` ship_combat and emit `dogfight.dispatch` — a wrong-engine seat. **Rebuttal:** the prompt doesn't ask for `type`, so production discovers the sealed-letter type; the risk is latent and recorded as a non-blocking Improvement. **(3) A stressed turn: the player engages a contact mid-other-encounter.** `instantiate_encounter_from_trigger` returns None (active encounter exists); the handler's `seated.encounter_type != enc_type` check then rejects loud rather than silently overwriting — correct, no corruption. **(4) Malicious/garbage opponent name** (huge string, injection chars): the name only becomes an `NpcMention` (pydantic) and an OTEL attribute string — no SQL/shell/eval surface; prompt-injection is handled upstream (ADR-047). **(5) Empty params entirely:** no type→discovery→ (swn pack has dogfight) seats with no opponent→ NoOpponentAvailableError→ loud reject. No crash. The honest residual risk is #1 (classification), which is correctly a playtest gate. Nothing here is a blocking defect.

## Reviewer Assessment

**Verdict:** APPROVED

**Confirmed findings by source:**
- `[DOC]` (comment-analyzer, 3× HIGH-confidence, LOW-severity) — stale docstring counts: dogfight span count (5→8), engagement-witness count (ten/153-5→eleven/153-6), subsystems registry count ("eight"→all-registered). **FIXED inline** by Reviewer (doc-only, no logic touched; 2 introduced by this diff, 1 pre-existing worsened-by-one). Re-verified: ruff clean, 9/9 tests still green.
- `[TEST]` (test-analyzer, MEDIUM/LOW) — coverage gaps (no_dogfight_type branch, bare-string opponent, active-encounter edge); not defects (branches exercised by inspection + sibling parity). Deferred to Delivery Findings (non-blocking).
- `[RULE]` (rule-checker, LOW) — `_load_pack()` test helper missing return annotation; rule exempts private helpers. Informational, non-blocking.
- `[EDGE]` (disabled — Reviewer-assessed): mid-encounter dispatch → loud `not_seated` reject (no overwrite); empty params → discovery → loud no-opponent reject. No unhandled path.
- `[SILENT]` (disabled — Reviewer-assessed + rule-checker #1): no swallowed errors; all 3 fail paths log warning + emit a rejected span + return error-coded output. Verified `_required_str_param` returns `None` (not raises) on a missing key, so the witness's production no-`type` path is correct.
- `[TYPE]` (disabled — Reviewer-assessed): pyright 0 errors; `threat_name` coerced to `str`; all boundary functions annotated.
- `[SEC]` (disabled — Reviewer-assessed + rule-checker #11): no auth/tenant/secret/deserialization surface; opponent name flows only into a pydantic `NpcMention` + an OTEL attribute string. Clean.
- `[SIMPLE]` (disabled — Reviewer-assessed): handler mirrors `confrontation.py`; ~100 lines, no dead code, no over-engineering. The 3 repeated rejected-span blocks carry distinct reasons — extraction would be marginal.

**Data flow traced:** player ship-combat utterance → IntentRouter.decompose (Haiku) → `SubsystemDispatch(subsystem="dogfight", params={opponent})` → `execute_intent_router_pre_narrator_pass` → unregistered-gate (dogfight registered, survives) → precondition-gate (no dogfight precondition, survives) → confidence-gate (≥0.6 engages) → `run_dogfight_dispatch` → `_resolve_dogfight_type` → materialize opponent (ADR-116) → `instantiate_encounter_from_trigger(encounter_type="dogfight")` → `snapshot.encounter` set → verified live → `dogfight.dispatch` span → narrator sees a real dogfight. Post-turn: `dispatch_engagement_watcher` `dogfight` witness confirms engagement. Safe end-to-end; fully wired (registry + pre-pass + prompt + spans + witness), not half-wired.

**Pattern observed:** thin-wrapper-over-shared-primitive — `run_dogfight_dispatch` mirrors `run_confrontation_dispatch` (`sidequest/agents/subsystems/dogfight.py` ↔ `confrontation.py`), reusing `instantiate_encounter_from_trigger`. Correct application of Don't Reinvent.

**Error handling:** three explicit loud-fail branches with reason-carrying `dogfight.dispatch.rejected` spans (`sidequest/agents/subsystems/dogfight.py`) — no silent fallback, satisfies AC-5.

**AC verification:** AC-1 ✓ (live dogfight seated, red+blue), AC-2 ✓ (`dogfight.dispatch` span), AC-3 ✓ (real bank + real pre-pass), AC-4 ✓ (course sibling green; both registered), AC-5 ✓ (loud reject). AC-3's live-LLM-classification half is correctly a playtest gate.

**Handoff:** To SM (Camina Drummer) for finish-story.