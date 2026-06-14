---
id: 144
title: "Fate Core Binding Replaces the Native Ruleset — Two SRDs, Zero Homebrew Rulesets to Balance"
status: accepted
date: 2026-06-14
deciders: ["Keith Avery", "Neo (Architect)"]
supersedes: []
superseded-by: null
related: [2, 33, 113, 114, 116, 117, 126, 139, 142, 143]
tags: [game-systems]
implementation-status: deferred
implementation-pointer: "docs/superpowers/specs/2026-06-14-fate-core-binding-replaces-native-design.md"
---

# ADR-144: Fate Core Binding Replaces the Native Ruleset — Two SRDs, Zero Homebrew Rulesets to Balance

> **This completes what ADR-143 began.** ADR-143 removed the native combat engine from
> the Without Number path; this ADR removes the native ruleset *entirely* by binding a
> second published SRD — **Fate Core** (Evil Hat, CC-BY) — for the narrative-first genres
> native was the default for. After this, SideQuest hosts **two pre-balanced SRDs and zero
> homebrew rulesets**. Operator directive, verbatim (Keith, 2026-06-14, emphatic):
> *"No native. AGAIN, we can't make an AI GM, and a content engine, AND THEN try to
> balance a ruleset — something has to give, and SRDs are for this."*

## Context

SideQuest is simultaneously building two genuinely hard things: an **AI Game Master**
(the narrator that must fool a 40-year career GM) and a **content engine** (so anyone —
Keith, Jade, a future table member — can add worlds and packs without touching engine
code). Maintaining a *third* hard thing — a homebrew combat ruleset we balance ourselves
— is the load that has repeatedly broken the project. ADR-143 records the WN half of this
lesson; this ADR records the rest.

The doctrine is **Bind the Ruleset, Don't Balance It** (SOUL.md, ADR-143): when a genre
binds a published ruleset, the *reason* is to inherit already-balanced math so we never
balance combat ourselves. ADR-117 made resolution pluggable per genre behind the
`RulesetModule` seam (`rules.yaml` → `ruleset:`), resolved through a fail-loud registry.

As of 2026-06-14 the **Without Number family has already absorbed 8 of 11 packs**:

| Module | Packs |
|--------|-------|
| `wwn` | caverns_and_claudes, elemental_harmony, heavy_metal |
| `swn` | space_opera |
| `cwn` | neon_dystopia, road_warrior |
| `awn` | mutant_wasteland |

Only **four packs still bind `native`** — and they are precisely the genres where a d20
ruleset is *tonally wrong* and where Fate is the canonical-best system:

- **pulp_noir** — Fate's direct ancestor, *Spirit of the Century*, is a pulp game.
- **tea_and_murder** — cozy mystery; almost pure create-advantage / overcome, combat rare.
- **wry_whimsy** — comedy runs on aspects and compels.
- **spaghetti_western** — the Leone standoff is a dramatic Contest/Conflict of nerve and
  reputation, not HP attrition. Fate Core ships western support out of the box (an undead
  Wild-West gunslinger is one of its three sample characters), so binding it is *adopting
  an SRD*, not inventing a fit. No WN family module fits a western cleanly.

The native engine (ADR-033, the `native` module) resolves action as **beats**
(`strike`/`brace`/`push`/`angle`) advancing a **dial** toward a threshold, granting
**fleeting tags** via `edge_config`, with a **per-beat auto-reprisal**. Its numbers are
*ours* — every encounter's tension dial, every edge magnitude, every threshold is a value
we chose and must balance by hand. That is the homebrew-ruleset burden the directive
forbids.

## Decision

**The `native` ruleset is removed. The four narrative-first packs bind Fate Core (`fate`),
a second published SRD. SideQuest's end state is two pre-balanced SRDs — Fate Core and the
Without Number family — and no homebrew ruleset. We never balance combat math again; we
pour content into published systems.**

Genre → ruleset assignment is settled doctrine (Keith, 2026-06-14):

- **Fate Core** — detective & social genres: **pulp_noir, tea_and_murder, wry_whimsy,
  spaghetti_western**.
- **Without Number** — classic/action genres (dungeons, spaceships, cyberpunk, mutants):
  the 8 packs above, unchanged.
- **native** — deleted. Not kept "for the light packs," not balanced, gone.

### What Fate is, mechanically (the SRD we inherit)

Fate Core supplies a complete, CC-BY-licensed, playtested resolution system:

- **Resolution:** 4dF (four Fudge dice, each −/0/+) + a **skill** rating on the **ladder**
  (Terrible −2 … Legendary +8), versus **opposition** (active = an opposed roll; passive =
  a set difficulty). **Shifts** = result − opposition. **Four outcomes:** fail (< 0), tie
  (= 0, minor cost / boost), succeed (1–2 shifts), **succeed with style** (3+ shifts).
