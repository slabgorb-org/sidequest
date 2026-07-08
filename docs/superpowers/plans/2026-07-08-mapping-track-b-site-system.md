# Track B: Site System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generalize the SideQuest procedural-dungeon machinery (today hard-fenced to `beneath_sunden`) into a first-class **Site** system: a named sub-location (tavern, vault, cave warren) attached to a world cartography node, entered/exited through symmetric seam resolvers, materialized whole (bounded) or lookahead-expanded (frontier), and projected to the UI as its own map scene. Scope is **milestones B1 (seam/site contract refactor + Sünden migration) and B2 (archetype catalog + bounded materialization with tavern + vault end-to-end)**. B3 (minted-on-the-fly sites) and B4 (per-archetype visual polish) are OUT OF SCOPE — see Follow-ups.

**Architecture:** A new `game/sites/` package holds a `SiteRegistry` built from a world's authored `sites:` declarations (a new `CartographyConfig.sites` field). The intent router emits **site targets** (`enter_site(descriptor)` / `exit_site`) instead of the `direction=deeper` vocabulary; `movement.py`'s five-rung inlined seam ladder collapses into `SiteRegistry` descriptor-resolution × symmetric `enter_site`/`exit_site` seam resolvers. Per-connection **scene context** (`world | site:<site_id>`) replaces the binary `surface|deep` map arbitration; the `DUNGEON_MAP` protocol message becomes `SITE_MAP` in one cutover with no alias. Per-site graph storage is keyed `(session_id, site_id)`; node ids are site-namespaced (`gilded_boar:r2`). Bounded sites materialize their whole graph + grids in one transaction from a per-genre `site_archetypes.yaml` catalog.

**Tech Stack:** Python 3.12 / FastAPI / pydantic v2 / psycopg3 + `psycopg_pool` / Alembic (server); React + TypeScript + Vite + vitest (ui); YAML genre packs (content); OpenTelemetry spans mirrored to `turn_telemetry` via `publish_event` (observability). Deterministic generation via `blake2b(campaign_seed, site_id)`.

## Global Constraints

- **uv-managed server.** Run tests with `cd sidequest-server && uv run pytest <path> -v`. Lint `uv run ruff check <touched paths>`; format only branch-touched files (`uv run ruff format <paths>` — a bare `ruff format .` reformats ~167 files and is forbidden). Type check `uv run pyright <paths>`.
- **UI.** `cd sidequest-ui && npx vitest run <path>`; `npm run lint`.
- **Branching.** Branch off `develop` in each subrepo. **Branch creation must be its own Bash call before any commit** — a pf PreToolUse hook rejects `git commit` while on `develop`/`main` even when `checkout -b` precedes it in the same compound command. Subrepo PRs target `develop`. This plan spans three subrepos (server, ui, content); each keeps its own feature branch.
- **TDD, every task.** Failing test WITH complete code → run and confirm the expected failure → minimal implementation WITH complete code → run to pass → commit. No task skips the RED step.
- **Wiring test, every suite.** At least one test must prove production reachability (imported, called, reachable from a real dispatch path). **Never grep production source as a wiring assertion** (`handler.read_text()` is banned). Prefer: OTEL span assertions, fixture-driven behavior tests, or registry/dispatch enumeration. Reflection-based dataclass/field checks (`inspect`) are the one allowed static form.
- **No content invariants in unit tests.** "every world has X", "file deleted", "all packs load" belong in the pack validator, never pytest. Pytest tests CODE with synthetic fixtures.
- **Materializer tests MUST monkeypatch `_resolve_world_dir`** to a tmp dir (`sidequest/dungeon/materializer.py:1991`). A `materialize()` test with a real `genre_slug` writes rooms into the REAL content pack via `_resolve_world_dir` (gitignored → git stays clean → later same-session `load_genre_pack` dies with `GenreLoadError`). Use a durable conftest fixture.
- **E2E/handler tests that are combat-adjacent** must stub the intent-router pass (post-ADR-113 the router pass makes handler tests flaky).
- **Single-writer invariant.** The narrator is denied location writes wherever the engine owns navigation. Extend the existing `/current_region` denial (`apply_world_patch.py:182`) and same-turn seam guard (`narration_apply.py:259`) to site scenes.
- **Every site/seam span reaches `turn_telemetry` via `publish_event`, not `Span.open` alone.** `Span.open` reaches Jaeger + the live GM dashboard but NOT the Postgres `turn_telemetry` sink. The model is `movement.py`'s `_mirror_movement_span_to_sink` (`sidequest/telemetry/spans/movement.py:151`): register a `SPAN_ROUTES[...]` route, then call `publish_event(route.event_type, route.extract(span), component=route.component)` after the span closes. `publish_event` signature: `sidequest/telemetry/watcher_hub.py:712`.
- **Bounded materialization = ONE transaction.** No partially-committed site may exist. Deterministic: `blake2b(campaign_seed, site_id)`. No `Date.now`/`random` in tests.
- **No silent fallbacks.** A missing store, unresolvable `enter_site`, or dangling site owner fails loud (`SeamCrossingError` stays recoverable with a caller-owned failure span; unresolved enter emits `site.enter_unresolved`).
- **Known pre-existing failures (do not attribute to this work):** ~13 server tests fail vs content `develop` (WWN migration + seaboard promotion); OTEL span-count tests deadlock under `-n auto` (run affected files with `-n0`); `test_message_type_complete_count` is a stale count test that THIS plan legitimately updates (Task 8).

## Design overview (read before starting)

**Scene context.** A connection is in exactly one scene: `world` (on cartography) or `site:<site_id>` (inside a site, `pc_region` is a site-namespaced node). Scene context is derived per-connection from `pc_region` + the `SiteRegistry`. It replaces `_descent_phase`'s binary `"n/a"|"surface"|"deep"` (`map_emit.py:928`) and decides map emission.

**Site model & three origins.** A `SiteDescriptor` carries `site_id`, `name`, `archetype`, `attached_to` (owning cartography region), `extent` (`bounded`|`frontier`). Origins: *authored* (declared in world YAML — B1/B2), *minted* (runtime Yes-And — **B3, out of scope**), *ephemeral* (single-room combat — Track C, out of scope). B1/B2 handle authored only.

**Namespacing.** Site node ids are `{site_id}:entrance`, `{site_id}:r{n}`, `{site_id}:exp{NNN}.r{n}`. This kills the global `exp001.r0` collision so two sites in one session never clash. `is_procedural_region_id` becomes site-aware.

**Router emits site targets.** `movement` gains an `action` param: `enter_site` (with `site_descriptor` free text) / `exit_site` / omitted (in-scene navigation via existing `direction`/`exit_descriptor`). The engine resolves `site_descriptor` against the current node's site list — dissolving BOTH sticky-descent (no more `direction=="deeper"` exact-match requirement, `movement.py:440`) AND the multi-seam ambiguity refusal (`seam_route_via_adjacency`/`surface_owner_for_entrance` return `None` on >1 seam — sites are distinguishable by name).

**Extent.** `bounded` (default): whole site graph + grids materialize in ONE committed transaction at first entry; no frontier worker; `no_candidate_edges` is structurally impossible. `frontier`: keeps ADR-106 edge-expansion + lookahead. **Sünden's deep becomes the first `frontier` site** (`site_id: frontier`, `attached_to: the_dropmouth`).

### Naming decisions (avoid collisions — verified in codebase)
- **Archetype catalog file = `site_archetypes.yaml`**, NOT `archetypes.yaml`. `archetypes.yaml` is already a required world-tier file holding `NpcArchetype` chargen data (`pack_schema.yaml:112`; loader `loader.py:2281`); `sidequest/genre/archetype/` is the chargen-archetype package. The site catalog needs a distinct filename/model to avoid clobbering that surface.
- **New protocol message = `SITE_MAP`** (replaces `DUNGEON_MAP`, one cutover, no alias).
- **Seam kinds = `enter_site` / `exit_site`** (replace `deep_descent` / `surface_ascent`).

### Risk sequencing (Sünden must stay green at every merge point)
- **Tasks 1–5 are pure/additive** — Sünden behavior is untouched; new code is registered/parsed but not yet on the hot path.
- **Task 6 is THE RISKY MOVEMENT CUTOVER** — the `movement.py` ladder is replaced AND Sünden's deep is declared as a frontier site in the same change. Guarded by Task 3's characterization tests.
- **Task 7 is THE RISKY MAP-ARBITRATION CUTOVER** — scene context replaces `_descent_phase`; the beneath_sunden fence (`region_projection.applies_to`) is dissolved.
- **Task 8 is THE RISKY PROTOCOL CUTOVER** — `DUNGEON_MAP → SITE_MAP`.
- **Task 9 is THE RISKY UI CUTOVER** — SITE_MAP handling + scene-keyed `mapData` + breadcrumb (the 158-36 fix).
- Tasks 10–15 are B2 (archetypes, bounded materialization, single-writer, content, scenario) — additive on top of a green B1.

### Track A coordination (surgical scoping)
Two files are ALSO touched by Track A (main-map treatments). Keep Track B changes scoped to the site/scene paths only:
- `sidequest/server/websocket_handlers/map_emit.py` — Track A adds a `treatment` block to `_maybe_emit_cartography_map` (`:1143`). **Track B only touches** `_descent_phase` (`:928`), `_maybe_emit_dungeon_map` (`:1034`), `_build_dungeon_map_payload` (`:966`), `_load_dungeon_map_context` (`:887`), `_maybe_build_runtime_cavern_payload` (`:113`). Do NOT modify the cartography `treatment` emission.
- `sidequest-ui/src/components/GameBoard/widgets/MapWidget.tsx` — Track A adds `RasterMap`/treatment routing. **Track B only touches** the site-scene branch (Automapper routing, `:248`) and adds the breadcrumb. Leave the orrery + cartography branches alone.

---

## Task 1: SiteDescriptor + SiteRegistry model + `CartographyConfig.sites` (pure/additive)

Foundational, pure model. Defines the site contract and namespacing. No behavior change — every existing world has an empty `sites` list.

**Files:**
- Create `sidequest-server/sidequest/game/sites/__init__.py`
- Create `sidequest-server/sidequest/game/sites/models.py` (SiteDecl, SiteDescriptor)
- Create `sidequest-server/sidequest/game/sites/registry.py` (SiteRegistry)
- Create `sidequest-server/sidequest/game/sites/namespacing.py` (id helpers)
- Modify `sidequest-server/sidequest/genre/models/world.py` — add `SiteDecl` import + `CartographyConfig.sites` field (after `:297` `routes`)
- Create `sidequest-server/tests/game/sites/__init__.py` + `tests/game/sites/test_site_registry.py`

**Interfaces:**
- Consumes: `CartographyConfig` (`sidequest/genre/models/world.py:267`, `model_config = {"extra": "ignore"}`), `Region.adjacent: list[str]` (`world.py:199`).
- Produces (consumed by Tasks 4, 6, 7): `SiteRegistry.from_cartography(cart) -> SiteRegistry`; `SiteRegistry.sites_for_node(region_id: str) -> list[SiteDescriptor]` (owner + adjacency-reachable); `SiteRegistry.resolve_descriptor(region_id, descriptor) -> tuple[SiteDescriptor | None, bool]` (site, ambiguous); `SiteRegistry.by_id(site_id) -> SiteDescriptor | None`; `SiteRegistry.site_owning_node(node_id) -> SiteDescriptor | None`. Namespacing: `site_entrance_id(site_id) -> str`, `is_site_node_id(node_id) -> bool`, `site_id_of(node_id) -> str | None`.

**Steps:**

- [ ] Write the failing test `tests/game/sites/test_site_registry.py`:
  ```python
  """SiteRegistry + namespacing unit tests (Track B, Task 1)."""
  from __future__ import annotations

  from sidequest.game.sites import (
      SiteDescriptor,
      SiteRegistry,
      is_site_node_id,
      site_entrance_id,
      site_id_of,
  )
  from sidequest.genre.models.world import CartographyConfig


  def _cart() -> CartographyConfig:
      return CartographyConfig.model_validate(
          {
              "navigation_mode": "region",
              "regions": {
                  "ropefoot": {"name": "Ropefoot Camp", "adjacent": ["the_dropmouth"]},
                  "the_dropmouth": {"name": "The Dropmouth", "adjacent": ["ropefoot"]},
                  "square": {"name": "Village Square", "adjacent": []},
              },
              "sites": [
                  {"site_id": "frontier", "name": "The Deep", "archetype": "megadungeon",
                   "attached_to": "the_dropmouth", "extent": "frontier"},
                  {"site_id": "gilded_boar", "name": "The Gilded Boar", "archetype": "tavern",
                   "attached_to": "square", "extent": "bounded"},
              ],
          }
      )

  def test_sites_field_parses_and_defaults_empty() -> None:
      assert CartographyConfig().sites == []
      assert len(_cart().sites) == 2

  def test_sites_for_node_includes_owner_and_adjacent() -> None:
      reg = SiteRegistry.from_cartography(_cart())
      # the_dropmouth OWNS the frontier site
      assert [s.site_id for s in reg.sites_for_node("the_dropmouth")] == ["frontier"]
      # ropefoot is ADJACENT to the owner -> the deep is enterable from the camp
      assert [s.site_id for s in reg.sites_for_node("ropefoot")] == ["frontier"]
      # square owns the tavern
      assert [s.site_id for s in reg.sites_for_node("square")] == ["gilded_boar"]

  def test_resolve_descriptor_by_name_disambiguates() -> None:
      reg = SiteRegistry.from_cartography(_cart())
      site, ambiguous = reg.resolve_descriptor("square", "the gilded boar")
      assert site is not None and site.site_id == "gilded_boar" and not ambiguous
      # unmatched descriptor -> (None, not-ambiguous)
      miss, amb = reg.resolve_descriptor("square", "the moon")
      assert miss is None and not amb

  def test_site_owning_node_maps_namespaced_id_back() -> None:
      reg = SiteRegistry.from_cartography(_cart())
      owner = reg.site_owning_node("gilded_boar:r2")
      assert owner is not None and owner.site_id == "gilded_boar"
      assert reg.site_owning_node("the_dropmouth") is None

  def test_namespacing_helpers() -> None:
      assert site_entrance_id("gilded_boar") == "gilded_boar:entrance"
      assert is_site_node_id("gilded_boar:r2") is True
      assert is_site_node_id("the_dropmouth") is False
      assert site_id_of("gilded_boar:entrance") == "gilded_boar"
      assert site_id_of("the_dropmouth") is None
  ```
- [ ] Run: `cd sidequest-server && uv run pytest tests/game/sites/test_site_registry.py -v` — expect `ModuleNotFoundError: sidequest.game.sites` (and `CartographyConfig().sites` AttributeError).
- [ ] Create `sidequest/game/sites/namespacing.py`:
  ```python
  """Site node-id namespacing. Site node ids are ``{site_id}:{suffix}``."""
  from __future__ import annotations

  import re

  _SITE_NODE_RE = re.compile(r"^(?P<site>[a-z0-9_]+):(?P<suffix>[a-z0-9_.]+)$")


  def site_entrance_id(site_id: str) -> str:
      """The per-site entrance anchor (replaces the global ENTRANCE_ID)."""
      return f"{site_id}:entrance"


  def is_site_node_id(node_id: str) -> bool:
      """True iff ``node_id`` is site-namespaced (``gilded_boar:r2``)."""
      return bool(node_id) and _SITE_NODE_RE.match(node_id) is not None


  def site_id_of(node_id: str) -> str | None:
      """The owning site id of a namespaced node, or None for a bare id."""
      m = _SITE_NODE_RE.match(node_id or "")
      return m.group("site") if m else None
  ```
