# Epic 151: Sidecar Accounting Off the Narrator Hot Path (ADR-150)

## Overview

Implement **ADR-150**: move the narrator's 13 sidecar (`game_patch`) bookkeeping
fields off the single Opus generation, so the narrator turn is (almost) pure
storytelling. `action_rewrite` moves to the **pre-narration** IntentRouter; eleven
prose-readout fields move to a new **post-narration** Haiku extractor;
`private_segments` stays narrator-inline as the one generation-entangled field
(ADR-105 perception firewall). The payoff is **narrator attention returned to
prose craft** (the load-bearing project goal); removing ~4k uncached tokens/turn
is a secondary benefit.

**Priority:** P2
**Repo:** server (sidequest-server) — all stories; 151-7 also exercises orchestrator playtest scenarios
**Stories:** 7 (25 points)

**ADR-150 is the spec of record.** This context orients; the ADR governs. When in
doubt, the ADR's §Decision and §Implementation Notes win.

## Planning Documents

| Document | Relevant Sections |
|----------|-------------------|
| **ADR-150** (`docs/adr/150-sidecar-accounting-off-narrator-hot-path.md`) | §Decision (the three-way field split), §Implementation Notes → *Sizing the follow-up* (this epic's decomposition), §Consequences, the field-partition table in §Context |
| **ADR-113** (`docs/adr/113-intent-router-mechanical-engagement-spine.md`) | The live lineage this epic extends: pre-narrator `IntentRouter` + `run_dispatch_bank` + `dispatch_engagement_watcher`. The no-fallbacks discipline and atomic-cutover pattern are reused verbatim |
| **ADR-067** (`docs/adr/067-unified-narrator-agent.md`) | The constraint: one narrator, one Opus call, on the critical path. Forbids a competing *pre-narration* classifier; **blesses** non-blocking post-narration extraction |
| **ADR-105 / ADR-104** (`docs/adr/105-*.md`, `104-*.md`) | The perception firewall that keeps `private_segments` narrator-inline — sacrosanct, must not regress |
| **ADR-005** (`docs/adr/005-*.md`) | Background-first pipeline — the async/off-critical-path home for the cosmetic bucket-B fields |
| **ADR-102** (`docs/adr/102-*.md`) | `emit_tool` forced-tool-use protocol the extractor uses (validated structured input, no JSON parsing) |
| **ADR-112 / ADR-110 / ADR-134** (`docs/adr/112-*.md`, `110-*.md`, `134-*.md`) | `STABLE_SECTION_NAMES` cache-promotion (151-1); snapshot-slimming + cost-band context |

## Background

### The problem — ten pounds in a five-pound bag

A single narrator generation today does three jobs in one Opus call: (1) write
prose, (2) emit ~13 structured sidecar fields in a fenced `game_patch` block,
(3) fire up to 8 categories of native tool calls inline. The output contract that
teaches all of this — `sidequest-server/sidequest/agents/narrator_prompts/output_only.md`
— is **~15,961 bytes ≈ 3,990 tokens, ~94% bookkeeping, ~0% craft**, and (verified
2026-06-18) rides the **uncached** per-turn user message despite being
byte-identical every turn (it sits in `AttentionZone.Primacy` but is absent from
`STABLE_SECTION_NAMES`, so it defaults to `SectionBucket.User`).

Two costs compound: the token cost (~4k uncached/turn) and the far more expensive
**attention cost** — every paragraph of bookkeeping the model reads and every
field it stops to emit is attention not spent on prose. For a project whose reason
to exist is a narrator *good enough to fool a career GM*, the attention cost is the
one that matters.

### Why now — the lineage already built the two passes

ADR-113 is **live**: a pre-narrator Haiku pass (`IntentRouter.decompose` →
`run_dispatch_bank`) engages mechanical engines *before* the narrator, and a
post-narration watcher (`dispatch_engagement_watcher.py`) audits *after* it. The
"decide some bookkeeping before, derive the rest after" shape this epic needs is
already the lineage's skeleton — this is muscle on existing bone, not a new limb.
Most bucket-B fields are *already* reconstructed from prose by server catch-loops
(`_detect_missed_recurring_npcs`, `_auto_mint_prose_only_npcs`, `unmatched_*`
watchers) as safety nets; this epic promotes that capability from unaudited backup
to instrumented first-class.

## Technical Architecture

### The three-way field partition (the core design)

| Home | Fields | Why |
|------|--------|-----|
| **Pre-narration** (extend `IntentRouter`) | `action_rewrite` (`you`/`named`/`intent`) | Derivable from the player's raw input alone; the IntentRouter already reads it and does referent resolution. Also *feeds* visibility classification (which runs after the narrator), so sourcing it pre-narrator closes a current ordering hazard |
| **Narrator turn** (stays inline) | prose + `private_segments` | `private_segments` is generation-entangled — ADR-105 MOVE-not-COPY must be decided *as* prose is written; a post-hoc reader cannot recover information already leaked into PART 1. Rare/high-drama → *Cost Scales with Drama* justifies the inline complexity |
| **Post-narration** (new Haiku extractor) | `items_gained/lost/discarded/consumed`, `gold_change`, `companions_added/dismissed`, `npcs_present`, `mood`, `visual_scene`, `footnotes` | Readouts of prose the narrator already wrote. New Haiku `emit_tool` single-shot call, AsideResolver-shaped, on the live `CallType.CLASSIFICATION` ladder. **One exception:** `npcs_present.side`/membership is owned by the engine the IntentRouter already engaged, not extracted from prose — only the descriptive enrichment (appearance/pronouns/role) is extracted |

### Key files

| File | Role |
|------|------|
| `sidequest/agents/narrator_prompts/output_only.md` | The contract being split (shrinks to a prose + `private_segments` brief by 151-6) |
| `sidequest/agents/prompt_framework/bucket.py` | `STABLE_SECTION_NAMES` + `default_bucket_for_section` (cache-promotion, 151-1) |
| `sidequest/agents/orchestrator.py` | `NarrationTurnResult` (`:474-587`), `_extract_game_patch_json` (`:1015-1051`), cache predicate `_section_rides_cache` (`:132-146`), SDK prompt assembly (`:3882-3923`) |
| `sidequest/agents/intent_router.py` | The pre-narrator pass (`action_rewrite` new home, 151-3) |
| `sidequest/agents/aside_resolver.py` | The shape to copy for the post-extractor (single-shot Haiku `emit_tool`) |
| `sidequest/agents/model_routing.py` | `CallType.CLASSIFICATION → claude-haiku-4-5` (the extractor's route) |
| `sidequest/agents/dispatch_engagement_watcher.py` | The lie-detector pattern to mirror for `sidecar_extraction.mismatch` |
| `sidequest/server/narration_apply.py` | The bucket-B consumers + the catch-loops kept as the loud net |
| `sidequest/server/visibility_classifier.py` | Reads `action_rewrite.named`/`.intent` (rewire to the pre-pass value, 151-3) |

### Build sequence (data flow target)

```
player submit
  → IntentRouter.decompose         # NOW ALSO emits action_rewrite (151-3)
  → run_dispatch_bank              # engines engage (unchanged)
  → narrator turn                  # prose + private_segments ONLY (151-6)
  → post-narration Haiku extractor # bucket-B fields, emit_tool (151-2 skeleton; 151-4/5 cutover)
       ├─ pre-broadcast: npcs_present enrichment, items, gold, companions
       └─ async (ADR-005): mood, visual_scene, footnotes
  → narration_apply                # applies extracted fields; catch-loops as loud net
  → sidecar_extraction.mismatch    # lie-detector (151-2)
  → broadcast
```

Critical path: **151-2 (foundation) → {151-4, 151-5} → 151-6 → 151-7**.
**151-1 and 151-3 are independent free agents.** 151-2 runs the extractor in
*shadow mode* first (computes fields, emits OTEL, applies nothing) so the
lie-detector watches from day one before any field cuts over — the ADR-113
discipline. Each field-group cutover is **atomic** (retire the sidecar emission in
the same change that lights the extractor for that group); never run both
producers in parallel for one field (*one mechanism per problem*).

### Telemetry (OTEL discipline — the GM panel is the lie detector)

New spans: `sidecar_extraction.run` (model/latency/field-count/pre-vs-async),
`sidecar_extraction.{field}` (emitted/empty), `sidecar_extraction.mismatch`
(extractor-vs-state divergence), `intent_router.action_rewrite` (151-3). No-fallbacks:
extraction failure → ERROR span → one bounded retry → explicit GM-panel error;
catch-loops remain the loud safety net, never silent masking.

### Testing discipline

Fixture-based only (project memory `feedback_no_content_coupled_tests`) — synthetic
prose fixtures drive the real extractor; assert emitted fields **and OTEL spans**,
never source-text grep (CLAUDE.md *No Source-Text Wiring Tests*). Each cutover adds
a retirement guard asserting `narration_apply` no longer reads the migrated field
from the `game_patch` sidecar. Gate on the **full suite with content**, not a
scoped subset.

## Cross-Epic Dependencies

**Depends on:**
- **Epic 59 (Intent Router — ADR-113), LIVE** — provides the pre-narrator
  `IntentRouter`, `run_dispatch_bank`, and `dispatch_engagement_watcher` that this
  epic extends. No new work required there; this epic consumes the existing spine.

**Related (not blocking):**
- **ADR-110 / ADR-134 (cost observability)** — sibling concerns; this epic improves
  the per-turn cached/uncached split that those track. Fits Sprint 2624's
  "cost observability" theme.

**Depended on by:**
- None yet. ADR-150 flags a *Phase 2* (folding descriptive tool-owned categories —
  `apply_world_patch` location/atmosphere, `tick_tropes` day-advance — into the
  extractor) as out of scope here; a future epic may build on this one's extractor.
