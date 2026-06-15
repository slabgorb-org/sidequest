---
story_id: "120-2"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 120-2: road_warrior (CWN) genre baseline -> verbatim sweep

## Story Details
- **ID:** 120-2
- **Jira Key:** (none — personal project)
- **Epic:** 120
- **Workflow:** tdd
- **Stack Parent:** none
- **Repos:** content, server

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-15T23:01:52Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-15T22:05:01Z | 2026-06-15T22:07:43Z | 2m 42s |
| red | 2026-06-15T22:07:43Z | 2026-06-15T22:20:03Z | 12m 20s |
| green | 2026-06-15T22:20:03Z | 2026-06-15T22:52:37Z | 32m 34s |
| review | 2026-06-15T22:52:37Z | 2026-06-15T23:01:52Z | 9m 15s |
| finish | 2026-06-15T23:01:52Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): road_warrior's genre-tier `starting_equipment` references four the_circuit-owned weapon ids (`pistol`, `tire_iron`, `chain`, `sawed_off_shotgun`) that 114-14 moved to the world tier, so `resolve_inventory(pack, None)` dangles them — the genre baseline is not standalone-playable, only playable via the_circuit. Affects `sidequest-content/genre_packs/road_warrior/inventory.yaml` `starting_equipment` (either point genre kits at genre-tier ids only, or document road_warrior as world-required). Pre-existing 114-14 condition, OUT OF SCOPE for 120-2 — surfaced so it is not mistaken for a 120-2 regression. *Found by TEA during test design.*
- **Question** (non-blocking): `rig_tier_1_prospect` is referenced by EVERY class kit and is one of the no-CWN-analog rig vessels slated to MOVE to the world tier. When Dev moves it, `worlds/the_circuit/inventory.yaml` MUST re-add it to its `item_catalog` (as honest `mode=bespoke`) or all six kits dangle. The `test_road_warrior_circuit_kits_resolve_no_dangling_ids` guard will catch this. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): the Story-86-5 vessel/rig tests (`test_road_warrior_vessel_calibration.py`, `test_vessel_full_stat_blocks.py`, `test_the_circuit_rig_playtest_otel.py`) were coupled to genre-tier vessel placement and broke when epic-120 moved the vessels to the_circuit. I redirected their loaders to the world tier (assertions unchanged). Affects those 3 server test files. Worth a Reviewer check that intent was preserved (vessels still parse to full stat blocks, mount weapons still carry damage, rig still binds + emits `rig_pool.delta`). *Found by Dev during implementation.*
- **Gap** (non-blocking, confirms TEA's finding): post-sweep, `resolve_inventory(pack, None)` (pure genre baseline) dangles 9 kit ids (`rig_tier_1_prospect`, `engine_part`, `ram_plow`, `armor_plate`, `radio_rig`, `pistol`, `tire_iron`, `chain`, `sawed_off_shotgun`) — up from 4 pre-sweep — because the rig vessels/parts now live at the world tier too. This is by design (road_warrior is world-required; only world is the_circuit) and production is unaffected: chargen binds from the merged the_circuit catalog (`resolve(the_circuit)` = 0 dangling, rig binds, verified). Affects `sidequest-content/genre_packs/road_warrior/inventory.yaml` `starting_equipment` — if a standalone genre-baseline ever becomes a requirement, the genre kits would need genre-tier-only ids. *Found by Dev during implementation.*
- **Note** (non-blocking): the full server suite shows 170 failures + 3 errors, ALL pre-existing (epic-108 WWN combat/sealed-round/dispatch/reprisal, `the_trade` e2e, `caverns_and_claudes` WWN chargen `test_cc_chargen_e2e.py` [class_hint=None, a caverns issue this road_warrior change cannot touch], lore/arc integration). Count dropped from 177→170 (the 6 vessel/rig fixes + ~1 random-ordering variance among known-flaky pre-existing integration tests). Zero failures touch road_warrior/the_circuit/vessel/rig/inventory. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `test_starting_mounted_weapons_fit_in_starting_rig_slots` builds its `catalog` from the world tier only, so the repointed `cwn_*` kit ids resolve to `{}` via silent `.get(i, {})` — a genre-tier blind spot. Affects `sidequest-server/tests/genre/test_road_warrior_vessel_calibration.py` (fast-follow: build `catalog` from `resolve_inventory(pack, "the_circuit")` so genre-tier kit ids are visible). Non-blocking — the test's live assertions hold and dangling-id detection is covered by `test_road_warrior_circuit_kits_resolve_no_dangling_ids`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `test_road_warrior_circuit_kits_resolve_no_dangling_ids` loops `resolved.starting_equipment.items()` with no non-empty guard → vacuous if `starting_equipment` were ever empty. Affects `sidequest-server/tests/genre/test_120_2_road_warrior_verbatim_baseline.py` (fast-follow: add `assert resolved.starting_equipment` before the loop). Non-blocking — non-emptiness is asserted by the calibration test's `assert starting`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking, ungated): `ruff format` would reflow `sidequest-server/tests/genre/test_120_2_road_warrior_verbatim_baseline.py:146-148` (a parenthesized one-string assert collapses to one line). Pure reflow, no logic; `ruff format --check` is not in the project gates. Recommend `uv run ruff format` on that file at finish or as a trivial follow-up. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Kit-trap test scoped to worlds only, excluding the bare genre baseline (`world_slug=None`)**
  - Spec source: sibling story 120-1 test (`tests/genre/test_120_1_caverns_verbatim_baseline.py:124`) + story-120-2 context ("Verify the_circuit kits still resolve via resolve_inventory")
  - Spec text: 120-1's `test_caverns_kits_resolve_no_dangling_ids` iterates `world_slugs = [None, *pack.worlds.keys()]`, asserting the pure genre baseline also resolves with no dangling kit ids.
  - Implementation: `test_road_warrior_circuit_kits_resolve_no_dangling_ids` iterates `pack.worlds` only (the_circuit), NOT `None`.
  - Rationale: MEASURED — `resolve_inventory(pack, None)` already dangles `['chain','pistol','sawed_off_shotgun','tire_iron']` TODAY. 114-14 moved those four personal weapons to `worlds/the_circuit/inventory.yaml`, but the genre-tier `starting_equipment` still references them. That is a pre-existing 114-14 condition unrelated to this sweep; asserting the `None` case would fail RED for the wrong reason. road_warrior is played via the_circuit, and the story explicitly says "verify the_circuit kits resolve" — so the world-scoped form is the faithful one. (caverns' `[None, *worlds]` form is correct there because caverns' genre baseline is self-contained.)
  - Severity: minor
  - Forward impact: Dev/Reviewer should treat the road_warrior genre baseline as world-required (not standalone-playable) — see the related Delivery Finding. Do not "fix" the dangling `None` case as part of 120-2.

