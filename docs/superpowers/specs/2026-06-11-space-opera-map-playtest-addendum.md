# Space-Opera Map — Playtest Addendum (corrects the Two-Scale epic, completes 100-12's dropped seam)

**Date:** 2026-06-11
**Author:** SM / Playtest DRIVER (coyote_star solo, 2026-06-11) + Operator (Keith)
**Amends:** [2026-06-08 — ADR-141 Two-Scale Spatial Model epic](./2026-06-08-two-scale-spatial-model-epic-design.md) and [2026-06-08 — Reference-Pages React Migration](./2026-06-08-reference-pages-react-migration-design.md)
**ADRs touched:** [141 — Two-Scale Spatial Model](../../adr/141-two-scale-spatial-model-galactic-graph-and-system-orrery.md) (amends its "no new world-level flag / derivable from node count" decision), [094 — Orrery Label Placement](../../adr/094-orrery-label-placement-three-strategy-taxonomy.md)
**Repos:** ui (primary), server, content (regression only)
**Status:** Draft addendum — ready for PM/SM to file as stories under the existing map epic
**Source:** live playtest findings, logged in `~/Projects/sq-playtest-pingpong.md` (2026-06-11)

---

## 1. Why this addendum exists

The 2026-06-08 Two-Scale epic is sound for **perseus_cloud** (a real multi-system
cluster). A 2026-06-11 coyote_star solo playtest exercised the in-game Map and the
lore reference page and found **three gaps the epic either got wrong or never
covered**. Two are corrections to a settled assumption; one completes a handoff that
story 100-12 explicitly dropped. The operator made the design calls live — they are
recorded here verbatim, not re-litigated.

