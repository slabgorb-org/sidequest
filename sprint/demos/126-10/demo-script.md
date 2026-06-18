**Setup before presenting:** Have a terminal ready with the understudy playtest harness and a saved before-state turn telemetry log. Have the GM panel open in the browser at the OTEL dashboard (`localhost:5173/#/dashboard`).

---

**Scene 1 — The Problem (Slide 2: Problem)**
*Timing: ~2 minutes*

Open the saved before-state turn telemetry log:
```bash
cat runs/annees_folles_before/turn_telemetry.jsonl | jq '.spans[] | select(.name == "intent_router.decompose") | .duration_ms'
```
Show the audience the output: values in the **37,000–81,000 ms range** (37 to 81 seconds). Contrast this by pulling the same span from a non-Fate world (e.g., `caverns_and_claudes`):
```bash
cat runs/caverns_baseline/turn_telemetry.jsonl | jq '.spans[] | select(.name == "intent_router.decompose") | .duration_ms'
```
That output shows **4,000–6,000 ms**. Let that contrast land.

*Fallback if terminal fails: Slide 2 has the before/after numbers in a table. Point to the 81s vs 5s row and describe what that means in human terms — "80 seconds of silence at the table."*

---

**Scene 2 — What We Built (Slide 3: What We Built)**
*Timing: ~2 minutes*

Explain: "We separated the Fate world description into two versions — a full one for narration, and a trimmed one for routing. The router only sees what it needs."

Show the state summary size difference — point to the GM panel in the browser, navigate to the `intent_router.decompose` span for a fresh Années Folles turn:
- **Before:** `state_summary` token count: ~3,200–4,100 tokens
- **After:** `state_summary` token count: ~400–600 tokens

*Fallback: Slide 3 has a "Before / After" token count callout graphic.*

---

**Scene 3 — Live Verification (Slide 3 continued)**
*Timing: ~3 minutes*

Run a 2-seat understudy playtest live:
```bash
understudy run runs/annees_folles_2seat.yaml --turns 3
```
Watch the terminal output for `intent_router_pass` timing lines. Show the audience numbers in the **4–7 second range** — within baseline.

*Fallback: Show the after-state telemetry file:*
```bash
cat runs/annees_folles_after/turn_telemetry.jsonl | jq '.spans[] | select(.name == "intent_router.decompose") | .duration_ms'
```

---

**Scene 4 — Accuracy Unchanged (Slide 4: Why This Approach)**
*Timing: ~1 minute*

Pull up the routing classification from the same telemetry:
```bash
cat runs/annees_folles_after/turn_telemetry.jsonl | jq '.spans[] | select(.name == "intent_router.decompose") | .attributes.intent_class'
```
Show the audience correct classifications: social confrontations correctly labeled, exploration correctly labeled. "We made it faster. We didn't make it dumber."

---