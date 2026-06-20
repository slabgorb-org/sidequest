---
story_id: "126-27"
jira_key: ""
epic: ""
workflow: "trivial"
---
# Story 126-27: [FATE/CLEANUP] Delete unreferenced FatePanel function + sweep stale FateWidget comments (126-26 follow-up)

## Story Details
- **ID:** 126-27
- **Jira Key:** (none)
- **Workflow:** trivial
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-20T05:06:38Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-20T18:00:00Z | 2026-06-20T04:46:11Z | -47629s |
| implement | 2026-06-20T04:46:11Z | 2026-06-20T04:57:49Z | 11m 38s |
| review | 2026-06-20T04:57:49Z | 2026-06-20T05:06:38Z | 8m 49s |
| finish | 2026-06-20T05:06:38Z | - | - |
| implement | 2026-06-20T18:00:00Z | 2026-06-20T04:57:49Z | -46931s |
| review | 2026-06-20T04:57:49Z | 2026-06-20T05:06:38Z | 8m 49s |
| finish | 2026-06-20T05:06:38Z | - | - |

## Delivery Findings

### Dev (implementation)
- **Gap** (non-blocking): `tsc -b` is RED on develop independent of this story — `src/components/GameBoard/__tests__/GameBoard-fate-inventory-tab.test.tsx:203` constructs a `Set<WidgetId>` including `'fate'`, but 126-26 removed `'fate'` from the `WidgetId` union (TS2769). Verified pre-existing via `git stash` (1 error with or without my changes; my diff adds 0). Affects `src/components/GameBoard/__tests__/GameBoard-fate-inventory-tab.test.tsx` (drop `'fate'` from the WidgetId set literal — another 126-26 follow-up). Vitest is GREEN (no typecheck), so it does not fail the test suite. *Found by Dev during implementation.*
- **Improvement** (non-blocking): `src/components/FateConflictSurface.tsx:183` ("the always-on Fate SHEET is FatePanel's job") and `:371` ("data FatePanel renders") still name the deleted FatePanel function present-tense. Left untouched because the 126-27 scope guard explicitly forbids touching the fate-conflict surface. Affects `src/components/FateConflictSurface.tsx` (reword FatePanel → the Fate sheet / FateCharacterSheet in a future, non-scope-guarded story). *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (non-blocking): deleting `FatePanel.test.tsx` dropped granular `FateCharacterSheet` rendering assertions — free-invoke **pips** (`fate-pip`), **stress boxes** (`fate-stress-box`), **consequence slots** (`fate-consequence`), aspect-kind grouping, and version-skew tolerance — that `CharacterPanelFateSheet.test.tsx` renders (its `FATE_SHEET` fixture carries stress/consequences/pips) but does not explicitly assert. `FateCharacterSheet` code is unchanged so nothing regressed, and the story explicitly mandated deleting both test files. Affects `src/components/__tests__/CharacterPanelFateSheet.test.tsx` (a follow-up could port the pip/stress/consequence assertions onto the surviving wiring test if that granularity is wanted). *Found by Reviewer during code review.*
- **Gap** (non-blocking): a second PRE-EXISTING develop test failure, independent of this story — `src/__tests__/no-google-fonts.test.ts > "the dice tray loads label faces from R2, not /public/fonts"` fails on clean develop (stash-verified: 1 failed/3 passed with my changes stashed). The diff touches no `src/dice` or `src/styles` files, so it cannot be the cause. Affects `src/dice/*` (the dice-tray font-source the test reads — a separate fix). *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 3 findings (2 Gap, 0 Conflict, 0 Question, 1 Improvement)
**Blocking:** None

- **Improvement:** `src/components/FateConflictSurface.tsx:183` ("the always-on Fate SHEET is FatePanel's job") and `:371` ("data FatePanel renders") still name the deleted FatePanel function present-tense. Left untouched because the 126-27 scope guard explicitly forbids touching the fate-conflict surface. Affects `src/components/FateConflictSurface.tsx`.
- **Gap:** deleting `FatePanel.test.tsx` dropped granular `FateCharacterSheet` rendering assertions — free-invoke **pips** (`fate-pip`), **stress boxes** (`fate-stress-box`), **consequence slots** (`fate-consequence`), aspect-kind grouping, and version-skew tolerance — that `CharacterPanelFateSheet.test.tsx` renders (its `FATE_SHEET` fixture carries stress/consequences/pips) but does not explicitly assert. `FateCharacterSheet` code is unchanged so nothing regressed, and the story explicitly mandated deleting both test files. Affects `src/components/__tests__/CharacterPanelFateSheet.test.tsx`.
- **Gap:** a second PRE-EXISTING develop test failure, independent of this story — `src/__tests__/no-google-fonts.test.ts > "the dice tray loads label faces from R2, not /public/fonts"` fails on clean develop (stash-verified: 1 failed/3 passed with my changes stashed). The diff touches no `src/dice` or `src/styles` files, so it cannot be the cause. Affects `src/dice/*`.

