---
story_id: "125-6"
jira_key: null
epic: "125"
workflow: "tdd"
---
# Story 125-6: Fate UI payload-boundary hardening (118-2 review): clamp free_invokes before Array.from + exclude fateState from sessionStorage

## Story Details
- **ID:** 125-6
- **Jira Key:** null
- **Workflow:** tdd
- **Repos:** ui (sidequest-ui — branch `feat/125-6-fate-ui-payload-hardening`, targets `develop`)
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-21T06:09:53Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-21T05:30:20Z | 2026-06-21T05:32:44Z | 2m 24s |
| red | 2026-06-21T05:32:44Z | 2026-06-21T05:44:06Z | 11m 22s |
| green | 2026-06-21T05:44:06Z | 2026-06-21T05:49:16Z | 5m 10s |
| review | 2026-06-21T05:49:16Z | 2026-06-21T05:58:08Z | 8m 52s |
| red | 2026-06-21T05:58:08Z | 2026-06-21T06:01:51Z | 3m 43s |
| green | 2026-06-21T06:01:51Z | 2026-06-21T06:05:07Z | 3m 16s |
| review | 2026-06-21T06:05:07Z | 2026-06-21T06:09:53Z | 4m 46s |
| finish | 2026-06-21T06:09:53Z | - | - |

## Sm Assessment

**Routing:** tdd (phased) → TEA (Fezzik) for the RED phase. This is real UI/TypeScript code (`sidequest-ui/src/components/FatePanel.tsx` + the sessionStorage hydration path in GameStateProvider/useStateMirror), not content — TDD applies, content-validation routing does not.

**Why this story is ready:**
- No `depends_on` — self-contained.
- Merge gate clear: zero open PRs on sidequest-ui.
- Session, context, and feature branch (`feat/125-6-fate-ui-payload-hardening`, base `develop`) all verified present.
- Context carries two concrete, testable ACs (the failing tests TEA must author):
  1. **free_invokes clamp** — bound the pip count before `Array.from` at `FatePanel.tsx:~104` (e.g. `Math.min(a.free_invokes ?? 0, N)` for sane N). RED test: a fateState payload with `free_invokes = 1e9` (and `Infinity`/`NaN`) renders a bounded pip count without hanging — closes the 118-2 "no test for free_invokes" gap.
  2. **sessionStorage exclusion** — exclude `fateState` from the sessionStorage hydration path so a malformed payload cannot bypass the FATE_STATE boundary guard on reload. RED test: a malformed `fateState` written to sessionStorage is NOT rehydrated into live state on mount; it re-enters only via a fresh FATE_STATE message through the guard.

**Scope discipline (for TEA/Dev):** This is hardening, not a live-exploit fix — the server emits valid payloads via `build_fate_projection`. Stay inside the two findings. Do NOT touch the FATE_ROLL dice-tuple guard in `useStateMirror` — that is 125-5's territory (different message/field/file).

**Findings note:** Originally typed `bug` in context metadata; it is defense-in-depth hardening. Non-blocking; no rescope needed.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Two defense-in-depth behaviors (a render clamp + a rehydration exclusion) with concrete, testable ACs — real TS/React code, not a chore bypass.

**Test Files:**
- `sidequest-ui/src/components/__tests__/FateCharacterSheet.free-invokes-clamp.test.tsx` — AC1: the Fate aspect free-invoke pip clamp.
- `sidequest-ui/src/providers/__tests__/GameStateProvider.fate-rehydration.test.tsx` — AC2: fateState excluded from sessionStorage rehydration.

**Tests Written:** 7 tests covering 2 ACs.
**Status:** RED — 4 failing AC discriminators, 3 passing regression/wiring guards. Verified via testing-runner (RUN_ID `125-6-tea-red`): VALID_RED (failures are assertion-level on the un-clamped / un-excluded behavior, clean collection). Typecheck clean for both new files under `tsconfig.app.json` (the 1 pre-existing error is in an unrelated file, `GameBoard-fate-inventory-tab.test.tsx`).

