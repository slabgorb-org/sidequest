---
story_id: "71-3"
jira_key: null
epic: null
workflow: "trivial"
---

# Story 71-3: WS reconnect error banner auto-clears on successful reconnect/turn round-trip

## Story Details

- **ID:** 71-3
- **Jira Key:** None (local sprint YAML only)
- **Workflow:** trivial
- **Stack Parent:** none

## Problem Summary

The WebSocket reconnect error banner (transient error, showing per-message rejections) does NOT automatically disappear when:
1. A WebSocket reconnection succeeds after a drop (socket reopens, OPEN state reached)
2. A turn round-trip completes successfully (player submits action → server processes → NARRATION_END arrives)

**Current state:**
- ReconnectBanner (amber "Reconnecting..." status bar) correctly clears when `isReconnecting` flips false on successful reconnect (see `useWebSocket.ts` line 259: `isReconnecting = hasEverOpened && !intentionalClose && !connected`)
- But the transient error banner (red/destructive "Your action couldn't be processed" text) persists indefinitely until the user manually clicks "Dismiss"

**Impact:**
- Players see stale error messages after the connection is restored, reducing confidence in the session's health
- Stale error text blocks visibility of subsequent valid rejections
- UX regression: the ReconnectBanner model (auto-clear on condition change) should apply to the transient error too

## Technical Approach

### Root Cause

The transient error state (`transientError: string | null`) is set in `App.tsx::handleMessage()` when an ERROR frame arrives with validation rejection (code != fatal), but there is **no effect** that clears it when:
- `isReconnecting` flips from true → false (successful reconnect)
- A turn round-trip completes (NARRATION_END arrives, `canType` re-enables)

The ReconnectBanner auto-clears because it's a pure presentational component with `visible={isReconnecting}` — when the hook prop flips, React re-renders. The transient error has no such wiring.

### Solution

Add an effect in `App.tsx` that monitors reconnection success and turn completion, and clears the transient error on either event:

1. **On successful reconnect:** When `isReconnecting` flips false AND `readyState === WebSocket.OPEN`, clear the error
   - Covers: WebSocket drops and recovers (mid-game, or on page reload where HMR restores state)
   - Timing: exact moment the socket is OPEN again

2. **On turn round-trip completion:** When NARRATION_END arrives (already sets `canType = true`), also clear the error
   - Covers: action was rejected → player retries → turn executes successfully → error should disappear
   - Timing: in the NARRATION_END branch of `handleMessage()` alongside the existing `setCanType(true)` call

**Why two signals?**
- Reconnect success clears errors from prior connection (pre-drop errors are stale)
- Turn completion clears errors from *this* action, right after it succeeds

**Test coverage:**
- Unit test: Create an effect wiring test in `.session/71-3-session.md`'s acceptance criteria to verify `setTransientError(null)` is called on the NARRATION_END path
- Wiring test: Verify reconnect-success clears the error in a scenario where transientError is set before reconnect fires

## Acceptance Criteria

### AC-1: Auto-clear on successful WebSocket reconnect

Given:
- A transient error banner is visible (e.g., "Your action couldn't be processed")
- The WebSocket is reconnecting (`isReconnecting === true`)

When:
- The reconnection succeeds and the socket reaches OPEN state
- `isReconnecting` flips false

Then:
- The transient error banner clears (`transientError` state becomes null)
- The ReconnectBanner ("Reconnecting...") simultaneously disappears

**Test scenario:** Simulate a validation error, drop the WS, wait for reconnect to succeed.

### AC-2: Auto-clear on turn round-trip completion

Given:
- A transient error banner is visible from a prior failed action (e.g., from a `session_unbound` recovery attempt)
- Player submits a retry action that succeeds

When:
- The server processes the action
- NARRATION_END arrives on the same turn

Then:
- The transient error banner clears as part of turn-completion
- The player sees the new narration without stale error text overlaid

**Test scenario:** Trigger a session-unbound error, player retries, NARRATION_END arrives.

### AC-3: Manual dismiss still works

Given:
- A transient error banner is visible

When:
- User clicks the "Dismiss" button

Then:
- The banner immediately clears (existing behavior preserved)

**Test scenario:** Existing dismissal flow unchanged.

### AC-4: No false clears

The error should NOT clear on:
- A reconnection attempt that fails (re-entering reconnect loop)
- An unrelated narration (e.g., from another player in MP)
- A transient error from a *different* action

**Test scenario:** Drop WS, reconnect fails after timeout (stays in reconnecting), error persists.

