---
story_id: "163-3"
jira_key: ""
epic: "163"
workflow: "spdd"
---
# Story 163-3: Server: pack validator — raster anchor coverage + provenance (plan tasks 8,18)

## Story Details
- **ID:** 163-3
- **Jira Key:** (none — sprint-tracked)
- **Workflow:** spdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** spdd
**Phase:** finish
**Phase Started:** 2026-07-09T10:03:16Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-09T09:09:54+00:00 | 2026-07-09T09:12:09Z | 2m 15s |
| red | 2026-07-09T09:12:09Z | 2026-07-09T09:22:53Z | 10m 44s |
| green | 2026-07-09T09:22:53Z | 2026-07-09T09:36:11Z | 13m 18s |
| review | 2026-07-09T09:36:11Z | 2026-07-09T09:47:20Z | 11m 9s |
| green | 2026-07-09T09:47:20Z | 2026-07-09T09:54:21Z | 7m 1s |
| review | 2026-07-09T09:54:21Z | 2026-07-09T10:03:16Z | 8m 55s |
| finish | 2026-07-09T10:03:16Z | - | - |

## Sm Assessment

**Setup complete — routing to TEA (Argus Panoptes) for the RED phase.**

- **Scope:** Two pure-validator additions to `sidequest-server/sidequest/cli/validate/pack.py` — `_validate_map_treatment` (plan Task 8: raster `map.yaml` must declare a non-empty `image`, a four-key `provenance` block [source/date/archive/pd_basis], and a `node_anchor` for every `cartography.yaml` region; absent `map.yaml` = dag fallback = OK) and `_validate_weather_zones` (plan Task 18: every region `weather_zone` must resolve to a `weather.yaml` `climate_zones` key). Both are appended to `_validate_world`'s `content_errors`. Tests go in `tests/cli/validate/test_pack_validator.py`.
- **Authoritative spec is the plan doc**, not this story YAML (which has no description/ACs): `docs/superpowers/plans/2026-07-08-mapping-track-a-main-map-treatments.md`, Task 8 (L601–725) and Task 18 (L1403–1495). Both tasks ship the exact failing-test bodies and full implementation — TEA should lift the test code, reusing the existing `_minimal_pack`/`_minimal_world` fixtures and `schema_path_real`.
- **Doctrine (load-bearing):** these are CONTENT INVARIANTS deliberately placed in the CI-gated pack VALIDATOR, never in unit tests. The validator *tests* use synthetic fixtures to exercise the validator CODE — that is correct and is not a "content in unit tests" violation. Do not assert against real genre-pack content.
- **Base branch:** 163-3 is branched fresh from `origin/develop` (`feat/163-3-pack-validator-map-treatment`). 163-1 (the map.yaml treatment models/loader/protocol) already squash-merged to develop as #1125 (`3d4af67a`); `pack.py` exists on develop but has neither validator yet, so this work is genuinely net-new. Note: `_validate_map_treatment` reads raw YAML via `_read_yaml` — it does **not** import 163-1's `MapTreatmentConfig` models, so there is no code dependency on 163-1 beyond the shared file.
- **Two AC-shaped behaviors TEA must pin in RED:** (1) absent `map.yaml` yields zero errors (dag fallback), and (2) a `weather_zone` declared with no `weather.yaml` climate_zones is itself an error (binding-without-a-climate). Both are easy to miss.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Two net-new content-invariant validators; behavior pinned before implementation.

**Test Files:**
- `sidequest-server/tests/cli/validate/test_pack_validator.py` — two new classes: `TestMapTreatmentValidation` (7 tests, Task 8) and `TestWeatherZoneValidation` (4 tests, Task 18). All synthetic-fixture (server tests never read live packs), black-box through `validate_pack_structure`. The black-box entry point IS the wiring test — a validator written but not appended to `_validate_world`'s `content_errors` leaves the RED tests red.

