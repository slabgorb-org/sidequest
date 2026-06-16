# Story 118-7: F3g — wire the 4dF roll surface end-to-end

**Status:** backlog → setup  
**Points:** 3  
**Priority:** p2  
**Workflow:** tdd (phased)  
**Repos:** server, ui  
**Depends on:** 118-3 (done, merged to develop)

## Narrative

**Epic:** F3 — Fate Core UI surfaces (ADR-144)

Story 118-7 carries deferred/non-blocking findings from 118-3 (F3c — 4dF roll display). The infrastructure is in place:
- 118-3 delivered the dF Fudge die (dice-lib, live on main), the server FateRollPayload/FATE_ROLL message + handler emit, and the FateDiceTray component + isFateRoll guard (merged to UI develop).
- 118-2 (F3b) is done — FatePanel.tsx, FATE_STATE routing (useStateMirror.ts:251), fateState slice, and FateWidget all exist on develop.

**What's missing:** The roll surface is not yet wired into the live client. The client can mount FateDiceTray into FatePanel by gating on `gameState.fateState != null` (FATE_STATE only arrives on ruleset=='fate' packs). In multiplayer, FATE_ROLL is currently delivered sender-only and peers never see the roll.

## Acceptance Criteria

### 1. UI Mount: Route FATE_ROLL + Mount FateDiceTray
- Route FATE_ROLL via `isFateRoll` in useStateMirror/App into a `latestRoll` slice (or equivalent state carrier).
- Mount FateDiceTray inside the FatePanel/FateWidget, gated on fate-pack presence (`gameState.fateState != null`).
- Currently FateDiceTray + isFateRoll have NO production consumer; this AC makes them live.

### 2. MP Broadcast: Fan-Out FATE_ROLL
- FATE_ROLL is currently delivered sender-only via per-socket `out_queue` (websocket.py:133-135).
- Broadcast via `session._room.broadcast` like DICE_RESULT (websocket_session_handler.py:1263) so peers see the acting PC's roll.
- Mirrors SOUL Guitar Solo principle: the soloist's roll is visible to the table.
- Fix the now-misleading 'broadcasts the same result to the table' comment in handlers/fate_action.py.

### 3. Attribution: Player ID on FATE_ROLL
- Stamp `player_id=acting_player_id` on FateRollMessage (currently empty `''`).
- Allows a consumer to attribute whose roll it is.
- Flagged by both security and edge-hunter reviewers.

### 4. Glyph Consistency: Zero Face Display
- FateDiceTray `faceGlyph(0)` returns `'0'` but the dF die label for a blank face is `''`.
- The table sees `+ + 0 -` vs the die's blank face — inconsistent.
- Pick one (recommended: `'0'` is clearer for Sebastien/Jade legibility per player-UI mandate) and make die + text readout agree.

### 5. Stretch: Throw Params / Seed on FATE_ROLL
- Carry `throw_params` and `seed` on FATE_ROLL (like DICE_RESULT) so the 3D Fudge dice animate to the actual rolled faces.
- Today they render the idle pickup row (decorative) and only the text readout is authoritative.

## Technical Approach

### Server Changes (sidequest-server)
1. **FateRollPayload enhancement:** Ensure FATE_ROLL message carries `player_id` (acting player attribution).
2. **Broadcast routing:** In handlers/fate_action.py or the dispatch layer, broadcast FATE_ROLL via `session._room.broadcast()` (like DICE_RESULT) instead of or in addition to the sender-only out_queue path.
3. **Comment cleanup:** Fix the misleading broadcast comment in handlers/fate_action.py.
4. **Optional:** Carry throw_params/seed for 3D animation (stretch goal).

### UI Changes (sidequest-ui)
1. **FATE_ROLL routing:** Add FATE_ROLL routing case in useStateMirror (or GameStateProvider) to capture the latest roll into a slice.
2. **FateDiceTray mount:** In FatePanel or FateWidget, conditionally mount FateDiceTray when:
   - `gameState.fateState != null` (fate-pack is active)
   - A FATE_ROLL message has arrived
3. **Glyph consistency:** Audit FateDiceTray.faceGlyph(0) and the dF die definition; align zero-face rendering (e.g., both render `'0'` or both render blank).
4. **Testing:** Ensure FATE_ROLL routes to UI and mounts the tray; test in MP that all seats receive the roll.

## Key Dependencies
- **118-3 (done):** dF die, FateRollPayload, FATE_ROLL message, FateDiceTray, isFateRoll guard.
- **118-2 (done):** FatePanel, FATE_STATE routing, fateState slice, FateWidget.
- **118-10 (done):** server-side invoke/player_action wiring (context for reroll/freeform in F3d/F3f).

## Notes
- This is a phased TDD workflow: red → green → review → finish.
- No Jira integration; track by story ID.
- Repos: sidequest-server (develop) and sidequest-ui (develop).
- Player-UI mandate: all roll information is legible (Sebastien/Jade mechanics-first preference).
- The mount pattern mirrors RELATIONSHIPS/QUESTS panels (ADR-136).
