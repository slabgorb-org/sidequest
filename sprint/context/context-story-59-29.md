---
parent: context-epic-59.md
workflow: tdd
---

# Story 59-29: Co-locate witnessed_act precondition coverage into test_dispatch_precondition_gate.py

## Business Context

Epic 59 (Intent Router — Mechanical-Engagement Spine) enforces SOUL's
anti-Illusionism principle: mechanical engines must engage *before* the narrator
runs, and every decision must emit OTEL so the GM panel can prove the engine
fired (not improvised). The pre-narrator **precondition gate**
(`dispatch_precondition_gate.py`, born in Story 59-8) is part of that honesty
machinery: it drops structurally-inert dispatches (a subsystem whose world-level
precondition can never be met on this snapshot) *before* the dispatch bank and
the lie-detector watcher read the package, emitting a loud
`intent_router.dispatch.gated` span per drop instead of letting the watcher fire
an unavoidable false-true-positive mismatch every turn.

Story 59-28 added the `witnessed_act` subsystem's structural precondition
(`snapshot.political_state is None → inert`) to the gate's
`_INERT_PRECONDITIONS` map. But that precondition is currently exercised only
*indirectly* — a single predicate-level assertion buried in
`tests/agents/test_witnessed_act_subsystem.py`
(`test_precondition_inert_without_political_state`, lines 77–81). The gate's own
coverage lives in `tests/agents/test_dispatch_precondition_gate.py`, where the
sibling `scenario_clue` precondition is tested thoroughly (pure-function drop/keep,
sibling preservation, OTEL span emission, router-pass integration).

**Value:** test hygiene. Co-locating the `witnessed_act` precondition coverage
beside `scenario_clue` in the gate test file means the gate's behavior is
verifiable in one place, the two registered preconditions are tested
symmetrically, and a future engineer reading the gate file finds its full test
surface adjacent — not split across an unrelated subsystem test. This is a
**test-only** story: **no production change** to `dispatch_precondition_gate.py`
or any other source file.

## Technical Guardrails

**Target file (where coverage lands):**
- `tests/agents/test_dispatch_precondition_gate.py` — mirror the existing
  `scenario_clue` test shapes for `witnessed_act`, keying off
  `snapshot.political_state` instead of `snapshot.scenario_state`. The file is
  already organized into three sections; place witnessed_act tests in the
  matching section(s):
  - **Pure function** — `gate_inert_dispatches(package, snapshot)` (line ~138).
    Sibling tests: `test_scenario_clue_dropped_when_scenario_state_none`,
    `test_scenario_clue_kept_when_scenario_state_present`,
    `test_scenario_clue_dropped_but_sibling_dispatch_preserved`.
  - **OTEL wrapper** — `run_dispatch_precondition_gate(...)` (line ~211).
    Sibling tests: `test_gate_emits_one_gated_span_per_drop`,
    `test_gate_emits_no_span_when_nothing_gated`.

**Source file (READ ONLY — do not modify):**
- `sidequest/agents/dispatch_precondition_gate.py` —
  `_witnessed_act_precondition_unmet` (lines 78–81) returns a non-None reason
  string `"snapshot.political_state is None (world ships no wry_whimsy
  premise/bloc layer)"` when `political_state is None`, else `None`.
  `_INERT_PRECONDITIONS["witnessed_act"]` (line 86) registers it.

**Source of the coverage to co-locate (the move-from site):**
- `tests/agents/test_witnessed_act_subsystem.py` lines 77–81
  (`test_precondition_inert_without_political_state`) — the existing indirect
  predicate-level assertion. Reuse its fixtures (`_snapshot()` hydrates
  `political_state` via `PoliticalState.from_world(...)`; a bare `GameSnapshot()`
  has `political_state is None`). Decide whether to **delete** it after
  co-locating (avoid duplicate coverage) or leave a thin predicate check — see AC
  Context.

**Patterns to follow:**
- Build a `political_state`-bearing snapshot the same way
  `test_witnessed_act_subsystem.py::_snapshot()` does (PremiseDef/BlocDef pack →
  `PoliticalState.from_world`), and a no-political-state snapshot via bare
  `GameSnapshot()` / `world_slug` without hydration. Reuse the gate test file's
  existing `_package_with(...)`, `_all_dispatch_subsystems(...)`, and
  fake-tracer helpers rather than inventing new ones.
- Assert at the **gate behavior** level (dispatch dropped / kept, `GatedDispatch`
  carries the right subsystem + reason, one span per drop), not just the raw
  predicate — that is what "co-locate into the gate test" means.

**What NOT to touch:**
- No edit to any file under `sidequest/` (production). If a test cannot pass
  without a production change, STOP and log a deviation — the story explicitly
  states "No production change."
- Do not alter the `scenario_clue` tests or the gate's shared helpers' behavior.

