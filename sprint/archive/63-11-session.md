---
story_id: "63-11"
epic: "63"
workflow: trivial
---
# Story 63-11: Reference — suppress or author empty Beat-Vocabulary + Achievements sections (cross-pack)

## Story Details
- **ID:** 63-11
- **Epic:** 63
- **Workflow:** trivial (phased → setup → implement → review → finish)
- **Points:** 1
- **Priority:** p3
- **Type:** bug
- **Repos:** server
- **Branch:** feat/63-11-suppress-empty-reference-sections
- **Assignee:** slabgorb

## Workflow Tracking
**Workflow:** trivial
**Phase:** setup
**Phase Started:** 2026-05-27

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-27 | - | - |

## Story Context

See `sprint/context/context-story-63-11.md` for TEA-verified premise, decision, and implementation seams.

### Decision
Suppress empty sections server-side (NOT author content).

### Census
- Beat-Vocabulary empty in 8/10 live packs; only heavy_metal + road_warrior have real content
- Achievements empty in 9/10 live packs; only tea_and_murder has real content
- **These three must still render (regression guard)**

### Seams to Fix
Both in `reference_renderer.py`:
1. `_wrap_sections_by_toc` — drop empty `<section>` AND TOC entry
2. `_render_file` with empty presenters — presenter returning "" must suppress, not fall through to placeholder

### Implementation Requirements
Guard tests must cover:
- Empty sections/TOC are suppressed (absent-file + present-but-empty cases)
- Three NON-empty sections still render (heavy_metal beat-vocab, road_warrior beat-vocab, tea_and_murder achievements)
- No new OTEL span (cosmetic-scope exempt, consistent with 63-10)

### Scope Note
Re-scoped from server,content → **server-only**. Content side is a no-op; the fix is entirely server-side suppression. No content branch created.

## Delivery Findings

### Dev (implementation)
- **Gap** (non-blocking): The dispatch's seam-2 instruction ("a presenter returning `''` must SUPPRESS the section") would have REGRESSED heavy_metal + road_warrior Beat-Vocabulary. Their `beat_vocabulary.yaml` carries player-facing `event_flavor` / `decision_framings` / `chase_modes` keys whose shape `present_beat_vocabulary` does not render, so it returns `""` — and pre-63-11 that content rendered via the generic-walk fall-through. Suppressing on presenter-`""` blackholed it. Corrected to a **body-empty** check (suppress only when the rendered body is `""` / `(empty)` / `(empty file)`), keeping the fall-through. The mandated regression guard caught the first (wrong) attempt. Affects `reference_renderer._render_file`. *Found by Dev during implementation.*

## Design Deviations

- Re-scoped YAML repos field from `server,content` to `server-only`. TEA confirmed content side is a no-op (absent files still trigger empty TOC sections — fix is entirely server-side suppression). No content branch created.

### Dev (implementation)
- **Seam-2 corrected from presenter-empty to body-empty suppression.**
  - Spec source: .session/63-11-session.md "Seams to Fix" #2 / dispatch — "presenter returning '' must suppress, not fall through to placeholder"
  - Spec text: "a presenter returning \"\" must SUPPRESS the section, not fall through to a placeholder"
  - Implementation: kept the generic-walk fall-through; suppress only when the resulting BODY is empty (`""` / `<p><em>(empty)</em></p>` / `<p><em>(empty file)</em></p>`) via new `_body_has_content`.
  - Rationale: present_beat_vocabulary returns "" for the wider heavy_metal/road_warrior shape (event_flavor/decision_framings/chase_modes); literal suppress-on-"" blackholed real content the fall-through renders. Body-empty check suppresses the genuinely-empty packs while preserving real content. Regression guard caught the first attempt.
  - Severity: minor
  - Forward impact: none — behavior matches the story intent (suppress empty, never blackhole content); team-lead ratified.
