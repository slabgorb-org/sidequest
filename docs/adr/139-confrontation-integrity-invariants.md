---
id: 139
title: "Confrontation Integrity Invariants — Win-Condition Liveness, Seated-Actor HP Durability, the Mechanically-Capable Other, and the Dispatch Applicability Gate"
status: accepted
date: 2026-06-04
deciders: ["Keith Avery", "The White Queen (Architect)"]
supersedes: []
superseded-by: null
related: [33, 59, 93, 113, 114, 116, 117, 123, 126]
tags: [game-systems, observability]
implementation-status: partial
implementation-pointer: "sidequest-server/sidequest/game/ — confrontation resolution + ADR-059 monster_manual injection + opponent-seater; first impl on FIXER branches fix/eh-opp-damage and fix/eh-magic-gate (2026-06-04 burning_peace playtest); verification home = Epic 73 Confrontation Engine Hardening"
---

# ADR-139: Confrontation Integrity Invariants

> **Amends ADR-116, does not supersede it.** ADR-116 guaranteed that *a
> confrontation requires an Other*. This record strengthens that contract for the
> pluggable-ruleset era (ADR-117): the Other must be able to *fight*, reaching the
> win state must *end* the fight, and the per-turn world refresh must *respect*
> in-encounter state. Triggered by the 2026-06-04 `elemental_harmony/burning_peace`
> (WWN) playtest, where a confrontation could be **neither lost nor won**.

## Context

The 2026-06-04 `burning_peace` (WWN ruleset) solo playtest exposed four independent
confrontation defects that combine into an **unbreakable infinite stalemate** plus a
dead magic subsystem. All four were measured against OTEL spans + the Postgres save,
not asserted from narration:

1. **Opponent deals 0 HP damage.** The seated Other was the generic group token
   `"Approaching Riders"` (HP 8/8, `manual_origin=False`) with **no damage spec** —
   every reprisal logged `dice.opponent_reprisal_damage_spec_missing` and the player
   HP never moved, even on a *failed* player beat (Strike total=4 → still 10/10).
   Meanwhile the four *statted* named riders the monster manual produced (Seok of
   Ancient Fortress HP 24, Agialik Huitane 16, Younghwari Daekwoomun 40, Nimbārka of
   the Thin Peak 32, all `disposition=-18`) sat **unseated** in `snapshot.npcs`.
2. **Win-condition never fires at 0 HP.** A CritSuccess (`total=22 beat_id=cast_spell
   resolved_encounter=False`) zeroed the opponent (`HP 0/8`), yet the encounter stayed
   `resolved=False active=True structured_phase=Escalation`, the UI kept offering the
   same attack beats, and **no `hp_depletion`/victory span fired at all**.
3. **Opponent HP resets every turn.** The very next beat the opponent was back to
   `HP 6/8`. Cause: `monster_manual.injected ... in_combat=True patches=11` fires on
   **every** combat turn, re-materializing the seated opponent and clobbering its
   damaged HP back up.
