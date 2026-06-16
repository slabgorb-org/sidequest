---
story_id: "118-7"
jira_key: ""
epic: "118"
workflow: "tdd"
---
# Story 118-7: F3g — wire the 4dF roll surface end-to-end: FATE_ROLL into the FatePanel + MP broadcast (carries 118-3 findings)

## Story Details
- **ID:** 118-7
- **Jira Key:** (none — no Jira integration for this project)
- **Workflow:** tdd
- **Stack Parent:** 118-3 (status: done, just pulled to develop)
- **Repos:** server, ui

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-16T12:35:41Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-16T11:53:30.564704+00:00 | 2026-06-16T11:55:57Z | 2m 26s |
| red | 2026-06-16T11:55:57Z | 2026-06-16T12:12:10Z | 16m 13s |
| green | 2026-06-16T12:12:10Z | 2026-06-16T12:27:59Z | 15m 49s |
| review | 2026-06-16T12:27:59Z | 2026-06-16T12:35:41Z | 7m 42s |
| finish | 2026-06-16T12:35:41Z | - | - |
| red | - | 2026-06-16T12:12:10Z | unknown |
| green | 2026-06-16T12:12:10Z | 2026-06-16T12:27:59Z | 15m 49s |
| review | 2026-06-16T12:27:59Z | 2026-06-16T12:35:41Z | 7m 42s |
| finish | 2026-06-16T12:35:41Z | - | - |
| green | - | 2026-06-16T12:27:59Z | unknown |
| review | 2026-06-16T12:27:59Z | 2026-06-16T12:35:41Z | 7m 42s |
| finish | 2026-06-16T12:35:41Z | - | - |
| review | - | 2026-06-16T12:35:41Z | unknown |
| finish | 2026-06-16T12:35:41Z | - | - |
| finish | - | - | - |

## Sm Assessment

**Scope (routing only — no implementation planning):** Wire the already-built 4dF roll surface into the live client. 118-3 shipped the infrastructure (dF Fudge die in dice-lib, server `FateRollPayload`/`FATE_ROLL` message + handler emit, `FateDiceTray` + `isFateRoll` guard); 118-2 shipped the host (`FatePanel.tsx`, `FATE_STATE` routing at `useStateMirror.ts:251`, `fateState` slice, `FateWidget`). The gap is the wire: mount `FateDiceTray` in the FatePanel (gate on `gameState.fateState != null`) and ensure MP broadcast fan-out so every seat sees the roll.

**Setup verification:**
- Pulled all repos before setup — confirmed 118-3, 118-2, and 118-10 all merged to develop (118-10 landed in another clone during this session; re-scanned backlog before selecting).
- Feature branch `feat/118-7-f3g-wire-fate-roll-surface` cut off latest develop in both `sidequest-server` and `sidequest-ui`.
- Session at orchestrator root; context at `sprint/context/context-story-118-7.md`.

**Watch-outs for downstream agents:**
- Ignore the stale 118-3 session note claiming "F3b absent" — that was clone-drift; FatePanel exists on develop.
- `sidequest-ui` build runs `tsc -b` (checks test files); run `npm install` before diagnosing build breaks (stale node_modules → phantom d3-dag error).
- This is wiring, not a new dock tab — FatePanel/FateWidget already exist, so the GameBoard widget-tab quartet doesn't apply.

**Routing:** tdd (phased). Next agent → **TEA** for RED phase (failing tests for the client mount + MP broadcast wiring).

## TEA Assessment

### Red Phase (test design)

**Tests Required:** Yes
**Status:** RED (failing — ready for Agent Smith / Dev)

