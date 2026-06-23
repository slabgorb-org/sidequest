# Story 158-1: WWN combat never seats on a fresh descent — reconcile surfaced-creature zone to PC region so the router projects a co-located Other

## Title

[BENEATH_SUNDEN-WWN-COMBAT-SEAT-ZONE-RECONCILE] When the narrator surfaces a live hostile creature in the PC's current scene, reconcile that creature's engine `location` to the PC's current region BEFORE the router projects co-located Others, so a combat intent routes to a seatable confrontation instead of narrating a fight with no mechanical backing.

## Metadata

- **Story ID:** 158-1
- **Type:** bug
- **Points:** 5
- **Priority:** p0
- **Repos:** server
- **Workflow:** tdd
- **Epic:** 158 — Playtest sweep follow-ups (open findings from the 2026-06-22 full-stack /sq-playtest sweep)

## Problem Statement

**Forensic Finding (2026-06-22, session `8b54610d`, beneath_sunden / caverns_and_claudes WWN):**

On a fresh descent to a procedural dungeon node, the narrator surfaces a live hostile creature "pooling at your feet" in the PC's current scene/zone. However, the creature's engine `location` field is stale and points to a DIFFERENT zone. The router's projection for co-located Others (per ADR-116: "a confrontation requires a co-located Other") finds ZERO candidates, so it never dispatches a confrontation to the seater. Result: `encounter_type=None`, `total_beats_fired=0`, `in_combat=False` — no intent_router combat subsystem fires, no confrontation seats, no dice roll.

The narrator then **free-narrates the entire fight and fabricates a player HP value** ("You have four hit points remaining") while the engine + character panel both show HP 10/10 unchanged — a textbook lie-detector failure. The invented "blade can't disperse it" mechanic-override rule was even persisted as a Lore footnote, canonizing the fabrication.

**Concrete repro from session snapshot:**
- **PC state:** current scene = "The Winding Catacomb" (current_region = `exp002.r3`)
- **Creature state:** engine has Gnaw-Swarm (`creature_id=gnaw_swarm`, disposition −20) seeded in `npcs`, BUT its `location="Under the Rope"` — a different zone entirely
- **Router outcome:** projection sees no creature at `exp002.r3` → no co-located Other → no confrontation dispatch → no intent_router.subsystem=combat → no seater invoked
- **Narrator outcome:** improvises fight, invents HP ("four hit points"), persists lie as Lore

**Why it matters:** The product's #1 goal is a narrator that a career GM can trust. A full fresh megadungeon descent with multiple MM-staged hostiles produced ZERO mechanical combat and a completely ungrounded narration.

**Related context (overlapping but distinct issues):**
- **153-23** (just-landed): threads `region_for()` room_id into monster-manual inject so authored room creatures populate generated rooms. The MM-injected creature's zone may drift from the PC's current region — this story reconciles that drift.
- **158-2** (sibling): IntentRouter routes literary/described attacks to combat, not only blunt "attacks X with Y" — distinct from zone reconciliation, but the router's classification happens downstream of this reconciliation.

## Root Cause Direction

**Forensic OTEL trace (2026-06-22, DRIVER live-inspector on the attack turn, session `8b54610d`):**

Live Inspector during the blunt "I attack the beetle swarm…" turn showed:
- **Encounters tab:** ENCOUNTER_TIMELINE — 0 EVENTS (no `ENCOUNTER_STARTED`, ever)
- **Subsystems → Component Summary (the attack turn):** `intent_router` fired (8 events, 0 errors) and `projection` fired (27 events), but there is **NO `confrontation` / `combat` / `dispatch` / `seater` / `mechanical` component** in the fired set at all
- **Decision locus:** the router's projection gate, NOT the seater — the decision died upstream, never reaching the seater

**The fix surface is co-location, not verb classification.** When the narrator surfaces/engages a creature in the current scene, that creature's `location` must be reconciled to the PC's current region BEFORE the router projects co-located Others. The seater will then see the creature and seat the confrontation. This overlaps both the 153-23 room-population work (MM-injected creatures may be in stale zones) and the broader issue of narrator/engine region desync.

**Architectural principle (ADR-116):** A confrontation requires an Other. The router's seater is the gate — it will not seat without a co-located, engine-backed opponent. The narrator surfacing a creature doesn't auto-seat; the creature must be present in the game state AT the PC's location for the projection to find it and the seater to materialize it.

## Acceptance Criteria

1. **Zone reconciliation fires before router projection.** When the narrator surfaces/engages a creature via the narration tool contract or an event handler (e.g. room entry, encounter triggered), that creature's engine `location` is reconciled to the PC's current region before the router projects co-located Others. The creature becomes "present" at the PC's location in the engine's eyes, not just the narrator's narration.

2. **Blunt combat intent against surfaced creature now seats.** A command like "I attack the <creature> with my <weapon>" against a creature the narrator just surfaced on-stage now SEATS a confrontation (intent_router dispatches combat; encounter starts; beats fire / dice roll). Verified on the beneath_sunden gnaw_swarm repro class — a fresh descent with MM-seeded hostiles now produces seated combat, not narrator improv.