### Downstream Effects

Cross-module impact: 3 findings across 3 modules

- **`src/components`** — 1 finding
- **`src/components/__tests__`** — 1 finding
- **`src/dice`** — 1 finding

### Deviation Justifications

2 deviations

- **Removed FatePanel-only private symbols alongside the function**
  - Rationale: tsconfig.app.json/tsconfig.node.json set `noUnusedLocals: true` + `noUnusedParameters: true`, so leaving these orphaned symbols breaks `tsc -b`; they are also dead code (No-Stubbing/No-Dead-Code). Deleting "the unused FatePanel function" necessarily includes its private-only dependencies.
  - Severity: minor
  - Forward impact: none — these symbols had no other consumer.
- **Expanded the comment sweep beyond the three enumerated targets**
  - Rationale: deleting the FatePanel function strands these present-tense references to a now-nonexistent symbol. Cleaning references to one's own deletion is intrinsic, not scope creep, and keeps docs honest. Did NOT touch `FateConflictSurface.tsx` (which has two similar refs) — the scope guard explicitly forbids the fate-conflict surface; logged as a delivery finding instead.
  - Severity: minor
  - Forward impact: none — comment-only, no behavior change.

## Design Deviations

### Dev (implementation)
- **Removed FatePanel-only private symbols alongside the function**
  - Spec source: 126-27 session scope, point 1
  - Spec text: "Delete the unused FatePanel function and its two dedicated test files"
  - Implementation: also deleted the symbols only FatePanel referenced — the `FatePanelProps` interface, the `FONT_BODY` and `PANEL_LABEL` consts, and the now-unused `FateDiceTray` / `FateStatePayload` / `FateRollPayload` imports. `FateCharacterSheet`, `FateStunts`, `AspectGroups`, and all shared deps (`FONT_DISPLAY`, `FOLIO`, `formatRating`, `kindLabel`, `KIND_LABELS`, `KIND_ORDER`) are untouched.
  - Rationale: tsconfig.app.json/tsconfig.node.json set `noUnusedLocals: true` + `noUnusedParameters: true`, so leaving these orphaned symbols breaks `tsc -b`; they are also dead code (No-Stubbing/No-Dead-Code). Deleting "the unused FatePanel function" necessarily includes its private-only dependencies.
  - Severity: minor
  - Forward impact: none — these symbols had no other consumer.
- **Expanded the comment sweep beyond the three enumerated targets**
  - Spec source: 126-27 session scope, point 2
  - Spec text: "Sweep lingering 'FateWidget'/'dock Fate tab' references in files 126-26 did NOT touch: src/components/FatePanel.tsx:142, ...GameBoard-fate-conflict.test.tsx:18, ...useStateMirror.fate-roll.test.ts:9"
  - Implementation: additionally reworded `src/components/FatePanel.tsx:284` (FateStunts doc "Stats tab + dock widget"), `src/types/protocol.ts:109` ("UI consumer is the FatePanel"), and `src/types/payloads.ts:1153` ("the FatePanel renders every mechanical number") — all named the deleted FatePanel symbol present-tense as the live consumer/renderer; reworded to FateCharacterSheet (the surviving renderer).
  - Rationale: deleting the FatePanel function strands these present-tense references to a now-nonexistent symbol. Cleaning references to one's own deletion is intrinsic, not scope creep, and keeps docs honest. Did NOT touch `FateConflictSurface.tsx` (which has two similar refs) — the scope guard explicitly forbids the fate-conflict surface; logged as a delivery finding instead.
  - Severity: minor
  - Forward impact: none — comment-only, no behavior change.

