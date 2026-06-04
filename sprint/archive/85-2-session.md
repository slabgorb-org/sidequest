---
story_id: "85-2"
jira_key: ""
epic: "85"
workflow: "tdd"
---

# Story 85-2: Location surface — pick ONE source of truth for where-am-I (header vs Location tab) — design-first

## Story Details

- **ID:** 85-2
- **Jira Key:** (no-jira project)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-04T18:41:33Z
**Round-Trip Count:** 1

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-04T17:50:35Z | 2026-06-04T17:52:31Z | 1m 56s |
| red | 2026-06-04T17:52:31Z | 2026-06-04T18:19:34Z | 27m 3s |
| green | 2026-06-04T18:19:34Z | 2026-06-04T18:23:04Z | 3m 30s |
| review | 2026-06-04T18:23:04Z | 2026-06-04T18:30:15Z | 7m 11s |
| red | 2026-06-04T18:30:15Z | 2026-06-04T18:35:16Z | 5m 1s |
| green | 2026-06-04T18:35:16Z | 2026-06-04T18:36:48Z | 1m 32s |
| review | 2026-06-04T18:36:48Z | 2026-06-04T18:41:33Z | 4m 45s |
| finish | 2026-06-04T18:41:33Z | - | - |

## Story Context

This is a **design-first** story. The full acceptance criteria, technical guardrails, business context, and scope boundaries are documented in the existing story context:

**File:** `sprint/context/context-story-85-2.md`

### Key Business Points

- "Where am I?" is the most basic question a player asks, and SideQuest answers it **twice with two different answers**
- Header (free-text scene title) vs Location tab (region-level authored description) visibly disagree during intra-region POI moves
- This is a **single-source-of-truth design problem**, not an implementation bug
- Playtest finding **L105 a/b** (2026-06-04) surfaced the divergence

### Design Decision (Gating Deliverable)

The load-bearing deliverable is a **decision** — which binding is authoritative — recorded before implementation.

**Two candidate resolutions to weigh:**

1. **Payload-authoritative:** `LocationDescriptionPayload` is the truth; the header derives its label from the payload's `region_name`. Requires LOCATION_DESCRIPTION to re-emit on any move the header would reflect.
2. **Header-authoritative:** `current_location` (free-text scene title) is the truth; the Location tab updates its heading to match on every move, with the authored `prose` as sub-detail.

### Repos & Branches

- **Repos:** ui, server
- **Branch Strategy:** gitflow (develop → feat/85-2-location-source-of-truth)
- **Slug:** location-source-of-truth

## Sm Assessment

**Setup complete — routing to TEA (RED phase).** This is a design-first TDD story; the
authoritative context is `sprint/context/context-story-85-2.md` (validated). Parent epic context:
`sprint/context/context-epic-85.md`.

**For TEA (The Caterpillar):** AC-1 is the gating deliverable — the source-of-truth *decision*
(payload-authoritative vs header-authoritative) must be recorded before the implementation ACs
are testable. Surface that to the Architect (The White Queen) early; do not let RED tests
hard-code a resolution before the decision is recorded. The divergence is pinned in the context
doc to exact code:

- Header rides **PARTY_STATUS every turn** — `sidequest-ui/src/hooks/useRunningHeader.ts:20-43`
  (reads `CharacterSummary.current_location`); server origin `views.py:442-455`.
- Location tab's `LocationDescriptionPayload` re-emits **only on room_id change** —
  `map_emit.py:~388`; client `LocationPanel.tsx:41-184`, type `payloads.ts:775-793`.
- The reproduction test (AC-2/AC-3) is an **intra-region POI move** that changes
  `party_location()` without changing room_id — header updates, tab goes stale.

