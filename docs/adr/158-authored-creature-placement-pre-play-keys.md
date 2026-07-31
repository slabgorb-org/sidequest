---
id: 158
title: "Authored Creature Placement Binds to Pre-Play Keys — `rooms/<id>.yaml` Is Engine-Written Runtime State, Not a Content Surface"
status: accepted
date: 2026-07-31
deciders: ["Keith Avery", "Naomi Nagata (Architect)"]
supersedes: []
superseded-by: null
related: [55, 59, 106, 109, 121, 140, 152, 155, 156, 157]
tags: [room-graph, game-systems, npc-character]
implementation-status: deferred
implementation-pointer: "docs/superpowers/specs/2026-07-31-authored-creature-placement-design.md"
---

# ADR-158: Authored Creature Placement Binds to Pre-Play Keys — `rooms/<id>.yaml` Is Engine-Written Runtime State, Not a Content Surface

## Context

Story 107-2 (2026-06) introduced a per-room creature binding to kill the
"creature of animal musk" Illusionism failure: the narrator improvising a
combat opponent with no mechanical backing. The mechanism it chose was a
top-level `encounter_creatures: [<bestiary_id>, ...]` list on
`genre_packs/<pack>/worlds/<world>/rooms/<room_id>.yaml`.

That mechanism cannot work, and has never worked outside one file. Four facts,
all verified against the tree on 2026-07-31:

1. **The engine WRITES that directory.**
   `sidequest/dungeon/room_yaml_emit.py::write_room_yaml`, called from
   `materializer.py::_stage_emit_room_yamls` (~`:2044`), writes
   `<world_dir>/rooms/<region_id>.yaml` after the expansion commit — into the
   *content repo's working tree* (`_resolve_world_dir` resolves the live pack
   root via `GenreLoader`). The emitted payload carries `room_type` / `name` /
   `description` / `entities` and **no** `encounter_creatures`. The content
   repo is being used as a runtime scratch directory.

