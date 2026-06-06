---
parent: context-epic-92.md
workflow: tdd
---

# Story 92-2: Local rung in the model ladder — CallType.CLASSIFICATION/SCRATCH route to Ollama behind explicit config; fail loud if unreachable (NO silent Haiku fallback)

## Business Context

This is the story that removes the Haiku bill for classification "once and for all." Epic 91's
forensics established that the Haiku 4.5 tier is roughly half the daily Anthropic spend —
**$3.3–3.5/day, ~100% uncached, firing ~8×/turn** and growing with play volume — and that the
Intent Router (ADR-113, `_IntentRouterLlm`) is the every-turn driver of that cost. Epic 91 made
that spend *visible and bounded*; this epic makes it *~zero*. The classification workload is the
one place local models are already proven in this codebase: epic 48 (closed) shipped the Ollama
backend, the qwen models, the num_ctx Modelfile pattern, the `agent.backend="ollama"` OTEL
attribution, and the A/B eval harness. This story is **wiring, not building** — Don't Reinvent.

The strategic payoff is wiring up the dormant epic-48 deliverables into the live production turn
path for a real, high-frequency call class. Classification (`CallType.CLASSIFICATION`) and scratch
(`CallType.SCRATCH`) move off the bill behind explicit operator config; the narrator Sonnet loop
(healthy, reconciling cleanly) is untouched.

**Cross-epic effects — both must be RECORDED, not silently absorbed:**

- **91-3 (Haiku cache repair) is DESCOPED by this story landing.** Once the router runs locally,
  there is no Haiku call to cache and no 4,096-token cacheable floor to fight — the cache-repair
  work becomes moot. Per epic-92 context and the epic-91 sequencing contract, this descope must be
  **recorded in 91-3's session/sprint entry, not silently dropped.** A descope that vanishes is how
  the next person re-discovers a "missing" task and wastes a cycle.
- **82-10 (IntentRouter `state_summary` slimming) is FREED from the 4,096-token cache-floor
  constraint.** Today 82-10 is boxed in: the router prefix must stay *above* Haiku's 4,096-token
  cacheable floor (the floor guard checks the combined tools+system prefix, ~4,730 tok — see the
  `_INTENT_ROUTER_CACHE_TTL` comment block in `llm_factory.py`), so slimming the prompt could push
  it below the floor and silently disable caching. With the router local, no Anthropic floor
  applies; 82-10 can slim freely. Note this unblock in the 82-10 entry.

## Technical Guardrails

- **Gated on 92-1's GO decision.** This story does NOT start until 92-1 (the A/B gate) returns GO
  at its review threshold. Cite the threshold artifact 92-1 produces (classification-agreement rate
  on the real captured `DispatchPackage` corpus; proposal in epic context is **≥95% dispatch
  selection with all disagreements manually adjudicated — qwen being *right* where Haiku was wrong
  counts FOR, not against**). If 92-1 has not landed GO, this story is blocked; do not proceed on
  optimism.

- **Backend + model resolution — extend the factory seam, do not invent a registry.**
  `resolve_model(CallType.CLASSIFICATION)` in `model_routing.py` returns a **model STRING** today
  (`"claude-haiku-4-5-20251001"`), consumed by Anthropic-flavored adapters. A local rung needs a
  **backend+model** decision, not just a string swap. Per the epic's key design decision: extend
  the existing `SIDEQUEST_LLM_BACKEND` factory seam in `llm_factory.py` rather than build a new
  registry. The seam already exists and **already fails loud** on unknown values
  (`UnknownBackend(LlmClientError)`, `_VALID_BACKENDS` frozenset check) — mirror that pattern for
  the local-classification config. The concrete change is in **`build_intent_router_llm()`** (and
  its `_AsideLlm` sibling for 92-3): the builder reads config and constructs either the existing
  `_IntentRouterLlm` (Haiku/SDK) or a new qwen-backed adapter. **`_IntentRouterLlm.emit_tool`'s
  public signature and the `IntentRouterLLM` Protocol in `intent_router.py` must stay IDENTICAL** —
  the router class is constructor-injected with an `IntentRouterLLM` and must not change. Caveat:
  `_INTENT_ROUTER_MODEL` is a module-level constant *imported by* `intent_router.py`; any ladder
  rework must not break that import or the `model=` attribute fed to `intent_router_decompose_span`.

