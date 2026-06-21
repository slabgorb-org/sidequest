---
story_id: "153-34"
jira_key: ""
epic: "153"
workflow: "tdd"
---
# Story 153-34: [WN-POINTBUY-DEAD-CONFIG] migrate the 4 WN point-buy packs to standard_array + size-validate the WN default spread against ability count (fail loud at load, not a chargen-time IndexError) — 153-4 review follow-up

## Story Details
- **ID:** 153-34
- **Jira Key:** (no Jira integration)
- **Workflow:** tdd
- **Stack Parent:** none
- **Type:** chore
- **Points:** 2
- **Priority:** p3

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-21T18:35:46Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-21T18:01:19Z | 2026-06-21T18:05:09Z | 3m 50s |
| red | 2026-06-21T18:05:09Z | 2026-06-21T18:18:44Z | 13m 35s |
| green | 2026-06-21T18:18:44Z | 2026-06-21T18:28:41Z | 9m 57s |
| review | 2026-06-21T18:28:41Z | 2026-06-21T18:35:46Z | 7m 5s |
| finish | 2026-06-21T18:35:46Z | - | - |

## Story Context

This is a direct 153-4 review follow-up (Reviewer findings, lines 84-101 of 153-4-session.md). The 153-4 fix silently supersedes `stat_generation: point_buy` in WN packs by hardwiring the shaped SRD `[14,12,11,10,9,7]` spread. This story addresses two non-blocking improvements flagged by the Reviewer:

### Scope Item 1 — Migrate dead `point_buy` config to `standard_array` (CONTENT repo)

The four WN point-buy packs currently author:
```yaml
stat_generation: point_buy
point_buy_budget: 27
```

This config is now DEAD — the `WithoutNumberRulesetModule._generate_attribute_values` override in 153-4 silently ignores the budget and yields the fixed spread. The authoring surface lies: content authors tuning `point_buy_budget` see no effect.

**Migration target:** Replace `stat_generation: point_buy` + `point_buy_budget: 27` with:
```yaml
stat_generation: standard_array
standard_array: [14, 12, 11, 10, 9, 7]
```

**Files to update (4 WN packs only):**
1. `sidequest-content/genre_packs/space_opera/rules.yaml` (SWN, lines 1-2)
2. `sidequest-content/genre_packs/mutant_wasteland/rules.yaml` (AWN, lines 34-35)
3. `sidequest-content/genre_packs/neon_dystopia/rules.yaml` (CWN, lines 1-2)
4. `sidequest-content/genre_packs/road_warrior/rules.yaml` (CWN, lines 10-11)

**GOTCHA:** A bare `grep point_buy` matches `spaghetti_western/rules.yaml`, but spaghetti_western is a **Fate** pack (ADR-144), NOT WN-family. It must remain untouched.

### Scope Item 2 — Size-validate the WN default spread at load (SERVER repo)

File: `sidequest-server/sidequest/game/ruleset/without_number.py`

The module-level `_WN_STANDARD_ARRAY = [14,12,11,10,9,7]` is a hardcoded 6-element default. It is **NOT validated** against a pack's ability-score count. A future WN pack declaring ≠6 abilities AND omitting an authored `standard_array` would fall back to this 6-element default and then crash with `IndexError` deep in `assign_attributes` at chargen time — a player-facing crash with an opaque traceback.

**Fix:** Add a LOAD-TIME size validation so mismatched defaults fail loud at pack-load, not at chargen. Mirror the existing `RulesConfig._validate_standard_array` validator (which validates *authored* `standard_array` against ability count) so the default-spread path is subject to the same length check.

### Acceptance Criteria
- The 4 WN packs author `stat_generation: standard_array` with explicit `standard_array: [14, 12, 11, 10, 9, 7]`; the dead `point_buy_budget` field is removed.
- `spaghetti_western` (Fate) is untouched.
- Loading a WN pack with ability-score count ≠ 6 (and no authored `standard_array`) raises a loud, descriptive error AT LOAD, not an `IndexError` at chargen.
- All current WN packs (6 abilities) still load and generate the shaped `[14,12,11,10,9,7]` spread unchanged — no behavioral regression.
- Existing chargen/ruleset/WN-integration test suites remain green.

