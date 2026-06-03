---
story_id: "83-1"
jira_key: ""
epic: "83"
workflow: "tdd"
---
# Story 83-1: Rebuild ConnectScreen as the Standing Folio lobby — genre accordion + cinematic preview

## Story Details
- **ID:** 83-1
- **Jira Key:** (not applicable — personal project, no Jira)
- **Workflow:** tdd
- **Stack Parent:** none

> NOTE: This session file was reconstructed by Dev on 2026-06-03 after the
> `testing-runner` subagent overwrote it with a test report (known hazard —
> testing-runner can clobber `.session/<id>-session.md`). All phase
> assessments, deviations, findings, and the Subagent Results table below were
> restored verbatim from the in-flight workflow context. Phase history is
> accurate through the green rework (round-trip 1).

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-03T20:05:20Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-03T18:55:33Z | 2026-06-03T18:57:43Z | 2m 10s |
| red | 2026-06-03T18:57:43Z | 2026-06-03T19:12:32Z | 14m 49s |
| green | 2026-06-03T19:12:32Z | 2026-06-03T19:33:03Z | 20m 31s |
| spec-check | 2026-06-03T19:33:03Z | 2026-06-03T19:35:08Z | 2m 5s |
| verify | 2026-06-03T19:35:08Z | 2026-06-03T19:40:57Z | 5m 49s |
| review | 2026-06-03T19:40:57Z | 2026-06-03T19:50:03Z | 9m 6s |
| green | 2026-06-03T19:50:03Z | 2026-06-03T19:58:17Z | 8m 14s |
| spec-check | 2026-06-03T19:58:17Z | 2026-06-03T19:59:02Z | 45s |
| verify | 2026-06-03T19:59:02Z | 2026-06-03T19:59:48Z | 46s |
| review | 2026-06-03T19:59:48Z | 2026-06-03T20:04:08Z | 4m 20s |
| spec-reconcile | 2026-06-03T20:04:08Z | 2026-06-03T20:05:20Z | 1m 12s |
| finish | 2026-06-03T20:05:20Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)

- **Question** (non-blocking): The redesign gates the pack-scoped Rules link behind world selection (it moved off the genre headers into the commit row). This is a discoverability regression vs ADR-135 ("reference pages are a public table tool"). Affects `sidequest-ui/src/screens/ConnectScreen.tsx` + `WorldPreview.tsx` (where Rules/Lore now render). Reviewer/Keith should confirm gating Rules on selection is acceptable, or ask Dev to expose a pack-Rules affordance without requiring a world pick. *Found by TEA during test design.*
- **Gap** (non-blocking): sm-setup wrote the story context to `.session/83-1-context.md` instead of the path the context gate validates (`sprint/context/context-story-83-1.md`), so the TEA context gate failed on entry. TEA recovered by authoring `sprint/context/context-story-83-1.md`. Affects the sm-setup setup-mode flow (recurring — see prior 75-4/75-6). *Found by TEA during test design.*
- **Improvement** (non-blocking): AC8's responsive breakpoints, hidden-scrollbar, and reduced-motion (no opacity:0-stuck nodes) are not assertable in jsdom and are deferred to manual Reviewer verification against the design HTML. Affects the review phase for 83-1. Reviewer should open the lobby at ≤880px and ≤560px and with `prefers-reduced-motion` to confirm. *Found by TEA during test design.*

### Dev (implementation)

- **Improvement** (non-blocking): The design wordmark uses Pirata One; the implementation falls back to the house heading serif because the app dropped Google Fonts for self-hosted faces and no Pirata One `.ttf` ships in the handoff bundle. Affects `sidequest-ui/src/styles/lobby-folio.css` (`.lobby-wordmark`). A follow-up should self-host Pirata One (or pick a display face) to match the masthead. *Found by Dev during implementation.*
- **Resolved (informational)**: AC8 reduced-motion "no opacity:0-stuck nodes" is satisfied by construction — the folio adds NO entrance animation that starts hidden (the exact bug the designer hit in the prototype); all content is visible at its end-state by default. Responsive breakpoints + hidden-scrollbar still warrant the manual Reviewer pass TEA flagged. *Found by Dev during implementation.*
- **Process** (non-blocking): During the green rework the `testing-runner` subagent overwrote this session file with a test report, destroying all phase assessments. Dev reconstructed it from context. Affects the testing-runner subagent / the workflow's use of it — it should never write to `.session/<id>-session.md`. Recurring hazard worth a guard. *Found by Dev during implementation (rework).*

