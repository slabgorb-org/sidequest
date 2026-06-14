---
story_id: "113-1"
jira_key: ""
epic: "113"
workflow: "tdd"
---
# Story 113-1: Relocate caverns_and_claudes themes/ from genre root to worlds/beneath_sunden/themes/ (ADR-140)

## Story Details
- **ID:** 113-1
- **Title:** Relocate caverns_and_claudes themes/ from genre root to worlds/beneath_sunden/themes/ (ADR-140)
- **Workflow:** tdd
- **Stack Parent:** none

## Sm Assessment

**Routing:** tdd (phased). Setup complete → handing off to **TEA (The Architect)** for the RED phase. Next phase: `red`.

**Story shape:** A coupled content+server refactor under ADR-140 (genre tier = mechanics only; the world owns flavor). `themes/` is live-wired single-world (beneath_sunden) palette content sitting at the genre-pack root. This is NOT a dead-file sweep — `load_theme_palette` raises if `themes/` is absent, so the content move and the server repoint must land **together** in coordinated PRs (server→develop, content→develop) or every beneath_sunden session crashes on dungeon attach.

**TDD guidance for TEA:**
- The mechanical contract to pin: theme palettes resolve from the **world directory** (`worlds/beneath_sunden/themes/`), not the genre-pack root (`world_dir.parent.parent`). Tests should fail RED against current root-resolution and pass once the 4 call sites repoint.
- Cover all four wiring sites listed in Setup Notes — `session_integration._theme_pack_root`, `session_helpers`, `map_emit`, and the `validate/pack.py` validator (which today checks themes/ at pack level).
- Add a regression/wiring test that proves a beneath_sunden dungeon attach still loads palettes after the move (the crash-on-absent-themes path is the real risk).
- Content side is a `git mv` (5 palette yamls + README.md) — the server tests are what guard the coupling.

