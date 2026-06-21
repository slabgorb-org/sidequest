---
story_id: "153-22"
jira_key: ""
epic: "153"
workflow: "tdd"
---
# Story 153-22: [DUNGEON-MOVEMENT-RESOLVER-MISSES-EDGES] resolve natural-language exits (deeper, leftmost west passage) to room-graph node edges and dedupe identical-neighbor exit lists

## Story Details
- **ID:** 153-22
- **Jira Key:** (not configured for this project)
- **Workflow:** tdd
- **Stack Parent:** none
- **Repo:** sidequest-server
- **Type:** bug
- **Points:** 5
- **Priority:** p1

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-21T16:05:19Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-21T15:10:33Z | 2026-06-21T15:13:21Z | 2m 48s |
| red | 2026-06-21T15:13:21Z | 2026-06-21T15:26:35Z | 13m 14s |
| green | 2026-06-21T15:26:35Z | 2026-06-21T15:38:05Z | 11m 30s |
| review | 2026-06-21T15:38:05Z | 2026-06-21T15:49:48Z | 11m 43s |
| green | 2026-06-21T15:49:48Z | 2026-06-21T15:57:03Z | 7m 15s |
| review | 2026-06-21T15:57:03Z | 2026-06-21T16:05:19Z | 8m 16s |
| finish | 2026-06-21T16:05:19Z | - | - |

## Sm Assessment

**Decision: READY for Red phase. Route to tea (Amos).**

- **Scope is a contained bug fix, correctly sized at 5pts/tdd.** The defect is the dungeon movement resolver failing to map natural-language exits ("deeper", "leftmost west passage") to room-graph node edges, plus an identical-neighbor exit list that produces false ambiguity. This is a server-only change with a clear blast radius (`agents/subsystems/movement.py`, `dungeon/region_projection.py`) — no cross-repo coordination needed.
- **ACs derived from the title + setup technical analysis, not invented.** The story YAML carried no description/AC, so the seven ACs above were reconstructed from the title's two named failures (NL-exit resolution; identical-neighbor dedupe) and the code-area investigation. AC-1 (dedupe/label-distinct parallel edges) is the root cause; AC-2/AC-3 are the descriptor-bridge behaviors; AC-4 is the regression guard; AC-5 keeps genuine ambiguity loud; AC-6/AC-7 are the OTEL + wiring obligations this project requires.
- **OTEL + wiring are non-negotiable and already specced.** AC-6 demands `movement.resolved`/`movement.unresolved` spans so the GM panel can verify the resolver engaged rather than the narrator improvising the crawl. AC-7 forces the wiring test to drive `run_movement_dispatch`, not `_resolve` in isolation. tea must hold the line on both.
- **Doctrine watch for Dev:** resolve *false* ambiguity (identical-neighbor lists) only — do **not** paper over *genuine* ambiguity (AC-5). The descriptor bridge is a layer onto existing `requested_bearing` + `_KIND_SYNONYMS` matching, **not** a new resolver subsystem (AC-3). No silent fallbacks — an unresolved move must fail loud with a precise reason.
- **Jira:** explicitly skipped — Jira is not configured for this project (`jira.project`/`jira.url` unset). No claim required.
- **Gate state:** session ✓, context (13KB, validated) ✓, branch `feat/153-22-dungeon-movement-resolver-edges` off `develop` ✓, merge gate clear (no open PRs) ✓.

## TEA Assessment

### Red Phase (test writing)

**Tests Required:** Yes
**Reason:** p1 behavioral bug — the dungeon movement resolver mis-handles parallel edges and ordinal descriptors. RED tests pin the post-fix contract.

**Test Files:**
- `tests/agents/subsystems/test_movement_dispatch.py` — appended 6 dispatch/bank tests (drive `run_movement_dispatch` / `run_dispatch_bank`, never `_resolve` in isolation — AC-7).
- `tests/dungeon/test_region_bearings.py` — appended 1 projection-level test for parallel-edge distinguishability (AC-1).

**Tests Written:** 7 tests covering all 7 ACs.
**Status:** RED — verified by testing-runner (run id `153-22-tea-red`). 6 fail on assertions (the right reason — behavior is wrong, no import/collection errors); 1 is an intentional GUARD that correctly passes today.

| Test | AC(s) | RED today | Why it fails (pre-fix) |
|------|-------|-----------|------------------------|
| `test_parallel_edges_same_node_false_ambiguity_resolves_153_22` | 1, 2, 6 | FAIL (assert) | "the stairs" over 3 parallel stairs→`b` returns `ambiguous_descriptor` (false ambiguity); PC stranded at `a`. |
| `test_descriptor_consistency_single_vs_parallel_corridor_153_22` | 4 | FAIL (assert) | "the corridor" resolves with ONE edge but goes ambiguous with 3 parallel edges to the same `b`. |
| `test_ordinal_descriptors_select_distinct_single_edges_153_22` | 3 | FAIL (assert) | "first"/"second passage" tie on the `passage` token → `ambiguous_descriptor`; no ordinal bridge. |
| `test_ordinal_leftmost_resolves_single_edge_153_22` | 3, 6 | FAIL (assert) | "leftmost passage" has no positional bridge → refuses. |
| `test_genuine_ambiguity_distinct_neighbors_still_refuses_153_22` | 5 | PASS (guard) | Two parallels→`b` + one→`c` is a real fork → must stay `ambiguous_descriptor`. Guards against over-collapse. |
| `test_parallel_edge_resolution_wires_through_bank_153_22` | 7 | FAIL (assert) | Through the real `run_dispatch_bank`, the parallel-edge move never advances the PC. |
| `test_parallel_edges_to_one_neighbor_are_distinguishable_153_22` | 1 | FAIL (assert) | `project_region` emits 3 identical `('b','southeast')` exits — `assign_bearings` collapses parallel edges on `to_region_id`. |

### Rule Coverage

Applicable Python lang-review rules for a resolver/projection bugfix:

| Rule | Test(s) | Status |
|------|---------|--------|
| #1 Silent exceptions / No Silent Fallbacks | `test_genuine_ambiguity_distinct_neighbors_still_refuses_153_22` (genuine fork must fail loud, never silently pick) | passing (guard) |
| #4 Logging / OTEL observability on every decision | `test_parallel_edges_same_node_false_ambiguity_resolves_153_22` (asserts `movement.resolved` carries `resolved_via`/`edge_kind`/`candidate_exits`); `test_parallel_edge_resolution_wires_through_bank_153_22` (span fired through the bank); guard asserts `movement.unresolved reason=ambiguous_descriptor` | failing + guard |
| #6 Test quality (meaningful assertions) | self-check across all 7 tests | passing |

