---
story_id: "126-34"
jira_key: ""
epic: "126"
workflow: "tdd"
---
# Story 126-34: [OTEL] Keep test-run sessions out of the live GM dashboard

## Story Details
- **ID:** 126-34
- **Jira Key:** (none — explicitly skipped; no Jira integration for this story)
- **Workflow:** tdd (phased)
- **Points:** 3
- **Type:** bug
- **Repos:** server, ui
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-20T11:06:45Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-20T10:04:10Z | 2026-06-20T10:20:39Z | 16m 29s |
| red | 2026-06-20T10:20:39Z | 2026-06-20T10:33:06Z | 12m 27s |
| green | 2026-06-20T10:33:06Z | 2026-06-20T10:41:51Z | 8m 45s |
| review | 2026-06-20T10:41:51Z | 2026-06-20T10:53:38Z | 11m 47s |
| green | 2026-06-20T10:53:38Z | 2026-06-20T10:58:01Z | 4m 23s |
| review | 2026-06-20T10:58:01Z | 2026-06-20T11:06:45Z | 8m 44s |
| finish | 2026-06-20T11:06:45Z | - | - |

## Technical Approach

### Root Cause
Test-run sessions (test-*, tool-test) accumulate in the live WatcherHub (ADR-122 never-evict policy) because test runs are pointed at the same port as the live server. They pollute the GM dashboard's liveSessions picker, pushing real sessions off-screen and interfering with auto-follow tracking.

**Solution: four-part isolation strategy**

1. **UI Filtering (Short-term UX fix)**
   - Filter test-*/tool-test sessions from liveSessions picker in useLiveSource.ts:347-355
   - Drop test sessions from State-tab debugState display
   - Prevents clutter without architectural change; leaves stale sessions in backend

2. **Activity Timestamp Decoupling (Fix auto-follow staleness)**
   - Stop bumping last_activity_ts on session-list and state polling calls
   - Only genuine player/narrator turn actions advance the timestamp
   - Ensures auto-follow tracking focuses on genuinely-active (game-engaging) sessions
   - Related OTEL work: tag polling activity distinctly so GM panel doesn't mis-attribute

3. **OTEL Span Filtering (GM panel clarity)**
   - Tag infra/test spans (session-list polls, state syncs, etc.) in WatcherHub
   - Session-pin filter in GM dashboard can then fully exclude test-session spans
   - Lie-detector legibility: GM panel shows only true game activity, no noise

4. **Architectural Fix (Root elimination — deferred implementation)**
   - Point test runs at a separate port / no-watcher mode so they never register with operator's WatcherHub
   - Prevents test-session creation in the first place
   - Requires: test runner config refactor (pytest → separate port or --no-watcher flag) + server startup variance
   - Blocks cleanup of 41 stale test-* sessions now (only restart clears them under ADR-122 never-evict)

### Acceptance Criteria
- [ ] useLiveSource.ts:347-355 UI filter drops all test-* and tool-test sessions from liveSessions picker (verify in React UI during liveSessions dropdown)
- [ ] State-tab debugState display excludes test-* sessions (verify in State tab that only real sessions appear)
- [ ] session-list and state polling calls do NOT increment last_activity_ts (verify in backend logs: polling calls preserve existing timestamp)
- [ ] WatcherHub session-tag spans tagged as `span_type: "infra"` or `session_type: "test"` for all test-session activity (verify in OTEL Inspector GM panel: infra spans present, filterable)
- [ ] OTEL lie-detector test: run a real game session + a test-run session in parallel; verify GM panel pin filter can hide test-session spans while showing real-game spans
- [ ] Document the architectural fix design (separate port / --no-watcher mode) as a deferred ADR or tech-debt story for future iteration

### Related ADRs
- **ADR-122:** SessionRoom Lifecycle — RoomRegistry Never-Evict Policy (explains why 41 stale sessions persist)
- **ADR-132:** WatcherHub Infrastructure — builtins-Pinned Singleton, ContextVar Per-Session Isolation, Ephemeral-Event Taxonomy
- **ADR-090:** OTEL Dashboard Restoration after Python Port
- **ADR-050:** Image Pacing Throttle (general render/activity throttling patterns)

