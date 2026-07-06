---
story_id: "162-6"
jira_key: ""
epic: "162"
workflow: "tdd"
---
# Story 162-6: space_opera bestiary de-triplication

## Story Details
- **ID:** 162-6
- **Jira Key:** (none — Jira not configured)
- **Workflow:** tdd
- **Stack Parent:** none
- **Type:** chore
- **Points:** 2
- **Priority:** p2
- **Repos:** content, server

## Story Summary

Several worlds under the space_opera genre pack carry byte-identical 12-entry bestiary.yaml files. Because effective_bestiary resolution merges world-over-genre, an identical per-world copy is redundant triplication.

**Acceptance Criteria:**
1. Identify byte-identical world bestiaries under space_opera genre pack
2. Collapse identical world bestiary files into a single genre-root bestiary file (genre_packs/space_opera/bestiary.yaml)
3. Verify effective_bestiary world-over-genre resolution delivers identical bestiary to each world (regression test on server side)
4. Apply the same byte-identity pattern check to long_foundry world and de-triplicate if the same pattern is found
5. No world's effective bestiary must change as a result (core acceptance criterion)

## Technical Approach

1. **Content side (sidequest-content):**
   - Audit space_opera genre pack worlds for byte-identical bestiary.yaml files
   - Extract the common 12-entry file to genre_packs/space_opera/bestiary.yaml
   - Remove per-world bestiary.yaml copies from worlds that were using the identical file
   - Check long_foundry for the same pattern and de-triplicate if found

2. **Server side (sidequest-server):**
   - Write regression tests that verify effective_bestiary resolution still delivers the correct bestiary to each world post-dedup
   - Tests must assert that worlds that had per-world copies now resolve to the genre-root file via effective_bestiary
   - Verify no other content has been affected
   - Ensure No Silent Fallbacks: if a world's effective bestiary changes, tests must fail loudly

## Constraints

- This is a content-dedup chore, but it depends on the server's effective_bestiary world-over-genre resolution behaving correctly
- Byte-identical is the precondition: only collapse files that are genuinely identical
- Divergent world bestiaries must stay put
- No Silent Fallbacks doctrine: removing per-world files must NOT change the effective bestiary any world sees

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-07-06T11:38:57Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-06T10:38:19Z | 2026-07-06T10:38:19Z | immediate |
| red | 2026-07-06T10:38:19Z | 2026-07-06T11:14:06Z | 35m 47s |
| green | 2026-07-06T11:14:06Z | 2026-07-06T11:24:55Z | 10m 49s |
| review | 2026-07-06T11:24:55Z | 2026-07-06T11:38:57Z | 14m 2s |
| finish | 2026-07-06T11:38:57Z | - | - |

## Delivery Findings

<!-- Append-only. Each agent writes under its own subheading. -->

### TEA (test design)
- **Improvement** (non-blocking): ADR-155 creature-image render key for the 12 collapsed SWN creatures moves from `space_opera/{perseus_cloud,aureate_span}/<id>` to `space_opera/default/<id>` once the entries live at the genre tier. Affects `scripts/generate_creature_images.py` (rglobs `bestiary.yaml`, keys by world dir → genre-root maps to world `"default"`); no code change. **Not a live regression** — `r2_manifest.json` has zero space_opera creature images today, so this is a future-render note for the art-director. *Found by TEA during test design.*
- **Question** (non-blocking): Creating a genre-root `space_opera/bestiary.yaml` changes `effective_bestiary(None or unknown-world)` for space_opera from `(None, "genre")` to `(genre-root, "genre")`. Affects any encountergen "fail-loud on empty pool" expectation for a null/unknown-world call (`pack.py:557`). Confirm no consumer depends on space_opera resolving `None` for an absent world. *Found by TEA during test design.*
- **Gap** (non-blocking): No server code change is required for this story — the genre-tier bestiary seam is already fully wired (`genre/loader.py:2577` reads `<pack>/bestiary.yaml` → `pack.bestiary`; `effective_bestiary` falls through at `pack.py:557`). The `server` repo is the regression-test surface only. Dev's work is content-only (create genre root, delete 2 world files). *Found by TEA during test design.*

