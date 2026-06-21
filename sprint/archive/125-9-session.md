---
story_id: "125-9"
jira_key: ""
epic: "125"
workflow: "tdd"
---
# Story 125-9: [126-34 follow-up] Test-run session isolation root fix — point test runs at a separate port / --no-watcher mode so they never register with the operator's live WatcherHub

## Story Details
- **ID:** 125-9
- **Jira Key:** (none — Jira disabled for this project)
- **Workflow:** tdd (phased)
- **Points:** 5
- **Type:** refactor
- **Repos:** server
- **Assignee:** Keith
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-21T11:27:19Z

> **Phase re-opened finish → red (SM manual repair, 2026-06-21):** user requested the OTLP-preserve fix BEFORE merge (see "SM (finish) — Rework Requested" at end of file). `pf workflow fix-phase` is forward-only, so the phase line was repaired by hand. Not merged. Re-running red(TEA) → green(Dev) → review(Reviewer) → finish(SM).

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-21T08:30:18Z | - | - |
| red→green→review→approved (round 1) | 2026-06-21T08:30 | 2026-06-21T09:01 | — |
| red | 2026-06-21T09:05:00Z | 2026-06-21T11:21:56Z | 2h 16m |
| green | 2026-06-21T11:21:56Z | 2026-06-21T11:23:49Z | 1m 53s |
| review | 2026-06-21T11:23:49Z | 2026-06-21T11:27:19Z | 3m 30s |
| finish | 2026-06-21T11:27:19Z | - | - |

## Technical Approach

### Root Cause
Test-run sessions (prefixed `test-*` and `tool-test`) register with the process-global `watcher_hub` singleton (ADR-132) because the headless test harness drives the same `:8765` server as the live operator. Under ADR-122's never-evict policy, these sessions linger forever (41 stale `test-*` sessions observed; only a server restart clears them), polluting the operator's GM dashboard picker.

**Related work:** 126-34 shipped a *downstream* mitigation — filter test sessions at the dashboard (`useLiveSource.ts`) and tag broadcast envelopes `session_type="test"` (watcher_hub.py). That story verified the predicate `is_test_session()` and proved the filtering wiring.

**This story is the *upstream root fix*:** stop test sessions reaching the live hub at all.

### Design Decision (Architect / Keith)

**Decision: BOTH flag and separate port — both IN SCOPE for 125-9** (Keith, this session; resolves the captured "Decision needed: flag vs. separate-port vs. both" to *both*). Do not narrow this to flag-only.

#### (a) SIDEQUEST_NO_WATCHER flag / --no-watcher mode (DEFAULT for most suites)

Add a server startup flag that no-ops WatcherHub operations. The hub already drops events when no loop is bound (`watcher_hub.py:publish_event()` early-returns if loop is `None`); a `--no-watcher` flag that skips `bind_loop()` entirely makes the hub inert for the whole session.

**This is the DEFAULT for most test suites** — simpler than a second port.

**Implementation anchors:**
- `sidequest/telemetry/watcher_hub.py` — singleton; `bind_loop()` and `publish_event()` already guard on loop presence.
- Server startup (likely `sidequest/server/server.py` or uvicorn entry) — where to check the flag and conditionally bind.
- `tests/conftest.py` or test runner harness — inject `SIDEQUEST_NO_WATCHER=1` for pytest runs.

#### (b) Separate port/process for span-asserting integration suites (IN SCOPE for 125-9)

For test suites that **assert on OTEL spans**, point them at a separate port/process (e.g., `:8766`) so they get a real, isolated watcher that never touches the operator's `:8765` hub. Span-asserting tests need real events; `--no-watcher` kills visibility, so those suites use this path instead.

**Trade-off:** `--no-watcher` is opt-in per test suite, never global. Default unit/functional tests to `--no-watcher` (a); span-asserting integration suites use the separate-port server (b). Both are built in this story; the cost (port allocation, separate process lifecycle in a fixture) is accepted, not deferred.

### Key Files (Reuse Anchors)

- **sidequest/telemetry/watcher_hub.py** — singleton `bind_loop()` / `publish_event()` paths; already no-ops when loop is `None`.
- **sidequest/server/server.py** (or entry point) — startup flag parsing and WatcherHub initialization.
- **tests/conftest.py** — pytest fixture/setup where to inject `SIDEQUEST_NO_WATCHER=1`.
- **ADR-132** — WatcherHub Infrastructure; ContextVar per-session isolation.
- **ADR-122** — SessionRoom Lifecycle; never-evict policy.
- **126-34** — Downstream mitigation (merged); do NOT regress `is_test_session()` predicate.

### Acceptance Criteria

#### AC#1: --no-watcher flag prevents hub binding
- [ ] Add `SIDEQUEST_NO_WATCHER` environment variable or `--no-watcher` CLI flag to server startup.
- [ ] When set, server skips `watcher_hub.bind_loop()` during initialization.
- [ ] WatcherHub `publish_event()` is a no-op (early returns) when loop is `None`.
- [ ] RED test: mock a --no-watcher session and assert `publish_event()` never calls the broadcast sink.

#### AC#2: Pytest uses --no-watcher by default
- [ ] `tests/conftest.py` sets `SIDEQUEST_NO_WATCHER=1` (or server fixture injects the flag) for the default pytest suite.
- [ ] RED test: verify the flag is injected for `just server-test` runs.
- [ ] GREEN test: run the full server suite; confirm zero `test-*` sessions accumulate in the live hub (if a real hub is present, they never reach it).

