# Three-Tier Mapping Architecture — World / Site / Battle

**Date:** 2026-07-08
**Status:** Approved (brainstorming session with Keith, 2026-07-08)
**Amendments:** 2026-07-10 — bounded-site interiors are cookbook-free (ADR-157, story 164-10);
see the §1 Extent `bounded` bullet and §5 Failure modes.
**Repos:** server (engine, protocol, telemetry) · ui (map components, state) · content (map.yaml, archetypes, validator) · orchestrator (umbrella ADR, ADR-096 amendment)

---

## Problem

Mapping is "all over the place": three parallel server substrates (cartography region
graph, ADR-106 procedural dungeon, orbital orrery) share one clobberable UI map slot;
players in the 10 region worlds orient by POI landscape + scrapbook + prose and are
**lost in textual descriptions — they cannot form tactical plans**; the procedural
interior machinery is hard-fenced to exactly one world (`beneath_sunden`); tactical
mechanics that ADR-096 declared canonical are display-only; and main-map presentation
is a generic d3-dag graph regardless of genre.

## Target (three tiers)

1. **Main (world) map** — the existing node-and-edge cartography graph, presented in a
   way that is *genre-true*: "a visual which makes real sense for that world, as opposed
   to a fantasy map with the serial numbers filed off." The orrery is the standard, not
   the component. The main map carries the mechanical bindings: factions, NPCs,
   descriptions, visuals, weather.
2. **Local map** — generated on the fly as needed: seeded sub-locations ("sites") —
   a tavern with rooms, a hotel, a cave warren, a sci-fi vault, city streets —
   extending the existing dungeon-generation machinery, with an actual visualization.
3. **Battle map** — a real tactical map with represented areas and distances. **The
   local map IS the battle map — it is a matter of scale.** Positions/distances/movement
   live in game state and feed the ruleset. Granularity is per-ruleset: Without Number
   bindings consume exact cells; Fate consumes zones projected from the same grid.

## Decisions of record (from the brainstorming Q&A)

- **Battle mechanics: full tactical** (positions/distances/movement in state, enforced
  by the ruleset binding), loosened for Fate via zone projection. Not display-only.
- **Local map = battle map**: one surface, two zoom regimes. No separate arena
  generator.
- **Realistic main maps: public-domain historical rasters** (Baedeker city plans,
  out-of-copyright Ordnance Survey sheets, territorial surveys, state highway maps) —
  the composer's PD-provenance playbook applied to maps. Not live geodata, not
  diffusion-generated real places.
- **Tracks run in parallel** (multiple sessions); the tiers are associated only by
  functionality.
- **The Sünden static→procedural seam is the hard part** and its lessons are design
  invariants (see below).
- **`extent: bounded | frontier` toggle**: almost all generated sites are dead-ended
  and finite (a tavern is not infinite). Bounded sites materialize whole; only
  megadungeon-style sites keep frontier/lookahead machinery.
- **The ADR-153 dogfight is exempt**: its POV relative-position model is doctrine for
  vehicle duels; it is a legitimate third battle paradigm and is not gridded. Leave it
  alone.

## Current-state assessment (2026-07-08, four-agent sweep)

**Exists and generalizes:**
- Two-layer generator (`sidequest/dungeon/`): topological Jaquays region graph +
  per-region 49×49 tile grids; four interior algorithms (`cellular`, `depthfirst`,
  `prim`, `roomcorridor` — the last already bound to a "built" theme class, i.e.
  taverns/vaults are geometrically in the toolbox). Deterministic blake2b seeding.
  Curate stage is LLM-free/deterministic since 158-12 (ADR-106 Amendment C).
- Runtime PNG floor renderer (`game/room_file_loader.py::emit_runtime_cavern_png`) +
  `TACTICAL_GRID` payload + UI `TacticalGridRenderer` (HTML overlay, `lib/cellMath.ts`).
