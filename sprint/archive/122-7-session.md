---
story_id: "122-7"
jira_key: ""
epic: "122"
workflow: "trivial"
---
# Story 122-7: Import-direction guard hardening — drop>=len root-escape boundary, except OSError in _parse_module, assert SIDEQUEST_PKG identity (ADR-147 122-5 review follow-up)

## Story Details
- **ID:** 122-7
- **Jira Key:** (not applicable)
- **Workflow:** trivial
- **Stack Parent:** none
- **Type:** chore
- **Points:** 1
- **Priority:** p3

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-17T09:59:10Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-17T09:42:23Z | 2026-06-17T09:44:29Z | 2m 6s |
| implement | 2026-06-17T09:44:29Z | 2026-06-17T09:51:12Z | 6m 43s |
| review | 2026-06-17T09:51:12Z | 2026-06-17T09:59:10Z | 7m 58s |
| finish | 2026-06-17T09:59:10Z | - | - |

## Sm Assessment

**Scope (trivial chore, server-only, 1pt):** Hardens the AST import-direction guard shipped in 122-5 (the ADR-147 CI guard that fails on any domain→server upward import). Three named, bounded changes — see the Story Context section for the full spec:
1. `drop >= len` root-escape boundary when walking package paths.
2. `except OSError` around `_parse_module`'s read/parse — loud, attributable per-file failure, **not** a silent skip (No-Silent-Fallbacks).
3. assert `SIDEQUEST_PKG` identity so the guard can't run against the wrong tree.

