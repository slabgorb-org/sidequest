---
story_id: "159-4"
jira_key: ""
epic: "159"
workflow: "tdd"
---
# Story 159-4: Companion package core — intent, manifest, persona, dice, protocol, brain, actuation

## Story Details
- **ID:** 159-4
- **Epic:** 159 (Companion Seat — full-PC AI companion over WS)
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 4
- **Type:** feature

## Story Context

A full-PC AI companion (Donut-to-your-Carl) that joins a live session as its own WebSocket seat. The companion package ships as a SIBLING package inside sidequest-understudy, alongside seat_core and understudy packages.

**Ruling (2026-06-26):** ONE REPO (sidequest-understudy), MULTIPLE PACKAGES. The companion imports the in-tree seat_core package directly and does NOT depend on understudy (test-harness). The coupling constraint is honored at the PACKAGE boundary, not the repo boundary.

**Design References:**
- docs/superpowers/specs/2026-06-25-companion-seat-design.md
- docs/superpowers/plans/2026-06-25-companion-C-companion-package.md
- docs/superpowers/plans/2026-06-25-companion-epic-breakdown.md

**Dependencies:**
- 159-1 (Extract sidequest-seat-core) — DONE ✓
- 159-6 (Relocate seat_core into sidequest-understudy) — DONE ✓

**Sibling / Blocked By:**
- 159-5 (Companion run loop, WebSocket transport, CLI, full-loop wiring) — depends on this story

## Scope: TDD RED Phase

Build the companion package core with test-driven design:

### Acceptance Criteria
1. Companion package structure created inside sidequest-understudy/src/companion/
2. Intent module — decision types (action, wait, error) and Intent class
3. Manifest module — persona-loaded companion descriptor
4. Persona module — archetypes, name sets, personality traits (from understudy/persona/)
5. Dice module — roll generation, notation parsing (stochastic combat/mechanical rolls)
6. Protocol module — message types (perception, action, observation payloads)
7. Brain module — per-turn LLM decision bridge (Claude via seat_core.llm)
8. Actuation module — decision → game state mutations (movement, speech, action dispatch)
9. Full test coverage for each module (RED phase)
10. pyproject.toml integration — companion as a workspace member in sidequest-understudy
11. Package properly imports in-tree seat_core with no dependency on understudy test harness

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-26T08:50:11Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-26T08:09:17Z | 2026-06-26T08:13:02Z | 3m 45s |
| red | 2026-06-26T08:13:02Z | 2026-06-26T08:24:16Z | 11m 14s |
| green | 2026-06-26T08:24:16Z | 2026-06-26T08:32:03Z | 7m 47s |
| review | 2026-06-26T08:32:03Z | 2026-06-26T08:50:11Z | 18m 8s |
| finish | 2026-06-26T08:50:11Z | - | - |
| red | - | 2026-06-26T08:24:16Z | unknown |
| green | 2026-06-26T08:24:16Z | 2026-06-26T08:32:03Z | 7m 47s |
| review | 2026-06-26T08:32:03Z | 2026-06-26T08:50:11Z | 18m 8s |
| finish | 2026-06-26T08:50:11Z | - | - |
| green | - | 2026-06-26T08:32:03Z | unknown |
| review | 2026-06-26T08:32:03Z | 2026-06-26T08:50:11Z | 18m 8s |
| finish | 2026-06-26T08:50:11Z | - | - |
| review | - | 2026-06-26T08:50:11Z | unknown |
| finish | 2026-06-26T08:50:11Z | - | - |
| finish | - | - | - |

