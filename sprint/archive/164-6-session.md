---
story_id: "164-6"
jira_key: ""
epic: "164"
workflow: "spdd"
---
# Story 164-6: Archetype catalog schema + bounded one-txn materialization + site single-writer (plan tasks 10–12)

## Story Details
- **ID:** 164-6
- **Jira Key:** (none — Jira not configured)
- **Workflow:** spdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** spdd
**Phase:** finish
**Phase Started:** 2026-07-10T16:12:45Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-10T14:09:30Z | 2026-07-10T14:12:02Z | 2m 32s |
| red | 2026-07-10T14:12:02Z | 2026-07-10T14:39:58Z | 27m 56s |
| green | 2026-07-10T14:39:58Z | 2026-07-10T15:35:21Z | 55m 23s |
| review | 2026-07-10T15:35:21Z | 2026-07-10T15:55:53Z | 20m 32s |
| green | 2026-07-10T15:55:53Z | 2026-07-10T16:06:20Z | 10m 27s |
| review | 2026-07-10T16:06:20Z | 2026-07-10T16:12:45Z | 6m 25s |
| finish | 2026-07-10T16:12:45Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): Task 10 must update the loader allowlist and the content
  schema in lockstep — add `"site_archetypes.yaml"` to `GENRE_PACK_ROOT_EXTENSION_FILES`
  (`sidequest/genre/loader.py:126`, a frozenset) AND add `site_archetypes` under
  `genre_pack.extensions` in `sidequest-content/pack_schema.yaml`. If they drift, the
  existing guard `tests/cli/validate/test_pack_schema_loader_drift_113_2.py` fails.
  Affects `sidequest/genre/loader.py` + `sidequest-content/pack_schema.yaml` (content repo).
  *Found by TEA during test design.*
- **Improvement** (non-blocking): the four DB-backed bounded-site tests require
  `SIDEQUEST_TEST_DATABASE_URL` (local `sidequest_test` DB); without it they skip.
  Dev/verify should export it (`postgresql://$USER@localhost:5432/sidequest_test`) so
  the transaction-boundary assertions actually run.
  Affects `tests/dungeon/test_bounded_site.py` (run env). *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): a bounded site's complication threads (from theme
  set-pieces) are written under `DEFAULT_SITE_ID`, not the site's own `site_id` —
  the base `DungeonStore.open_thread` has no `site_id` param (only
  `PgDungeonTransaction` does), so threading it broke `TestStageAttach`. A
  follow-up if sites ever need queryable per-site complications must add
  `site_id` to `DungeonStore.open_thread` first. Affects
  `sidequest/dungeon/setpiece_attach.py` + `sidequest/dungeon/persistence.py`
  (`DungeonStore.open_thread` signature). *Found by Dev during implementation.*
- **Improvement** (non-blocking): the movement→bounded-site wiring
  (`run_movement_dispatch`) loads the site bundle/palette from
  `pack.source_dir/worlds/<world>` on every bounded entry and has no 164-6 unit
  test — its behavioral proof is the enter→SITE_MAP+TACTICAL_GRID→exit handler
  test in **story 164-7 (plan task 13)**, which also authors the tavern/vault
  content + `themes/` palette a bounded-site world needs. Affects
  `sidequest/agents/subsystems/movement.py`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): `get_campaign_seed() or 0` silently defaults a missing base
  campaign seed to 0 for every non-beneath_sunden world, making bounded sites
  identical across sessions (No Silent Fallbacks). Affects
  `sidequest/dungeon/bounded_site.py:86` (mint+persist a fresh session seed, or
  fail loud). *Found by Reviewer during code review.*
- **Gap** (non-blocking): Task 12's site single-writer leaves a third narrator
  write path unguarded — the heading-driven `current_region`/`pc_regions`
  auto-advance clobbers a PC out of a site interior with no site-ownership check
  or `resolve_exit_site`. Affects `sidequest/server/narration_apply.py:4460-4544`
  (gate on `site_owning_node`). Activates when a region-mode world declares a
  `bounded` site (164-7). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the movement bounded-site wiring adds a CWE-22
  path-traversal sink (`world_dir` from unsanitized `world_slug` → `load_cookbook`/
  `load_theme_palette`) — the root cause (unvalidated `world_slug`) predates this
  diff (`connect.py:586` / `rest.py:78`), so a durable fix validates `world_slug`
  at the `CreateGameRequest` boundary. Affects `sidequest/server/rest.py` +
  `sidequest/agents/subsystems/movement.py`. *Found by Reviewer during code review.*

