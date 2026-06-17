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
implementation-status: partial
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

### 2026-06-15 — Interactive Fate chargen pulled into F4 (was a non-goal)

The design spec (§9 Non-goals) and the F4 sketch above scoped F4 as *content
migration only* and deferred a player-driven Fate character-creation flow to "a later
epic," with F4 auto-seeding a valid default `FateSheet`. **Operator decision
(Keith, 2026-06-15): interactive Fate chargen is now in F4 scope.** A Fate-bound pack
must let the player author their own aspects, allocate the skill ladder (pyramid /
column method), and choose stunts at creation — not merely receive a seeded default.

Consequences for the F4 decomposition (epic 121):

- **F4a** stays the runnable gate — the pack-content schema (`FateConfig`) + the
  `FateSheet` seeding/apply layer (build + validate a sheet from *explicit* choices,
  against the existing `FateSheet` model) + builder wiring + OTEL + wiring test.
- **F4a-design** (new) — an Architect design spec settling the real forks before the
  chargen build is RED-ready: skill-allocation method (pyramid vs columns vs
  point-buy), aspect method (full phase-trio vs high-concept + trouble + N free), how a
  Fate chargen **mode** forks/coexists with the ADR-015 builder FSM and ADR-016
  three-mode chargen (a Fate pack must not hard-require d20 stats/classes), the
  archetype-as-editable-template role, and the UI approach.
- **F4a2** (new, server) — the interactive chargen engine + legality validator.
- **F4a3** (new, ui) — the Fate chargen screens, `ruleset == 'fate'`-gated.

F4b–F4e (per-pack content) are unchanged in intent; their "playable" acceptance now
implies the chargen flow exists. This does not change the F5 sequencing (native removal
still strictly last) or the two-SRD end state.

### 2026-06-16 — Interactive Fate chargen design settled (F4a-design / story 121-6)

The 2026-06-15 amendment opened the forks; story 121-6 settles them. Full design and
schema in `docs/superpowers/specs/2026-06-16-fate-interactive-chargen-design.md`. The
decisions (Keith, 2026-06-16):

- **No new mode, no parallel pipeline.** Interactive Fate chargen is the **existing
  ADR-015 builder FSM walking Fate-authored scenes**, mapped onto the ADR-016 three
  modes: **Menu** = the F4a default-seed (unchanged), **Guided** = the interactive
  authoring path (archetype → aspects → pyramid → stunts), **Freeform** = LLM-extract →
  **validate to a legal sheet** (corrected/re-prompted, never silently accepted). The
  fork is **data-driven by which scenes a pack authors** — no `if ruleset == 'fate'` in
  the builder loop. The builder is already ruleset-agnostic (no hard d20 stats/classes).
- **Skill allocation: pyramid**, shape pack-configurable (`chargen_pyramid` default
  `[1,2,3,4]`, `chargen_apex_rating` default 4). Legality is a column-count check; skills
  drawn from the genre list (`FateConfig.skills`).
- **Aspects: High Concept + Trouble + N free** (`free_aspect_count` default 3), seeded
  from the archetype and editable; HC+Trouble must be confirmed. The full phase-trio is a
  YAGNI-deferred non-goal.
- **Archetype = hybrid seed-then-edit**, authored as an additive **`fate:` block on the
  existing `archetypes.yaml`** (reuse, not a new file; NPC generation ignores it). It
  seeds skills/stunts/suggested aspects; the player edits all.
- **Refresh/stunt economy: standard Fate, pack-tunable** — default 3 refresh / 3 free
  stunts; `refresh == base_refresh − max(0, total_stunts − free_stunts)` (floor 1). This
  is the **same invariant and the same `free_stunts`/base-refresh fields** as the Fate
  Gear Model spec (114-9/114-10); the two specs compose, neither double-defines.
- **UI: extend** the generic `input_type`-driven `CharacterCreation` screen (three new
  input_types: `fate_aspects`, `fate_skill_pyramid`, `fate_stunts`) — **not** a parallel
  Fate screen. The `ruleset=='fate'` gate is **structural** (a Fate pack only emits
  `fate_*` input_types); enforced by a paired negative test. Server is the validation
  authority; the client mirrors, never adjudicates.
- **No d20 identity on a Fate sheet.** Fate chargen never collects race/class; the High
  Concept is the identity; `Character.race`/`char_class` go benign/empty, never
  `"Human"`/`"Fighter"`.

