---
story_id: "105-1"
jira_key: ""
epic: "105"
workflow: "tdd"
---
# Story 105-1: Restore the span-proof instrument — teach scripts/playtest.py to answer the Epic-66 pick_portrait frame

## Story Details
- **ID:** 105-1
- **Jira Key:** (none — SideQuest is personal, no Jira integration)
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 2
- **Priority:** p1
- **Type:** bug

## Story Context

Beneath Sünden's procedural Deep is fully built but unreachable in live play. The root cause lies in the surface→deep crossing (movement.py 59-12 handoff). The narrative-spanning test scenarios/beneath_sunden_engagement.yaml (59-15) currently fails at chargen with WrongPhaseError when the headless playtest driver cannot answer the pick_portrait frame (portrait_confirm skip).

This story unblocks the scenario by teaching scripts/playtest.py to answer the Epic-66 pick_portrait frame so 59-15 can run past chargen and capture movement/confrontation/magic spans, proving the real defect lies in the crossing seam, not the chargen flow.

**Coordination Risk:** Story 90-9 (currently backlog) also edits scripts/playtest.py chargen. Coordinate the driver changes to avoid duplication or merge conflicts.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-12T15:34:15Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-12T15:11:40Z | 2026-06-12T15:13:04Z | 1m 24s |
| red | 2026-06-12T15:13:04Z | 2026-06-12T15:26:55Z | 13m 51s |
| green | 2026-06-12T15:26:55Z | 2026-06-12T15:29:40Z | 2m 45s |
| review | 2026-06-12T15:29:40Z | 2026-06-12T15:34:15Z | 4m 35s |
| finish | 2026-06-12T15:34:15Z | - | - |

## Sm Assessment

**Decision:** Hand off to RED phase (tea/Fezzik). Story is well-scoped and ready.

**What's clear:**
- Single, bounded defect in the headless driver: `scripts/playtest.py` does not answer the Epic-66 `pick_portrait` frame, so chargen dies with `WrongPhaseError` before the scenario can capture spans.
- Fix target is the orchestrator repo only (`scripts/playtest.py` + the gated scenario `scenarios/beneath_sunden_engagement.yaml`, Story 59-15).
- This is the *instrument* fix, not the crossing fix — 105-1 makes the span-proof test runnable; 105-2 (5pt, backlog) is the actual surface→deep seam fix that goes green on that proof. Keep scope to the driver.

**Test target for RED:** A failing assertion that the headless driver advances past chargen for `beneath_sunden_engagement.yaml` (no `WrongPhaseError`), i.e. it sends the `portrait_confirm`/skip in response to the `pick_portrait` frame. Don't over-reach into asserting movement/confrontation/magic spans go green — that's 105-2's job; here the bar is "runs past chargen."

**Coordination risk (carry forward):** Story 90-9 (backlog) also edits `scripts/playtest.py` chargen (it fixes headless chargen to honor scenario `class:`). 90-9 is not yet started, so no live conflict, but Dev should make the `pick_portrait` answer additive/composable so 90-9's class-honoring change layers cleanly. Flagged in Story Context above.

**Refs:** ADR-106, ADR-113; scenarios/beneath_sunden_engagement.yaml; movement.py:201-267 (the 59-12 handoff — context only, NOT in scope for 105-1).

## TEA Assessment

**Tests Required:** Yes
**Reason:** n/a — a real driver behavior bug; not a chore-bypass category.

**Test Files:**
- `tests/scripts/test_playtest_pick_portrait.py` — RED tests for the Epic-66 `pick_portrait` driver frame.

**Tests Written:** 11 tests covering 4 ACs (5 currently failing = the bug; 6 passing = additive-regression guards that must stay green through GREEN).
**Status:** RED (failing — ready for Dev)

**Repro confirmed:** `AutoChargen.respond(pick_portrait_frame)` currently returns `{phase: continue}` instead of `{phase: portrait_confirm}` — verified live. This is exactly why the server (with `portrait_step_shown=True`) never advances and the next action raises `WrongPhaseError`.

**ACs defined (none in YAML — authored here):**
- **AC-1** — The `pick_portrait` frame (`phase=scene`, `input_type=pick_portrait`) is answered with exactly one `phase=portrait_confirm` CHARACTER_CREATION message. (3 tests: with class_pref, without, and `portraits_available=False`.)
- **AC-2** — The answer is a SKIP: `selected_portrait_ref` is None/empty (driver never invents a slug). (Anchored on the portrait_confirm phase so it is not vacuous.)
- **AC-3** — The frame is NOT misrouted as a generic scene: not a `continue`, not a `scene` choice, and never a silent empty stall.
- **AC-4** — Additive: existing chargen input_types are unperturbed (select choice, class_pref selection, confirmation, complete). Doubles as the Story-90-9 coordination guard.

