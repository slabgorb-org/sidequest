---
story_id: "113-2"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 113-2: Reconcile pack_schema.yaml with the actual server loader allowlist (drift both directions)

## Story Details
- **ID:** 113-2
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-14T21:18:45Z
**Round-Trip Count:** 2
**Repos:** server, content

## Sm Assessment

**What:** Reconcile `pack_schema.yaml` (sidequest-content) against the real genre-pack loader allowlist (`sidequest-server/sidequest/genre/loader.py`). The 2026-06-14 audit found drift in BOTH directions.

**The drift (from the story spec — TEA/Dev verify against current code, line numbers may have moved):**
- Schema lists as genre extensions but loader DROPPED (dead): `openings.yaml` (world-tier only now, loader sets `openings=[]`), `powers.yaml` (fully unreferenced), `weather.yaml` (repointed to world_dir in Epic 74).
- Loader READS but schema OMITS (live, invisible to validator): `skills.yaml`, `spells_wwn.yaml`, `foci.yaml`, `bestiary.yaml`, `backgrounds.yaml`, `witnessed_acts.yaml`, `mutations.yaml`, `disciplines_psionic.yaml`.

**Root cause:** loader reads a fixed hard-coded filename allowlist (no glob at pack root). Hand-maintained `extensions[]` in the schema went stale against it. Unknown YAML at a pack root is **silently ignored** — a No-Silent-Fallbacks violation.

**Scope decision left to Architect/Dev (do NOT decide as SM):** make `pack_schema.yaml` the source of truth the loader allowlist is generated/validated against (so the two cannot silently diverge again), AND decide whether the validator should WARN on unknown pack-root YAML rather than silently ignoring it. This is the load-bearing design question — flag for the design/RED pass.

**Why this matters:** the validator today can neither flag dead files nor recognize live mechanics, so it gives false confidence (`validate pack ≠ load_genre_pack`, per the standing project lesson). Closing the drift restores the validator as a real wiring gate.

**Repos:** Coupled but asymmetric — schema authoritative source lives in **content** (`pack_schema.yaml`), the allowlist consumer lives in **server** (`loader.py` + `cli/validate/pack.py`). Branches created in both. Whatever single-source mechanism is chosen must keep both in lockstep.

**Pre-RED caution for Fezzik:** the genre suite is content-gated — set `SIDEQUEST_GENRE_PACKS` and `SIDEQUEST_DATABASE_URL` or you'll see phantom skips/failures. Run the loader against a real pack (not just the validator) to prove wiring.

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-14T20:39:59.480823Z | 2026-06-14T20:41:57Z | 1m 57s |
| red | 2026-06-14T20:41:57Z | 2026-06-14T20:51:03Z | 9m 6s |
| green | 2026-06-14T20:51:03Z | 2026-06-14T21:05:51Z | 14m 48s |
| review | 2026-06-14T21:05:51Z | 2026-06-14T21:14:00Z | 8m 9s |
| green | 2026-06-14T21:14:00Z | 2026-06-14T21:16:12Z | 2m 12s |
| review | 2026-06-14T21:16:12Z | 2026-06-14T21:18:45Z | 2m 33s |
| finish | 2026-06-14T21:18:45Z | - | - |

## TEA Assessment

**Tests Required:** Yes
**Reason:** tdd workflow; three ACs with real behavior to pin (schema reconciliation, drift guard, validator recognition).

**Test Files:**
- `sidequest-server/tests/cli/validate/test_pack_schema_loader_drift_113_2.py` — 7 tests across 3 classes, fully self-contained (synthesises packs in tmp_path; reads only the real `pack_schema.yaml`, matching the existing validator-test convention).

