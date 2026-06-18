---
parent: context-epic-151.md
workflow: tdd
---

# Story 151-5: Sidecar cutover II — npcs_present (engine-owned side) + async cosmetic fields

## Business Context

The second cutover handles the two trickier cases. `npcs_present` carries a
load-bearing `side`/membership that drives momentum routing — extracting it from
prose is exactly where today's "wrong side breaks momentum" bugs come from, so this
story sources `side`/membership from the **engine the IntentRouter already engaged**
and extracts only the descriptive enrichment from prose. The cosmetic fields
(`mood`, `visual_scene`, `footnotes`) are pure feed/UI signals with no same-turn
mechanical consumer, so they move **async** (ADR-005 background-first) — the player
reads prose immediately; these settle a beat later, like images and audio already do.

## Technical Guardrails

- **`npcs_present` split:**
  - Descriptive enrichment (`appearance`, `pronouns`, `role`) → from the 151-2
    extractor (prose readout). Consumer path: `narration_apply.py:5134-5206`.
  - **`side`/membership → from engine state**, NOT from prose. The
    IntentRouter-engaged confrontation seats opponents pre-narrator; read membership
    from there. This is the bug-class fix — a prose passage that misnames a side must
    NOT override the engine's authoritative side.
  - Keep `_auto_mint_prose_only_npcs` / `_detect_missed_recurring_npcs` as the net.
- **Cosmetic async:** `mood`, `visual_scene`, `footnotes` produced by a
  `asyncio.create_task`-spawned extraction after prose is broadcast (ADR-005).
  Consumers: `websocket_session_handler.py` mood/visual/footnotes forwards.
- **Atomic per group**, retirement guards, lie-detector watching.

## Scope Boundaries

**In scope:**
- `npcs_present` (enrichment extracted + `side`/membership from engine) and
  `mood`/`visual_scene`/`footnotes` (async) cutover + retirement guards + net retention.

**Out of scope:**
- Transactional fields (151-4); `output_only.md` shrink (151-6).

## AC Context

1. **npcs enrichment extracted:** descriptive fields come from the extractor.
2. **Side from engine:** `side`/membership is sourced from the engaged confrontation,
   not extraction — assert that a synthetic prose mislabeling a side still yields the
   engine's correct side (the bug-class regression test).
3. **Cosmetic async:** `mood`/`visual_scene`/`footnotes` are produced off the critical
   path; the prose broadcast does not block on them.
4. **Retired + net:** sidecar emissions removed (guards); `_auto_mint_prose_only_npcs`
   / `_detect_missed_recurring_npcs` still fire as the net.
5. Full suite (with content) green.

## Assumptions

- **Depends on 151-2 merged.** Blocked otherwise — log and notify SM.
- The IntentRouter-engaged confrontation holds authoritative `side`/membership at
  extraction time.
- Async settling of cosmetic fields is acceptable (ADR-005 precedent: images/audio
  already async; the UI tolerates a beat's delay for mood/visual/footnotes).
