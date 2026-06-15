---
story_id: "114-12"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 114-12: Complete CWN/WN inventory verbatim round-trip + harden the WN extraction CLIs

## Story Details
- **ID:** 114-12
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 5
- **Epic:** 114 (LEAD)
- **Repos:** server, content

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-15T23:49:52Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-15T23:20:21.930021Z | 2026-06-15T23:22:23Z | 2m 1s |
| red | 2026-06-15T23:22:23Z | 2026-06-15T23:32:38Z | 10m 15s |
| green | 2026-06-15T23:32:38Z | 2026-06-15T23:40:53Z | 8m 15s |
| review | 2026-06-15T23:40:53Z | 2026-06-15T23:49:52Z | 8m 59s |
| finish | 2026-06-15T23:49:52Z | - | - |

## Story Context (from Architect brief)

### Scope
This is the LEAD of epic 114, settling the `CatalogItem`/`DamageSpec` schema before downstream stories (114-13, 114-15, 114-10) author against it. The work is completing round-trip field extraction for both CWN and WWN equipment CLIs plus hardening argument parsing.

### Existing State
The two extraction CLIs are shipped and green (114-3/114-5). `CatalogItem` already carries `armor_class` (ascending AC), `mitigation` (SWN soak), `damage` (`DamageSpec` with `bonus`, `armor_piercing`, `trauma_die`, `trauma_rating`, `trauma_target`, `shock`, `shock_ac`), `system_strain`, `provenance`. Much of this story is wiring existing-but-unextracted fields into the parsers, plus DRY/hardening — NOT model additions.

### Technical Approach (RED→GREEN, TDD)
Extract a shared `wn_equip_core.py` module; keep two THIN CLI entry points (the `python -m sidequest.cli.wwn_equip_extract` / `cwn_equip_extract` entry points are pinned by wiring tests — do NOT collapse to one CLI). Shared core owns helpers + section parsers + `extract_catalog(srd_text, *, srd, license, sections)`; each CLI passes its own `_SECTION_PARSERS` (WWN 4 sections; CWN 5 incl. cyberware).

### RED (TEA) Test Suite
1. **DRY parity guard** — drive both `extract_catalog`s over a shared armor/melee/ranged/general row, assert identical handling (Behavioral — NO source-grep wiring test; project rule "No Source-Text Wiring Tests")
2. **Dual-AC/soak** — CWN armor carries both `armor_class` AND `mitigation`; WWN single-AC leaves `mitigation=None`
3. **Trauma-Target** — CWN melee populates trauma_die/rating/target verbatim; `None`/`-` cell emits no trauma fields (mirror `_NA_CELLS`)
4. **Ranged +N** — `1d8+2` → `dice=="1d8"`, `bonus==2`; plain `1d6` → `bonus==0`
5. **Hardening** — `--srd-path` `.resolve()`d; `--srd`/`--license` argparse `choices` (invalid → SystemExit)
6. **Verbatim round-trip** — `model_dump()` → `CatalogItem(**dump)` and CLI-stdout JSON round-trip for every fixture incl. new fields

### Concrete File List

**Production (edit):**
- `sidequest-server/sidequest/cli/wwn_equip_extract/wwn_equip_extract.py` — thin entry; delegate to core; `.resolve()`/`choices`
- `sidequest-server/sidequest/cli/cwn_equip_extract/cwn_equip_extract.py` — same; retains cyberware section
- `sidequest-server/sidequest/cli/wn_equip_extract_core.py` — NEW shared core

**Production (verify, likely no change):**
- `sidequest-server/sidequest/genre/models/inventory.py` — `CatalogItem`/`DamageSpec` already carry every target field (⚠️ SHARED SURFACE: 114-13/114-15 read it; 114-10 adds Fate fields)
- `sidequest-server/sidequest/server/dispatch/inventory_resolve.py` — `_MECHANICAL_FIELDS`/`_FIELD_DEFAULTS` lock list (⚠️ SHARED SURFACE: 114-13 adds a category constant here)

**Tests (edit/add):**
- `sidequest-server/tests/cli/test_wwn_equip_extract.py`, `tests/cli/test_cwn_equip_extract.py`
- `sidequest-server/tests/cli/test_wn_equip_core.py` — NEW parity/DRY test

**Fixtures (edit):**
- `sidequest-server/tests/fixtures/wwn_srd/equipment_chapter.txt` — add `+N` ranged row
- `sidequest-server/tests/fixtures/cwn_srd/equipment_chapter.txt` — add soak column to armor, Trauma column to melee, `+N` ranged row

