---
story_id: "126-7"
jira_key: ""
epic: "126"
workflow: "bdd"
---
# Story 126-7: Player 4dF roll is determinative

## Story Details
- **ID:** 126-7
- **Jira Key:** (none — SideQuest personal project, no Jira)
- **Epic:** 126 — Fate Core playtest follow-ups
- **Workflow:** bdd (Behavior-Driven Development, phased)
- **Stack Parent:** none
- **Repos:** sidequest-server (develop), sidequest-ui (develop)

## Workflow Tracking
**Workflow:** bdd  
**Phase:** finish  
**Phase Started:** 2026-06-17T13:35:57Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-17T08:55:42.821213+00:00 | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

- **Gap** (non-blocking): Pre-existing failures outside this story's blast radius, confirmed not caused by 126-7. Server full suite: 85 failures, all in `integration/`/`genre/`/`cli/`/`game/` (WN/WWN combat, spell-cast, chargen, bestiary, live-content — content-tree-lag; representative cause `unknown beat_id 'committed_blow' for encounter 'combat' — available: []`). UI `npm run lint`: 1 pre-existing error in `src/components/Dashboard/source/useForensicSource.ts:61` (`react-hooks/set-state-in-effect`) plus a pre-existing `App.tsx:1647` exhaustive-deps warning — neither in this diff. *Found by Dev during the full-suite gate.*

### Reviewer (code review)

- **Gap** (non-blocking): The determinative-reroll UX is half-wired — an `invoke_mode='reroll'` arming spends a fate point but the thrower UI offers no re-throw, so the point is burned with no effect (ADR-148 §5 intends the client to re-throw). Affects `sidequest-ui/src/components/FateConflictSurface.tsx` + `sidequest-server/sidequest/server/dispatch/fate_conflict.py` (wire the post-result re-throw, or gate `reroll` mode off in the pre-throw invoke arming). Belongs with the interactive re-throw/defend UX in 126-8. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `FateThrowHandler` (and the mirrored `FateActionHandler`) return `[]` on the unreachable `room is None` programming-error path, giving the client no feedback. Affects `sidequest-server/sidequest/handlers/fate_throw.py:158` + `handlers/fate_action.py:154` (return an `_error_msg` so a player isn't left hanging if the invariant ever breaks). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): 8 pre-existing `ruff I001` import-sort errors in untouched fate test files (`test_fate_state_emit.py`, `test_fate_state_emit_wiring.py`, `test_fate_gear_model.py`, +5) — auto-fixable, batch separately. Affects `sidequest-server/tests/`. *Found by Reviewer (preflight) during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

**RED phase (TEA) — test-strategy refinements to the plan (no spec/ADR change):**

1. **Test home is `tests/game/ruleset/`, not `tests/ruleset/`.** The plan (Tasks
   2/3/4) names `tests/ruleset/`; that dir does not exist. All existing Fate
   resolution/projection/module/span tests live under `tests/game/ruleset/`, so
   the three new files were placed there. Dev: implement against those paths.

2. **Task 5 determinism spy runs on an UNCLOSED multi-PC barrier, not `_solo_combat`.**
   The plan's literal fixture (`_solo_combat` + `assert called["n"] == 0`) is a
   FALSE test: a solo barrier closes immediately and `run_fate_exchange` then
   seats the opponent and rolls NPC defenses (`_seat_opponent_commits`:321 /
   `_roll_defense`:259, both `roll_4df`) — so `roll_4df` WOULD be called and the
   assertion could never pass even after GREEN. The test instead holds the
   barrier open (a second PC has not committed), isolating the player's proactive
   roll so the "no roll_4df on the player path" invariant is asserted cleanly. A
   positive control (`test_legacy_none_path_still_server_rolls`) proves the spy is
   not vacuous.

3. **Task 3 OTEL test uses an explicit per-test tracer, not `set_tracer_provider`.**
   The plan's global-provider pattern is flaky under the parallel suite (OTel
   honors only the first `set_tracer_provider` per process). The test follows the
   established `tests/server/dispatch/test_fate_dispatch_routing.py::_otel()`
   pattern (pass `_tracer=` explicitly). Also added the NPC `source="server_rolled"`
   assertion the RED brief requires (the plan only asserted `player_thrown`).