**Existing test surfaces to extend (don't reinvent):** UI —
`useRunningHeader.test.tsx`, `GameBoard/__tests__/GameBoard-location-tab.test.tsx`; server —
`tests/server/test_location_description_emit.py`, `..._resume.py`. ADR-109 governs the
LocationDescription surface — read before deciding.

**Honor No Silent Fallbacks:** the chosen non-authoritative surface must be an explicit
derivation of the authority, not a quiet `||` dual-read masking the divergence (AC-4).

**Repos:** ui, server. **Branch:** `feat/85-2-location-source-of-truth` (from `develop`).
No Jira (no-jira project).

## AC-1 Decision (Operator, 2026-06-04)

**RECORDED: Location is a two-level hierarchy — Region › Subregion — displayed as a
"Region — Subregion" breadcrumb.** Operator (Keith) call.

- The header (`useRunningHeader`) and the Location tab (`LocationPanel`/`LocationDescriptionPayload`)
  are **different granularities, not a binding conflict**: header = per-PC scene (preserves
  S2-UX(c)); tab = region-level shared record (preserves ADR-109). Neither original framing
  (payload-authoritative / header-authoritative) was adopted — both regress prior art.
- The tab must legibly show **`Region — Subregion`** so the two surfaces read as one hierarchy,
  and the tab must **stop going stale** on intra-region moves (the L105 a/b defect: emit gate at
  `map_emit.py:~388` only fires on `room_id` change).
- Architect (White Queen) is converting this into the precise payload/emit contract (where the
  per-PC subregion lives vs the shared region payload; server-half-or-UI-only; OTEL). RED tests
  are authored against that contract once returned. Until then, do NOT hard-code subregion
  sourcing in tests.

## TEA Assessment

**Tests Required:** Yes
**Phase:** finish
**Status:** RED (3 failing — ready for Dev)

**Final contract (Architect-confirmed UI-only):** the subregion is composed **client-side**
from the LOCAL player's `current_location` (the same per-turn-fresh value `useRunningHeader`
reads) + the shared `LocationDescriptionPayload.region_name`. **No new payload field, no server
emit-gate change, no new OTEL** — an intra-region re-emit is byte-identical because the region
record is `current_region`-keyed (ADR-109). `useRunningHeader` is untouched (S2-UX(c) preserved).

**Test Files:**
- `sidequest-ui/src/components/__tests__/LocationPanel.test.tsx` — breadcrumb composition (1 RED)
  + 4 companion guards (no separator when absent; no doubling on case/trim-insensitive equality;
  no dangling dash / `undefined` / `null`; `region_id` fallback when `region_name` absent).
