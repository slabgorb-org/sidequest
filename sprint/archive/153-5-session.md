---
story_id: "153-5"
jira_key: ""
epic: "153"
workflow: "tdd"
---
# Story 153-5: [SWN-ORBITAL-COURSE-INERT] wire ADR-130 course/clock to the IntentRouter subsystem bank

## Story Details
- **ID:** 153-5
- **Jira Key:** (none — no Jira integration)
- **Workflow:** tdd
- **Stack Parent:** none
- **Type:** bug
- **Points:** 5
- **Priority:** p3
- **Repos:** server

## Story Summary

ADR-130's orbital story-time clock and course model exists in the server but is INERT in actual play — the course/clock subsystem is not registered/reachable through the IntentRouter mechanical-engagement subsystem bank (ADR-113/123), so a player engaging orbital navigation in the SWN space_opera trio (aureate_span / coyote_star / perseus_cloud) never triggers the course/clock resolver; the narrator improvises instead.

**Root-cause direction:** Verify the ADR-130 course/clock code exists and wire it into the IntentRouter dispatch bank with confidence gating + OTEL spans so the GM panel can verify it engages.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-21T19:09:29Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-21T18:22:45Z | 2026-06-21T18:25:02Z | 2m 17s |
| red | 2026-06-21T18:25:02Z | 2026-06-21T18:47:27Z | 22m 25s |
| green | 2026-06-21T18:47:27Z | 2026-06-21T18:59:23Z | 11m 56s |
| review | 2026-06-21T18:59:23Z | 2026-06-21T19:09:29Z | 10m 6s |
| finish | 2026-06-21T19:09:29Z | - | - |

## SM Assessment

**Routing:** Phased TDD workflow → next phase is RED, owned by TEA (Fezzik). Single repo: server. No Jira. Branch `feat/153-5-swn-orbital-course-inert-wire-adr130-intentrouter` cut from `develop`.

**Nature of the work — integration, not reimplementation.** This is a playtest finding: ADR-130's orbital story-time clock + course model already exists in the server; it is simply *inert* because it is not registered in the IntentRouter mechanical-engagement subsystem bank (ADR-113/123). Per the project's "Don't Reinvent — Wire Up What Exists" and "Verify Wiring" principles, the deliverable is the dispatch registration + confidence gate, not a new resolver. TEA's first move should be to *locate the existing ADR-130 code* and write a wiring test that proves the course/clock resolver is reachable from the IntentRouter dispatch path against the real SWN space_opera pack — not a synthetic fixture (see the opposed-check wiring trap in prior playtest learnings: dispatch-only wiring can no-op in real play).

**OTEL is mandatory.** Per CLAUDE.md's OTEL Observability Principle, the wiring is only "done" when the course/clock subsystem emits watcher spans the GM panel can read — that is the lie detector that distinguishes a real resolver firing from narrator improvisation. RED must include a span-assertion test; do not accept narration prose as evidence the subsystem engaged.

**Judgment checks:**
- [x] Jira claimed — N/A (no Jira integration; `jira_key: ""`)
- [x] Story context written — `sprint/context/context-story-153-5.md` exists with root-cause direction and ACs
- [x] Session created, branch cut from correct base (`develop`), story `in_progress`

**Open question for TEA/Dev (non-blocking):** confirm whether ADR-130 course/clock advancement is beat-driven (story-time clock) vs. player-intent-driven — the IntentRouter gate must trigger on the right signal so a player articulating an orbital course change actually reaches the resolver.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Behavioral wiring story — a subsystem must become reachable end-to-end; this is exactly "Every Test Suite Needs a Wiring Test" territory.

**Test File:**
- `sidequest-server/tests/agents/subsystems/test_course_clock_dispatch_wiring.py` — 9 tests (7 RED, 2 documented green-at-RED guards) for the new `course` subsystem.