### Acceptance Criteria
1. Both CLIs route armor/melee/ranged/general through a single shared `wn_equip_core`; CWN-only cyberware stays CWN-side; parity test asserts identical output on a shared row
2. CWN armor populates `armor_class` AND `mitigation` verbatim; WWN single-AC leaves `mitigation=None`
3. CWN melee populates `trauma_die`/`trauma_rating`/`trauma_target` verbatim; `None`/`-` cell emits no trauma fields
4. Ranged parses `NdM+B` → `dice`+`bonus`; plain `NdM` → `bonus==0`
5. Every fixture survives `model_dump()`→`CatalogItem(**dump)` and CLI-stdout JSON round-trip with new fields intact
6. `main()` resolves `--srd-path` via `Path.resolve()`; `--srd`/`--license` `choices`-constrained (invalid → SystemExit)
7. All pre-existing 114-3/114-5 tests stay green
8. `just server-check` (ruff + pytest + pyright) passes

### Cross-Story Dependencies
- **114-12 ↔ 114-15:** Coupling reduces to the `CatalogItem` model (114-15 recommends hand-transcribe SWN, so extraction-core overlap does not materialize). 114-12 lands first → 114-15 authors against final schema
- **114-12 ↔ 114-10:** Fate gear adds new fields to `CatalogItem`/`_MECHANICAL_FIELDS`. 114-12 only reads existing fields. Sequence 114-12 before 114-10 to avoid model merge race (114-10 is p3)
- **114-12 ↔ 114-13:** No extraction-file overlap; 114-13 consumes emitted category vocabulary, edits `inventory_resolve.py`. Land 114-12 first

### Special Notes
- OTEL: extraction CLIs are offline authoring tools, not a runtime subsystem — the "OTEL-on-every-subsystem" rule does NOT apply. Do not invent spans
- No `CatalogItem`/`DamageSpec` model changes expected unless round-trip surfaces a gap
- The shared core must NOT collapse the two CLI entry points (wiring tests pin them separately)

## Branch Strategy
**Branch Strategy:** gitflow (feat/114-12-cwn-wn-verbatim-roundtrip-harden-extraction)

## Sm Assessment

**Story is RED-ready.** Setup complete, branches cut in both repos at `develop`, full Architect scoping brief folded into Story Context above.

**Technical approach (confirmed sound):** This is a wiring/DRY/hardening story, not a model-design story. The Architect verified `CatalogItem`/`DamageSpec` already carry every target field (`mitigation`, `trauma_*`, `bonus`) — the parsers just don't populate them yet. So the RED suite asserts *extraction behavior + round-trip*, and GREEN populates parsers + DRYs the shared core + hardens argparse. No model surgery expected; if round-trip surfaces a model gap, that's a real finding, not the plan.

**Sequencing rationale (why this story leads epic 114):** All four unblocked 114 stories share the hot files `genre/models/inventory.py` and `inventory_resolve.py`, so they cannot run as parallel implementations — one branch per working tree. 114-12 settles the `CatalogItem`/`DamageSpec` schema and DRYs the WN-extraction core; 114-13 (category constant in `inventory_resolve.py`), 114-15 (regression depends on the schema), and 114-10 (Fate fields on `CatalogItem`/`_MECHANICAL_FIELDS`) all author against it. Land this first or everyone rebases on a moving target.

**TEA watch-items for RED:**
- Honor the "No Source-Text Wiring Tests" rule — the DRY parity guard must be *behavioral* (drive both `extract_catalog`s over a shared row, assert identical output), not a grep that both CLIs import the core.
- Do NOT collapse the two CLI entry points; existing wiring tests pin `wwn_equip_extract` and `cwn_equip_extract` separately. The shared core sits beneath both.
- OTEL spans do NOT apply here — these are offline authoring CLIs, not a runtime subsystem. Don't invent spans to satisfy the observability rule.
- `_DICE_RE` rejects a `+B` suffix; prefer splitting `1d8+2`→`dice=1d8, bonus=2` in `_parse_ranged` over widening the regex.

**ACs:** 8 testable criteria in Story Context; the gate is `just server-check` (ruff + pytest + pyright) green plus all 114-3/114-5 regressions intact.