### Dev (implementation)
- **Dedup-by-deletion of 4 survival items instead of adding redundant verbatim entries**
  - Spec source: epic-120 context + TEA assessment ("items WITH a CWN analog → add verbatim provenance at the genre tier")
  - Spec text: "source each unprovenanced item verbatim from its SRD at the genre tier where an analog exists (mode=verbatim, srd=cwn)"
  - Implementation: 4 of the unprovenanced survival items (`medkit`, `tool_kit`, `binoculars`, `radio_handheld`) were EXACT functional duplicates of `cwn_*` verbatim items ALREADY in the catalog (`cwn_medkit`/`cwn_basic_tools_kit`/`cwn_binoculars`/`cwn_handheld_radio`), differing only in road_warrior-economy stats (value/category). Rather than mint a second verbatim entry for the same SRD item (redundant), I DELETED the 4 dups and repointed the class kits to the existing `cwn_*` twins in BOTH the genre and the_circuit `starting_equipment` blocks.
  - Rationale: Mirrors the merged 120-1 caverns rename pattern (genre catalog = pure SRD `cwn_*` ids; kits reference them). A duplicate verbatim item with a different id and road_warrior pricing would be dishonest provenance (its mechanical envelope ≠ the SRD source) and redundant. ADR-145 D1 allows the kit to carry the SRD item; the road_warrior flavor name is freely reskinnable but here the `cwn_*` twin already exists.
  - Severity: minor
  - Forward impact: none — the genre catalog reaches the required 0-unprovenanced/0-bespoke end state; kits resolve via the merge. The remaining 21 no-analog items moved to the_circuit as bespoke.
