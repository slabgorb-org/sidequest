---
story_id: "59-11"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 59-11: Retire the orchestrator's redundant second dispatch-bank run (engage once, collect directives without re-engaging)

## Story Details
- **ID:** 59-11
- **Jira Key:** (no Jira integration)
- **Workflow:** tdd
- **Stack Parent:** none

## Context

### The Problem

There are TWO `run_dispatch_bank` calls per turn in the orchestrator:

1. **Canonical pre-narrator ENGAGEMENT pass** (sidequest/server/intent_router_pass.py:158, `execute_intent_router_pre_narrator_pass`):
   - Runs on the CANONICAL package with full context: {snapshot, pack, player_name, npcs_present, additional_player_names}
   - Engages the mechanical engines (ADR-113)
   - This is the CORRECT pass, executed once per turn

2. **SECOND redundant re-run** (sidequest/agents/orchestrator.py:2538):
   - Runs AGAIN on the REDACTED package (visible_dispatch_package)
   - Purpose: collect narrator directives + feed the lethality arbiter
   - **Problem:** Uses a crippled bank_context={'npc_pool': [...]} (NO snapshot/pack/player_name)
   - **Result:** Every stateful subsystem raises TypeError (e.g. `run_confrontation_dispatch() missing 3 required keyword-only arguments`)
   - Captured in Playtest 2026-05-25 (~/.sidequest/logs/sidequest-server.log:87-88)

### Why This Happened

This is a pre-59-4 leftover:
- Story 59-4 moved engagement into `intent_router_pass` (the canonical pre-narrator pass)
- The older directive-collection re-run in the orchestrator was never retired
- It does NOT block engagement (pass 1 already engaged)
- PR #448's watcher fix stopped it crashing the turn
- **Current status:** NON-FATAL OTEL noise, not a functional blocker

### Why Fix It Now

Two problems with the current state:

1. **GM-panel pollution:** Pollutes the Subsystems tab with spurious TypeError rows that look like engagement failures
2. **Double-dispatch trap:** If anyone "fixes" it by handing the orchestrator full context, the stateful subsystems would RE-ENGAGE a second time:
   - Confrontation has a guard ('encounter already active' saves it)
   - But magic_working/scenario_clue/npc_agency are NOT all idempotent
   - This violates feedback_one_mechanism_per_problem
   - **Explicitly banned:** Do NOT paper it with context—that is the wrong fix

### Correct Fix Approaches (Design Phase)

Two candidate designs to weigh during the RED/GREEN phase. Both engage ONCE (pass 1) and collect narrator-visible directives WITHOUT re-exercising side-effecting subsystems:

**Approach A: Thread BankResult through turn_context + redact directives per-entry**
- Thread pass-1's BankResult through turn_context
- Redact the resulting DIRECTIVES per-entry via VisibilityTag.redact_from_narrator_canonical
- Same redaction flag that redact_dispatch_package uses at the package level
- Avoids re-executing the bank; reuses computed directives

**Approach B: Directive-collection-only mode of run_dispatch_bank**
- Create a directive-collection mode that does NOT invoke stateful subsystem side effects
- Separate the calculation-only path from the engagement path
- Cleaner separation of concerns but requires new abstraction

### Perception Firewall Subtlety (ADR-105)

**Critical to test carefully:**
- The lethality arbiter (orchestrator.py:2554, LethalityArbiter.arbitrate) currently consumes bank_result from the REDACTED package
- If you switch it to pass-1's CANONICAL bank_result, ensure NO canonical-only info leaks to the narrator through the arbiter's directives
- Cross-check 59-9 (cross_player redaction gap in redact_dispatch_package)—related firewall surface

## Acceptance Criteria