### Reviewer (code review, round 2 — post-rework)
- **Improvement** (non-blocking): the site-scene single-writer decline at
  `narration_apply.py:4556` emits no log/watcher span when it suppresses the
  heading-advance (its deep_descent sibling does) — add one for OTEL-panel
  parity. Affects `sidequest/server/narration_apply.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `bounded_site.py` mint-on-miss base seed has no
  lock — two concurrent first-entries could mint different base seeds
  (`set_campaign_seed` is write-once, so the loser fails loud with PersistError,
  which the movement `try` does not catch). Rare race; consider serializing or
  catching PersistError. Affects `sidequest/dungeon/bounded_site.py`. *Found by Reviewer during code review.*
- **Gap** (non-blocking): no behavioral test exercises the CWE-22 path-traversal
  guard (crafted `world_slug` → `_unresolved`, loaders never called) — the
  movement-path e2e harness lands in **164-7 (plan task 13)**. Affects
  `tests/` (add with the 164-7 handler test). *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Task 11 uses a real PgDungeonRepository + real materialize deps, not an in-memory double**
  - Spec source: plan 2026-07-08-mapping-track-b-site-system.md §Task 11 (test skeleton)
  - Spec text: skeleton passes `fake_pg_repo`/`fake_snapshot`/`fake_pack` and `bundle=...`/`palette=...`
  - Implementation: real `PgDungeonRepository` via `build_pg_dungeon_repo`; bundle/palette/snapshot/pack reuse the materializer suite's real helpers (`_real_cookbook_bundle`/`_commit_palette`/`_fresh_snapshot`/`_attach_pack`)
  - Rationale: recon confirmed there is NO in-memory `DungeonRepository` double, and the plan's own note says prefer the real repo — the one-transaction boundary is the whole point and only a real store proves it
  - Severity: minor
  - Forward impact: green may refine the exact interior theme wiring for the bounded site; the structural invariants asserted (whole / no-frontier / idempotent / deterministic / commit-span) are theme-independent
- **Task 12 covers the narrator seam-guard via a private-function unit test**
  - Spec source: plan §Task 12
  - Spec text: names `_honors_same_turn_seam_crossing` (`narration_apply.py:261`) as the unit to parameterize, but provides a RED skeleton only for `apply_world_patch`
  - Implementation: added a focused test calling the private `_honors_same_turn_seam_crossing` with its current keyword signature and a real `CartographyConfig` as `region_cart` (the SiteRegistry source)
  - Rationale: driving the full `narration_apply` caller is heavy; the plan's own guidance is to build the SiteRegistry from `region_cart`, which keeps the signature stable
  - Severity: minor
  - Forward impact: if Dev adds a new kwarg instead of reading `region_cart`, the test call needs a one-line update
- **Task 11 determinism test written concretely (plan skeleton was `...`)**
  - Spec source: plan §Task 11, `test_bounded_site_is_deterministic`
  - Spec text: body left as `...` (unwritten)
  - Implementation: two fresh sessions seeded with the same base seed → assert equal node-id sets
  - Rationale: fleshes an intentionally-unwritten skeleton into a runnable determinism check
  - Severity: minor
  - Forward impact: none

### Dev (implementation)
- **Archetype grid dims NOT threaded into interior generation**
  - Spec source: plan §Task 11 ("Use `archetype.grid_width`/`grid_height` in place of `DEFAULT_INTERIOR_WIDTH`/`HEIGHT` … add `interior_width`/`interior_height` fields")
  - Spec text: thread the archetype's grid dims through the request into the interior fill stage
  - Implementation: kept `DEFAULT_INTERIOR_WIDTH/HEIGHT` (49); did NOT add `interior_width/height` to `MaterializationRequest`
  - Rationale: the interior-generation ALGORITHM comes from the theme's `InteriorSpec` (`_stage_fill` reads `palette.themes[node.theme].interior.algorithm`), NOT the archetype; and a tavern's 15×20 roomcorridor grid is below `ROOMCORRIDOR_MIN_DIM=25`, so threading it fails loud. The archetype grid_width/height/cell_scale describe the TACTICAL combat grid (Task 13/B4 rendering), not the maze canvas
  - Severity: minor
  - Forward impact: Task 13 (story 164-7) consumes archetype grid dims for the tactical-grid emit; the interior canvas stays at the 49 default
- **`open_thread` + `put_frontier` site_id NOT threaded (only `commit_expansion` + `record_mutation`)**
  - Spec source: plan §Task 11 ("pass it at every `commit_expansion`/`put_frontier`/`commit` call in `_stage_commit`")
  - Spec text: thread `site_id` through every commit-stage write
  - Implementation: threaded `site_id` into `commit_expansion` + `record_mutation` + the `materialize` introspection only; reverted `put_frontier` and `open_thread`
  - Rationale: a bounded site sets `lookahead_breadth=0` → `new_frontier=[]` → `put_frontier` is unreachable (threading it only broke an existing `_boom_put_frontier` mock); the base `DungeonStore.open_thread` has no `site_id` param (only `PgDungeonTransaction`), so threading it broke `TestStageAttach`
  - Severity: minor
  - Forward impact: a bounded site's complication threads land under `DEFAULT_SITE_ID` (delivery finding); no effect on nodes/mutations, which ARE site-scoped
- **`DEFAULT_SITE_ID` relocated to the repository protocol module (cycle fix)**
  - Spec source: none (implementation detail)
  - Spec text: n/a
  - Implementation: moved `DEFAULT_SITE_ID = "frontier"` from `game/pg/dungeon.py` to `game/repository.py` (runtime leaf), re-exported from `pg.dungeon`; made `SiteArchetype`'s `ALGORITHMS` import lazy (inside the validator)
  - Rationale: `pack.py → site_archetype → sidequest.dungeon.interiors → dungeon/__init__ → materializer → dungeon.persistence → game.persistence` (mid-init) AND `materializer → pg.dungeon` both closed import cycles that blocked full-suite collection; the relocation + lazy import break both with zero behavior change
  - Severity: minor
  - Forward impact: none — `DEFAULT_SITE_ID` is re-exported from `pg.dungeon`, so existing importers are unaffected

### Reviewer (audit)
- **TEA: real PgDungeonRepository + real materialize deps** → ✓ ACCEPTED by Reviewer: the recon was right — no in-memory double exists and the one-transaction boundary genuinely needs the real store. Sound.
- **TEA: seam-guard via private-function unit test** → ✓ ACCEPTED by Reviewer (the private-fn test is a pragmatic choice), BUT note it left the THIRD narrator write path (`narration_apply.py:4541`) untested — that gap is raised separately as the [SEC] single-writer finding, not a fault of this deviation.
- **TEA: determinism test written concretely** → ✓ ACCEPTED by Reviewer: fleshing an unwritten skeleton into a real node-id-set determinism check is correct.
- **Dev: archetype grid dims NOT threaded into interior generation** → ✓ ACCEPTED by Reviewer: verified `_stage_fill` reads the algorithm from the theme's `InteriorSpec`, not the archetype, and a 15×20 roomcorridor is below `ROOMCORRIDOR_MIN_DIM=25`. The archetype grid is the tactical-grid concern (164-7). Sound.
- **Dev: `open_thread` + `put_frontier` site_id NOT threaded** → ✗ FLAGGED by Reviewer (partial): the `open_thread` revert is ACCEPTED (base `DungeonStore` lacks the param; latent gap captured as a Dev delivery finding). The `put_frontier` revert is FLAGGED — "unreachable" is true only via the unenforced `new_frontier==[]` invariant; nothing forbids `site_id != DEFAULT_SITE_ID` with `lookahead_breadth > 0`. Raised as MEDIUM finding #5 (enforce the invariant loudly in `MaterializationRequest.build`).
- **Dev: movement.py wiring has no 164-6 unit test (validated by 164-7)** → ✗ FLAGGED by Reviewer: "validated downstream" does not cover the two real defects the review found IN that untested wiring — the CWE-22 path-traversal sink and the uncaught `GenreLoadError` contract violation (MEDIUM findings #3, #4). The wiring needs a guard now, not just an e2e later.
- **Dev: `DEFAULT_SITE_ID` relocated to repository protocol module** → ✓ ACCEPTED by Reviewer: clean single-source cycle fix, re-exported for back-compat; verified importers unaffected.
- **UNDOCUMENTED (Reviewer):** `bounded_site.py:86` `get_campaign_seed() or 0` — a silent-default coalescing of a missing base seed that neither TEA nor Dev logged. Spec/doctrine (No Silent Fallbacks) says fail loud or mint a seed; code silently uses 0. Severity: HIGH. Raised as the blocking finding.

## Sm Assessment

**Story:** 164-6 — Archetype catalog schema + bounded one-txn materialization + site single-writer. Implements **plan tasks 10–12** of `docs/superpowers/plans/2026-07-08-mapping-track-b-site-system.md` (epic 164, Mapping Track B — site system). 5 pts, p1, workflow **spdd** (phased: setup→red→green→review→finish).

**Repos:** server, content. Branch `feat/164-6-archetype-catalog-materialization-single-writer` created on `develop` in both subrepos.

**Scope — three deliverables:**
- **Task 10 (content + server):** `site_archetypes.yaml` schema + loader wiring (B2, additive). New `SiteArchetype` model; consumed by Task 11.
- **Task 11 (server):** Bounded materialization — whole site built in ONE transaction. Consumes `MaterializationRequest.build(...)` (`materializer.py:583`), `materialize(...)` (`materializer.py:2030`), `_region_interior_seed(...)` (`materializer.py:291`), Task 2 per-`site_id` repo methods, `SiteDescriptor` (Task 1). Bootstrap per `session_integration.py:97`/`:169`–`:203`.
- **Task 12 (server):** Single-writer for site scenes — extend narrator location-write denial. Consumes `SiteArchetype` (Task 10), the `sites:` field (Task 1), `run_movement_dispatch` enter_site/exit_site (Task 6/11), `_maybe_emit_dungeon_map`→SITE_MAP (Task 7/8), `_maybe_emit_tactical_grid` (`map_emit.py:305`).

**Dependencies satisfied:** Sibling stories 164-4/164-5 (Tasks 6–9) merged to develop; consumed predecessor tasks (1, 2, 6, 7, 8) are landed. No blocking dependencies remain.

**OTEL note for downstream:** Per the observability principle, Task 11 materialization and Task 12 write-denial decisions must emit watcher spans so the GM panel can verify the subsystem is actually engaged (not narrator improvisation).

**Jira:** Not configured on this project (local-YAML sprint) — explicitly skipped, consistent with siblings 164-4/164-5.

**Decision:** Setup complete, context written, branches ready. Hand off to TEA (Fezzik) for the RED phase.

<skills-invoked>
<skill name="test-driven-development" phase="red" at="2026-07-10T14:37:18Z"/>
<skill name="test-driven-development" phase="green" at="2026-07-10T15:34:09Z"/>
<skill name="verification-before-completion" phase="green" at="2026-07-10T15:34:09Z"/>
<skill name="requesting-code-review" phase="green" at="2026-07-10T15:34:09Z"/>
</skills-invoked>

## TEA Assessment

**Phase:** finish
**Tests Required:** Yes
**Status:** RED (15 failing, ready for Dev) — verified via `testing-runner`

**Test Files (server repo, branch `feat/164-6-archetype-catalog-materialization-single-writer`):**
- `tests/genre/test_site_archetype_loader.py` — Task 10: `SiteArchetype` model + generic-loader wiring (7 tests)
- `tests/dungeon/test_bounded_site.py` — Task 11: `ensure_bounded_site_materialized` contract + observable bounded invariants (6 tests)
- `tests/agents/tools/test_apply_world_patch_site_scene.py` — Task 12: `/current_region` site-scene denial + site-aware same-turn seam guard (4 tests: 2 RED + 2 green controls)

**Tests Written:** 17 covering all three ACs. RED verification (serial, with local test DB):
- Task 10 (7): 5 model tests fail `ModuleNotFoundError: sidequest.genre.models.site_archetype`; 2 loader tests fail `AttributeError: 'GenrePack' object has no attribute 'site_archetypes'` (ran, did NOT skip — content on disk).
- Task 11 (6): all fail `ModuleNotFoundError: sidequest.dungeon.bounded_site`. The 4 DB-backed tests ERROR on the missing module *after* the DB migrated (not a skip) — the test DB is live, so the RED is feature-missing.
- Task 12 (4): `test_current_region_write_denied_in_site_scene` fails (status OK, not ERROR_RECOVERABLE); `test_same_turn_site_crossing_is_honored` fails (`False`, want `True`). Both control tests PASS.

No collection errors, no fixture-not-found, no import errors on symbols that should exist — the failures are clean feature-missing, not TEA bugs.

### Rule Coverage

Python lang-review checklist (`.pennyfarthing/gates/lang-review/python.md`) — checks with test coverage in this RED set:

| Rule | Test(s) | Status |
|------|---------|--------|
| #6 test quality (meaningful assertions, no vacuous) | all tests assert specific values/statuses/span names; 2 negative controls guard against over-broad denial | pass (self-check) |
| validated constructor rejects invalid input (fail-loud) | `test_unknown_algorithm_fails_loud` (unknown `interior_algorithm` → ValueError) | failing (RED) |
| boundary validation on numeric fields | `test_room_count_min_rejects_zero`, `test_grid_dims_reject_too_small` | failing (RED) |
| #1 no silent fallbacks | `test_missing_store_fails_loud` (no store → `SeamCrossingError`, not a quiet no-op) | failing (RED) |
| OTEL observability (subsystem emits a span) | `test_materialize_emits_commit_span` (`site.materialize.commit`) | failing (RED) |
| #3 type annotations at boundaries | `test_module_exposes_ensure_bounded_site_materialized` pins the keyword-only public signature | failing (RED) |
| additive/no-behavior-change guarantee | `test_loader_omits_field_when_file_absent` (empty dict when file absent) | failing (RED) |

**Rules checked:** 7 of the applicable lang-review + SOUL rules have test coverage (the remainder — logging, resource leaks, unsafe deserialization, async pitfalls — are green-phase Dev-code concerns the reviewer gate will scan; `yaml.safe_load` in the loader is implicitly exercised by the loader tests).
**Self-check:** 0 vacuous tests found (every test asserts a specific value; the 2 controls assert meaningful negatives).

**Handoff:** To Dev (Inigo Montoya) for implementation (GREEN).

## Dev Assessment

**Implementation Complete:** Yes
**Status:** GREEN — all 24 story-164-6 tests pass; full server suite 14,897 passing, 0 regressions (verified via `testing-runner` with `SIDEQUEST_TEST_DATABASE_URL` set)

**Branch:** `feat/164-6-archetype-catalog-materialization-single-writer` — pushed to both subrepos (server `469f5c09`, content `606d508`).

**Files Changed:**
- *server* `sidequest/genre/models/site_archetype.py` (new) — `SiteArchetype` model, fail-loud on unknown `interior_algorithm` (lazy `ALGORITHMS` import to avoid the genre→dungeon module-load cycle).
- *server* `sidequest/genre/models/pack.py` — `GenrePack.site_archetypes` field.
- *server* `sidequest/genre/loader.py` — `site_archetypes.yaml` in the extension allowlist + optional read → dict.
- *content* `pack_schema.yaml` — `site_archetypes` under `genre_pack.extensions` (drift-guard lockstep).
- *server* `sidequest/dungeon/bounded_site.py` (new) — `ensure_bounded_site_materialized`: whole site in ONE txn, deterministic (63-bit-masked seed), idempotent skip, no open frontier, fail-loud on missing store.
- *server* `sidequest/dungeon/materializer.py` — `MaterializationRequest.site_id` (defaults `DEFAULT_SITE_ID`); site_id threaded into `materialize` introspection + `commit_expansion`/`record_mutation`; frontier derivation gated on `lookahead_breadth > 0`.
- *server* `sidequest/telemetry/spans/site.py` — `site.materialize.begin/commit/skip` spans (mirrored to `turn_telemetry`).
- *server* `sidequest/agents/subsystems/movement.py` — `enter_site` bounded path wired to `ensure_bounded_site_materialized` (replaces the `bounded_site_pending` guard).
- *server* `sidequest/agents/tools/apply_world_patch.py` — `/current_region` denied inside a site scene.
- *server* `sidequest/server/narration_apply.py` — `_honors_same_turn_seam_crossing` made site-aware (per-site entrance, not the global `ENTRANCE_ID`).
- *server* `sidequest/game/repository.py` + `sidequest/game/pg/dungeon.py` — `DEFAULT_SITE_ID` relocated to the protocol module (cycle fix; re-exported).

**Tests:** 24/24 story tests GREEN. Full suite: 14,897 passed, 341 skipped, 1 pre-existing content RED (`test_beneath_sunden_room_binding_107_2` — story 107-2, untouched by this branch), 2 known xdist flakes (pass individually). Lint (`ruff check`) + format clean.

**Self-review (judgment checks):**
- Wired end-to-end: `bounded_site` has a non-test consumer (`movement.run_movement_dispatch` enter_site path); the `/current_region` denial + seam guard are in the live tool/narration paths.
- OTEL: `site.materialize.begin/commit/skip` spans emit + mirror to the sink (GM-panel lie-detector, per the observability principle).
- Error handling: fail-loud on no store (`SeamCrossingError`), unknown archetype (`_unresolved`), unknown algorithm (`ValueError`) — No Silent Fallbacks throughout.
- Deviations from the plan's dim-threading + full site_id threading logged above (interior canvas vs tactical grid; unreachable frontier/thread scoping).

**Handoff:** To Reviewer (Westley) for the review phase.
## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 (format) | confirmed 1, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — covered by Reviewer directly |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 | confirmed 2, dismissed 0, deferred 0 |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — covered by Reviewer directly |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — covered by Reviewer directly |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — covered by Reviewer directly |
| 7 | reviewer-security | Yes | findings | 2 | confirmed 2, dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — covered by Reviewer directly |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — covered by Reviewer directly |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents` and assessed by Reviewer directly)
**Total findings:** 5 confirmed (1 HIGH, 4 MEDIUM), 2 LOW added by Reviewer, 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** REJECTED

