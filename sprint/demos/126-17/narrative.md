# Narrative

## Problem Statement
Problem: When a player's character was attacked in a Fate Core combat encounter, the game froze. The server sent a "defend yourself" signal to the player's screen, but the UI had no way to receive it, show the player what was happening, or let them roll dice in response. Every Fate combat encounter that reached an attack landed the entire table in a dead hang — nobody could proceed.

Why it matters: Fate Core is one of the rulesets SideQuest supports. Until this was fixed, Fate conflict scenes — the dramatic core of the game — were unplayable for the whole table. One player being targeted ended everyone's session.

---

## What Changed
Before this story, the game client was deaf to one specific server message: "someone is attacking you, it's your turn to defend." The message arrived, nothing happened, and the game waited forever.

This story wires up the full defensive response loop:

1. **The client now listens** for the "defend yourself" signal from the server.
2. **A defend tray appears on screen** showing exactly who is attacking, which skill they used, and what total they rolled — all pulled directly from the server's message, never guessed or hardcoded.
3. **The player rolls their defense** using the same four Fate dice (4dF) tray already used for attacks, then the result is sent back to the server and the tray closes.
4. **The player can concede** instead of rolling — a one-tap affordance that sends the concede signal and clears the tray.
5. **All of this is wired into the real game screen**, not a floating prototype — proven by tests that mount the full component tree, not just the tray in isolation.

---

## Why This Approach
Fate Core has a symmetric design: attack and defense are mirror operations. Rather than build a second dice system, this story reuses the existing attack dice tray (FateDiceTray) and the existing message-sending path (handleFateThrow), adding a single `action: 'defend'` flag to distinguish the two directions. The server already spoke this language; the client just needed to listen.

Pulling attacker name, skill, and roll total from the live server payload — instead of embedding them as constants in the code — means the UI stays honest. If the server changes what it sends, the screen reflects the real values automatically. No maintenance trap, no drift between what the engine computed and what the player reads.

The concede option is built in from day one because Fate explicitly models surrender as a valid, mechanically meaningful move. Shipping it alongside the defend roll means the table has the full ruleset surface from the first session, not a partial one.

---