- **63-7 test fixture seeded with magic/achievements content to preserve DEFAULT_RULES_TOC-coverage intent under 63-11 empty-section suppression.**
  - Spec source: cross-story regression from 63-11 behavior change (Group-A-style, team-lead-approved Option A)
  - Spec text: test_unknown_pack_falls_back_to_default_toc_and_fires_error_span asserted #bearing/#edge/#affinities/#achievements all render
  - Implementation: seeded magic.yaml + achievements.yaml locally in that one test so #affinities + #achievements carry content and still render; assertions unchanged; shared `_seed_pack` untouched.
  - Rationale: 63-11 drops empty sections + TOC links; the test's `_seed_pack` omits magic/achievements. Seeding content preserves (and strengthens) the default-TOC-coverage intent rather than masking suppression.
  - Severity: minor
  - Forward impact: none — intent-preserving fixture cleanup.

## Reviewer Deviation Audit

- **server-only re-scope:** ACCEPTED. Verified the fix is entirely server-side; absent/empty content files still triggered hollow sections pre-fix, now suppressed in the renderer. No content edit needed.
- **Seam-2 corrected to body-empty suppression:** ACCEPTED — and this is the load-bearing call. Verified empirically: `present_beat_vocabulary` returns `""` for heavy_metal/road_warrior's `event_flavor`/`decision_framings`/`chase_modes` shape, but the generic-walk fall-through renders it. The body-empty check (`_body_has_content`) preserves that content while suppressing genuinely-empty packs. The original dispatch instruction (suppress-on-presenter-`""`) would have blackholed real player-facing content; Dev was right to deviate, and the regression guard caught the wrong first attempt. This is the correct, non-blackholing design.
- **63-7 fixture seeding:** ACCEPTED. The unknown-pack default-TOC test now seeds real magic/achievements content locally (shared `_seed_pack` untouched) so all four `DEFAULT_RULES_TOC` sections legitimately render — intent-preserving and strengthening, not coverage-masking.

## Reviewer Assessment

**Verdict:** APPROVED

Clean, correct, well-tested presentation fix. I verified the correctness trap and all four scrutiny points empirically against live content (ran the guard suite with `SIDEQUEST_GENRE_PACKS` set so the `@_live` regression tests executed, not skipped — 117 passed across the three reference test files).

**The correctness trap (load-bearing) — VERIFIED no blackholing:**
- heavy_metal + road_warrior beat-vocabulary fall-through content (`event_flavor` etc.) still renders → `<section id="vocab">` + `href="#vocab"` present (live regression tests pass; content token found in HTML). ✅
- tea_and_murder achievements (real content) still render → `<section id="achievements">` + nav present. ✅
- road_warrior/spaghetti_western `achievements.yaml` are `[]` stubs, heavy_metal's is an empty file → correctly suppressed (confirmed by reading the actual YAML). ✅
- `_body_has_content` correctly distinguishes the `(empty)`/`(empty file)` placeholders and whitespace from real fall-through markup.

**Four scrutiny points:**
1. **Other `_wrap_sections_by_toc` callers?** Only two (`assemble_rules_page`, `assemble_lore_page`); both updated to unpack the `(body, kept_toc)` tuple and thread `kept_toc` to `_wrap_document`. No stray caller gets a tuple. (Note: `assemble_lore_page` now ALSO passes `toc_entries=kept_toc` — a consistent latent improvement post-63-10, prunes empty lore nav too; tested green.)
2. **Empty-body detection robust / false-suppress tiny sections?** Robust — only exact placeholders/whitespace suppress; the synthetic one-class `bearing` section and tea_and_murder survive (positive control test `test_suppression_is_surgical_nonempty_sections_survive`). No false suppression.
3. **63-7 fixture seeding intent-preserving?** Yes — strengthens (see audit).
4. **Dangling TOC link on drop?** No — `kept_toc` → `_build_toc` prunes the nav; suppression tests assert both `<section id=...>` AND `href="#...">` are absent.

**Observations:** (1) `_EMPTY_BODY_PLACEHOLDERS` hardcodes the two placeholder strings that `render_node` emits inline — a localized intra-module coupling; if those literals ever change, suppression would silently stop. Non-blocking NIT — a shared constant would harden it, but a test would catch drift. (2) No OTEL span correctly omitted (deterministic cosmetic presentation — consistent with repo principle). (3) Stale TOC comment in `reference_theme.py` correctly updated. (4) Old "emit empty section so anchor resolves" path fully removed — no dead code. (5) No security/data concern — pure presentation.

**Handoff:** To SM for finish ceremony (single-repo, sidequest-server).