4. **Task 4 builds its outcome via `resolve_action(rng)`, not `resolve_action_from_faces`,**
   so the projection test's RED isolates the new `throw_params=` kwarg (TypeError)
   rather than coupling to Task 2's missing symbol.

5. **Task 1 adds two paranoia tests beyond the plan:** roll-verb-only `Literal`
   rejection (concede must NOT validate as a throw) and a too-many-faces case.

### Dev (implementation)

- **FateConflictSurface roll verbs now mount the dF thrower (deferred send) instead of dispatching FATE_ACTION synchronously**
  - Spec source: plan 2026-06-17-fate-proactive-determinism-126-7.md, Task 8 Step 4; ADR-148 §2
  - Spec text: "roll verbs mount the tray and defer the send until settle; non-roll verbs send FATE_ACTION synchronously as today"
  - Implementation: clicking overcome/create_advantage/attack arms an `ArmedThrow` and mounts `FateDiceTray mode="thrower"`; on settle the tray's FateThrowPayload is merged with the armed invoke/freeform and emitted via a new `onFateThrow` prop (threaded App→GameBoard→surface). concede/compel_* unchanged on `onFateAction`. The pre-existing `FateConflictSurface.test.tsx` assertions that pinned roll-verb→onFateAction were updated to the new roll-verb→arm→throw→onFateThrow contract (the story changes that contract).
  - Rationale: physics-is-the-roll requires capturing the thrown faces before sending; a synchronous dispatch cannot carry faces. Required by the no-half-wired-features rule (FATE_THROW must be reachable in production).
  - Severity: minor
  - Forward impact: 126-8 adds a defend-mode mount to the same surface (FATE_DEFEND_REQUEST); the `armed`/thrower scaffolding is the seam it extends.

- **Corrected a pre-existing MessageType count drift in test_enums.py**
  - Spec source: tests/protocol/test_enums.py::test_message_type_complete_count
  - Spec text: "assert len(MessageType) == 56"
  - Implementation: bumped to 58 and documented BOTH the missed FATE_ROLL (story 118-7 added it without updating this count → 56→57) and the new FATE_THROW (57→58). Added a FATE_THROW wire-string test beside the FATE_ACTION one.
  - Rationale: the count was already wrong before this story (FATE_ROLL drift); adding FATE_THROW required correcting it to the true count. Leaving it at 57 would have failed on a number unrelated to this change.
  - Severity: trivial
  - Forward impact: none — the contract test now matches reality.

### Reviewer (audit)

- **TEA RED deviations 1–5** → ✓ ACCEPTED by Reviewer: sound test-strategy refinements. The `tests/game/ruleset/` path correction, the unclosed-barrier spy isolation (the solo `_solo_combat` assertion would genuinely be false — NPC seating/defense rolls `roll_4df`), the explicit-tracer OTEL pattern, the Task-4 outcome-isolation, and the two paranoia tests are all correct and improve on the plan's literal wording.
- **Dev deviation: FateConflictSurface roll-verb→thrower rewire + test updates** → ✓ ACCEPTED by Reviewer: required by physics-is-the-roll (a synchronous dispatch cannot carry faces) and the no-half-wired rule; matches ADR-148 §2 + plan Task 8 Step 4. The updated `FateConflictSurface.test.tsx` assertions correctly pin the new contract; concede/compel_* remain on `onFateAction` (verified in the .compel suite).
- **Dev deviation: MessageType count correction (56→58)** → ✓ ACCEPTED by Reviewer: the FATE_ROLL drift was genuinely pre-existing (documented + bumped honestly); the contract test now matches `len(MessageType)`.
- **UNDOCUMENTED (Reviewer-spotted):** the determinative-reroll model (ADR-148 §5) is only half-wired — the server-side "no re-roll, accounting only" landed, but the thrower UI offers no post-result re-throw, so an `invoke_mode='reroll'` arming spends a fate point with no effect. Dev's dispatch comment notes "reroll = accounting only" but did not flag the resulting UI resource-loss gap. Severity: M. Captured as the MEDIUM finding above + a non-blocking delivery finding for 126-8. Not a blocker (advanced non-default affordance; explicit ACs met; staged model documented in the ADR).

## Technical Context

**Problem:** Current Fate 4dF roll path is backwards. Server rolls and decides; FateDiceTray animates post-hoc. Story 125-4 failed to reconcile physics-thrown faces with the already-decided result, creating contradictions.

