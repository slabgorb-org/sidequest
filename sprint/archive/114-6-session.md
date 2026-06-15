---
story_id: "114-6"
jira_key: ""
epic: "114"
workflow: "tdd"
---
# Story 114-6: road_warrior — bind the CWN vehicle chapter, retire bespoke Rig Composure (ADR-143)

## Story Details
- **ID:** 114-6
- **Jira Key:** (none — no Jira for SideQuest)
- **Workflow:** tdd
- **Stack Parent:** 114-5 (done, confirmed)
- **Points:** 8
- **Priority:** p2
- **Type:** feature

## Workflow Tracking
**Workflow:** tdd
**Phase:** red
**Phase Started:** 2026-06-15T03:14:46Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-15T03:14:46Z | - | - |
| red | - | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- findings below -->

### TEA (test design)
- **Conflict** (blocking): Story 114-6's premise is stale — "bind the CWN vehicle chapter" is **already done** by epic 86. road_warrior already binds `ruleset: cwn` (`genre_packs/road_warrior/rules.yaml:20`); `game/vehicle_combat.py` is a faithful CWN SRD §2.4.8 port and `game/chase_pace.py` is a faithful CWN §2.6.2 port, both with ~25 existing tests (`tests/game/test_vehicle_combat_ac.py`, `test_chase_pace.py`, `test_rig_ramming.py`, `tests/server/test_road_warrior_cwn_combat_e2e.py`, `tests/integration/test_chase_confrontation_cwn.py`, …). *Found by TEA during test design.*
- **Conflict** (blocking): The haiku-authored ACs reference artifacts that don't exist: AC1's `VehicleTemplate`/`ChaseRound` models (real names are `vehicle_combat.py`/`chase_pace.py` + `resolve_chase_round`), and AC4's `tests/server/game/vehicles/` directory (absent). Writing RED tests against these would direct Dev to reinvent shipped CWN code — violates ADR-143 and "Don't Reinvent — Wire Up What Exists." Affects all four ACs in `.session/114-6-session.md`. *Found by TEA during test design.*
- **Conflict** (blocking): The one genuine remnant — AC2 "remove RigComposurePool" — contradicts a deliberate epic-86 design (`game/war_rig_combat.py:25`: "Solo-rig combat **stays** on 86-2's RigComposurePool … not a replacement", spec §6) and is high-blast-radius (`views.py`, `protocol/models.py`, `creature_core.py`, `vessel_tags.py`, `chargen_loadout.py` + ~15 tests). Per ADR-143 it is part of the **CWN combat cutover, which ADR-143 explicitly stages BEHIND the in-progress WWN cutover (epic 108, 108-3 de-nativize)** — so it should be a separately-scoped, correctly-sequenced cutover story, not started now. *Found by TEA during test design.*
- **Conflict** (non-blocking): Epic mismatch — 114-6 is filed under epic 114 (*SRD-sourced inventory; bind the equipment catalog*), but it is a combat-engine cutover. The genuine remnant belongs with the CWN/WWN combat-cutover epic (108-family), not the inventory epic. *Found by TEA during test design.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

### TEA (test design)
- No deviations from spec. RED phase was not entered — story premise found stale before any test was written (see TEA Assessment below).

## TEA Assessment

**Tests Required:** No
**Reason:** Story premise is stale/mis-scoped. The CWN vehicle/chase chapter this story asks to "bind" is **already bound** (epic 86: `vehicle_combat.py` CWN §2.4.8, `chase_pace.py` CWN §2.6.2; road_warrior `ruleset: cwn`), with ~25 existing tests. The haiku-authored ACs invent models (`VehicleTemplate`/`ChaseRound`) and a test dir (`tests/server/game/vehicles/`) that don't exist. Writing RED tests would direct Dev to reinvent shipped CWN code — a violation of ADR-143 and Don't-Reinvent. See Delivery Findings for the four blocking conflicts.

**Status:** NOT RED — bounced to SM (user decision, 2026-06-15: "Bounce to SM as stale").

