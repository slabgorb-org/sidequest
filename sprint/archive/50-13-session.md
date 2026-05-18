---
story_id: 50-13
jira_key: null
epic: 50
workflow: tdd
---
# Story 50-13: Disposition: genre-configurable thresholds

## Story Details
- **ID:** 50-13
- **Epic:** 50 (Pingpong-archive triage and dropped-work cleanup)
- **Jira Key:** None (personal project)
- **Workflow:** tdd
- **Stack Parent:** 50-10 (dependency)

## Story Description

Make the disposition→attitude numeric thresholds genre-pack-configurable. Currently `disposition.py:78-82` hardcodes `>10⇒friendly / <-10⇒hostile / else neutral`. Add a genre-pack model field (default ±10) read at pack load time so a pack can widen/narrow the bands.

**CRITICAL CONSTRAINT:** The Attitude enum is the THREE-tier lowercase wire contract `friendly/neutral/hostile` (sidequest-server/sidequest/game/disposition.py:41-54, locked by tests/game/test_disposition_attitude_enum.py). This story changes the numeric BOUNDARIES only — it does NOT add/rename bands and there is NO five-tier capitalised set.

**Change vector:** disposition module + genre-pack model + pack loader (repos: server, content). Story 50-12 already wired `Disposition.attitude()` into the narrator roster, so corrected thresholds flow through with zero roster rework.

## Acceptance Criteria

- **AC-1:** Genre-pack model exposes a disposition-threshold field (`friendly_at` / `hostile_at` or equivalent) defaulting to +10 / -10, preserving exact current behavior (>10 friendly, <-10 hostile, else neutral) when unset.
- **AC-2:** Threshold is read at pack load time and used by `Disposition.attitude()` derivation; band labels remain the fixed 3-tier `Attitude` enum (friendly/neutral/hostile) — only the numeric cut points change.
- **AC-3:** A pack overriding the threshold (e.g. ±5) reclassifies dispositions at the new boundary; default/unset packs are byte-identical to pre-50-13 behavior (regression-locked).
- **AC-4:** No silent fallback — a malformed/out-of-range threshold in pack YAML fails loudly at load, not silently clamped.
- **AC-5:** OTEL/dashboard continuity — `SPAN_DISPOSITION_SHIFT` before/after attitude (shipped by 50-11) still reflects the configured thresholds; no new narrator-facing numeric leak (ADR-104/105).

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-05-18T08:48:37Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-18 | 2026-05-18T08:11:21Z | 8h 11m |
| red | 2026-05-18T08:11:21Z | 2026-05-18T08:22:30Z | 11m 9s |
| green | 2026-05-18T08:22:30Z | 2026-05-18T08:34:42Z | 12m 12s |
| spec-check | 2026-05-18T08:34:42Z | 2026-05-18T08:37:10Z | 2m 28s |
| verify | 2026-05-18T08:37:10Z | 2026-05-18T08:40:45Z | 3m 35s |
| review | 2026-05-18T08:40:45Z | 2026-05-18T08:46:39Z | 5m 54s |
| spec-reconcile | 2026-05-18T08:46:39Z | 2026-05-18T08:48:37Z | 1m 58s |
| finish | 2026-05-18T08:48:37Z | - | - |

## Sm Assessment

**Routing:** setup → red (TEA / Radar). Phased TDD, repos `server` + `content`, no Jira (personal project, sprint YAML only).

**Why this story now:** p2, 3pts, fits Sprint 3's state-hygiene/post-port-cleanup theme. Sibling 50-12 just merged and already wired `Disposition.attitude()` into the narrator roster — corrected thresholds flow through with zero roster rework. The 50-12 work also exposed the failure mode this spec is hardened against.

**Load-bearing constraint for the RED phase (do not let this drift):**
- The `Attitude` enum is the THREE-tier lowercase wire contract `friendly/neutral/hostile` — `sidequest-server/sidequest/game/disposition.py:41-54`, locked by `tests/game/test_disposition_attitude_enum.py`.
- This story moves the NUMERIC BOUNDARIES only (default ±10 → genre-pack-configurable, read at pack load time). It does NOT add or rename bands.
- There is NO five-tier capitalised set. Do **not** reintroduce the fictional `Literal["Hostile","Guarded","Neutral","Trusting","Allied"]` that a prior sm-setup invented for 50-12. Any test that asserts a five-tier or capitalised enum is wrong by construction — write tests against the three-tier contract and the numeric cut points.

**Test surface for TEA:** failing tests covering AC-1..AC-5. Key edges: default/unset pack is byte-identical to pre-50-13 behavior (regression-lock AC-3); malformed/out-of-range threshold fails loudly at load, no silent clamp (AC-4, No Silent Fallbacks principle); `SPAN_DISPOSITION_SHIFT` OTEL continuity with configured thresholds and no narrator-facing numeric leak (AC-5, ADR-104/105).

**Banned patterns (carry into every downstream agent):** never `git stash`; never run tests on a prior commit to "prove" a failure was pre-existing.

**Branch hygiene:** both subrepos already on `feat/50-13-genre-configurable-thresholds`; `sidequest-content` uses gitflow (base `develop`), `sidequest-server` base `develop`. Branch before first commit anywhere — the commit hook scans all subrepos.

## TEA Assessment

**Phase:** finish (test design)
**Tests Required:** Yes
**Reason:** New behavior (genre-configurable disposition→attitude thresholds) — not a chore-bypass category.

