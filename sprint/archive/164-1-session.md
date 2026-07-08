---
story_id: "164-1"
jira_key: ""
epic: "164"
workflow: "spdd"
---
# Story 164-1: SiteRegistry + CartographyConfig.sites + per-site storage keying (plan tasks 1–2)

## Story Details
- **ID:** 164-1
- **Jira Key:** (no jira)
- **Workflow:** spdd
- **Stack Parent:** none
- **Branch Strategy:** gitflow (feat/164-1-site-registry-storage-keying)

## Workflow Tracking
**Workflow:** spdd
**Phase:** finish
**Phase Started:** 2026-07-08T22:13:23Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-08T21:24:06Z | 2026-07-08T21:27:35Z | 3m 29s |
| red | 2026-07-08T21:27:35Z | 2026-07-08T21:40:43Z | 13m 8s |
| green | 2026-07-08T21:40:43Z | 2026-07-08T22:03:09Z | 22m 26s |
| review | 2026-07-08T22:03:09Z | 2026-07-08T22:13:23Z | 10m 14s |
| finish | 2026-07-08T22:13:23Z | - | - |

## Sm Assessment

**Setup complete — routing to TEA for the RED phase.**

- **Workflow decision:** Story YAML tags `workflow: superpowers`, which is not a registered pf workflow. Keith confirmed (2026-07-08) to run epics 163/164/165 as **`spdd`** (phased: setup → red → green → review → finish). Recorded in `sm-decisions.md` so siblings 164-2..164-7 don't re-ask. The written plan is reference material per phase, not a separate executing-plans run.
- **Scope:** Server-only. Backend model + storage work (SiteRegistry, `CartographyConfig.sites`, per-site storage keying). No UI/content in this story — 164-5 owns UI, later stories own the router/scene cutovers.
- **Branch:** `feat/164-1-site-registry-storage-keying` off `develop` — verified correct base (server `origin/HEAD → origin/develop`; no local `main`). Note: session line 14 says "gitflow"; subrepos are actually github-flow on develop — cosmetic label only, base is right.
- **Merge gate:** Clear. 0 in-progress, 0 in-review, no blocking PRs.
- **Jira:** Skipped — no Jira integration configured (`[no jira]`).

**For TEA (RED phase) — where to aim the failing tests:**
1. **Task 1 is pure/additive** — the whole point is *zero behavior change when `sites` is empty*. Write a regression-style test asserting existing worlds (empty `sites`) load unchanged, plus unit tests for each `SiteRegistry` method (`by_id`, `sites_for_node`, `resolve_descriptor` name/id disambiguation, `site_owning_node`) and the namespacing helpers.
2. **Task 2 keying** — the load-bearing test is AC-8: **two sites in one session store independently, no collision.** That's the integration test that proves the `site_id` keying actually works, not just that the column exists. Also assert AC-9: `DEFAULT_SITE_ID = "frontier"` preserves backward compatibility (existing Sünden data reads through unchanged).
3. **Wiring (AC-12, non-negotiable per CLAUDE.md):** at least one test must prove `SiteRegistry` is reachable from a production dispatch path — not merely constructed in isolation. Don't let Task 1 land as an unwired model package.
4. **Migration symmetry (AC-5):** upgrade *and* downgrade must be exercised.

