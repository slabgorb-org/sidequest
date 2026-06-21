# Story 157-3 Context

## Title
[ENGINE] NPC walk-on origin-stamp + authored-cast staging on region entry (Seam 2)

## Metadata
- **Story ID:** 157-3
- **Type:** story (ENGINE, wire-first)
- **Points:** 5
- **Priority:** p2
- **Workflow:** tdd
- **Repo:** server (only)
- **Epic:** 157 — Faction/zone-scoped content eligibility
- **Depends on:** 157-2 (DONE — merged server develop, PR #1002, commit `0f199b0f`)

## Authoritative design (READ THESE — they live in the ORCHESTRATOR repo, not server)
- **Spec:** `docs/superpowers/specs/2026-06-20-faction-zone-content-eligibility-design.md` → section **"Seam 2 — NPCs (two sub-parts)"** (and OTEL + Testing sections).
- **Plan:** `docs/superpowers/plans/2026-06-20-faction-zone-content-eligibility.md` → **"Task 3"** (maps 1:1 to this story; has the RED tests verbatim).
- **ADR:** `docs/adr/152-faction-zone-scoped-content-eligibility.md` (ADR-059 amendment).
- NOTE: the session file / epic description mis-cite this path as `sidequest-server/docs/...`. It is in the **orchestrator** repo at `./docs/...`.

## Problem
Multi-region worlds leak NPCs across zones. Seam 1 (157-2) scoped *creature/encounter*
injection by faction; Seam 2 does the same for **NPCs**, in two halves:
1. **Generated walk-ons** (runtime namegen filler) can resurface in the wrong region — a
   walk-on born in Lilliput later appears in Houyhnhnm-land.
2. **Authored cast** (cartography-homed NPCs) don't reliably appear when the party *enters*
   their region — the narrator has to elect `resolve_location_entity`, so it invents
   cross-voyage extras instead.

## Technical Approach (from spec "Seam 2" + plan "Task 3")
Two sub-parts. Reuse the merged Seam-1 `zone_eligibility` surface; do NOT re-implement it.

### Sub-part A — Generated walk-on origin-stamp (not exclude)
- The pre-seeded namegen pool is runtime filler, so the validator never touches it.
  Instead, **stamp on activation**: when an unplaced generated NPC is activated in a
  *zoned* world, set its `factions = [current region's controlled_by]` alongside the
  existing `activated_location`. No over-suppression — the narrator still gets walk-ons.
- File: `sidequest/game/monster_manual.py` — extend `mark_active(self, name, location, *, faction=None)`
  (currently `mark_active(self, name, location)` at ~line 283 — **verified no `faction`
  kwarg today**, so the RED test genuinely fails). When `faction` is provided and the NPC's
  `factions` is empty, origin-stamp it.
- Caller: `sidequest/server/dispatch/monster_manual_inject.py` passes the region's
  `controlled_by` **only in a zoned world**; surfacing consults `is_eligible`.

### Sub-part B — Authored-cast staging on region entry
- Register the **first real consumer** of the empty frontier observer registry.
- Observer module: `frontier_hook` lives at **`sidequest/dungeon/frontier_hook.py`**
  (NOT `game/` — spec/plan omit/mis-path this). Public surface verified:
  `register_frontier_observer`, `unregister_frontier_observer`, `registered_observer_count`,
  `notify_region_transition(snapshot, *, pc_name, from_region, to_region)`, module-global
  `_OBSERVERS`.
- Create: `sidequest/game/region_cast_staging.py` →
  `stage_region_cast(*, snapshot, pc_name, from_region, to_region) -> None`. On region entry,
  push-stage that region's cartography `entities` where `binding.kind == "npc"` into the
  active/in-scene set (materialize/activate into `snapshot.npc_pool`, mark active, advance
  `last_seen`/activated_location). **Idempotent** — skip NPCs already active/in pool.
- Register the observer **ONCE at server startup** (app wiring), never per session.

### HARD concurrency constraint (do not skip)
`frontier_hook._OBSERVERS` is **module-global**. `stage_region_cast` MUST resolve the
pack/cartography from the **snapshot it is handed** (`snapshot.genre_slug`,
`snapshot.world_slug`) — never from a per-session captured closure — or a transition in
session A would stage using session B's pack. (See `dungeon/session_integration.py:50`,
which builds a new bound observer per call — the anti-pattern to avoid.)

## OTEL (REQUIRED — the lie-detector; persisted, round-stamped game-engine events)
- `zone_eligibility.filtered` — on every NPC *exclusion* (subsystem=npc, content_id,
  content_factions, active_factions, region).
- `zone_eligibility.cast_staged` — authored NPCs push-staged on region entry (region + names/count).
- These are **persisted game-engine events** (like `state_patch_hp`), NOT live-only agent spans.
  Add the `cast_staged` span emitter alongside the existing `zone_eligibility` spans
  (`sidequest/telemetry/spans/zone_eligibility.py`, created in 157-2).

## Scope
- **In scope:** Seam 2 only — NPC walk-on origin-stamp + authored-cast staging + the two
  OTEL events + their wiring tests.
- **Out of scope:** Seam 3 (trope gate) and Seam 4 (seed draw) → 157-4. The strict
  load validator → 157-7 (lands last; runtime stays permissive here). Content tagging
  (gulliver/oz/etc.) → 157-5/6.

## Acceptance Criteria (from spec "Testing" + plan "Task 3" steps)
1. `mark_active(..., faction=<region controlled_by>)` origin-stamps a generated walk-on
   with empty `factions` in a zoned world; leaves an already-tagged NPC untouched.
2. Entering a region stages that region's authored cartography NPC cast into
   `snapshot.npc_pool` (e.g. entering Mildendo surfaces the Emperor + Reldresal),
   idempotently (re-entry stages nothing new).
3. `zone_eligibility.cast_staged` span fires on staging (region + names); the NPC
   `zone_eligibility.filtered` span fires on exclusion.
4. **Cross-fire guard:** firing a transition for world A's snapshot stages A's cast and
   never B's (pack resolved from snapshot, not a captured closure).
5. One wiring test per the new seam (fixture-driven behavior + OTEL — never source-grep
   wiring). The observer is registered once at startup and reachable from a production path.

## Verified infrastructure (exists today; wire it, don't reinvent)
- `sidequest/game/zone_eligibility.py`: `world_is_zoned`, `is_eligible`, `cartography_for`,
  `active_factions` (Seam 1).
- `sidequest/game/monster_manual.py`: `mark_active` (no faction kwarg yet),
  `add_npc`, `find_npc_by_exact_name`.
- `sidequest/dungeon/frontier_hook.py`: full observer registry (empty — 0 real consumers).
- `sidequest/telemetry/spans/zone_eligibility.py`: existing span emitters (add `cast_staged`).

---
_Enriched by SM from the 157-1 design spec + implementation plan (the auto-generated
template was hollow because the sprint YAML carries no description/ACs)._
