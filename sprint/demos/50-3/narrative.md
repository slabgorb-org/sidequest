# 50-3

## Problem

**Problem:** When players recruited NPC companions during a session, the Party Panel showed only the player characters — hired allies were invisible to the entire table. Why it matters: the core game loop in SideQuest's dungeon-crawl content requires players to hire companions at waypoints, descend with them, and track whether they survive. Without the roster showing up, the table had no way to confirm a hire actually happened versus the AI narrator simply *saying* it happened. Story and reality were decoupled, which breaks player trust instantly.

---

## What Changed

Think of the Party Panel like the sidebar of a team chat app — it shows who's "in the session." Before this fix, that sidebar only ever showed the human players. NPCs your character hired were referenced in the story text, but never appeared in the panel.

The server was doing its job correctly: every time someone recruited a companion, the server logged it and sent the full updated roster to the client. The client was just ignoring the companion section of that message.

This fix wires up the companion list in the message the client was already receiving. Now when the server says "Donut the Mercenary has joined the party," a new **Companions** sub-section appears at the bottom of the Party Panel showing Donut by name, role, and which player character they're traveling with. When a companion is dismissed, they disappear. When there are no active companions, the section hides itself entirely — it doesn't sit there showing an empty box.

---

## Why This Approach

The server already had the right data; it just wasn't being used. Rather than building a new endpoint or changing the server, the fix plumbs one already-arriving data field through three layers of the client — the main application, the game board, and the party panel component — all the way to the screen.

The companions list replaces itself completely on every update rather than merging changes in. This is intentional: "always trust the server" is simpler and safer than trying to reconcile what the client thinks it remembers. If the server says the roster is \[Donut, Katia\], that's what the panel shows, no questions asked.

---
