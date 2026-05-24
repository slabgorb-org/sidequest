# Demo Script — 60-7

**Total runtime: 12 minutes.** Presenter needs: a running `tea_and_murder/glenross` session, the GM dashboard open, and the captured JSON payload diffs from the diagnostic run.

---

**Slide 1: Title — "Fixing the Cache Leak" (0:30)**
Open on the title slide. One sentence: "We found out why the narrator was charging full price on every turn and fixed it."

---

**Slide 2: Problem — "What Was Broken" (2:00)**
Reference the 2026-05-23 baseline session (`annees_folles`). Show: average cost per turn was **$0.165**. Explain: the 60-4 fix was supposed to drop that to $0.04. It didn't. Every tool-use turn — which is every real narrator turn — was resetting the cache as if it had never seen the game before.

Show the lie-detector concept: "We had no alarm. We only found out this was broken during a live playtest."

*Fallback if live session not available:* Stay on Slide 2 and walk through the cost table verbally.

---

**Slide 3: Diagnosis — "Before We Fixed Anything, We Looked" (3:00)**

Show the two captured JSON payload files on disk:
```
ls /tmp/sidequest_cache_diagnostic/
# narrator_turn_iter1_<timestamp>.json
# narrator_turn_iter2_<timestamp>.json
```

Open both files side by side. Point to the diff:
- `iter1` has `"anthropic-beta": "extended-cache-ttl-2025-04-11"` in the headers.
- `iter2` (the follow-up call inside the tool loop) **does not**.
- Both files show `cache_control: {"type": "ephemeral", "ttl": "5m"}` on the last user message block.

"This diff is the bug. The second call — the one after the narrator asks the game engine for a result — forgot to send the header that tells Anthropic 'use the 1-hour cache.' So Anthropic treated it as a cold call and charged accordingly."

*Fallback:* Show a pre-captured screenshot of the diff in the slide deck.

---

**Slide 4: The Fix — "One Header, Every Call" (2:00)**

Plain language: "We added three words in the right place. The extended-TTL header now travels with every call inside the tool loop, not just the first one."

No code on this slide. One diagram: outer call → tool result → continuation call, with the header shown on both arrows.

---

**Live Demo: The Lie-Detector in Action (3:00)**

Start a fresh `tea_and_murder/glenross` session. Play 3 turns. Open the GM dashboard (`just otel` from the orchestrator root, or navigate to `localhost:8765/dashboard`).

```bash
just otel
```

Point to the `narration.turn` span. Show:
- Turn 1: `cache_creation.ephemeral_1h_input_tokens > 0` (expected — cold write)
- Turn 2: `cache_creation.ephemeral_1h_input_tokens == 0`, `ephemeral_5m_input_tokens == 0` (expected — cache hit)
- The `narrator.cache.both_writes_fired` span does **not** appear.

"If that red alarm had fired on turn 2, we'd know the fix regressed. It didn't fire. That's the test passing in production."

Show the per-turn cost estimate in the span: should read ≤ $0.04 on turns 2+.

*Fallback if live session fails:* Switch to Slide "Before/After" showing the pre-captured span screenshots.

---

**Slide 5: Before/After Cost Table (1:00)**
Point to the numbers (detailed in Before/After section below). One sentence: "Average per-turn cost dropped by roughly 75% on a warm session."

---

**Slide 6: Roadmap (0:30)**
Transition to roadmap section. Hand off to roadmap slide.

---

**Questions (remaining time)**

---
