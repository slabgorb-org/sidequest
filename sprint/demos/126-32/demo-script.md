**Premise:** You're showing that the game now maintains consistent character identity across turns — from introduction to confrontation.

---

**Scene 1 — Title (Slide 1)**
*(30 seconds)*
Open on the project name and story title. Briefly set the stakes: "We fixed a class of bugs where the game forgot who it was talking about."

---

**Scene 2 — The Problem, Live Evidence (Slide 2)**
*(2 minutes)*
Show the before state using saved session logs from the `dust_and_lead` playtest:

- Pull up the terminal and run:
  ```bash
  just logs server | grep -A5 "fate.opponent.seeded"
  ```
- Point to a log line showing `created=True` and `description="Fate conflict opponent"` — the phantom. Explain: "This is the engine inventing a stranger because it couldn't find Henry Shaw in the wrong place it was looking."
- Show the GM dashboard at `localhost:5173/#/dashboard` — filter to the session, find the `fate.opponent.seeded` span with no identity fields populated. "The lie detector shows the binding never fired."

*Fallback if server isn't running:* Switch to Slide 2 and show the screenshot of the phantom span in the dashboard.

---

**Scene 3 — What We Built (Slide 3)**
*(3 minutes)*
Run a live session in `dust_and_lead` (or `wry_whimsy` Oz world):

```bash
just server
# In a second pane:
just client
```

Navigate to `localhost:5173`, connect as a player, start the `dust_and_lead` world. Run two turns:
- Turn 1: describe Henry Shaw threatening you ("Henry Shaw steps into the bar and draws.")
- Turn 2: engage in combat.

Then show the GM dashboard — filter to `npc` spans. Point to the `fate.opponent.seeded` event showing:
- `created: false`
- `name: "Henry Shaw"`
- `pronouns: "he/him"`

Say: "The engine found Henry Shaw in the pending pool, promoted him, and seated him as the exact opponent — not a Western Diamondback."

*Fallback if live session is unstable:* Show Slide 3 with the annotated dashboard screenshot from the green test run.

---

**Scene 4 — Why This Approach (Slide 4)**
*(1.5 minutes)*
No live demo needed. Explain with the timing diagram (see Slide 4):
- "Seating happens *before* the narrator runs. The character lives in a 'mentioned' pool, not the 'established' registry. That's why fixing the narration timing didn't help — we had to fix the seater."
- "The person recency guard mirrors a pattern already in the engine for creatures. We didn't invent a new mechanism; we applied an existing, tested idea to human NPCs."

---

**Scene 5 — Before/After (optional, if time allows)**
*(1 minute)*
Show the side-by-side (see Before/After section below). Walk through the two columns top-to-bottom. Let the contrast speak.

---

**Scene 6 — Roadmap (Slide: Roadmap & Integration)**
*(1 minute)*
Point to 126-38 as the deferred third piece. Note that the fix pattern (pool-consult before seating) also applies to the WN/d20 combat seater — a follow-up will extend it there.

---

**Scene 7 — Questions**
*(remaining time)*

---