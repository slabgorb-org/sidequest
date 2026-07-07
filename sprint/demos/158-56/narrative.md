# Narrative

## Problem Statement
Problem: Players whose characters have special mutant powers had no way to actually pick which power to use in the middle of a fight. The game's rules engine already knew how to process a mutation being used — but the on-screen combat panel simply had no button or menu for it. Why it matters: without this piece, a player with a mutant character would hit a dead end at the exact moment the game gets interesting — either the action would fail outright, or it would quietly get treated as a generic, flavorless attack instead of the specific power the player wanted to use. For a game built around giving players real, informed choices in combat, that's a broken promise at the most visible moment of play.

## What Changed
Think of it like a restaurant that already knows how to cook a dish, but the menu never got printed — the kitchen (the game server) was fully ready to handle a mutant power being used in a fight, but the "menu" handed to the player (the combat overlay) never listed what powers they owned or let them pick one.

This update prints that menu. During a fight, when the moment comes for a mutant character to use a power, a picker now pops up showing every power that character owns — each with its name and how much it costs to use (a resource called "Strain"). The player clicks the one they want, and that specific choice now travels all the way from their screen to the server, which resolves it correctly.

Two things had to happen to make this real, not cosmetic:
1. **The server had to start sharing the "menu" at all.** It turned out the list of a character's owned powers never left the server in the first place — so the team added a small, targeted upgrade so the game now sends that list to the player's screen, the same way it already does for spellcasters.
2. **The picker itself had to be built** in the combat screen, styled and wired the same way as the existing spell-picker feature spellcasters already use — so mutant and magic characters now get the same quality of experience.

Along the way, testing surfaced a nasty edge case and the team fixed it before shipping: if a content creator ever renamed or removed a mutation that a player's saved character already owned, the original version of this feature would have crashed the game for the *entire table*, not just that one player. That's now handled gracefully — the game skips the outdated entry quietly in the background and keeps playing, while still logging the mismatch so it can be cleaned up later.

## Why This Approach
The team deliberately copied an already-proven pattern rather than inventing something new: this game already has a "spell picker" for magic-using characters, built and battle-tested earlier. Mirroring that exact pattern for mutations — same visual approach, same wiring approach — meant lower risk, faster delivery, and a consistent feel for players no matter which power system their character uses.

When early testing revealed the feature was scoped incorrectly (it assumed data that doesn't actually reach the player's screen), the team paused, got sign-off to expand the fix to include the small necessary server change, and did it as one coordinated piece of work rather than shipping something that would only render an empty, broken-looking menu.

The crash-on-stale-data issue was caught specifically because the team tests for exactly this kind of "what if the world changes underneath a save file" scenario — a recurring risk in a game where new content (new powers, new monsters, new items) is added continuously by multiple people. Fixing it the same way a similar situation is already handled elsewhere in the game keeps the codebase's safety behavior consistent, rather than introducing a second, different way of failing.
