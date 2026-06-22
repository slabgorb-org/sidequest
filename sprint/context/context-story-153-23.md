# Story 153-23 Context

## Title
[DUNGEON-ROOM-POPULATION-INERT] place authored encounter_creatures + bestiary creatures into generated rooms so exploration spawns real encounters instead of narrator-improvised ones

## Metadata
- **Story ID:** 153-23
- **Type:** bug
- **Points:** 5
- **Priority:** p1
- **Workflow:** tdd
- **Repo:** server
- **Epic:** 153 — Playtest follow-ups (open findings from the 2026-06-20/21 full-stack /sq-playtest sweep)

## Problem Statement

Playtest forensics (beneath_sunden / caverns_and_claudes, WWN): after a movement turn the
narrator advanced to an invented room and spawned "three pale, long-limbed, wet things" plus
"seven silver coins." The save tells a different story than the prose:

- `current_region` was STILL `exp002.r2` — the party never actually moved region.
- `npc_pool=[None]` — the three described creatures are NOT seeded. No bestiary placement, no
  encounter started, despite three described hostiles.
- The loot landed as inventory `id='narrator:seven_silver_coins' value=0` — a "Yes-And" flavor
  item, not a treasure drop.

The depth-graduated bestiary (gnaw_swarm/spider/goblin/skeleton → otyugh/pudding → aboleth/lich)
and the 6 pre-seeded "nearby" `creatures.yaml` NPCs exist, but are never PLACED into generated
rooms. Worst of all, the authored entrance room
(`worlds/beneath_sunden/rooms/entrance.yaml`) binds `encounter_creatures: [gnaw_swarm]` —
documented in-file as "an easy first fight, on purpose" — and **it never fired.**

Net: the dungeon generates topology, but rooms are UNPOPULATED by the engine. The narrator
improvises creatures and loot with zero mechanical backing — textbook Illusionism, the exact
failure the GM panel exists to catch.

## Status Update (2026-06-22) — movement confound removed; THIS story STILL OPEN

**Do NOT close this story on the back of the dungeon-affordance / crossing work.** That work
(server PR #1042, squash-merged to `develop` 2026-06-22 — the sünden surface→procedural crossing,
movement→`turn_telemetry` observability, the narrator `/current_region` denial, and the
generate-before-narrate "affordance race" fix) is the **movement/observability layer only**. It is
orthogonal to room population and does **not** satisfy any AC here.

What it *did* change for this story (helpful, not done):
- The original Problem Statement's lead symptom — *"`current_region` was STILL `exp002.r2` — the
  party never actually moved region"* — is **fixed.** The party now moves cleanly room-to-room and
  every move is recorded in `turn_telemetry` (was Jaeger-only), so this story's forensics are no
  longer muddied by a stuck PC + a narrator improvising the *movement*. The story is now cleanly
  testable: you can drive a party through real generated rooms and watch placement fire or skip.

What it did **not** change — re-verified live 2026-06-22 (14-turn `sunden_descend_trace` expansion
run; spans `/tmp/sunden_expand.spans.jsonl`, server log `~/.sidequest/logs/sidequest-server.log`):
- **The authored `entrance → encounter_creatures: [gnaw_swarm]` STILL never fired** (0 occurrences
  across the whole run) — AC-1 unmet.
- **Every room logged `state.room_state_injected … retrieved_count=0`** (The Drowned Cavern, The
  Bend, Going Deeper, Eastern Side Passage, The Winding Catacomb) — rooms entered, nothing placed.