**Rules checked:** 3 of 13 lang-review rules are directly exercisable by this story's behavioral surface (#1 fail-loud, #4 OTEL, #6 test quality). The remainder apply to the **production edit Dev will write** and are NOT yet covered by tests — Dev must self-check on the GREEN diff, especially: **#9 async pitfalls** (`run_movement_dispatch`/`_resolve` are on the async path — no blocking calls, no missing `await`), **#2 mutable defaults** (any new ordinal/bearing lookup tables must be module-level constants, not mutable params), **#3 type annotations** at the new helper boundaries, and **#13 fix-introduced regressions**.
**Self-check:** 0 vacuous tests found (every assertion checks a specific value; no `assert True`, no bare-truthy `assert result`).

**Handoff:** To Dev (Naomi) for implementation. Land AC-1 in `region_projection.py` (distinct-label or projection-side dedup — see TEA Deviation #1 + the ADR-106 Question in Delivery Findings); land AC-2/AC-3/AC-5 in `movement.py::_resolve` (collapse a descriptor tie by `to_region_id` so a same-node tie resolves while a distinct-node tie still refuses; add the ordinal/positional bridge). Keep emitting the `movement.resolved`/`movement.unresolved` spans (AC-6). One pre-existing unrelated red persists in the dispatch test file (see Delivery Findings — not yours to fix under 153-22).

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/dungeon/region_projection.py` — `project_region` collapses parallel edges to the same neighbor into one exit (prefer visible; stable kind/bearing order; `debug`-logged collapse). Added module `logger`. Fixes AC-1, AC-2, AC-4, AC-5 (one exit per neighbor ⇒ no false tie reaches `_resolve`; genuine distinct-node ties still refuse).
- `sidequest/agents/subsystems/movement.py` — added the ordinal/positional descriptor bridge: `_ORDINAL_INDEX` / `_MIDDLE_WORDS` / `_BEARING_LR_RANK` constants + `_resolve_ordinal()` helper, wired into `_resolve` BEFORE token-overlap. "first/second/leftmost/middle/last" map to a position in the kind-filtered, left-to-right-ordered exit list; secret exits never offered by position; out-of-range position fails loud (no silent reinterpret). Fixes AC-3. `resolved_via="ordinal"` keeps the OTEL lie-detector honest (AC-6).
- `tests/agents/subsystems/test_movement_dispatch.py` — out-of-scope baseline restore: `acting_player=None` added to a stale `_build_state_summary` monkeypatch stub (see Dev Deviation #2). The 7 RED tests TEA wrote are unchanged.

**Approach:** chose projection-side dedup over distinct-label/resolver-collapse (Dev Deviation #1, answering TEA's open ADR-106 Question). `assign_bearings` was NOT changed — it already collapses to one bearing per neighbor, so deduping the exit list keeps the narrator prose and the DUNGEON_MAP frame (`map_emit.py`) consistent.

**Tests:** 7/7 new 153-22 tests GREEN. Full regression `tests/agents/subsystems/ tests/dungeon/` = **683 passed / 0 failed / 0 errors** (run id `153-22-dev-green`). The pre-existing red is now fixed. Lint (ruff), format (ruff format), and types (pyright) all clean on the changed source.

**Self-review:** wired end-to-end through `run_movement_dispatch` + `run_dispatch_bank` (AC-7); follows existing patterns (module constants, no mutable defaults — lang-review #2; full type annotations — #3; no blocking calls added on the async path — #9); fail-loud preserved (no silent fallbacks — #1); OTEL spans intact (#4).

**Handoff:** To Reviewer (Chrisjen) — TDD has no verify phase configured for this story, routing per workflow.

### Green Rework (round-trip 1 — addressing Reviewer findings)

All Reviewer rework items resolved. **Production logic unchanged** (the fix was already correct); this round hardens tests + observability.

- **[TEST] coverage gaps closed** (`tests/agents/subsystems/test_movement_dispatch.py`): added `test_ordinal_middle_resolves_single_edge_153_22` (the named AC-3 `_MIDDLE_WORDS` path), `test_ordinal_last_resolves_single_edge_153_22` (negative-index path), `test_ordinal_out_of_range_refuses_loud_153_22` (the documented fail-loud invariant: "fifth passage"/3 → `no_candidate_edges`, no move). Added `test_dedup_prefers_visible_over_secret_parallel_153_22` (`tests/dungeon/test_region_bearings.py`).
- **[TEST][RULE#6] OTEL assertions pinned** (AC-6): `resolved_via == "descriptor_match"` (deduped false-ambiguity + bank tests), `== "ordinal"` (leftmost + the main AC-3 test, which now asserts both resolved spans). Renamed the confusingly-shadowed local `_resolve_ordinal` helper → `_run_ordinal`.
- **[RULE#4][DOC] dedup observability** (`region_projection.py`): `logger.debug` → `logger.info` so a materializer duplicate is actually visible in prod (the comment promised it); dedup sort key now prefers `shortcut` edges so the distance-collapse flag survives the merge.
- **[DOC] comment fix** (`movement.py`): `_BEARING_LR_RANK` comment now states north/south + verticals + bearing-less all sit at rank 2.
- **[EDGE] determinism** (`movement.py`): ordinal word pick now scans tokens in TEXT order (not set-iteration) so a multi-ordinal phrase ("second-to-last") resolves deterministically across restarts.
- **DISMISSED items NOT actioned** (per Reviewer): the rule-checker's `_cartography_for`/`_is_region_mode` annotation flags — pre-existing, not in diff, private-helper-exempt.

**Tests:** 687 passed / 0 failed across `tests/agents/subsystems/ tests/dungeon/` (run id `153-22-dev-green-rework`; confirmed by direct run + testing-runner). Lint (ruff), format, and pyright clean on all changed files. Commit `59fd25c3`, pushed.

**No new design deviations** — the rework implemented the Reviewer's findings; it did not diverge from spec.

**Handoff:** Back to Reviewer (Chrisjen) for re-review (round-trip 1).

## Subagent Results (Round 0 — REJECTED, superseded by re-review)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 smells; 683 passed/0 failed; ruff+format+pyright clean | N/A (mechanical baseline confirmed) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — assessed by Reviewer (see [EDGE]) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — assessed by Reviewer (see [SILENT]) |
| 4 | reviewer-test-analyzer | Yes | findings | 9 | confirmed 6, downgraded/merged 3 |
| 5 | reviewer-comment-analyzer | Yes | findings | 1 | confirmed 1 (DOC) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — assessed by Reviewer (see [TYPE]) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings — assessed by Reviewer (see [SEC]) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — assessed by Reviewer (see [SIMPLE]) |
| 9 | reviewer-rule-checker | Yes | findings | 5 | confirmed 3 (#4,#6×2), dismissed 2 (#3 pre-existing/private-exempt) |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 7 confirmed (1 TEST-cluster, 1 DOC, 1 RULE#4-log, + 4 Reviewer-found EDGE/SIMPLE), 2 dismissed (with rationale), 0 deferred

## Reviewer Assessment (Round 0 — REJECTED, superseded by re-review)

**Verdict:** REJECTED — test-hardening rework. The **production code is sound** (the playtest bug is genuinely fixed; 683/0 green; ruff/format/pyright clean; fail-loud and OTEL spans intact), but the test suite under-verifies the shipped behavior and one log line contradicts its own stated intent. These are testable findings → red rework to TEA.

**Data flow traced:** player text → `intent_router` → `run_dispatch_bank` → `run_movement_dispatch` → `project_region` (parallel-edge dedup) → `_resolve` → `_resolve_ordinal` → `WorldStatePatch(pc_region=…)` + `movement.resolved` span. The pipeline is wired end-to-end and reachable (AC-7 test drives the bank). Safe: descriptor is regex-tokenised (`[a-z]+`, ReDoS-safe), bounded to the candidate list, no SQL/path/deserialization surface.

| Severity | Tag | Issue | Location | Fix Required |
|----------|-----|-------|----------|--------------|
| [MEDIUM] | [TEST][RULE] | The `_MIDDLE_WORDS` path ("the middle one" — a **named AC-3 example**) ships with ZERO test coverage. AC-3 is not fully verified. | `tests/.../test_movement_dispatch.py` | Add `test_ordinal_middle_resolves_single_edge_153_22`: 3 exits, "the middle passage" → resolves to one exit, no error, `resolved_via == "ordinal"`. |
| [MEDIUM] | [TEST] | Out-of-range ordinal fail-loud invariant (docstring: "an out-of-range position is an honest no-match, never reinterpreted") is untested. | same | Add a test: 3 exits, "the fifth passage" → `error == "no_candidate_edges"`, PC does NOT move. |
| [MEDIUM] | [TEST][RULE] | The ordinal path's `resolved_via == "ordinal"` is never pinned (the main AC-3 test asserts no span; the leftmost test and the AC-7 bank test check only truthiness). AC-6 (OTEL lie-detector) is unverified for the ordinal bridge. Two specialists flagged this. | `test_movement_dispatch.py:316,427` + the truthy `resolved_via` asserts | Pin exact values: `== "ordinal"` (ordinal tests), `== "descriptor_match"` (false-ambiguity test); add a span assertion to `test_ordinal_descriptors_select_distinct_single_edges`. |
| [MEDIUM] | [TEST] | Dedup "prefer VISIBLE" invariant untested — a sort-order change could silently keep a secret edge. | same | Add a test: 1 visible + 2 secret parallel edges to one neighbor → projected exit is `hidden=False`. |
| [MEDIUM] | [RULE][DOC] | `logger.debug` for the dedup collapse contradicts its own comment ("Logged … so a true materializer duplicate stays visible for investigation — No Silent Fallbacks"). DEBUG is off in production, so the event is effectively invisible — undercutting the No-Silent-Fallbacks justification. | `region_projection.py:324` | Bump to INFO (rate is one-line-per-collapse, acceptable), OR record the collapse count on the `movement.resolved` span (preferred — OTEL is the project's observability), OR soften the comment to not overclaim. |
| [LOW] | [TEST] | "last"/"rightmost" (negative-index) and the bearing-informed LR ordering are never exercised (all test exits land at LR rank 2). | same | Add a "the last passage" test and a bearing-distinct ordering test if cheap. |
| [LOW] | [DOC] | `_BEARING_LR_RANK` comment says only "verticals and bearing-less exits sit in the middle" — north/south also occupy rank 2. Misleading-by-omission. | `movement.py` (constant comment) | Reword to include north/south at rank 2. |
| [LOW] | [EDGE] | Multi-ordinal-word descriptors ("the second-to-last passage" → both `second` and `last`) pick the word via `next()` over a **set** — hash-order-dependent, nondeterministic across restarts. Contradicts the "deterministic" comment. | `movement.py:_resolve_ordinal` | Pick by a defined precedence (e.g. smallest `abs(index)` or first-by-sorted-token), or document the limitation. |
| [LOW] | [SIMPLE] | Dedup sort key `(hidden, kind, bearing, to_region_id)` ignores `shortcut` — a parallel shortcut edge could be dropped in favor of a non-shortcut one, losing the distance-collapse flag from the projection. | `region_projection.py:320` | Include `shortcut` in the preference key, or note it's intentional. |

**[SEC]** No findings — verified: descriptor is internal game text, regex tokenizer is linear (no ReDoS), no SQL/HTML/path/deserialization surface introduced. `_resolve_ordinal` operates on a bounded in-memory candidate list.
**[TYPE]** rule-checker flagged `_cartography_for` (no return annotation) and `_is_region_mode(cart)` (no param annotation) — **DISMISSED**: both are pre-existing (NOT in this diff) AND private underscore-prefixed helpers, which rule #3 explicitly exempts ("Internal/private helpers are exempt"). pyright passes clean. The new `_resolve_ordinal` IS fully annotated.
**[SILENT]** Verified mostly clean: `(None, True)` from `_resolve_ordinal` routes to a loud `no_candidate_edges` unresolved span (not swallowed); `(None, False)` correctly falls through to token-overlap; no bare except / swallowed errors introduced. The ONE silent-ish concern is the DEBUG-level dedup log (see [RULE] row above).

### Rule Compliance (Python lang-review, exhaustive over the diff)

- **#1 Silent exceptions:** PASS — no try/except introduced in new code; typed `SeamCrossingError` handlers are pre-existing and unchanged.
- **#2 Mutable defaults:** PASS — `_ORDINAL_INDEX` (dict), `_MIDDLE_WORDS` (frozenset), `_BEARING_LR_RANK` (dict) are all module-level constants, not function defaults; `collapsed`/`ranked` are function locals.
- **#3 Type annotations:** PASS on the diff — `_resolve_ordinal` fully annotated; the two flagged helpers are pre-existing private (exempt). 
- **#4 Logging:** **VIOLATION** — dedup `logger.debug` level vs stated investigative intent (see severity table). Format string uses lazy `%s` (correct), no sensitive data (correct).
- **#5 Path handling:** N/A — no file I/O.
- **#6 Test quality:** **VIOLATION** — weak/absent OTEL span assertions and missing edge-case tests (see severity table). No `assert True`, no mock-on-wrong-target.
- **#7 Resource leaks:** N/A — no resources opened.
- **#8 Unsafe deserialization:** N/A.
- **#9 Async pitfalls:** PASS — `_resolve_ordinal`/`project_region` are sync pure functions; no blocking call added to the async `run_movement_dispatch`; no missing await.
- **#10 Import hygiene:** PASS — `import logging` added at correct module position; `logger` correctly NOT exported in `__all__`; no star/circular imports.
- **#11 Input validation:** PASS — regex tokenizer ReDoS-safe; internal boundary, not an HTTP edge.
- **#12 Dependency hygiene:** N/A — no dependency changes.
- **#13 Fix-introduced regressions:** PASS on logic; the #4 log-level and #6 test-quality items are the only fix-introduced quality issues.
- **SOUL/CLAUDE rules:** No Silent Fallbacks — dedup is logged (but see #4 level); No Source-Text Wiring Tests — PASS (tests drive `run_dispatch_bank`/`run_movement_dispatch`, OTEL spans, no source greps); OTEL Observability — spans fire but the ordinal path's `resolved_via` is under-asserted (#6); Don't Reinvent — PASS (extended `_resolve`/`project_region`, reused `_tokens`/`_KIND_SYNONYMS`/`RegionExit`, no parallel navigator).

### Devil's Advocate

Argue this is broken. **First, "the middle one" is a lie of omission.** Dev added `_MIDDLE_WORDS = {middle, middlemost, centre, center, central}` and a whole separate `is_middle` branch (`idx = len(lr) // 2`), and AC-3 literally names "the middle passage" as a target — yet not a single test types the word "middle." If the midpoint math were `len(lr) // 2 + 1` (off-by-one into an IndexError-adjacent slot) or if `is_middle` were shadowed by an ordinal word in a real phrase, no test would notice. A career GM typing "I take the middle passage" is the exact persona this story serves, and we shipped that path blind. **Second, the OTEL lie-detector is itself lying here.** This project's entire defense against Claude "winging it" is that every decision emits a span the GM panel can check — yet the ordinal bridge's resolved span value (`"ordinal"`) is asserted *nowhere*. The main AC-3 test pulls in `capture_spans` and then asserts nothing about spans; the AC-7 bank test only checks a span *exists*. So if a refactor made the ordinal path silently resolve via `descriptor_match` (or emit no `resolved_via` at all), the GM panel — and the tests — would shrug. For a story whose AC-6 is "the GM panel can see how it disambiguated," that is the one assertion that mattered, and it's the weakest one. **Third, the dedup hides what it claims to reveal.** The comment swears the collapse is "not silent … so a true materializer duplicate stays visible for investigation," but it logs at DEBUG, which is off in production — so a genuine materializer double-write (a data-integrity bug ADR-106 warns is possible) collapses silently in prod and nobody sees it. The comment is aspirational, the code is mute. **Fourth, a confused user breaks the determinism promise:** "the second-to-last door" feeds both `second` and `last` into a set, and `next()` picks whichever the hash seed surfaces — so the same words resolve to different rooms across server restarts, in a subsystem that explicitly promises "stable turn-to-turn." None of these crash or strand a player — the production behavior for the *reported* failure modes is correct — but four of the bridge's own branches (middle, last/rightmost, out-of-range, multi-word) ship without a test or a verified span, and that is exactly the "ship 3 of 5 connections and call it done" the project forbids. Sending it back for a one-cycle test-hardening pass is cheap insurance on a p1 the table will hammer.

**Handoff:** Back to TEA (Amos) for red rework — add the missing-path tests (middle, out-of-range, last, dedup-prefer-visible), pin the OTEL `resolved_via` assertions, and fold the source nits (log level, `_BEARING_LR_RANK` comment, multi-ordinal determinism) into the subsequent green.

## Subagent Results

(Re-review, round-trip 1 — verifying the rework against the prior REJECT findings.)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 smells; 687 passed/0 failed; ruff+format+pyright clean | N/A (mechanical baseline confirmed) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — assessed by Reviewer ([EDGE]) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — assessed by Reviewer ([SILENT]) |
| 4 | reviewer-test-analyzer | Yes | findings | 4 (all prior 6 RESOLVED) | confirmed 1 (LOW, corroborated), noted 3 LOW |
| 5 | reviewer-comment-analyzer | Yes | clean | 0 (all 3 prior comment fixes verified accurate) | N/A |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — assessed by Reviewer ([TYPE]) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings — assessed by Reviewer ([SEC]) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — assessed by Reviewer ([SIMPLE]) |
| 9 | reviewer-rule-checker | Yes | findings | 1 (prior #4 + #6 RESOLVED) | confirmed 1 (LOW, same as test-analyzer's) |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 1 confirmed (LOW, non-blocking — corroborated by 2 specialists), 3 noted (LOW), 0 blocking. All 7 round-0 findings verified RESOLVED.

## Reviewer Assessment

**Verdict:** APPROVED. The round-0 rework closed every substantive gap, verified by re-running all four enabled specialists: **687 passed / 0 failed**, ruff/format/pyright clean, and the prior REJECT findings (named-AC "middle" untested, OTEL `resolved_via` unpinned, dedup log at DEBUG, misleading comments, multi-ordinal nondeterminism) are all confirmed resolved. The residual findings are LOW-severity test polish on already-covered paths — none Critical/High, none leaving a shipping path unverified.

**Data flow re-traced:** player text → `run_dispatch_bank` → `run_movement_dispatch` → `project_region` (parallel-edge dedup, now INFO-logged + shortcut-preferring) → `_resolve` → `_resolve_ordinal` (text-order word pick) → `WorldStatePatch` + `movement.resolved` span (`resolved_via` now pinned per path). Wired and reachable; safe (ReDoS-free regex, bounded candidate list).

**Round-0 findings — resolution verified:**
- [TEST] "middle" (named AC-3 example) → RESOLVED: `test_ordinal_middle_resolves_single_edge_153_22` exercises the `is_middle`/`idx=len//2` branch, pins `resolved_via=="ordinal"`.
- [TEST] out-of-range fail-loud → RESOLVED: `test_ordinal_out_of_range_refuses_loud_153_22` asserts `error=="no_candidate_edges"`, no move, no resolved span.
- [TEST] "last"/negative-index → RESOLVED: `test_ordinal_last_resolves_single_edge_153_22`.
- [TEST][RULE] OTEL `resolved_via` unpinned → RESOLVED: 7/9 movement tests now pin the exact label; the main AC-3 test asserts both resolved spans.
- [TEST] dedup prefer-visible → RESOLVED: `test_dedup_prefers_visible_over_secret_parallel_153_22` asserts the kept exit is `hidden=False`.
- [RULE][DOC] dedup log level → RESOLVED: now `logger.info` with matching comment; fires only on parallel edges (not per-turn noise).
- [DOC] `_BEARING_LR_RANK` comment → RESOLVED: now lists north/south + verticals + bearing-less at rank 2 (comment-analyzer verified against the dict).
- [EDGE] multi-ordinal determinism → RESOLVED: word pick now scans tokens in text order (deterministic across restarts).

**Residual findings (LOW, non-blocking — recorded as Delivery Findings for optional follow-up):**

| Severity | Tag | Issue | Location | Why non-blocking |
|----------|-----|-------|----------|------------------|
| [LOW] | [TEST][RULE] | `test_descriptor_consistency_single_vs_parallel_corridor` takes `capture_spans` but asserts no span (AC-4 `resolved_via` unpinned). **Corroborated by test-analyzer + rule-checker (rule #6).** | `test_movement_dispatch.py:~1288` | CONFIRMED, not dismissed — but the exact dedup→`descriptor_match` path's `resolved_via` is already span-verified by `test_parallel_edges_same_node_false_ambiguity_resolves` AND `test_parallel_edge_resolution_wires_through_bank`. Redundant coverage, not a hole; the test's unique job (single==parallel destination) is fully asserted. |
| [LOW] | [TEST] | AC-1 projection test's 2nd assertion `len({bearing})==len(to_b)` is trivially `1==1` under dedup. | `test_region_bearings.py:~623` | The line ABOVE it (`len(set(keys))==len(keys)`) is the real, non-vacuous check that catches the bug. Redundant trailing line, not a vacuous test. |
| [LOW] | [TEST] | middle/last not asserted distinct-from-first (index-aliasing bug would pass each individually). | `test_movement_dispatch.py` | `first != second` IS asserted in `test_ordinal_descriptors_...`; the LR-index math (0/1/2/-1) is trivial; aliasing would also break the tested first!=second. |
| [LOW] | [TEST] | out-of-range test asserts the unresolved span exists but doesn't pin `reason`. | `test_movement_dispatch.py` | `data["error"]=="no_candidate_edges"` IS pinned, and `_unresolved` sets the span reason from the same param. |

**[SEC]** Clean — re-review confirmed `re.findall(r"[a-z]+", ...)` is ReDoS-immune (no alternation/backref/nested quantifier); the second tokenization is intentional (text-order, not redundant); `exit_descriptor` is str-coerced at the boundary.
**[SIMPLE]** Clean — the dual tokenization is not waste (set vs ordered list serve different needs); the dedup `shortcut` preference is a correct one-token addition.
**[TYPE]** Clean — `not e.shortcut` is well-typed (`RegionExit.shortcut: bool`); `_resolve_ordinal` fully annotated. The round-0 `_cartography_for`/`_is_region_mode` flags remain DISMISSED (pre-existing, private-helper-exempt).
**[SILENT]** Clean — fail-loud preserved: `(None, True)` → loud `no_candidate_edges`; `(None, False)` → token fall-through; the dedup is now INFO-visible (no silent fallback).

### Rule Compliance (re-review delta)

- **#4 Logging:** PASS now — `logger.debug`→`logger.info` resolves the round-0 violation; lazy `%s`, no sensitive data (`sorted(collapsed)` logs region-id slugs as a list repr — legible, benign).
- **#6 Test quality:** PASS with one LOW residual — 7/9 new tests pin `resolved_via`; the one unpinned consistency test is covered by siblings (above).
- **#11 Security/ReDoS:** PASS — simple character class, no backtracking risk.
- **#13 Fix-introduced regressions:** PASS — text-order word pick and shortcut sort-key change behavior only on multi-ordinal phrases / shortcut-bearing parallels respectively; 687 green confirms no regression on existing paths.
- All other rules: unchanged from round 0 (PASS / N/A).

### Devil's Advocate (re-review)

Argue the rework is still broken. The strongest remaining thread: the AC-4 consistency test pulls in `capture_spans` and then asserts nothing about spans — two specialists flagged it, so isn't approving it the same "the OTEL assertion that mattered is the weakest one" sin I rejected for in round 0? No — and the distinction is the point. In round 0 the ordinal path's `resolved_via=="ordinal"` was pinned *nowhere*; the GM-panel label for an entire resolver branch was unverified. Now it is pinned in seven tests, and the specific `descriptor_match` label the consistency test would assert is independently pinned in two sibling tests that drive the identical dedup→descriptor path. So the lie-detector IS armed for every path; the consistency test simply doesn't *also* re-assert it. A confused user still can't break a verified path. Second thread: could the text-order word pick mis-handle a real phrase? "the second-to-last passage" now deterministically picks "second" (idx 1) — still not the semantic "second from the end," but deterministic and a valid exit, and out of AC scope. Third: the INFO log could be noisy if a legit Jaquaysed region has permanent parallel edges — but that is exactly the materializer-audit signal the deferred Delivery Finding wants visible, and it is bounded to parallel-edge regions. None of these strand a player, corrupt state, or leave an AC unverified. The remaining items are assertions that *could* be marginally stronger, not behavior that *is* wrong — the correct disposition is APPROVE with the residuals recorded, not a third cycle over redundant coverage.

**Handoff:** To SM (Camina) for finish-story.

## Acceptance Criteria

From story title and technical analysis:

1. **Parallel edges are label-distinct (or deduped).** Standing in a region with three edges to the same neighbor (exp002.r1), the projected exits no longer present three indistinguishable exp002.r1 entries: either each parallel exit carries a distinct player-facing bearing/label (so assign_bearings no longer collapses them on to_region_id), or the graph/materializer guarantees a single edge per node pair. A career-GM-visible "name a bearing" prompt must list distinguishable ways.

2. **"deeper" resolves through parallel edges.** "move deeper into the next chamber" from exp002.r2 resolves to a single concrete neighbor and advances the PC (no ambiguous_descriptor, no no_candidate_edges), with the flavor descriptor "into the next chamber" not vetoing the coarse deeper direction (extend the existing descriptor-fallback so a tie among parallel edges to the same node resolves deterministically rather than refusing).

3. **Ordinal / positional descriptors bridge to edges.** "the leftmost of the three west passages" (and "the first/second/middle passage") resolves to a single edge when the exits are distinguishable, via an ordinal/positional descriptor bridge layered onto the existing requested_bearing + _KIND_SYNONYMS matching — not a new resolver subsystem.

4. **Consistency restored.** The same descriptor phrasing that resolved entrance→exp002.r2 one step earlier resolves at exp002.r2 too; the regression was the identical-neighbor edge list, and AC-1 removes it.

5. **Genuine ambiguity still fails loud.** When two genuinely distinct neighbors tie under a descriptor, the resolver still returns ambiguous_descriptor and asks "which way?" — the fix must not paper over real ambiguity, only resolve the false ambiguity created by identical-neighbor lists.

6. **OTEL / watcher spans.** A resolved move emits movement.resolved carrying resolved_via, edge_kind, and candidate_exits; a still-unresolved move emits movement.unresolved with the precise reason. The GM panel can see the resolver engaged and how it disambiguated, versus the narrator improvising the crawl.

7. **Wiring / integration test proves reachability.** Add behavior tests in tests/agents/subsystems/test_movement_dispatch.py that build a graph with three parallel edges to one neighbor, fire run_movement_dispatch for direction="deeper" and for an ordinal descriptor, and assert the PC's pc_regions patch advanced + the movement.resolved span fired. Drive the resolver through run_movement_dispatch, not _resolve in isolation.

## Delivery Findings

No upstream findings.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): a pre-existing, unrelated test fails on the baseline — `test_wiring_intent_router_pass_threads_context` in `tests/agents/subsystems/test_movement_dispatch.py`. It fails IN ISOLATION (confirmed not caused by the 153-22 appends; my diff is append-only, +315/-0). Root cause is a stale monkeypatch stub: production `sidequest/server/intent_router_pass.py:785` now calls `_build_state_summary(..., acting_player=player_name)`, but the test's stub lambda `lambda snapshot, *, pack, dungeon_store=None, palette=None: "summary"` does not accept `acting_player` → `TypeError: ... got an unexpected keyword argument 'acting_player'`. Affects `tests/agents/subsystems/test_movement_dispatch.py` (add `acting_player=None` to the stub lambda's keyword-only params). Out of 153-22 scope (different subsystem — intent-router threading, not the movement resolver); Dev/GREEN runs of this file will show this one persistent unrelated red. *Found by TEA during test design.*
- **Question** (non-blocking): AC-1's dedup-vs-distinct-label is a deliberate Dev/Architect decision per ADR-106 — parallel multi-edges between two regions MAY be legitimate Jaquaysed loop geometry (distinct-label) or a true materializer duplicate (dedup). The 153-22 RED tests are design-agnostic on this axis EXCEPT that the projection test requires the fix to touch `region_projection.py` (see TEA Design Deviation #1). Confirm the intended semantics against the materializer/lookahead worker before choosing. Affects `sidequest/dungeon/region_projection.py` + `sidequest/dungeon/` materializer. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): resolved TEA's stale-stub Gap in this story — `test_wiring_intent_router_pass_threads_context` now passes (`acting_player=None` added to its monkeypatch stub). Affects `tests/agents/subsystems/test_movement_dispatch.py` (already applied; no further action). *Found by Dev during implementation.*
- **Question** (non-blocking): TEA's dedup-vs-distinct-label Question is answered in code as projection-side DEDUP (see Dev Design Deviation #1), but the ROOT cause — whether `beneath_sunden`'s materializer/lookahead worker is emitting genuine parallel edges or duplicates — is NOT investigated. The collapse now logs at `debug` ("project_region collapsed N parallel exit(s)"), so a recurring duplicate is observable, but a materializer-level audit (is three-edges-to-one-node ever intended?) remains open. Affects `sidequest/dungeon/` materializer + lookahead worker. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking, this story): the ordinal bridge ships `_MIDDLE_WORDS` (a named AC-3 example), the negative-index "last"/"rightmost" path, and the out-of-range fail-loud invariant — all untested; and the ordinal `resolved_via=="ordinal"` is never pinned (AC-6 hole). Affects `tests/agents/subsystems/test_movement_dispatch.py` (add middle/out-of-range/last/dedup-prefer-visible tests + pin the OTEL `resolved_via` assertions). *Found by Reviewer during code review.* → addressed in red rework.
- **Improvement** (non-blocking): the `project_region` dedup log is `DEBUG`, which is off in production, undercutting its own "stays visible for investigation — No Silent Fallbacks" comment. Affects `sidequest/dungeon/region_projection.py:324` (bump to INFO, or record collapse count on the `movement.resolved` span, or soften the comment). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `_resolve_ordinal` picks the ordinal word via `next()` over a `set`, so a multi-ordinal phrase ("second-to-last") resolves nondeterministically across restarts — contradicts the "deterministic" comment. Affects `sidequest/agents/subsystems/movement.py` (pick by defined precedence or document the limitation). *Found by Reviewer during code review.* → RESOLVED in rework (now text-order).

