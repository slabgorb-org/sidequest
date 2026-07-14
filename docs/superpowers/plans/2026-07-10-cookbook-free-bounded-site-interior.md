# Cookbook-Free Bounded-Site Interior Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A bounded site (tavern/vault) materializes its whole interior from its `SiteArchetype` alone — no world `cookbook/`/`corpus/`/`themes/`/`world_register.yaml` — via a parallel `materialize_bounded()` coordinator, and a missing/failing interior fails loud-but-recoverable instead of crashing `run_movement_dispatch`.

**Architecture:** A new `materialize_bounded()` coordinator in `dungeon/materializer.py` reuses the already-cookbook-free geometry stages (`_stage_design` + `_stage_fill`), does a structural graph finalize (`attach_expansion` + `assign_depth_scores` — NOT the set-piece/trope/quest attach), derives tactical data per region (monster-free), and runs a dedicated geometry commit (`_commit_bounded`) that persists the region graph + per-room masks/tactical + archetype-derived room identities. The synthetic `ThemePalette` is built from the archetype (`build_bounded_palette`). `ensure_bounded_site_materialized` drops its `bundle`/`palette`/`pack`/`snapshot` params and calls the new coordinator; `movement.py`'s bounded branch stops loading a cookbook and wraps the crossing in a loud-but-recoverable `except`. The existing `materialize()` and its loud None-guards are untouched — zero regression risk to `beneath_sunden`.

**Tech Stack:** Python 3.14 / FastAPI, `uv`-managed. pytest (`-n auto` by default; use `-n0` for a single test). pydantic v2. PostgreSQL via `PgDungeonRepository` (behavioral tests skip without a test DB). OTEL spans via `sidequest.telemetry.spans`.

## Global Constraints

- **No Silent Fallbacks.** Every absent/invalid input fails loud. The bounded path adds no default-cookbook, no empty-palette fallback.
- **No Stubbing.** `materialize_bounded` is fully wired and consumed by `ensure_bounded_site_materialized`; that is consumed by `movement.py`. No dead shells.
- **`materialize()` is untouched.** Do NOT edit `materialize`, `_stage_curate`, `_stage_attach`, `_stage_commit`, or their guards. The bounded path is a *parallel* coordinator (ADR-157 mechanism decision).
- **Grid dims stay the 49×49 default in v1.** Per-archetype grid *sizing* is Track B4 (spec §3); the archetype's `grid_width`/`grid_height` are declared-but-not-yet-consumed. Do NOT thread archetype grid dims into `_stage_fill` (its `ROOMCORRIDOR_MIN_DIM=25` guard would reject a 15×20 tavern).
- **Zero engine-placed creatures.** The bounded path writes no `region_population`, no `setpiece_state`. `derive_region_tactical` is called with `hazard_setpieces=[]`, `creature_count=0`.
- **Determinism.** Seeds derive via `blake2b` (the house mixer), never XOR, never RNG. Same `(campaign_seed, site_id)` → identical interior.
- **Tests:** run via `uv run pytest ... -n0` (from `sidequest-server/`). Behavioral (DB) tests use `build_pg_dungeon_repo(monkeypatch, migrated_db)` and skip loudly without `SIDEQUEST_TEST_DATABASE_URL`.
- **Branch:** `feat/164-10-bounded-site-interior-path` (already cut off `develop` in `sidequest-server`). Commit per task.

---

### Task 1: `build_bounded_palette()` — archetype → synthetic ThemePalette

**Files:**
- Modify: `sidequest-server/sidequest/dungeon/materializer.py` (add function + reverse-map constant near the top-level helpers, after the `__all__` block ~line 196)
- Test: `sidequest-server/tests/dungeon/test_materialize_bounded.py` (new)

**Interfaces:**
- Consumes: `SiteArchetype` (duck-typed as `Any`: `.interior_algorithm: str`, `.archetype_id: str`), `ThemePalette`, `DungeonTheme`, `InteriorSpec`, `DepthBand`, `NarratorFlavor` (all from `sidequest.dungeon.themes`).
- Produces: `build_bounded_palette(archetype: Any) -> ThemePalette` — a single-theme palette keyed `f"bounded_{archetype.archetype_id}"`, theme eligible at all depths (`DepthBand(min=0.0, max=None)`), `interior.algorithm == archetype.interior_algorithm`, empty creature/loot/set-piece tables.

- [ ] **Step 1: Write the failing test**

Create `sidequest-server/tests/dungeon/test_materialize_bounded.py`:

```python
"""Cookbook-free bounded materialization (ADR-157, story 164-10).

Unit coverage that needs no DB: the synthetic archetype→palette build and the
room-identity helper. Behavioral (committed-graph) coverage lives in
tests/dungeon/test_bounded_site.py against a real PgDungeonRepository.
"""

from __future__ import annotations

from typing import Any


def _tavern_archetype(**over: Any) -> Any:
    from sidequest.genre.models.site_archetype import SiteArchetype

    base = dict(
        archetype_id="tavern",
        interior_algorithm="roomcorridor",
        room_count_min=3,
        room_count_max=6,
        grid_width=15,
        grid_height=20,
        cell_scale_feet=5,
        room_vocabulary=["common room", "cellar", "kitchen", "private booth"],
        feature_palette=["hearth", "long bar", "ale barrels"],
    )
    base.update(over)
    return SiteArchetype(**base)


def test_build_bounded_palette_single_theme_matches_algorithm() -> None:
    from sidequest.dungeon.materializer import build_bounded_palette

    palette = build_bounded_palette(_tavern_archetype())
    assert list(palette.themes) == ["bounded_tavern"]
    theme = palette.themes["bounded_tavern"]
    assert theme.interior.algorithm == "roomcorridor"
    assert theme.generator_class == "built"  # roomcorridor's class
    # Eligible at every depth (one theme covers the whole bounded site).
    assert palette.themes_for_depth(0.0) == [theme]
    assert palette.themes_for_depth(99.0) == [theme]
    # Cookbook-free: no creatures, no set-pieces.
    assert theme.creature_table == []
    assert theme.set_pieces == []


def test_build_bounded_palette_maps_each_algorithm_to_its_class() -> None:
    from sidequest.dungeon.materializer import build_bounded_palette

    cases = {
        "cellular": "organic",
        "depthfirst": "labyrinthine",
        "prim": "structured",
        "roomcorridor": "built",
    }
    for algorithm, generator_class in cases.items():
        palette = build_bounded_palette(
            _tavern_archetype(archetype_id=f"a_{algorithm}", interior_algorithm=algorithm)
        )
        theme = next(iter(palette.themes.values()))
        assert theme.generator_class == generator_class
        assert theme.interior.algorithm == algorithm
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/dungeon/test_materialize_bounded.py -n0 -q`
Expected: FAIL — `ImportError: cannot import name 'build_bounded_palette' from 'sidequest.dungeon.materializer'`

