# Narrative

## Problem Statement
Problem: When the AI narrator described a character receiving an item they already carried, the game engine added a second copy of that item to their inventory rather than recognizing they already had it. In an Oz-themed session, this caused a character to end up carrying two pairs of silver shoes — an impossible situation that undermines trust in the game's internal logic.

Why it matters: Inventory is the ledger of what a player owns and can use. Phantom duplicate items corrupt that ledger, can create cascading confusion in gear-dependent mechanics (item upgrades, aspect promotions, future crafting systems), and — most importantly — break the immersion that makes the AI narrator feel like a capable game master rather than a system that needs babysitting.

---

## What Changed
The game server stores each character's carried items as a list. Every time the narrator said a character "gained" something, the server would simply add it to that list — no check, no questions asked. If the narrator mentioned the same item twice (which happens naturally when re-describing a scene, resuming a session, or narrating a callback moment), the item would appear twice.

The fix adds a simple gatekeeper before any "gained" item is written to the list: look up whether the character already carries something with the same name or ID. If they do, the second mention is quietly ignored — with one important exception: the GM dashboard (the "lie detector" panel) logs a record of the catch, so it's always visible that a dedup happened and nothing was silently swallowed.

Three other inventory operations (marking items lost, discarded, or consumed) already did this identity check. The "gained" path was the lone outlier — this fix brings it into alignment.

---

## Why This Approach
The safest fix is a no-op: when we see a duplicate, we do nothing and move on. An alternative would be to add the quantities together (the character now has 2 of the item), but that creates a different problem — we have no reliable way to tell the difference between "the narrator mentioned the same pair of shoes twice in one scene" and "the character genuinely found a second identical pair." Treating every re-mention as a restock would just inflate the inventory in a different field.

The no-op choice mirrors an existing precedent: earlier work (the "45-13 container gate") already blocks re-retrieval of container items using the same logic. We extended that pattern consistently across the gained lane rather than inventing new behavior.

The OTEL telemetry requirement (the GM panel log) is non-negotiable under the project's "no silent fallbacks" principle — if something was suppressed, the developer must be able to see it.

---

## Before/After
**Before (broken behavior)**

```
Turn 7: Narrator grants 'silver shoes' to Dorothy
→ item appended to inventory: ['silver shoes']

Turn 7 (re-narration / RESUME callback):
→ Same grant processed again: bare append, no check
→ inventory: ['silver shoes', 'silver shoes']  ← duplicate
→ No log event; no GM panel record; silent corruption
```

**After (fixed behavior)**

```
Turn 7: Narrator grants 'silver shoes' to Dorothy
→ Identity check: nothing in inventory matches → append
→ inventory: ['silver shoes']

Turn 7 (re-narration / RESUME callback):
→ Identity check: 'silver shoes' (narrator:silver_shoes) already carried → SKIP
→ inventory: ['silver shoes']  ← unchanged, correct
→ item_gain.deduped event logged → visible in GM panel dashboard
```

The fix touches one file (`sidequest/server/narration_apply.py`), adds 64 lines in a single block, and requires zero changes to the inventory data model, the protocol, or any client-side code.
