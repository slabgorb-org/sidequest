# Authored Creature Placement — Implementation Design

**Date:** 2026-07-31
**Author:** Architect (Naomi Nagata)
**Status:** Design accepted; implementation unstarted
**ADR of record:** [ADR-158](../../adr/158-authored-creature-placement-pre-play-keys.md)
**Repos:** server (resolver + validator + tests), content (theme tables + anchor move + gitignore + schema)
**Filed for:** story 158-70 (design), re-plans story 158-63

---

## 0. The decision in one sentence

A dungeon region's creatures come from its **theme's authored `creature_table`**,
filtered by depth band and zone eligibility, drawn deterministically and frozen
at materialization; `worlds/<w>/rooms/` becomes 100% engine-written runtime state
and the only authored room files — anchors like `entrance` — move to
`worlds/<w>/anchor_rooms/`.

---

## 1. Verified ground truth (2026-07-31, `origin/develop` + working tree)

| Fact | Evidence |
| --- | --- |
| The server writes room YAMLs into the content working tree | `dungeon/room_yaml_emit.py:41-73` ← `dungeon/materializer.py::_stage_emit_room_yamls:2044`; destination resolved via `GenreLoader.find()` in `_resolve_world_dir:2088` |
| The writer cannot emit `encounter_creatures` | payload literal, `room_yaml_emit.py:66-72` — `room_type`/`name`/`description`/`entities` only |
| Content cannot commit into `rooms/` | `sidequest-content/.gitignore:88`, negation `:90` for `entrance.yaml` only; commit `3cafb30` (2026-05-20, #240) untracked 9 spilled files |
| One tracked room file repo-wide | `git ls-files` over all 22 worlds → `caverns_and_claudes/worlds/beneath_sunden/rooms/entrance.yaml`; no other world has a `rooms/` dir |
| Five hand-authored bindings are uncommittable | untracked `exp001.r0..r4` carry `encounter_creatures`; `write_room_yaml` never emits that key, so a human wrote them |
| Absent binding is a *silent* fallback | `server/dispatch/room_creature_binding.py:61-65` returns `[]` with no log/span/counter |
| Present-but-broken binding is loud | `materializer.py:1111-1131` → ERROR log + `dungeon.curate.authored_bind_failed` span |
| `DungeonTheme.creature_table` has zero production readers | `dungeon/themes.py:242`; full-repo grep = declaration + `tests/dungeon/test_themes.py` + `tests/dungeon/test_materialize_bounded.py` |
| 10 of 17 theme creature refs are dangling | `bone_crypt`, `drowned_cavern`, `labyrinth_trap`, `sunless_temple`, `winding_catacomb` resolve **zero**; `animated_armory`, `fungal_warren`, `skeleton_tomb` fully resolve |
| The region already carries the keys | `RegionNode{id, expansion_id, theme, depth_score}` — `dungeon/region_graph/model.py:16-21` |
| Depth units already agree | `CreatureEntry.depth_band` (`themes.py:161-177`) is in raw `depth_score` units (`region_graph/depth.py`, `depth_per_hop=10.0`) |
| The theme palette is world-tier | `dungeon/session_integration.py::_theme_pack_root:85-94` returns `world_dir` (ADR-140) |
| Theme loading is deliberately outside pack load | `dungeon/themes.py:271-278, 346-363` — `load_theme_palette` is standalone; ADR-157 relies on it |
| `encounter_tables.yaml` is the schema-sanctioned region-keyed surface | `sidequest-content/pack_schema.yaml` `world.extensions`; live in `mutant_wasteland/{flickering_reach,seaboard_of_saints}`, keys == `cartography.yaml` region ids |
| `themes`, `bestiary`, `anchor_rooms` are NOT in the world schema | `pack_schema.yaml` `world.extensions` lists `rooms`, `cookbook`, `creatures`, `encounter_tables`, … but not `themes` or `bestiary` |

---

## 2. Resolution algorithm

### 2.1 Materialization (once per region, frozen)

Runs inside `_stage_curate`, replacing the `_append_authored_creatures` room-YAML
read. Pure, seeded, no I/O beyond the already-loaded palette:

```
resolve_region_roster(node: RegionNode, palette: ThemePalette,
                      bestiary, cartography, rng) -> list[CuratedCreature]:

    theme := palette.themes[node.theme]            # loud KeyError — no default theme

    pool  := [row for row in theme.creature_table
                 if row.depth_band contains node.depth_score
                 and zone_eligibility.is_eligible(bestiary[row.ref], region=node)]   # ADR-152

    if not pool:  raise CurationError(theme.id, node.depth_score)   # ADR-106 Amdt C carve-out (i)

    n     := affinities.size_by_burst(expansion.burst_magnitude).wandering_rolls
    draws := rng.weighted_sample_with_replacement(pool, key=row.weight, k=n)

    return [curated_from_bestiary(bestiary[row.ref]) for row in dedupe_by_id(draws)]
```

Then, unchanged from today, set-piece creature slots resolved at attach
(ADR-106 clause 7) are unioned in, and the result is written to
`region_population` in the same commit transaction
(`materializer.py::_stage_commit`, `RegionCreature` rows).

**Explicitly out of the roster path:** `corpus/monsters.yaml` and
`cookbook/look_race_affinity`. They keep their jobs — CR banding
(`affinities.cr_bands` → `_threat_from_band`, `materializer.py:324`), size
budgeting (`size_by_burst`), loot, look/dressing — and lose the job of choosing
which creatures inhabit this world's dungeon. That job is the theme table's,
in the bestiary id space (ADR-158 D2).

**HP:** keep the existing `_hp_from_cr` path only where a corpus row is still
the source (loot/big-bad shaping). A bestiary-sourced creature already carries
an SRD/WWN-aligned `hp`, `armor_class`, `attack_bonus`, `damage`, `morale`,
`save` — use the authored stat line verbatim. Do not re-derive it. (SOUL: *Bind
the Ruleset, Don't Balance It*.)

### 2.2 Turn time (read the save, not the disk)

- `monster_manual_inject._npc_patches_for_region_population` already reads the
  frozen `RegionCreature` rows. It becomes the primary creature feeder for
  procedural regions — ADR-156 **tier 3**, unchanged in rank.
- `_npc_patches_for_room_binding` narrows to **anchor rooms** and keeps ADR-156
  **tier 2**. It calls the new `resolve_anchor_room_creatures`.
- The `if room_id and combat_encounters` gate at `monster_manual_inject.py:1121`
  is preserved.

### 2.3 The anchor-room seam

```python
def resolve_room_source(world_dir: Path, room_id: str) -> Path | None:
    anchor = world_dir / "anchor_rooms" / f"{room_id}.yaml"
    if anchor.is_file():
        return anchor
    runtime = world_dir / "rooms" / f"{room_id}.yaml"
    return runtime if runtime.is_file() else None
```

Three call sites repointed: `game/room_file_loader.py:64` (prose/entities),
`server/dispatch/room_creature_binding.py:60` (bindings), and
`dungeon/materializer.py::_stage_emit_room_yamls:2072` (freeze check — a room
with an anchor file is never emitted into `rooms/`).

`room_id` stays the lookup key, so `_ENTRANCE_ID = "entrance"` and the 105-2 seam
registry are untouched.

### 2.4 Fail-loud changes (No Silent Fallbacks)

| Today | After |
| --- | --- |
| absent room file → `[]`, no log, no span | absent **anchor** file → `[]` **plus** `monster_manual.room_bound` with `bound_count=0, source="none"` on the anchor path; and the procedural path no longer consults files at all |
| absent binding → flat `mm.encounters` pool | deleted; region always has a frozen theme-sourced roster |
| `RoomCreatureBindingError` caught in materializer, **uncaught on the turn path** (`websocket_session_handler.py:823` has `finally` with no `except`) | caught on both paths with the same loud-but-graceful contract; a dangling anchor ref never escapes a turn |

---

## 3. Content migration (`sidequest-content`)

1. `git mv genre_packs/caverns_and_claudes/worlds/beneath_sunden/rooms/entrance.yaml`
   → `.../beneath_sunden/anchor_rooms/entrance.yaml` (content unchanged).
2. `.gitignore`: delete the `!.../rooms/entrance.yaml` negation (line 90) and its
   comment. `rooms/*.yaml` stays blanket-ignored, now with no exceptions.
3. Repoint the **10 dangling** `creature_table` refs to real `bestiary.yaml` ids
   and fill out the five zero-resolving themes. This is the real content work —
   see §6 for how it decomposes. Author against the bestiary's informal band tags
   (`low`/`mid`/`deep`) and the theme's own `depth_band`, so a shallow theme
   fields low-band creatures.
4. `pack_schema.yaml` `world.extensions`: add `themes` (dir), `bestiary` (file),
   `anchor_rooms` (dir); remove `rooms` (runtime state, not an extension).
   Reconcile with `GENRE_PACK_ROOT_EXTENSION_FILES` — the drift guard
   `test_pack_schema_loader_drift_113_2.py` will catch a mismatch.
5. `beneath_sunden/world.yaml` `extensions:` currently declares
   `[creatures, rooms, cookbook, world_register]`. Update to
   `[creatures, anchor_rooms, cookbook, world_register, themes, bestiary]`.
6. Optionally delete the 32 untracked `exp*.r*.yaml` from local trees; they are
   regenerable and now unread on the binding path.

**Do not** author the five hand-edited `exp001.r*` bindings anywhere. Their
intent (rope_spider / shaft_goblin / hold_skeleton / grave_ghoul /
harrier_pack_leader as early-descent opposition) is preserved by putting those
ids in the shallow-band `creature_table` of the themes those regions draw.

---

## 4. Test replacement — `test_beneath_sunden_room_binding_107_2.py`

The file's `_room_bindings()` helper globs the gitignored `rooms/` directory.
Every assertion built on it is environment-dependent. Replacement, test by test:

| Existing test | Verdict | Replacement |
| --- | --- | --- |
| `test_entrance_room_binds_the_gnaw_swarm_first_fight` | **Keep, retarget** | read the single tracked file `anchor_rooms/entrance.yaml` by explicit path (no glob); assert `encounter_creatures` contains `gnaw_swarm`. Deterministic on a clean clone. |
| `test_some_rooms_declare_creature_bindings` | **Delete** | subsumed by the above and by the theme-table coverage test below; its premise ("at least one room file declares a binding") is now meaningless. |
| `test_distinct_rooms_bind_distinct_creatures` | **Delete from this file; replace with a behavior test** | see §4.1. Its real claim — *not a flat pool everywhere* — is a materializer property, not a content-file property, and cannot be asserted by reading files. |
| `test_all_room_bindings_reference_real_bestiary_ids` | **Keep, widen** | referential integrity over the *committable* surfaces: every `themes/*.yaml` `creature_table[].ref` **and** every `anchor_rooms/*.yaml` `encounter_creatures` id resolves to a bestiary entry. **RED today: 10 dangling refs.** That RED is correct and is the content story's gate. |
| `test_bound_creatures_are_renderable` | **Keep, widen** | renderable set = union of anchor bindings + theme `creature_table` refs; renderability per ADR-155 (non-empty bestiary `description` + naming handled by `name_is_secret`/override), not "present in `creatures.yaml`". |

Plus one new content test:

- `test_every_theme_can_field_a_creature_at_every_depth_it_is_eligible_for` —
  for each tracked theme, for each depth sampled across its own `depth_band`,
  the eligible `creature_table` subset is non-empty. Catches the
  five-zero-resolving-themes class of hole at author time.

### 4.1 The replacement behavior test (server, `tests/dungeon/`)

`test_region_rosters_are_theme_sourced_and_distinct_158_63.py` — fixture-driven,
per `sidequest-server/CLAUDE.md` (no source-text wiring tests, no disk globs of
runtime state):

1. Load the **tracked** `beneath_sunden` theme palette via `load_theme_palette`.
2. Materialize two regions with **different themes** (and one pair with the same
   theme at **different depth bands**) from one fixed `campaign_seed`, through
   the real `materialize()` path with a synthetic dungeon store.
3. Assert: each region's frozen `region_population` is **non-empty**; every
   `creature_id` is a member of that region's theme `creature_table` (proves
   authored-sourced, not improvised); and the two different-theme rosters
   **differ** (proves not-a-flat-pool).
4. Assert determinism: re-materialize from the same seed → identical rosters
   (ADR-106 Amendment C).
5. Assert OTEL: `dungeon.materialize.curate` fired per region carrying
   `roster_source="theme_table"` and the theme id — the GM-panel lie detector.

This is green on a clean clone (theme YAMLs are tracked), refactor-stable, and
tests the property 158-63 actually cares about.

---

## 5. OTEL

| Span | Change |
| --- | --- |
| `dungeon.materialize.curate` | **new attrs** `roster_source` ∈ {`theme_table`,`set_piece`,`anchor`}, `theme_id`, `depth_score`, `creature_ids[]`, `pool_size`, `pool_filtered_by_eligibility` |
| `monster_manual.room_bound` | **retained**, gains `source="anchor"`; now also fires with `bound_count=0` so an anchor room with no binding is visible, not silent |
| `dungeon.curate.authored_bind_failed` | **retained** for anchor-binding failures |
| `zone_eligibility.filtered` | **reused** (ADR-152) when the theme pool is narrowed |
| *new* `dungeon.curate.pool_empty` | alarm before the `CurationError` raise, naming theme + depth |

Acceptance is span-based, not source-grep: drive a descent and confirm every
region's roster carries `roster_source="theme_table"` and a theme id. A region
without one is the lie.

---

## 6. Re-plan for story 158-63

**158-63 as written is not actionable and should be closed as superseded.** Its
premise ("33 rooms lack `encounter_creatures`") counted runtime spill, and its
`repos: content` framing cannot be satisfied — the directory it targets is
gitignored by design. Replace it with the following, filed against ADR-158.

| # | Title | Repos | Pts | Type | Depends on |
| --- | --- | --- | --- | --- | --- |
| **A** | Anchor-room split: `anchor_rooms/` directory + `resolve_room_source` helper; repoint `room_file_loader`, `room_creature_binding`, `_stage_emit_room_yamls`; move `entrance.yaml`; delete the `.gitignore` negation | server, content | 3 | chore | — |
| **B** | Author the theme creature tables: repoint 10 dangling refs, fill the 5 zero-resolving themes, band-align against `bestiary.yaml` | content | 3 | feature | — |
| **C** | Referential + coverage validator over `themes/*.yaml` `creature_table` and `anchor_rooms/*` bindings, in `sidequest.cli.validate` + the retuned `test_beneath_sunden_room_binding_107_2.py` (§4) | server | 3 | test | B |
| **D** | Wire `DungeonTheme.creature_table` into `_stage_curate`: `resolve_region_roster` (§2.1) replaces the room-YAML read in `_append_authored_creatures`; delete the silent absent-file `[]` path; OTEL per §5 | server | 5 | feature | A, B |
| **E** | Behavior test `test_region_rosters_are_theme_sourced_and_distinct_158_63` (§4.1) — the permanent regression guard and the real AC3 | server | 3 | test | D |
| **F** | Schema sanction: `pack_schema.yaml` `world.extensions` += `themes`/`bestiary`/`anchor_rooms`, −`rooms`; update `beneath_sunden/world.yaml` `extensions` | content | 1 | chore | A |

**Ordering:** A and B in parallel → C (RED until B lands, which is the point) →
D → E. F any time after A.

**Sequencing note (ADR-152 pattern):** land the validator (C) *with* the content
(B), not before it, so the pack never fails load on a half-migrated tree.

**Descope from 158-63 entirely:** authoring per-room bindings for `exp*` ids.
That work cannot be committed and must not be attempted again.

---

## 7. Reuse ledger (pragmatic restraint)

| Concern | Verdict |
| --- | --- |
| Authored creature pool per region | **Reuse** `themes/*.yaml::creature_table` — authored, tracked, parsed, unread. Wire it. |
| Depth banding | **Reuse** `CreatureEntry.depth_band` + `RegionNode.depth_score` — already the same units. |
| Region→theme mapping | **Reuse** `RegionNode.theme` + `ThemePalette.themes_for_depth`. |
| Eligibility filter | **Reuse** ADR-152 `game/zone_eligibility.is_eligible`. |
| Roster sizing | **Reuse** `affinities.size_by_burst.wandering_rolls`. |
| Freezing / persistence | **Reuse** `region_population` `RegionCreature` rows + `_stage_commit`. |
| Injection into `<game_state>` | **Reuse** `monster_manual_inject` feeders + ADR-156 Green Room gate. Unchanged. |
| Specific-creature-in-specific-room | **Reuse** ADR-106 clause 7 set-pieces (already in the theme files). |
| Static-world region tables | **Reuse** `encounter_tables.yaml`, unchanged, for the worlds it already serves. |
| Anchor/runtime split | **New:** one 6-line `resolve_room_source` helper + one directory. Everything else repoints. |

Net: one small helper, one directory, one resolver swap. No new file format, no
new content directory *type*, no new persistence, no new injection path. The
change is mostly **deletion** — a silent fallback, a gitignore exception, three
environment-dependent test assertions, and a duplicate authoring surface.

---

## 8. SOUL alignment

- **Crunch in the Genre, Flavor in the World / ADR-140** — the roster is world
  content (`bestiary.yaml` ids, world-tier `themes/`); the genre keeps the
  rulebook. Jade can add the crunch a table wants as two YAML edits.
- **No Silent Fallbacks** — the absent-binding silent `[]`, the default state for
  32 of 33 rooms, is deleted. Every roster decision emits a span.
- **Don't Reinvent — Wire Up What Exists** — the surface ADR-106 clause 6
  specified has been shipped and unread since 2026-05. This wires it.
- **No Stubbing** — `creature_table` stops being parsed dead content.
- **The GM panel is the lie detector** — `roster_source` on the curate span makes
  "did a human choose this creature?" a queryable fact.
- **Diamonds and Coal** — a themed, banded roster is coal a table can polish; a
  set-piece is the diamond the author placed deliberately.
- **Keith-as-player** — the career GM notices when the monsters do not belong to
  the room. Theme-sourced rosters are the cheapest structural fix for that tell.
