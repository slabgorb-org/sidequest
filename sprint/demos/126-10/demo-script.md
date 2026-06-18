**Setup before presenting:**
- Have a fresh `annees_folles` 2-seat understudy run ready to launch (`just playtest --world annees_folles --seats 2`)
- Have the GM panel open at `localhost:5173/#/dashboard` filtered to `intent_router`
- Have a terminal tab with the turn_telemetry log ready: `tail -F ~/.sidequest/logs/sidequest-server.log | grep intent_router_pass`

---

**Slide 1 (Title) — 0:00–0:30**
Introduce the story: "This fix closes a performance hole that made our Fate Core worlds feel broken. Thirty seconds of silence after you type your action is not a game experience."

**Slide 2 (Problem) — 0:30–2:00**
Open the *before* telemetry screenshot (or the Before/After section of this doc). Point to the `intent_router_pass` span: "You can see durations of 37 to 81 seconds. This is the step that happens *before* the narrator even starts writing. Every Fate world turn paid this tax."

Walk through the cause in plain terms: "The router was being handed an encyclopedia of Fate rules when it just needed a sticky note."

Fallback if live data isn't available: Stay on Slide 2 and show the before telemetry screenshot with the annotated span durations.

**Slide 3 (What We Built) — 2:00–3:30**
Switch to the live terminal. Run:
```bash
just playtest --world annees_folles --seats 2 --turns 3
```
While it runs, narrate: "Watch the intent_router_pass span in the GM panel. On the fixed build, this should land between 4 and 6 seconds."

Point to the GM panel as spans appear. Call out the `intent_router.decompose` duration.

Fallback: Show the after telemetry screenshot. Point to the specific row showing `intent_router_pass: 4.2s` (or whatever the measured after value is).

**Slide 4 (Why This Approach) — 3:30–4:30**
"We didn't reduce the information the narrator sees — that would risk breaking Fate mechanics. We only trimmed what the *router* sees, because the router's job is classification, not rule adjudication."

Reference the separation from 126-9: "The narrator prompt work is a sibling fix; they touch different layers and were kept separate so each can be validated on its own."

**Before/After slide — 4:30–5:30**
Walk through the Before/After table below. Emphasize the floor-to-ceiling drop in router latency and that no Fate routing accuracy was lost.

**Roadmap slide — 5:30–6:00**
"With the router fast again, Fate worlds are table-ready. The next step is the narrator-side Fate prompt work in 126-9."

**Questions — 6:00+**

---