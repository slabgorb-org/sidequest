---
story_id: "118-6"
jira_key: ""
epic: "118"
workflow: "tdd"
---
# Story 118-6: F3f — Fate conflict surface

## Story Details
- **ID:** 118-6
- **Jira Key:** (not in scope)
- **Workflow:** tdd
- **Stack Parent:** 118-2 (depends_on)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-16T13:27:47Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-16T11:53:46Z | 2026-06-16T11:55:54Z | 2m 8s |
| red | 2026-06-16T11:55:54Z | 2026-06-16T12:19:38Z | 23m 44s |
| green | 2026-06-16T12:19:38Z | 2026-06-16T12:46:57Z | 27m 19s |
| review | 2026-06-16T12:46:57Z | 2026-06-16T13:01:32Z | 14m 35s |
| red | 2026-06-16T13:01:32Z | 2026-06-16T13:06:21Z | 4m 49s |
| green | 2026-06-16T13:06:21Z | 2026-06-16T13:13:38Z | 7m 17s |
| review | 2026-06-16T13:13:38Z | 2026-06-16T13:27:47Z | 14m 9s |
| finish | 2026-06-16T13:27:47Z | - | - |

## Sm Assessment

**Story selected:** 118-6 — F3f Fate conflict surface (8 pts, p2, tdd). Chosen as the teed-up continuation of the active F3 (ADR-144 Fate Core UI) thread — the most recent sprint commit folded the 118-10 findings R1–R3 into this story's scope.

**Dependencies — all satisfied:**
- 118-2 (FatePanel / FATE_STATE) — `done`
- 118-10 (server-side invoke_mode + player_action wire) — `done`/archived
- Composes 118-3 FateDiceTray (built, not yet mounted) and 118-8 (server-authenticated identity).

**Repos:** server + ui, both branched `feat/118-6-fate-conflict-surface` off `develop` per repos.yaml. Merge gate clear (no open PRs).

**Scope flagged for TEA's RED phase — three carried 118-10 findings the tests must pin down:**
1. **Reroll execution** — `invoke_mode='reroll'` must perform a real server-side 4dF reroll + OTEL span; 118-10 only carried the mode over the wire. Do NOT ship a reroll button before the server reroll exists. RED test must assert the reroll actually executes.
2. **player_action sanitization** — threading `FateActionPayload.player_action` into narrator prose needs an explicit ADR-047 sanitization decision (dice precedent threads RAW; freeform uses `sanitize_player_text`). Don't inherit the gap unconsidered.
3. **Concede + player_action** — decide whether a concession carrying freeform text emits the `flavor_rider` span / threads to narrator, or is intentionally rider-less.

**Negative tests required:** non-Fate `ruleset` guard (never co-renders with WN/native ConfrontationOverlay), sealed-commit-barrier disable, invoke disabled at no-free-invoke + 0-fate. Economy is server-authoritative — panel reflects FATE_STATE with NO optimistic decrement.

**Handoff:** → TEA (Argus Panoptes) for RED phase.

## TEA Assessment

RED phase complete. 6 failing test files across server + ui pin the three ACs, the
three story-named UI negatives, and the mandatory wiring. Verified RED directly (not
just "written"): **server 4 RED + 5 green guards**, **ui 3 files RED**.

### Server (tests/server/dispatch/)
- **`test_fate_reroll_execution_118_6.py`** — AC#1. RED: `test_reroll_keeps_the_second_roll`
  (dispatch keeps the original 4dF; a 'reroll' is a no-op), `test_reroll_outcome_is_attested_on_the_resolved_span`
  (the `fate.action_resolved` span the GM panel reads carries the discarded first roll, not
  the kept reroll — the Illusionism the lie-detector must catch). Determinism via a seeded
  `random.Random` (first roll = draws 1-4, reroll = draws 5-8); isolated with an idle-Ally
  open barrier so the opponent defense roll can't pollute the span stream. GREEN guards:
  `bonus_mode_keeps_the_first_roll`, `reroll_requires_an_invoke` (no free reroll without a
  spent invocation — No Silent Fallbacks in the other direction).
- **`test_fate_player_action_narrator_118_6.py`** — AC#2. RED: `player_action_rides_into_narrator_hints`
  (the freeform-rides-the-tile feature — no narrator path today), `player_action_is_sanitized_at_the_narrator_seam`
  (asserted on `encounter.narrator_hints`, the seam `render_encounter_summary` carries to the prompt).
- **`test_fate_concede_rider_118_6.py`** — AC#3. 3 GREEN guards locking the rider-less decision
  (see Delivery Finding F2): no `flavor_rider` span on concede, no freeform leak into the
  narrator seam, concede still earns its fate point.