Plan tasks 1–2 in `docs/superpowers/plans/2026-07-08-mapping-track-b-site-system.md` have the authoritative deliverable detail.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): The Track B plan's Task-2 integration test targets a `pg_dungeon_repo` fixture in `tests/game/pg/conftest.py` that does not exist, and imports `Expansion` from the wrong module with a wrong signature (`region_ids=`). Affects `docs/superpowers/plans/2026-07-08-mapping-track-b-site-system.md` — Dev must use `tests/dungeon/conftest.py::build_pg_dungeon_repo` (`(monkeypatch, migrated_db) -> (pool, repo, sid)`) and `sidequest.dungeon.region_graph.model.Expansion(expansion_id, new_nodes, new_edges)`. Same dungeon-repo seam recurs in sibling stories 164-2/3/4. *Found by TEA during test design.*
- **Question** (non-blocking): AC-8/AC-9 collision tests need `SIDEQUEST_TEST_DATABASE_URL` (unset in this dev shell) → they SKIP, not fail. Affects `tests/dungeon/test_dungeon_site_keying.py` — Dev/Reviewer must run `just pg-up` + export the URL to exercise the two-site path. RED is still verified via the module-level `DEFAULT_SITE_ID` ImportError at collection, and `test_default_site_id_is_frontier` gives a DB-independent RED→GREEN signal. *Found by TEA during test design.*
- **Conflict** (non-blocking): SM AC-12 asks for a dispatch-path wiring test, but the plan scopes Task 1 as pure/additive — `SiteRegistry` is consumed by tasks 4/6/7 (stories 164-2/3/4), and a premature dispatch hookup would break the "Sünden stays green at every merge" risk-sequencing. Affects the AC-12 interpretation for this story (see Design Deviations). Dispatch-path wiring tests belong to the consuming stories. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): The plan's `0003` migration hardcodes wrong revision ids — `revision = "0003_dungeon_site_id"` / `down_revision = "0002_asset_ledger"`. The real convention is short numeric (`0002_asset_ledger.py` has `revision = "0002"`); the descriptive part is only the filename. The plan's ids would make alembic fail "Can't locate revision '0002_asset_ledger'". Affects `docs/superpowers/plans/2026-07-08-mapping-track-b-site-system.md` — sibling migration stories (163/165 tracks) should use `revision="000N"` / `down_revision="000N-1"`. *Found by Dev during implementation.*
- **Question** (non-blocking): One pre-existing genre failure is in the tree and unrelated to 164-1: `tests/genre/test_beneath_sunden_room_binding_107_2.py::test_distinct_rooms_bind_distinct_creatures` (all rooms bind `gnaw_swarm`). It is one of the ~13 known content-develop drift failures (WWN/seaboard), NOT caused by the `site_id`/`CartographyConfig` change (my cartography/world-model selector ran 83/0). Flagged so Reviewer doesn't attribute it to this story. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (non-blocking): `SiteDecl.site_id` is unvalidated but the namespacing regex is lowercase-only — a CamelCase `site_id` produces an entrance node that `is_site_node_id`/`site_id_of`/`site_owning_node` silently reject (empirically confirmed). Affects `sidequest/genre/models/world.py` (`SiteDecl`) + `sidequest/game/sites/namespacing.py` — the **site-authoring story (164-2 / 164-6/7)** must validate `site_id` as lowercase-snake (fail loud at pack load) before homebrew authoring is exposed. *Found by Reviewer during code review.*
- **Gap** (non-blocking): `SiteDecl.name` is unvalidated; an empty `name` makes `resolve_descriptor`'s `name.lower() in desc` match every descriptor (spurious resolution). Affects `sidequest/game/sites/registry.py` + `SiteDecl` — validate non-empty `name`. Fold into the same authoring-validation pass. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `DEFAULT_SITE_ID="frontier"` defaults on every `PgDungeonRepository`/`Transaction` method are correct back-compat now, but once 164-2/3/4 pass real site_ids a call site that omits `site_id=` silently hits the wrong partition (No-Silent-Fallbacks). Affects the **dispatch-wiring stories** — require `site_id` explicit (keyword-only, no default) at movement/materializer call sites. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `alembic 0003.downgrade()` silently commingles multi-site data (drops `site_id`, re-keys `dungeon_meta` to `(session_id)`) — no guard, no loud failure. Not empirically confirmed (my probe hit a harness column error), DDL-reasoned. Affects `alembic/versions/0003_dungeon_site_id.py` — add a `site_id <> 'frontier'` guard to `downgrade()` **when multi-site materialization lands (164-6)**. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `SiteDecl` uses `extra="allow"`, so a typo'd authored key (e.g. `extemt:`) is silently ignored and `extent` falls back to `"bounded"`. Consistent with `Region`/`Route` convention but a homebrew-authoring footgun (Jade). Affects the authoring surface — consider a pack-lint unknown-key check for site declarations. *Found by Reviewer during code review.*
- **Gap** (non-blocking, load-bearing): `SiteRegistry` has **zero production consumers** in this diff (confirmed by grep). Acceptable ONLY because the plan sequences consumers to 164-2/3/4. Affects `sidequest/game/sites/` — **164-2 MUST wire `SiteRegistry` into a production dispatch path**, else this retroactively becomes dead code (CLAUDE.md "no half-wired features"). *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Task-2 integration test placed in `tests/dungeon/`, not `tests/game/pg/`**
  - Spec source: plan `2026-07-08-mapping-track-b-site-system.md`, Task 2 "Files"
  - Spec text: "Create `sidequest-server/tests/game/pg/test_dungeon_site_keying.py` … Reuse the repo/session fixture from `tests/game/pg/conftest.py` (`pg_dungeon_repo`)."
  - Implementation: test lives at `tests/dungeon/test_dungeon_site_keying.py`, using `tests/dungeon/conftest.py`'s `migrated_db` fixture + `build_pg_dungeon_repo` helper.
  - Rationale: neither `tests/game/pg/conftest.py` nor a `pg_dungeon_repo` fixture exists; the real PG dungeon fixtures are in `tests/dungeon/conftest.py`; a test under `tests/game/pg/` would error "fixture 'migrated_db' not found".
  - Severity: minor
  - Forward impact: the Code Organization line (`/tests/game/pg/test_dungeon_site_keying.py`) is superseded — keep the test in `tests/dungeon/`.
- **`Expansion` constructed from `region_graph.model`, not `materializer`**
  - Spec source: plan Task 2 embedded test sketch
  - Spec text: "`from sidequest.dungeon.materializer import Expansion` … `Expansion(expansion_id=0, region_ids=(...))`"
  - Implementation: `from sidequest.dungeon.region_graph.model import Expansion`; `Expansion(expansion_id=0, new_nodes=[...], new_edges=[])`.
  - Rationale: the real `Expansion` dataclass has `new_nodes`/`new_edges` and no `region_ids`; the plan itself says "read the dataclass and adapt — do not invent fields".
  - Severity: minor
  - Forward impact: none.