- [ ] Create `sidequest/game/sites/models.py`:
  ```python
  """Site declaration (authored YAML) and its resolved descriptor."""
  from __future__ import annotations

  from dataclasses import dataclass
  from typing import Literal

  from pydantic import BaseModel, Field

  from sidequest.game.sites.namespacing import site_entrance_id

  SiteExtent = Literal["bounded", "frontier"]


  class SiteDecl(BaseModel):
      """One authored site on a world node (cartography ``sites:`` entry).

      ``seed`` is NEVER authored — it is derived ``blake2b(campaign_seed,
      site_id)`` at materialization (Task 12). ``model_config`` allows extra
      fields so future per-archetype flavor doesn't fail load.
      """

      model_config = {"extra": "allow"}

      site_id: str
      name: str
      archetype: str
      attached_to: str
      extent: SiteExtent = "bounded"


  @dataclass(frozen=True)
  class SiteDescriptor:
      """Resolved, runtime-facing view of a declared site."""

      site_id: str
      name: str
      archetype: str
      attached_to: str
      extent: SiteExtent

      @property
      def entrance_node_id(self) -> str:
          return site_entrance_id(self.site_id)

      @classmethod
      def from_decl(cls, decl: SiteDecl) -> SiteDescriptor:
          return cls(
              site_id=decl.site_id,
              name=decl.name,
              archetype=decl.archetype,
              attached_to=decl.attached_to,
              extent=decl.extent,
          )
  ```
- [ ] Create `sidequest/game/sites/registry.py`:
  ```python
  """SiteRegistry — indexes a world's authored sites for the movement/seam
  and map-emit layers. Built once per dispatch from the active cartography."""
  from __future__ import annotations

  from typing import TYPE_CHECKING

  from sidequest.game.sites.models import SiteDescriptor
  from sidequest.game.sites.namespacing import site_id_of

  if TYPE_CHECKING:
      from sidequest.genre.models.world import CartographyConfig


  class SiteRegistry:
      """Read-only index of ``SiteDescriptor`` by owning node and by id."""

      def __init__(self, sites: list[SiteDescriptor], adjacency: dict[str, list[str]]) -> None:
          self._sites = sites
          self._by_id = {s.site_id: s for s in sites}
          self._by_owner: dict[str, list[SiteDescriptor]] = {}
          for s in sites:
              self._by_owner.setdefault(s.attached_to, []).append(s)
          self._adjacency = adjacency

      @classmethod
      def from_cartography(cls, cart: CartographyConfig | None) -> SiteRegistry:
          if cart is None:
              return cls([], {})
          sites = [SiteDescriptor.from_decl(d) for d in getattr(cart, "sites", []) or []]
          adjacency = {
              rid: list(getattr(region, "adjacent", []) or [])
              for rid, region in (getattr(cart, "regions", {}) or {}).items()
          }
          return cls(sites, adjacency)

      def by_id(self, site_id: str) -> SiteDescriptor | None:
          return self._by_id.get(site_id)

      def sites_for_node(self, region_id: str) -> list[SiteDescriptor]:
          """Sites the PC can enter from ``region_id``: those OWNED by this node
          plus those owned by an ADJACENT node (the "down the rope at the camp"
          one-action reach). Owner-first, de-duplicated, order-stable."""
          seen: set[str] = set()
          out: list[SiteDescriptor] = []
          for s in self._by_owner.get(region_id, []):
              if s.site_id not in seen:
                  seen.add(s.site_id)
                  out.append(s)
          for adj in self._adjacency.get(region_id, []):
              for s in self._by_owner.get(adj, []):
                  if s.site_id not in seen:
                      seen.add(s.site_id)
                      out.append(s)
          return out

      def resolve_descriptor(
          self, region_id: str, descriptor: str
      ) -> tuple[SiteDescriptor | None, bool]:
          """Match a free-text descriptor against the node's enterable sites.

          Returns ``(site, ambiguous)``. Unlike the retired multi-seam refusal,
          a NAMED descriptor disambiguates: exact/substring match on name or id.
          Sole enterable site with an empty descriptor still resolves (there is
          only one way in). Ambiguous only when a descriptor matches >1 site."""
          candidates = self.sites_for_node(region_id)
          if not candidates:
              return None, False
          desc = (descriptor or "").strip().lower()
          if not desc:
              return (candidates[0], False) if len(candidates) == 1 else (None, True)
          matches = [
              s
              for s in candidates
              if desc in s.name.lower() or desc in s.site_id.lower() or s.name.lower() in desc
          ]
          if len(matches) == 1:
              return matches[0], False
          if len(matches) > 1:
              return None, True
          return None, False

      def site_owning_node(self, node_id: str) -> SiteDescriptor | None:
          """The site whose namespace a graph node belongs to (for exit)."""
          sid = site_id_of(node_id)
          return self._by_id.get(sid) if sid else None
  ```
- [ ] Create `sidequest/game/sites/__init__.py`:
  ```python
  """Static→procedural SITE crossings and the site registry (Track B)."""
  from sidequest.game.sites.models import SiteDecl, SiteDescriptor, SiteExtent
  from sidequest.game.sites.namespacing import (
      is_site_node_id,
      site_entrance_id,
      site_id_of,
  )
  from sidequest.game.sites.registry import SiteRegistry

  __all__ = [
      "SiteDecl",
      "SiteDescriptor",
      "SiteExtent",
      "SiteRegistry",
      "is_site_node_id",
      "site_entrance_id",
      "site_id_of",
  ]
  ```
- [ ] Add the `sites` field to `CartographyConfig`. In `sidequest/genre/models/world.py`, after the `routes` line (`:297`), add:
  ```python
      sites: list[SiteDecl] = Field(default_factory=list)
  ```
  and add `SiteDecl` to the model definitions in `world.py` (define it here to avoid an import cycle — `game.sites.models` imports FROM `world` transitively via nothing, but keep the field type local): import at top of `world.py` is disallowed (game→genre dependency direction). Instead define `SiteDecl` **inline in `world.py`** (mirror the class from `models.py`) and have `game/sites/models.py` re-export it. Concretely: cut `SiteDecl` from `game/sites/models.py`, define it in `world.py` above `CartographyConfig`, and in `game/sites/models.py` do `from sidequest.genre.models.world import SiteDecl`.
- [ ] Create empty `tests/game/sites/__init__.py`.
- [ ] Run: `cd sidequest-server && uv run pytest tests/game/sites/test_site_registry.py -v` — expect all pass.
- [ ] Lint/format touched files: `uv run ruff check sidequest/game/sites/ sidequest/genre/models/world.py tests/game/sites/ && uv run ruff format sidequest/game/sites/ tests/game/sites/`.
- [ ] Commit (branch first, own Bash call):
  ```bash
  cd sidequest-server && git checkout -b feat/track-b-site-registry
  ```
  then:
  ```bash
  cd sidequest-server && git add sidequest/game/sites/ sidequest/genre/models/world.py tests/game/sites/ && git commit -m "feat(sites): SiteDescriptor + SiteRegistry + CartographyConfig.sites (Track B B1)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
  ```

---

## Task 2: Per-site storage keying — `site_id` column + repository methods (additive)

The dungeon tables are keyed by `session_id` only (`alembic/versions/0001_initial_unified_schema.py:166`), so a session holds ONE dungeon. Sites need `(session_id, site_id)`. This task adds the column + threads an optional `site_id` through `PgDungeonRepository` methods, defaulting to a legacy constant so Sünden's existing path is unchanged. **No saves to migrate** (per project memory — the migration is additive, no backfill worry).

**Files:**
- Create `sidequest-server/alembic/versions/0003_dungeon_site_id.py`
- Modify `sidequest-server/sidequest/game/pg/dungeon.py` — `load_map` (`:415`), `load_masks` (`:440`), `commit_expansion` (`:393`), `PgDungeonTransaction.commit_expansion` (`:103`), `put_frontier`/`load_frontier` (`:469`/`:474`), `record_mutation`/`load_mutations` (`:491`/`:496`), `get_campaign_seed`/`set_campaign_seed` (`:350`/`:359`)
- Modify `sidequest-server/sidequest/game/repository.py` — `DungeonRepository` Protocol (`:307`) method signatures
- Create `sidequest-server/tests/game/pg/test_dungeon_site_keying.py`

