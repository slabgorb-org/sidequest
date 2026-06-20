---
id: 152
title: "Faction/Zone-Scoped Content Eligibility — Region→Zone Grouping Gates the NPC/Creature/Trope Pools, and the Authored Region-Cast Is Push-Staged, Not Pull-Fetched"
status: proposed
date: 2026-06-20
deciders: ["Keith Avery", "Atlas the Endurer (Architect)"]
supersedes: []
superseded-by: null
related: [3, 18, 20, 55, 59, 118, 128, 136, 140]
tags: [game-systems, npc-character, genre-mechanics, room-graph, observability]
implementation-status: not-applicable
implementation-pointer: "PROPOSED. Seams to wire (none implemented yet): sidequest-content cartography.yaml (region.controlled_by faction + region.entities kind:npc — already authored) + bestiary.yaml (needs zone tags); sidequest-server sidequest/game/monster_manual.py (location_tags/culture/available_at_location — placement substrate exists, unfed) + sidequest/agents/tools/resolve_location_entity.py (cartography entities, today PULL-only) + sidequest/server/snapshot_slimming.py + sidequest/game/npc_scene.py (in-scene NPC projection — the push-stage target)."
---

# ADR-152: Faction/Zone-Scoped Content Eligibility — Region→Zone Grouping Gates the NPC/Creature/Trope Pools, and the Authored Region-Cast Is Push-Staged, Not Pull-Fetched

> Status **proposed**. Authored from a live `wry_whimsy/gulliver` playtest
> (2026-06-20, session `2026-06-20-gulliver-e721409c`) that surfaced cross-zone
> content bleed. Nothing here is built yet. This ADR records the decision and the
> reuse-first wiring plan; implementation is a follow-up (server + content).

## Context

SideQuest worlds are increasingly **multi-zone**: one world contains several
internally-coherent regions that should each draw on a *different* slice of the
world's cast, bestiary, and tone. The signature case is `wry_whimsy/gulliver` —
Swift's four voyages (Lilliput, Brobdingnag, Laputa/Lagado, the Houyhnhnms) are
one world but four sealed societies; a Lilliputian court official and a
Houyhnhnm have no business sharing a scene. The same shape recurs in
`wry_whimsy/oz` (Munchkin / Quadling / Winkie / Gillikin country + the Emerald
City) and `road_warrior/the_circuit` (vehicle subcultures sharing a port city,
each holding territory).

The gulliver playtest exposed two concrete failures of cross-zone hygiene:

1. **Creature bleed (the "Yahoo on the shore").** The Monster Manual (ADR-059)
   surfaced a fourth-voyage **Yahoo** in the npc_pool of the *first-voyage*
   `the_lilliput_shore` scene. Root cause: `bestiary.yaml` is a flat,
   all-four-voyages roster with **no zone tags**, and `monster_manual.py`'s
   placement rule is *"a creature with no `location_tags` is unplaced and
   eligible everywhere."* Untagged content defaults to global eligibility.

2. **NPC non-staging (the cast that never arrives).** The authored named cast
   *is* correctly homed in `cartography.yaml` (region `entities` carry
   `binding:{kind:npc}`; the Lilliput court — Emperor, Flimnap, Skyresh,
   Reldresal — is homed to `mildendo_capital`, not the shore). But that homing is
   consumed **only on-demand**, via the narrator tool `resolve_location_entity`
   (`agents/tools/resolve_location_entity.py:_authored_entities_for`) — a **pull**.
   Nothing **push-stages** a region's authored cast into the narrator's in-scene
   NPC set (`npc_pool` / the `is_npc_in_scene` projection in
   `snapshot_slimming.py`). With no authored cast proactively in context, the
   narrator invents generic, genre-bleeding extras ("The Flapper" [Laputa],
   "A Yahoo, the Braying" [Houyhnhnm], "A Fishwife of Wapping" [the PC's own
   Georgian-British home culture]). Because no authored NPC is ever *referenced*,
   none advances `last_seen_turn`, so ADR-136's relationship seen-gate never opens
   and the player-facing Relationships surface stays empty.

