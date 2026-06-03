---
story_id: "65-12"
jira_key: ""
epic: "65"
workflow: "tdd"
---
# Story 65-12: Lore world timeline — world-historical spine from legends, honest conditional sort

## Story Details
- **ID:** 65-12
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish

## Dev Recovery Result (2026-06-03) — rebase + conflict resolution + MERGE complete

The White Rabbit completed the SM-routed rebase-and-merge:
- `gh pr ready 615` (un-drafted), then rebased `feat/65-12-lore-world-timeline` onto `origin/develop`.
- **Resolved the conflict in `sidequest/telemetry/spans/reference.py`** — three "keep both" regions (65-13 added Cast portrait-gate spans `reference_portrait_{resolved,not_found}_span`; 65-12 added `reference_timeline_rendered_span`). Kept BOTH: both constant groups, both `FLAT_ONLY_SPANS` registrations, both constructor functions. `reference_renderer.py` and `test_reference_chrome_wiring.py` auto-merged cleanly (Cast/Map/Timeline appends all present).
- **Re-verified post-rebase (testing-runner):** `test_reference_timeline.py` **19/19**; full reference suite **462 passed, 0 failed, 2 skipped** (now includes 65-13's tests); ruff + pyright clean.
- Force-pushed (`--force-with-lease`), **merged PR #615 (squash) → `develop`** (mergedAt 2026-06-03T21:34:52Z; develop top `19fedded feat(65-12): lore world timeline (#615)`); remote branch deleted; local synced to develop.

**The code is now on `develop`.** SM (Mad Hatter): finalize — set status back to `done` and commit/push the held sprint artifacts (epic-65.yaml, `sprint/archive/65-12-session.md`, `sprint/context/context-story-65-12.md`, sidecars) to `main`. The desync is resolved (develop has the code); the sprint commit is now safe to land.

## SM Recovery Note (2026-06-03) — finish over-reported; merge blocked by concurrent landings

`pf sprint story finish 65-12` ran all steps and marked the story done, but **`merge_pr` did not actually merge**: **PR #615** (`feat/65-12-lore-world-timeline` → `develop`) is **OPEN, draft, and CONFLICTING** (mergeStateStatus DIRTY). The code is NOT on `develop`. During this session, **65-13** (PR #614) and **64-16** landed on `develop` and touched the same files 65-12 changed. Operator decision (2026-06-03): hand to Dev to rebase + resolve + merge.

**White Rabbit (Dev) — rebase-and-merge task:**
1. `gh pr ready 615` (un-draft) in `sidequest-server`.
2. `git fetch origin develop && git rebase origin/develop` on `feat/65-12-lore-world-timeline`. Expect conflicts in:
   - `sidequest/server/reference_renderer.py` — both 65-12 and 65-13 append to `assemble_lore_page`; keep BOTH the Cast/Map/Timeline appends (re-apply the Timeline section + `{id:timeline}` TOC append on top of 65-13's changes).
   - `sidequest/telemetry/spans/reference.py` — both add spans; keep BOTH (the `reference_timeline_rendered_span` + constant + `FLAT_ONLY_SPANS` entry alongside 65-13's span additions).
   - `tests/server/test_reference_chrome_wiring.py` — both edit the seed; merge both edits (65-13's chrome guards + 65-12's timeline-class seed enrichment).
   - Possibly `reference_presenters.py` / `presenters.css` — reconcile additively.
3. Re-run via testing-runner: `tests/server/test_reference_timeline.py` (19/19) + `tests/server/ -k reference` (must stay green) + ruff/pyright on the changed files.
4. Push the rebased branch; merge PR #615 to `develop` (squash per repo convention).
5. Hand back to SM (Mad Hatter) to finalize: SM commits/pushes the held sprint artifacts (epic-65.yaml `done`, `sprint/archive/65-12-session.md`, `sprint/context/context-story-65-12.md`, sidecar learnings) to `main` AFTER the merge lands. **SM is holding that commit** to avoid a sprint-says-done / develop-lacks-code desync.

The full assessments below (RED→GREEN→spec-check→verify→review APPROVED→reconcile) are unchanged and authoritative; only the merge remains.
**Phase Started:** 2026-06-03T21:04:12Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-03T15:30:00Z | 2026-06-03T20:06:48Z | 4h 36m |
| red | 2026-06-03T20:06:48Z | 2026-06-03T20:19:46Z | 12m 58s |
| green | 2026-06-03T20:19:46Z | 2026-06-03T20:39:54Z | 20m 8s |
| spec-check | 2026-06-03T20:39:54Z | 2026-06-03T20:43:59Z | 4m 5s |
| green | 2026-06-03T20:43:59Z | 2026-06-03T20:47:25Z | 3m 26s |
| spec-check | 2026-06-03T20:47:25Z | 2026-06-03T20:48:27Z | 1m 2s |
| verify | 2026-06-03T20:48:27Z | 2026-06-03T20:52:21Z | 3m 54s |
| review | 2026-06-03T20:52:21Z | 2026-06-03T21:02:41Z | 10m 20s |
| spec-reconcile | 2026-06-03T21:02:41Z | 2026-06-03T21:04:12Z | 1m 31s |
| finish | 2026-06-03T21:04:12Z | - | - |

## Sm Assessment

**Setup complete — routing to TEA (Caterpillar) for RED.**

- **Workflow:** tdd (phased), `setup → red → green → review → finish`. Repo: `sidequest-server` only, branch `feat/65-12-lore-world-timeline` off `develop` (NOT main). No Jira (sprint-YAML tracked only).
- **Context is authoritative and pre-authored.** The Architect (White Queen) ran a full pre-TDD pass: `sprint/context/context-story-65-12.md` (validated) + 8 ACs + description in `epic-65.yaml`. TEA writes failing tests against those 8 ACs — do not re-derive scope.
- **Read before writing tests:** the context doc's "AC Context" and "Assumptions" sections. The design was Operator-decided (2026-06-03): **world-historical spine from legends only**, verbatim era/period chip, **honest conditional sort** (numeric only when uniformly parseable, else authored order, mode recorded in OTEL).
- **One blocking Gap to confirm in RED (flagged by Architect):** legend reachability — `assemble_lore_page` currently walks files and may not hold a typed `World`/`world.legends`. Reuse `genre/loader._load_legends_flexible`, do not hand-roll a parser. If a new load path is needed, log a Design Deviation.
- **Lie-detector AC (AC6):** `reference_timeline_rendered` span with `sort_mode` — the complement assertion (sorted fixture vs mixed fixture) is the proof the conditional sort engaged. Mandatory per CLAUDE.md OTEL principle.
- **Two spec reinterpretations already logged in the context as Design Deviations** (vs spec line 234): campaign `history.yaml:chapters` excluded (wrong axis + ADR-135 D1 dormant-trope spoiler); POI founding deferred to 74-3 (no field exists — building a reader is dead code). TEA: do not write tests asserting chapter/POI-founding timeline entries.
- **Merge gate:** clear — no blocking open PRs across any repo.

## TEA Assessment

**Tests Required:** Yes
**Reason:** New player-facing render behaviour (the world Timeline section) with 8 ACs and a non-trivial honest-conditional-sort decision — needs failing tests before implementation.

**Test Files:**
- `sidequest-server/tests/server/test_reference_timeline.py` — 17 route-driven tests (no source-text wiring tests; every assertion drives the real `/reference/lore/{pack}/{world}` route and scopes to the `<section id="timeline">` slice, mirroring `test_reference_map.py`).
- 5 new fixture worlds under `tests/fixtures/packs/reference_v2_fixture/worlds/`: `timeline_fixture` (mixed-dialect, 5 legends → authored_order, + dormant-trope history.yaml + lore.history preamble), `timeline_sorted_fixture` (uniform clean-year eras authored out-of-order, undated-in-middle → sorted + undated-to-tail; no lore.history), `timeline_empty_fixture` (no legends), `timeline_malformed_fixture` (extra-key legend → typed-loader 500), `timeline_escape_fixture` (HTML-special era).

**Tests Written:** 17 tests covering all 8 ACs.
**Status:** RED confirmed via testing-runner (`65-12-tea-red`): **16 failed, 2 passed**, 4.27s, no errors.
- 13 fail on the missing `<section id="timeline">` (clean RED).
- 2 fail on the absent `sidequest.reference.timeline_rendered` span (AC6 — feature absent end-to-end).
- 1 (`test_malformed_legends_fails_loud_500`) fails because the page renders 200 today (the typed loader that must 500 does not exist yet) — exactly the No-Silent-Fallbacks contract Dev must satisfy.
- The 2 **passing** tests are intentional absence/regression guards (no-legends world → no section; Cast world unchanged + no timeline). Both carry meaningful assertions (would fail if Dev emitted a spurious timeline) — not vacuous. **Crucially: no happy-path fixture-load 500s** — every timeline world loads in the existing renderer, so all RED failures are clean contract assertions.

### Observable contract handed to Dev (the White Rabbit)
- `<section id="timeline">` (class `ref-timeline`, heading "Timeline") + TOC entry `{id:"timeline", label:"Timeline"}`, appended in `assemble_lore_page` exactly like the 65-9 Cast / 65-11 Map blocks.
- Per legend: one `data-timeline-entry="<slugify_player_name(name)>"` (class `ref-timeline__entry`); dated entries carry `data-temporal="<verbatim era-else-period>"` + a `ref-timeline__era` chip; undated entries carry no `data-temporal` and sit inside `data-timeline-group="undated"` after the dated entries.
- Order = authored, unless every dated entry is uniformly parseable → dated sorted ascending + undated tail.
- Span `sidequest.reference.timeline_rendered` (register in `FLAT_ONLY_SPANS`) with `reference.timeline_entry_count` / `reference.timeline_undated_count` / `reference.timeline_sort_mode` ∈ {`sorted`,`authored_order`}.
- `lore.yaml:history` prose → `ref-timeline__preamble` container (framing only); absent → no preamble.
- Public-only: no `history.yaml` chapter/trope/`session_range` token in the section; no `?audience` flip.
- CWE-79: the verbatim chip must be HTML-escaped.

### Rule Coverage (python lang-review)

| Rule | Test(s) | Status |
|------|---------|--------|
| #1 silent exceptions / No Silent Fallbacks | `test_malformed_legends_fails_loud_500` | failing (RED) |
| #6 test quality (meaningful assertions) | self-check below; all 17 carry value assertions | n/a |
| #11 input/output escaping (CWE-79) | `test_era_chip_is_html_escaped` | failing (RED) |

**Rules checked:** 3 of 13 lang-review rules are directly testable from the RED contract (#1, #6, #11). The remaining checks (#2 mutable defaults, #3 type annotations, #4 logging, #5 path handling, #7 resource leaks, #8 deserialization, #9 async, #10 imports, #12 deps, #13 fix-regressions) target implementation shape that does not exist yet — they are enforced on Dev's diff by the `lang-review/python.md` gate at green/review, not pinnable as RED behavioural tests.
**Self-check:** 0 vacuous tests. The 2 green-at-RED tests assert both presence (`id="cast-..."` / HTTP 200) and absence (`id="timeline"` not present), so neither passes trivially.

**Handoff:** To Dev (the White Rabbit) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes
**Branch:** `feat/65-12-lore-world-timeline` (pushed; commits `087d6317` RED, `50088548` GREEN)

**Files Changed:**
- `sidequest/server/reference_timeline.py` (NEW) — `load_legends` (reuses `genre/loader._load_legends_flexible`, no hand-rolled parser; raises → loud 500), `load_lore_history` (optional preamble), `present_lore_timeline` (verbatim era/period chip, undated group, honest conditional sort).
- `sidequest/server/reference_renderer.py` — appends the Timeline section + TOC entry in `assemble_lore_page`, mirroring the 65-9 Cast / 65-11 Map append blocks.
- `sidequest/telemetry/spans/reference.py` — `reference_timeline_rendered_span` (`entry_count`/`undated_count`/`sort_mode`) + constant registered in `FLAT_ONLY_SPANS`.
- `sidequest/server/static/reference/presenters.css` — `ref-timeline*` rules.
- `tests/server/test_reference_chrome.py`, `test_reference_chrome_v3.py`, `test_reference_chrome_wiring.py` — regression fix (see Delivery Findings): three seed worlds authored `Legend(extra="forbid")`-invalid legends (`origin: ...`); corrected to valid fields. The chrome-wiring seed enriched to render the full timeline class set (dated era chip + undated group + history preamble) so the keystone class-vs-CSS test validates every `ref-timeline` class (AC8).

**Tests:** Feature `test_reference_timeline.py` **18/18 GREEN**; full reference suite **455 passed, 0 failed, 2 skipped**. Lint (ruff check) clean, format clean, pyright 0 errors.

**Resolution of the Architect/TEA-flagged Gap:** `assemble_lore_page` does not hold a typed `World`, so the timeline loads legends via a new `load_legends(world_dir)` that reuses `_load_legends_flexible` (the same loader the genre loader uses at world-load, `loader.py:1048`) — exactly as TEA's finding directed. No parser was hand-rolled.

**Honest-sort note (AC4/AC6):** `sort_mode == "sorted"` only when every dated entry parses as a bare signed-integer year; any other dialect (relative, named-age, prose) → `authored_order`. The page never fabricates a chronology; the span records which mode fired.

**Self-review:** wired end-to-end (the section renders through the real `/reference/lore/` route, proven by the integration tests); follows the Cast/Map pattern; all 8 ACs covered; the only error path (malformed legends) fails loud per No-Silent-Fallbacks.

**Handoff:** To TEA (the Caterpillar) for verify (simplify + quality-pass).

### Dev Assessment — spec-check fix (re-green, commit `2a40e292`)

**Architect spec-check Major RESOLVED.** `load_legends` now handles BOTH legend authoring forms, mirroring `genre/loader.py:1037-1048`: the per-file `legends/` directory branch first (`sorted(glob("*.yaml"))`, skip `_meta.yaml`/`.gitkeep`, `Legend.model_validate` each, reusing `_load_yaml_raw`), with the flat `legends.yaml` (`_load_legends_flexible`) fallback. No re-implementation — reuses the loader's helpers.

- **Added** `tests/fixtures/packs/reference_v2_fixture/worlds/timeline_dir_fixture/` (a `legends/` directory world: `01_the_charter.yaml` dated 1500 + `02_the_drift.yaml` undated) and `test_directory_form_legends_render_a_timeline` — failing-first (confirmed RED: no section), then GREEN after the fix. Pins AC1/AC2 for the directory form so the blind spot can't reopen.
- **Tests:** `test_reference_timeline.py` **19/19**; reference suite **456 passed, 2 skipped, 0 failed**. ruff + pyright clean.

This was a genuine AC1/AC2 failure the original green fixtures missed (all flat-form). The spec-check seat earned its keep. **Handoff:** back to Architect (the White Queen) for spec-check re-verification.

## Architect Assessment (spec-check)

**Spec Alignment:** Drift detected
**Mismatches Found:** 1 blocking (Major) + 2 already-logged minor deviations (no action)

**Structural gate:** `gates/spec-check` → ready (AC coverage present, implementation complete, TEA + Dev deviation subsections well-formed).

- **Timeline only loads the FLAT `legends.yaml`, not the per-file `legends/` directory form** (Missing in code — Behavioral, **Major**)
  - Spec: context-story-65-12.md AC1 — "a world WITH at least one legend → response contains the Timeline section"; AC2 — "every `Legend` renders as exactly one entry." The world-loader (`genre/loader.py:1037-1048`) loads legends from EITHER a per-file `worlds/<slug>/legends/` directory (the `legends_dir.is_dir()` branch) OR a flat `legends.yaml` (`_load_legends_flexible`, the `else`).
  - Code: `reference_timeline.load_legends(world_dir)` calls only `_load_legends_flexible(world_dir / "legends.yaml")` — the flat-file branch alone. For a world authored as a `legends/` directory it reads a non-existent flat file → `([], None)` → `load_legends` returns `[]` → **no Timeline section renders**, silently (HTTP 200, as if the world had no legends).
  - Impact: **~19 of the live worlds author legends as a directory** (verified: `spaghetti_western/five_points` has `legends/` with 6 files and NO flat `legends.yaml`; same for `heavy_metal/evropi` (10), `neon_dystopia/franchise_nations` (4), `pulp_noir/annees_folles` (5), `space_opera/aureate_span`, `tea_and_murder/glenross`, `wry_whimsy/*`, …). These include the worlds the context itself named as manual-verify candidates. The feature is effectively dead-on-arrival for real content; the green suite missed it because **every timeline test fixture uses the flat `legends:` map form**, matching the implementation's blind spot.
  - Borderline No-Silent-Fallbacks: a directory-form world with many legends renders identically to a world with none.
  - Recommendation: **B — Fix code.** Extend `load_legends(world_dir)` to mirror `loader.py:1037-1048`: if `world_dir / "legends"` is a directory, load `sorted(glob("*.yaml"))` (skip `_meta.yaml` / `.gitkeep`) via `Legend.model_validate(_load_yaml_raw(f))`; else fall back to `_load_legends_flexible(world_dir / "legends.yaml")`. Reuse the loader's existing helpers — do not re-implement. TEA must add a **directory-form fixture world** (a `legends/` dir with ≥2 per-file legends, at least one dated) so AC1/AC2 are regression-pinned for both authoring forms; an honest fix needs the failing test first.

- **Conditional sort implements only the clean-year family** (Different behavior — Behavioral, Minor) — already logged by both TEA and Dev. Spec text said "e.g. all clean years OR all 'N <unit> ago'"; the "e.g." makes years-only a valid v1 subset and the authored-order fallback is honest (span records `authored_order`). **No action** — accept (Option A), deviation already captured for the boss.

- **`load_lore_history` reads `lore.yaml` raw rather than via `WorldLore`** (Different approach — Trivial) — functionally equivalent for the preamble; `yaml.safe_load` with no swallow (malformed → loud), missing/`non-str` history → `None` (correct AC5 graceful path). **No action** — accept (Option A).

**Decision:** **Hand back to Dev (the White Rabbit).** The Major directory-form mismatch is an AC1/AC2 failure for nearly all real worlds and must be fixed before review. The two minor items need no code change.

### Architect Assessment (spec-check) — RE-VERIFICATION (commit `2a40e292`)

**Spec Alignment:** Aligned. **Mismatches: None remaining.**

The Major directory-form mismatch is **RESOLVED** — independently verified, not just claimed:
- `reference_timeline.load_legends` now mirrors `genre/loader.py:1037-1048` exactly: `if (world_dir/"legends").is_dir()` → `sorted(glob("*.yaml"))` minus `_meta.yaml`/`.gitkeep` → `Legend.model_validate(_load_yaml_raw(f))`; else `_load_legends_flexible(world_dir/"legends.yaml")`. Reuses the loader's helpers (no re-implementation).
- Regression pinned: `timeline_dir_fixture` (a `legends/` directory world) + `test_directory_form_legends_render_a_timeline` — I re-ran it: **1 passed**. Timeline file 19/19; reference suite 456 passed.
- The two minor items (clean-year-only sort; raw `lore.yaml` history read) remain accepted (Option A), deviations logged.

**Decision:** **Proceed to verify (TEA).** Spec alignment confirmed across both legend authoring forms.

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed (Dev's green held; no code changed this phase).

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 4 (`reference_timeline.py`, `reference_renderer.py`, `telemetry/spans/reference.py`, `static/reference/presenters.css` + the test file for quality)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | clean | No genuine duplication; the new module intentionally mirrors the 65-9 Cast / 65-11 Map sibling pattern and reuses the loader helpers. |
| simplify-quality | clean | Naming/wiring/readability consistent with the codebase; tests route-driven. |
| simplify-efficiency | 4 findings | 0 applied — see triage below. |

**Applied:** 0 fixes.
**Triage of efficiency findings:**
1. `reference_timeline.py` — `or 0` in the sort-key lambda flagged "unreachable noise, remove" (confidence: high). **Dismissed — the finding is wrong.** I verified empirically: removing `or 0` makes pyright fail with 2 errors (`(e:_Entry)->(int|None)` is not a valid `sorted` key). The `or 0` is deliberate, commented type-narrowing on a branch where every value is guaranteed non-None at runtime. Keeping it.
2. `reference_renderer.py` — `_gate_poi_slugs_on_manifest` / `_gate_cast_slugs_on_manifest` duplication (high). **Dismissed — out of scope.** These are pre-existing 65-8/65-9 functions, not touched by 65-12; verify simplify acts on the story diff, not the whole file. A dedup refactor is a separate story.
3. `reference_renderer.py` — `_int_to_roman` micro-utility (medium). **Dismissed — out of scope** (pre-existing 65-9/65-11 helper, unchanged by 65-12; 65-12 merely calls it, consistent with Cast/Map).
4. `telemetry/spans/reference.py` — span-factory boilerplate across the whole file (high). **Dismissed — out of scope + convention.** 65-12 added exactly one span following the established per-span context-manager pattern used project-wide; collapsing 30+ spans into a factory is a cross-cutting refactor, not this story's, and would break the established convention the GM-panel span registry relies on.

**Flagged for Review:** none (all dismissals are scope/correctness calls, documented above for the Queen of Hearts).
**Reverted:** 0.

**Overall:** simplify: clean (no fixes applied; 1 in-scope finding dismissed as incorrect, 3 out-of-scope).

**Quality Checks:** Dev verified green pre-handoff (timeline 19/19; reference suite 456 passed, 0 failed; ruff + pyright clean). No code changed in verify, so that state holds. (Full-suite has 27 pre-existing Epic 74-3 content failures OUTSIDE `tests/server/` — confirmed pre-existing by Dev via stash; not in 65-12's scope.)

**Handoff:** To Reviewer (the Queen of Hearts) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (19 feat + 456 ref green; ruff/pyright clean; 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — domain assessed by Reviewer ([EDGE] below) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — domain assessed by Reviewer ([SILENT] below) |
| 4 | reviewer-test-analyzer | Yes | findings | 8 | confirmed 8 (all LOW; 1 borderline MEDIUM), dismissed 0, deferred 0 |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 | confirmed 3 (all LOW doc-precision), dismissed 0, deferred 0 |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — domain assessed by Reviewer ([TYPE] below) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings — domain assessed by Reviewer ([SEC] below) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — domain assessed by Reviewer ([SIMPLE] below) |
| 9 | reviewer-rule-checker | Yes | findings | 2 | confirmed 1 LOW (`__all__`, downgraded — convention), 1 dup of [TEST]; private-import dismissed (intentional, documented) |

**All received:** Yes (4 enabled returned; 5 disabled via `workflow.reviewer_subagents`, their domains assessed by the Reviewer directly).
**Total findings:** 12 confirmed (all LOW, one borderline MEDIUM), 1 dismissed (with rationale), 0 deferred. **No Critical/High.**

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** `GET /reference/lore/{pack}/{world}` → `reference_routes.lore_page` → `assemble_lore_page(world_dir)` → `load_legends(world_dir)` (directory branch `glob('legends/*.yaml')` → `Legend.model_validate(_load_yaml_raw(f))`, else flat `_load_legends_flexible`) → `present_lore_timeline(legends, history_prose=load_lore_history(world_dir))` → HTML `<section id="timeline">` appended to body + `{id:timeline,label:Timeline}` TOC entry. Every legend-derived value reaches the page **only** through `html.escape(...)` (verified 9/9 interpolations). Safe.

**Pattern observed:** new `reference_timeline.py` faithfully mirrors the 65-11 `reference_map.py` sibling (loader + presenter + section/TOC append + dedicated OTEL span) — consistent with the established reference-page architecture.

**Error handling:** `load_legends` and `load_lore_history` both fail **loud** — no `try/except`; a malformed/invalid file raises (`GenreLoadError`/`ValidationError`/`yaml.YAMLError`) and surfaces as HTTP 500, never a silent timeline-less 200 (`reference_timeline.py:57-102`). Empirically confirmed a bare-list invalid legend raises `GenreLoadError` (loud).

### Observations
- `[VERIFIED]` **CWE-79 escaping complete** — every interpolation in `present_lore_timeline` (`reference_timeline.py:154-177`) wraps the value in `html.escape(...)`: history prose, slug (×2), `data-temporal`, era chip, name (×2), summary (×2). Corroborated by `reviewer-rule-checker` rule #11 (8/8) and behavioural test `test_era_chip_is_html_escaped`. `[SEC]`
- `[VERIFIED]` **Public-projection firewall holds (ADR-135 D1)** — the timeline reads `legends` + `lore.history` only; `history.yaml` chapters/`tropes`/`session_range` are never touched. `test_timeline_excludes_campaign_chapter_spoilers` asserts no `SPOILER_*`/`session_range` token in the section. `[SEC]`
- `[VERIFIED]` **Fails loud on every legend authoring form** — directory form (`Legend.model_validate` raises), map form (`_load_legends_flexible` re-raises `GenreLoadError`), bare-list form (falls through to `GenreLoadError("unrecognized…")`). All three raise → 500. No silent fallback. `[SILENT]`
- `[VERIFIED]` **Edge cases sound** — empty `legends/` dir → `[]` → no section (graceful); `_temporal_of` strips whitespace → blank era falls back to period then `None` (undated); era wins over period when both present; year `0` and negative years sort correctly; equal years preserve authored order (Python stable sort); the `or 0`/`or ""` in the sort key are unreachable at runtime (guarded by `all(... is not None)`) and load-bearing for the type checker — I empirically confirmed removing `or 0` produces 2 pyright errors (`int|None` is not a valid `sorted` key). `[EDGE][SIMPLE]`
- `[LOW]` **`sort_mode` is a bare `str`** not a `Literal["sorted","authored_order"]` (`reference_timeline.py`/span attr). Acceptable (matches the span-attribute convention; tests pin both values), but a `Literal` would make the two-value contract type-enforced. `[TYPE]`
- `[LOW][TEST]` **Redundant OR assertion** — `test_timeline_section_present_for_world_with_legends` asserts `'>Timeline<' in resp.text or 'id="timeline"' in resp.text`; the second disjunct is already guaranteed by `_timeline_section()` having returned, so the OR can't add signal, and the TOC-label contract isn't independently asserted (test-analyzer + rule-checker #6 agree).
- `[LOW][TEST]` **`test_undated_entry_sorts_to_tail_in_sorted_mode` is subsumed** by `test_uniform_year_world_sorts_ascending`'s full-list equality — no independent coverage.
- `[LOW][TEST]` **`test_no_query_param_changes_timeline_section` is a no-op canary** — the lore route doesn't read `audience`, so FastAPI ignores it and `plain == gm` is structurally guaranteed; it cannot fail until the route honours the param. Encodes the ADR-135 intent but proves nothing today.
- `[LOW][TEST]` **Period-path / span-authored-counts / escape-`&amp;` / chrome-class-subset gaps** — the verbatim test doesn't assert the `period` value lands in `data-temporal`; the authored-order span's `entry_count`/`undated_count` aren't asserted (only `sort_mode`); the escape test omits `&amp;`/`<spears>`; AC8's chrome test asserts 3 of the 8 emitted classes (the chrome-wiring keystone validates all 8 against CSS, so coverage exists). All tightenable; none change behaviour.
- `[LOW][DOC]` **Three docstring-precision nits** — `load_legends` "ValidationError → 500" is imprecise for the bare-list form (still loud, but `GenreLoadError`); module docstring's "section/TOC append … reused, not rebuilt" is stale (that block is new code); `load_lore_history` omits the blank-string→`None` case. `[DOC]`
- `[LOW][RULE]` **No `__all__`** on `reference_timeline.py` (rule #10) — **downgraded, not dismissed:** none of the 7 sibling `reference_*.py` modules declare `__all__` (verified), so adding it only here would break the established module-family convention; if desired it should be a family-wide change, out of scope for 65-12.

### Rule Compliance (python lang-review, enumerated on the diff)
Cross-referenced with `reviewer-rule-checker`'s exhaustive pass (47 instances):
- #1 silent exceptions — **PASS** (no try/except in new code; all loaders raise loud).
- #2 mutable defaults — **PASS** (only `history_prose=None`, `_tracer=None`).
- #3 type annotations — **PASS** (all public fns + `_Entry` fully annotated).
- #4 logging — **PASS** (OTEL-first; no error paths needing a logger).
- #5 path handling — **PASS** (`Path /`, `glob`, `open(encoding="utf-8")`, `exists()` guard).
- #6 test quality — one **LOW** (redundant OR assert) + tightening gaps above; no vacuous/`assert True`/skip.
- #7 resource leaks — **PASS** (file + span both in `with`).
- #8 unsafe deserialization — **PASS** (`yaml.safe_load`; `_load_yaml_raw` reused, unchanged).
- #9 async — **N/A** (no async).
- #10 import hygiene — `__all__` **LOW** (convention, above); private-loader import is **intentional/documented** (dismissed — the context + TEA explicitly directed reusing `_load_legends_flexible`/`_load_yaml_raw` rather than hand-rolling a parser).
- #11 output escaping (CWE-79) — **PASS** (9/9 interpolations escaped).
- #12 dependency hygiene — **PASS** (no dep changes; stdlib `html`).
- #13 fix-introduced regressions — **PASS** (the 3 chrome-fixture corrections make engine-invalid legends valid; reference suite green).

### Devil's Advocate
Suppose this is broken. The richest attack surface is the legend loader, since it now runs the **strict typed loader on every lore-page render** where the old generic walk tolerated anything — could a real, playable world 500 its own lore page? I checked: `_load_legends_flexible`/the directory branch are the *same* code the genre loader runs at world-load (`loader.py:1037-1048`, fatal), so any world the engine can load has legends the timeline can load; an invalid legends file already makes the world unplayable, so the 500 is consistent, not a new failure. Next: the conditional sort. A malicious/odd author writes `era: "99999999999999999999"` — Python big-ints sort fine. `era: "007"` → `int("007")=7`, sorts numerically (the verbatim chip still shows "007") — correct, not a bug. `era: "-0"` → `int("-0")=0` — fine. A world where every dated entry is `"15 years ago"` (uniform relative) renders authored-order, **not** chronologically — but the span honestly reports `authored_order` and the page never claims a sort it didn't compute, which is the deliberate, logged design (No-Silent-Fallbacks honesty), not a defect. Confused-author case: a legend with `era: "   "` (whitespace) → stripped to `""` → falls to `period` → `None` → undated tail; never crashes. A directory with only `_meta.yaml`/`.gitkeep` → filtered → `[]` → no section. XSS: could a legend name like `<script>` escape the chip? No — every sink is `html.escape`, and the data-* attributes are double-quoted with escaped values (escape() encodes `"`). Spoiler leak: could chapter trope-seeds reach the page via the preamble? No — the preamble is `lore.history` only, never `history.yaml`. The one genuine residual risk is **test thinness** (the no-op audience test, the redundant tail/OR asserts, unasserted authored-mode span counts) — a future regression in authored-mode span emission or in period→`data-temporal` rendering could slip past the suite. That is a coverage weakness, not a current behavioural bug, and is recorded as LOW findings for a follow-up tightening. Nothing rises to Critical/High.

### Deviation Audit
- **TEA — conditional-sort coverage pins only clean-year family** → ✓ ACCEPTED: spec said "e.g.", years-only is a valid v1 subset; the authored-order fallback is honest.
- **TEA — chrome classes behavioural; seed-extension deferred to Dev** → ✓ ACCEPTED: Dev did extend the chrome-wiring seed in green (full class set now validated); resolved.
- **Dev — clean-year-family-only sort (relative not implemented)** → ✓ ACCEPTED: honest authored-order fallback, span records the mode; matches TEA's note.
- **Dev — no manifest gate (timeline emits no images)** → ✓ ACCEPTED: correct per context (No Stubbing — don't wire an unused gate).
- **Architect (spec-check) — directory-form gap** → ✓ ACCEPTED (resolved): the gap was caught and fixed in re-green; `load_legends` now handles both forms with a regression test.

**Handoff:** To SM for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): `assemble_lore_page` (`sidequest/server/reference_renderer.py:1297`) does NOT hold a typed `World` — it walks files via `_file_renders_by_stem`, so `world.legends` is not in scope. Confirmed the Architect's flagged Gap. Dev needs a `load_legends(world_dir)` helper that reuses `genre/loader._load_legends_flexible` (do NOT hand-roll a parser), mirroring the existing `load_cast_entries(world_dir)` / `load_cartography_config(world_dir)` loaders. Affects `reference_renderer.py` (resolve in green).
- **Improvement** (non-blocking): the natural module home is a new `sidequest/server/reference_timeline.py` exposing `load_legends` + `present_lore_timeline(...)`, mirroring `reference_map.py`'s `load_cartography_config` + `present_lore_map`, so `assemble_lore_page` stays a thin append block. Affects `sidequest/server/` (Dev's structural call).
- **Gap** (non-blocking): `test_malformed_legends_fails_loud_500` requires the typed loader to let the `Legend` `ValidationError` propagate to a 500 — Dev must NOT wrap the load in a try/except that swallows it into a timeline-less 200 (python rule #1). Affects the new loader.

### Architect (spec-check)
- **Gap** (blocking): `reference_timeline.load_legends` handles only the flat `legends.yaml` form, not the per-file `legends/` directory form that ~19 live worlds use (e.g. `five_points`, `evropi`, `franchise_nations`). Result: no Timeline section renders for those worlds (AC1/AC2 failure, silent). Fix `load_legends` to mirror `genre/loader.py:1037-1048` (directory branch first, flat fallback) and add a directory-form fixture. Affects `sidequest/server/reference_timeline.py` + a new `tests/fixtures/packs/reference_v2_fixture/worlds/timeline_dir_fixture/legends/`. *Found by Architect during spec-check.*

### Dev (implementation)
- **Improvement** (non-blocking): routing legends through the strict typed loader makes the reference page consistent with real world-load (`loader.py:1048`, fatal). Three pre-existing chrome-test seed worlds authored `Legend`-invalid legends (`origin: ...`, a forbidden field) that the old generic-walk renderer silently tolerated but the engine itself would reject at world-load. Corrected them to valid fields. Affects `tests/server/test_reference_chrome{,_v3,_wiring}.py` (done this phase). No production world is affected (an invalid legends.yaml is already unloadable).
- **Gap** (non-blocking): the full server suite has **27 pre-existing failures OUTSIDE `tests/server/`** (Epic 74-3 content refactor: `tests/genre/test_world_lore_required_74_3.py`, `test_loader.py`, `tests/cli/validate/*`, `tests/game/test_wire_genre_resources.py` — genre-tier `lore.yaml` still present, road_warrior fuel). **Confirmed pre-existing** by stashing this story's implementation and re-running two of them (still failed). Unrelated to 65-12; belongs to Epic 74-3 content work in `sidequest-content`. Reviewer/TEA-verify should scope `pf check` to `tests/server/` or treat these as known-red.

### TEA (test verification)
- **Improvement** (non-blocking): simplify-efficiency flagged real pre-existing cleanup opportunities OUTSIDE 65-12's diff — `_gate_poi_slugs_on_manifest`/`_gate_cast_slugs_on_manifest` duplication and the per-span context-manager boilerplate in `telemetry/spans/reference.py` (a project-wide convention). Both could be a future tech-debt refactor; neither is in scope here and the span pattern is intentional. Affects `sidequest/server/reference_renderer.py` + `sidequest/telemetry/spans/reference.py` (future story, not 65-12).

### Reviewer (code review)
- **Improvement** (non-blocking): timeline test suite has tightenable LOW gaps — a no-op `?audience` canary, a redundant OR assert + a subsumed tail test, and unasserted `authored_order` span counts / `period`→`data-temporal` / `&amp;` escaping / full chrome-class set. Behaviour is correct and otherwise well-covered; these are test-precision improvements. Affects `tests/server/test_reference_timeline.py` (future tightening). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): three docstring-precision nits in `reference_timeline.py` (`load_legends` fail-loud wording for bare-list, stale "section/TOC append … reused" line, `load_lore_history` blank-string case) + `sort_mode` could be a `Literal`. Cosmetic; no behaviour impact. Affects `sidequest/server/reference_timeline.py`. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Conditional-sort coverage pins only the clean-year parseable family**
  - Spec source: context-story-65-12.md, AC4
  - Spec text: "an ascending numeric sort is applied iff every dated entry exposes a uniformly-parseable comparable key (e.g. all clean ≤4-digit years, OR all 'N <unit> ago' with one unit family)"
  - Implementation: the `sorted`-mode fixture (`timeline_sorted_fixture`) uses the clean-year family only; the relative "N <unit> ago" uniform-parseable family is exercised only as part of the *mixed* (authored_order) world, not as a standalone sorted case.
  - Rationale: one parseable family proves the conditional engages and that order changes; pinning a second parseable dialect as its own sorted fixture is redundant for the RED contract and risks over-specifying the parser's accepted forms (Dev's parser design latitude).
  - Severity: minor
  - Forward impact: Reviewer should confirm the relative-phrase uniform-parseable path during review if Dev claims to support it; it is not regression-pinned by these tests.
- **Chrome classes pinned behaviourally; chrome-wiring seed-world extension deferred to Dev (green)**
  - Spec source: context-story-65-12.md, AC8
  - Spec text: "The chrome-wiring fixture (test_reference_chrome_wiring.py seed world) is extended so the new timeline CSS classes are actually rendered and validated"
  - Implementation: `test_timeline_emits_semantic_chrome_classes` asserts `ref-timeline` / `ref-timeline__entry` / `ref-timeline__era` are emitted in the section; the `test_reference_chrome_wiring.py` seed-world extension itself is NOT authored in RED.
  - Rationale: the chrome-wiring seed world can only be extended once the section renders (the feature is absent at RED); extending it now would assert against nonexistent markup. The behavioural class-emission test pins the contract; Dev extends the chrome-wiring seed + adds CSS in green (AC8 names this as Dev work).
  - Severity: minor
  - Forward impact: Dev must extend `test_reference_chrome_wiring.py` + add the CSS rules in green; Reviewer should verify the chrome-wiring suite covers the timeline classes before approve.

### Dev (implementation)
- **Conditional sort implements ONLY the clean-year parseable family (relative-phrase family not implemented)**
  - Spec source: context-story-65-12.md, AC4
  - Spec text: "an ascending numeric sort is applied iff every dated entry exposes a uniformly-parseable comparable key (e.g. all clean ≤4-digit years, OR all 'N <unit> ago' with one unit family)"
  - Implementation: `_year_key` parses only a bare signed integer (`^-?\d+$`). A world whose dated entries are all relative phrases ("15 years ago") is treated as NOT uniformly parseable → renders in `authored_order`, not sorted.
  - Rationale: minimalist + No-Silent-Fallbacks — the relative family is untested (TEA logged the same coverage gap) and adding it would ship untested parsing. Authored-order fallback is HONEST: the page renders in authored order and the span records `authored_order`; it never fabricates a relative-time chronology. The spec's "OR all 'N unit ago'" was an *example* of a parseable family, not a required second parser.
  - Severity: minor
  - Forward impact: a real world authored entirely in "N <unit> ago" will not auto-sort (it renders authored order, truthfully labelled). If that becomes desired, add a relative-phrase parser to `_year_key`'s call site + a uniform-relative fixture; no contract or sibling-story breakage.
- **No manifest gate wired for the Timeline (legends carry no images)**
  - Spec source: context-story-65-12.md, Technical Guardrails ("Manifest gate ... not needed unless a future entry emits an `<img>`. v1 emits none — note it, do not wire an unused gate")
  - Implementation: `present_lore_timeline` emits text + chips only; `load_r2_manifest_keys` / `_gate_*` are not called from the timeline path.
  - Rationale: directed by the context (No Stubbing — do not wire an unused gate).
  - Severity: trivial
  - Forward impact: none; if a future timeline entry gains imagery it must add the D2 manifest gate then.
### Reviewer (audit)
All logged deviations stamped (full rationale in the Reviewer Assessment → Deviation Audit):
- **TEA — conditional-sort coverage pins only clean-year family** → ✓ ACCEPTED (spec said "e.g."; honest authored-order fallback).
- **TEA — chrome classes behavioural; chrome-wiring seed-extension deferred to Dev** → ✓ ACCEPTED (Dev extended the chrome-wiring seed in green; full class set now validated — resolved).
- **Dev — clean-year-family-only sort (relative-phrase family not implemented)** → ✓ ACCEPTED (honest authored-order fallback; span records the mode; no fabricated chronology).
- **Dev — no manifest gate wired (timeline emits no images)** → ✓ ACCEPTED (correct per context; No Stubbing — no unused gate).
- **Architect (spec-check) — directory-form gap (blocking finding)** → ✓ ACCEPTED as RESOLVED (caught at spec-check, fixed in re-green; `load_legends` now handles both authoring forms with a regression test).
- No undocumented deviations found by Reviewer.
### Architect (reconcile)

Verified the in-flight TEA and Dev deviation entries above: spec sources (`context-story-65-12.md`, `2026-06-01-lore-reference-images-and-audience-split-design.md`) all exist; quoted spec text is accurate; the "Implementation" descriptions match the delivered code (`reference_timeline.py` `_year_key` parses `^-?\d+$` only; no manifest gate in the timeline path); forward-impact statements are sound. No corrections needed to existing entries. Two deviations not yet captured in the 6-field manifest — added here, self-contained, for the audit:

- **Delivered feature is a legends-only spine with an honest conditional sort, not the literal "merge legends + history chapters + POI founding into one sorted spine"**
  - Spec source: `docs/superpowers/specs/2026-06-01-lore-reference-images-and-audience-split-design.md` §6, line 234
  - Spec text: "Unified **world timeline** — merge legends (`era`) + history (`chapters.session_range`) + POI founding into one sorted spine"
  - Implementation: the Timeline section is built from **legends only**. (1) Campaign `history.yaml:chapters`/`session_range` are EXCLUDED — they ride the play-time axis (orthogonal to world-historical time) and carry `tropes: status: dormant` escalation seeds that ADR-135 D1 forbids on the public surface. (2) POI founding is DEFERRED to epic 74-3 — no structured founding field exists in any world (`Region.origin` is freeform prose), so a reader for it would be dead code (No Stubbing). (3) "one sorted spine" is delivered as an **honest conditional sort**: dated entries sort ascending only when every one is a clean integer year, else authored order, with the mode recorded in the `sidequest.reference.timeline_rendered` OTEL span — because the authored temporal values are free-text and not commensurable across (or within) worlds.
  - Rationale: Operator-decided 2026-06-03 (recorded in `context-story-65-12.md` Business Context + Scope Boundaries). The as-built legend/POI data has no shared sortable temporal axis and chapters are a spoiler-bearing different axis; the literal merge would either fabricate a chronology (a "convincing but mechanically-unbacked" output OTEL exists to catch) or leak spoilers.
  - Severity: major (reinterprets an explicit spec instruction) — but fully Operator-ratified and traced.
  - Forward impact: 74-3 owns POI founding (needs a content field first); a future story may add relative-phrase ("N <unit> ago") sorting; campaign-chapter rendering, if ever wanted, needs its own spoiler-safe projection — none block 65-12.

- **`load_lore_history` reads `lore.yaml`'s `history` field via raw `yaml.safe_load`, not via the `WorldLore` model**
  - Spec source: `context-story-65-12.md`, Technical Guardrails ("Optional preamble source")
  - Spec text: "`genre/models/lore.py:WorldLore.history` … reachable as `world.lore.history`. Rendered as section framing only…"
  - Implementation: `reference_timeline.load_lore_history(world_dir)` reads `lore.yaml` directly with `yaml.safe_load` and returns the `history` field when it is a non-blank `str`, rather than constructing a `WorldLore`. Same value, no validation of the rest of `lore.yaml`; still fails loud on malformed YAML (no `except`).
  - Rationale: minimal and decoupled — the assembler does not hold a typed `World`/`WorldLore` (it walks files), so reading the single field avoids constructing the full model just for a preamble string.
  - Severity: trivial (implementation detail; output identical).
  - Forward impact: none; if richer `lore.yaml` validation is ever needed on this surface, route through `WorldLore` then.

No further undocumented deviations found. AC accountability: all 8 ACs DONE (none deferred or descoped) — the deferral-justification cross-check is a no-op.