RED discriminators (must go GREEN after the fix):
- AC1 `clamps a pathologically large finite free_invokes` — 1000 pips → must be ≤100. (currently renders 1000)
- AC1 `does not throw a RangeError on Infinity` — render must not throw. (currently `RangeError: Invalid array length`)
- AC2 `does NOT rehydrate a malformed fateState` — must be null. (currently the malformed object)
- AC2 `rehydrates non-fate state while excluding fateState (surgical)` — location/characters survive, fateState null. (currently rehydrated as garbage)

Passing guards (pin correct behavior; must STAY green):
- AC1 `renders exactly the requested pip count for a valid value` — 2 → 2 pips (clamp preserves truth).
- AC1 `renders zero pips for free_invokes=0` — forces `?? 0`, never `|| N` (TS rule #4; goes RED if Dev uses `||`).
- AC2 `re-enters fateState only via a fresh FATE_STATE message` — recovery + wiring test (real provider + useStateMirror).

### Rule Coverage

| Rule (TS lang-review) | Test(s) | Status |
|------|---------|--------|
| #4 null/undefined (`??` not `\|\|`; 0 is valid) | AC1 `renders zero pips for free_invokes=0` | passing guard (RED if Dev uses `\|\|`) |
| #10 input validation (`JSON.parse() as T` w/o runtime validation) | AC2 `does NOT rehydrate a malformed fateState` + `surgical` | failing (RED) |
| Wiring (component reachable from the production path) | AC2 `re-enters via fresh FATE_STATE message` (real GameStateProvider + useStateMirror) | passing |

**Rules checked:** 2 of the applicable lang-review rules (#4, #10) have direct test coverage. The rest (#1 type escapes, #6 `key={index}`, etc.) are Dev-diff self-review concerns, not behaviors this story changes.
**Self-check:** 0 vacuous tests — every test has a meaningful assertion (pip-count bound, exact count, `toBeNull` on a value that is non-null in RED, `not.toThrow`). No `as any`; malformed fixtures use the project `as unknown as` idiom.

**Handoff:** To Dev (Inigo Montoya) for GREEN. Two surgical changes:
1. Clamp `a.free_invokes` before `Array.from` in the `Aspects` sub-component (`FatePanel.tsx:~362`, NOT the stale `:104` the story cites) — e.g. `Math.min(Math.max(0, a.free_invokes ?? 0), N)`; the zero-pips guard requires `?? 0`, not `|| N`. Leave the already-clamped `refresh` loop at ~137 alone.
2. Exclude `fateState` from the sessionStorage rehydration path in `GameStateProvider.tsx` (strip on LOAD in `loadGameStateFromStorage` — a malformed value already sitting in storage must not survive a reload). Do NOT touch the FATE_ROLL guard in useStateMirror (125-5's territory).

### TEA Rework — Round-Trip 1 (Reviewer [HIGH][SEC])

**Trigger:** Reviewer REJECT — the FatePoints `refresh` token loop (`FatePanel.tsx:153`) carries the identical unbounded-`Array.from` DoS the original fix closed for `free_invokes`. My RED-phase handoff wrongly called it "already clamped"; `Math.max(0, refresh)` only floors negatives.

**New test file:** `sidequest-ui/src/components/__tests__/FateCharacterSheet.refresh-clamp.test.tsx` — mirrors the free-invokes suite against the `fate-point-token` testid.
**Status:** RED — 2 failing discriminators, 2 passing guards. Verified via testing-runner (RUN_ID `125-6-tea-red-rework`): `expected 1000 to be less than or equal to 100`; `RangeError: Invalid array length` on Infinity. Typecheck clean for the new file.

RED discriminators (must go GREEN after the fix):
- `clamps a pathologically large finite refresh` — 1000 tokens → must be ≤100.
- `does not throw a RangeError on Infinity refresh` — render must not throw.

Passing guards (must STAY green): valid `refresh=3` → exactly 3 tokens; `refresh=0` → 0 tokens (`?? 0` not `|| N`).

**Handoff:** To Dev (Inigo Montoya) — clamp `refresh` in FatePoints the same way as `free_invokes`. Recommended: rename `clampFreeInvokes` → a generic `clampPipCount` (or add a `MAX_REFRESH`) and apply it at `FatePanel.tsx:153` (`Array.from({ length: clampPipCount(refresh) }, …)`), so one helper covers both wire-driven `Array.from` lengths. Keep all 8 existing free-invokes/refresh tests + the AC2 tests green.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-ui/src/components/FatePanel.tsx` — added `MAX_FREE_INVOKE_PIPS = 12` + `clampFreeInvokes()` helper; applied it at the `Aspects` pip loop (`Array.from({ length: clampFreeInvokes(a.free_invokes) })`). Uses `?? 0` (defaults a malformed/missing wire value to 0), `Math.max(0, _)` (floors negatives), `Math.min(_, 12)` (caps huge/Infinity). The already-clamped `refresh` loop was left untouched.
- `sidequest-ui/src/providers/GameStateProvider.tsx` — `loadGameStateFromStorage` now returns `{ ...parsed, fateState: null }`, dropping `fateState` on rehydration so a once-malformed value persisted to sessionStorage cannot survive a reload past the FATE_STATE boundary guard. The rest of the HMR-survival rehydration is unchanged.

**Tests:** 36/36 passing (GREEN) — verified via testing-runner (RUN_ID `125-6-dev-green`): the 2 new files (formerly RED) + 3 blast-radius regression guards (`CharacterPanelFateSheet`, `GameStateProvider`, `useStateMirror.fate`). Typecheck clean (`tsconfig.app.json`); eslint clean on both changed files (no `no-unnecessary-condition` on `?? 0` — the helper param is typed `number | null | undefined`).

**Branch:** `feat/125-6-fate-ui-payload-hardening` (pushed to origin, base `develop`).

**Scope held:** Only `fateState` stripped (the AC's exact field); the FATE_ROLL guard (125-5) untouched. The same rehydration bypass on the sibling event slices (`latestFateRoll` / `latestFateDefendRequest`) is logged as a non-blocking Delivery Finding for a follow-up, not fixed here.

**Handoff:** To Reviewer (Westley) for code review.

### Dev Rework — Round-Trip 1 (Reviewer [HIGH][SEC])

**Implementation Complete:** Yes
**File Changed:** `sidequest-ui/src/components/FatePanel.tsx` — generalized the clamp helper (`clampFreeInvokes`→`clampPipCount`, `MAX_FREE_INVOKE_PIPS`→`MAX_PIP_COUNT`) and applied it to the FatePoints `refresh` token loop (`FatePanel.tsx:157`) in addition to the `free_invokes` pip loop (`:385`). One guard now covers both wire-driven `Array.from` lengths — closes the [HIGH] refresh DoS and the [SIMPLE] shared-helper note in one move.

**Tests:** 22/22 passing (GREEN) — verified via testing-runner (RUN_ID `125-6-dev-green-rework`): the new `refresh-clamp` test, the `free-invokes-clamp` test (survived the rename), AC2 `fate-rehydration`, and the `CharacterPanelFateSheet` regression guard. Typecheck + eslint clean on FatePanel.tsx.

**Branch:** `feat/125-6-fate-ui-payload-hardening` (pushed, `66adcdc`).
**Residual (unchanged, non-blocking):** sibling event slices `latestFateRoll`/`latestFateDefendRequest` rehydration bypass — still a deferred follow-up (out of this story's AC).

**Handoff:** Back to Reviewer (Westley) for re-review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (GREEN: 36 tests pass, eslint clean, tsc clean in blast radius, tree clean, 0 code smells) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings (assessed domain manually — see [EDGE]) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 (all LOW, observability) | confirmed 3 non-blocking, dismissed 0 |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings (assessed domain manually — see [TEST]) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings (assessed domain manually — see [DOC]) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (assessed domain manually — see [TYPE]) |
| 7 | reviewer-security | Yes | findings | 2 (1 HIGH refresh DoS, 1 MEDIUM sibling-slice bypass) | confirmed 2 (1 blocking, 1 non-blocking deferred), dismissed 0 |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings (assessed domain manually — see [SIMPLE]) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings (assessed domain manually — see [RULE]) |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents` settings)
**Total findings:** 1 confirmed blocking (HIGH), 4 confirmed non-blocking (1 MEDIUM deferred + 3 LOW), 0 dismissed

### Re-Review (Round-Trip 1) — rework subagent results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (GREEN: 40 tests, eslint/tsc/tree clean, zero stale `clampFreeInvokes`/`MAX_FREE_INVOKE_PIPS`) | N/A |
| 3 | reviewer-silent-failure-hunter | Yes | clean | 0 (no new issues — the refresh clamp is byte-identical to the reviewed free_invokes pattern) | N/A |
| 7 | reviewer-security | Yes | clean | 0 — **Round-1 [HIGH] refresh DoS CLOSED** (traced Infinity→12, 1e9→12, NaN→0, neg→0; both Array.from sites clamped; no other numeric-length Array.from; AC2 intact) | N/A |
| 2,4,5,6,8,9 | (edge/test/comment/type/simplify/rule) | No | Skipped | disabled via settings | unchanged from Round 1 |

**All received:** Yes (3 enabled re-ran on the rework diff; 6 disabled)
**Total findings (re-review):** 0 blocking — the Round-1 [HIGH] is resolved; the 3 LOW observability notes + the 1 MEDIUM deferred sibling-slice finding remain non-blocking/deferred (unchanged).

## Reviewer Assessment

**Verdict:** APPROVED _(re-review, Round-Trip 1 — the Round-1 REJECT recorded below was resolved by the rework)_

**Re-Review (Round-Trip 1):** The rework clamped the FatePoints `refresh` token loop via a generalized `clampPipCount` helper (one guard now covers both wire-driven `Array.from` lengths — also closing the Round-1 [SIMPLE] shared-helper note). All three enabled specialists re-ran on the rework diff: **preflight GREEN** (40 tests, lint/tsc/tree clean, zero stale helper-name references), **silent-failure clean** (no new issues), **security clean — the [HIGH] refresh DoS is CLOSED** (input trace: Infinity→12, 1e9→12, -Infinity→0, NaN→0, -5→0, 0/null/undefined→0; no input escapes [0,12]; both `Array.from` sites clamped; the other Fate-sheet loops map over arrays, not numeric lengths; the AC2 `fateState` fix is intact and unchanged). I independently re-traced and concur. The sole blocker is resolved; no new findings. **Data flow traced:** a malformed `FateStatePayload.characters[].refresh`/`.free_invokes` → `clampPipCount` → bounded `[0,12]` `Array.from` length (safe). **Pattern observed:** single shared boundary clamp for every wire-driven `Array.from` length at `FatePanel.tsx:100`. **Error handling:** Infinity no longer throws; the AC2 rehydration drop forces re-entry through the loud `useStateMirror` FATE_STATE guard. **Residual (non-blocking, unchanged):** sibling slices `latestFateRoll`/`latestFateDefendRequest` rehydration bypass → deferred follow-up story; optional `console.warn` observability on the clamp/drop. **Handoff:** To SM (Vizzini) for finish-story.

---

**Round 1 verdict (superseded by the re-review above): REJECTED.**

The two named ACs are correctly implemented and their target findings are genuinely closed (verified below). But the security specialist surfaced an UNDOCUMENTED same-class DoS the fix walked past: the FatePoints `refresh` token loop carries the *identical* unbounded `Array.from` on wire data that this story exists to eliminate. The story is titled "Fate UI payload-boundary hardening" against unbounded `Array.from`; shipping it with an identical unbounded `Array.from` in the same component — one that *throws and crashes the render* on `Infinity` — does not meet that objective.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH][SEC] | Unbounded `Array.from({ length: Math.max(0, refresh) })` in FatePoints — the same Fate-panel DoS class the story targets, missed by the fix. `Math.max(0, refresh)` only floors negatives: `refresh: Infinity` → `Math.max(0, Infinity)` = `Infinity` → **RangeError (crashes the Fate-sheet render)**; `refresh: 1e9` → ~1B-node allocation (tab hang). `refresh` rides the same `FateStatePayload.characters[]` wire payload as `free_invokes`. TEA/Dev scoped this out on the FALSE premise that it was "already clamped." | `sidequest-ui/src/components/FatePanel.tsx:153` (FatePoints) | Clamp `refresh` the same way — reuse a shared helper (rename `clampFreeInvokes` → a generic `clampPipCount`, or add `MAX_REFRESH`): `Array.from({ length: clampPipCount(refresh) }, …)`. Add a regression test (refresh = Infinity / 1000 → bounded token count, no throw) mirroring the free_invokes tests. |

**Routing:** testable logic gap (missing clamp + missing regression test) → **red rework → TEA** (Fezzik writes the failing refresh test, Inigo clamps). The fix is small and the test pattern already exists in `FateCharacterSheet.free-invokes-clamp.test.tsx`.

### Observations (all 8 specialist domains)

- **[SEC]** (security subagent, HIGH, CONFIRMED — blocking): refresh unbounded `Array.from` DoS at FatePanel.tsx:153. See severity table. This is the reject driver.
- **[SEC]** (security subagent, MEDIUM, CONFIRMED — non-blocking, deferred): `latestFateRoll` + `latestFateDefendRequest` are rehydrated from sessionStorage past their own boundary guards (`JSON.parse`-as-T, only the `location`-string check) — the same bypass class as `fateState`. Genuinely OUT of this story's AC (AC2 names only `fateState`; these are different message types/fields) and already logged by Dev as a follow-up. Does not block; should get its own story.
- **[SILENT]** (silent-failure subagent, 3× LOW, CONFIRMED — non-blocking): no `console.warn` when `clampFreeInvokes` caps an out-of-range value or when `loadGameStateFromStorage` drops a persisted `fateState`. Pure observability gaps on *intentional, documented* defensive discards. The loud boundary already exists upstream (`useStateMirror` `console.error`s on malformed FATE_STATE), so these do not rise to a No-Silent-Fallbacks violation (the subagent agrees). Optional polish — Dev MAY add a `console.warn` during the rework, not required.
- **[EDGE]** (subagent disabled — manual): traced every `clampFreeInvokes` boundary (Infinity→12, 1e9→12, -Inf→0, NaN→0, -5→0, null/undefined→0, "5"→5, "abc"→0, 12.5→12) — all bounded, none throw. The unhandled edge is `refresh` (the finding). free_invokes edges fully covered.
- **[TEST]** (subagent disabled — manual): the 7 tests are meaningful (pip-count bounds, exact counts, `toBeNull` on a value non-null in RED, `not.toThrow`), non-vacuous, and include a wiring test (real provider + useStateMirror). GAP: no refresh-clamp regression test — part of the reject.
- **[DOC]** (subagent disabled — manual): new comments are accurate — verified the "`Array.from({ length: Infinity })` throws RangeError" and "1e9 materializes a billion nodes" claims against a node trace. No stale/misleading code comments. (The stale `:104` reference is in the story text, not the code, and TEA already flagged it.)
- **[TYPE]** (subagent disabled — manual): `clampFreeInvokes(freeInvokes: number | null | undefined)` is correctly typed so the `?? 0` is necessary (no `no-unnecessary-condition`). `MAX_FREE_INVOKE_PIPS` is a typed const, not a magic literal at the call site. Test malformed fixtures use the idiomatic `as unknown as` (test-only). No stringly-typed APIs introduced.
- **[SIMPLE]** (subagent disabled — manual): the clamp helper is minimal and correct. Note that a *shared* clamp helper would have naturally covered the `refresh` loop too — the duplication-avoidance angle reinforces fixing both call sites with one helper.
- **[RULE]** (subagent disabled — manual): TS lang-review #4 (nullish) COMPLIANT (`?? 0`); #10 (JSON.parse-as-T w/o runtime validation) COMPLIANT for `fateState` (load-side drop) but VIOLATED for the `refresh` `Array.from` (in scope, blocking) and the sibling slices (out of scope, deferred); No-Silent-Fallbacks COMPLIANT (documented discards behind a loud upstream boundary).

### Rule Compliance (rule-by-rule enumeration)

| Rule | Instances in diff | Verdict |
|------|-------------------|---------|
| TS #4 — `??` not `\|\|` for falsy-but-valid 0 | `clampFreeInvokes` (`freeInvokes ?? 0`) | COMPLIANT — 0 stays 0 (pinned by the zero-pips test) |
| TS #10 — wire/`JSON.parse`-as-T needs a boundary guard before use | (a) `fateState` rehydration; (b) `refresh` → `Array.from`; (c) `latestFateRoll`/`latestFateDefendRequest` rehydration | (a) COMPLIANT (dropped on load); (b) **VIOLATION — blocking**; (c) VIOLATION — out of scope, deferred |
| TS #6 — `key={index}` on lists | pip loop `key={pip}` (unchanged by this diff) | ACCEPTABLE — pips are identical/static, not reorderable; pre-existing, not in scope |
| No Silent Fallbacks | `clampFreeInvokes` clamp; `fateState` drop | COMPLIANT — intentional documented discards; the loud boundary is `useStateMirror` (LOW observability nit only) |

### Verified (target findings genuinely closed)

- **[VERIFIED]** AC1 target (free_invokes DoS) CLOSED — `clampFreeInvokes` at FatePanel.tsx:97-99 bounds every pathological input (node-traced); applied at the sole `free_invokes` `Array.from` site (FatePanel.tsx:381). Complies with TS#4 + No-Silent-Fallbacks.
- **[VERIFIED]** AC2 target (fateState rehydration bypass) CLOSED — `loadGameStateFromStorage` returns `{ ...parsed, fateState: null }` (GameStateProvider.tsx:188); the override is synchronous inside the `useState` initializer, so no consumer reads the malformed value before the null takes effect. Re-entry is only via a guarded FATE_STATE message. Complies with TS#10 for this slice.
- **[VERIFIED]** Preflight GREEN — 36 tests pass, eslint/tsc clean in blast radius, tree clean; the lone tsc error (`GameBoard-fate-inventory-tab.test.tsx:203`) predates this branch (exists on `origin/develop`, last touched by `#419`, not in this diff).

### Devil's Advocate

Assume this code is broken and a malicious or buggy payload is in play. The strongest break is already the reject driver: a `FateStatePayload` whose `characters[].refresh` is `Infinity` (a server serialization bug, a replayed/forged payload, or an XSS write to the WS/sessionStorage path) reaches FatePoints and `Array.from({ length: Math.max(0, Infinity) })` throws a `RangeError` *during React render*. If no error boundary wraps the Fate sheet, that throw white-screens the whole app — strictly worse than the `free_invokes` case this story prioritized (which only over-allocated). A `refresh: 1e9` instead hangs the tab on a billion-node allocation. So the story's own threat — a malformed Fate payload DoSing the panel — remains fully live one function above the line that was fixed. Pushing further: could `free_invokes` as a numeric string `"1e9"` slip the clamp? Traced — `Math.max(0, "1e9")` coerces to `1e9`, `Math.min(1e9, 12)` = 12, bounded. A non-numeric `"abc"`? → `NaN` → `Array.from({ length: NaN })` = 0, safe. Could a malformed `fateState` be read before the load-side drop? No — the drop is synchronous in the initializer. Could the sibling event slices (`latestFateRoll`, `latestFateDefendRequest`) carry garbage across a reload and reach a consumer? Yes — confirmed residual, but a different field/message class, correctly out of this AC. Could the persisted-but-dropped `fateState` cause a stale flash? No — it is null from the first render until a fresh FATE_STATE arrives. The decisive break is `refresh`: it is the same vulnerability, in the same file, fed by the same payload, and it *throws*. The fix is incomplete until it is clamped too.

**Handoff:** Back to TEA (Fezzik) for a failing `refresh`-clamp test (red rework), then Dev clamps it.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): the story/context cite `FatePanel.tsx:104` as the unclamped `Array.from({ length: a.free_invokes })` site, but the file was restyled 2026-06-20 (post-118-2) — line 104 is now a `SectionLabel` span. The real unclamped site is the per-aspect pip loop in the `Aspects` sub-component (`FatePanel.tsx:~362`). Affects `sidequest-ui/src/components/FatePanel.tsx` (Dev clamps `a.free_invokes` at ~line 362, NOT 104). The `refresh` token loop at ~line 137 is already clamped (`Math.max(0, refresh)`) — leave it. *Found by TEA during test design.*
- **Improvement** (non-blocking): `GAME_STATE_STORAGE_KEY` (`'sq_game_state'`) is module-private in GameStateProvider.tsx, so the AC2 test hardcodes the literal to seed sessionStorage. If the fix touches the storage helpers anyway, consider exporting the key so the test references the constant. Affects `sidequest-ui/src/providers/GameStateProvider.tsx`. *Found by TEA during test design.*
- (Rework, Round-Trip 1) No new upstream findings — the Reviewer's `refresh` DoS is now in-scope and covered by `FateCharacterSheet.refresh-clamp.test.tsx`. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): the two EVENT-style Fate slices `latestFateRoll` and `latestFateDefendRequest` are ALSO rehydrated from sessionStorage past their respective useStateMirror boundary guards (the FATE_ROLL face-validation from 125-5; the FATE_DEFEND_REQUEST routing/mechanical guard from 126-17) — the exact same bypass class as `fateState`. Held OUT of scope here (125-6 scopes to `fateState` only; the AC2 tests check only `fateState`), but a follow-up could strip them on load the same way. Affects `sidequest-ui/src/providers/GameStateProvider.tsx` (`loadGameStateFromStorage`). *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): the FatePoints `refresh` token loop (`Array.from({ length: Math.max(0, refresh) })`) is the same unbounded-`Array.from`-on-wire-data DoS the story fixes for `free_invokes`, but was left unclamped — `refresh: Infinity` throws a RangeError that crashes the Fate-sheet render. Must be clamped in this story (it IS the story's purpose). Affects `sidequest-ui/src/components/FatePanel.tsx:153` (reuse the clamp helper; add a regression test). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): confirms Dev's finding — `latestFateRoll` / `latestFateDefendRequest` carry the same sessionStorage-rehydration bypass class as `fateState` and remain unguarded on reload. Genuinely out of this story's AC (different message types/fields); recommend a dedicated follow-up story to strip them on load. Affects `sidequest-ui/src/providers/GameStateProvider.tsx`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `clampFreeInvokes` and the `loadGameStateFromStorage` `fateState` drop are silent on out-of-range/dropped values; a `console.warn` at each would aid HMR/dev observability (the loud wire boundary already lives in `useStateMirror`). Optional polish for the rework, not required. Affects `sidequest-ui/src/components/FatePanel.tsx`, `sidequest-ui/src/providers/GameStateProvider.tsx`. *Found by Reviewer during code review.*
- (Re-review, Round-Trip 1) The blocking `refresh` Gap above is RESOLVED — the rework clamps it via `clampPipCount`; security re-review confirmed CLOSED. The two non-blocking Improvements (sibling-slice rehydration bypass; optional `console.warn`) remain open as follow-up candidates, not gating this story. *Found by Reviewer during re-review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **AC1 large-count fixture: 1000 + Infinity instead of the literal 1e9**
  - Spec source: context-story-125-6.md, AC1 ("a fateState payload with free_invokes=1e9 (and Infinity)")
  - Spec text: "a fateState payload with free_invokes=1e9 (and Infinity) renders a bounded pip count without hanging"
  - Implementation: the finite case uses `free_invokes = 1000`; the unbounded case uses `Infinity`. 1e9 is NOT rendered against the current (unclamped) code.
  - Rationale: 1e9 < 2**32, so `Array.from({ length: 1e9 })` does NOT throw — it materializes a billion DOM nodes, hanging/OOM-ing the vitest worker in the RED state (an ugly failure that can take down sibling tests). 1000 is ~500x any legitimate pip count (a clean clamp discriminator that renders in <1ms); Infinity covers the throw path (`RangeError: Invalid array length`). A `Math.min(_, N)` clamp reduces 1e9, 1000, and Infinity identically, so the discriminator is equivalent to the literal spec value.
  - Severity: minor
  - Forward impact: none — Dev's clamp constant N is unconstrained by the tests (assertion ceiling is a generous 100; real N will be ~8–10).
