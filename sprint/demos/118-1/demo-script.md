**Setup before presenting:** Have a local server running with a Fate-genre pack loaded (pulp_noir or tea_and_murder). Have a WebSocket inspector open (browser DevTools → Network → WS, or wscat). Have the GM panel open at `localhost:5173/#/dashboard`. Have a second terminal ready with the session log tailing.

---

**Scene 1 — The Problem (Slide 2: Problem) — 1 minute**

Open the GM panel. Point to the OTEL span stream. Say: "Right now, if I open a Fate session and a player spends a Fate Point, the engine processes it correctly — but watch what reaches the client." Open the WebSocket inspector and filter on `FATE`. Show: nothing. "The scoreboard exists. The players just can't see it."

---

**Scene 2 — What We Built (Slide 3: What We Built) — 2 minutes**

Start a new Fate session (pulp_noir recommended). In the WebSocket inspector, clear the log. Have a player (or use a test script) take any action that changes game state — spend a Fate Point with:

```bash
# In a second terminal, trigger a state change via the scene harness
curl -X POST http://localhost:8765/dev/scene \
  -H "Content-Type: application/json" \
  -d '{"scenario": "fate_point_spend", "pack": "pulp_noir"}'
```

Watch the WebSocket inspector. Point to the `FATE_STATE` message appearing. Click it open. Walk through the payload live:

- "Here's **Carmen Reyes** — 2 Fate Points, refresh of 3. She's running low."
- "Her aspects: *'Dame with a Past'* — available to invoke, no cost. *'Mild Consequence: Shaken'* — she took a hit."
- "Stress track: boxes 1 and 2 checked. Box 3 is still open."
- "Scene situation aspect: *'The Alley is Poorly Lit'* — free invoke available."

Say: "Every connected player's client receives this the moment the state changes. This is the data layer that makes every Fate UI feature possible."

*Fallback if the curl command fails:* Switch to Slide 3 and show the pre-captured payload screenshot. Walk through the same fields from the static image.

---

**Scene 3 — The Monitoring Signal (Slide 3, continued) — 1 minute**

Switch to the GM panel OTEL stream. Filter on `fate.projection`. Show the `fate.projection.emitted` span appearing each time state changes. "The GM can see in real time that the Fate data pipeline is live. If this span stops appearing, something is wrong upstream — the signal is the proof of life."

*Fallback:* Show a pre-captured screenshot of the span in the GM panel.

---

**Scene 4 — What This Enables (Slide 6: Roadmap) — 1 minute**

Switch to a non-Fate session (caverns_and_claudes). Trigger a state change. Show the WebSocket inspector: no `FATE_STATE` message. "Zero impact on the other nine genres. The gate is precise."

Close with Slide 6 and the roadmap.

---