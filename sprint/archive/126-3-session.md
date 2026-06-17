---
story_id: "126-3"
jira_key: ""
epic: "126"
workflow: "tdd"
---
# Story 126-3: [FATE/UX] Surface Fate gear so a Fate player isn't stranded on an empty native Inventory panel

## Story Details
- **ID:** 126-3
- **Jira Key:** (none — epic-126 is [no jira])
- **Workflow:** tdd
- **Stack Parent:** none

## Story Context

Epic 126 captures post-playtest follow-ups from the 2026-06-16/17 Fate Core evaluation session (annees_folles, ADR-144 binding). Story 126-3 addresses a UX gap discovered during play: a Fate player opening the Inventory tab sees an empty native panel (items:[], gold:0) and never learns their gear became aspects.

**Working-as-designed per ADR-144:** The 114-10 migration (#472) deliberately deleted inventory.yaml for all four Fate packs. Fate has no carried inventory and no economy (per game/ruleset/fate_gear.py + 2026-06-15 design spec). Gear dissolves into aspects via `source_gear`. Populating inventory.items/gold would re-introduce the carried inventory that ADR-144 explicitly removed — a defined hard error.

**Decision (Keith, 2026-06-17):** Option (a) — HIDE the native Inventory tab for ruleset:fate PCs. Option (b), a read-only FatePanel Gear view, was declined.

**Critical Implementation Gotcha (from story description):** A GameBoard dock tab is registered in TWO places:
1. `widgetRegistry` / GameBoard (desktop path)
2. `MobileTabView`'s own `TABS` array (mobile path)

The jsdom wiring tests render the mobile path, so the conditional-hide must cover BOTH registrations or the tab-reachability test will mismatch desktop vs mobile visibility.

## Technical Approach

UI-only change. No server work despite the epic's server repo tag (that was inherited from epic context). The fix is pure presentation:

1. Determine ruleset from game state (likely via `pc.ruleset` or `game.genre.ruleset`)
2. Conditionally skip Inventory tab registration for `ruleset === 'fate'` in:
   - GameBoard's widget registry (where desktop tabs register)
   - MobileTabView's TABS array (where mobile tabs register)
3. Native (WN/non-Fate) packs remain unchanged — they keep Inventory
4. Do NOT populate inventory.items/gold for Fate pCs (preserve ADR-144 guard)

## Acceptance Criteria

- The native Inventory tab/panel is hidden for ruleset:fate PCs in BOTH desktop (widgetRegistry/GameBoard) AND mobile (MobileTabView TABS) paths
- Native (WN/non-Fate) packs are unchanged and keep the Inventory tab
- inventory.items / gold are NOT populated for Fate PCs (ADR-144 guard preserved)
- Wiring/render test: a Fate PC's GameBoard has no Inventory tab (desktop + mobile); a native PC's does

## Sm Assessment

**Routing decision: ready for RED (TEA / Argus Panoptes).** Scope is small, well-bounded, and fully specified — no design ambiguity remains because Keith already chose option (a) (hide the native Inventory tab for `ruleset: fate` PCs; the FatePanel "Gear" view, option b, was declined). This is a UI-only presentation change; the `server` repo tag is inherited from the epic and should be ignored.

**What the RED tests must pin (the gate against half-wiring):**
- A `ruleset: fate` PC's GameBoard exposes **no** Inventory tab on **both** registration paths — desktop (`widgetRegistry`/GameBoard) **and** mobile (`MobileTabView` TABS). This dual-path coverage is the crux: per the project's known dock-tab gotcha, a tab registers in two places and the jsdom wiring tests render the mobile path, so a test that only checks desktop will pass while mobile still leaks the tab.
- A native (WN / non-Fate) PC's GameBoard **still shows** Inventory — the negative control proving we hid by ruleset, not unconditionally.
- The ADR-144 guard holds: nothing in this change populates `inventory.items`/`gold` for a Fate PC (no carried-inventory reintroduction).

**Constraints for downstream agents:** UI-only (branch `feat/126-3-hide-fate-inventory-tab` in sidequest-ui, develop-based). Do not touch the server or the Fate gear model. Determine ruleset from game state (`pc.ruleset` / `game.genre.ruleset` — Dev to confirm the actual accessor).

**Jira:** intentionally skipped — epic-126 stories carry no Jira key (project `jira_sprint_id: 0`).

## TEA Assessment

**Tests Required:** Yes
**Reason:** A behavioral UI presence-gate with a known dual-surface wiring hazard (desktop dockview + mobile both consume the same `availableWidgets` set) — needs a render test AND a source-level gate guard so a wrong-layer fix is caught.

**Test Files:**
- `sidequest-ui/src/components/GameBoard/__tests__/GameBoard-fate-inventory-tab.test.tsx` — 9 tests across 4 groups.

**Tests Written:** 9 tests covering all 4 ACs. **Status:** RED — verified via testing-runner: 2 failing drivers + 7 passing guards/controls (no compile/import/type errors).

**RED drivers (fail today, pass once the gate lands):**
1. `does NOT show the Inventory ('Items') tab for a Fate PC — even with inventory data present` (behavioral, mobile render). Today `availableWidgets` adds `"inventory"` unconditionally.
2. `availableWidgets adds 'inventory' only when fateData is null` (raw-source guard). Forces the fix into the SHARED `availableWidgets`, not MobileTabView's own filter.

**Passing guards/controls (7):** native PC shows Items (AC2); native PC + active confrontation still shows Items (over-broad-gate guard); useMemo deps include `fateData` (#6); `WIDGET_REGISTRY` keeps `"inventory"` (no-deletion); MobileTabView TABS keeps `"inventory"` (no-deletion); MobileTabView filter hides/shows Items per `availableWidgets` (mobile contract, both directions).

**The implementation Dev should make (one-line gate):** in `GameBoard.tsx` `availableWidgets` useMemo (~line 398), change the unconditional `available.add("inventory")` to `if (fateData == null) available.add("inventory")`. Both the desktop dockview and MobileTabView read this set, so the single gate covers both surfaces. Do NOT gate inside `MobileTabView.visibleTabs` (would leave the desktop dock showing the tab — the half-wiring the RED source-guard catches). Do NOT remove the registry/TABS entries (the 7 WN/native packs need them). `fateData` is already in the useMemo deps (line 441) — no deps change needed. UI-only: do not touch inventory data (ADR-144).

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #6 React useMemo deps include the gate signal | `availableWidgets useMemo deps include fateData` | passing (guard) |
| #4 Null/undefined — ruleset null-check (not a truthy `||`) | `does NOT show ... Fate PC` + source-gate (`== null` / `=== null` / `!fateData`) | failing (RED) |
| #8 Test quality — meaningful assertions, no `as any` | self-check: 9/9 non-vacuous; raw imports use the precedented `as unknown as {default:string}` (mirrors gameboard-wiring.test.tsx); zero `as any` | n/a (self-check) |
| Project: every test suite needs a wiring test / no half-wired features | render tests reach the production GameBoard path; source-gate + registry/TABS guards enforce BOTH surfaces | mixed (1 RED, rest guards) |

**Rules checked:** 3 of 13 TS lang-review rules are applicable to a one-line presence-gate (#4 null-handling, #6 useMemo deps, #8 test-quality) — all 3 covered. The other 10 (enums, async, modules, input-validation, error-handling, perf, build-config, etc.) are not engaged by this change.
**Self-check:** 0 vacuous tests (all 9 assert a concrete presence / absence / match / contain).

**Handoff:** To Hephaestus the Smith (Dev) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-ui/src/components/GameBoard/GameBoard.tsx` — one-line gate in the `availableWidgets` useMemo: `available.add("inventory")` is now wrapped in `if (fateData == null) { ... }`. `fateData == null` is the ruleset!='fate' signal (the server emits FATE_STATE only on Fate packs, server #880). Both the desktop dockview and MobileTabView read `availableWidgets`, so this single gate hides the Inventory tab on both surfaces for Fate PCs and leaves the 7 WN/native packs untouched. `fateData` was already in the useMemo deps — no deps change. A documenting comment explains the ADR-144 rationale.

Followed TEA's prescription exactly (one-line gate at the shared site; no MobileTabView/registry/TABS edits; no inventory-data changes). Minimalist: the only logic change is the `if` guard.

**Tests:** GREEN — verified via testing-runner.
- Story file `GameBoard-fate-inventory-tab.test.tsx`: 9/9 pass (the 2 RED drivers now green, 7 guards still green).
- GameBoard `__tests__/` regression sweep: 96/96 pass (14 files).
- Full sidequest-ui suite: **2392/2392 pass (274 files)** — no regressions anywhere.
- `tsc --noEmit` clean; `eslint GameBoard.tsx` clean.

**Branch:** `feat/126-3-hide-fate-inventory-tab` (pushed to origin).

**Handoff:** To Hermes Psychopompos (Reviewer) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 96/96 GameBoard tests green, story file 9/9, tsc clean, eslint clean, 0 smells |
| 2 | reviewer-edge-hunter | Yes | findings | 5 (all med/low) | confirmed 2 (downgraded LOW, non-blocking), dismissed 3 (rationale below) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — assessed directly: gate is a deliberate `Set.add` skip, no try/catch, no swallowed error (see [SILENT]) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — assessed directly: 9 meaningful assertions, negative controls present, 0 vacuous (see [TEST]) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — assessed directly: comment block accurate, names ADR/PR/pack-count (see [DOC]) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — assessed directly: no new types; loose `== null` consistent with sibling gate (see [TYPE]) |
| 7 | reviewer-security | Yes | clean | none | N/A — no fabrication, deliberate gate, no injection/leak, client-trust self-defeating |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — assessed directly: 1-line gate, minimal, no over-engineering (see [SIMPLE]) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — enumerated rules directly in Rule Compliance (see [RULE]) |

**All received:** Yes (3 enabled subagents returned; 6 disabled via `workflow.reviewer_subagents` and assessed directly by the reviewer)
**Total findings:** 0 confirmed-blocking, 2 confirmed-LOW (non-blocking), 3 dismissed (with rationale)

## Reviewer Assessment

**Verdict:** APPROVED

A 14-line, UI-only presence-gate (`available.add("inventory")` wrapped in `if (fateData == null)` inside the `availableWidgets` useMemo) plus a 240-line test file. No Critical/High findings across preflight (clean), security (clean), edge-hunter (5 med/low), and my own direct review of the 6 disabled domains. The change is minimal, idiomatic, consistent with existing sibling gates, and well-tested on both surfaces.

**Data flow traced:** server emits `FATE_STATE` only on a `ruleset=='fate'` pack (server #880) → `useStateMirror` parses/guards it → `fateData` prop → `availableWidgets` gate (`fateData == null` ⇒ add `"inventory"`) → consumed by BOTH the desktop dockview layout AND `MobileTabView.visibleTabs` (`TABS.filter(t => t.id==="narrative" || availableWidgets.has(t.id))`, MobileTabView.tsx:133). Safe: a Fate PC never gets the tab on either surface; a native PC (fateData null/undefined forever) always does.

**Pattern observed:** the conditional add is consistent with the sibling gates in the same useMemo — `if (worldSlug === "coyote_star") available.add("ship")` (GameBoard.tsx:415) and `if (navMode === "region" || ...) available.add("location")` (426). Gating tab presence on a STABLE per-session signal is the established pattern here; the `location` comment explicitly chose a stable signal to avoid reconnect blink, and `fateData`/ruleset is exactly such a stable signal.

### Observations (tagged by source)

- `[VERIFIED]` Gate consistency — `fateData == null` (GameBoard.tsx:408) is the exact complement of the Fate-tab gate `if (fateData != null) available.add("fate")` (GameBoard.tsx:434). Mutually exclusive on the same server-authoritative signal; idiomatic null-or-undefined check (TS lang-review #4 — not the `||`-falsy bug; `fateData` is object-or-null/undefined, never `0`/`""`).
- `[VERIFIED]` Dual-surface coverage — evidence: MobileTabView.tsx:133 filters on `availableWidgets.has(t.id)`; the desktop dockview mounts panels from the same set. One gate hides both. The raw-source test forecloses a mobile-only (wrong-layer) fix.
- `[EDGE]` (LOW, non-blocking) F1 — a late-arriving `FATE_STATE` (fateData null→non-null AFTER GameBoard mount) could briefly add then remove the Items tab on the dockview (a transient flash). **Downgraded:** GameBoard mounts post-chargen, after FATE_STATE is delivered (the working Fate tab depends on the same at-mount presence — if fateData arrived late, the Fate tab would be equally broken, and it is not). Self-corrects via the sync effect (`removePanel`). Pre-existing property of ALL dataGated widgets; not introduced here. The edge-hunter's premise that the diff "violates the add-unconditionally invariant" is incorrect — ship/location/fate are already conditional adds on stable signals in this same block. No fix required.
- `[EDGE]` (LOW, non-blocking) F2 — `contentSignals` still computes an `inventory` entry when fateData != null, so MobileTabView's badge loop could accumulate a stale (never-rendered) `inventory` badge. **Downgraded:** Fate packs carry no inventory (ADR-144; `resolve_inventory` returns `None`), so `inventoryData` is null and the inventory signal never changes → no badge churn, nil practical trigger. Captured as a non-blocking tidy-up delivery finding.
- `[EDGE]` (dismissed) F3 — loose `== null` also catches `undefined`. The subagent itself concluded "there is no actual bug"; behavior is intentional and consistent with the sibling gate. Dismissed: not a defect.
- `[TEST]` (LOW, non-blocking) F4 — the raw-source regex guard could false-green after a logically-inverted refactor (`if (fateData !== null) {} else { add }`). **Downgraded:** the behavioral render test (`renderBoard({ fateData: seededFate })` → no Items tab) is refactor-proof and is the PRIMARY guard; the raw-source test is a precedented STRUCTURAL secondary (identical pattern to the `ship` guard in gameboard-wiring.test.tsx) whose purpose is to force the gate into the shared set. Net behavior stays covered. No blocker.
- `[TEST]` (LOW, non-blocking) F5 — the useMemo-deps regex is brittle (single-line dep array assumption). **Downgraded:** identical pattern is already precedented (gameboard-wiring.test.tsx:101); dep array is single-line today; no real failure. No blocker.
- `[TEST]` (VERIFIED — test_analyzer disabled, assessed directly) — 9 assertions, all meaningful (presence/absence/match/contain). Strong negative controls: a NON-empty inventory handed to a Fate board still hides the tab (proves ruleset-gating, not data-emptiness); native + active confrontation still shows it (proves the gate isn't over-broad). Zero vacuous assertions, zero `as any`.
- `[SILENT]` (VERIFIED — silent_failure_hunter disabled, assessed directly) — the gate is a deliberate skip of `Set.add`, not error-swallowing. No try/catch, no default substituted, no fallback path. Complies with No-Silent-Fallbacks; the comment documents the intentional ADR-144 gate.
- `[DOC]` (VERIFIED — comment_analyzer disabled, assessed directly) — the 10-line comment accurately names the pack count (4), server PR (#880), ADR-144, the migration (#472), the dual-surface claim, and the signal semantics. No stale/misleading documentation.
- `[TYPE]` (VERIFIED — type_design disabled, assessed directly) — no new types; `fateData: FateStatePayload | null` unchanged. The test's `as unknown as { default: string }` is the only viable type for a Vite `?raw` import and is precedented (gameboard-wiring.test.tsx) — compile-time, test-only.
- `[SEC]` (confirmed clean) — security subagent: no inventory fabrication (ADR-144 held), deliberate ruleset gate (not error-swallowing), no injection/XSS/info-leak, client-trust self-defeating (forging `FATE_STATE` only HIDES inventory; the gate is open-by-default so there is no bypass to restore it).
- `[SIMPLE]` (VERIFIED — simplifier disabled, assessed directly) — minimal: one `if` guard, no abstraction, no dead code. Cannot be simpler while covering both surfaces from the shared set.
- `[RULE]` (VERIFIED — rule_checker disabled, enumerated directly) — see Rule Compliance below; all applicable rules pass.

### Rule Compliance

| Rule | Instances in diff | Verdict |
|------|-------------------|---------|
| TS #4 null/undefined (idiomatic check, not `||`) | 1 — the `fateData == null` gate | compliant (loose `== null` = null-or-undefined; matches sibling `!= null`) |
| TS #6 React useMemo deps include captured signals | 1 — `availableWidgets` useMemo | compliant (`fateData` already in deps, GameBoard.tsx:453) |
| TS #1/#2 type-safety escapes / double-cast | 1 — test `as unknown as {default:string}` | compliant (only viable type for `?raw`; precedented; test-only) |
| TS #8 test quality (meaningful, no `as any`) | 9 tests | compliant (0 vacuous, 0 `as any`, negative controls) |
| SOUL No Silent Fallbacks | 1 — the gate | compliant (deliberate, documented; no swallowed error) |
| CLAUDE No half-wired features | both surfaces | compliant (shared gate + dual-path source/registry/TABS guards) |
| ADR-144 no inventory fabrication for Fate PCs | production change | compliant (no inventory data read or written) |

### Devil's Advocate

The strongest case that this is broken: the late-`FATE_STATE` flash (F1) colliding with the in-file comment that swears "Every widget that should ever appear MUST be added here UNCONDITIONALLY." On a mid-session reconnect where the state mirror has not yet replayed `FATE_STATE`, `fateData` is momentarily null, so the gate adds `"inventory"` to the mount layout; when the replay lands, `availableWidgets` recomputes without it and the sync effect tears the panel down. A Fate player who clicks "Items" in that sub-second window sees exactly the empty native panel this story exists to abolish — now intermittent instead of constant. A second angle: the gate trusts `fateData` as a proxy for ruleset; if the server ever (bug) emitted `FATE_STATE` on a native pack, inventory would silently vanish for a pack that genuinely has it. A third: a malicious client could drop its own `FATE_STATE` to keep inventory on a Fate pack. A fourth: the raw-source test could rot to a false green after a logically-equivalent inverted-`if` refactor, removing the very dual-path guarantee it was written to protect. A fifth: a future pack that is both Fate AND wants carried items would be silently inventory-less.

Why none of these reach Critical/High: the flash requires abnormal late-`fateData`, which the architecture rules out in the normal flow (GameBoard mounts after chargen delivers `FATE_STATE`) and which would equally break the already-shipped Fate tab — it is sub-second, self-correcting, and pre-existing to every dataGated widget (the `location` gate documents the exact same reconnect concern and resolves it by gating on a stable signal, which is what `fateData` is). The native-false-positive and dropped-`FATE_STATE` cases are server bugs / self-defeating attacks (the latter only yields an empty panel, no advantage) and would surface loudly via the co-gated Fate tab. The Fate-pack-with-inventory case is forbidden by ADR-144 (a defined hard error), so the gate is correct by invariant. The test-rot risk is backstopped by the refactor-proof behavioral render test. Net: real edges, all cosmetic or invariant-protected, none blocking. The F2 stale-badge is captured as a non-blocking follow-up.

**Handoff:** To Themis the Just (SM) for finish-story.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-17T07:22:51Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-17T06:59:06Z | 2026-06-17T07:01:50Z | 2m 44s |
| red | 2026-06-17T07:01:50Z | 2026-06-17T07:11:37Z | 9m 47s |
| green | 2026-06-17T07:11:37Z | 2026-06-17T07:15:48Z | 4m 11s |
| review | 2026-06-17T07:15:48Z | 2026-06-17T07:22:51Z | 7m 3s |
| finish | 2026-06-17T07:22:51Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): The `inventory` widget is `dataGated: true` in `widgetRegistry` but is added to `availableWidgets` UNCONDITIONALLY (`GameBoard.tsx:398`) — it never actually gates on `inventoryData`. The 126-3 `fateData == null` gate is the first real gating applied to inventory; add it at this same site rather than introducing a parallel `inventoryData` gate. Affects `sidequest-ui/src/components/GameBoard/GameBoard.tsx` (availableWidgets useMemo). *Found by TEA during test design.*

### Dev (implementation)
- **Confirmed** (non-blocking): Acted on TEA's finding above — added the gate at the existing `availableWidgets` site (the `available.add("inventory")` line), introducing no parallel `inventoryData` gate. The `inventory` registry entry's `dataGated: true` remains nominal for native packs (the tab is added unconditionally for them and the renderer shows a loading/empty state until `inventoryData` arrives) — unchanged by this story and out of scope. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `contentSignals` (`GameBoard.tsx:537`) still computes an `inventory` entry even when `fateData != null`, so MobileTabView's badge loop can track a never-rendered `inventory` badge on a Fate pack. Harmless today — Fate packs carry no inventory (ADR-144; `resolve_inventory` → `None`), so the signal never changes and no badge fires — but a tidy follow-up could mirror the `availableWidgets` gate by omitting the `inventory` signal when `fateData != null`. Affects `sidequest-ui/src/components/GameBoard/GameBoard.tsx` (contentSignals useMemo). *Found by Reviewer during code review (edge-hunter F2).*
- **Improvement** (non-blocking): The raw-source guard test (`GameBoard-fate-inventory-tab.test.tsx`, "availableWidgets adds 'inventory' only when fateData is null") is a precedented structural check but could false-green after a logically-inverted refactor; the behavioral render test in the same file is the refactor-proof primary, so coverage is intact. Optional: lean on the render test as the canonical guard. Affects `sidequest-ui/src/components/GameBoard/__tests__/GameBoard-fate-inventory-tab.test.tsx`. *Found by Reviewer during code review (edge-hunter F4).*

## Impact Summary

**Upstream Effects:** 2 findings (0 Gap, 0 Conflict, 0 Question, 2 Improvement)
**Blocking:** None

- **Improvement:** The `inventory` widget is `dataGated: true` in `widgetRegistry` but is added to `availableWidgets` UNCONDITIONALLY (`GameBoard.tsx:398`) — it never actually gates on `inventoryData`. The 126-3 `fateData == null` gate is the first real gating applied to inventory; add it at this same site rather than introducing a parallel `inventoryData` gate. Affects `sidequest-ui/src/components/GameBoard/GameBoard.tsx`.
- **Improvement:** `contentSignals` (`GameBoard.tsx:537`) still computes an `inventory` entry even when `fateData != null`, so MobileTabView's badge loop can track a never-rendered `inventory` badge on a Fate pack. Harmless today — Fate packs carry no inventory (ADR-144; `resolve_inventory` → `None`), so the signal never changes and no badge fires — but a tidy follow-up could mirror the `availableWidgets` gate by omitting the `inventory` signal when `fateData != null`. Affects `sidequest-ui/src/components/GameBoard/GameBoard.tsx`.

### Downstream Effects

- **`sidequest-ui/src/components/GameBoard`** — 2 findings

### Deviation Justifications

1 deviation

- **No UI test for AC-3's server-side "inventory.items/gold not populated for Fate PCs"**
  - Rationale: This is a UI-only story (session scope + story description); `sidequest-ui` has no server in its test harness and the UI cannot populate server-side inventory. The non-population invariant is enforced server-side (`resolve_inventory` returns `None` for the four Fate packs per the FIXER ruling) and belongs to a `sidequest-server` story, not this UI change.
  - Severity: minor
  - Forward impact: none — the server invariant is already enforced; this UI change neither reads nor writes inventory data for Fate PCs.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **No UI test for AC-3's server-side "inventory.items/gold not populated for Fate PCs"**
  - Spec source: context-story-126-3.md, AC-3
  - Spec text: "inventory.items / gold are NOT populated for Fate PCs (ADR-144 guard preserved)."
  - Implementation: Tests assert the UI realization only — a Fate PC has no Inventory tab on either surface, and inventory is hidden by GATING (not by deleting the registry/TABS entry). No test asserts server-side non-population of `inventory.items`/`gold`.
  - Rationale: This is a UI-only story (session scope + story description); `sidequest-ui` has no server in its test harness and the UI cannot populate server-side inventory. The non-population invariant is enforced server-side (`resolve_inventory` returns `None` for the four Fate packs per the FIXER ruling) and belongs to a `sidequest-server` story, not this UI change.
  - Severity: minor
  - Forward impact: none — the server invariant is already enforced; this UI change neither reads nor writes inventory data for Fate PCs.

### Dev (implementation)
- No deviations from spec. Implemented exactly the one-line `availableWidgets` gate TEA prescribed; no structure simplified, no abstraction added, no inventory data touched.

### Reviewer (audit)
- **TEA: "No UI test for AC-3's server-side inventory.items/gold non-population"** → ✓ ACCEPTED by Reviewer: sound. AC-3 is a server invariant (ADR-144; `resolve_inventory` → `None` for the four Fate packs), unreachable from `sidequest-ui`'s test harness on a UI-only story. The UI realization (no Inventory tab on either surface; hidden by gating, not deletion) is fully tested, and the change provably touches no inventory data. Correctly scoped out — belongs to a `sidequest-server` story if a server-side regression test is wanted.
- **Dev: "No deviations from spec"** → ✓ ACCEPTED by Reviewer: verified against the diff — the implementation is exactly TEA's prescribed one-line gate at the shared `availableWidgets` site, no extra abstraction, no inventory-data writes, registry/TABS entries untouched. Confirmed truly deviation-free.
- No undocumented deviations found. The diff matches the story scope (option-a hide-the-tab, UI-only, ADR-144-preserving) exactly.