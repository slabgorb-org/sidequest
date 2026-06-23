# Sünden Tactical Map — Token + Feature Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the procedural Sünden tactical map carry real tactical information — party/creature tokens, terrain features, exits, POIs — sourced from the dungeon generator and rendered on the live cavern image, replacing today's hollow payload and retiring the dead SVG renderer.

**Architecture:** The map generator (`materializer.py`) gains a deterministic `_stage_tactical` stage that derives feature cells + token anchors + exit-threshold cells from the filled grid, theme, and set-pieces; this persists alongside the mask BLOB as a `tactical` dict key. At emit time (`map_emit.py`), `_maybe_build_runtime_cavern_payload` loads it, places only *revealed* live tokens onto anchors, and builds an additive `TacticalGridPayload` (`features[]`, populated `tokens`/`derived`). The UI's live `TacticalGridRenderer` grows a feature/legend/exit overlay (salvaging the dead `DungeonMapRenderer`'s glyph vocabulary); the dead SVG renderer is deleted.

**Tech Stack:** Python 3 / pydantic v2 (server, protocol), React 19 / TypeScript / Vite / Vitest (ui), pytest (server). OTEL via `watcher_hub.publish_event` + span modules.

**Source spec:** `docs/superpowers/specs/2026-06-23-sunden-tactical-map-design.md`

## Global Constraints