**RED state:** `7 failed, 2 passed` (run scoped to the new file, `-n0`). Confirmed each failure is a real assertion/contract failure reaching past the fixtures — NOT a collection/import error:
- `test_course_handler_is_registered` — RED: `"course"` not in `get_registered()`.
- `test_course_intent_through_bank_plots_and_advances_clock` — RED: bank decision `unknown_subsystem` (engine never engaged); fixtures (`load_orbital_content`, `compute_eta_and_dv`, `run_dispatch_bank`) all work — the eta-sanity assert passed and decisions were recorded.
- `test_course_unknown_destination_rejects_loud` — RED: no `course.plot.rejected` span.
- `test_course_witness_registered` — RED: `"course"` not in `_WITNESSES`.
- `test_watcher_flags_course_dispatch_that_did_not_plot` — RED: watcher ignores unknown subsystem → no mismatch.
- `test_pre_pass_accepts_orbital_content_param` — RED: pre-pass has no `orbital_content` param.
- `test_pre_pass_threads_orbital_content_to_course_handler` — RED: `TypeError` (kwarg absent).

**The 2 green-at-RED are intentional guards (not vacuous-by-mistake), documented inline:**
- `test_low_confidence_course_degrades_and_does_not_engage` — green at RED because the bank's confidence gate (`run_dispatch_bank` line 340) fires BEFORE the registry lookup (line 359), so a low-confidence dispatch degrades regardless of registration. It asserts real behavior (no spans, clock unmoved, `must_narrate` hint, decision `degraded_to_hint`) and must stay green post-GREEN — a regression guard that the gate applies to `course`.
- `test_watcher_silent_when_course_committed` — paired inverse of the RED `test_watcher_flags...`; vacuous at RED (subsystem ignored), meaningful post-GREEN (the witness must NOT false-flag a committed course).

**The contract this RED pins for Dev (Inigo):**
- New `sidequest/agents/subsystems/course.py::run_course_dispatch`, registered as `"course"` in `_register_defaults`.
- A high-confidence `course` dispatch (`params={"destination": "<body_id>"}`) engages BOTH halves of ADR-130 in one dispatch: the **course model** (`compute_eta_and_dv` → `course.plot` span + committed `PlottedCourse`/arrival) AND the **clock model** (TRAVEL `StoryBeat`, `duration_hours == eta_hours` → `clock.advance` span + `snapshot.clock_t_hours += eta`). Reuse the existing pure resolvers — Don't Reinvent.
- Confidence-gated (ADR-113), loud-rejects an unknown destination (`course.plot.rejected` — No Silent Fallbacks), watcher witness in `_WITNESSES` **and** `_DISPATCHED_TYPE_KEY` (a missing `_DISPATCHED_TYPE_KEY['course']` will KeyError the detector).
- `execute_intent_router_pre_narrator_pass` gains an `orbital_content` param and threads it into the bank `context` dict (`intent_router_pass.py:951`); the caller `websocket_session_handler.py:984` passes `session.orbital_content`. Dev must also add the `course` subsystem key + `params` doc to the IntentRouter `_SYSTEM_PROMPT` (`intent_router.py:145-282`) so the live router can emit it — not asserted by a source grep (forbidden), but required for real-play engagement and verifiable in the post-merge playtest.

### Rule Coverage

