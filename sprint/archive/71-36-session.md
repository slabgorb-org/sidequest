---
story_id: "71-36"
jira_key: null
epic: null
workflow: "trivial"
---
# Story 71-36: Machine-guard the peer-reveal accumulator invariant — source-text wiring test that snapshot captures raw peerReveals.reveals, never mergedPeerReveals (71-12 follow-up)

## Story Details
- **ID:** 71-36
- **Jira Key:** (none — Jira not configured for this project)
- **Workflow:** trivial
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** implement
**Phase Started:** 2026-06-04T19:41:00Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-04T19:41:00Z | - | - |
| implement | 2026-06-04T19:41:00Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

No upstream findings

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

No deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `src/__tests__/turn-status-derivation-wiring.test.ts` - Added source-text wiring test machine-guarding the peer-reveal accumulator-direction invariant (capture must read raw `peerReveals.reveals`, never `mergedPeerReveals`).

**Tests:** 5/5 passing (GREEN) — 4 existing + 1 new
**Branch:** feat/71-36-peer-reveal-accumulator-guard (not pushed — SM handles git)

**Verification:**
- Confirmed App.tsx:1396 source matches: `persistedPeerActions.capture(currentRound, peerReveals.reveals)` — regex matches reality.
- Positive assertion PASSES against current correct App.tsx.
- Negative assertion (`not.toMatch(/persistedPeerActions\.capture\([^)]*mergedPeerReveals/)`) would FAIL if someone flipped the snapshot arg to `mergedPeerReveals`, catching the stale-draft regression.
- eslint clean (exit 0).

**Handoff:** To review