- **The narrator still improvised hostiles with no mechanical backing** (a "dragging pursuer in the
  dark"), the exact Illusionism this story targets — AC-3/AC-5 unmet.
- `inject()` at `websocket_session_handler.py` is still called **without `room_id`** — the wiring
  gap in Root Cause Direction below is intact.

**Net:** all ACs remain UNMET. Keep at `backlog`, p1. The fix is still the `inject(room_id=…)`
threading described below — now unblocked and observable thanks to PR #1042, but not begun by it.

## Root Cause Direction

**The room-binding placement path already exists and is simply not called in production.**
This is a wiring gap, not missing infrastructure — do NOT build a new spawn/curate system.

The 107-2 work (ADR-059 per-room binding) already ships every piece needed:

- `sidequest/server/dispatch/room_creature_binding.py::resolve_room_creatures(pack, world_slug, room_id)`
  reads the room YAML's `encounter_creatures` list, validates each id against the world's
  effective bestiary (fails loud on a dangling ref), and emits the `monster_manual.room_bound` span.
- `sidequest/server/dispatch/monster_manual_inject.py::_npc_patches_for_room_binding(sd, room_id, current_location)`
  calls that resolver, looks each id up in `pack.effective_bestiary(world)`, and builds an
  `NpcPatch(manual_origin=True)` carrying the authored name ("Gnaw-Swarm").
- `monster_manual_inject.inject(...)` accepts a `room_id` parameter; when `room_id` is supplied it
  runs `_npc_patches_for_room_binding` and materializes the bound creature.

**The break:** the sole production caller —
`sidequest/server/websocket_session_handler.py:843` — calls `inject(sd, snapshot,
current_location=..., in_combat=...)` and **never passes `room_id`.** It therefore defaults to
`room_id=None`, the binding branch is skipped, and the authored `gnaw_swarm` placement is dead
code in production. The 107-2 test
(`tests/integration/test_dungeon_scene_advance_107_1.py`) drives the resolver with an explicit
`room_id="exp001.r2"` override "as the handler would AFTER its gate" — but the handler never grew
that gate.

The fix direction: thread the entered room/region id into the `inject()` call. The id is already
available on the snapshot — `GameSnapshot.region_for()` (per-PC graph region truth, from
`pc_regions`) is the canonical key 107-1 introduced; `_ENTRANCE_ID = "entrance"` and
`expNNN.rN` are the literal node ids the placement must match. When the entered room declares
`encounter_creatures` (or, where appropriate, when a depth-appropriate bestiary pick is wanted for
an authored-room-less procedural node), place those creatures into `snapshot.npc_pool` / `snapshot.npcs`
and seed the encounter instead of leaving the narrator to improvise.

Compounding causes to reference but NOT solve here:
- **153-26 (DUNGEON-CURATE-TIMEOUT):** when curate degrades, the authored entrance room content
  (including `gnaw_swarm`) is dropped, so even a wired placement path can find nothing to place.
- **153-27 (DUNGEON-ZONE-ELIGIBILITY-UNKNOWN-REGION):** the zone/cast-eligibility layer treats
  procedural region ids as `unknown_region` and stages no cast into generated rooms.

THIS story is specifically "rooms get no creature/encounter placement on entry" — the
`inject(room_id=...)` wiring.

## Acceptance Criteria

1. **Authored room bindings are placed on entry.** When a PC enters a generated room whose YAML
   declares `encounter_creatures` (e.g. `entrance` → `[gnaw_swarm]`), the bound bestiary creature
   is materialized into game state under its authored name ("Gnaw-Swarm"), not left for the
   narrator to label.

2. **The entered room id is threaded into injection.** The production narration path
   (`websocket_session_handler.py`) resolves the entered room id from the snapshot's per-PC region
   truth (`GameSnapshot.region_for()` / `pc_regions`) and passes it as `inject(..., room_id=...)`,
   so `_npc_patches_for_room_binding` runs. The existing `room_id=None` behavior is preserved for
   any caller that has no room context (strictly additive).

3. **An encounter is seeded for a populated room.** When a room places one or more hostile
   creatures, the engine starts/arms the encounter (so the next combat action has a real Other to
   resolve against), rather than the creatures sitting inert in `npc_pool` while the narrator
   describes a fight with no mechanical state.

4. **Loot/treasure has mechanical backing OR is honestly flavor.** A room's authored treasure is
   placed as a real inventory drop with a non-improvised id and a real value; narrator "Yes-And"
   flavor items remain clearly tagged (`narrator:` source) and are NOT silently presented as
   mechanical loot. (Scope this to verifying the authored-placement path; do not build a new loot
   table system.)

5. **OTEL / watcher-span AC.** Entering a room with a resolved binding emits the existing
   `monster_manual.room_bound` span (`SPAN_MONSTER_MANUAL_ROOM_BOUND`, naming room + bound
   creatures) AND the per-turn `monster_manual.injected` count reflects the placed creatures, so
   the GM panel can distinguish "engine placed the authored Gnaw-Swarm" from "narrator improvised
   three wet things." If the room placement also seeds an encounter, the encounter-creation span
   fires. No populated-room turn may pass without a span proving the engine placed the creature.

6. **Wiring / integration-test AC.** A test reachable from the real play path drives a room
   transition into `entrance` (or a room with `encounter_creatures`) through the production
   `inject()` call site — NOT by calling `_npc_patches_for_room_binding` directly with an override
   — and asserts: (a) the bound creature is present in `snapshot.npcs`/`npc_pool` with
   `manual_origin=True` and the authored name, and (b) the `monster_manual.room_bound` span fired.
   This proves the `websocket_session_handler` → `inject(room_id=...)` wiring is live, closing the
   gap that `test_dungeon_scene_advance_107_1.py`'s `room_id_override` left open.

## Key Code Areas to Investigate

**The dead binding path (already built — wire it up):**
- `sidequest/server/dispatch/monster_manual_inject.py`
  - `inject(sd, snapshot, *, current_location, in_combat, room_id=None)` — the seam; `room_id`
    is the unused additive parameter (lines ~546–571).
  - `_npc_patches_for_room_binding(sd, room_id, current_location)` (~line 511) — resolves +
    materializes the room's bound creatures; only runs when `room_id` is non-None.
  - `_creature_patch_from_bestiary_entry(entry, location=...)` (~line 486) — stamps
    `manual_origin=True` and the authored name.
- `sidequest/server/dispatch/room_creature_binding.py`
  - `resolve_room_creatures(pack, world_slug, room_id)` — reads
    `{source_dir}/worlds/{world}/rooms/{room_id}.yaml`, validates ids, emits
    `monster_manual.room_bound`. Raises `RoomCreatureBindingError` on a dangling ref.

**The production caller (the wiring gap):**
- `sidequest/server/websocket_session_handler.py:830–867` — the ADR-059 injection block. Line
  843's `inject(...)` call omits `room_id`. This is where the entered room id must be resolved and
  threaded.

**Where the room id lives:**
- `sidequest/game/session.py`
  - `GameSnapshot.region_for(*, perspective=None)` (~line 1312) — per-PC graph region.
  - `pc_regions` (~line 1055), `current_region` (~line 908) — region state.
- `sidequest/dungeon/lookahead_worker.py:69` — `_ENTRANCE_ID = "entrance"`; `expNNN.rN` node-id shape.

**Authored content under test:**
- `sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden/rooms/entrance.yaml`
  — binds `encounter_creatures: [gnaw_swarm]`, three `entities`, the "easy first fight" affordance.

**Spans:**
- `sidequest/telemetry/spans/monster_manual.py` — `SPAN_MONSTER_MANUAL_ROOM_BOUND`,
  `SPAN_MONSTER_MANUAL_INJECTED`.

**Existing tests to extend (not replace):**
- `tests/integration/test_dungeon_scene_advance_107_1.py` — drives room entry with a
  `room_id_override`; the new wiring test must hit the real `inject()` call site instead.

## Technical Notes

- **ADR-059 (Monster Manual — server-side pre-generation via game-state injection):** the doctrine
  that the engine materializes creatures into `snapshot.npcs` BEFORE the narrator runs, so the
  gaslighting doctrine delivers them as world truth rather than an "available list." The per-room
  binding (107-2) is the precise placement seam this story activates — reuse it, do not author a
  parallel one.
- **ADR-106 (runtime procedural Jaquaysed megadungeon):** rooms are procedural region nodes
  (`entrance`, `expNNN.rN`). A procedural node may have NO authored room file at all — that's a
  legitimate non-binding room (`resolve_room_creatures` returns `[]`), and for those, depth-appropriate
  bestiary placement is the fallback intent. The entrance is the authored exception with a real binding.
- **ADR-106 Amendment A Layer 2 (degradation):** when curate degrades (153-26), the authored
  manifest is replaced by the deterministic `assemble_region` manifest and authored set-pieces /
  `encounter_creatures` can be lost upstream of placement. A wired placement path will find nothing
  to place under degradation — that's 153-26's fix, referenced here, not solved here.
- **epic-157 faction/zone (now archived):** the `zone_eligibility` / `region_cast_staging` layer is
  the *cast* (NPC) complement to creature placement; it skips procedural regions as `unknown_region`
  (153-27). Creature placement (this story) and cast staging (153-27) are siblings under ADR-059.
- **OTEL principle (CLAUDE.md):** the GM panel is the lie detector. A populated room with no span is
  indistinguishable from a winging narrator — every placement decision must emit.

## Story Scope

In scope:
- Thread the entered room/region id into the production `inject()` call so authored
  `encounter_creatures` are placed on room entry.
- Seed the encounter for a populated room and surface real loot vs. honest flavor.
- The wiring + OTEL ACs proving the path is live from a real play path.

Out of scope (reference only):
- The curate-timeout degradation that drops authored content (153-26).
- Procedural-region zone/cast eligibility (153-27).
- Any new spawn/curate/loot-table system — this is integration of the existing 107-2 / ADR-059
  placement path, not a reimplementation.