## Delivery Findings

No upstream findings at setup.

### TEA (test design)
- **Improvement** (non-blocking): AC#6 (design doc for the deferred architectural fix — point test runs at a separate port / `--no-watcher` mode) is a documentation deliverable, NOT code, so no test covers it. Affects a new deferred ADR or tech-debt story (`docs/adr/` or `pf sprint story add`) — Dev/SM must produce it so the root-cause fix isn't silently dropped. *Found by TEA during test design.*
- **Gap** (non-blocking): the story's AC#4 names a second tagging axis — `span_type="infra"` on infra/poll spans (session-list polls, state syncs) — distinct from the per-session `session_type="test"` marker this suite pins. The infra-span axis is NOT tested here. If Dev tags poll spans `span_type="infra"` too, that behavior is uncovered by 126-34's suite. Affects `sidequest/telemetry/watcher_hub.py` (publish path). *Found by TEA during test design.*
- **Question** (non-blocking): AC#3's root cause is pinpointed — `/api/debug/state` → `PgSaveRepository.for_slug` → `ensure_session` (`save_repository.py:108`), whose `ON CONFLICT (session_slug) DO UPDATE SET last_played` bumps the timestamp on every read. The fix must give the dashboard read path a non-bumping load (e.g. resolve session_id + load without `ensure_session`, or a `touch=False` flag). Affects `sidequest/server/rest.py` `debug_state` + `sidequest/game/pg/save_repository.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): the test-session predicate is duplicated across repos — `is_test_session` (`sidequest/telemetry/watcher_hub.py`) and `isTestSession` (`sidequest-ui/.../useLiveSource.ts`) encode the same `test-`/`tool-test` prefixes independently. Separate repos can't share the code; they must be kept in sync if the convention changes. Affects both predicates. *Found by Dev during implementation.*
- **Improvement** (non-blocking): AC#6 design content is captured in the Dev Assessment below (separate-port / `--no-watcher` test-isolation design); SM should file it as a tech-debt story (epic 125) at finish — Dev does not create sprint stories. Confirms TEA's AC#6 finding. Affects sprint backlog (`pf sprint story add`). *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): the new test file `sidequest-server/tests/server/test_test_session_isolation.py:33` imports `UTC` from `datetime` but never uses it — `ruff check .` fails with F401, and `just server-lint`/`server-check`/CI run `ruff check .` across the whole repo (no test-file F-rule exemption in `pyproject.toml [tool.ruff.lint]`). The branch cannot pass the lint gate as-is. Affects `tests/server/test_test_session_isolation.py` (change line 33 to `from datetime import datetime`). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): confirms TEA's AC#6 finding and Dev's predicate-duplication finding — both remain open and correctly tracked; no new upstream surface beyond them. *Found by Reviewer during code review.*
- **Resolved** (re-review, round-trip 1): the blocking F401 above is FIXED (`from datetime import datetime`); `ruff check` clean. AC#6 (architectural-fix design) and the cross-repo predicate-sync remain the only open follow-ups — both for SM to file as epic-125 tech-debt at finish, not blockers for this story. *Found by Reviewer during re-review.*

## Design Deviations

None at setup.

### TEA (test design)
- **Pinned `session_type="test"` for the broadcast test-session marker**
  - Spec source: context-story-126-34.md, AC#4
  - Spec text: "WatcherHub tags test-session activity with span_type=\"infra\" or session_type=\"test\""
  - Implementation: tests assert `session_type == "test"` on the published envelope for `test-*`/`tool-test*` slugs; do NOT assert `span_type="infra"`.
  - Rationale: the AC offers either field; `session_type` is the direct "this whole session is a test run" axis that the per-session pin filters on. One field, one contract — avoids an ambiguous OR-assertion.
  - Severity: minor
  - Forward impact: Dev implements `session_type` tagging in `publish_event`; `span_type="infra"` for poll-spans (if wanted) is a separate, untested addition (see Delivery Finding).
