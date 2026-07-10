# Story 164-5 Context

## Title
UI: SITE_MAP handling + scene-keyed mapData + breadcrumb — fixes 158-36 (plan task 9)

## Metadata
- **Story ID:** 164-5
- **Type:** story
- **Points:** 3
- **Priority:** p1
- **Workflow:** superpowers → resolves to **spdd** (phased: setup → red → green → review → finish)
- **Repo:** ui (sidequest-ui only)
- **Epic:** 164 — Mapping Track B — Site system (seam contract, archetypes)
- **Branch:** `feat/164-5-site-map-ui-scene-mapdata-breadcrumb` (base: develop)

## Authoritative Sources (read these before RED)
- **Plan task 9** (THE spec for this story): `docs/superpowers/plans/2026-07-08-mapping-track-b-site-system.md` → "## Task 9: [RISKY CUTOVER] UI SITE_MAP handling + scene-keyed mapData + breadcrumb (158-36)". It names exact files, line anchors, the failing-test seed, and the scope guardrails.
- Design spec: `docs/superpowers/specs/2026-07-08-three-tier-mapping-design.md`
- Bug being fixed: **158-36** (canceled in epic-158 — this story fixes it structurally). Symptom: after descending into a procedural expansion, the region-mode Map tab renders only the static surface cartography; the procedural regions the player occupies never plot, `discovered_routes` stays empty, and the surface map drops off with **no breadcrumb back**. A player two hops down has no usable map.
- Server contract already landed (all merged): **164-1** SiteRegistry, **164-2** enter/exit_site resolvers + site.* spans, **164-3** router site targets + Sünden migration, **164-4** scene context replaces surface|deep + DUNGEON_MAP→SITE_MAP cutover. The server now emits `SITE_MAP` with scene-keyed context and site metadata; this story makes the client consume it.

## Problem
The server side of the site cutover is done (164-1..164-4). The client still speaks `DUNGEON_MAP` and holds a single clobberable `mapData` slot, so the world map and an active site map cannot coexist — descending clobbers the surface map and there is no way back. This story cuts the UI over to `SITE_MAP`, splits `mapData` into scene-keyed state, and adds the drill-out breadcrumb.

## Technical Approach (per plan task 9 — TEA/Dev own the details)
UI surface (sidequest-ui):
- `src/types/protocol.ts` — `DUNGEON_MAP` (`:23`) → `SITE_MAP`.
- `src/lib/dungeonMap.ts` → `src/lib/siteMap.ts` — `SiteMapPayload` (+ `site_id`/`site_name`/`archetype`/`extent`), `isSiteMapPayload`, `siteMapToMapState` returning `MapState & { siteId; siteName; archetype; extent }`.
- `src/App.tsx` — replace single `mapData` slot (`:378`) with scene-keyed `{ worldMap, siteMap }`; route `MAP_UPDATE` → world, `SITE_MAP` (was `DUNGEON_MAP` `:1281`) → site, `TACTICAL_GRID` patches whichever map holds the room (prefer site). Pass both to `GameBoard`.
- `src/components/GameBoard/widgets/MapWidget.tsx` — site-scene branch (`:248`): foreground the site map when a site scene is active + add a breadcrumb header ("You are inside ⟨site⟩ · ▲ ⟨world region⟩"). **Drill-out is view-only** — it shows the world map, it does NOT move the party (travel stays prose-through-the-turn-barrier).

## Scope Guardrails (CRITICAL — Track A shares two files)
- `MapWidget.tsx` — **only** touch the site-scene branch (`:248`) + breadcrumb. **Leave the orrery + cartography (Track A `RasterMap`/treatment) branches alone.**
- Do NOT modify the cartography `treatment` emission path.
- The Map **tab** itself does not change — only its content. Verify (don't edit) the three registration sites: `widgetRegistry.ts:80`, `GameBoard.tsx:890` (`rightGroupOrder`), `MobileTabView.tsx:33` (`TABS`).
- Clean up stragglers: `grep -rn "DUNGEON_MAP\|dungeonMap\|DungeonMap" src/`.

## Acceptance Criteria (TEA to convert to failing tests in RED)
1. `SITE_MAP` protocol message type exists and `DUNGEON_MAP` is gone from `protocol.ts` (and no `dungeonMap`/`DungeonMap` stragglers remain in `src/`).
2. `isSiteMapPayload` / `siteMapToMapState` carry site metadata (`siteId`, `siteName`, `archetype`, `extent`) into `MapState`; explored coords resolve (adapt the existing dungeonMap test).
3. World map and active site map coexist in scene-keyed state — a `SITE_MAP` does not clobber the world map, and vice versa.
4. `MapWidget` foregrounds the site map when a site scene is active and renders a breadcrumb that drills out (view-only) to the world map — the visible 158-36 fix.
5. Wiring/reachability: a jsdom test asserts the Map tab renders the site breadcrumb when `siteMap` is set (component reachable from a production path, not just unit-tested in isolation).
6. `npx vitest run` (siteMap + MapWidget + App dispatch tests) and `npm run lint` green.

## Out of Scope
- Server-side emit (done in 164-1..164-4). B2 archetypes / bounded materialization (164-6+). Track A raster/treatment map work. Any change to the Map tab registration itself.

---
_SM-enriched from plan task 9 + epic-158 (158-36) + sibling server stories 164-1..164-4. TEA refines ACs into failing tests during RED._
