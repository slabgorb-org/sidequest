---
id: 153
title: "The Ace of Aces Dogfight — A Homebrew Relative-Position Positioning Graph Feeding Bound SWN Resolution, the Positioning/Resolution Firewall, and Narrator-Motivated Maneuver Selection"
status: accepted
date: 2026-06-26
deciders: ["Keith Avery", "Atlas the Endurer (Architect)"]
supersedes: [77]
superseded-by: null
related: [6, 20, 33, 67, 74, 77, 104, 105, 113, 114, 116, 117, 123, 125, 142, 143]
tags: [game-systems, agent-system, observability]
implementation-status: deferred
implementation-pointer: null
---

# ADR-153: The Ace of Aces Dogfight — A Homebrew Relative-Position Positioning Graph Feeding Bound SWN Resolution, the Positioning/Resolution Firewall, and Narrator-Motivated Maneuver Selection

**Supersedes:** [ADR-077](077-dogfight-subsystem.md) (Dogfight Subsystem via StructuredEncounter Extension).

## Context

### What the dogfight is supposed to be

The dogfight is SideQuest's fighter-vs-fighter duel: single-seat strike craft,
each pilot committing a maneuver in secret per turn, the relative geometry of
the two ships emerging from the cross-product of both commits. The design
lineage — though ADR-077 never named it — is **Ace of Aces** (Nova Game
Designs, 1980): two pilots, two identical gamebooks, and a single brilliant
constraint — *you only ever see your own cockpit view*. There is no top-down
board, no god's-eye map. Each round both pilots secretly pick a maneuver; you
cross-index the pair, turn to the page it sends you to, and *now* you see the
enemy from your new windscreen — on your tail, crossing, overshooting. When
the enemy sits in your gunsight, you fire. The thick book is really a **graph
of relative-position states** and their transitions under every maneuver pair.

