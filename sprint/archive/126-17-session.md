---
story_id: "126-17"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 126-17: [FATE] Build the Fate defend-throw UI surface — handle FATE_DEFEND_REQUEST + defend tray (4dF thrower) + concede affordance; un-hangs the 126-8 DEFEND barrier

## Story Details
- **ID:** 126-17
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-19T11:20:06Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-19T10:23:36Z | 2026-06-19T10:25:46Z | 2m 10s |
| red | 2026-06-19T10:25:46Z | 2026-06-19T10:42:04Z | 16m 18s |
| green | 2026-06-19T10:42:04Z | 2026-06-19T10:55:35Z | 13m 31s |
| review | 2026-06-19T10:55:35Z | 2026-06-19T11:04:57Z | 9m 22s |
| red | 2026-06-19T11:04:57Z | 2026-06-19T11:11:45Z | 6m 48s |
| green | 2026-06-19T11:11:45Z | 2026-06-19T11:15:24Z | 3m 39s |
| review | 2026-06-19T11:15:24Z | 2026-06-19T11:20:06Z | 4m 42s |
| finish | 2026-06-19T11:20:06Z | - | - |

## Story Context

**Repos:** sidequest-ui

**Branch Strategy:** gitflow (feat/126-17-fate-defend-throw-ui)

**Story Type:** UI/Feature

**Points:** 5