**Solution:** Make player Fate rolls determinative (physics-is-the-roll, ADR-074). Player throws 4 dF, faces settle, client reports faces + throw_params + seed. Server resolves from reported faces. NPC rolls stay server-side (roll_4df).

**Design-First:** Story explicitly mandates Architect design phase before code. Nail FATE_ACTION→throw→resolve sequence, new client→server message, and ADR-144/ADR-074 reconciliation note.

**Key Reuse:** 125-4's merged FateRollPayload throw_params/seed fields + dF '0' label stay. Tear out: 'server decides then animate' assumption in FateDiceTray + server-rolls-for-players path.

**Repos & Branches:**
- **sidequest-server:** `develop` → feat/126-7-fate-4df-determinative
- **sidequest-ui:** `develop` → feat/126-7-fate-4df-determinative

## Architect Design (design phase) — The Man in Black

**Formal decision:** `docs/adr/148-player-fate-roll-is-physics-is-the-roll.md` (ADR-148,
reconciles ADR-074 ↔ ADR-144). Read it first — this section is the implementation seam map.

### Load-bearing finding: mirror the LIVE d20 path (client-driven), not the story's literal 4-step sequence

ADR-074's "server requests a throw → client throws" round-trip is the *original Rust*
design, superseded 2026-05-02. The **live** d20 path is **client-driven**: selecting the
action builds the request locally, the tray throws, and a **single** `DICE_THROW` carries
both the action context (`beat_id`) and the authoritative `face[]`. We mirror *that*. So
the Fate flow is one client→server message (`FATE_THROW`), not a two-message handshake.

### Target flow

**Player roll verb** (`overcome` / `create_advantage` / `attack`):
1. Player picks verb + skill + target in `FateConflictSurface` → mounts the interactive
   Fate dice tray client-side (no server round-trip — client drives, like beat-select).
2. Player throws 4× dF in `DiceScene` (reuse the gesture/settle path); on settle the
   client captures `face[4]` (each −1/0/+1) + `throw_params`. Post-roll invokes happen
   client-side (bonus = +2 preview; reroll = re-throw).
3. Client sends one `FATE_THROW` { intent + `throw_params` + `face[4]` }.
4. Server resolves from `face` (no `roll_4df`), generates `seed`, broadcasts `FATE_ROLL`
   { `dice`=face (authoritative), `throw_params` echoed, `seed` }.
5. All seats replay `throw_params + seed` AND snap the die to the authoritative `dice`.

**Player non-roll verb** (`concede` / `compel_accept` / `compel_refuse`): unchanged —
stays on `FATE_ACTION`, no tray, no `FATE_ROLL`.

**NPC/opponent:** unchanged server roll (`roll_4df`) inside `run_fate_exchange`; projected
via `FATE_ROLL` with `_DEFAULT_FATE_THROW` + `generate_dice_seed` (125-4 groundwork).

### Server seams (sidequest-server)

- **NEW** `protocol/fate.py` → `FateThrowPayload(ProtocolBase)`: intent fields from
  `FateActionPayload` (action[roll verbs only], skill, target, difficulty, invoke_aspect,
  invoke_mode, aspect_text, player_action) + `throw_params: ThrowParams` +
  `face: tuple[int,int,int,int]`. `@model_validator`: exactly 4 faces, each in {−1,0,1}.
  `extra="forbid"` inherited from `ProtocolBase`.
- **NEW** `FateThrowMessage` in `protocol/messages.py`; add to the `GameMessage` union
  (`_Phase1Variant`, ~line 1750–1799, next to `FateActionMessage` line 1360 / 1780);
  `MessageType.FATE_THROW` in `protocol/enums.py`.
- **NEW** `handlers/fate_throw.py` → `FateThrowHandler` (mirror `handlers/fate_action.py`):
  register `"FATE_THROW"` in `websocket_session_handler.py` registry (~line 509/517–530).
  Builds the FATE_ROLL broadcast via existing `build_fate_roll_payload` +
  `generate_dice_seed` (handlers/fate_action.py:147–167 is the reference).
- `game/ruleset/fate_resolution.py`: extract `_build_outcome(dice, …)` from
  `resolve_action` (line 99). Add `resolve_action_from_faces(*, skill_rating, opposition,
  faces, invoke_bonus)` (player path, no rng). `roll_4df` (line 89) unchanged → NPC path.
