# Story 108-5: WN Combat Player Action Surface

## Story Details
- **ID:** 108-5
- **Epic:** 108 (WN Combat System Refactor)
- **Title:** WN combat player action surface — WN action buttons replace native beat menu
- **Points:** 5
- **Workflow:** tdd
- **Repos:** sidequest-ui, sidequest-server
- **Depends On:** 108-1 (Engine core cut must be done first)

## Acceptance Criteria

### AC1: WN Action Buttons Replace Native Beat Menu
The confrontation overlay displays the Without Number action button set instead of native beats:
- **Attack** (equipped weapon) → d20 + hit bonus + attribute mod vs target AC; weapon damage on hit
- **Use Item** (consumable from inventory) → item effect (e.g., heal 1d6+2); item consumed; no attack roll
- **Move / Disengage** → reposition in round; WWN Fighting Withdrawal where SRD grants it
- **Cast** (arcane classes only) → WN Effort spend + spell resolution

**Explicitly excluded:** Brace / total-defense button. WWN SRD has no total-defense action; defense is passive AC.

### AC2: Each Button Fires a Real WN Roll via WithoutNumberRulesetModule
When the player clicks an action button:
1. The UI sends a DICE_THROW with the action id (story/action identifier, not native BeatKind)
2. The server's WithoutNumberRulesetModule resolves the action (d20 roll, damage, saves, etc.)
3. The ADR-074 dice tray renders the WN attack roll
4. Opponent acts at its own initiative slot in run_wn_round() — the player's action doesn't lock out opponent turns

**Seams to verify:**
- dispatch/dice.py ~671-676 routes to ruleset module, not native apply_beat()
- WithoutNumberRulesetModule.attack_params / resolve_damage handles the roll
- run_wn_round() sequencing respects initiative (opponent can act after player)

### AC3: RP Flavor Rider is Mechanically Inert
The player may optionally type freeform text ("I swing from the chandelier") when clicking an action button:
1. The text rides on DICE_THROW.player_action (existing field, unchanged)
2. The text is passed to the narrator as a replay hook: `PLAYER_ACTION: {text}`
3. **The text NEVER affects mechanical outcome** — same d20 roll, same damage dice, whether text is present or not
4. The narrator colors the resolved button outcome with the RP intent; that is its sole purpose

**Explicit invariant:** There is no freeform-adjudication path. The engine never tries to mechanize "chandelier swing." The roll is already done on the button; the rider is downstream cosmetic context.

### AC4: Bare Combat Free-Text Does Not Resolve to a Combat Outcome
When the player is in combat:
1. The InputBar is bound to "type your flourish, then pick an action"
2. A bare text submission (text with no action button) is **not** submitted during combat
3. Out-of-band table-talk (ADR-107 aside channel) is unaffected — that is non-turn-consuming OOC

**Invariant preserved:** Every combat outcome traces to a button → roll, never to narrated free-text.

### AC5: Flavor Rider OTEL Proves Mechanical Inertness
When a WN combat action is resolved with optional RP flavor text:
1. Emit (or enrich the action-resolution span) with a marker proving the text was attached **and did not enter mechanical resolution**
2. Example span: `wn.action.flavor_rider{attached=true, affected_mechanics=false}`
3. The GM panel (OTEL dashboard) shows this span and confirms the rider was flavor-only

**The lie-detector test:** Without this OTEL, we cannot distinguish a flavor rider from a covert freeform-adjudication regression.

## Implementation Notes

### Repos and Branches
- **sidequest-ui:** UI button panel, InputBar bind, dice tray renderer (ADR-074)
- **sidequest-server:** DICE_THROW routing, WithoutNumberRulesetModule action resolution, OTEL spans

### Seams to Touch
1. **sidequest-ui/src/components/ConfrontationOverlay.tsx** (or equivalent) — replace native beat tile menu with WN action buttons
2. **sidequest-ui/src/components/InputBar.tsx** (or equivalent) — constrain text binding to "type flavor, pick button" (no bare submission)
3. **sidequest-server/sidequest/dispatch/dice.py ~671-676** — route DICE_THROW action-id to ruleset module, not apply_beat()
4. **sidequest-server/sidequest/game/ruleset/without_number.py** — ensure attack_params, resolve_damage are wired
5. **sidequest-server/sidequest/game/wn_round.py** — verify WN action resolution and opponent sequencing
6. **sidequest-server/sidequest/telemetry/** — add `wn.action.flavor_rider` OTEL spans

### Testing Strategy (TDD Phase)
**RED phase:** Write failing tests that specify:
- Button click emits correct action id (not BeatKind)
- WN roll is resolved (d20 visible in dice tray)
- Flavor text is present in narrator replay but doesn't change outcome
- Bare text submission fails during combat
- flavor_rider OTEL span is emitted with affected_mechanics=false

**GREEN phase:** Implement to make tests pass.

## Dependencies
- **Depends on 108-1** — The engine must resolve a WN action (not a native beat) behind the button. If 108-1 is not merged, the button has nothing to route to.

## Scope Notes
- **In scope:** Player-facing WN combat action surface (hp_depletion confrontations under a WN binding)
- **Out of scope:**
  - Engine cut (108-1)
  - Room-sourced seater (108-2)
  - Content de-nativization (108-3)
  - Dial chase / negotiation confrontations (keep native dial engine untouched)

## Specification Reference
See **docs/superpowers/specs/2026-06-14-wn-combat-action-surface-design.md** for full design rationale, the "Zork Problem" context, and architectural reconciliation notes.
