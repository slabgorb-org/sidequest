> This story has no runtime behavior change — the deleted code was never reachable by players. There is nothing to demo live. The before/after is a code comparison.

**Slide 2 (Problem):** Open `src/components/FatePanel.tsx` in the `before` state. Show the `FatePanel` function at line 304 — 250 lines of JSX nobody was calling. Point out the comment at line 142 still referencing a dock widget that was deleted last sprint.

**Slide 3 (What We Built):** Show the same file in the `after` state — the file is shorter; `FateCharacterSheet` (which is still used by the Character panel) remains intact. Then show the test count: `npx vitest run Fate GameBoard CharacterPanel useStateMirror` — 515 passing, same count before and after, meaning zero regression.

**Slide 4 (Why This Approach):** Show the TypeScript error that would have appeared if the orphaned private symbols had been left behind — the build enforced the cleanup rather than making it optional.

**Before/After slide:** Side-by-side of the old comment (`"used by the dock FateWidget AND the in-game Character panel"`) vs. the new wording (`"used by the Character panel Stats tab"`). One sentence; now accurate.

**Fallback:** If no live IDE is available, show the PR diff — 552 deletions in red, 20 additions in green. The ratio tells the story.

---