### Reviewer (code review)

- **Improvement** (non-blocking): Three swallowed-catch sites in the lobby log nothing, conflicting with the "No Silent Fallbacks / fail loudly" rule — `/dev/scenes` fetch catch, `loadSavedState` JSON-parse catch, `saveState` write catch (all `sidequest-ui/src/screens/ConnectScreen.tsx`). All three are preserved verbatim from the pre-redesign lobby (not introduced by 83-1) and are non-fatal; a `console.warn` in each would satisfy the rule. Candidate for a small follow-up (could fold into the localStorage-helper tech-debt story TEA already proposed). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `effectiveOpenGenre` can resolve to a `genreSlug` absent from `accordionGenres` for a single render when a previously-selected world's pack was removed from the catalogue (and in the `handleSelectHistory` legacy-prefill path), producing a one-frame all-collapsed accordion before the stale-clear effect self-corrects. Affects `sidequest-ui/src/screens/ConnectScreen.tsx` (effectiveOpenGenre derivation) — cheap guard: `accordionGenres.some(g => g.slug === genreSlug) ? genreSlug : firstGenreSlug`. Rare/transient; defer unless it surfaces in playtest. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The AC7 accent test couples to the `.lobby-folio` CSS classname rather than a stable testid; a class rename would silently break it. Affects `sidequest-ui/src/screens/__tests__/ConnectScreen.folio.test.tsx` (AC7 test) + `ConnectScreen.tsx:401`. Optional hardening: add `data-testid="lobby-accent-root"` to the outer wrapper and query that. Recorded at re-review; not worth a round-trip. *Found by Reviewer during code review (re-review).*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)

- **Rules/Lore reference links relocated from genre headers to the selection-contextual preview/commit row**
  - Spec source: context-story-83-1.md (AC5, Visual Constraints); supersedes story 80-1 surface / ADR-135
  - Spec text: story 80-1 placed a pack-scoped Rules link on every genre header, reachable WITHOUT selecting a world (ADR-135 — "reference pages are a public table tool"). `ConnectScreen.reference.test.tsx` previously asserted "Rules on each genre header, no world selection needed."
  - Implementation: tests now require Rules (pack-scoped → `/reference/rules/{genre}`) and Lore (world-scoped → `/reference/lore/{genre}/{world}`) in the preview/commit row, contextual to the SELECTED world. Rules is no longer present before a world is picked.
  - Rationale: the locked design (Direction A) is a single-open accordion of collapsed genre headers with no room for per-header links; the design places Rules/Lore in the commit row. Per the spec-authority hierarchy, the locked story design outranks the prior ADR-135 lobby surface.
  - Severity: minor
  - Forward impact: Rules discoverability is now gated on world selection — see the matching Delivery Finding (Question) for Reviewer/Keith to confirm acceptable vs ADR-135.

- **Default-open accordion genre when no world is selected**
  - Spec source: context-story-83-1.md (Interaction Patterns)
  - Spec text: "the genre holding the currently selected world is open by default on load." The design prototype always has a default-selected world, so it never specifies the no-selection case.
  - Implementation: tests pin that with NO selection the FIRST genre in render order is open (so a world stays reachable in one fewer click and the index never reads as fully empty).
  - Rationale: our real lobby starts with no selection (unlike the prototype); leaving every genre collapsed would make the index feel empty and add a click. Faithful to the design's "always something open" intent.
  - Severity: minor
  - Forward impact: none — Dev may revisit which genre opens, but the suite assumes first-open for the no-selection path.