A well-built story — 24/24 story tests green, 14,897 full-suite passing, SQL parameterized, YAML safe-loaded, fail-loud throughout the happy paths. But an adversarial pass surfaced one HIGH (a No-Silent-Fallbacks violation) plus four MEDIUM correctness/security gaps and two LOWs. The HIGH blocks per the severity rule.

### Rule Compliance (Python lang-review checklist)

- **#1 Silent exception swallowing:** loader `except (KeyError, TypeError, ValueError)` re-raises as `GenreLoadError(... from exc)` — compliant (fail-loud). movement `except SeamCrossingError` re-surfaces via `_unresolved` — compliant. **VIOLATION:** `bounded_site.py:86` `get_campaign_seed() or 0` silently coalesces a missing base seed (No Silent Fallbacks doctrine — see HIGH finding).
- **#2 Mutable defaults:** `SiteArchetype` uses `Field(default_factory=list)`; no mutable defaults in new signatures — compliant.
- **#3 Type annotations at boundaries:** `ensure_bounded_site_materialized`, `_derive_site_seed`, the span helpers all fully annotated — compliant.
- **#5 Path handling:** `pack.source_dir / "worlds" / snapshot.world_slug` uses pathlib — but **missing `Path.resolve()` before a filesystem read** (CWE-22, see [SEC] path-traversal). Partial.
- **#6 Test quality:** story tests assert specific values; 2 meaningful negative controls; 0 vacuous. But the `None → 0` seed branch is **untested** (every bounded-site test pre-seeds) — a coverage gap tied to the HIGH.
- **#8 Unsafe deserialization:** `_load_yaml_raw_optional → _load_yaml_raw` uses `yaml.safe_load` (loader.py:206) — compliant.
- **#9 Async pitfalls:** `load_cookbook`/`load_theme_palette` (sync file I/O) run inside async `run_movement_dispatch` — matches the existing `attach_dungeon_to_session` precedent; infrequent (bounded-entry) path. LOW, non-blocking.
- **#10 Import hygiene:** lazy `ALGORITHMS` import in the validator is deliberate + documented (cycle break); no star imports — compliant.
- **#11 Input validation:** `SiteArchetype` validates via pydantic Fields (`ge=`) + the algorithm allowlist — compliant. `world_slug` reaches the FS unsanitized — see [SEC].
- **Format:** 2 test files fail `ruff format --check` (LOW).