Gating: 121-6 (design) → **121-7** (F4a2, server engine + `validate_fate_sheet` validator +
wire contract) → **121-8** (F4a3, UI). The other three packs author their archetype `fate:`
blocks under 121-3/4/5. No change to F5 sequencing or the two-SRD end state.

### 2026-06-17 — Contests (the third Fate resolution mode)

#### The Contest mode

The Fate binding now includes **Contests** alongside Conflicts. A Contest is an opposed
4dF race: first participant to accumulate N victories wins; a tied exchange grants a
**boost** (a free invoke on the next exchange) to the leader. Fate-pack confrontations
resolve as **Contests or Conflicts, never `opposed_check`** — the native dial/beat
path is removed from the four Fate packs. The distinction is structural: a Contest has
**no stress and no consequences**. An `attack` action submitted during a Contest is
rejected loud (`ConflictActionInContestError`); the correct action is `overcome`.

#### Engine and selection plumbing

The Contest engine lives at `sidequest/server/dispatch/fate_contest.py::run_fate_contest_exchange`.
It is selected when an encounter carries `encounter.contest` — a `ContestState`
stamped at seating when the confrontation def declares `resolution_mode: contest`.
`dispatch_fate_action` branches Conflict-vs-Contest on that stamp, which reconciles
two things that might otherwise look inconsistent: resolution_mode selects between
Contest and Conflict, while the Conflict engine is gated by
`isinstance(ruleset, FateRulesetModule)` (not resolution_mode). The stamp bridges the
two — resolution_mode fires at seating time to populate `ContestState`; dispatch
reads the stamp to route. The Conflict engine is unchanged; Contest is additive.

OTEL spans: `fate.contest.seeded`, `fate.contest.exchange`, `fate.contest.resolved`.

#### Governing axis: substrate vs. resolution (Keith, 2026-06-17)

When binding an SRD, every "honor the native behavior?" call is settled by which
layer the behavior belongs to:

**Multiplayer / remote-substrate mechanics are PRESERVED; the SRD engine bends to
allow them.** They exist because SideQuest is remote, with no human GM at a physical
table. The Contest path therefore carries:

- **ADR-116 seating + fail-loud:** a confrontation requires an Other; no opponent
  available → `NoOpponentAvailableError`. This invariant holds on the Contest path
  exactly as it does on the Conflict path.
- **Per-turn presence stamping (story 72-12):** each Contest exchange stamps the
  seated NPC opponent's `last_seen_turn` / `last_seen_location` and emits
  `npc.edge_published(source="fate_contest")`, so the 72-6 last-seen prune never
  drops an NPC who is actively mid-contest.
- **Universal `encounter.resolved` span on a points-win:** fired alongside
  `fate.contest.resolved` (plus `pending_resolution_signal`), so the GM panel
  tears down the confrontation overlay, player input unlocks, the render trigger
  fires, and the forensic timeline records the close. The same signal drives
  post-confrontation advancement and scene transition regardless of which engine
  produced the win.

**Genre resolution mechanics belong to the SRD.** The native `opposed_check`
resolution — dial advance, threshold-7 / ADR-093 calibration, opponent-stat
ceilings, beat `stat_check`s — is **removed** from the four Fate packs. Fate
computes the outcome. We do not tune Fate's exchange math against native thresholds.

Preserving the substrate invariants on the Contest path is **consistent with "Bind
the Ruleset, Don't Balance It" (SOUL.md / ADR-143)**. The substrate mechanics are
SideQuest-side observability, world-state, and multi-seat coordination — not Fate
math. We wire the platform substrate through the new engine; we do not tune Fate
against native.

#### Implementation pointers

Design spec: `docs/superpowers/specs/2026-06-17-fate-contest-binding-design.md`.
Plan: `docs/superpowers/plans/2026-06-17-fate-contest-binding.md`.

The following are complete on `feat/fate-contest-binding` (server + content):
`native` → `dial` rename, fail-loud for three former silent fallbacks, `ContestState`
model, `fate.contest.*` OTEL spans, Contest engine (`run_fate_contest_exchange`),
seating + dispatch branching, spaghetti_western + tea_and_murder confrontation
conversion from `opposed_check` to `resolution_mode: contest`, Contest guardrail
(`attack`-in-Contest rejection), and regression fix.

**Deferred fast-follow:** `create_advantage` *during* a Contest (place a situation
aspect and forgo scoring that exchange). Deferred — aspect invokes already carry
over via the shared dispatch seal; this is an additive capability, not a blocker.