**The unifying picture (operator's end-state for space opera):**

- **local map = the orrery** (already true at local scale).
- **global/cluster map = the d3-dag `CartographyMap`** (story 100-10), upgraded to a
  real node graph (NPC portrait pins, richer paint — not "look ma, an SVG"), and
  actually **wired to the lore page**.
- **single system → the orrery IS the map** (collapse; `coyote_star`, `aureate_span`).
- **multi system → dual display**: hyperlanes (`CartographyMap`) + per-system orrery
  (`perseus_cloud`).
- *Scout other (unoccupied) systems* and *other genres' local maps* are explicitly
  **out of scope** here (future features).

## 2. Correction A — single-vs-cluster is NOT derivable from node count

**Epic claim being corrected:** Two-Scale epic U1 **AC4** ("two scales collapse …
*derivable from one graph node*") and §6 ("New world-level cluster-vs-single flag —
*derivable from node count*; add only if implementation finds it materially clearer")
— and ADR-141's "no new world-level flag" pointer.

**Playtest evidence (falsifies it):**

- `MapWidget.tsx:97` → `const isCluster = regionCount > 1;` (comment cites ADR-141:
  ">1 region node = cluster").
- `coyote_star` authors **8 regions** in `cartography.yaml` (Far Landing, Deep Root,
  Red Prospect, Grand Gate, Turning Hub, Mendes' Post, The Broken Drift, The Last
  Drift) but is **ONE system** — those 8 regions are the *bodies* in its single
  orrery (`chart.yaml` + `orbits.yaml`). It has **no `systems/` dir**.
- `perseus_cloud` is the only true cluster: it has a `systems/` dir **and**
  `perseus_cloud.sector.json`.
- `aureate_span` has `cartography.yaml` but **no `systems/`** and no orrery data yet →
  single system.

So `regionCount > 1` flags `coyote_star`/`aureate_span` as clusters, forcing the
campaign-graph + per-node drill. Two player-visible failures: (1) the orrery was
**undiscoverable** (nothing signals "click the node you occupy"); (2) **only the
occupied node drills** — the server only resolves the occupied region's local chart,
so the other 7 nodes are dead clicks. The heuristic shipped because it was written
against perseus, where multi-region and multi-system coincide.

**Operator decision (2026-06-11), overriding ADR-141 §"Single-system worlds" + epic §6:**

1. **Single-system is a first-class case.** A single-system world **collapses the two
   scales** — show the orrery directly (orrery-as-Map), **no cluster graph, no drill**.
2. **Cluster detection keys on multi-SYSTEM, not multi-region.** The signal is a
   **server-set flag** derived from `systems/` (or sector-graph) presence on the
   cartography/world payload — *not* `cartography.regions.length`. This **adds the
   world-level flag** ADR-141 deferred; the node-count heuristic is retired.
3. **Growth affordance:** `coyote_star` and `aureate_span` keep the ability to become
   multi-system later by adding a `systems/` dir — a content change, no code change
   (the whole point of the server flag).
4. **Out of scope:** scouting unoccupied systems' orreries (future).

This also makes Two-Scale **S1 AC5** (the coyote_star single-system regression) the
*primary* behavior for two of three space-opera worlds, not an edge case.

## 3. Correction/Completion B — the lore page's Map section has no client renderer

**Not in the Two-Scale epic at all** — this is the dropped seam of story **100-12**
(reference-pages React migration), surfaced by the same playtest.

- The lore page is **designed to lead with the map**: `ReferenceLorePage.tsx`
  `LORE_SECTION_ORDER = ["map","world","lore","poi","cast","timeline","history","legends"]`
  ("Map leads as the page header").
- **Server builds it every load:** `reference_projection.py::build_lore_map_section`
  (called ~line 527) projects `cartography.yaml` → a `map` section with
  `{id:"map", label:"Map", starting_region, regions:[{id,name,adjacent,pins:[{slug,label,portrait_url}]}], edges:[[a,b]…], dangling:[…]}`,
  including **R2-gated NPC portrait pins**, with OTEL (`reference_map_rendered_span`,
  `pin_resolved`, `pin_not_found`, `dangling_edge`).
- **Client drops it:** `SectionDispatch.tsx` handles `poi`/`cast`/`timeline`, then a
  default that renders `NodeTree` **only if** the section has a `node`. The map
  section has no `node` (it carries `regions`/`edges`/`pins`), so it falls through to
  **nothing**. The comment admits it: *"an unknown section WITHOUT a node (e.g. the
  not-yet-wired 'map' section) degrades to nothing, never a crash."*
- **History:** 100-10 built the shared d3-dag `CartographyMap` whose docstring claims
  it's *"consumed by BOTH surfaces: the session-free reference Map section AND the
  in-game MapOverlay."* 100-12 retired the server SVG emitter on the promise *"node
  positions are now a client concern (the SPA's d3-dag map)"* — but the reference Map
  surface was **never created** (`find … reference -iname "*map*"` → nothing;
  `CartographyMap` is imported only by the in-game `MapOverlay`). 100-12 retired the
  old renderer and left the new one un-wired here.

This is the operator's "new react component that seems not to be being used" —
precisely located: not globally unused, but its **intended lore-page surface has no
renderer**.

## 4. Correction C (low) — orrery arc label wrong sweep rotation

Cosmetic, governed by ADR-094. In the `coyote_star` orrery the engraved belt labels
render as curved text ("— Last Drift —", "— broken drift —"); the **"broken drift"**
label is arced in the **wrong rotation** (sweep direction flipped vs. the belt it
annotates, letters reading the wrong way). Likely site:
`sidequest-server/sidequest/orbital/render.py` textPath/arc-belt path
(render.py:483-484/~527/~562 document "sweep-flag=1 so letters stay upright";
`_arc_belt_bodies_with_textpath_annotation` ~669). A belt on the opposite side of the
chart needs the opposite sweep-flag (or a reversed path).

## 5. Story deltas (file under the existing map epic)

### Story M-A — Server: multi-system flag on the cartography/world payload
**Lane:** Dev · **Repo:** server
- AC1: Server sets an explicit boolean (e.g. `is_cluster` / `multi_system`) on the
  cartography payload (and the reference projection's map section), **true iff** the
  world has a `systems/` dir (or a sector graph). `perseus_cloud` → true;
  `coyote_star`, `aureate_span` → false.
- AC2: OTEL span on the decision: world, signal source (`systems/` present?), result.
- AC3: Supersedes the client `regionCount > 1` heuristic — the flag is authoritative.
- AC4: No silent fallback — absence of `systems/` is a definite single-system, not an
  "unknown."

### Story M-B — UI: route single-system worlds to orrery-as-Map; drive cluster off the flag
**Lane:** Dev · **Repo:** ui · **Files:** `MapWidget.tsx` (replace `isCluster` at :97)
- AC1: `isCluster` reads the M-A server flag, not `regionCount`.
- AC2: Single-system world → **orrery-as-Map**, no cluster graph, no drill (reuses the
  verified #748 collapse branch). `coyote_star`/`aureate_span` regression-tested.
- AC3: Cluster world (perseus_cloud) → campaign graph default + per-occupied-node
  orrery drill (unchanged from Two-Scale U1).
- AC4: UI test with a single-system multi-region fixture (coyote_star shape) asserting
  **no cluster graph + no drill + orrery rendered directly**.

### Story M-C — UI: wire the lore-page Map section (complete 100-12's seam) + portrait pins
**Lane:** Dev · **Repo:** ui · **Files:** `SectionDispatch.tsx`, new
`sections/MapSection.tsx`, `map/CartographyMap.tsx`
- AC1: `SectionDispatch` gains `case "map"` → `MapSection`, adapting the server
  `{regions, edges, pins, starting_region}` to what `CartographyMap` consumes
  (current `CartographyMetadata` = `regions: Record<id,{name,description,adjacent}>` +
  `routes`; reconcile shapes in the adapter).
- AC2: `CartographyMap` renders **NPC portrait pins** (the "fancy node thing" upgrade)
  — this is both the lore-map wiring and the richer renderer in one.
- AC3: Session-free (the reference SPA has no WebSocket) — `CartographyMap` already is.
- AC4: UI test asserting the lore projection's `map` section renders a graph (not
  nothing) and pins appear when `portrait_url` is present.
- AC5: The same upgraded renderer is what the in-game cluster graph uses (one
  component, both surfaces — honor 100-10's original "both surfaces" intent).

### Story M-D — Server: fix the orrery "broken drift" arc-label sweep (low)
**Lane:** Dev · **Repo:** server · **Files:** `orbital/render.py`
- AC1: Belt labels read upright/correct-direction on **both** sides of the chart
  (opposite-side belts use the opposite sweep-flag / reversed path).
- AC2: Cosmetic — no OTEL needed (per CLAUDE.md "not needed for cosmetic changes").

## 6. Sequencing & relationship to the Two-Scale epic

```
M-A ──► M-B          (single-system collapse — fixes 2 of 3 space-opera worlds)
M-C                  (lore-map wiring + fancy renderer; independent, do anytime)
M-D                  (cosmetic; independent)
```

- **M-A + M-B replace the Two-Scale epic's reliance on the node-count heuristic.**
  They do not block perseus_cloud's cluster path (U1) — they correct how the *single*
  case is detected. Two-Scale U1 AC4 ("single-system collapses") is now delivered by
  M-A/M-B with a real signal.
- **M-C completes story 100-12's dropped lore-Map seam** and delivers the richer
  renderer the operator wants. It is the shared component for both surfaces.
- Two-Scale C1/S1/S2/C2 (perseus per-system files + jump mechanics) are unaffected.

## 7. Non-goals

- Scouting unoccupied systems' orreries (future feature).
- Other genres' local-map representations (parked — space opera only here).
- Authoring `aureate_span`'s orrery data (Diamonds-and-Coal, on demand).
- Re-litigating ADR-141's cluster/orrery split — only its detection heuristic and the
  single-system collapse are amended.
