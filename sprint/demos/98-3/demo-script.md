**Setup before the presentation:** Have the game running with a space opera session loaded in the `perseus_cloud` region. The `yula` system should be the current location.

**Scene 1 — The Problem (Slide 2, ~1 min)**
Open the current build (pre-story) if available, or describe from memory: "Previously, the map widget had a toggle. You got either the galaxy graph or the orrery. No path between them — and the toggle wasn't even a player control." If showing live, display the old `orbital:bool` flag in the source. Fallback: skip to Slide 3 if the old build isn't handy.

**Scene 2 — Default State: Galaxy View (Slide 3, ~90 sec)**
Open the map widget. The galaxy cartography graph fills the panel: star systems as labeled nodes (`yula`, neighboring systems), jump routes as edges connecting them. Point out: "This is the default. You always land here first — campaign scale, where are we, where can we go." No toggle, no mode — just the map.

**Scene 3 — Drill Down into a System (Slide 3 continued, ~90 sec)**
Click the `yula` node on the galaxy graph. The widget transitions to the `yula` orrery: the star at center, planets in their orbital rings, ADR-130 story-time clock ticking. Say: "One click. We went from campaign map to local system. The orrery is the same renderer that's been powering space opera all along — we just gave it a proper front door." Point to the back-navigation affordance. Click it — galaxy view returns.

**Scene 4 — Uncharted System Behavior (Slide 4, ~60 sec)**
Click a system node that has no authored `systems/<id>.yaml` file (any non-`yula` neighbor in `perseus_cloud`). The widget shows a "no local chart" placeholder — it does not crash, does not show a stale orrery from the previous system. Say: "If a system hasn't been authored yet, the widget tells you that cleanly. No ghost data from wherever you were before."

**Scene 5 — What's Gone (Slide 4 continued, ~30 sec)**
Show the git diff removing `orbital:bool` from the MapWidget props. "This flag is deleted. There's no toggle state to manage, no 'which mode am I in' question. The hierarchy is structural now, not a runtime boolean."

**Fallback:** If the live app fails to load, show the before/after slide with the widget screenshots and narrate the scene descriptions above from the slide content.

---