### Reviewer (re-review, round-trip 1)
- **Improvement** (non-blocking, LOW): `test_descriptor_consistency_single_vs_parallel_corridor_153_22` takes the `capture_spans` fixture but asserts no span — the AC-4 path's `resolved_via=="descriptor_match"` is not pinned here (it IS pinned by two sibling tests). Corroborated by test-analyzer + rule-checker. Affects `tests/agents/subsystems/test_movement_dispatch.py` (add `assert all(s.attributes["resolved_via"]=="descriptor_match" ...)` to both arms). *Found by Reviewer during re-review.*
- **Improvement** (non-blocking, LOW): three small test-assertion strengthenings — pin the unresolved-span `reason` in the out-of-range test; replace the trivially-true 2nd assertion in the AC-1 projection test with `len(to_b)==1`; add a combined assert that first/middle/last pick mutually-distinct exits. Affects `tests/agents/subsystems/test_movement_dispatch.py` + `tests/dungeon/test_region_bearings.py`. *Found by Reviewer during re-review.*
- **Question** (non-blocking): the deferred materializer audit (TEA/Dev flagged) is now observable via the INFO `project_region collapsed N parallel exit(s)` log — a follow-up should confirm whether `beneath_sunden`'s three-edges-to-one-node is legit Jaquaysed geometry or a materializer dup. Affects `sidequest/dungeon/` materializer. *Found by Reviewer during re-review.*