### Dev (implementation)
- No new upstream findings. TEA's three findings stand and are unaffected by the implementation: the ADR-155 creature-image render-key shift is confirmed not-live (zero space_opera creature images in R2); no server code was needed (confirmed — content-only change); `effective_bestiary(None)` for space_opera now returns the genre root instead of `None`, but the full server suite (14658 passed / 0 failed) shows no consumer depended on the old `None`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): The genre-root header overclaims "copied byte-for-byte into worlds/aureate_span" — aureate_span was unzoned and shipped NO `factions:` tags; only the 12 stat blocks were byte-identical (the tagging diverged). Contradicts the story's own premise-correction. Affects `sidequest-content/genre_packs/space_opera/bestiary.yaml:15` (reword to "the 12 stat blocks were byte-identical across the three worlds; only perseus_cloud/coyote_star carried the factions:['*'] tags"). Also update the `# Genre tier rules (ADR-120)` citation at line 11 → ADR-140 (ADR-120 is superseded-by ADR-140). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The characterization golden `_core_stats` pins only combat numbers (level/hp/armor_class/attack_bonus/damage); name/description/tags/abilities are never compared, so a future flavor-text edit to the genre-root file would not be caught. Affects `sidequest-server/tests/genre/test_162_6_space_opera_bestiary_detriplication.py:119` (extend the golden or add a name/description invariant). Low real-impact today (entries are byte-identical to the pre-collapse perseus_cloud file). *Found by Reviewer during code review.*
- **Question** (non-blocking): Adding a genre-tier bestiary narrows the encountergen CLI typo-guard for space_opera — a typo'd or omitted `--world` now resolves to the genre pool instead of failing loud. Affects `sidequest-server/sidequest/cli/encountergen/encountergen.py` (dev-tool ergonomics only; NOT a production risk — ADR-004 binds/validates `world_slug` at connect time before dispatch reaches `effective_bestiary`). Confirm the CLI ergonomics change is acceptable. *Found by Reviewer during code review.*

## Design Deviations

### TEA (test design)
- **Story premise stale — "byte-identical triplication" is actually a 3-way divergence; scope narrowed to a 2-world collapse**
  - Spec source: sprint/epic-162.yaml story 162-6 title; context-story-162-6.md AC1–AC2
  - Spec text: "byte-identical 12-entry world bestiaries collapse to a genre-root file"
  - Implementation: Tests pin a **2-world** collapse (perseus_cloud + aureate_span → new genre root) with **coyote_star retained**. The three files are NOT byte-identical: aureate_span (unzoned) carries no faction tags; perseus_cloud (zoned) carries `factions:["*"]`; coyote_star (zoned) carries factions PLUS a world-specific `generics:` section (void_drifter/wreck_picker, added by 162-3 in this same epic). Scope confirmed with Keith via AskUserQuestion (2026-07-06): "collapse perseus + aureate."
  - Rationale: `effective_bestiary` is whole-file REPLACE (pack.py:549). coyote_star's world-specific generics cannot move to the genre root without leaking into every falling-through world, so it cannot collapse. Only worlds the genre root reproduces exactly may collapse.
  - Severity: major
  - Forward impact: Dev implements a 2-world collapse, not a 3-world one. AC1's "byte-identical" precondition is documented false in the test-module docstring; coyote_star's residual 12-entry duplication is intentional and permanent under whole-file-replace.
- **Invariant compares stat fields only, tolerating aureate_span's inherited `factions:["*"]`**
  - Spec source: context-story-162-6.md AC5
  - Spec text: "No world's effective bestiary must change as a result"
  - Implementation: The invariant tests assert the resolved creature-STAT set (id set + level/hp/armor_class/attack_bonus/damage) is unchanged, but tolerate aureate_span gaining `factions:["*"]` when it falls through to the factions-tagged genre root.
  - Rationale: `factions:["*"]` is verifiably inert for the unzoned aureate_span (`game/zone_eligibility.is_eligible` short-circuits to True for `zoned=False` and for `"*"`); encounter behavior is byte-identical. Strict full-model equality would wrongly redden on a behaviorally-null field.
  - Severity: minor
  - Forward impact: Reviewer should read "effective bestiary unchanged" as encounter-behavioral, not model-byte-identical.

### Dev (implementation)
- **Genre-root header rewritten rather than byte-copied from perseus_cloud's header**
  - Spec source: session TEA Assessment, handoff step 1
  - Spec text: "copy the entries block from perseus_cloud/coyote_star ... minus the generics"
  - Implementation: The 12 entries were copied verbatim (identical stats + `factions:["*"]`), but the file header comment was rewritten — added a 162-6 provenance note and reframed the epic-157 comment from "This world is zoned…" to genre-tier language (the `factions:["*"]` tags serve zoned worlds that fall through; inert for the unzoned aureate_span).
  - Rationale: perseus_cloud's header asserted "This world is zoned," which is false at the genre tier and would mislead the next reader. Comment-only; zero entry-data change; no test asserts header text.
  - Severity: trivial
  - Forward impact: none.

