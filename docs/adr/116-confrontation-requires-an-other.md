---
id: 116
title: "A Confrontation Requires an Other — Participant Membership Invariant, Single Opponent-Seater, End-on-No-Other"
status: accepted
date: 2026-05-26
deciders: ["Keith Avery", "Leonard of Quirm (Architect)"]
supersedes: []
superseded-by: null
related: [24, 33, 77, 113, 114]
tags: [game-systems]
implementation-status: partial
implementation-pointer: sprint/context/context-story-59-13.md
---

# ADR-116: A Confrontation Requires an Other

> **Amends, does not supersede.** This completes the participant model implied by
> ADR-033 (Genre Mechanics Engine — Confrontations) and the dual-track design
> (`docs/superpowers/specs/2026-04-25-dual-track-momentum-design.md`), and it
> overturns one local decision made in **Story 45-33**: the exemption that let
> `category="movement"` (and `social`) confrontations instantiate with no
> opponent seated. See §3.

## Context

### The bug that surfaced it

Story 59-13 was filed as "chase confrontation write-back is broken — dual-dial
frozen 0/7, opponent seat empty, Setup→active never fires." Measurement
(two probes, `tests/server/test_chase_writeback_probe.py`) proved the stated
root cause **false**:

- **Beat write-back works.** With an opponent seated, a chase beat advances the
  opponent dial (0→2) and the phase transitions Setup→Opening. The
  `_apply_narration_result_to_snapshot` → `apply_beat` path is sound for chase,
  identically to combat.
- **The real defect is upstream, in *who gets seated*.** `instantiate_encounter_from_trigger`
  for a chase with no narrator-named NPCs seats **only the player**. With no
  opponent-side actor, every opponent beat is skipped (`apply_beat` returns
  `skipped_reason="neutral_actor"`/no target), so the opponent dial never moves
  and the encounter never leaves Setup.

### The larger problem the bug exposed

The engine has **no enforced concept of confrontation membership** — no
authoritative, type-aware answer to *"who is on the other side of this
confrontation?"* Instead, "who is fighting" is recomputed each turn from a
heuristic: whoever the narrator happened to name this turn, else whoever was
`last_seen_location` in the same room. Worse, the side they get is inferred from
the confrontation's category (`_npc_fallback_at_location`: `opponent` if combat
else `neutral`) — which directly violates the `EncounterActor.side` contract
("*set at instantiation from the narrator's payload; engine never infers it*").

### What already exists (reuse-first audit)

The membership *primitives* are already present — only the entry discipline and
one invariant are missing:

| Concept | Where it lives | Status |
|---|---|---|
| Participant roster | `StructuredEncounter.actors: list[EncounterActor]` | present |
| Membership / alignment | `EncounterActor.side` ∈ {player, opponent, neutral} | present |
| Exit flag | `EncounterActor.withdrawn` (skipped by `apply_beat`) | present |
| Player-exit → resolve | `server/dispatch/yield_action.py` (`all(a.withdrawn …)` for player side) | present |
| Live-opponent count | `confrontation_lifecycle_detector.opponent_alive_count` | present |
| **Opponent entry discipline** | — | **missing** |
| **"Needs an Other" instantiation invariant** | combat-only guard (`NoOpponentAvailableError`) | **incomplete** |
| **Opponent-exit → resolve ("no Other remains")** | — | **missing** |

## Decision

A structured confrontation is, by the dual-dial construction (`player_metric` +
`opponent_metric`), a contest between **two sides**. We make that explicit and
enforce it.

### 1. The invariant: a confrontation requires an Other

A structured confrontation MUST have at least one live (`side="opponent"`,
not `withdrawn`) actor. If no opponent entity can be sourced, it is **not a
confrontation — it is narration.** A "race against time" (chase vs. a clock, a
tide, a blockade) is rendered as prose; an abstraction never gets a seat or a
dial. *Entities get seated and get the opponent dial; abstractions get narrated.*

"Solo" means **one player character**, never "no opponent." The 45-33 reasoning
that a solo chase is "a legitimate one-on-one scene the narrator can populate
later" conflated those two; nothing ever populated the later beat, so the dial
froze forever.

### 2. Single opponent-seater, room-sourced (Fork A: room-only for now)