| Rule / Principle | Test(s) | Status |
|------------------|---------|--------|
| Every Test Suite Needs a Wiring Test (CLAUDE.md) | `test_course_intent_through_bank_plots_and_advances_clock`, `test_pre_pass_threads_orbital_content_to_course_handler` | failing (RED) |
| No Source-Text Wiring Tests (CLAUDE.md) | all — registry / behavioral / OTEL-span / reflection-signature only | satisfied |
| No Silent Fallbacks (loud unknown-destination) | `test_course_unknown_destination_rejects_loud` | failing (RED) |
| OTEL Observability Principle (lie-detector) | `course.plot` / `clock.advance` / `course.plot.rejected` span asserts; `test_course_witness_registered`, `test_watcher_flags...` | failing (RED) |
| ADR-113 confidence gate applies to the new subsystem | `test_low_confidence_course_degrades_and_does_not_engage` | guard (green at RED) |
| Opposed-check wiring trap (don't mask the prod-context gap) | `test_pre_pass_accepts_orbital_content_param`, `test_pre_pass_threads_orbital_content_to_course_handler` | failing (RED) |
| Vacuous-assertion self-check (lang-review: `assert True` / truthy-only / no-assert) | all assert specific values/spans/decisions | satisfied |

**Rules checked:** 7 of 7 applicable principles have test coverage.
**Self-check:** 0 vacuous tests found; the 2 green-at-RED are documented guards with specific assertions, not `assert True`.

**Handoff:** To Dev (Inigo) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (server):**
- `sidequest/agents/subsystems/course.py` (NEW) — `run_course_dispatch`: resolves `params["destination"]` against `orbits.bodies`, computes ETA/Δv via the existing pure `compute_eta_and_dv`, commits a `PlottedCourse` (`course.plot` span), and advances the story clock by a TRAVEL `StoryBeat` of `duration_hours == eta` via the existing `advance_clock_via_beat` (`clock.advance` span). Loud-rejects malformed/no-orbital-tier/no-party-anchor/unknown-destination via `course.plot.rejected` — no phantom plot, no silent no-op.
- `sidequest/agents/subsystems/__init__.py` — registered `("course", run_course_dispatch)` in `_register_defaults`.
- `sidequest/agents/dispatch_engagement_watcher.py` — added `_check_course_engaged` witness + `course` entries in `_WITNESSES` and `_DISPATCHED_TYPE_KEY`; corrected the "nine"→"ten" docstring.
- `sidequest/server/intent_router_pass.py` — new `orbital_content` param on `execute_intent_router_pre_narrator_pass`, threaded into the bank `context` dict (signature-filtered, so non-orbital subsystems are unaffected).
- `sidequest/server/websocket_session_handler.py` — call site passes `sd._room.session.orbital_content` (None-safe; None for non-orbital worlds).
- `sidequest/agents/intent_router.py` — `_SYSTEM_PROMPT` documents the `course` subsystem key + `params={"destination": ...}` so the live Haiku router can emit it.
- `tests/agents/test_59_30_witnesses.py` — updated the witness-count invariant 9→10 (legitimate change: a real witness was added).

**Reuse, not reinvention:** the handler calls the existing ADR-130 resolvers (`compute_eta_and_dv`, `PlottedCourse`, `advance_clock_via_beat`, `Clock`) and the existing span emitters — zero new course/clock math.

**Tests:** new file 9/9 GREEN; `tests/agents/` + `tests/orbital/` = **1926 passed, 549 skipped, 0 failed**. Lint clean, format clean, pyright 0 errors on all changed files.

**Pre-existing failures (NOT regressions):** a scoped `tests/server/ -k "intent_router or dispatch or course or websocket"` run showed 6 failures (pregen/encounters ×4, lore-RAG double-dispatch, sealed-letter legacy beat). Verified by stashing my changes and re-running on the RED commit — **the same 6 fail without my work**, so they are pre-existing baseline failures unrelated to course/clock.

**Branch:** `feat/153-5-swn-orbital-course-inert-wire-adr130-intentrouter` (pushed).

**Self-review:**
- [x] Wired end-to-end: handler → registry → real `run_dispatch_bank` → pre-pass context → call site; watcher witness for the lie-detector; router prompt so the live router can emit it.
- [x] Follows project patterns (mirrors `quest_offer` subsystem + `movement` seam wiring).
- [x] All TEA ACs met (7 RED→GREEN, 2 guards stay GREEN).
- [x] Error handling: every failure path is a loud `course.plot.rejected` span + error-coded `SubsystemOutput` (No Silent Fallbacks).

**Handoff:** To Reviewer (Westley) for review.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Question** (non-blocking): the plot-vs-arrival semantics of a single course/clock dispatch are a genuine design fork. Tests assert the course is *committed* (robust via `_course_committed` = `plotted_course` set OR `party_body_id` arrived) and the clock advances by the full ETA, but do NOT pin whether the party immediately arrives (and `plotted_course` clears) or stays en route. Affects `sidequest/agents/subsystems/course.py` (Dev/Reviewer should confirm the intended fast-travel-vs-plot semantics with Keith; the SM raised the same open question). *Found by TEA during test design.*
- **Gap** (non-blocking): the course engine's inputs (`orbital_content`, `orbital_scope`, `recent_body_mentions`) live on `Session`, not `GameSnapshot`; only `party_body_id`/`clock_t_hours`/`quest_anchors`/`plotted_course` are on the snapshot. The bank context (`intent_router_pass.py:951`) and pre-pass signature carry none of the `Session`-only orbital state today. Tests require only `orbital_content` threaded (the destination resolves against `orbits.bodies` directly), but if Dev chooses the scoped `compute_courses` resolution path they'll also need scope/mentions threaded. Affects `sidequest/server/intent_router_pass.py` + `websocket_session_handler.py`. *Found by TEA during test design.*
- **Improvement** (non-blocking): the IntentRouter `_SYSTEM_PROMPT` subsystem enumeration is hand-maintained prose with no structured key list to assert against, so prompt/registry drift can't be unit-guarded without a forbidden source grep. Adding `course` to the prompt is required for real-play engagement but is only verifiable via the post-merge playtest. Affects `sidequest/agents/intent_router.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Question** (non-blocking): resolved the SM/TEA plot-vs-arrival fork toward **plot-persists** — `run_course_dispatch` commits a `PlottedCourse` and advances the clock by the full ETA, but does NOT update `party_body_id` (no immediate arrival). This makes "burn for X" consume the transit time while leaving the course on the chart; a distinct arrival trigger (clearing `plotted_course`, setting `party_body_id`) is out of scope. Confirm with Keith whether a single travel intent should also *arrive*. Affects `sidequest/agents/subsystems/course.py`. *Found by Dev during implementation.*
- **Improvement** (non-blocking): the legacy narrator-sidecar course path (`narration_apply.py::_apply_course_sidecar`, fed by the narrator's `plot_course` game_patch) still exists alongside the new dispatch subsystem. Both now write `snapshot.plotted_course`; they don't conflict (pre-narrator dispatch wins the turn, the sidecar is a narrator fallback), but a future story may retire the sidecar once the dispatch path is playtest-confirmed. Affects `sidequest/server/narration_apply.py`. *Found by Dev during implementation.*
- **Gap** (non-blocking): the `course` handler resolves a destination against the world's full `orbits.bodies` (Zork-aligned: any named body), not the scoped `compute_courses` menu — so it does not consume `orbital_scope`/`recent_body_mentions` (Session-only state not threaded into the bank). If a future design wants travel restricted to the surfaced `<courses>` set, those inputs must also be threaded. Affects `sidequest/server/intent_router_pass.py`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): the `course` engagement witness (`_check_course_engaged`) sees only `dispatch`+`snapshot`, not the `BankResult`, so a loudly-rejected dispatch (`no_orbital_tier` / `unknown_destination` / `no_party_anchor`) still fires `dispatch_engagement.course.mismatch` — a GM-panel false-positive. This is **consistent with every sibling witness** (`quest_offer`, `confrontation`, `movement` share the property); it is a pre-existing watcher-design limitation, not a regression in this story. A future watcher story could thread the per-dispatch `decision`/`error` so a loud rejection isn't reported as narrator-improvisation. Affects `sidequest/agents/dispatch_engagement_watcher.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the handler mutates `snapshot.plotted_course` and emits `course.plot` **before** advancing the clock, so a (config-malformed) raise from `advance_clock_via_beat` would leave a committed plot + a `course.plot` span with no matching `clock.advance` and no `course.plot.rejected`. Reachable only via a malformed `travel_speed_factor` (≤0 → ZeroDivision/negative ETA), and the bank records the error, so it is narrow; advancing the clock before committing the plot would make it atomic. Affects `sidequest/agents/subsystems/course.py`. *Found by Reviewer during code review.*
- **Question** (non-blocking): the same-body case (`destination == party_body_id`) plots a zero-ETA course and advances the clock by 0h with no rejection — harmless (the witness reads it as "arrived"), but a `same_body` loud-reject would be cleaner. Affects `sidequest/agents/subsystems/course.py`. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Course commitment asserted via OTEL span + arrival-OR-plot, not a single state field**
  - Spec source: context-story-153-5.md, "Acceptance Criteria — TEA to define"; story title "course/clock"
  - Spec text: "wire ADR-130 course/clock to the IntentRouter subsystem bank"
  - Implementation: the engagement assert uses `_course_committed()` (plotted_course set OR party arrived) plus the `course.plot` span, rather than hard-pinning `plotted_course` to a specific terminal state
  - Rationale: the plot-persists vs immediate-arrival semantics are an unresolved design fork (logged as a Question); pinning one terminal field would over-constrain Dev and could force a semantics Keith hasn't ruled on. The span + either-outcome assert proves the engine engaged without dictating the fork.
  - Severity: minor
  - Forward impact: if Keith rules on immediate-arrival, the `test_watcher_silent_when_course_committed` fixture (which sets `plotted_course`) may need to assert arrival instead — a one-line fixture change, not a contract change.
- **Production pre-pass wiring split across a reflection tripwire + a behavioral drive**
  - Spec source: CLAUDE.md "Verify Wiring, Not Just Existence" / "No Source-Text Wiring Tests"
  - Spec text: "verify it's actually connected end-to-end ... new code has non-test consumers"
  - Implementation: one runtime-signature (reflection) assert that the pre-pass accepts `orbital_content`, plus one behavioral drive of the REAL pre-pass with a stubbed router; no source grep of the prompt/handler
  - Rationale: the IntentRouter `_SYSTEM_PROMPT` key list is prose (no structured constant), so prompt registration can't be unit-asserted without a forbidden grep; the reflection + behavioral pair is the blessed substitute and the playtest covers the prompt half.
  - Severity: minor
  - Forward impact: none.

### Dev (implementation)
- **Course commitment is plot-persists, not immediate-arrival**
  - Spec source: 153-5 session (SM open question + TEA Question finding); story title "course/clock"
  - Spec text: "wire ADR-130 course/clock to the IntentRouter subsystem bank"
  - Implementation: a `course` dispatch commits `PlottedCourse` + advances the clock by ETA, but does NOT set `party_body_id` to the destination (no arrival/clear)
  - Rationale: the TEA tests assert engagement via `course.plot`+`clock.advance` spans and a committed course (the `_course_committed` helper accepts plotted OR arrived), so plot-persists satisfies the contract without inventing an arrival semantics Keith has not ruled on; arrival is a clean follow-up.
  - Severity: minor
  - Forward impact: a future "arrival" story would set `party_body_id` and clear `plotted_course` (ADR-130 "cleared on arrival"); the `course` watcher already treats arrival as engagement so it needs no change.
- **Destination resolves against full orbits.bodies, not the scoped compute_courses menu**
  - Spec source: SOUL.md "The Zork Problem"; TEA `test_course_intent_through_bank...`
  - Spec text: "never let the interface imply a closed set of options when the set is open"
  - Implementation: `run_course_dispatch` resolves the player-named body against `orbits.bodies` directly (compute_eta_and_dv), not via the capped/scoped `compute_courses` selection
  - Rationale: the IntentRouter path is open natural language — a player may name any body, not just the surfaced `<courses>` rows; this also keeps the bank context minimal (only `orbital_content` + `snapshot`, no Session-only scope/mentions). The unknown-body case still fails loud.
  - Severity: minor
  - Forward impact: none (a scoped-menu variant would need scope/mentions threaded — logged as a Delivery Finding).

### Reviewer (audit)
- **TEA: Course commitment asserted via OTEL span + arrival-OR-plot** → ✓ ACCEPTED by Reviewer: sound. The plot-vs-arrival fork is genuinely unresolved (SM + Dev concur); asserting engagement via `course.plot`/`clock.advance` spans + `_course_committed` (plotted OR arrived) proves the engine fired without over-pinning a semantics Keith hasn't ruled. Verified both spans are real (`telemetry/spans/course.py`, `telemetry/spans/clock.py`).
- **TEA: Production pre-pass wiring split across reflection tripwire + behavioral drive** → ✓ ACCEPTED by Reviewer: this is the blessed substitute for the forbidden source-grep (CLAUDE.md "No Source-Text Wiring Tests"). Verified `test_pre_pass_threads_orbital_content_to_course_handler` drives the REAL `execute_intent_router_pre_narrator_pass` with a stubbed router and asserts `clock.advance` + a committed course — a true end-to-end behavioral proof, not a shape grep.
- **Dev: Course commitment is plot-persists, not immediate-arrival** → ✓ ACCEPTED by Reviewer: within the TEA contract. Independently verified there is **no double-clock-advance**: arrival sets `party_body_id` via `server/session.py` scope-bind (line 209) which does NOT advance the clock — this dispatch is the sole travel clock-advance, which is exactly the stale-clock bug being fixed. The "confirm arrival-vs-plot with Keith" question is correctly flagged non-blocking.
- **Dev: Destination resolves against full `orbits.bodies`, not scoped `compute_courses`** → ✓ ACCEPTED by Reviewer: aligns with SOUL "The Zork Problem" (open natural-language travel, not a closed menu) and keeps the bank context minimal. The unknown-body path still fails loud (`course.plot.rejected` reason=`unknown_destination`) — verified.
- No undocumented spec deviations found. The handler advances the clock inline (constructs its own `Clock` + calls `advance_clock_via_beat`) rather than via `Session.advance_via_beat`, but it has no `Session` handle in the bank context (only `snapshot`+`orbital_content`) and calls the identical primitive — consistent, not a deviation.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 | N/A — 32 passed / 0 failed; ruff check + format clean; pyright 0 errors |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 4 | confirmed 4 (all LOW / non-blocking), dismissed 0, deferred 0 |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | clean | 0 | N/A — 1 low hardening note (no span-attr length cap), not actionable in a single-tenant game |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — rule compliance assessed by Reviewer below |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 4 confirmed (all LOW / non-blocking), 0 dismissed, 0 deferred

### Silent-failure-hunter findings — disposition
1. **same-body not rejected** (course.py) — CONFIRMED, downgraded to **LOW**. `destination == party_body_id` → `compute_eta_and_dv` returns `(0.0, 0.0)` (identity check), commits a zero-ETA plot, advances clock 0h, no reject. Harmless (the witness then reads `party_body_id == destination` → "arrived", no false mismatch; `Clock.advance(0.0)` is explicitly legal). Edge, no crash, no silent failure of a *real* action. Non-blocking; logged as a Question delivery finding.
2. **non-atomic plot+clock** (course.py) — CONFIRMED, downgraded to **LOW**. `plotted_course` + `course.plot` are set before `advance_clock_via_beat`; only a malformed `travel_speed_factor` (≤0) makes the advance raise (negative ETA → `Clock.advance` ValueError, or ZeroDivision). The bank catches + records it (`result.errors` + span `error` attr) — loud-ish, not silent — but leaves a phantom plot. Narrow (config error). Non-blocking; logged as an Improvement.
3. **witness false-positive on loud rejections** (watcher) — CONFIRMED, downgraded to **LOW**. The witness has no `BankResult`, so a loud `no_orbital_tier`/`unknown_destination` reject still fires `course.mismatch`. **Consistent with every sibling witness** (quest_offer/confrontation/movement) — pre-existing watcher design, not a regression here; observability-only (a GM-panel beep, never control flow). Non-blocking; logged as an Improvement for the watcher subsystem broadly.
4. **`_room.session` None silent** (websocket_session_handler) — CONFIRMED, downgraded to **LOW**. Low-confidence per the hunter; the new code is actually *more* defensive than surrounding `sd._room.session` accesses, and a live turn implies a bound session. A diagnostic log would help distinguish "non-orbital" from "session not yet bound" but is not required. Non-blocking.

### Rule Compliance

Enumerated against CLAUDE.md (server) + SOUL.md for every changed symbol:

- **No Silent Fallbacks** — `run_course_dispatch`: all four failure paths (`malformed_destination`, `no_orbital_tier`, `no_party_anchor`, `unknown_destination`) emit `course.plot.rejected` AND return an error-coded `SubsystemOutput`. No `except: pass`, no silent default. **COMPLIANT.** (The lone edge, `same_body`, plots a trivial valid course rather than rejecting — a Question, not a silent fallback.)
- **No Stubbing** — `course.py` is a complete handler; no empty shells. **COMPLIANT.**
- **Don't Reinvent — Wire Up What Exists** — handler reuses `compute_eta_and_dv`, `PlottedCourse`, `CourseSource`, `StoryBeat`, `advance_clock_via_beat`, `Clock`, and the existing `emit_course_plot_accepted`/`emit_course_plot_rejected` emitters. Zero new course/clock math. **COMPLIANT.**
- **Verify Wiring, Not Just Existence** — registered in `_register_defaults` (`__init__.py:208`); reachable through the real `run_dispatch_bank` (signature-filtered context delivers `snapshot`+`orbital_content`); `execute_intent_router_pre_narrator_pass` gains `orbital_content` and threads it; `websocket_session_handler.py:982-1002` passes `session.orbital_content`. Non-test consumer confirmed. **COMPLIANT.**
- **Every Test Suite Needs a Wiring Test** — `test_course_intent_through_bank_plots_and_advances_clock` (real bank) + `test_pre_pass_threads_orbital_content_to_course_handler` (real pre-pass). **COMPLIANT.**
- **No Source-Text Wiring Tests** — all wiring tests use OTEL-span assertions, behavioral drives through the real bank/pre-pass, registry enumeration, and `inspect.signature` reflection (the blessed tripwire). No `read_text()` / source grep. **COMPLIANT.**
- **OTEL Observability Principle** — every decision emits a span: `course.plot` (accept), `course.plot.rejected` (4 reasons), `clock.advance` (travel beat), plus the bank/subsystem spans and the `dispatch_engagement.course.mismatch` witness. The GM-panel lie-detector can see engage-vs-improvise. **COMPLIANT.**
- **Delete dead code in the same PR** — no dead code introduced; the legacy `_apply_course_sidecar` path remains a live narrator fallback (Dev logged it as a future-retire Improvement), not dead. **COMPLIANT.**
- **Agency / The Test (SOUL)** — N/A to a course/clock dispatch (no player-action authoring). No violation.

### Observations
- **[VERIFIED] No double clock-advance** — arrival is set via `server/session.py:209` scope-bind, which does NOT advance the clock; this dispatch is the only travel clock-advance. Evidence: `server/session.py:204-212` (scope-bind, no `advance_via_beat`) vs `course.py:111` (the sole TRAVEL advance). The pre-fix bug ("story clock went stale") is correctly resolved with no double-count.
- **[VERIFIED] No Silent Fallbacks** — `course.py:85-98, 100-114` — every reject path emits `course.plot.rejected` + error-coded output; evidence confirmed against `telemetry/spans/course.py:104-119`.
- **[VERIFIED] End-to-end wiring** — `__init__.py:181,208` (register) → `__init__.py:378-380` (bank signature-filtered call) → `intent_router_pass.py:754,979-986` (param + context) → `websocket_session_handler.py:982-1002` (call site). Plus witness in `_WITNESSES` + `_DISPATCHED_TYPE_KEY` (`dispatch_engagement_watcher.py:418,432`).
- **[SILENT][LOW] Non-atomic plot-then-advance** — `course.py:105-119` mutates plot + emits `course.plot` before the clock advance; a malformed-config raise leaves a half-state. Narrow, bank-recorded. Non-blocking.
- **[SILENT][LOW] Witness false-positive on loud rejects** — `dispatch_engagement_watcher.py:379-405`; consistent with sibling witnesses, observability-only. Non-blocking.
- **[SILENT][LOW] same-body zero-ETA plot** — `course.py:100` (no `destination == party_id` guard). Harmless edge. Non-blocking.
- **[SEC][LOW] No length cap on `destination` span attr** — `telemetry/spans/course.py:104`; single-tenant game, OTEL SDK truncates without crashing. Non-actionable.
- **[VERIFIED] Pattern fidelity** — mirrors the `quest_offer` subsystem + `movement` seam: handler shape, witness shape, `_DISPATCHED_TYPE_KEY` entry, confidence-gate participation (gate fires before registry lookup, so `course` degrades correctly below 0.6 — `__init__.py:342-359`).

### Devil's Advocate

Assume this code is broken. **Time-economy abuse:** plotting advances the story clock by the full ETA at *plot* time, before arrival. A player who declares travel every turn ("burn for X", next turn "burn for Y") advances the clock by `eta_X + eta_Y` while never arriving anywhere (`party_body_id` never changes), so the clock can race ahead of narrative reality and a later cancel can't reclaim the spent hours. Is that a corruption? No — it's the intentional "Cut the Dull Bits" fast-travel-time choice, explicitly logged as a design fork (TEA/Dev/SM all flagged it, deferred to Keith). One dispatch per turn (idempotency + confidence gate) bounds the rate; spending time to travel is legitimate, not abuse. **Confused user:** "where is the Red Prospect?" should be a query, not travel — the router prompt explicitly excludes "asking where something is", and the 0.6 confidence gate degrades ambiguous intents to a narrator hint (verified: `test_low_confidence_course_degrades_and_does_not_engage`). **Malformed world config:** `travel_speed_factor ≤ 0` → ZeroDivision or negative ETA → `advance_clock_via_beat` raises after `plotted_course` is already committed and `course.plot` already emitted, leaving a half-state with no `clock.advance` and no `course.plot.rejected`. Real but narrow (config defect, not player input), and the bank records the exception loudly — logged as a non-blocking Improvement to reorder for atomicity. **Stressed filesystem / missing session:** `_room.session is None` silently yields `None` orbital_content → `no_orbital_tier` reject, indistinguishable in logs from a genuine non-orbital world; low-confidence, defensive-only. **Router emits a junk destination:** resolved by `bodies.get(destination)` (plain dict lookup — no eval, no path traversal, no injection per the security pass) and rejected loud. None of these rise to Critical/High: the worst is a config-only half-state and observability noise, both non-blocking. The implementation is honest, loud, and wired.

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** player free-text → IntentRouter (Haiku) classifies `course` + `params={"destination"}` → `execute_intent_router_pre_narrator_pass` threads `session.orbital_content` into the bank context → `run_dispatch_bank` (confidence gate ≥0.6, signature-filtered) → `run_course_dispatch` resolves `destination` against `orbits.bodies` → commits `PlottedCourse` (`course.plot`) + advances the story clock by a TRAVEL beat == ETA (`clock.advance`) → post-narration `dispatch_engagement` watcher witnesses the plot/arrival. Unknown/malformed/no-tier/no-anchor destinations fail loud via `course.plot.rejected`. Safe: destination is a dict-key lookup (no injection), every path is OTEL-observable, and the clock is advanced exactly once for travel (no double-count).

**Pattern observed:** faithful reuse of the `quest_offer` subsystem + `movement` seam pattern (handler + witness + `_DISPATCHED_TYPE_KEY` + confidence-gate participation) — `sidequest/agents/subsystems/course.py:171` and `sidequest/agents/dispatch_engagement_watcher.py:379`.

**Error handling:** every failure path emits a loud `course.plot.rejected` span + error-coded `SubsystemOutput` (`course.py:85-114`); the bank catches handler exceptions non-fatally (`__init__.py:379-392`); the watcher is non-fatal by contract (`dispatch_engagement_watcher.py:534-558`).

**Subagent dispatch coverage:**
- `[EDGE]` — edge-hunter disabled via settings; boundary cases (same-body zero-ETA, below-threshold degrade, unknown destination, None session) assessed by Reviewer — all non-blocking.
- `[SILENT]` — 3 confirmed LOW non-blocking (non-atomic plot+advance, witness false-positive consistent-with-siblings, same-body no-reject); 0 blocking. No swallowed errors on real action paths.
- `[TEST]` — test-analyzer disabled; Reviewer verified 9 tests incl. 2 real wiring tests (bank + pre-pass), no vacuous assertions, 2 documented green-at-RED guards; preflight 32/0.
- `[DOC]` — comment-analyzer disabled; Reviewer verified the witness-count docstring corrected 9→10, module docstrings accurate, no stale comments.
- `[TYPE]` — type-design disabled; pyright 0 errors; `OrbitalContent`/`PlottedCourse`/`StoryBeat` typed, `orbital_content` param is `OrbitalContent | None` under TYPE_CHECKING. No stringly-typed regressions.
- `[SEC]` — security pass clean; 1 LOW hardening note (no span-attr length cap), non-actionable single-tenant. Destination lookup is injection-safe.
- `[SIMPLE]` — simplifier disabled; Reviewer found no over-engineering — handler is minimal and reuses existing resolvers.
- `[RULE]` — rule-checker disabled; Reviewer enumerated all 9 applicable rules in Rule Compliance above — every one COMPLIANT.

**Findings:** 4 confirmed, all LOW / non-blocking (logged as Delivery Findings for follow-up). No Critical or High.

**Handoff:** To SM (Vizzini) for finish-story.