- **AC8 responsive / scrollbar / reduced-motion left to manual Reviewer verification (test omission)**
  - Spec source: context-story-83-1.md (AC8, Accessibility/Visual)
  - Spec text: single-column folio + two-up index at ≤880px; stacked commit row + full-width Start at ≤560px; global scrollbars hidden; reduced-motion transform-only with a visible end-state (no opacity:0-stuck nodes).
  - Implementation: NOT unit-tested in Vitest/jsdom — jsdom has no layout engine, does not evaluate media queries, and does not run CSS animation clocks; asserting Tailwind class strings would be brittle implementation-coupling. Covered indirectly: a no-stub `a[href="#"]===0` guard and "old flat `World` radiogroup removed" assertion prove the scroll-list was replaced.
  - Rationale: these are pixel/layout/animation concerns the medium can't assert; over-specifying classnames would lock Dev into a brittle DOM.
  - Severity: minor
  - Forward impact: Reviewer must manually verify responsive breakpoints + reduced-motion against `design-reference/lobby-standing-folio/project/SideQuest Lobby.html` — captured as a Delivery Finding.

- **Start-button copy asserted loosely (regex) rather than exact string**
  - Spec source: context-story-83-1.md (AC5)
  - Spec text: AC5 says the MP label is "Start or Join"; existing code ships "Start or Join Adventure".
  - Implementation: tests assert solo `/^start adventure$/i` and MP `/join/i` (substring) instead of an exact MP string, so either "Start or Join" or "Start or Join Adventure" passes.
  - Rationale: avoids churning a copy decision that the design did not firmly settle; the meaningful contract is "label changes with mode and signals join in MP."
  - Severity: trivial
  - Forward impact: none.

### Dev (implementation)

- **Dropped the alphabetical genre sort — genres render in server (insertion) order**
  - Spec source: story 80-1 (prior lobby) / context-story-83-1.md (Interaction Patterns)
  - Spec text: story 80-1 sorted the genre groups alphabetically by label.
  - Implementation: genres render in `/api/genres` insertion order (no sort), so the first genre is a deterministic default-open target.
  - Rationale: the design uses a curated genre order, and the default-open accordion rule needs a stable "first" genre; alphabetising would open the wrong section. Matches TEA's contract (selected-genre, else first-in-render-order, open by default).
  - Severity: minor
  - Forward impact: genre display order now reflects server order; a curated order is the server/pack's responsibility.

- **Removed the wrapping `<form>` (Enter-to-submit) from the lobby**
  - Spec source: prior ConnectScreen implementation
  - Spec text: the old lobby wrapped its controls in `<form onSubmit>` so pressing Enter in the name field started the game.
  - Implementation: the folio has no form; Start is a button `onClick`. Enter in the name field no longer submits.
  - Rationale: the design's commit row is a discrete Start button and the below-the-fold sections don't belong inside a form; no AC/test requires Enter-to-submit.
  - Severity: trivial
  - Forward impact: none — an `onKeyDown` Enter handler can be re-added if desired.

- **Wordmark uses the house heading serif, not the design's Pirata One**
  - Spec source: context-story-83-1.md (Visual Constraints)
  - Spec text: type — Pirata One (display/masthead).
  - Implementation: `.lobby-wordmark` falls back to `var(--font-heading)` (Baskerville/serif); Pirata One is not wired.
  - Rationale: the app deliberately dropped Google Fonts for self-hosted faces (index.css, 2026-06-03) and the handoff bundle ships no Pirata One `.ttf`; reintroducing a Google Fonts link would contradict that decision.
  - Severity: minor
  - Forward impact: a follow-up should self-host Pirata One (or an alternative display face) — Delivery Finding logged.

- **Updated `character-creation-wiring` connectPlayer helper to the accordion contract**
  - Spec source: the redesigned lobby DOM contract (this story)
  - Spec text: the helper drove the lobby via `[role="radio"][data-slug=…]` genre radios + `[role="radiogroup"][aria-label="World"]` — the old OptionList contract this story replaces.
  - Implementation: the helper now expands the `[data-genre]` accordion section and clicks the first world radio in its radiogroup.
  - Rationale: the redesign replaced genre-radios + the flat "World" radiogroup with the accordion; the helper's intent (reach CharacterCreation) is preserved — only the lobby-navigation mechanics changed. Caught as a regression during the full-suite GREEN check and fixed.
  - Severity: minor
  - Forward impact: none — CharacterCreation coverage preserved (16/16 green).

