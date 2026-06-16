**Pre-flight (before presenting):**
- A running Fate Core session on `pulp_noir` or `tea_and_murder` (any `ruleset=='fate'` pack)
- FatePanel visible, player seated with at least 2 fate points
- Have a character with a compelling aspect ready (e.g., a "Overconfident to a Fault" high-concept)

---

**Scene 1 — Slide 2 (Problem): The Silent Offer**
*(~60 seconds)*

Start the session, have the GM trigger a compel from the server side. Show the `fate.compel.offered` OTEL span firing in the GM panel. Then show the player screen: nothing. No prompt, no buttons, no fate-point change. Say aloud: "The server told the player something happened. The player had nowhere to go with it." This is the before state.

*Fallback if live demo isn't available: show the `fate.compel.offered` span screenshot alongside the flat player screen.*

---

**Scene 2 — Slide 3 (What We Built): The Full Loop**
*(~90 seconds)*

Trigger a new compel. Show the compel prompt appearing in the player UI with the aspect name, the proposed complication text, and two clearly labeled controls: **Accept (+1 fate point)** and **Refuse (costs 1 fate point)**. Call out: "The player can see exactly what this decision costs before they make it."

Click **Accept**. Watch the fate-point counter tick up by 1 (e.g., from 2 → 3). Point to the delta display. Say: "Server confirmed. The engine updated the economy. The player didn't have to do arithmetic."

Then reset and trigger another compel. Click **Refuse**. Fate points tick down by 1 (e.g., 3 → 2). "Rulebook says refuse = pay one. That's what happened."

*Fallback: screen recording of both flows side by side.*

---

**Scene 3 — Slide 4 (Why This Approach): Server Owns the Economy**
*(~45 seconds)*

Open the OTEL GM panel. Show `fate.compel.accepted` span (or `fate.compel.refused`) with the fate-point delta logged. Say: "The UI didn't guess what to show. It waited for the server to confirm the transaction — then updated. Same pattern as aspect invokes. One source of truth."

---

**Scene 4 — Slide 6 (Roadmap): Where This Lands**
*(~30 seconds)*

Point to the Fate panel fate-point counter. "Before this story: a number. After: a live economy — offers, acceptances, refusals, deltas, all logged and surfaced. The conflict surface coming in F3f can now use compels as a real combat lever, not a decorative one."

---