# Track A: Main-Map Treatments Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give region-mode worlds a genre-true main map (spec §2). A new optional per-world `map.yaml` declares a `treatment` (`raster` | `orrery` | `dag` | `generated`); when `raster`, the server ships a PD scan URL + per-region pixel anchors + provenance in the existing `MAP_UPDATE` frame, and a new `RasterMap` React component draws the scan with an SVG overlay (node pins, party marker, routes, faction layer) and pan/zoom. Absent `map.yaml` → today's d3-dag fallback (by design). Also: bind weather to geography (`Region.weather_zone`, A2), delete dead cartography graph models (weed-whack rider), and verify the already-shipped 158-50 course/clock router wiring after syncing `develop`.

**Architecture:** The cartography graph stays coordinate-free and semantic (`CartographyConfig`); presentation is a separate optional layer loaded from `worlds/<slug>/map.yaml` into a new `World.map_treatment`. `_build_cartography_map_message` reads `map_treatment` and populates a new typed `treatment` block on `CartographyMapPayload`; the emit site fires a `map.treatment_emitted` OTEL span to `turn_telemetry`. The UI blind-casts the payload onto `mapData`, so `MapWidget` gains one `treatment?.kind === "raster"` branch → `RasterMap`. Content invariants (anchor coverage, provenance) live in the CI-gated pack validator, never in unit tests.

**Tech Stack:** Python 3.14 / FastAPI / pydantic v2 (server, uv-managed) · React 18 / TypeScript / Vite / vitest (ui) · YAML genre packs (content) · PostgreSQL telemetry sink (`PgTelemetrySink`) · OTEL via `publish_event`.

---

## Global Constraints (one line each, exact values)

- **SYNC FIRST — local `develop` is 75 commits behind `origin/develop`.** Do Task 1 before anything; branch off the freshly-pulled `origin/develop`, never the stale local tree.
- Python tests: `cd sidequest-server && uv run pytest <path> -v`; single-process for OTEL/span tests: add `-n0`.
- Python lint: `cd sidequest-server && uv run ruff check <path>`; format ONLY branch-touched files: `uv run ruff format <file>` (bare `ruff format .` reformats ~167 files — never do it).
- UI tests: `cd sidequest-ui && npx vitest run <path>`; UI lint: `cd sidequest-ui && npx eslint <path>` (or `just client-lint`).
- TDD strictly: write the failing test first, run it and SEE it fail, write minimal code, run it and SEE it pass, commit. Frequent small commits.
- Branch/commit in the SUBREPO. Server/UI branches target `develop`; content branches target `develop`. Cut the branch in its OWN `Bash` call BEFORE any `git commit` (a PreToolUse hook rejects `commit` while on `develop`/`main`, even in a compound command).
- Every test suite includes ≥1 WIRING test proving production reachability (CLAUDE.md critical rule). For emitters: an OTEL/DB-readback test, NOT a source-text grep (except the one sanctioned raw-import test the UI already uses).
- No content invariants in unit tests — anchor coverage + provenance go in the pack validator (`sidequest/cli/validate/pack.py`, the CI-gated path via `just content-validate-all`). Unit tests use synthetic fixtures.
- No silent fallbacks: a `raster` treatment whose image fails to load → explicit RasterMap error state, NEVER a silent dag fallback. Absent `map.yaml` → dag fallback (that one IS by design, spec §2). A malformed `map.yaml` → fail loud at load (pydantic `extra="forbid"` + `Literal` enum).
- New OTEL span `map.treatment_emitted` MUST reach `turn_telemetry` via `publish_event` (aliased `_watcher_publish`) — NOT `Span.open` alone. It reaches the DB automatically because the session binds a `PgTelemetrySink` at `/ws` connect. Do NOT add it to `_EPHEMERAL_EVENT_TYPES`.
- Known pre-existing failures (do not chase): ~13 server test failures vs current content develop (WWN migration); OTEL span-count tests deadlock under xdist (run affected files `-n0`); `test_message_type_complete_count` is stale.
- All file:line references below are **as-of `origin/develop`**; verify with `grep -n` at execution time (local is stale; numbers shift by a few lines).

## 158-50 status — ALREADY SHIPPED (verify, do not re-implement)

Story 158-50 (course/clock in-play wiring) is **merged on `origin/develop`**: `_build_state_summary` in `sidequest/server/intent_router_pass.py` gained an `orbital_content` param (~line 366) and assembles the `<courses>` block (~lines 703–745, `summary["courses"] = format_courses_block(...)`), threaded at the call site (~line 971). The RED wiring test `tests/agents/subsystems/test_course_router_summary_wiring.py` is present. **Task 1 folds 158-50 by pulling + running that test green — no new implementation.** If (and only if) the test is absent or red after sync, escalate to the team lead rather than re-writing it (avoids a duplicate/conflicting implementation).

## Track B cross-touch (keep changes surgically scoped)

- `sidequest/server/websocket_handlers/map_emit.py` — Track A edits `_maybe_emit_cartography_map` (region-mode) only. Track B edits `_maybe_emit_dungeon_map` / the `SITE_MAP` cutover (different functions in the same file). Do not touch the dungeon/site functions.
- `sidequest-ui/.../MapWidget.tsx` — Track A adds ONE `treatment?.kind === "raster"` early-return branch. Track B adds site/Automapper routing branches. Keep the raster branch self-contained; do not refactor the existing cascade.

---

### Task 1: Sync `develop`, cut branches, verify 158-50 baseline

**Files:** none created/modified (git sync + verification only).

**Interfaces:**
- Consumes: `origin/develop` (server, ui, content subrepos).
- Produces: three local feature branches off up-to-date `develop`; a green 158-50 wiring test proving the fold is already complete.

Steps:
- [ ] Sync the server subrepo: `cd sidequest-server && git checkout develop && git pull --rebase origin develop`
- [ ] Confirm 158-50 shipped (expect a non-zero count and the file present):
  `cd sidequest-server && grep -c 'summary\["courses"\]' sidequest/server/intent_router_pass.py && ls tests/agents/subsystems/test_course_router_summary_wiring.py`
- [ ] Run the 158-50 wiring test green: `cd sidequest-server && uv run pytest tests/agents/subsystems/test_course_router_summary_wiring.py -v -n0` — EXPECT: pass. If it fails or the file is absent, STOP and escalate to the team lead (do not re-implement 158-50).
- [ ] Sync UI + content: `cd sidequest-ui && git checkout develop && git pull --rebase origin develop` and `cd sidequest-content && git checkout develop && git pull --rebase origin develop`
- [ ] Cut the server branch (own Bash call, before any commit): `cd sidequest-server && git checkout -b feat/track-a-main-map-treatments`
- [ ] Cut the UI branch: `cd sidequest-ui && git checkout -b feat/track-a-raster-map`
- [ ] Cut the content branch: `cd sidequest-content && git checkout -b feat/track-a-map-yaml`
- [ ] Establish a green server baseline for the files this plan touches: `cd sidequest-server && uv run pytest tests/genre -q -n0` — EXPECT: pass (ignore the ~13 known WWN-content failures if they surface elsewhere).

---

### Task 2: Weed-whack dead cartography graph models (server)

**Files:**
- Modify: `sidequest-server/sidequest/genre/models/world.py` — delete `Terrain` (~L102–121), `WorldGraphNode` (~L124–138), `GraphEdge` (~L140–156), `SubGraph` (~L159–165), `WorldGraph` (~L168–174); delete the `world_graph` + `sub_graphs` fields on `CartographyConfig` (~L299–300).
- Modify: `sidequest-server/sidequest/genre/models/__init__.py` — delete imports `GraphEdge` (~L205), `SubGraph` (~L211), `Terrain` (~L212), `WorldGraph` (~L214), `WorldGraphNode` (~L215) and their `__all__` entries (~L422, L428, L429, L431, L432). Keep `TerrainScar` (a different symbol from `legends.py`).

**Interfaces:**
- Consumes: nothing (these models have no non-test consumers — verified: only definitions in `world.py` + re-exports in `__init__.py`; no content YAML uses `world_graph:`/`sub_graphs:`).
- Produces: a `CartographyConfig` with no dead graph fields. `RoomDef`, `Region`, `Route`, `CartographyConfig`, `NavigationMode`, `WorldConfig` remain.

Steps:
- [ ] Write the failing test. Create `sidequest-server/tests/genre/test_dead_cartography_models_removed.py`:
```python
"""Weed-whack rider (spec §2): the dead world-graph models are deleted.

Reflection-based tripwire (CLAUDE.md sanctioned exception) — interrogates
runtime types/fields, not source text.
"""

import sidequest.genre.models as models
from sidequest.genre.models.world import CartographyConfig


def test_dead_graph_models_are_gone() -> None:
    for name in ("Terrain", "WorldGraphNode", "GraphEdge", "SubGraph", "WorldGraph"):
        assert not hasattr(models, name), f"{name} should be deleted (dead cartography model)"


def test_cartography_config_has_no_graph_fields() -> None:
    fields = set(CartographyConfig.model_fields)
    assert "world_graph" not in fields
    assert "sub_graphs" not in fields
    # The graph of record survives:
    assert "regions" in fields and "routes" in fields
```
- [ ] Run it, SEE it fail: `cd sidequest-server && uv run pytest tests/genre/test_dead_cartography_models_removed.py -v -n0` — EXPECT failure (models still present).
- [ ] Delete the five model classes in `world.py`. After deleting, the `Annotated`/`Literal` imports and `StrEnum` may still be used by other models — leave imports that remain in use; remove `StrEnum` only if `NavigationMode` no longer needs it (it does — keep it).
- [ ] Delete `CartographyConfig.world_graph` and `CartographyConfig.sub_graphs` field lines.
- [ ] Delete the five imports + five `__all__` entries in `models/__init__.py` (leave `TerrainScar`, `FactionGrudge`, `Legend`).
- [ ] Run to pass: `cd sidequest-server && uv run pytest tests/genre/test_dead_cartography_models_removed.py -v -n0` — EXPECT pass.
- [ ] Regression-guard the loader still imports cleanly: `cd sidequest-server && uv run python -c "import sidequest.genre.loader; import sidequest.genre.models"` — EXPECT no error.
- [ ] Lint + format touched files: `cd sidequest-server && uv run ruff check sidequest/genre/models/world.py sidequest/genre/models/__init__.py tests/genre/test_dead_cartography_models_removed.py && uv run ruff format sidequest/genre/models/world.py sidequest/genre/models/__init__.py tests/genre/test_dead_cartography_models_removed.py`
- [ ] Commit:
```
cd sidequest-server && git add sidequest/genre/models/world.py sidequest/genre/models/__init__.py tests/genre/test_dead_cartography_models_removed.py && git commit -m "refactor(cartography): weed-whack dead WorldGraph/SubGraph/GraphEdge/Terrain models (spec §2)

CartographyConfig is the graph of record; the coordinate-free node/edge
models were never consumed. Reflection tripwire test guards regression.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: `MapTreatmentConfig` + `MapProvenance` models (server)

**Files:**
- Modify: `sidequest-server/sidequest/genre/models/world.py` — add `MapProvenance` and `MapTreatmentConfig` near `CartographyConfig`.
- Modify: `sidequest-server/sidequest/genre/models/__init__.py` — export both from the `world` import block + `__all__`.

**Interfaces:**
- Produces:
```python
class MapProvenance(BaseModel):
    model_config = {"extra": "forbid"}
    source: str
    date: str
    archive: str
    pd_basis: str