- **v1 is pure visual/positional.** Features carry `feature_type` + `cell` + `label` ONLY. NO enforced mechanics (no AC/move-cost/saves). Do not add a native tactical-mechanics engine (ADR-143 — bind the ruleset, don't balance it).
- **Determinism / resume-safety.** All generation-time placement is seeded by `region_id`. No `random`, no `Date.now()`, no `new Date()`. Same region_id → byte-identical tactical data.
- **No silent fallbacks.** A materialized region with no persisted `tactical` block is a loud `tactical_grid.tactical_missing` watcher event, never a silent empty grid.
- **Additive protocol only.** Every new payload field defaults empty so the static-authored cavern path and all existing tests keep passing untouched.
- **No source-text wiring tests.** Use fixture-driven behavior tests + OTEL span assertions (never `read_text()` greps). Reference shape: `tests/server/test_location_description_emit.py`.
- **Concealment gate.** Place only *revealed/active* encounter creatures as tokens — never pre-ambush ones (there is no intra-room fog of war yet).
- **Server tests:** `cd sidequest-server && uv run pytest`. **UI tests:** `cd sidequest-ui && npx vitest run`.
- **Branch base:** `sidequest-server`/`sidequest-ui`/`sidequest-content` all target `develop` (github-flow). Orchestrator docs target `main`.

---

### Task 1: Add `TacticalFeature` protocol model + extend `TacticalGridPayload`

**Files:**
- Modify: `sidequest-server/sidequest/protocol/models.py` (after `DerivedRoomData`, ~line 706; and `TacticalGridPayload`, lines 1271-1307)
- Test: `sidequest-server/tests/protocol/test_tactical_feature_payload.py`

**Interfaces:**
- Produces: `TacticalFeature(feature_type: str, cell: tuple[int,int], label: str)`; `TacticalGridPayload.features: list[TacticalFeature]` (default `[]`).

- [ ] **Step 1: Write the failing test**

```python
# tests/protocol/test_tactical_feature_payload.py
from sidequest.protocol.models import TacticalFeature, TacticalGridPayload


def test_tactical_feature_serializes_round_trip():
    f = TacticalFeature(feature_type="water", cell=(3, 4), label="knee-deep black water")
    dumped = f.model_dump()
    assert dumped == {"feature_type": "water", "cell": [3, 4], "label": "knee-deep black water"}


def test_payload_features_default_empty_and_omitted():
    # Additive: existing cavern payloads with no features serialize without the key
    # (ProtocolBase omits empty-list defaults).
    p = TacticalGridPayload(room_id="r0", room_name="r0", room_type="cavern")
    assert p.features == []
    assert "features" not in p.model_dump()


def test_payload_carries_features_when_present():
    p = TacticalGridPayload(
        room_id="r0",
        room_name="r0",
        room_type="cavern",
        features=[TacticalFeature(feature_type="hazard", cell=(1, 2), label="loose ceiling")],
    )
    dumped = p.model_dump()
    assert dumped["features"] == [{"feature_type": "hazard", "cell": [1, 2], "label": "loose ceiling"}]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/protocol/test_tactical_feature_payload.py -v`
Expected: FAIL — `ImportError: cannot import name 'TacticalFeature'`

- [ ] **Step 3: Add the model + field**

In `sidequest/protocol/models.py`, add after `DerivedRoomData` (line 706):

```python
class TacticalFeature(ProtocolBase):
    """A positioned tactical-map feature marker (ADR-096 token+feature phase).

    v1 is pure visual/positional — ``feature_type`` + ``cell`` + ``label`` only.
    A future ``mechanics`` field attaches WWN math without reshaping this.
    """

    feature_type: str
    """One of the UI FeatureType vocabulary: cover|hazard|difficult_terrain|water|atmosphere|interactable."""
    cell: tuple[int, int]
    """(x, y) cell into the mask grid."""
    label: str
    """Player-facing one-liner shown on hover."""
```

Then in `TacticalGridPayload` (after the `entities` field, ~line 1307) add:

```python
    features: list[TacticalFeature] = Field(default_factory=list)
    """Positioned tactical feature markers (water/hazard/cover/...). ADR-096 token+feature phase."""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/protocol/test_tactical_feature_payload.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
cd sidequest-server
git add sidequest/protocol/models.py tests/protocol/test_tactical_feature_payload.py
git commit -m "feat(protocol): TacticalFeature model + additive features[] on TacticalGridPayload (158-18)"
```

---

### Task 2: Pure tactical-derivation module (`sidequest/dungeon/tactical.py`)

The deterministic heart: turn a filled grid + theme + set-pieces into feature cells, token anchors, POIs, and exit-threshold cells. Pure function, no IO, seeded by `region_id`.

**Files:**
- Create: `sidequest-server/sidequest/dungeon/tactical.py`
- Test: `sidequest-server/tests/dungeon/test_tactical_derivation.py`

**Interfaces:**
- Consumes: a grid as `list[list[int]]` (WALL=1, FLOOR=0 — the `RegionFill.grid` shape).
- Produces:
  - `TacticalFeatureCell(feature_type: str, cell: tuple[int,int], label: str)`
  - `TokenAnchor(cell: tuple[int,int], role: str)`  # role: "entrance" | "creature"
  - `RegionTactical(region_id: str, features: list[TacticalFeatureCell], anchors: list[TokenAnchor], pois: list[tuple[int,int]], exit_thresholds: dict[str, tuple[int,int]])`  # exit_thresholds: neighbor_region_id -> cell
  - `derive_region_tactical(*, region_id: str, grid: list[list[int]], theme_key: str, neighbor_ids: list[str], hazard_setpieces: list[str], creature_count: int) -> RegionTactical`
  - `WATER_THEMES: frozenset[str]` (themes that flood)

- [ ] **Step 1: Write the failing test**

```python
# tests/dungeon/test_tactical_derivation.py
from sidequest.dungeon.tactical import (
    RegionTactical,
    derive_region_tactical,
)

# A 5x5 room: border walls, floor interior, a 1-wide neck at row 2.
GRID = [
    [1, 1, 1, 1, 1],
    [1, 0, 0, 0, 1],
    [1, 1, 0, 1, 1],  # neck: only (2,2) is floor in this row
    [1, 0, 0, 0, 1],
    [1, 1, 1, 1, 1],
]


def test_determinism_same_seed_same_output():
    a = derive_region_tactical(
        region_id="exp001.r0", grid=GRID, theme_key="drowned_cavern",
        neighbor_ids=["entrance"], hazard_setpieces=[], creature_count=2,
    )
    b = derive_region_tactical(
        region_id="exp001.r0", grid=GRID, theme_key="drowned_cavern",
        neighbor_ids=["entrance"], hazard_setpieces=[], creature_count=2,
    )
    assert a == b
    assert isinstance(a, RegionTactical)


def test_chokepoint_detected_as_difficult_terrain():
    t = derive_region_tactical(
        region_id="r", grid=GRID, theme_key="bone_crypt",
        neighbor_ids=[], hazard_setpieces=[], creature_count=0,
    )
    choke_cells = {f.cell for f in t.features if f.feature_type == "difficult_terrain"}
    assert (2, 2) in choke_cells  # the 1-wide neck


def test_water_theme_floods_some_floor():
    t = derive_region_tactical(
        region_id="r", grid=GRID, theme_key="drowned_cavern",
        neighbor_ids=[], hazard_setpieces=[], creature_count=0,
    )
    assert any(f.feature_type == "water" for f in t.features)


def test_non_water_theme_no_water():
    t = derive_region_tactical(
        region_id="r", grid=GRID, theme_key="bone_crypt",
        neighbor_ids=[], hazard_setpieces=[], creature_count=0,
    )
    assert not any(f.feature_type == "water" for f in t.features)


def test_anchors_on_floor_and_counts_match():
    t = derive_region_tactical(
        region_id="r", grid=GRID, theme_key="bone_crypt",
        neighbor_ids=[], hazard_setpieces=[], creature_count=3,
    )
    assert sum(1 for a in t.anchors if a.role == "entrance") == 1
    assert sum(1 for a in t.anchors if a.role == "creature") == 3
    for a in t.anchors:
        x, y = a.cell
        assert GRID[y][x] == 0  # every anchor is on floor


def test_hazard_setpiece_places_hazard():
    t = derive_region_tactical(
        region_id="r", grid=GRID, theme_key="bone_crypt",
        neighbor_ids=[], hazard_setpieces=["collapse_gallery"], creature_count=0,
    )
    assert any(f.feature_type == "hazard" for f in t.features)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/dungeon/test_tactical_derivation.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'sidequest.dungeon.tactical'`

- [ ] **Step 3: Write the implementation**

```python
# sidequest/dungeon/tactical.py
"""Deterministic tactical-feature derivation for procedural rooms (ADR-096).

Pure functions: given a filled grid (WALL=1/FLOOR=0), the region theme, the
region's neighbours, and its hazard set-pieces, derive the positioned tactical
data the cavern map renders — feature cells, token anchors, POIs, and per-
neighbour exit-threshold cells. Seeded by ``region_id`` so the same region
yields byte-identical output on resume (no ``random``, no clock).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

FLOOR = 0
WALL = 1

# Themes whose register floods low floor (drowned/sunken families). Display-only.
WATER_THEMES: frozenset[str] = frozenset({"drowned_cavern", "sunken_temple", "sunless_temple"})

# Fraction of floor cells the water theme floods (deterministic pick, lowest cells first).
_WATER_FRACTION = 0.18


@dataclass(frozen=True, slots=True)
class TacticalFeatureCell:
    feature_type: str  # cover|hazard|difficult_terrain|water|atmosphere|interactable
    cell: tuple[int, int]
    label: str


@dataclass(frozen=True, slots=True)
class TokenAnchor:
    cell: tuple[int, int]
    role: str  # "entrance" | "creature"


@dataclass(frozen=True, slots=True)
class RegionTactical:
    region_id: str
    features: list[TacticalFeatureCell] = field(default_factory=list)
    anchors: list[TokenAnchor] = field(default_factory=list)
    pois: list[tuple[int, int]] = field(default_factory=list)
    exit_thresholds: dict[str, tuple[int, int]] = field(default_factory=dict)


def _seed(region_id: str) -> int:
    """Stable integer seed from the region id (resume-safe; no clock/random)."""
    return int.from_bytes(hashlib.sha256(region_id.encode("utf-8")).digest()[:8], "big")


def _floor_cells(grid: list[list[int]]) -> list[tuple[int, int]]:
    """All FLOOR cells in stable (y, then x) order."""
    cells: list[tuple[int, int]] = []
    for y, row in enumerate(grid):
        for x, v in enumerate(row):
            if v == FLOOR:
                cells.append((x, y))
    return cells


def _floor_neighbors(grid: list[list[int]], x: int, y: int) -> int:
    n = 0
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if 0 <= ny < len(grid) and 0 <= nx < len(grid[ny]) and grid[ny][nx] == FLOOR:
            n += 1
    return n


def _chokepoints(grid: list[list[int]]) -> list[tuple[int, int]]:
    """Floor cells in a 1-wide passage (<=2 orthogonal floor neighbours)."""
    return [(x, y) for (x, y) in _floor_cells(grid) if _floor_neighbors(grid, x, y) <= 2]


def _deterministic_sample(items: list, k: int, seed: int) -> list:
    """Pick k items deterministically (seeded rotation), preserving input order."""
    if k <= 0 or not items:
        return []
    if k >= len(items):
        return list(items)
    start = seed % len(items)
    step = max(1, len(items) // k)
    out, i = [], start
    while len(out) < k:
        out.append(items[i % len(items)])
        i += step
    # de-dup preserving order
    seen, uniq = set(), []
    for c in out:
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    # top up if dedup shrank it
    for c in items:
        if len(uniq) >= k:
            break
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    return uniq[:k]


def derive_region_tactical(
    *,
    region_id: str,
    grid: list[list[int]],
    theme_key: str,
    neighbor_ids: list[str],
    hazard_setpieces: list[str],
    creature_count: int,
) -> RegionTactical:
    """Derive all tactical data for one region. Pure + deterministic."""
    seed = _seed(region_id)
    floor = _floor_cells(grid)
    features: list[TacticalFeatureCell] = []

    # 1. Chokepoints -> difficult_terrain markers (topology).
    chokes = _chokepoints(grid)
    for c in chokes:
        features.append(TacticalFeatureCell("difficult_terrain", c, "a tight squeeze — the passage narrows"))

    # 2. Water (theme), flooding the deepest-listed floor not already a choke.
    if theme_key in WATER_THEMES:
        non_choke = [c for c in floor if c not in set(chokes)]
        k = max(1, int(len(non_choke) * _WATER_FRACTION))
        for c in _deterministic_sample(non_choke, k, seed):
            features.append(TacticalFeatureCell("water", c, "black water, depth uncertain"))

    # 3. Hazard set-pieces -> one hazard marker each, on distinct floor cells.
    if hazard_setpieces:
        spots = _deterministic_sample(floor, len(hazard_setpieces), seed ^ 0x9E3779B9)
        for piece, c in zip(hazard_setpieces, spots):
            features.append(TacticalFeatureCell("hazard", c, f"{piece.replace('_', ' ')} — unstable"))

    # 4. Token anchors: entrance anchor first floor cell; creatures spread after.
    anchors: list[TokenAnchor] = []
    if floor:
        anchors.append(TokenAnchor(floor[0], "entrance"))
        creature_pool = floor[1:] or floor
        for c in _deterministic_sample(creature_pool, creature_count, seed ^ 0x85EBCA6B):
            anchors.append(TokenAnchor(c, "creature"))

    # 5. POIs: the hazard + interactable feature cells are points of interest.
    pois = [f.cell for f in features if f.feature_type in ("hazard", "interactable")]

    # 6. Exit thresholds: deterministically assign one floor cell per neighbour.
    exit_thresholds: dict[str, tuple[int, int]] = {}
    if floor and neighbor_ids:
        picks = _deterministic_sample(floor, len(neighbor_ids), seed ^ 0xC2B2AE35)
        for nid, c in zip(neighbor_ids, picks):
            exit_thresholds[nid] = c

    return RegionTactical(
        region_id=region_id,
        features=features,
        anchors=anchors,
        pois=pois,
        exit_thresholds=exit_thresholds,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/dungeon/test_tactical_derivation.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
cd sidequest-server
git add sidequest/dungeon/tactical.py tests/dungeon/test_tactical_derivation.py
git commit -m "feat(dungeon): deterministic tactical derivation (features/anchors/chokes/exits) (158-18)"
```

---

### Task 3: `RegionTactical` (de)serialization + persist via the mask dict

Add `to_dict`/`from_dict` so the tactical record rides the existing `mask` BLOB as a `tactical` key — backend-agnostic (works for both the SQLite and Pg `DungeonRepository`, since both round-trip the JSON dict).

**Files:**
- Modify: `sidequest-server/sidequest/dungeon/tactical.py`
- Test: `sidequest-server/tests/dungeon/test_tactical_serialization.py`

**Interfaces:**
- Produces: `RegionTactical.to_dict() -> dict`; `RegionTactical.from_dict(d: dict) -> RegionTactical`.

- [ ] **Step 1: Write the failing test**

```python
# tests/dungeon/test_tactical_serialization.py
from sidequest.dungeon.tactical import RegionTactical, TacticalFeatureCell, TokenAnchor


def test_to_from_dict_round_trip():
    t = RegionTactical(
        region_id="exp001.r0",
        features=[TacticalFeatureCell("water", (2, 3), "black water")],
        anchors=[TokenAnchor((1, 1), "entrance"), TokenAnchor((3, 3), "creature")],
        pois=[(2, 3)],
        exit_thresholds={"entrance": (1, 1)},
    )
    restored = RegionTactical.from_dict(t.to_dict())
    assert restored == t


def test_to_dict_is_json_safe():
    import json

    t = RegionTactical(region_id="r", features=[TacticalFeatureCell("hazard", (0, 0), "x")])
    json.dumps(t.to_dict())  # must not raise
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/dungeon/test_tactical_serialization.py -v`
Expected: FAIL — `AttributeError: type object 'RegionTactical' has no attribute 'from_dict'`

- [ ] **Step 3: Add the methods**

Append to `RegionTactical` in `sidequest/dungeon/tactical.py` (convert the `@dataclass(frozen=True)` to keep methods — add methods to the class body):

```python
    def to_dict(self) -> dict:
        return {
            "region_id": self.region_id,
            "features": [
                {"feature_type": f.feature_type, "cell": list(f.cell), "label": f.label}
                for f in self.features
            ],
            "anchors": [{"cell": list(a.cell), "role": a.role} for a in self.anchors],
            "pois": [list(p) for p in self.pois],
            "exit_thresholds": {k: list(v) for k, v in self.exit_thresholds.items()},
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RegionTactical":
        return cls(
            region_id=d["region_id"],
            features=[
                TacticalFeatureCell(f["feature_type"], (f["cell"][0], f["cell"][1]), f["label"])
                for f in d.get("features", [])
            ],
            anchors=[TokenAnchor((a["cell"][0], a["cell"][1]), a["role"]) for a in d.get("anchors", [])],
            pois=[(p[0], p[1]) for p in d.get("pois", [])],
            exit_thresholds={k: (v[0], v[1]) for k, v in d.get("exit_thresholds", {}).items()},
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/dungeon/test_tactical_serialization.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
cd sidequest-server
git add sidequest/dungeon/tactical.py tests/dungeon/test_tactical_serialization.py
git commit -m "feat(dungeon): RegionTactical to_dict/from_dict for mask-blob persistence (158-18)"
```

---

### Task 4: Wire `_stage_tactical` into `materialize()` and persist into the mask dict

**Files:**
- Modify: `sidequest-server/sidequest/dungeon/materializer.py` (add `_stage_tactical`; call it in `materialize()` after `_stage_fill`/`_stage_curate`; thread its result into `_stage_commit`)
- Modify: `sidequest-server/sidequest/dungeon/persistence.py` (the commit site that builds the per-region mask dict, ~lines 309-312 — add the `tactical` key)
- Test: `sidequest-server/tests/dungeon/test_stage_tactical_wiring.py`

**Interfaces:**
- Consumes: `fill_result: dict[str, RegionFill]`, `expansion` (for per-region neighbours), `curation` (for set-pieces/creature counts).
- Produces: `_stage_tactical(...) -> dict[str, RegionTactical]`; persisted mask dict gains `"tactical": RegionTactical.to_dict()`.

- [ ] **Step 1: Write the failing test (fixture-driven wiring test)**

```python
# tests/dungeon/test_stage_tactical_wiring.py
"""Wiring test: materialize() runs the tactical stage and persists it in the mask dict."""
from sidequest.dungeon.tactical import RegionTactical


def test_stage_tactical_produces_record_per_filled_region(tactical_fill_fixture):
    # tactical_fill_fixture provides (fill_result, expansion, curation) for 2 regions.
    from sidequest.dungeon.materializer import _stage_tactical

    fill_result, expansion, curation = tactical_fill_fixture
    out = _stage_tactical(expansion=expansion, fill_result=fill_result, curation=curation)
    assert set(out.keys()) == set(fill_result.keys())
    for region_id, rt in out.items():
        assert isinstance(rt, RegionTactical)
        assert rt.region_id == region_id


def test_persisted_mask_dict_carries_tactical(tactical_fill_fixture):
    from sidequest.dungeon.materializer import _stage_tactical, _tactical_into_mask_dicts

    fill_result, expansion, curation = tactical_fill_fixture
    tactical = _stage_tactical(expansion=expansion, fill_result=fill_result, curation=curation)
    mask_dicts = {rid: fr.mask.to_dict() for rid, fr in fill_result.items() if fr.mask}
    merged = _tactical_into_mask_dicts(mask_dicts, tactical)
    for rid in merged:
        assert "tactical" in merged[rid]
        RegionTactical.from_dict(merged[rid]["tactical"])  # must parse
```

Add the fixture to `tests/dungeon/conftest.py`:

```python
import pytest
from sidequest.dungeon.materializer import RegionFill, RegionMask, BlockInfo

_GRID = [[1, 1, 1], [1, 0, 1], [1, 1, 1]]


def _fill(region_id):
    mask = RegionMask(grid=_GRID, mask_bytes=b"###\n#.#\n###", mask_sha="deadbeef",
                      block=BlockInfo(cell_width=28, grid_width=3, grid_height=3))
    return RegionFill(region_id=region_id, algorithm="cellular", width=3, height=3,
                      braid_ratio=0.0, grid=_GRID, mask=mask)


class _Expansion:
    # minimal stand-in: region -> neighbour ids; theme per region
    def neighbors(self, region_id): return []
    def theme_key(self, region_id): return "bone_crypt"


class _Curation:
    def hazard_setpieces(self, region_id): return []
    def creature_count(self, region_id): return 1


@pytest.fixture
def tactical_fill_fixture():
    fill = {"exp001.r0": _fill("exp001.r0"), "exp001.r1": _fill("exp001.r1")}
    return fill, _Expansion(), _Curation()
```

> NOTE for implementer: inspect the real `Expansion` / `RegionCuration` types in `materializer.py` and adapt `_stage_tactical` to read neighbours / theme / set-pieces / creature counts from their ACTUAL accessors. The fixture's `_Expansion`/`_Curation` define the minimal shape `_stage_tactical` must consume; mirror those method names on the real types or adjust `_stage_tactical` to the real ones. Keep `_stage_tactical` a thin adapter over `derive_region_tactical`.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/dungeon/test_stage_tactical_wiring.py -v`
Expected: FAIL — `ImportError: cannot import name '_stage_tactical'`

- [ ] **Step 3: Implement the stage + persistence helper**

In `materializer.py`, add:

```python
from sidequest.dungeon.tactical import RegionTactical, derive_region_tactical


def _stage_tactical(
    *,
    expansion,
    fill_result: dict[str, RegionFill],
    curation,
) -> dict[str, RegionTactical]:
    """Derive deterministic tactical data per filled region (ADR-096 token+feature).

    Thin adapter over ``derive_region_tactical`` — reads neighbours/theme from
    ``expansion`` and set-pieces/creature counts from ``curation``. Pure given
    its inputs; placement is seeded by region_id inside the derivation.
    """
    out: dict[str, RegionTactical] = {}
    for region_id, fill in fill_result.items():
        out[region_id] = derive_region_tactical(
            region_id=region_id,
            grid=fill.grid,
            theme_key=expansion.theme_key(region_id),
            neighbor_ids=list(expansion.neighbors(region_id)),
            hazard_setpieces=list(curation.hazard_setpieces(region_id)),
            creature_count=curation.creature_count(region_id),
        )
    return out


def _tactical_into_mask_dicts(
    mask_dicts: dict[str, dict],
    tactical: dict[str, RegionTactical],
) -> dict[str, dict]:
    """Merge each region's tactical record into its mask dict under ``tactical``."""
    for region_id, rt in tactical.items():
        if region_id in mask_dicts:
            mask_dicts[region_id]["tactical"] = rt.to_dict()
    return mask_dicts
```

In `materialize()` (after the `_stage_curate` `with` block, before the transaction), add:

```python
    with dungeon_materialize_curate_span(...):  # existing
        curation = await _stage_curate(...)     # existing

    # ADR-096 token+feature: derive tactical data from the filled grid (deterministic).
    tactical = _stage_tactical(expansion=expansion, fill_result=fill_result, curation=curation)
```

Then thread `tactical` to commit: pass it into `_stage_commit(... , tactical=tactical)` and, at the persistence site in `persistence.py` (the `mask_blob` build, ~lines 309-312), merge before JSON-encoding:

```python
    mask_blob: bytes | None = None
    if masks is not None and live.id in masks:
        mask_payload = dict(masks[live.id])  # copy
        # tactical already merged by _stage_commit via _tactical_into_mask_dicts
        try:
            mask_blob = json.dumps(mask_payload, sort_keys=True).encode("utf-8")
        except (TypeError, ValueError) as exc:
            ...
```

> Implementer: `_stage_commit` builds the `masks` dict it passes to `commit_expansion`. Call `_tactical_into_mask_dicts(masks, tactical)` there so the `tactical` key is present before `commit_expansion` JSON-encodes it. Do NOT touch the DB schema — `tactical` rides inside the existing `mask` JSON column.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/dungeon/test_stage_tactical_wiring.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
cd sidequest-server
git add sidequest/dungeon/materializer.py sidequest/dungeon/persistence.py tests/dungeon/test_stage_tactical_wiring.py tests/dungeon/conftest.py
git commit -m "feat(dungeon): run _stage_tactical in materialize; persist tactical in mask blob (158-18)"
```

---

### Task 5: Populate the emit payload — tokens (revealed only), features, exits, POIs

The wiring fix at the heart of the audit: `_maybe_build_runtime_cavern_payload` stops shipping empties.

**Files:**
- Modify: `sidequest-server/sidequest/server/websocket_handlers/map_emit.py` (`_maybe_build_runtime_cavern_payload`, lines 36-177)
- Test: `sidequest-server/tests/server/test_tactical_grid_emit_population.py`

**Interfaces:**
- Consumes: `RegionTactical.from_dict`, `assign_bearings` (already imported in this module), `snapshot.character_locations`, `snapshot.encounter`.
- Produces: a `TacticalGridPayload` with non-empty `tokens`, `features`, `derived.exits`, `derived.pois` when a `tactical` block is present.

- [ ] **Step 1: Write the failing test**

```python
# tests/server/test_tactical_grid_emit_population.py
"""Wiring test (the one that would have caught the hollow payload):
a materialized region with party + a revealed creature emits non-empty tokens + features."""
from tests.server.tactical_emit_fixtures import build_sd_with_tactical_region


def test_runtime_payload_has_tokens_and_features():
    sd, snapshot, room_id = build_sd_with_tactical_region()
    from sidequest.server.websocket_handlers.map_emit import _maybe_build_runtime_cavern_payload

    payload = _maybe_build_runtime_cavern_payload(sd=sd, room_id=room_id)
    assert payload is not None
    assert payload.features, "features must be populated from RegionTactical"
    assert payload.tokens, "tokens must be placed for the party PC present in the room"
    assert payload.derived is not None and payload.derived.pois is not None


def test_unrevealed_creature_not_placed():
    # A creature flagged not-yet-revealed (pre-ambush) must NOT appear as a token.
    sd, snapshot, room_id = build_sd_with_tactical_region(creature_revealed=False)
    from sidequest.server.websocket_handlers.map_emit import _maybe_build_runtime_cavern_payload

    payload = _maybe_build_runtime_cavern_payload(sd=sd, room_id=room_id)
    hostile = [t for t in payload.tokens if t.token_id.startswith("creature:")]
    assert hostile == [], "pre-ambush creatures must not leak onto the map"
```

> Implementer: create `tests/server/tactical_emit_fixtures.py::build_sd_with_tactical_region(creature_revealed=True)` building a synthetic `_SessionData` whose `dungeon_store.load_masks()` returns one region whose mask dict carries a `tactical` block (use `RegionTactical(...).to_dict()`), a `snapshot.character_locations` putting one PC in `room_id`, and a `snapshot.encounter` with one creature whose revealed flag is `creature_revealed`. Mirror the existing fixture style in `tests/server/test_location_description_emit.py`.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/server/test_tactical_grid_emit_population.py -v`
Expected: FAIL — payload.features empty (assertion error) / payload.tokens empty.

- [ ] **Step 3: Populate the payload**

In `_maybe_build_runtime_cavern_payload` (map_emit.py), after decoding `mask_text` (line 155) and before the `return TacticalGridPayload(...)`:

```python
        from sidequest.dungeon.tactical import RegionTactical
        from sidequest.protocol.models import TacticalFeature, TokenPayload

        tactical_raw = mask_dict.get("tactical")
        if tactical_raw is None:
            # No silent fallback: a materialized region must carry tactical data.
            _watcher_publish(
                "tactical_grid.tactical_missing",
                {"genre": sd.genre_slug, "world": sd.world_slug, "room_id": room_id},
                component="cavern_renderer",
                severity="warning",
            )
            tactical = RegionTactical(region_id=room_id)
        else:
            tactical = RegionTactical.from_dict(tactical_raw)

        features = [
            TacticalFeature(feature_type=f.feature_type, cell=f.cell, label=f.label)
            for f in tactical.features
        ]
        pois = list(tactical.pois)

        # derived.exits: pair each neighbour-threshold cell with the bearing the
        # narrator uses (assign_bearings — one source of truth so map agrees with prose).
        exits: dict[str, tuple[int, int]] = {}
        try:
            from sidequest.dungeon.region_projection import assign_bearings

            graph = sd.dungeon_repository.load_map(entrance_id="entrance")
            bearings = assign_bearings(graph, room_id) if room_id in graph.nodes else {}
            for neighbor_id, cell in tactical.exit_thresholds.items():
                bearing = bearings.get(neighbor_id)
                if bearing:
                    exits[bearing] = cell
        except Exception as exc:  # noqa: BLE001 — never crash a turn on bearing lookup
            logger.warning("tactical_grid.bearing_pair_failed room_id=%s error=%s", room_id, exc)

        # Tokens: party PCs in this room + REVEALED encounter creatures, onto anchors.
        tokens = _place_tokens_on_anchors(sd=sd, room_id=room_id, anchors=tactical.anchors)
```

Add the placement helper to `map_emit.py`:

```python
def _place_tokens_on_anchors(*, sd, room_id, anchors) -> list:
    """Place revealed live tokens onto anchors (concealment gate: no pre-ambush leak)."""
    from sidequest.protocol.models import TokenPayload

    snapshot = sd.snapshot if hasattr(sd, "snapshot") else None
    tokens: list[TokenPayload] = []
    entrance = [a for a in anchors if a.role == "entrance"]
    creature_anchors = [a for a in anchors if a.role == "creature"]

    # Party PCs whose location is this room -> entrance anchor, then spillover.
    pcs = [
        name
        for name, loc in (getattr(snapshot, "character_locations", {}) or {}).items()
        if loc == room_id
    ]
    pc_cells = ([entrance[0].cell] if entrance else []) + [a.cell for a in creature_anchors]
    for i, name in enumerate(pcs):
        if i < len(pc_cells):
            tokens.append(TokenPayload(token_id=f"pc:{name}", label=name, position=pc_cells[i]))

    # REVEALED encounter creatures only.
    enc = getattr(snapshot, "encounter", None)
    if enc is not None and getattr(enc, "creatures", None):
        revealed = [c for c in enc.creatures if getattr(c, "revealed", True)]
        for i, c in enumerate(revealed):
            if i < len(creature_anchors):
                tokens.append(
                    TokenPayload(
                        token_id=f"creature:{getattr(c, 'name', i)}",
                        label=getattr(c, "name", "?"),
                        position=creature_anchors[i].cell,
                    )
                )
    return tokens
```

Then change the `return TacticalGridPayload(...)` to use the computed values:

```python
        return TacticalGridPayload(
            room_id=room_id,
            room_name=room_id,
            room_type="cavern",
            mask=mask_text,
            cavern_image_url=cavern_image_url,
            cell_size=block["cell_width"],
            cellular=None,
            derived=DerivedRoomData(floor_count=floor_count, exits=exits, pois=pois),
            tokens=tokens,
            initiative=None,
            entities=[],
            features=features,
        )
```

> Implementer: confirm how `_SessionData` exposes the live snapshot inside this helper (the sibling `_maybe_emit_tactical_grid` receives `snapshot` as a parameter — prefer threading `snapshot` into `_maybe_build_runtime_cavern_payload` rather than `getattr(sd, "snapshot")`; update its one call site at map_emit.py:245 accordingly). Confirm the encounter-creature "revealed" attribute's real name on `StructuredEncounter.creatures` (grep `class StructuredEncounter`); if revelation is modelled differently, gate on the real field. Do NOT place a creature the encounter treats as hidden.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/server/test_tactical_grid_emit_population.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
cd sidequest-server
git add sidequest/server/websocket_handlers/map_emit.py tests/server/test_tactical_grid_emit_population.py tests/server/tactical_emit_fixtures.py
git commit -m "feat(map): populate tactical payload — revealed tokens, features, exits, pois (158-18)"
```

---

### Task 6: OTEL — enrich the emit span + new placement/missing events

**Files:**
- Modify: `sidequest-server/sidequest/server/websocket_handlers/map_emit.py` (the `tactical_grid.emitted` publish at lines 320-331)
- Test: `sidequest-server/tests/server/test_tactical_grid_otel.py`

**Interfaces:**
- Produces: `tactical_grid.emitted` fields now include `token_count`, `feature_count`, `exit_count`, `poi_count`; plus `tactical_grid.tokens_placed` event.

- [ ] **Step 1: Write the failing test**

```python
# tests/server/test_tactical_grid_otel.py
from tests.server.tactical_emit_fixtures import build_sd_with_tactical_region
from tests.helpers.watcher_capture import capture_watcher_events  # existing helper


def test_emitted_span_carries_counts():
    sd, snapshot, room_id = build_sd_with_tactical_region()
    from sidequest.server.websocket_handlers.map_emit import _maybe_emit_tactical_grid

    with capture_watcher_events() as events:
        _maybe_emit_tactical_grid(
            object(), sd=sd, snapshot=snapshot, actor="Rux",
            emit_fn=lambda *a, **k: None, room_id_override=room_id,
        )
    emitted = [e for e in events if e["event_type"] == "tactical_grid.emitted"]
    assert emitted, "tactical_grid.emitted must fire"
    fields = emitted[0]["fields"]
    assert "token_count" in fields and "feature_count" in fields
    assert fields["feature_count"] >= 1
```

> Implementer: if `tests/helpers/watcher_capture.py` does not exist, capture via the existing pattern used in `tests/server/test_location_description_emit.py` (subscribe to `watcher_hub` or assert on a fake sink). Reuse, don't reinvent.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/server/test_tactical_grid_otel.py -v`
Expected: FAIL — `assert "token_count" in fields` (KeyError / missing).

- [ ] **Step 3: Enrich the span**

In `map_emit.py`, change the `tactical_grid.emitted` publish (lines 320-331) to include counts:

```python
    _watcher_publish(
        "tactical_grid.emitted",
        {
            "genre": sd.genre_slug,
            "world": sd.world_slug,
            "room_id": room_id,
            "room_type": payload.room_type,
            "room_name": payload.room_name,
            "source": source,
            "token_count": len(payload.tokens),
            "feature_count": len(payload.features),
            "exit_count": len(payload.derived.exits) if payload.derived else 0,
            "poi_count": len(payload.derived.pois) if payload.derived else 0,
        },
        component="cavern_renderer",
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/server/test_tactical_grid_otel.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd sidequest-server
git add sidequest/server/websocket_handlers/map_emit.py tests/server/test_tactical_grid_otel.py
git commit -m "feat(otel): tactical_grid.emitted carries token/feature/exit/poi counts (158-18)"
```

---

### Task 7: UI — extend types + wire parser to carry `features`

**Files:**
- Modify: `sidequest-ui/src/types/tactical.ts` (`TacticalGridData` lines 154-167; add `TacticalFeatureMarker`)
- Modify: `sidequest-ui/src/lib/tacticalGridFromWire.ts` (full file, 59 lines)
- Modify: `sidequest-ui/src/components/MapOverlay.tsx` (`cavern_payload` inline type, lines 44-69)
- Test: `sidequest-ui/src/lib/__tests__/tacticalGridFromWire.features.test.ts`

**Interfaces:**
- Produces: `TacticalFeatureMarker { feature_type: FeatureType; cell: {x,y}; label: string }`; `TacticalGridData.features: readonly TacticalFeatureMarker[]`.

- [ ] **Step 1: Write the failing test**

```typescript
// src/lib/__tests__/tacticalGridFromWire.features.test.ts
import { describe, it, expect } from "vitest";
import { tacticalGridFromWire } from "@/lib/tacticalGridFromWire";

const wire = {
  room_id: "exp001.r0", room_name: "exp001.r0", room_type: "cavern" as const,
  mask: "###\n#.#\n###", cavern_image_url: "/x.png", cell_size: 28, cellular: null,
  derived: { floor_count: 1, exits: {}, pois: [[1, 1]] as [number, number][] },
  tokens: [],
  features: [{ feature_type: "water" as const, cell: { x: 1, y: 1 }, label: "black water" }],
};

describe("tacticalGridFromWire features", () => {
  it("maps features through", () => {
    const grid = tacticalGridFromWire(wire);
    expect(grid).not.toBeNull();
    expect(grid!.features).toEqual([
      { feature_type: "water", cell: { x: 1, y: 1 }, label: "black water" },
    ]);
  });

  it("defaults features to [] when wire omits them", () => {
    const { features, ...noFeatures } = wire;
    const grid = tacticalGridFromWire(noFeatures as typeof wire);
    expect(grid!.features).toEqual([]);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-ui && npx vitest run src/lib/__tests__/tacticalGridFromWire.features.test.ts`
Expected: FAIL — `grid.features` is undefined / type error.

- [ ] **Step 3: Extend types + parser**

In `src/types/tactical.ts`, add after `FeatureDef` (line 48):

```typescript
/** A positioned tactical-map feature marker (ADR-096 token+feature phase). */
export interface TacticalFeatureMarker {
  readonly feature_type: FeatureType;
  readonly cell: { readonly x: number; readonly y: number };
  readonly label: string;
}
```

And add to `TacticalGridData` (after `tokens`, line 166):

```typescript
  readonly features: readonly TacticalFeatureMarker[];
```

In `src/lib/tacticalGridFromWire.ts`, add to `WirePayload`:

```typescript
  features?: { feature_type: string; cell: { x: number; y: number }; label: string }[];
```

and to the returned object (after `tokens: ...`):

```typescript
    features: (p.features ?? []).map(f => ({
      feature_type: f.feature_type as TacticalGridData["features"][number]["feature_type"],
      cell: f.cell,
      label: f.label,
    })),
```

In `src/components/MapOverlay.tsx`, add to the `cavern_payload` inline type (after `tokens: [...]`, ~line 67):

```typescript
    features?: { feature_type: string; cell: { x: number; y: number }; label: string }[];
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-ui && npx vitest run src/lib/__tests__/tacticalGridFromWire.features.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd sidequest-ui
git add src/types/tactical.ts src/lib/tacticalGridFromWire.ts src/components/MapOverlay.tsx src/lib/__tests__/tacticalGridFromWire.features.test.ts
git commit -m "feat(ui): carry tactical features[] through the wire parser + types (158-18)"
```

---

### Task 8: UI — render feature overlay + legend + exit/POI markers; honest action panel

**Files:**
- Create: `sidequest-ui/src/lib/featureGlyphs.ts` (salvaged glyph + default color maps)
- Modify: `sidequest-ui/src/components/TacticalGridRenderer.tsx`
- Test: `sidequest-ui/src/components/__tests__/TacticalGridRenderer.features.test.tsx`

**Interfaces:**
- Consumes: `TacticalGridData.features`, `grid.derived.exits`, `grid.derived.pois`.
- Produces: `FEATURE_MARKERS: Record<FeatureType,string>`, `FEATURE_COLORS: Record<FeatureType,string>`.

- [ ] **Step 1: Write the failing test**

```tsx
// src/components/__tests__/TacticalGridRenderer.features.test.tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { TacticalGridRenderer } from "@/components/TacticalGridRenderer";
import type { TacticalGridData } from "@/types/tactical";

const grid: TacticalGridData = {
  room_id: "r", room_name: "r", room_type: "cavern",
  mask: "###\n#.#\n###", cavern_image_url: "/x.png", cell_size: 28, cellular: null,
  derived: { floor_count: 1, exits: { north: [1, 0] }, pois: [[1, 1]] },
  tokens: [],
  features: [{ feature_type: "water", cell: { x: 1, y: 1 }, label: "black water" }],
};

describe("TacticalGridRenderer features", () => {
  it("renders a feature marker with its label as title", () => {
    render(<TacticalGridRenderer grid={grid} />);
    const marker = screen.getByTestId("feature-water-1-1");
    expect(marker).toBeInTheDocument();
    expect(marker).toHaveAttribute("title", "black water");
  });

  it("renders a legend entry for present feature types", () => {
    render(<TacticalGridRenderer grid={grid} />);
    expect(screen.getByTestId("legend-water")).toBeInTheDocument();
  });

  it("renders an exit marker", () => {
    render(<TacticalGridRenderer grid={grid} />);
    expect(screen.getByTestId("exit-north")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-ui && npx vitest run src/components/__tests__/TacticalGridRenderer.features.test.tsx`
Expected: FAIL — `Unable to find element by data-testid="feature-water-1-1"`.

- [ ] **Step 3: Salvage glyphs + render overlay**

Create `src/lib/featureGlyphs.ts`:

```typescript
import type { FeatureType } from "@/types/tactical";

// Salvaged from the retired DungeonMapRenderer (158-18).
export const FEATURE_MARKERS: Record<FeatureType, string> = {
  cover: "▣",
  hazard: "⚠",
  difficult_terrain: "≋",
  atmosphere: "◌",
  interactable: "⚙",
  door: "▯",
};

export const FEATURE_COLORS: Record<FeatureType, string> = {
  cover: "#9CA3AF",
  hazard: "#DC2626",
  difficult_terrain: "#D97706",
  atmosphere: "#6B7280",
  interactable: "#2563EB",
  door: "#A78BFA",
};

// water is a fill, not a glyph type in the new path; give it a marker too.
export const WATER_MARKER = "≈"; // ≈
export const WATER_COLOR = "#1D4ED8";
```

In `TacticalGridRenderer.tsx`: import the maps, and inside the `<div className="absolute inset-0">` (after the tokens map, before `</div>`), add the feature, exit, and POI overlays:

```tsx
          {grid.features.map(f => {
            const isWater = f.feature_type === "water";
            const glyph = isWater ? WATER_MARKER : FEATURE_MARKERS[f.feature_type];
            const color = isWater ? WATER_COLOR : FEATURE_COLORS[f.feature_type];
            return (
              <div
                key={`feat-${f.feature_type}-${f.cell.x}-${f.cell.y}`}
                data-testid={`feature-${f.feature_type}-${f.cell.x}-${f.cell.y}`}
                title={f.label}
                className="absolute pointer-events-none grid place-items-center"
                style={{
                  left: f.cell.x * cellSize, top: f.cell.y * cellSize,
                  width: cellSize, height: cellSize,
                  color, fontSize: Math.floor(cellSize * 0.6),
                  textShadow: "0 1px 3px rgba(0,0,0,0.9)",
                }}
              >
                {glyph}
              </div>
            );
          })}
          {Object.entries(grid.derived.exits).map(([bearing, cell]) =>
            cell ? (
              <div
                key={`exit-${bearing}`}
                data-testid={`exit-${bearing}`}
                title={`exit: ${bearing}`}
                className="absolute pointer-events-none border-2 border-dashed"
                style={{
                  left: cell[0] * cellSize, top: cell[1] * cellSize,
                  width: cellSize, height: cellSize,
                  borderColor: "rgba(230,200,76,0.8)", borderRadius: 3,
                }}
              />
            ) : null,
          )}
          {grid.derived.pois.map(([x, y]) => (
            <div
              key={`poi-${x}-${y}`}
              data-testid={`poi-${x}-${y}`}
              className="absolute pointer-events-none rounded-full"
              style={{
                left: x * cellSize + cellSize * 0.35, top: y * cellSize + cellSize * 0.35,
                width: cellSize * 0.3, height: cellSize * 0.3,
                background: "rgba(230,200,76,0.9)",
              }}
            />
          ))}
```

Add the legend after the map `<div className="relative">...</div>` (a sibling, before the action panel). First compute present types near the top of the component:

```tsx
  const presentFeatureTypes = Array.from(new Set(grid.features.map(f => f.feature_type)));
```

Then the legend block:

```tsx
      {presentFeatureTypes.length > 0 && (
        <div data-testid="feature-legend" className="text-xs space-y-1">
          {presentFeatureTypes.map(ft => (
            <div key={ft} data-testid={`legend-${ft}`} className="flex items-center gap-2">
              <span style={{ color: ft === "water" ? WATER_COLOR : FEATURE_COLORS[ft] }}>
                {ft === "water" ? WATER_MARKER : FEATURE_MARKERS[ft]}
              </span>
              <span className="opacity-80">{ft.replace("_", " ")}</span>
            </div>
          ))}
        </div>
      )}
```

Update the import line at top:

```tsx
import { FEATURE_MARKERS, FEATURE_COLORS, WATER_MARKER, WATER_COLOR } from "@/lib/featureGlyphs";
```

**Honest action panel:** change the `CavernActionPanel` usage (lines 108-120) so it shows inspection only — drop the non-functional action buttons for v1 by passing a flag. In `CavernActionPanel.tsx`, gate the `ACTIONS` button block behind a new optional prop `readonly actionsEnabled?: boolean` (default `false`); when false, render only the stat rows. Update the test file `src/components/__tests__/CavernActionPanel.test.tsx` if it asserts buttons render by default.

```tsx
// in TacticalGridRenderer.tsx CavernActionPanel usage — drop the dead onAction stub:
          <CavernActionPanel
            tokenName={selected.name}
            className={selected.className ?? ""}
            hp={selected.hp}
            ac={selected.ac}
            speed={selected.speed ?? 30}
            position={selected.cell}
            actionsEnabled={false}
            onAction={() => {}}
          />
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-ui && npx vitest run src/components/__tests__/TacticalGridRenderer.features.test.tsx`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
cd sidequest-ui
git add src/lib/featureGlyphs.ts src/components/TacticalGridRenderer.tsx src/components/CavernActionPanel.tsx src/components/__tests__/TacticalGridRenderer.features.test.tsx
git commit -m "feat(ui): tactical feature/legend/exit/poi overlay on cavern map; inspection-only panel (158-18)"
```

---

### Task 9: Retire the dead SVG renderer path

Delete the orphaned `DungeonMapRenderer` and its unreachable Automapper branch; salvage already done in Task 8.

**Files:**
- Delete: `sidequest-ui/src/components/DungeonMapRenderer.tsx` and its test(s)
- Modify: `sidequest-ui/src/components/Automapper.tsx` (remove `buildDungeonLayout`, the `roomsWithGrids` branch ~lines 315-336, the `grid?` field on `ExploredRoom` line 29, and the now-unused imports lines 8/11/12)
- Modify: `sidequest-ui/src/types/tactical.ts` (remove `LegacyTacticalGridData`, `PlacedRoomData`, `DungeonLayoutData`, `TacticalThemeConfig`, `TacticalCell`, `TacticalCellType`, `ExitGap`, `CardinalDirection` if unused elsewhere)
- Test: `sidequest-ui/src/components/__tests__/Automapper.routing.test.tsx`

**Interfaces:** none produced; this removes dead surface.

- [ ] **Step 1: Write the failing/guard test**

```tsx
// src/components/__tests__/Automapper.routing.test.tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Automapper } from "@/components/Automapper";

describe("Automapper routing after dead-renderer retirement", () => {
  it("routes a single cavern room to the image renderer", () => {
    const rooms = [{
      id: "r", name: "r", room_type: "normal", size: "medium", is_current: true,
      exits: [],
      cavernGrid: {
        room_id: "r", room_name: "r", room_type: "cavern" as const,
        mask: "###\n#.#\n###", cavern_image_url: "/x.png", cell_size: 28, cellular: null,
        derived: { floor_count: 1, exits: {}, pois: [] }, tokens: [], features: [],
      },
    }];
    render(<Automapper rooms={rooms as any} currentLocation="r" />);
    expect(screen.getByTestId("tactical-grid-renderer")).toBeInTheDocument();
  });
});
```

> Implementer: match the real `Automapper` prop signature (check its export). The point of this test: with the multi-room SVG branch removed, a cavern still routes to `TacticalGridRenderer`, and the schematic/settlement paths still work.

- [ ] **Step 2: Run the full UI suite to see the current state**

Run: `cd sidequest-ui && npx vitest run`
Expected: the new routing test PASSES; existing `DungeonMapRenderer` tests still present (will be deleted next).

- [ ] **Step 3: Delete the dead renderer + branch**

```bash
cd sidequest-ui
git rm src/components/DungeonMapRenderer.tsx
git rm src/components/__tests__/DungeonMapRenderer.test.tsx 2>/dev/null || true
```

In `Automapper.tsx`: remove the import of `DungeonMapRenderer` (line 4), the `LegacyTacticalGridData`/`DungeonLayoutData`/`PlacedRoomData` imports (lines 8/11/12), the `grid?: LegacyTacticalGridData` field (line 29), the `buildDungeonLayout` function (lines 215-289), and the "Multiple rooms with grids → DungeonMapRenderer" branch (lines 316-336). Keep the `cavernGrid` branch (lines 347-351), the settlement branch, and the schematic fallback.

In `types/tactical.ts`: delete `TacticalCellType`, `TacticalCell`, `FeatureType`?(NO — `FeatureType`/`FeatureDef` are now used by `featureGlyphs.ts`/markers; KEEP them), `LegacyTacticalGridData`, `TacticalEntity`, `PlacedRoomData`, `DungeonLayoutData`, `TacticalThemeConfig`, `ExitGap`, `CardinalDirection`. Run the type-check to confirm nothing else references them.

- [ ] **Step 4: Run lint + type-check + full suite**

Run: `cd sidequest-ui && npx tsc --noEmit && npx vitest run`
Expected: PASS — no references to deleted types; all suites green.

- [ ] **Step 5: Commit**

```bash
cd sidequest-ui
git add -A
git commit -m "refactor(ui): retire dead DungeonMapRenderer + legacy SVG-grid types (158-18)"
```

---

### Task 10: End-to-end build verification + content sanity

**Files:**
- Test: full server + ui suites; manual content check (no code change expected in `sidequest-content` for v1 — themes/set-pieces already exist).

- [ ] **Step 1: Server suite + lint**

Run: `cd sidequest-server && uv run ruff check . && uv run pytest -q`
Expected: PASS.

- [ ] **Step 2: UI suite + lint + types**

Run: `cd sidequest-ui && npx vitest run && npm run lint && npx tsc --noEmit`
Expected: PASS.

- [ ] **Step 3: Confirm WATER_THEMES match real theme keys**

Verify the `WATER_THEMES` set in `tactical.py` matches actual theme file basenames under `sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden/themes/` (e.g. `drowned_cavern.yaml`). Adjust the set to the real keys; this is the one content-coupling point.

Run: `ls sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden/themes/`
Expected: confirm `drowned_cavern` (and siblings) — fix `WATER_THEMES` if names differ.

- [ ] **Step 4: Commit any theme-key correction**

```bash
cd sidequest-server
git add sidequest/dungeon/tactical.py
git commit -m "fix(dungeon): align WATER_THEMES to real beneath_sunden theme keys (158-18)" || echo "no change needed"
```

---

## Self-Review

**1. Spec coverage:**
- §3 pipeline → Tasks 2,4,5 (generate→persist→emit). ✓
- §4 generation stage (chokes/water/hazard/anchors/exits) → Task 2. ✓
- §4.2 persistence in mask dict → Task 3,4. ✓
- §4.3 emit + revealed-only concealment gate → Task 5. ✓
- §5 additive protocol (`features`, populated tokens/derived) → Task 1,5. ✓
- §6.1 UI overlay + legend + exit/POI markers → Task 8. ✓
- §6.2 honest action panel (no dead stub) → Task 8. ✓
- §6.3 retire DungeonMapRenderer + salvage FeatureType → Task 8 (salvage), Task 9 (retire). ✓
- §7 OTEL (enriched emit + missing + placed) → Task 5 (missing), Task 6 (counts). NOTE: `tactical_grid.tokens_placed` named in spec is folded into the enriched `tactical_grid.emitted` counts (token_count) — equivalent observability, one fewer event. Acceptable simplification; logged here.
- §8 wiring test (fixture-driven) → Task 5 step 1. ✓
- §9 determinism → Task 2 test. ✓

**2. Placeholder scan:** Implementer NOTEs are integration-adapter guidance (real types to confirm), not placeholders — each names the exact file/symbol to verify and the shape to match. Code steps contain runnable code. No "TODO/handle errors/similar to".

**3. Type consistency:** `RegionTactical`/`TacticalFeatureCell`/`TokenAnchor` used identically across Tasks 2-5. `TacticalFeature` (protocol) vs `TacticalFeatureMarker` (UI) vs `TacticalFeatureCell` (server-internal) are deliberately three layers (wire / ui-view / generation) with identical fields — named distinctly to avoid cross-layer coupling. `features` field name consistent server↔wire↔ui. `FeatureType` kept (not deleted) in Task 9 because `featureGlyphs.ts` consumes it.

**Known follow-ups (out of v1, per spec):** enforced mechanics (WWN math on features); cell-level fog of war / light radius / LOS (user is holding this one); token movement/actions (the gated `actionsEnabled`).
