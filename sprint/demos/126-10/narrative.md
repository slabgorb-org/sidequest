# Narrative

## Problem Statement
**Problem:** On any SideQuest session using a Fate Core ruleset world (e.g., *Années Folles*), the game's "intent router" — the step that figures out what kind of action a player is attempting before narrating anything — was taking **37 to 81 seconds** to complete. In a turn-based game where players expect a response in roughly 4–6 seconds, this introduced a pause long enough for players to assume the game had frozen.

**Why it matters:** Every player turn in a Fate world hung for up to a minute before the narrator could even begin writing a response. In a multiplayer session, all seated players stall together. This made Fate worlds effectively unplayable at the table.

---

## What Changed
Think of the intent router as a dispatcher at the front desk: before passing your request to the narrator, it reads a summary of the current game state and decides what kind of request you're making (fighting, talking, exploring, etc.).

For Fate Core worlds, a function called `build_fate_projection` was packing *everything* it knew about Fate — all the Aspects, Stunts, stress tracks, fate point pools, and rulebook context — into that front-desk summary. The dispatcher was being handed a 50-page dossier when it only needed a business card.

The fix: `build_fate_projection` now produces a compact version of Fate state for the router — just enough to recognize what kind of action is happening — and reserves the full detailed projection for the narrator, where that depth is actually needed.

---

## Why This Approach
The router and the narrator have different jobs and different appetites for information. The router needs breadth (what domain is this?), not depth (what are all the Fate rules?). Feeding the router a full Fate ruleset snapshot forced the language model to process thousands of tokens before answering a question that should take hundreds.

Keeping the trim isolated to the router (rather than changing the narrator's view of Fate state) meant zero risk to narration quality or Fate mechanical accuracy — the narrator still gets the full picture; the router just gets a smaller ticket.

The fix was scoped to `build_fate_projection` alone, separate from the narrator prompt work in story 126-9, so both fixes can be verified independently and any regression is easy to isolate.

---

## Before/After
| Metric | Before (Fate world) | After (Fate world) | Non-Fate Baseline |
|---|---|---|---|
| `intent_router_pass` duration | 37–81 seconds | ~4–6 seconds | ~4–6 seconds |
| Router prompt token size | ~3–5× baseline (full Fate projection) | Compact (routing signal only) | Baseline |
| `error_max_turns` on Fate turns | Observed (structured call timing out) | Zero | Zero |
| Narrator Fate state | Full projection | Full projection (unchanged) | N/A |
| Routing accuracy | Correct (but slow) | Correct (and fast) | Correct |
| Understudy 2-seat run (`annees_folles`) | Stalls / timeouts | Completes cleanly | N/A |

**Old behavior:** Every player action on a Fate world triggered a multi-second (sometimes multi-minute) pause before narration began, because the router was processing a complete Fate ruleset dump on every turn.

**New behavior:** The router receives only what it needs — a compact Fate signal — and routes in baseline time. The narrator continues to receive the full Fate projection it needs for mechanically accurate responses.
