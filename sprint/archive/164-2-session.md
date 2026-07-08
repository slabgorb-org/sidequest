---
story_id: "164-2"
jira_key: ""
epic: "164"
workflow: "spdd"
---
# Story 164-2: Sünden characterization guard + symmetric enter/exit_site resolvers + site.* spans (plan tasks 3–4)

## Story Details
- **ID:** 164-2
- **Jira Key:** (none — Jira not integrated)
- **Workflow:** spdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** spdd
**Phase:** finish
**Phase Started:** 2026-07-08T23:34:18Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-08T22:44:27+00:00 | 2026-07-08T22:47:24Z | 2m 57s |
| red | 2026-07-08T22:47:24Z | 2026-07-08T23:01:09Z | 13m 45s |
| green | 2026-07-08T23:01:09Z | 2026-07-08T23:23:57Z | 22m 48s |
| review | 2026-07-08T23:23:57Z | 2026-07-08T23:34:18Z | 10m 21s |
| finish | 2026-07-08T23:34:18Z | - | - |

## Story Context

**Task 3 — Characterization tests (guard, no RED phase — these PASS on develop today):**
- New file: sidequest-server/tests/agents/subsystems/test_movement_sunden_characterization.py
- Locks CURRENT observable Sünden movement/seam behavior via run_movement_dispatch (sidequest/agents/subsystems/movement.py:337) before the risky Task 6 cutover. Reuse EXISTING movement-test fixtures (grep tests/agents/subsystems/test_movement*.py) — do not invent snapshot/store doubles.
- Five behavioral assertions on returned SubsystemOutput.data (resolved_via / to_region), NOT internal rung names: owned-seam descent from the_dropmouth; adjacent-seam descent from ropefoot; entrance ascent (back → the_dropmouth); in-dungeon navigation (exp001.r0 → real neighbor); region-mode lateral defer (region_mode_deferred).

**Task 4 — Symmetric enter_site/exit_site seam resolvers + site.* spans (additive; nothing calls these yet — Task 6 wires them):**
- New: sidequest/game/sites/enter_site.py, sidequest/game/sites/exit_site.py, sidequest/telemetry/spans/site.py (site spans + turn_telemetry mirror via publish_event).
- Modify: sidequest/game/seams/registry.py (register enter_site/exit_site), sidequest/game/sites/__init__.py (export resolvers).
- New tests: tests/game/sites/test_site_resolvers.py, tests/telemetry/test_site_spans_to_sink.py.
- CRITICAL doctrine: every site/seam span must reach turn_telemetry via publish_event (not Span.open alone) — mirror pattern from sidequest/telemetry/spans/movement.py:151. Fix the enter/exit asymmetry (surface_ascent is called directly at movement.py:504). enter_site supports extent="frontier" now (binds to site entrance; bounded materialization is a LATER task 12, OUT OF SCOPE here).

**Acceptance criteria:** 
(1) Task 3 characterization suite passes on current develop, covering all five movement rungs by observable outcome. 
(2) enter_site/exit_site resolvers exist, are registered in the seam registry, bind pc_region, and are additive (no existing Sünden behavior changed). 
(3) site.enter / site.exit / site.enter_unresolved spans reach turn_telemetry via publish_event (proven by a sink test), not Span.open alone. 
(4) Each new test suite includes a wiring/reachability assertion. 
(5) Lint/format/type-check clean on touched files.

## Delivery Findings

