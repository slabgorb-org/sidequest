# Interactive Fate Core Chargen — Player-Authored Sheets on the Existing Builder FSM

- **Date:** 2026-06-16
- **Status:** Design — approved (Keith, 2026-06-16)
- **Story:** 121-6 (F4a-design) → gates 121-7 (F4a2, server engine + validator) and 121-8 (F4a3, UI)
- **Implements:** ADR-144 §Amendment 2026-06-15 (interactive Fate chargen pulled into F4)
- **Builds on:** F4a (story 121-1, done) — `FateConfig`, `FateSheet`, `FateRulesetModule.seed_chargen_resources`
- **Couples with:** the Fate Gear Model spec (`2026-06-15-fate-gear-model-design.md`, stories 114-9/114-10) — shared `base_refresh`/`free_stunts` and the refresh invariant
- **Repos:** `sidequest-server` (schema + builder + validator + OTEL + wire contract), `sidequest-ui` (three new input_type renderers), `sidequest-content` (archetype Fate templates, authored under 121-3/4/5)
- **Author:** The Man in Black (Architect)

---

## Summary (the decision)

Interactive Fate chargen is **not** a new mode and **not** a parallel pipeline. It is the
**existing ADR-015 builder FSM walking Fate-authored scenes**, mapped onto the **ADR-016
three modes** by *reusing* the F4a default-seed as the Menu path. The builder is already
ruleset-agnostic and scene-driven (it does not hard-require d20 stats/classes); a Fate pack
authors **zero** stat-generation scenes and **zero** classes, so no d20 machinery fires.
The fork is **data-driven by which scenes a pack authors**, not an `if ruleset == 'fate'`
branch inside the builder loop.

The four settled design choices (Keith, 2026-06-16):

| # | Fork | Decision |
|---|------|----------|
| **S** | Skill allocation | **Pyramid** — canonical Fate Core, shape pack-configurable; legality is a column-count check |
| **A** | Aspect authoring | **High Concept + Trouble + N free** (N pack-configurable, default 3); seeded from archetype, editable |
| **T** | Archetype role | **Hybrid seed-then-edit** — archetype seeds skills/stunts/suggested aspects; player edits all, must confirm HC+Trouble |
| **R** | Refresh/stunt economy | **Standard Fate, pack-tunable** — default 3 refresh / 3 free stunts; each extra stunt debits 1 refresh (floor 1) |

Three architecture calls the code reality dictated (reuse-first), confirmed with the
operator:

- **Mode integration (§2):** same FSM + Fate scenes; Menu/Guided/Freeform stay meaningful in Fate-space.
- **UI (§7):** extend the generic `input_type`-driven `CharacterCreation.tsx`; do not build a parallel screen.
- **race/class gap (§6):** Fate chargen never collects d20 race/class; the High Concept is the identity; those fields go benign/empty, never `"Human"`/`"Fighter"`.

The deliverable of 121-6 is **this spec + an ADR-144 amendment. No code.**

---

## Context — what F4a already shipped (don't rebuild it)

Story 121-1 (F4a, done) built the foundation this design layers onto. Verified in code:

- **`FateSheet`** (`sidequest-server/sidequest/game/fate_sheet.py`) — `aspects`, `skills`,
  `stunts`, `refresh`, `fate_points`, `stress`, `consequences`. Lives on
  `CreatureCore.fate_sheet`. Complete; the chargen flow's job is to *populate it from
  explicit player choices*.
- **`FateConfig`** (`sidequest-server/sidequest/genre/models/rules.py`) — `skills:
  dict[str,int]`, `refresh: int = 3`, `default_high_concept`, `default_trouble`, `stunts:
  list[FateStuntDef]`. `RulesConfig.fate` is the binding; `ruleset == "fate"` with no `fate`
  block is a hard validation error.
