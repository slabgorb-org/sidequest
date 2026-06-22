# Story 153-19 Context

## Title
[PLAYTEST-DATA-ODDITIES] nottavello header latch + stale Adventurer location key + active_stakes class-name + npcs None-rows

## ⚠️ Scope Amendment (2026-06-22, SM)

**Oddity 1 (nottavello header latch) is DEFERRED out of this story.** It is a session-create
*location-seeding* bug that overlaps the in-flight **location-single-authority** effort (server PR
#1029 "Plan 1: engine-authoritative lateral region travel", with Plans 2–3 to follow that *sever
the narrator's `location_drift_repaired` title-scrape authority* — the exact mechanism oddity 1
leans on). Fixing the seeding symptom here would race the root-cause work, so it folds into that
effort instead.

**In scope for 153-19: oddities 2, 3, 4 only.** Below, oddity 1 and AC-1 are retained for history
but marked DEFERRED — do not write tests or code for them. The wiring AC (AC-5) draws from oddities
2–4.

## Metadata
- **Story ID:** 153-19
- **Type:** bug
- **Points:** 3
- **Priority:** p3
- **Workflow:** tdd
- **Repo:** server
- **Epic:** 153 — Playtest follow-ups (open findings from the 2026-06-20/21 full-stack /sq-playtest sweep)

## Problem Statement

Four low-severity "data oddity" snapshot/projection bugs recur across multiple worlds and have been
logged as CONFIRM/DO-NOT-RE-FILE on the board (the_circuit, shattered_accord, burning_peace,
earlier 150-11/150-12). Each is individually self-healing or cosmetic, but they collectively mean
the snapshot exposed to the narrator and the UI is transiently dirty on turn 1 or permanently stale
in named fields. This story exists to actually fix the family rather than re-confirming it on
another world.

### Oddity 1 — nottavello header latch (the_circuit) — ⚠️ DEFERRED (see Scope Amendment)

Turn-1 location chip shows **`nottavello`** — a raw lowercase region id that is neither the
cartography `starting_region` (`sturmichi`) nor the opening `location_label`. The session-create
path seeds the character's initial location to a non-starting region (`nottavello`) before the
opening narration repairs it via `narrator.location_drift_repaired`. The header latches that
pre-repair value and self-corrects only after the first action resolves. Ground truth was already
correct at that point (`current_region: sturmichi`, `character_locations.Riggs: "Kannai Onramp —
Kanjō Loop"`).

### Oddity 2 — stale "Adventurer" location key (barsoom)

`character_locations` carries a stale default `Adventurer` key alongside the real character key
(`Kantos`). This is a pre-name placeholder that was not cleaned up during character finalization.
The stale key persists in the snapshot and is visible in projections.

### Oddity 3 — active_stakes shows raw class-name (shattered_accord, burning_peace)

`active_stakes` is mis-populated with the PC's class name (`"Channeler"`) instead of a stakes
description. The Confrontation panel UI displays **Stakes: Channeler**, which is meaningless to
players and signals a projection bug at the stakes serialization or seating layer.

### Oddity 4 — npcs None-rows (shattered_accord, burning_peace)

The snapshot `npcs` roster contains 7× `None` entries when `authored_npcs_seeded=0` for a world
(MM-patch empty slots / serialization gap). Real scene NPCs are correctly present in `npc_pool`;
the None-rows are phantom entries from empty MM patch slots that survived serialization rather than
being filtered.

## Repro / Evidence

- **Board lines 262–270** (the_circuit, new session): turn-1 header shows `nottavello`, self-heals
  after first action. Root spelled out: `narrator.location_drift_repaired old_state='nottavello'`.
- **Board lines 356–362** (barsoom): `character_locations` carries stale `Adventurer` key alongside
  real `Kantos` key. Flagged as CONFIRM / DO-NOT-RE-FILE — matches 150-11/150-12.
- **Board lines 394–402** (shattered_accord, WWN, session 2026-06-20-shattered_accord-702c5fb9):
  `active_stakes: "Channeler"` + snapshot `npcs` = 7× `None`. Flagged as CONFIRM / matches 150-11.
