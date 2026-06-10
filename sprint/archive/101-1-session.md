---
story_id: "101-1"
jira_key: ""
epic: "101"
workflow: "tdd"
---
# Story 101-1: Align daemon renderer models with server contract — remove CARTOGRAPHY tier + zimage configs, align StageCue.camera typing, add cross-repo contract test

## Story Details
- **ID:** 101-1
- **Jira Key:** (none)
- **Workflow:** tdd
- **Epic:** 101 — Split-Brain Remediation — Daemon Renderer Drift & Dead Twins
- **Stack Parent:** none
- **Points:** 3
- **Type:** refactor

## Overview

The daemon and server have deliberately-duplicated renderer models that have drifted:

1. **Daemon RenderTier** carries `CARTOGRAPHY` (removed server-side 2026-04-28)
2. **Daemon RenderTier** carries two zimage-specific tier configs
3. **StageCue.camera** is typed `CameraPreset` enum daemon-side vs plain `str` server-side
4. **No contract test** holds the seam — drift can recur silently

This story aligns the daemon to the server contract and adds a cross-repo contract test to prevent drift.

## Acceptance Criteria

### 1. Daemon RenderTier Cleanup
- Daemon `RenderTier` no longer defines `CARTOGRAPHY` tier
- Daemon `RenderTier` no longer defines two zimage tier configs
- Verify by grep that neither term appears in production code post-removal
- All other RenderTier values (IMAGE, PORTRAIT, MUSIC, EMBED, ORCHESTRATION) remain unchanged and functional

### 2. StageCue.camera Type Alignment
- `StageCue.camera` is typed as plain `str` (matching server contract)
- No longer typed as `CameraPreset` enum daemon-side
- Serialization/deserialization of StageCue must accept any string camera value
- Verify by type-checking that server and daemon StageCue definitions are compatible

### 3. Cross-Repo Contract Test
- A new contract test exists that asserts the duplicated-subset model (RenderTier, StageCue, and any other shared types) remains in sync between repos
- Test fails loudly if daemon RenderTier fields diverge from server RenderTier fields
- Test is wiring test: runs as part of daemon test suite
- No silent fallbacks: error messages are clear

### 4. Code Quality
- `ruff check .` passes in daemon repo
- `pytest` passes in daemon repo (new test included)
- No debug code or temporary workarounds left behind
- Branch is clean and ready for review

## Technical Context

### Repos Involved
- **sidequest-daemon**: Remove CARTOGRAPHY, zimage configs, align StageCue.camera, add daemon-side test
- **sidequest-server**: Reference contract for RenderTier and StageCue

### Key Files (Likely Locations)
- **Daemon renderer models:** `sidequest-daemon/sidequest_daemon/renderer/` or similar
- **Daemon media:** `sidequest-daemon/sidequest_daemon/media/`
- **Server models:** `sidequest-server/sidequest/renderer/` or `sidequest/protocol/`

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-10T05:06:53Z
**Branch:** feat/101-1-align-daemon-renderer-models

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-10T04:41:58Z | 2026-06-10T04:44:10Z | 2m 12s |
| red | 2026-06-10T04:44:10Z | 2026-06-10T04:54:33Z | 10m 23s |
| green | 2026-06-10T04:54:33Z | 2026-06-10T04:58:37Z | 4m 4s |
| review | 2026-06-10T04:58:37Z | 2026-06-10T05:06:53Z | 8m 16s |
| finish | 2026-06-10T05:06:53Z | - | - |

## Sm Assessment

**Setup Complete:** Yes
**Story:** 101-1 — Align daemon renderer models with server contract (refactor, 3pts, p2)
**Epic:** 101 — Split-Brain Remediation — Daemon Renderer Drift & Dead Twins
**Repos:** daemon (sidequest-daemon)
**Workflow:** tdd (phased)
**Branch:** feat/101-1-align-daemon-renderer-models (created in sidequest-daemon off develop)
**Context:** sprint/context/context-story-101-1.md written with 4 ACs
**Jira:** none (epic has no Jira key — Jira ops skipped)

**Scope summary for TEA (RED phase):** Write failing tests covering three seams —
(1) daemon `RenderTier` no longer defines `CARTOGRAPHY` or the two zimage tier configs;
(2) `StageCue.camera` is plain `str`, not the `CameraPreset` enum; (3) a cross-repo
contract test that holds the daemon↔server renderer-model duplicated-subset seam and
fails loudly on future drift. Server-side is the reference contract — read the server
RenderTier/StageCue definitions to anchor the expected shape.

