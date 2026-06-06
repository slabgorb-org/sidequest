---
parent: context-epic-91.md
workflow: tdd
---

# Story 91-1: Single SDK choke point — universal usage instrumentation (log line + llm.request span + cost_usd + caller tag on EVERY Anthropic call; wiring test: no AsyncAnthropic() outside the factory)

## Business Context

This is the keystone story of epic 91 ("Dark Spend"). The cost forensics on 2026-06-05
(pingpong **[COST-1]**, see `context-epic-91.md` Background) found that ~half the daily
Anthropic bill is invisible to all internal accounting: the Haiku 4.5 tier burns
**$3.3–3.5/day** and ~97% of that spend emits neither a `narrator.sdk.usage` log line nor
an OTEL `llm.request` span. Jaeger captured only **41** Haiku spans / 219k tokens over 72h
against ~**6.4M** billed — the bulk of Haiku traffic is structurally untraceable.

The root cause is architectural, not a bug: the cost design assumed "narrator = the bill,"
but the system grew additional spenders — Intent Router (ADR-113, `_IntentRouterLlm`),
asides (ADR-107, `_AsideLlm`), dungeon curate (`CallType.SCRATCH`) — each wired ad hoc with
its own `AsyncAnthropic` and its own (or absent) telemetry. Every other story in the epic
depends on this one: **91-2** (attribute the 8×/turn volume), **91-4** (cross-model runaway
detector), and **91-5** (daily reconciliation) all consume the caller tags and per-call-site
cost baselines this story lands. 91-2 is explicitly evidence-driven — it cannot start until
caller tags exist to read.

This converts a "mystery bill" into a "list of named callers." It is the OTEL Observability
Principle applied to money: if a subsystem isn't emitting spend telemetry, you can't tell
whether it's efficient or hemorrhaging. Per-turn unit economics make or break the business
model (operator, P1, 2026-06-05) — and the narrator Sonnet loop (the one path that already
reconciles cleanly at 6.6–7.6¢/turn) proves what "instrumented and healthy" looks like for
the rest.

## Technical Guardrails

**Key files** (all paths under `sidequest-server/sidequest/agents/` unless noted):

- `llm_factory.py` — the choke point. Today holds **two** non-narrator `AsyncAnthropic`
  construction sites: `_AsideLlm.__init__` (line 106) and `_IntentRouterLlm.__init__`
  (line 201). `_record_haiku_usage_on_span(span, resp)` (line 150) already stamps
  token/cache attributes onto an `llm.request` span — but it is **span-only**: no log line,
  no `cost_usd`, no caller tag, and `_AsideLlm.complete` opens no span at all.
- `anthropic_sdk_client.py` — the narrator's `AnthropicSdkClient` constructs the **third**
  `AsyncAnthropic` (line 216, behind `if sdk is None`). Its per-iter ledger (lines 479–490)
  is the pattern to **generalize**: `logger.info("narrator.sdk.usage iter=%d input=%d
  output=%d cache_read=%d cache_write=%d 5m=%d 1h=%d cost_usd=%.6f", ...)`. It computes
  `cost` via `compute_cost_usd(**cost_kwargs)` (line 465) and sets span attributes including
  `llm.cost_usd` (lines 467–476). `complete_with_tools` already accepts `caller: str =
  "narrator"` (line 299) but that tag currently only reaches the span (per the 82-9 comment
  at lines 595–602), **not** the log line — the log line emits neither `caller` nor `model`.
- `anthropic_cost.py` — `compute_cost_usd(...)` (line 100), model-aware via `_PRICING`
  (Sonnet/Haiku/Opus, lines 39–64) and `model_pricing()`. **Reuse, never duplicate** —
  unknown models raise `UnknownModel` (fail loud). `cost_band()` (line 79) classifies $/turn.
- `model_routing.py` — `CallType` StrEnum (NARRATION/NARRATION_IMPORTANT/CLASSIFICATION/
  SCRATCH, lines 18–23). Caller tags should derive from `CallType` + an explicit caller
  string (e.g. `intent_router`, `aside`, `dungeon_curate`, `narrator`).
- `telemetry/spans/llm_request.py` — `llm_request_span(model=..., iteration=...)`
  context manager (line 27); attribute set is documented in its docstring (lines 3–12) and
  already includes `llm.cost_usd`. Emit into this existing infra (ADR-103/132); do not
  reinvent.

**Patterns to follow:** the `narrator.sdk.usage` log line format and the `llm_request_span`
+ `compute_cost_usd` pairing already used by the narrator. This is **consolidation, not new
infrastructure** (epic design constraint, "reuse-first").

**What NOT to touch:** the narrator loop's behavior (its tool-loop, iteration cap, cache
tiers) must be unchanged — existing narrator tests stay green. The Opus rung
(`NARRATION_IMPORTANT` → `claude-opus-4-7`) is **intentionally unused**; zero Opus calls is
correct, do not "fix" it. Do not attempt cache repair (91-3), volume reduction (91-2), or
detector extension (91-4) here.

