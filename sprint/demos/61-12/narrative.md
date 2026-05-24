# 61-12

## Problem

**Problem:** The AI narrator was told to write NPCs into a field called `npcs_met` in its structured output, but the rest of the system was looking for a field called `npcs_present`. The two halves of the pipeline never connected. On top of that, a hidden safety net in the code quietly papered over the mismatch — meaning the bug was invisible in normal operation. Non-player characters would silently vanish from game state with no error, no warning, and no indication anything had gone wrong.

At the same time, every narrator instruction file — the rulebook the AI consults before writing each turn — had ballooned to roughly 6,700 tokens of text. On a subscription AI API, you pay per token. On a game with real-time turns, every wasted token is latency. Most of that bulk was repetition: four nearly-identical paragraphs saying the same thing about item tracking, rules marked CRITICAL that weren't actually critical, and a full block of magic-system rules sent on every single turn — even when the current game world has no magic at all.

**Why it matters:** SideQuest's narrator has to produce correctly structured game data every turn, not just good prose. If it writes the wrong field name, characters stop picking up items, meeting NPCs, and advancing the story — silently, invisibly, while the session looks completely normal. The performance cost compounds across a real gaming session: a group of four players running sixty turns burns roughly 240,000 unnecessary tokens that didn't need to be there.

---

## What Changed

Think of the AI narrator as a chef who follows a recipe card before cooking each dish. This story rewrote that recipe card in two ways.

**The bug fix:** The recipe card had a typo. It said "put the result in bowl B" but the kitchen only has bowl A. Every dish came out missing an ingredient, quietly, with no one noticing. We corrected the typo, and removed the workaround someone had quietly taped to the counter that was masking the problem.

**The compaction:** The recipe card was also six pages when it only needed to be three. It had:
- Four separate paragraphs about how to handle items, all saying nearly the same thing — replaced with one compact table
- Eighteen places marked **CRITICAL** or **MANDATORY**, so many that cooks had started ignoring them — trimmed to four genuinely critical rules
- A full page of magic-system rules that fired even on non-magic games, like including a sushi guide in a BBQ restaurant's daily briefing — moved to a separate section that only appears when the game world actually has magic
- Repeated summaries at the end restating rules already stated at the top — deleted

Result: from roughly 6,700 tokens down to about 3,300. Non-magic games (like *Tea & Murder*) save around 3,400 tokens every single turn.

---

## Why This Approach

**On the field-name fix:** The system had 25+ places in the codebase all using `npcs_present` as the canonical name. Renaming all of them would have been a much larger change with more risk. The drift was in one place — the narrator's instruction text. Fixing the text and removing the silent fallback that was hiding the problem was the minimal, correct change. The project has a firm rule: "no silent fallbacks." A missing NPC field should surface as an empty roster that OTEL telemetry catches — not as a quietly-resolved alias that makes the bug invisible.

**On the magic conditional:** The magic rules were always-on because they were embedded in the main instruction file. Moving them into a conditional block that only fires when `magic_state is not None` reused the same gate the system already uses for magic game-context injection. One mechanism, one chokepoint — no new detection logic invented. This is how the project handles all conditional prompt sections.

**On the banner demotion:** Nineteen items marked CRITICAL is a boy-who-cried-wolf situation. When everything is critical, nothing is. Reducing to four survivors means the AI actually treats the remaining four as genuinely load-bearing rules, which is the intent.

**On the token count:** The story description targeted ≤ 2,000 tokens. The actual pre-change baseline turned out to be ~6,700 tokens — not the ~3,600 the story estimated. Getting to 2,000 from 6,700 would have required deleting rules, which the acceptance criteria explicitly forbade. The team landed at ~3,300 tokens — a 47% reduction, with per-turn savings of 2.26× the minimum target. The functional goal (API cost reduction per turn) was exceeded; the absolute ceiling number in the spec was a proxy that was based on a bad baseline measurement.

---
