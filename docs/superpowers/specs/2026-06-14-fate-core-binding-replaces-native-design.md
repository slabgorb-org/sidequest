# Fate Core Binding Replaces the Native Ruleset — Design & Decomposition

**Date:** 2026-06-14
**Author:** Neo (Architect)
**Decision of record:** ADR-144 (`docs/adr/144-fate-core-binding-replaces-native-ruleset.md`)
**Status:** Governing design — F1 is the next sub-project to plan

> This document is the engineering design and epic decomposition behind ADR-144. The ADR
> records *the decision*; this records *the architecture and the work*. Each epic (F1–F5)
> gets its own spec → plan → implementation cycle; this is the map they hang from.

---

## 1. One-paragraph summary

Remove the homebrew `native` ruleset and bind a second published SRD — **Fate Core**
(Evil Hat, CC-BY) — for the four narrative-first genres native was the default for
(`pulp_noir`, `tea_and_murder`, `wry_whimsy`, `spaghetti_western`). The Without Number
family keeps the other eight packs. End state: **two pre-balanced SRDs, zero homebrew
rulesets**. The implementation mirrors `wn_round.py` one tier over: a `FateRulesetModule`
plus a `fate_conflict.py` exchange engine, dispatch-routed by module type, with the native
beat/dial/edge/reprisal machinery deleted once no pack binds it.

## 2. Why (the load-bearing constraint)

SideQuest is building two hard things — an **AI GM** and a **content engine**. A third hard
thing — a homebrew ruleset we balance by hand — is what keeps breaking the project (ADR-143,
the repeatedly-undone WN/native hybrid). **Bind the Ruleset, Don't Balance It** (SOUL.md):
we adopt published, balanced math and pour content into it. Fate Core is the canonical-best
system for detective/social/dramatic genres, it *is* Fortune-in-the-Middle (the SOUL purpose
statement), and its **aspects are free-text → prompt fragments**, a uniquely strong synergy
with an LLM narrator.

## 3. Current state (what exists, what we build on)

- **Seam:** `sidequest-server/sidequest/game/ruleset/` — `base.py` (`RulesetModule` ABC),
  `registry.py` (fail-loud resolver), `native.py` (to delete), `without_number.py` + family.
- **Precedent:** `sidequest-server/sidequest/server/dispatch/wn_round.py` — a bound ruleset
  owns its round engine; dispatch routes by `isinstance`; native dispatch untouched; reuses
  the ADR-036 sealed submit-and-wait barrier.
- **Pack bindings (2026-06-14):** 8 packs WN (`wwn`×3, `swn`, `cwn`×2, `awn`), 4 packs native
  (the Fate targets). One file per pack: `genre_packs/<pack>/rules.yaml` → `ruleset:`.
- **The seam is native/WN-shaped** by admission (`base.py` Spec-0 note): abstract
  `compute_dc(beat)`, `apply_beat`, `attack_params → AttackRollParams`, ability-score
  `stat_modifier`. Optional methods already use the default-raise pattern
  (`ship_attack_params`, `save_params`, `roll_initiative → None`, etc.).
- **Ruleset-specific character/advancement is already a thing:** `awards_native_turn_xp`
  gate (native ticks XP; WN does not). Fate will return `False` and use milestones.

## 4. Target architecture

### 4.1 Module + conflict engine (mirrors `wn_round.py`)

```
ruleset/fate.py            FateRulesetModule  (slug = "fate")
ruleset/fate_resolution.py resolve_action(skill_rating, opposition, invokes) -> Outcome
server/dispatch/fate_conflict.py   the exchange engine
```

- `FateRulesetModule` implements **only the Fate-shaped surface**; the d20-shaped abstracts
  are demoted to default-raise (see 4.4). Dispatch selects the conflict engine via
  `isinstance(module, FateRulesetModule)` — WN paths untouched.
