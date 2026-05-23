---
parent: context-epic-59.md
workflow: tdd
---

# Story 59-2: IntentRouter producer skeleton (Haiku-via-SDK) + remove DispatchPackage.degraded

## Business Context

This story is the **foundation** of Epic 59's Intent Router spine (ADR-113). Without
it, the dormant consumer plumbing merged in 2026-04 (DispatchPackage,
`run_dispatch_bank`, lethality_arbiter, perception redaction, five orchestrator
consumer sites) stays unused on the live SDK path, and the narrator continues to
self-report engagement fields unreliably — the SOUL "Illusionism" failure mode
that prompted the epic reframe.

**The user-visible problem this targets** (delivered via the downstream stories
that depend on this one): the narrator currently emits convincing prose about
confrontations / magic / clues without the corresponding mechanical engines
firing. Players see narrative consequence with no mechanical substrate — Keith
catches this immediately; Sebastien (mechanical-first) is locked out of seeing
what actually happened. The Intent Router fixes this by engaging engines
**before** the narrator runs, so narration describes already-real state.

This story specifically delivers the **producer half** (Haiku-driven intent
classification → DispatchPackage emission) without yet wiring it into the live
turn pipeline (that lands in 59-4). It also retires the no-fallbacks-violating
`DispatchPackage.degraded` field per the project memory rule
`feedback_no_fallbacks_hard`.

## Technical Guardrails

**Key files to modify or extend:**

- `sidequest-server/sidequest/agents/local_dm.py` — RENAME to `intent_router.py`.
  The class `LocalDM` renames to `IntentRouter`. The dormant `DispatchPackage`
  construction site at line 462 stays — only the LLM client backing it changes.
- `sidequest-server/sidequest/agents/llm_factory.py` — ADD an SDK-Haiku adapter
  named after the pattern at `llm_factory.py:88` (`AsideResolver` /
  `_ASIDE_MODEL`). New constant `_INTENT_ROUTER_MODEL`; new
  `IntentRouterLlmClient` (or equivalent) implementing the same `LlmClient`
  interface the existing `LocalDM` injects.
- `sidequest-server/sidequest/protocol/dispatch.py` — REMOVE
  `DispatchPackage.degraded: bool`, REMOVE `DispatchPackage.degraded_reason:
  Optional[str]`, REMOVE the `_degraded_requires_reason` pydantic validator. All
  callers updated.
- `sidequest-server/sidequest/telemetry/spans/` — RENAME or RETIRE
  `local_dm_decompose_span` (if present); ADD `intent_router.decompose` (INFO,
  fields: action_length, model, confidence_global, dispatch_count, latency_ms,
  retry_count) and `intent_router.failed` (ERROR, fields: reason, raw_preview,
  retry_count). Follow the existing span definition style under
  `sidequest/telemetry/spans/`.
- `sidequest-server/sidequest/agents/model_routing.py:28` — pre-existing,
  `CallType.CLASSIFICATION → claude-haiku-4-5`. **Use, do not modify.**

**Patterns to follow (from epic architecture):**

- **Reuse-first.** Every component already exists in tree as a rename or trivial
  adapter. See epic context "Critical reuse-first findings" — no new
  infrastructure. The SDK-Haiku adapter mirrors `AsideResolver`/`_ASIDE_MODEL`
  shape verbatim.
- **Fail-loud / no silent fallbacks.** Router failure (Haiku timeout, transport
  error, unparseable output, schema-invalid output) → ERROR-level
  `intent_router.failed` OTEL span → ONE bounded retry → if retry also fails,
  surface an explicit error. **No silent narrator-only continuation.** No
  `degraded` field, no "best-effort" path, no exception swallowing.
- **Constructor injection for the LlmClient.** The Haiku→local-model swap point
  in ADR-073's future arrives as injection, not rewrite. `IntentRouter.__init__`
  accepts the LlmClient as a parameter.

**Dependencies and integration points:**

- `sidequest/protocol/dispatch.py:DispatchPackage` — the return type. Must
  validate after `degraded` removal.
- `sidequest/agents/llm_factory.py:88` blueprint (`AsideResolver` pattern) — the
  SDK adapter copies its shape.
- `sidequest/agents/model_routing.py:28` (`CallType.CLASSIFICATION`) — already
  wired to `claude-haiku-4-5-20251001`.