**Tests Written:** 11 tests — 7 error-driving (RED) + 4 green-guard controls.
**Status:** RED confirmed — **7 failed / 21 passed** (17 pre-existing + 4 controls). All 7 fail with `AssertionError: []` (validators absent — the right reason, not a typo/crash). Zero regressions; `test_all_live_packs_pass_content_validation` stays green (verified: no live world ships a `map.yaml` and no live `cartography.yaml` declares a `weather_zone` today — the content lands later in 163-4/163-6).

### Rule Coverage

| Rule (python lang-review) | Test(s) / Handling | Status |
|---|---|---|
| #6 Test quality (no vacuous asserts) | Every test asserts a specific token or scoped absence; grep for `assert True`/`assert result$`/`let _ =` → none | pass |
| #11 Input validation at file parsers | The whole suite validates `map.yaml`/`weather.yaml` content at the parse boundary | covered (7 RED tests) |
| #8 Unsafe deserialization / #5 Path handling | Validators must reuse `_read_yaml` (yaml.safe_load + `encoding="utf-8"`) + pathlib joins | Dev-owned (GREEN) |
| #1–4, #7, #9–10, #12–13 | Implementation-side (exceptions/logging/resources/imports/deps) — not exercisable via black-box RED tests | Dev-owned (GREEN) |

