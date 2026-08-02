---
story_id: "158-78"
jira_key: ""
epic: "158"
workflow: "tdd"
---
# Story 158-78: The DEFAULT server quality gate is red — uv run pytest fails 2 tests under xdist shared-state races

## Story Details
- **ID:** 158-78
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none
- **Branch:** feat/158-78-xdist-shared-state-races-red-gate
- **PR:** #1148 - fix(158-78): isolate every test from the developer's real Postgres database
- **Priority:** p1
- **Points:** 3

## Story Summary

The DEFAULT server quality gate (`just server-check`) runs pytest with xdist parallel execution (`-n auto` via addopts), which is the standard CI gate. This gate is currently RED due to 2 failing tests under parallel execution:

- `test_102_5_wn_tool_narrator_wiring.py:187` — `assert reloaded is not None` after a Postgres `store.load()` call
- A second test failure with the same root cause (xdist shared-state race)

The failures are **pre-existing on develop** and are **NOT caused by any 158 story**. This was isolated by re-running with both 158-58 files `--ignore'd`, confirming the races exist independently.

**Critical Finding:** Serial execution with `-n0` passes cleanly. The failures only manifest under parallel xdist execution, indicating a **shared Postgres state race across xdist workers**. The aggregate gate is unreliable until fixed.

## Technical Approach

This is a test-infrastructure determinism fix. The root cause hypothesis to be confirmed in RED: xdist parallel workers are sharing Postgres connection state or not properly isolating test database state between workers.

Expected investigation and fix will involve:
- Verifying the Postgres isolation setup for parallel test execution
- Ensuring each xdist worker has its own isolated test database or properly rolled-back state
- Confirming that fixtures managing database state respect xdist's worker isolation model
- Potentially adding fixture scope markers or session-level isolation hooks

## Acceptance Criteria

- `uv run pytest -n auto` (the default gate as run by `just server-check`) passes 100% of tests in both runs
- Serial execution `pytest -n0` remains clean (no regression)
- The specific failure at `test_102_5_wn_tool_narrator_wiring.py:187` is resolved
- OTEL/fixture coverage confirms the fix by running the suite multiple times with consistent results

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-08-01T22:58:57Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-08-01T21:09:43Z | 2026-08-01T21:11:20Z | 1m 37s |
| red | 2026-08-01T21:11:20Z | 2026-08-01T21:24:35Z | 13m 15s |
| green | 2026-08-01T21:24:35Z | 2026-08-01T22:08:13Z | 43m 38s |
| review | 2026-08-01T22:08:13Z | 2026-08-01T22:58:57Z | 50m 44s |
| finish | 2026-08-01T22:58:57Z | - | - |

## Sm Assessment

Branch created off `develop` (sidequest-server, gitflow strategy). No Jira — epic-158 is sprint-YAML-only, claim explicitly SKIPPED.

This story is a **sibling to 158-59's Delivery Finding**, which independently noted the xdist parallel-suite flakiness. Dev ran three consecutive full-suite runs and confirmed:
- Run 1 and 2 each failed one *different*, unrelated test
- Run 3 was clean
- Root cause: unseeded global `random` in e2e SWN combat fixtures (now filed as 158-83)

158-78 and 158-83 together mean **neither the parallel nor the serial suite is fully deterministic**. This story focuses on the xdist-shared-state races (Postgres isolation); 158-83 addresses the unseeded RNG flakiness (also present in serial).

## Related Work

- **158-83 (p1, serial-suite flakiness):** Unseeded global `random` in SWN e2e combat fixtures causes different test failures across runs in serial (`-n0`) mode. Related root cause but different scope.

## TEA Assessment

**Tests Required:** Yes
**Status:** RED (3 failing — ready for Dev)
**Test File:** `sidequest-server/tests/infrastructure/test_158_78_pg_isolation_coverage.py` (commit `80fdfaf2`)

### Root Cause (confirmed, not hypothesised)

The setup hypothesis ("xdist workers share Postgres state") was directionally right but named the wrong mechanism. The actual cause:

`tests/agents/tools/conftest.py` defines the `pg_store_with` / `pg_empty_store` helpers **and** the autouse `_pg_isolation` fixture that makes them safe (rebinds `SIDEQUEST_DATABASE_URL` to a per-worker throwaway DB, TRUNCATEs it, resets the process-global pool). **A conftest's autouse fixtures are directory-scoped.** Two modules one level up import the helper *function* and silently leave the *safety* behind:

- `tests/agents/test_102_5_wn_tool_narrator_wiring.py`
- `tests/agents/test_use_mutation_tool.py`

Exactly two — matching the story's "fails 2 tests". With no isolation, `db_pool.get_pool()` falls through to the ambient `SIDEQUEST_DATABASE_URL` (the developer's **real** `sidequest` DB), and both modules persist under the same hardcoded slug `tool-test`. Under `-n auto` the workers are separate processes sharing that one row, so each clobbers the other. Under `-n0` a single process cannot interleave the writes — hence "serial is clean".

**Evidence.** `-n 2 --dist loadfile` forces the two files onto separate workers and fails **3/3 runs**; the `-n0` control passes 6/6. Under the shipped `-n auto` the victim *rotates* — three distinct signatures observed from the one cause: `NOT_FOUND: unknown actor: 'Vesska'`, `assert reloaded is not None`, `no mutation state on this session; was 'Rux' seeded at chargen?`. The clearest evidence is a **torn row**: after two default-slug `pg_store_with()` calls the reload returns `meta=SessionMeta(heavy_metal/long_foundry)` with `snapshot=GameSnapshot(mutant_wasteland/dead_lands)` — metadata and payload from different tests.

The correct pattern **already exists in-repo**: `tests/integration/test_mutation_wiring.py::_pg_store_with` binds an explicit `migrated_db` and uses a unique `wiring-{uuid4}` slug. This is a wire-up-what-exists fix, not new machinery.

### Acceptance Criteria (defined here — sprint YAML carried none)

| AC | Test | Status |
|----|------|--------|
| AC-1 no test may run with a real database bound (unset → fail loud, or `sq_test_*` throwaway) | `test_no_test_runs_with_the_developer_database_bound` | failing |
| AC-2 `pg_store_with()` must not reuse one session slug — a second call must not clobber the first | `test_pg_store_with_does_not_reuse_a_single_session_slug` | failing |
| AC-3 wiring: the two unisolated modules pass under `-n 2 --dist loadfile` | `test_unisolated_helper_modules_pass_under_xdist` | failing |

