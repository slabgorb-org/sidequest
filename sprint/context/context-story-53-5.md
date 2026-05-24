# Story 53-5: UI surface RigComposure + Edge + injury tags on CharacterSheet

## Objective

Wire the RigComposurePool data (materialized in stories 53-1/53-2) into the React UI's CharacterSheet component so players can see:
1. **RigComposure pool** — the vessel's structural composure (current/max), displayed separately from Edge
2. **Edge pool** — personal composure (already wired via `current_hp`/`max_hp` aliasing)
3. **Injury tags** — damage tags applied when composure→0 crash event fires

The backend has shipped the model, materializer binding, crash handler, and OTEL spans (53-1 through 53-4). This story connects the frontend to display that data from the PARTY_STATUS snapshot.

## Acceptance Criteria

- [ ] **Protocol model** (`sidequest-server/sidequest/protocol/models.py`):
  - Add `rig_composure_current` + `rig_composure_max` fields to `PartyMember` (nullable, defaults to None)
  - Add optional `injury_tags` list field to `PartyMember` (defaults to empty)
  - Update serialization to pull from `character.core.rig_pool` + `character.core.tags` when present

- [ ] **UI types** (`sidequest-ui/src/types/party.ts`):
  - Extend `CharacterSummary` with optional `rig_composure_current`, `rig_composure_max`, `injury_tags`
  - Extend `CharacterSheetData` (in `CharacterSheet.tsx`) with the same fields

- [ ] **CharacterSheet component** (`sidequest-ui/src/components/CharacterSheet.tsx`):
  - Add new "Composure" section below the stats grid
  - Render two resource bars side-by-side:
    - **Edge** — personal composure (existing `hp`/`hp_max`, already wired)
    - **RigComposure** — vessel composure (new `rig_composure_current`/`rig_composure_max`, conditional render if available)
  - If `injury_tags` is present and non-empty, render a subsection listing the tags
  - Section should be styled consistently with the rest of the Folio palette (already imported in CharacterPanel)

- [ ] **CharacterPanel wiring** (`sidequest-ui/src/components/CharacterPanel.tsx`):
  - Pass the new rig pool fields from game state down through props
  - Integrate into the CharacterPanel's resource display logic (if applicable)

- [ ] **Tests** (`sidequest-ui/src/components/__tests__/CharacterSheet.test.tsx`):
  - Unit test: CharacterSheet renders Edge bar when `hp`/`hp_max` are present
  - Unit test: CharacterSheet renders RigComposure bar when `rig_composure_current`/`rig_composure_max` are present
  - Unit test: CharacterSheet renders injury tags when provided
  - Unit test: CharacterSheet renders nothing (or empty state) when rig pool is absent
  - Wiring test: CharacterSheet with rig pool data is imported and reachable from the component tree

- [ ] **Protocol tests** (`sidequest-server/tests/`):
  - Unit test: PartyMember serializes with rig pool fields when character has a rig pool
  - Unit test: PartyMember serializes without rig pool fields (None/empty) when character has no rig pool
  - Integration test: PARTY_STATUS message carries rig pool + injury tags for a Road Warrior character with an equipped rig

## Design Notes

### Resource Display

The Composure section should show two parallel resource bars:
- **Edge** — the character's personal composure pool (durable across vehicle changes, already wired via `hp` aliasing)
- **RigComposure** — the vehicle's structural pool (swaps when the rig changes)

Styling should match the Folio palette from CharacterPanel (FONT_LABEL, FOLIO colors). No magical formulas — render what the server sends.

### Injury Tags

When composure→0 crash event fires (story 53-3), the crash handler tags the character with injury markers (e.g., `broken_leg`, `dazed`). These tags are persisted in `character.core.tags` and should appear in a subsection below the RigComposure bar:

```
Injuries: broken_leg, dazed
```

If no injury tags, the subsection doesn't render.

### Conditional Rendering

- **RigComposure section**: Render only if `rig_composure_current` and `rig_composure_max` are both present and non-null
- **Injury tags subsection**: Render only if `injury_tags` is non-empty
- **Edge bar**: Already wired via `hp`/`hp_max`; no changes needed

### Protocol Integration

The server's PARTY_STATUS handler needs to expose `rig_pool` data. Check `sidequest-server/sidequest/handlers/` for the PARTY_STATUS emit handler, then add extraction logic:

```python
# Pseudo-code
rig_composure_current = character.core.rig_pool.current if character.core.rig_pool else None
rig_composure_max = character.core.rig_pool.max if character.core.rig_pool else None
injury_tags = [tag for tag in character.core.tags if tag.startswith("injury_")]
```

Per CLAUDE.md "No Silent Fallbacks", if the materializer fails to bind a rig pool (e.g., malformed tags), the crash should be visible — the character must either have a complete pool or none at all. A partial rig pool (max but no current) is a data error.

## References

- **Epic 53 context**: `sprint/context/context-epic-53.md`
- **Story 53-1** (RigComposurePool model): `sprint/context/53-1.md`
- **Story 53-2** (Materializer wiring): `sprint/context/context-story-53-2.md`
- **Story 53-3** (Crash handler): provides the injury tags
- **Story 53-4** (OTEL spans): instrumentation for GM panel visibility
- **ADR-014** (Diamonds and Coal): narrative weight / pool semantics
- **ADR-024** (Dual-Track Tension Model): Composure as structural pool
- **ADR-078** (Edge / Composure Combat): two-pool semantics
- **CharacterPanel.tsx**: Folio palette, resource display pattern
- **PARTY_STATUS protocol**: `sidequest-server/sidequest/protocol/messages.py`

## Testing Strategy (TDD)

1. **Red phase (TEA)**: Write failing tests for:
   - RigComposure bar rendering when data is present
   - RigComposure bar NOT rendering when data is absent
   - Injury tags subsection rendering
   - Protocol serialization of rig pool fields
   - PARTY_STATUS emit includes rig pool data

2. **Green phase (DEV)**: Implement:
   - Protocol model updates (PartyMember extensions)
   - UI type extensions (CharacterSheetData, CharacterSummary)
   - CharacterSheet component updates
   - Server-side PARTY_STATUS handler updates
   - Passing tests

3. **Refactor phase (ORCHESTRATOR)**: Extract common patterns, ensure wiring test passes

## Story Weight

- **Points**: 2
- **Estimated duration**: 45–60 minutes (TDD; protocol + UI component + server wiring)
- **Dependencies**: 53-1 (model), 53-2 (materializer), 53-3 (crash handler / tags), 53-4 (OTEL)
- **Blockers**: None (all predecessors shipped)

## Acceptance Definition of Done

- [ ] All tests pass (unit + integration)
- [ ] RigComposure bar renders correctly in a Road Warrior character with an equipped rig
- [ ] Injury tags display when present
- [ ] CharacterSheet gracefully handles missing rig pool (no error, clean render)
- [ ] PARTY_STATUS protocol includes rig pool fields
- [ ] Code review: "This is ready for QA / playtest"
