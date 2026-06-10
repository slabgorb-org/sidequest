---
story_id: "97-8"
jira_key: ""
epic: "97"
workflow: "tdd"
---
# Story 97-8: fix: flaky lobby-start-ws-open.test.tsx 5s timeout (vitest-websocket-mock/StrictMode)

## Story Details
- **ID:** 97-8
- **Jira Key:** N/A (Jira disabled)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-10T22:58:49Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-10T22:23:52.372198+00:00 | 2026-06-10T22:25:18Z | 1m 25s |
| red | 2026-06-10T22:25:18Z | 2026-06-10T22:37:20Z | 12m 2s |
| green | 2026-06-10T22:37:20Z | 2026-06-10T22:53:24Z | 16m 4s |
| review | 2026-06-10T22:53:24Z | 2026-06-10T22:58:49Z | 5m 25s |
| finish | 2026-06-10T22:58:49Z | - | - |

## Sm Assessment

**Story:** 97-8 — fix flaky `lobby-start-ws-open.test.tsx` 5s timeout (vitest-websocket-mock + React StrictMode).
**Repo:** sidequest-ui (base: develop). **Branch:** `feat/97-8-2026-06-10-fix-flaky-lobby-start-ws-open`. **Workflow:** tdd (phased). **1pt, p3, type: bug.**

**Context:** Residual from the 2026-06-07 ping-pong follow-ups (epic 97). The test at `src/__tests__/lobby-start-ws-open.test.tsx` intermittently hits vitest's 5s default timeout. Suspected root cause is the interaction between `vitest-websocket-mock` and React StrictMode's double-mount/double-effect: a second mount opens (or re-subscribes to) the mock WS while the first teardown is in flight, so the "WS open" assertion races against a connection that never settles deterministically. See memory note [project_message_type_count_test_stale] for the general "pre-existing flaky/stale test" pattern, but this one is a real fix, not a known-stale skip.

**Why this approach:** TDD-phased so TEA first makes the flake *reproducible/deterministic* (RED) before Dev applies the fix (GREEN). A flaky test can't be fixed by "winging it" — the failing condition must be pinned first. Scope is strictly the one test file plus any minimal test-harness/setup adjustment; no production lobby code changes expected unless TEA's investigation surfaces a real WS-lifecycle bug.

**Gate state:** Merge gate clear (no open PRs in any repo). Jira skipped (not configured). Session + context (`sprint/context/context-story-97-8.md`, validated) + branch all present.