- **AC-12 wiring narrowed to model-field parse + real-DB round-trip; dispatch-path wiring deferred**
  - Spec source: session SM Assessment, AC-12
  - Spec text: "Wiring test confirms SiteRegistry integration in the dispatch path (entry gate or seam resolver)."
  - Implementation: wiring proven by `test_cartography_config_sites_wire_into_registry` (registry built from a real `CartographyConfig`, not a mock) plus the real-`PgDungeonRepository` round-trip in the keying tests; NO dispatch-path hookup is asserted.
  - Rationale: the plan scopes Task 1 as pure/additive — `SiteRegistry` is consumed by tasks 4/6/7 (stories 164-2/3/4). Asserting dispatch wiring now would either fail permanently or force a premature `movement.py` cutover, violating SOUL "Bind the Ruleset"/the plan's "Sünden must stay green at every merge point".
  - Severity: minor
  - Forward impact: dispatch-path wiring tests are owned by stories 164-2/3/4.

### Dev (implementation)
- **Migration revision ids use the short-numeric convention, not the plan's descriptive ids**
  - Spec source: plan `2026-07-08-mapping-track-b-site-system.md`, Task 2 migration block
  - Spec text: `revision = "0003_dungeon_site_id"` / `down_revision = "0002_asset_ledger"`
  - Implementation: `revision = "0003"` / `down_revision = "0002"` (filename kept as `0003_dungeon_site_id.py`)
  - Rationale: the existing files use short ids (`0002_asset_ledger.py` → `revision = "0002"`); the plan's ids would break alembic ("Can't locate revision '0002_asset_ledger'"). Verified up/down/up symmetric on a throwaway DB.
  - Severity: minor
  - Forward impact: none (0003 chains cleanly onto 0002).
- **`site_id` threaded through the ENTIRE dungeon repository surface, not only the two tested methods**
  - Spec source: story ACs (AC-10 "all repository method signatures updated consistently") + the tests (which only touch `commit_expansion`/`load_map`)
  - Spec text: AC-10 — "All repository method signatures updated consistently across Protocol and implementation"
  - Implementation: keyword-only `site_id: str = DEFAULT_SITE_ID` added to every `PgDungeonRepository`/`PgDungeonTransaction` method (seed, frontier, mutations, ledger) + both Protocols, with `site_id` in every WHERE/INSERT, the frontier `ON CONFLICT`, and the per-site write-once seed check.
  - Rationale: `0003` re-keys ALL six dungeon tables' PKs — partial threading would break `put_frontier` (`ON CONFLICT` no longer matches the PK) and corrupt `set_campaign_seed` (2nd site can't seed). Full threading is the minimal COHERENT implementation (CLAUDE.md "no half-wired features"). Regression-verified: dungeon suite 541/0.
  - Severity: minor (scope is AC-mandated, not creep)
  - Forward impact: sibling stories 164-2/3/4 inherit a fully site-keyed repo surface (all callers may pass `site_id`).
- **Amended TEA's SiteRegistry test fixtures to satisfy the `Region` schema**
  - Spec source: the tests TEA wrote (`tests/game/sites/test_site_registry.py`)
  - Spec text: fixtures built regions as `{"name": ..., "adjacent": [...]}`
  - Implementation: added a `_region(name, adjacent)` helper that also supplies `summary`/`description`; rewrote the region maps to use it. No SiteRegistry assertion changed.
  - Rationale: `Region` requires `summary` and `description` (`world.py:206-207`, no defaults); the plan's fixture (copied by TEA) omitted them, so `CartographyConfig.model_validate` rejected all populated carts (11 tests errored before asserting). The registry only reads `adjacent`, so the helper keeps fixtures terse but valid.
  - Severity: minor
  - Forward impact: none.

### Reviewer (audit)
- **TEA — Task-2 test placed in `tests/dungeon/` not `tests/game/pg/`** → ✓ ACCEPTED: correct; the `migrated_db`/`build_pg_dungeon_repo` fixtures live in `tests/dungeon/conftest.py` and `tests/game/pg/` has no conftest. A test at the plan's path would error "fixture not found." Sound.
- **TEA — `Expansion` from `region_graph.model` not `materializer`** → ✓ ACCEPTED: the real dataclass is `region_graph.model.Expansion(expansion_id, new_nodes, new_edges)`; the plan's `materializer.Expansion(region_ids=…)` does not exist. pyright + green tests confirm the correct API.
- **TEA — AC-12 wiring narrowed to model-field + real-DB round-trip; dispatch wiring deferred** → ✓ ACCEPTED: matches the plan's pure/additive scope and risk-sequencing. See my Devil's Advocate — the zero-consumer state is acceptable ONLY because 164-2/3/4 are sequenced to consume it; I have filed a delivery finding making that load-bearing.
- **Dev — migration revision ids short-numeric (`0003`/`0002`) not the plan's descriptive ids** → ✓ ACCEPTED: the plan's `down_revision="0002_asset_ledger"` would break alembic (`0002_asset_ledger.py` has `revision="0002"`). I independently verified up→head/down→0002/down→base/re-up→head symmetry on a throwaway DB. Correct.
- **Dev — full `site_id` threading (not only the tested methods)** → ✓ ACCEPTED: AC-10-mandated and required for coherence — partial threading breaks `put_frontier`'s `ON CONFLICT` and corrupts `set_campaign_seed` against the re-keyed PKs. 541-test dungeon regression (with DB) proves the full surface. Not scope creep.
- **Dev — amended TEA's fixtures for `Region.summary/description`** → ✓ ACCEPTED: `Region` requires those fields; the fixture was objectively invalid. The `_region()` helper changed no SiteRegistry assertion, only made the cart schema-valid. Legitimate GREEN-phase fixture fix.
- **Reviewer — no undocumented deviations found.** The zero-production-consumer state of `SiteRegistry` is the one thing that looks like an undocumented divergence from CLAUDE.md's "no half-wired" rule, but it IS documented (TEA's AC-12 deviation + Dev assessment) and accepted above.

