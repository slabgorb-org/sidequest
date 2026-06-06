---
story_id: "82-10"
jira_key: ""
epic: "82"
workflow: "tdd"
---
# Story 82-10: IntentRouter state_summary slimming — extract+reuse narrator Phase B/C, OTEL before/after, re-verify p95 (ADR-110/82-9)

## Story Details
- **ID:** 82-10
- **Jira Key:** (none — project uses sprint YAML only)
- **Workflow:** tdd (compressed single-pass per right-size-ceremony; user-directed)
- **Points:** 5
- **Priority:** p2

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Repos:** sidequest-server

## Story Context

Direct user mandate 2026-06-06 ("slim down the prompt") during the 92-x A/B eval
operator session. The eval corpus (295 rows mined from 39 real saves) measured the
router's unslimmed state_summary at p50 34.9KB / p95 54.3KB — npcs up to 82% of the
payload, world_history 15KB median — and qwen2.5:7b latency p50 9.8s/p95 24s driven
almost entirely by prompt-eval over that bulk. The ADR-110 amendment prescribes the
exact fix this story shipped.

### Delivered (server PR #716, merged 2026-06-06)

- `sidequest/server/snapshot_slimming.py` (new) — `_PHASE_B_DROP_FIELDS`,
  `_apply_phase_c_projections`, shared `apply_snapshot_slimming()` moved verbatim
  from `session_helpers`; both consumers (narrator `_build_turn_context`, router
  `_build_state_summary`) call the shared seam.
- Router: party-consensus `party_location()` for the Phase C room/NPC projections;
  split party → loud pass-through (`projection_skipped=True`), never a gaslit-empty
  summary. Router-specific extra drop: `world_history` (corpus-measured, zero
  dispatch value; narrator registry untouched).
- New OTEL span `intent_router.state_summary_slimmed` (bytes_before/bytes_after +
  projection counts) — the amendment's mandated before/after evidence.
- 8 tests incl. production-path wiring + re-export identity pins. Full suite
  10,004 passed / 0 failed / 1,489 skipped.

### Measured result (re-mined from the same saves)

p50 34,868B → 12,024B (−66%); p95 54,316B → 21,957B (−60%).

## Design Deviations

### Dev (implementation)
- **Router-specific world_history drop added beyond the extract-and-reuse cut**
  - Spec source: ADR-110 amendment §Scope boundary
  - Spec text: "the few-KB allowlist is a measured follow-up, not this cut"
  - Implementation: one targeted negative drop (`world_history`) in the router
    builder, in addition to the shared Phase B/C cut
  - Rationale: corpus-measured 15KB median of chapter prose with zero
    dispatch-selection value; a single negative drop is not the positive
    allowlist the amendment defers (no precondition-gate audit required)
  - Severity: minor
  - Forward impact: none — narrator payload unaffected; documented in builder
    docstring
- **AC "re-verify p95" deferred to the next live capture**
  - Spec source: story title (re-verify p95 via latency_diag_82_9.py)
  - Spec text: "re-run scripts/latency_diag_82_9.py against a fresh capture"
  - Implementation: byte-level before/after measured offline on 303 real rows;
    live decompose p95 not yet re-captured
  - Rationale: requires live played turns post-merge; the 92-x A/B re-eval on the
    slimmed corpus (planned) and/or next playtest produces the p95 evidence via
    the new `intent_router.state_summary_slimmed` + existing decompose spans
  - Severity: minor
  - Forward impact: operator follow-up rides with the 92-2 enablement decision

## Delivery Findings

- **Improvement** (non-blocking): residual summary weight is `scenario_state`
  clue defs (9.6KB worst), whole in-scene NPC entries, and PC inventories — the
  deferred ADR-110 positive-allowlist follow-up now has measured targets.
  Affects `sidequest/server/intent_router_pass.py`. *Found by Dev during
  implementation.*
- **Gap** (non-blocking): 92-1 A/B eval evidence run executed this session
  (operator step previously missing): run 1 verdict NO-GO for qwen2.5:7b on
  UNSLIMMED prompts (26.7% agreement / 86% schema / p95 24s). qwen3-coder:30b run
  + slimmed-prompt re-eval pending; the 92-2 merged config default stays
  anthropic until a GO is recorded. Affects epic 92 enablement decision.
  *Found by TEA during eval.*

## Notes

- Cache-floor safety: the summary rides in the per-turn user message (never
  cacheable); the 4,096-token floor only ever constrained the system/tools
  prefix. The "82-10 is boxed in by the cache floor" framing in epic 91/92
  context was a category error — recorded here so it dies.