1. ✓ Exactly ONE `run_dispatch_bank` invocation exercises side-effecting subsystems per turn (the pre-narrator engagement pass); the orchestrator no longer re-exercises them
2. ✓ Narrator-visible directives still reach the prompt, correctly redacted per ADR-105 (no redacted/canonical-only entry leaks to the narrator)
3. ✓ Lethality arbiter still receives a correct bank_result with no perception-firewall leak; cross-checked against 59-9
4. ✓ OTEL Subsystems tab shows each subsystem exercised once per turn — no spurious TypeError rows; `dispatch_bank` + `subsystem_exercise` spans fire exactly once
5. ✓ Regression: a confrontation turn shows zero subsystem errors in OTEL when engagement succeeds (the clean-Subsystems-tab signal)

## Sm Assessment

**Routing:** TDD (phased) → RED phase → TEA (The Architect).

**Repo:** sidequest-server only, branch `feat/59-11-retire-redundant-dispatch-bank-run` off `origin/develop`.

**What this story is (and is not):**
- This is **engineering cleanup**, not a product decision — Keith confirmed (PR #448 origin, 2026-05-25). It is **non-fatal OTEL noise** today, not a turn-breaking bug. The value is a clean GM-panel Subsystems tab (the lie detector) and closing a latent double-dispatch trap.
- The fix is a **one-mechanism** correction: engage side-effecting subsystems exactly ONCE (pass 1 in `intent_router_pass.py`), and have the orchestrator collect narrator-visible directives WITHOUT re-exercising them.

**Hard constraints for the test author (TEA):**
- The "paper it with full context" fix is **explicitly banned** — it would re-engage non-idempotent subsystems (magic_working / scenario_clue / npc_agency) a second time. Tests must *prove* side-effecting subsystems fire exactly once per turn, not just that no TypeError is raised.
- **Perception firewall (ADR-105) is the subtle risk.** The lethality arbiter (`orchestrator.py:2554`) currently consumes bank_result from the REDACTED package. Any test that switches the arbiter to pass-1's CANONICAL bank_result MUST assert no canonical-only / redacted info leaks to the narrator. Cross-check 59-9 (cross_player redaction gap).
- **OTEL is the acceptance signal.** Tests should assert `dispatch_bank` + `subsystem_exercise` spans fire exactly once per turn (AC4/AC5). A clean Subsystems tab is how Keith verifies the engine isn't winging it.

**Design choice (A vs B) is deferred to RED/GREEN** — both approaches in the Context section are viable; let the failing tests shape which is minimal. Do not over-build a new abstraction (Approach B) if threading the existing BankResult (Approach A) satisfies the tests.

## Workflow Tracking
**Workflow:** tdd
**Phase:** red
**Phase Started:** 2026-05-29T11:52:14Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-29 | 2026-05-29T11:52:14Z | 11h 52m |
| red | 2026-05-29T11:52:14Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

### TEA (test design)
- **Gap** (blocking): Story 59-11 is **already delivered** — the redundant second `run_dispatch_bank` was retired by PR #508 (`63f3ffe`, "consolidate dispatch bank"), which predates this story's setup. Current HEAD has exactly one production call site (`intent_router_pass.py:165`, pass 1); the orchestrator consumes the stashed `context.bank_result` with per-directive `redact_from_narrator_canonical` filtering (`orchestrator.py:2570-2618`). No second call exists to retire. The story context's staleness check ("verified 2026-05-28, both call sites still exist") was wrong — #508 had already consolidated it.
  ACs are already pinned by `tests/server/test_dispatch_bank_consolidation_G5.py`: AC1/AC2 → `test_orchestrator_consumes_stashed_result_without_rerunning_bank` (monkeypatches `run_dispatch_bank` to explode if re-called); AC3 → `test_redacted_directive_filtered_from_prompt_via_visibility`; AC4 → `bank_result.errors == []` assertions; plus fail-loud `test_build_narrator_prompt_fails_loud_when_bank_result_missing`.
  No RED phase is possible (no failing behavior to write). Recommend SM cancel/close 59-11 as already-delivered by #508. Minor unmet literal: AC1's explicit OTEL `intent_router.dispatch_bank`-fires-once *span-count* assertion has no dedicated test — but the behavioral "orchestrator never re-runs the bank" proof is stronger and present, and there is only one production call site. *Found by TEA during test design.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

No design deviations yet.