## Technical Approach

This story implements **Tasks 1–2** of Track B (Site System), per `docs/superpowers/specs/2026-07-08-three-tier-mapping-design.md` §1/§3/§4 and `docs/superpowers/plans/2026-07-08-mapping-track-b-site-system.md`.

### Task 1: SiteDescriptor + SiteRegistry model + `CartographyConfig.sites` (pure/additive)

Foundational model definitions. No behavior change — every existing world has an empty `sites` list.

**Deliverables:**
- Create `sidequest/game/sites/` package with `__init__.py`, `models.py`, `registry.py`, `namespacing.py`
- Define `SiteDecl` (pydantic model for authored YAML), `SiteDescriptor` (frozen dataclass, resolved runtime view)
- Define `SiteRegistry` class with methods:
  - `from_cartography(cart: CartographyConfig) -> SiteRegistry`
  - `by_id(site_id: str) -> SiteDescriptor | None`
  - `sites_for_node(region_id: str) -> list[SiteDescriptor]` (owner + adjacency-reachable)
  - `resolve_descriptor(region_id: str, descriptor: str) -> tuple[SiteDescriptor | None, bool]`
  - `site_owning_node(node_id: str) -> SiteDescriptor | None`
- Implement namespacing helpers: `site_entrance_id()`, `is_site_node_id()`, `site_id_of()`
- Add `sites: list[SiteDecl] = Field(default_factory=list)` field to `CartographyConfig` (after `routes` in `world.py`)
- Create comprehensive unit tests covering all methods and edge cases

### Task 2: Per-site storage keying — `site_id` column + repository methods (additive)

Extends dungeon storage from `(session_id, ...)` keying to `(session_id, site_id, ...)`. Backward-compatible via `DEFAULT_SITE_ID = "frontier"`.

**Deliverables:**
- Create Alembic migration `0003_dungeon_site_id.py` that adds `site_id TEXT NOT NULL DEFAULT 'frontier'` column to all dungeon tables and re-keys primary keys to include it:
  - `dungeon_map`: PK becomes `(session_id, site_id, region_id)`
  - `dungeon_edge`: adds `site_id`
  - `dungeon_frontier`: PK becomes `(session_id, site_id, frontier_edge_id)`
  - `dungeon_mutation_overlay`: adds `site_id`
  - `dungeon_complication_ledger`: PK becomes `(session_id, site_id, thread_id)`
  - `dungeon_meta`: PK becomes `(session_id, site_id)`
- Add `DEFAULT_SITE_ID = "frontier"` constant to `sidequest/game/pg/dungeon.py`
- Thread keyword-only `site_id: str = DEFAULT_SITE_ID` parameter into all `PgDungeonRepository` and `PgDungeonTransaction` methods:
  - Readers: `load_map`, `load_masks`, `load_frontier`, `load_mutations`, `get_campaign_seed`
  - Writers: `PgDungeonTransaction.commit_expansion`, `put_frontier`, `record_mutation`, `set_campaign_seed`
- Update WHERE clauses and INSERT statements to include `site_id`
- Update `DungeonRepository` Protocol in `repository.py` with matching signatures
- Create integration tests proving two sites in one session do not collide

## Acceptance Criteria

1. ✓ SiteRegistry loads from CartographyConfig with zero behavior change when `sites` is empty
2. ✓ SiteRegistry correctly indexes sites by owner and adjacency
3. ✓ Site descriptor resolution disambiguates by name/id
4. ✓ Namespacing helpers correctly identify and extract site-scoped node ids
5. ✓ Alembic migration applies cleanly and upgrades/downgrades symmetrically
6. ✓ Dungeon storage queries include site_id in WHERE clauses
7. ✓ Dungeon storage INSERT statements include site_id in column lists
8. ✓ Two sites in the same session store independently (no collision)
9. ✓ Default site_id = "frontier" maintains backward compatibility for Sünden
10. ✓ All repository method signatures updated consistently across Protocol and implementation
11. ✓ Unit and integration tests pass; existing dungeon suite regresses zero tests
12. ✓ Wiring test confirms SiteRegistry integration in the dispatch path (entry gate or seam resolver)

## Code Organization

**Server (sidequest-server):**
- `/sidequest/game/sites/` — new package
  - `__init__.py` — public exports
  - `models.py` — `SiteDecl`, `SiteDescriptor`
  - `registry.py` — `SiteRegistry`
  - `namespacing.py` — `site_entrance_id()`, `is_site_node_id()`, `site_id_of()`