All opponent entry funnels through **one** seating chokepoint. Sourcing order
when the router/narrator names no opponent:

1. Router-named `npcs_present` (existing).
2. **Room scan** of `snapshot.npcs` at the acting PC's location — NPCs *and*
   bestiary mobs (the same roster, distinguished by `bestiary_id`), seated as
   `side="opponent"` for an adversarial confrontation (not `neutral`).
3. If still none → raise `NoOpponentAvailableError`. The dispatch handler
   (`run_confrontation_dispatch`) already catches this and lets the narrator
   render prose.

Bestiary / encounter-table pull (a *new* pursuer arriving) is **explicitly
deferred** — room-only for this round.

This resolves the `EncounterActor.side` contract violation: the engine *does*
legitimately own opponent-seating for adversarial confrontations. Update that
docstring to say so, and have the seater emit `participant.joined{source, side}`
so the GM panel can answer "why is this raider in my chase?" (OTEL Observability
Principle).

### 3. Generalize the empty-opponent guard — staged rollout

The `NoOpponentAvailableError` guard, today gated on `category == "combat"`,
generalizes to all **adversarial** confrontations. To avoid regressing the
social-first packs (`victoria`, `tea_and_murder`) without playtest validation,
roll out in stages:

- **Now (59-13):** enforce for `movement` (chase). Combat already enforces.
- **Follow-up:** extend to `social` / `pre_combat` after validating against the
  social packs — a negotiation/trial also needs a counterparty, but the failure
  mode must be confirmed against real social-pack flows first.

### 4. End-on-no-Other (Wild Card #9, accepted)

A confrontation resolves when its last live opponent leaves — the **mirror** of
the existing player-side rule in `yield_action.py`. When an opponent becomes
`withdrawn` (yield, defeat, flee, talked-down) and
`opponent_alive_count` drops to 0, resolve the encounter
(`resolved=True`, `outcome` reflecting the disposition) and emit
`participant.left{reason}`. A confrontation ends because there is no longer an
Other — not only because a dial hit threshold.

## Consequences

**Positive**
- One seating chokepoint replaces three disagreeing paths — the actual root cause.
- The "needs an Other" invariant is one architectural truth that covers combat,
  movement, and (staged) social/pre_combat — patching only chase would leave the
  same bomb under the other categories.
- Membership becomes legible on the GM panel via `participant.joined/left` spans.
- Symmetric lifecycle (player-exit and opponent-exit both resolve) — tidy.

**Negative / risks**
- Generalizing the guard could regress social packs if rolled out unstaged —
  hence §3's staging. Watch `victoria` / `tea_and_murder`.
- End-on-no-Other changes resolution semantics: an encounter can now end without
  a dial reaching threshold. Existing resolution consumers must tolerate this
  (they already do for player-side yield).

**Design-for, don't-build (out of scope, keep the seam open)**
- **Mid-scene recruitment** (guards arrive, allies join) — the reason entry
  should be event-shaped, not an instantiation snapshot. Don't build now; don't
  foreclose.
- **Bestiary / encounter-table opponent sourcing** — Fork A deferred.

## Alternatives considered

- **Patch chase only** (fourth special case in `_npc_fallback_at_location`):
  rejected — buries the same bomb under every other confrontation type and adds
  a third disagreeing seating path.
- **New first-class `Participant`/membership type**: rejected (reuse-first) —
  `actors`/`side`/`withdrawn` already model the set; the gap is discipline, not
  data.
- **Let one-sided confrontations stand and have the narrator populate later**
  (the 45-33 position): rejected — nothing populates the later beat; the dial
  freezes. This ADR overturns it.

## Testing guidance (for TEA)

Per this repo's "No Source-Text Wiring Tests" rule, prove wiring via OTEL spans
and fixture-driven behavior, never by grepping source:

- Fixture-drive `instantiate_encounter_from_trigger(encounter_type="chase",
  npcs_present=[])` with a room-present NPC/mob → assert an `opponent`-side actor
  is seated (not neutral); with an empty room → assert `NoOpponentAvailableError`.
- End-to-end: chase instantiated via the production path → advance → assert
  opponent dial moves off 0 and phase transitions (the AC1 the story already
  wanted, now hung on the corrected seam).
- End-on-no-Other: withdraw the last opponent → assert `resolved=True` and a
  `participant.left` span.