## Sm Assessment

**Setup complete — routing to TEA (RED).** Phased `tdd` workflow (explicit YAML field; type=chore/2pts but workflow tag wins over the points fallback). Repos: `server,content`. Branch `feat/153-34-wn-pointbuy-standard-array` created off `develop` in both subrepos. No Jira (integration absent). Merge gate clear — the one open server PR (#1024, dungeon seam) is a standalone playtest/FIXER fix, not a tracked sprint-story PR, and `pf sprint work 153-34` reported Available.

**Scope is tightly bounded by the 153-4 review** (`sprint/archive/153-4-session.md`, Reviewer findings ~L84-101 / L314-335): two independent items — (1) content-side config migration of 4 WN packs, (2) server-side load-time size validation of `_WN_STANDARD_ARRAY`. Both are non-blocking improvements the 153-4 Reviewer explicitly deferred to a follow-up, now this story.

**Load-bearing gotcha for TEA/Dev:** a bare `grep point_buy` sweeps in `spaghetti_western/rules.yaml`, which is a **Fate** pack (ADR-144), NOT WN — it is out of scope and must stay untouched. The 4 in-scope WN packs are confirmed: space_opera (swn), mutant_wasteland (awn), neon_dystopia (cwn), road_warrior (cwn), all `point_buy_budget: 27`.

**TEA focus:** RED tests should (a) drive a load-time failure for a WN pack with ability-count ≠ 6 that omits `standard_array` (assert loud load error, not a chargen `IndexError`), and (b) lock the 4-pack migration to `standard_array` while proving no spread regression for the existing 6-ability packs. Mirror the existing `RulesConfig._validate_standard_array` pattern.

No blockers. No ADR change required (this honors ADR-142/143 — it removes dead config, doesn't add a native mechanic).

## TEA Assessment

**Tests Required:** Yes
**Reason:** n/a — behavioral contracts for both scope items are testable without Claude calls.

**Test Files:**
- `sidequest-server/tests/game/ruleset/test_153_34_wn_default_spread_validation.py` — scope item 2 (load-time size-validation of the WN default spread).
- `sidequest-server/tests/integration/test_153_34_wn_pointbuy_migration.py` — scope item 1 (content migration of the 4 WN packs) + no-regression wiring.

**Tests Written:** 11 tests (8 RED, 3 GREEN guards) covering both ACs.
**Status:** RED — verified `8 failed, 3 passed` via `uv run pytest -n0` (0.61s, no DB).

**Bug reproduced before writing** (test-paranoia): a `wwn` config with 7 abilities,
`point_buy`, no authored `standard_array` constructs cleanly today, then
`generate_attributes` raises `IndexError: pop from empty list` for BOTH the
`point_buy` and `standard_array` methods. That confirms the gap is real and that
the failure is currently a deep opaque chargen crash, not a loud load error.

**Test design — load-time seam (scope 2):** the RED tests assert the loud failure at
`RulesConfig` construction (the pydantic model-validation step that runs when a pack's
`rules.yaml` is loaded), mirroring the sibling `RulesConfig._validate_standard_array`.
This is the truest "fail loud at load" seam and the one the 153-4 Reviewer named. Dev
must place the new validation where it runs during `RulesConfig` construction (a
`model_validator`), not solely in `without_number.py`'s chargen path — see the deviation
note. The default length is 6 for BOTH `_WN_STANDARD_ARRAY` and the base
`_DEFAULT_STANDARD_ARRAY`, so a single well-placed `standard_array is None && ability
count > default length` check satisfies both RED method-path tests at once.

**Negative guards (must stay GREEN through the fix):** 6-ability default loads + generates
the shaped spread; 7-ability-WITH-authored-7-array loads fine; spaghetti_western (Fate)
untouched. These pin the blast radius so the fix can't over-reject legitimate configs or
sweep in the Fate pack.

### Rule Coverage

| Rule (python.md) | Test(s) | Status |
|------|---------|--------|
| #1 No Silent Fallbacks (fail loud, not silent default→IndexError) | `test_undersized_wn_default_spread_raises_at_load_point_buy`, `..._standard_array_method`, `test_undersized_failure_is_not_a_chargen_indexerror` | failing (RED) |
| #3 Type annotations at boundaries | all test fns `-> None`; `_wwn_rules`/`_load_rules_yaml` annotated | passing |
| #6 Test quality (meaningful assertions, no vacuous asserts) | every test asserts specific values/types; self-checked | passing |
| #8 Unsafe deserialization (`yaml.safe_load`, never `yaml.load`) | `_load_rules_yaml` uses `yaml.safe_load` | passing |

**Rules checked:** 4 of 4 applicable lang-review rules have coverage (the rest — mutable
defaults, logging, path handling, resource leaks — are N/A for these test-only changes).
**Self-check:** 0 vacuous tests (no `assert True`, no bare-truthy-where-value-matters, no
`let _ =` equivalent); the 3 negative guards assert concrete pool contents, not truthiness.

**Handoff:** To Dev (Agent Smith) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-server/sidequest/genre/models/rules.py` — new `RulesConfig._validate_default_spread_covers_abilities` `model_validator` + `_WITHOUT_NUMBER_RULESETS` constant. Fails loud at load when a pack authors no `standard_array` but its effective fixed-length default spread (`_WN_STANDARD_ARRAY` for WN `point_buy`, base `_DEFAULT_STANDARD_ARRAY` for the `standard_array` method) can't cover every declared ability score. Local import of the two default constants mirrors the loader's cycle-avoidance pattern.
- `sidequest-content/genre_packs/{space_opera,mutant_wasteland,neon_dystopia,road_warrior}/rules.yaml` — migrated dead `stat_generation: point_buy` + `point_buy_budget: 27` → `stat_generation: standard_array` + `standard_array: [14, 12, 11, 10, 9, 7]` (with an explanatory comment). spaghetti_western (Fate) untouched.

**Tests:** 11/11 story tests passing (GREEN). Regression: `641 passed` across `tests/game/ruleset/` + builder stat/walk + standard-array-arrange + the 153-4 chargen wiring test; all 11 live packs load clean through the real loader.

**Pre-existing failures (NOT this story):** 4 `tests/genre/` tests fail (`test_premise_loader` ×2, `test_beneath_sunden_room_binding_107_2`, `test_wwn_spell_catalog_load::test_non_wwn_pack_with_spells_file_does_not_load_catalog`) — confirmed identical failures with my changes stashed. They are missing-fate-SRD-reference-content / clone-state issues unrelated to stat_generation; flagged here so the Reviewer isn't surprised.

**Quality gates:** `ruff check` clean, `ruff format` clean, `pyright` 0 errors on the changed module.
**Branch:** `feat/153-34-wn-pointbuy-standard-array` (server `6cc093c5`, content `3bf4835`) — both pushed.

**Handoff:** To verify (The Architect) / Reviewer.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | success | 0 actionable (2 pytest.skip content-guards are appropriate) | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — self-analyzed, see [EDGE] |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — self-analyzed, see [SILENT] |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — self-analyzed, see [TEST] |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — self-analyzed, see [DOC] |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — self-analyzed, see [TYPE] |
| 7 | reviewer-security | Yes | clean | 0 | confirmed 0, dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — self-analyzed, see [SIMPLE] |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — self-analyzed, see [RULE] |

**All received:** Yes (2 enabled returned clean/green; 7 disabled via `workflow.reviewer_subagents`, their domains analyzed by the Reviewer directly)
**Total findings:** 0 confirmed blocking, 1 LOW non-blocking observation (logged as Delivery Finding), 0 dismissed

- **reviewer-preflight (success):** story suite 11/11 GREEN; regression 635 passed; ruff check/format + pyright all clean; all 11 live packs load through the real loader; only the 4 Dev-reported baseline reds (`test_premise_loader` ×2, `test_beneath_sunden_room_binding_107_2`, `test_wwn_spell_catalog_load`), none attributable to this diff.
- **reviewer-security (clean):** 5 rules checked, 0 violations — fail-loud (no except/swallow), safe hard-coded local imports (ImportError would propagate loudly), no player-input construction path (RulesConfig built only from `yaml.safe_load` of pack files), no injection/leakage in the ValueError message (display-only config strings).

## Reviewer Assessment

**Verdict:** APPROVED

You come to me with a validator and four migrated packs. I traced every cause to every effect — the why holds.

**Data flow traced:** pack `rules.yaml` → `load_genre_pack` → `yaml.safe_load` → `RulesConfig.model_validate` → `_validate_default_spread_covers_abilities` runs at construction (`rules.py:1376`). When `standard_array is None` AND the effective fixed-length default spread (`_WN_STANDARD_ARRAY` for WN `point_buy`; base `_DEFAULT_STANDARD_ARRAY` for the `standard_array` method) is shorter than `len(ability_score_names)`, it raises a descriptive `ValueError` — the pack fails to load LOUDLY. Safe because the failure is moved from a deep, opaque chargen-time `IndexError: pop from empty list` (`assign_attributes`, `rest.pop(0)` on the over-count) to an actionable load-time config error naming the count and the fix. No player/WebSocket input reaches this path (confirmed [SEC]).

**Observations (7):**
1. `[VERIFIED]` No-Silent-Fallbacks compliance — the validator RAISES on the one bad-config branch with no `try/except`/swallow anywhere; the early-returns are genuinely-safe conditions (authored array already length-checked by `_validate_standard_array`; empty abilities; generative methods). Evidence: `rules.py:1411-1416` raise, no except in method. Corroborated by `[SILENT]` + `[SEC]` clean.
2. `[VERIFIED]` `[EDGE]` No missed underflow path — I enumerated EVERY `stat_generation` method in `base._generate_attribute_values` (`base.py:311-345`): `roll_3d6_strict` / `roll_the_bones` return one value per ability (no underflow); base `point_buy` → `_allocate_point_buy(len(ability_names), budget)` (per-ability); `standard_array` → authored OR `_DEFAULT_STANDARD_ARRAY`; `else` → `UnknownStatGenerationError` (loud). Only `standard_array` (any ruleset) and WN-overridden `point_buy` (`without_number.py:791`) use a fixed default — the validator covers exactly those two. No `standard_array_arrange` stat-gen method exists (grep across packs: the only authored value is `standard_array`). No gap.
3. `[VERIFIED]` The validator's chosen default mirrors the RUNTIME default for each (ruleset, method): WN+`point_buy`→`_WN_STANDARD_ARRAY`; `*`+`standard_array`→`_DEFAULT_STANDARD_ARRAY` (the WN override passes `standard_array` through to base, so base default is correct even for a WN pack). The threshold uses `len(default_spread)` dynamically — not a hardcoded `6` — so it self-tracks if either constant changes. Evidence: `rules.py:1401-1409`.
4. `[VERIFIED]` `[TEST]` Test quality — story tests assert concrete values (pool contents, exact spreads) and descriptive message tokens, not truthiness; negative guards (6-ability default, 7-ability+authored-array, Fate untouched) pin the blast radius; `test_undersized_failure_is_not_a_chargen_indexerror` is a real regression tripwire (an uncaught `IndexError` would fail `pytest.raises(ValueError)`). Content test uses `yaml.safe_load`.
5. `[VERIFIED]` Migration consistency — all four packs author 6 abilities + a 6-value `standard_array [14,12,11,10,9,7]`, drop `point_buy_budget`; all 11 packs load; `spaghetti_western` (Fate) untouched with a dedicated tripwire. Evidence: per-pack yq check + `[preflight]` 11/11 load.
6. `[VERIFIED]` `[TYPE]`/`[SIMPLE]`/`[DOC]` — returns `-> RulesConfig`; `_WITHOUT_NUMBER_RULESETS` is an immutable `frozenset`; ~30 lines of necessary two-branch logic (defaults differ by ruleset×method), not over-engineered; docstring + comments accurate. pyright 0 errors.
7. `[LOW]` `[RULE]` `_WITHOUT_NUMBER_RULESETS = {"swn","cwn","wwn","awn"}` is a hardcoded family set — a future WN sibling ruleset would need adding here too, or its `point_buy` underflow guard silently won't fire. Non-blocking: it's consistent with the file's existing per-slug checks (`_validate_swn`/`_cwn`/`_wwn`/`_awn` each hardcode their slug), all current WN siblings are present, and the `point_buy` path is itself being retired by this migration. Logged as a non-blocking Delivery Finding.

**Error handling:** the one failure mode (under-covered default) now raises at load with a fix-naming message (`rules.py:1411-1416`); a broken local import would propagate as a loud `ImportError` at pack load (no masking). On empty `ability_score_names` (Fate, `RulesConfig()` defaults, `ruleset="nonsense"`) the validator early-returns — preserving `test_loader_binding::test_unknown_ruleset_rejected_at_bind` (it never calls the registry, so construction can't raise `UnknownRulesetError`).

### Rule Compliance (lang-review python.md, exhaustive over the diff)

| Rule | Instances in diff | Verdict |
|------|-------------------|---------|
| #1 Silent exception swallowing | `_validate_default_spread_covers_abilities` (1 method) | COMPLIANT — raises, no `except`/`suppress`/`pass`; early-returns are safe conditions, not error-masking |
| #2 Mutable default arguments | `_WITHOUT_NUMBER_RULESETS` (module const), validator (no params) | COMPLIANT — `frozenset` is immutable; no function has a mutable default |
| #3 Type annotations at boundaries | validator signature; constant | COMPLIANT — `-> RulesConfig`; `frozenset[str]` annotated |
| #4 Logging coverage/correctness | n/a (no logging added) | N/A — validation raises, doesn't log |
| #5 Path handling | n/a | N/A — no filesystem paths |
| #6 Test quality | 11 tests across 2 files | COMPLIANT — concrete assertions, no vacuous `assert True`, no always-None checks |
| #7 Resource leaks | n/a | N/A — no file/socket/lock |
| #8 Unsafe deserialization | content test loads rules.yaml | COMPLIANT — `yaml.safe_load`; validator does no deserialization |

### Devil's Advocate

Let me argue this is broken. **First, the hardcoded family set.** `_WITHOUT_NUMBER_RULESETS` is a literal `{"swn","cwn","wwn","awn"}`. The day someone registers a fifth WN sibling — say a hypothetical "nwn" — and ships a pack binding it with `point_buy` and seven abilities and no `standard_array`, this validator silently skips the `point_buy` branch (the slug isn't in the set), the elif misses (`point_buy != standard_array`), the else returns `self`, the pack loads "fine," and a player crashes at chargen with the exact `IndexError` this story set out to kill. That is a real future regression vector — mitigated only by the fact that the same hardcoded-slug pattern pervades `rules.py` and a new sibling already requires a `_validate_*wn` companion, so the omission would be glaring. I logged it LOW, not blocking. **Second, method-string fragility.** The branches match `"point_buy"` / `"standard_array"` by exact string. An author who writes `Point_Buy`, `standard array`, or `point_buy ` (trailing space) sidesteps the validator entirely. But I traced that to a loud end: a non-matching method reaches `base._generate_attribute_values`' `else` and raises `UnknownStatGenerationError` at chargen — loud, not silent — so the worst case is "loud later" not "silent crash," and not a No-Silent-Fallbacks violation. **Third, validator ordering.** This runs before `_validate_cwn`/`_wwn`/`_awn`, so for a WN pack with BOTH a malformed `attribute_map` AND an under-covered default, the spread error masks the attribute_map error; the author fixes one, reloads, sees the next — annoying, not incorrect. **Fourth, circular import at first construction.** The local import of two private constants could, in principle, fault if `game.ruleset` weren't importable when the first `RulesConfig` is built. It is — the loader constructs configs after the ruleset package is importable, and preflight's 11/11 pack load + 635-test regression exercise this exact path with zero import faults. **Fifth, a confused content author** migrating a fifth WN pack copies `[14,12,11,10,9,7]` but their pack has seven abilities: now `_validate_standard_array` (the sibling) fires `"no silent padding"` at load — the intended safety net catches them. None of these rise to High; the one with teeth (the family set) is a maintenance footgun, surfaced as a finding.

**Pattern observed:** the validator faithfully mirrors its sibling `_validate_standard_array` (`rules.py:1350`) — same `model_validator(mode="after")` shape, same "no silent padding" loud-fail idiom, same field set — which is exactly the "mirror the existing validator" the 153-4 review asked for.

**Handoff:** To SM (Morpheus) for finish-story.

## Delivery Findings

No upstream findings.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- TEA's base-`_DEFAULT_STANDARD_ARRAY` finding is **RESOLVED** by this implementation: the new validator gates the `standard_array` method for ALL rulesets (not WN-only), so the identical base-default gap is closed by the same check. No new upstream findings during implementation.

### TEA (test design)
- **Improvement** (non-blocking): the base `_DEFAULT_STANDARD_ARRAY` (`[15,14,13,12,10,8]`, 6 elements) carries the IDENTICAL unvalidated-default gap as the WN default — any pack (not just WN) with ≠6 abilities, a default-spread method, and no authored `standard_array` IndexErrors at chargen. Affects `sidequest-server/sidequest/game/ruleset/base.py` (`_DEFAULT_STANDARD_ARRAY`) + the load-time validator (a single ruleset-agnostic "default spread must cover ability count" check covers both defaults). *Found by TEA during test design.*

### Reviewer (code review)
- **Improvement** (non-blocking): `_WITHOUT_NUMBER_RULESETS` in `rules.py` is a hardcoded `{"swn","cwn","wwn","awn"}` set — a future WN sibling ruleset would need adding here too, or its `point_buy` under-covered-default guard silently won't fire (re-opening the chargen `IndexError` for that sibling). Affects `sidequest-server/sidequest/genre/models/rules.py` (`_WITHOUT_NUMBER_RULESETS` — consider deriving WN-family membership from the ruleset registry / `WithoutNumberRulesetModule` isinstance check if a fifth sibling is ever added). Low severity: consistent with the file's existing per-slug validators (`_validate_swn`/`_cwn`/`_wwn`/`_awn`), all current siblings are present, and the `point_buy` path is itself being retired by this story's migration. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

3 deviations

- **Load-time failure asserted at the `RulesConfig` model-validation seam, not the WN module bind**
  - Rationale: `rules.yaml` → `RulesConfig` IS the pack-load validation step, and the sibling validator the spec names to mirror lives there; a module-only check that doesn't run at construction would leave the IndexError latent until chargen, defeating the "at load" AC.
  - Severity: minor
  - Forward impact: Dev places the new validation in/reachable-from a `RulesConfig` `model_validator`. The WN/base default length (6) may be imported or derived from the bound module via a local import (the loader's existing cycle-avoidance pattern).
- **RED also covers the `standard_array`-method default path, slightly broader than the WN-named scope**
  - Rationale: the AC says "no authored standard_array" without restricting the method; both default paths share the identical IndexError, and a single `standard_array is None && count > default-length` validator greens both — no extra Dev work.
  - Severity: minor
  - Forward impact: the fix should gate on `standard_array is None` (not on the method), naturally covering both; see the related Delivery Finding re: the base default.
- **Validator covers the base `_DEFAULT_STANDARD_ARRAY` (standard_array method) for ALL rulesets, not WN-only**
  - Rationale: TEA's RED `test_undersized_…_standard_array_method` and TEA's Delivery Finding both target the base-default path; a single ruleset-agnostic check for the `standard_array` method is *simpler* than a WN-only special-case AND closes the identical base-default gap. No live pack is affected — all 11 load clean.
  - Severity: minor
  - Forward impact: any future non-WN pack authoring `standard_array` with more ability scores than the 6-entry base default and no explicit array now fails loud at load (the intended No-Silent-Fallbacks behavior). Resolves the TEA base-default Delivery Finding.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Load-time failure asserted at the `RulesConfig` model-validation seam, not the WN module bind**
  - Spec source: context-story-153-34.md, Scope Item 2 ("Add a LOAD-TIME size validation … Mirror the existing `RulesConfig._validate_standard_array`")
  - Spec text: "fail loud at pack-load, not at chargen … mirror the existing `RulesConfig._validate_standard_array` validator"
  - Implementation: RED tests assert `RulesConfig(...)` construction raises `ValueError`; this constrains Dev to add the validation where it runs during model construction (a `model_validator`), reachable for any pack whose `rules.yaml` is loaded — rather than only in `without_number.py`'s chargen path (which the 153-4 note listed as the affected file).
  - Rationale: `rules.yaml` → `RulesConfig` IS the pack-load validation step, and the sibling validator the spec names to mirror lives there; a module-only check that doesn't run at construction would leave the IndexError latent until chargen, defeating the "at load" AC.
  - Severity: minor
  - Forward impact: Dev places the new validation in/reachable-from a `RulesConfig` `model_validator`. The WN/base default length (6) may be imported or derived from the bound module via a local import (the loader's existing cycle-avoidance pattern).
- **RED also covers the `standard_array`-method default path, slightly broader than the WN-named scope**
  - Spec source: context-story-153-34.md, Scope Item 2 AC ("a WN pack … omitting `standard_array` … no authored standard_array")
  - Spec text: "Loading a WN pack with ability-score count ≠ 6 (and no authored `standard_array`) raises a loud … error AT LOAD"
  - Implementation: a second RED test exercises `stat_generation: standard_array` (base default path), not only `point_buy` (WN-dead path); both reach a 6-element default when `standard_array is None`.
  - Rationale: the AC says "no authored standard_array" without restricting the method; both default paths share the identical IndexError, and a single `standard_array is None && count > default-length` validator greens both — no extra Dev work.
  - Severity: minor
  - Forward impact: the fix should gate on `standard_array is None` (not on the method), naturally covering both; see the related Delivery Finding re: the base default.

### Dev (implementation)
- **Validator covers the base `_DEFAULT_STANDARD_ARRAY` (standard_array method) for ALL rulesets, not WN-only**
  - Spec source: context-story-153-34.md, Scope Item 2 ("size-validate the WN default spread against ability count")
  - Spec text: "size-validate the WN default spread against ability count (fail loud at load …)"
  - Implementation: `_validate_default_spread_covers_abilities` gates the `point_buy` method only for WN-family rulesets (`_WN_STANDARD_ARRAY`), but the `standard_array` method for ALL rulesets (base `_DEFAULT_STANDARD_ARRAY`). So a non-WN pack using `standard_array` with >6 abilities and no authored array also fails loud at load.
  - Rationale: TEA's RED `test_undersized_…_standard_array_method` and TEA's Delivery Finding both target the base-default path; a single ruleset-agnostic check for the `standard_array` method is *simpler* than a WN-only special-case AND closes the identical base-default gap. No live pack is affected — all 11 load clean.
  - Severity: minor
  - Forward impact: any future non-WN pack authoring `standard_array` with more ability scores than the 6-entry base default and no explicit array now fails loud at load (the intended No-Silent-Fallbacks behavior). Resolves the TEA base-default Delivery Finding.

### Reviewer (audit)
- **TEA: Load-time failure at the `RulesConfig` model-validation seam** → ✓ ACCEPTED by Reviewer: this is the truest "fail loud at load" seam (pydantic validates `rules.yaml` at pack load) and faithfully mirrors the sibling `_validate_standard_array` the 153-4 review named. Dev implemented exactly here (`rules.py:1376`). Sound.
- **TEA: RED also covers the `standard_array`-method default path (broader than the WN-named scope)** → ✓ ACCEPTED by Reviewer: the underflow is identical for the base `_DEFAULT_STANDARD_ARRAY`; a single `standard_array is None && count > default-length` validator greens both with no extra surface. Verified no live pack is affected (11/11 load, 635 regression green).
- **Dev: Validator covers the base `_DEFAULT_STANDARD_ARRAY` (standard_array method) for ALL rulesets, not WN-only** → ✓ ACCEPTED by Reviewer: a ruleset-agnostic check for the `standard_array` method is simpler than a WN-only special-case AND closes the identical base-default gap (resolving the TEA Delivery Finding). I independently enumerated all `stat_generation` methods (`base.py:311-345`) and confirmed the two-branch logic covers exactly the two fixed-default paths with no missed method and no false-positive on generative methods. The only residual concern (hardcoded WN-family set) is logged as a non-blocking Reviewer Delivery Finding, not a flag on this deviation.
- No undocumented deviations found: the diff matches the logged TEA/Dev entries exactly (content migration = the 4 named WN packs only; server = the single `model_validator` + constant).