- `/sidequest/genre/models/world.py` — add `SiteDecl` and `sites` field to `CartographyConfig`
- `/sidequest/game/pg/dungeon.py` — add `DEFAULT_SITE_ID`, thread `site_id` through all methods
- `/sidequest/game/repository.py` — update `DungeonRepository` Protocol signatures
- `/alembic/versions/0003_dungeon_site_id.py` — new migration
- `/tests/game/sites/` — unit tests
- `/tests/game/pg/test_dungeon_site_keying.py` — integration tests

**Branch:** `feat/164-1-site-registry-storage-keying` (off `develop`)

## Context Links

- **Spec:** docs/superpowers/specs/2026-07-08-three-tier-mapping-design.md
- **Plan:** docs/superpowers/plans/2026-07-08-mapping-track-b-site-system.md
- **ADR-096:** Cavern Renderer Revival (procedural dungeon baseline)
- **ADR-109:** Persistent Location Descriptions + Mechanical Manifest

## TEA Assessment

**Tests Required:** Yes
**Reason:** 5-pt foundational feature — a new `game/sites/` package (SiteRegistry + namespacing) and per-site dungeon storage keying. Both need behavioral coverage before implementation.

**Test Files:**
- `tests/game/sites/test_site_registry.py` — SiteRegistry + namespacing units (Task 1) — 28 tests.
- `tests/game/sites/__init__.py` — package marker.
- `tests/dungeon/test_dungeon_site_keying.py` — per-site storage keying (Task 2) — 3 tests (1 DB-independent, 2 Postgres-backed).

