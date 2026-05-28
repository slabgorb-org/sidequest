# Story 63-11: Reference — suppress or author empty Beat-Vocabulary + Achievements sections

## TEA-Verified Premise

Develop HEAD: 9b2507e1

**DECISION: Suppress empty sections server-side (NOT author content)**

### Census
- Beat-Vocabulary: empty in 8/10 live packs
- Achievements: empty in 9/10 live packs
- Only heavy_metal + road_warrior have real Beat-Vocabulary
- Only tea_and_murder has real Achievements
- **These three must still render (regression guard)**

Authoring empty sections content-side is a content mountain and not the intent of this story.

## Implementation Seams

Both seams in `reference_renderer.py` must be fixed:

### Seam 1: `_wrap_sections_by_toc`
- **Current:** Emits an empty `<section>` for every DEFAULT_RULES_TOC entry even when the body is empty (deliberate, documented at reference_theme.py:357)
- **Fix:** When a section's rendered body is empty, drop BOTH the `<section>` AND its TOC entry

### Seam 2: `_render_file` with empty presenters
- **Current:** Presenter returning `""` (empty string) falls through to the generic walk, which renders `<p><em>(empty)</em></p>` for present-but-empty data
  - Examples: `achievements: []` or `beat_vocab` with only the KEEPER-skipped obstacles key
- **Fix:** When a presenter returns `""`, suppress it entirely — don't fall through to a placeholder

**Relevant presenters:**
- `present_beat_vocabulary` (reference_presenters.py:1130) — skips obstacles/KEEPER
- `present_achievements` (reference_presenters.py:994)

## Implementation Requirements

The implement phase MUST include guard tests covering:

1. **Empty sections and TOC entries are suppressed** for representative packs
   - Absent-file case (no beat_vocab or achievements key)
   - Present-but-empty case (beat_vocab: {} or achievements: [])

2. **Three NON-empty sections still render with their TOC entries**
   - heavy_metal: Beat-Vocabulary
   - road_warrior: Beat-Vocabulary
   - tea_and_murder: Achievements

**Note:** No new OTEL span required (deterministic page assembly, cosmetic-scope exempt — consistent with 63-10).

## Scope Note

Re-scoped from server,content to **server-only**. TEA confirmed:
- Content side is a no-op (deleting achievements:[] files wouldn't fix the empty-section render)
- Absent files still trigger empty TOC sections
- The fix is entirely server-side suppression
- No content branch created
