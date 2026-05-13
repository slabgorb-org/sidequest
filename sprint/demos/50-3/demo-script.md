# Demo Script — 50-3

**Setup before the demo (5 min prior):**
```bash
cd ~/Projects/oq-2
just up
# Wait for server + client to confirm ready in logs
# Open http://localhost:5173 in a browser window
```

---

**Scene 1 — Slide 2 (Problem)** *(~90 seconds)*

Open the browser to the game board. If a live session is available, navigate to the Party Panel on the right side. Point out that only player characters are listed. If no live session is available, show the "before" screenshot of the panel with Carl the Cleric and no companions sub-section.

Say: *"The server logged that Donut was hired. The narrator confirmed it in the story text. But look at this panel — only Carl is here. From a player's perspective: did that hire actually stick, or is the AI making it up?"*

---

**Scene 2 — Slide 3 (What We Built)** *(~2 minutes)*

Switch to a session where companions have been recruited, or feed in a fixture:

```bash
# In a second terminal — send a test PARTY_STATUS frame to the running server
# to trigger a recruitment event in the caverns_sunden world
npx vitest run src/__tests__/companions-app-wire-integration.test.tsx
```

Point at the green test output. Then in the browser, trigger or show a session where Donut is already in the roster. The Party Panel now shows a **Companions** section beneath the player characters, with:
- Donut's initials in a gold avatar badge
- "Donut" as the name, tagged **NPC**
- Role: `mercenary` · bonded to: `Carl`

Say: *"The same message the server was already sending — we just started listening to the right part of it."*

---

**Scene 3 — Slide 3, continued: multi-companion and dismissal** *(~90 seconds)*

Show the multi-companion test result or walk through the fixture scenario:

```bash
npx vitest run --reporter=verbose src/__tests__/companions-party-status-wiring.test.tsx
```

Point to the test names: *empty roster → hidden*, *single companion → one row*, *two companions → two rows (Donut, then Katia)*, *roster cleared → section disappears*.

If live: narrate Donut being dismissed in session and the panel updating immediately.

**Fallback if browser demo fails:** Navigate to Slide 3 and describe the test output — "All four states pass: empty hides the section, populated shows it, dismiss clears it, ordering is stable."

---

**Scene 4 — Slide 4 (Why This Approach)** *(~60 seconds)*

Show the test file name `companions-app-wire-integration.test.tsx`. Explain: *"We have two layers of tests on purpose. One tests the panel in isolation. The second tests the full chain from the WebSocket message down to the panel prop — so we catch the case where the panel works fine but the wire going into it is broken. That's the class of bug we just fixed."*

---
