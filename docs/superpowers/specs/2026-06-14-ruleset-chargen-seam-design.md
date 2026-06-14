# Design — Ruleset chargen seam: move chargen mechanics onto `RulesetModule`, make WWN chargen real

**Date:** 2026-06-14
**Author:** Architect (Atlas the Endurer), at Keith's direction
**Status:** Draft — pending user review
**Promote to:** ADR-143 once a plan exists (load-bearing: moves character-generation mechanics from `builder.py` onto the ruleset module surface — the chargen analogue of ADR-117/ADR-142's combat ownership).
**Context:** Deferred item #1 from the Without Number core extraction (`2026-06-13-without-number-core-extraction-design.md`, ADR-142, "As-built → Still deferred"). The combat/lethality/Effort chassis now lives on `WithoutNumberRulesetModule`; chargen does not. This spec gives chargen the same treatment **and** builds the Skills/Foci/Background substrate WWN needs, with real content, end-to-end.

---

## Why

ADR-142 made the rules **owned once by the ruleset** for combat, saves, Effort, and lethality. Chargen was left behind: attribute generation, point-buy, the standard array, and resource seeding still live in `sidequest/game/builder.py` (3,381 lines) and in per-pack `RulesConfig`, re-derived per pack instead of owned by the module. That asymmetry is the same disease ADR-142 named — "mechanics re-derived per world instead of owned by the ruleset" — one subsystem short of cured.

Two concrete drivers (from Keith, 2026-06-13/14):

1. **Attribute generation is not ruleset-owned.** `generate_stats`, `_allocate_point_buy`, and the `standard_array` branch live in `builder.py`; resource seeding leaks in as the module-level `seed_wwn_magic` / `seed_system_strain` functions. It should be owned by the `RulesetModule` the way combat now is.
2. **Fixed-order standard-array assignment puts the prime on the wrong stat.** `generate_stats` does `dict(zip(self._ability_score_names, base_values))` (builder.py:3225) — declaration order — so the array's top value (`14` for the WWN array `[14,12,11,10,9,7]`) lands on the first-declared stat (STR). Correct for a Warrior-default pack, **wrong for a caster Calling** whose prime is WIS/INT.

And the larger goal behind both: **a future WWN chargen library should be content, not an engine change** (the Jade requirement — authoring what a table wants must not require a server change). That only holds if the contribution surface lives on the module and the Skills/Foci/Background substrate exists to receive authored content.

### The structural problem (proven in code)

`RulesetModule` (`ruleset/base.py`) has **no chargen surface at all**. Its module docstring is explicit:

> "Spec 0 surface only: the five resolution operations the native turn already performs. Character-shape / advancement / narrator-contract surfaces are added when the SWN module plan needs them (YAGNI)."

That YAGNI moment is now. Meanwhile, ruleset-specific chargen mechanics have **already leaked into `builder.py`**, gated on slug/config-type rather than owned by a module:

| Leak | Location | Gate |
|---|---|---|
| Effort pools + spellcasting seed | `seed_wwn_magic(rules, stats, class_def)` (builder.py:103) | `rules.ruleset == "wwn"` |
| System Strain pool seed | `seed_system_strain(rules, stats)` (builder.py:84) | `isinstance(cfg, CwnConfig)` (covers CWN + AWN) |
| Attribute strategy + point-buy + array | `generate_stats` / `_allocate_point_buy` (builder.py:3141/3176) | `self._stat_generation` string switch |
| Attribute curve import | `from ...ruleset.swn import swn_attribute_modifier` (builder.py:28) | direct cross-module import |
| Standard-array "hint derivation" heuristic | `generate_stats` (builder.py:3242-3260) | `method == "standard_array"` + `acc.*_hint` |

These are ruleset decisions living in the orchestrator. The seam formalizes them.

### What does NOT exist yet (the substrate gap)

Confirmed repo-wide (server models, `Character`, `CreatureCore`, and the three WWN packs): there is **no Skills, Foci, or Background-as-skill-grant substrate**. `Character.background` is free-text prose (`str | None`); the only "skill" anywhere is `starting_skill_level` *inside* the WWN-magic Effort formula (one int per effort source). WWN's actual chargen pillars — the skill list, Foci (feat-like talents), and Backgrounds that grant skills — have no model representation. This spec **builds that substrate** (it is small and incremental — see §4) rather than deferring it.

---

## Target architecture

The combat seam is the template: **`builder.py : chargen :: dispatch/dice.py : combat`** — the builder is the FSM/scene/UI orchestrator; the module owns the mechanical contributions. The chargen surface is declared **flat on the `RulesetModule` ABC** (consistent with the existing flat `attack_params`/`save_params`/`resolve_trauma` surface), so `native` and the future `FateCoreRulesetModule` inherit the seam. WN-specific behavior lives on `WithoutNumberRulesetModule`; the ABC carries behavior-preserving defaults.

### The chargen contribution surface (five methods, all implemented)

| Method (on `RulesetModule`) | Owns | WN-core behavior | `native` behavior |
|---|---|---|---|
| `generate_attribute_values(*, method, ability_names, rng, cfg) -> list[int]` | the **batch** array / point-buy spread / 3d6 pool — the values, computed in one call | WWN array, SWN point-buy, etc. | reproduces today's `generate_stats` value generation exactly |
| `assign_attributes(*, pool, ability_names, class_def) -> dict[str,int]` | placement of values onto stats | **prime-aware** (top value → `class_def.prime_requisite`, rest by WN secondary priority) | fixed declaration order (today's behavior) |
| `seed_chargen_resources(*, rules, stats, class_def) -> ChargenResources` | Effort pools + System Strain | the migrated `seed_wwn_magic` + `seed_system_strain` | empty `ChargenResources` |
| `contribute_background_skills(*, background_def, rng) -> dict[str,int]` | Background → skill grants | reads `Background.free_skill` + `quick_skills` | `{}` |
| `contribute_foci(*, focus_defs) -> FociContribution` | Foci → skills + abilities | reads `Focus.levels[]` grants | empty |

`ChargenResources` and `FociContribution` are small typed return objects (Effort dict + spellcasting state + strain pool; skill-grant dict + `AbilityDefinition` list, respectively) — not new global state, just structured returns the builder applies.

The builder keeps **everything interactive**: the eager construction roll, the Roll-the-Bones reroll budget, the arrange turn-taking, scene gating. It calls the module for values/assignment/resources/grants. Driver 1 is satisfied — the *mechanics* move; the *FSM* stays.

### Module injection

`RulesConfig` already carries `rules.ruleset`, and the builder already reads `rules`. The single construction site (`handlers/connect.py:923`) needs **no signature change**: the builder resolves `self._ruleset = get_ruleset_module(rules.ruleset)` in `__init__` — the same source of truth the leaked `seed_*` functions read today, fail-loud via `UnknownRulesetError`.

---

## Scope of THIS spec (one vertical slice, real content)

Six sequential steps, one plan, atomic-or-not-at-all where behavior preservation demands it (the ADR-142 no-ball-drop rule). The chargen pipeline ships **complete and wired**, with **real WWN content** flowing to the character sheet — not fixtures, not `[]`-returning shells.

### Step 1 — Extract chargen mechanics to the seam (strictly behavior-preserving)

Extract-method-to-module refactor. Move `generate_attribute_values` / `_allocate_point_buy` / the standard-array branch / `seed_chargen_resources` behind the module surface. `NativeRulesetModule` and `WithoutNumberRulesetModule` reproduce **today's output byte-identically** — including the existing standard-array "hint derivation" heuristic, which moves onto the module unchanged (both native and WN-core inherit it for now; the WWN packs currently hit it). **Hard contract: zero behavior change** for every existing pack.

### Step 2 — Prime-aware assignment (the one deliberate change)

`WithoutNumberRulesetModule.assign_attributes` becomes prime-aware: the array's top value lands on the chosen Calling's `prime_requisite`; the remainder fill by a WN-defined secondary priority. This **supersedes the standard-array hint-derivation heuristic for WN packs** (the heuristic stays on `native`). Isolated from Step 1 so the characterization net cleanly separates "refactor (no change)" from "tuning (intended change)" — exactly ADR-142 Step 1 vs 2.

### Step 3 — Skills / Foci / Background substrate

- `Character.skills: dict[str,int]` (skill name → level; WWN untrained = absent/`-1`).
- `Background` model (`character.py`): `free_skill: str | None`, `quick_skills: list[str]` (and/or learning-table refs — minimal viable: free + quick).
- `Focus` model (`character.py`): `id`, `name`, `levels: list[FocusLevel]`, each `FocusLevel` granting `skills: dict[str,int]` and/or `abilities: list[AbilityDefinition]` (reuses the existing class-ability seeding path, `_seed_class_abilities`).
- `MechanicalEffects.skill_grants: dict[str,int]` + `focus_id: str | None` — the choice-scene grant carrier (parallels the existing `stat_bonuses` / `background` fields).
- `AccumulatedChoices` (builder.py:446) accumulates skills + foci across scenes.

### Step 4 — Contribution methods compute real grants

`contribute_background_skills` and `contribute_foci` on `WithoutNumberRulesetModule` compute grants from the chosen `Background`/`Focus` defs. `build()` applies them like `stat_bonuses` (builder.py:2461+ region), writing `Character.skills` and seeding focus abilities. OTEL spans on each (`{slug}.chargen.background_skills`, `{slug}.chargen.foci_applied`).

### Step 5 — UI: sheet surfacing + arrange reuse + the STAT_ORDER fix

- Reuse the **live** arrange picker (`StatArrangePanel` + `arrange_assign/clear/confirm/reject` messages + `chargen_mixin` handlers + builder arrange FSM) for the standard array: a builder seeding change parallel to `_roll_3d6_arrange_visible` feeds the array into `_arrangement_pool`, and the module's prime-aware `assign_attributes` becomes the **pre-filled default** (click-Confirm → correct caster build; rearrange available). `qualifying_classes_arrangement` already gates legality.
- `CharacterSheet` surfaces `skills` + Foci (incremental — it already renders stats).
- Fix `StatArrangePanel.STAT_ORDER`: read `ability_names` from the payload instead of the hardcoded `["STR","DEX","CON","INT","WIS","CHA"]`, so flavor-named packs arrange correctly.

### Step 6 — Real WWN content (3 packs)

For `caverns_and_claudes`, `heavy_metal`, `elemental_harmony`: the real WWN skill list, real Backgrounds with skill grants, and a **real starter Focus set** — enough that a freshly created character lands on the sheet with skills and a focus from actual play data. The full ~50-Focus catalog extends additively with **zero engine change** (that is the point of the seam).

---

## Test strategy

- **Chargen characterization net (pin Step 1):** capture per-method output (`point_buy`, `standard_array` + hint-derivation, `roll_3d6_strict`, `roll_the_bones`, `seed_chargen_resources`) for a synthetic matrix across `native`/`wwn`/`swn`/`cwn`/`awn` against current code; assert byte-identical after extraction. Synthetic fixtures only (no pack load — the "no content in unit tests" rule).
- **Step 2 (intended change):** new assertions that the WWN array's top value lands on a caster Calling's `prime_requisite` and on a Warrior's STR — the only output expected to change between Step 1 and Step 2.
- **Substrate + contribution:** fixture-driven — synthetic `Background`/`Focus` defs → assert `Character.skills` and seeded focus abilities after `build()`.
- **Wiring test (not source-grep, per "No Source-Text Wiring Tests"):** build a synthetic WWN pack through the real builder, assert the prime lands correctly and skills/foci reach the sheet — proving the builder calls the module end-to-end. OTEL span assertions for the chargen decisions.
- **Arrange reuse:** drive `arrange_assign/confirm` with a standard-array-seeded pool; assert the picker resolves and the prime-aware default pre-fills.

---

## Risks / watch-outs

- **Behavior preservation across all packs.** Every non-WWN pack's chargen output must be byte-identical post-Step-1. The characterization net is the enforcement; native must reproduce the hint-derivation heuristic exactly.
- **`generate_stats` is deeply entangled with the FSM.** The eager construction roll, Roll-the-Bones, and arrange turn-taking are interactive and must stay in the builder. The seam moves only value/assignment/resource *computation*, not turn flow — keep the cut at that line or the FSM breaks.
- **Standard-array arrange changes an interaction-free path into an interactive one for WWN packs.** The prime-aware *default* fixes Driver 2 with zero clicks; presenting the arrange picker is the optional richness. Confirm per-pack whether the WWN packs present the arrange scene or take the default silently (default is the safe, low-friction baseline — protects Alex).
- **Focus ability seeding reuses `_seed_class_abilities`.** Confirm during Step 4 that a focus-granted ability and a class-granted ability coexist without id collision.
- **Content magnitude.** The full WWN Focus catalog is large; Step 6 ships a real starter set, not the whole catalog. This is content backlog, not deferred engine work — the catalog grows with no code change.

---

## Explicitly out of scope (principled, not deferral-reflex)

1. **Lethality "feel" tuning** — Keith's call: needs playtest data; the WWN trauma/strain baseline is already faithful. Unchanged here.
2. **The exhaustive Focus catalog** — the *system* ships complete and *real* WWN skills/backgrounds/starter-foci ship with it; remaining foci are pure data entry (content), additive, zero engine change.
3. **SWN / CWN / AWN chargen libraries** — this spec makes the seam real and proves it on WWN. The sibling libraries are content authored against the now-existing surface (the ADR-142 deferred #3), no further builder surgery.
4. **Fate Core chargen** — `FateCoreRulesetModule` + its chargen, replacing `native` per genre (ADR-142 deferred #4).

---

## References

- Parent: `docs/superpowers/specs/2026-06-13-without-number-core-extraction-design.md` (ADR-142, "Still deferred #1"); `project_without_number_srd_strategy` memory.
- ADR-117 (pluggable ruleset module system), ADR-015 (character builder state machine), ADR-016 (three-mode character creation), ADR-007 (unified character model), ADR-140 (genre is rulebook only; world owns cast/catalog), ADR-095 (class mechanical surface).
- Code (server): `sidequest/game/builder.py` (`generate_stats`:3176, `_allocate_point_buy`:3141, arrange FSM:2985/1276-1334, `seed_wwn_magic`:103, `seed_system_strain`:84, `AccumulatedChoices`:446, `build()`:2424); `sidequest/game/ruleset/{base,without_number,native}.py`; `sidequest/genre/models/{character,rules}.py` (`MechanicalEffects`:98, `ClassDef`:244, `RulesConfig`:1000); `sidequest/server/websocket_handlers/chargen_mixin.py` (`_chargen_arrange_*`); `sidequest/protocol/messages.py` (`arrange_*`).
- Code (UI): `src/components/CharacterCreation/StatArrangePanel.tsx`, `CharacterCreation.tsx`, `CharacterSheet`.
- SRD: Worlds Without Number SRD (chargen: attributes, the standard array, Backgrounds, Foci, skills) — Sine Nomine local copy.
