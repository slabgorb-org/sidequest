# Narrative

## Problem Statement
**Problem:** During a live playtest of SideQuest's Fate Core genre, players reported that poker and card-game scenes were "totally broken and not engaging" — triggering a table game produced nothing; the encounter simply never started, leaving players with no ante, no seats, and no cards.

**Why it matters:** Table games (poker in the Spaghetti Western pack, auction mechanics in Tea & Murder, and the War Rig crew game in Road Warrior) are showcase moments — high-stakes, multi-player scenes where the narrative tension is mechanical, not just narrated. If a poker scene silently fails to start, the GM gets Claude narrating *around* a game that isn't happening, which is exactly the failure mode the engine is designed to prevent. For a group where at least two players are mechanics-first, a broken card game isn't just a bug — it's the absence of the feature they came for.

---

## What Changed
Think of SideQuest's game engine like a railroad switchyard. When a scene calls for a card game, an "intent router" reads the situation and throws the right switch — directing the train down the poker track so a table, seats, and an ante can be set up. 

A previous bug (fixed in story 126-9) had broken that router entirely: it was getting stuck in a loop and returning nothing. When the router returned nothing, every switch in the yard stayed neutral — including the poker switch. The card table never materialized, even though the card-game engine itself was perfectly intact the whole time.

This story's job was to **confirm the poker track is live again** now that the router is repaired, and to lay down a permanent sensor on that track so the system will immediately alert us if anything ever blocks it again.

What was delivered: four automated tests that simulate the exact signal the router sends when it decides "this is a poker scene" and verify that the signal reliably seats a full table — correct number of seats, win condition set to a showdown, pot slots open, sealed-commit loop armed. These tests also verify the inverse: if no opponent is available, the game declines gracefully instead of silently producing a broken state.

No production code had to change. The engine was fine. The tests are the deliverable.

---

## Why This Approach
The directive going in was explicit: *don't hunt*. The previous investigation had already traced the card-game failure to an upstream cause (the router), not to the card-game engine. Pre-emptively digging through table mechanics without evidence would have been the classic "fixing the wrong thing" trap — time-consuming, risky, and unnecessary.

Instead, the team wrote tests against the precise contract that the router-to-table seating path must satisfy. This approach:

1. **Proved the diagnosis was correct** — once the router fires, the table seats. No additional fix needed.
2. **Locked the contract permanently** — the four new tests will catch any future regression at the exact seam where the router hands off to the table engine, regardless of what other changes happen upstream.
3. **Used the real configuration** — the tests run against the actual Fate ruleset binding that the Spaghetti Western poker game uses in production, not a legacy test configuration that no live pack ever touches. If those tests pass, the real game works.

One additional quality finding was surfaced: the *resolution* half of table games (showdown payouts, pot awards, fold detection) is still only tested against an obsolete ruleset that no pack uses. That gap is filed as a follow-up story — not a blocker, but a real coverage hole worth closing.

---

## Before/After
| | Before (router degraded) | After (router restored + regression locked) |
|---|---|---|
| **What the router returned** | `dispatch_package = None` | Valid `ConfrontationDef` with `resolution_mode = table_resolution` |
| **Seating call** | `instantiate_table_encounter()` never reached | Called at `narration_apply.py:5450`; encounter materialized |
| **Encounter state** | `encounter = None` | Seated table: PC + opponent, win condition = `table_showdown`, pot slots open |
| **Player experience** | Narrator improvised "poker-flavored" narration with no mechanical game beneath it | Full antes/seats/sealed-commit loop present; real card game running |
| **OTEL signal** | No `table.dealt` span — GM panel showed nothing | `table.dealt` span fires with `seat_count = 2`, `game_kind = poker` |
| **Failure mode on no opponent** | Silent — encounter stayed None with no log | Graceful decline + `encounter.no_opponent_available` span emitted |
| **Test coverage** | None at this seam | 4 passing regression tests; production Fate binding; real dispatch bank wired |
