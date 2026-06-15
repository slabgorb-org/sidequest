---
story_id: "118-2"
jira_key: ""
epic: "118"
workflow: "tdd"
---
# Story 118-2: F3b — Fate panel (read surface)

## Story Details
- **ID:** 118-2
- **Jira Key:** (not configured for this project)
- **Workflow:** tdd
- **Stack Parent:** 118-1 (already merged / complete)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-15T11:31:54Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-15T10:56:34Z | 2026-06-15T10:59:19Z | 2m 45s |
| red | 2026-06-15T10:59:19Z | 2026-06-15T11:13:53Z | 14m 34s |
| green | 2026-06-15T11:13:53Z | 2026-06-15T11:24:28Z | 10m 35s |
| review | 2026-06-15T11:24:28Z | 2026-06-15T11:31:54Z | 7m 26s |
| finish | 2026-06-15T11:31:54Z | - | - |

## Sm Assessment

**Story:** 118-2 — F3b Fate panel (read surface). 5 pts, p2, repo `sidequest-ui`,
workflow `tdd` (phased). No Jira (jira field null) — Jira steps skipped.

**Branch:** `feat/118-2-f3b-fate-panel` (off origin/develop in sidequest-ui).

**Context:** `sprint/context/context-story-118-2.md` carries a concrete technical
approach + 7 derived ACs; epic context at `sprint/context/context-epic-118.md`.

**Scope summary:** Read-only display surface consuming the `FATE_STATE` projection
that shipped in 118-1 (server #880, `build_fate_state_payload`/`_maybe_emit_fate_state`,
ruleset=='fate'-gated). New `FatePanel.tsx` mirrors RelationshipsPanel/QuestsPanel;
`fateState` slice wired into useStateMirror + GameStateProvider; registered in
GameBoard; genre-themed CSS. No server work, no interactive fate actions.

**Handoff to TEA (red phase):** Define failing tests for the 7 ACs in the context.
Critical doctrine to enforce: No-Silent-Fallback on malformed `FATE_STATE` (log, don't
drop), at least one wiring test proving GameBoard registration + real useStateMirror
message path, and player-facing legibility (every number labeled — this is the
Sebastien/Jade mechanics surface).

**Merge gate:** clear (no open UI PRs at setup). Parent 118-1 merged.

## TEA Assessment

**Phase:** finish
**Tests Required:** Yes
**Status:** RED (failing — ready for Dev)

**Test Files (4, all committed `03a2d56`):**
- `src/types/__tests__/fate-protocol.test.ts` — protocol/payload parity (6 tests):
  `MessageType.FATE_STATE` + the 8 nested payload types mirror the server
  (`models.py` FateStatePayload tree / `fate_projection.build_fate_state_payload`).
- `src/hooks/__tests__/useStateMirror.fate.test.ts` — `fateState` mirror slice (7
  tests): null default, populate, snapshot full-replace, and the No-Silent-Fallback
  boundary guard (malformed payload → degrade to null, then a valid one still lands).
- `src/components/__tests__/FatePanel.test.tsx` — component (20 tests): labeled
  fate-point count, skills on the ladder w/ label+numeric incl. a negative rung
  (Terrible -2), aspects grouped by kind with free-invoke pips, four consequence
  slots filled-vs-open, stress boxes, conflict participants by side, empty state,
  ARIA region, version-skew tolerance.
- `src/components/GameBoard/__tests__/GameBoard-fate-tab.test.tsx` — wiring (8
  tests): FateWidget/FatePanel importable, registry `fate` entry **dataGated:true**
  + unique hotkey, end-to-end render through GameBoard, and the epic-required
  **paired negative co-render test** (tab absent when `fateData` null / mid-confrontation).

**Tests Written:** 41 across 4 files, covering all 7 ACs + the epic's ruleset-gate.

**RED verified two ways (honest — ran vitest + tsc directly, not testing-runner):**
- Runtime (`vitest run`): 8 assertion/2 module-resolution failures, every one
  tracing to missing feature code (`MessageType.FATE_STATE` undefined,
  `state.fateState` undefined, `../FatePanel` + `widgets/FateWidget` unresolved).
