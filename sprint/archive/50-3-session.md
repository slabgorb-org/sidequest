---
story_id: "50-3"
jira_key: null
epic: "50"
workflow: "trivial"
---
# Story 50-3: PartyPanel renders recruited companions section — server roster correct, UI was silent

## Story Details
- **ID:** 50-3
- **Jira Key:** N/A (SideQuest personal project)
- **Workflow:** trivial (switched from tdd during red phase — story revealed as silently-fixed by 2026-05-06/07 commits; integration test is the only deliverable)
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-05-13T11:36:36Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup (tdd) | 2026-05-13T06:52:00Z | 2026-05-13T10:53:25Z | 4h 1m |
| red (tdd) | 2026-05-13T10:53:25Z | 2026-05-13T11:05:00Z | 11m |
| implement (trivial, retroactive) | 2026-05-13T11:00:00Z | 2026-05-13T11:05:00Z | 5m (test commit) |
| review | 2026-05-13T11:05:00Z | 2026-05-13T11:36:36Z | 31m 36s |
| finish | 2026-05-13T11:36:36Z | - | - |

## Acceptance Criteria
- PartyPanel renders a "Companions" sub-section when the server's PARTY_STATUS / state mirror reports a non-empty companions roster
- Each companion row shows name, archetype/role, current location (if split-party), and a portrait or letter-fallback per the existing chrome
- The sub-section is hidden (not just empty) when the roster is empty
- Vitest covers the empty / single-companion / multi-companion / split-party-location states
- Wiring test confirms the section is reachable from the production state-mirror path (not just storybook fixtures)

## Story Context

**Discovered in:** `sq-playtest-pingpong.archive-20260507-085200.md` and `sq-playtest-pingpong.archive-20260508-pre472.md` (2026-05-07, 2026-05-08)

**Anti-pattern:** Server-half done, UI-half silent. The recruitment subsystem maintains a server-side companion roster; the UI `PartyPanel` component has no element to render them. Marked fixed on the server but never verified because the UI consumer was never built. Playtests moved to tea_and_murder solo immediately afterwards, leaving the gap silently broken for ~6 days.

**Impact:** 
- Sebastien-axis loss: recruited companions are mechanical state players cannot see
- Aspirational household-audience loss: companion-driven play (half of Heavy Metal / road_warrior pitch) is invisible

## Sm Assessment

**Setup Complete:** Yes
**Session File:** `.session/50-3-session.md`
**Branch:** `feat/50-3-partypanel-renders-recruited-companions` (sidequest-ui, base: develop)
**Repos:** sidequest-ui
**Workflow:** tdd (phased)

**Story Selection Rationale:** 3-point UI bug surfaced in pingpong-archive triage (50-1, completed 2026-05-13). Directly follows the recruitment-subsystem closeout — server roster is correct, the UI consumer is missing. Clean AC, single-repo scope, advances sprint closure (Sprint 3 at 13/34 pts).

**Acceptance Criteria:** 5 ACs defined in story body covering empty/single/multi/split-party render states plus a wiring test that confirms the section reaches the production state-mirror path (not just storybook fixtures). The wiring test is non-negotiable per CLAUDE.md "Every Test Suite Needs a Wiring Test."

**Anti-pattern Context:** This bug is the exact "server-half done, UI-silent" failure mode the project's "Verify Wiring, Not Just Existence" rule was written to prevent. TEA should write a failing test that exercises the production state-mirror path end-to-end before any greenwashing.

**Handoff:** To Radar (TEA) for the RED phase.

## Tea Assessment

**RED Phase Outcome:** Story is silently-fixed. No failing tests authored; one new App-level integration test added as a permanent regression guard.

**Files Added:**
- `sidequest-ui/src/__tests__/companions-app-wire-integration.test.tsx` — 4 tests covering the App → GameBoard wiring path through a real PARTY_STATUS WebSocket frame (recruit, dismiss, multi-companion ordering, malformed-row defensive filter)

**Verification chain:**
- Pre-existing `companions-party-status-wiring.test.tsx` (5 tests) — passing — CharacterPanel-only render check
- New `companions-app-wire-integration.test.tsx` (4 tests) — passing — App-level state-mirror integration through `jest-websocket-mock`
- ESLint: clean on new file
- `tsc --noEmit`: clean