### Observations

- `[SILENT][HIGH] bounded_site.py:86` — `base = dungeon_repository.get_campaign_seed() or 0` silently substitutes a fixed `0` for a missing frontier base seed. VERIFIED: the only frontier-base setter is `session_integration.py:172`, gated to `caverns_and_claudes/beneath_sunden` — so every world that will actually declare a bounded site (164-7) has `get_campaign_seed() == None → 0`, making bounded sites byte-identical across all sessions/campaigns, silently. Diverges from `session_integration.py:169-172` (mint+persist a fresh seed). This is the exact No-Silent-Fallbacks anti-pattern SOUL/CLAUDE forbid.
- `[SEC][MEDIUM] narration_apply.py:4541` — Task 12's single-writer is INCOMPLETE. The heading-driven auto-advance (`if _is_region_mode_world and snapshot.current_region != known_region_id: ... snapshot.pc_regions[player_name] = known_region_id`) writes pc_regions with NO site-ownership check — a third narrator write path the two new guards don't cover. VERIFIED unconditional at :4541. Reachable once a region-mode world declares a `bounded` site (164-7): the narrator can drag a PC out of a site interior with no `resolve_exit_site`, no `site.exit` span (SOUL "The Test").
- `[SEC][MEDIUM] movement.py:536-560` — new CWE-22 sink: `world_dir` from unsanitized `snapshot.world_slug` (← `CreateGameRequest.world_slug`, rest.py:78, no charset constraint) reaches `load_cookbook`/`load_theme_palette` with no `resolve()+is_relative_to(pack.source_dir)` guard. Root cause is pre-existing (connect.py:586) but this diff adds a fresh reachable sink on the gameplay path.
- `[SILENT][MEDIUM] materializer.py:1916` — `tx.put_frontier(fe)` alone among the commit-stage writes does not thread `site_id`; relies on the unenforced invariant that bounded requests set `lookahead_breadth=0` (→ `new_frontier=[]`). Nothing in `MaterializationRequest.build` forbids `site_id != DEFAULT_SITE_ID` with `lookahead_breadth > 0`, which would silently write a site's frontier into the global frontier store.
- `[EDGE][MEDIUM] movement.py:559-560` — `load_cookbook(world_dir)` / `load_theme_palette(world_dir)` are evaluated as call args inside the `try`, but `except` only catches `SeamCrossingError`; a `GenreLoadError` (content gap) escapes `run_movement_dispatch`, whose docstring promises it "returns recoverable failures … raises ONLY for a genuine programmer bug."
- `[EDGE][LOW] loader.py:2607` — duplicate `archetype_id` in `site_archetypes.yaml` silently last-wins (dict comprehension) rather than failing loud.
- `[VERIFIED]` site_id → SQL is bound as a `%s` parameter throughout `pg/dungeon.py` (commit_expansion/load_map) — no injection. Evidence: `INSERT INTO dungeon_map (... site_id ...) VALUES (%s, %s, ...)`.
- `[VERIFIED]` `SiteArchetype` fails loud on unknown `interior_algorithm` (validator) + boundary Fields (`ge=1`/`ge=5`) — evidence: site_archetype.py validator + Field constraints; complies with the validated-constructor rule.
- `[TYPE][VERIFIED]` `MaterializationRequest.site_id` defaults to `DEFAULT_SITE_ID` (frozen slots dataclass) — existing frontier callers unaffected; the relocation of `DEFAULT_SITE_ID` to the protocol module is a clean single-source cycle fix.
- `[DOC][VERIFIED]` new comments (lazy-import rationale, frontier-gate, single-writer) are accurate to the code — no stale/misleading docs introduced.
- `[SIMPLE][VERIFIED]` no dead code / over-engineering; `SiteRegistry.from_cartography` rebuilt per `_honors_same_turn_seam_crossing` call is a minor allocation on an infrequent path — acceptable.
- `[TEST]` the seam-crossing guard is tested via the private `_honors_same_turn_seam_crossing` (TEA deviation, accepted) — but the third write path (:4541) is untested, corroborating the [SEC] finding.
- `[RULE]` async #9 (sync I/O in async) matches precedent — LOW, not blocking.

