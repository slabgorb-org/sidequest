---
story_id: "59-15"
jira_key: ""
epic: ""
workflow: "trivial"
---
# Story 59-15: Engagement e2e validation — beneath_sunden + road_warrior: confrontation/movement/magic actually fire mechanically (OTEL span proof)

## Story Details
- **ID:** 59-15
- **Jira Key:** (none)
- **Workflow:** trivial
- **Stack Parent:** none
- **Points:** 2
- **Type:** chore

## Overview

This story validates end-to-end that the engagement pipeline (confrontation, movement, magic) actually fires mechanically in two worlds:
- **beneath_sunden** (caverns_and_claudes genre)
- **road_warrior** (road_warrior genre)

The validation is **proof by OTEL spans**, not narrative conviction. Claude is excellent at improvising convincing narration with zero mechanical backing. Only the GM dashboard (via OTEL watcher events) proves the subsystems are actually engaged.

## Technical Approach

### Acceptance Criteria

1. **Confrontation Firing:** Initiate a combat encounter in beneath_sunden. Verify:
   - OTEL spans emitted for confrontation initialization
   - Participant roster correctly populated (player + opponent)
   - Resolution mechanics (dice, ability checks) emit OTEL events
   - No confrontation → narration fallback (Claude improvising without mechanical backing)

2. **Movement Firing:** Execute movement commands in road_warrior. Verify:
   - OTEL spans for location transitions
   - State transitions (entering/exiting zones) emit watcher events
   - No silent fallback to narrative-only movement

3. **Magic Firing:** Cast a spell in both worlds (if available). Verify:
   - OTEL spans for spell resolution
   - Effect application emits mechanical telemetry
   - No magic → narration-only fallback

### Testing Strategy

1. Run playtest scenarios against beneath_sunden and road_warrior with `--otel-verbose` enabled
2. Tail the OTEL dashboard (`just otel`) to verify span emission in real-time
3. Check that each interaction emits expected span types (e.g., `confrontation.init`, `movement.transition`, `spell.cast`)
4. Log findings in the **Delivery Findings** section below

## Workflow Tracking
**Workflow:** trivial
**Phase:** setup
**Phase Started:** 2026-06-03T15:43:32Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-03T15:43:32Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->