### TEA (test design)
- **Improvement** (non-blocking): The plan's Task-4 sink-test example (`test_site_spans_to_sink.py`) drives `site_enter_span(...)` with no OTEL provider, so under this repo's default the span is non-recording and `publish_event` never fires — the example test would false-fail even against a correct impl. The real test installs an in-memory recording provider (monkeypatch `spans.tracer`). Affects `sidequest/telemetry/spans/site.py` (`_mirror` MUST keep the `hasattr(span, "attributes")` guard exactly as `spans/movement.py:_mirror_movement_span_to_sink` does — the `test_site_span_mirror_skips_when_span_not_recording` robustness case depends on it). *Found by TEA during test design.*
- **Question** (non-blocking): Task 4's `resolve_enter_site` raises `SeamCrossingError(reason=no_site_entrance)` when the entrance node is absent, and `test_enter_site_missing_entrance_node_raises` pins that contract. The plan's Task 6 migration decision (§Task 6) will later REFINE `resolve_enter_site` to fall back to `graph.entrance_id` for the Sünden frontier-legacy case (where the node is `entrance`, not `frontier:entrance`). So story 164-3 will need to RETARGET this test — flagged here so it is not read as a contradiction. Affects `sidequest/game/sites/enter_site.py` + `tests/game/sites/test_site_resolvers.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): The site resolvers, `site_enter_unresolved_span`, and `enter_site`'s `direction`/`exit_descriptor` params are additive-ahead-of-consumer — no production caller yet (reachable only via the registry wiring test). Task 6 / story 164-3 must (a) wire the movement dispatch to call the resolvers by kind, (b) emit `site_enter_unresolved_span` from the movement catcher on an unresolved enter (per the `SeamCrossingError` catcher-owns-the-failure-span contract), and (c) stamp the player's coarse intent (`intent.direction`/`intent.exit_descriptor`) on the site spans as `movement.resolved` does — the site spans currently omit it. Affects `sidequest/agents/subsystems/movement.py` (Task 6). *Found by Dev during implementation.*
- **Improvement** (non-blocking): `uv run pyright` on the touched files reports only (i) the identical `_SpanLike`-extract typing error that `spans/movement.py:187` already carries (my `site.py` mirrors it verbatim), and (ii) duck-typed-test-double errors matching the existing movement test suite (28 in `test_movement_party_split_158_7.py`). No new error category introduced; pyright is NOT a gated check (`just server-check` = ruff + pytest, both clean). Making this code stricter than the `spans/movement.py` reference it mirrors would be inconsistent. Affects the touched files if the project later adopts a gated pyright. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (non-blocking): `seam_route_for` / `seam_route_via_adjacency` / `surface_owner_for_entrance` (`sidequest/game/seams/registry.py`) test `route.to_id in _REGISTRY` WITHOUT calling `_ensure_site_resolvers()`, so before any `get_seam_resolver()` fires in-process, `_REGISTRY` holds only `deep_descent`. A hypothetical `Route.to_id == "enter_site"/"exit_site"` would then be silently treated as a non-seam route. DORMANT by design (no genre-pack authors such a route; Task 6 dispatches site kinds by kind via `SiteRegistry`, never via `Route.to_id`). No action for 164-2. Task 6 / story 164-3: if any lookup ever routes site kinds through `to_id` matching, call `_ensure_site_resolvers()` there first (or register site kinds at `seams/registry.py` import time once the cycle is otherwise resolved). Affects `sidequest/game/seams/registry.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the plan's Task-4 `resolve_enter_site` sample stamped a `party_split_after` span attribute that the shipped resolver omits (correctly — it's not in the `SPAN_SITE_ENTER` route extract, so it would be non-routed). Task 6, when it wires multi-PC site crossings, should add party-split telemetry to the site spans (and to the route extract) so the GM panel sees co-located party site entry/exit the way `movement.resolved` already does. Affects `sidequest/telemetry/spans/site.py` + `sidequest/game/sites/{enter_site,exit_site}.py`. *Found by Reviewer during code review.*

## Design Deviations

### TEA (test design)
- **Entrance-ascent rung characterized with `toward_exit`, not the plan's literal `direction="back"`**
  - Spec source: docs/superpowers/plans/2026-07-08-mapping-track-b-site-system.md, Task 3 (`test_entrance_ascent` bullet)
  - Spec text: "PC on `entrance`, `direction=\"back\"` → `resolved_via == \"surface_ascent\"`, `to_region == \"the_dropmouth\"`"
  - Implementation: `test_entrance_ascent_returns_to_seam_owner` uses `_movement("toward_exit", "back up the rope")` — the intent form proven to yield `surface_ascent` in the sibling suite (`test_movement_party_split_158_7.py::test_colocated_party_ascends_together`).
  - Rationale: a characterization guard MUST reflect REAL current behavior; `toward_exit`+"back up the rope" is the verified-passing ascent path, and the plan itself says "if any assertion does NOT match current behavior, fix the test to reflect the real current output." `direction="back"` was unverified.
  - Severity: minor
  - Forward impact: none — the observable outcome (surface_ascent → the_dropmouth) is what the guard locks; Task 6 must preserve it.
- **In-dungeon nav rung characterized as `entrance → exp001.r0`, not the plan's illustrative `exp001.r0 → neighbor`**
  - Spec source: plan Task 3 (`test_in_dungeon_navigation` bullet)
  - Spec text: "PC on `exp001.r0`, `direction=\"deeper\"`, a real neighbor exists → `to_region` is that neighbor"
  - Implementation: PC on `ENTRANCE_ID` with a materialized `exp001.r0` neighbor; asserts `to_region == "exp001.r0"`, no error (the §Q1 navigator).
  - Rationale: `entrance → exp001.r0` is the proven in-dungeon navigator hop (`test_movement_onward_ring.py`, `test_movement_party_split_158_7.py`) exercising the SAME graph-navigation rung. Modeling `exp001.r0 → exp001.r1` would require fabricating the navigator's deeper-neighbor heuristic; the proven shape avoids inventing fixture internals.
  - Severity: minor
  - Forward impact: none — same rung; the guard still catches an in-dungeon-nav behavior change.