- **One resolution primitive** for *all* Fate rolls (conflict and out-of-combat):
  `resolve_action(skill_rating: int, opposition: Opposition, invokes: list[Invoke]) ->
  Outcome{shifts: int, tier: Fail|Tie|Succeed|SucceedWithStyle, dice: [int,int,int,int]}`.
  4dF (each ∈ {−1,0,+1}) summed + `skill_rating`, minus opposition value; tier by shifts.
  `Opposition` is `Active(roll)` or `Passive(difficulty)`.

### 4.2 The conflict (replaces native combat)

`fate_conflict.py` owns the exchange loop. Reuses the existing encounter/MP substrate:
- **Establish:** sides, **zones** (reuse/extend the encounter's spatial notion), turn order
  by **Notice** (physical) / **Empathy** (mental).
- **Exchange:** each seated participant takes one action ∈ {overcome, create-advantage,
  attack, defend}; full-defense option (+2 to all defends, no proactive action). Opposition
  active (opposed roll) or passive (set difficulty).
- **Attack resolution:** shifts → target absorbs via **stress** boxes or **consequences**;
  no absorption ⇒ **taken out**. **Concede** (player-initiated, pre-roll) → fate points +
  narrative control, avoids worst outcome.
- **Aspects in play:** create-advantage places **situation aspects** with free invocations;
  boosts; consequences become aspects with a free invoke for the attacker.
- **MP:** ADR-036 sealed submit-and-wait barrier (same substrate as `wn_round`); peer action
  text stays visible (not hidden submission).

### 4.3 Character facet + economy

A Fate facet, added alongside the d20 model (not shoehorned into stats/`HpPool`):

```
FateSheet:
  aspects: [Aspect]            # high concept, trouble, + others; each free-text
  skills: {name -> ladder_int} # per-genre list authored as content
  stunts: [Stunt]
  refresh: int                 # per-session fate-point reset value
  fate_points: int             # current
  stress: {physical: [Box], mental: [Box]}     # box shift-values
  consequences: {mild, moderate, severe, extreme}  # slots; each becomes an Aspect when filled
```

- **Fate-point economy:** refresh (session reset), spend (invoke +2/reroll, declare detail,
  power stunt), earn (accept compel, concede). Every delta → OTEL span. This is the
  player-facing math.
- **Aspect store:** character / situation / boost / consequence aspects with free-invocation
  counts; created and discovered in play (create-advantage), removed on recovery/scene-end.
- **Advancement:** milestones (minor/significant/major); `awards_native_turn_xp = False`.

### 4.4 Seam re-cut (the one structural change to existing code)

Once native is gone, only the WN family needs the d20 surface. Demote the beat-centric
abstracts on `RulesetModule` from `@abstractmethod` to concrete default-raise:
`compute_dc`, `apply_beat`, `attack_params`, beat-sense `find_confrontation`,
ability-score `stat_modifier`. WN keeps overriding them; Fate implements the Fate surface
and never stubs a method it doesn't use (**No Stubbing**). Add the Fate-shaped surface the
module *does* own (the resolution primitive entry points, conflict hooks). This re-cut lands
in **F5** (after native removal), not F1 — F1 can subclass the current ABC and override the
d20 abstracts with default-raise locally until the base is re-cut.

### 4.5 Dice, narrator, magic

- **4dF:** fudge-die mode on the dice protocol (ADR-074) + the 3D overlay (ADR-075) — four
  dice, faces {−,0,+}. (F3.)
- **Narrator (F2):** Intent Router (ADR-113) classifies freeform action → {one of four
  actions, skill}; narrator surfaces invokable aspects, proposes compels, writes
  create-advantage results as situation aspects, renders outcomes. Aspects are passed as
  prompt fragments.
- **Magic:** Fate Fractal Extras / stunts as content; **no `MagicPlugin` on the Fate path.**

## 5. Decomposition (epics)

| Epic | Title | Depends on | Notes |
|------|-------|-----------|-------|
| **F1** | Fate engine core | — | Module, conflict engine, resolution primitive, character facet, fate-point economy, aspect store, 4dF roll, OTEL. The deep build. |
| **F2** | Narrator / intent-router integration | F1 | Action→{four-action, skill} classify; aspects-as-prompt; compels; invokes; create-advantage → situation aspects; honesty/OTEL lie-detector. |
| **F3** | UI surfaces | F1 (data), F2 (interactions) | Fate points, aspects panel (invoke), stress boxes, consequence slots, the ladder, 4dF dice overlay. Player-facing math (Sebastien/Jade). |
| **F4** | Content migration (4 packs) | F1 | Per-genre skill lists, aspects, stunts; strip native config; bind `ruleset: fate`. pulp_noir, tea_and_murder, wry_whimsy, spaghetti_western. |
| **F5** | Native removal | F4 (+ chase/negotiation re-home) | Delete `native.py`, `beat_kinds` combat, dial/edge/reprisal, native XP tick; re-cut seam abstracts; drop native from registry. **Strictly last.** |

F1→F2→F3 may overlap once F1's data contracts are stable. F4 needs F1. F5 is gated.

## 6. OTEL span inventory (the lie detector)

Per the OTEL Observability Principle, F1 emits at minimum:
`fate.action.classified` (action + skill) · `fate.opposition` (active/passive + value) ·
`fate.roll` (4dF dice + ladder rating + result) · `fate.outcome` (shifts + tier) ·
`fate.stress.applied` · `fate.consequence.taken` (level + aspect text) ·
`fate.aspect.invoked` (aspect + fate-point debit + free/paid) · `fate.compel.offered` /
`fate.compel.accepted` · `fate.fate_point.delta` (reason) · `fate.taken_out` /
`fate.conceded`. The GM panel must be able to confirm a Fate decision actually fired.

## 7. Test strategy (highlights)

- **Resolution primitive:** table-driven over the four outcome tiers; 4dF distribution
  sanity; invoke (+2 / reroll) application; active vs passive opposition.
- **Conflict engine:** an exchange resolves attack → stress → consequence → taken-out;
  concede path; create-advantage places a situation aspect with a free invoke; full-defense
  +2. Property: total absorbed ≤ available stress+consequence capacity, else taken-out.
- **Wiring tests (mandatory, per server CLAUDE.md):** OTEL-span assertion that a Fate action
  driven through the *real* dispatch emits `fate.roll`/`fate.outcome` (not a source grep);
  registry test that `get_ruleset_module("fate")` resolves; a pack bound `ruleset: fate`
  routes combat to `fate_conflict`, **not** `wn_round` or native beats.
- **Subprocess registry test** for `fate` registration via the production import path
  (in-process autouse conftest masks it — see project memory).

## 8. Open questions (for spec review / epic planning)

1. **WN chase/negotiation re-home (gates F5).** ADR-143 preserved the native dial-pacing
   device for WN packs' chase/negotiation. Deleting `native` removes it. Resolve as a
   genre-neutral pacing subsystem decoupled from the ruleset module, or as WN
   skill-challenges. **Does not block F1–F4.** Likely an ADR-143 amendment.
2. **Precious native saves?** Confirm none of the four packs has a save worth migrating
   before F5 (forward-only otherwise). Reference saves are WWN — unaffected.
3. **Zones:** reuse the existing encounter spatial model as Fate zones, or author zones as
   content per scene? (Lean: reuse; author zone aspects as content.)
4. **Skill list size per genre:** full 18-skill Core lists, or trimmed ~10-skill genre lists?
   (Lean: trimmed, genre-distinct — F4 content decision.)

## 9. Non-goals (YAGNI)

- FAE approaches as a separate engine mode (expressible later as a 6-row skill list, no
  engine change).
- A `MagicPlugin` for Fate (Extras/stunts as content instead).
- Migrating the WN family to Fate (explicitly rejected — ADR-144 Alternatives).
- Rebalancing any WN or native number (we are *removing*, not tuning).
