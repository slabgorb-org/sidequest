# Narrative

## Problem Statement
**Problem:** When players descend into a dungeon in SideQuest, clicking the Map tab shows only the surface map — the two towns and the path between them. The dungeon itself, with its branching passages, discovered rooms, and the player's current location marker, never appears. The player is exploring a maze with no map of it.

**Why it matters:** The dungeon room-graph is one of the most tactically important tools for the player. Without it, a player can't track which passages they've explored, which rooms they've been in, or how far they've gone. The whole "fog of war clears as you explore" experience — a core dungeon-crawl fantasy — was silently broken. Players had to hold the map in their heads, which is exactly what SideQuest is supposed to offload.

---

## What Changed
Imagine the server is a postal worker who has been correctly sending dungeon-map letters to your door for months. The problem was that your mailbox had no slot for that letter type — it only had a slot for "surface map" letters — so every dungeon-map letter just fell on the floor and was thrown away.

This fix does three things:

1. **Cut a new mail slot.** The app now knows that `DUNGEON_MAP` is a valid message type from the server. Before this, the UI had never heard of it.

2. **Hire a handler.** When a dungeon-map message arrives, it's now read, validated, and the room data is handed to the dungeon renderer — which was already built and fully working, just never fed any data.

3. **Keep the two maps coexisting cleanly.** On the surface, the town/region map still appears unchanged. The moment you descend into a dungeon, the Map tab switches to showing the room-graph. Surface and dungeon views share one Map tab and never stomp on each other.

The server, the renderer, and the routing logic all existed before this story. This was a two-line wiring gap that took the whole visual system offline.

---

## Why This Approach
The team's standing principle is "wire up what exists before building anything new." The dungeon map renderer (`Automapper`) was already built, tested, and working — it just needed to receive data. The routing logic in `MapWidget` already distinguishes between a room-graph payload and a surface-cartography payload and sends each to the right renderer.

Rather than adding a simpler but sloppier blind cast (the existing surface-map handler uses one), the team introduced a proper TypeScript type for the dungeon payload, a runtime shape guard, and an explicit adapter. This makes the boundary honest: if a malformed frame ever arrives, the app logs a clear warning and drops it rather than silently producing a corrupt map. The payoff is that the dungeon path is now more robust than the pre-existing surface-map path, not just "also wired."

Seven integration tests lock the full path: message arrives → handler fires → room nodes appear in the Map tab → current room is marked → surface view still works before and after. All 93 pre-existing map-suite tests still pass.

---
