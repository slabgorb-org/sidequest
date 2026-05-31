---
story_id: "71-27"
jira_key: ""
epic: ""
workflow: "trivial"
---
# Story 71-27: Router emits combat dispatch with no registered handler — register or stop emitting

## Story Details
- **ID:** 71-27
- **Title:** Router emits combat dispatch with no registered handler — register or stop emitting
- **Jira Key:** (none — kanban-only)
- **Workflow:** trivial
- **Stack Parent:** none

## Technical Context

### Problem
The game router emits a combat dispatch event with no registered handler. This creates a loose end: either the event should be handled by a subsystem, or the emit should be removed if the event is spurious.

### Approach
1. **Locate the emit:** Search sidequest-server for the unhandled combat dispatch emission
2. **Determine intent:** Verify whether the event is meaningful or should be removed
3. **Register or remove:** Either add the missing handler or remove the spurious emit
4. **Verify wiring:** Add OTEL span to confirm the handler is reached (if keeping the event)
5. **Test:** Confirm no loose ends remain

### Acceptance Criteria
- [ ] Unhandled dispatch identified and documented (with file path and line number)
- [ ] Decision made: handler registered OR emit removed
- [ ] If handler registered: OTEL span added per OTEL Observability Principle
- [ ] If emit removed: verify no subsystem depends on it (grep for consumers)
- [ ] Branch pushed, PR created with decision rationale
- [ ] Tests pass (wiring test if handler added)

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-05-31T06:31:10Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-31T06:08:24Z | 2026-05-31T06:09:41Z | 1m 17s |
| implement | 2026-05-31T06:09:41Z | 2026-05-31T06:23:29Z | 13m 48s |
| review | 2026-05-31T06:23:29Z | 2026-05-31T06:31:10Z | 7m 41s |
| finish | 2026-05-31T06:31:10Z | - | - |

## Sm Assessment

Story scoped as a trivial cleanup of an observability/wiring loose end: the router emits a combat dispatch event that no handler consumes. This is squarely a "Verify Wiring, Not Just Existence" concern — a fire-and-forget emit with no consumer is exactly the kind of half-wired path the project principles warn against.

**Routing decision:** trivial phased workflow (setup → implement → review → finish), single repo (sidequest-server). Handing to Dev (Agent Smith) for implement.

**Guidance for Dev:**
- The decision is binary and must be made on evidence: grep for any consumer/handler registration of the combat dispatch event before choosing. If a subsystem *should* consume it (combat is a live subsystem), register the handler. If it's a dead emit, remove it — don't leave a stub handler (No Stubbing).
- If you register a handler, add an OTEL span on the dispatch decision per the OTEL Observability Principle — the GM panel must be able to confirm the handler fires.
- If you remove the emit, document the grep that proves no consumer depends on it.
- A wiring test is required if a handler is added (Every Test Suite Needs a Wiring Test).

## Dev Assessment

**Implementation Complete:** Yes

**Decision: STOP EMITTING (not register).** Evidence-based, per Morpheus's guidance.
The investigation (Explore + grep) established that the "Router" is the Intent
Router (`sidequest/agents/intent_router.py`, ADR-113), and that **`combat` is a
confrontation *type*** (`params["type"]`) routed through the registered
`confrontation` subsystem — it is **not** a subsystem key. The 7 registered
subsystems are confrontation, magic_working, scenario_clue, npc_agency,
distinctive_detail_hint, movement, reflect_absence. Registering a `combat`
handler would be a **stub for a non-subsystem** (No Stubbing). The root cause:
`SubsystemDispatch.subsystem` is a free `str` (deliberately permissive — runtime
registration is the authority, and ~7 test fixtures use placeholder names like
`lethal_strike`/`arcane_probe`, so a `Literal` was ruled out as it would break
those and fight the design). The bank drops unknown subsystems, but only *after*
the dead dispatch has polluted `turn_context.dispatch_package` (read by narrator
redaction + the post-turn watcher).

**Fix:** a registry-membership gate in the pre-narrator pass, mirroring the
existing `run_dispatch_precondition_gate` (story 59-8) exactly — drop any
dispatch whose `subsystem` is absent from the live registry (`get_registered()`,
the single source of truth, injected by the pass), **before** the bank and
before the package reaches the caller. Each drop emits a **distinct** loud
`intent_router.dispatch.unregistered` OTEL span (separate from the benign
world-shape `dispatch.gated` span, so the GM-panel lie-detector tells a router
*defect* apart from a world-shape skip). The bank's own unknown-subsystem skip
stays as a defense-in-depth backstop.

