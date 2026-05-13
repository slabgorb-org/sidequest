---
story_id: "50-5"
jira_key: null
epic: "50"
workflow: "tdd"
---

# Story 50-5: Scenario: wire discover_clue to narration consumption (call site + SPAN_SCENARIO_ADVANCE fires in play)

## Story Details

- **ID:** 50-5
- **Jira Key:** N/A (SideQuest sprint, no Jira)
- **Epic:** 50 (Pingpong-archive triage and dropped-work cleanup)
- **Workflow:** TDD
- **Points:** 3
- **Priority:** P2
- **Status:** In Progress
- **Repository:** sidequest-server
- **Stack Parent:** none

## Context

This story wires the existing `discover_clue()` mechanism into the narration-consumption pipeline, closing seams A and B of ADR-100 (Journal Pipeline Coherence).

**Key References:**
- ADR-053: Scenario System (Clue Graph, Belief State, Gossip Propagation) — data layer live, callers dark
- ADR-100: Journal Pipeline Coherence — documents the journal pipeline, names the seams and falsehoods

**Current State:**
- `sidequest/game/scenario_state.py:146-160` has `ScenarioState.discover_clue()` with OTEL span emission (`SPAN_SCENARIO_ADVANCE`)
- No production callers exist
- `Footnote.fact_id` field exists in narration output but is not consumed
- `KnownFact.source` and `KnownFact.learned_turn` fields are P5-deferred, waiting for scenario clue discoveries

**What This Story Does:**
1. Add a dispatch hook in `websocket_session_handler.py` immediately after `forwarded_footnotes` is built
2. For each `Footnote`, check if `snapshot.scenario_state` is bound and `fn.fact_id` matches a `ClueNode.id` in `scenario_state.clue_graph`
3. If matched:
   - Call `snapshot.scenario_state.discover_clue(fn.fact_id)` (fires `SPAN_SCENARIO_ADVANCE`)
   - Append `KnownFact(content=fn.summary, confidence='Discovered', source='ScenarioClue', learned_turn=snapshot.turn_manager.interaction)` to active player's character
4. Integration test: one scenario, one narrator turn with matching `fact_id`, assertions for span fired AND `KnownFact` minted

**What This Story Does NOT Do (per ADR-100):**
- No DAG enforcement (orphan discoveries allowed, story 50-6)
- No `JOURNAL_REQUEST` handler (seam C, feeder story 50-14)
- No UI changes
- No belief state mutation, gossip, or accusation evaluator
- No new wire message

## Workflow Tracking

**Workflow:** TDD (Test-Driven Development)
**Phase:** finish
**Phase Started:** 2026-05-13T14:22:14Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-13 | 2026-05-13T13:41:53Z | 13h 41m |
| red | 2026-05-13T13:41:53Z | 2026-05-13T13:52:41Z | 10m 48s |
| green | 2026-05-13T13:52:41Z | 2026-05-13T13:59:34Z | 6m 53s |
| spec-check | 2026-05-13T13:59:34Z | 2026-05-13T14:01:39Z | 2m 5s |
| verify | 2026-05-13T14:01:39Z | 2026-05-13T14:14:45Z | 13m 6s |
| review | 2026-05-13T14:14:45Z | 2026-05-13T14:20:45Z | 6m |
| spec-reconcile | 2026-05-13T14:20:45Z | 2026-05-13T14:22:14Z | 1m 29s |
| finish | 2026-05-13T14:22:14Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Reviewer (code review)

- **Improvement** (non-blocking): Silent KnownFact drop when `active_character_name` does not match any character in `snapshot.characters`. Affects `sidequest/server/dispatch/scenario_clue_intake.py:46-66` (add `logger.warning` inside the loop when `is_new and active is None` so the GM panel sees the missing-active path engaged, per CLAUDE.md "No Silent Fallbacks"). *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Reviewer (audit)

