# Epic 93: Chargen Freeform Resolution & Character History Surface

## Problem Statement

All-freeform chargen hard-blocks at the archetype gate, and the player's chargen answers are orphaned. Two coupled problems found in the heavy_metal/barsoom playtest ([BAR-1] pingpong).

**PROBLEM 1 (hard-block):** A player who answers hint-bearing chargen scenes via the 'describe it in your own words' box accumulates ZERO archetype hints (builder.apply_freeform records the text but sets no jungian_hint/rpg_role_hint), so axis-bearing packs (heavy_metal, elemental_harmony) dead-end at confirm with 'archetype resolution failed (missing_axes_with_pack_axes)' (chargen_mixin gate ~495-540). The fail-loud gate is correct; freeform just offers no path to an archetype.

**PROBLEM 2 (orphaned data):** Freeform text is consumed only for the {class} prose slot then discarded; selections survive only as a few flavor labels (origin_label/calling_label/background/drive). The player's actual answers — their words and their picks — never reach the Character, snapshot, or sheet.

## Decisions (operator, 2026-06-06)

**(A) Resolve the block with Haiku inference:** One-shot inference of missing jungian_hint/rpg_role_hint from accumulated freeform text, constrained to pack's valid axis values, following intent-router emit_tool pattern. Emit chargen.archetype_inferred OTEL span (lie detector — GM panel must show inference fired vs preset accumulation). Still fail loud when there is nothing to infer from.

**(B) Durable creation_answers provenance:** Add creation_answers record to Character (per scene: prompt, kind=choice|freeform, the player's words or chosen label) and carry it in snapshot.

**(C) Character-sheet History section:** Render new 'History' section on character sheet, starting with origin block (chargen answers + inferred-archetype badge), designed as future home for player-linked lore.

**(D) Lore-store plumbing:** Wire History section to existing lore store (ADR-048 / story 75-15 creation-seed fragments) so player-linked lore surfaces.

## Audience

- **Narrative-first players (Alex/James):** Keeps freeform escape hatch viable instead of dead-ending
- **Mechanics-first players (Sebastien/Jade):** Makes chargen provenance legible in player UI, allows introspection of inferred mechanics

## Technical Approach

### Story 93-1: Haiku Archetype Inference

When archetype gate would BLOCK with missing_axes_with_pack_axes AND player supplied freeform answers:
- Run single Haiku call over accumulated freeform text
- Infer missing axis value(s), constrained to pack's valid enums
- Fill ONLY missing axis (don't override preset-set hints)
- Fail loud (keep existing block) when no freeform to infer from or out-of-enum result

Implementation: intent-router emit_tool pattern in agents/llm_factory.py, gates at chargen_mixin.py ~495-540.

Acceptance Criteria:
- Heavy_metal/barsoom all-freeform chargen succeeds (no missing_axes_with_pack_axes block)
- Inferred hints are pack-valid enum values (no coercion, reject out-of-enum)
- Partial preset + freeform: inference fills only missing axis, leaves preset untouched
- No freeform to infer from: keep fail-loud behavior (no pack-default fallback)
- chargen.archetype_inferred OTEL span on every inference (lie detector)
- Wiring test: inference reachable from production chargen flow

### Story 93-2: creation_answers Provenance Model

Add creation_answers field to Character: ordered list of {scene_id, prompt, kind, value, archetype_inferred?}. Populate from builder._results (ChoiceInput.choice_label / FreeformInput.text already captured). Expose in snapshot so UI can read it.

### Story 93-3: Character-Sheet History Section

Render 'History' section on CharacterSheet with origin block: prompt + player's answer per scene. Freeform shows verbatim words, preset shows chosen label. Scenes with inferred archetype get badge. Structured as future home for lore (93-4) but only origin block now.

### Story 93-4: History Lore-Link Plumbing

Wire History section to ADR-048 lore store. Story 75-15 already persists creation-seed fragments; surface character-/player-linked fragments in History beneath origin block. No new authoring, no silent fallbacks (log/skip loudly if fragment unresolvable).

## Related Stories

- 93-1: Haiku archetype inference (5pt, TDD, this story)
- 93-2: creation_answers provenance (5pt, TDD)
- 93-3: History section origin block (3pt, TDD)
- 93-4: History lore-link plumbing (5pt, TDD, depends 93-3)

## References

- [BAR-1] pingpong playtest session: all-freeform chargen hard-blocks at confirm
- builder.apply_freeform (game/builder.py ~1790)
- accumulation site (builder.py ~1418)
- archetype gate (chargen_mixin.py ~495-540)
- ADR-048: Lore RAG Store
- ADR-067: Unified Narrator Agent
- ADR-113: Intent Router — Mechanical-Engagement Spine
- ADR-134: Per-Session API Cost Runaway Detector