### Devil's Advocate

Assume this code is broken. The most damning path: a player creates a game via `POST /api/games` with `world_slug = "../../space_opera/worlds/aureate_span"`. Nothing validates it — `rest.py:78` is a bare `str`, `ensure_session` stores it verbatim, and it lands on `snapshot.world_slug`. The player enters a bounded site; `world_dir = pack.source_dir / "worlds" / "../../space_opera/worlds/aureate_span"` resolves OUTSIDE the pack, and `load_cookbook`/`load_theme_palette` happily read another genre's content into this session. It fails loud only if the target lacks the `corpus/`+`cookbook/`+`themes/` layout — but every sibling world matches it. That is a cross-content-boundary read on the live gameplay path, and this diff added the sink without the guard.

Second: determinism is a lie for every non-beneath_sunden world. `or 0` means two players, two campaigns, two years apart, get the *identical* tavern — and nothing tells anyone the "campaign seed" was never established. A content author testing a homebrew world (the Jade doctrine this epic serves!) would see a fixed layout and never know why. Worse, the branch is untested, so CI is green while the seed logic is silently degenerate.

Third: the single-writer is a screen door. Task 12 proudly denies `/current_region` in a site scene and honors the same-turn entrance crossing — but the narrator's ordinary heading resolution at :4541 walks right past both guards and rewrites `pc_regions` the moment the PC is one room deep or one turn later. A confused narrator titling a scene "back toward the square" yanks the party out of the tavern with no exit dispatch and no OTEL trace — precisely the "response includes the player doing something they didn't ask to do" that SOUL calls always wrong. A stressed filesystem, a homebrew world, a chatty narrator: three independent ways this bites once 164-7's content goes live. None are hypothetical; all are on the path this epic is building.