**Tests Written:** 31 tests covering 11 of 12 ACs (AC-12 wiring reinterpreted for this story's pure/additive scope — see Design Deviations).
**Status:** RED — **verified** via `testing-runner` (`164-1-tea-red`). Both files fail at *collection* for the exact missing-feature reason, not a test defect:
- `tests/game/sites/test_site_registry.py` → `ModuleNotFoundError: No module named 'sidequest.game.sites'`
- `tests/dungeon/test_dungeon_site_keying.py` → `ImportError: cannot import name 'DEFAULT_SITE_ID' from 'sidequest.game.pg.dungeon'`

**AC → test map (where Dev's GREEN lands):**
- AC-1 (zero behavior change, empty sites): `test_sites_field_defaults_empty`, `test_from_cartography_on_empty_config_is_inert`, `test_from_cartography_none_is_defensive_empty`
- AC-2 (owner + adjacency indexing): `test_sites_for_node_includes_owner`, `…_includes_adjacent_owner`, `…_owner_precedes_adjacent`, `…_dedups_repeated_adjacency`, `…_unknown_node_is_empty`, `test_by_id_hit_and_miss`
- AC-3 (descriptor disambiguation): the 7 `test_resolve_descriptor_*` (name, id-substring, unmatched, no-candidates, empty-sole, empty-multi-ambiguous, ambiguous-name)
- AC-4 (namespacing): `test_site_owning_node_*` (×3), `test_site_entrance_id`, `test_is_site_node_id_*` (×2), `test_site_id_of`
- AC-8 (two sites no collision): `test_two_sites_do_not_collide` *(needs DB)*
- AC-9 (DEFAULT_SITE_ID backward-compat): `test_default_site_id_is_frontier`, `test_default_key_write_isolated_from_new_site` *(2nd needs DB)*
- AC-12 (wiring, in-scope): `test_cartography_config_sites_wire_into_registry` + the real-repo round-trip
- AC-5/6/7/10/11 (migration symmetry, WHERE/INSERT keying, Protocol consistency, no-regression): **Dev-owned in GREEN** — exercised end-to-end by the DB-backed collision tests once `SIDEQUEST_TEST_DATABASE_URL` is set; the migration up/down and Protocol-signature parity are Dev implementation the collision round-trip proves. *(Flagged: TEA did not pin a standalone migration up/down test — the round-trip covers it; call out if Reviewer wants an explicit alembic downgrade assertion.)*

### Rule Coverage (python.md lang-review checklist)

| Rule | Test(s) | Status |
|------|---------|--------|
| #6 test quality (no vacuous asserts) | Phase-C self-check over all 31 tests — every test asserts a concrete value/type/exception (`== {...}`, `is True/False/None`, `pytest.raises(FrozenInstanceError)`) | pass (self-check) |
| #3 type annotations at boundaries | all test fns annotated `-> None`; registry public methods exercised with typed expectations | failing (RED) |
| #11 input validation (empty/None descriptor) | `test_resolve_descriptor_no_candidates_returns_none_false`, `…_empty_descriptor_sole_candidate_resolves`, `…_empty_descriptor_multi_candidate_is_ambiguous` | failing (RED) |
| #2 mutable defaults | future `site_id: str = DEFAULT_SITE_ID` is a str constant (no list/dict default); `test_default_site_id_is_frontier` pins it | failing (RED) |
| type-design (frozen runtime view) | `test_site_descriptor_is_frozen`, `test_site_extent_defaults_bounded` | failing (RED) |

**Rules checked:** 5 of 5 applicable python.md checks have test coverage (the rest — async, resource-leaks, unsafe-deserialization, path-handling — are N/A to this pure-model + repo-signature change).
**Self-check:** 0 vacuous tests found (written fresh, no pre-existing tests touched).

**Handoff:** To Dev (Inigo Montoya) for GREEN. Implement per plan tasks 1–2, but heed the three Design Deviations: keep the keying test in `tests/dungeon/`, use `region_graph.model.Expansion`, and do NOT add dispatch-path wiring (out of scope; 164-2/3/4 own it). Run the DB-backed cases with `just pg-up` + `SIDEQUEST_TEST_DATABASE_URL` before claiming GREEN.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/genre/models/world.py` — `SiteExtent` + `SiteDecl` models; `CartographyConfig.sites` field (additive, defaulted; defined in genre to avoid a game→genre import cycle).
- `sidequest/game/sites/{__init__,models,namespacing,registry}.py` — **new** site package (namespacing helpers, frozen `SiteDescriptor`, `SiteRegistry`). No dispatch-path consumers yet (owned by 164-2/3/4).
- `sidequest/game/pg/dungeon.py` — `DEFAULT_SITE_ID = "frontier"`; keyword-only `site_id` threaded through every `PgDungeonRepository`/`PgDungeonTransaction` method (WHERE + INSERT + frontier `ON CONFLICT` + per-site write-once seed check).
- `sidequest/game/repository.py` — `DungeonRepository` + `DungeonTransaction` Protocol signatures updated to match (AC-10).
- `alembic/versions/0003_dungeon_site_id.py` — **new** migration: `site_id` column + re-keyed PKs on all six dungeon tables.
- `tests/game/sites/test_site_registry.py` — fixture correction (`_region` helper supplies required `Region.summary/description`; no assertion changed).

**Tests:** 31/31 story tests GREEN — verified via `testing-runner` (`164-1-dev-green-2`) against a **live Postgres**, so the two DB-backed collision tests (`test_two_sites_do_not_collide`, `test_default_key_write_isolated_from_new_site`) **ran and passed** (AC-8/AC-9), not skipped.

**Verification evidence (fresh):**
- `ruff check`: 0 errors · `ruff format --check`: clean
- **AC-5 migration symmetry**: upgrade→head, downgrade→0002, downgrade→base, re-upgrade→head all PASS on a throwaway DB.
- **Dungeon regression**: `tests/dungeon/` = **541 passed / 0 failed** (site_id thread-through broke nothing).
- **Genre regression**: cartography/world-model selector **83 passed / 0 failed**; genre suite 1215/1 — the single failure (`test_distinct_rooms_bind_distinct_creatures`, beneath_sunden creature binding) is a **pre-existing** content-develop drift failure, unrelated to this story (see Delivery Findings).
- Content scan: no pack declares a cartography `sites:` key → the new typed field can't cause a validation regression.

**Branch:** `feat/164-1-site-registry-storage-keying` (pushed to origin).
**Handoff:** To Reviewer (Westley) for code review. Attention points: (1) full `site_id` threading is intentional/AC-mandated, not creep — see Design Deviations; (2) AC-12 wiring is deliberately model-only for this pure/additive story; (3) I amended TEA's fixtures for `Region` schema validity.

<skills-invoked>
<skill name="test-driven-development" phase="red" at="2026-07-08T21:28:30Z"/>
<skill name="test-driven-development" phase="green" at="2026-07-08T22:01:43Z"/>
<skill name="verification-before-completion" phase="green" at="2026-07-08T22:01:43Z"/>
<skill name="requesting-code-review" phase="green" at="2026-07-08T22:01:43Z"/>
</skills-invoked>

## Subagent Results

Only 3 reviewer subagents are enabled (`pf settings get workflow.reviewer_subagents`): preflight, silent_failure_hunter, security. The other 6 are disabled via settings — I assessed their domains **myself** (tagged inline in the Reviewer Assessment) since the review checklist coverage is not optional just because a specialist is toggled off.

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (581 tests green, pyright 0, lint/format 0, migration applied) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — self-assessed (see `[EDGE]`) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 4 | confirmed 4, dismissed 0, deferred 0 (all Low/Med, non-blocking) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — self-assessed (see `[TEST]`) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — self-assessed (see `[DOC]`) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — self-assessed (see `[TYPE]`) |
| 7 | reviewer-security | Yes | findings | 1 | confirmed 1, dismissed 0 (Low, forward-looking) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — self-assessed (see `[SIMPLE]`) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — self-assessed (see `[RULE]`) |

**All received:** Yes (3 enabled returned; 6 disabled via settings and self-assessed)
**Total findings:** 7 confirmed (2 edge self-found + 4 silent-failure + 1 security; net-deduped to the observation list below), 0 dismissed, 0 blocking. All Low/Medium and latent (future-consumer surface).

## Reviewer Assessment

**Verdict:** APPROVED

This is a pure/additive foundational story (Track B Task 1–2). It is correct, well-tested, and secure for its scoped behavior; every finding is a **latent** robustness/validation gap on the *future* consumer/authoring surface (164-2/3/4/6), which the plan explicitly defers. None is Critical/High, so none blocks — they are captured as delivery findings for the consuming stories.

**Data flow traced:**
- `site_id` (method kwarg, defaulted `"frontier"`) → **bound `%s` parameter** in every dungeon SQL statement → DB WHERE/INSERT/ON CONFLICT/UPDATE. Never string-interpolated. Isolation proven by `test_two_sites_do_not_collide` + `test_default_key_write_isolated_from_new_site` against live Postgres.
- `CartographyConfig.sites` (authored YAML → `yaml.safe_load` → pydantic `SiteDecl`) → `SiteRegistry.from_cartography` → frozen `SiteDescriptor`. Wired into the production model; **no dispatch-path consumer yet** (by design).

**Pattern observed:** Repo→Transaction delegation preserved — `PgDungeonRepository.*` open a `session_tx` and delegate to `PgDungeonTransaction.*` (e.g. `dungeon.py:406-409`), and `site_id=site_id` is correctly forwarded in every delegate. `SiteExtent`/`SiteDecl` defined in `genre` and re-exported by `game.sites.models` (`models.py:14`) correctly respects the game→genre dependency direction (avoids an import cycle). Good.

**Error handling:** `dungeon.py` catches only specific `psycopg` errors and re-raises domain errors (`PersistError`/`DatabaseError`/`SerializationError`) — no bare except, no swallowing (`dungeon.py:178-188` etc.). `registry.py`/`namespacing.py` are pure with no error paths. Migration DDL is transactional (alembic "assume transactional DDL"). Verified.

### Observations

- `[SEC]` **[VERIFIED] No SQL injection** — all 17 `execute`/`executemany` sites in `dungeon.py` use `%s` placeholders with `site_id` bound in the params tuple; the migration's only f-string interpolates the hardcoded internal `_SITE = "frontier"` (`0003:29`), no external-input path. Confirmed by reviewer-security (17/17) + my own grep. Complies with python.md #11 (CWE-89).
- `[SEC]` **[VERIFIED] Site isolation complete** — every read/write filters by `(session_id, site_id)` matching the new composite PKs; no sibling query left `session_id`-only. Complies with the tenant-isolation intent. Evidence: `dungeon.py:441,446,499,525,583…` + collision test.
- `[TYPE]` **[VERIFIED] Type design sound (type_design disabled — self-assessed)** — `pyright` 0 errors across the changed files; `SiteDescriptor` is a `@dataclass(frozen=True)` (immutable runtime view, proven by `test_site_descriptor_is_frozen`); `SiteExtent = Literal["bounded","frontier"]`; Protocol signatures in `repository.py` match the impl (the `= ...` default-elision convention). No stringly-typed leakage introduced.
- `[TEST]` **[VERIFIED] Test quality (test_analyzer disabled — self-assessed)** — 31 story tests + 541 dungeon regression, all with concrete assertions (value equality, `is True/False/None`, `pytest.raises(FrozenInstanceError)`); no vacuous `assert True`; the DB-backed collision/isolation tests genuinely RAN (not skipped) against live PG. Complies with python.md #6.
- `[DOC]` **[VERIFIED] Docs accurate (comment_analyzer disabled — self-assessed)** — module docstrings correctly state the pure/additive, no-dispatch-wiring scope (`registry.py:4-8`); the migration docstring documents the additive `DEFAULT 'frontier'` back-compat. No stale/misleading comments in the diff.
- `[EDGE]` **[LOW] Namespacing is case-sensitive-lowercase but `site_id` is unvalidated (edge_hunter disabled — self-found & empirically proven)** at `namespacing.py:12` + `world.py` `SiteDecl`. A CamelCase `site_id` yields an entrance node id (`GildedBoar:entrance`) that `is_site_node_id`/`site_id_of`/`site_owning_node` silently reject (→ False/None). Latent — zero authored sites, all in-scope ids are lowercase_snake. **Delivery finding for the authoring story** (validate `site_id` lowercase-snake, fail loud at load).
- `[EDGE]` **[LOW] `resolve_descriptor` spurious match on empty `name`** — a `SiteDecl.name == ""` matches every descriptor via `name.lower() in desc` (`registry.py`). Latent (authored sites have names). Delivery finding: validate non-empty `name`.
- `[SILENT]` **[LOW] Redundant defensive `getattr` in `from_cartography`** (`registry.py:38`, confidence medium) — after the `cart is None` guard, `getattr(cart, "sites", []) or []` / `getattr(region, "adjacent", [])` can only mask a future `AttributeError` (field rename), degrading to an empty registry instead of failing loud (No-Silent-Fallbacks). Mitigating: it matches repo-wide `getattr(cart, "regions", …)` house style. `[SIMPLE]` this is also the one simplification: direct `cart.sites`/`region.adjacent` access would be both loud and simpler. Non-blocking.
- `[SILENT]`/`[SEC]` **[LOW] `DEFAULT_SITE_ID` default is a forward foot-gun** (`dungeon.py:101`) — all three reviewers flagged independently. Correct back-compat today (every existing caller falls through to `"frontier"`, matching the migration backfill — verified against the real callers by silent-failure-hunter). But once 164-2/3/4 pass real site_ids, a call site that omits `site_id=` silently hits the wrong partition. Delivery finding: require explicit `site_id` at dispatch call sites.
- `[SILENT]` **[LOW] Migration downgrade unguarded against multi-site data** (`0003` `downgrade`) — dropping `site_id` silently commingles two sites' rows into one flat dungeon; the re-added `dungeon_meta` PK `(session_id)` would collide on multi-site data. Latent (no multi-site data until 164-6+); standard partition-migration caveat. I attempted to prove it empirically but my probe INSERT used a non-existent `sessions.updated_at` column (harness error, not a code defect), so this is a DDL-reasoned note, **not empirically confirmed**. Delivery finding: add a `site_id <> 'frontier'` guard to `downgrade()` when multi-site data becomes real.
- `[SILENT]` **[LOW] `SiteDecl extra="allow"` tolerates typo'd keys** — `extemt: frontier` is silently ignored and `extent` falls back to `"bounded"`. Consistent with `Region`/`Route` convention; relevant to Jade's homebrew authoring. Delivery finding.
- `[RULE]` **[VERIFIED] python.md lang-review compliance (rule_checker disabled — self-assessed)** — see `### Rule Compliance` below; 12/13 checks PASS, the sole flag being #11 input-validation (the `site_id`/`name`/`extent` authoring-validation gap above), which is out-of-scope for this pre-consumer story and captured as delivery findings.

### Rule Compliance (python.md, enumerated over the diff)

| # | Rule | Verdict | Evidence |
|---|------|---------|----------|
| 1 | Silent exception swallowing | PASS | `dungeon.py` catches specific psycopg errors → domain errors; no bare except |
| 2 | Mutable default args | PASS | `site_id: str = DEFAULT_SITE_ID` (str const); `_region(adjacent=None)` uses `or []` |
| 3 | Type annotations at boundaries | PASS | all new public fns annotated; pyright 0 errors |
| 4 | Logging coverage/correctness | PASS (N/A) | no logging added; error paths raise, consistent with existing code |
| 5 | Path handling | PASS (N/A) | no path manipulation |
| 6 | Test quality | PASS | concrete assertions, no vacuous; DB tests real |
| 7 | Resource leaks | PASS | all DB access via `with … connection()/session_tx()` |
| 8 | Unsafe deserialization | PASS | `SiteDecl` via existing `yaml.safe_load` loader; no pickle/eval |
| 9 | Async pitfalls | PASS (N/A) | repo methods sync; async only in test infra |
| 10 | Import hygiene | PASS | `TYPE_CHECKING` for CartographyConfig (cycle-safe); `__all__` present; no star imports |
| 11 | Input validation | **FLAG (deferred)** | SQL parameterized ✓; but `SiteDecl.site_id`/`name`/`extent` unvalidated at the YAML boundary → the latent namespacing/resolve gaps. Out-of-scope for this pre-consumer story; delivery findings filed for the authoring story. |
| 12 | Dependency hygiene | PASS (N/A) | no dependency changes |
| 13 | Fix-introduced regressions | PASS | 541 dungeon + 83 cartography regression green; pyright 0 |

### Devil's Advocate

Argue this is broken. **The strongest case:** this story ships a `SiteRegistry` with *zero production consumers* — `security` and `silent-failure` both grepped the tree and found nothing outside the `sites` package and tests calls it. By the letter of CLAUDE.md ("No half-wired features… Every Test Suite Needs a Wiring Test… verify it has non-test consumers"), this is exactly the dead-code shape the project forbids: a module that exists but is never reached from production. A hostile reviewer would reject on that alone. **Why it survives:** the plan (and TEA's logged deviation) explicitly scope this as the pure/additive foundation of a risk-sequenced multi-story track — the consumers are 164-2/3/4, and wiring them now would force a premature `movement.py` cutover that breaks the "Sünden stays green at every merge" invariant. The `CartographyConfig.sites` field *is* wired into the production model. So it's deferred wiring, not abandoned wiring — acceptable only because the sequencing is explicit and the very next story consumes it. If 164-2 does NOT wire it, this retroactively becomes dead code, so the delivery finding is load-bearing.

**Second angle — a confused/hostile content author.** Homebrew authoring is a stated project priority (Jade). An author who writes `site_id: "GildedBoar"` or `extemt: frontier` gets *silent* wrong behavior: the site loads, but its nodes can't be mapped back (namespacing rejects the CamelCase id) or its extent silently defaults to bounded (typo swallowed by `extra="allow"`). No error, no warning — the site is subtly broken and the author has no signal. Combined with the `DEFAULT_SITE_ID` fallback (a forgotten `site_id=` writes to the wrong partition with no error), there is a *cluster* of silent-fallback surfaces waiting for the consumer stories. **Why non-blocking now:** none is reachable in this diff (no authored sites, no dispatch wiring), and the convention is uniformly lowercase_snake in-scope. But the pattern is real and I have flagged every instance as a delivery finding so the authoring story cannot ship without addressing them.

**Stressed-DB / rollback angle:** a `downgrade` after multi-site data silently merges sites — a real data-integrity trap, mitigated only by the fact that no multi-site data exists until 164-6+. The migration *upgrade* is clean and symmetric for the single-site case (verified). Net: nothing broken today; a well-marked trail of hardening the consumer stories must complete. Verdict stands: APPROVED.

**Handoff:** To SM (Vizzini) for finish-story.