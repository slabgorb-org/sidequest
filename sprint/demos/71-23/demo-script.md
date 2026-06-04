**Setup required:** SideQuest server running with Anthropic SDK backend (default). Solo session active. Chrome DevTools Network tab open to WebSocket frame view optional.

---

**Slide 1 — Title:** Introduce: "Today we're showing what happens when the narrator stops making players wait."

---

**Slide 2 — Problem (timing: ~60s):**
Open the live game. Start a solo session. Submit a player action (e.g., "I look around the room."). Watch the narration panel. Point out: the spinner runs, nothing appears, then the full paragraph pops in all at once.

Say: "Every turn in SideQuest looks like this today. The AI has been typing the whole time — we just couldn't see it."

*Fallback if server is slow:* Show Slide 2 (Problem) with a screen recording of the blank-wait behavior.

---

**Slide 3 — What We Built (timing: ~90s):**
Switch to the patched branch. Start a new solo session. Submit the same action: "I look around the room."

Point to the narration scroll as words appear one group at a time. Say: "The narrator is writing this live. Every chunk — typically 3–10 words — arrives as a separate real-time message. The player sees it as it's being written."

Show the OTEL GM panel (`/dashboard` on the server). Point to the `narration.turn` span and highlight the `narration.turn.delta_count` attribute — it will show a number like `47` or `63`, representing the number of individual text chunks that streamed during that turn. Say: "This is our lie-detector. If this number is zero, the narrator isn't streaming — it's faking. Today it's real."

*Fallback if live demo fails:* Show Slide 3 with a screen recording captured earlier, plus a screenshot of the OTEL span with `delta_count: 52`.

---

**Slide 4 — Why This Approach (timing: ~45s):**
Say: "Both ends of this connection were already built — the server knew how to generate streaming chunks, the browser knew how to display them. The missing piece was one line of wiring. But before it shipped, code review caught a subtle issue: in a multiplayer room, different players see different versions of events. Streaming raw text mid-sentence would have sent the wrong version to the wrong player. We caught it, wrote a test that proved it, fixed it — and now multiplayer is explicitly protected."

*Fallback:* Slide 4 (Why This Approach) has the one-line summary.

---

**Before/After (optional, timing: ~20s):**
Side-by-side: left panel shows the blank-wait behavior, right panel shows streaming. No commands needed — just two screen recordings.

---

**Roadmap slide:** See Roadmap section below.

---

**Questions:** "The OTEL panel shows `delta_count` per turn — anyone want to see what a long fight scene looks like versus a short ambient moment?"

---