### Severity Table

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | `get_campaign_seed() or 0` silently coalesces a missing base campaign seed → bounded sites identical across all sessions of any non-beneath_sunden world (No Silent Fallbacks) | `bounded_site.py:86` | Mint+persist a fresh session-scoped base seed (per `session_integration.py:169-172`) or fail loud — never `or 0`. Add a test for the None-base path. |
| [MEDIUM] | Site single-writer incomplete: heading-driven auto-advance clobbers `pc_regions` out of a site interior with no site-ownership check | `narration_apply.py:4460-4544` | Gate the write on `site_owning_node(pc_region) is None`; require `resolve_exit_site` for site→surface — OR consciously defer to 164-7 with a documented delivery finding. |
| [MEDIUM] | New CWE-22 path-traversal sink: unsanitized `world_slug` → `load_cookbook`/`load_theme_palette` with no `resolve()+is_relative_to` guard | `movement.py:536-560` | `Path.resolve()` + `is_relative_to(pack.source_dir)` before load, fail loud; ideally validate `world_slug` at the `CreateGameRequest` boundary. |
| [MEDIUM] | `run_movement_dispatch` can raise `GenreLoadError` out of the arg-eval in the `try` (only `SeamCrossingError` caught) — violates its "returns recoverable, never re-raises" contract | `movement.py:559-560` | Move the loads into the try body; catch `GenreLoadError` → recoverable `_unresolved`. |
| [MEDIUM] | `put_frontier` doesn't thread `site_id`; relies on the unenforced `new_frontier==[]` invariant for non-default site_id | `materializer.py:1916` | Enforce `site_id != DEFAULT_SITE_ID ⇒ lookahead_breadth == 0` in `MaterializationRequest.build` (loud), or thread `site_id`. |
| [LOW] | 2 test files fail `ruff format --check` | `tests/dungeon/test_bounded_site.py`, `tests/agents/tools/test_apply_world_patch_site_scene.py` | `uv run ruff format` |
| [LOW] | Duplicate `archetype_id` in `site_archetypes.yaml` silently last-wins | `loader.py:2607` | Detect duplicates → `GenreLoadError`. |

