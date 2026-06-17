---
story_id: "125-5"
jira_key: ""
epic: "125"
workflow: "trivial"
---
# Story 125-5: Harden the FATE_ROLL boundary guard (118-7): validate Fudge face values in {-1,0,1}, not just dice-tuple length

## Story Details
- **ID:** 125-5
- **Jira Key:** (none — no Jira integration for this project)
- **Workflow:** trivial
- **Stack Parent:** none
- **Repos:** sidequest-ui

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-17T17:56:39Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-17T16:46:22+00:00 | 2026-06-17T16:46:22+00:00 | 0s |
| implement | 2026-06-17T16:46:22+00:00 | 2026-06-17T17:49:07Z | 1h 2m |
| review | 2026-06-17T17:49:07Z | 2026-06-17T17:56:39Z | 7m 32s |
| finish | 2026-06-17T17:56:39Z | - | - |

## Story Context

**Scope:** Harden the FATE_ROLL boundary guard in `sidequest-ui/src/hooks/useStateMirror.ts` to validate not just the structure of the dice tuple (4-element array) but also each face value.

**Background:** Story 118-7 (ADR-144 F3g) wired the Fate roll surface end-to-end, including a boundary guard at the UI message handler. The guard currently validates:
```
!Array.isArray(p.dice) || p.dice.length !== 4
```

This drops payloads with missing or wrong-length dice arrays. However, it does NOT validate that each face is in the valid Fudge die range {-1, 0, 1}. A malformed payload with valid-length but out-of-range faces renders a wrong glyph via `FateDiceTray.faceGlyph()` (which degrades any out-of-range value to '0').

**Risk Assessment:** Defense-in-depth hardening, NOT a security vulnerability.
- Cannot crash the browser (React escapes text)
- Cannot exfiltrate data
- Cannot escalate privilege
- Server always emits valid faces via `build_fate_roll_payload()`, so the realistic attack surface is nil today
- Captured as a finding by both the security subagent AND the Reviewer's own analysis during 118-7 (sprint/archive/118-7-session.md, Reviewer Observations `[EDGE]`)

**Technical Approach:**
1. Extend the FATE_ROLL guard in `useStateMirror.ts` to validate face values
2. Drop (with `console.error`) a malformed roll that fails the face-value check, matching the existing drop behavior for missing/wrong-length dice
3. Add a regression test to verify a roll with out-of-range faces is rejected

**Acceptance Criteria:**

AC1: The FATE_ROLL guard tightens to require `p.dice.every(d => d === -1 || d === 0 || d === 1)`
- The expanded guard checks both length AND valid face values
- A roll failing the face-value check is dropped with a loud `console.error`, matching the existing missing-dice drop behavior
- Uses the established No-Silent-Fallbacks pattern

AC2: Regression test added for face-value validation
- File: `sidequest-ui/src/hooks/__tests__/useStateMirror.fateRoll.test.ts` (if not already present; extend the existing test suite if the file exists)
- Test case: a FATE_ROLL payload with `p.dice = [2, 1, 0, -1]` (a face of 2, out of range) is rejected, NOT stored in state
- Test case: a FATE_ROLL payload with `p.dice = [-5, 0, 1, 1]` (a face of -5, out of range) is rejected, NOT stored in state
- Test case: a valid FATE_ROLL with `p.dice = [-1, 0, 0, 1]` (all faces in range) is accepted and stored as `latestFateRoll`
- The test reports the rejection to `console.error` (verify spy or mock)

AC3: Build and lint pass
- `npm run build` succeeds (or `just client-build` from orchestrator root)
- ESLint clean on changed files
- TypeScript build succeeds (tsc -b or equivalent)