- OTEL span family — follow conventions in `sidequest/telemetry/spans/*.py`.

**What NOT to touch:**

- The orchestrator turn pipeline (`orchestrator.py`). LIVE wiring is 59-4 scope.
- `run_dispatch_bank`, the subsystem handlers (chassis_voice, distinctive_detail,
  npc_agency, reflect_absence, lethality_arbiter, `redact_dispatch_package`).
  These are CONSUMER side and already merged.
- `_SDK_TOOL_OWNED_FIELDS` in `orchestrator.py:1088`. 59-4 amends it.
- `begin_confrontation` tool (`sidequest/agents/tools/begin_confrontation.py`).
  Its retirement is 59-4 scope.
- The `claude -p` legacy backend. ADR-013 still governs that path; ADR-113 only
  supersedes ADR-013 on the SDK path.

## Scope Boundaries

**In scope:**

- Rename `local_dm.py` → `intent_router.py`; `LocalDM` class → `IntentRouter`.
- Rewrite module docstring: remove "DORMANT" header, replace with "Production
  live-path producer per ADR-113" framing.
- Implement `IntentRouter.decompose(action: str, state_summary: dict) →
  DispatchPackage`. Returns schema-valid package on the synthetic fixture.
- Add SDK-Haiku adapter in `llm_factory.py` mirroring `_ASIDE_MODEL`/
  `AsideResolver` pattern. Uses `CallType.CLASSIFICATION → claude-haiku-4-5-20251001`.
- Remove `DispatchPackage.degraded` field, `degraded_reason` field, and
  `_degraded_requires_reason` validator. Migrate all references (callers + tests
  for the old degraded path) to assert fail-loud retry semantics instead.
- OTEL spans: `intent_router.decompose` (INFO) and `intent_router.failed`
  (ERROR). Retire/rename legacy `local_dm_decompose_span` if present.
- Fail-loud failure-mode tests for: Haiku timeout, transport error, unparseable
  output, schema-invalid output. Each emits ERROR span, attempts one bounded
  retry, surfaces explicit failure on retry-also-fails.
- Wiring test (per CLAUDE.md "Every Test Suite Needs a Wiring Test"): assert
  `IntentRouter` is importable and constructible with the SDK-Haiku adapter;
  comment that LIVE pipeline wiring happens in 59-4.

**Out of scope:**

- LIVE pipeline wiring (`orchestrator.py` hookup, `run_dispatch_bank` call site).
  → 59-4 (atomic confrontation cutover).
- Lie-detector watcher repurpose (`confrontation_intent_validator` →
  `dispatch_engagement.*` semantics). → 59-3.
- `begin_confrontation` tool retirement and `_SDK_TOOL_OWNED_FIELDS` cleanup.
  → 59-4.
