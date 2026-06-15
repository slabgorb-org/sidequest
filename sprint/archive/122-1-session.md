---
story_id: "122-1"
jira_key: ""
epic: "122"
workflow: "tdd"
---
# Story 122-1: Foundation floor — relocate asset_urls, slug_fold, reference_anchors below server tier (kills 4 upward edges)

## Story Details
- **ID:** 122-1
- **Jira Key:** (none — Jira not in use)
- **Workflow:** tdd
- **Stack Parent:** none
- **Epic:** 122 — Honest Layering (ADR-147)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-15T23:29:13Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-15T23:06:42.359945+00:00 | 2026-06-15T23:08:57Z | 2m 14s |
| red | 2026-06-15T23:08:57Z | 2026-06-15T23:15:59Z | 7m 2s |
| green | 2026-06-15T23:15:59Z | 2026-06-15T23:22:13Z | 6m 14s |
| review | 2026-06-15T23:22:13Z | 2026-06-15T23:29:13Z | 7m |
| finish | 2026-06-15T23:29:13Z | - | - |

## Technical Approach

**Scope:** Behavior-preserving relocation of three pure utility modules currently living under `sidequest/server/` to a new foundation tier (`sidequest/foundation/`), correcting upward-import edges per ADR-147's layering law.

**Design:** Establish a new `sidequest/foundation/` package with dependencies limited to third-party libraries and `sidequest/protocol/` only. Move three modules into it:

1. **`server/asset_urls.py`** → **`foundation/asset_urls.py`**
   - Pure function: `resolve_asset_url(spec: str, fallback: str = ...) -> str`
   - Reads `os.environ` for path prefixes; emits OTEL span (watcher API is foundation-level per ADR-132)
   - Current importers: `genre/audio_paths.py`, `game/room_file_loader.py`

2. **`server/slug_fold.py`** → **`foundation/slug_fold.py`**
   - Pure function: `fold_to_ascii(text: str) -> str`
   - NFKD text normalization; no dependencies beyond `unicodedata`
   - Current importer: `game/alias_resolution.py`

3. **`server/reference_anchors.py`** → **`foundation/reference_anchors.py`**
   - Pure functions: `reference_url_for_ability(...)`, `build_lore_url(...)`
   - URL builders; dependencies: string manipulation, `protocol/` lookups only
   - Current importers: `game/builder.py`, `game/cookbook/compose.py`

**Implementation Steps:**
1. Create `sidequest/foundation/` directory with `__init__.py`
2. Move `server/asset_urls.py`, `server/slug_fold.py`, `server/reference_anchors.py` into `foundation/`
3. Update all four importers to reference `foundation.*` instead of `server.*`
4. Verify no new upward edges are introduced (audit imports in `foundation/` modules)
5. Run full test suite to confirm behavior preservation
6. Update any relevant documentation or docstrings that reference the old paths

**Acceptance Criteria:**
- ✓ `sidequest/foundation/` directory exists with `__init__.py`
- ✓ Three modules relocated: `asset_urls.py`, `slug_fold.py`, `reference_anchors.py`
- ✓ All four importers (`genre/audio_paths.py`, `game/room_file_loader.py`, `game/alias_resolution.py`, `game/builder.py`, `game/cookbook/compose.py`) updated to import from `foundation`
- ✓ No imports in `foundation/` modules reach up into `server/`
- ✓ All existing tests pass; no logic changes, only import path updates
- ✓ OTEL behavior unchanged (asset_urls span emission preserved)

**Exit Condition:** Code review approval; story marked done + merged to develop branch per `pf sprint story finish`.

## Sm Assessment

**Verdict:** Setup complete; routing to TEA for the RED phase.

**Scope is sound and bounded.** A 3-point behavior-preserving refactor: relocate three pure helpers (`asset_urls`, `slug_fold`, `reference_anchors`) below the server tier per ADR-147, killing 4 upward import edges. No library extraction, no logic change — only module moves + importer rewrites. This is the foundation-floor step (122-1) that the rest of epic 122 builds on; 122-5 (the enforcing CI guard) lands last.

