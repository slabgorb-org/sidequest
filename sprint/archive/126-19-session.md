---
story_id: "126-19"
jira_key: ""
epic: "126"
workflow: "tdd"
---
# Story 126-19: [FATE/UX] Suppress residual native chrome on Fate characters (HP/level/class across 5 surfaces) + remove the duplicate Fate dock tab

## Story Details
- **ID:** 126-19
- **Jira Key:** (none)
- **Workflow:** tdd
- **Epic:** 126 — Fate Core playtest follow-ups
- **Stack Parent:** none

## Scope

This is a pure UI-surface fix addressing two [BUG] findings from sq-playtest-pingpong 2026-06-19 (screenshot 150-1-005-game-opening, pulp_noir/annees_folles PC 'Roy Calder'). Both touch the Character/Party/dock UI region and share the orphaned-native-model root.

### PART A — Native HP/level/class leak (5 surfaces)
Under a Fate ruleset there is no HP, no level, no class (harm = Stress + Consequences only). Leaks observed:
1. Character header 'Lv 1' + 'HP 10/10' pill
2. Character body HP in TWO redundant forms — 'HP/Vitality HP 10/10' pill AND a row of 10 diamond pips
3. Party panel 'Roy Calder (YOU) — Detective Lv.1 · HP 10/10' (native class 'Detective' = class_hint + level + HP)
4. Bottom action/input bar 'HP 10/10' pill