**Tests Written:** 7 tests covering 3 ACs.
**Status:** RED confirmed — 6 failing, 1 passing (`test_unknown_pack_root_yaml_is_flagged` is an intentional green regression guard for AC3's already-satisfied literal text). Verified via testing-runner (RUN_ID 113-2-tea-red). No collection/import errors; all failures are clean in-body assertions.

### AC → Test map

| AC | Test(s) | Status |
|----|---------|--------|
| AC1 dead removed | `TestSchemaReconciliation::test_dead_genre_extensions_removed` | failing (schema lists openings/powers/weather) |
| AC1 live added | `TestSchemaReconciliation::test_live_genre_extensions_added` | failing (schema omits 8 live files) |
| AC2 dead not in loader | `TestSchemaLoaderAgreement::test_loader_allowlist_excludes_dead_files` | failing (no constant yet) |
| AC2 live in loader | `TestSchemaLoaderAgreement::test_loader_allowlist_includes_live_files` | failing (no constant yet) |
| AC2 drift guard | `TestSchemaLoaderAgreement::test_schema_and_loader_allowlist_agree` | failing (no constant yet) |
| AC3 unknown→warn (guard) | `TestValidatorUnknownFileHandling::test_unknown_pack_root_yaml_is_flagged` | **passing** (regression guard) |
| AC3 live file not orphaned | `TestValidatorUnknownFileHandling::test_live_genre_root_file_is_not_orphaned` | failing (skills.yaml false-orphans) |

### GREEN-phase contract for Inigo (Dev)

The single source of truth this story creates:
1. **Loader (server):** add `sidequest.genre.loader.GENRE_PACK_ROOT_EXTENSION_FILES: frozenset[str]` — every OPTIONAL (extension-tier) YAML filename the loader reads at the **genre pack root**. (Required files — pack.yaml/rules.yaml/theme.yaml/etc. — are a separate schema list and out of scope.) If you rename the symbol, update the test import.
2. **Schema (content):** reconcile `pack_schema.yaml` `genre_pack.extensions` so its file set equals the loader constant. Audit-named delta: remove `openings`/`powers`/`weather`; add `skills`/`spells_wwn`/`foci`/`bestiary`/`backgrounds`/`witnessed_acts`/`mutations`/`disciplines_psionic`. **Also reconcile any extra drift the equality test surfaces** (see Delivery Findings re: spellbook/projection/calendar/history at the genre tier).
3. **Validator (server):** `_check_orphans` must treat the canonical allowlist (full schema extension set, not only pack.yaml-*declared* extensions) as "known", so a live undeclared genre-tier file (skills.yaml) is not false-flagged while genuine unknowns still WARN.

This is a coupled two-repo change (server + content) — the schema edit and the loader/validator change must land together (the equality test fails if either lags). No silent fallbacks: keep the fail-loud reads; this adds an enumerable allowlist + a CI drift guard on top.

**Rules checked:** No-Source-Text-Wiring-Tests (agreement tested via real data + a typed constant, not a grep); No-Silent-Fallbacks (regression guard pins that genuine unknowns still WARN); every assertion is meaningful (set-difference with named expected files).
**Self-check:** 0 vacuous tests.

**Handoff:** To Dev (Inigo Montoya) for implementation.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- **server** `sidequest/genre/loader.py` — added `GENRE_PACK_ROOT_EXTENSION_FILES: frozenset[str]` (19 names), the loader's half of the single-source-of-truth allowlist (every name has a real genre-root read-site).
- **server** `sidequest/cli/validate/pack.py` — genre-level orphan check now treats the FULL schema extension set as the canonical allowlist (not only pack.yaml-*declared* extensions), so live undeclared files aren't false-orphaned while genuine unknowns still WARN.
- **content** `pack_schema.yaml` — reconciled `genre_pack.extensions` to equal the loader allowlist: removed loader-dead `openings`/`powers`/`weather`/`calendar`/`history` + `spellbook.yaml` file (kept `spells/` dir); added live `skills`/`spells_wwn`/`foci`/`bestiary`/`backgrounds`/`witnessed_acts`/`mutations`/`disciplines_psionic`.
- **content** 5× `pack.yaml` — removed stale extension declarations (`openings` ×3, `powers`, `weather`, `seed_tropes`).
- **content** deleted 5 dead genre files: `{neon_dystopia,pulp_noir,road_warrior,wry_whimsy}/openings.yaml`, `road_warrior/powers.yaml`.

**Tests:** 7/7 story tests pass (113-2). Regression check GREEN: `tests/cli/validate/` 68/68 (the two live-pack tests that broke on the schema edit are fixed), `tests/genre/` load/pack/schema 319 passed / 48 skipped (all 11 packs load). ruff check + ruff format clean on changed files.

**Branches:** `feat/113-2-reconcile-pack-schema-with-loader-allowlist` (server + content) — pushed.

### Dev (rework — round-trip 1, green)
**Reviewer finding addressed:** `[HIGH]` F401 unused `import yaml` in `tests/cli/validate/test_pack_schema_loader_drift_113_2.py:49` failed `ruff check` (project gate).
**Fix:** removed the `import yaml` line — the test parses the schema via `load_pack_schema`, never `yaml` directly. One line, no logic or test-behavior change.
**Verification:** `uv run ruff check` on all 3 changed server files → All checks passed; `ruff format --check` → 3 files already formatted; story tests 7/7 GREEN; `tests/cli/validate/` 68/68 GREEN (via testing-runner). Committed `c00c839d`, pushed to origin.
**Non-blocking Reviewer findings (world-tier orphan asymmetry, `parents[4]` vacuous-path hardening):** acknowledged, left for a future story per Reviewer's own deferral — both are pre-existing and out of 113-2's genre-tier scope. No change made.

**Handoff:** To verify (TEA simplify/quality pass).

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): AC2's drift guard (`test_schema_and_loader_allowlist_agree`) may surface drift beyond the eleven audit-named files. Genre-tier `spellbook.yaml`, `projection.yaml`, `calendar.yaml`, `history.yaml` are listed as schema `genre_pack.extensions` but I could not confirm the loader reads them at the *genre* tier (history/projection reads I found are world-tier). Affects `sidequest-content/pack_schema.yaml` + `sidequest-server/sidequest/genre/loader.py` (Dev: when building `GENRE_PACK_ROOT_EXTENSION_FILES`, reconcile whichever of these the loader does/doesn't read — add to the constant if read, remove from the schema if not; that reconciliation IS the story's "both directions"). *Found by TEA during test design.*
- **Question** (non-blocking): AC3's literal requirement ("validator flags an unknown pack-root YAML, at least WARN") is ALREADY satisfied by the existing `_check_orphans` path (`tests/cli/validate/test_pack_validator.py::test_orphan_file_is_warning` passes). The genuine gap is the inverse — live files the loader reads (skills.yaml etc.) currently *false-orphan* when present-but-undeclared. I pinned that as the RED test and kept a regression guard for the literal text. If Keith intended AC3 to instead mean "surface orphan warnings by default (not only under `--verbose`)", that is a separate change not covered here. Affects `sidequest-server/sidequest/cli/validate/pack.py` (`_check_orphans` must treat the canonical allowlist — not just *declared* extensions — as known). *Found by TEA during test design.*

