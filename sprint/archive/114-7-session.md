---
story_id: "114-7"
jira_key: ""
epic: "114"
workflow: "tdd"
---
# Story 114-7: space_opera — de-triplicate world catalogs, hoist shared core, add world-distinct gear, backfill SWN tech levels

## Story Details
- **ID:** 114-7
- **Jira Key:** (none — Jira not configured)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-15T15:56:54Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-15T10:36:47Z | 2026-06-15T14:39:39Z | 4h 2m |
| red | 2026-06-15T14:39:39Z | 2026-06-15T15:16:16Z | 36m 37s |
| green | 2026-06-15T15:16:16Z | 2026-06-15T15:32:12Z | 15m 56s |
| review | 2026-06-15T15:32:12Z | 2026-06-15T15:44:28Z | 12m 16s |
| green | 2026-06-15T15:44:28Z | 2026-06-15T15:52:07Z | 7m 39s |
| review | 2026-06-15T15:52:07Z | 2026-06-15T15:56:54Z | 4m 47s |
| finish | 2026-06-15T15:56:54Z | - | - |

## Sm Assessment

**Story:** 114-7 — space_opera SWN inventory: de-triplicate world catalogs, hoist shared
core, add world-distinct gear, backfill SWN tech levels. Epic 114, repo=content, tdd (phased).

**Setup actions:**
- Fresh-pulled orchestrator main + fetched subrepos before claiming (no stale-clone risk).
- Verified this is genuinely fresh work: no 114-7 commit on `origin/develop`, no existing
  feature branch in sidequest-content.
- Confirmed the defect first-hand: the three world `inventory.yaml` files are byte-identical
  (md5 `80a030e3…`, 278 lines each), zero `tech_level` tags, zero world-distinct gear.
- Branch `feat/114-7-space-opera-inventory-srd` created in sidequest-content (base=develop).
- Story context (`sprint/context/context-story-114-7.md`) enriched by SM from the 2026-06-14
  inventory audit — it carries the SWN derive-only constraint, the WN-family item schema, the
  four scope clauses, and the ADR-140 placement open question.

**Routing:** Phased tdd workflow → next phase `red`, owner **TEA (The Architect)**.

**Load-bearing note for TEA:** SWN's free edition has **no open license** → gear must be
**derived against the SWN schema, NOT copied verbatim** (this is the key contrast with sibling
114-12, which is CC0 verbatim). And: where the "shared core" lives (genre-tier baseline + ADR-121
per-field world overrides vs. world-tier shared include) is an **OPEN DESIGN QUESTION** I have
deliberately not prescribed — it's TEA/Architect's call in RED. Whatever lands must keep ADR-140
(world owns the catalog) honest.

**Blockers:** None. **Jira:** not configured for this project (tracked in sprint YAML) — claim
step explicitly skipped.

## TEA Assessment

### Red Phase (test writing)

**Tests Required:** Yes
**Reason:** This is a content/data story with real, machine-checkable contracts
(genre-tier SWN baseline, provenance, tech_level, de-triplication, resolver wiring).
Not a chore bypass.

**Test Files:**
- `sidequest-server/tests/genre/test_114_7_space_opera_swn_inventory.py` — 12 tests
  (mirrors the sibling `test_114_8_mutant_wasteland_awn_inventory.py` pattern).

**Test vehicle note:** sidequest-content has **no test harness** (no pyproject/tests dir).
The only vehicle is server-side pytest that loads the pack via `sidequest.genre.loader`
— exactly how siblings 114-4/114-5/114-8 were tested. The test lives on a matching
server branch `feat/114-7-space-opera-inventory-srd` (off `origin/develop`); commit
`3ed7dfde`. **This means the story spans content + server (test) — see Delivery Findings.**

**Tests Written:** 12 tests covering the 4 story clauses + ADR-145 invariants + 1 wiring test.
**Status:** RED — 11 failing, 1 passing guard (`test_pack_loads_clean_and_binds_swn`, locks
the SWN-binding precondition). Verified via `uv run pytest -n0` (not testing-runner, which
hallucinates counts).

### Rule Coverage

