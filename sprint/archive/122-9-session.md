---
story_id: "122-9"
jira_key: ""
epic: "122"
workflow: "trivial"
---
# Story 122-9: Sweep pre-existing ruff I001 import-order debt across 8 server test files (ruff 0.15.11 flags them under uv-locked config; develop server-check currently red independent of any story)

## Story Details
- **ID:** 122-9
- **Jira Key:** none
- **Workflow:** trivial
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-17T09:33:49Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-17T09:21:02.738158Z | 2026-06-17T09:22:59Z | 1m 56s |
| implement | 2026-06-17T09:22:59Z | 2026-06-17T09:28:17Z | 5m 18s |
| review | 2026-06-17T09:28:17Z | 2026-06-17T09:33:49Z | 5m 32s |
| finish | 2026-06-17T09:33:49Z | - | - |

## Sm Assessment

**Scope (trivial chore, server-only, 1pt):** Pre-existing ruff I001 (unsorted-import) debt is making `just server-check` red on `develop` — independent of any story. ruff 0.15.11 under the uv-locked config now flags import-ordering in ~8 server *test* files that predate the lock bump. This story sweeps that debt so the baseline goes green again.

**Why now / ordering:** This is the baseline-greening prerequisite for the rest of epic-122's follow-up work (notably 122-7, the import-direction guard hardening, whose verification runs `server-check`). Clearing I001 first means 122-7 verifies against a clean tree instead of fighting unrelated red.

**Technical approach for Dev (Hephaestus):**
- Identify offenders: `cd sidequest-server && uv run ruff check . --select I001` (or `just server-lint`).
- Fix import order with `uv run ruff check --fix --select I001` on the flagged files. Import-order only — no production-logic changes, no behavioral edits.
- **Do NOT run a bare repo-wide `ruff format .`** — known to reformat ~167 files and displace `noqa F811`. Touch only the files ruff actually flags.
- Verify green: `just server-check` (lint + test) must pass. Note the known pre-existing OTEL deadlock — if the full parallel test run hangs on the ~18 span-count tests, run those files serially with `-n0` (that's a separate, pre-existing condition, not this story's regression).
- Note: WWN-content fixture failures (~13) are a separate pre-existing condition vs current content `develop` — classify as pre-existing, do not attempt to fix here.

**Branch/base:** server targets `develop`; branch `feat/122-9-ruff-i001-test-import-order-sweep` is cut from develop. No Jira (YAML sprint).

**Risk:** Very low — mechanical lint sweep, no logic change. The only trap is over-scoping the format command; the guardrail above prevents it.

**Next:** 122-7 (import-direction guard hardening) is queued behind this and will be set up after 122-9 merges + finishes.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed (all `sidequest-server`, import-order/import-source only):**
- `tests/agents/test_unseeded_objective_classifier.py` — I001
- `tests/foundation/test_foundation_floor_122_1.py` — I001
- `tests/game/test_builder_arrange_visible.py` — I001
- `tests/game/test_fate_gear_model.py` — I001
- `tests/server/dispatch/test_room_creature_binding_107_2.py` — I001
- `tests/server/test_fate_state_emit.py` — I001
- `tests/server/test_fate_state_emit_wiring.py` — I001
- `tests/server/test_dice_throw_auth_bypass_118_9.py` — UP035 (`typing.Iterator` → `collections.abc.Iterator`)

