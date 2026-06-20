# Narrative

## Problem Statement
Problem: When a player reconnects to a game that's already in the middle of a conflict, the interface shows them action buttons — Attack, Overcome, Create Advantage, Concede — even though they've already locked in their choice for that round. Clicking any of those buttons results in a silent rejection from the server. Why it matters: players are left confused, wondering if their action registered, why nothing happened, or whether the game is broken. It erodes trust in the interface at exactly the moment the drama is highest — mid-conflict.

---

## What Changed
Think of it like a ballot box. Once you've dropped your vote in, the slot closes. Before this fix, the ballot slot *looked* open to returning voters — it just silently swallowed any paper they put in. Now the slot visibly closes the moment your vote is locked. A player who reconnects mid-conflict sees a "sealed" indicator instead of clickable action tiles, matching what the server already knew: their turn is done.

Concretely: the game now tracks, for each player character, whether they've already committed an action this round. That true/false flag travels from the game engine to the interface. If it's true, the four action buttons swap out for the existing "fate sealed" visual — the same one that appears when you commit in real time. No new concepts, no new visual language. Just consistent behavior whether you stayed connected or came back mid-round.

---

## Why This Approach
The server already had a hard guard: it will reject a second commit from any player, no exceptions. That guard exists for good reason — it's the integrity lock that makes sealed-commit multiplayer fair. The tempting fix would have been to soften that guard ("just let it slide this once"), but that would open the door to accidental double-actions and undermine the fairness model the whole Fate conflict engine is built on.

Instead, this fix makes the UI *tell the truth* about what the server already knows. The state was always there in the game data (`fate_commits` on the encounter); we just weren't surfacing it to the button layer. Wiring that one boolean to the tile visibility closes the gap without touching the server's rules.

---
