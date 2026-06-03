---
story_id: "71-12"
jira_key: ""
epic: "epic-71"
workflow: "trivial"
---
# Story 71-12: Comment-guard at peer-reveal capture site (App.tsx) — 'MUST use raw reveals, never merged' to prevent stale-draft regression

## Story Details
- **ID:** 71-12
- **Jira Key:** None (no Jira integration for this story)
- **Workflow:** trivial
- **Stack Parent:** none
- **Type:** chore
- **Points:** 1
- **Priority:** p3

## Story Context

**Background:** Story 71-10 added peer-action rounding (PlayerActionPayload now carries an integer round field). The peer-action reveal map in App.tsx uses `usePersistedPeerActions()` which consumes raw reveals from the perception-filtered map. A critical design invariant: **the peer reveals used in App.tsx MUST be raw reveals, never merged reveals**, because merged reveals can stale (out-of-date disposition data, frozen at some past turn) and create a regression where peer actions appear under stale context.

**Technical Approach:**
1. Locate the peer-reveal capture site in sidequest-ui/src/screens/NarrativeView.tsx or src/App.tsx where `usePersistedPeerActions()` is called or peer reveals are sourced.
2. Add a guard comment (JSDoc or inline block comment) at the point where peer reveals are captured, stating:
   ```
   // GUARD: MUST use raw reveals from perception-filtered map, never merged.
   // Merged reveals carry stale disposition/metadata (frozen at past turns).
   // Stale-draft regression: if merged reveals are used here, peer action context
   // will appear out-of-date. Always source from the canonical raw-reveals map.
   // See ADR-104/105 (perception firewall) and 71-10 (peer-action rounding).
   ```
3. If the code already uses raw reveals correctly, verify it and leave the guard comment in place for future maintainers.
4. If any merged-reveal usage exists nearby, flag it as a separate concern (not in scope for this story — file a follow-up).

**Acceptance Criteria:**
- A guard comment is present at the peer-reveal capture site (App.tsx or component that consumes peer reveals).
- The comment explicitly names the rule: "MUST use raw reveals, never merged."
- The comment references the design principle (ADR-104/105, stale-draft regression, 71-10 context).
- The code currently uses raw reveals (no regression present); the comment is prophylactic.
- No logic changes; this is comment-guard only.

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-03T19:12:34Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-03 | 2026-06-03T19:04:27Z | 19h 4m |
| implement | 2026-06-03T19:04:27Z | 2026-06-03T19:08:03Z | 3m 36s |
| review | 2026-06-03T19:08:03Z | 2026-06-03T19:12:34Z | 4m 31s |
| finish | 2026-06-03T19:12:34Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->
No upstream findings

### Dev (implementation)
- No upstream findings. The capture site (`App.tsx:1342`) was already correctly fed from raw `peerReveals.reveals`; `mergedPeerReveals` is a separate display-only memo and is not used by the snapshot bridge. No latent merged-reveal usage found at the capture site.

### Reviewer (code review)
- **Improvement** (non-blocking): The accumulator-direction invariant this story documents with a comment has no machine guard, while the mirror display-direction does. `src/__tests__/turn-status-derivation-wiring.test.ts` pins the display path (`peerReveals={mergedPeerReveals}` reaches GameBoard, raw does not) but nothing asserts the snapshot path captures raw `peerReveals.reveals` and never `mergedPeerReveals`. Affects `sidequest-ui/src/__tests__/turn-status-derivation-wiring.test.ts` (add a matched source-text assertion: `toMatch(/persistedPeerActions\.capture\(\s*currentRound\s*,\s*peerReveals\.reveals\s*\)/)` + `not.toMatch(/...mergedPeerReveals.../)`). A future refactor flipping App.tsx:1351 to `mergedPeerReveals` — the exact stale-draft regression named in the guard comment — would pass every existing test. Recommend a 1-pt follow-up story to convert the comment guard into a machine guard. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->
None at setup time

### Dev (implementation)
- No deviations from spec. The capture site already used raw `peerReveals.reveals` (no regression present); the change is the prophylactic guard comment the ACs called for, with no logic change.

### Reviewer (audit)
- **Dev: "No deviations from spec."** → ✓ ACCEPTED by Reviewer: confirmed. The diff is exactly the prophylactic comment the ACs called for, no logic change. Capture site already fed from raw `peerReveals.reveals` (verified at App.tsx:1351). No undocumented deviations found.

## Sm Assessment

**Routing:** trivial (phased) → dev for the `implement` phase.

