# Narrative

## Problem Statement
Problem: The game engine was already gathering and sending players contextual lore clues tied to each quest — but the player screen never showed them. Why it matters: Keith and his playgroup were flying blind. The server had done the work of connecting quest threads to relevant world knowledge, but that insight was silently discarded before it ever reached the screen. Players couldn't see the coherent picture the system had already assembled for them.

---

## What Changed
Think of it like a research assistant who had already pulled together all the relevant files on a case — but then handed the detective an empty folder. The server was doing exactly that: attaching lore clues to each quest entry ("this job connects to the Merchant Guild collapse" or "the ruins you're heading to were a prison before the war") and sending them to the client. The client received them and threw them away.

Two small fixes closed that gap:

1. **The data was made visible.** The quest data structure in the client was updated to recognize the lore fields the server was already sending. Before this, the client didn't even know those fields existed.

2. **The screen was updated to show it.** A new "What I've learned about this job" block now appears under each quest in the Quests panel, listing the lore facts the engine has tied to that quest.

That's it. No new server logic. No new data generation. The engine was already doing the work — this change makes it visible.

---

## Why This Approach
The server-side projection (shipped in story 117-5) was the hard part — deciding which lore facts are relevant to which quests, scoring them, and packaging them per quest. That logic lives in one place on the server so it stays consistent no matter how many ways the UI evolves.

The client fix is intentionally minimal: recognize the data that's already arriving and render it. No duplication of server logic on the client side, no new API calls, no caching complexity. The data was on the wire; the client just needed to open its eyes.

A wiring test was added to confirm the lore block appears when the server sends quest data with lore attached — so this behavior is locked in and won't quietly regress.

---