- `game/ruleset/fate.py`: add `FateRulesetModule.resolve_action_from_faces` wrapper
  (mirror line 194) emitting `fate.action_resolved` with **new attr `source`**.
- `server/dispatch/fate_conflict.py`: `dispatch_fate_action` (line 734) takes the player's
  faces and calls the faces variant; `_seat_opponent_commits` (287) / `_roll_defense`
  (243) keep `rng`. Remove the second-roll reroll branch on the **player** path only.
- `telemetry/spans/fate.py`: `fate_action_resolved_span` (line 211) gains
  `source ∈ {"player_thrown","server_rolled"}`.

### UI seams (sidequest-ui + ../dice-lib — REUSE, don't reinvent)

- dF `DieKind` already exists (`dice-lib/dieRegistry.ts:159`, `dF.ts` `readDFValue`,
  procedural glyphs). `DiceScene` reads any registered kind generically. **No dice-lib
  change needed** beyond consuming it.
- Interactive throw: copy the `DiceOverlay.handleSettle → onThrow(wireParams, faces)`
  pattern (`src/dice/DiceOverlay.tsx:142–160`) into a thrower mode for the Fate tray.
- `FateDiceTray.tsx`: TEAR OUT the decoration assumption (`replayThrowParams` at :46 +
  `onAllSettle = () => {}` at :64) **for the thrower**; KEEP replay-and-snap for
  spectators. Add a thrower path that throws + captures `face[4]` + submits `FATE_THROW`.
- `FateConflictSurface`: roll verbs mount the tray and defer the send until settle;
  non-roll verbs send `FATE_ACTION` synchronously as today.
- App.tsx: add `handleFateThrow` → `send({type: FATE_THROW, …})` (mirror `handleDiceThrow`
  :1870 / `handleFateAction` :1976). Add `FATE_THROW` to `MessageType` (types/protocol.ts).
- **PRESERVE (125-4):** `throw_params`/`seed` on `FateRollPayload`
  (`types/payloads.ts:586–590`); dF `0` label (`dice-lib/dF.ts:25-26`,
  `FateDiceTray.faceGlyph` `return "0"`). Do NOT revert.

### Test plan (for Fezzik/RED)

- **Server determinism:** player path resolves from reported faces; assert `roll_4df` is
  NOT called on the player path (patch/spy). Faces → expected roll_total/ladder_total/
  shifts/tier.
- **Wire validation:** `FateThrowPayload` rejects ≠4 faces, faces ∉ {−1,0,1}, and extra
  fields (`extra="forbid"`).
- **NPC server-side:** opponent commit still calls `roll_4df`; `FATE_ROLL` carries
  synthesized throw_params + seed.
- **OTEL:** `fate.action_resolved` fires with `source="player_thrown"` (player) and
  `source="server_rolled"` (NPC). (OTEL-span assertion, not source-text grep.)
- **WIRING (mandatory):** end-to-end `FATE_THROW` → `FateThrowHandler` → resolve →
  `FATE_ROLL` round-trip through the **real** handler/registry (fixture snapshot, not a
  unit stub); confirm the NPC path still server-rolls in the same exchange.
- **UI:** thrower captures 4 dF settled faces and submits `FATE_THROW`; spectator replay
  snaps to authoritative `dice` (no contradiction with readout).

### AC coverage map

| AC | Where satisfied |
|----|-----------------|
| DESIGN + ADR | ADR-148 + this section |
| Player roll determinative | `resolve_action_from_faces`; spy-asserts no `roll_4df` on player path |
| Interactive throw (UI) | Fate tray thrower mode reusing `DiceScene` settle/capture |
| Client→server message | `FATE_THROW`/`FateThrowPayload` (4 faces, ∈{−1,0,1}, extra=forbid, in union) |
| NPC server-side | `_seat_opponent_commits`/`_roll_defense` keep `roll_4df` + synth throw_params/seed |
| Spectator consistency | replay `throw_params+seed` + snap-to-authoritative `dice` |
| OTEL | `fate.action_resolved` + `source` attr |
| Wiring + no-revert | e2e round-trip test; 125-4 fields/label preserved |

### Explicit scope boundaries / divergences from AC literal wording