- Compile (`tsc -b`): all type-level guards fail — 8 missing payload exports,
  missing `FATE_STATE` enum member, missing `ClientGameState.fateState`, both
  missing modules. (The protocol file's 5 typed-literal tests pass at vitest
  runtime — types are erased by esbuild — but are RED under `tsc`; this is the
  documented `quests-protocol.test.ts` compile-time-guard pattern, intentional.)

### Rule Coverage (typescript lang-review checklist)

| Rule | Test(s) | Status |
|------|---------|--------|
| #4 null/undefined handling | slice degrade-to-null (missing/non-array `characters`, non-array `scene_aspects`); panel version-skew "omits optional arrays" | failing |
| #10 input validation at the wire boundary | `useStateMirror.fate` malformed-payload guard (validate before store) | failing |
| #1 type-safety escapes | no `as any`; `as unknown as FateStatePayload` only for deliberately-malformed fixtures (documented, mirrors quests) | n/a (clean) |
| #8 test quality | self-check below; meaningful assertions throughout | n/a (clean) |
| #6 React/JSX list keys | NOT separately pinned — see Delivery Finding (Dev must key aspect/skill/consequence/pip lists on a stable id, not array index) | gap |

**Rules checked:** 4 of ~5 applicable lang-review rules have failing test coverage; #6 (stable list keys) intentionally left to Dev + flagged as a Delivery Finding rather than over-pinned in RED.
**Self-check:** 0 vacuous tests (no `let _ =`, no `assert(true)`, no always-null assertions). The protocol typed-literals assert real values and are compile-time guards.

**Handoff:** To Dev (Agent Smith) for GREEN. Wire chain (server FATE_STATE already
ships from 118-1): protocol enum → payloads types + union → GameStateProvider
slice → useStateMirror handler (boundary guard) → FatePanel → FateWidget →
widgetRegistry (`fate`, dataGated:true, hotkey `f`) → GameBoard availableWidgets
(`if (fateData != null) add("fate")`) + renderWidgetContent case → App.tsx
`fateData={gameState.fateState ?? null}`. The component testids my tests pin:
`fate-empty`, `fate-panel`, `fate-character`, `fate-points`, `fate-skill`,
`fate-aspect`, `fate-pip`, `fate-consequence`, `fate-stress-box` (`data-checked`),
`fate-conflict`.

## Dev Assessment

**Implementation Complete:** Yes
**Tests:** 41/41 passing (GREEN). Full UI suite: 2248/2248 passing (no regressions).
`tsc -b` exit 0. eslint on changed files: 0 errors (2 pre-existing App.tsx warnings,
unrelated to this change).
**Branch:** `feat/118-2-f3b-fate-panel` (pushed, commit after RED `03a2d56`).

**Files Changed:**
- `src/types/protocol.ts` — `MessageType.FATE_STATE`.
- `src/types/payloads.ts` — 8 Fate payload types (FateSkillEntry/FateAspectEntry/
  FateStressBox/FateConsequenceEntry/FateCharacterEntry/FateConflictParticipant/
  FateConflictEntry/FateStatePayload) + `FateStateMessage` in the union.
- `src/providers/GameStateProvider.tsx` — `fateState` slice on ClientGameState +
  `fateState: null` in EMPTY_GAME_STATE.
- `src/hooks/useStateMirror.ts` — FATE_STATE handler with the No-Silent-Fallback
  boundary guard (validate `characters`/`scene_aspects` are arrays → else
  `console.error` + keep prior); always-mirror `fateState` slice.
- `src/components/FatePanel.tsx` (new) — the read surface.
- `src/components/GameBoard/widgets/FateWidget.tsx` (new) — thin adapter.
- `src/components/GameBoard/widgetRegistry.ts` — `fate` WidgetId + entry
  (dataGated:true, hotkey `f`).
- `src/components/GameBoard/GameBoard.tsx` — import, `fateData` prop, availability
  gate (`if (fateData != null) add("fate")`), render case, deps, desktop
  `rightGroupOrder`.
