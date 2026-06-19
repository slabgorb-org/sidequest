---
story_id: "126-26"
jira_key: ""
epic: "126"
workflow: "tdd"
---
# Story 126-26: [FATE/UX] Remove the duplicate Fate dock tab + re-home the non-conflict 4dF roll surface under Character (PART B of 126-19)

## Story Details
- **ID:** 126-26
- **Jira Key:** (none — local sprint ID)
- **Workflow:** tdd
- **Stack Parent:** none
- **Branch:** feat/126-26-remove-duplicate-fate-tab
- **Branch Strategy:** gitflow (feat/{STORY_ID}-{SLUG})

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-19T14:49:33Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-19T14:13:05Z | 2026-06-19T14:14:49Z | 1m 44s |
| red | 2026-06-19T14:14:49Z | 2026-06-19T14:23:49Z | 9m |
| green | 2026-06-19T14:23:49Z | 2026-06-19T14:31:07Z | 7m 18s |
| review | 2026-06-19T14:31:07Z | 2026-06-19T14:41:35Z | 10m 28s |
| green | 2026-06-19T14:41:35Z | 2026-06-19T14:45:11Z | 3m 36s |
| review | 2026-06-19T14:45:11Z | 2026-06-19T14:49:33Z | 4m 22s |
| finish | 2026-06-19T14:49:33Z | - | - |

## SM Assessment

**Routing decision:** New work, 3pt tdd/phased → red phase first → hand off to TEA (Amos Burton). TEA writes failing tests that pin the new reality before Dev refactors.

**Merge gate:** Clear. Only 150-1 in progress (playtest, no PR); no open PRs in any repo. (126-15 and 126-25 landed in other workspaces — pulled clean.)

**Why this is NOT a trivial deletion (the load-bearing fact for TEA/Dev):**
The standalone `fate` dock tab duplicates the Fate sheet now under Character→Stats (118-2 consolidation) — EXCEPT it uniquely hosts 118-7's non-conflict 4dF roll tray (`FateDiceTray`, testid `fate-dice-tray`) via `FateWidget`→`FatePanel`. That tray is NOT duplicated under Character (the `FateCharacterSheet` takes no `latestRoll`). **Order matters: re-home the roll tray FIRST, then remove the tab.** Deleting wholesale loses the out-of-conflict roll surface and reddens `GameBoard-fate-roll.test.tsx`.

**Behavioral contract for the RED phase (what TEA must pin):**
1. The non-conflict 4dF roll tray (`fate-dice-tray`) still renders after a roll, in its NEW single home (Character surface preferred), reachable end-to-end through GameBoard.
2. The standalone `fate` dock/mobile tab no longer exists.
3. The `fate-conflict` surface is UNTOUCHED and still has its own tray.
4. No dangling `fate` references: `WidgetId` union, `WIDGET_REGISTRY`, GameBoard `availableWidgets`/`renderWidgetContent`/`rightGroupOrder`, `MobileTabView` TABS, `widgets/FateWidget.tsx`.

**Out of scope:** the `fate-conflict` widget + its tray; the `FateCharacterSheet` itself (only host the re-homed tray near it).

**Naming guard:** This is 126-26 (UI). It was mis-numbered 126-25 in a stale local branch; 126-25 is the SERVER Fate-gear story (separate, done). Do not collide.

**Branch:** `feat/126-26-remove-duplicate-fate-tab` (base `develop`, sidequest-ui github-flow).

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

No upstream findings

### TEA (test design)
- No upstream findings during test design. The story scope was accurate: the standalone `fate` tab exists, the `fate-conflict` surface is distinct, and the Fate sheet is already consolidated under Character→Stats (118-2). The only un-duplicated surface is the non-conflict roll tray, exactly as the story said.

