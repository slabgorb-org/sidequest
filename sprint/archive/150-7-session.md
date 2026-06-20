---
story_id: "150-7"
jira_key: ""
epic: "150"
workflow: "trivial"
---
# Story 150-7: [PLAYTEST] wry_whimsy/gulliver — full-stack verify (fate)

## Story Details
- **ID:** 150-7
- **Jira Key:** (none)
- **Workflow:** trivial
- **Stack Parent:** none
- **Points:** 2
- **Type:** chore

## Overview

Full-stack `/sq-playtest` verification of `wry_whimsy/gulliver` (ruleset: Fate Core, ADR-144).
Run via `/pf-gm` as the playtest DRIVER; bugs routed cross-workspace to FIXER via
`/Users/slabgorb/Projects/sq-playtest-pingpong.md`. Sixth+ Fate world; first wry_whimsy Fate
verify. Gulliver = the sensible-outsider-reshapes-absurd-society spine.

## Acceptance Criteria (from sprint YAML)
- Fate engine engages (FATE_ROLL + fate.* + confrontation.* spans).
- Harm ablates Fate stress/consequences, not core.hp (126-1).
- FATE_STATE hydrates on connect/resume (#942).
- Items become invokable aspects (#945).
- Contest resolves opposed checks (#936).
- Player 4dF is determinative (126-7).
- Native Inventory hidden (126-3).
- Whimsy genre-true narration; if the world hydrates a political layer, witnessed-act
  vocabulary/classification spans fire (double-gated — wry_whimsy Premise/Bloc substrate).

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish

## Known-Going-In
- **`[FATE-CONTEST-NARRATE-CRASH]` (from 150-6) WILL reproduce here.** It is an engine/genre-level
  crash in `narrator.build_encounter_context` (narrator.py:394, a `social_duel` beat with
  `kind=None`), not glenross-specific — any Fate Contest exchange crashes the
  `_narrate_resolved_fate_exchange` seam. So the "Contest resolves opposed checks (#936)" AC will
  hit the same wall until FIXER ships the fix. Drive chargen/health/narration/clue/political-layer
  ACs around it; confirm the contest reproduces the crash (don't re-file — point at the existing
  ping-pong task) and note any gulliver-specific seating/political differences.

## Delivery Findings

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Gap** (non-blocking): server stays stuck in `daemon_unavailable` when the daemon starts AFTER the server — render dispatch + RAG embed/retrieve never recover without a server restart. Affects `sidequest-server` daemon client / ADR-131 liveness (`lore_embedding`/`entity_embedding` workers + `_maybe_dispatch_render`) (needs a reconnect/back-off loop or a loud "daemon down" banner). *Found by Dev during implementation.* (Full repro in ping-pong: `[BUG / DAEMON-NO-RECONNECT]`.)
- **Gap** (non-blocking): a Fate Conflict with an outstanding `pending_defenses` entry does not re-present the ADR-151 DEFEND barrier after a server restart/reconnect (action rack stays disabled on "Committed — waiting…"); recoverable via free-text (narrator resolves out-of-band) but the structured defend is lost and an orphaned `pending_defenses` entry persists post-resolution. Affects `sidequest-server` fate defend re-emit on reconnect + stale-pending cleanup on resolve. *Found by Dev during implementation.* (Ping-pong: `[BUG / FATE-DEFEND-RESUME-WEDGE]`.)
- **Gap** (non-blocking): `npc.recurring_presence_missed` — the active in-scene antagonist ("the Officer") was named in narration but omitted from `npcs_present`. Affects `sidequest-server` narration_apply/presence tracking. *Found by Dev during implementation.*
- **Improvement** (non-blocking): OTEL watcher WS teardown logs `RuntimeError: Cannot call "send" once a close message has been sent` (`server/watcher.py:240`) when a dashboard tab disconnects — benign noise, should guard the send on a closed socket. *Found by Dev during implementation.*
- **Question** (non-blocking): the headline carried fixes #990 (contest-narrate-crash) + #936 (contest commit) could NOT be verified on gulliver — a no-stress Fate Contest never triggers there (genre tone routes to Conflict/narration). Recommend verifying them on `tea_and_murder/glenross` where the Contest fires. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `FatePanel.tsx` `Consequences` (L452) and `FateStunts` (L562) use semantic React keys (`c.level` / `st.name`); a duplicate level or name silently drops a row/card. Affects `sidequest-ui/src/components/FatePanel.tsx` (adopt the index-tiebreaker key the Aspects list already uses, e.g. `` `${c.level}-${i}` ``). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `FatePanel.tsx` lacks guards for protocol-violating edge data — a filled consequence with empty `text` (L497) renders crimson styling + blank label; an empty stress `boxes` array (L396) renders a label with no row; `FatePoints` (L135) has no NaN guard (`Math.max(0, NaN)` → "NaN of NaN"). Affects `sidequest-ui/src/components/FatePanel.tsx` (add finite/empty/filled-text fallbacks). Display-only, low likelihood. *Found by Reviewer during code review.*

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Cherry-picked + merged the Fate character-sheet restyle (work beyond the playtest scope)**
  - Spec source: 150-7 story scope (session file title)
  - Spec text: "[PLAYTEST] wry_whimsy/gulliver — full-stack verify (fate)"
  - Implementation: cherry-picked restyle commit `77649f9c7` onto a clean branch off develop → sidequest-ui PR #443 (merged `cd52fe6`); closed the conflicting #442 as superseded.
  - Rationale: operator (Keith) explicitly requested it mid-playtest ("not seeing expected character-tab changes"); #442 was CONFLICTING (it re-carried already-merged 126-34 commits), so a clean cherry-pick was the correct fix. Verified green (vitest 11/11, tsc clean for the 3 files, eslint clean) before merge.
  - Severity: minor
  - Forward impact: none negative — restyle now on develop; #442 closed.
- **Three ACs not exercisable on gulliver (documented coverage gap, not engine failures)**
  - Spec source: 150-7 Acceptance Criteria
  - Spec text: "Contest resolves opposed checks (#936)"; "Harm ablates Fate stress/consequences, not core.hp (126-1)"; "if the world hydrates a political layer, witnessed-act vocabulary/classification spans fire"
  - Implementation: a true no-stress Fate **Contest** never triggered — gulliver's `high menace` tone routes opposed actions to a Conflict (coercive framing) or plain narration (courteous parley), so `#990/#936` (contest-path) couldn't be verified here; 126-1 confirmed only its invariant (player `core.hp` never moved off 10/10) since no hit net stress onto a track; the captor/shore scene never hydrated a political layer.
  - Rationale: scenario/genre-tone constraints, not engine bugs. The Conflict path of the narrate seam IS verified crash-free.
  - Severity: minor (verification-coverage gap, documented)
  - Forward impact: #990/#936 should be verified on a cosy world (glenross) where the Contest fires — captured as a delivery finding.

### Reviewer (audit)
- **Cherry-picked + merged the Fate character-sheet restyle (beyond playtest scope)** → ✓ ACCEPTED by Reviewer: operator-directed mid-playtest; the clean cherry-pick of `77649f9c7` was the correct response to the CONFLICTING #442 (which re-carried already-merged 126-34 commits). Verified green before merge (vitest 11/11, tsc clean for changed files, eslint clean), security clean, well-commented. Sound.
- **Three ACs not exercisable on gulliver (Contest #990/#936, full 126-1 ablation, political-layer spans)** → ✓ ACCEPTED by Reviewer: honest coverage reporting, not a false pass. The Contest non-trigger is a genuine genre-tone consequence (gulliver `high menace` routes opposed actions to Conflict/narration), correctly escalated as a delivery finding to verify on glenross. The 126-1 invariant (player `core.hp` never moved off 10/10) WAS confirmed; only stress-accumulation observation was gated by roll outcomes. Reasonable.

## Dev Assessment

**Implementation Complete:** Yes — full-stack `/sq-playtest` verification of `wry_whimsy/gulliver` (Fate Core) completed as DRIVER (oq-3); findings routed to FIXER via `~/Projects/sq-playtest-pingpong.md`.

**Files Changed:**
- `sidequest-ui` (PR #443, merged `cd52fe6` → develop) — clean cherry-pick of the Fate character-sheet "Fate Sheet" restyle (`CharacterPanel.tsx`, `FatePanel.tsx`, `GameBoard.tsx`, `CharacterPanelFateSheet.test.tsx`); operator-requested mid-playtest. #442 closed as superseded.
- (No server/content code changes — this is a verification story; engine fixes belong to FIXER.)

**Verification result:** broad slate PASS (Fate engine, #942 hydrate connect/resume/restart, 4dF determinative, ADR-151 defend, items→aspects, 126-3 native-inv-hidden, RENDER-NO-SUBJECT #994 end-to-end [Keith-confirmed], footnotes→known_facts, FP economy, conflict surface, dice readout, Other-seating, narration). Not exercisable on gulliver (documented): #990/#936 Contest path (genre tone → Conflict/narration, verify on glenross), full 126-1 ablation (invariant confirmed: core.hp untouched), political-layer spans. Full scorecard in the ping-pong.

**Tests:** sidequest-ui PR #443 — vitest `CharacterPanelFateSheet` 11/11, `tsc -p tsconfig.app.json` clean for changed files (only the pre-existing `WidgetId` error remains), eslint clean.

**Branch:** restyle merged to develop via PR #443; oq-3 stack fast-forwarded to `cd52fe6`.

**New bugs filed (FIXER, via ping-pong):** DAEMON-NO-RECONNECT (med), FATE-DEFEND-RESUME-WEDGE (low-med), npc.recurring_presence_missed (low), watcher send-on-closed-socket (low). Carried confirms (no re-file): 126-17, 126-7, FATE-STRESS.

**Handoff:** To next phase (trivial workflow → finish/SM).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | tests 11/11 GREEN; tsc clean (only pre-existing WidgetId err); eslint clean; 0 smells | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | Yes | findings | 5 (display-only robustness on edge/malformed server data) | confirmed 5 (all Low, non-blocking), dismissed 0, deferred 0 |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | clean | 0 (all authored strings auto-escaped via JSX; no XSS/eval/injection/leak/secrets) | confirmed 0, dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 5 confirmed (all Low, non-blocking), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

**Scope.** 150-7 is a `[PLAYTEST]` verification story. Two deliverables reviewed: (a) the only code change — the Fate character-sheet restyle, already merged to `develop` via sidequest-ui PR #443 (`cd52fe6`); (b) the playtest verification itself (Dev Assessment + ping-pong findings + deviations). Review diff = `cd52fe6` (FatePanel.tsx +663, CharacterPanel.tsx +51, GameBoard.tsx +4, CharacterPanelFateSheet.test.tsx +67).

**Dispatch tags (subagent coverage):**
- `[EDGE]` — **5 confirmed, all Low/non-blocking** robustness nits in `FatePanel.tsx` (display-only component): (1) `Consequences` keyed by `c.level` (L452) → duplicate-level slots silently drop a row (medium-conf; legal-but-rare in some Fate variants); (2) `FateStunts` keyed by `st.name` (L562) → duplicate-name drops a card (low-conf); (3) filled consequence with empty `text` (L497) renders crimson styling + blank label (medium-conf); (4) empty stress `boxes` array (L396) renders a label with no row (low-conf, cosmetic); (5) `FatePoints` no NaN guard (L135) → "NaN of NaN" on protocol-violating input (low-conf). None crash; none corrupt state. Confirmed as non-blocking improvements → captured as delivery findings for a follow-up hardening pass.
- `[SEC]` — **clean.** Every authored string (aspect text, skill names, stunt name/desc, consequence text, world slug via `toDisplayName()`) reaches the DOM as a JSX text child (React auto-escape); no `dangerouslySetInnerHTML`, no `eval`/`Function`, no content-derived `href`/`url()`, no secrets, no cross-player/GM data leak (component is single-PC-scoped). Evidence-backed.
- `[SILENT]`, `[TEST]`, `[DOC]`, `[TYPE]`, `[SIMPLE]`, `[RULE]` — subagents **disabled** via `workflow.reviewer_subagents`; not run. I covered their domains directly: silent-failure (no swallowed errors in the diff — pure render code), test (preflight confirms 11/11 + the commit added 5 TDD cases: eyebrow content/absence, FP token fill, ladder grouping, read-only invariant), doc (the new code is heavily and accurately commented — see the "READ-ONLY per scope" docblock at FatePanel.tsx:129-134 and the GameBoard worldSlug comment), type (no `as any`/`@ts-ignore`/non-null-assertion in the diff; tsc clean), simplify (the restyle is presentational, no dead code — read-only controls omitted, not rendered-dead, per the No-Stubbing rule), rule (see Rule Compliance below).

**Observations (≥5):**
- `[VERIFIED]` Read-only invariant honored — FatePanel.tsx:129-134 docblock + the diff omit clickable tokens / per-aspect Invoke buttons (not rendered dead); spending still flows through the existing conflict surface (verified: I exercised Invoke/throw via the conflict surface during the playtest). Complies with No-Stubbing / "omit, don't stub dead controls."
- `[VERIFIED]` `FatePoints` index key is compliant — FatePanel.tsx:147-149 `key={i}` is on a *derived fixed-length* token array (`Array.from({length: refresh})`), not a reorderable data list, so TS rule #6 (`key={index}` on reorderable lists) does not apply. Tokens never reorder/insert/delete independently.
- `[VERIFIED]` Falsy-safe FP hint — FatePanel.tsx:138-141 uses `points > 0` (explicit comparison), not `points || …`, so a 0 value is handled correctly (TS rule #4).
- `[EDGE]` `Consequences`/`FateStunts` semantic keys risk silent row-drop on duplicate level/name (FatePanel.tsx:452, 562) — Low, non-blocking; Aspects already use the index-tiebreaker pattern (`${kind}-${a.text}-${i}`) the others should adopt.
- `[VERIFIED]` Wiring intact — GameBoard.tsx:589 passes `worldSlug` → CharacterPanel consumes it only when `fateSheet` is present (the Fate-pack surface); confirmed end-to-end live (the "Gulliver · Fate Core" eyebrow rendered in the playtest).
- `[VERIFIED]` Tests are non-vacuous and wired — CharacterPanelFateSheet.test.tsx asserts real DOM (eyebrow present/absent, FP token `data-filled`, ladder rung grouping, read-only invariant); renders the production component (not a stub). 11/11 GREEN.

**Data flow traced:** server `FateCharacterEntry` (aspects/skills/stunts/stress/consequences/FP) + `world_slug` (from `SESSION_EVENT.body.world_slug`, server-controlled) → `CharacterPanel`/`FatePanel` → JSX text children (auto-escaped) → DOM. Safe: no content reaches `innerHTML`, no content builds URLs, no cross-PC iteration. Confirmed live during the playtest (the sheet rendered the player's own data only).

### Rule Compliance (TypeScript lang-review checklist)
Enumerated against the diff (`.tsx`):
- **#1 Type-safety escapes:** none — no `as any`, `as unknown as`, `@ts-ignore`, or runtime-nullable `!` introduced. ✓
- **#2 Generics/interfaces:** props use concrete interfaces (`FateCharacterEntry`, `CharacterSheetData`); no `Record<string,any>`/`object`/`Function`. ✓
- **#3 Enums:** none introduced. N/A
- **#4 Null/undefined:** FP hint uses `> 0` not `||`; `Math.max(0, refresh)` floors negatives; optional `worldSlug` consumed only when present. ✓ (NaN edge is the [EDGE] Low finding, not a rule violation)
- **#5 Modules:** type-only imports correct; no missing-extension issues introduced. ✓
- **#6 React/JSX:** `key={index}` only on a derived fixed-length token list (compliant); semantic keys on Consequences/Stunts (the [EDGE] Low collision risk); no `useEffect`/dep issues in the diff (pure presentational); no `dangerouslySetInnerHTML`. ✓ (with the noted Low edge)
- **#7 Async:** none in the diff. N/A
- **#8 Tests:** no `as any` in assertions; renders the real component, asserts real DOM; 5 TDD cases added. ✓
- **#9 Build/config:** no compiler-flag changes. ✓

### Devil's Advocate
Arguing the code is broken: A malicious or buggy server could weaponize the unguarded render paths. If it emits two `mild` consequence slots (legal extra-mild in some Fate stunt builds), the player sees only one — a wound silently vanishes from a read-only sheet whose whole job is to be the trustworthy ground-truth display (a quiet "lie detector" failure of exactly the kind SOUL warns about, albeit cosmetic). If it emits `refresh: NaN` the header reads "NaN of NaN" with no tokens — confusing, but the player can't act on FP from the sheet anyway (read-only), so the blast radius is a bad-looking header, not a wrong decision. A confused author writing a homebrew Fate pack with an absurdly long aspect string would overflow the accent-barred row — cosmetic, no functional break. None of these throw (no `.map` on possibly-undefined: the components guard the outer arrays and only the per-track/per-row edge cases are unguarded; the data originates from server-seeded standard slots, so duplicates/NaN are protocol violations, not normal play). What about XSS — could an author inject `<script>` via an aspect name from a homebrew pack? No: every string is a JSX text child, React-escaped (security subagent confirmed, evidence-cited). Could the eyebrow leak another world's identity? No — `worldSlug` is the session's own server-set slug, only shown when `fateSheet` is present. Net: the realistic failure modes are bounded to cosmetic/edge display oddities on malformed server data, in already-merged code, with the standard fix (index-tiebreaker keys + finite/empty guards) being a clean follow-up. Nothing rises to High.

**Conclusion:** No Critical/High. Security clean. Restyle is well-typed, well-commented, tested (11/11), and wired end-to-end (verified live). The 5 edge findings are Low display-robustness nits on edge-case server data, captured as non-blocking delivery findings. The playtest verification (the story's real deliverable) is thorough and honestly reported, including a forthright "couldn't trigger a Contest on gulliver → verify on glenross" rather than a false pass. **APPROVED.**

**Handoff:** To SM for finish-story.