**Test Files:**
- `sidequest-server/tests/server/test_fate_roll_broadcast_wire_118_7.py` — NEW. AC2/AC3: drives the real `FateActionHandler` against a real `SessionRoom` (two attached outbound queues) and asserts the resolved 4dF roll is **broadcast** to both seats (peer + actor), is **stamped with the acting `player_id`**, and is NOT also returned (no sender-only double-deliver). Concession broadcasts nothing.
- `sidequest-server/tests/server/test_fate_action_handler_wiring.py` — UPDATED. The two behavior tests were rewritten from the old sender-only **return** contract to the new **broadcast** contract (the registry-membership test is unchanged).
- `sidequest-ui/src/hooks/__tests__/useStateMirror.fateRoll.test.ts` — NEW. AC1 routing: FATE_ROLL (via `isFateRoll`) threads onto state as `latestFateRoll` (event — latest wins, starts null), with a No-Silent-Fallbacks drop of a malformed roll (missing `dice`).
- `sidequest-ui/src/components/__tests__/FatePanel.fateRoll.test.tsx` — NEW. AC1 mount + the epic's required **paired ruleset-gate negative** (mounts on fate-pack+roll; absent with no roll / non-fate ruleset / no fate pack) + the AC4 zero-glyph guard (`+ + 0 −`).
- `sidequest-ui/src/components/GameBoard/__tests__/GameBoard-fate-roll.test.tsx` — NEW. The mandatory **wiring test**: the roll threads end-to-end through GameBoard → FateWidget → FatePanel → FateDiceTray (activate the Fate tab, assert the tray mounts), with the paired negative (sheet but no tray before a roll arrives).

**Tests Written:** 17 new + 2 updated across 5 files, covering AC1 (routing + mount + wiring), AC2 (broadcast fan-out), AC3 (player_id attribution), AC4 (UI zero-glyph). **RED counts:** server 5 failed / 3 passed (keepers: registry + both concede); ui 8 failed / 4 passed (the paired negatives are correct-by-construction and MUST stay green through GREEN).

**Intended GREEN contract (design guidance for Dev):**
- Server: in `handlers/fate_action.py`, when `result.action_roll is not None`, build `FateRollMessage(payload=payload_out, player_id=acting_player_id)` and `sd._room.broadcast(msg, exclude_socket_id=None)` (mirror DICE_RESULT at `websocket_session_handler.py:1286`) — then `return []`. `exclude_socket_id=None` already reaches the actor, so do NOT also return the message. Fix the misleading "broadcasts the same result to the table" comment (lines 127-128) — it described an unimplemented behavior this story implements. Add/extend an OTEL span for the broadcast emit (OTEL Observability Principle).
- UI: add `latestFateRoll: FateRollPayload | null` to `ClientGameState` + `EMPTY_GAME_STATE` (default `null`); route FATE_ROLL in `useStateMirror.ts` (guard on a valid `dice` tuple, mirror the FATE_STATE boundary guard); thread `latestRoll` + a `ruleset` (="fate" when `fateData != null`) down App → GameBoard → FateWidget → FatePanel, which mounts `<FateDiceTray roll={latestRoll} ruleset={ruleset} />` only when `data != null` AND `latestRoll != null`.

### Rule Coverage

| Rule (project) | Test(s) | Status |
|----------------|---------|--------|
| No Source-Text Wiring Tests (server CLAUDE.md) | broadcast asserted via real `SessionRoom` fan-out + queue inspection, never a `read_text()`/grep | RED |
| Every Test Suite Needs a Wiring Test | `GameBoard-fate-roll.test.tsx` (production render path) + server handler end-to-end | RED |
| Verify Wiring, Not Just Existence | tray reached through GameBoard→FateWidget→FatePanel; FateDiceTray/isFateRoll gain a production consumer | RED |
| No Silent Fallbacks | `useStateMirror.fateRoll` drops malformed roll; handler returns `[]` (no silent double-path) | RED |
| Ruleset-gate (epic 118 — paired negative required) | FatePanel + GameBoard negatives (no roll / non-fate / no fate pack) | PASS (guard — stays green) |
| Player-UI legibility mandate (AC4, Sebastien/Jade) | zero face renders `0`, not blank | RED |

**Self-check:** 0 vacuous assertions — every test asserts a specific value, recipient, or DOM presence/absence. No `let _ =`, no `assert(true)`, no always-None checks. The 4 passing UI negatives are intentional gate guards, not vacuous.

**Handoff:** To Agent Smith (Dev) for GREEN implementation.

## Dev Assessment

**Implementation Complete:** Yes — implemented exactly the TEA-specified GREEN contract.