## Delivery Findings

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): the companion package does not exist yet — Dev must create `src/companion/{intent,manifest,persona,dice,protocol,brain,actuation}.py` (+ `__init__.py` with a docstring) AND wire packaging so `import companion` resolves: add `"src/companion"` to `[tool.hatch.build.targets.wheel] packages` in pyproject.toml, then `uv sync`. Affects `sidequest-understudy/pyproject.toml` and `sidequest-understudy/src/companion/` (tests/companion/test_packaging.py enforces both the import and the wheel-package line). The `companion = "companion.cli:app"` script entry is 159-5's, NOT now. *Found by TEA during test design.*
- **Improvement** (non-blocking): seat_core surface verified live against Plan C — no harness drift. Import exactly: `seat_core.core.{Message, FakeStructuredModel, StructuredModel, ModelError, DecideResult}`, `seat_core.llm.factory.make_model(spec, output_model, *, default=None)`, `seat_core.persona.axis.{Role, SeatAxes}`. `make_model("fake", X, default=Y)` returns `FakeStructuredModel`; `decide()` reads `DecideResult.value`. Affects `src/companion/{brain,manifest,protocol}.py`. *Found by TEA during test design.*
- **Question** (non-blocking): Plan C's brain `decide()` catches broad `Exception` to degrade to YIELD — intentional per Plan C Global Constraints (a malformed decision is a legitimate YIELD, never a fabricated action). Tests pin BOTH directions (success not swallowed; timeout/error/non-intent → YIELD). Reviewer should treat the broad catch as the documented design, not a lang-review #1 silent-swallow violation. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): 159-5 (run loop, ws_transport, CLI) needs `websockets` and `typer` added to `[project.dependencies]` and a `companion = "companion.cli:app"` entry under `[project.scripts]`. NOT added in 159-4 — no consumer yet (minimalist; these modules import only stdlib + pydantic + pyyaml + in-tree seat_core). Affects `sidequest-understudy/pyproject.toml`. *Found by Dev during implementation.*
- **Improvement** (non-blocking): `protocol.py` already ships the builders 159-5's run loop will need but 159-4 does not yet consume — `seat_frame`, `chargen_choice_frame`, `fate_throw_frame` (only `connect_frame`, `player_action_frame`, `aside_frame`, `dice_throw_frame`, `yield_frame` have 159-4 consumers via actuation/packaging tests). They are exercised once 159-5 wires the run loop; they're public module functions so ruff does not flag them unused. Affects `src/companion/protocol.py`. *Found by Dev during implementation.*
- **Improvement** (non-blocking): editable resolution gotcha — after adding `"src/companion"` to the wheel packages, `import companion` only resolves after `uv sync` rebuilds the editable install. Recorded in dev-gotchas. Affects nothing further; flagged so 159-5 doesn't trip on a stale env. *Found by Dev during implementation.*

### Reviewer (code review)
- **Conflict** (blocking for 159-5, non-blocking for 159-4): `connect_frame()` puts the full WS URL (`defn.session_url`) into the payload field `game_slug` (`src/companion/protocol.py:25`). Per preflight's read of the server (`sidequest-server/.../handlers/connect.py`), the server consumes `payload.game_slug` as a short room slug — a full URL there will fail/mislook-up the room. 159-4 ships no live connection so this is latent here, but 159-5's WebSocketTransport MUST resolve it: add an explicit `game_slug` to `CompanionDef` (preferred — "explicit, never derived" matches the existing `session_url` comment) or extract the slug from the URL path in `connect_frame`, and add a test asserting the field. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `src/companion/manifest.py:40` `path.read_text()` omits `encoding="utf-8"` — lang-review #5 / CWE-838 (platform-dependent locale encoding). YAML manifests are UTF-8 by convention and the test code already uses `read_text(encoding="utf-8")`; production should match. One-word fix, fold into the next touch of this file (e.g. 159-5). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `brain.decide()`'s degrade-to-YIELD `except Exception` swallows the exception with no log/OTEL signal (`src/companion/brain.py:32`). A companion that always YIELDs because the LLM is failing is indistinguishable from one deliberately passing. When 159-5 adds the run loop, emit a `logger.warning`/watcher event on the degrade path (CLAUDE.md OTEL principle) — premature inside 159-4's pure-logic decide(), appropriate once there's a loop. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): test-hardening backlog (TEA, optional) — (a) `test_manifest_uses_safe_load_rejects_python_tags` passes even under unsafe `yaml.load` (asserts the raise, not the safe_load mechanism); assert the error names the YAML constructor path. (b) `build_turn_context` empty-narration branch, the StateMirror `"ready"` event branch, and the PEER bond template are uncovered. (c) `test_make_brain_binds_companion_intent` checks only the class name, not that the schema is bound to `CompanionIntent`. None affect correctness (code is right); they tighten the net. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

