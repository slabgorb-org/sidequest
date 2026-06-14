# Ruleset Chargen Seam Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move character-generation mechanics off `builder.py` onto a chargen contribution surface on `RulesetModule` (the chargen analogue of ADR-142's combat ownership), make standard-array assignment prime-aware, and build the real WWN Skills/Foci/Background substrate with content — end-to-end.

**Architecture:** The builder stays the FSM/scene/UI orchestrator; the module owns the mechanical contributions. Five methods are declared on the `RulesetModule` ABC with **behavior-preserving defaults** (native inherits today's behavior byte-identically); `WithoutNumberRulesetModule` overrides `assign_attributes` (prime-aware), `seed_chargen_resources` (migrated Effort/Strain seeding), and the two contribution methods (Background→skills, Foci). The live arrange picker is reused for the standard array via pool seeding. Two phases: **Phase 1** (Steps 1–2) is a behavior-preserving extraction + the one deliberate prime-aware change + arrange reuse + the `STAT_ORDER` UI fix — it ships standalone and fixes both drivers. **Phase 2** (Steps 3–6) adds the Skills/Foci/Background models, loader, contribution methods, sheet surfacing, and real WWN content.

**Tech Stack:** Python 3 / pytest (`-n auto` xdist default; `-n0` for OTEL span-count isolation per `project_server_test_otel_deadlock`), pydantic v2 models, OpenTelemetry spans; React/TypeScript + Vitest (UI); YAML genre-pack content.

**Source-of-truth design:** `docs/superpowers/specs/2026-06-14-ruleset-chargen-seam-design.md` (promote to ADR-143). Where code investigation refined the spec, this plan governs and the deviation is logged below.

**Repos & base branches (per repos.yaml):** orchestrator (`.`) → `main`; `sidequest-server` / `sidequest-ui` / `sidequest-content` → `develop`. Branch before committing in each (the PreToolUse hook blocks protected-branch commits). Server commits land on a `feat/chargen-seam-*` branch off `develop`.

---

## Design Decisions (refinements discovered in code)

- **DD-1 — The five methods live on the ABC as concrete defaults, not `@abstractmethod`.** `base.py`'s `RulesetModule` already mixes abstract operations with concrete defaults (e.g. `resolve_trauma` identity-passthrough, `resolve_shock` → 0). The chargen methods follow that pattern: concrete defaults reproducing today's `builder.generate_stats` behavior, so `NativeRulesetModule` (which adds nothing) inherits byte-identical chargen. `WithoutNumberRulesetModule` overrides the three that change. This is why Step 1 can be byte-identical.

- **DD-2 — `generate_attributes` is the single Step-1 move; the `_values`/`assign` split is Step 2.** Step 1 moves the *whole* `generate_stats` body to `RulesetModule.generate_attributes(...)` verbatim (byte-identical net passes). Step 2 refactors that default into `_generate_attribute_values(...)` + `assign_attributes(...)` so WN-core overrides only `assign_attributes`. Keeping the split in Step 2 means the characterization net cleanly attributes any output change to the prime-aware override, not the extraction.

- **DD-3 — `standard_array_arrange` is a NEW stat_generation mode, not a change to `standard_array`.** `standard_array` stays the non-interactive default (now prime-aware via the WN override). Packs that want the interactive picker author `stat_generation: standard_array_arrange` — parallel to the existing `roll_3d6_strict` vs `roll_3d6_arrange_visible` pair. No existing pack changes behavior unless it opts in.

- **DD-4 — The standard-array "hint derivation" heuristic (builder.py:3242-3260) stays in the ABC default path.** Native keeps it. WN-core's prime-aware `assign_attributes` override supersedes it (does not call it). Logged so a future reader knows the heuristic is intentionally native-only.

- **DD-5 — Backgrounds become modeled entities; `background: <id>` strings already exist (Evrópí).** heavy_metal/evropi authors `background: Zkęd-Frontier` today with no definitions file. Phase 2 adds `backgrounds.yaml` and resolves the id to a `Background` def. Until a pack authors `backgrounds.yaml`, an unmatched `background:` id remains free-text prose (current behavior — no regression).

- **DD-6 — `skills`/`foci` ride `members[].sheet` in PARTY_STATUS, not a new top-level payload.** The UI `CharacterSheetData` already flows through `sheet`. Phase 2 adds `skills`/`foci` to that dict server-side and to `CharacterSheetData` client-side.

---

## File Structure

**Server — created:**
- `sidequest/game/chargen_contribution.py` — `ChargenResources` + `FociContribution` typed return objects (small; one responsibility: structured chargen-contribution returns the builder applies).
- `tests/game/ruleset/test_143_chargen_characterization.py` — Step-1 byte-identity net (per-method, per-slug, synthetic fixtures).
- `tests/game/ruleset/test_143_prime_aware_assignment.py` — Step-2 intended-change assertions.
- `tests/game/ruleset/test_143_chargen_resources.py` — `seed_chargen_resources` parity with the old `seed_*` functions.
- `tests/game/test_chargen_seam_wiring.py` — end-to-end: build a synthetic WWN pack through the real builder; assert prime placement + skills/foci reach the sheet + OTEL spans.
- `tests/genre/test_skills_foci_background_models.py` — model + loader tests.

**Server — modified:**
- `sidequest/game/ruleset/base.py` — add the five chargen methods (concrete defaults).
- `sidequest/game/ruleset/without_number.py` — override `assign_attributes`, `seed_chargen_resources`, `contribute_background_skills`, `contribute_foci`.
- `sidequest/game/builder.py` — `__init__` resolves the module; `generate_stats` delegates; `build()` applies resources + skills + foci; new `_seed_standard_array_arrange`; `AccumulatedChoices` gains `skill_grants`/`foci`.
- `sidequest/genre/models/character.py` — `Skill`/`Background`/`Focus`/`FocusLevel` models; `MechanicalEffects.skill_grants`/`focus_id`; `Character.skills`/`foci`.
- `sidequest/genre/models/genre_pack.py` (+ loader) — load `skills.yaml`/`backgrounds.yaml`/`foci.yaml`; `resolve_backgrounds`/`resolve_foci`.
- `sidequest/handlers/connect.py` — pass resolved backgrounds/foci to the builder.
- `sidequest/server/websocket_handlers/chargen_mixin.py` — `members[].sheet` carries `skills`/`foci`.
- `sidequest/protocol/messages.py` — `stat_arrange` payload carries `ability_names`.

**UI — modified:**
- `src/components/CharacterCreation/StatArrangePanel.tsx` — `STAT_ORDER` → `statOrder` prop.
- `src/components/CharacterCreation/CharacterCreation.tsx` — pass `statOrder` from `scene.ability_names`; `CreationScene` gains `ability_names`.
- `src/components/CharacterSheet.tsx` — `skills`/`foci` sections + `CharacterSheetData` fields.
- `src/types/payloads.ts` — `ability_names` on `CharacterCreationPayload`.

**Content — created (per pack: caverns_and_claudes, heavy_metal, elemental_harmony):**
- `skills.yaml`, `backgrounds.yaml`, `foci.yaml`
- chargen scene extensions (genre-tier for C&C; world-tier for heavy_metal/elemental_harmony).

---

# PHASE 1 — Server extraction + prime-aware + arrange reuse (Steps 1–2)

## Task 1: Chargen characterization net (pin current behavior)

Captures current `generate_stats` / `seed_system_strain` / `seed_wwn_magic` output for a synthetic matrix so the extraction is provably byte-identical. Passes before AND after — a characterization net, not a red/green feature test. Synthetic fixtures only (the "no content in unit tests" rule).

**Files:**
- Create: `sidequest-server/tests/game/ruleset/test_143_chargen_characterization.py`

- [ ] **Step 1: Write the characterization tests**

Read `tests/game/ruleset/test_wwn_effort.py` and `tests/game/test_builder*.py` first for the exact `RulesConfig` / `ClassDef` / `CharacterBuilder` construction helpers and reuse them (copy minimal builders into this test; do not import test internals).

```python
"""Characterization net pinning chargen output across the ADR-143 extraction.

Pins builder.generate_stats + seed_system_strain + seed_wwn_magic byte-identical
before and after the move onto the RulesetModule surface. Synthetic fixtures only.
"""
from __future__ import annotations

import random

import pytest

from sidequest.game.builder import seed_system_strain, seed_wwn_magic
from sidequest.genre.models.rules import RulesConfig


def _wwn_rules() -> RulesConfig:
    # Minimal WWN rules: standard_array + attribute_map (mirror caverns_and_claudes/rules.yaml).
    return RulesConfig.model_validate(
        {
            "ruleset": "wwn",
            "stat_generation": "standard_array",
            "standard_array": [14, 12, 11, 10, 9, 7],
            "ability_score_names": ["STR", "DEX", "CON", "INT", "WIS", "CHA"],
            "wwn": {
                "attribute_map": {
                    "STRENGTH": "STR", "DEXTERITY": "DEX", "CONSTITUTION": "CON",
                    "INTELLIGENCE": "INT", "WISDOM": "WIS", "CHARISMA": "CHA",
                },
            },
        }
    )


def test_seed_system_strain_none_for_wwn():
    # WWN is not CwnConfig → no strain pool (current behavior).
    rules = _wwn_rules()
    assert seed_system_strain(rules, {"CON": 11}) is None


def test_seed_wwn_magic_empty_for_non_magic_class():
    rules = _wwn_rules()
    effort, sc = seed_wwn_magic(rules, {"INT": 14}, class_def=None)
    assert effort == {}
    assert sc is None


def test_generate_stats_standard_array_fixed_order_today():
    # Pin the CURRENT (pre-prime-aware) fixed-order assignment: 14 lands on STR.
    from sidequest.game.builder import CharacterBuilder  # noqa: PLC0415
    from tests.game._builder_helpers import minimal_scenes  # provide via conftest if absent
    builder = CharacterBuilder(scenes=minimal_scenes(), rules=_wwn_rules(), rng=random.Random(1))
    acc = builder.accumulated()
    stats = builder.generate_stats(acc)
    assert stats["STR"] == 14  # current fixed-order behavior — CHANGES in Step 2 (caster only)
```

Fill `minimal_scenes` from the existing builder test helpers. Run once, pin any captured value.

- [ ] **Step 2: Run against current code; confirm GREEN**

Run: `cd sidequest-server && uv run pytest -n0 tests/game/ruleset/test_143_chargen_characterization.py -v`
Expected: PASS (this is the frozen baseline).

- [ ] **Step 3: Commit**

```bash
git add tests/game/ruleset/test_143_chargen_characterization.py
git commit -m "test(ruleset): characterization net pinning chargen output pre-extraction (ADR-143)"
```

---

## Task 2: `ChargenResources` type + `seed_chargen_resources` on the module surface

Move `seed_system_strain` + `seed_wwn_magic` onto the module as one method returning a structured object. ABC default = empty; WN-core override = the migrated bodies.

**Files:**
- Create: `sidequest-server/sidequest/game/chargen_contribution.py`
- Modify: `sidequest-server/sidequest/game/ruleset/base.py`, `sidequest-server/sidequest/game/ruleset/without_number.py`
- Create: `sidequest-server/tests/game/ruleset/test_143_chargen_resources.py`

- [ ] **Step 1: Write the failing test**

```python
"""seed_chargen_resources parity with the legacy module-level seed_* functions."""
from __future__ import annotations

from sidequest.game.ruleset import get_ruleset_module
from sidequest.genre.models.rules import RulesConfig


def _wwn_rules() -> RulesConfig:
    return RulesConfig.model_validate({
        "ruleset": "wwn", "stat_generation": "standard_array",
        "standard_array": [14, 12, 11, 10, 9, 7],
        "ability_score_names": ["STR", "DEX", "CON", "INT", "WIS", "CHA"],
        "wwn": {"attribute_map": {"STRENGTH": "STR", "DEXTERITY": "DEX",
            "CONSTITUTION": "CON", "INTELLIGENCE": "INT", "WISDOM": "WIS", "CHARISMA": "CHA"}},
    })


def test_wn_core_seed_resources_empty_for_non_magic_class():
    module = get_ruleset_module("wwn")
    res = module.seed_chargen_resources(rules=_wwn_rules(), stats={"INT": 14}, class_def=None)
    assert res.effort == {}
    assert res.spellcasting is None
    assert res.system_strain is None


def test_native_seed_resources_is_empty():
    module = get_ruleset_module("native")
    res = module.seed_chargen_resources(rules=RulesConfig(), stats={}, class_def=None)
    assert res.effort == {} and res.spellcasting is None and res.system_strain is None
```

Run: `cd sidequest-server && uv run pytest -n0 tests/game/ruleset/test_143_chargen_resources.py -v`
Expected: FAIL — `seed_chargen_resources` does not exist.

- [ ] **Step 2: Create the return type**

`sidequest/game/chargen_contribution.py`:

```python
"""Structured returns from the RulesetModule chargen surface (ADR-143).

Not new global state — small typed bundles the builder applies onto the Character.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from sidequest.game.system_strain import SystemStrainPool
from sidequest.game.wwn_magic import EffortPool, SpellcastingState


class ChargenResources(BaseModel):
    """Effort pools + spellcasting + system strain seeded at chargen."""

    model_config = {"extra": "forbid"}

    effort: dict[str, EffortPool] = Field(default_factory=dict)
    spellcasting: SpellcastingState | None = None
    system_strain: SystemStrainPool | None = None


class FociContribution(BaseModel):
    """Skill grants + ability definitions contributed by selected Foci."""

    model_config = {"extra": "forbid"}

    skills: dict[str, int] = Field(default_factory=dict)
    # AbilityDefinition imported lazily by the builder when applying; store as the model.
    abilities: list = Field(default_factory=list)
```

- [ ] **Step 3: Add the ABC default**

In `sidequest/game/ruleset/base.py`, add to `RulesetModule` (after `resolve_hacking`, before `deal_table`):

```python
    def seed_chargen_resources(self, *, rules, stats, class_def):
        """Effort/spellcasting/system-strain seeded at chargen. Default: none.

        Only WithoutNumberRulesetModule overrides (Effort + Strain are WN-family).
        Returns ChargenResources. Imported lazily to keep lean rulesets free of
        the wwn_magic/system_strain import at module load."""
        from sidequest.game.chargen_contribution import ChargenResources

        return ChargenResources()
```

- [ ] **Step 4: Override on the WN core; migrate the bodies**

In `sidequest/game/ruleset/without_number.py`, add after `activate_discipline` (line ~793). Move the bodies of `seed_system_strain` and `seed_wwn_magic` here verbatim (from builder.py:84-100 and 103-172), adapting to return `ChargenResources`:

```python
    def seed_chargen_resources(self, *, rules, stats, class_def):
        """WN-family Effort pools + spellcasting + system strain (migrated from
        builder.seed_wwn_magic + seed_system_strain, ADR-143)."""
        from sidequest.game.chargen_contribution import ChargenResources
        from sidequest.game.ruleset.swn import swn_attribute_modifier
        from sidequest.game.system_strain import SystemStrainPool
        from sidequest.game.wwn_magic import EffortPool, SpellcastingState
        from sidequest.genre.models.rules import CwnConfig

        # --- system strain (was seed_system_strain) ---
        system_strain = None
        cfg = rules.ruleset_config()
        if isinstance(cfg, CwnConfig):
            con_flavor = cfg.attribute_map["CONSTITUTION"]
            body_score = int(stats.get(con_flavor, 10))
            system_strain = SystemStrainPool(current=0, max=max(1, body_score), permanent=0)

        # --- wwn magic (was seed_wwn_magic) ---
        effort: dict[str, EffortPool] = {}
        spellcasting: SpellcastingState | None = None
        if rules.ruleset == "wwn" and rules.wwn is not None and class_def is not None \
                and class_def.wwn_magic is not None:
            cm = class_def.wwn_magic
            effort_base = rules.wwn.magic.effort_base
            attr_map = rules.wwn.attribute_map
            for src in cm.effort_sources:
                flavor = attr_map[src.governing_attr]
                score = int(stats.get(flavor, 10))
                pool_max = effort_base + src.starting_skill_level + swn_attribute_modifier(score)
                if cm.partial:
                    pool_max -= 1
                pool_max = max(1, pool_max)
                effort[src.source] = EffortPool(source=src.source, max=pool_max)
            if cm.casts_per_day_by_level:
                level_key = "1"
                casts_per_day = cm.casts_per_day_by_level.get(level_key, 0)
                max_spell_level = cm.max_spell_level_by_level.get(level_key, 0)
                capacity = cm.prepared_by_level.get(level_key, len(cm.starting_prepared))
                spellcasting = SpellcastingState(
                    prepared=cm.starting_prepared[:capacity],
                    casts_remaining=casts_per_day,
                    casts_per_day=casts_per_day,
                    max_spell_level=max_spell_level,
                )

        return ChargenResources(effort=effort, spellcasting=spellcasting, system_strain=system_strain)
```

- [ ] **Step 5: Run the test; confirm PASS**

Run: `cd sidequest-server && uv run pytest -n0 tests/game/ruleset/test_143_chargen_resources.py -v`
Expected: PASS.

- [ ] **Step 6: Point the builder at the module; keep `seed_*` as thin shims (temporary)**

In `builder.py` `build()` (lines 2834-2839), replace the two `seed_*` calls with one module call. Keep the old `seed_system_strain`/`seed_wwn_magic` functions for now (Task 1's net imports them) — they become thin wrappers calling the module, deleted in Step 7:

```python
        _res = self._ruleset.seed_chargen_resources(
            rules=self._rules, stats=stats, class_def=_resolved_class_def
        )
        system_strain = _res.system_strain
        wwn_effort, wwn_spellcasting = _res.effort, _res.spellcasting
```

(`self._ruleset` is added in Task 3 Step 2 — if doing Task 2 first, add `self._ruleset = get_ruleset_module(rules.ruleset)` to `__init__` now and import `get_ruleset_module`.)

- [ ] **Step 7: Delete the migrated functions; update the net's imports**

Delete `seed_system_strain` (builder.py:84-100) and `seed_wwn_magic` (103-172). Update `test_143_chargen_characterization.py` to call `get_ruleset_module("wwn").seed_chargen_resources(...)` instead of the deleted functions. Grep for other callers:

Run: `cd sidequest-server && rg -n "seed_system_strain|seed_wwn_magic" sidequest tests`
Fix every non-test caller to use the module; update tests to the new surface.

- [ ] **Step 8: Run full ruleset + builder suites**

Run: `cd sidequest-server && uv run pytest -n0 tests/game/ruleset/ tests/game/test_builder*.py -q`
Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add sidequest/game/chargen_contribution.py sidequest/game/ruleset/base.py \
  sidequest/game/ruleset/without_number.py sidequest/game/builder.py tests/game/ruleset/test_143_chargen_resources.py \
  tests/game/ruleset/test_143_chargen_characterization.py
git commit -m "refactor(ruleset): move chargen resource seeding onto RulesetModule.seed_chargen_resources (ADR-143)"
```

---

## Task 3: Move `generate_attributes` onto the module (byte-identical)

**Files:**
- Modify: `sidequest-server/sidequest/game/ruleset/base.py`, `sidequest-server/sidequest/game/builder.py`

- [ ] **Step 1: Add the ABC default = today's `generate_stats` body**

In `base.py`, add `generate_attributes` to `RulesetModule`. Move the **entire** body of `builder.generate_stats` (builder.py:3176-3266, including `_allocate_point_buy` and the hint-derivation heuristic) into this method. Signature takes everything the body reads off `self` today as explicit params:

```python
    def generate_attributes(self, *, method, ability_names, standard_array,
                            point_buy_budget, rolled_stats, acc, rng):
        """Generate the ability-score dict per `method`. Default = the historical
        builder behavior (point_buy / standard_array + hint-derivation / 3d6 / bones).
        WithoutNumberRulesetModule overrides the assignment to be prime-aware (ADR-143)."""
        # ... verbatim generate_stats body, reading the passed params instead of self._* ...
```

Move `_allocate_point_buy` to a module-level helper in `base.py` (or a staticmethod on the ABC) so both the ABC default and any override can call it.

- [ ] **Step 2: Resolve the module in `__init__` and delegate `generate_stats`**

In `builder.py` `__init__`, add (with `from sidequest.game.ruleset import get_ruleset_module` at top):

```python
        self._ruleset = get_ruleset_module(rules.ruleset)
```

Replace `generate_stats`'s body with a delegation:

```python
    def generate_stats(self, acc: AccumulatedChoices) -> dict[str, int]:
        """Delegate to the bound RulesetModule (ADR-143). The module owns the
        attribute mechanics; the builder owns the FSM that gathered `acc`."""
        return self._ruleset.generate_attributes(
            method=self._stat_generation,
            ability_names=self._ability_score_names,
            standard_array=self._standard_array,
            point_buy_budget=self._point_buy_budget,
            rolled_stats=self._rolled_stats,
            acc=acc,
            rng=self._rng,
        )
```

- [ ] **Step 3: Run the characterization net; confirm byte-identical**

Run: `cd sidequest-server && uv run pytest -n0 tests/game/ruleset/test_143_chargen_characterization.py tests/game/test_builder*.py -q`
Expected: PASS (zero behavior change — `test_generate_stats_standard_array_fixed_order_today` still asserts `STR == 14`).

- [ ] **Step 4: Commit**

```bash
git add sidequest/game/ruleset/base.py sidequest/game/builder.py
git commit -m "refactor(ruleset): move generate_attributes onto RulesetModule, builder delegates (ADR-143 Step 1, byte-identical)"
```

---

## Task 4: Prime-aware `assign_attributes` on the WN core (the one deliberate change)

**Files:**
- Modify: `sidequest-server/sidequest/game/ruleset/base.py` (split default into `_generate_attribute_values` + `assign_attributes`), `sidequest-server/sidequest/game/ruleset/without_number.py` (override `assign_attributes`)
- Create: `sidequest-server/tests/game/ruleset/test_143_prime_aware_assignment.py`

- [ ] **Step 1: Write the failing Step-2 test**

```python
"""WN-core standard-array assignment is prime-aware (ADR-143 Step 2)."""
from __future__ import annotations

from sidequest.game.ruleset import get_ruleset_module
from sidequest.genre.models.character import ClassDef


def _class(prime: str) -> ClassDef:
    return ClassDef.model_validate({
        "id": "c", "display_name": "C", "rpg_role": "control", "jungian_default": "magician",
        "prime_requisite": prime, "minimum_score": 9, "kit_table": "k",
    })


def test_caster_prime_gets_top_value():
    module = get_ruleset_module("wwn")
    names = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
    stats = module.assign_attributes(
        pool=[14, 12, 11, 10, 9, 7], ability_names=names, class_def=_class("INT")
    )
    assert stats["INT"] == 14  # prime lands the top value, NOT STR


def test_warrior_prime_gets_top_value():
    module = get_ruleset_module("wwn")
    names = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
    stats = module.assign_attributes(
        pool=[14, 12, 11, 10, 9, 7], ability_names=names, class_def=_class("STR")
    )
    assert stats["STR"] == 14
```

Run: `cd sidequest-server && uv run pytest -n0 tests/game/ruleset/test_143_prime_aware_assignment.py -v`
Expected: FAIL — `assign_attributes` not defined.

- [ ] **Step 2: Split the ABC default into value-gen + assign**

In `base.py`, refactor `generate_attributes` so the standard-array/point-buy/3d6 branches produce a `pool: list[int]` via `_generate_attribute_values(...)`, then call `self.assign_attributes(pool=..., ability_names=..., class_def=acc-resolved-class)`. Add the ABC default `assign_attributes` = today's fixed-order zip + the hint-derivation heuristic (moved out of `generate_attributes`):

```python
    def assign_attributes(self, *, pool, ability_names, class_def, acc=None):
        """Place pool values onto stats. Default: declaration order (historical),
        plus the standard-array hint-derivation heuristic. WN-core overrides
        with prime-aware placement (ADR-143 DD-4: heuristic stays native-only)."""
        stats = dict(zip(ability_names, pool, strict=False))
        # ... the hint-derivation heuristic from old generate_stats:3242-3260 ...
        return stats
```

Thread `class_def` into the call chain: `generate_attributes` resolves it from `acc.class_hint` against the class roster — but the roster lives on the builder. **Pass the resolved `class_def` into `generate_attributes` as a param** (builder resolves it from `self._classes` + `acc.class_hint` before delegating). Update `builder.generate_stats` to resolve and pass `class_def=...`.

- [ ] **Step 3: Override on the WN core (prime-aware)**

In `without_number.py`:

```python
    def assign_attributes(self, *, pool, ability_names, class_def, acc=None):
        """Prime-aware: the chosen Calling's prime_requisite gets the highest pool
        value; remaining values fill the other stats high-to-low by declaration
        order (ADR-143 Step 2). Supersedes the native hint-derivation heuristic."""
        from sidequest.telemetry.spans import Emitter

        ordered = sorted(pool, reverse=True)
        stats: dict[str, int] = {}
        prime = class_def.prime_requisite if class_def is not None else None
        if prime is not None and prime in ability_names:
            stats[prime] = ordered[0]
            rest = ordered[1:]
        else:
            rest = ordered
        for name in ability_names:
            if name == prime:
                continue
            stats[name] = rest.pop(0)
        Emitter.fire(
            f"{self.slug}.chargen.attributes_assigned",
            {"prime": prime, "top": ordered[0], "stats": dict(stats)},
        )
        return stats
```

(Confirm the exact `Emitter`/span-constant pattern against an existing WN span emitter, e.g. `commit_effort`'s span, and match it — register the span name in `telemetry/spans/wn.py` if the slug-parameterized pattern requires it.)

- [ ] **Step 4: Run both nets**

Run: `cd sidequest-server && uv run pytest -n0 tests/game/ruleset/test_143_prime_aware_assignment.py tests/game/ruleset/test_143_chargen_characterization.py -v`
Expected: prime-aware test PASS; the characterization net's `STR == 14` assertion **now needs updating** — that build used a Warrior-default (no class_hint), so confirm whether it still places STR top. Update the net's standard-array assertion to reflect the deliberate Step-2 change (this is the *one* net assertion expected to move; annotate it `# ADR-143 Step 2: prime-aware`).

- [ ] **Step 5: Run the full builder + ruleset suite + lint**

Run: `cd sidequest-server && uv run pytest -n0 tests/game/ tests/server/ -q && uv run ruff check sidequest/game/ruleset sidequest/game/builder.py`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add sidequest/game/ruleset/base.py sidequest/game/ruleset/without_number.py \
  sidequest/game/builder.py sidequest/telemetry/spans/wn.py \
  tests/game/ruleset/test_143_prime_aware_assignment.py tests/game/ruleset/test_143_chargen_characterization.py
git commit -m "feat(ruleset): prime-aware standard-array assignment on WN core (ADR-143 Step 2, fixes Driver 2)"
```

---

## Task 5: `standard_array_arrange` mode — reuse the live picker

**Files:**
- Modify: `sidequest-server/sidequest/game/builder.py`
- Create: `sidequest-server/tests/game/test_standard_array_arrange.py`

- [ ] **Step 1: Write the failing test**

```python
"""standard_array_arrange seeds the arrange pool from the standard array (ADR-143)."""
from __future__ import annotations

import random

from sidequest.game.builder import CharacterBuilder
from sidequest.genre.models.rules import RulesConfig
# build minimal scenes whose first scene declares stat_generation: standard_array_arrange


def test_pool_seeded_from_standard_array():
    rules = RulesConfig.model_validate({
        "ruleset": "wwn", "stat_generation": "standard_array_arrange",
        "standard_array": [14, 12, 11, 10, 9, 7],
        "ability_score_names": ["STR", "DEX", "CON", "INT", "WIS", "CHA"],
        "wwn": {"attribute_map": {"STRENGTH": "STR", "DEXTERITY": "DEX", "CONSTITUTION": "CON",
            "INTELLIGENCE": "INT", "WISDOM": "WIS", "CHARISMA": "CHA"}},
    })
    builder = CharacterBuilder(scenes=_arrange_scenes(), rules=rules, rng=random.Random(1))
    assert sorted(builder.arrangement_pool()) == [7, 9, 10, 11, 12, 14]
```

Run: `cd sidequest-server && uv run pytest -n0 tests/game/test_standard_array_arrange.py -v`
Expected: FAIL — pool is None (mode not handled).

- [ ] **Step 2: Add the seeding method + wire the construction dispatch**

In `builder.py`, add after `_roll_3d6_arrange_visible` (line ~2997):

```python
    def _seed_standard_array_arrange(self) -> None:
        """Seed the arrange pool from the pack's standard array (ADR-143 DD-3).

        Parallel to _roll_3d6_arrange_visible, but the six values are the fixed
        standard array (default [15,14,13,12,10,8] when unset) instead of 3d6
        rolls. The existing arrange picker/handlers/FSM are reused unchanged."""
        base = self._standard_array if self._standard_array is not None else [15, 14, 13, 12, 10, 8]
        self._arrangement_pool = list(base)
        self._arrangement_assignment = {name: None for name in self._ability_score_names}
```

In the `__init__` construction loop (lines 1119-1127), add the branch:

```python
            elif eff.stat_generation == "roll_3d6_arrange_visible":
                self._roll_3d6_arrange_visible()
            elif eff.stat_generation == "standard_array_arrange":
                self._seed_standard_array_arrange()
```

- [ ] **Step 3: Run the test; confirm PASS**

Run: `cd sidequest-server && uv run pytest -n0 tests/game/test_standard_array_arrange.py -v`
Expected: PASS.

- [ ] **Step 4: Verify the picker message renders for the new mode**

`_render_arrangement_message` (builder.py:1806) is pool-generic — confirm a scene with `assignment_required: true` + `stat_generation: standard_array_arrange` reaches it. Add an assertion to the test that `to_scene_message` for that scene yields `input_type == "stat_arrange"` with the seeded pool.

Run: `cd sidequest-server && uv run pytest -n0 tests/game/test_standard_array_arrange.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add sidequest/game/builder.py tests/game/test_standard_array_arrange.py
git commit -m "feat(chargen): standard_array_arrange mode reuses the live arrange picker (ADR-143)"
```

---

## Task 6: UI — `StatArrangePanel` reads ability names from the payload

**Files:**
- Modify: `sidequest-server/sidequest/protocol/messages.py` (add `ability_names` to the stat_arrange payload), `sidequest-server/sidequest/game/builder.py` (`_render_arrangement_message` sets it)
- Modify: `sidequest-ui/src/types/payloads.ts`, `sidequest-ui/src/components/CharacterCreation/CharacterCreation.tsx`, `sidequest-ui/src/components/CharacterCreation/StatArrangePanel.tsx`
- Modify: `sidequest-ui/src/components/CharacterCreation/__tests__/CharacterCreation.test.tsx`

- [ ] **Step 1: Server — add `ability_names` to the arrange payload**

In `messages.py` (the `the_arrangement (server → client)` block ~442), add:

```python
    ability_names: list[str] | None = None
    """Ability-score names in declaration order, for the arrange panel's slots
    (flavor-named packs like elemental_harmony use non-STR/DEX names)."""
```

In `builder.py` `_render_arrangement_message` (1830-1843), set `ability_names=list(self._ability_score_names)` on the payload.

- [ ] **Step 2: UI — failing test (flavor names render)**

In `CharacterCreation.test.tsx`, add a test that a `stat_arrange` scene with `ability_names: ["Strength","Agility","Endurance","Insight","Spirit","Harmony"]` renders slots labeled `Strength`…`Harmony` (query `data-testid="arrange-slot-Strength"`).

Run: `cd sidequest-ui && npx vitest run src/components/CharacterCreation/__tests__/CharacterCreation.test.tsx`
Expected: FAIL — slots use hardcoded STR/DEX.

- [ ] **Step 3: UI — thread the prop**

`payloads.ts` `CharacterCreationPayload`: add `ability_names?: string[];`.
`CharacterCreation.tsx` `CreationScene`: add `ability_names?: string[];`; pass `statOrder={scene.ability_names ?? ["STR","DEX","CON","INT","WIS","CHA"]}` to `StatArrangePanel`.
`StatArrangePanel.tsx`: add `statOrder: string[];` to props; delete the `const STAT_ORDER = [...]` (line 20); replace the `STAT_ORDER.map` (line 73) with `statOrder.map`.

- [ ] **Step 4: Run UI test; confirm PASS**

Run: `cd sidequest-ui && npx vitest run src/components/CharacterCreation/__tests__/CharacterCreation.test.tsx`
Expected: PASS.

- [ ] **Step 5: Server protocol test + commit**

Add/confirm a server test that the arrange payload serializes `ability_names`. Run server + UI lints.

```bash
# server branch
git add sidequest/protocol/messages.py sidequest/game/builder.py
git commit -m "feat(protocol): arrange payload carries ability_names (ADR-143)"
# ui branch
cd ../sidequest-ui && git add src/types/payloads.ts src/components/CharacterCreation/StatArrangePanel.tsx \
  src/components/CharacterCreation/CharacterCreation.tsx src/components/CharacterCreation/__tests__/CharacterCreation.test.tsx
git commit -m "feat(chargen-ui): StatArrangePanel reads ability names from payload (ADR-143)"
```

> **Phase 1 ships here.** Both drivers fixed: attribute mechanics are module-owned (Driver 1), standard-array assignment is prime-aware (Driver 2), the picker is reusable for the standard array, and flavor-named packs arrange correctly. Open server + UI PRs against `develop`.

---

# PHASE 2 — Skills / Foci / Background substrate + content (Steps 3–6)

## Task 7: Skill / Background / Focus models + `Character` fields

**Files:**
- Modify: `sidequest-server/sidequest/genre/models/character.py`
- Create: `sidequest-server/tests/genre/test_skills_foci_background_models.py`

- [ ] **Step 1: Failing model test**

```python
from sidequest.genre.models.character import Background, Focus, FocusLevel


def test_background_grants_skills():
    bg = Background.model_validate({
        "id": "locksmith", "display_name": "Locksmith",
        "free_skill": "Sneak", "quick_skills": ["Convince", "Work"],
    })
    assert bg.free_skill == "Sneak" and "Work" in bg.quick_skills


def test_focus_levels_grant():
    f = Focus.model_validate({
        "id": "die_hard", "display_name": "Die Hard",
        "levels": [{"skills": {"Endure": 1}, "abilities": []}],
    })
    assert f.levels[0].skills["Endure"] == 1
```

Run: `cd sidequest-server && uv run pytest -n0 tests/genre/test_skills_foci_background_models.py -v`
Expected: FAIL — models don't exist.

- [ ] **Step 2: Add the models**

In `character.py`, after `ClassDef` (line ~270):

```python
class Background(BaseModel):
    """A WWN Background: grants a free skill + quick skills at chargen (SRD §1.3)."""

    model_config = {"extra": "forbid"}

    id: str
    display_name: str
    description: str = ""
    free_skill: str | None = None
    quick_skills: list[str] = Field(default_factory=list)


class FocusLevel(BaseModel):
    """One level of a Focus: skill grants + ability grants (SRD §1.5)."""

    model_config = {"extra": "forbid"}

    skills: dict[str, int] = Field(default_factory=dict)
    abilities: list[AbilityDefinition] = Field(default_factory=list)


class Focus(BaseModel):
    """A WWN Focus (feat-like talent), 1-2 levels."""

    model_config = {"extra": "forbid"}

    id: str
    display_name: str
    description: str = ""
    levels: list[FocusLevel] = Field(default_factory=list)
```

- [ ] **Step 3: Add `Character.skills` / `foci`**

Find the `Character` model (in `character.py` or the unified model file) and add:

```python
    skills: dict[str, int] = Field(default_factory=dict)
    foci: list[str] = Field(default_factory=list)
```

Confirm `AbilityDefinition` is importable at the point `FocusLevel` references it (it's already used by `ClassDef.abilities`).

- [ ] **Step 4: Run; confirm PASS + commit**

Run: `cd sidequest-server && uv run pytest -n0 tests/genre/test_skills_foci_background_models.py -v`

```bash
git add sidequest/genre/models/character.py tests/genre/test_skills_foci_background_models.py
git commit -m "feat(models): Skill/Background/Focus models + Character.skills/foci (ADR-143)"
```

---

## Task 8: `MechanicalEffects` grant fields + `AccumulatedChoices` accumulation

**Files:**
- Modify: `sidequest-server/sidequest/genre/models/character.py` (`MechanicalEffects`), `sidequest-server/sidequest/game/builder.py` (`AccumulatedChoices` + `accumulated()`)

- [ ] **Step 1: Failing accumulation test**

In a builder test, author two scenes each granting skills + one selecting a focus; assert `builder.accumulated().skill_grants == {"Sneak": 1, "Work": 1}` and `focus_id`/`foci` accumulates.

Run the test; Expected: FAIL.

- [ ] **Step 2: Extend `MechanicalEffects`**

In `character.py` `MechanicalEffects` (line 98), add alongside `stat_bonuses`:

```python
    skill_grants: dict[str, int] = Field(default_factory=dict)
    focus_id: str | None = None
```

- [ ] **Step 3: Extend `AccumulatedChoices` + `accumulated()`**

In `builder.py`, add to `AccumulatedChoices` (after line 516):

```python
    skill_grants: dict[str, int] = field(default_factory=dict)
    foci: list[str] = field(default_factory=list)
```

In `accumulated()` after the `stat_bonuses` loop (line ~1584):

```python
        for skill, lvl in eff.skill_grants.items():
            acc.skill_grants[skill] = max(acc.skill_grants.get(skill, 0), lvl)
        if eff.focus_id is not None and eff.focus_id not in acc.foci:
            acc.foci.append(eff.focus_id)
```

(WWN skills take the *higher* of stacking grants, not additive — note vs `stat_bonuses` which is additive.)

- [ ] **Step 4: Run; PASS + commit**

```bash
git add sidequest/genre/models/character.py sidequest/game/builder.py tests/game/test_builder*.py
git commit -m "feat(chargen): MechanicalEffects skill_grants/focus_id + accumulator (ADR-143)"
```

---

## Task 9: Loader — load `skills.yaml` / `backgrounds.yaml` / `foci.yaml` + resolvers

**Files:**
- Modify: the genre-pack loader (`sidequest/genre/` loader + `GenrePack` model) and `sidequest/handlers/connect.py`
- Create: loader test

- [ ] **Step 1: Failing loader test**

Construct a synthetic pack dir with `backgrounds.yaml` + `foci.yaml`; assert `genre_pack.backgrounds["locksmith"].free_skill == "Sneak"` and `genre_pack.foci["die_hard"].levels[0].skills == {"Endure": 1}`. Mirror the existing `classes.yaml` loader test shape.

Run; Expected: FAIL.

- [ ] **Step 2: Add `GenrePack` fields + loader reads**

Add `backgrounds: dict[str, Background]` and `foci: dict[str, Focus]` to `GenrePack` (and a `skills: list[str]` catalog if the loader validates skill ids). In the loader, read `backgrounds.yaml`/`foci.yaml`/`skills.yaml` if present (absent = empty dict, **not** a silent fallback — empty is the legitimate "pack authors none" state). Follow the exact pattern the loader uses for `classes.yaml`.

- [ ] **Step 3: Add `resolve_backgrounds` / `resolve_foci` (world-first)**

Mirror `resolve_classes(genre_pack, world_slug)` (used at connect.py:936) so a world can override/extend the genre roster (heavy_metal/elemental_harmony are world-tier).

- [ ] **Step 4: Pass resolved defs into the builder**

In `connect.py` (after line 938), attach to the builder via a fluent setter `with_chargen_defs(backgrounds=..., foci=...)` (add the setter on `CharacterBuilder` storing `self._backgrounds`/`self._foci`).

- [ ] **Step 5: Run; PASS + commit**

```bash
git add sidequest/genre/ sidequest/handlers/connect.py sidequest/game/builder.py tests/genre/
git commit -m "feat(loader): load backgrounds.yaml/foci.yaml/skills.yaml + world-first resolvers (ADR-143)"
```

---

## Task 10: Contribution methods compute real grants + `build()` applies them

**Files:**
- Modify: `sidequest-server/sidequest/game/ruleset/base.py` (defaults), `sidequest-server/sidequest/game/ruleset/without_number.py` (overrides), `sidequest-server/sidequest/game/builder.py` (`build()` application)

- [ ] **Step 1: Failing test**

Build a synthetic WWN pack with a background granting `Sneak` and a focus granting `Endure 1`; assert the built `Character.skills == {"Sneak": 1, "Endure": 1}` and `Character.foci == ["die_hard"]`, and that `{slug}.chargen.background_skills` + `{slug}.chargen.foci_applied` spans fire.

Run; Expected: FAIL.

- [ ] **Step 2: ABC defaults**

In `base.py`:

```python
    def contribute_background_skills(self, *, background_def, rng):
        """Background → skill-level dict. Default: none. WN-core reads the def."""
        return {}

    def contribute_foci(self, *, focus_defs):
        """Foci → skills + abilities. Default: none. WN-core reads the defs."""
        from sidequest.game.chargen_contribution import FociContribution

        return FociContribution()
```

- [ ] **Step 3: WN-core overrides**

In `without_number.py`:

```python
    def contribute_background_skills(self, *, background_def, rng):
        from sidequest.telemetry.spans import Emitter

        if background_def is None:
            return {}
        grants: dict[str, int] = {}
        if background_def.free_skill:
            grants[background_def.free_skill] = max(grants.get(background_def.free_skill, 0), 0)
        for s in background_def.quick_skills:
            grants[s] = max(grants.get(s, 0), 0)
        Emitter.fire(f"{self.slug}.chargen.background_skills",
                     {"background": background_def.id, "skills": dict(grants)})
        return grants

    def contribute_foci(self, *, focus_defs):
        from sidequest.game.chargen_contribution import FociContribution
        from sidequest.telemetry.spans import Emitter

        skills: dict[str, int] = {}
        abilities = []
        for f in focus_defs:
            for lvl in f.levels[:1]:  # chargen grants level 1 only
                for sk, n in lvl.skills.items():
                    skills[sk] = max(skills.get(sk, 0), n)
                abilities.extend(lvl.abilities)
        Emitter.fire("chargen.foci_applied", {"foci": [f.id for f in focus_defs], "skills": dict(skills)})
        return FociContribution(skills=skills, abilities=abilities)
```

(WWN: a level-0 skill is value 0; trained = 1. Confirm the skill-level convention against the SRD when authoring; the model stores ints.)

- [ ] **Step 4: `build()` applies grants**

In `build()` after stats/resources (after line 2839), resolve the chosen `Background`/`Focus` defs from `acc.background`/`acc.foci` against `self._backgrounds`/`self._foci`, call the module, merge into a `skills` dict (background ∪ foci ∪ `acc.skill_grants`), and pass `skills=skills, foci=acc.foci` to the `Character(...)` constructor (lines 2937+). Append focus abilities to the `abilities` list already assembled.

- [ ] **Step 5: Run the wiring test (end-to-end)**

Create `tests/game/test_chargen_seam_wiring.py`: synthetic WWN pack → real `CharacterBuilder.build()` → assert prime placement + skills + foci + spans. This is the **required wiring test** (fixture-driven, not source-grep).

Run: `cd sidequest-server && uv run pytest -n0 tests/game/test_chargen_seam_wiring.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add sidequest/game/ruleset/base.py sidequest/game/ruleset/without_number.py \
  sidequest/game/builder.py tests/game/test_chargen_seam_wiring.py
git commit -m "feat(chargen): WN-core background/foci contribution + build() application (ADR-143)"
```

---

## Task 11: Character sheet surfaces skills + foci

**Files:**
- Modify: `sidequest-server/sidequest/server/websocket_handlers/chargen_mixin.py` (and wherever `members[].sheet` is assembled) to include `skills`/`foci`
- Modify: `sidequest-ui/src/components/CharacterSheet.tsx`
- Modify: `sidequest-ui/src/components/__tests__/` (sheet test)

- [ ] **Step 1: Server — include skills/foci in the sheet dict**

Find where `sheet` is built for PARTY_STATUS members (grep `"sheet"` / `CharacterSheetData` assembly) and add `"skills": character.skills, "foci": character.foci`.

- [ ] **Step 2: UI — failing sheet test**

Add a test that a `CharacterSheetData` with `skills: {Sneak: 1}` + `foci: ["Die Hard"]` renders a Skills section and a Foci section.

Run: `cd sidequest-ui && npx vitest run` (the sheet test); Expected: FAIL.

- [ ] **Step 3: UI — add the sections + types**

`CharacterSheet.tsx`: add `skills?: Record<string, number>;` + `foci?: string[];` to `CharacterSheetData` (lines 25-99); after the Stats grid (line 171) add conditional Skills + Foci sections using the same grid/list pattern.

- [ ] **Step 4: Run; PASS + commit (both repos)**

```bash
# server
git add sidequest/server/websocket_handlers/chargen_mixin.py
git commit -m "feat(chargen): skills/foci on PARTY_STATUS sheet (ADR-143)"
# ui
cd ../sidequest-ui && git add src/components/CharacterSheet.tsx src/components/__tests__/
git commit -m "feat(sheet): render skills + foci sections (ADR-143)"
```

---

## Task 12: Real WWN content — skills / backgrounds / foci + chargen scenes

Author **real** WWN content for the three packs so a created character lands on the sheet with skills + a focus from play data. The schema below is the contract; author one full set per pack. (Content authoring across packs is repetitive by nature — the worked example is complete; replicate the *schema*, author pack-true *content*.)

**Files (per pack — `genre_packs/{caverns_and_claudes,heavy_metal,elemental_harmony}/`):**
- Create: `skills.yaml`, `backgrounds.yaml`, `foci.yaml`
- Modify: chargen scenes — C&C genre-tier `char_creation.yaml`; heavy_metal world-tier (`worlds/{barsoom,evropi,long_foundry}/char_creation.yaml`); elemental_harmony world-tier (`worlds/{burning_peace,shattered_accord}/char_creation.yaml`)

- [ ] **Step 1: Author `skills.yaml` (the WWN skill list)**

Example (`caverns_and_claudes/skills.yaml`) — the WWN skill catalog (SRD §1.6):

```yaml
skills:
  - Administer
  - Connect
  - Convince
  - Craft
  - Exert
  - Heal
  - Know
  - Lead
  - Magic
  - Notice
  - Perform
  - Pray
  - Punch
  - Ride
  - Sail
  - Shoot
  - Sneak
  - Stab
  - Survive
  - Trade
  - Work
```

- [ ] **Step 2: Author `backgrounds.yaml`**

Example entry (matches the `Background` model):

```yaml
backgrounds:
  - id: thief
    display_name: Thief
    description: You learned your trade in the dark, where locks and pockets were the only honest teachers.
    free_skill: Sneak
    quick_skills: [Sneak, Stab, Notice]
```

For heavy_metal/evropi, author definitions for the **existing** ID strings already in chargen (`Zkęd-Frontier`, `Aldkin-Rider`, …) so they resolve to real grants.

- [ ] **Step 3: Author `foci.yaml`**

Example entry (matches `Focus`/`FocusLevel`):

```yaml
foci:
  - id: die_hard
    display_name: Die Hard
    description: You are preternaturally hard to kill.
    levels:
      - skills: {Exert: 0}
        abilities:
          - name: Die Hard
            genre_description: Death takes a long look at you and decides to wait.
            mechanical_effect: "+2 max HP and +2 to rolls to stabilize when dying."
            involuntary: false
```

- [ ] **Step 4: Wire a chargen choice that grants a focus/skills**

C&C genre-tier — add a scene after `the_calling` in `char_creation.yaml`:

```yaml
- id: the_trade
  title: "Your Trade Before the Rope"
  narration: |
    Before Brecca's ledger claimed you, you had a trade. The hands remember.
  choices:
    - label: "Locksmith"
      description: "Tumblers and tension wrenches; doors were only ever suggestions."
      mechanical_effects:
        background: thief
        focus_id: die_hard
        skill_grants: {Sneak: 1}
  allows_freeform: false
```

For heavy_metal/elemental_harmony, fold `focus_id`/`skill_grants` into the existing world-tier `origins`/`path` choices (e.g. Evrópí's `origins` choices already carry `background:` IDs — add `focus_id`/`skill_grants` there).

- [ ] **Step 5: Validate content loads**

Run the pack validator (not unit tests — content invariants live in the validator per `feedback_no_content_in_unit_tests`):

Run: `cd sidequest-server && uv run python -m sidequest.cli.validate --pack caverns_and_claudes --pack heavy_metal --pack elemental_harmony`
Expected: all packs load; backgrounds/foci/skills resolve; no unmatched `focus_id`.

- [ ] **Step 6: Commit (content repo)**

```bash
cd sidequest-content && git add genre_packs/caverns_and_claudes genre_packs/heavy_metal genre_packs/elemental_harmony
git commit -m "content(wwn): skills/backgrounds/foci + chargen wiring for the 3 WWN packs (ADR-143)"
```

---

## Task 13: Pack validator coverage + full integration sweep

**Files:**
- Modify: the pack validator (`sidequest/cli/validate` or the content validator) to assert: every `focus_id`/`background` referenced in chargen resolves to a def; every `skill_grants`/`Background.free_skill`/`FocusLevel.skills` key is in the pack's `skills.yaml` catalog (fail loud on a typo'd skill).

- [ ] **Step 1: Add validator rules**

Add the cross-reference checks above. A referenced focus/background/skill that doesn't resolve is a **loud** validation error (No Silent Fallbacks).

- [ ] **Step 2: Run validator across all packs**

Run: `cd sidequest-server && uv run python -m sidequest.cli.validate --all`
Expected: PASS (the 3 WWN packs resolve; non-WWN packs unaffected — they author no skills/foci).

- [ ] **Step 3: Full gate**

Run: `cd sidequest-server && uv run pytest -n0 tests/game tests/genre tests/server -q && uv run ruff check . && cd ../sidequest-ui && npx vitest run`
Expected: PASS.

- [ ] **Step 4: Commit + open Phase 2 PRs**

```bash
git add sidequest/cli/validate*
git commit -m "feat(validate): cross-reference foci/backgrounds/skills in chargen (ADR-143)"
```

Open server / ui / content PRs against `develop`.

---

## Self-Review

**Spec coverage:**
- 5-method surface declared on ABC → Tasks 2, 3, 4, 10 (all five: `generate_attributes`, `assign_attributes`, `seed_chargen_resources`, `contribute_background_skills`, `contribute_foci`). ✓
- Driver 1 (attribute-gen ruleset-owned) → Tasks 2, 3. ✓
- Driver 2 (prime-aware) → Task 4. ✓
- Substrate (skills/Background/Focus + Character fields) → Tasks 7, 8. ✓
- Loader → Task 9. ✓
- Arrange reuse + STAT_ORDER → Tasks 5, 6. ✓
- Sheet surfacing → Task 11. ✓
- Real WWN content → Task 12. ✓
- Validator/wiring tests → Tasks 10 (wiring), 13. ✓
- Behavior-preserving two-step net → Tasks 1, 3 (byte-identical), 4 (the one change). ✓
- Out of scope (lethality tuning, full focus catalog, SWN/CWN/AWN libraries, Fate Core) — not tasked. ✓

**Placeholder scan:** Content Task 12 gives complete worked examples per file type; "author pack-true content" is content work, not an engine placeholder. No `TODO`/`TBD` in engine steps.

**Type consistency:** `ChargenResources(effort, spellcasting, system_strain)`, `FociContribution(skills, abilities)`, `Background(free_skill, quick_skills)`, `Focus(levels=[FocusLevel(skills, abilities)])`, `MechanicalEffects.skill_grants`/`focus_id`, `AccumulatedChoices.skill_grants`/`foci`, `Character.skills`/`foci` — names consistent across Tasks 2/7/8/10/11. `assign_attributes(pool, ability_names, class_def, acc=None)` signature consistent Tasks 3/4. ✓

**Known follow-up to confirm during execution (not placeholders):** the exact `Emitter`/span-constant registration pattern (match an existing WN emitter); the precise `Character` constructor field list when adding `skills`/`foci` (Task 7 Step 3 / Task 10 Step 4); the WWN skill-level integer convention (0 = level-0/trained-at-0 vs 1) when authoring content.
