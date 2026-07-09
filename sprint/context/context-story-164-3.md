# Story 164-3 Context

## Title
RISKY: router site targets + movement-ladder cutover + Sünden frontier migration (plan tasks 5–6)

## Metadata
- **Story ID:** 164-3
- **Type:** refactor
- **Points:** 5
- **Priority:** p1
- **Workflow:** spdd (phased: setup → red → green → review → finish)
- **Repo:** server, content
- **Epic:** 164 — Mapping Track B — Site system (seam contract, archetypes)
- **Branches:** `feat/164-3-router-sites-movement-cutover-sunden-frontier` (both server + content, off `develop`)

## Source of Truth
- **Plan:** `docs/superpowers/plans/2026-07-08-mapping-track-b-site-system.md` — **Task 5** (lines 885–950) and **Task 6** (lines 953–1085). Read these verbatim; they carry the exact file paths, line refs, and code shapes.
- **Spec:** `docs/superpowers/specs/2026-07-08-three-tier-mapping-design.md` (§1/§3/§4).
- **Depends on (already merged to `develop`):** 164-1 (`SiteRegistry` + `CartographyConfig.sites` + per-site storage keying, PR #1122) and 164-2 (symmetric `enter_site`/`exit_site` resolvers + `site.*` spans + Sünden characterization guard, PR #1123). The `sidequest/game/sites/enter_site.py` + `exit_site.py` resolvers this story wires are live on `develop`.

## Problem
`movement.py` currently resolves seam crossings via a five-rung inlined ladder
(`:386`–`:627`) with the enter/exit asymmetry 164-2 documented (`surface_ascent`
called directly at `movement.py:504`). 164-1/164-2 built the `SiteRegistry` and the
symmetric `enter_site`/`exit_site` resolvers **additively** — nothing calls them yet.
This story cuts the movement dispatch over to them and migrates Sünden's deep to be
the first `frontier` site, structurally fixing 158-36. **This is the riskiest task in
Track B B1.** Task 3's characterization tests (from 164-2) are the safety net.

## Technical Approach

### Task 5 — Router site targets (ADDITIVE, do first)
Teach the intent router to emit `enter_site`/`exit_site` and surface enterable sites.
Movement dispatch still ignores `action` until Task 6; the `direction`/`exit_descriptor`
in-scene vocabulary stays.
- Modify `sidequest/agents/intent_router.py` — movement bullet in `_SYSTEM_PROMPT`
  (`:192`–`:224`); replace the `direction`-only schema + hardcoded "seam goes DOWN"
  guidance with the two-shape site-target guidance (enter_site/exit_site vs in-scene nav).
- Modify `sidequest/server/intent_router_pass.py` — `_build_state_summary`
  (`:590`–`:626`) to add `current_sites: [{"site_id","name","archetype"}]` from
  `SiteRegistry.sites_for_node(region_id)`. Additive — keep `current_region_exits`/seam
  logic intact.
- New test: `tests/server/test_intent_router_sites_summary.py` (drive `_build_state_summary`
  with a Sünden-shaped pack declaring a frontier site; assert `current_sites` appears).

### Task 6 — RISKY CUTOVER (movement ladder → SiteRegistry × resolvers + Sünden frontier)
- Modify `sidequest/agents/subsystems/movement.py` — replace the region-mode seam rungs
  (`:386`–`:538`) with two site-target branches placed BEFORE the region-mode lateral
  block (`:554`). New dispatch order: (1) `exit_site` if PC inside a site; (2) `enter_site`
  from a world node; (3) existing lateral cartography travel; (4) `_defer_region_mode`;
  (5) §Q1 in-dungeon navigator (`:742`+, UNCHANGED). `resolved_via` becomes
  `"site_enter"`/`"site_exit"`.
- Modify `sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden/cartography.yaml`
  — add a `sites:` block after the `routes:` block declaring the frontier site:
  ```yaml
  sites:
    - site_id: frontier
      name: "The Deep"
      archetype: megadungeon
      attached_to: the_dropmouth
      extent: frontier
  ```
  **Keep the existing `deep_descent` route in place** (inert once movement stops reading it;
  a follow-up removes it — lowest risk).
- **Frontier-legacy id decision:** Sünden's frontier site keeps `site_id="frontier"` and
  storage uses the Task 2 default `site_id="frontier"`, but its NODE ids stay
  `entrance`/`expNNN.rN` for B1 (storage key, not node id, provides isolation). Full node-id
  namespacing (`frontier:entrance`) is a B2/B4 follow-up — NOT required for correctness.
- Membership detection for the un-namespaced frontier nodes uses
  `is_procedural_region_id` (`seed_bootstrap.py:45-48`) + `DEFAULT_SITE_ID` (`game/pg/dungeon.py`,
  = `"frontier"`). This shim is Sünden-legacy-specific by design and dies with the B4 node-id
  namespacing follow-up.

## Carryover — three findings 164-2 explicitly left for THIS story
(from `sprint/archive/164-2-session.md` Delivery Findings — treat as required work, not optional.)

1. **RETARGET the missing-entrance test (TEA).** Task 4's `resolve_enter_site` raises
   `SeamCrossingError(reason="no_site_entrance")` when the entrance node is absent, pinned by
   `test_enter_site_missing_entrance_node_raises` in
   `tests/game/sites/test_site_resolvers.py`. Task 6's migration decision REFINES
   `resolve_enter_site` to **prefer `graph.entrance_id` when `site.entrance_node_id not in
   graph.nodes`** (the Sünden frontier-legacy case, where the node is `entrance`, not
   `frontier:entrance`) — a **loud, single fallback** that is correct for frontier-legacy and
   harmless for bounded sites. This is NOT a contradiction of 164-2's contract; it is the
   planned refinement. Retarget the test accordingly (`enter_site.py` + `test_site_resolvers.py`).

2. **WIRE IT (Dev).** The site resolvers, `site_enter_unresolved_span`, and `enter_site`'s
   `direction`/`exit_descriptor` params are additive-ahead-of-consumer — no production caller
   yet. Task 6 must: **(a)** wire the movement dispatch to call the resolvers by kind;
   **(b)** emit `site_enter_unresolved_span` from the movement catcher on an unresolved enter
   (per the `SeamCrossingError` catcher-owns-the-failure-span contract); **(c)** stamp the
   player's coarse intent (`intent.direction`/`intent.exit_descriptor`) on the site spans as
   `movement.resolved` does — the site spans currently omit it. Affects `movement.py`.

3. **(Dormant, watch only)** `seam_route_for`/`seam_route_via_adjacency`/`surface_owner_for_entrance`
   (`game/seams/registry.py`) test `route.to_id in _REGISTRY` WITHOUT calling
   `_ensure_site_resolvers()`. Task 6 dispatches site kinds **by kind via `SiteRegistry`**,
   never via `Route.to_id`, so this stays dormant. Only if any lookup ever routes site kinds
   through `to_id` matching must `_ensure_site_resolvers()` be called first.

## Scope Fences
- **OUT OF SCOPE — bounded materialization (Tasks 11/12).** For B1, guard the bounded path:
  if `site.extent == "bounded"`, return `_unresolved(reason="bounded_site_pending",
  surface="That door isn't ready yet.")`. Sünden is `frontier`, so B1's live path never hits
  this. Do NOT implement `_ensure_bounded_site_materialized` here.
- **OUT OF SCOPE — §Q1 step-2b room-graph descent** (`movement.py:667`–`:740`, `resolve_deep_descent`):
  leave AS-IS (dead for Sünden post-migration but harmless; a follow-up removes `deep_descent`).
- **OUT OF SCOPE — DUNGEON_MAP→SITE_MAP protocol cutover & scene context** — those are Task 7/8
  (story 164-4). Do not touch protocol map emission here.
- **DO NOT balance native mechanics against anything.** This is a structural seam refactor, not
  a rules change (SOUL: Bind the Ruleset, Don't Balance It — not directly at issue here, but the
  cutover must preserve observable outcomes, not "improve" them).

## Acceptance Criteria (TEA to finalize in RED)
1. **Task 5 additive:** `_build_state_summary` surfaces `current_sites` for a node with an
   enterable site; existing `current_region_exits`/seam output unchanged. Router `_SYSTEM_PROMPT`
   movement bullet emits the enter_site/exit_site vs in-scene-nav two-shape schema. New test
   `test_intent_router_sites_summary.py` passes and includes a wiring/reachability assertion.
2. **Task 6 behavioral contract preserved:** the Sünden characterization suite
   (`test_movement_sunden_characterization.py`) passes with the **same `to_region`** assertions
   and **new `resolved_via`** values (`site_enter`/`site_exit` replacing
   `surface_descent`/`surface_ascent`). Full movement suite green (`test_movement*.py`).
3. **Wiring:** movement dispatch resolves `action=="enter_site"`/`"exit_site"` via the registry;
   `site_enter_unresolved_span` fires from the movement catcher on unresolved enter; site spans
   carry `intent.direction`/`intent.exit_descriptor` and reach `turn_telemetry` via `publish_event`.
4. **Frontier-legacy fallback:** `resolve_enter_site` prefers `graph.entrance_id` when the
   declared entrance node is absent (loud single fallback); `test_enter_site_missing_entrance_node_raises`
   retargeted to the new contract.
5. **End-to-end (load-bearing):** `just playtest-scenario sunden_descend_trace` stays green —
   party crosses into the deep and navigates; expected spans `movement.resolved
   onward_ring_drained=True`, no `movement.unresolved`. Unit tests alone are NOT sufficient
   sign-off for the cutover.
6. **Content `sites:` block** added to `beneath_sunden/cartography.yaml`; `deep_descent` route
   kept in place (inert). Content change commits on the content branch; server on the server branch.
7. Lint/format clean on all touched server + content files.

## OTEL / Observability Note
Per project doctrine, every site/seam span must reach `turn_telemetry` via `publish_event`
(mirror pattern, `telemetry/spans/movement.py:151`), NOT `Span.open` alone. Task 6 must also
stamp coarse intent on the site spans (carryover finding #2c) so the GM panel can verify the
site path is engaged rather than improvised.

---
_Authored by SM (Vizzini) from the Track B plan (Tasks 5–6) + 164-2 Delivery Findings carryover._