AC-1 is the durable, non-rotting invariant (the Postgres analogue of the existing `test_tmp_save_dir_fixture_isolated_from_real_home` guard). AC-3 is the wiring test — it reproduces the actual reported gate failure end to end rather than asserting a proxy.

### Rule Coverage

| Rule (CLAUDE.md / SOUL.md) | Test | Status |
|------|---------|--------|
| No Silent Fallbacks — an unisolated DB bind must fail loud, never resolve to prod | `test_no_test_runs_with_the_developer_database_bound` | failing |
| No Silent Fallbacks — a second helper call must not silently overwrite the first | `test_pg_store_with_does_not_reuse_a_single_session_slug` | failing |
| Every Test Suite Needs a Wiring Test | `test_unisolated_helper_modules_pass_under_xdist` (subprocess xdist run) | failing |
| No Source-Text Wiring Tests | all three are behavioral (env resolution, real PG round-trip, real subprocess) — no production source is grepped | complied |

**Self-check:** 0 vacuous assertions. No `assert True`, no bare `is not None` standing in for identity — AC-2 deliberately asserts `find_creature_core("Vesska") is not None` *inside* the payload, because a bare not-None load passes on a fully clobbered row. AC-1's `url is None or ...` admits two outcomes by design (both are safe); it cannot pass with a real DB bound.

**Suite safety:** all three tests write only to throwaway databases. Verified the real DB row count was unchanged (2391) across the entire RED phase.

### Verification

| Check | Result |
|-------|--------|
| New RED tests (`-n0`) | 3 failed / 3 — all for the intended reason |
| Pre-existing `tests/infrastructure/` | 18 passed, 0 failed — no regression |
| `tests/agents/` under shipped `-n auto` (throwaway DB) | 2250 passed, 2 skipped, **1 failed** — pre-existing race reproduced |

**Handoff:** To Dev (Naomi) for GREEN.

## Delivery Findings

### TEA (test design)

- **Gap** (blocking): The `_pg_isolation` autouse fixture is directory-scoped to `tests/agents/tools/`, but `pg_store_with`/`pg_empty_store` are imported by modules outside it, which therefore run with no PG isolation at all.
  Affects `sidequest-server/tests/agents/tools/conftest.py` (isolation must cover every consumer of the helpers — move it to a shared conftest, or make the helpers themselves refuse to run unisolated).
  *Found by TEA during test design.*

- **Gap** (blocking): `pg_store_with()` defaults every caller to the single hardcoded session slug `tool-test`, so two calls silently overwrite each other and produce a torn row (SessionMeta and GameSnapshot from different tests).
  Affects `sidequest-server/tests/agents/tools/conftest.py` (give each store a unique slug, as `tests/integration/test_mutation_wiring.py` already does).
  *Found by TEA during test design.*

- **Improvement** (non-blocking): **The suite has been writing to the developer's real Postgres database.** 1,938 of 2,391 rows in the live `sidequest` DB are test junk (`test-*` / `tool-test` slugs), 24 of them written on 2026-08-01. This is a data-integrity hazard independent of the gate failure, and no fixture guards against it the way `_isolate_monster_manuals` (story 162-1) guards `~/.sidequest`. AC-1 closes the hole for future runs; **the existing 1,938 junk rows still need a separate cleanup pass** — this story does not delete them.
  Affects the live `sidequest` database (cleanup) and `sidequest-server/tests/conftest.py` (the guard).
  *Found by TEA during test design.*

- **Improvement** (non-blocking): Those same junk rows are almost certainly the bulk of story **166-8**'s "/api/debug/state full-scan pins the event loop — sync per-save load+migrate+span across **1849 saves**". The save count and the junk count are the same order and the same origin. Cleaning the pollution may shrink 166-8's problem substantially, and 166-8 should be re-measured after this lands rather than optimised against a polluted baseline.
  Affects story 166-8 scope (re-measure before optimising).
  *Found by TEA during test design.*

- **Improvement** (non-blocking): `tests/integration/test_mutation_wiring.py:205` sets `os.environ["SIDEQUEST_DATABASE_URL"]` directly instead of via `monkeypatch.setenv`, so the binding leaks to every subsequent test in that xdist worker. It happens to be harmless today (it points at an isolated DB) but it is the same class of latent cross-test leak.
  Affects `sidequest-server/tests/integration/test_mutation_wiring.py` (use `monkeypatch.setenv`).
  *Found by TEA during test design.*

- **Question** (non-blocking): AC-1 admits either an unset `SIDEQUEST_DATABASE_URL` (fail-loud on unisolated access) or a per-worker throwaway bind. The unset approach is cheaper — binding `migrated_db` suite-wide would make all ~28 workers pay a `CREATE DATABASE` + `alembic upgrade head` even for tests that never touch Postgres. Dev/Architect should pick deliberately; the test does not force either.
  Affects `sidequest-server/tests/conftest.py` (choice of isolation strategy).
  *Found by TEA during test design.*

## Dev Assessment

**Implementation Complete:** Yes
**Tests:** 3/3 AC tests passing; full gate 15056 passed / 0 failed
**Branch:** `feat/158-78-xdist-shared-state-races-red-gate` (pushed, commit `2b806d33`)

**Files Changed:**
- `tests/conftest.py` — new autouse `_no_ambient_database_url` (redirects `SIDEQUEST_DATABASE_URL` to the per-worker throwaway DB); `pg_isolation` hoisted here from the tools conftest so any module can request it
- `tests/agents/tools/conftest.py` — `_pg_isolation` now delegates to the shared fixture; `pg_store_with`/`pg_empty_store` default to a unique per-call slug instead of the shared literal `"tool-test"`
- `tests/agents/test_102_5_wn_tool_narrator_wiring.py`, `tests/agents/test_use_mutation_tool.py` — request `pg_isolation` explicitly via a module-level autouse fixture
- `tests/infrastructure/test_158_78_pg_isolation_coverage.py` — AC-2 simplified to use the hoisted `pg_isolation` rather than duplicating its TRUNCATE logic