- **Four actions:** **overcome**, **create an advantage** (place/discover a situation
  aspect with free invocations), **attack**, **defend**. Every roll is one of these four.
- **Aspects + fate points:** aspects are free-text truths (character: high concept,
  trouble, others; situation; boosts; consequences-as-aspects). **Invoke** (spend 1 fate
  point or a free invoke) for +2 or a reroll; **compel** an aspect to introduce a
  complication for a fate point. This is **Fortune-in-the-Middle** — the SOUL purpose
  statement, made native: roll first, then bend the result.
- **Conflict (replaces native combat):** establish sides and zones; turn order by Notice
  (physical) / Empathy (mental); per exchange each participant takes one action; a
  successful attack's shifts are absorbed by **stress** (physical/mental boxes) or
  **consequences** (mild 2 / moderate 4 / severe 6 / extreme 8, each a new aspect with a
  free invoke for the attacker); out of absorption ⇒ **taken out**; a player may
  **concede** before the roll for fate points and narrative control.
- **Advancement:** **milestones** (minor / significant / major) — rename an aspect, swap
  skills, add a stunt or refresh, raise skills. **Not XP.**

Fate is *more* divergent from the current substrate than WN is: WN is d20-with-a-
different-round (ability scores, AC, HP, dice-vs-number); Fate has **no d20, no AC, no HP,
no ability scores** — 4dF, the ladder, skills, stress/consequences, and a fate-point/aspect
economy with no analog in the engine today.

### The seam and where the cut goes (mirrors `wn_round.py`)

ADR-143 set the precedent: a bound ruleset **owns its own round engine**, and dispatch
routes to it by module type (`isinstance`), leaving other modules' dispatch untouched.
Fate follows the identical pattern, one tier over:

- **`FateRulesetModule`** (`ruleset/fate.py`, slug `fate`) + **`fate_conflict.py`** (the
  exchange engine — sides, zones, turn order, the four actions, shifts → stress /
  consequences, taken-out / concede). Dispatch routes to it by
  `isinstance(module, FateRulesetModule)`; WN dispatch is untouched. It reuses the ADR-036
  sealed submit-and-wait barrier as its MP substrate, exactly as `wn_round` does.
- **One Fate resolution primitive** — `resolve_action(skill_rating, opposition, invokes)
  → Outcome{shifts, tier}` over 4dF — serves **both** conflict *and* out-of-combat
  overcome / create-advantage. Chase and negotiation become Fate **Contests**; no native
  dial is needed on the Fate path.
- **Seam re-cut.** The current `RulesetModule` abstract surface is native/WN-shaped by
  admission (`base.py`: *"Spec 0 surface only — the operations the native turn performs"*):
  `compute_dc(beat)`, `apply_beat`, `attack_params → AttackRollParams(d20-mod,
  target_number)`, ability-score `stat_modifier`, beat-sense `find_confrontation`. Fate has
  no beats, DCs, d20, or ability scores. Once native is gone, **only the WN family needs
  that d20 surface**, so those beat-centric methods are **demoted from abstract to
  default-raise** (the treatment `ship_attack_params` / `save_params` already receive). Each
  module then implements **only its own paradigm's surface** — Fate never stubs a
  `compute_dc` it does not use. This honors **No Stubbing**.

### Character shape

A Fate character is **not** ability-scores + `HpPool`. It is a Fate-shaped facet:
`aspects[]`, `skills{name → ladder}`, `stunts[]`, `refresh`, `fate_points`, stress tracks
(physical / mental boxes), consequence slots. It is added alongside — not shoehorned into
— the d20 stat model. The seam already proves character shape is ruleset-specific (the
`awards_native_turn_xp` gate); Fate returns `False` and advances by milestones.

### Capabilities are authored per genre (Crunch in the Genre)

The engine models a capability generically as `name → ladder rating`. The four launch
packs author **Fate Core per-genre skill lists** (noir: Investigate / Contacts / Deceive;
western: Shoot / Ride / Physique) — genre-distinct mechanical identity, honoring **Crunch
in the Genre, Flavor in the World**. FAE-style approaches remain expressible later as a
6-row skill list with no engine change, but are not built now (YAGNI).

### Magic

Fate handles magic as **Extras / stunts** via the Bronze Rule (the Fate Fractal), authored
as content. None of the four Fate genres is magic-heavy; any magic (whimsy, weird-west,
pulp-weird) is a stunt or Extra. **No `MagicPlugin` (ADR-126) on the Fate path** — a whole
subsystem stays off the critical path.

### OTEL (the lie detector must prove Fate fired)

