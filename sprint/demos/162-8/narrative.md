# Narrative

## Problem Statement
**Problem:** Two pieces of "in case we need it later" code had been sitting in the game engine, doing nothing, for a while. One was a helper function that its own internal notes admitted had "no caller yet" — written to be hooked up once a related feature landed. The other was a name-generation tool that looked fully wired into the system everywhere except the one place that actually mattered, so every time it ran, it silently returned nothing.

**Why it matters:** Code that looks connected but isn't is worse than no code at all — it fools engineers into thinking a capability exists when it doesn't, and it adds weight (more files, more tests, more places to check) with zero payoff. This cleanup follows the team's standing rule: don't leave empty shells lying around — either finish wiring them up, or remove them. Since neither piece had a live consumer, removal was the right call. This was the closing chore in a longer initiative (Epic 162) to unify how non-player characters and creatures get created in the game, so leaving loose ends here would have undercut the "one clean system" goal of the whole effort.

## What Changed
Think of it like a construction project where the crew installed two utility hookups "for later" — a pipe stub capped off in a wall, and a light switch wired to nothing. Nobody ever ran the rest of the plumbing or wiring to them. This story sent someone through to check: is anything actually going to use these? The answer was no in both cases, so the stubs got removed rather than left to confuse the next person who opens up the wall.

Concretely:
1. **`resolve_encounter_from_trope`** — a function written as a placeholder for a future encounter-resolution feature. That future feature did eventually get built, but it took a different path entirely and never called this function. It was deleted, along with its dedicated test file that only existed to test the dead function.
2. **`generate_name` tool + its `name_generators` slot** — a tool meant to let the game's narrator ask for freshly generated character names. It was registered and available everywhere except the one spot where it needed a live data feed to actually work, so it always came back empty-handed. Meanwhile, a separate, actively used naming system was already doing this job correctly. The redundant, non-functional tool was removed entirely — the field, the tool file, and its tests.

Nothing about how the game behaves for players changed. This is exclusively "cleaning out things nobody was using."

## Why This Approach
The team runs on two simple rules here: don't build fake front-doors ("no stubbing" — if it's not finished, don't leave a shell of it around), and don't silently paper over gaps (if something's supposed to work but doesn't, that should be loud and obvious, not quietly ignored).

Both pieces of code failed those rules in a low-stakes way: they *looked* like real capabilities but were actually inert. The team could have instead spent effort finishing the wiring on both — but investigation showed that in each case, a different, better system had already taken over the job. Finishing the wiring would have created a second, competing way to do the same thing, which runs directly against the larger goal of this initiative (consolidating multiple overlapping ways of creating game characters down to one clean system). Removing the dead code was simpler, safer, and aligned with where the system is headed.

Before removing anything, tests were written first that specifically check "this code is gone" — so if anyone ever re-adds a broken version of either piece by accident, the tests will catch it immediately.

## Before/After
| | Before | After |
|---|---|---|
| `resolve_encounter_from_trope` | Present in code, zero callers, docstring admitted it was waiting for a feature that never used it | Fully deleted, along with its dedicated (now-pointless) test file |
| `generate_name` tool | Registered and visible to the narrator, but its data feed was never connected — always returned an empty result | Tool, its data-feed field, and its 24 tests all removed |
| Narrator's available tools | 41 | 40 |
| Test coverage for "is this dead code really gone" | None | 4 new tests explicitly proving both removals |
| Total test suite | 14,651 tests passing (with dead code present) | 14,651 tests passing (dead code confirmed absent) |
| Lines of code | — | 713 removed, 85 added (mostly new proof-of-removal tests) |
| Reviewer verdict | — | Approved, zero blocking issues; one minor leftover comment (an outdated "41" reference) flagged for a quick follow-up fix |