### The defect was 10× larger than the story described

The story said "2 tests fail". The first fix attempt — a root-conftest `monkeypatch.delenv("SIDEQUEST_DATABASE_URL")`, the textbook No-Silent-Fallbacks guard — turned **18 additional tests** red with `MissingDatabaseUrlError`. Those tests (`tests/server/test_app.py`, `test_forensics_routes.py`, `test_lore_rag_wiring.py`, `test_culture_context.py`, …) had *also* been silently binding the developer's real database; they simply weren't racing on a shared slug the way the two named modules were, so nobody noticed. **Twenty tests, not two.** That is the honest scale, and it is consistent with the 1,938 junk rows TEA found — two tests could never have produced that many.

The shipped fix therefore **redirects** rather than deletes: every test binds the same per-worker throwaway database `migrated_db` builds. This satisfies AC-1's option (b), keeps all twenty tests working, and takes the real database out of reach. The delete path survives only for the case where no test Postgres is configured at all — there, no safe target exists, so failing loud is the honest option.

### Verification

| Check | Result |
|-------|--------|
| AC tests (`-n0`) | 3/3 passing |
| Full default gate (`-n auto`), run 1 | 15056 passed, 341 skipped, **0 failed** |
| Full default gate, run 2 | 15056 passed, 341 skipped, **0 failed** — identical |
| Real DB row count across a full run | 2405 → 2405, **unchanged** |
| The two originally-failing modules | 6/6 passing |

An earlier full run showed `15055 passed, 1 failed` — `test_space_opera_swn_combat_e2e.py::test_firefight_resolves_on_hp_depletion_vs_content_ac`. Measured over 20+ iterations per side: **baseline 1/20 vs. this change 1/29**. Pre-existing ~4% unseeded-RNG flake (the test asserts an unseeded d20 attack *hits*), tracked as **158-83**. Not a regression, and out of scope here.

**No regressions introduced** — every quality metric matches the base commit exactly: `ruff check` 4 errors (identical), `ruff format --check` 48 files (identical), `pyright` 12 errors on the touched files (identical). The new test file is clean on all three (0/0/0).

**Handoff:** To Reviewer (Chrisjen) for review.

## Design Deviations

### TEA (test design)

- **AC-2 (unique slug) exceeds the literal reported symptom**
  - Spec source: `sprint/context/context-story-158-78.md`, story title
  - Spec text: "uv run pytest ... fails 2 tests under xdist shared-state races ... The aggregate gate is unreliable until fixed"
  - Implementation: added a third AC requiring `pg_store_with()` to stop sharing one hardcoded session slug, beyond what a pure per-worker-DB fix would need
  - Rationale: per-worker isolation alone leaves the helper structurally able to clobber itself — two calls in one test still collide silently. Fixing only the isolation would make the gate green while leaving the footgun armed, and the story's own framing is that the gate must become *reliable*, not merely green. Verified no existing test depends on the shared default slug (all 33 consumers call it once per test, or pass an explicit slug), so uniquifying it is non-breaking.
  - Severity: minor
  - Forward impact: Dev must change the helper's default slug, not just the fixture scope. If Reviewer judges this out of scope, AC-2 can be dropped without affecting AC-1/AC-3.

- **No test asserts the ~1,938 existing junk rows are removed**
  - Spec source: `sprint/context/context-story-158-78.md`, Scope ("In scope: the behavior described by the story title")
  - Spec text: story title scopes the work to the red gate, not to data cleanup
  - Implementation: AC-1 prevents *future* pollution; no test asserts the existing rows are deleted
  - Rationale: deleting rows from Keith's live database is a destructive operation well outside a test-determinism story, and it needs his explicit say-so. Filed as a non-blocking Delivery Finding instead.
  - Severity: minor
  - Forward impact: the live DB stays polluted until a separate cleanup is authorised; story 166-8's baseline is affected until then.
### Dev (implementation)

- **Redirected `SIDEQUEST_DATABASE_URL` instead of stripping it**
  - Spec source: `.session/158-78-session.md`, TEA Assessment AC-1
  - Spec text: "the variable is UNSET, so any test that reaches for Postgres without explicitly requesting an isolated database fails loud with `MissingDatabaseUrlError` (No Silent Fallbacks); **or** it is bound to a `sq_test_*` per-worker throwaway database"
  - Implementation: chose option (b) — redirect to the per-worker `migrated_db` — after option (a) broke 18 tests that were silently relying on the ambient value. The strip path is retained only when `SIDEQUEST_TEST_DATABASE_URL` is unset (no safe target exists, so failing loud is the only honest outcome).
  - Rationale: TEA explicitly admitted both outcomes and asked Dev to choose. Option (a) was tried first and empirically converted 18 silent prod-DB consumers into hard failures at once; migrating all 18 is a much larger story. Redirecting satisfies the same invariant (no test can reach the real database) without the blast radius, and is strictly more protective than the status quo for those 18.
  - Severity: minor
  - Forward impact: none for AC-1's assertion (it accepts either). Those 18 tests now run against an isolated per-worker DB rather than a clean-per-test one — no behavioural change, since they previously accumulated state in the shared real DB.

- **The two offending modules opt in via a module-level autouse fixture rather than isolation being made autouse suite-wide**
  - Spec source: `.session/158-78-session.md`, TEA Assessment AC-3
  - Spec text: "wiring: the two unisolated modules pass under `-n 2 --dist loadfile`"
  - Implementation: added a module-scoped `_isolate_pg(pg_isolation)` autouse fixture to each of the two modules, rather than hoisting the truncate-per-test autouse up to `tests/agents/conftest.py`
  - Rationale: making the per-test TRUNCATE autouse across all of `tests/agents/` would tax ~2,250 tests that never touch Postgres. The suite-wide `_no_ambient_database_url` guard is what prevents recurrence — a future module that imports the helpers without isolation now lands on a throwaway DB rather than prod, and cannot corrupt real saves.
  - Severity: minor
  - Forward impact: a future module that imports `pg_store_with` without requesting `pg_isolation` gets an isolated-but-not-truncated database; it cannot reach prod, but may see leftover rows from earlier tests on the same worker.

<!-- delivery-findings-marker -->