| Rule / invariant | Test(s) | Status |
|------------------|---------|--------|
| ADR-145 D3 — hoist a genre-tier SWN baseline | `test_genre_tier_swn_baseline_exists` | failing |
| ADR-145 D2 — every baseline item carries provenance | `test_every_genre_baseline_item_carries_provenance` | failing |
| ADR-145 **D4 — SWN is VERBATIM not derived** (the conflict) | `test_genre_baseline_is_swn_verbatim_sourced`, `test_no_genre_baseline_item_uses_derived_mode`, `test_verbatim_items_are_swn_wn_free_with_srd_ref` | failing |
| ADR-145 D3 — no bespoke at genre tier (world-tier privilege) | `test_genre_baseline_has_no_bespoke_items` | failing |
| Clause 4 — backfill SWN tech_level tags | `test_baseline_backfills_tech_level_tags`, `test_every_swn_weapon_and_armor_declares_tech_level` | failing |
| Clause 1 — de-triplicate world catalogs | `test_world_catalogs_are_no_longer_triplicated` | failing |
| Clause 3 — world-distinct gear per world | `test_each_world_has_distinct_gear` | failing |
| "Every Test Suite Needs a Wiring Test" (CLAUDE.md) | `test_resolve_inventory_merges_swn_baseline_into_each_world` | failing |
| SOUL — Bind the Ruleset, Don't Balance It (content edition) | the verbatim pins above | failing |

**Rules checked:** Python lang-review checklist (non_exhaustive enums, validated
constructors, Deserialize bypass, etc.) is **N/A** here — the RED phase adds no production
code and the GREEN deliverable is YAML data validated against the *existing* `CatalogItem`/
`ItemProvenance` Pydantic models (whose own validators are already covered). The applicable
rubric is the ADR-145 D2/D3/D4 provenance invariants + the wiring rule, all covered above.
**Self-check:** 0 vacuous tests. The two absence-tests (`no_derived`, `no_bespoke`) are
paired with positive existence tests (`verbatim_sourced`), so neither passes vacuously.

**Handoff:** To Dev (Agent Smith) for GREEN — create the genre-tier SWN baseline + de-triplicated
world overrides (content), making all 12 tests pass on the server branch.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed — content** (branch `feat/114-7-space-opera-inventory-srd`, commit `b0156f8`, pushed):
- `genre_packs/space_opera/inventory.yaml` (**NEW**) — genre-tier SWN baseline: 15 standard
  items (weapons/armor/consumables/tools), each reproducing an SWN SRD equipment entry
  **VERBATIM** (`mode=verbatim, srd=swn, license=wn-free, srd_ref`) with the SRD's
  damage/AC/cost/enc/range/magazine + a `tech_level` tag; sci-fi names are a free reskin
  (ADR-145 D1). Carries genre-default currency/starting_equipment/starting_gold/philosophy.
- `genre_packs/space_opera/worlds/{aureate_span,coyote_star,perseus_cloud}/inventory.yaml` —
  **de-triplicated**: each shrunk from the byte-identical 278-line catalog to a thin override
  with world-**distinct bespoke** gear (aureate_span: mirrorsilk_mantle/house_chit; coyote_star:
  jump_key/claim_beacon; perseus_cloud: ion_compass/driftrunner_charm) + its own world-owned
  currency/kits/gold/philosophy. `jump_key` (no SWN analog) relocated to coyote_star (ADR-145 D3).

**Test — server** (branch `feat/114-7-space-opera-inventory-srd`, commit `3ed7dfde`, pushed):
TEA's `tests/genre/test_114_7_space_opera_swn_inventory.py`, unchanged.

