---
story_id: "73-5"
jira_key: ""
epic: "73"
workflow: "trivial"
---
# Story 73-5: Suppress re-fired encounter.confrontation_initiated span on resolution turn

## Story Details
- **ID:** 73-5
- **Jira Key:** (none — project does not use Jira)
- **Workflow:** trivial
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Repos:** sidequest-server
**Phase:** implement
**Phase Started:** 2026-06-03T12:17:27Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-03T12:17:27Z | 2026-06-03T12:17:27Z | 0m |

## Delivery Findings

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

No upstream findings.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Gap** (non-blocking): `tests/e2e/test_encounter_wiring_e2e.py` errors at setup with
  `fixture 'session_handler_factory' not found` for both its tests
  (`test_combat_walkthrough_initiate_tick_resolve`, `test_xp_award_higher_in_combat_than_out`).
  The fixture is defined in `tests/server/conftest.py`, which is NOT visible to `tests/e2e/`.
  Affects `tests/e2e/test_encounter_wiring_e2e.py` / `tests/server/conftest.py` (the
  `session_handler_factory` + `span_exporter` fixtures need to live in a conftest visible to
  `tests/e2e/`, e.g. `tests/conftest.py`, or the e2e file needs its own fixtures). Pre-existing,
  unrelated to 73-5 (my diff touches only `encounter_lifecycle.py` + `tests/server/`).
  *Found by Dev during implementation.*

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Repurposed an existing test instead of leaving its same-type premise intact**
  - Spec source: context-story-73-5.md (no ACs recorded); story title + epic-73.yaml 73-5 directive
  - Spec text: "the resolution turn re-fires a cosmetic initiated span" — suppress the re-fired `encounter.confrontation_initiated` span on the resolution turn
  - Implementation: The chosen gate keys on `current.resolved and current.encounter_type == encounter_type` (the just-resolved same-type confrontation still on the snapshot). This changed the premise of the pre-existing `test_instantiate_replaces_resolved_encounter`, which used the SAME type (`combat`/`combat`) and asserted replacement. I updated that test to use a DIFFERENT prior type (`negotiation` resolved → new `combat`) so it still pins its real intent ("a resolved prior does not block a genuinely-new confrontation"), and added `test_resolution_turn_same_type_suppresses_initiated_span` for the new same-type-suppression behavior.
  - Rationale: A resolved encounter of the same type still sitting on the snapshot is precisely the resolution-turn re-dispatch the epic describes; a genuinely-new same-type fight only arises after the resolved encounter is torn down (`snapshot.encounter is None`), which still fires the span. Different-type replacement is preserved.
  - Severity: minor
  - Forward impact: minor — sibling story 73-2 tears down the panel/encounter on resolution; once that lands, `snapshot.encounter` is cleared on the resolution turn and the first guard (`current is None`) already covers it. The 73-5 same-type gate is the belt-and-suspenders for the window where the resolved encounter has not yet been torn down.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/server/dispatch/encounter_lifecycle.py` — added a resolution-turn guard in `instantiate_encounter_from_trigger`: when the prior `snapshot.encounter` is `resolved` AND is the same `encounter_type`, return `None` (no rebuild, no span) instead of re-firing `encounter.confrontation_initiated`.
- `tests/server/test_encounter_lifecycle.py` — added `test_resolution_turn_same_type_suppresses_initiated_span` (asserts the span fires exactly once across initiation + resolution turn); updated `test_instantiate_replaces_resolved_encounter` to use a different prior type so it still pins genuinely-new-confrontation replacement.

**Premise check:** CONFIRMED LIVE. A standalone harness drove initiation → unresolved mid-turn (no-op, correct) → resolution turn (same type, prior `resolved=True`) and observed `encounter.confrontation_initiated` firing **twice**. After the fix it fires once.

**Tests:** 20/20 in `test_encounter_lifecycle.py` (GREEN); 36/36 across related dispatch/confrontation suites. The 2 errors in `tests/e2e/test_encounter_wiring_e2e.py` are a pre-existing `fixture 'session_handler_factory' not found` conftest-scoping issue (logged as a Delivery Finding), not caused by this change.

**Ruff:** `ruff format --check` + `ruff check` clean on both changed files.

**Branch:** feat/73-5-suppress-refired-confrontation-span (pushed)

**Handoff:** To finish phase (SM creates/merges PR per trivial workflow — but per story instructions, Dev self-merges this trivial story).