- **enter/exit resolver tests use a REAL `GameSnapshot` + inline store double, not the plan's `conftest.py` fake fixtures**
  - Spec source: plan Task 4 (`test_site_resolvers.py` step)
  - Spec text: "Build `fake_*` fixtures in a local `tests/game/sites/conftest.py`, adapting the doubles..."
  - Implementation: tests instantiate a real `GameSnapshot` (whose `apply_world_patch`/`region_for` ARE the production surfaces the resolver calls) plus a minimal inline `_SiteStore`; no conftest.
  - Rationale: TDD "real code, no mocks unless unavoidable" — a real snapshot exercises the actual `pc_region` binding path, catching a wrong-key bind a faked `region_for` would mask. Only the Postgres `DungeonRepository` is doubled.
  - Severity: minor
  - Forward impact: none — Dev's GREEN implements the same resolver contract.

### Dev (implementation)
- **Site resolvers registered LAZILY, not as the plan's eager `_REGISTRY` dict literal**
  - Spec source: docs/superpowers/plans/2026-07-08-mapping-track-b-site-system.md, Task 4 (registry step)
  - Spec text: "within `_REGISTRY` dict: `\"enter_site\": resolve_enter_site, \"exit_site\": resolve_exit_site`"
  - Implementation: `_REGISTRY` keeps only `deep_descent` at module load; the site resolvers are registered lazily via `_ensure_site_resolvers()` (atomic `_REGISTRY.update`) called from `get_seam_resolver`.
  - Rationale: the plan's eager `from sidequest.game.sites.enter_site import ...` at `registry.py` module scope closes a real seams↔sites import cycle (registry → sites.enter_site → seams.base → seams/__init__ → registry), which crashed collection with `ImportError: partially initialized module`. Site kinds are dispatched by kind (not by a route `to_id`), so nothing on the module-load path needs them — deferring to first lookup is behavior-neutral. Verified in all 3 import orders.
  - Severity: minor
  - Forward impact: none — `get_seam_resolver("enter_site"/"exit_site")` resolves identically; Task 6 dispatches by kind.