**Setup decisions:**
- Workflow `trivial` taken straight from the epic-71 YAML (1pt chore) — no fallback judgment needed.
- Jira **explicitly skipped**: this story carries no Jira key (Jira not enabled for epic-71 stories).
- Repo: `sidequest-ui`; branch `feat/71-12-peer-reveal-comment-guard` cut off `develop` (gitflow).
- Session file was initially written to `sidequest-ui/.session/` by setup; SM relocated it to the orchestrator-root `.session/` to match the gate/next-agent convention.

**Scope note for dev:** This is a **comment-guard-only** chore. The intent is prophylactic — locate the peer-reveal capture site that feeds `usePersistedPeerActions()` (App.tsx / NarrativeView.tsx) and add a guard comment asserting "MUST use raw reveals, never merged" to prevent a stale-draft regression. Verify the code already uses raw reveals; **no logic changes**. If a real merged-reveal usage is found, do NOT fix it here — file a follow-up and flag it as a Delivery Finding.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-ui/src/App.tsx` — added a 7-line guard comment at the persisted peer-action snapshot capture site (`peerRevealsSnapshotRef.current`), asserting the snapshot MUST capture from raw `peerReveals.reveals`, never the display-only `mergedPeerReveals` memo defined just below. Names the failure mode (TURN_STATUS-frozen rows → stale-draft regression) and cites ADR-104/105 + 71-10.

**Verification:**
- Capture site (`App.tsx:1342`) confirmed already using raw `peerReveals.reveals` — no regression present, guard is prophylactic as specified.
- `mergedPeerReveals` confirmed to be a separate display-only memo, not consumed by the snapshot bridge.
- ESLint on App.tsx: 0 errors (2 pre-existing exhaustive-deps warnings at lines 1323/1925, unrelated to this change).

**Tests:** 1744/1744 passing (GREEN), 181 test files; TypeScript `tsc --noEmit` clean. Directly-relevant suites green: `usePersistedPeerActions.test.tsx` (4), `usePeerReveals.test.tsx` (10), `peer-action-persistence-wiring-71-4.test.tsx` (2).
**Branch:** `feat/71-12-peer-reveal-comment-guard` (pushed, commit `4fc8bee`)

**ACs met:** Guard comment present at capture site ✓ · explicitly names "raw reveals, never merged" ✓ · references design principle (ADR-104/105, stale-draft, 71-10) ✓ · code currently uses raw reveals, comment is prophylactic ✓ · no logic changes ✓.

**Handoff:** To review phase (Queen of Hearts).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 1 | confirmed 1 (non-blocking [TEST]), dismissed 0, deferred 0 |
| 5 | reviewer-comment-analyzer | Yes | clean | none | N/A |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | none | N/A |

**All received:** Yes (4 enabled returned; 5 disabled via settings)
**Total findings:** 1 confirmed (non-blocking), 0 dismissed, 0 deferred

## Rule Compliance

The diff adds 7 comment lines and no code. Enumerating the rules that could govern a comment-only TS change:

- **CLAUDE.md / "Comments must be accurate" (stale/misleading comments are a defect):** Governs the single changed instance (the guard comment at App.tsx:1343-1349). Verified COMPLIANT — every factual claim cross-checked by comment-analyzer and rule-checker against live code: `mergedPeerReveals` is a `useMemo` at App.tsx:1363 (genuinely "just below"), derived via `mergePeerRevealsWithSubmittedStatus(peerReveals.reveals, turnStatusEntries)`; its sole production consumer is the JSX prop at App.tsx:2262 (display-only ✓); the snapshot at App.tsx:1351 captures raw `peerReveals.reveals` ✓; ADR-104/105 (perception firewall) references are structurally correct.
- **No Silent Fallbacks:** No code paths added — N/A (no struct/branch to enumerate).
- **No Stubbing / No dead code:** No code added — N/A.
- **TS checklist #1–#13 (type escapes, generics, enums, null-handling, modules, react-jsx, async, test-quality, build-config, input-validation, error-handling, perf, fix-regressions):** Zero code instances added across all 13 categories — rule-checker confirmed 0 violations. The only category with a live instance is #13 (fix-introduced-regressions / comment correctness), checked COMPLIANT above.
- **Every test suite needs a wiring test:** Governs new features/components. This story adds no component — but see the [TEST] observation below: the *documented* invariant has no machine guard. Judged a non-blocking Improvement (the code is correct and pre-existing; this story didn't introduce the gap), captured as a Delivery Finding for follow-up rather than a scope expansion.

## Devil's Advocate

Let me argue this change is broken. First attack: **a comment is the weakest possible guard.** The story's entire premise is preventing a "stale-draft regression," yet the deliverable is prose a maintainer can ignore, delete, or refactor past without any machine catching it. The test-analyzer proved the teeth are missing: flip App.tsx:1351 from `peerReveals.reveals` to `mergedPeerReveals` and all 1744 tests stay green. So the story arguably fails its own stated goal — it documents the cliff edge instead of building the fence. That is the real finding, and I have confirmed and captured it; the mitigating fact is that the story's AC explicitly and deliberately scopes itself to "comment-guard only, no logic changes," so the missing test is a known boundary, not an oversight — but a reviewer who rubber-stamped without noticing the uncovered mirror invariant would have let a paper guard ship as if it were steel.

Second attack: **is the comment actually accurate, or does it lie with confidence?** A confidently-wrong guard comment is worse than none — it actively misleads. I pushed on all six claims: "defined just below" (true, 12 lines), "folds in TURN_STATUS submitted-status" (true, `mergePeerRevealsWithSubmittedStatus` overwrites status to submitted), "display-only" (true, single JSX consumer at 2262), "accumulator is canonical" (consistent with `persistedPeerActions.capture`), "keep this fed from peerReveals.reveals" (matches line 1351). No claim is contradicted by the code. Third attack: **does the comment introduce a maintenance trap** — e.g., naming a line number that will drift? It names symbols (`peerReveals.reveals`, `mergedPeerReveals`) and ADRs, not line numbers, so it resists drift. Fourth attack: **could the comment break the build** via an unterminated block or stray token? It is pure `//` line comments; `tsc --noEmit` is clean and eslint reports 0 errors. Fifth attack: **scope creep** — did the dev secretly change logic? Diff is +7/-0, all comment lines; the assignment is byte-identical. Conclusion: the change is correct and accurate; the only legitimate complaint (no machine guard) is real but out-of-scope for this story's explicit AC, and is now recorded as a follow-up. No Critical/High surfaced.

