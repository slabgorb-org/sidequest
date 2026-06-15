# Narrative

## Problem Statement
Problem: The Fate Core rules engine (built in F1) does all its work inside the server and never tells the player interface what's happening. Fate characters have Fate Points, skills ranked on a ladder, aspects that grant story advantages, stress boxes that absorb harm, and consequences that linger from wounds — none of that data is flowing to the screen yet. Why it matters: A player clicking "Attack" in a Fate session sees nothing about their character sheet, their current Fate Points, or the scene's situation. The mechanical layer exists but it's invisible, like a scoreboard that never updates. Every future Fate UI feature (character panels, the Fate Point economy display, the stress tracker) is blocked until there's a reliable pipeline delivering this data to the client.

---

## What Changed
Think of the server as a kitchen and the player's screen as the dining room. Previously, the Fate Core kitchen was cooking — tracking points, aspects, skills — but had no pass-through window to send food to the table.

This story installs that window.

Whenever something meaningful changes in a Fate session (a Fate Point is spent, an aspect is invoked, stress is taken, a scene shifts), the server now bundles up a complete snapshot of the table's Fate state and sends it to every connected player as a `FATE_STATE` message. That bundle includes:

- **Each character's Fate Points** (current balance and their refresh rate — the number they reset to each scene)
- **Skill ratings** translated to the Fate ladder (Mediocre, Average, Fair, Good, Great, Superb, Fantastic, Epic, Legendary)
- **All aspects** — the descriptive phrases that define a character — tagged by type (character aspect, consequence, boost) and noting whether they're available to be invoked for free
- **Stress boxes** — the row of checkboxes that absorb hits before real harm sets in
- **Consequence slots** — the named wounds a character is carrying (Mild, Moderate, Severe)
- **Scene-level data** — the situation aspects and boosts active in the current scene, plus who's on which side of a conflict and whose turn it is

This message only fires for Fate sessions — it does nothing in a Dungeons & Dragons or space opera game. And it only fires when something actually changes, not on every single player action, keeping the system efficient.

A new monitoring signal (`fate.projection.emitted`) now appears in the GM observability panel every time this snapshot goes out, so the game master can verify the pipeline is live.

---

## Why This Approach
The team used an existing, proven pattern from the same codebase: the `RELATIONSHIPS` message (how character relationship data flows to the UI) and the `QUESTS` message. Both follow the same "snapshot on change, not on every tick" model that's already battle-tested in live sessions.

By matching that pattern exactly, this work plugs into the client's existing message-handling infrastructure without requiring the UI team to learn a new protocol. When it's time to build the Fate character panel (story F3b and beyond), developers will find the data arriving in exactly the shape they expect, because it mirrors what the client already knows how to receive.

The "only fires for Fate packs" gate means zero performance impact on the nine other genres. The "only fires on change" rule means a quiet scene doesn't generate noise.

---