### Reviewer (audit)
- **Removed FatePanel-only private symbols alongside the function** → ✓ ACCEPTED by Reviewer: sound. `noUnusedLocals`/`noUnusedParameters` (tsconfig.app/node) make these orphaned symbols a hard `tsc -b` break, and they are dead code. Verified the cascade is FatePanel-only: `FatePanelProps`, `FONT_BODY`, `PANEL_LABEL`, and the `FateDiceTray`/`FateStatePayload`/`FateRollPayload` imports had no other consumer; `AspectGroups`/`FateCharacterSheet`/`FateStunts` and shared helpers (`FONT_DISPLAY`, `FOLIO`, `formatRating`, `kindLabel`) remain consumed. `tsc -b` introduces 0 new errors from the diff.
- **Expanded the comment sweep beyond the three enumerated targets** → ✓ ACCEPTED by Reviewer: agrees with author reasoning. `protocol.ts:109` and `payloads.ts:1153` named the deleted `FatePanel` function present-tense as the live renderer; rewording them to `FateCharacterSheet` cleans dangling references to one's own deletion (intrinsic, not scope creep). Dev correctly did NOT touch `FateConflictSurface.tsx` (two similar refs) — the scope guard forbids the fate-conflict surface, and it was flagged as a delivery finding instead. Correct discipline.
- **No undocumented deviations found.** The diff matches the two logged deviations exactly; nothing slipped through.

Setup complete for 126-27 — a 1-point trivial-workflow cleanup in **sidequest-ui** (follow-up from 126-26). Verified the work is genuinely available (not already merged in another clone): `FatePanel.tsx`, both FatePanel test files, and the `FatePanel` function (line 304) all still exist on develop; the only importers of the `FatePanel` function are its own two test files.

**Scope (two cleanups, both sidequest-ui):**
1. **Dead code** — delete the production-unreferenced `FatePanel` function from `src/components/FatePanel.tsx` and its two dedicated test files (`src/components/__tests__/FatePanel.test.tsx`, `src/components/__tests__/FatePanel.fateRoll.test.tsx`). Its only consumer was the `FateWidget` 126-26 deleted.
2. **Stale comments** — sweep lingering `FateWidget`/`dock Fate tab` references in files 126-26 did not touch: `src/components/FatePanel.tsx:142`, `src/components/GameBoard/__tests__/GameBoard-fate-conflict.test.tsx:18`, `src/hooks/__tests__/useStateMirror.fate-roll.test.ts:9`. Reword to post-126-26 reality (non-conflict roll tray lives under Character→Stats; the Fate conflict surface has its own tray).

**Scope guard (DO NOT cross):** `FateCharacterSheet` is exported from the SAME `FatePanel.tsx` file and is still imported by `CharacterPanel` — it MUST stay. Do not touch `FateCharacterSheet` or the fate-conflict surface.

**Verification expectation:** after the FatePanel deletion, run the full Fate + GameBoard suite to confirm no regression, and confirm `tsc -b` build passes (stale node_modules can throw a phantom d3-dag error — `npm install` first if so).

