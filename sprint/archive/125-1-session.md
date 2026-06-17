---
story_id: "125-1"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 125-1: Inspector token chart — hit-rate dot tooltip mislabels turn # when null turns interspersed

## Story Details
- **ID:** 125-1
- **Epic:** 125 (Tech debt — deferred cleanups & review follow-ups)
- **Jira Key:** (none — oq-2 is sprint-YAML only)
- **Workflow:** tdd
- **Stack Parent:** none
- **Bundle:** YES — this is the lead story for a three-story bundle (125-1, 125-2, 125-3) that must be implemented on one branch / one PR because 125-1 and 125-2 both edit TokenBarChart.tsx and would conflict if split.

## Bundle Scope

This session covers three tightly-coupled tech-debt stories from the 124-1 Reviewer audit, all sidequest-ui, all 1-point:

### 125-1 (lead, TDD) — Cache hit-rate tooltip turn-index bug
**Problem:** TokenBarChart.tsx:143 builds the cache-hit-rate dot's tooltip turn label from the post-filter index (i+1) of the hitPoints array, not the real turnIndex. The x-position and aggregate cold-miss count are correct; only the hover label is wrong when null (non-SDK) turns are interspersed before a known turn.

**Fix:** Carry turnIndex into each hitPoints object and use it in the <title>.

**Test:** A series like [null, cold] must show the cold dot's tooltip as the SECOND turn, not 'T1'.

**Touches:** 
- sidequest-ui/src/components/Dashboard/charts/TokenBarChart.tsx
- Tests: telemetryAdapter-cache-join / TokenBarChart-cache-split

### 125-2 (TDD, folded) — Visible 'cache: n/a' caption for all-non-SDK sessions
**Problem:** When every turn is cacheState null (all non-SDK, e.g. Ollama/claude-p), the 'served from cache' summary line is suppressed (line 149) and the only 'n/a' is in per-bar SVG <title> tooltips (hover-only, line 93). A GM can't tell if cache data is absent vs zero without hovering.

**Fix:** Add a visible 'cache: n/a (non-SDK)' caption for the all-null case.

**Test:** 
- An all-null series renders a visible (non-title) n/a caption.
- A series with >=1 known turn renders the savings line instead.

**Legibility enhancement, NOT a correctness fix.** AC-4's no-fabrication is met.

**Touches:** sidequest-ui/src/components/Dashboard/charts/TokenBarChart.tsx

### 125-3 (trivial, folded) — Surface malformed cache_usage instead of silently folding to null
**Problem:** buildTurnTokenCacheRows (telemetryAdapter.ts) folds a MALFORMED cache_usage (a dict present but cache_read absent/non-numeric) into the same 'null' bucket as genuinely-absent cache_usage — masking server schema-drift as a benign 'non-SDK' turn (No-Silent-Fallbacks concern). Server guarantees cache_read is an int when the dict is present (test_prompt_cache_attribution_otel.py), so realistic surface is nil today. This is defensive hardening.

