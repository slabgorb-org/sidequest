# Story 160-2 Context

## Title
Animal companion portraits — companion_creature entries (cat/owl/raven/toad/goat) across 9 worlds, world-specific appearance prose, rendered via Z-Image and pushed to R2; cliche-judge + sidequest-validate pass

## Metadata
- **Story ID:** 160-2
- **Epic:** 160
- **Points:** 5
- **Priority:** p2
- **Repo:** sidequest-content
- **Workflow:** trivial

## Scope
Add the five companion species (cat, owl, raven, toad, goat) as `companion_creature` entries to each of 9 worlds' `portrait_manifest.yaml` files. Each entry includes world-specific `appearance` prose. Render via the daemon Z-Image pipeline and push to R2. Update each world's `r2_manifest.json`.

**9 worlds × 5 species = 45 portraits total.**

### Target Worlds
- wry_whimsy: oz, wonderland, gulliver
- caverns_and_claudes: beneath_sunden
- elemental_harmony: burning_peace, shattered_accord
- heavy_metal: evropi, long_foundry, barsoom

## Technical Approach

### Portrait Entry Structure
Each world's `portrait_manifest.yaml` gets five new entries following the existing `companion_creature` precedent (Oz's `toto` and `the_cowardly_lion`). Schema:

```yaml
- id: <species>_<world-unique-suffix>  # e.g., cat_oz, owl_oz_variant
  name: <Species in Title Case>
  role: <One-line descriptor matching the world's register>
  type: companion_creature
  appearance: >-
    <camera-style concrete prose, no proper nouns, positive-only,
     follows Z-Image rules>
  culture_aesthetic: >-
    <world-keyed style note>
  element_visual: >-
    No text, no caption, no title, no writing, no signature, no labels,
    no watermark, no border, no frame.
```

### Appearance Prose Rules (from PROMPTING_Z_IMAGE.md)
- **Camera-style concrete prose** — describe physical fact, never impression/expression editorial
- **Positive-only** — no negative prompts; phrase negations as positive constraints ("bareheaded or a plain cap", not "no hat")
- **No proper nouns, dates, quoted phrases**
- **Cleanup clause** — every entry must end with "No text, no caption, no title, no writing, no signature, no labels, no watermark, no border, no frame."
- **Style suffix** — comes from each world's `visual_style.yaml::positive_suffix`, NOT hardcoded in the manifest

### Per-World Visual Styles
Each world pulls its drawing discipline from `visual_style.yaml`:
- **oz (wry_whimsy):** Denslow 1900 plate (bold pen-and-ink, flat color fields, Art Nouveau ornament)
- **wonderland (wry_whimsy):** John Tenniel (pen-and-ink, decorative linework)
- **gulliver (wry_whimsy):** Hand-tinted 18th-century engraving style
- **beneath_sunden (caverns_and_claudes):** Otus/Trampier pen-and-ink (crosshatched black, single fire light, cold scoured stone)
- **burning_peace (elemental_harmony):** Brush-ink / sumi-e influenced (flowing strokes, economy of line, martial grace)
- **shattered_accord (elemental_harmony):** Stained glass aesthetic (bold geometric shapes, saturated jewel tones)
- **evropi (heavy_metal):** Chiaroscuro (theatrical lighting, deep blacks, baroque drama)
- **long_foundry (heavy_metal):** Industrial engraving (technical precision, mechanical detail, pent-up energy)
- **barsoom (heavy_metal):** Pulp-era airbrush (retro-futuristic, bold simplified forms, bold saturated color)

### Rendering & Uploading
1. **Manifest update:** Add all 45 entries to respective `portrait_manifest.yaml` files with appearance prose
2. **Validation:** Run `cliche-judge` + `sidequest-validate` to confirm no text collisions or malformed entries
3. **Daemon render:** Operator-run pass via existing Z-Image pipeline (`scripts/generate_portrait_images.py` or daemon CLI) — **no daemon code changes required**
4. **R2 upload:** `scripts/r2_sync_packs.py` syncs rendered PNGs to R2 CDN
5. **Manifest index update:** `scripts/r2_manifest_from_bucket.py` regenerates `r2_manifest.json` with new asset keys

## Acceptance Criteria
- [ ] All five species have entries in all 9 worlds' `portrait_manifest.yaml` (45 entries total)
- [ ] Each entry follows the `companion_creature` type schema
- [ ] `appearance` prose is camera-style, positive-only, no proper nouns, includes cleanup clause
- [ ] `role` and `appearance` reflect each world's visual register (Denslow storybook ≠ Otus crosshatch)
- [ ] `cliche-judge` passes (no overworn phrases, tropes vetted)
- [ ] `sidequest-validate` passes (no schema violations)
- [ ] All 45 PNGs rendered via Z-Image and uploaded to R2
- [ ] `r2_manifest.json` updated with new asset keys and checksums
- [ ] No changes to daemon code, server code, or UI code

## Relationship to Other Stories
- **160-1 (done):** Persona templates for the five species. This story gives them real `selected_portrait_ref` to use in chargen. Useful, not tightly coupled.
- **160-3 (blocked on 160-2):** Dogfood validation will use these portraits during play.

## Out of Scope
- New run-loop code, server changes, UI changes
- Player-owned in-game familiar entity (deferred per §6 of design spec)
- Daemon modifications

---
_Generated by story setup; augmented with technical approach and acceptance criteria from design spec (docs/superpowers/specs/2026-06-27-animal-companions-design.md)._