**Handoff:** To TEA (Amos Burton) for the RED phase.

## TEA Assessment

**Tests Required:** Yes
**Reason:** N/A — this is a contract-alignment refactor with behavioral and structural assertions, not a doc/config chore.

**Test Files:**
- `tests/test_101_1_renderer_contract.py` (NEW) — 13 tests across AC-1/2/3: CARTOGRAPHY removal (enum + both zimage config tables), StageCue.camera retype to `str | None`, daemon-internal routing invariants, and the cross-repo contract (loads real server `renderer.models`, asserts RenderTier members + StageCue fields + camera type match).
- `tests/test_stage_cue_camera.py` (MODIFIED) — enum-identity assertion retargeted to str-value (new contract).
- `tests/test_zimage_mlx_worker.py` (MODIFIED) — `test_tier_configs_match_render_tier_enum` now asserts `"cartography" not in` configs.
- `tests/test_otel_spans.py` (MODIFIED) — two render calls moved off the removed `cartography` tier to `fog_of_war` (same 1024² / 20-step high-fidelity config).

**Tests Written/Updated:** 16 (13 new + 3 modified files' assertions) covering 3 ACs.
**Status:** RED confirmed (run 101-1-tea-red): 9 failed / 10 passed.
- 8 core AC assertions FAIL against current code (CARTOGRAPHY present, camera enum-typed, cross-repo drift detected) — the desired RED.
- 1 modified assertion (`test_tier_configs_match_render_tier_enum`) FAILS (cartography still in configs).
- The 10 passing include over-deletion/invariant guards (live-tier retention, IMAGE_TIERS/_TIER_TO_R2_KIND consistency, field-name parity) that are GREEN now and only flip RED on a *partial* removal — drift guards by design.

**Cross-repo loader verified OPERATIONAL:** `_load_server_renderer_models()` loaded `sidequest-server/sidequest/renderer/models.py` with no FileNotFoundError/ImportError and correctly reported `daemon-only={'cartography'}`. This is real cross-repo wiring, not a snapshot.

### Rule Coverage

| Rule (python.md) | Test(s) | Status |
|------|---------|--------|
| #6 test quality — meaningful assertions, no vacuous | every test asserts a specific value/membership; self-checked, none vacuous | enforced |
| #3 type annotations at boundaries | all test fns annotated `-> None`; `_load_server_renderer_models() -> ModuleType` | pass |
| #5 path handling — pathlib + `resolve()` + explicit lookup | `_load_server_renderer_models()` uses `Path(...).resolve()` / `parents[2]`, no string concat | pass |
| #1 silent exceptions / No Silent Fallbacks | loader raises `FileNotFoundError`/`ImportError` loudly; no skip, no bare except | enforced |
| #10 import hygiene | removed unused `pytest` import; ruff clean on all 4 files | pass |

**Rules checked:** 5 of 13 lang-review rules are materially applicable to a test-only delta (the rest target source error-handling/async/deser/deps not present in these test files).
**Self-check:** 0 vacuous tests (every assertion checks a concrete value; the modified `test_stage_cue_accepts_camera` asserts both str-value equality AND `isinstance str`).

**Wiring test:** `test_render_tier_members_match_server` + `test_stage_cue_fields_match_server` + `test_stage_cue_camera_type_matches_server` are the integration/wiring tests — they import and compare the real production models from BOTH repos, not isolated stubs.

**Handoff:** To Dev (Naomi Nagata) for GREEN. Removal surface: `renderer/models.py` (drop CARTOGRAPHY member + the now-unused `CameraPreset` import, retype `StageCue.camera` to `str | None`), `media/zimage_config.py` (drop both CARTOGRAPHY config entries), `media/daemon.py` (drop `"cartography"` from `IMAGE_TIERS`), `media/workers/zimage_mlx_worker.py` (drop `"cartography"` from `_TIER_TO_R2_KIND`), and the stale comment in `media/prompt_composer.py:35`.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed (sidequest-daemon):**
- `sidequest_daemon/renderer/models.py` — dropped `RenderTier.CARTOGRAPHY`, dropped the now-unused `CameraPreset` import, retyped `StageCue.camera` `CameraPreset | None` → `str | None` (matches server contract).
- `sidequest_daemon/media/zimage_config.py` — deleted the CARTOGRAPHY entry from both `ZIMAGE_TIER_CONFIGS` (turbo) and `ZIMAGE_HIGH_FIDELITY_TIER_CONFIGS` (the "two zimage configs").
- `sidequest_daemon/media/daemon.py` — removed dead `"cartography"` from `IMAGE_TIERS`.
- `sidequest_daemon/media/workers/zimage_mlx_worker.py` — removed dead `"cartography"` from `_TIER_TO_R2_KIND`.
- `sidequest_daemon/media/prompt_composer.py` — refreshed stale `CARTOGRAPHY` comment reference to `FOG_OF_WAR`.

**Tests:** Full daemon suite GREEN — 431 passed / 0 failed / 0 skipped (run 101-1-dev-green). Story files: `test_101_1_renderer_contract.py` 13/13, `test_stage_cue_camera.py` 3/3, `test_zimage_mlx_worker.py` 16/16, `test_otel_spans.py` 17/17. No regressions across the suite.
**Lint:** `ruff check` clean on all changed source.
**Branch:** feat/101-1-align-daemon-renderer-models (pushed to origin).

**Wiring:** The cross-repo contract test (`test_render_tier_members_match_server` / `test_stage_cue_fields_match_server` / `test_stage_cue_camera_type_matches_server`) loads the real server `renderer.models` and now passes — the seam is held end-to-end against production models in both repos, not stubs. `grep -rn "CARTOGRAPHY\|cartography"` over `sidequest_daemon/` returns NONE.

**OTEL note:** No new OTEL spans required. This is a model-alignment/dead-code-removal refactor with no new subsystem decision path — the existing `zimage_mlx.render` spans (verified by `test_otel_spans.py`) already cover the render path. Per CLAUDE.md, OTEL is not needed for removals that add no decision logic.

**Self-review:**
- [x] Code wired end-to-end (contract test compares live production models both repos; no cartography refs remain)
- [x] Follows project patterns (minimal removal, no new abstractions)
- [x] All ACs met (AC-1 tier+configs removed, AC-2 camera→str, AC-3 contract test green, AC-4 ruff+pytest clean)
- [x] No error handling needed (pure removal + type narrowing; arbitrary camera strings now accepted at StageCue, validated downstream at RenderTarget — fail-loud preserved)

**Handoff:** To verify/review phase.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (431 pass, 0 lint, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 5 | confirmed 0 blocking, 5 noted non-blocking |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 | confirmed 3 (all Low), 0 blocking |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 2 (rule #3, #13) | confirmed real, downgraded High→Medium with empirical evidence, non-blocking |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 1 confirmed-Medium (camera type-contract), 4 confirmed-Low (2 stale docstrings, 1 weak assertion, 1 inherited comment imprecision), 4 deferred (test-quality improvements), 0 blocking

## Reviewer Assessment

**Verdict:** APPROVED

This is a clean, minimal contract-alignment refactor. Full suite GREEN (431 passed), lint clean, zero `cartography` references remain in production. No Critical or High issues. The findings are Low/Medium and non-blocking; the most substantive (camera type-contract) is empirically verified to be a pre-existing condition, not a regression introduced by this diff.

### Confirmed findings (all non-blocking)

| Severity | Tag | Issue | Location | Disposition |
|----------|-----|-------|----------|-------------|
| [MEDIUM] | [RULE][TYPE] | `build_render_target` passes `cue.camera` (now `str \| None`) into `RenderTarget(camera=...)` typed `CameraPreset \| None`. Valid presets coerce fine; an unknown camera string fails at RenderTarget construction. | `media/workers/zimage_mlx_worker.py:121,156,167` | Non-blocking — pre-existing & fail-loud (see Devil's Advocate). Tracked as Delivery Finding for epic-101. |
| [LOW] | [DOC] | Module docstring says "7 image tiers"; now 6 after CARTOGRAPHY removal. | `renderer/models.py:3` | Should fix — fold into finish or fast-follow. |
| [LOW] | [DOC] | Test docstring says "five surviving image tiers" but the loop asserts six. | `tests/test_101_1_renderer_contract.py:162` | Should fix — off-by-one in docstring only; test body correct. |
| [LOW] | [TEST] | `test_stage_cue_accepts_camera` assertion (`== "topdown_90"`, `isinstance str`) does not discriminate the new `str` contract from the old enum (CameraPreset is a `str` subclass). | `tests/test_stage_cue_camera.py:18` | Non-blocking — the contract IS discriminated by `test_stage_cue_camera_annotation_is_optional_str` (`str in get_args` is False under old typing) + `test_stage_cue_accepts_arbitrary_camera_string` (construction raises under old typing). Suggest `type(cue.camera) is str` to harden. |
| [LOW] | [DOC] | `prompt_composer.py:35` "FOG_OF_WAR vs LANDSCAPE" names a tier not in `_KIND_TO_TIER`; inherited imprecision from the old CARTOGRAPHY wording. | `media/prompt_composer.py:35` | Non-blocking — dimensions do differ (1024² vs 1024×768), claim is factually true. |

### Dispatch tags
- **[EDGE]** — subagent disabled; I traced boundary paths myself (empty camera, None camera, unknown camera, valid preset) — see Devil's Advocate.
- **[SILENT]** — subagent disabled; I checked: no swallowed exceptions; the contract-test loader raises `FileNotFoundError`/`ImportError` loudly (No Silent Fallbacks honored), no bare except in the diff.
- **[TEST]** — test-analyzer: 5 non-blocking notes (weak assertion confirmed Low, missing empty-string/round-trip edge cases deferred as out-of-scope improvements).
- **[DOC]** — comment-analyzer: 2 stale docstring counts (Low), 1 inherited imprecision (Low).
- **[TYPE]** — covered via rule-checker's #3 finding (camera type-contract, Medium, see above).
- **[SEC]** — subagent disabled; I checked: `SIDEQUEST_SERVER_ROOT` env is a test-only path prefix, `resolve()`+`is_file()` guarded, `importlib` loads a version-controlled file (not untrusted input). No secrets, no injection surface. Clean.
- **[SIMPLE]** — subagent disabled; the diff is pure deletion + a one-line type narrowing — already minimal, no over-engineering. Clean.
- **[RULE]** — rule-checker: 11/13 rules clean, 2 findings (#3, #13) both the same camera type-contract root cause, confirmed real and downgraded to Medium with empirical before/after evidence.

### Rule Compliance (python.md, applied to the diff)
- **#1 silent exceptions:** PASS — loader raises loudly; no bare except / suppress in diff.
- **#2 mutable defaults:** PASS — `StageCue` list/dict defaults are pydantic fields (per-instance deep-copied), pre-existing; no new function mutable-defaults.
- **#3 type annotations at boundaries:** 1 finding — `cue.camera: str | None` flows into `RenderTarget.camera: CameraPreset | None` (Medium, non-blocking, pre-existing call sites unchanged by diff).
- **#5 path handling:** PASS — pathlib `/` + `resolve()`, no string concat, no bare `open()`.
- **#6 test quality:** PASS — all 16 tests assert specific values; one weak (non-discriminating) assertion noted Low; no vacuous `assert True`/truthy-only.
- **#10 import hygiene:** PASS — removed `CameraPreset` import from `models.py` confirmed unused there; still imported where needed (scene_interpreter, prompt_composer, recipe_loader, camera_specs, preview, worker); no star imports.
- **#4/#7/#8/#9/#11/#12:** N/A or PASS — no new logging/resources/deserialization-of-untrusted/async/API-boundary/dependency changes in the diff.

### Five+ observations
1. [VERIFIED] CARTOGRAPHY removal is complete and consistent across all 5 sites — evidence: `grep -rn "CARTOGRAPHY\|cartography" sidequest_daemon/` returns NONE; the two `RenderTier.CARTOGRAPHY`-keyed config dicts (`zimage_config.py`) would have been import-time `AttributeError` if left, so removal was self-forcing. Complies with "Delete Dead Code in the Same PR".
2. [VERIFIED] Cross-repo contract test loads the REAL server model — evidence: `test_101_1_renderer_contract.py:307-314` uses `importlib.util.exec_module` on `sidequest-server/sidequest/renderer/models.py`; preflight confirms it ran green against the co-located server, and it correctly reported `daemon-only={'cartography'}` in the RED phase. Genuine wiring test, not a stub/snapshot.
3. [MEDIUM][RULE][TYPE] camera type-contract — see finding table + Devil's Advocate. Confirmed real, non-blocking.
4. [LOW][DOC] two stale docstring tier-counts (models.py:3, test:162) introduced/left by the removal.
5. [VERIFIED] No Silent Fallbacks honored in the new code — evidence: loader raises `FileNotFoundError` (not `pytest.skip`) when server repo absent (`test_101_1_renderer_contract.py:299-305`); the daemon's unknown-camera path fails loud at RenderTarget rather than silently rendering a wrong angle.
6. [VERIFIED] OTEL not required — evidence: pure dead-code removal + type narrowing adds no subsystem decision path; existing `zimage_mlx.render` spans (test_otel_spans.py) still cover the render path. Complies with CLAUDE.md ("not needed for cosmetic/removal changes with no new decision logic").

### Devil's Advocate

Argue this is broken. The strongest case: **the camera retype is cosmetic theatre.** AC-2's stated intent is that the daemon "accept any string camera value" the server sends. But I proved the daemon still cannot *render* an arbitrary camera — a non-CameraPreset string sails through `StageCue` and then detonates a `ValidationError` inside `build_render_target` → `RenderTarget`. A confused operator reading AC-2 would believe arbitrary cameras now work; they don't. Worse, the failure moved from a clean ingestion-boundary rejection to a deeper render-time crash — harder to attribute. And lines 156/167's `cue.camera or CameraPreset.scene` only catch the `None` case; a non-empty unknown string is truthy and flows straight through to the crash, so there's an asymmetry (None → graceful scene default; unknown string → crash).

Why this does NOT sink the PR: I verified empirically (case 5) that the *old* `CameraPreset`-typed `StageCue` crashed on an arbitrary camera **even earlier**, at ingestion — so this diff introduced no new failure; it removed the wire-boundary one. The realistic contract is that the server emits camera values from the shared CameraPreset vocabulary (the daemon owns those names; the server only passes strings through), and for that real contract the full path works end-to-end (case 3 OK). An unknown camera the renderer genuinely can't draw *should* fail loud (No Silent Fallbacks), not silently substitute. The story's ACs are scoped to the StageCue model + cartography removal + the contract test — all met and tested. The RenderTarget.camera boundary is pre-existing behavior outside this story's scope; hardening it (widen to `str|None`, or coerce-with-OTEL-fallback for the None/unknown asymmetry) is the right epic-101 follow-up, recorded below. The `cue.camera or CameraPreset.scene` asymmetry is real but pre-existing and unchanged by this diff. Net: a genuine, tracked design seam — not a defect in this diff.

**Data flow traced:** server-sent `camera` string → `StageCue.camera: str|None` (accepts, AC-2) → `build_render_target` → `RenderTarget.camera: CameraPreset|None` (coerces valid preset / fails loud on unknown). Safe for the real contract; unknown-camera fail-loud is correct.
**Pattern observed:** clean self-forcing enum removal (dict keys make partial removal an import error) at `media/zimage_config.py:126,176`.
**Error handling:** loud failures preserved end-to-end (loader raise, RenderTarget validation, metadata guard at `zimage_mlx_worker.py:108`).
**Handoff:** To SM for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Reviewer (code review)
- **Improvement** (non-blocking): The camera-contract alignment is complete at the `StageCue` wire boundary (AC-2) but the daemon's internal `build_render_target` (`media/workers/zimage_mlx_worker.py:121,156,167`) still passes the now-`str` camera into `RenderTarget.camera: CameraPreset | None` (`media/recipes.py:82`). Valid presets coerce fine; an unknown camera string fails loud at RenderTarget (pre-existing, verified not a regression). Two epic-101 hardening options: (a) widen `RenderTarget.camera` to `str | None` for true end-to-end string acceptance, or (b) add an explicit coerce-with-OTEL-fallback in `build_render_target` to resolve the `None → scene default` vs `unknown-string → crash` asymmetry. Recommend folding into a later epic-101 story, not blocking 101-1.
- **Improvement** (non-blocking): Two stale docstring tier-counts introduced/left by the CARTOGRAPHY removal — `renderer/models.py:3` ("7 image tiers" → 6) and `tests/test_101_1_renderer_contract.py:162` ("five surviving" → six). Trivial; fold into SM finish commit or a fast-follow. Test bodies are correct; docstrings only.

### Dev (implementation)
- No upstream findings during implementation. The removal surface TEA mapped was exact; consumers of `cue.camera` pass it into a `RenderTarget(camera=...)` that stays `CameraPreset`-typed, so the str retype coerces (or fails loud) at that boundary — no consumer required changes. Full daemon suite green (431 passed). [Reviewer note: "no consumer required changes" holds for the valid-preset and None cases (the real contract); an *unknown* camera string fails loud at RenderTarget — pre-existing, not a regression. See Reviewer Delivery Finding above.]

### TEA (test design)
- **Gap** (non-blocking): The story context's AC-1 listed guessed surviving tier names (IMAGE, PORTRAIT, MUSIC, EMBED, ORCHESTRATION) that do not match the real daemon `RenderTier` (SCENE_ILLUSTRATION, PORTRAIT, PORTRAIT_SQUARE, LANDSCAPE, TEXT_OVERLAY, FOG_OF_WAR). Tests anchor on actual code, not the guessed list. Affects `sprint/context/context-story-101-1.md` (AC-1 surviving-tiers list is illustrative only; the test file is authoritative).
- **Gap** (non-blocking): CARTOGRAPHY's real blast radius is 5 production sites, wider than the "enum + 2 configs" in the story title — also `media/daemon.py` (`IMAGE_TIERS` frozenset), `media/workers/zimage_mlx_worker.py` (`_TIER_TO_R2_KIND`), and a stale comment in `media/prompt_composer.py:35`. Affects those files (Dev must remove the `"cartography"` strings; tests enforce the first two, the comment is reviewer-caught).
- **Improvement** (non-blocking): The cross-repo contract test only covers the renderer-model seam (RenderTier + StageCue). The epic notes other duplicated subsets (e.g. daemon genre-model subset VisualStyle/AudioConfig) that have no contract test. Affects future epic-101 stories — consider a general "duplicated-subset contract" suite. Out of scope for 101-1.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Removed CARTOGRAPHY's dead routing strings + a stale comment, beyond the literal "enum + 2 configs" of AC-1**
  - Spec source: context-story-101-1.md, AC-1
  - Spec text: "remove CARTOGRAPHY tier + the two zimage tier configs"
  - Implementation: Also deleted the leftover `"cartography"` string from `media/daemon.py` `IMAGE_TIERS`, the `"cartography"` key from `media/workers/zimage_mlx_worker.py` `_TIER_TO_R2_KIND`, and refreshed a stale `CARTOGRAPHY` reference in a `media/prompt_composer.py` comment (`FOG_OF_WAR vs LANDSCAPE`).
  - Rationale: TEA's invariant guard tests (`test_image_tier_routing_has_no_dead_tiers`, `test_r2_kind_mapping_has_no_dead_tiers`) — the highest-authority spec — require those tables to route only real RenderTier values, so a tier removed from the enum but left in routing is a half-removed feature (No Silent Fallbacks). Minimal code to pass the tests required deleting them.
  - Severity: minor
  - Forward impact: none — these were dead string references to a tier that no longer exists.
- **No deviations from the test contract otherwise** — implemented exactly the five-site removal + camera retype the RED tests pinned; no abstractions added.

### TEA (test design)
- **Cross-repo contract test reaches the sibling sidequest-server repo (against the 78-3 "don't reach sibling repos" precedent)**
  - Spec source: context-story-101-1.md, AC-3
  - Spec text: "A cross-repo contract test exists that asserts the duplicated-subset model ... remains in sync between repos"
  - Implementation: `_load_server_renderer_models()` loads `../sidequest-server/sidequest/renderer/models.py` via `importlib.util` (env override `SIDEQUEST_SERVER_ROOT`, else sibling path). Story 78-3's TEA log warned that a daemon-repo test reaching another repo is "fragile and wrong-repo."
  - Rationale: 78-3's concern was a *documentation* obligation (ADR notes in the orchestrator repo) verifiable by code review. A wire-contract test inherently MUST compare both sides — that is its entire purpose — and both repos are always co-located in the orchestrator checkout. The server module depends only on pydantic + stdlib, so it loads in isolation in the daemon env.
  - Severity: minor
  - Forward impact: none — if the layout changes, set `SIDEQUEST_SERVER_ROOT`.
- **Missing server repo is a hard FAILURE, not a pytest skip**
  - Spec source: SOUL.md / CLAUDE.md "No Silent Fallbacks"
  - Spec text: "If something isn't where it should be, fail loudly. Never silently try an alternative path, config, or default."
  - Implementation: `_load_server_renderer_models()` raises `FileNotFoundError` when the server models file is absent, rather than `pytest.skip(...)`.
  - Rationale: A skipped contract test silently stops holding the seam and gives false confidence — the exact failure mode the epic is remediating. Fail-loud is the correct behavior here, not a defect.
  - Severity: minor
  - Forward impact: none in the orchestrator checkout (server always present).
- **Scope expansion: tests force removal of the dead "cartography" routing/R2 strings, not just the enum + 2 configs**
  - Spec source: context-story-101-1.md, AC-1
  - Spec text: "remove CARTOGRAPHY tier + the two zimage tier configs"
  - Implementation: Added invariant tests `test_image_tier_routing_has_no_dead_tiers` and `test_r2_kind_mapping_has_no_dead_tiers` that require `daemon.IMAGE_TIERS` and `zimage_mlx_worker._TIER_TO_R2_KIND` to contain only real RenderTier values. These force Dev to also delete the leftover `"cartography"` string in those two tables.
  - Rationale: A tier removed from the enum but left in the routing frozenset and R2-kind map is a half-removed feature (dead code / No Silent Fallbacks). These pass now and only flip RED on a partial removal.
  - Severity: minor
  - Forward impact: Dev must touch `media/daemon.py` and `media/workers/zimage_mlx_worker.py` in addition to `renderer/models.py` and `media/zimage_config.py`.
- **Updated existing tests that encoded the old contract (test maintenance, not new coverage)**
  - Spec source: context-story-101-1.md, AC-2/AC-1
  - Spec text: "StageCue.camera is typed as plain str" / "remove CARTOGRAPHY tier"
  - Implementation: Retargeted `test_stage_cue_camera.py::test_stage_cue_accepts_camera` (enum-identity → str-value), `test_zimage_mlx_worker.py::test_tier_configs_match_render_tier_enum` (`cartography in` → `not in`), and two `test_otel_spans.py` render calls (`cartography` → `fog_of_war`, same 1024² / 20-step high-fidelity config).
  - Rationale: Those pre-existing tests assert the OLD contract; without updating them the suite could never reach GREEN (contradictory assertions). TEA owns all test changes; Dev touches only source.
  - Severity: minor
  - Forward impact: none.

### Reviewer (audit)
- **Dev: removed dead routing strings + comment beyond literal AC-1** → ✓ ACCEPTED by Reviewer: correct — the highest-authority spec (TEA's invariant tests) required it, and leaving a tier in routing after enum removal is a half-wired feature the project forbids. Verified clean: `grep` returns zero cartography refs.
- **Dev: no other deviations from the test contract** → ✓ ACCEPTED by Reviewer: confirmed — the diff is exactly the five-site removal + camera retype the RED tests pinned; no scope creep, no unrequested abstractions.
- **TEA: cross-repo contract test reaches the sibling server repo (vs 78-3 precedent)** → ✓ ACCEPTED by Reviewer: sound — a wire-contract test inherently must compare both live sides; 78-3's concern was a doc obligation, not a contract test. The `importlib` isolation load is correct (server module is pydantic+stdlib only) and ran green in preflight.
- **TEA: missing server repo is a hard FAILURE, not a pytest skip** → ✓ ACCEPTED by Reviewer: correct and load-bearing — a skipped contract test is a silent fallback that stops holding the seam (exactly the epic's defect class). Verified `FileNotFoundError`/`ImportError` raised loudly, no `pytest.skip`.
- **TEA: scope expansion — tests force removal of dead routing/R2 strings** → ✓ ACCEPTED by Reviewer: agrees — the invariant guards are meaningful (green now, RED on partial removal) and enforce the No-Silent-Fallbacks completeness the story needs.
- **TEA: updated existing tests encoding the old contract** → ✓ ACCEPTED by Reviewer: necessary test maintenance — contradictory old/new assertions would block GREEN; TEA correctly owns the test edits. Noted one resulting weak assertion (`test_stage_cue_accepts_camera`, Low, non-blocking) — see assessment finding table.
- **UNDOCUMENTED — none material.** The camera type-contract at `RenderTarget` (Medium) is a *pre-existing* boundary, not a spec deviation introduced by this diff (the call sites are unchanged); captured as a non-blocking Delivery Finding rather than a deviation. The two stale docstring counts are accuracy nits, not spec deviations.