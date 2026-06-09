# Narrative

## Problem Statement
**Problem:** The map in SideQuest showed either a star-chart *or* a planetary orrery — never both, and switching between them required toggling a hidden developer flag (`orbital:bool`). Why it matters: players navigating a space opera campaign need to see the big picture *and* zoom into a specific star system without leaving the map. A boolean switch that flips the whole screen isn't a player feature — it's a placeholder that blocked real navigation from being built.

---

## What Changed
Think of it like Google Maps switching between a country-level road map and Street View. Before this story, the map either showed you the whole galaxy (nodes and jump-routes between star systems) *or* a single system's orbiting planets — and the only way to switch was a developer toggle buried in the code.

Now, the galaxy map is always the starting view. When a player clicks on a star system node, the map smoothly drills into that system's orrery — showing the planets, moons, and orbital paths around that star. Click away or press back, and the galaxy view returns. The old `orbital:bool` whole-map toggle is gone entirely.

---

## Why This Approach
The two views already existed and worked — the galaxy graph renderer (d3-dag) was built in a sibling story (100-10), and the orrery renderer has been live since the space opera launch. The work here was wiring them into a single widget with the right hierarchy: galaxy first, system on demand. Rather than building a new component from scratch, this story layered the drill-down interaction model on top of the shared layout engine that 100-10 delivered. Retiring the boolean toggle removes a dead-end API surface that couldn't express "I'm in this system's orrery" — it only expressed "show orbits: yes/no."

---
