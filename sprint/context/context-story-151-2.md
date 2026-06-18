---
parent: context-epic-151.md
workflow: tdd
---

# Story 151-2: Post-narration Haiku sidecar extractor — shadow mode + OTEL + lie-detector

## Business Context

This is the **foundation** of the epic: a new Haiku pass that reads the narrator's
emitted prose and produces the bucket-B sidecar fields, freeing the Opus narrator
from inline bookkeeping. Per ADR-113's discipline, it ships first in **shadow
mode** — it computes fields and emits OTEL, but applies nothing — so the
lie-detector is watching from day one before any field cuts over (151-4/151-5).
No field migration happens here; this is the skeleton everything else hangs on.

## Technical Guardrails

- **Shape:** model on `sidequest/agents/aside_resolver.py` — a single-shot
  Haiku-via-SDK `emit_tool` forced-tool-use call (ADR-102), returning a validated
  structured object (no JSON parsing).
- **Route:** `CallType.CLASSIFICATION → claude-haiku-4-5` (`model_routing.py`), or a
  new dedicated `CallType` if cleaner. Reuse the existing transport/ladder — no new infra.
- **Placement:** runs **post-narration, pre-broadcast**, in shadow (emits spans,
  mutates no state). Do NOT wire it to `narration_apply` yet.
- **OTEL (mirror `dispatch_engagement_watcher.py`):** `sidecar_extraction.run`
  (model, input prose length, field count, latency), `sidecar_extraction.{field}`
  (emitted/empty), `sidecar_extraction.mismatch` (extractor output vs existing
  state divergence).
- **No-fallbacks:** failure (timeout/transport/schema-invalid) → ERROR span → **one
  bounded retry** → explicit GM-panel error. Never silently proceed.
- **ADR-067 compliance:** passive post-narration read; one narrator, one Opus call,
  on the critical path. This is the pattern ADR-067 *blesses*, not the competing
  pre-narration classifier it forbids.

## Scope Boundaries

**In scope:**
- The extractor component + its prompt; the `emit_tool` call; the three
  `sidecar_extraction.*` spans; the no-fallbacks retry; shadow-mode wiring;
  fixture-driven tests incl. one wiring test through the real pipeline.

**Out of scope:**
- Retiring or applying ANY sidecar field (`action_rewrite`→151-3; transactional→151-4;
  npcs/cosmetic→151-5). Shadow only — applies nothing.
- `output_only.md` content changes (151-6).

## AC Context

1. **Structured output:** the extractor is a single-shot Haiku `emit_tool` call that
   returns a validated object for the bucket-B field set (no manual JSON parse).
2. **Shadow:** it runs post-narration/pre-broadcast and mutates no game state —
   `narration_apply` behavior is unchanged this story.
3. **Spans fire:** `sidecar_extraction.run` and `.{field}` emit with the documented
   attributes; drive a synthetic turn and assert the spans (not source-grep).
4. **Lie-detector:** `sidecar_extraction.mismatch` fires when the extractor's output
   contradicts existing state (e.g. an item the inventory cannot match).
5. **No silent fallback:** an induced extractor failure emits an ERROR span, retries
   once, then surfaces an explicit error; no silent narrator-only continuation.
6. **Wiring test:** a fixture turn flows orchestrator → narrator(stub) → extractor and
   asserts the extractor is reached and emits — proving it's connected, not just unit-tested.

## Assumptions

- The narrator's prose is available to a post-narration step before broadcast in the
  orchestrator flow.
- The `CallType.CLASSIFICATION` Haiku route and the `AsideResolver` `emit_tool`
  pattern transfer cleanly (they are the live precedent).