1. **Single `FATE_THROW` message, client-driven** (not the AC's "FATE_ACTION → server
   requests throw" 2-message handshake) — faithful to the *live* d20 path.
2. **`seed` is server-generated**, not in the client message — `DiceThrowPayload` (the
   thing we mirror) has no seed. Client sends `throw_params` + `face`.
3. **Player defense rolls stay server-side** — they resolve inside the sealed-commit
   exchange where there is no interactive throw moment. Not a regression (defense isn't
   visualized today). Deferred to a future story.
4. **`reroll` invoke** = client re-throws; server does fate-point accounting only (no
   server reroll on player path).

## TEA Assessment (RED phase) — Fezzik

**Verdict: RED confirmed.** 8 failing test files written (6 server + 2 ui),
each failing for the right reason. Tests-only; no production code touched.
Committed: server `6ae33ae4`, ui `db66a30`.

### Tests written (→ AC / plan-task map)

| File | Plan task | AC covered | RED failure (verified) |
|------|-----------|------------|------------------------|
| `tests/protocol/test_fate_throw_payload.py` | 1 | CLIENT→SERVER MESSAGE | ImportError: `FateThrowPayload` absent |
| `tests/game/ruleset/test_fate_resolution_from_faces.py` | 2 | PLAYER ROLL DETERMINATIVE | ImportError: `resolve_action_from_faces` absent |
| `tests/game/ruleset/test_fate_module_from_faces_span.py` | 3 | OTEL (player_thrown + server_rolled) | AttributeError (player) + `source` attr None (NPC) |
| `tests/game/ruleset/test_fate_projection_throw_params.py` | 4 | SPECTATOR CONSISTENCY (echo gesture) | TypeError: no `throw_params=` kwarg |
| `tests/server/test_fate_dispatch_from_faces.py` | 5 | PLAYER ROLL DETERMINATIVE (no roll_4df) | TypeError: no `thrown_faces=` kwarg |
| `tests/server/test_fate_throw_handler_wiring.py` | 6 | WIRING + NPC SERVER-SIDE | ModuleNotFoundError: `handlers.fate_throw` |
| `src/__tests__/fateThrow.test.ts` | 7 | CLIENT→SERVER MESSAGE (ui) | unresolved `../lib/fateThrow` |
| `src/__tests__/fateDiceTrayThrow.test.tsx` | 8 | INTERACTIVE THROW (ui) | TypeError: no thrower mode (`roll` undefined) |

**Controls that PASS in RED (by design, guard existing behavior):**
`test_defaults_to_synthesized_throw_for_npc` (Task 4 — _DEFAULT_FATE_THROW still
the NPC default) and `test_legacy_none_path_still_server_rolls` (Task 5 — the
spy proves roll_4df is observable, so the 0-count assertion is meaningful).

### Rule coverage (lang-review checklists)
- **python #11 (input validation at boundary):** `FateThrowPayload` rejects ≠4
  faces, out-of-range faces, extra fields, and non-roll verbs — the faces-required
  wire contract (No Silent Fallbacks: no optional dice on FATE_ACTION).
- **python #8 (deserialization trusts structure):** `test_routes_in_game_message_union`
  drives the payload through `GameMessage.model_validate` so the validator/
  `extra='forbid'` runs on the wire path, not just direct construction.
- **python #6 (test quality):** assertions check specific values (dice tuples,
  roll_total/ladder_total, span `source`/`dice`, echoed `throw_params`); spy
  patches `roll_4df` where it is *used* (fate_resolution module global); positive
  controls prevent vacuous spy assertions.

### Scope held (PROACTIVE only — 126-8 untouched)
No test references `_roll_defense` or `_seat_opponent_commits` as a player path;
both stay server-rolled (asserted via the NPC `server_rolled` span + the e2e
"NPC still server-rolls in the same exchange" spy). 125-4 groundwork
(`throw_params`/`seed` on FateRollPayload, dF `0` label) is preserved — the
`_DEFAULT_FATE_THROW` default test pins it.

### Note for Dev/GREEN
The 3 ImportError files are valid RED but abort a **whole-suite** collection
(server `addopts` lacks `--continue-on-collection-errors`). The first GREEN step
(create `FateThrowPayload`, `resolve_action_from_faces`, `handlers/fate_throw.py`)
clears collection. Run the full-suite baseline gate AFTER those symbols exist
(or pass `--continue-on-collection-errors` to measure mid-flight). Server tests
need `SIDEQUEST_DATABASE_URL`; ui via `npx vitest run`.

