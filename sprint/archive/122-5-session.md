---
story_id: "122-5"
jira_key: ""
epic: "122"
workflow: "trivial"
---
# Story 122-5: CI guard — fail on any domain->server upward import (foundation/game/genre/orbital/magic/interior); lands last + enforcing

## Story Details
- **ID:** 122-5
- **Jira Key:** (none — Jira disabled for this project)
- **Workflow:** trivial
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-16T05:40:30Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-16T18:00:00Z | 2026-06-16T05:13:47Z | -45973s |
| implement | 2026-06-16T05:13:47Z | 2026-06-16T05:19:57Z | 6m 10s |
| review | 2026-06-16T05:19:57Z | 2026-06-16T05:27:08Z | 7m 11s |
| implement | 2026-06-16T05:27:08Z | 2026-06-16T05:31:26Z | 4m 18s |
| review | 2026-06-16T05:31:26Z | 2026-06-16T05:40:30Z | 9m 4s |
| finish | 2026-06-16T05:40:30Z | - | - |

## Context

**Epic 122: Honest Layering** (ADR-147) restructures the layering law: imports flow downward only (`foundation ← {game, genre, orbital, magic, interior} ← server`). Stories 122-1 through 122-4 have already relocated the misfiled code (foundation floor, combat-rules relocation, interior endpoint lift, orbital narrowing). **This story adds the enforcing CI guard** that makes the law executable by failing the build if any upward edge creeps in.

## Technical Approach

Write a ~20-line AST/grep CI guard in `tests/test_import_direction.py` that:

1. **Scans modules under `sidequest/{foundation,game,genre,orbital,magic,interior}/`** for import statements.
2. **Detects upward edges** — any `import sidequest.server` or `from sidequest.server import ...` — and reports the file + line number.
3. **Fails the test** if any upward edge is found; otherwise passes.
4. **Runs as part of the standard test suite** (`pytest tests/`).

