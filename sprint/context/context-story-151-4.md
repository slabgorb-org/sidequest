---
parent: context-epic-151.md
workflow: tdd
---

# Story 151-4: Sidecar cutover I — transactional fields

## Business Context

The first real cutover: move the **transactional** sidecar fields off `game_patch`
to the post-narration extractor (151-2). These are `items_gained`, `items_lost`,
`items_discarded`, `items_consumed`, `gold_change`, `companions_added`,
`companions_dismissed` — discrete inventory/roster/purse mutations the prose already
states. The server already reconstructs most via catch-loops; this promotes that to
the primary, instrumented path while keeping the catch-loops as the loud net.

## Technical Guardrails

- **Source:** the 151-2 extractor produces these fields from prose. This story wires
  the `narration_apply` consumers to read the **extractor output** instead of the
  `game_patch` sidecar:
  - items: `narration_apply.py:4683-4970` (gained/lost/discarded/consumed lanes)
  - gold: `narration_apply.py:5004-5070`
  - companions: `narration_apply.py:6535-6695`
- **Atomic per field-group:** retire each group's `output_only.md` PART 2 emission in
  the same change that lights the extractor for it; lie-detector watching.
- **Keep the catch-loops** (`unmatched_*` item watchers, companion dedup watchers) as
  the loud safety net — do not delete them.
- **Preserve attribution:** `recipient` on items, `recruited_by` on companions;
  split multi-recipient hand-offs into one entry per recipient.

## Scope Boundaries

**In scope:**
- Cutover of items×4, `gold_change`, companions×2 to the extractor + retirement guards
  + catch-loop retention.

**Out of scope:**
- `npcs_present`, cosmetic fields (151-5); `output_only.md` final shrink (151-6);
  `action_rewrite` (151-3).

## AC Context

For each field-group (items, gold, companions):
1. **Extracted:** the 151-2 extractor produces the field from synthetic prose.
2. **Applied from extractor:** `narration_apply` applies the mutation from the
   extractor output, not the `game_patch` sidecar.
3. **Retired:** the sidecar emission is removed from `output_only.md`; a retirement
   guard asserts `narration_apply` no longer reads it from `game_patch`.
4. **Loud net intact:** an unmatched item / duplicate companion still fires its
   existing watcher span.
5. **Attribution preserved:** recipient / recruited_by routing is correct, incl.
   multi-recipient splits.
6. Full suite (with content) green.

## Assumptions

- **Depends on 151-2 merged** (extractor skeleton live in shadow). If 151-2 is not
  merged, this story is blocked — log and notify SM.
- Catch-loops remain as the net throughout (not removed by this story).
