# Story 71-1: space_opera Rules page — render per-class signature ability in the class picker

## Story Details
- **ID:** 71-1
- **Epic:** 71 (Playtest bugfix — uncovered findings (coyote_star MP, 2026-05-27))
- **Type:** Bug
- **Points:** 3
- **Priority:** P2
- **Repos:** sidequest-server
- **Workflow:** tdd
- **Status:** backlog

## Story Context

**Problem:** The space_opera Rules page class picker currently renders a class card with:
- Display name (heading)
- Flavor text
- Role, Prime Requisite, Magic Access (label grid)
- Beat Choices (chip strip)

Missing: Each class has a **signature ability** (per ADR-095, exactly one per non-magical class) that should be visible on the class card. The ability includes:
- Name (e.g., "Call the Shot", "Threading the Needle")
- Genre description (narrative flavor)
- Mechanical effect (what the ability does)

Reference data: `/sidequest-content/genre_packs/space_opera/classes.yaml` — each class has an `abilities` list with a single item (involuntary: false).

**Acceptance Criteria:**

1. The `_class_panel_body()` function in `reference_presenters.py` extracts the class's signature ability (if present) and renders it in the class card.
2. The rendered ability includes the name, genre_description, and mechanical_effect in a visually distinct container within the card.
3. The card layout preserves existing elements (flavor, label grid, beat choices) and adds the ability section below them.
4. A test in `test_reference_presenters.py` verifies that a class with a signature ability renders all three fields (name, genre_description, mechanical_effect).
5. Lint and typecheck pass. No debug code. Tree clean.

## Technical Approach

The fix is a presenter enhancement:

1. **Extract ability from class dict** — In `_class_panel_body()`, after rendering the label grid and beat choices, check if the class has an `abilities` field (list).
2. **Render ability section** — If `abilities` is present and non-empty, extract the first item and render:
   - Ability name as a sub-heading (e.g., `<h4>`)
   - Genre description as narrative prose
   - Mechanical effect as a separate block (possibly with a distinct CSS class for visual emphasis)
3. **CSS class** — Use `ref-card__ability` or similar namespace (coordinating with story 63-7's reference CSS) to style the ability section. Do not invent new classes; ensure they exist in `sidequest/server/static/reference/presenters.css`.
4. **Unit test** — Add `test_class_picker_renders_signature_ability()` to `test_reference_presenters.py` that:
   - Constructs a class dict with an `abilities` list containing one ability
   - Calls `present_classes_picker()`
   - Asserts that the HTML contains the ability name, genre_description, and mechanical_effect
5. **Integration test** — Verify the wiring by checking that space_opera classes on the live Rules page render their signature abilities (can be done manually or via a page render fixture).

## Workflow Tracking
**Workflow:** tdd
**Phase:** setup
**Phase Started:** 2026-05-27

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-27 | - | - |

## Delivery Findings

No upstream findings.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Question** (non-blocking): The story/reference notes all space_opera signature abilities are `involuntary: false`, but the ACs do not specify whether an `involuntary: true` ability should be filtered out of the class picker. Dev should confirm intent — current tests render the first ability unconditionally. Affects `sidequest/server/reference_presenters.py` (`_class_panel_body` ability extraction). *Found by TEA during test design.*
- **Improvement** (non-blocking): AC-2 calls for a "visually distinct container" and the technical approach names `ref-card__ability`, but no such class exists in `sidequest/server/static/reference/presenters.css`. Dev must add the CSS rule (the `_disposition_badge` comment notes a chrome-wiring regression guard that trips on undefined `.ref-*` classes). Affects `sidequest/server/static/reference/presenters.css`. *Found by TEA during test design.*

## Design Deviations

None yet. Deviations logged here as they occur.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Presenter behavior change with explicit AC-4 requiring a unit test.

**Test Files:**
- `tests/server/test_reference_presenters.py` — 3 new tests for class-picker signature-ability rendering

**Tests Written:** 3 tests covering ACs 1–4
**Status:** RED (2 failing, ready for Dev; 1 guard test passes)

- `test_class_picker_renders_signature_ability` — FAILING (RED). Asserts name, genre_description, mechanical_effect render in a `ref-card__ability` container below beat choices. Fails because `_class_panel_body()` does not read `abilities`.
- `test_class_picker_escapes_signature_ability_content` — FAILING (RED). Asserts ability fields are HTML-escaped. Fails because ability content is not rendered at all.
- `test_class_picker_omits_ability_section_when_absent` — PASSING (guard). Protects AC-3: missing/empty `abilities` yields no ability container. Passes today (nothing rendered) and must continue passing after implementation.

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #11 input-validation / HTML escaping (CWE-79) | `test_class_picker_escapes_signature_ability_content` | failing |
| #6 test quality (self-applied) | all 3 — meaningful value assertions, no vacuous checks | n/a |

**Rules checked:** 2 of 14 lang-review rules apply to this presenter change (#6, #11). Others (#1 exceptions, #2 mutable defaults, #7 resource leaks, #8 deserialization, #9 async, #14 state cleanup) are not exercised by a pure HTML presenter function.
**Self-check:** 0 vacuous tests. Every assertion checks a specific string/ordering.

**Handoff:** To Dev for implementation (GREEN).
