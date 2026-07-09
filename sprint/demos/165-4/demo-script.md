**Total runtime: ~6 minutes**

**Scene 1 (0:00–0:30) — Slide 1: Title**
Presenter opens on the title slide ("Protocol Adjudication Echoes: Putting the Math on Screen"). One line: "Today I'm showing you what happens when a player attacks or moves in SideQuest — and why they can now see the numbers behind it."

**Scene 2 (0:30–1:15) — Slide 2: Problem**
Walk through the problem statement above. Show the "before" framing: a roll result that just says hit/miss with no supporting numbers. Emphasize the audience it serves: players who want to verify the game is actually doing math, not just narrating.

**Scene 3 (1:15–3:00) — Slide 3: What We Built (LIVE DEMO)**
Open two terminal panes and run:
```
just server
just client
```
Wait for both to report ready (server on :8765, client on :5173). In a browser, navigate to `http://localhost:5173`, join the running session, and select a character equipped with a melee weapon.

- Target an enemy positioned 2 cells away and roll an attack.
- Point to the resolution card and read the new line aloud: **"· melee range · 2 cells"** — call out that this is a real, calculated distance, not a placeholder.
- Switch to the tactical grid view. Point to the movement chip near the player's token, showing **"0/5"** cells used/available.
- Move the character 2 cells; the chip updates live to **"2/5"**.
- Attempt to move beyond the remaining budget; show the denial banner explaining the move isn't valid.

**Scene 4 (3:00–3:45) — Slide 4: Why This Approach**
Cut back to slides. Explain the "receipt, not a new register" analogy — the math already existed; this story made it visible. Then show the one-slide version of the QA story: "Our first attempt shipped the display without the wiring underneath. Our review process caught it, sent it back, and verified live data before we approved it." This is a good trust-building beat for a non-technical audience — it shows the safety net worked.

**Scene 5 (3:45–4:30) — Optional Before/After slide**
Side-by-side: left panel shows the old resolution card (hit/miss only); right panel shows the new card with the range/distance line. Same for the tactical grid: left with no budget indicator, right with the chip and denial banner.

**Scene 6 (4:30–5:15) — Roadmap slide**
Cover the Roadmap & Integration section below.

**Scene 7 (5:15–6:00) — Questions**
Open floor.

**Fallback instructions:** If the live demo environment fails to start or the browser session doesn't connect, skip directly to the Before/After slide (Scene 5) and narrate the same example values from there: *"· melee range · 2 cells"* on the attack card, and *"2/5"* on the movement chip. These are the exact values verified in our automated test suite, so they're safe to present as ground truth even without a live run. If asked for proof of live wiring, offer to follow up with a recorded clip rather than debugging live on stage.