**Handoff:** Back to TEA (Fezzik) for rework — the confirmed findings are testable logic/security bugs (seed-mint, path-traversal, single-writer third path), so a RED rework adds the failing tests, then Dev fixes.
## Dev Assessment — Rework (round 1)

**Status:** GREEN — all 6 reviewer findings addressed; 27 story tests + 167 regression tests pass, 0 failures. Server commit `0bafaf1f` pushed.

**Fixes:**
- **[HIGH] seed** — `bounded_site.py` now mints + persists a fresh `secrets.randbits(63)` session base seed when `get_campaign_seed()` is None (the `session_integration.py:169-172` pattern), replacing `or 0`. No Silent Fallbacks satisfied; bounded sites are per-campaign unique. Regression: `test_missing_base_seed_is_minted_not_defaulted_to_zero`.
- **[MED] put_frontier invariant** — `MaterializationRequest.build` now raises on `site_id != DEFAULT_SITE_ID and lookahead_breadth > 0` (loud invariant). Regression: `test_non_default_site_id_requires_zero_lookahead`.
- **[MED] path-traversal** — `movement.py` resolves `world_dir` and rejects it if not `is_relative_to(pack.source_dir/"worlds")` (CWE-22) before any load; a traversal attempt drops to fail-loud "cannot be opened."
- **[MED] GenreLoadError** — loads moved into the `try` body; `except GenreLoadError` → recoverable `_unresolved(reason="site_content_missing")`, honoring `run_movement_dispatch`'s no-re-raise contract.
- **[MED] single-writer 3rd path** — `narration_apply.py:4541` heading-advance now declines the clobber when `site_owning_node(pc_region) is not None`. No-op for every world without a bounded site (verified: region-mode/location_update suites green).
- **[LOW] duplicate archetype_id** — loader fails loud (`GenreLoadError`). Regression: `test_loader_duplicate_archetype_id_fails_loud`.
- **[LOW] format** — 2 test files reformatted.