**Caveat for TEA (verify before writing tests):** The exact target filenames and the importer list in the Technical Approach were *inferred* by my setup subagent, not confirmed against the tree. The story title fixes the three modules to relocate and asserts "4 upward edges." Before authoring RED tests, grep the server repo to confirm the real module paths and the actual set of importers, and pin the test to the true edge count. Ground the import-direction assertions in what the code actually does, not the inferred summary.

**Pre-handoff checklist:** session ✓, fields set ✓, context written ✓, branch `feat/122-1-foundation-floor-relocate-pure-utils` (base `develop`) ✓, no blocking PRs ✓, Jira skipped (no-jira project).

## TEA Assessment

**Tests Required:** Yes
**Phase:** finish

**Test Files:**
- `tests/foundation/test_foundation_floor_122_1.py` — 18 tests (the spec for ADR-147 step 1)
- `tests/foundation/__init__.py` — new test tier (mirrors the new `sidequest/foundation/` source tier)

**Tests Written:** 18 tests across 5 enforced invariants. **Status: RED** (18 failed, 0 passed; verified via testing-runner, RUN_ID `122-1-tea-red`, `-n0`). Zero collection/syntax errors — every failure is a genuine precondition (`ModuleNotFoundError: sidequest.foundation`, or an assertion that the old path/edge still exists).

**Invariant coverage:**
- **A. Foundation package + API** (4 tests) — `sidequest.foundation` exists; the three modules re-expose their full public surface (asset_urls: 3 fns; slug_fold: 1; reference_anchors: 7).
- **B. Old server paths removed, no shim** (2 tests) — `find_spec("sidequest.server.{mod}")` is None + the `.py` files are gone. Enforces relocation-not-copy (No Silent Fallbacks / No Stubbing).
- **C. Behaviour preserved** (3 tests) — known-output anchors harvested from the existing suites: `resolve_asset_url` CDN/local/raise; `fold_to_ascii("Évropi")=="Evropi"`, `"café"=="cafe"` (case-preserving NFKD, not `ascii,"ignore"`); reference-anchor URL fragments (which transitively exercise `reference_slug.slugify`).
- **D. Killed upward edges** (6 tests) — AST scan: no `game/genre/orbital/magic/interior` module imports the three relocated modules from `sidequest.server`; plus one parametrized test per concrete importer.
- **E. Foundation-floor purity** (1 test) — AST scan: nothing under `sidequest/foundation/` imports `sidequest.server` (bans server only — `protocol/` and `sidequest.telemetry` are allowed per ADR-147 / ADR-132). Guarded by a floor-exists precondition so it can't pass vacuously.

### Rule Coverage

| Rule (python.md) | Test(s) | Status |
|------|---------|--------|
| #10 import hygiene (no circular / no upward) | `test_no_domain_tier_upward_edges_for_relocated_modules`, `test_foundation_floor_imports_nothing_from_server`, `test_known_importer_*` | failing (RED) |
| #6 test quality (meaningful assertions, no vacuous) | self-check below + floor-exists precondition in invariant E | n/a (self-applied) |
| CLAUDE.md "No Silent Fallbacks / No Stubbing" | `test_old_server_module_path_removed`, `test_old_server_module_file_removed` | failing (RED) |
| ADR-147 §Enforcement (AST layer guard) | invariants D + E | failing (RED) |

