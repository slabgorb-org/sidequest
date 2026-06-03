---
story_id: "78-3"
jira_key: ""
epic: "78"
workflow: "tdd"
---
# Story 78-3: Daemon deferred observability — start_periodic_heartbeat (ADR-131) + detect_gpu/GpuInfo span (ADR-046) unwired: wire or cut

## Story Details
- **ID:** 78-3
- **Jira Key:** (not in use)
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 2
- **Type:** chore
- **Priority:** p3

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-03T15:23:51Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-03T14:51:25Z | 2026-06-03T14:53:25Z | 2m |
| red | 2026-06-03T14:53:25Z | 2026-06-03T15:01:09Z | 7m 44s |
| green | 2026-06-03T15:01:09Z | 2026-06-03T15:07:52Z | 6m 43s |
| spec-check | 2026-06-03T15:07:52Z | 2026-06-03T15:09:46Z | 1m 54s |
| verify | 2026-06-03T15:09:46Z | 2026-06-03T15:15:59Z | 6m 13s |
| review | 2026-06-03T15:15:59Z | 2026-06-03T15:22:37Z | 6m 38s |
| spec-reconcile | 2026-06-03T15:22:37Z | 2026-06-03T15:23:51Z | 1m 14s |
| finish | 2026-06-03T15:23:51Z | - | - |

## Summary

This is the **deferred-feature** lane of the 2026-06-02 `sq-wire-it` daemon wiring audit (epic 78). Two deferred-feature exports carry ADR lineage and require explicit finish-or-cut decisions:

1. **`start_periodic_heartbeat` (`media/daemon.py:155`) — ADR-131, status `live`.**
   - The 30s idle-heartbeat contract from ADR-131 Liveness (Contract 1)
   - Docstring says "NOT YET WIRED INTO `_run_daemon`"
   - Only test caller exists today; zero production callers
   - **Leans WIRE** — ADR-131 is live and names this as explicit follow-up
   - Wiring requires: schedule as background task in `_run_daemon`, implement broadcast emit to active client writers, cancel in shutdown

2. **`detect_gpu`/`GpuInfo` (`media/gpu_detect.py:25`) — ADR-046, status `retired`.**
   - GPU detection span that was meant to feed ADR-046's `ModelMemoryManager` budget coordinator
   - The coordinator **was deleted 2026-05-10** (commit `5118d6c`)
   - No production caller; only test references exist
   - **Does NOT clearly lean wire** — its parent coordinator is gone
   - Honest options: (a) CUT with ADR-046 deferral note, or (b) minimal WIRE as standalone boot diagnostic (if standalone value exists)

### Key Constraints

- **Wiring real heartbeat requires active-writer registry** — `_handle_client` doesn't currently track active writers for broadcast fan-out. This is the main architectural challenge for AC1.
- **GPU span parent ADR is retired** — the `ModelMemoryManager` it was designed to feed no longer exists. Don't treat ADR-046 as mandating wiring; it doesn't.
- **AC3 is the lie-detector** — if either is wired, the OTEL span-assertion test must prove the span fires on the *live path* in `_run_daemon`, not just isolated unit test. Existing `test_heartbeat_emit.py` and `test_otel_spans.py` satisfy unit-level proof but not live-path proof.
- **No stub-in-disguise** — a `start_periodic_heartbeat(emit=None)` scheduled with no-op emit would violate AC1's "idle-heartbeat emission verified" requirement. AC3's wiring test prevents that failure mode.

### Acceptance Criteria

**AC1:** `start_periodic_heartbeat` — scheduled in `_run_daemon` as background task AND idle-heartbeat emission verified, OR removed with ADR-131 deferral note.

**AC2:** `detect_gpu`/`GpuInfo` — called at daemon warmup so GPU-detection span fires in production, OR removed with ADR-046 deferral note.

**AC3:** If wired — OTEL span-assertion test proves heartbeat/GPU span fires on live path (not just isolated unit test).

## Delivery Findings

No upstream findings.