## Sm Assessment

Setup verified for peloton handoff to Dev (Major Winchester). This is a well-scoped UI bug in `sidequest-ui`: stale `transientError` banner never auto-clears after the connection recovers or a turn succeeds. Root cause and two clear-signals (socket OPEN on reconnect; NARRATION_END on turn completion) are identified; 4 ACs cover the happy paths plus the regression gate (manual dismiss) and the no-false-clear guard.

**Routing notes for the team:**
- Trivial workflow (setup → implement → review → finish). Dev owns implement and writes the tests inline (no separate TEA red phase). TEA stands by for verify assist if Dev wants a second pair of eyes on the effect-wiring test.
- AC-4 (no false clears) is the trap door — Dev must scope the clear to *successful* reconnect (OPEN reached) and *this-turn* NARRATION_END, not fire on every render or every narration frame. Reviewer: hold this as the focus check.
- Project doctrine: include a wiring test (effect actually mounted in App.tsx and reachable), not just a unit assertion that `setTransientError(null)` exists.
- Architect on standby — low architectural risk, no ADR implications.

Branch `feat/71-3-ws-reconnect-banner-autoclear` created off develop in sidequest-ui. Clear to hand to Dev.

## Delivery Findings

No upstream findings.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Improvement** (non-blocking): `sidequest-ui/src/__tests__/dice-overlay-wiring-34-5.test.ts` (the "NARRATION_END clears dice TARGET + result widget" test, ~line 275) is a **source-text wiring test** — it `readSrc("App.tsx")`, slices a fixed 2000-char window from the NARRATION_END branch, and regexes for `setDiceRequest(null)`/`setDiceResult(null)`. This violates CLAUDE.md "No Source-Text Wiring Tests" and proved the doctrine's point: my behavior-preserving edit pushed `setDiceResult(null)` past the 2000-char window and the test went red on a harmless change. I worked around it (placed the AC-2 clear at the *end* of the branch instead of widening the window or editing another story's test), but the test should be migrated to a behavioral test (render App, send DICE_REQUEST/RESULT then NARRATION_END, assert dice widgets clear). Affects `sidequest-ui/src/__tests__/dice-overlay-wiring-34-5.test.ts`. Recommend a separate chore. *Found by Dev during implementation.*
- **Improvement** (non-blocking): three unrelated files are modified-but-uncommitted in the `sidequest-ui` working tree and were carried into this branch at checkout — `src/__tests__/chrome-archetype-css.test.ts`, `src/index.css`, `src/styles/archetype-chrome.css`. Not part of 71-3; left untouched and NOT staged in my commit. Likely WIP from another peloton lane sharing the checkout. Worth confirming their owner so they aren't orphaned. *Found by Dev during implementation.*

### Reviewer (code review)
- No new upstream findings. I corroborate both of Dev's findings:
  (1) the brittle source-text test `dice-overlay-wiring-34-5.test.ts` should be migrated
  to a behavioral test (team-lead filed chore 71-9 — confirmed appropriate scope-out); and
  (2) the 3 uncommitted archetype-chrome files are another lane's WIP, correctly excluded
  from the 71-3 commit (verified via `git status --short` — they are unstaged, not in
  549e33e). Neither blocks 71-3. *Confirmed by Reviewer during code review.*

## Design Deviations

None.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **AC-2 clear placement: end of NARRATION_END branch, not adjacent to `setCanType(true)`**
  - Spec source: 71-3 session "Technical Approach" §2 + team-lead implement contract
  - Spec text: "in the NARRATION_END branch of `handleMessage()` alongside the existing `setCanType(true)` call"
  - Implementation: `setTransientError(null)` placed at the END of the NARRATION_END branch (after the existing dice-state clears) rather than immediately after `setCanType(true)`. Still inside the same NARRATION_END branch.
  - Rationale: Behavior is identical — React batches all setState calls within one handler, so ordering among them is immaterial. Placing it adjacent to `setCanType(true)` (as the literal contract said) pushed `setDiceResult(null)` past the fixed 2000-char window that the brittle source-text test `dice-overlay-wiring-34-5.test.ts` slices, turning that pre-existing test red on a harmless edit. End-of-branch placement keeps the existing test green without my editing another story's test or widening its brittle window. Logged the test itself as a delivery finding.
  - Severity: trivial
  - Forward impact: none — same branch, same turn-boundary semantics; AC-2 behavior (clear on turn completion) is unchanged and is covered by the new real-App wiring test.