### Dev (implementation)

- **Gap** (non-blocking): Eighteen tests beyond the two this story named were also binding the developer's real Postgres database — `tests/server/test_app.py`, `test_forensics_routes.py`, `test_lore_rag_wiring.py`, `test_culture_context.py`, `test_chargen_complete_no_hp_leak.py`, `test_scene_listing.py`, `test_pool_relationship_projection.py`, `dispatch/test_pregen_bestiary_90_1.py`. They are now redirected to an isolated per-worker database, but they never *request* isolation — they still just read whatever `SIDEQUEST_DATABASE_URL` happens to be. A follow-up could make each one bind explicitly (via `pg_isolation`) so the guard is defence-in-depth rather than the only thing standing between them and prod.
  Affects `sidequest-server/tests/server/` (eight modules should request `pg_isolation` explicitly).
  *Found by Dev during implementation.*

- **Improvement** (non-blocking): `tests/server/test_space_opera_swn_combat_e2e.py::test_firefight_resolves_on_hp_depletion_vs_content_ac` asserts that an unseeded d20 attack roll *hits* (`opponent_core.hp.current < hp_before`). Measured flake rate ~4% (baseline 1/20, with this change 1/29) — it fails whenever the roll misses. This is a concrete, reproducible instance of story **158-83**'s unseeded-global-`random` defect and is the single remaining nondeterminism in the default gate.
  Affects `sidequest-server/tests/server/test_space_opera_swn_combat_e2e.py` (seed the RNG or force the hit, under 158-83).
  *Found by Dev during implementation.*

- **Question** (non-blocking): TEA's finding that ~1,938 junk rows sit in the live `sidequest` database still stands — this story stops new pollution but deletes nothing. The count rose 2391 → 2405 *during* this story's own baseline runs (runs made at the pre-fix commit, before the guard existed), which is itself evidence of how fast it accumulated. Cleanup needs Keith's explicit authorisation and should precede any measurement work on story 166-8.
  Affects the live `sidequest` database (authorised cleanup pass).
  *Found by Dev during implementation.*
- **Improvement** (non-blocking): **Junk-row cleanup COMPLETED 2026-08-01 on Keith's explicit authorisation.** Deleted 1,950 synthetic sessions (1,949 `test-<hex8>` + 1 `tool-test`); all 20 child tables cascaded (`ON DELETE CASCADE`), removing ~6,494 events, ~1,609 game_state, ~2,073 narrative_log and ~159,866 turn_telemetry rows. 455 real `YYYY-MM-DD-<world>-<hex8>` play sessions retained and verified intact (455 sessions ↔ 455 game_state, 0 orphans, asset_ledger untouched at 127; a real save round-trips through `PgSaveRepository.load()`). Database 413 MB → 184 MB after `VACUUM FULL`. Full pre-cleanup backup at `~/.sidequest/backups/sidequest-pre-158-78-cleanup-20260801-181820.dump` (114 MB, `pg_restore -l` verified).
  Affects the live `sidequest` database (done).
  *Found by Dev during implementation.*

- **Gap** (non-blocking): **Story 166-8's premise is now stale.** It is scoped as "/api/debug/state full-scan pins the event loop — sync per-save load+migrate+span across **1849 saves**". After this cleanup the real save count is **455** — a 75% reduction — and the suite can no longer add to it. 166-8 should be re-measured (fresh py-spy) before any optimisation work; the endpoint may now be acceptable, or the remaining cost may sit somewhere other than the scan width. Do not optimise against the polluted baseline.
  Affects story 166-8 scope (re-measure before implementing).
  *Found by Dev during implementation.*