**Branch Strategy:** gitflow (feat/125-5-{slug})
- Base: `sidequest-ui` repository, `develop` branch
- Branch name: `feat/125-5-harden-fate-roll-guard`

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `src/hooks/useStateMirror.ts` — FATE_ROLL boundary guard now also rejects out-of-range faces (`!p.dice.every(d => d === -1 || d === 0 || d === 1)`), dropping the roll with the existing loud `console.error`. (AC1)
- `src/hooks/__tests__/useStateMirror.fateRoll.test.ts` — added a "face-value boundary (Story 125-5)" describe block: rejects face=2, rejects face=-5, accepts all-in-range and stores it, keeps prior valid roll on a range violation; `console.error` spy asserted. (AC2)
- `src/types/payloads.ts` — added `[key: string]: unknown` to `FateThrowPayload` to fix a pre-existing 126-7/ADR-148 build break (out-of-scope one-liner, folded in per Mortal's decision; see Design Deviations + Delivery Findings). (AC3 unblock)

**Tests:** 9/9 passing (GREEN) — `useStateMirror.fateRoll.test.ts`
**Build:** `npm run build` succeeds (tsc -b + vite) — was RED on clean develop, now green. (AC3)
**Lint:** ESLint clean on all three changed files. (AC3)
**Branch:** feat/125-5-harden-fate-roll-guard (sidequest-ui, base develop) — pushed

**Handoff:** To review (Hermes Psychopompos). Note the blocking Delivery Finding: 126-7's verify/review did not run the TS build; recommend the verify gate run `npm run build`, not just vitest.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — tests 9/9, lint clean, build green, tree clean |
| 2 | reviewer-edge-hunter | Yes | findings | 9 (1 high, 3 med, 5 low/completeness) | 0 confirmed-blocking; 3 deferred as non-blocking Delivery Findings (all pre-existing / out-of-scope); 6 dismissed as pre-existing-not-regression or completeness-confirmations |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — self-assessed below ([SILENT]) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — self-assessed below ([TEST]) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — self-assessed below ([DOC]) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — self-assessed below ([TYPE]) |
| 7 | reviewer-security | Yes | findings | 2 (both low) | 0 confirmed-blocking; 2 deferred as non-blocking Delivery Findings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — self-assessed below ([SIMPLE]) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — self-assessed below ([RULE] / Rule Compliance) |

**All received:** Yes (3 enabled returned: preflight, edge-hunter, security; 6 disabled via `workflow.reviewer_subagents` and pre-filled as Skipped)
**Total findings:** 0 confirmed-blocking, 5 deferred as non-blocking Delivery Findings, 6 dismissed (pre-existing-not-regression / completeness)

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** server `build_fate_roll_payload()` → WebSocket FATE_ROLL frame → `useStateMirror` boundary guard (`useStateMirror.ts:280`) → `latestFateRoll` → `FateDiceTray.faceGlyph`. The new clause `!p.dice.every(d => d === -1 || d === 0 || d === 1)` is the runtime validation that the pre-existing `as unknown as FateRollPayload` cast otherwise lacks. Safe: it is strictly more restrictive than the prior length-only check and never widens what was accepted.

**Pattern observed:** `[key: string]: unknown` on `FateThrowPayload` (`payloads.ts:619`) matches the established sibling-payload pattern (same index signature at `payloads.ts:78` and `:325`) used to satisfy `GameMessage.payload: Record<string, unknown>` assignability. Consistent, not novel.

**Error handling:** malformed roll dropped with loud `console.error` + `continue`, prior valid roll preserved (`useStateMirror.ts:286`). No-Silent-Fallbacks compliant.

**Observations (tagged by source):**
- `[EDGE]` **[LOW — non-blocking, PRE-EXISTING, not a regression]** null/non-object `msg.payload` crashes the guard at `!Array.isArray(p.dice)` (`useStateMirror.ts:281`). Verified the original develop guard dereferences `p.dice` identically (`git show develop:…` — same line), and the new `.every()` clause only runs after `Array.isArray(p.dice)` is true (p proven non-null). **My diff introduces zero new null-deref risk.** Captured as a follow-up Delivery Finding; does NOT block 125-5.
- `[EDGE]` **[MEDIUM — non-blocking, out-of-scope, PRE-EXISTING]** the guard validates only the `dice` tuple; a payload with valid dice but missing/wrong-typed `throw_params` passes and could crash `replayThrowParams` on the Three.js mount. Story scope is dice faces only; the prior guard had the same gap. Deferred as a Delivery Finding.
- `[EDGE]` **[LOW]** `-0` passes `=== 0` and is stored as `-0`; `faceGlyph(-0)` renders `'0'` correctly (display-correct), latent identity-comparison hazard only. Server emits integer 0, so surface is nil. Noted.
- `[EDGE]` `[VERIFIED]` NaN, float (0.5), boolean, string, null-element, and non-array-iterable (Set/TypedArray) faces are all correctly rejected by strict `===` + `Array.isArray` — evidence: `useStateMirror.ts:282-285`, confirmed by edge-hunter's enumeration.
- `[SEC]` **[LOW — non-blocking]** index signature is a latent unsanitized-field-forwarding vector *only if* a future call site spread-merges server data into a `FateThrowPayload` before `send()`; no such merge exists today. Deferred as a Delivery Finding (with the security agent's wrapper-intersection alternative noted).
- `[SEC]` **[LOW — non-blocking]** `console.error` logs the full rejected payload; `FateRollPayload` carries no PII/credentials (dice faces, ladder math, seed, tier), benign in a same-origin browser threat model. Noted.
- `[SILENT]` *(subagent disabled — self-assessed)* `[VERIFIED]` the only error path drops with `console.error` (loud) and preserves the last valid roll; no swallowed errors, no empty catch, no silent default substituted — evidence: `useStateMirror.ts:286-287`. No-Silent-Fallbacks compliant.
- `[TEST]` *(subagent disabled — self-assessed)* `[VERIFIED]` 4 new tests cover reject-2, reject-(-5), accept-in-range, keep-prior-valid; `console.error` spy asserted **both** directions (`toHaveBeenCalled` on reject, `not.toHaveBeenCalled` on accept) — evidence: `useStateMirror.fateRoll.test.ts:130-162`. `beforeEach`/`afterEach` restore the spy (no mock leak). Minor coverage gap: no explicit float/NaN test, but strict `===` covers them and is asserted indirectly; non-blocking.
- `[DOC]` *(subagent disabled — self-assessed)* `[VERIFIED]` the new inline comments accurately describe the face-validation rationale (`useStateMirror.ts:275-279`) and the index-signature genesis (`payloads.ts:615-618`); no stale/misleading docs introduced.
- `[TYPE]` *(subagent disabled — self-assessed)* `[VERIFIED]` index signature uses `unknown`, not `any` (TS checklist #2 compliant); declared properties remain narrowly typed (every named type is assignable to `unknown`). The `as unknown as FateRollPayload` double-cast (TS checklist #1) is **pre-existing context**, not introduced by this diff.
- `[SIMPLE]` *(subagent disabled — self-assessed)* `[VERIFIED]` the `.every()` predicate and the one-line index signature are the minimal expressions of both fixes; no dead code, no over-engineering.
- `[RULE]` *(subagent disabled — self-assessed)* see `### Rule Compliance` below — all applicable TypeScript lang-review checks pass.

### Rule Compliance (TypeScript lang-review checklist)

- **#1 Type-safety escapes:** `as unknown as FateRollPayload` exists at `useStateMirror.ts:280` but is **pre-existing** (unchanged context); the diff adds the runtime `.every()` validation that the cast lacked — net improvement. No new `as any`, `@ts-ignore`, or non-null assertion. ✓
- **#2 Generic/interface pitfalls:** `[key: string]: unknown` (not `Record<string, any>` / not `any`). Compliant inline form of the recommended `Record<string, unknown>`. ✓
- **#4 Null/undefined:** face check uses strict boolean `===` comparisons, not `||`/`??` defaults — no falsy-coercion bug. ✓ (The pre-existing null-`p` deref is flagged as a non-blocking finding, not a checklist violation introduced here.)
- **#6 React/JSX:** change is inside the hook's message-loop body, not a `useEffect`/`useMemo` deps array; no hook-deps regression, no `dangerouslySetInnerHTML`. ✓
- **#8 Test quality:** no `as any` in assertions; `vi.spyOn` mock typed via `ReturnType<typeof vi.spyOn>`; tests import from `src/`, not `dist/`. ✓
- **#10 Input validation:** this diff **is** the runtime validation at the WebSocket boundary that checklist #10 asks for. ✓
- **#13 Fix-introduced regressions:** the folded build-fix (index signature) re-scanned — uses `unknown`, adds no `||`/`as any`. ✓

### Devil's Advocate

Suppose this code is broken. The loudest attack is the null payload: a malicious or buggy server sends `{"type":"FATE_ROLL","payload":null}`. `p` is `null`, `!Array.isArray(p.dice)` throws, and the entire `useStateMirror` replay loop dies — every subsequent message in the batch is dropped and the client white-screens. That is a genuine, reachable crash. But it is **pre-existing**: develop's guard dereferences `p.dice` on the same line, so 125-5 neither caused nor worsened it, and the realistic surface is nil because the server's `build_fate_roll_payload()` only ever emits a populated object. A confused future author is the second threat: the new index signature on `FateThrowPayload` silently swallows excess-property checks, so someone spread-merging an inbound `Record<string, unknown>` frame into an outbound throw payload would forward arbitrary fields to the server with no compile error — the security agent's latent-forwarding finding. Again, no such call site exists today. Third, a stressed consumer: `-0` survives the face check and is stored verbatim; any future code doing `Object.is(face, 0)` or set-membership would misbehave, though `faceGlyph` and `JSON.stringify` both normalize it. Fourth, the test suite: it asserts the spy fired on rejection but does not pin *which* message logged, so a refactor that logged twice would still pass — a vacuity risk, but low. None of these four rise to Critical/High **for this diff**: the crash and the field-forwarding are pre-existing or latent-with-no-call-site, the `-0` is display-correct, and the test vacuity is marginal. The change does exactly what its AC demands, is strictly more restrictive than before, and is covered by four green tests. The right disposition is APPROVE-with-follow-up-findings, not reject — but the null-payload guard genuinely deserves its own hardening story, because "the server always sends valid data" is precisely the assumption a boundary guard exists to stop trusting.

**Handoff:** To SM (Themis the Just) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

No upstream findings.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Gap** (blocking): Story 126-7 / ADR-148 shipped a build-broken `develop` — `tsc -b` fails because `FateThrowPayload` lacks the `[key: string]: unknown` index signature required to send it as a `GameMessage` (`App.tsx:2010` `handleFateThrow`). Build break predates and is unrelated to 125-5 (confirmed via stash + rebuild). Fixed one-liner here per Mortal's scope decision. Affects `sidequest-ui/src/types/payloads.ts` (added index signature) — but the real process gap is that **126-7's verify/review did not run `npm run build`**; the trivial/tdd verify gate should run the TS build, not just vitest, so a red `tsc -b` can't merge again. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (non-blocking): A `null`/non-object FATE_ROLL `msg.payload` crashes the `useStateMirror` replay loop at `!Array.isArray(p.dice)` (white-screens the client). Affects `sidequest-ui/src/hooks/useStateMirror.ts` (FATE_ROLL branch — add a `!p || typeof p !== 'object'` pre-check). **Pre-existing** (identical on develop) and not introduced by 125-5; realistic surface nil today (server emits valid objects), but deserves its own hardening story since a boundary guard exists precisely to stop trusting "the server always sends valid data." *Found by Reviewer during code review.*
- **Gap** (non-blocking): The FATE_ROLL guard validates only the `dice` tuple, not `throw_params`; a payload with valid dice but missing/wrong-typed `throw_params` passes and can crash `replayThrowParams` on the Three.js mount. Affects `sidequest-ui/src/hooks/useStateMirror.ts` (extend the guard or guard at the tray). Pre-existing, out of 125-5 scope. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): No client-side guard on outbound `FateThrowPayload.face` before `send()` (126-7/ADR-148 path); the index signature now also suppresses wrong-type compile errors on outbound fields. Affects `sidequest-ui/src/components/.../FateThrowerTray` / `App.tsx` `handleFateThrow` (assert `face.length === 4 && every dF` pre-send). Server remains the validation authority; this would catch dice-lib settle bugs before the wire. The security agent's alternative — keep `FateThrowPayload` closed and widen only at the wrapper (`FateThrowPayload & Record<string, unknown>`) — is noted but conflicts with the established sibling-payload index-signature pattern, so low priority. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

1 deviation

- **Folded a one-line out-of-scope build fix into this story (FateThrowPayload index signature)**
  - Rationale: AC3 (build passes) is unsatisfiable while develop is build-broken. Root cause is a pre-existing 126-7/ADR-148 regression: `handleFateThrow` at `App.tsx:2010` sends a `FateThrowMessage` whose `FateThrowPayload` lacks the `[key: string]: unknown` index signature that the `GameMessage` union (`payload: Record<string, unknown>`) requires; sibling sent payloads carry it. One-line, low-risk, same Fate feature family. User (Mortal) explicitly chose "Fold 1-line fix into 125-5" when presented the scope fork.
  - Severity: minor
  - Forward impact: minor — turns develop's build green again; no behavior change. The deeper gap (126-7 shipped a red build) is captured as a blocking Delivery Finding below.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Folded a one-line out-of-scope build fix into this story (FateThrowPayload index signature)**
  - Spec source: 125-5 session, AC3
  - Spec text: "Build and lint pass — `npm run build` succeeds … TypeScript build succeeds"
  - Implementation: Added `[key: string]: unknown` to `FateThrowPayload` in `src/types/payloads.ts`, beyond the guard-only scope, because `develop`'s `tsc -b` was already RED — independent of this story's two intended files (verified by stashing my changes and rebuilding clean develop).
  - Rationale: AC3 (build passes) is unsatisfiable while develop is build-broken. Root cause is a pre-existing 126-7/ADR-148 regression: `handleFateThrow` at `App.tsx:2010` sends a `FateThrowMessage` whose `FateThrowPayload` lacks the `[key: string]: unknown` index signature that the `GameMessage` union (`payload: Record<string, unknown>`) requires; sibling sent payloads carry it. One-line, low-risk, same Fate feature family. User (Mortal) explicitly chose "Fold 1-line fix into 125-5" when presented the scope fork.
  - Severity: minor
  - Forward impact: minor — turns develop's build green again; no behavior change. The deeper gap (126-7 shipped a red build) is captured as a blocking Delivery Finding below.

### Reviewer (audit)
- **Folded a one-line out-of-scope build fix into this story (FateThrowPayload index signature)** → ✓ ACCEPTED by Reviewer: the build break was independently confirmed pre-existing (`git show develop` + stash-rebuild), the fix uses `unknown` (not `any`) and matches the established sibling-payload index-signature pattern (`payloads.ts:78`, `:325`), it is the minimal change to restore `GameMessage` assignability, and the scope expansion was explicitly authorized by Mortal. No new behavior, build now green. The deeper process gap (126-7's verify gate didn't run `tsc -b`) is a valid blocking process finding for follow-up — agreed; the code-level break itself is resolved on this branch.
- No undocumented deviations found. The diff matches the logged scope: guard change (AC1), tests (AC2), build-fix index signature (AC3 unblock).