**Files Changed:**
- `sidequest-server/sidequest/handlers/fate_action.py` — when an action rolls, build `FateRollMessage(payload=payload_out, player_id=acting_player_id)` and `sd._room.broadcast(msg, exclude_socket_id=None)` (mirror DICE_RESULT), then `return []` (no sender-only double-deliver). Loud `logger.error` guard if `_room` is None (No Silent Fallbacks). Emit a `fate_roll.broadcast_emitted` OTEL watcher event with the recipient count (lie-detector). Fixed the misleading "broadcasts the same result to the table" comment.
- `sidequest-server/tests/server/test_fate_action_auth_bypass.py` — attached a bare MP `SessionRoom` to the `_two_pc_session` fixture (collateral: the overcome roll now broadcasts; these tests assert the sealed-commit ledger, not delivery).
- `sidequest-ui/src/providers/GameStateProvider.tsx` — `latestFateRoll: FateRollPayload | null` on `ClientGameState` + `EMPTY_GAME_STATE` (default null).
- `sidequest-ui/src/hooks/useStateMirror.ts` — route FATE_ROLL into `latestFateRoll` (event; latest wins) with a dice-tuple boundary guard (drops malformed rolls).
- `sidequest-ui/src/components/FatePanel.tsx` — `latestRoll` + `ruleset` props; mounts `<FateDiceTray>` when a roll has arrived (FateDiceTray self-gates on `ruleset==="fate"`).
- `sidequest-ui/src/components/GameBoard/widgets/FateWidget.tsx` + `GameBoard.tsx` + `App.tsx` — thread the roll + ruleset App → GameBoard → FateWidget → FatePanel.

**Tests:** GREEN.
- Server fate suite (handler + broadcast + auth-bypass + dispatch + projection + telemetry + integration): **107+ passed, 0 failed** at `-n0`.
- UI full suite: **2273 passed, 0 failed**; `tsc -b` clean; ESLint clean on changed files.
- Pre-existing failures: the full server suite shows ~85–91 failures in WWN combat / spellcasting / dead-premise integration tests — **stash-verified present at the branch base** (disjoint from this story; flaky under `-n auto`). See the Dev finding below. Not introduced by 118-7.

**Branch:** `feat/118-7-f3g-wire-fate-roll-surface` (pushed, both repos).

**Handoff:** To verify (The Architect) / review (The Merovingian).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean (GREEN) | 0 smells; 85 tests pass | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — covered by Reviewer's own `[EDGE]` analysis |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — covered by Reviewer's own `[SILENT]` analysis |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — covered by Reviewer's own `[TEST]` analysis |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — covered by Reviewer's own `[DOC]` analysis |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — covered by Reviewer's own `[TYPE]` analysis |
| 7 | reviewer-security | Yes | clean | 0 violations, 1 low obs | confirmed 0, deferred 1 (defense-in-depth) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — covered by Reviewer's own `[SIMPLE]` analysis |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — covered by Reviewer's own `[RULE]` analysis |