### Rule Coverage

| Rule (project) | Test(s) | Status |
|------|---------|--------|
| No Silent Fallbacks (fail loud, don't stall) | `test_pick_portrait_does_not_silently_stall` | passing-guard |
| Verify wiring, not just existence (fixture mirrors prod server frame) | `test_pick_portrait_frame_returns_portrait_confirm` | failing |
| No vacuous assertions (self-check) | `test_portrait_confirm_is_a_skip` (anchored on phase) | failing |
| Additive change / no regression | `TestExistingChargenUnaffected` (4 tests) | passing-guard |

**Rules checked:** Python lang-review has no enum/constructor/tenant rules applicable to a dict-message driver; the load-bearing ones (No Silent Fallbacks, fixture-driven wiring, no vacuous asserts) all have coverage.
**Self-check:** 1 initially-vacuous test found (`test_portrait_confirm_is_a_skip` passed against the buggy `continue` reply) — fixed by anchoring on the `portrait_confirm` phase before asserting the empty ref.

**Handoff:** To Dev (Inigo Montoya) for implementation.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `scripts/playtest_messages.py` — added `make_chargen_portrait_confirm(selected_portrait_ref=None)` helper (a `{phase: portrait_confirm, selected_portrait_ref: None}` skip message).
- `scripts/playtest.py` — imported the helper; added an `input_type == "pick_portrait"` branch in `AutoChargen.respond` that returns the portrait_confirm skip before the generic-scene fall-through.

**Tests:** 11/11 passing (GREEN) — `tests/scripts/test_playtest_pick_portrait.py`. Lint clean (ruff).
**Approach:** Minimal and additive — one new branch keyed on the server's `input_type=pick_portrait`, matching the verbatim frame TEA fixtured. No other chargen path touched, so Story 90-9's class-honoring change composes cleanly.
**Branch:** main (orchestrator is trunk-based; no feature branch / PR — SM finish archives).

**Handoff:** To TEA (Fezzik) for the verify phase.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (11/11 GREEN, ruff clean, 0 smells, +240/-0) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (1 enabled returned; 8 disabled via `workflow.reviewer_subagents`, pre-filled as Skipped)
**Total findings:** 0 confirmed, 0 dismissed, 1 deferred (the TEA unit-vs-e2e deviation — accepted, deferred to 105-2)

## Reviewer Assessment

**Verdict:** APPROVE

**Diff:** +240 / −0 across 3 files (`scripts/playtest.py`, `scripts/playtest_messages.py`, `tests/scripts/test_playtest_pick_portrait.py`). Purely additive — no pre-existing code mutated.

### Rule Compliance

Applicable project rules for a headless playtest-driver change (orchestrator `scripts/`, not production engine):
- **No Silent Fallbacks (CLAUDE.md):** ✓ The `pick_portrait` branch returns an explicit `portrait_confirm` reply rather than the silent empty/`continue` that previously stalled chargen. `test_pick_portrait_does_not_silently_stall` enforces it.
- **No Stubbing / No half-wired features:** ✓ The helper is fully wired — imported (`playtest.py:90`) and dispatched (`playtest.py:450`), with the receiver loop (`playtest.py:751`) already calling `AutoChargen.respond`. Non-test consumer confirmed.
- **Verify Wiring, not just Existence:** ✓ The test fixture mirrors the server emitter (`chargen_mixin.py::_render_portrait_scene`) verbatim and drives the real `respond()` method — fixture-driven behavior, not a source-text grep.
- **OTEL Observability Principle:** N/A here — the *server* fires `chargen.portrait_select` on confirm/skip (`chargen_mixin.py:642`); this story only teaches the *client driver* to send the confirm. No backend subsystem decision is added in this diff.
- **Crunch/Flavor, SOUL gameplay rules:** N/A — test harness, no narrator/player-facing behavior.
- **Type rules (newtypes, validated constructors, private fields, tenant isolation):** N/A — dict-based protocol messages are the established convention across all of `playtest_messages.py`; no new type, enum, or tenant-bearing field introduced. No struct to audit.
- **Security (injection/auth/secrets):** N/A — local playtest driver, no untrusted input, no auth surface, no secrets.

### Observations

- `[VERIFIED]` Dispatch branch correctness — `scripts/playtest.py:450-456` returns `[make_chargen_portrait_confirm()]` for `input_type == "pick_portrait"`, placed before the generic `choices` fall-through (`:459`). The frame carries no choices, so ordering is safe either way; early return is clean. Evidence: diff hunk + `_render_portrait_scene` (chargen_mixin.py:557) confirms the frame shape.
- `[VERIFIED]` Skip honors the server contract — `make_chargen_portrait_confirm()` defaults `selected_portrait_ref=None`; server `_chargen_portrait_confirm` reads `payload.selected_portrait_ref or None` (chargen_mixin.py:604) and treats None as a skip, advancing to the confirmation summary. No required field is omitted (all `CharacterCreationPayload` fields are Optional).
- `[VERIFIED]` Out-of-order safety — server guards `portrait_confirm` behind `portrait_step_shown` (chargen_mixin.py:596); the driver only emits it in response to the frame, which is exactly when that flag is set (chargen_mixin.py:2184). No spurious-send path.
- `[VERIFIED]` Additive / no regression — `TestExistingChargenUnaffected` covers select-choice, class_pref selection, confirmation, and complete; all pass. The `done` flag is untouched on the new branch (correct — chargen continues to `confirmation`→`complete`).
- `[VERIFIED]` Non-vacuous tests — `test_portrait_confirm_is_a_skip` anchors on `phase == "portrait_confirm"` before asserting the empty ref, so it cannot pass against the old `continue` reply (the vacuity TEA self-caught).
- `[LOW]` Stringly-typed dict messages — consistent with the entire `playtest_messages.py` module; not a new anti-pattern, no action.
- `[LOW]` Pre-existing debt — `scripts/tests/test_playtest_split.py` (story 21-1) has 9 stale source-text-grep failures, outside the gated `testpaths`. Not caused by this story (diff is +240/−0); already logged as a Dev delivery finding for future cleanup. No action this story.

### Devil's Advocate

Suppose the driver is broken. Could the `portrait_confirm` skip dead-end chargen? No — the server records the (empty) choice, fires its span, and advances to the confirmation summary, which `AutoChargen` already handles (`phase=confirmation` → `make_chargen_confirm`), then `complete`. Could a malformed frame slip through? The branch keys strictly on `input_type == "pick_portrait"`; any other input_type falls through to the unchanged paths, so the blast radius is exactly one new case. Could the server reject the message for a missing field? `CharacterCreationPayload` makes every field Optional with a default, and the handler reads only `selected_portrait_ref` — a minimal `{phase, selected_portrait_ref:None}` validates. Could this story falsely claim the scenario now runs to completion? No — and this is the important honesty check: the diff does NOT claim the span legs go green. TEA explicitly deviated to a unit test and logged that the live e2e (movement/confrontation/magic spans) cannot pass until **105-2** lands the surface→deep crossing; the verdict here is scoped to "chargen is no longer the blocker," which is exactly what the tests prove. Could a confused future reader think the portrait is actually chosen? The helper docstring and the dispatch comment both state plainly that the driver always skips and why. The one genuine residual risk — that the unit fixture drifts from the server frame — is mitigated by the fixture comment pointing at the exact server emitter; if Epic-66 reshapes the frame, the test must move with it, but that is a maintenance note, not a defect. No new finding surfaces.

### Deviation Audit

- **TEA: "RED scoped to a driver unit test, not a live-server e2e"** → ✓ ACCEPTED by Reviewer: sound. The portrait_confirm clears the precise `portrait_step_shown` gate that causes the downstream `WrongPhaseError`, so the unit assertion fully captures "runs past chargen." A live e2e cannot reach green for the span legs until 105-2 lands the crossing; coupling 105-1's gate to it would be wrong. Verbatim-server-frame fixture is the right wiring guard.
- **Dev: "No deviations from spec"** → ✓ ACCEPTED by Reviewer: implementation matches the tests and SM scope exactly (additive `pick_portrait`→`portrait_confirm` skip).

**Blocking issues:** None (0 Critical, 0 High, 0 Medium).
**Handoff:** To SM (Vizzini) for the finish ceremony.

## Delivery Findings

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Reviewer (review)
- No upstream findings. The one pre-existing item (stale `test_playtest_split.py`) is already captured by Dev; nothing new surfaced.

### Dev (implementation)
- **Improvement** (non-blocking): `scripts/tests/test_playtest_split.py` (story 21-1) has 9 pre-existing failures — stale source-text-grep assertions for symbols long gone from the refactored `playtest.py` (`run_interactive`, `run_scripted`, `run_multiplayer`, `playtest_dashboard`, `def receiver` all count 0 in source). It is NOT in the gated `testpaths=["tests"]` and fails on HEAD independent of this change (my diff only added 26 lines, removed nothing). Affects `scripts/tests/test_playtest_split.py` (delete or rewrite as behavior tests — the exact "No Source-Text Wiring Tests" anti-pattern). Out of scope for 105-1. *Found by Dev during implementation.*

### TEA (test design)
- **Question** (non-blocking): SM-set RED target was "driver advances past chargen for `beneath_sunden_engagement.yaml` with no `WrongPhaseError`" — i.e. a live e2e. I scoped RED to a **pure unit test** on `AutoChargen.respond` (no live server) per the Spec Authority Hierarchy and the project's fixture-driven-behavior wiring guidance (server CLAUDE.md "No Source-Text Wiring Tests"). The unit frame is copied verbatim from the server emitter, so it is the wiring contract. A live-server e2e remains a manual gate (`uv run python3 scripts/playtest.py --scenario scenarios/beneath_sunden_engagement.yaml --span-jsonl ...`) — but it cannot go fully green until **105-2** lands the surface→deep crossing. Dev/Reviewer should run that manual e2e to confirm chargen is cleared, but accept that movement/confrontation/magic spans stay red until 105-2. Logged as a deviation below.
- **Improvement** (non-blocking): the driver needs a `make_chargen_portrait_confirm`-style helper in `scripts/playtest_messages.py` (a `{type: CHARACTER_CREATION, payload: {phase: portrait_confirm, selected_portrait_ref: None}}` message). My tests assert behavior through `AutoChargen.respond` only, leaving Dev free on the helper name. Affects `scripts/playtest.py` (`AutoChargen.respond`) + `scripts/playtest_messages.py`. *Found by TEA during test design.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

1 deviation

- **RED scoped to a driver unit test, not a live-server e2e**
  - Rationale: A live-server e2e is slow, flaky, and — more importantly — cannot reach GREEN for the span legs until Story 105-2 lands the surface→deep crossing; gating 105-1's RED on it would couple this story to 105-2. The server CLAUDE.md "No Source-Text Wiring Tests" guidance prefers fixture-driven behavior tests; the verbatim server frame is the wiring contract between server and driver. The "runs past chargen" behavior is fully captured by the unit assertion (portrait_confirm clears the `portrait_step_shown` gate that causes the downstream `WrongPhaseError`).
  - Severity: minor
  - Forward impact: Dev/Reviewer should still run the manual e2e to confirm chargen clears in live play, but must accept movement/confrontation/magic spans remain red until 105-2.

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No deviations from spec. Implementation matches TEA's tests and the SM scope exactly (route `pick_portrait` → `portrait_confirm` skip, additive).

### TEA (test design)
- **RED scoped to a driver unit test, not a live-server e2e**
  - Spec source: .session/105-1-session.md → SM Assessment, "Test target for RED"
  - Spec text: "A failing assertion that the headless driver advances past chargen for `beneath_sunden_engagement.yaml` (no `WrongPhaseError`) ... it sends the `portrait_confirm`/skip in response to the `pick_portrait` frame."
  - Implementation: Failing tests assert `AutoChargen.respond(pick_portrait_frame)` returns a `phase=portrait_confirm` skip message, using a fixture copied verbatim from the server emitter (`chargen_mixin.py::_render_portrait_scene`). No live server is started in the test suite.
  - Rationale: A live-server e2e is slow, flaky, and — more importantly — cannot reach GREEN for the span legs until Story 105-2 lands the surface→deep crossing; gating 105-1's RED on it would couple this story to 105-2. The server CLAUDE.md "No Source-Text Wiring Tests" guidance prefers fixture-driven behavior tests; the verbatim server frame is the wiring contract between server and driver. The "runs past chargen" behavior is fully captured by the unit assertion (portrait_confirm clears the `portrait_step_shown` gate that causes the downstream `WrongPhaseError`).
  - Severity: minor
  - Forward impact: Dev/Reviewer should still run the manual e2e to confirm chargen clears in live play, but must accept movement/confrontation/magic spans remain red until 105-2.

## Branch Strategy

**Branch Strategy:** trunk-based (branching skipped — work happens on the default branch / main)

The orchestrator repo uses trunk-based development. Work will proceed directly on the main branch without creating a feature branch.