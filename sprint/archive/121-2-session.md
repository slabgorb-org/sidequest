---
story_id: "121-2"
jira_key: ""
epic: "121"
workflow: "tdd"
---
# Story 121-2: F4b — pulp_noir Fate migration (pilot)

## Story Details
- **ID:** 121-2
- **Jira Key:** (not tracked)
- **Workflow:** tdd
- **Stack Parent:** 121-1 (F4a engine spine — prerequisite)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-15T14:22:47Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-15T13:23:54Z | 2026-06-15T13:25:08Z | 1m 14s |
| red | 2026-06-15T13:25:08Z | 2026-06-15T14:00:30Z | 35m 22s |
| green | 2026-06-15T14:00:30Z | 2026-06-15T14:12:07Z | 11m 37s |
| review | 2026-06-15T14:12:07Z | 2026-06-15T14:22:47Z | 10m 40s |
| finish | 2026-06-15T14:22:47Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (blocking): Story 121-2's dependency 121-1 (F4a engine spine) is archived `done` but its server code is NOT in the repository. The whole F4b premise — bind `ruleset: fate` → builder constructs a populated FateSheet — is unbuildable. Verified absent on `sidequest-server` @ `develop` (and across `git log --all`, all local/remote branches, and stash): no `FateConfig`/`FateStuntDef` in `genre/models/rules.py`, no `fate` field or `_validate_fate` or `ruleset_config()` fate arm, no `ChargenResources.fate_sheet` (`game/chargen_contribution.py`), no `FateRulesetModule.seed_chargen_resources` (`game/ruleset/fate.py`), no `fate.chargen.seeded` span, and no `tests/game/ruleset/test_121_1_fate_chargen_seed.py` (the 19 tests the 121-1 archive claims). The F4a feature branch `feat/121-1-f4a-fate-chargen-spine` does not exist on origin (only `feat/f1c-fate-conflict` does); no open server PR. The F1 fate engine DOES exist (`fate_sheet.py`, `FateRulesetModule` sans chargen hook, `fate_conflict.py` dispatch, `telemetry/spans/fate.py`), so this is specifically the F4a chargen-seeding spine that is missing. Likely the `merge_pr` no-op gotcha (commit a661be68) or a lost branch — the session was archived without the PR landing. Affects `sidequest-server` (F4a must be re-landed before 121-2 can start). Per story context line 31 ("do not patch F4a from F4b — report the finding and escalate to 121-1 rework") I am NOT implementing F4a from this lane and NOT writing RED tests against the absent substrate. *Found by TEA during test design.* **[RESOLVED — see SM (resolution) below; was a stale local checkout, not a real blocker.]**
- **Gap** (blocking): Story 121-2 is scoped `repos: content`, but its acceptance criteria can only be verified by a **server** test — `sidequest-content` has no Python test harness (no pyproject/conftest/tests), and real-pack chargen+routing checks run against the engine loading real content (the established `tests/integration/test_real_*` pattern). The RED tests therefore live in `sidequest-server/tests/integration/test_121_2_pulp_noir_fate_migration.py` on a new server branch `feat/121-2-pulp-noir-fate-migration`. Affects sprint story 121-2 (`repos` must become `content,server`) and the finish flow (two PRs: content pack migration + server test). The 121-1 reviewer predicted exactly this ("F4b should add a skipif-gated real-pack chargen integration test"). *Found by TEA during test design.*
- **Conflict** (non-blocking): Story context AC3 names OTEL span `fate.conflict.resolved` as the routing proof — **that span does not exist.** The real fate resolution spans are `fate.action_resolved` (per 4dF roll) and `fate.exchange.resolved` (conflict walk finished); chargen emits `fate.chargen.seeded`. Minting a literal `fate.conflict.resolved` summary span is an engine change, out of this content-only story's scope. RED pins AC3 via the FateRulesetModule routing gate instead (the `isinstance` check `dispatch_fate_action` actually uses), faithful to "routes to fate_conflict, not native" without touching the engine. Affects `sprint/context/context-story-121-2.md` AC3 wording (correct the span name) — or open an engine story if a real conflict-resolved summary span is wanted. *Found by TEA during test design.*
- **Improvement** (non-blocking): F4a's `seed_chargen_resources` consumes only `fate.default_high_concept` / `default_trouble` for aspects (archetype→aspect mapping is deferred to 121-7). So per-archetype starting-aspect templates that story context guardrails mention authoring in `archetypes.yaml` are **forward content, not engine-consumed yet** — RED does not test them (it asserts the default HC/trouble pair the engine actually seeds). Dev should author the `fate:` block's `default_high_concept`/`default_trouble` to satisfy AC2; per-archetype templates can be authored but won't drive seeding until 121-7. Affects `sidequest-content/genre_packs/pulp_noir/` authoring scope. *Found by TEA during test design.*