---
## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — mechanical data confirmed (ruff clean, format clean, pyright 0/0/0 on new file, AC 3/3, xdist modules 6/6). Challenged: its "SUCCESS / ready for review" framing is a rubber stamp; it ran one gate-adjacent slice, not the gate. I ran the full gate twice myself (see below). |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings (`edge_hunter: false`) — boundary conditions assessed by me: env-var shapes (unset/empty/whitespace), `_dbname("")`, None-URL short-circuit in AC-1's assert message, `--timeout` interaction. |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — assessed by me under Rule Compliance #1/#14. |
| 4 | reviewer-test-analyzer | Yes | findings | 6 | confirmed 4, downgraded 2, dismissed 0. Its AC-3 proof (revert slug fix only → AC-3 stays green, AC-2 goes red) is the strongest finding in this review. |
| 5 | reviewer-comment-analyzer | Yes | findings | 5 | confirmed 4, downgraded 1. Independently reached my `_isolate_pg` stale-docstring conclusion; verified 6 factual docstring claims as accurate. |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (`type_design: false`) — `slug: str \| None` sentinel and `Iterator[None]` vs `None` fixture annotations assessed by me and by rule-checker #3. |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings (`security: false`) — TRUNCATE identifier construction and DB-isolation (this repo's tenant-isolation analogue) assessed by me; see Rule Compliance #11 and the Isolation Audit. |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings (`simplifier: false`) — duplicate-isolation-logic sweep done by me (3 surviving copies, filed as a Delivery Finding). |
| 9 | reviewer-rule-checker | Yes | findings | 6 | confirmed 5, downgraded 1 (its #14 "silent fallback" reading — see Rule Compliance #14 for the rule-text argument, not a dismissal). Independently found the third helper consumer I had already located. |

**All received:** Yes (4 enabled returned, 5 disabled via `workflow.reviewer_subagents` and covered by me directly)
**Total findings:** 13 confirmed, 0 dismissed, 4 deferred to Delivery Findings as upstream/pre-existing

### Challenging my VERIFIEDs against subagent findings

Every `[VERIFIED]` below was re-checked against all four returning specialists. Two collisions, both resolved by re-reading the code rather than by assertion:

- I initially had "the two `_isolate_pg` module fixtures are load-bearing" as a VERIFIED. comment-analyzer contradicted it (high confidence). I re-tested empirically instead of arguing: with both fixtures neutralised, `-n 2 --dist loadfile` still gives **6 passed**. **My VERIFIED was wrong and is withdrawn** — downgraded to finding [DOC-1]. What they *do* buy showed up in the same experiment (a `psycopg_pool` `PythonFinalizationError` at shutdown without them), so they are not dead code.
- I initially had "AC-3 is the wiring test for the whole fix" as a VERIFIED. test-analyzer contradicted it with a decisive experiment. **Withdrawn** — downgraded to finding [TEST-1].

## Rule Compliance

Enumerated against `.pennyfarthing/gates/lang-review/python.md` (13 checks) and the five `<critical>` rules in `CLAUDE.md`. Every function/fixture in the diff, not one exemplar each. 34 instances across 18 rules.

**#1 Silent exception swallowing** — 0 instances. No `try`/`except`/`suppress` anywhere in the diff. Compliant.

**#2 Mutable defaults** — 2 instances, both compliant. `pg_store_with(slug: str | None = None)` and `pg_empty_store(slug: str | None = None)` (`tests/agents/tools/conftest.py:44,69`) use the `None` sentinel with `slug if slug is not None else _unique_slug(...)`, which is stricter than the checklist's own suggested `x or default` — it correctly distinguishes an explicit `""` from unset.

**#3 Type annotations** — 13 instances, **1 violation**. `_pg_isolation(pg_isolation: None)` at `tests/agents/tools/conftest.py:19` has no return annotation; it `yield`s, so it should be `-> Iterator[None]` to match the `pg_isolation` it delegates to (`tests/conftest.py:351`). Both sibling `_isolate_pg` fixtures in this same diff *are* annotated, so this is an inconsistency inside one changeset. Confirmed [RULE-1]. `_no_ambient_database_url -> None` is correct, not a gap — it has no `yield` because `monkeypatch` self-reverts.

**#4 Logging** — 0 applicable instances. Neither new fixture has an error branch. Compliant.

**#5 Path handling** — 1 instance, compliant. `REPO_ROOT = Path(__file__).resolve().parent.parent.parent` uses pathlib with `.resolve()`.

**#6 Test quality** — 3 instances, 0 vacuous. Each AC test asserts a specific value with a diagnostic message. I verified each is genuinely RED at base rather than trusting the labels — see the Reviewer Assessment. Related but distinct coverage gaps are [TEST-1]/[TEST-2].

**#7 Resource leaks** — 2 instances, compliant. `psycopg.connect(...)` is inside `with` (`tests/conftest.py:372`); `subprocess.run` is blocking and self-cleaning. (A separate, pre-existing pool leak lives *outside* the diff — Delivery Findings.)

**#8 Unsafe deserialization** — 0 instances. No pickle/eval/`yaml.load`/`shell=True`.

**#9 Async pitfalls** — 0 instances. No async code added.

**#10 Import hygiene** — 7 instances, compliant. `import uuid` is used; all module imports used; the function-local imports are genuine runtime imports (not annotation-only), so correctly outside `TYPE_CHECKING`.

**#11 SQL construction** — 1 instance, **1 literal violation**. `tests/conftest.py:374-379` builds `TRUNCATE {names} RESTART IDENTITY CASCADE` by f-string over identifiers from `pg_tables`, quoting with `f'"{r[0]}"'` rather than `psycopg.sql.Identifier`. Naive quoting does not double embedded `"`. Confirmed [RULE-2] at **Low**: the identifiers come from a catalog in a database this process just created and migrated (not external input), and the code is a **verbatim relocation** of pre-existing lines, not new logic. Per the project-rules directive I am downgrading severity with rationale, not dismissing.

**#12 Dependency hygiene** — 0 instances. No dependency files changed.

**#13 Fix-introduced regressions** — re-scanned commit `2b806d33` against #1-#12. No broadened handling, no reintroduced mutable defaults. Only #3 and #11 carry forward.

**#14 CLAUDE.md `<critical>` No Silent Fallbacks** — 5 instances, **0 violations, 1 confirmed adjacent finding**.
- `monkeypatch.delenv(..., raising=False)` (`:56`) — compliant. Idempotent-unset idiom for a possibly-absent var; suppresses no application signal.
- The `_PG_ADMIN_ENV` guard (`:55`) — compliant. Mirrors the pre-existing `_pg_admin_conninfo()` skip-if-unset convention already in this file.
- The strip branch (`:56-57`) — **actively compliant**, and the best part of the design: with no test Postgres there is no safe target, so the var is removed and the first pool access raises `MissingDatabaseUrlError`. That is fail-loud.
- The redirect (`:58-62`) — rule-checker rated this a violation. **I am downgrading, and citing rule text rather than overriding it.** The rule reads "If something isn't where it should be, fail loudly. Never silently try an alternative path, config, or default." A fallback is a *substitute reached for when the primary is missing or broken*. Here the primary is present and healthy and is overridden unconditionally as a deliberate sandbox policy — the failure mode the rule guards ("masks configuration problems") is inverted, since the whole point is that the operator's config must **not** reach the test process. The in-repo precedent is explicit and accepted: `_isolate_monster_manuals` (story 162-1, `tests/conftest.py:33`) does exactly this for `~/.sidequest`, and Dev cites it. Not a violation. **The residual real concern is the failure mode when the redirect target is unreachable** — filed separately as [CRIT-ADJACENT] below, which is a distinct defect from the doctrine question.
- The dead `"SIDEQUEST_DATABASE_URL": plain` binding passed to AC-3's subprocess — confirmed as part of [TEST-1].

**#15 CLAUDE.md `<critical>` No Stubbing** — 1 instance, compliant. The `_pg_isolation` shim is not a stub: naming `pg_isolation` as a parameter is what forces pytest to run the real TRUNCATE/monkeypatch/pool-reset body for every test in that directory. It is live wiring with an empty body by necessity, not a placeholder. Independently verified — neutralising it produces a real behavioural change.

**#16 CLAUDE.md `<critical>` Don't Reinvent — Wire Up What Exists** — 1 instance, compliant, and done well. The fix **hoists** the existing `_pg_isolation` body verbatim rather than writing a second one, and reuses the `{prefix}-{uuid4().hex[:8]}` slug convention already established at `tests/integration/test_mutation_wiring.py:208`. I found an even closer in-repo precedent Dev did not cite — `tests/server/conftest.py:73-84`, story 97-6 — which fixed the *identical* shared-default-slug bug for the server helper for the *identical* reason. Same conclusion, independently reached. (That 3 further copies of the bind/truncate/close logic survive elsewhere is a pre-existing condition, filed as a Delivery Finding, not a violation by this diff.)

**#17 CLAUDE.md `<critical>` Verify Wiring, Not Just Existence** — 1 instance, **1 violation**. `_UNISOLATED_HELPER_MODULES` (`tests/infrastructure/test_158_78_pg_isolation_coverage.py:62-65`) lists two modules; a repo-wide grep for importers of the helper finds **three** — `tests/server/test_pool_relationship_projection.py:165` also does `from tests.agents.tools.conftest import pg_store_with`. The fix's completeness was verified against the two the CI failure happened to surface, not against every consumer. Confirmed [RULE-3] at **Medium** (not High: the global redirect does cover it, and Dev independently documented it in Delivery Findings).

**#18 CLAUDE.md `<critical>` Every Test Suite Needs a Wiring Test** — 1 instance, compliant. AC-3 is a real subprocess-driven reproduction of the reported `-n auto --dist loadfile` failure, not a source-text scan. I confirmed it is genuinely RED at base. Its coverage *claim* is overstated — [TEST-1] — but the requirement is met.

### Isolation Audit (this repo's tenant-isolation analogue)

SideQuest has no tenants; the equivalent blast-radius question is **"can any code path reach the developer's real database?"** I enumerated every path rather than spot-checking:

1. `_no_ambient_database_url` (autouse, root conftest, declared **first** so it wins fixture ordering) — redirects or strips for every test. No opt-out marker exists; that is correct for a safety policy.
2. `pg_isolation`'s TRUNCATE target derives from `migrated_db`, **never** from the ambient env — `migrated_db` always builds `sq_test_{worker_id}_{uuid8}`. **There is no input by which `pg_isolation` could TRUNCATE the real database, even if `SIDEQUEST_TEST_DATABASE_URL` were set to the real DB's URL.** This is the single most important safety property in the diff and it holds. `tests/conftest.py:369-379` + `:311-322`.
3. Import-time escapes — I grepped for module-level `get_pool()` in `tests/`: **none**; every call is inside a function or fixture, so the autouse fixture always precedes it. No collection-time hole.
4. Tests that rebind the var themselves — 2 found (`test_bug_report_endpoint.py:17`, `test_91_5_dark_spend_reconcile_endpoint.py:75`), both to the deliberately-unreachable `postgresql://localhost/test_notreal`. Harmless, but invisible to AC-1 — [TEST-2].
5. `alembic_version` is excluded from the TRUNCATE (`tablename <> 'alembic_version'`), so the per-test truncate cannot destroy the session-scoped migration state the whole worker depends on. Correct.

### Devil's Advocate

Arguing this code is broken.

**The strongest attack, and it lands.** This fixture makes Postgres a hard dependency of all ~15,000 tests, including the thousands with no database in them. Everyone in the pipeline tested with the service up. I tested with it *configured but unreachable* — the state of any machine that rebooted while `SIDEQUEST_TEST_DATABASE_URL` sits in a shell profile — and `tests/foundation` went from **18 passed to 18 errors**, while base was untouched. A dev in that state previously kept 95% of the suite and could work; now they get 15,056 identical stack traces and are fully blocked. For a story whose entire subject is gate reliability, adding a new way for the gate to die wholesale is squarely on-topic, and nothing in TEA's or Dev's analysis mentions it. That is [CRIT-ADJACENT].

**Second attack: the fix hides the mess it didn't clean.** Twenty-odd tests were never isolated. The global redirect makes them all silently work. A future reader sees a green suite and infers isolation that isn't there; the guard is load-bearing for tests that never asked for it, and narrowing it later would quietly re-expose them. Dev documented this honestly in Delivery Findings, which is the right call — but the *code* carries no marker, and the AC-1 tripwire cannot see it.

**Third: what a confused user does.** They open `test_use_mutation_tool.py`, read "Without this it bound the developer's real database," and believe deleting `_isolate_pg` leaks to production. It doesn't — I proved it. Or they trust the claim, keep it for the wrong reason, and never learn what it actually buys (pool close). A comment that is wrong about *why* is worse than none.

**Fourth: what a stressed machine does.** I hypothesised 28 simultaneous `CREATE DATABASE` calls would contend on `template1` — a classic CI flake. **Three runs at `-n auto`, no contention, hypothesis not confirmed**; PG 18's WAL_LOG strategy handles it. Reporting the negative result because a plausible-and-refuted theory is worth as much as a confirmed one. But the same sweep found the real artifact: `migrated_db` drops its database in a `finally`, which does not survive a kill, and this change takes creation from "workers running PG tests" to "all 28." There are **521 orphaned `sq_test_*` databases holding 4.5 GB** on the dev server right now, and no reaper recipe exists anywhere in `justfile` or `scripts/`. Mostly historical accumulation by OID spread, but this change raises the rate.

**Fifth: the malicious-input angle** is thin, correctly. The TRUNCATE identifiers come from a catalog in a database the process just created; there is no attacker-reachable path. I checked whether a hostile `SIDEQUEST_TEST_DATABASE_URL` could aim the TRUNCATE at the real database — it cannot, because the target is always derived from the freshly-created `sq_test_*` name.

**Where the attack fails.** I tried hard to break the core claim and could not. All three ACs are genuinely red at base and green at head; I verified each *independently*, including reverting only the helper change to confirm AC-2 guards the slug fix on its own. The isolation property in the Isolation Audit holds under every input I could construct. This is careful work.

### Reviewer (audit)

- **TEA: "AC-2 (unique slug) exceeds the literal reported symptom"** → ✓ **ACCEPTED by Reviewer.** Agrees with author reasoning, and the scope expansion is vindicated by evidence TEA did not have: `tests/server/conftest.py:73-84` (story 97-6) records the *identical* shared-default-slug bug being fixed for the server-side helper for the identical reason. This was a known, recurring footgun in this repo, not a speculative one. TEA offered to drop AC-2 if I judged it out of scope — I do not; keep it. I independently confirmed AC-2 carries its own weight: reverting only the helper change turns AC-2 red while everything else stays green.
- **TEA: "No test asserts the ~1,938 existing junk rows are removed"** → ✓ **ACCEPTED by Reviewer.** Refusing to script destructive deletes against Keith's live database inside a test-determinism story is the correct call. The cleanup subsequently happened under explicit authorisation with a verified backup, which is how it should have gone.
- **Dev: "Redirected `SIDEQUEST_DATABASE_URL` instead of stripping it"** → ✓ **ACCEPTED by Reviewer, with one caveat carried forward as a finding.** TEA's AC-1 explicitly admitted both outcomes and asked Dev to choose; Dev tried option (a) first, found empirically that it converted 18 silent prod-DB consumers into hard failures, and chose (b). That is a deviation resolved with evidence rather than preference, which is the standard. The caveat: the deviation analysis weighs the redirect's cost only as *migration effort for 18 tests* and never considers its **failure mode** — what happens when the redirect target is unreachable. That gap is [EDGE] below. Accepting the choice; the missing analysis is the finding.
- **Dev: "The two offending modules opt in via a module-level autouse fixture rather than isolation being made autouse suite-wide"** → ✓ **ACCEPTED by Reviewer.** Not taxing ~2,250 non-Postgres tests in `tests/agents/` with a per-test TRUNCATE is right, and Dev's stated forward impact ("a future module that imports `pg_store_with` without requesting `pg_isolation` gets an isolated-but-not-truncated database") is **accurate** — I verified exactly that on the third consumer. Honest and correct. What the entry gets wrong is which mechanism does the work: it implies the module fixtures are the protection, when the suite-wide guard and the unique slugs are. See [DOC].
- **UNDOCUMENTED — spotted by Reviewer, not logged by TEA or Dev:** the redirect makes a reachable Postgres a **precondition for every test in the suite**, not just Postgres tests. Spec said "no test may bind the developer's real database"; code additionally says "no test runs at all unless `migrated_db` can be built." With PG configured but unreachable, `tests/foundation` goes 18 passed → 18 errors; base is unaffected. Severity: **M**. Filed as [EDGE].

<!-- delivery-findings-marker -->

### Reviewer (code review)

- **Gap** (non-blocking): With `SIDEQUEST_TEST_DATABASE_URL` set but Postgres unreachable, the autouse `_no_ambient_database_url` fixture forces `migrated_db` for every test, so the *entire* suite errors rather than just the Postgres tests — measured `tests/foundation` 18 passed (base) → 18 errors (HEAD). CI is shielded by the `pg_isready` service healthcheck; local developers are not. Suggested shape: fall back to the existing strip-and-fail-loud branch when the admin URL is set but unreachable, so a Postgres outage costs only the Postgres tests.
  Affects `sidequest-server/tests/conftest.py` (add an unreachable-target branch to `_no_ambient_database_url`).
  *Found by Reviewer during code review.*

- **Improvement** (non-blocking): `test_pregen_bestiary_90_1.py::test_seed_manual_populates_encounters_for_wwn_world[evropi]` failed once in my two full `-n auto` gate runs (run 1: 15055 passed / 1 failed; run 2: 15056 / 0). It consumes **26.18s of the repo's 30s `--timeout` addopt on an idle machine** and tips over under 28-way load. I verified this is **not** caused by this story: the same module at base commit `d1ce4443` against an equivalent throwaway database measures 26.08s — timing-neutral. This is a **second, independent** gate flake source alongside 158-83's unseeded-RNG test, and the gate will not be reliably 100% green until both are addressed. Cheapest fix is a per-test `@pytest.mark.timeout` raise or splitting the pregen work.
  Affects `sidequest-server/tests/server/dispatch/test_pregen_bestiary_90_1.py` (timeout headroom) and epic 158's "gate is green" definition of done.
  *Found by Reviewer during code review.*

- **Gap** (non-blocking): The `migrated_db` fixture drops its throwaway database in a `finally`, which does not survive a killed worker, Ctrl-C, or a timeout kill — and this story takes database creation from "workers that run Postgres tests" to "all 28 workers on every run." The dev Postgres server currently holds **521 orphaned `sq_test_*` databases totalling 4.5 GB**, and no reaper exists in `justfile` or `scripts/`. Mostly historical accumulation (OID spread is wide), but the per-run creation rate is now higher. A `just pg-reap` recipe dropping `sq_test_*` older than a day would close it.
  Affects `sidequest-server/tests/conftest.py` and the orchestrator `justfile` (add a reaper recipe).
  *Found by Reviewer during code review.*

- **Improvement** (non-blocking): Three near-verbatim copies of the bind/TRUNCATE/`close_pool` logic this story just hoisted into the shared `pg_isolation` fixture still exist and were not migrated to it: `tests/server/conftest.py:1000-1013`, `tests/magic/test_47_9_innate_proactive.py:795-817`, `tests/integration/test_resources_wired_on_session_create.py:70-83` (plus a partial at `tests/dungeon/conftest.py:203-204`). Scattered isolation logic is precisely what let a consumer get missed in the first place; now that one canonical fixture exists, the duplicates are the next drift.
  Affects the four listed files (migrate each to request the shared `pg_isolation`).
  *Found by Reviewer during code review.*

- **Improvement** (non-blocking): The connection pool is process-global with `max_size=16` (`sidequest/game/db_pool.py:29`) and is only closed by `pg_isolation`'s teardown. Postgres-touching tests that do not request that fixture leak an open pool until process exit — reproducible as a `psycopg_pool` `PythonFinalizationError: cannot join thread at interpreter shutdown` on `tests/server/test_pool_relationship_projection.py` (present at base too, so pre-existing). With 28 workers against `max_connections = 100`, this is latent headroom pressure worth a deliberate look rather than a surprise later.
  Affects `sidequest-server/sidequest/game/db_pool.py` and the modules in the Dev-logged eighteen.
  *Found by Reviewer during code review.*

## Reviewer Assessment

**Verdict:** APPROVED

The story fixes what it set out to fix, and — unusually — I could verify that independently rather than take it on report. I reconstructed the RED state three separate ways and each acceptance test failed at base for the reason it claims: AC-1 fails against my real ambient `SIDEQUEST_DATABASE_URL`; AC-2 fails with a precise torn-row message (`the first store reloaded a DIFFERENT session's snapshot (mutant_wasteland/dead_lands)`) when only the helper change is reverted; AC-3 fails end-to-end under `-n 2 --dist loadfile` at base. None of these are ceremonial. The central safety property holds under every input I could construct: `pg_isolation`'s TRUNCATE target is always derived from the freshly-created `sq_test_*` database and never from the ambient environment, so there is no reachable path by which the suite can truncate the real one.

I ran the full default gate twice myself rather than accept Dev's two clean runs — a story about gate reliability cannot be signed off on someone else's runs. Run 1 came back **15055 passed / 1 failed**, which is not what Dev reported. I chased it: the failing module is one of the eighteen whose database binding this story changed, so it looked like a regression. It is not. `--durations` shows it burning 26.18s of the repo's 30s timeout on an idle machine, and the same module at base against matched conditions measures 26.08s — timing-neutral, therefore pre-existing. Run 2 was clean at 15056. The honest statement is that this story removed the xdist shared-state races it targeted, and the gate still has two unrelated flake sources (this timeout-headroom test and 158-83's unseeded RNG).