**No Silent Fallbacks:** keep the existing fail-loud posture — missing `ANTHROPIC_API_KEY`
raises at construction (factory lines 100, 195); an unknown model raises `UnknownModel`.
Do not swallow a missing-usage shape into a zero-cost log; if `resp.usage` is absent, that is
a real condition to surface, not paper over.

## Scope Boundaries

**In scope:**
- Consolidate Anthropic SDK construction so the factory is the **single** construction site;
  the non-narrator adapters (`_AsideLlm`, `_IntentRouterLlm`) stop constructing their own
  `AsyncAnthropic` and the narrator's `AnthropicSdkClient` construction is the one folded-to /
  shared path.
- A **uniform usage log line** + an `llm.request` span carrying model, fresh/cached token
  split (`input_tokens`, `output_tokens`, `cache_read`, `cache_write`), `cost_usd` (via
  `compute_cost_usd`), and a **caller tag** on **every** Anthropic call: narrator, intent
  router, asides, dungeon curate.
- A **wiring test** asserting no `AsyncAnthropic(` construction occurs outside the factory
  (see AC Context for the mechanism — note the server's "No Source-Text Wiring Tests" rule).
- An **integration test** proving a non-narrator call (e.g. an aside) emits **both** the log
  line (caplog) and the span (span exporter) through the production path.

**Out of scope:** fixing the ~8×/turn Haiku volume (**91-2**); repairing the dead Intent
Router cache / the 4,096-token floor guard (**91-3**); extending the ADR-134 runaway
detector cross-model (**91-4**); daily Admin-API reconciliation (**91-5**); any local-model
routing (**epic 92** / sibling local-classification epic). Do not change narrator cache
tiers or prompt content.

## AC Context

Derive testable ACs from the title. The server's **"Every Test Suite Needs a Wiring Test"**
rule is explicitly in force here, *and* its corollary **"No Source-Text Wiring Tests"** —
do not grep production source as an assertion.

1. **Single construction site + wiring test.** After consolidation, the only
   `AsyncAnthropic(...)` call lives in the factory (or the shared client it owns). Verify
   *behaviorally*, not by grepping source: e.g. monkeypatch/inject a fake `AsyncAnthropic`
   into the factory and assert every adapter (`build_aside_llm`, `build_intent_router_llm`,
   the narrator client) obtains its SDK through that one seam — an adapter that bypassed the
   factory would not receive the fake and the test would catch it. (A repo-grep guard *may*
   exist as a lint-style belt-and-suspenders, but the load-bearing assertion is the
   injection test.)
2. **Uniform usage log line on every call site.** Assert via `caplog` in the integration
   test, driving a real non-narrator call through the production code path (e.g. the aside
   resolver), that a `*.sdk.usage`-shaped line is emitted carrying model, tokens,
   cache split, `cost_usd`, and the caller tag. The current narrator line (lacking `caller`
   and `model`) is the baseline to extend uniformly.
3. **`llm.request` span with the caller-tag attribute on every call site.** Assert via an
   in-memory span exporter that the span fires for the non-narrator call and carries the new
   caller-tag attribute (e.g. `llm.caller`) plus the existing token/cost attributes that
   `_record_haiku_usage_on_span` / the narrator already set.
4. **`cost_usd` via existing `compute_cost_usd` for all models.** Every call site computes
   cost through `anthropic_cost.compute_cost_usd` (no duplicated pricing), correct for
   Haiku, Sonnet, and Opus.
5. **No behavior change to the narrator loop.** Existing narrator/`anthropic_sdk_client`
   tests remain green; the consolidation must not alter tool-loop iteration, cache tiers, or
   the runaway-detector pre-flight.

## Assumptions

- `compute_cost_usd` already covers Haiku/Sonnet/Opus pricing (`_PRICING` has all three,
  lines 48–63) — no pricing-table edits needed.
- The telemetry span infra (ADR-103/132, `llm_request_span`) accepts a new caller-tag
  attribute without any schema change — spans are attribute bags; the docstring lists
  current attributes but does not forbid additions.
- **Surprise / red-phase confirmation needed:** the dungeon materializer
  (`CallType.SCRATCH`) does **not** construct its own `AsyncAnthropic`. It already routes
  through `claude_client.complete_with_tools(..., caller="dungeon_curate")`
  (`dungeon/materializer.py` ~line 1213), i.e. through the narrator's `AnthropicSdkClient`.
  So curate is **already inside the choke point and already carries a caller tag** — but its
  tag currently only reaches the span, not the (to-be-uniform) log line. Confirm during the
  red phase that the curate path emits the new uniform log line with `caller=dungeon_curate`;
  treat "make the log line carry the caller for the already-tagged SCRATCH path" as in-scope
  rather than assuming a fourth construction site needs folding in. The two genuinely
  separate SDK constructions to consolidate are `_AsideLlm` (factory:106) and
  `_IntentRouterLlm` (factory:201).
- The caller-tag taxonomy derives from `CallType` + an explicit caller string; the four live
  caller values are `narrator`, `intent_router`, `aside`, `dungeon_curate`.