### Reviewer (audit)
- **TEA #1 (premise stale → 2-world collapse, coyote_star retained)** → ✓ ACCEPTED by Reviewer: Verified against content (`git show develop~1` on both world files) and code. The whole-file-REPLACE constraint is real (`pack.py:549`); coyote_star's world-specific generics genuinely cannot be genre-tiered. The genre-tier consolidation is explicitly permitted by ADR-140 D2 ("a shared genre-tier catalog is a permitted default… first-class, non-hole choice rather than a violation"; ADR-140 lines 112-118, 178-181 — which name space_opera), and precedent exists (neon_dystopia + mutant_wasteland already ship genre-root bestiaries; this file originated at the genre root in story 90-1). Scope was stakeholder-approved. Sound.
- **TEA #2 (invariant tolerates aureate_span's inherited `factions:["*"]`)** → ✓ ACCEPTED by Reviewer: The tolerance is verified inert against production code, not just asserted — `game/zone_eligibility.is_eligible` short-circuits `True` for `zoned=False` (aureate_span has zero `controlled_by`) and for the `"*"` sentinel. Encounter behavior is byte-identical. Comparing stat fields only is the correct invariant.
- **Dev (genre-root header rewritten, not byte-copied)** → ✓ ACCEPTED by Reviewer, with a follow-up: The tier-appropriate reframe of the epic-157 comment is correct and improves accuracy. HOWEVER the rewrite introduced a new inaccuracy — "copied byte-for-byte into worlds/aureate_span" overclaims (aureate_span shipped no factions tags). Captured as a non-blocking [DOC] delivery finding recommending a one-line reword + ADR-120→ADR-140 citation update. Does not block.
- No UNDOCUMENTED deviations found. The apparent ADR-140 tension (genre-tier bestiary vs "world owns catalog") was chased to ground and ruled COMPLIANT under ADR-140 D2, so it is not a deviation.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Content de-triplication with a load-bearing "no world's effective bestiary changes" invariant — needs a characterization safety net + end-state assertions.

**Test Files:**
- `sidequest-server/tests/genre/test_162_6_space_opera_bestiary_detriplication.py` — content-gated (`GENRE_PACKS_DIR.is_dir()`) assertions on the real space_opera + heavy_metal packs via `load_genre_pack` / `effective_bestiary`.

**Tests Written:** 27 (11 test functions, several parametrized) covering ACs 1–5 + the long_foundry pattern check.
**Status:** RED — 20 failing (end-state), 7 passing (invariant guards). 0 errored, 0 skipped. Verified via testing-runner.

**RED set (fails until Dev implements):** genre-root file existence + 12-entry roster + factions:["*"] + per-entry stat golden (14); collapsed worlds ship no own bestiary + resolve to genre tier + files removed from disk (6).
**GREEN guards (must stay green):** collapsed-world resolved stat set unchanged; collapsed worlds don't inherit coyote generics; coyote_star retention + generics intact; coyote base roster == genre-generic block; long_foundry no-triplication (AC4).

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| Test quality — meaningful assertions (no vacuous `assert True`/`is_none`-on-always-None) | every test asserts concrete id-sets / stat tuples / resolution `source` | pass |
| Wiring test — real production path, not isolation | `test_collapsed_world_resolves_to_genre_tier` (loads real pack, exercises `effective_bestiary`, asserts `bestiary is pack.bestiary`) | RED (wiring proof) |
| No source-text wiring tests (CLAUDE.md) | assertions ride the loaded pydantic model + `effective_bestiary`; the one disk check targets a DATA file (content deliverable), not source | pass |
| No Silent Fallbacks (SOUL) | `test_collapsed_world_does_not_inherit_coyote_generics`, `test_genre_root_..._faction_tagged` (zoned fall-through must satisfy 157-7 validator) | pass/RED |
| Characterization golden (dedup safety net) | `CANONICAL_SWN_BLOCK` frozen golden pins stat lines before/after | pass |

**Rules checked:** the applicable subset — this is a content chore + regression tests, not new production types, so constructor/Deserialize/tenant/non_exhaustive lang-review rules do not apply.
**Self-check:** 0 vacuous tests (every assertion checks a concrete value; parametrized cases fail granularly).

