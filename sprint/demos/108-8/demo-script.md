**Total runtime: ~8 minutes**

---

**Slide 1 — Title (0:00–0:30)**
Introduce the story: "Today we're showing how we restored combat in the Without Number ruleset after a complete outage. This is story 108-8."

---

**Slide 2 — Problem (0:30–2:00)**
Walk through the problem visually. Say: "After our last sprint's cleanup work, we ended up in a state where every single combat action in three genre packs crashed immediately. Not slowly, not intermittently — 100% of the time."

Show the test failure count: **78 e2e failures**, spanning:
- `caverns_and_claudes` (beneath_sunden world)
- `heavy_metal` (barsoom world)
- `elemental_harmony`

Read the error aloud: *"DiceDispatchError: unknown beat_id … available: []"* — "The engine was looking for actions on an empty list."

*Fallback: If you can't show a live terminal, stay on Slide 2 and read the error message from the slide.*

---

**Slide 3 — What We Built (2:00–4:30)**
Live demo portion. With a running server pointed at a WWN session:

```bash
# Start a session in heavy_metal / barsoom
just server

# In the game UI, connect as a character with a melee weapon equipped
# Initiate a combat encounter
# Submit an attack action
```

Show the result: narration fires, dice roll appears, damage is applied. No crash.

Then open the OTEL dashboard (`just otel`, navigate to `localhost:5173/#/dashboard`) and filter spans for `wn.native_scaffolding_suppressed`. Show it firing with the session ID. Say: "This span is our proof that the new engine path — not the old broken one — handled that attack."

*Fallback: If the server isn't available, show the Before/After slide (Slide 5) and the screenshot of the OTEL span in the slide deck.*

---

**Slide 4 — Why This Approach (4:30–6:00)**
No live demo here. Walk through the engineering reasoning. Key talking point: "We didn't change the rules. We changed which drawer the engine opens to find them. The dice math is identical — the fix is purely about how the valid actions are assembled."

Point to the analogy: "The 'drink a potion' action was already working this way. We extended a pattern that was already battle-tested."

---

**Slide 5 — Before/After (6:00–7:00)**
Show the side-by-side. Walk through it. Emphasize: "Before this fix, zero WWN combat sessions could proceed. After, all 78 previously-failing tests pass."

---

**Slide 6 — Roadmap (7:00–7:45)**
"This was the last blocker for story 108-3 — which is the gate for the full WWN combat pipeline. We'll cover that in the next increment."

---

**Slide 7 — Questions (7:45–8:00)**
Open floor.

---