---
story_id: "118-3"
jira_key: ""
epic: "118"
workflow: "spdd"
---
# Story 118-3: F3c — 4dF roll display (dice surface)

## Story Details
- **ID:** 118-3
- **Jira Key:** (none)
- **Workflow:** spdd
- **Stack Parent:** 118-1 (done)

## Workflow Tracking
**Workflow:** spdd
**Phase:** finish
**Phase Started:** 2026-06-15T12:56:48Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-15T12:05:01Z | 2026-06-15T12:06:53Z | 1m 52s |
| red | 2026-06-15T12:06:53Z | 2026-06-15T12:21:13Z | 14m 20s |
| green | 2026-06-15T12:21:13Z | 2026-06-15T12:45:10Z | 23m 57s |
| review | 2026-06-15T12:45:10Z | 2026-06-15T12:56:48Z | 11m 38s |
| finish | 2026-06-15T12:56:48Z | - | - |

## Context & Scope Summary

**Resolution (Keith, 2026-06-15):** Option B — 3D Fudge die (NOT flat readout)

**F3c — 4dF roll display:** Surface the 4dF result to the player — four Fudge faces {-,0,+}, ladder rating, shifts, outcome tier, succeed-with-style highlight. 

**Scope:** 3 repos (server, ui, dice-lib)

### dice-lib (trunk-based, source-linked @local/dice-lib)
- Add NEW 'dF' DieKind ADDITIVELY to DIE_REGISTRY
- Fudge die = d6 cube (reuse D6_RADIUS / D6_COLLIDER_VERTICES / geometryKind 'box')
- Face→value map: {+1, 0, −1} ×2 each
- Render glyphs via existing procedural FaceLabels + drei <Text> (no new FBX)
- NEVER mutate d6/d20 or existing kinds
- Commit straight to main (no feature branch — shared working copy symlinked into all oq clones)

### server
- FATE_STATE / FateRollPayload must carry 4dF tuple to client (currently lives only on OTEL span)
- Mirrors ADR-136 RELATIONSHIPS pattern

### ui
- InlineDiceTray (or fate variant) wires kind='dF', count=4
- Sums faces→shift, renders ladder/tier/succeed-with-style overlay
- ruleset=='fate' gate + paired negative co-render test vs WN/native ConfrontationOverlay
- Player-facing legibility mandatory (Sebastien/Jade)

## Sm Assessment

Story re-filed at **Option B (3D Fudge die)** after Keith confirmed (2026-06-15) the dice library makes a new die kind cheap: 5pt, `spdd` workflow, scope = server + ui + dice-lib.