## Dev Assessment

**Implementation Complete:** Yes — all 8 RED tests GREEN; full chain wired.

**Files Changed:**

*sidequest-server* (commit `01599ae3`, pushed):
- `protocol/enums.py` — `MessageType.FATE_THROW`
- `protocol/fate.py` — `FateThrowPayload` (faces-authoritative, roll-verb Literal, validator)
- `protocol/messages.py` — `FateThrowMessage` + union registration
- `game/ruleset/fate_resolution.py` — `_build_outcome` extract + `resolve_action_from_faces` (no rng)
- `game/ruleset/fate.py` — `FateRulesetModule.resolve_action_from_faces` wrapper; `source` on both spans
- `telemetry/spans/fate.py` — `source` kwarg (default `server_rolled`) on `fate_action_resolved_span`
- `game/ruleset/fate_projection.py` — `build_fate_roll_payload(throw_params=...)` echo
- `server/dispatch/fate_conflict.py` — `dispatch_fate_action(thrown_faces=...)` player path; reroll = accounting only
- `handlers/fate_throw.py` (new) — `FateThrowHandler`; broadcasts FATE_ROLL with thrown dice + echoed gesture
- `server/websocket_session_handler.py` — `FATE_THROW` registry entry
- `tests/protocol/test_enums.py` — count drift correction (56→58)

*sidequest-ui* (commit on `feat/126-7-fate-4df-determinative`, pushed):
- `types/protocol.ts` + `types/payloads.ts` — `FATE_THROW` + `FateThrowPayload`/`FateThrowMessage`
- `lib/fateThrow.ts` (new) — `makeFateThrowMessage`
- `App.tsx` — `handleFateThrow` send path + thread to GameBoard
- `components/GameBoard/GameBoard.tsx` — `onFateThrow` prop threaded to the surface
- `components/FateConflictSurface.tsx` — roll verbs arm the dF thrower (deferred send)
- `dice/FateDiceTray.tsx` — thrower mode (spectator replay-and-snap preserved)
- `components/__tests__/FateConflictSurface.test.tsx` — updated to the new throw contract

**Tests:**
- Server: 8 RED files GREEN (21 tests); regression slice 1615 passed; full suite 85 pre-existing content-drift failures, **0 in the Fate blast radius** (verified — my 8 files + enum test all pass). ruff check + format clean.
- UI: full suite **2399/2399 pass** (incl. all Fate files); `tsc --noEmit` clean; my changed files lint clean (the 1 `npm run lint` error is pre-existing, in an untouched Dashboard file).

**Wiring (no half-wired features):** FATE_THROW reachable end-to-end — FateConflictSurface roll verb → FateDiceTray thrower → `onFateThrow` → App → `makeFateThrowMessage` → socket → FateThrowHandler (real registry) → `dispatch_fate_action(thrown_faces)` → broadcast FATE_ROLL. Server e2e proven by `test_fate_throw_handler_wiring.py`.

**Branch:** `feat/126-7-fate-4df-determinative` (both repos, pushed)

**Scope held:** PROACTIVE only — `_roll_defense`/`_seat_opponent_commits` untouched (NPC + player-defense stay server-rolled; defense is 126-8).

**Handoff:** To verify (TEA simplify + quality-pass).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 smells; server blast-radius 839/0/41; UI 2399/0; 0 new lint in changed files | N/A (clean) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 5 | confirmed 0, dismissed 2, deferred 3 (LOW/Improvement) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | findings | 6 (0 rule violations) | confirmed 0 blocking, 1 MEDIUM surfaced, 5 by-design notes |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 0 confirmed blocking, 2 dismissed (with rationale), 4 deferred as non-blocking LOW/MEDIUM improvements

### Rule Compliance (server CLAUDE.md + lang-review)

