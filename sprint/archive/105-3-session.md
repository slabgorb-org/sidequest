---
story_id: "105-3"
jira_key: ""
epic: "105"
workflow: "tdd"
---
# Story 105-3: Reverse seam — leaving the Deep: entrance→surface ascent (back up the rope)

## Story Details
- **ID:** 105-3
- **Jira Key:** (none — personal project)
- **Workflow:** tdd
- **Stack Parent:** 105-2

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-13T21:49:30Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-13T20:47:57Z | 2026-06-13T20:49:28Z | 1m 31s |
| red | 2026-06-13T20:49:28Z | 2026-06-13T20:58:46Z | 9m 18s |
| green | 2026-06-13T20:58:46Z | 2026-06-13T21:18:44Z | 19m 58s |
| review | 2026-06-13T21:18:44Z | 2026-06-13T21:27:11Z | 8m 27s |
| red | 2026-06-13T21:27:11Z | 2026-06-13T21:34:27Z | 7m 16s |
| green | 2026-06-13T21:34:27Z | 2026-06-13T21:45:45Z | 11m 18s |
| review | 2026-06-13T21:45:45Z | 2026-06-13T21:49:30Z | 3m 45s |
| finish | 2026-06-13T21:49:30Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Question** (non-blocking): The AC3 projection (`current_region_exits` at the entrance node) is gated by an `actor_location_unresolved` skip — `_build_state_summary` logs `intent_router.region_exits projection_skipped reason=actor_location_unresolved` when the PC is at `ENTRANCE_ID` because the entrance node is not a cartography region. Affects `sidequest/server/intent_router_pass.py` (`_build_state_summary`) — Dev must let the projection treat the dungeon entrance node as a resolvable location and derive the surface exit from the descent route's `from_id` (the_dropmouth) without needing the dungeon store. *Found by TEA during test design.*
- **Improvement** (non-blocking): The surface owner of the entrance crossing is derivable from cartography ALONE — the descent route `from_id=the_dropmouth → to_id=deep_descent` means the ascent target is that route's `from_id`. A reverse lookup over `cartography.routes` (route whose `to_id` is a registered seam kind) avoids needing a separate reverse `Route` object in content. Affects `sidequest/game/seams/` + `intent_router_pass.py`. *Found by TEA during test design.*

### TEA (test design — review rework)
- **Conflict** (blocking): The Reviewer's finding-#1 fix text gives two hints that pull apart — "wrap `resolve_surface_ascent` in `try/except SeamCrossingError → _unresolved`" (fail LOUD via `movement.unresolved`) vs. "filter null `from_id` in `surface_owner_for_entrance` (skip/ambiguity, not return)" (which makes `ascent_route is None` → the branch falls through to `region_mode_deferred`, a SILENT defer). A registered-kind (`deep_descent`) route IS a seam — a malformed one is a wiring fault that must surface on the GM panel, not be hidden by the same defer path a genuinely seam-less world (oz) uses. The new RED tests pin the loud channel (`movement.unresolved`). Affects `sidequest/agents/subsystems/movement.py` (the load-bearing fix is the `try/except`; let `surface_owner_for_entrance` keep returning the malformed route so `resolve_surface_ascent` raises and the caught error becomes `_unresolved`) — do NOT filter null `from_id` to None in `surface_owner_for_entrance`, or the malformed seam defers silently and `test_null_from_id_seam_fails_loud_not_raises` stays red. *Found by TEA during test design (review rework).*

### Dev (implementation)
- **Gap** (non-blocking): Multi-descent worlds are not yet supported — `surface_owner_for_entrance` returns None when 2+ distinct surface regions each own a `deep_descent` route, so the ascent defers rather than choosing. The single shared `ENTRANCE_ID` node can't disambiguate which surface to return to. Affects `sidequest/game/seams/registry.py` (`surface_owner_for_entrance`) — a future multi-entrance dungeon needs per-entrance seam provenance to resolve the owner. No current world has multiple descents. *Found by Dev during implementation.*
- **Question** (non-blocking): The two sibling pingpong findings in the SM Assessment (narration_apply cartography-advance prose-teleport ~line 3895; `attach_dungeon_to_session` seeding `pc_regions=entrance` before cartography init) were left OUT of scope — the reverse-seam ascent does not require them and they are independent defects. Affects `sidequest/agents/.../narration_apply` + dungeon attach — recommend a separate story per Architect. *Found by Dev during implementation.*