- `src/components/GameBoard/MobileTabView.tsx` — `fate` TAB (Dices icon). **Note:**
  TEA's wire chain didn't enumerate MobileTabView/rightGroupOrder, but the jsdom
  test path renders tabs from MobileTabView's `TABS` filtered by availableWidgets —
  the tab only appears once `fate` is in BOTH. Added to both for desktop/mobile parity.
- `src/App.tsx` — threads `fateData={gameState.fateState ?? null}` into GameBoard.

**TEA delivery findings addressed:**
- Stable React keys — aspects `${kind}-${text}-${i}`, skills `name`, consequences
  `level`, stress `${track}-${i}`, conflict `${name}-${i}` (no bare array-index keys
  on reorderable lists).
- snake_case→display labels — `KIND_LABELS` map renders "High Concept"/"Trouble"/etc.

**Handoff:** To Reviewer (The Merovingian) for review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean (GREEN) | 1 smell (defensive console.error) | confirmed 0, dismissed 1 (legit No-Silent-Fallback guard, matches QUESTS), deferred 0 |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — edge domain covered by Reviewer manual analysis (found conflict.participants gap) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled — silent-failure domain covered manually (boundary guard is loud, verified) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled — test domain covered manually |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled — comment domain covered manually |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled — type domain covered manually |
| 7 | reviewer-security | Yes | findings | 2 (1 MEDIUM free_invokes, 1 LOW sessionStorage) | confirmed 2 (both non-blocking), dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled — simplify domain covered manually |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled — lang-review rule enumeration done manually (see Rule Compliance) |

**All received:** Yes (2 enabled returned; 7 disabled pre-filled per `workflow.reviewer_subagents` settings)
**Total findings:** 3 confirmed (all non-blocking: 2 MEDIUM, 1 LOW), 1 dismissed (preflight console.error — legitimate guard), 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

No Critical or High issues. The feature is correct for all valid payloads, fully
tested (2248/2248 green), wired end-to-end with a real non-test consumer, XSS-safe,
and ruleset-gated exactly as the epic requires. The three confirmed findings are
defense-in-depth against *contract-violating* payloads that the trusted same-project
server never emits — non-blocking by the severity rubric (only Critical/High block).
Logged as hardening delivery findings for an optional fast-follow.

**Data flow traced:** `FATE_STATE` wire message → `useStateMirror.ts:251` boundary
guard (validates `characters`/`scene_aspects` are arrays; `console.error`+`continue`
on malformed) → `fateState` slice → `GameStateProvider` state → `App.tsx:2657`
`fateData={gameState.fateState ?? null}` → `GameBoard` prop → `availableWidgets` gate
(`GameBoard.tsx:394` `if (fateData != null) add("fate")`) → `MobileTabView` TABS /
desktop `rightGroupOrder` → `renderWidgetContent` `case "fate"` (`GameBoard.tsx:574`)
→ `FateWidget` → `FatePanel`. **Safe because** every text node is a React child
(auto-escaped — no XSS); malformed top-level shapes are rejected at the boundary.

**Pattern observed:** Faithful mirror of the QUESTS/RELATIONSHIPS reactive-panel
pattern — snapshot full-replace slice, pure presentational component with empty-state
first, FOLIO genre CSS custom props, thin Widget adapter (`FateWidget.tsx`). The
only intentional divergence (Fate tab `dataGated:true`) is the epic's ruleset gate,
logged as a TEA deviation and audited below.

**Error handling:** `useStateMirror.ts:254` logs loudly and keeps the prior value on
a malformed top-level payload (No-Silent-Fallback). `FatePanel.tsx:127/164-167/147`
guards every character sub-array and `scene_aspects` with `?? []`/`?? {}`
(version-skew tolerance). Gaps: `free_invokes` (numeric, unclamped) and
`conflict.participants` (unguarded) — see findings.

### Observations (dispatch-tagged)

1. `[VERIFIED]` `[SEC]` `[PRE]` **No XSS** — 0 `dangerouslySetInnerHTML`; all
   player/LLM-authored text (`a.text`, `c.text`, `ch.name`, `p.name`, `s.name`,
   `s.ladder`, stress `track`) renders as React text children (auto-escaped).
   Complies with ADR-047 (UI is the escape boundary; server presents text raw) and
   lang-review TS #6. Evidence: `FatePanel.tsx` — every value is in a `{...}` JSX
   slot, never an HTML sink.