- **UI filtering pinned at the hook (`useLiveSource`), not the StateTab component**
  - Spec source: context-story-126-34.md, AC#1/#2
  - Spec text: "useLiveSource.ts:347-355 filters … from liveSessions picker" + "State-tab debugState excludes test-* sessions"
  - Implementation: tests assert the hook's RETURNED `liveSessions` and `debugState` both exclude test sessions — one shared predicate in the hook feeds both the picker and the State tab.
  - Rationale: a single source of truth in the hook is harder to drift than per-consumer filters; AC#1 already anchors the fix at `useLiveSource.ts`.
  - Severity: minor
  - Forward impact: Dev adds the test-session predicate in `useLiveSource`; StateTab consumes the already-filtered `debugState`.
- **No red test for AC#6 (architectural fix doc)** — non-code deliverable, out of scope per the story ("out of scope: implementation of the architectural fix"). Tracked as a Delivery Finding instead. Severity: minor. Forward impact: none on the test suite.

### Dev (implementation)
- **debug_state read path: dropped `get_game` + `GameMode(mode)`, use `resolve_session_id` + direct `PgSaveRepository(...)`**
  - Spec source: context-story-126-34.md, AC#3 + TEA's `test_debug_state_poll_does_not_bump_last_activity_ts`
  - Spec text: "session-list and state polling calls do NOT bump last_activity_ts"
  - Implementation: replaced `get_game(...)` + `PgSaveRepository.for_slug(..., mode=GameMode(game.mode), ...)` with `session_id = resolve_session_id(...)` + `PgSaveRepository(pool, session_id=session_id)`. `for_slug`'s `ensure_session` was the bump; binding the repo directly is the non-bumping read TEA's finding suggested.
  - Rationale: minimal way to stop the bump without a new `touch=False` flag on the write path. The dropped `GameMode(game.mode)` parse was only an argument to the removed `ensure_session`; the read never needs `mode`/`genre`/`world`, so a malformed mode now can't even affect the State tab — strictly MORE resilient than before, and the per-slug `try/except` still guards `load()`.
  - Severity: minor
  - Forward impact: none — `for_slug` is unchanged and still used by the real save/connect paths; only the read-only projection switched off it.
- **`session_type="test"` added only for test sessions (omitted for real)** — matches TEA's pinned contract (`.get("session_type") != "test"` for real); did NOT add `span_type="infra"` for poll-spans (TEA's untested second axis — left for a follow-up). Severity: minor. Forward impact: none on the suite.

### Reviewer (audit)
- TEA **`session_type="test"` pinned over `span_type="infra"`** → ✓ ACCEPTED: the AC offered either; one unambiguous field is the right contract. The omitted `span_type="infra"` poll-span axis is tracked as a non-blocking finding.
- TEA **UI filtering pinned at the hook, not StateTab** → ✓ ACCEPTED: a single shared predicate feeding picker + State tab + auto-follow is the lower-drift design; verified `visibleDebugState` is the one source all three derive from (`useLiveSource.ts`).
- TEA **No red test for AC#6 (architectural doc)** → ✓ ACCEPTED: AC#6 is a non-code deliverable, explicitly out of scope; correctly tracked as a Delivery Finding for SM to file.
- Dev **debug_state read path dropped `get_game`+`GameMode`, uses `resolve_session_id`+direct constructor** → ✓ ACCEPTED: verified the direct `PgSaveRepository(pool, session_id=…)` bind runs no `ensure_session` upsert, so the read no longer bumps `last_played`. Dropping `GameMode(mode)` validation is strictly more resilient for a read (mode is unused in the projection) and the per-slug `try/except` still guards `load()`. The integration test proves it end-to-end through the real route. Sound.
- Dev **`session_type` added only for test sessions** → ✓ ACCEPTED with a note: this is the right minimal behavior, but the negative-control TEST asserting it (`!= "test"`) is weaker than the contract (the *key should be absent*) — flagged in the assessment as a test-hardening item, not a code defect.
- **Undocumented deviations:** none found. The implementation matches the logged TEA/Dev deviations; no silent divergence.

## Tea Assessment