**Jira:** none assigned (story has no jira_key) — claim skipped intentionally.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): The "DRY shared WN-extraction core" cannot share ALL four common sections — CWN armor adds a Soak column and CWN melee adds a Trauma column, so `_parse_armor`/`_parse_melee` genuinely diverge between WWN and CWN. Only `general` and `ranged` are byte-identical and truly shareable. The shared core should factor the common HELPERS (`_slugify`, `_provenance`, `_data_rows`, `_row_context`, `_split_trailing`, `_slice_section`, the `extract_catalog` driver, the licensing gate) + the `general`/`ranged` parsers, while `armor`/`melee` get a WWN variant and a CWN variant (CWN reads the extra column). Affects `sidequest/cli/wn_equip_extract_core.py` (the new core's parser-sharing boundary). *Found by TEA during test design.*
- **Question** (non-blocking): The synthetic CWN Trauma cell format (`<die>/x<rating>/T<target>`, e.g. `1d10/x2/T6`, or `None`) is a TEA invention for the fixture — the real CWN SRD melee table represents Trauma differently. Dev should confirm the real column shape against the SRD when wiring the parser; the tests assert only the RESULT fields (`trauma_die`/`trauma_rating`/`trauma_target`), so the parse format is free to change. Affects `cwn_equip_extract` melee parsing. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): The TEA armor/melee divergence finding is resolved WITHOUT forking — `parse_armor`/`parse_melee` live once in the shared core and take a `has_soak`/`has_trauma` keyword, bound per-CLI via `functools.partial`. So all four common sections (armor/melee/ranged/general) genuinely route through the single `wn_equip_extract_core` module (AC1), and the soak/Trauma divergence is a parameter, not a copy. Downstream 114-15: a future `swn_equip_extract` can reuse this core by passing its own `section_parsers` table — `WN_SRD_CHOICES` already includes `"swn"`. Affects `sidequest/cli/wn_equip_extract_core.py`. *Found by Dev during implementation.*
- **Question** (non-blocking): The real CWN SRD Trauma/Soak column shapes were NOT verified against the actual SRD (offline, no PDF in-repo) — the parser is pinned to the synthetic fixture format. When the real CWN equipment text is run through this tool, the Trauma/Soak column parsing may need a format adjustment; the field semantics (`mitigation`, `trauma_die/rating/target`) are correct regardless. Affects `cwn_equip_extract`/`wn_equip_extract_core` melee+armor parsing. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): Test-polish punch-list — all LOW, none block. (1) `test_wn_equip_core.py:435` `assert os.path.isabs(resolved)` is tautological (resolve() always returns absolute) — drop it; the load-bearing `resolved in err` assertion at :436 stands. (2) AC6 choices tests use bare `pytest.raises(SystemExit)` without asserting `.value.code == 2`. (3) `Path.resolve()` resolved-relative-message behavior is tested for `cwn_main` only, not `wwn_main` (the wwn `.resolve()` exists at wwn:105 and the wwn suite is green, so this is a coverage-symmetry gap not a bug). (4) AC1 DRY is asserted behaviorally (general/ranged parity) but not structurally; a reflection identity check (`parse_general is core.parse_general`) would harden it — I verified the wiring is real by diff (both CLIs import the parsers from the core). Affects `tests/cli/test_wn_equip_core.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Comment/doc staleness — LOW. (1) The `TOOL_VERSION` comment in `wwn_equip_extract.py:56` copy-pastes "referenced by tests/server/test_cwn_inventory_wiring" from the CWN file; the WWN version string is actually pinned by `tests/cli/test_wwn_equip_extract.py:87` (the CWN file's comment IS accurate — that test exists). (2) `test_wn_equip_core.py:1` opens "RED-phase tests … RED until 114-12 lands" — now stale post-implementation; reword to describe what the tests verify. Affects `sidequest/cli/wwn_equip_extract/wwn_equip_extract.py`, `tests/cli/test_wn_equip_core.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `wn_equip_extract_core.py` defines no `__all__`. Not a codebase convention (only ~19% of modules use it; zero sibling CLI modules do) and module privates use the underscore-prefix convention correctly, so practical risk is nil — noting for consistency only. Affects `sidequest/cli/wn_equip_extract_core.py`. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 1 findings (0 Gap, 0 Conflict, 0 Question, 1 Improvement)
**Blocking:** None

