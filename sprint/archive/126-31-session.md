---
story_id: "126-31"
jira_key: ""
epic: "126"
workflow: "tdd"
---
# Story 126-31: [FATE/UX] Render the opponent stress/consequence track + a taken-out win-meter in FateConflictSurface from the now-projected FATE_STATE.conflict data

## Story Details
- **ID:** 126-31
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none
- **Priority:** p2
- **Points:** 2
- **Repos:** ui

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-20T10:33:41Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-20T10:04:14Z | 2026-06-20T10:04:14Z | - |
| red | 2026-06-20T10:04:14Z | 2026-06-20T10:21:05Z | 16m 51s |
| green | 2026-06-20T10:21:05Z | 2026-06-20T10:27:44Z | 6m 39s |
| review | 2026-06-20T10:27:44Z | 2026-06-20T10:33:41Z | 5m 57s |
| finish | 2026-06-20T10:33:41Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): `tsc -p tsconfig.app.json` (the real `tsc -b` build gate) reports a PRE-EXISTING type error 126-31 did NOT introduce — `src/components/GameBoard/__tests__/GameBoard-fate-inventory-tab.test.tsx:203` (TS2769 "No overload matches this call"), a different file. After Dev clears the 10 AC1 errors in the new test file, this 1 residual error will remain in the typecheck output. Affects `sidequest-ui/src/components/GameBoard/__tests__/GameBoard-fate-inventory-tab.test.tsx` (needs its own fix; out of 126-31 scope). *Found by TEA during test design.*
- **Improvement** (non-blocking): the win-meter math (used-absorption / total-capacity → taken-out) is already encoded server-side in `sidequest-server/sidequest/game/ruleset/fate_projection.py::conflict_opponent_progress`; the UI computation in `FateConflictSurface` should reproduce that exact formula (Σ checked-stress.value + Σ filled-consequence.value over Σ all .value), not invent a parallel one. Affects `sidequest-ui/src/components/FateConflictSurface.tsx` (GREEN-phase reference). *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): the full UI vitest suite has ONE pre-existing failure unrelated to 126-31 — `src/__tests__/no-google-fonts.test.ts` ("the dice tray loads label faces from R2, not /public/fonts"), which asserts on `InlineDiceTray.tsx` (untouched by this story). It matches the known dice-font finding from the 150-3 closeout (#430 same-origin font proxy → 403). 2510/2511 tests pass; this is the only red and it is baseline. Affects `sidequest-ui/src/dice/InlineDiceTray.tsx` (separate fix). *Found by Dev during implementation.*
- **Gap** (non-blocking): `tsc -p tsconfig.app.json` still reports the one pre-existing TS2769 in `GameBoard-fate-inventory-tab.test.tsx:203` that TEA flagged; all 10 of this story's AC1 type errors are cleared. Affects `sidequest-ui/src/components/GameBoard/__tests__/GameBoard-fate-inventory-tab.test.tsx` (separate fix). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): fill-bar percent math has no NaN guard — `Math.max(0, Math.min(100, NaN))` is `NaN`, so a contract-breaking payload (non-numeric `value`) would render `width: "NaN%"` (invisible bar) with no loud failure. This is a CODEBASE-WIDE pattern, NOT introduced by 126-31: `ConfrontationOverlay`'s `EdgeBar` (line 373) and the existing self-track have the identical un-guarded form, and `FateStressBox.value`/`FateConsequenceEntry.value` are server-validated ints (pydantic v2), so the precondition can't occur with the real server. Best fixed once, as a shared `clampPct` helper across EdgeBar + FateConflictSurface. Affects `sidequest-ui/src/components/{ConfrontationOverlay,FateConflictSurface}.tsx` (shared NaN-safe clamp). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): consequence list `key={c.level}` collides when a Fate sheet has two slots of the same level (e.g. an extra *mild* from high Physique). Latent in BOTH the existing self-track (line 442) and the new opponent-track (line 531) — a React key-uniqueness warning + possible reconciliation glitch on mid-exchange updates. Consider `key={`${c.level}-${i}`}` in both. Affects `sidequest-ui/src/components/FateConflictSurface.tsx` (both consequence maps). *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **AC1 (type parity) is gated at `tsc`, not at the vitest runner**
  - Spec source: context-story-126-31.md, AC-1
  - Spec text: "The UI FateConflictParticipant type models opponent stress + consequences (reusing FateStressBox / FateConsequenceEntry); existing payloads/fixtures stay valid."
  - Implementation: opponent fixtures are typed `FateConflictParticipant` with `stress`/`consequences` and NO cast, so `tsc -p tsconfig.app.json` (the `tsc -b` build gate) fails TS2353/TS2339 (10 errors) until the type is extended. Two runtime parity asserts confirm field presence and stay GREEN under vitest (esbuild strips types).
  - Rationale: vitest cannot fail on a missing type field; the type contract's real gate is tsc/build. Mirrors the established repo convention in `src/types/__tests__/fate-protocol.test.ts`.
  - Severity: minor
  - Forward impact: Dev's GREEN must pass `npm run build` / `tsc -b`, not only `vitest run`; the 2 AC1 runtime tests are GREEN during RED by design.
- **Test design fixes the testid + win-meter presentation contract Dev implements to**
  - Spec source: context-story-126-31.md, AC-2/AC-3
  - Spec text: "render a taken-out win-meter ... mirror ConfrontationOverlay's EdgeBar"
  - Implementation: RED pins concrete selectors/attrs — `fate-conflict-opponent-track` (data-opponent), `fate-conflict-opponent-stress-box` (data-checked), `fate-conflict-opponent-consequence` (data-filled), `fate-conflict-win-meter` (data-opponent; data-at-threshold "true" when used≥capacity; visible "used/capacity" text), `fate-conflict-win-meter-fill` (inline width "{pct}%", pct = used/total*100).
  - Rationale: RED must assert concrete selectors; chose names mirroring the existing self-track testids and EdgeBar's `metric-bar`/`data-at-threshold`/`current/threshold` conventions.
  - Severity: minor
  - Forward impact: Dev implements to these exact testids/attrs; changing a selector means updating the test.

### Dev (implementation)
- No deviations from spec. Implemented exactly to the TEA win-meter + testid contract: extended `FateConflictParticipant` with optional `stress`/`consequences`, added `opponentProgress` (reproducing `fate_projection.conflict_opponent_progress`), rendered the opponent track + win-meter mirroring `EdgeBar`. Styling uses the `--destructive` token (the existing opponent-side color, see the participant badge) — presentation only, no contract change.

### Reviewer (audit)
- TEA deviation **"AC1 gated at `tsc`, not the vitest runner"** → ✓ ACCEPTED by Reviewer: correct — vitest (esbuild) cannot fail on a missing type field; the typed-fixture-no-cast pattern + `tsc -p tsconfig.app.json` is the right gate, and matches `fate-protocol.test.ts`. Verified the 10 AC1 errors existed in RED and are cleared in GREEN.
- TEA deviation **"test design fixes the testid + win-meter presentation contract"** → ✓ ACCEPTED by Reviewer: the chosen selectors mirror the existing self-track testids + EdgeBar conventions (`data-at-threshold`, fill width, `used/capacity` text); Dev implemented to them faithfully (13/13).
- Dev **"no deviations from spec"** → ✓ ACCEPTED by Reviewer: confirmed against the diff — `opponentProgress` reproduces `conflict_opponent_progress` (Σ checked-stress + Σ filled-consequence over Σ all), renders only opponent-side capacity>0, reads `?? {}`/`?? []`. The `--destructive` color is the established opponent-side token (participant badge line 359). No undocumented deviations found.

## TEA Assessment

**Tests Required:** Yes
**Reason:** UI render story — observable behavior (opponent track + win-meter) plus a typed wire contract; both need coverage.

**Test Files:**
- `sidequest-ui/src/components/__tests__/FateConflictSurface.opponent-track.test.tsx` — 13 tests across AC1–AC4 + the ADR-143 win-signal invariant. Renders the REAL `FateConflictSurface` (imported, not mocked) against realistic FATE_STATE → this IS the wiring/integration test (the component is the production consumer of `conflict.participants[opponent].stress/consequences`).

**Tests Written:** 13 tests covering 4 ACs + 1 invariant.
**Status:** RED — verified two ways:
- **vitest** (`npx vitest run …opponent-track.test.tsx`): **7 failing / 6 passing**. The 7 failures are every positive render assertion (opponent track section, stress boxes, consequences, win-meter fill, at-threshold flag, multi-opponent) — the surface draws nothing for the Other today (FateConflictSurface.tsx ~L377-382 explicitly punted it). The 6 "passing" are intentional **negative/back-compat guards** (sheetless → no meter; player-side → no meter; legacy omitted-fields → no crash) + the 2 AC1 runtime parity asserts — all designed to stay GREEN and catch a wrong implementation (over-rendering / a `||` crash / side-filter miss).
- **tsc** (`npx tsc -p tsconfig.app.json --noEmit`): **10 errors in the test file** — `'stress'/'consequences' does not exist on type 'FateConflictParticipant'` (TS2353 ×4, TS2339 ×6). This is AC1's RED, enforced at the build gate.

> NOTE on RED verification: a naive `npx tsc --noEmit` reports a FALSE "clean" — the root `tsconfig.json` is solution-style (only `references`, no `include`), so non-build `tsc` compiles nothing. The real gate is `tsc -b` (what `npm run build` runs) / `tsc -p tsconfig.app.json`. Dev/Reviewer: use the latter to see AC1.

### Rule Coverage (lang-review: typescript.md)

| Rule | Test(s) | Status |
|------|---------|--------|
| #1 type-safety escapes (no `as any`) | fixtures typed `FateConflictParticipant` with NO cast — forces a real type extension, not an `as any` read in the component | RED (tsc) |
| #2 generic/interface (no `Record<string,any>`) | AC1 parity test uses `Record<string, FateStressBox[]>` (typed) | green-guard |
| #4 null/undefined (`??` not `||`) | "survives a legacy participant with the track fields omitted (?? not ||)" | green-guard |
| #6 React/JSX list keys | multi-opponent + per-box rendering exercise list output; React keys are not directly assertable in jsdom (noted, not faked) | indirect |
| #8 test quality (no vacuous asserts) | Phase-C self-check below | pass |

**Rules checked:** 5 of the applicable typescript.md checks have explicit coverage; #6 is covered indirectly (jsdom can't read React keys — honestly noted, not asserted vacuously).
**Self-check (Phase C):** 0 vacuous tests. The 2 AC1 runtime asserts check real values (`.toBe(true)/.toBe(2)/.toBe("Winded")`) and are tsc-gated, not vacuous; the negative guards assert `undefined`/`not.toBeInTheDocument` against concrete over-render failure modes.

### Win-meter contract (for Dev)
- capacity = Σ(all stress box `.value`, every track) + Σ(all consequence `.value`); used = Σ(checked stress `.value`) + Σ(filled consequence `.value`); pct = `used/capacity*100`.
- Render the meter ONLY for `side === "opponent"` participants with capacity > 0 (sheetless and player-side draw nothing). `data-at-threshold="true"` when `used >= capacity`.
- Read `p.stress ?? {}` / `p.consequences ?? []` (back-compat). Reproduce `fate_projection.py::conflict_opponent_progress`, don't re-derive.
- ADR-143 invariant: the meter is the opponent's stress+consequence fill toward taken-out — never the native `opponent_metric.tension` dial.

**Handoff:** To Dev (Inigo Montoya) for GREEN implementation.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-ui/src/types/payloads.ts` — extended `FateConflictParticipant` with optional `stress?: Record<string, FateStressBox[]>` + `consequences?: FateConsequenceEntry[]` (mirrors the server model; reuses the PC-sheet wire shapes; back-compat optional like `committed?`). Clears AC1.
- `sidequest-ui/src/components/FateConflictSurface.tsx` — added the `opponentProgress` helper (used-absorption / total-capacity, reproducing `fate_projection.conflict_opponent_progress`) and an opponent-track + win-meter render block per opponent-side participant. The meter mirrors `ConfrontationOverlay`'s `EdgeBar` (fill % via inline width, `data-at-threshold` flash, legible `used/capacity` numerator). Updated the now-stale "server follow-up" punt comment.

**Implementation notes:**
- Renders ONLY for `side === "opponent"` participants with capacity > 0 — `opponentProgress` returns null for player-side and sheetless (capacity 0) actors, so they draw nothing (the honest empty state). Reads `stress ?? {}` / `consequences ?? []` for pre-projection back-compat (`??`, never `||`).
- ADR-143 invariant honored: the win signal is the opponent's stress+consequence fill toward taken-out, read from the projected track — never the native `opponent_metric.tension` dial.
- Wiring: `FateConflictSurface` is consumed in production by `App.tsx` + `GameBoard/GameBoard.tsx`; this is an additive render block on an already-wired component (the test renders the real component, not a mock).

**Tests:** Story file 13/13 passing (GREEN). Full UI suite 2510/2511 passing — the single red (`no-google-fonts.test.ts`) is pre-existing and unrelated (see Delivery Findings). Typecheck: all 10 AC1 errors cleared; only the pre-existing `GameBoard-fate-inventory-tab.test.tsx:203` TS2769 remains.
**Branch:** feat/126-31-fate-opponent-track-winmeter (pushed, commit e63b8ee)

**Handoff:** To Reviewer (Westley) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (1 style note) | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — covered by Reviewer's own edge analysis |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 (LOW) | confirmed 1 (LOW), dismissed 0, deferred 0 |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — covered by Reviewer's own test review |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — covered by Reviewer's own doc review |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — covered by Reviewer's own type review |
| 7 | reviewer-security | Yes | clean | 0 | confirmed 0, dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — covered by Reviewer's own simplicity review |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — covered by Reviewer's own Rule Compliance section |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents` settings)
**Total findings:** 1 confirmed (LOW, [SILENT]) + 3 Reviewer-originated LOW observations; 0 dismissed, 0 deferred. No High/Critical.

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** server `fate_projection._project_conflict_participant` reads the NPC `core.fate_sheet` → projects `FateConflictParticipant.stress/consequences` onto the wire → UI mirror → `opponentProgress(o)` (sums absorption) → win-meter `width`/`data-at-threshold` + the stress-box/consequence render. Safe because: every server string (`o.name`, `c.text`, `c.level`, `track`) is rendered as escaped JSX text/attribute (no `dangerouslySetInnerHTML`), and the only numeric path into inline `style.width` is `pct`, clamped `0..100` after a `capacity > 0` guard.