**Rules checked:** 2 of 13 lang-review rules are TEA-testable for this pure-validator story (#6, #11); the remainder are Dev GREEN-phase self-review.
**Self-check:** 0 vacuous tests found.

**Handoff:** To Dev (Hephaestus the Smith) for GREEN implementation.

<skills-invoked>
<skill name="test-driven-development" phase="red" at="2026-07-09T09:20:02Z"/>
<skill name="test-driven-development" phase="green" at="2026-07-09T09:27:05Z"/>
<skill name="verification-before-completion" phase="green" at="2026-07-09T09:27:05Z"/>
<skill name="requesting-code-review" phase="green" at="2026-07-09T09:30:00Z"/>
<skill name="receiving-code-review" phase="green" at="2026-07-09T09:32:00Z"/>
<skill name="test-driven-development" phase="green" at="2026-07-09T09:52:18Z"/>
<skill name="verification-before-completion" phase="green" at="2026-07-09T09:52:18Z"/>
<skill name="receiving-code-review" phase="green" at="2026-07-09T09:52:18Z"/>
</skills-invoked>

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-server/sidequest/cli/validate/pack.py` — added `_validate_map_treatment` (Task 8) and `_validate_weather_zones` (Task 18), both wired into `_validate_world`'s `content_errors.extend(...)` (so they inherit draft-world demotion). Both guard the file read with `.is_file()` before `_read_yaml` — fixing the `FileNotFoundError` crash Argus pinned in the plan's verbatim Task-18 code.
- `sidequest-server/tests/cli/validate/test_pack_validator.py` — TEA's 11 tests plus 2 Dev-added regression tests (from the pre-handoff review).

**Tests:** 30/30 passing in the validator file (GREEN); pyright 0 errors; ruff clean. The `tests/cli/` tree has one unrelated pre-existing failure (`test_162_5_encountergen_v4.py::test_v4_spawned_creature_stats_match_bestiary` — bestiary/creature-stats fixture drift, no code path from the pack validator; documented pre-existing WWN content breakage).

**Branch:** `feat/163-3-pack-validator-map-treatment` (pushed). Commits: `a2c26845` (RED tests) → `43bf706d` (GREEN impl) → `29ee9384` (review hardening).

**Pre-handoff review (requesting-code-review):** dispatched a reviewer on the impl diff. It found one Important + two Minor issues, all verified real and fixed:
- Important: `_validate_map_treatment` crashed on a non-dict `cartography.yaml` (`.get` on a list) while its sibling guarded the same case → added `isinstance(cart_data, dict)` guard (regression test `test_raster_map_non_dict_cartography_does_not_crash`).
- Minor: a bare-list `node_anchors` was silently treated as coverage via list membership → normalize to `{}` unless a mapping (regression test `test_raster_map_list_node_anchors_not_silently_covered`).
- Minor: dead `(r or {})` defensiveness in the weather comprehension → simplified to `r.get(...)`.
- (Declined) empty `map.yaml` → "must be a mapping" error is intended loud behavior per No Silent Fallbacks (absent map.yaml = dag fallback = OK; empty ≠ absent).

**Handoff:** To Reviewer (Hermes Psychopompos) for the review phase.

### Rework Response (Reviewer REJECT — 2026-07-09)

Addressed all four HIGH crash findings + the MEDIUM whitespace finding via bug-fix TDD (6 new RED tests → guards; each crash reproduced red, then fixed green):
- **F1** non-hashable `treatment` (`treatment: [raster]`) → `isinstance(kind, str)` guard before the set-membership check (`pack.py:1055`); now reported as unknown treatment.
- **F2** non-hashable region `weather_zone` (`weather_zone: [glen_floor]`) → `isinstance(wz, str)` guard in the membership loop; now reported as an invalid zone.
- **F3/F4/F5** malformed `climate_zones` (scalar `42`, list-of-mappings, bare-string char-set) → `isinstance(climate_zones, dict)` guard before `set()`, else a clean "climate_zones must be a mapping" error (`pack.py:1137`).
- **MEDIUM** whitespace/type → `image` must be a non-empty **stripped** string; provenance values reject whitespace-only (closes the PD-provenance-defeated-by-blank gap Task 8's licensing invariant depends on).
- **DEFERRED** (Reviewer non-blocking sub-item): validating anchor VALUES are coordinate-shaped (`node_anchors: {r1: null}` still counts as covered). Task 8 requires each region to "appear in node_anchors" (key presence), not coordinate validation — logged as a Design Deviation, out of scope for this story.

Independently re-verified the four former crashes now return clean error strings (no `TypeError`). **36/36** validator tests green; ruff + pyright clean. Commit `d9b09299` pushed.

**Handoff:** Back to Reviewer (Hermes Psychopompos) for re-review.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

### TEA (test design)
- **Gap** (blocking): The plan's `_validate_weather_zones` (Task 18, plan L1473) calls `_read_yaml(world_dir / "weather.yaml", label)` with NO preceding `.is_file()` guard. `_read_yaml` does not guard existence — `Path.read_text()` raises `FileNotFoundError`, which `_read_yaml` does NOT catch (it only catches `YAMLError`/`UnicodeDecodeError`). So a region that declares a `weather_zone` while `weather.yaml` is absent **crashes the whole validator** instead of returning the intended "no weather.yaml climate_zones" error — the `if not zones:` branch is unreachable for the absent-file case as the plan wrote it. Affects `sidequest-server/sidequest/cli/validate/pack.py`: `_validate_weather_zones` must guard with `if not (world_dir / "weather.yaml").is_file(): return [<climate-binding-with-no-climate error>]` before the `_read_yaml` call, mirroring every sibling validator's `if not path.is_file(): return []` pattern. Pinned by `test_weather_zone_declared_without_weather_yaml_is_error`. *Found by TEA during test design.*
- **Improvement** (non-blocking): The plan's `_validate_map_treatment` (Task 8) also reads `cartography.yaml` via `_read_yaml` without an `.is_file()` guard, but `cartography.yaml` is a REQUIRED world file so it is always present — safe in practice. Dev may add the guard for consistency, but no test requires it. Affects `sidequest-server/sidequest/cli/validate/pack.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Resolved (was TEA blocking):** The plan's absent-`weather.yaml` crash is fixed — `_validate_weather_zones` now guards `if not weather_path.is_file(): return [no_climate_error]` before `_read_yaml`. TEA's non-blocking cartography-guard improvement is also applied: both `_validate_map_treatment` and `_validate_weather_zones` now `isinstance`-guard `cart_data`. No open action for the Reviewer here.
- **Improvement** (non-blocking): `tests/cli/test_162_5_encountergen_v4.py::test_v4_spawned_creature_stats_match_bestiary` fails on this branch, but it is PRE-EXISTING and unrelated to 163-3 (spawned creature stats vs `bestiary.yaml` drift — no code path from the pack validator to encountergen). Reviewer should not attribute it to this story; it matches the documented WWN content-fixture breakage. Affects `sidequest-server/tests/cli/test_162_5_encountergen_v4.py` (separate content-fixture reconciliation). *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): `_validate_map_treatment` crashes on a non-hashable `treatment` (e.g. `treatment: [raster]`) — `kind not in {…}` raises `TypeError: unhashable type: 'list'` (empirically reproduced). No `try/except` wraps `_validate_world` in the CLI loop, so this ABORTS the entire `pf validate pack` run for ALL packs, not just the bad world. Affects `sidequest-server/sidequest/cli/validate/pack.py:1055` (guard `if not isinstance(kind, str) or kind not in {…}`). *Found by Reviewer during code review.* `[EDGE]`
- **Gap** (blocking): `_validate_weather_zones` crashes on a non-hashable region `weather_zone` (e.g. `weather_zone: [glen_floor]`) — it survives the truthy `declared` filter then `wz not in zones` raises `TypeError: unhashable type` (reproduced). Aborts the whole run. Affects `sidequest-server/sidequest/cli/validate/pack.py:1116,1146` (filter non-str out of `declared` and/or `isinstance(wz, str)` before membership). *Found by Reviewer during code review.* `[EDGE]`
- **Gap** (blocking): `_validate_weather_zones` crashes on a malformed `climate_zones` that isn't a mapping/list-of-hashables (`climate_zones: 42` → `set(42)` `TypeError: not iterable`; `climate_zones: [{...}]` → `TypeError: unhashable dict`; reproduced). Aborts the whole run. A bare-string `climate_zones: glen_floor` doesn't crash but silently decomposes to a character set (silently-wrong membership). Affects `sidequest-server/sidequest/cli/validate/pack.py:1137` (require `isinstance(climate_zones, dict)` before `set(...)`, else emit a malformed-climate_zones error). *Found by Reviewer during code review.* `[EDGE]`
- **Improvement** (non-blocking): The presence checks are truthiness-only, not type/whitespace-checked — `image: 123`, `provenance: {date: 1900}` (int), `image: "   "` (whitespace), and `node_anchors: {r1: null}` (null coord value) are all silently accepted as satisfying "non-empty image / provenance key / a node_anchor". The spec asks for "non-empty", which truthiness satisfies literally, so this is a strictness enhancement, not a blocker; worth folding into the rework since Dev is already in these functions. Affects `sidequest-server/sidequest/cli/validate/pack.py:1061-1072,1086-1094`. *Found by Reviewer during code review.* `[EDGE]`