### UI
- **`src/components/__tests__/FateConflictSurface.test.tsx`** — the new conflict surface (suite RED:
  component doesn't exist). Covers: participants-by-side/turn-order, FateDiceTray mount, the
  proactive tiles + Concede, the **ruleset gate** (non-fate → empty) and **no-active-conflict gate**,
  the **invoke-disabled-at-0-fate+0-free-invoke** economy negative (+ the two enabled cases),
  the **sealed-commit-barrier disable**, and **freeform-text-rides-the-tile** (`player_action` on the dispatch).
- **`src/components/GameBoard/__tests__/GameBoard-fate-conflict.test.tsx`** — mandatory wiring +
  the epic's paired negative: surface reachable when `conflict.active`; absent when sheet-only;
  absent during a WN/native confrontation (never co-renders with ConfrontationOverlay).
- **`src/hooks/__tests__/useStateMirror.fate-roll.test.ts`** — wires the orphaned FATE_ROLL into a
  `fateRoll` state field (latest-wins event; malformed degrades to null).

### Rule Coverage
- **OTEL / Illusionism (CLAUDE.md OTEL principle, SOUL):** AC#1 reroll-span attestation is the
  core — the GM panel must see the kept roll, not a reroll that never happened.
- **No Silent Fallbacks:** reroll-without-invoke guard (no free reroll); malformed FATE_ROLL → null.
- **No Source-Text Wiring Tests:** every server assertion drives the real dispatch and checks the
  roll / span / economy — zero `read_text()` greps.
- **Every Test Suite Needs a Wiring Test:** GameBoard-fate-conflict is the reachability proof.
- **ADR-047 / 116-4 prompt-injection boundary:** AC#2 sanitization at the narrator seam.
- **ADR-143 (bind, don't balance):** the surface reuses ConfrontationOverlay's mount *pattern*
  only; Fate state, never native dial/beat internals (the gate tests enforce non-co-render).

### For Dev (Hephaestus)
Two TEA design decisions are encoded in the tests and **must be honored or explicitly
overridden with the Reviewer** (see Delivery Findings F1, F2). The UI tests DEFINE the
component contract (props: `fateState`, `fateRoll`, `ruleset`, `actorName`, `sealedWaiting?`,
`onFateAction`); testids are the seam — match them or update the tests with rationale.

**Handoff:** → Dev (Hephaestus the Smith) for GREEN phase.

## Dev Assessment

**Implementation Complete:** Yes — all 9 server tests + all UI tests GREEN, end-to-end wired.

**Files Changed:**
- **server** `sidequest/server/dispatch/fate_conflict.py` — AC#1 reroll execution (re-resolve + keep
  the second outcome on a real `invoke_mode='reroll'` invocation; the second `fate.action_resolved`
  span attests the kept roll) + AC#2 sanitized `player_action` rider appended to `encounter.narrator_hints`.
  AC#3 needed no code (concede returns before the rider path — F2 confirmed).
- **ui** `src/components/FateConflictSurface.tsx` (NEW) — the Fate analog of ConfrontationOverlay.
- **ui** `src/hooks/useStateMirror.ts`, `src/providers/GameStateProvider.tsx` — FATE_ROLL → `state.fateRoll`.
- **ui** `src/components/GameBoard/GameBoard.tsx` — mounts the surface (conflict-gated widget), threads
  `fateRoll`/`onFateAction`; `dockviewReady` re-trigger so a mount-time conflict panel is added.
- **ui** `src/components/GameBoard/widgetRegistry.ts` + `MobileTabView.tsx` — `fate-conflict` widget/tab
  (the dual registration both dock surfaces need; the jsdom path is MobileTabView).
- **ui** `src/types/protocol.ts` + `src/App.tsx` — outbound `FATE_ACTION` channel → server FateActionHandler.

**Tests:** server 9/9 (new) + 44 existing Fate dispatch + 1427 in the broad serial run; ui 2281/2281 (full suite).
**Pre-existing failure (NOT mine):** `test_sealed_letter_dispatch_integration::test_legacy_beat_selection_path_still_works`
— CAC content-fixture drift ("needs a 'strike' beat"); fails identically with my change stashed (see
memory `wwn_content_breaks_server_fixtures`).
**Branch:** `feat/118-6-fate-conflict-surface` (pushed — server `a003f57d`, ui `224873f`).

**Wiring proof (end-to-end):** FATE_STATE(conflict)+FATE_ROLL → useStateMirror → GameStateProvider →
GameBoard → FateConflictSurface → onFateAction → App.handleFateAction → FATE_ACTION over WS →
server FateActionHandler → dispatch_fate_action. Reroll/rider verified by the AC tests; surface
reachability by the GameBoard wiring test (+ paired negative).

**Handoff:** → TEA (Argus Panoptes) for the verify phase.

## Delivery Findings

- **F1 (Question / non-blocking) — AC#2 sanitization decision (TEA-ratified):** `player_action`
  threaded to the narrator MUST pass `sanitize_player_text` at the `narrator_hints` seam, matching
  the 116-4 [HIGH][SEC] aspect-text precedent and the 118-8 seal-site `payload.skill` sanitization —
  NOT the dice self-action precedent that threads raw (dice.py:285/312). `narrator_hints` reach the
  prompt unsanitized via `render_encounter_summary`, so threading the rider raw re-opens the exact
  injection hole 116-4 closed. Encoded in `test_player_action_is_sanitized_at_the_narrator_seam`.
  Reviewer: confirm or override.
- **F2 (Question / non-blocking) — AC#3 concede is rider-less (TEA-ratified):** a concession carrying
  freeform text emits NO `flavor_rider` span and threads nothing to the narrator. Rationale: concede is
  pre-roll and withdraws the actor (its narrative rides the `fate.conceded` event); keeping it rider-less
  holds the narrator-bound `player_action` surface to exactly ONE path (proactive), so there is a single
  seam to sanitize (F1). Encoded as GREEN guards in `test_fate_concede_rider_118_6.py` — locking current
  behavior so it can't drift unsanitized. If the project later wants concede flavor, revise these guards
  together with an AC#2-style sanitized seam — never silently.
- **F3 (Gap / non-blocking) — reroll implementation seam:** `ruleset.invoke_aspect(mode='reroll')` returns
  0 by contract ("the reroll itself is the caller's job", fate.py:280). The reroll therefore belongs in
  `dispatch_fate_action` (fate_conflict.py:758-783): when an invoke actually fired with `invoke_mode='reroll'`,
  re-run `ruleset.resolve_action` and KEEP the second outcome (SRD reroll = replace, not take-better), so a
  fresh `fate.action_resolved` span attests the kept roll. Gate the reroll on a real invocation, not the bare
  `payload.invoke_mode` flag (the `reroll_requires_an_invoke` guard).
- **F4 (Gap / non-blocking) — FateConflictEntry carries only `active` + `participants`:** the surface renders
  turn order from participant seating order and absorption math from each PC's `stress`/`consequences` in
  `FateCharacterEntry` (all already on FATE_STATE). If Dev finds "taken-out" / explicit turn-order needs a
  payload field, that's a scoped FATE_STATE extension — flag it rather than faking it client-side.

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Improvement** (non-blocking): the `dockviewReady` re-trigger I added (GameBoard.tsx) also fixes a
  latent gap — a `confrontation` panel for an encounter already active at MOUNT (reconnect mid-fight)
  was never added, because the panel-sync effect's first run saw a null dockview api and never re-ran.
  Affects `src/components/GameBoard/GameBoard.tsx` (now covered for fate-conflict; confrontation benefits
  for free). *Found by Dev during implementation.*
- **Gap** (non-blocking): the server already emits FATE_ROLL from `dispatch_fate_action`'s `action_roll`,
  so a reroll's KEPT dice flow to the client for free — but the 3D dice in FateDiceTray still render the
  idle pickup row (FATE_ROLL carries no throw_params/seed to replay), a pre-existing 118-3 limitation the
  conflict surface inherits. The text readout is authoritative. Affects `src/dice/FateDiceTray.tsx`
  (replay-params follow-up). *Found by Dev during implementation.*
- **Question** (non-blocking): the conflict surface is mounted as a right-tab-group widget (in
  `rightGroupOrder`), not a canvas-claiming overlay like ConfrontationOverlay. It auto-focuses on
  mid-session arrival (sync effect setActive) but joins as a tab on mount-time reconnect. If the drama-peak
  canvas-claim is required at parity with confrontation, that's a layout follow-up. Affects
  `src/components/GameBoard/GameBoard.tsx`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): the Attack tile sends no `target` → `_resolve_attack` always raises "an attack must
  name a target", so attacks from the surface never land. Affects `src/components/FateConflictSurface.tsx`
  (add a `target` field + opponent picker) and the new RED test. *Found by Reviewer during code review.*
