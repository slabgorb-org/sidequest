---
id: 157
title: "The Bounded-Site Interior Is Cookbook-Free — A Bounded Site Materializes From Its Archetype Alone, Not From the Megadungeon Cookbook/Corpus/Themes Stack"
status: accepted
date: 2026-07-10
deciders: ["Keith Avery"]
supersedes: []
superseded-by: null
related: [55, 96, 106, 121, 140]
tags: [room-graph, game-systems]
implementation-status: partial
implementation-pointer: "sidequest-server/sidequest/dungeon/bounded_site.py::materialize_bounded"
---

# ADR-157: The Bounded-Site Interior Is Cookbook-Free — A Bounded Site Materializes From Its Archetype Alone, Not From the Megadungeon Cookbook/Corpus/Themes Stack

## Context

The three-tier mapping design (`docs/superpowers/specs/2026-07-08-three-tier-mapping-design.md`,
§1) makes a **Site** a first-class named entity with an `extent: bounded | frontier`
toggle: "almost all generated sites are dead-ended and finite (a tavern is not
infinite). Bounded sites materialize whole." Track B task 11 landed the bounded
materializer (`bounded_site.ensure_bounded_site_materialized`), and task 10 landed the
`SiteArchetype` content model, whose docstring states the doctrine outright: *"Content,
not engine code (Jade doctrine): a new archetype is YAML, never a server change."*

Story 164-7 (the tavern+vault e2e) exposed that the substrate does not honor its own
doctrine. `ensure_bounded_site_materialized` calls the **full megadungeon** `materialize()`
pipeline (design → fill → **curate** → **attach** → commit), and the movement dispatch
feeds it via:

```python
site_bundle  = load_cookbook(world_dir)          # game/cookbook/loader.py:55
site_palette = load_theme_palette(world_dir)      # a themes/ tree
```

`load_cookbook` **hard-requires** world-local `corpus/monsters.yaml`, `corpus/items.yaml`,
`world_register.yaml`, `cookbook/races/`, `cookbook/looks.yaml`, `cookbook/affinities.yaml`,
and `cookbook/special_rooms.yaml` — raising `FileNotFoundError` on the first one missing.
The `curate` stage then force-populates **every room** with a wandering-monster table + a
`big_bad` sampled from that corpus; the `attach` stage seeds set-pieces / tropes / quests
from the `themes/` tree.

Two facts make this untenable:

1. **The stack exists in exactly one world.** Only `caverns_and_claudes/beneath_sunden`
   ships `cookbook/` + `corpus/` + `themes/` + `world_register.yaml`.
   `tea_and_murder/blackthorn_moor` and `space_opera/aureate_span` ship **none** of it. So
   authoring a tavern/vault there is *not* "YAML-only content" — it would require porting
   the entire dungeon interior pipeline into two non-dungeon worlds, violating the
   `SiteArchetype` doctrine (ADR-121/140) and blowing past the plan's "two YAML files."
2. **The content is genre-wrong even where present.** A cozy `tea_and_murder` pub is not a
   monster den. The curate stage would stamp a wandering-monster roster + a big_bad into
   the common room. 164-6's own bounded tests hid this by materializing a "tavern" against
   *beneath_sunden's caverns cookbook* — geometrically a tavern, mechanically a dungeon.

There is also a latent contract bug on the crossing path: `movement.py` wraps the loads in
a `try` whose comment promises "a content gap ... surfaces as a RECOVERABLE movement
failure," but the `except` clauses catch only `(SeamCrossingError, GenreLoadError)`.
`load_cookbook`'s `FileNotFoundError` matches neither, so it propagates out of
`run_movement_dispatch` — a re-raise the dispatch contract forbids.

## Decision

**A bounded site materializes from its `SiteArchetype` alone. The megadungeon
cookbook/corpus/themes/world_register stack is NOT a dependency of a bounded site.**

