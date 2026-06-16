---
story_id: "122-2"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 122-2: Relocate pure combat-rules helpers (find_confrontation_def, resolve_damage_spec) out of server/dispatch into game/ruleset; drop lazy imports

## Story Details
- **ID:** 122-2
- **Jira Key:** (none — Jira disabled)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-16T00:48:26Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-16T00:20:14Z | 2026-06-16T00:22:09Z | 1m 55s |
| red | 2026-06-16T00:22:09Z | 2026-06-16T00:30:44Z | 8m 35s |
| green | 2026-06-16T00:30:44Z | 2026-06-16T00:41:40Z | 10m 56s |
| review | 2026-06-16T00:41:40Z | 2026-06-16T00:48:26Z | 6m 46s |
| finish | 2026-06-16T00:48:26Z | - | - |

## Sm Assessment

**Story selected:** 122-2 — relocate pure combat-rules helpers (`find_confrontation_def`, `resolve_damage_spec_from_beat_and_actor`) out of `sidequest/server/dispatch/` UP into `sidequest/game/ruleset/`, dropping the lazy function-local imports. ADR-147 (Honest Layering, epic 122).

**Why now / sequencing:** This was a deliberate pivot. The user first selected 122-5 (the enforcing CI guard), but that story's own title says "lands last + enforcing." I verified the codebase still has **5 live domain→server upward imports** — exactly the violations the relocation siblings remove — so an enforcing guard added now would turn CI red immediately. We pivoted to work the epic in its lawful order. 122-2 is the highest-priority relocation (p2) and clears **2 of the 5** violations:
- `game/ruleset/without_number.py:141` + `:275` (lazy imports of both helpers from `server.dispatch.*`)
- `game/ruleset/native.py:21-22` (top-level imports of both from `server.dispatch.*`)

Remaining violations are owned by siblings: 122-3 (`interior/dispatch.py` → `server.rest`), 122-4 (`orbital/intent.py` → `server.session.Session`), plus an unowned `game/projection/validator.py` → `server.session_handler` import noted for the epic. 122-5 (the guard) lands clean only after 2/3/4 complete.

**Workflow:** tdd (phased). This is a `refactor` — characterization tests should pin current behavior of both helpers before the move, then the relocation keeps them green.

**Acceptance criteria for RED phase to encode:**
- Both helpers physically moved into `sidequest/game/ruleset/` (a module that is pure ruleset logic, no server dependency)
- All callers updated (server/dispatch consumers, `native.py`, `without_number.py`)
- Lazy/function-local imports in `without_number.py` dropped for module-level imports
- No `sidequest.game.* → sidequest.server.*` import remains for these two symbols
- Existing combat/confrontation/damage tests still green

**Handoff:** RED phase → Argus Panoptes (TEA). Session, story context, and branch `feat/122-2-relocate-combat-rules-helpers` are in place.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Behavior-preserving relocation refactor — the RED markers are structural (the upward import edges must vanish); a green behavior net pins combat resolution so the move can't silently change it.

**Test Files:**
- `tests/game/ruleset/test_122_2_combat_rules_relocation.py` — 13 tests (2 RED layering markers, 1 transitive-dependency guard, 10 behavior characterization)

**Tests Written:** 13 tests
**Status:** RED confirmed (2 FAILED as designed, 11 PASSED) via testing-runner, run `122-2-tea-red`. No collection/construction errors.

### Test Map

