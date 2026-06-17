# Story 126-7: Player 4dF roll is determinative

**Epic:** 126 — Fate Core playtest follow-ups

**Type:** Feature  
**Points:** 5  
**Priority:** p1

## Technical Approach

**Problem:** The current Fate 4dF roll path is backwards. The server rolls 4dF itself and decides the outcome; the 3D FateDiceTray is a post-hoc decoration. Story 125-4 tried to animate that decoration to match the already-decided result and failed — the dice tumble to physics-determined faces unrelated to the actual roll, contradicting the text readout.

**Solution:** Make the player's Fate (4dF) roll determinative — physics-is-the-roll (ADR-074), the same model the d20 path already uses. The player throws the four dF dice in the tray and the faces they settle on ARE the roll; the server resolves from those reported faces.

**Model:** Mirror the d20 flow:
1. FATE_ACTION (action+skill+target) → server requests a Fate throw
2. Client throws 4 dF (interactive DiceScene, reuse InlineDiceTray gesture path)
3. Client reports 4 settled faces + throw_params + seed (Fate analog of DiceThrowPayload)
4. Server resolves from reported faces and broadcasts

**NPC Path:** NPC rolls stay server-side using roll_4df, broadcast FATE_ROLL with server-synthesized throw_params+seed (existing 125-4 path). Spectators replay; no client throw needed.

**Reuse (do NOT revert):** 125-4's merged groundwork stays — FateRollPayload throw_params/seed wire fields and dF '0' face label are correct and needed here. Tear out: the 'server decides, then animate' assumption in FateDiceTray + the server-rolls-for-players path.

## Key Decisions

- **Design-First:** Nail the FATE_ACTION→throw→resolve sequence and new client→server message before code; write an ADR-144/ADR-074 reconciliation note (player Fate rolls are physics-is-the-roll; NPC rolls server-side).
- **Determinism:** Faces come from physics throw → replaying throw_params+seed reproduces them for all seats (consistent by construction, like DICE_RESULT).
- **Legibility:** Dice show what was actually rolled; no contradiction between physics result and text readout.

## Acceptance Criteria

- **DESIGN (Architect):** Written design for FATE_ACTION→request-throw→client-throw→resolve sequence + new client→server Fate-throw message, plus ADR-144/ADR-074 reconciliation note. Design approved before RED.
- **PLAYER ROLL IS DETERMINATIVE:** Player Fate action resolves from CLIENT-reported 4dF faces, NOT server roll_4df. resolve_action derives roll_total/ladder_total/shifts/tier from thrown faces. Server test asserts no server-side roll_4df invoked on player path.
- **INTERACTIVE THROW (UI):** FateDiceTray lets player throw 4 dF via DiceScene gesture, captures 4 settled faces (each −1/0/+1) on settle, submits. No hardcoded/decorative throw.
- **CLIENT→SERVER MESSAGE:** Typed message carries 4 settled faces + throw_params + seed; faces authoritative at wire (pydantic, extra='forbid'); exactly 4 faces, each in {−1,0,1}. Routable in GameMessage union.
- **NPC ROLLS STAY SERVER-SIDE:** Non-player Fate rolls still use server roll_4df, broadcast FATE_ROLL with server-synthesized throw_params+seed. Server test confirms NPC/opponent rolls server-side; player path does not.
- **SPECTATOR CONSISTENCY:** Other seats replay thrower's throw_params+seed and land on SAME faces thrower reported (consistent by construction, like DICE_RESULT). 3D dice never contradict text readout.
- **OTEL:** fate.action_resolved span records dice that resolved action + whether player-thrown or server-rolled (GM-panel lie-detector).
- **WIRING:** End-to-end test of player throw→resolve round-trip through real handler (not fixture); confirm NPC path still server-rolls. Reuse 125-4's throw_params/seed payload fields + dF '0' label (no revert).

## Repos

- **sidequest-server** (develop)
- **sidequest-ui** (develop)

## Depends On

None

## References

- ADR-074: Dice Resolution Protocol — Player-Facing Rolls via WebSocket
- ADR-144: Fate Core Binding Replaces the Native Ruleset
- ADR-036: Multiplayer Turn Coordination
- Story 125-4: FateDiceTray 3D dice replay (throw_params/seed) + dF '0' label
- Story 126-1: Verify Fate-conflict harm to ablate stress/consequences, not core.hp
