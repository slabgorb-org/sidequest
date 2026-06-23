# Story 158-3: Block narrator apply-path opponent-HP writes when no confrontation is seated

## Title

[NARRATOR-HP-WRITE-GUARD] Block narrator apply-path opponent-HP writes (damage application) when there is NO confrontation currently seated in the game state. An unbacked mechanical write — prose damage without an engine encounter — must be rejected or logged loudly so the LLM cannot silently "apply" damage with zero mechanical backing.

## Metadata

- **Story ID:** 158-3
- **Type:** bug
- **Points:** 3
- **Priority:** p1
- **Workflow:** tdd
- **Repo:** server
- **Epic:** 158 — Playtest sweep follow-ups (open findings from the 2026-06-22 full-stack /sq-playtest sweep)

## Problem Statement

**OTEL Lie-Detector Principle (CLAUDE.md § Development Principles):**

> Every backend fix that touches a subsystem MUST add OTEL watcher events so the GM panel can verify the fix is working. Claude is excellent at "winging it" — writing convincing narration with zero mechanical backing. The only way to catch this is OTEL logging on every subsystem decision.
>
> **The GM panel is the lie detector. If a subsystem isn't emitting OTEL spans, you can't tell whether it's engaged or whether Claude is just improvising.**

**Finding (2026-06-22 beneath_sunden playtest):**

During a no-encounter narrative beat (PC exploring, no seated confrontation), the narrator narrated damage to an enemy that exists only in prose: *"Your blade cuts deep; he gasps and stumbles back, bleeding."* The narration tool's apply-path accepted and processed opponent-HP writes (`opponent_state.hp` decrements) **even though there is no opponent seated in the game state.**

**Why it matters:**
1. **Mechanical integrity (ADR-114, ADR-116, ADR-139):** A seated confrontation is the prerequisite for opponent HP to be legally modified. Opponent HP outside a confrontation is undefined — there is no opponent.
2. **Product surface:** The GM panel (the lie detector) cannot verify a mechanical write when the underlying confrontation is missing. A changed field (opponent HP decremented) combined with zero OTEL dispatch/seater/mechanical spans = narrator improvisation, not real mechanics.
3. **Player trust:** Keith (the primary audience) has 40 years of tightly-run tabletop experience. A game that writes HP with no backing is exactly the kind of "nice prose, broken engine" failure the system was built to prevent.

**Concrete manifestation:**
- **apply-path contract (narration_tool.py):** accepts opponent-state writes without checking if a confrontation is seated
- **No guard:** if `in_combat=False` or `confrontation=None`, the apply-path still processes the write
- **No OTEL:** no span emitted when a write is attempted/rejected, so the GM panel cannot see the decision

## Root Cause Direction

**The apply-path in narration_tool.py accepts opponent-state mutations without validating that a confrontation is seated.**

The narration tool contract allows the narrator to report damage via the apply-path: e.g., setting `opponent_state.hp` to a lower value. The current code does not validate that:
1. A confrontation is seated (`game_state.in_combat == True` or `game_state.confrontation is not None`)
2. An opponent exists in the seater's projection

**Fix surface:**
- Add a guard in the apply-path handler that rejects opponent-state writes when `in_combat=False` or `confrontation is None`.
- Emit an OTEL warning span when a write is rejected (so the GM panel sees the decision).
- Log a distinct OTEL event when an opponent-state write is ACCEPTED (so we can verify the path is live during combat).

## Acceptance Criteria

1. **Guard blocks unbacked writes.** When the narrator attempts to write opponent-state fields (e.g., `opponent_state.hp`, `opponent_state.status`) via the apply-path and NO confrontation is seated (`in_combat == False` or `confrontation is None`), the write is REJECTED. The narration tool returns a safe no-op or error signal (TBD with Dev: silent skip vs. tool error).

2. **OTEL observability for all opponent-state decisions.** When an opponent-state write is attempted:
   - If confrontation is seated and write is ACCEPTED: emit an OTEL info/debug span with the field name, old value, new value, and opponent_id (so the GM panel can verify mechanical writes during combat).
   - If confrontation is NOT seated and write is REJECTED: emit an OTEL warning span indicating the rejection reason (no_confrontation, no_opponent, etc.) and the attempted write spec (field, value).
   - Both spans must fire so the GM panel can see the full decision tree.