#### AC#3: Wiring test — real test harness isolation
- [ ] Integration test: spin a real --no-watcher server in pytest; spawn a real server with WatcherHub enabled in parallel (e.g., on a different port in a fixture or background process).
- [ ] Inject a game session into the real server; verify the real server's hub/GM panel shows the session.
- [ ] Verify the --no-watcher server's sessions do NOT appear in the real hub (even if somehow they try to register, they're silently dropped by the no-op loop).
- [ ] **OTEL principle:** this wiring test IS the "lie-detector" for the flag — prove isolation end-to-end.

#### AC#4: is_test_session() predicate remains stable (126-34 carve-out)
- [ ] Verify no modification or duplication of the `is_test_session()` predicate (watcher_hub.py).
- [ ] Confirm 126-34's downstream dashboard filter still works (the predicate is the source of truth for test-session identification).
- [ ] RED test: assert `is_test_session("test-foo")` and `is_test_session("tool-test-bar")` return `True`; `is_test_session("game-real")` returns `False`.

#### AC#5: Separate-port path for span-asserting suites (IN SCOPE — Keith chose "Both")
- [ ] Implement a separate-port/process path (pytest fixture or harness mode) that starts an isolated real server (e.g., `:8766`) with a live WatcherHub, and tears it down after the suite.
- [ ] Span-asserting integration suites route to this path INSTEAD of `--no-watcher` — they emit and read back real spans on the isolated server.
- [ ] Wiring test: a span-asserting test on the separate-port server reads back its own real spans, while the operator's `:8765` hub records nothing from it (no cross-contamination either direction).
- [ ] Trade-off documented: `--no-watcher` (AC#2) is the default for unit/functional suites; separate-port (this AC) is the opt-in for suites that assert on spans, because `--no-watcher` kills span visibility.
- [ ] No silent fallbacks: both the flag and the separate-port routing must be explicit and classified, never guessed.

---

## Delivery Findings

_Setup: no upstream findings._

### TEA (test design)
- **Gap** (non-blocking for the server scope; blocking for "Both" to work end-to-end): the separate-port half of "Both" needs a cross-repo follow-up. The server already runs on any port (`uvicorn --port 8766`) and `scripts/playtest.py` already accepts `--server ws://localhost:8766/ws` — but NOTHING points the headless harness (playtest driver / understudy) at a separate watcher-live port by default, so 125-9 delivers only the server-side `--no-watcher` flag while the separate-port path stays a manual invocation. Affects `scripts/playtest.py` (orchestrator) + `sidequest-understudy` (harness invocation/config) — file a follow-up story. *Found by TEA during test design.*
- **Question** (non-blocking): AC#2's premise ("pytest defaults to `--no-watcher`") guards a near-non-problem. pytest runs in its OWN process with its OWN builtins-pinned `watcher_hub` singleton, so it never reaches the operator's `:8765` hub; the real polluters are the WebSocket-driven harness runs (`just playtest` / understudy). The flag's primary consumer is the harness, not pytest. Dev should weigh whether a global conftest `SIDEQUEST_NO_WATCHER=1` is worth it (it's harmless — the `*_otel_wiring` integration tests call `bind_loop` directly via `watcher_setup`, bypassing the startup gate). Affects `tests/conftest.py` vs `scripts/`+understudy. *Found by TEA during test design.*
- **Improvement** (non-blocking): `--no-watcher` must disable LOUDLY (No Silent Fallbacks) — Dev should emit a startup log line (e.g. `watcher.disabled reason=SIDEQUEST_NO_WATCHER`) when the flag skips wiring, so an operator who accidentally booted the live server with the flag set sees WHY the dashboard is deaf. Affects `sidequest/server/app.py` `_wire_watcher`. *Found by TEA during test design.*
- **Improvement** (non-blocking): `test_no_watcher_startup_wiring.py` drives the real `create_app()` lifespan (opens the PG pool), so it SKIPS unless `SIDEQUEST_TEST_DATABASE_URL` is set — like every `migrated_db` test. RED was verified with `SIDEQUEST_TEST_DATABASE_URL=postgresql://slabgorb@localhost:5432/sidequest`. Affects test/CI invocation. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking, pre-existing — NOT introduced by 125-9): `tests/server/test_app.py::test_create_app_uses_build_llm_client_by_default` fails on clean HEAD (verified via `git stash`) — it `monkeypatch.setattr`s `sidequest.agents.llm_factory.build_async_anthropic`, which no longer exists (only a comment references it). Stale test vs. a removed factory function. Affects `tests/server/test_app.py` (re-point to the current SDK construction site) + matches the known `build_async_anthropic` hermeticity baseline. *Found by Dev during implementation.*