**Tests:** 12/12 passing (GREEN), verified via `uv run pytest -n0` (not testing-runner).
**Regression:** 54/54 passing across inventory_resolve / inventory_union_merge / inventory_wiring /
space_opera_hp_e2e / 114-8 AWN. **Pack validator:** PASS (0 errors; only pre-existing schema-gap
warnings, identical to mutant_wasteland's genre baseline).
**Verbatim sourcing:** every stat transcribed from the Stars Without Number Revised Free Edition
SRD (Equipment chapter — Armor / Ranged / Melee / General Equipment tables). No invented numbers.

**Branches:** content + server, both pushed → TWO PRs at finish (per TEA's repos-scope Gap).

**Handoff:** To the next phase (verify / review).

### Rework — round 1 (review fix, HIGH)

The Merovingian's REJECT was correct. Fixed the `multifocal_laser` id collision:
- **Removed** the personal Mag Pistol sidearm from the genre baseline (`inventory.yaml`); left a NOTE comment so it isn't re-added under that id. Baseline now 14 verbatim items. No class kit referenced it.
- **Restored** the bespoke ship weapon `multifocal_laser` (1d4, `armor_piercing: 20`, value 8000, `ship-weapon`/`vehicle-mounted`) to all three worlds' `item_catalog`, stamped `provenance.mode: bespoke` (world-tier — D3 forbids genre-tier bespoke). Verified the dogfight's `weapon_lookup` queries `resolve_inventory(pack, world).item_catalog` (`narration_apply.py:5377-5389`), so world-tier placement resolves it with AP 20 intact.
- **Added** the regression tests TEA's suite lacked (`test_confrontation_weapon_ids_resolve_in_every_world`, `test_multifocal_laser_stays_a_ship_weapon_with_armor_piercing`).

**Tests:** 14/14 GREEN (12 original + 2 regression), `uv run pytest -n0`. **Regression:** 52/52 inventory suites pass; pack validator 0 errors; worlds still distinct (3 distinct md5s, de-triplication preserved). ruff clean.
**Commits:** content `feat/114-7…` (multifocal_laser fix), server `feat/114-7…` (regression tests) — both pushed.

**Pre-existing unrelated failure (NOT 114-7):** `tests/server/test_dogfight_player_throw_roundtrip.py::test_session_handler_emits_dice_request_and_stashes_on_sd` fails on LLM-SDK hermeticity (`build_async_anthropic()` guard). It uses the bundled `swn_test_pack` fixture (its own world-tier multifocal_laser), the test file is unchanged by this branch, and fails identically with no causal path from the space_opera content change. See Delivery Findings.

**Handoff:** Back to The Merovingian (Reviewer) for re-review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 2 actionable (multifocal_laser collision, mirrorsilk category) + 4 informational | confirmed 1 (HIGH), confirmed 1 (LOW), 1 deferred (shock wiring), informational noted |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — boundary domain covered manually below |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — silent-failure domain covered manually below |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — test-quality domain covered manually below |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — comment domain covered manually below |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — type domain covered manually below |
| 7 | reviewer-security | Yes | clean | none (21 provenance stamps + 46 strings checked) | N/A — clean |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — simplicity domain covered manually below |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — rule domain covered manually below (Rule Compliance) |

**All received:** Yes (2 enabled subagents returned; 7 disabled via `workflow.reviewer_subagents`, pre-filled)
**Total findings:** 1 confirmed HIGH, 1 confirmed LOW, 1 deferred (non-blocking), 0 dismissed

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] [PRE] | **`multifocal_laser` id collision breaks the SWN dogfight.** The original `multifocal_laser` is a *ship weapon* (1d4, `armor_piercing: 20`, value 8000, `ship-weapon`/`vehicle-mounted`) wired into the `dogfight` confrontation `Fighter Duel` (rules.yaml:566-567 — `player_weapon`/`opponent_weapon: multifocal_laser`). `dogfight_shot.py:_resolve_weapon` (280-283) resolves the id to the CatalogItem and consumes `.damage`; `effective_armor_after_ap(armor=5, ap)` (138-140, used at 232/257) means the cannon's AP 20 fully pierced the opponent's seeded `armor: 5`. I reused the id for a 400cr personal Mag Pistol (2d6+2, **AP 0**), so the Fighter Duel weapon is now a pocket pistol that gets 5 dmg soaked every shot. The SWN-calibrated dogfight is corrupted. | `genre_packs/space_opera/inventory.yaml:89` (the bogus sidearm) + the ship weapon was deleted from all 3 world catalogs | (1) Drop/rename the personal `multifocal_laser` sidearm — no class kit references it. (2) Restore the bespoke ship weapon `multifocal_laser` (1d4, AP 20) to the catalog so rules.yaml resolves it; it is bespoke (no SWN analog) so it must live at the **world tier** (D3 forbids genre-tier bespoke), in all 3 worlds where it originally was, stamped `provenance.mode: bespoke`. |
| [LOW] [PRE] | `mirrorsilk_mantle` (a ceremonial garment) is `category: tool`. Freeform-string category, validator passes, no combat path — but semantically it is apparel/cosmetic. | `worlds/aureate_span/inventory.yaml` | Optional during rework: recategorize as apparel/armor or a cosmetic category. Non-blocking. |

**Confirmed findings, tagged by source:**
- **[PRE][HIGH]** the `multifocal_laser` collision above — independently verified by tracing rules.yaml → dogfight_shot.py.
- **[PRE][LOW]** the `mirrorsilk_mantle` category smell above.
- **[SEC]** CLEAN — reviewer-security checked 21 provenance stamps (all 15 genre items `mode=verbatim/srd=swn/license=wn-free`; 6 world items `mode=bespoke/license=na`; licensing invariant honored) and 46 authored strings (no prompt-injection payloads, no secrets). I concur.

**Domains for disabled subagents (assessed manually):**
- **[EDGE]** Boundary: each world's `starting_equipment` references only ids in the merged (genre∪world) catalog — verified zero dangling refs (preflight + my own grep). The resolver returns the pure genre baseline for worlds shipping no inventory; all 3 ship one. No empty-catalog path.
- **[SILENT]** No silent fallbacks: the change is static YAML; the D3 loader validator and the verbatim-license validator fail loud, not silently. No swallowed errors introduced.
- **[TEST]** **Coverage gap (this is why the HIGH slipped):** the 12 tests assert provenance/TL/de-triplication/baseline-merge but NOTHING asserts that weapon ids referenced by `rules.yaml` confrontation defs (`opponent_weapon`/`player_weapon`) resolve in the catalog, nor that `multifocal_laser` retains ship-weapon semantics. A regression test would have caught the collision. Add it in rework.
- **[DOC]** Comments are accurate and thorough — each baseline item cites its exact SWN SRD entry; the file headers document the ADR-145 D1/D3/D4 rationale and the licensing-supersession. No stale/misleading comments.
- **[TYPE]** All items validate against the existing `CatalogItem`/`ItemProvenance` Pydantic models (`extra="forbid"`); no new types. `category` is stringly-typed (pre-existing model design, not introduced here) — see the mirrorsilk LOW finding.
- **[SIMPLE]** The genre baseline + thin world overrides are appropriately minimal; net −482 lines. No over-engineering. (The one ship weapon that must re-duplicate across 3 worlds is an inherent consequence of D3 forbidding genre-tier bespoke — see Delivery Findings.)
- **[RULE]** See Rule Compliance below.

### Rule Compliance

- **ADR-145 D2 (every genre-tier item carries provenance):** ✓ all 15 genre items stamped (security subagent enumerated all 15).
- **ADR-145 D3 (no bespoke at genre tier; bespoke is world-tier):** ✓ genre baseline is all-verbatim; the 6 world items are bespoke. **BUT** the HIGH finding exposes the corollary gap: a bespoke *ship weapon* referenced by genre-tier `rules.yaml` has no D3-legal genre home — it must sit at the world tier and re-duplicate. Compliant, but see Delivery Findings.
- **ADR-145 D4 (SWN reproduces verbatim, wn-free):** ✓ every verbatim item is `srd=swn, license=wn-free`, with an `srd_ref` citing the SWN SRD. Spot-checked 5 items against the SRD tables (preflight) — exact.
- **SOUL "Bind the Ruleset, Don't Balance It":** ✓ stats are the SWN SRD's, not hand-balanced. The HIGH finding is the *inverse* risk realized — replacing a balanced ship weapon with an unbalanced pistol — which the fix restores.
- **CLAUDE "No half-wired features / verify wiring":** ✗ VIOLATED by the HIGH finding — the inventory change silently de-wired the dogfight's weapon. This is the blocking issue.

### Devil's Advocate

Argue this is broken. It *is* — and the break is exactly the kind a content refactor hides. The story's framing ("de-triplicate the personal-gear catalog") quietly assumed every id in those world catalogs was personal gear. It wasn't: `multifocal_laser` was a strike-fighter cannon smuggled into the personal `inventory.yaml`, and it was load-bearing for a *different subsystem* (the sealed-letter dogfight) via a genre-tier `rules.yaml` reference. The author (me, as Dev) saw the id in the world catalog, pattern-matched "laser → energy sidearm," mapped it to an SWN Mag Pistol, and never grepped for who else consumed the id. The green tests reinforced the false confidence: 12/12 passed because they tested the *new* contract (provenance/TL/merge) and were blind to the *old* contract (the dogfight's weapon resolution). A confused GM running a Fighter Duel after this merge would watch their interceptor's cannon do pistol damage and get soaked by armor it used to punch through — a silent balance corruption with no error, the worst kind. What else could be lurking? I checked: `grep multifocal_laser` found exactly two consumers (inventory + rules.yaml), and I verified the other 14 baseline ids ARE genuine personal gear referenced only by kits. The `house_chit`/`jump_key`/etc. world items are inert flavor (no rules.yaml refs). The Shock fields newly on vibroblade/vibroknife/stun_baton are verbatim-correct but depend on the SWN combat engine honoring Shock — if it doesn't, those are dead stats (deferred, non-blocking, engine concern). Stressed inputs (a world shipping no inventory) resolve to the pure genre baseline — safe. The one real, blocking defect is the weapon-id collision; everything else is sound. Reject, fix the collision, add the regression test that pins confrontation-weapon resolution, and this is a clean win.

**Data flow traced:** `rules.yaml` dogfight `player_weapon: multifocal_laser` → `dogfight_shot.py:_resolve_weapon(weapon_lookup, "multifocal_laser")` → CatalogItem.damage (with armor_piercing) → `effective_armor_after_ap(armor=5, ap)` → shot damage. Pre-change: AP 20 → 0 effective armor. Post-change: AP 0 → 5 effective armor. **Broken.**

**Handoff:** Back to TEA (The Architect) for red rework — add the regression test pinning confrontation-weapon resolution + ship-weapon semantics, then Dev fixes the collision. *(Gate recovery_config routed the rework to green→Dev, who both fixed the content and added the regression test. Re-review below.)*

## Subagent Results

_Re-review (round-trip 1), on the rework commits (content `e8bb4de`, server `dfc7a518`)._

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 14/14 story + 52/52 regression green; validator 0 errors; fix verified | N/A — clean |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none (4 provenance + 3 strings + 5 secret checks) | N/A — clean |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (re-review: 2 enabled returned clean; 7 disabled via settings)
**Total findings:** 0 new — the prior HIGH is resolved and independently verified.

## Reviewer Assessment

**Verdict:** APPROVED (re-review, round-trip 1)

The prior HIGH (`multifocal_laser` id collision breaking the dogfight) is **resolved and independently verified** — I loaded the pack and confirmed: genre baseline no longer contains `multifocal_laser` (14 items); all three worlds resolve `multifocal_laser` as the bespoke ship weapon with `armor_piercing=20`, `mode=bespoke`, value 8000. The dogfight data flow is restored: `effective_armor_after_ap(armor=5, ap=20)=0` → the cannon pierces as designed.

**Confirmed clean, tagged by source:**
- **[PRE]** preflight clean — 14/14 story (12 + 2 regression), 52/52 inventory regression, ruff clean, pack validator 0 errors, 3 distinct world md5s (de-triplication preserved despite the shared ship weapon). The `test_dogfight_player_throw_roundtrip` failure is **confirmed pre-existing & unrelated** (0 diff lines in this branch; real-SDK hermeticity on the `swn_test_pack` fixture).
- **[SEC]** clean — the restored ship weapon is `mode=bespoke`/`license=na` in all 3 worlds (no verbatim claim), genre baseline carries no bespoke item, no injection payloads, no secrets.
- **[TEST]** the round-0 coverage gap is **closed**: `test_confrontation_weapon_ids_resolve_in_every_world` + `test_multifocal_laser_stays_a_ship_weapon_with_armor_piercing` now pin the contract that broke. Both fail on the old (AP-0) state and pass on the fix — meaningful, non-vacuous.
- **[EDGE]** all 3 worlds' kits reference only resolvable ids; the shared ship weapon resolves per-world via the union merge. No empty-catalog path.
- **[SILENT]** no silent fallbacks; static YAML + read-only tests; the verbatim-license + D3 validators still fail loud.
- **[DOC]** the fix left a NOTE comment in the genre baseline explaining why `multifocal_laser` must NOT be re-added there — prevents regression. World items cite their dogfight role. Accurate.
- **[TYPE]** items validate against the unchanged `CatalogItem`/`ItemProvenance` models; the ship weapon's `DamageSpec{armor_piercing: 20}` is type-valid.
- **[SIMPLE]** minimal fix — removed 1 item, restored 1 (the original, verbatim), added 2 tests. No over-engineering.
- **[RULE]** ADR-145 D2/D3/D4 still satisfied (genre all-verbatim, world bespoke, wn-free). The "no half-wired features" rule that the round-0 HIGH violated is now satisfied — the dogfight weapon is wired end-to-end again.

**Data flow re-traced:** `rules.yaml` dogfight `player_weapon: multifocal_laser` → `dogfight_shot.py:_resolve_weapon` → `resolve_inventory(world).item_catalog` → ship weapon (1d4, AP 20) → `effective_armor_after_ap(5, 20)=0` → full damage penetrates. **Restored to correct behavior.**

**Handoff:** To SM (Morpheus) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Conflict** (blocking): The story context frames SWN as *derive-only* (from the 2026-06-14
  audit), but ADR-145 D4 **explicitly supersedes** that read — SWN (like all four WN SRDs)
  reproduces **verbatim** under Sine Nomine free-use terms (`mode=verbatim, srd=swn,
  license=wn-free`). The code (`_VERBATIM_LICENSES`, the D3 loader validator) and siblings
  114-4/114-5/114-8 all implement verbatim. The RED tests pin verbatim. Affects
  `sprint/context/context-story-114-7.md` (the "derive-only" Technical Approach + ACs are
  stale — reconcile to verbatim) and the GREEN deliverable (Dev must source verbatim, NOT
  derived). *Found by TEA during test design.*
- **Gap** (non-blocking): The story's `repos: content` is too narrow. sidequest-content has
  no test harness, so the verification vehicle is a **server-side** pytest (same shape as
  sibling 114-8) on server branch `feat/114-7-space-opera-inventory-srd`. The story spans
  **content + server** and will produce TWO PRs (content yaml → content/develop; test →
  server/develop). Affects the session repo scope + the finish flow. *Found by TEA during
  test design.*
- **Question** (non-blocking): 114-4 shipped a WWN extraction tool and 114-5 a CWN extractor;
  it is unverified whether an **SWN** SRD→inventory extractor exists. Dev should check before
  hand-deriving the ~200-item SWN baseline. Affects the GREEN approach (extraction tool vs
  hand-authoring against the SWN SRD equipment chapter). *Found by TEA during test design.*

### Dev (implementation)
- **Resolved (Question, TEA)**: No SWN extractor exists (only `wwn_equip_extract` / `cwn_equip_extract`,
  and SWN's TL-bearing tables differ). Followed the **hand-authored** path — the same approach as the
  AWN sibling baseline (mutant_wasteland, 9 curated items) — transcribing verbatim from the on-disk
  SWN SRD. Building a tested `swn_equip_extract` was out of this 3-pt story's lane. *Found by Dev during implementation.*
- **Improvement** (non-blocking): `pack_schema.yaml` does not list `inventory.yaml` as a known
  genre-tier or world-tier file, so the pack validator emits an "orphan file" WARNING for every pack
  that ships one. This is **pre-existing** (mutant_wasteland's genre baseline triggers the identical
  warning) — NOT introduced here — but the schema should be updated to clear it. Affects
  `sidequest-content/pack_schema.yaml` (add `inventory.yaml` to the genre + world file schema).
  *Found by Dev during implementation.*
- **Gap** (non-blocking, pre-existing, NOT 114-7): `tests/server/test_dogfight_player_throw_roundtrip.py::test_session_handler_emits_dice_request_and_stashes_on_sd`
  fails on LLM-SDK hermeticity (constructs the real `build_async_anthropic()` instead of a fake).
  It uses the bundled `swn_test_pack` fixture, the test file is unchanged by this branch, and it
  fails identically on develop — no causal path from the space_opera content change. Affects
  `sidequest-server/tests/server/test_dogfight_player_throw_roundtrip.py` (install a fake SDK fixture).
  *Found by Dev during rework round 1.*

### Reviewer (code review)
- **Conflict** (blocking): The `multifocal_laser` id was reused for a personal sidearm, but the
  original is a *ship weapon* wired into the `dogfight` confrontation (`rules.yaml:566-567`); the
  dogfight engine (`dogfight_shot.py`) resolves the id to the CatalogItem and consumes its
  damage/armor_piercing. Affects `genre_packs/space_opera/inventory.yaml` (remove/rename the bogus
  sidearm) and the 3 world catalogs (restore the bespoke ship weapon `multifocal_laser`). MUST fix
  before merge. *Found by Reviewer during code review.*
- **Gap** (non-blocking): No test asserts that confrontation-def weapon ids (`opponent_weapon`/
  `player_weapon` in `rules.yaml`) resolve in the merged catalog or retain their mechanical
  semantics — the coverage hole that let the collision pass green. Affects
  `sidequest-server/tests/genre/test_114_7_*.py` (add the regression test in red rework).
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking): A bespoke ship weapon referenced by a genre-tier `rules.yaml`
  confrontation has no D3-legal genre home (D3 forbids genre-tier bespoke), so it must re-duplicate
  across worlds. Worth a follow-up: a dedicated ship-weapons catalog, or SWN-sourcing ship weapons
  from the SWN starship schema. Affects `genre_packs/space_opera/` ship-combat content. *Found by
  Reviewer during code review.*
- **Question** (non-blocking): vibroblade/vibroknife/stun_baton now carry verbatim SWN `shock`/
  `shock_ac`; confirm the SWN combat path applies Shock, else these are dead (correct) stats.
  Affects the SWN ruleset combat engine (engine concern, not this content story). *Found by
  Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

2 deviations

- **Tests pin SWN as verbatim, not derive-only**
  - Rationale: ADR-145 D4 (lines 51, 56-60, 152-153, 189-190, 329) explicitly supersedes the 2026-06-14 audit's "derive-only" read — Sine Nomine's standing free-use policy covers all four WN SRDs (WWN/CWN/SWN/AWN), every one "reproduce verbatim." The code (`_VERBATIM_LICENSES={"wn-free"}`, the `_validate_genre_baseline_no_bespoke` D3 validator) and the three sibling stories (114-4 WWN, 114-5 CWN, 114-8 AWN) all implement verbatim. The story context cited the now-superseded audit. Per spec-authority, I logged this deviation before writing the tests rather than encode a known-stale premise.
  - Severity: major
  - Forward impact: Dev must source the SWN baseline verbatim. The story context's derive-only framing is stale and should be reconciled (see Delivery Findings, Conflict). If the Operator intends derived contra ADR-145, these tests must be revised first.
- **Implemented the SWN baseline as verbatim, not derive-only**
  - Rationale: I implemented against TEA's RED tests (the authoritative GREEN target), which encode ADR-145 D4 — SWN, like all four WN SRDs, reproduces verbatim under the WN free-use terms (superseding the 2026-06-14 audit's derive-only read that the story context cited). The model (`_VERBATIM_LICENSES`), the D3 loader validator, and siblings 114-4/114-5/114-8 all enforce verbatim; a `derived` baseline would fail `test_no_genre_baseline_item_uses_derived_mode`. I concur with TEA's analysis.
  - Severity: major
  - Forward impact: The story context's derive-only framing is stale — SM/Operator should reconcile `context-story-114-7.md`. No code or sibling-story impact (matches the established WN-family pattern).

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Tests pin SWN as verbatim, not derive-only**
  - Spec source: context-story-114-7.md — "Technical Approach" + "Acceptance Criteria"
  - Spec text: "SWN licensing = DERIVE-ONLY, NOT verbatim ... re-stated against the SWN schema, not copied ... no verbatim SRD copy"
  - Implementation: The RED suite asserts `provenance.mode == "verbatim"`, `srd == "swn"`, `license == "wn-free"` and explicitly rejects `mode == "derived"` for genre-tier SWN items.
  - Rationale: ADR-145 D4 (lines 51, 56-60, 152-153, 189-190, 329) explicitly supersedes the 2026-06-14 audit's "derive-only" read — Sine Nomine's standing free-use policy covers all four WN SRDs (WWN/CWN/SWN/AWN), every one "reproduce verbatim." The code (`_VERBATIM_LICENSES={"wn-free"}`, the `_validate_genre_baseline_no_bespoke` D3 validator) and the three sibling stories (114-4 WWN, 114-5 CWN, 114-8 AWN) all implement verbatim. The story context cited the now-superseded audit. Per spec-authority, I logged this deviation before writing the tests rather than encode a known-stale premise.
  - Severity: major
  - Forward impact: Dev must source the SWN baseline verbatim. The story context's derive-only framing is stale and should be reconciled (see Delivery Findings, Conflict). If the Operator intends derived contra ADR-145, these tests must be revised first.

### Dev (implementation)
- **Implemented the SWN baseline as verbatim, not derive-only**
  - Spec source: context-story-114-7.md — "Technical Approach" + "Acceptance Criteria"
  - Spec text: "SWN licensing = DERIVE-ONLY, NOT verbatim ... re-stated against the SWN schema, not copied ... no verbatim SRD copy"
  - Implementation: Every genre-tier SWN item is stamped `provenance.mode=verbatim, srd=swn, license=wn-free, srd_ref`, with the SWN SRD's exact damage/AC/cost/enc/range/magazine/TL reproduced.
  - Rationale: I implemented against TEA's RED tests (the authoritative GREEN target), which encode ADR-145 D4 — SWN, like all four WN SRDs, reproduces verbatim under the WN free-use terms (superseding the 2026-06-14 audit's derive-only read that the story context cited). The model (`_VERBATIM_LICENSES`), the D3 loader validator, and siblings 114-4/114-5/114-8 all enforce verbatim; a `derived` baseline would fail `test_no_genre_baseline_item_uses_derived_mode`. I concur with TEA's analysis.
  - Severity: major
  - Forward impact: The story context's derive-only framing is stale — SM/Operator should reconcile `context-story-114-7.md`. No code or sibling-story impact (matches the established WN-family pattern).