**Files Changed:**
- `sidequest/telemetry/spans/intent_router.py` — new `SPAN_INTENT_ROUTER_DISPATCH_UNREGISTERED` constant, `SpanRoute`, and `intent_router_dispatch_unregistered_span` context manager (GM-panel routing).
- `sidequest/agents/dispatch_precondition_gate.py` — new `UnregisteredDispatch` dataclass, pure `gate_unregistered_subsystems(package, registered)`, and OTEL wrapper `run_unregistered_subsystem_gate(...)`; `__all__` updated.
- `sidequest/server/intent_router_pass.py` — wired `run_unregistered_subsystem_gate(package, registered=set(get_registered()))` in immediately after `decompose`, before the precondition gate and bank.
- `tests/agents/test_dispatch_unregistered_gate.py` — new (8 tests: pure-fn drop/keep/sibling/no-copy, OTEL one-span-per-drop + zero-when-clean, + 2 behavioral wiring tests driving the real pass with the live registry).

**Tests:** 8/8 new green. Regression: 38 passing across `test_dispatch_precondition_gate`, `test_subsystem_registry`, `test_59_4_router_wiring`; full `tests/telemetry/` 344 green. Lint + format + pyright clean on all changed files.

**Wiring:** `test_router_pass_gates_unregistered_combat_dispatch` drives the real `execute_intent_router_pre_narrator_pass` with a `combat` dispatch and asserts it is absent from the returned package — proving the gate runs with the production registry, not just in isolation. No source-text wiring assertions (per CLAUDE.md "No Source-Text Wiring Tests").

**Handoff:** To review (The Merovingian).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 3 (2 medium, 1 low) | confirmed 0 blocking, 3 noted non-blocking |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — boundary paths covered by reviewer's own analysis (Devil's Advocate) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — silent-fallback path verified by reviewer (span-per-drop, no early exit) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — test quality assessed by reviewer (non-vacuous asserts, identity check) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — docstrings/comments reviewed by reviewer |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — type invariants verified by reviewer (idempotency subset, frozen dataclass) |
| 7 | reviewer-security | Yes | findings | 3 (all low) | confirmed 0 blocking; 1 captured as forward Delivery Finding |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — duplication noted by preflight + reviewer |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — rule compliance enumerated by reviewer below |

**All received:** Yes (2 enabled subagents returned; 7 disabled via `workflow.reviewer_subagents` and pre-filled)
**Total findings:** 0 confirmed blocking, 6 noted non-blocking (3 preflight + 3 security, all low/medium), 0 deferred

### Subagent finding dispositions
- **[preflight] gate-function duplication (MEDIUM)** — `gate_unregistered_subsystems` structurally mirrors `gate_inert_dispatches` (~30 lines). NOT a bug — deliberate pattern-parity with the reviewed 59-8 sibling. Extract a shared `_filter_package` helper only if a 3rd gate appears. Non-blocking. → noted, see Observation 5.
- **[preflight] no-op `with span(): pass` pattern (LOW)** — correct (span records on enter/exit) and already the established convention (`intent_router_confrontation_vocabulary_span`). Dismissed as non-issue: cites existing convention at `intent_router_pass.py:120`.
- **[preflight] span INFO vs ERROR status (MEDIUM/design)** — the routed `SpanRoute` event reaches the GM panel regardless of OTEL status code; a recurring LLM mis-classification is correctly INFO-loud, not an alert. Non-blocking design choice. → noted, see Observation 6.
- **[preflight] test module-level `_REGISTERED` snapshot (MEDIUM)** — production reads `set(get_registered())` fresh each turn; the test cache is safe for its assertions (combat never registered; 7 defaults always present). Non-blocking fragility. → noted, see Observation 7.
- **[security] VisibilityTag shared-by-reference via shallow `model_copy` (LOW)** — latent, not exploitable: the gate never mutates a kept dispatch's `VisibilityTag`, and the pre-gate `package` reference is overwritten immediately at `intent_router_pass.py:181`. Identical to the sibling gate — pre-existing pattern characteristic, not introduced here. Non-blocking. → captured as forward Delivery Finding (Improvement).
- **[security] shared `_keep` closure across per_player/cross_player (LOW)** — code-quality only; the `dropped` list drives span emission only, and the package validator blocks duplicate keys at construction. Same as sibling. Non-blocking.
- **[security] TOCTOU on `set(get_registered())` snapshot (LOW)** — design-acknowledged (comment at `intent_router_pass.py:181`); not exploitable in the single-process static-registry deployment. Non-blocking. → captured as forward Delivery Finding (constraint to document).