- **Gap** (blocking): the FATE_ACTION handler catches only `FateConflictError`; an unaffordable invoke raises
  the sibling `FateEconomyError`, which escapes as an untyped error on a stale-FATE_STATE race now that the
  invoke affordance is user-reachable. Affects `sidequest-server/sidequest/handlers/fate_action.py:120`
  (broaden the catch). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): a reroll emits TWO `fate.action_resolved` spans (discarded + kept), both
  unmarked — the GM panel can't tell them apart. Affects `sidequest-server/sidequest/server/dispatch/fate_conflict.py:810`
  (consider a `superseded`/`reroll` span attribute). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): an all-injection `player_action` sanitizes to "" but still appends an empty
  "(flourish):" narrator hint — gate the append on the sanitized result. Affects `fate_conflict.py:749`.
  *Found by Reviewer during code review.*
- **Gap** (non-blocking): scene aspects/boosts (from create_advantage) are never offered for invocation on the
  surface (only the PC's character aspects) — a core Fate mechanic absent. Affects `FateConflictSurface.tsx`
  + server `FateSheet.all_aspects()` scene-aspect path. *Found by Reviewer during code review.*
- **Gap** (non-blocking): `me=null`/`actorName=''` (pre-identity / non-participant) dispatches `skill:''` →
  server `skills.get('',0)=0`, a silent fallback; guard the tiles when the local actor can't be resolved.
  Affects `FateConflictSurface.tsx:99` / `GameBoard.tsx:619`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the FATE_ROLL mirror guard validates only the dice 4-tuple, not the other
  required fields — a partial payload (version skew) reaches FateDiceTray. Affects `src/hooks/useStateMirror.ts`.
  *Found by Reviewer during code review.*
- **Question** (non-blocking): for create_advantage the one freeform box feeds BOTH `aspect_text` (the placed
  aspect's name) and `player_action` (the narrator flourish); consider separate inputs. Affects
  `FateConflictSurface.tsx:112`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking, pre-existing): client-supplied `difficulty` is trusted for passive opposition
  unclamped; and `aspect_text` is stored unsanitized at the seal site — both [SEC]; the latter is **already
  scoped as backlog 118-9**. Affects `fate_conflict.py:790,835`. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

3 deviations

- **Action skill selection simplified to a default-first `<select>`**
  - Rationale: no test pins skill selection; a minimal real selector keeps the action functional (a real
  - Severity: minor
  - Forward impact: minor — a richer skill picker is an additive UI follow-up; the wire contract is unchanged.
- **FATE_ACTION payload hardcodes `difficulty: 0`**
  - Rationale: the client never computes opposition DCs — the server derives active (opposed) vs passive
  - Severity: minor
  - Forward impact: none — matches the server default; passive-difficulty scenarios are server-driven.
- **Invoke affordance includes a +2/reroll mode toggle beyond the tested economy gate**
  - Rationale: the story scope explicitly says "+2 or reroll", and AC#1 made the server reroll real —
  - Severity: minor
  - Forward impact: minor — the dispatch shape is the FateActionPayload contract; a Reviewer may want a

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Action skill selection simplified to a default-first `<select>`**
  - Spec source: context-story-118-6.md, story title (proactive-action tiles)
  - Spec text: "proactive-action tiles (overcome/create_advantage/attack)" — a player picks a skill to act on
  - Implementation: the surface renders a `fate-skill-select` defaulting to the actor's first skill; the
    dispatched FateActionPayload carries that skill. No full skill-picker UX (grouping, ladder hints beyond
    the option label).
  - Rationale: no test pins skill selection; a minimal real selector keeps the action functional (a real
    skill on the wire) without untested picker UX. Server is the rating authority.
  - Severity: minor
  - Forward impact: minor — a richer skill picker is an additive UI follow-up; the wire contract is unchanged.
- **FATE_ACTION payload hardcodes `difficulty: 0`**
  - Spec source: server `FateActionPayload` (protocol/fate.py)
  - Spec text: `difficulty: int = 0` — passive opposition value when target is None
  - Implementation: App.handleFateAction sends `difficulty: 0`; the surface does not expose a DC input.
  - Rationale: the client never computes opposition DCs — the server derives active (opposed) vs passive
    opposition from `target`. A player-set DC would be a mechanical authority the client must not hold
    (No Silent Fallbacks / server-authoritative economy).
  - Severity: minor
  - Forward impact: none — matches the server default; passive-difficulty scenarios are server-driven.
- **Invoke affordance includes a +2/reroll mode toggle beyond the tested economy gate**
  - Spec source: context-story-118-6.md, story title (the F3d invoke affordance)
  - Spec text: "clickable per-aspect Invoke, keyed on aspect TEXT, +2 or reroll"
  - Implementation: clicking Invoke arms a pending invocation (default mode 'bonus') with a +2/Reroll
    toggle; the next proactive tile carries `invoke_aspect`+`invoke_mode`. The tests only assert the
    Invoke button's disabled/enabled economy, not the dispatch or the toggle.
  - Rationale: the story scope explicitly says "+2 or reroll", and AC#1 made the server reroll real —
    shipping a bonus-only invoke would leave the live server reroll unreachable (No half-wired features).
    Kept minimal (no separate testids drive logic the tests pin).
  - Severity: minor
  - Forward impact: minor — the dispatch shape is the FateActionPayload contract; a Reviewer may want a
    test pinning the invoke-bearing dispatch (currently untested-by-design, flagged here).

### Reviewer (audit)
- **Skill selection simplified to a default-first `<select>`** → ✓ ACCEPTED by Reviewer: sound minimal
  surface; the server is the rating authority and the wire contract is unchanged.
- **FATE_ACTION payload hardcodes `difficulty: 0`** → ✓ ACCEPTED by Reviewer (with caveat): correct for the
  current passive-opposition model and matches the server default; the client correctly does not adjudicate.
  Caveat — the server trusts the wire value unclamped ([SEC] finding, pre-existing); a follow-up, not a blocker.
- **Invoke affordance includes a +2/reroll mode toggle beyond the tested economy gate** → ✗ FLAGGED by
  Reviewer: the toggle is reasonable (the server reroll is now real), BUT the invoke-bearing dispatch ships
  with NO server-side `FateEconomyError` handling — a session-error vector on a stale-state race (HIGH #2).
  Acceptable only once the handler returns a typed error for an unaffordable invoke. Re-test required.
- **UNDOCUMENTED — the Attack tile dispatches no `target`:** Spec implied a working "attack" tile that can
  take an opponent "taken-out"; code ships an Attack button that sends `target:null` and always errors in
  `_resolve_attack`. Not logged by Dev. Severity: **HIGH** (blocking) — see Reviewer Assessment.

### Reviewer (audit — R2 re-review)
- **R1 FLAGGED "Invoke +2/reroll toggle ships with no `FateEconomyError` handling"** → ✓ RESOLVED by Reviewer:
  the GREEN rework broadened the handler catch to `(FateConflictError, FateEconomyError)` (fate_action.py:121)
  and TEA pinned it with `test_unaffordable_invoke_returns_typed_error_not_uncaught` + the affordable-invoke
  GREEN guard. The flag's precondition ("acceptable only once the handler returns a typed error") is now met.
- **R1 UNDOCUMENTED "Attack tile dispatches no target"** → ✓ RESOLVED by Reviewer: the rework adds `target` to
  `FateActionInput`, derives it from an opponent-side participant, and exposes a `fate-target-select` picker;
  3 new UI tests pin the dispatched target. No new deviations introduced by the rework.

## Subagent Results — R1 (superseded by R2 re-review below)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (GREEN: 29 tests pass, lint/tsc clean, 0 smells) | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | Yes | findings | 13 | confirmed 9 (1 HIGH-blocking, 8 non-blocking), dismissed 0, deferred 4 (dup/low) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | N/A — disabled via settings; silent-failure dimension assessed manually |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | N/A — disabled; test quality assessed manually (preflight confirms green + meaningful asserts) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | N/A — disabled; comment accuracy assessed manually |
| 6 | reviewer-type-design | No | Skipped | disabled | N/A — disabled; type design assessed manually |
| 7 | reviewer-security | Yes | findings | 2 | confirmed 2 (both non-blocking/pre-existing), dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | No | Skipped | disabled | N/A — disabled; simplicity assessed manually |
| 9 | reviewer-rule-checker | No | Skipped | disabled | N/A — disabled; lang-review rules enumerated manually (see Rule Compliance) |

**All received:** Yes (3 enabled subagents returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 2 confirmed blocking (HIGH), 9 confirmed non-blocking, 4 deferred (low/dup)

## R1 Verdict (REJECTED — superseded by R2 re-review below)

**Verdict:** REJECTED (R1 — superseded; both HIGH blockers fixed in the GREEN rework, see R2 assessment)

Two HIGH-severity defects block this story. The first is squarely introduced by this diff (the new
Attack tile is non-functional); the second is a pre-existing robustness gap that this diff makes
user-reachable for the first time (the new invoke affordance). Both are testable behavior bugs →
rework returns to TEA for RED tests.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] [EDGE] | The Attack tile dispatches **no target** — `FateActionInput` has no `target` field and `dispatch()` never sets one, so every attack sends `target: null`. `_resolve_attack` hard-raises `FateConflictError("an attack must name a target")` when `commit.target is None`. **Every Attack from the surface errors at exchange time** (after the 4dF already rolled + sealed). A core advertised tile is non-functional — "No half-wired features." | `sidequest-ui/src/components/FateConflictSurface.tsx:101` (FateActionInput / dispatch) → server `fate_conflict.py:500-501` | Add `target?: string` to `FateActionInput`; for the Attack verb, surface an opponent-side target picker (from `conflict.participants` where `side==='opponent'`) and populate `target` before dispatch. Add a test pinning that an attack carries a target. |
| [HIGH] [EDGE] | The new invoke affordance can raise `FateEconomyError` (unaffordable invoke: 0 fate points + 0 free invokes) on a **stale-FATE_STATE race** — the client gates the button on `canInvoke()`, but the economy is server-authoritative and the client's FATE_STATE can lag. `FateEconomyError` and `FateConflictError` are **sibling** `ValueError`s, so the handler's `except FateConflictError` (fate_action.py:120) does NOT catch it → an untyped error escapes instead of the graceful typed `fate_dispatch_error`. | `sidequest-server/sidequest/handlers/fate_action.py:120` | Broaden the catch to `except (FateConflictError, FateEconomyError)` (or add a sibling base) and return a typed `fate_dispatch_error`. Add a test: an unaffordable invoke returns a typed error, not an uncaught exception. |
| [LOW] [EDGE] | `player_action` that sanitizes to empty (pure injection tokens, e.g. `<system></system>`) still appends an empty `"{actor} (flourish): "` hint — the guard checks `payload.player_action.strip()` BEFORE sanitization, never the sanitized result. Pollutes narrator context with a contentless line. | `sidequest-server/sidequest/server/dispatch/fate_conflict.py:749,761` | Compute `sanitized = sanitize_player_text(payload.player_action)` first, gate the append on `if sanitized:`. |

**Data flow traced:** player types freeform + clicks Attack tile → `FateConflictSurface.dispatch("attack")`
builds `{action:"attack", skill, player_action}` (NO target) → `App.handleFateAction` → `FATE_ACTION`
over WS (`target: null`) → `FateActionHandler` → `dispatch_fate_action` seals + rolls → barrier closes →
`run_fate_exchange` → `_resolve_attack` raises `FateConflictError` (target None). **The attack always
fails after the roll already fired.** (Unsafe because the tile advertises a working attack.)

**Pattern observed:** the server reroll (`fate_conflict.py:801-818`) correctly re-resolves and keeps the
second outcome — a clean, SRD-faithful implementation. The sanitization seam (`:761`) correctly applies
`sanitize_player_text` (confirmed by [SEC]). The defect is not in the server reroll/rider logic but in the
UI surface's incomplete action payload.

**Error handling:** the dispatch's loud guards are good (`_resolve_attack` fails loud on a missing target —
that's WHY the attack errors rather than silently passing), but the *handler* doesn't translate
`FateEconomyError` into a typed client error (HIGH #2). The client `me=null` / `actorName=''` path silently
dispatches `skill:''` → server `skills.get('',0)=0` (a silent fallback — deferred finding, non-blocking).

### Rule Compliance (lang-review: python.md + typescript.md, enumerated)

- **python #1 silent exception swallowing:** `fate_conflict.py` change adds no try/except — COMPLIANT. (The
  HANDLER's narrow `except FateConflictError` is the HIGH #2 finding, but that file is unchanged by this diff.)
- **python #3 type annotations at boundaries:** change is inside the already-annotated `dispatch_fate_action`;
  `invoked_reroll: bool`, `opposition: Opposition` — COMPLIANT.
- **python #6 test quality:** the 3 new server test files have meaningful assertions (dice equality, span
  attrs, economy deltas) — no `assert True`/vacuous — COMPLIANT (preflight green).
- **python #8 unsafe deserialization / #7 resource leaks / #9 async:** none introduced — COMPLIANT.
- **typescript #1 type-safety escapes:** `as unknown as FateRollPayload` in the mirror + `as WithFateRoll`
  in tests match the existing FATE_STATE boundary idiom — COMPLIANT.
- **typescript #4 null/undefined:** `activeSkill = skill || skills[0]?.name || ""` uses `||` intentionally
  ("" = unset) — acceptable; FATE_ROLL guard validates the dice 4-tuple — COMPLIANT (partial-field validation
  is a deferred Medium, consistent with the FATE_STATE guard).
- **typescript #6 React/JSX:** `key={p.name}`/`key={a.text}` (not index); no `dangerouslySetInnerHTML`;
  effect deps updated (`dockviewReady`, `fateRoll`, `onFateAction`) — COMPLIANT.
- **typescript #10 input validation:** participant/aspect text rendered as auto-escaped React children;
  `player_action` sanitized server-side; `makeRequestId` uses CSPRNG — COMPLIANT ([SEC] confirmed).

### Dispatch-tag coverage
- **[EDGE]** — confirmed: the two HIGH blockers + the empty-flourish LOW (above); deferred non-blocking edges
  recorded in Delivery Findings.
- **[SEC]** — confirmed 2, both non-blocking: (a) `aspect_text` stored unsanitized at the seal site
  (`fate_conflict.py:835`) — pre-existing, the live narrator paths ARE sanitized, and it is **already scoped
  as backlog story 118-9**; (b) client-trusted `difficulty` (`:790` / App `difficulty:0`) — pre-existing
  endpoint, already a logged Dev deviation. Central ADR-047 concern (the new `player_action` rider) is
  correctly sanitized.
- **[SILENT]** (disabled — assessed manually): the `me=null → skill:''` dispatch is a client-side silent
  fallback (deferred, non-blocking); server-side guards fail loud correctly. No swallowed errors introduced.
- **[TEST]** (disabled — assessed manually): preflight GREEN, asserts meaningful; gap — no test pins the
  attack target or the invoke-bearing dispatch (the HIGH #1 root cause TEA must now cover).
- **[DOC]** (disabled — assessed manually): comments accurate; the reroll comment "the GM panel sees the kept
  reroll" slightly overstates (it sees BOTH the discarded and kept resolved spans — deferred finding).
- **[TYPE]** (disabled — assessed manually): `FateActionInput` is a clean interface but **missing the `target`
  field** the attack verb requires (root of HIGH #1).
- **[SIMPLE]** (disabled — assessed manually): no over-engineering; the reroll re-uses `resolve_action` cleanly.
- **[RULE]** (disabled — assessed manually): see Rule Compliance above — no violations.

### Devil's Advocate

Assume this is broken. A player joins a Fate conflict and does the most obvious thing: clicks **Attack** on
the opponent. The 4dF rolls, the dice tray animates a result — and then an error frame returns:
"FATE_ACTION rejected: an attack must name a target." The player saw dice resolve but the attack evaporated;
worse, the roll already consumed RNG and sealed a commit, so the encounter state is now half-mutated. They try
again — same failure, every time. The single most central verb of a *conflict* surface cannot land a blow.
This is not a rare edge; it is the happy path. The tests pass only because TEA pinned the tile's *existence*
and the freeform dispatch, never that an attack reaches a defender — a classic "green tests, dead feature."

Now the stressed case: a player on their last fate point invokes an aspect for +2, the server debits it, then
on their next action the client (FATE_STATE still in flight) shows the now-spent point as available and offers
Invoke again. They click. The server raises `FateEconomyError`; the handler — which only knows
`FateConflictError` — lets it escape as an untyped error. In multiplayer this is a race every table will hit.

A confused user: for Create Advantage, the one freeform box becomes BOTH the aspect's name and the narrator
flourish, so "I swing from the chandelier and fire" is placed as a *situation aspect literally named that*.
A malicious user: types pure injection as `player_action` — correctly stripped, but a contentless
"(flourish):" line still enters the narrator context. None of these are catastrophic, but the Attack defect
alone is disqualifying: a conflict UI whose Attack button always errors is not shippable.

**Handoff:** Back to TEA (Argus Panoptes) for RED tests covering the attack-target dispatch and the
unaffordable-invoke typed-error path, then Dev for the fixes.
## TEA Assessment — Rework R1 (RED)

Reviewer REJECTED with two HIGH blockers. Added one new RED test per blocker (verified RED for the
right reason), each pinning the exact behavior the fix must produce. Existing 118-6 tests untouched
and still pass (11/11 UI in the surface file, 3/3 server handler-wiring).

**HIGH #1 — Attack must name an opponent target** (`sidequest-ui/src/components/__tests__/FateConflictSurface.test.tsx`,
new describe "the attack names an opponent"):
- `dispatches an opponent-side participant as the target when Attack is clicked` — RED: the surface sends no target.
- `never targets a player-side participant` — guard: the target is the Other (`The Fat Man`), never the acting PC.
- `still carries the freeform rider alongside the target` — guard: the target fix must not drop freeform-rides-the-tile.
- **Dev contract:** add `target?: string` to `FateActionInput`; for the Attack verb, populate it from an
  opponent-side `conflict.participants` entry (auto-target the sole opponent; a picker if multiple). `App.handleFateAction`
  already forwards `target` — only the surface needs to supply it.

**HIGH #2 — Unaffordable invoke returns a typed error** (`sidequest-server/tests/server/test_fate_unaffordable_invoke_handler_118_6.py`):
- `test_unaffordable_invoke_returns_typed_error_not_uncaught` — RED: `FateEconomyError` escapes the handler
  (asyncio.run re-raises). The fix is one line in `sidequest/handlers/fate_action.py:120` — broaden
  `except FateConflictError` to also catch `FateEconomyError` (sibling `ValueError`), returning a fate-coded `ERROR`.
- `test_affordable_invoke_still_resolves_to_a_roll` — GREEN GUARD: a payable invoke (free invocation) must STILL
  reach the 4dF roll, not be swallowed by the new economy-error handling.

**Not re-tested (Reviewer non-blocking findings):** left for Dev's judgement / follow-ups (dual reroll span,
empty-flourish hint, scene-aspect invokes, `me=null` skill=0 guard, FATE_ROLL partial-payload validation,
create_advantage double-use, the pre-existing `[SEC]` items incl. backlog 118-9). The empty-flourish LOW is a
trivial one-line fix Dev may fold in; no RED test written for it (cosmetic narrator noise, not a contract).

**Branches:** `feat/118-6-fate-conflict-surface` — server `18800836`, ui `2da8692` (RED rework committed).

**Handoff:** → Dev (Hephaestus the Smith) for the GREEN fixes.

### TEA (rework R1)
- No new upstream findings — the rework scope is exactly the two Reviewer HIGH blockers, both now pinned by RED tests.
## Dev Assessment — Rework R1 (GREEN)

Both Reviewer HIGH blockers fixed; the rework RED tests are GREEN and no existing tests regressed.

**HIGH #1 — Attack names an opponent target** (`sidequest-ui/src/components/FateConflictSurface.tsx`):
- Added `target?: string` to `FateActionInput`; the attack verb now dispatches `target` from an
  opponent-side `conflict.participants` entry (default the sole/first opponent; a `fate-target-select`
  picker when several). Overcome/create_advantage stay passive (no target). `App.handleFateAction`
  already forwarded `target`, so no App change was needed.
- All 14 FateConflictSurface tests GREEN (3 new attack-target + 11 existing).

**HIGH #2 — Typed error for an unaffordable invoke** (`sidequest-server/sidequest/handlers/fate_action.py:120`):
- Broadened `except FateConflictError` → `except (FateConflictError, FateEconomyError)` (the two are sibling
  `ValueError`s), returning the graceful typed `fate_dispatch_error` instead of letting the economy error escape.
- Both rework server tests GREEN (the typed-error RED + the affordable-invoke guard).

**LOW (folded in) — empty-flourish guard** (`sidequest-server/.../fate_conflict.py:749`):
- The `player_action` narrator-hint append is now gated on the SANITIZED result, so an all-injection rider
  that sanitizes to "" no longer appends a contentless "(flourish):" line. Existing player_action tests still pass.

**Tests:** ui 2284/2284 (full suite, +3); server rework 2/2 + 9 existing 118-6 + 379 fate-ecosystem (1 pre-existing
sealed-letter CAC content-drift failure, unrelated — fails identically with my change stashed). tsc + ruff + eslint clean.
**Branches:** `feat/118-6-fate-conflict-surface` — server `d09559f7`, ui `f7a1b64` (pushed).

**Non-blocking Reviewer findings NOT addressed (deferred, by design):** dual reroll span, scene-aspect invokes,
`me=null` skill=0 guard, FATE_ROLL partial-payload validation, create_advantage aspect_text/player_action
double-use, and the pre-existing `[SEC]` items (difficulty clamp; aspect_text seal sanitization — the latter is
backlog 118-9). These remain in Delivery Findings for follow-up stories.

**Handoff:** → Reviewer (Hermes Psychopompos) for re-review.

### Dev (rework R1)
- No new upstream findings — the rework was exactly the two Reviewer HIGH fixes plus the folded-in LOW.

### Reviewer (re-review R2)
- **Improvement** (non-blocking): the Attack tile dispatches `target: ""` when `opponents.length === 0` (a
  stale-FATE_STATE race after a conflict ends); App's `?? null` doesn't coerce `""`, so the server returns a
  *misleading* typed error ("attack target '' has no Fate sheet") instead of "an attack must name a target".
  Affects `sidequest-ui/src/components/FateConflictSurface.tsx` (gate the spread on `verb === "attack" && activeTarget`).
  *Found by Reviewer during re-review.*
- **Improvement** (non-blocking): `payload.target` is interpolated into `narrator_hints` unsanitized at the seal
  site (pre-existing Story 118-8 code, not the 118-6 diff) — defense-in-depth consistency with the adjacent
  `sanitize_player_text(payload.skill)`. Practically gated by seated-creature name validation. Fold into the
  **backlog 118-9** seal-site sanitization scope. Affects `sidequest-server/sidequest/server/dispatch/fate_conflict.py:834`.
  *Found by Reviewer during re-review.*
- **Improvement** (non-blocking): the handler's client-facing error string interpolates the raw `FateEconomyError`
  message (internal config/type names). Consider a generic player message with full detail logged server-side only.
  Affects `sidequest-server/sidequest/handlers/fate_action.py:130`. *Found by Reviewer during re-review.*
- **Gap** (non-blocking, follow-up): `test_handler_drives_dispatch_end_to_end` is a pre-existing probabilistic flake
  (unseeded RNG asserting a liveness outcome) — not introduced by 118-6. Seed the handler RNG in the wiring test or
  replace the liveness assertion with an OTEL-span assertion. Affects
  `sidequest-server/tests/server/test_fate_action_handler_wiring.py:92`. *Found by Reviewer during re-review.*

## Subagent Results

(R2 re-review of the GREEN rework delta — `a003f57d..d09559f7` server / `224873f..f7a1b64` ui. Re-ran the three
enabled specialists against the rework changes; the 6 disabled-via-settings specialists are pre-filled as before.)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (GREEN: 14 server + 23 ui tests pass, ruff/tsc clean, 0 smells) | confirmed 0, dismissed 0, deferred 1 (pre-existing RNG flake in `test_handler_drives_dispatch_end_to_end`, unrelated to rework) |
| 2 | reviewer-edge-hunter | Yes | findings | 3 | confirmed 3 (all non-blocking), dismissed 1 fix-suggestion (catch-NotImplementedError violates No Silent Fallbacks), deferred 0 |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | N/A — disabled via settings; silent-failure dimension assessed manually |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | N/A — disabled; rework tests assessed manually (5 new RED→GREEN; meaningful asserts) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | N/A — disabled; rework comments accurate (verified inline) |
| 6 | reviewer-type-design | No | Skipped | disabled | N/A — disabled; `target?: string` addition + `Opposition` use assessed manually |
| 7 | reviewer-security | Yes | findings | 2 | confirmed 2 (both non-blocking/pre-existing), dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | No | Skipped | disabled | N/A — disabled; rework is minimal (no over-engineering) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | N/A — disabled; lang-review rules enumerated manually (see Rule Compliance) |

**All received:** Yes (3 enabled specialists returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 0 confirmed blocking, 5 confirmed non-blocking, 1 fix-suggestion dismissed (with rationale), 1 deferred (pre-existing flake)

## Reviewer Assessment

**Verdict:** APPROVED

R2 re-review of the GREEN rework. Both R1 HIGH blockers are closed, verified end-to-end against the source —
not just by green tests. No new Critical/High introduced. The rework is minimal, well-commented, and each fix is
pinned by a RED→GREEN test (5 new across the two repos). The five new non-blocking findings are edge/consistency
items routed to follow-ups; none reopen a blocker or warrant another round-trip.

**Blocker closure (both confirmed by every specialist + independent source read):**
- **HIGH #1 — Attack must name a target** (`FateConflictSurface.tsx`): `FateActionInput` now carries `target?: string`;
  the attack verb dispatches `target` from an opponent-side `conflict.participants` entry (`activeTarget = target ||
  opponents[0]?.name || ""`) with a `fate-target-select` picker when several. `_resolve_attack`'s `commit.target is
  None` loud-raise (fate_conflict.py:500) is no longer hit on the happy path. Pinned by 3 new UI tests (target is an
  opponent, never the self; the freeform rider survives). `App.handleFateAction` already forwarded `target` — no App change.
- **HIGH #2 — Unaffordable invoke returns a typed error** (`fate_action.py:121`): `except FateConflictError` →
  `except (FateConflictError, FateEconomyError)`. Verified the hierarchy directly: both are sibling `ValueError`
  subclasses (`fate.py:43`, `fate_conflict.py:61`), so the sibling was genuinely uncaught before. Pinned by the
  typed-error RED + the `test_affordable_invoke_still_resolves_to_a_roll` GREEN guard (no over-catch).
- **LOW (folded) — empty-flourish guard** (`fate_conflict.py:763`): the narrator-hint append is now gated on the
  non-empty *sanitized* rider, so an all-injection `player_action` that sanitizes to "" no longer emits a contentless
  "(flourish):" line.

**Data flow traced (attack happy path, the dead verb from R1):** player picks an opponent in `fate-target-select` →
clicks Attack → `dispatch("attack")` spreads `{ target: activeTarget }` → `App.handleFateAction` → `FATE_ACTION` over
WS (`target: "The Fat Man"`) → `FateActionHandler` → `dispatch_fate_action` seals + rolls → `_resolve_attack` finds the
target's Fate sheet and resolves shifts/absorption/taken-out. **The attack now lands.** Safe because the target is a
validated seated-creature name; a non-matching/empty target terminates in a typed `fate_dispatch_error` (no crash, no
half-mutated escape) — the same graceful rejection HIGH #2 established.

**Pattern observed:** the broadened catch mirrors the existing `FateConflictError` rejection shape exactly — consistent
typed-error handling at the handler seam (`fate_action.py:121`). The UI target-derivation mirrors the existing
`activeSkill` default-first idiom (`FateConflictSurface.tsx:106`) — consistent, minimal.

**Error handling:** server-side guards fail loud correctly (`_resolve_attack` raises on a missing/sheet-less target);
the handler now translates BOTH sibling domain errors into the typed client rejection. Residual `me=null → skill:''`
and `opponents=[] → target:''` paths are stale-state-race edges that now degrade to graceful typed errors — deferred,
non-blocking.

### Rule Compliance (lang-review: python.md + typescript.md — rework delta, enumerated)

- **python #1 silent exception swallowing:** the broadened `except (FateConflictError, FateEconomyError)` narrows to
  two named sibling domain errors and returns a *loud typed* rejection (logged `warning` + `ERROR` message) — NOT a
  bare/silent swallow — COMPLIANT. Correctly does NOT catch `NotImplementedError` (the no-d20-surface stubs must fail
  loud per No Silent Fallbacks — edge-hunter's suggestion to add it is DISMISSED on that rule).
- **python #6 test quality:** the 2 new server tests assert message type + fate-domain code + roll-reachability —
  meaningful, non-vacuous — COMPLIANT (preflight GREEN).
- **python #3 type annotations / #8 deserialization / #9 async:** the rework adds no new boundary, no new async, no
  new deserialization — COMPLIANT.
- **typescript #1 type-safety escapes:** `target?: string` is a plain optional field; no `as`/`any` added — COMPLIANT.
- **typescript #4 null/undefined:** `activeTarget = target || opponents[0]?.name || ""` uses `||` intentionally
  ("" = unset, parallel to `activeSkill`) — acceptable; the residual `""`-on-no-opponents edge is non-blocking (typed
  server rejection) — COMPLIANT.
- **typescript #6 React/JSX:** `key={o.name}` (not index); the `fate-target-select` rendered only when
  `opponents.length > 0`; no `dangerouslySetInnerHTML` — COMPLIANT.
- **typescript #10 input validation:** opponent names render as auto-escaped React children; `target` is
  server-validated against seated creatures — COMPLIANT.

### Dispatch-tag coverage
- **[EDGE]** — confirmed 3, all non-blocking: (1) `target:""` on `opponents.length===0` → graceful typed rejection
  (medium; recommend the one-line `verb==="attack" && activeTarget` guard as a fold-in — same class as the deferred
  `me=null` finding); (2) `NotImplementedError` not caught — latent/unreachable from the 4 actions, and catching it
  would *violate* No Silent Fallbacks, so the fix-suggestion is **dismissed**, observation deferred; (3) `[blocked]`
  rider passes the non-empty guard — pre-existing sanitizer behavior, arguably a desirable GM-visible injection marker.
- **[SEC]** — confirmed 2, both non-blocking/pre-existing: (a) `payload.target` stored unsanitized at the seal site
  (`fate_conflict.py:834`) and interpolated into `narrator_hints` — verified this is **pre-existing Story 118-8 code on
  develop** (not in the 118-6 diff), structurally identical to `commit.actor` (already unsanitized in the same hint
  strings), and gated by server-side seated-creature name validation before it reaches the prompt; routed to the same
  family as **backlog 118-9** (seal-site sanitization). (b) `FateEconomyError` message interpolated into the
  client-facing error — Low; mirrors the unchanged pre-existing `FateConflictError` path (internal config names, not
  secrets). Central ADR-047 concern (the new `player_action` rider) IS correctly sanitized at its seam.
- **[SILENT]** (disabled — assessed manually): the rework swallows nothing — it adds a *loud* typed rejection; the
  `me=null`/`target=""` client paths are deferred silent-fallback edges, unchanged by the rework.
- **[TEST]** (disabled — assessed manually): preflight GREEN; the 2 server + 3 ui rework tests are RED-verified and
  assert the exact fixed behavior (typed error, opponent target, rider-survives). Adequate.
- **[DOC]** (disabled — assessed manually): the new comments are accurate and cite the governing reason (sibling
  ValueError; ADR-047 seam; SRD reroll-replaces). No stale/misleading comments in the delta.
- **[TYPE]** (disabled — assessed manually): `target?: string` cleanly completes the `FateActionInput` contract the
  attack verb required (the root TYPE gap from R1 is closed).
- **[SIMPLE]** (disabled — assessed manually): minimal — a one-line catch broadening, a derived `activeTarget`, a
  gated select. No over-engineering.
- **[RULE]** (disabled — assessed manually): see Rule Compliance above — no violations; one edge-hunter fix-suggestion
  dismissed precisely *because* it would breach a project rule (No Silent Fallbacks).

### Devil's Advocate

Assume the rework is still broken. The R1 catastrophe was the dead Attack verb — so attack it again. A player on their
last fate point invokes for +2, the server debits it, and the still-in-flight FATE_STATE shows the spent point as
available; they Invoke again and Attack. Before: `FateEconomyError` escaped uncaught — a session error every table
hits. Now: the handler catches the sibling and returns `FATE_ACTION rejected: …` with a fate code. I traced the class
graph to be sure the sibling is real (not a subclass that was already caught) — it is. The GREEN guard proves a
*payable* invoke still reaches the roll, so the broadening didn't turn into a swallow-everything net.

Next, the confused/stressed case: a conflict ends server-side, the client hasn't updated, and the player clicks Attack
with an empty opponent list. `activeTarget` is `""`; App's `?? null` doesn't coerce `""` to null, so the server gets
`target:""`, slips past `is None`, and `find_creature_core("")` raises — now caught, returning a typed rejection
rather than a crash. Mildly confusing message ("'' has no Fate sheet" vs "must name a target"), but no crash and no
half-mutated escape. ADR-116 keeps this off the happy path. A one-line UI guard would make the message honest; it's a
fold-in, not a blocker.

The malicious case: pure injection in the flourish now sanitizes to "" and is suppressed; an override-preamble rider
sanitizes to "[blocked]" and shows as a neutralized marker (informative, not an injection vector). The `target` string
can only reach the narrator prompt if it exactly matches a real seated creature — the same trust level as the actor's
own name, which already flows there. Nothing here is shippable-blocking. The two disqualifying R1 defects are gone, and
nothing new rises to their level. **APPROVED.**

**Handoff:** To SM (Themis the Just) for finish-story.