### Dev (rework)
- No new upstream findings during rework. All four Reviewer HIGH crash findings and the MEDIUM whitespace finding are resolved (guards + 6 regression tests, commit `d9b09299`); the anchor-value coordinate-shape sub-item is deferred as spec-compliant (logged in Design Deviations). *Found by Dev during rework.*

### Reviewer (code review — round 2)
- **Improvement** (non-blocking): An empty-string region `weather_zone: ''` is filtered out of `declared` by truthiness, so it is treated as "not declared" and reported as no error. Defensible (an unfilled optional field ≠ an error) and pre-existing, but a future pass could filter on key-presence to flag a blank-but-present weather_zone. Affects `sidequest-server/sidequest/cli/validate/pack.py:1116`. *Found by Reviewer during code review.* `[EDGE]`
- **Improvement** (non-blocking): Provenance values that are non-string truthy types (list/dict) still satisfy the gate — the whitespace guard only special-cases strings (kept lenient deliberately so int dates like `date: 1900` pass). A future pass could require string provenance values while allowing an int date. Affects `sidequest-server/sidequest/cli/validate/pack.py:1074`. *Found by Reviewer during code review.* `[EDGE]`
- **Improvement** (non-blocking): A bare-list `node_anchors` produces per-region "no node_anchor" errors rather than a dedicated "node_anchors must be a mapping" diagnostic — still errors (no false-negative), just a less specific message. Affects `sidequest-server/sidequest/cli/validate/pack.py:1090`. *Found by Reviewer during code review.* `[EDGE]`

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Expanded coverage beyond the plan's 5 enumerated tests to 11**
  - Spec source: plan `2026-07-08-mapping-track-a-main-map-treatments.md`, Task 8 (3 tests) + Task 18 (2 tests)
  - Spec text: Task 8 gives `test_raster_map_missing_anchor` / `missing_provenance` / `absent_map_yaml`; Task 18 gives `test_region_weather_zone_unknown` / `valid_passes`
  - Implementation: added 6 tests hitting distinct implementation branches the plan's 5 miss — partial-provenance (per-key loop), missing-image, unknown-treatment-kind, non-raster-skips-raster-rules (control), weather_zone-without-weather.yaml (absent-file path, SM-flagged), no-weather_zone-anywhere (control). All 5 plan tests are included verbatim.
  - Rationale: each added test exercises a distinct branch of the planned implementation; the weather-without-weather.yaml test surfaced a real crash-bug in the plan's verbatim code (see blocking Delivery Finding)
  - Severity: minor
  - Forward impact: none (additive test coverage)

