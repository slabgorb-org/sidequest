---
story_id: "165-5"
jira_key: ""
epic: "165"
workflow: "spdd"
---
# Story 165-5: Fate zone projection + binding zone state/legality + conflict-seating wiring (plan tasks 11–13)

## Story Details
- **ID:** 165-5
- **Jira Key:** (not configured)
- **Workflow:** spdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** spdd
**Phase:** finish
**Phase Started:** 2026-07-10T13:56:48Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-10T11:44:34Z | 2026-07-10T11:46:11Z | 1m 37s |
| red | 2026-07-10T11:46:11Z | 2026-07-10T12:01:16Z | 15m 5s |
| green | 2026-07-10T12:01:16Z | 2026-07-10T12:27:33Z | 26m 17s |
| review | 2026-07-10T12:27:33Z | 2026-07-10T12:41:22Z | 13m 49s |
| red | 2026-07-10T12:41:22Z | 2026-07-10T12:47:03Z | 5m 41s |
| green | 2026-07-10T12:47:03Z | 2026-07-10T13:38:54Z | 51m 51s |
| review | 2026-07-10T13:38:54Z | 2026-07-10T13:56:48Z | 17m 54s |
| finish | 2026-07-10T13:56:48Z | - | - |

## Sm Assessment

**Story:** 165-5 — Fate zone projection + binding zone state/legality + conflict-seating wiring (Track C plan tasks 11–13). 5 pts, p1.

**Workflow routing:** Sprint YAML tags this `superpowers`, which is NOT a registered pf workflow. Per settled Keith decision (`sm-decisions.md`, 2026-07-08), the 163/164/165 mapping-track stories run as **spdd** (setup→red→green→review→finish). Set up as spdd. Do not re-ask.

**Repos:** server. Branch `feat/165-5-fate-zones-seating` created off `develop` in the server subrepo (server branches off develop, not main).

**Scope (from context-story-165-5 + epic plan tasks 11–13):**
- IN: Pure zone projection (grid → contiguous cell clusters) in `sidequest.game.tactical.zones`; the Fate binding consuming that projection to wire zone state + zone-move legality + OTEL; conflict-seating wiring (gated on `isinstance(ruleset, FateRulesetModule)` so WN/dial packs are untouched).
- OUT: WN enforcement (165-3), protocol/UI math (165-4). Dogfight (ADR-153) untouched.

**ACs:** Deferred to TEA to define during RED from plan tasks 11–13, per the explicit instruction in `context-story-165-5.md`.

**Plan doc:** `docs/superpowers/plans/2026-07-08-mapping-track-c-tactical-mechanics.md` §tasks 11–13.

**Load-bearing carryover for TEA (from 165-1, mostly pure-library discipline — full detail in `context-story-165-5.md` §Carryover and the `*-gotchas.md` tagged 165-1):**
1. **The plan doc has bugs in its embedded code — hand-verify before transcribing** any mask/coordinate/impl into a RED test. A quick `python3 -c` reimplementing `parse_mask`/`is_floor` catches mask bugs in seconds.
2. **Reuses C1 primitives** (`parse_mask`/`is_floor`/`neighbors`) from `sidequest/game/tactical/adjudication.py` — same pure-library discipline (no IO, no clock, no random). Coordinate convention: `cell = (x, y)`, x=col, y=row, origin top-left.
3. Per the plan, `ZoneMoveAdjudication(free, requires_overcome, from_zone, to_zone)` is already defined in `zones.py` (Task 11) — import it in Task 12, do not redefine.
4. New spans must call `publish_event` + carry a `SPAN_ROUTES`/`FLAT_ONLY_SPANS` entry.

**Branch Strategy:** gitflow (feat/165-5-fate-zones-seating)

## Skills Invoked

<skills-invoked>
<skill name="test-driven-development" phase="red" at="2026-07-10T11:47:17Z"/>
<skill name="test-driven-development" phase="green" at="2026-07-10T12:02:26Z"/>
<skill name="verification-before-completion" phase="green" at="2026-07-10T12:02:26Z"/>
<skill name="requesting-code-review" phase="green" at="2026-07-10T12:02:26Z"/>
<skill name="test-driven-development" phase="red" at="2026-07-10T12:42:32Z"/>
<skill name="test-driven-development" phase="green" at="2026-07-10T12:47:55Z"/>
<skill name="verification-before-completion" phase="green" at="2026-07-10T12:47:55Z"/>
<skill name="requesting-code-review" phase="green" at="2026-07-10T12:47:55Z"/>
<skill name="test-driven-development" phase="green" at="2026-07-10T13:34:26Z"/>
<skill name="verification-before-completion" phase="green" at="2026-07-10T13:34:26Z"/>
<skill name="requesting-code-review" phase="green" at="2026-07-10T13:34:26Z"/>
</skills-invoked>

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)

- **Improvement** (non-blocking): The plan doc's Task 12/13 file paths and run commands reference `tests/agents/ruleset/test_fate_zone_binding.py`, but that directory does not exist — the WN sibling binding test lives at `tests/game/ruleset/`. Affects `docs/superpowers/plans/2026-07-08-mapping-track-c-tactical-mechanics.md` (Dev must substitute `tests/game/ruleset/test_fate_zone_binding.py` in the Task 12/13 pytest sweeps). *Found by TEA during test design.*
- **Question** (non-blocking): The plan's Task 12 interface text says `project_conflict_zones(..., anchors=None, ...)` seats each actor's zone "from its cell (or an anchor fallback)", but the plan's embedded implementation accepts `anchors` and never reads it. Tests pin cell-derived seating + skip-unseated only; if Dev implements the anchor fallback, it needs its own test. Affects `sidequest/game/ruleset/fate.py` (decide: implement the fallback or drop the dead parameter — No Stubbing). *Found by TEA during test design.*
- **Improvement** (non-blocking): The plan's embedded `project_conflict_zones` emits `tactical_zone_projected_span(zone_count=..., room_id="")` — an empty `room_id` from the binding, while the Task 13 call site knows the real room. Tests do not pin `room_id`; Dev may plumb it through for a more useful GM-panel event. Affects `sidequest/game/ruleset/fate.py` / `sidequest/server/dispatch/encounter_lifecycle.py`. *Found by TEA during test design.*

### Dev (implementation)

