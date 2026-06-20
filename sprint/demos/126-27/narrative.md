# Narrative

## Problem Statement
**Problem:** A recently removed UI feature (the Fate dock tab, story 126-26) left a trail of dead code and stale documentation comments throughout the frontend codebase. A JavaScript function with no live callers, two test files that only existed to test that dead function, and six code comments still describing a widget that no longer exists.

**Why it matters:** Dead code is invisible technical debt — it occupies mental space when developers read files, creates false leads when searching the codebase, and can cause type-checking tools to fail unexpectedly. Stale comments are worse than no comments: they actively mislead. Left unaddressed, these accumulate across refactors and make the codebase incrementally harder to trust.

---

## What Changed
Imagine you removed a door from a building but left the doorframe, the welcome mat, and all the signs pointing to it on other floors. That's what story 126-26 left behind. Story 126-27 cleaned all of it up.

Specifically:

- **Deleted a function nobody calls anymore.** `FatePanel` was a UI component whose only job was to render a pop-out dock tab. When 126-26 deleted that dock tab, the function lost its only caller. It was now ghost code — present in the file, compiled on every build, but never shown to a player. Gone.
- **Deleted the tests for that ghost function.** Two test files (518 lines combined) existed solely to test `FatePanel`. With the function gone, they tested nothing live. Deleted.
- **Cleaned up six stale comments.** Six places in the codebase still described "the dock FateWidget" and "the FatePanel" as if they were current. Three were called out in the story spec; three more were discovered during implementation because they named a now-deleted function as its present-tense owner. All six reworded to describe what actually exists today.

Net result: **552 lines deleted, 20 lines added** (the 20 are the reworded comments). All 515 existing tests remain green.

---

## Why This Approach
The codebase enforces `noUnusedLocals` and `noUnusedParameters` in TypeScript — meaning that leaving the orphaned private symbols alongside the deleted function would have caused a hard build failure. Deleting the function necessarily meant deleting its private-only dependencies (a props interface, two constants, three imports). This is enforced discipline, not optional tidiness.

The comment sweep was extended beyond the three files named in the story spec because when you delete a function, any comment still naming it present-tense as "the renderer" is immediately false. Cleaning references to one's own deletion is intrinsic housekeeping, not scope creep. The one surface explicitly off-limits (`FateConflictSurface.tsx`, which has two similar stale refs) was deliberately left alone and logged as a follow-up finding — discipline enforced even when cleaning up.

---

## Before/After
| | Before | After |
|---|---|---|
| `FatePanel` function | Present in `FatePanel.tsx` (~250 lines), production-unreferenced | Deleted |
| `FatePanelProps`, `FONT_BODY`, `PANEL_LABEL` | Orphaned private symbols in same file | Deleted (compiler-enforced) |
| `FatePanel.test.tsx` | 2 test files, 518 lines, testing dead code | Deleted |
| Comment at `FatePanel.tsx:142` | `"the dock FateWidget AND the in-game Character panel"` | `"the Character panel Stats tab"` |
| Comment at `GameBoard-fate-conflict.test.tsx:18` | Referenced `FateWidget` as the consumer | Reworded to post-126-26 reality |
| Comment at `useStateMirror.fate-roll.test.ts:9` | Referenced `FateWidget` as the consumer | Reworded to post-126-26 reality |
| Comments at `protocol.ts:109`, `payloads.ts:1153`, `FatePanel.tsx:284` | Named deleted `FatePanel` function as live renderer | Reworded to `FateCharacterSheet` |
| `FateCharacterSheet`, `FateStunts`, shared helpers | Present, used by `CharacterPanel` | **Unchanged — still present** |
| Test suite | 515/515 passing | 515/515 passing |
| TypeScript new errors | N/A | 0 new errors introduced |

**Summary:** The file tells the truth now. What exists in code matches what players can actually see. The function that was deleted last sprint no longer casts a shadow in tests, comments, or type definitions.