### Dev (rework)
- No upstream findings. Rework was a one-line lint fix (F401 unused import removal); no new spec gaps or deviations surfaced.

### Dev (implementation)
- **Improvement** (non-blocking): `tea_and_murder/weather.yaml` is a legitimate **weathergen CLI input** (`sidequest/cli/weathergen/weathergen.py` reads `pack_dir/weather.yaml`) but is NOT read by the runtime genre loader (runtime reads `world_dir/weather.yaml` via `world_grounding_bootstrap`). Since `weather` is no longer a schema genre extension, the validator now emits an orphan WARNING for it. Affects `sidequest-content/genre_packs/tea_and_murder/weather.yaml` + `pack_schema.yaml` (consider a schema affordance for tool-only inputs, relocate the file, or accept the benign warning). Kept the file to avoid breaking weathergen. *Found by Dev during implementation.*
- **Gap** (non-blocking): the loader reads several OTHER world-authoritative optional files at the genre root that are in NEITHER schema `required_files` NOR `extensions` (`archetypes`, `tropes`, `cultures`, `char_creation`, `inventory`, `power_tiers`, `visual_style`). These remain outside the 113-2 allowlist (the story scoped to the extension tier) and may still orphan-warn when present-undeclared. Affects `sidequest-content/pack_schema.yaml` (a future story could fold the world-authoritative-optional tier into the canonical allowlist). *Found by Dev during implementation.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **AC3 reframed from "flag unknown YAML" to "don't false-orphan live files"**
  - Spec source: context-story-113-2.md, AC3
  - Spec text: "pack validator flags (at least WARN) an unknown YAML file at a pack root instead of silently ignoring it"
  - Implementation: AC3's literal requirement is already met by the existing `_check_orphans` orphan-warning path (proven by the pre-existing `test_orphan_file_is_warning`). I wrote that as a green regression guard (`test_unknown_pack_root_yaml_is_flagged`) and made the *RED* AC3 test the real gap: a live genre-tier file the loader reads (skills.yaml) present-but-undeclared must NOT be flagged as an orphan (`test_live_genre_root_file_is_not_orphaned`).
  - Rationale: writing a RED test for behavior that already passes would be vacuous. The reconciliation's real validator impact is recognizing live files, not inventing an unknown-file warning that already exists.
  - Severity: minor
  - Forward impact: Dev must make `_check_orphans` treat the canonical allowlist (full schema extension set / loader constant) as known, not only *declared* extensions.