class MapTreatmentConfig(BaseModel):
    model_config = {"extra": "forbid"}
    treatment: Literal["raster", "orrery", "dag", "generated"]
    image: str | None = None                 # filename under worlds/<slug>/assets/maps/
    provenance: MapProvenance | None = None
    node_anchors: dict[str, list[float]] = Field(default_factory=dict)  # region_id -> [x, y] px
    style_hints: dict[str, Any] = Field(default_factory=dict)
```
- Note the layering (documented in the model docstring): the MODEL enforces STRUCTURE only (enum, types, `extra="forbid"`) and fails loud on malformed YAML. CONTENT-completeness — raster requires `image` + `provenance`, every region has an anchor — is enforced by the pack validator (Task 8), never the model (the model can't see cartography). `image`/`provenance` stay Optional so a non-raster treatment need not supply them.

Steps:
- [ ] Write the failing test. Create `sidequest-server/tests/genre/test_map_treatment_model.py`:
```python
import pytest
from pydantic import ValidationError

from sidequest.genre.models.world import MapProvenance, MapTreatmentConfig


def test_raster_treatment_parses_full_shape() -> None:
    mt = MapTreatmentConfig.model_validate(
        {
            "treatment": "raster",
            "image": "os_one_inch_1900.jpg",
            "provenance": {
                "source": "Ordnance Survey One-Inch",
                "date": "1900",
                "archive": "NLS Map Images",
                "pd_basis": "Crown copyright expired",
            },
            "node_anchors": {"the_glenross_arms": [512, 340]},
            "style_hints": {"faction_layer": "default"},
        }
    )
    assert mt.treatment == "raster"
    assert mt.image == "os_one_inch_1900.jpg"
    assert mt.node_anchors["the_glenross_arms"] == [512, 340]
    assert isinstance(mt.provenance, MapProvenance)


def test_dag_treatment_needs_no_image_or_provenance() -> None:
    mt = MapTreatmentConfig.model_validate({"treatment": "dag"})
    assert mt.treatment == "dag"
    assert mt.image is None and mt.provenance is None


def test_unknown_treatment_kind_fails_loud() -> None:
    with pytest.raises(ValidationError):
        MapTreatmentConfig.model_validate({"treatment": "hologram"})


def test_extra_key_fails_loud() -> None:
    with pytest.raises(ValidationError):
        MapTreatmentConfig.model_validate({"treatment": "dag", "bogus": 1})
```
- [ ] Run it, SEE it fail: `cd sidequest-server && uv run pytest tests/genre/test_map_treatment_model.py -v -n0` — EXPECT ImportError (models don't exist).
- [ ] Add the two models to `world.py` (place directly after `CartographyConfig`). `Any`, `Literal`, `Field`, `BaseModel` are already imported at the top of `world.py`:
```python
class MapProvenance(BaseModel):
    """Public-domain sourcing metadata for a raster main-map scan (spec §2).

    Required for a ``raster`` treatment — enforced by the pack validator, not
    here, so a non-raster treatment can omit it. The composer's PD-provenance
    pattern applied to maps: every scan names its source, date, archive, and
    the basis on which it is public domain.
    """

    model_config = {"extra": "forbid"}

    source: str
    date: str
    archive: str
    pd_basis: str


class MapTreatmentConfig(BaseModel):
    """Optional per-world main-map presentation layer, loaded from
    ``worlds/<slug>/map.yaml`` (spec §2).

    The cartography graph stays coordinate-free and semantic; this declares
    HOW it is drawn. Absent ``map.yaml`` → no treatment → d3-dag fallback (by
    design). This model enforces STRUCTURE only (enum kind, types,
    ``extra="forbid"`` — a malformed map.yaml fails loud at load). Content
    completeness (raster requires ``image`` + ``provenance``; every region
    has a ``node_anchor``) is enforced by the pack validator, which can see
    the sibling cartography.yaml.
    """

    model_config = {"extra": "forbid"}

    treatment: Literal["raster", "orrery", "dag", "generated"]
    image: str | None = None
    provenance: MapProvenance | None = None
    node_anchors: dict[str, list[float]] = Field(default_factory=dict)
    style_hints: dict[str, Any] = Field(default_factory=dict)
```
- [ ] Export both in `models/__init__.py`: add `MapProvenance`, `MapTreatmentConfig` to the `from sidequest.genre.models.world import (...)` block and to `__all__`.
- [ ] Run to pass: `cd sidequest-server && uv run pytest tests/genre/test_map_treatment_model.py -v -n0` — EXPECT pass.
- [ ] Lint + format: `cd sidequest-server && uv run ruff check sidequest/genre/models/world.py sidequest/genre/models/__init__.py tests/genre/test_map_treatment_model.py && uv run ruff format sidequest/genre/models/world.py sidequest/genre/models/__init__.py tests/genre/test_map_treatment_model.py`
- [ ] Commit:
```
cd sidequest-server && git add sidequest/genre/models/world.py sidequest/genre/models/__init__.py tests/genre/test_map_treatment_model.py && git commit -m "feat(cartography): MapTreatmentConfig + MapProvenance models for map.yaml (spec §2 A1)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: Load `map.yaml` into `World.map_treatment` (server)

**Files:**
- Modify: `sidequest-server/sidequest/genre/loader.py` — add `_load_map_treatment(world_path)` next to `_load_cartography` (~L1053); call it in the world leaf loader (near the `cartography = _load_cartography(...)` line, ~L1539); add `map_treatment=map_treatment` to the `World(...)` construction (~L2075).
- Modify: `sidequest-server/sidequest/genre/models/pack.py` — add the `map_treatment` field on `World` (near `cartography: CartographyConfig`, ~L198).

**Interfaces:**
- Consumes: existing `_load_yaml_raw_optional(path) -> Any | None` (loader helper; returns None for an absent file) and `MapTreatmentConfig` (Task 3).
- Produces:
```python
def _load_map_treatment(world_path: Path) -> MapTreatmentConfig | None: ...
# World gains:
map_treatment: MapTreatmentConfig | None = None
```
- Absent `map.yaml` → returns `None` (by design, dag fallback). Malformed → `MapTreatmentConfig.model_validate` raises (fail loud, surfaced as a GenreLoadError-adjacent load failure).

