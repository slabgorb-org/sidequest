---
parent: context-epic-71.md
workflow: tdd
---

# Story 71-40: Per-turn latency diagnosis — router decompose + narrator tool-loop p50/p95 + env-vs-code/iteration attribution

> **Combined story.** This merges former 71-22 (router decompose pass) and 71-26
> (narrator tool-loop pass) into a single per-turn latency diagnosis. The two LLM
> passes per turn are the two halves of the same player-facing stall; diagnosing
> them together keeps the percentile harness, the OTEL attribution discipline, and
> the env-vs-code narrative unified. The two surfaces remain distinct in code (the
> router decompose pass vs. the narrator tool-loop) and each must be instrumented
> on its own real path.

## Business Context

Each narration turn runs **two** LLM passes, and the 2026-05-27 `coyote_star` MP
playtest (plus the Glenross / `tea_and_murder` follow-up) flagged both as slow:

1. **Router decompose pass (Haiku, first pass).** Epic 59 (Intent Router —
   Mechanical-Engagement Spine) added a pre-narrator Haiku pass that decomposes
   every player action into a `DispatchPackage` *before* the narrator runs.
   ADR-113's latency budget (59-8 AC5) was an explicit **< 1.2s** — Haiku 4.5 was
   expected at ~0.3-0.5s, the rest absorbing pipeline overhead. The playtest
   measured **4-12s** for the decompose pass — 3-10x over budget. The table waits
   on the lie-detector spine before the narrator even begins.

