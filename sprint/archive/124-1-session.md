---
story_id: "124-1"
jira_key: "124-1"
epic: "124"
workflow: "tdd"
---
# Story 124-1: Timing token chart — per-turn cached/fresh split + cache-hit sparkline

## Story Details
- **ID:** 124-1
- **Jira Key:** 124-1
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-16T12:35:51Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-16T11:58:44+00:00 | 2026-06-16T12:01:16Z | 2m 32s |
| red | 2026-06-16T12:01:16Z | 2026-06-16T12:21:56Z | 20m 40s |
| green | 2026-06-16T12:21:56Z | 2026-06-16T12:28:56Z | 7m |
| review | 2026-06-16T12:28:56Z | 2026-06-16T12:35:51Z | 6m 55s |
| finish | 2026-06-16T12:35:51Z | - | - |

## Repos
- **sidequest-server** (develop → feat/124-1-timing-token-cached-fresh-split)
- **sidequest-ui** (develop → feat/124-1-timing-token-cached-fresh-split)

## Design Notes

### Open Wiring Question (For DEV Phase)
The cache metrics (cache_read, cache_hit, cold) currently live on the **prompt_assembled event** (PromptFields.cache_usage), not on turn_complete (TurnCompleteFields). The Inspector dashboard needs per-turn cache visibility to render the stacked token chart.

**Two wiring options exist (choose in DEV phase):**

(a) **Server-side per-turn cache field:** Add a cache field to turn_complete event server-side, populated from the prompt_assembled event. This is the "right" place semantically.

(b) **Dashboard-side join:** In the telemetryAdapter (dashboard), join prompt_assembled.cache_usage to turns by turn_number. This avoids a server change but couples the dashboard logic to the event structure.

**Critical constraint:** cache_usage can be null for non-SDK backends (e.g., claude-p, Ollama). The charts must render only what's present with no fabricated estimates (No Silent Fallbacks).

## SM Assessment

**Scope (5pt, tdd, server + ui):** Split the per-turn tokens-in chart into cached (faded) vs fresh (solid) stacked bars on a shared scale, add a cache-hit-rate sparkline (cold-start misses flagged in accent), and a "served from cache" savings summary. Frontend lands in `sidequest-ui` `charts/TokenBarChart.tsx`; the data plumbing decision spans both repos.

**The load-bearing question (do NOT pre-decide — Architect/Dev own it):** cache fields (`cache_read`/`cache_hit`/`cold`) live on the `prompt_assembled` event (`PromptFields.cache_usage`), not on `turn_complete` (`TurnCompleteFields`). Two wiring options, captured in Design Notes above:
- (a) add a per-turn cache field to `turn_complete` server-side (semantically cleaner; a server change + new test);
- (b) join `prompt_assembled.cache_usage` to turns by `turn_number` in the dashboard `telemetryAdapter` (no server change; couples dashboard to event shape).

This choice determines whether the server repo carries real work or is a no-op. **TEA: write the RED tests around the chosen contract — but the choice is a design step.** If it isn't obvious from the existing telemetryAdapter shape, flag for a quick Architect (The Man in Black) consult before locking the red tests, so we don't pin tests to a contract Dev then abandons.

**Hard constraint for every test:** `cache_usage` is null for non-SDK backends (claude-p, Ollama). Charts render only what's present — **no fabricated/estimated cache splits** (No Silent Fallbacks). A test asserting graceful null-handling is mandatory, plus a wiring test proving `TokenBarChart` is actually mounted in the Inspector (not just unit-green).

**Verification env reminder for the test phase:** server suite needs `SIDEQUEST_DATABASE_URL` + `SIDEQUEST_GENRE_PACKS`; run the full suite and baseline pre-existing failures (notably in-flight epic-108 `tests/genre/` beat failures) rather than mislabeling them as regressions.

## TEA Assessment

**Tests Required:** Yes (UI only — see Findings: server is a no-op for option (b))
**Phase:** finish
**Status:** RED — 18 failing, 2 deliberate green guards (verified via verbose vitest)

