# Story Context: 158-28

## Story Title
WWN combat is narration-only — confrontation never seats, narrator confabulates kills with zero mechanical backing (IntentRouter combat-verb routing + opponent seater)

## Story Type
Bug

## Story Points
5

## Priority
P1

## Workflow
tdd

## Repository
server

## Story Description
Playtest finding (pingpong 2026-06-24 beneath_sunden + 2026-06-25 barsoom, WWN, @aed2d812). Post-#1072 the crash is gone but combat is NARRATION-ONLY: attack → narrator narrates a KILL while ground truth shows encounter=null, total_beats_fired=0, creature untouched, no Other seated; plus weapon confab (narrates 'mace' vs the PC long-blade kit). #1072 scoped to don't-crash, not do-seat.

## Acceptance Criteria

1. **After an attack, encounter != null**: A confrontation MUST be created/seated when the PC attacks a creature in a WWN world. Ground truth: `encounter` object exists in the game state.

2. **Beats fire mechanically**: After combat is seated, narrator writes beats to `total_beats_fired` counter. Ground truth: `total_beats_fired > 0` post-narration.

3. **Creature HP changes**: The attacked creature's HP MUST decrease after a successful attack. Ground truth: compare creature HP before and after the attack turn — delta must be non-zero.

4. **Weapon sourced from inventory**: Attack narration uses a weapon from the PC's actual inventory, not confabulated. Ground truth: extract the weapon name from narration and verify it exists in `pc.inventory`.

5. **max_turns exhaustion degrades loudly (ADR-006)**: When the narrator breaches the `max_turns` limit, the system MUST log a clear error and disconnect gracefully instead of crashing/wedging. Ground truth: session logs show explicit "max_turns exceeded" message; no silent wedges.

## Technical Approach

**Root Cause**: The WWN combat dispatch path (ADR-143) does not SEAT a confrontation. The IntentRouter classifies combat verbs correctly (158-2 done), but the opponent-seater does not instantiate a Confrontation object.

**Fix Strategy** (ADR-143 doctrine):
1. **Opponent Seater**: Wire the `opponent_seater` subsystem to SEAT a Confrontation when a combat intent is routed. This must:
   - Instantiate a Confrontation with the routed creature as the opponent
   - Validate the creature is a mechanically-capable Other (ADR-116 / ADR-139)
   - Bind the seated Confrontation to the game state so narrator engagement fires
   
2. **Ruleset Ownership**: Once seated, the WN (Without Number) ruleset MUST own resolution (ADR-143):
   - Combat beats must draw from the WN ruleset (not the native dial-threshold system)
   - HP deltas must come from WN combat mechanics, not freeform narrator writes
   - The dispatcher must gate the native combat tools when WN is active (like #1072 did for tool-withhold, but extended to all dispatches)

3. **Narration Grounding**:
   - Weapon MUST be extracted from PC inventory before narration, passed to the narrator as a constraint
   - Narrator sees the actual weapon name, not a free choice
   - Creature HP is pre-authorized by the ruleset, not a narrator write

4. **Graceful Degradation (ADR-006)**:
   - Wrap narrator calls with a max_turns budget check
   - If narrator breaches max_turns, emit a clear OTEL span `narrator.max_turns_exceeded`, log the reason (e.g., "max_turns=8, step 7 failed to complete"), and disconnect gracefully
   - Do NOT crash or wedge; emit the event and let the session teardown proceed

## Related ADRs
- **ADR-143**: WWN Binding Replaces the Native Combat Engine — we bind the ruleset to stop balancing, not to balance against it (LOAD-BEARING)
- **ADR-116**: Confrontation Integrity Invariants — Mechanically-Capable Other, Dispatch Applicability Gate
- **ADR-139**: Confrontation Integrity Invariants — Win-Condition Liveness, Seated-Actor HP Durability
- **ADR-113**: Intent Router — Mechanical-Engagement Spine (routing is already working; seating is the gap)
- **ADR-123**: Mechanical-Engagement Pipeline — Confidence-Gated Topological Dispatch Bank
- **ADR-006**: Graceful Degradation

## Lie-Detector OTEL Assertions (Required for Test)

1. `dispatch_engagement.confrontation.seated` — MUST fire when combat lands
2. `dispatch_engagement.confrontation.beats_fired` — MUST fire per beat with `own_delta` and `opponent_delta` attributes
3. `confrontation.hp_change` — creature HP MUST show non-zero delta
4. `narrator.combat_weapon_extracted` — weapon name sourced from inventory (new span or extended narration.weapon_used)
5. `narrator.max_turns_exceeded` — MUST fire (not crash) when max_turns breached; includes reason

## Dependencies
- 158-1: WWN combat never seats on fresh descent (DONE) — zone reconciliation, but not the general seating path
- 158-2: IntentRouter routes literary attacks (DONE) — verb classification works; seating is the fix
- 158-3: Block unbacked opponent HP writes (DONE) — guard against narration-only kills; this story ENABLES the seater
- #1072 (merged): WN tool-withhold to stop narrator from calling native combat tools — builds on this; extend to all dispatches

## Test Coverage Plan

1. **Seating Test**: WWN PC attacks creature → encounter != null, encounter.opponent is the creature
2. **Beats Test**: Seated encounter → narrator applies beat → total_beats_fired increases, creature HP changes
3. **Weapon Test**: Extracted weapon matches inventory; narration includes it
4. **Graceful Degradation**: Narrator max_turns=8 breach → log "max_turns exceeded", no crash
5. **Regression**: 158-1, 158-2, 158-3 paths still pass; non-WWN combat unaffected

## Context Notes

This story is **ADR-143 doctrine ground**: The fix is the combat-SEATS path so a confrontation actually SEATS and the WN ruleset owns resolution. Do NOT balance native mechanics against WWN. This is about wiring the seater, not tuning combat numbers.

The lie-detector ACs (OTEL assertions) are CRITICAL — they confirm the fix is mechanically backed, not narration-only confabulation.

