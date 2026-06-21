# Story 153-15 Context: [SWN-CHARGEN-RECAP-GRAMMAR] map background label to a noun form and drop the from-race-space stitch

**Story ID:** 153-15  
**Epic:** 153 (Playtest follow-ups)  
**Points:** 1  
**Type:** chore  
**Priority:** p3  
**Workflow:** trivial  
**Repos:** server  

## Summary

This is a grammar/prose-quality fix in the SWN (Without Number) character-generation confirmation recap. Two distinct asks in the title:

1. **Map background label to a noun form** — the chargen confirmation summary surfaces the character's `background_label` (a display flavor label, last-wins, symmetric with `race_label`/`class_label`). It should be rendered as a noun form rather than whatever raw/adjectival form is currently emitted in the recap sentence.

2. **Drop the from-race-space stitch** — there is a recap sentence that stitches race + background into a phrasing like "... from {race} space" which reads badly. That from-race-space stitch should be removed.

## Technical Context

This is a server-only, content-grammar fix focused on the chargen summary rendering pipeline.

### Relevant Files

The implementation touches these two files:

- **`sidequest/server/dispatch/chargen_summary.py`** — renders the confirmation summary
  - `render_confirmation_summary` function
  - `_add(...)` projection
  - `background_display` / `backstory_label` handling (~lines 254, 378–382)
  - humanize/title-case helpers (~lines 95–126)
  - The recap-sentence stitch and background-label rendering live in this area

- **`sidequest/game/builder.py`** — character-builder state accumulation
  - `background_label` / `race_label` / `freeform_race_label` accumulation (defs ~lines 361, 427; assignment ~1535–1560)
  - summary-render notes (~lines 1504, 1689, 1754–1755)

### Acceptance Criteria

1. **AC-1:** The chargen confirmation recap renders the background label in a noun form (not raw/adjectival form).
2. **AC-2:** The "from {race} space" stitch is removed from the recap sentence.
3. **AC-3:** A unit test covers both the noun-form rendering and the absence of the from-race-space stitch.
4. **AC-4:** No silent fallbacks; existing chargen-summary tests still pass.

### Approach for Dev

1. Investigate the chargen_summary.py recap rendering, identify the exact lines that emit the background label and the "from {race} space" stitch.
2. Extract or add a helper to map the background label to a noun form (similar to how race_label and class_label are handled).
3. Remove the "from {race} space" stitching logic from the recap sentence.
4. Write a unit test that verifies:
   - The background label appears in noun form in the recap
   - The recap does NOT contain the substring "from {race} space"
   - Existing tests continue to pass
5. Verify the fix in chargen flow end-to-end.

## Context Notes

- No Jira key; Jira is not configured for this project.
- Phased trivial workflow: setup → implement → review → finish.
- Small story (1 point, chore). Likely localized to chargen_summary.py with a small targeted test.
- Part of the playtest follow-ups epic (153) addressing findings from the 2026-06-20/21 full-stack /sq-playtest sweep.