## Rule Compliance

Enumerated against `.pennyfarthing/gates/lang-review/python.md` (13 checks), CLAUDE.md, and SOUL.md, applied to every function/dataclass/span in the diff.

- **#1 Silent exception swallowing** — COMPLIANT. No `try/except`, `suppress`, or bare except in any changed file.
- **#2 Mutable default arguments** — COMPLIANT. `gate_unregistered_subsystems(*, package, registered)` and `run_unregistered_subsystem_gate(*, package, registered, tracer=None)` — no mutable defaults; `tracer` defaults to `None`.
- **#3 Type annotations at boundaries** — COMPLIANT. Public fns fully annotated (`-> tuple[DispatchPackage, list[UnregisteredDispatch]]`, `-> DispatchPackage`); span fn `-> Iterator[trace.Span]`; inner `_keep(dispatch: SubsystemDispatch) -> bool`. `**attrs: Any` on the span mirrors the sibling span and is structural.
- **#4 Logging coverage AND correctness** — COMPLIANT. Observability is via OTEL span (the canonical loud record per the OTEL Observability Principle), matching the sibling gate which also emits a span rather than a log. No f-string-in-log, no sensitive data.
- **#5 Path handling** — N/A (no filesystem ops).
- **#6 Test quality** — COMPLIANT. 8 tests with specific assertions (`subsystem == "combat"`, `idempotency_key == "k-combat-1"`, span-name counts, `filtered is package` identity). No `assert True`, no truthy-only checks, no skips. The local `from ... import` inside each test mirrors the sibling test file convention.
- **#7 Resource leaks** — COMPLIANT. Span used via `with` context manager.
- **#8 Unsafe deserialization** — N/A (no pickle/eval/yaml).
- **#9 Async/await pitfalls** — COMPLIANT. `run_unregistered_subsystem_gate` is a pure synchronous CPU op called synchronously inside the async pass (no `await` needed, no blocking I/O), identical to the existing precondition-gate call two lines below it.
- **#10 Import hygiene** — COMPLIANT. No star imports added; `__all__` correctly extended with `UnregisteredDispatch`, `gate_unregistered_subsystems`, `run_unregistered_subsystem_gate`.
- **#11 Input validation at boundaries** — COMPLIANT. The router-supplied `subsystem` string is used only as a set-membership test and as a structured OTEL attribute value (security subagent confirmed: no shell/SQL/template interpolation; psycopg3 parameterized downstream).
- **#12 Dependency hygiene** — N/A (no dependency changes).
- **#13 Fix-introduced regressions** — COMPLIANT. 382 tests green including the full telemetry suite and `test_59_4_router_wiring`.
- **CLAUDE.md "No Stubbing"** — COMPLIANT. No `combat` handler stub created; the dead emit is gated out (the chosen "stop emitting" path).
- **CLAUDE.md "No Silent Fallbacks"** — COMPLIANT. Every drop emits `intent_router.dispatch.unregistered`; no silent remap/default.
- **CLAUDE.md "Verify Wiring / Wiring Test / No Source-Text Wiring Tests"** — COMPLIANT. `test_router_pass_gates_unregistered_combat_dispatch` drives the real `execute_intent_router_pre_narrator_pass` with the live registry and asserts behavior, not source text.
- **CLAUDE.md OTEL Observability Principle** — COMPLIANT. New subsystem decision (drop) emits a routed span (`SPAN_ROUTES[...]`) the GM panel reads.
- **SOUL "Crunch in Genre / perception firewall (ADR-104/105)"** — COMPLIANT. Visibility neither broadened nor cross-pollinated (Observation 1).

## Reviewer Observations