**Diagnosis:** The 2026-05-07 pingpong archive entry was authored AFTER commit 890dc4b (UTC 07:12) shipped the fix (archive timestamp 08:52). 50-1 triage carried that stale read forward to 50-3 without re-running the existing test or checking commit history (`feedback_pingpong_parallel_writers.md` failure mode). Code paths verified intact:
- `App.tsx:849-863` — extracts `payload.companions`, maps to `CompanionSummary[]`, calls `setPartyCompanions`
- `App.tsx:1961` — forwards as `companions={partyCompanions}` prop
- `GameBoard.tsx:387` — threads to CharacterWidget
- `CharacterPanel.tsx:548-602` — renders `data-testid="companions-section"` when non-empty

**Recommendation:** Dev phase has nothing to implement. Commit the new test file, push, and hand to Reviewer for the merge ceremony. The story is verified, not built.

**Deviation:** AC2/AC4 split-party-location is a new feature the SM-setup added; original bug report didn't include it. Deferred to a follow-up — see Design Deviations section.

**Handoff:** To Major Charles Emerson Winchester III (Dev) for commit + push, then onward to Colonel Potter (Reviewer).

## Delivery Findings

### Sm (setup)
- No upstream findings.

### Tea (red)
- **Improvement** (non-blocking): 50-1 triage punted Item 2 to 50-3 without verifying the existing fix. Affects `sprint/archive/50-1-session.md` (verdict shape) and the pingpong triage process (`.claude/skills/sq-playtest/pingpong.md` could note "re-run any existing test for the affected component before declaring `confirmed broken`"). *Found by Tea during implementation.*
- **Gap** (non-blocking): The pre-existing `companions-party-status-wiring.test.tsx` is mis-named — it does NOT test wiring, it re-implements the App.tsx mapper inside the test file and exercises only CharacterPanel directly. The new `companions-app-wire-integration.test.tsx` is the actual wiring test. Affects test naming convention — future "X-wiring.test.tsx" files should genuinely traverse production code paths. *Found by Tea during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): Promote `companions-app-wire-integration.test.tsx` as the canonical project template for App-level "wiring" tests. Pair with `app-gameboard-world-slug-wiring.test.tsx` in any future test-writing guide. Affects test conventions (no specific file). *Found by Reviewer during code review.*
- **Question** (non-blocking): Should the misnamed pre-existing `companions-party-status-wiring.test.tsx` be renamed to `companions-character-panel-render.test.tsx` to stop the naming lie? Out of scope for 50-3 but worth a 1-point rename chore. Affects `sidequest-ui/src/__tests__/companions-party-status-wiring.test.tsx`. *Found by Reviewer during code review.*

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (1438 pass / 0 fail / 0 skip; 0 code smells; tsc clean; new file lint clean) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (1 ran, 8 skipped per `workflow.reviewer_subagents` settings)
**Total findings:** 0 confirmed, 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

**Diff scope:** Single new file — `sidequest-ui/src/__tests__/companions-app-wire-integration.test.tsx` (327 insertions / 0 deletions / 0 production code touched). Confirmed via `git diff develop...HEAD --name-only`.

**Observations:**

1. `[VERIFIED]` Test mock surface is correct — `vi.mock("@/components/GameBoard/GameBoard")` at test.tsx:38 stubs the receiving component so the prop received from App.tsx is the unit under test, not GameBoard's render tree. Mirror of the pattern in `app-gameboard-world-slug-wiring.test.tsx:38-46` — same trick, same testid serialization shape. Evidence: test.tsx:38-45, app-gameboard-world-slug-wiring.test.tsx:38-46.

2. `[VERIFIED]` Wire shape matches server canonical builder — fixture at test.tsx:154-169 carries the same field set that `sidequest-server/sidequest/server/views.py:548` emits via `PartyStatusPayload(members, companions)`. CompanionMember fields name/role/description/notes/recruited_turn/recruited_by all present and in the right shape.

3. `[VERIFIED]` PARTY_STATUS handler reached unconditionally — App.tsx:782 has no `sessionPhase` gate on the PARTY_STATUS branch, so the test's `SESSION_EVENT{ready}` → `PARTY_STATUS` sequence will trigger `setPartyCompanions` regardless of UI mode. Tests fire on the same path production uses.

