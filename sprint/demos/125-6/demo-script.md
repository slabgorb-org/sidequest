**Total runtime:** ~6 minutes

---

**Scene 1 — Set the stage (Slide 1: Title + Slide 2: Problem) | 0:00–1:00**

Open the deck to Slide 1. Introduce the session: "We're hardening the Fate game panel against two edge cases that could disrupt a live session." Advance to Slide 2. Say: "Imagine you're mid-session — three players at the table, Fate dice just rolled — and a single bad server message freezes your browser. That's the scenario we closed today."

---

**Scene 2 — Show the before state (Slide 3: What We Built, first half) | 1:00–2:30**

Keep the deck on Slide 3. Open a browser dev console on the running UI (localhost:5173). Paste and run:

```js
// Simulate a corrupted free_invokes payload arriving
window.__testFatePip = 1e9;
```

Narrate: "Before this fix, asking the panel to render one billion dots would pin the browser. We've closed that path. Now let's see the guard working." Navigate to the Fate Panel with a test character that has an active aspect. The pip display renders a bounded count — not a billion dots, not a freeze.

*Fallback if live console step is unavailable: show Slide 5 (Before/After) — the left column shows "free_invokes: 1e9 → browser hangs," the right column shows "free_invokes: 1e9 → renders 10 pips, session continues."*

---

**Scene 3 — Show the reload guard (Slide 3: What We Built, second half) | 2:30–4:00**

Still on Slide 3. Open DevTools → Application → Session Storage. Point out: "Notice there's no `fateState` key here anymore. Before this fix, you'd see the full Fate payload cached here, and it would reload without going through the validator." Refresh the page. The panel shows a loading state briefly, then populates correctly once the server sends a fresh validated message. Say: "The data took the safe road — through the same checkpoint as every live message."

*Fallback if the live environment isn't available: show Slide 5 (Before/After) — left column shows sessionStorage screenshot with fateState key, right column shows empty key / clean reload.*

---

**Scene 4 — Wrap up (Slide 4: Why This Approach + Slide 6: Roadmap) | 4:00–5:30**

Advance to Slide 4. "Two small targeted guards. No new architecture, no new dependencies. Defend at the two entry points." Advance to Slide 6 (Roadmap). "This is defensive groundwork for the broader Fate integration work coming up — inventory boundary hardening and multi-seat Fate state sync."

---

**Scene 5 — Questions (Slide 7) | 5:30–6:00**

Open to questions.

---