1. **[VERIFIED] Perception firewall preserved** — `gate_unregistered_subsystems` rebuilds `per_player` and `cross_player` as independent per-slot `model_copy` comprehensions (`dispatch_precondition_gate.py:211-217`), byte-for-byte mirroring the reviewed sibling `gate_inert_dispatches:114-121`. Filtering only *removes* `SubsystemDispatch` entries; `PlayerDispatch.player_id`, `CrossAction` participants/witnesses, and each kept dispatch's `VisibilityTag` are untouched. A drop cannot broaden `visible_to` or move a per-player dispatch cross-player. Complies with ADR-104/105. `[SEC]`
2. **[VERIFIED] No silent fallback** — `run_unregistered_subsystem_gate` (`:243-248`) fires exactly one `intent_router.dispatch.unregistered` span per element of `dropped`, with no early-exit between the gate call and the loop; the zero-drop path emits zero spans (the correct quiet signal). `[SILENT]`
3. **[VERIFIED] Idempotency-key uniqueness preserved** — the gate is strictly subtractive, so the output key set is a subset of the original unique set; uniqueness holds by construction even though `model_copy` bypasses `DispatchPackage._unique_idempotency_keys` (Pydantic v2 does not re-validate on copy). `UnregisteredDispatch` is a `frozen=True` dataclass. `[TYPE]`
4. **[VERIFIED] Gate ordering correct** — the unregistered gate runs before the precondition gate (`intent_router_pass.py:181` → `:194`). An unregistered subsystem has no `_INERT_PRECONDITIONS` entry, so the precondition gate would pass it through; dropping the router defect first is the clean order and the inline comment documents the rationale. `[EDGE]`
5. **[LOW] Structural duplication of the two gate functions** — ~30 lines shared shape with `gate_inert_dispatches`. Deliberate pattern-parity (mirrors a live, reviewed function); a `_filter_package` extraction is only warranted at a third gate. Non-blocking. `[SIMPLE]`
6. **[LOW] Unregistered span is INFO, not ERROR status** — defensible: the GM panel consumes the routed `SpanRoute` event regardless of OTEL status, and a recurring LLM mis-classification is correctly "loud but not an alert." Documented in the span docstring. Non-blocking. `[DOC]`
7. **[LOW] Test `_REGISTERED` is a module-import snapshot** — production code reads `set(get_registered())` fresh each turn (correct); the test snapshot is safe for its assertions (combat is never registered; the 7 defaults are always present at import). Non-blocking fragility note. `[TEST]`
8. **[LOW] `cross_player` filter branch not directly exercised** — tests populate only `per_player`; the `cross_player` comprehension is correct by symmetry with the reviewed sibling (which is likewise per_player-only in its filter tests). Non-blocking. `[TEST]`
9. **[RULE] No project-rule violations** — full enumeration above; every applicable python-review check, CLAUDE.md principle, and SOUL perception rule is COMPLIANT.

## Devil's Advocate

Suppose this code is broken. Where would it bite? **First attack: empty registry.** If `get_registered()` returned `{}` at turn time, the gate would drop *every* dispatch and silently strip all mechanics from every turn — a catastrophic, invisible failure. Refuted: `_register_defaults()` runs at import of `sidequest.agents.subsystems`, and the pass imports `get_registered` from that very module, guaranteeing the 7 defaults are present before any turn; the wiring test confirms `combat` is dropped while the registry is populated. **Second attack: the false-drop.** The whole point of the story is `combat`, which is *also* a legitimate confrontation `params["type"]`. If the gate keyed on params instead of `subsystem`, it would wrongly nuke real combat. Refuted: the gate keys strictly on `dispatch.subsystem`, and `test_confrontation_kept_because_registered` plus the async `test_router_pass_preserves_registered_confrontation_dispatch` pin that a `confrontation` dispatch carrying `params={"type":"combat"}` survives untouched — the exact failure mode is covered. **Third attack: a `depends_on` dangling reference.** If a kept registered dispatch declared `depends_on` a dropped unregistered key, would the bank crash? Refuted: `_topo_sort` adds absent keys to `visited` rather than raising, so a dangling dependency on a never-engageable dropped dispatch is tolerated — no crash, and the dependency was inert anyway. **Fourth attack: injection via the router-supplied strings.** A hostile LLM emits a `subsystem`/`idempotency_key` with shell metacharacters or SQL. Refuted by the security subagent: both flow only as structured OTEL attribute values and parameterized psycopg3 args — no shell, template, or SQL string interpolation. **Fifth attack: visibility leakage.** The shallow `model_copy` shares `VisibilityTag` references; could downstream code widen one and leak? The hazard is real but latent — the gate never mutates a kept tag, and the pre-gate `package` reference is overwritten on the same line, so no live alias survives to observe a mutation; it is identical to the already-shipped sibling gate, introducing no new exposure. **Sixth attack: TOCTOU.** A subsystem registered between the gate snapshot and the bank read could diverge — acknowledged in-comment, not exploitable under the static single-process registry. None of these six escalates beyond LOW; the covered failure modes are exactly the dangerous ones (false-drop, empty registry), and they are pinned by tests.

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** LLM router → `DispatchPackage` (free-string `subsystem`) → `execute_intent_router_pre_narrator_pass` → `run_unregistered_subsystem_gate(registered=set(get_registered()))` drops any subsystem with no handler, emitting `intent_router.dispatch.unregistered` per drop → filtered package → precondition gate → bank → `turn_context.dispatch_package`. Safe because the gate is strictly subtractive (no visibility broadening, no key duplication) and every drop is loudly observable.