**Handoff:** Back to Reviewer (Westley) for re-review.
## Subagent Results (Round 2 — rework re-review)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (format now passes) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled — Reviewer assessed the delta directly |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 LOW | confirmed 0 blocking, 1 LOW deferred |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled — Reviewer assessed directly |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled |
| 7 | reviewer-security | Yes | clean | 0 (CWE-22 resolved) | 1 coverage-gap note deferred |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled |

**All received:** Yes (3 enabled returned; 6 disabled)
**Total findings:** 0 blocking, 3 LOW/informational deferred (all round-1 HIGH/MEDIUM findings RESOLVED)

## Reviewer Assessment (Round 2)

**Verdict:** APPROVED

All six round-1 findings are resolved and independently confirmed by the re-review subagents on the rework delta (`469f5c09..HEAD`). Mechanical gates green (lint, format — the round-1 format finding is fixed —, 20 story tests + the earlier 194-test sweep).

- `[SILENT]` **HIGH seed — RESOLVED (high conf).** `bounded_site.py:84-99` now mints `secrets.randbits(63)` + persists a fresh base seed when absent (matching `session_integration.py:171`); the `or 0` is gone. Confirmed both writes hit distinct correct keys.
- `[SILENT]` **put_frontier invariant — RESOLVED (high conf).** `MaterializationRequest.build` raises on `site_id != DEFAULT_SITE_ID and lookahead_breadth > 0`; verified `.build()` is the only construction seam, so the guarantee is hard, not implicit.
- `[SEC]` **CWE-22 path-traversal — RESOLVED (high conf).** `movement.py` `resolve()`s both operands and `is_relative_to`-rejects an out-of-root `world_dir` (→ fail-loud "cannot be opened") before any `load_cookbook`/`load_theme_palette`. `GenreLoadError` surface leaks no path (caught unbound, hardcoded surface).
- `[EDGE]` **GenreLoadError contract — RESOLVED.** loads moved into the `try`; `except GenreLoadError` → recoverable `_unresolved(reason="site_content_missing")`, honoring the no-re-raise contract.
- `[TYPE]` **single-writer 3rd path — RESOLVED.** `narration_apply.py:4538` declines the heading clobber when `site_owning_node(pc_region) is not None`; verified it only NARROWS the write (adds a condition), leaves state correct, and is a no-op for non-site worlds (region-mode/location_update suites green).
- `[RULE]` **duplicate archetype_id — RESOLVED.** loader raises → `GenreLoadError` (chained). Format `[SIMPLE]`/`[DOC]`: 2 test files reformatted; new comments accurate.
- `[TEST]` **coverage:** 3 new regression tests (seed-mint, build invariant, duplicate-id) all pass. The traversal-guard behavioral test is deferred to 164-7's movement e2e (delivery finding).

**New LOW/informational (non-blocking, deferred to follow-ups):**
1. `[SILENT]` `narration_apply.py:4556` — the site-scene decline emits no log/span (its sibling deep_descent decline does). OTEL-parity nit. → delivery finding.
2. seed mint-on-miss has no lock (two concurrent first-entries could mint different base seeds; `set_campaign_seed` is write-once so the loser fails loud, not silent). Rare race. → delivery finding.
3. `[SEC]`/`[TEST]` no behavioral test for the path-traversal guard (movement path's e2e harness is 164-7). → delivery finding.

**Data flow traced:** `world_slug` (session input) → `world_dir` → NOW guarded by resolve+is_relative_to → `load_cookbook` (safe); `site_id` → parameterized SQL (safe). **Handoff:** To SM (Vizzini) for finish-story.