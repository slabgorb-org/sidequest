---
story_id: "120-1"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 120-1: caverns_and_claudes (WWN) genre baseline -> 100% verbatim

## Story Details
- **ID:** 120-1
- **Jira Key:** (not used)
- **Workflow:** tdd
- **Repos:** content,server
- **Stack Parent:** none
- **Branch:** feat/120-1-caverns-wwn-verbatim-baseline

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-15T21:58:11Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-15T13:22:26Z | 2026-06-15T13:25:04Z | 2m 38s |
| red | 2026-06-15T13:25:04Z | 2026-06-15T13:35:12Z | 10m 8s |
| green | 2026-06-15T13:35:12Z | 2026-06-15T21:50:14Z | 8h 15m |
| review | 2026-06-15T21:50:14Z | 2026-06-15T21:58:11Z | 7m 57s |
| finish | 2026-06-15T21:58:11Z | - | - |

## Delivery Findings

**SM → TEA (RED framing).** This is content+server, NOT content-only, so it gets a real RED
phase (not the validate-only path content sweeps usually take). Aim the failing test at the
SERVER seam: assert `resolve_inventory(pack, world)` resolves **every** kit id across all
caverns_and_claudes worlds AND that the 31 (formerly-unprovenanced) genre item_catalog items
carry honest provenance — `mode=verbatim, srd=wwn, license=wn-free`, with a populated `srd_ref`.
GREEN = the content migration (source the 31 from the WWN SRD at GENRE tier; MOVE no-analog
plot devices to WORLD tier as `mode=bespoke`, each logged as a Design Deviation here).

**Kit-trap guard (ADR-140 / `world-replaces-genre`).** Any new `worlds/<w>/inventory.yaml`
MUST copy genre `starting_equipment`/`starting_gold`/`currency` verbatim or classes ship empty
kits. A regression test that loads each caverns world and asserts non-empty resolved kits is
the cheapest way to pin this. Precedent packs already 100% WWN-verbatim: elemental_harmony,
heavy_metal. World-tier bespoke precedent: mutant_wasteland rad_pills/geiger.

**Out of scope:** the D3 validator (that is 120-3 — do NOT touch it here).

## Sm Assessment

**Routing:** tdd / phased → TEA for RED phase. Justified: this is content+server (not the
content-only validate path) — there is a genuine server-side assertion to drive the cycle
(`resolve_inventory` resolves every caverns kit id + provenance shape on the 31 items).

**Acceptance (what "done" looks like):**
1. All 31 formerly-unprovenanced caverns_and_claudes GENRE `item_catalog` items carry honest
   provenance: `mode=verbatim, srd=wwn, license=wn-free`, non-empty `srd_ref`, sourced where a
   WWN SRD analog exists.
2. Items with NO WWN analog (genuine plot devices) MOVED to WORLD tier as `mode=bespoke`, each
   logged below under Design Deviations.
3. `resolve_inventory(pack, world)` resolves every kit id across ALL caverns_and_claudes worlds
   (no empty kits); kit-trap guard test in place for any new world `inventory.yaml`.
4. Validator (120-3) untouched.

**Risk / watch-items:** the world-replaces-genre kit trap (ADR-140) — a world `inventory.yaml`
that omits `starting_equipment`/`starting_gold`/`currency` silently ships empty class kits.
Pin with a load-every-world regression test. Precedents to mirror: elemental_harmony &
heavy_metal (100% WWN-verbatim genres); mutant_wasteland (world-tier bespoke moves).

### TEA (test design)
- No upstream findings during test design. The story scope is well-formed: the RED
  target (31 unprovenanced caverns_and_claudes genre `item_catalog` items) reproduced
  exactly, the model + resolver seams are all present, and the guard tests confirm the
  pack currently loads and its chargen kits resolve. One non-blocking note is carried
  forward as a deviation (the genre→world relocation set is intentionally not pinned by id).

