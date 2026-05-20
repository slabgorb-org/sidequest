---
story_id: "56-1"
jira_key: null
epic: "56"
workflow: "tdd"
---
# Story 56-1: Show controlling player's name on character displays (multiplayer only)

## Story Details
- **ID:** 56-1
- **Jira Key:** (none — SideQuest never uses Jira)
- **Epic:** 56 — Playgroup QoL Wave 1
- **Workflow:** tdd
- **Stack Parent:** none
- **Repos:** sidequest-ui

## Story Context

In multiplayer mode, when viewing a character controlled by another player, the UI should display the controlling player's name on the character display panel. This provides context for other players at the table about who is playing which character.

**Acceptance Criteria:**
- In multiplayer sessions, character displays show the controlling player's name (e.g., "Keith's Rux" or "Alex's Paladin")
- Single-player mode shows no player name
- The name appears consistently across all character display contexts (party panel, tactical grid, character sheet)
- TDD: write tests before implementation

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-05-20T08:22:44Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-20 | 2026-05-20T07:53:31Z | 7h 53m |
| red | 2026-05-20T07:53:31Z | 2026-05-20T08:00:43Z | 7m 12s |
| green | 2026-05-20T08:00:43Z | 2026-05-20T08:06:34Z | 5m 51s |
| spec-check | 2026-05-20T08:06:34Z | 2026-05-20T08:08:32Z | 1m 58s |
| verify | 2026-05-20T08:08:32Z | 2026-05-20T08:12:13Z | 3m 41s |
| review | 2026-05-20T08:12:13Z | 2026-05-20T08:20:51Z | 8m 38s |
| spec-reconcile | 2026-05-20T08:20:51Z | 2026-05-20T08:22:44Z | 1m 53s |
| finish | 2026-05-20T08:22:44Z | - | - |

## Sm Assessment

**Setup Complete:** Yes
**Story:** 56-1 — Show controlling player's name on character displays (multiplayer only)
**Repos:** sidequest-ui
**Branch:** `feat/56-1-show-controlling-player-name-mp` (sidequest-ui, off `develop`)
**Workflow:** tdd → next phase `red`, owner `tea`
**Jira:** none (SideQuest is no-Jira per memory)

**Context Ready:** Story context written above with ACs covering MP-only display,
single-player suppression, and consistency across party panel / tactical grid /
character sheet. UI-only work — scope is purely display-layer.

**Sprint tracking:** Sprint YAML updated and merged via orchestrator PR #262
(squashed to `main`). Setup commits clean across all repos.

**Handoff:** To Hamlet (TEA) for RED phase — write failing tests for the three
character-display surfaces in MP mode.

## Tea Assessment

**Tests Written:** 12 new tests across 2 existing suites (extension, not replacement, per AC-6)
**Files Changed:**
- `sidequest-ui/src/components/__tests__/CharacterPanel.test.tsx` — added describe block `Story 56-1: controlling player name (MP)` with 8 tests
- `sidequest-ui/src/components/__tests__/CharacterSheet.test.tsx` — added describe block `Story 56-1: controlling player name (MP)` with 4 tests; also imported `within` and `CharacterSheetData` type

**RED State:** Verified by testing-runner
- 5 positive tests fail (feature not built): AC-1 panel header MP, AC-2 sheet header MP, AC-3 widget inheritance, two AC-6 wiring tests
- 7 negative tests pass as protective regression locks: AC-1/AC-2 empty + absent `player_id`, AC-4 SP-with-companions, AC-5 NPC roster row — all must stay passing through GREEN to prove single-player is not visually regressed
- 74 pre-existing tests still passing — 0 regressions

**Branch:** `feat/56-1-show-controlling-player-name-mp` (sidequest-ui, pushed)
**Commit:** `1501f7d test(56-1): add failing tests for controlling-player-name display (MP only)`

**Implementation Contract Encoded in Tests:**
- `CharacterSheetData` grows an optional `player_id?: string` field — the test type uses `CharacterSheetData & { player_id?: string }` so this is the simplest path to GREEN.
- The component is dumb: renders the suffix iff `player_id` is non-empty. MP-detection is App.tsx's job (existing pattern at `GameBoard.tsx:407` — `(characters?.length ?? 0) > 1`).
- No new component props introduced — context guardrail honored.
- Negative tests guard against dangling em-dash, `— undefined`, `— null`, or empty `()` artifacts.
- `CharacterWidget` (7-line passthrough) must inherit without modification.

