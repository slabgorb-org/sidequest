---
story_id: "67-2"
jira_key: "67-2"
epic: "epic-67"
workflow: "tdd"
---
# Story 67-2: ACTION_REVEAL delivery resilience — retry/backfill on reconnect so a sealed peer never stalls at Composing

## Story Details
- **ID:** 67-2
- **Jira Key:** 67-2
- **Workflow:** tdd
- **Type:** bug
- **Points:** 3
- **Priority:** p2
- **Stack Parent:** none

## Story Context
This story is part of **Epic 67: Multiplayer resilience & presence** (Playtest-3 findings).

Full context available at: `sprint/context/context-story-67-2.md`

**Root Problem:** When a peer seals (submits their action), the table needs to see "Adam Sealed" immediately. Currently, if the `ACTION_REVEAL{submitted}` or `TURN_STATUS{submitted}` broadcast races a transient socket disconnect, the peer can be permanently stranded at "Adam Composing…" until resolution (or forever if everyone else has sealed).

**Business Impact:** This erodes trust in the turn barrier and invites confused re-submits.

**Recommended Fix (Architect):**
1. Server: on (re)connect, re-derive and send the current `build_turn_status_roster` so seal state is always reconciled
2. Server: replace the silent `ws.send_failed` drop with loud OTEL watcher events
3. UI: verify the existing `TURN_STATUS` merge in `mergePeerRevealsWithSubmittedStatus` surfaces recovered seal state (likely already wired)

**Scope:** See story context for in-scope vs. out-of-scope details. Key constraints: perception firewall (ADR-104/105), no silent fallbacks, OTEL proof required, every test must be a wiring test.

## Workflow Tracking
**Workflow:** tdd
**Phase:** setup
**Phase Started:** 2026-05-27T20:06:50Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-27T20:06:50Z | - | - |

## Repositories & Branches
- **sidequest-server** (api): `feat/67-2-action-reveal-delivery-resilience`
- **sidequest-ui** (ui): `feat/67-2-action-reveal-delivery-resilience`

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

No upstream findings

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

No design deviations