2. **Content therefore cannot commit into it.** `sidequest-content/.gitignore:88`
   blanket-ignores `genre_packs/**/worlds/*/rooms/*.yaml` — added by commit
   `3cafb30` (2026-05-20, "chore: gitignore procedural megadungeon room YAMLs",
   #240), which simultaneously untracked nine spilled `exp00*.r*.yaml` files.
   Line 90 whitelists exactly one filename: `!genre_packs/**/worlds/*/rooms/entrance.yaml`.
   Repo-wide, across 22 worlds, **one** room file is tracked:
   `caverns_and_claudes/worlds/beneath_sunden/rooms/entrance.yaml`. No other
   world even has a `rooms/` directory.

3. **The room id does not exist before play.** ADR-106 makes the megadungeon
   runtime-procedural: region ids (`exp001.r3`) are minted by edge-expansion at
   materialization. An author cannot bind a creature to `exp001.r3` because
   `exp001.r3` will not exist until a particular party pushes the frontier a
   particular way. Room ids are not an addressable content namespace.

4. **Authoring effort has already been silently destroyed by this.** The local
   working tree carries five *hand-authored* `encounter_creatures` bindings
   (`exp001.r0` → `rope_spider`, `.r1` → `shaft_goblin`, `.r2` → `hold_skeleton`,
   `.r3` → `grave_ghoul`, `.r4` → `harrier_pack_leader` + `shaft_goblin`) in
   gitignored files. `write_room_yaml` never emits that key, so a human wrote
   them; git will never see them; the next clean clone loses them. This is not
   hypothetical drift — it is the failure mode, already realized.

The consequence is a live Illusionism hole. Every consumer —
`dungeon/materializer.py::_append_authored_creatures` (`:1071`, main path per
ADR-106 Amendment C), `dungeon/lookahead_worker.py:382`,
`dungeon/session_integration.py:201`, `server/websocket_session_handler.py:847`,
`server/dispatch/monster_manual_inject.py:806/1001` — routes through
`room_creature_binding.resolve_room_creatures`, which reads
`{pack.source_dir}/worlds/{world}/rooms/{room_id}.yaml`. On a clean checkout
that file is absent for every room in the dungeon except `entrance`, and the
absent-file branch (`room_creature_binding.py:61-65`) returns `[]` **with no
log, no span, and no counter** — the one genuinely *silent* fallback in the
chain, and the default state for 32 of 33 rooms. A *broken* binding gets a
routed `dungeon.curate.authored_bind_failed` span; an *absent* one gets
silence, and `_stage_curate`'s summary records `creature_count` without ever
distinguishing authored from procedural. `monster_manual_inject` then falls
through to `mm.encounters` — the flat unfiltered pool that is the original
107-2 bug. The narrator improvises, and the GM panel cannot see that it did.
That is a direct violation of *No Silent Fallbacks* and of the OTEL principle,
on the exact subsystem both were written for.

**A test is lying about it.**
`sidequest-server/tests/genre/test_beneath_sunden_room_binding_107_2.py`
globs `rooms/*.yaml` on disk. `test_distinct_rooms_bind_distinct_creatures`
passes on this machine *only* because of the five uncommittable hand edits in
fact 4, and goes RED on a clean clone. A content gate whose verdict depends on
whether the developer has played the game is not a gate.

**And the authored surface that WAS designed for this is dead content.**
ADR-106 clause 6 already ruled: *"Authored theme palette, procedural placement.
The pack ships a curated `themes/` directory (interior algorithm + params,
**creature/loot tables**, narrator register, depth-band eligibility, adjacency
affinities, a set-piece library). The generator chooses, places, and connects."*
`beneath_sunden` ships eight tracked `themes/*.yaml`, each carrying a
`creature_table:` of `{ref, weight, depth_band}` rows. The server parses it into
`DungeonTheme.creature_table` (`sidequest/dungeon/themes.py:242`) — and **no
production code reads it.** A full-repo grep for `creature_table` returns the
declaration and two test files. Nothing else.

And because nothing reads it, nothing validates it: of the **17
`creature_table` refs across the eight themes, 10 are dangling** — `bone_drake`,
`crypt_warden`, `blind_cave_eel`, `drowned_revenant`, `minotaur_of_the_deep`,
`starved_seeker`, `temple_acolyte_shade`, `altar_horror`, `ossuary_crawler`,
`lamp_wight` exist in no `bestiary.yaml` (192 entries), no `creatures.yaml`, no
`corpus/`. Five of the eight themes — `bone_crypt`, `drowned_cavern`,
`labyrinth_trap`, `sunless_temple`, `winding_catacomb` — resolve **zero**
creatures. Only `animated_armory`, `fungal_warren`, and `skeleton_tomb` have
tables that would work if anything read them.

The two keys needed to consume that surface are already on the region:
`RegionNode` (`dungeon/region_graph/model.py:16-21`) carries `theme` and
`depth_score`, and `CreatureEntry.depth_band` is expressed in the same raw
`depth_score` units the region freezes at attach.

So 107-2 built a second authoring surface, in a directory the engine writes to,
keyed on ids that do not exist, while the surface ADR-106 specified sat parsed
and unread with dangling refs.

## Decision

**Authored creature placement binds to a key that exists before play. A
procedural room id is not such a key and never becomes one.
`worlds/<world>/rooms/` is engine-written runtime state and holds no authored
content.**

### D1 — Three pre-play binding keys, all already committable

Every axis below already exists in tracked content. This ADR adds no new file
format and no new content directory.

| Binding key | Committable surface | Serves | Status today |
| --- | --- | --- | --- |
| **theme + depth band** | `worlds/<w>/themes/<theme>.yaml` → `creature_table: [{ref, weight, depth_band}]` | procedural megadungeon regions (ADR-106) | authored, parsed, **unread**; 10 of 17 refs dangling |
| **authored region id** | `worlds/<w>/encounter_tables.yaml` → `tables: {<cartography region id>: {encounters: [...]}}` | static/cartography worlds | live; `pack_schema.yaml` `world.extensions`; 2-world precedent (`flickering_reach`, `seaboard_of_saints`) |
| **anchor room id** | `worlds/<w>/anchor_rooms/<id>.yaml` → `encounter_creatures: [...]` (see D4) | rooms that exist before generation (`entrance`) | today `rooms/entrance.yaml` under a filename-specific gitignore negation |

`theme` is the correct key for a procedural dungeon precisely because it is what
the author *can* know: the generator picks a theme and a depth band for a region
at attach, and both are authored vocabulary. `exp001.r3` is not.

`encounter_tables.yaml` is **not** extended to the megadungeon. Its keys are
`cartography.yaml` region ids, which for `beneath_sunden` are two surface regions
(`ropefoot`, `the_dropmouth`); the deep has no cartography regions by design.
Region-keyed tables would hit the same does-not-exist-before-play wall as room
ids. Two axes, two surfaces, one rule.

### D2 — The id space for authored creature placement is the world bestiary

Every `creature_table[].ref`, every `encounter_creatures` id, and every
`encounter_tables` `creature:` MUST resolve to an id in the world's effective
bestiary (`pack.effective_bestiary(world)`). This is already what
`resolve_room_creatures` enforces for room bindings, what ADR-155 established for
render derivation, and what ADR-140 means by "the world owns the catalog." A
dangling ref is a **load-time authoring error**, not a runtime shrug — see D6.

The `cookbook/` + `corpus/monsters.yaml` stack is **not** an authoring surface
for placement. It is the SRD-derived weighting/sizing machinery
(`affinities.yaml::cr_bands` / `look_race_affinity` / `size_by_burst`,
`looks.yaml`, `races/`) that `assemble_region` uses to *shape* a draw. Under this
ADR it keeps that job and loses the job of *choosing which creatures exist in
this world's dungeon* — that is the theme table's job, and the bestiary's id
space. This resolves the standing two-roster ambiguity (192-entry world bestiary
vs 2598-line SRD corpus) in favour of the bestiary, consistent with ADR-155 and
ADR-059's addendum.

### D3 — Runtime resolution: derive once at materialization, freeze, never re-read disk

A region's creature roster is produced **at materialization** and **frozen into
the committed expansion**, exactly as ADR-106 Amendment C already established for
the deterministic curate stage:

```
region roster :=
    theme := palette.theme_for(region)
    pool  := theme.creature_table
             |> filter depth_band contains region.depth_score
             |> filter ADR-152 faction/zone eligibility
    seeded weighted draw, sized by affinities.size_by_burst
    ∪ set-piece creature slots resolved at attach (ADR-106 clause 7)
    → frozen RegionCreature rows in the committed expansion
```

Consequences for the existing seams:

- `_append_authored_creatures` **stops reading `rooms/<id>.yaml`** for procedural
  regions. Its authored-binding read narrows to anchor rooms (D4).
- `resolve_room_creatures` becomes an **anchor-room** resolver. For a procedural
  region it does not touch the filesystem; the roster is already in the save.
- `monster_manual_inject`'s room-binding patch builder reads the frozen roster
  from the region record, not a YAML file. Its ADR-156 **tier-2 (room-bound)**
  candidates therefore come from anchor rooms; the theme-derived roster enters at
  **tier 3 (region-population)** — "a placed, frozen, deterministic roster,"
  which is exactly what it now is. ADR-156's ladder is unchanged; only the
  *source* of each tier's candidates is corrected.
- Determinism is preserved and strengthened: same seed ⇒ same roster (ADR-106
  Amendment C), and the roster no longer varies with whether a developer's
  working tree happens to contain spilled room files.

### D4 — Authored anchor rooms move out of `rooms/`; the gitignore exception is deleted

An **anchor room** is a room that exists before generation: a fixed, authored
node the materializer never emits. Today there is exactly one per megadungeon
world (`entrance`, the surface-seam landing from the 105-2 seam registry).

Anchor rooms move to `worlds/<world>/anchor_rooms/<id>.yaml` — same file shape,
new directory. `rooms/` becomes **100% engine-written**, gitignored with no
exceptions, and `.gitignore:90`'s `!.../rooms/entrance.yaml` negation is removed.

One resolution helper, used by every reader and by the emit freeze-check:

```
resolve_room_source(world_dir, room_id) -> Path | None
    anchor := world_dir / "anchor_rooms" / f"{room_id}.yaml"
    return anchor if anchor.is_file() else (runtime := world_dir / "rooms" / f"{room_id}.yaml") if runtime.is_file() else None
```

An anchor file is authoritative: `_stage_emit_room_yamls` must not emit a
`rooms/<id>.yaml` for a room that has an anchor file (the freeze invariant,
extended one directory).

**Why not keep the negation** (the zero-code option): it does not generalize. A
world wanting a second authored anchor — a hub landing, a second seam, a second
megadungeon world with a differently-named entrance — cannot commit it without
editing `.gitignore`. That is repo configuration, not content, and it breaks the
load-bearing requirement that an author (Jade) can add what a table wants as
content without touching engine or repo plumbing (ADR-140). It also leaves
authored content living in a directory the engine writes to, which is precisely
how the five bindings in Context fact 4 were lost. A directory split makes
authored-vs-runtime a git-visible, structural fact instead of a magic filename.

### D5 — Wire `ThemePalette.creature_table` or delete it; this ADR wires it

`creature_table` is parsed content with zero production consumers. Per *No
Stubbing* ("dead code is worse than no code") and *Don't Reinvent — Wire Up What
Exists*, it must not stay in that state. This ADR wires it as the D3 pool.
Its 10 dangling refs are repointed to real `bestiary.yaml` ids as part of the
same work — a content job at a committable tier, which is what story 158-63 was
always really asking for.

`_append_authored_creatures` is the correct seam and is kept: it already runs
per-region on the deterministic main path, already merges by name against the
procedural roster, and already has a routed failure span. What changes is the
resolver it calls, not the call site.

Note a loading constraint the spec must honour: `load_theme_palette`
(`themes.py:314`) is deliberately standalone and **not** wired into
`load_genre_pack` (ADR-157 depends on that separation). The D6 referential
validator therefore runs in `sidequest.cli.validate` and in CI, not inside
`load_genre_pack` — the pack load stays theme-agnostic.

### D6 — Fail loud at load time; never hand the narrator an unfiltered pool

- **Authoring validator (`sidequest.cli.validate` + CI, fails the pack):** every
  `creature_table[].ref`, every anchor-room `encounter_creatures` id, and every
  `encounter_tables` `creature:` resolves to a real bestiary entry; and every
  theme has at least one `creature_table` row eligible at every depth it is
  itself eligible for. A theme that can produce no creature at a depth it can be
  placed at is an authoring hole, caught before play, not a runtime empty pool.
  This runs on the same footing as ADR-152's untagged-content validator, and it
  is RED today on the 10 dangling refs — which is the point.
- **Materialization:** a region whose eligible pool is empty raises loudly
  (`CurationError`, ADR-106 Amendment C's retained carve-out (i) — a structurally
  invalid assembled input is a content bug, never degraded).
- **Runtime:** the "absent binding ⇒ silent `[]` ⇒ unfiltered Available pool"
  path is **deleted**. A region always has a frozen, theme-sourced roster. If the
  roster is somehow empty at seat time, that is a loud failure per ADR-156 §5 —
  the sanctioned last resort is a bestiary `generics:` row (story 162-3), never
  improvisation.
- **OTEL (the lie detector):** `dungeon.materialize.curate` carries
  `roster_source` ∈ {`theme_table`, `set_piece`, `anchor`}, the theme id, the
  depth band, and the drawn bestiary ids. `monster_manual.room_bound` is retained
  for anchor rooms and gains `source="anchor"`. There is no longer any path on
  which a region's roster is chosen without a span saying where it came from —
  which is the specific property the current absent-binding silence destroys.

### D7 — Schema-sanction the surfaces an author must be able to find

`sidequest-content/pack_schema.yaml` lists neither `themes` nor `bestiary` under
`world.extensions`, despite `bestiary.yaml` being tracked in 20 of 22 worlds and
`themes/` being the surface this ADR makes load-bearing.
`beneath_sunden/world.yaml` likewise declares `extensions: [creatures, rooms,
cookbook, world_register]` — omitting both. Add `themes` (dir), `bestiary`
(file), and `anchor_rooms` (dir) to `world.extensions`; remove `rooms` (it is
runtime state, not an extension). An author cannot be expected to use a surface
the schema does not admit exists.

## Invariants / Contracts

- **`worlds/<w>/rooms/` contains only engine-written files.** No authored
  content, no gitignore exceptions. Anything a human writes there is lost by
  design.
- **A binding key must exist before play.** Theme, depth band, cartography region
  id, and anchor room id qualify. A procedural region id does not.
- **The bestiary is the id space** for every authored creature reference in a
  world (ADR-140 catalog ownership, ADR-155 derivation precedent).
- **Rosters are derived once, frozen, and read from the save** — never re-read
  off the content directory at turn time.
- **Dangling refs and empty eligible pools fail at pack load, loudly and by
  name.** No runtime fallback to an unfiltered pool.
- **ADR-156's origin-precedence ladder is unchanged.** Tier 2 (room-bound) is
  sourced from anchor rooms; tier 3 (region-population) is sourced from the
  frozen theme-derived roster.

## Consequences

**Positive**

- The Illusionism hole closes for the whole dungeon, not one room. Every region
  fields creatures a human chose, from a file a human can commit.
- Authoring effort stops being destroyed. The five hand-authored bindings in
  Context fact 4 become one theme-table edit each, in tracked files.
- ADR-106 clause 6 becomes true in code for the first time — "authored theme
  palette, procedural placement" stops being an aspiration and a parsed-but-unread
  model field.
- The content repo stops being a runtime scratch directory for authored paths;
  authored-vs-runtime becomes a directory boundary git can see.
- The two-roster ambiguity (world bestiary vs SRD corpus) is resolved in favour
  of the bestiary, aligning the runtime roster with ADR-155's render roster —
  a bound creature now has a portrait by construction.
- Jade's requirement holds: adding the crunch a table wants is a theme-file edit
  plus a bestiary entry. No server change, no `.gitignore` change.
- Sebastien/Jade's mechanics-first read of the player UI improves: the seated
  opponent is an authored entity with a stat line and a name, every time.

**Negative / accepted cost**

- **The content job is bigger than 107-2 assumed.** Eight themes × a real
  creature table, with all 15 existing refs repointed to bestiary ids. That is
  the honest size of "the dungeon fields authored creatures"; the 33-room framing
  was an artifact of counting runtime spill.
- **`rooms/entrance.yaml` moves.** One file relocation plus a small resolver
  change across three read sites and the emit freeze-check.
- **Theme granularity is coarser than room granularity.** An author cannot say
  "this exact creature in this exact room" for a procedural room — by design, the
  room does not exist yet. The escape hatch is a **set-piece** (ADR-106 clause 7),
  which is exactly the authored-specific-placement mechanism the spec already
  provides, and which the theme files already carry.
- A migration window where the theme tables exist but are still refless would
  fail the D6 validator; the validator lands with the content, not before it
  (the ADR-152 sequencing pattern).

**Neutral**

- ADR-157 is untouched: a bounded site remains cookbook-free and
  materializer-creature-free. This ADR governs the `extent: frontier` path only.
- ADR-059's Monster Manual injection mechanism, ADR-152's eligibility predicate,
  and ADR-156's Green Room gate are all unchanged. This ADR only corrects where
  candidates come from.

## Alternatives Considered

**A — Carve more gitignore exceptions for "genuinely authored" rooms.**
*Rejected.* It requires a rule distinguishing authored from procedural files in a
directory the engine writes to, and no such rule can be enforced by git — the
engine emits into the same namespace. It also keeps binding to ids that do not
exist before play, so it cannot cover a dungeon that grows without bound: an
author would be chasing the frontier, committing bindings for rooms after the
fact. That is the opposite of ADR-106.

**B — Commit the whole materialized dungeon as content (drop the procedural
model for `beneath_sunden`).** *Rejected.* It reverses ADR-106's central
decision, and ADR-106 clause 9 is explicit that the save is the source of truth
and the dungeon is not byte-reproducible content. It would also freeze one
party's dungeon as every party's dungeon.

**C — Extend `encounter_tables.yaml` to procedural regions.** *Rejected.* Its
keys are cartography region ids. Keying it on `exp001.r3` reproduces the
does-not-exist-before-play problem in a schema-sanctioned file, which is worse
than the current state because it looks legitimate. `encounter_tables.yaml`
remains correct and unchanged for the worlds it already serves.

**D — Keep `rooms/<id>.yaml` bindings and have the materializer WRITE
`encounter_creatures` into the files it emits.** *Rejected — this is the trap.*
It would make `test_distinct_rooms_bind_distinct_creatures` green on any machine
that has played, and it would be pure circularity: the engine writing its own
procedural choice into a file, then reading it back and calling it "authored."
The GM panel would show a room-bound span for a creature no human ever chose.
That is Illusionism with a paper trail — strictly worse than the current honest
gap.

**E — Keep the `!entrance.yaml` gitignore negation and add a validator that
tracked room files are declared anchors.** *Rejected, though it is the
zero-code option.* See D4: it does not generalize past the single magic
filename, requires a repo-config edit to author a second anchor, and leaves
authored content in an engine-written directory. The directory split costs one
small helper and deletes a special case.

## Answers to the five questions this ADR was filed against (story 158-70)

1. **Where do authored bindings live?** `worlds/<w>/themes/<theme>.yaml`
   `creature_table` for procedural regions; `worlds/<w>/encounter_tables.yaml`
   for authored cartography regions; `worlds/<w>/anchor_rooms/<id>.yaml` for
   rooms that exist before generation. All tracked, all world-tier, all
   homebrewable (D1).
2. **How does the materializer resolve a room's creatures?** Theme + depth band →
   eligibility-filtered, seeded weighted draw from the theme table (bestiary id
   space), sized by `affinities.size_by_burst`, plus set-piece slots, frozen into
   the committed expansion at materialization and read from the save thereafter
   (D3).
3. **What should the test assert?** See the spec §4. In short: the disk glob dies;
   `entrance` asserts against the one tracked anchor file; the
   distinct-rooms claim becomes a fixture-driven materializer behavior test over
   the tracked theme palette; referential integrity becomes a validator over
   theme tables + anchor bindings (which is RED today on 15 dangling refs, as it
   should be).
4. **Is `entrance.yaml`'s tracked status the right precedent?** The *instinct* is
   right — an anchor room is genuine pre-play content and the negation on
   `.gitignore:90` was a deliberate, commented decision, not an accident. The
   *mechanism* is wrong: it is a magic filename inside an engine-written
   directory. D4 regularises it by giving anchor rooms their own directory and
   deleting the exception.
5. **Re-plan for 158-63:** see the spec §6.

## Implementation

Design detail, migration order, test replacement, and the story decomposition
live in
[`docs/superpowers/specs/2026-07-31-authored-creature-placement-design.md`](../superpowers/specs/2026-07-31-authored-creature-placement-design.md).