2 deviations

- **Companion package + its tests live in-tree under sidequest-understudy, not in a standalone ../sidequest-companion repo**
  - Rationale: The 2026-06-26 owner ruling (story context — higher authority than the plan doc per the spec-authority hierarchy) re-scoped the companion to an in-tree package; the standalone repo and the `../sidequest-seat-core` path dep no longer exist (deleted by 159-6). The tests/companion/ subdir is also required to avoid a pytest package-import-mode basename collision with understudy's existing tests/test_manifest.py, tests/test_persona.py, tests/test_actuation.py.
  - Severity: minor
  - Forward impact: 159-5's run/ws_transport/cli/wiring tests must also live in tests/companion/; the `src/companion` wheel-package line and the `companion = "companion.cli:app"` script entry go in understudy's pyproject (the script entry waits for 159-5's cli module).
- **brain.decide catches `Exception` instead of `(TimeoutError, ModelError, Exception)`**
  - Rationale: The plan's tuple is redundant — `Exception` already covers `TimeoutError` (subclass of OSError) and `ModelError` (subclass of Exception); listing them trips ruff and reads as noise. Behavior is byte-identical (any failure → YIELD). `except Exception` correctly does NOT catch `asyncio.CancelledError` (BaseException), so cancellation still propagates — exactly the desired semantics.
  - Severity: trivial
  - Forward impact: none — `decide()`'s contract (success → intent; timeout/model-error/non-intent → YIELD) is unchanged; all six brain tests pass.

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Companion package + its tests live in-tree under sidequest-understudy, not in a standalone ../sidequest-companion repo**
  - Spec source: docs/superpowers/plans/2026-06-25-companion-C-companion-package.md, Tasks 1–8
  - Spec text: "Create: ../sidequest-companion/src/companion/…" and "Create: ../sidequest-companion/tests/test_intent.py" (standalone repo, seat-core via `../sidequest-seat-core` path dep)
  - Implementation: Tests written under sidequest-understudy/tests/companion/; the companion will be an in-tree SIBLING import package at src/companion alongside src/seat_core and src/understudy, built into the existing sidequest-understudy wheel. Tests import the in-tree `seat_core` directly.
  - Rationale: The 2026-06-26 owner ruling (story context — higher authority than the plan doc per the spec-authority hierarchy) re-scoped the companion to an in-tree package; the standalone repo and the `../sidequest-seat-core` path dep no longer exist (deleted by 159-6). The tests/companion/ subdir is also required to avoid a pytest package-import-mode basename collision with understudy's existing tests/test_manifest.py, tests/test_persona.py, tests/test_actuation.py.
  - Severity: minor
  - Forward impact: 159-5's run/ws_transport/cli/wiring tests must also live in tests/companion/; the `src/companion` wheel-package line and the `companion = "companion.cli:app"` script entry go in understudy's pyproject (the script entry waits for 159-5's cli module).

### Dev (implementation)
- **brain.decide catches `Exception` instead of `(TimeoutError, ModelError, Exception)`**
  - Spec source: docs/superpowers/plans/2026-06-25-companion-C-companion-package.md, Task 7 (brain.py)
  - Spec text: `except (TimeoutError, ModelError, Exception):  # noqa: BLE001 — any failure → safe pass`
  - Implementation: `except Exception:  # noqa: BLE001`; dropped the now-unused `ModelError` import.
  - Rationale: The plan's tuple is redundant — `Exception` already covers `TimeoutError` (subclass of OSError) and `ModelError` (subclass of Exception); listing them trips ruff and reads as noise. Behavior is byte-identical (any failure → YIELD). `except Exception` correctly does NOT catch `asyncio.CancelledError` (BaseException), so cancellation still propagates — exactly the desired semantics.
  - Severity: trivial
  - Forward impact: none — `decide()`'s contract (success → intent; timeout/model-error/non-intent → YIELD) is unchanged; all six brain tests pass.

### Reviewer (audit)
- **TEA's "in-tree under sidequest-understudy, not standalone repo"** → ✓ ACCEPTED by Reviewer: correct application of the spec-authority hierarchy — the 2026-06-26 owner ruling (story context) outranks Plan C's standalone-repo paths, and the `tests/companion/` subdir is genuinely required to avoid the pytest basename collision with understudy's own `test_manifest.py`/`test_persona.py`/`test_actuation.py`. `test_packaging.py` structurally enforces the no-understudy-import half of the ruling. Sound.
- **Dev's "brain.decide catches `Exception` instead of `(TimeoutError, ModelError, Exception)`"** → ✓ ACCEPTED by Reviewer: byte-identical behavior (the tuple was redundant — `Exception` subsumes both), and `except Exception` correctly leaves `asyncio.CancelledError` (a `BaseException`) to propagate, which is the desired semantics. rule-checker confirmed the broad catch is consistent with the documented degrade-to-YIELD carve-out, and all three failure-path tests + the success-path test pin both directions. The drop of the now-unused `ModelError` import is correct hygiene. No concern.
- No UNDOCUMENTED deviations found — the diff matches the logged TEA/Dev deviations and Plan C Tasks 2–8 within the ruling's in-tree reframing.

## Implementation Notes

**Repo:** sidequest-understudy
**Branch Strategy:** gitflow (develop is default branch)
**Branch Name:** feat/159-4-companion-package-core

## Sm Assessment

**Setup complete — story routed to TEA for RED.**

Story 159-4 (Companion package core — intent, manifest, persona, dice, protocol, brain, actuation) was blocked on an unresolved companion↔seat_core coupling. Owner ruled it on 2026-06-26 — recorded in the story description and the context doc:

- **ONE repo, MULTIPLE packages.** The companion ships as a SIBLING package inside `sidequest-understudy`, alongside the in-tree `seat_core` package and the `understudy` package.
- The companion imports the `seat_core` PACKAGE directly; it does NOT depend on the `understudy` (test-harness) package. The "companion must not depend on the test harness" constraint is honored at the **package** boundary, not the repo boundary.
- The original `repos: sidequest-companion` target is VOID — no such repo. All work lands in `sidequest-understudy` (repos field corrected during setup).

**Dependency state:** 159-1 (seat-core extract) and 159-6 (seat-core relocation into understudy) are both DONE. Sibling 159-5 (run loop, WS transport, CLI, full-loop wiring) depends on this story.

**For TEA (RED):** Write failing tests for the seven companion-package modules (intent, manifest, persona, dice, protocol, brain, actuation) per Plan C (`docs/superpowers/plans/2026-06-25-companion-C-companion-package.md`). The implementing team owns the concrete uv multi-package mechanics (workspace members / pyproject layout) — establish the package skeleton so the companion is importable as its own package under sidequest-understudy.

**Setup-exit gate:** session exists ✓, fields set ✓, context written ✓, branch `feat/159-4-companion-package-core` created on sidequest-understudy (gitflow → develop) ✓. Jira: no key for epic 159 — claim explicitly skipped.

## TEA Assessment

**Tests Required:** Yes
**Reason:** n/a — feature story (7 new modules).

**Test Files:** (all under `sidequest-understudy/tests/companion/`, committed `b01dc2e`)
- `test_intent.py` — CompanionIntent decision contract (Plan C Task 2)
- `test_manifest.py` — CompanionDef loader; loud failures; safe_load (Task 3)
- `test_persona.py` — voice/role system prompt; SOUL Test; pet vs hireling bond (Task 4)
- `test_dice.py` — fair faces per die system; physics-is-the-roll (Task 5)
- `test_protocol.py` — frame builders + StateMirror (Task 6)
- `test_brain.py` — seat-core decide + degrade-to-YIELD on every failure (Task 7)
- `test_actuation.py` — intent→outgoing-frame composition (Task 8)
- `test_packaging.py` — packaging + the coupling-ruling wiring guard

**Tests Written:** 47 tests across 8 files covering the 7 in-scope modules + packaging.
**Status:** RED — verified by `testing-runner` (RUN_ID 159-4-tea-red): all failures are exactly `ModuleNotFoundError: No module named 'companion'`; ZERO seat_core / syntax / fixture / conftest errors. RED is clean (fails only on the missing implementation; seat_core surface verified live).

**Scope:** Story 159-4 = Plan C Tasks 2–8 (intent, manifest, persona, dice, protocol, brain, actuation). Tasks 9–11 (run loop, ws_transport, CLI, full-loop wiring) are **159-5** — NOT written here.

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #1 silent exception swallowing (broad catch must not eat valid results) | `test_decide_returns_scripted_intent`, `test_decide_non_intent_value_to_yield` | failing (RED) |
| #8 unsafe deserialization (safe_load, no python-tag exec) | `test_manifest_uses_safe_load_rejects_python_tags`, `test_malformed_yaml_fails_loud` | failing (RED) |
| No Silent Fallbacks (SOUL) — loud fail before any socket | `test_missing_file/unknown_role/missing_field_fails_loud`, `test_unknown_system_fails_loud` | failing (RED) |
| SOUL *Test* — act only for self, never narrate others | `test_prompt_states_player_not_narrator` (+ frame builders emit own actions only) | failing (RED) |
| Coupling ruling — in-tree, no understudy dependency, wheel-wired | `test_companion_source_does_not_import_understudy`, `test_companion_registered_in_wheel_packages`, `test_companion_manifest_built_on_seat_core_types` | failing (RED) |
| Never-stall-the-table — bounded decide → YIELD | `test_decide_times_out_to_yield`, `test_decide_model_error_to_yield` | failing (RED) |

**Rules checked:** 4 of 13 lang-review checks are applicable to this pure-logic package (#1, #6, #8 + #2 mutable-defaults satisfied by design — `rng=None`/keyword-only, no test needed); #3/#4/#5/#7/#9/#11/#12 apply to I/O, logging, paths, and API handlers that arrive with 159-5's transport/CLI. Plus SOUL (No Silent Fallbacks, the *Test*) and the 2026-06-26 coupling ruling.
**Self-check:** 0 vacuous tests — every test asserts a concrete value/shape/raise; no `assert True`, no bare-truthy, no `let _ =`-equivalent.

**Handoff:** To Dev (Naomi Nagata) for GREEN. Build `src/companion/` per Plan C Tasks 2–8 and wire `"src/companion"` into the wheel packages (see Delivery Findings). Do not author the run loop / ws_transport / CLI — that's 159-5.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:** (sidequest-understudy, commit `54fe8aa`)
- `src/companion/__init__.py` — package docstring (in-tree sibling; reuses seat_core, never understudy)
- `src/companion/intent.py` — `IntentKind` (act/aside/roll/beat/defend/yield) + `CompanionIntent` validators + `YIELD_INTENT` (Task 2)
- `src/companion/manifest.py` — `CompanionDef`, `ManifestError`, `load_companion` (safe_load, loud-fail) (Task 3)
- `src/companion/persona.py` — `build_system_prompt` (voice + role bond + SOUL *Test* frame) (Task 4)
- `src/companion/dice.py` — `roll_faces` (d20/2d6/4dF, loud on unknown) (Task 5)
- `src/companion/protocol.py` — `Transport` Protocol, frame builders, `StateMirror` (Task 6)
- `src/companion/brain.py` — `make_brain`, `build_turn_context`, `decide` (degrade-to-YIELD) (Task 7)
- `src/companion/actuation.py` — `actuate` (intent → one outgoing frame, fair faces) (Task 8)
- `pyproject.toml` — added `"src/companion"` to `[tool.hatch.build.targets.wheel] packages`

**Tests:** 47/47 companion tests passing (GREEN) — verified by `testing-runner` (RUN_ID verify-scratch-159-4-green). seat_core regression suite 34/34 still green (wheel-packages change did not break sibling resolution). `ruff check src/companion tests/companion` clean.

**Branch:** feat/159-4-companion-package-core (pushed to origin/slabgorb-org).

**Wiring (self-review):** the package is wired end-to-end within its scope — `actuate()` composes intent + dice + protocol + mirror (the in-package integration point), `make_brain()` reaches in-tree `seat_core.llm.factory.make_model`, and `test_packaging.py` proves `import companion` resolves, the manifest is built on `seat_core`'s `SeatAxes`, no source file imports `understudy`, and `src/companion` is in the wheel packages. Run loop / ws_transport / CLI consumers arrive in 159-5 (scope held).

**ACs met:** 1–8 (package + 7 modules) ✓; 9 full test coverage ✓; 10 pyproject wheel-package integration ✓; 11 imports in-tree seat_core with zero understudy dependency ✓ (structurally enforced).

**Handoff:** To Reviewer (Chrisjen Avasarala) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 4 smells (tests 47/47 + 34/34 green, ruff clean) | confirmed 3, dismissed 1 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings (domain covered by Reviewer) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings (domain covered by Reviewer) |
| 4 | reviewer-test-analyzer | Yes | findings | 8 | confirmed 6, dismissed 2 |
| 5 | reviewer-comment-analyzer | Yes | findings | 4 | confirmed 4 |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (domain covered by Reviewer) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings (domain covered by Reviewer) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings (domain covered by Reviewer) |
| 9 | reviewer-rule-checker | Yes | findings | 9 (Rule 5 ×1, Rule 10 ×8) | confirmed 9 (all Low; Rule 10 convention-contextualized) |

**All received:** Yes (4 enabled returned; 5 disabled via `workflow.reviewer_subagents` pre-filled as Skipped)
**Total findings:** 13 confirmed (all Low/Medium, none blocking), 3 dismissed (with rationale), 1 Medium deferred to 159-5

## Reviewer Assessment

**Verdict:** APPROVED

A small, disciplined, in-tree package built straight from Plan C and held honest by a packaging wiring test. 47/47 companion tests green, seat_core regression 34/34 green, ruff clean. The subagents surfaced no Critical or High issue in the shipped 159-4 surface — only Low polish and one Medium that genuinely belongs to 159-5's live-connection gate. Per the severity framework (only Critical/High block), this approves; every finding is recorded, none dismissed without evidence.

**Data flow traced:** authored YAML manifest → `load_companion()` (`manifest.py:36`) `path.exists()` guard → `yaml.safe_load` (safe against `!!python/object` — `manifest.py:40`) → `CompanionDef.model_validate` (pydantic v2, `extra="forbid"`, `Role` enum, required fields) → consumed by `build_system_prompt` (persona), `make_brain`/`decide` (brain), and `actuate` (actuation) → `actuate()` emits exactly ONE frame, always stamped with `mirror.self_player_id`, or `None` when self-id is unknown. Untrusted input (the manifest) is validated at the boundary and fails loud; the only thing that ever crosses into "soft" handling is a failed model decision, which degrades to YIELD by design.

**Observations (tagged):**
- `[VERIFIED]` SOUL *The Test* holds **mechanically** — `actuate()` (`actuation.py:29`) reads `pid = mirror.self_player_id`, returns `None` if unset, and every frame builder stamps `player_id=pid`; no builder emits NARRATION or any other player's action. Evidence: `protocol.py:41-72` builders + `test_actuation.py:test_no_self_id_returns_none`. This is the single most load-bearing invariant of a player-agent and it is enforced in code, not just prose. Complies with SOUL "The Test".
- `[VERIFIED]` Coupling ruling holds — zero `import understudy` / `from understudy` in any of the 8 `src/companion/*.py` (AST/grep), and `test_packaging.py:test_companion_source_does_not_import_understudy` rglob-scans to keep it from rotting. `CompanionDef.axes` is `seat_core`'s `SeatAxes` (identity-checked by `test_companion_manifest_built_on_seat_core_types`). Complies with the 2026-06-26 owner ruling.
- `[VERIFIED]` No Silent Fallbacks at the manifest/dice boundary — missing file, unknown role, missing field, malformed YAML, and python-tag all raise loud (`ManifestError`); unknown die system raises `ValueError`. Evidence: `manifest.py:38-41`, `dice.py:18-19`, six manifest tests + `test_unknown_system_fails_loud`. The brain's `except Exception → YIELD` is the documented, tested carve-out (YIELD is a legitimate choice, never fabrication), confirmed by rule-checker.
- `[RULE]` `manifest.py:40` `path.read_text()` omits `encoding="utf-8"` — lang-review #5 / CWE-838. **Confirmed, Low.** The test code already does this correctly; production should match. Non-blocking → delivery finding.
- `[RULE]` All 8 companion modules omit `__all__` (lang-review #10). **Confirmed, Low, convention-contextualized:** 0 of 37 existing `seat_core`+`understudy` source files declare `__all__` — the codebase convention is to omit it, so enforcing it only on `companion` would be inconsistent. If desired, address codebase-wide, not piecemeal. Non-blocking.
- `[TEST]` `test_manifest_uses_safe_load_rejects_python_tags` is vacuous as a *safety* proof — under unsafe `yaml.load` the payload would execute then `model_validate(0)` raises → `ManifestError` → test still passes. **Confirmed, Low** — the *code* is safe (safe_load is used, AST-confirmed; ConstructorError→YAMLError→ManifestError); the *test* just asserts the raise, not the mechanism. Hardening noted.
- `[DOC]` `protocol.py:3` describes the 159-5 ws adapter / wiring test in present tense ("live in 159-5") though neither exists yet; `roll_faces` and `actuate` lack docstrings documenting their raise / `None` contract. **Confirmed, Low.**
- `[SILENT]` `brain.decide()` swallows the failure with no log/OTEL signal (`brain.py:32`) — an always-YIELDing companion (LLM down) is indistinguishable from a deliberately-passing one. **Confirmed, Low** — premature inside 159-4's pure-logic decide(); add a warning/watcher emit when 159-5 builds the loop (CLAUDE.md OTEL principle). Deferred to 159-5.
- `[TYPE]` `persona._BOND[defn.role]` (`persona.py`) and `actuate`'s `match` are not structurally exhaustive — a 4th `Role`/`IntentKind` added to `seat_core` would `KeyError` / fall through to YIELD. **Confirmed, Low, latent** (current enums are exactly covered). An `assert set(_BOND) == set(Role)` at import would make it explicit.
- `[SEC]` `CompanionDef.session_url` is a bare `str` with no URL-format validation — an invalid URL surfaces at 159-5 connect time, not load time. **Confirmed, Low**, deferred to 159-5. yaml is `safe_load`; no secrets logged; no injection vector.
- `[EDGE]` Coverage gaps (test-analyzer): the `build_turn_context` empty-narration branch, the StateMirror `"ready"` event branch, and the PEER bond template are untested. **Confirmed, Low** — correctness is fine; the net could be tighter. Hardening noted.
- `[SIMPLE]` `persona.py` `.format(name=…, species=…)` is a no-op on the PEER/HIRELING templates (no placeholders) — harmless (name/species still appear via the "## Who you are" line), but the call reads as if it interpolates them. `actuation.py:77` comment says "unreachable" but the `match` is reachable if an `IntentKind` is added. **Confirmed, Low** cleanups.

**Dismissed (with rationale):**
- `[TEST]` "test_prompt_states_player_not_narrator OR-arm is dead" (test-analyzer, low conf) — **DISMISSED:** `persona.py:34` "Describe ONLY your own" puts the substring contiguous on one line; lowercased it matches "only your own", so the first arm is live (rule-checker concurs).
- `[TEST]` "test_yield_and_roll_and_defend_need_nothing is tautological" — **DISMISSED:** the meaningful assertion is that constructing YIELD/ROLL/DEFEND does NOT raise (no text/beat required); a validator bug that wrongly required text would raise `ValidationError` and fail the test. The `.kind is X` line is weak but the construction-succeeds check has real value.
- `[SIMPLE]` preflight "PEER/HIRELING prompts carry no identity" — **DISMISSED:** name and species ARE in the prompt via the separate `## Who you are\nYou are {name}, a {species}.` line (`persona.py:48`); only the bond *sentence* differs by role, which is intended.

### Rule Compliance (lang-review python.md, mapped)
- #1 silent exception swallowing — COMPLIANT (brain carve-out documented + tested; manifest catches named types).
- #2 mutable defaults — COMPLIANT (all `None`/scalar; instance dicts/lists built in `__init__`).
- #3 type annotations at boundaries — COMPLIANT (all public fns fully annotated).
- #4 logging — N/A (no module imports logging); secondary observability gap noted `[SILENT]`, deferred to 159-5.
- #5 path handling — **VIOLATION (Low):** `manifest.py:40` missing `encoding=`. Confirmed.
- #6 test quality — COMPLIANT overall (no `assert True`, no bare-truthy, no skips); one weak safety-proof test noted `[TEST]`.
- #7 resource leaks — COMPLIANT (`Path.read_text` self-closing; no open handles).
- #8 unsafe deserialization — COMPLIANT (`yaml.safe_load`; verified by test + AST).
- #9 async pitfalls — COMPLIANT (`asyncio.wait_for` awaited with explicit timeout; no blocking calls in async).
- #10 import hygiene — `__all__` absent on all 8 modules; convention-contextualized Low (0/37 existing files use it). No star/circular imports.
- #11 input validation at boundaries — COMPLIANT (`load_companion` validates path/yaml/model; `extra="forbid"`).
- #12 dependency hygiene — COMPLIANT (no new deps; dev deps segregated).
- #13 fix-introduced regressions — N/A (all-new code).

### Tenant isolation audit
N/A — the companion package has no multi-tenant surface (no `tenant_id`, no auth, no per-tenant data). The closest analog is per-seat identity: `actuate()` only ever acts for `mirror.self_player_id` and returns `None` otherwise, so the companion structurally cannot act for another seat — the player-agent equivalent of isolation, and it holds.

### Devil's Advocate
Let me argue this is broken. **Attack 1 — the manifest is attacker-controlled content.** A malicious `companion.yaml` is the obvious vector. I tried the `!!python/object/apply:os.system` tag: blocked by `safe_load` (raises ConstructorError → ManifestError). Unknown role `overlord`: rejected by the `Role` enum. Extra smuggled field: rejected by `extra="forbid"`. Empty file → `safe_load` returns `None` → `model_validate(None)` raises → `ManifestError`. So the boundary is genuinely hardened. The one residual: `session_url` is an unvalidated string — a `file://` or `http://` URL, or a garbage string, sails through `load_companion` and only explodes (or worse, connects somewhere unexpected) when 159-5 opens it. That's a real but deferred concern, flagged. **Attack 2 — starve the table.** Can a confused/hostile brain stall the game? `decide()` is bounded by `asyncio.wait_for(timeout_s)` and any failure (timeout, exception, wrong-shape result) degrades to YIELD — I verified all three branches are tested. A brain that returns garbage can't fabricate an action (the `isinstance` guard) and can't hang the loop (the timeout). The companion yields to humans, never the reverse — structurally true. **Attack 3 — act for someone else.** The whole point of a player-agent is that it must not seize another seat. `actuate()` stamps `mirror.self_player_id` on every frame and returns `None` before self-id is known; no frame builder can address another player. I could not construct a path where the companion emits a frame for a seat that isn't its own. **Attack 4 — the latent wire bug.** `connect_frame` sends a full URL in `game_slug`; if the server keys rooms on that field, every live companion silently joins the wrong room (or none). This is the realest defect — but it cannot fire in 159-4 (no socket opens) and its fix depends on the server contract 159-5 wires and tests. Confirmed and deferred, loudly. **Attack 5 — a stressed filesystem / weird locale.** `read_text()` without `encoding=` could misdecode a non-UTF-8 manifest on an exotic locale; Low, flagged. **Verdict of the advocacy:** the genuinely dangerous surfaces (deserialization, table-starvation, acting-for-others) are all closed and tested; what remains is one deferred wire-semantics question and a handful of Low polish items. Nothing here is broken enough to bounce a package-core story.

**Challenge of VERIFIEDs:** I marked SOUL *Test*, the coupling ruling, and No-Silent-Fallbacks VERIFIED. No subagent contradicted any of them; the rule-checker independently confirmed all three with line evidence. The only tension is `[SILENT]`'s "broad except" — but that is the *documented* carve-out, not a violation, and I cite the three passing degrade-path tests + the success-path test as proof the catch neither fabricates nor swallows valid results. No VERIFIED needs downgrading.

**Handoff:** To SM (Camina Drummer) for finish-story. None of the recorded findings block 159-4; the game_slug item is captured as blocking-for-159-5.