**Handoff:** → TEA (O'Brien) for RED phase. Make the 5s timeout reproducible, then characterize the StrictMode/mock-WS race.

## TEA Assessment

**Tests Required:** No new tests — the existing test IS the failing artifact under repair.
**Reason:** This is a flaky/broken-test story. The defect is in the test's fixture seed, not in production code. Adding a parallel test would be scope creep on a 1pt fix; the existing `Leave + Start` test already encodes the regression contract and must be restored to passing.

**Status:** RED confirmed — `src/__tests__/lobby-start-ws-open.test.tsx` → 1 passed, 1 failed. The "Leave + Start opens a new WebSocket for the new slug" test times out at 5003ms. Verified by testing-runner (RUN_ID 97-8-tea-red) and 10/10 deterministic failures in isolation.

### Root Cause (the story's hypothesis is WRONG)

The story title blames `vitest-websocket-mock`/StrictMode. **It is neither.** Evidence:
- **Not slowness:** raising the timeout to 20s still hangs (true hang, not a slow path).
- **Not StrictMode:** removing both `<StrictMode>` wrappers still hangs.
- **Bisect:** the hang is at the *very first* await — `await firstServer.connected` — long before the second WS server is built. Probes past that point never fire.
- **DOM probe:** at first mount the body renders **"What name shall be yours?"** (the `NamePrompt`), and **no `WebSocket` is ever constructed**. The first session never enters game phase, so `firstServer.connected` never resolves → 5s timeout.

**Actual cause:** App's slug-mode **trust gate** (`src/App.tsx:2074-2076`) was tightened on **2026-06-05 [BAR-1]** to require *both* slug AND identity match:
```js
const slugKnown = loadHistory().some(
  (e) => e.game_slug === slug && e.player_name === displayName,
);
```
The test (authored 2026-04-27, commit 26d2f3c) deliberately seeds the `FIRST_SLUG` history entry with `player_name: 'Tarn'` — a *non-matching* name — to dodge the matching-journey resume short-circuit. Under the old gate (slug-only) that was fine. Under the new [BAR-1] gate, `displayName` is `'Keith'` ≠ `'Tarn'` → `slugKnown === false` → the slug-connect effect returns early → NamePrompt stays up → no WS → hang. **The product gate is correct (it fixes a real silent-rebind class). The test fixture is stale.**

### Confirmed Fix (for Dev — GREEN)

One line. In `lobby-start-ws-open.test.tsx`, change the seeded history entry's `player_name` from `'Tarn'` to `'Keith'` (so it matches the `sq:display-name` the first mount runs under, satisfying the [BAR-1] trust gate). **Do NOT touch `App.tsx`** — no production change is warranted.

Coverage is preserved: the test already does `localStorage.removeItem('sidequest-history')` between Leave and Start, so the matching-journey resume short-circuit cannot fire on the second click — the lobby still POSTs for a fresh slug and the assertions still verify `game_slug === SECOND_SLUG`. **Verified:** with the `'Keith'` seed the file passes 5/5 (both tests green), assertions intact.

Dev should also refresh the now-misleading 2026-04-27 code comment block (lines ~184-212) that explains the `'Tarn'` rationale, since the [BAR-1] gate has inverted it.

### Rule Coverage

| Rule | Test | Status |
|------|------|--------|
| Frontend/Vitest: deterministic async (no real-timer races) | existing `Leave + Start` test (after seed fix) | RED now → GREEN target |
| No vacuous assertions | existing test asserts `type`, `event`, `game_slug=SECOND_SLUG`, `player_name` | meaningful ✓ |
| Wiring test present | test drives full App mount → lobby → POST → WS connect end-to-end | ✓ |

**Rules checked:** Frontend lang-review async-determinism + test-quality rules applied. **Self-check:** no vacuous assertions in the file; assertions verify real payload values.

**Handoff:** To Dev (Julia) — apply the confirmed one-line seed fix + comment refresh, verify GREEN, hand to Reviewer.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

### TEA (test design)
- **Improvement** (non-blocking): The story title misdiagnoses this as a `vitest-websocket-mock`/StrictMode flake; the real cause is the [BAR-1] 2026-06-05 trust-gate tightening (`App.tsx:2074-2076`) stranding a stale `player_name: 'Tarn'` fixture seed. Affects `sidequest-ui/src/__tests__/lobby-start-ws-open.test.tsx` (seed must match `displayName`). *Found by TEA during test design.*
- **Question** (non-blocking): Other tests authored before 2026-06-05 that mount directly at `/solo/:slug` with a non-matching seeded `player_name` may carry the same latent break. A grep for `sidequest-history` seeds across the test suite would confirm whether 97-8 is isolated. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): Checked TEA's latent-break question — 24 other test files seed `sidequest-history`. None are currently failing, so any sharing the `/solo/:slug` + non-matching-`player_name` pattern would already be red; the [BAR-1] break is not realized elsewhere. 97-8 was isolated because its fixture deliberately used a non-matching name to dodge the resume short-circuit. No action needed now; if a future [BAR-1]-style gate tightens further, re-audit those seeds. Affects `sidequest-ui/src/__tests__/*` (history-seeding tests). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `lobby-start-ws-open.test.tsx` first connect assertion (line ~237) checks `game_slug` but not `player_name`; adding `expect(firstConnect.payload.player_name).toBe('Keith')` would symmetrically guard the [BAR-1] identity consumption on the first session (the second connect already asserts it). Affects `sidequest-ui/src/__tests__/lobby-start-ws-open.test.tsx` (add one assertion). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The `firstServer.close()` + `WS.clean()` + `new WS()` sequence (line ~264-267) is not wrapped in `act()`; deterministic today, but an explicit `act()` drain would harden it against future React state-flush timing changes. Pre-existing pattern, not introduced by this story. Affects `sidequest-ui/src/__tests__/lobby-start-ws-open.test.tsx`. *Found by Reviewer during code review.*

## Impact Summary

**Story:** 97-8 (fix flaky lobby-start-ws-open test fixture)

**Risk Level:** Low (test-only fix; no production changes)