### Disposition recommendation (for SM)
1. **Block or cancel 114-6** in the sprint YAML (`pf sprint story` — do not hand-edit YAML).
2. **Clean up:** the empty `feat/114-6-road-warrior-cwn-vehicle-bind` branches in `sidequest-server` and `sidequest-content` (created at setup, no commits), and the `.session/114-6-session.md` + `sprint/context/context-story-114-6.md` artifacts.
3. **Re-file the genuine remnant** (if/when ADR-143 sequencing allows): "Retire bespoke `RigComposurePool`; confirm road_warrior solo-rig combat + chase resolve purely through CWN `vehicle_combat.py`/`chase_pace.py` + driver ablative HP." Scope it under the **CWN/WWN combat-cutover epic (108-family)**, not inventory epic 114, and **sequence it behind the WWN cutover** per ADR-143's explicit staging.

**Handoff:** To SM (Vizzini) for story disposition.

## Technical Summary

**Epic:** 114 — SRD-sourced inventory; bind equipment catalog, don't author it
**Depends On:** 114-5 (CWN extraction + neon/road_warrior personal gear) — DONE
**Related:** Epic 86 (road_warrior CWN bind prior work)

### Scope
Bind the CWN (Cyberpunk Without Number) vehicle chapter to replace bespoke road_warrior Rig Composure mechanics. Per ADR-143 doctrine ("Bind the Ruleset, Don't Balance It"), the native Rig Composure pool is removed in favor of CWN's vehicle/chase mechanics.

### Repos
- **sidequest-server:** Game engine + CWN vehicle models + OTEL spans
- **sidequest-content:** road_warrior world crunch + inventory updates

### Branch Strategy
**Branching Strategy:** gitflow (standard for subrepos)
- **sidequest-server:** `feat/114-6-road-warrior-cwn-vehicle-bind`
- **sidequest-content:** `feat/114-6-road-warrior-cwn-vehicle-bind`

### Acceptance Criteria

**AC1: CWN Vehicle Chapter Extracted**
- Extract vehicle/chase mechanics from CWN SRD
- Create VehicleTemplate and ChaseRound models as typed fields
- Wire vehicle state to game engine without bespoke pooling
- Verify extraction completeness against SRD reference

**AC2: Rig Composure Removal + CWN Binding**
- Remove RigComposurePool from all road_warrior instances
- Repoint rig/chase mechanics to CWN vehicle chapter
- Verify vessel_tags compatibility with CWN vehicle categories
- Confirm rig_crash/rig_damage resolve through CWN seams

**AC3: Content Layer Update**
- Update road_warrior world crunch to use CWN vehicle chapter
- Remove bespoke Rig Composure pools from encounters/NPCs
- Add CWN vehicle stats to road_warrior starting loadouts
- Verify test_road_warrior_pack_loads with new binding

**AC4: Integration Tests**
- Green: tests/server/game/vehicles/ passing
- Green: tests/genre/road_warrior/ for CWN vehicle wiring
- No regressions in confrontation/chase flow
- OTEL spans emit for vehicle actions (ADR-090)

### Implementation Plan

1. **Extract CWN Vehicle Seams** — Read CWN SRD vehicle chapter; identify resolve paths (maneuvers, damage, crew damage)
2. **Model Definition** — VehicleTemplate, ChaseRound, VehicleDamage as game/vehicles module
3. **Remove RigComposure** — Strip RigComposurePool; repoint rig-state queries to vehicle seams
4. **Content Binding** — Load CWN vehicle catalog into road_warrior genre/world inventory
5. **Test Coverage** — Unit tests per seam; integration tests for full chase flow

### Implementation Notes

- Coordinate with epic-86 scope (rig solo vs War Rig crew)
- Verify rig/composure/chase = native dials are fully replaced, not supplemented
- Check existing vessel_tags for reuse in CWN vehicle categories
- OTEL: emit spans on vehicle_maneuver, vehicle_damage, chase_round_trigger
- RigComposurePool, rig_crash, vessel_tags currently EXIST but dormant prose per memory