- **NO silent Haiku fallback when Ollama is unreachable — the epic's named doctrine.** A wedged
  Ollama process that silently routes load back to Haiku is *exactly how dark spend gets re-created*
  (epic-92 "Why fail-loud, not fallback"; CLAUDE.md No Silent Fallbacks; memory rule
  `feedback_no_fallbacks_hard`). When the configured local backend is unreachable, the call must
  raise a **typed error**, emit an **OTEL event**, and stop — the operator decides. Do NOT issue a
  Haiku request as a backstop. (The 91-5 dark-spend reconciliation detector is the safety net if
  this doctrine ever erodes — but it is a backstop, not a license to fall back.)

- **Structured-output handling — schema-validate qwen, fail loud on malformed.** The router depends
  on a forced tool-call returning a schema-valid `DispatchPackage` (the `tool_use` block's `input`
  dict, ADR-102). **qwen tool-calling is not Anthropic tool-calling**, and the existing
  `OllamaClient.capabilities().supports_tools` is `False` — today it only does text completion
  (`/api/generate`, `/api/chat`) returning a `ClaudeResponse`. The new adapter must bridge qwen's
  output into the same `dict[str, Any]` `emit_tool` returns. Whatever the bridge (qwen native
  tool-calling via the Ollama `/api/chat` `tools` param, or a forced-JSON prompt + parse), **the
  output must be schema-validated against `DispatchPackage` and fail loud on malformed output** —
  extend the `IntentRouterEmptyResponse` taxonomy (in `llm_factory.py`) with a typed local-malformed
  error carrying a `raw_preview`, surfaced the same way (OTEL `intent_router.failed` span with a
  distinct `reason`). NEVER a silent retry-loop and NEVER a fallback. The router's existing bounded
  retry (`_MAX_TOTAL_ATTEMPTS = 2` with the schema-correction suffix in `intent_router.py`) is the
  *only* documented retry bound — do not add an unbounded local retry beneath it.

- **num_ctx via Modelfile ONLY.** Per the 48-2 finding, a per-request `num_ctx` override forces a
  full **~28s KV-cache reload** per call. The context size must be baked into the qwen Modelfile at
  load time; the adapter must NOT pass a per-request `num_ctx`. Treat any per-request context
  override as a regression.

- **Instrumentation parity — free is a measurement, not an absence of one.** Local calls bypass the
  Anthropic bill but NOT accounting. Every local classification call must flow through the **91-1
  choke-point telemetry** (the `llm.request` span / usage-log line) carrying `cost_usd=0.0`,
  `backend=ollama`, and the caller tag. The existing `OllamaClient` paths already open
  `agent_call_span`/`agent_call_session_span` with `backend="ollama"`, but the *cost/choke-point*
  parity is the 91-1 seam, not the agent.call span — the adapter must emit the same `llm.request`
  attributes the Haiku path emits (`_record_haiku_usage_on_span` is the Haiku precedent), with
  `cost_usd=0.0`. The GM panel must show local calls as instrumented zero-cost, not as a gap.

- **`agent.backend="ollama"` span attribution (48-2 precedent).** Carry the `backend="ollama"`
  attribute through so the GM panel can *prove* the migration — distinguishing "router ran locally
  at $0" from "router silently fell back to Haiku." This is the OTEL Observability Principle applied
  to the migration itself.

- **GPU memory risk (ADR-046) — note, don't solve here.** The M3 Ultra shares GPU memory between
  Ollama (keeping qwen resident) and the image daemon (Z-Image). Per ADR-046's budget coordinator,
  concurrent daemon rendering could evict the model and trigger a reload. Flag this as a known risk
  for 92-4's playtest; this story should not try to solve GPU coordination, only avoid making it
  worse (e.g. no model eviction on the call path).

## Scope Boundaries

**In scope:**
- `CallType.CLASSIFICATION` + `CallType.SCRATCH` routing to the Ollama backend behind explicit
  config (extend `SIDEQUEST_LLM_BACKEND` factory seam / a classification-backend config).
- A qwen adapter satisfying the **`IntentRouterLLM` protocol unchanged** (`emit_tool` returns a
  schema-valid `DispatchPackage` dict); `intent_router.py` is not modified except possibly its
  error-taxonomy imports.
- The **fail-loud unreachable path**: typed error + OTEL event, NO Haiku request issued.
- **Telemetry parity**: `cost_usd=0.0`, `backend=ollama`, caller tag through the 91-1 choke point.
- Config documentation (how an operator enables the local rung; the default remains an operator
  decision surfaced at review).

