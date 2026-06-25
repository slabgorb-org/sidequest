---
story_id: "158-26"
jira_key: "158-26"
epic: "158"
workflow: "trivial"
---

# Story 158-26: dispatch_engagement watcher crashes KeyError on course/dogfight — add missing _SUBSYSTEM_TO_SPAN_NAME entries so the GM-panel lie-detector covers both new space-scale subsystems

## Story Details

- **ID:** 158-26
- **Jira Key:** 158-26
- **Workflow:** trivial
- **Stack Parent:** none

## Workflow Tracking

**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-25T17:40:13Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-25T17:28:39Z | 2026-06-25T17:30:51Z | 2m 12s |
| implement | 2026-06-25T17:30:51Z | 2026-06-25T17:35:07Z | 4m 16s |
| review | 2026-06-25T17:35:07Z | 2026-06-25T17:40:13Z | 5m 6s |
| finish | 2026-06-25T17:40:13Z | - | - |

## Delivery Findings

### Dev (implementation)
- No upstream findings. The `course`/`dogfight` engagement checkers (153-5
  `_check_course_engaged`, 153-6 `_check_dogfight_engaged`) already existed and
  were correctly wired into the watcher's subsystem-check dispatch; only the
  span-name mapping in the spans module was missing. Clean, isolated fix.

### Reviewer (code review)
- **Improvement** (non-blocking): The `watcher_crashed` span records the full
  exception message via `str(exc)` as the `error` OTEL attribute
  (`sidequest/agents/dispatch_engagement_watcher.py:~587`). A future witness whose
  exception message embeds a `params` value (NPC name, fact_id, player-typed text)
  would persist that into GM-panel/`turn_telemetry` storage (CWE-209, low severity —
  GM/dev-facing only, `logger.error(exc_info=True)` already captures the traceback
  server-side). **Pre-existing; NOT introduced or touched by this diff** — surfaced
  by reviewer-security because the new tests exercise the crash path. Affects
  `sidequest/agents/dispatch_engagement_watcher.py` (truncate/sanitize `str(exc)`
  or store only `type(exc).__name__` + a fixed-format summary). *Found by Reviewer
  during code review.*

## Design Deviations

### Dev (implementation)
- No deviations from spec. The implementation matches the Sm Assessment scope
  exactly: two span-name constants added, registered in `SPAN_ROUTES`, mapped in
  `_SUBSYSTEM_TO_SPAN_NAME`, exported in `__all__`. No new behavior invented; no
  change to the watcher's engagement logic (it already handled both subsystems).
  → ✓ ACCEPTED by Reviewer: verified — the diff is additive-only (180 insertions,
  0 deletions), the engagement checkers (`_check_course_engaged`,
  `_check_dogfight_engaged`) and their `_WITNESSES`/`_DISPATCHED_TYPE_KEY` registrations
  pre-date this story; only the spans-module mapping changed. Scope matches exactly.

### Reviewer (audit)
- No undocumented deviations. The implementation is a faithful, minimal realization
  of the Sm Assessment scope; no spec divergence escaped the Dev log.

## Sm Assessment