**Context:** Foundational ADR-140 genre-pack-root sweep (content PR #447) is already merged to content `develop`, so the working tree is clean of the dead genre-tier files. Epic 113 follow-ons (113-2 pack_schema reconcile, 113-3 design-doc relocation) are independent and remain in backlog.

**Risks/notes:** Coupling is the only real hazard — never merge one repo's PR without the other. No Jira key (no-jira sprint story); Jira claim skipped intentionally.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-14T21:11:54Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-14T20:42:01Z | 2026-06-14T20:44:18Z | 2m 17s |
| red | 2026-06-14T20:44:18Z | 2026-06-14T20:57:53Z | 13m 35s |
| green | 2026-06-14T20:57:53Z | 2026-06-14T21:05:40Z | 7m 47s |
| review | 2026-06-14T21:05:40Z | 2026-06-14T21:11:54Z | 6m 14s |
| finish | 2026-06-14T21:11:54Z | - | - |

## TEA Assessment

**Tests Required:** Yes
**Reason:** Coupled content+server refactor with a real crash path — `load_theme_palette` raises `ThemePaletteMissingError` on dungeon attach if the content move and the code repoint diverge. The resolution contract changes (genre-pack root → world dir); not a chore bypass.

**Test Files:**
- `tests/dungeon/test_themes_world_tier.py` (NEW) — 5 tests pinning world-tier resolution (synthetic fixtures + real content; no DB)
- `tests/dungeon/test_region_projection_wiring.py` (MODIFIED) — repointed the real-attach palette load to the world dir (call site #5)

**Tests Written:** 6 failing (5 new + 1 repointed) covering AC1–AC4 + the coupling guard
**Status:** RED (verified failing via `pytest -n0` — ready for Dev)

### RED verification
- `test_theme_pack_root_resolves_to_world_dir` — RED: `_theme_pack_root` returns the pack root (AC1)
- `test_world_tier_palette_loads_via_resolver_and_genre_root_is_empty` — RED: `ThemePaletteMissingError` (resolves to empty pack root) (AC1/AC2)
- `test_load_dungeon_map_context_reads_world_tier_palette` — RED: loads `old_root_theme` not `new_world_theme` — pins `map_emit.py:799` (AC2)
- `test_real_beneath_sunden_palette_lives_at_world_tier` — RED: `ThemePaletteMissingError` on real `worlds/beneath_sunden` (content not moved) (AC4)
- `test_pack_validator_flags_malformed_world_tier_theme` — RED: validator returns `[]` (AC3)
- `test_region_projection_wiring::...real_move_vocab` — RED: `ThemePaletteMissingError` at the repointed line (real attach, needs PG)
- Untouched loader suites `test_themes.py` + `test_themes_wiring.py` → **37 passed** (loader behavior unchanged)

### Dev scope — repoint ALL FOUR production sites (same change: `world_dir.parent.parent` → `world_dir`)
1. `sidequest/dungeon/session_integration.py:75/149` — `_theme_pack_root` → return `world_dir` *(tests 1,2 + real attach)*
2. `sidequest/server/session_helpers.py:574` — ⚠️ **NOT independently behavior-tested** (deep async fn); MUST repoint; Reviewer verify
3. `sidequest/server/websocket_handlers/map_emit.py:799` — *(test 3 — differentiated fixture)*
4. `sidequest/cli/validate/pack.py:361-370` — `_validate_theme_palette` must scan `worlds/*/themes/`, not pack-root `themes/` *(test 5)*

PLUS content: `git mv genre_packs/caverns_and_claudes/themes/ → worlds/beneath_sunden/themes/` (5 yamls + README) *(test 4 + real attach)*. **Coupling: never merge one repo's PR without the other.**

### Rule Coverage

| Rule (python.md) | Test(s) | Status |
|------|---------|--------|
| #5 path-handling (pathlib resolution, no string concat) | all 6 tests (Path-based) | failing |
| #6 test-quality (meaningful assertions, no vacuous checks) | self-check — differentiated OLD/NEW ids, specific exceptions | pass |

**Rules checked:** #5 (path-handling) is the substantive applicable rule — this is a path-resolution refactor. #6 (test-quality) self-applied. Rules #1/#8/#9/#11 (exceptions/deserialization/async/input-validation) N/A — no new I/O, async, or boundary surface is introduced.
**Self-check:** 0 vacuous tests — every test asserts specific palette contents or a specific exception type.

**Handoff:** To Dev (Agent Smith) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**

_sidequest-server_ (`feat/113-1-relocate-themes-beneath-sunden`, base develop):
- `sidequest/dungeon/session_integration.py` — `_theme_pack_root` now returns `world_dir` (themes/ is world-tier)
- `sidequest/server/session_helpers.py` — region-projection palette load repointed to `world_dir`
- `sidequest/server/websocket_handlers/map_emit.py` — `_load_dungeon_map_context` palette load repointed to `world_dir`
- `sidequest/cli/validate/pack.py` — `_validate_theme_palette` now scans `worlds/<world>/themes/` (per-world loop) instead of pack-root `themes/`

_sidequest-content_ (`feat/113-1-relocate-themes-beneath-sunden`, base develop):
- `git mv genre_packs/caverns_and_claudes/themes/ → worlds/beneath_sunden/themes/` (5 palette yamls + README, 100% renames)

**Tests:** 6/6 target tests GREEN (5 new in `test_themes_world_tier.py` + 1 repointed in `test_region_projection_wiring.py`). Untouched loader suites still green (37 passed). Broader sweep: `tests/dungeon/` + `tests/cli/validate/` = 536 passed, 2 skipped. The only 2 failures are **pre-existing and unrelated** (live-pack extension-file gaps, story 113-2 — verified by stashing my changes; both still fail). Ruff clean on all 4 changed files.

**Coupling:** Both branches pushed. The content move and server repoint MUST merge together — neither alone is correct (`load_theme_palette` raises `ThemePaletteMissingError` on beneath_sunden attach if they diverge).

**Branches:** `feat/113-1-relocate-themes-beneath-sunden` (pushed: both server + content)

**Handoff:** To verify/review phase (The Merovingian / next owner). No PR created (SM owns PR creation).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 smells; 536 passed / 2 pre-existing-fail / 2 skipped; 6/6 target tests pass | N/A (no findings) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings (edge_hunter=false) — domain assessed by Reviewer ([EDGE] below) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings (silent_failure_hunter=false) — domain assessed by Reviewer ([SILENT] below) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings (test_analyzer=false) — domain assessed by Reviewer ([TEST] below) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings (comment_analyzer=false) — domain assessed by Reviewer ([DOC] below) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (type_design=false) — domain assessed by Reviewer ([TYPE] below) |
| 7 | reviewer-security | Yes | clean | 0 violations (5 rule classes checked: deserialization, path-traversal, symlink, no-silent-fallback, sensitive-logging) | N/A (no findings) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings (simplifier=false) — domain assessed by Reviewer ([SIMPLE] below) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings (rule_checker=false) — domain assessed by Reviewer (### Rule Compliance) |

**All received:** Yes (2 enabled specialists returned; 7 disabled via `workflow.reviewer_subagents`, domains assessed by Reviewer directly)
**Total findings:** 0 confirmed blocking, 1 LOW non-blocking observation (dead defensive branch — [SIMPLE]), 0 deferred

### Rule Compliance (.pennyfarthing/gates/lang-review/python.md)

Exhaustive enumeration against every rule that governs the changed `.py`:

- **#1 Silent exception swallowing** — `pack.py:_validate_theme_palette` has two `except` clauses. `except ThemePaletteMissingError: continue` = valid non-error state (world has no dungeon palette). `except Exception as exc: errors.append(...)` (with `# noqa: BLE001`) **surfaces** the loader error into the returned list — not swallowed. COMPLIANT.
- **#3 Type annotations** — `_theme_pack_root(world_dir: Path) -> Path` ✓; `_validate_theme_palette(pack_dir: Path, label: str) -> list[str]` ✓; local `errors: list[str] = []` ✓. COMPLIANT.
- **#5 Path handling** — all operations are `pathlib.Path` (`pack_dir / "worlds"`, `world_dir / "themes"`, `sorted(worlds_dir.iterdir())`); no string concat, no hardcoded separators. No new `open()` (loader's read uses `encoding`-managed handle, unchanged). `Path.resolve()` before security checks: N/A — slugs are whitelisted via `GenreLoader.find` `is_dir()` + `sd.genre_pack.worlds` membership, no user-path security gate here. COMPLIANT.
- **#6 Test quality** — new tests assert specific values (set equality on theme ids, `pytest.raises(ThemePaletteMissingError)`, differentiated OLD/NEW ids proving which dir is read, substring on error text). No `assert True`, no bare-truthy-on-wrong-value, no skips. `test_real_beneath_sunden...`'s `assert palette.themes` is an intentional non-empty guard over real content (ids may evolve) + a complementary genre-root-absent assertion. COMPLIANT.
- **#8 Unsafe deserialization** — `load_theme_palette` uses `yaml.safe_load` (themes.py:315); diff introduces no new parsing. COMPLIANT.
- **#10 Import hygiene** — function-local imports (`from sidequest.dungeon.themes import ...`) match the established lazy-import pattern in these modules (map_emit documents the precedent). No star imports, no new cycles. COMPLIANT.
- **#11 Input validation at boundaries** — confirmed by reviewer-security: `genre_slug`/`world_slug` pass through `GenreLoader.find` (existence-checked against a fixed server-rooted search-path set) and `worlds.get()` membership before the path join. No traversal surface added. COMPLIANT.
- **#9 Async** — both touched call sites (`_project_current_region`, `_load_dungeon_map_context`) are sync `def`; no async pitfalls introduced. N/A.

## Reviewer Assessment

**Verdict:** APPROVED

A clean, minimal ADR-140 refactor: the dungeon theme palette is world-tier flavor, and all four resolution sites + the content location move together. I traced every cause to every effect and found no broken link.

**Observations (11):**

1. [VERIFIED] All four production resolution sites pass `world_dir` (not `.parent.parent`): `session_integration.py:81` (`_theme_pack_root` returns `world_dir`, consumed at :152), `session_helpers.py:575`, `map_emit.py:801`, `pack.py:378`. My grep sweep confirms **zero** remaining `.parent.parent` theme/palette resolutions in `sidequest/`.
2. [SEC] Security specialist clean — slug→path join is unchanged by the diff (only the `.parent.parent` suffix dropped); `GenreLoader.find` guards with `is_dir()`, `world_slug` is a `worlds` dict key, `yaml.safe_load` throughout (`themes.py:315`). No new traversal/deserialization surface. Evidence: security subagent report + `loader.py:2314-2321`.
3. [PRE][TEST] Preflight clean: 0 code smells, 536 passed in `tests/dungeon/` + `tests/cli/validate/`, all 6 story-113-1 target tests pass. The 2 failures are pre-existing and out-of-scope (live-pack extension-file gaps in five non-caverns packs → story 113-2; verified by Dev via stash). New tests use differentiated OLD/NEW theme ids and specific-exception assertions — not vacuous.
4. [VERIFIED] Wiring proven end-to-end: `test_region_projection_wiring::...real_move_vocab` drives a **real** Pg dungeon attach loading the **real** beneath_sunden palette from the world dir; `test_load_dungeon_map_context_reads_world_tier_palette` drives the real `map_emit` fn with a differentiated fixture. Non-test consumers exercised through production code paths.
5. [VERIFIED] Validator broadening is bounded — the new `worlds/*/themes/` scan validates *all* world palettes, but `find genre_packs -type d -path "*/worlds/*/themes"` returns **only** `caverns_and_claudes/worlds/beneath_sunden/themes`, and **no** genre-root `themes/` dirs remain. So no other pack gets a newly-surfaced palette error, and the move is provably complete (no half-done leftover). Evidence: content-repo `find`.
6. [EDGE] Boundary paths all handled: no `worlds/` dir → `return []`; a non-dir entry under `worlds/` → `(world_dir/"themes").is_dir()` is False → `continue`; an empty `themes/` dir → loader raises `ValueError("no theme files…")` → surfaced as an error (correct: malformed). `sorted(iterdir())` gives deterministic error ordering.
7. [SIMPLE][LOW] Non-blocking: in the new validator the `except ThemePaletteMissingError: continue` branch is effectively unreachable — the preceding `(world_dir/"themes").is_dir()` guard already guarantees the dir exists, and the loader only raises `ThemePaletteMissingError` when `themes/` is *absent* (`themes.py:304-305`). Harmless defensive belt-and-suspenders that mirrors the loader contract for readability; not worth a change.
8. [DOC] Comments/docstrings updated to cite ADR-140 at all four sites; no stale `world_dir.parent.parent` / "pack root holds themes/" comments survive. The moved `README.md` already describes the beneath_sunden world and reads correctly at the new location.
9. [SILENT] No silent fallbacks: loader errors are returned in the validator's list (loud); `ThemePaletteMissingError → continue` is a genuine non-error state. At runtime, an absent `themes/` raises loudly on attach — which is exactly the intended coupling tripwire, not a swallow.
10. [TYPE] Type contracts intact — `Path` in/out on `_theme_pack_root`, `list[str]` return on the validator, annotated local accumulator. No stringly-typed path surface.
11. [RULE] python.md rule-by-rule done above (### Rule Compliance) — #1/#3/#5/#6/#8/#10/#11 all COMPLIANT, #9 N/A.

**Data flow traced:** WS connect → session `genre_slug`/`world_slug` (validated against the loaded pack at connect) → `loader.find(genre_slug)/"worlds"/world_slug` = `world_dir` → `load_theme_palette(world_dir)` reads `world_dir/themes/*.yaml` via `yaml.safe_load` → `ThemePalette` → `project_region` / dungeon map emit. Safe: slugs whitelisted, palette content is operator-authored.

**Coupling (process, not code):** The one real hazard is merge ordering — the server repoint and the content `git mv` MUST land together, or beneath_sunden raises `ThemePaletteMissingError` on attach. Both branches are pushed (base `develop`). SM must merge both or neither. Flagged for finish.

### Devil's Advocate

Argue this is broken. **(1) A half-merge ships.** If SM merges the server PR without the content PR, every beneath_sunden dungeon attach raises `ThemePaletteMissingError` and the session dies on connect. This is real — but it is the *designed* loud failure (No Silent Fallbacks), the coupling guard test (`test_real_beneath_sunden_palette_lives_at_world_tier`) fails RED until the move lands, and Dev pushed both branches. The residual risk is purely human merge-ordering, mitigated by explicit flags in three places. Not a code defect. **(2) `_theme_pack_root` is now an identity function** — `return world_dir`. A future reader could see dead abstraction. But it is the named seam two tests pin and a comment anchor in `session_helpers`; inlining it would force test edits for zero behavioral gain. Acceptable. **(3) Malicious slugs.** Could a crafted WS `world_slug` like `../../etc` traverse? No: `GenreLoader.find` returns only a path whose `is_dir()` holds under a fixed server-rooted search set, and `world_slug` must be a key in the already-loaded `worlds` dict before the join. The diff does not widen this; it narrows the resolved root from pack to world. **(4) A future world adds a typo'd `themes/`.** Previously unvalidated (validator only saw the pack root); now the `worlds/*/themes/` scan catches it — a strict improvement, and it can only surface *real* malformations (proven: only beneath_sunden has a world themes dir today, and it's well-formed). **(5) TOCTOU** between `is_dir()` and `load_theme_palette` — the unreachable-branch concern (obs 7) — is a non-issue for operator-authored content validation and is handled (skip) if it ever fired. Nothing uncovered changes the verdict.

**Handoff:** To SM (Morpheus) for finish-story. Merge both coupled PRs together (server + content → develop) or neither.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): The story's WIRING list omitted a 5th theme-resolution site. `tests/dungeon/test_region_projection_wiring.py:153` resolves the REAL beneath_sunden palette via `world_dir.parent.parent` and raises `ThemePaletteMissingError` after the content move. Repointed to `world_dir` during RED. Affects `sidequest-server/tests/dungeon/test_region_projection_wiring.py` (already updated; Dev/Reviewer should confirm no other `world_dir.parent.parent` theme reads remain anywhere). *Found by TEA during test design.*
- **Gap** (non-blocking): `session_helpers.py:574` and `map_emit.py:799` are *inline* `world_dir.parent.parent` resolutions (no shared `_theme_pack_root` helper), so fixing the helper alone leaves them broken. `map_emit:799` is behavior-tested (test 3); `session_helpers:574` is NOT (it sits deep inside an async projection fn with self-heal/DB-error preconditions — disproportionate to drive in a unit test). Affects `sidequest-server/sidequest/server/session_helpers.py` (repoint to `world_dir`; Reviewer must verify). *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): Two live-pack validation tests fail on this branch *independent of 113-1* — `test_pack_validator.py::test_all_live_packs_pass_content_validation` and `test_pack_validator_crossref.py::test_all_live_packs_pass_cross_reference_lint`. Cause is missing genre-tier extension files (`openings.yaml`/`powers.yaml`/`weather.yaml`/`seed_tropes.yaml`) in neon_dystopia/pulp_noir/road_warrior/tea_and_murder/wry_whimsy — the `pack_schema` still lists extensions whose files moved to worlds under the ADR-140 sweep. **Verified pre-existing**: both fail with my changes stashed; none of the failing packs is `caverns_and_claudes`. This is the sibling backlog story 113-2 (pack_schema reconcile) per the SM assessment. Affects `sidequest-content/genre_packs/*/pack_schema` (reconcile extensions list against world-tier moves). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): The new `_validate_theme_palette` keeps an `except ThemePaletteMissingError: continue` branch that is unreachable given the preceding `(world_dir / "themes").is_dir()` guard (the loader only raises that error when `themes/` is absent). Harmless defensive code; a future cleanup could drop it. Affects `sidequest-server/sidequest/cli/validate/pack.py` (remove the dead branch). *Found by Reviewer during code review.*
- **Process note** (non-blocking, for SM): This is a coupled two-repo change — merge the server and content PRs **together** (both base `develop`) or neither, or beneath_sunden raises `ThemePaletteMissingError` on dungeon attach. Affects merge ordering in the finish phase. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Did not edit test_themes.py / test_themes_wiring.py**
  - Spec source: context-story-113-1.md, AC5
  - Spec text: "existing dungeon theme tests (tests/dungeon/test_themes.py, test_themes_wiring.py) updated and green"
  - Implementation: Left both unchanged (verified 37 pass as-is). The loader `load_theme_palette` reads `<dir>/themes/` and is unchanged — only the directory passed at the call sites changes. test_themes.py builds `tmp_path/themes/`; test_themes_wiring.py uses an owned fixture pack — neither exercises genre-root-vs-world-tier resolution. New coverage lives in `test_themes_world_tier.py` + the repointed `test_region_projection_wiring.py`.
  - Rationale: Editing tests that don't exercise the changed behavior is churn; the AC assumed those files needed updating, but analysis shows they don't.
  - Severity: minor
  - Forward impact: none