- **AC2 loader-allowlist symbol named by the test (net-new API)**
  - Spec source: context-story-113-2.md, AC2
  - Spec text: "a test asserts schema and loader allowlist agree, so future drift fails CI"
  - Implementation: the test imports a net-new `sidequest.genre.loader.GENRE_PACK_ROOT_EXTENSION_FILES: frozenset[str]`. No such allowlist object exists today (the loader reads files via scattered hard-coded `path / "X.yaml"` calls), so the story must introduce one as the single source of truth.
  - Rationale: AC2 requires the loader allowlist to be a referenceable object; per the No-Source-Text-Wiring-Tests rule the agreement must be tested against real data, not a grep of loader.py.
  - Severity: minor
  - Forward impact: Dev owns the exact symbol; if renamed, update this test's import. The behavior under test (schema == loader allowlist) is fixed.

### Dev (implementation)
- **Removed three MORE dead genre extensions than AC1 named (calendar, history, spellbook.yaml file)**
  - Spec source: context-story-113-2.md, AC1 (+ TEA Improvement finding)
  - Spec text: "openings/powers/weather removed, skills/.../disciplines_psionic added"
  - Implementation: Kept the loader allowlist honest (every file in `GENRE_PACK_ROOT_EXTENSION_FILES` has a real genre-root read-site). Since AC2's equality test requires schema-extension-files == loader allowlist, I also dropped `calendar` (no genre-tier read), `history` (world-tier only; the loader reads `world_path/history.yaml`, never the genre copy), and `spellbook`'s `spellbook.yaml` file (the loader reads the `spells/` DIR — kept — not the file). Confirmed: zero packs declare or ship genre-tier calendar/history/spellbook, so no pack regressed.
  - Rationale: TEA's finding explicitly authorized "remove from the schema if [the loader does] not [read it]"; this IS the "drifted in both directions" the story closes. A dishonest constant (listing files the loader never reads) would violate No-Silent-Fallbacks.
  - Severity: minor
  - Forward impact: none — these were already loader-dead at the genre tier.