Steps:
- [ ] Confirm the helper name for optional-raw YAML load: `cd sidequest-server && grep -n "_load_yaml_raw_optional\|def _load_yaml_raw" sidequest/genre/loader.py | head` — use whichever optional loader exists; the plan assumes `_load_yaml_raw_optional`.
- [ ] Write the failing test. Create `sidequest-server/tests/genre/test_map_treatment_loader.py`:
```python
from pathlib import Path

import yaml

from sidequest.genre.loader import _load_map_treatment


def _write(p: Path, data: dict) -> None:
    p.write_text(yaml.safe_dump(data), encoding="utf-8")


def test_absent_map_yaml_returns_none(tmp_path: Path) -> None:
    assert _load_map_treatment(tmp_path) is None


def test_present_raster_map_yaml_loads(tmp_path: Path) -> None:
    _write(
        tmp_path / "map.yaml",
        {
            "treatment": "raster",
            "image": "sheet.jpg",
            "provenance": {
                "source": "OS",
                "date": "1900",
                "archive": "NLS",
                "pd_basis": "Crown copyright expired",
            },
            "node_anchors": {"r1": [10, 20]},
        },
    )
    mt = _load_map_treatment(tmp_path)
    assert mt is not None
    assert mt.treatment == "raster"
    assert mt.node_anchors["r1"] == [10, 20]
```
- [ ] Run it, SEE it fail: `cd sidequest-server && uv run pytest tests/genre/test_map_treatment_loader.py -v -n0` — EXPECT ImportError (`_load_map_treatment` missing).
- [ ] Add `_load_map_treatment` after `_load_cartography` in `loader.py` (ensure `MapTreatmentConfig` is imported from `sidequest.genre.models.world` in the loader's import block — extend the existing `from sidequest.genre.models.world import CartographyConfig, NavigationMode, WorldConfig` line):
```python
def _load_map_treatment(world_path: Path) -> MapTreatmentConfig | None:
    """Load the optional per-world ``map.yaml`` presentation layer (spec §2).

    Absent → None (d3-dag fallback, by design). Present but malformed →
    MapTreatmentConfig.model_validate raises (No Silent Fallbacks).
    """
    raw = _load_yaml_raw_optional(world_path / "map.yaml")
    if raw is None:
        return None
    return MapTreatmentConfig.model_validate(raw)
```
- [ ] Add the `World` field in `pack.py` (right after `cartography: CartographyConfig`): `map_treatment: MapTreatmentConfig | None = None` and import `MapTreatmentConfig` in `pack.py`'s model imports.
- [ ] In the world leaf loader, after `cartography = _load_cartography(...)`, add: `map_treatment = _load_map_treatment(world_path)`; then add `map_treatment=map_treatment,` to the `return World(...)` kwargs.
- [ ] Run to pass: `cd sidequest-server && uv run pytest tests/genre/test_map_treatment_loader.py -v -n0` — EXPECT pass.
- [ ] Wiring/regression: load a real pack end-to-end so the loader change is exercised in production code: `cd sidequest-server && uv run python -c "from sidequest.genre.loader import load_genre_pack; import pathlib; p=load_genre_pack(pathlib.Path('../sidequest-content/genre_packs/tea_and_murder')); w=p.worlds['glenross']; print('map_treatment', w.map_treatment)"` — EXPECT `map_treatment None` (no map.yaml yet; proves the field loads and defaults cleanly). Adjust the `load_genre_pack` signature to the real one if it differs (grep `def load_genre_pack`).
- [ ] Lint + format touched files, then commit:
```
cd sidequest-server && uv run ruff check sidequest/genre/loader.py sidequest/genre/models/pack.py tests/genre/test_map_treatment_loader.py && uv run ruff format sidequest/genre/loader.py sidequest/genre/models/pack.py tests/genre/test_map_treatment_loader.py && git add sidequest/genre/loader.py sidequest/genre/models/pack.py tests/genre/test_map_treatment_loader.py && git commit -m "feat(cartography): load worlds/<slug>/map.yaml into World.map_treatment (spec §2 A1)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 5: Protocol — `CartographyTreatmentWire` + `treatment` field on `CartographyMapPayload` (server)

**Files:**
- Modify: `sidequest-server/sidequest/protocol/messages.py` — add `CartographyTreatmentWire` above `CartographyMapPayload` (~L1724); add a `treatment` field on `CartographyMapPayload` (~L1745).

**Interfaces:**
- Produces:
```python
class CartographyTreatmentWire(ProtocolBase):
    kind: str                                  # raster | orrery | dag | generated
    image_url: str | None = None               # resolved CDN/local URL
    node_anchors: dict[str, list[float]] = Field(default_factory=dict)
    style_hints: dict[str, Any] = Field(default_factory=dict)

# CartographyMapPayload gains:
treatment: CartographyTreatmentWire | None = None
```
- `ProtocolBase` has `extra="forbid"`, so this is a declared, typed additive field. App.tsx blind-casts the whole payload onto `MapState`, so `payload.treatment` reaches `mapData.treatment` in the UI with no handler change.

Steps:
- [ ] Write the failing test. Create `sidequest-server/tests/protocol/test_cartography_treatment_wire.py`:
```python
from sidequest.protocol.messages import (
    CartographyMapMessage,
    CartographyMapPayload,
    CartographyTreatmentWire,
)


def test_payload_serializes_with_treatment() -> None:
    msg = CartographyMapMessage(
        payload=CartographyMapPayload(
            current_location="the_glenross_arms",
            treatment=CartographyTreatmentWire(
                kind="raster",
                image_url="https://cdn.example/sheet.jpg",
                node_anchors={"the_glenross_arms": [512, 340]},
                style_hints={"faction_layer": "default"},
            ),
        )
    )
    dumped = msg.model_dump(mode="json")
    assert dumped["type"] == "MAP_UPDATE"
    assert dumped["payload"]["treatment"]["kind"] == "raster"
    assert dumped["payload"]["treatment"]["node_anchors"]["the_glenross_arms"] == [512, 340]


def test_treatment_defaults_none() -> None:
    p = CartographyMapPayload(current_location="x")
    assert p.treatment is None
```
- [ ] Run it, SEE it fail: `cd sidequest-server && uv run pytest tests/protocol/test_cartography_treatment_wire.py -v -n0` — EXPECT ImportError.
- [ ] Add `CartographyTreatmentWire` immediately above `CartographyMapPayload` (`Any` + `Field` already imported in messages.py):
```python
class CartographyTreatmentWire(ProtocolBase):
    """Optional main-map presentation block on the MAP_UPDATE payload (spec §4).

    Absent → the UI falls back to the d3-dag CartographyMap. ``kind`` is one of
    raster | orrery | dag | generated. For ``raster``, ``image_url`` is the
    already-resolved CDN/local URL and ``node_anchors`` maps region_id ->
    [x, y] image pixels.
    """

    kind: str
    image_url: str | None = None
    node_anchors: dict[str, list[float]] = Field(default_factory=dict)
    style_hints: dict[str, Any] = Field(default_factory=dict)
```
- [ ] Add `treatment: CartographyTreatmentWire | None = None` to `CartographyMapPayload` (after `cartography: dict[str, Any] | None = None`).
- [ ] Run to pass: `cd sidequest-server && uv run pytest tests/protocol/test_cartography_treatment_wire.py -v -n0` — EXPECT pass.
- [ ] Lint + format + commit:
```
cd sidequest-server && uv run ruff check sidequest/protocol/messages.py tests/protocol/test_cartography_treatment_wire.py && uv run ruff format sidequest/protocol/messages.py tests/protocol/test_cartography_treatment_wire.py && git add sidequest/protocol/messages.py tests/protocol/test_cartography_treatment_wire.py && git commit -m "feat(protocol): optional treatment block on CartographyMapPayload (spec §4 A1)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 6: Populate `payload.treatment` from `World.map_treatment` (server)

**Files:**
- Modify: `sidequest-server/sidequest/server/session_helpers.py` — `_build_cartography_map_message` (~L1548): add a `genre_slug` param, build a `CartographyTreatmentWire` from `world.map_treatment`, set it on the payload.
- Modify: `sidequest-server/sidequest/server/websocket_handlers/map_emit.py` — the `_build_cartography_map_message(...)` call inside `_maybe_emit_cartography_map` (~L1194 region): pass `genre_slug=getattr(sd, "genre_slug", "")`.

**Interfaces:**
- Consumes: `World.map_treatment: MapTreatmentConfig | None` (Task 4); `resolve_asset_url(relative_path, *, scope="pack") -> str` from `sidequest.foundation.asset_urls` (image resolution — mirrors `reference_projection.py` POI usage); `CartographyTreatmentWire` (Task 5).
- Produces: `_build_cartography_map_message(pack, world_slug, current_location, player_id="", discovered_regions=None, genre_slug="") -> CartographyMapMessage | None` with `payload.treatment` set when the world declares a `map_treatment`.
- Image path convention (matches `resolve_player_portrait_url`): `genre_packs/<genre>/worlds/<world>/assets/maps/<image>` → `resolve_asset_url(...)`.

Steps:
- [ ] Write the failing test. Create `sidequest-server/tests/server/test_cartography_treatment_build.py`:
```python
from types import SimpleNamespace

from sidequest.genre.models.world import MapProvenance, MapTreatmentConfig
from sidequest.server.session_helpers import _build_cartography_map_message


def _pack_with_treatment(mt: MapTreatmentConfig | None):
    region = SimpleNamespace(name="The Glenross Arms", description="A pub", summary="", adjacent=[])
    cart = SimpleNamespace(
        navigation_mode="region",
        starting_region="the_glenross_arms",
        regions={"the_glenross_arms": region},
        routes=[],
        discovery_mode="public",
    )
    world = SimpleNamespace(cartography=cart, is_cluster=False, map_treatment=mt)
    return SimpleNamespace(worlds={"glenross": world})


def test_no_treatment_leaves_payload_treatment_none() -> None:
    pack = _pack_with_treatment(None)
    msg = _build_cartography_map_message(pack, "glenross", "the_glenross_arms", genre_slug="tea_and_murder")
    assert msg is not None and msg.payload.treatment is None


def test_raster_treatment_populates_payload(monkeypatch) -> None:
    import sidequest.server.session_helpers as sh

    monkeypatch.setattr(sh, "resolve_asset_url", lambda p, **k: f"https://cdn/{p}")
    mt = MapTreatmentConfig(
        treatment="raster",
        image="sheet.jpg",
        provenance=MapProvenance(source="OS", date="1900", archive="NLS", pd_basis="expired"),
        node_anchors={"the_glenross_arms": [512, 340]},
        style_hints={"faction_layer": "default"},
    )
    pack = _pack_with_treatment(mt)
    msg = _build_cartography_map_message(pack, "glenross", "the_glenross_arms", genre_slug="tea_and_murder")
    assert msg is not None
    t = msg.payload.treatment
    assert t is not None and t.kind == "raster"
    assert t.image_url == "https://cdn/genre_packs/tea_and_murder/worlds/glenross/assets/maps/sheet.jpg"
    assert t.node_anchors["the_glenross_arms"] == [512, 340]
    assert t.style_hints == {"faction_layer": "default"}
```
- [ ] Run it, SEE it fail: `cd sidequest-server && uv run pytest tests/server/test_cartography_treatment_build.py -v -n0` — EXPECT fail (`genre_slug` param + treatment build missing).
- [ ] In `session_helpers.py`: add the import near the top (`from sidequest.foundation.asset_urls import resolve_asset_url` — grep first; it may already be imported) and `from sidequest.protocol.messages import CartographyTreatmentWire` (extend the existing messages import).
- [ ] Add `genre_slug: str = ""` to the `_build_cartography_map_message` signature (after `discovered_regions`).
- [ ] Just before the `return CartographyMapMessage(...)` block, build the treatment:
```python
    treatment_wire: CartographyTreatmentWire | None = None
    mt = getattr(world, "map_treatment", None)
    if mt is not None:
        image_url = None
        if mt.image:
            image_url = resolve_asset_url(
                f"genre_packs/{genre_slug}/worlds/{world_slug}/assets/maps/{mt.image}"
            )
        treatment_wire = CartographyTreatmentWire(
            kind=mt.treatment,
            image_url=image_url,
            node_anchors=mt.node_anchors,
            style_hints=mt.style_hints,
        )
```
- [ ] Add `treatment=treatment_wire,` to the `CartographyMapPayload(...)` construction.
- [ ] In `map_emit.py`, add `genre_slug=getattr(sd, "genre_slug", ""),` to the `_build_cartography_map_message(...)` call inside `_maybe_emit_cartography_map`.
- [ ] Run to pass: `cd sidequest-server && uv run pytest tests/server/test_cartography_treatment_build.py -v -n0` — EXPECT pass.
- [ ] Lint + format + commit:
```
cd sidequest-server && uv run ruff check sidequest/server/session_helpers.py sidequest/server/websocket_handlers/map_emit.py tests/server/test_cartography_treatment_build.py && uv run ruff format sidequest/server/session_helpers.py sidequest/server/websocket_handlers/map_emit.py tests/server/test_cartography_treatment_build.py && git add sidequest/server/session_helpers.py sidequest/server/websocket_handlers/map_emit.py tests/server/test_cartography_treatment_build.py && git commit -m "feat(cartography): ship map.yaml treatment in the MAP_UPDATE payload (spec §4 A1)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 7: Emit `map.treatment_emitted` OTEL span → `turn_telemetry` (server)

**Files:**
- Modify: `sidequest-server/sidequest/server/websocket_handlers/map_emit.py` — in `_maybe_emit_cartography_map`, after the existing `cartography.map_emitted` publish and before `emit_fn(msg, "MAP_UPDATE")`, publish `map.treatment_emitted` when `msg.payload.treatment is not None`.

**Interfaces:**
- Consumes: module-level `_watcher_publish` (= `publish_event` alias, already imported at map_emit.py:23). Reaches `turn_telemetry` via `_persist_turn_telemetry` → the connect-bound `PgTelemetrySink`; no `tx` needed (out-of-frame).
- Produces: an OTEL event `map.treatment_emitted` with `component="location"` and fields `{world, treatment_kind, region_count, anchor_count, has_image}`.

Steps:
- [ ] Write the failing tests (both flavors — capture + DB-readback wiring). Create `sidequest-server/tests/server/test_map_treatment_span.py`:
```python
from types import SimpleNamespace

import sidequest.server.websocket_handlers.map_emit as map_emit
from sidequest.genre.models.world import MapProvenance, MapTreatmentConfig


def _sd_and_snapshot(mt):
    region = SimpleNamespace(name="The Glenross Arms", description="pub", summary="", adjacent=[])
    cart = SimpleNamespace(
        navigation_mode="region",
        starting_region="the_glenross_arms",
        regions={"the_glenross_arms": region},
        routes=[],
        discovery_mode="public",
    )
    world = SimpleNamespace(cartography=cart, is_cluster=False, map_treatment=mt)
    pack = SimpleNamespace(worlds={"glenross": world})
    sd = SimpleNamespace(
        genre_pack=pack, world_slug="glenross", genre_slug="tea_and_murder", player_id=""
    )
    snapshot = SimpleNamespace(
        current_region="the_glenross_arms",
        discovered_regions=["the_glenross_arms"],
        party_location=lambda perspective=None: "the_glenross_arms",
    )
    return sd, snapshot


def test_treatment_span_fires_when_treatment_present(monkeypatch) -> None:
    captured: list[dict] = []
    monkeypatch.setattr(
        map_emit,
        "_watcher_publish",
        lambda et, fields, **k: captured.append({"event_type": et, "fields": fields, **k}),
    )
    monkeypatch.setattr(
        "sidequest.server.session_helpers.resolve_asset_url", lambda p, **k: f"https://cdn/{p}"
    )
    mt = MapTreatmentConfig(
        treatment="raster",
        image="sheet.jpg",
        provenance=MapProvenance(source="OS", date="1900", archive="NLS", pd_basis="x"),
        node_anchors={"the_glenross_arms": [1, 2]},
    )
    sd, snapshot = _sd_and_snapshot(mt)
    map_emit._maybe_emit_cartography_map(
        object(), sd=sd, snapshot=snapshot, emit_fn=lambda msg, t: None
    )
    hits = [e for e in captured if e["event_type"] == "map.treatment_emitted"]
    assert len(hits) == 1
    assert hits[0]["fields"]["treatment_kind"] == "raster"
    assert hits[0]["fields"]["anchor_count"] == 1
    assert hits[0]["component"] == "location"


def test_no_treatment_span_when_absent(monkeypatch) -> None:
    captured: list[dict] = []
    monkeypatch.setattr(
        map_emit,
        "_watcher_publish",
        lambda et, fields, **k: captured.append({"event_type": et}),
    )
    sd, snapshot = _sd_and_snapshot(None)
    map_emit._maybe_emit_cartography_map(
        object(), sd=sd, snapshot=snapshot, emit_fn=lambda msg, t: None
    )
    assert not [e for e in captured if e["event_type"] == "map.treatment_emitted"]
```
- [ ] Add a DB-readback wiring test to the same file, modeled on `tests/server/test_save_write_lock.py` (bind a real `PgTelemetrySink`, drive the emit out-of-frame, `SELECT ... FROM turn_telemetry WHERE event_type = 'map.treatment_emitted'`). Use the `store_bound_to_hub` fixture from `tests/server/conftest.py` if present; else replicate the `repo_and_sink` + `bind_event_store(sink)` pattern. Assert a row exists. (This is the mandatory production-reachability wiring test.)
- [ ] Run them, SEE fail: `cd sidequest-server && uv run pytest tests/server/test_map_treatment_span.py -v -n0` — EXPECT fail (span not emitted).
- [ ] In `_maybe_emit_cartography_map`, right after the `cartography.map_emitted` publish block and before `emit_fn(msg, "MAP_UPDATE")`:
```python
    if msg.payload.treatment is not None:
        _watcher_publish(
            "map.treatment_emitted",
            {
                "world": getattr(sd, "world_slug", ""),
                "treatment_kind": msg.payload.treatment.kind,
                "region_count": len(msg.payload.cartography.get("regions", {}))
                if msg.payload.cartography
                else 0,
                "anchor_count": len(msg.payload.treatment.node_anchors),
                "has_image": bool(msg.payload.treatment.image_url),
            },
            component="location",
        )
```
- [ ] Run to pass: `cd sidequest-server && uv run pytest tests/server/test_map_treatment_span.py -v -n0` — EXPECT pass.
- [ ] Lint + format + commit:
```
cd sidequest-server && uv run ruff check sidequest/server/websocket_handlers/map_emit.py tests/server/test_map_treatment_span.py && uv run ruff format sidequest/server/websocket_handlers/map_emit.py tests/server/test_map_treatment_span.py && git add sidequest/server/websocket_handlers/map_emit.py tests/server/test_map_treatment_span.py && git commit -m "feat(telemetry): map.treatment_emitted span to turn_telemetry (spec §5 A1)

GM panel proves the treatment seam engaged, not silently skipped.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 8: Pack validator — anchor coverage + provenance for `raster` (server)

**Files:**
- Modify: `sidequest-server/sidequest/cli/validate/pack.py` — add `_validate_map_treatment(world_dir, label)` and call it from `_validate_world` (append its result to `content_errors`, alongside the other `_validate_*` content checks ~L1156–1234).
- Modify: `sidequest-server/tests/cli/validate/test_pack_validator.py` — add tests using the existing synthetic-pack fixtures.

**Interfaces:**
- Consumes: `_read_yaml(path, label) -> tuple[Any, str | None]` (pack.py helper); the world's `cartography.yaml` (`regions:` mapping) and `map.yaml`.
- Produces: `_validate_map_treatment(world_dir: Path, label: str) -> list[str]` returning one error string per violation. Rules: absent `map.yaml` → `[]` (dag fallback, OK). Present with `treatment: raster` → require `image` (non-empty), require a `provenance` block with all four of `source`/`date`/`archive`/`pd_basis`, and require every `cartography.yaml` region id to appear in `node_anchors`. Non-raster treatments → structural check only (must have a valid `treatment` kind).

Steps:
- [ ] Write the failing tests. Add to `sidequest-server/tests/cli/validate/test_pack_validator.py` (reuse `_minimal_pack`/`_minimal_world`; `schema_path_real` already defined in the file):
```python
    def test_raster_map_missing_anchor_is_error(self, tmp_path: Path) -> None:
        pack_dir = tmp_path / "p"
        pack_dir.mkdir()
        _minimal_pack(pack_dir)
        world_dir = pack_dir / "worlds" / "w"
        world_dir.mkdir(parents=True)
        _minimal_world(world_dir)
        (world_dir / "cartography.yaml").write_text(
            "navigation_mode: region\nstarting_region: r1\n"
            "regions:\n  r1: {name: R1, summary: s, description: d}\n"
            "  r2: {name: R2, summary: s, description: d}\n",
            encoding="utf-8",
        )
        (world_dir / "map.yaml").write_text(
            "treatment: raster\nimage: sheet.jpg\n"
            "provenance: {source: OS, date: '1900', archive: NLS, pd_basis: expired}\n"
            "node_anchors:\n  r1: [1, 2]\n",  # r2 missing
            encoding="utf-8",
        )
        errors, _ = validate_pack_structure(pack_dir, schema_path_real)
        assert any("r2" in e and "anchor" in e.lower() for e in errors), errors

    def test_raster_map_missing_provenance_is_error(self, tmp_path: Path) -> None:
        pack_dir = tmp_path / "p"
        pack_dir.mkdir()
        _minimal_pack(pack_dir)
        world_dir = pack_dir / "worlds" / "w"
        world_dir.mkdir(parents=True)
        _minimal_world(world_dir)
        (world_dir / "cartography.yaml").write_text(
            "navigation_mode: region\nstarting_region: r1\n"
            "regions:\n  r1: {name: R1, summary: s, description: d}\n",
            encoding="utf-8",
        )
        (world_dir / "map.yaml").write_text(
            "treatment: raster\nimage: sheet.jpg\nnode_anchors:\n  r1: [1, 2]\n",
            encoding="utf-8",
        )
        errors, _ = validate_pack_structure(pack_dir, schema_path_real)
        assert any("provenance" in e.lower() for e in errors), errors

    def test_absent_map_yaml_is_ok(self, tmp_path: Path) -> None:
        pack_dir = tmp_path / "p"
        pack_dir.mkdir()
        _minimal_pack(pack_dir)
        world_dir = pack_dir / "worlds" / "w"
        world_dir.mkdir(parents=True)
        _minimal_world(world_dir)  # writes an empty cartography.yaml, no map.yaml
        errors, _ = validate_pack_structure(pack_dir, schema_path_real)
        assert not any("map.yaml" in e for e in errors), errors
```
- [ ] Run them, SEE fail: `cd sidequest-server && uv run pytest tests/cli/validate/test_pack_validator.py -k "raster or absent_map" -v -n0` — EXPECT fail (validator ignores map.yaml).
- [ ] Add `_validate_map_treatment` to `pack.py` (mirror `_validate_history_trope_refs`'s shape: absent file → `[]`, parse error → the read_err string, one `f"{label}: ..."` per violation):
```python
def _validate_map_treatment(world_dir: Path, label: str) -> list[str]:
    """Spec §2/§5: a raster main-map treatment must declare provenance and an
    anchor for every cartography region. Absent map.yaml → dag fallback (OK)."""
    map_path = world_dir / "map.yaml"
    if not map_path.is_file():
        return []
    data, read_err = _read_yaml(map_path, label)
    if read_err is not None:
        return [read_err]
    if not isinstance(data, dict):
        return [f"{label}: map.yaml must be a mapping"]
    kind = data.get("treatment")
    if kind not in {"raster", "orrery", "dag", "generated"}:
        return [f"{label}: map.yaml has unknown treatment {kind!r} "
                f"(raster|orrery|dag|generated)"]
    if kind != "raster":
        return []

    errors: list[str] = []
    if not data.get("image"):
        errors.append(f"{label}: raster map.yaml requires a non-empty 'image'")
    prov = data.get("provenance")
    required_prov = ("source", "date", "archive", "pd_basis")
    if not isinstance(prov, dict):
        errors.append(f"{label}: raster map.yaml requires a 'provenance' block "
                      f"({', '.join(required_prov)})")
    else:
        for key in required_prov:
            if not prov.get(key):
                errors.append(f"{label}: raster map.yaml provenance missing {key!r}")

    cart_path = world_dir / "cartography.yaml"
    cart_data, cart_err = _read_yaml(cart_path, label)
    if cart_err is not None:
        return errors + [cart_err]
    regions = (cart_data or {}).get("regions") or {}
    anchors = data.get("node_anchors") or {}
    if isinstance(regions, dict):
        for region_id in regions:
            if region_id not in anchors:
                errors.append(
                    f"{label}: raster map.yaml has no node_anchor for region "
                    f"{region_id!r} (every region needs an anchor)"
                )
    return errors
```
- [ ] Call it from `_validate_world` alongside the other content checks: `content_errors.extend(_validate_map_treatment(world_dir, label))` (use the same `label = f"world '{world_dir.name}'"` variable already in scope).
- [ ] Run to pass: `cd sidequest-server && uv run pytest tests/cli/validate/test_pack_validator.py -k "raster or absent_map" -v -n0` — EXPECT pass.
- [ ] Regression: `cd sidequest-server && uv run pytest tests/cli/validate/test_pack_validator.py -v -n0` — EXPECT the happy-path `test_valid_pack_passes` still green (absent map.yaml is OK).
- [ ] Lint + format + commit:
```
cd sidequest-server && uv run ruff check sidequest/cli/validate/pack.py tests/cli/validate/test_pack_validator.py && uv run ruff format sidequest/cli/validate/pack.py tests/cli/validate/test_pack_validator.py && git add sidequest/cli/validate/pack.py tests/cli/validate/test_pack_validator.py && git commit -m "feat(validate): raster map.yaml anchor-coverage + provenance gate (spec §5 A1)

Content invariant lives in the CI-gated pack validator, not unit tests.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 9: Content — Glenross OS-sheet `map.yaml` + authoring checklist (content)

**Files:**
- Create: `sidequest-content/genre_packs/tea_and_murder/worlds/glenross/map.yaml`.
- Create: `sidequest-content/genre_packs/tea_and_murder/worlds/glenross/assets/maps/.gitkeep` (the real scan is sourced separately; see checklist).

**Interfaces:**
- Consumes: the 14 real region ids from `glenross/cartography.yaml` (`the_glenross_arms`, `the_post_office`, `the_tea_rooms`, `the_school`, `the_surgery`, `the_manse`, `st_margarets_chapel`, `the_kirk_of_st_maelrubha`, `the_railway_halt`, `the_bridge`, `the_distillery`, `castle_ross`, `the_cricket_ground`, `the_long_pass`).
- Produces: a `raster` treatment the validator accepts (all 14 anchors present, provenance complete). Pixel anchors are **placeholders on a 1024×768 canvas** — Keith calibrates them against the real NLS scan (checklist).

Steps:
- [ ] Write `map.yaml` (every cartography region gets a placeholder anchor; provenance complete):
```yaml
# Glenross main-map treatment (spec §2 A1). Ordnance Survey period sheet.
# Anchors are placeholders on a 1024x768 canvas — recalibrate against the
# real NLS scan once sourced (see assets/maps/README authoring checklist).
treatment: raster
image: os_one_inch_glenross.jpg
provenance:
  source: "Ordnance Survey, One-Inch to the Mile, Scotland"
  date: "1900"
  archive: "National Library of Scotland — Map Images (maps.nls.uk)"
  pd_basis: "Crown copyright expired (published more than 50 years ago)"
style_hints:
  faction_layer: default
  routes: default
node_anchors:
  the_glenross_arms: [512, 384]
  the_post_office: [560, 360]
  the_tea_rooms: [472, 360]
  the_school: [600, 420]
  the_surgery: [440, 300]
  the_manse: [560, 300]
  st_margarets_chapel: [620, 340]
  the_kirk_of_st_maelrubha: [360, 260]
  the_railway_halt: [700, 480]
  the_bridge: [512, 480]
  the_distillery: [300, 420]
  castle_ross: [420, 180]
  the_cricket_ground: [640, 520]
  the_long_pass: [200, 140]
```
- [ ] Add the authoring checklist. Create `sidequest-content/genre_packs/tea_and_murder/worlds/glenross/assets/maps/README.md`:
```markdown
# Glenross main-map raster — authoring checklist

1. Source the PD scan: an out-of-copyright Ordnance Survey One-Inch sheet
   covering the Glenross area from the National Library of Scotland
   (maps.nls.uk). Confirm publication >50 years ago (Crown copyright expired).
2. Save it here as `os_one_inch_glenross.jpg` (the `image:` in ../../map.yaml).
3. Calibrate `node_anchors` in ../../map.yaml against the real scan: open the
   image, read the [x, y] pixel of each region's landmark, replace the
   placeholders. Every one of the 14 regions MUST have an anchor (validator).
4. Upload to R2 (canonical media source) via the orchestrator scripts:
   `python scripts/r2_sync_packs.py` then `python scripts/r2_manifest_from_bucket.py`
   (run from the orchestrator root; these are separate manual steps — render/copy
   scripts do NOT auto-upload).
5. Verify: `just content-validate tea_and_murder` passes and the Map tab shows
   the scan with pins in place.
```
- [ ] Verify the validator accepts it: `cd sidequest-server && uv run python -m sidequest.cli.validate pack ../sidequest-content/genre_packs/tea_and_murder` — EXPECT no map.yaml errors for glenross (a missing image FILE is OK; the validator checks the `image:` field is declared, not that the file exists — the file arrives via the checklist/R2).
- [ ] Commit (content subrepo):
```
cd sidequest-content && git add genre_packs/tea_and_murder/worlds/glenross/map.yaml genre_packs/tea_and_murder/worlds/glenross/assets/maps/README.md genre_packs/tea_and_murder/worlds/glenross/assets/maps/.gitkeep && git commit -m "content(glenross): raster map.yaml (OS one-inch sheet) + sourcing checklist (spec §2 A1)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 10: Content — Années Folles Baedeker `map.yaml` (content)

**Files:**
- Create: `sidequest-content/genre_packs/pulp_noir/worlds/annees_folles/map.yaml`.
- Create: `sidequest-content/genre_packs/pulp_noir/worlds/annees_folles/assets/maps/README.md` + `.gitkeep`.

**Interfaces:**
- Consumes: the 11 real region ids from `annees_folles/cartography.yaml` (`montparnasse`, `montmartre`, `pigalle`, `saint_germain`, `latin_quarter`, `marais`, `les_halles`, `opera_grands_boulevards`, `ile_de_la_cite`, `seizieme`, `gare_montparnasse`).
- Produces: a `raster` treatment (Baedeker city plan) the validator accepts.

Steps:
- [ ] Write `map.yaml` (placeholder anchors on a 1024×768 canvas, roughly Paris-arrondissement-relative; provenance complete):
```yaml
# Années Folles main-map treatment (spec §2 A1). Baedeker Paris city plan.
treatment: raster
image: baedeker_paris_plan.jpg
provenance:
  source: "Baedeker's Paris and Environs — city plan"
  date: "1913"
  archive: "David Rumsey Map Collection"
  pd_basis: "Published pre-1929; copyright expired (public domain)"
style_hints:
  faction_layer: default
  routes: default
node_anchors:
  montparnasse: [440, 560]
  montmartre: [560, 140]
  pigalle: [520, 200]
  saint_germain: [460, 460]
  latin_quarter: [540, 500]
  marais: [640, 420]
  les_halles: [560, 380]
  opera_grands_boulevards: [520, 300]
  ile_de_la_cite: [540, 440]
  seizieme: [280, 380]
  gare_montparnasse: [420, 600]
```
- [ ] Write `assets/maps/README.md` (same checklist shape as Task 9, but source = David Rumsey / BnF Gallica Baedeker Paris plan; filename `baedeker_paris_plan.jpg`; R2 upload via the same two orchestrator scripts).
- [ ] Verify: `cd sidequest-server && uv run python -m sidequest.cli.validate pack ../sidequest-content/genre_packs/pulp_noir` — EXPECT no map.yaml errors for annees_folles.
- [ ] Commit:
```
cd sidequest-content && git add genre_packs/pulp_noir/worlds/annees_folles/map.yaml genre_packs/pulp_noir/worlds/annees_folles/assets/maps/README.md genre_packs/pulp_noir/worlds/annees_folles/assets/maps/.gitkeep && git commit -m "content(annees_folles): raster map.yaml (Baedeker Paris plan) + sourcing checklist (spec §2 A1)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 11: Content — The Circuit highway `map.yaml` with defacement style (content)

**Files:**
- Create: `sidequest-content/genre_packs/road_warrior/worlds/the_circuit/map.yaml`.
- Create: `sidequest-content/genre_packs/road_warrior/worlds/the_circuit/assets/maps/README.md` + `.gitkeep`.

**Interfaces:**
- Consumes: the 13 real region ids from `the_circuit/cartography.yaml` (`sturmichi`, `bruveil`, `nokutori`, `doracanto`, `farolumi`, `aschgrund`, `grisevont`, `nottavello`, `grensholt`, `langbrenner`, `harifasi`, `damreocha`, `bromsviken`).
- Produces: a `raster` treatment carrying `style_hints` that A1's RasterMap keys off for the road_warrior look — `routes: highway_tracing` (route-number shields, mileage ticks) and `faction_layer: wasteland_defacement` (scrawled gang-territory annotations). Same schema — a rendering style keyed off genre theme, no new engine surface (spec §2).

Steps:
- [ ] Write `map.yaml` (13 anchors; the defacement/highway style_hints):
```yaml
# The Circuit main-map treatment (spec §2 A1). Mid-century state highway map.
# road_warrior renders routes as highway tracing and the faction layer as
# wasteland defacement (RasterMap reads style_hints; no new engine surface).
treatment: raster
image: state_highway_map.jpg
provenance:
  source: "State Highway Department official road map"
  date: "1955"
  archive: "US government works / state DOT archive"
  pd_basis: "US government work — public domain"
style_hints:
  faction_layer: wasteland_defacement
  routes: highway_tracing
node_anchors:
  sturmichi: [500, 400]
  bruveil: [620, 340]
  nokutori: [700, 460]
  doracanto: [560, 520]
  farolumi: [420, 300]
  aschgrund: [340, 460]
  grisevont: [640, 220]
  nottavello: [760, 360]
  grensholt: [280, 360]
  langbrenner: [460, 200]
  harifasi: [820, 500]
  damreocha: [200, 480]
  bromsviken: [380, 600]
```
- [ ] Write `assets/maps/README.md` (checklist; source = mid-century US state highway department map / pre-war auto-trail atlas, US-gov PD; filename `state_highway_map.jpg`; R2 upload via the two orchestrator scripts).
- [ ] Verify: `cd sidequest-server && uv run python -m sidequest.cli.validate pack ../sidequest-content/genre_packs/road_warrior` — EXPECT no map.yaml errors for the_circuit.
- [ ] Commit:
```
cd sidequest-content && git add genre_packs/road_warrior/worlds/the_circuit/map.yaml genre_packs/road_warrior/worlds/the_circuit/assets/maps/README.md genre_packs/road_warrior/worlds/the_circuit/assets/maps/.gitkeep && git commit -m "content(the_circuit): raster map.yaml (state highway map) + wasteland-defacement style (spec §2 A1)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 12: UI — `MapState.treatment` type + `RasterTreatment` interface (ui)

**Files:**
- Modify: `sidequest-ui/src/components/MapOverlay.tsx` — add `RasterTreatment` interface and a `treatment?: RasterTreatment` field on `MapState` (~L110–116).

**Interfaces:**
- Produces:
```tsx
export interface RasterTreatment {
  kind: string;                                   // raster | orrery | dag | generated
  image_url: string | null;
  node_anchors: Record<string, [number, number]>;
  style_hints: Record<string, unknown>;
}
// MapState gains:  treatment?: RasterTreatment;
```
- App.tsx already blind-casts the MAP_UPDATE payload `as unknown as MapState`, so `treatment` reaches `mapData.treatment` at runtime with no handler change; this add is what makes it type-check.

Steps:
- [ ] Write the failing test. Create `sidequest-ui/src/components/map/__tests__/RasterTreatmentType.test.ts`:
```ts
import { describe, it, expect } from "vitest";
import type { MapState, RasterTreatment } from "@/components/MapOverlay";

describe("MapState.treatment type", () => {
  it("accepts a raster treatment", () => {
    const t: RasterTreatment = {
      kind: "raster",
      image_url: "https://cdn/sheet.jpg",
      node_anchors: { r1: [1, 2] },
      style_hints: { faction_layer: "default" },
    };
    const s: MapState = {
      current_location: "r1",
      region: "w",
      explored: [],
      fog_bounds: { width: 0, height: 0 },
      treatment: t,
    };
    expect(s.treatment?.kind).toBe("raster");
  });
});
```
- [ ] Run it, SEE it fail: `cd sidequest-ui && npx vitest run src/components/map/__tests__/RasterTreatmentType.test.ts` — EXPECT type error / fail (`RasterTreatment` unexported, `treatment` not on MapState).
- [ ] Add `RasterTreatment` (near `CartographyMetadata`) and the `treatment?` field on `MapState` in `MapOverlay.tsx`.
- [ ] Run to pass: `cd sidequest-ui && npx vitest run src/components/map/__tests__/RasterTreatmentType.test.ts` — EXPECT pass.
- [ ] Lint + commit:
```
cd sidequest-ui && npx eslint src/components/MapOverlay.tsx src/components/map/__tests__/RasterTreatmentType.test.ts && git add src/components/MapOverlay.tsx src/components/map/__tests__/RasterTreatmentType.test.ts && git commit -m "feat(ui): MapState.treatment / RasterTreatment type (spec §4 A1)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 13: UI — `RasterMap.tsx` component (ui)

**Files:**
- Create: `sidequest-ui/src/components/map/RasterMap.tsx`.
- Create: `sidequest-ui/src/components/map/__tests__/RasterMap.test.tsx`.

**Interfaces:**
- Consumes: `RasterTreatment`, `MapState` (Task 12). Pan/zoom mechanism lifted from `OrbitalChartView.tsx` (imperative `translate()/scale()` on a wrapping transform, wheel clamp [0.25, 8], drag-pan via `panRef` delta-from-clientX).
- Produces:
```tsx
export interface RasterMapProps {
  treatment: RasterTreatment;
  mapData: MapState;
  onNodeSelect?: (regionId: string) => void;
}
export function RasterMap(props: RasterMapProps): JSX.Element;
```
- DOM contract (testids): host `data-testid="map-panel-raster"`; the `<img>` `data-testid="raster-scan"`; one pin per anchored region `data-region-id="<id>"`; the current-location pin marked `data-current="true"`; on image error → `data-testid="map-panel-raster-error"` (explicit error, NEVER a dag fallback — spec §5).

**Note (Track B touchpoint):** this is a new file; no contention. The faction layer honors `treatment.style_hints.faction_layer` (`"wasteland_defacement"` for road_warrior draws crossed-out/scrawled annotations) and `style_hints.routes` (`"highway_tracing"` draws route lines with shields/ticks). Keep the style branches data-driven off `style_hints`, not genre strings.

Steps:
- [ ] Write the failing test. Create `sidequest-ui/src/components/map/__tests__/RasterMap.test.tsx`:
```tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import type { MapState, RasterTreatment } from "@/components/MapOverlay";
import { RasterMap } from "../RasterMap";

const TREATMENT: RasterTreatment = {
  kind: "raster",
  image_url: "https://cdn/sheet.jpg",
  node_anchors: { r1: [100, 120], r2: [300, 240] },
  style_hints: { faction_layer: "default", routes: "default" },
};
const MAP: MapState = {
  current_location: "r1",
  region: "w",
  explored: [],
  fog_bounds: { width: 0, height: 0 },
  cartography: {
    navigation_mode: "region",
    starting_region: "r1",
    regions: { r1: { name: "R1" }, r2: { name: "R2" } },
    routes: [],
  },
  treatment: TREATMENT,
};

describe("RasterMap", () => {
  it("renders the scan image and a pin per anchored region", () => {
    const { container } = render(<RasterMap treatment={TREATMENT} mapData={MAP} />);
    expect(screen.getByTestId("map-panel-raster")).toBeInTheDocument();
    expect(screen.getByTestId("raster-scan")).toHaveAttribute("src", "https://cdn/sheet.jpg");
    expect(container.querySelectorAll("[data-region-id]")).toHaveLength(2);
    expect(container.querySelector('[data-region-id="r1"]')).toHaveAttribute("data-current", "true");
  });

  it("fires onNodeSelect when a pin is clicked (orientation, not travel)", () => {
    const onSelect = vi.fn();
    const { container } = render(<RasterMap treatment={TREATMENT} mapData={MAP} onNodeSelect={onSelect} />);
    fireEvent.click(container.querySelector('[data-region-id="r2"]')!);
    expect(onSelect).toHaveBeenCalledWith("r2");
  });

  it("shows an explicit error state on image load failure (no dag fallback)", () => {
    render(<RasterMap treatment={TREATMENT} mapData={MAP} />);
    fireEvent.error(screen.getByTestId("raster-scan"));
    expect(screen.getByTestId("map-panel-raster-error")).toBeInTheDocument();
  });
});
```
- [ ] Run it, SEE it fail: `cd sidequest-ui && npx vitest run src/components/map/__tests__/RasterMap.test.tsx` — EXPECT fail (component missing).
- [ ] Implement `RasterMap.tsx`. Complete component:
```tsx
import { useRef, useState, useCallback } from "react";
import type { MapState, RasterTreatment } from "@/components/MapOverlay";

export interface RasterMapProps {
  treatment: RasterTreatment;
  mapData: MapState;
  onNodeSelect?: (regionId: string) => void;
}

const PIN_R = 7;

export function RasterMap({ treatment, mapData, onNodeSelect }: RasterMapProps) {
  const vpRef = useRef<HTMLDivElement | null>(null);
  const panRef = useRef({ x: 0, y: 0 });
  const dragRef = useRef<{ startX: number; startY: number } | null>(null);
  const [scale, setScale] = useState(1);
  const [dragging, setDragging] = useState(false);
  const [imgFailed, setImgFailed] = useState(false);

  const apply = useCallback((s: number, p: { x: number; y: number }) => {
    const vp = vpRef.current;
    if (vp) vp.style.transform = `translate(${p.x}px, ${p.y}px) scale(${s})`;
  }, []);

  function onWheel(e: React.WheelEvent<HTMLDivElement>) {
    e.preventDefault();
    const next = Math.max(0.25, Math.min(8, scale * (e.deltaY < 0 ? 1.1 : 0.9)));
    setScale(next);
    apply(next, panRef.current);
  }
  function onMouseDown(e: React.MouseEvent<HTMLDivElement>) {
    dragRef.current = { startX: e.clientX - panRef.current.x, startY: e.clientY - panRef.current.y };
    setDragging(true);
  }
  function onMouseMove(e: React.MouseEvent<HTMLDivElement>) {
    if (!dragRef.current) return;
    panRef.current = { x: e.clientX - dragRef.current.startX, y: e.clientY - dragRef.current.startY };
    apply(scale, panRef.current);
  }
  function onMouseUp() {
    dragRef.current = null;
    setDragging(false);
  }

  if (imgFailed) {
    return (
      <div
        data-testid="map-panel-raster-error"
        className="flex items-center justify-center h-full text-sm p-4 text-[var(--text-muted)]"
      >
        Map scan unavailable. Check the R2 upload for this world's map image.
      </div>
    );
  }

  const anchors = treatment.node_anchors ?? {};
  const routeTracing = treatment.style_hints?.routes === "highway_tracing";
  const defaced = treatment.style_hints?.faction_layer === "wasteland_defacement";
  const routes = mapData.cartography?.routes ?? [];

  return (
    <div
      data-testid="map-panel-raster"
      className="relative overflow-hidden w-full h-full bg-[var(--surface)]"
      onWheel={onWheel}
      onMouseDown={onMouseDown}
      onMouseMove={onMouseMove}
      onMouseUp={onMouseUp}
      onMouseLeave={onMouseUp}
      style={{ cursor: dragging ? "grabbing" : "grab" }}
    >
      <div ref={vpRef} style={{ transformOrigin: "0 0", position: "absolute", top: 0, left: 0 }}>
        <img
          data-testid="raster-scan"
          src={treatment.image_url ?? ""}
          alt="World map"
          className="block max-w-none select-none"
          draggable={false}
          onError={() => setImgFailed(true)}
        />
        <svg className="absolute top-0 left-0 overflow-visible" aria-label="Map overlay">
          {routes.map((rt, i) => {
            const a = rt.from_id ? anchors[rt.from_id] : undefined;
            const b = rt.to_id ? anchors[rt.to_id] : undefined;
            if (!a || !b) return null;
            return (
              <line
                key={i}
                data-route-tracing={routeTracing ? "true" : "false"}
                x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]}
                stroke="var(--accent)"
                strokeWidth={routeTracing ? 3 : 1.5}
                strokeDasharray={routeTracing ? "6 3" : undefined}
              />
            );
          })}
          {Object.entries(anchors).map(([regionId, [x, y]]) => {
            const isCurrent = regionId === mapData.current_location;
            return (
              <g
                key={regionId}
                data-region-id={regionId}
                data-current={isCurrent ? "true" : undefined}
                data-defaced={defaced ? "true" : undefined}
                onClick={() => onNodeSelect?.(regionId)}
                style={{ cursor: "pointer" }}
              >
                <circle
                  cx={x} cy={y} r={PIN_R}
                  fill={isCurrent ? "var(--accent)" : "var(--surface-raised)"}
                  stroke="var(--text)"
                  strokeWidth={isCurrent ? 3 : 1.5}
                />
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
```
- [ ] Run to pass: `cd sidequest-ui && npx vitest run src/components/map/__tests__/RasterMap.test.tsx` — EXPECT pass. (If `fireEvent.error` on the img doesn't flip state in jsdom, ensure the `onError` handler is on the `<img>` and the test targets `raster-scan`.)
- [ ] Lint + commit:
```
cd sidequest-ui && npx eslint src/components/map/RasterMap.tsx src/components/map/__tests__/RasterMap.test.tsx && git add src/components/map/RasterMap.tsx src/components/map/__tests__/RasterMap.test.tsx && git commit -m "feat(ui): RasterMap — scan + SVG overlay (pins, routes, party marker, pan/zoom) (spec §4 A1)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 14: UI — `MapWidget` raster routing branch (ui)

**Files:**
- Modify: `sidequest-ui/src/components/GameBoard/widgets/MapWidget.tsx` — add ONE early-return branch after the `if (!mapData)` guard (~L237) and before the room-graph branch (~L248); import `RasterMap`.
- Modify: `sidequest-ui/src/components/GameBoard/widgets/__tests__/MapWidget.test.tsx` — add a routing test + the sanctioned raw-import wiring test.

**Interfaces:**
- Consumes: `RasterMap` (Task 13), `MapState.treatment` (Task 12).
- Produces: MapWidget renders `<RasterMap>` when `mapData.treatment?.kind === "raster"`, else the existing cascade is unchanged (dag/orrery/room-graph). Orrery worlds are chosen by the `orbital` flag before this branch, so `treatment: orrery` needs no MapWidget change. `dag`/`generated`/absent → fall through to the existing fallback (by design).

Steps:
- [ ] Write the failing tests. Add to `MapWidget.test.tsx`:
```tsx
  it("routes a raster treatment to RasterMap, not MapOverlay", () => {
    const mapData = {
      current_location: "r1",
      region: "w",
      explored: [],
      fog_bounds: { width: 0, height: 0 },
      cartography: { navigation_mode: "region", starting_region: "r1", regions: { r1: { name: "R1" } }, routes: [] },
      treatment: { kind: "raster", image_url: "https://cdn/x.jpg", node_anchors: { r1: [1, 2] }, style_hints: {} },
    } as unknown as import("@/components/MapOverlay").MapState;
    const { queryByTestId } = render(<MapWidget mapData={mapData} />);
    expect(queryByTestId("map-panel-raster")).toBeInTheDocument();
    expect(queryByTestId("map-overlay")).not.toBeInTheDocument();
  });

  it("MapWidget module imports RasterMap (raster branch A1)", async () => {
    const src = (await import("../MapWidget?raw")) as unknown as { default: string };
    expect(src.default).toContain("@/components/map/RasterMap");
  });
```
- [ ] Run them, SEE fail: `cd sidequest-ui && npx vitest run src/components/GameBoard/widgets/__tests__/MapWidget.test.tsx -t raster` — EXPECT fail.
- [ ] Add the import `import { RasterMap } from "@/components/map/RasterMap";` and insert the branch immediately after the `if (!mapData) { return ...; }` guard:
```tsx
  if (mapData.treatment?.kind === "raster") {
    return (
      <div data-testid="map-panel-raster-host" style={{ width: "100%", height: "100%" }}>
        <RasterMap treatment={mapData.treatment} mapData={mapData} />
      </div>
    );
  }
```
- [ ] Run to pass: `cd sidequest-ui && npx vitest run src/components/GameBoard/widgets/__tests__/MapWidget.test.tsx -t raster` — EXPECT pass.
- [ ] Regression: `cd sidequest-ui && npx vitest run src/components/GameBoard/widgets/__tests__/MapWidget.test.tsx` — EXPECT the existing orrery/room-graph/overlay branch tests still green.
- [ ] Lint + commit:
```
cd sidequest-ui && npx eslint src/components/GameBoard/widgets/MapWidget.tsx src/components/GameBoard/widgets/__tests__/MapWidget.test.tsx && git add src/components/GameBoard/widgets/MapWidget.tsx src/components/GameBoard/widgets/__tests__/MapWidget.test.tsx && git commit -m "feat(ui): MapWidget routes raster treatment to RasterMap (spec §4 A1)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 15: UI — MobileTabView tab-reachability wiring test (ui)

**Files:**
- Create: `sidequest-ui/src/components/GameBoard/__tests__/GameBoard-map-raster-tab.test.tsx`.

**Interfaces:**
- Consumes: `GameBoard` (renders the MobileTabView path under jsdom). The `map` tab is ALREADY dual-registered (widgetRegistry `map` entry + MobileTabView `TABS` `{ id: "map", label: "Map" }`) and always available (`available.add("map")`), so RasterMap needs NO new registration — it rides the existing Map tab. This test proves RasterMap is REACHABLE through the mobile tab path (the jsdom wiring tripwire), closing the "every emitter/renderer needs a reachability wiring test" rule.

Steps:
- [ ] Write the wiring test. Model it on `GameBoard-location-tab.test.tsx` (`renderBoard` helper + `getByRole("tab", { name: /^map$/i })`). Pass a `mapData` prop carrying a raster treatment (via whatever prop GameBoard threads to MapWidget — grep `mapData` in `GameBoard.tsx` to confirm the prop name), click the Map tab, assert `map-panel-raster` renders:
```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { GameBoard, type GameBoardProps } from "../GameBoard";
import { ImageBusProvider } from "@/providers/ImageBusProvider";

const RASTER_MAP = {
  current_location: "r1", region: "w", explored: [], fog_bounds: { width: 0, height: 0 },
  cartography: { navigation_mode: "region", starting_region: "r1", regions: { r1: { name: "R1" } }, routes: [] },
  treatment: { kind: "raster", image_url: "https://cdn/x.jpg", node_anchors: { r1: [1, 2] }, style_hints: {} },
};

function renderBoard(overrides: Partial<GameBoardProps> = {}) {
  const defaults: GameBoardProps = {
    messages: [],
    characters: [{ player_id: "p1", name: "Mira", character_name: "Mira", class: "Sleuth",
      level: 1, hp: 10, hp_max: 10, status_effects: [], portrait_url: "", current_location: "" }],
    onSend: vi.fn(), disabled: false,
  };
  const props = { ...defaults, ...overrides };
  return render(
    <ImageBusProvider messages={props.messages ?? []}>
      <GameBoard {...props} />
    </ImageBusProvider>,
  );
}

describe("GameBoard — raster map reachable via Map tab (wiring)", () => {
  it("renders RasterMap when the Map tab is opened with a raster treatment", () => {
    // NOTE: confirm the mapData prop name on GameBoardProps by grepping GameBoard.tsx.
    renderBoard({ mapData: RASTER_MAP } as unknown as Partial<GameBoardProps>);
    fireEvent.click(screen.getByRole("tab", { name: /^map$/i }));
    expect(screen.getByTestId("map-panel-raster")).toBeInTheDocument();
  });
});
```
- [ ] Confirm the `mapData` prop name on `GameBoardProps`: `cd sidequest-ui && grep -n "mapData" src/components/GameBoard/GameBoard.tsx | head` — adjust the override key/type if needed.
- [ ] Run, SEE it pass once the prop is threaded correctly (it exercises Tasks 12–14 together): `cd sidequest-ui && npx vitest run src/components/GameBoard/__tests__/GameBoard-map-raster-tab.test.tsx` — EXPECT pass. If the Map tab isn't reachable because it's data-gated on something else, verify `available.add("map")` in GameBoard.tsx and that the raster `mapData` satisfies any content-signal gating.
- [ ] Lint + commit:
```
cd sidequest-ui && npx eslint src/components/GameBoard/__tests__/GameBoard-map-raster-tab.test.tsx && git add src/components/GameBoard/__tests__/GameBoard-map-raster-tab.test.tsx && git commit -m "test(ui): raster map reachable via MobileTabView Map tab (wiring, spec §4 A1)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 16: A2 — `Region.weather_zone` field (server)

**Files:**
- Modify: `sidequest-server/sidequest/genre/models/world.py` — add `weather_zone: str | None = None` on `Region` (after `controlled_by`, ~L220).

**Interfaces:**
- Produces: `Region.weather_zone: str | None` — the optional binding of a cartography region to a climate zone in the world's `weather.yaml` (spec §2). `Region` has `extra="allow"`, so this authored field already round-trips; the explicit field makes it typed + accessible + documentable.

Steps:
- [ ] Write the failing test. Create `sidequest-server/tests/genre/test_region_weather_zone.py`:
```python
from sidequest.genre.models.world import Region


def test_region_accepts_weather_zone() -> None:
    r = Region.model_validate(
        {"name": "Castle Ross", "summary": "s", "description": "d", "weather_zone": "highland_pass"}
    )
    assert r.weather_zone == "highland_pass"


def test_region_weather_zone_defaults_none() -> None:
    r = Region.model_validate({"name": "The Bridge", "summary": "s", "description": "d"})
    assert r.weather_zone is None
```
- [ ] Run it, SEE it fail: `cd sidequest-server && uv run pytest tests/genre/test_region_weather_zone.py -v -n0` — EXPECT fail (attribute absent; `extra="allow"` keeps it in `__pydantic_extra__`, not as `.weather_zone`).
- [ ] Add `weather_zone: str | None = None` to `Region`.
- [ ] Run to pass: `cd sidequest-server && uv run pytest tests/genre/test_region_weather_zone.py -v -n0` — EXPECT pass.
- [ ] Lint + format + commit:
```
cd sidequest-server && uv run ruff check sidequest/genre/models/world.py tests/genre/test_region_weather_zone.py && uv run ruff format sidequest/genre/models/world.py tests/genre/test_region_weather_zone.py && git add sidequest/genre/models/world.py tests/genre/test_region_weather_zone.py && git commit -m "feat(cartography): Region.weather_zone binds geography to climate (spec §2 A2)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 17: A2 — region-aware bootstrap zone selection (server)

**Files:**
- Modify: `sidequest-server/sidequest/game/world_grounding_bootstrap.py` — `load_world_grounding` + a new `_select_zone_for_region(...)` that prefers the STARTING region's `weather_zone` over the genre hardcode.
- Modify: `sidequest-server/sidequest/handlers/connect.py` — pass the world's cartography/starting-region into `load_world_grounding` (grep the call site ~L649 / ~L1177).

**Interfaces:**
- Consumes: `CartographyConfig` (`starting_region`, `regions[...].weather_zone`), `ClimateRulesFile`.
- Produces: `load_world_grounding(..., cartography: CartographyConfig | None = None)` selects the climate zone from `cartography.regions[cartography.starting_region].weather_zone` when present (and valid against the loaded rules), else the existing `_select_zone_season` behavior (genre override table → first-zone default). This "binds weather to geography" at session start with no silent drift (a declared-but-invalid zone fails loud, mirroring `_select_zone_season`).

Steps:
- [ ] Write the failing test. Create `sidequest-server/tests/game/test_weather_region_zone_selection.py`:
```python
from pathlib import Path

import pytest

from sidequest.game.weather import ClimateRulesFile
from sidequest.game.world_grounding_bootstrap import _select_zone_for_region

_RULES = ClimateRulesFile.model_validate(
    {
        "climate_zones": {
            "glen_floor": {"seasons": {"autumn": {"temp_range": [5, 12], "conditions": ["smirr"], "weights": [1]}}},
            "highland_pass": {"seasons": {"autumn": {"temp_range": [-2, 6], "conditions": ["blizzard"], "weights": [1]}}},
        }
    }
)


class _Region:
    def __init__(self, wz):
        self.weather_zone = wz


class _Cart:
    def __init__(self, start, regions):
        self.starting_region = start
        self.regions = regions


def test_region_weather_zone_wins_over_default() -> None:
    cart = _Cart("castle_ross", {"castle_ross": _Region("highland_pass")})
    zone = _select_zone_for_region(_RULES, cart, genre_slug="tea_and_murder")
    assert zone == "highland_pass"


def test_no_region_zone_falls_back_to_genre_default() -> None:
    cart = _Cart("the_bridge", {"the_bridge": _Region(None)})
    # tea_and_murder genre override picks glen_floor.
    zone = _select_zone_for_region(_RULES, cart, genre_slug="tea_and_murder")
    assert zone == "glen_floor"


def test_declared_but_invalid_region_zone_fails_loud() -> None:
    cart = _Cart("castle_ross", {"castle_ross": _Region("stratosphere")})
    with pytest.raises(ValueError):
        _select_zone_for_region(_RULES, cart, genre_slug="tea_and_murder")
```
- [ ] Run it, SEE it fail: `cd sidequest-server && uv run pytest tests/game/test_weather_region_zone_selection.py -v -n0` — EXPECT ImportError.
- [ ] Add `_select_zone_for_region` to `world_grounding_bootstrap.py`:
```python
def _select_zone_for_region(
    rules: ClimateRulesFile, cartography: Any, genre_slug: str
) -> str:
    """Prefer the starting region's ``weather_zone`` (spec §2 A2); else the
    existing genre-override / first-zone selection. A declared-but-unknown
    region zone fails loud (No Silent Fallbacks)."""
    start = getattr(cartography, "starting_region", None) if cartography else None
    regions = getattr(cartography, "regions", {}) if cartography else {}
    region = regions.get(start) if isinstance(regions, dict) else None
    wz = getattr(region, "weather_zone", None) if region is not None else None
    if wz is not None:
        if wz not in rules.climate_zones:
            raise ValueError(
                f"region {start!r} declares weather_zone {wz!r}, not in weather.yaml "
                f"(zones: {sorted(rules.climate_zones)})"
            )
        return wz
    zone, _season = _select_zone_season(rules, genre_slug)
    return zone
```
- [ ] Thread `cartography` through `load_world_grounding`: add a `cartography: Any | None = None` param, and where it currently does `zone, season = _select_zone_season(weather_rules, genre_slug)`, replace `zone` with `_select_zone_for_region(weather_rules, cartography, genre_slug)` while keeping the season from `_select_zone_season` (season binding is out of A2 scope — geography drives zone, not season).
- [ ] In `connect.py`, pass the loaded world's cartography to `load_world_grounding` at the call site (grep the existing `load_world_grounding(` invocation; add `cartography=<world>.cartography`).
- [ ] Run to pass: `cd sidequest-server && uv run pytest tests/game/test_weather_region_zone_selection.py -v -n0` — EXPECT pass.
- [ ] Regression (tea_and_murder still bootstraps): `cd sidequest-server && uv run pytest tests/game -k weather -v -n0` — EXPECT existing weather tests green.
- [ ] Lint + format + commit:
```
cd sidequest-server && uv run ruff check sidequest/game/world_grounding_bootstrap.py sidequest/handlers/connect.py tests/game/test_weather_region_zone_selection.py && uv run ruff format sidequest/game/world_grounding_bootstrap.py sidequest/handlers/connect.py tests/game/test_weather_region_zone_selection.py && git add sidequest/game/world_grounding_bootstrap.py sidequest/handlers/connect.py tests/game/test_weather_region_zone_selection.py && git commit -m "feat(weather): starting-region weather_zone drives bootstrap climate (spec §2 A2)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 18: A2 — validator: `weather_zone` must resolve to a real climate zone (server)

**Files:**
- Modify: `sidequest-server/sidequest/cli/validate/pack.py` — add `_validate_weather_zones(world_dir, label)` and call it from `_validate_world` (append to `content_errors`).
- Modify: `sidequest-server/tests/cli/validate/test_pack_validator.py` — add good/bad tests.

**Interfaces:**
- Consumes: the world's `cartography.yaml` (`regions[*].weather_zone`) and `weather.yaml` (`climate_zones` keys).
- Produces: `_validate_weather_zones(world_dir: Path, label: str) -> list[str]`. Any region `weather_zone` that isn't a key of the world's `weather.yaml` `climate_zones` → one error. A world with no `weather.yaml` but a region declaring a `weather_zone` → error (declares climate binding without a climate). No `weather_zone` anywhere → `[]`.

Steps:
- [ ] Write the failing tests. Add to `test_pack_validator.py`:
```python
    def test_region_weather_zone_unknown_is_error(self, tmp_path: Path) -> None:
        pack_dir = tmp_path / "p"
        pack_dir.mkdir()
        _minimal_pack(pack_dir)
        world_dir = pack_dir / "worlds" / "w"
        world_dir.mkdir(parents=True)
        _minimal_world(world_dir)
        (world_dir / "cartography.yaml").write_text(
            "navigation_mode: region\nstarting_region: r1\n"
            "regions:\n  r1: {name: R1, summary: s, description: d, weather_zone: nope}\n",
            encoding="utf-8",
        )
        (world_dir / "weather.yaml").write_text(
            "climate_zones:\n  glen_floor:\n    seasons:\n      autumn:\n"
            "        temp_range: [5, 12]\n        conditions: [smirr]\n        weights: [1]\n",
            encoding="utf-8",
        )
        errors, _ = validate_pack_structure(pack_dir, schema_path_real)
        assert any("weather_zone" in e and "nope" in e for e in errors), errors

    def test_region_weather_zone_valid_passes(self, tmp_path: Path) -> None:
        pack_dir = tmp_path / "p"
        pack_dir.mkdir()
        _minimal_pack(pack_dir)
        world_dir = pack_dir / "worlds" / "w"
        world_dir.mkdir(parents=True)
        _minimal_world(world_dir)
        (world_dir / "cartography.yaml").write_text(
            "navigation_mode: region\nstarting_region: r1\n"
            "regions:\n  r1: {name: R1, summary: s, description: d, weather_zone: glen_floor}\n",
            encoding="utf-8",
        )
        (world_dir / "weather.yaml").write_text(
            "climate_zones:\n  glen_floor:\n    seasons:\n      autumn:\n"
            "        temp_range: [5, 12]\n        conditions: [smirr]\n        weights: [1]\n",
            encoding="utf-8",
        )
        errors, _ = validate_pack_structure(pack_dir, schema_path_real)
        assert not any("weather_zone" in e for e in errors), errors
```
- [ ] Run them, SEE fail: `cd sidequest-server && uv run pytest tests/cli/validate/test_pack_validator.py -k weather_zone -v -n0` — EXPECT fail.
- [ ] Add `_validate_weather_zones` to `pack.py`:
```python
def _validate_weather_zones(world_dir: Path, label: str) -> list[str]:
    """Spec §2 A2: every region weather_zone must be a real climate zone."""
    cart_path = world_dir / "cartography.yaml"
    cart_data, cart_err = _read_yaml(cart_path, label)
    if cart_err is not None or not isinstance(cart_data, dict):
        return []  # cartography problems reported elsewhere
    regions = cart_data.get("regions") or {}
    declared = {
        rid: (r or {}).get("weather_zone")
        for rid, r in regions.items()
        if isinstance(r, dict) and (r or {}).get("weather_zone")
    }
    if not declared:
        return []
    weather_data, w_err = _read_yaml(world_dir / "weather.yaml", label)
    if w_err is not None:
        return [w_err]
    zones = set((weather_data or {}).get("climate_zones") or {}) if isinstance(weather_data, dict) else set()
    if not zones:
        return [f"{label}: regions declare weather_zone but world has no weather.yaml climate_zones"]
    errors: list[str] = []
    for rid, wz in declared.items():
        if wz not in zones:
            errors.append(
                f"{label}: region {rid!r} weather_zone {wz!r} is not a climate zone "
                f"(zones: {sorted(zones)})"
            )
    return errors
```
- [ ] Call it from `_validate_world`: `content_errors.extend(_validate_weather_zones(world_dir, label))`.
- [ ] Run to pass: `cd sidequest-server && uv run pytest tests/cli/validate/test_pack_validator.py -k weather_zone -v -n0` — EXPECT pass; then full validator file `-n0` green.
- [ ] Lint + format + commit:
```
cd sidequest-server && uv run ruff check sidequest/cli/validate/pack.py tests/cli/validate/test_pack_validator.py && uv run ruff format sidequest/cli/validate/pack.py tests/cli/validate/test_pack_validator.py && git add sidequest/cli/validate/pack.py tests/cli/validate/test_pack_validator.py && git commit -m "feat(validate): region weather_zone must resolve to a climate zone (spec §2 A2)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 19: A2 — per-region-change weather re-generation + span (server)

**Files:**
- Modify: `sidequest-server/sidequest/server/session_state.py` — cache `weather_generator` + `weather_season` on `_SessionData` at bootstrap (so re-gen needs no world-dir resolution on the hot turn path).
- Modify: `sidequest-server/sidequest/handlers/connect.py` — populate the two cached fields from the bootstrap.
- Modify: `sidequest-server/sidequest/server/websocket_session_handler.py` — in the region-mode `_region_changed` block (~L2551), when the new region declares a `weather_zone` differing from `sd.weather_state.zone`, re-sample and update `sd.weather_state`, emitting `weather.zone_changed`.

**Interfaces:**
- Consumes: `WeatherGenerator.generate(zone, season, seed) -> WeatherState`; the already-computed `_region_changed: bool` and `snapshot.current_region`; the world's cartography region `weather_zone`.
- Produces: as the party moves between regions of different climate zones, `sd.weather_state` re-samples (deterministic seed = `crc32(game_slug + region_id)`), so `get_world_grounding` reaches the narrator with per-zone weather. A `weather.zone_changed` OTEL event (`component="location"`) to `turn_telemetry`. This is the "reaches narrator grounding per-zone as the party moves" completion of A2; the core A2 (Tasks 16–18) is valuable without it.

Steps:
- [ ] Add the cache fields to `_SessionData` (grep the dataclass; add `weather_generator: Any | None = None` and `weather_season: str | None = None` near `weather_state`). Write a reflection tripwire test first (mirrors `tests/dungeon/test_setpiece_attach_wiring.py` assertion 4). Create `sidequest-server/tests/server/test_weather_zone_change.py`:
```python
import zlib
from types import SimpleNamespace

import sidequest.server.websocket_handlers.map_emit as _  # ensure package import side effects
from sidequest.game.weather import ClimateRulesFile, WeatherGenerator
from sidequest.server.session_state import _SessionData


def test_session_data_has_weather_cache_fields() -> None:
    fields = set(_SessionData.__dataclass_fields__)
    assert "weather_generator" in fields
    assert "weather_season" in fields
```
- [ ] Run it, SEE it fail: `cd sidequest-server && uv run pytest tests/server/test_weather_zone_change.py -v -n0` — EXPECT fail.
- [ ] Add the two fields to `_SessionData`; in `connect.py` set `session._session_data.weather_generator = WeatherGenerator(Path(world_dir)/"weather.yaml")` (only when `weather.yaml` exists — reuse the bootstrap's presence check) and `session._session_data.weather_season = <the season selected at bootstrap>` (thread the season out of `load_world_grounding`, or recompute via `_select_zone_season`). Keep it None when the world has no weather.
- [ ] Add a helper `regenerate_weather_for_region(sd, region_id, zone) -> None` (in `world_grounding_bootstrap.py` or a small helper module) that: returns early if `sd.weather_generator is None`; `seed = zlib.crc32(f"{game_slug}:{region_id}".encode())`; `sd.weather_state = sd.weather_generator.generate(zone, sd.weather_season, seed)`. Add a unit test in the same file that constructs a real `WeatherGenerator` from a synthetic `ClimateRulesFile`-shaped `weather.yaml` in `tmp_path`, calls the helper, and asserts `sd.weather_state.zone` flips to the new zone.
- [ ] In `websocket_session_handler.py`, inside `if _region_changed:` (region-mode block), resolve the new region's `weather_zone` from `sd.genre_pack.worlds[sd.world_slug].cartography.regions.get(snapshot.current_region)`; if it exists AND differs from `getattr(sd.weather_state, "zone", None)`, call the helper and publish:
```python
                            _new_region = _world_for_region_emit.cartography.regions.get(
                                snapshot.current_region
                            )
                            _new_zone = getattr(_new_region, "weather_zone", None)
                            _cur_zone = getattr(sd.weather_state, "zone", None)
                            if _new_zone and _new_zone != _cur_zone and sd.weather_generator is not None:
                                regenerate_weather_for_region(sd, snapshot.current_region, _new_zone)
                                _watcher_publish(
                                    "weather.zone_changed",
                                    {
                                        "world": sd.world_slug,
                                        "region": snapshot.current_region,
                                        "from_zone": _cur_zone or "",
                                        "to_zone": _new_zone,
                                    },
                                    component="location",
                                )
```
- [ ] Add a capture-based span test (monkeypatch `_watcher_publish` in the session-handler module) driving a synthetic region change and asserting one `weather.zone_changed` fires with the right `to_zone`. Add a DB-readback wiring test (bind `PgTelemetrySink`, assert the row lands in `turn_telemetry`) per the wiring rule.
- [ ] Run to pass: `cd sidequest-server && uv run pytest tests/server/test_weather_zone_change.py -v -n0` — EXPECT pass.
- [ ] Lint + format + commit:
```
cd sidequest-server && uv run ruff check sidequest/server/session_state.py sidequest/handlers/connect.py sidequest/server/websocket_session_handler.py sidequest/game/world_grounding_bootstrap.py tests/server/test_weather_zone_change.py && uv run ruff format sidequest/server/session_state.py sidequest/handlers/connect.py sidequest/server/websocket_session_handler.py sidequest/game/world_grounding_bootstrap.py tests/server/test_weather_zone_change.py && git add sidequest/server/session_state.py sidequest/handlers/connect.py sidequest/server/websocket_session_handler.py sidequest/game/world_grounding_bootstrap.py tests/server/test_weather_zone_change.py && git commit -m "feat(weather): re-sample weather per-zone on region change + zone_changed span (spec §2 A2)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 20: A2 content — Glenross `weather_zone` annotations (content)

**Files:**
- Modify: `sidequest-content/genre_packs/tea_and_murder/worlds/glenross/cartography.yaml` — add `weather_zone` to each region.

**Interfaces:**
- Consumes: glenross `weather.yaml` climate zones (`glen_floor`, `highland_pass`).
- Produces: high-altitude regions bound to `highland_pass`, the rest to `glen_floor`, so the validator (Task 18) passes and the party feels colder weather in the passes/castle (Task 17 bootstrap + Task 19 on-move).

Steps:
- [ ] Add `weather_zone: highland_pass` to `castle_ross`, `the_long_pass`, and `the_kirk_of_st_maelrubha` (upland); `weather_zone: glen_floor` to the remaining 11 regions. (Edit each region block in `cartography.yaml`; keep existing keys intact.)
- [ ] Verify: `cd sidequest-server && uv run python -m sidequest.cli.validate pack ../sidequest-content/genre_packs/tea_and_murder` — EXPECT no `weather_zone` errors.
- [ ] Commit:
```
cd sidequest-content && git add genre_packs/tea_and_murder/worlds/glenross/cartography.yaml && git commit -m "content(glenross): bind regions to weather zones (highland_pass/glen_floor) (spec §2 A2)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Final integration gate (run before opening PRs)

- [ ] Server: `cd sidequest-server && uv run pytest tests/genre tests/protocol tests/cli/validate tests/server/test_map_treatment_span.py tests/server/test_cartography_treatment_build.py tests/game/test_weather_region_zone_selection.py tests/server/test_weather_zone_change.py -v -n0` — EXPECT green (ignore the ~13 known WWN-content failures if any surface outside these paths).
- [ ] Server lint: `cd sidequest-server && uv run ruff check sidequest/` — EXPECT clean on touched files.
- [ ] Content: `just content-validate tea_and_murder && just content-validate pulp_noir && just content-validate road_warrior` — EXPECT pass.
- [ ] UI: `cd sidequest-ui && npx vitest run src/components/map src/components/GameBoard/widgets/__tests__/MapWidget.test.tsx src/components/GameBoard/__tests__/GameBoard-map-raster-tab.test.tsx` — EXPECT green.
- [ ] Open three PRs targeting `develop` (server, ui, content), each referencing this plan. Keep the map_emit.py / MapWidget.tsx changes scoped to the raster path (Track B contention note above).

## Follow-up / out of scope

- **A3 `generated` treatment** (deterministic seeded layout + genre-styled SVG cartography for invented-geography worlds): the `generated` enum value is reserved in `MapTreatmentConfig.treatment` and validated structurally, but the renderer is NOT built here. It is Track A milestone 3 — a separate plan. Until built, a `generated` treatment falls through to the d3-dag fallback in `MapWidget` (no raster branch match), which is acceptable (the graph still renders).
- **Real PD scan sourcing + R2 upload** for the three worlds is a Keith-owned authoring step (checklists in Tasks 9–11); the code + validator ship independently of the image bytes.
- **A↔B touchpoint** (site pins on the world map) is deferrable to B4/A-late per the spec; not in this plan.
