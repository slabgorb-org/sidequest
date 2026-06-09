---
story_id: "96-1"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 96-1: Rewrite content-coupled server tests against fixtures (decouple from live packs)

## Story Details
- **ID:** 96-1
- **Jira Key:** (none — no Jira for this project)
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 8
- **Priority:** p2
- **Type:** refactor

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-09T23:46:16Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-09T22:34:32Z | 2026-06-09T22:37:01Z | 2m 29s |
| red | 2026-06-09T22:37:01Z | 2026-06-09T23:16:42Z | 39m 41s |
| green | 2026-06-09T23:16:42Z | 2026-06-09T23:39:27Z | 22m 45s |
| review | 2026-06-09T23:39:27Z | 2026-06-09T23:46:16Z | 6m 49s |
| finish | 2026-06-09T23:46:16Z | - | - |

## Branch Strategy
**Branch Strategy:** github-flow — branch from develop (feat/96-1-content-test-fixtures)
**Repos:** sidequest-server

## Sm Assessment

Setup complete and verified:
- Session file at `.session/96-1-session.md`; branch
  `feat/96-1-content-test-fixtures` created from sidequest-server develop.
- Jira: skipped — this project has no Jira (sprint YAML is the tracker).
- Story context (`sprint/context/context-story-96-1.md`) enriched from the
  epic-96 description: work list = tests skipped by sidequest-server#726
  (skip reasons cite 94-4), rewrite against fixtures, no live pack/world slug
  coupling. ACs recorded; TEA refines in RED.
- Out of scope guard: Earthman tier-leak test belongs to story 96-2.
- Route: tdd (phased) → next agent TEA (RED phase).

## TEA Assessment

**Tests Required:** Yes
**Reason:** The story's deliverable IS tests — every #726-skipped content-coupled test
rewritten against synthetic fixture packs, RED until the fixtures (and one validator
function) exist.

**Test Files:**
- `tests/_helpers/fixture_packs.py` — NEW: fixture-pack resolution contract
  (`swn_test_pack`, `wwn_test_pack`, `test_world`; fail-loud `FixturePackNotFound`,
  explicitly NOT skippable — fixtures ship with the suite)
- `tests/fixtures/dogfight_playtest_encounter.py` — repointed to swn_test_pack +
  world binding (world-tier `resolve_inventory` REPLACE path, epic 94 shape)
- `tests/integration/test_dogfight_playtest_smoke.py`, `test_dogfight_swn_production_wiring.py`
  — module skips removed; fixture-driven
- `tests/integration/test_space_opera_hp_e2e.py` — module skip removed; blaster_sidearm
  resolved via world-tier `resolve_inventory`; synthetic pack mirrors both tiers
- `tests/integration/test_wwn_heavy_metal_chargen.py` — 2 skipped barsoom params dropped;
  NEW `test_world_tier_caster_seeds_effort_and_populated_spellcasting` (Psychic/Gadgeteer,
  builds through `resolve_classes` world-REPLACE seam); shared `_assert_caster_seeded`
- `tests/server/test_dogfight_shot_wiring.py`, `test_dogfight_player_throw_roundtrip.py`,
  `tests/server/dispatch/test_sealed_letter_dispatch_integration.py` — all 94-4 skips
  removed; fixture-driven; cac legacy tests keep a scoped `_NEEDS_LIVE_CONTENT` skipif
- `tests/server/test_space_opera_swn_combat_e2e.py`, `test_space_opera_melee_e2e.py`
  — skipped e2e tests + seam-sharing siblings fixture-driven; content smokes stay live
- `tests/server/test_reference_smoke.py` — skipped HTML test RETIRED (rationale in file)
- `tests/game/projection/test_visibility_tag_rule.py` — live-pack sweeps deleted
- `tests/cli/validate/test_pack_validator_projection_visibility.py` — NEW: pins
  `validate_visibility_coverage` + `pf validate pack` wiring (the one production-code
  contract in this story)

**Tests Written/Rewritten:** 28 RED (19 FixturePackNotFound errors + 9 failures incl.
6 validator ImportErrors), verified by testing-runner run 96-1-tea-red against the FULL
suite: 9916 passed / 27 failed / 40 errors / 1512 skipped, zero collection errors, zero
remaining `94-4` skip markers. Non-96-1 failures match the pre-existing baseline
recorded in Delivery Findings.
**Status:** RED (failing — ready for Dev)

