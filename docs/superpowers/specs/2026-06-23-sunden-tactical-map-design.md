# Sünden Tactical Map — Generation-Sourced Token + Feature Pipeline

**Date:** 2026-06-23
**Status:** Design (approved for spec) — pending implementation plan
**Author:** Architect (Naomi Nagata, design mode)
**Relates to:** ADR-096 (Cavern Renderer Revival — *partial*), ADR-106 (Runtime Procedural Jaquaysed Megadungeon), ADR-109 (Persistent Location Descriptions + Mechanical Manifest), ADR-055 (Room Graph Navigation), ADR-143 (Bind the Ruleset, Don't Balance It)
**Proving ground:** `caverns_and_claudes/beneath_sunden`

---

## 1. Problem — the wiring audit

A targeted wiring audit (sq-wire-it, 2026-06-23) found the Sünden tactical map is three layers, only one of which works:

| Layer | Path | State | Evidence |
|-------|------|-------|----------|
| **Region overview** | `DUNGEON_MAP` → Automapper schematic | ✅ Wired | `map_emit.py:_maybe_emit_dungeon_map` — per-PC YOU-ARE-HERE, fog of war, typed exits + bearings, OTEL |
| **Single-room tactical** | `TACTICAL_GRID` → `TacticalGridRenderer` | ⚠️ Hollow | `map_emit.py:159-175` hardcodes `tokens=[]`, `derived.exits={}`, `pois=[]`, `entities=[]`; `map_emit.py:311-315` defers tokens to "ADR-096 Phase 3 … out of scope for Phase E" |
| **Rich cell/feature renderer** | `DungeonMapRenderer` + `LegacyTacticalGridData` | ❌ Dead code | No protocol payload carries `cells`/`legend`/`features`; nothing populates `ExploredRoom.grid`; `MapWidget.tsx:298-304` confesses "no current world emits … leave it unconsumed until a wire-to-LegacyTacticalGridData parser lands" — that parser never landed |

**Net effect during a Sünden descent:** the player sees a black-and-white pen-and-ink cavern PNG with *nothing on it* — no tokens, no exits, no hazards, no cover. The narrator describes the rope-spider dropping from the worked stone and the water at the knees (Pattern 5 — LLM compensation), while `tactical_grid.emitted` fires an honest span over a hollow payload (Pattern 4 — OTEL blind spot). The map is a screensaver.

The failure patterns at play (per sq-wire-it): **#2 Deferral Cascade** ("until X lands"), **#3 Test-Passing Illusion** (DungeonMapRenderer fully built + tested, zero production consumers), **#4 OTEL Blind Spot**, **#5 LLM Compensation**.

## 2. Goal & scope

Build the tactical-data pipeline **end to end** — the map generator becomes the source of tactical truth, the protocol carries it, the live renderer draws it — as **one coherent pipeline, sequenced tokens → features**.

**v1 depth: pure visual/positional.** Markers show *where* things are (party + creatures, exits, water, hazards, cover, choke points) with **zero enforced mechanics**. The narrator and the WWN binding adjudicate exactly as today; the map becomes *readable*, not *authoritative*. This keeps us clear of the ADR-143 trap (no native tactical-mechanics engine layered on a bound ruleset) while delivering a map that finally informs.

**Built to expand.** Every feature carries `feature_type` + `label` now, shaped so a `mechanics` sub-object (WWN cover effect, movement cost, save) attaches in **v2 without a reshape**. Expansion path: v2 = surface WWN's *own* math; later = whatever the table needs.

**In scope (v1):** token placement, feature/exit/POI/choke emission, deterministic generation, additive protocol, live renderer overlay + legend, OTEL at every seam, retirement of the dead Layer-3 island. Proving ground is `beneath_sunden`; the pipeline generalizes to any procedural/cavern world but only Sünden is wired in v1.

**Out of scope (v2+):** enforced mechanics (AC/move-cost/saves), authored multi-room SVG maps, token movement/actions, non-procedural worlds.

## 3. Architecture

```
materialize()  [server: dungeon/materializer.py]
  _stage_fill     → grid (WALL/FLOOR)                          [existing]
  _stage_curate   → creatures (deterministic, Amendment C)     [existing]
  _stage_tactical → RegionTactical{ features[], anchors[] }    [NEW — seeded by region_id]
  _stage_commit   → persist RegionTactical alongside mask BLOB [extend existing commit]
        ↓ (PgDungeonRepository / dungeon_store — one IO seam)
map_emit.py:_maybe_build_runtime_cavern_payload  [server]
  load mask + RegionTactical
  place LIVE tokens (party PCs at room_id + encounter creatures) onto anchors
  build TacticalGridPayload{ tokens✓, derived.exits/pois✓, features[]✓ }
  OTEL: tactical_grid.emitted carries token/feature/exit/poi counts
        ↓ (TACTICAL_GRID message — envelope unchanged)
tacticalGridFromWire → TacticalGridData  [ui — parse new fields]
        ↓
TacticalGridRenderer  [ui]
  cavern PNG  +  token layer (now populated)  +  feature overlay + legend + exit/POI markers
```

**Load-bearing decision — static vs live split:**
- **Features + anchors are generated once and persisted** (the generator *is* the source of tactical truth; emit does not re-derive them).
- **Tokens are placed at emit time from live game state** onto the persisted anchors (which PCs are here, which creatures are alive changes every turn; features don't).

## 4. Server design

### 4.1 `_stage_tactical` (new materializer stage)

Runs after `_stage_fill` + `_stage_curate`. **Fully seeded by `region_id`** — no `random`, no clock (resume-safe; same seed → identical output; consistent with ADR-106 Amendment C determinism). Produces a `RegionTactical` value object:

```python
@dataclass(frozen=True)
class TacticalFeatureCell:
    feature_type: str          # FeatureType: cover | hazard | difficult_terrain | water | atmosphere | interactable
    cell: tuple[int, int]      # (x, y) into the mask grid
    label: str                 # player-facing one-liner ("knee-deep black water")
    # v2 expansion slot: mechanics: TacticalMechanics | None = None

@dataclass(frozen=True)
class TokenAnchor:
    cell: tuple[int, int]
    role: str                  # "entrance" | "creature"

@dataclass(frozen=True)
class RegionTactical:
    region_id: str
    features: list[TacticalFeatureCell]
    anchors: list[TokenAnchor]
    exits: dict[str, tuple[int, int]]   # bearing -> threshold cell  (fills derived.exits)
    pois: list[tuple[int, int]]         # feature anchors            (fills derived.pois)
```

Feature derivation sources (v1 — all from data that already exists, no new authoring required):
- **Topology-derived** (pure function of grid + region graph): `exits` (threshold floor cell per region bearing — currently `{}`), `choke` cells (floor cells in 1-wide passages / articulation points — the bottleneck analysis the audit flagged absent; rendered as `difficult_terrain` glyph in v1 or a dedicated `choke` glyph), `pois`.
- **Theme-derived:** `water` from `drowned_cavern`-family themes; theme palettes already declare register/motifs we map to feature density.
- **Set-piece-derived:** `hazard` from `collapse_gallery`; `cover` from rubble/pillar set-pieces; `interactable` from reliquary/teleporter special rooms. These already carry semantic intent in `cookbook/special_rooms.yaml`.

Token anchors: one `entrance` anchor near the inbound bearing's threshold cell; N `creature` anchors distributed on floor cells away from the entrance (deterministic scatter).

### 4.2 Persistence

`RegionTactical` persists in the same record as the mask BLOB, via the existing `dungeon_store` / `PgDungeonRepository` seam (extend `RegionMask.to_dict()` / `load_masks()` to round-trip a `tactical` block, or a sibling `load_tactical()` — Dev/plan decides the minimal extension). One IO seam; DDL via Alembic if a column is added (never hand-write CREATE TABLE).

### 4.3 Emit — `_maybe_build_runtime_cavern_payload`

Stays thin. After loading the mask:
1. Load `RegionTactical` for `room_id`.
2. Resolve **live tokens**: party PCs whose `character_locations == room_id`, plus encounter creatures bound to this room (`snapshot.encounter`). Map each to a `TokenPayload` and assign cells from anchors (entrance anchor → first-arriving PCs by bearing; creature anchors → creatures; overflow falls to nearest free floor cell, deterministic).
3. **Place only *revealed* creatures (concealment gate).** Today fog of war is region-granular only — once a PC is in a room the entire mask renders, with no intra-room concealment. So placing *every* encounter creature as a token the instant the party enters would **spoil ambushes** (the rope-spider that "drops on what passes the seam" would just sit on the map). v1 places only creatures that are **revealed/active** in the encounter (tied to encounter state), never pre-ambush ones. True cell-level fog of war / light radius / line-of-sight is a deliberate **follow-up**, not v1.
4. Build `TacticalGridPayload` with populated `tokens`, `derived.exits`/`pois`, and the new `features` list.
5. **No silent fallback:** a missing `RegionTactical` for a materialized region is loud (`tactical_grid.tactical_missing` watcher event) — it means generation didn't run the stage, which is a real bug, not an empty-room.

## 5. Protocol design (additive only)

`TacticalGridPayload` already declares `tokens: list[TokenPayload]` and `derived: DerivedRoomData`. Changes:
- **Populate** `tokens` and `derived.exits`/`pois` (were empty).
- **Add** `features: list[TacticalFeature]`:
  ```python
  class TacticalFeature(ProtocolBase):
      feature_type: str    # FeatureType vocabulary
      cell: tuple[int, int]
      label: str
      # v2: mechanics: TacticalMechanics | None = None
  ```
- All additive with empty defaults → the static-authored cavern path and every existing protocol/UI test keeps passing untouched. Worlds without tactical data simply emit `features=[]`.

UI mirror: extend `TacticalGridData` (`src/types/tactical.ts`) with `features` and update `tacticalGridFromWire` to parse it.

## 6. UI design

### 6.1 Grow the live image path (`TacticalGridRenderer.tsx`)
- **Token layer:** already coded (lines 80-105) — now it has data. Keep; verify faction colors + initials.
- **Feature overlay (new):** for each `feature`, render a marker at `cell.x*cellSize, cell.y*cellSize` with glyph + color per `FeatureType` — **salvaged from the dead `DungeonMapRenderer`** (its `FeatureType`→glyph/color maps are the *good* part). `title` tooltip = `label`.
- **Legend (new):** compact panel listing the `FeatureType`s present in the room (reuse `FeatureDef`).
- **Exit + POI markers (new):** from `derived.exits` (threshold cells, bearing-labeled) and `derived.pois`.
- **Token selection:** click → inspection panel (positional, already partially present via `CavernActionPanel`).

### 6.2 Honesty fix (no dead stubs)
The `onAction = (_id) => { /* wired by future story */ }` stub (line 117) currently presents action buttons that do nothing. v1: token select shows an **inspection** panel (name, class, HP, AC, position); non-functional movement/action buttons are **hidden**, not stubbed. No dead button claiming a future. (Per CLAUDE.md No Stubbing.)

### 6.3 Retire the dead Layer-3 island
Remove (git history preserves them):
- `DungeonMapRenderer.tsx`
- `buildDungeonLayout` + the `roomsWithGrids` branch in `Automapper.tsx`
- the `grid?: LegacyTacticalGridData` field on `ExploredRoom`
- the `MapWidget.tsx:298-304` "parser never landed" comment + dead `grid` wiring
- `LegacyTacticalGridData` / `PlacedRoomData` / `DungeonLayoutData` types and their orphaned tests

**Salvage** `FeatureType` / `FeatureDef` into the live path before deleting. Safe to remove: the `roomsWithGrids` branch is provably unreachable — nothing on the wire sets `.grid` (MapWidget only ever sets `.cavernGrid`).

## 7. OTEL — fix the "honest span, hollow payload" trap

The audit was hard *because* a span fired over an empty payload. OTEL is therefore first-class here:
- **Enrich** `tactical_grid.emitted` → add `token_count`, `feature_count`, `exit_count`, `poi_count`. A populated grid now proves itself on the GM panel; an unexpected `0` is visible.
- **New** `dungeon.tactical.placed` at the generation seam — `region_id`, per-type feature counts, anchor count. The GM panel sees the generator producing tactical truth.
- **New** `tactical_grid.tokens_placed` at emit — `party_count`, `creature_count`. Distinguishes "empty room" from "placement broke."
- **New** `tactical_grid.tactical_missing` (warning) — materialized region with no `RegionTactical` (loud, never silent).

## 8. Testing strategy

Per CLAUDE.md "Every Test Suite Needs a Wiring Test" and "No Source-Text Wiring Tests" (use OTEL-span / fixture-driven behavior tests, never `read_text()` greps):

- **Server unit:** `_stage_tactical` determinism — same `region_id` seed → identical features/anchors; topology derivation (chokes, exit thresholds) on a known fixture grid.
- **Server wiring test (the one that would have caught this):** fixture-driven — synthetic genre pack + snapshot with a party PC at a materialized region + a persisted `RegionTactical`, fire the real `_maybe_emit_tactical_grid`, assert the emitted `TACTICAL_GRID` message carries non-empty `tokens` **and** `features`. (Mirror of the canonical `test_location_description_emit.py` shape.)
- **Server OTEL assertions:** drive a turn → assert `tactical_grid.emitted` carries `feature_count>0` and `dungeon.tactical.placed` fired.
- **UI unit:** `TacticalGridRenderer` renders feature markers + tokens + legend from a fixture payload; `tacticalGridFromWire` parses the new fields.
- **UI wiring:** `MapWidget` routes a features-bearing `cavern_payload` to `TacticalGridRenderer`.

## 9. Determinism & resume-safety

All generation-time placement is seeded by `region_id` (no `random`/`Date.now`/`new Date()` — those break resume and are banned in the dungeon path). Re-materialization on resume yields byte-identical tactical data. Live token placement is a pure function of (anchors, snapshot) — deterministic given the same game state.

## 10. ADR & artifacts

- Lands as an **ADR-096 amendment** ("Cavern Renderer Revival — completes the deferred token/feature phase"), cross-referencing ADR-106 (procedural source) and ADR-109 (location manifest as a future feature source). It explicitly records: (a) generator is the tactical-truth source; (b) image-overlay path chosen over reviving the SVG renderer; (c) `DungeonMapRenderer` retired; (d) v1 is display-only by ADR-143 doctrine, with a named v2 expansion to WWN math.
- Cross-references prior Sünden work: `2026-06-22-static-procedural-crossing-design.md`, `2026-06-22-sunden-crossing-FINDINGS.md`.

## 11. Open questions for the plan

- Minimal persistence shape for `RegionTactical` — extend the mask BLOB dict vs. a sibling column/store (Alembic migration if a column).
- `choke` rendering in v1 — reuse the `difficult_terrain` glyph, or add a dedicated `choke` glyph to the salvaged `FeatureType` map.
- Overflow rule when live tokens exceed anchors (deterministic nearest-free-floor — confirm tie-break ordering).