**Fix:** Surface the anomaly: either a console.warn or a distinct 'malformed' cacheState (implementer's choice; avoid noisy prod logging).

**Test:** A prompt_assembled with cache_usage={cache_write:500} (no cache_read) is flagged/warned, not silently treated as non-SDK.

**Touches:** sidequest-ui/src/components/Dashboard/source/telemetryAdapter.ts

## Sm Assessment

**Bundle rationale:** Three 1-point tech-debt stories from the 124-1 Reviewer audit, all in `sidequest-ui`, all touching the Inspector token-chart / cache-join code. 125-1 and 125-2 both edit `TokenBarChart.tsx`; splitting them onto parallel branches guarantees a merge conflict. So they ride one branch (`feat/125-1-inspector-cache-chart-fixes`), one PR, one review. tdd is the umbrella workflow (125-3's trivial fix is subsumed — it gets a regression test like the other two).

**Scope is fully specified** in the Bundle Scope section above — three discrete fixes, each with a named file and a named regression test:
1. 125-1 — `TokenBarChart.tsx:143`: carry `turnIndex` into each hitPoints object; use it in the dot `<title>`. Test: `[null, cold]` → cold dot tooltip reads turn **2**, not `T1`.
2. 125-2 — `TokenBarChart.tsx` (lines 93/149): add a VISIBLE `cache: n/a (non-SDK)` caption when every turn is cacheState `null`. Test: all-null series → visible (non-`<title>`) caption; ≥1 known turn → savings line instead.
3. 125-3 — `telemetryAdapter.ts` `buildTurnTokenCacheRows`: surface a malformed `cache_usage` (dict present, `cache_read` absent/non-numeric) via `console.warn` or a distinct `malformed` cacheState rather than folding to `null`. Test: `cache_usage={cache_write:500}` (no `cache_read`) is flagged, not treated as non-SDK.

**Verification posture:** All three name their own test, so this is genuinely test-first. 125-1's fix is a pure label correctness bug; 125-2 is a legibility addition (not a correctness change — AC-4 no-fabrication already holds); 125-3 is defensive hardening (server contract makes the malformed surface nil today). No engine/server changes — UI-only.

**Routing:** Phased tdd → **TEA (Fezzik)** writes failing tests for all three fixes in the red phase, then Dev (Inigo) makes them green on the one branch. At finish, all three stories archive together against the single PR.

**Risks/notes:** Keep the per-bar `<title>` n/a (125-2) AND add the visible caption — don't replace one with the other. For 125-3, prefer the quietest signal that a test can assert (a distinct cacheState is more testable than a console.warn); implementer's choice per the story, but TEA should pick the assertable surface.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-17T00:04:33Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-16T23:24:54Z | 2026-06-16T23:28:31Z | 3m 37s |
| red | 2026-06-16T23:28:31Z | 2026-06-16T23:35:48Z | 7m 17s |
| green | 2026-06-16T23:35:48Z | 2026-06-16T23:40:24Z | 4m 36s |
| review | 2026-06-16T23:40:24Z | 2026-06-17T00:04:33Z | 24m 9s |
| finish | 2026-06-17T00:04:33Z | - | - |

## TEA Assessment

**Tests Required:** Yes
**Reason:** Three behavioral fixes, each named its own regression test in the story — genuinely test-first.

**Test Files:**
- `src/components/Dashboard/__tests__/TokenBarChart-hitrate-turnindex.test.tsx` — 125-1 (3 tests)
- `src/components/Dashboard/__tests__/TokenBarChart-nonsdk-caption.test.tsx` — 125-2 (3 tests)
- `src/components/Dashboard/__tests__/telemetryAdapter-malformed-cache.test.ts` — 125-3 (5 tests)

**Tests Written:** 11 tests (6 RED new-behavior + 5 green guards) covering 3 ACs across the bundle.
**Status:** RED — 6 failing, verified by testing-runner (run id `125-1-tea-red`), each failing for the RIGHT reason:
- 125-1 cold dot tooltip received `"T1 cold-start miss"`, expected `T2`; warm dot received `"T1 90% from cache"`, expected `T3`.
- 125-2 all-null visible `<text>` had no `n/a` (only the hover `<title>` did).
- 125-3 malformed `cache_usage` returned `cacheState "null"`, expected `"malformed"`.

### Rule Coverage

| Rule (project) | Test(s) | Status |
|----------------|---------|--------|
| No Silent Fallbacks | `telemetryAdapter-malformed-cache` — malformed dict surfaced, not folded to `null` | failing (RED) |
| No fabricated values | `nonsdk-caption` negative guard — no `n/a` when a turn is known; no invented savings | passing (guard) |
| Honest unknown vs known | `hitrate-turnindex` + malformed guards — null≠cold, absent≠malformed | mixed (2 RED, guards green) |
| Meaningful assertions (test quality) | self-check below | n/a |

**Rules checked:** No-Silent-Fallbacks is the load-bearing project rule here (125-3 directly enforces it); fabrication/honesty rules covered by 125-2 guards.
**Self-check:** 0 vacuous assertions in the new tests — every `it` asserts a specific string/value (`toMatch(/\bT2\b/)`, `toBe("malformed")`, `toBeNull()`); no `let _ =`, no `assert(true)`, no always-null `is_none`. No pre-existing tests modified.

**Handoff:** To Dev (Inigo) for GREEN — implement all three fixes on the one branch.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-ui/src/components/Dashboard/source/telemetryAdapter.ts` — **125-3**: widened the `cacheState` union with `"malformed"`; restructured the cache-read branch so a present `cache_usage` whose `cache_read` is missing/non-numeric yields `cacheState: "malformed"` (with `cached` left `null`) instead of folding into the benign `"null"` bucket. Genuinely-absent `cache_usage` and no-prompt turns still resolve to `"null"`.
- `sidequest-ui/src/components/Dashboard/charts/TokenBarChart.tsx` — **125-1**: each `hitPoints` entry now carries `turnIndex`, and the hit-rate dot `<title>` reads `T${p.turnIndex}` instead of the post-filter map index `T${i + 1}`. **125-2**: the all-non-SDK case (`knownTurns.length === 0`) now renders a visible `cache: n/a (non-SDK)` `<text>` caption; the per-bar hover `<title>` n/a is unchanged, so both coexist.

**Tests:** 2351/2351 passing (GREEN) — full sidequest-ui vitest suite. 11/11 new bundle tests green; related cache tests no regression (cache-split 12, cache-join 10, TimingTab-cache-split 3). `tsc --noEmit` clean, `eslint` clean on all changed files.
**Branch:** `feat/125-1-inspector-cache-chart-fixes` (pushed)

**Minimalism note:** No `console.warn` added for 125-3 — TEA's pinned, tested contract is the distinct `cacheState`, and the story's "avoid noisy prod logging" makes the typed-but-quiet surface the cleaner choice. The malformed value is now in the data model for any consumer that wants it.

**Handoff:** To Reviewer (Westley) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | success | none (2351/2351 GREEN, eslint+tsc clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — covered manually (see Devil's Advocate) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 (1 high-confidence, 1 low) | confirmed 1 (severity downgraded to Medium, non-blocking), deferred 1 (pre-existing, out of diff) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — covered manually ([TEST] below) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — covered manually ([DOC] below) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — covered manually ([TYPE] below) |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — covered manually ([SIMPLE] below) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — covered manually ([RULE] below) |

**All received:** Yes (3 enabled specialists returned; 6 disabled pre-filled and covered manually)
**Total findings:** 1 confirmed (Medium, non-blocking), 0 dismissed, 1 deferred (pre-existing low)

### Rule Compliance (TypeScript lang-review checklist + SOUL)

Exhaustive enumeration against `.pennyfarthing/gates/lang-review/typescript.md` for the two changed source files:

| Check | Instances in diff | Verdict |
|-------|-------------------|---------|
| #1 Type-safety escapes | source: 0 `as any`/`@ts-ignore`/non-null. Tests: `as unknown as Record<string,unknown>` (fixture, mirrors existing cache-join test) + now-redundant `as string` on `cacheState` | compliant (test casts established pattern; `as string` harmless) |
| #3 Enum anti-patterns | `cacheState` is a **string-literal union** (checklist prefers this over enums); widened 3→4 members; no `switch` needing `assertNever` | compliant |
| #4 Null/undefined | new branch uses `typeof === "number"` guard then else; `cached` stays `null`; `?? 0` unchanged; no `||` on falsy-valid | compliant |
| #6 React/JSX | no `useEffect`, no `dangerouslySetInnerHTML`, no user input; caption is a static literal; `key={`hr${i}`}` **unchanged** by this diff (pre-existing) | compliant (key is pre-existing, not introduced) |
| #8 Test quality | specific assertions (`toMatch(/\bT2\b/)`, `toBe("malformed")`, `toBeNull()`); no `as any` in assertions; wiring covered by existing TimingTab-cache-split | compliant |
| #10/#11 Input validation / error handling | the malformed branch IS the input-validation hardening; no `JSON.parse as T`; no `catch` | compliant (improves validation) |
| SOUL No-Silent-Fallbacks | adapter emits distinct `"malformed"` ≠ `"null"` | compliant at adapter; **display layer re-folds** → see [SILENT] finding |
| SOUL No-fabricated-values | `cached` stays `null` for malformed; chart shows `n/a`, never invents a number | compliant |

### Observations (≥5)

- `[VERIFIED]` 125-1 fix carries the real turn — `TokenBarChart.tsx:65` adds `turnIndex: t.turnIndex` to each hitPoint and `:149-151` reads `T${p.turnIndex}`. The post-filter `i+1` is gone from the label (the `key={`hr${i}`}` still uses `i`, which is correct for React keys). Evidence: diff hunk @@ -61 and @@ -146.
- `[VERIFIED]` 125-2 keeps BOTH surfaces — the per-bar hover `<title>` n/a at `:93` is untouched; the new visible `<text>` caption is added only in the `knownTurns.length === 0` else-branch. SM's risk-note ("keep both") is satisfied. Evidence: `:92-93` unchanged, `:166-170` new ternary.
- `[VERIFIED]` 125-3 distinguishes absent from malformed — `telemetryAdapter.ts:109-121`: `pendingUsage == null` (absent / no-prompt) stays `"null"`; present dict with non-numeric `cache_read` → `"malformed"`; `cached` left `null`. Confirmed by the 5 adapter tests (2 malformed, 3 guards). [SEC] confirms no value from the untrusted object reaches JSX.
- `[SILENT] [MEDIUM]` All-non-SDK caption mislabels a malformed-only (or null+malformed) session as `"cache: n/a (non-SDK)"` at `TokenBarChart.tsx:166` — because malformed turns have `cached === null` and so drop out of `knownTurns`. The schema-drift signal 125-3 surfaces in the model is re-folded to "non-SDK" at the display layer. Confirmed (matches No-Silent-Fallbacks, not dismissible) but downgraded to Medium — see verdict rationale. Already self-logged by Dev as an Improvement.
- `[TYPE]` (manual) Union widening `"warm"|"cold"|"null"|"malformed"` is sound type design — a meaningful literal member, no stringly-typing, no `switch` left non-exhaustive (only `=== "cold"`/`=== null` equality consumers, verified by grep). Minor: the inline hitPoint type `{x;rate;cold;turnIndex}` is duplicated in the map return and the filter predicate — acceptable for a 4-field local.
- `[SIMPLE]` (manual) No over-engineering; the `&&`→ternary swap is the minimal change for the caption. No dead code.
- `[DOC]` (manual) New comments are accurate — the `turnIndex` comment correctly explains the post-filter divergence; the `cacheState` doc and the malformed-branch comment match behavior. No stale/misleading docs introduced.
- `[TEST]` (manual) Tests are non-vacuous and pin the right contracts; guards (aligned-index, absent≠malformed, warm-unaffected, savings-line-when-known) protect against over-correction. Low nit: the `r.cacheState as string` casts are now redundant post-widening (harmless, document the TDD ordering).
- `[EDGE]` (manual) Empty `data` → early `"No data yet"` return before the changed code. `typeof NaN === "number"` would pass a `cache_read: NaN` into `"cold"`, but JSON telemetry cannot carry `NaN` (no NaN literal in JSON) and the original code had the identical guard — unreachable and not a regression.
- `[RULE]` (manual) Full TS-checklist enumeration above — all applicable checks compliant.

### Devil's Advocate

Let me argue this code is broken. The loudest claim: 125-3 advertises itself as a No-Silent-Fallbacks fix, yet the very same PR re-buries the signal. The adapter dutifully stamps `cacheState: "malformed"`, and then `TokenBarChart` throws that distinction away — a malformed turn has `cached === null`, so it is invisible to `knownTurns`, to `savedFromCache`, to `coldTurns`, and to `hitPoints`, and the only place it could surface visibly — the summary caption — hard-codes the words "non-SDK". So a GM staring at a session where the server emitted broken payloads reads a calm "cache: n/a (non-SDK)" and concludes "ah, Ollama, nothing wrong here," when the truth is "the server's cache schema drifted." That is precisely the masking the story set out to kill, relocated from the adapter to the view. A skeptic says: you didn't fix the silent fallback, you moved it one layer up and called it done.

That argument is real, and it's why I will NOT dismiss the finding — it matches a load-bearing project rule. But is it *blocking today*? No. The malformed state is unreachable in production: the server contract guarantees `cache_read` is an int whenever `cache_usage` is present (`test_prompt_cache_attribution_otel.py`), so `knownTurns.length === 0` means "all genuinely null" and the caption is *correct* for every session that can actually occur right now. The malformed×caption cross-product only manifests under a future server regression — and when that regression lands, the adapter's `"malformed"` state is already in the model, queryable and test-covered, ready for a caption branch to consume. What would a malicious user do? Nothing — this is a read-only GM dev surface, all rendered values are numeric or static literals, React escapes the text, and [SEC] found no injection vector. What would a confused user misunderstand? Exactly the "non-SDK" label above — which is why it must be captured, not buried. What about a stressed event stream — duplicate prompts, missing fields? The most-recent-prompt-wins logic is unchanged; `token_count_in ?? 0` silently zeroes an absent field, but that is pre-existing code outside this diff. Conclusion: a genuine legibility gap on an unreachable-today path, honestly pre-disclosed by Dev, belonging in epic 125's tech-debt backlog — not a defect in the delivered scope of three 1-point stories that never specified the cross-product.

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** `WatcherEvent.fields.cache_usage` (WebSocket telemetry) → `buildTurnTokenCacheRows` type-guards `cache_read` → emits `cacheState ∈ {warm,cold,null,malformed}` with `cached: number|null` → `TokenBarChart` renders numeric/static strings into React-escaped SVG `<title>`/`<text>`. Safe: no untrusted value reaches JSX as markup; no `dangerouslySetInnerHTML`; [SEC] clean.

**Subagent dispatch:**
- `[SILENT]` (silent-failure-hunter, high-confidence) — **CONFIRMED, downgraded to Medium (non-blocking).** Caption mislabels malformed-only/mixed sessions as "non-SDK" (`TokenBarChart.tsx:166`). NOT dismissed (matches No-Silent-Fallbacks). Downgraded because: (a) the `"malformed"` state is unreachable in production today per the server contract, so every *actually-occurring* all-null session is labelled correctly; (b) the adapter layer — the story's stated scope — is honest; (c) the malformed×caption cross-product is beyond 125-1/2/3's specified scope, and 125-2's test pins the "non-SDK" wording for the all-null case. Captured as a deferred Delivery Finding for epic 125 (tech-debt home). Independently pre-logged by Dev.
- `[SILENT]` low (`token_count_in ?? 0` zeroes an absent field) — **DEFERRED**: pre-existing, outside the diff's changed lines.
- `[SEC]` — clean (6 render sites + cache_usage handling checked; No-Silent-Fallbacks + No-fabricated-values compliant).
- `[EDGE] [TEST] [DOC] [TYPE] [SIMPLE] [RULE]` — specialists disabled via settings; covered manually above. No blocking issues; one Low nit (redundant `as string` casts) and one Low note (inline-type duplication), neither blocking.

**Pattern observed:** Defensive type-state widening done right — `telemetryAdapter.ts:56` widens the literal union and `:109-121` adds the branch without disturbing the existing warm/cold/null logic; no production `switch` left non-exhaustive (verified by grep).

**Error handling:** The malformed branch is itself the error-surfacing path; `cached` stays `null` (no fabrication). Null/absent/empty inputs all handled (empty→early return; absent→"null"; non-numeric→"malformed").

**Verdict basis:** 0 Critical, 0 High. Tests GREEN (2351/2351), lint/tsc clean. The single confirmed finding is Medium/non-blocking on an unreachable-today path and is captured for follow-up.

**Handoff:** To SM (Vizzini) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): 125-3's fix requires widening the `cacheState` union to `"warm" | "cold" | "null" | "malformed"`. Affects `sidequest-ui/src/components/Dashboard/source/telemetryAdapter.ts` (extend the `TurnTokenCacheRow["cacheState"]` union + add the malformed branch in `buildTurnTokenCacheRows`: `havePending && pendingUsage != null && typeof pendingUsage.cache_read !== "number"` → `"malformed"`). No exhaustive `switch` on `cacheState` exists in production — only `=== "cold"` equality in `TokenBarChart.tsx` — so the widening is safe (verified by grep). A malformed row keeps `cached: null`, so the chart renders it fresh-only like a null turn; no chart change is needed for 125-3. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): A `"malformed"` turn now exists in the data model but the chart renders it identically to a `"null"` (non-SDK) turn — fresh-only, and the all-non-SDK caption would read "non-SDK" even if the cause was schema drift. A future enhancement could surface malformed turns distinctly in `TokenBarChart` (e.g. an accent mark or a separate caption). Affects `sidequest-ui/src/components/Dashboard/charts/TokenBarChart.tsx` (out of scope for 125-3, which is adapter-level hardening only). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): The all-non-SDK caption renders `"cache: n/a (non-SDK)"` for a session of all-`malformed` (or mixed null+malformed) turns — re-folding the schema-drift signal 125-3 surfaces at the adapter layer back into "non-SDK" at the display layer. Affects `sidequest-ui/src/components/Dashboard/charts/TokenBarChart.tsx:166` (add a `data.some(t => t.cacheState === "malformed")` branch with a distinct caption, e.g. "cache: malformed payload (schema drift)"; fall through to "non-SDK" only when all non-known turns are `"null"`). Non-blocking — `"malformed"` is unreachable in production today (server guarantees well-formed `cache_usage` per `test_prompt_cache_attribution_otel.py`); a natural epic-125 tech-debt follow-up. Corroborates Dev's own Improvement note. *Found by Reviewer during code review.*
- **Gap** (non-blocking): Pre-existing — `buildTurnTokenCacheRows` (`sidequest-ui/src/components/Dashboard/source/telemetryAdapter.ts:104-105`) silently defaults `token_count_in/out` to `0` when absent from `turn_complete`, masking a missing field as a 0-token turn. Outside this diff's changed lines; flagged for a future No-Silent-Fallbacks pass. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Pinned 125-3's "surface the anomaly" contract to a distinct `cacheState: "malformed"`**
  - Spec source: story 125-3 description
  - Spec text: "Surface the anomaly: either a console.warn or a distinct 'malformed' cacheState (implementer's choice; avoid noisy prod logging)."
  - Implementation: tests assert `cacheState === "malformed"`, removing the console.warn-only option from Dev's choice.
  - Rationale: a return-value contract is deterministically assertable in a pure-function unit test, whereas a console.warn couples the test to a spy on a global side effect AND leaves the data model itself still folding malformed into `null`. The SM assessment explicitly delegated this pick to TEA ("TEA should pick the assertable surface"). Dev MAY additionally `console.warn`, but the `cacheState` value is the pinned, tested contract.
  - Severity: minor
  - Forward impact: Dev must widen `TurnTokenCacheRow["cacheState"]` to include `"malformed"`; no chart change (a malformed row renders fresh-only like a null turn).

### Dev (implementation)
- No deviations from spec. Implemented all three fixes exactly to TEA's tests: carried `turnIndex` into the hit-rate dots (125-1), added the visible all-non-SDK caption while keeping the hover `<title>` n/a (125-2), and surfaced malformed `cache_usage` as the distinct `"malformed"` cacheState (125-3, TEA's pinned contract — no console.warn added).

### Reviewer (audit)
- **TEA — Pinned 125-3's contract to `cacheState: "malformed"`** → ✓ ACCEPTED by Reviewer: a return-value contract is the assertable, honest surface; SM explicitly delegated the pick to TEA; the resulting 3→4 union widening is safe (no non-exhaustive consumers, verified by grep). Sound — agrees with author reasoning.
- **Dev — No deviations from spec** → ✓ ACCEPTED by Reviewer: verified the implementation matches TEA's tests exactly and the no-`console.warn` choice is consistent with the story's "avoid noisy prod logging." No undocumented spec deviation found in the diff. The one display-layer gap (malformed→"non-SDK" caption) is a scope-boundary follow-up, not a deviation from the three stories' stated scope — captured as a Delivery Finding above.