Both failures share one missing abstraction: **content has no notion of which
zone of the world it belongs to, and the engine has no notion of which zone the
party is currently in for the purpose of gating eligibility.** This violates
SOUL **Genre Truth** (a Yahoo in Lilliput is off-tone) and the **Living World**
(the authored court should *be there* and act, not be replaced by improvised
walk-ons), and it is the structural cause of the ADR-140 promise ("the World owns
the cast and catalog") silently not reaching the table.

### What already exists (reuse-first inventory)

This is deliberately **not** a request for new infrastructure. The substrate is
largely present and merely unfed/unwired:

| Capability | Where it lives today | Gap |
|---|---|---|
| Region → faction | `cartography.yaml` region `controlled_by: <faction>` | authored, but never read for eligibility |
| Region → NPC homing | `cartography.yaml` region `entities[].binding:{kind:npc}` | consumed PULL-only via `resolve_location_entity`; never push-staged |
| Creature placement | `monster_manual.py` `ManualNpc.location_tags` + `available_at_location()` | works, but bestiary content carries no tags → everything is "unplaced = global" |
| Creature → faction | `monster_manual.py` `ManualNpc.culture` field | unpopulated |
| In-scene NPC projection | `snapshot_slimming.py` / `npc_scene.is_npc_in_scene` | the natural push-stage target; not fed from cartography entities |

## Decision

Introduce **zone-scoped content eligibility** as a first-class, world-authored
concept, and make the **current region's authored cast push-staged** rather than
pull-fetched.

A **zone** is a named grouping of one or more regions under a shared faction /
culture / voyage. Every region resolves to exactly one zone (default: its own
`controlled_by` faction; an explicit `zone:` may group several regions, e.g. all
four Lilliput-court regions). Every eligibility-bearing content unit — NPC,
creature, and (where authored) trope/seed — resolves to a zone. **A content
unit is eligible in a scene only if its zone matches the scene's region's zone**
(plus an explicit "global"/"any" opt-out for genuinely world-spanning content
such as the PC, weather, or a wandering antagonist who is *meant* to cross
zones).

Two concrete mechanisms:

1. **TAG (content).** Give every zone-bound content unit a zone. Reuse the
   existing fields rather than inventing parallel ones:
   - Regions already carry `controlled_by`; add an optional `zone:` to group
     regions whose `controlled_by` differs but which share a society.
   - Bestiary creatures get `location_tags` / a `zone:` (and `culture` where the
     creature is faction-bound) so the Monster Manual stops treating them as
     globally eligible. Untagged-means-global stays the rule, but authored
     multi-zone worlds are expected to tag — a validator severity (below) flags
     untagged content in a multi-zone world.

2. **WIRE + PUSH-STAGE (engine).** At scene-build time, resolve the acting PC's
   region → zone, then:
   - **Push-stage** that region's `cartography` `entities[kind:npc]` into the
     narrator's in-scene NPC set (`npc_pool` / the `is_npc_in_scene` projection)
     so the authored cast is *present by default*, not merely *pullable*. This is
     the fix for failure (2): Reldresal is in the narrator's `<game_state>` the
     moment the party is in a Mildendo region, the narrator uses him by name,
     `last_seen_turn` advances, and he appears in Relationships (ADR-136) and the
     disposition ledger (ADR-020) for free.
   - **Filter** the Monster Manual's candidate creature pool
     (`available_at_location` and its seed) by the scene's zone, so an
     out-of-zone creature (the Yahoo on the shore) is never eligible. This is the
     fix for failure (1).
   - **Optionally** scope trope/seed selection (ADR-018 / ADR-128) by zone where
     the world authors zone-bound tropes; out of scope for v1 but the same
     region→zone resolver should serve it.

The narrator-invents-extras behavior is acceptable *only* for genuinely nameless
crowd walk-ons in a zone with no more specific authored NPC; it must never
replace a present, zone-appropriate named NPC (this is already the intent of
ADR-126-32 / "bind narrated NPCs to existing identities" — push-staging simply
gives that binder a non-empty candidate set to bind against).

### Observability (CLAUDE.md OTEL principle)

The eligibility decision is exactly the kind of subsystem choice the GM panel
must be able to audit. Emit per scene-build:

- `zone.resolved {region, zone, faction}` — which zone the scene resolved to.
- `zone.npcs_staged {zone, staged_count, staged_ids}` — authored cast push-staged.
- `zone.creature_pool_filtered {zone, eligible, excluded, excluded_ids}` — what
  the Monster Manual filter admitted vs. rejected (so a future Yahoo-on-the-shore
  shows up as an `excluded` line, not a silent leak).

Without these spans the fix is unfalsifiable in play — a narrator that *happens*
to behave looks identical to a filter that is actually engaged.

## Consequences

**Positive.**
- Cross-zone bleed (Yahoo in Lilliput, Munchkin in Winkie country, a rival crew
  on another's turf) becomes structurally impossible, not prompt-dependent.
- The authored Living World cast reaches the table by default; Relationships /
  disposition / gossip light up without the narrator having to *elect* to fetch
  anyone. ADR-140 ("the World owns the cast and catalog") becomes true in play.
- Reuses existing fields and seams; no new storage, no new service.
- Generalizes to oz and the_circuit with content tagging alone (no further engine
  work once the resolver + push-stage + filter land).

**Negative / risks.**
- **Content debt:** multi-zone worlds must now tag their bestiary (and group
  regions into zones). Mitigated by a pack-validator severity (ADR-126 validator
  model): *warn* on untagged content in a single-zone world, *error* (or loud
  warn) on untagged eligibility-bearing content in a multi-zone world. Never a
  silent default that hides the gap.
- **Over-filtering:** a too-strict zone gate could starve a scene (no eligible
  creatures/NPCs). The "global"/"any" opt-out and the untagged-means-global
  fallback prevent a hard-empty pool; the `zone.*_filtered` spans make
  starvation visible.
- **Wandering antagonists / cross-zone arcs** (a villain who pursues the party
  across zones) need the explicit global/any tag — zone scoping is a default, not
  a cage.

## Alternatives considered

1. **Prompt-only fix (tell the narrator "stay in-voyage").** Rejected: it is the
   improvisation-without-backing pattern SOUL/OTEL exist to kill. A prompt nudge
   is unfalsifiable and regresses silently; the Yahoo came from the *Monster
   Manual*, not the narrator, so a narrator prompt wouldn't even touch it.
2. **Per-NPC/creature `region:` field only (no zone grouping).** Rejected as the
   sole mechanism: many worlds want *several* regions to share one cast (the four
   Lilliput-court regions; the Emerald City + its approaches). A flat region tag
   forces duplicating a faction across every region id; the zone grouping is the
   reuse-friendly unit. (Per-region homing still works underneath — `cartography`
   `entities` already provides it — zone is the grouping over regions.)
3. **Keep pull-only `resolve_location_entity` and just prompt the narrator to
   call it.** Rejected: the playtest showed the narrator does not reliably call
   it (5 shore turns, 0 calls, 5 invented extras). Presence must be a push
   default; the pull tool remains useful for *resolving a named entity the
   narrator already decided to use*, not for *populating who is present*.
4. **Hard-code voyage logic in the gulliver world.** Rejected: it's a
   cross-world pattern (oz, the_circuit, future worlds); engine-level region→zone
   resolution + content tags keep it in content, per ADR-140 / "Crunch in the
   Genre, Flavor in the World."

## Implementation notes (for the FIXER / Dev — non-binding)

- Resolver: one `zone_for(region_id) -> zone` helper over `cartography`
  (`zone:` if present, else `controlled_by`), shared by NPC staging, the Monster
  Manual filter, and (later) trope selection. Single source of truth.
- NPC push-stage: at the same scene-build seam that runs `is_npc_in_scene`
  (`snapshot_slimming.py` / `session_helpers.py`), union the current region's
  `entities[kind:npc]` refs into the in-scene set before projection. The binder
  (ADR-126-32) then has the authored identities as candidates.
- Monster Manual filter: scope `available_at_location()` + the seed candidate set
  by `zone_for(current_region)`; untagged creatures stay global (with a
  validator warning in multi-zone worlds).
- Content: add zone tags to `wry_whimsy/gulliver` bestiary + group its regions
  into the four voyage-zones first (the reproduction case), then `oz` and
  `road_warrior/the_circuit`.
- Tests: an OTEL span assertion that a scene in zone A excludes a zone-B creature
  and push-stages zone-A's authored cast (per the No-Source-Text-Wiring-Tests
  rule — drive the flow, assert the `zone.*` spans).