**Interfaces:**
- Consumes: `session_tx` / `self._pool` / `self._sid` (existing). SQL tables `dungeon_map`, `dungeon_edge`, `dungeon_frontier`, `dungeon_mutation_overlay`, `dungeon_meta`, `dungeon_complication_ledger`.
- Produces (consumed by Tasks 6, 7, 12): every `PgDungeonRepository` method gains a keyword-only `site_id: str = DEFAULT_SITE_ID`. `DEFAULT_SITE_ID = "frontier"` exported from `sidequest/game/pg/dungeon.py` (Sünden's legacy dungeon lands here after Task 10 migration; before it, all writes are under this default, so no behavior change).

**Steps:**

- [ ] Write the failing test `tests/game/pg/test_dungeon_site_keying.py` (requires `SIDEQUEST_TEST_DATABASE_URL`; mark accordingly and mirror the existing `tests/game/pg/` fixtures — read a sibling test e.g. `tests/game/pg/test_dungeon.py` for the `pg_dungeon_repo`/session fixture shape before writing):
  ```python
  """Two sites in one session must not collide (Track B, Task 2)."""
  from __future__ import annotations

  from sidequest.dungeon.region_graph.model import RegionGraph, RegionNode
  from sidequest.game.pg.dungeon import DEFAULT_SITE_ID

  # Reuse the repo/session fixture from tests/game/pg/conftest.py (pg_dungeon_repo).

  def _node(nid: str) -> RegionNode:
      return RegionNode(id=nid, theme="stone", depth_score=0.0, expansion_id=0)

  def test_default_site_id_is_frontier() -> None:
      assert DEFAULT_SITE_ID == "frontier"

  def test_two_sites_do_not_collide(pg_dungeon_repo) -> None:
      repo = pg_dungeon_repo
      # Commit a node into site 'gilded_boar' and a different node into 'frontier'.
      from sidequest.dungeon.materializer import Expansion  # existing dataclass
      g1 = RegionGraph(entrance_id="gilded_boar:entrance")
      g1.add_node(_node("gilded_boar:entrance"))
      repo.commit_expansion(Expansion(expansion_id=0, region_ids=("gilded_boar:entrance",)),
                            g1, site_id="gilded_boar")
      g2 = RegionGraph(entrance_id="frontier:entrance")
      g2.add_node(_node("frontier:entrance"))
      repo.commit_expansion(Expansion(expansion_id=0, region_ids=("frontier:entrance",)),
                            g2, site_id="frontier")
      # Each site's map contains only its own node.
      boar = repo.load_map(entrance_id="gilded_boar:entrance", site_id="gilded_boar")
      deep = repo.load_map(entrance_id="frontier:entrance", site_id="frontier")
      assert set(boar.nodes) == {"gilded_boar:entrance"}
      assert set(deep.nodes) == {"frontier:entrance"}
  ```
  (If the `Expansion` constructor signature differs, read `sidequest/dungeon/materializer.py` around the `Expansion` dataclass and adapt the fixture — do not invent fields.)
- [ ] Run: `cd sidequest-server && uv run pytest tests/game/pg/test_dungeon_site_keying.py -v -n0` — expect failures (`ImportError: DEFAULT_SITE_ID`, `commit_expansion() got an unexpected keyword argument 'site_id'`).
- [ ] Write the Alembic migration `alembic/versions/0003_dungeon_site_id.py` (revises `0002_asset_ledger`; add `site_id TEXT NOT NULL DEFAULT 'frontier'` to each dungeon table and re-key PKs to include it — verify the down-revision id by reading `0002_asset_ledger.py`'s `revision`):
  ```python
  """add site_id to dungeon tables (Track B multi-site).

  Revision ID: 0003_dungeon_site_id
  Revises: 0002_asset_ledger
  """
  from alembic import op

  revision = "0003_dungeon_site_id"
  down_revision = "0002_asset_ledger"
  branch_labels = None
  depends_on = None

  _SITE = "frontier"


  def upgrade() -> None:
      op.execute(
          f"""
          ALTER TABLE dungeon_map ADD COLUMN site_id TEXT NOT NULL DEFAULT '{_SITE}';
          ALTER TABLE dungeon_map DROP CONSTRAINT dungeon_map_pkey;
          ALTER TABLE dungeon_map ADD PRIMARY KEY (session_id, site_id, region_id);

          ALTER TABLE dungeon_edge ADD COLUMN site_id TEXT NOT NULL DEFAULT '{_SITE}';

          ALTER TABLE dungeon_frontier ADD COLUMN site_id TEXT NOT NULL DEFAULT '{_SITE}';
          ALTER TABLE dungeon_frontier DROP CONSTRAINT dungeon_frontier_pkey;
          ALTER TABLE dungeon_frontier ADD PRIMARY KEY (session_id, site_id, frontier_edge_id);

          ALTER TABLE dungeon_mutation_overlay ADD COLUMN site_id TEXT NOT NULL DEFAULT '{_SITE}';

          ALTER TABLE dungeon_complication_ledger ADD COLUMN site_id TEXT NOT NULL DEFAULT '{_SITE}';
          ALTER TABLE dungeon_complication_ledger DROP CONSTRAINT dungeon_complication_ledger_pkey;
          ALTER TABLE dungeon_complication_ledger ADD PRIMARY KEY (session_id, site_id, thread_id);

          ALTER TABLE dungeon_meta ADD COLUMN site_id TEXT NOT NULL DEFAULT '{_SITE}';
          ALTER TABLE dungeon_meta DROP CONSTRAINT dungeon_meta_pkey;
          ALTER TABLE dungeon_meta ADD PRIMARY KEY (session_id, site_id);
          """
      )


  def downgrade() -> None:
      op.execute(
          """
          ALTER TABLE dungeon_meta DROP CONSTRAINT dungeon_meta_pkey;
          ALTER TABLE dungeon_meta DROP COLUMN site_id;
          ALTER TABLE dungeon_meta ADD PRIMARY KEY (session_id);
          ALTER TABLE dungeon_complication_ledger DROP CONSTRAINT dungeon_complication_ledger_pkey;
          ALTER TABLE dungeon_complication_ledger DROP COLUMN site_id;
          ALTER TABLE dungeon_complication_ledger ADD PRIMARY KEY (session_id, thread_id);
          ALTER TABLE dungeon_mutation_overlay DROP COLUMN site_id;
          ALTER TABLE dungeon_frontier DROP CONSTRAINT dungeon_frontier_pkey;
          ALTER TABLE dungeon_frontier DROP COLUMN site_id;
          ALTER TABLE dungeon_frontier ADD PRIMARY KEY (session_id, frontier_edge_id);
          ALTER TABLE dungeon_edge DROP COLUMN site_id;
          ALTER TABLE dungeon_map DROP CONSTRAINT dungeon_map_pkey;
          ALTER TABLE dungeon_map DROP COLUMN site_id;
          ALTER TABLE dungeon_map ADD PRIMARY KEY (session_id, region_id);
          """
      )
  ```
- [ ] Add `DEFAULT_SITE_ID = "frontier"` near the top of `sidequest/game/pg/dungeon.py` (alongside `_DEFAULT_GENERATOR_VERSION`). Thread a keyword-only `site_id: str = DEFAULT_SITE_ID` into each method and add `AND site_id = %s` (or the column) to every query, and `site_id` to every INSERT. Concretely, for `load_map` (`:415`) replace the two queries:
  ```python
      def load_map(self, *, entrance_id: str, site_id: str = DEFAULT_SITE_ID) -> RegionGraph:
          with self._pool.connection() as conn:
              node_rows = conn.execute(
                  "SELECT payload FROM dungeon_map WHERE session_id = %s AND site_id = %s",
                  (self._sid, site_id),
              ).fetchall()
              edge_rows = conn.execute(
                  "SELECT payload FROM dungeon_edge WHERE session_id = %s AND site_id = %s "
                  "ORDER BY edge_id",
                  (self._sid, site_id),
              ).fetchall()
          # ... rest unchanged (RegionGraph rebuild)
  ```
  Apply the parallel edit to `load_masks` (`:440`, add `AND site_id = %s`), `load_frontier` (`:474`), `load_mutations` (`:496`), `get_campaign_seed` (`:350`, `WHERE session_id = %s AND site_id = %s`). For the writers — `PgDungeonTransaction.commit_expansion` (`:103`, add `site_id` param, include it in the `dungeon_map`/`dungeon_edge` INSERT column lists at `:167`/`:174`), `put_frontier` (`:200` INSERT + ON CONFLICT target now `(session_id, site_id, frontier_edge_id)`), `record_mutation` (`:226`), `set_campaign_seed` (`:376`) — add `site_id` to the INSERT columns and thread the param. The public `PgDungeonRepository` wrappers (`commit_expansion` `:393`, `put_frontier` `:469`, `record_mutation` `:491`) forward `site_id` to their `PgDungeonTransaction` calls. **Note:** `PgDungeonTransaction.__init__` (`:99`) may need a `site_id` field, or pass `site_id` per-call — pass per-call to keep the tx object site-agnostic.
- [ ] Update the `DungeonRepository` Protocol (`sidequest/game/repository.py:307`) method signatures to add the `site_id: str = ...` keyword to `load_map`, `load_masks`, `commit_expansion`, `put_frontier`, `load_frontier`, `record_mutation`, `load_mutations`, `get_campaign_seed`, `set_campaign_seed`.
- [ ] Apply the migration to the test DB: `cd sidequest-server && uv run alembic upgrade head` (ensure `SIDEQUEST_TEST_DATABASE_URL`/`SIDEQUEST_DATABASE_URL` points at the local pg; `just pg-up` provisions it).
- [ ] Run: `cd sidequest-server && uv run pytest tests/game/pg/test_dungeon_site_keying.py -v -n0` — expect pass. Then run the existing dungeon repo suite to confirm no regression: `uv run pytest tests/game/pg/ -v -n0`.
- [ ] Lint/format touched files; commit:
  ```bash
  cd sidequest-server && git add alembic/versions/0003_dungeon_site_id.py sidequest/game/pg/dungeon.py sidequest/game/repository.py tests/game/pg/test_dungeon_site_keying.py && git commit -m "feat(sites): key dungeon storage by (session_id, site_id) (Track B B1)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
  ```

---

## Task 3: Characterization tests — pin CURRENT Sünden movement/seam behavior (guard)

Before touching the `movement.py` ladder (Task 6), lock its OBSERVABLE behavior with tests that PASS on `develop` today. These are the safety net for the risky cutover: they must still pass (possibly with updated internal ids) after Task 6/10.

**Files:**
- Create `sidequest-server/tests/agents/subsystems/test_movement_sunden_characterization.py`

**Interfaces:**
- Consumes: `run_movement_dispatch` (`sidequest/agents/subsystems/movement.py:337`); `SubsystemDispatch` (`sidequest/protocol/dispatch.py:106`); a synthetic `beneath_sunden`-shaped `GenrePack`/`GameSnapshot`/`DungeonStore`. Read the EXISTING movement tests (`tests/agents/subsystems/test_movement*.py` — grep the tree) and reuse their fixtures rather than inventing snapshot/store doubles.
- Produces: five behavioral assertions covering the five rungs. These do NOT assert internal rung names — only observable outcomes (patch applied to the right region; `resolved_via` on the emitted span; `movement.unresolved` NOT fired).

**Steps:**

- [ ] Discover the existing movement-test fixtures: `cd sidequest-server && grep -rln "run_movement_dispatch" tests/ && grep -rn "def .*dungeon_store\|seam_route_for\|region_mode\|the_dropmouth\|ropefoot" tests/agents/subsystems/ | head`. Reuse the closest fixture (a fake `DungeonStore` exposing `load_map(entrance_id=...) -> RegionGraph` with `entrance`/`exp001.r*` nodes; a `GameSnapshot` with `pc_regions`; a cartography with `the_dropmouth`→`deep_descent` route + `ropefoot` adjacency).
- [ ] Write `test_movement_sunden_characterization.py` with five async tests capturing today's behavior (asserting on the returned `SubsystemOutput.data["resolved_via"]` / `data["to_region"]` and, via a span-capture helper if one exists in the fixture suite, the fired span):
  - `test_owned_seam_descent_from_dropmouth` — PC on `the_dropmouth`, `direction="deeper"` → `data["resolved_via"] == "surface_descent"`, `data["to_region"] == "entrance"`.
  - `test_adjacent_seam_descent_from_ropefoot` — PC on `ropefoot`, `direction="deeper"` → `resolved_via == "surface_descent_adjacent"`, `to_region == "entrance"`.
  - `test_entrance_ascent` — PC on `entrance`, `direction="back"` → `resolved_via == "surface_ascent"`, `to_region == "the_dropmouth"` (the seam owner).
  - `test_in_dungeon_navigation` — PC on `exp001.r0`, `direction="deeper"`, a real neighbor exists → `to_region` is that neighbor, no error.
  - `test_region_mode_lateral_defers_or_resolves` — PC on a non-seam surface region with a non-travel descriptor → `data["resolved_via"] == "region_mode_deferred"` (the `_defer_region_mode` outcome, `movement.py:1209`).
- [ ] Run: `cd sidequest-server && uv run pytest tests/agents/subsystems/test_movement_sunden_characterization.py -v -n0` — **expect all PASS on current `develop`** (this task locks behavior; there is no RED phase because the code already behaves this way — the "failing test" discipline here is: if any assertion does NOT match current behavior, you've mis-modeled the fixture; fix the test to reflect the real current output before proceeding).
- [ ] Lint/format; commit:
  ```bash
  cd sidequest-server && git add tests/agents/subsystems/test_movement_sunden_characterization.py && git commit -m "test(sites): characterize current Sünden movement/seam behavior (Track B guard)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
  ```

---

## Task 4: Symmetric `enter_site` / `exit_site` seam resolvers + registry (additive)

Add the new resolvers alongside the existing `deep_descent`/`surface_ascent`, driven by `SiteDescriptor`. Both registered in the seam registry (fixing the asymmetry where `surface_ascent` is called directly, `movement.py:504`). Each emits a span that reaches `turn_telemetry`. **Additive** — nothing calls these yet (Task 6 wires them). `enter_site` supports `extent="frontier"` now (binds to the site entrance; bounded materialization is Task 12).

**Files:**
- Create `sidequest-server/sidequest/game/sites/enter_site.py`
- Create `sidequest-server/sidequest/game/sites/exit_site.py`
- Create `sidequest-server/sidequest/telemetry/spans/site.py` (site spans + turn_telemetry mirror)
- Modify `sidequest-server/sidequest/game/seams/registry.py` — register `enter_site`/`exit_site`
- Modify `sidequest-server/sidequest/game/sites/__init__.py` — export resolvers
- Create `sidequest-server/tests/game/sites/test_site_resolvers.py`
- Create `sidequest-server/tests/telemetry/test_site_spans_to_sink.py`

**Interfaces:**
- Consumes: `SiteDescriptor` (Task 1); `DungeonRepository.load_map(*, entrance_id, site_id)` (Task 2); `GameSnapshot.apply_world_patch(WorldStatePatch(pc_region={name: node}))` (`session.py:1502` / `:537`); `SeamCrossingError(reason=, surface=)` (`seams/base.py:15`); `SPAN_ROUTES`/`SpanRoute` (`telemetry/spans/_core.py`), `Span.open` (`telemetry/spans/span.py`), `publish_event` (`watcher_hub.py:712`) — mirror pattern from `telemetry/spans/movement.py:151`.
- Produces (consumed by Task 6): `resolve_enter_site(*, snapshot, player_name, site, dungeon_repository, resolved_via, direction="", exit_descriptor="", **_) -> SeamCrossingResult`; `resolve_exit_site(*, snapshot, player_name, site, cartography, resolved_via, **_) -> SeamCrossingResult`. Span helpers `site_enter_span`, `site_exit_span`, `site_enter_unresolved_span`.

**Steps:**

- [ ] Write the failing span-mirror test `tests/telemetry/test_site_spans_to_sink.py` (model on the existing movement-span sink test — grep `tests/telemetry/` for `_mirror_movement_span_to_sink`/`publish_event` monkeypatch):
  ```python
  """site.* spans must reach turn_telemetry via publish_event, not Span.open alone."""
  from __future__ import annotations

  from unittest.mock import patch

  from sidequest.telemetry.spans.site import site_enter_span


  def test_site_enter_span_publishes_to_sink() -> None:
      with patch("sidequest.telemetry.spans.site.publish_event") as pub:
          with site_enter_span(pc_name="Rux", site_id="frontier", from_region="the_dropmouth") as span:
              span.set_attribute("to_region", "frontier:entrance")
              span.set_attribute("resolved_via", "site_enter")
      assert pub.called, "site.enter must mirror to turn_telemetry via publish_event"
      event_type, fields = pub.call_args.args[0], pub.call_args.args[1]
      assert event_type == "state_transition"
      assert fields["op"] == "site.enter"
      assert fields["site_id"] == "frontier"
  ```
- [ ] Run: `cd sidequest-server && uv run pytest tests/telemetry/test_site_spans_to_sink.py -v -n0` — expect `ModuleNotFoundError: sidequest.telemetry.spans.site`.
- [ ] Create `sidequest/telemetry/spans/site.py` (register routes + mirror; the sole publisher pattern from `movement.py`):
  ```python
  """Site seam spans (Track B). Every helper mirrors to turn_telemetry via
  publish_event after the span closes — Span.open alone reaches Jaeger + the
  live GM dashboard but NOT the Postgres sink (see spans/movement.py:151)."""
  from __future__ import annotations

  from collections.abc import Iterator
  from contextlib import contextmanager
  from typing import Any

  from opentelemetry import trace
  from opentelemetry.trace import Status, StatusCode

  from sidequest.telemetry.watcher_hub import publish_event

  from ._core import SPAN_ROUTES, SpanRoute
  from .span import Span

  SPAN_SITE_ENTER = "site.enter"
  SPAN_SITE_EXIT = "site.exit"
  SPAN_SITE_ENTER_UNRESOLVED = "site.enter_unresolved"


  def _attr(field: str):
      return lambda span, f=field: (span.attributes or {}).get(f)


  SPAN_ROUTES[SPAN_SITE_ENTER] = SpanRoute(
      event_type="state_transition",
      component="sites",
      extract=lambda s: {
          "field": "pc_regions",
          "op": "site.enter",
          "pc_name": _attr("pc_name")(s),
          "site_id": _attr("site_id")(s),
          "from_region": _attr("from_region")(s),
          "to_region": _attr("to_region")(s),
          "resolved_via": _attr("resolved_via")(s),
          "extent": _attr("extent")(s),
      },
  )
  SPAN_ROUTES[SPAN_SITE_EXIT] = SpanRoute(
      event_type="state_transition",
      component="sites",
      extract=lambda s: {
          "field": "pc_regions",
          "op": "site.exit",
          "pc_name": _attr("pc_name")(s),
          "site_id": _attr("site_id")(s),
          "from_region": _attr("from_region")(s),
          "to_region": _attr("to_region")(s),
          "resolved_via": _attr("resolved_via")(s),
      },
  )
  SPAN_ROUTES[SPAN_SITE_ENTER_UNRESOLVED] = SpanRoute(
      event_type="state_transition",
      component="sites",
      extract=lambda s: {
          "field": "pc_regions",
          "op": "site.enter_unresolved",
          "pc_name": _attr("pc_name")(s),
          "from_region": _attr("from_region")(s),
          "reason": _attr("reason")(s),
          "descriptor": _attr("descriptor")(s),
      },
  )


  def _mirror(span_name: str, span: trace.Span) -> None:
      route = SPAN_ROUTES.get(span_name)
      if route is None or not hasattr(span, "attributes"):
          return
      publish_event(route.event_type, route.extract(span), component=route.component)


  @contextmanager
  def site_enter_span(
      *, pc_name: str, site_id: str, from_region: str,
      _tracer: trace.Tracer | None = None, **attrs: Any,
  ) -> Iterator[trace.Span]:
      with Span.open(
          SPAN_SITE_ENTER,
          {"pc_name": pc_name, "site_id": site_id, "from_region": from_region, **attrs},
          tracer_override=_tracer,
      ) as span:
          yield span
      _mirror(SPAN_SITE_ENTER, span)


  @contextmanager
  def site_exit_span(
      *, pc_name: str, site_id: str, from_region: str,
      _tracer: trace.Tracer | None = None, **attrs: Any,
  ) -> Iterator[trace.Span]:
      with Span.open(
          SPAN_SITE_EXIT,
          {"pc_name": pc_name, "site_id": site_id, "from_region": from_region, **attrs},
          tracer_override=_tracer,
      ) as span:
          yield span
      _mirror(SPAN_SITE_EXIT, span)


  @contextmanager
  def site_enter_unresolved_span(
      *, pc_name: str, from_region: str, reason: str, descriptor: str,
      _tracer: trace.Tracer | None = None, **attrs: Any,
  ) -> Iterator[trace.Span]:
      with Span.open(
          SPAN_SITE_ENTER_UNRESOLVED,
          {"pc_name": pc_name, "from_region": from_region, "reason": reason,
           "descriptor": descriptor, **attrs},
          tracer_override=_tracer,
      ) as span:
          span.set_status(Status(StatusCode.ERROR, reason))
          yield span
      _mirror(SPAN_SITE_ENTER_UNRESOLVED, span)


  __all__ = [
      "SPAN_SITE_ENTER", "SPAN_SITE_EXIT", "SPAN_SITE_ENTER_UNRESOLVED",
      "site_enter_span", "site_exit_span", "site_enter_unresolved_span",
  ]
  ```
  (Verify `SpanRoute`'s field names by reading `sidequest/telemetry/spans/_core.py` — the movement routes use `event_type`, `component`, `extract`; match exactly.)
- [ ] Run the span test — expect pass.
- [ ] Write the failing resolver test `tests/game/sites/test_site_resolvers.py`:
  ```python
  """enter_site / exit_site resolvers bind pc_region + emit spans (Track B)."""
  from __future__ import annotations

  import pytest

  from sidequest.game.seams.base import SeamCrossingError
  from sidequest.game.sites import SiteDescriptor
  from sidequest.game.sites.enter_site import resolve_enter_site
  from sidequest.game.sites.exit_site import resolve_exit_site

  # Reuse a fake DungeonRepository + GameSnapshot (grep tests/ for a fake dungeon
  # store exposing load_map(entrance_id=..., site_id=...) with the entrance node).

  _FRONTIER = SiteDescriptor(site_id="frontier", name="The Deep", archetype="megadungeon",
                             attached_to="the_dropmouth", extent="frontier")

  @pytest.mark.asyncio
  async def test_enter_site_binds_pc_to_site_entrance(fake_snapshot, fake_frontier_repo) -> None:
      # fake_frontier_repo.load_map(site_id="frontier") returns a graph containing
      # "frontier:entrance".
      result = resolve_enter_site(
          snapshot=fake_snapshot, player_name="Rux", site=_FRONTIER,
          dungeon_repository=fake_frontier_repo, resolved_via="site_enter",
      )
      assert result.to_region == "frontier:entrance"
      assert fake_snapshot.region_for(perspective="Rux") == "frontier:entrance"

  @pytest.mark.asyncio
  async def test_enter_site_missing_store_raises_recoverable(fake_snapshot) -> None:
      with pytest.raises(SeamCrossingError) as ei:
          resolve_enter_site(snapshot=fake_snapshot, player_name="Rux", site=_FRONTIER,
                             dungeon_repository=None, resolved_via="site_enter")
      assert ei.value.reason == "no_site_store"

  @pytest.mark.asyncio
  async def test_exit_site_binds_pc_to_attached_region(fake_snapshot_in_site, fake_cart) -> None:
      result = resolve_exit_site(
          snapshot=fake_snapshot_in_site, player_name="Rux", site=_FRONTIER,
          cartography=fake_cart, resolved_via="site_exit",
      )
      assert result.to_region == "the_dropmouth"
      assert fake_snapshot_in_site.region_for(perspective="Rux") == "the_dropmouth"
  ```
  (Build `fake_*` fixtures in a local `tests/game/sites/conftest.py`, adapting the doubles used by Task 3's movement fixtures — a minimal `GameSnapshot` with `apply_world_patch`/`region_for(perspective=...)` and a repo with `load_map(entrance_id=, site_id=)`.)
- [ ] Run: expect import failures.
- [ ] Create `sidequest/game/sites/enter_site.py` (parallels `deep_descent.py:26`, site-parameterized, span mirrored):
  ```python
  """enter_site seam resolver — bind THIS PC onto a site's entrance node."""
  from __future__ import annotations

  import logging
  from typing import TYPE_CHECKING, Any

  from sidequest.game.seams.base import SeamCrossingError, SeamCrossingResult
  from sidequest.game.session import WorldStatePatch
  from sidequest.telemetry.spans.site import site_enter_span

  if TYPE_CHECKING:
      from sidequest.game.repository import DungeonRepository
      from sidequest.game.session import GameSnapshot
      from sidequest.game.sites import SiteDescriptor

  logger = logging.getLogger(__name__)


  def resolve_enter_site(
      *,
      snapshot: GameSnapshot,
      player_name: str,
      site: SiteDescriptor,
      dungeon_repository: DungeonRepository | None = None,
      resolved_via: str = "site_enter",
      direction: str = "",
      exit_descriptor: str = "",
      **_context: Any,
  ) -> SeamCrossingResult:
      """Bind THIS PC onto ``site.entrance_node_id``, or raise SeamCrossingError.

      Bounded materialization (extent=='bounded') is performed by the caller
      BEFORE this resolver (Task 12) so the entrance node already exists; a
      frontier site (Sünden) was bootstrapped at connect. This resolver only
      binds + emits — it never generates."""
      from_region = snapshot.region_for(perspective=player_name) or ""
      if dungeon_repository is None:
          raise SeamCrossingError(
              reason="no_site_store",
              surface=(
                  f"The way into {site.name} exists, but its interior has not "
                  "been opened — a wiring fault, not a closed door."
              ),
          )
      graph = dungeon_repository.load_map(entrance_id=site.entrance_node_id, site_id=site.site_id)
      if site.entrance_node_id not in graph.nodes:
          raise SeamCrossingError(
              reason="no_site_entrance",
              surface=f"The interior of {site.name} has not yet formed.",
          )
      snapshot.apply_world_patch(WorldStatePatch(pc_region={player_name: site.entrance_node_id}))
      with site_enter_span(
          pc_name=player_name, site_id=site.site_id, from_region=from_region
      ) as span:
          span.set_attribute("to_region", site.entrance_node_id)
          span.set_attribute("resolved_via", resolved_via)
          span.set_attribute("extent", site.extent)
          span.set_attribute("archetype", site.archetype)
          span.set_attribute("party_split_after", snapshot.region_for() is None)
      logger.debug(
          "site.enter pc=%s site=%s from=%s to=%s via=%s",
          player_name, site.site_id, from_region, site.entrance_node_id, resolved_via,
      )
      return SeamCrossingResult(to_region=site.entrance_node_id)
  ```
- [ ] Create `sidequest/game/sites/exit_site.py` (parallels `surface_ascent.py:30`, membership-checked):
  ```python
  """exit_site seam resolver — bind THIS PC back to the site's owning region."""
  from __future__ import annotations

  import logging
  from typing import TYPE_CHECKING, Any

  from sidequest.game.seams.base import SeamCrossingError, SeamCrossingResult
  from sidequest.game.session import WorldStatePatch
  from sidequest.telemetry.spans.site import site_exit_span

  if TYPE_CHECKING:
      from sidequest.game.session import GameSnapshot
      from sidequest.game.sites import SiteDescriptor
      from sidequest.genre.models.world import CartographyConfig

  logger = logging.getLogger(__name__)


  def resolve_exit_site(
      *,
      snapshot: GameSnapshot,
      player_name: str,
      site: SiteDescriptor,
      cartography: CartographyConfig | None = None,
      resolved_via: str = "site_exit",
      **_context: Any,
  ) -> SeamCrossingResult:
      """Bind THIS PC back to ``site.attached_to`` (the owning cartography
      region), or raise. Membership-checked (never strand the PC in a phantom)."""
      from_region = snapshot.region_for(perspective=player_name) or ""
      surface_id = site.attached_to
      regions = getattr(cartography, "regions", None) or {}
      if not surface_id or surface_id not in regions:
          raise SeamCrossingError(
              reason="dangling_site_owner",
              surface=(
                  f"There is a way out of {site.name}, but it returns to a place "
                  "that isn't on the map — a wiring fault, not a sealed door."
              ),
          )
      snapshot.apply_world_patch(WorldStatePatch(pc_region={player_name: surface_id}))
      with site_exit_span(
          pc_name=player_name, site_id=site.site_id, from_region=from_region
      ) as span:
          span.set_attribute("to_region", surface_id)
          span.set_attribute("resolved_via", resolved_via)
          span.set_attribute("party_split_after", snapshot.region_for() is None)
      logger.debug(
          "site.exit pc=%s site=%s from=%s to=%s", player_name, site.site_id, from_region, surface_id
      )
      return SeamCrossingResult(to_region=surface_id)
  ```
- [ ] Register both in `sidequest/game/seams/registry.py`. Import the resolvers and add to `_REGISTRY` (`:20`). NOTE: the existing `_REGISTRY` maps `to_id` (a route sentinel) → resolver; `enter_site`/`exit_site` are called directly by Task 6 (not via `to_id` lookup), so also expose a thin accessor. Add:
  ```python
  from sidequest.game.sites.enter_site import resolve_enter_site
  from sidequest.game.sites.exit_site import resolve_exit_site
  # ... within _REGISTRY dict:
      "enter_site": resolve_enter_site,
      "exit_site": resolve_exit_site,
  ```
  (This keeps `get_seam_resolver("enter_site")` working AND leaves `deep_descent` registered for now — Task 6/10 removes the deep_descent path.)
- [ ] Export `resolve_enter_site`/`resolve_exit_site` from `sidequest/game/sites/__init__.py`.
- [ ] Run: `cd sidequest-server && uv run pytest tests/game/sites/ tests/telemetry/test_site_spans_to_sink.py -v -n0` — expect all pass.
- [ ] Lint/format; commit:
  ```bash
  cd sidequest-server && git add sidequest/game/sites/ sidequest/game/seams/registry.py sidequest/telemetry/spans/site.py tests/game/sites/ tests/telemetry/test_site_spans_to_sink.py && git commit -m "feat(sites): symmetric enter_site/exit_site resolvers + turn_telemetry spans (Track B B1)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
  ```

---

## Task 5: Router site targets — movement `action` param + enterable-site surfacing (additive)

Teach the intent router to emit `enter_site`/`exit_site` and surface enterable sites in the state summary. **Additive** — the movement dispatch still ignores `action` until Task 6, and the existing `direction`/`exit_descriptor` vocabulary stays for in-scene navigation.

**Files:**
- Modify `sidequest-server/sidequest/agents/intent_router.py` — movement bullet in `_SYSTEM_PROMPT` (`:192`–`:224`) + the "seam goes down" guidance (`:216`–`:224`)
- Modify `sidequest-server/sidequest/server/intent_router_pass.py` — `_build_state_summary` (`:590`–`:626`) to list enterable sites
- Create `sidequest-server/tests/server/test_intent_router_sites_summary.py`

**Interfaces:**
- Consumes: `SiteRegistry.sites_for_node` (Task 1); the `summary` dict built in `_build_state_summary` (`intent_router_pass.py:590`); `snapshot.region_for` / `snapshot.world_slug`.
- Produces (consumed by Task 6): the router may emit `movement` dispatches with `params={"action": "enter_site", "site_descriptor": "<free text>"}` or `params={"action": "exit_site"}`. The state summary gains `current_sites: [{"site_id", "name", "archetype"}]` so the router knows which sites are enterable by name.

**Steps:**

- [ ] Write the failing test `tests/server/test_intent_router_sites_summary.py` (drive `_build_state_summary` with a beneath_sunden-shaped pack that now declares a `frontier` site, plus a tavern world; assert `current_sites` appears with the site name). Reuse the existing `_build_state_summary` test fixtures (grep `tests/server/` for `_build_state_summary`/`current_region_exits`).
  ```python
  def test_state_summary_lists_enterable_sites(sunden_snapshot, sunden_pack) -> None:
      from sidequest.server.intent_router_pass import _build_state_summary
      summary = _build_state_summary(snapshot=sunden_snapshot, pack=sunden_pack, dungeon_store=...)
      assert any(s["name"] == "The Deep" for s in summary.get("current_sites", []))
  ```
  (Match `_build_state_summary`'s real signature by reading `intent_router_pass.py` around `:560`–`:590`; it is a module-level or nested helper — call it exactly as the existing tests do.)
- [ ] Run: expect `KeyError`/assertion failure (`current_sites` absent).
- [ ] In `_build_state_summary` (`intent_router_pass.py`, in the region-exits block after the seam handling at `:613`–`:619`), build `current_sites` from a `SiteRegistry`:
  ```python
  from sidequest.game.sites import SiteRegistry
  _reg = SiteRegistry.from_cartography(_cart)
  _enterable = _reg.sites_for_node(_region_id) if _region_id else []
  if _enterable:
      summary["current_sites"] = [
          {"site_id": s.site_id, "name": s.name, "archetype": s.archetype} for s in _enterable
      ]
  ```
  (Keep the existing `current_region_exits`/seam span logic intact — this is additive.)
- [ ] Update the movement bullet in `intent_router.py:_SYSTEM_PROMPT` (`:192`–`:224`). Replace the `direction`-only param schema and the hardcoded "A 'seam' exit ... goes DOWN — direction 'deeper'" guidance (`:216`–`:224`) with site-target guidance:
  ```
  - movement: the party physically relocates. params take one of two shapes:
    * ENTER/EXIT A SITE — when game_state.current_sites lists enterable
      sub-locations (a tavern, a vault, the deep below a shaft) and the
      player heads into or out of one:
        {"action": "enter_site",
         "site_descriptor": "<the site the player named, in their own words —
                             e.g. 'the tavern', 'the gilded boar', 'down into
                             the deep'>"}
      or, when the party is already INSIDE a site and leaves:
        {"action": "exit_site"}
      Name the site by descriptor only; the engine matches it against
      game_state.current_sites and refuses honestly if nothing matches.
    * IN-SCENE NAVIGATION — moving between rooms WITHIN a site (or between
      adjacent cartography regions):
        {"direction": "<deeper | back | toward_exit>",
         "exit_descriptor": "<the way the player named — 'the iron stair',
                             'south', 'the east passage'>"}
    Emit movement ONLY for genuine relocation, not look-around/search/examine.
    NEVER emit a region id — you do not know the graph. "Enter the tavern" is
    enter_site; "go through the archway to the next room" is in-scene navigation.
  ```
- [ ] Run: `cd sidequest-server && uv run pytest tests/server/test_intent_router_sites_summary.py -v -n0` — expect pass.
- [ ] Lint/format; commit:
  ```bash
  cd sidequest-server && git add sidequest/agents/intent_router.py sidequest/server/intent_router_pass.py tests/server/test_intent_router_sites_summary.py && git commit -m "feat(sites): router emits enter_site/exit_site targets + surfaces enterable sites (Track B B1)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
  ```

---

## Task 6: **[RISKY CUTOVER]** Movement ladder → SiteRegistry × enter/exit resolvers + Sünden frontier-site migration

Replace `movement.py`'s five-rung inlined seam ladder (`:386`–`:627`) with SiteRegistry descriptor-resolution × the `enter_site`/`exit_site` resolvers, AND declare Sünden's deep as the first `frontier` site so it keeps working. Task 3's characterization tests are the guard. **This is the riskiest task in B1.**

**Files:**
- Modify `sidequest-server/sidequest/agents/subsystems/movement.py` — the region-mode seam rungs (`:386`–`:538`), the §Q1 step-2b surface→deep handoff (`:667`–`:740`), imports (`:34`–`:43`)
- Modify `sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden/cartography.yaml` — add a `sites:` block declaring the `frontier` site (retire the `deep_descent` route, or leave it inert)
- Modify `sidequest-server/tests/agents/subsystems/test_movement_sunden_characterization.py` — retarget node ids if Sünden migrates to namespaced ids (see decision below)
- Modify `sidequest-server/sidequest/dungeon/session_integration.py`, `sidequest/dungeon/seed_bootstrap.py`, `sidequest/game/pg/dungeon.py` call sites that pass `entrance_id`/`site_id` for the frontier site

**Migration decision (id namespacing for Sünden):** To keep the diff bounded and Sünden green, **Sünden's frontier site keeps `site_id="frontier"` and its storage uses the Task 2 default `site_id="frontier"`, but its NODE ids stay `entrance`/`expNNN.rN` for B1** (they are already unique within the single frontier store; the storage key, not the node id, provides site isolation). Full node-id namespacing (`frontier:entrance`) is a B2/B4 follow-up (noted) — it is NOT required for correctness because storage is `(session, site_id)`-keyed. This means: `SiteDescriptor.entrance_node_id` for the frontier site must resolve to the store's actual entrance id. Handle this by having `resolve_enter_site` load the graph and use `graph.entrance_id` when the declared entrance node isn't present (Sünden's legacy `entrance`). **Simplest correct rule:** the frontier site declares `attached_to: the_dropmouth`, and `resolve_enter_site` binds to `graph.entrance_id` (already `"entrance"` for Sünden via the bootstrap) rather than the namespaced form. Adjust `resolve_enter_site` (Task 4) to prefer `graph.entrance_id` if `site.entrance_node_id not in graph.nodes` — a loud, single fallback that is correct for the frontier-legacy case and harmless for bounded sites (whose entrance is the namespaced id).

**Interfaces:**
- Consumes: `SiteRegistry` (Task 1), `resolve_enter_site`/`resolve_exit_site` (Task 4), `site_enter_unresolved_span` (Task 4), `_cartography_for`/`_is_region_mode` (`movement.py:258`/`:270`), `_advance_colocated_peers` (`movement.py:286`), `_unresolved` (`movement.py:1212`), `snapshot.region_for(perspective=)` (`session.py:1331`).
- Produces: the movement dispatch resolves `action=="enter_site"`/`"exit_site"` via the registry; the §Q1 in-dungeon navigator (`:742`+) is UNCHANGED (in-scene navigation still traverses the graph). `resolved_via` values become `"site_enter"`/`"site_exit"` (the characterization tests update from `surface_descent`/`surface_ascent` to these — the OBSERVABLE outcome, `to_region`, is unchanged).

**Steps:**

- [ ] Re-run Task 3's characterization tests to confirm the green baseline: `cd sidequest-server && uv run pytest tests/agents/subsystems/test_movement_sunden_characterization.py -v -n0`.
- [ ] Add the Sünden `sites:` declaration to `sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden/cartography.yaml`. After the existing `routes:` block (the `Down the Rope`/`to_id: deep_descent` route at `:192`), add:
  ```yaml
  sites:
    - site_id: frontier
      name: "The Deep"
      archetype: megadungeon
      attached_to: the_dropmouth
      extent: frontier
  ```
  Leave the `deep_descent` route in place for now (inert once movement stops reading it) OR delete it — deletion is cleaner; if deleted, also confirm nothing else parses that route (grep content + `seam_route_for`). **Keep the route for this task** (lowest risk); a follow-up removes it.
- [ ] Update the characterization tests to the new `resolved_via` names (`site_enter`/`site_exit`) while keeping the SAME `to_region` assertions. This encodes the behavioral contract: same destination, new internal path.
- [ ] Refactor `run_movement_dispatch` (`movement.py:337`). Read `direction`/`exit_descriptor`/`action` from params at the top (`:356`):
  ```python
      action = str(dispatch.params.get("action", "") or "")
      direction = str(dispatch.params.get("direction", "") or "")
      exit_descriptor = str(dispatch.params.get("exit_descriptor", "") or "")
      site_descriptor = str(dispatch.params.get("site_descriptor", "") or "")
  ```
  Build the `SiteRegistry` once, next to the existing `cart` probe (`:373`):
  ```python
      from sidequest.game.sites import SiteRegistry, is_site_node_id
      site_registry = SiteRegistry.from_cartography(cart)
  ```
  Replace the region-mode seam rungs (`:386`–`:538` — the owned-seam, adjacent-seam, and entrance-ascent blocks) with two site-target branches placed BEFORE the region-mode lateral block (`:554`). The dispatch order becomes: (1) `exit_site` if the PC is inside a site; (2) `enter_site` from a world node; (3) existing lateral cartography travel; (4) `_defer_region_mode`; (5) §Q1 in-dungeon navigator (unchanged):
  ```python
      # --- Site EXIT: PC stands inside a site (pc_region is a site node) ---
      current = snapshot.region_for(perspective=player_name) or ""
      owning_site = site_registry.site_owning_node(current) if current else None
      # For the legacy frontier site whose nodes are un-namespaced ('entrance'/
      # 'expNNN.rN'), detect membership via the existing legacy-id detector —
      # is_procedural_region_id (seed_bootstrap.py:45-48) matches exactly the
      # legacy frontier namespace; no per-turn graph load needed:
      if owning_site is None and current and is_procedural_region_id(current):
          owning_site = site_registry.by_id(DEFAULT_SITE_ID)
      # (imports for this block: `from sidequest.dungeon.seed_bootstrap import
      # is_procedural_region_id` and `from sidequest.game.pg.dungeon import
      # DEFAULT_SITE_ID` — DEFAULT_SITE_ID = "frontier", Task 2. This shim is
      # Sünden-legacy-specific by design and dies with the B4 node-id
      # namespacing follow-up.)
      if owning_site is not None and action == "exit_site":
          try:
              crossing = resolve_exit_site(
                  snapshot=snapshot, player_name=player_name, site=owning_site,
                  cartography=cart, resolved_via="site_exit",
              )
          except SeamCrossingError as err:
              return _unresolved(snapshot=snapshot, player_name=player_name, reason=err.reason,
                                 from_region=current, direction=direction,
                                 exit_descriptor=exit_descriptor, available=[], surface=err.surface)
          _advance_colocated_peers(snapshot, acting_pc=player_name, from_region=current,
                                   to_region=crossing.to_region,
                                   additional_player_names=additional_player_names,
                                   resolved_via="site_exit")
          return SubsystemOutput(data={"to_region": crossing.to_region,
                                       "from_region": current, "resolved_via": "site_exit"})

      # --- Site ENTER: PC on a world node, action == enter_site ---
      if owning_site is None and action == "enter_site" and _is_region_mode(cart):
          site, ambiguous = site_registry.resolve_descriptor(current, site_descriptor)
          if ambiguous:
              names = ", ".join(s.name for s in site_registry.sites_for_node(current))
              return _unresolved(snapshot=snapshot, player_name=player_name,
                                 reason="ambiguous_site", from_region=current, direction=direction,
                                 exit_descriptor=site_descriptor, available=[],
                                 surface=f"Which way in — {names}?")
          if site is None:
              with site_enter_unresolved_span(pc_name=player_name, from_region=current,
                                              reason="no_matching_site", descriptor=site_descriptor):
                  pass
              return _defer_region_mode(snapshot=snapshot, player_name=player_name,
                                        from_region=current, direction=direction,
                                        exit_descriptor=site_descriptor)
          # Bounded sites materialize whole before binding (Task 12 wires this).
          if site.extent == "bounded":
              await _ensure_bounded_site_materialized(  # defined in Task 12; import lazily
                  site=site, dungeon_repository=dungeon_store, snapshot=snapshot, pack=pack,
              )
          try:
              crossing = resolve_enter_site(
                  snapshot=snapshot, player_name=player_name, site=site,
                  dungeon_repository=dungeon_store, resolved_via="site_enter",
                  direction=direction, exit_descriptor=site_descriptor,
              )
          except SeamCrossingError as err:
              return _unresolved(snapshot=snapshot, player_name=player_name, reason=err.reason,
                                 from_region=current, direction=direction,
                                 exit_descriptor=site_descriptor, available=[], surface=err.surface)
          _advance_colocated_peers(snapshot, acting_pc=player_name, from_region=current,
                                   to_region=crossing.to_region,
                                   additional_player_names=additional_player_names,
                                   resolved_via="site_enter")
          return SubsystemOutput(data={"to_region": crossing.to_region,
                                       "from_region": current, "resolved_via": "site_enter"})
  ```
  **For B1, guard the `_ensure_bounded_site_materialized` call behind a `try/except ImportError` or a `NotImplementedError` surfaced as `_unresolved(reason="bounded_not_ready")`** so Task 6 lands green before Task 12 exists; Task 12 replaces the guard with the real call. Simplest: in Task 6, if `site.extent == "bounded"`, return `_unresolved(reason="bounded_site_pending", surface="That door isn't ready yet.")`; Task 12 swaps this for the materialize call. (Sünden is `frontier`, so B1's live path never hits this.)
  Update imports (`:34`–`:43`): add `from sidequest.game.sites.enter_site import resolve_enter_site`, `from sidequest.game.sites.exit_site import resolve_exit_site`, `from sidequest.telemetry.spans.site import site_enter_unresolved_span`. Leave the §Q1 navigator (`:742`+) and `_defer_region_mode` untouched.
- [ ] Update the §Q1 step-2b surface→deep handoff (`:667`–`:740`, the room-graph-world descent via `resolve_deep_descent`): this path is for room-graph (non-region-mode) worlds. Since Sünden is region-mode, the migration routes through the region-mode block above. Leave the §Q1 step-2b block AS-IS for now (it's dead for Sünden post-migration but harmless; a follow-up removes `deep_descent`).
- [ ] Run: `cd sidequest-server && uv run pytest tests/agents/subsystems/test_movement_sunden_characterization.py -v -n0` — expect all pass (same `to_region`, new `resolved_via`). Then run the full movement suite: `uv run pytest tests/agents/subsystems/test_movement*.py -v -n0`. Some tests asserting `resolved_via=="surface_descent"` on the region-mode path may need updating to `"site_enter"` — update them (same behavioral contract).
- [ ] **Verify Sünden end-to-end** (not just unit tests): start the stack (`just server` etc. per playtest ops), run `just playtest-scenario sunden_descend_trace`, and confirm the party crosses into the deep and navigates (the scenario's comment-documented spans: `movement.resolved onward_ring_drained=True`, no `movement.unresolved`). This is the load-bearing Sünden-stays-green check.
- [ ] Lint/format touched server files. Commit server changes on the server branch and content changes on a content branch (branch-first, own Bash calls):
  ```bash
  cd sidequest-content && git checkout -b feat/track-b-sunden-frontier-site
  ```
  ```bash
  cd sidequest-content && git add genre_packs/caverns_and_claudes/worlds/beneath_sunden/cartography.yaml && git commit -m "feat(beneath_sunden): declare the deep as the first frontier site (Track B B1)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
  ```
  ```bash
  cd sidequest-server && git add sidequest/agents/subsystems/movement.py tests/agents/subsystems/ && git commit -m "refactor(sites): movement ladder -> SiteRegistry x enter/exit resolvers; Sünden frontier site (Track B B1 RISKY CUTOVER)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
  ```

---

## Task 7: **[RISKY CUTOVER]** Scene context replaces binary map arbitration; dissolve the beneath_sunden fence

Replace `_descent_phase`'s `"n/a"|"surface"|"deep"` binary (`map_emit.py:928`) with a per-connection scene context (`world | site:<site_id>`), and dissolve the `region_projection.applies_to` hardcode (`region_projection.py:110`) so any site scene projects its map. Sünden must still emit its deep map — now as a site scene.

**Files:**
- Modify `sidequest-server/sidequest/server/websocket_handlers/map_emit.py` — `_descent_phase` (`:928`), `_load_dungeon_map_context` (`:887`), `_maybe_emit_dungeon_map` (`:1034`), `_maybe_build_runtime_cavern_payload` (`:113`, the `applies_to` fence)
- Modify `sidequest-server/sidequest/dungeon/region_projection.py` — `applies_to` (`:110`) generalized OR bypassed for site scenes
- Create `sidequest-server/sidequest/server/scene_context.py` (the scene resolver)
- Create `sidequest-server/tests/server/test_scene_context.py`

**Interfaces:**
- Consumes: `SiteRegistry` (Task 1); `_resolve_connection_pc_region(snapshot, player_id)` (`map_emit.py:860`); `sd.genre_pack`/`sd.world_slug`/`sd.dungeon_repository` (`_SessionData`); `snapshot.region_for`.
- Produces (consumed by Tasks 8, 9): `resolve_scene_context(*, sd, snapshot, player_id) -> SceneContext` where `SceneContext` is `("world", None)` or `("site", site_id)`. `_maybe_emit_dungeon_map` emits for ANY site scene (not just beneath_sunden), keyed by `site_id`.

**Steps:**

- [ ] Write the failing test `tests/server/test_scene_context.py`:
  ```python
  """Per-connection scene context (world | site:<id>) — Track B, Task 7."""
  from sidequest.server.scene_context import SceneContext, resolve_scene_context

  def test_world_scene_when_pc_on_cartography(sunden_sd, sunden_snapshot_surface) -> None:
      ctx = resolve_scene_context(sd=sunden_sd, snapshot=sunden_snapshot_surface, player_id="p1")
      assert ctx == SceneContext(kind="world", site_id=None)

  def test_site_scene_when_pc_in_deep(sunden_sd, sunden_snapshot_in_deep) -> None:
      ctx = resolve_scene_context(sd=sunden_sd, snapshot=sunden_snapshot_in_deep, player_id="p1")
      assert ctx.kind == "site" and ctx.site_id == "frontier"
  ```
  (Reuse the `_SessionData`/snapshot doubles from the existing `map_emit` tests — grep `tests/server/` for `_descent_phase`/`_maybe_emit_dungeon_map`.)
- [ ] Run: expect `ModuleNotFoundError`.
- [ ] Create `sidequest/server/scene_context.py`:
  ```python
  """Per-connection scene context: world (on cartography) vs site (inside a
  site's graph). Replaces map_emit._descent_phase's surface|deep binary."""
  from __future__ import annotations

  from dataclasses import dataclass
  from typing import Literal

  from sidequest.game.sites import SiteRegistry


  @dataclass(frozen=True)
  class SceneContext:
      kind: Literal["world", "site"]
      site_id: str | None


  def _cartography_for(sd):
      world = getattr(getattr(sd, "genre_pack", None), "worlds", {}).get(
          getattr(sd, "world_slug", "") or ""
      )
      return getattr(world, "cartography", None)


  def resolve_scene_context(*, sd, snapshot, player_id: str) -> SceneContext:
      """A connection is in a site scene iff its PC's region is a node in some
      site's graph. Owner-namespaced nodes resolve directly; the legacy frontier
      site (un-namespaced 'entrance'/'expNNN.rN') resolves via the store."""
      from sidequest.server.websocket_handlers.map_emit import _resolve_connection_pc_region

      _pc, pc_region = _resolve_connection_pc_region(snapshot, player_id)
      if not pc_region:
          return SceneContext(kind="world", site_id=None)
      reg = SiteRegistry.from_cartography(_cartography_for(sd))
      owner = reg.site_owning_node(pc_region)
      if owner is not None:
          return SceneContext(kind="site", site_id=owner.site_id)
      repo = getattr(sd, "dungeon_repository", None)
      if repo is not None:
          for site in reg.sites_for_node(""):  # all sites; sites_for_node("") == []
              pass
      # legacy frontier: check each frontier site's store for membership
      for site in [s for s in reg._sites if s.extent == "frontier"]:
          if repo is not None and pc_region in repo.load_map(
              entrance_id=pc_region, site_id=site.site_id
          ).nodes:
              return SceneContext(kind="site", site_id=site.site_id)
      return SceneContext(kind="world", site_id=None)
  ```
  (Clean up the dead `sites_for_node("")` loop; it is shown only to flag the legacy path. The frontier-store membership check is the load-bearing branch.)
- [ ] Run the scene-context test — expect pass.
- [ ] Rewire `map_emit.py`. Replace `_descent_phase` (`:928`) body to delegate: `return "site" if resolve_scene_context(...).kind == "site" else ("n/a" if _load_dungeon_map_context(sd) is None else "world")` — but simpler: introduce the scene context at the two call sites (`_maybe_emit_dungeon_map` `:1034`, `_maybe_emit_cartography_map` `:1143`) and gate on `ctx.kind`. In `_maybe_emit_dungeon_map`, replace the `applies_to`-driven `_load_dungeon_map_context` gate + the `pc_region not in graph.nodes` surface check (`:1087`–`:1112`) with:
  ```python
      ctx = resolve_scene_context(sd=sd, snapshot=snapshot, player_id=player_id)
      if ctx.kind != "site":
          return  # world scene -> cartography emit owns the map
      site_id = ctx.site_id
      graph = sd.dungeon_repository.load_map(entrance_id=..., site_id=site_id)
      # ... build payload keyed by site_id (Task 8 adds site fields to the payload)
  ```
  In `_maybe_emit_cartography_map` (`:1143`), replace the `if _descent_phase(sd, snapshot) == "deep"` gate (`:1179`) with `if resolve_scene_context(sd=sd, snapshot=snapshot, player_id=getattr(sd,"player_id","")).kind == "site": ...stand down...`. **Do NOT touch the Track A cartography treatment block.**
- [ ] Generalize the runtime cavern fence. In `_maybe_build_runtime_cavern_payload` (`:113`) and `_load_dungeon_map_context` (`:906`), replace the `applies_to(sd.genre_slug, sd.world_slug)` gate with a site-scene check: the payload builds when the room is a node in the current scene's site store. Keep the `SIDEQUEST_OUTPUT_DIR` guard (`:191`) and the `load_masks()` read, but call `load_masks(site_id=ctx.site_id)`. In `region_projection.py`, change `applies_to` (`:110`) to accept an optional site check OR add a sibling `applies_to_site(...)`; the least-churn approach is to leave `applies_to` for the legacy Sünden narrator-prompt projection and add scene-context gating at the map_emit call sites only. **Minimal change:** keep `region_projection.applies_to` but stop map_emit from depending on it — gate on `resolve_scene_context().kind == "site"` instead.
- [ ] Run: `cd sidequest-server && uv run pytest tests/server/test_scene_context.py tests/server/ -k "map_emit or dungeon_map or cartography_map or scene" -v -n0`. Update any `_descent_phase`-asserting test to the scene-context outcome.
- [ ] **Verify Sünden**: `just playtest-scenario sunden_descend_trace` and confirm the deep map still emits (span `dungeon.map_emitted`, now under a site scene) and the surface cartography stands down in the deep.
- [ ] Lint/format; commit:
  ```bash
  cd sidequest-server && git add sidequest/server/scene_context.py sidequest/server/websocket_handlers/map_emit.py sidequest/dungeon/region_projection.py tests/server/test_scene_context.py tests/server/ && git commit -m "refactor(sites): per-connection scene context replaces surface|deep map arbitration (Track B B1 RISKY CUTOVER)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
  ```

---

## Task 8: **[RISKY CUTOVER]** Protocol `DUNGEON_MAP → SITE_MAP` (one cutover, no alias)

Rename the message + add site fields. ONE cutover — server and UI both controlled. The cutover surface is small (verified): enum member, message classes, the `_KIND_TO_MESSAGE_CLS` registry, the union member, and the single `emit_fn(msg, "DUNGEON_MAP")` label. Everything else referencing DUNGEON_MAP is comments.

**Files:**
- Modify `sidequest-server/sidequest/protocol/enums.py` — `DUNGEON_MAP` (`:138`) → `SITE_MAP`
- Modify `sidequest-server/sidequest/protocol/messages.py` — `DungeonMap*` classes (`:1640`–`:1699`) → `SiteMap*`; `_Phase1Variant` union member (`:1838`); `_KIND_TO_MESSAGE_CLS` (`:1910`); add `site_id`/`site_name`/`archetype`/`extent` to the payload
- Modify `sidequest-server/sidequest/server/websocket_handlers/map_emit.py` — `emit_fn(msg, "DUNGEON_MAP")` (`:1140`) → `"SITE_MAP"`; build payload with the new fields
- Modify `sidequest-server/tests/protocol/test_enums.py` — `test_message_type_complete_count` (`:219`, assert `:297`) count + add a `SITE_MAP` wire-string test
- Create/modify `sidequest-server/tests/protocol/test_site_map_message.py`

**Interfaces:**
- Consumes: `MessageType` (`enums.py:20`); `ProtocolBase`; the discriminated-union pattern (`type: Literal[MessageType.SITE_MAP] = MessageType.SITE_MAP`, `Field(discriminator="type")`).
- Produces (consumed by Task 9): `SiteMapMessage`/`SiteMapPayload` with `current_location`, `region`, `explored: list[SiteMapLocation]`, `fog_bounds`, plus NEW `site_id: str`, `site_name: str`, `archetype: str`, `extent: str`. Wire string `"SITE_MAP"`.

**Steps:**

- [ ] Write/adjust the failing tests. In `tests/protocol/test_enums.py`, bump the count assertion (`:297`) from `59` to `59` (unchanged — a RENAME, not an addition; `DUNGEON_MAP` becomes `SITE_MAP`, so `len(MessageType)` is stable) and update the docstring changelog line + any test asserting `MessageType.DUNGEON_MAP` to `MessageType.SITE_MAP`. Create `tests/protocol/test_site_map_message.py`:
  ```python
  from sidequest.protocol.enums import MessageType
  from sidequest.protocol.messages import SiteMapMessage, SiteMapPayload

  def test_site_map_wire_type_and_fields() -> None:
      msg = SiteMapMessage(
          payload=SiteMapPayload(current_location="frontier:entrance", region="frontier:entrance",
                                 site_id="frontier", site_name="The Deep", archetype="megadungeon",
                                 extent="frontier"),
      )
      assert msg.type == MessageType.SITE_MAP
      assert msg.model_dump()["type"] == "SITE_MAP"
      assert msg.payload.site_id == "frontier"

  def test_dungeon_map_symbol_is_gone() -> None:
      import sidequest.protocol.messages as m
      assert not hasattr(m, "DungeonMapMessage"), "one cutover, no alias"
  ```
- [ ] Run: `cd sidequest-server && uv run pytest tests/protocol/test_site_map_message.py -v -n0` — expect `ImportError: SiteMapMessage`.
- [ ] In `enums.py:138`, rename `DUNGEON_MAP = "DUNGEON_MAP"` → `SITE_MAP = "SITE_MAP"` (update the comment block `:132`–`:137` to describe the site frame).
- [ ] In `messages.py`, rename `DungeonMapExit`→`SiteMapExit`, `DungeonMapLocation`→`SiteMapLocation`, `DungeonMapPayload`→`SiteMapPayload`, `DungeonMapMessage`→`SiteMapMessage`. Add to `SiteMapPayload` (after `fog_bounds`, `:1685`):
  ```python
      site_id: str = ""
      site_name: str = ""
      archetype: str = ""
      extent: str = ""
  ```
  Update the `type` Literal (`:1697`) to `MessageType.SITE_MAP`, the union member (`:1838`), and `_KIND_TO_MESSAGE_CLS` (`:1910`) key to `"SITE_MAP": SiteMapMessage`.
- [ ] In `map_emit.py`: rename the local imports/usages of `DungeonMap*` (`:961`, `:981`–`:985`, `:1061`, `:1114`) to `SiteMap*`; change `emit_fn(msg, "DUNGEON_MAP")` (`:1140`) → `emit_fn(msg, "SITE_MAP")`; populate the new payload fields from the `SceneContext` + `SiteRegistry` (site_id/site_name/archetype/extent from the descriptor).
- [ ] Run: `cd sidequest-server && uv run pytest tests/protocol/ -v -n0` (use `-n0` — span-count tests deadlock under xdist). Expect pass. Then grep for stragglers: `grep -rn "DungeonMap\|DUNGEON_MAP" sidequest/ tests/` and fix any remaining non-comment references.
- [ ] Lint/format; commit:
  ```bash
  cd sidequest-server && git add sidequest/protocol/enums.py sidequest/protocol/messages.py sidequest/server/websocket_handlers/map_emit.py tests/protocol/ && git commit -m "feat(protocol): DUNGEON_MAP -> SITE_MAP one cutover + site_id/name/archetype/extent (Track B B1 RISKY CUTOVER)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
  ```

---

## Task 9: **[RISKY CUTOVER]** UI SITE_MAP handling + scene-keyed mapData + breadcrumb (158-36)

Cut the client over to `SITE_MAP`, split the single clobberable `mapData` slot into scene-keyed state (world map + active site map coexist), and add the "you are inside ⟨site⟩ at ⟨node⟩" breadcrumb — the structural 158-36 fix.

**Files:**
- Modify `sidequest-ui/src/types/protocol.ts` — `DUNGEON_MAP` (`:23`) → `SITE_MAP`
- Modify `sidequest-ui/src/lib/dungeonMap.ts` — rename to site-map shape + add site fields (or create `src/lib/siteMap.ts`)
- Modify `sidequest-ui/src/App.tsx` — `DUNGEON_MAP` handler (`:1281`), `mapData` state (`:378`) → scene-keyed
- Modify `sidequest-ui/src/components/GameBoard/widgets/MapWidget.tsx` — site-scene foreground selection + breadcrumb header (`:248` branch)
- Create/modify UI tests `sidequest-ui/src/__tests__/siteMap.test.ts(x)` + a MapWidget breadcrumb test
- Verify MobileTabView TABS (`MobileTabView.tsx:33`) + widgetRegistry (`widgetRegistry.ts:80`) + `rightGroupOrder` (`GameBoard.tsx:890`) unchanged (the Map tab itself doesn't change — only its content)

**Interfaces:**
- Consumes: `GameMessage` (`src/types/protocol.ts:146`), `MapState`/`ExploredLocation` (`MapOverlay.tsx`), the existing `dungeonMapToMapState` adapter (`dungeonMap.ts:83`).
- Produces: `App.tsx` routes `SITE_MAP` into a scene-keyed map store `{ world: MapState | null, site: (MapState & {siteId, siteName, archetype}) | null }`; `MapWidget` shows the site map when a site scene is active, with a breadcrumb drilling out to the world map. The clobber class (surface-vs-deep, site-vs-site) dies structurally.

**Steps:**

- [ ] Write the failing test `src/__tests__/siteMap.test.tsx` (adapt the existing dungeonMap test — grep `src/__tests__` for `dungeonMap`/`isDungeonMapPayload`):
  ```ts
  import { isSiteMapPayload, siteMapToMapState } from "@/lib/siteMap";

  test("site map payload carries site metadata into MapState", () => {
    const payload = {
      current_location: "frontier:entrance", region: "frontier:entrance",
      explored: [{ id: "frontier:entrance", name: "Entrance", room_exits: [], is_current_room: true }],
      site_id: "frontier", site_name: "The Deep", archetype: "megadungeon", extent: "frontier",
    };
    expect(isSiteMapPayload(payload)).toBe(true);
    const state = siteMapToMapState(payload);
    expect(state.siteId).toBe("frontier");
    expect(state.explored[0].x).toBe(0);
  });
  ```
- [ ] Run: `cd sidequest-ui && npx vitest run src/__tests__/siteMap.test.tsx` — expect module-not-found.
- [ ] In `src/types/protocol.ts`, rename `DUNGEON_MAP: "DUNGEON_MAP"` (`:23`) → `SITE_MAP: "SITE_MAP"`.
- [ ] Rename `src/lib/dungeonMap.ts` → `src/lib/siteMap.ts` (or add exports): `DungeonMapPayload` → `SiteMapPayload` with `site_id`/`site_name`/`archetype`/`extent`; `isDungeonMapPayload` → `isSiteMapPayload`; `dungeonMapToMapState` → `siteMapToMapState` returning `MapState & { siteId; siteName; archetype; extent }`.
- [ ] In `App.tsx`: replace the single `mapData` slot (`:378`) with scene-keyed state:
  ```tsx
  const [worldMap, setWorldMap] = useState<MapState | null>(null);
  const [siteMap, setSiteMap] = useState<(MapState & { siteId: string; siteName: string; archetype: string; extent: string }) | null>(null);
  ```
  Route `MAP_UPDATE` (`:1269`) → `setWorldMap(...)`; the `SITE_MAP` handler (was `DUNGEON_MAP` `:1281`) → `setSiteMap(siteMapToMapState(payload))`; `TACTICAL_GRID` (`:1303`) patches into whichever map holds the room (prefer `siteMap`, fall back to `worldMap`). Pass both to `GameBoard` (a new `siteMap` prop alongside `mapData={worldMap}`), and MapWidget selects the foreground.
- [ ] In `MapWidget.tsx`: add a `siteMap` prop; when present, render the site scene (Automapper) with a breadcrumb header `<div>You are inside {siteMap.siteName} · <button onClick={drillOut}>▲ {worldRegionName}</button></div>` above the Automapper (the 158-36 fix — a visible "drill out to the world map" affordance). "Drill out" is view-only (shows the world map); it does NOT move the party (travel stays prose-through-the-turn-barrier). Keep the orrery/cartography branches (Track A) untouched.
- [ ] Confirm the Map tab's three registration sites are unchanged (`WIDGET_REGISTRY.map` `:80`, `rightGroupOrder` `:890`, `MobileTabView TABS` `:33`) — this task changes tab CONTENT, not the tab itself, so no dual-registration edit is needed. Add a jsdom test asserting the Map tab renders the site breadcrumb when `siteMap` is set (reachability).
- [ ] Run: `cd sidequest-ui && npx vitest run src/__tests__/siteMap.test.tsx src/components/GameBoard/widgets/` and the App message-dispatch tests. Expect pass. Fix any `DUNGEON_MAP`/`dungeonMap` straggler: `grep -rn "DUNGEON_MAP\|dungeonMap\|DungeonMap" src/`.
- [ ] `cd sidequest-ui && npm run lint`.
- [ ] Commit (branch-first):
  ```bash
  cd sidequest-ui && git checkout -b feat/track-b-site-map
  ```
  ```bash
  cd sidequest-ui && git add src/types/protocol.ts src/lib/siteMap.ts src/App.tsx src/components/GameBoard/widgets/MapWidget.tsx src/__tests__/ && git commit -m "feat(map): SITE_MAP + scene-keyed mapData + site breadcrumb (Track B B1 RISKY CUTOVER, fixes 158-36)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
  ```

---

## Task 10: `site_archetypes.yaml` schema + loader wiring (B2, additive)

Introduce the per-genre archetype catalog binding interior algorithm / size ranges / grid dims / cell scale. Genre-tier file, loaded by the GENERIC loader (unlike `themes/`, which is deliberately standalone). Distinct filename to avoid the `archetypes.yaml` (chargen `NpcArchetype`) collision.

**Files:**
- Create `sidequest-server/sidequest/genre/models/site_archetype.py` (`SiteArchetype` model)
- Modify `sidequest-server/sidequest/genre/loader.py` — read `site_archetypes.yaml` (`GENRE_PACK_ROOT_EXTENSION_FILES` `:121` + a read site in `load_genre_pack` `:2245`+) 
- Modify `sidequest-server/sidequest/genre/models/pack.py` — `GenrePack.site_archetypes: dict[str, SiteArchetype]` (`:389`)
- Modify `sidequest-content/pack_schema.yaml` — add `site_archetypes` to `genre_pack.extensions`
- Create `sidequest-server/tests/genre/test_site_archetype_loader.py`
- Verify `tests/cli/validate/test_pack_schema_loader_drift_113_2.py` still passes (the loader↔schema drift guard)

**Interfaces:**
- Consumes: the loader's optional-genre-file allowlist mechanism (`GENRE_PACK_ROOT_EXTENSION_FILES`, `loader.py:121`; kept in lockstep with `pack_schema.yaml`'s `genre_pack.extensions` via `test_pack_schema_loader_drift_113_2.py`); `ALGORITHMS` keys (`sidequest/dungeon/interiors/generator.py:17` — `cellular`/`depthfirst`/`prim`/`roomcorridor`).
- Produces (consumed by Tasks 11, 12): `SiteArchetype` with `archetype_id`, `interior_algorithm` (validated ∈ ALGORITHMS), `room_count_min`/`room_count_max`, `grid_width`/`grid_height`, `cell_scale_feet`, `room_vocabulary: list[str]`, `feature_palette: list[str]`. `GenrePack.site_archetypes` dict keyed by `archetype_id`.

**Steps:**

- [ ] Write the failing test `tests/genre/test_site_archetype_loader.py` (synthetic pack dir with a `site_archetypes.yaml`; monkeypatch nothing — it's a pure load test):
  ```python
  """site_archetypes.yaml loads into GenrePack.site_archetypes (Track B B2)."""
  from sidequest.genre.models.site_archetype import SiteArchetype

  def test_site_archetype_validates_algorithm() -> None:
      a = SiteArchetype.model_validate({
          "archetype_id": "tavern", "interior_algorithm": "roomcorridor",
          "room_count_min": 3, "room_count_max": 6,
          "grid_width": 15, "grid_height": 20, "cell_scale_feet": 5,
          "room_vocabulary": ["common room", "kitchen", "cellar"],
          "feature_palette": ["hearth", "bar", "stairs"],
      })
      assert a.interior_algorithm == "roomcorridor"

  def test_unknown_algorithm_fails_loud() -> None:
      import pytest
      with pytest.raises(ValueError):
          SiteArchetype.model_validate({"archetype_id": "x", "interior_algorithm": "nope",
                                        "room_count_min": 1, "room_count_max": 1,
                                        "grid_width": 5, "grid_height": 5, "cell_scale_feet": 5})

  def test_loader_populates_site_archetypes(synthetic_pack_with_site_archetypes) -> None:
      from sidequest.genre.loader import load_genre_pack
      pack = load_genre_pack(synthetic_pack_with_site_archetypes)
      assert "tavern" in pack.site_archetypes
  ```
  (Build `synthetic_pack_with_site_archetypes` in a local conftest copying a minimal valid pack skeleton + a `site_archetypes.yaml`; reuse the pack-skeleton helper other loader tests use — grep `tests/genre/` for `load_genre_pack` fixtures.)
- [ ] Run: expect failures.
- [ ] Create `sidequest/genre/models/site_archetype.py`:
  ```python
  """SiteArchetype — a genre's site catalog entry (interior algorithm, size,
  grid dims). Content, not engine code (Jade doctrine): a new archetype is YAML."""
  from __future__ import annotations

  from pydantic import BaseModel, Field, field_validator

  from sidequest.dungeon.interiors import ALGORITHMS


  class SiteArchetype(BaseModel):
      model_config = {"extra": "allow"}

      archetype_id: str
      interior_algorithm: str
      room_count_min: int = Field(ge=1)
      room_count_max: int = Field(ge=1)
      grid_width: int = Field(ge=5)
      grid_height: int = Field(ge=5)
      cell_scale_feet: int = Field(ge=1, default=5)
      room_vocabulary: list[str] = Field(default_factory=list)
      feature_palette: list[str] = Field(default_factory=list)

      @field_validator("interior_algorithm")
      @classmethod
      def _known_algorithm(cls, v: str) -> str:
          if v not in ALGORITHMS:
              raise ValueError(
                  f"interior_algorithm {v!r} not in {sorted(ALGORITHMS)}"
              )
          return v
  ```
  (Confirm `from sidequest.dungeon.interiors import ALGORITHMS` is importable — `generator.py:17` defines it; check `interiors/__init__.py` re-exports it, else import `from sidequest.dungeon.interiors.generator import ALGORITHMS`.)
- [ ] Add `site_archetypes: dict[str, SiteArchetype] = Field(default_factory=dict)` to `GenrePack` (`pack.py:389`+).
- [ ] Wire the generic loader. Add `"site_archetypes.yaml"` to `GENRE_PACK_ROOT_EXTENSION_FILES` (`loader.py:121`), and in `load_genre_pack` add a read parallel to the other optional-genre-file reads (`:2281`-ish): load the YAML list, build `{a["archetype_id"]: SiteArchetype.model_validate(a)}`, pass into the `GenrePack(...)` construction.
- [ ] Add `site_archetypes` under `genre_pack.extensions` in `sidequest-content/pack_schema.yaml` (mirror the `bestiary: {files: [bestiary.yaml]}` shape at `:91`).
- [ ] Run: `cd sidequest-server && uv run pytest tests/genre/test_site_archetype_loader.py tests/cli/validate/test_pack_schema_loader_drift_113_2.py -v -n0` — expect pass (drift guard confirms loader↔schema lockstep).
- [ ] Lint/format; commit (server + content on their branches):
  ```bash
  cd sidequest-content && git add pack_schema.yaml && git commit -m "feat(schema): register site_archetypes.yaml genre extension (Track B B2)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
  ```
  ```bash
  cd sidequest-server && git add sidequest/genre/models/site_archetype.py sidequest/genre/loader.py sidequest/genre/models/pack.py tests/genre/test_site_archetype_loader.py && git commit -m "feat(sites): site_archetypes.yaml catalog + generic-loader wiring (Track B B2)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
  ```

---

## Task 11: Bounded materialization — whole site in one transaction

Materialize a `bounded` site's ENTIRE graph + grids in ONE committed transaction at first entry, deterministic from `blake2b(campaign_seed, site_id)`, using the archetype's dims. No frontier worker, no lookahead. Wire it into `resolve_enter_site` (replace Task 6's `bounded_site_pending` guard). Emit `site.materialize.*` spans to `turn_telemetry`.

**Files:**
- Create `sidequest-server/sidequest/dungeon/bounded_site.py` (`materialize_bounded_site` + `ensure_bounded_site_materialized`)
- Modify `sidequest-server/sidequest/dungeon/materializer.py` — parameterize `DEFAULT_INTERIOR_WIDTH`/`HEIGHT` (`:214`) via the archetype in `_region_interior_seed`/tactical stage; add a `site_id` to the seed input
- Modify `sidequest-server/sidequest/telemetry/spans/site.py` — add `site.materialize.begin/commit/skip` spans (mirrored)
- Modify `sidequest-server/sidequest/agents/subsystems/movement.py` — replace the Task 6 `bounded_site_pending` guard with `await ensure_bounded_site_materialized(...)`
- Create `sidequest-server/tests/dungeon/test_bounded_site.py`

**Interfaces:**
- Consumes: `MaterializationRequest.build(...)` (`materializer.py:583`); `materialize(request, graph=, bundle=, palette=, dungeon_repository=, snapshot=, pack_tropes=, pack=)` (`materializer.py:2030`); `_region_interior_seed(campaign_seed, expansion_id, region_id)` (`materializer.py:291`, `blake2b(f"{campaign_seed}|{expansion_id}|{region_id}")`); `SiteArchetype` (Task 10); `DungeonRepository.get_campaign_seed(site_id=)`/`set_campaign_seed(seed, site_id=)`/`commit_expansion(..., site_id=)` (Task 2); `SiteDescriptor` (Task 1). Bootstrap model: `attach_dungeon_to_session` (`session_integration.py:97`, the fresh-seed-then-materialize flow at `:169`–`:203`).
- Produces (consumed by Task 6/12): `async def ensure_bounded_site_materialized(*, site: SiteDescriptor, archetype: SiteArchetype, dungeon_repository, snapshot, pack, bundle, palette) -> None` — idempotent (skips if the site's entrance node already exists); ONE transaction; deterministic. `materialize_bounded_site` builds the whole bounded graph (no frontier edges left open).

**Steps:**

- [ ] Write the failing test `tests/dungeon/test_bounded_site.py` — **monkeypatch `_resolve_world_dir` to tmp** (content-pollution hazard):
  ```python
  """Bounded site materializes whole, one transaction, deterministic (Track B B2)."""
  from __future__ import annotations

  import pytest

  from sidequest.game.sites import SiteDescriptor
  from sidequest.genre.models.site_archetype import SiteArchetype

  _TAVERN = SiteDescriptor(site_id="gilded_boar", name="The Gilded Boar", archetype="tavern",
                           attached_to="square", extent="bounded")
  _ARCH = SiteArchetype(archetype_id="tavern", interior_algorithm="roomcorridor",
                        room_count_min=3, room_count_max=6, grid_width=15, grid_height=20,
                        cell_scale_feet=5)

  @pytest.fixture(autouse=True)
  def _no_content_pollution(monkeypatch, tmp_path):
      monkeypatch.setattr("sidequest.dungeon.materializer._resolve_world_dir", lambda req: tmp_path)

  @pytest.mark.asyncio
  async def test_bounded_site_materializes_whole(fake_pg_repo, fake_snapshot, fake_pack) -> None:
      from sidequest.dungeon.bounded_site import ensure_bounded_site_materialized
      fake_pg_repo.set_campaign_seed(12345, site_id="gilded_boar")
      await ensure_bounded_site_materialized(
          site=_TAVERN, archetype=_ARCH, dungeon_repository=fake_pg_repo,
          snapshot=fake_snapshot, pack=fake_pack, bundle=..., palette=...,
      )
      graph = fake_pg_repo.load_map(entrance_id="gilded_boar:entrance", site_id="gilded_boar")
      assert "gilded_boar:entrance" in graph.nodes
      assert 3 <= len(graph.nodes) <= 7  # entrance + room_count rooms, bounded
      # No open frontier edges -> load_frontier is empty for a bounded site.
      assert fake_pg_repo.load_frontier(site_id="gilded_boar") == []

  @pytest.mark.asyncio
  async def test_bounded_site_is_deterministic(fake_pg_repo_factory) -> None:
      from sidequest.dungeon.bounded_site import ensure_bounded_site_materialized
      # Same seed + site_id -> identical node id set across two fresh repos.
      ...  # materialize into two repos seeded 12345/"gilded_boar"; assert node sets equal

  @pytest.mark.asyncio
  async def test_idempotent_second_entry_skips(fake_pg_repo, fake_snapshot, fake_pack) -> None:
      from sidequest.dungeon.bounded_site import ensure_bounded_site_materialized
      fake_pg_repo.set_campaign_seed(12345, site_id="gilded_boar")
      await ensure_bounded_site_materialized(site=_TAVERN, archetype=_ARCH, dungeon_repository=fake_pg_repo, snapshot=fake_snapshot, pack=fake_pack, bundle=..., palette=...)
      count1 = len(fake_pg_repo.load_map(entrance_id="gilded_boar:entrance", site_id="gilded_boar").nodes)
      await ensure_bounded_site_materialized(site=_TAVERN, archetype=_ARCH, dungeon_repository=fake_pg_repo, snapshot=fake_snapshot, pack=fake_pack, bundle=..., palette=...)
      count2 = len(fake_pg_repo.load_map(entrance_id="gilded_boar:entrance", site_id="gilded_boar").nodes)
      assert count1 == count2
  ```
  (This needs a real pg repo or a faithful in-memory `DungeonRepository` double with `commit_expansion`/`load_map`/`load_frontier`/`get_campaign_seed`/`set_campaign_seed` all `site_id`-aware. Prefer the real `PgDungeonRepository` against the test DB — read `tests/game/pg/conftest.py` for the fixture — since bounded materialization exercises the transaction boundary that matters.)
- [ ] Run: expect `ModuleNotFoundError: sidequest.dungeon.bounded_site`.
- [ ] Add `site.materialize.begin/commit/skip` spans to `telemetry/spans/site.py` (same mirrored pattern; `component="sites"`, `op="site.materialize.<phase>"`, fields `site_id`, `archetype`, `node_count`).
- [ ] Create `sidequest/dungeon/bounded_site.py`. Model the flow on `attach_dungeon_to_session` (`session_integration.py:169`–`:203`) but: (a) key everything by `site.site_id`; (b) drive room_count from the archetype (bounded burst = `room_count_max`, `lookahead_breadth=0` so no frontier edges survive); (c) use archetype `grid_width`/`grid_height` for interior dims; (d) wrap the whole build in ONE `dungeon_repository.transaction()` so no partial site is ever visible; (e) idempotency: return early if `load_map(entrance_id=site.entrance_node_id, site_id=site.site_id).nodes` already contains the entrance.
  ```python
  """Bounded site materialization — whole graph + grids in ONE transaction."""
  from __future__ import annotations

  from typing import TYPE_CHECKING, Any

  from sidequest.dungeon.materializer import materialize  # + MaterializationRequest
  from sidequest.game.sites.namespacing import site_entrance_id
  from sidequest.telemetry.spans.site import (
      site_materialize_begin_span,
      site_materialize_commit_span,
      site_materialize_skip_span,
  )

  if TYPE_CHECKING:
      from sidequest.game.repository import DungeonRepository
      from sidequest.game.sites import SiteDescriptor
      from sidequest.genre.models.site_archetype import SiteArchetype


  async def ensure_bounded_site_materialized(
      *,
      site: SiteDescriptor,
      archetype: SiteArchetype,
      dungeon_repository: DungeonRepository | None,
      snapshot: Any,
      pack: Any,
      bundle: Any,
      palette: Any,
  ) -> None:
      if dungeon_repository is None:
          from sidequest.game.seams.base import SeamCrossingError
          raise SeamCrossingError(reason="no_site_store", surface=f"{site.name} cannot be opened.")
      entrance = site_entrance_id(site.site_id)
      existing = dungeon_repository.load_map(entrance_id=entrance, site_id=site.site_id)
      if entrance in existing.nodes:
          with site_materialize_skip_span(site_id=site.site_id, archetype=site.archetype):
              pass
          return
      seed = dungeon_repository.get_campaign_seed(site_id=site.site_id)
      if seed is None:
          # Deterministic per-site seed: derive from the session seed folded with
          # site_id so re-entry is reproducible without a random draw.
          import hashlib
          base = dungeon_repository.get_campaign_seed() or 0
          seed = int.from_bytes(
              hashlib.blake2b(f"{base}|{site.site_id}".encode(), digest_size=8).digest(), "big"
          )
          dungeon_repository.set_campaign_seed(seed, site_id=site.site_id)
      with site_materialize_begin_span(site_id=site.site_id, archetype=site.archetype) as span:
          span.set_attribute("seed", seed)
          span.set_attribute("room_count_max", archetype.room_count_max)
      # Build the whole bounded graph in ONE transaction (materialize() drives
      # the 5-stage pipeline; a bounded request uses burst=room_count_max and
      # lookahead_breadth=0 so no frontier edges remain open). See
      # materializer.materialize (:2030) + MaterializationRequest.build (:583).
      # ... assemble the seed graph (site entrance node) + MaterializationRequest,
      # then await materialize(request, graph=..., bundle=bundle, palette=palette,
      #     dungeon_repository=dungeon_repository, snapshot=snapshot,
      #     pack_tropes=pack, pack=pack) with site_id threaded into commit.
      committed = dungeon_repository.load_map(entrance_id=entrance, site_id=site.site_id)
      with site_materialize_commit_span(site_id=site.site_id, archetype=site.archetype) as span:
          span.set_attribute("node_count", len(committed.nodes))
  ```
  **Note for the implementer:** `materialize()` currently commits via the repo's `commit_expansion`/`transaction` WITHOUT a `site_id`. Thread `site_id` through: either (a) add a `site_id` field to `MaterializationRequest` and have `_stage_commit` pass it to `tx.commit_expansion(..., site_id=request.site_id)`, or (b) wrap the repo in a site-scoped adapter that fills `site_id` on every method. Option (a) is cleaner and localizes the change — add `site_id: str = ""` to `MaterializationRequest` (`:580`) and pass it at every `commit_expansion`/`put_frontier`/`commit` call in `_stage_commit` (`:1650`). Set `lookahead_breadth=0` in the bounded request so `_stage_attach` opens no frontier edges (verify by reading `_stage_attach` `:1306` — if it always opens edges, gate the frontier writes on `request.lookahead_breadth > 0`). Use `archetype.grid_width`/`grid_height` in place of `DEFAULT_INTERIOR_WIDTH`/`HEIGHT` (`:214`) — thread them through the request too (add `interior_width`/`interior_height` fields, default to the 49 constants for the frontier path).
- [ ] Replace the Task 6 `bounded_site_pending` guard in `movement.py` with the real call: look up the archetype (`pack.site_archetypes.get(site.archetype)`), fail loud if absent (`_unresolved(reason="unknown_archetype")`), else `await ensure_bounded_site_materialized(...)` before `resolve_enter_site`.
- [ ] Run: `cd sidequest-server && uv run pytest tests/dungeon/test_bounded_site.py -v -n0` — expect pass. Run the existing materializer suite to confirm the `site_id`/dims threading didn't break the frontier path: `uv run pytest tests/dungeon/ -v -n0`.
- [ ] Lint/format; commit:
  ```bash
  cd sidequest-server && git add sidequest/dungeon/bounded_site.py sidequest/dungeon/materializer.py sidequest/telemetry/spans/site.py sidequest/agents/subsystems/movement.py tests/dungeon/test_bounded_site.py && git commit -m "feat(sites): bounded-site materialization in one transaction, deterministic per site_id (Track B B2)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
  ```

---

## Task 12: Single-writer for site scenes — extend narrator location-write denial

The narrator must be denied location writes wherever the engine owns navigation. Today `/current_region` writes are denied for region-mode worlds (`apply_world_patch.py:182`) and the same-turn seam-crossing guard is keyed to the single `ENTRANCE_ID`/surface-owner (`narration_apply.py:259`). Parameterize both for site scenes.

**Files:**
- Modify `sidequest-server/sidequest/agents/tools/apply_world_patch.py` — the `/current_region` denial (`:182`–`:198`) to also deny when the acting connection is in a site scene
- Modify `sidequest-server/sidequest/server/narration_apply.py` — `_honors_same_turn_seam_crossing` (`:259`) to key off the current site's entrance/owner, not the global `ENTRANCE_ID`
- Create `sidequest-server/tests/agents/tools/test_apply_world_patch_site_scene.py`

**Interfaces:**
- Consumes: `SiteRegistry` (Task 1); `resolve_scene_context` (Task 7) OR a direct `site_owning_node(pc_region)` check; the existing `NavigationMode.region` denial path (`apply_world_patch.py:187`); `snapshot.region_transitions`/`region_for` (`narration_apply.py:289`–`:294`).
- Produces: `apply_world_patch` returns a recoverable error for `/current_region` in a site scene (mirrors the region-mode denial); `_honors_same_turn_seam_crossing` recognizes a same-turn `site.enter` crossing (PC on a site entrance node + a this-turn `region_transitions` receipt) and declines the clobber, parameterized per site.

**Steps:**

- [ ] Write the failing test `tests/agents/tools/test_apply_world_patch_site_scene.py`:
  ```python
  """Narrator /current_region write is denied inside a site scene (single-writer)."""
  def test_current_region_write_denied_in_site_scene(site_scene_tool_ctx) -> None:
      from sidequest.agents.tools.apply_world_patch import apply_world_patch  # match real entry
      result = apply_world_patch(args=..., ctx=site_scene_tool_ctx)  # PC inside gilded_boar
      assert result.is_error and not result.aborts  # recoverable
      assert site_scene_tool_ctx.otel_span.attributes.get("tool.world_patch.region_write_denied")
  ```
  (Match the real `apply_world_patch` call shape by reading `apply_world_patch.py` around `:150`–`:198`; build a `ctx` double whose PC region is a site node.)
- [ ] Run: expect the write to SUCCEED (denial not yet extended) → test fails.
- [ ] Extend the denial in `apply_world_patch.py`. In the `if args.path == "/current_region":` block (`:182`), after the region-mode check (`:190`), add a site-scene check: build a `SiteRegistry` from the world's cartography and deny if the acting PC's region is a site node (`site_owning_node(pc_region) is not None`). Reuse the existing `region_write_denied` span attribute + recoverable error shape.
- [ ] Parameterize `_honors_same_turn_seam_crossing` (`narration_apply.py:259`). Replace the `ENTRANCE_ID`-keyed clauses (`:289`–`:298`) with a site-aware version: the PC is on a site's entrance node (`SiteRegistry.site_owning_node(region).entrance_node_id == region` OR the legacy frontier entrance), there is a this-turn `region_transitions` receipt to that node, and `known_region_id` is that site's `attached_to`. Keep the region-mode-world precondition.
- [ ] Run: `cd sidequest-server && uv run pytest tests/agents/tools/test_apply_world_patch_site_scene.py tests/server/ -k "seam_crossing or narration_apply" -v -n0` — expect pass.
- [ ] Lint/format; commit:
  ```bash
  cd sidequest-server && git add sidequest/agents/tools/apply_world_patch.py sidequest/server/narration_apply.py tests/agents/tools/test_apply_world_patch_site_scene.py && git commit -m "feat(sites): extend narrator location-write denial + same-turn guard to site scenes (Track B B2)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
  ```

---

## Task 13: Tavern + vault archetype content + end-to-end enter/map/grid/exit

Author the tavern and vault archetypes and attach sites to world nodes, then prove the full loop: enter a tavern from a world node → get a SITE_MAP (local map) + TACTICAL_GRID (tactical grid) → exit back. This is the B2 acceptance target.

**Files:**
- Create `sidequest-content/genre_packs/tea_and_murder/site_archetypes.yaml` (tavern)
- Create `sidequest-content/genre_packs/space_opera/site_archetypes.yaml` (vault)
- Modify `sidequest-content/genre_packs/tea_and_murder/worlds/blackthorn_moor/cartography.yaml` — add a `sites:` block (tavern on `thornkirk`)
- Modify `sidequest-content/genre_packs/space_opera/worlds/aureate_span/cartography.yaml` — add a `sites:` block (vault on `underspine`)
- Create `sidequest-server/tests/server/test_site_enter_exit_handler.py` (handler-level wiring test)

**Interfaces:**
- Consumes: `SiteArchetype` schema (Task 10); the `sites:` field (Task 1); `run_movement_dispatch` `enter_site`/`exit_site` (Task 6/11); `_maybe_emit_dungeon_map`→SITE_MAP (Task 7/8); `_maybe_emit_tactical_grid` (`map_emit.py:305`) / `_maybe_build_runtime_cavern_payload` (`:113`).
- Produces: two authored archetypes + two site declarations; a handler test proving enter→SITE_MAP+TACTICAL_GRID→exit emits the right messages (STUB the intent-router pass per the flaky-test rule).

**Steps:**

- [ ] Author `tea_and_murder/site_archetypes.yaml` — a `tavern` archetype (`interior_algorithm: roomcorridor`, `grid_width: 15`, `grid_height: 20`, `cell_scale_feet: 5`, room vocab: common room/kitchen/cellar/private parlour, feature palette: hearth/bar/stairs). Author `space_opera/site_archetypes.yaml` — a `vault` archetype (`interior_algorithm: roomcorridor`, larger grid e.g. 25×25, cell_scale 5, room vocab: antechamber/reliquary/security-lock/data-core).
- [ ] Add the site declarations. In `blackthorn_moor/cartography.yaml`, add:
  ```yaml
  sites:
    - site_id: blackthorn_arms
      name: "The Blackthorn Arms"
      archetype: tavern
      attached_to: thornkirk
      extent: bounded
  ```
  (`thornkirk`'s description already narrates "The Blackthorn Arms pub" — natural fit.) In `aureate_span/cartography.yaml`, add a `routes:`/`sites:` pair attaching a `vault` to `underspine` (this world has no `routes:` today — adding `sites:` is sufficient; a seam Route is NOT required, the SiteDecl.attached_to IS the seam ownership):
  ```yaml
  sites:
    - site_id: kesh_vault
      name: "The Vaal-Kesh Vault"
      archetype: vault
      attached_to: underspine
      extent: bounded
  ```
- [ ] Write the handler wiring test `tests/server/test_site_enter_exit_handler.py` — **stub the intent-router pass** (feed a pre-built `enter_site` dispatch), drive the real turn-dispatch path (or `run_movement_dispatch` + the map-emit helpers directly), and assert: (1) after `enter_site`, the PC's region is the site entrance; (2) `_maybe_emit_dungeon_map` emits a `SITE_MAP` message with `site_id=="blackthorn_arms"`; (3) `_maybe_emit_tactical_grid`/`_maybe_build_runtime_cavern_payload` emits a `TACTICAL_GRID` for the entrance room; (4) after `exit_site`, the PC is back on `thornkirk` and the world map (cartography) owns the scene again. Use span assertions for the mechanical facts (`site.enter`/`site.materialize.commit`/`site.exit`).
  ```python
  @pytest.mark.asyncio
  async def test_tavern_enter_emits_site_map_and_grid(blackthorn_session, captured_frames) -> None:
      # blackthorn_session: real pack load of tea_and_murder/blackthorn_moor,
      # PC seated on 'thornkirk'; captured_frames collects emit_fn(msg, kind).
      await drive_movement(blackthorn_session, action="enter_site", site_descriptor="the blackthorn arms")
      kinds = [k for _m, k in captured_frames]
      assert "SITE_MAP" in kinds
      assert "TACTICAL_GRID" in kinds
      site_map = next(m for m, k in captured_frames if k == "SITE_MAP")
      assert site_map.payload.site_id == "blackthorn_arms"
      await drive_movement(blackthorn_session, action="exit_site")
      # world scene resumes -> MAP_UPDATE emitted, no SITE_MAP
      assert any(k == "MAP_UPDATE" for _m, k in captured_frames[-3:])
  ```
- [ ] Run: `cd sidequest-server && uv run pytest tests/server/test_site_enter_exit_handler.py -v -n0` — expect pass once the content + wiring are in place. (If the tactical grid needs `SIDEQUEST_OUTPUT_DIR`, set it to `tmp_path` in the fixture.)
- [ ] **Validate content**: `cd sidequest-server && uv run python -m sidequest.cli.validate pack ../sidequest-content/genre_packs/tea_and_murder` and `.../space_opera` — the archetype schema + site declarations must pass the pack validator (content invariants live here, not in pytest).
- [ ] **Verify end-to-end in the running stack**: start the stack, drive a tea_and_murder/blackthorn_moor session, walk into the pub, confirm the Map tab shows the tavern local map + tactical grid and the breadcrumb, then exit back to the world map.
- [ ] Commit content (content branch) + server test (server branch):
  ```bash
  cd sidequest-content && git add genre_packs/tea_and_murder/site_archetypes.yaml genre_packs/tea_and_murder/worlds/blackthorn_moor/cartography.yaml genre_packs/space_opera/site_archetypes.yaml genre_packs/space_opera/worlds/aureate_span/cartography.yaml && git commit -m "feat(sites): tavern (blackthorn_moor) + vault (aureate_span) archetypes end-to-end (Track B B2)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
  ```
  ```bash
  cd sidequest-server && git add tests/server/test_site_enter_exit_handler.py && git commit -m "test(sites): enter->SITE_MAP+TACTICAL_GRID->exit handler wiring (Track B B2)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
  ```

---

## Task 14: `tavern_enter_trace` headless playtest scenario + span-jsonl assertions

The per-track headless playtest scenario, modeled on `sunden_descend_trace.yaml`, verifying mechanics (never narration) via emitted spans. Runs LAST — it proves the whole B1+B2 chain end-to-end against the running server.

**Files:**
- Create `sidequest-content` is not the location — scenarios live in the ORCHESTRATOR repo: create `orc-quest` (this repo) `scenarios/tavern_enter_trace.yaml`
- (No code change; this is a scenario + a documented span-assertion checklist, matching the existing scenario convention where assertions are top-of-file comments verified out-of-band via `playtest.py --span-jsonl`.)

**Interfaces:**
- Consumes: the scenario schema (`name`, `genre`, `world`, `character.strategy`, `actions:`) — `scenarios/sunden_descend_trace.yaml`; the runner `scripts/playtest.py` (`--scenario`, `--span-jsonl`); `just playtest-scenario <file>` (`justfile:584`).
- Produces: `scenarios/tavern_enter_trace.yaml` with actions that walk into the Blackthorn Arms, look around the tavern interior, and leave — plus a top-of-file comment block naming the spans to assert (`site.enter`, `site.materialize.commit`, `SITE_MAP` emit / `dungeon.map_emitted`, `TACTICAL_GRID` / `tactical_grid.emitted`, `site.exit`; and the NEGATIVE: no `site.enter_unresolved`, no `movement.unresolved`).

**Steps:**

- [ ] Create `scenarios/tavern_enter_trace.yaml` (orchestrator repo):
  ```yaml
  # Tavern enter/exit trace — does a BOUNDED site materialize whole on entry,
  # project a SITE_MAP + TACTICAL_GRID, and exit cleanly back to the world map?
  #
  # Inspect afterward (Jaeger jsonl via --span-jsonl + turn_telemetry):
  #   - site.enter site_id=blackthorn_arms resolved_via=site_enter
  #   - site.materialize.commit site_id=blackthorn_arms node_count>=3  (bounded, whole)
  #   - dungeon.map_emitted (SITE_MAP) + tactical_grid.emitted  (both zoom regimes)
  #   - site.exit site_id=blackthorn_arms to_region=thornkirk
  #   - NO site.enter_unresolved / movement.unresolved / dispatch_engagement.movement.mismatch
  name: Tavern enter + exit trace — bounded site materialize, map, grid, return
  genre: tea_and_murder
  world: blackthorn_moor

  character:
    strategy: auto

  actions:
    - "I walk into the Blackthorn Arms."
    - "I look around the common room of the pub."
    - "I step through into the back of the tavern."
    - "I head back out to the village square."
  ```
- [ ] Run the scenario against the running stack: `just playtest-scenario tavern_enter_trace` (with `--span-jsonl` wired per `scripts/playtest.py`), then inspect the emitted span jsonl for the asserted spans. Confirm the bounded site materialized once (`site.materialize.commit` fires exactly once across re-entries), the SITE_MAP + TACTICAL_GRID emitted, and no unresolved/mismatch spans. (Verify mechanics via spans — never credit narration prose.)
- [ ] Commit (orchestrator repo — `scenarios/` is not self-mod-blocked; this is a trunk-based sprint/scenario file, commit directly or via a branch per local convention):
  ```bash
  cd /Users/slabgorb/Projects/oq-3 && git add scenarios/tavern_enter_trace.yaml && git commit -m "test(sites): tavern_enter_trace headless scenario with span assertions (Track B B2)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
  ```

---

## Follow-ups (OUT OF SCOPE for B1+B2 — do not implement here)

- **B3 — minted-on-the-fly sites (Yes-And):** the ADR-109 promotion path where an improvised interior the narrative demands becomes a durable minted site (not prose). Needs a mint entry point + narrator tool; NOT in this plan.
- **B4 — per-archetype grids + visual polish:** archetype-declared feature palettes rendered on the tactical grid, per-archetype room vocabulary in prose, distinct visual treatments per site type. B2 ships MINIMAL grid sizing (archetype width/height/cell_scale); the richer palette/vocabulary rendering is B4.
- **Full node-id namespacing for the frontier site:** B1 keeps Sünden's node ids un-namespaced (`entrance`/`expNNN.rN`) because storage is `(session, site_id)`-keyed and the frontier site is alone in its store. Migrating to `frontier:entrance`/`frontier:expNNN.rN` is a mechanical follow-up (touches `seed_bootstrap.is_procedural_region_id` `:48`, the lookahead worker's `_ENTRANCE_ID`, and `region_projection`).
- **Retire `deep_descent`/`surface_ascent`:** Task 6 leaves them registered and the §Q1 step-2b room-graph descent (`movement.py:667`) inert-but-present. A cleanup follow-up deletes `game/seams/deep_descent.py`, `surface_ascent.py`, `seam_route_via_adjacency`, `surface_owner_for_entrance`, and the `deep_descent` route from `beneath_sunden/cartography.yaml` once the site path is proven in playtests.
- **Weed-whack dead map models:** the spec's Migration section deletes `WorldGraph`/`SubGraph`/`GraphEdge`/`Terrain` and the unconsumed `tactical_grid` field on `ExploredLocation`. Track A owns this (the graph of record is `CartographyConfig`); not Track B.
- **Ephemeral single-room combat sites** (outdoor/no-site fights, spec §3): owned by a **dedicated follow-up plan after B2 + C2 both land** — it needs B's archetype/materializer machinery AND C's enforcement seam. Track C explicitly does NOT build these (its no-grid boundary emits `tactical.enforcement.skipped` and resolves combat as today). Neither B1/B2 nor C may silently absorb this; it is unowned until that plan exists.