- **Gap** (non-blocking): `adjudicate_zone_move` + the `tactical.zone.move` span have no production consumer yet — the plan's Grounding Limit #3 explicitly defers the Fate move verb / player-facing zone-move control (a costed move surfaces via the existing Overcome) to a named follow-up, so this is sanctioned wiring debt, not an oversight. Affects `sidequest/game/ruleset/fate.py` (the follow-up story that adds zone-derived Overcome opposition must consume `adjudicate_zone_move`; until then the span never fires in production). Flagged Important by the pre-handoff review subagent. *Found by Dev during implementation.*
- **Gap** (non-blocking): `project_zones` trusts the caller for floor connectivity — a floor component that is entirely chokepoints AND disconnected from every cored component would be silently orphaned (absent from `cell_to_zone`), and an actor seated there would silently get no zone. Unreachable in production today (`interiors/cellular.py:_keep_largest_floor_region` guarantees a single floor component; maze generators are connected by construction), but the pure library could self-enforce with a loud totality assert. Affects `sidequest/game/tactical/zones.py` (consider `assert set(zone_of) == set(floor)` in a polish pass, with a test). *Found by Dev during implementation (via pre-handoff review).*
- **Improvement** (non-blocking): Zone-id ordering is lexicographic (`z10` sorts before `z2`) in `encounter.zones` and the BFS tie-break — deterministic but not numeric-ascending; only matters for rooms with 10+ zones, which room-scale grids don't produce. Affects `sidequest/game/tactical/zones.py` / `sidequest/game/ruleset/fate.py` (docstring precision or numeric sort in a polish pass). *Found by Dev during implementation (via pre-handoff review).*
- **Improvement** (non-blocking): Now that [G] makes `project_zones` TOTAL, `project_conflict_zones`'s `zid is None` skip path can only be reached by an actor seated on an off-floor/wall coordinate — arguably the same "impossible/corrupt state" class this same rework hardened into fail-loud in `_seat_tactical_cells` ([K]), yet here it stays a silent per-actor exclusion (observable only via the span's `placed_count`). Deliberately unchanged this round — TEA's `test_project_conflict_zones_skips_actor_on_unzoned_cell` pins the skip as a regression contract — but the two treatments of "seated position that resolves to nothing" now diverge. Affects `sidequest/game/ruleset/fate.py:552-558` (a follow-up should decide: fail loud like the seating wire, or keep the observable skip and document the divergence intentionally). *Found by Dev during rework GREEN (via pre-handoff review, finding #1).*
- **Improvement** (non-blocking): The full serial suite is clean (1 known pre-existing failure), but the parallel (`-n auto`) run surfaces `tests/agents/test_102_5_wn_tool_narrator_wiring.py::test_narrator_turn_drives_wn_attack_through_production_dispatch` and `tests/server/dispatch/test_pregen_bestiary_90_1.py::test_seed_manual_populates_encounters_for_wwn_world[evropi]` as failures that PASS in isolation — xdist test-isolation / shared-state pollution, unrelated to 165-5. Affects those two test files (test-isolation hardening in a separate story). *Found by Dev during rework GREEN full-suite verification.*

### Reviewer (code review)