### Dev (implementation)
- **Improvement** (non-blocking): With the `fate` widget gone, the `FatePanel` *function* in `src/components/FatePanel.tsx` is now production-unreferenced (only `FateCharacterSheet`, exported from the same file, is still imported — by `CharacterPanel`). I left `FatePanel` intact because it has dedicated passing tests (`FatePanel.test.tsx`, `FatePanel.fateRoll.test.tsx`) and removing it is outside this story's named cleanup scope (which listed only `widgets/FateWidget.tsx`). Affects `sidequest-ui/src/components/FatePanel.tsx` (a follow-up could delete the unused `FatePanel` function + its two test files, keeping `FateCharacterSheet`). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `src/components/FatePanel.tsx:142` and the unchanged test comments at `GameBoard-fate-conflict.test.tsx:18` / `useStateMirror.fate-roll.test.ts:9` still reference `FateWidget` (now deleted). They're outside this diff so not part of the rework, but a follow-up should sweep them (pairs with Dev's FatePanel-unreferenced finding). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the tab-removal suite's preservation block only asserts the Fate sheet shows on a Fate pack; a symmetric native-pack negative (`fateData:null` → no `fate-character`, native StatsContent survives) would harden it. The roll suite already has its native-pack negative. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the roll wiring test asserts `fate-dice-tray` is present anywhere in the DOM; a containment/count assertion (tray is inside the Character panel, exactly one instance) would self-seal it against a future stray tray from another surface. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 1 findings (0 Gap, 0 Conflict, 0 Question, 1 Improvement)
**Blocking:** None

- **Improvement:** With the `fate` widget gone, the `FatePanel` *function* in `src/components/FatePanel.tsx` is now production-unreferenced (only `FateCharacterSheet`, exported from the same file, is still imported — by `CharacterPanel`). I left `FatePanel` intact because it has dedicated passing tests (`FatePanel.test.tsx`, `FatePanel.fateRoll.test.tsx`) and removing it is outside this story's named cleanup scope (which listed only `widgets/FateWidget.tsx`). Affects `sidequest-ui/src/components/FatePanel.tsx`.

### Downstream Effects

- **`sidequest-ui/src/components`** — 1 finding

### Deviation Justifications

1 deviation

- **Pinned the roll-tray re-home target to Character→Stats (not free choice)**
  - Rationale: Character→Stats is the spec's *preferred* home AND already hosts the Fate sheet (118-2), so sheet+roll stay co-located — the same layout the old FatePanel had (tray above sheet). Picking a concrete home is required to write a deterministic wiring test.
  - Severity: minor
  - Forward impact: minor — if Dev re-homes the tray somewhere other than Character→Stats, `GameBoard-fate-roll.test.tsx` must be updated to the chosen home. The behavioral contract (tray survives, fateData-gated, reachable through GameBoard) is unchanged either way.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Pinned the roll-tray re-home target to Character→Stats (not free choice)**
  - Spec source: context-story-126-26.md / session scope ("Re-home the non-conflict roll tray under Character (or another single home)")
  - Spec text: "Re-home the non-conflict 4dF roll tray ... under Character (preferred) or another single home"
  - Implementation: Tests assert the tray (`fate-dice-tray`) mounts under the Character surface specifically — the Stats tab, beside the existing `FateCharacterSheet` (`fate-character`), reached via the Character tab (Stats is CharacterPanel's default). Dev must thread `latestFateRoll` into the Character render path (CharacterWidget → CharacterPanel) mirroring how `fateSheet` is already threaded.
  - Rationale: Character→Stats is the spec's *preferred* home AND already hosts the Fate sheet (118-2), so sheet+roll stay co-located — the same layout the old FatePanel had (tray above sheet). Picking a concrete home is required to write a deterministic wiring test.
  - Severity: minor
  - Forward impact: minor — if Dev re-homes the tray somewhere other than Character→Stats, `GameBoard-fate-roll.test.tsx` must be updated to the chosen home. The behavioral contract (tray survives, fateData-gated, reachable through GameBoard) is unchanged either way.

### Dev (implementation)
- **Honored TEA's pinned re-home target (Character→Stats) exactly — no deviation.** Threaded `latestFateRoll` → CharacterWidget (`{...props}` pass-through) → CharacterPanel's new `fateRoll` prop; the Stats tab mounts `<FateDiceTray roll={fateRoll} ruleset="fate" />` above `FateCharacterSheet` when `fateSheet && fateRoll`, mirroring the old FatePanel layout (tray above sheet). The `fateSheet ?` branch already gates on Fate, so a native pack never mounts the tray even though GameBoard passes `fateRoll` unconditionally.
- **Left `FatePanel` (function) in place rather than deleting the now-unreferenced code.** Logged as a non-blocking Delivery Finding above (it has passing tests and is outside this story's named cleanup scope of `widgets/FateWidget.tsx`). This is a conscious scope boundary, not an oversight.

### Reviewer (audit)
- **TEA's pinned re-home target (Character→Stats)** → ✓ ACCEPTED: the spec's *preferred* home; Dev implemented it exactly (CharacterPanel `fateRoll` prop, FateDiceTray above FateCharacterSheet in the Stats tab). Reachable end-to-end through GameBoard, verified by the wiring test. Sound.
- **Dev's `fateSheet ?`-branch gating of the re-homed tray** → ✓ ACCEPTED: mounting the tray inside the existing `fateSheet ?` branch makes the ruleset gate free (native packs have null fateSheet → no tray), confirmed by the roll suite's native-pack negative and the rule-checker (two-level guard, no native regression).
- **Dev's decision to leave the now-unreferenced `FatePanel` function** → ✓ ACCEPTED: correct scope boundary — it has passing tests and is outside the story's named cleanup (`widgets/FateWidget.tsx` only). Filed as a non-blocking follow-up, not an oversight.
- **UNDOCUMENTED (Reviewer-found):** the removal left three stale comments in `GameBoard.tsx` that describe the deleted Fate tab in present tense (lines ~199, ~448, ~602) — see the REJECT findings table. Spec scope was "clean up the dead path on removal"; stale docs about the removed path are an incomplete-cleanup miss. Severity M/L. Routed back for green rework.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Behavior-changing refactor (a tab is removed, a surface re-homes) — the existing suites encode the OLD reality and must be flipped to the new contract. Not a chore bypass.

**Test Files (modified — flipped to the new reality):**
- `src/components/GameBoard/__tests__/GameBoard-fate-tab.test.tsx` — was 118-2's "fate tab exists" suite; now pins REMOVAL of the duplicate `fate` widget + dead-path cleanup, with two preservation guards.
- `src/components/GameBoard/__tests__/GameBoard-fate-roll.test.tsx` — was 118-7's "roll tray in the dock fate tab" suite; now pins the roll tray RE-HOMED under Character→Stats, still fateData-gated.

**Tests Written:** 10 tests total across the two files (6 failing = the new contract, 3 passing = preservation/ruleset guards, 1 paired-negative passing).
**Status:** RED (verified) — `tsc --noEmit` clean (no type errors; tests use only real `GameBoardProps`).

**RED breakdown (verified by testing-runner, RUN_ID 126-26-tea-red):**
- fate-tab: 5 FAIL (registry `fate` gone · hotkey `f` free · `FateWidget.tsx` deleted · MobileTabView `fate` entry gone · no standalone "Fate" tab) + 2 PASS guards (`fate-conflict` kept · Fate sheet survives under Character→Stats).
- fate-roll: 1 FAIL (tray mounts under Character with a roll) + 2 PASS negatives (no tray pre-roll · no tray on native pack).

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| CLAUDE.md "Every Test Suite Needs a Wiring Test" | `mounts the roll surface beside the Fate sheet under Character` — end-to-end through GameBoard `renderWidgetContent`→CharacterWidget→CharacterPanel, not a hand-mounted tray | failing (RED) |
| CLAUDE.md "No Stubbing / dead code worse than no code" | `deletes widgets/FateWidget.tsx` (import.meta.glob) · `WIDGET_REGISTRY no longer defines 'fate'` · `MobileTabView no longer lists a 'fate' tab` · `frees the 'f' hotkey` | failing (RED) |
| TS checklist #6 React/JSX (keys/structure preserved on refactor) | covered by `tsc --noEmit` clean + the full suite render path (no key/JSX regression) | passing |
| TS checklist #8 Test quality (meaningful assertions, no `as any`) | all 10 tests assert concrete DOM/registry state; zero `as any` (props are real now) — self-check below | passing |
| Over-deletion guard (paired test, mirrors fate-native-chrome doctrine) | `KEEPS the 'fate-conflict' widget` · `still surfaces the Fate sheet under Character→Stats` · ruleset-gated negative on native pack | passing |

**Rules checked:** 5 of 5 applicable (the change is a UI refactor — enum/async/security/null TS rules do not apply to a tab-removal + prop-thread).
**Self-check:** 0 vacuous tests. Every test has a concrete assertion (testid presence/absence, registry value, hotkey map, source regex, file-glob membership). No `let _ =`, no `assert(true)`, no always-None checks. The old 118-2/118-7 tests' not-yet-wired type widening (`as` casts) was REMOVED — the props are all real now.

**Handoff:** To Dev (Naomi Nagata) for the GREEN phase — re-home the roll tray under Character→Stats FIRST, then remove the `fate` widget and clean up all dead paths (WidgetId union, WIDGET_REGISTRY, GameBoard availableWidgets/renderWidgetContent/rightGroupOrder, MobileTabView TABS, widgets/FateWidget.tsx). Leave `fate-conflict` and the FateCharacterSheet untouched.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-ui/src/components/CharacterPanel.tsx` — added `fateRoll?: FateRollPayload | null` prop; the Stats tab now mounts `<FateDiceTray roll={fateRoll} ruleset="fate" />` above `FateCharacterSheet` when `fateSheet && fateRoll` (the re-home). Imports `FateDiceTray` + `FateRollPayload`. Also de-staled two comments that referenced the deleted dock FateWidget.
- `sidequest-ui/src/components/GameBoard/GameBoard.tsx` — `character` case now passes `fateRoll={latestFateRoll ?? null}` to CharacterWidget. Removed: `FateWidget` import, the `availableWidgets` `fate` gate, the `renderWidgetContent` `"fate"` case, and `"fate"` from `rightGroupOrder`. Updated the `latestFateRoll` prop doc + the fateSheet comment to the new (re-homed) reality.
- `sidequest-ui/src/components/GameBoard/widgetRegistry.ts` — removed `"fate"` from the `WidgetId` union and the `fate` `WIDGET_REGISTRY` entry (frees hotkey `f`).
- `sidequest-ui/src/components/GameBoard/MobileTabView.tsx` — removed the `fate` TABS entry and the now-unused `Dices` icon import.
- `sidequest-ui/src/components/GameBoard/widgets/FateWidget.tsx` — **deleted** (dead path).

**Order honored:** Re-home first (Step 1), then remove (Step 2) — so the out-of-conflict roll surface is never lost.

**Tests:** 10/10 story tests (GameBoard-fate-tab + GameBoard-fate-roll) GREEN. Full regression: **155/155** across 20 files (entire GameBoard test dir + FatePanel + FatePanel.fateRoll + FateConflictSurface + FateDiceTray). `tsc --noEmit` 0 errors (proves no lingering `fate` WidgetId reference). ESLint clean on all changed files.

**Wiring:** The re-homed tray is reachable end-to-end through GameBoard → CharacterWidget (`{...props}` pass-through) → CharacterPanel → FateDiceTray — exactly what `GameBoard-fate-roll.test.tsx` exercises (the wiring test). The roll uses GameBoard's existing `latestFateRoll` slice (no new prop on GameBoard).

**Scope honored:** `fate-conflict` widget + its own tray untouched (regression-guarded green); `FateCharacterSheet` untouched; `FatePanel` function left intact (now production-unreferenced — logged as a non-blocking follow-up, it has passing tests and is outside the named cleanup scope). No backend/OTEL (cosmetic UI surface relocation, exempt per UI CLAUDE.md).

**Branch:** `feat/126-26-remove-duplicate-fate-tab` (pushed, base `develop`).

**Handoff:** To review (Chrisjen Avasarala / Reviewer).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean (GREEN) | 165/165 tests, tsc + eslint clean, no lingering `fate` WidgetId in src | confirmed 0; noted FatePanel.tsx:142 stale comment (unchanged file → non-blocking) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 6 | confirmed 1 blocking (`as GameBoardProps` cast), confirmed 3 non-blocking (native-pack negative, tray containment, hotkey count → all Improvements), dismissed 2 (MobileTabView ?raw fragility — behavioral test is the strong guard; exact-name match — verified safe) |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 | confirmed 3 blocking (all stale comments in the changed GameBoard.tsx) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 2 | confirmed 1 blocking (rule#1/#8 `as GameBoardProps` cast — corroborates test-analyzer), dismissed 1 (rule#6 `key={i}` at CharacterPanel.tsx:868 — pre-existing, NOT in diff, fixed-length cosmetic pip row, not a reorderable list) |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 4 confirmed blocking (3 stale comments + 1 stale type cast), 4 confirmed non-blocking (Improvements), 3 dismissed (with rationale)

## Reviewer Assessment

**Verdict:** REJECTED

The implementation is *functionally* correct — 165/165 tests green, `tsc --noEmit` clean (proving the `WidgetId` union removal left no dangling reference), eslint clean, the re-home wired genuinely end-to-end, and the dead-path removal complete in code. I am not rejecting the behavior. I am rejecting because this is a **clean-removal story** and the diff leaves the changed file documenting the feature it just deleted as if it still exists. The comment-analyzer (a confirmed dimension) found three stale comments in `GameBoard.tsx`, two of them present-tense descriptions of the removed Fate tab; the rule-checker and test-analyzer independently flagged a stale `as GameBoardProps` cast the sibling test already dropped. Individually these are M/L severity, but "clean up the dead path on removal" is the story's own acceptance scope — wrong docs about the removed path are incomplete cleanup, not cosmetic polish. The fixes are mechanical (comments + one cast), so this is a fast green-rework, not a redesign.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [MEDIUM] `[DOC]` | `fateData` prop doc claims "The Fate tab is dataGated:true and added to availableWidgets only when this is non-null" — present tense for the tab this diff DELETED | `GameBoard.tsx:199-201` | Rewrite to the post-126-26 reality: `fateData` gates the `fateSheet` prop on CharacterPanel and the `fate-conflict` surface; the standalone Fate tab is gone. |
| [MEDIUM] `[DOC]` | "Distinct from the always-available Fate SHEET tab above." — references the removed tab (and it was never "always-available"; it was dataGated) | `GameBoard.tsx:448` | Point to the Character→Stats consolidation instead of a "Fate SHEET tab above." |
| [LOW] `[DOC]` | "Before 118-2 the Fate sheet lived only in a separate dock tab (removed in 126-26)" — historically inverted: 118-2 *added* the dock tab (and the consolidation); the removal boundary is 126-26 | `GameBoard.tsx:602-603` | Reword: the dock tab was added in 118-2, removed in 126-26; before the 118-2 consolidation a Fate PC opening Character saw "No stats available." |
| [LOW] `[TEST]`/`[RULE]` | Stale `as GameBoardProps` cast — leftover from the RED-stub era; `fateData`/`latestFateRoll` are now real `GameBoardProps`, so the cast bypasses assignability. The sibling `GameBoard-fate-tab.test.tsx` already dropped this exact cast (uses `Partial<GameBoardProps>`). | `GameBoard-fate-roll.test.tsx:112` (+ the obsolete "widen-type RED" comment above `BoardOverrides`) | Drop the cast; use `Partial<GameBoardProps>` directly (or `satisfies GameBoardProps`), matching the tab test. |

**Dispatch tags (all 8 accounted for):**
- `[DOC]` — **3 confirmed blocking** (the stale-comment table above). The central finding of this review.
- `[TEST]` — **1 confirmed blocking** (`as GameBoardProps` cast). Non-blocking Improvements: native-pack negative in the tab suite's preservation block; `fate-dice-tray` containment/count assertion in the roll suite; explicit hotkey-count assertion. Dismissed: MobileTabView `?raw` regex "fragility" (the behavioral `queryByRole tab name:"Fate"` test is the authoritative guard, so the raw check is harmless belt-and-suspenders for the file-text path); exact-name match safety (verified — "Fate Conflict" ≠ "Fate", badge aria-label "new Fate Conflict" also no match).
- `[RULE]` — **1 confirmed blocking** (rule#1/#8 cast, corroborates `[TEST]`). Dismissed: rule#6 `key={i}` at `CharacterPanel.tsx:868` — pre-existing, NOT in this diff, and a fixed-length cosmetic ♦-pip row (not a reorderable list), so no reconciliation hazard. tsc-clean confirms no dangling `WidgetId "fate"`.
- `[EDGE]` — subagent disabled. Self-assessed: the only new boundaries are `fateRoll &&` and the enclosing `fateSheet ?` branch; both states are tested (roll present / absent / native pack). No unhandled path.
- `[SILENT]` — disabled. Self-assessed: no error paths introduced; this is render wiring + a removal. No swallowed errors, no silent fallback (the removal fails loud at compile time via the union).
- `[TYPE]` — disabled. Self-assessed + corroborated by rule-checker: new `fateRoll?: FateRollPayload | null` is concretely typed; the only type smell is the test cast (a confirmed finding). `tsc --noEmit` clean proves the `WidgetId` removal is type-sound.
- `[SEC]` — disabled. Self-assessed: `fateRoll` is server-emitted client-mirror state, not user input; no `dangerouslySetInnerHTML`, no `JSON.parse`, no injection surface. `ruleset="fate"` is a literal.
- `[SIMPLE]` — disabled. Self-assessed: the diff is net-negative LOC (a removal); the re-home is minimal (one prop + one Fragment). The one residue is the now-unreferenced `FatePanel` function — Dev filed it as a non-blocking follow-up (correct scope call, accepted).

**Observations (≥5):**
1. `[VERIFIED]` Re-home wired end-to-end — GameBoard `renderWidgetContent("character")` → `CharacterWidget` (`{...props}`) → `CharacterPanel` with `fateRoll={latestFateRoll ?? null}` (GameBoard.tsx:624); tray renders in the Stats tab. Proven by `GameBoard-fate-roll.test.tsx` through the real path. Wiring rule satisfied.
2. `[VERIFIED]` Ruleset gate preserved on the move — the tray sits inside the `fateSheet ?` branch (CharacterPanel.tsx:449); `fateSheet` is null off Fate, so native packs never grow a tray. Confirmed by the roll suite's native-pack negative.
3. `[VERIFIED]` Dead path fully removed in code — `WidgetId` union member, `WIDGET_REGISTRY` entry, `availableWidgets` gate, `renderWidgetContent` case, `rightGroupOrder`, MobileTabView TABS entry + unused `Dices` import, and `FateWidget.tsx` (deleted). `tsc` clean + grep confirm no lingering `fate` WidgetId. Over-deletion guarded: `fate-conflict` and `FateCharacterSheet` intact (tests green).
4. `[DOC]` Dead path NOT fully removed in *docs* — three GameBoard.tsx comments still describe the deleted tab as present (the blocking findings). This is the gap between "works" and "clean removal."
5. `[TEST]`/`[RULE]` Stale `as GameBoardProps` cast in the roll test — double-flagged; the sibling test already fixed it, so this is an inconsistency as well as a smell.
6. `[VERIFIED]` No backend/OTEL needed — UI surface relocation, exempt per `sidequest-ui/CLAUDE.md`.

**### Rule Compliance**
- "Don't Reinvent — Wire Up What Exists" (CLAUDE.md) — COMPLIANT: reuses the existing `latestFateRoll` slice and the `{...props}` CharacterWidget pass-through; no new GameBoard prop, no new Fate-detection.
- "No Stubbing / dead code worse than no code" (CLAUDE.md) — PARTIAL: production dead path removed and proven; residual is the now-unreferenced `FatePanel` function (Dev filed it as a deliberate, tested, out-of-scope follow-up — accepted) and the stale comments (the REJECT findings).
- "No Silent Fallbacks" (CLAUDE.md) — COMPLIANT: the union removal fails loud at compile time; nothing is silently rerouted.
- "Every Test Suite Needs a Wiring Test" (CLAUDE.md, `<critical>`) — COMPLIANT: the roll re-home is exercised end-to-end through GameBoard.
- "Bind the Ruleset, Don't Balance It" (SOUL) — N/A to this UI relocation, but the Fate/native split is respected (the tray is Fate-gated, the native StatsContent path untouched).
- "OTEL on every backend subsystem" — N/A: cosmetic UI surface move, exempt.

**Data flow traced:** `state.latestFateRoll` (server-emitted FATE_ROLL) → GameBoard `latestFateRoll` prop → `character` case `fateRoll={latestFateRoll ?? null}` → CharacterWidget `{...props}` → CharacterPanel; rendered as `<FateDiceTray>` only inside the `fateSheet ?` branch of the Stats tab. Safe: display-only payload, no mutation, no async, no auth surface; Fate-gated by `fateSheet`.

**### Devil's Advocate**
Argue this is broken. First attack: the removal could have orphaned a `WidgetId "fate"` reference somewhere — a `rightGroupOrder` entry, a hotkey handler, a persisted layout key — and rendered a ghost tab or a crash. Checked: `tsc --noEmit` is clean across the project, and `WidgetId[]`/`id: WidgetId` typings would reject any leftover literal; grep finds only `ruleset=='fate'` strings. The union removal is the strongest possible guarantee here, and it holds. Second attack: a player who had the old "Fate" tab pinned/focused in a persisted dockview layout (localStorage `sq-character-panel` or the dockview state) could now hit a dangling panel id on reload and see a blank or a throw. This is the real risk of removing a registered widget — but it's not provable from this diff alone; the dockview restore path filters unknown ids against `availableWidgets`/`WIDGET_REGISTRY` (it already had to, for data-gated widgets that aren't present at mount), so an absent `fate` id is dropped the same way a Fate tab on a native pack always was. Worth a manual smoke test on a save that had the Fate tab open, but not a code defect in this diff. Third attack: the re-homed tray could render in the WRONG place — e.g. for a native pack, or twice (once under Character, once via the conflict surface). The `fateSheet ?` gate blocks the native case (tested), and `fate-conflict` is not in `availableWidgets` unless a conflict is active, so the two trays don't co-render today; the roll test's lack of a containment assertion means a *future* weakening of that gate wouldn't be caught — filed as a non-blocking hardening Improvement, not a present defect. Fourth attack: the stale comments could actively mislead the next engineer into thinking the Fate tab still exists and "fixing" availableWidgets to re-add it — which is exactly why they're blocking findings, not cosmetic. Fifth: removing `Dices` from the lucide import — could it be used elsewhere? eslint no-unused-vars is clean and grep confirms it was the fate tab's only user. None of these rise to a code-correctness defect; the binding constraint remains the documentation cleanup, which the story's own scope requires.

**Verdict rationale:** No Critical/High *correctness* defects — the code works. But on a story whose acceptance is "remove the dead path cleanly," the changed file still documents the removed tab as live (3 confirmed stale comments, 2 present-tense) and carries a stale type cast the sibling test already dropped. That is the cleanup being incomplete, surfaced by a confirmed review dimension. Rejecting for a fast, mechanical green-rework. When in doubt on a cleanup story, finish the cleanup.

**Handoff:** Back to Dev (Naomi Nagata) for a green rework — fix the 4 blocking items (3 GameBoard.tsx comments + the roll-test cast). The non-blocking Improvements (native-pack negative, tray containment, FatePanel/test-comment sweep) are Dev's discretion.

## Dev Assessment — Rework Round 1

**All 4 blocking review findings addressed.** Verified each was genuinely stale before fixing (the feedback was technically sound).

| # | Finding | Fix |
|---|---------|-----|
| B1 `[DOC]` | `GameBoard.tsx` fateData prop doc claimed the (deleted) Fate tab "is dataGated:true and added to availableWidgets" | Rewrote to the post-126-26 reality: fateData drives the `fateSheet` prop (Character→Stats) and the `fate-conflict` gate; the standalone tab is gone. |
| B2 `[DOC]` | `GameBoard.tsx` "Distinct from the always-available Fate SHEET tab above" referenced the removed tab | Now points to the Fate sheet under Character→Stats (standalone tab removed in 126-26). |
| B3 `[DOC]` | `GameBoard.tsx` "Before 118-2 the Fate sheet lived only in a separate dock tab" — historically inverted | Reworded: the dock tab was added in 118-2, removed in 126-26; before the 118-2 consolidation a Fate PC opening Character saw "No stats available." |
| B4 `[TEST]`/`[RULE]` | `GameBoard-fate-roll.test.tsx` stale `BoardOverrides` alias + `as GameBoardProps` cast (sibling tab test already dropped it) | Removed the alias and cast; `renderBoard(overrides: Partial<GameBoardProps>)` with an un-cast spread. tsc confirms it still satisfies GameBoard's props. |

**Non-blocking Improvements:** left for follow-up per the reviewer's "Dev's discretion" — the FatePanel/test-comment sweep (unchanged files, pairs with the FatePanel-unreferenced finding), the native-pack negative in the tab suite, and the tray-containment assertion. Not done now to keep the rework tightly scoped to the blocking items.

**Tests:** 10/10 story tests GREEN; `tsc --noEmit` 0 errors; ESLint clean on changed files.

**Deviations:** none introduced by the rework (comment + test-cleanup only — no behavior change).

**Branch:** `feat/126-26-remove-duplicate-fate-tab` (rework pushed).

**Handoff:** Back to review (Chrisjen Avasarala / Reviewer).

## Subagent Results — Round 2 (rework verification)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean (GREEN) | 10/10 target + 155/155 regression, tsc + eslint clean | confirmed 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | clean | 0 — prior cast finding RESOLVED, imports clean | confirmed 0 |
| 5 | reviewer-comment-analyzer | Yes | clean | 0 new — all 3 prior stale comments RESOLVED (verified accurate) | confirmed 0 |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | 0 — prior rule#1/#8 cast violation RESOLVED, 0 violations | confirmed 0 |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 0 new; all 4 round-1 blocking findings verified RESOLVED

## Reviewer Assessment — Round 2

**Verdict:** APPROVED

The round-1 rejection was for 4 mechanical cleanup items on a clean-removal story; the rework fixed all 4 precisely and verifiably, and introduced nothing new.

**Round-1 blocking findings — all RESOLVED (verified):**
- `[DOC]` GameBoard.tsx fateData prop doc → now accurately describes the post-126-26 reality (fateData drives `fateSheet` + the `fate-conflict` gate; the standalone tab is gone). comment-analyzer confirmed all three claims against the code (high confidence).
- `[DOC]` GameBoard.tsx fate-conflict comment → "Distinct from the Fate SHEET, which lives under Character→Stats (its standalone dock tab was removed in 126-26)." Accurate.
- `[DOC]` GameBoard.tsx fateSheet comment → history corrected: dock tab added in 118-2, removed in 126-26; before the 118-2 consolidation a Fate PC saw "No stats available." Accurate.
- `[TEST]`/`[RULE]` GameBoard-fate-roll.test.tsx → `BoardOverrides` alias + `as GameBoardProps` cast removed; now `Partial<GameBoardProps>` + un-cast spread, matching the sibling tab test. tsc confirms type-soundness. test-analyzer and rule-checker both `clean`. (rule-checker noted a bonus: the old nullable `tab!` non-null assertion is also gone, replaced by a throwing `getByRole` — strictly safer.)

**Dispatch tags (all 8 accounted for):**
- `[DOC]` — clean (3 prior findings resolved, 0 new).
- `[TEST]` — clean (cast resolved, imports consumed, 0 new). Prior non-blocking Improvements remain deferred (native-pack negative, tray containment) — Dev's discretion, not blocking.
- `[RULE]` — clean (cast violation resolved, 0 violations; remaining `as Record<...>` and `?raw` casts justified).
- `[EDGE]` — disabled; self-assessed unchanged from round 1 (the rework is comments + a cast removal, no new branches).
- `[SILENT]` — disabled; no error paths touched.
- `[TYPE]` — disabled; rule-checker confirms `latestFateRoll ?? null` → `fateRoll` is type-sound; no new casts.
- `[SEC]` — disabled; comment/cast-only change, no input surface.
- `[SIMPLE]` — disabled; the rework is net-simpler (removed an alias + a cast).

**Observations (≥5):**
1. `[VERIFIED]` All 3 stale comments now factually correct — comment-analyzer cross-checked each against the live code (availableWidgets has no `fate`; the `character` case threads `fateSheet`; the `fate-conflict` gate is `fateData?.conflict?.active`).
2. `[VERIFIED]` Test cast removed and type-sound — `{ ...defaults, ...overrides }` with `Partial<GameBoardProps>` satisfies GameBoard's props without a cast; tsc clean.
3. `[VERIFIED]` No regression — 155/155 full Fate+GameBoard regression green; eslint clean; no orphaned imports (`FateStatePayload`/`FateRollPayload` still used).
4. `[VERIFIED]` Functional correctness from round 1 stands — the re-home wiring, ruleset gate, and complete dead-path removal were already approved-in-substance; this round only cleaned docs + a cast.
5. `[VERIFIED]` Net-negative complexity — the rework removed a type alias and a cast; nothing added.
6. Non-blocking follow-ups remain captured in Delivery Findings (FatePanel unreferenced + stale comments in unchanged files; two test-hardening Improvements) — not blocking, available for a future sweep.

**### Rule Compliance**
- "No Stubbing / dead code worse than no code" — now FULLY COMPLIANT in the changed surface (the production dead path and its stale docs are gone; the only residue, the unreferenced `FatePanel` function, is an accepted out-of-scope follow-up).
- "Don't Reinvent / No Silent Fallbacks / Every Test Suite Needs a Wiring Test" — COMPLIANT (unchanged from round 1; re-home wired end-to-end, removal fails loud at compile time).
- OTEL — N/A (cosmetic UI surface move).

**Data flow traced:** unchanged from round 1 and re-confirmed — `state.latestFateRoll` → GameBoard `latestFateRoll` → `character` case `fateRoll={latestFateRoll ?? null}` → CharacterWidget → CharacterPanel → `<FateDiceTray>` inside the `fateSheet ?` Stats branch. Fate-gated, display-only, safe.

**### Devil's Advocate**
Argue the rework is broken or the approval premature. First attack: a comment fix could have accidentally changed code — a stray character in a JSDoc, a deleted line of logic. Checked: the diff is purely within comment blocks (lines starting with `*` or `//`) plus the test-only alias/cast removal; tsc and 155 tests pass, so no logic was touched. Second attack: dropping the `as GameBoardProps` cast could have masked a real type error that the cast was legitimately suppressing. Checked: rule-checker reasoned through assignability — `defaults: GameBoardProps` supplies all required fields and `overrides: Partial<GameBoardProps>` only narrows, so the spread is assignable without the cast; tsc agrees (0 errors). The cast was suppressing nothing real. Third attack: the new comments could themselves be subtly wrong (a worse kind of stale). Checked: comment-analyzer verified each of the three rewrites against the actual gate code at high confidence — the claims now match the code exactly. Fourth attack: maybe I'm approving too quickly because it's "just comments," and a real defect slipped in under the cover of a doc rework. Checked: I re-ran all four enabled subagents on the full diff, not just the delta; preflight ran the entire regression suite green. There is no hidden behavioral change. Fifth: the deferred non-blocking Improvements — am I shipping known gaps? Yes, but they are genuine hardening nice-to-haves (a redundant negative, a containment assertion) with the core behavior already proven by three-case coverage; deferring them is proportionate, and they're recorded. Nothing rises to a defect. The rework does exactly what was asked, cleanly.

**Verdict rationale:** All 4 blocking findings resolved and independently verified; 0 new findings across 4 enabled subagents; full regression green; tsc + eslint clean. The clean-removal story is now actually clean — code AND docs. APPROVED.

**Handoff:** To SM (Camina Drummer) for finish-story.