---
story: 92-3
title: "Asides to local (ADR-107) — single-shot Haiku → qwen, same fail-loud config seam"
parent: context-epic-92.md
epic: 92
points: 2
type: feature
workflow: tdd
repo: sidequest-server
depends_on: [92-1]
related_adrs: [107, 101, 113, 073]
---

# Story 92-3 — Asides to local (ADR-107): single-shot Haiku → qwen

Route the out-of-band player-aside resolution call (ADR-107) off the Anthropic Haiku
tier onto the local Ollama/qwen backend, behind the **same explicit fail-loud config
seam** that 92-2 establishes for the Intent Router. This is the small, structurally
simpler sibling of 92-2 — `_AsideLlm.complete()` is plain text-in / text-out, not
tool-calling — and is a candidate to fold into the 92-2 PR if that adapter pattern
drops in cleanly.

## Business Context

Asides are **low-volume**. Unlike the Intent Router, which fires on the order of
~8×/turn (every player action, the per-turn classification spine of ADR-113/-123), an
aside is an occasional out-of-band "wait, can I X?" table-talk question (ADR-107) — rare
relative to the router's cadence. So the **direct dollar win here is small**: this is not
where the Haiku bill lives.

The real value is **uniformity**, not savings:

- **One local seam for all single-shot cheap calls.** Once 92-2 makes the router resolve
  to a backend+model pair behind the `SIDEQUEST_LLM_BACKEND` factory seam, the aside path
  is the *only other* single-shot Haiku caller. Migrating it means there is one config
  story for "cheap classification/Q&A goes local," not two — the next person reasoning
  about cost doesn't have to discover a second, separately-wired Haiku path.
- **No orphaned Haiku path left to become future dark spend.** Epic 92's whole premise
  (epic-92 context, "Why fail-loud, not fallback") is that any *silent* residual Haiku
  path is how dark spend re-creates itself. Leaving `build_aside_llm()` hardcoded to
  Haiku after the router goes local leaves exactly such an orphan: a low-but-nonzero,
  un-toggleable, easily-forgotten Anthropic caller. Closing it keeps the migration
  *complete* and the 91-5 dark-spend detector's job simple.

**Fold-into-92-2 option (explicit).** If 92-2's adapter/config pattern (`build_*` factory
switching on backend config, backend+model OTEL attribution, typed fail-loud on
unreachable Ollama) drops in cleanly enough that the aside variant is a near-verbatim
reuse, **deliver 92-3 as part of the 92-2 PR and record the fold** — in the 92-2 session
and by transitioning 92-3 to done by hand (a co-delivered story is not auto-closed by
`pf finish`; see the "bundled co-delivered story finish" memory). If the aside path needs
its own non-trivial work (e.g. the `complete()` text contract diverges from the router's
`emit_tool` contract in a way that needs its own adapter), keep it a standalone 2pt PR.
Decide at implementation time based on how 92-2 actually lands.

## Technical Guardrails

- **Plain completion, no tool-calling.** `_AsideLlm.complete(*, system, user) -> str`
  (`agents/llm_factory.py:108-122`) is strictly simpler than the router's forced-
  tool-choice → `DispatchPackage` structured output. There is **no schema-validity risk**
  here — qwen just has to return text. This is *why* the fold-if-trivial note exists: the
  hard part of 92-2 (qwen tool-calling fidelity, malformed-JSON handling) does not apply.
  The aside adapter must satisfy `AsideResolver`'s `AsideLLM` protocol with the same
  `complete()` signature — keep that public contract identical, swap only the backend
  underneath.
