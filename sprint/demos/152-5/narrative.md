# Narrative

## Problem Statement
Problem: In a multiplayer Without-Number-rules combat session, the second player's submitted action was being assigned to the wrong character — the game engine thought the first player was trying to commit twice, rejected it as a duplicate, and the combat round **never resolved**. At the same time, the automated test that was supposed to catch this problem was itself accidentally reaching out to a live AI service during test runs, making it impossible to run reliably in isolation.

Why it matters: Any two-player table running a WWN-ruleset campaign (Caverns & Claudes, Heavy Metal / Barsoom, Elemental Harmony) would reach a permanent stalemate the moment the second player submitted their combat move. The round would hang silently — no damage resolved, no narration, no way forward — requiring a session restart. It also meant the safeguard test that should prevent this regression was quarantined and non-functional.

---

## What Changed
Think of the combat round as a sealed envelope: every player at the table slips their action into it, and only when the last envelope is sealed does the engine open them all and play out the fight.

The problem was that the post office was mis-sorting mail. When player 2 ("Vex Calder") dropped their envelope in the slot, the sorting code looked up the wrong name and delivered it to player 1's mailbox instead. Player 1's mailbox already had an envelope. The post office said "already full — rejected" and the round never completed.

Two things were fixed:

1. **The mailbox lookup** — the code that maps a player's login ID to their character's seat in the fight now correctly follows the `player_seats` table (a simple `player-1 → Rux`, `player-2 → Vex Calder` directory). Before, it was defaulting to the first character regardless of who submitted.

2. **The test isolation leak** — a part of the test setup was still wired to the live AI narration service even when the test explicitly substituted a fake narrator. A seam was made injectable so the test's substitute narrator is honored all the way down the call chain, with no silent fallback to the real service.

---

## Why This Approach
The engineering principle at work here is "bind, don't balance" — the same philosophy that governs this whole combat engine redesign. The seat-resolution fix doesn't touch the round-walk logic, the damage math, or the action allowlist. It fixes the plumbing one layer upstream: who is speaking, not what they're saying.

The hermeticity fix follows the same logic the solo-player tests already used: the narrator is a seam that can be substituted with a fake in tests. The MP path just hadn't threaded that substitution all the way down. Rather than adding a fallback or a workaround, the real transport call was moved behind the same injectable seam — making the MP test use exactly the same isolation technique as the working solo tests.

Both fixes are minimal and surgical. No existing combat behavior changes; native-ruleset packs are completely unaffected. The closed action allowlist remains closed. Every combat decision still emits an OTEL span so the GM panel can verify the engine is doing real math.

---

## Before/After
| | Before (152-5 bug) | After (152-5 fix) |
|---|---|---|
| **Player 2 submits action** | Resolved to Player 1's character seat | Resolved to Player 2's own seat via `player_seats` lookup |
| **Engine response** | `'Rux' has already committed` — barrier stays open | Barrier counts second unique commit, closes |
| **Combat round** | Never fires — permanent hang | Fires exactly once: `wwn.round.resolved` count = 1 |
| **Narration** | Never triggered | Fires after round resolves |
| **OTEL after both commits** | `wwn.round.committed` × 1, zero `wwn.round.resolved` | `wwn.round.committed` × 2, `wwn.round.resolved` × 1 |
| **Test status** | Quarantined behind `@pytest.mark.skip` + leaks to live AI SDK | Unskipped, hermetic, green |
| **Solo-player path** | Unaffected (different code path) | Unaffected — no regression |
