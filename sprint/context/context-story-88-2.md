---
parent: context-epic-88.md
workflow: tdd
---

# Story 88-2: AWN Plan 1 content — mutant_wasteland awn binding, standard-six sweep, hp_depletion combat confrontation

**Story:** 88-2
**Points:** 3
**Workflow:** tdd
**Epic:** 88 (Ashes Without Number — mutant_wasteland ruleset port)
**Repos:** sidequest-content (primary); see Assumptions re: server calibration tests
**Depends on:** 88-1 (done — `_validate_awn` + registry binding merged in sidequest-server PR #682)

## Business Context

This is **Story B** of the spec §11.6 split: the content half that makes `mutant_wasteland` an actual working `awn` pack. 88-1 built the engine seam; until this story lands, no pack binds to it — the module is registered but unreachable from play. After this story, mutant_wasteland combat resolves on real ablative HP with Shock, Trauma, Mortal/Major Injury, and four saves — visible on the sheet and in the dice overlay. This is the crunch Sebastien and Jade asked for after `coyote_star`, delivered **as content** (pack YAML), which is itself the point: per the Jade doctrine, the crunch a table wants must be expressible in homebrew content, not engine code.

## Technical Guardrails

**Authoritative spec:** `docs/superpowers/specs/2026-06-05-ashes-without-number-mutant-wasteland-design.md` — §4 (the numbers), §6.2 (rules.yaml changes), §6.3 (sweep), §6.4 (calibration trap), §11.5 (chargen faithfulness note), §11.6 (story split).

**Pattern precedent:** road_warrior → CWN binding (`2026-06-04-road-warrior-cwn-rig-combat-design.md` §6) — follow its `rules.yaml` shape verbatim where applicable.

- **All changes are content YAML** in `genre_packs/mutant_wasteland/`. No engine code. If something can't be expressed in pack YAML, that's a finding to escalate, not a license to touch the server.
- **`rules.yaml`:** add `ruleset: awn`; add `awn:` config block carrying the §4 numbers — `unarmored_ac: 10`, `save_base: 15`, trauma (`default_trauma_target: 6`, `mortal_injury_rounds: 6`, `major_injury_save: "physical"`), system_strain (`max_source: CONSTITUTION`, `rest_recovery_per_night: 1`, `first_aid_cost: 1`), and the now-identity six-key `attribute_map`. `_validate_awn` (from 88-1) fails loud on an incomplete map — that's the contract this story authors against.
- **No hacking config.** `AwnConfig.hacking` stays `None`; do not add a hacking block.
- **Standard six (D4):** replace `ability_score_names` (rules.yaml:13) and sweep every flavor-name reference: `Brawn`→STR, `Reflexes`→DEX, `Toughness`→CON, `Wits`→INT, `Instinct`→WIS, `Presence`→CHA. Ground-truth grep (2026-06-05) found hits in: `rules.yaml` (~23 lines, incl. confrontation `stat_check:`s), `archetypes.yaml` (~12), `power_tiers.yaml` (~4), `char_creation.yaml` (~2), `progression.yaml` (~1); `inventory.yaml`/`axes.yaml`/`prompts.yaml` currently clean — **verify, don't trust the count** (prose words like "presence" can false-positive; stat references can hide in tropes/cultures/magic too — sweep the whole pack dir). Classes/Stocks (Scavenger/Mutant/Pureblood/etc.) keep their flavor names; only the six attribute labels change.
- **Combat confrontation:** replace "Wasteland Brawl" (rules.yaml:90, momentum-to-7) with an `hp_depletion` combat confrontation. **Keep the strike/brace/angle/push beat texture** — HP flows underneath. Must carry `opponent_default_stats` with **all six** ability scores + `hp` + `armor_class` (the documented "needs ALL SIX for saves" gotcha).
- **Keep as dial confrontations:** "Wasteland Parley" (rules.yaml:44, negotiation) and "Wasteland Pursuit" (rules.yaml:160, chase) — not combat, no `hp_depletion`.
- **Retire `magic_level`** (rules.yaml:3) per its own DRAFT note. Do **not** touch `magic.yaml` itself — the mutations↔magic reconciliation is Plan 2's Architect call (spec §7). Until then the pack carries both framings; flag, don't fix.
- **Lethality:** the pack is `lethality: moderate` (`lethality_policy.yaml`) — the 0-HP outcome honors it.
- **Do NOT touch:** `flickering_reach` world content (spoilable world — its recalibration is a separate post-Plan-1 pass, spoiler discipline applies); encumbrance (stays `none`); any other pack.

## Scope Boundaries

**In scope:**
- `rules.yaml`: `ruleset: awn`, `awn:` config block, standard-six `ability_score_names`, `hp_depletion` combat confrontation, `magic_level` retirement
- Standard-six sweep across all mutant_wasteland pack files (§6.3)
- Calibration-test migration fallout per §6.4 precedent (see Assumptions)
- Pack loads cleanly via the genre loader with the bound `awn` ruleset

**Out of scope:**
- Mutations, Radiation, Disease, Stress, survival, creatures, enclaves (Plans 2–7)
- `magic.yaml` reconciliation (Plan 2)
- `flickering_reach` world recalibration
- Weapon-level `DamageSpec` Trauma/Shock authoring beyond what the confrontation needs (the inventory-fattening plan)
- `stat_generation: point_buy` change — AWN-native is 3d6/standard-array, but point-buy stays mechanically valid; faithfulness call deferred to GM (§11.5), not a blocker
- Any engine/server code

## AC Context

1. **Pack binds to awn and loads.** `rules.yaml` carries `ruleset: awn` + a complete `awn:` block; the loader resolves `get_ruleset_module("awn")` and `_validate_awn` passes. Test: pack-load test with `SIDEQUEST_GENRE_PACKS` set; a deliberately incomplete attribute_map must fail loud (validator contract from 88-1).
2. **Standard six everywhere.** No flavor attribute name (Brawn/Reflexes/Toughness/Wits/Instinct/Presence) survives as a *mechanical reference* anywhere in the pack (stat_check fields, ability_score_names, archetype stat blocks, progression/power-tier references). Test: exhaustive grep assertion across the pack dir; prose mentions in narrative flavor text are acceptable only where they aren't parsed as stat keys.
3. **Combat is hp_depletion.** "Wasteland Brawl" is replaced by an `hp_depletion` confrontation with `opponent_default_stats` carrying all six scores + `hp` + `armor_class`; beat texture preserved. Test: confrontation schema validation + the seeded-combat wiring path.
4. **Social confrontations untouched mechanically.** Parley and Pursuit remain dial confrontations (their stat_checks renamed to standard six only).
5. **`magic_level` retired.** The flag and its DRAFT note are gone; `magic.yaml` is unmodified.
6. **Calibration migration handled per precedent (§6.4).** Baseline failure list recorded *before* the change; dial-schema/`COMBAT_PACKS` regressions resolved the road_warrior way (filter `dial_threshold`, drop mutant_wasteland from the dial-`COMBAT_PACKS` set); full suite green with `SIDEQUEST_DATABASE_URL` + `SIDEQUEST_GENRE_PACKS` set.
7. **End-to-end wiring (the lie detector).** A mutant_wasteland combat turn through the production dispatch path fires the inherited `cwn.*` spans and depletes HP on the ablative pool, and the opponent reprisal fires. (88-1 proved the engine path; this AC proves it *with the real pack content* — span assertions, not source-text greps.)

## Assumptions

- **88-1's seams are complete and merged** (PR #682): registry binding, `_validate_awn`, chargen strain-pool fix, downed-seam/stabilize/strain guards. If 88-2 testing reveals a missed slug-string site, that's an 88-1 gap — log a deviation and route the engine fix properly; do not patch it from the content story.
- **Calibration-test fallout lives in sidequest-server** (§6.4) even though this story's repo is content. Per the road_warrior precedent the dial-`COMBAT_PACKS` membership change is a test-file edit in the server repo. If so, the story touches server *tests only* — flag in the session file and PR description; if the repos field needs amending to `content,server`, SM handles it.
- **The §6.3 file list is a floor, not a ceiling** — the sweep verifies the whole pack dir, including files the spec didn't enumerate (tropes.yaml, cultures.yaml, magic.yaml prose, achievements.yaml).
- **Worlds under `mutant_wasteland/worlds/` may carry stat references** — in-scope for the rename sweep *except* `flickering_reach` lore beyond mechanical stat keys (spoiler discipline).
