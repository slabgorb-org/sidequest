# Story 93-1: Haiku Archetype Inference Unblocks All-Freeform Chargen

## Overview

Resolve the all-freeform chargen hard-block with a Haiku one-shot archetype inference. When the archetype gate would BLOCK with `missing_axes_with_pack_axes` — i.e., the pack declares `base_archetypes`/`archetype_constraints` but the accumulated `jungian_hint`/`rpg_role_hint` pair is incomplete — AND the player supplied freeform answers, run a single Haiku call over the accumulated freeform text to infer the missing axis value(s), constrained to the pack's valid enums.

## Problem

The all-freeform chargen pathway accumulates ZERO archetype hints because `builder.apply_freeform()` records the text but sets neither `jungian_hint` nor `rpg_role_hint`. Axis-bearing packs (heavy_metal, elemental_harmony) dead-end at confirm with:

```
archetype resolution failed (missing_axes_with_pack_axes)
```

This blocks narrative-first players (Alex/James) who want to describe chargen in their own words without being forced into preset selections. The fail-loud gate is correct; freeform just offers no path to resolution.

## Solution

Intercept at the gate before failing loud. If the player supplied freeform answers, infer the missing axis values via a targeted Haiku call:

1. **Inference trigger:** Gate detects `missing_axes_with_pack_axes` AND freeform answers exist
2. **Prompt:** Haiku receives accumulated freeform text + the pack's valid jungian/rpg_role enums
3. **Output:** Inferred axis value(s) constrained to pack enum
4. **Fill strategy:** Only fill missing axes; never override a hint that a preset already set
5. **Fail-safe:** Still fail loud (keep existing block) when:
   - There is no freeform text to infer from
   - Haiku returns out-of-enum value (no coercion, no pack-default fallback)
6. **Observability:** Emit `chargen.archetype_inferred` OTEL span with attrs: `inferred_axes`, `jungian_hint`, `rpg_role_hint`, `source='freeform'`

## Technical Approach

### Location: chargen_mixin.py Gate (~495-540)

The current gate path:

```python
# chargen_mixin.py ~495-540 (archetype resolution)
if not all_axes_present:
    if any axis missing:
        raise ChargenError("archetype resolution failed (missing_axes_with_pack_axes)")
```

Change to:

```python
if not all_axes_present:
    if any_axis_missing and has_freeform_text:
        # NEW: Try inference
        inferred = infer_archetype_from_freeform(
            freeform_text=accumulated_freeform,
            pack_constraints=pack.archetype_constraints,
            existing_hints={jungian_hint, rpg_role_hint}  # Don't override these
        )
        # inferred is {jungian_hint?, rpg_role_hint?} or None on failure
        if inferred is not None:
            if inferred.get('jungian_hint'):
                jungian_hint = inferred['jungian_hint']
            if inferred.get('rpg_role_hint'):
                rpg_role_hint = inferred['rpg_role_hint']
            # Emit span for observability
            emit_chargen_archetype_inferred(inferred)
        else:
            # Out-of-enum or inference error
            raise ChargenError("archetype resolution failed (inference_invalid)")
    elif not any_axis_missing:
        # All axes present (normal path)
        pass
    else:
        # No freeform to infer from
        raise ChargenError("archetype resolution failed (missing_axes_with_pack_axes)")
```

### Inference Implementation: Intent-Router Pattern

Create a new inference function in `agents/llm_factory.py` following ADR-067 (Unified Narrator Agent) and ADR-113 (Intent Router) patterns:

```python
def infer_archetype_from_freeform(
    freeform_text: str,
    pack_constraints: ArchetypeConstraints,
    existing_hints: dict[str, str | None]
) -> dict[str, str] | None:
    """
    Infer missing archetype axis(es) from player's freeform chargen answers.
    
    Args:
        freeform_text: Accumulated freeform answers from chargen
        pack_constraints: Pack's base_archetypes or archetype_constraints
        existing_hints: {jungian_hint?, rpg_role_hint?} already set (don't override)
    
    Returns:
        {jungian_hint?, rpg_role_hint?} with only missing axes filled, or None on failure.
        None means: Haiku returned out-of-enum value, or freeform was empty.
    
    Raises:
        ChargenError if Haiku call fails (cost ceiling, etc.)
    """
    # Determine which axes are missing
    missing_axes = []
    if existing_hints.get('jungian_hint') is None and pack_constraints.jungian_axis:
        missing_axes.append(('jungian_hint', pack_constraints.jungian_axis.enum))
    if existing_hints.get('rpg_role_hint') is None and pack_constraints.rpg_role_axis:
        missing_axes.append(('rpg_role_hint', pack_constraints.rpg_role_axis.enum))
    
    if not missing_axes:
        return {}  # Nothing to infer
    
    # Build Haiku prompt
    missing_axis_names = [ax_name for ax_name, _ in missing_axes]
    prompt = f"""Given the player's chargen answers (their own words), infer the missing archetype axis(es): {missing_axis_names}.

Chargen answers:
{freeform_text}

Constrained values:
- jungian_hint: {pack_constraints.jungian_axis.enum if 'jungian_hint' in missing_axis_names else 'ALREADY SET'}
- rpg_role_hint: {pack_constraints.rpg_role_axis.enum if 'rpg_role_hint' in missing_axis_names else 'ALREADY SET'}

Infer ONLY the missing axes. Return as JSON:
{{"jungian_hint": "value" | null, "rpg_role_hint": "value" | null}}
Use null for axes you don't infer or that are already set.
All values MUST be from the constrained enum above. No coercion, no defaults."""

    # Call Haiku via intent-router pattern
    try:
        result = call_haiku_inference(prompt)  # Uses emit_tool, respects cost ledger
        parsed = parse_json_output(result)
        
        # Validate output
        inferred = {}
        for ax_name, valid_enum in missing_axes:
            value = parsed.get(ax_name)
            if value is not None:
                if value not in valid_enum:
                    return None  # Out-of-enum, fail loud
                inferred[ax_name] = value
        
        return inferred
    except Exception as e:
        raise ChargenError(f"archetype inference failed: {e}")
```