4. `[VERIFIED]` Test isolation correct — `WS.clean()` + `AudioEngine.resetInstance()` + `localStorage.clear()` + `vi.unstubAllGlobals()` in afterEach (test.tsx:119-125). `slugCounter` plus `Date.now()` makes freshSlug() collision-proof (test.tsx:79-96). No shared state between tests.

5. `[VERIFIED]` Comment hygiene — every test has a docstring tying it to either the 2026-05-07 playtest bug, a specific App.tsx line (test.tsx:286 cites `App.tsx:861`), or the canonical Sünden recruitment arc. Comments document the *why*, not the *what*. Reads cleanly against the project rule "default to writing no comments unless the WHY is non-obvious."

6. `[MEDIUM]` Coverage gap — the malformed-row test (test.tsx:285-326) only exercises empty-string name; it doesn't cover `null`/`undefined` name. App.tsx:861's filter `(c) => c.name` catches all falsy values, so behavior is correct, but a future refactor to `c.name != null` (only-undefined filter) would slip past this test. Not blocking — minor coverage gap on a defensive branch.

7. `[MEDIUM]` PARTY_STATUS with missing `companions` field not exercised — App.tsx:851 has `Array.isArray(rawCompanions) ? ... : []` which handles the field being absent. Test only covers present-but-empty (`companions: []`) and present-with-rows. Pydantic's default_factory means the server always emits the field, so this is forward-compat ground only — not blocking.

8. `[LOW]` Test depends on App.tsx absorbing `SESSION_EVENT{event:"ready", has_character:true}` as the chargen-bypass — same brittle coupling already accepted in `app-gameboard-world-slug-wiring.test.tsx`. If that bypass path is ever renamed/removed, this whole class of App-level wiring tests breaks together. Documented in test.tsx:148-150 comment. Pattern-consistent with the rest of the suite; not a blocker.

9. `[VERIFIED]` Workflow correctness — story was filed as a bug; verification showed code already shipped; switched to `trivial` workflow per user direction; no production change attempted. Branch contains exactly one commit (`71b4759 test(50-3): App-level wiring integration for PARTY_STATUS companions`) with no scope creep.

**Data flow traced:** PARTY_STATUS WS frame → `useWebSocket.onMessage` (parses JSON, dispatches) → App.tsx:782 branch → maps `payload.companions` → `setPartyCompanions` → React state → `<GameBoard companions={partyCompanions} />` at App.tsx:1961. Test mock at GameBoard.tsx import substitutes a stub that serializes the prop into a DOM attribute, asserted via `waitFor`.

**Pattern observed:** Genuine integration test that replaces a misnamed unit test masquerading as "wiring." Matches the established `app-gameboard-*-wiring.test.tsx` family. Worth promoting as the project's canonical "wiring test" template.

**Error handling:** Defensive `c.name` filter at App.tsx:861 (verified in test 4); `Array.isArray(rawCompanions) ? ... : []` fallback at App.tsx:851 (not directly tested but exercised indirectly). No error paths introduced or removed by this diff.

**Devil's Advocate:** Is this test theatre — does it actually catch the regression it claims to? If I revert commit `890dc4b` (the original 2026-05-06 fix), does this test go red? Let me mentally simulate: pre-fix, App.tsx had no `setPartyCompanions` call in the PARTY_STATUS branch. The `companions={partyCompanions}` prop at App.tsx:1961 would receive the initial empty `useState<CompanionSummary[]>([])` value. The test would see `data-companions="[]"` and fail at `expect(companions).toHaveLength(1)`. Yes — this test would have caught the original bug. What about a different regression class: someone refactors `setPartyCompanions` to use functional update `setPartyCompanions(prev => [...prev, ...mappedCompanions])` (merge instead of overwrite)? Test 2 catches that — the dismissal test asserts a SECOND PARTY_STATUS with empty companions clears the roster; a merge regression would keep Donut around. What if the WS message dispatcher gets a new `if (msg.type === ...)` branch that intercepts PARTY_STATUS first and returns? Test 1 catches that — no setPartyCompanions = empty prop. What about a regression where companions are correctly stored in state but not threaded to GameBoard (e.g., a refactor drops `companions={partyCompanions}` at App.tsx:1961)? Test 1 catches it — the mock receives undefined and serializes to `"[]"`. Genuine coverage. The 327-line file isn't padding — it's four distinct regression classes per test. Approve. One worry: the test depends on the SESSION_EVENT-as-chargen-bypass being a stable App-level convention. If that contract changes (e.g., requires `has_character: true` + a separate CHARACTER_STATE frame), the test wedges along with the existing wiring suite. That's structural coupling but not unique to this test — it's already the team norm. Not a blocker.