### Dev (implementation)
- **Added 2 Dev-authored regression tests during GREEN (review-driven)**
  - Spec source: pre-handoff code review (requesting-code-review skill), not a plan task
  - Spec text: plan Task 8 enumerates 3 tests; no test covered a malformed non-dict `cartography.yaml` or a bare-list `node_anchors`
  - Implementation: added `test_raster_map_non_dict_cartography_does_not_crash` and `test_raster_map_list_node_anchors_not_silently_covered` to `TestMapTreatmentValidation`, plus the `isinstance` guards they drive
  - Rationale: the review surfaced a real crash (AttributeError on a list cartography) and a silent-coverage bug (list `node_anchors`); bug-fix TDD requires a failing test before the fix. Test-authoring is normally TEA's lane, but these pin Dev-introduced hardening for review-found defects.
  - Severity: minor
  - Forward impact: none (additive coverage + defensive guards; all plan/TEA tests unchanged and green)

### Reviewer (audit)
- **TEA: "Expanded coverage beyond the plan's 5 to 11"** → ✓ ACCEPTED by Reviewer: more branch coverage than the plan enumerated is strictly good; all five plan tests are included verbatim and the additions surfaced a real crash-bug. Sound.
- **Dev: "Added 2 Dev-authored regression tests during GREEN (review-driven)"** → ✓ ACCEPTED by Reviewer: bug-fix TDD for two genuine defects the pre-handoff review found; test-authoring in the Dev lane is justified here because it pins Dev-introduced hardening. Sound.
- **UNDOCUMENTED (Reviewer):** Story/spec intent (and the whole point of a CI-gated content validator) is that malformed content is reported as a clean error, never a crash. The code diverges: `_validate_map_treatment` and `_validate_weather_zones` raise uncaught `TypeError` on four malformed-content shapes (non-hashable `treatment`, non-hashable `weather_zone`, non-iterable/non-hashable `climate_zones`), aborting the entire multi-pack run. TEA + Dev fixed two crash paths of this class (FileNotFoundError, non-dict cartography) but did not enumerate the remaining four. Severity: **High** — this is the blocking finding driving the REJECT.

### Dev (rework)
- **Deferred the anchor-VALUE coordinate-shape check (Reviewer non-blocking finding)**
  - Spec source: plan Task 8 (L601–725) + Reviewer MEDIUM finding
  - Spec text: "require every cartography.yaml region id to appear in node_anchors" (key presence)
  - Implementation: anchor coverage remains a key-presence check; `node_anchors: {r1: null}` still counts as covered. The four crash guards + whitespace/type checks WERE applied; only the coordinate-shape validation of anchor VALUES is deferred.
  - Rationale: Task 8's stated contract is "appear in node_anchors" (the key exists), not "carry valid coordinates". Validating coordinate shape is a spec extension beyond this story; the runtime `MapTreatmentConfig` model (163-1) is the type-checking layer for anchor values.
  - Severity: minor
  - Forward impact: none for this story; a future hardening story could add coordinate-shape validation if authoring mistakes surface.

