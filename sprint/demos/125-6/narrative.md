# Narrative

## Problem Statement
**Problem:** Two small gaps in the Fate game panel could let a bad or corrupted game state message freeze the player's browser or silently inject invalid data into a live session. **Why it matters:** Players mid-session — especially in a multi-seat game — should never see a hung browser tab or mysteriously wrong game state after a page refresh. A single malformed message from the server shouldn't be able to ruin the table's session.

---

## What Changed
**Change 1 — The Pip Guard (free invocations display)**

In Fate Core, when a player creates an advantage, they earn "free invocations" — bonus uses of that advantage shown as small filled dots (pips) in the Fate Panel. The panel was building those dots by telling the browser "make me *N* dots" — but it never checked whether *N* was a sane number. If the server sent a corrupted message with `free_invokes = 1,000,000,000` (or the mathematical concept of infinity), the browser would obediently try to render a billion dots and freeze solid.

The fix: before drawing any dots, we now cap the number at a reasonable maximum. If the server says "one billion pips," the panel renders a small, bounded count and moves on. The game continues; the table never notices.

**Change 2 — Blocking the Reload Backdoor**

Modern browsers remember things across page refreshes using a small storage area called session storage — think of it as a sticky note the browser keeps while a tab is open. The app was saving Fate game state onto that sticky note so that refreshing the page felt instant. The problem: that sticky note was read back on reload *before* the safety check that validates incoming Fate state. A corrupted payload sitting in storage would walk straight past the guard and infect the live session.

The fix: Fate state is no longer saved to the sticky note at all. On reload, the panel waits for a fresh, validated message from the game server — the same safety checkpoint all live messages go through. The reload is marginally slower, but the data is always clean.

---

## Why This Approach
Both fixes follow the same principle: **defend at the boundary, not in the middle.** Rather than adding complexity to how the game processes Fate state after it arrives, we stop bad data at the two places it can enter — the display layer (clamp before rendering) and the reload path (exclude from storage). This keeps the fix small, targeted, and easy to verify. There's no new feature machinery; just two guards that say "no" to data that shouldn't be there.

---