- [ ] **Step 3: Write minimal implementation**

In `sidequest-server/sidequest/dungeon/materializer.py`, add these imports to the existing `from sidequest.dungeon.themes import ThemePalette` line (it currently imports only `ThemePalette`):

```python
from sidequest.dungeon.themes import (
    DepthBand,
    DungeonTheme,
    InteriorSpec,
    NarratorFlavor,
    ThemePalette,
)
```

Then add, just after the `__all__ = [...]` block (~line 196), the reverse map and builder:

```python
# ADR-157: a bounded site materializes from its SiteArchetype alone. The
# archetype's interior_algorithm reverse-maps to a generator_class (the inverse
# of themes._CLASS_ALGORITHM — total over interiors.ALGORITHMS) so we can mint a
# one-theme in-memory palette with NO world themes/ tree.
_ALGORITHM_GENERATOR_CLASS = {
    "cellular": "organic",
    "depthfirst": "labyrinthine",
    "prim": "structured",
    "roomcorridor": "built",
}


def build_bounded_palette(archetype: Any) -> ThemePalette:
    """Synthesize a single-theme ThemePalette from a bounded SiteArchetype.

    Cookbook-free (ADR-157): the archetype's interior_algorithm drives the whole
    interior; the theme is eligible at every depth (a bounded site has no depth
    gradient) and carries no creature/loot/set-piece tables. The archetype's
    interior_algorithm is already validated against interiors.ALGORITHMS by the
    SiteArchetype model, so the reverse map is total — a KeyError here would be
    an unreachable authoring-validator gap, not a silent fallback.
    """
    algorithm = archetype.interior_algorithm
    generator_class = _ALGORITHM_GENERATOR_CLASS[algorithm]
    theme_id = f"bounded_{archetype.archetype_id}"
    theme = DungeonTheme(
        id=theme_id,
        display_name=archetype.archetype_id.replace("_", " ").title(),
        generator_class=generator_class,
        interior=InteriorSpec(algorithm=algorithm, params={}, braid_ratio=0.0),
        depth_band=DepthBand(min=0.0, max=None),
        narrator=NarratorFlavor(
            register="bounded-site",
            flavor=f"a bounded {archetype.archetype_id.replace('_', ' ')} interior",
        ),
    )
    return ThemePalette(themes={theme_id: theme})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/dungeon/test_materialize_bounded.py -n0 -q`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