**Change Profile:**
- Type: Test fixture repair (single file)
- Files modified: 1 (`src/__tests__/lobby-start-ws-open.test.tsx`)
- Lines changed: +19/−16 (seeded history value + comment refresh)
- Production code changes: 0

**Key Finding:** The story's title misdiagnoses the root cause. The flake is *not* a vitest-websocket-mock or React StrictMode interaction; it's a stale fixture seed that no longer passes the 2026-06-05 [BAR-1] trust-gate tightening in App.tsx (slug + player_name identity match required). TEA's investigation confirmed the root cause and prescribed a one-line fixture seed fix (`'Tarn'` → `'Keith'`). Dev applied exactly that fix with no production changes. Reviewer independently verified the [BAR-1] gate logic and confirmed the fixture-only approach is correct — the gate itself prevents real silent-rebind regressions and must remain tight.

**Blocking Issues:** 0

**Non-Blocking Findings:** 4 (all Improvements, non-blocking)
1. Fixture seed misdiagnosis corrected by TEA (non-blocking improvement to understanding)
2. Adjacent history-seeding test audit completed by Dev (no action needed, isolated issue)
3. Reviewer suggestion to strengthen first-connect assertion with `player_name` check (test-quality enhancement, deferred)
4. Reviewer suggestion to wrap server-close sequence in `act()` (pre-existing pattern hardening, deferred)

**Coverage:** Regression coverage preserved — history is wiped before the second Start click, so the lobby POST and SECOND_SLUG assertions remain meaningful. No silent-rebind firewall gap introduced.

**Acceptance Criteria Met:** All 0 AC items (test-only story, no AC specified in story) ✓

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

### TEA (test design)
- No deviations from spec. Story scope ("fix the flaky test") is honored — no new tests added (existing test is the artifact under repair), no production code in scope. The only re-scoping is the corrected root-cause diagnosis (trust-gate fixture staleness, not StrictMode), which sharpens rather than departs from the story intent.

### Dev (implementation)
- No deviations from spec. Applied TEA's confirmed fix exactly: seed `player_name: 'Keith'` (matching `sq:display-name`) so the first mount passes the [BAR-1] trust gate, and refreshed the two now-misleading comment blocks. No production code touched, per TEA's GREEN guidance. Regression coverage preserved (history wiped before the second Start click; SECOND_SLUG assertions intact).

