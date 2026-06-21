# Story Context: 153-4 — SWN Narrative Chargen: Flat Stats & Missing Skills/Foci

## Story Metadata
- **Story ID:** 153-4
- **Epic:** 153 (Playtest follow-ups — open findings)
- **Type:** Bug
- **Points:** 5
- **Workflow:** TDD
- **Repositories:** sidequest-server
- **Priority:** P2

## Problem Statement

SWN (Stars Without Number) narrative character generation is producing **flat, non-differentiated attribute stats** and is **not assigning skills and foci** according to the WN SRD chargen specification. This finding came from the 2026-06-20/21 full-stack playtest sweep across the space_opera genre pack worlds (aureate_span, coyote_star, perseus_cloud).

## Root Cause Direction

The scope from the story title points to:
1. **Missing WN 14-to-7 attribute spread** — narrative chargen must apply the Without Number attribute array/point-spread logic (the shaped-attribute retune from ADR-142) instead of falling back to flat/default generation
2. **Skills and foci not assigned** — the SWN narrative chargen path is not invoking the ruleset's `contribute_background_skills()` and `contribute_foci()` methods during character assembly

## Acceptance Criteria

1. **SWN narrative chargen applies WN 14-to-7 attribute spread:**
   - Chargen produces a differentiated attribute array rather than flat stats
   - The attribute assignment respects the prime requisite (Calling's highest ability score)
   - Generated scores follow the WN distribution (14-point pool mapped to 7 shaped stats)

2. **Skills and foci are assigned during chargen:**
   - Background skills are granted per WWN SRD §1.3 (free_skill + quick_skills at level 0)
   - Focus skills and abilities are granted per WWN SRD §1.5 (first level of each chosen focus)
   - Merged skill sets use higher-of (max) semantics across sources (scene grants ∪ background ∪ foci)

3. **OTEL watcher visibility:**
   - Chargen attribute assignment emits `{ruleset}.chargen.attributes_assigned` span (already live in `without_number.py`)
   - Background skill grants emit `{ruleset}.chargen.background_skills` span (already live)
   - Focus grants emit `{ruleset}.chargen.foci_applied` span (already live)
   - GM panel can verify mechanical decisions fired correctly

4. **Wiring test proves production reachability:**
   - Integration test establishes that the narrative chargen path reaches the ruleset's attribute/skill assignment methods
   - Test confirms skills and foci are present in the final character snapshot after chargen confirmation
   - Test exercises the full chargen flow for an SWN world (not isolated unit tests of ruleset methods)

## Key Code Areas to Investigate

**Character creation entry:**
- `sidequest/handlers/character_creation.py` — CharacterCreationHandler routes chargen phases
- `sidequest/server/websocket_handlers/chargen_mixin.py` — Phase handlers for arrange/story/confirmation

**Attribute/skill generation:**
- `sidequest/game/builder.py` — CharacterBuilder orchestrates chargen scene flow and `build()` finalization
- `sidequest/game/ruleset/without_number.py` — `assign_attributes()`, `contribute_background_skills()`, `contribute_foci()` (WN-specific overrides)
- `sidequest/game/ruleset/base.py` — `generate_attributes()` base method

**SWN ruleset module:**
- `sidequest/game/ruleset/swn.py` — SWN-specific configuration (may be thin or defer to parent)

**Narrative chargen narrative definition:**
- `sidequest-content/genre_packs/space_opera/` — Pack-level chargen scene definitions (if present)

## Technical Notes

- **ADR-142/143:** Without Number ruleset binding; the shaped-attribute retune is the "14-to-7 attribute spread" mentioned in the story title
- **ADR-117:** Pluggable RulesetModule seam — SWN uses the WithoutNumberRulesetModule base
- **OTEL principle:** Every mechanical subsystem decision must emit watcher spans for GM-panel visibility (CLAUDE.md)
- **Wiring tests:** Must reach production code paths, not just unit-test isolates (CLAUDE.md "No Source-Text Wiring Tests")

## Story Scope

This story addresses the narrative chargen path for SWN only. It does NOT address:
- Other rulesets (Fate, WWN, CWN, AWN) unless their narrative chargen also exhibits the same gap
- The non-narrative "arrange" chargen path (which may already be working correctly)
- Content authoring or pack-level chargen scene definitions (those are separate tasks if needed)

---

## Development Notes

Start with a light research pass to:
1. Locate where SWN narrative chargen is invoked in the builder/handler flow
2. Identify which ruleset methods are called (or should be called) during narrative chargen
3. Spot any conditional gates preventing attribute/skill assignment in the narrative path
4. Check whether the existing OTEL spans are being fired correctly or skipped