2. **Narrator tool-loop (second pass).** On the ADR-101 default backend, each
   narration turn runs `AnthropicSdkClient.complete_with_tools`, a loop that calls
   the model, dispatches any requested tools, appends the results, and calls again —
   up to `max_iterations` times. A turn that keeps requesting tools (or a model that
   won't converge on a final text block) burns one full SDK round-trip per
   iteration, and solo-turn p95 latency balloons. The playtest flagged solo turns
   running long; the suspect is runaway tool-loop iterations.

This is a **diagnosis** story, not a fix. Instrument both passes, capture p50/p95
over a representative Glenross (`tea_and_murder`) run, and **attribute the cost** so
the next story (a fix) knows where to cut. It serves Keith-the-dev: the GM panel
(the lie detector) must show *why* a turn is slow, not just that it is. The two
passes bracket the full per-turn LLM cost.

## Technical Guardrails

### Shared: reuse-first for percentiles

- `sidequest/telemetry/validator.py` already has `_percentile(values, pct)`
  (line ~572) and uses it for p50/p99 (lines ~555-556). **Reuse it** for both the
  router p50/p95 and the solo-turn p95 — do not write a second percentile helper.

### Pass 1 — Router decompose (former 71-22)

**Primary instrumentation site — already emits latency:**
- `sidequest/agents/intent_router.py` — `IntentRouter.decompose` wraps the
  successful path in `intent_router_decompose_span(...)` and already sets
  `latency_ms` (measured via `time.perf_counter_ns()` around the whole attempt loop,
  lines ~222 and ~296-304), plus `retry_count` and `dispatch_count`. The span is
  `intent_router.decompose` (`SPAN_INTENT_ROUTER_DECOMPOSE` in
  `sidequest/telemetry/spans/intent_router.py`). **The latency signal already
  exists** — the work is capturing it across a run and decomposing it, not adding
  the first measurement.
- The per-attempt failure span `intent_router.failed` (`intent_router_failed_span`)
  carries `retry_count` — a high retry rate inflates total latency (each retry is a
  fresh SDK round-trip). Whether retries are firing is a first-order env-vs-code
  signal.

**Env-attribution anchors (the SDK call itself):**
- `sidequest/agents/llm_factory.py` — `_INTENT_ROUTER_MODEL = "claude-haiku-4-5-20251001"`
  (line ~119); `build_intent_router_llm()` (line ~199) builds the SDK-Haiku adapter
  the router injects. The raw SDK round-trip is the env cost; isolate it by timing
  *inside* `emit_tool` separately from the surrounding `decompose` bookkeeping.
- `sidequest/agents/model_routing.py` — `CallType.CLASSIFICATION → claude-haiku-4-5-20251001`
  (line ~28). Confirms the router is on Haiku, not accidentally routed to a slower
  model.

**Code-attribution anchors (prompt size / loop / schema):**
- `sidequest/server/intent_router_pass.py` — `_build_state_summary` (line ~75)
  builds the JSON state-summary the router sends. It uses
  `snapshot.model_dump(exclude_defaults=True, exclude_none=True)` and appends a
  `confrontation_types` projection. **Prompt-size is the prime code suspect**:
  measure the serialized `state_summary` byte/token length per turn and correlate
  with `latency_ms`. `action_length` is already a decompose-span attribute — add
  state-summary size alongside it.
- `_dispatch_tool_schema()` in `intent_router.py` (line ~94) =
  `DispatchPackage.model_json_schema()`. A large forced tool schema adds input
  tokens every call.

### Pass 2 — Narrator tool-loop (former 71-26)

**Primary surface — the tool loop:**
- `sidequest/agents/anthropic_sdk_client.py` — `complete_with_tools` (line ~281).
  - The loop: `for iteration in range(1, max_iterations + 1):` (line ~330).
  - `max_iterations: int = 8` (line ~290) — the existing ceiling.
  - Per-iteration span ALREADY exists: `with llm_request_span(model=model,
    iteration=iteration) as span:` (line ~356) wraps each SDK call. Iteration count
    is therefore already observable per call, but there is no *turn-level* "loop
    consumed K iterations" or "cap hit" summary span.
  - Non-convergence ALREADY raises loud: `raise AnthropicSdkLoopExceeded("Tool-use
    loop did not converge in {max_iterations} iterations")` (line ~610-612). The
    exception class docstring is at line ~104. **Do not weaken this fail-loud
    behavior** — the cap this story adds is about observability + an earlier,
    recorded throttle, not silencing the ceiling.

**Turn duration is already recorded:**
- `sidequest/server/websocket_session_handler.py` logs
  `session.narration_complete ... duration_ms=%s` (line ~801-807) with
  `result.agent_duration_ms`. That is the solo-turn wall-clock to feed the p95
  measurement.
- The cost-summary span at the end of `complete_with_tools` (around line ~979,
  "fires once per successful complete_with_tools return") is the natural home for a
  turn-level `iterations_used` attribute.

**OTEL discipline (CLAUDE.md):** the cap-hit decision is a subsystem decision and
MUST emit a span. Add a span (or an attribute on the existing per-turn cost/summary
span) recording `iterations_used`, the cap value, and a boolean/`decision` for
cap-hit, routed through the telemetry span registry (`sidequest/telemetry/spans/`,
following the `intent_router.py` span-route pattern).

### Shared: do NOT touch

- The confidence-gate logic or the fail-loud retry contract on the router
  (`_MAX_TOTAL_ATTEMPTS = 2`) — this story measures router behavior, it does not
  change it.
- Streaming deltas (71-23), the cost-ceiling / runaway-fingerprint alarm (Story
  61-4 — a separate guard), or the `claude -p` non-tooling path.
- Source-text wiring tests are banned (CLAUDE.md "No Source-Text Wiring Tests") —
  assert via span emission or fixture-driven behavior.

## Scope Boundaries

**In scope:**
- **Pass 1:** Capture p50/p95 of `intent_router.decompose` `latency_ms` over a
  representative Glenross (`tea_and_murder`) run (live or replayed scenario). Add
  the missing decomposition signals to attribute env vs code: the raw SDK-call
  duration (inside `emit_tool`) separated from the surrounding decompose
  bookkeeping, the serialized `state_summary` size, and the observed `retry_count`
  distribution. Emit as OTEL attributes on the existing spans (no new span family).
- **Pass 2:** Measure solo-turn p95 latency over a representative run; correlate
  with tool-loop iteration counts to confirm/deny tool-loops as the cause. Add a
  tool-loop iteration cap (a configurable max, defaulting to the current 8 or lower
  as diagnosis warrants) with an OTEL span/attribute recording `iterations_used`
  and a cap-hit signal that surfaces throttled turns on the GM panel.
- A written diagnosis with evidence covering both passes: numeric env-vs-code
  attribution for the router (e.g. "SDK round-trip = N s p95, state-summary = M
  tokens, retries fired on K% of turns") and an iteration-count correlation for the
  narrator loop.

**Out of scope:**
- Any latency *fix* (prompt slimming, caching the router system prompt, connection
  reuse, retry tuning, tool-description fixes that make the model converge faster) —
  downstream fix stories this diagnosis scopes.
- Streaming narration (71-23).
- Changing the 1.2s budget, the ADR-113 fail-loud contract, or the cost-ceiling
  terminal-refusal contract.

## AC Context

**AC1 — router p50/p95 captured.** Drive a representative Glenross turn set and
collect the `intent_router.decompose` `latency_ms` values. A test asserts the
measurement harness produces p50 and p95 from a list of captured decompose spans,
reusing `telemetry/validator.py:_percentile`. Edge case: a run where retries fired
must include the retry-inflated turns (do not silently drop `intent_router.failed`
attempts — they are part of the wall-clock cost the player feels).

**AC2 — router env-vs-code attribution with evidence.** The decompose span (or a
sibling span) must carry enough attributes to split total `latency_ms` into (a) raw
SDK round-trip and (b) in-process bookkeeping/prompt-assembly. A test asserts the
new attribute(s) are present and that raw-SDK ≤ total. Concretely: time `emit_tool`
independently and record both, plus the serialized `state_summary` size.

**AC3 — solo-turn p95 measured.** Drive a representative solo run and collect
per-turn `agent_duration_ms` (or the `complete_with_tools` summary duration);
compute p95 via `_percentile`. Test: feed the harness a list of recorded turn
durations, assert it yields a p95 number. Edge case: include a turn that hit
`max_iterations` (loop-exceeded) so the tail is represented.

**AC4 — runaway tool-loops identified + iteration cap with OTEL cap-hit span.** The
per-turn summary must expose `iterations_used` so a turn that consumed many
iterations is distinguishable from a one-shot turn. When the loop reaches the cap, a
span fires recording the cap value and `iterations_used`, AND the existing
`AnthropicSdkLoopExceeded` fail-loud behavior is preserved at the true ceiling.
Test: mock the SDK to request a tool every iteration; assert (a) the cap-hit span
emits with the cap value, (b) `iterations_used` is recorded, and (c)
`AnthropicSdkLoopExceeded` still raises (no silent swallow). If the cap is set below
8 and below the loop-exceeded ceiling, assert the cap-hit span fires at the cap
before the ceiling raise.

**AC5 — diagnosis artifact (both passes).** A diagnosis (committed as a
session/report artifact, not engine code) stating which cause dominates for each
pass, with the captured numbers. Testable precondition: the instrumentation from
AC1-AC4 is present and emits on the real `decompose` and `complete_with_tools`
paths.

**Wiring (required):**
- At least one test must drive the *real* `IntentRouter.decompose` (with a mocked
  `IntentRouterLLM` returning a valid `DispatchPackage`) and assert the new
  router-attribution attributes land on the emitted `intent_router.decompose` span.
- At least one test must drive the *real* `complete_with_tools` (mocked SDK
  transport) and assert the iteration/cap span actually emits through the watcher
  hub — not a unit test of a counter in isolation.

## Assumptions

- The `intent_router.decompose` span's `latency_ms` is the canonical router-pass
  cost and is already wired through `publish_event` to the GM panel (confirmed: the
  span route exists in `telemetry/spans/intent_router.py`).
- `result.agent_duration_ms` is the canonical solo-turn wall-clock and is already
  populated on the success path (confirmed at the `narration_complete` log site).
- A Glenross / `tea_and_murder` scenario can be driven headlessly (via the playtest
  driver or a scenario fixture) without a live human table; if not, the run may be
  captured from a recorded session's telemetry rows.
- Mocked-LLM tests cannot measure real network/env latency; the env-vs-code split's
  *real numbers* come from a live or recorded run, while tests only assert the
  attribution *instrumentation* is present and correct.
- The router retry path (`_MAX_TOTAL_ATTEMPTS = 2`) and the narrator
  `max_iterations=8` ceiling + `AnthropicSdkLoopExceeded` raise are unchanged
  fail-loud anchors; if diagnosis finds either retries or tool-loops dominate, that
  informs a downstream fix, not this story.

If any assumption proves wrong (e.g. the decompose span is not reaching the panel on
degraded turns — see 71-29 — or diagnosis shows tool-loops are NOT the solo-turn
cause), log a Design Deviation and notify SM.
