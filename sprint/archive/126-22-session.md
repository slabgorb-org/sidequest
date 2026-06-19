---
story_id: "126-22"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 126-22: [PERF] projection_cache unbounded growth (~3k rows/session, 4.3M rows) — add eviction/TTL/per-session cap + turn_telemetry retention to stop save-DB bloat

## Story Details
- **ID:** 126-22
- **Jira Key:** none
- **Workflow:** tdd
- **Stack Parent:** none
- **Branch:** feat/126-22-projection-cache-retention (gitflow, server subrepo, base: develop)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-19T21:49:51Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-19T20:56:59Z | 2026-06-19T20:59:19Z | 2m 20s |
| red | 2026-06-19T20:59:19Z | 2026-06-19T21:15:33Z | 16m 14s |
| green | 2026-06-19T21:15:33Z | 2026-06-19T21:25:07Z | 9m 34s |
| review | 2026-06-19T21:25:07Z | 2026-06-19T21:36:53Z | 11m 46s |
| green | 2026-06-19T21:36:53Z | 2026-06-19T21:44:42Z | 7m 49s |
| review | 2026-06-19T21:44:42Z | 2026-06-19T21:49:51Z | 5m 9s |
| finish | 2026-06-19T21:49:51Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): `turn_telemetry` is excluded from the only existing cleanup by design — `sessions._PER_SESSION_TABLES` deliberately omits it ("global-lifecycle ... survive"). Confirm the new retention does not break ADR-124 save-forensics, which reads `turn_telemetry` by round; the keep-last-N-rounds window must be generous enough to preserve a meaningful forensic tail. Affects `sidequest/game/pg/sessions.py` + `sidequest/game/pg/forensic.py` (Dev picks the round window; Reviewer sanity-checks the value vs forensic needs). *Found by TEA during test design.*
- **Question** (non-blocking): the prune DELETEs are new SQL on `projection_cache` / `turn_telemetry`. Confirm there are supporting indexes — `projection_cache` PK is `(session_id, event_seq, player_id)`, so a per-player keep-last window query (`PARTITION BY player_id ORDER BY event_seq`) is index-friendly; `turn_telemetry` round filtering wants `(session_id, round)` coverage. A perf fix that adds an unindexed full-scan DELETE would be self-defeating. Affects `sidequest/game/pg/events.py` (+ possibly an alembic index migration). *Found by TEA during test design.*
- **Gap** (non-blocking): the prune SQL must stay parameterized (CWE-89) — `session_id` flows into a DELETE; never f-string it. Not unit-assertable (row-count tests pass either way), so this is a Dev-self-review (python lang-review #11) + Reviewer item. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking, RESOLVES TEA's index Question): the prune queries are fully index-supported by existing indexes — no new migration. `idx_projection_cache_player (session_id, player_id, event_seq)` exactly serves the per-player keep-last window (`PARTITION BY player_id ORDER BY event_seq DESC`), and `idx_turn_telemetry_round (session_id, round)` exactly serves the round-retention (`DISTINCT round ... ORDER BY round DESC`). Verified against the live DB. The perf fix adds no unindexed scan. *Found by Dev during implementation.*
- **Improvement** (non-blocking, RESOLVES TEA's CWE-89 Gap): all three retention SQL statements (`_PRUNE_PROJECTION`, `_PRUNE_TELEMETRY`) are fully parameterized — `session_id` and the keep-last bounds are passed as `%s` params, never interpolated. *Found by Dev during implementation.*
- **Question** (non-blocking, for Reviewer): the keep-last values are `PROJECTION_CACHE_KEEP_LAST_PER_PLAYER=200` and `TURN_TELEMETRY_KEEP_LAST_ROUNDS=100`. 100 rounds is a generous forensic tail (Keith's longest sessions are ~140 turns), but Reviewer should sanity-check it against ADR-124 save-forensics needs. The prune runs on every `save()` (per-turn + disconnect); under the cap it deletes 0 rows via an index-only scan — cheap, but worth a Reviewer eye since this is a perf story. Affects `sidequest/game/pg/events.py`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): a prune fault inside `PgSaveRepository.save()` propagates as a snapshot-save failure — it contaminates `last_save_failure` (gates `close_store` on disconnect) and skips the post-save per-turn narrative-log write. Affects `sidequest/game/pg/save_repository.py` (isolate the two prune calls in a log-and-continue try/except, mirroring the lore-persist isolation at `websocket_session_handler.py:594-606`). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `prune_projection_cache(keep_last_per_player=0)` deletes ALL rows for the session while `prune_turn_telemetry(keep_last_rounds=0)` deletes NOTHING — inverted, unguarded zero-semantics. Add `>= 1` preconditions. Affects `sidequest/game/pg/events.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the `rows_pruned` span attribute is unset if `session_tx` raises (set after the tx block). Initialize `pruned = 0` and emit it even on the failure path so the GM panel can distinguish "pruned 0" from "prune errored." Folds into the isolation fix. Affects `sidequest/game/pg/events.py`. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 2 findings (1 Gap, 0 Conflict, 1 Question, 0 Improvement)
**Blocking:** 1 BLOCKING items — see below

**BLOCKING:**
- **Gap:** a prune fault inside `PgSaveRepository.save()` propagates as a snapshot-save failure — it contaminates `last_save_failure` (gates `close_store` on disconnect) and skips the post-save per-turn narrative-log write. Affects `sidequest/game/pg/save_repository.py`.

- **Question:** the prune DELETEs are new SQL on `projection_cache` / `turn_telemetry`. Confirm there are supporting indexes — `projection_cache` PK is `(session_id, event_seq, player_id)`, so a per-player keep-last window query (`PARTITION BY player_id ORDER BY event_seq`) is index-friendly; `turn_telemetry` round filtering wants `(session_id, round)` coverage. A perf fix that adds an unindexed full-scan DELETE would be self-defeating. Affects `sidequest/game/pg/events.py`.

### Downstream Effects

- **`sidequest/game/pg`** — 2 findings

### Deviation Justifications

2 deviations

- **Tests pin a specific retention strategy, where the story left it open ("eviction / TTL / per-session cap / prune-on-session-end").**
  - Rationale: a per-player window directly satisfies "a multi-turn session does not accumulate ~3k unbounded rows" and is provably safe — `projection/cache_fill.lazy_fill` rebuilds pruned cache rows from the event log on reconnect, and live resume only reads the head of the window. turn_telemetry is forensic (ADR-124), not a rebuildable cache, so it gets round-retention rather than wholesale eviction; NULL-round rows are un-attributable infra rows and must not be silently dropped (No Silent Fallbacks). Dev owns the threshold *values* (the keep-last constants) — tests read them via the importable constants, not hard-coded magic.
  - Severity: minor
  - Forward impact: If Dev/Reviewer prefer a different mechanism (e.g. TTL), the behavior + OTEL-span tests still largely hold; only the strategy-specific assertions need re-pointing.
- **Wiring test pins the production trigger to `PgSaveRepository.save()`, where the story named no trigger.**
  - Rationale: the measured bug is literally "nothing prunes"; a prune method with no production caller would not fix it, so a *behavioral* wiring assertion through a real production path is mandatory. `save()` is the lightest real path that runs every turn and on disconnect, bounding both live and dead-session growth.
  - Severity: minor
  - Forward impact: If Dev wires the trigger elsewhere (disconnect-only, inline-on-write, periodic sweep), re-point the two `test_save_*_in_production_path` tests; the unit-level prune tests are trigger-agnostic.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Tests pin a specific retention strategy, where the story left it open ("eviction / TTL / per-session cap / prune-on-session-end").**
  - Spec source: context-story-126-22.md, AC-1 / AC-2
  - Spec text: "Add an eviction / TTL / per-session cap (or prune-on-session-end) for projection_cache; add a retention policy for turn_telemetry."
  - Implementation: RED tests pin (a) `projection_cache` → a **per-(session, player) keep-last-N window** (`prune_projection_cache(keep_last_per_player)`), and (b) `turn_telemetry` → **keep-last-N-rounds**, NULL-round rows retained (`prune_turn_telemetry(keep_last_rounds)`). TTL / time-based eviction was NOT chosen.
  - Rationale: a per-player window directly satisfies "a multi-turn session does not accumulate ~3k unbounded rows" and is provably safe — `projection/cache_fill.lazy_fill` rebuilds pruned cache rows from the event log on reconnect, and live resume only reads the head of the window. turn_telemetry is forensic (ADR-124), not a rebuildable cache, so it gets round-retention rather than wholesale eviction; NULL-round rows are un-attributable infra rows and must not be silently dropped (No Silent Fallbacks). Dev owns the threshold *values* (the keep-last constants) — tests read them via the importable constants, not hard-coded magic.
  - Severity: minor
  - Forward impact: If Dev/Reviewer prefer a different mechanism (e.g. TTL), the behavior + OTEL-span tests still largely hold; only the strategy-specific assertions need re-pointing.
- **Wiring test pins the production trigger to `PgSaveRepository.save()`, where the story named no trigger.**
  - Spec source: context-story-126-22.md, AC-1; CLAUDE.md "Every Test Suite Needs a Wiring Test" / "No half-wired features"
  - Spec text: (no trigger specified) — "fixes the CAUSE so it doesn't re-bloat."
  - Implementation: the wiring tests drive the real `PgSaveRepository.save()` (the per-turn + on-disconnect persistence path) and assert the bound is enforced + a prune span fires. Full `WebSocketSessionHandler.cleanup()` was rejected as a wiring target — existing cleanup tests use `AsyncMock`/fakes, so a real-DB full-handler drive would be brittle.
  - Rationale: the measured bug is literally "nothing prunes"; a prune method with no production caller would not fix it, so a *behavioral* wiring assertion through a real production path is mandatory. `save()` is the lightest real path that runs every turn and on disconnect, bounding both live and dead-session growth.
  - Severity: minor
  - Forward impact: If Dev wires the trigger elsewhere (disconnect-only, inline-on-write, periodic sweep), re-point the two `test_save_*_in_production_path` tests; the unit-level prune tests are trigger-agnostic.

### Dev (implementation)
- No deviations from spec. Implemented exactly the contract TEA pinned: the two prune methods on `PgEventStore`, the two OTEL spans + `SpanRoute` registrations, the two keep-last constants, and the `PgSaveRepository.save()` wiring. Constant values (200 / 100) were explicitly delegated to Dev by the TEA deviation, and the existing indexes cover the queries, so no schema deviation either.

### Reviewer (audit)
- **TEA deviation — "Tests pin a per-(session,player) keep-last window + keep-last-rounds, not TTL."** → ✓ ACCEPTED by Reviewer: the window strategy is provably safe (lazy_fill rebuilds, verified against `cache_fill.py` + `connect.py` resume) and directly satisfies AC-1; TTL was reasonably not chosen.
- **TEA deviation — "Wiring test pins the production trigger to `PgSaveRepository.save()`."** → ✗ FLAGGED by Reviewer: the *trigger choice itself* is sound (save() is the right per-turn + disconnect path), BUT wiring a best-effort prune **unguarded** into the durable-save path is the source of the HIGH finding below — `save()` now propagates a cleanup-DELETE fault as a snapshot-save failure, contaminating `last_save_failure`/`close_store` and skipping per-turn narrative logging. The trigger is right; the *un-isolated* wiring is the defect. Fix is to isolate the prune (log-and-continue), mirroring the existing lore-persist isolation at `websocket_session_handler.py:594-606`. See severity table.
- **Dev deviation — "No deviations from spec."** → ✓ ACCEPTED by Reviewer as to scope/strategy, with the caveat that the un-isolated `save()` wiring (which Dev did not flag as a risk) is a robustness regression — captured as the HIGH finding, not a spec deviation.
- **Reviewer (undocumented):** none — no further spec divergence beyond what TEA/Dev logged.
- **Round 2 (re-review):** the FLAGGED deviation (the *un-isolated* `save()` wiring) is now ✓ RESOLVED — the rework isolates the two prune calls in a loud log-and-continue `try/except` (verified: `save_snapshot()` stays outside the guard at `save_repository.py:157`). The trigger choice (`save()`) stands. All deviations now ACCEPTED.

## Sm Assessment

**Setup complete — routing to TEA (Argus Panoptes) for the RED phase.**

- **Story:** 126-22 — [PERF] `projection_cache` unbounded growth. Measured 2026-06-19 during save-DB rotation: 4,313,951 `projection_cache` rows + 470,647 `turn_telemetry` rows for only 1,399 sessions (~3k projection_cache rows/session). Root-cause fix so the save DB does not re-bloat after the truncate.
- **Workflow:** tdd (phased) · **Repo:** sidequest-server only · **Branch:** `feat/126-22-projection-cache-retention` (base `develop`).
- **Context doc:** `sprint/context/context-story-126-22.md`.

**What RED must pin down (no explicit ACs on the story — TEA derives them):**
1. `projection_cache` gets a bound — eviction / TTL / per-session cap / prune-on-session-end. First locate the write path (`grep -rn projection_cache` in the server repo) to choose the right eviction point; align with the existing persistence substrate (ADR-115 Postgres-per-session; projection/state-mirror path ADR-026/027/133).
2. `turn_telemetry` gets a retention policy (growth expected, but currently unbounded).
3. A test that proves per-session row growth is **bounded** after the fix (the measured ~3k/session no longer accrues without limit).
4. OTEL: per CLAUDE.md's Observability Principle, the eviction/retention decision should emit a watcher event so the GM panel can verify it fires — RED should assert the span is emitted, not just the row count.

**Heads-up for Dev (Hephaestus) later — pre-existing, NOT this story:** ~13 server test failures vs current content `develop` (WWN migration) and ~18 OTEL span-count tests that deadlock under full parallel run. Run affected files serially with `-n0`; classify these as pre-existing.

**Verdict:** Clean standalone perf fix, no deps, merge gate open. Ready for RED.

---
## TEA Assessment

**Tests Required:** Yes
**Status:** RED (10 tests failing — ready for Dev)

**Test Files:**
- `tests/persistence/test_pg_projection_retention.py` (5 tests) — projection_cache bounded-growth window + OTEL span + production-save wiring.
- `tests/persistence/test_pg_telemetry_retention.py` (5 tests) — turn_telemetry keep-last-N-rounds + NULL-round retention + OTEL span + production-save wiring.

Both use the project's canonical real-Postgres harness (`migrated_db` → `db_pool` → `PgEventStore` / `PgSaveRepository.for_slug`), mirroring `tests/persistence/test_pg_events.py`. RED verified serially (`-n0`, to dodge the known OTEL span-count parallel deadlock): **10 failed, 0 passed, 0 skipped, 0 collection errors**; every failure is missing *production* behavior (the two prune methods, the two span constants, the two keep-last constants), and the DB was reached (seeding ran) — not a scaffold or skip failure.

**Contract handed to Dev (Hephaestus):**
1. `PgEventStore.prune_projection_cache(*, keep_last_per_player: int) -> int` — keep newest N event_seqs per (session, player); return deleted count; emit `SPAN_PROJECTION_CACHE_PRUNE` ("projection.cache.prune") with `rows_pruned` + `session_id`. Safe because `lazy_fill` rebuilds pruned rows on reconnect.
2. `PgEventStore.prune_turn_telemetry(*, keep_last_rounds: int) -> int` — keep newest N distinct rounds; **retain NULL-round rows** (No Silent Fallbacks); return deleted count; emit `SPAN_TURN_TELEMETRY_PRUNE` ("turn_telemetry.prune") with `rows_pruned` + `session_id`.
3. Module constants `PROJECTION_CACHE_KEEP_LAST_PER_PLAYER` and `TURN_TELEMETRY_KEEP_LAST_ROUNDS` in `sidequest/game/pg/events.py` (Dev owns the values — pick a generous forensic tail for telemetry; see Delivery Finding re: index support + ADR-124).
4. **Wiring:** `PgSaveRepository.save()` must apply both bounds so the table is bounded in production (the two `test_save_*_in_production_path` tests drive the real `save()`).
5. New span constants registered in `sidequest/telemetry/spans/` with a `SpanRoute` (mirror `projection_cache_fill_span`) so they route to the watcher/forensics, and re-exported from `sidequest.telemetry.spans`.

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| OTEL Observability Principle (CLAUDE.md) | `test_prune_emits_otel_span_with_count_and_scope`, `test_prune_turn_telemetry_emits_otel_span` | failing |
| No Silent Fallbacks (SOUL/CLAUDE.md) | `test_prune_turn_telemetry_retains_null_round_rows` — un-attributable rows not silently dropped | failing |
| Every Test Suite Needs a Wiring Test / No half-wired | `test_save_enforces_projection_cache_bound_in_production_path`, `test_save_applies_turn_telemetry_retention_in_production_path` (drive real `save()`) | failing |
| python #3 type annotations at boundaries | new methods' signature pinned by kwargs + `int` return asserted across the prune tests | failing (methods absent) |
| python #6 test quality (no vacuous asserts) | self-check: all 10 tests assert exact counts / seq-sets / span attrs; idempotence tests assert `== 0` + rows intact (not truthy) | pass (own tests) |
| python #11 SQL parameterized (CWE-89) | not unit-assertable — flagged for Dev self-review + Reviewer (Delivery Finding) | deferred to review |

**Rules checked:** applicable subset (most lang-review rules — mutable defaults, async, deserialization, path handling, deps — N/A to pure-SQL retention methods).
**Self-check:** 0 vacuous tests found; no `assert True`, no truthy-only `assert result`, no skips, no `let _ =`-equivalents.

**Handoff:** To Dev (Hephaestus the Smith) for GREEN — implement the two prune methods + constants + spans and wire them into `PgSaveRepository.save()`. Heads-up (from SM Assessment): pre-existing ~13 server failures vs content `develop` (WWN) + ~18 OTEL span-count tests that deadlock under full parallel run — run affected files serially with `-n0`; classify as pre-existing.

---
## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/game/pg/events.py` — `PROJECTION_CACHE_KEEP_LAST_PER_PLAYER=200` + `TURN_TELEMETRY_KEEP_LAST_ROUNDS=100` constants; `_PRUNE_PROJECTION` / `_PRUNE_TELEMETRY` parameterized SQL; `PgEventStore.prune_projection_cache` (per-(session,player) keep-last-N window via `ROW_NUMBER`) and `PgEventStore.prune_turn_telemetry` (keep-last-N-distinct-rounds, `round IS NOT NULL` guard keeps out-of-frame rows).
- `sidequest/telemetry/spans/projection.py` — `SPAN_PROJECTION_CACHE_PRUNE` + `SpanRoute` + `projection_cache_prune_span` cm.
- `sidequest/telemetry/spans/persistence.py` — `SPAN_TURN_TELEMETRY_PRUNE` + `SpanRoute` + `turn_telemetry_prune_span` cm.
- `sidequest/game/pg/save_repository.py` — `save()` now applies both bounds on the production persistence path (per-turn + on disconnect).

**Approach:** projection_cache gets a per-player sliding window (safe — `cache_fill.lazy_fill` rebuilds pruned rows from the event log on reconnect; live resume only reads the head). turn_telemetry gets round-retention (forensic data, not a rebuildable cache; NULL-round infra rows retained per No Silent Fallbacks). Both prunes ride a locked `session_tx` and emit an OTEL span with `rows_pruned` + `session_id` (GM-panel observable, routed via `SPAN_ROUTES`). Both queries are served by existing indexes (`idx_projection_cache_player`, `idx_turn_telemetry_round`) — no migration.

**Tests:** 10/10 new tests passing (GREEN). Regression-checked: 30 existing persistence/telemetry tests + 77 tests across six real-`save()` span-capture handler suites — all pass, no span-count regression. Verified serially (`-n0`). Lint clean (`ruff check`); the only `pyright` findings (events.py:94/159) are pre-existing `.fetchone()[0]` Optional-subscripts in untouched code.

**Branch:** `feat/126-22-projection-cache-retention` (pushed to origin).

**Handoff:** To Reviewer (Hermes Psychopompos) for code review.

---
## Round 1 Specialist Dispatch (superseded)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (32 tests green, lint clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 5 | confirmed 4 (1 HIGH, 2 MED, 1 LOW), 1 verified-safe |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | clean | 0 (parameterization + scoping + no-leak confirmed) | N/A |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 4 confirmed (1 HIGH blocking, 2 Medium, 1 Low), 1 verified-safe, 0 dismissed

### Rule Compliance

- **python #11 — SQL parameterized (CWE-89):** 2 instances (`events.py:181` `_PRUNE_PROJECTION`, `events.py:196` `_PRUNE_TELEMETRY`). Both pass `(self._sid, self._sid, keep)` tuples against `%s`-only templates — no f-string/format/concat. **COMPLIANT** (both).
- **No Silent Fallbacks (SOUL/CLAUDE.md):** the retention DELETEs — `_PRUNE_TELEMETRY` has the `round IS NOT NULL` guard in BOTH outer + inner clauses (NULL-round forensic rows structurally retained); both prunes emit `rows_pruned` spans. The retention itself is **COMPLIANT**. BUT the HIGH finding is a related concern from the opposite angle: the prune wiring in `save()` lets a cleanup failure masquerade as a save failure — the fix MUST log loudly (mirror the lore-isolation pattern), not swallow silently, to stay compliant.
- **No half-wired features / wiring test:** `save()` calls both prunes; two real-Postgres wiring tests drive `save()` and assert bounds + spans. **COMPLIANT.**
- **python #6 — test quality:** (test_analyzer disabled — checked myself) the 10 new tests assert exact counts/seq-sets/span attrs; idempotence tests assert `== 0` + rows intact; NULL-round test asserts retention; no vacuous assertions. **COMPLIANT.**
- **python #3 — type annotations at boundaries:** new methods are `(*, keep_*: int) -> int`; constants are ints; spans typed `Iterator[trace.Span]`. **COMPLIANT.**
- **python #1 — silent exception swallowing:** no bare excepts in the diff. (The HIGH finding asks to ADD a try/except — it must be a loud log-and-continue, not a silent swallow.) **COMPLIANT (current diff).**

### Devil's Advocate

Assume this code is broken. The most damning path: this is a *performance* story whose fix makes the **save hot path more fragile**. Every player turn now fires two extra `DELETE`s, each opening its own `session_tx` row-lock, *after* the snapshot is already committed. Picture Keith's group mid-session, the Postgres pool briefly saturated (a render burst, a slow query). The snapshot commits fine, but `prune_projection_cache` times out acquiring the sessions-row lock. `save()` raises. The per-turn handler at `websocket_session_handler.py:1580` is mid-`try`: the player's `NarrativeEntry` write (same try, after `room.save()`) never happens, so that turn's player line silently vanishes from `narrative_log` — exactly the "every entry was author='narrator'" defect #177 the narrative-log write exists to fix, re-introduced via a cleanup fault. On disconnect, the same exception sets `last_save_failure`, and `ws_endpoint` skips `close_store()` — the slug never resets its rolling SDK baseline (Story 61-4), so a later runaway alarm could stay silenced. None of this loses the snapshot, but a *retention sweep* — the lowest-value operation in the method — can now degrade narration persistence and teardown. A confused operator sees "disconnect_save_failed" in the log and hunts a phantom save bug that is really a prune hiccup. The codebase already solved this exact problem for lore persistence (isolated try/except, loud log, watcher event, explicit comment that it "must NOT set last_save_failure"); this change ignored that precedent. Second angle — a misconfiguration footgun: `keep_last_per_player=0` is `rn > 0`, which is *every* row, so a single wrong constant silently wipes every session's cache (mass lazy_fill storms on reconnect), while `keep_last_rounds=0` does the *opposite* (keeps everything) — two sibling methods, inverted catastrophe modes, neither guarded. The window is narrow and the production constants are safe today, but "safe today because of a magic constant elsewhere" is precisely the fragility review exists to flag. Verdict: the retention logic is correct and well-tested; the *integration* into the durable-save path is not defensive enough to ship.

---
## Round 1 Reviewer Verdict (REJECTED — superseded by Round 2 below)

**Verdict:** REJECTED

The retention logic itself is correct, safe, and well-tested (security clean, parameterization confirmed, NULL-round forensic rows structurally retained, lazy_fill recovery verified, 32 tests green). It is **rejected on one HIGH integration defect**: the prune is wired into the durable-save path without isolation, so a best-effort cleanup fault corrupts the save-failure signal and per-turn narrative logging.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] [EDGE] | A prune fault inside `save()` propagates as a snapshot-save failure: contaminates `last_save_failure` (gates `close_store` on disconnect) and skips the post-`save()` per-turn `NarrativeEntry` write (re-opening defect #177). The snapshot is already durably committed — a cleanup-DELETE fault must not fail the save. Violates the established lore-persist isolation pattern in the same flow. | `sidequest/game/pg/save_repository.py:158-161` (prune calls); consequence at `websocket_session_handler.py:1580-1587` & `:586-591`; precedent at `:594-606` | Isolate the two prune calls in their own `try/except` that **logs loudly + continues** (mirror the lore-persist isolation), so `save()` propagates ONLY genuine snapshot-save failures. |
| [MEDIUM] [EDGE] | Unguarded inverted zero-semantics: `prune_projection_cache(keep_last_per_player=0)` deletes ALL rows (`rn > 0`); `prune_turn_telemetry(keep_last_rounds=0)` deletes NONE. | `sidequest/game/pg/events.py` (both prune methods) | Add `>= 1` preconditions (raise loudly on 0/negative). |
| [LOW] [EDGE] | `rows_pruned` span attribute unset if `session_tx` raises (set after the tx block) — GM panel can't tell "pruned 0" from "prune errored". | `sidequest/game/pg/events.py:183, :198` | Init `pruned = 0`; emit `rows_pruned` even on the failure path (folds into the HIGH fix). |

**Verified-good (no action):**
- [VERIFIED] [SEC] SQL fully parameterized (CWE-89) — `events.py:181,196` pass int tuples to `%s`-only templates; no interpolation. Complies with python lang-review #11.
- [VERIFIED] [SEC] Cross-session safety — both `_PRUNE_PROJECTION` and `_PRUNE_TELEMETRY` scope `WHERE session_id = %s` in BOTH the outer DELETE and the inner subquery; the missing inner scope would be a cross-session corruption hazard — it is present.
- [VERIFIED] [SEC] No info leakage — span attributes are `session_id` + `rows_pruned` only; no `payload_json`/PII.
- [VERIFIED] [EDGE] NULL-round retention is structural (`round IS NOT NULL` in outer + inner); empty-table `MIN(NULL)` is a safe no-op; `cur.rowcount` is reliable for DELETE in psycopg3.
- [VERIFIED] lazy_fill rebuilds pruned projection rows on reconnect; live delivery uses the WS fan-out, not `projection_cache` — pruning is recoverable, AC-1 safe.

**Data flow traced:** player turn → `save()` (snapshot commit OK) → `prune_*` (best-effort DELETE) → on fault, exception escapes `save()` → per-turn `try` skips `NarrativeEntry` write / disconnect sets `last_save_failure` → `close_store` skipped. The unsafe link is `save()` not isolating the prune.

**Subagent dispatch tags:** [EDGE] 4 confirmed (1 HIGH/2 MED/1 LOW). [SEC] clean (parameterization, scoping, no-leak). [SILENT] subagent disabled — assessed in Rule Compliance (No Silent Fallbacks): retention compliant; the fix must log loudly. [TEST] subagent disabled — assessed myself: 10 tests non-vacuous, exact-value assertions. [DOC] subagent disabled — comments accurate (the prune docstrings correctly describe the SQL). [TYPE] subagent disabled — signatures correctly typed (`-> int`). [SIMPLE] subagent disabled — no over-engineering; the SQL is minimal. [RULE] subagent disabled — backstopped by the Rule Compliance section above.

**Handoff:** Back to Dev for fixes (testable robustness defect → RED test first via TEA: a prune that raises must NOT fail `save()`, and the snapshot must remain saved).

---
## Dev Assessment — Rework Round 2

**Implementation Complete:** Yes — all three Reviewer findings addressed.

**Received the review (verified, not rubber-stamped):** the HIGH finding is sound — I confirmed the lore-persist isolation precedent at `websocket_session_handler.py:594-606` and that the per-turn `try` (`:1580`) wraps the post-`save()` `NarrativeEntry` write. My round-1 unguarded wiring genuinely violated that pattern. Implemented the fix.

**Fixes:**
- **[HIGH] resolved** — `PgSaveRepository.save()` now wraps the two prune calls in a `try/except Exception` that `logger.exception(...)`-logs and continues (loud, not silent — satisfies No Silent Fallbacks; mirrors the lore-persist isolation). The snapshot `save_snapshot()` stays *outside* the guard, so genuine snapshot-save failures still propagate and still set `last_save_failure`. Added a module `logger`. `save_repository.py`.
- **[MEDIUM] resolved** — `prune_projection_cache` and `prune_turn_telemetry` now `raise ValueError` on `keep < 1` (before opening the span), killing the inverted zero-semantics footgun. `events.py`.
- **[LOW] resolved** — both prune methods init `pruned = 0` and set `rows_pruned` in a `finally`, so the span carries the count even when `session_tx` raises. `events.py`.

**New tests (3):** `test_save_isolates_prune_failure_from_the_durable_snapshot` (monkeypatched raising prune → `save()` does not propagate, snapshot still loads), `test_prune_projection_cache_rejects_zero_keep`, `test_prune_turn_telemetry_rejects_zero_keep`.

**Tests:** 35/35 persistence tests green (13 retention + 22 existing). Lint clean; format applied.

**Branch:** `feat/126-22-projection-cache-retention` (pushed — commit `11f71911`).

**Handoff:** Back to Reviewer (Hermes Psychopompos) for re-review.

---
## Subagent Results

(Round 2 — re-review of the rework delta `11f71911`. Same 3 enabled specialists re-run.)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (35 tests green, lint clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 2 (both LOW, informational) | confirmed-as-noted 2 (pre-existing structural, no change required) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | clean | 0 (loud-not-silent confirmed, no new SQL) | N/A |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 0 blocking; 2 LOW informational (pre-existing structural, no change required); 0 dismissed

### Rule Compliance (Round 2)

- **No Silent Fallbacks (SOUL/CLAUDE.md):** the new `except Exception` in `save()` calls `logger.exception("save_db_retention_prune_failed session_id=%s", ...)` — ERROR-level + full traceback. **Loud, not silent. COMPLIANT.** Security specialist confirmed; it is `except Exception` (not bare), so `KeyboardInterrupt`/`SystemExit` still propagate.
- **python #11 SQL parameterized (CWE-89):** rework added NO new SQL/f-string/interpolation. **COMPLIANT.**
- **python #1 silent-exception-swallowing:** the one new broad except is loud-logged with a `# noqa: BLE001` rationale matching the established lore-persist pattern; the `try/finally` blocks in `events.py` suppress nothing. **COMPLIANT.**
- **Fail-loud-on-misconfig:** `keep < 1` now raises `ValueError` (before any I/O). **COMPLIANT.**

### Devil's Advocate (Round 2)

Assume the rework is broken. The new `try/except Exception` is broad — could it mask a real bug? I traced it: the try contains ONLY the two prune calls (`save_repository.py:169-174`); `save_snapshot()` is on line 157, outside it, so a genuine lost-snapshot still raises and still sets `last_save_failure` — the fix does not over-catch. Could the `except` hide a programming error (e.g., a typo'd attribute on the events store)? In principle yes — an `AttributeError` from a bad call would be logged and swallowed like a DB fault. But the prune calls are exercised by the wiring tests on every run, so a structural break surfaces in CI, not silently in prod; and the alternative (let it propagate) is exactly the HIGH defect we just fixed. Net: acceptable, and it logs loudly so the error is never invisible. Second angle: the `keep < 1` guard raises `ValueError`, which inside `save()` is caught by the same broad except — so a misconfiguration would be logged-and-swallowed rather than crashing. Is that a silent-failure regression? No: it logs at ERROR with a traceback, AND the production constants (200/100) are module literals that can only change via a reviewed code edit — there is no config-injection path. The guard's real value is protecting *direct* callers of `prune_*` (a future maintenance script), where the ValueError propagates normally. Third angle: does the `try/finally` double-handle? Traced — on a tx fault, `pruned` stays 0, `finally` sets `rows_pruned=0`, the exception propagates once into `save()`'s except, logged once. No double-handling. The span carries ERROR status because `Span.open` → `start_as_current_span` defaults to `set_status_on_exception=True` (verified `span.py:34`), so the GM panel genuinely distinguishes "pruned 0" from "prune errored" — the in-code comment is accurate, not aspirational. I cannot find a way to make this rework lose data or hide a fault invisibly. The fix is sound.

---
## Reviewer Assessment

**Verdict:** APPROVED

The Round-1 HIGH is fixed and **verified with evidence**, not just claimed: `save_snapshot()` is provably outside the new `try/except` (`save_repository.py:157`), the two prune calls are the sole contents of the guard (`:169-174`), and the except logs loudly via `logger.exception`. Genuine snapshot-save failures still propagate and still set `last_save_failure`. The two non-blocking items are resolved (`keep < 1` guards; `rows_pruned` emitted via `try/finally`). Re-review specialists: preflight GREEN (35 tests, lint clean), security clean (loud-not-silent, no new SQL), edge-hunter confirms the fix correct + 2 LOW pre-existing-structural notes requiring no change.

**Data flow traced:** player turn → `save()` → `save_snapshot()` (durable, *outside* guard — real failures still raise) → `try{ prune_projection_cache; prune_turn_telemetry }except{ logger.exception, continue }`. A cleanup-DELETE fault is now logged and swallowed; the durable write and its failure signal are uncontaminated. Safe.

**Pattern observed:** best-effort-cleanup isolation mirroring the lore-persist pattern at `websocket_session_handler.py:594-606` — `save_repository.py:163-176`.

**Error handling:** `except Exception` (not bare; `KeyboardInterrupt`/`SystemExit` propagate) + `logger.exception` (ERROR + traceback) — `save_repository.py:175-176`. `keep < 1` → `ValueError` fail-loud — `events.py:179, :211`. `rows_pruned` emitted on the failure path via `finally` — `events.py`.

**Non-blocking observations (LOW — not gating; optional tech-debt):**
- [LOW] [EDGE] A `keep < 1` `ValueError` raised inside `save()` would be caught by the broad except (unreachable today — constants are literals). Optional hardening: a module-level `assert PROJECTION_CACHE_KEEP_LAST_PER_PLAYER >= 1` to fail at import. Not required.
- [LOW] [EDGE] If a span context-manager `__enter__` itself raises (wedged tracer), `rows_pruned` is not set (missing span, not a crash). Pre-existing structural exposure, not a regression.

**Subagent dispatch tags:** [EDGE] 2 LOW informational confirmed-as-noted (no change required). [SEC] clean — loud-not-silent except, no new injection surface. [SILENT] subagent disabled — assessed in Rule Compliance: the new except is loud (`logger.exception`), not a silent fallback. [TEST] subagent disabled — assessed myself: 3 new tests are non-vacuous (isolation test monkeypatches a raising prune and asserts both no-propagation AND snapshot-loadable; guard tests use `pytest.raises(match=...)`). [DOC] subagent disabled — the new comments are accurate (the "pruned 0 vs errored" span-status claim verified against `span.py:34`). [TYPE] subagent disabled — signatures unchanged (`-> int`); guards raise typed `ValueError`. [SIMPLE] subagent disabled — the rework is minimal (a try/except, two guards, a finally); no over-engineering. [RULE] subagent disabled — backstopped by Rule Compliance (Round 2) above.

**Handoff:** To SM (Themis the Just) for finish-story.