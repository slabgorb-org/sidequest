# Epic 91: Dark Spend — LLM Cost Observability & Cache Integrity

## Overview

Make every Anthropic API token attributable, metered, and reconciled. Cost forensics on 2026-06-05 (pingpong **[COST-1]**) found ~half the daily Anthropic bill invisible to all internal accounting: the Haiku 4.5 tier burns $3.3–3.5/day with zero prompt caching, ~8× the expected call volume per turn, and ~97% of that spend emitting neither a usage log line nor an OTEL `llm.request` span. This epic closes the accounting gap at a single SDK choke point, repairs the dead Intent Router cache, extends the ADR-134 runaway detector across all models, and installs an automated daily reconciliation against the Anthropic Admin API so dark spend can never silently reappear.

**Priority:** P1 — per-turn unit economics make or break the business model (operator, 2026-06-05)
**Repo:** sidequest-server (91-5 also touches orchestrator `scripts/`)
**Stories:** 6 (17 points)

## Planning Documents

| Document | Relevant Sections |
|----------|-------------------|
| **/sq-llm-costs skill** (`.claude/skills/sq-llm-costs/SKILL.md`) | Entire document — the three-layer reconciliation methodology (server logs / Jaeger / Admin API), red-flags table, healthy baselines. 91-5 automates this skill's manual procedure. |
| **Pingpong [COST-1]** (`/Users/slabgorb/Projects/sq-playtest-pingpong.md`) | The originating finding with full measured evidence (Admin API per-model/per-key breakdown, Jaeger span census, log reconciliation) |
| **ADR-101** (`docs/adr/101-anthropic-sdk-narrator-backend.md`) | Per-call model routing ladder (Haiku/Sonnet/Opus), prompt-caching architecture — this epic extends its accounting story |
| **ADR-134** (`docs/adr/134-cost-runaway-detector.md`) | Rolling-baseline triggers + hard-kill ceiling — currently narrator-only; 91-4 extends it cross-model |
| **ADR-113** (`docs/adr/113-intent-router.md`) | The Intent Router whose caching is dead and whose call volume is unexplained (91-2, 91-3) |
| **ADR-103 / ADR-132** (`docs/adr/`) | Native OTEL via tool registry; WatcherHub — the span/event infrastructure 91-1 must emit into (reuse, don't reinvent) |

## Background

### The incident

A routine cache/cost analysis (GM session, 2026-06-05) compared the Console Cost page against the server's `narrator.sdk.usage` log lines and found the logs accounted for barely half the bill. Admin API ground truth (grouped by model and API key):

- **Haiku 4.5, 100% uncached:** `cache_creation = 0` and `cache_read = 0` org-wide, every day — despite `llm_factory.py` (`_IntentRouterLlm.emit_tool`) documenting a 1h `cache_control` marker + mandatory `extended-cache-ttl` beta header on a ~4,730-token tools+system prefix. The in-code comment itself names the trap: below Haiku's **4,096-token cacheable floor**, markers are *accepted by the API and silently never cache* — a No Silent Fallbacks violation embedded in API behavior. Warm reads would cut Haiku spend ~75% (~$2.5/day at current volume).
- **Volume anomaly:** Jun 4 ≈ 575 Haiku calls (output 57,463 ÷ ~100/call; per-call uncached input ≈ 5.2k matches the router prefix+turn shape) vs ~70 game turns = **~8 calls/turn**. Expected: ~1 (router) + rare asides. Growth correlates with something that landed around Jun 2–3 (uncached Haiku: 525k → 713k → 3.16M tokens/day over Jun 1→2→3).
- **Observability hole:** Jaeger captured only 41 Haiku `llm.request` spans / 219k tokens over 72h vs ~6.4M billed — the bulk of Haiku traffic emits no span. The Haiku adapters also emit no `narrator.sdk.usage`-equivalent log line, so log-based accounting structurally excludes them.

### Why this is architectural, not a bug-fix

The cost-accounting design assumed "narrator = the bill." The system has since grown additional spenders (Intent Router ADR-113, asides ADR-107, dungeon curate via `CallType.SCRATCH`) that were each wired ad hoc — separate `AsyncAnthropic` constructions, separate (or absent) telemetry. The fix is a **structural choke point**, not patches per call site: one factory through which every SDK call flows, emitting uniform usage telemetry with a caller tag. This is the OTEL Observability Principle applied to money: *if a subsystem isn't emitting spend telemetry, you can't tell whether it's efficient or hemorrhaging.*

### What is healthy (do not touch)

The narrator Sonnet loop fully reconciles against the Admin API: trivial uncached input, 76–82% cache hit rate, cost/turn stable at 6.6–7.6¢ since the 2026-05-31 cache-tier restructure (warm 1h re-writes ≈ 0–4/day, down from 92/day). **Zero Opus calls is intentional** — the `NARRATION_IMPORTANT` rung is deliberately unused (Sonnet is fine and cheaper); do not "fix" it.

## Technical Architecture

### Component view

```
                      ┌─────────────────────────────────────────┐
                      │  llm_factory (SINGLE CHOKE POINT, 91-1) │
                      │  - sole AsyncAnthropic construction site │
                      │  - usage log line per call (model,      │
                      │    tokens, cache split, cost_usd,       │
                      │    caller tag)                          │
                      │  - llm.request span per call            │
                      │  - feeds ADR-134 detector (91-4)        │
                      └───┬──────────┬──────────┬───────────────┘
        narrator loop ────┘          │          └──── dungeon curate (SCRATCH)
   (anthropic_sdk_client)     intent router            asides (ADR-107)
                              (ADR-113, 91-2/91-3)
                                     │
                      ┌──────────────▼──────────────────────────┐
                      │  Reconciliation (91-5, orchestrator)    │
                      │  instrumented totals  vs  Admin API     │
                      │  (scripts/anthropic_usage.py)           │
                      │  gap >10% → loud alert + GM dashboard   │
                      └─────────────────────────────────────────┘
```

### Key files

| File | Role |
|------|------|
| `sidequest-server/sidequest/agents/llm_factory.py` | Becomes the choke point. Today: `_AsideLlm`, `_IntentRouterLlm` construct their own `AsyncAnthropic`; `_record_haiku_usage_on_span` exists but is span-only |
| `sidequest-server/sidequest/agents/anthropic_sdk_client.py` | Narrator loop; emits `narrator.sdk.usage` (line ~480) — the pattern to generalize, and the third `AsyncAnthropic` site to fold in |
| `sidequest-server/sidequest/agents/anthropic_cost.py` | `compute_cost_usd` — already model-aware (Sonnet/Haiku/Opus pricing tables); reuse, do not duplicate |
| `sidequest-server/sidequest/agents/model_routing.py` | `CallType` ladder — the caller-tag taxonomy should derive from `CallType` + explicit caller string |
| `sidequest-server/sidequest/agents/intent_router.py`, `server/intent_router_pass.py`, `server/websocket_session_handler.py` (~:852, :923) | Router invocation paths — 91-2's hunt for the 8×/turn volume starts here |
| `sidequest-server/sidequest/dungeon/materializer.py` (~:1213) | `CallType.SCRATCH` consumer (idle during the incident window, but must be instrumented) |
| `sidequest-server/sidequest/telemetry/` | Span definitions + WatcherHub (ADR-132) — emit into existing infra |
| `scripts/anthropic_usage.py` (orchestrator) | Admin API client for 91-5 — already supports cost + usage reports; extend, don't rewrite |

### Design constraints

- **Reuse-first:** `compute_cost_usd`, `_record_haiku_usage_on_span`, `llm_request_span`, WatcherHub, and `scripts/anthropic_usage.py` all exist. 91-1 is consolidation, not new infrastructure.
- **Fail loud:** the floor guard (91-3) raises at client-build time if the combined cacheable prefix is below 4,096 tokens — never ship a marker that silently doesn't cache. Same doctrine for 91-5's reconciliation gap alert.
- **Wiring tests mandatory:** 91-1's acceptance includes a test asserting no `AsyncAnthropic(` construction outside the factory (grep-level or import-hook), plus an integration test proving a non-narrator call produces both the log line and the span through the production path.
- **Live-gated tests:** cache assertions (creation>0 then read>0) require real API calls — gate them like the composer's Gymnopedie smoke test; they must not run in default CI.
- **91-2 is evidence-driven:** do not guess at the 8×/turn caller. Land 91-1's caller tags, run one playtest, read the attribution, then fix.

### Sequencing

```
91-1 (choke point)  ──►  91-2 (attribute 8×/turn)
       │
       ├──►  91-4 (cross-model runaway)     [parallel after 91-1]
       └──►  91-5 (dark-spend detector)     [parallel after 91-1]
91-3 (cache repair)                          [independent; DESCOPE if local-routing epic lands first]
91-6 (warning gate)                          [independent, trivial]
```

## Cross-Epic Dependencies

**Depends on:**
- Epic 48 (Local-LLM Workstream, **closed**) — not a blocker, but context: its deliverables (Ollama backend, A/B eval harness 48-4) are what the sibling local-routing epic will wire. If that sibling lands first, **91-3 is descoped** — a local router has no cache floor and no cache bill.
- ADR-134 implementation (complete) — 91-4 extends the existing detector; it must not fork it.

**Depended on by:**
- **Sibling epic: Local Classification Routing** (to be created) — needs 91-1's caller tags and per-call-site cost baselines to prove the local migration's savings, and 91-5's reconciliation to verify the Haiku line actually goes to zero.
- Story 82-10 (IntentRouter state_summary slimming, backlog) — **design tension:** slimming the router prompt below 4,096 tokens makes Anthropic-side caching impossible (91-3's floor guard would correctly refuse it). Resolution order matters: if the router goes local (sibling epic), 82-10 can slim freely; if 91-3 lands instead, 82-10 must keep the combined prefix above the floor. Whoever picks up 82-10 must read this paragraph first.
- All future cost analyses — `/sq-llm-costs` Layer-1/Layer-2 coverage becomes total instead of narrator-only once 91-1 lands.