## Impact Summary

**Upstream Effects:** 2 findings (0 Gap, 0 Conflict, 0 Question, 2 Improvement)
**Blocking:** None

- **Improvement:** resolved TEA's stale-stub Gap in this story — `test_wiring_intent_router_pass_threads_context` now passes (`acting_player=None` added to its monkeypatch stub). Affects `tests/agents/subsystems/test_movement_dispatch.py`.
- **Improvement:** the `project_region` dedup log is `DEBUG`, which is off in production, undercutting its own "stays visible for investigation — No Silent Fallbacks" comment. Affects `sidequest/dungeon/region_projection.py:324`.

### Downstream Effects

Cross-module impact: 2 findings across 2 modules

- **`sidequest/dungeon`** — 1 finding
- **`tests/agents/subsystems`** — 1 finding

### Deviation Justifications

4 deviations

- **AC-1 distinguishability is asserted at the `project_region` level, which excludes a materializer-ONLY fix.**
  - Rationale: AC-2's own parenthetical ("a tie among parallel edges to the same node resolves deterministically rather than refusing") implies parallel edges DO reach the resolver/projection, so projection must be robust to them. Asserting the observable projection output is design-agnostic between the distinct-label fix and a projection-side dedup, and survives refactor — but it does pin the fix to *touch projection*, not the materializer alone.
  - Severity: minor
  - Forward impact: Dev/Architect must land the AC-1 fix in `region_projection.py` (distinct-label in `assign_bearings`, or dedup in `project_region`), not solely in the materializer. Raised to Architect in Delivery Findings.