### Dev (implementation)
- **Gap** (blocking): the verbatim sweep cascades into caverns *chargen* (`equipment_tables.yaml` —
  Warrior/Mage/Expert `class_tables` + `guaranteed_grants`), which the story scope did not name.
  Of the 31 legacy ids, 17 have WWN analogs (mechanical repoint to `wwn_*`) and **7 moved to the
  beneath_sunden world tier** (`lockpicks, ten_foot_pole, chalk, spellbook, component_pouch,
  helmet_iron, potion_healing[_greater]`) — all referenced by the genre chargen kits. Production
  chargen enriches via `resolve_inventory(pack, world)` (chargen_mixin.py:1242), so beneath_sunden
  can still resolve them. **Keith ruled (2026-06-15): Option B — world-tier kit override** (genre
  kits go WWN-pure; a NEW `worlds/<w>/equipment_tables.yaml` carries the dungeon-flavor slots +
  grants, merged over genre by the builder). That is a **server feature** (World model field +
  loader + CharacterBuilder merge + merge-semantics design + tests), beyond this green phase and
  beyond TEA's RED (which only covers the inventory contract). 120-1's green is **blocked** on it.
  *Found by Dev during implementation.* Affects `sidequest-server/sidequest/genre/` (loader, World
  model), `sidequest/game/builder.py` (kit merge), `genre_packs/caverns_and_claudes/equipment_tables.yaml`
  (+ new world override), and ~6 coupled chargen tests. **Recommend re-scope via SM** (see Dev note below).
- **RESOLVED (Dev green resume 2026-06-15):** the blocker above cleared — the re-scoped server feature
  shipped as **story 120-4** (world-tier equipment_tables override; loader + `resolve_equipment_tables` +
  CharacterBuilder per-slot merge), merged to server develop as PR #888. Keith confirmed (2026-06-15
  AskUserQuestion) to **fold the caverns equipment_tables reconciliation into 120-1's green** rather than
  file it separately. This pass completed the content half (genre WWN-pure + beneath_sunden override) and
  the coupled-test updates. *Found/resolved by Dev during implementation.*
- **Gap** (non-blocking): `tests/integration/test_cc_chargen_e2e.py` (4 tests) is PRE-EXISTING red on
  develop — a new `the_trade` background-selection scene was added to caverns `char_creation.yaml` (lines
  40+) but the e2e walker `_drive_chargen` (line 90) was not updated, so it reads `the_trade`'s
  `background` choices (`class_hint=None`) before reaching class selection. Independent of 120-1 (my diff
  does not touch `char_creation.yaml` or the e2e). **Forward impact:** when that walker is fixed,
  `test_e2e_warrior_kit_always_includes_exactly_one_heal_potion` must switch from genre-only
  `pack.equipment_tables` (line 57) to `resolve_equipment_tables(pack, "beneath_sunden")` — 120-1 moved the
  heal-potion guarantee to the world tier, so the genre-only path no longer grants it (production uses the
  world-merged path at `connect.py:935`, which is correctly wired and covered by
  `test_106_4_consumable_heal` + the new merge wiring test). Affects `tests/integration/test_cc_chargen_e2e.py`.
  *Found by Dev during implementation.*
- **Gap** (non-blocking): the WWN-combat-cutover beat failures (`test_wwn_caverns_dispatch` `cast_spell`,
  caverns/elemental_harmony/heavy_metal `committed_blow`/`cast_spell` missing from combat beats) are
  PRE-EXISTING epic-108 territory (ADR-143: WWN combat has no native beats; the legacy beat path at
  `narration_apply.py:5833` still looks them up). Independent of 120-1 (inventory/equipment_tables, not
  combat). Affects epic 108. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `resolve_equipment_tables` resolving a world with no `equipment_tables.yaml`
  to genre-only is silent — a `world_slug` typo or a genre `guaranteed_grants: {}` baseline yields zero
  heal grants for any future non-beneath_sunden caverns world with no fail-loud signal. Affects
  `sidequest-server/sidequest/server/dispatch/equipment_tables_resolve.py` (120-4 code; add a negative-confirmation
  OTEL attribute / builder-side `chargen.empty_kit_grants` event so the GM panel surfaces empty-grant resolution).
  Not triggered by 120-1's content (verified). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `_merge_equipment_tables` / `_append_by_key` silently creates an orphan kit for a
  mis-keyed world kit id (`warror_kit`) — the builder never requests it, so its gear/grants vanish with no error.
  Affects `sidequest-server/sidequest/server/dispatch/equipment_tables_resolve.py:34` (120-4; emit an OTEL warning for
  world-only `class_tables`/`guaranteed_grants` keys not present in genre). Also worth hardening
  `test_cc_beneath_sunden_merged_kits_resolve_against_world_catalog` to assert world kit keys ⊆ genre kit keys.
  Content correct today (no typo). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `apply_starting_loadout` falls through to `_item_dict_minimal` for an unresolved
  starting_equipment id and silently adds a mechanic-less stub item (counted as success). Affects
  `sidequest-server/sidequest/server/dispatch/chargen_loadout.py:242` (pre-existing 120-4/chargen code; add a
  `logger.warning` + OTEL event at the stub branch — No Silent Fallbacks). Not triggered by 120-1's verified content.
  *Found by Reviewer during code review.*