No Critical or High findings. Nine Medium/Low findings below, none of which block.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [EDGE] Medium | Postgres configured-but-unreachable now errors the *entire* suite, not just PG tests (18 passed → 18 errors on `tests/foundation`; base unaffected). Undocumented deviation. | `tests/conftest.py:55-62` | Add an unreachable-target branch that falls through to the existing strip-and-fail-loud path |
| [TEST] Medium | AC-3 does not exercise the slug fix it claims to. `--dist loadfile` puts the two files on different workers with different databases, so collision cannot occur — proven by reverting only the slug change: AC-2 goes red, AC-3 stays green. The `"SIDEQUEST_DATABASE_URL": plain` env binding is also dead, re-overridden by the child's own autouse fixture. | `test_158_78_pg_isolation_coverage.py:169,187` | Narrow the docstring to what it verifies, or force both files onto one database |
| [DOC] Medium | Both `_isolate_pg` docstrings claim "Without this it bound the developer's real database and raced ... on a shared session slug." Both claims are false as shipped — I neutralised both fixtures and got 6 passed under `--dist loadfile`. What they actually buy is the per-test TRUNCATE and pool close. | `test_102_5_wn_tool_narrator_wiring.py:56`, `test_use_mutation_tool.py:55` | Reword to the real rationale |
| [RULE] Medium | `_UNISOLATED_HELPER_MODULES` names two consumers; a repo-wide grep finds three. Completeness verified against the failures CI surfaced, not against every importer. | `test_158_78_pg_isolation_coverage.py:62-65`, `tests/server/test_pool_relationship_projection.py:165` | Enumerate importers programmatically so a fourth consumer cannot appear unnoticed |
| [TEST] Low | AC-1 is a per-process tripwire, not the suite-wide invariant its name asserts — it reads only its own environment. Two tests rebind the var to a non-`sq_test_*` value invisibly to it. | `test_158_78_pg_isolation_coverage.py:76` | Narrow the claim, or enforce via `pytest_runtest_teardown` |
| [TYPE] Low | `_pg_isolation` has no return annotation despite `yield`ing; should be `-> Iterator[None]` like the fixture it delegates to. Both sibling fixtures in this same diff are annotated. | `tests/agents/tools/conftest.py:19` | Add `-> Iterator[None]` |
| [SEC] Low | TRUNCATE identifiers interpolated via f-string with naive `f'"{r[0]}"'` quoting rather than `psycopg.sql.Identifier`. Downgraded, not dismissed: input is the process's own freshly-migrated catalog, and the lines are a verbatim relocation. | `tests/conftest.py:374-379` | Optional hardening to `sql.Identifier` |
| [DOC] Low | `pg_empty_store`'s slug default changed identically to `pg_store_with`'s, but only the latter's docstring was updated. | `tests/agents/tools/conftest.py:69` | Mirror the sentence |
| [SIMPLE] Low | Three near-verbatim copies of the just-hoisted isolation logic survive un-migrated (pre-existing; filed as a Delivery Finding). | `tests/server/conftest.py:1000`, `tests/magic/test_47_9_innate_proactive.py:795`, `tests/integration/test_resources_wired_on_session_create.py:70` | Migrate to the shared `pg_isolation` |

