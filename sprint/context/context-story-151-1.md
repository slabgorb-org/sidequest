---
parent: context-epic-151.md
workflow: tdd
---

# Story 151-1: Cache-promote the narrator output contract

## Business Context

The narrator's output contract (`output_only.md`, ~4k tokens) is byte-identical
every turn yet rides the **uncached** per-turn message, so we pay ~4k fresh input
tokens per narrator turn for nothing. This story is ADR-150's **companion
quick-win** (§Companion quick-win / Alternative A): promote the section into the
cached prefix. It is independent of the rest of the epic, shippable first, and
**necessary but not sufficient** — it fixes the *token* cost, not the *attention*
cost (that's the extraction work in 151-2…151-6). Take it early for cheap value.

## Technical Guardrails

- **Change:** add `"narrator_output_only"` to `STABLE_SECTION_NAMES` in
  `sidequest/agents/prompt_framework/bucket.py`. `default_bucket_for_section` then
  returns `SectionBucket.System`; combined with its `AttentionZone.Primacy` zone,
  `_section_rides_cache` (`orchestrator.py:132-146`) will let it ride the cached
  system block.
- **LANDMINE (not in the ADR — project memory `project_adr112_promotion_breaks_test_60_6`):**
  adding a section to `STABLE_SECTION_NAMES` promotes it into the cached prefix and
  **breaks `test_60_6_stable_prefix_live_drift`**, which pins the *old* volatile
  invariant. Update that test to the new stable invariant (this is the ADR-112
  cache-promotion pattern). Do not skip it; fix it.
- **Prerequisite check:** confirm `narrator_output_only` is byte-identical per
  session (no runtime interpolation). The 2026-06-18 deep-dive verified it; re-confirm.
- **Validate** the cache write/read deltas via the existing
  `narration.turn.cached_input_read_tokens` / `cached_input_write_tokens` spans.

## Scope Boundaries

**In scope:**
- Promote `narrator_output_only` to `STABLE_SECTION_NAMES`; update `test_60_6`.
- Verify byte-stability; validate cache deltas via existing cost spans.

**Out of scope:**
- Any change to `output_only.md` *content* (that's 151-6's shrink).
- Any extraction / field-cutover work (151-2…151-5).

## AC Context

1. **Cached:** `narrator_output_only` resolves to `SectionBucket.System` and rides
   the cached prefix — assert via `_section_rides_cache` / `compose_split_by_zone`
   placing it in the cached system block, not the per-turn user message.
2. **test_60_6 updated:** `test_60_6_stable_prefix_live_drift` reflects the new
   stable invariant and passes (it should now *expect* `narrator_output_only` in the
   stable prefix).
3. **Byte-stability:** a test (or assertion) confirms the section has no per-turn
   interpolation, so cache promotion is safe.
4. **Cache deltas observable:** after promotion, `cached_input_read_tokens` rises and
   uncached input falls on a second same-session turn (the cache hit).
5. Full suite (with content) green; no regression beyond the intended `test_60_6` update.

## Assumptions

- `narrator_output_only` is byte-identical per session (verified 2026-06-18). If a
  per-turn interpolation is discovered, STOP and log a Design Deviation — promotion
  would then be unsafe.
- `test_60_6` is the only test pinning this section as volatile. If another test also
  pins it, update both.