- Magic, scenario_clue, NPC agency dispatch handlers. → 59-5, 59-6, 59-7.
- ADR-113 authorship (the ADR is referenced as accepted; 59-2 does NOT write it
  per the story description — it's already pending acceptance per the epic
  context's "ADR Plan" section). NOTE: the epic context AC list (item 6) says
  "ADR-113 written and accepted" within 59-2 — story description disagrees and
  defers that wording. **Per spec-authority hierarchy (story scope > epic
  context), the story description wins: 59-2 does not write ADR-113; it
  references it as the architectural authority.** Log this as a design
  deviation if needed.
- Playtest validation. → 59-8.

## AC Context

### AC-1: IntentRouter.decompose returns schema-valid DispatchPackage on synthetic input

**What must be true:** After rename, `IntentRouter` exposes `decompose(action,
state_summary)` returning a `DispatchPackage` that passes its own pydantic
validation. The fixture test supplies a deterministic synthetic
(action, state_summary) input and a synthetic Haiku response (mocked LlmClient),
and asserts the returned `DispatchPackage` matches expected dispatch shape.

**Edge cases:**
- Empty `per_player` and empty `cross_player` lists (quiet-turn no-op dispatch
  case) — still must be schema-valid.
- Single per-player dispatch, multiple per-player dispatches.
- A dispatch with `visibility` tags (so the perception layer downstream can
  honor them).

**Test approach:** Inject a mock LlmClient that returns a canned JSON string
matching the schema. Call `decompose`. Assert: (a) return type is
`DispatchPackage`, (b) pydantic validation passes, (c) dispatch contents match
the canned response.

### AC-2: DispatchPackage.degraded + degraded_reason fields REMOVED; validator REMOVED; references migrated

**What must be true:**
- `DispatchPackage` no longer has `degraded` or `degraded_reason` attributes.
- `_degraded_requires_reason` pydantic validator no longer exists in the model.
- Any test that previously built `DispatchPackage(degraded=True, ...)` is
  rewritten to assert the new fail-loud-retry path instead.
- Any non-test caller that read `package.degraded` is removed or rewritten.

**Edge cases:**
- A test that exercises "the degraded code path" must now exercise the
  fail-loud-retry path — the assertion changes from "degraded=True, narrator
  proceeds" to "ERROR span emitted, one retry attempted, explicit failure
  surfaced if retry fails."
- Searching the codebase for `degraded` should return zero matches in
  `protocol/dispatch.py` and zero matches outside of historical doc text.

**Test approach:**
- Compile-time / import-time test: `DispatchPackage(degraded=True)` raises
  `TypeError` or `pydantic.ValidationError` (extra field forbidden).
- Search-based test (optional): grep over `sidequest/` source for `degraded`
  attribute access on DispatchPackage instances returns zero hits.

### AC-3: SDK-Haiku adapter implemented in llm_factory.py via CallType.CLASSIFICATION

**What must be true:**
- A new class (e.g., `IntentRouterLlmClient`) exists in
  `sidequest/agents/llm_factory.py` implementing the same `LlmClient` interface
  the existing `LocalDM` injected.
- Internally it uses the Anthropic SDK with the model resolved via
  `CallType.CLASSIFICATION` (currently `claude-haiku-4-5-20251001`).
- The constant `_INTENT_ROUTER_MODEL` mirrors `_ASIDE_MODEL` pattern (module
  constant at the top of the file).
- The adapter's signature and behavior shape match `AsideResolver`.

**Edge cases:**
- Network timeout → adapter raises a typed exception that the router catches
  and converts to a fail-loud retry.
- Transport error (anthropic SDK exceptions) → same path.
- Successful response with malformed JSON body → adapter returns the raw text;
  the router's parsing layer is responsible for the unparseable case.

**Test approach:** Unit-test the adapter in isolation with a mocked Anthropic
client. Assert: (a) the correct model name is passed, (b) the correct CallType
is used, (c) exceptions propagate correctly to the router.

### AC-4: local_dm.py (renamed) docstring rewritten — DORMANT header REMOVED

**What must be true:** The module-level docstring at the top of
`sidequest/agents/intent_router.py` no longer reads "DORMANT" or "not invoked on
the live turn path as of 2026-04-28". It reads as a production producer
description per ADR-113 (suggested wording per the epic context: "Production
live-path producer for the Intent Router engagement spine, per ADR-113.").

**Test approach:** Docstring assertion test — `import sidequest.agents.intent_router;
assert "DORMANT" not in sidequest.agents.intent_router.__doc__; assert
"ADR-113" in sidequest.agents.intent_router.__doc__` (or equivalent
production-vs-dormant marker check).

### AC-5: Fail-loud failure path — ERROR span, one bounded retry, explicit surface; no silent fallback

**What must be true** (the lie-detector AC for this story):

Four failure modes — each must:
1. Emit an ERROR-level `intent_router.failed` OTEL span with `reason` and
   `raw_preview` fields populated.
2. Attempt exactly ONE bounded retry (the spec's §5 says "single visible
   retry").
3. If the retry also fails, surface an explicit error — NO silent narrator-only
   continuation, NO returning a degraded package, NO swallowing the exception.

Four failure modes to cover:
- **Haiku timeout** — adapter raises timeout exception
- **Transport error** — adapter raises Anthropic SDK exception (rate limit,
  auth, network)
- **Unparseable output** — Haiku returns text the router can't JSON-parse
- **Schema-invalid output** — Haiku returns JSON that fails pydantic
  validation on DispatchPackage

**Edge cases:**
- Retry succeeds (no fail-loud path needed) — assert ONE retry attempted, then
  success returned, with retry_count=1 on the success span.
- Retry also fails — assert TWO total attempts, ERROR span emitted twice (once
  per attempt), explicit exception raised on the second failure.
- The "no silent narrator-only continuation" assertion is the project-memory
  lie-detector: assert that no `DispatchPackage` (degraded or otherwise) is
  returned on the failure path — the function raises.

**Test approach:** Four test functions, one per failure mode, each:
- Mocks LlmClient to raise (or return malformed/invalid) on the first call.
- For "retry succeeds" variants: second call returns valid response.
- For "retry fails" variants: second call also raises/returns malformed.
- Asserts on: (a) OTEL span captured (use the existing span-capture test harness
  — see `tests/telemetry/` for the pattern), (b) retry count, (c) whether the
  function raises vs returns.

### AC-6: OTEL spans — intent_router.decompose + intent_router.failed; legacy span retired

**What must be true:**
- `intent_router.decompose` span (INFO) fires on every `decompose` call with
  fields: `action_length` (int), `model` (str), `confidence_global` (float or
  null), `dispatch_count` (int), `latency_ms` (int), `retry_count` (int 0 or 1).
- `intent_router.failed` span (ERROR) fires on each failed attempt with fields:
  `reason` (str — timeout/transport/unparseable/schema_invalid), `raw_preview`
  (str, truncated).
- `local_dm_decompose_span` (if it exists) is renamed or retired — search
  returns zero matches in source.

**Edge cases:**
- Successful decompose with one retry needed: `retry_count=1` on the success
  span; `intent_router.failed` ALSO fires once for the first attempt.
- Empty dispatch (quiet turn): `dispatch_count=0`, span still fires.

**Test approach:** Use the existing span-capture test harness (likely
`telemetry/test_helpers.py` or similar — Igor will discover). Drive `decompose`
through three scenarios (success, success-after-retry, two-failures) and assert
the expected span sequence and field values.

### AC-7: Wiring test — IntentRouter importable + constructible with SDK-Haiku adapter

**What must be true:** A test that:
- Imports `IntentRouter` from `sidequest.agents.intent_router` (catches
  import-time errors, missing dependencies, module-loading bugs).
- Constructs `IntentRouter` with an `IntentRouterLlmClient` (the SDK-Haiku
  adapter from AC-3).
- Asserts the constructor succeeds and produces a working instance.
- Includes a comment / docstring noting that LIVE pipeline wiring (orchestrator
  hookup, `run_dispatch_bank` invocation) lands in 59-4.

**Edge cases:**
- Without this test, AC-1's fixture test would still pass with a mock
  LlmClient — and we wouldn't catch the real adapter being broken until 59-4.
  This is the CLAUDE.md "wiring test" critical rule manifested for this story.

**Test approach:** A simple integration test in `tests/agents/test_intent_router_wiring.py`
(or similar) that does no network calls (the adapter constructor doesn't make
calls — just configures the SDK client) but asserts the full import+construct
chain works end-to-end without mocks.

## Assumptions

- **The dormant `local_dm.py` and `DispatchPackage` types are unchanged since
  2026-04-28.** If subsequent work has modified them, RED-phase test design may
  need to adjust. Verify via `git log -p sidequest/agents/local_dm.py
  sidequest/protocol/dispatch.py | head -100`.
- **The `AsideResolver` / `_ASIDE_MODEL` pattern at `llm_factory.py:88` is
  still the canonical blueprint** for per-call-type SDK adapters. If
  refactored, mirror the current shape, not the 2026-04 shape.
- **`CallType.CLASSIFICATION → claude-haiku-4-5-20251001`** in
  `model_routing.py:28` is still wired. Verify before writing tests that
  depend on this constant.
- **No existing live callers of `DispatchPackage(degraded=...)`** outside tests.
  If grep finds one, that's a Delivery Finding — the field can't be removed
  without coordinating the caller change.
- **OTEL span helpers and the test-side span capture harness already exist**
  in `sidequest/telemetry/` and `tests/telemetry/`. If not, the wiring test
  scaffolding for spans is a Delivery Finding back to SM (it should be a
  prerequisite for emitting any new OTEL).
- **The story does NOT write ADR-113.** Per spec-authority hierarchy (story
  scope > epic context), the story description's "Foundation story for the
  reframed Epic 59 Intent Router spine" framing supersedes the epic context AC
  list item 6's "ADR-113 written and accepted" — IF the ADR is missing at RED
  time, that's a finding back to SM/Architect, not work for this story.

If any of these assumptions prove wrong during RED, log a Design Deviation under
`### TEA (test design)` per the format in `guides/deviation-format.md`, and
surface the discrepancy as a Delivery Finding for downstream agents.