cd sidequest-server
git add sidequest/dungeon/materializer.py tests/dungeon/test_materialize_bounded.py
git commit -m "feat(164-10): build_bounded_palette — archetype-derived synthetic ThemePalette (ADR-157)"
```

---

### Task 2: `materialize_bounded()` coordinator + `_commit_bounded()` geometry commit

**Files:**
- Modify: `sidequest-server/sidequest/dungeon/materializer.py` (add `_commit_bounded` after `_stage_commit`; add `materialize_bounded` after `materialize`; export both in `__all__`)
- Test: `sidequest-server/tests/dungeon/test_bounded_site.py` (add a behavioral test using the new coordinator directly — real Pg repo)

**Interfaces:**
- Consumes: `build_bounded_palette` (Task 1); `_stage_design`, `_stage_fill`, `derive_region_tactical`, `_tactical_into_mask_dicts`, `attach_expansion`, `assign_depth_scores`, `MaterializationRequest`, `RegionGraph`, `DungeonRepository`, `PersistError` (all in-module or already imported by materializer.py); `Expansion`.
- Produces:
  - `materialize_bounded(request: MaterializationRequest, *, graph: RegionGraph, palette: ThemePalette, dungeon_repository: DungeonRepository, archetype: Any) -> None` — runs design → fill → structural-attach → tactical → geometry-commit; NO curate, NO set-piece/trope/quest attach. `async def` (mirrors `materialize`; awaits nothing internally).
  - `_commit_bounded(request, *, graph, expansion, fill_result, tactical, room_identities, is_fresh_save, tx, span) -> None` — Seed=Expansion-0 + `commit_expansion(masks)` + `room_identity` mutations; no frontier edges, no `region_population`, no `setpiece_state`. (`room_identities` is threaded now but always `{}` until Task 3 populates it.)

- [ ] **Step 1: Write the failing test**

Append to `sidequest-server/tests/dungeon/test_bounded_site.py`:

```python
@pytest.mark.asyncio
async def test_materialize_bounded_commits_whole_graph_with_masks(
    monkeypatch: Any, migrated_db: str
) -> None:
    """materialize_bounded() commits the entrance + rooms whole, WITH per-room
    masks, using a synthetic archetype palette and NO cookbook."""
    import hashlib
    import secrets

    from sidequest.dungeon.bounded_site import _SEED_BITS, _derive_site_seed
    from sidequest.dungeon.materializer import (
        MaterializationRequest,
        build_bounded_palette,
        materialize_bounded,
    )
    from sidequest.dungeon.persistence import FrontierEdge
    from sidequest.dungeon.region_graph.model import RegionGraph, RegionNode
    from sidequest.dungeon.seed_bootstrap import select_entrance_theme_id
    from sidequest.game.sites.namespacing import site_entrance_id
    from tests.dungeon.conftest import build_pg_dungeon_repo

    _pool, repo, _sid = build_pg_dungeon_repo(monkeypatch, migrated_db)
    repo.set_campaign_seed(4242)
    seed = _derive_site_seed(base_seed=4242, site_id=_SITE_ID)
    repo.set_campaign_seed(seed, site_id=_SITE_ID)

    archetype = _tavern_archetype()
    palette = build_bounded_palette(archetype)
    entrance = site_entrance_id(_SITE_ID)
    entrance_theme = select_entrance_theme_id(palette)
    graph = RegionGraph(entrance_id=entrance)
    graph.add_node(RegionNode(id=entrance, expansion_id=0, theme=entrance_theme))
    fe = FrontierEdge(
        frontier_edge_id=f"{_SITE_ID}:seed_fe1",
        from_region_id=entrance,
        heading="in",
        spawn_depth_score=0.0,
    )
    request = MaterializationRequest.build(
        campaign_seed=seed,
        expansion_id=1,
        frontier_edge=fe,
        frontier=[fe],
        attach_region_ids=[entrance],
        heading="in",
        burst_magnitude=archetype.room_count_max,
        lookahead_breadth=0,
        site_id=_SITE_ID,
    )
    await materialize_bounded(
        request,
        graph=graph,
        palette=palette,
        dungeon_repository=repo,
        archetype=archetype,
    )

    committed = repo.load_map(entrance_id=entrance, site_id=_SITE_ID)
    assert entrance in committed.nodes
    assert archetype.room_count_min <= len(committed.nodes) <= archetype.room_count_max + 1
    # Bounded → no frontier edges left for a lookahead worker.
    assert repo.load_frontier(site_id=_SITE_ID) == []
    # Per-room masks were persisted (the TACTICAL_GRID source).
    masks = repo.load_masks(site_id=_SITE_ID)
    room_ids = [n for n in committed.nodes if n != entrance]
    assert room_ids, "expected at least one procedural room"
    assert all(rid in masks for rid in room_ids)
    # Cookbook-free: NO monster population mutations written.
    kinds = {m.kind for m in repo.load_mutations(site_id=_SITE_ID)}
    assert "region_population" not in kinds
    assert "setpiece_state" not in kinds
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/dungeon/test_bounded_site.py::test_materialize_bounded_commits_whole_graph_with_masks -n0 -q`
Expected: FAIL — `ImportError: cannot import name 'materialize_bounded'` (or skip if no test DB — in that case verify the import error by running the module import: `uv run python -c "from sidequest.dungeon.materializer import materialize_bounded"` → ImportError)

- [ ] **Step 3: Write minimal implementation**

In `materializer.py`, add `_commit_bounded` immediately AFTER `_stage_commit` (before `_frontier_edge_id`, ~line 1650) — NOTE it reuses the module globals `_live_persistence.GENERATOR_VERSION`, `_new_frontier_edges` is NOT called (bounded has no frontier):

```python
def _commit_bounded(
    request: MaterializationRequest,
    *,
    graph: RegionGraph,
    expansion: Expansion,
    fill_result: Mapping[str, RegionFill],
    tactical: dict[str, RegionTactical],
    room_identities: dict[str, dict],
    is_fresh_save: bool,
    tx: DungeonTransaction,
    span: _otel_trace.Span,
) -> None:
    """ADR-157 geometry commit for a bounded site — cookbook-free.

    Persists Seed=Expansion-0 (entrance) on a fresh site store, the room
    expansion + per-room masks (with tactical merged into the mask blob), and
    one ``room_identity`` mutation per labelled room. Writes NO frontier edges
    (a bounded site has lookahead_breadth == 0), NO ``region_population`` and NO
    ``setpiece_state`` (zero engine-placed creatures / set-pieces). Rides the
    caller's ``tx``; the coordinator's ``with transaction()`` commits/rolls back.
    """
    from sidequest.dungeon import persistence as _live_persistence

    generator_version = _live_persistence.GENERATOR_VERSION
    try:
        if is_fresh_save:
            entrance = graph.nodes.get(graph.entrance_id)
            if entrance is None:
                raise PersistError(
                    f"Seed=Expansion-0: entrance {graph.entrance_id!r} is not in "
                    f"the graph — cannot seed a fresh bounded site (No Silent Fallbacks)"
                )
            tx.commit_expansion(
                Expansion(expansion_id=0, new_nodes=[entrance], new_edges=[]),
                graph,
                generator_version=generator_version,
                site_id=request.site_id,
            )

        expansion_masks: dict[str, dict] | None = {
            rid: rf.mask.to_dict() for rid, rf in fill_result.items() if rf.mask is not None
        } or None
        if expansion_masks is not None:
            _tactical_into_mask_dicts(expansion_masks, tactical)

        tx.commit_expansion(
            expansion,
            graph,
            generator_version=generator_version,
            masks=expansion_masks,
            site_id=request.site_id,
        )

        identities_written = 0
        for node in expansion.new_nodes:
            payload = room_identities.get(node.id)
            if payload is None:
                continue
            tx.record_mutation(node.id, "room_identity", payload, site_id=request.site_id)
            identities_written += 1
    except PersistError as exc:
        span.set_attribute("error", str(exc))
        span.set_attribute("reason", f"commit_bounded: {exc}")
        raise

    span.set_attribute("expansion_id", request.expansion_id)
    span.set_attribute("seeded_entrance", is_fresh_save)
    span.set_attribute("regions_committed", len(expansion.new_nodes))
    span.set_attribute("edges_committed", len(expansion.new_edges))
    span.set_attribute("room_identities_committed", identities_written)
    span.set_attribute("frontier_edges_added", 0)
    span.set_attribute("generator_version", generator_version)