**Acceptance Criteria:**
1. FATE_DEFEND_REQUEST MessageType added to protocol.ts
2. 'defend' entry added to action union in payloads.ts (~line 614)
3. Defend tray component renders 4dF dice thrower (REUSE 126-7's FateDiceTray pattern)
4. handleFateThrow + makeFateThrowMessage patterns wired for defend throws
5. Concede affordance available + wired to server concede field (from 126-14)
6. FATE_DEFEND_REQUEST hangs resolved: UI no longer drops unknown message

**Notes:**
- Reuse 126-7 patterns (FateConflictSurface, FateDiceTray thrower mode)
- Server half (126-8 DEFEND barrier broadcast + 126-14 concede field) already merged
- This is UI-ONLY work — do NOT add server changes
- Blocks on: 126-8 DEFEND barrier server broadcast (already live), 126-14 concede field (merged PR #959)

## Sm Assessment

**Story selected:** 126-17 — the lone p1 in the backlog and a latent **showstopper**. Until this lands, the first NPC attack in any Fate conflict broadcasts `FATE_DEFEND_REQUEST`, the server parks at `fate_throw.py:161-173`, the UI drops the unknown message, and the exchange hangs forever.

**Scope is UI-ONLY (sidequest-ui).** This is the load-bearing fact for the whole pipeline. The server half is already in production:
- 126-8 shipped the DEFEND barrier (broadcasts `FATE_DEFEND_REQUEST`, blocks-and-waits, no auto-roll).
- 126-14 shipped the server-side concede field (merged PR #959, confirmed in `main` git log).
This story *consumes* those existing server messages. **No server, content, or daemon changes** — if the RED tests reach for a server file, that's scope creep; bounce it back.

**Reuse mandate (do not reinvent — CLAUDE.md doctrine):** 126-7 already built the Fate UI plumbing this story extends — `FateConflictSurface`, `FateDiceTray` (thrower mode), `handleFateThrow`, and `makeFateThrowMessage`. The defend tray is a *thrower-mode reuse* of `FateDiceTray`, not a new component. Verify these symbols exist in the UI before authoring against them.

**Wiring gate (CLAUDE.md — every test suite needs a wiring test):** the RED suite must include at least one integration-level test proving the new `FATE_DEFEND_REQUEST` MessageType is actually handled in the live socket/message dispatch path — not merely that a defend-tray component renders in isolation. The whole point of the story is that the message currently gets *dropped*; an isolated render test would pass while the hang persists.

**Player-UI surface (audience note):** this is a player-facing mechanical surface. Per CLAUDE.md (Sebastien/Jade mechanics-first in player UI), the 4dF defend throw and its math should be legible to the player. This is a player-UI concern, not an OTEL/observability one.

**AC source of truth:** the six ACs in Story Context above. No ambiguity flagged; the spec section 8 patterns from 126-7 are the template. Handing to TEA (Fezzik) for the RED phase.

## TEA Assessment

**Tests Required:** Yes
**Reason:** 5-pt feature story; pure UI behavior across four layers. RED-verified.

**Test Files:**
- `sidequest-ui/src/types/__tests__/fate-defend-protocol.test.ts` — AC1: protocol/payload contract pinned to the SERVER source of truth (`protocol/fate.py`). `MessageType.FATE_DEFEND_REQUEST`, `FateDefendRequestPayload` (6 fields), `FateThrowPayload.action += 'defend'`, `FateThrowPayload.concede`. (Typed-literal constructions are compile-time guards under `tsc -b`; the `MessageType` value assertion is the runtime RED anchor — mirrors `fate-protocol.test.ts`.)
- `sidequest-ui/src/components/__tests__/FateConflictSurface.defend.test.tsx` — AC2/3/4/5: defend tray mounts on a request targeting the local PC, reads attacker/skill/total **from the payload** (118-5 anti-drift, asserted twice with different values), settle emits `FATE_THROW(action='defend')` echoing `request_id` + faces (reuse FateDiceTray thrower), Concede folds (concede=true, no faces), tray consumed/dismisses after answer. Drives the dF gesture via the 126-7 dice-lib `sceneProps` capture harness.
- `sidequest-ui/src/hooks/__tests__/useStateMirror.fate-defend.test.ts` — AC6 (wire→mirror): `latestFateDefendRequest` EVENT slice (most-recent-wins, starts null) + **No-Silent-Fallbacks boundary guard** (defender-less request dropped, slice unchanged). Mirrors the FATE_ROLL/FATE_STATE guards.
- `sidequest-ui/src/components/GameBoard/__tests__/GameBoard-fate-defend-wiring.test.tsx` — AC6 (mirror→tray): the **mandatory wiring test** — renders the real GameBoard, activates the Fate Conflict tab, asserts the defend tray is reachable through the real mount path and a Concede click routes through GameBoard's `onFateThrow` prop. (App→GameBoard prop-pass left untested by injection, same convention as the 118-5 compel wiring test.)

**Tests Written:** 19 tests across 4 files covering all 6 ACs.
**Status:** RED (12 failing for missing-feature reasons; all 4 files collect cleanly). The 7 passing are (a) 4 protocol typed-literal constructions whose real teeth are compile-time under `tsc -b` (the runtime `MessageType` test fails), and (b) 3 negative-case guards in the component suite whose PAIRED positives fail in RED (so the pair is non-vacuous — "mounts for me, not for others/none/pre-emptively").

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #4 Null/undefined + No Silent Fallbacks (wire boundary) | `useStateMirror…drops a malformed request (missing defender)` | failing |
| #10 Input validation — runtime-validate the wire payload, not just type it | `useStateMirror…drops a malformed request` | failing |
| #6 React/JSX — exercised through the REAL component tree (no isolation-only) | `GameBoard…reaches the defend tray from the real mount path` | failing |
| 118-5 anti-drift — mechanical readouts from the payload, never hardcoded | `FateConflictSurface…reads attacker/skill/total FROM THE PAYLOAD`, `…reflects a DIFFERENT request's values` | failing |
| Wiring test (CLAUDE.md — every suite needs one) | `GameBoard…` (2 tests) + `useStateMirror…threads the request` | failing |
| #8 Test quality (self-check) | n/a — see Self-check below | — |

**Rules checked:** 5 of the applicable TS/React lang-review checks (#4, #6, #8, #10) plus the SideQuest 118-5 anti-drift project rule have behavioral coverage. Checks #1–3,#5,#7,#9,#11–13 are Dev-side self-review concerns with no net-new behavior to test in this story.
**Self-check:** 0 vacuous tests. No `assert(true)`, no `let _ =`, no always-undefined assertions. No `as any`; the only casts are the established `as unknown as Record<string, unknown>` wire-message idiom (matches `useStateMirror.fateRoll.test.ts`) and `as GameBoardProps` on the spread (matches the compel wiring test).

### Prescribed contract (the symbol names the tests pin — for Dev)

The tests intentionally fix these names (TDD defines the contract; mirror the existing Fate slices):
- `MessageType.FATE_DEFEND_REQUEST = "FATE_DEFEND_REQUEST"`; `FateDefendRequestPayload { request_id, defender, attacker, attack_skill, attack_total, mental }`.
- `FateThrowPayload.action` widened to include `"defend"`; add `concede?: boolean`. **Also widen `FateDiceTray`'s thrower-mode `action` union to include `"defend"`** (FateConflictSurface mounts the thrower with `action="defend"`).
- State slice `latestFateDefendRequest` on GameState (default `null`, like `latestFateRoll`); GameBoard prop `latestFateDefendRequest` threaded into `FateConflictSurface` as a new `defendRequest` prop; App passes `gameState.latestFateDefendRequest` down (analog of `latestFateRoll`).
- Defend tray testids: `fate-defend-tray` (container), `fate-defend-concede` (concede button).

**Handoff:** To Dev (Inigo Montoya) for the GREEN implementation.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (sidequest-ui):**
- `src/types/protocol.ts` — `MessageType.FATE_DEFEND_REQUEST`.
- `src/types/payloads.ts` — `FateDefendRequestPayload` + `FateDefendRequestMessage` (added to the inbound `TypedGameMessage` union, alongside `FateStateMessage`/`FateRollMessage`); `FateThrowPayload.action` widened to include `"defend"`; new optional `concede?: boolean`; `face` made optional (`face?: number[]`) so a concession can omit it (matches the server `tuple | None`).
- `src/dice/FateDiceTray.tsx` — thrower-mode `action` union widened to include `"defend"` (the defend throw is physics-is-the-roll, reusing the existing thrower).
- `src/hooks/useStateMirror.ts` — `latestFateDefendRequest` EVENT slice (most-recent-wins) + No-Silent-Fallbacks boundary guard (drops a request with no `request_id`/`defender`, leaving the slice unchanged), mirrored into `current` like `latestFateRoll`.
- `src/providers/GameStateProvider.tsx` — `latestFateDefendRequest` on `ClientGameState` (default `null` in `EMPTY_GAME_STATE`).
- `src/components/FateConflictSurface.tsx` — `defendRequest` prop; `pendingDefend` gate (filter by `defender === actorName`, suppress once answered via local `answeredDefendId`); defend tray (`data-testid="fate-defend-tray"`) reads attacker/skill/total **from the payload** (118-5 anti-drift), mounts `FateDiceTray` thrower `action="defend"`, settle forwards the FATE_THROW to `onFateThrow` and consumes the request; Concede button (`fate-defend-concede`) sends `concede=true` + a neutral `throw_params` and no faces, then consumes.
- `src/components/GameBoard/GameBoard.tsx` — `latestFateDefendRequest` prop threaded into `FateConflictSurface` as `defendRequest` (+ memo dep).
- `src/App.tsx` — passes `gameState.latestFateDefendRequest` to GameBoard (analog of `latestFateRoll`).

**Tests:** 19/19 new tests passing (GREEN); full project `tsc -b` typecheck clean; fate regression set (FateConflictSurface/FateDiceTray/useStateMirror/GameBoard-fate/protocol — 77 tests) all passing; eslint clean on changed files (one pre-existing unrelated `App.tsx:1651` warning).
**Branch:** `feat/126-17-fate-defend-throw-ui` (pushed).

**Scope adherence:** UI-only, per the SM assessment. No server/content/daemon changes — the surface consumes the already-merged 126-8 broadcast + 126-14 concede field.

**Handoff:** To verify phase (TEA — Fezzik).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (72 tests pass: 19 new + 53 regression; tsc -b clean; 0 smells; 1 pre-existing App.tsx:1651 lint warning outside diff) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — edge domain self-assessed (multi-pending defense, below) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 | confirmed 2, dismissed 1 (pre-existing) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — test quality self-assessed (below) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — comments self-assessed (below) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — type design self-assessed (below) |
| 7 | reviewer-security | Yes | clean | none | N/A (React escapes text children; no dangerouslySetInnerHTML; client correctly not the authority; routing-key guard fails loud) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — simplification self-assessed (below) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — rule compliance self-assessed (below) |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`, their domains self-assessed)
**Total findings:** 2 confirmed (blocking the verdict), 1 dismissed (pre-existing), 1 self-found edge (non-blocking Delivery Finding), plus several VERIFIED-good

## Reviewer Assessment

**Verdict:** REJECTED

The story is genuinely close — all 6 ACs are implemented, 19/19 new tests pass, the fate regression set (53 tests) is green, `tsc -b` is clean, and security is clean. But the adversarial pass surfaced two real correctness/robustness issues with cheap, clearly-correct fixes, **one of which (the mirror guard) is an incomplete application of the `<critical>` No-Silent-Fallbacks project rule** and diverges from the FATE_ROLL guard's own established precedent. Rule-matching findings may be downgraded but not dismissed, and a 3-line fix to close a No-Silent-Fallbacks gap should land now, not as a deferred follow-up. Routing to a quick TDD rework.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] [SILENT][RULE] | The `FATE_DEFEND_REQUEST` mirror guard validates only the routing keys (`request_id`, `defender`) — it does NOT validate the mechanical display fields (`attacker`, `attack_skill`, `attack_total`). A version-skewed/corrupt payload with valid routing keys but a missing/null `attack_total` passes the guard and renders a blank/`0` committed-attack total on the defend tray — a silent, wrong-but-plausible mechanical value on a surface whose entire purpose is legible mechanics (118-5 anti-drift, which the code itself names). This is a No-Silent-Fallbacks gap (`<critical>` CLAUDE.md rule) and diverges from the same file's FATE_ROLL guard, which validates EVERY face value, not just the tuple length. | `src/hooks/useStateMirror.ts:307-316` | Extend the guard to also require `typeof p.attacker === 'string' && p.attacker`, `typeof p.attack_skill === 'string' && p.attack_skill`, and `typeof p.attack_total === 'number'`; `console.error` + `continue` (drop) on failure, mirroring the FATE_ROLL per-face validation in the same file. |
| [MEDIUM] [SILENT] | `onDefendThrow` consumes the request by re-reading `pendingDefend.request_id` inside the settle callback instead of the `thrown.request_id` it was handed. If the mirror slice is replaced by a NEW `FATE_DEFEND_REQUEST` between the throw gesture and the dice settling, the throw fires for the OLD request (the tray's mounted `requestId`) but `setAnsweredDefendId` marks the NEW request answered — dismissing the wrong tray while the old throw goes out. The concede path is already correct (it guards `if (!pendingDefend) return` up front). | `src/components/FateConflictSurface.tsx:229-232` | Consume by the thrown id: `setAnsweredDefendId(thrown.request_id)` (the payload already carries the authoritative echoed id — no re-read of `pendingDefend` needed). |

### Observations (tagged)

- [VERIFIED] Security clean — `attacker`/`attack_skill`/`attack_total` render as escaped React text children inside `<strong>` (`FateConflictSurface.tsx:309-318`); no `dangerouslySetInnerHTML`/`innerHTML`/`eval` anywhere in the diff. Checked against the no-raw-HTML rule. **[SEC]** subagent corroborates (clean).
- [VERIFIED] Wiring is real end-to-end — `latestFateDefendRequest` flows wire→mirror (`useStateMirror.ts:307`) → `ClientGameState` (`GameStateProvider.tsx`) → `App.tsx:2748` → `GameBoard.tsx` `defendRequest` → `FateConflictSurface`. Both halves are under test (`useStateMirror.fate-defend.test.ts` + `GameBoard-fate-defend-wiring.test.tsx` renders the real GameBoard, clicks the tab, asserts the tray + the Concede→`onFateThrow` route). Reachable from production, not isolation-only.
- [HIGH] [SILENT][RULE] mirror guard incompleteness — see severity table (`useStateMirror.ts:307`).
- [MEDIUM] [SILENT] `onDefendThrow` consume race — see severity table (`FateConflictSurface.tsx:231`).
- [MEDIUM] [EDGE] (self-assessed — edge_hunter disabled) **Multiple simultaneous defenses for one PC are not representable.** The mirror is latest-wins (`latestFateDefendRequest = p` overwrites), but the server broadcasts ONE `FATE_DEFEND_REQUEST` per incoming attack (`fate_throw.py:168` loops over `result.defend_requests`). If two NPCs attack the same PC in one round, two requests target the same `defender`; the UI keeps only the last, the player answers one, and the server stays parked on the other — re-introducing the exact hang this story fixes, for the multi-attacker case. Out of AC scope (the AC + tests model a single request, and the primary single-attack showstopper is correctly fixed), so logged as a **non-blocking Delivery Finding** for a follow-up — but note the codebase's own multi-pending precedent is the compel *rack* (an array), not a latest-wins slice.
- [LOW] [SILENT] (dismissed — pre-existing) `FateDiceTray.handleAllSettle` silently returns when `pendingParams.current` is null (`FateDiceTray.tsx:147`). The defend tray now relies on this path, so a dropped settle would silently not send the defense. **Dismissed as out-of-diff**: this guard is unchanged 126-7 code (the diff only widened the action union), and the scenario (settle before a throw gesture) is not reachable in normal thrower-mode play. Noted as a Delivery Finding for a future loud-log hardening.
- [VERIFIED] [TYPE] (self-assessed — type_design disabled) `FateThrowPayload.face` widening to optional is safe — `tsc -b` is clean, so no consumer assumes `face` is always present; the only producer (`FateDiceTray` thrower) still always sets it; `concede` correctly typed `boolean`. Mirrors the server `tuple | None`.
- [LOW] [SIMPLE] (self-assessed — simplifier disabled) `NEUTRAL_THROW_PARAMS` is declared `as const` then spread-and-cast back to mutable tuples in `concedeDefend` (`FateConflictSurface.tsx:243-247`) — a small readonly→mutable dance. A plain `const NEUTRAL_THROW_PARAMS: DiceThrowParams = {...}` (no `as const`) would let it be passed directly. Non-blocking; fix opportunistically during the rework.
- [VERIFIED] [TEST] (self-assessed — test_analyzer disabled) Behavioral tests are strong (tray mounts/reads-payload/throw-emits/concede-folds/dismisses; anti-drift asserted with two different payloads; wiring through real GameBoard). The 4 protocol typed-literal tests are near-tautological at runtime but are compile-time guards under `tsc -b` (the established `fate-protocol.test.ts` convention). No vacuous assertions. **Note:** the rework should add a mirror test that a payload missing `attack_total` is dropped (mirrors the existing malformed-`defender` test) — that's the test that pins the [HIGH] fix.
- [VERIFIED] [DOC] (self-assessed — comment_analyzer disabled) Comments are accurate and cite the right ADRs/stories; the `NEUTRAL_THROW_PARAMS` comment correctly explains the required-but-ignored `throw_params` server wrinkle. No stale/misleading comments.

### Rule Compliance

Project rules (no `.claude/rules/`; sourced from CLAUDE.md, SOUL.md, lang-review/typescript.md):

- **No Silent Fallbacks (CLAUDE.md `<critical>`):** `useStateMirror.ts:307` guard — **VIOLATION (partial):** routing keys fail loud (✓), but `attacker`/`attack_skill`/`attack_total` are unvalidated and silently degrade (✗). See [HIGH]. All OTHER changed surfaces comply (no silent defaults introduced elsewhere).
- **Every test suite needs a wiring test (CLAUDE.md):** ✓ `GameBoard-fate-defend-wiring.test.tsx` renders the real GameBoard mount path; `useStateMirror.fate-defend.test.ts` covers the wire→mirror half.
- **Don't reinvent — wire up what exists (CLAUDE.md):** ✓ Reuses `FateDiceTray` thrower (action union widened, not duplicated), `FateConflictSurface`, `onFateThrow`. No new component.
- **118-5 anti-drift / mechanics legible in player UI (CLAUDE.md Sebastien/Jade):** ✓ at the render layer (reads attacker/skill/total from payload, asserted with two payloads) — but undermined by the [HIGH] guard gap, which lets a corrupt total reach that legible surface silently.
- **lang-review TS #4 (null/undefined, `??` not `||`):** ✓ `defendRequest = null` default, `?? null` threading, `&&` chains in `pendingDefend`. No `||` on falsy-valid values.
- **lang-review TS #6 (React/JSX hooks):** ✓ `answeredDefendId` `useState` is BEFORE the early returns (`FateConflictSurface.tsx:149` vs returns at 155-157); `latestFateDefendRequest` added to the GameBoard `renderWidget` memo deps. No conditional hooks, no stale closure.
- **lang-review TS #10 (runtime-validate wire payloads):** **partial** — same as No-Silent-Fallbacks: routing keys validated, mechanical fields not. See [HIGH].
- **lang-review TS #1 (type-safety escapes):** ✓ no `as any`; the `as [number,number,number]` casts are justified readonly→mutable conversions; `as unknown as FateDefendRequestPayload` matches the file's FATE_ROLL wire-cast idiom.
- **Tenant isolation:** N/A — single-user personal project, no multi-tenant model; no tenant-scoped fields in the diff.

### Devil's Advocate

Assume this code is broken. The most damaging case: a malicious or buggy server. The whole defend surface trusts a wire message. The guard at `useStateMirror.ts:307` only checks `request_id` and `defender` — so a server (or a MITM, though the transport is trusted) that sends `{request_id:"x", defender:"<me>"}` with NO `attack_total` mounts a defend tray that tells the player they're being attacked "at total " (blank) — the player throws or concedes against a phantom with no legible stakes. On a mechanics-first surface, a blank where a number belongs is worse than a crash: it reads as authoritative. That is the [HIGH]. A confused-but-honest server (version skew after a server deploy that renames a field) produces the same silent corruption. Next: the race. A player is attacked, the tray mounts, they pick up the dice — and a SECOND attack lands (new `FATE_DEFEND_REQUEST`, new `request_id`). The slice swaps under them. They release the dice; `onDefendThrow` fires the throw for the FIRST request (the tray's mounted `requestId`) but marks the SECOND answered, so the second tray vanishes unanswered and the server parks forever on it — the hang returns. Even without a race, two NPCs ganging one PC in a single round breaks the latest-wins slice the same way (the [EDGE] finding) — and combat-flavored Fate conflicts absolutely do gang up. A confused USER: mid-defense, the proactive Attack/Overcome tiles are still live (Dev's own logged Question), so a player could fire a proactive throw while owing a defense — server will sort it out, but the UI invites incoherence. What would a stressed renderer do? `attack_total` of `0` (a real Fate value — a defended-down-to-zero attack) renders as "0", indistinguishable from the missing-field "0" — so even the guard fix must keep `0` as valid (`typeof === 'number'`, not truthiness). The happy path is solid; the failure modes are where this needs another pass.

**Handoff:** Back to TEA (Fezzik) for a TDD rework — the two confirmed findings are testable logic/validation fixes (red rework).

## TEA Assessment — Rework Round 1 (2026-06-19)

**Tests Added (RED):** 4 + 1 anti-regression, all in `sidequest-ui/src/hooks/__tests__/useStateMirror.fate-defend.test.ts`, for Reviewer **finding #1** (the [HIGH] mirror-guard incompleteness):
- `drops a request missing attack_total` — RED (guard currently lets it through).
- `drops a request with a non-number attack_total` — RED.
- `drops a request missing attacker` — RED.
- `drops a request missing attack_skill` — RED.
- `KEEPS a request with attack_total === 0` — **GREEN now and must stay GREEN** — pins the fix to `typeof === 'number'`, NOT truthiness (zero is a valid Fate total). The single most important guard against a wrong fix.

**RED verified:** 4 fail (missing-feature), 1 anti-regression passes, all pre-existing pass, file collects clean.

**Dev fix for #1:** extend the `FATE_DEFEND_REQUEST` guard at `useStateMirror.ts:307` to also require `typeof p.attacker === 'string' && p.attacker`, `typeof p.attack_skill === 'string' && p.attack_skill`, and `typeof p.attack_total === 'number'`; `console.error` + `continue` on failure (mirror the FATE_ROLL per-face guard). **Do not** use truthiness on `attack_total` (would drop a valid 0).

**Finding #2 ([MEDIUM] onDefendThrow re-read) — analyzed as NON-REACHABLE; no test written.** On writing the failing test I traced the path: the defend tray mounts `FateDiceTray` with `requestId={pendingDefend.request_id}`, and `FateDiceTray.onThrow` builds `request_id: requestId` — so `thrown.request_id === pendingDefend.request_id` **by construction** whenever the tray renders, and `onDefendThrow` only fires from a rendered tray (a render where `pendingDefend` is non-null). A null-`pendingDefend` render unmounts the DiceScene, so no settle can fire from it. Therefore `if (pendingDefend) setAnsweredDefendId(pendingDefend.request_id)` and `setAnsweredDefendId(thrown.request_id)` are behaviorally identical in every reachable state — there is no failing test to write (measure-don't-assert). **Recommendation to Dev:** still apply the one-line `setAnsweredDefendId(thrown.request_id)` refactor — it's free, removes the fragile re-read, and future-proofs against a change that decouples `requestId` from `pendingDefend` — but it is NOT RED-gated and needs no new test. Logged as a deviation below.

**Handoff:** To Dev (Inigo Montoya) — make finding #1's 4 tests green (keep the zero-total test green), and apply the #2 clarity refactor.

## Dev Assessment — Rework Round 1 (2026-06-19)

**Implementation Complete:** Yes

**Files Changed (sidequest-ui):**
- `src/hooks/useStateMirror.ts` — extended the `FATE_DEFEND_REQUEST` boundary guard to also require `attacker` + `attack_skill` (non-empty strings) and `attack_total` (`typeof === 'number'`). Uses `typeof number`, NOT truthiness, so a valid `attack_total: 0` is kept. `console.error` + `continue` (drop) on failure, mirroring the FATE_ROLL per-face guard. Closes Reviewer finding #1 ([HIGH]).
- `src/components/FateConflictSurface.tsx` — `onDefendThrow` now consumes via `setAnsweredDefendId(thrown.request_id)` instead of re-reading `pendingDefend`. Applied per TEA's recommendation for Reviewer finding #2; behaviorally equivalent today (no failing test, by TEA's non-reachability analysis), kept for robustness/clarity.

**Tests:** guard file `useStateMirror.fate-defend.test.ts` is 9/9 green (verified exact count: the 4 previously-RED mechanical-field tests pass, the `attack_total===0` anti-regression stays green, all pre-existing pass); affected component/wiring tests (`FateConflictSurface.defend`, `GameBoard-fate-defend-wiring`) green with no regression; full project `tsc -b` clean; eslint clean on both changed files.
**Branch:** `feat/126-17-fate-defend-throw-ui` (pushed — `5549a9d`).

**Non-blocking follow-ups NOT addressed (Reviewer Delivery Findings — out of this rework's scope):** the multi-pending-defense latest-wins gap and the `FateDiceTray` silent settle-drop log remain logged for follow-up stories.

**Handoff:** To Reviewer (Westley) for re-review.

## Subagent Results

_Re-Review Round 1 — subagents re-run on the rework delta (commits `fb8374f` + `5549a9d`)._

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (65 tests green: guard file 9/9 + 56 fate regression; `tsc -b` clean; eslint clean; 0 rework-introduced smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled — delta is a validation-tightening + no-op refactor; no new edges; the multi-pending follow-up is unchanged/logged |
| 3 | reviewer-silent-failure-hunter | Yes | clean | prior [HIGH] #1 RESOLVED, 0 new | confirmed-resolved |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled — 5 new guard tests self-assessed below |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled — rework comments self-assessed (accurate, explain the zero-total rationale) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled — self-assessed (no type changes in the delta) |
| 7 | reviewer-security | Yes | clean | none | N/A (additive rejections only — cannot admit more payloads; no new surface) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled — delta is minimal |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled — rule compliance self-assessed below |

**All received:** Yes (3 enabled re-run on the rework delta; 6 disabled via `workflow.reviewer_subagents`, self-assessed)
**Total findings:** 0 new. Prior [HIGH] #1 RESOLVED; prior [MEDIUM] #2 closed (refactor applied; non-reachable per TEA, corroborated by the silent-failure + security subagents).

## Reviewer Assessment

_Re-Review Round 1._

**Verdict:** APPROVED

Inigo earned the reprieve. The rework closes both findings exactly as required, with zero new findings from the re-run subagents and a clean preflight (65 tests, `tsc -b`, eslint). The non-blocking follow-ups remain logged for separate stories.

- [VERIFIED] [SILENT][RULE] Finding #1 RESOLVED — the `FATE_DEFEND_REQUEST` guard now validates `attacker` + `attack_skill` (non-empty strings) and `attack_total` (`typeof === 'number'`), failing loud (`console.error` + `continue`). Evidence: `useStateMirror.ts:309-316`. **Crucially uses `typeof`, not truthiness** — `attack_total === 0` (a valid Fate total) is preserved, pinned by the `KEEPS attack_total === 0` test (green). Now matches the FATE_ROLL per-face guard's thoroughness. **[SILENT]** subagent confirms RESOLVED.
- [VERIFIED] [SILENT] Finding #2 closed — `onDefendThrow` consumes `thrown.request_id` (`FateConflictSurface.tsx:233`). `thrown.request_id` is structurally guaranteed a non-empty string (the tray is mounted `requestId={pendingDefend.request_id}`, itself guard-validated, and `FateDiceTray` echoes it). The removal of the `if (pendingDefend)` re-read introduces no new silent path and eliminates a stale-read; behaviorally equivalent today (TEA's non-reachability analysis, independently corroborated by the [SILENT] and [SEC] subagents).
- [VERIFIED] [SEC] Security clean — the guard change is purely additive rejections (cannot admit a payload the old guard rejected); `attacker`/`attack_skill`/`attack_total` render as escaped React text children; `request_id` stays opaque server-correlation data; client remains correctly non-authoritative.
- [VERIFIED] [TEST] (self-assessed) The 5 new guard tests are strong and non-vacuous: 4 RED drivers (missing/non-number `attack_total`, missing `attacker`, missing `attack_skill`) + the `attack_total === 0` anti-regression that pins the `typeof`-not-truthiness contract. Exact count verified 9/9 green.
- [VERIFIED] [DOC] (self-assessed) The rework comments are accurate — the guard comment explains the `typeof`/zero-total rationale; the `onDefendThrow` comment honestly notes the equivalence + future-proofing.
- [VERIFIED] [TYPE] (self-assessed) No type changes in the delta; `tsc -b` clean.
- [LOW] [SIMPLE] (self-assessed) The `NEUTRAL_THROW_PARAMS` spread-cast noted in round 0 remains (untouched by the rework) — still non-blocking, deferred.
- [N/A] [EDGE] (self-assessed) No new edges in the delta; the multi-pending-defense [EDGE] from round 0 is unchanged and remains a logged non-blocking Delivery Finding (follow-up story).

### Rule Compliance (re-review)

- **No Silent Fallbacks (`<critical>`):** ✓ NOW FULLY COMPLIANT — the round-0 partial violation (mechanical fields unvalidated) is fixed; the guard validates all routing + mechanical fields and fails loud. `mental` (optional boolean, server default) is acceptable graceful degradation, not a silent corruption.
- **118-5 anti-drift / mechanics legible:** ✓ the legible surface can no longer receive a silently-corrupt total.
- **lang-review TS #10 (runtime-validate wire payloads):** ✓ now complete.
- **lang-review TS #4 (typeof vs truthiness on numerics):** ✓ `typeof p.attack_total !== 'number'` correctly admits `0`.
- All other rules unchanged from round 0 (compliant).

### Devil's Advocate (re-review)

The round-0 attack: feed a payload with valid routing keys but no `attack_total` and watch a blank render as authoritative. That attack is now dead — the guard drops it loud. The new attack surface to probe: does the tighter guard over-reject a LEGITIMATE payload? The one trap is `attack_total === 0` (a real value — an attack the dice reduced to nothing, or a +0 ladder result). A lazy `!p.attack_total` would have dropped it; the code uses `typeof !== 'number'`, and the `KEEPS attack_total === 0` test pins it green. Could `thrown.request_id` be undefined and mark a phantom id answered? No — it's a non-optional string wired from the guard-validated `pendingDefend.request_id`. Could the `mental` gap bite? Worst case a social attack shows no "(mental)" tag — cosmetic, not mechanical. The remaining real risk is entirely out-of-scope and already logged: two NPCs ganging one PC still overflow the latest-wins slice (the round-0 [EDGE]). Nothing the rework introduced is broken; the rework strictly improved robustness.

**Handoff:** To SM (Vizzini) for finish-story.

## Delivery Findings

<!-- Append findings below. Append-only; never edit another agent's entries. -->

### TEA (test design)
- **Gap** (non-blocking): The server `FateThrowPayload` model requires `throw_params` with **no default** (`protocol/fate.py:98`), yet on a concede the defense short-circuits before replaying it (`fate_throw.py` `_finish_defense`, "unless they conceded"). So the UI Concede path MUST still send a non-empty `throw_params` (a synthesized neutral gesture) or the server rejects the message at validation. Affects `sidequest-ui/src/components/FateConflictSurface.tsx` (the concede builder must populate `throw_params`). My `FateConflictSurface.defend.test.tsx` concede test deliberately leaves `throw_params` loose (asserts only `action='defend'`, `concede=true`, no `face`) so Dev is free to synthesize the gesture. *Found by TEA during test design.*
- **Question** (non-blocking): The defend tray is hosted inside `FateConflictSurface` and therefore inherits its `conflict?.active` gate. This assumes the server's `FATE_STATE` still reports `conflict.active=true` while the round is PARKED at the DEFEND barrier (it should — the conflict is mid-exchange). If a future server change clears `active` at the barrier, the tray would not mount; verify during playtest. Affects `sidequest-ui/src/components/FateConflictSurface.tsx`. *Found by TEA during test design.*
- **Improvement** (non-blocking, rework round 1): Reviewer finding #2 (onDefendThrow re-read) was analyzed as non-reachable (the two consume expressions are equivalent by construction — see TEA deviation). No test written; recommended the trivial refactor anyway. Affects `sidequest-ui/src/components/FateConflictSurface.tsx`. *Found by TEA during test design (rework).*

### Dev (implementation)
- **Improvement** (non-blocking): The defend throw currently sends `skill=""` (the FateDiceTray thrower requires a `skill` string, and the defense skill is resolved server-side — there is no defense-skill picker in this story's ACs). If a future story wants the player to *choose* their defense skill (Fight vs Athletics, etc.) the tray would need a skill select like the proactive section's. Affects `sidequest-ui/src/components/FateConflictSurface.tsx`. *Found by Dev during implementation.*
- **Question** (non-blocking): While a defend tray is mounted, the proactive action tiles + pre-roll Concede remain enabled (not disabled). The ACs/tests don't require suppressing them, and the server is the authority, but a player mid-defense seeing live attack tiles is slightly incoherent UX — consider disabling the proactive section while `pendingDefend` is set in a follow-up. Affects `sidequest-ui/src/components/FateConflictSurface.tsx`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (non-blocking, follow-up story): The `latestFateDefendRequest` mirror slice is latest-wins, so it cannot represent multiple simultaneous pending defenses for one PC. The server broadcasts one `FATE_DEFEND_REQUEST` per incoming attack (`fate_throw.py:168`), so two NPCs attacking the same PC in one round produce two requests the UI cannot both surface — re-hanging the round for the unanswered one. Out of this story's AC scope (single-request model), but a real multi-attacker gap; the codebase's multi-pending precedent is the compel *rack* (an array on the conflict). Affects `sidequest-ui/src/hooks/useStateMirror.ts` + `FateConflictSurface.tsx` (model defenses as a queue/array). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `FateDiceTray.handleAllSettle` silently returns when `pendingParams.current` is null (`FateDiceTray.tsx:147`, pre-existing 126-7 code). The defend tray now depends on this path to send the defense; a dropped settle would silently fail to answer the barrier. Add a `console.warn` on that early-return so a dropped throw is observable. Affects `sidequest-ui/src/dice/FateDiceTray.tsx`. *Found by Reviewer during code review.*
- No new upstream findings during re-review (round 1). The two follow-ups above stand for future stories; the two blocking findings are RESOLVED. *Found by Reviewer during code review (re-review).*

## Design Deviations

### TEA (test design)
- **Wiring split across two tests instead of an App-mounted e2e**
  - Spec source: context-story-126-17.md, AC6 ("rendered through the real mount path — not just the component in isolation")
  - Spec text: "the defend tray is reachable from the production component tree (mounted on FATE_DEFEND_REQUEST via the real App/GameBoard path)"
  - Implementation: Covered as two paired wiring tests — `useStateMirror.fate-defend.test.ts` (wire→mirror slice) + `GameBoard-fate-defend-wiring.test.tsx` (mirror→tray through the real GameBoard) — rather than one `<App>`-mounted socket-to-tray e2e.
  - Rationale: Matches the established Fate wiring convention (the 118-5 compel wiring test explicitly injects `onFateAction`/the slice as props and notes the App→GameBoard seam stays untested-by-injection). Mounting `<App>` would pull in the live WebSocket/provider stack with no added confidence over the two-test split.
  - Severity: minor
  - Forward impact: The App→GameBoard prop-pass for `latestFateDefendRequest` (one line, analog of `latestFateRoll` at App.tsx:2745) is the one seam not under test — close it by mounting `<App>` if it ever regresses.
- **No failing test for Reviewer finding #2 (onDefendThrow re-read race) — analyzed as non-reachable**
  - Spec source: Reviewer Assessment finding #2 ([MEDIUM] [SILENT], `FateConflictSurface.tsx:231`)
  - Spec text: "rework: consume by `thrown.request_id` instead of re-reading `pendingDefend.request_id`"
  - Implementation: No test added. Traced the path: the tray mounts `FateDiceTray requestId={pendingDefend.request_id}`, `onThrow` echoes `request_id: requestId`, and `onDefendThrow` only fires from a rendered (non-null `pendingDefend`) tray — so `thrown.request_id === pendingDefend.request_id` and `pendingDefend` is non-null in every reachable call. The two consume expressions are behaviorally identical; a contrived test would have to fire stale closures on an unmounted component, which models nothing real (a vacuous test by my own TEA standard).
  - Rationale: Measure-don't-assert — a confirmed finding that doesn't reproduce gets documented, not faked into a test. Recommended Dev still apply the trivial refactor (free, future-proofs) but it is not RED-gated.
  - Severity: minor
  - Forward impact: If a future change decouples `requestId` from `pendingDefend` (e.g. capturing the gesture's request_id separately), the race could become reachable and would then need a test. Flagged for that future change.

### Dev (implementation)
- **Corrected a test-access defect in the RED suite**
  - Spec source: `useStateMirror.fate-defend.test.ts` (TEA RED file), AC6 wire→mirror
  - Spec text: assertions on the mirrored slice, e.g. `expect(r.current.latestFateDefendRequest).toEqual(payload)`
  - Implementation: Changed the 5 access sites from `r.current.latestFateDefendRequest` to `r.current.state.latestFateDefendRequest`. The harness returns `useGameState()` (a `GameStateContextValue` = `{ state, setState, … }`), so mirror slices live at `r.current.state.<slice>` — the same access the passing sibling `useStateMirror.fateRoll.test.ts` uses. The original path could never go green (the property is on `ClientGameState`, not `GameStateContextValue`); `tsc -b` confirmed it.
  - Rationale: A pure test-access correction, not a weakening — the asserted behavior (slice populated, most-recent-wins, malformed-drop guard) is unchanged, and the production contract (slice exposed on `ClientGameState`) is correct. Modifying a TEA test was warranted because the test was structurally unsatisfiable as written.
  - Severity: minor
  - Forward impact: none — the test now matches the established state-mirror access convention.
- **Applied Reviewer finding #2's refactor as a no-op clarity change (rework round 1)**
  - Spec source: Reviewer Assessment finding #2 ([MEDIUM]); TEA rework deviation (non-reachable analysis)
  - Spec text: "consume by `thrown.request_id` instead of re-reading `pendingDefend.request_id`"
  - Implementation: Changed `onDefendThrow` to `setAnsweredDefendId(thrown.request_id)` (dropped the `if (pendingDefend)` re-read). TEA established the two expressions are behaviorally identical in all reachable states (so no failing test exists); applied anyway for robustness/clarity per TEA's recommendation.
  - Rationale: Closes the review loop cleanly and future-proofs against a change that decouples `requestId` from `pendingDefend`, at zero behavioral cost. Not test-gated (TEA wrote no test, by design).
  - Severity: trivial
  - Forward impact: none.

### Reviewer (audit)
- **TEA — Wiring split across two tests instead of an App-mounted e2e** → ✓ ACCEPTED by Reviewer: matches the established 118-5 compel-wiring convention; the two paired tests cover both halves (wire→mirror, mirror→tray-through-real-GameBoard) and I independently confirmed the App→GameBoard one-line prop-pass exists (`App.tsx:2748`). Sound.
- **Dev — Corrected a test-access defect in the RED suite (`r.current.X` → `r.current.state.X`)** → ✓ ACCEPTED by Reviewer: not a weakening — the access path was structurally unsatisfiable (`latestFateDefendRequest` lives on `ClientGameState`, not `GameStateContextValue`); the fix matches the passing sibling `useStateMirror.fateRoll.test.ts` and the asserted behavior is unchanged. `tsc -b` corroborates.
- **No UNDOCUMENTED spec deviations found** — the implementation matches the 6 ACs. The issues I'm rejecting on (mirror-guard incompleteness, consume race) are robustness/No-Silent-Fallbacks gaps, not spec deviations, and the multi-pending limitation is out-of-AC-scope (logged as a Delivery Finding, not a deviation).

_Re-Review Round 1 — rework deviation audit:_
- **TEA — No failing test for finding #2 (onDefendThrow re-read), analyzed as non-reachable** → ✓ ACCEPTED by Reviewer: I independently re-traced it and the [SILENT] + [SEC] re-review subagents corroborated — `onDefendThrow` is only reachable from a rendered (non-null `pendingDefend`) tray, and `requestId` is wired to `pendingDefend.request_id`, so the two consume expressions are equivalent by construction. Writing no test for a non-reproducing finding is correct (measure-don't-assert); not faking a contrived test is the right call.
- **Dev — Applied finding #2's refactor as a no-op clarity change** → ✓ ACCEPTED by Reviewer: harmless, removes the fragile re-read, future-proofs against a `requestId`/`pendingDefend` decoupling, zero behavioral cost. Closing the loop with the refactor (not skipping it) is the right level of diligence.