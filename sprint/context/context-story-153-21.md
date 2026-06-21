# Story 153-21 Context

## Title
[DUNGEON-SEAM-CROSSING-STICKY] descend-the-rope must traverse the the_dropmouth->deep_descent seam into the procedural entrance node, not latch the narrator title back to the static cartography region

## Metadata
- **Story ID:** 153-21
- **Type:** bug
- **Points:** 5
- **Priority:** p1
- **Workflow:** tdd
- **Repo:** server
- **Epic:** 153 — Playtest follow-ups — open findings from the 2026-06-20/21 full-stack /sq-playtest sweep

## Problem Statement

In `beneath_sunden` (caverns_and_claudes, region-mode + procedural-dungeon hybrid),
a normal one-descent player is told they are "in the first chamber" but is
mechanically still parked on the **surface** cartography region. The generated
ADR-106 dungeon never attaches.

Verbatim finding (2026-06-20/21 sweep):

> Cartography defines route 'Down the Rope' `from_id: the_dropmouth` →
> `to_id: deep_descent` (a SEAM SENTINEL the ADR-106 materializer maps to the
> procedural dungeon root `entrance`, room `rooms/entrance.yaml` "Under the
> Rope"). Turn-1 action "descend the shaft to the first chamber, step off the
> rope into that chamber" → narrator titles the scene "The Dropmouth — First
> Chamber", and log
> `region.entry_resolved_to_cartography entry='The Dropmouth — First Chamber'
> region_id='the_dropmouth'` — the resolver string-matches "Dropmouth" and parks
> the PC in the static cartography region, never crossing the `deep_descent`
> seam (`dungeon.map_emitted region=the_dropmouth discovered=0/7`). Only a 2nd,
> more insistent descent finally advances `current_region='entrance'` and
> `discovered=1/10`.

Impact: the player believes they have entered the dungeon; the engine has not
moved them. Combat, room graph, fog-of-war, and look-ahead materialization all
remain inert until a second, more forceful descent — a SOUL.md "Illusionism"
failure a career GM will catch immediately.

## Root Cause Direction

The seam-crossing path **already exists** (movement.py hybrid-descent block and
the narration_apply seam-recovery `elif`) — the bug is an ordering/precedence
defect, not a missing subsystem. **Extend the existing seam path; do not build a
new one.**

In `narration_apply.py::_apply_narration_result_to_snapshot`, the narrator scene
title flows through `_resolve_heading_to_cartography(...)` →
`resolve_known_region_id(...)`. That resolver canonicalizes the heading's
**leading place segment** ("The Dropmouth — First Chamber" → `"the_dropmouth"`
via `leading_place_segment`) and matches it against the cartography region ids
(`region_validation.py:172`). Because `the_dropmouth` IS a declared region, the
match succeeds and `known_region_id` is non-None.

That non-None match drives the code into the `if known_region_id is not None:`
branch (narration_apply.py ~line 4291), which latches `current_region` /
`pc_regions[player]` to `the_dropmouth` and logs
`region.entry_resolved_to_cartography` (~line 4374) — the static-region latch.
The seam-crossing recovery lives only in the **sibling** `elif
_is_region_mode_world:` branch (~line 4380), which fires ONLY when the heading
does **not** resolve to a known region. So a descent whose title still names the
seam-owning region ("The Dropmouth — ...") is captured by the latch BEFORE the
seam route can fire.

The seam machinery the fix must reach is intact and proven:
`movement.py::run_movement_dispatch` already has the hybrid descent block
(`seam_route_for(cart, from_region)` + `get_seam_resolver(...)` →
`resolve_deep_descent`) that binds the PC onto the `entrance` node and fires
`movement.resolved`. The fix should make a descent heading that names the
seam-owning region (and whose action crosses `deep_descent`) take the
**seam-crossing** path rather than the static `region.entry_resolved_to_cartography`
latch — i.e. when `known_region_id` equals a region that `seam_route_for` says
owns a registered seam route AND the move semantics are a descent, prefer the
crossing over the static-region re-anchor.

## Acceptance Criteria

1. **One descent crosses the seam.** A turn-1 descent action in `beneath_sunden`
   whose narrator title is "The Dropmouth — First Chamber" (or any
   leading-segment match on `the_dropmouth`) binds the PC onto the procedural
   `entrance` node: after apply, `snapshot.region_for(perspective=player) ==
   "entrance"` and `current_region == "entrance"` (NOT `the_dropmouth`).

2. **The static-region latch no longer wins on a descent heading.** When the
   PC's current region OWNS a registered seam route (`seam_route_for(cart,
   from_region) is not None`) and the incoming heading resolves back to that same
   seam-owning region, the engine performs the `deep_descent` crossing instead of
   logging `region.entry_resolved_to_cartography` and parking on the static
   region. A non-descent re-title of the same region (e.g. a POI sub-title that is
   genuinely "still at the Dropmouth") must NOT spuriously cross — it stays put.

3. **Scene re-anchors to the authored entrance room.** After the crossing,
   `result.location` is re-anchored to the authored entrance room name ("Under
   the Rope", via `_entrance_room_name`), and the location ledger is rewritten so
   ledger and scene agree (reuse the existing `_reanchor_location_ledger` path).

4. **discovered counter advances on the first descent.** `discovered_regions`
   reflects entry into the deep on the first descent (`discovered=1/N`), not after
   a forced second descent.

5. **Fail loud on an unresolvable crossing.** If the crossing cannot complete
   (no dungeon store, no entrance node), the patch is REJECTED loudly via the
   existing `region_entry_rejected_span(reason="seam_crossing_unresolvable")`
   path and the PC stays put honestly — never silently accept the confabulated
   "first chamber" scene (No Silent Fallbacks).

6. **OTEL / watcher spans (every subsystem decision emits a span).** The crossing
   emits `movement.resolved` (`movement_resolved_span`,
   `sidequest/telemetry/spans/movement.py`) with `resolved_via` indicating the
   narration-driven seam crossing, and the static-latch
   `region.entry_resolved_to_cartography` is NOT emitted for the crossed descent.
   The `region_current_advanced` watcher publish fires with
   `new_region="entrance"`. The GM panel can distinguish "the engine crossed the
   seam" from "the narrator just retitled the scene."

7. **Wiring / integration test proves reachability from a real play path.** Add
   a behavior test that drives a `beneath_sunden` narration result with the
   sticky "The Dropmouth — First Chamber" heading through the real
   `_apply_narration_result_to_snapshot` (extend the existing
   `tests/server/test_narration_seam_recovery.py` `hybrid_apply_kit` fixtures) and
   asserts the PC lands on `entrance` after ONE descent, with the
   `movement.resolved` span captured. No source-text grep assertions (CLAUDE.md
   "No Source-Text Wiring Tests").

## Key Code Areas to Investigate

**The static-region latch vs. the seam-recovery branch (the bug site):**
- `sidequest/server/narration_apply.py::_apply_narration_result_to_snapshot`
  (function starts ~line 3907) — the `if result.location:` location-update block:
  - `if known_region_id is not None:` branch (~line 4291) — sets
    `current_region`/`pc_regions` and logs `region.current_region_advanced`
    (~line 4312) + `region.entry_resolved_to_cartography` (~line 4374). **This is
    the latch that wins too early.**
  - `elif _is_region_mode_world:` seam-recovery branch (~line 4380) — calls
    `seam_route_for(_region_cart, _pc_region)` then
    `get_seam_resolver(str(_seam_route.to_id))(...)`, re-anchors via
    `_entrance_room_name` + `_reanchor_location_ledger`, and emits
    `region_entry_rejected_span(reason="seam_crossing_unresolvable")` on failure.
    **This is the path the descent must reach.**
- `sidequest/server/narration_apply.py::_resolve_heading_to_cartography`
  (line 3671) — produces `known_region_id` from the heading.
- `sidequest/server/narration_apply.py` location-drift repair (~lines 4000-4039):
  `_extract_leading_bold_title` + `location_drift_repaired_span` promote the bold
  title into `result.location` when the narrator leaves it blank — the upstream
  that feeds the latch.

**The resolver that string-matches the title back to the region:**
- `sidequest/game/region_validation.py::resolve_known_region_id` (line 172) —
  matches full form then `leading_place_segment`; this is why "The Dropmouth —
  First Chamber" resolves to `the_dropmouth`.

**The seam machinery the fix must reuse (already wired in movement.py):**
- `sidequest/agents/subsystems/movement.py::run_movement_dispatch` — the hybrid
  region-mode descent block (~lines 169-211): `seam_route_for(cart, from_region)`
  + `get_seam_resolver(...)` → `resolve_deep_descent`. The room-graph surface→deep
  handoff (~lines 340-392) is the same resolver via a synthetic Route.
- `sidequest/game/seams/registry.py` — `seam_route_for` (line 34),
  `get_seam_resolver` (line 25), `surface_owner_for_entrance` (line 49); the
  `_REGISTRY` maps `"deep_descent" → resolve_deep_descent`.
- `sidequest/game/seams/deep_descent.py::resolve_deep_descent` — binds the PC onto
  `_ENTRANCE_ID` and fires the per-PC patch + movement span.
- `sidequest/dungeon/seed_bootstrap.py` — `ENTRANCE_ID` (the `entrance` anchor).
- `sidequest/server/narration_apply.py::_entrance_room_name` (line 168) +
  `_reanchor_location_ledger` (line 210) — scene/ledger re-anchor helpers.

**Cartography source (the route under test):**
- `sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden/cartography.yaml`
  — `navigation_mode: region`, `starting_region: ropefoot`; region `the_dropmouth`;
  `routes: [{name: "Down the Rope", from_id: the_dropmouth, to_id: deep_descent}]`.

**Existing tests to extend (wiring + behavior):**
- `tests/server/test_narration_seam_recovery.py` — `hybrid_apply_kit` /
  `hybrid_apply_kit_empty_store` fixtures; `test_unresolved_heading_on_seam_region_recovers_crossing`,
  `test_dead_store_rejects_patch_loud`, `test_drift_strip_on_seam_region`. Add the
  sticky-resolved-heading case here.
- `tests/agents/subsystems/test_movement_seam_crossing.py`,
  `tests/game/test_seam_deep_descent.py`, `tests/game/test_seam_registry.py` —
  seam-resolver unit coverage to mirror.

## Technical Notes

- **ADR-106** (Runtime Procedural Jaquaysed Megadungeon): `deep_descent` is the
  documented static→procedural SEAM SENTINEL; the materializer roots its Stage-1
  `entrance` expansion there. No authored region carries the `deep_descent` id by
  design — the deep is generated at runtime.
- **ADR-055** (Room Graph Navigation): the PC standing inside the dungeon is on a
  graph node (`entrance` / `expNNN.rN`), not a cartography region.
- **ADR-105 / Story 105-2** (broadcast-layer perception firewall / hybrid seam
  recovery): the `elif _is_region_mode_world:` seam-recovery branch exists
  *because* a region-mode hybrid world's seam crossing can arrive as a narrator
  heading; this story closes the precedence gap that 105-2's recovery left open
  when the heading still resolves to the seam-owning region.
- **OTEL Observability Principle** (CLAUDE.md): the crossing decision must emit a
  watcher span so the GM panel can tell an engine crossing from a narrator retitle
  — that span is the lie detector for this exact Illusionism failure.
- **Reuse-first / Don't Reinvent** (CLAUDE.md): movement.py already owns the
  descent-bind path (`surface_owner_for_entrance`, `deep_descent`, `_ENTRANCE_ID`,
  `dungeon_store.load_map`) and narration_apply already owns the seam-recovery
  branch. The fix is precedence/routing — make the resolved-heading descent reach
  the seam crossing — not a new movement mechanism.

## Story Scope

**In scope:**
- The precedence fix in `narration_apply.py` so a descent whose heading resolves
  to a seam-owning region (`the_dropmouth`) crosses the `deep_descent` seam to the
  `entrance` node instead of latching the static region.
- Scene/ledger re-anchor to the authored entrance room on a successful crossing
  (reuse `_entrance_room_name` + `_reanchor_location_ledger`).
- Fail-loud rejection on an unresolvable crossing (reuse the existing rejected
  span path).
- OTEL span coverage + a wiring/behavior test through the real apply path.

**Out of scope:**
- The in-dungeon descriptor→edge resolver and identical-neighbor dedup — that is
  Story 153-22 (`movement.py::_resolve`).
- Multi-descent / multi-seam cartographies (`surface_owner_for_entrance` ambiguity
  case) — a documented follow-up.
- New seam kinds (ascent geometry, lateral crossings) beyond `deep_descent`.
- The intent-router classification of the descent action (the router already
  emits a movement dispatch; this story fixes the narration-apply latch that
  shadows it).

---
_Enriched from the 2026-06-20/21 /sq-playtest finding; code-area claims verified
against `sidequest-server` source on 2026-06-21._