```

Then add `materialize_bounded` immediately AFTER `materialize` (end of file, ~line 2235). It reuses the geometry stages and the structural graph primitives, and threads `room_identities={}` for now (Task 3 populates it):

```python
async def materialize_bounded(
    request: MaterializationRequest,
    *,
    graph: RegionGraph,
    palette: ThemePalette,
    dungeon_repository: DungeonRepository,
    archetype: Any,
) -> None:
    """ADR-157: materialize a bounded site's WHOLE interior, cookbook-free.

    A parallel coordinator to ``materialize`` for ``extent: bounded`` sites. It
    reuses the two already-cookbook-free geometry stages (design + fill), does a
    STRUCTURAL graph finalize (``attach_expansion`` + ``assign_depth_scores`` —
    the connectivity/depth primitives, NOT the set-piece/trope/quest attach
    stage), derives monster-free tactical data, and runs the dedicated geometry
    commit. There is NO ``CookbookBundle`` in the signature: a bounded site needs
    no world ``cookbook/``/``corpus/``/``themes/``/``world_register.yaml``.

    Grid dims stay the 49×49 default (per-archetype sizing is Track B4). Zero
    engine-placed creatures — inhabitants come from the Living World.

    ``async def`` mirrors ``materialize`` (call-site symmetry); it awaits nothing
    internally.
    """
    if graph is None:
        raise ValueError(
            "materialize_bounded requires a real RegionGraph — graph=None is not "
            "valid (No Silent Fallbacks)"
        )

    with dungeon_materialize_span(
        expansion_id=request.expansion_id,
        heading=request.heading,
        burst_magnitude=request.burst_magnitude,
    ):
        with dungeon_materialize_design_span(expansion_id=request.expansion_id) as design_span:
            expansion, _report = _stage_design(
                request, graph=graph, palette=palette, span=design_span
            )

        with dungeon_materialize_fill_span(expansion_id=request.expansion_id) as fill_span:
            fill_result = _stage_fill(request, expansion=expansion, palette=palette, span=fill_span)

        # STRUCTURAL graph finalize (NOT the set-piece attach stage): add the
        # new nodes/edges to the graph and freeze depth scores so the committed
        # graph is connected + depth-scored exactly like the frontier path's,
        # minus the monster content. attach_expansion re-verifies the global
        # connected+loopful invariants (loud raise aborts the whole run).
        attach_expansion(graph, expansion)
        assign_depth_scores(graph, campaign_seed=request.campaign_seed)

        # Monster-free tactical: no set-piece hazards, no creature tokens.
        tactical: dict[str, RegionTactical] = {}
        for node in expansion.new_nodes:
            fill = fill_result.get(node.id)
            if fill is None or fill.mask is None:
                continue
            tactical[node.id] = derive_region_tactical(
                region_id=node.id,
                grid=fill.grid,
                theme_key=node.theme,
                neighbor_ids=list(graph.neighbors(node.id)),
                hazard_setpieces=[],
                creature_count=0,
            )

        # Task 3 populates room_identities from the archetype vocabulary; empty
        # here keeps the commit contract stable across the two tasks.
        room_identities: dict[str, dict] = {}

        existing_map = dungeon_repository.load_map(
            entrance_id=graph.entrance_id, site_id=request.site_id
        )
        existing_frontier = dungeon_repository.load_frontier(site_id=request.site_id)
        is_fresh_save = not existing_map.nodes and not existing_frontier

        with dungeon_repository.transaction() as tx:
            with dungeon_materialize_commit_span(expansion_id=request.expansion_id) as commit_span:
                _commit_bounded(
                    request,
                    graph=graph,
                    expansion=expansion,
                    fill_result=fill_result,
                    tactical=tactical,
                    room_identities=room_identities,
                    is_fresh_save=is_fresh_save,
                    tx=tx,
                    span=commit_span,
                )
```

Add `"materialize_bounded"` and `"build_bounded_palette"` to the `__all__` list (~line 186).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/dungeon/test_bounded_site.py::test_materialize_bounded_commits_whole_graph_with_masks -n0 -q`
Expected: PASS (or `skipped` if no test DB — then also run `uv run python -c "import sidequest.dungeon.materializer"` and expect no error, and `uv run pytest tests/dungeon/test_materialize_bounded.py -n0 -q` still PASS).

- [ ] **Step 5: Commit**

```bash
cd sidequest-server
git add sidequest/dungeon/materializer.py tests/dungeon/test_bounded_site.py
git commit -m "feat(164-10): materialize_bounded() cookbook-free coordinator + geometry commit (ADR-157)"
```

---

### Task 3: Archetype-derived room identities

**Files:**
- Modify: `sidequest-server/sidequest/dungeon/materializer.py` (add `_bounded_room_identities` helper; populate `room_identities` in `materialize_bounded`)
- Test: `sidequest-server/tests/dungeon/test_materialize_bounded.py` (add unit test for the helper) + `sidequest-server/tests/dungeon/test_bounded_site.py` (add behavioral test that mutations land)

**Interfaces:**
- Consumes: `hashlib` (already imported in materializer.py), the archetype's `.room_vocabulary: list[str]` and `.feature_palette: list[str]`, `expansion.new_nodes`.
- Produces: `_bounded_room_identities(archetype: Any, *, campaign_seed: int, site_id: str, region_ids: list[str]) -> dict[str, dict]` — one `{region_id: {"region_id", "label", "features"}}` entry per region when `room_vocabulary` is non-empty; `{}` when it is empty (a valid, label-less archetype). Deterministic (`blake2b`).

- [ ] **Step 1: Write the failing test**

Append to `sidequest-server/tests/dungeon/test_materialize_bounded.py`:

```python
def test_bounded_room_identities_are_deterministic_and_from_vocabulary() -> None:
    from sidequest.dungeon.materializer import _bounded_room_identities

    arch = _tavern_archetype()
    ids = ["gilded_boar:r1", "gilded_boar:r2", "gilded_boar:r3"]
    a = _bounded_room_identities(arch, campaign_seed=777, site_id="gilded_boar", region_ids=ids)
    b = _bounded_room_identities(arch, campaign_seed=777, site_id="gilded_boar", region_ids=ids)
    assert a == b  # deterministic
    assert set(a) == set(ids)
    for rid in ids:
        assert a[rid]["region_id"] == rid
        assert a[rid]["label"] in arch.room_vocabulary
        assert set(a[rid]["features"]).issubset(set(arch.feature_palette))
    # A different seed can change assignments (no constant fallback).
    c = _bounded_room_identities(arch, campaign_seed=778, site_id="gilded_boar", region_ids=ids)
    assert c != a or len(arch.room_vocabulary) == 1


def test_bounded_room_identities_empty_vocabulary_is_no_op() -> None:
    from sidequest.dungeon.materializer import _bounded_room_identities

    arch = _tavern_archetype(room_vocabulary=[], feature_palette=[])
    out = _bounded_room_identities(arch, campaign_seed=1, site_id="s", region_ids=["s:r1"])
    assert out == {}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/dungeon/test_materialize_bounded.py -n0 -q`
Expected: FAIL — `ImportError: cannot import name '_bounded_room_identities'`

- [ ] **Step 3: Write minimal implementation**

In `materializer.py`, add the helper just above `materialize_bounded`:

```python
def _bounded_room_identities(
    archetype: Any,
    *,
    campaign_seed: int,
    site_id: str,
    region_ids: list[str],
) -> dict[str, dict]:
    """Deterministically label each bounded room from the archetype vocabulary.

    ADR-157: the archetype's ``room_vocabulary`` gives each generated room an
    identity ("common room", "cellar") and up to two ``feature_palette`` props —
    Diamonds-and-Coal, not anonymous cells. Seeded by ``blake2b(campaign_seed,
    site_id, region_id)`` (the house mixer) so re-entry reproduces the same
    labels. An archetype with an empty ``room_vocabulary`` yields ``{}`` (a valid
    label-less site, not a silent default).
    """
    vocab = list(archetype.room_vocabulary)
    if not vocab:
        return {}
    features = list(archetype.feature_palette)
    out: dict[str, dict] = {}
    for rid in region_ids:
        digest = hashlib.blake2b(
            f"roomid|{campaign_seed}|{site_id}|{rid}".encode(), digest_size=8
        ).digest()
        mix = int.from_bytes(digest, "big")
        label = vocab[mix % len(vocab)]
        chosen: list[str] = []
        if features:
            # Deterministic, stable subset (up to 2), no RNG.
            start = mix % len(features)
            take = min(2, len(features))
            chosen = [features[(start + i) % len(features)] for i in range(take)]
        out[rid] = {"region_id": rid, "label": label, "features": chosen}
    return out
```

Then in `materialize_bounded`, replace the placeholder line:

```python
        room_identities: dict[str, dict] = {}
```

with:

```python
        room_identities = _bounded_room_identities(
            archetype,
            campaign_seed=request.campaign_seed,
            site_id=request.site_id,
            region_ids=[node.id for node in expansion.new_nodes],
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/dungeon/test_materialize_bounded.py -n0 -q`
Expected: PASS (4 tests)

- [ ] **Step 5: Add the behavioral assertion**

Append to `sidequest-server/tests/dungeon/test_bounded_site.py`:

```python
@pytest.mark.asyncio
async def test_materialize_bounded_writes_room_identities(
    monkeypatch: Any, migrated_db: str
) -> None:
    """Each procedural room gets a room_identity mutation labelled from the
    archetype's room_vocabulary (ADR-157 room identities)."""
    from sidequest.dungeon.bounded_site import _derive_site_seed
    from sidequest.dungeon.materializer import (
        MaterializationRequest,
        build_bounded_palette,
        materialize_bounded,
    )
    from sidequest.dungeon.persistence import FrontierEdge
    from sidequest.dungeon.region_graph.model import RegionGraph, RegionNode
    from sidequest.dungeon.seed_bootstrap import select_entrance_theme_id
    from sidequest.game.sites.namespacing import site_entrance_id
    from tests.dungeon.conftest import build_pg_dungeon_repo

    _pool, repo, _sid = build_pg_dungeon_repo(monkeypatch, migrated_db)
    repo.set_campaign_seed(4242)
    seed = _derive_site_seed(base_seed=4242, site_id=_SITE_ID)
    repo.set_campaign_seed(seed, site_id=_SITE_ID)

    archetype = _tavern_archetype()
    palette = build_bounded_palette(archetype)
    entrance = site_entrance_id(_SITE_ID)
    graph = RegionGraph(entrance_id=entrance)
    graph.add_node(
        RegionNode(id=entrance, expansion_id=0, theme=select_entrance_theme_id(palette))
    )
    fe = FrontierEdge(
        frontier_edge_id=f"{_SITE_ID}:seed_fe1",
        from_region_id=entrance,
        heading="in",
        spawn_depth_score=0.0,
    )
    request = MaterializationRequest.build(
        campaign_seed=seed,
        expansion_id=1,
        frontier_edge=fe,
        frontier=[fe],
        attach_region_ids=[entrance],
        heading="in",
        burst_magnitude=archetype.room_count_max,
        lookahead_breadth=0,
        site_id=_SITE_ID,
    )
    await materialize_bounded(
        request, graph=graph, palette=palette, dungeon_repository=repo, archetype=archetype
    )

    identities = [m for m in repo.load_mutations(site_id=_SITE_ID) if m.kind == "room_identity"]
    assert identities, "expected room_identity mutations"
    for m in identities:
        assert m.payload["label"] in archetype.room_vocabulary
```

Run: `cd sidequest-server && uv run pytest tests/dungeon/test_bounded_site.py::test_materialize_bounded_writes_room_identities -n0 -q`
Expected: PASS (or skip without a test DB).

- [ ] **Step 6: Commit**

```bash
cd sidequest-server
git add sidequest/dungeon/materializer.py tests/dungeon/test_materialize_bounded.py tests/dungeon/test_bounded_site.py
git commit -m "feat(164-10): archetype-derived room identities for bounded sites (ADR-157)"
```

