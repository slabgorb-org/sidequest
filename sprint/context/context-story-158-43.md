# Context: Story 158-43

**Story ID:** 158-43  
**Epic:** 158  
**Title:** Authored quest offer never mints into quest_log — anchor-crossing acceptance for self-directed seeds  
**Type:** Bug  
**Points:** 3  
**Priority:** p2  
**Workflow:** tdd  
**Repository:** sidequest-server  

## Overview

Authored quest offers (self-directed seeds with no giver, like `the_unspent_hold` in beneath_sunden) never mint into the player's quest_log. They sit in `pending_quest_offers` indefinitely. The original ADR-146 pipeline covered only giver-hook offers ("yeah, I'll take the job"); this story closes the gap for giver-less seeds by adding a deterministic anchor-crossing acceptance trigger.

## Problem

- ADR-146 (merged 2026-06-14) built the Intent Router path for offer acceptance: router classifies accept/decline → `mint_quest_offer` mints into quest_log with no narrator call
- The router's prompt is written for GIVER-HOOK offers ("yes to someone")
- Self-directed / giver-less seeds (like `the_unspent_hold`: "acceptance is the descent, not a yes to anyone") are classified as `movement` or other intents, never triggering the quest_offer router path
- Result: player descends the Dropmouth, the engine never recognizes the descent as acceptance, the offer sits in pending_quest_offers forever, and the Quests tab stays blank
- Surfaced in sq-playtest 2026-06-27 (beneath_sunden, Harpo)

## Approved Solution

**Anchor-Crossing Deterministic Backstop:** Amend ADR-146 with a second mint trigger independent of the Intent Router.

When a seated PC TRANSITIONS INTO the seed's `anchor` region:
- The engine calls `mint_quest_offer(source="anchor_crossed", confidence=1.0)`
- No LLM call; purely deterministic state-watch
- The router's verbal-acceptance path is unchanged; first-writer-wins prevents double-mint
- Giver-hook offers that carry an anchor also mint on crossing (any anchor-bearing seed, not just giver-less)

### Key Constraints

1. **Decline respect:** A previously declined/consumed offer is NOT resurrected by anchor-crossing
2. **First-placement exclusion:** Spawning INTO the anchor at turn 0 (no prior region) does NOT mint — the transition must be genuine (from_region truthy)
3. **First-writer-wins:** If router or narrator already minted, anchor path skips (idempotent via existing reconciliation)
4. **Router unchanged:** The verbal-acceptance path (ADR-146 router prompt) is NOT extended — the anchor path is the deterministic fallback for the gap case

### Hook Points

- **quest_offer.py:** New `mint_on_anchor_crossing(snapshot, *, pc_name, from_region, to_region)` function
  - Scans `pending_quest_offers` for a seed with `anchor == to_region`
  - If found, `from_region` is truthy, and offer is not declined/consumed: calls `mint_quest_offer` with `source="anchor_crossed"`
  
- **session.py:** Call in `_apply_world_patch_inner` from the `pc_region` genuine-change block
  - Adjacent to existing `notify_region_transition` call
  - Covers ALL transition paths: movement dispatch, seam descent (deep_descent.py), procedural relocation
  
- **state_patch.py:** Extend `quest_seeded_span` source vocabulary to include `"anchor_crossed"` with `confidence=1.0`
  - OTEL principle: GM panel must distinguish "router classified as yes" (`router_accept`) from "engine watched the crossing" (`anchor_crossed`)

## Acceptance Criteria

1. **Mint on anchor transition:** A seated PC transitioning INTO a seed's `anchor` region mints the authored offer into `quest_log` with no narrator/LLM call; player sees the quest in the Quests tab
2. **OTEL observability:** The `quest.seeded` OTEL span fires with `source="anchor_crossed"`, `confidence=1.0` on the anchor-mint path
3. **No first-placement mint:** Spawning/initial-placement INTO the anchor region at turn 0 (from_region empty) does NOT mint
4. **Decline stays declined:** A previously declined/consumed offer is NOT resurrected by anchor-crossing
5. **First-writer-wins:** If router verbal path or narrator `record_quest` already minted, anchor path does not double-mint
6. **Regression guard:** Existing giver-hook verbal-acceptance router path (ADR-146) still mints as before; no breaking changes

## ADR Work

Draft **ADR-146 Amendment: Anchor-Crossing Acceptance — a Deterministic Second Mint Trigger**

- State that ADR-146 originally covered only giver-hook offers
- Document that this amendment closes the gap for self-directed / giver-less seeds
- This is a feature gap closure, not a redesign of ADR-146

## Related Stories

- **158-42:** Quest tracker: region quest marks completed before objective is met; quest mint/complete emits no OTEL (sibling story, dependency for OTEL observability pattern)
- **ADR-146:** Deterministic Authored-Offer Mint Pipeline (referenced, being amended)

## Testing Strategy

### Unit Tests (quest_offer.py)
- Test `mint_on_anchor_crossing` with a pending offer matching the target anchor
- Test decline reconciliation (offer already declined → no re-mint)
- Test idempotence (offer already minted → first-writer-wins, no double-mint)
- Test first-placement exclusion (from_region="" → no mint)

### Integration Tests (session.py)
- Test PC region transition triggering anchor-crossing mint
- Test all transition paths: movement dispatch, seam descent, procedural relocation
- Test OTEL span emission on anchor-mint path

### Wiring Tests (e2e)
- Test the beneath_sunden `the_unspent_hold` seed: PC descends the Dropmouth → offer mints into quest_log
- Verify quest appears in the Quests tab
- Verify `quest.seeded` span carries `source="anchor_crossed"`, `confidence=1.0`
- Regression: giver-hook offers still mint via router verbal path

## Context References

- **Playtest evidence:** ~/Projects/sq-playtest-pingpong.md (2026-06-27 beneath_sunden session)
- **ADR-146:** Deterministic Authored-Offer Mint Pipeline (currently live, being amended)
- **ADR-146 gap:** Only covers giver-hook offers; self-directed seeds unhandled
- **Game state:** `pending_quest_offers`, `quest_log`, `QuestEntry`, `QuestOffer` models
- **Content:** beneath_sunden's `the_unspent_hold` seed (giver-less, has anchor)