### SM (resolution) — finding RESOLVED, NOT a blocker
- **Root cause: stale local checkout, not a missing dependency.** PR #884 ("feat(121-1): F4a — Fate chargen-seeding spine") merged cleanly into `origin/develop` (merge commit `f527ddb7`) at 2026-06-15T13:01:07Z. Local `sidequest-server/develop` was 3 commits behind origin (0 ahead, 3 behind), so the F4a symbols weren't in the working tree TEA inspected. `git log --all`/`git branch -a` missed it because the merge hadn't been fetched locally. SM ran `git fetch origin && git pull --ff-only origin develop` (clean FF, working tree was clean). Post-pull verification: `class FateConfig` ✓, `ChargenResources.fate_sheet` ✓, `FateRulesetModule.seed_chargen_resources` ✓, `tests/game/ruleset/test_121_1_fate_chargen_seed.py` ✓ — all present. The F4a engine spine is live; AC2/AC3/AC5 are buildable. No 121-1 rework needed. Gotcha corrected in `tea-gotchas.md` (the lesson is "fetch + check origin before declaring a dep missing"). **RED resumes with the real substrate present.**

### Dev (implementation)
- **Improvement** (non-blocking): The `annees_folles` world (pulp_noir's only world) still carries d20 vestiges under the now-Fate genre — `worlds/annees_folles/archetypes.yaml` NPC archetypes declare `stat_ranges` keyed to the removed ability scores (Savvy/Charm/Nerve/Finesse/Brawn/Grit) and `typical_classes` from the removed class list. These flow through encountergen as enemy-stat-block *flavor* and do NOT break pack load or chargen (genre suite green), but they should be re-expressed in Fate terms (skills + aspects) in a follow-up. Affects `sidequest-content/genre_packs/pulp_noir/worlds/annees_folles/archetypes.yaml` (world-tier NPC re-stat — likely folds into the F4c–e pattern or a dedicated world story). *Found by Dev during implementation.*
- **Gap** (non-blocking, pre-existing): 4 genre tests fail on BASE `develop` content independent of this story (proven by stashing the pulp_noir change and re-running — all 4 fail identically): `test_caverns_and_claudes_loads_with_committed_blow_beat`, `test_classes_yaml_loads_entries`, `test_elemental_harmony_loads_clean_under_wwn`, `test_heavy_metal_blade_work_has_class_filtered_cast_spell` — caverns/elemental_harmony/heavy_metal WWN content drift, same family the 121-1 Dev assessment flagged. NOT caused by and NOT touching pulp_noir. Affects `sidequest-content` (those packs) — tracked by epic-114/WWN-port work, not 121-2. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking, **address before F4c–e copy this template**): AC5 (`test_f4a_wiring_holds_for_real_pulp_noir`) is a composite of AC2+AC3 assertions and adds no discriminating power; nothing asserts the existing `fate.chargen.seeded` OTEL span fires when the **real** pulp_noir pack is built. F4a proved that span synthetically (`TestAC5ChargenSeededSpan` via `InMemorySpanExporter` + injected `_tracer`); F4b should re-assert it on real content per the OTEL lie-detector doctrine. Affects `sidequest-server/tests/integration/test_121_2_pulp_noir_fate_migration.py` (strengthen AC5 into a real-pack OTEL wiring test, mirroring F4a). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `test_fate_sheet_skills_match_pack_config` asserts `character.core.fate_sheet.skills == pack.rules.fate.skills` — tautological (both derive from the same YAML; a seed that truncated/reordered would still pass). Pin at least one concrete value (e.g. `skills["Investigate"] == 4`), as F4a did against a hardcoded constant. Affects the same test file. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): AC4 (`test_no_d20_ability_scores`) checks the pack *config* but not the *built character* — add `assert not character.core.stats` (or equiv.) so the de-d20 invariant is proven at the character level, not just config. Same file. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): test helpers `_load_pack()` / `_build_pulp_noir_character()` return `object`, forcing `# type: ignore[attr-defined]` across ~17 call sites; lines 146/161 access `pack.rules.fate.skills/.refresh` raw (AttributeErrors in a hypothetical pre-migration RED rather than failing cleanly). Use the real return types (`GenrePack`/`Character`) and `ruleset_config()`/None-guards. Same file. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): stale/misleading comments — the test module docstring says "RED today / still native-bound" but the migration lands in the same diff (GREEN at merge); the `rules.yaml` header comment lists "encounter tension" as "flavor Fate doesn't own" but `encounter_base_tension` has **no consumer anywhere in the engine** (verified by grep — only the field declaration at `rules.py:1123`), so it is pre-existing dead config, not active flavor; the AC3 inline comment names `dispatch_fate_action()`/`fate_conflict.py` which this test does not call. Affects the test file + `sidequest-content/genre_packs/pulp_noir/rules.yaml` (reword; optionally strip the dead `encounter_base_tension` block). *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 1 findings (0 Gap, 0 Conflict, 0 Question, 1 Improvement)
**Blocking:** None