**Data flow traced:** developer shell `SIDEQUEST_DATABASE_URL` → autouse `_no_ambient_database_url` (root conftest, declared first so it wins ordering) → redirected to `sq_test_{worker_id}_{uuid8}` or stripped → `db_config.database_url()` → `db_pool.get_pool()` → `PgSaveRepository`. Safe because the redirect target is always derived from `migrated_db`, never from the ambient value, and because I grepped for module-level `get_pool()` in `tests/` and found none — every call site sits inside a function or fixture, so no collection-time path escapes the fixture.

**Pattern observed (good):** the hoist reuses rather than reimplements — `tests/conftest.py:351-383` is the old body moved verbatim, and `_unique_slug` (`tests/agents/tools/conftest.py:31-41`) adopts the repo's established `{prefix}-{uuid4().hex[:8]}` convention. A non-obvious consequence held: `is_test_session` matches on `slug.startswith(("test-", "tool-test"))` (`sidequest/telemetry/watcher_hub.py:476`), so the new `tool-test-{hex8}` slugs remain correctly classified as test sessions and the byte-identical cross-repo prefix contract in `tests/fixtures/test_session_prefix_contract.json` is preserved. Had the new slug shape broken that prefix, test rows would have started leaking into live GM-panel views — it doesn't.

**Error handling:** [SILENT] assessed directly, since silent-failure-hunter is disabled. No swallowed exceptions exist in the diff — zero `try`/`except`/`suppress`. `monkeypatch.delenv(..., raising=False)` (`tests/conftest.py:56`) is the idempotent-unset idiom and suppresses no application signal. The no-Postgres branch is genuinely fail-loud: the variable is stripped so the first pool access raises `MissingDatabaseUrlError` rather than reaching for a default, which satisfies **No Silent Fallbacks** as written. The redirect branch is a deliberate sandbox with accepted in-repo precedent (`_isolate_monster_manuals`, story 162-1), not a fallback — reasoning under Rule Compliance #14. Its one real weakness is the unreachable-target case, which is [EDGE].

**Handoff:** To Camina (SM) for finish-story.