2. `[VERIFIED]` `[SILENT]` **Loud boundary guard** — `useStateMirror.ts:251-256`
   validates `Array.isArray(characters) && Array.isArray(scene_aspects)`, else
   `console.error` + `continue` (keeps prior, never stores garbage). Matches the
   QUESTS guard idiom. No swallowed errors anywhere in the diff.
3. `[MEDIUM]` `[SEC]` **`free_invokes` unclamped** at `FatePanel.tsx:104` —
   `Array.from({ length: a.free_invokes })`. A malformed payload with a huge/`Infinity`
   `free_invokes` (passes the array-only boundary guard) would allocate a pathological
   array → tab hang. Non-blocking: server sends small ints; requires a contract
   violation / MitM. Fix: clamp (`Math.min(a.free_invokes ?? 0, N)`) or validate
   `Number.isSafeInteger` at the boundary.
4. `[MEDIUM]` `[EDGE]` **`conflict.participants` unguarded** at `FatePanel.tsx:297` —
   `conflict.participants.map(...)` throws (crashes the GameBoard subtree, caught by
   the ErrorBoundary) if a malformed conflict omits `participants`. Inconsistent with
   the component's own `?? []` defensive style for every other sub-array, and exactly
   the version-skew class TEA wrote a test for (character path only). Non-blocking:
   server always emits a list. Fix: `(conflict.participants ?? []).map`.
5. `[LOW]` `[SEC]` **sessionStorage hydration bypass** at
   `GameStateProvider.tsx:157` — `loadGameStateFromStorage` rehydrates the persisted
   `fateState` with only a `location` typecheck, bypassing the FATE_STATE boundary
   guard. Pre-existing pattern; this diff *extends* the surface by persisting
   `fateState`. Non-blocking.
6. `[VERIFIED]` `[TYPE]` **Payload parity** — `payloads.ts` 8 interfaces mirror
   `models.py` field-for-field (`stress: Record<string, FateStressBox[]>` ==
   `dict[str, list[FateStressBox]]`; `conflict: FateConflictEntry | null`). No
   `as any`; the single `as unknown as FateStatePayload` is the documented
   wire-boundary cast (same as QUESTS). `string` for `kind`/`level`/`side` mirrors
   the server's `str` and sibling payloads (QuestsPayload.status) — consistent, not a
   stringly-typed regression.
7. `[VERIFIED]` `[RULE]` **Wiring complete** — non-test consumer exists
   (`App.tsx:2657`); `fateData` added to BOTH the `availableWidgets` memo deps
   (`GameBoard.tsx:405`) and the `renderWidgetContent` callback deps (`:638`) — no
   stale closure. Ruleset gate (`dataGated:true` + `fateData != null`) realizes the
   epic constraint; the paired negative test proves the tab is absent on non-fate /
   mid-confrontation states.
8. `[VERIFIED]` `[TEST]` **Test quality** — 41 meaningful assertions; covers
   version-skew, malformed-payload degrade, negative ladder rung, and the paired
   negative co-render. Gap (non-blocking): no test for the `free_invokes` /
   `conflict.participants` malformed paths (the new findings).
9. `[VERIFIED]` `[SIMPLE]` **No over-engineering** — `AspectGroups` helper reused for
   character + scene aspects (DRY); component size is proportionate to the six
   legibility surfaces; no dead code, no speculative abstraction.
10. `[VERIFIED]` `[DOC]` **Comments accurate** — reference the correct ADR-144/118-x
    stories; the `useStateMirror` guard comment matches its behavior; widgetRegistry
    `fate` comment correctly explains the dataGated divergence.

### Rule Compliance (typescript lang-review checklist — manual enumeration, rule_checker disabled)

