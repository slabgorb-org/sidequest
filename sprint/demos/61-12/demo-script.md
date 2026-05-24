# Demo Script — 61-12

**Total runtime:** ~10 minutes. Slides 1–4 are the story; the live demo portion is 3–4 minutes max.

---

**Slide 1 — Title (30 seconds)**

"Story 61-12 ships today. Two things: we fixed a silent NPC bug, and we cut the narrator's per-turn token spend roughly in half. Let me show you both."

---

**Slide 2 — Problem (2 minutes)**

Walk through the two problems:

1. *The field name bug.* "The narrator was writing NPCs into a field called `npcs_met`. The parser was reading a field called `npcs_present`. Those never matched. There was a hidden fallback in the code silently resolving the mismatch — which is exactly the kind of invisible failure this project bans."

2. *The bloated instruction file.* "Before this story, the narrator's formatting instructions were roughly 6,700 tokens. About half of that was redundant: repeated paragraphs, banners marked CRITICAL on things that aren't actually critical, and a full magic ruleset that fired on every turn even in magic-free games like Tea & Murder."

If the live demo environment isn't ready, show the Before/After slide instead.

---

**Slide 3 — What We Built (3–4 minutes, includes live demo)**

Show the test suite passing. At the terminal:

```bash
cd /Users/slabgorb/Projects/sidequest-server
uv run pytest tests/agents/test_61_12_output_format_compaction.py -v
```

Expected output: **39 passed, 0 failed.** Point to the test names:
- `test_output_only_prose_has_zero_npcs_met_references` — proves the typo is gone
- `test_orchestrator_parser_has_no_npcs_met_silent_fallback` — proves the hidden workaround is gone
- `test_critical_and_mandatory_banner_count_under_ceiling` — proves we're at ≤ 4 banners
- `test_output_only_prose_under_byte_budget` — proves the file is inside the size target
- `test_magic_output_rules_section_absent_when_magic_state_none` — proves magic rules don't fire on non-magic worlds

Then show the full suite:

```bash
uv run pytest -v --tb=no -q
```

Expected: **7,538 passed / 0 failed / 375 skipped.**

*Fallback if tests won't run:* Skip to Slide 4 and reference the token table in the Before/After slide with concrete numbers.

---

**Slide 4 — Why This Approach (1 minute)**

Key point: "We didn't invent new mechanisms. The magic conditional reused the exact same gate the system already uses for magic context injection — one chokepoint, not two. The field name fix was one corrected line of text and removal of a safety net that was hiding the bug. The project principle is: fail loud, not silently."

---

**Before/After slide (1 minute)**

Read off the numbers from the table (see Before/After section below). Emphasize: "On a Tea & Murder session, that's 3,389 tokens saved per turn. Sixty turns, four players — that's over 200,000 tokens not sent to the API."

---

**Roadmap slide (30 seconds)**

"This is one piece of the Epic 61 prompt-slimming work. The next levers are snapshot slimming — reducing how much game-state JSON is serialized per turn — and eventually the RAG store for lore retrieval. Each piece is independent and can ship without blocking the others."

---

**Questions.**

---
