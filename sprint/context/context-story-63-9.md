---
parent: context-epic-63.md
workflow: tdd
---

# Story 63-9: Reference renderer humanization guard — never emit raw key/dict/snake_case/bool/dev-note prose; humanize section-key headings; + output-scan test

## Business Context

The `/reference/rules/<pack>` and `/reference/lore/<pack>/<world>` pages are SideQuest's in-world wiki — player- and author-facing surfaces (Jade authors content against them per CLAUDE.md). When the renderer hits a section that has no dedicated presenter, it falls back to a generic walk that emits the raw YAML structure: snake_case keys as headings, Python `repr()` of dicts/lists, bare `True`/`False`, and occasionally dev-note/placeholder strings. That breaks the wiki illusion — a reader sees `mechanical_surface` instead of "Mechanical Surface", or `{'tier': 1, 'cost': 2}` instead of prose. This story makes the renderer's fallback path *safe by construction*: anything that reaches HTML is humanized, and a test scans the rendered output to prove no raw developer string leaks through. The value is presentation integrity across every pack/world — including ones authored after this lands, since the guard is structural, not a per-section patch.

## Technical Guardrails

**Key files (server-only story):**
- `sidequest-server/sidequest/server/reference_renderer.py` — the generic fallback walk (`<h2>key</h2>` path) lives here; this is the primary humanization seam.
- `sidequest-server/sidequest/server/reference_presenters.py` — per-section presenters and `PresenterContext`; a shared humanize helper should live where both the renderer fallback and presenters can use it.
- `sidequest-server/sidequest/telemetry/spans/reference.py` — `SPAN_REFERENCE_*` flat-only OTEL spans. Per the OTEL Observability Principle, the guard firing (a raw string caught and humanized, or a dev-note suppressed) should emit a span so the GM panel can verify the guard is engaged and not just dormant.

**Patterns to follow:**
- **No Source-Text Wiring Tests** (epic's recurring lesson, codified in `sidequest-server/CLAUDE.md`): the output-scan test must assert against the **served HTML artifact**, not the existence of a helper function or a source string. Render a fixture page and scan the resulting HTML for raw-string leakage.
- Humanization is a pure transform `key -> display` (underscores→spaces, title-case, `True`/`False`→`Yes`/`No`, suppress/format dict & list reprs). Keep it a pure function — no I/O, no theme dependence.
- **No Silent Fallbacks** (project rule): when the guard catches a dev-note or unrenderable value, it should suppress it *loudly* (OTEL span), not vanish it silently.

**Integration points:** the generic walk in `reference_renderer.py` is the only place raw keys currently reach HTML; presenters already humanize their own output. Verify the helper is wired into the fallback walk, not just defined.

**Do NOT touch:** the chrome/CSS (63-4/63-7 territory), the anchor/slug system, `EXCLUDED_FILES` policy, or any presenter's intentional formatting. This is purely the fallback-path humanization + scan test.

## Scope Boundaries

**In scope:**
- A humanization helper applied to section-key headings (h2/h3) in the generic fallback walk: underscores→spaces, title-case, bool→Yes/No.
- Guard against raw dict/list `repr()` and raw bool values reaching HTML from the fallback walk.
- Suppress or humanize dev-note/placeholder prose so it never renders to a reader.
- An output-scan test that renders a fixture page (against `reference_v2_fixture`) and asserts the served HTML contains no raw snake_case heading, no Python dict/list repr, no bare `True`/`False`, no dev-note marker.
- OTEL span emitted when the guard humanizes/suppresses, so the GM panel can confirm engagement.

**Out of scope:**
- Any new per-section presenter (this is the *fallback* path only).
- Chrome, CSS, fonts, palettes, hero, contents rail (63-4/63-7).
- Lore-vs-genre content decisions (63-10), empty-section suppression (63-11), validator crash-hardening (63-13).
- Live `genre_packs/*` coverage — that is the content validator's job, not a server unit test.

## AC Context

This story has no formal acceptance_criteria in the epic YAML — the Architect should ratify these derived ACs in the design phase before TEA writes RED tests.

Derived ACs (testable):
1. **Heading humanization** — a fixture section keyed `mechanical_surface` renders as a heading reading "Mechanical Surface" (spaces, title case), never `mechanical_surface`. Edge cases: already-humanized keys pass through unchanged; acronyms/initialisms (decide policy — likely leave as-is or title-case) documented.
2. **No raw container reprs** — a fixture value that is a dict or list reaching the fallback walk never renders as `{...}`/`[...]` Python repr; it is either dispatched to structured markup or formatted as prose. Test scans HTML for `{'` / `[{` / `': ` repr signatures.
3. **No raw bools** — a fixture bool value renders as `Yes`/`No` (or is suppressed), never `True`/`False`. Test scans for the bare tokens in text nodes.
4. **No dev-note leakage** — a fixture field carrying a dev-note/placeholder marker does not appear in rendered HTML; suppression fires an OTEL span.
5. **Output-scan test exists and is the gate** — renders a fixture page end-to-end and asserts the served HTML is free of all the above raw signatures. This is a behavior-against-artifact test, not a source-text assertion.
6. **OTEL engagement** — the guard emits a `SPAN_REFERENCE_*` span when it humanizes/suppresses, verifiable from the span registry.

## Assumptions

- The generic fallback walk in `reference_renderer.py` is the **only** path that emits un-humanized keys; presenters already humanize. (If a presenter is found leaking raw strings, that's an in-scope fix or a Design Deviation — log it.)
- The `reference_v2_fixture` pack (world `long_fixture`) can host a section that exercises the fallback walk; if no such section exists, a fixture addition is in scope for the test.
- `SPAN_REFERENCE_*` flat-only span pattern is the right home for the guard's telemetry (consistent with epic architecture).
- 63-4/63-7 chrome is merged and stable (confirmed: done).

If any assumption proves wrong during implementation, log it as a Design Deviation in the session file and notify SM.