- **Ordinal bridge tests assert the invariant, not the exact ordinal→edge mapping.**
  - Rationale: the ordinal→position ordering (e.g. west-to-east, or candidate-list index) is an open Dev design choice; pinning a specific mapping would couple the test to an arbitrary implementation detail. The invariant (single + distinct + advances) is the behavioral contract.
  - Severity: minor
  - Forward impact: none — Dev is free to choose the ordering rule.
- **AC-1/AC-2 fixed by projection-side DEDUP, not distinct-label or resolver-collapse (resolves TEA's open Question).**
  - Rationale: three edges that all land in `exp002.r1` are navigationally identical — distinct labels would create "north passage / east passage" leading to the SAME room (worse for a career GM). Dedup is the smaller, lower-risk change, leaves `_resolve` untouched for AC-2/AC-4/AC-5, and is consistent with `assign_bearings` + `map_emit.py` which already collapse to one key per neighbor (so prose and the DUNGEON_MAP frame agree). Collapse is logged at `debug` (No Silent Fallbacks) so a true materializer duplicate stays visible.
  - Severity: minor
  - Forward impact: the dungeon narrator/map shows ONE exit per neighbor even when the materializer emits parallel edges. A world needing multiple distinct-destination ways must use distinct destination NODES (not parallel edges to one node) — unaffected. The ADR-106 "is this parallel edge legit geometry or a materializer dup?" question is now observable via the debug log but NOT root-caused at the materializer — deferred (see Dev Delivery Findings).
- **Out-of-scope baseline restore: fixed an unrelated stale test stub.**
  - Rationale: verified production `_build_state_summary` already declares `acting_player: str | None = None` (`intent_router_pass.py:247`) and the call site at line 785 is correct — the stub was simply stale and masked no production bug. Leaving a known-red test in the file I'm handing off creates noise and risks the dev-exit "tests green" gate; the fix is one line and verified-safe.
  - Severity: minor
  - Forward impact: none — restores a fully green baseline (683 passed / 0 failed across the two affected suites); no behavior change.

## Design Deviations

No deviations yet.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **AC-1 distinguishability is asserted at the `project_region` level, which excludes a materializer-ONLY fix.**
  - Spec source: context-story-153-22.md, AC-1
  - Spec text: "either each parallel exit carries a distinct player-facing bearing/label (so `assign_bearings` no longer collapses them on `to_region_id`), or the graph/materializer guarantees a single edge per node pair"
  - Implementation: `test_parallel_edges_to_one_neighbor_are_distinguishable_153_22` feeds `project_region` a hand-built three-parallel-edge graph and asserts the projected exits are distinguishable (distinct `(to_region_id, bearing)`) OR deduped. A pure materializer-side dedup that leaves `project_region`/`assign_bearings` assuming "parallel edges never arrive" would NOT satisfy this test.
  - Rationale: AC-2's own parenthetical ("a tie among parallel edges to the same node resolves deterministically rather than refusing") implies parallel edges DO reach the resolver/projection, so projection must be robust to them. Asserting the observable projection output is design-agnostic between the distinct-label fix and a projection-side dedup, and survives refactor — but it does pin the fix to *touch projection*, not the materializer alone.
  - Severity: minor
  - Forward impact: Dev/Architect must land the AC-1 fix in `region_projection.py` (distinct-label in `assign_bearings`, or dedup in `project_region`), not solely in the materializer. Raised to Architect in Delivery Findings.
- **Ordinal bridge tests assert the invariant, not the exact ordinal→edge mapping.**
  - Spec source: context-story-153-22.md, AC-3
  - Spec text: "the leftmost of the three west passages (and the first/second/middle passage) resolves to a single edge"
  - Implementation: the ordinal tests assert that "first"/"second" each resolve to a *single* neighbor and to *different* neighbors, and that "leftmost" resolves to a single neighbor — but they do NOT pin which physical edge "leftmost"/"first" maps to.
  - Rationale: the ordinal→position ordering (e.g. west-to-east, or candidate-list index) is an open Dev design choice; pinning a specific mapping would couple the test to an arbitrary implementation detail. The invariant (single + distinct + advances) is the behavioral contract.
  - Severity: minor
  - Forward impact: none — Dev is free to choose the ordering rule.

### Dev (implementation)
- **AC-1/AC-2 fixed by projection-side DEDUP, not distinct-label or resolver-collapse (resolves TEA's open Question).**
  - Spec source: context-story-153-22.md, AC-1 + AC-2; TEA Design Deviation #1 + TEA Question.
  - Spec text: AC-1 "either each parallel exit carries a distinct player-facing bearing/label … or the graph/materializer guarantees a single edge per node pair"; AC-2 "extend the existing descriptor-fallback so a tie among parallel edges to the same node resolves deterministically rather than refusing".
  - Implementation: `project_region` now collapses parallel edges to the same neighbor into ONE `RegionExit` (prefer visible, then stable kind/bearing). With one exit per neighbor the candidate list no longer ties on parallel edges, so the existing descriptor/bearing paths resolve naturally and a genuine distinct-node tie still refuses — `movement.py::_resolve` was NOT changed for the false-ambiguity case (only the ordinal bridge was added for AC-3).
  - Rationale: three edges that all land in `exp002.r1` are navigationally identical — distinct labels would create "north passage / east passage" leading to the SAME room (worse for a career GM). Dedup is the smaller, lower-risk change, leaves `_resolve` untouched for AC-2/AC-4/AC-5, and is consistent with `assign_bearings` + `map_emit.py` which already collapse to one key per neighbor (so prose and the DUNGEON_MAP frame agree). Collapse is logged at `debug` (No Silent Fallbacks) so a true materializer duplicate stays visible.
  - Severity: minor
  - Forward impact: the dungeon narrator/map shows ONE exit per neighbor even when the materializer emits parallel edges. A world needing multiple distinct-destination ways must use distinct destination NODES (not parallel edges to one node) — unaffected. The ADR-106 "is this parallel edge legit geometry or a materializer dup?" question is now observable via the debug log but NOT root-caused at the materializer — deferred (see Dev Delivery Findings).
- **Out-of-scope baseline restore: fixed an unrelated stale test stub.**
  - Spec source: 153-22 story scope (movement resolver / projection only); TEA Delivery Finding (Gap).
  - Spec text: TEA Gap — "`test_wiring_intent_router_pass_threads_context` … stale monkeypatch stub … Out of 153-22 scope".
  - Implementation: added `acting_player=None` to the test's `_build_state_summary` monkeypatch lambda so it matches the production signature.
  - Rationale: verified production `_build_state_summary` already declares `acting_player: str | None = None` (`intent_router_pass.py:247`) and the call site at line 785 is correct — the stub was simply stale and masked no production bug. Leaving a known-red test in the file I'm handing off creates noise and risks the dev-exit "tests green" gate; the fix is one line and verified-safe.
  - Severity: minor
  - Forward impact: none — restores a fully green baseline (683 passed / 0 failed across the two affected suites); no behavior change.

### Reviewer (audit)
- **TEA Deviation #1 (AC-1 distinguishability asserted at `project_region` level)** → ✓ ACCEPTED by Reviewer: sound — the projection is exactly where the narrator and DUNGEON_MAP frame read exits, so asserting distinguishability there is the right behavioral level; Dev's dedup satisfies it cleanly.
- **TEA Deviation #2 (ordinal tests assert the invariant, not the exact mapping)** → ✓ ACCEPTED by Reviewer (principle sound): not pinning the arbitrary ordinal→edge mapping is correct and refactor-stable. CAVEAT: the design-agnostic graphs left all test exits at LR rank 2, so the bearing-informed ordering is never exercised and "middle"/"last"/out-of-range went untested — captured as [TEST] rework items, not a flaw in the deviation itself.
- **Dev Deviation #1 (projection-side DEDUP over distinct-label/resolver-collapse)** → ✓ ACCEPTED by Reviewer: well-reasoned and correct. Dedup is the smaller change, keeps `_resolve` untouched for the false-ambiguity case, and stays consistent with `assign_bearings` + `map_emit.py` (one bearing per neighbor) so prose and the map frame agree. The ADR-106 "legit geometry vs materializer dup" question is correctly deferred — BUT the chosen observability (DEBUG log) is too quiet for the deferral to be safe (see Reviewer [RULE]#4 finding); fix the log level/span in rework.
- **Dev Deviation #2 (out-of-scope stale-stub baseline restore)** → ✓ ACCEPTED by Reviewer: verified safe — production `_build_state_summary` already declares `acting_player` (`intent_router_pass.py:247`), so the stub was genuinely stale and masks no production bug. Correctly documented; restores green.

## Technical Context

**Branch Strategy:** gitflow (feat/153-22-dungeon-movement-resolver-edges)
**Repository:** sidequest-server (path: sidequest-server/, default branch: develop)

**Key Investigation Areas:**
- `sidequest/agents/subsystems/movement.py::run_movement_dispatch` — movement dispatch entrypoint
- `sidequest/agents/subsystems/movement.py::_resolve` — descriptor→edge bridging logic
- `sidequest/dungeon/region_projection.py::project_region` — exit list projection (parallel edge dedup point)
- `sidequest/dungeon/region_projection.py::assign_bearings` — bearing assignment (currently collapses parallel edges by to_region_id)
- `sidequest/dungeon/region_graph/model.py::RegionGraph` — graph model (allows multi-edges between same pair)
- `sidequest/telemetry/spans/movement.py` — OTEL span definitions

**Test Paths:**
- `tests/agents/subsystems/test_movement_dispatch.py` — primary test home (extend with parallel-edge + ordinal-descriptor cases)
- `tests/dungeon/test_region_bearings.py`, `tests/dungeon/test_region_projection_wiring.py` — bearing/projection coverage

**Wiring Gate Requirement:**
This story implements a TDD workflow; the RED phase entry gate (`gates/tea-context`) requires the story context to validate before tea can begin. The context file (sprint/context/context-story-153-22.md) has been created and pre-populated with full technical scope.