- **Improvement:** The "DRY shared WN-extraction core" cannot share ALL four common sections — CWN armor adds a Soak column and CWN melee adds a Trauma column, so `_parse_armor`/`_parse_melee` genuinely diverge between WWN and CWN. Only `general` and `ranged` are byte-identical and truly shareable. The shared core should factor the common HELPERS (`_slugify`, `_provenance`, `_data_rows`, `_row_context`, `_split_trailing`, `_slice_section`, the `extract_catalog` driver, the licensing gate) + the `general`/`ranged` parsers, while `armor`/`melee` get a WWN variant and a CWN variant (CWN reads the extra column). Affects `sidequest/cli/wn_equip_extract_core.py`.

### Downstream Effects

- **`sidequest/cli`** — 1 finding

### Deviation Justifications

2 deviations

- **Inline fixture text instead of mutating the shared `equipment_chapter.txt` files**
  - Rationale: Mutating the shared fixtures' columns makes the OLD parser raise/misparse during RED, which would turn every pre-existing 114-3/114-5 count/entrypoint test red and force editing those test files — conflating "feature missing" with "everything broken." Inline text is the codebase's own idiom for parser edge cases (cf. `test_none_shock_melee_weapon_emits_without_inventing_shock`) and keeps RED failures attributable to one capability each. Pre-existing suites stayed 37/37 green.
  - Severity: minor
  - Forward impact: Dev MAY still enrich the shared fixtures in GREEN if desired, but it is not required — the behavioral contract is fully pinned by the inline tests.