- **`FateRulesetModule.seed_chargen_resources(rules, stats, class_def)`**
  (`sidequest-server/sidequest/game/ruleset/fate.py`) — builds a **valid default**
  `FateSheet` from `FateConfig` (skills copied, HC+Trouble seeded, refresh set). **Ignores
  `stats`/`class_def`** by design (the de-d20 invariant). This is the Menu path, unchanged.
- **The builder** (`sidequest-server/sidequest/game/builder.py`) — ruleset-agnostic,
  scene-driven. `ability_score_names` may be empty; no classes ⇒ no qualification filtering;
  d20 stat-generation only fires when a scene *declares* it. The only ruleset touch in
  `build()` is `self._ruleset.seed_chargen_resources(...)` (~line 2866).
- **`CharacterCreation.tsx`** (`sidequest-ui`) — renders by `scene.input_type`, **not** by
  ruleset. New Fate input_types render by extension; no parallel screen needed.
- **pulp_noir** — bound `ruleset: fate` (story 121-2, done); the F4a2 validation target.

What is **not** built and this design specifies: the interactive flow that produces *explicit*
choices (archetype → aspects → pyramid → stunts), the **legality validator**, the
server→UI **wire contract**, and the three UI renderers.

---

## §2 — Mode integration (the spine)

The builder stays one FSM. The three ADR-016 modes map onto Fate so that the F4a default-seed
*is* the Menu path:

| ADR-016 mode | Fate behavior | Path | LLM |
|--------------|---------------|------|-----|
| **Menu** | Pick archetype → instant **legal default sheet** | `seed_chargen_resources` (F4a, unchanged) | 0 |
| **Guided** | Walk Fate scenes: archetype → edit HC+Trouble → author N free aspects → allocate pyramid → pick stunts | the new F4a2 interactive path (`apply_fate_chargen`) | 0 |
| **Freeform** | Player writes prose → LLM extracts a candidate sheet → **server validates to a legal sheet** | F4a2 + existing freeform parser | 1 |

**Guided is the heart of F4a2.** Menu reuses F4a verbatim. Freeform reuses the existing
freeform parser to produce a *candidate* `FateSheet`, then runs the **same legality
validator** Guided uses; an illegal candidate is corrected or re-prompted — **never silently
accepted** (No Silent Fallbacks). The default-seed path is *not* a silent fallback: it is the
explicitly-selected Menu mode.

**No d20 in the Fate path.** A Fate pack authors no stat-generation scenes, no `classes.yaml`,
no `ability_score_names`. The existing scene machinery (`requires_stock`,
`mechanical_effects`) is the precedent; Fate adds new scene `input_type`s rather than a
ruleset branch in the loop. The builder gains **Fate accumulators** (chosen archetype,
authored aspects, pyramid allocation, chosen stunts) the way it already accumulates hints;
`build()` passes them to the apply step.

### Data flow

```
CONTENT (authoring)                BUILDER FSM (per scene)              ENGINE (build)
───────────────────                ──────────────────────              ──────────────
archetypes.yaml                    Menu:   choice → archetype id  ─┐
  - name, ocean, ...               Guided: fate_aspects   → aspects │
  - fate:                                  fate_skill_pyramid       │  FateRulesetModule
      high_concept                          → skill allocation       │  Menu →
      trouble                              fate_stunts → stunt picks  ├─ seed_chargen_resources
      aspects: [..]                Freeform: prose → LLM → candidate │  Guided/Freeform →
      skills: {legal pyramid}              sheet                      │  apply_fate_chargen(choices)
      stunts: [names]                                                 ▼        │ validate
      gear: [ids]  (gear spec)     accumulators: {archetype,          FateSheet  │ legal?
                                    aspects, pyramid, stunts}          on Core    ▼ fail loud
rules.yaml: fate: {skills,                                                       OTEL spans
  refresh, free_stunts,                                                          fate.chargen.*
  chargen_pyramid, ...}
```

---

## §3 — Skill pyramid (decision **S**)

Canonical Fate Core pyramid, **shape pack-configurable** (Crunch in the Genre). New
`FateConfig` fields:

```python
# additive to the shipped FateConfig (genre/models/rules.py), extra="forbid"
chargen_pyramid: list[int] = Field(default_factory=lambda: [1, 2, 3, 4])
# counts per rung, apex first → 1 Great / 2 Good / 3 Fair / 4 Average (SRD default)
chargen_apex_rating: int = 4          # ladder value of the top rung (Great=4); rungs descend by 1
```

- Rung *i* (0 = apex) has ladder rating `chargen_apex_rating − i` and holds
  `chargen_pyramid[i]` skills. Default `[1,2,3,4]` @ apex 4 → ratings 4,3,2,1 (Great…Average).
  Skills not placed are **Mediocre (+0)** — the `FateSheet.skills` default.
- The **available skill list** is `FateConfig.skills.keys()` — the full genre skill list,
  already shipped. The pyramid places a *subset*; `FateConfig.skills` *values* remain the
  Menu-mode default ratings. **No new skill-list field.**
- **Config validity** (content validator, §9): `chargen_pyramid` must itself be a legal
  pyramid — apex-narrowest, `chargen_pyramid[i] ≤ chargen_pyramid[i+1]` (never wider at the
  top).
- **Allocation legality** (server authority, runtime): a player's allocation must (1) match
  the `chargen_pyramid` rung counts exactly (standard chargen fills the pyramid — chosen for
  determinism); (2) place only skills in `FateConfig.skills`; (3) place no skill twice.
  Violations are named, not silently corrected.

---

## §4 — Aspects (decision **A**)

```python
free_aspect_count: int = 3            # free aspects beyond HC + Trouble (→ 5 total, SRD count)
```

- Mandatory **High Concept + Trouble**, both non-empty. Plus exactly `free_aspect_count` free
  aspects, each non-empty.
- All are **seeded from the chosen archetype as editable suggestions**; the player accepts or
  rewrites. The HC and Trouble must be *confirmed* (the hybrid-template rule, §5) — a player
  may keep the seeded text but must pass through the confirm.
- Kinds: HC → `high_concept`, Trouble → `trouble`, the rest → `character`. Situation aspects,
  boosts, and consequence-aspects are **runtime** (F2/F1), not chargen.
- Remaining aspects emerge in play via create-an-advantage (F2) and the gear model (found items).

---

## §5 — Archetype as editable template (decision **T**) + schema

**Reuse the existing `archetypes.yaml`** (reuse-first) with an *additive, optional* `fate:`
block per entry. NPC generation ignores `fate:`; chargen ignores the NPC-only fields. One file
serves both PC chargen templates and NPC generation.

```yaml
# sidequest-content/genre_packs/<g>/archetypes.yaml — one entry
- name: The Fixer
  description: >- ...
  personality_traits: [resourceful, transactional]   # cross-ruleset, kept
  dialogue_quirks: [...]                              # cross-ruleset, kept
  ocean: {openness: 4.5, ...}                         # NPC-only; chargen ignores
  disposition_default: 10                             # NPC-only; chargen ignores
  fate:                                               # chargen template; fate packs only
    high_concept: "Well-Connected Fixer Who Knows Everybody"
    trouble: "Everyone Wants a Favor"
    aspects: ["A Card With No Name On It", "Owes the Wrong People", "Never Carries a Gun"]
    skills: {Contacts: 4, Rapport: 3, Deceive: 3, Notice: 2, Resources: 2, Will: 2,
             Investigate: 1, Empathy: 1, Stealth: 1, Physique: 1}   # legal default pyramid
    stunts: ["The Right Word in the Right Ear"]       # signature stunts, names from catalog
    gear: [fixer_kit]                                 # (gear-model spec) gear ids → compiled grants
    refresh: 3                                        # optional per-archetype override of base_refresh
```

