# Story 126-33: [BUG] Dedup inventory grants

## Story Details
- **ID:** 126-33
- **Epic:** 126 (Fate Core playtest follow-ups)
- **Title:** [BUG] Dedup inventory grants
- **Points:** 2
- **Type:** bug
- **Priority:** p3
- **Workflow:** tdd
- **Repository:** sidequest-server

## Problem Statement

When a character receives an inventory item via state.inventory_update with action='gained', the engine appends the item without checking if the character already holds an identical item (by name or id). This creates duplicate stacks rather than merging or treating the second grant as a no-op.

**Observed manifestation:** In the Oz world (turn 7), 'silver shoes' were granted twice, resulting in `inventory=['silver shoes','silver shoes']`.

**Scope:** Small, server-side fix to the inventory grant apply path.

## Acceptance Criteria

1. **Dedup logic:** `state.inventory_update` with action='gained' checks the existing inventory for a match (by id, then by name). If a match exists, the grant is a no-op (or merges if the item tracks quantities).

2. **OTEL observability:** Emit an OTEL span/event when a dedup occurs so the GM panel can confirm the behavior (lie-detector for the fix).

3. **Unit test:** Test case driving a duplicate inventory_update and asserting no duplicate entry is added.

4. **Wiring test:** Repro the Oz turn-7 scenario (initial grant + re-grant) on a snapshot and verify the dedup fires and the span is present.

5. **No regression:** Non-duplicate grants and other inventory operations remain unchanged.

## Technical Context

- **Inventory model:** `core.inventory` is a list of item entries (check schema for id/name structure and quantity tracking).
- **Apply path location:** Likely in `sidequest/server/dispatch/inventory_lifecycle.py` or `narration_apply.py`.
- **Related:** ADR-014 (Diamonds and Coal), ADR-145 (inventory cataloging), the 126-21/126-25 Fate item-promotion work that depends on stable inventory state.

## Test Plan

1. **Unit test:** `test_inventory_dedup_gained_same_item`
   - Arrange: Create a character with 'silver shoes' in inventory.
   - Act: Apply `state.inventory_update(action='gained', item='silver shoes')`.
   - Assert: Inventory still has one 'silver shoes' entry (not two).

2. **Wiring test:** `test_inventory_dedup_oz_turn7_repro`
   - Load the Oz snapshot (or create a fixture).
   - Apply the initial 'silver shoes' grant.
   - Re-apply the same grant.
   - Assert the inventory has one 'silver shoes' and the dedup OTEL span fired.

## Branch Strategy

- **Repository:** sidequest-server (gitflow)
- **Base branch:** develop
- **Feature branch:** feat/126-33-dedup-inventory-grants

## Files to Review

- `sidequest/server/dispatch/inventory_lifecycle.py` (or inline location in narration_apply.py)
- `sidequest/game/character.py` (if inventory model needs changes)
- `tests/server/dispatch/test_inventory_*.py` (or equivalent)
- Possibly `sidequest/telemetry/` (for OTEL span definitions)

## Key Invariants

- **Idempotency:** A grant of an item the character already holds must be safe to replay (RESUME-safe, ADR-128).
- **No silent fallbacks:** If a dedup occurs, it must be observable via OTEL or logs (CLAUDE.md principle).
- **Preserve semantics:** If items track quantity, merge the quantities; do not silently drop the second grant.