3. **No regression on legal opponent-state writes.** During an active confrontation, opponent-state writes (e.g., damage application) continue to work end-to-end. Verified via integration test: a combat turn with narrator damage application now emits acceptance spans and correctly updates opponent HP.

4. **Repro-level end-to-end test.** A test reachable from real play: a no-encounter narrative beat where the narrator attempts to apply opponent damage, followed by a combat beat where the narrator applies damage with a confrontation seated. Test asserts: (a) the no-encounter write is rejected and produces a warning OTEL span, (b) the combat write is accepted and produces an info OTEL span, (c) opponent HP is unchanged after the no-encounter beat, and (d) opponent HP is updated after the combat beat.

## Technical Approach

**High-level fix (for Dev):**

1. **Identify the opponent-state apply-path** in `sidequest/server/agents/tools/narration_tool.py` (the handler that processes narrator updates to game state via the apply dictionary).

2. **Add a guard before processing opponent-state writes:**
   ```python
   # Pseudocode
   if field_path.startswith("opponent_state."):
       if not (game_state.in_combat and game_state.confrontation):
           # Reject: log a warning OTEL span and skip the write
           emit_otel_warning("opponent_state_write_without_confrontation", {
               "field": field_path,
               "attempted_value": new_value,
               "reason": "no_confrontation_seated",
               "in_combat": game_state.in_combat,
               "confrontation_exists": game_state.confrontation is not None,
           })
           return  # or raise an error; coordinate with Dev
   ```

3. **Add OTEL spans for accepted writes:**
   ```python
   if field_path.startswith("opponent_state."):
       if game_state.in_combat and game_state.confrontation:
           # Accepted write
           emit_otel_info("opponent_state_write_accepted", {
               "field": field_path,
               "old_value": old_value,
               "new_value": new_value,
               "opponent_id": game_state.confrontation.opponent_id,
           })
   ```

4. **Test the guard** with an integration test (or unit test + wiring test) that:
   - Runs a no-encounter narrative beat with attempted opponent-state writes → verifies rejection + warning OTEL
   - Runs a combat beat with narrator damage → verifies acceptance + info OTEL

**Key code areas:**
- `sidequest/server/agents/tools/narration_tool.py` — narration tool contract, apply-path handler
- `sidequest/game/session.py` — GameSnapshot: `in_combat`, `confrontation` fields
- `sidequest/game/confrontation.py` — Confrontation model
- `sidequest/telemetry/spans/narration.py` or a new `sidequest/telemetry/spans/opponent_state.py` — OTEL span definitions
- **Tests:** `tests/integration/test_narration_tool_*.py` or a new `tests/integration/test_opponent_state_guard.py`

**Related ADRs:**
- **ADR-114 (Ablative HP Substrate):** opponent HP is part of the ablative layer; reconciles with game-state lethality tracking
- **ADR-116 (A Confrontation Requires an Other):** a confrontation is the authority for co-located opponent state
- **ADR-139 (Confrontation Integrity Invariants):** opponent HP durability is a confrontation invariant; writes must be backed by a seated confrontation
- **ADR-123 (Mechanical-Engagement Pipeline):** narration tool is downstream of confrontation dispatch; no confrontation → no valid opponent-state write

## Scope

**In scope:**
- Block/reject opponent-state field writes when no confrontation is seated.
- Emit OTEL warning spans for rejected writes (no confrontation signal).
- Emit OTEL info spans for accepted writes (mechanical write signal).
- Integration test: no-encounter attempted write (rejection + span), combat write (acceptance + span).

**Out of scope:**
- Narration tool design changes (adding new fields, changing the apply contract).
- Opponent HP fabrication *detection* (that's a separate GM-panel finding; this story is about *blocking* unbacked writes).
- Narrator behavior or LLM prompting (the block is a mechanical gate, not a prompt change).
- Other unbacked writes (player-state, location, npc-state, etc.) — scope is opponent-state only.

## Story Scope Clarification

This is a **single, tightly-scoped guard:** reject opponent-state writes when no confrontation is seated, and emit OTEL so the GM panel can verify the decision. Do not expand to other narration-tool fields, narrator behavior tuning, or new state-validation subsystems; those are separate concerns.
