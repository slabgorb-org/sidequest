# Epic 92: Local Classification Routing — Haiku → Ollama/qwen

## Overview

Take the high-frequency classification workload (Intent Router ADR-113, asides ADR-107, `CallType.SCRATCH` callers) off Anthropic billing by routing it to the local Ollama/qwen stack that epic 48 (Local-LLM Workstream, closed) already built and validated. The Haiku tier currently costs $3.3–3.5/day, 100% uncached, and grows with play volume; a local qwen-class model serves the same workload at $0 marginal cost with no cache-floor games. The flip is hard-gated on A/B evidence over the real captured router corpus — a misclassified dispatch is a SOUL/agency problem, not just a cost problem.

**Priority:** P1 — completes the make-or-break unit-economics work started in epic 91
**Repo:** sidequest-server
**Stories:** 4 (12 points)

## Planning Documents

| Document | Relevant Sections |
|----------|-------------------|
| **Epic 91 context** (`sprint/context/context-epic-91.md`) | Background (the [COST-1] forensics), Cross-Epic Dependencies (descope/sequencing contract with 91-3 and 82-10) |
| **Epic 48 archive** (`sprint/archive/48-2-session.md`, `48-4-session.md`) | What already exists: Ollama 0.23.1 on the M3 Ultra, qwen2.5:7b-instruct + qwen3-coder:30b, num_ctx Modelfile load-time pattern (per-request override forces ~28s KV reload — do not regress), `agent.backend="ollama"` OTEL attribution, A/B eval harness |
| **ADR-113** (`docs/adr/113-intent-router.md`) | The router contract being re-backed: forced tool_choice, `DispatchPackage` schema, confidence gating |
| **ADR-101** (`docs/adr/101-anthropic-sdk-narrator-backend.md`) | The per-call routing ladder this epic adds a local rung to; backend selection seam (`SIDEQUEST_LLM_BACKEND`) |
| **ADR-073** (`docs/adr/073-local-fine-tuned-model.md`) | The strategic lineage — local models for cost/latency-sensitive call classes |
| **Pingpong [COST-1]** (`/Users/slabgorb/Projects/sq-playtest-pingpong.md`) | Originating evidence: Haiku volume, dead caching, OTEL blind spot |

## Background

### Why now

Epic 91's forensics established that the Haiku tier is roughly half the daily bill, structurally uncached (the router's ~4.7k-token prefix sits near Haiku's 4,096 cacheable floor, where markers silently no-op), and firing ~8×/turn. Epic 91 makes that spend visible and bounded; this epic makes it ~zero. Classification is the workload where local models are *already proven in this codebase*: epic 48 shipped the backend (48-2: full playtest turn through Ollama, OTEL-attributed, within latency budget) and the measurement instrument (48-4: A/B harness, Claude vs local qwen on identical prompts), then closed. This epic is wiring, not building — Don't Reinvent.

### Why a hard A/B gate

The Intent Router is the mechanical-engagement spine (ADR-113 → ADR-123 dispatch bank). A router that misclassifies player intent silently degrades agency — the player attempts something and the wrong subsystem (or none) engages. Cost savings cannot buy that. Story 92-1 therefore precedes any routing change and must produce: classification agreement rate between Haiku and qwen on real captured `DispatchPackage` traffic, per-field disagreement analysis, and latency distribution. The flip in 92-2 only proceeds if agreement clears the threshold set in 92-1's review (proposal: ≥95% on dispatch selection, with all disagreements manually adjudicated — if qwen is *right* where Haiku was wrong, that counts for, not against).

### Why fail-loud, not fallback

The obvious "safe" design — fall back to Haiku when Ollama is unreachable — is exactly how dark spend gets re-created: a wedged Ollama process would silently move the entire classification load back onto the bill, and nobody would notice until the next reconciliation. Per No Silent Fallbacks: the local rung is explicit config; if Ollama is down, the call fails loudly and the operator decides. (The 91-5 dark-spend detector is the backstop if this doctrine ever erodes.)

## Technical Architecture

### The change, structurally

```
model_routing.py (ADR-101 ladder)            llm_factory.py / backend seam
┌──────────────────────────────┐             ┌───────────────────────────────┐
│ NARRATION            sonnet  │             │ anthropic_sdk (default)       │
│ NARRATION_IMPORTANT  opus*   │   today     │ claude-cli (opt-in)           │
│ CLASSIFICATION       haiku ──┼──────────►  │ ollama (opt-in, 48-2,         │
│ SCRATCH              haiku   │             │   validated e2e)              │
└──────────────────────────────┘             └───────────────────────────────┘
                 │ this epic: CLASSIFICATION/SCRATCH (+asides) resolve to the
                 ▼ ollama backend behind explicit config — not a model string
        ┌─────────────────────────┐   swap inside the Anthropic client
        │ OllamaClient            │
        │ (agents/ollama_client.py│
        │  num_ctx via Modelfile, │
        │  NOT per-request)       │
        └─────────────────────────┘
        * opus rung intentionally unused — leave it
```