### Reviewer (code review)
- **[SILENT]/[DOC] Improvement** (non-blocking, MEDIUM): the `_wire_watcher` early-return skips `init_tracer()` (app.py:212) too — and `init_tracer()` is the SOLE production caller (verified `grep init_tracer sidequest/`), so it ALSO registers the OTLP exporter (`SIDEQUEST_OTLP_ENDPOINT`) + console exporter. Consequence: `SIDEQUEST_NO_WATCHER=1` silently disables ALL OTEL export, not just the GM-dashboard hub the flag names — and the "Loud, not silent" comment + the `watcher.disabled` INFO line name only the GM dashboard, so an operator who boots with both `SIDEQUEST_NO_WATCHER=1` and `SIDEQUEST_OTLP_ENDPOINT` set gets a silently-dark Jaeger with no log. Matches the load-bearing No-Silent-Fallbacks rule, so confirmed (not dismissed); MEDIUM because it's observability-only (no functional break), the bite is a live-server misconfiguration outside the flag's harness-isolation intent, and the flag's primary use (harness runs, no OTLP endpoint) is unaffected. **Cheap fix (recommended follow-up or quick rework if the user wants it pre-merge):** call `init_tracer()` BEFORE the early return and skip only `bind_loop` + the `WatcherSpanProcessor` registration — that disables the GM-dashboard hub (the flag's actual scope) while preserving OTLP/console; at minimum, extend the `watcher.disabled` log to name that OTLP export is also off. **Design question for the user:** should `--no-watcher` mean "no GM-dashboard hub" (preserve OTLP) or "no observability at all" (current behavior)? Affects `sidequest/server/app.py` `_wire_watcher`. *Found by Reviewer during code review (corroborated by reviewer-silent-failure-hunter).*

## Design Deviations

_Setup: none._

### TEA (test design)
- **Separate-port path tested as the opt-in/default-live contract, not a new server port flag**
  - Spec source: context-story-125-9.md AC#5; session AC#5
  - Spec text: "Implement a separate-port/process path (pytest fixture or harness mode) that starts an isolated real server (e.g., :8766)…"
  - Implementation: no new server-repo port code/fixture written. The separate-port mechanism already exists end-to-end (`uvicorn --port` boots any port; `scripts/playtest.py --server ws://localhost:8766/ws` already targets it). The server-repo's contribution to path (b) is the OPT-IN / default-live guarantee, tested by `test_watcher_live_by_default_when_flag_unset` (the watcher stays fully wired unless the flag is explicitly set).
  - Rationale: building a redundant `SIDEQUEST_PORT` server flag would have NO consumer (`just server` + the harness do not call `app.main()`), violating No-Stubbing / TDD-against-real-consumers. The genuine cross-repo wiring is out of this server-only story's repo scope — logged as a Delivery Finding.
  - Severity: major
  - Forward impact: the separate-port half of "Both" is satisfied by existing infra + a cross-repo config follow-up (orchestrator + understudy), not by new server code.
- **AC#2 (pytest defaults to `--no-watcher`) — no dedicated test written**
  - Spec source: context-story-125-9.md AC#2; session AC#2
  - Spec text: "pytest configuration (conftest.py or setup) sets `SIDEQUEST_NO_WATCHER=1` for the default pytest suite."
  - Implementation: omitted. Asserting `os.environ["SIDEQUEST_NO_WATCHER"] == "1"` is circular (it tests the test-harness env, not product behavior), and the finding above shows pytest doesn't pollute the operator's hub, so the AC guards a near-non-problem. The MECHANISM (predicate + startup gate) is fully covered; whether pytest opts in by default is a low-value config decision for Dev/review.
  - Severity: minor
  - Forward impact: if Dev sets the conftest env, no test pins it; the predicate + startup-gate tests still pass either way.
- **AC#4 (is_test_session stability) covered by existing tests, not a new one**
  - Spec source: context-story-125-9.md AC#4; session AC#4
  - Spec text: "Verify the 126-34 `is_test_session()` predicate is NOT modified or duplicated."
  - Implementation: no new predicate test. `tests/server/test_test_session_prefix_contract.py` (125-10, with a cross-repo tripwire) and `tests/server/test_test_session_isolation.py` (126-34) already lock the predicate + its prefix set. My no-watcher work must keep them green; Dev must not touch `_TEST_SESSION_SLUG_PREFIXES` / `is_test_session`.
  - Severity: minor
  - Forward impact: none — the existing guard is the regression net.

### Dev (implementation)
- **AC#2 (pytest defaults to `--no-watcher`) — not implemented**
  - Spec source: context-story-125-9.md AC#2; session AC#2
  - Spec text: "pytest configuration (conftest.py or setup) sets `SIDEQUEST_NO_WATCHER=1` for the default pytest suite."
  - Implementation: did NOT add a global `SIDEQUEST_NO_WATCHER=1` to `tests/conftest.py`. No test requires it (minimalist discipline), and TEA's finding shows the AC guards a near-non-problem — pytest runs in its own process with its own `watcher_hub` singleton, so it never reaches the operator's `:8765` hub. A global suite-wide env flip is a broad, untested behavior change; the watcher mechanism (predicate + startup gate) is what actually matters and is fully covered.
  - Rationale: avoid an untested global change of dubious value; the real `--no-watcher` consumer is the headless harness, addressed by the flag itself.
  - Severity: minor
  - Forward impact: AC#2 effectively deferred; if the user wants pytest to default to no-watcher, it's a one-line conftest follow-up (the predicate + gate already support it).