The guard should be simple enough to read at a glance (no `import-linter` dependency, consistent with ADR-088's "the script is the schema" stance). It is the wiring test that verifies the layering law is executable rather than aspirational.

### Implementation Details

- Write the test to scan the filesystem directly (glob patterns) or use `ast` module to parse Python files.
- Report offending imports with file path + line number so developers can see exactly what to fix.
- The test should PASS now because 122-1..122-4 have already removed the offending edges.
- If any upward edge is discovered, the test fails with a clear message pointing to the violation.

## Acceptance Criteria

1. ✓ CI guard test exists in `tests/test_import_direction.py`.
2. ✓ Guard scans all domain packages (`foundation`, `game`, `genre`, `orbital`, `magic`, `interior`) for imports from `sidequest.server`.
3. ✓ Guard FAILS with a clear error message listing the file + line if any upward import is found.
4. ✓ Guard PASSES (no output) if no upward imports are detected.
5. ✓ Test runs as part of `pytest tests/` (standard test suite).
6. ✓ Code is readable + documented in ~20 lines (no external dependencies like `import-linter`).
7. ✓ Tree is clean (no other changes).

## Delivery Findings

No upstream findings — 122-1..122-4 completed with no upward-import violations detected.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Conflict** (non-blocking): One live upward edge remains that ADR-147 names but never scheduled a move for — `game/projection/validator.py` lazily imports `_KIND_TO_MESSAGE_CLS` from `sidequest.server.session_handler` (two in-method imports, lines 37 & 108). ADR-147 lists this in its *diagnosis* ("the smell that proves the layering is dishonest … `projection/validator.py` does the same with `server.session_handler`") but it is absent from the §Decision moves table and the 5-step §Implementation Plan. The guard grandfathers it by exact (file, target) pair so 122-5 lands *enforcing* against all other edges today. Recommended follow-up: relocate `_KIND_TO_MESSAGE_CLS` (defined in `server/session_handler.py`; also consumed by `server/emitters.py`) down to the `protocol/` tier — its values are all `sidequest.protocol.*` message classes, so the dict has no genuine server dependency. Affects `sidequest/game/projection/validator.py`, `sidequest/server/session_handler.py`, `sidequest/server/emitters.py` (move the dict down + repoint three importers). Once moved, the `GRANDFATHERED` entry's self-expiry test (`test_grandfathered_exceptions_are_still_live`) will fail until the exception is deleted — by design. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (non-blocking): The guard's AST scan only matches absolute `sidequest.server[.*]` import targets; relative (`from ..server import X`) and dynamic (`importlib.import_module`/`__import__`) upward imports evade it. The relative-import gap is the blocking review finding (REJECTED — see Reviewer Assessment); the dynamic-import gap is an accepted, to-be-documented limitation. Affects `sidequest-server/tests/infrastructure/test_import_direction_guard.py` (resolve `node.level > 0` ImportFrom to absolute before matching; note the dynamic-import limitation in the docstring). *Found by Reviewer during code review.*
- **Improvement** (non-blocking, round 2): Three LOW guard-hardening polish items surfaced during re-review and APPROVED as non-blocking — fold into the **122-6** ADR-147 honesty follow-up (which already touches this area): (1) `_resolve_relative` guard `drop > len` → `drop >= len` so root-escaping relatives return `None` uniformly (verified nil impact — root-escapes aren't real `sidequest.server` edges); (2) add `except OSError` to `_parse_module` so broken-symlink/unreadable `.py` files fail loud *legibly* per its docstring; (3) `assert SIDEQUEST_PKG.name == "sidequest"` at module load to catch a misresolved editable/`.pth` install. All three are fail-safe (red, never a false green). Affects `sidequest-server/tests/infrastructure/test_import_direction_guard.py`. *Found by Reviewer during code review (round 2).*

## Impact Summary

**Upstream Effects:** 1 findings (1 Gap, 0 Conflict, 0 Question, 0 Improvement)
**Blocking:** None

- **Gap:** The guard's AST scan only matches absolute `sidequest.server[.*]` import targets; relative (`from ..server import X`) and dynamic (`importlib.import_module`/`__import__`) upward imports evade it. The relative-import gap is the blocking review finding (REJECTED — see Reviewer Assessment); the dynamic-import gap is an accepted, to-be-documented limitation. Affects `sidequest-server/tests/infrastructure/test_import_direction_guard.py`.

### Downstream Effects

- **`sidequest-server/tests/infrastructure`** — 1 finding

### Deviation Justifications

2 deviations

- **Guard reports file + import targets, not file + line number**
  - Rationale: Matches the established sibling guard `tests/foundation/test_foundation_floor_122_1.py`, which reports file→targets and which the ADR says 122-5 "generalises." The dotted target (e.g. `sidequest.server.session_handler._KIND_TO_MESSAGE_CLS`) is more actionable than a bare line number for locating the offending symbol, and `ast.walk` discards line numbers in the aggregation. Verified the message is clear via a synthetic violation (named the file + both targets).
  - Severity: trivial
  - Forward impact: none — cosmetic message-shape choice, no downstream assumptions.
- **Grandfathered exception for `game/projection/validator.py`**
  - Rationale: That edge is real and live but ADR-147 deliberately scoped it out of its moves (see the Conflict delivery finding). Relocating `_KIND_TO_MESSAGE_CLS` is genuine cross-module design work beyond a 2pt guard story and beyond the ADR's sanctioned scope. A documented, exact-pinned, self-expiring exception lands the guard enforcing now (prevents all *new* edges) without an out-of-scope refactor or an xfail that would contradict "lands last + enforcing." Not a silent fallback — the exception is loud, tested, and routed to a follow-up.
  - Severity: minor
  - Forward impact: minor — a follow-up story (per the delivery finding) removes the edge and must delete the `GRANDFATHERED` entry; the self-expiry test enforces that deletion.

## Design Deviations

### Dev (implementation)
- **Guard reports file + import targets, not file + line number**
  - Spec source: context-story-122-5.md / session ACs, AC-3
  - Spec text: "Guard FAILS with a clear error message listing the file + line if any upward import is found."
  - Implementation: Failure message lists `{package-relative path: [offending dotted import targets]}` rather than line numbers.
  - Rationale: Matches the established sibling guard `tests/foundation/test_foundation_floor_122_1.py`, which reports file→targets and which the ADR says 122-5 "generalises." The dotted target (e.g. `sidequest.server.session_handler._KIND_TO_MESSAGE_CLS`) is more actionable than a bare line number for locating the offending symbol, and `ast.walk` discards line numbers in the aggregation. Verified the message is clear via a synthetic violation (named the file + both targets).
  - Severity: trivial
  - Forward impact: none — cosmetic message-shape choice, no downstream assumptions.

- **Grandfathered exception for `game/projection/validator.py`**
  - Spec source: session scope (story title), AC-3
  - Spec text: "fail on any domain->server upward import (foundation/game/genre/orbital/magic/interior); lands last + enforcing"
  - Implementation: Guard enforces against every edge except one pinned (file, target) grandfather entry for validator.py's `_KIND_TO_MESSAGE_CLS` import.
  - Rationale: That edge is real and live but ADR-147 deliberately scoped it out of its moves (see the Conflict delivery finding). Relocating `_KIND_TO_MESSAGE_CLS` is genuine cross-module design work beyond a 2pt guard story and beyond the ADR's sanctioned scope. A documented, exact-pinned, self-expiring exception lands the guard enforcing now (prevents all *new* edges) without an out-of-scope refactor or an xfail that would contradict "lands last + enforcing." Not a silent fallback — the exception is loud, tested, and routed to a follow-up.
  - Severity: minor
  - Forward impact: minor — a follow-up story (per the delivery finding) removes the edge and must delete the `GRANDFATHERED` entry; the self-expiry test enforces that deletion.

### Dev (rework round 1)
- No new deviations from spec. The round-1 changes implement the Reviewer's required fixes (relative-import resolution, fail-loud parse) and the accepted documented limitation (dynamic imports) — these tighten the guard toward the AC ("fail on **any** upward import"), they do not diverge from it.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Reviewer (audit)
- **Guard reports file + import targets, not file + line number** → ✓ ACCEPTED by Reviewer: a file→targets map is more actionable than a bare line number for a layering guard, matches the merged 122-1 sibling, and satisfies AC-3 ("clear error message listing the file"). Verified the assertion message names the file + offending dotted targets (`test_no_upward_imports_beyond_grandfathered`, lines 178–184; Dev's synthetic-violation run).
- **Grandfathered exception for `game/projection/validator.py`** → ✓ ACCEPTED by Reviewer: the edge is real and ADR-147 explicitly scopes it out of its §Decision moves table and §Implementation Plan (verified against the ADR); the exception is loud, exact-pinned, and self-expiring (`test_grandfathered_exceptions_are_still_live`). Relocating `_KIND_TO_MESSAGE_CLS` is out of scope for a 2pt guard story and correctly routed to a follow-up delivery finding. This is the honest call, not a silent fallback.

### Reviewer (audit — round 2)
- **Dev (rework round 1): "No new deviations from spec"** → ✓ ACCEPTED by Reviewer: confirmed — the round-1 rework implements my required fixes (relative-import resolution, fail-loud parse) and the accepted documented dynamic-import limitation. These tighten the guard toward the AC ("fail on any upward import"); they do not diverge from spec. No undocumented deviations spotted in the rework diff.

## Sm Assessment

Setup complete and ready for Dev (Hephaestus).

- **Story:** 122-5 — the final, *enforcing* step of epic 122 (ADR-147 Honest Layering). 2pt trivial/refactor.
- **Dependencies:** 122-1..122-4 all `done` — the upward import edges they targeted are already removed, so the guard lands green/enforcing rather than red.
- **Scope:** Add a CI guard (pytest-based, no `import-linter` dependency) that fails on any upward import from `sidequest.{foundation,game,genre,orbital,magic,interior}` into `sidequest.server`. Import-direction law: `foundation ← {game,genre,orbital,magic,interior} ← server`.
- **Repo/branch:** sidequest-server @ `feat/122-5-ci-guard-domain-server-import` (off `develop`).
- **Wiring note (CLAUDE.md):** the guard IS the wiring test for the epic — it must run in the standard `pytest tests/` path so CI enforces the law going forward.
- **Merge-gate housekeeping:** cleared a stale open PR (#893, story 114-12 already `done`) by squash-merging it — user-authorized — before setup.

Next: Dev implements the guard, verifies it passes against current `develop`, and confirms it fails on a synthetic upward-import fixture.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `tests/infrastructure/test_import_direction_guard.py` (new) — enforcing CI guard for the ADR-147 import-direction law. AST scan (`ast.walk`, catches lazy in-method imports) over `sidequest/{foundation,game,genre,orbital,magic,interior}`; fails on any import of `sidequest.server[.*]`. Three tests: the law (`test_no_upward_imports_beyond_grandfathered`), a non-vacuity/coverage guard (`test_guarded_tiers_exist_and_have_modules`), and a self-expiry check on the one grandfathered exception (`test_grandfathered_exceptions_are_still_live`).

**Tests:** 3/3 passing (GREEN). Negative case verified out-of-band: a synthetic `game/_tmp_122_5_violation.py` importing `sidequest.server.session` made the guard FAIL with a clear file→targets message; the temp file was removed (tree clean). `ruff check` passes.

**Branch:** `feat/122-5-ci-guard-domain-server-import` (pushed to origin).

**Acceptance criteria:** 1✓ (test exists in `tests/`), 2✓ (scans all six tiers), 3✓ (fails with clear message — see deviation re: targets-not-line-numbers), 4✓ (passes when clean), 5✓ (lives under `tests/infrastructure/`, collected by the default `pytest tests/` run), 6✓ (readable, no `import-linter` dep), 7✓ (tree clean).

**Notable:** One residual upward edge (`game/projection/validator.py`) is grandfathered with a documented, self-expiring exception — see the Conflict delivery finding and Design Deviations. The guard is enforcing against every other edge.

**Handoff:** To review (Hermes Psychopompos).

## Subagent Results (round 1 — superseded)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (3/3 pass, ruff clean, tree clean) | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 9 (3 high, 2 med, 4 low/handled) | confirmed 3, dismissed 0, deferred 0 |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | findings | 3 (1 med, 2 low) | confirmed 0, dismissed 1, deferred 0 (2 folded into robustness finding) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (3 enabled returned; 6 disabled via settings)
**Total findings:** 3 confirmed (1 High, 1 Medium, 1 Low), 1 dismissed (with rationale)

### Rule Compliance

Rules enumerated against the single changed file (`tests/infrastructure/test_import_direction_guard.py`, a test):

- **No Silent Fallbacks** (CLAUDE.md) — `_scan_tier` returns `{}` for a missing tier dir (a local silent skip), BUT `test_guarded_tiers_exist_and_have_modules` (lines 156–161) fails loud if any of the six tiers is missing or empty, closing the gap. COMPLIANT. Residual: `ast.parse`/`read_text` (lines 134, 200) raise an opaque `SyntaxError`/`UnicodeDecodeError` on a malformed file instead of a clear ADR-147 message — still loud, but a poor failure mode. Flagged MEDIUM (not a rule violation; a robustness gap).
- **No Stubbing** (CLAUDE.md) — three real assertions, no placeholder/skeleton code. COMPLIANT.
- **Every Test Suite Needs a Wiring Test** (CLAUDE.md) — this guard IS the wiring test for layer direction (ADR-147 §Enforcement); the coverage test prevents a vacuous green. COMPLIANT.
- **No Source-Text Wiring Tests** (CLAUDE.md) — the test reads production source via `read_text` + `ast.parse`. Examined closely: the rule targets *call-site/wiring-shape* assertions ("assert `_fn(` appears N times") and regex-DOTALL ReDoS that hangs the GIL. This is an architectural *import-direction invariant* using `ast` (no regex, no backtracking), explicitly sanctioned by ADR-147 §Enforcement ("a ~20-line AST/grep test in tests/ is sufficient, no import-linter dependency") and precedented by the already-merged 122-1 foundation guard (`tests/foundation/test_foundation_floor_122_1.py`) which uses identical AST scanning. COMPLIANT — the rule does not govern this artifact. (See the dismissed [SEC] finding.)
- **OTEL Observability** (CLAUDE.md) — N/A: test-only change, no runtime subsystem decision; CLAUDE.md exempts test/cosmetic changes.

### Observations

- [HIGH] **Relative-import upward edges evade the guard.** `from ..server import X` / `from .. import server` inside a guarded tier are `ast.ImportFrom` nodes whose `node.module` is the *relative* suffix (`"server"` or `None`), never `"sidequest.server"`, so `_record` never matches and the file passes. The story's contract is "fail on **any** domain->server upward import" and ADR-147's stated value is "regression structurally impossible" — an entire upward-import spelling is uncaught, so the guarantee is not structural. `tests/infrastructure/test_import_direction_guard.py:116-124`. [EDGE] confirmed.
- [MEDIUM] **Parse errors crash the suite opaquely.** `ast.parse(path.read_text(encoding="utf-8"))` (line 134; also line 200) has no `SyntaxError`/`UnicodeDecodeError` handling — a WIP/malformed/non-UTF-8 `.py` file under any tier aborts the run with an unrelated traceback instead of a clear ADR-147 layering report. Loud but unhelpful; worth a try/except → `pytest.fail(path)`. [EDGE] confirmed.
- [LOW] **Dynamic imports are invisible.** `importlib.import_module("sidequest.server")` / `__import__` appear as `ast.Call`, not import nodes, so they slip past. Genuinely lower likelihood; accept as a documented limitation rather than block. [EDGE] confirmed (downgraded).
- [VERIFIED] **The realistic threat IS caught and the guard is GREEN.** `from sidequest.server import X`, `import sidequest.server as s`, and `from sidequest import server` all resolve to a `sidequest.server*` target — evidence: lines 117–123; corroborated by Dev's synthetic-violation run (failed, naming file + both targets). The codebase has **0** relative imports across all six tiers (grep), so the guard is correct for the code as it stands today.
- [VERIFIED] **Self-expiry of the grandfather works.** `test_grandfathered_exceptions_are_still_live` (lines 193–211) fails the instant `validator.py` stops importing the pinned target, forcing the exception's deletion — no rotting allowlist. Loud + tested (complies with No Silent Fallbacks). evidence: lines 204–211.
- [VERIFIED] **Non-vacuity guard present.** `test_guarded_tiers_exist_and_have_modules` (lines 156–161) fails if a tier is renamed/removed or empty. Prevents a false green. evidence: lines 158–161.
- [SEC] **Dismissed** — "No Source-Text Wiring Tests" flagged at line 134. Dismissed: ADR-147 §Enforcement explicitly authorizes an AST/grep test for this exact purpose; the rule's scope is call-site/wiring-shape assertions + regex ReDoS (neither applies — `ast`, no regex), and the merged 122-1 sibling sets precedent. The two low-confidence security items (unhandled `SyntaxError`; assert `SIDEQUEST_PKG.name == "sidequest"`) are robustness, folded into the MEDIUM finding above — not security defects (no external input, no shell-out, no eval).
- Disabled specialists — [SILENT]/[TEST]/[DOC]/[TYPE]/[SIMPLE]/[RULE]: not spawned (settings). I performed the rule enumeration myself (see Rule Compliance) and checked the one silent-return path by hand.

### Devil's Advocate

Assume this guard is broken and gives false confidence. The most damning case: it is an *enforcement* artifact whose marketing ("fail on any upward import", "regression structurally impossible") exceeds its actual coverage. A future developer, deep in `sidequest/game/`, wanting `_KIND_TO_MESSAGE_CLS` or some new server helper, writes `from ..server.session_handler import _KIND_TO_MESSAGE_CLS`. isort (ruff `I`) tidies it; ruff does not ban relative imports (no `TID` in `select`); the guard stays green because `node.module` is `"server.session_handler"`, not `"sidequest.server.session_handler"`. The exact layering violation the epic exists to prevent ships, and the green checkmark actively *hides* it — worse than no guard, because the team now trusts it. A second route: `importlib.import_module("sidequest.server")` for a genuinely dynamic need — also green. A third: someone drops a half-written `.py` (merge-conflict markers, a new-syntax feature) into `game/`; instead of a crisp layering report, CI vomits a `SyntaxError` traceback from a test named "import_direction_guard", and the next engineer wastes twenty minutes deciding whether they broke the layering law or just have a typo — the guard fails for a reason unrelated to its purpose. A confused user misreads the grandfather block as "validator.py is allowed to reach into server forever" and copies the pattern. A stressed filesystem with a latin-1-encoded vendored file under a tier produces a `UnicodeDecodeError`, again unrelated to layering. None of these corrupt data, but for a guard whose only job is *completeness of enforcement*, an enforcement hole is the defect. The relative-import gap is high-confidence, AC-relevant ("any"), and ~10 lines to close (resolve `node.level` to the absolute module path before matching). Shipping the capstone with that hole, when the author is in the loop, is the wrong trade. That uncovered class is added as the blocking finding; the parse-robustness gap rides along in the same pass; dynamic imports are accepted as a documented limitation.

## Reviewer Assessment (round 1 — REJECTED, superseded by round 2 below)

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | Relative-import upward edges (`from ..server import X`, `from .. import server`) evade the AST scan — `node.module` is the relative suffix, not `sidequest.server`, so they never match. Defeats the "fail on **any** upward import" contract / ADR-147 "structurally impossible to regress." | `tests/infrastructure/test_import_direction_guard.py:116-124` | In `_server_import_targets`, when `node.level > 0` resolve the relative `ImportFrom` to its absolute dotted path before calling `_record` (compute the importing file's package depth from `SIDEQUEST_PKG` and join with `node.module`). Add a fixture/parametrized assertion proving a relative `from ..server import x` under a tier is detected. |
| [MEDIUM] | `ast.parse(path.read_text(...))` has no error handling — a malformed or non-UTF-8 `.py` file under any tier crashes the suite with an opaque traceback instead of a clear layering failure. | `tests/infrastructure/test_import_direction_guard.py:134,200` | Wrap parse/read in `try/except (SyntaxError, UnicodeDecodeError)` and `pytest.fail()` naming the offending file (keeps the failure actionable and loud, per No Silent Fallbacks). |

**Accepted as documented limitation (non-blocking):** dynamic imports (`importlib.import_module`/`__import__`) are out of reach for a static AST scan — note this explicitly in the module docstring rather than chasing `ast.Call` literals.

**Subagent tag coverage:** [EDGE] 3 confirmed (1 High, 1 Medium, 1 Low) · [SEC] 1 dismissed (rationale above) + 2 robustness folded into MEDIUM · [SILENT]/[TEST]/[DOC]/[TYPE]/[SIMPLE]/[RULE] not spawned (disabled via settings; rule enumeration performed by Reviewer).

**Data flow traced:** source `.py` file under a guarded tier → `read_text` → `ast.parse` → `ast.walk` → `_record` filters `sidequest.server*` targets → set-difference against `GRANDFATHERED` → assertion. Safe for absolute imports; the relative branch never reaches `_record` with a matchable string (the High finding).

**Pattern observed:** AST-based static import guard, consistent with the merged 122-1 sibling — good pattern, incomplete instance.

**Error handling:** unguarded `ast.parse`/`read_text` (MEDIUM finding).

**Handoff:** Back to Dev (Hephaestus) for fixes — testable logic/edge-case changes.

## Dev Rework Assessment (round 1)

**Rework Complete:** Yes — all blocking findings addressed.

**Findings resolved:**
- **[HIGH] Relative-import evasion** — FIXED. `_server_import_targets` now takes the importing module's package (`_package_parts_for`) and resolves relative `ImportFrom` nodes to absolute paths (`_resolve_relative`) before matching. `from ...server import x` / `from .. import server` are caught; sibling resolutions (`from ..server` → `sidequest.game.server`) correctly do **not** false-positive; over-deep relatives resolve to `None` without crashing. **Verified end-to-end:** a synthetic `from ...server import session_handler` under `sidequest/game/` was caught by the full-codebase scan (named the file + both resolved targets), then removed.
- **[MEDIUM] Opaque parse crash** — FIXED. New `_parse_module` wraps `read_text`/`ast.parse` and `pytest.fail()`s with the offending file's path on `SyntaxError`/`UnicodeDecodeError` instead of an unrelated traceback (fail loud *and* legibly).
- **Dynamic imports (accepted limitation)** — documented in the module docstring and `_server_import_targets` as out-of-scope for a static AST scan.

**Files Changed:** `tests/infrastructure/test_import_direction_guard.py` (resolver + parse-robustness + docstring; +5 resolver unit tests).

**Tests:** 8/8 passing (GREEN) — was 3, added `test_relative_import_reaching_server_is_detected`, `test_relative_bare_import_reaching_server_is_detected`, `test_relative_import_to_sibling_is_not_a_false_positive`, `test_overdeep_relative_import_does_not_crash`, `test_package_parts_for_handles_init_and_module`. `ruff check` clean. Tree clean.

**Branch:** `feat/122-5-ci-guard-domain-server-import` (pushed — commit 523267e1).

**Handoff:** Back to review (Hermes Psychopompos).

## Subagent Results

(Round 2 — re-review of the rework. Same three subagents enabled; six disabled via settings.)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (8/8 pass, ruff clean, tree clean) | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 3 (2 med-confidence, 1 high-confidence "add a test"); confirmed both round-1 fixes correct | confirmed 3 as LOW-impact non-blocking, dismissed 0, deferred 0 |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | findings | 2 (both low) | confirmed 2 as LOW non-blocking, dismissed 0 |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (3 enabled returned; 6 disabled via settings)
**Total findings:** 0 blocking; 3 LOW non-blocking (off-by-one boundary, OSError robustness, SIDEQUEST_PKG identity assert) routed to the 122-6 follow-up. Both round-1 blockers (relative-import evasion, opaque parse crash) verified FIXED.

### Rule Compliance (round-2 delta)

- **No Silent Fallbacks** — `_parse_module` now `pytest.fail()`s with the file path on `SyntaxError`/`UnicodeDecodeError` (lines 193, 197): fail loud + legible. COMPLIANT. Residual: `OSError`/broken-symlink path is uncaught (still fails loud as a test error, just less legibly) — LOW finding below.
- **No Source-Text Wiring Tests** — unchanged; `ast`-based, no regex. COMPLIANT (per round-1 ADR-147 §Enforcement authorization).
- All other rules: unchanged from round 1.

### Observations (round 2)

- [VERIFIED] **[HIGH round-1] relative-import evasion is FIXED.** `_server_import_targets` now resolves relative `ImportFrom` via `_package_parts_for` + `_resolve_relative` (lines 106–179). Verified by my own trace: `from ..server` in `sidequest.game` and `from ...server` in `sidequest.game.projection` both resolve to `sidequest.server` (caught); `from ..server` in `sidequest.game.projection` → `sidequest.game.server` (sibling, correctly NOT flagged). Confirmed by edge-hunter ("cannot evade by switching spelling") and the 5 new resolver unit tests (all green). [EDGE]
- [VERIFIED] **[MEDIUM round-1] opaque parse crash is FIXED.** `_parse_module` (lines 182–198) catches `SyntaxError`/`UnicodeDecodeError` → `pytest.fail(file)`. `pytest.fail` raises `Failed` (an exception) that propagates correctly through the helper to the test boundary. [EDGE][SEC]
- [LOW] **Off-by-one at the `drop == len(package_parts)` boundary.** `_resolve_relative` guards `drop > len` (line 130) but `drop == len` returns a bare name (e.g. `"server"`) instead of `None`. **Impact verified nil for the guard's job:** the only imports affected are root-escaping relatives (`from ...server` in `sidequest.game`) which Python rejects as "beyond top-level package" and which do NOT denote `sidequest.server` — every *reachable* upward edge is still caught (traced live). Tidy fix: `>` → `>=` so root-escapes return `None` uniformly (matching the `test_overdeep_relative_import_does_not_crash` intent). [EDGE] confirmed, non-blocking.
- [LOW] **`_parse_module` leaves `OSError` uncaught** (line 191). A broken symlink / unreadable `.py` under a tier raises `FileNotFoundError`/`PermissionError` → opaque traceback, contradicting the helper's own fail-loud-*legibly* docstring. Still fails loud (test errors red — no false green), just less legibly. Uncommon trigger. Fix: add `except OSError`. [EDGE] confirmed, non-blocking.
- [LOW] **`SIDEQUEST_PKG` identity is unasserted** (line ~65). If `sidequest.__file__` resolves to a stale editable/`.pth` install, the scan could target the wrong tree (false green). CI-environment-dependent, low likelihood. Fix: `assert SIDEQUEST_PKG.name == "sidequest"` at module load. [SEC] confirmed, non-blocking. (Round-1 note, unregressed.)
- [SEC] info-leakage (line 198): `pytest.fail(... {exc})` could embed a source line in CI logs — internal repo, CI-only, low consequence. Noted, non-blocking.
- Disabled specialists — [SILENT]/[TEST]/[DOC]/[TYPE]/[SIMPLE]/[RULE]: not spawned (settings); rule enumeration performed by Reviewer (see Rule Compliance).

### Devil's Advocate (round 2)

Try to break the rework. The resolver is new code added under review pressure — exactly where a subtle bug hides. I found one: the `drop == len` boundary returns `"server"` not `None`. Could that hide a real edge? I traced it live: to reach `sidequest.server` by relative import you go up *to* `sidequest` and *into* `server` — `from ..server` from `sidequest.game` (caught) or `from ...server` from `sidequest.game.projection` (caught). The boundary case is `from ...server` from `sidequest.game`, which Python refuses to import at all ("beyond top-level package") and which semantically is not `sidequest.server`. So the off-by-one cannot conceal a working upward edge; it's cosmetic. Next: could the fail-loud helper swallow a real violation? No — `pytest.fail` raises, it never returns a parsed tree, so a parse failure can never be silently treated as "no imports found" (which would be the dangerous false green). It correctly converts a parse failure into a red test, not a green one. The OSError gap is the one place the helper under-delivers on its docstring, but even there the outcome is a red error, not a hidden pass — the guard fails safe. A confused user reading the grandfather block might still think validator.py is permanently blessed, but the self-expiry test (unchanged, still green) forecloses that. A malicious developer wanting to sneak an upward edge has no remaining cheap spelling: absolute, aliased, `from sidequest import server`, and all reachable relative forms are caught; only `importlib`/`__import__` remain, now explicitly documented as out-of-scope and conspicuous against the absolute-import convention. The residual findings are all fail-safe and low-impact. Nothing here rises to blocking; the capstone is correct and enforcing for every reachable upward import.

## Reviewer Assessment

**Verdict:** APPROVED

**Round-1 blockers — both resolved & verified:**
- [HIGH] relative-import evasion → FIXED (`_resolve_relative`; traced + 5 unit tests + end-to-end synthetic catch).
- [MEDIUM] opaque parse crash → FIXED (`_parse_module` fail-loud).

**Non-blocking (LOW) — routed to the 122-6 ADR-147 honesty follow-up:** off-by-one `>`→`>=` at the root-escape boundary (verified nil impact on reachable edges); `except OSError` in `_parse_module`; `assert SIDEQUEST_PKG.name == "sidequest"`. None block: all fail-safe (red, never a false green), low-likelihood, and the guard catches every reachable upward edge today.

**Subagent tag coverage:** [EDGE] 2 round-1 fixes verified + 2 LOW confirmed · [SEC] 2 LOW confirmed (CI-log hygiene, pkg-identity) · [SILENT]/[TEST]/[DOC]/[TYPE]/[SIMPLE]/[RULE] not spawned (disabled; rule enumeration by Reviewer).

**Data flow traced:** `.py` under a guarded tier → `_parse_module` (fail-loud) → `ast.walk` → relative/absolute resolution → `sidequest.server*` filter → set-difference vs `GRANDFATHERED` → assertion. Fails safe: a parse error becomes a red test, never a silent empty-import pass.

**Pattern observed:** AST static import guard with correct relative-import resolution and a self-expiring grandfather — strong, complete instance now. `tests/infrastructure/test_import_direction_guard.py`.

**Error handling:** `SyntaxError`/`UnicodeDecodeError` handled with legible `pytest.fail`; `OSError` is the one residual (LOW, fail-safe).

**Handoff:** To SM (Themis the Just) for finish-story.