**Handoff:** To Dev (Naomi Nagata) for GREEN. Implementation is **content-only** (no server code):
1. Create `sidequest-content/genre_packs/space_opera/bestiary.yaml` — the 12 SWN entries, each `factions: ["*"]`, no `generics:` (copy the entries block from perseus_cloud/coyote_star, which are byte-identical, minus the generics).
2. Delete `worlds/perseus_cloud/bestiary.yaml` and `worlds/aureate_span/bestiary.yaml`.
3. Leave `worlds/coyote_star/bestiary.yaml` untouched.
4. Run the 162-6 test file → all 27 green. Then `just server-test` for no regressions in siblings (esp. `test_world_bestiary_content.py`, `test_162_3_generics_content.py`).
## Dev Assessment

**Implementation Complete:** Yes (content-only — no server code, per the wired genre-tier seam)

**Files Changed:**
- `sidequest-content/genre_packs/space_opera/bestiary.yaml` — NEW genre-tier roster: 12 genre-generic SWN entries, each `factions:["*"]`, no `generics:`. Header reframed for the genre tier (162-6 provenance + epic-157 rationale).
- `sidequest-content/genre_packs/space_opera/worlds/perseus_cloud/bestiary.yaml` — DELETED (falls through to genre root; was byte-identical to it).
- `sidequest-content/genre_packs/space_opera/worlds/aureate_span/bestiary.yaml` — DELETED (falls through; inherits inert `factions:["*"]`).
- `sidequest-content/genre_packs/space_opera/worlds/coyote_star/bestiary.yaml` — UNTOUCHED (world-specific generics can't be genre-tiered).

**Tests:** 27/27 GREEN in `test_162_6_space_opera_bestiary_detriplication.py`. Full server suite: **14658 passed / 0 failed / 341 skipped** (one flaky xdist worker crash on an unrelated `test_pregen_bestiary_90_1.py::[evropi]` — passes in isolation, not a regression from this space_opera-only change).

**End-to-end resolution confirmed** (`effective_bestiary` on the real loaded pack):
- `aureate_span`  → source=`genre`, 12 entries, generics=[]
- `perseus_cloud` → source=`genre`, 12 entries, generics=[]
- `coyote_star`   → source=`world`, 12 entries, generics=[void_drifter, wreck_picker]
- genre-root `pack.bestiary`: 12 entries, all `factions == ["*"]`

**Branches (pushed):**
- content: `feat/162-6-space-opera-bestiary-de-triplication` (commit b707668)
- server:  `feat/162-6-space-opera-bestiary-de-triplication` (commit efe0db94 — TEA's tests)

**Self-review:** No dangling references to the deleted files anywhere in server/scripts/daemon (TEA sweep) or the content repo (Dev sweep). Loader treats world bestiary as optional, so fall-through is clean. AC1–AC5 met; AC4 (long_foundry) = no-triplication negative finding, pinned green.

**Handoff:** To Reviewer (Chrisjen Avasarala) for code review. Note the two design points: coyote_star's residual 12-entry duplication is intentional/permanent under whole-file-replace; "no world's effective bestiary changes" is encounter-behavioral (aureate_span's inherited `factions:["*"]` is verified inert), not model-byte-identical.
## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 27/27 story tests + 20/20 siblings green; ruff/format/pyright clean; file structure correct |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 3 (1 med, 2 low) | confirmed 1 non-blocking (golden pins only combat stats); 2 noted (intentional redundancy — keep; content-gated skip — CI mitigates) |
| 5 | reviewer-comment-analyzer | Yes | findings | 2 (1 high, 1 low) | confirmed 1 non-blocking [DOC] (byte-for-byte overclaim); 1 subsumed by the first |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 0 violations / 2 low observations | confirmed 0 rule violations (18 rules); 2 low notes (encountergen CLI typo-guard; stale ADR-120 citation) |

**All received:** Yes (4 enabled returned; 5 disabled pre-filled per `workflow.reviewer_subagents`)
**Total findings:** 0 confirmed blocking, 4 non-blocking (2 DOC, 1 TEST, 1 RULE/Question), 0 dismissed

## Reviewer Assessment

**Verdict:** APPROVED

Content-only de-triplication (a genre-tier `space_opera/bestiary.yaml` created from perseus_cloud's byte-identical roster; perseus_cloud + aureate_span world copies deleted → fall through; coyote_star retained for its world-specific generics). Mechanically sound and behavior-preserving.

**Data flow traced:** `load_genre_pack(space_opera)` → `pack.bestiary` (new genre-root, 12 entries) → `effective_bestiary(world)`: aureate_span/perseus_cloud resolve `source="genre"` (same object), coyote_star resolves `source="world"` (own file + 2 generics). Verified live. No world's resolved creature-stat set changes (safe because the entries are byte-identical to the pre-collapse perseus_cloud file, confirmed by diff, and the `factions:["*"]` delta on the unzoned aureate_span is inert per `zone_eligibility.is_eligible`).

**Pattern observed:** ADR-140 D2 "genre default is authoritative when present" — a shared genre-tier catalog where worlds genuinely share one — at `sidequest-content/genre_packs/space_opera/bestiary.yaml`. Precedent: `neon_dystopia/bestiary.yaml`, `mutant_wasteland/bestiary.yaml`, `elemental_harmony/spells_wwn.yaml`.

**Error handling:** Fail-loud path preserved — `encountergen` still returns 1 + explicit error when NEITHER tier resolves a bestiary (`encountergen.py:807-820`, unchanged). Loader treats world bestiary as optional (`_load_yaml_optional`), so fall-through is clean, not a silent fallback.

**Subagent dispatch (all 8 tags):**
- `[TEST]` (test-analyzer): golden pins only combat numbers, not name/description — non-blocking hardening note. Tests otherwise strong (real disk load, no mocks, load-bearing parametrization, meaningful assertions). Confirmed non-blocking.
- `[DOC]` (comment-analyzer): genre-root header overclaims "byte-for-byte into aureate_span"; stale ADR-120 citation. Non-blocking; reword recommended. Confirmed.
- `[RULE]` (rule-checker): 18 rules, 0 violations. ADR-140 compliance VERIFIED (D2 carve-out); No-Silent-Fallbacks VERIFIED (fail-loud path intact); No-Stubbing VERIFIED (full stat blocks). One low CLI-ergonomics note. Confirmed clean.
- `[EDGE]` — disabled via settings. Inline: the only boundary is the `effective_bestiary` fall-through and the unknown/None-world case; both covered by tests + the preserved fail-loud gate. No unhandled path found.
- `[SILENT]` — disabled via settings. Inline: assessed under rule-checker #14; the genre-tier default is doctrine-sanctioned, fail-loud gate unchanged. No swallowed error.
- `[TYPE]` — disabled via settings. Inline: no new types; the test file's annotations are complete (rule-checker #3). N/A for YAML data.
- `[SEC]` — disabled via settings. Inline: no user-input surface (content data + test file); `load_genre_pack` uses safe YAML loading; no injection/secret surface. N/A.
- `[SIMPLE]` — disabled via settings. Inline: the change is a deletion + a single new data file + one test file — no over-engineering. One belt-and-suspenders test flagged by test-analyzer but intentional (keep).

**Devil's Advocate:** Could this break? The sharpest attack: it reverses ADR-140's "world owns the catalog." Chased to ground — ADR-140 D2 explicitly permits a shared genre-tier catalog and names space_opera; git history shows the file originated at the genre root; two sibling packs already ship genre-root bestiaries. Not a violation. Second attack: does deleting the world files orphan anything? Swept server/scripts/daemon (TEA) and the content repo (Dev + Reviewer) for hardcoded refs to the deleted paths — none; ADR-155 creature-image render keys shift to `default` but zero space_opera creature images exist in R2 (future-render note, tracked). Third attack: does the invariant's `factions` tolerance hide a regression? No — the collapsed worlds resolve to the *same object* as the verified-tagged genre root (identity check), and the tag is inert for the unzoned world (verified against `zone_eligibility.py`). Fourth: a typo'd `encountergen --world` now silently uses the genre pool instead of erroring — real but dev-CLI-only; production binds world_slug at connect (ADR-004). Fifth: the golden only pins combat stats, so a future flavor-text edit to the genre root could drift undetected — a genuine test-coverage gap, captured as a non-blocking finding, zero impact on THIS byte-identical change. Nothing rises to blocking.

**Handoff:** To SM (Camina Drummer) for finish-story. Four non-blocking findings recommended for a quick follow-up or fold-in before merge (2 header-comment touch-ups, 1 golden-hardening, 1 CLI-ergonomics confirmation) — none block the merge.