| Rule | Applies to | Verdict |
|------|-----------|---------|
| #1 type-safety escapes | all changed files | PASS — no `as any`/`@ts-ignore`; `as unknown as` only at wire boundary (documented) |
| #2 generic/interface | payloads.ts | PASS — `Record<string, FateStressBox[]>`, no `Record<string, any>` |
| #3 enums | protocol.ts | PASS — const-object MessageType (no TS enum) |
| #4 null/undefined | FatePanel/useStateMirror/GameBoard | PASS for `??` usage; PARTIAL on numeric sanity (`free_invokes`, finding #3) |
| #5 module/declaration | all | PASS — `import type` for all type-only imports |
| #6 React/JSX | FatePanel/GameBoard/MobileTabView | PASS — memo+callback deps updated for `fateData`; stable keys; 0 `dangerouslySetInnerHTML` |
| #8 test quality | 4 test files | PASS — meaningful assertions, no vacuous tests |
| #10 input validation | useStateMirror boundary | PARTIAL — top-level arrays validated; nested numeric/conflict shape not (findings #3/#4) |
| #11 error handling | useStateMirror | PASS — loud `console.error`, no swallow |

### Devil's Advocate

Assume this code is broken. The most exploitable seam is that the boundary guard is
*shallow*: it proves `characters` and `scene_aspects` are arrays, then trusts every
nested field. A malicious or buggy WebSocket server (or a same-origin browser
extension writing sessionStorage) can ship `free_invokes: 1e9` and the pip renderer
at `FatePanel.tsx:104` will try to materialize a billion-element array, freezing the
tab — a client-side DoS that no test covers. Ship a `conflict` of `{active:true}`
with no `participants` key and `:297` throws, collapsing the GameBoard subtree into
the ErrorBoundary; the player loses the board mid-scene. Persist a corrupt `fateState`
to sessionStorage and it reloads straight past the guard. A confused user is less of a
risk here — the tab is ruleset-gated, so non-fate players never see it — but note the
UI does NOT itself enforce Fate/Confrontation mutual exclusion; it trusts the server
to never emit both. If a future server regression emitted `FATE_STATE` during a native
confrontation, both surfaces would co-render, silently violating the epic's invariant
that the paired test only checks at the UI-state level, not as a runtime assertion.
Each of these is real. The mitigating truth: the threat model is a personal-project
localhost server that is the single source of these payloads, the wire fields are
server-derived small integers and always-present lists, and React's auto-escaping
closes the one genuinely dangerous door (XSS from player-authored aspect text). So
the findings are defense-in-depth, not live exploits — but the `free_invokes` clamp
and the `conflict.participants` guard are one-line hardening that would close the two
crash/hang doors and bring the whole component up to the version-skew-tolerance bar it
already sets for itself everywhere else. Recommended as a fast-follow, not a blocker.