**Test Files:**
- `sidequest-server/tests/game/test_disposition_genre_thresholds.py` — unit + model: `AttitudeThresholds` defaults/validation, `RulesConfig.disposition_thresholds`, byte-identical default boundary table (regression-lock vs pre-50-13), narrowed/widened/asymmetric reclassification, cross-pack no-leak via `reset`, loud-fail on inverted/equal/non-int/unknown-key, `__all__` export, `attitude()` no-required-arg callsite-stability guard.
- `sidequest-server/tests/game/test_disposition_threshold_loader_wiring.py` — load-time wiring + OTEL: `load_genre_pack` applies declared thresholds; pack-without-block stays ±10; cross-pack default-load clears prior ±5 (multiplayer hazard); inverted thresholds → `GenreLoadError` at load; failed load does not half-apply config; SPAN_DISPOSITION_SHIFT reflects configured band (positive + negative) through the **unchanged** session.py callsite.

**Tests Written:** 26 tests covering AC-1..AC-5
**Status:** RED confirmed — collection ImportError (missing API: `AttitudeThresholds`, `DEFAULT_ATTITUDE_THRESHOLDS`, `configure_attitude_thresholds`, `reset_attitude_thresholds`, `RulesConfig.disposition_thresholds`). Expected RED for new-API TDD; no syntax/fixture/import-path bugs in the test files (testing-runner classified the failure as expected RED).

**Pinned API surface (architecture-forced, not invented):** Because `session.apply_world_patch` reconstructs `Disposition(before + delta)` from a bare int and calls `.attitude()` with no args, and the story + the 50-11 span comment explicitly forbid revisiting that callsite, a per-call `attitude(threshold)` parameter is infeasible. Therefore the configured thresholds MUST be process-level state in `sidequest.game.disposition`, set once at `load_genre_pack` time and read by the no-arg `Disposition.attitude()`. Dev may rename symbols but must preserve: (a) no required arg on `attitude()`, (b) default ±10 byte-identical, (c) load-time application + reset-on-default-pack, (d) loud-fail at model validation.

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| python #2 shared mutable state (cross-pack/MP leak) | `test_reset_restores_default_bands_after_a_configured_pack`, `test_reconfigure_overwrites_rather_than_accumulates`, `test_default_pack_load_clears_prior_pack_thresholds` | failing (RED) |
| python #10 import hygiene / `__all__` | `test_new_public_symbols_are_exported` | failing (RED) |
| python #11 input validation at parser boundary | `test_non_integer_threshold_is_rejected_not_coerced`, `test_unknown_threshold_key_is_rejected` | failing (RED) |
| python #6 test quality (self-check) | n/a — Phase C scan: 0 vacuous assertions in authored tests | pass |
| SOUL No Silent Fallbacks | `test_inverted_thresholds_raise_not_silently_swapped`, `test_equal_thresholds_raise_no_zero_width_neutral_band`, `test_inverted_thresholds_in_rules_yaml_fail_pack_load`, `test_failed_threshold_load_does_not_mutate_global_state` | failing (RED) |
| CLAUDE.md "Every Test Suite Needs a Wiring Test" | `test_loading_pack_with_thresholds_reconfigures_attitude`, `test_span_disposition_shift_uses_configured_band` | failing (RED) |
| ADR-020 three-tier contract (50-12 anti-trap) | `test_unconfigured_state_still_three_tier_only`, byte-identical boundary table | failing (RED) |
| OTEL continuity (AC-5, ADR-104/105) | `test_span_disposition_shift_uses_configured_band`, `test_span_no_crossing_when_configured_band_not_reached` | failing (RED) |

**Rules checked:** 4 of the applicable python lang-review rules (#2, #6, #10, #11) plus 3 project principles (No Silent Fallbacks, wiring test, three-tier contract) have test coverage. Checks #1/#3/#4/#5/#7/#8/#9/#12/#13/#14 are not exercised by this change vector (no exception handling, no logging, no file/resource I/O beyond the existing safe-yaml loader path, no async beyond the proven watcher scaffold, no deps).
**Self-check:** 0 vacuous tests found (all assertions are concrete value/raise checks).

**Handoff:** To Dev (Major Charles Emerson Winchester III) for GREEN — implement the module API + `RulesConfig.disposition_thresholds` + `load_genre_pack` wiring. Content-repo deliverable (a real pack opting into custom thresholds in its `rules.yaml`) is Dev's GREEN data work; RED tests deliberately use the synthetic `minimal_pack_factory` clone, never a live pack slug.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): No `sprint/context/context-story-50-13.md` (and no `context-epic-50.md`) was produced by SM setup; `pf validate context` passes globally but there is no story-specific context doc. Affects `sprint/context/` (epic 50 has zero context docs — sibling cleanup stories 50-9/13/21/22 will hit the same). Proceeded using the session file as spec (highest authority per spec-authority hierarchy; ACs + constraint were fully specified there). *Found by TEA during test design.*
- **Improvement** (non-blocking): `sidequest-content` has no test harness (pure data repo) — the content-side AC deliverable (a real pack declaring `disposition_thresholds`) cannot carry its own regression test. Coverage relies on the server loader test with a synthetic fixture pack. Affects `sidequest-content/` (consider a server-side parametrized "every live pack's rules.yaml parses" guard if real packs adopt the field). *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): RED verification only reached pytest *collection* (the API-missing ImportError fired before fixture resolution), which masked that the wiring suite — placed in `tests/game/` — referenced `minimal_pack_factory`, a fixture scoped to `tests/genre/conftest.py`. Surfaced only at GREEN. Affects `tests/game/` wiring suites and the RED-verification step (consider TEA confirming fixtures resolve even when the target API import fails, e.g. `pytest --collect-only` after stubbing imports, or placing cross-cutting fixtures at `tests/conftest.py` from the start). *Found by Dev during implementation.*
- No other upstream findings during implementation.