- `sidequest-ui/src/components/GameBoard/__tests__/GameBoard-location-tab.test.tsx` — end-to-end
  wiring (2 RED): local-PC subregion (NOT a peer's — guards the per-PC `ignores non-local party
  members` invariant); not-stale-on-intra-region-move via PARTY_STATUS rerender (same
  `LocationDescriptionPayload`, only `current_location` changes → subregion segment updates,
  region segment holds).

**Tests Written:** 7 new (3 RED positive/wiring + 4 guards) covering AC-1's display contract.
**RED verified:** 3 assertion failures (not infrastructure — tab clicks, panel mounts,
`location-header` resolves); pre-existing Story 54-9 tests still pass; no regressions.

**The Dev seam (GREEN target):**
1. Add `subregion?: string | null` to `LocationPanelProps` (+ thread through `LocationWidget`).
2. `regionDisplayName(data, subregion)` composes `` `${region} — ${subregion}` `` with the locked
   separator ` — ` (space · EM DASH U+2014 · space) — only when subregion is present, non-blank,
   and `!== region` (case/trim-insensitive). Region segment = `region_name || region_id`.
3. `GameBoard` (`GameBoard.tsx:~506`) passes the LOCAL PC's `current_location`
   (`characters.find(c => c.player_id === currentPlayerId)?.current_location`) as `subregion`.
4. Do **NOT** touch `useRunningHeader`, `LocationDescriptionPayload`, or the server.

### Rule Coverage

| Rule (lang-review/typescript.md) | Test(s) | Status |
|------|---------|--------|
| #4 null/undefined — no `\|\|` silent fallback on `""` | breadcrumb "no dangling dash / undefined / null"; "no doubling on equality" | failing-or-guard |
| #8 test quality — meaningful assertions, no `as any` | all 7 (assert real `textContent`); self-check below | pass |

**Rules checked:** 2 of 13 TS lang-review rules are story-applicable (the rest — enums, async,
input-validation, build-config — don't apply to a cosmetic breadcrumb composition).
**Self-check:** 0 vacuous assertions; 0 `as any`; no `@ts-expect-error` left dangling (removed so
GREEN's tsc stays clean once `subregion` exists).

**Handoff:** To Dev (White Rabbit) for GREEN.

### TEA Rework — Round 1 (post-review)

**Trigger:** Reviewer (Queen of Hearts) REJECTED on two HIGH-confidence false-green tests +
coverage/comment gaps. **All fixes are test-only; the implementation is unchanged and was already
correct — so the hardened suite is GREEN, not RED.**

**Changes (both test files):**
- **[HIGH fixed]** Split-party test (`GameBoard-location-tab.test.tsx`) now orders the local PC
  LAST — `[pc("p2","Engine Room"), pc("p1","Docking Crescent")]`, `currentPlayerId="p1"`. An
  index-based `characters[0]` pick now resolves to the peer ("Engine Room") and FAILS; only the
  correct `player_id` lookup passes. The invariant the test is named for is now actually enforced.
- **[HIGH fixed]** Slug-fallback guard (`LocationPanel.test.tsx`) now asserts the FULL
  `outer_coyote_star${SEP}Docking Crescent` breadcrumb — RED against an impl that drops the
  subregion on the `region_name`-absent branch.
- **[MEDIUM fixed]** Added `subregion={null}` literal guard (the untested third union value).
- **[MEDIUM fixed]** Added POI-image `alt` region-only guard — pins the intentional
  header-vs-alt divergence so a future change can't leak the subregion into screen-reader text.
- **[MEDIUM already satisfied]** The not-stale test already asserts "Docking Crescent" *before*
  the rerender (pre-existing lines), then the transition to "Cargo Spine" after — the reviewer's
  intermediate-assertion ask was already present; left as-is.
- **[LOW fixed]** De-staled the "RED today" comments and dropped the now-false `(RED)` name
  suffixes in both files.

**Dismissed findings (Reviewer concurred as non-blocking):** the inherited `toContain(region)` in
the no-subregion guard (harmless redundancy) and the tab-click coupling (real activation confirmed
by preflight) — left unchanged.

**Verification:** 34/34 GREEN (was 32; +2 net new tests); no regressions. Commit `fef7e55`.
**Note for Dev (White Rabbit):** this rework added NO implementation work — `LocationPanel.tsx`,
`LocationWidget.tsx`, `GameBoard.tsx` are unchanged from the GREEN commit `c3e16ce`. The tests are
already passing; your green phase is verify-and-forward to review.

**Handoff:** To Dev (White Rabbit) — verify GREEN, forward to review.

## Dev Assessment

**Implementation Complete:** Yes
**Scope:** UI-only (as TEA scoped; server untouched).

**Files Changed:**
- `sidequest-ui/src/components/LocationPanel.tsx` — added optional `subregion` prop;
  `regionDisplayName(data, subregion)` composes the `Region — Subregion` breadcrumb with the
  locked separator ` — ` (space · U+2014 · space), appending the subregion only when present,
  non-blank, and distinct from the region (case/trim-insensitive). Region segment stays
  `region_name || region_id`. POI image `alt` deliberately left region-only (the landscape is
  region-level).
- `sidequest-ui/src/components/GameBoard/widgets/LocationWidget.tsx` — threads `subregion`.
- `sidequest-ui/src/components/GameBoard/GameBoard.tsx` (`renderWidgetContent` `case "location"`) —
  passes the LOCAL player's `current_location`
  (`characters.find(c => c.player_id === currentPlayerId)?.current_location`) as `subregion`.
  `characters`/`currentPlayerId` were already in the `useCallback` deps — no dep change needed.

**Untouched (per contract):** `useRunningHeader` (S2-UX(c) per-PC freshness),
`LocationDescriptionPayload`/`payloads.ts` (ADR-109 region-keyed shared record), all server code.

**Tests:** 32/32 passing (GREEN) across both files; all 3 previously-RED tests now pass; no
regressions. `npx tsc --noEmit` clean; `eslint` clean on all changed files.
**Branch:** `feat/85-2-location-source-of-truth` (pushed, `c3e16ce`).

**Self-review:** wired GameBoard → LocationWidget → LocationPanel end-to-end (the wiring test
drives that path); follows the existing `regionDisplayName` pattern; AC-1 display contract met;
no-silent-fallback honored (blank/echoed subregion never produces a dangling dash or doubling).

**Handoff:** To TEA (verify phase — simplify + quality-pass).

### Dev Green-Verify — Round 1 (post-rework)

The Reviewer rejected on **test-quality** only; TEA's rework round 1 hardened the tests
(commit `fef7e55`) with **no implementation change**. My green phase here is verify-and-forward:

- **Implementation untouched:** `git diff c3e16ce HEAD -- LocationPanel.tsx LocationWidget.tsx
  GameBoard.tsx` is **empty**. The three source files are byte-identical to the original GREEN.
- **Tests:** 34/34 GREEN (was 32; +2 net new guards — `subregion={null}` literal, POI-`alt`
  region-only). No regressions.
- **`npx tsc --noEmit` clean; `eslint` clean** on the two changed test files.
- **Pushed:** `c3e16ce..fef7e55`.

No code work was required. **Handoff:** back to Reviewer (Queen of Hearts) for re-review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 32/32 green, tsc + eslint clean, no smells |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 7 | confirmed 2 (blocking) + 3 (non-blocking), dismissed 2 |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 | confirmed 3 (non-blocking, bundled into rework) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 1 | confirmed 1 (LOW, non-blocking) |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 2 confirmed blocking, 7 confirmed non-blocking, 2 dismissed (with rationale)

## Reviewer Assessment

**Verdict:** REJECTED

**Why a clean, rule-compliant implementation is still rejected:** the *code* is correct and
verified — rule-checker cleared 13 rules / 31 instances with no Critical/High, and No-Silent-
Fallbacks / No-half-wired / OTEL-exempt all PASS. This is a **TDD story, so the test suite is the
deliverable**, and two of its tests do not enforce the invariants their names assert. A test that
passes against the very bug it claims to guard is a defect in the deliverable, not a style nit.
The implementation does **not** change in rework — this is test-suite hardening + comment hygiene,
all in the test files.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] `[TEST]` | Split-party test false-greens: local PC `p1` is `characters[0]`, so a broken `characters[0]` index-pick passes identically to the correct `player_id` lookup — the "uses LOCAL not peer" guard is satisfied by array-position coincidence. | `GameBoard-location-tab.test.tsx:116` | Reorder so the local PC is NOT first: `[pc("p2","Engine Room"), pc("p1","Docking Crescent")]`, `currentPlayerId="p1"`. Then the test is RED against an index-based bug. |
| [HIGH] `[TEST]` | Slug-fallback guard never asserts the composed breadcrumb — only that the slug appears. An implementation that drops the subregion on the `region_name`-absent path passes clean. | `LocationPanel.test.tsx:339` | Assert the full composition: `toContain(`outer_coyote_star${BREADCRUMB_SEP}Docking Crescent`)`. |
| [MEDIUM] `[TEST]` | Not-stale test lacks an intermediate assertion that the header showed `Docking Crescent` *before* the rerender, so a memoised/non-propagating rerender could false-green. | `GameBoard-location-tab.test.tsx:128` | Assert the pre-rerender value, then the post-rerender transition. |
| [MEDIUM] `[TEST]` | `subregion={null}` (literal, distinct from omitted/`undefined`) — the only value in the `string\|null\|undefined` union with no test. | `LocationPanel.test.tsx:302` | Add a guard: `subregion={null}` → no separator. |
| [MEDIUM] `[TEST]`/`[DOC]` | The region-only `alt` divergence (`regionDisplayName(data)` at `LocationPanel.tsx:140`) is intentional but untested and undocumented — invites a well-meaning "fix" that adds subregion noise to screen-reader output. | `LocationPanel.tsx:140` + a new test | Add a test asserting `img alt` is region-only even when `subregion` is set; add a one-line comment at the call site. |
| [LOW] `[DOC]` | Stale "RED today" block comment + `(RED)` test-name suffixes now claim the feature is absent when it shipped in the same diff. | `GameBoard-location-tab.test.tsx:171`, `LocationPanel.test.tsx:320` | De-stale the comments; drop/adjust the `(RED)` suffixes. |

**Dismissed (with rationale):**
- `[TEST]` inherited `toContain("The Outer Coyote Star")` in the no-subregion guard is "non-load-bearing" (test-analyzer, low) — **dismissed**: a redundant-but-true assertion is harmless; the co-located `not.toContain(SEP)` carries the guard. Not worth a change.
- `[TEST]` tab-click `fireEvent` coupling could become a silent no-op if the default tab changes (test-analyzer, low) — **dismissed**: preflight confirms the click drives a real activation today (the panel mounts on click); speculative future-coupling, not a current defect.

**Confirmed findings by source:** `[TEST]` ×5 (test-analyzer), `[DOC]` ×3 (comment-analyzer), `[RULE]` ×1 (rule-checker, LOW img-alt — same locus as the MEDIUM above), `[SIMPLE]`/`[EDGE]`/`[SILENT]`/`[SEC]`/`[TYPE]` — n/a (subagents disabled or clean).

### Rule Compliance (lang-review/typescript.md — exhaustive, via rule-checker + my read)

- **#1 type-safety escapes** — COMPLIANT across all 8 instances: no `as any`, no `@ts-ignore`, no non-null assertions. `subregion?: string | null` (LocationPanel:10, LocationWidget:8), `characters?.find(...)?.current_location` (GameBoard:511) all clean.
- **#4 null/undefined** — COMPLIANT: `(subregion ?? "").trim()` handles null/undefined/`""` → empty → region-only (no dangling dash). `data.region_name && data.region_name.length > 0 ? region_name : region_id` is a deliberate non-empty guard, **not** a `||`-on-falsy bug. The only `||` in the diff is a boolean OR between two booleans (`sub.length === 0 || sub.toLowerCase() === region.toLowerCase()`) — correct.
- **#6 React/JSX** — COMPLIANT: `localSubregion` is a plain const inside the `case "location"` block, not a hook; `useCallback` deps already include `characters` + `currentPlayerId` (GameBoard:526) — no stale-closure/missing-dep.
- **#8 test quality** — the two HIGH findings above are the violations (weak/coincidental assertions); otherwise no `as any`, fixtures typed, wiring through real components.
- **#10/#13 security/regression** — COMPLIANT: display-only text, no injection surface; img-alt one-arg is intentional (LOW).
- **#2,#3,#5,#7,#9,#11,#12** — n/a (no enums/async/module/build/error-handling/perf surfaces touched).
- **CLAUDE.md No-Silent-Fallbacks / No-half-wired / OTEL-cosmetic-exempt** — all PASS (rule-checker confirmed; 3-hop wiring GameBoard→LocationWidget→LocationPanel with a real end-to-end wiring test).

### Devil's Advocate

Assume this is broken. The implementation reads `characters.find(c => c.player_id === currentPlayerId)?.current_location` — what if `currentPlayerId` is undefined (pre-identity, solo bootstrap)? Then `find` returns undefined, `localSubregion` is undefined, breadcrumb degrades to region-only. Safe. What if two PCs share a `player_id` (data bug)? `find` returns the first — but that's a server-side invariant violation, not this code's concern. What if `current_location` is a huge string or contains the em-dash separator itself (the existing fixtures literally use `"Bridge — Outer Coyote Star"`)? Then the header would render two ` — ` separators — visually ambiguous but not broken, and the region segment carrying an em-dash is a *pre-existing* server-supplied possibility this diff neither introduces nor worsens. What would a confused future maintainer do? Two things the tests fail to stop: (1) "simplify" the local-PC lookup to `characters[0]` — the split-party test would **still pass** because p1 is first, so the per-PC scene invariant (load-bearing for split-party play, the whole reason S2-UX(c) exists) silently dies with green tests; (2) "tidy" the slug-fallback branch to return the slug alone, dropping the subregion — the fallback guard would **still pass**. Both are exactly the regressions the tests are named to prevent, and both slip through. That is the case for rejection: not that the code is wrong today, but that the regression net has two holes shaped precisely like the most likely future mistakes. A stressed filesystem / weird config angle does not apply (pure client render of in-memory state). The malicious-input angle is nil (display-only, no sink). The real adversary here is the next well-meaning refactor, and the suite must be armed against it.

**Handoff:** Back to TEA (red rework) — harden the two false-green tests, add the null + alt-text + intermediate-staleness coverage, and de-stale the `(RED)` comments. Implementation unchanged; the strengthened tests should stay GREEN against the existing correct code.

## Subagent Results (Re-review — Round 2)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 34/34 green, tsc + eslint clean, zero smells |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | clean | 0 (both prior HIGH **CLOSED**) | N/A — confirmed split-party now discriminating + slug-fallback asserts full breadcrumb; new guards meaningful |
| 5 | reviewer-comment-analyzer | Yes | findings | 1 (3 prior **CLOSED**) | confirmed 1 (LOW, non-blocking) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | 0 | N/A — 13 rules / 31 instances, 0 violations; source confirmed unchanged |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 0 blocking, 1 confirmed non-blocking (LOW doc), 0 dismissed

## Reviewer Assessment (Re-review — Round 2)

**Verdict:** APPROVED

The rework was **test-only** (source byte-identical to the R1-approved GREEN, confirmed by
rule-checker + `git diff c3e16ce HEAD -- <source>` empty). Both blocking R1 findings are
**CLOSED**, verified by the specialists:

- `[TEST]` **Split-party false-green → CLOSED**: array reordered to `[p2 "Engine Room", p1
  "Docking Crescent"]`, `currentPlayerId="p1"`. The peer is now `characters[0]`, so an index-based
  pick resolves to "Engine Room" and trips both `toContain("…Docking Crescent")` and
  `not.toContain("Engine Room")`. Genuinely discriminating against the `player_id`-lookup
  regression. (test-analyzer + rule-checker concur.)
- `[TEST]` **Slug-fallback missing-breadcrumb → CLOSED**: now asserts the full
  `outer_coyote_star — Docking Crescent`, RED against an impl that drops the subregion on the
  `region_name`-absent branch.
- `[TEST]` New guards (`subregion={null}` literal; POI-`alt` region-only) are behaviorally
  load-bearing, not vacuous.
- `[DOC]` Prior stale "RED today" / `(RED)` comments → **CLOSED** (comment-analyzer confirmed gone).
- `[RULE]` 13 rules / 31 instances, **0 violations**; No-Silent-Fallbacks / No-half-wired /
  OTEL-cosmetic-exempt still PASS.
- `[EDGE]`/`[SILENT]`/`[TYPE]`/`[SEC]`/`[SIMPLE]` — subagents disabled via settings (pre-filled
  Skipped); domains assessed by me against the test-only diff: no boundary/error/type/security/
  complexity surface introduced by adding test assertions.

**Sole remaining finding — non-blocking [DOC], LOW:** the region-only POI `alt`
(`regionDisplayName(data)` at `LocationPanel.tsx:140`) lacks an inline comment marking the
one-arg call deliberate. **Not a blocker** — the behavior is now *mechanically* protected by the
new "keeps the POI image alt region-only" test (a "fix" that adds the subregion fails the suite),
so the invariant can't silently regress. Captured as a delivery finding for an optional one-line
source comment.

**Data flow traced:** `current_location` (PARTY_STATUS) → GameBoard `player_id` lookup →
LocationWidget → LocationPanel `regionDisplayName(data, subregion)` → header breadcrumb. Safe,
display-only, no sink. **Pattern:** composition guarded on present/non-blank/distinct before
appending the locked separator — `LocationPanel.tsx:222-225`. **Error handling:** `(subregion ??
"").trim()` + `characters?.find(...)?.` degrade cleanly to region-only on null/undefined/empty/
no-match.

**Handoff:** To SM (The Mad Hatter) for finish-story.

## Delivery Findings

No upstream findings at setup time.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): Story `repos` is `ui,server` but the work is **UI-only**
  (Architect-confirmed). The server tree is untouched — expect **no server PR**. Affects sprint
  finish bookkeeping (`epic-85.yaml` repos for 85-2). *Found by TEA during test design.*
- **Question** (non-blocking): the breadcrumb separator is locked to ` — ` (EM DASH U+2014 with
  surrounding spaces) per the Architect contract; tests assert it literally. If a future design
  pass wants `›` or a different glyph, the constant + 3 assertions move together. Affects
  `sidequest-ui/src/components/LocationPanel.tsx` (the `regionDisplayName` composer Dev adds).
  *Found by TEA during test design.*

### Dev (implementation)
- No upstream findings during implementation. The TEA seam was exact; implementation matched it
  with no surprises (the composition point and GameBoard deps were already in place).

### Reviewer (code review)
- **Improvement** (non-blocking): the region-only POI-image `alt` (`regionDisplayName(data)` at
  `sidequest-ui/src/components/LocationPanel.tsx:140`) is an intentional divergence from the
  breadcrumb header but is undocumented and untested — a one-line comment + a test asserting the
  `alt` stays region-only would lock the decision. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the breadcrumb region segment can itself contain the em-dash
  separator if the server supplies a `region_name` like `"Bridge — Outer Coyote Star"` (such
  values exist in fixtures), yielding a double-separator header. Pre-existing/cosmetic, not
  introduced here; affects `sidequest-ui/src/components/LocationPanel.tsx` (`regionDisplayName`)
  if a future pass wants to disambiguate. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the region-only POI `alt` (`regionDisplayName(data)` one-arg
  call at `sidequest-ui/src/components/LocationPanel.tsx:140`) is intentional but uncommented at
  the call site — a one-line comment would stop a future maintainer "fixing" it. Already
  mechanically protected by the "keeps the POI image alt region-only" test, so non-blocking.
  *Found by Reviewer during re-review (round 2).*

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Architect contract #3/#5 (server emit-gate + new OTEL span) retracted — 85-2 is UI-only**
  - Spec source: Architect contract for 85-2 (SendMessage, items #3 "stale-emit fix has a server
    half" and #5 "watcher span fires")
  - Spec text: "85-2 has both halves … widen the emit trigger … `location_description.emit { reason:
    intra_region_move … }` fires at the emit gate"
  - Implementation: No server test written. RED suite is client-only (breadcrumb composition +
    PARTY_STATUS-driven freshness). No emit-gate change, no new OTEL.
  - Rationale: Reading the actual gates (`websocket_session_handler.py:2015` room_graph /
    `:2057-2087` region-mode) + `_maybe_emit_location_description` sourcing (`map_emit.py:430-441`)
    proved the region payload is `current_region`-keyed; an intra-region re-emit is byte-identical
    (no-op). The finer subregion lives only in per-PC `current_location` (PARTY_STATUS, every turn)
    → client composition. Architect re-reviewed the falsifier and replied `CONFIRM UI-only`,
    explicitly retracting #3/#5. Per CLAUDE.md, cosmetic UI composition needs no OTEL; the existing
    `narrator.region_patch_check` watcher already covers the dev-side "region didn't move when prose
    did" case.
  - Severity: minor
  - Forward impact: none for 85-2. Guardrail for Dev: the pre-existing region-CROSSING re-emit
    (`:2079`) and room-change re-emit (`:2015`) must stay intact — the breadcrumb's region segment
    still depends on `LOCATION_DESCRIPTION` firing on a real region change (server untouched, so no
    action; noted so a later refactor doesn't silently break it).

### Dev (implementation)
- No deviations from spec. Implemented the TEA seam exactly: client-side breadcrumb composition,
  no server/payload/`useRunningHeader` change.

### Reviewer (audit)
- **TEA deviation — "Architect contract #3/#5 retracted, 85-2 is UI-only"** → ✓ ACCEPTED by
  Reviewer: sound and independently confirmed. The rule-checker verified the OTEL exemption holds
  (cosmetic UI composition) and that the region payload is `current_region`-keyed, so an
  intra-region re-emit would be a no-op — the client-composition fix is the correct and complete
  one. The guardrail (pre-existing region-crossing/room-change re-emits must stay intact) is noted;
  server untouched, so nothing regressed.
- **Dev deviation — "No deviations from spec"** → ✓ ACCEPTED by Reviewer: confirmed against the
  diff — implementation matches the TEA seam exactly (client-side only; `useRunningHeader`, the
  payload type, and all server code untouched).
- No **undocumented** deviations found: the implementation does not diverge from the recorded
  AC-1 contract. (The rejection is on test-suite hardening, not a spec deviation.)
- **Round 2 (re-review):** the rework was test-only and added no new deviations. The R1 stamps
  above stand; nothing new to ACCEPT or FLAG. Verdict APPROVED.