### Reviewer (audit)
- **TEA: Separate-port path tested as opt-in/default-live contract, not a new server port flag** → ✓ ACCEPTED by Reviewer: sound. Verified the harness already targets a configurable URL (`scripts/playtest.py` `--server`, default `ws://localhost:8765/ws`, line 1170-1176) and the server runs on any port via `uvicorn --port`. Building a `SIDEQUEST_PORT` server flag with no production consumer would be a stub. The opt-in/default-live guarantee IS the server's contribution and is tested (`test_watcher_live_by_default_when_flag_unset`). The genuine cross-repo "point the harness at :8766 by default" gap is correctly logged as a Delivery Finding for a follow-up — confirm that scoping is acceptable to the user.
- **TEA: AC#2 no dedicated test** → ✓ ACCEPTED: a `assert os.environ[...]=="1"` test is circular; the mechanism (predicate + startup gate) is what carries behavior and is covered.
- **TEA: AC#4 covered by existing tests** → ✓ ACCEPTED: verified `is_test_session` / `_TEST_SESSION_SLUG_PREFIXES` are untouched in the diff; `test_test_session_prefix_contract.py` (cross-repo tripwire) + `test_test_session_isolation.py` remain the regression guard and pass (preflight: green).
- **Dev: AC#2 not implemented** → ✓ ACCEPTED with a note: consistent with TEA's analysis (pytest runs in its own process/hub and never pollutes the operator's `:8765` hub, so the AC guards a near-non-problem). **Net effect: AC#2 is fully deferred (no test + no impl).** Sound for this story, but the user should be aware AC#2 was dropped — it's a one-line conftest follow-up if wanted.
- **Reviewer (undocumented):** the `--no-watcher` flag silently disables OTLP/console export beyond the GM-dashboard hub it names (skips `init_tracer`). Logged as a Reviewer Delivery Finding above (MEDIUM, non-blocking). Severity: M.

## TEA Assessment

**Tests Required:** Yes

**Test Files:**
- `tests/server/test_no_watcher_mode.py` — flag predicate `no_watcher_enabled()`: live env read, exact-`"1"` match, no fuzzy truthiness (4 cases incl. a 7-value parametrize).
- `tests/server/test_no_watcher_startup_wiring.py` — real `create_app()` lifespan: with `SIDEQUEST_NO_WATCHER=1` the hub loop is NOT bound and a publish drops (the lie-detector); control proves the watcher is LIVE by default (opt-in for the separate-port path).

**Tests Written:** 12 (incl. parametrize) covering ACs #1, #3, #5; AC#2/#4 addressed via deviations (see above).
**Status:** RED — verified 11 failed, 1 passed (the opt-in control is green-now by design).

RED proof (run with `SIDEQUEST_TEST_DATABASE_URL=postgresql://slabgorb@localhost:5432/sidequest`):
- predicate tests → `AttributeError: no_watcher_enabled` (feature missing).
- `test_no_watcher_flag_skips_loop_binding_at_startup` → `assert <_UnixSelectorEventLoop running=True> is None` (startup binds unconditionally today — the missing gate).
- `test_watcher_live_by_default_when_flag_unset` → PASS (control / opt-in guard).
- `ruff check` + `ruff format --check` clean on both files (avoided the 126-34 F401 gate trap).

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| CLAUDE.md No Silent Fallbacks | `test_no_watcher_enabled_false_for_non_exact_1`, `…is_read_live_not_cached_at_import` | failing |
| CLAUDE.md No Source-Text Wiring Tests | `test_no_watcher_flag_skips_loop_binding_at_startup` (real lifespan + runtime-state + behavior) | failing |
| CLAUDE.md Every-suite-needs-a-wiring-test | `test_no_watcher_flag_skips_loop_binding_at_startup` | failing |
| CLAUDE.md OTEL lie-detector | publish-drops assertion (no broadcast while disabled) | failing |
| python.md #6 Test quality | all tests — meaningful asserts, no vacuous `is_none`/`assert True` | failing/green |
| python.md #9 Async/await | loop-bind + `run_coroutine_threadsafe` publish exercised via real lifespan | failing |
| python.md #10 Import hygiene | `ruff check` clean (no F401 — the 126-34 trap) | green |
| python.md #13 Fix-introduced regressions | opt-in control + existing `is_test_session` contract guard | green |

**Rules checked:** 8 of 13 python.md checks applicable; the rest (mutable defaults, path handling, resource leaks, deserialization, dependency hygiene) don't apply to a boolean env-flag + startup gate.
**Self-check:** 0 vacuous tests written.

**Handoff:** To Dev (Inigo Montoya) for GREEN — add `no_watcher_enabled()` to `watcher_hub.py` (live env read, exact-`"1"`), and gate `_wire_watcher` in `app.py` on it (skip `bind_loop` + span-processor registration, log the disable loudly). Do NOT touch `is_test_session` / `_TEST_SESSION_SLUG_PREFIXES`.

---

## Dev Assessment

