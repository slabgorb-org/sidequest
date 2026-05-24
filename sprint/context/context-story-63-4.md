# Story 63-4: Chrome rendering — context & acceptance criteria

**Story ID:** 63-4  
**Epic:** 63 (Reference pages v3)  
**Workflow:** TDD (red → green → refactor)  
**Plan Reference:** docs/superpowers/plans/2026-05-23-reference-pages-v3.md Tasks 18, 20–22

---

## Story Scope

Server-side chrome rendering for reference pages: per-pack palette + font injection, static CSS route, hero section, contents rail (TOC), and per-file section markup wrapping.

The story implements Tasks 18, 20–22 from the v3 plan. Tasks 1–16 (v2: hyperlinks + protocol fields + UI panels) are already complete on develop. Task 19 (display_font_family field in content packs) is a dependency (63-3) completed 2026-05-24.

---

## Task Surfaces

### Task 18: Renderer Reads `theme.yaml` + Emits Chrome Data Attributes

**Files:**
- New: `sidequest-server/sidequest/server/reference_theme.py` — pure loader
- Modify: `sidequest-server/sidequest/server/reference_renderer.py` (assemble_rules_page, assemble_lore_page, _wrap_document)
- Test: `tests/server/test_reference_theme.py`

**Deliverable:**
- ReferenceTheme dataclass collects archetype, palette (primary/accent/background), web_font_family, display_font_family, and three dinkus glyphs from theme.yaml
- Renderer emits `<html data-pack="tea_and_murder" data-world="glenross" data-archetype="parchment" class="dark">` (or similar per pack)
- Missing required field raises `MissingThemeFieldError` — loud, no silent fallback
- Renderer threads theme into _wrap_document so HTML attributes flow to browser

**AC1:** theme.yaml missing display_font_family (dependency: 63-3 must land first) raises ERROR span (`sidequest.reference.theme_missing`) with field name in message.  
**AC2:** Per-pack archetype, palette, web/display font, dinkus glyphs all populated in rendered HTML `<html>` element.

### Task 20: Static CSS Route Serves Bundled `theme.css` + `styles.css`

**Files:**
- Create: `sidequest-server/sidequest/server/reference_static.py` — FastAPI sub-router
- Move: `docs/design-bundles/2026-05-23-lore-and-rules/project/{theme,styles}.css` → `sidequest-server/sidequest/server/static/reference/{theme,styles}.css`
- Modify: `sidequest-server/sidequest/server/reference_routes.py` (mount sub-router at /reference/static/)
- Modify: `sidequest-server/sidequest/server/reference_renderer.py` (_wrap_document emits stylesheet links)
- Test: `tests/server/test_reference_static.py`

**Design Bundle Source:** `/Users/slabgorb/Projects/oq-1/docs/design-bundles/2026-05-23-lore-and-rules/project/`

**Critical:** The bundle's CSS includes dead `.tweaks-panel`, `.tweaks-toggle`, `.tweaks-body` selectors used only by the design tool's iteration UI. These are **design-tool affordances, NOT product features** — strip them during the copy-to-production step. See ADR-048 / CLAUDE.md feedback [no-design-tool-affordances](design_tool_affordances_arent_features.md).

**Deliverable:**
- `GET /reference/static/theme.css` returns the bundled theme.css (content-type: text/css)
- `GET /reference/static/styles.css` returns the bundled styles.css (content-type: text/css)
- _wrap_document emits both `<link>` tags (theme first, styles second; styles wins on conflicts)
- No .tweaks-* selectors in final CSS files

**AC3:** Static CSS route returns 200 with correct content-type; CSS payloads contain theme tokens (e.g., color variables, font declarations).  
**AC4:** Dead .tweaks-panel/.tweaks-toggle/.tweaks-body selectors verified absent from both CSS files.

### Task 21: Emit the Hero Section with World Name

**Files:**
- Modify: `sidequest-server/sidequest/server/reference_renderer.py` (assemble_lore_page)
- Test: `tests/server/test_reference_renderer.py` (new cases)

