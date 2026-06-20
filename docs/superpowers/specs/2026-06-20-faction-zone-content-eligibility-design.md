# Faction / Zone-Scoped Content Eligibility — Design Spec

- **Date:** 2026-06-20
- **Author:** Architect (Neo), with Keith
- **Epic:** epic-157 — Faction/zone-scoped content eligibility
- **Design story:** 157-1
- **Related ADR:** ADR-059 (Monster Manual) — amended by this work; see also ADR-018 (trope engine), ADR-128 (seed-trope deck), ADR-109 (location entities), ADR-055 (region navigation), ADR-113 (frontier hook / region transition).
- **Status:** approved (design phase)

## Problem

Multi-region worlds leak content across zones. Confirmed in the wry_whimsy/gulliver
playtest (session `2026-06-20-gulliver-e721409c`): a 4th-voyage **Yahoo** surfaces on
the 1st-voyage **Lilliput shore**. Two facets of one root cause:

1. **Wrong content appears.** The Monster Manual (ADR-059) samples bestiary creatures
   with no location/region/faction axis, and `monster_manual_inject._npc_patches_for_encounters()`
   applies **zero** location filtering — every available encounter is eligible everywhere.
2. **Right content does not appear.** A region's authored cartography cast (the Lilliput
   court — Emperor, Reldresal, Skyresh) is consumed **pull-only** via the narrator tool
   `resolve_location_entity`; nothing push-stages it on region entry, so the narrator
   invents cross-voyage extras (a Laputan "Flapper" on the Lilliput shore) instead.

The same gap exists, unscoped, in the trope engine and the seed-trope deck: tropes and
seeds are drawn world-wide with no region predicate (`trope_tick._gate_activations()`
comments that region filtering is "a future seam"; `SeedDeck` is keyed by
`(genre, world, session)`, never region).

This applies to every multi-region world: **gulliver** (4 voyages), **oz** (7 regions),
**wonderland** (2 zones), **road_warrior/the_circuit** (subculture territories), and
others. It does **not** apply to the 11 single-zone worlds that declare no zones.

## Key reuse-first finding

The eligibility key **already exists in authored content**: `Region.controlled_by`
(`genre/models/world.py`). It is authored exactly where the bleed problem lives and
absent where it does not:

| World | `controlled_by` partition |
|---|---|
| gulliver | `the_lilliput_court` / `the_brobdingnag_crown` / `the_lagado_academy` / `the_houyhnhnm_assembly` / `no_one` |
| oz | 7 region-factions (1:1): `munchkins`, `witch_of_the_west`, `the_wizard`, `glinda`, `gillikin_hedge_witches`, `open_country`, `no_one` |
| wonderland | `the_queens_terror` / `the_rigged_game` / `no_one` |
| the_circuit | subcultures: `bosozoku`, `cafe_racers`, `lowriders`, `dekotora`, … |
| perseus_cloud | houses (`house_akkad`, …) |
| **11 other worlds** | **no `controlled_by` → unzoned → unaffected** |