**Scope (trivial, 1pt, server only):** Register the two missing subsystem keys in
`_SUBSYSTEM_TO_SPAN_NAME` (`sidequest-server/sidequest/telemetry/spans/dispatch_engagement.py:100`)
so `span_name_for_subsystem()` (:155) stops raising `KeyError` for `course` and `dogfight`.
Today that KeyError is swallowed by `run_dispatch_engagement_watcher` (:570) which emits
`watcher_crashed` — so the GM-panel lie-detector is blind on both new space-scale subsystems
(added by 153-5 #1026 and 153-6 #1036).

**Technical approach (bind, don't invent):** Add the two keys following the existing dict
pattern, pointing at `dispatch_engagement.course.mismatch` / `dispatch_engagement.dogfight.mismatch`
span-name constants. Confirm those constants exist and are registered in `SPAN_ROUTES` — verify,
do not fabricate.

**Acceptance criteria:**
- `course` + `dogfight` keys present in `_SUBSYSTEM_TO_SPAN_NAME` with correct constants.
- Constants exist and are registered in `SPAN_ROUTES` (verified).
- Wiring test drives a course mismatch AND a dogfight mismatch, asserting the respective
  `dispatch_engagement.{course,dogfight}.mismatch` span fires and `watcher_crashed` does NOT.
- `just server-check` (ruff + pytest) green.
- Prereq for verifying 158-27 on the GM panel.

**Deviation — setup overstepped:** The setup subagent pre-wrote the implementation and tests
(diff already staged on `feat/158-26-dispatch-engagement-span-keys`: +8 in dispatch_engagement.py,
+150 / +22 in the two test files). **Dev owns this diff now — verify it, do not re-derive it.**
Run the real test suite via testing-runner; the subagent's "52 tests pass" claim is unverified
narration and must not be trusted. Confirm the wiring assertion actually exercises a real
course/dogfight mismatch (not a vacuous mock) before handing to review.

## Dev Assessment

**Implementation Complete:** Yes (verified the pre-written diff; did not re-derive)

**Files Changed:**
- `sidequest/telemetry/spans/dispatch_engagement.py` — added `SPAN_DISPATCH_ENGAGEMENT_COURSE_MISMATCH`
  + `SPAN_DISPATCH_ENGAGEMENT_DOGFIGHT_MISMATCH` constants, registered both in the `SPAN_ROUTES`
  loop, mapped `"course"`/`"dogfight"` in `_SUBSYSTEM_TO_SPAN_NAME`, exported both in `__all__` (+8).
- `tests/agents/test_dispatch_engagement_watcher.py` — 6 wiring tests driving real course/dogfight
  mismatch + happy-path snapshots through `run_dispatch_engagement_watcher` (+150).
- `tests/telemetry/test_dispatch_engagement_spans.py` — 2 constant-registration tests (+22).

**Verification (run directly via pytest `-n0`, NOT testing-runner — it clobbers this session
file and hallucinates pass/fail):**
- GREEN: `52 passed` across both test files.
- RED-without-fix confirmed: stashed the source change, re-ran — `4 failed` (the two mismatch-span
  tests hit the KeyError→watcher_crashed path; the two registration tests fail). The four
  "emits_no_span" happy-path tests pass either way (no mismatch → no span lookup → no crash),
  so they're false-positive guards, not vacuous. Tests are genuine red-before-green.
- `ruff check` clean; `ruff format --check` clean (scoped to the 3 changed files).
- Engagement logic was already present and wired (`_check_course_engaged` 153-5,
  `_check_dogfight_engaged` 153-6, registered in `_SUBSYSTEM_CHECKS`); the only gap was the
  span-name mapping. Fix is correct, minimal, and matches the diagnosis.

**Tests:** 52/52 passing (GREEN)
**Branch:** `feat/158-26-dispatch-engagement-span-keys` (pushed, commit `9da9d85b`)

**Handoff:** To review (The Queen of Hearts). Prereq for verifying 158-27 on the GM panel.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (52 pass, 0 smells) | N/A — flagged "is detection real?"; Reviewer confirmed real |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | findings | 1 (low) | deferred 1 (pre-existing, out-of-scope → Delivery Finding) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (2 enabled returned; 7 disabled via `workflow.reviewer_subagents`)
**Total findings:** 0 confirmed blocking, 1 dismissed-from-scope (with rationale → captured as non-blocking Delivery Finding), 0 deferred-to-rework

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** intent-router `SubsystemDispatch(subsystem="course"|"dogfight")` →
`run_dispatch_engagement_watcher` iterates dispatches → `_WITNESSES["course"]`/`["dogfight"]`
(`_check_course_engaged` reads `snapshot.plotted_course`/`party_body_id`;
`_check_dogfight_engaged` reads `snapshot.encounter`/`encounter_type`) → on mismatch,
`span_name_for_subsystem(subsystem)` resolves via `_SUBSYSTEM_TO_SPAN_NAME` (previously
KeyError → `watcher_crashed`; now returns `dispatch_engagement.{course,dogfight}.mismatch`)
→ span emitted with `subsystem` attribute (set at `dispatch_engagement.py:182`) → routed to
GM panel via `SPAN_ROUTES` (`component="intent_router"`, shared `_extract`). Safe: no
player-controlled string reaches any span name or attribute key.

**Pattern observed:** Textbook "Wire Up What Exists" (CLAUDE.md) — the engagement checkers
and their `_WITNESSES`/`_DISPATCHED_TYPE_KEY` registrations already existed from 153-5/153-6;
the only gap was the span-name mapping. The two new entries mirror the eight existing
dispatch_engagement mismatch siblings exactly across all four insertion sites (constant,
`SPAN_ROUTES` loop, `_SUBSYSTEM_TO_SPAN_NAME`, `__all__`). `dispatch_engagement.py:91`.

**Error handling:** The fix *preserves* fail-loud: `span_name_for_subsystem` still raises
`KeyError` for genuinely-unknown subsystems (a router typo), per its docstring and
`feedback_no_fallbacks_hard` — it just stops mis-classifying the *legitimate* course/dogfight
subsystems as typos. This is the opposite of a silent fallback; it removes an accidental
crash without weakening the loud-failure contract. `dispatch_engagement.py:155`.

### Subagent dispatch tags
- `[PRE]` reviewer-preflight: GREEN 52/52, ruff clean, format clean, 0 code smells, 180/0
  add/del. Its lone concern — "could the test be driving a stubbed/no-op detection?" — I
  ran down personally: detection is real (see Data flow). **Resolved, not a finding.**
- `[SEC]` reviewer-security: diff clean; 1 low-confidence, **pre-existing** info-leakage on
  `str(exc)` in the unrelated `watcher_crashed` span (line ~587, not in this diff). Dismissed
  from this story's scope, captured as a non-blocking Delivery Finding for future hardening.
- `[EDGE]` (subagent disabled) — manual: additive dict/constant insertions have no boundary
  conditions; the only branch is the existing `KeyError` path, now correctly avoided for the
  two registered keys. No edge gaps.
- `[SILENT]` (subagent disabled) — manual: no `try/except`, no `suppress`, no swallowed errors
  added. The change *reduces* silent-crash surface. Clean.
- `[TEST]` (subagent disabled) — manual: 8 new tests are non-vacuous — they assert exact span
  name, span count (==1), and the `subsystem` attribute, against real engine objects (not
  Mocks). Verified genuinely red-without-fix (4 fail when the source change is stashed). No
  `assert True`, no skips, no truthy-only checks.
- `[DOC]` (subagent disabled) — manual: new constants self-describe; test docstrings explain
  the lie-detector intent and cite 153-5/153-6. No stale/misleading comments.
- `[TYPE]` (subagent disabled) — manual: constants are module-level `str` literals (correct,
  matching siblings); test fns annotated `-> None`. No stringly-typed API regressions.
- `[SIMPLE]` (subagent disabled) — manual: minimal — 8 source lines, no abstraction, no dead
  code. Could not be simpler while following the pattern.
- `[RULE]` (subagent disabled) — manual rule enumeration below.

### Rule Compliance (manual enumeration — rule_checker disabled)
- **No Silent Fallbacks (CLAUDE.md):** COMPLIANT — fail-loud `KeyError` preserved for unknown
  subsystems; legitimate keys registered, not defaulted.
- **No Stubbing (CLAUDE.md):** COMPLIANT — zero stubs; both subsystems have live checkers.
- **Wire Up What Exists (CLAUDE.md):** COMPLIANT — integration, not reimplementation.
- **Every Test Suite Needs a Wiring Test (CLAUDE.md):** COMPLIANT — tests drive the real
  `run_dispatch_engagement_watcher` entry point end-to-end; `test_watcher_wired_into_session_handler`
  covers session-handler reachability.
- **OTEL Observability Principle (CLAUDE.md):** COMPLIANT — this fix *restores* GM-panel
  lie-detector coverage for both new space-scale subsystems (the story's whole point).
- **python checklist #1 (silent except):** N/A — no except added. **#3 (type annotations):**
  COMPLIANT. **#6 (test quality):** COMPLIANT (real assertions, no skips). **#10 (import
  hygiene / `__all__`):** COMPLIANT — `__all__` updated for both new public constants;
  function-level test imports match the file's existing pattern. **#2/#4/#5/#7/#8/#9/#11/#12:**
  N/A — no mutable defaults, logging, paths, resources, deserialization, async, input
  boundaries, or deps in this diff.

### Devil's Advocate
Let me try to break this. *Could the tests be green against a stub?* That was preflight's
sharpest worry, and the most plausible failure for a 1-pt "just add two dict keys" change:
the registration tests would pass trivially, and the watcher tests *could* pass if the
detection were a no-op that emits nothing. But the mismatch tests assert `len(spans) == 1`
with the exact span name — a no-op detector would emit *zero* spans and fail that assertion.
And I confirmed the RED-without-fix run produced exactly those failures. So the tests have
teeth. *Could `snap.plotted_course = None` be silently attaching a phantom attribute the
watcher never reads?* No — `_check_course_engaged` reads `snapshot.plotted_course.to_body_id`
and `snapshot.party_body_id`, and the happy-path test sets a real `PlottedCourse` and gets
*no* span, proving the read path discriminates on field value. *Could a malicious/garbage
subsystem string now route somewhere unsafe?* No — only `"course"`/`"dogfight"` were added;
any other unknown subsystem still hits the fail-loud `KeyError`, unchanged. *Could the shared
`_extract` mis-handle the new spans?* No — they use the identical `SpanRoute` config as eight
working siblings; if `_extract` were broken it would already be broken for all of them.
*Could there be a name collision?* The two new constants and dict keys are unique (grep
confirms single definitions). *What about the pre-existing `str(exc)` leak?* Real, but it
lives at line 587, outside this diff, low-confidence, GM-only — blocking a telemetry-coverage
fix on an unrelated pre-existing hardening item would be exactly the kind of scope-creep the
trivial workflow exists to avoid. Captured for follow-up; not a blocker here. I cannot find a
correctness defect introduced by this change.

### Observations (≥5)
1. `[VERIFIED]` Detection is real, not stubbed — `_check_course_engaged` reads
   `snapshot.plotted_course`/`party_body_id`; `_check_dogfight_engaged` reads
   `snapshot.encounter` — `dispatch_engagement_watcher.py:379,408`. Complies with No-Stubbing.
2. `[VERIFIED]` Both new constants registered in `SPAN_ROUTES` loop with shared `_extract`,
   identical to 8 siblings — `dispatch_engagement.py:91`. Complies with pattern consistency.
3. `[VERIFIED]` `subsystem` attribute the tests assert is genuinely emitted —
   `dispatch_engagement.py:182` (`"subsystem": subsystem`). Test assertion is non-vacuous.
4. `[VERIFIED]` Fail-loud `KeyError` preserved for unknown subsystems —
   `dispatch_engagement.py:155` docstring + behavior. Complies with No-Silent-Fallbacks.
5. `[VERIFIED]` Tests genuinely red-without-fix — 4 fail when the source change is stashed
   (2 mismatch + 2 registration); happy-paths stay green (false-positive guards). Real TDD.
6. `[LOW]` Pre-existing `str(exc)` info-leakage in `watcher_crashed` span —
   `dispatch_engagement_watcher.py:~587`. Out of scope; logged as non-blocking Delivery Finding.

**Handoff:** To SM (The Mad Hatter) for finish-story.