**Pattern observed:** Faithful mirror of the reviewed 59-8 precondition-gate pattern (pure decision fn + thin span-emitting wrapper) at `dispatch_precondition_gate.py:185-248` — the right call over a protocol-level `Literal` (which would have broken ~7 permissive-name test fixtures and fought the deliberate "permissive protocol, strict runtime" design).

**Error handling:** Unregistered subsystem → drop + routed OTEL span (`run_unregistered_subsystem_gate:243-248`); bank's own unknown-subsystem skip retained as defense-in-depth backstop. No silent path.

**Subagent coverage:** `[SEC]` security — 3 low, 0 blocking (1 forwarded). `[SILENT]` `[EDGE]` `[TEST]` `[TYPE]` `[SIMPLE]` `[DOC]` `[RULE]` — subagents disabled via settings; each domain assessed directly by the reviewer (Observations + Rule Compliance + Devil's Advocate). Preflight: 382 tests green, ruff/pyright clean.

**Handoff:** To SM (Morpheus) for finish-story.

## Delivery Findings

### Dev (implementation)
- **Improvement** (non-blocking): The `dispatch_engagement_watcher` and `dispatch_precondition_gate` each maintain their own subsystem-name lists (`_WITNESSES`, `_DISPATCHED_TYPE_KEY`, `_INERT_PRECONDITIONS`) parallel to the bank registry. They can drift from `get_registered()`. Affects `sidequest/agents/dispatch_engagement_watcher.py` and `dispatch_precondition_gate.py` (consider a parity test asserting these key sets are subsets of the live registry). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `VisibilityTag` is shared by reference through the gates' shallow `model_copy` and is not `frozen`. Not exploitable today (kept tags are never mutated and the pre-gate package reference is overwritten immediately), but a future perception rewriter retaining the original package alongside the filtered one could silently leak. Affects `sidequest/protocol/dispatch.py` (add `frozen=True` to `VisibilityTag.model_config`) and both gates in `sidequest/agents/dispatch_precondition_gate.py` (or `model_copy(deep=True)`). Fix both gates together. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The `set(get_registered())` snapshot in `execute_intent_router_pre_narrator_pass` is a design-acknowledged TOCTOU vs the bank's live `_REGISTRY` read; safe only while the registry is static after import. Affects `sidequest/server/intent_router_pass.py` (document the constraint: no `register_subsystem`/unregister after module init without revisiting this gate). *Found by Reviewer during code review.*

## Design Deviations

### Dev (implementation)
- No deviations from spec. The story explicitly offered "register OR stop emitting"; "stop emitting" was selected on evidence (combat is a confrontation type, not a subsystem) and implemented exactly as Morpheus's setup guidance framed it (loud OTEL, no stub, wiring test).

### Reviewer (audit)
- **Dev "No deviations from spec"** → ✓ ACCEPTED by Reviewer: the story offered "register OR stop emitting" as an explicit either/or; "stop emitting" is evidence-backed (combat is a confrontation type routed via the registered `confrontation` subsystem, not a subsystem key — registering would be a No-Stubbing violation). No spec divergence. No undocumented deviations found in the diff.