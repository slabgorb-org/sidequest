---
story_id: "126-2"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 126-2: [BUG] Re-verify router-driven encounter seating returns the table/card game (poker)

## Story Details
- **ID:** 126-2
- **Jira Key:** (none — Jira not configured for this project)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** red
**Phase Started:** 2026-06-18T08:41:41Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-18T08:35:33.243982+00:00 | 2026-06-18T08:41:41Z | 6m 7s |
| red | 2026-06-18T08:41:41Z | - | - |

## Technical Approach

### Root Cause (Diagnosis)
The 'card game totally broken' finding from sq-playtest-pingpong was traced to a DOWNSTREAM effect of the intent-router error_max_turns blocker (now fixed in 126-9), NOT a regression in the table engine itself.

**Seating Flow:** N-seat table games are instantiated at `narration_apply.py:5450` only when:
1. A `ResolutionMode.table_resolution` ConfrontationDef arrives via the router-driven dispatch path (post-ADR-113)
2. Router fires successfully and returns a valid dispatch_package
3. `instantiate_table_encounter()` (encounter_lifecycle.py:1175) is invoked

**What Broke:** Router degraded (dispatch_package=None) → no table_resolution cdef → instantiate_table_encounter() never reached → live save showed encounter=None

**Engine Status:** The table engine is intact. Last table work: #522 (feat(table)) and #685 (War Rig crew table-game), both pre-Fate-port. The issue is in the dispatch path, not table mechanics.

### Test Plan
1. **Re-run with Fixed Router:** Now that 126-9 (narrator latency + extended-thinking OFF) is merged and the router is restored to baseline:
   - Trigger a poker/table scene in a pack with table games (e.g., spaghetti_western/poker)
   - Confirm a `table_resolution` cdef arrives via the live router
   - Verify `instantiate_table_encounter()` runs and encounter != None
   - Confirm antes/seats/sealed-commit loop is present

2. **If Still Broken:** Capture the dispatch trace (router output → cdef ResolutionMode) and file as a separate finding with the debugging work required.

3. **DO NOT Preemptively Hunt:** Per FIXER's explicit instruction, do not hunt in game/table/ speculatively. Re-test first, fix if needed based on findings.

### Acceptance Criteria (Detailed)
1. **In a pack with a table game (e.g. spaghetti_western poker), trigger a poker/table scene; confirm a table_resolution cdef arrives via the live router and instantiate_table_encounter() runs (encounter != None, antes/seats/sealed-commit loop present).**
   - Use an understudy run or manual playtest on a server running post-126-9 develop
   - Add OTEL spans or debug output at router dispatch to confirm cdef.resolution_mode == ResolutionMode.table_resolution
   - Assert encounter is not None after narration_apply.py:5450 runs
   - Verify table-seating preconditions (antes, seats dict, sealed_commit_loop present)

2. **If it STILL does not seat after the router fix, capture the dispatch trace (router output -> cdef ResolutionMode) and fix the seating gap — that is the separate finding.**
   - If router returns a non-table_resolution cdef for table scenarios, capture and document why
   - If encounter is still None despite table_resolution arriving, debug instantiate_table_encounter() and file a follow-up story
   - Do NOT assume table engine is broken; verify router dispatch first

## Sm Assessment

**Routing:** tdd / phased → handing to TEA (Amos) for RED. Single repo: `sidequest-server`. Branch `feat/126-2-reverify-router-table-seating` (off develop). 2 pts, p3.