**Lint:** `uv run ruff check .` → *All checks passed* (was red on develop — the story's target red). No production-logic or test-behavior edits.
**Tests:** 82/82 GREEN across the 8 touched files (`pytest -n0`, RUN_ID `122-9-dev-green`). Full-suite pre-existing failures (WWN content fixtures ~13, MessageType count 54-vs-55, OTEL span-count deadlock) are out of scope per the Sm Assessment and cannot be affected by an import-order-only change.
**Branch:** `feat/122-9-ruff-i001-test-import-order-sweep` (pushed to origin)

**Handoff:** To review — Hermes Psychopompos.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean (GREEN) | none (lint clean, 82/82, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 1 medium, 1 low | dismissed 2 (line-level rationale) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (3 enabled returned — preflight clean, security clean, edge-hunter 2 findings both dismissed with line-level evidence; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 0 confirmed, 2 dismissed (with rationale), 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

**Scope:** Pure ruff lint sweep across 8 server *test* files — I001 import-order in 7 files + one UP035 `typing.Iterator`→`collections.abc.Iterator` swap in the 8th. `git diff develop...HEAD` = +11/−15, entirely within import blocks. No production code, no test logic, no assertions touched.

**Data flow traced:** N/A — no user input or runtime data path in the diff (test-module import reordering only). Noted explicitly rather than skipped.
**Wiring:** N/A — no UI→backend connections; test files are not wired into production paths. The one wiring *test* affected (`test_fate_state_emit_wiring.py`) had only its import order changed; its `wired is _maybe_emit_fate_state` assertion is untouched and passes.
**Tenant isolation audit:** N/A — no trait methods, no structs with tenant fields, no data handling in the diff.
**Error handling:** N/A — no error-handling code in the diff.

### Observations (tagged by source)
- [VERIFIED] Change is purely import-order/source — evidence: `git diff develop...HEAD` shows only reordered `from … import` lines, blank-line removals inside import blocks, and one `Iterator` source swap; no logic, no assertion, no fixture changes. Complies with the "format only branch-touched files" guardrail (no bare `ruff format .`; diff is 8 files, not ~167).
- [EDGE] (DISMISSED, was medium) edge-hunter flagged that `monster_manual_inject` now imports *before* `room_creature_binding` at `test_room_creature_binding_107_2.py:39`, hypothesizing an import-time registry coupling. Dismissed with evidence: `sidequest/server/dispatch/__init__.py` is intentionally empty (its docstring states so — no import-time registration); `room_creature_binding.py` has no module-level side effects beyond a class + function def and imports only `sidequest.telemetry.spans` (not `monster_manual_inject`); the two are independent submodules of the same package whose empty `__init__` runs on first touch regardless of order. Decisive: the module imports cleanly and all 82 touched-file tests pass — an import-time ordering break would fail at collection.
- [EDGE] (DISMISSED, low) blank-line removal at `test_foundation_floor_122_1.py:59` — cosmetic; the `# noqa: E402` stays attached to `import sidequest`; edge-hunter itself concluded "no action required."
- [SEC] security subagent returned clean — no auth/secret/data-path surface; `test_dice_throw_auth_bypass_118_9.py` assertions untouched, only the `Iterator` import source changed (verified against diff).
- [SIMPLE] No complexity added — the change net-removes lines (drops intra-block blank lines, consolidates import groups); UP035 swap is the canonical modern source. (simplifier disabled — assessed directly.)
- [TEST] No behavioral test change; preflight confirms 82/82 GREEN on touched files, 0 skips, 0 TODOs; no assertion edits in diff. (test_analyzer disabled — assessed directly.)
- [DOC] `# RED:` and `# noqa: E402` comments remain correctly attached to their statements after the reorder; no public-API docs affected (test files). (comment_analyzer disabled — assessed directly.)
- [TYPE] `collections.abc.Iterator` is the type-checker-canonical source for `Iterator` (PEP 585 / ruff UP035); no other type surface in diff. (type_design disabled — assessed directly.)
- [SILENT] No error-handling or fallback code in the diff; nothing swallowed or silently defaulted. (silent_failure_hunter disabled — assessed directly.)
- [RULE] Compliant with project rules — "No Silent Fallbacks" (no fallback logic touched), "No Stubbing" (no stubs), and the server-format-drift guardrail (flagged-files-only fix, no mass reformat). (rule_checker disabled — assessed directly.)

### Rule Compliance
- **"No Silent Fallbacks" (CLAUDE.md):** N/A to diff content; no fallback path added or removed — compliant.
- **"No Stubbing" (CLAUDE.md):** no placeholder/stub code introduced — compliant.
- **"Server ruff format drift — format only branch-touched files" (memory):** COMPLIANT — Dev applied `ruff check --fix` to the 8 flagged files only and did NOT run bare `ruff format .`; the diff touches exactly 8 files, confirming no mass reformat / no `noqa F811` displacement.
- **"No content in unit tests" (memory):** N/A — no new tests or content fixtures added; only import order changed.
- SOUL.md narration/gameplay rules: N/A — no narrator/engine code in diff.

### Devil's Advocate
Suppose this "trivial" sweep is actually broken. The strongest attack is import-ordering: ruff's isort reordered side-effecting imports, and Python import side effects are order-sensitive — if `room_creature_binding` registered a decorator into a dispatch registry that `monster_manual_inject` reads at import time, reversing their order would silently load a half-built registry and the test would assert against stale state rather than crash. A second attack: the `# noqa: E402` files deliberately place imports after `sys.path`/discovery code; if isort hoisted a `sidequest.*` import above the path-manipulation it depends on, the import would resolve against the wrong path or `ImportError`. A third: the UP035 swap — what if some code introspects `Iterator.__module__` and branches on `typing` vs `collections.abc`? A fourth: a confused future maintainer reads the reordered block and assumes the new order encodes a dependency that isn't there. Refuting each: (1) `dispatch/__init__.py` is empty by design and `room_creature_binding.py` registers nothing at module scope — verified by reading both; no registry exists to half-build. (2) The path-discovery import (`import sidequest` in `test_foundation_floor_122_1.py`) kept its position and its `# noqa: E402`; ruff did not hoist it above the geography comment — only an adjacent blank line was removed. (3) `Iterator` is re-exported identically; nothing in the touched tests introspects `__module__`, and `ruff check` (which enforces UP035) is green. (4) The reordered order is ruff's canonical isort output — the maintainer's tool will agree with it, not be misled. The decisive, attack-proof fact: the full `ruff check .` is clean and all 82 tests in the touched files pass, so any import-time breakage would already have surfaced as a collection error. No attack survives.

**Handoff:** To SM (Themis the Just) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

### Dev (implementation)
- **Improvement** (non-blocking): 3 of the 8 touched files carry pre-existing `ruff format` drift — line-wrapping in non-import code (frozenset literals, multi-line asserts, call args), NOT import-related and NOT flagged by `ruff check`/`server-check`. Left untouched to avoid scope creep per the format-drift guardrail (bare `ruff format .` is hazardous; format only branch-touched files). Affects `tests/foundation/test_foundation_floor_122_1.py`, `tests/game/test_builder_arrange_visible.py`, `tests/server/test_fate_state_emit_wiring.py` (would only matter if the team ever gates on `ruff format --check`). *Found by Dev during implementation.*

### Reviewer (code review)
- No upstream findings during code review. (The Dev-noted pre-existing `ruff format` drift in 3 files is real but correctly out of scope — `server-check` runs `ruff check` + tests, not `ruff format --check` — and was rightly left untouched per the format-drift guardrail.) *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

1 deviation

- **Expanded the lint sweep from I001 to also clear one UP035 error in the 8th test file**
  - Rationale: The story's stated goal is greening `server-check` (= `ruff check .` + tests). Only 7 files have `I001`; the 8th had `UP035`, and that error also kept `ruff check .` red. Fixing only I001 would have left server-check red, failing the story's own goal. "8 server test files" in the title matches 7 I001 + 1 UP035 exactly. Same class of pre-existing test-lint debt, same baseline.
  - Severity: minor
  - Forward impact: none — `collections.abc.Iterator` is the canonical, functionally identical import; no sibling story depends on this.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

### Dev (implementation)
- **Expanded the lint sweep from I001 to also clear one UP035 error in the 8th test file**
  - Spec source: `.session/122-9-session.md` story title (scope) + Sm Assessment
  - Spec text: "Sweep pre-existing ruff I001 import-order debt across **8 server test files** … develop server-check currently red independent of any story"
  - Implementation: Auto-fixed a `UP035` (`from typing import Iterator` → `from collections.abc import Iterator`) in `tests/server/test_dice_throw_auth_bypass_118_9.py` — the 8th flagged test file — in addition to the 7 `I001` files.
  - Rationale: The story's stated goal is greening `server-check` (= `ruff check .` + tests). Only 7 files have `I001`; the 8th had `UP035`, and that error also kept `ruff check .` red. Fixing only I001 would have left server-check red, failing the story's own goal. "8 server test files" in the title matches 7 I001 + 1 UP035 exactly. Same class of pre-existing test-lint debt, same baseline.
  - Severity: minor
  - Forward impact: none — `collections.abc.Iterator` is the canonical, functionally identical import; no sibling story depends on this.

### Reviewer (audit)
- **Dev's "Expanded the lint sweep from I001 to also clear one UP035 error in the 8th test file"** → ✓ ACCEPTED by Reviewer: sound and necessary. The story's stated goal is greening `ruff check .`/`server-check`; the UP035 in `test_dice_throw_auth_bypass_118_9.py` was part of the same red baseline, so fixing only I001 would have left server-check red and failed the story's own goal. `collections.abc.Iterator` is the canonical source (UP035 is a ruff autofix, functionally identical), and "8 server test files" in the title matches 7 I001 + 1 UP035 exactly. No undocumented deviations found — diff is fully accounted for by the two logged scopes.