### TEA (verify)
- **Improvement** (non-blocking): The OTEL watcher-capture test scaffold (`_make_pc` / `_make_npc` / `_setup`(`_setup_watcher`) / `_wait_for_event`) is copy-pasted across 5+ test files — `tests/integration/test_disposition_otel_wiring.py`, `tests/integration/test_disposition_threshold_crossing.py`, `tests/integration/test_combat_otel_wiring.py`, `tests/game/test_disposition_call_site_migration.py`, and the new `tests/game/test_disposition_threshold_loader_wiring.py`. simplify-reuse flagged this high-confidence; the new file deliberately conformed to the dominant existing pattern for consistency. NOT consolidated under 50-13: the fix would touch 4 files outside this story's diff, one of which (`test_disposition_call_site_migration.py`) is in the `_CAVERNS_SUNDEN_DEPRECATED_TESTS` skip-list and therefore cannot be regression-verified. Affects `tests/` (recommend a dedicated test-hygiene story to extract the OTEL watcher scaffold into a shared `tests/conftest.py` helper across all consumers). *Found by TEA during test verification.*

### Reviewer (code review)
- **Improvement** (non-blocking): `Disposition.attitude()` reads a single process-global `_active_thresholds`. Cross-pack *sequential* isolation is tested and correct (`or DEFAULT` overwrite). But if the server process ever hosts two concurrent sessions on *different* genre packs, the last `load_genre_pack` wins for *both* — a session could derive NPC attitude (and emit a SPAN_DISPOSITION_SHIFT) using the wrong pack's bands. Not a regression (pre-50-13 was a hardcoded global ±10 with no per-pack variance) and not a real play pattern for this single-campaign personal game; the global is architecture-forced (the story forbade the only alternative — threading thresholds through the session.py callsite). Affects `sidequest/game/disposition.py` (revisit only if multi-pack concurrent hosting is ever added — would need per-session pack context, i.e. the deferred callsite refactor). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `AttitudeThresholds` is not `frozen`; `DEFAULT_ATTITUDE_THRESHOLDS` is a module singleton aliased into `_active_thresholds` by `reset_attitude_thresholds()`. No code mutates `.friendly_at`/`.hostile_at` today (verified: only reads at disposition.py:150/152, only whole-object reassignment at :119/:126) so there is no live bug, but a future in-place mutation of the active thresholds would silently corrupt the shared default for every subsequently-"reset" pack — the exact cross-pack-bleed class this story guards against. Affects `sidequest/game/disposition.py` (recommend `model_config = {"extra": "forbid", "frozen": True}` as defense-in-depth; non-blocking, latent-only). *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Threshold field pinned to `RulesConfig.disposition_thresholds`**
  - Spec source: .session/50-13-session.md, AC-1
  - Spec text: "Genre-pack model exposes a disposition-threshold field (`friendly_at` / `hostile_at` or equivalent)"
  - Implementation: Tests assert the field lives on `RulesConfig` as a typed `AttitudeThresholds | None` (default None), not elsewhere on the pack aggregate.
  - Rationale: AC-1 says "or equivalent" — TEA chose RulesConfig because rules.yaml is the rulebook and every other mechanical threshold (EdgeConfig, ResourceDeclaration, MetricDef) already lives there; keeps `extra="forbid"` parity. Dev may relocate but must keep the typed-model + None-default + load-wiring behavior.
  - Severity: minor
  - Forward impact: If Dev places the field elsewhere, the model-level tests need their target updated; the behavioral/loader/OTEL tests are location-agnostic.
- **`attitude()` thresholds pinned as process-level config, not a method parameter**
  - Spec source: .session/50-13-session.md, AC-2 + SM Assessment "do not let this drift" + session.py:~1190 50-11 span comment
  - Spec text: "Threshold is read at pack load time and used by `Disposition.attitude()` derivation" / callsite "must not be revisited"
  - Implementation: Tests pin `configure_attitude_thresholds()` / `reset_attitude_thresholds()` module functions + a no-required-arg `attitude()`, rather than `attitude(thresholds=...)`.
  - Rationale: `session.apply_world_patch` rebuilds `Disposition(before+delta)` from a bare int and calls `.attitude()` with no args; a parameter would force a forbidden callsite rework. Module-level read-only-after-load config is the only design consistent with the no-rework constraint AND the existing instance-independence guard.
  - Severity: minor
  - Forward impact: Constrains Dev's implementation shape (intentionally — this is architecture-forced). Symbol names are Dev's to choose; the behavior contract is fixed by the tests.

