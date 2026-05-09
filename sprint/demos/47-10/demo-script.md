# Demo Script — 47-10

**Pre-demo setup (5 min before):**
```bash
cd ~/Projects/oq-1
just up
# Wait for server, client, and daemon to be ready
# Navigate browser to http://localhost:5173
# Open a second tab to http://localhost:8765/dashboard (GM/OTEL panel)
```

---

**Scene 1 — Title (Slide 1)**
*Time: 0:00–0:30*
Open with the game client running. Show the title slide. Say: "We're going to watch a Mage prepare spells for the first time, and then watch the game actually enforce that."

---

**Scene 2 — Problem (Slide 2)**
*Time: 0:30–1:30*
Show old behavior in words only (no live demo needed — the old code is gone). "Before this story, a Mage could cast any spell any time. There was no spell book, no preparation ritual, no slot economy. For a genre built on Gygax's resource management, that's a dealbreaker."

Fallback: Slide 2 alone if audio/video issues.

---

**Scene 3 — What We Built (Slide 3)**
*Time: 1:30–4:00*

Start a new session in the Caverns & Claudes / Sünden world. Select or create a Mage character.

**Step 3a — Session init:**
Point to the character sheet. The magic panel should already be visible with known spells populated and slots showing (e.g., "2 / 2 L1 slots remaining"). Say: "This is automatic. The moment the session loads, the Mage's spell book is seeded from the class definition — no clicks, no configuration."

Exact thing to show: `spell_slots_l1_<actor>` ledger bar reading `2/2`, `known_spells` list showing Sleep, Magic Missile, and Charm Person (or whatever the starting_known_spells 2 resolved to).

Fallback if session init is broken: Show Slide 3 screenshot of the expected panel state.

**Step 3b — Prepare spells:**
Type as the player: `I prepare Sleep and Magic Missile`
Expected: Prepared list updates to show Sleep (L1) and Magic Missile (L1). OTEL dashboard shows `learned_v1.prepare` span firing with `actor_id`, `spell_id`.

Terminal to verify OTEL is firing:
```bash
just otel
# or watch logs
tail -f /tmp/sidequest-server.log | grep "learned_v1"
```

Fallback: Show OTEL span screenshot from Slide 3.

**Step 3c — Cast Magic Missile (null-stat auto-apply):**
Type: `I cast Magic Missile at the goblin`
Expected: Hit resolves immediately, no save roll, damage applied. GM panel shows `innate_v1.cast` span with `save_skipped: true`.

Say: "Magic Missile doesn't ask for a saving throw. The system knows that. No dice, no negotiation — it just hits."

**Step 3d — Attempt to cast unprepared spell:**
Type: `I cast Charm Person`
Expected: The prepared spell list in the UI pulses (CSS animation, ~600ms), "Charm Person" appears struck-through in the cast-attempt log, narrator responds in-fiction ("your thoughts reach for the enchantment, but the words aren't there").
OTEL shows `rejected_unprepared` decision value.

Say: "No modal. No freeze. The game stays moving."

**Step 3e — Cleric divine favor bar (Slide 3 continued):**
Switch to or show a Cleric character. Point to the divine favor bar — bidirectional, showing threshold markers at +0.7 (pious) and -0.7 (fallen). Show Turn Undead button. Say: "The Cleric gets a second resource to manage: standing with their deity."

Fallback: Show Slide 3 screenshot of Cleric panel.

---

**Scene 4 — Why This Approach (Slide 4)**
*Time: 4:00–5:30*
No live demo needed. Walk through the three engineering choices on Slide 4: pulse-not-popup, session-start seeding, OTEL on every cast. One sentence each.

---

**Scene 5 — Before / After (optional slide)**
*Time: 5:30–6:30*
Side-by-side: old character sheet (no magic panel, no slot bars) vs new (full magic block). If screenshots are available, show them. Otherwise skip this slide.

---

**Scene 6 — Roadmap (Slide: Roadmap & Integration)**
*Time: 6:30–7:30*
Brief. Point to what's coming: rest flow, higher-level spell slots, the Sebastien-tier numeric overlay.

---

**Scene 7 — Questions (Slide: Questions)**
*Time: 7:30+*
Live: keep the OTEL dashboard visible so mechanics questions can be answered with real data.

---