## Design Deviations

None at setup.

### TEA (test design)
- **Did not assert the specific genre→world relocation set (which of the 31 items move to the world tier)**
  - Spec source: SM Assessment (session) AC-2 / context-epic-120.md
  - Spec text: "Items with NO WWN analog (genuine plot devices) MOVED to WORLD tier as `mode=bespoke`, each logged below under Design Deviations."
  - Implementation: Tests assert the genre baseline is 100% verbatim and that every `starting_equipment` id still resolves; they do NOT pin which item ids relocate, nor that the world tier gains specific bespoke ids.
  - Rationale: verbatim sourcing legitimately renames ids (bare `torch` → `wwn_torch`), so an id-keyed relocation assertion would false-fail on correct work; *which* items lack a WWN analog is a Dev/Reviewer judgment logged as a deviation, not a fixed test contract. The kit-trap test (no dangling `starting_equipment` id) is the rename-safe safety net that still catches a dropped/forgotten item.
  - Severity: minor
  - Forward impact: Reviewer must confirm — from Dev's deviation log — that relocated items actually land at the world tier as `mode=bespoke` and that none were silently dropped.

### Dev (implementation)
- **Scope expansion: story converts from content-sweep to content + a server feature**
  - Spec source: SM Assessment (session), context-story-120-1.md (story scope: genre `item_catalog` verbatim sweep)
  - Spec text: "source the 31 unprovenanced genre item_catalog items from the WWN SRD ... MOVE genuinely-unique items ... to the world tier."
  - Implementation: completed the inventory work (genre `inventory.yaml` 100% verbatim; `worlds/beneath_sunden/inventory.yaml` created with 11 bespoke items + kit-trap copies). PAUSED before touching `equipment_tables.yaml`, because reconciling the genre chargen kits per Keith's Option-B ruling requires a new server capability (world-tier `equipment_tables` load + merge).
  - Rationale: the story named only `item_catalog`; the chargen-kit cascade + the chosen world-tier-override approach is a server feature with its own design (merge semantics) and RED tests. Free-handing an untested chargen-merge feature inside a content sweep's green phase violates TDD + "no half-wired features."
  - Severity: major (changes the story's shape and dependencies)
  - Forward impact: needs SM re-scope — a server story for "world-tier equipment_tables override" that 120-1 depends on/bundles; likely an Architect merge-semantics design pass → TEA RED → Dev green. Done WIP so far: genre inventory sweep + world inventory.yaml (option-agnostic; both A/B need them) — UNCOMMITTED on the feature branch.

### Dev note — concrete plan for the re-scoped server feature (Option B)
1. **Content:** genre `equipment_tables.yaml` → WWN-pure (repoint the 17 to `wwn_*`, drop the 7 world items from genre kits + the genre `guaranteed_grants` potion). NEW `worlds/beneath_sunden/equipment_tables.yaml` carrying the dungeon-flavor kit slots (`lockpicks`, `ten_foot_pole`, `chalk`, `spellbook`, `component_pouch`, `helmet_iron`) + the `guaranteed_grants` heal potion.
2. **Server:** `World` model gains `equipment_tables` (genre/models/pack.py); loader loads `worlds/<w>/equipment_tables.yaml`; `CharacterBuilder` merges world over genre — **per-slot append within each kit + world-provides `guaranteed_grants`** (the merge semantics Keith sketched in the Option-B preview). Builder needs world context wired to the merge.
3. **Tests:** loader-loads-world-equipment-tables; builder per-slot merge; beneath_sunden chargen e2e yields lockpicks/spellbook/potion; update the ~6 coupled tests (test_106_1_caverns_armor_content, test_cc_class_kits, test_cc_chargen_e2e, test_chargen_dispatch, test_chargen_persist_and_play, the equipment_tables wiring test) to the new ids / world-merged catalog.

### Dev (implementation — green resume 2026-06-15, post-120-4)
- **Folded the caverns equipment_tables reconciliation into 120-1's green (scope expansion past item_catalog)**
  - Spec source: story scope (session **Repos**/SM Assessment) — 120-1 named only the genre `item_catalog` verbatim sweep
  - Spec text: "source the 31 unprovenanced genre item_catalog items from the WWN SRD ... MOVE genuinely-unique items ... to the world tier."
  - Implementation: also rewrote genre `equipment_tables.yaml` to WWN-pure and authored `worlds/beneath_sunden/equipment_tables.yaml` (world override), because the item_catalog rename left every genre chargen-kit id dangling (regressing caverns chargen). Rode the merged 120-4 `resolve_equipment_tables` capability.
  - Rationale: shipping 120-1 inventory-only would knowingly regress caverns chargen (No half-wired features). Keith approved folding it in via AskUserQuestion 2026-06-15 (Option B was already his 2026-06-15 ruling; 120-4 unblocked it).
  - Severity: major (changes the story's committed shape; was the prior pass's "needs SM re-scope" finding, now resolved)
  - Forward impact: 120-3 (validator) and 120-2 (road_warrior) unaffected; the equipment_tables world-override pattern is now a worked precedent for any WWN/CWN pack whose verbatim sweep strands chargen kits.
- **leather_armor → wwn_linothorax (WWN AC-13 light armor) for the kit + content-AC test**
  - Spec source: tests/integration/test_106_1_caverns_armor_content.py (WWN_LEATHER_AC = 13)
  - Spec text: "leather = AC 13 (WWN SRD)"
  - Implementation: mapped the old `leather_armor` slot to `wwn_linothorax` (the SRD's AC-13 light armor; buff_coat is AC 12, war_shirt AC 11), in both the genre kits and the armor data-contract test.
  - Rationale: preserve the AC-13 "leather" role with the faithful WWN verbatim item; AC parity over name literalism (mechanics-first players read AC).
  - Severity: minor
  - Forward impact: none — slug stability is id stability; the test asserts the same AC-13 contract against the new id.
- **Updated 2 coupled tests + added 1 wiring test during green (Dev touching tests)**
  - Spec source: TEA Assessment (Dev guidance, GREEN) + server CLAUDE.md ("Every Test Suite Needs a Wiring Test")
  - Spec text: "update the ~6 coupled chargen tests ... to the new ids / world-merged catalog"
  - Implementation: (a) `test_cc_expert_kit_has_lockpicks` now asserts the WWN-pure genre kit omits lockpicks AND the world-merged kit re-adds them; (b) `test_106_1` armor id → wwn_linothorax; (c) NEW `test_cc_beneath_sunden_merged_kits_resolve_against_world_catalog` proves every world-merged kit id + grant resolves in the merged catalog (the loud guard for the rename cascade). Did NOT update `test_cc_chargen_e2e` (pre-existing-red on an unrelated `the_trade` scene — see Delivery Findings).
  - Rationale: the renamed ids/world-tier move legitimately require these test changes; the new wiring test is the refactor-stable behavior guard the cascade needed.
  - Severity: minor
  - Forward impact: Reviewer should confirm the wiring test is behavioral (resolves through `resolve_equipment_tables`/`resolve_inventory`, not source-grep) and that the e2e is left red for a documented pre-existing reason, not my change.

### Reviewer (audit)
- **TEA: "Did not assert the specific genre→world relocation set"** → ✓ ACCEPTED by Reviewer: sound — verbatim sourcing renames ids, so an id-keyed relocation assertion would false-fail; the kit-trap test is the rename-safe net. Reviewer independently confirmed all relocated items land at the world tier as `mode=bespoke` (11 items) and none were dropped (0 dangling, genre+merged catalogs).
- **Dev: "Scope expansion → content + a server feature" (prior pass, major)** → ✓ ACCEPTED by Reviewer: the pause + re-scope was the correct call at the time; the server feature shipped as 120-4 (PR #888, merged), and Keith approved folding the content half back into 120-1's green. Resolved.
- **Dev: "Folded the caverns equipment_tables reconciliation into 120-1's green" (green resume, major)** → ✓ ACCEPTED by Reviewer: shipping inventory-only would regress caverns chargen (the genre kits dangled). Keith-approved (AskUserQuestion 2026-06-15). The reconciliation is correct and rides the merged 120-4 capability — verified end-to-end.
- **Dev: "leather_armor → wwn_linothorax (WWN AC-13)" (minor)** → ✓ ACCEPTED by Reviewer: independently confirmed `wwn_linothorax.armor_class == 13`; faithful AC-13 light-armor analog (buff_coat=12, war_shirt=11). Sound.
- **Dev: "Updated 2 coupled tests + added 1 wiring test during green" (minor)** → ✓ ACCEPTED by Reviewer: all behavioral (no source-grep, confirmed by [SEC] subagent); the new wiring test is a genuine merge-resolution guard. One non-blocking hardening noted in Delivery Findings (wiring test iterates post-merge kit keys, so it would not catch a world-kit-key typo — content is correct today).
- No undocumented deviations found: the diff footprint is exactly content (inventory + equipment_tables, genre + world) + the three named test files; nothing diverged silently.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Content+server story — a genuine server-side assertion (`resolve_inventory` + provenance shape on the genre baseline, run through the real loader) drives the RED→GREEN cycle. Not the content-only validate-path.

**Test Files:**
- `sidequest-server/tests/genre/test_120_1_caverns_verbatim_baseline.py` — content-gated (real pack via `find_pack_path`, env-skips on `PackNotFound`); mirrors the 114-14 real-pack pattern. 5 tests.

**Tests Written:** 5 tests. RED today: 2 failing (as designed). Guards: 3 passing.
**Status:** RED — ready for Dev (GREEN = the content sweep).

### Rule Coverage

| AC / Rule | Test | Status |
|-----------|------|--------|
| AC1 — no unprovenanced genre items | `test_caverns_genre_baseline_has_no_unprovenanced_items` | **failing (RED)** — lists all 31 ids |
| AC1 — genre baseline 100% WWN-verbatim (mode/srd/license/srd_ref) | `test_caverns_genre_baseline_is_fully_wwn_verbatim` | **failing (RED)** — 31 offenders |
| AC2 — plot devices to WORLD tier, never genre bespoke | `test_caverns_genre_baseline_carries_no_bespoke` | passing (guard, must stay green) |
| AC3 — `resolve_inventory` kits resolve / no empty kits (kit-trap, ADR-140) | `test_caverns_kits_resolve_no_dangling_ids` | passing (guard, must stay green) |
| Wiring — real loader gate accepts the pack | `test_caverns_pack_loads_clean` | passing (guard) |
| AC4 — validator untouched (120-3) | n/a — test file neither imports nor edits `_validate_genre_baseline_no_bespoke` | satisfied |

**Rules checked:** Server CLAUDE.md testing rules honored — behavior-through-the-real-loader, NO source-text wiring assertions; the wiring test goes through `load_genre_pack` (the production gate). No new types/constructors are introduced by this story (it's content data against the existing `ItemProvenance` model), so no constructor/Deserialize-rejection rule tests apply.
**Self-check:** 0 vacuous tests — every test aggregates offenders and asserts an empty/non-empty list with a descriptive message; no `assert True`, no always-None checks.

**RED evidence (testing-runner, RUN_ID 120-1-tea-red):** 2 failed / 3 passed; both failures are assertion errors (not import/collection) citing the exact 31 unprovenanced ids.

### Dev guidance (GREEN)
- Source each of the 31 verbatim from the WWN SRD AT THE GENRE TIER where an analog exists, using the elemental_harmony/heavy_metal shape: `provenance: {mode: verbatim, srd: wwn, srd_ref: "WWN SRD §...", license: wn-free, extracted_by: ...}`.
- MOVE genuinely-unique plot devices (no WWN analog) to `genre_packs/caverns_and_claudes/worlds/beneath_sunden/inventory.yaml` as `mode: bespoke` — log each move as a Dev deviation.
- **Kit trap (ADR-140):** if you create `worlds/beneath_sunden/inventory.yaml`, it REPLACES genre `starting_equipment`/`starting_gold`/`currency` wholesale — copy them verbatim or kits ship empty. If you rename ids (`torch` → `wwn_torch`), update `starting_equipment` to match (the kit-trap test will catch a miss).
- Do NOT touch the D3 validator (`loader.py::_validate_genre_baseline_no_bespoke`) — that's 120-3.

**Handoff:** To Dev (Inigo Montoya) for the content sweep.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-content/genre_packs/caverns_and_claudes/inventory.yaml` — genre item_catalog 100% WWN-verbatim (68 items, all `mode=verbatim`/`srd=wwn`/`license=wn-free`/`srd_ref`); 0 bespoke at genre tier (prior-pass commit on branch).
- `sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden/inventory.yaml` — 11 no-WWN-analog plot devices as `mode=bespoke`; kit-trap copies of `starting_equipment`/`starting_gold`/`currency` (prior-pass commit on branch).
- `sidequest-content/genre_packs/caverns_and_claudes/equipment_tables.yaml` — genre chargen kits repointed to the WWN-verbatim `wwn_*` catalog; world-tier items dropped from genre kits; `guaranteed_grants` emptied (heal potion is world-tier now). **(this pass)**
- `sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden/equipment_tables.yaml` — NEW world override; re-adds dungeon-flavor slots + heal-potion grant, merged world-over-genre by `resolve_equipment_tables` (120-4). **(this pass)**
- `sidequest-server/tests/genre/test_120_1_caverns_verbatim_baseline.py` — the TEA RED tests (rebased onto develop).
- `sidequest-server/tests/genre/test_cc_class_kits.py` — lockpicks test → world-merged; new world-merge wiring test. **(this pass)**
- `sidequest-server/tests/integration/test_106_1_caverns_armor_content.py` — leather_armor → wwn_linothorax (AC 13). **(this pass)**

**Tests (GREEN):**
- `test_120_1_caverns_verbatim_baseline.py` — **5/5 pass** (the story contract).
- `test_cc_class_kits.py` — **7/7 pass** (incl. new `test_cc_beneath_sunden_merged_kits_resolve_against_world_catalog`).
- `test_120_4_world_equipment_tables_override.py` — **8/8 pass** (capability unbroken).
- Caverns chargen sweep (`test_106_1*` armor/wire, `test_106_4_consumable_heal`, `test_chargen_loadout`/`dispatch`/`persist_and_play`) — pass.
- Full `tests/genre/` — **998 passed, 5 failed, 50 skipped**; all 5 failures PRE-EXISTING (epic-108 WWN-combat beats in caverns classes.yaml + elemental_harmony + heavy_metal; ADR-107 room binding) — none touch inventory/equipment_tables, none in files this story changed. Verified via isolated tracebacks + diff footprint (no banned prior-commit runs).
- `ruff format --check` + `ruff check` clean on edited tests.

**Branch:** `feat/120-1-caverns-wwn-verbatim-baseline` (content + server) — both pushed to origin.

**Handoff:** To Reviewer (Westley) for review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 21/21 pass, lint+format clean; 1 note (holy_symbol world-only, unused-in-kit) | confirmed 0, dismissed 0, deferred 1 (holy_symbol → verified intentional) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — domain assessed by Reviewer ([EDGE] below) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 4 (1 medium genre `{}`-grants, 1 medium typo'd-world-kit, 1 low empty-slot, 1 medium chargen_loadout stub) | confirmed 0 blocking; 4 captured as non-blocking Delivery Findings (all in 120-4 production code or latent/documented; content verified correct) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — domain assessed by Reviewer ([TEST] below) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — domain assessed by Reviewer ([DOC] below) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — domain assessed by Reviewer ([TYPE] below) |
| 7 | reviewer-security | Yes | clean | 0 violations (No-Silent-Fallbacks, No-Stubbing, No-Source-Text-Wiring, content-coupling all clean) | confirmed 0, dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — domain assessed by Reviewer ([SIMPLE] below) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — domain assessed by Reviewer ([RULE] below) |

**All received:** Yes (3 enabled returned: preflight, silent-failure-hunter, security; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 0 confirmed blocking, 0 dismissed, 5 deferred to Delivery Findings (4 silent-failure non-blocking + 1 holy_symbol verified-intentional)

## Reviewer Assessment

**Verdict:** APPROVED

A content-YAML + test-only change (the chargen merge capability is the already-merged, already-reviewed 120-4). The deliverable — caverns_and_claudes genre baseline 100% WWN-verbatim, chargen `equipment_tables` reconciled WWN-pure with a beneath_sunden world override — is correct, behaviorally tested, and green. I independently verified the merge resolution rather than trusting the green suite.

**Independent verification (Reviewer ran the real resolvers, not just the tests):**
- Genre `equipment_tables`: 17 ids, **0 dangling** vs the genre catalog, **0 non-`wwn_` ids** — WWN-purity holds; `guaranteed_grants == {}`.
- beneath_sunden world-merged: 23 kit+`tables` ids (incl. the top-level random-table pool the wiring test skips), **0 dangling** vs the merged catalog; guaranteed-grant ids `potion_healing`/`potion_healing_greater` resolve, all four kits carry the guarantee — the heal guarantee is **not** silently lost in the genre→world move.
- `wwn_linothorax.armor_class == 13` — faithful AC-13 leather analog.

### Rule Compliance (rule_checker disabled — enumerated by Reviewer)
- **No Silent Fallbacks (SOUL/CLAUDE):** the content introduces no new silent fallback. The silent paths [SILENT] flagged (genre `{}`-grants for future worlds; typo'd world-kit orphan; `_item_dict_minimal` stub) live in **120-4 production code** (`equipment_tables_resolve.py`, `builder.py`, `chargen_loadout.py`) — not this diff — and are not triggered by the (verified-correct) content. Captured as non-blocking Improvements. COMPLIANT for this diff.
- **No Stubbing:** world `inventory.yaml` (11 items) and `equipment_tables.yaml` are fully authored with real stats/provenance — confirmed by [SEC]. COMPLIANT.
- **No Source-Text Wiring Tests (server CLAUDE.md):** every assertion in all 3 test files drives `load_genre_pack`/`GenreLoader.load`/`resolve_equipment_tables`/`resolve_inventory` and inspects the object graph — zero `read_text`/source-grep. Confirmed by [SEC]. COMPLIANT.
- **Every Test Suite Needs a Wiring Test:** `test_cc_beneath_sunden_merged_kits_resolve_against_world_catalog` is a genuine behavioral wiring test through the production resolvers. COMPLIANT.
- **Bind the Ruleset, Don't Balance It (ADR-143/SOUL):** the sweep removes bespoke caverns gear in favor of the WWN catalog rather than re-stating mechanics; the "would inject Shock" 114-4 concern is correctly resolved as doctrine (WWN's gear IS the rulebook). COMPLIANT.
- **OTEL Observability Principle:** does not bind — 120-1 touches no backend subsystem (content + tests). The merge-path OTEL (`resolved_equipment_tables` span) is 120-4's, already present.
- **No new types:** content data against existing `EquipmentTables`/`GuaranteedGrant` (extra:forbid) models — the YAML loaded clean (loader gate green), so no schema violation.

### Observations
- `[VERIFIED]` Genre `equipment_tables` is WWN-pure — evidence: Reviewer cross-check, 17 ids, 0 non-`wwn_`, 0 dangling vs `pack.inventory.item_catalog`. Complies with ADR-145 D3 (verbatim genre baseline).
- `[VERIFIED]` World-merge resolves end-to-end incl. heal guarantee — evidence: `resolve_equipment_tables`+`resolve_inventory` for beneath_sunden, 0 dangling across class_tables, tables, and grants. Complies with No-Silent-Fallbacks (no lost guarantee).
- `[SEC]` Tests are behavioral, not source-text wiring — confirmed clean at `tests/genre/test_cc_class_kits.py`, `tests/integration/test_106_1_caverns_armor_content.py`.
- `[SILENT]` `[MEDIUM→LOW]` genre `guaranteed_grants: {}` gives future non-beneath_sunden caverns worlds no heal grant — `equipment_tables.yaml:146`. Non-blocking: latent (only beneath_sunden exists), documented by Dev, and inherent to ADR-140 world-tier flavor. Deferred to Delivery Findings.
- `[SILENT]` `[LOW]` the new wiring test iterates post-merge `class_tables` keys, so a future world-kit-key typo (`warror_kit`) would orphan silently and still pass — `tests/genre/test_cc_class_kits.py`. Content is correct today (no typo; verified). Non-blocking test-hardening, deferred.
- `[SILENT]` `[LOW]` `chargen_loadout.py:242` `_item_dict_minimal` stubs unresolved starting_equipment ids silently — **pre-existing 120-4/chargen production code, not in this diff**; not triggered by the verified-correct content. Deferred as Improvement.
- `[TEST]` (analyzer disabled — Reviewer) The updated `test_cc_expert_kit_has_lockpicks` correctly asserts genre-absence AND world-merge-presence (production path); not vacuous. The new wiring test aggregates dangling ids into a dict and asserts empty — not vacuous.
- `[DOC]` (comment-analyzer disabled — Reviewer) Comments are accurate: the 114-4 reconciliation flag is properly retired, id-mapping comments match the actual ids, and the world-override docstring correctly states the 120-4 merge semantics. No stale/misleading comments.
- `[EDGE]` (edge-hunter disabled — Reviewer) Edge: `mage_kit utility: []` at genre tier ships an empty slot if the world override is absent — only relevant under a loader failure (would itself be loud) or a future non-beneath_sunden world; not a current path.
- `[TYPE]` (type-design disabled — Reviewer) No new types; YAML conforms to `EquipmentTables`/`GuaranteedGrant` `extra:forbid` models (loader gate passed).
- `[SIMPLE]` (simplifier disabled — Reviewer) No over-engineering: the world override is the minimal per-slot append; the wiring test is concise. No dead code (the inventory sweep deletes the legacy bespoke block rather than leaving it).
- `[RULE]` (rule-checker disabled — Reviewer) See Rule Compliance above — all applicable rules COMPLIANT for this diff.

### Pre-existing failures (not regressions — Reviewer confirmed by diff footprint)
The diff is exactly `{inventory,equipment_tables}.yaml` (genre+world) + 3 named test files. The 5 failures Dev flagged (`test_cc_chargen_e2e` ×4 on the develop-side `the_trade` scene; `test_wwn_caverns_dispatch` `cast_spell` at `narration_apply.py:5833`, epic-108) are in files this diff does not touch. Accepted as pre-existing.

### Devil's Advocate
Let me argue this is broken. **First attack — the heal potion silently vanished.** The Dev emptied genre `guaranteed_grants` to `{}`. If the world override's `guaranteed_grants` were mis-keyed, or `_append_by_key` treated `{}` as an explicit "wipe," every caverns character would lose their guaranteed heal — a real player-facing regression (Carl-the-Cleric's 2026-05-06 zero-resource failure mode). **Rebuttal:** I ran the real resolver — all four kits resolve `potion_healing`/`potion_healing_greater`, 0 dangling; `_append_by_key` unions genre+world, and `{}` is a clean base, not a wipe. Disproven. **Second attack — a confused content author.** A future author adds `caverns_and_claudes/worlds/new_world` without an `equipment_tables.yaml`; their mages get an empty utility slot and nobody gets a heal, silently. **Rebuttal:** real, but latent — caverns has only beneath_sunden today, the Dev documented it as a forward-impact finding, and it is the intended ADR-140 model (flavor lives in the world). I captured it for follow-up rather than blocking correct work. **Third attack — the wiring test is theater.** It iterates post-merge kit keys, so a typo'd world kit would orphan and the test would still pass. **Rebuttal:** true as a future-typo guard gap, but the test catches the actual cascade it was written for (dangling ids), and the content has no typo (verified). A defense-in-depth note, not a defect. **Fourth attack — the AC mapping is wrong.** `leather_armor`→`wwn_linothorax`: linothorax is laminated linen, not leather; mechanics-first Sebastien/Jade would notice. **Rebuttal:** the gate is AC parity (old leather = AC 13), and linothorax is the SRD's AC-13 light armor (buff_coat=12 would have changed the number); the Dev chose AC fidelity over name literalism, which is the correct call for a verbatim sweep. **Fifth attack — stressed filesystem / partial load.** If the world `item_catalog` partially loads, `_item_dict_minimal` silently stubs the missing id. **Rebuttal:** real silent-fallback, but pre-existing 120-4/chargen code not in this diff, and not triggered by correct content. Net: every attack either disproves or resolves to a non-blocking, out-of-diff, or latent item. No Critical/High. The work is sound.

**Data flow traced:** chargen → `connect.py:935` `resolve_equipment_tables(pack, world_slug)` (world-over-genre append) + `resolve_inventory` → `builder.with_equipment_tables` → kit rolls + guaranteed grants enriched from the merged catalog. Safe: every merged id resolves (verified, 0 dangling).
**Pattern observed:** world-tier override mirroring `resolve_inventory` — `worlds/beneath_sunden/equipment_tables.yaml` at the merge contract in `equipment_tables_resolve.py:34`.
**Error handling:** verbatim baseline is enforced by the loader gate (`test_caverns_pack_loads_clean`) + the D3 validator (untouched, 120-3); dangling kit ids are caught by the new behavioral wiring test.
**Handoff:** To SM for finish-story.