**Deliverable:**
- Hero markup emitted server-side in _wrap_document or assemble_lore_page
- Displays world name from lore.yaml (e.g., "Glenross") + a brief lore epigraph/intro
- Falls back to pack name only if world is unbound (logs WARN span)
- Hero anchor id is stable (e.g., `id="hero"` or slugified world name) for scroll-spy

**AC5:** Hero block renders with world name + lore intro text fetched from lore.yaml.  
**AC6:** Hero markdown/HTML properly escaped (no XSS); falls back to pack name with WARN span if lore.yaml missing.

### Task 22: Emit the Contents Rail (TOC) + Per-File Section Markup

**Files:**
- Modify: `sidequest-server/sidequest/server/reference_renderer.py` (_render_file, render_node)
- Test: `tests/server/test_reference_renderer.py` (new cases)

**Deliverable:**
- Contents rail markup emitted server-side (locked, not toggleable in browser)
- TOC structure populated from file stems + list-of-dict item names
- Markup includes `data-scroll-spy` attrs or equivalent hooks for IntersectionObserver
- Per-file sections wrapped in `<section id="file-{stem}">` with stable ids
- List-of-dict items (classes, cultures, etc.) already have namespaced ids from Task 2 (e.g., `class-knight`)
- IntersectionObserver scroll-spy wired via ~15-line inline JS (can be embedded in HTML or loaded from static route)

**AC7:** Contents rail markup present in _wrap_document output; locked (no toggle UI).  
**AC8:** Per-file section wrappers with stable `id` attributes allow contents rail TOC to link to them.  
**AC9:** List-of-dict item ids are namespaced (e.g., `class-knight` not `knight`) per Task 2.  
**AC10:** IntersectionObserver scroll-spy hooks (data-scroll-spy or equivalent) present in markup; JS inline ~15 lines.

---

## Acceptance Criteria (Full Story 63-4)

These roll in the test gaps from canceled stories 63-1 and 63-2:

1. **Per-pack theme injection** via `<html data-pack data-world data-archetype>`, palette + web_font_family + display_font_family pulled from theme.yaml; missing fields fail loud with ERROR span (no silent fallback).

2. **Static CSS route** serves bundled theme.css + styles.css; both linked in _wrap_document; dead .tweaks-* selectors stripped before commit.

3. **Hero block** renders world name from lore.yaml + epigraph; falls back to pack name only if world is unbound (then logs WARN span).

4. **Contents rail markup** emitted server-side; locked (not toggleable); IntersectionObserver scroll-spy ~15 lines inline JS.

5. **ROLLED-IN from 63-1 cancellation:** write `tests/server/test_reference_otel.py` covering reference URL attached/skipped/failed spans against the existing `sidequest/telemetry/spans/reference.py` helpers.

6. **ROLLED-IN from 63-2 cancellation:** write `sidequest-ui/src/components/__tests__/LocationPanel.reference.test.tsx` mirroring CharacterSheet.reference.test.tsx pattern.

---

## Repo Touchpoints

### sidequest-server

- `sidequest/server/reference_renderer.py` — existing, will be modified
- `sidequest/server/reference_theme.py` — new module (Task 18)
- `sidequest/server/reference_static.py` — new sub-router (Task 20)
- `sidequest/server/static/reference/` — new directory, will contain theme.css + styles.css
- `sidequest/telemetry/spans/reference.py` — existing helpers, test coverage gap to fill (AC5)
- `tests/server/test_reference_theme.py` — new
- `tests/server/test_reference_static.py` — new
- `tests/server/test_reference_otel.py` — new (rolled-in from 63-1)
- Tests in `test_reference_renderer.py` — append hero + contents rail cases

### sidequest-ui

- `src/components/__tests__/LocationPanel.reference.test.tsx` — new (rolled-in from 63-2)

### sidequest-content