Per the OTEL Observability Principle, every Fate subsystem decision emits a span: action
classification (which of the four actions + which skill), opposition (active/passive +
value), the 4dF roll + ladder rating, shifts and outcome tier, stress applied, consequence
taken, aspect invoked (with the fate-point debit), compel offered/accepted, every
fate-point delta, taken-out / concede. The fate-point economy *is* the player-facing math
surface (the GM panel is the lie detector; players read fate points spent).

### Scope and sequencing

This is multi-epic. The governing design and the full F1–F5 decomposition live in
`docs/superpowers/specs/2026-06-14-fate-core-binding-replaces-native-design.md`:

- **F1 — Fate engine core** (`FateRulesetModule`, `fate_conflict.py`, the resolution
  primitive, the character facet, the fate-point economy, the aspect store, 4dF, OTEL).
- **F2 — Narrator / intent-router integration** (action→{four-action, skill} classification,
  aspects-as-prompt-fragments, compels, invokes, create-advantage → situation aspects).
- **F3 — UI surfaces** (fate points, aspects panel with invoke, stress boxes, consequence
  slots, the ladder, 4dF dice overlay — ADR-074 / ADR-075 extension).
- **F4 — Content migration** of the four packs (per-genre skill lists, aspects, stunts;
  strip native config; bind `ruleset: fate`).
- **F5 — Native removal** (delete `native.py`, `beat_kinds` combat, dial/edge/reprisal
  machinery, native XP tick; re-cut the seam abstract surface; drop `native` from the
  registry). **Strictly last**, after F4.

## Consequences

**Positive**

- One homebrew ruleset is *deleted*, not maintained. Effort concentrates on the two hard
  problems — the AI GM and the content engine — never on balancing combat.
- The four narrative genres get their canonical-best system; Fate's Fortune-in-the-Middle
  *is* the SOUL purpose statement, finally native rather than approximated.
- Aspects are free-text → they are **prompt fragments**: a uniquely strong AI-narrator
  synergy no d20 system offers.
- Fate Core is CC-BY — rights-clean, consistent with the project's licensing posture.

**Negative / cost**

- Fate diverges from the substrate more than WN did: a new dice paradigm (4dF), a new
  character facet, and a fate-point/aspect economy are net-new engine surface (F1) —
  larger than ADR-143's cleanup, which mostly reused an existing round engine.
- The seam re-cut touches every module's relationship to the abstract surface; care is
  needed not to regress the WN family.
- **F5 dependency on ADR-143's carve-out:** ADR-143 preserved the native *dial-pacing*
  device (chase / negotiation) for WN packs as a genre-neutral pacing scene. Deleting
  `native` wholesale (F5) removes that too. Before F5 can complete, WN-pack chase /
  negotiation must be re-homed (a genre-neutral pacing subsystem decoupled from the
  `native` ruleset module, or expressed as WN skill-challenges). This intersects ADR-143
  and is the gating open item for F5 — tracked in the design spec's open questions; it does
  **not** block F1–F4. (Fate packs are unaffected: chase / negotiation are Fate Contests.)
- **Saves: forward-only.** New Fate-pack sessions use Fate; pre-cutover `native` saves for
  the four packs become read-only at cutover. Open item: confirm none are precious before
  F5. (The reference saves — e.g. James's "Rux" — are caverns_and_claudes = WWN, unaffected.)

## Alternatives considered

- **PbtA (Dungeon World SRD) instead of Fate.** Rejected. PbtA's 2d6 partial-success and
  GM-moves are an excellent single mechanic for an LLM MC, but PbtA is a *framework*, not
  one ruleset: binding it means authoring playbooks + moves **per genre**, which re-creates
  per-genre balancing — the exact ADR-143 trap. Fate is one genre-agnostic engine (genres
  supply skills/aspects/stunts as data), it is Fortune-in-the-Middle by identity (the SOUL
  purpose), and its aspects are free-text prompt fragments. Fate fills the `native` slot
  (one engine, many genres) with published math; PbtA does not.
- **Keep `native` for the light/narrative packs and "only balance it a little."** Rejected,
  emphatically (Keith, 2026-06-14). This is the homebrew-ruleset burden the directive
  forbids; "a little balancing" is still us owning combat math. SRDs exist precisely so we
  do not.
- **Force the four narrative packs onto a WN module.** Rejected. d20 / HP attrition is
  tonally wrong for cozy mystery, noir, comedy, and the operatic western; no WN family
  module fits a western; and it would make four distinct genres feel mechanically identical.
- **Fate everywhere (retire the WN family too).** Rejected. It would undo ADR-143 (one day
  old) and drop the SRD-grade crunch the mechanics-first players (Sebastien, Jade)
  specifically want. Two SRDs, each where it fits, is the decision.

## Amendments

_None yet._