**Tests Required:** Yes
**Reason:** n/a — behavioral bug across server + ui with clear, observable contracts.

**Test Files:**
- `sidequest-ui/src/components/Dashboard/__tests__/useLiveSource-test-session-filter.test.tsx` — 4 tests: liveSessions picker excludes `test-*`/`tool-test` (from debugState AND the event stream); State-tab `debugState` excludes them; a newer test session can't steal auto-follow from the real session.
- `sidequest-server/tests/server/test_test_session_isolation.py` — 5 tests: `/api/debug/state` poll does not bump `last_activity_ts` (real route + DB); `publish_event` tags `test-*` and `tool-test*` activity `session_type="test"`; real-session activity is NOT tagged (negative control); real vs test are separable in the live stream (wiring/lie-detector).

**Tests Written:** 9 tests covering 5 of 6 ACs (AC#6 is a non-code doc deliverable — see Delivery Findings).
**Status:** RED (verified by testing-runner):
- ui: `4 failed (4)` — clean compile, all assertion failures (no filtering yet).
- server: `4 failed, 1 passed` — clean collection. The DB test RAN (Postgres available) and concretely showed the bug: poll bumped `last_activity_ts 1577836800000 → 1781951380622`. The 1 pass is the real-session negative control (correctly untagged today; guards against over-tagging — not vacuous).

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| Python #6 / TS test-quality — no vacuous assertions | self-check across all 9 tests | passed (0 vacuous) |
| Python #6 — `mock.patch` on the used target, not the defined one | `captured_publishes` patches `watcher_hub.watcher_hub.publish` (where `publish_event` calls it) | enforced |
| TS #6 — memoized hook outputs (`liveSessions`/`debugState`) | UI tests assert the hook's returned memo values, the real production outputs | enforced |
| Wiring (CLAUDE.md "every suite needs a wiring test") | `test_test_and_real_activity_are_separable_in_the_live_stream` (server, real `publish_event` path); UI tests drive the real `useLiveSource` hook | failing (RED) |

**Rules checked:** Most lang-review rules (silent-except, mutable-defaults, path-handling, resource-leaks) govern Dev's GREEN implementation, not these behavior tests — they are Dev/Reviewer responsibilities, not test-pinnable here. The directly test-coverable rule (test quality / no vacuous assertions) is satisfied.
**Self-check:** 0 vacuous tests. The single passing server test is a meaningful negative control, not an always-true assertion.

**Handoff:** To Dev (Naomi Nagata) for GREEN implementation — server `publish_event` tagging + `debug_state` non-bumping read; ui `useLiveSource` test-session predicate feeding both picker and State tab. Honor the OTEL principle (the `session_type` tag IS the lie-detector hook) and the No-Silent-Fallbacks rule (a test slug is classified, not guessed).

## Sm Assessment

Setup complete and ready for the RED phase. Handing to TEA (Amos Burton).

**State verified:**
- Session file at canonical `sprint/.session/126-34-session.md`; root `.session` symlink repaired this session (was a stray real dir causing handoff split-brain — stray backed up at `.session.stray-20260620`).
- Context written (`sprint/context/context-story-126-34.md`) with the four-part isolation strategy and ACs.
- Branches `feat/126-34-filter-test-sessions-from-dashboard` created in `sidequest-server` and `sidequest-ui` (both off `develop`).
- Jira: explicitly skipped — story has no Jira key.

**Scope for TEA's red tests (server + ui):**
- **ui** — `useLiveSource.ts:347-355`: failing test that test-*/tool-test sessions are dropped from the liveSessions picker and State-tab debugState.
- **server** — `last_activity_ts` is NOT bumped on session-list/state polls (only genuine turn actions advance it); WatcherHub tags infra/test-session spans (`span_type: "infra"` / `session_type: "test"`) so the GM-panel per-session pin can filter them.
- **Part 4 (separate-port / no-watcher test isolation) is DEFERRED** — do not write red tests against an architectural refactor this story isn't implementing; file it as the deferred AC notes.

**Doctrine guardrails for this story:**
- This is an **OTEL story** (CLAUDE.md OTEL principle): the span-tagging fix MUST be verifiable in the GM panel — include the OTEL lie-detector wiring test (real session + test session in parallel; pin filter hides test spans, keeps real ones).
- **Every test suite needs a wiring test** (CLAUDE.md): the UI filter and the server span-tagging each need an integration test proving they're reached from production code paths, not just unit-tested in isolation.

## Dev Assessment

**Implementation Complete:** Yes (AC#1–#5 in code; AC#6 is a non-code doc deliverable — design captured below for SM to file)

**Files Changed:**
- `sidequest-server/sidequest/server/rest.py` — `debug_state` binds `PgSaveRepository` directly via `resolve_session_id` instead of `for_slug`, so the dashboard poll no longer upserts `last_played`/bumps `last_activity_ts` (AC#3).
- `sidequest-server/sidequest/telemetry/watcher_hub.py` — new `is_test_session()` predicate; `publish_event` tags `test-*`/`tool-test*` activity `session_type="test"` on the broadcast envelope (rides broadcast only, never persisted) so the GM-panel pin can filter it (AC#4/#5).
- `sidequest-ui/src/components/Dashboard/source/useLiveSource.ts` — new `isTestSession()` predicate; `visibleDebugState` filters test sessions; `liveSessions` picker, returned State-tab `debugState`, and `autoSlug` (auto-follow) all derive from the non-test set (AC#1/#2 + auto-follow).

**Tests:** GREEN (verified by testing-runner):
- server: 26/26 passing — 5 new (`test_test_session_isolation.py`) + 13 `test_rest_pg_forensic` + 8 `test_debug_state_projection` (no regression in the changed read path). DB tests ran live.
- ui: 12/12 passing — 4 new + 4 `useLiveSource-session-scope` + 4 `useLiveSource-session-select` (no regression in the changed hook).
- Lint/type: server `ruff` clean on both files; ui `tsc --noEmit` exit 0.

**Branches (pushed):**
- `feat/126-34-filter-test-sessions-from-dashboard` @ `60e31305` (sidequest-server)
- `feat/126-34-filter-test-sessions-from-dashboard` @ `f8a1f5d` (sidequest-ui)

**AC#6 design (for SM to file as an epic-125 tech-debt story):**
> **Point test runs at a separate port / `--no-watcher` mode so they never reach the operator's live WatcherHub.** Today the headless harness drives the same `:8765` server, so every test session registers with the process-global `watcher_hub` singleton (ADR-132) and, under ADR-122 never-evict, lingers forever (41 stale `test-*` sessions; only a restart clears them). This story is the *downstream* mitigation (filter at the dashboard, tag at the broadcast). The *root* fix is to stop test sessions reaching the live hub at all: (a) a `SIDEQUEST_NO_WATCHER=1` / `--no-watcher` server flag that no-ops `bind_loop`/`publish` (the hub already drops when no loop is bound), and/or (b) point the harness at a second port/process. Trade-off: a no-watcher test server loses OTEL visibility *for tests that assert on spans* — so it must be opt-in per test-suite, not global. Decision needed: flag vs. separate-port vs. both.

**Handoff:** To Reviewer (Chrisjen Avasarala) for code review.

### Rework — round-trip 1 (Reviewer findings addressed)

All findings were in the test files; no production code changed.
- **[HIGH/blocking] F401** — dropped the unused `UTC` import (`test_test_session_isolation.py:33` → `from datetime import datetime`). `ruff check` on all three server files now clean.
- **[MEDIUM] Negative controls hardened** — `test_publish_event_does_not_tag_real_session_activity` and the separability test now assert `"session_type" not in ev` / `not in by_slug[real]` (key-absent contract), so an accidental non-"test" tag on a real session also fails.
- **[LOW] Coverage added** — bump test now uses a real-style (non-test-prefixed) slug to prove the read-only fix is universal; new `test_publish_event_does_not_tag_infix_test_slug` (`greatest-*`) and `test_publish_event_does_not_tag_sessionless_infra` (None slug); UI event-stream test now drives a `tool-test-` slug too.

**Re-verified:** server `ruff` clean; server 28/28 (isolation suite 5→7) + forensic + projection; ui 12/12; `tsc` exit 0.
**Rework commits:** `61c5deef` (sidequest-server), `fa69b34` (sidequest-ui).
**Handoff:** Back to Reviewer (Chrisjen Avasarala) for re-review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 (lint F401) | confirmed 1 (blocking), dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 7 | confirmed 2 (med), deferred 4 (non-blocking), dismissed 1 (low/redundant) |
| 5 | reviewer-comment-analyzer | Yes | clean | none | N/A |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | none (0 violations / 47 instances) | N/A |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 3 confirmed (1 blocking lint, 2 medium test-hardening), 4 deferred (non-blocking coverage), 1 dismissed (redundant assertion)

## Reviewer Assessment

**Verdict:** REJECTED

The implementation is correct, well-tested (server 26/26, ui 12/12), and clean on type-check and on `ruff` for the *production* files. But the branch **fails the lint gate**: the new test file has an unused import (F401), and `just server-lint`/`server-check`/CI run `ruff check .` over the whole repo with no test-file exemption. A branch that fails a required quality gate is not mergeable — that is the blocking issue. Bundled with it are two medium test-hardening fixes worth doing in the same pass.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | Unused `UTC` import fails `ruff check .` (F401) — blocks `just server-check`/CI. Intrinsically a Low nit, elevated because it breaks a required gate. | `tests/server/test_test_session_isolation.py:33` | `from datetime import datetime` (drop `UTC`). |
| [MEDIUM] | [TEST] Negative control under-constrains: `ev.get("session_type") != "test"` passes for ANY non-"test" value (incl. an accidental `"infra"` tag). The contract is *key absent*. | `test_test_session_isolation.py` (`test_publish_event_does_not_tag_real_session_activity`; the `by_slug[real]` assert in the separability test) | Use `assert "session_type" not in ev` (and `"session_type" not in by_slug[real]`). |
| [LOW] | [TEST] Coverage gaps (non-blocking, fix opportunistically): no infix-`test-` slug guard (e.g. `greatest-foo`); no `session_slug=None` (session-less infra) assertion; `tool-test` never driven through the UI event stream; bump test only uses a test-prefixed slug. | `test_test_session_isolation.py`, `useLiveSource-test-session-filter.test.tsx` | Add the missing-case assertions if cheap; not required to pass. |

**Data flow traced:** GM dashboard `GET /api/debug/state` → `list_saves()` enumerates slugs → for each, `resolve_session_id` (pure SELECT) → `PgSaveRepository(pool, session_id=…)` (no `ensure_session`) → `load()` → `project_session_state_view`. No write occurs on the read path — verified the direct constructor (`save_repository.py:18`) only binds sub-stores, runs no upsert. The bump is gone. Parallel path: `publish_event` → `current_session_slug()` → conditional `session_type="test"` on the envelope (top-level, not in `fields`, so never persisted) → `watcher_hub.publish`. Both paths proven by integration tests through the real route/function.

**Pattern observed:** filter-at-the-returned-view, keep-the-reducer-lossless (`useLiveSource.ts` `visibleDebugState`) correctly mirrors the existing per-session scoping pattern — good consistency. Server envelope-tagging mirrors the existing `session_slug` broadcast-only field — good consistency.

**Error handling:** the per-slug `try/except Exception … logger.warning … continue` (`rest.py:461`) is intentional, loud, and No-Silent-Fallbacks-compliant (rule-checker PY-1 confirmed). `resolve_session_id` returning `None` → named `continue`, not a silent alternative path.

**Security:** rule-checker confirmed no injection surface — slug comes from a ContextVar (`current_session_slug`), not raw HTTP input; `startswith` on a tuple has no ReDoS risk; the predicate participates in no SQL/HTML.

**Specialist findings incorporated:** `[TEST]` reviewer-test-analyzer — 2 confirmed (weak negative controls → strengthen to key-absence), 4 deferred coverage, 1 dismissed redundant. `[DOC]` reviewer-comment-analyzer — clean; the stale `GameMode()` reference was correctly removed from the `debug_state` comment, all new docstrings accurate. `[RULE]` reviewer-rule-checker — 0 production-code violations across 47 instances (PY-1 silent-except, TS-4 `?? 0`, TS-6 useMemo deps all verified compliant); its PY-10 "no unused imports" VERIFIED is overruled below by `ruff`.

### Rule Compliance

Checked the full `python.md` (13) + `typescript.md` (13) + 3 CLAUDE.md/SOUL rules against every changed type/function (rule-checker: 47 instances). Result: **0 production-code violations.** Specifically verified:
- **PY-1 silent-except** (`rest.py:461`): compliant — broad catch is intentional per-slug resilience with a loud `logger.warning`; `# noqa: BLE001` justified.
- **PY-3 type annotations**: `is_test_session(slug: str | None) -> bool` fully annotated; `event: dict[str, Any]` correct for a heterogeneous envelope.
- **PY-6 / TS-8 test quality**: no *vacuous* assertions (all check specific values); the two `!= "test"` asserts are *under-constrained*, not vacuous — flagged Medium above.
- **PY-10 import hygiene**: rule-checker said "compliant" but MISSED the unused `UTC` — preflight's `ruff` is authoritative here; the F401 stands (challenged the rule-checker's VERIFIED, see below).
- **TS-4 null/undefined**: `last_activity_ts ?? 0` is correct (`??` not `||`; preserves a legitimate `0`); `visibleDebugState ?? []` correct.
- **TS-6 useMemo deps**: `visibleDebugState`→`[state.debugState]`, `autoSlug`→`[visibleDebugState]`, `liveSessions`→`[visibleDebugState, state.allEvents]` all complete; `isTestSession` is a stable module-level const, correctly absent from deps.
- **No-Source-Text-Wiring-Tests**: compliant — wiring tests call real `publish_event`/`useLiveSource`, no source greps.
- **OTEL Observability**: the `session_type` tag IS the lie-detector hook; satisfied.

**Challenged VERIFIED:** the rule-checker marked PY-10 import hygiene "compliant" and asserted "no unused imports." Preflight's `ruff check` contradicts this with a concrete F401 at line 33. I re-ran `ruff check tests/server/test_test_session_isolation.py` myself — F401 confirmed. The rule-checker's VERIFIED is overruled by direct tool evidence.

### Devil's Advocate

Argue this is broken. First, the obvious: it ships a lint failure. Anyone running `just check-all` before merge eats a red `ruff` and the "clean branch" claim evaporates — exactly the kind of "tests pass so it's fine" trap the adversarial pass exists to catch. Beyond that: the predicate is a bare prefix match duplicated in two languages with no shared contract test. The day someone introduces a *real* world whose slug legitimately begins with `test-` (a `test-chamber` dungeon, a world literally named "Test of the Gods"), this silently erases that real session from the entire GM dashboard — picker, State tab, and auto-follow all — and the operator has no signal it happened (no "N sessions hidden" affordance). The classification is a guess dressed as a rule; "loud, explicit classification — not a guess" is aspirational, because a prefix collision is invisible. Second: `bind_session_slug` is a process-global/ContextVar; a test harness that binds `test-foo` and forgets to clear it could, in a shared dev server, tag a subsequent *real* session's events as test and hide them — the fixture clears it, but production binding discipline isn't tested. Third: the negative-control assertion genuinely under-tests — if a future refactor tags real sessions `session_type="live"`, the suite stays green while the dashboard starts dropping real sessions whose pin filter keys on key-presence. Fourth: the `autoSlug` now returns `null` when every visible session is filtered out — if a developer is ONLY running test sessions (common!), the dashboard auto-follows *nothing* and looks dead; is that the intended UX, or should there be a "test sessions hidden — show anyway" escape hatch? None exists. None of these except the lint failure block this story (the slug-collision and escape-hatch concerns are genuine but out of scope — worth a follow-up finding), but they're the seams a malicious or confused user would hit. The lint failure is the one that's real, today, and blocking.

**Handoff:** Back to TEA (Amos Burton) — the blocking F401 and the test-hardening fixes are all in the test file (test-design rework).

---

## Subagent Results — Re-Review (round-trip 1)

Rework touched ONLY the two test files (server +30/-4, ui +6/-3); production code byte-identical to the prior clean pass. All four enabled specialists re-run on the current diff.

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | F401 GONE; server 28/28, ui 12/12, tsc 0 | confirmed: blocking item resolved |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 2 (both low/dismissed) | all 5 prior findings verified fixed; 2 new dismissed (see below) |
| 5 | reviewer-comment-analyzer | Yes | clean | none | N/A |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 1 (low/pre-existing) | dismissed (see below) |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 0 confirmed blocking; 3 dismissed (all low / pre-existing / evidence-refuted)

Dismissals (with evidence):
- [TEST] sessionless-infra test may hit the DB → **DISMISSED**: both persist paths guard `if sink is None: return` (`watcher_hub.py:523, 605`) and `bind_event_store(None)` nulls the sink; ran the test in isolation with no `pool`/DB fixture → 1 passed. DB-free, proven.
- [TEST] tautological `not.toBe` negatives in the auto-follow test (lines 448-449) → **DISMISSED**: low/cosmetic, pre-existing (not introduced by rework); the preceding `waitFor(...toBe(REAL))` is the real assertion. Harmless documentation.
- [TYPE] `driveEvent!` non-null assertion (ui test) → **DISMISSED**: low, pre-existing project idiom (identical in `useLiveSource-session-scope.test.tsx`), produces a loud crash not a silent wrong pass; not introduced by this rework.

### Reviewer (audit) — re-review confirmation
All five deviation stamps from round 1 stand; the rework added NO new deviations (test-hardening only, per my findings). Re-confirmed ACCEPTED.

## Reviewer Assessment — Re-Review (round-trip 1)

**Verdict:** APPROVED

The sole blocking item from round 1 — the F401 unused `UTC` import failing `ruff check .` — is fixed (`from datetime import datetime`; preflight confirms "All checks passed"). Every prior finding was addressed correctly: the two negative controls now assert key-absence (`"session_type" not in …`); the bump test uses a real-style slug proving the read-only fix is universal; new infix-`test-` and sessionless-`None` guards were added; the UI event-stream test now drives `tool-test`. The three notes raised this round are all low-severity and either pre-existing or refuted by evidence (see dismissals). No Critical/High issues remain.

**Specialist findings incorporated:**
- `[TEST]` reviewer-test-analyzer — verified all 5 prior findings fixed; 2 new notes (tautological negatives 448-449; sessionless-infra DB concern) both dismissed as low/pre-existing/evidence-refuted (sink-None guards `watcher_hub.py:523,605` + isolated test pass).
- `[DOC]` reviewer-comment-analyzer — clean: all four new/changed test comments (real-style-slug rationale, key-ABSENT contract, infix + sessionless docstrings, "both prefixes via the stream") accurately describe the code.
- `[RULE]` reviewer-rule-checker — clean on the rework: PY-10 import hygiene now passes (no unused `UTC`), PY-6/TS-8 test quality clean; the one `[RULE]`/`[TYPE]` note (`driveEvent!` non-null assertion) is low-severity and a pre-existing project idiom, not introduced here — dismissed.

**Data flow re-traced:** unchanged from round 1 — read path is `resolve_session_id` + direct `PgSaveRepository` (no `ensure_session`, no bump); broadcast path tags `session_type="test"` envelope-only for test slugs. Both proven by the now-stronger suite (server 28/28, ui 12/12).
**Pattern:** filter-at-returned-view / lossless-reducer (ui) and envelope-broadcast-only tag (server) — consistent with existing code.
**Error handling:** per-slug `try/except … logger.warning … continue` (`rest.py:461`) intact; No-Silent-Fallbacks-compliant.
**Lint/type:** `ruff check` clean (whole changed set), `tsc --noEmit` exit 0.

Round-trip 1 of 3 — resolved cleanly. The branch is mergeable.

**Handoff:** To SM (Camina Drummer) for finish-story.