**Contract source:** Architect (The Man in Black) ratified the wiring contract 2026-06-16 (consult run `a79ab1074ca37e211`), grounded in measured server facts. Decision: **option (b), dashboard-side join** — the data is already 100% client-side (`view.turns` + `view.allEvents` in both live and forensic paths), and option (a) would create a redundant second source of truth for `cache_read`. **Server carries no production change.**

**The honest math (every test pins it):**
- `fresh = turn_complete.token_count_in` — this is the narrator's Anthropic `input_tokens`, already **cache-EXCLUSIVE** (`anthropic_sdk_client.py:439-442`).
- `cached = prompt_assembled.cache_usage.cache_read`.
- Stack is **ADDITIVE**: total = cached + fresh. `fresh` is **never** `token_count_in − cache_read` (that double-discounts the cache — a RED test forbids it explicitly).
- Join is **stream-order adjacency within a session**, NOT by `turn_number` (which collides across sessions in a forensic bundle and would cross-attribute cache).
- **cold** (cache_usage present, `cache_read===0`) ≠ **null** (no cache_usage; non-SDK). null is excluded from hit-rate and never scored as a miss.

**Test Files (sidequest-ui):**
- `src/components/Dashboard/__tests__/telemetryAdapter-cache-join.test.ts` (8) — the `buildTurnTokenCacheRows` join contract: additive/no-subtract, turnIndex/turnNumber, cold-vs-null, session-safe adjacency pairing (incl. the cross-session no-attribution guard), most-recent-prompt selection, no double-consume.
- `src/components/Dashboard/__tests__/TokenBarChart-cache-split.test.tsx` (9) — stacked cached+fresh on the shared scale, combined-total peak, served-from-cache savings (real `cache_read` sum only), cold-start flag present/absent, null honesty (n/a, never fabricated), empty-state preserved.
- `src/components/Dashboard/__tests__/TimingTab-cache-split.test.tsx` (3) — end-to-end wiring (tab→adapter→chart) + graceful degrade with no prompt stream (no fabricated cache).

**Tests Written:** 20 across 3 files, covering all 4 ACs + the CLAUDE.md wiring requirement.
- AC-1 (per-turn cache_read/fresh_in/cache_hit/cold via dashboard join) → telemetryAdapter-cache-join.
- AC-2 (stacked cached+fresh on shared honest scale) → TokenBarChart stack + combined-total tests.
- AC-3 (hit-rate sparkline w/ cold accent + savings line) → TokenBarChart cold-flag + savings tests.
- AC-4 (null renders honestly, no estimate) → null tests in all three files.
- Wiring (TokenBarChart mounted in the Inspector) → TimingTab-cache-split end-to-end render.

### Rule Coverage (lang-review/typescript.md)

| Rule | Test(s) | Status |
|------|---------|--------|
| #4 null/undefined — `0` is falsy-but-valid (`??` not `\|\|`) | cold test asserts `cached===0` (known zero), null test asserts `cached===null` — catches a `cache_read \|\| null` bug that would mislabel a cold turn | failing (RED) |
| #4 null/undefined — distinct null handling | "marks a non-SDK turn as null" + "no preceding prompt → null" | failing (RED) |
| #2 interface (no `Record<string, any>`) | `TurnTokenCacheRow` is a typed interface w/ a `"warm"\|"cold"\|"null"` union — Dev must keep it typed | enforced by import in tests |
| #6 React (key stability / useMemo deps) | TimingTab wiring test renders the real tab; Dev keeps append-only key pattern + memo deps | covered by render |
| #8 test quality (no vacuous asserts) | self-check below; 3 negative-only tests given positive RED anchors | done |