- **Gap** (non-blocking): The pre-existing `tests/telemetry/test_tactical_telemetry_sink.py` and `tests/dungeon/conftest.py` fail `uv run ruff check` on develop today (same RED→GREEN isort-reclassification disease as this branch's finding, from earlier stories) — the repo's aggregate lint gate is already red independent of 165-5. Affects `tests/telemetry/test_tactical_telemetry_sink.py`, `tests/dungeon/conftest.py` (one-line import-order fixes in a housekeeping pass). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `pyproject.toml` pins `ruff>=0.3` — an unpinned floor (lang-review #12); ruff minor bumps change isort classification behavior and silently shift the lint gate under committed code. Affects `sidequest-server/pyproject.toml` (consider a compatible-release pin). *Found by Reviewer during code review.*
- **Gap** (non-blocking): reviewer-preflight subagent ran `ruff --fix` and left the working tree dirty mid-review (restored by Reviewer via `git checkout --`). Affects `.pennyfarthing/agents/reviewer-preflight.md` (instruct check-only, never `--fix`). *Found by Reviewer during code review.*

#### Rework round 1 review (round 2)
- **Improvement** (non-blocking): `test_seating_fails_loud_on_missing_pack_ruleset` is the only caller of `_fate_gridded_session()` in its file *without* the `@_needs_fate_pack` skip guard, yet it loads the real `pulp_noir` pack via that helper and then discards it (it passes `pack=None` and never uses the loaded pack). In a checkout without `sidequest-content` present, it ERRORs with `PackNotFound` instead of skipping like its siblings — reproduced by the test-analyzer in an isolated worktree. Passes fine today (content is present). Affects `sidequest-server/tests/server/dispatch/test_fate_zone_seating_wiring.py:226` (either drop the unused `_fate_gridded_session()` load — build `snap`/`store` directly — or add `@_needs_fate_pack` for sibling consistency). *Found by Reviewer during code review (test-analyzer, medium confidence).*
- **Improvement** (non-blocking): The `tactical.zone.projected` span's `placed_count` is only exercised at the OTEL-span layer for the `cell is None` skip path (the Bystander in `test_zone_projected_span_counts_only_placed_actors`). The second skip path this rework documented (`zid is None` — off-floor/wall cell) is pinned only at the dict-return layer (`test_project_conflict_zones_skips_actor_on_unzoned_cell`). Since span `placed_count == len(placed)` and `placed` is the same dict the dict-level test pins, a miscount is still caught — but no span-level test isolates the off-floor skip. Affects `sidequest-server/tests/game/ruleset/test_fate_zone_binding.py:286` (add a span-level `placed_count` variant using an off-floor-cell actor). *Found by Reviewer during code review (test-analyzer, low confidence).*
- **Improvement** (non-blocking): `ZoneProjection` (`fate.py:27`) was hoisted out of the `TYPE_CHECKING` block into a runtime import alongside `ZoneMoveAdjudication`/`project_zones`, but unlike those two it is used only in an annotation (`projection: ZoneProjection`) under `from __future__ import annotations` (PEP 563), so it never evaluates at runtime and could have stayed type-only — a minor rule-#10 nit with zero functional or dependency-graph cost (the module is imported at runtime regardless for the other two names). Affects `sidequest-server/sidequest/game/ruleset/fate.py:25-29` (one-line: move `ZoneProjection` back into the `TYPE_CHECKING` block in a housekeeping pass). *Found by Reviewer during code review (rule-checker, high confidence). See the ACCEPTED-with-note deviation audit below.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Binding test placed at `tests/game/ruleset/`, not the plan's `tests/agents/ruleset/`** → ✓ ACCEPTED by Reviewer: repo layout is authoritative over plan-doc paths; the WN sibling lives there.
  - Spec source: `docs/superpowers/plans/2026-07-08-mapping-track-c-tactical-mechanics.md`, Task 12 Files list
  - Spec text: "Create `sidequest-server/tests/agents/ruleset/test_fate_zone_binding.py`"
  - Implementation: Created `tests/game/ruleset/test_fate_zone_binding.py` instead
  - Rationale: `tests/agents/ruleset/` does not exist in the repo; the Task-5 WN sibling (`test_wn_tactical_binding.py`) that this test mirrors lives at `tests/game/ruleset/`. Repo layout wins over plan-doc text (established 165-1 precedent: the plan doc is not authoritative on mechanics or paths).
  - Severity: minor
  - Forward impact: Dev's Task 12/13 pytest run commands must use the corrected path (logged as a Delivery Finding).

### Dev (implementation)
- **Dropped the `anchors=None` parameter from `project_conflict_zones`** → ✓ ACCEPTED by Reviewer: the plan's own snippet never read it — No Stubbing correctly applied; TEA's finding posed exactly this choice.
  - Spec source: plan doc Task 12, Interfaces ("Produces")
  - Spec text: "`project_conflict_zones(*, encounter, mask, anchors=None, _tracer=None) -> dict[str, str]` … seats each actor's `per_actor_state['zone']` from its `per_actor_state['cell']` (or an anchor fallback)"
  - Implementation: Signature is `project_conflict_zones(*, encounter, mask, room_id="", _tracer=None)` — no `anchors`; zones derive from seated cells only, unseated actors are skipped
  - Rationale: The plan's own embedded implementation accepts `anchors` and never reads it — a dead parameter (No Stubbing). TEA's tests pin cell-derived seating + skip-unseated and pass no `anchors`; TEA's Delivery Finding explicitly posed this choice ("implement the fallback or drop the dead parameter").
  - Severity: minor
  - Forward impact: If a future story wants anchor-fallback zone seating, it adds the parameter with its own test; nothing consumes it today.
- **Added `room_id` parameter and `placed_count` span attribute beyond the plan's span shape** → ✓ ACCEPTED by Reviewer: strengthens the lie-detector; additive only. But `placed_count` shipped UNASSERTED — a test must pin it (carried as a rework finding).
  - Spec source: plan doc Task 12, embedded `project_conflict_zones` snippet + span step
  - Spec text: "`tactical_zone_projected_span(zone_count=len(proj.zones), room_id=\"\", ...)`" (empty room_id, no placed count)
  - Implementation: `project_conflict_zones` takes `room_id: str = ""`; the seating wire passes the real room id; the span also carries `placed_count=len(placed)` and its route extracts it
  - Rationale: TEA's Improvement finding (empty room_id makes a weak GM-panel event) + pre-handoff review finding (without an outcome count the lie-detector can't distinguish "2 zones, both actors placed" from "2 zones, none placed" — the exact OTEL-principle failure mode)
  - Severity: minor
  - Forward impact: None — additive span fields; tests assert the pinned fields and pass.
- **Task 13 wire lives in `_seat_tactical_cells`, not inline in `instantiate_encounter_from_trigger`** → ✓ ACCEPTED by Reviewer: the helper already owns the mask load; the plan's "extend that block" instruction sanctions it. The silent-return guards inside it are a separate rework finding.
  - Spec source: plan doc Task 13, step 3
  - Spec text: "In `instantiate_encounter_from_trigger` (the same site as Task 8), after `seat_actor_cells`, add: `if isinstance(ruleset, FateRulesetModule) and mask is not None: ...`"
  - Implementation: Extended the `_seat_tactical_cells` helper (new required `pack` kwarg; the trigger's call site passes `pack=pack`) — the projection runs right after `seat_actor_cells` inside the helper
  - Rationale: `seat_actor_cells` and the Task-8 mask load both live inside `_seat_tactical_cells`; extending it is the plan's own "extend that block rather than reloading" instruction (also TEA note 4). The isinstance gate + mask-present guard are exactly as specified.
  - Severity: minor
  - Forward impact: None — behavior identical to the plan's placement; the wiring test asserts outcomes, not call shape.

#### Rework round 1 (green)
- **[N] import hoist also consolidated `ZoneProjection` from the TYPE_CHECKING block into the runtime top-level import** → ⚠️ ACCEPTED-WITH-NOTE by Reviewer: a real but zero-cost rule-#10 nit (rule-checker confirmed it — `ZoneProjection` is annotation-only under PEP 563, so it could have stayed in `TYPE_CHECKING`). Not dismissed; kept LOW and non-blocking because the module is imported at runtime regardless (for `project_zones`/`ZoneMoveAdjudication`), so the extra name adds no dependency and no cycle. Captured as a non-blocking Delivery Finding for a one-line housekeeping move — not worth a rework round-trip. The rest of the [N] hoist (the four genuinely-runtime local imports) is correct.
  - Spec source: Reviewer severity table [LOW] [RULE] N + TEA rework handoff ("hoist `fate.py` zone/span imports to module top")
  - Spec text: "zone/span imports local-in-method in `fate.py` … hoist to module top"
  - Implementation: Moved the two local-in-method imports (`project_zones`, `tactical_zone_projected_span`, `ZoneMoveAdjudication`, `tactical_zone_move_span`) to module top AND lifted `ZoneProjection` — which was annotation-only under `if TYPE_CHECKING:` — into the same runtime `from sidequest.game.tactical.zones import (...)` block, so all three zone symbols live in one import site.
  - Rationale: One consolidated import site reads cleaner than splitting `ZoneMoveAdjudication`/`project_zones` (runtime) from `ZoneProjection` (TYPE_CHECKING) across two blocks; no cycle exists (`zones.py` imports only `tactical/adjudication.py`, verified by the pre-handoff reviewer and a clean full-suite import). Strictly, [N] named only the local-in-method imports; `ZoneProjection` was already at module scope.
  - Severity: minor
  - Forward impact: None — `ZoneProjection` is now a hard runtime import in `fate.py`; harmless since there is no `zones.py`→`fate.py` dependency.

## TEA Assessment

**Tests Required:** Yes
**Reason:** n/a — full RED suite written for plan tasks 11–13.

### Acceptance Criteria (defined by TEA from plan tasks 11–13, per context-story-165-5 instruction)

- **AC-1 (Task 11):** `sidequest.game.tactical.zones` exposes pure, deterministic `project_zones(mask) -> ZoneProjection` — stable ids `z0, z1, ...` in scan order; every floor cell (chokes included) assigned to exactly one zone; walls never assigned; open room and all-choke corridor each degenerate to one zone; no-floor mask → empty projection; adjacency symmetric, no self-loops; `zones`/`adjacency` values are frozensets. `ZoneMoveAdjudication(free, requires_overcome, from_zone, to_zone)` is a frozen dataclass defined in `zones.py`.
- **AC-2 (Task 12):** `FateRulesetModule.project_conflict_zones(*, encounter, mask, ...)` populates `encounter.zones` (inert ADR-144 slot goes live) and each cell-seated actor's `per_actor_state['zone']`, returns name→zone; unseated actors are skipped (no crash, no fabricated position).
- **AC-3 (Task 12):** `FateRulesetModule.adjudicate_zone_move(*, from_zone, to_zone, projection, ...)` returns the Task-11 `ZoneMoveAdjudication` (imported, never redefined): same/adjacent zone → `free`; non-adjacent (2+) → `requires_overcome`; an unknown zone id is never free.
- **AC-4 (Task 12):** `tactical.zone.projected` and `tactical.zone.move` spans exist, carry `SPAN_ROUTES` entries (`event_type=state_transition`, `component=tactical`), are exported in `__all__`, and mirror into the turn_telemetry sink via `publish_event` (GM-panel lie detector).
- **AC-5 (Task 13):** At Fate conflict instantiation on a gridded room (production path `instantiate_encounter_from_trigger`), `encounter.zones` is populated, every actor carries a valid zone (entrance vs creature anchors land in different DUMBBELL lobes), and `tactical.zone.projected` reaches the sink.
- **AC-6 (Task 13, gates):** A WN pack seating combat on the same grid gets cell seating but NO zones/span (isinstance gate); a Fate conflict with no dungeon_store/grid seats normally with no zones and no span (clean no-op).

**Test Files:**
- `sidequest-server/tests/game/tactical/test_zones.py` — 13 tests, AC-1 (all mask assertions hand-traced against the merged C1 `parse_mask`/`is_floor`/`neighbors` per the 165-1 carryover; DUMBBELL cores are exactly (3,1)/(3,3) → top lobe z0 (8 cells) / bottom lobe z1 (5 cells))
- `sidequest-server/tests/game/ruleset/test_fate_zone_binding.py` — 8 tests, AC-2/3/4 (span-mirror tests use the recording-tracer fixture from `test_tactical_telemetry_sink.py` — the `_mirror` helper skips NonRecordingSpans, a documented plan-doc bug class)
- `sidequest-server/tests/server/dispatch/test_fate_zone_seating_wiring.py` — 4 tests, AC-5/6 (live `pulp_noir` pack via the production loader, persisted-mask fixture shape reused from `tactical_emit_fixtures.py`)

**Tests Written:** 25 tests covering 6 ACs
**Status:** RED (verified by testing-runner, RUN_ID 165-5-tea-red)

**RED verification detail:**
- `test_zones.py` + `test_fate_zone_binding.py`: collection error `ModuleNotFoundError: No module named 'sidequest.game.tactical.zones'` — fails because the feature is missing, exactly.
- Wiring headline tests: AssertionError on empty `enc.zones` / missing `tactical.zone.projected` — and the observed-ops output shows `tactical.positions.seated` DID fire, proving the fixture grid is live and only the projection is unwired.
- 2 negative guards (WN gate, no-grid no-op) PASS by design — they pin existing no-op boundaries GREEN must preserve (model: `test_encounter_position_seating.py`'s no-store guard).
- Neighbouring suites: 45/45 pass, zero regression.

### Rule Coverage

| Rule (python.md lang-review) | Test(s) | Status |
|------|---------|--------|
| #6 test quality (no vacuous asserts) | every test asserts specific values/sets; self-check done | n/a (meta) |
| #1 silent fallbacks (project rule) | `test_adjudicate_zone_move_unknown_zone_is_never_free`, `test_project_conflict_zones_skips_unseated_actor`, `test_fate_conflict_without_grid_is_a_clean_noop` | failing/guard |
| #3 type contracts | `test_adjudicate_zone_move_returns_the_task11_dataclass` (`type() is`), `test_projection_zone_sets_are_frozen`, `test_zone_move_adjudication_is_a_frozen_verdict` | failing |
| #4 observability (OTEL principle) | `test_zone_projected_span_mirrors_to_sink`, `test_zone_move_span_mirrors_to_sink`, `test_fate_zone_projection_span_fires_at_seating`, `test_zone_span_routes_registered` | failing |
| #10 import hygiene (`__all__`) | `test_zone_span_routes_registered` (export assertions) | failing |
| #11 input validation at boundaries | `test_no_floor_mask_is_empty_projection`, `test_no_wall_cell_gets_a_zone`, corridor/open-room degenerates | failing |
| Wiring test (CLAUDE.md mandate) | entire `test_fate_zone_seating_wiring.py` (production reachability + isinstance gate) | failing/guard |

**Rules checked:** 6 of 13 lang-review rules applicable to test design have coverage; the rest (resource leaks, async, deps, paths) have no surface in this story's scope.
**Self-check:** 0 vacuous tests found.

**Load-bearing notes for Dev (Naomi):**
1. `zones.py` goes at `sidequest/game/tactical/zones.py`; reuse C1 `parse_mask`/`is_floor`/`neighbors` — pure library discipline (no IO/clock/random). The plan's embedded implementation hand-verified OK this time, but the DUMBBELL partition is TOP/BOTTOM lobes (cores (3,1)/(3,3)), not left/right — don't "fix" the tests to match intuition.
2. `ZoneMoveAdjudication` is defined in `zones.py` (Task 11); `fate.py` imports it — `type() is` in the binding test will catch a redefinition.
3. Span helpers must mirror via `publish_event` + `SPAN_ROUTES` entries + `__all__` (plan Task 12 step 1); run `tests/telemetry/test_routing_completeness.py -n0` in the sweep.
4. Task 13 gate goes in `instantiate_encounter_from_trigger` right after the `_seat_tactical_cells` call (`encounter_lifecycle.py:2641`) — `is_fate` is already in scope there; gate on `isinstance(ruleset, FateRulesetModule)` + mask present, and extend Task 8's mask-load block rather than reloading.
5. Corrected test path for the plan's Task 12/13 run commands: `tests/game/ruleset/test_fate_zone_binding.py`.

**Handoff:** To Dev for implementation (GREEN).

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/game/tactical/zones.py` (new) — pure choke-seeded zone projection: `project_zones` → `ZoneProjection`; frozen `ZoneMoveAdjudication` (Task 11)
- `sidequest/game/ruleset/fate.py` — `FateRulesetModule.project_conflict_zones` (populates `encounter.zones` + `per_actor_state['zone']`, returns name→zone, emits `tactical.zone.projected` with `zone_count`/`placed_count`/`room_id`) and `adjudicate_zone_move` (Fate RAW: same/adjacent free, 2+ requires Overcome, unknown zone never free; emits `tactical.zone.move`) (Task 12)
- `sidequest/telemetry/spans/tactical.py` — `SPAN_TACTICAL_ZONE_PROJECTED` / `SPAN_TACTICAL_ZONE_MOVE`, `SPAN_ROUTES` entries, sink-mirroring context-manager helpers, `__all__` (Task 12)
- `sidequest/server/dispatch/encounter_lifecycle.py` — `_seat_tactical_cells` extended (required `pack` kwarg from the trigger's call site): after cell seating, resolve the pack's ruleset and, gated on `isinstance(ruleset, FateRulesetModule)` + mask bytes present, decode the mask and call `project_conflict_zones` with the real room id (Task 13)

**Tests:** 25/25 story tests GREEN; full sweep 75/75 (tactical + WN binding + Fate binding + wiring + telemetry sink + routing completeness, serial); neighbouring seating suites 13/13; full server suite 14,905 passed / 341 skipped / 1 failed — the 1 failure (`test_dungeon_map_frame_is_emitted_to_ui`) is pre-existing on develop, attributed by stash-test. Ruff clean; pyright introduces 0 new errors (15 pre-existing on develop in touched files, 15 on branch; new `zones.py` is 0).
**Branch:** `feat/165-5-fate-zones-seating` (pushed, 3 commits: RED tests d82b7b3b, implementation f37fc0fc, span observability 2765aaea)

**Pre-handoff review (requesting-code-review skill):** dispatched a reviewer over ca68638..f37fc0f — verdict "ready to proceed", 0 Critical. Its Important finding (no production consumer for `adjudicate_zone_move` yet) is the plan's own sanctioned Grounding-Limit-#3 deferral, logged as a Delivery Finding with the named follow-up; its actionable Minor (span couldn't distinguish placed vs unplaced actors) was fixed in 2765aaea; remaining Minors logged as Delivery Findings.

**Handoff:** To Chrisjen Avasarala (Reviewer) for review phase.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | tests 63/63 green, no smells; 1 process anomaly (ran `--fix`, dirtied tree) | confirmed 1 (lint I001, corroborated by own re-run), process anomaly logged as Delivery Finding |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — domain self-assessed ([EDGE] notes in assessment) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — domain self-assessed ([SILENT] notes in assessment) |
| 4 | reviewer-test-analyzer | Yes | findings | 4 (2 high, 2 medium) + 4 clean checks | confirmed 4 (B placed_count, C zid-None path, D mask_b64 branch, E multi-PC) |
| 5 | reviewer-comment-analyzer | Yes | findings | 5 (3 high, 2 medium) | confirmed 5 (F tie-break wording, G totality — repro re-verified by Reviewer, H same-zone free teleport — repro re-verified by Reviewer, I skip-doc, J gate-doc) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — domain self-assessed ([TYPE] notes in assessment) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings — domain self-assessed ([SEC] notes in assessment) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — domain self-assessed ([SIMPLE] notes in assessment) |
| 9 | reviewer-rule-checker | Yes | findings | 5 (1 medium, 4 low) + full 13-rule table | confirmed 4 (K silent returns, N local imports, O truthy assert, M no `__all__` noted-only); **corrected 1** — its "unknown-zone handling correct" clean-pass is contradicted by the executed H repro (rule-checker read the differing-zone test only; execution wins) |

**All received:** Yes (4 returned, 5 disabled via settings)
**Total findings:** 13 confirmed, 0 dismissed, 1 corrected (rule-checker clean-pass overturned by executed repro), 1 noted-only (`__all__`, sibling-consistent)

### Rule Compliance

Rubric: `.pennyfarthing/gates/lang-review/python.md` (13 checks) + CLAUDE.md/SOUL.md project rules. Full instance enumeration by reviewer-rule-checker; Reviewer spot-verified the load-bearing ones.

| Rule | Instances | Verdict |
|------|-----------|---------|
| #1 silent exceptions | 0 try/except in diff | compliant |
| #2 mutable defaults | 8 functions/dataclasses | compliant |
| #3 type annotations at boundaries | 7 public functions | compliant (`**attrs: Any` matches 5 pre-existing sibling signatures) |
| #4 logging | no logger use in diff | n/a |
| #5 path handling | none | n/a |
| #6 test quality | 25 tests | compliant except [LOW] truthy assert at `test_fate_zone_binding.py:140` |
| #7 resource leaks | 0 | compliant |
| #8 unsafe deserialization | 1 b64decode of store-owned data | compliant (matches `dice.py:359` precedent) |
| #9 async | none | n/a |
| #10 import hygiene | 4 local-import sites, 1 new module | [LOW] `fate.py` local imports break the file's own top-level span-import convention (no cycle exists — verified); `zones.py` no `__all__` (sibling-consistent, noted only) |
| #11 input validation | mask + zone ids | **violation via H**: unknown same-zone id yields a free verdict (see severity table) |
| #12 dependency hygiene | no dep changes in diff | compliant in-diff; `ruff>=0.3` unpinned floor pre-exists (Delivery Finding) |
| #13 fix regressions | n/a | n/a |
| No Silent Fallbacks (CLAUDE.md) | `_seat_tactical_cells` Task-13 guards | **violation (K)**: two silent `return`s with zero signal, contradicting the file's own `_raise_missing_ruleset` precedent and the sibling `seated_count=0` honest-skip span |
| Verify Wiring / non-test consumers | `project_conflict_zones`, `adjudicate_zone_move` | projected-span path production-reachable (wiring test); `adjudicate_zone_move` has zero production consumers — sanctioned Grounding-Limit-#3 deferral, disclosed in Delivery Findings; accepted as paper-trailed debt |
| Every suite needs a wiring test | `test_fate_zone_seating_wiring.py` | compliant (drives real `instantiate_encounter_from_trigger` with live pulp_noir pack) |
| No source-text wiring tests | all 25 tests | compliant (OTEL span + fixture-driven assertions only) |

### Devil's Advocate

Argue this ships broken. Start with the contract the code signs and breaks the same day: `zones.py` line 34 calls `ZoneProjection` "a total partition of the floor" and the plan says "guarantees every floor cell gets a home." I ran it: a disconnected all-choke corridor loses 4 of 13 floor cells — no zone, no error, no span. Today's generators can't author that mask, so everyone shrugs — but this is a *pure library*, the exact kind of module the next story imports for a homebrew world's hand-authored mask (Jade pastes YAML, remember — content is the surface we promise never breaks the engine), and when her hand-drawn map has a lonely bridge, an actor stands in a room the Fate binding says doesn't exist. The narrator will then do what it always does when mechanics go quiet: improvise. That is the precise Illusionism failure OTEL exists to catch, and the projected span will smile and report `zone_count=2` while an actor floats zoneless — because `placed_count`, the field added *specifically* to catch this, is asserted by **zero tests**; a regression that hardcodes it to `len(actors)` passes the whole suite. Meanwhile `adjudicate_zone_move` promises "never a free teleport" and hands `z99→z99` a free pass — unconsumed today, but the follow-up story will consume it with the docstring as its spec. And the branch fails the repo's own `ruff check` gate as committed, so the finish phase bounces regardless. Two guards in the seating wire return silently where the file's own doctrine helper raises loudly. None of this corrupts a byte in production this week; all of it is precisely the class of quiet rot this project wrote its rules against.

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [MEDIUM] [RULE] K: two silent `return` guards (ruleset_slug None / mask_b64 absent) with zero signal — No Silent Fallbacks violation contradicting in-file `_raise_missing_ruleset` precedent and the sibling honest-skip span | `sidequest/server/dispatch/encounter_lifecycle.py:1743-1747` | ruleset branch → `_raise_missing_ruleset("fate_zone_projection")`; mask-bytes branch → fail loud or emit an honest-skip span; TEA pins with test (covers D/J) |
| [MEDIUM] [DOC] H: `adjudicate_zone_move(z99→z99)` returns `free=True` for a zone unknown to the projection — contradicts the docstring's "never a free teleport"; same-zone-unknown path untested (Reviewer re-verified by execution) | `sidequest/game/ruleset/fate.py:568-596` | validate zone membership before the same-zone shortcut (unknown → `requires_overcome`); TEA adds failing `z99→z99` test. No production consumer exists, so the semantic change is free |
| [MEDIUM] [DOC] G: "total partition" contract false — disconnected all-choke floor component silently orphaned (Reviewer re-verified: 4/13 cells dropped, no error, no signal); plan's stated contract IS totality | `sidequest/game/tactical/zones.py:52-118` | seed one zone per core-less connected component (extend the degenerate branch) so totality holds unconditionally; TEA adds the disconnected-component test |
| [MEDIUM] [TEST] B: `placed_count` (the entire point of commit 2765aaea) asserted by zero tests | `tests/game/ruleset/test_fate_zone_binding.py:182-203`, `tests/server/dispatch/test_fate_zone_seating_wiring.py:179-196` | assert `placed_count == 2` in the happy path and `placed_count == 2` with `zone_count == 2` + one unseated actor variant asserting the split |
| [MEDIUM] [TEST] C+I: the `zid is None` skip path (actor HAS a cell but it's off-floor/unzoned) is untested and undocumented — indistinguishable from the tested no-cell skip | `sidequest/game/ruleset/fate.py:552-558` | TEA adds wall-cell (`[0,0]`) actor test asserting exclusion from `placed`/no `zone` key; Dev broadens the docstring to name both skip conditions |
| [MEDIUM] [TEST] E: multi-PC (2+ player-side actors with cells) untested through the zone layer — `seating.py`'s own doctrine says a table of PCs is the common case, not an edge | `tests/game/ruleset/test_fate_zone_binding.py` (fixture `_fate_conflict`) | TEA adds a 2-PC + 1-opponent binding test asserting all three get valid zones |
| [LOW] [RULE] A: 2 new test files fail the repo's `uv run ruff check` (I001) as committed — RED→GREEN isort reclassification (`zones` module now exists → first-party); `just server-lint` fails freshly on this branch | `tests/game/ruleset/test_fate_zone_binding.py:32`, `tests/game/tactical/test_zones.py:24` | apply the mechanical import reorder (ruff --fix) and commit |
| [LOW] [DOC] F: "ties break to the lowest zone id" is lexicographic, not numeric (`z10 < z2`); plan text says "lowest zone id" — latent doc/spec divergence past 10 zones | `sidequest/game/tactical/zones.py:9-11,95` | reword docstring + inline comment to "lexicographically-smallest zone-id string" (or zero-pad ids) |
| [LOW] [RULE] N: zone/span imports local-in-method in `fate.py` with no cycle to justify, breaking the file's own top-level span-import convention | `sidequest/game/ruleset/fate.py:551-552,585-586` | hoist to module top (no cycle — verified by import) |
| [LOW] [TEST] O: truthy-only assert `placed["Hero"] and placed["Rival"]` | `tests/game/ruleset/test_fate_zone_binding.py:140` | assert specific zone-id values |

**Disabled-specialist domains, self-assessed:** [EDGE] boundary conditions on the projection hand-checked — empty mask, all-wall, all-choke corridor, open room all pinned by tests; the two REAL edge holes found are G (disconnected components) and H (same-zone unknown), both in the severity table. [SILENT] silent-failure sweep is the K/G/C findings above — the diff introduces no try/except at all, so swallowed-exception risk is nil; the silence here is control-flow, not exceptions. [TYPE] both new dataclasses are frozen with full annotations; `type() is` delegation test pins the import-don't-redefine contract; no stringly-typed API introduced (zone ids are strings by design — the projection is the validator). [SEC] no auth/tenant/injection surface: the mask is server-persisted content, b64-decoded per established `dice.py:359` precedent; no user input reaches the new code un-adjudicated. [SIMPLE] no dead code beyond the sanctioned `adjudicate_zone_move` deferral (disclosed, named follow-up); no over-engineering — the algorithm is the plan's, minimal.

**Data flow traced:** player action → confrontation dispatch → `instantiate_encounter_from_trigger` → `_seat_tactical_cells` (store mask + anchors → `seat_actor_cells` stamps cells) → Fate isinstance gate → b64 mask decode → pure `project_zones` → `encounter.zones` + `per_actor_state['zone']` → `tactical.zone.projected` → `_mirror` → `publish_event` → turn_telemetry sink → GM panel. Safe: mask is store-owned content (not player input); corrupt b64 raises loudly; per-session row locks serialize writes (ADR-115).
**Pattern observed:** good — the wiring test discriminates gate-off from grid-dead by asserting cells DID seat before asserting zones did NOT (`test_fate_zone_seating_wiring.py:214-218`); this is the honest-negative pattern the repo should keep.
**Error handling:** `get_ruleset_module` raises `UnknownRulesetError` on garbage slug (fail-loud, correct); the two silent guards flanking it are finding K.
**Verified good (evidence):** [VERIFIED] WN/dial packs untouched — `FateRulesetModule` subclasses `RulesetModule` directly (`fate.py:58`), no WN sibling inherits it, and the passing negative test proves cells seat while zones stay `[]`; complies with Bind-the-Ruleset doctrine (no native mechanic tuned against a binding — zones are Fate-only state). [VERIFIED] single mask load — `mask_dict` (`encounter_lifecycle.py:1728`) reused at `:1745`, no reload. [VERIFIED] monkeypatch targets correct — `_mirror` resolves `publish_event` from `spans/tactical.py` module globals; `Span.open` resolves `tracer()` lazily from `spans/__init__` (`span.py:25-33`) — both patched where used. [VERIFIED] `tactical.zone.projected` is production-reachable and sink-mirrored — wiring test drives the real trigger with the live pulp_noir pack and asserts the published event, complying with the OTEL Observability Principle.

**Rework routing:** findings are predominantly testable (H, G, B, C, E need failing tests first) → red rework to TEA (Amos Burton); Dev (Naomi Nagata) then greens including the K fail-loud fix, the lint reorder (A), and the doc/import polish (F, I, J, N, O). The `adjudicate_zone_move` no-consumer deferral stays accepted as disclosed debt — do NOT wire a Fate move verb (Grounding Limit #3; Bind the Ruleset, Don't Balance It).

**Handoff:** Back to TEA (red rework) with this table as the work order.

## TEA Assessment (rework round 1)

**Tests Required:** Yes — Reviewer's severity table is the work order.

**Changes (commit 6f28d9d4, pushed):**
- `tests/game/ruleset/test_fate_zone_binding.py` — [H] RED `test_adjudicate_zone_move_unknown_same_zone_is_not_free` (z99→z99 must not be free) + guard pin `test_adjudicate_zone_move_known_same_zone_is_free` (the fix must not break the legitimate stay-put); [B] `placed_count == 2` pinned in the span test + new `test_zone_projected_span_counts_only_placed_actors` (3 actors, 1 unseated → placed_count 2); [C] `test_project_conflict_zones_skips_actor_on_unzoned_cell` (wall-cell actor skipped); [E] `test_project_conflict_zones_zones_a_full_table_of_pcs` (2 PCs + Other, all zoned); [O] truthy assert → exact `{"Hero": "z0", "Rival": "z1"}`; [A] import order fixed.
- `tests/game/tactical/test_zones.py` — [G] RED `test_disconnected_all_choke_component_is_still_zoned` on `SPLIT_CAVERN` (9-cell cored room + 4-cell disconnected all-choke corridor): totality, corridor is its own single zone, no phantom adjacency across the wall, deterministic; [A] import order fixed.
- `tests/server/dispatch/test_fate_zone_seating_wiring.py` — [K] RED `test_seating_fails_loud_on_tactical_block_without_mask_bytes` (`pytest.raises(ValueError, match="mask_bytes_b64")` through the production trigger) and RED `test_seating_fails_loud_on_missing_pack_ruleset` (helper driven directly with `pack=None`, `pytest.raises(ValueError, match="ruleset")`); [B] `placed_count == 2` pinned on the production-path span.

**Rework-RED verified** (testing-runner, RUN_ID 165-5-tea-red-2): 33 collected — 4 FAIL for exactly the mapped reasons (free=True for z99→z99; 4 orphaned corridor cells; DID NOT RAISE ×2), 29 PASS including all regression pins. No errors, no typo-failures.

**Contract decision for Dev ([K], within Reviewer-granted latitude):** the mask-bytes branch is pinned as **fail-loud ValueError** (not the honest-skip span option). Rationale: a `tactical` block without `mask_bytes_b64` is an *impossible* state (materializer only merges tactical into a dict already carrying mask bytes) — impossible states raise per the `_raise_missing_ruleset` doctrine; the honest-skip span is reserved for the *legitimate* no-tactical-block state, which stays unchanged. Test pins `match="mask_bytes_b64"` and `match="ruleset"` — put those words in the messages.

**Doc-only items for Dev (no tests, from Reviewer table):** [F] lexicographic tie-break wording in `zones.py:9-11,95` (+ totality wording becomes TRUE once G is fixed — reword to match the per-component seeding); [I] broaden `project_conflict_zones` docstring to name both skip paths; [J] `_seat_tactical_cells` docstring documents the (now fail-loud) guards; [N] hoist `fate.py` zone/span imports to module top.

**Handoff:** To Dev (Naomi Nagata) for GREEN — 4 failing tests + doc/import polish; the `adjudicate_zone_move` no-consumer deferral stays as-is (do NOT wire a Fate move verb).

## Dev Assessment (rework round 1)

**Implementation Complete:** Yes

**Files Changed (commit 61504bd6, pushed):**
- `sidequest/game/ruleset/fate.py` — **[H]** `adjudicate_zone_move` validates zone membership (`from_zone in projection.zones and to_zone in projection.zones`) BEFORE the same-zone shortcut, so an unknown zone id (incl. `z99→z99`) is never `free`; **[I]** `project_conflict_zones` docstring now names both skip paths (`cell is None` and `zid is None`); **[N]** the four local-in-method zone/span imports hoisted to module top (+ `ZoneProjection` consolidated there — logged as a minor deviation).
- `sidequest/game/tactical/zones.py` — **[G]** `project_zones` is now TOTAL: a floor component with no cored seed floods as its own zone, one per connected component (no orphaned cells); **[F]** docstring reworded to lexicographically-smallest tie-break + the (now true) totality guarantee. *(This file was already edited uncommitted from the pre-context-clear session; verified correct and committed this round.)*
- `sidequest/server/dispatch/encounter_lifecycle.py` — **[K]** `_seat_tactical_cells`'s two silent `return` guards fail LOUD: missing pack ruleset → `_raise_missing_ruleset("fate_zone_projection")` (msg contains "ruleset"); tactical block without `mask_bytes_b64` → `ValueError` (msg contains "mask_bytes_b64"); **[J]** docstring documents both fail-loud guards + the preserved honest `seated_count=0` skip span.

**Tests:** Story suite 33/33 GREEN (was 30/33 — the 3 red were [H]×1 + [K]×2; [G] already green from the carried-over `zones.py` fix). Targeted regression sweep 54/54 (zones + Fate binding + wiring + WN sibling binding + telemetry sink + routing completeness). Full server suite **serial (`-n0`): 14,913 passed / 341 skipped / 1 failed** — the single failure is the known pre-existing `test_dungeon_map_frame_is_emitted_to_ui` (develop regression, unrelated). Ruff clean on all touched files; **0 new pyright errors** (14 pre-existing in `encounter_lifecycle.py`, all outside the diff; `fate.py`/`zones.py` report 0). *(Parallel run shows 2 extra failures that pass in isolation — xdist flakiness, logged as a Delivery Finding.)*

**Branch:** `feat/165-5-fate-zones-seating` (pushed; rework commit 61504bd6 on top of TEA's rework-red 6f28d9d4).

**Pre-handoff review (requesting-code-review skill):** dispatched a reviewer over `6f28d9d4..61504bd6` — verdict **"ready to proceed"**, 0 Critical, 0 Important. It independently verified: the [H] membership source is correct for all four known/unknown combinations; [G] totality is provably free of phantom cross-wall adjacency (same `neighbors()` for flood + adjacency); [K] fail-loud rests on a materializer invariant (`_tactical_into_mask_dicts` only merges a tactical block into a dict already carrying `mask_bytes_b64`) it read and confirmed; no new import cycle. Three Minors, none requiring a change: (#1) the `zid is None` silent-skip doctrinal asymmetry — logged as a Delivery Finding (TEA's regression test pins the skip, so it's intentionally out of scope); (#2) the "dead" `if mask_dict else None` branch — **kept**, it is load-bearing for pyright None-narrowing (`mask_dict` is typed `dict | None`; removing it would introduce a new `reportOptionalMemberAccess` error); (#3) lexicographic tie-break — already addressed via the [F] docstring.

**Handoff:** To Chrisjen Avasarala (Reviewer) for the review phase.

## Subagent Results

*(Rework round 1 review — round 2. Same subagent toggles as round 1: 4 enabled, 5 disabled. Diff under review: `git diff 2765aaea..HEAD` — TEA's rework-red tests + Dev's green fixes.)*

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 | N/A — ruff clean (I001 fixed), 33/33 targeted tests pass, 14 pyright errors ALL pre-existing outside the changed regions |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — domain self-assessed ([EDGE]) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — domain self-assessed ([SILENT]) |
| 4 | reviewer-test-analyzer | Yes | findings | 2 (1 medium, 1 low) | confirmed 2, both non-blocking (Delivery Findings): missing `@_needs_fate_pack` guard + unused pack load; span-level `placed_count` only covers the `cell is None` skip |
| 5 | reviewer-comment-analyzer | Yes | clean | 0 | N/A — all docstrings/comments verified accurate; independently corroborated the materializer `mask_bytes_b64` invariant |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — domain self-assessed ([TYPE]) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings — domain self-assessed ([SEC]) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — domain self-assessed ([SIMPLE]) |
| 9 | reviewer-rule-checker | Yes | findings | 1 (low) | confirmed 1, non-blocking (Delivery Finding): rule-#10 `ZoneProjection` hoisted out of `TYPE_CHECKING` though annotation-only |

**All received:** Yes (4 enabled returned, 5 disabled via settings)
**Total findings:** 3 confirmed (all non-blocking), 0 dismissed, 0 deferred

### Rule Compliance

Rubric: `.pennyfarthing/gates/lang-review/python.md` (13 checks) + CLAUDE.md/SOUL.md project rules. Exhaustive enumeration by reviewer-rule-checker (17 rules, 32 instances); Reviewer spot-verified the load-bearing ones.

| Rule | Instances | Verdict |
|------|-----------|---------|
| #1 silent exceptions | 0 try/except in diff | compliant — the rework's entire point is REMOVING two silent returns |
| #2 mutable defaults | 0 new/changed signatures | compliant |
| #3 type annotations at boundaries | 3 public fns unchanged + `_seat_tactical_cells` (private, exempt) | compliant |
| #4 logging | 2 new raise sites | compliant — propagate per the in-file `_raise_missing_ruleset` convention (siblings at :1949/:2624 don't log either); messages carry `room_id`, no sensitive data |
| #5 path handling | none | n/a |
| #6 test quality | 11 test instances | compliant except two **non-blocking** improvements ([TEST], below); the [O] truthy assert is fixed to exact dict-equality |
| #7 resource leaks | 0 | n/a |
| #8 unsafe deserialization | `b64decode` is unchanged context, not in diff | n/a to diff |
| #9 async | none | n/a |
| #10 import hygiene | 7 (the [N] hoist) | **1 LOW nit**: `ZoneProjection` runtime-imported though annotation-only under PEP 563 (could stay `TYPE_CHECKING`). No cycle — `zones.py`/`spans.tactical` traced, neither reaches `fate.py`. Non-blocking. |
| #11 input validation | the two fail-loud invariant checks | compliant — strengthened (store-derived state validated at the seating boundary) |
| #12 dependency hygiene | no dep changes | n/a |
| #13 fix-introduced regressions | full re-scan | compliant — only the #10 nit; no new bare-except/mutable-default/silent path |
| No Silent Fallbacks (CLAUDE.md) | 2 return→raise conversions | **compliant — this IS the fix**: both silent `return`s replaced with distinct, well-messaged raises matching the `_raise_missing_ruleset` doctrine |
| Bind the Ruleset (SOUL.md) | isinstance gate | compliant — zones stay Fate-only projection state; the two new checks are pack-family-agnostic data-integrity invariants, no native mechanic tuned against the binding |
| OTEL Observability | `tactical.zone.projected` / `.move` | compliant — spans still fire, `SPAN_ROUTES` untouched, and `placed_count` is now asserted (the round-1 [B] gap is closed) |
| Every suite needs a wiring test | `test_fate_zone_seating_wiring.py` | compliant — drives the real `instantiate_encounter_from_trigger` with the live pulp_noir pack |

### Devil's Advocate

Let me argue this ships broken. The rework's boldest move is converting two silent `return`s into hard `raise`s inside `_seat_tactical_cells` — a function on the **live confrontation-seating hot path** (`run_confrontation_dispatch` / `run_dogfight_dispatch` → `instantiate_encounter_from_trigger` → here). A raise where there was a graceful skip is exactly how a "fix" turns a quiet degradation into a table-flipping crash mid-session. So: can either raise fire in production? The ruleset branch fires only when `pack is None` — but `instantiate_encounter_from_trigger` types `pack` as a non-Optional `GenrePack` and dereferences it *unguarded* (`defs = pack.rules.confrontations if pack.rules else []`) hundreds of lines before reaching the seating helper, so a None pack already dies upstream; and `GenrePack.rules` is a required `RulesConfig`, so `pack.rules` is never None. The mask branch fires only when a `tactical` block exists but `mask_bytes_b64` doesn't — and the comment-analyzer *traced the materializer* (`RegionMask.to_dict()` always writes the bytes; `_tactical_into_mask_dicts` merges the tactical block into that already-populated dict), so the absent-bytes state is a genuinely unreachable corrupt store. Both raises are `ValueError`, and both live callers catch only `NoOpponentAvailableError` (a ValueError subclass) — *not* bare `ValueError` — so a real corruption propagates loudly instead of being swallowed. Good: fail-loud is honored, and the impossible states are truly impossible.

Where else could it break? The [G] totality flood could mint a phantom cross-wall adjacency, silently merging two rooms a homebrew author drew as separate — but the flood and the adjacency pass share the same 8-connected `neighbors()`, and any cell reachable from a seed was already claimed by the BFS, so orphan components are provably `neighbors`-isolated (I hand-traced SPLIT_CAVERN: a 2-column wall gap, unbridgeable by 8-connectivity). The [H] membership guard could over-restrict and deny a legitimate stay-put — but `test_adjudicate_zone_move_known_same_zone_is_free` pins `z1→z1` still free. The real soft spots are cosmetic: one test errors instead of skipping when `sidequest-content` is absent (it isn't, here), and `placed_count`'s off-floor skip path is only pinned at the dict layer, not the span layer. Neither corrupts a byte in production. I tried to make this bleed; it didn't.

## Reviewer Assessment

**Verdict:** APPROVED

*(Rework round 1 review — round 2. Round 1 REJECTED with a 10-row severity table; every item is addressed and empirically re-verified.)*

**Round-1 findings — all resolved (verified, not taken on faith):**
- **[MEDIUM][RULE] K** silent seating guards → **fail-loud** `_raise_missing_ruleset("fate_zone_projection")` + `ValueError("…mask_bytes_b64…")`. Both pinned RED→GREEN (`test_seating_fails_loud_*`). Production-safe: `pack` is non-Optional and dereferenced upstream; the corrupt-mask state is unreachable per the traced materializer invariant.
- **[MEDIUM][DOC] H** `z99→z99` free teleport → **membership validated before the same-zone shortcut** (`known = from_zone in projection.zones and to_zone in projection.zones`). `projection.zones` is the authoritative key set; correct across all known/unknown × same/adjacent combos. Pinned by `test_adjudicate_zone_move_unknown_same_zone_is_not_free` + the `_known_same_zone_is_free` guard.
- **[MEDIUM][DOC] G** false totality → **per-component flood** seeds every core-less connected component its own zone; the deleted degenerate branch is losslessly subsumed. `test_disconnected_all_choke_component_is_still_zoned` (SPLIT_CAVERN — hand-verified genuinely disconnected).
- **[MEDIUM][TEST] B** `placed_count` unasserted → asserted `== 2` on both the unit span and the production-path span, plus `test_zone_projected_span_counts_only_placed_actors`.
- **[MEDIUM][TEST] C+I** `zid is None` skip untested/undocumented → `test_project_conflict_zones_skips_actor_on_unzoned_cell` + docstring names both skip paths.
- **[MEDIUM][TEST] E** multi-PC untested → `test_project_conflict_zones_zones_a_full_table_of_pcs`.
- **[LOW][RULE] A** test-file I001 → ruff clean (preflight confirmed).
- **[LOW][DOC] F** tie-break wording → "lexicographically-smallest" (comment-analyzer verified against the sort key).
- **[LOW][RULE] N** local-in-method imports → hoisted to module top (see the one residual [RULE] nit below).
- **[LOW][TEST] O** truthy assert → exact `{"Hero": "z0", "Rival": "z1"}`.

**Confirmed findings this round (all non-blocking — no Critical/High):**
- **[TEST]** `test_seating_fails_loud_on_missing_pack_ruleset` lacks the `@_needs_fate_pack` guard its siblings carry yet loads (and discards) the real pulp_noir pack → errors instead of skipping when `sidequest-content` is absent. Medium confidence; passes today. Delivery Finding.
- **[TEST]** span-level `placed_count` only exercises the `cell is None` skip; the `zid is None` (off-floor) skip is pinned only at the dict-return layer. Low confidence; underlying `placed` dict is already pinned for both paths, so a miscount is still caught. Delivery Finding.
- **[RULE]** `ZoneProjection` hoisted out of `TYPE_CHECKING` though annotation-only under PEP 563 — could stay type-only. Confirmed (not dismissed), LOW, zero functional/dependency cost. Delivery Finding + ACCEPTED-with-note deviation stamp.

**Self-assessed disabled domains:** **[EDGE]** boundary conditions hand-checked — empty mask → empty projection (existing test), all-choke corridor → one zone, disconnected component → own zone, unknown/known zone-move combos all pinned; no edge holes. **[SILENT]** the diff introduces zero `try/except`; the two former silent returns are now loud raises; the two per-actor skips (`cell is None`, `zid is None`) are honest-skips observable via `placed_count`, not swallowed errors. **[TYPE]** both dataclasses frozen; the membership guard keys on the authoritative `projection.zones`; the fail-loud ternary types `ruleset_slug` as a clean `str`; the only type-hygiene item is the `ZoneProjection` TYPE_CHECKING nit above. **[SEC]** no auth/tenant/injection/user-input surface — the mask is server-persisted content b64-decoded per unchanged established precedent; the new raises are internal invariant checks. **[SIMPLE]** the totality loop replaces a special-case branch (net simplification); the retained `if mask_dict else None` is load-bearing for pyright None-narrowing (`mask_dict` is `dict | None`), not dead code; no over-engineering.

**Data flow traced:** player action → confrontation/dogfight dispatch → `instantiate_encounter_from_trigger` (pack: GenrePack, non-Optional) → `_seat_tactical_cells(pack=pack)` → store mask load → tactical-block gate → **[K]** ruleset + mask_bytes_b64 fail-loud guards → `isinstance(ruleset, FateRulesetModule)` gate → `project_conflict_zones` → pure `project_zones` (now total) → `encounter.zones` + `per_actor_state['zone']` → `tactical.zone.projected` (zone_count + placed_count) → `_mirror` → `publish_event` → turn_telemetry sink → GM panel. Safe: store-owned content, corrupt states raise loudly, per-session row locks serialize writes.

**Pattern observed:** honest-negative testing retained — `test_wn_pack_on_same_grid_projects_no_zones` asserts cells DID seat before asserting zones did NOT, discriminating gate-off from grid-dead (`test_fate_zone_seating_wiring.py`).
**Error handling:** the two new `ValueError` raises fail loud and propagate (callers catch only `NoOpponentAvailableError`, not bare `ValueError`); `get_ruleset_module` still raises `UnknownRulesetError` on a garbage slug.
**Verified good (evidence):** [VERIFIED] no import cycle — `sidequest.game.tactical.zones` imports only `tactical.adjudication`; `sidequest.telemetry.spans.tactical` imports only watcher_hub/_core/span; neither reaches `fate.py` (rule-checker + Reviewer traced). [VERIFIED] `pack.rules` non-None — `pack.py:400 rules: RulesConfig` (required); ruleset raise reachable only on `pack is None`, itself impossible past the trigger's unguarded `pack.rules` deref. [VERIFIED] materializer invariant — `RegionMask.to_dict()` always writes `mask_bytes_b64` before `_tactical_into_mask_dicts` merges the tactical block (comment-analyzer traced materializer.py:378/1631). [VERIFIED] genuine RED→GREEN — test-analyzer ran the new tests against pre-rework source in an isolated worktree; all fail on old code, pass on new.

**Handoff:** To SM (Camina Drummer) for finish-story.