So no new cartography authoring is required. The work is: (a) tag the **pooled,
home-less** content (bestiary creatures, tropes, seed-tropes) with the faction(s) it
belongs to; (b) wire one shared eligibility predicate into the four draw/inject seams;
(c) push-stage the authored cartography cast on region entry; (d) a strict load-time
validator. Faction is the eligibility axis Keith directed ("group locations by faction;
scope content-eligibility by the region's faction-group").

`ManualNpc.location_tags` already exists with the doc comment "biome/terrain for future
filtering" (ADR-059 entry schema) — this design realizes that anticipated filtering on
the **faction** axis, leaving `location_tags` as the orthogonal *within-zone* placement
refinement.

## Decisions (from the design dialogue)

- **Scope:** all three pools — creatures **and** NPCs **and** tropes/seeds.
- **Approach:** derive the zone from `region.controlled_by`; tag content with an explicit
  `factions: list[str]`; one shared predicate at four seams; the authored cast staged via
  the existing (empty) `frontier_hook` observer registry. (Not: substring `location_tags`
  reuse; not: a new first-class `factions.yaml` registry — `controlled_by` already encodes
  membership. A first-class faction registry is the future option if factions must become
  mechanical actors — disposition/reputation/grudges.)
- **Untagged content in a zoned world:** **strict fail-loud at load** (`GenreLoadError`).
  Strictness lives in the *load validator*, not the runtime predicate (see "Runtime is
  permissive" below).

## Model

### The content tag (new field, additive, default empty)

```python
# on BestiaryEntry (genre/models/bestiary.py),
#    TropeDefinition + SeedTrope (genre/models/tropes.py)
factions: list[str] = Field(default_factory=list)
```

- Each value is either an **exact** `controlled_by` string from the world's cartography
  (e.g. `the_houyhnhnm_assembly`) or the reserved sentinel `"*"` meaning *all zones in
  this world* (world-global content — e.g. a cross-voyage thematic trope).
- Default empty → unzoned worlds and all existing content keep parsing unchanged. The
  **validator** (not the field) enforces non-empty in zoned worlds.
- Authored cartography NPCs and runtime generated walk-ons do **not** carry this field —
  their zone is derived (see Seams 2). Only the three pooled, home-less content types are
  tagged.

### Zoned-world detection (computed once per loaded world, cached)

```python
def world_is_zoned(cartography) -> bool:
    return any(r.controlled_by for r in cartography.regions.values())
```

The 11 worlds with no `controlled_by` → `False` → every predicate short-circuits to
eligible. Zero behavior change for them.

### Active-faction resolver (split-party safe, never raises on None)

```python
def active_factions(snapshot, pack, *, perspective=None) -> set[str]:
    # perspective given: {controlled_by of that PC's region} or ∅
    # perspective None + consensus region: {controlled_by of consensus region}
    # perspective None + split party (region_for() → None):
    #     UNION of every seated PC's region controlled_by
    # returns ∅ when no region resolvable (pre-bind / malformed turn)
```

Per-perspective seams (creature/NPC injection — they already hold `turn_context`) pass
the perspective; party-global seams (trope/seed ticks) pass `None` and get the union —
eligible if it matches **any** seated PC's zone.

### The one predicate (runtime is permissive; strictness is the validator's job)

```python
def is_eligible(content_factions, active, *, zoned) -> bool:
    if not zoned:                return True   # unzoned world → no scoping
    if not active:               return True   # region unresolvable → do not suppress
    if "*" in content_factions:  return True   # explicit world-global
    if not content_factions:     return True   # untagged → permissive (see below)
    return bool(set(content_factions) & active)  # tagged-but-wrong-zone → EXCLUDED
```

**Why untagged is permissive, not excluding.** If the runtime *excluded* untagged
content, the moment the engine ships every still-untagged gulliver creature would vanish,
breaking the world mid-epic before tagging lands. Instead, **tagged-wrong-zone** is the
exclusion (the bug fix), **untagged** is permissive, and the **load validator** guarantees
untagged authored content cannot ship in a zoned world — so the permissive branch is dead
code in production. This decouples sequencing (engine can land before content tagging) and
fails toward *showing* content, never toward a silent empty scene. Hub regions
(`controlled_by: no_one`) are not special-cased — sea content is tagged `factions: [no_one]`.

## The four application seams

Each seam is a thin call into a new `sidequest/game/zone_eligibility.py`. No seam
re-derives anything.

### Seam 1 — Creature/encounter injection (the headline fix)

- File: `server/dispatch/monster_manual_inject.py`, `_npc_patches_for_encounters()`.
- Propagate factions through seeding: add `factions: list[str]` to `ManualEncounter`
  (and `ManualNpc` for symmetry). `_generate_encounter()` (pregen) stamps an encounter's
  `factions` = union of its source bestiary entries' `factions`.
- At inject, filter each candidate encounter: `is_eligible(encounter.factions,
  active_factions(perspective), zoned)`. The Yahoo encounter (`the_houyhnhnm_assembly`)
  is dropped on `the_lilliput_shore`.
- **Resolution note (applies to Seams 1 & 2):** the active faction is resolved from the
  canonical region (`snapshot.region_for(perspective)` → that region's `controlled_by`),
  **not** from the free-text `current_location` string `inject()` currently receives —
  `current_location` may be a POI/scene string, not a region slug. `zone_eligibility`
  owns this resolution; the seam passes the snapshot (+ optional perspective).

### Seam 2 — NPCs (two sub-parts)

- **Generated walk-ons — origin-stamp, not exclude.** The pre-seeded namegen pool
  (`pregen` calls `manual.add_npc(data, [])`) is runtime filler, not authored content, so
  the validator does not touch it. Instead, when an unplaced generated NPC is *activated*
  in a zoned world, stamp its faction = the current region's `controlled_by` (alongside the
  existing `activated_location`). A walk-on born in Lilliput is a Lilliputian and cannot
  later resurface in Houyhnhnm-land. No over-suppression — the narrator still gets walk-ons.
- **Authored cast staging — the "right cast appears" half.** Register the first real
  consumer of the empty `frontier_hook.notify_region_transition` observer registry. On
  region entry, push-stage that region's cartography `entities` where
  `binding.kind == "npc"` into the active/in-scene set (mark active, advance `last_seen`).
  Entering Mildendo surfaces the Emperor/Reldresal/Skyresh without the narrator electing
  `resolve_location_entity`, curbing invented cross-voyage extras.

### Seam 3 — Trope activation gate

- File: `game/trope_tick.py`, `_gate_activations()` (whose comment already flags this seam).
- A dormant trope is a candidate only if `is_eligible(trope.factions,
  active_factions(perspective=None), zoned)`. Party-global → union.

### Seam 4 — Seed-deck draw

- Files: `game/seed_deck.py` `draw()`, `game/seed_tick.py` `draw_engaged_seed()`.
- Filter candidates by `is_eligible(seed.factions, active_factions(None), zoned)` before
  the draw, so a Houyhnhnm seed is never dealt on the Lilliput shore. The deterministic
  shuffle / resume-safety is untouched — we filter the candidate set, not the ordering.

## Strict load validator + error handling

- Location: `genre/loader.py`, alongside existing `GenreLoadError` paths.
- After a world loads, compute `world_is_zoned(cartography)`. If zoned, for every pooled,
  home-less authored item (bestiary entries, tropes, seed_tropes) assert: (1) `factions`
  non-empty; and (2) every value is either `"*"` or a real `controlled_by` present in that
  world's cartography. Either failure → `GenreLoadError` naming the offending ids + world.
- The referential check (2) is load-bearing: a typo'd faction
  (`the_houyhnhm_assembly`) would silently never match at runtime — the validator turns a
  silent-disappear into a loud load failure.
- **Exempt** (zone derived, not tagged): authored cartography NPCs (region = zone),
  runtime generated walk-ons (stamped on activation).
- `"*"` does not weaken fail-loud: it is a *conscious authoring decision*, not an omission.
  The validator still requires non-empty, so an author must deliberately mark each pooled
  item zoned or global.

## OTEL (the lie-detector — persisted game-engine events)

Per the OTEL Observability Principle, the scoping must emit watcher events so the GM panel
can verify the engine engaged (vs. the narrator merely not mentioning a Yahoo by luck):

- `zone_eligibility.filtered` — on every *exclusion*: subsystem (creature/npc/trope/seed),
  content_id, content_factions, active_factions, region. ("yahoo_brute suppressed on
  the_lilliput_shore.")
- `zone_eligibility.cast_staged` — authored NPCs push-staged on region entry (count + names).

These are persisted, round-stamped game-engine events (like `state_patch_hp`), **not** the
live-only agent-pipeline spans (sidecar/intent_router/dispatch) — so forensics can verify
from a stored session.

## Testing (fixture-driven behavior + OTEL spans — never source-grep wiring)

- Unit truth table for `is_eligible` / `active_factions` (unzoned, unresolvable,
  untagged-permissive, tagged-match, tagged-mismatch, `"*"`, split-party union).
- One wiring test per seam. Headline: synthetic zoned world + a Houyhnhnm encounter +
  party in Lilliput → `inject()` → assert the Yahoo patch is **not** emitted (and **is**
  when the party is in Houyhnhnm-land) + assert the `zone_eligibility.filtered` span fired.
- Validator RED test: zoned world + one untagged bestiary entry → `GenreLoadError`.

## Story breakdown (design-first; validator lands last)

| Story | Type | Pts | Dep | Repo |
|---|---|---:|---|---|
| 157-1 | DESIGN — ADR-059 amendment + this spec | architecture | 3 | — | orchestrator |
| 157-2 | ENGINE — `zone_eligibility` module + `factions` on BestiaryEntry + Manual propagation + **Seam 1** + OTEL | wire-first | 5 | 157-1 | server |
| 157-3 | ENGINE — **Seam 2 (NPC):** generated walk-on origin-stamp + authored-cast staging via frontier_hook + OTEL | wire-first | 5 | 157-2 | server |
| 157-4 | ENGINE — `factions` on Trope/Seed + **Seam 3 (trope gate)** + **Seam 4 (seed draw)** + OTEL | wire-first | 5 | 157-2 | server |
| 157-5 | CONTENT — tag gulliver (bestiary+tropes+seeds), **proof**; verify no Yahoo bleed | trivial | 3 | 157-4 | content |
| 157-6 | CONTENT — fan-out: oz, wonderland, the_circuit | trivial | 5 | 157-5 | content |
| 157-7 | ENGINE — **strict validator** (GenreLoadError + referential check), lands last | wire-first | 3 | 157-6 | server |

~29 pts, p2 (behind the p1 epic-152 WWN combat work).

**Sequencing constraint (load safety).** The validator (157-7) refuses to load a zoned
world with any untagged pooled item. The runtime (157-2/3/4) is permissive, so it ships
without breaking anything. Then each world is tagged (157-5/6). Only after all four zoned
worlds are fully tagged does the validator merge (157-7) — "locking the door." At no point
does `develop` carry a zoned world that won't load. No flags (a flag would be a
silent-fallback smell).

## Out of scope / future

- A first-class faction registry (`factions.yaml`, region→faction index, `Faction` as a
  mechanical actor for disposition/reputation/grudges). `ReputationFaction` and
  `FactionGrudge` models already hint at this; `controlled_by` suffices for eligibility today.
- Finer within-zone placement beyond `location_tags` (unchanged here).
- Scoping content other than the three pools (e.g. loadout/inventory) — no evidence of bleed.
