---
story_id: "98-3"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 98-3: U1 UI — two-scale MapWidget (cartography graph default + orrery drill-down), retire orbital:bool whole-Map toggle

## Story Details
- **ID:** 98-3
- **Jira Key:** (none — Jira integration disabled)
- **Workflow:** tdd
- **Stack Parent:** none (single story)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-09T23:17:25Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-09T22:33:02Z | 2026-06-09T22:35:11Z | 2m 9s |
| red | 2026-06-09T22:35:11Z | 2026-06-09T22:44:49Z | 9m 38s |
| green | 2026-06-09T22:44:49Z | 2026-06-09T22:53:02Z | 8m 13s |
| review | 2026-06-09T22:53:02Z | 2026-06-09T23:02:18Z | 9m 16s |
| red | 2026-06-09T23:02:18Z | 2026-06-09T23:07:31Z | 5m 13s |
| green | 2026-06-09T23:07:31Z | 2026-06-09T23:13:36Z | 6m 5s |
| review | 2026-06-09T23:13:36Z | 2026-06-09T23:17:25Z | 3m 49s |
| finish | 2026-06-09T23:17:25Z | - | - |

## Story Context

**Type:** enhancement
**Points:** 5
**Priority:** p3
**Epic:** 98 (ADR-141 Two-Scale Spatial Model — Galactic Graph + Per-System Orrery)
**Repository:** sidequest-ui
**Branch Strategy:** gitflow (feat/98-3-two-scale-mapwidget)
**Branch Created:** feat/98-3-two-scale-mapwidget (from develop)

### Acceptance Criteria
Authoritative ACs are epic spec §4 Story U1 (`docs/superpowers/specs/2026-06-08-two-scale-spatial-model-epic-design.md`):
1. (AC1) Cluster world (perseus_cloud) default Map = cartography nodes-and-edges graph rendered via the shared d3-dag component from 100-10 — NOT the orrery, NOT the retired `cartographyLayout.ts` SVG.
2. (AC2) Selecting/entering a node drills into that system's orrery; a back affordance returns to the galactic graph.
3. (AC3) The `orbital: boolean` whole-Map toggle is replaced by a scale/drill state (campaign ↔ local). Do not regress #748's verified "orrery renders" behavior — only re-scope *when* it renders.
4. (AC4) Single-system world (`coyote_star`) shows orrery-as-Map (two scales collapse to one — derivable from one graph node).
5. (AC5) A node with no authored orrery shows a legible "no local chart" state on drill-down, not a crash or blank.

### Dependency Context
- **Depends On:** 100-10 (epic 100, Phase 3 shared d3-dag Map) — SATISFIED
- **Owned By:** 98-3 (view-model: scale/drill UX at MapWidget layer, retiring orbital:bool)
- **Related to:** 100-10 owns the layout engine (d3-dag); 98-3 builds on top

### Specification Notes
- Ownership division per story description: 100-10 owns layout engine (d3-dag); 98-3 owns the view-model (scale/drill UX at MapWidget layer, retiring orbital:bool)
- Cross-epic sequencing: must build on shared d3-dag component from 100-10, NOT against the doomed SVG cartographyLayout.ts
- Spec location: docs/superpowers/specs/2026-06-08-two-scale-spatial-model-epic-design.md
- Architect spec reconciliation note: epic-100 spec lines 51-52 ('overlay feed frozen') contradicts this story — the U1 render-target note in the epic spec governs

## Sm Assessment

**Setup status:** Complete. Session file created, story context validated at `sprint/context/context-story-98-3.md`, feature branch `feat/98-3-two-scale-mapwidget` created in sidequest-ui, epic-98 YAML updated to in_progress.

**Jira:** Skipped — Jira integration disabled for this project; no key in sprint YAML.

**Dependency gate:** 100-10 (shared d3-dag Map, epic 100) is SATISFIED — epic 100 archived complete (orchestrator commit 00fc6042). 98-3 builds the two-scale drill view-model on top of the shared d3-dag layout component, not the retired SVG cartographyLayout.ts.

**Routing:** Workflow `tdd` (phased). Next phase `red`, owner TEA (Amos Burton). TEA should note the open spec-reconciliation flag — epic-100 spec lines 51-52 ("overlay feed frozen") contradicts this story; the Architect's reconciliation note in the story context governs.

## TEA Assessment

**Tests Required:** Yes
**Reason:** 5-point enhancement with five spec ACs (epic spec §4 Story U1); tdd workflow.

**Test Files:**
- `sidequest-ui/src/components/GameBoard/widgets/__tests__/MapWidget.twoScale.test.tsx` — RED-phase contract for the two-scale view-model (14 tests; commit `98b46c7`)