| Test | Layer | Now | After move | Encodes |
|------|-------|-----|-----------|---------|
| `test_native_module_imports_nothing_from_server` | layering (AST) | **FAIL** | pass | native.py drops the upward edge (lines 21-22) |
| `test_without_number_module_imports_nothing_from_server` | layering (AST) | **FAIL** | pass | without_number.py drops the *lazy* upward edge (lines 141, 275) |
| `test_no_game_tier_module_imports_inventory_resolve_from_server` | transitive guard (AST) | pass | pass* | *only stays green if Dev relocates `resolve_inventory` too (ADR-147 Move #1 — see blocking finding) |
| `test_find_confrontation_*` (×4, incl. native+wwn params) | behavior (seam) | pass | pass | exact match / miss / first-on-duplicate / empty — via `RulesetModule.find_confrontation` |
| `test_resolve_damage_*` (×4) | behavior (seam) | pass | pass | priority 1 (override) / 2 (weapon) / 4 (unarmed) / none — via `RulesetModule.resolve_damage` |

### Rule Coverage

| Rule (python.md) | Test(s) | Status |
|------|---------|--------|
| #10 import hygiene (no circular / upward imports) | `test_native_module_imports_nothing_from_server`, `test_without_number_module_imports_nothing_from_server`, `test_no_game_tier_module_imports_inventory_resolve_from_server` | RED / RED / green |
| #6 test quality (meaningful assertions, no vacuous) | self-checked — every test asserts a concrete value (`.dice`, `.confrontation_type`, identity, `is None`); no `assert True` / bare-truthy | pass |

**Rules checked:** import-hygiene (#10) and test-quality (#6) are the applicable lang-review rules for a relocation refactor; the rest (#1 exceptions, #5 paths, #7 resources, #8 deserialization, #9 async, #11 input-validation) target runtime behavior not exercised by a pure-move. The CLAUDE.md "No Source-Text Wiring Tests" rule drove the AST (structural) choice over `read_text()` regex.
**Self-check:** 0 vacuous tests.

**Wiring test:** the behavior tests exercise the relocated helpers through their *real consumers* (`NativeRulesetModule` + a WN sibling resolved via `get_ruleset_module`), satisfying "every test suite needs a wiring test" — they prove consumer→helper wiring survives the move, not just that the function exists.

**Handoff:** To Hephaestus the Smith (Dev) for GREEN. **Read the blocking Delivery Finding first** — the `resolve_inventory` transitive dependency must relocate with the damage helper, or the new module re-opens the upward edge (and 122-5's guard will later fail on it).

## Dev Assessment

**Status:** GREEN — all 13 relocation tests pass (the 2 RED layering markers flipped); behavior preserved.

### What moved (ADR-147 Move #1)

| Symbol | From | To |
|--------|------|----|
| `find_confrontation_def` | `server/dispatch/confrontation.py` | `game/ruleset/combat_rules.py` (new) |
| `resolve_damage_spec_from_beat_and_actor` | `server/dispatch/damage_roll.py` | `game/ruleset/combat_rules.py` (new) |
| `resolve_inventory` (+ `merge_inventory_catalog`, `VerbatimFieldLockError`, helpers) | `server/dispatch/inventory_resolve.py` | `game/inventory_resolve.py` (`git mv`) |

**Edges deleted:** `native.py` (module-level) and `without_number.py` (2 lazy in-method) no longer import upward into `sidequest.server`; the layer-inversion comment is gone. The TEA blocking finding is resolved — `resolve_inventory` came down with the damage helper, so the relocated `combat_rules` module's priority-3 catalog lookup is game→game, not a re-opened upward edge.

**Behavior preservation:** the 3 old server paths (`confrontation.py`, `damage_roll.py`, `inventory_resolve.py`) became re-export shims (server→game, the legal direction), so ~6 server-tier modules + ~10 test files importing from the old paths keep working untouched. An `is`-identity smoke test confirms every shim + consumer resolves to the single new-home object; no circular import on the early-loaded `game/ruleset` path (annotation-only types — `ConfrontationDef`/`BeatDef`/`GenrePack` — are under `TYPE_CHECKING` in `combat_rules.py`).

### Verification (testing-runner, run `122-2-dev-green`, `-n0`)

| Set | Result |
|-----|--------|
| `test_122_2_combat_rules_relocation.py` (the story's tests) | **13/13 PASS** (incl. both previously-RED layering markers) |
| `test_damage_dice_request.py` + `test_inventory_union_merge.py` + `tests/game/ruleset/` | **468/468 PASS** |
| confrontation / find_confrontation_def consumers (non-content) | **25/25 PASS** |

**Pre-existing failures (NOT this story):** 12 failures in WN-family content-pack tests (mutant_wasteland/awn, road_warrior/cwn, neon_dystopia/cwn) — all `PackError: genre-tier baseline carries bespoke item(s) ... (ADR-145 D3)` from `_validate_genre_baseline_no_bespoke` in `genre/loader.py:743` during `load_genre_pack`. This is the epic 114-14/120-3 content-vs-validator gap (un-swept bespoke genre gear), present on develop, unrelated to helper placement. Verified by reading the traceback — content validation, not an ImportError/AttributeError from the move. (Matches the documented known-failure set.)

**Lint:** `ruff check` + `ruff format` clean on all 7 touched files.

**Handoff:** To Hermes Psychopompos (Reviewer) for review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (1 pre-existing TODO, not introduced) | N/A |
| 2 | reviewer-edge-hunter | Yes | clean | none | N/A |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (3 enabled returned, all clean; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 0 confirmed, 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

This is a faithful, behavior-preserving relocation (ADR-147 Move #1). I independently verified the move rather than trusting the green suite, and every check corroborates the three clean subagent reports.

**Data flow traced:** a strike beat → `RulesetModule.resolve_damage(beat, actor_core, pack, world_slug)` → `resolve_damage_spec_from_beat_and_actor` (now in `game/ruleset/combat_rules.py`) → priority-3 lazy `resolve_inventory` (now `game/inventory_resolve.py`) → `DamageSpec | None`. The chain is now entirely within the game tier (game→game), where before it crossed game→server twice. Safe: the function body is byte-identical (see drift check below), so the resolution priority ladder (override → item-dict → catalog → unarmed floor → None) is unchanged.

**Pattern observed:** re-export shim at the vacated tier — `server/dispatch/{confrontation,damage_roll,inventory_resolve}.py` import the relocated names back from the game tier (server→game, the legal direction) so ~6 server modules + ~10 test files keep their imports. This mirrors the pre-existing `dice.py`-re-exports-`damage_roll` idiom. Good pattern: minimal blast radius, no caller churn.

**Error handling:** unchanged and preserved. The two `except Exception` blocks in `resolve_damage_spec` log-and-skip a single unparseable item (`combat_rules.py:92-104`) — not silent swallow; `logger` is correctly re-declared module-level in the new home. `VerbatimFieldLockError`/`PackError` fail-loud raises survive the `inventory_resolve` move verbatim (No Silent Fallbacks intact).

### Observations

- [VERIFIED] No behavior drift — `find_confrontation_def` and `inventory_resolve.py` are **byte-identical** to develop; `resolve_damage_spec` differs by exactly one line (the intended `server.dispatch.inventory_resolve` → `game.inventory_resolve` import). Evidence: `diff` against `git show develop:...` — `find_confrontation_def` IDENTICAL, `inventory_resolve.py` IDENTICAL, `resolve_damage_spec` 1-line delta at the priority-3 import.
- [VERIFIED] Re-export shims are complete — AST-scanned every `from <old path> import` across `sidequest/` + `tests/` (multi-line aware). `confrontation` callers need 8 names (7 still defined there + `find_confrontation_def` re-exported); `damage_roll` callers need 5 (4 still defined + `resolve_damage_spec` re-exported); `inventory_resolve` callers need 3, all 3 moved + re-exported via `__all__`. No dropped name → no broken import.
- [VERIFIED] Shim identity, not copy — preflight's `is`-identity check confirms each re-exported name resolves to the *same object* as the game-tier canonical; there is no duplicated definition to drift.
- [VERIFIED] No circular import — `combat_rules` imports only `logging`/`DamageSpec` at module level (annotation types under `TYPE_CHECKING`) and lazily defers `game.inventory_resolve`; `game/ruleset/__init__.py` does not eagerly load the concrete modules (registry loads lazily). Evidence: import smoke test loads all 7 modules cleanly; 468 tests pass.
- [VERIFIED] `TYPE_CHECKING` is sound — `ConfrontationDef`/`BeatDef`/`GenrePack` appear only in the `TYPE_CHECKING` block, annotations, and a docstring; zero runtime references; `from __future__ import annotations` makes annotations lazy strings regardless. No `NameError`. (`combat_rules.py:23-25,31,33,48,50`)
- [VERIFIED] No new upward edge — diff's added lines contain no real `from sidequest.server import` from a game-tier file (the one textual match is a docstring describing the test's AST scanner). The story's own AST layering tests (now GREEN) enforce this.
- [MEDIUM→pre-existing, not blocking] 12 WN-family content-pack tests fail with `PackError: genre-tier baseline carries bespoke item(s) (ADR-145 D3)` from `_validate_genre_baseline_no_bespoke` in `genre/loader.py:743`. Confirmed via traceback to be the epic 114-14/120-3 content gap, present on develop, unrelated to helper placement (a content-vs-validator mismatch, not an import error from the move).
- [EDGE] reviewer-edge-hunter returned **clean** (0 findings) — independently confirmed all four high-risk relocation edges: byte-identical moved bodies (drift), complete re-exports (no dropped name across multi-line imports), no circular/load-order cycle, and correct `TYPE_CHECKING` (annotation-only). Corroborates my independent VERIFIEDs above.
- [SEC] reviewer-security returned **clean** (0 findings) — confirmed the `except Exception` blocks log-and-skip (not silent swallow), `VerbatimFieldLockError`/`PackError` fail-loud survives the move, no secrets/PII in moved code, and the shims expose no previously-private surface (no new attack surface).

### Rule Compliance (sidequest-server CLAUDE.md + python.md lang-review)

- **No Silent Fallbacks** — COMPLIANT. The `None`/`raise` returns in the moved functions are documented contracts (caller decides on a miss), not silent alternative-path fallbacks; `except` blocks log before skipping. Verified across both moved functions + `inventory_resolve`.
- **No Stubbing / No half-wired features** — COMPLIANT. No empty shells; the re-export shims are live, functional, and exercised. The relocated code has real non-test consumers (`native.py`, `without_number.py`, + the 6 server shim consumers).
- **No Source-Text Wiring Tests** — COMPLIANT. The story's layering tests use `ast` parsing (structural), not `read_text()` regex; behavior is proven through the real `RulesetModule` seam.
- **python.md #10 import hygiene** — COMPLIANT. No star imports; no circular imports (verified); `noqa: F401` on the two re-export imports is the correct idiom; `__all__` on the inventory shim. No cycle introduced.
- **python.md #3 type annotations at boundaries** — COMPLIANT. Public function signatures retain full annotations (carried verbatim from originals).
- **python.md #6 test quality** — COMPLIANT (TEA-authored). Spot-checked: every test asserts a concrete value; no vacuous assertions.
- **OTEL Observability** — N/A. Cosmetic relocation of pure helpers with no subsystem decision change; CLAUDE.md exempts placement/label changes. No spans removed (the helpers never emitted any).

### Devil's Advocate

Let me argue this is broken. First attack: a relocation that *looks* faithful but silently changes behavior — the classic copy-paste-with-a-typo. I defended against this by diffing the moved bodies against `git show develop:` rather than eyeballing the new files; `find_confrontation_def` and the whole `inventory_resolve` module are byte-identical, and `resolve_damage_spec` deviates by exactly the one import line the story requires. A reviewer who only ran the tests could miss a subtle drift the tests don't cover — but here there is literally nothing to drift to.

Second attack: a broken import for some caller the tests don't exercise. A relocation's real danger is the long tail of importers, especially multi-line `from x import (\n a,\n b,\n)` blocks that a single-line grep misses. I caught exactly that risk and re-ran the enumeration with an AST walk over `sidequest/` + `tests/`, then cross-checked every imported name against each shim's surface. `narration_apply.py` imports `resolve_damage_spec_from_beat_and_actor` in a parenthesized block — the shim re-exports it. `VerbatimFieldLockError` is imported from the old `inventory_resolve` path (not just `resolve_inventory`) — the shim's `__all__` includes it. Nothing is dropped.

Third attack: import-time circular load. The original code used *lazy* imports specifically to dodge a cycle; what if hoisting them to module level reintroduces it under some import order? But the cycle existed because the lazy imports reached *up* into heavyweight `server.dispatch.*`; `combat_rules` reaches only *down* (genre models) and defers `game.inventory_resolve` to call-time, and `game/ruleset/__init__` doesn't eagerly load the concrete modules. Both the smoke test and 468 passing tests load the graph without error.

Fourth attack: `TYPE_CHECKING` hiding a runtime name. If any of the three annotation types were used at runtime, the module would `NameError` on first call — and the tests *do* call these functions. They pass. Confirmed annotation-only.

Fifth, the confused-maintainer angle: two files named `inventory_resolve.py` now exist (game canonical + server shim). Mildly surprising, but the shim's docstring + `__all__` make the relationship explicit, and it's the documented project idiom. Not a defect. I cannot break this change.

**Handoff:** To Themis the Just (SM) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (blocking): `resolve_damage_spec_from_beat_and_actor` lazy-imports `resolve_inventory` from `server.dispatch.inventory_resolve` (damage_roll.py:212, priority-3 catalog lookup). `resolve_inventory` is itself **pure** (imports only `sidequest.genre.*` + `sidequest.telemetry.*`, never `sidequest.server.*`). If Dev relocates the damage helper into the game tier but leaves it importing `resolve_inventory` from server, the upward edge merely **moves** — it is not deleted. ADR-147 Move #1 explicitly scopes this in: relocate the two named helpers "**and any sibling pure-resolution helpers they pull in**". Affects `sidequest/server/dispatch/inventory_resolve.py` (must relocate to the game tier alongside the damage helper) and the new combat-rules module (must import `resolve_inventory` from its new home, not from server). Guarded by `test_no_game_tier_module_imports_inventory_resolve_from_server`. *Found by TEA during test design.*
- **Improvement** (non-blocking): `find_confrontation_def` lives in `server/dispatch/confrontation.py`, a module that also holds genuinely server-tier functions (`make_confrontation_frame_supplier`, `make_confrontation_portrait_resolver` — these DO import `server.emitters`). Dev moves only `find_confrontation_def` down; the rest stays. ~6 server-tier modules + ~10 test files import `find_confrontation_def` from the old path — these are legal *downward* imports (server→game), so a re-export shim at the old location (or updating the call sites) preserves them. No game→server edge there to fix. Affects `sidequest/server/dispatch/confrontation.py`, `damage_roll.py`, `dice.py` (re-exports), `narration_apply.py`, `session_helpers.py`, `encounter_lifecycle.py` (decide: re-export shim vs. update imports). *Found by TEA during test design.*

### Reviewer (code review)
- **Improvement** (non-blocking): three re-export shims (`server/dispatch/{confrontation,damage_roll,inventory_resolve}.py` for the moved names) are correct and low-risk, but a future cleanup could update the ~25 remaining old-path importers and delete the shims so there is a single canonical import path per symbol. Not required by 122-2 and harmless to leave (server→game is legal); 122-5's enforcing guard is unaffected. Affects the listed importers across `sidequest/server/*` + `tests/*`. *Found by Reviewer during code review.*
- **Note** (non-blocking): the 12 pre-existing WN-family content-pack failures (`PackError: genre-tier baseline carries bespoke item(s)`, ADR-145 D3) are the epic 114-14/120-3 content sweep, already tracked (120-3 in backlog). Not introduced here. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

5 deviations

- **Destination module not pinned; tests are module-agnostic**
  - Rationale: ADR-147 explicitly leaves the destination module to Dev; hardcoding a path would force a specific filename and false-fail on a legitimate choice. Seam-based behavior tests are refactor-stable and double as the wiring test (consumer → relocated helper).
  - Severity: minor
  - Forward impact: none — Dev picks the module freely; the layering + behavior contract holds regardless.
- **No dedicated "lazy import dropped" assertion**
  - Rationale: A behavioral form of "module-level not lazy" over-couples to Dev's import style (named import vs. module import vs. alias) and CLAUDE.md forbids source-text wiring tests (`read_text()` regex on production source). The substantive contract — no upward edge, module loads without circular-import tricks — is fully enforced.
  - Severity: minor
  - Forward impact: none.
- **Re-export shims at the old server paths instead of updating ~25 call sites**
  - Rationale: Those callers are server-tier — server→game is the legal import direction (ADR-147 law), so they carry no layering defect to fix. A shim deletes the upward edges with a ~25-edit-smaller, lower-risk diff and is exactly the behavior-preservation pattern `dice.py`/`damage_roll.py` already document. Verified by `is`-identity smoke test: every shim + consumer resolves to the single new-home object.
  - Severity: minor
  - Forward impact: the 3 shim modules can be deleted later by a follow-up that updates the remaining importers; harmless to leave (legal direction). 122-5's enforcing guard is unaffected (it forbids game→server, not these server→game shims).
- **`resolve_inventory` module relocated to `game/` top-level, not `game/ruleset/`**
  - Rationale: inventory-catalog resolution is consumed by chargen/views/narration/combat, not ruleset-specific, so the neutral `game/` tier (its dependencies are only `genre.models` + `telemetry`) is the honest home. Still satisfies the finding (out of `server/`, into the game tier) and the guard test (`test_no_game_tier_module_imports_inventory_resolve_from_server`).
  - Severity: minor
  - Forward impact: none — could descend further to `genre/` later (its deps permit it), but `game/` is correct and lower-churn now.
- **`resolve_damage_spec` priority-3 inventory import kept function-local**
  - Rationale: That import was never an upward/cycle workaround being targeted; keeping it function-local preserves exact load-time behavior and adds no new import-time edge. It passes the layering guard (game→game, not game→server) and all behavior tests.
  - Severity: trivial
  - Forward impact: none.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Destination module not pinned; tests are module-agnostic**
  - Spec source: context-story-122-2.md (story title) + ADR-147 Move #1
  - Spec text: "move ... into `game/ruleset/` alongside `base.py`, or a sibling `game/` module; **Dev confirms the exact module**"
  - Implementation: Layering tests assert via AST that `native.py` / `without_number.py` import nothing from `sidequest.server` (RED→GREEN), rather than asserting a concrete `from sidequest.game.ruleset.combat_rules import ...` path. Behavior is characterized through the public `RulesetModule` seam (`NativeRulesetModule` + a WN sibling via `get_ruleset_module`), not a direct import of the relocated symbol.
  - Rationale: ADR-147 explicitly leaves the destination module to Dev; hardcoding a path would force a specific filename and false-fail on a legitimate choice. Seam-based behavior tests are refactor-stable and double as the wiring test (consumer → relocated helper).
  - Severity: minor
  - Forward impact: none — Dev picks the module freely; the layering + behavior contract holds regardless.
- **No dedicated "lazy import dropped" assertion**
  - Spec source: SM Assessment AC ("Lazy/function-local imports in `without_number.py` dropped for module-level imports")
  - Spec text: "drop lazy imports"
  - Implementation: Covered indirectly — `test_without_number_module_imports_nothing_from_server` (AST, walks into method bodies) goes GREEN only when the lazy server imports are gone; the "module-level vs lazy" placement of the *new* (game-tier) import is not separately asserted.
  - Rationale: A behavioral form of "module-level not lazy" over-couples to Dev's import style (named import vs. module import vs. alias) and CLAUDE.md forbids source-text wiring tests (`read_text()` regex on production source). The substantive contract — no upward edge, module loads without circular-import tricks — is fully enforced.
  - Severity: minor
  - Forward impact: none.

### Dev (implementation)
- **Re-export shims at the old server paths instead of updating ~25 call sites**
  - Spec source: SM Assessment AC ("All callers updated"); ADR-147 Move #1
  - Spec text: "All callers updated (server/dispatch consumers, native.py, without_number.py)"
  - Implementation: `native.py` / `without_number.py` (the game-tier callers, the actual upward edges) are updated to import from the new home. The ~6 server-tier modules + ~10 test files that import the helpers from `server.dispatch.confrontation` / `damage_roll` / `inventory_resolve` are NOT edited; those three old modules became thin re-export shims (`from sidequest.game.<new home> import ...`).
  - Rationale: Those callers are server-tier — server→game is the legal import direction (ADR-147 law), so they carry no layering defect to fix. A shim deletes the upward edges with a ~25-edit-smaller, lower-risk diff and is exactly the behavior-preservation pattern `dice.py`/`damage_roll.py` already document. Verified by `is`-identity smoke test: every shim + consumer resolves to the single new-home object.
  - Severity: minor
  - Forward impact: the 3 shim modules can be deleted later by a follow-up that updates the remaining importers; harmless to leave (legal direction). 122-5's enforcing guard is unaffected (it forbids game→server, not these server→game shims).
- **`resolve_inventory` module relocated to `game/` top-level, not `game/ruleset/`**
  - Spec source: TEA blocking finding ("must relocate to the game tier alongside the damage helper")
  - Spec text: "Affects `sidequest/server/dispatch/inventory_resolve.py` (must relocate to the game tier ...)"
  - Implementation: `git mv` to `sidequest/game/inventory_resolve.py` (game top-level), not under `game/ruleset/`. `combat_rules.py` imports it (game→game).
  - Rationale: inventory-catalog resolution is consumed by chargen/views/narration/combat, not ruleset-specific, so the neutral `game/` tier (its dependencies are only `genre.models` + `telemetry`) is the honest home. Still satisfies the finding (out of `server/`, into the game tier) and the guard test (`test_no_game_tier_module_imports_inventory_resolve_from_server`).
  - Severity: minor
  - Forward impact: none — could descend further to `genre/` later (its deps permit it), but `game/` is correct and lower-churn now.
- **`resolve_damage_spec` priority-3 inventory import kept function-local**
  - Spec source: ADR-147 ("deletes the lazy-import workarounds on the combat path")
  - Spec text: "delete the lazy import workarounds in native.py / without_number.py"
  - Implementation: The lazy workarounds ADR-147 names — the *upward* `server.dispatch` imports in `native.py`/`without_number.py` — are deleted. The unrelated function-local `from sidequest.game.inventory_resolve import resolve_inventory` inside `resolve_damage_spec` (priority-3 block) is kept function-local (now a game→game import).
  - Rationale: That import was never an upward/cycle workaround being targeted; keeping it function-local preserves exact load-time behavior and adds no new import-time edge. It passes the layering guard (game→game, not game→server) and all behavior tests.
  - Severity: trivial
  - Forward impact: none.

### Reviewer (audit)
- **TEA: module-agnostic tests (no pinned destination)** → ✓ ACCEPTED by Reviewer: correct call — ADR-147 explicitly leaves the module to Dev; AST + seam-based tests are refactor-stable and still pinned the substantive contract (verified GREEN after the move).
- **TEA: no dedicated "lazy import dropped" assertion** → ✓ ACCEPTED by Reviewer: a behavioral form would over-couple to import style and CLAUDE.md forbids source-text wiring tests; the AST layering test (walks method bodies) fully covers the intent.
- **Dev: re-export shims instead of updating ~25 call sites** → ✓ ACCEPTED by Reviewer: server→game is the legal direction (no defect in those callers); minimal blast radius; AST-verified that every shim covers every imported name; matches the existing `dice.py` idiom.
- **Dev: `resolve_inventory` relocated to `game/` top-level (not `game/ruleset/`)** → ✓ ACCEPTED by Reviewer: it is consumed beyond ruleset (chargen/views/narration), so neutral `game/` is the honest home; satisfies the finding and the guard test.
- **Dev: priority-3 inventory import kept function-local** → ✓ ACCEPTED by Reviewer: it was never the upward/cycle workaround ADR-147 targets; keeping it call-time preserves exact load behavior and is game→game (passes the guard).