## Reviewer Assessment

**Verdict:** APPROVED

**Observations (5+):**
- [VERIFIED] Guard comment is factually accurate — App.tsx:1351 captures raw `peerReveals.reveals`; `mergedPeerReveals` is a display-only `useMemo` at App.tsx:1363 consumed only at App.tsx:2262. Complies with CLAUDE.md "comments must be accurate." Corroborated by comment-analyzer and rule-checker.
- [DOC] Comment-analyzer: clean — all six claims in the guard comment borne out by code; the deliverable (the comment) is sound. No misleading guidance introduced.
- [RULE] Rule-checker: clean — 0 violations across 13 TS checklist categories + 3 CLAUDE.md rules; the only live instance (comment correctness, check #13) is compliant.
- [TEST] Test-analyzer (high, **confirmed, non-blocking, Medium**): the documented invariant has no machine guard. Mirror display-direction is pinned in `turn-status-derivation-wiring.test.ts` (verified: "passes the merged peer reveals (not peerReveals.reveals directly) to GameBoard"); the accumulator direction is uncovered (my grep for a snapshot-capture source-text test returned nothing). Not blocking — the code is correct, the gap pre-existed this story, and the AC scopes to comment-only. Captured as a follow-up Delivery Finding.
- [SIMPLE] Not run (disabled). Self-assessed: +7/-0 comment-only diff, nothing to simplify; comment is concise and symbol-based (drift-resistant).
- [SEC] Not run (disabled). Self-assessed: no input handling, no data flow, no auth surface in a comment — no security surface.
- [TYPE] Not run (disabled). Self-assessed: no type declarations or casts added — no type-design surface.
- [EDGE] Not run (disabled). Self-assessed: no branches or boundaries added — no edge surface.
- [SILENT] Not run (disabled). Self-assessed: no error paths or fallbacks added — no swallowed-error surface.

**Data flow traced:** Peer ACTION_REVEAL → `usePeerReveals` raw map (`peerReveals.reveals`) → `peerRevealsSnapshotRef.current` snapshot → `persistedPeerActions.capture(currentRound, …)` accumulator. Safe because the snapshot reads the raw firewall-filtered map, not the display-merged `mergedPeerReveals` (which would inject TURN_STATUS-frozen status into the durable accumulator). The added comment documents exactly this seam.
**Pattern observed:** Prophylactic guard comment at a two-map split where the wrong sibling is a plausible refactor mistake — App.tsx:1343-1349.
**Error handling:** N/A — comment-only change, no error paths added or modified.

**Preflight:** 1744/1744 green, `tsc --noEmit` clean, eslint 0 errors (2 pre-existing warnings at 1323/1925, out of scope).

**Handoff:** To SM for finish-story.