- **Drop for Fate packs:** `stat_ranges`, `typical_classes`, `typical_races` (d20-only).
- **Flow:** pick archetype → seeds skills (a legal pyramid), stunts, and suggested aspects →
  player edits anything → **must confirm/author HC+Trouble**. The same `fate:` block seeds
  Menu mode (instant) and pre-fills Guided mode (editable).
- The archetype's `fate.skills` MUST itself be a legal pyramid under the pack's
  `chargen_pyramid` (checked by the content validator, §9), so Menu-mode output is legal by
  construction.

**Open sub-decision (recommend reuse, flagged for veto):** reuse `archetypes.yaml` vs a
dedicated chargen-template list. Recommendation is reuse-with-additive-`fate:`-block; PC and
NPC archetypes in these four genres read as the same concepts ("The Fixer", "The War
Veteran"). If a future pack needs PC-only concepts, a separate list is addable with no rework.

---

## §6 — Refresh/stunt economy (decision **R**) + race/class resolution

```python
free_stunts: int = 3                  # stunts free before refresh is debited (SHARED with gear spec)
# base refresh = the shipped FateConfig.refresh (alias of the gear spec's `base_refresh`)
```

- **Invariant (identical to the gear-model spec, one source of truth):**
  `refresh == base_refresh − max(0, total_stunts − free_stunts)`, floored at 1; `fate_points`
  start `== refresh`.
- `total_stunts` counts **archetype `fate.stunts` + gear-granted stunts (gear spec) +
  player-added stunts at chargen**. The interactive stunt picker (§7) shows the live refresh
  readout as the player adds/removes.
- Stunts at chargen are chosen from the pack catalog (`FateConfig.stunts`). Custom-stunt
  authoring is YAGNI-deferred to play/milestones.
- **Base refresh** reuses the existing `FateConfig.refresh` field; the gear-model spec names
  the same concept `base_refresh`. Whichever story lands first owns the (optional) rename; this
  spec treats them as the same field and does **not** define a second one.

### race/class resolution (the §1 gap)

`Character.race`/`char_class` are required fields with `"Human"`/`"Fighter"` fallbacks — wrong
for a Fate PC. Resolution: **Fate chargen never collects d20 race/class.** The High Concept
*is* the identity. For a Fate-built `Character`:

- `char_class` and `race` are set from Fate-appropriate, non-fantasy sources — preferably left
  empty/`None` if the field validators allow optionality, else set to the High Concept text (a
  display-only label), **never** the `"Human"`/`"Fighter"` defaults.
- F4a2 makes the minimal field-validator change needed so a Fate `Character` carries no phantom
  class/race. (If optionality is too invasive, the documented fallback is HC-as-label; the
  decision is "no d20 default surfaces on a Fate sheet.")
- `stats` stays `{}` for Fate (already supported).

---

## §7 — UI (extend, not parallel) + wire contract

Extend `CharacterCreation.tsx` (already `input_type`-driven). Archetype pick reuses the
existing `choice` renderer. Three **new `input_type`s**, each a new renderer:

| input_type | renders | client→server |
|------------|---------|---------------|
| `fate_aspects` | HC + Trouble + N free text inputs, **pre-filled** from archetype, editable | the edited aspect texts |
| `fate_skill_pyramid` | pyramid allocation widget with **live legality feedback** (rung labels, remaining slots) | `{skill: rating}` allocation |
| `fate_stunts` | stunt picker (from catalog) with **refresh readout** | selected stunt names |

**Server is the validation authority; the client mirrors and previews, never adjudicates**
(No Silent Fallbacks — ADR consistent). Live legality in the UI is a *convenience mirror* of
the server validator; the server re-validates every submission and on `build()`.

**Wire contract (server→UI `CreationScene` extension, additive):**

```
fate_aspects:        aspect_slots: [{kind, label, value, required, suggestion}]
fate_skill_pyramid:  available_skills: [name],
                     pyramid: [counts], apex_rating: int,
                     current_allocation: {skill: rating},
                     ladder_labels: {rating: name},   # Great/Good/Fair/Average
                     legal: bool, violations: [str]
fate_stunts:         available_stunts: [{name, description}],
                     selected: [name],
                     free_stunts: int, base_refresh: int, current_refresh: int,
                     legal: bool, violations: [str]
```

**Structural ruleset gate (the §1 confirmation):** a Fate pack only ever emits `fate_*`
input_types; a d20/WN pack only ever emits `roll_the_bones`/`stat_arrange`/etc. The gate is
satisfied by which scenes the pack authors — no `ruleset=='fate'` check in the renderer.
**Paired negative test (mandatory, §8):** a Fate pack never emits a d20 stat input_type, and a
d20/WN pack never emits a `fate_*` input_type, so the surfaces never co-render.

---

## §8 — OTEL (the lie detector) + wiring tests

### Spans (register in `SPAN_ROUTES`)

`fate.chargen.seeded` already exists (Menu/F4a). Net-new for the interactive path:

- `fate.chargen.archetype_selected` — `{archetype}`
- `fate.chargen.aspects_authored` — `{high_concept_present, trouble_present, free_count}`
- `fate.chargen.pyramid_allocated` — `{rung_counts, skills_placed, legal}`
- `fate.chargen.stunts_selected` — `{count, refresh_before, refresh_after}`
- `fate.chargen.validated` — `{legal, violations}`
- `fate.chargen.completed` — `{aspect_count, skill_count, stunt_count, refresh}`

### Wiring tests (behavior/OTEL, **never** a source-grep)

1. **Real-pack legal build:** pulp_noir through the **production** builder in Guided mode
   produces a legal `FateSheet` — valid pyramid matching `chargen_pyramid`, refresh invariant
   holds, HC+Trouble present — asserted via the built character + `fate.chargen.completed`
   span (InMemorySpanExporter + injected `_tracer`, mirroring F4a's AC5).
2. **Validator rejects illegal (mutation):** widen the apex (e.g. 2 skills at Great) → the
   validator returns a non-empty `violations`; the build fails loud. De-tautologized by pinning
   a concrete legal pyramid value.
3. **Module routing:** `get_ruleset_module("fate")` resolves to `FateRulesetModule`; a Fate
   pack routes combat to `fate_conflict`, not native/`wn_round` (paired negative: a WN pack
   resolves to its module and gets `fate_sheet is None`).
4. **Paired negative input_type:** a Fate-pack chargen run emits no `roll_the_bones`/
   `stat_arrange`; a WN-pack run emits no `fate_*` (the §7 structural gate).
5. **Menu == legal default:** Menu mode (the F4a seed) still yields a legal sheet under the
   same validator (regression guard that F4a and F4a2 agree on legality).

---

## §9 — Legality validator (server, the authority)

A **pure function** reused by the engine, the wire contract, and the content validator:

```python
def validate_fate_sheet(sheet: FateSheet, cfg: FateConfig) -> list[str]:
    """Return a list of human-readable violations; empty == legal. Pure; no I/O."""
```

Checks: pyramid shape vs `chargen_pyramid`/`chargen_apex_rating`; skills ∈ `cfg.skills`; no
duplicate skill; HC + Trouble present and non-empty; free-aspect count == `free_aspect_count`;
stunts ∈ catalog; refresh invariant `refresh == base − max(0, total_stunts − free_stunts)`
floored at 1.

- **Engine:** `apply_fate_chargen(choices)` builds the sheet then asserts
  `validate_fate_sheet == []` before attaching (fail loud).
- **Content validator (`sidequest-validate`):** `chargen_pyramid` is itself a valid pyramid
  (apex-narrowest); every archetype's `fate.skills` is a legal allocation under it and its
  `refresh` satisfies the invariant — so Menu-mode output is legal by construction (the same
  posture the gear-model spec took for the refresh invariant).
- **UI:** mirrors the same rules for live feedback; the server re-runs the function as the
  authority.

---

## Cross-spec coupling — the Fate Gear Model (114-9/114-10)

This design and the gear model both touch `FateConfig`, archetypes, and chargen. They
**compose**; neither double-defines:

- **Shared fields:** `free_stunts` and base refresh (`FateConfig.refresh` ≡ the gear spec's
  `base_refresh`). Whichever story lands first adds `free_stunts`; the other reuses it.
- **Shared invariant:** the refresh formula is identical and lives in **one** validator
  (`validate_fate_sheet` + the content validator). `total_stunts` includes gear-granted stunts.
- **Archetype `fate.gear: [ids]`** is the gear spec's field; this spec's chargen flow compiles
  it (gear → aspects/stunts with `source_gear`) as part of `apply_fate_chargen`, then validates
  the combined sheet. If the gear story has not landed, `gear` is simply absent and chargen
  proceeds on `fate.stunts` alone.
- **`AspectKind += "permission"`** and `source_gear` are the gear spec's engine deltas, not
  this spec's; chargen tolerates them when present.

---

## Invariants / Contracts

- **One FSM, no ruleset branch in the loop.** Fate chargen is the existing builder walking
  Fate-authored scenes; the fork is which scenes/`input_type`s the pack authors.
- **Server is the validation authority.** `validate_fate_sheet` is the single legality
  source; the UI mirrors, never adjudicates; `build()` re-validates and fails loud.
- **No d20 on the Fate path.** No stat generation, no classes, no `ability_score_names`; no
  phantom `"Human"`/`"Fighter"` on a Fate `Character`.
- **Pyramid is legal by construction at Menu.** Archetype `fate.skills` is validated as a legal
  pyramid by the content validator, so the default seed is always legal.
- **Refresh invariant is one formula** shared with the gear model; no free stunts ever.
- **Surfaces never co-render.** The paired negative input_type test enforces that Fate and
  d20/WN chargen never emit each other's input_types.
- **No silent fallback.** Menu's default seed is an *explicit* mode; Freeform's illegal
  candidate is corrected/re-prompted, not accepted.

## Decomposition this spec gates

- **121-7 (F4a2, server):** `FateConfig` chargen fields (`chargen_pyramid`,
  `chargen_apex_rating`, `free_aspect_count`, `free_stunts`); archetype `fate:` schema;
  builder Fate accumulators + `apply_fate_chargen`; `validate_fate_sheet`; race/class
  resolution; OTEL spans; server→UI wire contract; wiring tests 1–5. Validates against
  pulp_noir.
- **121-8 (F4a3, UI):** the three input_type renderers (aspect editor, pyramid widget with
  live legality, stunt picker with refresh readout); the structural ruleset gate + paired
  negative test; consumes the F4a2 wire contract; server stays the authority.
- **121-3/4/5 (content):** tea_and_murder, wry_whimsy, spaghetti_western author their
  archetype `fate:` blocks (HC/Trouble/aspects/skills/stunts) as part of their migrations.
  pulp_noir's `fate:` archetype blocks are authored under 121-7 as the pilot.

## Out of scope (explicitly)

- The Fate **conflict/combat** engine and narrator integration (ADR-144 F1/F2) — unchanged.
- **Gear** authoring/compile internals (the Fate Gear Model spec, 114-9/114-10) — this spec
  only composes with it.
- **Custom-stunt authoring** at chargen, **à-la-carte gear selection**, **FAE approaches**,
  the **full phase-trio** aspect method — all expressible later, none built now (YAGNI).
- **`native` removal** (ADR-144 F5).

## Open questions

1. **Archetype source (§5):** reuse `archetypes.yaml` with a `fate:` block (recommended) vs a
   dedicated chargen-template list. Recommendation stands unless the operator prefers
   separation.
2. **race/class optionality (§6):** make `Character.race`/`char_class` truly optional vs
   HC-as-display-label fallback. F4a2 picks the least-invasive change that keeps no d20 default
   on a Fate sheet.