### Dev (implementation — review rework)
- **Improvement** (non-blocking): Adding `pyright` to the dev-exit gate (the Reviewer's own non-blocking finding) would have caught the `intent_router_pass.py` type error before review. The original 105-3 green passed `just server-check` (lint+test) but not `pyright`. Affects `justfile` / `.pennyfarthing/gates/dev-exit` — consider `pyright` on changed files. *Found by Dev during implementation (review rework).*
- **Resolved** (non-blocking): Reviewer finding #1 (uncaught raise), #2 (pyright), #3 (phantom-region bind) all fixed and verified — full suite 10718 passed / 0 failed, pyright 0 errors on all three touched files. The TEA blocking Conflict (loud vs. silent-defer) is resolved in favor of `movement.unresolved`; `surface_owner_for_entrance` intentionally left unchanged. *Found by Dev during implementation (review rework).*

### Reviewer (code review)
- **Gap** (blocking): The ascent branch in `movement.py` does not catch `SeamCrossingError`, so a `deep_descent` route with a null/empty `from_id` (legal — `Route.from_id` is `str | None = None` with NO validator enforcement) makes `resolve_surface_ascent` raise uncaught out of `run_movement_dispatch`, skipping the mandated `movement.unresolved` span. Affects `sidequest/agents/subsystems/movement.py` (wrap the call in `try/except SeamCrossingError` → `_unresolved`, mirroring the descent block) and `sidequest/game/seams/registry.py` (filter null `from_id` in `surface_owner_for_entrance`). *Found by Reviewer during code review.*
- **Gap** (blocking): `intent_router_pass.py:426` fails `pyright` — `owner.name` is `str | None`, so the appended dict violates the `list[dict[str, str]]` annotation. `just server-check` gates lint+test but NOT pyright, so it passed RED/GREEN unnoticed. Affects `sidequest/server/intent_router_pass.py` (use `owner.name or ascent.from_id`). *Found by Reviewer during code review (preflight).*
- **Improvement** (non-blocking): No project gate runs `pyright`; a typecheck regression in changed files can reach review unflagged. Affects the server check pipeline / justfile — consider adding pyright-on-changed-files to the dev-exit gate. *Found by Reviewer during code review.*

### Reviewer (code review — re-review)
- **Improvement** (non-blocking): Pre-existing ruff `I001` (un-sorted imports) at `tests/game/pg/test_telemetry_sink_missing_session.py:71` — present on `develop`, untouched by 105-3, `--fix`-able. Not a 105-3 regression (verified: file absent from `develop..HEAD`); flagged only so it isn't lost. *Found by Reviewer during code review (re-review).*
- **Improvement** (non-blocking): The AC3 entrance projection still lists a seam exit named after a malformed route's `from_id` (e.g. `ghost_dropmouth`) that movement-dispatch then fails loud on. Cosmetic incoherence in a malformed-pack-only path; the fail-loud `movement.unresolved` is the safety net. Affects `sidequest/server/intent_router_pass.py` (`_build_state_summary`) — a future tidy could skip the projection when `from_id` isn't in `cartography.regions`. *Found by Reviewer during code review (re-review).*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **seam_kind stays "deep_descent" on ascent (NOT a new "surface_ascent" kind)**
  - Spec source: sprint YAML story 105-3 description + context-story-105-3.md, AC2
  - Spec text: "movement.resolved seam_kind=deep_descent resolved_via=surface_ascent"
  - Implementation: Tests assert `seam_kind == "deep_descent"` (the same bidirectional route) and `resolved_via == "surface_ascent"` (the new direction discriminator). A pre-test code-scout subagent proposed a NEW `seam_kind="surface_ascent"` registry entry; that contradicts the story and was rejected per the spec-authority hierarchy (story scope wins).
  - Rationale: The seam is one bidirectional route at the threshold; the kind names the route, the `resolved_via` names the direction. Keeping `seam_kind` stable matches the descent contract and the GM-panel lie-detector reads one seam, two directions.
  - Severity: minor
  - Forward impact: Dev should reverse-traverse the existing `deep_descent` seam, not register a second kind.
- **AC tested at the behavioral layers (movement dispatch + projection), no resolver-unit test**
  - Spec source: context-story-105-3.md, AC1/AC2
  - Spec text: "resolves the PC to the seam-owning cartography region ... via the per-PC patch path"
  - Implementation: Tests drive `run_movement_dispatch(...)` and `_build_state_summary(...)` — the real production entry points — rather than asserting a specific new resolver module/function exists (e.g. `resolve_surface_ascent`).
  - Rationale: TEA pins ACs and observable behavior, not implementation shape. Behavioral tests double as wiring tests and survive Dev's choice of internal structure (reverse-lookup vs new resolver). Avoids over-coupling to the scout's proposed file layout.
  - Severity: minor
  - Forward impact: Dev is free to choose the internal mechanism so long as the dispatch + projection contracts hold.
- **AC4 non-regression delegated to the existing 105-2 suites, not duplicated**
  - Spec source: context-story-105-3.md, AC4
  - Spec text: "in-dungeon traversal ... and the 105-2 surface→deep crossing remain green"
  - Implementation: No new copies of the descent / in-graph traversal tests; AC4 is verified by running the existing `test_movement_seam_crossing.py`, `test_seam_deep_descent.py`, and `test_intent_router_region_exits.py` suites and confirming they still pass. NEW ascent-specific guards (`test_deeper_from_entrance_does_not_ascend`, `test_no_seam_world_does_not_invent_surface`) cover the no-fallback boundary the ascent introduces.
  - Rationale: AC4 is literally "remain green" — re-asserting existing coverage is duplication; the green run IS the assertion.
  - Severity: minor
  - Forward impact: Dev/Reviewer must run the full server suite (not just the new files) to honor AC4.
- **Malformed-seam ascent pinned to `movement.unresolved` (fail loud), NOT a silent `region_mode` defer**
  - Spec source: Reviewer Assessment (REJECTED 2026-06-13) finding #1 handoff text + CLAUDE.md OTEL Observability Principle + SOUL "No Silent Fallbacks"
  - Spec text: "null `from_id` → graceful `_unresolved` + `movement.unresolved` span, NOT an uncaught raise" — but the same finding's fix also says "filter null `from_id` in `surface_owner_for_entrance` (skip/ambiguity, not return)", which would route the case to `region_mode_deferred` (silent)
  - Implementation: The two rework tests assert a `movement.unresolved` span fires (and no `movement.resolved`), pinning the LOUD channel for a malformed registered-kind seam — distinct from the oz no-seam world, which correctly defers. The malformed-route case is NOT pinned to defer.
  - Rationale: A route with `to_id="deep_descent"` is explicitly a seam; a missing/typo'd `from_id` is a wiring fault, not the absence of a dungeon. Deferring it silently hands a confabulated "way up" to the narrator — the exact "convincing narration, zero mechanical backing" the OTEL lie-detector exists to catch. Failing loud lights the GM panel for the author (Jade writes packs now). This resolves the two-hint tension in the Reviewer's fix toward the principle-grounded, explicitly-stated `movement.unresolved` contract.
  - Severity: minor
  - Forward impact: Dev should make the `try/except SeamCrossingError → _unresolved` wrap the load-bearing fix and let `surface_owner_for_entrance` keep returning the malformed route (or add an explicit unresolved emit). Filtering null `from_id` to None in `surface_owner_for_entrance` will leave `test_null_from_id_seam_fails_loud_not_raises` red.

### Dev (implementation)
- **Ascent triggers on any non-deeper intent at the entrance (symmetric to the descent rule)**
  - Spec source: context-story-105-3.md, AC1 + sprint YAML story description
  - Spec text: "a back/up/toward_exit intent with no deeper in-graph candidate resolves the PC to the seam-owning cartography region"
  - Implementation: The region-mode entrance branch fires when `from_region == ENTRANCE_ID and direction != "deeper"` — i.e. ANY departure intent (back/up/toward_exit AND a descriptor-only "back up the rope"), mirroring the descent's "any intent except back crosses down" rule, rather than an explicit allow-list of three direction tokens.
  - Rationale: Symmetry with the existing descent crossing keeps one mental model; it also covers the descriptor-only departure case TEA tested (`("", "back up the rope")`) which an explicit token list would miss. The discrimination guard (`deeper` must not ascend) is preserved by the `!= "deeper"` gate.
  - Severity: minor
  - Forward impact: none — behavior is a strict superset of the AC's listed tokens; the guard tests pin the boundary.
- **surface_ascent is a directly-called resolver, NOT a registry-keyed seam kind**
  - Spec source: TEA Design Deviation ("seam_kind stays deep_descent"), context-story-105-3.md AC2
  - Spec text: "movement.resolved seam_kind=deep_descent resolved_via=surface_ascent"
  - Implementation: Added `seams/surface_ascent.py::resolve_surface_ascent`, imported and called directly from `movement.py` (mirroring how `resolve_deep_descent` is also called directly for the room-graph door). It is intentionally NOT added to the `_REGISTRY` dict, because the registry maps a descent `seam_kind`→resolver and the ascent reuses the SAME route (`to_id="deep_descent"`); registering a new kind would have contradicted TEA's deviation and the story.
  - Rationale: Honors the one-bidirectional-route model; keeps `seam_kind` stable for the GM panel.
  - Severity: minor
  - Forward impact: none.
- **Ambiguous/absent seam owner defers rather than fails loud**
  - Spec source: SOUL "No Silent Fallbacks"; context-story-105-3.md
  - Spec text: implicit — the engine must not invent a surface region
  - Implementation: When `surface_owner_for_entrance` finds zero or ambiguous (>1 distinct from_id) owners, the ascent branch is skipped and the move falls through to `region_mode_deferred` (the pre-existing path) — NOT an ERROR `movement.unresolved`.
  - Rationale: A region-mode world without a seam route legitimately has no dungeon entrance (the oz-shaped degenerate fixture); deferring is the correct non-ascent outcome and matches the existing region-mode contract. The key No-Silent-Fallback property — never binding the PC to a fabricated surface region — holds: no owner means no patch, no movement. The multi-descent ambiguity is logged as a Delivery Finding for future fail-loud handling.
  - Severity: minor
  - Forward impact: a future multi-descent world should upgrade the ambiguous case to fail-loud.
- **(rework) Malformed seam fails loud via the try/except, NOT by filtering null `from_id` in `surface_owner_for_entrance`**
  - Spec source: Reviewer Assessment finding #1 fix-text vs. TEA blocking Conflict (Delivery Findings — review rework)
  - Spec text: Reviewer fix said "filter null `from_id` in `surface_owner_for_entrance` (skip/ambiguity, not return)" — which would route the malformed route to `region_mode_deferred` (silent)
  - Implementation: Left `registry.py::surface_owner_for_entrance` UNCHANGED (still returns the malformed registered-kind route). The fix lives in `movement.py` (wrap `resolve_surface_ascent` in `try/except SeamCrossingError → _unresolved`) and `surface_ascent.py` (raise `no_surface_owner` for null `from_id`, `dangling_surface_owner` for an unmapped region). Both error reasons fail loud through `movement.unresolved`.
  - Rationale: A registered-kind (`deep_descent`) route IS a seam — a malformed one is a wiring fault that must light the GM panel, not be hidden by the same silent defer a genuinely seam-less world (oz) uses. Filtering to None would have made `test_null_from_id_seam_fails_loud_not_raises` stay red. Honors TEA's higher-authority test contract + the OTEL principle; resolves the two-hint tension in the Reviewer's fix toward the explicitly-stated `movement.unresolved` channel.
  - Severity: minor
  - Forward impact: `surface_owner_for_entrance` still returns null/unmapped-`from_id` routes; the loud-fail guard lives in the resolver + caller, not the registry.
- **(rework) pyright fix uses `surface_id or _region_id`, not the Reviewer's literal `owner.name or ascent.from_id`**
  - Spec source: Reviewer Assessment finding #2
  - Spec text: "`\"name\": owner.name or ascent.from_id`"
  - Implementation: `intent_router_pass.py` — `surface_id = ascent.from_id; owner = _cart.regions.get(surface_id) if surface_id else None; "name": owner.name if owner is not None else (surface_id or _region_id)`.
  - Rationale: The literal suggestion `owner.name or ascent.from_id` is still typed `str | None` (because `ascent.from_id` is `str | None`) and would NOT clear pyright. The `or _region_id` (str) fallback makes both branches `str`, satisfying `list[dict[str, str]]`; and `.get(surface_id)` is only called on a truthy str (the `.get(str | None)` arg-type error also cleared). Verified `0 errors` via `uv run pyright`.
  - Severity: minor
  - Forward impact: none.

### Reviewer (audit)
- **TEA: seam_kind stays "deep_descent"** → ✓ ACCEPTED: code emits `seam_kind=route.to_id` (=deep_descent), `resolved_via=surface_ascent` — matches story AC2; the rejected scout guess would have broken the bidirectional-route contract.
- **TEA: behavioral tests, no resolver-unit test** → ✓ ACCEPTED: driving `run_movement_dispatch` / `_build_state_summary` is the stronger choice (doubles as wiring tests).
- **TEA: AC4 delegated to existing suites** → ✓ ACCEPTED: full serial suite ran (10716 passed); existing 105-2 suites green.
- **Dev: ascent triggers on any non-deeper intent (symmetric rule)** → ✓ ACCEPTED with caveat: sound for the current depth-rooted single-entrance dungeon (in-graph moves from the entrance are "deeper" and defer correctly per the discrimination test). FLAGGED as a LOW future risk only — a hypothetical multi-way junction entrance with lateral in-graph exits could see a `direction=""` lateral intent mis-ascend. Not blocking; no such topology exists.
- **Dev: surface_ascent is a directly-called resolver, not registry-keyed** → ✓ ACCEPTED: correct; preserves the single bidirectional seam_kind.
- **Dev: ambiguous/absent owner defers rather than fails loud** → ✗ FLAGGED: the *absent* (zero owners) and *ambiguous* (>1 from_id) cases correctly return None → defer. But the reasoning "the No-Silent-Fallback property holds: no owner means no patch, no movement" MISSED a third shape — a SINGLE registered-kind route with a null `from_id` is returned by `surface_owner_for_entrance` (it only counts distinct from_ids, len==1 for `{None}`), and `resolve_surface_ascent` then RAISES uncaught rather than deferring. See blocking Delivery Finding. The fail-loud channel must be `movement.unresolved`, not an uncaught exception.

## SM Assessment

**Scope:** Single repo — `sidequest-server` only. The orchestrator stays on `main`; no
content/ui/daemon changes. Branch `feat/105-3-reverse-seam-ascent` off `develop`.

**This is the reverse of a just-merged story, not greenfield.** 105-2 (server PR #831 +
content PR #430, both merged 2026-06-12) built the surface→deep seam crossing and the
bidirectional seam registry. 105-3 wires the *ascent*: a PC standing on the dungeon
entrance node who intends back/up/toward_exit with no in-graph candidate edge must resolve
to the cartography region that OWNS the seam route (`seam_route_for(from_id)` → `the_dropmouth`)
via the same per-PC `pc_region` patch path 105-2 already uses — emitting a `movement.resolved`
span with `resolved_via=surface_ascent` and the `seam_kind`. Today that intent fail-louds with
`movement.unresolved` (`no_candidate_edges`), which is honest but strands the party below.

**Wire-up, not rebuild.** The seam registry is already bidirectional at the threshold and the
per-PC region-patch path exists. The work is the *return* half. TEA must mind the hybrid gates
from the in-dungeon-movement fix: `movement.py` `_defer_region_mode` fall-through and the
`intent_router_pass` dungeon-exits projection — the surface exit should appear in
`current_region_exits` at the entrance node. Load-bearing zones: `movement.py` seam binding,
`narration_apply` location_update.

**OTEL is the gate.** Per project doctrine, the fix must be span-provable: `movement.resolved`
with `resolved_via=surface_ascent` is the lie-detector that the engine — not narrator improv —
crossed the seam upward. RED must assert on the span, not just on prose.

**Adjacent findings flagged in the source pingpong** (TEA/Dev to scope, possibly same-story):
narration_apply cartography-advance prose-teleport hazard (~line 3895), and
`attach_dungeon_to_session` seeding `pc_regions=entrance` before cartography init (bypassed the
105-2 crossing in session 14836). Treat as in-scope-adjacent unless Architect splits them out.

**Routing:** phased TDD → handing to TEA (Fezzik) for the RED phase.

---
## TEA Assessment

**Tests Required:** Yes
**Reason:** Behavioral feature (reverse seam crossing) with three observable ACs + a no-fallback boundary.

**Test Files:**
- `tests/agents/subsystems/test_movement_surface_ascent.py` — the core crossing: entrance-node back/up/toward_exit → ascend to the_dropmouth; the `movement.resolved` span (`resolved_via=surface_ascent`, `seam_kind=deep_descent`); + the discrimination guard (deeper-intent must not hijack) + the No-Silent-Fallback guard (no-seam world must not invent a surface region). Mirrors `test_movement_seam_crossing.py`.
- `tests/server/test_intent_router_region_exits_ascent.py` — AC3 projection: `current_region_exits` at the entrance node lists the surface exit; + the no-seam-world guard. Mirrors `test_intent_router_region_exits.py`.

**Tests Written:** 8 tests (6 + 2) covering AC1, AC2, AC3 and the no-fallback boundary.
**Status:** RED (5 failing on unimplemented behavior, 3 passing control/guard tests, 0 collection errors).

### Rule Coverage (python-review-checklist)

| Rule | Test(s) | Status |
|------|---------|--------|
| #6 test quality — no vacuous asserts | every test asserts a specific value + message (no `assert True`, no bare truthy) | passing structure |
| #6 test quality — negative cases | `test_deeper_from_entrance_does_not_ascend`, `test_no_seam_world_does_not_invent_surface`, `test_no_seam_world_entrance_has_no_surface_exit` | passing guards |
| #1 silent exceptions / No-Silent-Fallback (SOUL) | no-seam-world guards pin that ascent fires only on a real seam route | passing guards |
| OTEL principle (CLAUDE.md) | `test_entrance_node_ascends_to_surface` asserts the `movement.resolved` span + attrs (the lie-detector), not just prose | failing (RED) |

**Rules checked:** test-quality (#6), silent-fallback (#1/SOUL), OTEL-span proof. Other lang-review rules (mutable defaults, async, deserialization, paths, deps) are N/A to test-only changes — they apply to Dev's implementation diff and are deferred to the GREEN gate.
**Self-check:** 0 vacuous tests; every assertion checks a concrete value with a failure message. No source-text wiring asserts (used real entry points + OTEL spans per CLAUDE.md "No Source-Text Wiring Tests").

**RED verification:** `uv run pytest -n0 -v` on both files → `5 failed, 3 passed`; all 5 failures are AssertionError (`resolved_via=region_mode_deferred` instead of `surface_ascent`; `current_region_exits` absent). No import/fixture/collection errors.

**Handoff:** To Dev (Inigo Montoya) for GREEN. Watch items: (1) the AC3 `actor_location_unresolved` projection skip at the entrance node — see Delivery Findings; (2) honor the seam_kind/resolved_via split from Design Deviations; (3) run the FULL server suite for AC4, not just the new files; (4) the entrance node's `back`-defer at the SURFACE seam region (`test_seam_region_back_does_not_cross`) is a DIFFERENT position and must stay green.

---
## TEA Assessment — Review Rework (red)

**Trigger:** Reviewer (Westley) REJECTED the GREEN implementation (2026-06-13): the ascent's error geometry is asymmetric with the descent it mirrors. Re-entered red to pin the malformed-seam contract with failing tests before Dev fixes.

**Tests Required:** Yes
**Reason:** Two of the three findings are testable runtime behaviors (uncaught exception; phantom-region bind). Finding #2 (pyright `str | None` at `intent_router_pass.py:426`) is a static-type defect covered by `uv run pyright`, not a runtime behavior — no test added (documented choice, not an omission).

**Test File:** `tests/agents/subsystems/test_movement_surface_ascent.py` (extended — +2 cartography helpers, +2 fixtures, +2 tests)

**Tests Written (this rework):** 2 new
- `test_null_from_id_seam_fails_loud_not_raises` (finding #1, HIGH) — a registered-kind `deep_descent` route with null `from_id` must NOT raise an uncaught `SeamCrossingError` out of `run_movement_dispatch`; it must fail loud via a `movement.unresolved` span, PC unmoved, no `movement.resolved`.
- `test_dangling_from_id_does_not_bind_phantom_region` (finding #3, MEDIUM) — a `from_id` naming a region absent from `cartography.regions` must NOT bind the PC to a phantom region; it must fail loud via `movement.unresolved` (symmetric to the descent's `entrance_id in graph.nodes` guard), PC unmoved.

**Status:** RED — verified by `testing-runner` (RUN_ID `105-3-tea-red-rework`): `2 failed, 6 passed`.
- #1 fails with an **uncaught** `SeamCrossingError(no_surface_owner)` at `surface_ascent.py:44` — the exact bug.
- #3 fails on `resolved_via == "surface_ascent"` with `to_region == "ghost_dropmouth"` — the missing existence guard.
- The 6 pre-existing tests still PASS (no collection errors, no fixture breakage).

### Rule Coverage (python-review-checklist + project doctrine)

| Rule | Test | Status |
|------|------|--------|
| #1 silent exceptions / SOUL No-Silent-Fallbacks | `test_null_from_id_seam_fails_loud_not_raises` (no uncaught raise; loud `movement.unresolved`, not silent defer) | failing (RED) |
| OTEL Observability Principle (CLAUDE.md) | both tests assert the `movement.unresolved` span fires (GM-panel lie-detector), not prose | failing (RED) |
| #6 test quality — no vacuous asserts | both tests assert concrete values + failure messages; no `assert True` / bare truthy | passing structure |
| Descent/ascent symmetry (Reviewer pattern) | #3 pins the region-existence guard the descent already has and the ascent lacks | failing (RED) |

**Rules checked:** silent-fallback (#1/SOUL), OTEL-span proof, test-quality (#6). No source-text wiring asserts — drove the real `run_movement_dispatch` entry point + asserted OTEL spans (CLAUDE.md "No Source-Text Wiring Tests").
**Self-check:** 0 vacuous tests; the null-`from_id` test's RED is an uncaught exception (the bug itself), the dangling test's RED is a concrete assertion failure.

**Deviation logged:** Pinned `movement.unresolved` (fail loud) over the Reviewer's secondary "filter null `from_id` → defer" hint — see Design Deviations + the blocking Conflict in Delivery Findings. Dev must NOT filter null `from_id` to None in `surface_owner_for_entrance` or #1 stays red.

**Handoff:** To Dev (Inigo Montoya) for GREEN — wrap `resolve_surface_ascent` in `try/except SeamCrossingError → _unresolved`, add the symmetric surface-region-existence guard, fix the pyright `str | None` at `intent_router_pass.py:426`, and run the FULL server suite for AC4.

---
## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/game/seams/surface_ascent.py` (NEW) — `resolve_surface_ascent`: binds the PC back to the surface owner (`route.from_id`) via the per-PC `WorldStatePatch`; emits `movement.resolved` with `resolved_via=surface_ascent`, `seam_kind=deep_descent` (same bidirectional route), `edge_kind=surface_ascent`. Mirrors `resolve_deep_descent`; fails loud (`SeamCrossingError reason=no_surface_owner`) on a routeless owner.
- `sidequest/game/seams/registry.py` — added `surface_owner_for_entrance(cart)`: reverse lookup returning the route whose `to_id` is a registered seam kind (its `from_id` is the surface owner); returns None on zero/ambiguous owners.
- `sidequest/game/seams/__init__.py` — export `surface_owner_for_entrance`.
- `sidequest/agents/subsystems/movement.py` — new branch in the region-mode block: PC at `ENTRANCE_ID` + non-deeper intent → ascend via `resolve_surface_ascent`; no owner → defer (never invent).
- `sidequest/server/intent_router_pass.py` — `_build_state_summary` projection: at the entrance node (not a cartography region), list the surface ascent exit `{name: <surface region display>, kind: seam}` derived from `surface_owner_for_entrance`; emits the existing `intent_router.region_exits` span.
- `sidequest/agents/intent_router.py` — movement nudge clarified: a seam exit goes DOWN from the surface ("deeper") and UP from the entrance ("back"/"toward_exit") — honors the registry's directive to update the nudge for new seam geometry.

**Tests:** 31/31 passing GREEN (8 new + 23 existing 105-2 non-regression). Full serial server suite: **10716 passed, 0 failed, 1581 skipped** — blast radius (seam/movement/intent_router/dispatch) zero failures. The two xdist-parallel flakes (`test_102_5_wn_tool_narrator_wiring`, `test_reference_poi_projection`) pass in isolation and serially — pre-existing xdist-isolation noise, not this change.

**Quality gates:** `ruff check` clean (one import-order autofix applied); `ruff format --check` clean.

**Branch:** `feat/105-3-reverse-seam-ascent` (pushed to origin).

**ACs:** AC1 ✓ (entrance→surface ascent via per-PC patch, no improvisation), AC2 ✓ (`movement.resolved` `resolved_via=surface_ascent` `seam_kind=deep_descent` span), AC3 ✓ (`current_region_exits` lists the surface exit at the entrance), AC4 ✓ (full suite green, existing 105-2 + in-graph traversal intact).

**Handoff:** To Reviewer (Westley) for code review.

---
## Dev Assessment — Review Rework (green)

**Implementation Complete:** Yes — all three Reviewer findings fixed; the two new RED tests are GREEN.

**Files Changed (this rework):**
- `sidequest/agents/subsystems/movement.py` — finding #1 (HIGH): wrapped the ascent's `resolve_surface_ascent` call in `try/except SeamCrossingError → _unresolved`, mirroring the descent block, and threaded `cartography=cart` through. A malformed registered-kind route now fails loud via the `movement.unresolved` span (the OTEL lie-detector), never an uncaught raise and never a silent `region_mode_deferred`.
- `sidequest/game/seams/surface_ascent.py` — finding #3 (MEDIUM): added a region-existence guard symmetric to the descent's `entrance_id in graph.nodes` check — a `from_id` absent from `cartography.regions` raises `SeamCrossingError(dangling_surface_owner)` instead of binding the PC to a phantom region. Added the `cartography` parameter + `CartographyConfig` TYPE_CHECKING import.
- `sidequest/server/intent_router_pass.py` — finding #2 (HIGH): pyright fix — both branches of the seam-exit `name` are now `str` (`surface_id or _region_id`), and `_cart.regions.get(...)` is guarded so it never receives `None`.
- `sidequest/game/seams/registry.py` — **intentionally UNCHANGED.** Per TEA's blocking Conflict, `surface_owner_for_entrance` still returns the malformed route so the loud-fail channel (`movement.unresolved`) fires; NOT filtered to a silent defer. (See Design Deviations — rework.)

**Tests:** Ascent suite 8/8 GREEN (the 2 new rework tests pass). Full serial server suite: **10718 passed, 0 failed, 1581 skipped** (baseline 10716 + the 2 new tests) — verified by `testing-runner` (RUN_ID `105-3-dev-green`). No regressions.

**Quality gates:** `ruff check` clean; `ruff format --check` clean; **`pyright` 0 errors** on all three touched source files (the gap that let finding #2 slip RED/GREEN originally).

**Branch:** `feat/105-3-reverse-seam-ascent` (pushed — HEAD `d2d240f8`).

**Findings resolved:** #1 (uncaught raise → loud `movement.unresolved`) ✓; #2 (pyright `str | None`) ✓; #3 (phantom-region bind → existence guard) ✓.

**Handoff:** To Reviewer (Westley) for re-review.

---
## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 (pyright type error @ intent_router_pass.py:426) + tests GREEN 31/31, lint/format clean | confirmed 1, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — domain covered by Reviewer (see [EDGE] obs) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — domain covered by Reviewer (see [SILENT] obs) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — domain covered by Reviewer (see [TEST] obs) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — domain covered by Reviewer (see [DOC] obs) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — domain covered by Reviewer (see [TYPE] obs) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings — domain covered by Reviewer (see [SEC] obs) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — domain covered by Reviewer (see [SIMPLE] obs) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — domain covered by Reviewer (see [RULE] obs) |

**All received:** Yes (1 enabled subagent returned; 8 disabled via `workflow.reviewer_subagents`, domains covered directly by Reviewer)
**Total findings:** 2 confirmed blocking, 0 dismissed, 0 deferred

## Rule Compliance

Rules checked: `.pennyfarthing/gates/lang-review/python.md` (13 checks) + SOUL "No Silent Fallbacks" + CLAUDE.md OTEL Observability Principle + "No half-wired features". Enumerated against every changed function.

- **#1 silent exceptions** — `resolve_surface_ascent` raises `SeamCrossingError` (explicit, specific). VIOLATION at the *caller*: `movement.py` ascent branch does not catch it, unlike the symmetric descent block → the documented-recoverable error escapes uncaught and the `movement.unresolved` span never fires. (Blocking finding 1.)
- **#3 type annotations at boundaries** — `surface_owner_for_entrance`, `resolve_surface_ascent` fully annotated. VIOLATION: `intent_router_pass.py:426` constructs `dict[str, str | None]` against a `list[dict[str, str]]` boundary (pyright fail). (Blocking finding 2.)
- **#2 mutable defaults** — none introduced. COMPLIANT (kwargs are scalars/str).
- **#4 logging** — `resolve_surface_ascent` uses `logger.debug("...%s", ...)` lazy %-args, no f-string, no sensitive data. COMPLIANT.
- **#6 test quality** — 8 new tests assert concrete values + messages; 3 guards are negative cases. COMPLIANT. GAP: no test exercises the malformed-route (null from_id) ascent path — the exact case finding 1 crashes on. (See [TEST].)
- **#8 unsafe deserialization / #11 input validation** — no deserialization, eval, SQL, or HTML. N/A.
- **#10 import hygiene** — explicit imports, `surface_owner_for_entrance` added to `__all__`. COMPLIANT.
- **SOUL No Silent Fallbacks** — oz/absent-owner defers (no invented surface) COMPLIANT; null-from_id raises uncaught (wrong channel) VIOLATION (finding 1).
- **OTEL Principle** — happy-path ascent emits `movement.resolved`. VIOLATION on the error path: an uncaught exception emits no `movement.unresolved` span, blinding the GM panel (finding 1).
- **No half-wired** — the intent_router nudge WAS updated for the new ascent geometry per the registry directive. COMPLIANT.

## Reviewer Observations

1. `[HIGH][SILENT][EDGE][RULE]` Uncaught `SeamCrossingError` on the ascent path — `movement.py` ascent branch calls `resolve_surface_ascent(...)` with NO `try/except`, while the symmetric descent block (movement.py ~163-183) wraps `get_seam_resolver(...)(...)` in `try/except SeamCrossingError → _unresolved`. `Route.from_id` is `str | None = None` (world.py:232) with NO validator enforcement (grep confirms zero route-field validation), and `surface_owner_for_entrance` returns a single registered-kind route even when its `from_id` is None (it only de-dupes distinct from_ids; `{None}` has len 1). Result: a homebrew/malformed `deep_descent` route lacking `from_id` → `resolve_surface_ascent` raises `no_surface_owner` uncaught out of `run_movement_dispatch`, and the contract-mandated `movement.unresolved` span never fires (base.py: span emission is the catcher's obligation). Fix: wrap in `try/except SeamCrossingError → _unresolved(reason=err.reason, surface=err.surface, ...)` AND filter null `from_id` in `surface_owner_for_entrance`.
2. `[HIGH][TYPE]` pyright failure at `intent_router_pass.py:426` — `owner.name` is `str | None`; the appended dict is `dict[str, str | None]`, violating `region_exits: list[dict[str, str]]`. `just server-check` does not run pyright, so it slipped RED/GREEN. Fix: `"name": owner.name or ascent.from_id` (str in both branches).
3. `[MEDIUM][EDGE]` `resolve_surface_ascent` binds the PC to `route.from_id` WITHOUT verifying it resolves to a real cartography region. The descent verifies `entrance_id in graph.nodes` and fails loud otherwise; the ascent has no equivalent dangling-region guard, so a route pointing at a non-existent surface id strands the PC in a phantom region. Recommend validating the resolved region exists (fold into finding 1's fix).
4. `[LOW][SIMPLE]` `direction != "deeper"` is intentionally broad (Dev deviation). Verified safe for the current depth-rooted single-entrance dungeon: in-graph descent from the entrance is `direction="deeper"` and defers correctly (`test_deeper_from_entrance_does_not_ascend`). Noted as a future risk only for a hypothetical multi-way junction entrance.
5. `[VERIFIED][DOC]` Comments/docstrings accurate — `surface_ascent.py` module docstring and the movement.py "Story 105-3" banner correctly describe the bidirectional-route model and the no-invent fallthrough; no stale/misleading text. Evidence: surface_ascent.py:1-11, movement.py ascent-branch comment.
6. `[VERIFIED][SEC]` No security surface — no auth, user-supplied paths, secrets, SQL, or deserialization in the diff. Region ids flow from authored cartography, not untrusted input. N/A.
7. `[VERIFIED]` AC2 span contract correct — `resolve_surface_ascent` emits `movement.resolved` with `seam_kind="deep_descent"` (route.to_id, unchanged), `resolved_via="surface_ascent"`, `edge_kind="surface_ascent"` — matches the story, not the contradicted scout guess. Evidence: surface_ascent.py:55-69; `test_entrance_node_ascends_to_surface` asserts both attrs.
8. `[VERIFIED]` Projection refactor is behavior-preserving for surface regions — `region_exits` lifted out of the `if _region is not None` block; the emit-once block now serves both branches. Existing `test_intent_router_region_exits.py` (6 tests, incl. adjacency + seam + split-party omit) stays green. Evidence: preflight 31/31.

## Devil's Advocate

Assume this ascent is broken. The most damning path: a homebrew author — exactly the audience CLAUDE.md says the content surface must serve (Jade writes packs now) — authors a `deep_descent` seam route and, copying an adjacency route or fat-fingering YAML, omits `from_id`. The pack loads: `Route.from_id` is `str | None = None`, and nothing in `sidequest/genre/` validates route fields (I grepped — zero hits). The world plays fine on the surface and on descent (the descent uses `seam_route_for`, which requires `route.from_id == region_id` and so silently ignores a null-from_id route). The bomb is buried until a player at the bottom types "head back up" — `surface_owner_for_entrance` happily returns the null-from_id route (its distinct-from_id set is `{None}`, length 1), `resolve_surface_ascent` raises `SeamCrossingError(no_surface_owner)`, and because the ascent branch — unlike its descent twin — has no `try/except`, the exception unwinds out of `run_movement_dispatch` into the dispatch bank. The player isn't told the truth via an honest `movement.unresolved` surface; the GM panel sees no failure span; the turn dies with a stack trace. That is precisely the "convincing-narration-with-no-mechanical-backing" failure the OTEL principle exists to prevent, inverted: a real mechanical failure with no observability. A confused author would have no signal pointing at the missing `from_id`. Second angle: even with a present `from_id`, nothing checks it names a real region — point it at a typo'd id and the PC is bound to a region that doesn't exist, a silent corruption the descent path guards against (`entrance_id in graph.nodes`) but the ascent does not. Third angle — the stressed/odd-config case: a world with two descent points (two routes to `deep_descent` from different surfaces) returns None (ambiguous) and the party is simply stranded again, the very bug this story exists to kill, now merely relocated. None of these are exotic; the first is one missing YAML key away and ships an uncaught server exception. The happy path is correct and well-tested, but the error geometry is asymmetric with the descent it claims to mirror, and that asymmetry is the flaw.

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | Uncaught `SeamCrossingError` on ascent — no `try/except`, unlike the descent block; reachable via a `deep_descent` route with null `from_id` (unvalidated). Skips the `movement.unresolved` span (OTEL + base.py catcher-contract violation). | `sidequest/agents/subsystems/movement.py` (ascent branch) + `sidequest/game/seams/registry.py` (`surface_owner_for_entrance`) | Wrap `resolve_surface_ascent` in `try/except SeamCrossingError → _unresolved(reason=err.reason, surface=err.surface, …)`; filter null `from_id` in `surface_owner_for_entrance` (skip/ambiguity, not return). |
| [HIGH] | pyright failure: `owner.name` (`str \| None`) appended to `list[dict[str, str]]`. | `sidequest/server/intent_router_pass.py:426` | `"name": owner.name or ascent.from_id` |
| [MEDIUM] | Ascent binds to `route.from_id` without verifying it's a real cartography region (descent guards its target; ascent does not). | `sidequest/game/seams/surface_ascent.py` / `movement.py` | Validate the resolved surface id exists; else `_unresolved` (fold into HIGH fix). |

**Data flow traced:** player movement intent → `run_movement_dispatch` (region-mode block) → PC at `ENTRANCE_ID` + non-deeper → `surface_owner_for_entrance(cart)` → `resolve_surface_ascent` → `apply_world_patch(pc_region)` + `movement.resolved` span. SAFE on the happy path (verified by 8 tests); UNSAFE on the null/dangling-`from_id` edge (HIGH finding) where the error path lacks the descent's recoverable-failure handling.

**Pattern observed:** the descent door is the correct template (try/except SeamCrossingError → _unresolved at movement.py ~163-183); the ascent door diverged from it. Bring the ascent into symmetry with the descent.

**Error handling:** happy path correct; the recoverable-error path is the defect — must route through `_unresolved` (honest surface + `movement.unresolved` span), never an uncaught raise.

**Tags present:** [EDGE] [SILENT] [TEST] [DOC] [TYPE] [SEC] [SIMPLE] [RULE]

**Handoff:** Back to TEA (Fezzik) for a failing test on the malformed-route ascent path (null `from_id` → graceful `_unresolved` + `movement.unresolved` span, NOT an uncaught raise), then Dev wraps the `try/except` + fixes the pyright type and the dangling-region guard. (red rework — the dominant finding is a testable logic bug.)
---
## Subagent Results — Re-review (Round-Trip 1)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 (pre-existing ruff I001 outside touch set) + tests GREEN 23/23, pyright 0 errors, format clean, tree clean, 0 code smells | confirmed 0 blocking, dismissed 1 (pre-existing, out-of-scope), deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — domain covered by Reviewer (see [EDGE] obs) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — domain covered by Reviewer (see [SILENT] obs) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — domain covered by Reviewer (see [TEST] obs) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — domain covered by Reviewer (see [DOC] obs) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — domain covered by Reviewer (see [TYPE] obs) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings — domain covered by Reviewer (see [SEC] obs) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — domain covered by Reviewer (see [SIMPLE] obs) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — domain covered by Reviewer (see [RULE] obs) |

**All received:** Yes (1 enabled subagent returned; 8 disabled via `workflow.reviewer_subagents`, domains covered directly by Reviewer)
**Total findings:** 0 confirmed blocking, 1 dismissed (pre-existing, out-of-scope), 0 deferred

## Rule Compliance — Re-review

Re-checked the three rejected findings against `.pennyfarthing/gates/lang-review/python.md` + SOUL "No Silent Fallbacks" + CLAUDE.md OTEL Principle, enumerated over the rework diff.

- **#1 silent exceptions / SOUL No-Silent-Fallbacks / OTEL** — `movement.py` ascent branch now wraps `resolve_surface_ascent` in `try/except SeamCrossingError → _unresolved(reason, surface)`, exactly mirroring the descent block (movement.py ~169-189). A malformed registered-kind route fails LOUD through the `movement.unresolved` span — never an uncaught raise, never a silent `region_mode_deferred`. RESOLVED (was the dominant HIGH).
- **#3 type annotations at boundaries** — `intent_router_pass.py` seam-exit dict is now `dict[str, str]`: both name branches resolve to `str` (`surface_id or _region_id`), and `_cart.regions.get(...)` is guarded against a `None` key. `uv run pyright` → **0 errors** on all three touched files. RESOLVED (was HIGH; the pyright gap that hid it is logged as a non-blocking Improvement).
- **descent/ascent symmetry (region-existence guard)** — `surface_ascent.py` adds `if surface_id not in regions: raise SeamCrossingError(dangling_surface_owner)`, symmetric to the descent's `entrance_id in graph.nodes`; the PC is never bound to a phantom region. RESOLVED (was MEDIUM).
- **#6 test quality** — the two new RED→GREEN tests assert concrete values + the `movement.unresolved` span (and absence of `movement.resolved`); the malformed-route coverage gap the original review flagged is now closed. COMPLIANT.
- **No half-wired** — single caller (`movement.py`) passes `cartography=cart`; resolver guards membership. COMPLIANT.

## Devil's Advocate — Re-review

Assume the rework only *looks* fixed. The strongest attack: did the `try/except` actually change the observable outcome, or does some other path still escape? Traced every raise site in `resolve_surface_ascent` — there are exactly two (`no_surface_owner` for a null `from_id`; `dangling_surface_owner` for an unmapped region), both `SeamCrossingError`, both inside the `try`. The patch/span emission below them is only reached after both guards pass, and on a verified-real region. So no `SeamCrossingError` can now leave `run_movement_dispatch` on the ascent path — and the two RED tests, which previously raised uncaught / bound a phantom region, now assert exactly one `movement.unresolved` span and the PC unmoved. Second attack: did the fix trade the crash for a *silent* failure (the very thing No-Silent-Fallbacks forbids)? No — the chosen channel is `movement.unresolved` (ERROR span + honest narrator surface), not `region_mode_deferred`. Dev pointedly did NOT filter `surface_owner_for_entrance` (which would have silently deferred), honoring the OTEL lie-detector. This is *more* correct than my original fix-text, which contained that very tension. Third attack: a residual phantom-exit hint in the AC3 projection for a malformed route — real but cosmetic, gated behind a malformed-pack-only path, and backstopped by the same fail-loud dispatch; logged LOW, non-blocking. Fourth: regression blast radius — full serial suite 10718 passed / 0 failed (baseline 10716 + 2 new), pyright clean, the prior-approved happy path (8 ascent tests) intact. I cannot manufacture a blocking failure. The error geometry is now symmetric with the descent it mirrors. Approve.

## Reviewer Assessment — Re-review (Round-Trip 1)

**Verdict:** APPROVED

All three findings from the prior rejection are resolved and verified:
- **[HIGH][SILENT][EDGE] finding #1** — uncaught `SeamCrossingError` → now `try/except → _unresolved` (`movement.unresolved` span). Fixed at `movement.py` ascent branch. Verified by `test_null_from_id_seam_fails_loud_not_raises` (GREEN) + my raise-site trace.
- **[HIGH][TYPE] finding #2** — pyright `str | None` at `intent_router_pass.py:426` → both branches now `str`; `uv run pyright` 0 errors. Verified by preflight + my own run.
- **[MEDIUM][EDGE] finding #3** — missing region-existence guard → `surface_ascent.py` now raises `dangling_surface_owner` for an unmapped `from_id`. Verified by `test_dangling_from_id_does_not_bind_phantom_region` (GREEN).

**Data flow traced:** entrance-node departure intent → `surface_owner_for_entrance(cart)` (still returns malformed routes, by design) → `resolve_surface_ascent(cartography=cart)` → null `from_id` ⇒ `no_surface_owner`, unmapped `from_id` ⇒ `dangling_surface_owner`, else bind + `movement.resolved`. Both raises are caught in `movement.py` → `_unresolved` → `movement.unresolved` span. SAFE on happy path AND on the malformed-route edges that were UNSAFE before.

**Pattern observed:** the ascent door is now symmetric with the descent template (try/except SeamCrossingError → _unresolved) — `movement.py` ascent branch + `surface_ascent.py` guard. The original divergence is corrected.

**Error handling:** every recoverable seam fault routes through `_unresolved` (honest surface + ERROR span); no uncaught raise, no silent defer, no phantom-region bind.

**Deviation audit (rework):**
- **Dev: malformed seam fails loud via try/except, NOT by filtering `surface_owner_for_entrance`** → ✓ ACCEPTED by Reviewer: this overrides my original fix-text and is the better resolution — a registered-kind route IS a seam, so a malformed one must be loud (`movement.unresolved`), not silently deferred like a genuinely seam-less world. Aligns with the OTEL principle + No-Silent-Fallbacks.
- **Dev: pyright fix uses `surface_id or _region_id`, not the literal `owner.name or ascent.from_id`** → ✓ ACCEPTED by Reviewer: my literal suggestion was still `str | None`-typed and would not have cleared pyright; the implemented form is correct (0 errors).
- **TEA: malformed-seam ascent pinned to `movement.unresolved` (fail loud), not a silent defer** → ✓ ACCEPTED by Reviewer: the test contract correctly resolved the two-hint tension in my original fix-text toward the principle-grounded loud channel.

**Quality gates:** ruff clean (1 finding pre-existing & out-of-scope), format clean, pyright 0 errors, full suite 10718 passed / 0 failed / 1581 skipped, working tree clean at `d2d240f8`.

**Tags present:** [EDGE] [SILENT] [TEST] [DOC] [TYPE] [SEC] [SIMPLE] [RULE]

**Handoff:** To SM (Vizzini) for finish-story — create + merge the single server PR, archive the session.