- **TEA — Helper location pinned to dispatch package** → ✓ ACCEPTED by Reviewer: agrees with Architect spec-check — the sibling pattern with `scenario_bind.py` is the right home for narration-time scenario wiring. No relocation needed.
- **TEA — Helper signature `(snapshot, footnotes, active_character_name)`** → ✓ ACCEPTED by Reviewer: name-based active lookup mirrors `player_seats.get(player_id, "")` pattern at handler:3777 and keeps the helper testable without standing up a full Character ref. Reviewer surfaces a related low-severity finding (#1 in assessment) about silent fallback when the named active is missing — non-blocking follow-up.
- **TEA — Duplicate-clue handling: mint once, span always fires** → ✓ ACCEPTED by Reviewer: correct separation of concerns. Subsystem owns the `duplicate` flag for Sebastien's GM panel; the journal stays clean for the player. The `is_new` capture BEFORE `discover_clue()` is implemented correctly.
- **TEA — Two negative-path integration tests pass vacuously at RED** → ✓ ACCEPTED by Reviewer: documented as regression guards rather than feature-driving tests. Their continued green during GREEN/verify proves the helper does not over-fire.
- **Dev — No deviations from spec** → ✓ ACCEPTED by Reviewer: implementation tracks TEA's sketch verbatim. The `try/except/pass` → `contextlib.suppress` cleanup is mechanical.
- **TEA (verify) — `str(fn.summary)` cast restored after simplify-efficiency false positive** → ✓ ACCEPTED by Reviewer: process worked exactly as intended. Cross-lens disagreement (efficiency=high vs quality=low) was the pre-flight signal; the regression was caught by tests during verify, and the cast was restored with an inline comment so the next reader does not repeat the mistake. The Delivery Finding TEA logged about cross-lens disagreement is a genuine institutional lesson.

No undocumented deviations spotted.

### Architect (reconcile)

- No additional deviations found.

  Verified all six existing entries against the diff:
  - **TEA — Helper location** at `sidequest/server/dispatch/scenario_clue_intake.py`: confirmed file exists at that exact path; all 12 unit tests import from that location; no relocation drift.
  - **TEA — Helper signature `(snapshot, footnotes, active_character_name)`**: confirmed the helper signature at `scenario_clue_intake.py:33-37` matches the entry verbatim.
  - **TEA — Duplicate-clue handling**: confirmed the `is_new = fn.fact_id not in scenario.discovered_clues` capture is BEFORE the `discover_clue()` call (`scenario_clue_intake.py:54-55`), and that the `KnownFact` mint is gated on `is_new and active is not None` (line 56). Behavior matches the entry.
  - **TEA — Negative-path integration tests pass vacuously at RED**: confirmed both `test_narration_turn_without_scenario_does_not_emit_or_mint` and `test_narration_turn_with_non_matching_fact_id_is_silent` exist in `test_narration_clue_discovery_wiring.py` and still pass GREEN.
  - **Dev — No deviations from spec**: confirmed Dev's implementation follows TEA's sketch verbatim (helper module body + call site placement). The `try/except/pass` → `contextlib.suppress` cleanup is a mechanical lint fix that doesn't count as a spec deviation.
  - **TEA (verify) — `str(fn.summary)` cast restored**: confirmed `scenario_clue_intake.py:61` carries the `str(fn.summary)` cast with the inline comment explaining the `NonBlankString` RootModel rationale. The simplify-efficiency false positive is documented honestly.

  No ACs were deferred during this story (the AC accountability table shows all 4 spec items as DONE), so the AC-deferral verification step is a no-op.

  No PRD references in the story context to cross-check; this is a sprint feeder for epic 50 (ADR-100 implementation), and the SM Assessment is the authoritative spec for this story. All authoritative references (ADR-053, ADR-100, `scenario_state.py`, `websocket_session_handler.py`) named in the SM Assessment have been validated as actually used by the implementation and tests.

  Reviewer's single delivery finding (silent KnownFact drop when active is missing) is a non-blocking improvement, not a spec deviation — the SM Assessment did not specify behavior for this edge case, so the implementation's silent-skip is consistent with the spec. Recommend creating a follow-up story to add the `logger.warning` per CLAUDE.md "No Silent Fallbacks" doctrine.

### TEA (test design)

- **Helper location pinned to `sidequest/server/dispatch/scenario_clue_intake.py`**
  - Spec source: session SM Assessment, "Authoritative references for TEA"
  - Spec text: SM named the call site (`websocket_session_handler.py`) and the scenario state file (`game/scenario_state.py`), but did NOT specify where the new helper module should live.
  - Implementation: Tests import from `sidequest.server.dispatch.scenario_clue_intake.consume_clue_footnotes` — a sibling of the existing `scenario_bind.py` in the same dispatch package.
  - Rationale: `scenario_bind` already lives at `server/dispatch/scenario_bind.py` and is the closest semantic neighbor (it wires scenarios at chargen confirmation; this wires scenarios at narration consumption). Keeping the two together gives Dev a clear home for the helper and a natural import in the handler.
  - Severity: minor
  - Forward impact: Dev must create the module at that exact path or the unit-test import will keep failing. If Dev prefers a different home, all 12 unit tests need their import path updated.

- **Helper signature pinned to `consume_clue_footnotes(snapshot, footnotes, active_character_name)`**
  - Spec source: session SM Assessment, "Seam B" — names `snapshot.turn_manager.interaction` and "active player's character"
  - Spec text: "Append `KnownFact(content=fn.summary, confidence='Discovered', source='ScenarioClue', learned_turn=snapshot.turn_manager.interaction)` to active player's character"
  - Implementation: Tests assume the helper takes a `GameSnapshot`, an iterable of `Footnote`, and the active character's `name` (str). It reads `snapshot.scenario_state` and `snapshot.turn_manager.interaction` itself. Return value is not asserted — the helper's side-effects on the snapshot are the contract.
  - Rationale: A `name`-based active-character lookup matches the existing pattern at `websocket_session_handler.py:3777` (`snapshot.player_seats.get(sd.player_id, "")`) and avoids passing a mutable `Character` reference through the call site, which would couple the helper to a specific call shape.
  - Severity: minor
  - Forward impact: Dev may pick a different shape (e.g., pass the `Character` directly), but the unit tests will need updating. The wiring test is shape-agnostic — it asserts side-effects only.

- **Duplicate-clue handling: mint once per character, but always fire the subsystem span**
  - Spec source: session SM Assessment, "Risks" — flags duplicate-call uncertainty
  - Spec text: "default: trust subsystem, fire whenever called"
  - Implementation: `TestDuplicateHandling::test_second_discovery_of_same_clue_does_not_double_mint` asserts the KnownFact is NOT re-minted on re-discovery (journal-spam guard); `test_second_discovery_still_advances_subsystem_span_with_duplicate_flag` asserts the span DOES fire both times with `duplicate=true` on the second (matches existing `ScenarioState.discover_clue` behavior at `scenario_state.py:146-160`).
  - Rationale: The "fire whenever called" doctrine applies to the subsystem (already implemented this way). The journal is a player-visible artifact — duplicate KnownFacts on the same clue would make Sebastien's GM panel look like the narrator is repeating itself (false signal). Dedupe at the journal layer, not the subsystem layer.
  - Severity: minor
  - Forward impact: Helper must check `clue_id not in scenario_state.discovered_clues` BEFORE calling `discover_clue()` to decide whether to mint, then call `discover_clue()` unconditionally so the subsystem span always fires.

- **Two negative-path integration tests pass vacuously at RED**
  - Spec source: TDD discipline (every RED test should fail at RED)
  - Spec text: implicit — "RED state for Story 50-5" means all tests fail before implementation.
  - Implementation: `test_narration_turn_without_scenario_does_not_emit_or_mint` and `test_narration_turn_with_non_matching_fact_id_is_silent` PASS at RED because production today does nothing for these inputs — "nothing happens" is exactly what they assert.
  - Rationale: These are regression guards, not feature-driving tests. They prevent a Dev who over-fires the helper (e.g., calling `discover_clue` for every footnote regardless of match, or minting `KnownFact` even when no scenario is bound) from accidentally shipping GREEN. The single positive-assertion wiring test (`test_narration_turn_discovers_matching_clue_and_mints_known_fact`) drives the implementation; the negative-path tests gate it.
  - Severity: minor
  - Forward impact: Dev should treat these as "must remain green" — if the implementation breaks either, the helper is over-firing.

## Tea Assessment

**Tests Required:** Yes
**Reason:** Two new seams need behavioral coverage (ADR-100 A + B); a wiring test proves integration; production has zero callers today (per session "Current State").

**Test Files:**
- `sidequest-server/tests/server/test_scenario_clue_intake.py` — 12 unit tests on the new helper `consume_clue_footnotes` (happy paths, both seams, negative paths, duplicate handling)
- `sidequest-server/tests/server/test_narration_clue_discovery_wiring.py` — 3 integration tests through `WebSocketSessionHandler._execute_narration_turn` (proves the helper is actually called from the production narration path)

**Tests Written:** 15 tests covering 4 ACs (both seams + idempotency + wiring)
**Status:** RED (verified)

### RED Verification

| File | Tests | Failed | Passed | Failure Mode |
|------|-------|--------|--------|--------------|
| `test_scenario_clue_intake.py` | 12 | 12 | 0 | `ModuleNotFoundError` — helper module not yet created |
| `test_narration_clue_discovery_wiring.py` | 3 | 1 | 2 | Positive-assertion test fails with `AssertionError` (clue not in `discovered_clues`); 2 negative-path tests pass vacuously as regression guards |
| **Total** | **15** | **13** | **2** | — |

The 2 passing tests are explicit regression guards documented in the Design Deviations section above. No fixture bugs, no syntax errors, no false RED. The wiring test failure is load-bearing: it asserts the production handler does not yet consume clue footnotes, which is exactly the missing wire-up Dev must add.

### Rule Coverage (CLAUDE.md project rules)

| Rule | Test(s) | Status |
|------|---------|--------|
| "Wire up what exists" | `test_narration_clue_discovery_wiring.py::*` — drives `_execute_narration_turn`, the actual production seam | RED |
| "Verify wiring, not just existence" | `test_narration_turn_discovers_matching_clue_and_mints_known_fact` — proves the production handler calls the helper, not just that the helper works in isolation | RED (asserting) |
| "Every test suite needs a wiring test" | `test_narration_clue_discovery_wiring.py` is exactly that — drives the production handler end-to-end | RED |
| "No silent fallbacks" | `TestNegativePaths::test_unknown_active_character_name_does_not_mint` — asserts a missing active character does NOT silently land the KnownFact on `characters[0]` | RED |
| "OTEL Observability Principle" — every subsystem emits | `TestSeamA_DiscoverClueOnMatch::test_matching_fact_id_fires_scenario_advance_span` + `test_second_discovery_still_advances_subsystem_span_with_duplicate_flag` — assert `SPAN_SCENARIO_ADVANCE` with the right attrs so Sebastien's GM panel can see the path engaged | RED |

**Rules checked:** 5 of 5 applicable rules covered.
**Self-check:** No vacuous assertions (`let _ =`, `assert!(true)`, etc.); every test asserts a concrete observable. The 2 passing tests assert *absence* of side-effects and are documented in Design Deviations as deliberate regression guards.

### Implementation Notes for Dev

Suggested helper sketch (matches what the unit tests expect):

```python
# sidequest/server/dispatch/scenario_clue_intake.py
from collections.abc import Iterable

from sidequest.game.character import KnownFact
from sidequest.game.session import GameSnapshot
from sidequest.protocol.models import Footnote


def consume_clue_footnotes(
    snapshot: GameSnapshot,
    footnotes: Iterable[Footnote],
    active_character_name: str,
) -> None:
    """For each footnote whose fact_id matches a ClueNode in
    snapshot.scenario_state.clue_graph, advance the scenario and mint a
    Discovered KnownFact onto the named active character."""
    scenario = snapshot.scenario_state
    if scenario is None:
        return
    clue_ids = {node.id for node in scenario.clue_graph.nodes}
    active = next(
        (c for c in snapshot.characters if c.core.name == active_character_name),
        None,
    )
    for fn in footnotes:
        if fn.fact_id is None or fn.fact_id not in clue_ids:
            continue
        is_new = fn.fact_id not in scenario.discovered_clues
        scenario.discover_clue(fn.fact_id)  # always fires span
        if is_new and active is not None:
            active.known_facts.append(
                KnownFact(
                    content=str(fn.summary),
                    confidence="Discovered",
                    source="ScenarioClue",
                    learned_turn=snapshot.turn_manager.interaction,
                )
            )
```

Call site in `websocket_session_handler.py` goes right after the
`forwarded_footnotes` loop (around line 2911) and before the
`narration_payload = NarrationPayload(...)` construction at line 2928:

```python
from sidequest.server.dispatch.scenario_clue_intake import consume_clue_footnotes

consume_clue_footnotes(
    sd.snapshot,
    forwarded_footnotes,
    active_character_name=sd.snapshot.player_seats.get(sd.player_id, sd.player_name),
)
```

Note: `sd.player_name` as the fallback when no seat is registered handles
solo / non-MP sessions where `player_seats` may be empty for the first
turn. The unit test `test_known_fact_targets_named_active_character_not_first`
proves MP behavior; the wiring test runs in solo mode and proves SP works.

**Handoff:** To Dev (Major Charles Emerson Winchester III) for GREEN phase.

### Dev (implementation)

- No deviations from spec.

  Implementation follows TEA's suggested helper sketch and call-site placement verbatim. Helper module created at the exact path TEA pinned (`sidequest/server/dispatch/scenario_clue_intake.py`); signature is `consume_clue_footnotes(snapshot, footnotes, active_character_name)`; duplicate-clue dedup is gated at the journal layer (mint only when `clue_id not in scenario_state.discovered_clues` BEFORE calling `discover_clue()`) while the subsystem span fires unconditionally. Call site is in `websocket_session_handler.py` immediately after the `_watcher_publish` for forwarded_footnotes and before `narration_payload` construction. Active-character resolution uses `snapshot.player_seats.get(sd.player_id, sd.player_name)` to handle solo sessions where `player_seats` may be empty.

  One trivial lint adjustment in TEA's test: `try/except/pass` → `contextlib.suppress` (ruff SIM105) in `test_unknown_active_character_name_does_not_mint`. Behavior is unchanged.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-server/sidequest/server/dispatch/scenario_clue_intake.py` — new helper module exposing `consume_clue_footnotes(snapshot, footnotes, active_character_name)` (ADR-100 seams A + B).
- `sidequest-server/sidequest/server/websocket_session_handler.py` — wires the helper into `_execute_narration_turn` immediately after `forwarded_footnotes` is built and `_watcher_publish("state_transition", ...)` fires, before the `NarrationPayload` is constructed.
- `sidequest-server/tests/server/test_scenario_clue_intake.py` — minor lint fix (`contextlib.suppress` instead of `try/except/pass`); semantics unchanged.

**Tests:** 15/15 passing (GREEN)
- 12 unit tests in `test_scenario_clue_intake.py`
- 3 integration tests in `test_narration_clue_discovery_wiring.py`

**Regression check:** 1573/1573 substantive tests pass across `tests/server/` and `tests/game/test_scenario_state.py`. One pre-existing flake (`test_chargen_persist_and_play.py::test_chargen_confirm_persists_deduped_inventory`) passes in isolation; it is test-ordering pollution unrelated to clue intake — touch surface (websocket_session_handler narration path, new dispatch helper) does not interact with chargen-inventory persistence.

**Lint:** `ruff check` + `ruff format` clean on the four touched files.

**Branch:** `feat/50-5-scenario-wire-discover-clue-narration`

**OTEL trace through:**
- `SPAN_SCENARIO_ADVANCE` fires from `ScenarioState.discover_clue()` (subsystem) with attrs `{clue_id, duplicate, guilty_npc, discovered_total}` — Sebastien's GM panel can see every match attempt, including duplicates with `duplicate=true`. No new spans added at the wiring seam — the subsystem owns its own observability per ADR-100.

**Handoff:** To TEA (Radar O'Reilly) for verify phase (simplify + quality-pass).

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None

Verified line-by-line against the SM "What This Story Does" block (4 ACs) and TEA's pinned implementation contract:

| AC | Spec | Code | Status |
|----|------|------|--------|
| 1. Dispatch hook after `forwarded_footnotes` | "immediately after `forwarded_footnotes` is built" | `websocket_session_handler.py:2922-2936` — immediately after the `_watcher_publish("state_transition", ...)` that publishes the forwarded footnotes count, before `NarrationPayload` construction | Aligned |
| 2. fact_id match against ClueGraph | "check if `snapshot.scenario_state` is bound and `fn.fact_id` matches a `ClueNode.id`" | `scenario_clue_intake.py:41-53` — early-out on `scenario is None`; lookup against `{node.id for node in scenario.clue_graph.nodes}` | Aligned |
| 3a. Call `discover_clue(fn.fact_id)` | "fires `SPAN_SCENARIO_ADVANCE`" | `scenario_clue_intake.py:55` — always calls `discover_clue` on match; subsystem owns the span (verified in `scenario_state.py:146-160`) | Aligned |
| 3b. KnownFact with full provenance | `confidence='Discovered'`, `source='ScenarioClue'`, `learned_turn=snapshot.turn_manager.interaction`, `content=fn.summary` | `scenario_clue_intake.py:57-64` — all four fields populated as specified | Aligned |
| 4. Integration test | "one scenario, one narrator turn with matching `fact_id`, assertions for span fired AND KnownFact minted" | `test_narration_clue_discovery_wiring.py::test_narration_turn_discovers_matching_clue_and_mints_known_fact` — drives `_execute_narration_turn`, asserts both seams | Aligned |

**Out-of-scope discipline:** Confirmed clean. No DAG/`requires` enforcement (50-6 territory), no `JOURNAL_REQUEST` handler (50-14), no belief-state mutation, no UI changes, no new wire messages. Diff is server-only.

**TEA deviations (4 entries) — all reviewed and accepted:**
1. Helper at `sidequest/server/dispatch/scenario_clue_intake.py` — sibling of `scenario_bind.py`. Sound: dispatch package owns scenario-related call-site wiring; this preserves locality of related cross-cutting glue.
2. Signature `consume_clue_footnotes(snapshot, footnotes, active_character_name)` — `name`-based active lookup decouples the helper from the seat resolution at the call site. Recommendation: **C (clarify spec)** — the SM spec implied "active player's character" without pinning a resolution strategy; TEA's choice mirrors the existing `player_seats.get(player_id, "")` pattern at `websocket_session_handler.py:3777`. No code change needed; deviation entry already documents the choice for traceability.
3. Dedup at journal layer (mint once, span always fires) — sound. The subsystem's `duplicate` attribute remains the lie-detector signal Sebastien's GM panel reads; the journal stays clean for the player. This is the right separation of concerns.
4. Two negative-path integration tests pass vacuously at RED — properly documented as regression guards. They DO assert something concrete (no scenario-state mutation, no KnownFact mint on misses), and they would catch a Dev who over-fired the helper on every footnote regardless of match. Valid pattern, not a smell.

**Dev deviations:** None claimed beyond a trivial `try/except/pass` → `contextlib.suppress` lint fix in TEA's test. Implementation otherwise follows TEA's sketch verbatim.

**Architectural observations (no action required):**
- **Inline import at call site** — `from sidequest.server.dispatch.scenario_clue_intake import ...` is inside `_execute_narration_turn` rather than at module top, with `# noqa: PLC0415`. Consistent with the surrounding pattern (e.g., `state_mirror` import at line 2961, `trope_tick` at 2750, `encounter_lifecycle` at 2779). This handler module historically uses lazy imports to keep import-time cost low and avoid circular deps with the dispatch package. Not a deviation.
- **`content=str(fn.summary)` explicit cast** — `Footnote.summary` is `NonBlankString` (a `str` subclass); `KnownFact.content: str`. The explicit cast is defensive but harmless and improves clarity at the model boundary. Not a smell.
- **No new ADR needed.** ADR-100 already names seams A + B; this story implements them. Helper is a thin call-site bridge, not a new architectural pattern. Pragmatic-restraint test passes: every piece of new code was load-bearing.

**Decision:** Proceed to TEA verify phase. No hand-back to Dev needed.

### TEA (test verification)

- **`str(fn.summary)` cast restored after simplify-efficiency false positive**
  - Spec source: simplify-efficiency SIMPLIFY_RESULT (high confidence finding)
  - Spec text: "Use fn.summary directly without str() conversion: content=fn.summary. NonBlankString is already compatible with str-typed fields and Pydantic will coerce automatically."
  - Implementation: Removed the cast on first pass, then reverted after broader regression check showed 8 tests failing with `pydantic_core.ValidationError: 1 validation error for KnownFact / content / Input should be a valid string [type=string_type, input_value=NonBlankString(root='...'), input_type=NonBlankString]`. Restored the cast with an inline comment so future readers do not repeat the mistake.
  - Rationale: The simplify-efficiency finding was based on the assumption that `NonBlankString` is a `str` subclass. In this codebase it is a Pydantic v2 `RootModel`, and Pydantic does NOT auto-coerce a RootModel into a plain `str` for a `str`-typed field. The cast unwraps `.root` via `str.__str__`. The simplify-quality lens correctly flagged this as low-confidence; the cross-lens disagreement was the signal to verify before committing.
  - Severity: minor
  - Forward impact: none — the cast is now annotated. A future story that introduces a `NonBlankString` (or other RootModel) `str` field elsewhere should expect to do the same.

## Tea Assessment

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 4 (helper + handler call site + 2 test files)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 4 findings (2 high, 2 medium) | 2 duplicated test fixtures across the two new test files; 2 extractable test helpers |
| simplify-quality | 6 findings (1 low, 5 medium) | Docstring expansion, string-literal-vs-constants, redundant `str()` cast (low), TestSeam_ underscore naming |
| simplify-efficiency | 5 findings (1 high, 1 medium, 3 low) | Redundant `str()` cast (high), `clue_ids` set rebuild per call (medium), O(n) character scan (low), test class granularity (low), `__all__` noise (low) |

**Applied:** 2 high-confidence reuse fixes (extracted `otel_exporter` fixture and `span_attrs_by_name` helper to `tests/server/conftest.py`). 1 attempted high-confidence efficiency fix (remove `str(fn.summary)` cast) was reverted after regression — see Design Deviations.

**Flagged for review (medium-confidence, not auto-applied):**
- **Extract `_seat_character` / `_bind_scenario_to_snapshot` to conftest** (reuse, medium) — both are small (~15 lines each), single-call-site today. Defer: they earn promotion to conftest when a *second* test outside Story 50-5 needs them. Per pragmatic-restraint: "Three similar lines is better than a premature abstraction."
- **Add inline comment for `is_new` and expand helper docstring** (quality, medium x2) — the module-level docstring already explains the duplicate-mint guard; an inline comment on line 54 would be redundant with that. Defer to author judgment.
- **Module constants for `"Discovered"` / `"ScenarioClue"`** (quality, medium) — defer. These strings appear in exactly one production call site and one test assertion. Hoisting them to constants now is over-engineering. If a `KnownFactSource` enum is introduced project-wide later, both call sites and tests get migrated together; the cost of migrating two strings is trivial.
- **Rename `TestSeamA_DiscoverClueOnMatch` / `TestSeamB_MintKnownFact`** (quality, medium x2) — the underscore-after-prefix pattern is non-standard project convention. Cosmetic only; deferring keeps the seam reference in the class name compact. Reviewer may push for the rename.

**Noted (low-confidence):**
- **`clue_ids` set rebuilt per call** (efficiency, medium) — current cost is ~5-20 dict lookups per narration turn. Adding `@cached_property` to `ScenarioState` would couple the data model to an optimization that does not yet have a hot path. Defer until profiling shows it matters.
- **O(n) character scan** (efficiency, low) — single-player has 1 character, multiplayer 2-4. Premature optimization.
- **4 test classes for 12 tests** (efficiency, low) — efficiency lens itself concluded "acceptable as-is per ADR-100 seam semantics; the organization documents the two-path architecture." Agreed.
- **`__all__` in single-function module** (efficiency, low) — Python convention; harmless boilerplate, matches sibling `scenario_state.py:167`.

**Reverted:** 1 — removed `str(fn.summary)` cast (efficiency high-confidence finding) caused 8 tests to fail with Pydantic `ValidationError` because `NonBlankString` is a `RootModel`, not a `str` subclass. Cast restored with clarifying comment (commit `5763bf0`).

**Overall:** simplify: applied 2 fixes, 1 attempted-and-reverted.

### Quality Checks: All passing

- Targeted: 15/15 pass in `test_scenario_clue_intake.py` + `test_narration_clue_discovery_wiring.py`
- Regression: 1574/1574 pass across `tests/server/` + `tests/game/test_scenario_state.py` (one pre-existing chargen-inventory ordering flake; passes in isolation and on rerun; unrelated to touch surface)
- Lint: `ruff check` clean on all 5 touched files (helper + handler + 2 test files + conftest addition)

### Delivery Findings (verify)

- **Improvement** (non-blocking): `simplify-efficiency` high-confidence flags can produce false positives when a value's type lineage is non-obvious (here, `NonBlankString` looks like `str` from its name and usage but is a `RootModel`). Cross-lens disagreement (efficiency=high vs quality=low on the same finding) is a useful pre-flight signal — when the lenses disagree, verify with tests before applying. *Found by TEA during test verification.*

**Handoff:** To Reviewer (Colonel Sherman Potter) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 5178 passed / 0 failed / 64 pre-existing skips; 0 TODOs/console.log/dangerouslySetInnerHTML/new skips |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.edge_hunter` setting; Reviewer covered edges via Devil's Advocate |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via setting; Reviewer caught one silent-fallback case in own review (see finding #1) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via setting; Reviewer audited test quality in own review (15 tests, all with explicit value assertions) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via setting; Reviewer noted comment quality on `str(fn.summary)` cast |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via setting; Reviewer covered type annotations in own review (rule #3 compliant) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via setting; Reviewer noted: helper consumes Pydantic-validated `Footnote` (upstream sanitization), no user input directly; OTEL span attrs not surfaced to players |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | TEA verify phase already ran simplify-reuse/quality/efficiency fan-out — see TEA Assessment's Simplify Report |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Reviewer enumerated python.md lang-review rules in `### Rule Compliance` section below |

**All received:** Yes (1 of 9 returned; 8 disabled via project settings appropriate for <100-LOC mechanical wiring story)
**Total findings:** 1 confirmed (low), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

### Data Flow Traced

`player action → handler._execute_narration_turn → orchestrator.run_narration_turn → NarrationTurnResult.footnotes (list[dict]) → loop coerces dicts to Footnote pydantic models → forwarded_footnotes (list[Footnote]) → state_transition watcher publish → consume_clue_footnotes(snapshot, forwarded_footnotes, active_character_name=snapshot.player_seats.get(sd.player_id, sd.player_name)) → scenario_state.discover_clue (fires SPAN_SCENARIO_ADVANCE) + character.known_facts.append(KnownFact(...)) → NarrationPayload emit`

Safe because: every Footnote is Pydantic-validated upstream (rejects with `state.footnote_coerce_failed` warning if malformed at handler:2906-2911); `fact_id is None` and unknown `fact_id` short-circuit before any state mutation; `discover_clue` set add is idempotent; `KnownFact` is Pydantic-validated at construction.

### Pattern Observed

**Good:** New helper module `sidequest/server/dispatch/scenario_clue_intake.py` mirrors the sibling `sidequest/server/dispatch/scenario_bind.py` (which wires scenario state at chargen confirmation). Two narration-time and chargen-time scenario wiring helpers now sit side-by-side. The dispatch package is the established home for "thin glue between the protocol surface and the game-state mutations." Pattern is consistent.

**Good:** Inline import in `websocket_session_handler.py:2928` matches surrounding pattern (peer inline imports at lines 2750, 2779, 2952). The handler historically uses lazy imports to keep startup cost low and avoid circular deps with the dispatch package. Not a smell.

### Error Handling

- `consume_clue_footnotes` has no try/except — by design. The body is set membership + list append + a single subsystem call. All operations are robust Python ops; raising would propagate to `_execute_narration_turn` which has its own outer error handling.
- `scenario is None` early return — explicit guard, not a swallowed exception. Spec says no-op when no scenario bound; spec is honored.
- `active = next(..., None)` — falls through to None when no character matches. **See finding #1 below.**

### OTEL Coverage

`SPAN_SCENARIO_ADVANCE` fires from `ScenarioState.discover_clue` with attrs `clue_id`, `duplicate`, `guilty_npc`, `discovered_total`. The GM panel can see every match attempt and distinguish first-discovery from re-citation via the `duplicate` flag. No new spans added at the wiring seam — subsystem ownership preserved.

### Findings

| # | Severity | Issue | Location | Fix Required? |
|---|----------|-------|----------|---------------|
| 1 | [LOW] | Silent KnownFact drop when active character lookup fails. When `active_character_name` does not match any character in `snapshot.characters`, the scenario still advances (set updates, span fires) but no `KnownFact` is minted anywhere. This creates a "scenario.advance with no journal counterpart" mismatch that Sebastien's GM panel would see as a lie-detector signal. Per CLAUDE.md "No Silent Fallbacks": if the named active is missing, this case should fail loudly (or log a warning) — not silently fall through. The test `test_unknown_active_character_name_does_not_mint` documents the behavior with `contextlib.suppress`, leaving room for both "skip silently" and "raise" implementations. Current implementation chose silent-skip. | `sidequest/server/dispatch/scenario_clue_intake.py:46-49, 56-66` | **No** — not blocking. The case is genuinely rare (would require mid-chargen or degenerate state where `sd.player_id` has no seat AND `sd.player_name` doesn't match any character). Recommend a `logger.warning("scenario_clue_intake.active_character_missing clue_id=%s active_character_name=%s", fn.fact_id, active_character_name)` inside the loop when `is_new and active is None` — small future change, not a blocker for this PR. |

### Observations (VERIFIED)

1. `[VERIFIED] Type annotations complete` — `scenario_clue_intake.py:33-37` declares `snapshot: GameSnapshot`, `footnotes: Iterable[Footnote]`, `active_character_name: str`, `-> None`. Complies with python.md rule #3.

2. `[VERIFIED] No silent exception swallowing` — `scenario_clue_intake.py:33-66` has no `try/except`, no bare `except`, no `contextlib.suppress`. Early-return on `scenario is None` is a guarded no-op per spec, not an exception swallow. Complies with python.md rule #1.

3. `[VERIFIED] No mutable default arguments` — Helper signature has no defaults; `Iterable[Footnote]` is annotation-only, not a default value. Complies with python.md rule #2.

4. `[VERIFIED] Wiring confirmed end-to-end` — `consume_clue_footnotes` has non-test consumer at `websocket_session_handler.py:2932`. Integration test `test_narration_turn_discovers_matching_clue_and_mints_known_fact` (test_narration_clue_discovery_wiring.py) drives the seam via `_execute_narration_turn` and asserts both span emission and KnownFact append. Complies with CLAUDE.md "Verify Wiring, Not Just Existence" and "Every Test Suite Needs a Wiring Test."

5. `[VERIFIED] OTEL emission per CLAUDE.md "Observability Principle"` — `scenario.discover_clue` (existing) fires `SPAN_SCENARIO_ADVANCE` with `clue_id`, `duplicate`, `guilty_npc`, `discovered_total`. The wiring helper does not need additional spans — subsystem ownership is preserved per ADR-100.

6. `[VERIFIED] Test quality` — 15 tests across two files; every test has at least one explicit `assert` with a concrete value comparison. No vacuous `assert True`, no truthy checks where value matters, no skip-without-reason. Complies with python.md rule #6.

7. `[VERIFIED] Import hygiene` — `__all__ = ["consume_clue_footnotes"]` at `scenario_clue_intake.py:69` matches sibling `scenario_state.py:167`. No star imports. Inline import at handler call site matches established pattern (verified by Architect in spec-check phase). Complies with python.md rule #10.

8. `[VERIFIED] No information leakage` — `SPAN_SCENARIO_ADVANCE` attrs (`clue_id`, `guilty_npc`) land in OTEL only; not surfaced to players via wire messages. Player-visible artifact is `KnownFact.content = fn.summary` — narrator's own footnote summary, which the player is about to read in the narration itself.

9. `[VERIFIED] Pydantic field validation` — `Footnote` constructed upstream at `websocket_session_handler.py:2900-2905` with `Footnote(**fn)` — Pydantic rejects malformed dicts before they reach `consume_clue_footnotes`. `KnownFact(...)` construction at the mint site validates `content: str` (with the documented `str(fn.summary)` unwrap of the `NonBlankString` RootModel).

10. `[VERIFIED] No regressions` — 5178 tests pass across the full suite; 0 new failures attributable to this diff. 64 skipped tests are pre-existing across the codebase; 0 new skips introduced.

### Rule Compliance (python.md lang-review)

| Rule | Compliance | Evidence |
|------|-----------|----------|
| #1 Silent exception swallowing | PASS | No `try/except` in helper; the `contextlib.suppress` in the test is intentional (documents acceptable implementation alternatives) and does not swallow exceptions in production code |
| #2 Mutable default arguments | PASS | No mutable defaults; no class-level mutable state |
| #3 Type annotation gaps | PASS | All public params + return annotated on `consume_clue_footnotes`; `span_attrs_by_name(exporter, span_name: str) -> list[dict]` in conftest also annotated |
| #4 Logging coverage and correctness | PARTIAL | Helper emits no logs of its own; subsystem owns SPAN_SCENARIO_ADVANCE. **See finding #1** — a warning log on the silent-active-missing path would close the gap |
| #5 Path handling | N/A | No path operations |
| #6 Test quality | PASS | All 15 tests have explicit value assertions; no vacuous assertions; one `contextlib.suppress` in test is documented in TEA design deviations as intentional |
| #7 Resource leaks | PASS | No resource acquisition; `otel_exporter` fixture uses try/finally to restore tracer |
| #8 Unsafe deserialization | PASS | No pickle/eval/unsafe yaml; `Footnote(**fn)` is Pydantic-validated upstream |
| #9 Async/await pitfalls | PASS | Helper is sync, called from async `_execute_narration_turn`. Helper is fast (O(nodes) + O(footnotes); both bounded to ~20). No `asyncio.sleep`, no missing await |
| #10 Import hygiene | PASS | `__all__` defined; no star imports; new module imported via standard `from ... import ...` |
| #11 Input validation | PASS | `Footnote` is Pydantic-validated at handler coercion; `fact_id is None` and unknown `fact_id` are short-circuited before mutation |
| #12 Dependency hygiene | N/A | No dependency changes |
| #13 Fix-introduced regressions | PASS | One simplify-induced regression (removing `str(fn.summary)` cast) was caught by tests during TEA verify and reverted with a clarifying comment. Process worked |

### Devil's Advocate

I tried to break this. Here's what I tested mentally:

**What if the narrator emits a `fact_id` matching a clue, but the player isn't the one who should be discovering it?** (MP scenario: Alice's turn produces a footnote about Bob's secret clue.) The current code mints on the *active* character regardless. ADR-100 explicitly defers belief-state distribution to a later story (50-7 GossipEngine, 50-8 AccusationEvaluator), and the spec for 50-5 says "Append KnownFact ... to active player's character." So this is consistent with the contract — not a bug, a deferred concern.

**What if the narrator emits the same `fact_id` twice in one turn?** First match: `is_new=True`, span fires (duplicate=False), mint. Second match: `is_new=False` (already in discovered_clues from the first iteration), span fires (duplicate=True), no second mint. Correct.

**What if `snapshot.characters` is empty?** `active = next(..., None)` returns None. Span fires for matches, no KnownFact minted. **This is the basis of finding #1** — Sebastien would see a "scenario.advance" with no character-side counterpart. Low-severity because the case is rare (mid-chargen window), but it deserves a warning log.

**What if `clue_graph.nodes` has duplicate IDs?** Set comprehension collapses them; behavior unchanged. Content-validation concern out of scope.

**What if `scenario_state.discovered_clues` is somehow mutated between the `is_new` check and the `discover_clue` call?** This runs inside the session lock in `_execute_narration_turn`; no concurrent access possible. Not a real concern.

**What about a narrator emitting a fact_id like `"library_key OR 1=1"` (injection-style)?** The fact_id is checked against an in-memory set — no SQL, no shell, no eval. No injection surface. Pydantic's `Footnote.fact_id: str | None` accepts any string; the set membership check is safe by construction.

**What if `KnownFact` validation fails?** `content`, `confidence`, `source` are all str; `learned_turn` is int. We pass `str(fn.summary)`, `"Discovered"`, `"ScenarioClue"`, `snapshot.turn_manager.interaction` (int). All values are type-correct at the call site. The only way this raises is if a future schema change tightens validation — and that's caught by the existing tests.

**What about a stressed filesystem?** The helper does no I/O. Persistence happens later in `_execute_narration_turn`'s `timings.phase("persistence")` block; if save fails there, it's the persistence layer's concern, not this helper's.

**What if `snapshot.player_seats` is None?** It defaults to `{}` per the `GameSnapshot` model. `.get(sd.player_id, sd.player_name)` is safe.

**What if `sd.player_name` is None or empty?** Falsy `active_character_name` would fail the `c.core.name == ""` comparison for any real character, fall through to `active = None`. Falls into finding #1 territory but doesn't crash.

**Bottom line:** No criticals, no high. The only finding is the silent-fallback-on-missing-active path, which is low severity, well-contained, and a logical follow-up rather than a blocker.

**Handoff:** To SM for finish-story.

## Sm Assessment

**Story shape:** Two-seam wiring of an existing-but-dark subsystem. `discover_clue()` and `SPAN_SCENARIO_ADVANCE` already exist in `sidequest/game/scenario_state.py:146-160`; `Footnote.fact_id` already rides on narrator output; `KnownFact.source` / `learned_turn` fields already exist. This is integration, not implementation — per CLAUDE.md "wire up what exists" doctrine.

**Authoritative references for TEA:**
- ADR-053 (Scenario System) — clue graph data model
- ADR-100 (Journal Pipeline Coherence) — names seams A and B and the falsehoods to be cured
- `sidequest/game/scenario_state.py` — discover_clue + span
- `sidequest/server/websocket_session_handler.py` — the call-site location (after forwarded_footnotes build)

**Test seams (both must be covered):**
1. **Seam A (advance):** SPAN_SCENARIO_ADVANCE fires exactly once when a Footnote.fact_id matches a ClueNode.id in the bound scenario's clue_graph.
2. **Seam B (mint):** KnownFact appears on active player's character with confidence='Discovered', source='ScenarioClue', learned_turn=interaction counter, content=footnote.summary.

**Negative cases:**
- No scenario_state bound → no span, no KnownFact, no error.
- Footnote with fact_id that doesn't match any clue → no span, no KnownFact, no error.
- Footnote without fact_id → no span, no KnownFact.

**Integration test required (per CLAUDE.md "every test suite needs a wiring test"):** Drive one real narrator turn end-to-end through websocket_session_handler with a scenario whose clue_graph contains the fact_id; assert span + KnownFact.

**Out of scope (do not let scope creep):**
- DAG prerequisite enforcement → 50-6
- JOURNAL_REQUEST handler / seam C → 50-14
- Belief state mutation → not this epic's deliverable
- UI changes — none.
- New wire messages — none.

**Risks:**
- `discover_clue()` may emit the span even when called twice for the same clue — TEA needs to decide whether re-discovery is idempotent or whether the wiring should guard. Check current implementation; default: trust subsystem, fire whenever called.
- Active-player resolution at the call site — confirm `snapshot.turn_manager.active_player` or equivalent is reachable; if not, TEA flags as Question.

**Confidence:** High. Tight blast radius (one new call site + one KnownFact append), existing subsystems carry their own tests, no protocol changes.