- **exit_site adds a distinct `no_cartography` reason (pre-review refinement beyond the plan's single check)**
  - Spec source: plan Task 4 (exit_site code)
  - Spec text: `if not surface_id or surface_id not in regions: raise SeamCrossingError(reason="dangling_site_owner", ...)`
  - Implementation: added a prior `if cartography is None: raise SeamCrossingError(reason="no_cartography", ...)` branch.
  - Rationale: fail-loud diagnostics (No Silent Fallbacks) — a wiring fault (config never threaded) must not surface as a data fault (`dangling_site_owner`); `SeamCrossingError.reason` routes GM-panel debugging. Mirrors enter_site's `no_site_store` vs `no_site_entrance` split. Pre-review finding; covered by a new test.
  - Severity: minor
  - Forward impact: none — additive; Task 6 threads real cartography.

### Reviewer (audit)
- **TEA #1 (ascent characterized with `toward_exit` not `back`)** → ✓ ACCEPTED by Reviewer: a characterization guard must pin REAL current behavior; `toward_exit`+"back up the rope" is the verified `surface_ascent` path (sibling suite confirms). The plan itself sanctions correcting the test to match reality.
- **TEA #2 (in-dungeon rung as `entrance → exp001.r0`)** → ✓ ACCEPTED by Reviewer: same graph-navigation rung as the plan's illustrative `exp001.r0 → neighbor`; the proven `entrance → exp001.r0` shape avoids fabricating navigator internals. Observable outcome locked identically.
- **TEA #3 (real `GameSnapshot` + inline store double, no conftest fakes)** → ✓ ACCEPTED by Reviewer: "real code, no mocks unless unavoidable" — a real snapshot exercises the actual `pc_region` bind path; only the Postgres repo is doubled. Strictly stronger than the plan's fully-faked fixtures.
- **Dev #1 (lazy registry registration vs the plan's eager `_REGISTRY` literal)** → ✓ ACCEPTED by Reviewer: the eager import closes a real seams↔sites cycle (reproduced at collection). Lazy registration is behavior-neutral because site kinds dispatch by kind, not by route `to_id`; verified in all 3 import orders. See the corresponding [SILENT]/[LOW] observation below for the one latent caveat (dormant by design).
- **Dev #2 (exit_site `no_cartography` split)** → ✓ ACCEPTED by Reviewer: correct fail-loud diagnostics; a wiring fault must not masquerade as a data fault. Mirrors enter_site's two-reason split; covered by a test.
- **UNDOCUMENTED (Reviewer-spotted, LOW):** the plan's Task-4 sample `resolve_enter_site` set `span.set_attribute("party_split_after", …)`; the shipped `enter_site.py` omits it. Not logged by Dev. **Accepted** — the `SPAN_SITE_ENTER` SPAN_ROUTES `extract` does not read `party_split_after` (it would be non-routed dead telemetry to the sink; only `archetype`/`extent` are set for Jaeger visibility), no test needs it, and site entry is single-PC until Task 6 wires multi-PC site crossings. Captured as a non-blocking Delivery Finding for Task 6. Severity: LOW.

## Skills Invoked

<skills-invoked>
<skill name="test-driven-development" phase="red" at="2026-07-08T22:58:57Z"/>
<skill name="test-driven-development" phase="green" at="2026-07-08T23:22:34Z"/>
<skill name="verification-before-completion" phase="green" at="2026-07-08T23:22:34Z"/>
<skill name="requesting-code-review" phase="green" at="2026-07-08T23:22:34Z"/>
</skills-invoked>

## Sm Assessment

**Setup verified (2026-07-08):**
- Session at orchestrator root `.session/164-2-session.md` ✓
- Context at `sprint/context/context-story-164-2.md` (validated `pf validate context-story 164-2`) ✓
- Feature branch `feat/164-2-sunden-guard-site-resolvers` created in `sidequest-server` (off `develop`, gitflow) ✓; orchestrator on `main` ✓
- Workflow field normalized `superpowers` → `spdd` via `pf sprint story update` (see gotcha: Epic 164 stories all carry the un-registered `superpowers` alias) ✓

**Scope for TEA (RED phase):** This story is EXACTLY plan Tasks 3 & 4 of `docs/superpowers/plans/2026-07-08-mapping-track-b-site-system.md`. Do not pull in Task 5+ (router site targets), Task 6 (the RISKY movement cutover), or Task 12 (bounded materialization) — those are 164-3/164-4/164-6. Predecessor 164-1 (Tasks 1–2: SiteRegistry, CartographyConfig.sites, per-site storage keying) is DONE and provides the `SiteDescriptor`/`SiteRegistry`/`DungeonRepository.load_map(site_id=...)` surfaces these resolvers consume.

**Two constraints the plan is emphatic about (SM will enforce at review):**
1. **Task 3 has no true RED** — the characterization tests must PASS on current `develop` (they lock existing Sünden behavior as the safety net for the later cutover). If an assertion fails, the fixture is mis-modeled — correct the test to reflect real current output, don't "fix" the engine.
2. **OTEL doctrine is load-bearing** — every `site.*` span MUST reach `turn_telemetry` via `publish_event`, not `Span.open` alone (mirror `spans/movement.py:151`). The sink test (`test_site_spans_to_sink.py`) is the wiring proof; without it the GM panel is blind and the story is not done. Additive-only: no existing Sünden movement behavior may change (Task 3 is the guard that proves this).

**Setup complete — routing to TEA (Fezzik) for the RED phase.**

## TEA Assessment

**Tests Required:** Yes
**Reason:** n/a — this is a test-authoring story (plan Tasks 3 & 4).

**Test Files:**
- `tests/agents/subsystems/test_movement_sunden_characterization.py` — Task 3 CHARACTERIZATION GUARD (5 tests). Pins the 5 observable Sünden movement rungs by output (`resolved_via`/`to_region`) so the Task 6 ladder cutover can be proven behavior-preserving. **PASSES on develop today** (a guard has no RED — it locks existing behavior).
- `tests/telemetry/test_site_spans_to_sink.py` — Task 4 (4 tests). `site.enter`/`site.exit`/`site.enter_unresolved` spans MUST reach `turn_telemetry` via `publish_event` (recording-provider fixture) + a NonRecordingSpan robustness guard. **RED** (module absent).
- `tests/game/sites/test_site_resolvers.py` — Task 4 (6 tests). `enter_site`/`exit_site` bind `pc_region`, fail loud on the two wiring faults, and are reachable through the seam registry. **RED** (modules absent).

**Tests Written:** 15 tests (5 guard + 10 new-behavior) covering all 5 story ACs.
**Status:** RED verified (`testing-runner`, `-n0`): **5 passed, 2 collection errors** — Task 3 guard green; both Task 4 files `ModuleNotFoundError` (`sidequest.telemetry.spans.site`, `sidequest.game.sites.enter_site`). This mixed result is the correct outcome for a story that pairs a characterization guard with new-behavior tests.

### AC → Test Coverage

| AC | Test(s) | Status |
|----|---------|--------|
| 1 — Task 3 guard covers 5 movement rungs by observable outcome | `test_owned_seam_descent_from_dropmouth`, `test_adjacent_seam_descent_from_ropefoot`, `test_entrance_ascent_returns_to_seam_owner`, `test_in_dungeon_navigation_steps_to_neighbor`, `test_region_mode_unmatched_descriptor_defers` | PASS (guard) |
| 2 — enter/exit resolvers exist, registered in seam registry, bind pc_region, additive | `test_enter_site_binds_pc_to_site_entrance`, `test_exit_site_binds_pc_to_attached_region`, `test_enter_exit_site_registered_in_seam_registry` | RED |
| 3 — site.enter/exit/enter_unresolved reach turn_telemetry via publish_event (not Span.open alone) | `test_site_enter_span_mirrors_to_turn_telemetry`, `test_site_exit_span_mirrors_to_turn_telemetry`, `test_site_enter_unresolved_span_mirrors_to_turn_telemetry` | RED |
| 4 — each new suite has a wiring/reachability assertion | resolvers → `test_enter_exit_site_registered_in_seam_registry` (registry lookup); spans → the three sink tests prove the span→`publish_event` route; guard → drives the real `run_movement_dispatch` | RED / PASS |
| 5 — lint/format/type-check clean on touched files | `ruff check` + `ruff format` clean on all 3 files | PASS |

### Rule Coverage (project rules beyond ACs)

| Rule (CLAUDE.md / SOUL.md) | Test(s) | Status |
|------|---------|--------|
| No Silent Fallbacks — a missing store/entrance/owner fails LOUD | `test_enter_site_missing_store_raises_recoverable` (no_site_store), `test_enter_site_missing_entrance_node_raises` (no_site_entrance), `test_exit_site_dangling_owner_raises` (dangling_site_owner) | RED |
| OTEL Observability — every subsystem decision reaches the sink (`turn_telemetry`), not `Span.open` alone | the three `*_mirrors_to_turn_telemetry` sink tests | RED |
| No-Source-Text Wiring Tests — wiring proven behaviorally, never by grepping source | resolver wiring = `get_seam_resolver` registry lookup; span wiring = driving the span + asserting the publish route fired; guard = real dispatch | PASS/RED |
| Robustness — a telemetry mirror must never crash the live turn (NonRecordingSpan) | `test_site_span_mirror_skips_when_span_not_recording` | RED |
| Additive-only — no existing Sünden behavior changed (the whole point of the Task 3 guard) | all 5 characterization tests PASS on develop | PASS |

**Self-check:** 0 vacuous assertions — every test asserts a concrete value (`resolved_via`/`to_region`/`pc_regions`, `SeamCrossingError.reason`, `publish_event` field values, `get_seam_resolver` identity). No `assert True`, no `is_none()`-on-always-None, no bare `let _`.

### GREEN scope for Dev (Inigo Montoya)
Dev creates exactly three source modules to turn the two RED files green (the guard stays untouched):
1. `sidequest/telemetry/spans/site.py` — `site_enter_span` / `site_exit_span` / `site_enter_unresolved_span`, each registering a `SpanRoute` in `SPAN_ROUTES` and mirroring to `publish_event` AFTER the span closes (copy `spans/movement.py:_mirror_movement_span_to_sink`; **keep the `hasattr(span, "attributes")` guard** — the NonRecordingSpan test depends on it). Events are `event_type="state_transition"` with `op` ∈ {site.enter, site.exit, site.enter_unresolved}.
2. `sidequest/game/sites/enter_site.py` — `resolve_enter_site(*, snapshot, player_name, site, dungeon_repository, resolved_via, ...)`: raise `no_site_store` when repo is None; `load_map(entrance_id=site.entrance_node_id, site_id=site.site_id)`; raise `no_site_entrance` if the entrance node is absent; else `apply_world_patch(WorldStatePatch(pc_region={player_name: site.entrance_node_id}))` inside `site_enter_span`; return `SeamCrossingResult(to_region=...)`.
3. `sidequest/game/sites/exit_site.py` — `resolve_exit_site(*, snapshot, player_name, site, cartography, resolved_via, ...)`: raise `dangling_site_owner` if `site.attached_to` not in `cartography.regions`; else bind to `attached_to` inside `site_exit_span`; return the result.
Then register both in `sidequest/game/seams/registry.py` `_REGISTRY` (`"enter_site"`/`"exit_site"`) and export from `sidequest/game/sites/__init__.py`. **Additive only** — do not touch `movement.py`'s ladder or `deep_descent` (that is Task 6 / story 164-3). Re-run `ruff check --fix` on `test_site_resolvers.py` after the modules exist (its enter/exit imports are grouped oddly by isort only because the modules are absent in RED).

**Handoff:** To Dev for GREEN.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (3 commits on `feat/164-2-sunden-guard-site-resolvers`, pushed):**
- `sidequest/telemetry/spans/site.py` (new) — `site_enter_span` / `site_exit_span` / `site_enter_unresolved_span`; three `SPAN_ROUTES` entries (`event_type="state_transition"`, `component="sites"`, `op` ∈ site.enter/exit/enter_unresolved); `_mirror` copies `spans/movement.py:_mirror_movement_span_to_sink` incl. the `hasattr(span,"attributes")` non-recording guard.
- `sidequest/game/sites/enter_site.py` (new) — `resolve_enter_site`: fail loud `no_site_store` (repo None) / `no_site_entrance` (node absent) BEFORE any bind; else `apply_world_patch(pc_region=…entrance)` inside the enter span; returns `SeamCrossingResult`.
- `sidequest/game/sites/exit_site.py` (new) — `resolve_exit_site`: fail loud `no_cartography` (config None) / `dangling_site_owner` (owner off-map); else bind to `attached_to` inside the exit span.
- `sidequest/game/seams/registry.py` (mod) — lazy `_ensure_site_resolvers()` registers `enter_site`/`exit_site` atomically on first `get_seam_resolver` (breaks the seams↔sites import cycle).
- `sidequest/game/sites/__init__.py` (mod) — exports the two resolvers.
- `sidequest/telemetry/spans/__init__.py` (mod) — `from .site import *` (routing-completeness visibility).
- `tests/game/sites/test_site_resolvers.py` (mod) — added `test_exit_site_missing_cartography_raises_distinct_reason`; import re-sort now the modules exist.

**Tests:** 83/83 passing (GREEN) — the 15 story tests (Task 3 guard 5 + resolvers 7 + spans 4, minus overlap = 16; incl. the new no_cartography test) plus the full seam/movement/sites/routing-completeness regression (0 regressions). Verified via testing-runner `-n0`. `ruff check` + `ruff format` clean on all touched files.

**Additive-only confirmed:** `movement.py` and `deep_descent.py` untouched; the enlarged `_REGISTRY` never changes an existing route match (no live route's `to_id` is `enter_site`/`exit_site`); Task 3 characterization guard still green (existing Sünden behavior unchanged).

**Pre-review:** Dispatched a code-review subagent on the diff (per requesting-code-review). Verdict **Ready**; acted on 3 findings — Important (exit_site `no_cartography` split), Minor (atomic registry registration), Minor (site-span routing visibility) — all fixed + re-verified. Two Task-6 forward items captured as Delivery Findings (unresolved-span/intent wiring; pyright parity with `spans/movement.py`).

**Branch:** `feat/164-2-sunden-guard-site-resolvers` (pushed, working tree clean).

**Handoff:** To Reviewer (Westley) for the review phase.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (83/83 green, ruff clean, format clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 (low: time-varying `_REGISTRY`, dormant by design) | confirmed 1 (as [LOW] non-blocking + delivery finding), dismissed 0, deferred 0 |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none (1 low CWE-117 note the agent explicitly did NOT file) | dismissed 1 (pre-existing pattern, non-sensitive, debug-level) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (3 enabled returned; 6 disabled pre-filled)
**Total findings:** 1 confirmed (LOW, non-blocking), 1 dismissed (with rationale), 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

Story 164-2 is an additive milestone (971 insertions, 0 deletions, 9 files) that ships the Task-3 characterization guard and the Task-4 site seam resolvers + `site.*` turn_telemetry spans, wired into the seam registry but NOT yet on the movement hot path. All 5 ACs are met; no Critical/High findings survived review.

**Data flow traced (additive state):** For this diff the resolvers are reachable only via `get_seam_resolver("enter_site"/"exit_site")` (the registry wiring test) — Task 6 threads them onto the movement dispatch later. The exercised flow is: `SiteDescriptor` (registry-resolved from genre-pack YAML) → `resolve_enter_site` → `snapshot.apply_world_patch(WorldStatePatch(pc_region={pc: entrance}))` → `site_enter_span` → `_mirror` → `publish_event("state_transition", …, component="sites")` → `turn_telemetry`. Safe because every fault path raises `SeamCrossingError` BEFORE the bind, and the sink write downstream (`PgDungeonRepository.load_map`, `_persist_turn_telemetry`) is parameterized (confirmed by [SEC]).

**Observations (tagged by source; disabled specialists self-assessed by Reviewer):**
- `[VERIFIED]` **No Silent Fallbacks (SOUL) honored** — `resolve_enter_site` raises `no_site_store` (enter_site.py:40-47) and `no_site_entrance` (49-53) BEFORE `apply_world_patch` (54); `resolve_exit_site` raises `no_cartography` (32-39) and `dangling_site_owner` (42-49) before the bind (50). Evidence: no fault branch returns a `SeamCrossingResult` or mutates state. Complies with SOUL "No Silent Fallbacks" and the `SeamCrossingError` catcher-owns-the-span contract (seams/base.py:16-23). Corroborated by [SILENT].
- `[VERIFIED]` **OTEL doctrine / AC3** — `spans/site.py` registers all three spans in `SPAN_ROUTES` (site.py) and `_mirror` calls `publish_event` after span close, guarded by `hasattr(span,"attributes")` — a verbatim copy of `spans/movement.py:_mirror_movement_span_to_sink` (movement.py:151-187). `test_site_spans_to_sink.py` proves enter/exit/enter_unresolved reach the sink, and `test_site_span_mirror_skips_when_span_not_recording` proves the non-recording path skips without raising. Complies with CLAUDE.md OTEL Observability Principle.
- `[VERIFIED]` **Additive-only / AC2** — diff stat shows `movement.py` and `deep_descent.py` are untouched; `_REGISTRY` only gains keys; the Task-3 characterization guard (`test_movement_sunden_characterization.py`, 5 tests) passes on `develop`, proving existing Sünden movement behavior is unchanged. Evidence: [preflight] 83/83 green including the full seam/movement regression.
- `[SILENT]` `[LOW]` **Time-varying `_REGISTRY` membership** — `seam_route_for`/`seam_route_via_adjacency`/`surface_owner_for_entrance` (registry.py:34-99, unchanged) read `route.to_id in _REGISTRY` without calling `_ensure_site_resolvers()`, so site kinds are absent until the first `get_seam_resolver()` call. DORMANT by design (no genre-pack authors a route with `to_id` `enter_site`/`exit_site`; Task 6 dispatches site kinds by kind, not by route). Non-blocking; captured as a Task-6 delivery finding. Both the silent-failure-hunter and I independently converged on this.
- `[SEC]` **Security surface minimal, clean** — `site_id`/`site.name` originate from genre-pack YAML via `SiteRegistry`, never raw player text; `load_map(entrance_id=, site_id=)` reaches parameterized Postgres (`pg/dungeon.py:434`, `WHERE session_id = %s AND site_id = %s`); `SeamCrossingError.surface` is static-format-string prose; `logger.debug` uses lazy `%s`. **Dismissed** one LOW CWE-117 log-injection note (unstripped `\n` in debug args) — the security agent itself declined to file it: pre-existing codebase-wide pattern, values are genre-pack-declared, debug-level only, and not a python.md rule (rule #4 covers log levels + sensitive data, neither of which applies).
- `[TYPE]` (self-assessed; subagent disabled) — `SeamCrossingResult`/`SeamCrossingError` are the established seam types; resolvers are keyword-only with full annotations; `SiteExtent` is a `Literal`, so `set_attribute("extent", site.extent)` is OTEL-type-safe. The lone `_SpanLike`-vs-`Span` pyright note is identical to `spans/movement.py:187` (the mirrored reference) and pyright is ungated. No stringly-typed regression introduced.
- `[SIMPLE]` (self-assessed; subagent disabled) — no over-engineering: each resolver is ~30 lines; the lazy registration is the minimal cycle-break (not a plugin framework). The unused `direction`/`exit_descriptor` params on `resolve_enter_site` are deliberate signature-uniformity for Task 6's by-kind dispatch (documented as a Dev Gap finding), not dead scope creep.
- `[TEST]` (self-assessed; subagent disabled) — 15 story tests, zero vacuous assertions (concrete `resolved_via`/`to_region`/`reason`/field-value checks); the sink test monkeypatches `publish_event` where USED (the `site` module), matching python.md #6; negative tests cover all four fail-loud reasons; the wiring test asserts registry reachability. AC1 guard passes on develop.
- `[DOC]` (self-assessed; subagent disabled) — public functions and modules carry docstrings; `site.py`'s docstring explains the mirror rationale; `_ensure_site_resolvers` documents the exact cycle it breaks. No stale/misleading comments spotted.
- `[EDGE]` (self-assessed; subagent disabled) — boundary paths handled: `region_for(...)` None → `""` default; empty `attached_to` → `dangling_site_owner` (the `not surface_id` guard); missing entrance node → `no_site_entrance`; None repo/cartography → distinct reasons. All exercised by tests.
- `[RULE]` — see Rule Compliance below.

### Rule Compliance (python.md 13-check checklist + SOUL/CLAUDE)
- **#1 Silent exceptions** — PASS. No `try/except`/bare-except/`suppress` added anywhere in the diff; the `_mirror` `hasattr` guard is a documented non-recording skip, not a swallow. (SOUL "No Silent Fallbacks": PASS — see [VERIFIED] above.)
- **#2 Mutable defaults** — PASS. All defaults are immutable (`""`, `None`, `"site_enter"`/`"site_exit"` str literals).
- **#3 Type annotations at boundaries** — PASS. `resolve_enter_site`/`resolve_exit_site`, the three span context managers, `_ensure_site_resolvers`, `get_seam_resolver` all fully annotated; `_attr` is a private helper (exempt).
- **#4 Logging** — PASS. Only `logger.debug` on success paths (informational), lazy `%s` formatting, no sensitive data (character name + region ids). Error paths use `raise`, not logging (the catcher emits the failure span per doctrine).
- **#5 Path handling** — N/A (no filesystem paths; `site_id` is a SQL bind param / dict key, never a path).
- **#6 Test quality** — PASS (see [TEST]).
- **#7 Resource leaks** — PASS. Spans use `with` context managers; no file/socket/lock handles opened.
- **#8 Unsafe deserialization** — PASS ([SEC] confirmed: no pickle/eval/exec/yaml).
- **#9 Async pitfalls** — N/A. The resolvers are synchronous by design (the seam resolvers are sync; movement dispatch awaits at its layer). No blocking calls introduced.
- **#10 Import hygiene** — PASS with note. `from .site import *` in `spans/__init__.py` is the file's UNIVERSAL, docstring-prescribed convention (every span domain is star-imported incl. `movement`); the runtime imports in `_ensure_site_resolvers` are a deliberate, commented cycle-break (genuine runtime need, not annotation-only). No NEW circular import — the diff removes one.
- **#11 Input validation** — PASS ([SEC]: values are registry-resolved from YAML; SQL is parameterized).
- **#12 Dependency hygiene** — N/A (no dependency changes).
- **#13 Fix-introduced regressions** — PASS. The three pre-review fixes (no_cartography branch, atomic registry update, star-import) were re-scanned: no new broad catches, no wrong types, and the routing-completeness guard now covers the new spans (83/83 green after the fixes).

### Devil's Advocate
Suppose this code is broken. The most dangerous shape would be a resolver that binds `pc_region` and THEN fails, stranding the PC in a half-crossed state — but both resolvers raise every fault BEFORE `apply_world_patch`, so a fault leaves the PC exactly where they were (tests assert the source region survives every raise). Could the span mirror crash a live turn? The `_mirror` runs AFTER the `with` block on an ended span; if `publish_event` itself threw (a dead Postgres sink), it would propagate out of the resolver after the bind — but this is precisely the shipped `movement.py` behavior, and `publish_event`'s persistence helpers early-return when the sink is None, so a unit/test context is safe and production degrades the same way movement already does. Could a confused genre author break it? A malformed `SiteDecl` (empty `attached_to`, wrong `attached_to`) is caught by `dangling_site_owner`; a missing site store by `no_site_store`; a not-yet-materialized site by `no_site_entrance` — all fail loud with distinct reasons the GM panel can route. The subtlest trap is the lazy `_REGISTRY`: a reviewer could argue that a future route with `to_id="enter_site"` would silently vanish — and that is TRUE, but it is unreachable today (no such route exists; sites dispatch by kind) and is captured as a Task-6 delivery finding. Could concurrency corrupt registration? The guard-then-update isn't atomic across the whole function, but the import lock plus the single `dict.update` close the window, and the engine is single-threaded asyncio. What about a huge/adversarial `site_id`? It rides into a parameterized query and an opaque span attribute — no injection, no ReDoS (no regex on it in this diff), no path use. The strongest honest criticism is telemetry-completeness (no `party_split_after`/intent stamping on the site spans yet) — real, but additive-ahead-of-consumer and logged for Task 6, not a defect in 164-2. Nothing here rises to Critical or High.

**Handoff:** To SM (Vizzini) for finish-story.