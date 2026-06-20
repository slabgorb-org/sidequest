# Narrative

## Problem Statement
**Problem:** The game's AI narrator was suffering from a kind of in-session amnesia — it would introduce a character by name ("Henry Shaw, the cattle baron"), then moments later when that character became a combat opponent, create a completely different, unnamed placeholder instead of the person it had just described. Separately, when a scene referenced a canonical figure already built into the game world (like the Good Witch of the North in the Oz setting), the engine would invent a random hollow stranger ("Amaranth Warmacre") with no stats, no pronouns, no personality — discarding the authored character entirely.

**Why it matters:** SideQuest is built for experienced players — people who have run tabletop games for decades and will immediately notice when the AI contradicts itself. A GM who introduces a villain by name and then "forgets" who they are two turns later isn't a GM; it's a chatbot. These bugs broke narrative continuity, corrupted combat identity (wrong stats, wrong pronouns, no backstory), and directly undermined the core promise of the product: an AI that can surprise a career game master. Every occurrence was a table-breaking moment.

---

## What Changed
Think of each named character in the story as having two states: *mentioned* (the narrator just described them) and *established* (they're fully in the game engine). The bug was that the combat engine only looked at the *established* pile when deciding who the opponent was — it never checked the *mentioned* pile.

**Fix A:** The combat seating logic now looks in both piles. When a fight starts, it checks whether the opponent was recently mentioned by name and, if so, brings them forward — carrying their full identity (pronouns, appearance, disposition) — rather than fabricating a nameless placeholder.

**Fix B:** A new "person recency guard" was added to the narration engine. When the AI references someone in a scene where only one other person is present and that reference isn't flagged as a brand-new arrival, the engine now recognizes it's talking about that same person — not a newly invented stranger with a random name. The Good Witch stays the Good Witch.

**Fix C:** Deferred to a follow-up story (126-38). The name-culture routing bug (Anglo names being sent to the wrong cultural generator) needs a content-side design decision about how regions map to cultures before it can be safely fixed.

---

## Why This Approach
The underlying ordering problem was subtle: character seating (deciding *who* fights) happens *before* the narrator runs in each turn. That means a character mentioned in turn 1 lives in a "pending" pool at seating time in turn 2 — they haven't been promoted to the full engine registry yet. The fix was applied at the seating step itself rather than trying to pre-promote everyone, because touching the narration timing would have been a much riskier change affecting every turn in every session.

For Fix B, the team chose a "recency scene-guard" pattern — the same technique the engine already used for creature NPCs — rather than trying to do fuzzy name-matching. Name matching would have been fragile and prone to false positives across languages and epithets. Recency-in-scene is a much more reliable signal: if you're in a room with one person and the narrator references "a woman," it's that woman.

Both fixes include telemetry events (GM dashboard spans) so the operator can verify the binding fired and the AI isn't improvising NPC identity without mechanical backing.

---

## Before/After
| Moment | Before (broken) | After (fixed) |
|---|---|---|
| Turn 1: Henry Shaw threatens the players | Narrator describes "Henry Shaw, the cattle baron, draws his pistol" — Shaw enters the *pending NPC pool* | Same |
| Turn 2: Combat starts | Seater looks only in `snapshot.npcs` (empty), finds nothing, fabricates `Npc(description="Fate conflict opponent")` — the Western Diamondback from the bestiary | Seater finds "Henry Shaw" in `snapshot.npc_pool`, promotes him carrying `pronouns=he/him`, appearance, disposition — `fate.opponent.seeded created=false` |
| GM dashboard | `fate.opponent.seeded: created=true, description="Fate conflict opponent"` — the lie detector shows a fabrication | `fate.opponent.seeded: created=false, name="Henry Shaw", pronouns="he/him"` — binding confirmed |
| Oz world: narrator references "the Good Witch" | Engine mints a hollow `NpcPoolMember("Amaranth Warmacre")` — no hp, no pronouns, no disposition | Scene-guard fires: one person in scene, reference is non-new → engine binds to the seeded registry NPC "Good Witch of the North" carrying `she/her`, disposition 25 |
| GM dashboard (Good Witch) | No reconciliation span — silent hollow mint | `npc.person_reconciled` span emitted with `reconciled_to="Good Witch of the North"`, `signal="scene_guard"` |
| New character entering the scene | `is_new=True` in narrator output → fresh mint (same as before) | `is_new=True` → guard skips → fresh mint (unchanged path, explicitly tested) |