Key design decision for 92-2: the routing ladder today returns a **model string** consumed by Anthropic-flavored adapters. A local rung means `resolve_model(CallType.CLASSIFICATION)` must resolve to a *backend + model* pair (or the adapters must consult a backend map). Prefer extending the existing `SIDEQUEST_LLM_BACKEND` factory seam (`llm_factory.build_*` functions) over inventing a new registry — the seam already exists and fails loud on unknown values.

### Key files

| File | Role |
|------|------|
| `sidequest-server/sidequest/agents/model_routing.py` | `CallType` ladder — gains backend-aware resolution for CLASSIFICATION/SCRATCH |
| `sidequest-server/sidequest/agents/llm_factory.py` | `_IntentRouterLlm` / `_AsideLlm` — the adapters whose construction switches on config; keep their public `emit_tool` / `complete` contracts identical |
| `sidequest-server/sidequest/agents/ollama_client.py` | Existing local backend (48-2). Honor the num_ctx Modelfile pattern — per-request override costs ~28s/call in KV reload |
| `sidequest-server/sidequest/agents/ab_eval_harness.py` | 48-4 deliverable — 92-1 runs it over captured router prompts; extend its corpus loader if needed, do not fork |
| `sidequest-server/sidequest/agents/intent_router.py` | Consumer whose `IntentRouterLLM` protocol the qwen adapter must satisfy (forced tool-call → structured `DispatchPackage`; qwen tool-calling fidelity is part of what 92-1 measures) |
| `sidequest-server/sidequest/handlers/player_action.py` (~:312) | Aside resolution site (92-3) |
| `sidequest-server/sidequest/telemetry/spans/agent.py` | `agent.backend` attribution — every local call must carry `backend="ollama"` so the GM panel proves the migration (OTEL Observability Principle) |

### Constraints

- **Structured output is the risk.** The router depends on forced tool-choice returning schema-valid `DispatchPackage` JSON. qwen tool-calling is not Anthropic tool-calling — 92-1 must measure schema-validity rate, and 92-2 must fail loud (typed error, OTEL event) on malformed output rather than retry-loop or fall back silently. ADR-113's `IntentRouterEmptyResponse` taxonomy extends naturally.
- **Latency budget:** 48-2 validated ≤3× Claude baseline for narration; classification is latency-sensitive per-turn overhead. 92-1 captures the distribution; 92-2's acceptance includes p95 within the budget set there. M3 Ultra keeps the model resident — avoid anything that evicts it (GPU memory coordination per ADR-046 if the daemon is rendering concurrently).
- **Instrumentation parity:** local calls bypass Anthropic billing but NOT accounting — they flow through the 91-1 choke-point telemetry with `cost_usd=0.0`, `backend=ollama`, caller tag. Free is a measurement, not an absence of one.
- **Leave the narrator alone.** Sonnet narration is healthy and out of scope. The Opus rung stays intentionally unused.

### Sequencing

```
92-1 (A/B gate) ──► 92-2 (router local rung) ──► 92-4 (playtest + cost proof)
        └─────────► 92-3 (asides; fold into 92-2 if trivial)
```

Cross-epic: 92-2 landing **descopes 91-3** (cache repair — no floor, no cache bill) and **frees 82-10** (router prompt slimming) from the 4,096-token constraint; 92-4 **consumes** 91-1 caller tags and 91-5 reconciliation as its proof instruments. Ideal order: 91-1 → 92-1 → 92-2 → 92-4, with 91-5 landed before 92-4.

## Cross-Epic Dependencies

**Depends on:**
- Epic 48 (closed) — Ollama backend, qwen models, num_ctx pattern, A/B harness. All exist; this epic wires them.
- Epic 91 — soft dependency: 92-4's cost proof uses 91-1 (caller-tagged baselines) and 91-5 (dark-spend reconciliation). 92-1 can start immediately.

**Depended on by:**
- Epic 91 story 91-3 — descoped when 92-2 lands (record the descope in 91-3's session, don't silently drop).
- Story 82-10 (IntentRouter state_summary slimming) — unblocked from the cache-floor constraint once routing is local; sequencing note lives in epic 91 context.
- ADR-073's broader local-model ambitions — this is the first production call class to go local; its A/B methodology and fail-loud backend seam become the template.
