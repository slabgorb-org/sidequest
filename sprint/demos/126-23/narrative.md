# Narrative

## Problem Statement
**Problem:** The GM panel's real-time monitoring screen — the "lie-detector" that operators use to verify the game engine is actually running mechanics instead of just improvising narration — would randomly switch to showing a *different game session* whenever any concurrent process emitted a signal. The operator watching game session A would suddenly see session B's activity, or worse, see "Waiting for first turn…" on a session that had already taken a dozen turns.

**Why it matters:** SideQuest's automated headless tests run alongside live playtest sessions routinely. When that happens, the monitoring panel becomes completely unreliable — operators lose the ability to verify that the engine's combat math, trope triggers, and encounter logic are actually firing. The whole point of the GM panel is to catch the narrator "winging it" (generating plausible narration with zero mechanical backing). If the panel can't be trusted during concurrent runs, that safety net disappears exactly when it's most needed.

---

## What Changed
Before this fix, the monitoring panel was like a TV tuned to "whatever channel happened to speak last" — whichever game session emitted any signal would hijack the display for everyone watching.

We made two changes:

1. **On the dashboard (front-end):** Added a session picker so the operator can pin the specific game session they're watching. Once pinned, no other session can steal the screen — even if a dozen concurrent tests are flooding signals, the operator sees only their chosen session.

2. **On the server (back-end):** Fixed a memory buffer that was shared across all sessions. Previously, a noisy session (like a fast automated test) could push a quiet session's history out of memory before the operator even connected to watch it — causing the dreaded "Waiting for first turn…" on a session that had already completed turns. Now every session gets its own private memory slot.

---

## Why This Approach
The fix was deliberately minimal. The monitoring websocket already attached a session label (`session_slug`) to every signal it broadcast — the plumbing was there. What was missing was (a) an operator control to say "I want to watch *this* session" and (b) stable per-session storage on the server so that history doesn't get evicted by a noisy neighbor.

Rather than redesigning the transport layer (which would have been a much larger, riskier change for a 3-point bug), the team extended the existing scoping logic: the dashboard already knew how to filter signals by session, it just had no way to accept an operator's choice. Adding that choice — a dropdown, a pin, and a "clear pin" option — was the minimal honest fix. The server side added per-session ring buffers (each session gets up to 2,000 events of private history, capped at 64 concurrent sessions) instead of one big shared buffer everyone competed for.

---

## Before/After
| Dimension | Before | After |
|---|---|---|
| Live header | Showed whichever session emitted last — often a concurrent headless test | Shows the operator-selected session; a concurrent session cannot steal it |
| Timeline on connect | "Waiting for first turn…" if a noisy session evicted the quiet one's history | Shows all prior turns immediately, regardless of concurrent noise |
| Session picker | "Live" was a single auto-follow option (no operator control) | "Live sessions" group with one entry per active session; auto-follow available as default |
| Concurrent test impact | Any concurrent run made the panel unusable | Concurrent runs are invisible to the pinned session's view |
| Server replay buffer | One shared `deque(maxlen=2000)` — noisy session evicts quiet session | Per-session ring buffers (up to 2,000 events each), capped at 64 sessions, LRU |
| Lie-detector reliability | Unusable during concurrent runs (routine for headless tests) | Trustworthy under concurrency; AC1, AC2 passing in 56/56 tests |