4. **`magic_working` dispatch hard-fails on WWN.** Channeling routed to the ADR-126
   pact-working `magic_working` dispatch, which requires a populated
   `snapshot.magic_state` — but a WWN world's `magic_state = null`, so every channel
   raised `MagicWorkingParseError('... world has no magic_state loaded')`. The
   narrator still narrated the fire (textbook "convincing prose, zero mechanical
   backing").

Plus a data-hygiene defect in the same encounter: **Yield** tore down the UI but left
the snapshot `encounter` at `resolved=False, outcome=None`, seated actors intact.

**Why this is an architecture decision, not four bug tickets.** Epic 86
(`road_warrior → CWN`) and Epic 87 (`heavy_metal → WWN`, the *second* WWN pack) are
about to build SRD combat on this exact machinery. Every one of these defects lives in
the **confrontation engine + world-materialization + dispatch seams — beneath any
`RulesetModule`** (ADR-117). They are ruleset-agnostic: native, swn, cwn, and wwn all
re-incur them. Without a governing invariant, both SRD-port epics inherit a combat loop
that can neither end nor deal damage. ADR-116 closed "does an Other exist?"; it never
asked "can the Other fight, does reaching the win-state end the fight, and does the
hourly world-refresh heal a wound the player just dealt?"

## Decision

Four invariants on the confrontation engine, each with a **load-bearing OTEL span**.
Per the project's Illusionism-detector principle, *an invariant you cannot observe is an
invariant you cannot trust* — the GM panel is the lie detector, so each invariant ships
the span that proves it engaged.

### Invariant 1 — Win-Condition Liveness (the terminal state must resolve)

For any `win_condition` whose terminal predicate is a **state threshold** —
`hp_depletion` (a seated opponent's `core.hp.current ≤ 0`), `dial_threshold`,
opponent-yield — **reaching that state MUST resolve the encounter**, independent of
whether a beat carried `resolution: true`. Resolution is evaluated on **state**, not
gated on a beat opting in.

- **Span:** `confrontation.win_condition_evaluated { win_condition, terminal_reached,
  outcome }` every turn a seated actor crosses (or sits past) the threshold.
- Closes the known "exit beats need `resolution: true`; prose `consequence:` is inert"
  trap **at the win-condition layer**, not merely the exit-beat layer.

### Invariant 2 — Seated-Actor HP Durability (the encounter owns current HP)

Per-turn world materialization (ADR-059 `monster_manual` injection) **MUST NOT
overwrite the `core.hp.current` of an actor already seated in an active encounter.**
Injection may *add* new combatants and may set HP for *new* actors; for an actor the
encounter already seats, **the encounter is the authority on current HP** and the
injection preserves it.

- **Span:** `monster_manual.injection_hp_preserved { actor, seated, preserved_hp }`
  (per-actor preserve/overwrite decision) so the panel shows the refresh did not heal a
  damaged Other.

### Invariant 3 — The Mechanically-Capable Other (extends ADR-116)

ADR-116 requires an Other. This ADR strengthens it: **a damage-resolved encounter must
seat an Other that can actually deal damage.** A toothless Other is as invalid as no
Other. But the 2026-06-04 fix established *where the teeth come from* — and it is **not**
where the first draft of this ADR assumed:

1. **The engine MUST detect, at instantiation, whether the seated Other has a resolvable
   reprisal damage source** — mirroring the runtime reprisal priority exactly
   (confrontation-def `opponent_damage` → beat `damage_override` → the actor's inventory
   weapon) — and emit the toothless span when none of those resolves. The lie-detector
   fires at **seat time**, not six rounds deep.
2. **The engine MUST NOT fabricate a default damage spec** (No Silent Fallbacks), and
   **MUST NOT assume a "statted" combatant supplies damage.** Seating a named statted
   actor over a generic crowd token does *not* fix toothlessness on its own — a seeded
   monster-manual actor carries **no inventory weapon**, so `resolve_damage` returns
   `None` for it just as it does for the crowd token. Preferring the statted actor is
   still correct for Diamonds-and-Coal/ADR-059 reasons, but it is **not** the damage
   lever.
3. **The damage lever is authored content.** A damage-resolved confrontation MUST author
   `opponent_damage` (a `DamageSpec`) at the **confrontation-def level** — as
   `space_opera` (67-10) and now `elemental_harmony` (#16) do — because seeded mooks have
   empty inventories. A toothless Other is therefore a **content defect surfaced loudly
   by the engine**, never auto-healed.

- **Span:** `encounter.opponent_toothless { opponent, encounter_type, checked_sources }`
  **at instantiation** — emitted when the seated Other has no resolvable reprisal damage.
  Silent on a properly-armed Other.

### Invariant 4 — Dispatch Applicability Gate (a subsystem dispatch must fit the world)

A subsystem dispatch **MUST NOT be emitted for a world that structurally cannot service
it.** Specifically, the `magic_working` dispatch (ADR-126 pact-working `MagicPlugin`) is
gated on **plugin presence, not the ruleset slug** — concretely, on whether
`snapshot.magic_state` is populated. The pact-working ledger is loaded at chargen only
for worlds that ship a `magic.yaml`; where it is absent the dispatch is dropped before
the bank runs and the channel/cast falls through to the existing narrator/beat path (a
dedicated ruleset spellcasting/Effort route is a follow-up, not a precondition).

> **Gate on the plugin, not the slug.** It is tempting to gate by ruleset
> (`wwn`/`swn`/`cwn` ⇒ no pact-working magic), but that is wrong: `space_opera` is
> `swn` yet its `coyote_star` world ships a `magic.yaml`, so its `magic_state` *is*
> populated and channeling there must pass through. The bound magic plugin — surfaced as
> `magic_state is None` — is the correct discriminator. (WWN magic lives on the
> character `core`, so a WWN world's `magic_state` stays `None` and is gated.)

- Generalizes ADR-113's honesty caveat ("every dispatch in the package fires, no
  confidence gating") into a **structural applicability gate keyed on plugin presence,
  not pack and not ruleset slug**.
- **Span:** reuse the existing GM-panel-wired `intent_router.dispatch.gated`
  (`subsystem=magic_working`, `reason="snapshot.magic_state is None …"`) — no new span
  type. Suppression is a *decision*, not silence — we suppress **loudly** (No Silent
  Fallbacks: we do not `try/except` the error away downstream; we never emit the
  inapplicable dispatch in the first place).

### Corollary — Yield resolves the snapshot

The yield path MUST stamp the snapshot `encounter` `resolved=True, outcome=yielded` and
clear seated actors, not only tear down the UI. (Forensics + resume correctness.)

## The OTEL contract

| Invariant | Span | The lie it detects |
|-----------|------|--------------------|
| 1 Win-condition liveness | `confrontation.win_condition_evaluated` | "I beat them" but the encounter never ended |
| 2 Seated-HP durability | `monster_manual.injection_hp_preserved` | the world-refresh secretly healed a wounded Other |
| 3 Capable Other | `encounter.opponent_toothless` (at instantiation) | the Other can't actually hurt you (content gap, surfaced loudly) |
| 4 Dispatch gate | `intent_router.dispatch.gated` (`subsystem=magic_working`) | a channel narrated as resolved that the engine couldn't service |

## Consequences

- **Epics 86 (CWN) and 87 (WWN) inherit a confrontation loop that can deal damage, can
  end, and is observable.** Their `RulesetModule`s supply damage specs and spellcasting
  paths; the engine guarantees liveness, durability, capability, and applicability
  *beneath* them. This is the precondition that makes the two SRD ports safe to start.
- **ADR-116 is amended** — "an Other" becomes "a mechanically-capable Other."
- **First implementation** is the FIXER work from the 2026-06-04 `burning_peace` session
  (branches `fix/eh-opp-damage` = Invariants 1–3, `fix/eh-magic-gate` = Invariant 4).
  The `calling_label` (chargen) and combat-player-echo (UI) fixes from the same session
  are *unrelated* and **not** governed by this ADR.
- `implementation-status: partial` until those PRs merge **and** a confrontation-
  hardening verification confirms all four spans fire in a live WWN combat.

## Alternatives considered

- **Fix it inside the WWN `RulesetModule`.** Rejected — the defects are *beneath* the
  RulesetModule seam; `native`/`cwn`/`swn` would re-incur them. ADR-117's whole point is
  that the engine owns cross-ruleset invariants.
- **Default damage spec only (skip the statted-combatant preference).** Rejected as the
  *primary* path — seating the statted named combatant honors Diamonds-and-Coal and
  ADR-059; the group default is the fallback when no statted actor exists.
- **Make the narrator responsible for ending the fight.** Rejected — Illusionism. The
  engine must own resolution; narration *honors* it. Narrator-owned resolution is
  exactly the "convincing prose, zero mechanical backing" failure the OTEL principle
  exists to catch.

## Relationship to existing stories

Epic 73 **Confrontation Engine Hardening** is the natural implementation/verification
home. Recommend filing a story — *"Confrontation integrity invariants (ADR-139):
win-condition liveness + seated-HP durability + capable-Other + dispatch applicability
gate, with the four OTEL spans"* — and **gating the Epic 86/87 combat stories on it** so
the SRD ports do not build on unhardened combat. The in-flight FIXER PRs satisfy the
code; the story owns the verification (all four spans fire end-to-end in a live WWN
fight) and the ADR-116 amendment note.
