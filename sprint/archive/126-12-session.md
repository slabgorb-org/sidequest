---
story_id: "126-12"
jira_key: ""
epic: "126"
workflow: "architecture"
---
# Story 126-12: [NARRATOR][ADR] Design: move sidecar accounting off the narrator hot path

## Story Details
- **ID:** 126-12
- **Jira Key:** (none — design/ADR story)
- **Workflow:** architecture
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** architecture
**Phase:** setup
**Phase Started:** 2026-06-18T19:10:40Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-18T19:10:40Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Architect (design)

- **Deliverable:** `docs/adr/150-sidecar-accounting-off-narrator-hot-path.md` (status: proposed). ADR indexes regenerated (`scripts/regenerate_adr_indexes.py`).
- **(Improvement, non-blocking)** The ~4k uncached tokens/turn claim is VERIFIED, with a *bonus* finding: `narrator_output_only` sits in `AttentionZone.Primacy` but is NOT in `STABLE_SECTION_NAMES` (`prompt_framework/bucket.py:28-108`), so it defaults to `SectionBucket.User` and rides the uncached per-turn message despite being byte-identical. A one-line cache-promotion is an immediate quick-win independent of the extraction work (ADR §Companion quick-win / Alternative A).
- **(Improvement, non-blocking)** The 13 sidecar fields partition cleanly: 1 pre-narration (`action_rewrite`, player-input-derived), 11 post-narration (prose-readout — the server *already* reconstructs most via catch-loops `_detect_missed_recurring_npcs`/`_auto_mint_prose_only_npcs`/`unmatched_*`), 1 generation-entangled (`private_segments` / ADR-105 firewall — stays inline). The design extends the live ADR-113 lineage (IntentRouter pre-pass + dispatch_engagement_watcher) — near-zero new infra.
- **(Improvement, non-blocking)** `npcs_present.side`/membership is better owned by the engine the IntentRouter already engaged than extracted from prose — removes a class of "wrong side breaks momentum routing" bug. Folded into the ADR.
- **(Question, non-blocking → for Keith)** Two genuine forks surfaced in §Decision are recorded as the ADR's reasoned position, open to pushback: (a) `private_segments` stays narrator-inline vs. pre-pass directive; (b) sync-pre-broadcast vs. async for the post-extractor's cosmetic fields. ADR takes a position on both; Keith is a decider.
- **(Improvement, non-blocking)** Scope held to the *sidecar* (game_patch). A subset of tool-owned categories (descriptive `apply_world_patch` location/atmosphere, `tick_tropes` day-advance) are *also* extraction candidates but deferred to a flagged Phase 2 to keep this ADR from re-opening the ADR-113/114 tool partition.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Architect (design)

- **Workflow tag corrected at setup: `tdd` → `architecture`.** The story arrived tagged `workflow: tdd`, which has no Architect/design phase (it routes TEA to write failing tests). For a DESIGN-ONLY ADR (story explicitly says "Architect, no code"), `tdd` is a category error. Convention precedent: both prior DESIGN+ADR stories (117-2 "Design + ADR: quest-seed authoring contract", 75-3 "[DESIGN] Universal RAG retrieval layer (ADR)") used the `architecture` workflow. Corrected via `pf sprint story update 126-12 --workflow architecture` (SM, at setup). No code/spec impact.