Investigation backing the call (so TEA/Dev don't re-derive it):
- `dF` does not exist yet — `DieKind = d4|d6|d8|d10|d12|d20`. Purely additive to `DIE_REGISTRY`.
- A Fudge die **is** a d6 cube — reuse `D6_RADIUS` / `D6_COLLIDER_VERTICES` / `geometryKind: "box"`. New work is only the face→value map (`{+1,0,−1}` ×2) and glyph labels.
- Glyphs ride the **existing** procedural `FaceLabels` + drei `<Text>` path (dice without an FBX). No new 3D asset. The current `{face.number}` label just generalizes to a label string.
- Additive registry entry does **not** touch d6/d20 — WN/native pass `kind="d20"`/`"d6"`, Fate passes `kind="dF"`. Disjoint paths; satisfies the "never mutate d6" rule.

Coordination notes:
- **dice-lib is one shared working copy** (`~/Projects/dice-lib`, `@local/dice-lib`) symlinked into every oq clone via `file:../../dice-lib`. Registered in `repos.yaml` as trunk-based/main. **Do NOT cut a feature branch in dice-lib** — that would switch oq-1/2/4 too. Edit, test (`vitest run`), commit straight to `main`. Only server + ui carry feat branches/PRs.
- The server `FATE_STATE`/`FateRollPayload` spine and the legibility overlay are needed regardless of A vs B, so B's marginal cost over the flat readout is just the `dF` die + 3D-tray wiring.
- Merge gate clear (no blocking PRs), dependency 118-1 done.

Routing to TEA (Argus Panoptes) for RED.

<skills-invoked>
<skill name="test-driven-development" phase="red" at="2026-06-15T12:19:44Z"/>
<skill name="test-driven-development" phase="green" at="2026-06-15T12:43:26Z"/>
<skill name="verification-before-completion" phase="green" at="2026-06-15T12:43:26Z"/>
<skill name="requesting-code-review" phase="green" at="2026-06-15T12:43:26Z"/>
</skills-invoked>

## TEA Assessment

**Tests Required:** Yes
**Status:** RED (failing — ready for Dev)

The story carried no ACs; I authored four (now in the epic YAML) and pinned each
with failing tests across all three repos. Verified RED by direct targeted runs.

**Test Files:**
- `dice-lib/__tests__/dF.test.ts` — the Fudge die (6 fail; 2 green are the
  "never mutate d6" regression guards, correctly green by design)
- `sidequest-server/tests/protocol/test_fate_roll_payload.py` — the roll spine
  (10 fail)
- `sidequest-ui/src/__tests__/fate-roll-payload.test.ts` — FATE_ROLL wire
  contract (3 fail)
- `sidequest-ui/src/dice/__tests__/FateDiceTray.test.tsx` — the dice surface
  (file-level RED: `../FateDiceTray` does not exist yet)

**AC → test coverage:**

| AC | Repo | Tests | Status |
|----|------|-------|--------|
| AC-1 dF die | dice-lib | registry/cube/values/readValue/glyph/d6-guard (8) | RED (6 fail, 2 guard green) |
| AC-2 roll on wire | server | payload + extra-forbid + arity + round-trip + builder×2 + message + union + parse (10) | RED |
| AC-3 UI routing | ui | `MessageType.FATE_ROLL`, `isFateRoll` ±  (3) | RED |
| AC-4 fate-gated tray | ui | dF×4 props, shift/ladder/tier readout, style highlight, non-fate renders nothing (4) | RED |

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| Boundary validation — `extra="forbid"` fails loud (No Silent Fallbacks) | `test_payload_forbids_unknown_fields`, `test_payload_rejects_wrong_dice_arity` | failing |
| Routability — message must be in the `GameMessage`/`TypedGameMessage` union | `test_fate_roll_message_in_game_message_union`, `isFateRoll` guard | failing |
| Wire round-trip integrity | `test_payload_round_trips_through_json`, `test_game_message_parses_fate_roll_wire_form` | failing |
| Never mutate an existing die kind (SOUL / ADR-144) | `does NOT mutate d6 ...`, `dieKindForSides never resolves to dF` | green (regression guards) |
| Fate surface never co-renders with WN/native overlay | `renders nothing when the ruleset is not fate` | failing |

**Self-check:** Removed 1 vacuous UI test (it inspected only my own object
literal — types are erased at runtime, so it passed regardless of production
code). No `let _ =` / `assert(true)` / always-None assertions remain.

**Note for Dev (GREEN):** the protocol/projection tests pin the roll *contract*,
not the *emit call site*. Wiring `build_fate_roll_payload` + broadcasting a
`FateRollMessage` from the Fate resolution path (`FateRulesetModule.resolve_action`
/ the fate dispatch) is the integration to add — with an OTEL span and a
fixture-driven wiring test (OTEL principle + every-suite-needs-a-wiring-test).
dice-lib: commit straight to `main` (no feature branch — shared working copy).

**Handoff:** To Dev (Hephaestus the Smith) for implementation.

## Dev Assessment

**Implementation Complete:** Yes
**Tests:** GREEN — dice-lib 152/152 (incl. dF 8), server 208 fate + 13 protocol/wiring, ui 2214/2214. tsc/ruff/eslint all exit 0.

**Files Changed:**
- `dice-lib` (main): `src/types.ts` (DieKind += dF), `src/d20.ts` (FaceInfo.label?), `src/dF.ts` (NEW — d6-cube Fudge die, {+1,0,−1}×2 + glyphs), `src/dieRegistry.ts` (dF entry), `src/DiceScene.tsx` (FaceLabels renders `label ?? String(number)`). Commit `046fa29` on `main`.
- `sidequest-server` (feat): `protocol/enums.py` (FATE_ROLL), `protocol/models.py` (FateRollPayload), `protocol/messages.py` (FateRollMessage + union), `game/ruleset/fate_projection.py` (build_fate_roll_payload), `server/dispatch/fate_conflict.py` (FateDispatchResult.action_roll), `handlers/fate_action.py` (broadcasts FateRollMessage), `tests/server/test_fate_action_handler_wiring.py` (updated: asserts the broadcast + concede→no-roll). Commit `ddf1a0c4`.
- `sidequest-ui` (feat): `types/protocol.ts` (FATE_ROLL), `types/payloads.ts` (FateRollPayload/FateRollMessage/union/isFateRoll), `dice/FateDiceTray.tsx` (NEW). Commits `c102b44`, `67f515c`.

**Branches (pushed):** server + ui `feat/118-3-fudge-die-4df-display`; dice-lib committed straight to `main` (shared working copy — no feature branch, per spec).

### Wiring status (per "No half-wired features")
- **dice-lib dF die — fully wired & live.** In `DIE_REGISTRY`; any `DiceScene kind="dF"` renders it. d6/d20 untouched.
- **server roll spine — fully wired end-to-end.** This story landed the F3 broadcast the `FateActionHandler` docstring had deferred: the handler now returns a `FateRollMessage` carrying the acting PC's own `action_roll` (threaded out of `dispatch_fate_action`). The handler wiring test drives it via the real registry and asserts the broadcast. The roll's dice/tier remain on the `fate.action_resolved` OTEL span (the GM-panel polygraph); the broadcast is transport, logged at `fate.roll.emitted`.
- **ui roll surface — components delivered & unit-tested, consumer wiring F3b-gated.** `FateDiceTray` + `isFateRoll` have no in-app consumer yet because **the client carries no `ruleset` value to evaluate the fate-gate** (grep of `sidequest-ui/src` for `ruleset` returns nothing outside these new files), and there is no Fate panel host (F3b never landed — `TypedGameMessage` had no `FATE_STATE` either). `FateDiceTray` takes `ruleset` as a prop precisely so the F3b host supplies it. This mirrors how 118-1 (F3a) shipped server `FATE_STATE` before any UI consumer. See Delivery Findings.

### Pre-handoff review (requesting-code-review)
Dispatched one reviewer over the three-repo diff. Verdict: ready to hand off; no Critical/Important confirmed.
- **PUSHED BACK** on its one "Important" (claimed dice-lib has zero dF tests): false — `dice-lib/__tests__/dF.test.ts` (8 tests on the REAL `computeDFFaceInfo`/`readDFValue`) exists (commit `9fd6302`) and passes as part of the 152. The reviewer scoped its diff to `-- src/` and looked in `src/__tests__/`, missing dice-lib's top-level `__tests__/`. Verified present + green.
- Accepted minors: 3D dice render the idle pickup row (no replay params on FATE_ROLL yet) — added an honest TODO note in `FateDiceTray`; UI `dice: number[]` vs server `tuple[int×4]` — left as-is (wire is a JSON array; server enforces arity).

**Handoff:** To TEA (Argus Panoptes) for the verify phase.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 7 structural obs (0 blocking; tests/lint/typecheck all GREEN) | confirmed 4, dismissed 1, deferred 2 |
| 2 | reviewer-edge-hunter | Yes | findings | 12 | confirmed 7, dismissed 2, deferred/pre-existing 3 |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | N/A — Disabled via settings |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | N/A — Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | N/A — Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | N/A — Disabled via settings |
| 7 | reviewer-security | Yes | findings | 3 (1 high PRE-EXISTING, 2 low) | confirmed 3 (1 escalated, 2 non-blocking) |
| 8 | reviewer-simplifier | No | Skipped | disabled | N/A — Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | N/A — Disabled via settings |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 9 confirmed (1 HIGH pre-existing escalated, 8 non-blocking MEDIUM/LOW), 3 dismissed (with rationale), 3 pre-existing flagged

## Reviewer Assessment

**Verdict:** APPROVED

The story's three-repo diff is sound: all tests GREEN (dice-lib 152, server 208 fate + 13 protocol/wiring, ui 2214), lint/typecheck clean, zero code smells. **No Critical/High issue is introduced by the diff.** The dF Fudge die is mathematically correct and additive (d6/d20 untouched), the server roll spine is faithful and emitted, and the UI surface is delivered ready-to-mount. The one HIGH finding (auth-bypass) is **pre-existing** — outside this diff's changed lines — and is escalated as a blocking-urgency follow-up, not a blocker for F3c.

**Data flow traced:** player FATE_ACTION → `FateActionHandler.handle` → `dispatch_fate_action` rolls 4dF (`fate_resolution.resolve_action`, line 750) → `FateOutcome` threaded out as `FateDispatchResult.action_roll` → `build_fate_roll_payload` → `FateRollMessage` → `out_queue` (per-socket) → client. Safe for the acting player; see [SEC]/[SILENT] re: MP scope.

### Confirmed findings (non-blocking)

- `[SEC]` `[SILENT]` **[MEDIUM] FATE_ROLL is delivered sender-only, not room-broadcast.** Handler-returned messages go to the per-socket `out_queue` (`websocket.py:133-135`), so in MP the rest of the table never sees the acting PC's roll — inconsistent with the `DICE_RESULT` room-broadcast pattern (`websocket_session_handler.py:1263`, which even has spectator-replay) and SOUL's *Guitar Solo* ("keep the soloist reachable"). The acting player (the primary legibility target) IS served, and no UI consumer renders it yet (F3b-gated), so it's latent. The handler comment claiming it "broadcasts the same result to the table" is therefore misleading `[DOC]`. *Fix: broadcast via `session._room.broadcast(...)` like DICE_RESULT — bundle with the F3b consumer wiring.*
- `[SEC]` `[EDGE]` **[MEDIUM] `FateRollMessage.player_id=""` — no actor attribution.** Both security (low) and edge-hunter (medium) flagged it: the roll frame carries no `player_id`, so a consumer can't attribute "whose roll." *Fix: `FateRollMessage(payload=payload_out, player_id=acting_player_id)`.*
- `[EDGE]` **[MEDIUM] Glyph inconsistency: `faceGlyph(0)` returns `"0"` but the dF die label for a blank face is `""`.** The 3D die shows a blank Fudge face; the text readout shows `"0"` → the table sees `"+ + 0 −"` vs the die's `"+ +   −"`. Not a crash (the shift total derives from `roll.shifts`, not the glyphs) — a legibility/consistency choice to resolve at F3b mount (lean: pick one — `"0"` is arguably clearer for Sebastien/Jade; blank is Fudge-canonical).
- `[EDGE]` **[LOW] `dF.ts:30` unguarded `D6_TO_FUDGE[face.number]`.** Latent `TypeError` if `computeD6FaceInfo` ever returns a number outside 1–6 (it can't today — fixed/tested). Defensive guard optional.
- `[EDGE]` **[LOW] `FateDiceTray` `rollKey={0}` never remounts the Rapier sim** between rolls — part of the already-documented "3D dice are decorative until replay params" deferral, not a separate defect.
- `[EDGE]` **[LOW] `dF.ts` `readDFValue` degenerate-pose / exact-45° tie-break** returns `0`/iteration-order silently. Geometrically near-impossible; mirrors `readD6Value`'s own init hazard. Document if touched.
- `[EDGE]` **[LOW] UI `roll.dice: number[]` vs server `tuple[int×4]`** — no UI runtime arity check. Server enforces arity 4 + `extra="forbid"`, so a malformed payload can't pass validation; the UI trusts the validated wire. Acceptable.

### Confirmed — pre-existing (flagged, NOT introduced by this diff → not blocking F3c)

- `[SEC]` **[HIGH, PRE-EXISTING] Auth-bypass via spoofed `msg.player_id`** (`fate_action.py:58`, `acting_player_id = getattr(msg, "player_id", "") or sd.player_id`). A client can set a non-empty `player_id` to a victim seat and the handler acts as that PC (sealing a commit, spending their fate point / invoking their aspect). **Verified out-of-diff:** the seat-resolution lines are unchanged by 118-3. F3c adds a *minor amplification* — the spoofer now receives the victim's roll result on their own socket. Root fix belongs to a dedicated security story (ADR-119 authenticated-identity territory): drive seat resolution from `sd.player_id` only, treat `msg.player_id` as server-set output, not trusted input. Escalated in Delivery Findings (blocking-urgency).
- `[SEC]` **[LOW, PRE-EXISTING] `FateActionPayload.skill` stored unsanitized** on `FateSealedCommit` (`fate_conflict.py`, not in diff). No current narrator hint interpolates it (latent); `aspect_text`/`boost.text` get `sanitize_player_text` per ADR-047, `skill` does not. Future-proofing gap.
- `[EDGE]` **[LOW, PRE-EXISTING] `concede_in_conflict` non-`FateConflictError` → 500.** The handler only catches `FateConflictError`; an unexpected exception type propagates raw. Pre-existing error-handling shape, not introduced here.

### Dismissed (with rationale)

- `[EDGE]` *FateDiceTray returns `null` silently for non-fate ruleset* — DISMISSED: returning nothing when the pack isn't Fate is the **intended render-gate** (the whole point of the fate-gate, preventing co-render with the WN overlay), not a masked config error. "No Silent Fallbacks" targets hidden error-masking, not a deliberate gate.
- `[EDGE]` *`roll_4df` lacks dice-range validation* — DISMISSED: each die is `rng.choice((-1, 0, 1))` — values are drawn from a fixed literal tuple and cannot be out of range. Also pre-existing, not in diff.
- `[DOC]` *preflight: dF.ts pair-assignment comment is "misleading"* — DISMISSED: the comment is **correct** — it describes opposite-pair balance (`(1,6)`/`(2,5)` → `(+,−)`, `(3,4)` → `(0,0)`), which exactly matches the code (`{1:+,2:+,3:0,4:0,5:−,6:−}`). Preflight misread the assignment order as the pairing.

### Dispatch-tag coverage

`[TEST]`, `[TYPE]`, `[SIMPLE]`, `[RULE]` — subagents **disabled** via `workflow.reviewer_subagents`; I assessed each domain myself:
- `[TEST]`: TEA's RED suite + Dev's wiring-test update reviewed — meaningful assertions (len/isinstance/specific values/union membership), the handler wiring test correctly flipped from `out == []` to assert the broadcast; the concede→`[]` negative path is covered. No vacuous assertions. Clean.
- `[TYPE]`: `FateRollPayload` (pydantic, `extra="forbid"`, `tuple[int×4]`) and `FateRollMessage` (`Literal[MessageType.FATE_ROLL]` + union membership) are well-typed; `DieKind` extended additively; `FaceInfo.label?` optional. The UI `number[]` vs server tuple is the one looseness (noted LOW above). No `as any`/`@ts-ignore`.
- `[SIMPLE]`: no dead code or over-engineering — the dF die reuses d6 wholesale (minimal), the builder is a flat 1:1 map, the emit is a single conditional. `readDFValue` recomputing face-info per call (vs module-scope elsewhere) is a trivial consistency nit, not worth a change.
- `[RULE]`: see Rule Compliance below.

### Rule Compliance

- **No Silent Fallbacks (CLAUDE.md):** `dispatch_fate_action` raises `FateConflictError` loud on non-Fate ruleset / missing encounter / missing actor (security confirmed 3/3 compliant). The `FateDiceTray` non-fate `null` return is an intended gate, not a fallback. ✓ (one pre-existing gap: concede non-FateConflictError, noted)
- **Boundary validation / `extra="forbid"`:** `FateRollPayload` sets `model_config = {"extra": "forbid"}`; round-trip + unknown-field + wrong-arity tests all green. ✓
- **No half-wired features:** dice-lib dF — live in registry; server emit — wired end-to-end with a wiring test; UI consumer — explicitly deferred to F3b and documented (Dev finding). The server builder now has a real production caller (the handler). ✓ for server/dice-lib; UI deferral documented.
- **OTEL Observability:** the roll's dice/tier/shifts remain on the `fate.action_resolved` span (the GM-panel polygraph); the broadcast is logged at `fate.roll.emitted`. The emit is transport over an already-spanned decision. ✓
- **Never mutate a bound/existing die kind (SOUL / ADR-144):** `[VERIFIED]` — `DIE_REGISTRY.dF` is additive; d6/d20 entries unchanged; `dF.test.ts` d6-guard green (`__tests__/dF.test.ts`); `computeD6FaceInfo` untouched. ✓
- **Prompt-injection sanitization (ADR-047):** `FateRollPayload` carries no player-authored free text — all fields server-derived ints/adjective/bool (security confirmed). N/A to this payload. ✓ (pre-existing `skill` gap noted)

### Devil's Advocate

Argue this is broken. **First:** the feature renders nothing. `FateDiceTray` and `isFateRoll` have no production consumer — no `handleMessage` case dispatches a `FATE_ROLL` to the component, and the client has no `ruleset` value to satisfy the gate. So a player on a Fate pack today sees *zero* dice surface despite the server faithfully emitting the frame. A cynic says "Option B shipped a die nobody can see." Rebuttal: this is the documented, accepted F3b boundary (the consumer host doesn't exist yet), exactly as 118-1 shipped server `FATE_STATE` before a UI consumer — the components are delivered ready-to-mount, and the deferral is logged, not hidden.

**Second:** the malicious user. A second player at the table sends `FATE_ACTION` with `player_id` set to the GM's favorite PC and burns *their* fate point, then receives the victim's roll on their own screen — confirmation of a successful impersonation. This is real and high-impact, but pre-existing (the seat resolution predates F3c); F3c only adds the result-feedback amplification. It's escalated for a dedicated fix rather than silently shipped.

**Third:** the confused user. On a future MP mount, two players commit in one exchange; player A's roll is broadcast (once delivery is fixed) the instant they commit, before player B acts — does that leak sealed information? In collaborative PvE Fate this is table-coordination, sanctioned by ADR-036's peer-visibility amendment, not a sealed-PvP scenario. Acceptable, but worth a conscious decision at mount time. **Fourth:** the stressed renderer. A roll at an extreme ladder rating yields `"Legendary+4"` from `ladder_name`; the UI renders it verbatim with no test for out-of-range adjectives — cosmetically fine (intended Fate behavior), but untested. None of these rise to a diff-introduced blocker.

**Pattern observed:** clean additive extension — `dF` rides the existing `DIE_REGISTRY`/`FaceLabels` seam; `FATE_ROLL` mirrors `DICE_RESULT`/`FATE_STATE` message shape; the server emit reuses the documented handler-return seam.
**Error handling:** loud `FateConflictError` rejections on the dispatch boundary; concede correctly yields no roll.

**Handoff:** To SM (Themis the Just) for finish-story.

## Delivery Findings

No upstream findings.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Reviewer (code review)
- **Conflict** (blocking — pre-existing, dedicated follow-up): auth-bypass — a client can spoof `msg.player_id` in a `FATE_ACTION` to act as another seated player (seal their commit, spend their fate point / invoke their aspect). Affects `sidequest-server/sidequest/handlers/fate_action.py:58` (drive seat resolution from `sd.player_id` only; treat `msg.player_id` as server-set output, per ADR-119). NOT introduced by 118-3 (seat-resolution lines unchanged); F3c adds minor roll-result-feedback amplification. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `FATE_ROLL` is delivered sender-only (per-socket `out_queue`), so the MP table won't see the roll — inconsistent with the `DICE_RESULT` room-broadcast pattern and SOUL's Guitar Solo. Affects `sidequest-server/sidequest/handlers/fate_action.py` (broadcast via `session._room.broadcast`) + the misleading "broadcasts to the table" comment; bundle with the F3b consumer wiring. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): stamp `player_id=acting_player_id` on `FateRollMessage` for attribution, and resolve the `faceGlyph(0)`→`"0"` vs die-label `""` glyph inconsistency, when F3b mounts the surface. Affects `sidequest-server/sidequest/handlers/fate_action.py` + `sidequest-ui/src/dice/FateDiceTray.tsx`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking, pre-existing): apply `sanitize_player_text` to `FateActionPayload.skill` before it is stored on `FateSealedCommit` (latent ADR-047 gap; no current hint interpolates it). Affects `sidequest-server/sidequest/server/dispatch/fate_conflict.py`. *Found by Reviewer during code review.*

### Dev (implementation)
- **Gap** (non-blocking): the UI Fate-roll consumer is unwired — `FateDiceTray` + `isFateRoll` have no in-app caller because the client has no `ruleset` value and no Fate panel host (F3b absent). Affects `sidequest-ui` (`App.tsx` `handleMessage` needs an `isFateRoll` case → roll state; a mount slot for `FateDiceTray`; and the pack `ruleset` must be sent to + threaded through the client to drive the gate). The server now emits `FATE_ROLL`, so this is the only remaining link for the surface to appear in-app. *Found by Dev during implementation.*
- **Improvement** (non-blocking): `FATE_ROLL` carries no `throw_params`/`seed`, so the 3D Fudge dice can't replay to the rolled faces (they render the idle pickup row; the text readout is authoritative). To make the dice animate to the actual result, the server roll should carry replay params like `DICE_RESULT`, or `DiceScene` needs a static set-to-face mode. Affects `sidequest-server` (FateRollPayload) + `sidequest-ui` (FateDiceTray) + possibly `dice-lib` (DiceScene). *Found by Dev during implementation.*

### TEA (test design)
- **Gap** (non-blocking): F3b never landed in the UI — `TypedGameMessage` has no
  `FATE_STATE`, and there is no Fate panel anywhere in `sidequest-ui`. The dF dice
  surface therefore has no host panel and no Fate routing yet. Affects
  `sidequest-ui` (`App.tsx` message routing + a render host for `FateDiceTray`):
  Dev must wire minimal `FATE_ROLL` routing and a place to mount the tray, or it
  will never appear in-app. *Found by TEA during test design.*
- **Question** (non-blocking): the `-1` Fudge glyph — tests accept `-` or `−`
  (U+2212). Dev should pick the proper minus glyph for visual polish. Affects
  `dice-lib` (the `dF` face `label`). *Found by TEA during test design.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

4 deviations

- **Dedicated FATE_ROLL message rather than folding the roll into FATE_STATE**
  - Rationale: a roll is a momentary EVENT, not reactive state; `FATE_STATE` is change-gated and would mis-fit a per-roll payload. The spec phrased it as either/or ("FATE_STATE / FateRollPayload").
  - Severity: minor
  - Forward impact: Dev may instead carry the roll on `FATE_STATE`; if so, the `FATE_ROLL` enum/message/guard tests would need revising to match.
- **New `FateDiceTray` component rather than extending `InlineDiceTray`**
  - Rationale: the fate surface is ruleset-gated and must never co-render with the WN overlay; a separate component keeps the disjoint paths disjoint (matches the server-side gate).
  - Severity: minor
  - Forward impact: none — the spec explicitly permits a fate variant.
- **Server FATE_ROLL emit added (beyond the tested contract) to avoid a half-wired builder**
  - Rationale: TEA's RED tests pinned the payload/message contract but not the emit call site; shipping a builder with no production caller is dead code (project rule). The handler was the documented, clean seam.
  - Severity: minor
  - Forward impact: none — additive; the prior `out == []` behavior was explicitly an F1d placeholder ("broadcast is F2/F3").
- **UI consumer (routing + mount) NOT wired — deferred to F3b**
  - Rationale: the client has no `ruleset` value and no Fate panel host (F3b never landed); wiring the consumer means building F3b-scale plumbing, which is out of F3c's scope and beyond the RED tests. Components are delivered ready-to-mount.
  - Severity: minor
  - Forward impact: F3b (or a follow-up) must add the `isFateRoll` route + mount + `ruleset` plumbing for the surface to appear in-app. Logged as a Delivery Finding.

## Design Deviations

No deviations recorded.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Dedicated FATE_ROLL message rather than folding the roll into FATE_STATE**
  - Spec source: context-story-118-3.md, Problem ("FATE_STATE / FateRollPayload spine must carry the 4dF tuple")
  - Spec text: "FATE_STATE / FateRollPayload spine must carry the 4dF tuple to the client"
  - Implementation: tests pin a dedicated `FATE_ROLL` event message (mirrors `DICE_RESULT`), not a roll field on the change-gated `FATE_STATE` reactive snapshot
  - Rationale: a roll is a momentary EVENT, not reactive state; `FATE_STATE` is change-gated and would mis-fit a per-roll payload. The spec phrased it as either/or ("FATE_STATE / FateRollPayload").
  - Severity: minor
  - Forward impact: Dev may instead carry the roll on `FATE_STATE`; if so, the `FATE_ROLL` enum/message/guard tests would need revising to match.
- **New `FateDiceTray` component rather than extending `InlineDiceTray`**
  - Spec source: context-story-118-3.md, scope ("InlineDiceTray (or a fate variant)")
  - Spec text: "InlineDiceTray (or a fate variant) wires kind='dF', count=4 ..."
  - Implementation: tests target a new `FateDiceTray` (fate variant), keeping the WN/native `InlineDiceTray` path untouched
  - Rationale: the fate surface is ruleset-gated and must never co-render with the WN overlay; a separate component keeps the disjoint paths disjoint (matches the server-side gate).
  - Severity: minor
  - Forward impact: none — the spec explicitly permits a fate variant.

### Dev (implementation)
- **Server FATE_ROLL emit added (beyond the tested contract) to avoid a half-wired builder**
  - Spec source: TEA Assessment ("Note for Dev") + server CLAUDE.md ("No half-wired features")
  - Spec text: "Wiring build_fate_roll_payload + broadcasting a FateRollMessage from the Fate resolution path is the integration to add"
  - Implementation: threaded `action_roll` through `FateDispatchResult` and had `FateActionHandler` broadcast a `FateRollMessage` (the F3 broadcast its own docstring deferred); updated the existing handler wiring test (was asserting `out == []`) to assert the broadcast.
  - Rationale: TEA's RED tests pinned the payload/message contract but not the emit call site; shipping a builder with no production caller is dead code (project rule). The handler was the documented, clean seam.
  - Severity: minor
  - Forward impact: none — additive; the prior `out == []` behavior was explicitly an F1d placeholder ("broadcast is F2/F3").
- **UI consumer (routing + mount) NOT wired — deferred to F3b**
  - Spec source: context-story-118-3.md, ui scope; epic-118 context (F3b)
  - Spec text: "InlineDiceTray (or a fate variant) wires kind='dF', count=4 ... fate-ruleset gate"
  - Implementation: delivered `FateDiceTray` (gated, unit-tested) + `isFateRoll`, but did NOT wire `handleMessage` routing, a mount slot, or the `ruleset` plumbing.
  - Rationale: the client has no `ruleset` value and no Fate panel host (F3b never landed); wiring the consumer means building F3b-scale plumbing, which is out of F3c's scope and beyond the RED tests. Components are delivered ready-to-mount.
  - Severity: minor
  - Forward impact: F3b (or a follow-up) must add the `isFateRoll` route + mount + `ruleset` plumbing for the surface to appear in-app. Logged as a Delivery Finding.

### Reviewer (audit)
- **TEA: Dedicated FATE_ROLL message vs folding into FATE_STATE** → ✓ ACCEPTED by Reviewer: a roll is a momentary event, correctly modeled like `DICE_RESULT` rather than the change-gated `FATE_STATE` snapshot. Sound.
- **TEA: New `FateDiceTray` vs extending `InlineDiceTray`** → ✓ ACCEPTED by Reviewer: a separate fate-gated component keeps the disjoint fate/WN paths disjoint, matching the server-side gate. Spec explicitly permitted a fate variant.
- **Dev: Server FATE_ROLL emit added beyond the tested contract** → ✓ ACCEPTED by Reviewer: correct call — a builder with no production caller is dead code; the handler-return seam is the documented F3 broadcast point. (Caveat captured as a finding: the chosen seam is sender-only, not a room broadcast — improvement, not a reversal.)
- **Dev: UI consumer (routing + mount) deferred to F3b** → ✓ ACCEPTED by Reviewer: the client has no `ruleset` value and no Fate-panel host today; wiring the consumer would mean building F3b-scale plumbing, out of F3c's scope. Components are delivered ready-to-mount and the deferral is documented. Independently corroborated by edge-hunter (no production consumer).