### Reviewer (audit)

All TEA and Dev deviations reviewed and stamped:

- **TEA: Rules/Lore relocated to selection-contextual commit row** → ✓ ACCEPTED: follows the locked Direction A; the open ADR-135 discoverability question is correctly raised as a Delivery Finding for Keith, not silently buried.
- **TEA: Default-open first genre when none selected** → ✓ ACCEPTED: sensible interaction default; consistent with the design's "always something open" intent.
- **TEA: AC8 responsive/scrollbar/reduced-motion not unit-tested** → ✓ ACCEPTED: jsdom genuinely cannot assert layout/media-queries/animation; deferring to a manual Reviewer pass is the correct call (and reduced-motion is satisfied by construction — no hidden-start entrance animation).
- **TEA: Start-button copy asserted with regex not exact string** → ✓ ACCEPTED: the meaningful contract (mode-driven label, "join" in MP) is preserved; exact copy was never settled by the design.
- **Dev: Dropped alphabetical genre sort → server insertion order** → ✓ ACCEPTED: required for a deterministic default-open target and matches the design's curated ordering. (Stale in-test comments since corrected in the rework.)
- **Dev: Removed the wrapping `<form>` (Enter-to-submit)** → ✓ ACCEPTED: the commit-row Start button is the designed action; minor UX loss is acceptable and trivially restorable.
- **Dev: Wordmark uses house serif, not Pirata One** → ✓ ACCEPTED: honours the repo's self-hosted-fonts decision; correctly logged as a follow-up Delivery Finding.
- **Dev: Updated `character-creation-wiring` connectPlayer helper** → ✓ ACCEPTED: the old contract was replaced by the redesign; intent preserved, regression caught + fixed.

**Undocumented spec deviations:** None found. The AC7 vacuous test was a test-quality defect (basis for the rejection), not an unlogged spec deviation — fixed in the green rework.

### Architect (reconcile)

**Context loaded:** story context `sprint/context/context-story-83-1.md` (9 ACs, guardrails); epic context `sprint/epic-83.yaml` (epic 83 — Lobby Redesign: The Standing Folio); PRD/design source `sidequest-content`? — N/A: the authoritative spec is the Claude Design handoff bundle committed at `sidequest-ui/design-reference/lobby-standing-folio/` (chat transcript = intent, `SideQuest Lobby.html` + `tokens.css` = visual target). No sibling stories in epic 83 (83-1 is the only story). In-flight deviation logs: 4 TEA + 4 Dev entries reviewed.

**Existing entries verified (6-field accuracy):**
- All four TEA deviations and all four Dev deviations carry the full 6 fields (description, spec source, spec text, implementation, rationale, severity, forward impact), reference real artifacts (context-story-83-1.md, story 80-1, ADR-135, the design bundle), and accurately describe what the code does. The Reviewer audit stamped each ACCEPTED. No field is placeholder. No corrections needed.

**Additional deviations found during reconcile:**

- No additional deviations found. Independent re-read of the full diff against the 9 ACs and the design bundle surfaced nothing the TEA/Dev/Reviewer logs missed. Specifically checked and cleared as NON-deviations: (a) the `lobby-world-count` eyebrow renders "{N} worlds across {M} genres" — matches AC2 verbatim; (b) the design-reference bundle committed under `sidequest-ui/design-reference/` is intentional reference material per the story scope, not a code deviation; (c) the per-genre gradient `genreArt.HOUSE` fallback is a documented presentation default (genreArt.ts JSDoc), not an undocumented behavior change; (d) the AC7 test-classname-coupling raised at re-review is a test-robustness nit (logged as a Delivery Finding), not a spec deviation.