- **Improvement:** The `annees_folles` world (pulp_noir's only world) still carries d20 vestiges under the now-Fate genre — `worlds/annees_folles/archetypes.yaml` NPC archetypes declare `stat_ranges` keyed to the removed ability scores (Savvy/Charm/Nerve/Finesse/Brawn/Grit) and `typical_classes` from the removed class list. These flow through encountergen as enemy-stat-block *flavor* and do NOT break pack load or chargen (genre suite green), but they should be re-expressed in Fate terms (skills + aspects) in a follow-up. Affects `sidequest-content/genre_packs/pulp_noir/worlds/annees_folles/archetypes.yaml`.

### Downstream Effects

- **`sidequest-content/genre_packs/pulp_noir/worlds/annees_folles`** — 1 finding

### Deviation Justifications

5 deviations

- **Per-archetype aspect templates not authored (only the engine-consumed default HC/trouble)**
  - Rationale: the F4a engine consumes only the default templates — archetype→aspect seeding is deferred to 121-7 (F4a2). Authoring per-archetype templates now would be inert content with no consumer, and no RED test pins them (TEA logged the matching deviation). Honors "No Stubbing — dead code is worse than no code."
  - Severity: minor
  - Forward impact: 121-7 authors per-archetype aspect templates + the engine path that seeds from them.
- **Native config stripped wholesale, beyond the strict test minimum**
  - Rationale: under a Fate binding the native engine is *replaced*, so its config is dead, not dormant — leaving it would be the "balance native against bound ruleset" trap SOUL forbids. This realizes AC4's intent, not just its test assertions.
  - Severity: minor
  - Forward impact: none negative; pack is cleanly Fate-only. World NPC stat_ranges remain (logged as a Dev finding).
- **AC3 pinned via routing gate, not a `fate.conflict.resolved` span**
  - Rationale: minting the named span is an engine change, out of this content-only story's scope; the routing proof is faithful to AC3's intent ("routes to fate_conflict, not native") and mirrors F4a's `test_fate_pack_routes_to_fate_module_not_native`.
  - Severity: minor
  - Forward impact: AC3 wording should be corrected, or an engine story opened if a literal conflict-resolved summary span is desired (logged as a Conflict finding).
- **RED tests placed in sidequest-server, not the content story repo**
  - Rationale: `sidequest-content` has no Python test harness; these ACs are only verifiable by the engine loading real content (the existing `test_real_*` real-pack pattern). No alternative placement exists.
  - Severity: major
  - Forward impact: story `repos` must become `content,server`; finish flow PRs both repos (logged as a blocking Gap finding).
- **No test for per-archetype aspect templates**
  - Rationale: F4a defers archetype-driven aspect seeding to 121-7 — the engine does not read per-archetype templates yet, so a test would pin unimplemented behavior.
  - Severity: minor
  - Forward impact: 121-7 (F4a2) adds archetype-driven seeding + its tests; per-archetype templates authored now are inert until then (logged as an Improvement finding).

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Per-archetype aspect templates not authored (only the engine-consumed default HC/trouble)**
  - Spec source: context-story-121-2.md, Technical Guardrails (archetypes.yaml)
  - Spec text: "author per-archetype starting-aspect templates (high concept + trouble pairs for each archetype; free aspects seeded in play)"
  - Implementation: authored a single `fate.default_high_concept` / `default_trouble` pair in rules.yaml (the only aspect templates F4a's `seed_chargen_resources` reads); did NOT add per-archetype aspect mappings to archetypes.yaml.
  - Rationale: the F4a engine consumes only the default templates — archetype→aspect seeding is deferred to 121-7 (F4a2). Authoring per-archetype templates now would be inert content with no consumer, and no RED test pins them (TEA logged the matching deviation). Honors "No Stubbing — dead code is worse than no code."
  - Severity: minor
  - Forward impact: 121-7 authors per-archetype aspect templates + the engine path that seeds from them.
- **Native config stripped wholesale, beyond the strict test minimum**
  - Spec source: context-story-121-2.md, AC4 + SOUL "Bind the Ruleset, Don't Balance It"
  - Spec text: "reconcile/strip the now-inert native config (power_tiers, native progression beats, d20 char_creation bits)"
  - Implementation: removed not just `ability_score_names` + `power_tiers.yaml` (the strictly test-gated bits) but also `stat_generation`, `point_buy_budget`, `allowed_classes`, `default_class`, `class_label`, the `hp`/`defense` `stat_display_fields`, and the entire native `confrontations:` block (6 dual-track defs). Left `progression.yaml` (narrative affinities, not d20-shaped, not test-gated) intact.
  - Rationale: under a Fate binding the native engine is *replaced*, so its config is dead, not dormant — leaving it would be the "balance native against bound ruleset" trap SOUL forbids. This realizes AC4's intent, not just its test assertions.
  - Severity: minor
  - Forward impact: none negative; pack is cleanly Fate-only. World NPC stat_ranges remain (logged as a Dev finding).

### TEA (test design)
- **AC3 pinned via routing gate, not a `fate.conflict.resolved` span**
  - Spec source: context-story-121-2.md, AC3
  - Spec text: "OTEL span `fate.conflict.resolved` is emitted ... GM-panel ... shows the action routed to `fate_conflict` (not native resolution)"
  - Implementation: AC3 asserted through the `FateRulesetModule` isinstance routing gate (the wire `dispatch_fate_action` uses to send actions to `fate_conflict`), not a `fate.conflict.resolved` span — because that span does not exist in the engine (real spans: `fate.action_resolved`, `fate.exchange.resolved`).
  - Rationale: minting the named span is an engine change, out of this content-only story's scope; the routing proof is faithful to AC3's intent ("routes to fate_conflict, not native") and mirrors F4a's `test_fate_pack_routes_to_fate_module_not_native`.
  - Severity: minor
  - Forward impact: AC3 wording should be corrected, or an engine story opened if a literal conflict-resolved summary span is desired (logged as a Conflict finding).
- **RED tests placed in sidequest-server, not the content story repo**
  - Spec source: story 121-2 `repos` field
  - Spec text: "repos: content"
  - Implementation: the failing integration tests live in `sidequest-server/tests/integration/test_121_2_pulp_noir_fate_migration.py` on server branch `feat/121-2-pulp-noir-fate-migration`; the pack migration remains content-side.
  - Rationale: `sidequest-content` has no Python test harness; these ACs are only verifiable by the engine loading real content (the existing `test_real_*` real-pack pattern). No alternative placement exists.
  - Severity: major
  - Forward impact: story `repos` must become `content,server`; finish flow PRs both repos (logged as a blocking Gap finding).
- **No test for per-archetype aspect templates**
  - Spec source: context-story-121-2.md, Technical Guardrails (archetypes.yaml per-archetype HC+trouble templates)
  - Spec text: "author per-archetype starting-aspect templates (high concept + trouble pairs for each archetype)"
  - Implementation: RED tests only the single default high-concept/trouble pair the F4a seed actually consumes (`fate.default_high_concept`/`default_trouble`); no assertion on archetype→aspect mapping.
  - Rationale: F4a defers archetype-driven aspect seeding to 121-7 — the engine does not read per-archetype templates yet, so a test would pin unimplemented behavior.
  - Severity: minor
  - Forward impact: 121-7 (F4a2) adds archetype-driven seeding + its tests; per-archetype templates authored now are inert until then (logged as an Improvement finding).

### Reviewer (audit)
- **AC3 pinned via routing gate, not a `fate.conflict.resolved` span** (TEA) → ✓ ACCEPTED: the named span genuinely does not exist (verified — fate spans are `fate.action_resolved`/`fate.exchange.resolved`/`fate.chargen.seeded`); the `isinstance(module, FateRulesetModule)` routing proof is the same wiring assertion F4a used and is faithful to AC3 without an engine change. Sound. (Separately recommended the **chargen** span `fate.chargen.seeded` be asserted on the real pack — that one exists — as a non-blocking finding.)
- **RED tests placed in sidequest-server, not the content story repo** (TEA) → ✓ ACCEPTED: forced by reality — `sidequest-content` has no Python test harness; real-pack verification only runs server-side (the established `test_real_*` pattern). The blocking repos-field finding (`content` → `content,server`) correctly captures the bookkeeping fix.
- **No test for per-archetype aspect templates** (TEA) / **Per-archetype aspect templates not authored** (Dev) → ✓ ACCEPTED: the F4a seed consumes only `default_high_concept`/`default_trouble`; archetype→aspect mapping is 121-7. Testing/authoring inert content now would violate "No Stubbing." Correct deferral.
- **Native config stripped wholesale, beyond the strict test minimum** (Dev) → ✓ ACCEPTED: this realizes AC4's intent and SOUL's "Bind the Ruleset, Don't Balance It" — the native combat engine is replaced, so its config (confrontations, ability scores, classes, power_tiers) is correctly removed, not balanced. Verified the strip is clean (no leftover native keys). One residue: `encounter_base_tension` was retained — but it has no consumer anywhere (dead config pre-dating this story), so this is a Low cleanup note, not a flaw in the deviation.
- No undocumented deviations found beyond those logged — the diff matches the audited deviation set (plus the `encounter_base_tension` retention, logged as a Reviewer finding).

## TEA Assessment

**Tests Required:** Yes — but **BLOCKED, no tests written.**
**Status:** RED complete — 11 failing / 1 passing, ready for GREEN.

> **History note:** RED was first halted on a *suspected* missing F4a dependency. SM traced it to a stale local `sidequest-server` checkout (3 commits behind origin), fast-forwarded, and the real F4a substrate (FateConfig / seed_chargen_resources / ChargenResources.fate_sheet / the 19-test file) is present. RED then proceeded normally against real F4a. See the SM (resolution) note above.

**Test Files:**
- `sidequest-server/tests/integration/test_121_2_pulp_noir_fate_migration.py` (NEW, server branch `feat/121-2-pulp-noir-fate-migration`, commit `fd98ba4d`) — real-pack integration: loads the production `pulp_noir` pack via `find_pack_path` + `load_genre_pack`, walks the production `CharacterBuilder`, asserts the 121-2 ACs. Mirrors `test_real_neon_character_gets_strain_pool` and the F4a fate_sheet/routing contract.

**Tests Written:** 13 tests across the 5 ACs.
**RED verified:** `uv run pytest -n0` (direct — testing-runner fabricates output, per project memory): **11 failed, 1 passed**. All 11 fail for the correct reason — pulp_noir is still native-bound (`ruleset=="native"`, `power_tiers` populated, `ability_score_names` present, `fate_sheet=None`). The 1 pass is the invariant negative `test_native_module_is_not_the_fate_module` (must always pass). Imports all resolved (FateConfig/FateSheet/FateRulesetModule present) and the generic chargen walk **built a real pulp_noir PC** (`Sam Spade, An Old Money Detective`) — so the suite flips GREEN cleanly once content authors the `fate:` block and strips native config. Lint: `ruff check` clean.

| AC | Tests | Status |
|----|-------|--------|
| AC1 pack loads + valid fate block | `test_pulp_noir_binds_fate_ruleset`, `test_pulp_noir_authors_a_valid_fate_block`, `test_pulp_noir_authors_hardboiled_core_skills` | failing (RED) |
| AC2 PC gets populated FateSheet | `test_real_pulp_noir_character_gets_fate_sheet`, `test_fate_sheet_skills_match_pack_config`, `test_fate_sheet_has_high_concept_and_trouble_aspects`, `test_fate_sheet_refresh_and_starting_fate_points` | failing (RED) |
| AC3 routes to fate_conflict not native | `test_pulp_noir_resolves_to_fate_module`, `test_native_module_is_not_the_fate_module` (passing invariant) | failing (RED) + invariant green |
| AC4 native config stripped | `test_power_tiers_removed`, `test_no_d20_ability_scores` | failing (RED) |
| AC5 F4a wiring holds on real pack | `test_f4a_wiring_holds_for_real_pulp_noir` | failing (RED) |

### Rule Coverage (python lang-review + project rules)

| Rule | Test(s) | Status |
|------|---------|--------|
| No Source-Text Wiring Tests (CLAUDE.md) | AC3/AC5 wiring via `get_ruleset_module` + `isinstance` behavior, never `read_text()` grep | pass (by construction) |
| OTEL / lie-detector intent (CLAUDE.md) | AC3 routing gate is the honest "fate not native" proof; documented why the AC-named `fate.conflict.resolved` span is absent (Conflict finding) | addressed |
| No Silent Fallbacks (SOUL) | AC1 relies on loader's fail-loud `_validate_fate`; `find_pack_path` raises `PackNotFound` (no silent default) | pass |
| #6 test-quality (meaningful, non-vacuous asserts) | exact-value asserts on skills/aspects/refresh/ruleset; paired negatives discriminate (native≠fate) | pass |

**Self-check:** 0 vacuous tests — every test has a concrete assertion; the one passing test is a deliberate discriminating invariant, not a tautology.

**Note for Dev (GREEN is content-authoring):** make the failing assertions pass by migrating `sidequest-content/genre_packs/pulp_noir/` — set `rules.yaml ruleset: fate` + author the `fate:` block (skills incl. the hard-boiled core, `refresh>=1`, `default_high_concept`, `default_trouble`), strip `power_tiers.yaml` + native d20 bits (`ability_score_names`, char_creation d20 scenes) so the de-d20 build path engages. Content authoring delegated to gm/scenario-designer/writer. **Do not touch the engine** — if an AC can't pass without an engine change, that's an F4a gap; escalate (per story context line 31). The server test branch already carries the RED tests; Dev's content branch is `feat/121-2-pulp-noir-fate-migration` on `sidequest-content`.

**Handoff:** To Naomi Nagata (Dev) for GREEN — content migration of pulp_noir.

## Dev Assessment

**Implementation Complete:** Yes — GREEN.

**Approach:** Content-only migration. Authoring delegated to the **scenario-designer** specialist (per story directive) against the RED test contract; Dev (Naomi) integrated, verified, and ran regression. No engine code touched — the F4a spine (FateConfig / seed_chargen_resources / FateRulesetModule routing) was already in place and consumed as-is.

**Files Changed:**
- `sidequest-content/genre_packs/pulp_noir/rules.yaml` (content branch `feat/121-2-pulp-noir-fate-migration`, commit `60647f5`) — bind `ruleset: fate`; author the `fate:` block (17-skill hard-boiled pyramid incl. the 6 asserted core skills Investigate/Contacts/Notice/Rapport/Deceive/Shoot, `refresh: 3`, default high-concept + trouble, 4 pulp stunts); strip the inert native d20 engine config (`ability_score_names`, `stat_generation`, `point_buy_budget`, `allowed_classes`, `default_class`, `class_label`, `hp`/`defense` `stat_display_fields`, the 6 native `confrontations:` defs); retain genre flavor Fate doesn't own (custom_rules heat/contacts/occult, Heat resource, encounter tension, scene defaults).
- `sidequest-content/genre_packs/pulp_noir/power_tiers.yaml` — **deleted** (Fate has no power tiers; AC4).
- (RED tests already on server branch `feat/121-2-pulp-noir-fate-migration`, commit `fd98ba4d`.)

**Tests:** 12/12 passing (GREEN) — verified by **direct** `uv run pytest tests/integration/test_121_2_pulp_noir_fate_migration.py -n0` (not via testing-runner, which fabricates output per project memory). The real-pack build walks pulp_noir's choice-based chargen and produces a populated FateSheet; routing resolves to FateRulesetModule. *(Correction: the suite is 12 tests, not the "13" stated at RED exit — RED was 11 failed + 1 passed = 12; scenario-designer caught the miscount.)*
**Pack validation:** `python -m sidequest.cli.validate pack ../sidequest-content/genre_packs/pulp_noir` → PASS (0 errors; 9 pre-existing genre-wide structural warnings).
**Regression:** genre + ruleset + fate suites = **1488 passed, 52 skipped**. The only 4 failures (caverns_and_claudes / elemental_harmony / heavy_metal WWN class tests) are **pre-existing content drift, proven by stashing this change and re-running on base — all 4 fail identically without it.** Zero regressions from the migration.
**Branches pushed:** content `60647f5` + server `fd98ba4d`, both `origin/feat/121-2-pulp-noir-fate-migration`.

**Genre quality:** Skill pyramid is Fate-canonical (Investigate +4 apex). Aspects ("Disbarred Lawyer Working the Other Side of the Law" / "I Can't Leave a Loose Thread Alone") and stunts (Read the Room, Know a Guy, Talk Past the Lie, Cold Under Fire) avoid Spade/Marlowe pastiche — sourced to Hammett's Continental Op + Malet's Nestor Burma per the scenario-designer's provenance notes. A cliche-judge pass in review is welcome.

**⚠ Carries TEA's blocking repos finding:** this story is cross-repo (content pack + server test). Story `repos` is still `content` only — SM must set it to `content,server` so the finish flow opens/merges **both** PRs. Both branches are pushed and ready.

**Handoff:** To The Architect (Amos Burton / TEA) for the verify phase (simplify + quality-pass), then Reviewer.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (12/12 green, validate PASS, 0 new regressions, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 11 | confirmed 4 (AC5/OTEL, tautology, AC4-config-only, 146/161 guard), dismissed 1 (skipif: load is in-test not collection), deferred/low 6 |
| 5 | reviewer-comment-analyzer | Yes | findings | 4 | confirmed 3 (docstring "RED today" stale, _build class-free, AC3 names uncalled dispatch fn), dismissed 1 (header "invents heat/occult" — heat/occult ARE retained, lines 78/83/91) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 3 | confirmed 2 (object return types ×2 → Low; lang-review rules 1/2/6/10/15/17 all compliant), downgraded 1 (encounter_base_tension "active native hook" → Low: verified NO consumer exists, dead config pre-dating story) |
| 10 | cliche-judge (bonus, genre quality) | Yes | findings | 8 | 0 blockers — ships; 4 register-level fixes, 4 nits; "would satisfy a career GM" |

**All received:** Yes (5 ran — preflight, test-analyzer, comment-analyzer, rule-checker, cliche-judge; 5 disabled via `workflow.reviewer_subagents`, domains low-relevance for a YAML-migration + single-test diff and covered first-party)
**Total findings:** 9 confirmed (all non-blocking Medium/Low), 2 dismissed (with rationale), several low deferred. 0 Critical, 0 High.

## Reviewer Assessment

**Verdict:** APPROVED

The delivered artifact — the pulp_noir Fate Core migration plus its real-pack integration test — meets all five acceptance criteria, is doctrine-aligned, green, and regression-free. Every confirmed finding is a non-blocking test-rigor or documentation improvement; **no Critical or High defect exists.** The strongest cluster (AC5 should assert the real-pack `fate.chargen.seeded` OTEL span; de-tautologize the skills check) is logged as Improvements to fold in **before F4c–e replicate this pilot's test pattern** — I recommend SM spin them into a fast-follow or fold them into the next F4 story rather than block a correct, green change.

**Data flow traced:** `pulp_noir/rules.yaml` `fate:` block → `load_genre_pack()` (pydantic `FateConfig`, `extra="forbid"`, fail-loud `_validate_fate`) → `RulesConfig.ruleset_config()` returns `FateConfig` → `FateRulesetModule.seed_chargen_resources` (from F4a) seeds skills/HC+trouble aspects/refresh onto a `FateSheet` → `CharacterBuilder.build()` attaches it to `CreatureCore.fate_sheet`; dispatch routes conflict actions to `fate_conflict` via the `isinstance(module, FateRulesetModule)` gate. Every input is genre-authored content (not player free-text). Verified the migrated pack loads clean and a real PC builds with a populated sheet.

**Observations (≥5):**
1. `[VERIFIED]` Native strip is complete — independent grep of the migrated `rules.yaml` for `point_buy|ability_score|stat_check|allowed_classes|stat_display|power_tier|stat_generation|confrontations|progression_beats` returns **zero** matches; `power_tiers.yaml` deleted; `pack.yaml` carries no power_tiers reference. Realizes SOUL "Bind the Ruleset, Don't Balance It."
2. `[VERIFIED]` `[PRE]` GREEN + no regression — `uv run pytest ...121_2... -n0` → 12 passed; genre+ruleset+fate suites 1488 passed; the 4 failures (caverns/elemental_harmony/heavy_metal WWN) are pre-existing, proven by Dev's stash-and-rerun (all 4 fail identically on base). Confirmed independently.
3. `[VERIFIED]` `[RULE]` FateConfig schema conformance — the `fate:` block uses only `skills`/`refresh`/`default_high_concept`/`default_trouble`/`stunts` (each stunt `{name,description}`); `extra="forbid"` would have failed load on any stray key, and load passes. Genre-tier (rules.yaml), not world-tier — complies with "Crunch in the Genre."
4. `[MEDIUM]` `[TEST]` AC5 adds no discrimination beyond AC2/AC3 and omits the real-pack `fate.chargen.seeded` OTEL span assertion (the span exists; F4a tests it synthetically). Non-blocking — F4a covers the engine→span wiring and AC2/AC3 provide a behavioral real-pack wiring proof (build + routing); but strengthen before the template propagates.
5. `[MEDIUM]` `[TEST]` `test_fate_sheet_skills_match_pack_config` is tautological (both sides from the same YAML) — pin a concrete value to catch a seed-transform bug.
6. `[LOW]` `[RULE]`/`[SIMPLE]` `encounter_base_tension` retained in `rules.yaml` but has **no consumer anywhere** (only the field declaration at `rules.py:1123`) — pre-existing dead config the new header comment mislabels as "flavor Fate doesn't own." Optional strip; not introduced by this story.
7. `[LOW]` `[TYPE]` test helpers return `object` (forcing ~17 `# type: ignore[attr-defined]`); use real types.
8. `[LOW]` `[DOC]` test module docstring "RED today / still native-bound" is stale at merge (migration lands same diff → GREEN); reframe as historical.
9. `[VERIFIED]` `[CLICHE]` genre quality clears the career-GM bar — skill pyramid (Investigate +4 apex, Fight/Shoot low) is a genre thesis; aspects/stunts sourced to Hammett's Continental Op / Malet's Burma, no trenchcoat pastiche. One pre-existing cliché outside scope: `default_location` "a city that never sleeps."

### Rule Compliance (python lang-review + SOUL/CLAUDE)

| Rule | Instances checked | Verdict |
|------|-------------------|---------|
| #1 silent exceptions | `_has_pulp_noir_content`, `_load_pack` (catch specific `PackNotFound`, skip — no swallow) | compliant |
| #3 type annotations | helper return types are `object` (no comment) | LOW violation — use real types (finding) |
| #6 test quality | 12 tests, exact-value asserts + discriminating negative; one tautological assert (skills-match) | mostly compliant; 1 finding |
| #8 unsafe deserialization | YAML via production `load_genre_pack` (safe loader); no pickle/eval | compliant |
| #10 import hygiene | explicit sorted imports, deliberate deferred `load_genre_pack`, no star imports | compliant |
| No Source-Text Wiring Tests (CLAUDE) | AC3/AC5 wiring via `get_ruleset_module`+`isinstance` behavior, no `read_text` grep | compliant |
| Every Suite Needs a Wiring Test (CLAUDE) | real-pack build + routing IS a behavioral wiring test; OTEL-span belt-and-suspenders missing | compliant (finding to strengthen) |
| Bind the Ruleset, Don't Balance It (SOUL) | native engine config removed wholesale; only inert residue is consumer-less `encounter_base_tension` | compliant (Low cleanup) |
| No Silent Fallbacks (SOUL) | relies on fail-loud `_validate_fate` + `PackNotFound`; no silent default | compliant |
| No Stubbing / dead code (SOUL/CLAUDE) | `encounter_base_tension` retained but consumer-less (pre-existing) | LOW finding |
| Crunch in the Genre, Flavor in the World (SOUL) | `fate:` block at genre tier (rules.yaml), no world-tier fate block | compliant |

### Devil's Advocate

*Argue this is broken.* The whole green result rests on `seed_chargen_resources` copying `fate.skills` verbatim — and the one test that checks the seeded skills (`test_fate_sheet_skills_match_pack_config`) compares the sheet against the very same `pack.rules.fate.skills` it was seeded from. So a seeding bug that silently dropped half the ladder, or rounded every rating to +0, would sail straight through: both sides move together. AC4 has the mirror weakness — it asserts the *pack* declares no ability scores but never inspects the *built character*, so a builder that fell through to a legacy stat-gen path and quietly rolled six d20 attributes onto the Fate PC would still pass every assertion. AC5 calls itself the "wiring contract" yet exercises nothing AC2 and AC3 didn't; the actual production conflict path (`execute_intent_router_pre_narrator_pass` → `dispatch_fate_action` → `fate_conflict`) and the `fate.chargen.seeded` span — the project's own lie-detector — are never driven, so a chargen path that attaches a sheet through an un-instrumented branch would look identical to a correct one. A hostile content author could re-add `power_tiers.yaml` or set `Shoot: 99999` and only the file-deletion test or nothing at all would object. And `encounter_base_tension` proves the migration's mental model is "strip what I remembered," not "strip everything the native engine touched" — it survived because no one checked for a consumer.

*Why it holds anyway.* Each of these is a *test could be sharper*, not *the delivery is wrong*. The seed-copy contract is independently proven against a hardcoded constant in F4a's `TestAC3SeedBuildsPopulatedSheet` (real discrimination at the engine layer); F4b's tautology is redundant-but-not-false. The de-d20 build path is exercised end-to-end — the real PC builds with `fate_sheet` populated and no ability scores, which is the behavior AC4 cares about even if it asserts on config. The `Shoot: 99999` and re-added-power_tiers cases are content-authoring degeneracies Fate inherits from SRD norms, out of an engine-free migration's remit. `encounter_base_tension` is inert (no consumer, verified) so it changes no behavior. Nothing here corrupts state, leaks data, or fails a requirement — the gaps are rigor, and they are logged for the template. No Critical/High emerges.

**Verdict rationale:** All five ACs met; content correct, doctrine-aligned, cliché-clear, green, zero new regressions. Nine non-blocking findings (test rigor, type/doc nits, one Low dead-config residue), two dismissed with verified rationale, all deviations audited and ACCEPTED. The test-rigor improvements are recommended as a fast-follow before F4c–e copy the pattern. **APPROVED.**

**Handoff:** To Camina Drummer (SM) for finish-story. ⚠ SM must reconcile the blocking repos-field finding (`content` → `content,server`) so both PRs (content `60647f5` + server `fd98ba4d`) are opened and merged.

## Sm Assessment

**Story:** 121-2 — F4b, the pulp_noir Fate migration. This is the **pilot** that proves the F4a engine spine (121-1) works end-to-end, and it establishes the per-pack pattern that F4c–e (tea_and_murder, wry_whimsy, spaghetti_western) will follow. pulp_noir is Fate's ancestral home, so it's the right pack to lead with.

**Dependency — satisfied.** 121-1 (F4a engine spine) is `done` and archived (`sprint/archive/121-1-session.md`). F4a seeds a valid default FateSheet from pack config via the chargen seam, so a pulp_noir PC bound to `ruleset: fate` will now construct a populated sheet instead of `fate_sheet=None`. AC5 (F4a wiring test passes with pulp_noir as test pack) is reachable.

**Scope.** Per the epic context (Neo Architect, 2026-06-15): F4b seeds skills (mandatory) plus default high-concept/trouble aspects and pulp stunts from pack config. Interactive Fate chargen — player authors aspects, allocates the skill pyramid, picks stunts — is explicitly OUT of this epic. Don't build a chargen UI here.

**Repo.** `content` only. The work is: author `pulp_noir` fate config (skill list, per-archetype starting-aspect templates, stunts), set `rules.yaml ruleset: fate`, and reconcile/strip the now-inert native config (`power_tiers`, native progression beats, d20 char_creation bits). Content authoring is delegated to gm/scenario-designer/writer per the story.

**Acceptance:** pack loads + `sidequest-validate` passes + a created PC has a populated FateSheet + a Fate action resolves through `fate_conflict` (not native), verifiable via OTEL span.

**Watch items for downstream phases:**
- The "strip native config" half is a deletion task — TEA should pin a test that asserts native resolution does NOT fire for a Fate-bound pulp_noir action (the OTEL `fate_conflict` span is the lie detector here, per the OTEL principle).
- This is a pilot: keep the pattern clean and documented in-session, because F4c–e copy it.

**Routing:** phased tdd → handing off to **tea** (Amos Burton) for the RED phase.