### Reviewer (audit)
- **TEA deviation (verbatim, not derive-only)** → ✓ ACCEPTED by Reviewer: ADR-145 D4 is explicit and code-enforced (`_VERBATIM_LICENSES`, D3 validator) and three siblings (114-4/114-5/114-8) shipped verbatim; the story context cited the superseded audit. Sound.
- **Dev deviation (implemented verbatim per TEA's tests + ADR-145)** → ✓ ACCEPTED by Reviewer: correct execution of the accepted TEA deviation; the genre baseline is verbatim, provenance-stamped, and SRD-faithful (spot-checked 5 items).
- **Dev deviation (hand-authored, no SWN extractor built)** → ✓ ACCEPTED by Reviewer: matches the AWN sibling's curated-baseline approach; building a tested extractor was correctly out of this 3-pt story's lane.
- **UNDOCUMENTED deviation (caught by Reviewer):** the refactor silently changed the meaning of the `multifocal_laser` id — spec/precedent treats catalog ids as stable references, but the change re-pointed a wired ship-weapon id (consumed by the rules.yaml dogfight) to a personal sidearm. Neither TEA nor Dev logged that `multifocal_laser` was a ship weapon with a cross-file consumer. Severity: **HIGH** (blocking). See the Reviewer Assessment severity table + the blocking Delivery Finding.
  - → ✓ RESOLVED (re-review, round-trip 1): the rework restored the bespoke ship weapon `multifocal_laser` (AP 20) to the world tier and removed the colliding sidearm; a regression test now pins the contract. Id stability is preserved — `multifocal_laser` once again means the ship weapon. No outstanding deviations.