**Implementation Complete:** Yes (AC#1, #3, #5 in code; AC#2 deviated — see Design Deviations; AC#4 = no-op, predicate untouched)

**Files Changed:**
- `sidequest/telemetry/watcher_hub.py` — new `no_watcher_enabled()` predicate (live `os.environ` read, exact-`"1"` match), placed beside `_watcher_as_spans_enabled()`. No change to `is_test_session` / `_TEST_SESSION_SLUG_PREFIXES`.
- `sidequest/server/app.py` — import `no_watcher_enabled`; gate the `_wire_watcher` startup handler on it: when set, log `watcher.disabled reason=SIDEQUEST_NO_WATCHER …` and early-return BEFORE `bind_loop` and span-processor registration, so the hub stays inert (publish drops). Watcher fully wired when the flag is unset.

**Tests:** GREEN — 12/12 of the story's tests pass (`test_no_watcher_mode.py` + `test_no_watcher_startup_wiring.py`), run with `SIDEQUEST_TEST_DATABASE_URL=postgresql://slabgorb@localhost:5432/sidequest`. Regression batch: 18 passing across `test_startup_schema_guard_wiring`, `test_test_session_isolation` (126-34), `test_test_session_prefix_contract` (125-10). `pyright` 0 errors, `ruff check` + `ruff format --check` clean on both changed files.

**One pre-existing failure (NOT 125-9):** `test_app.py::test_create_app_uses_build_llm_client_by_default` fails identically on clean HEAD (verified via `git stash`) — stale monkeypatch of the removed `llm_factory.build_async_anthropic`. Logged as a Delivery Finding.

**Branch:** `feat/125-9-no-watcher-test-isolation` (pushed to `origin`, sidequest-server).

**Handoff:** To Reviewer (Westley) for code review. Key review notes: (1) the separate-port half of "Both" is delivered by existing infra + a logged cross-repo follow-up — confirm that scoping is acceptable; (2) AC#2 not implemented (deviation logged) — confirm pytest-default is genuinely low-value; (3) `_loop is None`/private-attr access in the wiring test is a deliberate runtime-state check, not a source-text grep.

---

## Notes for Next Agent (TEA)

### Test Design Guidance

1. **Flag injection is the critical wiring point.** The RED suite must prove the real pytest harness (via `conftest.py` or server fixture) actually injects `SIDEQUEST_NO_WATCHER=1` or the equivalent. A unit test that mocks the flag passing is not enough — you need an integration test that drives `just server-test` or a real pytest run and inspects the running server's state (e.g., via OTEL or the hub's internal loop ref).

2. **OTEL lies if the flag fails silently.** If a developer forgets to set the flag and the test suite runs with a live hub, test-\* sessions accumulate silently. The wiring test must measure this (before/after session count in the live hub, or the loop ref is `None` after startup).