### Reviewer (audit)
- **AC-2 clear placement at end of NARRATION_END branch** (Dev deviation above) → ✓ ACCEPTED
  by Reviewer. Behavior is provably identical: React batches all `setState` calls within a
  single event handler, and `setTransientError(null)` reads no frame field and has no
  ordering dependency on the co-located `setCanType(true)` / `setDiceRequest(null)` /
  `setDiceResult(null)` calls. End-of-branch placement was the correct call — widening or
  editing another story's brittle source-text window would have been worse. The root cause
  (the source-text test) is correctly punted to chore 71-9. No spec change needed.
- No undocumented deviations found. Both clear sites match the Technical Approach intent
  (socket-OPEN reconnect transition + NARRATION_END turn boundary).

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-ui/src/App.tsx` — (1) AC-1 reconnect effect tracking the true→false TRANSITION of `isReconnecting` (`prevIsReconnectingRef`) gated on `readyState === OPEN`; (2) AC-2 `setTransientError(null)` in the NARRATION_END branch, gated on `localTurnInFlightRef`
- `sidequest-ui/src/__tests__/transient-error-autoclear-wiring.test.tsx` (NEW) — real-App wiring tests via jest-websocket-mock

**`localTurnInFlightRef` arm/disarm (final, post Potter re-review):**
- ARM (every genuine local submit that round-trips to NARRATION_END): `handleSend` (text PLAYER_ACTION, non-aside) · `handleDiceThrow` beat-roll block (DICE_THROW w/ beat_id) · `handleYield` (YIELD)
- DISARM: both transient-error set sites (local action bounced) · every NARRATION_END boundary (unconditional)
- `auto_resolved` never arms (server resolved for the player — none of those handlers ran) → auto-resolved player's stale error survives → AC-4 hole stays closed.
- The dead `SESSION_EVENT{event:"waiting"}` arm was REMOVED — the server emits no such event (Potter-verified; zero in source/history).

**Tests:** Full client suite **1622/1622 passing** (160 files). New file: 9/9 passing.
- AC-1 (successful reconnect clears) — real App: drop 1006 → fresh server → reconnect OPEN → banner clears ✓
- AC-2 (LOCAL turn round-trip clears) — real submits via GameBoard stub forwarding App's own callbacks: text (`handleSend`) ✓, beat-roll (`handleDiceThrow`) ✓, yield (`handleYield`) ✓ → each → NARRATION_END → clears
- AC-3 (manual Dismiss still works) ✓
- AC-4 (no false clears), four guards:
  - (a) failed reconnect (no replacement server) keeps banner ✓
  - (b) streaming NARRATION frame (not a turn boundary) does not clear ✓
  - (c) **[hazard 2]** NARRATION_END for a turn the local player did NOT submit into (MP cross-player) does not clear ✓
  - (d) **[hazard 1]** error while connected-and-never-dropped not cleared by the reconnect effect (initial-mount/React edge) ✓

**Reviewer findings addressed:**
- *(b1b8221)* Hazard 1 — `prevIsReconnectingRef` transition tracking. Hazard 2 — `localTurnInFlightRef` MP-locality gate.
- *(1ee1a48, Potter re-review)* HIGH — armed the gate in `handleDiceThrow` beat block + `handleYield` (were missing → AC-2 regression for beat/yield turns). MEDIUM — dropped the dead `"waiting"` arm; reworked the AC-2 happy-path tests onto REAL submits through the production handlers (no synthetic server event).

**Wiring proof:** all nine tests drive the REAL `App` through a mocked WebSocket server; the AC-2 cases drive App's actual submit handlers via a GameBoard stub that forwards real callbacks — not source-text grep, not isolated unit assertions. Satisfies CLAUDE.md "Verify Wiring, Not Just Existence."

**Lint:** eslint clean on changed files (one pre-existing `displayName` exhaustive-deps warning at App.tsx:~1831 is unrelated). **Typecheck:** `tsc --noEmit` exit 0.
**OTEL:** Not applicable — cosmetic banner-clear UI change, no subsystem decision.
**Branch:** feat/71-3-ws-reconnect-banner-autoclear — commits 549e33e (impl) + b1b8221 (AC-4 hardening) + 1ee1a48 (Potter punch list), pushed. Squash at merge.

**Handoff:** To review phase (Colonel Potter). Both Reviewer-flagged AC-4 hazards are now covered by dedicated tests (c, d above).

## Subagent Results

Subagent toggles (`workflow.reviewer_subagents`): only `preflight` and `security` enabled;
the other seven disabled via settings and pre-filled as Skipped. (sidequest-ui JS/TS toolchain.)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 new (1618/1618 vitest; 5/5 target; tsc exit 0; 1 lint warning confirmed pre-existing/unrelated; 0 smells) | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — domain self-assessed (mount/transition + MP analysis below) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — domain self-assessed (no swallowed errors) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — domain self-assessed (5 behavioral tests reviewed below) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — domain self-assessed (comments accurate) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — domain self-assessed (effect deps, no `as any`) |
| 7 | reviewer-security | Yes | clean | 0 | confirmed 0, dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — domain self-assessed (minimal, no over-engineering) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — Rule Compliance done by Reviewer |

**All received:** Yes (2 enabled subagents returned; 7 disabled via settings, pre-filled as Skipped)
**Total findings:** 0 confirmed blocking, 0 dismissed, 0 deferred. Pre-existing items (lint
displayName warning, brittle source-text test) confirmed out of 71-3 scope.

## Reviewer Assessment

**Verdict:** APPROVED

A tight, well-reasoned bugfix with a genuine behavioral wiring test. Both trap-door
concerns from my pre-review scouting — the initial-mount/healthy-socket false-clear and the
MP cross-talk on NARRATION_END — were investigated in depth and come out clean, by both
code analysis and test evidence.

**Dispatched subagent coverage (tags):**
- `[SEC]` reviewer-security (enabled): CLEAN — `transientError` renders as a React text node
  (`App.tsx:2022`, `<span>{transientError}</span>`), no `dangerouslySetInnerHTML`; the
  set-site is pre-existing and runs `sanitizeErrorMessage()` (`:1119`); both new clear sites
  write `null`, not server content; no info leak (clears on success signals only, never
  while degraded); no new console logging; no frame-field trusted for a privileged action.
- `[EDGE]` (disabled — self-assessed): Both critical edges handled — see AC-1 transition
  analysis and AC-2 MP analysis below. No false-clear path exists.
- `[SILENT]` (disabled — self-assessed): No swallowed errors. The guard surfaces errors
  (keeps them visible while degraded) rather than hiding them — the opposite of a silent
  failure.
- `[TEST]` (disabled — self-assessed): 5 behavioral tests through the REAL `App` via
  jest-websocket-mock (message→state→banner), `mode: "multiplayer"`. Covers all 4 ACs plus
  two AC-4 guards (failed reconnect keeps banner; streaming NARRATION keeps banner). Specific
  assertions on `getByTestId`/`queryByTestId`, real socket-close codes (1006). One minor nit
  (L1 below). NOT a source-text grep — honors "No Source-Text Wiring Tests."
- `[DOC]` (disabled — self-assessed): The two new comment blocks (`:584-592`, `:1155-1168`)
  are accurate and load-bearing — they correctly explain WHY the effect is keyed on
  `[readyState, isReconnecting]` and not `transientError`, and why NARRATION_END (not
  streaming NARRATION) is the clear boundary. No stale/misleading docs.
- `[TYPE]` (disabled — self-assessed): No `as any`, no `@ts-ignore`, no non-null assertions.
  `useEffect` deps `[readyState, isReconnecting]` are exhaustive (setter is stable/exempt);
  no object/array-literal dep, no infinite loop. `tsc --noEmit` exit 0.
- `[SIMPLE]` (disabled — self-assessed): Minimal — a 4-line effect + one line in an existing
  branch. Reuses existing `transientError` state and the ReconnectBanner auto-clear pattern.
  No dead code, no over-engineering.
- `[RULE]` (disabled — self-assessed): See Rule Compliance below.

### Rule Compliance

TypeScript lang-review checklist (`.pennyfarthing/gates/lang-review/typescript.md`):

| # | Rule | Verdict |
|---|------|---------|
| 1 | Type-safety escapes | PASS — no `as any` / `@ts-ignore` / non-null assertion in diff |
| 2 | Generic/interface pitfalls | N/A |
| 3 | Enum anti-patterns | PASS — uses `MessageType.NARRATION_END` / `WebSocket.OPEN` correctly |
| 4 | Null/undefined handling | PASS — explicit `=== WebSocket.OPEN` and `!isReconnecting`; no `\|\|`-vs-`??` hazard |
| 5 | Module/declaration | N/A — no import changes |
| 6 | **React/JSX** | **PASS (key check)** — `useEffect` deps present & exhaustive, no infinite-loop literal dep, no `dangerouslySetInnerHTML`; effect correctly keyed to avoid re-clearing live errors |
| 7 | Async/Promise | N/A — synchronous handler + effect |
| 8 | Test quality | PASS (one nit L1) — behavioral, no `as any`, real mock types |
| 9 | Build/config | N/A |
| 10 | Type-level input validation | PASS — server error string sanitized at pre-existing set-site; diff writes `null` |
| 11 | Error handling | N/A — no `catch` in diff |
| 12 | Performance/bundle | N/A |
| 13 | Fix-introduced regressions | PASS — no `as any`/`\|\|` shortcuts introduced |

Project rules (`sidequest-ui/CLAUDE.md`):
- **No Silent Fallbacks** — PASS. The clear is gated on a *success* signal; degraded states keep the error visible.
- **No Stubbing** — PASS.
- **Wire Up What Exists** — PASS. Reuses `transientError` state + ReconnectBanner auto-clear model.
- **Verify Wiring, Not Just Existence** — PASS. `transient-error-autoclear-wiring.test.tsx` drives the real `App` end-to-end.
- **Every Test Suite Needs a Wiring Test** — PASS. That file *is* the wiring test.
- **No Source-Text Wiring Tests** — PASS. Behavioral assertions, no source grep. (The pre-existing offender `dice-overlay-wiring-34-5.test.ts` is correctly punted to chore 71-9.)
- **OTEL Observability** — N/A. Cosmetic banner-clear UI change; CLAUDE.md exempts cosmetic UI.

### AC-1 transition analysis (my "initial-mount false-clear" trap)

The effect `useEffect(() => { if (!isReconnecting && readyState === OPEN) setTransientError(null) }, [readyState, isReconnecting])` is **correct and cannot false-clear**:
- It re-runs only when `readyState` or `isReconnecting` change — NOT when `transientError`
  changes. So a rejection arriving on a healthy OPEN socket sets the error and the effect
  does not re-run → the error persists. (Empirically confirmed: every test's
  `connectAndRaiseError` raises the error on an OPEN/not-reconnecting socket and asserts the
  banner IS present, line 126-128.)
- On mount, `setTransientError(null)` may fire, but `transientError` is already `null` and no
  error can exist pre-OPEN (no message arrives before OPEN) → harmless no-op.
- The guard becomes true on a re-run ONLY via a transition INTO `(OPEN && !reconnecting)`,
  which requires having LEFT that state — i.e. a real drop→reconnect cycle (AC-1) or first
  connect (nothing to clear). A *failed* reconnect keeps `readyState != OPEN` / `isReconnecting
  true` → guard stays false → error survives (AC-4, tested).

### AC-2 MP analysis (my "peer NARRATION_END wipes my error" trap)

The new `setTransientError(null)` sits in the `NARRATION_END` branch **alongside the
pre-existing** `setCanType(true)`, `setConfrontationData(null)`, `setDiceRequest(null)`,
`setDiceResult(null)` — all per-client turn-boundary effects. If `NARRATION_END` fired on a
peer's turn, `setCanType(true)` would already wrongly unlock this client's input — a
pre-existing bug. It does not, because SideQuest's submit-and-wait barrier (root CLAUDE.md;
ADR-036) makes `NARRATION_END` a **shared round-boundary** signal: no narration until all
players submit, so a round cannot complete (NARRATION_END) while my action is outstanding/
rejected. The new clear therefore inherits the same trusted scoping — it lands only when the
shared round I participated in completes, which is exactly AC-2's intent. Streaming
`NARRATION` frames hit the outer `if` but NOT the inner `NARRATION_END` block, so peer/mid-turn
narration cannot clear it (AC-4, tested).

### Devil's Advocate

Trying to break it: **The "stale error from a prior round in MP" attack.** Could a
NARRATION_END from a round I didn't error in clear an error I'm still showing? Only if I had
an outstanding error AND a round completed without my valid submission. Under submit-and-wait
that can't happen — my rejected action blocks round completion until I resubmit successfully,
at which point clearing is correct. **The "rapid drop/reconnect flicker" attack:** each
OPEN-transition fires the clear, but there's nothing to clear unless an error was set, and an
error set mid-flicker (while not OPEN) correctly survives until a true OPEN-and-not-reconnecting
state. **The "unmounted setState" attack:** the effect could in theory call setState after
unmount, but React 18 no-ops this; RTL `afterEach`/`WS.clean()` covers the tests. **The
"streaming NARRATION race" attack:** a NARRATION frame can't reach the NARRATION_END clear
because of the message-type guard. **Confused-author/garbage-frame:** the effect reads no
frame content; the NARRATION_END clear reads no payload field — so a malformed frame can't
trigger an unexpected clear. The only thing the devil surfaced is the test-timing nit (L1),
which is a test-robustness concern, not a product defect. Nothing blocking.

### Non-blocking observations

- **[LOW / test-robustness] L1** — the AC-4 streaming-NARRATION test (`...wiring.test.tsx:169-170`)
  uses `await Promise.resolve()` then a synchronous `getByTestId` assert. For a *negative*
  assertion (banner must STILL exist) a single microtask flush is slightly weak: if a clear
  ever became async, the banner could be present at assert-time and removed later, passing
  falsely. Today the clear is synchronous setState within the handler, so it's correct, but a
  `waitFor` with a short negative hold (or `expect(...).not.toBeNull()` after a longer flush)
  would be more robust. Not required for approval. The other four tests use `waitFor` properly.
- **[INFO]** Pre-existing `react-hooks/exhaustive-deps` warning at `App.tsx:1778` (`displayName`)
  is unrelated to 71-3 (confirmed on develop) — not this story's concern.

**Data flow traced:** server ERROR frame → `sanitizeErrorMessage()` → `transientError` state
(`:1119`, pre-existing) → rendered as escaped text (`:2022`). Cleared by: (a) NARRATION_END
turn boundary (`:593`), (b) successful-reconnect effect (`:1165-1169`), (c) manual Dismiss
(`:2025`, untouched). Safe at every step.

**Pattern observed:** Clean reuse of the established ReconnectBanner auto-clear-on-condition
model, applied to `transientError` via a connection-state-keyed effect. Comments document the
non-obvious dependency-array reasoning.

**Error handling:** The change deliberately *preserves* error visibility during degraded
states (failed reconnect, mid-turn) and clears only on confirmed success — exactly the right
posture for a user-facing error banner.

**Handoff:** To SM (Hawkeye) for finish-story.

## Reviewer Re-Review — Hardening Delta (commit b1b8221)

**Context:** The first 71-3 commit (549e33e) was squash-merged to develop as #292. Dev had
also committed a SECOND commit (b1b8221) that hardens the exact two AC-4 hazards I raised in
the original review. Team-lead requested a re-review of this not-yet-merged delta before
creating a follow-up PR. Reviewed `git diff 549e33e..b1b8221` (2 files, +100/-20).

**Verdict:** REJECTED — changes requested.

The reconnect-transition hardening is correct and I commend it. But the turn-locality gate is
not armed for beat-roll / dice / yield turns, and it relies on a "waiting" signal the server
never emits — so the delta REGRESSES AC-2 ("auto-clear on turn round-trip completion") for
confrontation and yield turns relative to the now-merged develop baseline, which cleared
unconditionally.

**Subagents (re-run on delta):**
- `[SEC]` reviewer-security: CLEAN — pure client state; the gate is UI-cosmetic, no privilege, no new render/log/frame-trust.
- preflight: GREEN — full suite 1620/1620; target file 7/7 (incl. NEW MP cross-player test + NEW initial-mount/React-edge test); tsc exit 0; lint clean (1 pre-existing displayName warning); 0 smells.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | **AC-2 not satisfied for beat-roll/dice/yield turns.** `handleDiceThrow` (beat rolls → `DICE_THROW`) and `handleYield` (`YIELD`) are local turn submissions that round-trip to `NARRATION_END` server-side (`dice_throw.py` → `_execute_narration_turn`), but neither arms `localTurnInFlightRef`. With the new gate, a stale transient error will NOT auto-clear on these successful turns — a regression from develop (549e33e cleared unconditionally). Hittable in normal confrontation play. | `sidequest-ui/src/App.tsx` `handleDiceThrow` (~1455, the `if (beatId)` block) and `handleYield` (~1465) | Arm `localTurnInFlightRef.current = true` on these real local turn submissions (beat rolls and yield), mirroring the `handleSend` arm. |
| [MEDIUM] | **Dead "waiting" arm path + test that fabricates the signal.** Verified the server emits NO `SESSION_EVENT{event:"waiting"}` (zero occurrences in `sidequest-server/sidequest/**`, zero in git history via `git log -S'"waiting"'`, not among emitted event values). So the arm added at `App.tsx:642` is dead in production; the only LIVE arm is `handleSend`. The AC-2 happy-path test (`...wiring.test.tsx:142`) injects a synthetic `SESSION_EVENT{waiting}` the server never sends, then asserts the clear — validating a non-production path and giving false confidence. Dev's stated assumption ("'waiting' SESSION_EVENT is the authoritative local-submit signal") is incorrect. | `App.tsx:634-642`; `transient-error-autoclear-wiring.test.tsx:142` | Remove (or correctly wire server emission for) the dead "waiting" arm; drive the AC-2 test through the real submit path (`handleSend` text submit) and add beat/dice coverage. |

**What is correct (commended):**
- `[VERIFIED]` AC-1 transition tracking via `prevIsReconnectingRef` (`App.tsx:1184-1200`) — reads the captured old value BEFORE updating the ref, gates on `wasReconnecting && !isReconnecting && OPEN`. Correctly eliminates the initial-mount false-clear (false→false on first connect is not a recovery) and the healthy-socket false-clear. Ref mutated inside the effect (post-commit), not during render — no purity violation. No staleness/ordering bug. The NEW initial-mount test covers it.
- `[VERIFIED]` Disarm completeness: `NARRATION_END` (unconditional, after the guard), and both bounce paths (`:1133`, `:1153`) disarm. A spuriously-armed flag self-clears at the next turn boundary, so the gate cannot cause an AC-4 false-clear — the failure mode is strictly a missed clear (false negative), never a wrong clear.
- The AC-4 MP gate concept is sound; it just needs arms on all local-submit modalities.

**Note on AC-4:** This delta does NOT regress AC-4 — no false-clear path exists. Both findings
are false-negative (error lingers) gaps, not false-positives. The canonical text-retry AC-2
scenario DOES work in production (handleSend arms). The gap is specific to beat/dice/yield turns.

**Recommended path:** The HIGH fix is ~2-3 lines (arm in `handleDiceThrow`'s `if (beatId)` block
+ `handleYield`). Recommend Dev applies it plus the test correction rather than shipping the
gap. Alternatively the team may consciously accept the beat/dice/yield gap as a documented
limitation with a follow-up chore — but that is a product call to make WITH this information,
not silently. I am not approving the delta as-is.

**Handoff:** Back to Dev (Major Winchester) for the arm-site fix + test correction; team-lead to decide accept-gap vs. fix.

### Addendum — protocol proof + answers to team-lead's stress questions

**"waiting" is confirmed dead at the protocol level (finding #2 upgraded from "appears dead" to PROVEN):**
- `SessionEventPayload.event` (sidequest-server `protocol/messages.py:346`) documents the ONLY valid values: `'connect', 'connected', 'ready', 'theme_css'`. No "waiting".
- Server emits exactly three SESSION_EVENT event values: `connected`, `theme_css`, `ready` (`handlers/connect.py:1041/1069/1347`). Zero `event="waiting"` emissions anywhere (all forms checked).
- The real MP submit signal is `TURN_STATUS` with per-player entry states (`submitted` / `auto_resolved` / `resolved`, `protocol/messages.py:484`). The UI receives TURN_STATUS (`App.tsx:336` `turnStatusEntries`) but does NOT use it to arm `localTurnInFlightRef`.
- Conclusion: the arm at `App.tsx:642` (`event === "waiting"`) never fires in production. It is a Rust-era leftover the Python port did not carry. The only LIVE arm is `handleSend`.

**Q1 — Is "waiting" vs "auto_resolved" mutual-exclusivity the load-bearing invariant? NO.**
The invariant as stated is a mischaracterization because "waiting" is never emitted. The
auto_resolved false-clear hole IS closed by b1b8221, but the actual mechanism is: an
auto-resolved local player never calls `handleSend` (the sole live arm), so the ref stays
false and their stale error correctly survives the round's NARRATION_END. The protection is
real — but it rests on handleSend-is-the-only-arm, not on waiting/auto_resolved exclusivity.

**Q2 — Any path where a legit local submit fires NEITHER handleSend NOR "waiting" (missed clear)? YES, several:**
- Beat rolls (`handleDiceThrow` → `DICE_THROW`) — no handleSend, no "waiting".
- Yield (`handleYield` → `YIELD`) — same.
- **Reconnect / HMR resubmit** — Dev explicitly intended "waiting" to cover this ("covers
  reconnect/HMR where the optimistic handleSend arm didn't run"). Since "waiting" is dead,
  this case is ALSO a missed clear. Dev's own stated coverage case is unhandled.

**Net:** b1b8221 correctly closes the narrow auto_resolved AC-4 false-clear hole present in the
merged 549e33e — good. But it does so while introducing AC-2 missed-clears for beat/dice/yield
and failing to deliver the reconnect/HMR coverage it claims, because the "waiting" backstop
does not exist. Verdict unchanged: REJECTED. Correct fix: arm at the real submit sites
(`handleDiceThrow` beat block + `handleYield`), remove the dead `:642` "waiting" arm (or
replace with the real `TURN_STATUS{submitted}`-for-local-player signal if reconnect/HMR
coverage is wanted), and make the AC-2 test drive `handleSend` + a beat/dice case instead of a
fabricated "waiting" frame.

## Reviewer Re-Review #2 — Fix (commit 1ee1a48)

**Verdict:** ✅ APPROVED.

Dev addressed both findings cleanly. Re-reviewed `git diff 549e33e..1ee1a48`.

**HIGH (AC-2 beat/dice/yield gap) — RESOLVED.** `localTurnInFlightRef` is now armed in
`handleDiceThrow`'s `if (beatId)` block (`App.tsx:1465`) and `handleYield` (`:1482`), joining
the `handleSend` arm (`:1280`). I verified these three are the EXHAUSTIVE set of local-submit
paths that produce a NARRATION_END turn boundary — enumerated all 7 `send()` sites: the other
four (CLIENT_ERROR crash `:1232`, SESSION_EVENT{connect} `:1820`, chargen respond `:1215`,
ORBITAL_INTENT) do not produce a local turn-completion NARRATION_END and correctly do not arm.
Tests 1-3 drive each real handler and assert the clear.

**MEDIUM (dead "waiting" arm + fabricated-signal test) — RESOLVED.** The dead arm at the old
`:642` `event === "waiting"` branch is removed (the branch no longer touches the ref). The
AC-2 tests no longer inject a synthetic `SESSION_EVENT{waiting}` — they drive real
text/beat-roll/yield submits through the production handlers.

**Judgment call (team-lead's Q): is there an AC-2 gap from NOT adopting the TURN_STATUS{submitted} arm for reconnect/HMR? — NO. I CONCUR.**
For a missed-clear you need, simultaneously: (a) `transientError` non-null, (b) a NARRATION_END
for a turn the local player submitted, (c) `localTurnInFlightRef` false. Trace:
- Error set BEFORE drop → cleared by AC-1's `prevIsReconnectingRef` effect on the reconnect transition. No AC-2 needed.
- Error set AFTER reconnect, then retry → the retry is a local submit through one of the three armed handlers → arms → NARRATION_END clears. Covered by AC-2.
- Mid-turn reconnect WITHOUT remount → `useRef` persists across reconnect, so an armed turn stays armed → clears. No gap.
- HMR / full reload (remount) → React resets `transientError` (useState→null) AND `localTurnInFlightRef` (useRef→false) TOGETHER (same component, same Fast Refresh boundary — they cannot diverge). Nothing to clear; ref correctly false. No gap.
Conditions (a) and (c) can only co-occur via a remount between submit and NARRATION_END — but a
remount nulls the error, so they cannot co-occur. The `TURN_STATUS{submitted}` arm would be
strictly redundant. The reconnect/HMR scenario is fully covered by AC-1 (error-before-drop) and
the per-handler arms (error-after-reconnect retry). No residual AC-2 gap.

**Kept-correct (re-verified):** `prevIsReconnectingRef` transition gate; unconditional
NARRATION_END disarm + both bounce-path disarms (so a bounced action's error survives until an
active retry — AC-4 preserved); MP cross-player + connected-never-dropped negative tests.

**Subagents:** preflight GREEN — full suite 1622/1622; target 9/9 (3 AC-2 real-handler cases +
2 AC-4 negatives + AC-1/AC-3); tsc exit 0; lint clean (1 pre-existing displayName warning, no
new hook warnings from the ref writes); zero smells. Security previously CLEAN on the mechanism
(pure client state, UI-cosmetic gate, no new render/log/frame-trust); the fix adds only two ref
writes at submit sites — no new security surface.

**No AC-4 regression** anywhere in the fix — all residual failure modes remain missed-clears
(false negatives), never false-clears, and the beat/dice/yield missed-clears are now closed.

**Handoff:** APPROVED → team-lead to PR the delta to develop and finish 71-3. Good work, Major Winchester.