### Dev (implementation)
- No deviations from spec. Repointed exactly the four sites named in the TEA scope (`world_dir.parent.parent` → `world_dir`) plus the content `git mv`. Kept `session_integration._theme_pack_root` rather than inlining it (the AC permits either; keeping it is the minimal change that passes the two seam-named tests with no test edits).

### Reviewer (audit)
- **TEA: "Did not edit test_themes.py / test_themes_wiring.py"** → ✓ ACCEPTED by Reviewer: correct call. The loader (`load_theme_palette`) is unchanged — only the directory passed at the call sites changed — so those two suites don't exercise the changed resolution. Verified 37 still pass (preflight). Editing them would be pure churn.
- **Dev: "Kept `_theme_pack_root` rather than inlining"** → ✓ ACCEPTED by Reviewer: the AC explicitly permits "`_theme_pack_root` *or its callers*." Keeping it is the minimal change that passes the two seam-named tests with zero test edits. It is now an identity function (noted as obs 7/Devil's-Advocate #2) but serves as a named seam + comment anchor — inlining would force test edits for no behavioral gain.
- No undocumented deviations found. The diff matches the TEA scope exactly (four sites + content move); I traced each and found nothing diverging from spec that TEA/Dev failed to log.

## Setup Notes

**Repositories:** server (sidequest-server), content (sidequest-content)
**Branch Strategy:** gitflow (coupled content + server change)
**Branches Created:**
- sidequest-server: `feat/113-1-relocate-themes-beneath-sunden` (base: develop)
- sidequest-content: `feat/113-1-relocate-themes-beneath-sunden` (base: develop)

**Work Summary:**
This story is a coupled content + server refactoring per ADR-140 (genre tier = mechanics only; world owns flavor). The `themes/` directory must move from the caverns_and_claudes genre-pack root to `worlds/beneath_sunden/themes/`. All server code that resolves themes to the genre-pack root must be updated to resolve to the world directory instead.

**Server Wiring to Update:**
- `sidequest/dungeon/session_integration.py:75` — `_theme_pack_root()` returns `world_dir.parent.parent` (called at :149)
- `sidequest/server/session_helpers.py:574` — `load_theme_palette(world_dir.parent.parent)`
- `sidequest/server/websocket_handlers/map_emit.py:799` — `load_theme_palette(world_dir.parent.parent)`
- `sidequest/cli/validate/pack.py:370` — `load_theme_palette(pack_dir)` (validator checks themes/ at pack level)
- `load_theme_palette` signature: `sidequest/dungeon/themes.py:288` (reads `<pack_dir>/themes/*.yaml`)

**Content Change:**
`git mv genre_packs/caverns_and_claudes/themes/ -> genre_packs/caverns_and_claudes/worlds/beneath_sunden/themes/`
(5 palette yamls + README.md)

**Critical Constraint:** Content move and code change must land together in coordinated PRs (server→develop, content→develop) or beneath_sunden sessions will crash on dungeon attach when attempting to load themes.