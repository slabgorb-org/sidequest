# Story Context: 153-28 — beneath_sunden Authors Zero NPCs; Author the Surface-Camp Cast

## Story Metadata
- **Story ID:** 153-28
- **Epic:** 153 (Playtest follow-ups — open findings from the 2026-06-20/21 full-stack /sq-playtest sweep)
- **Type:** chore (content authoring)
- **Points:** 2
- **Workflow:** trivial
- **Repositories:** sidequest-content
- **Priority:** P2

## Problem Statement

`beneath_sunden` authors **zero NPCs**. Chargen logs:

```
pregen.authored_npcs_seeded (world=beneath_sunden, inserted=0, refreshed=0, total_authored=0)
```

Because there is no roster, **Brecca Half-Hand** — the camp boss / ledger-keeper who is named in chargen, speaks every turn, and runs the board of the unreturned — is pure narrator invention. With no roster entry and no disposition tracking, the narrator cannot hold her: on **Turn 2** it de-named her to "a woman by the shaft-side bench." The 6 entries that *do* surface come from `bestiary.yaml` (Monster-Manual creatures: undead, ooze, aberration, goblinoid, vermin), none of which is a named, persistent hub NPC.

This finding merges two ping-pong items (Brecca-loses-her-name + zero-authored-NPCs) because they share one root cause: **there is no `npcs.yaml` for this world.** Per ADR-059 the loader pre-injects authored NPCs as "present from session start, not yet met," giving the narrator a name-anchored, disposition-tracked entity it cannot drop. Brecca is plainly a **Diamond** (Diamonds-and-Coal, ADR-014): the load-bearing fixed point of the surface hub.

## Root Cause Direction

`beneath_sunden`'s world directory has no `npcs.yaml`. The server's seeding path
(`_seed_authored_npcs` in `pregen.py`) reads `pack.worlds[world].authored_npcs`,
which is empty, so `total_authored=0` and no NPC gets a registry entry or
disposition slot. The fix is **pure content**: author
`worlds/beneath_sunden/npcs.yaml` mirroring the shipped `AuthoredNpc` schema, homing
the cast at `ropefoot`. No engine change — the loader, seeder, and disposition
tracking already exist and fire unconditionally; they simply have nothing to read.

## Acceptance Criteria

1. **`npcs.yaml` exists and is well-formed:**
   - Create `genre_packs/caverns_and_claudes/worlds/beneath_sunden/npcs.yaml` with the
     shipped top-level shape: `version: "0.1.0"`, `world: beneath_sunden`, then a
     `npcs:` list.
   - Every entry validates against `AuthoredNpc` (`extra="forbid"`): keys limited to
     `id, name, pronouns, role, ocean, appearance, age, distinguishing_features,
     history_seeds, initial_disposition, location_tags`. No unknown keys.

2. **Brecca Half-Hand is authored as the camp-boss Diamond:**
   - One entry `id: brecca_half_hand`, `name: "Brecca Half-Hand"`, the camp boss /
     ledger-keeper, seven-delve veteran, missing three fingers — surfaced in the
     `appearance` / `distinguishing_features` / `history_seeds` prose.
   - `initial_disposition` set as a clearly-warm Diamond value (positive integer,
     `-100..100`), consistent with her being the player's anchor at the hub.
   - `location_tags: ["ropefoot"]` so the Monster Manual surfaces her at the surface camp.

3. **At least two more rope-keepers / stopped-going-down delvers are authored:**
   - ≥2 additional entries (e.g. the winch-keeper who counts the rope, a delver who
     has stopped going down and not yet left), each `location_tags: ["ropefoot"]`,
     each with distinct `id`/`name` and an `initial_disposition`.
   - Roster total ≥3 NPCs, all homed at `ropefoot`.

4. **Surface-camp framing only (spoiler discipline):**
   - All prose is camp-side (the winch-house, the kept fire, the board of the
     unreturned, the rigging benches). No dungeon secrets, no content about what is
     below `the_dropmouth` — the deep is procedurally generated (Plan-7) and not
     authored here.

5. **Validation / wiring AC:**
   - The pack validator passes with the new file:
     `cd sidequest-server && uv run python -m sidequest.cli.validate pack <abs path to>/genre_packs/caverns_and_claudes`
     reports no errors for `beneath_sunden`.
   - (Loader contract proof) the file loads cleanly: a server-side load of the
     `caverns_and_claudes/beneath_sunden` world materializes the roster without an
     `AuthoredNpc` `ValidationError` (the `extra="forbid"` + `id/name min_length=1` +
     `initial_disposition ge=-100/le=100` constraints all hold).
   - (Forward note, not a content-AC) a later `beneath_sunden` playtest should log
     `pregen.authored_npcs_seeded (... total_authored>=3)` and keep Brecca
     name-anchored past Turn 2 — this is the downstream effect, verified in playtest,
     not in this content PR.