- **No Silent Fallbacks** — `[VERIFIED]` enumerated every new decision point: `FateThrowPayload` requires `face` + range-validates (fate.py:91,96 — raises); `resolve_action_from_faces` re-raises on malformed faces (fate_resolution.py:173); `dispatch_fate_action` player path never server-rolls (fate_conflict.py:867); `FateThrowHandler` `room is None` logs error + returns (fate_throw.py:158 — loud-logged, mirrors FateActionHandler). COMPLIANT.
- **No Stubbing / Don't Reinvent** — `[VERIFIED]` reuses `build_fate_roll_payload`, `generate_dice_seed`, `FateActionPayload`, `DiceScene`, `replayThrowParams`, the dF `DieKind`. No empty shells. COMPLIANT.
- **Verify Wiring / Every suite needs a wiring test** — `[VERIFIED]` `test_fate_throw_handler_wiring.py` drives the REAL registry → handler → dispatch → broadcast; the UI chain App→GameBoard→FateConflictSurface→FateDiceTray is threaded end-to-end. COMPLIANT.
- **No Source-Text Wiring Tests** — `[VERIFIED]` wiring test uses registry resolution + broadcast assertion; the OTEL `source` test uses span assertions (not greps). COMPLIANT.
- **OTEL Observability** — `[VERIFIED]` `fate.action_resolved` gains `source ∈ {player_thrown, server_rolled}` (spans/fate.py:24); broadcast `publish_event` carries `source=player_thrown` (fate_throw.py:377). COMPLIANT.
- **input validation at boundary (python #11)** — `[VERIFIED]` two-layer (wire `@model_validator` + engine re-check). COMPLIANT. `[SEC]` confirmed 0 violations.
- **ADR-119 auth identity** — `[VERIFIED]` `[SEC]` FateThrowHandler uses `sd.player_id` as sole seat source; inbound `msg.player_id` only for spoof logging; mismatch → GM-panel publish_event before any seat lookup (fate_throw.py:69-91). Exact mirror of FateActionHandler. COMPLIANT.
- **ADR-047 sanitization** — `[VERIFIED]` `[SEC]` the throw path builds a `FateActionPayload` and routes through the SAME `dispatch_fate_action` seal site that sanitizes skill/target/aspect_text/player_action. No second (double-escape) layer added. COMPLIANT.
- **test quality (python #6)** — `[VERIFIED]` specific-value asserts + positive controls (the dispatch spy control, the NPC `server_rolled` span). No vacuous assertions.

### Findings (none blocking)

1. `[MEDIUM][SEC]` **Reroll invoke under the thrower spends a fate point with no re-throw.** Under FATE_THROW, `invoke_mode='reroll'` calls `invoke_aspect` (spends the point, returns 0) then `resolve_action_from_faces(invoke_bonus=0)` resolves the single thrown faces — `invoked_reroll` is unused on the faces path (fate_conflict.py:864-889). The determinative-reroll model (ADR-148 §5) intends the CLIENT to re-throw, but the thrower UI throws once with no post-result re-throw affordance, so a reroll-mode invoke currently burns a fate point for no effect. Bonus invokes (+2) work correctly. **Non-blocking** (Medium; advanced non-default affordance; explicit ACs all met; ADR-148 §5 documents the staged model). → Delivery finding for 126-8 (where the interactive re-throw/defend UX lands), or a cheap interim guard (suppress `reroll` mode in the pre-throw invoke arming).
2. `[LOW][SILENT]` `FateThrowHandler` `room is None` returns `[]` after `logger.error` without a client error message → on the (unreachable-in-Playing-state) programming-error path the player gets no feedback. **Challenged/downgraded from the hunter's HIGH:** room is guaranteed non-None in Playing state (guarded at the top, fate_throw.py:46), and it's a verbatim mirror of the shipped `FateActionHandler:154-162` — loud-logged, not silent. Non-blocking improvement; if applied, apply to BOTH handlers.
3. `[LOW][SILENT/TYPE]` `FateThrowPayload.face` is `number[]` (TS) / no client-side range check — consistent with the existing `DiceThrowPayload.face: number[]`; server validates 4+range. Could tighten to a `[number,number,number,number]` tuple + a client assert for parity-plus. Non-blocking.
4. `[LOW][SILENT]` `dispatch_fate_action` `thrown_faces is None` branch (transitional) has no OTEL tripwire to catch an accidental server-rolls-for-players caller after 126-8. Cheap future tripwire; non-blocking.
5. `[VERIFIED]` client-forged max roll (`face=(1,1,1,1)`) and `throw_params` echo are BY DESIGN — physics-is-the-roll trusts the client's faces, identical to the live d20 `DiceThrowPayload` trust model (ADR-074 / Story 34-12). `[SEC]` confirmed not a new vuln.

**Dismissed (with rationale):**
- `[SILENT]` `onTrayThrow` `onFateThrow?.()` optional-chain — matches the sibling `onFateAction?.()` convention used throughout FateConflictSurface; wired in prod (App→GameBoard→surface).
- `[SILENT]` `handleAllSettle` early-return on null `pendingParams` — verbatim mirror of the live d20 `DiceOverlay.handleSettle:144` guard; in thrower mode settle cannot fire before a throw (`throwParams` starts null).

### Devil's Advocate

Assume this is broken. **Cheating:** a malicious client submits `face=(1,1,1,1)` every throw for a guaranteed +4. Confirmed reachable — but this is the explicit physics-is-the-roll trust model the d20 path already ships (ADR-074); the GM-panel `source=player_thrown` span makes it observable. Not a new hole, by design. **Spoofing:** can a client throw AS another seat? No — `acting_player_id = sd.player_id` (server-authenticated) is the sole seat source; inbound `msg.player_id` only triggers a spoof-logged publish_event (mirrors the audited FateActionHandler). **Resource loss:** a confused player picks "Reroll" mode, throws, and silently loses a fate point with no re-throw — the real MEDIUM above; niche (non-default) but genuine. **Confused user:** when armed, BOTH the spectator tray (last result) and the thrower tray render — two `fate-dice-tray` nodes; mildly cluttered, not broken (the prior result + the active throw). **Malformed wire:** `face=[99]` or `[1,2,3,4,5]` — rejected at the pydantic boundary (count + range) AND re-rejected in the engine; double defense. **Stressed state:** `room is None` mid-Playing — can't happen (guarded), and is loud-logged if it somehow did. **Stale closure:** does `onTrayThrow` capture a stale `armed`? No — it's recreated each render with the current `armed`, and the tray only mounts while `armed !== null`. **Reroll trust extension:** the server never observes the re-thrown dice on the faces path while still charging the fate point — but this is the same single-throw trust applied once, not a new escalation, and the spend is the intended cost. Net: the one genuine defect is the reroll-mode resource-loss (Medium, documented, 126-8); everything else is by-design trust or an unreachable guard. No Critical/High.

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** client throws 4 dF → `FateDiceTray` thrower `handleAllSettle` captures faces + gesture → `onFateThrow` → `App.handleFateThrow` → `makeFateThrowMessage` → socket → `FateThrowHandler` (real registry) → `dispatch_fate_action(thrown_faces=)` → `resolve_action_from_faces` (no rng) → broadcast `FATE_ROLL` (authoritative dice + echoed gesture). Safe: faces validated at the wire AND engine; seat resolved from the server-authenticated identity; player text sanitized at the shared seal site.

**Pattern observed:** faithful mirror of the live d20 physics-is-the-roll path (`DiceThrowPayload`/`DiceOverlay.handleSettle`) and the existing `FateActionHandler` — including the ADR-119 spoof guard — at `handlers/fate_throw.py` and `dice/FateDiceTray.tsx`.

**Error handling:** fail-loud throughout (wire validator, engine re-check, dispatch ruleset gate); `room is None` is a loud-logged unreachable guard (fate_throw.py:158).

**Findings:** 1 MEDIUM (reroll-mode resource loss — non-blocking, 126-8), 3 LOW improvements, 0 Critical/High. Subagent-tagged findings incorporated:
- `[SEC]` security — 0 rule violations (ADR-119 spoof guard, two-layer faces validation, ADR-047 sanitization, No-Silent-Fallbacks all compliant); the MEDIUM reroll trust-extension is surfaced (non-blocking); client-forged max roll + throw_params echo are by-design (d20 ADR-074 trust model).
- `[SILENT]` silent-failure — 5 findings, 0 blocking: `room is None` returns `[]` (LOW, Challenged — mirrors FateActionHandler, unreachable in Playing state, loud-logged); `face: number[]` no client range-check (LOW, matches DiceThrowPayload); None-branch tripwire (LOW); `onFateThrow?.()` and `handleAllSettle` early-return dismissed (match the live `onFateAction?` / `DiceOverlay.handleSettle` patterns).
- `[VERIFIED]` preflight clean — 0 code smells, server blast-radius 839/0/41, UI 2399/0, 0 new lint in changed files.

**Handoff:** To SM for finish-story.