---

### Task 4: `ensure_bounded_site_materialized` goes cookbook-free

**Files:**
- Modify: `sidequest-server/sidequest/dungeon/bounded_site.py` (change signature; build palette from archetype; call `materialize_bounded`)
- Test: `sidequest-server/tests/dungeon/test_bounded_site.py` (rewrite the cookbook-based helpers + the module/loud-fail contract tests to the new cookbook-free signature)

**Interfaces:**
- Consumes: `build_bounded_palette`, `materialize_bounded` (from materializer), `select_entrance_theme_id`, `SeamCrossingError`, existing `_derive_site_seed`/`_SEED_BITS`/`_ENTRANCE_DEPTH`, `SiteArchetype` (TYPE_CHECKING).
- Produces: `ensure_bounded_site_materialized(*, site: SiteDescriptor, archetype: SiteArchetype, dungeon_repository: DungeonRepository | None) -> None` — cookbook-free. Drops `snapshot`, `pack`, `bundle`, `palette`.

- [ ] **Step 1: Rewrite the failing tests**

Replace the top helpers and the two contract tests in `sidequest-server/tests/dungeon/test_bounded_site.py`. Delete `_real_bundle_palette_snapshot_pack` and rewrite `_materialize_site`, `test_module_exposes_ensure_bounded_site_materialized`, `test_missing_store_fails_loud`, `test_idempotent_second_entry_skips`, and `test_missing_base_seed_is_minted_not_defaulted_to_zero` to the cookbook-free signature. New helper + contract tests:

```python
async def _materialize_site(repo: Any, *, base_seed: int = 12345) -> None:
    from sidequest.dungeon.bounded_site import ensure_bounded_site_materialized

    repo.set_campaign_seed(base_seed)
    await ensure_bounded_site_materialized(
        site=_tavern_descriptor(),
        archetype=_tavern_archetype(),
        dungeon_repository=repo,
    )


def test_module_exposes_ensure_bounded_site_materialized() -> None:
    """Cookbook-free (ADR-157): the entry point is an async function whose ONLY
    keyword params are site/archetype/dungeon_repository — no bundle/palette."""
    from sidequest.dungeon.bounded_site import ensure_bounded_site_materialized

    assert inspect.iscoroutinefunction(ensure_bounded_site_materialized)
    params = inspect.signature(ensure_bounded_site_materialized).parameters
    assert set(params) == {"site", "archetype", "dungeon_repository"}
    for name in params:
        assert params[name].kind is inspect.Parameter.KEYWORD_ONLY


@pytest.mark.asyncio
async def test_missing_store_fails_loud() -> None:
    from sidequest.dungeon.bounded_site import ensure_bounded_site_materialized
    from sidequest.game.seams.base import SeamCrossingError

    with pytest.raises(SeamCrossingError):
        await ensure_bounded_site_materialized(
            site=_tavern_descriptor(),
            archetype=_tavern_archetype(),
            dungeon_repository=None,
        )
```

Update `test_idempotent_second_entry_skips` and `test_missing_base_seed_is_minted_not_defaulted_to_zero` to call `ensure_bounded_site_materialized` with only `site=/archetype=/dungeon_repository=` (drop the `bundle/palette/snapshot/pack` kwargs). `_tavern_archetype` gains the `room_vocabulary`/`feature_palette` fields shown in Task 1's fixture (copy them in). The `_tavern_descriptor` and behavioral whole/deterministic/commit-span tests stay as-is but their `_materialize_site` now uses the cookbook-free helper.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd sidequest-server && uv run pytest tests/dungeon/test_bounded_site.py::test_module_exposes_ensure_bounded_site_materialized -n0 -q`
Expected: FAIL — the current signature still has `bundle`/`palette`/`snapshot`/`pack`, so `set(params) == {...}` fails.

- [ ] **Step 3: Rewrite the implementation**

In `sidequest-server/sidequest/dungeon/bounded_site.py`:

Replace the imports block's `from sidequest.dungeon.materializer import MaterializationRequest, materialize` with:

```python
from sidequest.dungeon.materializer import (
    MaterializationRequest,
    build_bounded_palette,
    materialize_bounded,
)
```

Replace the whole `ensure_bounded_site_materialized` function signature + body's cookbook-dependent parts. New signature and body:

```python
async def ensure_bounded_site_materialized(
    *,
    site: SiteDescriptor,
    archetype: SiteArchetype,
    dungeon_repository: DungeonRepository | None,
) -> None:
    """Materialize ``site`` whole on first entry; a no-op on re-entry.

    Cookbook-free (ADR-157): the interior is built from ``archetype`` alone via a
    synthetic in-memory palette — no world ``cookbook/``/``corpus/``/``themes/``.
    Idempotent (emits ``site.materialize.skip`` if already committed); fail-loud
    on a missing store (``SeamCrossingError``, No Silent Fallbacks).
    """
    if dungeon_repository is None:
        raise SeamCrossingError(reason="no_site_store", surface=f"{site.name} cannot be opened.")

    entrance = site_entrance_id(site.site_id)
    existing = dungeon_repository.load_map(entrance_id=entrance, site_id=site.site_id)
    if entrance in existing.nodes:
        with site_materialize_skip_span(site_id=site.site_id, archetype=site.archetype):
            pass
        return

    seed = dungeon_repository.get_campaign_seed(site_id=site.site_id)
    if seed is None:
        base = dungeon_repository.get_campaign_seed()
        if base is None:
            base = secrets.randbits(_SEED_BITS)
            dungeon_repository.set_campaign_seed(base)
        seed = _derive_site_seed(base_seed=base, site_id=site.site_id)
        dungeon_repository.set_campaign_seed(seed, site_id=site.site_id)

    with site_materialize_begin_span(site_id=site.site_id, archetype=site.archetype) as span:
        span.set_attribute("seed", seed)
        span.set_attribute("room_count_max", archetype.room_count_max)

    palette = build_bounded_palette(archetype)
    entrance_theme = select_entrance_theme_id(palette)
    seed_graph = RegionGraph(entrance_id=entrance)
    seed_graph.add_node(RegionNode(id=entrance, expansion_id=0, theme=entrance_theme))

    fe = FrontierEdge(
        frontier_edge_id=f"{site.site_id}:seed_fe1",
        from_region_id=entrance,
        heading="in",
        spawn_depth_score=_ENTRANCE_DEPTH,
    )
    request = MaterializationRequest.build(
        campaign_seed=seed,
        expansion_id=1,
        frontier_edge=fe,
        frontier=[fe],
        attach_region_ids=[entrance],
        heading="in",
        burst_magnitude=archetype.room_count_max,
        lookahead_breadth=0,
        site_id=site.site_id,
    )
    await materialize_bounded(
        request,
        graph=seed_graph,
        palette=palette,
        dungeon_repository=dungeon_repository,
        archetype=archetype,
    )

    committed = dungeon_repository.load_map(entrance_id=entrance, site_id=site.site_id)
    with site_materialize_commit_span(site_id=site.site_id, archetype=site.archetype) as span:
        span.set_attribute("node_count", len(committed.nodes))
```