3. **OTEL watcher events expose co-location reconciliation.** Spans emit at the router/projection gate exposing the reconciliation decision: reconciled creature id, from-zone (stale), to-zone (PC's current region), and whether a co-located Other was found (Y/N). The GM panel is the lie detector and must be able to verify the zone-reconcile path fired and what it found. Events should enable classifying "zone mismatch found and fixed" vs "creature not found at either zone" vs "no reconciliation needed (zones already matched)".

4. **No regression on genuinely-off-stage creatures.** A creature genuinely in a DIFFERENT zone (not surfaced on-stage by the narrator) is NOT spuriously reconciled/seated. The reconciliation must be scoped to creatures that the narrator has explicitly engaged — either the turn's primary target or creatures mentioned in the narration. A distant pack of shadows lurking in an unexplored cavern should not teleport to the PC's feet.

5. **Creature HP and state survive reconciliation.** When a creature's `location` is reconciled from zone A to zone B, its HP, status effects, equipment, and disposition remain intact. A reconciled creature does not reset to template HP or lose in-progress state — it's a location fix, not a respawn.

6. **Wiring / integration test AC.** A test reachable from the real play path — a narration turn against a surfaced creature in a different zone — drives the reconciliation and asserts: (a) the creature's `location` is updated to the PC's current region after reconciliation, (b) the seater finds a co-located Other and seats a confrontation, and (c) the OTEL spans fire proving the reconciliation path was live. This test must NOT bypass the router's projection gate — it must verify the full intent → router → projection → seater path.

## Key Code Areas to Investigate

**Router projection and seater (the fix gate):**
- `sidequest/server/dispatch/intent_router.py` — the router's projection step that filters co-located Others
  - The projection enumerates `npcs` and filters to those at the PC's location
  - The seater examines the projection result and decides whether to seat
  - **Fix locus:** before projection, reconcile surfaced-creature locations to the PC's current region

**Narrator surfacing contract:**
- `sidequest/server/agents/tools/narration_tool.py` — the narration tool where the narrator describes a creature
  - Identify the narration input/event that "surfaces" a creature (e.g. describing a creature at the PC's feet)
  - Hook reconciliation BEFORE the narration output is returned to the router

**Creature location state:**
- `sidequest/game/npc.py` — NPC/creature model, `location` field
- `sidequest/game/session.py` — GameSnapshot, per-PC current region (`current_region`, `region_for()`)

**Monster Manual injection (related context, 153-23):**
- `sidequest/server/dispatch/monster_manual_inject.py` — MM injects creatures; reconciliation complements room-binding wiring
- `sidequest/server/dispatch/room_creature_binding.py` — room creature binding (153-23 wiring)

**Dungeon traversal (region authority):**
- `sidequest/game/dungeon/` — region/room state
- `sidequest/dungeon/lookahead_worker.py` — region node ids (`entrance`, `expNNN.rN`)

**Spans and observability:**
- `sidequest/telemetry/spans/router.py` — router events
- `sidequest/telemetry/spans/projection.py` — projection events (create zone-reconcile spans here)

**Existing tests to extend:**
- `tests/integration/test_wn_combat_*.py` — WWN combat seating tests
- `tests/integration/test_intent_router_*.py` — router projection and seating tests
- Add a new test that drives a surfaced creature in a stale zone and verifies reconciliation + seating

## Technical Notes

- **ADR-116 (A Confrontation Requires an Other — Participant Membership Invariant):** the seater is the enforcement gate for co-location. A creature in a different zone is orthogonal to the seater and invisible to the projection.
- **ADR-059 (Monster Manual — server-side pre-generation via game-state injection):** creatures are materialized into game state before the narrator runs, so they're world truth, not improvisation. The location field is part of that truth.
- **ADR-113 (Intent Router — mechanical-engagement spine):** the router's projection is the gate for co-located Others; reconciliation must fire upstream of projection so the seater sees the reconciled creature.
- **ADR-123 (Mechanical-Engagement Pipeline — confidence-gated topological dispatch bank):** dispatch happens at the router/seater seam; reconciliation enables the dispatch path.
- **Narrator region desync (broader issue):** the narrator may advance the scene/POI within a region while the engine's `current_region` lags. Reconciliation is a targeted fix for one manifestation (surfaced creatures); the broader desync is a separate concern (153-24 room-axis persistence, 158-8 MP desync).

## Story Scope

**In scope:**
- Reconcile surfaced creature `location` to PC's current region before router projection.
- Hook the reconciliation in the narration tool contract or the intent-router projection gate.
- Emit OTEL spans at the reconciliation gate proving the path is live.
- Verify seating on a fresh descent with MM-seeded creatures.
- Integration test driving the real play path (not a unit-test bypass).

**Out of scope (reference only):**
- Narrator/engine region desync (153-24 room-axis, 158-8 MP pronoun/desync).
- Literary verb classification (158-2).
- Narrator HP fabrication block (158-3) — this story is routing/seating, not HP validation.
- Any new creature-spawning or zone-management system — this is reconciliation of existing creature state, not a new subsystem.

## Story Scope Clarification

This is a **single focused fix:** ensure that when a creature is surfaced in narration AT the PC's location, its engine location matches. The fix is a targeted reconciliation, not a redesign of creature placement, narrator/engine sync, or the router itself. Do not expand to other zone-desync manifestations; those are separate stories (153-24, 158-7, 158-8).