### Fixture-Authoring Contract for Dev (GREEN)

The RED tests pin these fixture requirements (freeze values from what live
space_opera shipped pre-/post-94 — do NOT point at live content):
- `tests/fixtures/genre_packs/swn_test_pack/` (+ matching entry under
  `tests/fixtures/packs/` — note existing slugs there are symlinks):
  `ruleset: swn`; ConfrontationDefs: `combat` (Firefight, beat_selection,
  hp_depletion, shoot beat id=`shoot` kind=strike stat_check=Physique
  damage_channel=strike, opponent_default_stats hp=7 ac=12 + ALL SIX ability
  scores), `ship_combat` (hull 30 / ac 14), `melee` (strike beat, distinct ids),
  `dogfight` (sealed_letter_lookup, interaction_table with maneuvers
  straight/loop/kill_rotation/bank; (loop,kill_rotation)=mutual gunline;
  ≥2 distinct cell names across (straight,straight),(loop,kill_rotation),
  (bank,bank); frame_hp=8 in player/opponent_default_stats; weapon id
  `multifocal_laser` armor_piercing=20 vs armor=5);
  `worlds/test_world/inventory.yaml` item_catalog: `blaster_sidearm`
  (damage 1d6+0), `multifocal_laser` (the world tier REPLACES genre per
  `resolve_inventory` — genre-tier inventory may be empty/None)
- `tests/fixtures/genre_packs/wwn_test_pack/`: `ruleset: wwn` (complete
  canonical→abbrev attribute_map — wwn REQUIRES it), genre classes incl.
  Warrior; `worlds/test_world/` classes: caster Callings `Psychic` and
  `Gadgeteer` with wwn_magic (effort_sources, casts_per_day_by_level["1"],
  starting_prepared, prepared_by_level; make ONE of them `partial: true` so
  the -1 effort branch is exercised); char_creation scenes resolvable for
  the world
- `validate_visibility_coverage(rules: ProjectionRules) -> list[str]` in
  `sidequest/game/projection/validator.py` (non-raising; findings name the
  kind + "visibility_tag") wired into `_validate_projection` in
  `sidequest/cli/validate/pack.py` (only when projection.yaml exists);
  `validate_projection_rules` MUST NOT change

### Rule Coverage

| Rule (python.md) | How covered | Status |
|------|---------|--------|
| #5 path handling | fixture_packs.py is pathlib-only; test YAML writes pass `encoding="utf-8"` | self-check pass |
| #6 test quality | rewritten tests keep their original behavioral assertions; new validator tests assert exact finding counts + content with a positive control (`test_non_visibility_rule_for_kind_does_not_count_as_coverage`); no reason-less skips remain | self-check pass |
| #10 import hygiene | no star imports; unused imports removed (ruff clean) | self-check pass |