### Reviewer (audit — round 2)
- **Dev: "Deferred the anchor-VALUE coordinate-shape check"** → ✓ ACCEPTED by Reviewer: Task 8's stated contract is "region id appears in node_anchors" (key presence), not coordinate validation — deferring value-shape validation is spec-compliant and out of scope. The round-2 edge-hunter agreed it is Low/optional. Sound.
- **Round-1 blocking crashes** → RESOLVED: all four (non-hashable treatment/weather_zone, malformed climate_zones scalar+list) are fixed and independently re-confirmed returning clean error strings. No new spec deviations introduced by the guards.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 | N/A — GREEN: 30/30 tests, ruff clean, pyright 0 errors, no smells, both validators wired at L1300-1301, all 22 live packs validate |
| 2 | reviewer-edge-hunter | Yes | findings | 10 | confirmed 4 blocking crashes (F1–F4, reproduced) + 4 non-blocking strictness (image/provenance/whitespace/anchor-value) + 2 low/dup |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | clean | 0 | N/A — yaml.safe_load confirmed, no content→path (no CWE-22), encoding=utf-8, no host-path/secret leak, no ReDoS |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (3 enabled subagents returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 4 confirmed blocking (all [EDGE], all reproduced), 4 confirmed non-blocking (Medium strictness), 2 dismissed as duplicates/low; security + preflight clean

### Round 2 (re-review after rework)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 | N/A — 36/36 validator tests green, ruff clean, pyright 0 errors; 151 broader-suite failures all pre-existing/unrelated (WWN content-fixture drift), not attributable to this story |
| 2 | reviewer-edge-hunter | Yes | findings | 5 | Objective 1: **all 4 round-1 crash paths CONFIRMED fixed** (each returns a clean error string, reproduced empirically; int-date regression check passes). Objective 2: 5 remaining findings, all NON-BLOCKING — 3 Medium (empty-string weather_zone bypass, non-string provenance value, node_anchors-list diagnostic), 2 Low (non-string climate_zones keys, anchor-value shape). None are crashes/regressions. |
| 7 | reviewer-security | Carried forward | clean | 0 | N/A — round-1 clean; rework adds only isinstance/strip guards, no new parse/path/exec surface, so the security verdict stands |

**All received:** Yes (2 re-run + security carried forward; the other 6 remain disabled)
**Total findings (round 2):** 0 blocking (all 4 round-1 crashes fixed + verified), 5 non-blocking Medium/Low (captured as delivery findings for a future hardening pass)

### Rule Compliance

Rubric = `.pennyfarthing/gates/lang-review/python.md`. Enumerated against both new functions:

| Rule | Instances checked | Verdict |
|---|---|---|
| #1 Silent exception swallowing | `_validate_weather_zones:1111` returns `[]` on cartography parse error ("reported elsewhere") | ⚠ minor — cartography.yaml is NOT model-validated by this validator, so the "elsewhere" safety net is unproven; out-of-scope for this story but noted (Devil's Advocate) |
| #3 Type annotations | both fns `(world_dir: Path, label: str) -> list[str]` | ✓ compliant |
| #5 Path handling | `world_dir / "map.yaml"` etc. pathlib; `_read_yaml` uses `encoding="utf-8"` | ✓ compliant |
| #6 Test quality | 13 new tests, all assert specific tokens/scoped absence; 0 vacuous | ✓ compliant |
| #8 Unsafe deserialization | both parse via `_read_yaml` → `yaml.safe_load` | ✓ compliant (security confirmed) |
| #11 Input validation at file parsers | **parsed values are used without a type guard** before `in`/`set()`/membership | ✗ **VIOLATION** — the 4 blocking crashes (F1–F4): `treatment`, `weather_zone`, and `climate_zones` values are operated on without shape-guarding, so malformed content crashes the parser instead of being reported. This is the exact rule this story is meant to satisfy. |
| #2/#4/#7/#9/#10/#12/#13 | no mutable defaults, no logging path, no resources/async/imports/deps introduced | ✓ N/A / compliant |

### Devil's Advocate

Assume this code is broken and hostile-authored. The project's load-bearing goal (CLAUDE.md) is that *non-Keith homebrew authors* — Jade, a future table member — can add world content **without touching engine code**, and the CI-gated pack validator is the safety net that catches their mistakes with a friendly, actionable error. Now watch it fail its one job. An author writes the most natural YAML mistakes imaginable: `treatment:` as a bulleted list instead of a scalar; `weather_zone: [temperate, alpine]` because they reasonably assume a region can span two climates; `climate_zones: temperate` as a scalar because they only have one. Every one of these produces not a helpful "unknown treatment" / "weather_zone is not a climate zone" message but an **uncaught `TypeError` that aborts validation of every other pack** — the author gets a Python stack trace, and CI dies on the first bad file. A validator that crashes on malformed content is worse than no validator: it actively punishes the exact audience it exists to serve. This is not a hypothetical — I reproduced all four crashes against the real `validate_pack_structure` entry point.

Worse, the story's *raison d'être* for Task 8 is **PD-provenance enforcement** for rights-free raster map scans (source/date/archive/pd_basis — a licensing invariant). The provenance gate is truthiness-only: `pd_basis: "   "` (whitespace) or `pd_basis: 0`-that-is-actually-truthy passes. An author can *accidentally* satisfy the legal-provenance gate with a blank-looking value, defeating the very invariant the task encodes. The `image` and anchor-value checks are similarly presence-only — `image: {url: x}` (wrong shape) and `node_anchors: {r1: null}` (no coordinates) both pass, so a "validated" raster map can carry an unrenderable image and coordinate-less anchors. And the `_validate_weather_zones:1111` comment asserts cartography errors are "reported elsewhere" — but cartography.yaml is not model-validated anywhere in the pack validator, so a malformed cartography silently yields `[]` from this path. Four crashes plus a provenance gate that whitespace defeats is not a shippable content-invariant validator.

## Reviewer Assessment (Round 1 — REJECTED, superseded)

**Verdict:** REJECTED

The two validators are well-structured, correctly wired (L1300-1301, inheriting draft-demotion), safe on YAML parsing ([SEC] clean), and green on the happy paths ([preflight] 30/30). But the edge-hunter surfaced — and I independently reproduced against the real `validate_pack_structure` — four uncaught-crash paths on malformed content. That is the precise defect class this story exists to eliminate, and the precedent set by TEA's `FileNotFoundError` finding and the pre-handoff review's non-dict-cartography `AttributeError` (both fixed) makes leaving four more of the same class a "ship 3 of 5 connections" violation of CLAUDE.md's No-half-wired-features rule.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] `[EDGE]` | Non-hashable `treatment` (`treatment: [raster]`) → `TypeError: unhashable type` on `kind not in {…}`; aborts the whole `pf validate pack` run | `pack.py:1055` | `if not isinstance(kind, str) or kind not in {…}:` → treat non-str as unknown treatment |
| [HIGH] `[EDGE]` | Non-hashable region `weather_zone` (`weather_zone: [glen_floor]`) → `TypeError` on `wz not in zones`; aborts whole run | `pack.py:1116,1146` | filter non-str out of `declared` (or `isinstance(wz, str)` guard before membership) → report as invalid zone |
| [HIGH] `[EDGE]` | Malformed `climate_zones` — scalar (`42`) → `set()` not-iterable; list-of-dicts → unhashable; aborts whole run. Bare string → silent char-set (wrong result) | `pack.py:1137` | require `isinstance(climate_zones, dict)` before `set(...)`, else emit a malformed-climate_zones error |
| [MEDIUM] `[EDGE]` | Presence checks are truthiness-only: `image`/provenance keys accept non-string & whitespace-only values; `node_anchors: {r1: null}` counts as covered. Undermines the PD-provenance licensing invariant (Task 8's purpose) | `pack.py:1061-1072,1086-1094` | require non-empty **stripped strings** for image + provenance keys; consider validating anchor values are coordinate-shaped |

**Subagent dispatch tags:** `[EDGE]` 4 confirmed blocking + 1 medium (edge-hunter); `[SEC]` clean (security — yaml.safe_load, no CWE-22, no leak); `[SILENT]` not run (disabled); `[TEST]` not run (disabled — but preflight confirms 30/30 green and TEA's own coverage is strong); `[DOC]` not run (disabled); `[TYPE]` not run (disabled); `[SIMPLE]` not run (disabled); `[RULE]` not run (disabled — I performed the rule-by-rule enumeration myself in `### Rule Compliance`; #11 violated by the crash paths).

**Data flow traced:** author-written `map.yaml`/`cartography.yaml`/`weather.yaml` → `_read_yaml` (`yaml.safe_load`) → the two validators → error strings → `content_errors` → `validate_pack_structure` → `pf validate pack` CLI. Safe on parsing and on info-leak (error strings carry only content-derived names + `path.name`, never host paths/secrets), but **unsafe on malformed-value handling** — the crash paths propagate uncaught through the per-world loop and abort the multi-pack run.

**The three HIGH crashes are blocking and testable** (each malformed input should yield a clean error string, not a `TypeError`). The MEDIUM strictness/whitespace item is recommended in the same rework because Dev is already in these functions and it touches the story's licensing purpose. Routing back to TEA for RED tests on the four malformed-content shapes, then Dev for the guards.

**Handoff:** Back to TEA (Argus Panoptes) for red-phase rework — findings are testable logic/edge-case bugs.
## Reviewer Assessment

**Verdict:** APPROVED

Round 1 rejected on four HIGH uncaught-crash paths (malformed `treatment`/`weather_zone`/`climate_zones` aborting the whole `pf validate pack` run). The rework fixed all four — independently re-confirmed by the round-2 edge-hunter that each degenerate input now returns a clean, actionable error string rather than raising, with no regression to legitimate shapes (int dates, unicode, valid mappings) and no new crash introduced by the guards. The MEDIUM whitespace gap on the PD-provenance licensing invariant is also closed (`image` and provenance values reject whitespace-only). Preflight is green (36/36 validator tests, ruff clean, pyright 0 errors).

The round-2 edge-hunter surfaced five residual findings; all are **non-blocking** (3 Medium strictness/diagnostic, 2 Low) on degenerate inputs, none are crashes or regressions, and several are debatable judgment calls or pre-existing behavior. They are captured as delivery findings for a future hardening pass and do not gate this story, whose Task-8/18 contract (report malformed content gracefully; require an anchor per region; resolve weather_zone to a real climate zone) is met.

**Subagent dispatch tags:** `[EDGE]` — round 1: 4 blocking crashes (all fixed) + 4 medium; round 2: crashes confirmed fixed, 5 residual non-blocking. `[SEC]` clean (yaml.safe_load, no CWE-22, no host-path/secret leak; unchanged by the guard-only rework). `[SILENT]` not run (disabled — but the validators are loud-by-design, returning error strings, and the "reported elsewhere" cartography comment is noted). `[TEST]` not run (disabled — preflight confirms 36/36; TEA + Dev coverage is strong, incl. 8 crash/whitespace regression tests). `[DOC]` not run (disabled). `[TYPE]` not run (disabled — I enumerated `### Rule Compliance` myself; #11 now satisfied by the shape guards). `[SIMPLE]` not run (disabled). `[RULE]` not run (disabled — rule-by-rule done in `### Rule Compliance`; the round-1 #11 violation is resolved).

**Data flow traced:** author-written `map.yaml`/`cartography.yaml`/`weather.yaml` → `_read_yaml` (`yaml.safe_load`, encoding=utf-8) → the two validators (now shape-guarding every parsed value before `in`/`set()`/membership) → error strings (content-derived names + `path.name` only, no host-path/secret leak) → `content_errors` (draft-demoted for draft worlds) → `validate_pack_structure` → `pf validate pack`. No crash path, no info leak, no path traversal.

**Pattern observed:** the validators now mirror the sibling-validator defensive shape (`.is_file()` guard + `isinstance` before structural ops) consistently — `pack.py:1046-1163`.

**Error handling:** every malformed-content shape returns a clean `f"{label}: ..."` error rather than raising; verified for all four former crash inputs plus YAML-parse errors, non-dict cartography, and absent files.

**Handoff:** To SM (Themis the Just) for finish-story.