**Out of scope:**
- **Asides** (`_AsideLlm`, ADR-107) → **92-3** (fold in only if trivial; named separately here).
- **Playtest cost-proof** → **92-4** (consumes 91-1 caller tags + 91-5 reconciliation).
- **Narrator / any Sonnet-class call** — `CallType.NARRATION` / `NARRATION_IMPORTANT` stay on
  Anthropic. The Opus rung stays intentionally unused. Leave the narrator alone.
- **Fine-tuning** qwen — out of scope; this uses the epic-48 models as-is.
- **Removing the Haiku code path.** The config still *selects* it; `_IntentRouterLlm` and
  `_INTENT_ROUTER_MODEL` stay. The **default config value is an operator decision to surface at
  review, NOT a hardcode** — do not delete or default-disable the Anthropic path.

## AC Context

All acceptance criteria are testable; each maps to a guardrail above.

1. **Live round-trip (wiring / e2e).** With the local-classification config enabled, a *production*
   Intent Router pass (`IntentRouter.decompose` via the real `build_intent_router_llm()` builder)
   round-trips a real `DispatchPackage` through qwen — schema-valid output, dispatches present.
   Use the scene harness (ADR-092) or a live-gated test (qwen must be resident). This is the wiring
   test: prove the qwen adapter is *actually constructed and called* by the production builder, not
   just unit-tested in isolation.

2. **Unreachable = fail loud, NO Haiku issued.** With Ollama down (assert via a transport-layer
   mock / injected `http_fn` that raises), the turn fails with the **typed error + OTEL event**, and
   **no Anthropic/Haiku request is issued** — assert the Anthropic transport (`messages.create`) was
   never called. This is the doctrine test; it is the most load-bearing AC.

3. **Malformed qwen output = typed error + OTEL, bounded retry.** Inject qwen output that fails
   `DispatchPackage` schema validation; assert a typed error + an `intent_router.failed` OTEL span
   with a distinct local-malformed `reason`, and that retries stay within the documented bound
   (`_MAX_TOTAL_ATTEMPTS`), with no silent fallback.

4. **Telemetry parity.** A successful local call shows `backend=ollama`, `cost_usd=0.0`, and the
   caller tag **through the 91-1 choke point** (the `llm.request` span / usage line), not only the
   `agent.call` span. Assert the span attributes.

5. **Haiku config path still green (regression).** With the local config OFF (default Anthropic
   path), the existing `_IntentRouterLlm` Haiku path round-trips unchanged — existing intent-router
   and cache-floor tests stay green. The `emit_tool` signature and `IntentRouterLLM` protocol are
   byte-for-byte unchanged.

## Assumptions

- **92-1 returned GO at threshold.** This story is gated on it; if 92-1's review has not recorded a
  GO with a cited agreement rate, STOP — the cost win does not buy a silent agency regression.
- **91-1 is merged** (the single-SDK choke-point telemetry seam — `llm.request` span + `cost_usd`
  + caller tag — exists). The instrumentation-parity AC depends on it. **If 91-1 is NOT yet merged,
  emit the equivalent `llm.request`/`cost_usd=0.0`/`backend=ollama` telemetry locally in the qwen
  adapter and reconcile to the choke point later — but FLAG the ordering** in the session so the
  reconciliation is not forgotten. (Ideal epic order is 91-1 → 92-1 → 92-2 → 92-4.)
- **OllamaClient gaps found in my read, all bridgeable within 5 pts:**
  - `OllamaClient` exposes only text completion (`send_with_model` / `send_with_session` /
    `send_stateless`) returning `ClaudeResponse`; **it has no `emit_tool`** and
    `capabilities().supports_tools` is `False`. The new qwen adapter must implement `emit_tool`
    on top of the existing HTTP client (or a thin wrapper), bridging qwen output → a schema-valid
    `DispatchPackage` dict. The HTTP transport, error types (`OllamaClientError`,
    `UnknownModel`), and `backend="ollama"` attribution already exist and are reusable.
  - `DEFAULT_MODEL_MAP` maps hints (`haiku`/`sonnet`/`opus`) to `sidequest-*` Modelfile names; the
    classification adapter needs its qwen model present in the map (or an explicit hint), and an
    unmapped hint already raises `UnknownModel` — fail-loud, reuse it.
  - The existing `OllamaClient` transport error path (`OllamaClientError` on connection failure) is
    the natural seam for the AC-2 unreachable-detection — surface it as the typed fail-loud error
    rather than catching and falling back.
- Epic-48 infrastructure (Ollama 0.23.1 on the M3 Ultra, qwen models, num_ctx Modelfile pattern,
  A/B harness) is present and validated; this story wires it, per the epic's "wiring, not building."