**Critical constraint:** Suppression MUST BRANCH on the bound ruleset. HP/level/class are legitimate under Worlds Without Number (ADR-142, ADR-143 bind-don't-balance). Never delete globally.

### PART B — Duplicate 'Fate' dock tab (regression)
Right dock shows a standalone 'Fate' tab rendering the same sheet (Skills/HC/Trouble/Aspects/Stress/Consequences/Fate Points) already under Character→Stats. The consolidation partially landed (Character tab has correct Stats/Abilities/Status) but the separate Fate tab was not removed. Remove the standalone Fate dock tab; the Fate sheet lives ONLY in Character.

## Acceptance Criteria

1. Under a Fate binding, the Character header/body, Party panel, and action bar show NO HP, NO level, NO class; harm surfaces as Stress + Consequences only.
2. Suppression branches on the bound ruleset: a WN-bound pack still shows HP/level/class (no global deletion). Test both a Fate pack and a WN pack.
3. Body HP de-duplicated: the pips+pill double-render is gone for Fate (it was both native AND redundant).
4. The standalone 'Fate' dock tab is removed; the Fate sheet renders only under Character (Stats=skills+aspects, Abilities=stunts, Status=stress/consequences); no information lost.

## Related ADRs & Context
- **ADR-144** — Fate Core Binding Replaces the Native Ruleset (the bind-don't-balance architecture)
- **ADR-142** — Without Number Core Extraction (WN rules as a baseline)
- **ADR-117** — Pluggable Ruleset Module System (the runtime dispatch mechanism)
- **ADR-143** — A Without-Number Binding Replaces the Native Ruleset (mechanical replacement, not layering)

Key insight: Ruleset branching is the core design constraint. The UI must query the bound ruleset (pack.rules.ruleset) and conditionally suppress native surfaces that are replaced by Fate ruleset mechanics.

## Sm Assessment

**Routing:** Phased TDD, single repo (`sidequest-ui`). Setup → red (TEA) → green (Dev) → review (Reviewer) → finish (SM). Handing to TEA for the RED phase.

**Why TDD (not trivial):** Kept the YAML-assigned `tdd` (5pt). This is not a trivial chore — it has a hard correctness invariant (ruleset-branching) that must be locked by failing tests before any code moves, exactly what TDD protects.

**The load-bearing constraint for TEA — do not let a global-deletion fix pass.** The naive fix ("hide HP/level/class") is *wrong* and would satisfy a sloppy test. Suppression must BRANCH on the bound ruleset (ADR-144/143/117). So the RED suite MUST be two-sided:
- Fate-bound pack (pulp_noir/annees_folles, PC like 'Roy Calder') → asserts HP, level, and class_hint are ABSENT on all surfaces; harm shows as Stress + Consequences.
- WN-bound pack → asserts HP/level/class are STILL PRESENT (regression guard against global deletion).
A test that only checks the Fate side is insufficient and would green-light an ADR-violating fix.

**Surface coverage (PART A) — five distinct render sites, each needs an assertion:** (1) Character header Lv+HP pill, (2) Character body — both the HP/Vitality pill AND the diamond-pip row (double-render must both vanish for Fate), (3) Party panel `class_hint · Lv · HP`, (4) bottom action/input bar HP pill. Don't fold these into one assertion — they're separate components and a partial fix is the likely failure mode.

**PART B — dock dedup:** assert the standalone 'Fate' dock tab is gone and the Fate sheet renders only under Character (Stats/Abilities/Status). Verify no information is lost in the consolidation.

**Wiring test required (project rule):** include at least one test proving the suppression reads the *actual bound ruleset* from real state (pack.rules.ruleset path), not a mocked-in-isolation prop — otherwise the branch could be dead in production.

**Open question for TEA/Dev to surface as a Delivery Finding if hit:** confirm where the UI learns the bound ruleset (state mirror field vs. derived). If that signal isn't already reaching these components, that's a green-phase wiring task, not a CSS tweak — flag it.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-19T12:13:45Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-19T10:46:46Z | 2026-06-19T10:50:16Z | 3m 30s |
| red | 2026-06-19T10:50:16Z | 2026-06-19T11:58:17Z | 1h 8m |
| green | 2026-06-19T11:58:17Z | 2026-06-19T12:03:48Z | 5m 31s |
| review | 2026-06-19T12:03:48Z | 2026-06-19T12:13:45Z | 9m 57s |
| finish | 2026-06-19T12:13:45Z | - | - |

## TEA Assessment

### Red Phase (test writing)

**Tests Required:** Yes
**Reason:** Hard ruleset-branching correctness invariant — exactly what TDD locks before code moves.

**Scope decision (Keith, 2026-06-19):** This story is reduced to **PART A only** (native chrome suppression). **PART B** (remove the standalone Fate dock tab) is **split to a follow-up** — see Delivery Findings: the dock Fate tab also hosts story 118-7's non-conflict 4dF roll tray (`FateDiceTray`), which is NOT duplicated under Character→Stats, so removing the tab wholesale would lose the out-of-conflict roll surface. AC-4 is therefore deferred (logged under Design Deviations).

**Test Files:**
- `sidequest-ui/src/components/GameBoard/__tests__/GameBoard-fate-native-chrome.test.tsx` — PART A, GameBoard-integration (the wiring test). Two-sided across all four native render sites.

**Tests Written:** 10 tests covering ACs 1–3 (AC-4 deferred). RED: 5 (the four Fate-suppression sites + the ruleset-signal robustness case). GREEN guards: 5 (four WN-side regression guards + the Fate-harm positive).
**Status:** RED (failing — ready for Dev). Verified via testing-runner (`126-19-tea-red`): file compiles clean, 5 failed / 5 passed, no vacuous assertions.

**The signal Dev must use:** the bound-ruleset signal is GameBoard's existing `fateData` prop (`fateData != null` ⇒ Fate pack) — the SAME signal that already drives `showCurrency={fateData == null}` on the inventory widget (renderWidgetContent). Thread a Fate-suppression flag from there into CharacterWidget/CharacterPanel (header level/HP badge, FolioEdgeTicks, party-row class/level/HP) and into the input region's `HpPipScale`. The ruleset-signal test forbids keying off a per-PC name-matched `fateSheet` (fragile — a roster name mismatch would leak). This resolves the SM's open question: the signal is `fateData`; it already reaches the Character widget (as `fateSheet`) but does NOT reach `HpPipScale` — that thread is green-phase wiring, not a CSS tweak.

**Surface→testid map for Dev:** header = `character-level-badge` + `character-edge-badge`; body pill+pips = `character-edge-ticks`; party row = `party-member-edge-{id}` + the `{class} Lv.{level}` text; action bar = `input-hp-scale`. Suppress on Fate, keep on WN. The header subtitle (calling/origin) is intentionally OUT of scope — only the four enumerated sites.

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| Two-sided ruleset branch (SOUL "Bind the Ruleset") | every assertion paired Fate-vs-WN | RED/guard |
| Every Test Suite Needs a Wiring Test (CLAUDE.md) | whole file drives real GameBoard render path | RED |
| #8 test quality (no vacuous / no `as any`) | self-checked — all assertions meaningful | pass |

**Rules checked:** 3 of 3 applicable (the TS lang-review list is otherwise Dev/impl-facing; this is a behavioral UI fix with no new constructor/enum/API boundary).
**Self-check:** 0 vacuous tests. No `as any` (all fixtures are properly typed against real GameBoardProps — no prop-widening needed since this story adds no new props).

**Handoff:** To Dev (Naomi Nagata) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes (PART A — Fate native-chrome suppression)
**Files Changed:**
- `sidequest-ui/src/components/CharacterPanel.tsx` — added optional `suppressNativeChrome?: boolean` (default false); gates the header level badge (`character-level-badge`), the header HP `EdgeBadge` (`character-edge-badge`), the body `FolioEdgeTicks` (`character-edge-ticks`), and the party-row class/level/HP secondary line (`party-member-edge-*` + `{class} Lv.{level}`). Name is kept.
- `sidequest-ui/src/components/GameBoard/GameBoard.tsx` — passes `suppressNativeChrome={fateData != null}` into the Character widget (threaded through the `{...props}` `CharacterWidget`), and guards the input-region `HpPipScale` with `{fateData == null && …}`. Same ruleset gate as the existing inventory `showCurrency` line.

**Approach:** Pure additive — one optional prop + two call-site guards. The suppression keys on the ruleset signal `fateData != null` (not the per-PC name-matched `fateSheet`), so a Fate roster-name mismatch can never leak the chrome (TEA's mismatch test passes). WN/native packs render the native chrome unchanged because the prop defaults false and `fateData` is null there.

**Tests:** 10/10 story tests passing (GREEN). Full UI regression sweep: 2461 + 10 = **2471 passing, 0 failing** (284 files). `eslint` clean, `tsc --noEmit` clean.
**Branch:** `feat/126-19-fate-suppress-native-chrome-and-dock-dedup` (pushed).

**Self-review:** Wired end-to-end (GameBoard → CharacterWidget → CharacterPanel; GameBoard input region → HpPipScale). Follows the established `showCurrency` ruleset-gate pattern. ACs 1–3 met; AC-4 deferred to PART B follow-up (see TEA deviation, Keith-approved). No new error handling required (cosmetic suppression; no OTEL needed per UI CLAUDE.md "cosmetic UI changes").

**Handoff:** To Reviewer (Chrisjen Avasarala).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (87 tests green, lint+tsc clean, 0 smells) | N/A — 1 note (loose `!=null`) confirmed correct |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 5 (1 high, 2 med, 2 low) | confirmed 5 (severity-calibrated), 0 dismissed, 0 deferred |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 (2 high-conf, 1 med — all LOW severity) | confirmed 3, 0 dismissed |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 1 (low style — loose equality) | confirmed 1 (LOW), all 13 rules + SOUL + no-half-wired PASS |

**All received:** Yes (4 enabled returned; 5 disabled via `workflow.reviewer_subagents`)
**Total findings:** 9 confirmed (severity-calibrated to MEDIUM/LOW; rationale below), 0 dismissed, 0 deferred

## Reviewer Observations

- `[VERIFIED]` end-to-end wiring — `GameBoard.tsx:614` passes `suppressNativeChrome={fateData != null}` into the `character` case; `CharacterWidget` is a `{...props}` pass-through (`widgets/CharacterWidget.tsx:6`); `CharacterPanel` destructures `suppressNativeChrome = false` and gates 4 sites; `HpPipScale` guarded at `GameBoard.tsx:835`. Real non-test consumer exists. Complies with UI CLAUDE.md "no half-wired features" (rule-checker enumerated all 5 suppression points reached).
- `[VERIFIED]` "Bind the Ruleset, Don't Balance It" (SOUL) — every site *removes* the native element (`{!suppressNativeChrome && …}`), none re-tune or substitute a Fate-equivalent. Harm surfaces via the pre-existing 118-2 `FateCharacterSheet` in the Stats tab. evidence: CharacterPanel.tsx:312/339/351/586, GameBoard.tsx:835.
- `[VERIFIED]` null-handling — `fateData` is `FateStatePayload | null`, defaulted `= null` in GameBoard destructuring, so `!= null`/`== null` correctly treat both null and (unreachable) undefined as "not Fate"; matches the sibling `showCurrency={fateData == null}` (GameBoard.tsx:621) and `availableWidgets` (line 438). No `||`-vs-`??` misuse; `survivability_pool_label ?? "HP"` is correct. evidence: rule-checker rule #4, 5 instances.
- `[TEST]` `[MEDIUM]` the ruleset-signal "mismatch" test (the one whose whole purpose is to forbid keying suppression off the per-PC name-matched `fateSheet`) covers header/edge-ticks/input-bar but **omits the party-row** — the surface most naturally name-keyed, i.e. exactly what the test exists to protect. The shipping impl keys the party-row on `suppressNativeChrome` (correct), but the test doesn't enforce it there. `GameBoard-fate-native-chrome.test.tsx:195`.
- `[TEST]` `[MEDIUM→LOW]` vacuous-absence robustness — only the first suppress test anchors `getByTestId("character-panel")`; the other panel-interior absent-checks don't re-assert the panel mounted, so a future regression breaking CharacterPanel mount would make them falsely green. **Downgraded from the specialist's HIGH** with rationale: TEA's RED run proved these exact assertions *failed* (element present) before the fix → they bite today and are not vacuous-as-written; `renderBoard` always passes a non-null `characterSheet` so the mount is deterministic; rule-checker independently rated #8 compliant. Real future-hardening, not a present defect. `:146`, `:153`.
- `[TEST]` `[LOW]` the "harm surfaces as Fate sheet" positive (`fate-character` present) has no paired WN-side negative at the GameBoard wiring level (the inverse IS covered in isolation by `CharacterPanelFateSheet.test.tsx:85`). Two more LOW: presence-only assertions on the WN edge-ticks and party HP pill where a content check would match the paired specificity. `:169`, `:392`, `:399`.
- `[DOC]` `[LOW]` three comment-accuracy nits, none touching logic: (a) test header "no new props are introduced by this story" is false — `suppressNativeChrome` is new on `CharacterPanelProps` (true only at the GameBoard-prop level); (b) `GameBoard.tsx:611` "same gate as showCurrency" uses `!= null` vs that line's `== null` — same signal, complementary polarity, worth a clarifying word; (c) pre-existing `CharacterPanel.tsx:599` cites retired ADR-078 (carried forward verbatim in the reindent, not introduced here) — should read ADR-114.
- `[RULE]` `[LOW]` loose equality `!= null`/`== null` at GameBoard.tsx:614/835 — style only, consistent with three pre-existing sites in the same file; not a correctness risk (rule-checker, low confidence).
- `[EDGE]`/`[SILENT]`/`[TYPE]`/`[SEC]`/`[SIMPLE]` — specialists disabled via settings; assessed in-line below by the Reviewer. No edge/silent-failure/type/security/complexity issues found: the diff is additive conditional JSX + one boolean prop, no error paths, no async, no user-input boundary, no new abstraction (mirrors the existing `showCurrency` gate — no simpler form available).

### Rule Compliance

- **Bind the Ruleset, Don't Balance It (SOUL/CLAUDE.md):** COMPLIANT — all 5 suppression sites remove native chrome; none re-tune. (rule-checker: 5/5 instances.)
- **No half-wired features (UI CLAUDE.md):** COMPLIANT — all 5 stated surfaces reach the `fateData` gate, including the previously-unwired `HpPipScale`.
- **OTEL not required for cosmetic UI (UI CLAUDE.md):** COMPLIANT — no mechanical state mutation; suppression is a render-path change; the exemption applies.
- **TS lang-review #1–#13:** COMPLIANT across 31 instances (rule-checker). Only LOW style note: loose `!= null`.
- **TS #8 / Every Test Suite Needs a Wiring Test:** the suite IS a real wiring test (drives `GameBoard → CharacterWidget → CharacterPanel`); two-sided contract present for all 4 surfaces. The test-analyzer MEDIUM/LOW gaps are completeness/robustness, not a present-vacuity violation (corroborated: rule-checker rated #8 compliant; RED evidence proves the assertions bite).

### Devil's Advocate

Argue the code is broken. **Could a WN player ever see chrome wrongly suppressed?** Only if `fateData` were non-null on a non-Fate pack — but the server emits `FATE_STATE` exclusively on `ruleset=='fate'` packs, and the whole UI (showCurrency, availableWidgets, the Fate tab gate) already trusts that signal; this change adds no new trust, it reuses the established one. **Could a Fate player still see leaked HP?** The four panel surfaces key on the single `suppressNativeChrome` flag and the input bar on the same `fateData` gate; rule-checker enumerated all five and confirmed each removes its element. The one residual path is the Character→Stats *content*: on a Fate pack where the local sheet name does NOT match any `fateData.characters` entry, `fateSheet` derives null and the Stats tab falls back to native `StatsContent` ("No stats available.") — but that is pre-existing 118-2 behavior, out of PART-A scope (which is HP/level/class chrome, not Stats-tab content), and the chrome itself still suppresses correctly because it keys on `fateData`, not the name match. **What would a confused reviewer misread?** The "same gate as showCurrency" comment with opposite operators — addressed as a LOW doc nit. **What would a stressed test miss?** If a future dev re-keyed the party-row off `fateSheet != null` (name match), the mismatch test would NOT catch it because it omits the party-row — the sharpest finding, logged MEDIUM. **Empty/huge inputs?** `characters: []` → no party rows, no crash; many PCs → all rows suppressed uniformly (one pack, one ruleset). **Layout?** When both header badges suppress, the `items-end` flex container renders empty — cosmetically inert, no overflow. Net: no Critical/High. The shipping behavior is correct, proven RED→GREEN, fully wired, and rule-compliant; the genuine findings are test-hardening and comment-accuracy, all MEDIUM/LOW, none blocking.

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** server `FATE_STATE` → `state.fateState` → GameBoard `fateData` → `suppressNativeChrome={fateData != null}` → CharacterWidget (`{...props}`) → CharacterPanel gates header level badge / HP `EdgeBadge` / `FolioEdgeTicks` / party-row class·level·HP; in parallel `{fateData == null && <HpPipScale/>}` at the input region. Safe because the signal is server-authoritative (Fate-only emission) and reused from the established `showCurrency`/`availableWidgets` gates — no new trust surface.

**Pattern observed:** ruleset-gate via existing `fateData` signal, mirroring `showCurrency={fateData == null}` — GameBoard.tsx:614/835. Idiomatic and consistent.

**Error handling:** none required — additive conditional JSX, no error paths, no async, no input boundary (rule-checker #7/#10/#11 = 0 instances). Cosmetic suppression ⇒ no OTEL (UI CLAUDE.md exemption).

**Dispatch tags:** `[PREFLIGHT]` clean · `[TEST]` 5 findings (1 calibrated-down from HIGH, all MEDIUM/LOW — test-hardening, non-blocking) · `[DOC]` 3 LOW comment nits · `[RULE]` 1 LOW style (loose equality) · `[EDGE]`/`[SILENT]`/`[TYPE]`/`[SEC]`/`[SIMPLE]` disabled via settings, assessed in-line — none found.

**Why APPROVED not REJECTED:** zero production-code defects; all 13 lang-review rules + SOUL "Bind the Ruleset" + "no half-wired" PASS; the implementation is correct, proven, and fully wired. Every confirmed finding is MEDIUM/LOW after honest severity calibration (the specialist's lone HIGH is a future-regression fragility mitigated by the RED evidence + deterministic mount + rule-checker corroboration). Per the severity rule, no Critical/High ⇒ no block. The test-hardening items are genuine and recorded as non-blocking Delivery Findings (not dismissed) for a follow-up sweep alongside the comment nits.

**Handoff:** To SM for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Conflict** (blocking): PART B (remove the standalone "Fate" dock tab) cannot be done as a pure tab removal — the dock Fate tab hosts BOTH the duplicate sheet AND story 118-7's non-conflict 4dF roll tray (`FateDiceTray`, `fate-dice-tray`), which is NOT duplicated under Character→Stats (`FateCharacterSheet` takes no `latestRoll`). Removing the tab wholesale loses the out-of-conflict roll surface and breaks `GameBoard-fate-roll.test.tsx`. Affects `sidequest-ui/src/components/GameBoard/widgetRegistry.ts`, `GameBoard.tsx` (availableWidgets `fate` gate + renderWidgetContent), `MobileTabView.tsx`, `widgets/FateWidget.tsx`. *Found by TEA during test design.*
- **Gap** (blocking): a follow-up story is needed for PART B — "Remove the duplicate Fate dock tab AND re-home the 4dF non-conflict roll surface under Character→Stats (or another single home)" — under epic 126. Keith chose "PART A now, split PART B" (2026-06-19). SM to file at finish; story 126-19 title/ACs should be trimmed to PART A. *Found by TEA during test design.*
- **Improvement** (non-blocking): the orphaned native model is the shared root with 126-24 (chargen cluster) — the server still emits HP/level/class on PARTY_STATUS/CHARACTER_SHEET for a Fate PC. This story masks it at the UI; a server-side fix (don't emit native HP/level/class on a Fate pack) would be the deeper cure. Affects `sidequest-server` party/sheet projection. *Found by TEA during test design.*

### Dev (implementation)
- No upstream findings during implementation. (Confirmed TEA's: the suppression signal is `fateData != null` at GameBoard; `HpPipScale` had no ruleset signal and is now guarded at the call site. The deeper server-side fix — TEA's Improvement above — remains the real cure; this story masks at the UI as scoped.)

### Reviewer (code review)
- **Improvement** (non-blocking): test-hardening sweep recommended on `sidequest-ui/src/components/GameBoard/__tests__/GameBoard-fate-native-chrome.test.tsx` — (1) the ruleset-signal "mismatch" test omits the party-row, the surface most prone to a name-keyed regression it exists to forbid (add `party-member-edge-p1` + class/`Lv.` absence to the mismatch body); (2) anchor `getByTestId("character-panel")` in every panel-interior absent-check (fold into `openCharacterTab()`) to remove future vacuous-absence risk; (3) add a WN-side `fate-character` negative for the two-sided harm-model contract; (4) optional: content (not presence-only) assertions on the WN edge-ticks + party HP pill. Impl is correct — these strengthen the contract, do not fix a defect. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): three comment-accuracy nits to sweep alongside (all LOW, zero logic impact): test-file header "no new props are introduced" is false (`suppressNativeChrome` is new on `CharacterPanelProps`); `GameBoard.tsx:611` "same gate as showCurrency" should note complementary polarity (`!= null` vs `== null`); pre-existing `CharacterPanel.tsx:599` cites retired ADR-078 (carried forward in the reindent) — update to ADR-114. Affects `sidequest-ui/src/components/{CharacterPanel.tsx,GameBoard/GameBoard.tsx,GameBoard/__tests__/GameBoard-fate-native-chrome.test.tsx}`. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

1 deviation

- **AC-4 (remove the standalone Fate dock tab) not tested — PART B deferred**
  - Rationale: The dock Fate tab also hosts story 118-7's non-conflict 4dF roll tray, not duplicated under Character — removing it wholesale loses functionality (see Delivery Findings). Keith chose "PART A now, split PART B" (2026-06-19).
  - Severity: minor (explicit scope reduction, user-approved)
  - Forward impact: PART B + roll-surface re-home becomes a follow-up story under epic 126; this story's title/ACs should be trimmed to PART A at finish.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **AC-4 (remove the standalone Fate dock tab) not tested — PART B deferred**
  - Spec source: context-story-126-19.md, AC-4 ("The standalone 'Fate' dock tab is removed; the Fate sheet renders only under Character")
  - Spec text: "Remove the standalone Fate dock tab; the Fate sheet lives ONLY in Character."
  - Implementation: No PART B tests written; the existing `GameBoard-fate-tab.test.tsx` / `GameBoard-fate-roll.test.tsx` are left untouched (the dock tab stays this story). Only PART A (chrome suppression, ACs 1–3) is tested.
  - Rationale: The dock Fate tab also hosts story 118-7's non-conflict 4dF roll tray, not duplicated under Character — removing it wholesale loses functionality (see Delivery Findings). Keith chose "PART A now, split PART B" (2026-06-19).
  - Severity: minor (explicit scope reduction, user-approved)
  - Forward impact: PART B + roll-surface re-home becomes a follow-up story under epic 126; this story's title/ACs should be trimmed to PART A at finish.

### Dev (implementation)
- No deviations from spec. Implemented exactly the behavior the PART A tests pin (suppress on Fate, keep on WN, ruleset-signal not name-match), within the user-approved reduced scope. AC-4 deferral is logged under TEA above; Dev added nothing beyond what the tests require.

### Reviewer (audit)
- **TEA: AC-4 (remove the standalone Fate dock tab) not tested — PART B deferred** → ✓ ACCEPTED by Reviewer: the conflict is real and correctly diagnosed — the dock Fate tab hosts story 118-7's non-conflict `FateDiceTray` (not duplicated under Character→Stats via `FateCharacterSheet`), so a wholesale removal would lose the out-of-conflict roll surface and red `GameBoard-fate-roll.test.tsx`. Splitting PART B (with roll re-home) to a follow-up is the sound call; Keith-approved 2026-06-19. SM must trim this story's title/ACs to PART A and file the PART B follow-up.
- **Dev: No deviations from spec** → ✓ ACCEPTED by Reviewer: confirmed — the diff implements exactly the four-surface suppression the PART A tests pin, keyed on the ruleset signal `fateData != null` (not the per-PC name match), with no scope creep. rule-checker corroborates: additive boolean prop + conditional JSX, no new abstraction.
- No undocumented deviations found. The diff matches the (reduced PART-A) spec and the tests; nothing diverged silently.