Other checklist rules (#1-#4, #7-#9, #11-#13) target production code; this story's only
production contract (validator function) is pinned by failing tests for Dev to satisfy.
**Self-check:** 0 vacuous tests in the rewritten set; one unused-import hack caught and
removed during authoring.

**Handoff:** To Dev for GREEN — author the two fixture packs, implement
`validate_visibility_coverage` + the pack.py wiring, make the 28 RED tests pass
without touching their assertions.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `tests/fixtures/packs/swn_test_pack/` — NEW fixture pack: SWN rulebook frozen from
  live space_opera (rules.yaml + dogfight/ interaction tables + classes/progression/
  etc.), `worlds/test_world/` carries the world-tier item catalog (blaster_sidearm
  1d6+0, multifocal_laser AP20, frozen from coyote_star) + minimal world files
  (donor: flickering_reach for lore-ish files, coyote_star for tropes/char_creation)
- `tests/fixtures/packs/wwn_test_pack/` — NEW fixture pack: WWN rulebook frozen from
  heavy_metal; `worlds/test_world/` (frozen from barsoom) authors WORLD-TIER caster
  Callings `Psychic` + `Gadgeteer` (renamed Mentalist/Super-scientist; Gadgeteer
  flipped to `partial: true` for the -1 effort branch)
- `sidequest/server/dispatch/damage_roll.py` — **production fix**: priority-3 catalog
  lookup now resolves through `resolve_inventory(pack, world_slug)` (world REPLACES
  genre); previously read only genre-tier `pack.inventory`, so strike damage silently
  skipped (`dice.damage_spec_missing`) for every epic-94-migrated pack IN LIVE PLAY
- `sidequest/game/ruleset/{base,native,swn}.py` — `resolve_damage(..., world_slug=None)`
  threaded through the RulesetModule seam (wwn/cwn inherit)
- `sidequest/server/dispatch/dice.py` — 3 call sites pass `snapshot.world_slug`
  (player strike, shock-on-miss, opponent reprisal)
- `sidequest/server/narration_apply.py` — opposed_check damage path passes
  `snapshot.world_slug` (both resolution paths wired per the opposed-check trap)
- `sidequest/game/projection/validator.py` — NEW `validate_visibility_coverage`
  (non-raising, content-gate severity; `validate_projection_rules` untouched)
- `sidequest/cli/validate/pack.py` — `_validate_projection` appends coverage findings
- `sidequest/telemetry/spans/__init__.py`, `tests/game/table/test_war_rig_command.py`
  — ride-along: 2 pre-existing auto-fixable ruff findings on develop

**Note:** `tests/fixtures/genre_packs` is a SYMLINK ALIAS of `tests/fixtures/packs`
(one physical tree) — the new packs exist once, reachable via both paths. Two
accidental circular self-symlinks from pack creation were caught and removed.

**Tests:** all 96-1 tests passing; full suite 9954 passed / 6 failed / 23 errors /
1512 skipped (run 96-1-dev-green) — every failure matches the pre-existing baseline
recorded in TEA's findings; zero mentions of swn_test_pack / wwn_test_pack /
FixturePackNotFound / validate_visibility_coverage. OTEL: world-tier damage resolution
is observable for free via the existing `resolved_inventory` state_transition span
(resolve_inventory emits on every call, including the genre fall-through).
**Branch:** feat/96-1-content-test-fixtures (pushed, d4142329)

**Handoff:** To Westley (Reviewer) for review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (tests GREEN 3458/0, 0 smells, tree clean, branch synced) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (1 enabled subagent returned; 8 disabled via workflow.reviewer_subagents — their domains covered by direct review below)
**Total findings:** 3 confirmed (1 Medium, 2 Low), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** player DICE_THROW face → `dispatch_dice_throw` (dice.py:550) →
`ruleset.resolve_damage(world_slug=snapshot.world_slug)` →
`resolve_damage_spec_from_beat_and_actor` priority-3 → `resolve_inventory(pack,
world_slug)` (world REPLACES genre, OTEL `resolved_inventory` span fires) → catalog
DamageSpec → server-side damage roll → `apply_beat_hp_channel` → HpPool ablation +
`state_patch_hp` span → `encounter.resolved` on 0 HP. Safe: snapshot is dereferenced
(`find_creature_core`) immediately above every new `snapshot.world_slug` read, so no
new None-deref path; falsy/unknown world falls through to genre tier inside
`resolve_inventory` (pre-existing, span-observable semantic). Proven end-to-end by
`test_firefight_resolves_on_hp_depletion_vs_content_ac`.

**Observations (≥5, with evidence):**
1. [VERIFIED] All four damage-resolution call sites carry world_slug — dice.py:554,
   :704, :1202 (opponent reprisal) and narration_apply.py:6897 (opposed path) — both
   resolution paths wired per the opposed-check trap; checked against CLAUDE.md
   "Verify Wiring" and the ruleset-module checklist (native+swn updated; wwn/cwn
   inherit from swn — no override of resolve_damage exists, confirmed by grep).
2. [VERIFIED] `validate_visibility_coverage` wiring is real and live:
   `_validate_projection` (cli/validate/pack.py:283 list-comp) → `validate_pack_structure`
   → `pf validate pack` / `just validate-pack`. I ran the validator over ALL 11 live
   packs: PASS — and a NEGATIVE CONTROL (NARRATION-only rules string) correctly
   reports the missing SECRET_NOTE rule. Not a no-op.
3. [VERIFIED] Fixture packs load through the production loader and satisfy the test
   contract: swn_test_pack rules.yaml carries combat hp:7/ac:12, ship hull hp:30,
   frame_hp:8, both projection visibility_tag rules; wwn_test_pack world classes
   resolve Psychic (partial:false) + Gadgeteer (partial:true) through resolve_classes.
4. [VERIFIED] No new silent failures: the change REMOVES one (strike damage silently
   skipping for migrated packs); `_validate_projection`'s broad except is pre-existing,
   commented (noqa BLE001 with rationale), and converts failures into labeled errors,
   not swallows.
5. [MEDIUM] Absent projection.yaml escapes the coverage check: elemental_harmony ships
   NO projection.yaml, so the validator passes it while the pack runs with a
   pass-through ProjectionFilter (the MP secret-note leak the rules prevent). NOT a
   regression — the old parametrized test's elemental_harmony param was skip-disabled
   since #726, so this was already unenforced — but the content decision (require
   projection.yaml in pack_schema, or warn on absence) is now visible. Logged as a
   Delivery Finding; non-blocking for this story.
