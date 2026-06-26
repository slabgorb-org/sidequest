---
story_id: "158-36"
jira_key: ""
epic: "158"
workflow: "tdd"
---
# Story 158-36: Map incoherent in the deep — region-mode map renders only the static surface cartography; the procedural regions the player occupies + discovered_routes are not plotted (distinct from 158-6 labels / 158-18 tactical grid)

## Story Details
- **ID:** 158-36
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none
- **Repos:** server, ui

## Problem Statement
Playtest findings (pingpong 2026-06-23 + 2026-06-24, beneath_sunden). After descending into a procedural expansion the region-mode Map tab renders only the static surface cartography (Ropefoot + The Dropmouth); it does not plot the procedural regions the player occupies (entrance / Oathbound Armoury), and discovered_routes stays empty even when a connected node cluster IS drawn (nodes render, routes do not). Server logs `dungeon.map_emitted region=entrance discovered=1/7` but UI never plots it; surface map drops off entirely in the deep (no breadcrumb back). DISTINCT from 158-6 (done, label dedup) and 158-18 (done, tactical token/feature grid, which also does not surface in region-mode per board). The world premise is the descent; a player two hops down has no usable map. Likely 153-25 DUNGEON_MAP frame layer mismatch + dropped ropefoot frames + route persistence.

## Workflow Tracking
**Workflow:** tdd
**Phase:** red
**Phase Started:** 2026-06-26T09:19:58Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-26T09:17:29Z | 2026-06-26T09:19:58Z | 2m 29s |
| red | 2026-06-26T09:19:58Z | - | - |

## Sm Assessment

**Routing:** tdd (phased) → TEA owns RED next. Scope is two-repo: `sidequest-server` (route/region emit) + `sidequest-ui` (region-mode plot). Branch `feat/158-36-map-deep-region-routes` exists off `origin/develop` in both subrepos (server d9106da4, ui current). Orchestrator NOT branched.

**Pulled forward, not next-in-id-order:** This story was selected ahead of the 158-29..31 / 34 / 35 dogfight cluster, which is under redesign and parked. 158-36 is fully independent of that rethink — a self-contained map-rendering bug. Its named root-cause prerequisite (153-25 DUNGEON-MAP-UI-NO-ROOMGRAPH) is already **done** (archived epic-153), so there is no upstream wait.

**The defect (verbatim from the finding):** descend into a procedural expansion → region-mode Map tab renders only the static surface cartography (Ropefoot + The Dropmouth) → procedural regions the player occupies (entrance / Oathbound Armoury) are NOT plotted → `discovered_routes` stays empty even when a connected node cluster IS drawn (nodes render, routes do not). Server logs `dungeon.map_emitted region=entrance discovered=1/7` but the UI never plots it; the surface map drops off entirely in the deep (no breadcrumb back).

**Distinct from siblings (do not re-solve these):** 158-6 (done — region-node *label* dedup), 158-18 (done — tactical token/feature grid, which itself does not surface in region-mode per the board). This is the region-mode *cartography plot* (regions + routes + surface breadcrumb), a different surface.

**Open disambiguation TEA must resolve before pinning the RED test (drive from the watcher/log stream + payload inspection, do not guess):**
- The server already emits `dungeon.map_emitted region=entrance discovered=1/7` — so does that payload actually *carry* the procedural region nodes **and** the `discovered_routes` edges, or only the discovered *count*?
  - **If the payload is missing the region nodes / route edges** → server-side emit gap (routes not serialized / not persisted across descent). RED pins the emit contract.
  - **If the payload carries them but the UI drops them** → UI-side plot gap, likely the 153-25 DUNGEON_MAP frame-layer mismatch + dropped ropefoot frames. RED pins the region-mode plot/reducer.
- Two threads may both be live (nodes render but routes do not strongly suggests a *partial* UI plot path). TEA decides whether to pin server-emit and UI-plot in one RED or stage them.

**Likely-relevant references (for orientation — NOT a fix prescription):** ADR-055 (Room Graph Navigation — region/route model), ADR-106 (procedural megadungeon edge-expansion), 153-25 + 153-27 (done, DUNGEON_MAP frame layer + zone eligibility), the `dungeon.map_emitted` server event, and the region-mode Map tab reducer in `sidequest-ui`. SM stayed in lane: no implementation, no test code, no diff written during setup.

## Resolution — CANCELED (overtaken by events)

**Closed by TEA (the Caterpillar), 2026-06-26, during RED investigation. No new PR — the headline defect was already fixed by prior work; verified against the actual playtest records (2026-06-22 `697cbc14`, 2026-06-23 `mp-e88e04d6`) + git history, not by guessing.**

**1. Headline ("Map renders only static surface cartography; procedural regions not plotted") — FIXED.**
- **UI #446** `feat(ui): Wire DUNGEON_MAP frame into the Map tab room-graph` — fixes the 06-22 console symptom "room-graph frames arrive and apply but to a different component than the Map tab renders."
- **Server #1047** `fix(map): phase-aware switch so beneath_sunden shows the generated deep` (+ `tests/server/test_descent_phase_map_switch.py`) — the descent-phase gate suppresses dungeon-emit on the surface, eliminating the malformed `ropefoot` DUNGEON_MAP frame (`missing current_location/explored`) that was dropped client-side.
- Confirmed live: the 2026-06-23 playtest says "Map-in-the-deep renders procedural nodes now" (Drowned Cavern 1/2/3 + `?` + `↓`). Siblings 158-6 (label dedup, #449) and 158-18 (tactical grid, #1065/#450) also done.

**2. "`discovered_routes` stays empty" — NOT a defect (DRIVER misread).** `discovered_routes` is the *hidden-route reveal* set, consumed only to un-hide secret exits (`movement.py:745`, `intent_router_pass.py:548`: `(not e.hidden) or (e.to_region_id in discovered_routes)`) and written only by the narrator `discover_routes` patch (`session.py:1737`). Empty `[]` is *correct* when no hidden routes have been discovered. Visible map edges draw from `room_exits` (all non-hidden graph edges, `map_emit.py:1006-1013`), independent of `discovered_routes`.

**3. "Surface map drops off in the deep — no breadcrumb back" — by design, not a bug.** The #1047 phase-aware switch deliberately renders a "current-depth view" (single `mapData` slot, `App.tsx:1269-1290`). A surface-breadcrumb-back view would be a NEW feature contradicting that recent decision — deferred as a separate product/design question for Keith, not part of this bug.

**Disposition:** status → `canceled`. Points (3) NOT counted as done — they were earned by #1047/#446 under their own stories. No code written by this story; setup branches (`feat/158-36-map-deep-region-routes`, 0 commits, both repos) deleted; no PR.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->