3. **Separate-port is IN SCOPE (Keith chose "Both").** Write RED tests for BOTH paths: (a) the `--no-watcher` isolation (AC#1–#3) AND (b) the separate-port span-asserting path (AC#5). The separate-port RED test must prove a span-asserting suite reads back its own real spans on the isolated `:8766` server while the operator's `:8765` hub stays clean. Do not defer (b) to a future story.

4. **Reuse 126-34 predicate.** `is_test_session()` is already proven by 126-34's tests. Your job is to prove the flag *applies* it (i.e., the predicate filters test-\* slugs before they ever hit the hub). Don't re-test the predicate itself.

5. **No-op is verifiable.** Use a mock or spy on `watcher_hub.publish_event()` to prove it's a no-op (early return, never calls the sink). Or inspect the WatcherHub's internal loop ref and assert it's `None`.

---

## Related ADRs

- **ADR-132** — WatcherHub Infrastructure — builtins-Pinned Singleton, ContextVar Per-Session Isolation, and Ephemeral-Event Taxonomy
- **ADR-122** — SessionRoom Lifecycle — RoomRegistry Never-Evict Policy
- **ADR-090** — OTEL Dashboard Restoration after Python Port
- **126-34** — Downstream mitigation (MERGED); filter test sessions at dashboard + tag envelopes

---

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (6 informational confirmations) | N/A — GREEN 24/24 targeted, 0 smells, lint/format/pyright clean |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer (see [EDGE] below) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 (medium) | confirmed 1, dismissed 0, deferred 0 |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer (see [TEST] below) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer (see [DOC] below) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer (see [TYPE] below) |
| 7 | reviewer-security | Yes | clean | 0 | N/A — operator-controlled env, exact-match, no secret leak, no remote surface |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer (see [SIMPLE] below) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer Rule Compliance (see [RULE] below) |

**All received:** Yes (3 enabled returned, 6 disabled pre-filled)
**Total findings:** 1 confirmed (MEDIUM, non-blocking), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

A small, well-scoped diff: a live-read boolean env predicate (`no_watcher_enabled()`) mirroring the existing `_watcher_as_spans_enabled()`, and a single early-return gate in the `_wire_watcher` startup handler. Tests are behavior-based (real `create_app()` lifespan + runtime-state + publish-counter assertions), green, and lint/type clean. One genuine MEDIUM finding (silent OTLP disable) — confirmed, non-blocking, logged with a cheap fix + a design question for the user. No Critical/High.

**Data flow traced:** `SIDEQUEST_NO_WATCHER` (operator process env) → `no_watcher_enabled()` (`watcher_hub.py:89`, `== "1"`) → `_wire_watcher` startup gate (`app.py:200`) → early-return skips `bind_loop`/span-processor → `watcher_hub._loop` stays `None` → `WatcherHub.publish` drops every event (`watcher_hub.py:139`). Safe: env is operator-controlled, no remote/player path, exact-match keeps the watcher LIVE on any non-`"1"` value (loud-safe default).

**Observations (≥5):**
- `[VERIFIED]` Exact-`"1"` match is the loud-safe default — evidence: `watcher_hub.py:89` returns `os.environ.get(...) == "1"`; a typo (`true`) → `False` → watcher stays live. Complies with No-Silent-Fallbacks. Tested by `test_no_watcher_enabled_false_for_non_exact_1` (7 values).
- `[VERIFIED]` Gate covers BOTH bind_loop and span-processor — evidence: `app.py:200-206` returns before line 207 `bind_loop` AND before line 240 `add_span_processor`. Skipping only one would leak spans; the single early-return is correct (corroborated by preflight obs #2).
- `[SILENT]/[DOC]` **MEDIUM (confirmed, non-blocking):** the early-return also skips `init_tracer()` (`app.py:212`, the sole production caller), silently disabling OTLP/console export beyond the GM-dashboard hub the flag names; the "Loud, not silent" comment + `watcher.disabled` log mention only the dashboard. See Reviewer Delivery Finding + design question. Fix is ~2 lines.
- `[EDGE]` (my coverage, edge_hunter disabled) `uvicorn --reload` re-runs `_wire_watcher` on every reload; with the flag set it logs + returns each time — idempotent, no double-registration. The only odd edge (flag flipped mid-process after a prior bind) is not realistic — env vars are set before boot, read live at startup. Not a defect.
- `[TEST]` (my coverage, test_analyzer disabled) assertions are meaningful (loop-`None` + publish-counter deltas, not vacuous); the `_loop` access is a deliberate runtime-state check (`noqa: SLF001`), not a source-text grep — compliant with No-Source-Text-Wiring-Tests; `reset_hub_loop` correctly restores the builtins-singleton baseline before AND after (preflight obs #4). The control test is green-now by design (opt-in guard).
- `[TYPE]` (my coverage) `no_watcher_enabled() -> bool` — fully annotated, no stringly-typed surface, no unsafe cast.
- `[SIMPLE]` (my coverage) one-liner predicate + one early-return; no over-engineering, no dead code, no stub.
- `[SEC]` reviewer-security: clean — env is operator-controlled, no injection, no secret in the log (env-var NAME only), disabling one's own GM dashboard is not a privilege escalation (post-compromise only).

### Rule Compliance

Checked python.md (13 checks) + CLAUDE.md load-bearing rules against the diff (`[RULE]` — rule_checker disabled, done manually):
- **#1 silent exceptions:** none — the gate is a conditional early-return, not an exception swallow. ✓
- **#3 type annotations:** `no_watcher_enabled() -> bool` annotated (public, cross-module). ✓
- **#4 logging:** INFO level for a mode notice (correct — not an error path), static string (no f-string, lazy-safe), no secret/PII. ⚠ INCOMPLETE — names the GM dashboard but not OTLP (the MEDIUM finding). Compliant on level/secrets; the coverage gap is the finding.
- **#6 test quality:** meaningful asserts, no vacuous, no `@skip`, parametrize cases test distinct values. ✓
- **#9 async pitfalls:** gate is in an async startup handler; no blocking calls added; early-return before `bind_loop` is correct. ✓
- **#10 import hygiene:** `no_watcher_enabled` added to the existing `from sidequest.telemetry.watcher_hub import …` line; no star/circular (watcher_hub does not import app). ✓
- **#13 fix-introduced regressions:** the change introduces the `init_tracer`-skip side effect (the finding) but no broad-catch / wrong-type regressions. ✓
- **CLAUDE.md No-Silent-Fallbacks:** mostly upheld (loud-safe exact-match, INFO disable log) — except the OTLP collateral (the MEDIUM). Confirmed, downgraded to MEDIUM with rationale, NOT dismissed.
- **CLAUDE.md No-Stubbing / Don't-Reinvent:** upheld — no redundant `SIDEQUEST_PORT` flag invented; reuses existing `uvicorn --port` + harness `--server`. ✓
- **CLAUDE.md is_test_session untouched:** verified — diff does not touch `is_test_session` / `_TEST_SESSION_SLUG_PREFIXES`; contract test passes. ✓

### Devil's Advocate

Argue this is broken. The flag is named `SIDEQUEST_NO_WATCHER` and the story scope is "disable the WatcherHub so harness test sessions don't pollute the operator's GM dashboard." But the implementation reaches further than its name: by early-returning before `init_tracer()`, it silently turns off the ENTIRE OTEL export pipeline (OTLP→Jaeger and console), not just the GM-dashboard broadcast. An operator debugging a harness run who sets `SIDEQUEST_NO_WATCHER=1` to declutter the dashboard, while keeping `SIDEQUEST_OTLP_ENDPOINT` pointed at Jaeger to trace the run, gets a silently-dark Jaeger — and the one log line they'd grep for says only "GM dashboard receives no events," reinforcing the false belief that OTLP is unaffected. The code comment literally asserts "Loud, not silent," which is the precise property it fails to fully deliver; a reviewer who trusts comments would be misled. Worse, this is a project whose entire thesis is "OTEL is the lie detector" (SOUL.md) — a flag that silently disables OTEL export is doctrinally uncomfortable, even if the bite is a misconfiguration. What would a confused user do? Set the flag on the live `:8765` server (the comment even anticipates this), lose all telemetry, and not know why traces vanished. What about a stressed startup? If `init_tracer()` had been doing other load-bearing setup (it isn't — verified it only registers exporters), the skip could break unrelated subsystems; future code that assumes a real TracerProvider after startup would silently no-op. None of this is a crash or data loss, and the flag's intended use (harness runs without an OTLP endpoint) is unaffected — so it stays MEDIUM, not blocking. But it IS a real gap between the flag's name/comment and its behavior, and it earns the confirmed finding + the design question (no-GM-hub vs. no-observability-at-all) rather than a silent pass. Everything else withstands the attack: the exact-match predicate fails safe, the gate is idempotent under reload, the tests assert behavior not shape, and there is no remote/player attack surface on an operator-only env var.

**Handoff:** To SM (Vizzini) for finish-story. APPROVED with one MEDIUM non-blocking finding (silent OTLP disable) + a design question for the user (should `--no-watcher` preserve OTLP?). Two ACs deferred by design (AC#2 pytest-default; AC#5 separate-port = existing infra + cross-repo follow-up) — both logged and audited. The user should confirm those scoping calls and decide whether the MEDIUM fix lands now or as a follow-up.
---

## SM (finish) — Rework Requested (user decision 2026-06-21)

Story was APPROVED (non-blocking MEDIUM), but the user (Keith) ruled on the two open decisions at finish **before merge**:

1. **OTLP scope → "Preserve OTLP; fix before merge."** `--no-watcher` must mean "no GM-dashboard hub ONLY" — it must NOT disable OTLP/console export. Current code over-reaches: the `_wire_watcher` early-return skips `init_tracer()` (the sole OTLP/console exporter setup). **Required change (red→green rework):**
   - Restructure `_wire_watcher` so `init_tracer()` ALWAYS runs (OTLP/console preserved), and gate ONLY `watcher_hub.bind_loop()` + the `WatcherSpanProcessor` registration on `no_watcher_enabled()`.
   - Net behavior: flag set → watcher hub unbound (publish drops, GM dashboard dark) BUT OTLP/console export still live.
   - Fix the comment + `watcher.disabled` log to match (no longer claim/imply OTLP is off).
   - **NEW testable contract for TEA (red):** with `SIDEQUEST_NO_WATCHER=1` + real `create_app()` lifespan, the global tracer provider IS a real SDK `TracerProvider` (init_tracer ran / OTLP preserved) WHILE `watcher_hub._loop is None` (hub still disabled). Existing `test_no_watcher_flag_skips_loop_binding_at_startup` (loop None + publish drops) stays valid.

2. **"Both" leftovers → File a follow-up story.** Separate-port is existing infra (`uvicorn --port` + `playtest --server`); the cross-repo gap (point the harness at a separate watcher-live port by default) + AC#2 (pytest-default `--no-watcher`) go to a NEW epic-125 follow-up (orchestrator + understudy). **SM to file after the rework lands.**

**Routing:** red rework → TEA (Fezzik) for the OTLP-preserve test, then Dev (Inigo) green, then Reviewer (Westley) re-review, then SM finish. NOT merging now.

---

## TEA Assessment — Round 2 (OTLP-preserve rework)

**Tests Required:** Yes (1 new)
**New test:** `tests/server/test_no_watcher_startup_wiring.py::test_no_watcher_preserves_otlp_export_at_startup` — spies on `init_tracer` and asserts it STILL runs with `SIDEQUEST_NO_WATCHER=1` (OTLP/console preserved) while `watcher_hub._loop is None` (GM-dashboard hub still disabled). Spy chosen over a provider-type check because `set_tracer_provider` is once-per-process (sticky across tests → a type assertion would be vacuous).
**Status:** RED — verified `1 failed, 2 passed`. New test fails with `assert []` (round-1 `_wire_watcher` returns before `init_tracer`). Existing `test_no_watcher_flag_skips_loop_binding_at_startup` + `test_watcher_live_by_default_when_flag_unset` stay green. ruff/format clean.

**Design Deviations (round 2):** No new deviations. The OTLP-preserve behavior is now IN scope per the user's finish-phase decision (2026-06-21) and is the contract this test pins.

**Handoff:** To Dev (Inigo) — restructure `_wire_watcher` so `init_tracer()` runs unconditionally and ONLY `bind_loop` + the `WatcherSpanProcessor` registration are gated on `no_watcher_enabled()`; fix the comment + `watcher.disabled` log to stop implying OTLP is off.
---

## Dev Assessment — Round 2 (OTLP-preserve fix)

**Implementation Complete:** Yes
**File Changed:** `sidequest/server/app.py` — restructured `_wire_watcher`: `init_tracer()` now runs UNCONDITIONALLY (OTLP/console exporters always wired); only `watcher_hub.bind_loop()` + the `WatcherSpanProcessor` registration are gated on `no_watcher_enabled()`. Comment + `watcher.disabled` INFO log corrected ("GM-dashboard hub not wired … OTLP/console export unaffected"). Addresses the Reviewer MEDIUM (silent OTLP disable) per the user's decision.

**Design Deviations (round 2):** No deviations from spec.

**Tests:** GREEN — 13/13 no-watcher tests pass (incl. the new `test_no_watcher_preserves_otlp_export_at_startup`); regression batch 12/12 (`test_startup_schema_guard_wiring`, `test_test_session_isolation`, `test_test_session_prefix_contract`). `ruff check` + `ruff format --check` + `pyright` clean on `app.py`.
**Branch:** `feat/125-9-no-watcher-test-isolation` @ c40fa90f (pushed).

**Delivery Findings (round 2):** No new upstream findings.

**Handoff:** To Reviewer (Westley) for re-review of the OTLP-preserve restructure.
---

## Subagent Results — Round 2 (re-review of OTLP-preserve fix)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 | N/A — GREEN 25/25 targeted, 0 smells, ruff/format/pyright clean |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer below |
| 3 | reviewer-silent-failure-hunter | Yes | clean | 0 | round-1 MEDIUM RESOLVED; no new silent paths (init_tracer unconditional + idempotent + loud-fail) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled — domain covered by Reviewer below |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled — Reviewer verified comment/log now honest |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled — no type surface change |
| 7 | reviewer-security | Yes | clean | 0 | N/A — no new surface; OTLP endpoint log is pre-existing operator config |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled — reorder is simpler/correct, no over-engineering |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled — Reviewer rule pass below |

**All received:** Yes (3 enabled returned, 6 disabled pre-filled)
**Total findings:** 0 confirmed (round-1 MEDIUM resolved), 0 dismissed, 0 deferred

## Reviewer Assessment — Round 2

**Verdict:** APPROVED

The round-2 delta is exactly the prescribed fix and resolves my round-1 MEDIUM. `init_tracer()` now runs unconditionally (OTLP/console export preserved); only `bind_loop` + the `WatcherSpanProcessor` registration are gated on `no_watcher_enabled()`. The comment + `watcher.disabled` log are corrected to state OTLP/console is unaffected — the round-1 over-claim ([DOC]) is gone. New test pins the contract.

**Data flow traced:** `SIDEQUEST_NO_WATCHER=1` → `init_tracer()` runs (OTLP/console wired, real SDK provider) → `no_watcher_enabled()` true → early-return skips `bind_loop` + processor → hub `_loop is None` (GM dashboard dark) BUT OTEL export live. Flag unset → identical to pre-125-9 (init_tracer, bind_loop, processor registered).

**Observations:**
- `[SILENT]` round-1 MEDIUM RESOLVED — `init_tracer()` at app.py:197 precedes the gate at :207 (confirmed by silent-failure-hunter + my read). OTLP no longer silently disabled.
- `[DOC]` the "Loud, not silent" over-claim is fixed — log now reads "GM-dashboard hub not wired … OTLP/console export unaffected" (accurate).
- `[EDGE]` (my coverage) running `init_tracer()` in no-watcher mode is safe: it is `_initialized`-guarded (idempotent under `--reload`), and its missing-endpoint / half-wired branches `logger.warning` (loud), never swallow.
- `[TEST]` (my coverage) `test_no_watcher_preserves_otlp_export_at_startup` spies on `init_tracer` (robust vs. the sticky process-global provider) + asserts `_loop is None`; behavior-level, not a source grep. Round-1 tests (`flag_skips_loop_binding`, `live_by_default`) stay green — the hub-disabled contract is unchanged.
- `[TYPE]`/`[SIMPLE]` (my coverage) pure reorder of two statements; no type change, no added complexity, no dead code.
- `[SEC]` reviewer-security: clean — no new surface; the pre-existing OTLP-endpoint log is operator config, not a secret.
- `[RULE]` python.md re-pass on the delta: #1 no silent except, #4 logging level/secrets correct (now also complete), #9 async startup handler unchanged-safe, #10 imports clean, #13 no fix-introduced regression. CLAUDE.md No-Silent-Fallbacks now fully upheld.

### Rule Compliance (delta)
Re-checked the changed lines against python.md + CLAUDE.md: all compliant. The one round-1 gap (#4 logging coverage — log didn't name OTLP) is now closed. `is_test_session` / `_TEST_SESSION_SLUG_PREFIXES` remain untouched (AC#4 guard intact). No-Stubbing / No-Silent-Fallbacks: upheld.

### Devil's Advocate
Argue it's still broken. Could `init_tracer()` running in no-watcher mode cause harm the round-1 version avoided? It registers a `BatchSpanProcessor` exporter if `SIDEQUEST_OTLP_ENDPOINT` is set — a background thread/flush. In a short-lived harness run with no endpoint set (the common case) this is inert; with an endpoint set it does exactly what the operator asked (export traces) — which is the whole point of the fix. Idempotency holds via `_initialized`, so `--reload` won't stack exporters. Could the early-return now leave a half-initialized state? No — `init_tracer()` completes fully before the gate; the gate only skips hub binding. Does the spy test give false confidence? It asserts `init_tracer` is invoked, not that exporters flush — but exporter wiring is `init_tracer`'s own tested responsibility, and asserting the call is the correct seam for "did no-watcher preserve the OTLP setup path." The prior `_loop is None` + publish-drop contract is re-asserted, so the hub really is off. Nothing here regresses the isolation guarantee; the fix is net-strictly-better than round 1.

**Handoff:** To SM (Vizzini) for finish-story. APPROVED — round-1 MEDIUM resolved, no new findings, all gates green.

### Reviewer (audit) — Round 2
- **Dev (round 2): "No deviations from spec"** → ✓ ACCEPTED: verified — the change is the exact reviewer-mandated, user-approved fix; no scope drift.
- **TEA (round 2): "No new deviations"** → ✓ ACCEPTED: the OTLP-preserve contract is in-scope per the user's finish-phase decision and is correctly tested.