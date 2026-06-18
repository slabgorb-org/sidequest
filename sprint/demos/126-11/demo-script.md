**Setup (before presenting):** Have the SideQuest server running on a session that's been through at least one confrontation. OTEL Inspector open at `localhost:5173/#/dashboard`. Branch: `feat/126-11-drama-aware-length-limit`.

---

**Scene 1 — The Problem (Slide 2: Problem)**
*Timing: ~2 min*

Open the OTEL Inspector. Find a narration span from the current `develop` branch (or describe from memory). Point out: every `narrator.verbosity` span shows `cap_sentences: 8`, `cap_chars: 800`, regardless of what was happening in the game. Read the two narration examples side-by-side in the slide: a market visit and a boss reveal — same word budget.

> *Fallback if OTEL unavailable:* Show the Slide 2 before/after text comparison directly.

---

**Scene 2 — The Fix: Tiers in the GM Panel (Slide 3: What We Built)**
*Timing: ~3 min*

Switch to the `feat/126-11` branch in the running server. In the OTEL Inspector, locate a `narrator.verbosity_tier` span from a recent turn. Show the span attributes:

- `tier: "climax"` (or `"quiet"` / `"normal"`)
- `drama_weight: 0.82` (example from a confrontation turn)
- `cap_sentences: 12`
- `cap_chars: 1200`

Click a quiet turn's span — show `tier: "quiet"`, `cap_sentences: 6`. The GM panel now shows, for every single turn, exactly what budget the narrator was given and why.

> *Fallback if live OTEL not available:* Show the slide screenshot of the two span side-by-side (`tier: quiet` vs `tier: climax`).

---

**Scene 3 — Live Turn Comparison (Before/After slide)**
*Timing: ~3 min*

Trigger a quiet turn (e.g., "I look around the room") and a confrontation turn ("I attack the warlord") in sequence. Pull up the narration output for each. Point to the word counts. The confrontation response is measurably longer — not because the narrator was "told to be dramatic" in a vague way, but because the hard ceiling was raised from 8 to 12 sentences.

> *Fallback:* Use the pre-captured session transcript in the slide deck (Before/After tab).

---

**Scene 4 — The Lie Detector (Slide 4: Why This Approach)**
*Timing: ~2 min*

Return to OTEL. Explain: previously there was no way to tell whether the narrator was *actually* respecting a length limit or just happening to write short responses. Now the `verbosity_tier` span records what the engine decided, and the GM panel can cross-reference the actual narration length against the span's `cap_sentences`. The drama cap is now *verifiable*, not aspirational.

---