<!-- findings appended below -->
### TEA (test design)
- **Conflict** (non-blocking): The CUT-path ADR-deferral note (AC1/AC2) lands in the
  **orchestrator repo** (`docs/adr/ADR-131*`, `docs/adr/ADR-046*`), but the session
  REPOS scope is `daemon` only. The deletion + orphaned-test removal is a daemon-repo
  PR; the two ADR amendments are a separate orchestrator-repo change. Dev must produce
  both. Affects `docs/adr/` (amend ADR-131 Consequences = periodic emitter deferred;
  one-line ADR-046 note that the orphaned `gpu.detect` diagnostic followed the
  `ModelMemoryManager` coordinator out, 2026-05-10). *Found by TEA during test design.*
- **Improvement** (non-blocking): Removing `start_periodic_heartbeat` also orphans the
  `Callable`/`Awaitable` imports in `media/daemon.py:29` (their only use is its
  signature). `just daemon-lint` (ruff F401) will catch the unused imports — no pytest
  guard needed, but Dev should clear them in the same commit. Affects
  `sidequest_daemon/media/daemon.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): This story produces **two PRs** that must merge together —
  daemon code cut (`sidequest-daemon` → `develop`) and ADR deferral notes
  (`orc-quest` → `main`). The pf finish flow operates on session REPOS=`daemon` only and
  will not see the orchestrator ADR-notes PR. Affects the merge/finish ceremony
  (`feat/78-3-daemon-deferred-observability-adr-notes` on the orchestrator must be merged
  by hand alongside the daemon PR). *Found by Dev during implementation.*
- **Improvement** (non-blocking): Confirmed TEA's note — the `Callable`/`Awaitable`
  imports were cleared when `start_periodic_heartbeat` was removed; `ruff` is green.
  No residual orphans. Affects `sidequest_daemon/media/daemon.py`. *Found by Dev during
  implementation.*

## Design Deviations

### TEA (test design)
- **ADR-note obligation verified by review, not pytest**
  - Spec source: context-story-78-3.md, AC1 & AC2 (CUT path)
  - Spec text: "removed with an ADR-131 deferral note" / "removed with an ADR-046 deferral note"
  - Implementation: No automated test asserts the ADR notes exist. The deletion guards
    (`test_78_3_deferred_observability_cut.py`) cover the code removal; the ADR-note
    half is a code-review checklist item for The Merovingian.
  - Rationale: ADRs live in the orchestrator repo (`docs/adr/`); a daemon-repo test
    reaching `../docs/adr` is fragile (breaks in a standalone daemon checkout / CI) and
    crosses the repo boundary. Honest coverage of a cross-repo doc deliverable is review,
    not a brittle relative-path file read.
  - Severity: minor
  - Forward impact: Reviewer must confirm both ADR amendments are present before merge.
- **Deletion story → removal-regression guards instead of behavioral RED tests**
  - Spec source: context-story-78-3.md, AC3
  - Spec text: "If wired: OTEL span assertion test proves the span fires on the live path."
  - Implementation: Operator decided CUT for both exports (2026-06-03), so AC3 is
    vacuously satisfied (nothing wired). RED tests are removal guards (symbol/module gone
    + orphaned-test gone) plus one over-deletion preservation guard, not live-path span
    assertions.
  - Rationale: The wire-vs-cut fork determines test shape; a WIRE test and a CUT test are
    opposite. With CUT chosen, the meaningful failing tests are "the trap is gone and
    stays gone."
  - Severity: minor
  - Forward impact: If the heartbeat capability is ever revived, ADR-131 + a live-path
    AC3 test come back as new work.

### Dev (implementation)
- **ADR deferral notes shipped as a separate orchestrator-repo PR, not the daemon PR**
  - Spec source: context-story-78-3.md, AC1 & AC2 (CUT path) + session REPOS=daemon
  - Spec text: "removed with an ADR-131 deferral note" / "removed with an ADR-046 deferral note"
  - Implementation: The code cut + orphaned-test removal landed on the daemon branch
    `feat/78-3-daemon-deferred-observability` (PR → daemon `develop`). The ADR-131 /
    ADR-046 deferral notes live in the orchestrator repo (`docs/adr/`), so they went on a
    second branch `feat/78-3-daemon-deferred-observability-adr-notes` (PR → orchestrator
    `main`). Two PRs, one story.
  - Rationale: ADRs are not in the daemon repo; a daemon PR physically cannot contain
    them. Splitting is the only honest path. Both branches are pushed.
  - Severity: minor
  - Forward impact: Reviewer + SM must merge BOTH PRs to consider 78-3 complete — the
    daemon PR alone leaves the ADR-note half of AC1/AC2 unshipped.

### Architect (reconcile)

Verified all three in-flight deviation entries against the shipped code and the spec
sources. Every entry is accurate and complete (all 6 fields present and substantive):

- **TEA — "ADR-note obligation verified by review, not pytest":** Spec source
  `context-story-78-3.md` AC1/AC2 exists; quoted spec text ("removed with an ADR-131/046
  deferral note") is accurate. Implementation matches — no pytest asserts the ADR notes;
  Reviewer hand-verified both (Observation 5 + Reviewer audit). Accurate. ✓
- **TEA — "Deletion story → removal-regression guards instead of behavioral RED tests":**
  Spec source AC3 exists; quoted text accurate. Implementation matches — AC3 is vacuous
  under the CUT decision; guards assert symbol/module absence + over-deletion survival.
  Accurate. ✓
- **Dev — "ADR deferral notes shipped as a separate orchestrator-repo PR":** Both branches
  exist and are pushed (`feat/78-3-daemon-deferred-observability` → daemon `develop`;
  `feat/78-3-daemon-deferred-observability-adr-notes` → orchestrator `main`). Accurate. ✓

**Missed deviations:** None. Note for the record — the Operator's CUT choice over the
context's "Leans WIRE" framing is **not** a deviation: AC1/AC2 are explicitly OR-branched
("... OR removed with an ADR deferral note"), and the story context assigns the wire-vs-cut
call to this phase. Choosing CUT selects a spec-sanctioned path, not a divergence from it.
The `test_otel_spans.py` section renumber (5→4) is a trivial implementation detail, not a
spec deviation.

**AC deferral verification:** No-op — no ACs were deferred. AC1 and AC2 were *completed*
via their CUT/OR branch (code removed + ADR note); AC3 is vacuously satisfied (nothing
wired). No DEFERRED/DESCOPED ACs to reconcile.

## Sm Assessment

Story 78-3 is set up and ready for the red phase. This is a **finish-or-cut** decision story — two deferred daemon exports with ADR lineage, not pure dead code, so a blind delete is off the table. The session frames each export's lean clearly:

- **`start_periodic_heartbeat` leans WIRE** — ADR-131 is live and names this as the explicit unfinished follow-up. The architectural cost is real (active-writer registry for broadcast fan-out), so The Architect should weigh whether AC1 wiring fits a 2-pt budget or whether the honest call is the ADR-131 deferral note.
- **`detect_gpu`/`GpuInfo` does NOT clearly lean wire** — its parent coordinator (`ModelMemoryManager`) was deleted 2026-05-10. ADR-046 does not mandate wiring. CUT-with-deferral-note is a legitimate outcome here.

**Routing note for tea:** AC3 is the lie-detector. Whatever gets wired must have a test that drives the `_run_daemon` live path and proves the span fires in production — no `emit=None` stub-in-disguise. The wire-vs-cut decision per export belongs to the design/red phase, not to SM. Existing `test_heartbeat_emit.py` and `test_otel_spans.py` prove unit-level behavior but not live-path firing.

Handing off to **The Architect** (tea) for the red phase. No blocking PRs; merge gate clear.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Deletion story — removal-regression guards (RED now, GREEN after Dev deletes).

**Decision (Operator, 2026-06-03):** **CUT both** deferred exports, each with an ADR
deferral note. Rationale captured at the decision point:
- **`start_periodic_heartbeat` → CUT (ADR-131 note).** Honest wiring required a net-new
  active-writer registry (`_handle_client` register/deregister) + a broadcast `emit`
  helper + `create_task` scheduling in `_run_daemon` + cancellation in the shutdown
  `finally` + a live-path AC3 test — comfortably past a 2-pt budget. And idle liveness is
  **not currently broken**: the server's `DaemonClient.heartbeat_listener` reconnects
  ~15s (4× margin under the 60s unresponsive threshold). Cutting removes the
  `NOT YET WIRED` trap now; ADR-131 Consequences gets a deferral note.
- **`detect_gpu`/`GpuInfo` → CUT (ADR-046 note).** ADR-046 is `retired`; the
  `ModelMemoryManager` coordinator it fed was deleted in `5118d6c` (2026-05-10). No live
  consumer, no standalone value claimed. The orphaned `gpu.detect` diagnostic follows the
  coordinator out.

**Test Files:**
- `tests/test_78_3_deferred_observability_cut.py` — 6 guards (5 RED removal guards + 1
  GREEN over-deletion preservation guard).

**Tests Written:** 6 tests covering AC1, AC2, AC3 (vacuous), and a collateral-damage guard.
**Status:** RED (5 failing, 1 passing-by-design — verified via direct pytest; `testing-runner`
skipped to protect the session file per the known clobber issue).

| Test | AC | Asserts | RED now? |
|------|----|---------|---------|
| `test_periodic_heartbeat_export_removed` | AC1 | `start_periodic_heartbeat` gone from daemon module | ✅ fails |
| `test_default_heartbeat_interval_constant_removed` | AC1 | orphaned `DEFAULT_HEARTBEAT_INTERVAL_SECONDS` gone | ✅ fails |
| `test_orphaned_periodic_heartbeat_isolation_test_removed` | AC1 | `test_heartbeat_emit.py` no longer references the symbol (same-PR test deletion) | ✅ fails |
| `test_gpu_detect_module_removed` | AC2 | importing `media.gpu_detect` raises `ModuleNotFoundError` | ✅ fails |
| `test_orphaned_gpu_detect_span_test_removed` | AC2 | `test_otel_spans.py` no longer references `gpu_detect`/`detect_gpu` (same-PR test deletion) | ✅ fails |
| `test_per_connection_heartbeat_path_preserved` | over-deletion | `_write_heartbeat`/`_make_heartbeat`/`_handle_client` survive | ⬜ passes by design |

### Rule Coverage

| Rule (project) | Test(s) | Status |
|------|---------|--------|
| Delete Dead Code in the Same PR | `*_isolation_test_removed`, `*_gpu_detect_span_test_removed` | failing |
| No Stubbing (no `NOT YET WIRED` traps) | `test_periodic_heartbeat_export_removed` | failing |
| Verify Wiring, Not Just Existence (no orphaned exports) | `test_gpu_detect_module_removed` + constant guard | failing |
| Don't over-delete (preserve working per-connection liveness) | `test_per_connection_heartbeat_path_preserved` | passing (guard) |
| AC3 live-path span test | n/a — vacuous (both cut), logged as deviation | — |

**Rules checked:** removal-discipline + over-deletion guard covered. ADR-note rule is
review-verified (deviation logged — cross-repo doc deliverable).
**Self-check:** 0 vacuous tests — every guard has a meaningful `assert` with a failure
message tied to an AC; no `assert True` / `let _` / always-None patterns.

### Dev (Agent Smith) GREEN obligations — checklist
1. Delete `start_periodic_heartbeat` (daemon.py:155-189) + `DEFAULT_HEARTBEAT_INTERVAL_SECONDS`
   (118) + clear the now-unused `Callable`/`Awaitable` imports (29). Keep `_make_heartbeat`,
   `_write_heartbeat`, `_IN_FLIGHT_COUNTS` — per-connection liveness stays.
2. Delete the orphaned AC2 test `test_idle_daemon_emits_periodic_ready_heartbeat`
   (`tests/test_heartbeat_emit.py:364`). Keep the other 5 heartbeat tests.
3. Delete the entire `sidequest_daemon/media/gpu_detect.py` module.
4. Delete `TestGpuDetectSpan` + its section header (and the docstring mention) in
   `tests/test_otel_spans.py`. Keep the Z-Image worker span tests.
5. **ADR notes (orchestrator repo — separate change):** amend `docs/adr/` ADR-131
   Consequences (periodic emitter cut/deferred; reconnect cadence covers idle) and add a
   one-line ADR-046 note (orphaned `gpu.detect` diagnostic followed `ModelMemoryManager`
   out, 2026-05-10).
6. Gate: `just daemon-test` + `just daemon-lint` green. The 6 guards in
   `test_78_3_deferred_observability_cut.py` must all pass.

**Handoff:** To Dev (Agent Smith) for implementation (GREEN).
## Dev Assessment

**Implementation Complete:** Yes
**Approach:** Pure CUT (Operator decision) — deleted both deferred-observability exports
+ their orphaned isolation tests; added ADR deferral notes. No new behavior wired, so
AC3 is vacuous.

**Files Changed (daemon repo — `feat/78-3-daemon-deferred-observability`):**
- `sidequest_daemon/media/daemon.py` — removed `start_periodic_heartbeat` coroutine,
  `DEFAULT_HEARTBEAT_INTERVAL_SECONDS`, and the now-orphaned `Awaitable`/`Callable`
  imports. **Kept** `_make_heartbeat`, `_write_heartbeat`, `_IN_FLIGHT_COUNTS`,
  `_handle_client` — the per-connection liveness path that actually works.
- `sidequest_daemon/media/gpu_detect.py` — **deleted** (whole module: `detect_gpu`,
  `GpuInfo`, `GpuBackend`).
- `tests/test_heartbeat_emit.py` — removed the orphaned AC2 test
  `test_idle_daemon_emits_periodic_ready_heartbeat` + its section header. Other 5
  heartbeat tests kept.
- `tests/test_otel_spans.py` — removed `TestGpuDetectSpan` + section header + the
  `gpu_detect` mention in the module docstring; renumbered the trailing section.
- `tests/test_78_3_deferred_observability_cut.py` — (TEA's RED guards, now GREEN).

**Files Changed (orchestrator repo — `feat/78-3-daemon-deferred-observability-adr-notes`):**
- `docs/adr/131-daemon-server-oob-contracts.md` — periodic idle-heartbeat emitter marked
  deferred/cut across its Strategy, Observability, and Consequences references (no longer
  "NOT YET WIRED").
- `docs/adr/046-gpu-memory-budget-coordinator.md` — one note that the orphaned
  `detect_gpu`/`gpu.detect` diagnostic followed the deleted `ModelMemoryManager`
  coordinator out (5118d6c, 2026-05-10).

**Tests:** GREEN — 6/6 guards pass; full daemon suite **373 passed**; `ruff` clean.
(`testing-runner` skipped to protect the gitignored session file per the known clobber
issue; verified via direct `just daemon-test` + `uv run pytest`.)

**Branches (pushed, two PRs needed):**
- `feat/78-3-daemon-deferred-observability` → `sidequest-daemon` `develop`
- `feat/78-3-daemon-deferred-observability-adr-notes` → `orc-quest` `main`

**Handoff:** To Reviewer (The Merovingian). Confirm BOTH ADR notes are present and BOTH
PRs merge together — the daemon PR alone leaves the ADR-note half of AC1/AC2 unshipped.
## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None

Independently verified the diffs against the spec's CUT branch (not just the Dev Assessment):

- **AC1 — `start_periodic_heartbeat` CUT (ADR-131 OR-branch).** Confirmed the coroutine,
  `DEFAULT_HEARTBEAT_INTERVAL_SECONDS`, and the orphaned `Awaitable`/`Callable` imports
  are gone from production (`grep` → zero references in `sidequest_daemon/`); the orphaned
  isolation test removed. ADR-131's three load-bearing references (Strategy line ~90,
  Observability "Gap", Consequences) are converted from "NOT YET WIRED" to
  "deferred/cut". The one surviving `NOT YET WIRED` string (ADR-131 Consequences) is an
  intentional descriptive quote in the cut rationale ("rather than shipped as a
  `NOT YET WIRED` stub"), not a residual trap. ✅
- **AC2 — `detect_gpu`/`GpuInfo` CUT (ADR-046 OR-branch).** Whole `gpu_detect.py` module
  deleted; `TestGpuDetectSpan` + its docstring mention removed. ADR-046 STALE banner gains
  a substantive note that the orphaned `gpu.detect` diagnostic followed the deleted
  `ModelMemoryManager` coordinator out (5118d6c). ✅
- **AC3 — live-path span test.** Vacuously satisfied; nothing wired. ✅
- **Over-deletion guard.** Per-connection liveness (`_write_heartbeat`/`_make_heartbeat`,
  9 refs) preserved — the cut is exports-only, the working liveness path is intact. ✅

**Architectural concurrence (no new deviation):** The two-PR cross-repo split (daemon code
→ daemon `develop`; ADR notes → orchestrator `main`) already logged by TEA and Dev is the
only honest structure — ADRs physically cannot live in the daemon PR. The reuse-first bar
is trivially met: this story *removes* code, adds none. Net diff 156 ins / 201 del, with
+152 of the insertions being the guard test.

**Decision:** Proceed to review (TEA verify → The Merovingian). Reviewer's load-bearing
check: confirm BOTH PRs are merged together — the daemon PR alone leaves the ADR-note half
of AC1/AC2 unshipped.
## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 2 (`media/daemon.py` post-cut, `tests/test_78_3_deferred_observability_cut.py`)
— `gpu_detect.py` deleted (nothing to analyze); the two existing test files had deletion-only edits (no new code).

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 2 findings | Extract helpers for import+hasattr and file-read+substring patterns (high) |
| simplify-quality | clean | Deletion complete, no orphaned code, no dead imports, naming consistent |
| simplify-efficiency | 3 findings | Import fixture, file-read helper, trim assertion messages (all medium) |

**Applied:** 1 fix — extracted `_assert_sibling_test_lacks(filename, *symbols, hint)` for the
two orphaned-test guards (flagged by reuse-high *and* efficiency-medium; independent signal).
The helper also improves diagnostics (reports *which* symbol survived).
**Flagged for Review:** 0
**Declined (with rationale):**
- *Import fixture* (efficiency, medium) — `sys.modules` already caches the import; a fixture
  adds indirection and erodes each guard's self-contained readability. Negligible benefit.
- *Trim assertion messages* (efficiency, medium) — the verbose "delete X, here's why" messages
  are the intentional anti-trap deferral signal the epic wants; not noise. The efficiency agent
  itself conceded the over-explanation is intentional.
- *Module import+hasattr helper for the 5 hasattr sites* (reuse, high) — declined extraction
  beyond the file-source helper: for 5 trivial `hasattr` call sites, test-local explicitness
  beats DRY; each guard should read independently.
**Reverted:** 0

**Overall:** simplify: applied 1 fix

**Quality Checks:** All passing — full daemon suite **373 passed**, `ruff` clean, before and
after the refactor. 6/6 story guards green.

### Delivery Findings Capture
- No upstream findings during test verification.

**Handoff:** To Reviewer (The Merovingian) for code review.
## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (373 pass, 0 smells, 0 TODOs) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (2 enabled returned clean; 7 disabled via workflow.reviewer_subagents)
**Total findings:** 0 confirmed, 0 dismissed, 1 deferred (two-PR merge coordination — non-blocking, for SM)

### Rule Compliance

Rules sourced from `sidequest-daemon/CLAUDE.md` + `SOUL.md` (no `.claude/rules/` or lang-review checklist exists). Enumerated against every changed unit:

| Rule | Instances checked | Verdict |
|------|-------------------|---------|
| **No Stubbing** (no `NOT YET WIRED` shells) | `start_periodic_heartbeat` (the self-documented stub), `gpu_detect.py` (orphan) | ✅ Both removed — the cut *eliminates* stubs |
| **No Silent Fallbacks** | daemon.py removal, gpu_detect deletion | ✅ No fallback/alt-path introduced |
| **Delete Dead Code in the Same PR** | `test_idle_daemon_emits_periodic_ready_heartbeat`, `TestGpuDetectSpan`, `DEFAULT_HEARTBEAT_INTERVAL_SECONDS`, orphaned `Awaitable`/`Callable` imports | ✅ All removed in-PR; lint confirms no orphan imports |
| **Every Test Suite Needs a Wiring Test** | new guard suite | ✅ `test_per_connection_heartbeat_path_preserved` verifies the surviving production path stays reachable; module-import guards verify removal |
| **OTEL Observability** (don't blind the GM panel) | `gpu.detect` span removal | ✅ Span fed the deleted `ModelMemoryManager`, had zero production callers, never fired in prod — removing a never-firing span is zero observability loss; Z-Image worker spans untouched |
| **Crunch-in-genre / flavor-in-world**, multiplayer, agency | n/a | Not applicable to a daemon infra cut |

### Reviewer Observations

1. `[VERIFIED]` Deletion completeness — `start_periodic_heartbeat`, `DEFAULT_HEARTBEAT_INTERVAL_SECONDS`, and the `Awaitable`/`Callable` imports removed; `TYPE_CHECKING` correctly preserved (still used at `daemon.py:12`). Evidence: daemon diff lines 9-10, 18-19, 28-62.
2. `[VERIFIED]` Over-deletion guard holds — `_make_heartbeat`/`_write_heartbeat`/`_IN_FLIGHT_COUNTS`/`_handle_client` untouched; only the periodic-emitter block excised. The per-connection liveness path (the one that actually fires today) is intact. Evidence: diff shows backpressure-counter comment retained (lines 21-23); `test_per_connection_heartbeat_path_preserved` enforces it.
3. `[VERIFIED]` Orphaned tests removed in-PR — `test_idle_daemon_emits_periodic_ready_heartbeat` and `TestGpuDetectSpan` deleted with their section headers + the docstring mention; no dangling imports (preflight lint clean). Evidence: diff lines 302-366, 385-432.
4. `[VERIFIED]` OTEL principle not violated — the removed `gpu.detect` span fed a coordinator deleted in 5118d6c and had no production caller, so it never fired; removal is documented in the ADR-046 note. Corroborated by `[SEC]` security subagent (clean). Evidence: adr diff lines 10-15.
5. `[VERIFIED]` ADR deferral obligation (AC1/AC2 CUT branch) satisfied — ADR-131's three references converted from "NOT YET WIRED"/"Gap" to "deferred/cut" with rationale; ADR-046 gains the orphaned-diagnostic note. Evidence: /tmp/78-3-adr.diff in full.
6. `[LOW]` The `_assert_sibling_test_lacks` guards are text-grep, not semantic — a future false-fail is possible if the symbol name appears in an unrelated comment. Acceptable: the `hasattr`/`ModuleNotFoundError` guards are the semantic checks; the grep is a cleanup enforcer. If the sibling file were deleted entirely, `read_text()` raises `FileNotFoundError` (errors loudly, no false-pass). Location: `test_78_3_deferred_observability_cut.py:169-180`. Non-blocking.

### Devil's Advocate

Argue this cut is broken. **First attack — liveness regression.** ADR-131 exists because of the 2026-04-19 "13-minute silence" failure; deleting a *heartbeat* function in that subsystem looks reckless. But the deleted coroutine was never wired into `_run_daemon` — it had no production caller and emitted nothing at runtime. Deleting code that never executed cannot change runtime liveness behavior. The two mechanisms that *do* keep liveness fresh — per-connection `_write_heartbeat` on accept/lock-transition and the server's ~15s reconnect listener (4× margin under the 60s threshold) — are untouched and guard-protected. No regression. **Second attack — observability loss.** Removing an OTEL span violates the "GM panel is the lie detector" principle on its face. But the `gpu.detect` span fed `ModelMemoryManager`, deleted 2026-05-10; `detect_gpu` had zero non-test callers, so the span never emitted in production. You cannot blind a panel to a signal it never received. **Third attack — hidden consumer.** What if something imports `gpu_detect` dynamically (string import, entry point)? Grep found zero references outside the deleted test; the full 373-test suite passes with the module gone; the module-import guard asserts `ModuleNotFoundError`. **Fourth attack — test theater.** Are the guards vacuous? No — they assert real post-conditions (symbol absence, module-unimportability, sibling-test cleanliness, and survival of the preserved path), each with a meaningful failure message. **Fifth attack — the real risk: split delivery.** The code lives in the daemon PR; the ADR notes live in a *separate* orchestrator PR. If the daemon PR merges alone, AC1/AC2's "OR removed with an ADR deferral note" is only half-shipped — the code trap is gone but the doc would still say "Gap: not yet wired." This is the one genuine hazard, and it's a *merge-coordination* concern, not a code defect. Flagging it as a deferred finding for SM. Conclusion: no Critical/High; the cut is correct, well-guarded, and well-documented.

### Reviewer (audit)

Design-deviation audit — every logged entry stamped:

- **TEA: ADR-note obligation verified by review, not pytest** → ✓ ACCEPTED by Reviewer: correct — a daemon-repo test reaching `../docs/adr` would be fragile/wrong-repo; I verified both ADR notes by hand (see Observation 5).
- **TEA: Deletion story → removal-regression guards instead of behavioral RED tests** → ✓ ACCEPTED by Reviewer: the CUT decision makes AC3 vacuous; removal guards + an over-deletion guard are the right shape.
- **Dev: ADR deferral notes shipped as a separate orchestrator-repo PR** → ✓ ACCEPTED by Reviewer: the only honest structure — ADRs cannot live in the daemon PR. Carries a merge-coordination obligation (captured as a delivery finding below).
- No undocumented deviations found: the implementation matches the spec's CUT branch on every AC.

## Reviewer Assessment

**Verdict:** APPROVED
**Data flow traced:** No external/runtime data flows through this diff — it removes unwired code (`start_periodic_heartbeat`, never called) and a never-called diagnostic (`detect_gpu`), and adds a static-introspection guard test. The only inputs are hardcoded module-name/filename string literals in the guard suite (no injection surface — corroborated by the security subagent).
**Pattern observed:** Clean finish-or-cut deletion with removal-regression guards + an explicit over-deletion guard — `tests/test_78_3_deferred_observability_cut.py:275` preserves the real liveness path while proving the traps are gone. Good model for future `sq-wire-it` cut stories.
**Error handling:** N/A for deletions; the guard suite fails loudly (`AssertionError`/`ModuleNotFoundError`/`FileNotFoundError`), no silent passes.
**Subagents:** preflight GREEN (373 pass, 0 smells); `[SEC]` security clean — 0 findings, all project rules (No Stubbing / No Silent Fallbacks / Delete Dead Code in Same PR / Wiring Test / OTEL) verified compliant. 7 disabled via settings.
**Blocking issues:** None (0 Critical, 0 High). One non-blocking deferred finding for SM: merge BOTH PRs together.
**Handoff:** To SM (Morpheus) for finish-story.

<!-- reviewer findings below -->
### Reviewer (code review)
- **Gap** (non-blocking): Story completion requires merging TWO PRs — daemon code (`sidequest-daemon` `feat/78-3-daemon-deferred-observability` → `develop`) AND ADR notes (`orc-quest` `feat/78-3-daemon-deferred-observability-adr-notes` → `main`). The pf finish flow only sees REPOS=`daemon`; the orchestrator ADR PR must be merged by hand or AC1/AC2's ADR-deferral-note half ships incomplete (code trap removed but ADRs still read "Gap: not yet wired"). Affects the finish/merge ceremony. *Found by Reviewer during code review.*