### OTEL Observability

In the chargen_mixin gate, after successful inference:

```python
from sidequest.telemetry.spans import emit_chargen_archetype_inferred

emit_chargen_archetype_inferred(
    inferred_axes=['jungian_hint', 'rpg_role_hint'],  # Which axes were inferred
    jungian_hint=jungian_hint,  # Final value
    rpg_role_hint=rpg_role_hint,  # Final value
    source='freeform'  # Always 'freeform' for 93-1
)
```

Span attributes visible on GM panel so operator can verify inference fired vs. preset-set values.

## Acceptance Criteria

1. **Heavy_metal/barsoom all-freeform chargen succeeds:**
   - Heavy_metal pack has base_archetypes(jungian + rpg_role axes)
   - Barsoom world has chargen scenes (origins, crucible, obligation, the_road)
   - Player answers all scenes via freeform (no preset picks)
   - `Create Character` succeeds; archetype resolution does NOT fail with `missing_axes_with_pack_axes`

2. **Inferred hints are pack-valid enum values:**
   - Both `jungian_hint` and `rpg_role_hint` are members of pack's declared enum
   - Out-of-enum Haiku output is rejected (NOT coerced or packed-default fallback)
   - Error message is clear: "archetype inference failed (invalid_enum_value)"

3. **Partial preset + freeform inference:**
   - Preset path sets one axis (e.g., jungian_hint='Innocent')
   - Freeform chargen must supply the other (rpg_role_hint)
   - Inference fills ONLY the missing rpg_role_hint
   - Preset-set jungian_hint is never touched/overridden

4. **No freeform fallback:**
   - Preset-only chargen (no freeform answers) that still lacks axes: still fails loud
   - Error: "archetype resolution failed (missing_axes_with_pack_axes)"
   - No pack-default archetype invented, no silent fallback

5. **OTEL span on every inference:**
   - `chargen.archetype_inferred` span fires with attrs:
     - `inferred_axes`: ["jungian_hint"] or ["rpg_role_hint"] or both
     - `jungian_hint`: final value (or omitted if not inferred)
     - `rpg_role_hint`: final value (or omitted if not inferred)
     - `source`: "freeform" (for this story)
   - Visible on GM panel (proves inference fired vs. preset-only accumulation)

6. **Wiring test (integration, not unit):**
   - Test drives full chargen build end-to-end with heavy_metal/barsoom all-freeform
   - Asserts Create Character succeeds
   - Asserts span was emitted (not mocked, real OTEL context)
   - Asserts archetype matches inferred values
   - Verifies inference is reachable from production flow (not stubbed)

7. **Cost accounting:**
   - Haiku call accounts to session cost ledger (ADR-134)
   - Respects hard ceiling; inference does not cause unmetered cost spike
   - Test verifies cost delta on the session

## Implementation Notes

- **No Silent Fallbacks (CLAUDE.md principle):** If Haiku returns out-of-enum, fail loud with clear error. Never coerce or invent a pack default.
- **Verify Wiring (CLAUDE.md principle):** Wiring test must prove the inference path is reachable from production chargen flow (not isolated unit test). This catches stubbed/mocked gates.
- **Cost Transparency (ADR-134):** Haiku call rides the session ledger. Cheap, targeted (single per chargen), does not bypass the session ceiling.

## References

- **Problem:** [BAR-1] pingpong playtest — all-freeform chargen hard-blocks at confirm
- **Builder:** `sidequest-server/sidequest/game/builder.py` (~1418: accumulation site; ~1790: apply_freeform)
- **Gate:** `chargen_mixin.py` (~495-540: archetype resolution gate)
- **ADR-067:** Unified Narrator Agent (single narrator, structured output)
- **ADR-113:** Intent Router — Mechanical-Engagement Spine (classification + dispatch)
- **ADR-134:** Per-Session API Cost Runaway Detector and Hard-Kill Ceiling