6. [LOW] `RulesetModule.resolve_damage`'s new `world_slug=None` param is un-annotated
   in base.py/native.py/swn.py signatures (matches the surrounding un-annotated
   `beat/actor_core/pack` style; the concrete resolver function IS annotated
   `str | None`). Consistent with file style; flagging per python.md #3.
7. [LOW] `wwn_test_pack/worlds/test_world/world.yaml` retains Barsoom's description
   prose + a stale "live (Keith 2026-06-05)" comment and barsoom cover_poi — loads
   fine (history.yaml is the matching barsoom copy) and is invisible to players, but
   a one-line fixture-note header would prevent future confusion. Cosmetic.

**Pattern observed:** the fix reuses the existing `resolve_inventory` seam (Don't
Reinvent) and inherits its OTEL `resolved_inventory` state_transition span on every
damage lookup — the GM panel can now prove which tier a weapon resolved from
(inventory_resolve.py:52-75). Good pattern; no new telemetry needed.

**Error handling:** `FixturePackNotFound` is fail-loud and documented as
non-skippable (tests/_helpers/fixture_packs.py:49-63); validator findings are
labeled strings, never raised past the CLI boundary (pack.py:281-283).

**Security analysis:** no auth/input surfaces changed; the visibility-coverage check
STRENGTHENS the perception firewall posture (ADR-104/-105) by making missing
NARRATION/SECRET_NOTE routing a content-gate error. Tenant isolation N/A (no tenant
concept; the per-player firewall analog was audited above).

**Rule Compliance (python.md, changed production code):** #1 silent-exceptions PASS
(see obs 4); #2 mutable-defaults PASS (`world_slug=None` immutable); #3 annotations
PARTIAL (obs 6, Low); #4 logging PASS (damage_spec_missing warnings retained); #5
path handling PASS (pathlib throughout fixture helper); #6 test quality PASS
(validator tests assert exact finding counts + positive control; no reason-less
skips; preflight confirms 0 added skips); #7 resources PASS (no handles); #8
deserialization PASS (existing safe loaders only); #9 async PASS (none touched);
#10 imports PASS (function-local imports follow established lazy-import pattern,
e.g. swn.py:200; telemetry __init__ sort fixed); #11 input validation PASS (CLI
genre_dir checks pre-existing); #12 dependencies PASS (untouched); #13
fix-regressions PASS (ride-along lint fixes re-scanned — import sort + unused
import removal only).

### Devil's Advocate

