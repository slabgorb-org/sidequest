# 60-4

## Problem

**Problem:** Every time the game narrator used a tool (like looking up a monster stat or checking an NPC's inventory), it was paying to re-cache the same massive block of game instructions — twice per turn — at the wrong (cheaper-per-write but wasteful) rate. Over consecutive turns, this added up to roughly $0.116 per turn in AI API costs instead of the $0.04 it should cost at steady state.

**Why it matters:** The narrator uses a layered caching system so it doesn't have to re-send its entire rulebook to the AI on every single exchange. When a tool call happens (e.g., "check what traps are in this room"), the narrator makes two API calls in sequence: one to decide to use the tool, and one to continue narrating after getting the tool's answer. The second call should reuse the already-cached rulebook. Instead, it was re-caching it every time, throwing money away and hitting an API hard cap (4 cache markers per request) that could cause outright request failures.

---

## What Changed

Think of the narrator's memory like a hotel key card system. There are two types of cards: a 5-minute key (cheap to cut, expires fast) and a 1-hour key (slightly more expensive to cut, but lasts long enough to be worth it).

The narrator has a big stack of house rules it sends with every message. Before this fix, whenever the narrator called a tool and then came back to finish writing the story, it was stamping that big rules stack with a fresh 5-minute key — as if it had never seen those rules before. That meant: wasted money cutting a new key, and burning one of the four allowed card slots per request.

After the fix, the continuation call correctly stamps that same rules stack with a 1-hour key — the one that actually persists across the back-and-forth of a full tool loop — and subsequent turns read from that cache instead of writing again.

One related cleanup: the code that flags "this game-state section is in the wrong memory zone" was too aggressive. Some sections (NPC roster, confrontation directives) live in the player-message area of the conversation by design. The mis-zone detector now understands that and stops raising false alarms for those sections.

---

## Why This Approach

The Anthropic API has strict rules: each request can carry at most 4 cache markers. The narrator already uses 3 of those markers for its stable content (system prompt, genre rules, world lore). That leaves one slot for the dynamic game-state that changes each turn.

During a tool-use turn, the narrator makes a chain of API calls. The naive fix — just add another cache marker on the continuation message — would have blown past the 4-marker limit and gotten the request rejected. Instead, the fix teaches the narrator to move the single dynamic marker to the most recent continuation message, replacing any stale marker from earlier in the chain. This is called a "moving breakpoint" — it travels with the conversation as it grows, rather than piling up.

The 1-hour vs. 5-minute distinction matters because tool-loop continuation calls need to stay warm across several seconds of tool execution time, not just the milliseconds of a normal generation step. The 1-hour slot is the right tool for that job.

---
