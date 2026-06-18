# Narrative

## Problem Statement
**Problem:** When players took turns in Fate-system worlds (like the 1920s Paris world *Années Folles*), the game engine was taking 37 to 81 seconds just to *decide what kind of action the player intended* — before any narration was even written. In normal worlds, this step takes 4 to 6 seconds. **Why it matters:** A 60-second pause between a player typing their action and the game responding breaks immersion entirely. In a multiplayer session, every seated player sits in silence waiting. For a game designed around the table experience of Keith's playgroup — including players like Alex who already struggle with pacing pressure — a one-minute dead zone is a session-killer.

---

## What Changed
Think of the game's "intent router" as a traffic cop that reads a player's action and decides which lane it belongs in: combat, social encounter, exploration, magic, etc. To do its job, it gets a summary of the current game state.

The problem was that for Fate-system worlds, that summary was being handed a *full Fate character sheet* — Aspects, Stunts, Fate Points, the entire mechanical picture — when the traffic cop only needed to know roughly *who the characters are* and *what the scene looks like*. It was like asking a parking attendant to read your entire medical history before deciding which floor of the garage you should park on.

The fix trimmed what gets handed to the router from the Fate character projection. The router now gets a lightweight, "need to know" version of Fate world state, while the full projection is still available downstream where it's actually needed — during narration itself.

---

## Why This Approach
The Fate router prompt and the Fate narrator prompt are separate problems. Story 126-9 (already completed) fixed narrator verbosity. This story fixed the router — a different call, a different prompt, an earlier step in the pipeline.

The routing decision is a fast, coarse-grained classification. Flooding it with rich Fate mechanical data doesn't improve accuracy — it just makes the AI model work through a much larger context window to produce the same two-word answer ("this is a social confrontation"). By trimming the input to only what routing actually needs, the call gets faster without changing what it decides.

The structured call also has a two-turn limit (`max_turns=2`). When the prompt was bloated, the model occasionally hit that limit before finalizing, producing a fragile failure mode. With a leaner prompt, the call completes cleanly in one turn.

---

## Before/After
| Metric | Before | After |
|--------|--------|-------|
| `intent_router_pass` — Fate worlds | 37,000–81,000 ms | 4,000–7,000 ms |
| `intent_router_pass` — non-Fate baseline | 4,000–6,000 ms | 4,000–6,000 ms (unchanged) |
| Router state summary size (Fate) | ~3,200–4,100 tokens | ~400–600 tokens |
| `error_max_turns` on Fate turns | Occasional (structured call hit limit) | Eliminated |
| Routing accuracy (Fate worlds) | Correct | Correct (unchanged) |
| Années Folles 2-seat understudy run | Impractical (timeouts) | Clean, within baseline |