### Dev (implementation)
- **Content repo: no live pack given a custom `disposition_thresholds` block**
  - Spec source: .session/50-13-session.md, Change vector "(repos: server, content)"
  - Spec text: "Change vector is the disposition module + genre-pack model + pack loader (repos: server,content)"
  - Implementation: Server-only change. The capability is fully wired (model + loader + derivation), but no shipped pack's `rules.yaml` was given a non-default band. Opting in is author-chosen data.
  - Rationale: No test requires a live pack to adopt the field — TEA's RED suite deliberately uses the synthetic `minimal_pack_factory` clone (per the TEA handoff). Imposing a non-default attitude band on a shipped pack is an unrequested gameplay/balance change during a state-hygiene sprint and would alter NPC behavior for the playgroup with no balance mandate. Minimalist discipline + "don't change gameplay without being asked."
  - Severity: minor
  - Forward impact: A pack can adopt the block at any time with zero server rework (one-line YAML). No sibling story assumes a shipped pack carries custom thresholds. If a future balance decision wants a specific pack tuned, that is a content-only follow-up.
- **Shared test fixture relocated: `tests/genre/conftest.py` → `tests/conftest.py`**
  - Spec source: TEA Assessment + tests/game/test_disposition_threshold_loader_wiring.py
  - Spec text: "RED tests deliberately use the synthetic `minimal_pack_factory` clone"
  - Implementation: Moved `MinimalPack` + `_FIXTURE_PACK` + the `minimal_pack_factory` fixture to the top-level `tests/conftest.py` and deleted `tests/genre/conftest.py`; `_FIXTURE_PACK` path recomputed for the shallower file depth.
  - Rationale: pytest conftest fixtures are directory-scoped; the wiring suite TEA placed under `tests/game/` could not resolve a `tests/genre/`-scoped fixture (RED masked this — the API ImportError aborted collection before fixture resolution). A single top-level definition is the standard pytest idiom and avoids duplicating the fixture across two conftests.
  - Severity: minor
  - Forward impact: None functional — genre suite re-verified green; full server suite 6262 pass / 0 fail. Any test in any package can now use `minimal_pack_factory`.
- **Ruff auto-fix/format applied to TEA's two committed test files (cosmetic)**
  - Spec source: project quality rules (ruff clean before handoff) + the tests TEA wrote
  - Spec text: "Tests green, working tree clean" (dev-exit gate); ruff must pass
  - Implementation: `ruff --fix` + `ruff format` reordered imports, swapped one SIM300 Yoda-condition operand (`DEFAULT_ATTITUDE_THRESHOLDS == AttitudeThresholds()` → operands swapped), and re-wrapped long lines in both test files. No assertion, value, or test logic changed; re-verified GREEN post-format (56/56).
  - Rationale: The dev-exit gate requires a clean working tree and the project forbids shipping ruff violations; the swaps are semantically inert (equality is symmetric).
  - Severity: trivial
  - Forward impact: None — behavior identical, confirmed by post-format test run.

### Reviewer (audit)
- **TEA: Threshold field pinned to `RulesConfig.disposition_thresholds`** → ✓ ACCEPTED by Reviewer: rules.yaml is the rulebook; `EdgeConfig`/`ResourceDeclaration`/`MetricDef` set the precedent. `extra="forbid"` parity verified (disposition.py:87). Sound.
- **TEA: `attitude()` thresholds pinned as process-level config, not a method parameter** → ✓ ACCEPTED by Reviewer: architecture-forced and independently confirmed — `session.apply_world_patch` rebuilds `Disposition(before+delta)` from a bare int and calls `.attitude()` with no args; a parameter is infeasible without the forbidden callsite rework. Architect blessed; the only viable shape. (Residual concurrency limitation recorded as a non-blocking finding, not a deviation defect.)
- **Dev: Content repo — no live pack given a custom block** → ✓ ACCEPTED by Reviewer: no test mandates a shipped-pack opt-in; imposing a non-default band mid-hygiene-sprint would be an unrequested balance change. Capability is fully wired; opt-in is one line of author YAML. Correct minimalist call.
- **Dev: Shared test fixture relocated `tests/genre/conftest.py` → `tests/conftest.py`** → ✓ ACCEPTED by Reviewer: standard pytest idiom for cross-package fixtures; single definition (no duplication); genre suite + full 6262 suite re-verified green; `_FIXTURE_PACK` path correctly recomputed for the shallower depth.
- **Dev: Ruff auto-fix/format on TEA's two test files (cosmetic)** → ✓ ACCEPTED by Reviewer: import-sort + SIM300 operand swap + line-wrap are semantically inert; re-verified GREEN post-format. Working tree clean.
- **Architect (spec-check) AC-4 "out-of-range" magnitude not bounded → resolution C (clarify spec)** → ✓ ACCEPTED by Reviewer: concur. A deliberately unreachable band is valid Genre Truth ("Crunch in the Genre"); `friendly_at=99` is a legitimate hard-to-befriend pack. The genuine error class (inverted/zero-width/non-int/unknown-key) DOES fail loudly. Magnitude is a tuning knob, not an authoring error — no code change warranted.

**No undocumented spec deviations found.** The implementation matches the session-file spec (highest authority; no `context-story-50-13.md` exists). All five logged deviations are accepted; the lone spec ambiguity (AC-4 magnitude) was correctly resolved by the Architect as a clarification.

### Architect (reconcile)

**Existing-entry audit:** All five in-flight deviations (TEA ×2, Dev ×3) verified against code at reconcile — every entry has all 6 fields, spec-source paths resolve (`.session/50-13-session.md` is the authoritative spec; no `context-story-50-13.md`/`context-epic-50.md` exist — confirmed), quoted spec text is accurate, implementation descriptions match the diff, and forward-impact claims are correct (sibling epic-50 stories 50-9 mood-aliases / 50-21 & 50-22 scene-harness-hydration are unrelated subsystems — none assume disposition thresholds or a shipped-pack opt-in; content repo verified genuinely untouched by 50-13). No corrections or missing-field annotations required. Reviewer stamped all five ACCEPTED.