**Pattern observed:** the opponent section faithfully mirrors two existing patterns — `ConfrontationOverlay`'s `EdgeBar` (FateConflictSurface.tsx:456-489 ↔ ConfrontationOverlay.tsx:365-407: fill width %, `data-at-threshold`, `used/capacity` ↔ `current/threshold`) and the sibling self-track block (FateConflictSurface.tsx:411-451). `opponentProgress` (153-183) reproduces `fate_projection.conflict_opponent_progress` exactly. Good consistency, no reinvention.

**Error handling:** `?? {}`/`?? []` (nullish, not `||`) for pre-projection back-compat; `if (capacity <= 0) return null` guards both the divide and the sheetless/player-side no-draw (FateConflictSurface.tsx:180). The honest empty state (no bar) is intentional per the #966 seated-without-a-sheet case — confirmed not a swallowed error.

### Observations (tagged by source)

- `[SILENT] [LOW]` NaN not guarded in the fill clamp — `Math.max(0, Math.min(100, NaN))` → `width: "NaN%"` if a non-numeric `value` ever arrived (FateConflictSurface.tsx:181). **Confirmed LOW, non-blocking.** Requires a contract-breaking payload (`value` is a server-validated pydantic int), and `EdgeBar` (ConfrontationOverlay.tsx:373) + the self-track share the identical un-guarded pattern — so this is codebase-wide, not a 126-31 regression. Captured as a non-blocking Delivery Finding (shared clamp helper).
- `[SEC] [VERIFIED]` No injection/leak — security subagent CLEAN. Evidence: no `dangerouslySetInnerHTML` in the diff; `o.name`/`c.text` are escaped JSX; `data-opponent`/`aria-label`/`style.width` are React-escaped attribute/number paths; only player-visible fields (name/side/stress/consequence) are surfaced, server-controlled by projection. Complies with lang-review #6/#10 and CLAUDE.md No-Silent-Fallbacks.
- `[EDGE] [LOW]` (edge-hunter disabled — my analysis) `key={c.level}` on opponent consequences collides if a sheet has duplicate-level slots (extra *mild* from high Physique; server `_project_consequences` projects `sheet.consequences` 1:1). Latent in the self-track too (line 442). Non-blocking Delivery Finding filed.
- `[EDGE] [LOW]` (my analysis) `key={o.name}`/`data-opponent={o.name}` ambiguous for two same-named opponents — mirrors the pre-existing Participants list `key={p.name}` (line 349). Non-blocking.
- `[TEST] [VERIFIED]` (test-analyzer disabled — my review) 13 tests, no vacuous assertions: the 6 RED-green tests are real negative/back-compat guards (sheetless/player-side/legacy → `undefined`/`not.toBeInTheDocument`), the AC1 runtime asserts check concrete values. Gap: no test for duplicate consequence levels or same-name opponents (the two `[EDGE]` items) — non-blocking, latent-pattern territory.
- `[TYPE] [VERIFIED]` (type-design disabled — my review) the type extension uses `Record<string, FateStressBox[]>` + `FateConsequenceEntry[]` (not `Record<string, any>`), optional/additive like `committed?`, no `as`/`as any` introduced (payloads.ts:1228-1234). Mirrors the server model. Complies with lang-review #1/#2.
- `[DOC] [VERIFIED]` (comment-analyzer disabled — my review) the now-false "server follow-up — not faked client-side" punt comment was correctly updated in place (FateConflictSurface.tsx:406-410); the new helper + section carry accurate ADR-143/projection docs. No stale comments left.
- `[SIMPLE] [VERIFIED]` (simplifier disabled — my review) `opponentProgress` is a minimal pure function; the render mirrors the self-track without added abstraction. No dead code, no over-engineering.
- `[RULE]` (rule-checker disabled — my review) see Rule Compliance below.
- `[VERIFIED]` Wiring — `FateConflictSurface` is consumed by `App.tsx` + `GameBoard/GameBoard.tsx` (production); the opponent section is additive inside the already-mounted surface, and the tests render the REAL component.