**What TEA needs to know:**
- This is a **re-verification** bug, not a confirmed-broken story. The "card game broken" symptom was diagnosed as DOWNSTREAM of the intent-router `error_max_turns` blocker, which 126-9 already fixed (extended-thinking OFF on the narrator tool-loop, merged to develop). The table engine itself is intact (#522, #685).
- The RED phase locks in the **seating contract**: when a `ResolutionMode.table_resolution` ConfrontationDef reaches the router-driven dispatch path, `instantiate_table_encounter()` (encounter_lifecycle.py:1175) must run and `narration_apply.py:5450` must produce `encounter != None` (antes/seats/sealed-commit loop present). Write the test against that contract — not against the live LLM router.
- **Likely outcome:** the seating path may already pass now that the router is restored. That is a legitimate TDD result — the RED test may need to target the actual gap (a unit/integration test that drives a synthesized `table_resolution` cdef through dispatch → seating, asserting the encounter materializes), so the regression is locked even though the upstream router is fixed. If TEA finds the seating genuinely still fails with a valid table_resolution cdef in hand, that is the "separate finding" FIXER described — capture the dispatch trace.
- **Boundary (FIXER's explicit instruction):** DO NOT pre-emptively hunt in `game/table/`. Verify dispatch → seating first; only debug the table engine if a valid table_resolution cdef demonstrably fails to seat.
- **OTEL:** per project doctrine, the verification should assert on an OTEL span at router dispatch confirming `cdef.resolution_mode == table_resolution` — the GM-panel lie-detector for whether the path is actually engaged vs. narrated.

## TEA Assessment

**Tests Required:** Yes (regression lock)
**Status:** GREEN — re-verification PASSES. This is the legitimate re-verify outcome SM flagged: the seating contract already holds; the bug was upstream (126-9). No production code change needed.

**Test File:**
- `tests/agents/subsystems/test_table_resolution_seating_dispatch.py` — 4 tests, all passing.

**What was verified (the seating contract, at the router-driven dispatch entry — the exact seam the degraded router bypassed):**
1. `test_table_resolution_dispatch_seats_the_table` — `run_confrontation_dispatch({type: poker})` mutates `snapshot.encounter` None→seated `table_state` (PC + opponent seats, win_condition=table_showdown, one pot-contribution slot per seat).
2. `test_table_resolution_seats_through_real_dispatch_bank` — same contract end-to-end through `run_dispatch_bank` (the production fan-out path).
3. `test_table_resolution_dispatch_emits_table_dealt_span` — `table.dealt` OTEL span fires with seat_count≥2 + game_kind=poker (GM-panel lie-detector: actually seated, not narrated).
4. `test_table_resolution_declines_when_no_other_seat` — lone-PC table declines (encounter stays None) + `encounter.no_opponent_available` span (ADR-116).

**Key fidelity correction (Keith's steer — these tables were being reworked for Fate):** initially bound the synthetic pack to vestigial `dial`; re-pointed to the **real `fate` binding** that `spaghetti_western` poker ships. Under `dial` all 4 passed; binding `fate` first failed only on a missing `FateConfig` (RulesConfig fails loud per ADR-144) — a fixture gap, NOT an engine break — then passed once `FateConfig()` was supplied. **Confirmed: table seating is ruleset-agnostic (Fate inherits `deal_table`/`resolve_table` from base) and holds under the production Fate binding.**

**Rule Coverage:**

| Rule | Test | Status |
|------|------|--------|
| Every suite needs a wiring test | `test_table_resolution_seats_through_real_dispatch_bank` (real dispatch bank) | passing |
| No source-text wiring tests | all assertions on snapshot/table_state/OTEL spans | satisfied |
| No silent fallbacks | no-opponent guard declines + fires span | passing |
| OTEL observability | `table.dealt` span asserted | passing |

**Self-check:** 0 vacuous tests — every test asserts on materialized seating state or a named span.

**Disposition (Keith's decision):** Close 126-2 as **verified, no fix needed**. Reclassify off the tdd `tests_fail` gate (re-verification produced green by design). Resolution-under-Fate coverage gap filed as a follow-up (see Delivery Findings).

**Handoff:** To SM (Camina Drummer) to close as verified.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): the table **resolution** path (showdown / pot award / fold-barrier) is verified ONLY under the vestigial `dial` ruleset, which no live pack binds. Affects `tests/server/test_table_resolution_wiring.py` (its `_poker_table_snapshot` and the multi-DP tests all pass `ruleset_slug="dial"`). The live table packs bind `fate` (spaghetti_western poker, tea_and_murder auction) and `cwn` (road_warrior war_rig_crew). Re-point/duplicate those resolution tests under the production bindings so the "card game not engaging" *resolution* half is covered at production fidelity. *Found by TEA during test design (126-2).* → suggest a follow-up story.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **RED phase produced PASSING tests (no failing-test → fix cycle)**
  - Spec source: tdd workflow red phase, gate `tests_fail`
  - Spec text: red phase hands off green-only when tests FAIL (RED state)
  - Implementation: the 4 regression tests pass on arrival; no production change was made
  - Rationale: 126-2 is a re-verification bug whose root cause was fixed upstream (126-9). The seating contract already holds — manufacturing an artificial failure would violate "No Stubbing / no hacks." Keith ruled the story closes as verified (regression-locked), reclassified off the `tests_fail` gate.
  - Severity: minor
  - Forward impact: story closes via verified/trivial path rather than red→green→review; resolution-under-Fate coverage tracked as a separate finding.
- **Synthetic pack re-pointed from `dial` to the real `fate` binding**
  - Spec source: story scope (re-verify production poker seating) + CLAUDE.md (no live pack binds `dial`)
  - Spec text: verify the path production actually takes
  - Implementation: fixture binds `ruleset="fate"` + `FateConfig()` (matching spaghetti_western poker) instead of vestigial `dial`
  - Rationale: testing under `dial` verifies a binding no live pack uses; the reported card game runs under Fate. Re-pointing makes the regression lock production-faithful.
  - Severity: minor
  - Forward impact: none (seating is ruleset-agnostic; confirmed green under both).