- **Redirected 3 existing Story-86-5 vessel/rig test files from the genre tier to the_circuit world tier**
  - Spec source: pre-existing tests `tests/genre/test_road_warrior_vessel_calibration.py`, `tests/game/test_vessel_full_stat_blocks.py`, `tests/server/test_the_circuit_rig_playtest_otel.py` (epic 86, Story 86-5)
  - Spec text: those tests load the rig vessels + mount weapons from the genre `inventory.yaml` (`find_pack_path("road_warrior") / "inventory.yaml"` and `pack.inventory`), asserting they parse with full stat blocks, carry damage, fit mount slots, and bind a rig pool.
  - Implementation: pointed each loader at `worlds/the_circuit/inventory.yaml` (and `pack.worlds["the_circuit"].inventory`) — the tier epic-120 relocated the bespoke vessels/mount weapons to. Assertions are UNCHANGED. This also un-vacuums two calibration tests that would otherwise pass trivially on an empty genre-tier vessel list after the move.
  - Rationale: The vessels are bespoke (no CWN analog) and ILLEGAL at a WN genre tier (114-14 validator); epic-120 mandates moving them to the world tier. The 86-5 tests' genre-tier assumption is superseded by epic-120. Production runtime is unaffected — the chargen loadout binds the rig from `resolve_inventory(pack, world)` (the merged catalog), which still contains the vessel via world-replaces-genre (verified: `resolve(the_circuit)` has 0 kit-dangling). Tests should read the runtime-truthful tier.
  - Severity: minor (touches existing tests, not just this story's RED tests — flagged for Reviewer)
  - Forward impact: none functional; any future road_warrior world would likewise own its rig vessels at the world tier (ADR-140 "the world owns the cast and catalog").

### Reviewer (audit)
- **TEA — kit-trap test scoped to worlds only (excludes `world_slug=None`)** → ✓ ACCEPTED by Reviewer: independently re-measured — `resolve(None)` dangles 9 ids post-sweep because road_warrior's genre kits reference world-owned items (a pre-114-14/ADR-140 condition, not a 120-2 break). The world-scoped form is faithful to the story ("verify the_circuit kits resolve") and to runtime (road_warrior is played via the_circuit). Correct call.
- **Dev — dedup-by-deletion of 4 survival items instead of adding redundant verbatim entries** → ✓ ACCEPTED by Reviewer: the 4 deleted items (`medkit`/`tool_kit`/`binoculars`/`radio_handheld`) had exact `cwn_*` verbatim twins already in the catalog with different road_warrior-economy stats; minting a second verbatim entry would be redundant AND dishonest (mechanical envelope ≠ SRD). Repointing kits to the twins mirrors the merged 120-1 caverns rename pattern. Verified the 4 are gone from both tiers and kits repointed in both `starting_equipment` blocks.
- **Dev — redirected 3 existing Story-86-5 vessel/rig test files to the_circuit world tier** → ✓ ACCEPTED by Reviewer: the vessels are bespoke and illegal at a WN genre tier (114-14 validator); epic-120 mandates the world-tier move, so the 86-5 genre-tier assumption is legitimately superseded. I read the full diff: every change is a loader path redirect with assertions UNCHANGED and fail-loud guards preserved (not weakened). Production runtime is unaffected (binds from the merged catalog). The residual test-hardening gaps are captured as the two [SILENT] findings (non-blocking).
- No UNDOCUMENTED deviations found — TEA and Dev logged every divergence I could identify.

## Known Traps & Warnings

**Kit Trap:** Renaming/moving genre item_catalog entries can dangle the chargen kits. The fix infrastructure `resolve_equipment_tables` and world-tier `equipment_tables` override landed in 120-4 (PR #888). **MUST NOT drop starting_equipment/gold/currency**. Verify kits resolve via resolve_inventory after moving items.

**Pre-Existing Failures:** 
- the_trade-e2e failures pre-exist on develop
- epic-108 beat failures pre-exist on develop

Record these in baseline so they are not mislabeled as regressions.

**Test Suite Baseline:**
Run FULL suite for baseline (not scoped subset):
- content-gated tests/genre/ calibration tests SKIP without SIDEQUEST_GENRE_PACKS
- Server suite needs SIDEQUEST_DATABASE_URL=postgresql://$USER@localhost:5432/sidequest_test

## Branch Strategy

**Story Repos:** content (sidequest-content, base: develop), server (sidequest-server, base: develop)
**Orchestrator:** main

**Branches created:**
- content: feat/120-2-road-warrior-cwn-verbatim (base: develop)
- server: feat/120-2-road-warrior-cwn-verbatim (base: develop)

## Sm Assessment

**Routing:** Phased TDD. Setup complete → handing RED phase to TEA (Fezzik).

**What this story is:** The road_warrior (CWN) sibling of the already-done caverns 120-1 verbatim sweep. Drive the road_warrior genre `inventory.yaml`/`item_catalog` to **0 bespoke AND 0 unprovenanced** at the genre tier:
- Items with a CWN analog → source from the CWN SRD at genre tier (`mode=verbatim, srd=cwn`).
- Genuinely-unique items (rig-tier vessels, road-warrior-specific gear) with no CWN analog → MOVE to `worlds/the_circuit/inventory.yaml` as honest `mode=bespoke` (ADD to the file 114-14 created; do not clobber it).

**Where the tests go:** The infrastructure to verify is `resolve_inventory` / `resolve_equipment_tables` (server, landed 120-4 / PR #888). RED should pin: (1) genre tier reports 0 bespoke + 0 unprovenanced after the sweep, (2) `the_circuit` chargen kits still resolve — `starting_equipment`, `gold`, and `currency` all intact (THE KIT TRAP — this is the failure mode that bit 120-1's cascade). At least one wiring test must drive `resolve_inventory` against the REAL road_warrior/the_circuit pack, not a synthetic fixture.

**Baseline discipline:** Capture the FULL-suite baseline with `SIDEQUEST_GENRE_PACKS` + `SIDEQUEST_DATABASE_URL` set. `the_trade-e2e` and epic-108 beat failures pre-exist — record them so green-phase doesn't mislabel them as regressions.

**Authorship lane:** Item sourcing is content authoring; defer SRD-analog judgment calls to a content specialist (scenario-designer / writer) during green if needed. Mind that world `inventory.yaml` now MERGES over genre per 114-11 — the moved bespoke items must not collide with genre keys.

---
## TEA Assessment

**Tests Required:** Yes
**Reason:** This story has a hard mechanical invariant (0 bespoke AND 0 unprovenanced at the genre tier) plus a kit-resolution regression risk — both pinnable by tests driven against the real pack. NOT a content-validate-only story (the verification rides on the server's `resolve_inventory` / provenance model), so TDD RED is appropriate.

**Test Files:**
- `sidequest-server/tests/genre/test_120_2_road_warrior_verbatim_baseline.py` — new; mirrors the proven 120-1 caverns template (CWN instead of WWN), with two documented deviations (kit test scoped to worlds; added world-tier honest-bespoke guard).

**Tests Written:** 6 tests (2 RED gates + 4 stay-green guards), driven against the REAL road_warrior pack via `load_genre_pack(find_pack_path("road_warrior"))` + `resolve_inventory` — no fixtures.

**RED state — VERIFIED by testing-runner (run id `120-2-tea-red`):** `2 failed, 4 passed`, no skips, no import errors.

| Test | Now | Role |
|------|-----|------|
| `test_road_warrior_genre_baseline_has_no_unprovenanced_items` | **FAIL** | RED gate — 25 unprovenanced items today (exact list matches the epic) |
| `test_road_warrior_genre_baseline_is_fully_cwn_verbatim` | **FAIL** | RED gate — same 25 not verbatim/cwn |
| `test_road_warrior_pack_loads_clean` | PASS | wiring gate (runs the 114-14 loader validator) |
| `test_road_warrior_genre_baseline_carries_no_bespoke` | PASS | stay-green guard (0 bespoke at genre; 114-14) |
| `test_road_warrior_circuit_kits_resolve_no_dangling_ids` | PASS | **kit-trap guard** — the_circuit merged catalog; catches `rig_tier_1_prospect` (every kit) moving without re-add, and rename-without-update |
| `test_road_warrior_circuit_world_items_are_provenanced` | PASS | honest-bespoke guard — moved uniques land provenanced, not unprovenanced at world tier |

Both RED tests fail on the IDENTICAL 25-item offender list (scrap_metal … rig_tier_5_road_immortal) — failing for the right reason (missing provenance), not an import error or skip.

### Rule Coverage

| Rule (project) | Test(s) | Status |
|------|---------|--------|
| Every test suite needs a wiring test (real production path, not a fixture) | all 6 drive `load_genre_pack` + `resolve_inventory` against the real pack | satisfied |
| No source-text wiring tests | behavior/data assertions only; no `read_text()` grep of source | satisfied |
| Meaningful assertions (no vacuous) | every test asserts an empty offender/dangling list with a diagnostic message | satisfied |
| Fail-loud / no silent fallback (ADR-145 D4) | `pack_loads_clean` exercises the loader validator; verbatim test asserts `license=wn-free` + cwn `srd_ref` | satisfied |

**Rules checked:** 4 of 4 applicable (this is a content-invariant story — the Rust-style lang-review checks for constructors/newtypes/tenant-context do not apply).
**Self-check:** 0 vacuous tests (each `assert not offenders/dangling` carries a real, populated failure list in the RED case).

### What Dev (Inigo) must do — GREEN
1. In `sidequest-content/genre_packs/road_warrior/inventory.yaml`: for each of the 25 unprovenanced items WITH a CWN analog, add `provenance: {mode: verbatim, srd: cwn, license: wn-free, srd_ref: "CWN SRD §…", extracted_by: …}` (match the existing 66-item format). The 5 rig-tier vessels (and any road-specific gear with no CWN analog) MOVE to `worlds/the_circuit/inventory.yaml` `item_catalog` as `mode=bespoke`.
2. **Kit trap:** `rig_tier_1_prospect` is in every class kit. When it (and any other kit-referenced item) moves to the world tier, re-add it to the_circuit world `item_catalog`. Do NOT touch the_circuit `starting_equipment`/`starting_gold`/`currency` (already copied verbatim by 114-14). If a verbatim item is RENAMED (e.g. `medkit`→`cwn_medkit`), update every `starting_equipment` reference.
3. SRD-analog judgment ("does this rig part have a CWN analog?") is a content call — pull in the scenario-designer/writer if unsure. The tests do NOT presuppose which items stay vs move; they only require genre tier = 100% verbatim and kits resolve via the_circuit.
4. Run the FULL suite for the green baseline (`SIDEQUEST_DATABASE_URL` set); `the_trade-e2e` + epic-108 beat failures pre-exist — do not mislabel.

**Handoff:** To Dev (Inigo Montoya) for implementation.

---
## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-content/genre_packs/road_warrior/inventory.yaml` — genre catalog swept to the 66 `cwn_*` verbatim items; deleted 4 redundant survival dups; repointed kits to `cwn_*` twins; comments updated. (committed `2fb74ba`)
- `sidequest-content/genre_packs/road_warrior/worlds/the_circuit/inventory.yaml` — added 21 no-CWN-analog bespoke items (rig parts, mount weapons, 5-tier rig ladder, survival consumables, rig radio); repointed kits; comment updated. (committed `2fb74ba`)
- `sidequest-server/tests/genre/test_road_warrior_vessel_calibration.py` — vessel/mount-weapon loaders → the_circuit world tier. (committed `5804153d`)
- `sidequest-server/tests/game/test_vessel_full_stat_blocks.py` — vessel loader → the_circuit world tier. (committed `5804153d`)
- `sidequest-server/tests/server/test_the_circuit_rig_playtest_otel.py` — real-rig loader → the_circuit world tier. (committed `5804153d`)

**Approach:** Mirrored the merged 120-1 caverns sweep — genre tier becomes the pure SRD (`cwn_*`) extraction; no-analog bespoke gear relocates to the play world (the_circuit) per ADR-145 D3 / ADR-140. Item sourcing executed by the scenario-designer specialist against the existing CWN extraction (cwn_equip_extract@114-5); all judgment calls (which items have a CWN analog) decided by Dev and verified.

**Tests:**
- The 6 RED-phase 120-2 tests: **GREEN** (2 former-RED now pass; 4 guards hold).
- The 6 Story-86-5 vessel/rig tests broken by the vessel relocation: **fixed and GREEN** (loaders redirected to the world tier; assertions unchanged).
- Full server suite: **170 failed / 3 errors / 11368 passed / 1601 skipped** — all failures pre-existing (epic-108 / the_trade / caverns WWN chargen / lore-arc); **zero** touch road_warrior/the_circuit/vessel/rig/inventory. Down from a 177-failure pre-fix baseline.
- ruff check + format: clean on the 3 changed server files.

**Independent verification (measured, not asserted):** genre catalog = 66 items, 0 unprovenanced / 0 bespoke / 0 non-cwn-verbatim; the_circuit world catalog = 26 items, 0 unprovenanced; `resolve_inventory(pack, "the_circuit")` = 0 kit-dangling; production rig binding path reads the merged catalog (`bind_rig_pool_from_inventory` over the chargen-resolved inventory), so the vessel relocation does not break runtime.

**Branches (pushed, no PRs — SM creates at finish):**
- content: `feat/120-2-road-warrior-cwn-verbatim` @ `2fb74ba`
- server: `feat/120-2-road-warrior-cwn-verbatim` @ `5804153d` (also carries TEA's RED commit `3f2565b5`)

**Watch for (Reviewer):** the 3 modified Story-86-5 test files are EXISTING tests, not this story's RED tests — see the Dev deviation. They were redirected (not weakened) because epic-120 relocated the vessels they read; verify intent preserved.

**Handoff:** To TEA (Fezzik) for the verify phase (simplify + quality-pass).

---
## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 (ruff format reflow) + suite baseline | confirmed 1 (Low), dismissed 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 | confirmed 2 (Medium, non-blocking), dismissed 0 |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — domain assessed by Reviewer directly |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — Reviewer verified comments updated |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (no new types; data + test loaders) |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — Reviewer ran Rule Compliance manually |

**All received:** Yes (3 enabled subagents returned; 6 disabled via `workflow.reviewer_subagents` and pre-filled)
**Total findings:** 3 confirmed (2 Medium + 1 Low, all non-blocking), 0 dismissed, 0 deferred

---
## Reviewer Assessment

**Verdict:** APPROVED

The story does exactly what epic-120 mandates and mirrors the merged 120-1 caverns precedent. I independently re-measured every claim (did not trust the Dev/subagent reports): genre tier = 66 items, **0 unprovenanced / 0 bespoke / 0 non-cwn-verbatim**; the_circuit world tier = 26 items, **all `mode=bespoke`, 0 falsely-verbatim**; `resolve_inventory(pack, "the_circuit")` = **0 kit-dangling**; the 21 moved items had **every field preserved** (only `provenance:{bespoke,na}` added); the 66 `cwn_*` verbatim items were **untouched**; stale "deferred to epic 120" comments **updated**. No Critical/High issues. Three non-blocking findings (below) are test-hardening + an ungated format reflow, with the underlying invariants covered by sibling tests.

**Observations (≥5):**
- `[VERIFIED]` Genre baseline is 100% CWN-verbatim — `genre_packs/road_warrior/inventory.yaml`: every remaining item is `mode=verbatim, srd=cwn, license=wn-free` (re-measured: non-cwn-verbatim list empty). Complies with ADR-145 D3.
- `[VERIFIED]` World relocation is honest — `worlds/the_circuit/inventory.yaml`: all 26 items `mode=bespoke` (0 claim verbatim). The 21 no-CWN-analog items (rig parts/mount weapons/5-tier rig ladder/survival consumables) are honestly bespoke, not falsely SRD-sourced. Complies with ADR-145 D1/D4 (no false provenance).
- `[VERIFIED]` Kit trap avoided — every class kit resolves through the the_circuit merge with 0 dangling ids; `rig_tier_1_prospect` (in every kit) is present at the world tier; the 4 deleted survival dups are repointed to their `cwn_*` twins in BOTH the genre and world `starting_equipment` blocks; `starting_gold`/`currency`/`philosophy` untouched.
- `[VERIFIED]` No data loss in the move — field-set comparison of develop-genre vs HEAD-world for all 21 moved ids: every field preserved, only `provenance` added (evidence: scripted field-diff returned "NONE").
- `[SEC]` reviewer-security: clean — `yaml.safe_load` only, no executable YAML, no secrets, no false-verbatim licensing claim; mount-weapon "CWN vehicle weapon" comments describe inspiration, not sourcing (honest `mode=bespoke`; CWN vehicle chapter binding is deferred 114-6).
- `[SILENT]` reviewer-silent-failure-hunter (MEDIUM, non-blocking): `test_starting_mounted_weapons_fit_in_starting_rig_slots` builds `catalog` from the world tier only, so the repointed `cwn_*` kit ids resolve to `{}` via silent `.get(i, {})`. CONFIRMED real, but low impact: the test's live assertion (`len(rig_ids)==1` per class) still holds, the mount-slot check was already trivially satisfied (no kit grants mount weapons, pre- and post-change), and dangling-id detection is covered by `test_road_warrior_circuit_kits_resolve_no_dangling_ids` against the *merged* catalog. Recommend (fast-follow) building `catalog` from `resolve_inventory(pack, "the_circuit")` so genre-tier kit ids are visible.
- `[SILENT]` reviewer-silent-failure-hunter (MEDIUM, non-blocking): `test_road_warrior_circuit_kits_resolve_no_dangling_ids` loops `resolved.starting_equipment.items()` with no non-empty guard → vacuous if `starting_equipment` were ever empty. CONFIRMED real, but the non-empty invariant IS asserted by `test_starting_mounted_weapons_fit_in_starting_rig_slots` (`assert starting, "road_warrior must define starting_equipment"`) and the_circuit ships 6 kits. Recommend (fast-follow) adding `assert resolved.starting_equipment` before the loop.
- `[PREFLIGHT]` (LOW, non-blocking, ungated): `ruff format --check` would reflow `tests/genre/test_120_2_road_warrior_verbatim_baseline.py:146-148` (a parenthesized one-string assert collapses to one line). Pure reflow, no logic change. Project gates (server-check/check-all) do not run `ruff format --check`, so this is ungated. Per documented preference, APPROVE-with-note on pure reflows — recommend running `uv run ruff format` on that file (fold into finish or a trivial follow-up).
- `[EDGE]` N/A — edge-hunter disabled; Reviewer checked boundaries manually (empty kits, missing world inventory: the redirected loaders fail loud via `assert world is not None and world.inventory is not None` and `raise AssertionError` — no silent fallback).
- `[TEST]` N/A — test-analyzer disabled; Reviewer assessed test quality directly: the 3 redirected loaders preserve every assertion (only the data source + messages changed), and the redirect un-vacuums the calibration tests that would otherwise have passed on an empty genre-tier vessel list. The 2 [SILENT] findings above are the residual test-hardening gaps.
- `[DOC]` N/A — comment-analyzer disabled; Reviewer verified the stale "verbatim sweep deferred to epic 120" comments were updated in both files (genre doc-block + the_circuit header now reference 114-14 + 120-2; the move + 4 deletions documented).
- `[TYPE]` N/A — type-design disabled; no new types/models — pure YAML data + test-loader path changes.
- `[SIMPLE]` N/A — simplifier disabled; the diff is minimal (loader path redirects; contiguous bespoke-section relocation). No over-engineering.
- `[RULE]` rule-checker disabled; Reviewer ran the Python lang-review checklist manually — see Rule Compliance below.

**Data flow traced:** chargen kit grant → `resolve_inventory(pack, world_slug="the_circuit")` (merged genre⊕world catalog, ADR-140) → character inventory carries `rig_tier_1_prospect` (now world-tier bespoke) → `bind_rig_pool_from_inventory` scans character inventory → rig pool binds + emits `rig_pool.delta`. The vessel relocation does not break runtime because production reads the merged catalog, not the genre tier (verified: `test_the_circuit_rig_binds_from_real_content` GREEN).

**Pattern observed:** rename-genre-to-pure-SRD + relocate-no-analog-to-world, mirroring the merged 120-1 caverns sweep (`tests/genre/test_120_1_caverns_verbatim_baseline.py`). Consistent with ADR-140 ("the world owns the cast and catalog") and SOUL "Crunch in the Genre, Flavor in the World."

**Error handling:** redirected test loaders fail loud — `assert vessels, ...` (`test_vessel_full_stat_blocks.py`), `assert world is not None and world.inventory is not None` (`test_road_warrior_vessel_calibration.py:166`), `raise AssertionError(...)` (`test_the_circuit_rig_playtest_otel.py`). No silent fallbacks introduced (SOUL "No Silent Fallbacks" upheld).

### Rule Compliance (Python lang-review checklist, manual — rule_checker disabled)

| # | Rule | Applies? | Verdict |
|---|------|----------|---------|
| 1 | Silent exception swallowing | yes (test loaders) | PASS — no bare/blanket except; `pytest.skip` is an env-gate, fail-loud asserts on the data path |
| 6 | Test quality (no vacuous assertions) | yes | 2 MEDIUM findings (above) — individual-test defense-in-depth gaps; suite invariants covered by sibling tests; redirected tests preserve assertions |
| 8 | Unsafe deserialization | yes | PASS — `yaml.safe_load` only (no `yaml.load`/`pickle`/`eval`) |
| 5 | Path handling | yes | PASS — `find_pack_path(...) / "worlds" / "the_circuit" / "inventory.yaml"` uses `pathlib` `/` operator, no string concat |
| 3 | Type annotations at boundaries | minor | PASS — helpers retain existing annotations; no new public API |
| 2,4,7,9,10,11,12,13 | mutable defaults / logging / resource leaks / async / imports / input-validation / deps / fix-regressions | no | N/A — no such code in the diff (test-loader path changes + YAML data) |

### Devil's Advocate

Suppose this code is broken. The most dangerous claim is "production still works after moving the rig vessels off the genre tier." If any production path read vessels from `pack.inventory` (genre) rather than the merged catalog, every the_circuit character would chargen with a dangling `rig_tier_1_prospect` and bind no rig pool — a silent, table-killing regression for Sebastien/Jade's mechanics-first play. I chased this: `chargen_loadout.py` binds via `bind_rig_pool_from_inventory` over the character's inventory, which is populated from `resolve_inventory(pack, world_slug)` (every production consumer passes the world slug — views.py, chargen_summary.py, narration_apply.py, wn_tools.py). The merged catalog contains the world-tier vessel, so the bind succeeds — and `test_the_circuit_rig_binds_from_real_content` proves it against real content. A confused author's next move is the real risk: a FUTURE road_warrior world would NOT inherit these vessels (they're the_circuit-specific now), so a second world would chargen with empty rigs unless it ships its own vessels — but road_warrior has exactly one world today, and ADR-140 makes world-owned catalog the intended model, so this is correct-by-design, not a bug. A malicious/sloppy content edit that marked a moved item `mode=verbatim, srd=cwn` to dodge the bespoke rule would be caught structurally (ItemProvenance validator requires `license=wn-free` for verbatim) and by `test_road_warrior_genre_baseline_is_fully_cwn_verbatim`. The stressed-filesystem case (content not on disk) yields `pytest.skip`, not a false pass. The empty-catalog case is the one genuine soft spot — the two [SILENT] findings — but the suite as a whole still catches an empty kit (calibration `assert starting`) and a dangling id (the dedicated merged-catalog kit test), so a real break would surface. The genre baseline standalone now dangles 9 ids, but it is documented world-required and not a runtime path. Net: I tried to break it and could not find a correctness hole — only two defense-in-depth test gaps and one cosmetic reflow.

**Handoff:** To SM (Vizzini) for finish-story.