Remove the now-unused imports: `select_entrance_theme_id` is still used (keep it); the `Any`-typed `snapshot`/`pack`/`bundle`/`palette` params are gone. Delete the `from typing import TYPE_CHECKING, Any` `Any` if no longer referenced elsewhere in the file (keep `TYPE_CHECKING`). Keep `DungeonRepository` under TYPE_CHECKING.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd sidequest-server && uv run pytest tests/dungeon/test_bounded_site.py -n0 -q`
Expected: PASS (DB tests skip without a test DB; the no-DB contract tests PASS).

- [ ] **Step 5: Commit**

```bash
cd sidequest-server
git add sidequest/dungeon/bounded_site.py tests/dungeon/test_bounded_site.py
git commit -m "feat(164-10): ensure_bounded_site_materialized goes cookbook-free (ADR-157)"
```

---

### Task 5: `movement.py` bounded branch — cookbook-free routing + loud-but-recoverable

**Files:**
- Modify: `sidequest-server/sidequest/agents/subsystems/movement.py` (bounded branch ~535-613; remove dead imports)
- Test: `sidequest-server/tests/agents/test_movement_bounded_recover.py` (new)

**Interfaces:**
- Consumes: `ensure_bounded_site_materialized` (new cookbook-free signature), `_unresolved`, `site_enter_unresolved_span`, `logger`, `SeamCrossingError`.
- Produces: bounded branch that (a) resolves the archetype, (b) calls `ensure_bounded_site_materialized(site=, archetype=, dungeon_repository=dungeon_store)` with NO cookbook/world-dir read, (c) catches `SeamCrossingError` (specific surface) AND `Exception` (loud-but-recoverable) → recoverable `_unresolved`, never re-raising out of `run_movement_dispatch`.

- [ ] **Step 1: Write the failing test**

Create `sidequest-server/tests/agents/test_movement_bounded_recover.py`:

```python
"""movement.py bounded branch: cookbook-free routing + loud-but-recoverable
(ADR-157, story 164-10). A materialize failure must NOT propagate out of
run_movement_dispatch — the dispatch contract is recoverable failures only.
"""

from __future__ import annotations

import inspect


def test_bounded_branch_no_longer_imports_cookbook_loader() -> None:
    """The bounded path is cookbook-free: movement.py must not import
    load_cookbook / load_theme_palette / GenreLoadError anymore."""
    import sidequest.agents.subsystems.movement as mv

    for gone in ("load_cookbook", "load_theme_palette", "GenreLoadError"):
        assert not hasattr(mv, gone), f"{gone} should be removed from movement.py"


def test_ensure_bounded_call_is_cookbook_free() -> None:
    """The dispatch calls ensure_bounded_site_materialized with only
    site/archetype/dungeon_repository — no bundle/palette kwargs."""
    from sidequest.dungeon.bounded_site import ensure_bounded_site_materialized

    params = set(inspect.signature(ensure_bounded_site_materialized).parameters)
    assert params == {"site", "archetype", "dungeon_repository"}
```

(These two are the wiring tripwires that need no DB/session scaffold. The behavioral crash-recovery is covered by the reflection test plus the manual verify in Step 6.)

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/agents/test_movement_bounded_recover.py -n0 -q`
Expected: FAIL — `load_cookbook`/`load_theme_palette`/`GenreLoadError` are still module attributes of movement.py.

- [ ] **Step 3: Rewrite the bounded branch + remove dead imports**

In `sidequest-server/sidequest/agents/subsystems/movement.py`:

Remove these three import lines (37, 38, 45):

```python
from sidequest.dungeon.themes import load_theme_palette
from sidequest.game.cookbook.loader import load_cookbook
```
```python
from sidequest.genre.error import GenreLoadError
```

Replace the bounded branch body (the `if site.extent == "bounded":` block, ~lines 535-613) with this cookbook-free, loud-but-recoverable version:

```python
            if site.extent == "bounded":
                archetype = pack.site_archetypes.get(site.archetype) if pack is not None else None
                if archetype is None:
                    return _unresolved(
                        snapshot=snapshot,
                        player_name=player_name,
                        reason="unknown_archetype",
                        from_region=from_region,
                        direction=direction,
                        exit_descriptor=site_descriptor,
                        available=[],
                        surface=f"{site.name} cannot be opened.",
                    )
                try:
                    # Cookbook-free (ADR-157): a bounded site materializes from
                    # its archetype ALONE — no load_cookbook / load_theme_palette,
                    # no world-dir filesystem read. This removes the megadungeon
                    # FileNotFoundError source entirely for bounded sites.
                    await ensure_bounded_site_materialized(
                        site=site,
                        archetype=archetype,
                        dungeon_repository=dungeon_store,
                    )
                except SeamCrossingError as err:
                    with site_enter_unresolved_span(
                        pc_name=player_name,
                        from_region=from_region,
                        reason=err.reason,
                        descriptor=site_descriptor,
                    ):
                        pass
                    return _unresolved(
                        snapshot=snapshot,
                        player_name=player_name,
                        reason=err.reason,
                        from_region=from_region,
                        direction=direction,
                        exit_descriptor=site_descriptor,
                        available=[],
                        surface=err.surface,
                    )
                except Exception as err:
                    # LOUD-but-recoverable (ADR-157): run_movement_dispatch must
                    # NEVER re-raise — a site-materialization failure (a content
                    # gap, a malformed archetype, a PersistError) is surfaced as a
                    # recoverable movement.unresolved + an ERROR log + a
                    # site.enter_unresolved span (the lie-detector sees it), not a
                    # crash that takes down the whole turn.
                    logger.error(
                        "bounded site %s materialization failed: %s",
                        site.site_id,
                        err,
                        exc_info=True,
                    )
                    with site_enter_unresolved_span(
                        pc_name=player_name,
                        from_region=from_region,
                        reason="site_materialize_failed",
                        descriptor=site_descriptor,
                    ):
                        pass
                    return _unresolved(
                        snapshot=snapshot,
                        player_name=player_name,
                        reason="site_materialize_failed",
                        from_region=from_region,
                        direction=direction,
                        exit_descriptor=site_descriptor,
                        available=[],
                        surface=f"{site.name} isn't ready yet.",
                    )
```

(The CWE-22 `world_dir` block is deleted along with the cookbook loads — a bounded site reads no files, so there is no path-traversal surface to guard. `snapshot`/`palette`/`pack` are no longer threaded into `ensure_bounded_site_materialized`; `pack` is still used above to resolve `archetype`.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/agents/test_movement_bounded_recover.py -n0 -q`
Expected: PASS (2 tests)

- [ ] **Step 5: Run the full dungeon + movement suites (regression)**

Run: `cd sidequest-server && uv run pytest tests/dungeon/ tests/agents/test_movement_bounded_recover.py -q`
Expected: PASS (bounded DB tests skip without a DB; nothing else regresses). Also lint: `uv run ruff check sidequest/dungeon/materializer.py sidequest/dungeon/bounded_site.py sidequest/agents/subsystems/movement.py` → clean (no unused-import warnings for the removed loaders).

- [ ] **Step 6: Manual end-to-end verify (loud-but-recoverable)**

Confirm the crash is gone with a focused REPL check (no DB needed — a `None` store drives the SeamCrossingError recoverable path; a raising store double drives the `except Exception` path). Run:

```bash
cd sidequest-server && uv run python - <<'PY'
import asyncio, inspect
from sidequest.dungeon.bounded_site import ensure_bounded_site_materialized
# Signature is cookbook-free:
print("params:", set(inspect.signature(ensure_bounded_site_materialized).parameters))
# Missing store → SeamCrossingError (recoverable, caught by movement.py):
from sidequest.game.seams.base import SeamCrossingError
from sidequest.game.sites.models import SiteDescriptor
from sidequest.genre.models.site_archetype import SiteArchetype
site = SiteDescriptor(site_id="s", name="S", archetype="tavern", attached_to="x", extent="bounded")
arch = SiteArchetype(archetype_id="tavern", interior_algorithm="roomcorridor",
                     room_count_min=3, room_count_max=6, grid_width=15, grid_height=20)
try:
    asyncio.run(ensure_bounded_site_materialized(site=site, archetype=arch, dungeon_repository=None))
except SeamCrossingError as e:
    print("OK recoverable SeamCrossingError:", e.reason)
PY
```
Expected: prints `params: {'site', 'archetype', 'dungeon_repository'}` and `OK recoverable SeamCrossingError: no_site_store`.

- [ ] **Step 7: Commit**

```bash
cd sidequest-server
git add sidequest/agents/subsystems/movement.py tests/agents/test_movement_bounded_recover.py
git commit -m "fix(164-10): bounded enter is cookbook-free + loud-but-recoverable, no dispatch re-raise (ADR-157)"
```

---

## Self-Review

**Spec coverage (ADR-157 + three-tier spec §1/§5):**
- Cookbook-free bounded coordinator → Task 2 (`materialize_bounded`).
- Archetype is the whole content source → Task 1 (`build_bounded_palette`) + Task 3 (room identities).
- Zero engine-placed creatures → Task 2 (`hazard_setpieces=[]`, `creature_count=0`; no `region_population`/`setpiece_state`).
- `materialize()` untouched → no task edits it; Task 2 adds parallel functions only.
- movement.py stops calling `load_cookbook` + loud-but-recoverable → Task 5.
- Determinism (blake2b) → Task 3 helper + reused seed pipeline.
- Grid dims deferred to B4 → Global Constraints (do not thread archetype dims into `_stage_fill`).

**Placeholder scan:** none — every step has full code or exact commands.

**Type consistency:** `materialize_bounded(request, *, graph, palette, dungeon_repository, archetype)` and `_commit_bounded(...)` and `_bounded_room_identities(...)` signatures are identical across the task that defines them and the tasks that call them. `ensure_bounded_site_materialized(*, site, archetype, dungeon_repository)` is consistent between Task 4 (definition) and Task 5 (caller) and the tests.

**Wiring:** `materialize_bounded` is consumed by `ensure_bounded_site_materialized` (Task 4), which is consumed by `movement.py` (Task 5). Task 5's reflection tests are the wiring tripwires (module-attribute + signature), per CLAUDE.md's "no source-text wiring tests" rule they interrogate runtime types, not source strings. The DB behavioral tests prove the committed-graph outcome.

**Out of scope (re-planned into 164-7):** authoring the real `site_archetypes.yaml` (tavern/vault) as pack content; `SITE_MAP`/`TACTICAL_GRID` emission consuming the `room_identity` mutations; the `tavern_enter_trace` span-jsonl e2e scenario; per-archetype grid sizing (Track B4).
