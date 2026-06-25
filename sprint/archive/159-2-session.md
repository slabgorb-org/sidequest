---
story_id: "159-2"
jira_key: ""
epic: ""
workflow: "trivial"
---
# Story 159-2: Migrate understudy onto seat-core

## Story Details
- **ID:** 159-2
- **Jira Key:** (none — Jira not enabled)
- **Workflow:** trivial
- **Stack Parent:** 159-1

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-25T20:42:10Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-25T20:13:48Z | 2026-06-25T20:16:06Z | 2m 18s |
| implement | 2026-06-25T20:16:06Z | 2026-06-25T20:27:50Z | 11m 44s |
| review | 2026-06-25T20:27:50Z | 2026-06-25T20:42:10Z | 14m 20s |
| finish | 2026-06-25T20:42:10Z | - | - |

## Delivery Findings

Architects carried forward (from 2026-06-25 design):
- Gap (non-blocking, resolved by this story): seat_core had zero production consumers — wiring debt cleared once unify lands.
- Question (non-blocking, owned by 159-4/5): how the shipping companion reaches in-tree seat_core without importing the understudy harness — out of 159-2 scope.

### Dev (implementation)
- **Gap RESOLVED** (non-blocking): the Architect's "seat_core has zero production consumers" finding is now cleared — `understudy.brain.llm.factory.make_model` delegates to `seat_core.llm.factory.make_model(spec, Intent)` and the live run loop (`orchestrate/run.py:16`) routes through it. seat_core's production consumer is now the understudy run loop, exercised end-to-end by `tests/wiring/test_full_loop.py`. Affects `src/seat_core/` (no further change needed). *Found by Dev during implementation.*
- **Improvement** (non-blocking): `tests/test_reconnect.py` carried 2 pre-existing E402 lint errors on develop (late module-level imports, from PR #10 2026-06-12); fixed in passing here. Affects nothing downstream. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `seat_core.core.DecideResult.value` is typed `BaseModel`, so the understudy run loop's `intent = result.value` (`orchestrate/seat.py:134`) and `FakeActionModel`'s `super().__init__(script, …)` (`brain/core.py:46`) are now static type-mismatches (no type checker runs in understudy, so no gate fails; runtime is correct because the factory always binds `Intent`). Affects `src/understudy/orchestrate/seat.py`, `src/understudy/brain/core.py` (a `cast(Intent, …)` localizes it; the clean fix is making `DecideResult` generic in seat_core — out of 159-2 scope, belongs to the 159-4/5 companion work). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): no test exercises `make_model("ollama/…"|"anthropic/…").decide()` returning a real `Intent` via the shim's Intent binding — the dispatch tests check only class names; seat_core's `decide()` tests use the generic `Ping`. The `.value` read IS covered via `FakeActionModel` in the wiring/seat-loop tests, so the critical path is safe; the narrow gap is the literal `Intent` arg in the factory. Affects `tests/test_brain_core.py` (one mocked-transport async test would pin it). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): two comments made stale by the backend deletions — `src/understudy/manifest.py:16` and `tests/test_manifest.py:16` both say "see claude_p_model.py", which now lives at `seat_core/llm/claude_p_model.py`. Out of this diff's files; left for a fast-follow rather than expanding scope. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 1 findings (0 Gap, 0 Conflict, 0 Question, 1 Improvement)
**Blocking:** None

- **Improvement:** no test exercises `make_model("ollama/…"|"anthropic/…").decide()` returning a real `Intent` via the shim's Intent binding — the dispatch tests check only class names; seat_core's `decide()` tests use the generic `Ping`. The `.value` read IS covered via `FakeActionModel` in the wiring/seat-loop tests, so the critical path is safe; the narrow gap is the literal `Intent` arg in the factory. Affects `tests/test_brain_core.py`.

### Downstream Effects

- **`tests`** — 1 finding

### Deviation Justifications

2 deviations

- **Relocated factory-dispatch coverage instead of deleting it with test_backends.py**
  - Rationale: seat_core/test_factory.py covers only the GENERIC factory (Ping + FakeStructuredModel, where `fake` requires an explicit default). It does NOT cover understudy's Intent-bound shim factory — the new production entry point (run.py → brain.llm.factory.make_model). Deleting all of test_backends.py would leave the shim's dispatch and its no-default `fake` contract untested — the exact "tested-but-unwired / no wiring test" smell the Architect flagged about seat_core. The backend-internals tests (ollama/anthropic/claude_p) WERE genuinely duplicated by tests/seat_core/* (in fact a strict superset) and were dropped as the spec intended.
  - Severity: minor
  - Forward impact: none — net adds shim coverage; no API change.
- **Fixed pre-existing E402 lint in tests/test_reconnect.py (out of story scope)**
  - Rationale: These 2 E402 errors pre-existed on develop (introduced 2026-06-12, PR #10), unrelated to this refactor, but blocked the named `ruff check .` gate. Zero-risk import reorder; chose to hand off lint-green rather than red.
  - Severity: minor
  - Forward impact: none.

## Design Deviations

### Dev (implementation)
- **Relocated factory-dispatch coverage instead of deleting it with test_backends.py**
  - Spec source: SM Assessment scope (159-2), "DELETE … tests/test_backends.py (coverage lives in tests/seat_core/*)"
  - Spec text: "DELETE src/understudy/brain/llm/{anthropic_model,ollama_model,claude_p_model}.py and tests/test_backends.py (coverage lives in tests/seat_core/*)."
  - Implementation: Deleted test_backends.py AND moved its two factory-dispatch tests (now understudy-shim-specific) into tests/test_brain_core.py; added test_factory_fake_needs_no_default.
  - Rationale: seat_core/test_factory.py covers only the GENERIC factory (Ping + FakeStructuredModel, where `fake` requires an explicit default). It does NOT cover understudy's Intent-bound shim factory — the new production entry point (run.py → brain.llm.factory.make_model). Deleting all of test_backends.py would leave the shim's dispatch and its no-default `fake` contract untested — the exact "tested-but-unwired / no wiring test" smell the Architect flagged about seat_core. The backend-internals tests (ollama/anthropic/claude_p) WERE genuinely duplicated by tests/seat_core/* (in fact a strict superset) and were dropped as the spec intended.
  - Severity: minor
  - Forward impact: none — net adds shim coverage; no API change.
- **Fixed pre-existing E402 lint in tests/test_reconnect.py (out of story scope)**
  - Spec source: SM Assessment gate (159-2), "uv run ruff check . green"
  - Spec text: "Gate: cd sidequest-understudy && uv run pytest -q && uv run ruff check . both green."
  - Implementation: Reordered two late module-level imports (RunManifest, SeatSpec, run_table) to the top of tests/test_reconnect.py.
  - Rationale: These 2 E402 errors pre-existed on develop (introduced 2026-06-12, PR #10), unrelated to this refactor, but blocked the named `ruff check .` gate. Zero-risk import reorder; chose to hand off lint-green rather than red.
  - Severity: minor
  - Forward impact: none.

### Reviewer (audit)
- **Relocated factory-dispatch coverage instead of deleting it with test_backends.py** → ✓ ACCEPTED by Reviewer: correct and well-reasoned. test_analyzer confirmed every deleted assertion has an equivalent (the claude_p key-strip wiring assertion in `tests/seat_core/test_claude_p.py` is in fact *stronger* than the deleted one). Relocating the understudy-shim factory tests preserves wiring coverage seat_core's generic factory test does not provide. No coverage lost.
- **Fixed pre-existing E402 lint in tests/test_reconnect.py (out of story scope)** → ✓ ACCEPTED by Reviewer: zero-risk import reorder; verified pre-existing on develop; keeps the named `ruff check .` gate green. The right call over handing off lint-red. The symmetric out-of-scope collateral (2 stale comments in manifest.py/test_manifest.py made stale by the module deletions) was correctly NOT chased into the diff — recorded as a non-blocking follow-up instead.
- No undocumented deviations found. The diff matches the SM-scoped plan (shim re-export, factory delegation, deletions, `.intent`→`.value` rename) with no smuggled scope.

## Sm Assessment

**Routing rationale.** 159-2 ("Migrate understudy onto seat-core") was re-scoped by 159-6, which moved `seat_core` in-tree — dissolving the original path-dependency framing. The only residue was a convergence question explicitly flagged for the Architect. Per Bossmang's steer (2026-06-25), the Architect (Naomi) ruled FIRST before any implementation scaffolding.

**Architect ruling: UNIFY.** `seat_core` is the generalized lift of `understudy.brain.llm.*` (Jun 25 vs Jun 11–13) but has **zero production consumers** — the live run loop wires to `brain.*` (`orchestrate/run.py:16`, `orchestrate/seat.py:17`), leaving `seat_core` as tested-but-unwired infra (a standing wiring violation). Fix direction is **understudy → seat_core**: understudy becomes seat_core's proof consumer and seat_core stays a clean leaf for the 159-4/5 companion (spec requires the shipping companion not depend on the test harness).

**Workflow choice: trivial (not the tagged tdd).** This is a refactor with an existing regression net (`tests/seat_core/*` + `tests/wiring/test_full_loop.py`) and preserved behavior — there is no failing test for a tdd `red` phase to write. `trivial` (setup → implement → review → finish; triggers on `refactor`, points-max 2) is the right-sized fit and matches the Architect's primary recommendation. Workflow field updated tdd → trivial.

**Scope for Dev (≈2pt, pre-written diffs in Plan A Tasks 8–9, MINUS packaging since 159-6 brought seat_core in-tree):**
- Rewrite `src/understudy/brain/core.py` → shim re-exporting `seat_core.core` (`DecideResult, Message, ModelError, StructuredModel as ActionModel, parse_structured`); define `parse_intent(raw)=parse_structured(raw, Intent)` and `FakeActionModel(FakeStructuredModel)` defaulting to `Intent(kind=IntentKind.WAIT)`.
- Rewrite `src/understudy/brain/llm/factory.py` → bind `seat_core.llm.factory.make_model(spec, Intent)`; `"fake"` returns `FakeActionModel([])`. Preserve public `make_model` API so `seat.py:17`, `run.py:16`, and wiring tests need no change.
- DELETE `src/understudy/brain/llm/{anthropic_model,ollama_model,claude_p_model}.py` and `tests/test_backends.py` (coverage lives in `tests/seat_core/*`).
- Apply field rename `DecideResult.intent` → `.value` at `orchestrate/seat.py:134`, `tests/test_brain_core.py`, `tests/test_seat_loop.py:84`.
- Optional fast-follow (do NOT bloat 159-2): `Archetype` subclass `seat_core.persona.axis.SeatAxes`; drop now-indirect `anthropic>=0.40` from understudy pyproject deps.

**Gate:** `cd sidequest-understudy && uv run pytest -q && uv run ruff check .` both green.

**Reference docs:** `docs/superpowers/plans/2026-06-25-companion-A-seat-core.md` (Tasks 8–9), `docs/superpowers/specs/2026-06-25-companion-seat-design.md`.

**Handoff → Dev (Naomi Nagata, implement phase).** ACs are on the story YAML. Jira skipped (not enabled). Branch `feat/159-2-unify-understudy-onto-seat-core` cut in `sidequest-understudy`.

---
## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `src/understudy/brain/core.py` — rewritten as a thin shim over `seat_core.core`: re-exports `DecideResult, Message, ModelError, StructuredModel as ActionModel, parse_structured`; defines `parse_intent(raw)=parse_structured(raw, Intent)` and `FakeActionModel(FakeStructuredModel)` (WAIT default baked in).
- `src/understudy/brain/llm/factory.py` — rewritten to delegate to `seat_core.llm.factory.make_model(spec, Intent)`, intercepting `fake` → `FakeActionModel([])`; preserves the public `make_model(spec)` signature.
- `src/understudy/orchestrate/seat.py` — `DecideResult.intent` → `.value` (line 134).
- `tests/test_brain_core.py` — `.intent` → `.value`; absorbed the shim-factory dispatch tests (relocated from deleted test_backends.py) + `test_factory_fake_needs_no_default`.
- `tests/test_seat_loop.py` — `DecideResult(intent=…)` → `DecideResult(value=…)` (line 84).
- `tests/test_reconnect.py` — moved 2 late imports to top (pre-existing E402 fix; out-of-scope, gate-required — see deviation).
- **Deleted:** `src/understudy/brain/llm/{anthropic_model,claude_p_model,ollama_model}.py`, `tests/test_backends.py`.

**Wiring (verified, not just existence):**
- Production entry point `orchestrate/run.py:16` → `brain.llm.factory.make_model` now routes to seat_core. seat_core gains its first production consumer (the run loop), clearing the Architect's wiring-debt finding.
- `tests/wiring/test_full_loop.py` and `tests/wiring/test_reconnect_state.py` exercise the live loop through the new shim (FakeActionModel) — green.
- Shim factory dispatch (Intent-bound backends, no-default fake) covered by `tests/test_brain_core.py`.

**Tests:** 123/123 passing (GREEN). `ruff check .` clean.
**Branch:** `feat/159-2-unify-understudy-onto-seat-core` (sidequest-understudy)

**Acceptance Criteria:** all 5 met — shim re-export + parse_intent/FakeActionModel (AC1); factory binds seat_core + fake intercept + preserved API (AC2); duplicate modules deleted (AC3); field rename applied (AC4); seat_core has a production importer + pytest & ruff green (AC5).

**Out of scope (deferred, per Architect):** `Archetype` → `SeatAxes` convergence; dropping now-indirect `anthropic>=0.40` from understudy pyproject. Not touched.

**Handoff:** To Reviewer (Chrisjen Avasarala) for the review phase.

---
## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 123/123 green, ruff clean, 0 smells, no dangling imports to deleted modules |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings (assessed by reviewer — see [EDGE]) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings (assessed by reviewer — see [SILENT]) |
| 4 | reviewer-test-analyzer | Yes | findings | 2 | confirmed 1 (coverage gap, Medium, non-blocking), confirmed 1 (near-dup test, Low) |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 | confirmed 3 (2 stale comments Low, parse_structured docstring Low — all non-blocking) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (assessed by reviewer + rule-checker — see [TYPE]) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings (assessed by reviewer — see [SEC]) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings (assessed by reviewer — see [SIMPLE]) |
| 9 | reviewer-rule-checker | Yes | findings | 5 (3 sites) | confirmed 3 sites (type x2 sites Medium/Low non-blocking, factory `__all__` Low) |

**All received:** Yes (4 enabled returned; 5 disabled via `workflow.reviewer_subagents` pre-filled as skipped)
**Total findings:** 0 confirmed-blocking, 9 confirmed non-blocking (Medium/Low), 0 dismissed

## Reviewer Assessment

**Verdict:** APPROVED

A clean unification refactor: +74/−356 (net −282), removes three duplicate LLM-backend modules and a 112-line duplicate test, and makes understudy the proof-consumer of in-tree `seat_core` (arrow correctly points understudy → seat_core; seat_core imports nothing from understudy — confirmed, no cycle). 123/123 tests green, ruff clean. No Critical/High issues; every finding is Medium/Low and non-blocking.

**Data flow traced:** seat model spec (`SeatSpec.model`, e.g. `"ollama/qwen3:8b"`) → `brain.llm.factory.make_model(spec)` → (`fake` intercepted → `FakeActionModel`; else) `seat_core.llm.factory.make_model(spec, Intent)` → backend `.decide()` → `DecideResult(value=Intent)` → `seat.py:134 intent = result.value` → `intent.kind/.text_input/.model_copy` drive actuation. Safe: the only untrusted input (LLM output) is pydantic-validated in `parse_structured`/tool-call before use; unknown backend strings raise loud via seat_core's `case _`.

**Observations (≥5):**
- [VERIFIED] Loud-failure on unknown backend survives the delegation — `make_model("bard/gpt-1")` is not `fake`, falls to `_make_model("bard/gpt-1", Intent)`, hits seat_core `factory.py` `case _: raise ValueError`. Evidence: `factory.py:18-20` + `seat_core/llm/factory.py:30-31`. Complies with SOUL "No Silent Fallbacks." Test: `test_brain_core.py:65`.
- [VERIFIED] `fake` intercept preserves old behavior for both `"fake"` and `"fake/x"` — `spec.partition("/")[0] == "fake"` matches both, same as the old `match backend` after partition. Returns `FakeActionModel([])` with WAIT baked in. Evidence: `factory.py:18`, `brain/core.py:45-46`.
- [VERIFIED] No circular import — `grep` confirms `seat_core` imports nothing from `understudy`; `brain/core.py` declares `__all__`. Evidence: rule-checker rule 10.
- [EDGE] (subagent disabled; reviewer-assessed) Boundary cases sound: empty spec `""` → not `fake` → seat_core `case _` raises loud; `"fake/anything"` → fake. `FakeStructuredModel` plays script then returns the WAIT default forever (no IndexError on exhaustion). No unhandled boundary.
- [SILENT] (subagent disabled; reviewer-assessed) No swallowed errors introduced: `parse_intent` raises `ModelError`; the run loop records `TimeoutError`/`ModelError` as `FrictionSignal` (telemetry, not silencing). No bare excepts in the diff.
- [TEST] Coverage gap (Medium, non-blocking): dispatch tests check class names only; no `decide()`-level test pins the shim's `Intent` binding for a real backend. Mitigated — the `.value` path is exercised by `FakeActionModel` in the wiring/seat-loop tests, so the critical path is safe. Near-dup `test_factory_fake_needs_no_default` (Low) — kept; it documents the no-default contract.
- [DOC] Three Low doc nits: stale `"see claude_p_model.py"` pointers in `manifest.py:16` and `test_manifest.py:16` (out-of-diff files; fast-follow); `parse_structured` in `__all__` is required by AC-1 but unexplained in the docstring. Non-blocking.
- [TYPE] (subagent disabled; reviewer + rule-checker assessed) `DecideResult.value: BaseModel` makes `seat.py:134` and `brain/core.py:46` static type-mismatches against `Intent`/`list[Intent]`. **No type checker runs in understudy (no mypy/pyright config, dep, or CI recipe), so no gate fails; runtime is correct.** Medium/Low type-hygiene, non-blocking. Clean fix (generic `DecideResult`) belongs to seat_core / the 159-4/5 companion, not this 2pt refactor.
- [SEC] (subagent disabled; reviewer-assessed) No new attack surface: LLM output validated by pydantic; the API-key-strip and subprocess logic moved unchanged into seat_core; no injection, no secrets logged. Naivety invariant untouched (perception/ and actuation/ not in the diff).
- [SIMPLE] (subagent disabled; reviewer-assessed) The refactor *removes* complexity (−282 lines, three duplicate modules gone). factory delegation is minimal. No over-engineering. Only the mildly redundant fake test (Low).
- [RULE] rule-checker: 17 rules / 43 instances, 5 hits at 3 sites — the two type sites (above) and `factory.py` missing `__all__` (Low; the new `brain/core.py` added one, factory didn't; pre-existing pattern). All doctrine rules (No Stubbing, No Silent Fallbacks, Naivety Invariant, Don't-Reinvent direction) compliant.

### Rule Compliance (python lang-review + SideQuest doctrine)
- **#1 Silent exceptions** — compliant: `seat.py` Timeout/ModelError → FrictionSignal; no bare except in diff.
- **#2 Mutable defaults** — compliant: `FakeActionModel.__init__(script: list[Intent])` has no default; `make_model`/`parse_intent` no defaults.
- **#3 Type annotations** — every function in the diff is annotated (params + returns present). The two type *mismatches* (value:BaseModel→Intent) are narrowing gaps, not missing annotations; non-blocking absent a type checker.
- **#6 Test quality** — compliant: no vacuous asserts; `.intent`→`.value` renames preserve real `IntentKind` checks; no skips.
- **#8 Unsafe deserialization** — compliant: `json.loads` + pydantic `model_validate`; no pickle/eval/shell.
- **#9 Async** — compliant: `await asyncio.wait_for(model.decide(...))`; `FakeStructuredModel.decide` is `async`, non-blocking.
- **#10 Import hygiene** — `brain/core.py` declares `__all__` ✓; `factory.py` missing `__all__` (Low finding); no star/circular imports.
- **Doctrine** — No Stubbing ✓ (real shim, fully wired), No Silent Fallbacks ✓ (loud unknown-backend), Naivety Invariant ✓ (untouched), Don't-Reinvent ✓ (duplication removed, correct direction).

### Devil's Advocate
Argue this is broken. The strongest case: the refactor silently widened a type contract. `DecideResult.intent: Intent` became `DecideResult.value: BaseModel` — understudy's run loop now *assumes* `.value` is an `Intent` and immediately calls `.kind`, `.text_input`, `.model_copy`, `.model_dump_json` on it (`seat.py:167-196`). Nothing in the type system enforces that assumption anymore; the guarantee lives only in the factory's `_make_model(spec, Intent)` call. A future edit that constructs a backend with a different output model, or a seat_core change that returns a non-Intent in `.value`, would sail past ruff and the test suite (which only ever feeds Intent) and explode at runtime with an `AttributeError` deep in actuation — exactly the kind of latent landmine the "no type checker" environment can't catch. A malicious or confused author adding a new backend to seat_core that returns a bare `BaseModel` would not be warned. Second angle: the deleted `test_backends.py` exercised the *understudy* backends' `decide()` against `Intent`-shaped JSON; the replacement seat_core tests exercise the same code against `Ping`. If seat_core's generic backends ever special-cased a field name that `Intent` has and `Ping` doesn't, understudy would break and no understudy test would notice. Third: `parse_structured` is now public API of `brain.core` via `__all__` — a name the module never owned — inviting callers to depend on a re-export that could vanish. 

Rebuttal: these are real but bounded. The Intent assumption is concentrated at one factory line and one assignment, both covered behaviorally by the wiring tests through `FakeActionModel` (which returns `DecideResult(value=Intent)` — so `seat.py:134`→actuation is exercised end-to-end with a real Intent). The Ping-vs-Intent divergence is hypothetical (seat_core backends are schema-agnostic — they pass `output_model.model_json_schema()` through; they never name a field). The coverage gap and the type narrowing are recorded as non-blocking Delivery Findings with the correct fix (generic `DecideResult`) routed to seat_core/companion scope. None reach Critical/High; none fail a gate; the runtime is green. The landmine is worth a fast-follow, not a rejection of a sound −282-line de-duplication.

**Pattern observed:** Thin-shim-over-generic-core, re-exporting under historical names — `brain/core.py:11-31`. Good pattern; the only refinement is propagating the generic type parameter so `.value` narrows to `Intent` (seat_core scope).

**Error handling:** Loud-fail preserved — unknown backend → `ValueError` (`seat_core/llm/factory.py:31`); malformed model output → `ModelError` → `FrictionSignal(MODEL_ERROR)` (`seat.py:144-152`). Verified.

**Handoff:** To SM (Camina Drummer) for finish-story.