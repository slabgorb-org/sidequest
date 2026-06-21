# Story 125-9: Test-Run Session Isolation Root Fix

**ID:** 125-9  
**Type:** refactor  
**Points:** 5  
**Workflow:** tdd (phased)  
**Repos:** server  
**Status:** backlog  

---

## Problem Statement

The headless test harness drives the same `:8765` live server, so every test session registers with the process-global `watcher_hub` singleton (ADR-132). Under ADR-122's never-evict policy, these test-\* sessions linger forever — only a server restart clears them. This pollutes the operator's live GM dashboard picker, pushing real sessions off-screen and interfering with auto-follow tracking.

**Related:** 126-34 (already merged) shipped the *downstream* mitigation (filter test sessions at the dashboard in `useLiveSource.ts` + tag broadcast envelopes `session_type="test"` in `watcher_hub.publish_event`). 125-9 is the *upstream root fix*.

---

## Design Decision (Architect / Keith)

**Decision: BOTH flag and separate port.**

### (a) SIDEQUEST_NO_WATCHER flag / --no-watcher mode

Add a server startup flag that no-ops `bind_loop` and `publish` in the WatcherHub. The hub already drops events when no loop is bound, so this leverages existing behavior. **This is the DEFAULT for most test suites** — simpler than spinning a second port.

**Implementation anchor:** `sidequest/telemetry/watcher_hub.py` — the singleton's `bind_loop()` and `publish_event()` methods already guard on loop presence; a `--no-watcher` flag/env var that skips `bind_loop` entirely makes the hub a no-op sink for the entire session.

### (b) Separate port/process path for span-asserting tests

For test suites that **assert on OTEL spans** (integration tests), point them at a separate port/process so they get a real, isolated watcher. The span-assertion suite needs real events; --no-watcher loses visibility.

**Trade-off:** --no-watcher is OPT-IN per test suite, never global. Default to --no-watcher for isolated unit tests; use separate-port for integration suites that validate span behavior.

---

## Key Files (Reuse Anchors for Next Agent)

- **sidequest/telemetry/watcher_hub.py** — process-global singleton; `bind_loop()`/`publish_event()` paths; already no-ops when no loop is bound.
- **sidequest/server/server.py** (or entry point) — startup flag parsing; where to bind the WatcherHub loop.
- **tests/conftest.py** / test runner harness — where to inject `--no-watcher` or route to separate port.
- **ADR-132** — WatcherHub Infrastructure; ContextVar per-session isolation; the hub's behavior with no loop.
- **ADR-122** — SessionRoom Lifecycle; never-evict policy explaining why test-\* sessions persist.
- **126-34 wiring:** `is_test_session()` predicate in `watcher_hub.py` — do NOT duplicate/regress.

---

## Acceptance Criteria

### AC#1: --no-watcher flag prevents bind_loop call
- [ ] Add `SIDEQUEST_NO_WATCHER` env var or `--no-watcher` CLI flag to server startup.
- [ ] When set, server skips `watcher_hub.bind_loop()` during initialization.
- [ ] Verify: with --no-watcher, a test session runs and `publish_event()` is a no-op (no events reach the live hub).
- [ ] OTEL wiring test: confirm no spans appear in the live operator's GM panel when a --no-watcher session runs in parallel with a real session.

### AC#2: Default test harness uses --no-watcher
- [ ] pytest configuration (conftest.py or setup) sets `SIDEQUEST_NO_WATCHER=1` for the default test suite.
- [ ] Verify: `just server-test` runs with --no-watcher by default; test sessions do NOT accumulate in the live hub.
- [ ] After a test run, the live operator's session list (via GM panel) shows no `test-*` sessions.

### AC#3: Separate-port path for span-asserting suites (IN SCOPE — Keith chose "Both")
- [ ] Implement a separate-port/process path so OTEL-asserting integration suites spawn an isolated real server (e.g., `:8766`) with a live WatcherHub that never touches the operator's `:8765` hub.
- [ ] A pytest fixture (or harness mode) allocates the port, starts the isolated server process, and tears it down — span-asserting suites use this path INSTEAD of `--no-watcher`.
- [ ] Document the trade-off: `--no-watcher` (AC#2) is the default for unit/functional suites; separate-port (this AC) is opt-in for the suites that assert on spans, because `--no-watcher` kills span visibility.
- [ ] Wiring test: a span-asserting test on the separate-port server emits and reads back real spans, while the operator's `:8765` hub records nothing from it.

### AC#4: No regression: is_test_session() remains stable
- [ ] Verify the 126-34 `is_test_session()` predicate (watcher_hub.py) is NOT modified or duplicated.
- [ ] Wiring test: confirm that even with --no-watcher, a `test-*`-prefixed session is still correctly identified as a test (the predicate remains valid for filtering at the dashboard layer).

### AC#5: OTEL principle satisfied — span isolation verified
- [ ] RED test: mock test run with --no-watcher; assert no watcher events emitted (publish is no-op).
- [ ] GREEN test: real test suite run; measure live hub before and after; confirm zero accumulation of test-\* sessions.
- [ ] Wiring test (integration): spin a real --no-watcher server + a real full server in parallel; inject a game session into the full server; confirm the full server's GM panel shows the real session only, not the test-run sessions.

---

## Doctrine / OTEL Principle

Per CLAUDE.md: every test suite needs a wiring test. The --no-watcher flag must be an **explicit, classified mode**, not a guessed default. This story's RED phase must:

1. **Prove (a) isolation:** with --no-watcher, test events do NOT reach the live hub (`publish` is a no-op / loop is unbound).
2. **Prove (b) opt-in:** the flag must be intentional, not silent. Tests that need OTEL visibility opt out via the separate-port path (AC#3, in scope this story).
3. **Prove (c) wiring:** the real test harness actually uses the flag (integration test against real pytest configuration).

---

## Related ADRs & Stories

- **ADR-132** — WatcherHub Infrastructure; process-global singleton; ContextVar per-session isolation.
- **ADR-122** — SessionRoom Lifecycle; never-evict policy.
- **126-34** — Downstream mitigation (MERGED); filter test sessions at dashboard + tag envelopes.
- **Epic 125** — Test isolation / daemon / tooling improvement stories.