**AC accountability:** No ACs deferred or descoped — AC-1..AC-5 all DONE (Dev assessment, Reviewer-confirmed). Deferral-justification step is a no-op.

**Missed deviation formalized** (adjudicated by Architect at spec-check; existed only as Assessment prose — promoted to a self-contained manifest entry so the audit artifact stands alone):

- **AC-4 "out-of-range" threshold is not magnitude-bounded against the ±100 disposition clamp**
  - Spec source: `.session/50-13-session.md`, AC-4
  - Spec text: "No silent fallback — a malformed/out-of-range threshold in pack YAML fails loudly at load, not silently clamped."
  - Implementation: `AttitudeThresholds._validate_strict_ordering` (sidequest/game/disposition.py:93) rejects only the inverted / zero-width ordering case (`not hostile_at < friendly_at` → `ValueError` → `GenreLoadError`). It does NOT bound threshold magnitude; `friendly_at: 500` (beyond the `Disposition` ±100 clamp, making "friendly" unreachable) validates and loads without error.
  - Rationale: Adjudicated at spec-check as resolution **C — clarify spec**, not a code fix. A deliberately unreachable band is legitimate Genre Truth (a grimdark "no one is ever truly your friend" pack); `friendly_at=99` is a valid hard-to-befriend tuning. Threshold magnitude is a genre design knob ("Crunch in the Genre"), not an authoring error — a hard magnitude bound would wrongly forbid valid pack design. "Out-of-range" in AC-4 is satisfied by the ordering rejection plus `extra="forbid"` (typo'd key) and strict int typing (non-int); the genuine error class fails loudly. Reviewer concurred and stamped ACCEPTED.
  - Severity: minor
  - Forward impact: None for shipped behavior. If a future story wants packs prevented from authoring an unreachable band, that is a new explicit AC + a magnitude validator — not rework of 50-13. No sibling story depends on magnitude bounding.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed (sidequest-server):**
- `sidequest/game/disposition.py` — `AttitudeThresholds` (pydantic, `extra=forbid`, strict `hostile_at < friendly_at` validator), `DEFAULT_ATTITUDE_THRESHOLDS`, module-level `_active_thresholds` + `configure_attitude_thresholds()` / `reset_attitude_thresholds()`; `Disposition.attitude()` reads the module config (no signature change); `__all__` updated; module docstring corrected (boundaries are now configurable, default ±10).
- `sidequest/genre/models/rules.py` — `RulesConfig.disposition_thresholds: AttitudeThresholds | None = None` + import from `sidequest.game.disposition` (no circular import — disposition has no genre/game-heavy deps; full suite confirms).
- `sidequest/genre/loader.py` — top-level import of `DEFAULT_ATTITUDE_THRESHOLDS` / `configure_attitude_thresholds`; `load_genre_pack` calls `configure_attitude_thresholds(rules.disposition_thresholds or DEFAULT_ATTITUDE_THRESHOLDS)` on the fully-assembled success path (after the genre-pack-loaded watcher event). Malformed thresholds already fail loudly as `GenreLoadError` at `_load_rules_config` (line ~203) before any config is applied — failed loads never half-apply.
- `tests/conftest.py` — relocated `MinimalPack` / `_FIXTURE_PACK` / `minimal_pack_factory` here (see deviation).
- `tests/genre/conftest.py` — deleted (fixture relocated; single definition, no duplication).
- `tests/game/test_disposition_genre_thresholds.py`, `tests/game/test_disposition_threshold_loader_wiring.py` — ruff cosmetic reformat only (see deviation).

**Content repo:** No changes — capability fully wired server-side; a pack opting in is author data (see deviation; not test-mandated, avoids unrequested balance change).

**Tests:** 26/26 new tests GREEN. Pre-50-13 ±10 enum-lock suite still GREEN (byte-identical default). **Full server suite: 6262 passed / 0 failed / 400 skipped (pre-marked).** Ruff check + format clean on all changed files.

**AC coverage:** AC-1 (model field + ±10 default + RulesConfig None) ✓ · AC-2 (load-time wiring → `attitude()` derivation, no callsite change) ✓ · AC-3 (override reclassifies both directions; default/unset byte-identical; cross-pack no-leak) ✓ · AC-4 (inverted/equal/non-int/unknown-key fail loudly as ValidationError/GenreLoadError, no silent clamp, no partial apply) ✓ · AC-5 (SPAN_DISPOSITION_SHIFT reflects configured band through the unchanged session.py callsite — positive and negative) ✓.

**Self-review (judgment checks):** Wired end-to-end (loader → module config → `attitude()` → live OTEL span, proven by the wiring/OTEL tests, not just unit isolation) ✓ · follows project patterns (pydantic `extra=forbid` + `model_validator` like `EdgeConfig`/`ResourceDeclaration`) ✓ · all ACs met ✓ · loud-fail error handling per No Silent Fallbacks ✓ · no debug code · working tree clean · correct branch (`feat/50-13-genre-configurable-thresholds`, base `develop`, pushed).

**Branch:** `feat/50-13-genre-configurable-thresholds` (sidequest-server, pushed, tracking origin) — commit `81398b2`.

**Handoff:** To verify phase (Radar O'Reilly — TEA simplify + quality-pass).

## Architect Assessment (spec-check)

**Spec Alignment:** Drift detected (1 minor, spec-clarity only — no code change required)
**Mismatches Found:** 1
**Structural gate:** spec-check PASSED (AC coverage present in Dev Assessment, implementation complete, TEA + Dev deviation subsections well-formed).

**AC-by-AC substance review** (spec source = session file; no `context-story-50-13.md` exists, session is highest authority):
- **AC-1** Aligned. `RulesConfig.disposition_thresholds: AttitudeThresholds | None = None`; `AttitudeThresholds.friendly_at=10`/`hostile_at=-10`. Field names match the AC's literal preferred example; `None` → loader applies `DEFAULT_ATTITUDE_THRESHOLDS` (±10). Byte-identical default confirmed by the still-green enum-lock suite.
- **AC-2** Aligned. `load_genre_pack` applies the pack's bands via `configure_attitude_thresholds(...)` on the assembled success path; `Disposition.attitude()` reads `_active_thresholds` and still returns the locked 3-tier `Attitude` enum — only cut points move. The module-level (not method-parameter) design is architecture-*forced* by the no-callsite-rework constraint (session.py rebuilds `Disposition(before+delta)` from a bare int); the chosen shape is the only one consistent with that constraint and is sound.
- **AC-3** Aligned. Override reclassifies both directions; `or DEFAULT` on every load overwrites a prior pack's band (cross-pack / multiplayer no-leak) rather than accumulating module state — the correct fix for the python-review #2 shared-state hazard.
- **AC-4** Minor spec ambiguity (see mismatch below). The genuine error class (inverted / zero-width ordering, unknown key, non-int) fails loudly as `ValidationError` → `GenreLoadError` *before* `configure_attitude_thresholds` runs, so a failed load never half-applies. This is correct and matches No Silent Fallbacks.
- **AC-5** Aligned. SPAN_DISPOSITION_SHIFT callsite in `session.apply_world_patch` is unchanged; it reads `Disposition.attitude()` which now reflects the configured band (verified positive + negative by the wiring suite). No new numeric field on the span, thresholds are server-internal config and never serialized toward the narrator — no ADR-104/105 leak.

**Mismatch:**
- **AC-4 "out-of-range" threshold not magnitude-bounded** (Ambiguous spec — Behavioral, Minor)
  - Spec: AC-4 — "a malformed/**out-of-range** threshold in pack YAML fails loudly at load, not silently clamped."
  - Code: `AttitudeThresholds._validate_strict_ordering` enforces `hostile_at < friendly_at` (rejects inverted and zero-width). It does NOT bound threshold magnitude against the `Disposition` ±100 clamp. A pack could set `friendly_at: 500`, making "friendly" unreachable, with no loud failure.
  - Recommendation: **C — clarify spec.** Code is architecturally correct and should NOT change. `friendly_at=99` is a legitimate "hard to befriend" pack and a deliberately unreachable band is valid Genre Truth for a grimdark world — magnitude is a genre tuning knob ("Crunch in the Genre"), not an authoring error, so a hard magnitude bound would wrongly forbid valid pack design. "Out-of-range" in AC-4 is satisfied by the inverted/zero-width rejection. This is recorded for traceability; no hand-back to Dev.

**Decision:** Proceed to verify. No code change required (sole mismatch resolved as spec-clarification C). The implementation is architecturally sound — module-level config is forced by the callsite constraint, the validator follows the established `EdgeConfig`/`ResourceDeclaration` pattern, loud-fail ordering is correct, and the fixture-relocation / content-untouched deviations are well-reasoned and already logged.

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed (Dev's full server suite: 6262 passed / 0 failed / 400 pre-marked skips; spec-check made zero code edits)

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 6 (`disposition.py`, `loader.py`, `rules.py`, `tests/conftest.py`, the two new test files; deleted `tests/genre/conftest.py` excluded — no file to analyze)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 4 high + 1 low | OTEL watcher-capture scaffold (`_make_pc`/`_make_npc`/`_setup`/`_wait_for_event`) duplicated across 5+ test files; low: `_patch_rules_yaml` could become a `MinimalPack` method |
| simplify-quality | clean | Naming, dead code, type safety, wiring, OTEL, test isolation all pass; pydantic pattern matches `EdgeConfig`/`ResourceDeclaration` |
| simplify-efficiency | clean | No over-engineering; module-global is architecture-forced; test edge coverage is AC-required, not bloat |

**Applied:** 0 high-confidence fixes
**Flagged for Review:** 0 medium-confidence findings
**Noted:** 1 low-confidence observation (`_patch_rules_yaml` → `MinimalPack` method — single-use, fine test-local; not actioned)
**Reverted:** 0

**Triage rationale (why the 4 high-confidence reuse findings were NOT auto-applied):** The flagged duplication is *pre-existing and systemic* — the OTEL watcher scaffold is copy-pasted across `test_disposition_otel_wiring.py`, `test_disposition_threshold_crossing.py`, `test_combat_otel_wiring.py`, and `test_disposition_call_site_migration.py`. The new `test_disposition_threshold_loader_wiring.py` deliberately conformed to that dominant pattern (consistency with the prevailing convention until a deliberate consolidation). The simplify-reuse *fix* (extract to `tests/conftest.py`, consolidate all consumers) would (a) touch 4 files outside the 50-13 diff — scope creep on a 3-pt story during verify — and (b) modify `test_disposition_call_site_migration.py`, which is in `_CAVERNS_SUNDEN_DEPRECATED_TESTS` and is skipped, so a change there could not be regression-verified by `pf check`. Auto-applying a multi-file, partially-unverifiable refactor in the verify phase fails the minimalist-discipline and blast-radius tests. Recorded as a non-blocking Delivery Finding recommending a dedicated test-hygiene story. simplify-reuse's verdict is correct *as future work*; declining it *here* is the correct scope call.

**Overall:** simplify: clean (no in-scope actionable findings; sole systemic duplication is pre-existing and deferred to a dedicated story)

**Quality Checks:** Full server suite GREEN at Dev green (6262/0); no code changed in spec-check or verify (zero simplify edits applied), so no regression surface introduced post-green. Ruff check + format already clean on all changed files (verified at Dev exit).

**Handoff:** To Reviewer (Colonel Sherman Potter) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 smells; 588 pass / 0 fail / 49 known-skip; ruff+pyright clean | N/A (mechanically clean) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — domain assessed by Reviewer (see Devil's Advocate + Rule Compliance) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — domain assessed by Reviewer (loud-fail path verified) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — domain assessed by Reviewer (TEA verify simplify already covered; assertions concrete) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — domain assessed by Reviewer (docstrings accurate, stale ±10 docstring fixed) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — domain assessed by Reviewer (typed pydantic model, no stringly-typed API) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings — domain assessed by Reviewer (author-controlled YAML, safe_load, no narrator leak) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — domain covered by TEA verify simplify trio (clean + 1 deferred systemic dup) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — Reviewer did the exhaustive rule-by-rule enumeration (see Rule Compliance) |

**All received:** Yes (1 enabled subagent returned; 8 disabled via `workflow.reviewer_subagents`, pre-filled and self-assessed)
**Total findings:** 0 confirmed blocking, 0 dismissed, 2 LOW deferred (recorded as non-blocking Delivery Findings)

## Reviewer Assessment

**Verdict:** APPROVED

### Rule Compliance (python lang-review checklist, exhaustive)

| # | Rule | Enumerated instances | Verdict |
|---|------|----------------------|---------|
| 1 | Silent exception swallowing | No new try/except in diff; validator `raise ValueError`; `_load_rules_config` pre-existing `except Exception → GenreLoadError` (loud) | Compliant |
| 2 | Mutable defaults / shared mutable state | `AttitudeThresholds` int defaults (immutable); `_active_thresholds` module global is whole-object *reassigned* (disposition.py:119,126), never in-place mutated; read-only at :150/:152. Latent footgun (non-frozen singleton) → LOW finding, no live violation | Compliant (1 LOW defensive note) |
| 3 | Type annotation gaps at boundaries | `configure_attitude_thresholds(thresholds: AttitudeThresholds) -> None`, `reset_attitude_thresholds() -> None`, `_validate_strict_ordering(self) -> AttitudeThresholds`, `disposition_thresholds: AttitudeThresholds \| None` — all annotated | Compliant |
| 4 | Logging coverage/correctness | Boundary error path raises (No-Silent-Fallback) rather than logs; consistent with loader's existing GenreLoadError pattern; no logging module touched | Compliant |
| 5 | Path handling | `tests/conftest.py` uses `Path(__file__).resolve().parent`, `open(..., encoding="utf-8")` | Compliant |
| 6 | Test quality | Concrete value/`pytest.raises` assertions; `inspect`-based signature guard is meaningful; TEA Phase-C self-check + preflight = 0 vacuous | Compliant |
| 7 | Resource leaks | All file I/O via `with ...open()` context managers | Compliant |
| 8 | Unsafe deserialization | `yaml.safe_load` (not `yaml.load`); pydantic `model_validate` on parsed dict | Compliant |
| 9 | Async pitfalls | `await asyncio.sleep(0)` at wiring test :295/:331 — yield-to-loop for span flush, established OTEL-test idiom (mirrors `test_disposition_call_site_migration.py`); test-only | Compliant (idiomatic) |
| 10 | Import hygiene | `__all__` updated with all 4 new public symbols; `rules.py`→`disposition` import has no cycle (disposition imports only pydantic/enum/typing; full 6262 suite confirms); no star imports | Compliant |
| 11 | Input validation at boundaries | Pack YAML boundary: `AttitudeThresholds` (extra=forbid, strict ordering, int typing) → `_load_rules_config` wraps in `GenreLoadError` | Compliant |
| 12 | Dependency hygiene | No dependency changes | N/A |
| 13 | Fix-introduced regressions | Ruff auto-fix re-verified GREEN (56/56) + full 6262 | Compliant |
| 14 | State cleanup ordering w/ fallible side effects | `configure_attitude_thresholds` runs only on the fully-assembled success path; malformed block raises `GenreLoadError` at `_load_rules_config` **before** configure is reached → a failed load never half-applies. Verified ordering correct | Compliant (exemplary) |

### Observations

- `[VERIFIED]` Loud-fail ordering correct — `_load_rules_config` (loader.py:203) raises `GenreLoadError` on bad `disposition_thresholds` **before** `configure_attitude_thresholds` (loader.py:~1206); `test_failed_threshold_load_does_not_mutate_global_state` proves no partial apply. Complies with SOUL No-Silent-Fallbacks.
- `[VERIFIED]` Byte-identical default — `attitude()` strict `> friendly_at` / `< hostile_at` with defaults 10/-10 reproduces pre-50-13 exactly; enum-lock suite `test_disposition_attitude_enum.py` still GREEN. Evidence: disposition.py:150-153, preflight 588/0.
- `[VERIFIED]` Wiring is real (not test-only) — `loader.py` is a non-test consumer of `configure_attitude_thresholds`; end-to-end path proven by `test_span_disposition_shift_uses_configured_band`. Satisfies CLAUDE.md "verify wiring not just existence".
- `[VERIFIED]` `or DEFAULT` is safe — pydantic `BaseModel` instances are always truthy (no `__bool__`/`__len__`), so `rules.disposition_thresholds or DEFAULT` correctly means "None → default", never a falsy-valid-model bug.
- `[LOW]` Process-global precludes per-session pack isolation under concurrent multi-pack hosting (disposition.py:110) — architecture-forced, Architect-accepted, not a current play pattern; recorded as non-blocking finding.
- `[LOW]` `AttitudeThresholds` not `frozen`; DEFAULT singleton aliased by `reset` (disposition.py:108-110,126) — latent only (no mutation path today); recorded as non-blocking finding recommending `frozen=True`.
- `[VERIFIED]` Data flow traced: rules.yaml `disposition_thresholds` → `_load_rules_config` (validate/raise) → `RulesConfig.disposition_thresholds` (typed) → `load_genre_pack` → `configure_attitude_thresholds(... or DEFAULT)` → `_active_thresholds` → `Disposition.attitude()` → `Attitude` → SPAN_DISPOSITION_SHIFT (session.py unchanged) → GM panel. Clean, OTEL-visible, no narrator-facing numeric leak (AC-5).

### Devil's Advocate

Arguing this code is broken: A malicious or careless **pack author** sets `friendly_at: 100000000` — the model accepts it, "friendly" becomes unreachable, and no error fires. *Counter:* the Architect adjudicated this as legitimate Genre Truth (a grimdark "no one is ever your friend" pack) and the genuine error class (inverted/zero-width/typo/non-int) *does* fail loudly; "out-of-range" is satisfied by the ordering rejection. Accepted, not a defect. A **confused operator** runs two campaigns on different packs in one server process: the process-global `_active_thresholds` means the second `load_genre_pack` silently rebinds attitude derivation for the first session's NPCs, and the OTEL span — the project's designated lie detector — would confidently report an attitude computed from the wrong pack's bands. This is the sharpest concern: it inverts "OTEL catches the lie" into "OTEL emits the lie." *Counter:* it is not a regression (pre-50-13 was a single hardcoded global with zero per-pack variance, so no isolation ever existed to break), the global is *architecture-forced* (the story explicitly forbade the only alternative — threading a threshold through the no-arg `session.apply_world_patch` callsite), the Architect formally accepted the design, and the actual audience is one playgroup running one campaign at a time (not concurrent multi-pack). A **stressed filesystem / unexpected YAML**: a typo'd key is caught by `extra="forbid"` (loud); a non-int by pydantic; a partial/corrupt rules.yaml by the pre-existing `_load_rules_config` `GenreLoadError`. A **future maintainer** mutates `pack.rules.disposition_thresholds.friendly_at` in place: because the model is not frozen and the no-block path aliases the shared DEFAULT singleton, that would poison every subsequently-"reset" pack — precisely the cross-pack bleed AC-3 guards against. No such mutation exists today (grep-verified: only reads + whole-object reassignment), so it is latent, but it is a real sharp edge. Both sharp edges are recorded as non-blocking Delivery Findings with concrete remediation (per-session context if multi-pack hosting is added; `frozen=True` for defense-in-depth). Neither manifests in the shipped behavior for the actual audience; neither is a regression; both are architecture-forced or latent-only. Verdict stands: APPROVED with two LOW non-blocking findings — honest about the sharp edges, not over-rejecting an architecture-forced, Architect-blessed, fully-tested 3-pt change.

**Data flow traced:** pack rules.yaml → `_load_rules_config` (validates, raises `GenreLoadError` on malformed) → typed `RulesConfig.disposition_thresholds` → `load_genre_pack` success path → `configure_attitude_thresholds(... or DEFAULT_ATTITUDE_THRESHOLDS)` → module `_active_thresholds` → `Disposition.attitude()` → `Attitude` enum → unchanged `SPAN_DISPOSITION_SHIFT` callsite → GM panel. Safe: malformed input fails loudly before any state change; default path byte-identical to pre-50-13.

**Pattern observed:** pydantic `extra="forbid"` + `@model_validator(mode="after")` validator — matches the established `EdgeConfig`/`ResourceDeclaration`/`MetricDef` precedent in `sidequest/genre/models/rules.py`.

**Error handling:** Loud-fail at the parser boundary — `AttitudeThresholds._validate_strict_ordering` (disposition.py:93) raises `ValueError` → wrapped to `GenreLoadError` at `loader.py:203`, before `configure_attitude_thresholds` at `loader.py:~1206`. No silent fallback, no partial apply (proven by `test_failed_threshold_load_does_not_mutate_global_state`).

**No Critical/High findings. 2 LOW (non-blocking, recorded as Delivery Findings). All 5 deviations + the Architect AC-4 clarification stamped ACCEPTED.**

**Handoff:** To SM (Hawkeye Pierce) for finish-story.