**Project rules in force (sidequest-server/CLAUDE.md):**
- **No Source-Text Wiring Tests.** Do NOT add a test that greps
  `dispatch_precondition_gate.py` source for `witnessed_act`. Prove wiring via
  *behavior*: drive a witnessed_act dispatch through `gate_inert_dispatches` /
  `run_dispatch_precondition_gate` and assert the drop + the
  `intent_router.dispatch.gated` span. (Reflection over `_INERT_PRECONDITIONS`
  as a dict is acceptable — that interrogates a runtime object, not source text.)
- **Every test must assert something meaningful** — no `is_none()` on
  always-None, no vacuous passes. The "kept when hydrated" case must assert the
  dispatch *survives* (subsystem still present in the filtered package), not just
  that no exception was raised.

## Scope Boundaries

**In scope:**
- Add `witnessed_act` precondition coverage to
  `tests/agents/test_dispatch_precondition_gate.py`, mirroring the `scenario_clue`
  coverage: (a) dropped when `political_state is None`, (b) kept when
  `political_state` is hydrated, and (c) the OTEL `gated` span fires once on the
  drop carrying `subsystem == "witnessed_act"` and the precondition reason.
- Co-locate (move) the existing indirect predicate assertion out of
  `test_witnessed_act_subsystem.py`, removing the duplicate once gate-level
  coverage exists, so the gate's coverage lives in one place.
- Keep the full server test suite green (`uv run pytest`).

**Out of scope:**
- Any change to production source (`dispatch_precondition_gate.py`,
  subsystems, intent router pass).
- New preconditions or new subsystems in `_INERT_PRECONDITIONS`.
- Confidence-gating / threshold work (epic-level, not this story).
- 59-30 (`_WITNESSES` engagement witness) — a sibling story, not this one.

## AC Context

Derived from the story description and the SM session ACs. Each must be verified
by a meaningful assertion driven through the real gate functions.

**AC1 — Inert when `political_state is None` (drop + reason).**
A `DispatchPackage` carrying a `witnessed_act` dispatch, gated against a snapshot
with `political_state is None`, must come back with that dispatch **removed** and
exactly one `GatedDispatch` whose `subsystem == "witnessed_act"` and whose
`reason` is the non-None precondition string. Mirror
`test_scenario_clue_dropped_when_scenario_state_none`.
- *Edge:* a turn dispatching `witnessed_act` **and** a sibling (e.g.
  `npc_agency` or `confrontation`) into a no-political-state snapshot drops only
  `witnessed_act`; the sibling survives. (Mirror
  `test_scenario_clue_dropped_but_sibling_dispatch_preserved`.)

**AC2 — Not inert when `political_state` is hydrated (pass-through).**
The same dispatch gated against a snapshot whose `political_state` is hydrated
(`PoliticalState.from_world(...)`) must pass through **untouched**: the filtered
package still contains the `witnessed_act` dispatch and `gated` is empty. Assert
the dispatch *is present* in the filtered package (not merely "no error"). Mirror
`test_scenario_clue_kept_when_scenario_state_present`.

**AC3 — OTEL span on drop / silence on no-drop (lie-detector honesty).**
Driving the **wrapper** `run_dispatch_precondition_gate(...)` with a fake tracer
over a no-political-state snapshot emits exactly **one**
`intent_router.dispatch.gated` span with `subsystem == "witnessed_act"`; driving
it over a hydrated snapshot emits **zero** spans. Mirror
`test_gate_emits_one_gated_span_per_drop` and
`test_gate_emits_no_span_when_nothing_gated`. This is the OTEL-observability leg
(CLAUDE.md OTEL principle) — the gate must be *seen* dropping the dispatch.

**AC4 — Coverage co-located, not duplicated; suite green.**
The witnessed_act precondition coverage now lives in
`test_dispatch_precondition_gate.py`. The indirect assertion previously in
`test_witnessed_act_subsystem.py` (lines 77–81) is removed (or reduced to a
predicate-only check with no overlap) so there is one home for gate coverage. The
full `uv run pytest` suite passes (no regression in either touched test file or
elsewhere), lint (`ruff check`) and types (`pyright`) are clean. This is the
wiring/no-regression AC — verified by a green run, **not** by a source grep.

## Assumptions

- The `witnessed_act` precondition predicate and its `_INERT_PRECONDITIONS`
  registration (from 59-28) are already merged on `develop` and stable — verified
  present at `dispatch_precondition_gate.py:78–87`. No production change is needed
  to make these tests pass; if one turns out to be required, that is a deviation
  to log, not a silent fix.
- The gate test file's existing helpers (`_package_with`,
  `_all_dispatch_subsystems`, fake-tracer span capture) are reusable as-is for a
  witnessed_act dispatch; only a `political_state`-bearing snapshot builder needs
  adapting from `test_witnessed_act_subsystem.py::_snapshot()`.
- Removing the duplicated predicate assertion from
  `test_witnessed_act_subsystem.py` does not drop coverage of anything *other*
  than the precondition (the rest of that file tests the handler, which stays).
