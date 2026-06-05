# Story 86-2 Context

## Title
Plan 2 — Solo rig two-pool vehicle combat: wire the dormant RigComposurePool + rig_crash into a real confrontation.

## Story Details
- **ID:** 86-2
- **Epic:** 86 (road_warrior → Cities Without Number: Two-Tier Rig Combat)
- **Points:** 8
- **Repos:** sidequest-server, sidequest-content
- **Workflow:** tdd (phased: SM setup → TEA red → Dev green → Reviewer → SM finish)
- **Parent:** None (depends on 86-1 for CWN binding completion)

## Overview
Wire the dormant `RigComposurePool` and `rig_crash` subsystems into real combat confrontation mechanics. Implement a **two-pool resolution model** for solo rig vehicle combat:
1. **Rig pool** (Composure, hull damage) — governs vehicle destruction and crash events
2. **Driver pool** (ablative HP) — governs driver incapacitation after crash

When rig Composure reaches 0, the vehicle crashes → occupants take crash damage (Physical + Luck saves per CWN §2.4.8) → dismounted survivors are now engaged in foot combat.

## Technical Approach

### 1. Vehicle AC Calculation
- **Stationary:** −4 AC (easier to hit)
- **Moving:** +Driver's Drive skill modifier to AC (armor bonus for motion)

### 2. Vehicle Armor & Damage
- Each vehicle type has an **Armor rating** (subtracted from all damage, per CWN §2.4.8)
- Damage applied to Rig Composure (the `RigComposurePool`)
- Rig pool spans (`rig_pool.delta`, `rig_pool.zero_crossing`) should fire on each damage event

### 3. Rig Zero-Crossing (Crash Trigger)
- When Rig Composure ≤ 0, a crash event occurs
- Emit `rig_pool.crash_event` OTEL span
- All occupants must pass **Physical + Luck saves** (per CWN §2.4.8.2):
  - Both pass → unscathed
  - Fail Physical → half-max-HP damage (may be Mortal)
  - Fail Luck → half-max-HP damage (may be Mortal)
  - Fail both → Mortally Wounded + Major Injury if survived
- Driver and all passengers are dismounted to foot combat after crash

### 4. Ramming Mechanic
- Attacking vehicle & target each roll **Dex + Drive skill** opposed check
- Winner → target takes **vehicle's max HP in damage**, **Trauma 1d12×3**
- Ramming vehicle also takes damage as if rammed back (mutual damage)
- Implement as a combat action available during rig confrontations

### 5. Two-Pool Resolution Variant
This story must introduce a **new WinCondition variant** or extend the beat-application system:
- **First pool:** Rig Composure (hull damage, confrontation-level resolution)
- **Second pool:** Driver HP (personal combat after crash)
- Win condition: Driver HP ≤ 0 (after dismount from rig crash) OR rig destroyed with no escape
- A single confrontation may transition from rig combat → foot combat if a crash is forced

### 6. Integration Points
- `RigComposurePool` class (`sidequest/game/rig_composure_pool.py`) — already exists; wire into damage flow
- `rig_crash.py` — already exists; wire crash event trigger
- `vessel_tags.py` — already exists; use vessel type to determine Armor/AC
- Telemetry: ensure `rig_pool.*` spans fire on rig damage, zero crossing, crash events
- Confrontation dispatch: route vehicle-vs-vehicle encounters to the two-pool resolver

## Acceptance Criteria

1. **Vehicle AC applies correctly**
   - Stationary vehicle AC = −4
   - Moving vehicle AC = base + Driver's Drive modifier
   - Ranged/melee attacks vs vehicle use vehicle AC, not driver AC

2. **Rig Composure as ablative pool**
   - Damage to rig is applied to `RigComposurePool.current`
   - `rig_pool.delta` span fires on each damage event with delta amount
   - `rig_pool.zero_crossing` span fires when pool crosses ≤ 0

3. **Armor reduction works**
   - Each vehicle type has an Armor rating in inventory
   - Damage taken = dealt damage − Armor (minimum 1)
   - Armor stat is visible in the rig stat block

4. **Crash event triggers on zero crossing**
   - When `rig_pool.current` ≤ 0, emit `rig_pool.crash_event` span
   - Crash event initiates Physical + Luck saves for all occupants
   - Failed saves apply half-max-HP damage and potential Mortal/Major Injury

5. **Driver dismounts after crash**
   - Crashed vehicle occupants are moved to foot combat state
   - Driver switches from rig actions (Drive, ramming) to personal combat actions
   - New confrontation or state transition for foot combat resolution

6. **Ramming is mechanically implemented**
   - Ramming is available as a main action during rig combat
   - Attacker rolls Dex + Drive vs defender Dex + Drive
   - Winner deals max-HP damage + Trauma to target
   - Attacker takes damage back as if rammed (mutual damage)

7. **Two-pool resolution model**
   - A single confrontation can encompass both rig and driver damage pools
   - Win condition accounts for driver incapacitation (not just rig destruction)
   - Transition from rig → foot combat is mechanically distinct

8. **OTEL wiring test passes**
   - Create integration test (`test_rig_two_pool_combat`) that verifies:
     - `rig_pool.delta` spans fire on damage
     - `rig_pool.zero_crossing` span fires on crash
     - `rig_pool.crash_event` span fires on crash trigger
     - Driver takes crash damage and transitions to foot combat
     - Ramming damage applies correctly to both vehicles
   - Test runs on a real turn in a rig confrontation scenario (not mocked)

9. **Branch & PR**
   - Branch: `feat/86-2-road-warrior-solo-rig-two-pool-combat`
   - Both sidequest-server and sidequest-content changes in the PR
   - Tests passing, OTEL integration verified

## Design References
- **Design Doc:** `docs/superpowers/specs/2026-06-04-road-warrior-cwn-rig-combat-design.md`
- **CWN SRD:** Vehicle Combat §2.4.8, Vehicle Chases §2.6.2
- **Epic 86 Context:** `sprint/context/context-epic-86.md`
- **ADR-114:** Ablative HP Substrate
- **ADR-117:** Pluggable Ruleset Module System
- **ADR-125:** Chassis/Rig as First-Class Entity

## Notes for Implementation

- **No reinvention:** The subsystems are already implemented and dormant (RigComposurePool, rig_crash, vessel_tags, OTEL spans); the work is wiring them into a confrontation flow.
- **Faithful port:** Damage, AC, Armor, crash saves, and ramming all follow CWN §2.4.8 exactly — do not redesign.
- **Two-pool is new:** The transition from rig pool → driver pool on crash is net-new logic; plan the state machine carefully.
- **GM panel verification:** The GM panel's OTEL dashboard must show `rig_pool.*` spans firing in live play to verify the feature is engaged (not improvised).

---
_Generated by sm-setup for story 86-2 from sprint/epic-86.yaml and design spec._
