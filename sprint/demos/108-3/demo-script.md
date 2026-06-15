**Audience:** Product stakeholders, non-technical. Run time: ~8 minutes.

---

**Slide 1: Title (0:00–0:30)**
Open with the slide. One sentence: "We cleaned up leftover combat instructions from three genre packs so the WN engine fully owns the fight."

---

**Slide 2: Problem (0:30–2:00)**
Walk through the problem slide. Key talking point: show the before-state (Slide 5, Before column) — a raw snippet of the old `caverns_and_claudes/rules.yaml` Dungeon Combat block, five beats and `resolution_mode: beat_selection` visible. Say: "The WN engine ignores all of this. It supplies its own combat menu — attack, move, item, cast — at runtime. These 50 lines had been sitting here doing nothing since the WN port landed."

---

**Slide 3: What We Built (2:00–3:30)**
Show the After column (Slide 5). The same Dungeon Combat block now has three lines: `win_condition: hp_depletion`, the opponent stat block, and `opponent_damage: {dice: "1d8", bonus: 0}`. Say: "That's the whole definition. The engine fills in the rest. The enemy still hits for 1d8 — the damage is authored content, not something the engine improvises."

Live terminal demo (optional, if server is running):
```bash
cd ~/Projects/sidequest-content
uv run sidequest validate pack caverns_and_claudes
```
Expected output: `PASS — 0 errors, combat beats=0, hp_depletion, opponent_damage=1d8`

**Fallback if terminal fails:** Stay on Slide 5 and read the validation result aloud from the session notes: "All three packs passed — zero errors, zero leftover beats."

---

**Slide 4: Why This Approach (3:30–5:00)**
Reference the "Bind the Ruleset, Don't Balance It" doctrine. Say: "When SideQuest adopts an external ruleset like Without Number, the ruleset owns combat. Our job is to wire it up, not to write competing rules alongside it. Deletion was the right move — anything added here would contradict the engine."

Point out the scope guardrail: "We only touched combat definitions. The chase and negotiation systems still use SideQuest's own engine, and those files weren't touched — zero lines changed in any chase or negotiation definition."

---

**Slide 5: Before / After (5:00–6:00)**
This slide is already cued from the walkthrough. Linger here. Highlight: before = ~50 lines of dead beat config per pack × 3 packs = ~150 lines of orphaned content. After = 3-line combat definition. Net change: −222 lines across six files, no additions.

---

**Slide 6: Roadmap (6:00–7:30)**
See Roadmap section below. Key points: this unlocks WN combat working cleanly in beneath_sunden, evropi, long_foundry, and barsoom. Follow-up work (re-anchor signature ability descriptions, add live-pack wiring test) is identified and scoped.

---

**Slide 7: Questions (7:30–8:00)**
Open floor.

---