- `genre_packs/<pack>/theme.yaml` — dependency on 63-3; must include display_font_family field
- No changes needed by this story; content is already updated by 63-3

---

## Design Bundle Location

`/Users/slabgorb/Projects/oq-1/docs/design-bundles/2026-05-23-lore-and-rules/`

**Files to reference:**
- `/project/theme.css` — contains per-pack CSS variables + structural styles; serves at `/reference/static/theme.css`
- `/project/styles.css` — component/page styles; serves at `/reference/static/styles.css`
- `/project/*.html` — visual contract (JSX prototypes); DOM structure should match byte-equivalently

**Critical:** The bundle's CSS includes designer-tool UI (`.tweaks-panel`, `.tweaks-toggle`, `.tweaks-body`). These are **out of scope** per project memory and CLAUDE.md feedback — strip them during CSS copy.

---

## Risk Register

1. **Dependency on 63-3:** display_font_family must flow through theme.yaml before this story can assert complete chrome. Verify 63-3 merged to develop before claiming AC2. If 63-3 hasn't landed, raise as a blocker for the RED phase.

2. **Per-pack palette/font injection point:** Decide whether per-pack tokens go in HEAD as inline `<style>` (per-request, varies by pack) or as a CSS route parameter (`?pack=foo`). The design bundle's theme.css likely defines CSS variables; per-pack values from theme.yaml need to override them. Document this decision in the story session file.

3. **Test discipline:** Per project memory (no-content-coupled-tests), pytest must not load live `genre_packs/*` and assert per-pack chrome. Use FIXTURES for unit tests and VALIDATORS for live pack coverage. Markup-shape tests run against fixture packs.

4. **Design-tool affordance removal:** Grep the bundled CSS for `.tweaks-` selectors. Strip them before committing the copied CSS to production. This is a non-optional step — keeping them would expose dead UI concepts.

---

## Testing Strategy

Per project memory [no-content-coupled-tests](feedback_no_content_coupled_tests.md):

- **Unit tests:** Use fixture packs with minimal theme.yaml + lore.yaml. Assert markup shape (hero presence, contents rail structure, per-file ids).
- **Integration tests:** Test reference routes against fixture pack to verify route returns 200 and contains theme tokens.
- **Validator (separate from pytest):** Live-pack scanner (`python -m sidequest.cli.validate reference-chrome <pack>`) walks every pack's theme.yaml for required chrome fields. Coverage is the validator's job, not pytest's.
- **No live pack assertions:** Never write `for pack in genre_packs: assert pack.theme.display_font_family ...` in pytest. That's a validator job.

---

## Implementation Notes

- **Server-side rendering only:** Reference pages are generated by Python at request time. No React SPA, no client-side enrichment. The design bundle's JSX is a **visual contract, not runtime code**.
- **No silent fallbacks:** Missing theme.yaml fields, missing lore.yaml sections, and unresolved anchors all produce ERROR or WARN spans. Loud logging is the safety net.
- **One mechanism per problem:** The renderer is the single emitter of chrome. No parallel client-side enricher or post-render JS injection. The IntersectionObserver scroll-spy is inline (~15 LOC), not a separate bundle.

---

## Dependency

- **63-3 (completed 2026-05-24):** display_font_family field added to all genre_packs' theme.yaml
- **v2 Tasks 1–16 (merged 2026-05-23):** hyperlink protocol + URL builders + UI panels

---

## Resources

- Plan: `/Users/slabgorb/Projects/oq-1/docs/superpowers/plans/2026-05-23-reference-pages-v3.md`
- Design spec: `/Users/slabgorb/Projects/oq-1/docs/superpowers/specs/2026-05-23-reference-pages-v2-design.md`
- Design bundle: `/Users/slabgorb/Projects/oq-1/docs/design-bundles/2026-05-23-lore-and-rules/`
- ADR-037 (reference pages): `docs/adr/037-unified-narrator.md` (historical, context only)
- CLAUDE.md feedback: design-tool-affordances, no-content-coupled-tests, no-silent-fallbacks