### Reviewer (audit)
- **TEA — "No deviations from spec" (corrected root-cause diagnosis)** → ✓ ACCEPTED by Reviewer: The re-diagnosis (stale fixture vs. the [BAR-1] gate, not StrictMode/mock-WS) is verified against `App.tsx:2074-2078`. Sharpening the story's misdiagnosis is not a spec departure; the fix stayed inside the one-test-file scope SM set.
- **Dev — "No deviations from spec" (seed `'Keith'` + comment refresh, no production code)** → ✓ ACCEPTED by Reviewer: Diff matches TEA's prescribed fix exactly. No production change is the correct call — the [BAR-1] gate is a real silent-rebind firewall and must not be loosened to accommodate a stale test.
- No undocumented deviations found. The diff is confined to the seed literal and surrounding comments; nothing diverges from spec silently.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-ui/src/__tests__/lobby-start-ws-open.test.tsx` — seeded history `player_name` `'Tarn'` → `'Keith'` to satisfy the 2026-06-05 [BAR-1] slug-mode trust gate (slug + name match); refreshed the two stale comment blocks that documented the old slug-only gate rationale.

**Tests:** 2/2 passing (GREEN) — verified deterministic across 3 runs (~200ms; previously hung at 5003ms).
**Branch:** feat/97-8-2026-06-10-fix-flaky-lobby-start-ws-open (pushed)

**Handoff:** To Reviewer (The Thought Police)

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A (GREEN 2/2, lint silent, tree clean, 0 smells) |
| 2 | reviewer-edge-hunter | Yes | findings | 4 (1 med race, 1 med ordering, 2 low) | confirmed 0, dismissed 2, deferred 2 (all non-blocking, none in diff) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings (domain covered by Reviewer directly — see Rule Compliance) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings (domain covered by Reviewer directly — comments verified vs App.tsx) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (no type surface — test fixture only) |
| 7 | reviewer-security | Yes | clean | none | N/A (BAR-1 rejection path covered in slug-routing.test.tsx; no coverage gap) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (19/-16 line diff, nothing to simplify) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings (rule check performed by Reviewer — see Rule Compliance) |

**All received:** Yes (3 enabled returned: preflight clean, security clean, edge-hunter 4 non-blocking findings; 6 disabled via settings)
**Total findings:** 0 confirmed blocking, 2 dismissed (with rationale), 2 deferred (low, non-blocking)

## Reviewer Assessment

**Verdict:** APPROVED

**Scope.** Single-file, test-only diff: `src/__tests__/lobby-start-ws-open.test.tsx`, +19/−16. The seeded `sidequest-history` fixture's `player_name` changed `'Tarn'` → `'Keith'`; the two explanatory comment blocks were rewritten to describe the 2026-06-05 [BAR-1] gate. No production code touched.

**Independent root-cause verification.** I read the production gate myself at `App.tsx:2074-2078`: `slugKnown = loadHistory().some(e => e.game_slug === slug && e.player_name === displayName)`, then `if (!confirmedThisSlug && !slugKnown) return;`. With the test mounting at `/solo/FIRST_SLUG` under `sq:display-name='Keith'` and the old seed `player_name:'Tarn'`, `slugKnown` was `false` → the slug-connect effect returned before constructing a WebSocket → `NamePrompt` persisted → `await firstServer.connected` hung to the 5s timeout. TEA's diagnosis (stale fixture vs. the [BAR-1] tightening, NOT StrictMode/mock-WS) is correct and the `'Keith'` seed is the right, minimal fix.

**Data flow traced:** localStorage `sidequest-history` seed → `loadHistory()` in App.tsx slug-mode gate (2074) → gate passes for matching identity → fetch `/api/games/:slug` → `appendHistory` (2135) → `connect()` (2166) → WS opens → `SESSION_EVENT{connect, game_slug, player_name}`. The test asserts `game_slug===SECOND_SLUG` and `player_name==='Keith'` on the post-Leave connect — meaningful, non-vacuous assertions on real payload values.

**Pattern observed:** Fixture-fix-not-product-fix is the correct discipline here — the [BAR-1] gate is a genuine silent-rebind firewall (App.tsx:2065-2073 documents the Groucho/alice, Richie/Potsie, Lenny/Laverne regressions). Loosening it to satisfy a stale test would have re-opened a real identity-rebind class. Dev correctly left production untouched.

**Subagent findings — disposition:**
- [SILENT] reviewer-silent-failure-hunter — disabled via settings; no swallowed-error surface in a test fixture diff. No action.
- [TEST] reviewer-test-analyzer — disabled via settings; I assessed test quality directly. No vacuous assertions; the changed test asserts `type`, `event`, `game_slug`, `player_name` on real payloads. The fix restores the test to actually reaching its target assertion (the `slugConnectFired.current` stale-latch regression) instead of dying at the first await.
- [DOC] reviewer-comment-analyzer — disabled via settings; I verified the rewritten comments against `App.tsx:2065-2076`. They accurately describe the [BAR-1] slug+name gate and correctly explain why `removeItem('sidequest-history')` before the second Start click preserves regression coverage. The previously misleading 2026-04-27 rationale (which the [BAR-1] gate had inverted) is now removed. VERIFIED accurate.
- [TYPE] reviewer-type-design — disabled via settings; no type surface (string literal in a JSON fixture). No action.
- [SEC] reviewer-security — clean. Confirmed the BAR-1 rejection path (slug in history under a DIFFERENT `player_name` → must show NamePrompt, must not emit `SESSION_EVENT{connect}`) retains dedicated, unchanged coverage in `slug-routing.test.tsx:272-311` (groucho/alice) and `:329-405` (effect-level no-fetch/no-history-write proof). This fixture change does NOT create a coverage gap in the silent-rebind firewall.
- [SIMPLE] reviewer-simplifier — disabled via settings; nothing to simplify in a one-literal change.
- [RULE] reviewer-rule-checker — disabled via settings; rule check performed directly (see Rule Compliance). No violations.
- [EDGE] reviewer-edge-hunter — 4 findings, all medium/low, **none inside the diff**:
  1. (line 267, med, race) `firstServer.close()`/`WS.clean()`/`new WS()` not wrapped in `act()`. **DISMISSED** — pre-existing code outside the diff; the test is deterministically green across 3+ runs and the first-message `game_slug===SECOND_SLUG` assertion would catch the speculated mis-interception. Not introduced or worsened by this change.
  2. (line 260, med, ordering) `appendHistory` could fire after `removeItem`, re-seeding history. **DISMISSED** — I traced `App.tsx`: `appendHistory` (2135) runs *before* `connect()` (2166) in the same synchronous `.then()` block, and the WebSocket is only constructed by `connect()`. Therefore `await firstServer.connected` (which resolves several awaits before `removeItem`) guarantees `appendHistory` already fired. The race cannot manifest; the implicit await chain provides the ordering the edge-hunter wanted made explicit.
  3. (line 237, low) first connect doesn't assert `player_name`. **DEFERRED** — non-blocking test-strengthening nice-to-have; the second connect already asserts it (line ~282). Captured as a non-blocking Delivery Finding.
  4. (line 131, low) first it-block doesn't set `sq:display-name`. **DEFERRED** — speculative future-refactor robustness; test passes today. Captured as a non-blocking Delivery Finding.

### Rule Compliance

Applicable rules (from CLAUDE.md / SOUL.md / sidequest-ui CLAUDE.md), enumerated against the diff:
- **No Silent Fallbacks** — N/A to a JSON fixture literal; no fallback path introduced. Compliant.
- **No Stubbing / No dead code** — No stubs or empty shells added; the change is a value edit + comment rewrite. Compliant.
- **No skipping tests** — No `.skip`/`.only`/`xfail` added (preflight: 0 test_skips). The fix *restores* a hanging test to passing rather than skipping it. Compliant.
- **No half-wired features** — Test drives the full App mount → lobby → POST → WS connect pipeline end-to-end (the existing wiring test). Unchanged and intact. Compliant.
- **Test quality (no vacuous assertions)** — Both `it` blocks assert real payload fields (`type`, `event`, `game_slug`, `player_name`). No `expect(true).toBe(true)`-class assertions. Compliant.
- **Comment accuracy** — Rewritten comments verified against `App.tsx:2065-2076`; they describe the live [BAR-1] gate correctly. Compliant.
- **OTEL Observability Principle** — "Not needed for cosmetic UI changes"; explicitly not applicable to a test-fixture fix with no subsystem decision. N/A.

### Devil's Advocate

Let me argue this change is broken. First attack: the fix *masks* a real product regression. If the [BAR-1] gate now strands legitimate returning players the way it stranded the test, the "fix" is papering over a UX defect by editing the test to match buggy production. Rebuttal: I read the gate. It rejects only when the *cached* display-name does not match the slug's history entry — which is exactly the silent-rebind it was built to stop (App.tsx:2065-2073, the Groucho-into-foreign-save incident). A genuine returning player's name *does* match and skips the prompt. The test's old seed was deliberately mismatched (to dodge a different short-circuit), so it tripped a gate working as designed. Editing the fixture is correct, not concealment.

Second attack: the fixture change silently deletes coverage of the rejection path — we now only test the happy path, so a future regression that drops the `player_name` check would go uncaught. This is the most serious concern. Rebuttal: the security subagent and I independently located dedicated, unchanged coverage in `slug-routing.test.tsx` (groucho/alice at 272-311 asserts NamePrompt shows and no connect fires; 329-405 asserts no metadata fetch and no history write on a stale-name mount). The negative path is firewalled elsewhere. No gap.

Third attack: a stressed test runner reorders microtasks and `appendHistory` lands after `removeItem`, re-seeding `FIRST_SLUG`, so the second click resumes instead of POSTing and the `SECOND_SLUG` assertion fails intermittently — i.e., we've traded one flake for another. Rebuttal: traced above — `appendHistory` precedes `connect()` synchronously, and `connect()` is what builds the WS that `firstServer.connected` awaits, several awaits before `removeItem`. The ordering is causally guaranteed, not timing-dependent. Fourth attack: what if a confused future author copies this `'Keith'`-matches-`'Keith'` pattern and writes a test that *intends* to exercise rejection but accidentally passes the gate? That's a documentation problem, and the rewritten comment block specifically explains the gate semantics and why the match is required — it reduces, not increases, that risk. Conclusion: the devil finds nothing blocking; the two real concerns (product-masking, coverage-gap) both resolve under inspection.

**Handoff:** To SM (Winston Smith) for finish-story.