**AC deferral verification:** No-op — no ACs were deferred or descoped. All 9 ACs are DONE in code; AC8's responsive/scrollbar/reduced-motion sub-items are implemented but their *automated verification* was deferred to a manual Reviewer pass (a test-coverage deferral, logged as a TEA deviation + Delivery Finding — not an AC deferral). Reviewer findings did not invalidate any AC.

**Manifest status:** Complete. Every spec divergence in this story is logged and Reviewer-accepted; nothing slips through undocumented.

## Sm Assessment

**Routing:** setup → red. Handed to TEA (red phase).

**What this is:** From-scratch visual + structural redesign of the lobby from a Claude Design handoff. User locked in **Direction A — "The Standing Folio."** Reference bundle committed at `sidequest-ui/design-reference/lobby-standing-folio/`.

**Scope guardrails:** structural + visual only; reuse existing wiring (ConnectScreen + lobby/* + `/api/genres`); ignore the prototype's 20 invented worlds; hero art stays CSS-gradient placeholders; personal project — no Jira.

**ACs:** 9 ACs in `sprint/epic-83.yaml` (83-1) and `sprint/context/context-story-83-1.md`.

## TEA Assessment (red)

**Tests Required:** Yes — rich interactive UI behaviour, not a chore bypass.

**Test Files:** rewrote `ConnectScreen.test.tsx` (accordion + preserved 2026-04 past-journey regressions) and `ConnectScreen.reference.test.tsx` (commit-row Rules/Lore); added `ConnectScreen.folio.test.tsx` (masthead/eyebrow/preview/fallbacks/accent/scene-library) and `lobby-folio-wiring.test.tsx` (App-route mount).

**Tests Written:** 48 across 4 files covering all 9 ACs. **Status at red:** RED — 17 failing (new structure), 31 preserved-behaviour passing. Verified by testing-runner (RUN_ID 83-1-tea-red): all failures legitimate structural assertion failures, zero authoring bugs.

**Contract test-hooks documented for Dev:** name input keeps both visible label + `aria-label="Player name"`; masthead heading "SideQuest"; genre headers = `aria-expanded` buttons, single-open, default-open selected/first genre; per-genre `role=radiogroup` "{Genre} worlds" with `aria-checked` world radios; testids `lobby-folio`, `lobby-world-count`, `lobby-hero`, keep `lobby-start-button`; `[data-genre]` accent on a container; Rules `/reference/rules/{genre}` + Lore `/reference/lore/{genre}/{world}` on selection, no `href="#"`; Start label solo "Start Adventure" / MP contains "Join".

**Rule Coverage:** all applicable TS/React lang-review checks covered or enforced by query design. Self-check: 0 vacuous assertions at red.

**Handoff:** To Dev for GREEN.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `src/screens/ConnectScreen.tsx` — rebuilt into the Standing Folio (masthead, folio card = accordion index + cinematic preview, commit row, below-the-fold). Insertion-order genres; default-open first/selected genre; `data-genre` accent on `.lobby-folio` root; `lobby-folio` + `lobby-world-count` testids. All prior handlers/effects preserved verbatim.
- `src/screens/lobby/GenreAccordion.tsx` — NEW single-open accordion (aria-expanded headers; per-genre `role=radiogroup`; aria-checked radios; per-row `data-genre`).
- `src/screens/lobby/genreArt.ts` — NEW per-genre accent + CSS-gradient hero placeholder; documented HOUSE fallback.
- `src/screens/lobby/WorldPreview.tsx` — added `genreSlug` prop, `lobby-hero` wrapper, genre placard, per-genre gradient, card `data-genre`; kept `world-hero-frame` + all image-state behaviour.
- `src/screens/lobby/ModePicker.tsx` — comment refresh.
- `src/styles/lobby-folio.css` — NEW scoped folio presentation; imported by `src/index.css`.
- `src/screens/lobby/OptionList.tsx` + its test — REMOVED (dead after redesign).
- `src/__tests__/character-creation-wiring.test.tsx` — connectPlayer helper updated to the accordion contract.

**Tests (at first green):** story target 48/48; full UI suite 1751/1751; typecheck + lint clean. **Branch:** `feat/83-1-lobby-standing-folio` (pushed).

**AC coverage:** AC1–AC7, AC9 ✓; AC8 motion satisfied by construction, responsive/scrollbar deferred to manual review.

**Handoff:** To spec-check.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned (locked design faithfully implemented). **Mismatches:** 3 — all pre-logged deviations, none requiring hand-back.
- Rules gated on selection → A (update spec; ADR-135 question raised for Keith).
- Insertion-order genres → A (matches design ordering).
- AC8 responsive/motion not unit-asserted → C/D (manual review).

**Decision:** Proceed to review. New surface (GenreAccordion, genreArt) replaces the deleted OptionList rather than duplicating it; everything else reuses existing infra.

## TEA Assessment (verify)

**Phase:** finish **Status:** GREEN confirmed.

### Simplify Report
**Teammates:** reuse, quality, efficiency. **Files Analyzed:** 5.
| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 7 findings | localStorage boilerplate + composite-slug parsing (high); prettify/AccentButton/SelectableRow/useAccordionState (med/low) |
| simplify-quality | clean | — |
| simplify-efficiency | 2 findings | duplicated open-genre fallback chain (high); three-valued openGenre state (medium) |

**Applied:** 1 high-confidence fix — `handleToggleGenre` reused `effectiveOpenGenre` (removed duplicated fallback). **Rejected:** three-valued `openGenre` state (the `undefined` sentinel is load-bearing for async genres). **Deferred:** localStorage helper + slugUtils (pre-existing, cross-module — tech-debt finding). **Reverted:** 0.

**Overall:** simplify: applied 1 fix. **Quality Checks:** regression 65/65 + tsc clean. **Handoff:** To Reviewer.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 errors (1751 tests pass, tsc clean, 2 pre-existing App.tsx lint warns) | confirmed 0, dismissed 0 |
| 2 | reviewer-edge-hunter | Yes | findings | 10 (2 medium, 8 low) | confirmed 2 (non-blocking), dismissed 0, deferred 8 |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 4 (pre-existing swallowed-catch patterns) | confirmed 3 (non-blocking), dismissed 1 (out-of-diff App.tsx) |
| 4 | reviewer-test-analyzer | Yes | findings | 8 (2 high, 6 medium) | confirmed 1 BLOCKING + 4 minor, dismissed 1 (router misread), deferred 2 |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | clean | 0 | confirmed 0 — relative hrefs/History-API nav/static CSS map, no XSS/secrets |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (5 enabled returned, 4 disabled via settings)
**Total findings:** 1 confirmed blocking (since fixed), 8 confirmed non-blocking, 2 dismissed, 10 deferred

## Reviewer Assessment

**Verdict:** REJECTED (round-trip 1) → resolved in green rework.

Production code correct across all 9 ACs; security clean; 1751 tests green. Blocker: the **AC7 accent-shift test was vacuous** — it asserted the accordion's static per-row `data-genre` (always present) instead of the `.lobby-folio` root's selection-driven `data-genre` (ConnectScreen.tsx:403), so it would stay green even if the accent shift were removed. Matches the non-dismissable "meaningful assertions" rule.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] [TEST] | AC7 accent test vacuous — asserts always-present accordion-row data-genre, not the selection-driven lobby root | `ConnectScreen.folio.test.tsx` (AC7 test) | Assert `.lobby-folio` root data-genre flips on selection (prod already correct) |

Bundled minor [TEST]/[DOC] fixes: assert initial aria-expanded values; add collapse-path test; positive scene-library-empty assert; empty-hero test; fix stale "sorts" comments.

**Dispatch tags:** [EDGE] 2 non-blocking · [SILENT] 3 non-blocking (pre-existing) · [TEST] 1 blocking + 4 minor + 1 dismissed · [SEC] clean · [DOC] inline (1 comment nit) · [TYPE] inline (compliant) · [SIMPLE] handled in verify · [RULE] inline (compliant except #8 test quality).

**Rule Compliance (TypeScript lang-review):** #1 type-safety (justified `as CSSProperties`, guarded non-null) ✓ · #2 generics ✓ · #4 nullish ✓ · #5 type imports ✓ · #6 React keys/effects ✓ · #7 async ✓ · #8 test quality VIOLATION (AC7 vacuous — basis for rejection) · #10 input validation ✓ · #11 error handling (pre-existing silent catches, Low).

**Handoff:** Back to Dev for test-only rework (review → green, round-trip 1).

## Dev Assessment (green rework — round-trip 1)

**Rework Complete:** Yes (test-only; no production change).

**Files Changed:**
- `src/screens/__tests__/ConnectScreen.folio.test.tsx` — AC7 test now asserts the `.lobby-folio` root carries no `data-genre` before selection, then flips to `tea_and_murder` → `road_warrior` as worlds are picked (gates on selection, fails if the accent shift breaks). Added an empty-state test (no `lobby-hero` + "choose a world" copy before selection). Scene-library-empty now positively asserts the section heading is mounted. Fixed the stale "sorts before" comment (insertion order).
- `src/screens/__tests__/ConnectScreen.test.tsx` — accordion-structure test now asserts initial `aria-expanded` values ("true"/"false"); added a collapse-path test (toggling the open genre shut hides its worlds + flips aria-expanded). Fixed the stale "sorts first" comment.

**Tests:** full UI suite **1753/1753** (2 new tests); the 6 targeted files 67/67; typecheck clean. **Branch:** `feat/83-1-lobby-standing-folio` (pushed, commit 7b5c207).

**Reviewer findings addressed:** the blocking AC7 vacuous-test finding is fixed; all 4 bundled minor [TEST]/[DOC] items done. The non-blocking findings (silent catches, transient stale-genre collapse) remain as Delivery Findings for a follow-up per the Reviewer's own routing.

**Handoff:** To spec-check / verify / review (rework re-validation).
## Architect Assessment (spec-check — round-trip 1 re-validation)

**Spec Alignment:** Aligned (unchanged).
**Mismatches Found:** None new.

The Reviewer rework was **test-only** — `ConnectScreen.folio.test.tsx` + `ConnectScreen.test.tsx` assertions tightened (AC7 root-data-genre, aria-expanded values, collapse-path, empty-hero, scene-empty positive) plus stale-comment fixes. No production source changed, so the spec-vs-code alignment from my first spec-check stands: all 9 ACs implemented, the three logged deviations (Rules-on-selection, insertion-order genres, AC8 manual-review) remain Accepted. The AC7 test fix actually *strengthens* spec fidelity — the per-genre accent AC is now genuinely guarded.

**Decision:** Proceed to verify. Elegant survives; the tightened test now fails if the accent shift breaks, which is exactly what AC7 needs.
## TEA Assessment (verify — round-trip 1 re-pass)

**Phase:** finish (re-pass). **Status:** GREEN confirmed.

### Simplify Report
**Skipped — no production code changes in the rework.** The round-trip-1 delta (commit 7b5c207) is test-only (`ConnectScreen.folio.test.tsx`, `ConnectScreen.test.tsx`); the production source was untouched and already passed the first verify pass (1 simplify fix applied then). Per the verify workflow, simplify is skipped when no changed code files remain.

**Teammates:** n/a (no production diff) · **Files Analyzed:** 0 · **Applied:** 0 · **Reverted:** 0
**Overall:** simplify: clean (skipped — test-only rework)

**Quality Checks:** Full UI suite 1753/1753 + `tsc --noEmit` clean, verified by the Dev green-rework testing-runner (RUN_ID 83-1-dev-green-rework) on the committed rework.

**Handoff:** To Reviewer for re-review of the AC7 fix.
## Subagent Results (re-review — round-trip 1)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 errors (1753 tests pass, tsc clean, lint 0 err / 2 pre-existing App.tsx warns) | confirmed 0 |
| 2 | reviewer-edge-hunter | Yes (carried) | n/a | production byte-identical to first review — prior result stands (10 deferred/low, none blocking) | carried forward |
| 3 | reviewer-silent-failure-hunter | Yes (carried) | n/a | production unchanged — prior result stands (3 non-blocking, pre-existing) | carried forward |
| 4 | reviewer-test-analyzer | Yes | findings | 2 minor (1 low classname-coupling, 1 medium async-anchor → verified safe) | confirmed 1 low (non-blocking), dismissed 1 (verified) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes (carried) | clean | production unchanged — prior clean result stands | carried forward |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (preflight + test-analyzer re-run on the test delta; edge/silent/security carried forward — production code is byte-identical to the first review; 4 disabled via settings)
**Total findings:** 0 confirmed blocking, 1 confirmed non-blocking, 1 dismissed (verified safe)

## Reviewer Assessment (re-review — round-trip 1)

**Verdict:** APPROVED

The single blocking finding from round-trip 0 — the vacuous AC7 accent test — is **resolved**. I independently verified the fix and confirmed it via reviewer-test-analyzer: the AC7 test now queries the `.lobby-folio` root (not the accordion's always-present per-row `data-genre`), asserts no `data-genre` before selection, then `tea_and_murder` → `road_warrior` as worlds are picked. Removing `data-genre={genreSlug}` from ConnectScreen.tsx:403 would now fail assertion (2) — the test genuinely guards AC7. The bundled items (empty-state hero absence, collapse-path, aria-expanded true/false, scene-empty positive assert, insertion-order comment fixes) are all meaningful, correctly assert their target, and introduce no new vacuous assertions.

**Data flow traced:** world radio click → `handleSelectWorld` sets `genreSlug`/`worldSlug` → `.lobby-folio` root `data-genre={genreSlug}` → tokens.css accent (AC7), now test-guarded.
**Pattern observed:** test asserts the selection-driven attribute on the accent-bearing element — correct gating.
**Error handling:** unchanged from approved production (preflight green, no new smells).

### Re-review findings (non-blocking)
- [LOW] [TEST] AC7 test couples to the `.lobby-folio` classname rather than a testid. Assertion logic is sound; a class rename would silently break it. Optional hardening: add `data-testid="lobby-accent-root"` to the outer wrapper (ConnectScreen.tsx:401) and query that. Recorded as a Delivery Finding; not worth another round-trip.
- [DISMISSED] [TEST] async-anchor concern on the AC6 empty-scenes test — DISMISSED with evidence: the Scene Library `<section>` + `<h2>Scene Library</h2>` are rendered UNCONDITIONALLY (ConnectScreen.tsx:570–572); only the scene-button grid is gated on `scenes.length > 0` (line 574). The synchronous heading assertion is therefore safe; the suite confirms it (test green).

### Dispatch tag coverage
[EDGE] carried (production unchanged) · [SILENT] carried (production unchanged) · [TEST] 1 low non-blocking + 1 dismissed; AC7 blocker resolved · [SEC] carried clean · [DOC] disabled — inline (insertion-order comments now correct) · [TYPE] disabled — no type change in delta · [SIMPLE] disabled — TEA verify skip (test-only) · [RULE] disabled — test-quality rule #8 now SATISFIED (the vacuous assertion that violated it is fixed).

### Devil's Advocate (re-review)
Could the fix be a sham that passes without testing AC7? No — I traced it: `container.querySelector(".lobby-folio")` returns the outer wrapper (ConnectScreen.tsx:401), whose `data-genre={genreSlug ?? undefined}` is omitted when `genreSlug` is null and set to the genre on selection. The before-assertion (`not.toHaveAttribute("data-genre")`) and the two after-assertions gate on the selection state-change, so a broken accent (attribute removed, or not updated on selection) fails the test. Could the collapse-path test pass vacuously? No — it asserts `aria-expanded="false"` (value, not presence) AND that the greyhawk radio leaves the DOM. Could the empty-state test be hollow? No — `queryByTestId("lobby-hero")` returning null is meaningful because `lobby-hero` only exists inside WorldPreview's non-empty branch. The remaining classname-coupling nit is brittleness, not correctness. Nothing here warrants blocking.

### Deviation audit (re-review)
No new spec deviations introduced by the test-only rework. The round-trip-0 deviation audit (all TEA + Dev entries stamped ACCEPTED) stands unchanged.

**Handoff:** To SM for finish-story.