- **Updated the shared `cwn_srd/equipment_chapter.txt` to the dual-AC/Trauma schema; did NOT add separate `+N` ranged rows to the shared fixtures**
  - Rationale: The new CWN parser needs the new columns present; updating the shared fixture in-place (no row count change) realigns with the File List while preserving the 37/37 pre-existing green that TEA's inline-only choice protected. Skipping the `+N` shared-fixture row avoids count-assertion churn with zero loss of coverage.
  - Severity: minor
  - Forward impact: none — counts unchanged, all pre-existing tests still green; AC4 (ranged +N) fully covered by inline tests.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Inline fixture text instead of mutating the shared `equipment_chapter.txt` files**
  - Spec source: context-story-114-12.md, "Concrete File List" → Fixtures
  - Spec text: "`tests/fixtures/wwn_srd/equipment_chapter.txt` — add `+N` ranged row" / "`cwn_srd/equipment_chapter.txt` — add soak column to armor, Trauma column to melee, `+N` ranged row"
  - Implementation: New-schema rows are exercised via INLINE text builders (`_wwn_text`/`_cwn_text`) inside `tests/cli/test_wn_equip_core.py`; the shared fixture files are left unchanged. The round-trip AC is covered by dedicated new-field items (not the shared file's items).
  - Rationale: Mutating the shared fixtures' columns makes the OLD parser raise/misparse during RED, which would turn every pre-existing 114-3/114-5 count/entrypoint test red and force editing those test files — conflating "feature missing" with "everything broken." Inline text is the codebase's own idiom for parser edge cases (cf. `test_none_shock_melee_weapon_emits_without_inventing_shock`) and keeps RED failures attributable to one capability each. Pre-existing suites stayed 37/37 green.
  - Severity: minor
  - Forward impact: Dev MAY still enrich the shared fixtures in GREEN if desired, but it is not required — the behavioral contract is fully pinned by the inline tests.

### Dev (implementation)
- **Updated the shared `cwn_srd/equipment_chapter.txt` to the dual-AC/Trauma schema; did NOT add separate `+N` ranged rows to the shared fixtures**
  - Spec source: context-story-114-12.md, "Concrete File List" → Fixtures
  - Spec text: "`cwn_srd/equipment_chapter.txt` — add soak column to armor, Trauma column to melee, `+N` ranged row" / "`wwn_srd/...` — add `+N` ranged row"
  - Implementation: Added the Soak column to the 2 CWN armor rows and a Trauma column to the 2 CWN melee rows (row COUNT unchanged at 10, so the pre-existing 114-5 count/entrypoint tests stay green). The CWN parser binds `has_soak=True`/`has_trauma=True`, which REQUIRES those columns, so the shared fixture had to match. Did NOT add `+N` ranged rows to either shared fixture (would change item counts and break pre-existing count assertions); ranged `+N` is covered by inline tests in `test_wn_equip_core.py` instead. The WWN fixture is unchanged (WWN binds `has_soak=False`/`has_trauma=False`, i.e. the old single-AC/no-Trauma layout).
  - Rationale: The new CWN parser needs the new columns present; updating the shared fixture in-place (no row count change) realigns with the File List while preserving the 37/37 pre-existing green that TEA's inline-only choice protected. Skipping the `+N` shared-fixture row avoids count-assertion churn with zero loss of coverage.
  - Severity: minor
  - Forward impact: none — counts unchanged, all pre-existing tests still green; AC4 (ranged +N) fully covered by inline tests.

### Reviewer (audit)
- **TEA: inline fixture text instead of mutating shared fixtures** → ✓ ACCEPTED by Reviewer: sound — preserves clean attributable RED and the 37/37 pre-existing green; inline text is the codebase's documented idiom for parser edge cases.
- **Dev: updated shared `cwn_srd/equipment_chapter.txt` to dual-AC/Trauma schema, skipped `+N` shared-fixture rows** → ✓ ACCEPTED by Reviewer: necessary co-change (the `has_soak=True`/`has_trauma=True` parser requires the columns), row count held at 10 so pre-existing CWN tests stay green, and AC4 is fully covered by inline tests — skipping the `+N` shared rows correctly avoids count-assertion churn with zero coverage loss.
- No undocumented deviations found: the WWN fixture is correctly unchanged (WWN binds the no-extra-column variant), and the public-API surface change (private `_parse_*` → public core parsers) is the intended DRY refactor, not a silent contract change.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-server/sidequest/cli/wn_equip_extract_core.py` (NEW) — shared WN-extraction core: helpers (`slugify`/`provenance`/`data_rows`/`row_context`/`split_trailing`/`slice_section`/`section_ref`), the licensing gate + `extract_catalog` driver, and the section parsers. `parse_armor`/`parse_melee` take `has_soak`/`has_trauma` (dual-AC/soak + Trauma); `parse_ranged` splits `NdM+B` → dice+bonus; `parse_general` shared. `WN_SRD_CHOICES`/`WN_LICENSE_CHOICES` allowlists.
- `sidequest-server/sidequest/cli/wwn_equip_extract/wwn_equip_extract.py` — thinned onto the core; binds `has_soak=False`/`has_trauma=False`; argparse `choices` + `Path.resolve()` hardening.
- `sidequest-server/sidequest/cli/cwn_equip_extract/cwn_equip_extract.py` — thinned onto the core; binds `has_soak=True`/`has_trauma=True`; keeps CWN-only `parse_cyberware` local; same hardening.
- `sidequest-server/tests/fixtures/cwn_srd/equipment_chapter.txt` — Soak column on armor, Trauma column on melee (10 rows unchanged).

**How each AC is met:**
- AC1 (single shared core): all four common parsers live in `wn_equip_extract_core`; cyberware stays CWN-side. Behavioral parity tests for general/ranged green.
- AC2 (dual-AC/soak): `parse_armor(has_soak=True)` populates `mitigation`; WWN leaves it None; `-` soak → None.
- AC3 (Trauma): `parse_melee(has_trauma=True)` populates trauma_die/rating/target; `None` → no trauma fields; WWN unaffected.
- AC4 (ranged +N): `_RANGED_DAMAGE_RE` splits `1d8+2` → dice=`1d8`, bonus=`2`; plain → bonus 0; malformed → loud row-context error.
- AC5 (round-trip): model_dump→reconstruct + CLI-stdout JSON round-trip green.
- AC6 (hardening): `choices` on `--srd`/`--license` (bogus → SystemExit); `Path.resolve()` so the missing-file error names the absolute path.
- AC7 (no regression): pre-existing 114-3/114-5 suites 37/37 green; integration tests (cwn_inventory_wiring, catalog_item_system_strain) 9/9 green.
- AC8 (quality gate): ruff check clean, ruff format applied, pyright 0 errors on all changed files.

**Tests:** 66/66 passing (GREEN) — 20 new + 37 pre-existing CLI + 9 integration. ruff clean, pyright 0 errors.
**Branch:** `feat/114-12-cwn-wn-verbatim-roundtrip-harden-extraction` (server) — pushing.

**Handoff:** To verify (TEA simplify + quality-pass).

**Tests Required:** Yes
**Reason:** 5pt feature story (dual-AC/soak extraction, Trauma fields, ranged +N, DRY core, argparse hardening) — not a chore-bypass candidate.

**Test Files:**
- `sidequest-server/tests/cli/test_wn_equip_core.py` — 18 tests (20 with parametrization) covering all 6 deliverables: DRY parity (general/ranged), dual-AC/soak, Trauma-Target, ranged +N, model + CLI-stdout round-trip, argparse choices + Path.resolve hardening.

**Tests Written:** 20 test items covering 6 ACs (AC1–AC6). AC7 (no regression) verified separately; AC8 (`just server-check`) is the Dev/verify gate.
**Status:** RED — 17 failing / 3 passing (the 3 green are WWN-side divergence guards + the positive argparse guard, intentionally already-true). Pre-existing 114-3/114-5 suites: 37/37 GREEN (no regression).

### Rule Coverage

| Rule (python.md) | Test(s) | Status |
|------|---------|--------|
| #1 silent exception swallowing | `test_ranged_malformed_bonus_fails_loud_with_row_context` (bad bonus must raise, not zero/swallow) | failing |
| #5 path handling — `Path.resolve()` before use (CWE-59) | `test_missing_relative_path_error_names_the_resolved_absolute_path` | failing |
| #6 test quality — no vacuous assertions | self-check: every test asserts a concrete value (no `assert True`/bare-truthy); negative cases paired with positives | pass |
| #11 input validation at CLI boundary | `test_unknown_srd_value_is_rejected_by_choices`, `test_unknown_license_value_is_rejected_by_choices` (+ positive guard) | failing |
| (verbatim N/A discipline) | `test_cwn_armor_na_soak_cell_leaves_mitigation_none`, `test_cwn_melee_na_trauma_emits_no_trauma_fields` | failing |

**Rules checked:** 4 of 13 lang-review rules are directly applicable to an offline extraction CLI (the rest — async, deserialization, resource leaks, logging-severity, dependency hygiene — don't apply to a pure text-in/models-out tool). All 4 applicable rules have test coverage.
**Self-check:** 0 vacuous tests (every assertion checks a concrete value; parametrized cases test distinct SRDs/parsers, not the same path).

**Watch-items for Dev (GREEN):**
- The dice validator `_DICE_RE = ^\d+d\d+$` rejects `1d8+2` — split the bonus in `_parse_ranged` BEFORE constructing `DamageSpec` (don't widen the regex).
- Keep the two `python -m` entry points distinct (regression tests pin them); share the core beneath.
- `armor`/`melee` parsers legitimately diverge WWN↔CWN (see Delivery Finding) — share `general`/`ranged` + helpers, not all four.
- No OTEL spans — offline authoring CLI, not a runtime subsystem.

**Handoff:** To Dev (Naomi) for GREEN implementation.
## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 66/66 green, ruff clean, pyright 0 errors, 0 smells |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (manual pass performed) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings (manual pass performed) |
| 4 | reviewer-test-analyzer | Yes | findings | 9 | confirmed 7 (all LOW), dismissed 2 (covered by pre-existing tests) |
| 5 | reviewer-comment-analyzer | Yes | findings | 6 | confirmed 2 (LOW), dismissed 4 (1 factually wrong, 3 pre-existing/carried-over) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (manual pass performed) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings (manual pass performed) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (manual pass performed) |
| 9 | reviewer-rule-checker | Yes | findings | 4 | confirmed 1 (LOW, __all__), dismissed 3 (1 hallucinated, 1 comment-exists, 1 pre-existing) |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 10 confirmed (all LOW), 9 dismissed (with rationale), 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

No Critical or High issues. All 8 ACs met, 66/66 tests green, ruff clean, pyright 0 errors. Every finding from every specialist is LOW severity (test polish + comment staleness); none are correctness bugs, and per the severity table LOW/MEDIUM do not block. I did not rubber-stamp: I confirmed the real LOW findings, dismissed the wrong/pre-existing ones with line-level evidence, and ran manual passes for the five disabled specialist domains.

**Data flow traced:** SRD chapter text (`--srd-path` file) → `Path(args.srd_path).resolve()` (CWE-59 hardening, cwn:183 / wwn:105) → `read_text(encoding="utf-8")` → `extract_catalog` (licensing gate: `license not in _VERBATIM_LICENSES` raises) → per-section `data_rows` → `split_trailing` (fails loud on too-few columns) → parser regex (`_RANGED_DAMAGE_RE`/`_SHOCK_RE`/`_TRAUMA_RE`, malformed → ValueError via `row_context` naming the row) → `CatalogItem`/`DamageSpec` (pydantic validation) → `json.dumps(model_dump())` to stdout. Every malformed-input branch fails loud and attributable; no silent corruption path exists. Safe.

**Pattern observed:** Shared-core-with-`functools.partial` flag binding (`parse_armor`/`parse_melee` take `has_soak`/`has_trauma`) — the simplest DRY that honors the WWN↔CWN armor/melee divergence without forking. ~520 lines of duplication removed; cyberware correctly stays CWN-local (`cwn_equip_extract.py:72`). Confirmed both CLIs import the shared parsers (wwn:34-37, cwn:44-47) — the DRY is structurally real, not behavioral-only.

**Error handling:** N/A cells (`_NA_CELLS`) map to absent fields (verbatim "not applicable", never an invented 0/number — ADR-143 binding discipline), `wn_equip_extract_core.py:50-55`. `main()`'s broad `except Exception` (cwn:193/wwn:115) surfaces to stderr + returns 1 (noqa: BLE001, pre-existing pattern) — not a swallow.

### Observations

- [VERIFIED] DRY is real, not copy-paste — both CLIs import `parse_armor/parse_melee/parse_ranged/parse_general` from `wn_equip_extract_core` (wwn:34-37, cwn:44-47) and reference them in `_SECTION_PARSERS`. Complies with CLAUDE.md "Don't Reinvent / Verify Wiring." Evidence: grep confirmed imports + `extract_catalog` driver at core:283.
- [VERIFIED] No Silent Fallbacks — every malformed cell raises `ValueError` wrapped with row context (`row_context`, core:114-120); missing section header raises (core:~295); missing file fails loud (cwn:185). N/A→absent-field is verbatim discipline, not a swallow. Evidence: `test_ranged_malformed_bonus_fails_loud_with_row_context` green.
- [VERIFIED] Verbatim-binding fidelity — `system_strain` stays float (Keith's 2026-06-14 ruling), soak/trauma/bonus reproduce SRD values, no re-stat. Evidence: core:50-55 comment + `test_catalog_item_system_strain` 6/6 green.
- [VERIFIED] CLI hardening live — `Path.resolve()` (cwn:183/wwn:105) + argparse `choices` on `--srd`/`--license` (stricter than the old accept-anything). Evidence: `test_missing_relative_path_error_names_the_resolved_absolute_path` + choices tests green.
- [TEST] (LOW) Tautological `assert os.path.isabs(resolved)` at test:435 — matches python.md rule #6 (vacuous assertion); confirmed, non-blocking (the real assertion at :436 is sound).
- [TEST] (LOW) AC6 `pytest.raises(SystemExit)` doesn't assert `.value.code == 2`; resolve()-message behavior untested for `wwn_main` (symmetry gap, wwn path green); AC1 DRY not asserted structurally (I verified by diff). Confirmed, non-blocking.
- [TEST] (dismissed) WWN armor value/weight gap (test-analyzer #5) — already covered by pre-existing `test_wwn_equip_extract.py:200-202` through the same `parse_armor(has_soak=False)`. Dismissed.
- [DOC] (LOW) `wwn_equip_extract.py:56` TOOL_VERSION comment copy-pastes a CWN test name; `test_wn_equip_core.py:1` "RED-phase" docstring now stale. Confirmed, non-blocking.
- [DOC] (dismissed) CWN TOOL_VERSION comment, §3.6.7, "Yield" docstring — CWN comment is accurate (`test_cwn_inventory_wiring.py:77` exists & references `cwn_equip_extract@114-5`); §3.6.7 + "Yield" are pre-existing, carried verbatim from the old code (not introduced here). Dismissed.
- [RULE] (LOW) No `__all__` on the new public module — not a codebase convention (~19% of modules; 0 sibling CLI modules); underscore-privacy followed. Confirmed, non-blocking.
- [RULE] (dismissed) `slugify` missing `-> str` — HALLUCINATION: it has `-> str` at core:73. `SectionParser = Callable[...]` "Any without comment" — comment exists at core:57-59 explaining the uniform call signature. `except Exception` broad — pre-existing, surfaces error, noqa-annotated. Dismissed with evidence.
- [EDGE] (subagent disabled) Manual pass: column-count off-by-one fails loud via `split_trailing`; N/A cells handled; `1d8+` fails the anchored regex; `1d8+00`→bonus 0 (correct, "+0" is no bonus). No silent-corruption boundary. VERIFIED.
- [SILENT] (subagent disabled) Manual pass: no swallowed errors; `_NA_CELLS` is verbatim-N/A not a fallback; `main()`'s broad catch surfaces to stderr. VERIFIED.
- [TYPE] (subagent disabled) Manual pass: `DamageSpec(**damage_kwargs)` typed `dict[str, object]` with `# type: ignore[arg-type]` (specific code, rule #3 compliant); pyright 0 errors. VERIFIED.
- [SEC] (subagent disabled) Manual pass: offline CLI, no untrusted network input; regexes anchored `^…$`, no catastrophic backtracking (no ReDoS); path resolved (CWE-59); explicit utf-8 encoding; no injection/eval/pickle. VERIFIED.
- [SIMPLE] (subagent disabled) Manual pass: partial-bound shared parser is the minimal DRY for the divergence; ~520 lines of duplication removed; no dead code (old privates deleted, not stubbed). VERIFIED.

### Rule Compliance (python.md, exhaustive)

- #1 silent exceptions: `row_context` catches ValueError specifically (compliant); `main()` broad catch surfaces+returns-1, noqa-annotated, pre-existing (LOW, not a swallow). PASS.
- #2 mutable defaults: none (all list literals inside function bodies; `argv=None` standard). PASS.
- #3 type annotations at boundaries: all public core functions fully annotated incl. `slugify -> str` (core:73); `Callable[...]` documented at core:57-59; `# type: ignore[arg-type]` has a specific code. PASS.
- #4 logging: offline CLI, errors → stderr/raise, no PII. N/A/PASS.
- #5 path handling: `Path.resolve()` + explicit `encoding="utf-8"`; no string path concat. PASS.
- #6 test quality: one tautological assertion (test:435) + one bare-truthy guard (test:334, count locked elsewhere) — confirmed LOW, non-blocking. Otherwise concrete-value assertions throughout. PASS-with-LOW.
- #7 resource leaks: `read_text`/`write_text`/`subprocess.run` are self-closing. PASS.
- #8 unsafe deserialization: `json.loads` only on the tool's own stdout in a test; no pickle/yaml.load/eval. PASS.
- #9 async: none. N/A.
- #10 import hygiene: explicit named imports, no star/cycles; missing `__all__` (LOW, non-convention). PASS-with-LOW.
- #11 input validation at boundaries: argparse `choices` + defense-in-depth license gate + malformed-cell raises. PASS.
- #12 dependency hygiene: no dependency files touched. N/A.
- #13 fix-introduced regressions: re-scan clean — hardening/`_NA_CELLS`/resolve are improvements; the only deltas are the LOW `__all__`/comment items. PASS.

### Devil's Advocate

Let me argue this is broken. A malicious or careless operator feeds a hand-mangled SRD text file. Attack 1: a CWN armor row with a two-word soak like `Plate 14 heavy 300 1` — `int("heavy")` raises, but does it fail attributably? Yes: `row_context` wraps it as "CWN SRD §3.0.1 Armor row '…': invalid literal for int()". No silent corruption. Attack 2: a ranged damage `1d8+999999999999` — `int()` accepts arbitrarily large ints, bonus becomes huge; `DamageSpec.bonus: int` has no upper bound, so a nonsense bonus passes. Is that a bug? It's *verbatim* reproduction — the tool's job is to reproduce what the SRD prints, and a real SRD never prints that; a huge value would be caught by a human reading the catalog, not this extractor. Not a security or correctness defect. Attack 3: a trauma cell `1d8/x2/T1` — `trauma_target=1` violates `DamageSpec.trauma_target ge=2`, raising at model construction, wrapped by row_context. Loud. Attack 4: column-count confusion — a CWN armor name containing a digit-like token. `split_trailing(row, 4)` is positional from the right, so a weird name shifts columns; but the resulting `int()` coercions raise on non-numeric, failing loud. The genuine residual risk is a name whose trailing tokens *happen* to all be numeric — that would mis-map silently. But that risk is pre-existing (the old parsers had identical positional splitting) and not introduced here. Attack 5: empty file / missing section header → `extract_catalog` raises "missing expected section header", never emits a partial catalog. Attack 6: a confused operator passes `--srd swn` to the WWN tool — accepted (it's in `WN_SRD_CHOICES`), stamping `srd=swn`; semantically odd but the old code accepted *any* string, so this is strictly tighter. Conclusion: every adversarial input I can construct either fails loud-and-attributable or is verbatim-faithful by design. No path produces silent data corruption that this change introduced.

**Handoff:** To SM for finish-story.