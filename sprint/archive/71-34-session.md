---
story_id: "71-34"
jira_key: ""
epic: "71"
workflow: "trivial"
---
# Story 71-34: Extract shared OTEL watcher-test harness (_setup/_Sock/_wait_for) into tests/integration/conftest — dedupe across combat + beat-advance wiring tests

## Story Details
- **ID:** 71-34
- **Jira Key:** (none — Jira integration not configured)
- **Workflow:** trivial
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** implement
**Phase Started:** 2026-06-04T20:34:00Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-04T20:34:00Z | 2026-06-04T20:34:00Z | <1m |
| implement | 2026-06-04T20:34:00Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Improvement** (non-blocking): Six more `*_otel_wiring`-style integration tests (disposition, levelup, npc_identity_seed, npc_manual_origin, npc_spawn_disposition, room_entry) plus `test_dual_track_wiring.py` carry near-identical local watcher harnesses (`_setup`/`_Sock`/poll-loop variants). Now that `watcher_setup` + `wait_for_state_transition` live in `tests/integration/conftest.py`, those could be migrated in a follow-up. Out of scope for this 2pt dedupe (story scoped to combat + beat-advance only). *Found by Dev during implementation.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Naming:** Session title said extract `_setup`/`_Sock`/`_wait_for`. Implemented as `watcher_setup` (public name, no leading underscore since it's now imported across modules) and `wait_for_state_transition` (a single predicate-based poller). Reason: leading-underscore names signal module-private; these are now shared imports. `_Sock` was dropped entirely — reused the existing canonical `FakeSocket` recording double from `tests/_helpers/doubles.py` instead of creating a third copy.
- **Wait helper unification:** The two tests had divergent `_wait_for_*` variants (combat matched `fields.field`; beat-advance matched presence of `beat_from`/`beat_to`). Unified into one `wait_for_state_transition(captured, predicate, ...)`; each test keeps its thin domain-specific wrapper (`_wait_for_event` / `_wait_for_beat_event`) that supplies the predicate. Behavior identical — same assertions pass.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `tests/integration/conftest.py` - added shared `watcher_setup` + `wait_for_state_transition` helpers (reusing `FakeSocket` from `tests/_helpers/doubles.py`)
- `tests/integration/test_combat_otel_wiring.py` - consume shared helpers; deleted local `_setup`/`_Sock`/poll-loop; `_wait_for_event` now a thin wrapper
- `tests/integration/test_encounter_beat_advance_otel_wiring.py` - consume shared helpers; deleted local `_setup`/`_Sock`/poll-loop; `_wait_for_beat_event` now a thin wrapper

**Canonical home:** `tests/integration/conftest.py` (importable helpers, not pytest fixtures — `watcher_setup` is async and parameterized by `monkeypatch`+`label`, so a plain awaitable helper fits better than a fixture). Chosen because the story title designated conftest, it is auto-discovered for the integration dir, and the recording-socket need is already met by the consolidated `FakeSocket` double — no second parallel shared location created.

**Tests:** 5/5 affected passing (GREEN); full `tests/integration/` 216 passed / 15 skipped. `ruff check .` clean.
**Branch:** feat/71-34-shared-otel-watcher-test-harness (NOT committed — SM handles git)

**Handoff:** To review