## Authoring Targets

**File to CREATE (this story's only deliverable):**
- `sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden/npcs.yaml`

**Schema source of truth (read, do not edit):**
- `sidequest-server/sidequest/genre/models/authored_npc.py` — the `AuthoredNpc` pydantic
  model. Fields and constraints: `id` (min_length 1), `name` (min_length 1),
  `pronouns` (default ""), `role` (default ""), `ocean` (`dict[str,float] | None`),
  `appearance` (default ""), `age` (default ""), `distinguishing_features` (list),
  `history_seeds` (list), `initial_disposition` (int, default 0, `ge=-100 le=100`),
  `location_tags` (list of lowercase substrings). `extra="forbid"`.

**Schema exemplars to MIRROR (read, do not edit):**
- `sidequest-content/genre_packs/wry_whimsy/worlds/oz/npcs.yaml` — richest exemplar;
  shows the header doctrine block, `version`/`world`, OCEAN on a 0.0–1.0 scale, the
  bracketed-role-tag convention in `role:`, voice tics in `history_seeds`, and
  `location_tags` placement.
- `sidequest-content/genre_packs/tea_and_murder/worlds/glenross/npcs.yaml` — clean
  prose-driven exemplar (`initial_disposition`, `distinguishing_features`,
  multi-paragraph `history_seeds`).

**World context to GROUND the cast in (read, do not edit):**
- `sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden/cartography.yaml`
  — `starting_region: ropefoot`; the four `ropefoot` landmarks (The Winch-House, The
  Kept Fire, The Board of the Unreturned, the rigging benches) give the prose its
  anchors. The region id string to put in `location_tags` is exactly `ropefoot`.
- `worlds/beneath_sunden/world.yaml`, `history.yaml`, `lore.yaml`, `tropes.yaml` — for
  tone and the "people who keep the rope / have stopped going down" framing.
- `worlds/beneath_sunden/bestiary.yaml` — the existing 6 roster creatures (so the new
  NPCs are clearly distinct named individuals, not bestiary entries).

## Technical Notes

- **Names via namegen, never invented at authoring time** (per the `AuthoredNpc`
  module docstring and ADR-091). "Brecca Half-Hand" is **fixed by the chargen finding**
  (she is named in chargen and must keep that name) — author her verbatim. For the
  additional rope-keepers, if you need fresh given names, produce them with
  `python -m sidequest.cli.namegen` against the `caverns_and_claudes` culture rather
  than hand-coining.
- **`initial_disposition` is an integer −100..100** (ADR-020), not an enum — no
  friendly/neutral/hostile strings. See `docs/relationship-systems.md` for how it
  seeds the party's baseline standing.
- **`location_tags` is a lowercase substring match (case-insensitive, either
  direction)** carried to `ManualNpc.location_tags` at seed time. `["ropefoot"]` pins
  the cast to the surface camp; an empty list would make them "eligible everywhere"
  (legacy unplaced behavior) — do **not** leave it empty.
- **OCEAN convention:** `{ O, C, E, A, N }` on a 0.0–1.0 scale (matching glenross /
  oz / coyote_star). Optional, but recommended for the Diamond so the disposition
  engine has personality to work with.
- **No server change.** The seeding path (`_seed_authored_npcs` in
  `sidequest-server/sidequest/server/dispatch/pregen.py`, called by `seed_manual`) and
  the `pregen.seed_manual` OTEL span (`authored_npcs_seeded` attribute) already fire
  every session; they will pick the new roster up with zero code edits. The
  `total_authored=0` log line is the *symptom*, not a bug to patch.

## Story Scope

This story authors the **surface-camp cast only** for `beneath_sunden`. It does NOT:
- Author any NPC, region, or secret below `the_dropmouth` (the deep is procedurally
  generated — Plan-7 — and out of scope by world design).
- Touch any server code, the loader, the seeder, or OTEL emission (those already work).
- Add or modify `bestiary.yaml` creatures (those are creatures, not named hub NPCs).
- Author NPCs for any other world or pack.
- Run or verify a playtest (the downstream `total_authored>=3` / Brecca-stays-named
  proof is a separate playtest follow-up, noted in AC 5 as a forward expectation only).