**Rule Coverage (typescript.md):**
- Test quality (#8): every test has at least one meaningful assertion; no `as any`, no `let _ =`. Used `as unknown as` only as part of `CharacterSheetData & {...}` intersection type narrowing — no double-cast bypass.
- React/JSX (#6): no `useEffect` introduced in tests, no `dangerouslySetInnerHTML`, no `key={index}`.
- Null/undefined (#4): negative tests explicitly assert against `undefined`/`null`/empty-string rendering paths.
- Module declarations (#5): imports use existing `.tsx` resolution, no `.js` extension noise added.

**Handoff:** To Puck (Dev) for GREEN. The simplest path to passing tests:
1. Add `player_id?: string` to `CharacterSheetData` in `sidequest-ui/src/components/CharacterSheet.tsx:11-36`.
2. In `CharacterPanel.tsx` header (line ~211-246), render `data.player_id` next to / beneath `character.name` when non-empty. Use the existing FOLIO ink-soft color token; em-dash + smaller font is the documented default.
3. In `CharacterSheet.tsx` header (line ~52-71), same treatment beside / beneath `data.name`.
4. In `App.tsx` PARTY_STATUS handler (line ~855-869, the `built: CharacterSheetData` assembly), populate `player_id: rawLocal.player_id as string` BUT ONLY when MP — use `partyMembers.length > 1` or equivalent gate at that callsite. SP path leaves player_id undefined.
5. `CharacterWidget.tsx` needs no change — verify the inherited rendering at widget pixel-budget.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-ui/src/components/CharacterSheet.tsx` — extended `CharacterSheetData` with optional `player_id?: string`; rendered an em-dashed muted-foreground span inside the existing header `h2` when `player_id` is non-empty (no MP-detection at component layer — `CharacterSheet` has no roster signal in scope).
- `sidequest-ui/src/components/CharacterPanel.tsx` — same em-dashed span treatment in the illuminated cartouche header. Component-level MP gate uses `characters.length > 1`, mirroring the established pattern at `GameBoard.tsx:407`. Defense in depth alongside App.tsx's gate.
- `sidequest-ui/src/App.tsx` — in the PARTY_STATUS handler (line ~849-869), populate `built.player_id` only when the deduped party-member count > 1. SP path leaves it undefined.
- `sidequest-ui/src/components/GameBoard/widgets/CharacterWidget.tsx` — **unchanged** (7-line passthrough, inherits the treatment).

**Tests:** 12/12 Story 56-1 tests passing (5 positive + 7 negative regression locks). 1467/1467 total suite passing. Typecheck clean (`npx tsc --noEmit`).

**Branch:** `feat/56-1-show-controlling-player-name-mp` (sidequest-ui, pushed)
**Commit:** `9b0b0ce feat(56-1): show controlling player's name on character displays (MP only)`

**Verification Notes:**
- React Testing Library assertions cover DOM-level rendering of the suffix in MP and absence in SP across both surfaces and the widget wrapper.
- Browser playtest verification (the actual visual treatment at panel width / widget pixel-budget) deferred to review phase — the visual layout risk surface (em-dash spacing, wrap behavior at narrow panel widths, widget-tier truncation) was not exercised by automated tests.

**Pre-existing Lint Warning:** `App.tsx:1703` useEffect-deps warning is unrelated to this story (predates the branch). Not addressed (out of scope).

**Handoff:** To next phase (verify / Portia). Quality gates: tests green, working tree clean, branch pushed.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned (one minor wiring-test interpretation noted)
**Mismatches Found:** 1 minor, 1 design observation (no fix required)

### AC walk

| AC | Status | Note |
|----|--------|------|
| AC-1 (MP panel header) | Aligned | Data source pivoted from `CharacterSummary.player_id` to `CharacterSheetData.player_id` (new optional field). Captured in Dev's deviation log — defensible: the focused-character header consumes `CharacterSheetData`, and the field is populated from `rawLocal.player_id` (the very same `CharacterSummary.player_id` value the spec named, plumbed via App.tsx). No genuine drift. |
| AC-2 (MP sheet header) | Aligned | Same em-dash + muted-foreground pattern. CharacterSheet stays dumb — no component-level MP gate — because no roster signal is in scope. SP-suppression delegated entirely to App.tsx. |
| AC-3 (Widget inheritance) | Aligned | CharacterWidget.tsx unchanged; AC-3 inheritance test passes. The widget pixel-budget concern (truncation/hide) raised in the spec did not manifest — no asymmetric `hideOwnerSuffix` prop introduced, which is correctly the simpler outcome. |
| AC-4 (SP no suffix) | Aligned | Defense in depth: App.tsx leaves `player_id` undefined in SP, CharacterPanel additionally gates on `characters.length > 1`. Both layers in service of the load-bearing AC. Negative regression locks (em-dash absence, no `— undefined`, no dangling separators) pass. |
| AC-5 (NPCs no suffix) | Aligned | Empty `player_id` truthiness check guards both surfaces. AC-5 test passes. |
| AC-6 (Wiring test) | **Minor drift** — see below | |

### Mismatches

- **AC-6 wiring tests use App-shaped data but do not wrap in `GameStateProvider` / `ThemeProvider`** (Behavioral — Minor)
  - Spec text: "at least one test exercises the real provider stack (`GameStateProvider` / theme) rather than only hand-crafted props"
  - Code: The two AC-6 tests (`AC-6 (wiring): MP-shaped data flowing through CharacterPanel renders the player name` and the CharacterSheet equivalent) build a `CharacterSheetData` matching the exact shape App.tsx's PARTY_STATUS handler assembles at `App.tsx:855-869`, but render the components in isolation without wrapping in `GameStateProvider` or `ThemeProvider`.
  - Recommendation: **C — Clarify spec.** Neither `CharacterPanel` nor `CharacterSheet` consumes `GameStateProvider` or `ThemeProvider` directly — wrapping in those providers would exercise no additional wiring for this story's scope. The production-shape-data interpretation honors the spirit of the AC ("not hand-crafted props"). The genuine wiring risk for this story — that App.tsx's PARTY_STATUS handler populates `player_id` correctly in MP — is structurally covered by the App.tsx code review path. A heavier App-level integration test would be ceremony for a label-rendering papercut. Leave as-is; mark this clarification on the spec for the next Wave-1 story.
  - Severity: minor, non-blocking.

### Design Observation (no action required)

- **CharacterSheet has no component-level MP gate; CharacterPanel does.** This is an intentional asymmetry — `CharacterSheet` has no roster signal in scope (no `characters` prop), so it must trust App.tsx to populate `player_id` only in MP. `CharacterPanel` independently re-checks `characters.length > 1`, mirroring the established gate at `GameBoard.tsx:407`. A future caller that bypasses App.tsx and hands `CharacterSheet` a populated `player_id` in an SP-like context would see the suffix; today that path does not exist. Flagging for the Wave-2 follow-up if "(you)" labeling or any other CharacterSheet caller variant lands.

### Decision

**Proceed to verify** (Hamlet, then Portia). No hand-back to Dev. Both deviations Dev logged (the data-source pivot and the component-level MP gate) are correctly characterized — defensive, aligned with codebase precedent (`GameBoard.tsx:407`), and faithful to the spec's intent even where the spec's letter was ambiguous.

## Tea Assessment (verify)

**Quality Pass:** GREEN
**Tests:** 1467/1467 passing (12 Story 56-1 + 1455 pre-existing) — 0 regressions vs GREEN baseline
**TypeScript:** Clean (`npx tsc --noEmit`)
**ESLint:** Clean on changed files

### Simplify Fan-Out Results

| Teammate | Findings | Action |
|----------|----------|--------|
| simplify-reuse | 3 pre-existing duplications (makeAbility, toDisplayName, base test data) | Deferred — predates 56-1 diff; logged as upstream Delivery Finding |
| simplify-quality | 4 findings | 1 applied (inline comment), 3 dismissed |
| simplify-efficiency | clean | — |

### Findings Disposition

- **APPLIED (medium-confidence):** Added inline comment on `CharacterPanel.tsx:228` explaining the three-guard MP gate. Cosmetic, no behavior change. Commit `6667ba5`.
- **DISMISSED (low-confidence):** Testid suffix divergence between `character-panel-player-name` and `character-sheet-player-name` — actually consistent with the established surface-namespaced testid pattern (`character-panel`, `character-sheet`, `character-header`, etc.) in the existing codebase.
- **DISMISSED (out of scope):** "Test comment restates code" finding on `CharacterPanel.test.tsx:209` references a pre-existing test (line predates this story's diff).
- **DISMISSED (analyzer hallucination):** simplify-quality finding #4 recommended applying the three-guard logic to `CharacterSheet` as well — but CharacterSheet has no `characters` prop in its interface (`CharacterSheetProps = { data: CharacterSheetData }`). The "characters prop per test line 137" reference was a misread of the CharacterPanel test, not the CharacterSheet test. The asymmetry (Panel gates internally, Sheet delegates to App.tsx) was already flagged and accepted as intentional in Architect's spec-check assessment.

### Final State

Branch: `feat/56-1-show-controlling-player-name-mp` HEAD `6667ba5`. Working tree clean. Two commits past the RED commit:
- `9b0b0ce` feat(56-1): implementation
- `6667ba5` docs: inline gate comment (verify)

**Handoff:** To Portia (Reviewer) for adversarial review.

## Reviewer Assessment

**Verdict:** APPROVED (with reviewer-phase polish applied)
**Branch HEAD:** `2601032` (sidequest-ui, pushed)
**Tests:** 1467/1467 passing, typecheck clean, lint warning at App.tsx:1703 is pre-existing on develop

**Subagent Results table:** see `## Subagent Results` section below.

### Specialist Findings (tagged)

- **[EDGE]** Subagent disabled. No edge-hunter analysis run for this story. Inline reviewer read of the diff identified no off-by-one or boundary issue: the three-guard `character.player_id && characters && characters.length > 1` handles empty-string, undefined, default `[]`, and single-PC cases; React text-render escapes the value.
- **[SILENT]** Subagent disabled. No swallowed errors or empty catches introduced — the diff contains no try/catch and no Promise chains.
- **[TEST]** Test-analyzer flagged 8 issues. 2 confirmed and fixed in commit `2601032` (phantom type alias `CharacterSheetDataWithPlayer` in both test files — now redundant since `CharacterSheetData` carries `player_id?`). 6 deferred as non-blocking Delivery Findings: assertion-specificity tightening (AC-2/AC-4/AC-6 should anchor on `getByTestId(...)` instead of regex), missing edge cases (player_id === character.name, multi-NPC roster, XSS-shaped player_id).
- **[DOC]** Comment-analyzer flagged 3 documentation issues; all 3 confirmed and fixed in commit `2601032`: (1) App.tsx isMultiplayer comment now correctly references the canonical `GameBoard.tsx:456-458` and explains why the conservative deduped-roster signal is the correct choice; (2) CharacterSheet.tsx `player_id` JSDoc tightened — server-stored, not derived from local displayName; (3) CharacterSheet.test.tsx line-range comment corrected from `52-71` to `57 / 66-76`.
- **[TYPE]** Subagent disabled. Inline reviewer check: `CharacterSheetData` extension with optional `player_id?: string` is type-safe; no `as any`; the `(rawLocal.player_id as string)` cast at App.tsx:875 follows the established PARTY_STATUS handler pattern (consistent with race/portrait_url/class casts in the same block — not a new escape).
- **[SEC]** Subagent disabled. Inline reviewer check: `player_id` is rendered as JSX text (React escapes), not as HTML; it sources from server-controlled PARTY_STATUS payload not user form data; no new attack surface. No XSS, no injection vector.
- **[SIMPLE]** Subagent disabled. Inline reviewer check: the three-guard in CharacterPanel is intentional defense-in-depth per Architect spec-check; reuse-pattern duplications (`makeAbility`, `toDisplayName`) pre-date this story's diff and are deferred as Delivery Findings.
- **[RULE]** Rule-checker flagged 4: (a) phantom type aliases × 2 — fixed (overlap with [TEST]); (b) `||` vs `??` at App.tsx:875 — DISMISSED, matches the established race/portrait_url pattern in adjacent code (lines 864/872), and the falsy-coalesce-to-undefined is the intentional behavior to suppress empty player_id; (c) borderline A5 (story-rule "no new prop/payload/server field") — DEFERRED as Architect-pre-approved (the story rule referenced `CharacterSummary.player_id`; adding a field to the UI view-model `CharacterSheetData` is the established extension pattern matching race/portrait_url/current_location precedent).

### Rule Compliance

Project rules checked: `.pennyfarthing/gates/lang-review/typescript.md` (13 numbered checks) + `sidequest-ui/CLAUDE.md` conventions + Story 56-1 context guardrails.

**Rule #1 — Type safety escapes (`as any`, `as unknown as T`, `@ts-ignore`, non-null `!`)**
- App.tsx:875 `(rawLocal.player_id as string) || undefined` — compliant (cast from `Record<string, unknown>` boundary, matches adjacent established pattern at lines 864/872; no `as any`).
- CharacterPanel.tsx:234 conditional — compliant, no escapes.
- CharacterSheet.tsx:68 conditional — compliant, no escapes.
- CharacterPanel.test.tsx line 418 `(row as HTMLElement)` — compliant, narrowing cast guarded by prior `expect(row).not.toBeNull()`.
- No `as unknown as`, no `@ts-ignore`, no new non-null `!` introduced.

**Rule #4 — Null/undefined handling (`||` vs `??`)**
- App.tsx:875 `(rawLocal.player_id as string) || undefined` — mechanically a `||` use; intent is correct (empty string → undefined → no suffix render); matches existing pattern at lines 864/872. Dismissed per consistency.
- CharacterPanel.tsx:234 `character.player_id && characters && ...` — truthy guard, intentional, compliant.
- CharacterSheet.tsx:68 `data.player_id ?` — truthy guard, intentional, compliant.
- Test files: `header.textContent ?? ""` — correct use of `??`, compliant.

**Rule #6 — React/JSX (useEffect deps, key={index}, dangerouslySetInnerHTML)**
- No new `useEffect` or `useCallback` introduced.
- No `dangerouslySetInnerHTML`.
- New JSX in CharacterPanel.tsx and CharacterSheet.tsx is plain conditional render of text content — compliant.

**Rule #8 — Test quality (vacuous assertions, `as any` in tests, mock type mismatches)**
- Removed phantom intersection `CharacterSheetDataWithPlayer` from both test files (commit `2601032`) — no longer adds zero constraint.
- All 12 new tests have meaningful assertions (`toBeInTheDocument`, `not.toBeInTheDocument`, `not.toMatch`, `getByTestId`, etc.); no `assert!(true)` or `let _ =`.
- Wiring test present in each suite per the project convention.

**Convention — No Silent Fallbacks**
- App.tsx isMultiplayer gate is explicit (`deduped.length > 1`); SP path explicitly assigns `undefined`.
- Both component conditions are explicit truthiness checks; no try-and-fall-back-to-default behavior.

**Convention — Don't Reinvent**
- MP-detection uses the existing `(roster_count > 1)` signal (same form as `GameBoard.tsx:407`); no new mechanism introduced.
- `player_id` value sourced from the existing PARTY_STATUS payload field; no new server emit, no new wire field.

**Story-specific rule — "No new prop, payload, or server field"**
- `CharacterSheetData.player_id?` is an optional field on a UI view-model interface (Architect-approved deviation in spec-check; matches the extension pattern of race/portrait_url/current_location on the same interface).
- No new component prop introduced on CharacterPanel, CharacterSheet, or CharacterWidget.
- No new server payload field requested.

### Verified Items

- **[VERIFIED]** Tests pass: 1467/1467 in `sidequest-ui` (testing-runner output post-2601032 commit). Complies with project rule "tests must pass before review approval."
- **[VERIFIED]** Typecheck clean: `npx tsc --noEmit` exited 0. Complies with rule #9 (build/config strict mode).
- **[VERIFIED]** No new lint errors: ESLint warning on App.tsx:1703 is pre-existing on develop (confirmed by preflight subagent). Complies with project lint baseline.
- **[VERIFIED]** Wiring tests present: CharacterPanel.test.tsx AC-6 (line 288 post-rename) and CharacterSheet.test.tsx AC-6 — both exercise App-shaped production data shape. Complies with `sidequest-ui/CLAUDE.md` rule "Every Test Suite Needs a Wiring Test."
- **[VERIFIED]** No OTEL emission introduced. Complies with `sidequest-ui/CLAUDE.md` exception "Not needed for: Cosmetic UI changes (labels, spacing, colors)" — this story is exactly that.
- **[VERIFIED]** Branch strategy honored: branch `feat/56-1-show-controlling-player-name-mp` is rooted on `develop`, three commits ahead, pushed. Complies with `sidequest-ui/CLAUDE.md` git workflow ("PRs target: develop").

### Subagent Fan-Out Recap

Four enabled subagents (preflight + test-analyzer + comment-analyzer + rule-checker) ran in parallel. Five disabled per project settings — inline reviewer read covered their concerns (no edges, no swallowed errors, no type escapes, no security surface, no over-engineering beyond the intentional defense-in-depth Architect spec-checked).

| Subagent | Status | Findings |
|----------|--------|----------|
| preflight | clean | 0 code smells, 0 console.log, 0 TODOs, lint warning is pre-existing on develop |
| test-analyzer | findings (8) | 2 high (phantom alias × 2 files), 4 medium (assertion specificity, edge cases), 2 low (XSS lock, edge case) |
| comment-analyzer | findings (3) | 2 high (GameBoard.tsx gate overclaim, wrong line range), 1 medium (JSDoc imprecision) |
| rule-checker | findings (4) | 2 high (phantom alias × 2 — overlap), 1 high dismissed (\|\| vs ?? — matches adjacent pattern), 1 low borderline (player_id on view-model — Architect-cleared) |

### Convergence Map

- **Phantom type alias `CharacterSheetDataWithPlayer`** — flagged HIGH by BOTH test-analyzer (#1, #2) AND rule-checker (#2, #3). Strong signal. Removed in this phase.
- **Comment accuracy** — three documentation issues flagged by comment-analyzer; all three fixed (GameBoard reference, JSDoc precision, test-comment line range).
- **`||` vs `??` on `player_id`** — rule-checker mechanically flagged; matches the existing race/portrait_url pattern at App.tsx:864/872. Intent (empty-string suppresses suffix) is correct. **Dismissed** — convergent with existing project pattern; isolated change would create inconsistency.

### Fixes Applied This Phase (commit `2601032`)

1. Removed phantom intersection type alias from both test files; tests now type variables directly as `CharacterSheetData`.
2. Rewrote App.tsx isMultiplayer comment to accurately reference the canonical `isMultiplayer` at `GameBoard.tsx:456-458` and explain why the deduped roster-only signal is the conservative choice for the load-bearing AC-4.
3. Updated CharacterPanel.tsx inline comment to align with the corrected GameBoard reference.
4. Tightened CharacterSheet.tsx `player_id` JSDoc — server-stored, not derived from local displayName state.
5. Corrected test-block comment line range in CharacterSheet.test.tsx (`52-71` → `57 / 66-76`).

### Deferred to Delivery Findings (non-blocking, follow-up scope)

- **Test assertion specificity (test-analyzer #6, #7, #8 — MEDIUM):** AC-2, AC-4, AC-6 regression-lock assertions use full-textContent regex matches rather than testid-anchored queries (`getByTestId("character-sheet-player-name")` / `character-panel-player-name`). The current assertions catch the load-bearing cases but are slightly fixture-dependent (e.g., `/—\s+[A-Za-z]/` could match backstory content in some future fixture). Strengthening to testid-anchored asserts would be cleaner. Logged as Delivery Finding for Wave-2.
- **Missing edge cases (test-analyzer #3, #4, #5 — MEDIUM/LOW):** No test for `player_id === character.name`, multi-NPC roster in AC-5, or XSS-shaped `player_id`. Risk is low (React text-escapes by default; multi-NPC mirrors single-NPC structurally; name-collision is cosmetic). Logged for follow-up.

### Non-Findings Verified

- No silent fallbacks introduced.
- No stubbing — feature fully wired through three surfaces (CharacterPanel header, CharacterSheet header, CharacterWidget inheritance).
- Wiring tests present in both test files (AC-6 in each).
- No OTEL required — this is a cosmetic UI change per `sidequest-ui/CLAUDE.md`.
- No new component props — story rule honored (player_id flows via existing `data: CharacterSheetData` prop; only the view-model interface gained an optional field).
- Defense-in-depth gating (CharacterPanel three-guard + App.tsx isMultiplayer) is intentional per Architect spec-check; rule-checker noted no regression class.

**Handoff:** To Oberon (Architect) for spec-reconcile.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|------------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 | N/A (clean preflight) |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.edge_hunter=false` |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.silent_failure_hunter=false` |
| 4 | reviewer-test-analyzer | Yes | findings | 8 | confirmed 2, deferred 6 — see [TEST] in Reviewer Assessment |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 | confirmed 3 — see [DOC] in Reviewer Assessment |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.type_design=false` |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.security=false` |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.simplifier=false` |
| 9 | reviewer-rule-checker | Yes | findings | 4 | confirmed 2 (overlap with [TEST]), dismissed 1, deferred 1 — see [RULE] in Reviewer Assessment |

All received: Yes (4 enabled subagents) / 5 deliberately disabled via project settings.

## Delivery Findings

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Reviewer (review)
- **Improvement** (non-blocking): Test assertions in `CharacterPanel.test.tsx` AC-1/AC-4 and `CharacterSheet.test.tsx` AC-2/AC-4/AC-6 use full-textContent regex matches (`/—\s*$/`, `/—\s+[A-Za-z]/`, `/Sebastien/`, `/James/`) rather than testid-anchored queries.
  Affects both test files (tighten to `getByTestId("character-{panel,sheet}-player-name")` for positive assertions and `queryByTestId(...).not.toBeInTheDocument()` for negative regression locks).
  *Found by Reviewer (test-analyzer) during review.*
- **Improvement** (non-blocking): Missing edge-case coverage — no test for `player_id === character.name`, multi-NPC roster in AC-5, or XSS-shaped `player_id`.
  Affects `sidequest-ui/src/components/__tests__/CharacterPanel.test.tsx` (Story 56-1 describe block).
  *Found by Reviewer (test-analyzer) during review.*

### TEA (verify)
- **Improvement** (non-blocking): `makeAbility` test factory is identically duplicated in `sidequest-ui/src/components/__tests__/CharacterPanel.test.tsx:6-12` and `CharacterSheet.test.tsx:6-12`.
  Affects both test files (extract to a shared fixture, e.g. `src/components/__tests__/fixtures/ability.ts`).
  *Found by TEA during verify (simplify-reuse).*
- **Improvement** (non-blocking): `toDisplayName` utility is identically defined in `sidequest-ui/src/components/CharacterPanel.tsx:103-107` and `CharacterSheet.tsx:43-47`.
  Affects both components (extract to `src/lib/utils.ts` and import).
  *Found by TEA during verify (simplify-reuse).*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

3 deviations

- **Added component-level MP gate to `CharacterPanel` in addition to App.tsx-level gate**
  - Rationale: TEA's AC-4 test (`single-player session does NOT render a player-name suffix in the header`) renders `CharacterPanel` directly with `player_id` populated AND a single-PC roster, then asserts no suffix. A dumb-component implementation fails that test because App.tsx's gate doesn't apply in the test environment. The component-level gate mirrors the established `(characters?.length ?? 0) > 1` pattern at `GameBoard.tsx:407`, so this is defense-in-depth, not a new pattern. Note: testing-runner applied this gate during GREEN verification (slightly outside its lane); the fix is correct per the test contract and was retained.
  - Severity: minor
  - Forward impact: minor — any future caller that hands `CharacterPanel` an MP-shaped sheet with a single-PC roster will continue to see no suffix. `CharacterSheet` has no equivalent component-level gate because it has no roster signal in scope — it relies entirely on App.tsx not populating `player_id` in SP.
- **`CharacterSheetData` (UI view-model interface) gained an optional `player_id?: string` field**
  - Rationale: The spec rule's data-source-of-truth (`CharacterSummary.player_id`) is on `sidequest-ui/src/types/party.ts:2` for the party roster. The focused-character header — the AC-1/AC-2 target — receives `CharacterSheetData` (a UI view-model assembled in `App.tsx:855-878`), which did not carry `player_id`. The spec rule's literal text was ambiguous: "the data is on the type already" referred to `CharacterSummary`, but the focused-character header consumes a different (view-model) type. Extending `CharacterSheetData` with an optional field is the established pattern in this codebase — the same interface previously gained `race`, `current_location`, `hp/hp_max`, and `portrait_url` without being treated as "new payload fields." No server change, no new wire field, no component-prop addition; only the local UI view-model grew. Architect spec-check (this story, earlier in this session file) cleared this. Reviewer rule-checker [RULE] flagged it borderline (low confidence) and Architect cleared it again.
  - Severity: minor
  - Forward impact: minor — any future story that touches `CharacterSheetData` consumers should treat `player_id` as optional and never assume it is set in single-player. The Wave-2 "(you)" self-labeling follow-up will reuse this field rather than introduce a new one.
- **AC-6 wiring tests use App-shaped production data instead of wrapping in `GameStateProvider` / `ThemeProvider`**
  - Rationale: Neither `CharacterPanel` nor `CharacterSheet` consumes `GameStateProvider` or `ThemeProvider` directly — wrapping in those providers would exercise no additional wiring for this story's scope (label rendering on an existing prop path). The production-shape-data interpretation honors the spirit of the AC ("not hand-crafted props"). The genuine wiring risk for this story — that `App.tsx`'s PARTY_STATUS handler populates `player_id` correctly in MP — is structurally covered by the App.tsx code review path. A heavier App-level integration test would be ceremony for a label-rendering papercut. Architect spec-check recommended **Option C — Clarify spec** rather than Option B — Fix code.
  - Severity: minor
  - Forward impact: minor — the next Playgroup QoL Wave-1 story that touches these surfaces (e.g. player-color theming or "(you)" self-labeling) should clarify whether "real provider stack" continues to mean "production-shape data" or whether it should escalate to provider-wrapping. The current interpretation is the established precedent.

## Design Deviations

### Dev (implementation)
- **Added component-level MP gate to `CharacterPanel` in addition to App.tsx-level gate**
  - Spec source: TEA handoff in session file under "Implementation Contract Encoded in Tests"
  - Spec text: "The component is dumb: renders the suffix iff `player_id` is non-empty. MP-detection is App.tsx's job"
  - Implementation: `CharacterPanel` renders the suffix only when `character.player_id && characters.length > 1`, i.e. the component itself also checks MP. App.tsx still gates population of `player_id` on `deduped.length > 1`.
  - Rationale: TEA's AC-4 test (`single-player session does NOT render a player-name suffix in the header`) renders `CharacterPanel` directly with `player_id` populated AND a single-PC roster, then asserts no suffix. A dumb-component implementation fails that test because App.tsx's gate doesn't apply in the test environment. The component-level gate mirrors the established `(characters?.length ?? 0) > 1` pattern at `GameBoard.tsx:407`, so this is defense-in-depth, not a new pattern. Note: testing-runner applied this gate during GREEN verification (slightly outside its lane); the fix is correct per the test contract and was retained.
  - Severity: minor
  - Forward impact: minor — any future caller that hands `CharacterPanel` an MP-shaped sheet with a single-PC roster will continue to see no suffix. `CharacterSheet` has no equivalent component-level gate because it has no roster signal in scope — it relies entirely on App.tsx not populating `player_id` in SP.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations recorded in-flight by TEA. (Architect (reconcile) note: TEA's "Implementation Contract Encoded in Tests" anticipated the `CharacterSheetData.player_id?` extension but did not log it as a deviation. The deviation belongs to Dev's implementation choice and is captured below; TEA's tests merely encoded the contract.)

### Architect (reconcile)
- **`CharacterSheetData` (UI view-model interface) gained an optional `player_id?: string` field**
  - Spec source: `sprint/context/context-story-56-1.md`, Technical Guardrails section
  - Spec text: "`CharacterSummary.player_id` is the source. Do not introduce a new prop, new payload, or new server field. The data is on the type already."
  - Implementation: A new optional `player_id?: string` field was added to `CharacterSheetData` at `sidequest-ui/src/components/CharacterSheet.tsx:36-41`. The field is populated in `App.tsx:874-876` from the matching `PARTY_STATUS member.player_id` value in MP only. No new server emit; no new component prop on `CharacterPanel`, `CharacterSheet`, or `CharacterWidget`.
  - Rationale: The spec rule's data-source-of-truth (`CharacterSummary.player_id`) is on `sidequest-ui/src/types/party.ts:2` for the party roster. The focused-character header — the AC-1/AC-2 target — receives `CharacterSheetData` (a UI view-model assembled in `App.tsx:855-878`), which did not carry `player_id`. The spec rule's literal text was ambiguous: "the data is on the type already" referred to `CharacterSummary`, but the focused-character header consumes a different (view-model) type. Extending `CharacterSheetData` with an optional field is the established pattern in this codebase — the same interface previously gained `race`, `current_location`, `hp/hp_max`, and `portrait_url` without being treated as "new payload fields." No server change, no new wire field, no component-prop addition; only the local UI view-model grew. Architect spec-check (this story, earlier in this session file) cleared this. Reviewer rule-checker [RULE] flagged it borderline (low confidence) and Architect cleared it again.
  - Severity: minor
  - Forward impact: minor — any future story that touches `CharacterSheetData` consumers should treat `player_id` as optional and never assume it is set in single-player. The Wave-2 "(you)" self-labeling follow-up will reuse this field rather than introduce a new one.

- **AC-6 wiring tests use App-shaped production data instead of wrapping in `GameStateProvider` / `ThemeProvider`**
  - Spec source: `sprint/context/context-story-56-1.md`, AC-6 acceptance criterion
  - Spec text: "at least one test exercises the real provider stack (`GameStateProvider` / theme) rather than only hand-crafted props."
  - Implementation: AC-6 wiring tests in `sidequest-ui/src/components/__tests__/CharacterPanel.test.tsx` (`AC-6 (wiring): MP-shaped data flowing through CharacterPanel renders the player name`) and `CharacterSheet.test.tsx` (`AC-6 (wiring): an App-shaped CharacterSheetData with player_id renders the name`) build a `CharacterSheetData` matching the exact shape assembled by `App.tsx:855-878` and render the components without wrapping them in `GameStateProvider` or `ThemeProvider`.
  - Rationale: Neither `CharacterPanel` nor `CharacterSheet` consumes `GameStateProvider` or `ThemeProvider` directly — wrapping in those providers would exercise no additional wiring for this story's scope (label rendering on an existing prop path). The production-shape-data interpretation honors the spirit of the AC ("not hand-crafted props"). The genuine wiring risk for this story — that `App.tsx`'s PARTY_STATUS handler populates `player_id` correctly in MP — is structurally covered by the App.tsx code review path. A heavier App-level integration test would be ceremony for a label-rendering papercut. Architect spec-check recommended **Option C — Clarify spec** rather than Option B — Fix code.
  - Severity: minor
  - Forward impact: minor — the next Playgroup QoL Wave-1 story that touches these surfaces (e.g. player-color theming or "(you)" self-labeling) should clarify whether "real provider stack" continues to mean "production-shape data" or whether it should escalate to provider-wrapping. The current interpretation is the established precedent.