**Handoff:** To SM (Morpheus) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): Fate aspect / skill / consequence / free-invoke-pip
  lists must use stable React keys, not the array index (lang-review #6). Affects
  `src/components/FatePanel.tsx` (Dev — key aspects on `text+kind`, skills on `name`,
  consequences on `level`, pips on a stable index-within-aspect). RED does not pin a
  duplicate-content key test; Reviewer should verify keys are stable.
  *Found by TEA during test design.*
- **Improvement** (non-blocking): the server emits aspect `kind` as snake_case
  (`high_concept`/`trouble`/`character`/`situation`/`boost`/`consequence`); the panel
  must map these to display labels. My grouping test matches `/high.?concept/i` so
  either `High Concept` or `high_concept` passes — Dev should render human labels.
  Affects `src/components/FatePanel.tsx`. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): the Fate tab needs entries in BOTH
  `MobileTabView.TABS` and GameBoard's desktop `rightGroupOrder` to render — the
  registry entry + availability gate alone are not enough (a widget is invisible
  in the mobile/jsdom path unless it's in `TABS`). Affects future widget additions
  (the registry/availableWidgets/MobileTabView/rightGroupOrder quartet must move
  together). Documented here so the next widget author wires all four.
  *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): clamp `free_invokes` before `Array.from`. Affects
  `src/components/FatePanel.tsx:104` (use `Math.min(a.free_invokes ?? 0, N)` or
  validate `Number.isSafeInteger` at the useStateMirror boundary) — a malformed
  payload with a huge/`Infinity` `free_invokes` would allocate a pathological array
  and hang the tab. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): guard `conflict.participants`. Affects
  `src/components/FatePanel.tsx:297` (use `(conflict.participants ?? []).map`) — a
  malformed conflict omitting `participants` crashes the GameBoard subtree, contrary
  to the component's own `?? []` defensive style used for every other sub-array.
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking): consider excluding `fateState` from sessionStorage
  persistence (it is re-emitted on reconnect) OR add a shape check in
  `loadGameStateFromStorage`. Affects `src/providers/GameStateProvider.tsx:157` —
  rehydration bypasses the FATE_STATE boundary guard. Pre-existing pattern; this diff
  extends the surface. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Fate tab is data-gated (dataGated:true), not always-present like Quests/Relationships**
  - Spec source: context-story-118-2.md (story title: "mirror RelationshipsPanel/QuestsPanel … register in GameBoard") vs context-epic-118.md
  - Spec text: "Every Fate surface ruleset=='fate'-gated so it never co-renders with the WN/native beat/dial ConfrontationOverlay (paired negative test required)."
  - Implementation: tests pin the `fate` registry entry as `dataGated:true` (appears only when a FATE_STATE projection has arrived), diverging from quests'/relationships' `dataGated:false` always-present pattern. The component still mirrors QuestsPanel structurally.
  - Rationale: epic context (higher authority than the story title's "mirror" verb for tab behavior) requires the ruleset gate; the server only emits FATE_STATE on the 4 Fate packs, so a data-gate is the UI realization that keeps the tab off the 7 WN/native packs and prevents co-render with the ConfrontationOverlay. Satisfies the mandated paired negative test.
  - Severity: minor
  - Forward impact: Dev must gate `available.add("fate")` on `fateData != null` (like `confrontation`/`location`), NOT add it unconditionally like quests.
- **Stress-track rendering is tested though the story title's per-PC enumeration omits it**
  - Spec source: context-story-118-2.md (title) vs context-epic-118.md + server payload
  - Spec text: story enumerates "fate-point count, aspect list …, skills …, consequence slots"; epic lists "stress boxes"; `FateCharacterEntry.stress` ships on the wire.
  - Implementation: added one `fate-stress-box` rendering test (count + checked/unchecked).
  - Rationale: a read-only legibility surface that drops the stress track the payload carries would be incomplete for the mechanics-first players; the epic explicitly lists stress boxes.
  - Severity: minor
  - Forward impact: Dev renders both stress tracks (`physical`/`mental`) with per-box checked state.

### Dev (implementation)
- No deviations from spec. Implemented exactly the wire chain and behaviors the
  RED tests + TEA assessment specified (dataGated:true Fate tab, No-Silent-Fallback
  boundary guard, labeled mechanical surfaces). The only files touched beyond TEA's
  enumerated chain were `MobileTabView.tsx` + `rightGroupOrder` (recorded as a
  Delivery Finding) — necessary wiring to make the registered tab actually render,
  not a spec deviation.

### Reviewer (audit)
- **TEA: Fate tab is data-gated (dataGated:true)** → ✓ ACCEPTED by Reviewer: the
  epic context outranks the story title's "mirror" verb for tab behavior, and a
  data-gate is the only UI realization that satisfies "never co-renders with the
  ConfrontationOverlay." Verified implemented at `GameBoard.tsx:394` + registry
  `dataGated:true`, and proven by the paired negative test.
- **TEA: Stress-track rendering tested though the story title omits it** → ✓ ACCEPTED
  by Reviewer: stress is on the wire (`FateCharacterEntry.stress`) and the epic lists
  stress boxes; a read surface dropping it would be incomplete. Rendered at
  `FatePanel.tsx:223-261`, sound.
- **Dev: "No deviations" (MobileTabView/rightGroupOrder additions)** → ✓ ACCEPTED by
  Reviewer: agrees these are necessary wiring (a widget is invisible in the
  mobile/jsdom path without a `TABS` entry), not a spec deviation. Correctly logged
  as a Delivery Finding for future widget authors.
- No undocumented deviations found. The implementation matches the RED test contract
  and the logged deviations cover every divergence from the story title.