**Tests Written:** 14 tests covering all 5 U1 ACs
**Status:** RED (10 failing define new behavior; 4 pass deliberately as pinning guards — AC4 orrery-as-Map collapse and the non-orbital capability gate match current #748 behavior and must survive the refactor)

**AC → test mapping:**
- AC1 (cluster default = d3-dag cartography graph, not orrery): 4 tests, incl. the **wiring test** required by the epic verification spine — `map-region-graph` is emitted only by the shared `CartographyMap` (100-10), so its presence proves the d3-dag path mounts as default Map for a cluster world.
- AC2 (drill-down + back affordance): 4 tests — occupied-node click sends `{kind:"view_map", scope:"system_root"}` (98-2 resolves by party's current region), back affordance (`map-drill-back`) exists in loading/chart/error states, non-occupied nodes do NOT drill (see Deviations).
- AC3 (orbital:bool retired as whole-Map router): stale-chart-stays-at-campaign-scale test + AC1 negatives. The `orbital` prop survives as a *capability* signal only.
- AC4 (single-system orrery-as-Map): 3 tests (1-node cartography, empty-regions cartography, no back affordance). Plus the pre-existing orbital tests in `MapWidget.test.tsx` (mapData:null + orbital) which pin #748 and must keep passing.
- AC5 (unauthored system → legible no-local-chart): 2 tests via the new prop seam `lastOrbitalError?: { code: string; message: string } | null` (testid `map-panel-no-local-chart`; spinner must clear; back affordance retained).

**Contract testids defined for Dev:** `map-drill-back`, `map-panel-no-local-chart` (existing: `map-region-graph`, `map-region-node-<id>`, `map-panel-orbital`, `map-panel-orbital-loading`).

### Rule Coverage

| Rule (lang-review/typescript.md) | Test(s) | Status |
|------|---------|--------|
| #4 null/undefined handling | null mapData (pre-existing), null chart, empty `regions:{}` fixture, null error | failing/pinned |
| #6 React/JSX state + hook deps | AC2 drill/rerender/back transitions exercise the scale-state machine + `useOrbitalChart` enable gating | failing |
| #8 test quality (no `as any`, meaningful asserts) | self-check below | done |
| #1/#2/#10 (type escapes, generics, input validation) | implementation-time checks — Dev must type `lastOrbitalError` in `MapWidgetProps` (the RED test passes it untyped by design); review gate enforces | n/a (Dev) |

**Rules checked:** 3 of 13 lang-review rules are behaviorally testable pre-implementation and have coverage; the rest gate Dev's diff at review.
**Self-check:** 0 vacuous tests — every test asserts DOM presence/absence, attribute values, or spy call counts; the AC5 legibility test asserts non-empty visible text, not mere existence.

### Test Run (testing-runner, RUN_ID 98-3-tea-red, 2026-06-09)

- ui suite: **1996 passed / 11 failed** (2007 total, 217 files, 12.8s)
- 10 of the 11 failures are the new `MapWidget.twoScale` RED tests (all element-not-found / spy-count failures against the not-yet-built contract — correct RED).
- The 11th is the pre-existing flaky `lobby-start-ws-open.test.tsx` timeout, already tracked as backlog story 97-8 (unrelated to 98-3).

**Handoff:** To Dev (Naomi Nagata) for implementation. Dev notes: build the scale/drill state in `MapWidget.tsx` on top of `CartographyMap`'s `activeNodeId`/`onNodeSelect` (do NOT fork the layout); `MapOverlay` may need an `onNodeSelect` pass-through; `lastOrbitalError` must be threaded App → GameBoard → MapWidget the same way `lastOrbitalChart` is — and see the server-side Gap finding below before wiring AC5.

## TEA Assessment (round-trip 1 — rework red)

**Tests Required:** Yes
**Reason:** Reviewer REJECTED with 1 HIGH + 2 MEDIUM testable findings; this round-trip adds the failing tests that pin the required fixes.

**Test changes (commit `007a932`):**
- `MapWidget.twoScale.test.tsx` — NEW RED: "error supersedes a stale cached chart" (review HIGH — at the widget gate a present `lastOrbitalError` must win over any chart, killing the wrong-system-orrery display); NEW RED: "returns to campaign scale when the party's current region changes mid-drill" (review MEDIUM — drill state resets on `current_location` change, pins `map-region-node-forma` as current). Strengthened AC5 assertion to `toContain(error.message)` (review LOW). Error fixtures now typed via `import type { OrbitalIntentError }` through a shared `errorFixture()` helper (review LOW).
- `GameBoard-map-orbital-error.test.tsx` — NEW wiring pin (review MEDIUM): renders real GameBoard, opens the Map tab, drills the occupied node, delivers `lastOrbitalError` via rerender, asserts the no-local-chart panel renders the message through the production prop chain. PASSES now (the chain exists) — it is a regression guard, per the CLAUDE.md wiring-test mandate.

**Status:** RED — testing-runner (RUN_ID `98-3-tea-red-rt1`): 2007 passed / 3 failed; the 2 new RED tests + the pre-existing 97-8 flake. Wiring pin green.

**Self-check:** 0 vacuous tests added; both RED tests assert testid presence/absence AND message content/current-node attributes.

**Handoff:** To Dev (Naomi Nagata). Fix direction per Reviewer: (1) flip the widget error gate to error-wins (`lastOrbitalError` before `chart`) AND clear `lastOrbitalChart` in App's `orbital_unavailable` branch (symmetry); (2) reset `drilledIn` when the current region id changes (Reviewer recommends reset-to-campaign over refetch); (3) fix the stale `worldOrbital` JSDoc at `GameBoard.tsx:226` (review LOW, doc-only).

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-ui/src/components/GameBoard/widgets/MapWidget.tsx` — two-scale view-model: `drilledIn` state, cluster detection by cartography node count (>1 region = cluster, ADR-141 "derivable, no new flag"), campaign-scale branch (MapOverlay + occupied-node drill gate), local-scale branch (back affordance `map-drill-back` in all sub-states; `map-panel-no-local-chart` error state; orrery panel), single-system orrery-as-Map branch preserved verbatim (#748)
- `sidequest-ui/src/components/MapOverlay.tsx` — optional `onNodeSelect` pass-through to the shared `CartographyMap` (100-10 component used as-is; layout not forked)
- `sidequest-ui/src/types/orbital-intent.ts` — `OrbitalIntentError { code, message }` wire-adjacent type
- `sidequest-ui/src/components/GameBoard/GameBoard.tsx` — `lastOrbitalError` prop threaded to MapWidget; added to the widget memo dep list
- `sidequest-ui/src/App.tsx` — `lastOrbitalError` state; ERROR handler branch for `code === "orbital_unavailable"` (chart-panel concern, not a narrative banner); cleared when a fresh ORBITAL_CHART supersedes it; passed to GameBoard

**AC coverage:**
- AC1: cluster default = d3-dag campaign graph via MapOverlay→CartographyMap — DONE
- AC2: occupied-node drill-in (view_map system_root via the existing useOrbitalChart enable gate) + `map-drill-back` return — DONE
- AC3: `orbital` reduced to capability signal; whole-Map routing removed; #748 single-system behavior preserved (pre-existing MapWidget.test.tsx orbital tests still green) — DONE
- AC4: ≤1 region node (or no cartography) → orrery-as-Map, no back affordance — DONE
- AC5: `lastOrbitalError` + no-local-chart panel, spinner cleared, back retained — DONE in UI; live end-to-end requires the server handler gap fix (see Delivery Findings)

**Tests:** 25/25 MapWidget tests passing (14 twoScale + 11 pre-existing) — GREEN. Full ui suite 2006/2007; the 1 failure is the pre-existing flaky `lobby-start-ws-open` timeout (story 97-8, unrelated). Typecheck clean; 1 pre-existing lint warning (App.tsx useCallback, untouched by this diff).
**Branch:** feat/98-3-two-scale-mapwidget (pushed, head `ab70f43`)

Note: a stray pre-existing untracked file (`src/styles/reference.css`, epic-100 leftover) was accidentally committed by `git add -A` and removed via amend + force-with-lease before review; it remains untracked on disk, not part of this branch.

**Handoff:** To next phase (verify/review).

## Dev Assessment (round-trip 1 — rework green)

**Implementation Complete:** Yes
**Files Changed (commit `8c50bc9`):**
- `sidequest-ui/src/components/GameBoard/widgets/MapWidget.tsx` — drill state re-keyed from boolean to `drilledRegionId: string | null`; `drilledIn` derived as `drilledRegionId === currentRegionId`, so a region change invalidates the drill by construction (review MEDIUM — no effect/reconciliation code needed). Error gate flipped to error-wins: `lastOrbitalError ?` replaces `lastOrbitalError && !chart` (review HIGH).
- `sidequest-ui/src/App.tsx` — `orbital_unavailable` branch now also `setLastOrbitalChart(null)` — a rejection invalidates any cached chart, symmetric with chart-clears-error (review HIGH, second half).
- `sidequest-ui/src/components/GameBoard/GameBoard.tsx` — stale `worldOrbital` JSDoc rewritten to capability-signal wording (review LOW).

**Review findings addressed:** HIGH (stale-chart-over-error) — both halves fixed; MEDIUM (drill survives region change) — fixed via region-keyed state; MEDIUM (wiring test) — covered by TEA's `GameBoard-map-orbital-error.test.tsx` (passing); 3× LOW — message-pinning assertion + typed fixture (TEA), JSDoc (this commit).

**Tests:** 28/28 map-related tests passing (16 twoScale + 1 GameBoard wiring + 11 pre-existing). Full ui suite 2009/2010 — sole failure is the pre-existing 97-8 flake. Typecheck clean; lint: only the pre-existing App.tsx exhaustive-deps warning.
**Branch:** feat/98-3-two-scale-mapwidget (pushed, head `8c50bc9`)

**Handoff:** Back to Reviewer (Chrisjen Avasarala) for re-review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (1 pre-existing flake noted, 1 pre-existing lint warning) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 6 | confirmed 4, dismissed 1, deferred 1 |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 | confirmed 1, dismissed 2 |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 1 | dismissed 1 (pre-existing, out of diff scope) |

**All received:** Yes (4 enabled returned; 5 disabled via settings)
**Total findings:** 5 confirmed, 4 dismissed (with rationale), 1 deferred

**Dismissals (with evidence):**
- [TEST] "re-drill after back doesn't re-fetch (fetchedForCycle stays true)" — WRONG: `useOrbitalChart.ts:80-84` resets `fetchedForCycle`/`lastFetchedEpoch` when `enabled` goes false, so back+re-drill fires a fresh view_map. Dismissed on cited evidence.
- [DOC] "MapOverlay onNodeSelect doc asserts unverified downstream behavior" — the claim is true: `CartographyMap.tsx:95-96` attaches `onClick`/pointer-cursor only when `onNodeSelect` is provided. Dismissed.
- [DOC] "test header 'RED-phase contract (TEA, 2026-06-09)' goes stale on merge" — dated provenance labels are this repo's established comment idiom (e.g. "wiring fix sq-playtest 2026-04-09"); the header names author+date, it does not claim the tests are currently red. Dismissed.
- [RULE] `skipLibCheck: true` in tsconfig.app.json — pre-existing build config, untouched by this diff. Dismissed as out of scope (worth a backlog chore).

**Deferred:**
- [TEST low] tests should `import type { OrbitalIntentError }` rather than duck-type the fixture — valid polish; folded into the rework batch below rather than tracked separately.

## Rule Compliance

Rubric: `.pennyfarthing/gates/lang-review/typescript.md` (13 checks) + CLAUDE.md principles. Exhaustive sweep by reviewer-rule-checker (17 rules × 58 instances), spot-verified by me:

- #1 type-safety escapes — PASS: zero new `as any`/`as unknown as`/`!`; the two `as unknown as` casts in App.tsx handlers are pre-existing context lines.
- #2 generics/interfaces — PASS: `OrbitalIntentError`, both prop additions, and `onNodeSelect` are concretely typed; no `Record<string,any>`/`Function`.
- #3 enums — N/A (none in diff). #7 async — N/A (none). #12 perf/bundle — PASS (direct imports, no barrels).
- #4 null/undefined — PASS: all new guards use `??` (`MapWidget.tsx:91,94,116`, `GameBoard.tsx:523`); the one `||` flagged (`MapOverlay.tsx:148 mapData.region || …`) is pre-existing untouched code.
- #5 modules — PASS: `import type` used at all three import sites of `OrbitalIntentError`.
- #6 React/JSX — PASS: `drilledIn` plain boolean state; new memo dep `lastOrbitalError` correctly added to GameBoard's widget memo (`GameBoard.tsx:610`); no `key={index}`; no `dangerouslySetInnerHTML`.
- #8 test quality — PASS mechanically (no `as any`, no dist/ imports, typed fixtures); but see confirmed findings F2/F4 for assertion strength gaps.
- #9 build config — untouched by diff (pre-existing `skipLibCheck` noted, dismissed).
- #10 input validation — PASS: `lastOrbitalError.message` rendered as React text (XSS-safe); no `JSON.parse as T`.
- #11 error handling — PASS for what exists; F1 below is a *state-precedence* logic flaw, not a catch-shape violation.
- #13 fix-regressions — PASS.
- CLAUDE.md No Silent Fallbacks / No Stubbing / Don't Reinvent / Verify Wiring — PASS: `CartographyMap` reused not forked (`MapOverlay.tsx:163-168`); `lastOrbitalError` chain has non-test producers and consumers (`App.tsx:1331→2553`, `GameBoard.tsx:310/523`, `MapWidget.tsx:162-169`). One wiring-TEST gap remains (F3).

## Reviewer Observations

1. [HIGH] [SILENT-class, found by lead + corroborated by TEST] Stale chart suppresses the AC5 error state at `MapWidget.tsx` (error branch gated `lastOrbitalError && !chart`) + `App.tsx` (orbital_unavailable branch sets the error but never clears `lastOrbitalChart`). Reachable today: drill yula (chart cached) → back → travel to an unauthored region (region movement is live) → drill → server rejects → widget renders the cached **yula** orrery for the wrong system; no-local-chart never shows. AC5 violated on a reachable path.
2. [MEDIUM] [TEST] Region change mid-drill is unspecified: `drilledIn` persists when `mapData.current_location` changes; no refetch fires (hook keyed on enable transitions only) → stale orrery for the new region. Policy needed (recommend: reset drill state when the current region id changes) + covering test.
3. [MEDIUM] [TEST] Wiring-test rule (CLAUDE.md "Every Test Suite Needs a Wiring Test"): the new `lastOrbitalError` prop chain has no test above the MapWidget unit level — nothing renders GameBoard and proves the prop reaches the widget. Static wiring verified by rule-checker, but the rule asks for a test. Rule-matching → cannot dismiss.
4. [LOW] [TEST] AC5 legibility assertion `expect(panel.textContent ?? "").not.toBe("")` is near-vacuous — it never pins that `lastOrbitalError.message` itself renders. Use `toContain(message)`.
5. [LOW] [DOC] Stale JSDoc at `GameBoard.tsx:226`: `worldOrbital` still documented as "Gates MapWidget's OrbitalChartView" — false after this diff (capability signal only).
6. [VERIFIED] Occupied-node drill gate — `MapWidget.tsx:136-139` compares clicked id to `currentRegionId` derived from `mapData.current_location` each render; complies with ADR-141 "drilled into from the node the party occupies" and the logged TEA deviation. Checked against No Silent Fallbacks: ignoring non-occupied clicks is specified behavior, not a fallback.
7. [VERIFIED] Back affordance present in all three local-scale sub-states — `MapWidget.tsx:152-160` renders `map-drill-back` before the error/loading/chart ternary, so the player is never trapped; test "no-local-chart state retains the back affordance" pins it.
8. [VERIFIED] #748 single-system non-regression — orrery-as-Map branch preserved (`MapWidget.tsx` `if (orbitalEnabled)` block unchanged in behavior); pre-existing `MapWidget.test.tsx` orbital tests pass unmodified. Complies with AC3's "do not regress" clause.
9. [VERIFIED] Data flow traced: server ERROR(`orbital_unavailable`) → `App.tsx:1331` setLastOrbitalError (early return, no narrative banner) → prop at `App.tsx:2553` → `GameBoard.tsx:523` → `MapWidget.tsx:162` text render. XSS-safe (React text node), no cast added, memo deps correct.
10. [VERIFIED] Shared-component reuse — `CartographyMap` consumed via existing `MapOverlay` call site with the `onNodeSelect` API 100-10 exposed for exactly this purpose; no fork, no layout duplication (`MapOverlay.tsx:163-168`).

### Devil's Advocate

Assume this code is broken. The drill state machine has three inputs that change independently — `drilledIn` (local state), `lastOrbitalChart`/`lastOrbitalError` (App state), and `mapData.current_location` (server state) — and nothing reconciles them. That's where the bodies are buried. First: the High above — the chart cache outlives its region. The team wired "chart supersedes error" but not "error supersedes chart," and the widget trusts whichever artifact happens to be non-null. A player who tours two systems sees the wrong sky, and worse, sees it *confidently* — a labeled, rendered orrery for a system they're not in. A confused player won't file a bug; they'll trust the map. Second: travel while drilled. The party jumps mid-scene (the narrator can move them any turn), `current_location` flips, and the widget keeps showing the old system with no refetch — same wrong-sky failure by another door. Third: what if the server starts emitting a *different* error code for missing system files (the handler gap means today it emits nothing — an unhandled exception server-side)? Then `orbital_unavailable` never arrives, the spinner runs forever, and AC5 is satisfied only in tests. That dependency on an unbuilt server behavior is documented but fragile. Fourth: a malicious/garbled ERROR message renders as text — React escapes it, fine — but an enormous message would blow out the panel; cosmetic only. Fifth: `regionCount` counts regions, not graph nodes — if a future world ships cartography with 2 regions but `navigation_mode: room_graph`, the widget would treat it as a cluster and hide the orrery behind a drill; today's worlds don't, but the derivation is one field away from lying. The first two findings are real and one is High; the rest are watched, documented, or out of scope.

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | Stale cached chart suppresses AC5 no-local-chart state (wrong system's orrery rendered after travel to unauthored region) | `src/App.tsx` orbital_unavailable branch; `src/components/GameBoard/widgets/MapWidget.tsx` error gate `lastOrbitalError && !chart` | Clear `lastOrbitalChart` (`setLastOrbitalChart(null)`) when an orbital error arrives so error supersedes chart symmetrically (and/or flip widget precedence to error-wins); TEA adds a precedence test: drilled + both error and stale chart present → `map-panel-no-local-chart` wins |
| [MEDIUM] | Drill state survives region change with no refetch — stale orrery for the new region | `MapWidget.tsx` (`drilledIn` useState) | Reset drill to campaign scale when `mapData.current_location` changes (or refetch); TEA adds covering test (rerender with new current_location while drilled) |
| [MEDIUM] | No wiring test for the new `lastOrbitalError` prop chain above the widget unit level | `MapWidget.twoScale.test.tsx` | TEA adds one GameBoard-level test: render GameBoard with `lastOrbitalError` + cluster mapData drilled state unreachable from GameBoard — minimum: assert GameBoard forwards the prop (e.g. MapWidget receives and renders error state with widget visible on map tab) |
| [LOW] | AC5 assertion doesn't pin `lastOrbitalError.message` rendering | `MapWidget.twoScale.test.tsx` AC5 test | `expect(panel.textContent).toContain(<fixture message>)` |
| [LOW] | Stale `worldOrbital` JSDoc ("Gates MapWidget's OrbitalChartView") | `GameBoard.tsx:226` | Reword to capability-signal description |
| [LOW] | Error fixture duck-typed in tests | `MapWidget.twoScale.test.tsx` | `import type { OrbitalIntentError }` and type the fixture |

**Data flow traced:** ERROR(`orbital_unavailable`) → App state → GameBoard prop → MapWidget text render (safe: React text node, `import type` everywhere, memo deps correct).
**Pattern observed:** good — shared-component reuse with callback threading instead of forking (`MapOverlay.tsx:163-168`); bad — asymmetric cache invalidation between paired message types (`App.tsx` chart-clears-error but not error-clears-chart).
**Error handling:** orbital rejection routed to the chart panel, not the narrative banner (`App.tsx:1331`, early return) — correct; the gap is state precedence, not handling shape.
**Dispatch tags considered:** [EDGE] n/a (disabled — lead covered boundaries in observations 1-2), [SILENT] finding 1 is this class (found by lead), [TEST] findings 2-4/6, [DOC] finding 5, [TYPE] n/a (disabled — rule-checker #1/#2 covered), [SEC] n/a (disabled — checked in observation 9: XSS-safe), [SIMPLE] n/a (disabled — no over-engineering seen; minimal diff), [RULE] rule-checker clean for new code.

**Handoff:** Back through red rework (Amos Burton/TEA writes the failing precedence + region-change + wiring tests; Naomi/Dev then makes them green with the App-side clear and drill-reset).

## Subagent Results (re-review, round-trip 1)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (97-8 flake + pre-existing lint warning only) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | not re-run | N/A | First-round findings verified fixed by lead (see assessment) |
| 5 | reviewer-comment-analyzer | Skipped | not re-run | N/A | First-round DOC finding verified fixed by lead (GameBoard JSDoc) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | none (16 rules × 38 instances on the delta, 0 violations) | N/A |

**All received:** Yes (2 re-run on the delta and returned; 5 disabled via settings; 2 first-round specialists not re-run — their findings were individually re-verified against the delta by the lead, below)
**Total findings:** 0 new; all 6 first-round findings verified FIXED

## Reviewer Assessment (re-review, round-trip 1)

**Verdict:** APPROVED

**Finding-by-finding verification (delta commits `007a932` + `8c50bc9`):**
1. [HIGH → FIXED] Error supersedes stale chart — widget gate is now `lastOrbitalError ?` (error always wins) AND App's `orbital_unavailable` branch clears `lastOrbitalChart` (symmetric invalidation). Pinned by the new test "error supersedes a stale cached chart" (drilled + stale yula chart + forma error → no-local-chart panel, no orbital panel, back affordance intact). [RULE]-checker #13 confirms the gate flip is sound.
2. [MEDIUM → FIXED] Region-change drill reset — drill state re-keyed to `drilledRegionId: string | null`; `drilledIn` derived as `drilledRegionId !== null && drilledRegionId === currentRegionId`, so travel invalidates the drill by construction (no effect, no reconciliation). Pinned by "returns to campaign scale when the party's current region changes mid-drill" (asserts `map-region-node-forma` data-current and no orbital panels).
3. [MEDIUM → FIXED] Wiring test — `GameBoard-map-orbital-error.test.tsx` renders the real GameBoard → MapWidget chain (Map tab click → occupied-node drill → error via rerender → message rendered). Satisfies the CLAUDE.md wiring-test mandate for the new prop chain. [TEST]
4. [LOW → FIXED] AC5 assertion pins `lastOrbitalError.message` via `toContain` (both AC5 tests + wiring test). [TEST]
5. [LOW → FIXED] `worldOrbital` JSDoc rewritten to capability-signal wording at `GameBoard.tsx:225-229`. [DOC]
6. [LOW → FIXED] Error fixtures typed via `import type { OrbitalIntentError }` + shared `errorFixture(): OrbitalIntentError`. [TYPE]

**New observation (not blocking):** `drilledRegionId` persists as residue after travel, so returning to a previously-drilled region resumes the drill without a click. Benign-to-desirable: the enable flip resets the hook's fetch cycle (`useOrbitalChart.ts:80-84`), so a fresh chart for the correct region is fetched; the player simply finds their drill where they left it. Noted for UX review if anyone ever finds it surprising. [EDGE]

**Verification:** preflight re-run — full suite 2009/2010 (sole failure: pre-existing 97-8 flake), typecheck clean, lint clean except pre-existing App.tsx warning, 0 code smells. Rule-checker on the delta: 16 rules × 38 instances, 0 violations ([SEC]/[SILENT]/[SIMPLE] domains covered by its #10/#14/#15 checks on this small delta).
**Data flow traced:** orbital ERROR → `setLastOrbitalError` + `setLastOrbitalChart(null)` (same handler, batched) → GameBoard prop → widget error-wins gate → message text render. No path remains on which a stale chart can mask a rejection.
**Pattern observed:** good — region-keyed UI state making staleness structurally impossible instead of patched with effects (`MapWidget.tsx` `drilledRegionId`).
**Error handling:** symmetric invalidation between paired message types; rejection routed to the chart panel, never the narrative banner.

**Handoff:** To Camina Drummer (SM) for finish — PR creation and merge.

## Delivery Findings

### Reviewer (re-review, round-trip 1)
- No upstream findings during re-review.

### Reviewer (code review)
- **Gap** (blocking): error/chart precedence asymmetry — App clears `lastOrbitalError` on ORBITAL_CHART but never clears `lastOrbitalChart` on an orbital ERROR, so a cached chart from a previously-visited system suppresses the AC5 no-local-chart state and renders the wrong system's orrery.
  Affects `sidequest-ui/src/App.tsx` (clear chart in the orbital_unavailable branch) and `sidequest-ui/src/components/GameBoard/widgets/MapWidget.tsx` (error gate).
  *Found by Reviewer during code review.*
- **Question** (non-blocking): drill-state policy on region change (reset vs refetch) should be decided explicitly when fixing the MEDIUM above — recommend reset-to-campaign as the simpler, ADR-consistent behavior.
  Affects `sidequest-ui/src/components/GameBoard/widgets/MapWidget.tsx` (`drilledIn` lifecycle).
  *Found by Reviewer during code review.*

### Dev (implementation)
- **Gap** (non-blocking): confirming TEA's finding — live AC5 cannot fire until `OrbitalIntentHandler` converts `OrbitalContentMissingError` into a typed ERROR; the UI now matches `code === "orbital_unavailable"`, so the server fix should either reuse that code or the UI match must be extended when a new code (e.g. `orbital_system_missing`) is chosen.
  Affects `sidequest-server/sidequest/handlers/orbital_intent.py` (add the except branch; pick the wire code deliberately — natural home is story 98-5's server lane).
  *Found by Dev during implementation.*
- **Improvement** (non-blocking): stray untracked `src/styles/reference.css` sits in sidequest-ui's working tree (epic-100 leftover, no git home); it should be either committed by whoever owns it or deleted.
  Affects `sidequest-ui/src/styles/reference.css` (adopt or remove).
  *Found by Dev during implementation.*

### TEA (test design)
- **Gap** (non-blocking): `OrbitalIntentHandler` catches only `OrbitalContentUnavailableError` (code `orbital_unavailable`); the 98-2 fail-loud `OrbitalContentMissingError` for an unauthored `systems/<region>.yaml` is not converted to a typed ERROR message, so the UI may never receive the rejection AC5 renders.
  Affects `sidequest-server/sidequest/handlers/orbital_intent.py` (catch `OrbitalContentMissingError` and emit a typed ERROR code the UI can match).
  *Found by TEA during test design.*
- **Question** (non-blocking): U1 AC2 says "Selecting/entering a node drills into that system's orrery" — for a *non-occupied* node the server has no resolution path (98-2 keys to the party's current region). Tests pin ADR-141's narrower wording ("drilled into from the node the party occupies"); confirm at spec-check whether any-node browsing is a future story.
  Affects `sidequest-ui/src/components/GameBoard/widgets/MapWidget.tsx` (drill gate on `activeNodeId`).
  *Found by TEA during test design.*
- **Improvement** (non-blocking): pre-existing flaky `lobby-start-ws-open.test.tsx` timeout reproduced in the RED run; already tracked as story 97-8 — no action in 98-3.
  Affects `sidequest-ui/src/__tests__/lobby-start-ws-open.test.tsx` (97-8 scope).
  *Found by TEA during test design.*

### TEA (test design — round-trip 1)
- No upstream findings during test design (round-trip 1).

### Dev (implementation — round-trip 1)
- No upstream findings during implementation (round-trip 1).

## Design Deviations

### Dev (implementation)
- **Campaign scale renders the full MapOverlay, not a bare graph**
  - Spec source: docs/superpowers/specs/2026-06-08-two-scale-spatial-model-epic-design.md, Story U1 AC1 + key-files table
  - Spec text: "Cluster world (perseus_cloud) default Map = cartography nodes-and-edges graph rendered via the shared d3-dag component from 100-10" / "`components/MapOverlay.tsx` (drives the graph)"
  - Implementation: The campaign-scale branch renders `MapOverlay` (which renders `CartographyMap` plus the regions/routes text panels) with an `onNodeSelect` pass-through, rather than mounting `CartographyMap` directly.
  - Rationale: The spec's own key-files table names MapOverlay as the graph driver; reusing it keeps the regions/routes legend, the visited/current overlay logic, and the single existing CartographyMap call site (reuse-first, no forked render path).
  - Severity: trivial
  - Forward impact: none — `map-region-graph` assertions hold either way.
  - → ✓ ACCEPTED by Reviewer: the spec's own key-files table names MapOverlay as the graph driver; reuse over fork is the correct call.

### TEA (test design)
- **Drill-down restricted to the occupied node (not any node)**
  - Spec source: docs/superpowers/specs/2026-06-08-two-scale-spatial-model-epic-design.md, Story U1 AC2
  - Spec text: "Selecting/entering a node drills into **that system's orrery**; a back affordance returns to the galactic graph."
  - Implementation: Tests assert clicking a non-occupied node does NOT send an orbital intent; only the current-region node drills (intent `{kind:"view_map", scope:"system_root"}`).
  - Rationale: ADR-141 states the orrery is "drilled into from the node the party occupies," and the merged 98-2 server resolves system files by the party's current region only — an any-node drill would render the *wrong* system's chart against today's wire protocol.
  - Severity: minor
  - Forward impact: if any-node orrery browsing is wanted, it needs a region-scoped view intent server-side (new story); 98-4/98-5 are unaffected.
  - → ✓ ACCEPTED by Reviewer: ADR-141's "drilled into from the node the party occupies" is the controlling text, and the merged 98-2 wire protocol cannot serve any-node charts — drilling elsewhere would render the wrong system (exactly the failure class my HIGH finding catches in another form).
- **AC5 error seam defined as a new `lastOrbitalError` MapWidget prop**
  - Spec source: docs/superpowers/specs/2026-06-08-two-scale-spatial-model-epic-design.md, Story U1 AC5
  - Spec text: "A node with no authored orrery shows a legible 'no local chart' state on drill-down, not a crash or blank."
  - Implementation: Tests define `lastOrbitalError?: { code: string; message: string } | null` on MapWidget (mirroring the `lastOrbitalChart` threading pattern) and testid `map-panel-no-local-chart`.
  - Rationale: the spec names the UI state but not the data seam; the ERROR-message prop mirror is the least-new-machinery path consistent with how chart responses already flow. Server-side conversion gap logged as a Delivery Finding.
  - Severity: minor
  - Forward impact: Dev must thread the prop from App's ERROR handling; Reviewer should check the error code string matches whatever the server emits once the handler gap is fixed.
  - → ✓ ACCEPTED by Reviewer: the seam itself is sound (mirrors `lastOrbitalChart` threading); the precedence flaw between the two props is logged as the HIGH finding, which is an implementation bug, not a fault of this deviation. Code-string match (`orbital_unavailable`) re-checked: it is the only orbital code the server emits today.

### Reviewer (audit)
- All three logged deviations stamped ACCEPTED above. No undocumented deviations found — the diff was checked against epic spec §4 U1 ACs, ADR-141, and the session scope; every divergence is already in the log.

### TEA (test design — round-trip 1)
- No deviations from spec — the round-trip tests implement the Reviewer's required fixes verbatim (error-wins precedence at the widget gate; reset-to-campaign on region change, the Reviewer's recommended policy).
  - → ✓ ACCEPTED by Reviewer: confirmed against the delta — tests match the rejection's fix directions exactly.

### Dev (implementation — round-trip 1)
- No deviations from spec — fixes implement the Reviewer's required directions exactly (error-wins gate + App-side chart clear; region-keyed drill state realizing the reset-to-campaign policy).
  - → ✓ ACCEPTED by Reviewer: confirmed against the delta; the region-keyed state is a cleaner realization of the reset policy than the literal effect-based reset I sketched.

### Reviewer (audit — round-trip 1)
- No undocumented deviations in the rework delta.