**Rules checked:** 4 of 8 typescript lang-review groups apply (1,2,4,6,8 partially); 3,5,7 (enums, module/ESM, async) are N/A to a sync pure-join + SVG render.
**Self-check:** Re-ran verbose; the 3 previously-trivial negative tests (#4/#6/#7 in TokenBarChart) were tightened with positive anchors (`n/a` marker / rendered `cache_read`) and now fail RED. The 2 remaining green tests are *intentional* back-compat guards (empty-state survives the redesign; no-prompt-stream degrades without fabricating cache) — both carry real assertions that catch regressions, neither is vacuous.

**Handoff:** To Dev (Inigo Montoya) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed (sidequest-ui only):**
- `src/components/Dashboard/source/telemetryAdapter.ts` — new `TurnTokenCacheRow` interface + `buildTurnTokenCacheRows(events)`: the stream-order, session-safe join. Additive split (cached=`cache_read`, fresh=`token_count_in`); cold (`cache_read===0`) vs null (no `cache_usage`) kept distinct via an explicit numeric check (no `||` falsy collapse — addresses TEA's lang-review #4 finding).
- `src/components/Dashboard/charts/TokenBarChart.tsx` — stacks cached (faded, opacity 0.32) under fresh (solid) on the shared scale (peak now reflects cached+fresh); cache-hit-rate dot track with cold-start misses in `THEME.accent`; "served from cache N tokens · M cold-start miss(es)" summary from real `cache_read` only; null turns render fresh-only with an explicit `cache n/a` tooltip.
- `src/components/Dashboard/tabs/TimingTab.tsx` — optional `allEvents` prop; builds the chart data via `buildTurnTokenCacheRows(allEvents ?? turns)` (degrades to fresh-only when the stream is absent); subtitle updated to "cached · fresh · out".
- `src/components/Dashboard/DashboardApp.tsx` — passes `allEvents={view.allEvents}` to `TimingTab` (both live + forensic paths).

**Tests:** 20/20 story tests GREEN; full Dashboard suite 90/90 (no regressions). `tsc -b` clean, `eslint` clean.
**Branch:** `feat/124-1-timing-token-cached-fresh-split` (sidequest-ui, pushed).
**Server:** no changes — confirmed no-op (see Findings). No server branch work.

**Handoff:** To Reviewer (Westley) for code review.

## Delivery Findings

### TEA (test design)
- **Gap** (blocking): With option (b) chosen, the **`sidequest-server` repo is a no-op for 124-1** — the UI's only new dependency (`prompt_assembled.cache_usage.cache_read` per narrator turn, and `cache_usage===null` for non-SDK) is ALREADY fully guarded by `tests/agents/test_prompt_cache_attribution_otel.py` (`test_cache_usage_carries_real_sdk_numbers_not_estimates`, `test_cache_usage_is_explicit_na_when_sdk_usage_unavailable`). Writing a server "contract guard" would duplicate existing coverage (makework). **Action for SM/Dev:** drop `server` from 124-1's scope and delete the empty `feat/124-1-timing-token-cached-fresh-split` branch in `sidequest-server` before finish, so the finish ceremony does not create an empty server PR. *Found by TEA during test design.*
- **Improvement** (non-blocking): Dev must guard the `cache_read === 0` case against the `||` falsy trap (lang-review #4) — use explicit `cache_read` presence checks, not `cache_read || ...`, or a cold turn (real 0) collapses into the null/unknown bucket. The RED cold test pins this. Affects the new `buildTurnTokenCacheRows` in `sidequest-ui/.../source/telemetryAdapter.ts`. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (blocking): Reaffirming TEA's finding for the Reviewer/SM — **`sidequest-server` has zero changes**; this shipped UI-only (option b). The empty `feat/124-1-timing-token-cached-fresh-split` branch in `sidequest-server` must be dropped before finish so the finish ceremony does not attempt an empty server PR. The UI's `cache_read` dependency is already guarded by `tests/agents/test_prompt_cache_attribution_otel.py`. *Found by Dev during implementation.*
- Implemented TEA's lang-review #4 guard (explicit `typeof cache_read === "number"` + `cached > 0 ? warm : cold`), so `cache_read === 0` resolves to cold, not null. No other upstream findings.

### Reviewer (code review)
- **Improvement** (non-blocking): Hit-rate dot tooltip mislabels the turn number when `null` turns are interspersed before a known turn — `TokenBarChart.tsx:143` uses the post-`filter` index `i+1` instead of the turn's real `turnIndex`. Dot position (`p.x`) and the aggregate cold-miss count are correct; only the hover label is wrong. Fix: carry `turnIndex` into the `hitPoints` objects and use it in the `<title>`. Affects `sidequest-ui/src/components/Dashboard/charts/TokenBarChart.tsx`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): In an all-non-SDK session (every turn `cacheState: "null"`), the "served from cache" summary is suppressed and the only `n/a` is inside per-bar SVG `<title>` tooltips (hover-only). Consider a visible "cache: n/a (non-SDK)" caption so the absence of cache data is legible without hovering. AC-4 ("no fabricated estimate") is met; this is a legibility enhancement. Affects `sidequest-ui/.../charts/TokenBarChart.tsx`. *Found by Reviewer during code review (via silent-failure-hunter).*
- **Improvement** (non-blocking): `buildTurnTokenCacheRows` folds a malformed `cache_usage` dict (present but `cache_read` absent/non-numeric) into the same `"null"` bucket as a genuinely-absent `cache_usage`. The current server contract guarantees `cache_read` is an int whenever the dict is present (`test_prompt_cache_attribution_otel.py`), so the realistic surface is nil — but per "No Silent Fallbacks" a `console.warn` on the malformed case would surface server schema-drift instead of masking it as "non-SDK". Affects `sidequest-ui/.../source/telemetryAdapter.ts`. *Found by Reviewer during code review (via silent-failure-hunter).*
- **Gap** (blocking, process — reaffirms TEA/Dev): `sidequest-server` has zero code changes; SM must drop `server` from 124-1's scope and delete the empty `feat/124-1-…` server branch before finish so the ceremony does not create an empty server PR. *Found by Reviewer during code review.*

## Design Deviations

### TEA (test design)
- **Server scoped out — story is UI-only under option (b)**
  - Spec source: `.session/124-1-session.md` Repos line + context-story-124-1.md ("Repo: server,ui")
  - Spec text: story scoped to `server,ui`; AC-1 reads "turn_complete (or a dashboard-side join)"
  - Implementation: RED tests written for `sidequest-ui` only; no server tests/code (option b — dashboard-side join; AC-1's "or a dashboard-side join" clause is satisfied client-side)
  - Rationale: cache data already lives authoritatively on `prompt_assembled` and is already test-guarded server-side; a server change would be a redundant second source of truth (Architect ruling + "Don't Reinvent")
  - Severity: minor (scope correction, not a behavior change)
  - Forward impact: SM/Dev must drop the `sidequest-server` branch before finish (see blocking Finding)
- **Join keyed on stream-order adjacency, not `turn_number`**
  - Spec source: context-story-124-1.md, problem statement ("join … by turn_number in the dashboard telemetryAdapter")
  - Spec text: "(b) join prompt_assembled cache_usage to turns by turn_number"
  - Implementation: tests pin pairing by stream-order adjacency within a session, NOT by `turn_number`
  - Rationale: `turn_number` collides across sessions in a forensic bundle (the same hazard the timeline session-divider already works around); a `turn_number` join would cross-attribute one session's cache onto another's — a chart that lies. Architect-ratified.
  - Severity: minor (refines the spec's suggested mechanism to a correct, session-safe one)
  - Forward impact: none — the join still lives in `telemetryAdapter.ts` as the story intended

### Dev (implementation)
- Implementation followed TEA's tests and the Architect-ratified contract exactly; no further deviations from spec.
- **TimingTab gained an optional `allEvents` prop rather than re-deriving order from `turns`+`promptEvents`**
  - Spec source: TEA tests (TimingTab-cache-split.test.tsx) + Architect ruling (join in telemetryAdapter on the ordered stream)
  - Spec text: "the join lives in telemetryAdapter.ts … pass the ordered full event stream"
  - Implementation: TimingTab takes `allEvents?` and calls `buildTurnTokenCacheRows(allEvents ?? turns)`; DashboardApp feeds `view.allEvents`. The prop is optional so existing `<TimingTab turns={…} />` callers/tests keep working (degrade to fresh-only).
  - Rationale: stream-order adjacency pairing needs the interleaved order, which the separate `turns`/`promptEvents` arrays lose; `allEvents` preserves it and exists in both live and forensic `view`s.
  - Severity: trivial (additive optional prop)
  - Forward impact: none

### Reviewer (audit)
- **TEA: "Server scoped out — story is UI-only under option (b)"** → ✓ ACCEPTED by Reviewer: sound. AC-1's "(or a dashboard-side join)" clause authorizes it; the `cache_read` contract is already guarded by `test_prompt_cache_attribution_otel.py`, so a server change would be a redundant second source of truth. SM must drop the server branch at finish (tracked as a blocking process finding).
- **TEA: "Join keyed on stream-order adjacency, not `turn_number`"** → ✓ ACCEPTED by Reviewer: correct and necessary. Verified `buildTurnTokenCacheRows` pairs by adjacency (telemetryAdapter.ts:107) and the RED test `pairs by adjacency … (no cross-session attribution)` proves no cross-session leakage. A `turn_number` join would have been a real correctness defect in forensic bundles.
- **Dev: "TimingTab gained an optional `allEvents` prop"** → ✓ ACCEPTED by Reviewer: the optional prop preserves the existing `<TimingTab turns={…} />` callers (TimingTab-phase-breakdown tests still green) and `allEvents` is the only source carrying interleaved order needed for adjacency pairing. Sound, minimal.
- No undocumented deviations found — the implementation matches the TEA tests and the Architect-ratified contract.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (90/90 tests, lint/tsc clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 (1 med, 1 med, 1 low) | confirmed 2 (non-blocking), dismissed 1 (rationale) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 3 confirmed non-blocking (2 from silent-failure-hunter + 1 from my own analysis), 1 dismissed (with rationale), 0 deferred. Zero Critical/High.

## Reviewer Assessment

**Verdict:** APPROVED

No Critical or High findings. All four story ACs are met, tests green (90/90), lint/tsc clean, security clean. Three small non-blocking improvements are documented for a fast follow-up; none degrade correctness of the core feature.

**Data flow traced:** `WatcherEvent` stream (`view.allEvents`, both live + forensic) → `DashboardApp` passes `allEvents` to `TimingTab` → `buildTurnTokenCacheRows` pairs each `turn_complete` with its preceding narrator `prompt_assembled` (stream-order, session-safe) → `TurnTokenCacheRow[]` → `TokenBarChart` renders stacked cached/fresh + hit-rate + savings. Safe: only numeric fields are extracted and only numbers reach the DOM; React escapes all `<title>`/`<text>` children. `[SEC]` confirmed clean — no `dangerouslySetInnerHTML`, no telemetry strings interpolated.

**Observations:**
- `[VERIFIED]` Additive split is honest — `telemetryAdapter.ts:101` `tokensIn = token_count_in` (cache-exclusive per Anthropic), `cached = cache_read`; chart stacks `tokensIn + (cached ?? 0)` on one shared scale (`TokenBarChart.tsx:54,87-90`). No subtraction anywhere. Complies with the story's honest-scale AC and No Silent Fallbacks.
- `[VERIFIED]` cold vs null distinct — `telemetryAdapter.ts:101-107` uses `pendingUsage != null && typeof cache_read === "number"`, then `cached > 0 ? "warm" : "cold"`. A real `cache_read===0` resolves to cold (known), absent `cache_usage` to null (unknown). The `||` falsy-collapse trap (lang-review #4) is correctly avoided — evidence: RED tests `flags a real cache miss … as cold with cached=0` and `marks a non-SDK turn … as null` both green.
- `[VERIFIED]` session-safe join — adjacency pairing (`telemetryAdapter.ts`, consume-on-turn at the loop tail), proven by the cross-session no-attribution RED test. A `turn_number` join would have leaked across sessions; this avoids it.
- `[SILENT][MEDIUM]` all-null session shows no *visible* cache caption — `n/a` lives only in hover `<title>` tooltips (`TokenBarChart.tsx:93`); savings line suppressed at `:149`. Honest (no fabrication) but not legible without hover. Non-blocking improvement.
- `[MEDIUM]` hit-rate dot tooltip mislabels turn number with interspersed null turns — `TokenBarChart.tsx:143` post-filter `i+1` vs real `turnIndex`. Position/count correct; hover label wrong. Non-blocking improvement (own analysis).
- `[SILENT][LOW]` malformed `cache_usage` (dict w/o numeric `cache_read`) silently folds to `"null"` — contract-prevented today; a `console.warn` would honor No Silent Fallbacks. Confirmed (matches the rule, not dismissed), severity LOW given nil realistic surface.
- `[SILENT]` dismissed: the `allEvents ?? turns` degraded path being "invisibly fresh-only" — dismissed because `DashboardApp` always supplies `allEvents`; the fallback is documented, honest, and fabricates nothing (not a silent fallback).
- `[VERIFIED]` no security surface — `[SEC]` subagent clean; only numeric data reaches the DOM, React auto-escapes.

### Rule Compliance (lang-review/typescript.md)
- **#1 Type-safety escapes:** No `as any`, no double-cast, no `@ts-ignore`. The `as TurnCompleteFields` / `as { cache_usage?… }` narrowing casts of the untyped `event.fields` match the file's existing pattern (`row.event_type as WatcherEventType`). The `hitPoints` type-predicate filter (`:66`) HAS a runtime `p !== null` check — compliant. ✓
- **#2 Interfaces:** `TurnTokenCacheRow` and `CacheUsageLike` are proper interfaces (no `Record<string, any>`); `cacheState` is a `"warm"|"cold"|"null"` union. ✓
- **#4 Null/undefined:** the load-bearing rule — `cache_read` checked via `!= null && typeof === "number"` (not `||`), so `0` (cold) is preserved; `token_count_in ?? 0` uses `??` not `||`. ✓
- **#6 React/JSX:** `useMemo` deps `[allEvents, turns]` correct; index `key`s on append-only chronological lists match the pre-existing chart pattern (not reordered data). ✓
- **#8 Test quality:** TEA self-checked; 2 green guards are intentional back-compat, not vacuous. ✓
- **No Silent Fallbacks (CLAUDE.md, critical):** honored everywhere except the contract-prevented malformed-`cache_usage` case (LOW finding above) — confirmed, not dismissed.

### Devil's Advocate
Argue this is broken. A malicious or confused server emits a `prompt_assembled` with `cache_usage: {cache_write: 500}` — `cache_read` absent. The chart shows that turn as "non-SDK / n/a", identical to an Ollama turn, hiding the fact the server's SDK path is emitting a structurally broken event. The GM trusts the lie detector and never learns the cache accounting drifted. That's the F1 finding — real, but the server contract (and `test_prompt_cache_attribution_otel.py`) guarantees `cache_read` is present whenever the dict is, so today it cannot fire; it's hardening, not a live bug. Next: a session that alternates non-SDK and SDK turns (mixed backends mid-session — possible if `SIDEQUEST_LLM_BACKEND` changes). Now null turns are interspersed, and the hit-rate dot tooltips name the wrong turns (F4). A GM hunting "which turn missed cache" is misled by the hover — but the dot's x-position still sits under the correct bar and the aggregate count is right, so the misdirection is bounded to the hover string. What about huge sessions? `Math.max(...data.map(...))` spreads the array — a 100k-turn session could blow the call-stack arg limit, but that's the pre-existing chart pattern and session turn counts are bounded (tens–low hundreds); not introduced here. Empty/zero: `maxTok` floored at 1, `denom > 0` guards the rate division — no NaN/Infinity reaches SVG. A turn with `token_count_in` absent renders a 0-height fresh bar (honest, not a crash). Confused user: sees faded vs solid with a "cached + fresh" subtitle and per-bar tooltips — legible, except the all-null case (F2) where they must hover to learn cache data is absent. Net: the failure modes are either contract-prevented (F1), bounded-cosmetic (F4), or legibility (F2) — none corrupt data, crash, or fabricate. The core additive math, the session-safe join, and the no-fabrication contract all hold under adversarial poking.

**Handoff:** To SM (Vizzini) for finish-story. The server-branch scope correction is a blocking process finding for SM to action before finish.