### Rule Compliance (typescript.md lang-review)

- **#1 type-safety escapes** — COMPLIANT. No `as any`/`@ts-ignore`/non-null-assert in the diff; the type extension forced a real model change, not a cast.
- **#2 generic/interface** — COMPLIANT. `Record<string, FateStressBox[]>` (typed), not `Record<string, any>`.
- **#4 null/undefined** — COMPLIANT. `stress ?? {}`, `consequences ?? []` (nullish, not `||`); no falsy-`0`/`""` hazard (both fields are object/array-typed).
- **#6 React/JSX** — MOSTLY COMPLIANT. No `dangerouslySetInnerHTML`; `motion-reduce` honored; `prefers-reduced-motion` respected. Minor: `key={c.level}` / `key={o.name}` collision risk on duplicates (the two `[EDGE] LOW` items) — mirrors existing code, filed non-blocking.
- **#8 test quality** — COMPLIANT. No `as any` in tests, no vacuous assertions (verified above).
- **#10 input validation** — N/A here (no NEW deserialization boundary; the new fields ride the existing FateStatePayload pipeline; security subagent confirmed no `as T` introduced).

### Devil's Advocate

Assume this is broken. The most dangerous surface is the win-meter math feeding an inline style, because a wrong number there is a silent visual lie — exactly the "Claude wings it" failure the OTEL doctrine warns about, except here it's the client. What if `used > capacity`? The clamp caps the bar at 100% but the *text* would read e.g. "7/5" — a contradiction a mechanics-first player (Sebastien/Jade) would immediately distrust; however, `used` is a subset-sum of `capacity` by construction (checked ⊆ all, filled ⊆ all), so with valid data this is impossible, and the only way to break it is a server that violates its own projection contract. What about NaN? Confirmed real (the `[SILENT]` finding) but only under the same contract-breaking precondition, and identical to EdgeBar — so rejecting here would single out new code for a codebase-wide pattern. What would a confused user misread? An opponent with open consequence slots renders "moderate (4) — open"; a player might think the Other already *has* a moderate consequence. But this exactly mirrors the self-track's wording the table already reads, so the convention is established, not novel. What about a malicious NPC name like `</section>` or an emoji bomb? React escapes it to text — the security subagent verified no breakout. What about many opponents (ADR-116 allows several)? Each maps to its own keyed section; the only risk is duplicate names (filed LOW). What if `conflict.participants` is huge? `opponentProgress` is O(boxes) per opponent, called once per render — negligible. Could the meter fire its pulse forever and burn CPU? `animate-pulse` is CSS, GPU-cheap, and gated behind `motion-reduce`. Net: the failure modes are all either impossible with contract-valid data or identical to long-standing sibling code. Nothing rises to High.

### Challenge: VERIFIEDs vs subagent findings

My initial read claimed "no NaN/Infinity into the width style." The silent-failure subagent contradicted this. **Challenged:** I re-examined FateConflictSurface.tsx:181 — my claim holds ONLY for contract-valid (numeric) `value` fields, where `used`/`capacity` are finite and `pct` clamps cleanly; the subagent is correct that a *non-numeric* `value` yields `NaN` past the clamp. I downgrade my VERIFIED to the `[SILENT] LOW` finding above (with the EdgeBar-precedent rationale). No other VERIFIED is contradicted by a subagent. Tenant isolation: N/A — this is a single-player-perspective game render with no tenancy/auth boundary in the diff.

**Handoff:** To SM for finish-story.