- **Rework (Round-Trip 1): added `refresh` token-clamp coverage beyond the literal AC**
  - Spec source: context-story-125-6.md AC1 (names `free_invokes` only) + Reviewer Assessment [HIGH][SEC] finding
  - Spec text: AC1 — "bound the pip count before Array.from … so a huge/Infinity/NaN free_invokes cannot allocate a pathological array"
  - Implementation: added `FateCharacterSheet.refresh-clamp.test.tsx` covering the FatePoints `refresh` token loop (`Array.from({ length: Math.max(0, refresh) })`) — beyond the AC's literal `free_invokes` field
  - Rationale: Reviewer rejected — `refresh` carries the IDENTICAL unbounded-Array.from DoS in the same component, fed by the same payload; the story's purpose ("Fate UI payload-boundary hardening" against unbounded Array.from) is not met without it. The scope expansion is review-driven, not unilateral.
  - Severity: minor (scope clarification within the story's stated purpose; not a behavior change to the existing fix)
  - Forward impact: Dev must clamp `refresh` (reuse the helper) for the new test to go green.

### Dev (implementation)
- No deviations from spec. Both ACs implemented as TEA specified: clamp applied at the real `Aspects` pip-loop site (FatePanel.tsx, NOT the stale `:104`) via `clampFreeInvokes()` using `?? 0` (not `||`); `fateState` stripped on LOAD in `loadGameStateFromStorage`. Clamp constant `MAX_FREE_INVOKE_PIPS = 12` chosen within the AC's "sane N" latitude. Scope held to `fateState` only (the AC's exact field) — the FATE_ROLL guard in useStateMirror was left untouched (125-5's territory).
- (Rework, Round-Trip 1) No deviations from the rework spec. Clamped the FatePoints `refresh` token loop per the Reviewer [HIGH] finding by generalizing the existing helper: renamed `clampFreeInvokes`→`clampPipCount` and `MAX_FREE_INVOKE_PIPS`→`MAX_PIP_COUNT`, and applied `clampPipCount` to BOTH wire-driven `Array.from` lengths (`refresh` tokens at FatePanel.tsx:157 + `free_invokes` pips at :385). One guard, both call sites — also resolves the Reviewer [SIMPLE] note about a shared helper. No behavior change to the already-green free_invokes/fateState fixes.

### Reviewer (audit)
- **TEA — AC1 fixture `1000`+`Infinity` instead of literal `1e9`** → ✓ ACCEPTED: sound. Rendering the unclamped code with `1e9` would materialize a billion DOM nodes and hang/OOM the runner in RED; `1000` + `Infinity` is an equivalent discriminator (a `Math.min(_, N)` clamp reduces 1e9, 1000, and Infinity identically — node-verified).
- **Dev — "No deviations from spec"** → ✓ ACCEPTED *with respect to the literal ACs* (which name only `free_invokes` and `fateState`); both were implemented faithfully. BUT see the undocumented gap below — the AC's example field was handled correctly while the story's broader DoS-hardening purpose was left incomplete.
- **UNDOCUMENTED (Reviewer) — `refresh` token loop left unbounded:** Story purpose = "Fate UI payload-boundary hardening" against unbounded `Array.from` on wire data. The code clamps `free_invokes` but leaves `Array.from({ length: Math.max(0, refresh) })` in FatePoints (FatePanel.tsx:153) unbounded — same DoS class, same file, same `FateStatePayload` source. TEA's handoff and Dev's note both scoped `refresh` out on the FALSE premise that `Math.max(0, refresh)` clamps it; it only floors negatives (`Math.max(0, Infinity)` = `Infinity` → RangeError). Severity: **HIGH**. → ✗ FLAGGED — drives the REJECT (see Reviewer Assessment severity table). **→ RESOLVED in the rework (Round-Trip 1): `refresh` now routes through `clampPipCount`; security re-review confirmed CLOSED.**

### Reviewer (re-review audit, Round-Trip 1)
- **TEA rework — added `refresh` token-clamp coverage** → ✓ ACCEPTED: the correct response to the Round-1 [HIGH] finding; the scope expansion is review-driven and squarely within the story's stated "Fate UI payload-boundary hardening" purpose.
- **Dev rework — `clampFreeInvokes`→`clampPipCount` rename + apply to `refresh`** → ✓ ACCEPTED: a clean generalization (one helper for both wire-driven `Array.from` lengths) that closes the [HIGH] DoS and the Round-1 [SIMPLE] shared-helper note in one move; re-review preflight confirms no regression (40 tests green, zero stale references).