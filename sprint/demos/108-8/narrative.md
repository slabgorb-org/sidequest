# Narrative

## Problem Statement
**Problem:** Every combat encounter in the Without Number (WWN) ruleset — covering three genre packs and two worlds — crashed with a hard error the moment a player committed an action. **Why it matters:** This was a total combat outage affecting Caverns & Claudes, Heavy Metal, and Elemental Harmony, including the flagship worlds Beneath Sunden and Barsoom. Any session using WWN rules could not get past the first sword swing. 78 automated end-to-end tests confirmed it: zero percent of WWN combat was functional.

---

## What Changed
Think of it like a vending machine that was rewired mid-production. The old system required every action a player could take in combat — attack, move, use an item, cast a spell — to be listed on a pre-printed menu card (`cdef.beats`). A previous fix (story 108-1) correctly removed some outdated items from that menu card. But nobody updated the vending machine itself: it still tried to find the player's selection on the old card, found an empty list, and threw an error every single time.

This fix teaches the vending machine a new trick: when the game is running under the Without Number ruleset, it no longer looks at the card at all. Instead, it generates the valid action set on the fly — attack, move, use an item, cast — based on the rules of the WWN system itself. The WN math (dice rolls, weapon damage, armor checks, Shock values) is completely preserved. The machine just no longer requires the old menu card to exist.

A "receipt" (`wn.native_scaffolding_suppressed`) is now printed every time this new path fires, so developers and QA can verify the right engine is running.

---

## Why This Approach
The engine already had a proof-of-concept for exactly this pattern: "drink a potion" was already handled as a **synthesized action** that doesn't need to appear on the pre-printed card. Rather than invent a new architecture, this fix extends that existing, proven pattern to cover the full WWN combat vocabulary.

This matters for three reasons:

1. **Safety for native packs.** The fix is gated strictly to WWN-bound sessions. Every other genre pack — anything *not* using the Without Number ruleset — still requires beats on the card, exactly as before. The gate is explicit in code; there's no way for it to accidentally apply to the wrong system.

2. **No math changes.** The d20+hit-bonus vs. AC check, weapon dice from the character's inventory, Shock damage on near-misses, and saving throws are all untouched. This is plumbing, not rebalancing.

3. **Observability first.** The `wn.native_scaffolding_suppressed` telemetry event means the GM panel can confirm — in real time — that the correct engine is engaged. This is the lie-detector principle: if the span isn't firing, something is wrong.

---

## Before/After
| | Before (broken) | After (fixed) |
|---|---|---|
| **WWN combat action submitted** | `DiceDispatchError: unknown beat_id … available: []` | Clean resolution: d20 roll, weapon damage, narration |
| **Action source** | Looked up `beat_id` in `cdef.beats` (empty list) | Synthesizes WN action set on the fly from ruleset |
| **Native packs affected** | No change (they still work) | No change (gate is strict to WWN binding) |
| **WN dice math** | N/A — crashed before reaching it | d20+hit vs AC · weapon dice · Shock · saves — all intact |
| **OTEL signal** | No signal (crash before telemetry) | `wn.native_scaffolding_suppressed` fires on every WN combat turn |
| **Test suite** | 78 e2e failures across Caverns & Claudes, Heavy Metal, Elemental Harmony | 78 tests passing |
| **Affected worlds** | Barsoom, Beneath Sunden (combat fully broken) | Both worlds fully combat-capable |