**All received:** Yes (2 enabled subagents returned — preflight + security; 7 disabled via `workflow.reviewer_subagents` and covered by the Reviewer's own analysis)
**Total findings:** 0 confirmed blocking, 1 dismissed (with rationale), 2 deferred (defense-in-depth dice-value validation; AC4 dice-lib + AC5 already raised by TEA/Dev)

## Reviewer Assessment

**Verdict:** APPROVED

The change is a faithful, minimal wiring of an already-built surface (FateDiceTray / FateRollMessage / isFateRoll), exactly to the TEA-specified contract. Both enabled specialists returned clean; my own pass covering the disabled lenses found only Low observations. No Critical/High.

**Observations (≥5, tagged):**
- `[PRE]` Preflight GREEN — 85 story-scoped tests pass (49 server + 36 ui), ruff/eslint/`tsc -b` clean, 0 code smells. The full-suite WWN/spellcasting failures are pre-existing (stash-verified by Dev) and correctly excluded from the story scope.
- `[SEC]` **VERIFIED** server-authenticated attribution — `FateRollMessage(payload=payload_out, player_id=acting_player_id)` (fate_action.py:136) where `acting_player_id = sd.player_id` (line 68, the Cf-Access identity); a mismatching inbound `msg.player_id` is detected and discarded at lines 70-90. A spoofed inbound id cannot stamp the broadcast with the victim's identity. Complies with ADR-119. (Security subagent: 1 instance, 0 violations.)
- `[SEC]` **VERIFIED** perception firewall intact — the broadcast `FateRollPayload` carries only engine-computed public mechanical output (dice/roll_total/ladder/opposition/shifts/tier); no character-sheet internals or per-player hidden state ride along. Complies with ADR-104/105. (Security: 0 violations.)
- `[SILENT]` **VERIFIED** loud-fail, not silent drop — `if room is None: logger.error("fate.roll.broadcast_no_room …"); return []` (fate_action.py) surfaces the programming-error at ERROR level; the UI boundary guard uses `console.error(...)` + `continue` (useStateMirror.ts). No swallowed errors. Complies with No Silent Fallbacks.
- `[EDGE]` (deferred, non-blocking) — the UI guard validates `dice` is an array of length 4 (`!Array.isArray(p.dice) || p.dice.length !== 4`) but not that each face ∈ {-1,0,1}. A corrupted face renders a wrong glyph (`faceGlyph` degrades any out-of-range value to `"0"`) but cannot crash, exfiltrate, or escalate. Defense-in-depth gap; the server always emits valid faces via `build_fate_roll_payload`. Flagged independently by both the security subagent and my own analysis.
- `[DOC]` **VERIFIED** comment corrected — the prior misleading "broadcasts the same result to the table" comment (which described an *unimplemented* behavior) was replaced with an accurate F3g broadcast comment that matches the code. Net documentation improvement.
- `[TYPE]` `const p = msg.payload as unknown as FateRollPayload` (useStateMirror.ts) — a double-cast (typescript.md #1), but it is the established validated-boundary idiom used identically by the FATE_STATE handler in the same file, immediately followed by runtime `dice`-tuple validation. **Dismissed** — not a new violation; matches the codebase's wire-boundary pattern.
- `[TEST]` **VERIFIED** non-vacuous tests — broadcast/attribution asserted by inspecting real `SessionRoom` queues; mount asserted by DOM presence; the epic's required paired ruleset-gate negatives are present; the mandatory wiring test (`GameBoard-fate-roll.test.tsx`) drives the full production render path. No truthy-only or always-None assertions.
- `[SIMPLE]` `ruleset={fateData != null ? "fate" : ""}` (GameBoard.tsx) — the `: ""` branch is unreachable (the Fate tab only renders when `fateData != null`) but is a harmless defensive default. **Dismissed** — Low, not worth churn.
- `[RULE]` **VERIFIED** OTEL Observability Principle — the change adds a `fate_roll.broadcast_emitted` watcher event with the recipient count, the GM-panel lie-detector for "did the roll actually reach the table." Required by CLAUDE.md and satisfied.

**Data flow traced:** player FATE_ACTION → `acting_player_id = sd.player_id` (server-auth) → `dispatch_fate_action` → `build_fate_roll_payload` → `FateRollMessage(player_id=acting_player_id)` → `room.broadcast(exclude_socket_id=None)` → every seat's `out_queue` → WS → `useStateMirror` FATE_ROLL branch (dice-validated) → `latestFateRoll` → App → GameBoard → FateWidget → FatePanel → FateDiceTray. Safe: attribution is server-derived; the payload is public; the broadcast reaches the actor too (so the handler returns `[]` — no double-deliver).

**Pattern observed:** mirrors the existing snapshot-slice idiom (FATE_STATE / QUESTS / RELATIONSHIPS) for the new event-slice, and the DICE_RESULT broadcast idiom on the server (`exclude_socket_id=None`) — consistent, not novel. `FatePanel.tsx:171` conditional mount; `GameBoard.tsx:586` thread.

**Error handling:** `room is None` → loud `logger.error` + `[]` (fate_action.py); malformed FATE_ROLL → `console.error` + drop (useStateMirror.ts); empty/null `latestRoll` → no tray mount (FatePanel.tsx:171). Null inputs handled at every hop.

### Rule Compliance

| Rule | Instances checked | Verdict |
|------|-------------------|---------|
| No Silent Fallbacks | room-None guard (loud `logger.error`); UI malformed guard (`console.error`) | Compliant |
| Wire Up What Exists / Verify Wiring | FateDiceTray + isFateRoll + FateRollMessage gain production consumers; GameBoard wiring test proves reachability | Compliant |
| Every Test Suite Needs a Wiring Test | `GameBoard-fate-roll.test.tsx` (production render path) | Compliant |
| No Source-Text Wiring Tests | broadcast via real `SessionRoom` queue inspection; UI via DOM — no source greps | Compliant |
| OTEL Observability Principle | `fate_roll.broadcast_emitted` watcher event with recipient count | Compliant |
| ADR-119 (server-auth identity sole source) | `player_id=acting_player_id` from `sd.player_id` (1 instance) | Compliant |
| ADR-104/105 (perception firewall) | broadcast payload is public mechanical data only | Compliant |
| ADR-047 (sanitization) | no new player free-text reaches any prompt | Compliant |
| Player-UI legibility (AC4) | zero Fudge face renders `"0"` in the readout | Compliant |
| ADR-143 (Bind the Ruleset, Don't Balance It) | Fate UI wiring; no native/WWN mechanic tuned or gated | N/A — not engaged |
| python.md #4 (log-level correctness) | error path `logger.error`, success `logger.info` | Compliant |

### Devil's Advocate

Arguing this is broken: **Stale-roll persistence.** `latestFateRoll` is never cleared — a roll resolved on turn 1 remains mounted in the FatePanel through turn 50 until the next roll arrives. A player glancing at the panel mid-scene could misread an old roll as the current outcome; there is no timestamp or turn anchor. Counter: this matches the DICE_RESULT persistence model and the AC's explicit "latest roll wins" semantics; the surface is a panel artifact, not a live feed. Mild UX risk, non-blocking.

**Broadcast-to-non-participants.** The roll fans out to *every* seat, including players not seated in the Fate conflict. Is that the Guitar-Solo anti-pattern (the table watching a screen they can't touch)? No — the SOUL Guitar Solo doctrine wants exactly this: "keep the soloist reachable, give everyone a part." Seeing the soloist's roll is inclusion, not exclusion. Safe.

**Concurrency.** Under the submit-and-wait barrier two PCs can resolve near-simultaneously; `latestFateRoll` becomes whichever FATE_ROLL the mirror processes last, so a player may briefly see a peer's roll rather than their own. The message carries `player_id`, so a future "show only my roll" filter is possible, but the AC mandates broadcast-all and the mirror processes in arrival order — deterministic, non-corrupting. Non-blocking.

**Version skew.** The `as unknown as FateRollPayload` cast trusts wire fields beyond `dice`; a payload missing `ladder_name`/`tier` would render the literal "undefined" rather than crash. The dice guard is the crash-guard; the rest is cosmetic. **Malicious input.** A crafted FATE_ROLL with out-of-range face values renders a wrong glyph (degrades to "0") — no XSS (React escapes text), no crash, no privilege path. **room is None in production** would silently vanish the roll from players (only the operator log shows it), but the room is invariantly set in Playing state — a defensive path, not a live one. Nothing the devil's advocate raises rises above Low.

**Handoff:** To SM (Morpheus) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

No upstream findings.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): AC4's recommended end state (die + text both render `0`) is only partly satisfiable in the declared `server,ui` scope. The UI side is already correct (`FateDiceTray.faceGlyph(0)` returns `"0"`, now pinned by a test); the DIE side lives in a THIRD repo — `../dice-lib/src/dF.ts:22-23` labels the two blank Fudge faces `label: ""`. Affects `../dice-lib/src/dF.ts` (change the blank-face `label` from `""` to `"0"` + a dice-lib test). Out of this story's declared repos. Mitigant: the tray currently renders the dice with `throwParams={null}` (idle/decorative — they do NOT animate to the rolled faces), so the die-label discrepancy is not player-visible yet; it becomes visible only once AC5 lands. Recommend folding the dF.ts label fix into the AC5 / throw-params follow-up (which also touches dice-lib), or a 1-line dice-lib chore — Operator's call on scope. *Found by TEA during test design.*
- **Improvement** (non-blocking): AC5 (carry `throw_params`/`seed` on FATE_ROLL so the 3D Fudge dice animate to the rolled faces) is explicitly a stretch goal and is NOT covered by RED tests — deferred to keep GREEN focused on the AC1–AC4 spine. It pairs naturally with the dice-lib dF.ts fix above. Affects `sidequest-server` (FateRollPayload + projection) and `sidequest-ui` (FateDiceTray throwParams). *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): the full `sidequest-server` suite has ~85–91 failures in WWN combat / spellcasting / dead-premise integration tests (`test_wwn_shock_kill_observability.py`, `test_106_2_wwn_defensive_reprisal.py`, `test_confrontation_payload_spellcasting_102_2.py`, `test_102_4_dead_premise.py`). **Pre-existing on the branch base** — stash-verified (stash my `sidequest/` changes → same files still fail), disjoint from this story's fate-only change, and flaky under `-n auto` (consistent with the in-flight WWN-owns-the-round refactor, ADR-114/-143 *partial*, epic 108). Affects the WWN combat path, not `fate_action.py`. Flagged so the Reviewer/SM are not alarmed by a red full-suite run and so the WWN-combat owners can triage. *Found by Dev during implementation.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

5 deviations

- **Rewrote two existing handler tests to the new broadcast contract**
  - Rationale: those tests encoded the exact contract this story replaces; left as-is they would fail after GREEN for the wrong reason. Updating them in RED makes the suite green-on-correct-implementation.
  - Severity: minor
  - Forward impact: none (the new `test_fate_roll_broadcast_wire_118_7.py` owns the fan-out + attribution detail).
- **AC5 (throw_params/seed replay) intentionally untested**
  - Rationale: explicitly a stretch goal; writing a failing test would block GREEN on out-of-spine work. Captured as a Delivery Finding (Improvement) instead, paired with the dice-lib dF.ts follow-up.
  - Severity: minor
  - Forward impact: AC5 + the dF.ts label fix should land together (both touch dice-lib).
- **Broadcast tests set `_room` on BOTH session and session_data**
  - Rationale: keep the behavior test refactor-stable across the `sd._room` vs `session._room` choice.
  - Severity: trivial
  - Forward impact: none.
- **Updated an existing test (test_fate_action_auth_bypass.py) not in TEA's list**
  - Rationale: collateral from the delivery-contract change; the production `_SessionData` always carries `_room`, so only the test fake needed it. No production behavior weakened.
  - Severity: minor
  - Forward impact: none.
- **Added a loud `_room is None` guard rather than a silent drop**
  - Rationale: honor No-Silent-Fallbacks without inventing a sender-only fallback that would resurrect the bug this story fixes.
  - Severity: trivial
  - Forward impact: none.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Rewrote two existing handler tests to the new broadcast contract**
  - Spec source: context-story-118-7.md, AC2
  - Spec text: "FATE_ROLL is currently delivered sender-only via per-socket out_queue … Broadcast via session._room.broadcast like DICE_RESULT so peers see the acting PC's roll."
  - Implementation: `test_fate_action_handler_wiring.py::test_handler_drives_dispatch_end_to_end` and `::test_handler_concede_emits_no_roll` previously asserted the sender-only RETURN contract (`out[0] is FateRollMessage`). They now attach a real `SessionRoom` and assert broadcast delivery + an empty return. The registry-membership test is unchanged.
  - Rationale: those tests encoded the exact contract this story replaces; left as-is they would fail after GREEN for the wrong reason. Updating them in RED makes the suite green-on-correct-implementation.
  - Severity: minor
  - Forward impact: none (the new `test_fate_roll_broadcast_wire_118_7.py` owns the fan-out + attribution detail).
- **AC5 (throw_params/seed replay) intentionally untested**
  - Spec source: context-story-118-7.md, AC5
  - Spec text: "Stretch: Throw Params / Seed on FATE_ROLL … so the 3D Fudge dice animate to the actual rolled faces."
  - Implementation: no RED tests written for AC5.
  - Rationale: explicitly a stretch goal; writing a failing test would block GREEN on out-of-spine work. Captured as a Delivery Finding (Improvement) instead, paired with the dice-lib dF.ts follow-up.
  - Severity: minor
  - Forward impact: AC5 + the dF.ts label fix should land together (both touch dice-lib).
- **Broadcast tests set `_room` on BOTH session and session_data**
  - Spec source: context-story-118-7.md, AC2 (Technical Approach)
  - Spec text: "broadcast FATE_ROLL via `session._room.broadcast()`"
  - Implementation: the fake session sets `_room` on both `session` and `session._session_data` (production plumbs the SessionRoom onto both — `websocket_session_handler.py:284` + `session_state.py:207`), so the test does not couple to which attribute the GREEN handler reads.
  - Rationale: keep the behavior test refactor-stable across the `sd._room` vs `session._room` choice.
  - Severity: trivial
  - Forward impact: none.

### Dev (implementation)
- **Updated an existing test (test_fate_action_auth_bypass.py) not in TEA's list**
  - Spec source: context-story-118-7.md, AC2
  - Spec text: "Broadcast via session._room.broadcast … so peers see the acting PC's roll."
  - Implementation: the auth-bypass fixture `_two_pc_session` drove the handler with a roomless SimpleNamespace; the overcome action rolls, so the new broadcast path raised `AttributeError` on `sd._room`. Attached a bare MP `SessionRoom` to the fixture (no queues — these tests assert the sealed-commit ledger, not delivery).
  - Rationale: collateral from the delivery-contract change; the production `_SessionData` always carries `_room`, so only the test fake needed it. No production behavior weakened.
  - Severity: minor
  - Forward impact: none.
- **Added a loud `_room is None` guard rather than a silent drop**
  - Spec source: server CLAUDE.md, "No Silent Fallbacks"
  - Spec text: "If something isn't where it should be, fail loudly."
  - Implementation: when `result.action_roll` exists but `sd._room is None`, the handler logs `logger.error("fate.roll.broadcast_no_room …")` and returns `[]` instead of silently dropping the roll. In Playing state `_room` is always set (slug-connect), so this is a defensive loud-fail, not a normal path.
  - Rationale: honor No-Silent-Fallbacks without inventing a sender-only fallback that would resurrect the bug this story fixes.
  - Severity: trivial
  - Forward impact: none.

### Reviewer (audit)
- **TEA — Rewrote two existing handler tests to the new broadcast contract** → ✓ ACCEPTED by Reviewer: the sender-only return contract is genuinely replaced by this story; updating the tests in RED is correct TDD, not test-fudging. The new `test_fate_roll_broadcast_wire_118_7.py` independently re-asserts the fan-out, so coverage strengthened, not weakened.
- **TEA — AC5 (throw_params/seed replay) intentionally untested** → ✓ ACCEPTED by Reviewer: AC5 is explicitly a stretch goal; deferring it (with a tracked Improvement finding) is sound and keeps GREEN focused on the AC1–AC4 spine.
- **TEA — Broadcast tests set `_room` on BOTH session and session_data** → ✓ ACCEPTED by Reviewer: matches production plumbing (`websocket_session_handler.py:284` + `session_state.py:207`) and keeps the behavior test refactor-stable. Trivial, sound.
- **Dev — Updated an existing test (test_fate_action_auth_bypass.py) not in TEA's list** → ✓ ACCEPTED by Reviewer: legitimate collateral from the delivery-contract change (the overcome roll now broadcasts). Production `_SessionData` always carries `_room`; only the test fake needed it. No production behavior weakened, and the auth-bypass security assertions (commit ledger) are unchanged and still pass.
- **Dev — Added a loud `_room is None` guard rather than a silent drop** → ✓ ACCEPTED by Reviewer: honors No Silent Fallbacks; the reviewer-security subagent independently confirmed the `logger.error` + `[]` path is a loud operator-surfaced fail, not a silent swallow.
- No UNDOCUMENTED deviations found — every spec divergence in the diff is logged by TEA or Dev.

### Reviewer (code review)
- **Improvement** (non-blocking): the UI FATE_ROLL boundary guard (`useStateMirror.ts`) validates that `dice` is a 4-element array but not that each face is in `{-1, 0, 1}`. A corrupted/replayed payload with a valid-length but out-of-range face renders a wrong glyph (`FateDiceTray.faceGlyph` degrades any out-of-range value to `"0"`) — it cannot crash, exfiltrate, or escalate. Defense-in-depth only; the server always emits valid faces via `build_fate_roll_payload`. Optional hardening: tighten the guard to `p.dice.every(d => d === -1 || d === 0 || d === 1)`. Affects `sidequest-ui/src/hooks/useStateMirror.ts` (FATE_ROLL branch). Independently flagged by the reviewer-security subagent. *Found by Reviewer during code review.*
- Concur with the TEA/Dev deferrals: the AC4 dice-lib `dF.ts` blank-face label and AC5 throw-params replay are correctly out of `server,ui` scope and should land together as a dice-lib follow-up (no objection). *Reviewed by Reviewer during code review.*