**Baseline:** Branch `feat/122-7-import-direction-guard-hardening` is cut from `develop` tip `b70f6334`, which now includes 122-9 (#932). So the lint/test baseline is green — 122-7 verifies against a clean tree, which was the whole reason 122-9 went first.

**Scope boundary for Dev/Reviewer:** The title's three items are the authoritative scope. 122-5's review also flagged a **HIGH** gap — relative-import upward edges (`from ..server`) evade the guard because `node.module` is a relative suffix, not `sidequest.server`. That is *not* in this story's named scope; if Dev confirms it's still unaddressed, log it as a Delivery Finding (Gap) for a future story rather than expanding 122-7. Don't silently fold it in.

**Risk:** Low–moderate. Real guard-logic edits (unlike 122-9's pure lint), but bounded and test-tier. The `except OSError` change must surface failures loudly — watch that it doesn't become a silent `pass` that lets a bad file slip the guard.

**Routing:** trivial → phased; next phase `implement` → Hephaestus the Smith (Dev).

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed (all `sidequest-server`):**
- `tests/infrastructure/test_import_direction_guard.py` — the three named hardenings + 4 new unit tests:
  1. `_resolve_relative`: boundary `drop > len(package_parts)` → `drop >= len(...)`. At `drop == len` the slice was empty and joined into a misleading bare `"server"`; now it correctly returns `None` (root escape above the `sidequest` top-level). Docstring updated.
  2. `_parse_module`: added `except OSError` → `pytest.fail("… could not be read …")`, alongside the existing `UnicodeDecodeError`/`SyntaxError` loud-fails. Covers vanished / permission-denied / is-a-directory reads (No Silent Fallbacks). Docstring updated.
  3. `SIDEQUEST_PKG` identity: new `test_sidequest_pkg_is_the_real_package` asserts the scanned root is the real importable `sidequest` package (`.name`, `__init__.py` present, and matches `Path(sidequest.__file__)`), so the guard can't run vacuously against a stray/shadowed tree.
- New unit tests: `test_resolve_relative_rejects_root_escape_at_boundary`, `test_resolve_relative_keeps_deepest_valid_drop`, `test_parse_module_fails_loud_on_unreadable_file`, `test_sidequest_pkg_is_the_real_package`.

**Form note (not a deviation):** "assert SIDEQUEST_PKG identity" was implemented as a `pytest` test function with asserts — the idiomatic form in this module (which already houses its structural-invariant test `test_guarded_tiers_exist_and_have_modules` the same way) — rather than a module-level `assert`. The spec's "assert" is satisfied; a test fails loudly under pytest and reads consistently with the file.

**122-5 HIGH gap status:** The 122-5 review flagged that relative-import upward edges (`from ..server`) could evade the guard. That is **already closed** in the current code — `_server_import_targets` resolves relative imports via `_resolve_relative` (lines 157–158) before matching, with three dedicated tests (`test_relative_import_reaching_server_is_detected`, `…_bare_…`, `…_to_sibling_is_not_a_false_positive`). No outstanding Gap; nothing to fold in here.

**Lint:** `uv run ruff check .` → All checks passed. `ruff format --check` clean on the touched file.
**Tests:** 17/17 GREEN (`pytest -n0`, RUN_ID `122-7-dev-green`) across the guard file + its consumer `test_kind_to_message_cls_relocation.py`; real-tree scan `test_no_upward_imports_beyond_grandfathered` still passes (the `>`→`>=` change cannot affect real files — a drop==len relative import is illegal Python and cannot exist in working code).
**Branch:** `feat/122-7-import-direction-guard-hardening` (pushed to origin).

**Handoff:** To review — Hermes Psychopompos.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean (GREEN) | none (lint clean, 17/17, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 2 medium, 1 low | 3 confirmed, all non-blocking |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (3 enabled returned — preflight clean, security clean, edge-hunter 3 findings all confirmed non-blocking; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 3 confirmed (all Medium/Low, non-blocking), 0 dismissed, 0 deferred-to-block

## Reviewer Assessment

**Verdict:** APPROVED

**Scope:** Hardens the ADR-147 import-direction guard (`tests/infrastructure/test_import_direction_guard.py`), single-file diff +66/−5: (1) `_resolve_relative` boundary `drop > len` → `drop >= len`; (2) `except OSError` loud-fail in `_parse_module`; (3) `SIDEQUEST_PKG` identity test + 3 new resolver/parse unit tests. Real guard logic — reviewed for behavioral correctness, not just lint.

**Data flow traced:** A relative import spelling (e.g. `from ...server import x`) → `_server_import_targets` → `_resolve_relative(level, module, package_parts)` → boundary check → dotted-path match against `sidequest.server*`. Traced the boundary: `package_parts[0]` is always `"sidequest"` (paths are relative to `SIDEQUEST_PKG.parent`), so the deepest *legal* drop is `len-1` (base `["sidequest"]`); `drop == len` empties the base and escapes above the package root — which Python rejects at import as "relative import beyond top-level package," so it cannot occur in importable code. `>=` is therefore correct and **not** over-tight. Safe.
**Wiring:** The identity test (`test_sidequest_pkg_is_the_real_package`) + the real-tree scan (`test_no_upward_imports_beyond_grandfathered`, confirmed passing by preflight) are the integration tests anchoring the guard to the real imported `sidequest` package. The top-of-file `import sidequest` is the production consumer.
**Tenant isolation audit:** N/A — no tenant data, no trait methods, no structs in the diff.
**Error handling:** The new `except OSError` → `pytest.fail("… could not be read …")` is loud and attributable, consistent with the existing `UnicodeDecodeError`/`SyntaxError` arms.

### Observations (tagged by source)
- [VERIFIED] Boundary `>`→`>=` is correct and minimal — evidence: with `package_parts[0] == "sidequest"`, valid drops are `0..len-1`; `drop == len` → empty base → root escape (illegal Python). The old `>` let `drop == len` through as a bogus bare `"server"`. New tests pin both ends (`…rejects_root_escape_at_boundary`, `…keeps_deepest_valid_drop`), and the real-tree scan still passes (no new false-positive layering violation).
- [VERIFIED] `except OSError` ordering is sound — `UnicodeDecodeError` is a `ValueError` subclass, disjoint from `OSError`, so the two `except` arms don't shadow; both fail loud. Strengthens the guard (an unreadable file can't slip the scan silently).
- [EDGE] (CONFIRMED — Medium, non-blocking) Finding 3: `test_parse_module_fails_loud_on_unreadable_file` matches only `"could not be read"`, not the file path — so a future refactor dropping the `{rel}` interpolation would still pass, leaving the docstring's load-bearing "naming the file" behavior unverified. Production code is correct (it does include `{rel}`); the test under-asserts. Recorded as a non-blocking follow-up (tighten `match` to pin the filename).
- [EDGE] (CONFIRMED — Low, non-blocking) Finding 1: identity assertion #3 `Path(sidequest.__file__).resolve() == SIDEQUEST_PKG / "__init__.py"` is partially tautological given `SIDEQUEST_PKG := Path(sidequest.__file__).resolve().parent` — it reduces to "`__file__` basename is `__init__.py`." Assertions #1 (`.name == "sidequest"`) and #2 (`__init__.py` is_file) carry the real identity check, and the namespace-package case (`__file__ is None`) already fails loud at the module-level `SIDEQUEST_PKG` definition (TypeError at collection). Harmless; the docstring's "shadowing" claim slightly overstates. Non-blocking.
- [EDGE] (CONFIRMED — Low, deferred) Finding 2: `_parse_module`'s `path.relative_to(SIDEQUEST_PKG)` (before the try) raises `ValueError`, not `OSError`, for an out-of-tree path, and is unguarded. Theoretical only — every caller (`_scan_tier` via `_iter_py_files(SIDEQUEST_PKG / tier)`) supplies in-tree paths. Deferred: document the precondition or guard it in a follow-up.
- [SEC] security clean — defensive hardening only; no `exec`/dynamic-import/subprocess, no writes, no out-of-tree access; `except OSError` fails loud (does not weaken the invariant).
- [SIMPLE] No unnecessary complexity — a one-character boundary fix, one `except` clause, and four focused tests. (simplifier disabled — assessed directly.)
- [TEST] New tests are behavioral, not vacuous — boundary (both sides), OSError loud-fail (with `match`), identity, all GREEN; real-tree scan green. The two test-tightening gaps (findings 1, 3) are noted above. (test_analyzer disabled — assessed directly, corroborated by edge-hunter.)
- [DOC] `_resolve_relative` and `_parse_module` docstrings updated accurately for the new behavior; only the identity-test docstring's "shadowing" line overstates (finding 1). (comment_analyzer disabled — assessed directly.)
- [TYPE] No type/signature changes; `pytest.fail.Exception` resolves in this pytest (the test passed). (type_design disabled — assessed directly.)
- [SILENT] No silent failures introduced — every error path raises `pytest.fail`; No-Silent-Fallbacks honored. (silent_failure_hunter disabled — assessed directly.)
- [RULE] Compliant — No-Silent-Fallbacks (loud, named pytest.fail), Every-Suite-Needs-a-Wiring-Test (identity + real-tree scan), No-Source-Text-Wiring-Tests (identity test uses reflection on `Path`/`__file__`, not a source-string grep; the guard's `read_text` is to AST-parse for the layering law — the legitimate use), format-only-touched-files (single file). (rule_checker disabled — assessed directly.)

### Rule Compliance
- **No Silent Fallbacks (CLAUDE.md):** COMPLIANT — `except OSError` → `pytest.fail`, loud and file-named; no swallow/skip.
- **No Stubbing:** COMPLIANT — no placeholder code.
- **Every Test Suite Needs a Wiring Test:** COMPLIANT — `test_sidequest_pkg_is_the_real_package` pins the scan root to the real imported package; `test_no_upward_imports_beyond_grandfathered` is the integration scan over the live tree.
- **No Source-Text Wiring Tests:** COMPLIANT — the identity test interrogates runtime types (`Path(sidequest.__file__)`), not source strings; the guard's `read_text` feeds `ast.parse` (behavioral), not a grep assertion.
- **Server format-drift guardrail (memory):** COMPLIANT — single touched file, `ruff format --check` clean, no mass reformat.

### Devil's Advocate
Assume this hardening is broken. Attack 1: the `>=` boundary is over-tight and now silently *drops* a legitimate upward edge from the scan, turning the guard blind — a domain file could import `sidequest.server` via a deep relative spelling and the guard would resolve it to `None` and miss it. Refutation: the only spellings newly mapped to `None` are those with `drop == len`, i.e. relative imports that climb above the `sidequest` top-level — Python raises `ImportError: attempted relative import beyond top-level package` for these, so no importable module can contain one; the live-tree scan (`test_no_upward_imports_beyond_grandfathered`) stayed green, proving zero real edges were newly hidden. Attack 2: the `except OSError` swallows a transient read error and lets an unscanned file pass as clean — a layering violation slips through. Refutation: the handler calls `pytest.fail`, which raises and *fails the build*; it cannot continue past a bad read, so a vanished/unreadable file halts the suite loudly rather than passing. Attack 3: the new OSError test is vacuous and would pass even if the handler were deleted. Refutation: with the handler removed, a `FileNotFoundError` would propagate uncaught and `pytest.raises(pytest.fail.Exception)` would NOT match it — the test would error, so it genuinely pins the behavior (though, per finding 3, not the filename portion). Attack 4: the identity test gives false confidence. Partly conceded — assertion #3 is tautological (finding 1) — but assertions #1/#2 plus the line-58 `Path(None)` TypeError still catch the real namespace/wrong-root failure modes. Net: the production behavior is correct and adequately covered; the surviving weaknesses are test-assertion tightness, not engine defects.

**Handoff:** To SM (Themis the Just) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No upstream findings. (The 122-5 HIGH relative-import gap this story follows up on is already closed in current code — see Dev Assessment — so no Gap is raised.)

### Reviewer (code review)
- **Improvement** (non-blocking): tighten `test_parse_module_fails_loud_on_unreadable_file`'s `match` to also pin the file path (e.g. `match=r"does_not_exist_122_7_guard_probe\.py.*could not be read"`), so the docstring's load-bearing "naming the file" behavior is actually verified and survives refactor. Affects `tests/infrastructure/test_import_direction_guard.py` (one-line test change). *Found by Reviewer during code review (edge-hunter finding 3).*
- **Improvement** (non-blocking): identity assertion #3 in `test_sidequest_pkg_is_the_real_package` is partially tautological; consider replacing with a directly-meaningful check (e.g. `assert sidequest.__file__ is not None`) or tightening the docstring's "shadowing" claim. Affects `tests/infrastructure/test_import_direction_guard.py`. *Found by Reviewer during code review (edge-hunter finding 1).*
- **Gap** (non-blocking): `_parse_module`'s `path.relative_to(SIDEQUEST_PKG)` raises `ValueError` (not `OSError`) for an out-of-tree path and is unguarded; harmless today (all callers pass in-tree paths) but the precondition is undocumented. Affects `tests/infrastructure/test_import_direction_guard.py` (document the precondition or guard the call). *Found by Reviewer during code review (edge-hunter finding 2).*

## Impact Summary

**Upstream Effects:** 2 findings (1 Gap, 0 Conflict, 0 Question, 1 Improvement)
**Blocking:** None

- **Improvement:** tighten `test_parse_module_fails_loud_on_unreadable_file`'s `match` to also pin the file path (e.g. `match=r"does_not_exist_122_7_guard_probe\.py.*could not be read"`), so the docstring's load-bearing "naming the file" behavior is actually verified and survives refactor. Affects `tests/infrastructure/test_import_direction_guard.py`.
- **Gap:** `_parse_module`'s `path.relative_to(SIDEQUEST_PKG)` raises `ValueError` (not `OSError`) for an out-of-tree path and is unguarded; harmless today (all callers pass in-tree paths) but the precondition is undocumented. Affects `tests/infrastructure/test_import_direction_guard.py`.

### Downstream Effects

- **`tests/infrastructure`** — 2 findings

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No deviations from spec. All three named items (drop>=len boundary, except OSError, SIDEQUEST_PKG identity) implemented as specified. The identity check was realized as a pytest test rather than a module-level `assert` — a form choice within spec, documented in the Dev Assessment, not a behavioral divergence.

### Reviewer (audit)
- **Dev's "No deviations from spec" + identity-test form note** → ✓ ACCEPTED by Reviewer: all three named items are implemented as specified, and the pytest-test form for the identity check is consistent with this module's existing structural-invariant test (`test_guarded_tiers_exist_and_have_modules`) — within spec, not a divergence. No undocumented deviations found; the diff is fully accounted for by the three named changes + their tests.

## Branch Information

**Branch Strategy:** gitflow (feat/122-7-import-direction-guard-hardening)
**Repo:** sidequest-server
**Base:** develop
**Stack Parent:** none (stack root)

## Story Context

**ADR Reference:** docs/adr/147-honest-layering-pure-logic-below-server.md

**Background:**
Story 122-5 shipped an import-direction guard (AST-based test) that fails on any domain→server upward import. 122-7 addresses three robustness gaps flagged in 122-5's review:

1. **drop>=len root-escape boundary** — Guard against the case where the number of trailing path components to drop is >= the path length (prevent escaping above SIDEQUEST_PKG root).

2. **except OSError in _parse_module** — Wrap `ast.parse` and file read in `except OSError` to handle malformed or non-UTF-8 files gracefully with loud, attributable failure (no silent fallbacks per CLAUDE.md principle).

3. **assert SIDEQUEST_PKG identity** — Verify the resolved SIDEQUEST_PKG root is the actual `sidequest` package location to prevent the guard running against the wrong tree.

**Acceptance Criteria:**
- All three hardening changes implemented in the import-direction guard
- Guard still passes on clean tree
- `just server-check` is green
- No unrelated changes

**Note:** The 122-5 review flagged a HIGH finding about relative-import upward edges (`from ..server`) evading the AST guard; that scope may be separate and should be flagged if not addressed in this story.