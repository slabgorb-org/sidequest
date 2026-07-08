# Story 162-11 Context

## Title
Understudy perception real-UI aria fidelity: two_names_one_enemy (162-7) and the tool-wide log:/panel assumptions parse aria tokens (region "Enemies", listitem, log:) absent from sidequest-ui — the detector returns None on every real session (inert in production).

## Metadata
- **Story ID:** 162-11
- **Type:** bug
- **Points:** 3
- **Priority:** p1
- **Workflow:** tdd
- **Repos:** understudy, ui
- **Epic:** 162 — NPC origin consolidation — one identity, one arbiter, derived Monster Manual

## Problem

Story 162-7 added a `two_names_one_enemy` detector to understudy's findings pipeline, which flags when a single creature appears under two names in the same confrontation (an identity fork). The detector works by parsing ARIA markup in the UI's ConfrontationOverlay and narration card surfaces.

However, the detector's regex patterns assume ARIA tokens that don't exist in the real `sidequest-ui` codebase:
- `region "Enemies"` — the enemies list has no ARIA region label
- `listitem` — opponent names lack listitem roles
- `log:` prefix in the narration surface — the narration card has no ARIA log role

As a result, the detector returns `None` on every real session and never fires. It works only in the wiring test fixture (which stubs the ARIA tokens) and is **inert in production**.

This blocks two outcomes:
1. The two_names_one_enemy detector can't validate that identity fixes (162-1, 162-2, 162-3) actually work in the live UI
2. Other understudy detectors that rely on similar assumptions also fail silently in production

## Technical Approach

### 1. Capture Real ConfrontationOverlay/Narration ARIA via perceive()
**File anchors:** sidequest-understudy/src/understudy/perception/*.py

The understudy bot perceives the UI via Playwright's `page.locator()` and screen-reader simulation (ADR-107 perception layer). Currently, the perception methods read DOM text and structure but don't capture ARIA roles, labels, or regions.

**Work:**
- Extend `perceive()` in the perception layer to extract ARIA roles, regions, and labels from the ConfrontationOverlay
  - Query the enemies container for ARIA region name
  - Extract listitem roles from opponent name elements
  - Check narration surface for ARIA live region roles (polite/assertive/log)
- Log the captured ARIA structure to the perception audit trail so we can verify what the real UI emits
- **No changes to understudy detector logic yet** — just capture and document

### 2. Add Perceivable ARIA Roles to UI Surfaces if Needed
**File anchors:** sidequest-ui/src/components/ConfrontationOverlay.tsx, NarrationCards.tsx

Examine the real UI surfaces (ConfrontationOverlay opponent list, narration card) to determine whether they need ARIA roles added:
- **Enemies container:** Add `role="region" aria-label="Enemies"` if not present
- **Opponent names:** Ensure each opponent name element has `role="listitem"` if it's a semantic list item
- **Narration surface:** Ensure the narration card container has `role="log" aria-live="polite"` or equivalent if it's a live-updating region

**Decision tree:**
- If ARIA roles are missing: add them (small, low-risk UI changes, no behavior change)
- If ARIA roles are present but understudy is querying for the wrong selectors: update the understudy query logic instead
- If ARIA roles are present but the detector regex is wrong: update the regex

**Testing:** Manually inspect the UI in DevTools; verify that the ConfrontationOverlay and narration surfaces have correct ARIA roles for a screen reader

### 3. Reconcile Understudy Detector Regexes + Wiring Fixtures
**File anchors:** sidequest-understudy/src/understudy/findings/*.py (detector implementation), tests/fixtures/ (wiring test stubs)

Once the real UI ARIA is captured:
- Update the `two_names_one_enemy` detector's regex patterns to match the real ARIA structure
- Update the wiring-test fixture stubs (tests/fixtures/*) to reflect the real UI markup, not the assumed markup
- Verify the detector fires in a **live confrontation** (not just the fixture)

**Implementation:**
1. **Live confrontation test:** Add a scenario that spawns two creatures with name variants (e.g., "Veyra" and "Veyra Solnë" via diacritic aliasing) and runs understudy against the real server + real UI. The two_names_one_enemy detector should flag this as a BEHAVIORAL/CONFIRMED finding.
2. **Regex validation:** For each regex pattern in the detector, add a unit test that verifies it matches the real ARIA tokens (or matches the fixed tokens if UI changes are needed)
3. **Wiring verification:** Confirm the detector is called in the understudy perception loop and the finding is emitted in the report

## Acceptance Criteria

**AC1 — Real ARIA capture:** The understudy perception layer extracts and logs ARIA roles, regions, and live-region settings from the ConfrontationOverlay and narration surfaces.
- Perception methods extend to query ARIA attributes
- Audit trail includes captured ARIA structure
- Log shows which tokens are present (or absent) in the real UI

**AC2 — UI ARIA correctness:** The ConfrontationOverlay and narration surfaces have perceivable ARIA roles for screen-reader / outsider tooling.
- Enemies container: `role="region" aria-label="Enemies"` or equivalent semantic region
- Opponent names: `role="listitem"` if the structure is a semantic list
- Narration surface: `role="log" aria-live="polite"` if it's a live-updating region
- Decision: Either UI changes are minimal (add missing roles), or detector logic is updated to match what the UI actually has

**AC3 — Detector regex validation:** The two_names_one_enemy detector's regex patterns are updated to match the real (or newly added) ARIA tokens.
- Regex unit tests verify each pattern matches the expected ARIA structure
- Fixture stubs in wiring tests reflect the real UI markup
- No silent returns (None) on valid ARIA input

**AC4 — Live confrontation test:** A scenario with identity-fork conditions (two name variants of the same creature) runs understudy against the real server + real UI, and the two_names_one_enemy detector fires with a CONFIRMED or BEHAVIORAL finding.
- Scenario definition: creature spawned with variant name (e.g., diacritic variant via 162-2 alias ledger)
- Detector output: CONFIRMED finding "two_names_one_enemy" or BEHAVIORAL finding indicating the fork
- Verification: understudy report includes the finding; no INTERNAL/NONE fallback

**AC5 — All understudy detectors benefit:** Other understudy detectors (if any) that rely on UI ARIA assumptions are verified to work with the fixed perception layer.
- Audit: enumerate detectors with ARIA dependencies
- Verification: each detector either fires in a live session or is marked as future work
- No new silent failures introduced

**AC6 — No production regressions:** All existing understudy scenarios and tests continue to pass with the new perception layer.
- Existing test suite green
- No new None-return silent failures in other detectors
- Ruff/pyright/pytest clean

## Success Definition

- Understudy perception captures and logs the real ARIA structure from sidequest-ui
- ConfrontationOverlay and narration surfaces are perceivable by screen-reader tools (ARIA roles added if needed)
- The two_names_one_enemy detector is updated to match the real UI ARIA and fires in a live confrontation with identity-fork conditions
- Live scenario confirms the detector catches the fork (CONFIRMED or BEHAVIORAL finding emitted)
- All existing understudy tests and scenarios remain green
- Code is clean (ruff/pyright/pytest passing)
- No silent failures; detectors either fire or fail loudly

---
_Generated by sm-setup for story 162-11 based on epic 162 context and 162-7 (two_names_one_enemy detector) setup._
