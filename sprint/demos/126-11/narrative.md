# Narrative

## Problem Statement
**Problem:** The narrator spoke at the same length whether the party was strolling through a market or watching the villain reveal a world-ending plan. A hard ceiling of 8 sentences / 800 characters applied to every turn equally — the climactic reveal got the same word budget as "you walk to the door."

**Why it matters:** SideQuest exists to give a career GM (Keith) a real player experience — one good enough that a 40-year veteran can't see the seams. A narrator that can't breathe during a dramatic moment breaks that illusion immediately. Flat caps strangle the beats that *define* a story.

---

## What Changed
Think of it like a movie's score. A quiet scene gets a few notes; the final boss fight gets the full orchestra. Before this fix, the narrator was forced to play every scene with the same two-bar loop.

Now the game measures how tense and dramatic each moment is — a number it was *already computing* but never using for this purpose — and adjusts the narrator's word limit to match. Three tiers:

- **Quiet** (exploring a corridor, casual conversation): tighter cap, fewer words, faster pace
- **Normal** (standard adventuring turns): the baseline you've always seen
- **Climax** (active confrontation, big reveals, high-stakes moments): room to breathe — up to 50% more narration

The narrator's personal word-count preference (concise/normal/verbose) still works: drama scaling applies on top of whatever the player chose. A player who likes short responses still gets shorter responses; they just get proportionally *more* room during a climax than a stroll.

Every turn now emits a telemetry event recording which tier fired and what limits were set — so the GM panel's "lie detector" can verify the narrator is actually using the room it was given, not just improvising.

---

## Why This Approach
The drama signal already existed. `TensionTracker` had been computing a `drama_weight` value (0.0 to 1.0) every turn and using it to nudge the *soft* pacing suggestion. This change routes that same signal into the *hard* limit — the actual ceiling — for the first time.

This is the project's "wire up what exists" principle in action: no new plumbing, no new subsystems. The signal was there; it just wasn't connected to the right dial.

The three-tier design (quiet / normal / climax) keeps the logic a simple lookup table. Tuning the numbers — raising the climax ceiling, tightening the quiet floor — is a data change, not a code change. Future authors can adjust the feel of the narrator without touching the engine.

One cleanup was also necessary: the narrator's style guide had an old hardcoded rule ("BREVITY IS KING — maximum 2–4 sentences, always") that would contradict the new wider climax cap. That instruction now defers to the dynamic limit, so the narrator doesn't receive two contradictory directives in the same breath.

---

## Before/After
| | Before (126-11) | After (126-11) |
|---|---|---|
| **Hard cap, any turn** | 8 sentences / 800 chars | Quiet: 6/600 · Normal: 8/800 · Climax: 12/1200 |
| **Climax narration** | Truncated at 8 sentences — reveals cut mid-beat | Up to 12 sentences — scene has room to land |
| **Quiet narration** | 8 sentences (same as climax — wasteful) | 6 sentences — faster pacing for low-stakes turns |
| **Player concise mode at climax** | 4 sentences (flat) | 6 sentences (scales up proportionally) |
| **Player verbose mode at climax** | 10 sentences (flat) | 14 sentences (scales up proportionally) |
| **OTEL visibility** | No span recording the cap decision | `narrator.verbosity_tier` span: tier, drama_weight, cap_sentences, cap_chars |
| **`output_style.md` brevity rule** | "BREVITY IS KING — max 2–4 sentences" (contradicted a wide cap) | "BREVITY IS KING — *within the cap*" (defers to drama-scaled limit) |
| **Drama signal usage** | Drove soft pacing hint only | Drives **both** soft pacing hint and hard length cap |