- `Automapper.tsx` room-graph SVG with fog-of-war — built, wired, dormant (reachable
  only in Sünden's deep).
- `CartographyMap.tsx` (d3-dag) — the reusable node-and-edge renderer; serves in-game
  and reference page. ADR-141's epic-100 gate is therefore ALREADY SATISFIED.
- Seam mechanism (`game/seams/`): kind-keyed resolver registry, per-PC `pc_region`
  rebind between disjoint graph namespaces, engine-first crossing
  (`surface_descent_adjacent`, the 8th-attempt winner), same-turn don't-clobber guard.
- Faction↔region coupling (`Region.controlled_by` → `zone_eligibility`) is live.

**Broken / fenced / missing:**
- Everything procedural hard-fenced to `beneath_sunden`
  (`dungeon/region_projection.py::applies_to`).
- Tactical mechanics display-only (ADR-096 v2 named but unbuilt).
- Cartography graph is coordinate-free; no presentation layer; `WorldGraph`/
  `SubGraph`/`GraphEdge`/`Terrain` models are dead code.
- Map arbitration is binary `surface|deep` per connection (`map_emit.py::_descent_phase`);
  UI `mapData` is a single clobberable slot.
- Seam singularity: global `ENTRANCE_ID="entrance"` (`seed_bootstrap.py`), one graph,
  one store; ambiguity guards (`registry.py::seam_route_via_adjacency`,
  `surface_owner_for_entrance`) deliberately return None when >1 seam exists —
  **multi-site is currently designed to refuse**.
- Seam verticality: router direction taxonomy `{deeper|back|toward_exit}`, "seam goes
  down" baked into the router prompt, `depth_score` gradient. "Enter the tavern" is
  lateral and unclassifiable today; sticky-descent is Haiku variance on the
  `direction=deeper` requirement of the adjacency rung (`movement.py:440`).
- Region-mode lateral movement retains the narration-scrape backstop
  (`_defer_region_mode`) — the narrator can still move the party.
- Weather has no structural binding to map nodes.
- Orphaned stories: 158-36 (map incoherent in the deep; canceled, un-owned),
  158-50 (course/clock inert in play; backlog).

**Sünden seam lessons (design invariants):**
1. Crossings resolve by **graph adjacency**, engine-first — never a special-cased
   teleport (7 failed attempts say so).
2. **Single-writer**: the narrator is denied location writes wherever the engine owns
   navigation (the party-split race otherwise re-opens per site type).
3. The fragile part is the **upstream trigger** (router classification), not the seam
   resolver.
4. Generated content must be **materialized ahead of need** or the engine runs dry and
   the narrator improvises (`no_candidate_edges` → mismatch).
5. **All seam/site/tactical spans land in `turn_telemetry`** (publish_event path), not
   Jaeger alone — eight investigations chased a "dead" engine that was firing.
6. Binary scene arbitration does not survive N sites; scene context must be first-class.

---

## §1 Site contract (Track B core)

A **Site** is a first-class named entity:

```yaml
# authored on a world node (world YAML / cartography), or minted at runtime
site_id: gilded_boar
name: "The Gilded Boar"
archetype: tavern          # from the genre pack's archetype catalog
attached_to: ropefoot      # cartography region that owns the seam
extent: bounded            # bounded | frontier
# seed: blake2b(campaign_seed, site_id) — derived, write-once, never authored
```

- **Namespacing:** all node ids inside a site are site-scoped (`gilded_boar:r2`).
  Kills the global `exp001.r0` collision; `is_procedural_region_id` becomes
  site-aware. Per-site graph storage keyed `(session, site_id)`; per-site entrance
  anchor replaces the global `ENTRANCE_ID`.
- **Three origins:** *authored* (declared in world YAML); *minted* (runtime, when the
  narrative demands an interior that doesn't exist — the ADR-109 Yes-And promotion
  path; improvised places become durable sites, not prose); and *ephemeral*
  (single-room combat instances for outdoor/no-site fights, §3 — same machinery, not
  seam-attached, not persisted as places).
- **Archetypes are pack content, not engine code** (Jade doctrine): per-genre YAML
  catalog binding interior algorithm (`roomcorridor` for tavern/hotel/manor/vault,
  `cellular` for warrens/caves), size ranges, room vocabulary, feature palette, grid
  dimensions and cell scale. A new archetype is YAML.
- **Seam:** a cartography Route from world node to a *site-id-keyed* sentinel.
  Symmetric `enter_site` / `exit_site` resolvers, both registered in the seam registry
  (fixing today's asymmetry where `surface_ascent` is called directly). Crossing =
  per-PC `pc_region` rebind between namespaces; don't-clobber guard parameterized per
  site. Failure stays `SeamCrossingError` (recoverable, caller-owned failure spans).
- **Router emits site targets, not directions:** "I go into the tavern" →
  `enter_site(descriptor)`, engine-resolved against the current node's site list
  (surfaced to the router as seam vocabulary is today). Dissolves sticky-descent's
  root cause and the multi-seam ambiguity refusal simultaneously — seams are
  distinguishable by name.
- **Extent:**
  - `bounded` (default): the entire site graph + grids materialize in ONE committed
    transaction at first entry. No frontier worker, no lookahead; `no_candidate_edges`
    is structurally impossible.
    - **Cookbook-free interior (ADR-157, amended 2026-07-10):** a bounded site materializes
      from its `SiteArchetype` *alone* — NOT from the megadungeon `cookbook/` + `corpus/` +
      `themes/` + `world_register.yaml` stack (which exists only in `beneath_sunden`; a
      cozy pub is not a monster den). A parallel `materialize_bounded()` coordinator runs
      only the two already-cookbook-free geometry stages (design + fill: `generate_interior`
      + `_emit_mask`) plus a dedicated geometry commit (graph + masks/tactical + room
      identities). **No curate** (no wandering-monster table / `big_bad`) and **no attach**
      (no set-pieces / tropes / quests). The archetype's `interior_algorithm` + grid dims
      drive a synthetic in-memory `ThemePalette`; its `room_vocabulary` / `feature_palette`
      label the rooms (Diamonds-and-Coal: identities, not anonymous cells). **Zero
      engine-placed creatures** — inhabitants and drama come from the Living World (narrator
      + NPC / scenario / confrontation systems); a vault guardian or tavern brawl is a
      *seated* confrontation, never materializer roster content. The existing `materialize()`
      and its loud None-guards are untouched — zero regression to the frontier path.
  - `frontier`: keeps ADR-106 edge-expansion + lookahead. Sünden's deep becomes the
    first frontier site rather than a parallel system.
- **Scene context:** per-connection `world | site:<site_id>` replaces the
  `surface|deep` binary. Determines map emission (§4).
- **Invariants:** single-writer (narrator denied location writes in engine-owned
  navigation contexts); all site/seam spans → `turn_telemetry`.
- **v1 non-goal:** nested sites (a tavern inside a generated street-grid). Sites
  attach to cartography nodes only. Nesting = named v2 with a scene *stack*.

## §2 Main map treatments (Track A)

The cartography graph stays **coordinate-free and semantic** (regions, adjacency,
`controlled_by`, terrain). Presentation is a separate optional per-world layer:
**`map.yaml`** declaring a `treatment`. No `map.yaml` → d3-dag fallback (today's
behavior). Diamonds-and-Coal: a world earns its treatment when someone authors it.

| treatment | worlds | payload |
|---|---|---|
| `raster` | realistic/period worlds | PD scan on R2 + provenance + `node_anchors: {region_id: [x,y]}` (image px) |
| `orrery` | space worlds | existing orbital path, unchanged — already the exemplar |
| `dag` | fallback | themed d3-dag CartographyMap, zero authoring |
| `generated` | invented-geography worlds | deterministic seeded layout + genre-styled SVG cartography (parchment, terrain glyphs, corpus-derived labels). Slot designed now; built as Track A milestone 3 |

- **Raster sourcing = PD historical maps**: Baedeker city plans (Années Folles),
  out-of-copyright Ordnance Survey sheets (Glenross), territorial surveys
  (spaghetti_western), storybook plates where period-appropriate. Provenance metadata
  (source, date, archive, PD basis) required — the composer provenance pattern is now
  map doctrine. R2 is the canonical media source.
- **road_warrior explicit callout:** road maps — mid-century state highway department
  maps (US government works, clean PD) and pre-war auto-trail/service-station atlases.
  Routes and party marker render as **highway tracing** (route-number shields, mileage
  ticks; distance-along-road is the_circuit's natural metric). The faction layer
  renders as **wasteland defacement**: `controlled_by` territories as scrawled
  gang-territory annotations, crossed-out dead towns, hand-drawn detours. Same
  `map.yaml` schema — a rendering style keyed off genre theme, no new engine surface.
- **Mechanical bindings live on the graph node, not the picture:** `controlled_by`
  (already live) plus new optional `weather_zone` on Region so weather binds to
  geography and reaches narrator grounding per-zone. NPCs/descriptions/visuals already
  hang off regions (ADR-109, POI imagery); the treatment makes them visible in place
  (portrait pins, landmark markers).
- **Orientation surface, not control surface:** clicking a node inspects (description
  preview, reference deep-link). Travel stays prose-through-the-turn-barrier
  (submit-and-wait; no fast-clicker bypass).
- **Validator:** every cartography region must have an anchor when treatment is
  `raster`; provenance fields required. Content invariants live in the pack validator,
  never unit tests.
- **Weed-whack rider:** delete dead `WorldGraph`/`SubGraph`/`GraphEdge`/`Terrain`
  models. The graph of record is `CartographyConfig`.

## §3 Local/battle rendering & tactical mechanics (Tracks B+C)

**One surface, two zoom regimes.** A site scene renders:
- *Local view*: the site's room graph — the existing Automapper (fog-of-war, current
  room, exits), unfenced.
- *Battle-scale view*: the occupied room's tile grid — the existing
  `TACTICAL_GRID` → `TacticalGridRenderer` path (PNG floor + token/feature overlay).

Work = generalize emission to all sites (scene context decides what emits) +
**per-archetype grid sizing** replacing fixed 49×49 (tavern common room ~15×20 @5ft
cells; street scene ~60×40 @10ft; archetype declares dimensions and cell scale).

**Combat happens on the grid you were already standing in.** When a confrontation
seats, actors get cell positions on the current room's grid (tokens already carry
hp/ac/faction). Outdoor/no-site fights materialize a **single-room ephemeral site**
from a terrain-keyed archetype (roadside, clearing, cargo bay) — same machinery, one
room, no seam ceremony.

**Mechanics — ADR-096 v2, behind the ruleset seam (Track C):**
- The **mask is truth**: movement spends cells per WN movement rates; reach and ranged
  bands computed (Chebyshev) from cell distance; AoE templates evaluated cell-by-cell
  against the mask; LOS raycast on the grid.
- Enforcement lives **in the RulesetModule binding**, not native code (ADR-117/143
  discipline): WN modules consume exact cells; **the Fate binding consumes the same
  grid coarsened into zones** (contiguous cell clusters) — "loosen for Fate" is a
  projection, not a fork.
- Dispatch outcomes carry position deltas. Every adjudication emits OTEL
  (`tactical.move.validated/denied`, `tactical.aoe.cells`) → GM panel proves the grid
  is live and the narrator isn't improvising positions.
- **Player-facing math** (Sebastien/Jade): resolution card shows the numbers; movement
  denials come back legible ("that's 40ft, you can move 30ft"), never silently
  corrected.

**Dogfight exemption:** ADR-153's POV relative-position model stays as-is. It is the
third battle paradigm (grid, zones, relative-position). Not gridded, not touched.

## §4 Protocol & UI

**Wire contract follows the scene context.** One clean cutover (we control both ends):
- `MAP_UPDATE` (world scene) gains optional `treatment` block:
  `{kind, image_url, node_anchors, style_hints}`. Absent → d3-dag fallback.
- `DUNGEON_MAP` → **`SITE_MAP`**, one cutover, **no alias** (no-silent-fallbacks).
  Same explored/room_exits/fog shape + `site_id`, `site_name`, `archetype`, `extent`.
  Sünden migrates in the same change: exactly one emitter/consumer before and after.
- `TACTICAL_GRID` keeps its shape; gains site/room keying and (Track C) adjudication
  echoes (move validated/denied, cells spent, band) so the client shows the math.
- **No new inbound messages in v1** — map is read-only; click-inspect rides existing
  `LOCATION_DESCRIPTION`/reference deep-links; `ORBITAL_INTENT` drill unchanged.

**Client state stops being one clobberable slot.** `mapData` becomes **scene-keyed**:
world map and active site map coexist; the connection's scene context selects the Map
tab foreground. The clobber class (surface-vs-deep, site-vs-site) dies structurally.
**Breadcrumb back:** site scene shows "you are inside ⟨site⟩ at ⟨node⟩" header
drilling out to the world map — the proper 158-36 fix.

**Components:** `MapWidget` routes on scene + treatment: new `RasterMap` (scan + SVG
overlay: pins, routes, party marker, faction layer; pan/zoom lifted from the orrery
host), existing `CartographyMap`, existing orrery host; site scenes use Automapper +
`TacticalGridRenderer` as the two zoom regimes. Dock-tab **dual registration**
(widgetRegistry AND MobileTabView TABS) — known jsdom wiring-test tripwire.

## §5 Failure modes, observability, testing

**Failure modes:**
- Authoring errors die in the **pack validator** (anchor coverage, archetype schema,
  provenance fields) — never at the table.
- Runtime fail-loud: missing raster on R2 → explicit error state, not silent dag
  fallback. Unresolvable `enter_site` → `site.enter_unresolved` span + visible defer
  to narration (lie-detector watches the mismatch).
- Bounded materialization is one transaction: no partially-committed site exists.
- **Interior-content load is fail-loud-but-recoverable (ADR-157, amended 2026-07-10):**
  a bounded crossing no longer calls `load_cookbook` at all (the archetype drives it), so
  the megadungeon `FileNotFoundError` source is removed. As defense-in-depth, `movement.py`'s
  content-load `except` is broadened so ANY content-load failure (incl. `FileNotFoundError`)
  surfaces as a recoverable `movement.unresolved` + `site.enter_unresolved` span — never a
  re-raise out of `run_movement_dispatch` (the prior narrow `(GenreLoadError,
  SeamCrossingError)` catch let `load_cookbook`'s `FileNotFoundError` crash the dispatch,
  contradicting the code's own "recoverable" comment).

**Observability:** every new span (`site.enter/exit`, `site.materialize.*`,
`tactical.move.validated/denied`, `tactical.aoe.cells`, `map.treatment_emitted`)
routes to `turn_telemetry` via publish_event, not `Span.open` alone. If the GM panel
can't see it, it isn't shipped.

**Testing:**
- Unit tests: code-only, synthetic fixtures. Content invariants → validator.
- Every emitter gets a **wiring test** proving production reachability; UI includes
  MobileTabView tab reachability.
- Per-track **headless playtest scenario** with span-jsonl assertions
  (`tavern_enter_trace` modeled on `sunden_descend_trace`) — verify mechanics, never
  narration.
- Site-materialization tests monkeypatch `_resolve_world_dir` (known content-pollution
  hazard; durable conftest fixture).

## Migration

- Sünden's deep → first `frontier` site, in the same cutover as `SITE_MAP`.
- Delete dead `WorldGraph`/`SubGraph`/`GraphEdge`/`Terrain` models; delete the
  unconsumed legacy `tactical_grid` field on `ExploredLocation`.
- Kestrel ship-interior SVG (`interior/render.py`): untouched, out of scope.

## Track sequencing (parallel sessions; independently mergeable)

- **Track A — main map:** A1 `map.yaml` schema + validator + `MAP_UPDATE` treatment
  block + `RasterMap` + first three worlds (Glenross OS sheet, Années Folles Baedeker,
  the_circuit highway map with defacement) · A2 `weather_zone` binding · A3
  `generated` treatment · folds **158-50** (course/clock in-play wiring).
- **Track B — sites:** B1 seam/site contract refactor (SiteRegistry, router site
  targets, scene context, `SITE_MAP` cutover, Sünden migration — the risky core,
  first; refactors movement.py's five-rung seam ladder into
  site-registry × enter/exit resolvers × per-site stores) · B2 archetype catalog +
  bounded materialization (tavern, vault first) · B3 minted-on-the-fly sites (Yes-And)
  · B4 per-archetype grids + visual polish · fixes **158-36** structurally.
- **Track C — tactical:** C1 pure adjudication library over masks (testable functions)
  · C2 WN binding enforcement + OTEL + player-visible math · C3 Fate zone projection.
  **C1/C2 run against existing cavern grids today — no dependency on B.**

Cross-track touchpoints (kept minimal): B↔C meet at `TACTICAL_GRID` adjudication
echoes; A↔B meet at site pins on the world map (deferrable to B4/A-late if contended).

## v1 non-goals

Nested sites (scene stack) · travel-by-click · per-player sealed fog (fog stays
table-shared per ADR-036) · dogfight changes of any kind · `hierarchical`
navigation_mode.

## Deliverables beyond code

- One **umbrella ADR** (orchestrator repo, direct to main): three-tier map doctrine +
  site contract + scene context + treatment taxonomy; names the three battle paradigms
  (grid, zones, relative-position).
- **ADR-096 amendment**: v2 enforced mechanics land behind the ruleset seam.