**Rules checked:** import-hygiene (#10) is the load-bearing rule for a layering refactor and is fully covered; #6 self-applied. Checks #1–5, #7–9, #11–13 are not applicable to a RED suite of pure-relocation assertions (no I/O, async, deserialization, or user input in the tests).
**Self-check:** 0 vacuous tests. Every test has a concrete value/spec/state assertion. The two AST-scan invariants (D, E) are guarded against vacuous-pass: D scans dirs that exist now (5 real violations → non-vacuous RED); E asserts `FOUNDATION_DIR.is_dir()` first so an absent floor fails loudly rather than scanning an empty set.

**Handoff:** To Dev (Hephaestus) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes
**Branch:** `feat/122-1-foundation-floor-relocate-pure-utils` (pushed to origin, base `develop`)

**What changed:** Established the `sidequest/foundation/` floor (ADR-147 step 1) and `git mv`'d four pure modules into it. Acted on TEA's blocking Gap finding — `reference_slug` came down with `reference_anchors` (it's the transitive `slugify` dep), so the floor is self-consistent: `reference_anchors → foundation.reference_slug → foundation.slug_fold`. `asset_urls` retains its `sidequest.telemetry.spans.asset_url` span import, which ADR-147/ADR-132 bless as foundation-level (the floor-purity test bans `sidequest.server` only, and passes).

**Files Changed (31):**
- `sidequest/foundation/__init__.py` (new — charter docstring), `foundation/{asset_urls,slug_fold,reference_slug,reference_anchors}.py` (relocated via git mv; internal imports repointed to the floor)
- Production importers repointed `server.* → foundation.*`: `server/{rest,views,emitters,render_mounts,reference_projection,reference_renderer,utils}.py`, `server/websocket_handlers/map_emit.py`, `game/{room_file_loader,builder,alias_resolution}.py`, `game/cookbook/compose.py`, `genre/audio_paths.py`, `handlers/{connect,journal_request}.py`, `cli/validate/locations.py`
- Existing tests repointed (behaviour preservation): `tests/server/{test_asset_urls,test_player_portrait_party_status,test_views,test_reference_rules_projection,test_reference_slug,test_reference_poi_projection,test_101_8_slug_unification}.py`, `tests/game/{test_room_file_loader_runtime_png,test_alias_diacritic_fold_and_pos}.py`, `tests/genre/test_audio_url_resolution.py`
- No compatibility shim left at the old `sidequest.server.*` paths (No Silent Fallbacks / No Stubbing).

**Tests:** 18/18 guard tests GREEN (`tests/foundation/test_foundation_floor_122_1.py`); regression set across 21 affected files 272 passed / 12 pre-existing skips / **0 new failures**; import smoke OK across all 19 relocated/importer modules (re-verified after ruff import-reorg — no circular import introduced). Verified via testing-runner RUN_IDs `122-1-dev-green` + `122-1-dev-green-postruff`. `ruff check` + `ruff format` clean on all 31 touched files (scoped to touched files only — bare `ruff format .` churns ~167 files, a known repo drift).

**Self-review:** behaviour-preserving relocation, no logic edits; all ACs met (foundation exists + full public API, old paths gone, no domain→server edges for the three modules, floor purity holds); wired end-to-end (the 19-module import smoke is the wiring proof — every relocated symbol resolves from its new home in production paths). No OTEL change needed — pure relocation; the `asset_url_resolved_span` emit is preserved and exercised by `test_asset_url_behaviour_preserved`.

**Handoff:** To Reviewer (Hermes) — verify phase.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (3 pre-existing smells, none introduced) | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | Yes | findings | 3 (1 low/self-dismissed, 1 low, 1 medium) | confirmed 0 blocking, dismissed 1, deferred 2 (non-blocking notes) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings (assessed manually — no try/except in moved code; relocation adds no error paths) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings (assessed manually — guard suite non-vacuous per TEA self-check + my read) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings (assessed manually — slug_fold docstring ref accurate; OTEL span-name doc mismatch noted) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (assessed manually — signatures byte-identical, no type changes) |
| 7 | reviewer-security | Yes | findings | 2 (both pre-existing, low, not introduced) | confirmed 0 blocking, deferred 2 (non-blocking notes) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings (assessed manually — pure relocation, no complexity added) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings (assessed manually — see Rule Compliance below) |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`, assessed manually)
**Total findings:** 0 confirmed blocking, 1 dismissed (with rationale), 4 deferred (non-blocking improvements/pre-existing)

## Reviewer Assessment

**Verdict:** APPROVED

A textbook behavior-preserving relocation. I traced every moved file old-vs-new and every importer hunk myself; all three enabled specialists corroborate. No Critical/High findings.

**Data flow traced:** player `portrait_ref` (session state, not client input) → `resolve_player_portrait_url` (`foundation/asset_urls.py:78`) → `resolve_asset_url` (`:48`) → CDN/local URL. Path is byte-identical to pre-relocation; safe.

**Pattern observed:** clean four-file `git mv` to a new lowest tier with a documented charter (`foundation/__init__.py` states the import-direction law); internal chain `reference_anchors → foundation.reference_slug → foundation.slug_fold` is self-contained; `asset_urls → sidequest.telemetry` is the one allowed non-protocol edge (ADR-132).

**Error handling:** unchanged — `_local_path_for` still raises `ValueError` on unknown prefix (`foundation/asset_urls.py:38`), satisfying No Silent Fallbacks; no try/except added anywhere.

### Observations

1. `[VERIFIED]` All four moved modules are **logically byte-identical** to their server originals — `diff develop:sidequest/server/asset_urls.py sidequest/foundation/asset_urls.py` shows ONLY a ruff one-line reflow of the `with asset_url_resolved_span(...)` call (`foundation/asset_urls.py:71`); `slug_fold`/`reference_slug`/`reference_anchors` each changed exactly one internal import/docstring line. Complies with the behavior-preserving AC.
2. `[VERIFIED]` Foundation-floor purity holds — `foundation/reference_anchors.py:18`→`foundation.reference_slug`, `reference_slug.py:17`→`foundation.slug_fold`, `asset_urls.py:28`→`sidequest.telemetry` (ADR-132 allowed). No `sidequest.server` import in any foundation module; `test_foundation_floor_imports_nothing_from_server` green.
3. `[VERIFIED]` **No shim / no silent fallback** — old `server/{asset_urls,slug_fold,reference_anchors,reference_slug}.py` deleted (git rename), **zero** surviving `sidequest.server.<mod>` references repo-wide (my grep + preflight grep agree). Complies with CLAUDE.md No Stubbing / No Silent Fallbacks.
4. `[VERIFIED]` Wiring end-to-end — import smoke across 19 modules (`sidequest.server.rest`, `websocket_session_handler`, `foundation.reference_anchors`) succeeds with no circular import; 272 regression tests pass, 0 new failures.
5. `[EDGE]` OTEL span name `server.asset_url.resolved` (`telemetry/spans/asset_url.py:14`) now names the wrong tier for a foundation-emitted span. **LOW, non-blocking** — the span constant is pre-existing and untouched by this PR; renaming would break the `server.asset_url.resolved` assertion contract and is out of scope for a behavior-preserving move. Deferred as a tracked improvement.
6. `[EDGE]`/`[TEST]` Guard test's named-importer list covers only the 5 domain-tier importers, not the server/handlers/cli callers also rewritten. **Correct by design** — ADR-147 forbids only DOMAIN→server; server/handlers importing foundation is allowed-direction. The no-shim relocation makes any stale-path reversion a hard `ImportError` (not silent), and story 122-5 adds the repo-wide guard. Non-blocking; matches TEA's logged scoping deviation.
7. `[SEC]` Two pre-existing low-risk observations in the moved code: CDN-mode `resolve_asset_url` lacks the prefix-allowlist local-mode enforces (`asset_urls.py:68`); `build_rules_url`/`build_lore_url` don't validate `pack`/`world` are slug-safe (`reference_anchors.py:32`). **NOT introduced by this PR** (byte-identical relocation); inputs are session/authored, not client WebSocket. Non-blocking; noted for tracking.
8. `[DOC]` `slug_fold.py:5` docstring references `sidequest.server.utils.slugify_player_name` — **accurate, leave as-is**: `server/utils.py` is a *caller* of the fold and was not relocated; documenting a downward caller relationship is correct.

### Rule Compliance

`[RULE]` (rule_checker disabled — enumerated manually against python lang-review + CLAUDE.md):
- **#10 import hygiene** (no circular / honest layering): foundation modules import only third-party + `protocol`-adjacent + telemetry; domain importers now point down to foundation; import smoke confirms no cycle. **COMPLIANT** (this is the story's whole point).
- **#1 silent exception swallowing**: no try/except in any moved module; none added. **COMPLIANT.**
- **#6 test quality**: 18 guard tests, all with concrete value/spec/state assertions; AST scans guarded against vacuous-pass (floor-exists precondition). **COMPLIANT.**
- **#3 type annotations at boundaries**: all moved public functions retain their full annotations (byte-identical). **COMPLIANT.**
- **CLAUDE.md No Silent Fallbacks / No Stubbing**: no compatibility shim at old paths. **COMPLIANT.**
- **CLAUDE.md OTEL**: `asset_url_resolved_span` emission preserved (exercised by `test_asset_url_behaviour_preserved`); span-name tier label is cosmetic/pre-existing (Observation 5). **COMPLIANT** (emission intact).

Manual coverage for disabled specialists: `[SILENT]` no swallowed errors introduced (no try/except in diff); `[TYPE]` signatures byte-identical, no stringly-typed regressions; `[SIMPLE]` pure relocation, zero complexity added (no new abstractions, no dead code — the only new file is an `__init__.py` charter docstring).

### Devil's Advocate

Suppose this PR is broken. The most plausible failure for a relocation is a *missed* importer — a lazy in-function import, a `TYPE_CHECKING` block, or a string-built `importlib.import_module("sidequest.server." + mod)` that a literal-text sed sweep never touched. If one existed, production would `ImportError` at first call on a path the test suite doesn't exercise. I hunted exactly this: a repo-wide grep (not just import statements) for both dotted and slash forms returned zero hits outside the intentional guard test; edge-hunter independently swept lazy/conditional/`TYPE_CHECKING`/string-literal forms and also found zero. The no-shim design is actually *protective* here — there is no `server.asset_urls` left to silently resolve, so any survivor is a loud failure, and `rest.py`/`websocket_session_handler.py` (which transitively import nearly everything) load cleanly in the smoke test.

Second attack: did a "pure relocation" smuggle a logic change? A reformatted line could alter behavior if ruff mis-joined a string. I diffed the moved files old-vs-new byte-for-byte: the only non-import change is `asset_urls.py:71` collapsing a 3-line `with` onto one line — semantically identical. The `test_asset_urls.py` assertions changed only by line-joining; the asserted URL strings are character-identical.

Third: could the floor secretly still touch server? That would defeat the ADR. `reference_anchors` pulls `slugify` from `reference_slug`, which pulls `fold_to_ascii` from `slug_fold` — all now in foundation; the AST purity scan (which bans *any* `sidequest.server` import, not just the three relocated names) is green. A confused future dev reverting one importer is caught immediately by ImportError, and 122-5 will add the standing guard. The pre-existing CDN path-traversal and slug-validation gaps are real but unchanged by this diff and reach no client-controlled input — flagging them as blockers would be punishing a relocation for sins it inherited. Nothing here rises above LOW. Verdict stands: APPROVED.

**Handoff:** To SM (Themis) for finish-story.

## Delivery Findings

<!-- marker -->
### TEA (test design)

- **Gap** (blocking): The relocation's foundation-purity AC drags a 4th module down that the ADR/story did not name. `server/reference_anchors.py` imports `slugify` from `server/reference_slug.py`; `reference_slug` is pure (only `re` + `slug_fold`). Moving `reference_anchors` to `foundation/` while leaving `reference_slug` in `server/` mints a **new** `foundation → server` upward edge, violating ADR-147's foundation law. Dev must also relocate `sidequest/server/reference_slug.py` → `sidequest/foundation/reference_slug.py` (it imports `slug_fold`, which is also moving — the floor stays self-consistent). Affects `sidequest/server/reference_anchors.py`, `sidequest/server/reference_slug.py` (relocate), and its other importers `server/reference_renderer.py`, `server/reference_projection.py`, `cli/validate/locations.py` (repoint to `foundation`). Enforced by `test_foundation_floor_imports_nothing_from_server`. *Found by TEA during test design.*
- **Improvement** (non-blocking): The "4 upward edges" figure (story title + ADR-147 Decision §2) under-counts. The live tree has **5** domain-tier import statements of the three modules: `game/room_file_loader.py` & `genre/audio_paths.py` (asset_urls), `game/alias_resolution.py` (slug_fold), `game/builder.py` & `game/cookbook/compose.py` (reference_anchors). ADR-147's own Context table lists all five files; only its Decision prose says "four". Tests pin the real set and assert *zero* remain (robust to the discrepancy). Worth reconciling the scalar in ADR-147 / 122-5's guard. Affects `docs/adr/147-honest-layering-pure-logic-below-server.md`. *Found by TEA during test design.*
- **Note** (non-blocking): A large set of **server-tier and `handlers/`** files also import these three modules (rest.py, render_mounts.py, audio_cue.py, websocket_session_handler.py, emitters.py, views.py, reference_projection.py, websocket_handlers/map_emit.py, utils.py, reference_slug.py, handlers/connect.py, handlers/journal_request.py). These are *allowed-direction* (server → foundation) but still break on a no-shim relocation, so Dev must repoint them all, plus the existing test files that import the old paths (`tests/server/test_asset_urls.py`, `tests/game/test_alias_diacritic_fold_and_pos.py`, etc.). Not layering violations — mechanical follow-through for behaviour preservation. *Found by TEA during test design.*

### Dev (implementation)

- TEA's blocking Gap (relocate `reference_slug` too) was **resolved in this implementation** — not deferred. The floor is self-consistent and the purity guard passes.
- **Improvement** (non-blocking): With `foundation/` now established, story **122-5**'s global no-upward-import CI guard should add `foundation/` to its scanned-package set (a foundation module importing `sidequest.server` would be just as illegal as a domain one). TEA's `test_foundation_floor_imports_nothing_from_server` already covers it for this story; 122-5 should fold the same check into the repo-wide guard so it survives independently. Affects the future `122-5` guard test. *Found by Dev during implementation.*

### Reviewer (code review)

- **Improvement** (non-blocking): The OTEL span name `server.asset_url.resolved` now mislabels the tier — it fires from `foundation/asset_urls.py` but is named `server.*`, so the GM panel attributes a foundation event to the server tier. The constant is pre-existing (untouched by this PR) and renaming it breaks the `server.asset_url.resolved` assertion contract, so it was correctly left out of this behavior-preserving move. Worth a follow-up span-rename pass (foundation tier → `foundation.asset_url.resolved`) once 122-x stabilizes. Affects `sidequest/telemetry/spans/asset_url.py` + the two asserting tests in `tests/server/test_asset_urls.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking, pre-existing): Two low-risk gaps live in the relocated (not new) code: CDN-mode `resolve_asset_url` skips the prefix-allowlist that local mode enforces, and `build_rules_url`/`build_lore_url` don't validate `pack`/`world` are slug-safe. Both reach only session/authored inputs today, not client WebSocket data — not introduced here and not blocking, but worth a defensive-validation ticket. Affects `sidequest/foundation/asset_urls.py`, `sidequest/foundation/reference_anchors.py`. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

3 deviations

- **Scoped the import-direction guard to the three relocated modules, not a full server-import ban**
  - Rationale: A full ban here would fail on edges that stories 122-2/3/4 remove; scoping keeps 122-1 independently green and matches ADR-147's "each step independently shippable behind the guard."
  - Severity: minor
  - Forward impact: 122-5 must generalize the same AST helper to all five domain packages (no module-name scope).
- **Added a 4th-module purity assertion the story scope did not enumerate**
  - Rationale: The named-three list is insufficient to satisfy the foundation-purity AC ("no imports in foundation/ reach up into server/"); the test enforces the *invariant*, leaving Dev free to choose relocate-vs-rewire.
  - Severity: minor
  - Forward impact: Dev relocates one extra pure module; no behaviour change.
- **Relocated a fourth module (`reference_slug`) beyond the three the session scope enumerated**
  - Rationale: `reference_anchors` calls `reference_slug.slugify`; leaving `reference_slug` in `server/` would mint a new `foundation→server` edge, failing the foundation-purity AC. `reference_slug` is pure (`re` + `slug_fold`, which is also moving), so relocation is the clean, behaviour-preserving fix — no call-signature change.
  - Severity: minor
  - Forward impact: none — `reference_slug`'s other importers (`server/reference_renderer.py`, `server/reference_projection.py`, `cli/validate/locations.py`, plus 4 tests) were repointed to `foundation.reference_slug`; all allowed-direction.

## Design Deviations

### TEA (test design)
- **Scoped the import-direction guard to the three relocated modules, not a full server-import ban**
  - Spec source: ADR-147 §Enforcement; sprint/epic-122.yaml (122-5)
  - Spec text: "Add a CI guard that fails if any module under game/, genre/, ... imports from sidequest.server"
  - Implementation: 122-1 tests assert no domain import of `asset_urls`/`slug_fold`/`reference_anchors` specifically; the *global* no-upward guard is story 122-5.
  - Rationale: A full ban here would fail on edges that stories 122-2/3/4 remove; scoping keeps 122-1 independently green and matches ADR-147's "each step independently shippable behind the guard."
  - Severity: minor
  - Forward impact: 122-5 must generalize the same AST helper to all five domain packages (no module-name scope).
- **Added a 4th-module purity assertion the story scope did not enumerate**
  - Spec source: session Technical Approach (names three modules); ADR-147 Decision §2
  - Spec text: "move resolve_asset_url, fold_to_ascii, and the reference_anchors URL builders"
  - Implementation: `test_foundation_floor_imports_nothing_from_server` will also force `reference_slug` down (see Delivery Finding Gap).
  - Rationale: The named-three list is insufficient to satisfy the foundation-purity AC ("no imports in foundation/ reach up into server/"); the test enforces the *invariant*, leaving Dev free to choose relocate-vs-rewire.
  - Severity: minor
  - Forward impact: Dev relocates one extra pure module; no behaviour change.

### Dev (implementation)
- **Relocated a fourth module (`reference_slug`) beyond the three the session scope enumerated**
  - Spec source: `.session/122-1-session.md` Technical Approach; sprint/epic-122.yaml (122-1 title)
  - Spec text: "relocate asset_urls, slug_fold, reference_anchors below server tier"
  - Implementation: also `git mv`'d `server/reference_slug.py → foundation/reference_slug.py` (chose relocate over rewire, per TEA's blocking Gap).
  - Rationale: `reference_anchors` calls `reference_slug.slugify`; leaving `reference_slug` in `server/` would mint a new `foundation→server` edge, failing the foundation-purity AC. `reference_slug` is pure (`re` + `slug_fold`, which is also moving), so relocation is the clean, behaviour-preserving fix — no call-signature change.
  - Severity: minor
  - Forward impact: none — `reference_slug`'s other importers (`server/reference_renderer.py`, `server/reference_projection.py`, `cli/validate/locations.py`, plus 4 tests) were repointed to `foundation.reference_slug`; all allowed-direction.

### Reviewer (audit)
- **TEA: scoped import-direction guard to the three relocated modules** → ✓ ACCEPTED by Reviewer: correct — ADR-147 forbids only DOMAIN→server upward edges; a full ban here would falsely flag edges that 122-2/3/4 remove. The repo-wide guard is explicitly 122-5's job. Sound scoping.
- **TEA: added a 4th-module purity assertion (`reference_slug`) the scope didn't enumerate** → ✓ ACCEPTED by Reviewer: the foundation-purity AC ("no foundation→server imports") logically requires it, and testing the invariant rather than the file-list is the right call.
- **Dev: relocated a fourth module (`reference_slug`) beyond the enumerated three** → ✓ ACCEPTED by Reviewer: relocate-over-rewire is the clean fix; `reference_slug` is pure and its transitive dep `slug_fold` was also moving, so the floor stays self-consistent. Verified byte-identical content; all other importers repointed (allowed-direction). No behaviour change.
- No undocumented deviations found: every hunk in the diff is either an import-path repoint or ruff reformatting of pre-existing drift in a touched file. Confirmed by old-vs-new byte comparison of the four moved modules.