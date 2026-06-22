---
story_id: "153-30"
jira_key: ""
epic: "153"
workflow: "trivial"
---
# Story 153-30: [MP-CONFRONTATION-ROSTER-VS-DISPLAY] group allied combatants on one side of the confrontation roster; render vs only across the faction boundary

## Story Details
- **ID:** 153-30
- **Jira Key:** (not applicable — Jira integration disabled)
- **Workflow:** trivial
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-22T09:24:04Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-22T09:08:20Z | 2026-06-22T09:10:43Z | 2m 23s |
| implement | 2026-06-22T09:10:43Z | 2026-06-22T09:19:33Z | 8m 50s |
| review | 2026-06-22T09:19:33Z | 2026-06-22T09:24:04Z | 4m 31s |
| finish | 2026-06-22T09:24:04Z | - | - |

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-ui/src/components/ConfrontationOverlay.tsx` — `StatusLine` now groups
  `data.actors` by the existing `EncounterActor.side` field. Opponents form a "them" camp;
  players + neutrals + legacy/missing-`side` actors form an "us" camp. The single "vs"
  (`data-testid="roster-vs"`) renders only when a genuine player↔opponent boundary exists;
  allies within a side are joined by a muted, `aria-hidden` dot. `ActorChip`, the player-only
  commitment badge, HP/metric bars, and `data.label` are unchanged.
- `sidequest-ui/src/__tests__/confrontation-roster-faction-grouping-153-30.test.tsx` (new) —
  renders the real `ConfrontationOverlay` and asserts on rendered DOM: exactly one "vs" at the
  faction boundary (after both player chips, before the opponent — via `compareDocumentPosition`),
  zero "vs" between allies, single "vs" for 1-PC-vs-1-opponent, zero "vs" for all-same-side and
  for legacy missing-`side` payloads, and all 3 roster chips still render.

**Approach:** Reuse-first per context — no new component, no new data. Grouping reads the same
`side` field `ThemPanel` already consumes. The "us"/"them" split makes missing-`side` collapse
to one no-"vs" group (fails toward "no false opposition", never a wrong "vs").

**Acceptance Criteria:** All 7 met (AC-1 allies no "vs"; AC-2 single boundary "vs"; AC-3
side-driven; AC-4 per-actor behaviors preserved; AC-5 legacy safe; AC-6 single-side no "vs";
AC-7 rendered-DOM wiring test through the real overlay).

**Tests:** 5/5 new GREEN. No regressions: 146/146 confrontation tests, full suite 2552/2552.
Lint clean on changed files. `tsc -b` adds zero new errors (one pre-existing GameBoard "fate"
WidgetId error on `develop` — see Delivery Findings, out of scope).

**OTEL:** none — cosmetic UI grouping change (ui CLAUDE.md: not needed for cosmetic UI).

**Branch:** `feat/153-30-confrontation-roster-vs-faction-boundary` (pushed, base `develop`).

**Handoff:** To review (The Merovingian).

## Sm Assessment

**Story:** 153-30 — [MP-CONFRONTATION-ROSTER-VS-DISPLAY] group allied combatants on one
side of the confrontation roster; render "vs" only across the faction boundary.

**Type / size / workflow:** Bug, 1 point, `trivial` (phased: setup → implement → review →
finish). **Repo:** `sidequest-ui` only (base branch `develop`). No server/wire change.

**What's wrong (from the playtest finding):** The confrontation header roster renders a flat
list of all combatants with "vs" between *every* adjacent pair, so two allied PCs read as if
they oppose each other ("Brann vs Vesna vs The Thing That Learned Your Name"). The separate
"Them" block correctly identifies the real opponent; only the roster join is wrong.

**Fix direction (reuse-first, no new component):** In `ConfrontationOverlay.tsx` the
`StatusLine` sub-component (`:452`) maps `data.actors` and inserts "vs" on the `i > 0` index
test (`:476-497`). Group by the existing `EncounterActor.side` field — the same field the
sibling `ThemPanel` (`:1035`) already consumes — so allies render together (intra-side
separator that is NOT "vs", e.g. a thin dot) and the single "vs" sits only at the
player↔opponent faction boundary. Preserve `ActorChip`, the player-only commitment badge
(`a.side === "player"` gate), HP/metric bars, `data.label`, and `key={a.name}`.

**Edge cases that must hold:** missing/legacy `side` degrades to one no-"vs" group (never a
false adversary boundary); single-side rosters render no "vs"; `neutral` third group handled
without implying opposition.

**Verification:** A component/wiring test renders the real `ConfrontationOverlay`/`StatusLine`
with a 2-player + 1-opponent fixture and asserts on the rendered DOM — exactly one "vs"
between the player group and the opponent, zero "vs" between the two allies. Reuse existing
confrontation fixtures (`__tests__/confrontation-commitment-102-4.test.tsx` already has a
player-side commitment fixture to extend). UI rule: assert on rendered DOM, not source text.

**OTEL:** none — cosmetic UI grouping change, no server subsystem decision (per ui CLAUDE.md).

**Context doc:** Full ACs (7) and code anchors already written at
`sprint/context/context-story-153-30.md` — Agent Smith (Dev) should read it before touching code.

**Routing:** trivial/phased → next agent is **Dev**. No design phase needed; the approach is
settled and reuse-first. Handing off to implement.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement

### Dev (implementation)
- **Gap** (non-blocking): `npm run build` (`tsc -b`) fails on `develop` independent of
  this story — `src/components/GameBoard/__tests__/GameBoard-fate-inventory-tab.test.tsx:203`
  builds a `new Set(["narrative","character","fate"])` but `"fate"` is not in the `WidgetId`
  type (TS2769). Verified pre-existing: the error reproduces with this story's changes
  stashed, and is the *only* `tsc -b` error. This story adds zero new type errors. Affects
  `sidequest-ui` GameBoard fate-inventory widget typing (the `WidgetId` union likely needs
  `"fate"` added, or the test fixture corrected) — out of scope for 153-30 (ConfrontationOverlay
  only). *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (non-blocking): Confirmed Dev's pre-existing GameBoard `WidgetId` "fate" `tsc -b`
  error — independently reproduced (stash-and-rebuild) and it is the only build error;
  unrelated to this diff. Affects `sidequest-ui` GameBoard fate-inventory widget typing —
  worth a tracked follow-up so `npm run build`/CI is green again. *Found by Reviewer during
  code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

### Dev (implementation)
- No deviations from spec.

### Reviewer (audit)
- **"No deviations from spec." (Dev)** → ✓ ACCEPTED by Reviewer: the implementation matches
  the context's reuse-first direction exactly — grouping by the existing `EncounterActor.side`
  field inside `StatusLine` (the same field `ThemPanel` reads), no new component, no new wire
  data, and `ActorChip` + the player-only commitment badge + HP/metric bars + `data.label`
  all preserved unchanged. No undocumented divergence found.
## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (49/49 green, lint clean, 0 new tsc errors) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (assessed by Reviewer) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings (assessed by Reviewer) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings (assessed by Reviewer) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings (assessed by Reviewer) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (assessed by Reviewer) |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (assessed by Reviewer) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings (assessed by Reviewer) |

**All received:** Yes (2 enabled subagents returned — preflight + security; 7 disabled via `workflow.reviewer_subagents`, their domains assessed by Reviewer below)
**Total findings:** 0 confirmed blocking, 0 dismissed, 1 deferred (pre-existing out-of-scope GameBoard `WidgetId` tsc error — non-blocking, logged in Delivery Findings)

## Reviewer Assessment

**Verdict:** APPROVED

A pure presentation change in `ConfrontationOverlay.tsx::StatusLine`: the roster is grouped by
the existing `EncounterActor.side` field so allied PCs render together and the single "vs" sits
only at the genuine player↔opponent boundary (ADR-116). I traced every branch of the grouping
and every edge the ACs name; the implementation is correct, minimal, and reuse-first.

### Data flow traced
`data.actors` (server-delivered, already perception-filtered per ADR-104/105) → `filter(side)` →
`opponentActors` / `alliedActors` → `rosterGroups` → rendered chips. The grouping derives
**only** from `data.actors`; it never unions with another source or re-derives visibility, so it
cannot surface an actor the old flat list hid ([SEC] confirms). The single mutation to the render
is *where* the "vs" goes — not *what* is shown.

### Rule Compliance
- **ui CLAUDE.md "No Silent Fallbacks":** COMPLIANT. Missing/legacy `side` lands in the allied
  bucket and `hasFactionBoundary` requires an explicit `side === "player"`, so an absent `side`
  degrades to one no-"vs" group — a visible safe default ("no false opposition"), never a silent
  wrong "vs". (`ConfrontationOverlay.tsx:471-476`)
- **ui CLAUDE.md "assert on rendered DOM, not source text":** COMPLIANT. The new test renders the
  real `ConfrontationOverlay` and asserts on DOM (`getAllByText("vs")` count + `compareDocumentPosition`
  placement), not on component source.
- **ui CLAUDE.md OTEL "not needed for cosmetic UI":** COMPLIANT. No subsystem decision added; no
  OTEL expected. Correct call.
- **ADR-104/105 perception firewall:** COMPLIANT (renders only `data.actors`; [SEC] verified).
- **ADR-116 "a confrontation requires an Other":** the single "vs" now aligns to exactly the
  player↔Other boundary the ADR guarantees — this change tightens the display to the doctrine.
- **SOUL "Crunch in genre / cosmetic in UI":** no mechanics touched; layout only.

### Observations (tagged by source)
1. `[VERIFIED]` Allies never separated by "vs" — `rosterGroups` puts all non-opponents in one
   group and only the inter-group separator (`gi > 0`) emits "vs"; intra-group uses the
   `aria-hidden` "·". Evidence: `ConfrontationOverlay.tsx:489-528`. Satisfies AC-1.
2. `[VERIFIED]` Exactly one "vs" at the boundary — groups is at most `[allied, opponent]`, so the
   `gi > 0` separator fires once. Evidence: test `getAllByText("vs")` length 1 + placement assertion.
   Satisfies AC-2.
3. `[VERIFIED]` Grouping is side-driven, not array-order — `filter(a.side === "opponent")` vs
   `!== "opponent"`; reorder the input and the camps are unchanged. Satisfies AC-3.
4. `[VERIFIED]` Per-actor behaviors preserved — `ActorChip` and the `committedActors !== null &&
   a.side === "player"` commitment badge are unchanged inside the inner `group.map`; the 102-4
   commitment suite stays green (49/49 incl. it). Evidence: `ConfrontationOverlay.tsx:512-525`.
   Satisfies AC-4.
5. `[VERIFIED]` Legacy/missing `side` is safe — `hasFactionBoundary` is false without an explicit
   player, so an all-missing roster collapses to one no-"vs" group (test 4). Satisfies AC-5.
6. `[VERIFIED]` Single-side roster shows no "vs" — all-player ⇒ `opponentActors` empty ⇒ no
   boundary ⇒ `[data.actors]` one group (test 3). Satisfies AC-6.
7. `[PRE]` Mechanical gates green — preflight: 49/49 tests, eslint clean on both files, zero new
   `tsc` errors (the one error is the pre-existing GameBoard `WidgetId` "fate" issue, out of scope).
8. `[SEC]` Security clean — no new text sink (`a.name` only into `data-*`/`title`, set via
   `setAttribute`, not innerHTML; no `dangerouslySetInnerHTML`); perception firewall intact.
9. `[TEST]` (self-assessed — analyzer disabled) Test quality is strong: drives the real component,
   asserts placement via `compareDocumentPosition` (not just a count), covers 5 distinct rosters
   (multi-ally boundary, 1v1, all-same-side, legacy-missing-side, chip preservation). No vacuous
   assertions, no coupling to internals.
10. `[SIMPLE]` (self-assessed — simplifier disabled) Minimal: two `filter`s + one boolean + a
    ternary; no over-engineering, no dead branches. The two-camp model is the simplest structure
    that satisfies every AC.
11. `[TYPE]` (self-assessed — type-design disabled) `rosterGroups: EncounterActor[][]` is explicitly
    typed; no `any`, no unsafe cast. `actors` is a required `EncounterActor[]`; `data.actors` was
    already dereferenced pre-diff so no new null risk is introduced.
12. `[DOC]` (self-assessed — comment-analyzer disabled) The new block comment is accurate and
    explains the *why* (ADR-116 boundary, missing-side safety); the two inline comments on the
    separators are correct. No stale/misleading docs.
13. `[EDGE]` (self-assessed — edge-hunter disabled) Edges enumerated: empty roster (renders nothing,
    same as before — no crash), all-opponent (no player ⇒ one no-"vs" group), neutral+opponent
    without a player (no boundary ⇒ no false "vs"), multiple opponents (`p vs o1 · o2`, one "vs").
    All behave safely.
14. `[SILENT]` (self-assessed — silent-failure-hunter disabled) No swallowed errors, no empty
    catches, no silent fallback. The missing-`side` path is an explicit, intended branch (fail
    visibly toward "no false opposition"), not a silent default.

### Devil's Advocate
Suppose I want this broken. First attack: feed a roster the server "shouldn't" send — all opponents,
no player. Old code drew `o1 vs o2`; new code, lacking a `side === "player"`, sets
`hasFactionBoundary` false and collapses to a single dot-joined group — so this change actually
*removes* a false "vs" the old code could draw. No regression; an improvement. Second attack: a
neutral bystander seated with players — `Brann · Bystander vs Thing`. The neutral is dot-joined on
the players' side of the boundary; a purist could call that a mild mis-grouping (a neutral isn't a
player ally), but the context explicitly permits "group neutrals alongside players per design," and
the load-bearing rule — "vs" only at a genuine adversary boundary — holds, because a real
player↔opponent boundary exists here. Not a defect. Third attack: duplicate actor names → React key
collision on `key={a.name}`. But that keying predates this diff (the old flat list used the same
key), so it is neither introduced nor in scope. Fourth attack: `data.actors` undefined (ProtocolBase
drops empty lists). Both old and new code dereference `data.actors` identically, and a confrontation
always seats actors (ADR-116) — no new crash surface. Fifth attack: a confused screen-reader user —
the "·" is `aria-hidden` (decorative), the "vs" is read aloud as before; parity with the prior
behavior, no accessibility regression. Sixth: could the commitment badge stop rendering after the
nesting change? No — it is still gated on `a.side === "player"` inside the inner map, and the 102-4
suite (which asserts `commitment-Vesska`/`commitment-Brakka` and the opponent's absence) passes.
Stressing every angle, I cannot manufacture a Critical or High defect. The worst I find is a
defensible neutral-grouping nuance the spec already blesses.

**Pattern observed:** Reuse-first side-grouping mirroring `ThemPanel`'s `a.side` read — good pattern,
single source of truth for the faction boundary. `ConfrontationOverlay.tsx:471` / `:1036`.
**Error handling:** Missing-`side` and single-side rosters handled explicitly toward a safe default
(`ConfrontationOverlay.tsx:474-476`); no swallowed errors.
**Handoff:** To SM (Morpheus) for finish-story.