- **Board lines 439–447** (burning_peace, WWN, session 2026-06-20-burning_peace-e6f5cbe6):
  `active_stakes: "Channeler"` + snapshot `npcs` = 7× `None`. Filed as BUG-LOW / open.

## Fix Direction

Address each oddity at its source so the snapshot/projection is clean from turn 1 rather than
self-correcting a turn later or carrying phantom/stale rows:

1. **nottavello header latch:** ensure session-create seeds the character's location to the correct
   `starting_region` / `location_label` before the first snapshot is exposed — so the header never
   latches the pre-repair transient value.
2. **stale "Adventurer" location key:** clean up the pre-name placeholder key from
   `character_locations` at character finalization (when the real character name is committed) so no
   stale default key persists alongside the real key.
3. **active_stakes class-name:** fix the stakes population/serialization path so `active_stakes`
   carries a stakes description, not the PC class name. Investigate the seating or
   confrontation-payload layer where this field is written.
4. **npcs None-rows:** filter None entries from the `npcs` collection before serialization / before
   the snapshot is exposed to the narrator and projections. Empty MM-patch slots must not survive
   as None rows; the npc_pool path is already correct.

Treat as a cluster of targeted fixes under one story — each fix is small, but they share the theme
of snapshot/projection cleanliness and recur as a family.

## Acceptance Criteria

1. **⚠️ DEFERRED — Header shows resolved location on turn 1.** (Folded into the location-single-authority
   effort, server PR #1029 + Plans 2–3. NOT in scope for 153-19 — do not write tests or code for this
   AC.) On a fresh session, the turn-1 location chip/header shows the resolved `location_label` (e.g.
   "Kannai Onramp — Kanjō Loop"), never a raw region id like `nottavello`. The
   `narrator.location_drift_repaired` telemetry should not fire on turn 1 because the location was
   never wrong to begin with.

2. **No stale "Adventurer" location key.** After character finalization, `character_locations` in
   the snapshot contains only the real character key — no stale pre-name default key (`Adventurer`
   or equivalent) alongside it.

3. **active_stakes shows a display label, not a class-name.** When `active_stakes` is present in
   the snapshot, it contains a stakes description string, not the PC's class name. The Confrontation
   panel should never display "Stakes: Channeler" or any other raw class identifier.

4. **No None-rows in npcs.** The snapshot `npcs` collection contains no `None` entries. Worlds with
   `authored_npcs_seeded=0` (empty MM-patch) produce an empty list, not a list of `None` placeholders.

5. **Wiring / integration-test AC.** At least one test drives the real snapshot/projection path (not
   just an isolated helper) and asserts at least one of the above oddities is absent. E.g. a session
   creation test that asserts the initial `character_locations` snapshot contains no `None`-keyed or
   placeholder-keyed entries, OR a confrontation-payload test that asserts `active_stakes` is not a
   class-name string.

6. **Do not re-file the carried-forward CONFIRM items.** These oddities are the 150-11/150-12 data
   oddity family. This story is the resolution; no new tracking items should be created for the same
   symptoms on additional worlds.

## Source

- Board lines 262–270 (nottavello header latch, the_circuit)
- Board lines 356–362 (stale Adventurer location key, barsoom — CONFIRM/DO-NOT-RE-FILE)
- Board lines 394–402 (active_stakes class-name + npcs None-rows, shattered_accord — CONFIRM)
- Board lines 439–447 (active_stakes class-name + npcs None-rows, burning_peace — BUG-LOW/open)

## Scope Notes

In scope (oddities 2–4 only — see Scope Amendment):
- Oddity 2 (stale Adventurer key), oddity 3 (active_stakes class-name), oddity 4 (npcs None-rows).
- Fixes at source (character finalization cleanup, stakes serialization, None-filtering before
  snapshot exposure).
- Integration test reproducing at least one of oddities 2–4 through the real snapshot/projection path.

Out of scope:
- **Oddity 1 (nottavello header latch / session-create location seeding) — DEFERRED** into the
  location-single-authority effort (server PR #1029 + Plans 2–3). Do not fix here.
- ADR-145 SRD inventory skinning (generic barsoom kit) — that is a separate deferred item.
- Any new snapshot/projection architecture — targeted fixes only.
- Re-filing any of these as new items on additional worlds; this story closes the family.