1. **A parallel, cookbook-free coordinator.** A new `materialize_bounded()` (in
   `dungeon/bounded_site.py`) runs only the two **already-cookbook-free** geometry stages —
   `_stage_design` + `_stage_fill` (`generate_interior` + `_emit_mask`) — followed by a
   **dedicated geometry commit** that persists the region graph + per-room masks/tactical +
   room identities. It runs **no curate** (no wandering monsters, no big_bad) and **no
   attach** (no set-pieces/tropes/quests). The existing `materialize()` and its loud
   None-guards are **left untouched** — zero regression risk to `beneath_sunden`, the single
   most load-bearing procedural path. The bounded path is self-evidently monster-free: there
   is no `CookbookBundle` in its signature.

2. **The archetype is the whole content source.** `SiteArchetype.interior_algorithm` + the
   grid dimensions drive a synthetic in-memory `ThemePalette` (one theme, all-depth band) so
   the geometry stages run unchanged. The previously-dormant `room_vocabulary` and
   `feature_palette` fields finally earn their keep: they label the generated rooms.
   Diamonds-and-Coal — a bounded site's rooms have identities ("common room", "cellar"), not
   anonymous cells.

3. **Zero engine-placed creatures in a bounded interior.** Inhabitants and drama come from
   the **Living World** (the narrator + the existing NPC / scenario / confrontation systems),
   never a materializer roster. A vault guardian or a tavern brawl is a confrontation the
   narrator/scenario **seats**, not cookbook content the materializer stamps into a room.

4. **Missing interior content fails LOUD-but-recoverable.** The `movement.py` bounded branch
   stops calling `load_cookbook`/`load_theme_palette` for bounded sites entirely — the
   archetype drives materialization, so the `FileNotFoundError` *source* is removed. As
   defense-in-depth for the frontier path and any future content-load, the surrounding
   `except` is broadened so **any** content-load failure surfaces as a recoverable
   `movement.unresolved` (+ `site.enter_unresolved` span), never a re-raise out of
   `run_movement_dispatch`.

## Consequences

- **A new bounded archetype (tavern, vault, hotel, warren) is authored as pure pack YAML** —
  no world change, no engine change. This realizes the Jade / ADR-140 doctrine ("genre is
  the rulebook only; the world owns the cast and catalog") for *sites*: the site catalog is
  genre content, and a bounded interior needs nothing world-local.
- **`beneath_sunden`'s frontier megadungeon is unchanged.** It keeps the cookbook path;
  `frontier` sites (ADR-106) still curate + attach. The two extents are two coordinators, not
  one conditional pipeline.
- **Determinism is preserved.** The bounded seed is `blake2b(campaign_seed, site_id)`
  (write-once) and the whole graph + grids materialize in one committed transaction
  (`lookahead_breadth = 0`, no frontier edges) exactly as task 11 established.
- **Observability.** The bounded coordinator emits the existing `site.materialize.*`
  spans (begin/commit/skip) plus the geometry-stage spans (`dungeon.materialize.design/fill/
  mask`). It emits **no** `curate`/`attach` spans — their absence on a bounded materialize is
  itself the lie-detector signal that the site is monster-free. All spans route to
  `turn_telemetry` (spec §5 invariant).
- **The three-tier spec is amended** (§1 Extent, §3, §5) to record the cookbook-free bounded
  path and the fail-loud-but-recoverable crossing contract.

## Alternatives considered

- **Genre-default / minimal cookbook + themes stack (data-side fix).** *Rejected.* A cookbook
  is intrinsically a monster-roster concept; authoring one per genre whose only purpose is to
  say "no monsters here" is large, fights the grain, and is still genre-wrong. Two of the
  three v1 target worlds ship zero interior stack, so this is net-new authoring in every
  non-dungeon world — the opposite of "a tavern is YAML."
- **Make `materialize()`'s curate/attach optional (`content_stack=None`).** *Rejected.* It
  weakens the loud None-guards on the most load-bearing procedural path with conditional
  branches threaded through curate/attach/commit — precisely the kind of "make it work with
  the other path" tuning that SOUL's *Bind the Ruleset, Don't Balance It* discipline warns
  against. Keep the megadungeon path pure; give the bounded site its own honest coordinator.
- **Extract a shared geometry core + two thin coordinators.** *Deferred, not rejected.* The
  cleanest long-term separation, but a larger refactor and blast radius than a 3-point story
  warrants. `materialize_bounded()` reuses `_stage_design`/`_stage_fill` directly today; a
  later refactor can hoist a shared core if a third extent ever appears.