Branch `feat/126-27-fatepanel-cleanup` created in sidequest-ui (off develop). Routing to **Agent Smith (Dev)** for the implement phase.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (sidequest-ui):**
- `src/components/FatePanel.tsx` — deleted the production-unreferenced `FatePanel` function and its only-private deps (`FatePanelProps`, `FONT_BODY`, `PANEL_LABEL`, the `FateDiceTray`/`FateStatePayload`/`FateRollPayload` imports); reworded the `FateCharacterSheet` doc block (`:142` sweep target) and the `FateStunts` doc to post-126-26 reality. **Kept** `FateCharacterSheet`, `FateStunts`, `AspectGroups` and all shared helpers.
- `src/components/__tests__/FatePanel.test.tsx` — **deleted** (FatePanel-only coverage).
- `src/components/__tests__/FatePanel.fateRoll.test.tsx` — **deleted** (FatePanel-only coverage).
- `src/components/GameBoard/__tests__/GameBoard-fate-conflict.test.tsx` — reworded `:18` stale `FateWidget` consumer ref.
- `src/hooks/__tests__/useStateMirror.fate-roll.test.ts` — reworded `:9` stale `FateWidget` consumer ref.
- `src/types/protocol.ts` / `src/types/payloads.ts` — reworded comments that named the deleted `FatePanel` function as the live consumer/renderer → `FateCharacterSheet` (see deviation #2).

Net diff: **20 insertions, 552 deletions**.

**Verification:**
- `FateCharacterSheet`/`FateStunts` coverage survives in `CharacterPanelFateSheet.test.tsx` (confirmed before deleting the FatePanel tests).
- Only production importer of the module is `CharacterPanel.tsx` (`FateCharacterSheet, FateStunts`) — no importer of the `FatePanel` function remained.
- **Tests: 515/515 passing (GREEN)** across 52 files — full Fate + GameBoard + CharacterPanel + state-mirror suites (`npx vitest run Fate GameBoard CharacterPanel useStateMirror`). No regression from the deletion.
- `tsc -b`: my diff adds **0** new type errors (verified clean cascade-deletion under `noUnusedLocals`). One PRE-EXISTING develop error remains in an untouched file — see Delivery Findings (GameBoard-fate-inventory-tab.test.tsx `'fate'` WidgetId, a separate 126-26 follow-up).

**Branch:** `feat/126-27-fatepanel-cleanup` (sidequest-ui)

**Handoff:** To review phase → The Merovingian (Reviewer).

## Subagent Results

Per `workflow.reviewer_subagents` settings, only `preflight` and `security` are enabled; the other seven are disabled and pre-filled as Skipped. The Merovingian assessed each disabled domain personally (see Reviewer Assessment tags).

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 (pre-existing tsc error, outside diff) | confirmed 0 (in-diff), 1 noted as pre-existing/out-of-scope |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (self-assessed [EDGE]) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings (self-assessed [SILENT]) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings (self-assessed [TEST] — coverage gap found) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings (self-assessed [DOC] — all 6 rewords verified accurate) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (self-assessed [TYPE] — 13-check TS list applied) |
| 7 | reviewer-security | Yes | clean | none | N/A — clean |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (self-assessed [SIMPLE]) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings (self-assessed [RULE]) |

**All received:** Yes (2 enabled subagents returned; 7 disabled via settings, self-assessed)
**Total findings:** 0 confirmed blocking, 2 dismissed-as-pre-existing (with rationale), 2 deferred (non-blocking delivery findings)

### Rule Compliance

Exhaustive enumeration of project rules (CLAUDE.md root + UI, SOUL.md) against the diff:

- **No Stubbing / No Dead Code** ("Dead code is worse than no code"): COMPLIANT — actively advanced. The story REMOVES the production-unreferenced `FatePanel` function + its orphaned deps. Verified no NEW dead code: every retained symbol (`AspectGroups`, `FateCharacterSheet`, `FateStunts`, `FONT_DISPLAY`, `FOLIO`, `formatRating`, `kindLabel`, `KIND_LABELS`, `KIND_ORDER`) has a live consumer; `tsc -b` reports 0 new unused-symbol errors from the diff.
- **No Silent Fallbacks**: COMPLIANT — no fallback added or removed. The deleted "version-skew tolerance" test exercised FatePanel's graceful degradation; the same `?? []` guards live on in the unchanged `FateCharacterSheet` (`skills ?? []`, `aspects ?? []`, etc., FatePanel.tsx:161-165).
- **Don't Reinvent / Verify Wiring / Every Test Suite Needs a Wiring Test**: COMPLIANT — the surviving renderer `FateCharacterSheet` is wired via `CharacterPanel.tsx:7` (live import) and exercised by `CharacterPanelFateSheet.test.tsx` (renders it through `CharacterPanel` — a true wiring test, not isolation-only).
- **OTEL Observability Principle**: COMPLIANT (exempt) — CLAUDE.md states OTEL is "Not needed for: Cosmetic UI changes." This is dead-code deletion + comment rewords with zero subsystem-decision change.
- **No Jira / personal project (slabgorb-org)**: COMPLIANT — no Jira or work-org references anywhere in the diff.
- **Comment accuracy** (DOC): COMPLIANT — all 6 reworded comments traced to live code and verified accurate (see [DOC] tag).

### Devil's Advocate

Let me argue this change is broken. **First attack — the deletion stranded a live consumer.** If anything still mounted `<FatePanel>` (JSX), or a widget registry resolved the string `"FatePanel"` to a component, deleting the function white-screens that surface. I traced it: the preflight grep returns ten `FatePanel` hits, but exactly one is an import (`CharacterPanel.tsx:7`) and it imports `{ FateCharacterSheet, FateStunts }` — named exports that survive — not the deleted default. The other nine are prose in comments. 126-26 already deleted `widgets/FateWidget.tsx` and the `'fate'` `WidgetId`, so no registry entry can reach the function. No live consumer; the white-screen attack fails. **Second attack — coverage theatre.** "515 green" can hide a coverage cliff: the deleted `FatePanel.test.tsx` asserted free-invoke pips, stress boxes, consequence slots, and aspect-kind grouping. Does `CharacterPanelFateSheet.test.tsx` re-assert them? No — it renders a fixture carrying stress/consequences/pips but only asserts skills, aspects, fate-points, and stunts. So regression detection for those sub-renderings genuinely narrows. This is real, and I filed it (non-blocking) — but it does NOT block, because the `FateCharacterSheet`/`AspectGroups` code that renders pips/stress/consequences is byte-unchanged, the story explicitly mandated deleting both files, and the wiring-test rule is still satisfied. **Third attack — a confused future maintainer.** The reworded comments could mislead. I verified each names a real, current surface (Character→Stats tab, `CharacterPanel.tsx:450-451` mounts both the roll tray and `FateCharacterSheet`). **Fourth attack — the build is red.** `tsc -b` fails — but on `GameBoard-fate-inventory-tab.test.tsx:203`, stash-verified pre-existing, untouched by this diff, and a separate 126-26 follow-up. Vitest (which does not typecheck) is green for everything this diff touches. **Fifth attack — a stressed CI deletes the wrong file.** The diff deletes exactly the two FatePanel test files and nothing else; `git diff --stat` confirms 7 files, 552 deletions concentrated in dead code. Nothing here rises to Critical or High.

### Reviewer (audit)

Tenant isolation audit: **N/A** — frontend cleanup; no trait methods handling tenant data, no structs with tenant fields, no auth surface in the diff. Data flow traced: `FATE_STATE` message → `useStateMirror` → `CharacterPanel.fateSheet` → `FateCharacterSheet` (Character→Stats tab). The deleted `FatePanel` was NOT on this live path — it was the dead dock-tab renderer — so its removal cannot affect the live Fate sheet.

## Reviewer Assessment

**Verdict:** APPROVED

This is a clean, disciplined dead-code-removal + comment-sweep with zero live-path behavior change. 552 deletions concentrated in the unreferenced `FatePanel` function, its two dedicated test files, and its private-only symbols; 20 insertions are all reworded comments. No Critical or High findings.

**Observations (8, no rubber-stamp):**
- `[VERIFIED]` Dead-code deletion is complete and consumer-free — the only live import (`CharacterPanel.tsx:7`) pulls `FateCharacterSheet, FateStunts`, both retained; the deleted `FatePanel` function has no JSX/call/import consumer (preflight grep: 1 named-export import + 9 comment refs).
- `[VERIFIED]` `tsc -b` adds 0 errors from the diff; the single remaining error (`GameBoard-fate-inventory-tab.test.tsx:203`, `'fate'` WidgetId) is pre-existing on develop (stash-verified) and outside the diff.
- `[SEC]` reviewer-security returned clean — the deleted presentational component held no sanitization, perception-firewall, or XSS logic; no info-leak or guard removed. Corroborated by my own trace.
- `[TYPE]` Applied the 13-check TypeScript review checklist myself (type_design disabled): no `as any`/`@ts-ignore`/non-null assertions added; the diff even *removes* a test-only `as unknown as FateStatePayload` double-cast. Remaining `import type` block is correctly type-only. PASS.
- `[DOC]` All 6 reworded comments verified accurate against live code (comment_analyzer disabled): `CharacterPanel.tsx:450-451` confirms the FateDiceTray roll tray + `FateCharacterSheet` mount in the Stats tab; the two `latestFateRoll` consumers are the conflict surface + the Character→Stats roll tray.
- `[MEDIUM][TEST]` Coverage reduction (test_analyzer disabled, self-found): deleting `FatePanel.test.tsx` dropped granular `FateCharacterSheet` assertions (pips/stress/consequences/kind-grouping/version-skew) not replicated in `CharacterPanelFateSheet.test.tsx`. Non-blocking — story mandated the deletion, component code unchanged, core rendering still covered, wiring test intact. Filed as a delivery finding.
- `[SIMPLE]` This change IS a simplification (simplifier disabled): −552 lines of dead code, reduced coupling (FatePanel.tsx no longer imports `FateDiceTray`). No new complexity introduced.
- `[RULE]` No-Dead-Code rule actively advanced; all enumerated rules compliant (see Rule Compliance). `[EDGE]` no new runtime branches or boundary inputs (deletion only). `[SILENT]` no error handling changed; no swallowed errors.

**Data flow traced:** `FATE_STATE` → `useStateMirror` → `CharacterPanel` → `FateCharacterSheet` (Character→Stats tab) — safe because the deleted `FatePanel` was off this live path.
**Pattern observed:** Faithful dead-code removal with cascade cleanup forced by `noUnusedLocals` — `FatePanel.tsx` (deletion + 2 comment rewords).
**Error handling:** Unchanged; degradation guards (`?? []`) live on in `FateCharacterSheet` (`FatePanel.tsx:161-165`).
**Deviations:** Both Dev deviations ACCEPTED (see Reviewer audit); no undocumented deviations.

**Handoff:** To SM (Morpheus) for finish-story.