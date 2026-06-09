# Story 86-5: Road Warrior CWN — Content Remap + Calibration + Playtest

**Epic:** 86 (road_warrior → Cities Without Number: Two-Tier Rig Combat)
**Points:** 5
**Workflow:** tdd
**Repos:** sidequest-server, sidequest-content

## Acceptance Criteria

1. **Vessel stat blocks created** in `sidequest-content/genre_packs/road_warrior/inventory.yaml`:
   - Composure, armor, speed, and mount_slots per rig tier (solo rig vs War Rig)
   - mount_slots mapped to CWN vehicle weapons from the rules

2. **Archetype + lethality calibration** against the live CWN substrate:
   - Every rig/chassis stat block passes validation against the CWN ruleset
   - Stat ranges align with expected difficulty across tier levels
   - Player-facing armor/speed values are legible and consistent

3. **OTEL playtest pass** on `road_warrior/the_circuit` scenario:
   - Every rig subsystem fires mechanically (no improvised prose)
   - rig_pool.* spans emit on rig damage/composure changes
   - Rig confrontation win_condition logic executes correctly
   - Chase subsystem (if tested) fires appropriately
   - War Rig crew subsystem (if tested) dispatches seats and Command Points

4. **Integration gate:** Story confirms Plans 1–4 are production-ready and the epic can be marked complete

## Technical Scope

- Content file updates: `inventory.yaml`, potentially `rules.yaml` clarifications
- OTEL validation: run playtest scenario, grep logs for rig_* and confrontation.* spans
- Calibration: cross-check all vessel AC, Armor, HP formulas against SRD baseline
- Test/wiring: ensure no silent fallbacks (all subsystems fail-loud if config is missing)

## Dependencies

- Plans 86-1, 86-2, 86-3, 86-4, 86-6, 86-7 complete (all done as of 2026-06-09)
- Design spec: `docs/superpowers/specs/completed/2026-06-04-road-warrior-cwn-rig-combat-design.md`
- War Rig spec: `docs/superpowers/specs/2026-06-09-road-warrior-war-rig-crew-spec.md`

## Known Blockers

- None; all upstream stories are complete