- **Reconciled 5 packs' pack.yaml + deleted 5 dead genre files (content half)**
  - Spec source: context-story-113-2.md, AC1; session Repos line (server, content)
  - Spec text: schema/loader reconciliation (repos: server, content)
  - Implementation: removing the dead extension DEFINITIONS from the schema made `_check_extensions` error on packs still DECLARING them, so I removed the stale declarations: `openings` (neon_dystopia, pulp_noir, wry_whimsy), `powers` (road_warrior), `weather` (tea_and_murder), and the pre-existing stale `seed_tropes` (wry_whimsy — retired to world-tier in #439 but never un-declared). Deleted the 4 dead genre `openings.yaml` + `road_warrior/powers.yaml`. Kept `tea_and_murder/weather.yaml` (a weathergen CLI input — see finding).
  - Rationale: required for GREEN on `test_all_live_packs_pass_content_validation`; the coupled content change the session anticipated. Dead files deleted per "delete dead code in the same PR".
  - Severity: minor
  - Forward impact: none for runtime; world-tier openings/seed_tropes unaffected (each world ships its own).

### Reviewer (audit)
- **TEA — AC3 reframed (false-orphan, not unknown-flag)** → ✓ ACCEPTED by Reviewer: writing a RED test for already-passing behavior would be vacuous; the live-file-false-orphan gap is the real validator impact of the reconciliation, and the literal AC3 text is kept as a green regression guard (`test_unknown_pack_root_yaml_is_flagged`), which I verified still flags `tea_and_murder/weather.yaml` and a synthetic `totally_unknown_xyz.yaml`. Both halves of AC3 are honored.
- **TEA — AC2 net-new `GENRE_PACK_ROOT_EXTENSION_FILES` symbol** → ✓ ACCEPTED by Reviewer: a referenceable data object tested against real schema data is the No-Source-Text-Wiring-Tests-compliant way to satisfy AC2; verified the symbol is a module-level `frozenset[str]` and the drift guard imports it and asserts exact set equality.
- **Dev — removed 3 more dead extensions (calendar, history, spellbook.yaml file)** → ✓ ACCEPTED by Reviewer: independently confirmed each is loader-dead at the genre tier (`history` reads only `world_path/history.yaml` at loader.py:1249; no genre-tier `calendar`/`spellbook.yaml` read anywhere; `spells/` dir retained). Keeping the constant honest is mandatory under No-Silent-Fallbacks; this IS the "both directions" reconciliation the story exists to close.
- **Dev — reconciled 5 pack.yaml + deleted 5 dead genre files** → ✓ ACCEPTED by Reviewer: required for GREEN (`_check_extensions` errors on declarations whose schema entry was removed); deleting the 5 dead files (`powers.yaml` has zero server read-sites; the 4 `openings.yaml` are genre-tier-dead, loader reads only `worlds/{slug}/openings.yaml`) satisfies "delete dead code in the same PR". Scan confirms the cleanup is complete — only the intentional `tea_and_murder/weather.yaml` weathergen input remains.
- **No undocumented deviations found.** Spec scope (genre/extension tier) matches the implementation; the world-tier orphan symmetry and world-authoritative-optional tier are explicitly out of scope and already logged as non-blocking findings by Dev/TEA/Reviewer.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 blocking lint (F401) + 1 pre-existing genre failure | confirmed 1 (F401), dismissed 1 (pre-existing, not a regression) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings (workflow.reviewer_subagents.edge_hunter=false) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 4 | confirmed 0 blocking, deferred 2 (world-tier asymmetry, vacuous-pass hardening — both non-blocking/out-of-scope), dismissed 2 (pre-existing/intended) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings (test_analyzer=false) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings (comment_analyzer=false) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (type_design=false) |
| 7 | reviewer-security | Yes | clean | none | N/A (clean — 5 topics assessed, no findings) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings (simplifier=false) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings (rule_checker=false) |

**All received:** Yes (3 enabled returned, 6 disabled pre-filled)
**Total findings:** 1 confirmed blocking (F401), 2 deferred non-blocking, 3 dismissed (with rationale)

### Rule Compliance

- **No Silent Fallbacks** (CLAUDE.md / server CLAUDE.md): the widened orphan allowlist (`all_genre_ext_files` from full schema keys) does NOT silence genuine unknowns — a file in neither `required_files` nor the schema extension set still WARNs. Verified independently: only `tea_and_murder/weather.yaml` orphan-warns across all 11 packs, which is intended. **COMPLIANT.**
- **No Stubbing / Delete dead code in same PR**: `GENRE_PACK_ROOT_EXTENSION_FILES` — every one of the 19 names has a confirmed genre-root read-site in loader.py (verified line-by-line). 5 dead content files deleted; `powers.yaml`/genre-tier `openings.yaml` confirmed zero live read-sites. **COMPLIANT** — except the new test's unused `import yaml` (F401) is itself dead code → the one violation (see assessment).
- **No Source-Text Wiring Tests**: AC2's drift guard tests data (`frozenset` vs parsed schema), not source grep. **COMPLIANT.**
- **Tests must not iterate over live content packs**: fixtures synthesised in `tmp_path`; the single allowed exception (reading the real `pack_schema.yaml`, the artifact under reconciliation) matches existing `test_pack_validator.py` convention. **COMPLIANT.**
- **OTEL Observability**: N/A — this is dev-tooling/validation + schema reconciliation, not a runtime subsystem decision; cosmetic-exempt per the principle. **N/A.**

## Delivery Findings

<!-- Reviewer: append below -->

### Reviewer (code review)
- **Gap** (blocking): the new test file `tests/cli/validate/test_pack_schema_loader_drift_113_2.py` has an unused `import yaml` (F401) — `ruff check` exits non-zero, failing the project gate. Affects `sidequest-server/tests/cli/validate/test_pack_schema_loader_drift_113_2.py:49` (remove the line; `yaml` is unused — the test parses the schema via `load_pack_schema`). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): world-tier orphan check (`pack.py:1062-1066`) builds its genre-override allowlist from `genre_extensions_declared` only, NOT the full schema key set the genre-tier check now uses — a world override of an undeclared-but-loader-read file (e.g. `worlds/x/skills.yaml` when the pack doesn't declare `skills`) would still false-orphan-WARN. Pre-existing, out of 113-2's genre-tier scope; mirrors Dev's world-authoritative-optional Gap. Affects `sidequest-server/sidequest/cli/validate/pack.py` (a future story could widen the world-tier allowlist symmetrically). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the drift-guard test's `schema_path_real` (`parents[4]`) resolves to an empty/missing path silently if the cross-repo layout changes; `test_dead_genre_extensions_removed` could then pass vacuously (the agreement + live-files tests would still fail loudly, so the suite as a whole is safe). A module-level `assert schema_path_real.is_file()` would harden it. Affects `sidequest-server/tests/cli/validate/test_pack_schema_loader_drift_113_2.py:193`. *Found by Reviewer during code review.*

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | `[SIMPLE]`/preflight: unused `import yaml` (F401) — `ruff check` exits non-zero, failing the `server-check` / `check-all` project gate | `sidequest-server/tests/cli/validate/test_pack_schema_loader_drift_113_2.py:49` | Remove `import yaml` (the test uses `load_pack_schema`, not `yaml` directly). Re-run `uv run ruff check` to confirm clean. |

**Why REJECTED:** A single blocking finding, but it is a hard gate failure — `ruff check` is part of `server-check`/`check-all`, so the PR cannot merge clean and the dead import violates the project's "delete dead code" rule. The fix is lint-only (one line, no logic, no test-behavior change), so this routes to **Dev (green rework)**, not TEA.

**Substance is sound — independently verified (the work is correct; only the lint blocks):**
- `[TEST]` AC2 drift guard: I re-derived the two file sets independently — schema `genre_pack.extensions[*].files` (19) **exactly equals** loader `GENRE_PACK_ROOT_EXTENSION_FILES` (19), zero asymmetric members. The guard genuinely fails CI on future drift.
- `[VERIFIED]` Constant honesty (No-Silent-Fallbacks): all 19 names have a real genre-pack-root read-site in `loader.py` (e.g. `magic.yaml`:1373, `skills.yaml`:1937, `bestiary.yaml`:1995, `disciplines_psionic.yaml`:1977, `pacing.yaml`:1870, `seed_tropes.yaml`:1836) — verified each `path / "X.yaml"` call inside the genre-tier load functions. The constant does not lie.
- `[VERIFIED]` Removed/dead files: `openings` (genre-tier tombstoned; reads only `worlds/{slug}/openings.yaml`), `powers` (zero server read-sites), `calendar`/`history` (no genre-tier read; `history` reads `world_path/history.yaml`:1249), `spellbook.yaml` file (loader reads the `spells/` dir, retained). All genuinely loader-dead at the genre tier.
- `[SEC]` security subagent: **clean** — bare-basename allowlist (no `..`/separators), `iterdir().name` comparison (no path construction from input), dev-only CLI warnings (no info leakage), all 5 deleted files have zero live read-sites. Cross-repo `parents[4]` path is pre-existing convention, not a vuln.
- `[SILENT]` silent-failure subagent: the orphan-allowlist widening does NOT silence genuine unknowns (confirmed — only the intended `weather.yaml` warns); world-tier asymmetry + vacuous-path are non-blocking/out-of-scope (deferred above).
- Dead-file cleanup is **complete**: scan of all 11 packs shows only the intentional `tea_and_murder/weather.yaml` (weathergen CLI input, Dev-documented) remains as an orphan-WARN.

**Disabled lenses (no coverage claimed):** `[EDGE]` `[DOC]` `[TYPE]` `[RULE]` `[SIMPLE]` `[TEST]`-analyzer subagents are disabled via `workflow.reviewer_subagents`. I covered their domains manually where load-bearing: type design (the `frozenset[str]` constant is well-typed), simplification (no over-engineering; the orphan widening is the minimal correct change), and rule compliance (see `### Rule Compliance`). Edge/doc surface is minimal for a schema-reconciliation diff.

### Devil's Advocate

Suppose this code is broken. The most dangerous failure mode for a *reconciliation* story is a guard that passes while the two artifacts silently disagree — a false sense of safety. Could the drift guard pass vacuously? I checked: if `load_pack_schema` returned an empty dict (bad cross-repo path), `test_dead_genre_extensions_removed` would pass vacuously (`DEAD & {} = {}`), BUT `test_live_genre_extensions_added` (`LIVE - {} = LIVE`, 8 items → assert fails) and `test_schema_and_loader_allowlist_agree` (`loader_only` = 19 → assert fails) would both fail loudly. So the suite cannot greenlight a missing schema — the vacuous path is contained. Could the constant claim a file the loader never reads, defeating the orphan check by widening the allowlist past reality? I enumerated all 19 against `loader.py` read-sites; none are phantom. Could a malicious/confused author drop a sensitive file (`secrets.yaml`) at a pack root and have it silently accepted? No — it's neither required nor in the schema extension set, so it WARNs. Could the deletion have orphaned a runtime read? `powers.yaml` and genre-tier `openings.yaml` have zero live read-sites (grepped). Could the schema and loader drift the moment someone adds a 20th file to only one side? That is exactly what the guard catches — and it's wired (imports the real symbol, reads the real schema). The one real wart the devil finds is the unused `import yaml` — dead code in a story whose whole point is *removing* dead declarations, which is a fitting irony and precisely why it must not ship. No deeper break surfaced; the logic is sound, the bounce is purely mechanical.

**Handoff:** Back to Dev (Inigo Montoya) for the one-line lint fix (green rework — lint-only).

---

## Subagent Results (round-trip 2 — rework re-review)

Rework delta is exactly the 2-line removal of `import yaml` (commit `c00c839d`, `1 file changed, 2 deletions`). The previously-confirmed substance (schema↔loader equality, constant honesty, dead-file deletion, security posture) is byte-for-byte unchanged — removing a dead import cannot touch the security or silent-failure domains, so those lenses carry forward from round-trip 1. Preflight was re-run because it found the blocker.

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (blocker resolved) | N/A — ruff check exit 0, format clean, story 7/7, validate 68/68 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings (edge_hunter=false) |
| 3 | reviewer-silent-failure-hunter | Yes (carried fwd) | findings | 0 new | re-assessed: rework removes only a dead import; the 2 deferred non-blocking findings from RT1 (world-tier asymmetry, vacuous-path hardening) are unchanged and remain deferred |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings (test_analyzer=false) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings (comment_analyzer=false) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (type_design=false) |
| 7 | reviewer-security | Yes (carried fwd) | clean | none | re-assessed: a dead-import removal introduces no security surface; RT1 clean verdict stands |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings (simplifier=false) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings (rule_checker=false) |

**All received:** Yes (preflight re-run clean; security + silent-failure carried forward unchanged; 6 disabled pre-filled)
**Total findings:** 0 new; RT1's 1 blocking finding (F401) is RESOLVED; 2 non-blocking deferrals stand.

### Rule Compliance (round-trip 2)

- **No Stubbing / Delete dead code:** the F401 unused `import yaml` — itself dead code — is now removed. **COMPLIANT** (the one RT1 violation is closed).
- **No Silent Fallbacks / No Source-Text Wiring Tests / tests-not-on-live-content:** unchanged by the rework — all **COMPLIANT** as verified in round-trip 1.

## Reviewer Assessment (round-trip 2)

**Verdict:** APPROVED

**Data flow traced:** developer-authored `pack_schema.yaml` → `load_pack_schema()` → `genre_pack.extensions[*].files` set ↔ `loader.GENRE_PACK_ROOT_EXTENSION_FILES` frozenset; the drift-guard test asserts exact equality (19 == 19, re-confirmed this round). The orphan check resolves the full schema extension set as the allowlist; genuine unknowns still WARN (only the intentional `tea_and_murder/weather.yaml` warns across all 11 packs). Safe — no user input flows through any of this (dev-tooling + schema reconciliation).

**Pattern observed:** single-source-of-truth allowlist enforced by a data-driven CI drift guard — `sidequest/genre/loader.py:105` (constant) ↔ `sidequest-content/pack_schema.yaml:46` (schema), guarded by `tests/cli/validate/test_pack_schema_loader_drift_113_2.py:330`.

**Error handling:** orphan check fails-loud (WARN) on genuinely unknown files; loader reads stay fail-loud per No-Silent-Fallbacks (verified RT1).

**Resolution of RT1 blocker:** `[SIMPLE]` F401 unused `import yaml` removed (commit `c00c839d`); `ruff check` now exits 0 (preflight-confirmed), the `server-check`/`check-all` gate passes. Rework delta verified to be *only* the import removal — no scope creep.

**Lens dispatch tags (this story):** `[SIMPLE]` blocker resolved · `[SEC]` clean (carried fwd) · `[SILENT]` 2 non-blocking deferrals stand (carried fwd) · `[TEST]` story 7/7 + validate 68/68 green · `[EDGE]` `[DOC]` `[TYPE]` `[RULE]` disabled lenses, domains covered manually in RT1 (minimal surface for a schema-reconciliation diff).

### Devil's Advocate (round-trip 2)

Could the rework have introduced a regression while "just" deleting a line? The git delta proves it removed exactly `import yaml` and its trailing blank — no logic line touched. Could removing the import break a runtime usage of `yaml`? No: the test parses the schema via `load_pack_schema`, and the post-fix `ruff check` (which would flag an *undefined* name as F821) plus a green 7/7 run prove `yaml` was never referenced. Could the bounce-and-fix have drifted the schema/loader sets? I re-ran the equality computation independently this round: still 19 == 19, exact. Could a stale tree be masking the result? Preflight ran against the committed `c00c839d` HEAD with a clean working tree. There is nothing left to find — the substance was sound in RT1 and the only open item, the lint gate, is now green.

### Reviewer (audit — round-trip 2)
- **Dev (rework) "No upstream findings"** → ✓ ACCEPTED by Reviewer: the rework introduced no new spec deviation; a lint-only fix has no design surface. All RT1 deviation stamps stand.

### Reviewer (code review — round-trip 2)
- No new upstream findings. The RT1 blocking F401 is resolved; the two RT1 non-blocking Improvements (world-tier orphan symmetry, `parents[4]` vacuous-path hardening) remain valid future work, unchanged.

**Handoff:** To SM (Vizzini) for finish-story.