**AC compliance:**
- AC1 (renders section on non-empty roster): pre-existing test covers; new test 1 reinforces at the wire boundary ✓
- AC2 (name/role/location/portrait per row): name + role + recruited_by covered by new test 1; location deferred per logged deviation
- AC3 (hidden on empty roster): pre-existing test covers; new test 2 reinforces at App boundary ✓
- AC4 (vitest covers states): empty/single/multi covered; split-party-location deferred per logged deviation
- AC5 (wiring confirms production state-mirror path): **only now genuinely satisfied** by the new file — the pre-existing test bypassed the production path entirely ✓

**Handoff:** To Hawkeye (SM) for finish-story.

## Design Deviations

### Tea (red)
- **Story declared silently-fixed; no implementation deviations to AC1/AC3/AC5**
  - Spec source: sprint/current-sprint.yaml story 50-3 description ("UI half wasn't wired")
  - Spec text: "the UI PartyPanel component has no element to render them"
  - Implementation: Already shipped 2026-05-06/07 on develop (commits 890dc4b feat(party-panel), 6d7fdd3 test(wiring), 784147b test(live-update + dismiss)). Code path App.tsx:782-865 → GameBoard:387 → CharacterWidget → CharacterPanel:548-602 is intact.
  - Rationale: 50-1 pingpong triage punted Item 2 without re-testing. Both the pre-existing wiring test (5 tests) and the new App-level integration test (4 tests) pass; the live runtime wire path is verified end-to-end through a mocked WebSocket.
  - Severity: minor
  - Forward impact: none

- **AC2 + AC4 "current location (if split-party)" deferred — not implemented**
  - Spec source: .session/50-3-session.md ACs (written by sm-setup, not in original story description)
  - Spec text: "Each companion row shows name, archetype/role, current location (if split-party), and a portrait or letter-fallback" + "Vitest covers the empty / single-companion / multi-companion / split-party-location states"
  - Implementation: No `current_location` field exists on `CompanionSummary` (UI) or `CompanionMember` (server). Adding it requires server schema changes (sidequest/protocol/messages.py CompanionMember, sidequest/server/views.py builder, sidequest/server/narration_apply.py mutation seam) + UI render in CharacterPanel + new tests. ~5+ pts of new feature work.
  - Rationale: SM-setup expanded the ACs beyond the original bug-report scope. The user-facing 2026-05-07 pingpong report only flagged "companions section not visible"; split-party-location tracking is a new feature, not the filed bug. Per project memory `feedback_no_invented_urgency.md` and `feedback_plan_ceremony.md`, do not over-scope a 3pt UI verification into a multi-repo feature.
  - Severity: major (deviates from current-session AC list)
  - Forward impact: If the playgroup actually splits the party with companions on Mawdeep-style detours, the panel won't surface location. File as a follow-up 3-5pt story rather than expand 50-3.

### Reviewer (audit)
- **TEA: "Story declared silently-fixed"** → ✓ ACCEPTED by Reviewer: Confirmed by inspection. Commit 890dc4b shipped at 2026-05-07 07:12 UTC, pingpong archive timestamp 08:52 UTC postdates the fix; 50-1 triage carryforward is the structural cause. Live wire path verified end-to-end by the new integration test.
- **TEA: "AC2/AC4 split-party-location deferred"** → ✓ ACCEPTED by Reviewer: User explicitly chose "Convert to trivial workflow and finish" over "Implement AC2/AC4 split-party-location anyway." SM-setup over-scoped the original 2026-05-07 bug report. Right call to defer; flag as a follow-up rather than balloon a 3pt verification story into multi-repo feature work. Note for SM finish: consider whether to file the follow-up explicitly in `sprint/future.yaml` or leave it implicit until split-party play surfaces it.
- No undocumented spec deviations spotted.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->