- **Same fail-loud / no-fallback doctrine as 92-2.** Today `_AsideLlm.__init__` already
  fails loud when `ANTHROPIC_API_KEY` is unset (`llm_factory.py:97-103`, "No silent
  fallback"). The local rung inherits that posture: if config selects Ollama and Ollama
  is unreachable, raise a **typed error + OTEL event — never silently fall back to Haiku**
  (epic-92 "Why fail-loud, not fallback"; No Silent Fallbacks). A wedged Ollama must not
  quietly re-route aside spend onto the bill.
- **The span hardcodes a lie — fix it.** At `handlers/player_action.py:376` the
  `SPAN_ASIDE_RESOLVE` span sets `span.set_attribute("model", "haiku")` unconditionally.
  After this change that attribute must become **backend/model-accurate** (e.g.
  `backend="ollama"`, model = the resolved qwen id) — the **GM panel is the lie detector
  and must not lie** (OTEL Observability Principle). The existing `asker_id`, `outcome`,
  `grounded_on`, `latency_ms` attributes stay; this adds/corrects the backend+model pair
  and `cost_usd=0.0` for the local path (instrumentation parity, epic-92 "Free is a
  measurement").
- **Aside quality bar = grounded answers, spot-check not A/B.** An aside answer is good
  when it is *grounded on game state* — the `AsideReadView` (character summary, region,
  inventory, rulebook, recent narration; `player_action.py:361-367`) the resolver is
  handed, surfaced via `res.grounded_on`. 92-1's eval method can **spot-check a small
  aside corpus** to confirm qwen stays grounded on the read view. A **formal A/B
  agreement gate is overkill at this volume** — the router earns its hard gate (a
  misclassification is a SOUL/agency failure firing every turn); a rare, read-only,
  non-state-mutating Q&A does not. State this judgment explicitly so the lighter bar is a
  decision, not an omission.
- **No cache work here, at all.** The aside system prompt is ~361 tokens and is
  **deliberately uncached** — it sits far below Haiku 4.5's 4,096-token cacheable-prefix
  floor, so a `cache_control` marker would be accepted but silently never cache, implying
  caching that does not happen (`llm_factory.py:108-115`). There is therefore **no cache
  marker to port, repair, or reason about** — unlike the router, whose combined
  tools+system prefix clears the floor (`llm_factory.py:137-147`). Do not add caching to
  this path under any backend.

## Scope Boundaries

**In:**
- Aside resolution path (`build_aside_llm` → `_AsideLlm`) routes to qwen behind the **same
  `SIDEQUEST_LLM_BACKEND` config seam** 92-2 uses (extend the factory; do not invent a new
  registry).
- `SPAN_ASIDE_RESOLVE` attributes corrected to be backend/model-accurate (no more
  hardcoded `model="haiku"`).
- Fail-loud unreachable-Ollama path: typed error + OTEL event, no Haiku fallback.
- Telemetry parity for the local path: `cost_usd=0.0`, `backend="ollama"`, caller tag
  (flows through the 91-1 choke-point instrumentation like every other local call).

**Out:**
- The Intent Router migration (that is 92-2 — this story *reuses* its seam, does not build
  it).
- Any change to **aside feature behavior or prompt** — the ADR-107 channel semantics
  (out-of-band, table-visible `ASIDE_ANSWER`, no turn consumed), the read-view shape, and
  the ~361-token system prompt are unchanged. This is a backend swap only.
- A **formal A/B eval gate** for asides — lightweight spot-check over a small corpus only
  (see Technical Guardrails); no per-field agreement threshold.

## AC Context

1. **End-to-end round-trip on local config.** With backend config = ollama, a player aside
   round-trips through qwen end-to-end at the **handler level** (drive
   `player_action.py`'s aside branch, ~:300-394, not just the adapter in isolation —
   CLAUDE.md "Every Test Suite Needs a Wiring Test"). The returned `AsideAnswerMessage`
   answer is **non-empty and grounded** (`grounded_on` reflects the supplied
   `AsideReadView`). Use a fake/stub Ollama client at the seam so the test is hermetic and
   doesn't require a live model.
2. **Span carries accurate backend/model attributes.** Assert via OTEL span capture (not
   source-grep — CLAUDE.md "No Source-Text Wiring Tests") that `SPAN_ASIDE_RESOLVE` on the
   local path emits `backend`/`model` matching the resolved qwen backend and `cost_usd=0.0`
   — and crucially that it **no longer emits `model="haiku"`** when config is ollama.
3. **Ollama-down is fail-loud AND out-of-band-safe.** With config = ollama and the backend
   unreachable: a **typed error + OTEL event** is raised, **no Haiku request is made**, and
   the aside failure **does not consume a turn or corrupt session state**. This is the
   load-bearing ADR-107 invariant (an aside is out-of-band: no `narrative_log` row, no
   scrapbook entry, no turn/round advance — ADR-107 §"No turn consumed", `player_action.py`
   comment at :388-390). Verify the *error path* preserves that out-of-band guarantee
   (turn manager round unchanged, no enqueue/advance/scrapbook/patch side effects) — a
   failed aside must degrade like a no-op, not a half-applied turn.
4. **Haiku config path stays green (regression).** With config = anthropic_sdk (default),
   the existing Haiku aside path is unchanged: round-trips, emits the (now backend-accurate
   for Haiku) span, and existing aside tests remain green.

## Assumptions

- **92-2 establishes the adapter/config pattern this reuses.** The backend+model
  resolution and the `SIDEQUEST_LLM_BACKEND`-driven factory switch land in 92-2; 92-3
  applies the identical pattern to the aside adapter. If folded, it is literally the same
  PR. If standalone, 92-2 must merge first (DEPENDS ON 92-1 in the tracker; the *adapter
  shape* dependency is on 92-2).
- **qwen handles the aside shape trivially.** The workload is a ~361-token system prompt
  plus a short player question, plain text out — well inside what the resident qwen model
  (epic 48: qwen2.5:7b-instruct, num_ctx set at Modelfile load time) handles without
  schema or context-window pressure. No num_ctx per-request override (epic-92 constraint:
  ~28s KV reload).
- The local Ollama backend and num_ctx Modelfile pattern from epic 48 are live and
  resident; this story wires the aside caller to them, it does not stand up infrastructure
  (Don't Reinvent).