ADR-077 had this instinct exactly right ("each pilot, secret commit… cross-
product lookup of both commits… per-pilot descriptor… sealed-letter then
revealed… render cockpit POV, never narrate geometry not present in the
descriptor"). It is Ace of Aces. The author simply did not build out the
state graph, and a later rework grafted a homebrew win condition on top that
broke the whole thing.

### What it actually is now (the 2026-06-25 playtest forensics)

A full-stack `/sq-playtest` sweep of `space_opera/coyote_star` (SWN) surfaced
five findings (158-29/30/31/34/35). Tracing them through code revealed the
live `dogfight` ConfrontationDef declares **three mutually-contradictory
resolution paradigms at once**:

- `resolution_mode: sealed_letter_lookup` — the ADR-077 maneuver cross-product.
- `win_condition: dial_threshold` + `player_metric`/`opponent_metric` (energy,
  threshold 30) + a full `beats:` list — the **native dial/beat engine** (the
  pre-port homebrew that SOUL doctrine forbids us from balancing).
- SWN frame stats (hp/ac/armor/pilot_skill/weapon) + `geometry_modifiers` —
  the [2026-05-27 dogfight×SWN compatibility spec](../superpowers/specs/completed/2026-05-27-dogfight-swn-compatibility-design.md)'s
  "layer SWN shots onto the cross-product" work.

These cannot all decide the duel. The SWN shot layer **does** fire, rolls
d20s, ablates frame HP to 0 — and then nothing happens, because
`win_condition: dial_threshold` only checks whether the energy dial reached
30, and the sealed-letter path never touches that dial. A correctly-seated
dogfight ablates the enemy to 0 HP and keeps flying forever, waiting for a
metric nothing increments. The 2026-05-27 spec explicitly intended
`win_condition: hp_depletion`; that single field never reached content.

Worse, in practice the *real* dogfight rarely even instantiates:

- **158-29:** ship-combat verbs match dogfight verbs but the IntentRouter
  dispatch bank *declines* (`confrontation_verb_unrouted`); with no engine
  seated, the narrator grinds the SDK tool loop to `max_turns=8` and
  **hard-crashes the turn** (`disconnect_save` + room teardown) instead of
  degrading loudly (ADR-006).
- **158-31:** what the playtester fought as a "dogfight" ran `apply_beat`
  (push beats, `resolution_beat:straight`) — provably *not* the sealed-letter
  path (which blocks the legacy beat loop). It was a generic native combat
  stood up in place of the dogfight; push "Success" moved the dial by zero and
  it resolved after one beat regardless of the threshold.
- **158-34:** when the seater *does* run, `_SHIP_SCALE_CONFRONTATION_TYPES`
  contains only `{"ship_combat"}` — not `"dogfight"` — so the seater consults
  the co-located-NPC fallback and seats a Monster-Manual *ground* creature
  ("Gengineered Killer") as the enemy fighter. The chassis registry (ADR-125,
  the Kestrel) is never consulted; no scale/kind check exists.
- **158-30:** a resolved dogfight resurrects — `husk_reaped` clears it at turn
  start, then `continued_same_region_drift` re-attaches it the same turn with
  no `created_turn`/`resolved` check, resetting Resolution→Setup and soft-
  locking the player into ship maneuvers on foot.
- **158-35:** dice-replay re-entry re-emits the prior turn's narration, leaving
  the dogfight unnarrated.

### The doctrine the old design violates

SOUL.md (*Bind the Ruleset, Don't Balance It*) and [ADR-143](143-wwn-binding-replaces-native-combat.md)
ruled it doctrine: a native mechanic must never be *balanced against* a bound
ruleset. The current dogfight is precisely that anti-pattern — a native
energy-dial **competing with** SWN HP for the right to decide who dies. Two
systems answering "did I hurt you, are you dead" is the trap we always lose.

ADR-077 also predates the Rust→Python port (ADR-082), pluggable ruleset
modules (ADR-117), the WN binding family (ADR-142/143), the IntentRouter
dispatch bank (ADR-113/123), the chassis/rig entity (ADR-125), and the
ablative-HP substrate (ADR-114). It is a pre-port artifact whose plumbing the
rest of the engine grew up around without a contract. Patching the five
findings individually keeps five seams limping while the contradiction at the
center regenerates. **This is a rebuild, not a patch.**

## Decision

Rebuild the dogfight as **Ace of Aces positioning feeding bound SWN
resolution, with a hard firewall between them.** Eight decisions:

### 1. The dogfight is a positioning *subsystem*, not a resolution *ruleset*

Ace of Aces does not answer "did I hurt you, are you dead." It answers "**who
has the shot, and from what angle?**" That is a *positioning* problem, wholly
orthogonal to SWN's resolution. Because the two systems do not overlap, there
is nothing to balance against each other — the homebrew is doctrine-legal.

The positioning subsystem is therefore **not** a `RulesetModule` (ADR-117).
Those *are* the resolution rulesets (SWN/WWN/CWN/Fate/native). We are not
adding a sixth combat-resolution ruleset to balance. The dogfight is a
confrontation subsystem that **delegates all resolution to whatever
`RulesetModule` the genre already binds** — SWN for `space_opera`. (This makes
it genre-portable later — a CWN vehicle joust, a WWN wyvern duel — but that is
out of scope here; `space_opera` only.)

### 2. The positioning/resolution firewall

This is the load-bearing invariant and the reason the homebrew is legal:

> **The positioning subsystem never computes damage and never decides death.
> The instant a trigger is pulled, control passes to the bound ruleset.**
> Positioning emits only: relative geometry (the new descriptor), a
> `gun_solution` boolean, and a geometry-derived to-hit modifier
> (aspect/range). Hull, hit, and kill are 100% SWN.

Concretely:

- **Win condition = SWN `hp_depletion` on hull.** This is the single field
  that kills the contradiction.
- **Delete the native graft from the dogfight def:** remove `win_condition:
  dial_threshold`, `player_metric`/`opponent_metric`, and the `beats:` list.
  The dogfight path **never** calls `apply_beat` and **never** touches a dial.
- **Energy survives, but only as the maneuver budget** — what you can afford to
  fly this turn (loop costs 30, straight recovers). It is a positioning
  resource, never a win track.
- **Refuse the original gamebook's damage model.** Real Ace of Aces marks
  bullet hits ("2 grazes = a kill"); ADR-077's MVP copied it
  (`graze/clean/devastating`, `damage_increments`, `starting_hull`). Those are
  deleted. The 2026-05-27 spec already saw this ("Cells no longer carry
  damage. SWN does 100% of hit and damage"); we ratify it as doctrine.

### 3. The full relative-position state graph

The feel of Ace of Aces lives in the *graph*, not a single flat table.
Resolution is **(my maneuver × your maneuver × current relative state) → new
relative state**, looked up per-state. Build out the graph the prototype
stubbed:

- **Live today:** `merge`, `tail_chase` (authored interaction tables).
- **Stubbed `future` in `descriptor_schema.yaml`:** `beam`, `overhead`.
- **Add:** `scissors`, `overshoot` (the emergent "he got on my tail, I broke
  hard, we overshot into a scissors" beats).
- **Extend-and-return:** when the engagement breaks apart with no gun solution,
  geometry resets toward `merge` with energy carried over (an engine rule with
  a content override hook, per ADR-077 Open Question #5).

Each state's transition table is **authorable content** (no engine code per
state). The ADR records the *model*; the cells live in
`genre_packs/space_opera/dogfight/`. The interaction cells carry geometry and
`gun_solution` only (firewall §2).

### 4. Narrator-motivated maneuver selection (the opponent ace's "brain")

Ace of Aces assumes two humans; solo/co-op play means the enemy ace must pick
its own maneuver each turn. The split mirrors how NPC beats already work — the
narrator chooses the *move*, motivated by character; the engine resolves the
*mechanics*:

- **Narrator owns intent.** The ace's maneuver each turn flows from its
  goal/disposition (ADR-020) — *revenge*, *escape*, *protect the convoy*,
  *prove itself* — chosen from the legal menu the engine offers. This is the
  same authority the narrator already holds for any NPC beat. An ace out for
  revenge presses a loop into your six on fumes; a scout ordered to report
  banks for the exit and runs. Picking a *maneuver from a menu* is not
  geometry-composition (which the LLM must never do — §5); it is a discrete
  choice, exactly like a beat.
- **Engine owns legality + geometry deterministically.** It gates the menu by
  energy and pilot tier (Rookie→Ace; `pilot_skills.yaml`), resolves the sealed
  cross-product into the new geometry, and sets the `gun_solution` flag. It
  never picks the move and never invents position.
- **SWN owns the trigger-pull.** Hit, hull, kill.
- **Deterministic disposition fallback (ADR-006).** If the narrator pass is
  skipped or fails, a deterministic disposition-derived policy ("aggressive ace
  → press; routed rookie → disengage") keeps the duel moving so a turn never
  wedges. The fallback is the floor, not the default.

Skill tier gates the *menu* (an Ace can fly moves a Rookie cannot); motivation
drives the *choice*. The difference between a Rookie-who-wants-to-live and an
Ace-out-for-blood is character, not a flat skill dial.

### 5. Sealed simultaneous commit + cockpit-POV perception

Two properties make this a dogfight and not a slugfest, and both are *additive*
to the normal motivated-NPC + SWN loop:

- **Sealed simultaneous commit** — both pilots choose blind, at once, then
  reveal (normal beats are sequential reactions). Reuses the existing
  sealed-letter / TurnBarrier infrastructure.
- **POV-only perception** — each pilot gets cockpit prose + their own
  descriptor; **never a shared map**. The perception firewall (ADR-104/105) is
  the hook: each pilot's descriptor is their perceptual filter. The narrator
  renders strictly from the descriptor and never narrates geometry not present
  in it (ADR-067 narration contract; the SOUL "never invent geometry" rule).

### 6. Opponent is a ship/chassis, never a co-located creature

- The dogfight opponent is seated as a **ship/chassis** (ADR-125), from the
  def's `opponent_default_stats` frame and/or the world's chassis registry —
  never the nearest co-located Monster-Manual creature.
- **Add `dogfight` to the ship-scale confrontation set** so the co-located-
  ground-creature fallback can never fire for it (158-34). A scale/kind guard
  fails loud if a personal-scale creature is ever proposed as the enemy vessel.
- A dogfight requires an Other (ADR-116): if no hostile chassis can be sourced
  or instantiated, fail loud rather than seat a wrong-scale stand-in.

### 7. The router → seater → lifecycle contract

The 2026-05-27 spec predates the IntentRouter dispatch bank; this is the genuinely
new design surface, and it owns findings 158-29/30/35:

- **Loud degradation, not a crash (158-29).** When the router matches dogfight
  verbs, it must dispatch the dogfight seater. If the engagement cannot seat,
  it degrades *loudly and observably* (ADR-006) — it must never leave the
  narrator to grind the SDK tool loop into a `max_turns` crash + session
  teardown. *(The general "`max_turns` should degrade, not wedge" robustness
  gap is tracked separately as a narrator-robustness item; this ADR only
  guarantees the dogfight path degrades.)*
- **No resurrection (158-30).** `continued_same_region_drift` must carry over
  only a **live** encounter; it must never re-attach a `resolved`/`husk_reaped`
  encounter, and must respect the `created_turn` fresh-this-turn exemption. A
  reaped duel stays reaped.
- **No stale narration (158-35).** Dice-replay / dogfight-shot re-entry narrates
  the *resolved beat* (the maneuver, the gun pass, the outcome), not the prior
  turn's text.

### 8. OTEL observability (CLAUDE.md, non-negotiable)

Every decision the subsystem makes emits a span so the GM panel is the lie
detector: `dogfight.confrontation_started`, `dogfight.maneuver_committed`
(per pilot, with the chosen maneuver_id and — for the NPC — the motivating
stance/source: narrator vs. fallback), `dogfight.cell_resolved` (from-state,
to-state, gun_solutions), and the SWN-side `dogfight.shot_attempted` /
`dogfight.shot_damage` (d20, AC, AP, applied, hull after). The state-graph
transition and the NPC's stance source are the two spans that prove the engine
chose the move and the geometry — not the narrator improvising.

### 9. Supersede ADR-077

ADR-077 is marked `superseded-by: 153`. Its core decision (native sealed-letter
resolution with cell-carried damage) is contrary to current doctrine. Its
*instinct* (sealed-letter cockpit POV, per-pilot descriptor, no improvised
geometry) is preserved and carried forward here.

## Consequences

### Positive

- **Doctrine-clean.** No native mechanic balanced against SWN; the firewall
  makes positioning and resolution orthogonal. Binding the ruleset *is* the
  balance decision (SOUL / ADR-143).
- **Deletes more than it adds.** The native dial/beats/metrics and the
  cell-carried damage model are removed; the surviving machinery (sealed-letter,
  descriptor, SWN shot layer, pilot tiers) is finished and rewired, not
  reinvented. No saves to migrate.
- **The favorite feature actually runs.** Fixing the seater + router contract
  means players reach the dogfight engine instead of an improvised generic
  combat.
- **Living-World opponents.** Motivated maneuver selection makes the enemy ace
  a character (revenge, flight, duty), not a skill dial — and it's
  OTEL-observable, so the GM panel can tell motivation from improvisation.
- **Genre-portable later.** A positioning subsystem that delegates to the bound
  ruleset can be reskinned to other genres' duels without new resolution code.

### Negative

- **Content authoring load.** A full state graph (6+ states × per-state
  maneuver-pair tables) is real content work. Mitigated: it is pure YAML,
  authorable incrementally, and the model lets us ship `merge`+`tail_chase`
  first and grow the graph.
- **Two commit shapes in one engine.** The sealed simultaneous commit differs
  from sequential beats; the dispatch/handler layer must keep both straight.
  Mitigated: the sealed-letter path already exists and is exclusive of the beat
  loop.
- **A removed-field migration.** Deleting `dial_threshold`/metrics/`beats`/
  `damage_increments`/`starting_hull` from the dogfight def + models touches
  several files and their tests. Mitigated: mechanical, and the validator
  catches stragglers.

### Risks

- **Positioning balance (the one real calibration risk).** The interaction
  cells encode rock-paper-scissors among maneuvers; bad cells make the game
  *solved* (one maneuver dominates) or *incoherent* (no maneuver helps). This
  is genuinely bounded and tractable — unlike lethality math, it never spirals,
  because lethality is entirely SWN's. **Mitigation:** the `playtest/` scaffolds
  are the calibration gate; tag each cell and tune before expanding the graph.
- **Narrator stance honesty.** The narrator could pick a maneuver inconsistent
  with the ace's stated goal. **Mitigation:** the chosen maneuver_id + stance
  source are OTEL-logged; the GM panel surfaces incoherent picks, and the
  deterministic fallback bounds the worst case.
- **Extend-and-return tuning.** The auto-reset-to-merge rule can feel abrupt or
  loop forever if mis-tuned. **Mitigation:** start with the simple engine rule,
  add the content override only if playtest demands it.

## Alternatives Considered

- **A — Collapse the dogfight into `ship_combat`.** Delete the distinct
  confrontation; fighter duels become a scale variant of the working crewed
  `ship_combat` (`beat_selection` + `hp_depletion` + chassis). Cheapest and
  most doctrine-pure. **Rejected:** it throws away the Ace of Aces secret-
  commit positioning game, which is the entire reason the dogfight exists. The
  feel is the point.
- **B — Keep the native energy-dial and tune it against SWN.** **Rejected
  emphatically** — this is the exact balancing trap SOUL/ADR-143 forbid, and it
  is what broke the current dogfight. We remove the native engine from this
  path, we do not balance it.
- **C — Model the dogfight as a new `RulesetModule`.** **Rejected:** `RulesetModule`
  is the resolution-ruleset seam; a sixth combat ruleset is a sixth thing to
  balance. The dogfight resolves through the genre's already-bound module.
- **D — LLM picks everything (maneuver *and* geometry) each turn.**
  **Rejected:** composing 3D geometry across turns is the precise failure mode
  ADR-077 and SOUL forbid; it is unverifiable and reintroduces the "narrator
  winging it" risk. The LLM picks the *move from a menu*; the engine composes
  the geometry.
- **E — Deterministic-only opponent brain (no narrator).** **Rejected** (the
  Architect's first proposal, corrected in brainstorming): a flat skill-tier
  policy makes every ace fly the same and ignores plot. NPC motivation is the
  narrator's job; the engine only gates legality and resolves geometry.

## Relationship to prior art

- **Supersedes [ADR-077](077-dogfight-subsystem.md)** — preserves its sealed-
  letter cockpit-POV instinct; refuses its native-damage model and its
  unfinished single-table scope.
- **Consolidates the [2026-05-27 dogfight×SWN compatibility spec](../superpowers/specs/completed/2026-05-27-dogfight-swn-compatibility-design.md)**
  — that spec's layered "positioning feeds SWN, cells carry no damage,
  `hp_depletion` win" intent was correct but only partially landed (the
  `dial_threshold` win condition shipped instead). This ADR ratifies the intent
  as doctrine and adds the state graph + router/seater/lifecycle contract the
  spec could not have covered.
- **Defers** the multiplayer "Guitar Solo" concurrent-thread problem (what the
  rest of the table does during a 1v1 dogfight) to the
  [spotlight-cardinality roadmap](../superpowers/specs/2026-05-29-spotlight-cardinality-roadmap.md)
  Spec 2. PvP dogfights (both pilots players) remain out of scope.

## Implementation status (2026-06-26)

**Accepted; implementation deferred to the epic-158 dogfight rebuild track.**
The five playtest findings fold into this rebuild rather than being patched
individually:

| Finding | Folds into decision |
|---|---|
| 158-31 (mechanically inert / hollow dial) | §2 firewall — `hp_depletion`, delete native dial/beats |
| 158-34 (ground creature seated as ship) | §6 opponent = ship/chassis + ship-scale set |
| 158-30 (resolved dogfight resurrects) | §7 lifecycle — drift carries only live encounters |
| 158-35 (post-beat narration desync) | §7 lifecycle — narrate the resolved beat |
| 158-29 (router decline → max_turns crash) | §7 router contract — loud degradation (dogfight path); general `max_turns` robustness tracked separately |

Next step: an implementation plan (via the writing-plans skill) decomposing the
rebuild into ordered, independently-mergeable stories, and reslating epic 158's
dogfight stories against this ADR.