Suppose this is broken. The sharpest attack: the priority-3 catalog lookup changed
semantics for EVERY pack, not just migrated ones — a native-ruleset pack whose bound
world ships an inventory.yaml now has its genre catalog REPLACED during damage
resolution. If such a world's catalog omits an item the genre catalog carried, a
weapon that used to resolve damage now returns None and the hit deals 0 HP. Is that
a regression? No — it is the epic-94 semantic every OTHER consumer (chargen loadout,
gained-item catalog, dogfight weapons, views) already applies via the same
resolve_inventory call; damage resolution was the LAST holdout reading the genre
tier, which is precisely the bug. A split-brain catalog (chargen grants an item the
damage path can't price) would be worse. Second attack: `snapshot.world_slug` could
be stale or empty on synthetic snapshots — empty string is falsy, falls to genre
tier, identical to pre-change behavior; every rewritten test that NEEDS world tier
binds it explicitly. Third: the MagicMock pack in test_space_opera_hp_e2e now leaks
MagicMock attributes into resolve_inventory (`pack.worlds.get` on a mock returns a
mock → world.inventory is a mock → mock catalog!). Checked: the test assigns BOTH
`pack.inventory = real_pack.inventory` AND `pack.worlds = real_pack.worlds` (real
dict), so .get returns a real World; had Dev forgotten worlds, the catalog iteration
would have thrown on a Mock, and the test passed — covered. Fourth: the deleted
shipping-pack sweeps weakened live enforcement — partially true (validator is
operator-run via `just validate-pack`, not CI), and the absent-file case (obs 5) is
genuinely weaker than the old assert-exists. That is the one real loss; it is logged
as a finding with a concrete remediation (pack_schema required-file or absence
warning) rather than blocking a story whose param was already skip-dead. Fifth: the
fixture freeze is 15k lines of copied content that will rot — but rot is the POINT
(frozen = content changes can't turn tests red), and the loader gauntlet pins it.

**Handoff:** To Vizzini (SM) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)

- **Improvement** (non-blocking): live-content couplings remain OUTSIDE the #726 skip
  inventory and should get a follow-up story: `cac_pack`/`cac_snap` legacy
  beat_selection regression tests in
  `tests/server/dispatch/test_sealed_letter_dispatch_integration.py`, the
  melee content-contract tests + `test_ranged_shoot_still_routes_*` in
  `tests/server/test_space_opera_melee_e2e.py`, `test_world_loads_clean_under_swn`
  in `tests/server/test_space_opera_swn_combat_e2e.py` (deliberate content
  smoke), the heavy_metal genre-tier chargen walks in
  `tests/integration/test_wwn_heavy_metal_chargen.py`, the keeper-leak smokes
  in `tests/server/test_reference_smoke.py`, and content-gated `tests/genre/`
  calibration tests. Affects those files (decide per-test: fixture rewrite,
  validator move, or sanctioned-content-smoke designation).
  *Found by TEA during test design.*
- **Gap** (non-blocking): full-suite baseline failures pre-existing this story,
  recorded for the GREEN/finish comparison (any failure NOT in this list and
  not 96-1-RED is a regression): tests/orbital/test_perseus_cloud_systems_split.py
  (7 failed + 18 errors — story 98-1 yula content lag in this checkout),
  tests/protocol/test_api_contract_aside.py (docs/api-contract.md not found),
  tests/genre/test_road_warrior_vessel_calibration.py::test_mounted_rig_weapons_carry_vehicle_damage
  (epic 86-5 pending), tests/server/test_chargen_complete_no_hp_leak.py::test_chargen_complete_log_uses_edge_not_hp,
  tests/server/test_culture_context.py::test_connect_to_evropi_populates_filtered_world_context,
  tests/server/test_lore_rag_wiring.py::test_player_action_drives_full_lore_pipeline.
  Affects `.session/96-1-session.md` (baseline ledger only). *Found by TEA during test design.*

### Dev (implementation)

- **Gap** (non-blocking): live-play strike damage has been silently dead for
  epic-94-migrated packs (space_opera, heavy_metal etc.) — every catalog-weapon hit
  logged `dice.damage_spec_missing` and dealt 0 HP because the priority-3 lookup read
  genre-tier `pack.inventory` only. Fixed this story; old playtest logs showing the
  warning are this bug, not content errors.
  Affects `sidequest/server/dispatch/damage_roll.py` (fixed here; recommend
  playtest-verify of live space_opera combat). *Found by Dev during implementation.*
- **Improvement** (non-blocking): `tests/fixtures/genre_packs` is a symlink alias of
  `tests/fixtures/packs` (one physical tree) — docs/helpers that describe them as two
  parallel dirs (incl. the TEA fixture contract wording) slightly overstate the
  topology; consider a README in tests/fixtures/.
  Affects `tests/fixtures/` (documentation only). *Found by Dev during implementation.*

### Reviewer (review)

- **Gap** (non-blocking, Medium): absent projection.yaml escapes the new
  visibility-coverage check — elemental_harmony ships none, so it runs with a
  pass-through ProjectionFilter while the validator passes it. Pre-existing
  (the old test's EH param was skip-dead since #726), but now a visible content
  decision: require projection.yaml in pack_schema.yaml's required files, or
  make `_validate_projection` warn on absence for shipping packs.
  Affects `sidequest-content/pack_schema.yaml` or
  `sidequest/cli/validate/pack.py` (policy decision needed).
  *Found by Reviewer during review.*
- **Improvement** (non-blocking, Low): enforcement of the visibility coverage is
  operator-run only (`just validate-pack`); there is no content CI. Fine for a
  personal project's authoring flow, but worth wiring into the content-PR
  checklist for homebrew authors (the Jade path).
  Affects `justfile` / authoring docs. *Found by Reviewer during review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)

- **Engine fix shipped beyond fixture authoring (world-tier strike damage)**
  - Spec source: context-story-96-1.md, Scope ("any fixture infrastructure needed")
  - Spec text: "In scope: the server tests skipped by #726 as content-coupled; any
    fixture infrastructure needed to rewrite them."
  - Implementation: Threaded `world_slug` through `RulesetModule.resolve_damage` →
    `resolve_damage_spec_from_beat_and_actor` → `resolve_inventory`, touching
    dice.py (3 sites) + narration_apply.py (opposed path).
  - Rationale: TEA's tests pin the production world-REPLACE path; without the fix the
    catalog lookup reads genre-tier only and strike damage is silently dead — in the
    fixtures AND in live play for every migrated pack. Authoring a genre-tier fixture
    inventory instead would have papered over a real production regression
    ("never say the right fix is X and then do Y").
  - Severity: moderate (production behavior change — it un-breaks live combat damage)
  - Forward impact: live space_opera/heavy_metal strike damage resumes ablating HP;
    recommend a playtest-verify; sibling story 96-2 unaffected.
- **Fixture packs are full frozen copies, not minimal synthetic YAML**
  - Spec source: .session/96-1-session.md, TEA Fixture-Authoring Contract
  - Spec text: "freeze values from what live space_opera shipped" (values, not files)
  - Implementation: Copied complete genre + world YAML trees (incl. barsoom flavor
    prose, legends, cultures) rather than hand-minimizing each file.
  - Rationale: `load_genre_pack` requires the full world file set (lore/tropes/
    char_creation/openings/...); frozen known-good copies are the established
    test_genre precedent and survive loader-schema tightening better than
    hand-minimized YAML.
  - Severity: minor
  - Forward impact: fixture tree is larger than strictly necessary (~15k lines);
    safe to trim opportunistically later.
- **Ride-along lint fixes outside story scope**
  - Spec source: context-story-96-1.md, Scope ("Out of scope: unrelated changes")
  - Spec text: "Out of scope: ... unrelated changes."
  - Implementation: `ruff check --fix` repaired 2 pre-existing findings on develop
    (telemetry spans `__init__` import sort, war_rig test unused import).
  - Rationale: `just server-lint` (a story gate) fails on develop without them;
    both are mechanical one-liners.
  - Severity: minor
  - Forward impact: none.

### Reviewer (audit)

- **AC2 narrowed to the rewritten inventory** → ✓ ACCEPTED by Reviewer: the epic names
  the #726 skips as the debt; residual couplings are catalogued as a follow-up finding,
  and the sanctioned content smokes are correctly designated.
- **test_rules_route_against_live_tea_and_murder retired** → ✓ ACCEPTED by Reviewer:
  doubly stale (route deleted in 100-12; behavior pinned fixture-first by 100-6 tests);
  AC-1 explicitly allows retirement with rationale, which is in-file.
- **Visibility sweeps moved to the pack validator** → ✓ ACCEPTED by Reviewer: right
  layer per the epic doctrine; I verified the wiring live (all 11 packs validated;
  negative control fires). One residual gap (absent projection.yaml) logged as a
  Medium finding rather than reversal — the old enforcement for that case was
  already skip-dead.
- **Previously-passing seam-sharing tests ride the fixture** → ✓ ACCEPTED by Reviewer:
  forking the harnesses would have preserved the coupling; their RED window closed
  within the same story (GREEN restored them, full suite verified).
- **Engine fix beyond fixture authoring (world-tier strike damage)** → ✓ ACCEPTED by
  Reviewer: required by the pinned tests AND un-breaks live combat damage for
  migrated packs; reuses the existing resolve_inventory seam with its OTEL span;
  all four call sites threaded (both resolution paths). Severity "moderate" is
  honest; playtest-verify recommended at finish.
- **Fixture packs are full frozen copies** → ✓ ACCEPTED by Reviewer: test_genre
  precedent; loader requires the full world file set; freeze-don't-minimize survives
  schema tightening. Trim opportunistically later (Low note on the barsoom prose in
  world.yaml).
- **Ride-along lint fixes** → ✓ ACCEPTED by Reviewer: two mechanical one-liners that
  unblock the server-lint gate; re-scanned, no new issues introduced.

### TEA (test design)

- **AC2 narrowed from "no server test depends on a live pack" to the rewritten inventory**
  - Spec source: context-story-96-1.md, AC-2
  - Spec text: "No server test depends on a live pack/world slug from sidequest-content."
  - Implementation: All #726-skipped tests (plus tests sharing their loading seams) are
    decoupled; remaining live couplings are catalogued as a Delivery Finding instead of
    rewritten here.
  - Rationale: The epic names the #726 skips as the debt; a whole-suite decoupling audit
    is a separate story's worth of scope (8 pts already). Sanctioned content smokes
    (world-loads-clean, keeper-leak) arguably SHOULD stay live.
  - Severity: minor
  - Forward impact: follow-up story needed for the residual couplings (finding logged).
- **test_rules_route_against_live_tea_and_murder retired, not rewritten**
  - Spec source: context-story-96-1.md, AC-1
  - Spec text: "rewritten against fixtures or explicitly retired with rationale"
  - Implementation: Deleted with an in-file rationale comment.
  - Rationale: Doubly stale — drove the server-rendered HTML route deleted in the
    100-12 SPA cutover, and its surviving behavior (rules projection sections +
    keeper firewall) is already pinned fixture-first by
    tests/server/test_reference_rules_projection.py (story 100-6).
  - Severity: minor
  - Forward impact: none (AC-1 explicitly allows retirement).
- **Visibility sweeps moved to the pack validator instead of fixture parametrization**
  - Spec source: context-epic-96.md (doctrine: "validators validate content, tests test fixtures")
  - Spec text: "rewrite against fixtures — story 94-4" (the skip reason)
  - Implementation: Deleted the two per-shipping-pack sweeps in
    tests/game/projection/test_visibility_tag_rule.py; pinned a NEW contract
    `validate_visibility_coverage(rules) -> list[str]` in
    sidequest/game/projection/validator.py, wired into `pf validate pack`
    (validator-CLI severity only — explicitly NOT a load gate; a pinning test
    guards `validate_projection_rules` against growing the requirement).
  - Rationale: Asserting fixture packs carry visibility rules tests nothing about the
    engine; the real requirement is on shipping CONTENT, which is the validator's
    jurisdiction. This is the only rewrite that adds production code for Dev (the
    validator function + pack.py wiring).
  - Severity: minor
  - Forward impact: GREEN must implement validate_visibility_coverage + pack.py wiring;
    content repo CI gets the coverage check for free via pf validate pack.
- **Previously-PASSING tests sharing the rewritten seams now ride the fixture too**
  - Spec source: context-story-96-1.md, Scope ("the server tests skipped by #726")
  - Spec text: in-scope list = the skipped tests
  - Implementation: Tests that share module fixtures/helpers with skipped ones were
    repointed wholesale rather than forking the helpers: the four sealed-letter
    instantiation tests, test_initiative_rolled_and_persisted_on_instantiation,
    test_ship_combat_resolves_on_hull_depletion_vs_ship_ac, all of
    test_dogfight_shot_wiring.py, and test_dice_throw_completes_pending_shot. They are
    temporarily RED (FixturePackNotFound) until Dev authors the fixture packs.
  - Rationale: Forking _seated_combat/snap_with_pilot into live+fixture variants would
    duplicate harnesses and preserve the exact coupling the story removes.
  - Severity: minor
  - Forward impact: GREEN restores them; reviewer should not read their RED as a
    regression (they are part of the verified RED set).