---
story_id: "125-4"
jira_key: ""
epic: "125"
workflow: "tdd"
---
# Story 125-4: F3g follow-up (118-7): animate the FateDiceTray 3D Fudge dice to the rolled faces (throw_params/seed) + align the dF blank-face label to '0'

## Story Details
- **ID:** 125-4
- **Jira Key:** (none — personal SideQuest sprint, no Jira)
- **Workflow:** tdd
- **Stack Parent:** none
- **Repos:** dice-lib, server, ui

## Story Context

**Type:** Enhancement / Deferred Followup
**Points:** 3
**Priority:** p3

This is a deferred coupling from story 118-7 (ADR-144 F3g). Two interdependent changes make the FateDiceTray 3D Fudge dice display the actual rolled faces instead of the idle pickup row.

### Acceptance Criteria

**AC4 (dice-lib, 1-line change):** Align the dF die's blank-face label to '0'.
- The UI text readout already renders faceGlyph(0)='0' (pinned by a test in 118-7)
- The dice-lib die still labels its two blank Fudge faces as '' (empty string)
- Change labels in ../dice-lib/src/dF.ts:22-23 from '' to '0'
- Add a dice-lib test to verify the face labels are correct
- Not player-visible until AC5 lands (dice are decorative/idle today)

**AC5 (server + ui, substantive change):** Carry throw_params + seed on the FATE_ROLL message/payload.
- Mirrors the DICE_RESULT message structure
- FateRollPayload is model_config extra='forbid' — this is a deliberate protocol change
- Server changes:
  - sidequest-server/protocol/models.py: FateRollPayload — add throw_params and seed fields
  - sidequest-server/game/ruleset/fate_projection.py: build_fate_roll_payload() — emit throw_params and seed
- UI changes:
  - sidequest-ui/src/components/FateDiceTray.tsx: pass throwParams through to DiceScene so dice animate to rolled faces instead of idle state
- Test coverage: verify the 3D Fudge dice render with the actual rolled face values

### Coupled Dependency
AC5 depends on AC4 being complete. The dice won't show meaningful faces in the UI until the dice-lib face labels are aligned.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-17T07:33:58Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| red | 2026-06-17T06:45:12Z | 2026-06-17T07:06:39Z | 21m 27s |
| green | 2026-06-17T07:06:39Z | 2026-06-17T07:25:30Z | 18m 51s |
| review | 2026-06-17T07:25:30Z | 2026-06-17T07:33:58Z | 8m 28s |
| finish | 2026-06-17T07:33:58Z | - | - |

## Branch Information
**Strategy:** Feature branch per repo. dice-lib has no `develop` (only `main`), so its feature branch is cut from `main`; server/ui from `develop`. All three PR back to their base at finish.

- **dice-lib:** feat/125-4-fate-dice-tray-3d-faces (from main — no develop exists)
  - Current: feat/125-4-fate-dice-tray-3d-faces, clean
- **server:** gitflow — feat/125-4-fate-dice-tray-3d-faces (from develop)
  - Created from: origin/develop (fbc6ab41)
  - Current: feat/125-4-fate-dice-tray-3d-faces
- **ui:** gitflow — feat/125-4-fate-dice-tray-3d-faces (from develop)
  - Created from: origin/develop (d847255)
  - Current: feat/125-4-fate-dice-tray-3d-faces

## Delivery Findings

No upstream findings at setup.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Question** (non-blocking): The story title says "animate the dice to the rolled faces," but `DiceScene` (dice-lib) has NO target-faces prop — its physics-is-the-roll path tumbles from `throw_params`+`seed` and reads whatever face it settles on (`computeSnapTarget` snaps to the *settled* value, not a target). So a server-rolled 4dF cannot be guaranteed to settle on `roll.dice`; the text readout stays authoritative and the 3D tumble is decorative. Exact-face fidelity would need a `DiceScene` settle-to-predetermined-faces change, which is OUT of 125-4's dice-lib scope (scoped to the dF label only). Affects `../dice-lib/src/DiceScene.tsx` + `sidequest-ui/src/dice/FateDiceTray.tsx` (Dev/Architect: confirm decorative-tumble is acceptable, or file a follow-up dice-lib story). *Found by TEA during test design.*
- **Gap** (non-blocking): The UI `FateRollPayload` TS interface lacks `throw_params`/`seed`; Dev must add them (mirror `DiceResultPayload`'s `throw_params: DiceThrowParams` + `seed: number`) so the wire type matches the server and `tsc -b`/`build` passes. The established replay converter is `replayThrowParams(roll.throw_params, roll.seed, D6_RADIUS)` (dF is a d6 cube) — InlineDiceTray uses the D20 form at `sidequest-ui/src/dice/InlineDiceTray.tsx:264`. Affects `sidequest-ui/src/types/payloads.ts` + `sidequest-ui/src/dice/FateDiceTray.tsx`. *Found by TEA during test design.*
- **Improvement** (non-blocking): `build_fate_roll_payload(outcome)` takes only a `FateOutcome`, which carries no seed/gesture (`fate_resolution.py` `roll_4df` uses the rng directly). Dev must decide where the synthesized `throw_params`+`seed` originate (synthesize in the projection vs. thread a captured seed through `FateOutcome`). The wiring test only pins that the projection *emits* a real `ThrowParams` + `int` seed, leaving the source to Dev. Affects `sidequest-server/sidequest/game/ruleset/fate_projection.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): Implemented decorative-tumble per scope — the 4 dF dice now tumble from a constant gesture + per-roll seed but do NOT settle on `roll.dice` (DiceScene has no target-faces prop; the text readout stays authoritative). This resolves TEA's Question for the 125-4 deliverables (emit fields + pass them through, both done). Exact-face fidelity remains a separate dice-lib follow-up (DiceScene settle-to-predetermined-faces). Affects `../dice-lib/src/DiceScene.tsx`. *Found by Dev during implementation.*
- **Gap** (non-blocking): Pre-existing, NOT caused by 125-4 — `tests/protocol/test_enums.py::test_message_type_complete_count` fails (`len(MessageType) == 57` but the test hardcodes `56`). `enums.py` was last touched by commit `27fc0c63` (118-3) and 125-4 adds no MessageType; this is a stale count on the oq-2 tree (likely already fixed on develop). Flagged so it isn't attributed to this story. Affects `sidequest-server/tests/protocol/test_enums.py`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `fate_action.py` `room is None` path logs `logger.error` and returns `[]`, silently dropping the freshly-built roll to the table. PRE-EXISTING (125-4 only added the seed/payload work above it; the guard is unchanged) and it logs at error level, so deferred — but a future hardening could raise or emit a watcher span so a missed broadcast surfaces. Affects `sidequest-server/sidequest/handlers/fate_action.py` (room-None branch). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `build_fate_roll_payload`'s optional `seed=None` + `_fallback_seed` default is required by TEA's no-seed wiring test, but means a future refactor that drops `seed=roll_seed` at the call site would silently fall back to a dice-derived seed (same animation across turns for identical faces) without failing a test. Consider asserting/logging if the fallback fires outside tests, or a test-only constructor. Affects `sidequest-server/sidequest/game/ruleset/fate_projection.py`. *Found by Reviewer during code review.*

## Design Deviations

- **dice-lib branch:** sm-setup initially left dice-lib on `main` ("trunk-based, branching skipped"). Corrected at setup: dice-lib has only `main` (no `develop`), so a feature branch `feat/125-4-fate-dice-tray-3d-faces` was cut from `main` for consistency with server/ui and so the change can be PR'd/reviewed at finish. Working tree was clean at branch creation.
- **Session phase pointer:** sm-setup wrote `Phase: red` directly, skipping SM's own `setup` phase. Reset to `setup` so the `sm_setup_exit` gate runs and `complete-phase` advances setup→red correctly.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **throw_params/seed pinned as REQUIRED, not optional**
  - Spec source: context-story-125-4.md, AC5
  - Spec text: "Carry throw_params + seed on the FATE_ROLL message/payload (mirroring DICE_RESULT) so the 3D dice ... animate ... instead of rendering the idle pickup row (throwParams=null)"
  - Implementation: Tests pin `throw_params: ThrowParams` and `seed: int` as REQUIRED on `FateRollPayload` (`test_throw_params_is_required`, `test_seed_is_required`), matching `DiceResultPayload`.
  - Rationale: An optional field defaulting to None would silently re-introduce the exact `throwParams=null` idle-dice bug this story kills (No Silent Fallbacks); DICE_RESULT's mirror fields are required.
  - Severity: minor
  - Forward impact: Dev must make `build_fate_roll_payload` always emit both, and add the two fields to the UI TS interface.
- **Updated existing 118-3 fixtures to carry the new required fields**
  - Spec source: context-story-125-4.md, AC5
  - Spec text: "FateRollPayload is model_config extra='forbid' — this is a deliberate protocol change"
  - Implementation: Added `throw_params`/`seed` to the 5 direct `FateRollPayload` constructions in `tests/protocol/test_fate_roll_payload.py` and to the SUCCEED/STYLE fixtures in `sidequest-ui FateDiceTray.test.tsx`.
  - Rationale: With the fields required, those existing constructions would error permanently in GREEN; updating them re-pins the new contract. Test-fixture edits only; no AC behavior changed.
  - Severity: minor
  - Forward impact: none.
- **Flipped the pinned dF 0-face label invariant from '' to '0'**
  - Spec source: context-story-125-4.md, AC4
  - Spec text: "Change those labels '' -> '0' so the 3D die and the text readout agree"
  - Implementation: Updated the existing 118-3 `dF.test.ts` assertion + `FUDGE_GLYPHS` const (0-face) from `''` to `'0'`, plus a new focused test.
  - Rationale: The 118-3 test pinned the OLD invariant (`label===''`); leaving it would make Dev's AC4 change break a green test. TEA owns evolving the pinned contract.
  - Severity: minor
  - Forward impact: Dev must also fix the now-stale dF.ts header comment ("glyphs '+' / '' (blank) / '−'").
- **Did NOT assert the 3D dice settle on roll.dice (face fidelity)**
  - Spec source: story title — "animate the FateDiceTray 3D Fudge dice to the rolled faces"
  - Spec text: "animate ... to the rolled faces"
  - Implementation: UI tests pin that FateDiceTray passes a non-null, payload-derived `throwParams` + a roll-derived `rollKey` to DiceScene; they do NOT assert settled faces equal `roll.dice`.
  - Rationale: DiceScene has no target-faces prop (physics reads whatever it lands on); exact-face replay would need a dice-lib change OUT of 125-4's label-only scope. Raised as a Delivery Finding (Question) for Dev/Architect.
  - Severity: minor
  - Forward impact: if exact-face fidelity is required, a follow-up dice-lib story is needed (the AC-level deliverables — emit fields, pass them through — are fully covered).

### Dev (implementation)
- **build_fate_roll_payload gained an optional `seed` param; the gesture is a shared constant**
  - Spec source: context-story-125-4.md, AC5 + TEA Improvement finding (source of throw_params/seed left to Dev)
  - Spec text: "build_fate_roll_payload() — emit throw_params and seed" (FateOutcome carries neither)
  - Implementation: signature is now `build_fate_roll_payload(outcome, *, seed: int | None = None)`. The production caller (`handlers/fate_action`) computes a per-turn seed via `generate_dice_seed(f"{genre}:{world}:{player}", interaction)` — the exact keying the dF dice path uses — and passes it. `throw_params` is the module constant `_DEFAULT_FATE_THROW` (mirrors the `dice_throw.py` fallback gesture); a dice-derived `_fallback_seed` covers test/non-handler callers.
  - Rationale: A per-turn seed (not dice-derived) is required so two identical rolls yield different rollKeys and the UI re-throws; the gesture can be constant because the seed drives the per-roll initial rotation in `replayThrowParams`. Kept the param optional so the projection stays single-arg-callable (TEA's wiring test + future callers).
  - Severity: minor
  - Forward impact: none.
- **Completed UI roll fixtures + dice-lib test mocks for the now-required fields**
  - Spec source: context-story-125-4.md, AC5 (extra='forbid', deliberate protocol change)
  - Spec text: "FateRollPayload is model_config extra='forbid' — this is a deliberate protocol change"
  - Implementation: Added `throw_params`/`seed` to 8 existing UI `FateRollPayload` fixtures (7 files) + 1 server wire-form fixture (`test_game_message_parses_fate_roll_wire_form`, which TEA's constructor sweep missed); added a faithful `replayThrowParams` stub to 4 UI test mocks of `@local/dice-lib` (FateDiceTray, FateConflictSurface, FatePanel, GameBoard-fate-roll).
  - Rationale: Making the fields required (server) + adding them to the TS interface (UI) breaks tsc/runtime for every pre-existing fixture/mock; completing them re-pins the contract without weakening any assertion. The stub is a pure-function double (dice-lib's own tested concern), keeping WebGL out of jsdom.
  - Severity: minor
  - Forward impact: none (test harness only).

### Reviewer (audit)
- **TEA: throw_params/seed pinned REQUIRED** → ✓ ACCEPTED: mirrors DiceResultPayload and is the fail-loud choice (No Silent Fallbacks); verified `extra='forbid'` + no defaults at protocol/models.py.
- **TEA: updated existing 118-3 fixtures** → ✓ ACCEPTED: necessary for a required-field protocol change; test-fixture only, no assertion weakened.
- **TEA: flipped the dF 0-face label invariant '' → '0'** → ✓ ACCEPTED: the 118-3 test pinned the old invariant; flipping it is correct ownership of the evolving contract (AC4).
- **TEA: did NOT assert exact-face fidelity** → ✓ ACCEPTED: DiceScene has no target-faces prop and that is out of 125-4's dice-lib (label-only) scope; correctly raised as a finding, not silently dropped. The AC-level deliverables (emit fields, pass them through) ARE covered.
- **Dev: build_fate_roll_payload gained optional `seed`; gesture is a constant** → ✓ ACCEPTED (with note): a per-turn seed from the handler is the right call for re-throw; the constant gesture is acceptable because the seed drives per-roll rotation, matching the dice_throw precedent. The optional-default's silent-fallback risk is recorded as a non-blocking Reviewer finding.
- **Dev: completed UI fixtures + dice-lib mocks** → ✓ ACCEPTED: required by the new TS interface + the new replayThrowParams dependency; faithful test doubles, no assertion weakened.

## Sm Assessment

Setup complete and verified for story 125-4 (TDD, 3 pts, p3). No Jira (personal sprint).

**Verified:**
- Session file at `.session/125-4-session.md` (not the archive morgue); fields set (workflow tdd, repos dice-lib/server/ui, phase setup).
- Story context at `sprint/context/context-story-125-4.md`; epic context present.
- Feature branch `feat/125-4-fate-dice-tray-3d-faces` exists in all three repos (dice-lib from main, server/ui from develop).
- Sprint status `in_progress`. No stack dependency (`depends_on: null`).

**Scope for TEA (RED phase):** Two coupled changes, both deferred from 118-7 (ADR-144 F3g), player-UI legibility mandate (Sebastien/Jade — dice should show what was actually rolled):
- **AC4 (dice-lib, 1-line + test):** `../dice-lib/src/dF.ts:22-23` — change the two blank Fudge face labels from `''` to `'0'` so the 3D die agrees with the text readout `faceGlyph(0)='0'` (pinned by an 118-7 test). Add a dice-lib test asserting the face-label set.
- **AC5 (server + ui):** Carry `throw_params` + `seed` on the FATE_ROLL payload (mirroring DICE_RESULT) so `FateDiceTray`'s 3D Fudge dice animate to the actual rolled faces instead of the idle pickup row (`throwParams=null`). Server: `FateRollPayload` (protocol/models.py) + `build_fate_roll_payload` (game/ruleset/fate_projection.py). UI: `FateDiceTray.tsx` passes `throwParams` through to `DiceScene`. NOTE: `FateRollPayload` is `model_config extra='forbid'` — adding fields is a deliberate protocol change; TEA should pin the new fields with a payload schema test.

**TEA notes:** AC4 is not player-visible until AC5 lands (dice are decorative/idle today) — that coupling is why they're bundled. Per project rule, every test suite needs a wiring test: assert `build_fate_roll_payload` actually emits the new fields (not just that the model accepts them), and that `FateDiceTray` passes them onward. Reference: `sprint/archive/118-7-session.md` Delivery Findings (TEA test design + Reviewer code review).

**Routing:** Phased TDD → next agent TEA (red). RED → GREEN (Dev) → REVIEW (Reviewer) → FINISH (SM).

---
## TEA Assessment

**Tests Required:** Yes
**Status:** RED (failing — ready for Dev) — verified across all three repos.

**Test Files:**
- `../dice-lib/__tests__/dF.test.ts` — AC4: flipped the pinned 0-face label invariant `'' → '0'` + a focused test that the two blank Fudge faces read `'0'` and no face keeps the empty glyph.
- `sidequest-server/tests/protocol/test_fate_roll_payload.py` — AC5 protocol half: `throw_params`/`seed` present+typed, both REQUIRED (fail-loud), round-trip through JSON; 5 existing constructions updated to carry the new fields.
- `sidequest-server/tests/server/test_fate_roll_replay_emit_125_4.py` — AC5 projection **wiring**: `build_fate_roll_payload` actually EMITS a real `ThrowParams` gesture + an `int` seed, and the F3c legibility mapping is undisturbed.
- `sidequest-ui/src/dice/__tests__/FateDiceTray.test.tsx` — AC5 UI half: FateDiceTray passes a non-null, payload-derived `throwParams` to DiceScene (not the idle `null`) and a roll-derived `rollKey` (a new roll re-throws); SUCCEED/STYLE fixtures updated to carry the replay fields.

**Measured RED (targeted runs, not the full gate):**
- dice-lib: `2 failed | 7 passed` — both failures `expected '' to be '0'` (dF.ts still labels 0-faces `''`).
- server: `7 failed, 10 passed` — `ValidationError` on the new fields (extra='forbid' rejects them today) + `AttributeError` on the projection (build doesn't emit them).
- ui: `2 failed | 4 passed` — `throwParams` is `null` / `rollKey` constant today.

**Tests Written:** 11 new/updated assertions across 4 files covering AC4 (dice-lib) + AC5 (server protocol, server projection wiring, UI pass-through).

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| No Silent Fallbacks (required, fail-loud fields) | `test_throw_params_is_required`, `test_seed_is_required` | guard (holds) |
| Boundary validation (extra='forbid') | `test_payload_forbids_unknown_fields` | pass (negative) |
| Every Test Suite Needs a Wiring Test | `test_fate_roll_replay_emit_125_4.py::test_projection_emits_a_real_throw_params_gesture` (real production-caller projection) + existing `test_fate_roll_broadcast_wire_118_7.py` (real handler) | failing/RED |
| No Source-Text Wiring Tests | all wiring tests assert behavior (model construction / projection output / captured DiceScene props) — zero source greps | n/a (complied) |
| Python #6 / test quality (no vacuous asserts) | self-checked: every test asserts concrete values (faces, gesture components, seed type, JSON round-trip) | clean |
| AC4 — dF 0-face label '0' | `dF.test.ts` "each face carries a glyph label..." + "labels the two blank (0) Fudge faces '0'" | failing/RED |
| AC5 — payload carries throw_params/seed | `test_payload_carries_throw_params_and_seed`, `test_payload_round_trips_with_replay_fields` | failing/RED |
| AC5 — UI passes throwParams through | FateDiceTray "passes the roll's throw gesture..." + "derives throwParams + rollKey..." | failing/RED |

**Rules checked:** Python + TypeScript lang-review checklists scanned; the load-bearing ones for this change are the fail-loud/boundary-validation and wiring rules above. **Self-check:** 0 vacuous tests written.

**Note on the two "guard" rows:** `test_throw_params_is_required`/`test_seed_is_required` pass *today* for a transitional reason (the omitted field's sibling is also unknown under extra='forbid'); once Dev adds both fields they become true required-field guards. They are not vacuous (each asserts a `ValidationError` is raised).

**Scope boundary flagged (see Delivery Findings + Deviations):** the 3D dice are wired to *tumble* from the payload's gesture; whether they settle on exactly `roll.dice` is a `DiceScene` capability that's out of 125-4's dice-lib (label-only) scope — Dev/Architect to confirm decorative-tumble is acceptable.

**Handoff:** To Dev (Inigo Montoya) for GREEN — make the dice-lib dF 0-face label `'0'`, add `throw_params: ThrowParams` + `seed: int` (required) to `FateRollPayload` + emit them from `build_fate_roll_payload`, add the two fields to the UI `FateRollPayload` TS interface, and wire `FateDiceTray` to pass `replayThrowParams(roll.throw_params, roll.seed, D6_RADIUS)` + a seed-derived `rollKey` to `DiceScene`. Also fix the stale dF.ts header comment.

---
## Dev Assessment

**Implementation Complete:** Yes — all of TEA's RED is now GREEN across the three repos.

**Files Changed (production):**
- `../dice-lib/src/dF.ts` — AC4: the two 0-value Fudge faces now carry label `'0'` (was `''`); header comment updated.
- `sidequest-server/sidequest/protocol/models.py` — AC5: `FateRollPayload` gains required `throw_params: ThrowParams` + `seed: int` (import added from `protocol.dice`; no circular import — verified).
- `sidequest-server/sidequest/game/ruleset/fate_projection.py` — AC5: `build_fate_roll_payload(outcome, *, seed=None)` emits the gesture (`_DEFAULT_FATE_THROW`) + seed (handler-supplied, dice-derived fallback).
- `sidequest-server/sidequest/handlers/fate_action.py` — AC5 wiring: computes a per-turn `generate_dice_seed(...)` and passes it to the projection (same keying as the dF `dice_throw` path).
- `sidequest-ui/src/types/payloads.ts` — AC5: `FateRollPayload` TS type gains `throw_params: DiceThrowParams` + `seed: number`.
- `sidequest-ui/src/dice/FateDiceTray.tsx` — AC5: replays the roll via `replayThrowParams(roll.throw_params, roll.seed, D6_RADIUS)`, keyed by `roll.seed` (was hardcoded `throwParams={null} rollKey={0}`).

**Files Changed (test harness — fixture/mock completion, see Deviations):**
- server: `tests/protocol/test_fate_roll_payload.py` (wire-form fixture).
- ui: 8 roll fixtures across 7 files + `replayThrowParams` stub in 4 dice-lib mocks.

**Tests / Verification (measured):**
- dice-lib: full suite **153/153** pass.
- ui: full suite **2385/2385** pass (273 files); `tsc -b` clean; `eslint` n/a-run by gate.
- server: fate suite **27/27** pass; protocol dir 320 pass / **1 pre-existing** failure (`test_message_type_complete_count` 57≠56 — not 125-4, see Findings); `ruff format --check` clean; `pyright` 0 errors on changed files; import smoke clean.

**Branches (pushed):** `feat/125-4-fate-dice-tray-3d-faces` in dice-lib (from main), server, ui (from develop).

**Self-review:** Code wired end-to-end (handler → projection → payload → wire → FateDiceTray → DiceScene), with production consumers confirmed (`FatePanel`, `FateConflictSurface`, `GameBoard`). No stubs in production. Followed the existing dF/DICE_RESULT replay pattern rather than inventing one. Decorative-tumble scope boundary acknowledged (Findings).

**Handoff:** To Reviewer (Westley) for code review.

---
## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (GREEN all repos) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (Reviewer self-assessed edges) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 | confirmed 0, deferred 2 (1 pre-existing, 1 downgraded LOW) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings (Reviewer self-assessed tests) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings (Reviewer self-assessed docs) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (Reviewer self-assessed types) |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (Reviewer self-assessed complexity) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings (Rule Compliance done by Reviewer) |

**All received:** Yes (3 enabled subagents returned; 6 disabled via `workflow.reviewer_subagents` and self-assessed)
**Total findings:** 0 confirmed blocking, 2 deferred (non-blocking, with rationale)

---
## Reviewer Assessment

**Verdict:** APPROVED

A tight, well-scoped 3-repo change that does exactly what AC4 + AC5 ask, faithful to the existing DICE_RESULT/dF replay pattern. Preflight GREEN everywhere (dice-lib 153/153, ui 2385/2385 + tsc clean, server fate suite 27/27, lint clean), security clean, no Critical/High.

### Rule Compliance (enumerated)
- **No Silent Fallbacks** (CLAUDE.md): `FateRollPayload.throw_params`/`seed` are REQUIRED with `extra='forbid'` (protocol/models.py:1129-1131) — a missing field raises ValidationError (fail-loud) ✓. The one fallback in scope — `build_fate_roll_payload(seed=None → _fallback_seed)` — is a deterministic default for a pure projection helper required by TEA's no-seed wiring test, not a config-masking fallback; downgraded to non-blocking with a tracked finding. The pre-existing `room is None → return []` path logs at error level (loud) and is unchanged by this diff.
- **No Stubbing** (CLAUDE.md): no production stubs. The `replayThrowParams` doubles exist only in test mocks (legitimate). ✓
- **Don't Reinvent / Wire Up What Exists**: Dev reused `replayThrowParams` (FateDiceTray, mirroring InlineDiceTray:264), `generate_dice_seed` (same keying as dice_throw.py:201), and the dice_throw fallback gesture. No reimplementation. ✓
- **Every Test Suite Needs a Wiring Test**: `test_fate_roll_replay_emit_125_4.py` drives the real projection (production caller path); `test_fate_roll_broadcast_wire_118_7.py` exercises the real handler; FateDiceTray pass-through test asserts the prop reaches DiceScene. ✓
- **No Source-Text Wiring Tests**: all assertions are behavioral (model construction, projection output, captured DiceScene props) — no source greps. ✓
- **OTEL Observability**: the roll broadcast already emits a `state_transition`/`fate_roll` watcher span (fate_action.py); the new fields are cosmetic animation metadata (CLAUDE.md OTEL exclusion: "Not needed for cosmetic changes"). No new span required. ✓
- **Python**: `build_fate_roll_payload` fully type-annotated; no bare except; no mutable default (None + helper). pyright 0 errors. ✓
- **TypeScript**: no `any`/`as unknown as` escapes in production; `throw_params: DiceThrowParams`, `seed: number` properly typed; tsc -b clean. ✓

### Observations (10)
1. [VERIFIED] AC4 dF 0-face label — evidence: ../dice-lib/src/dF.ts:25-26 set `label: "0"` for the two value-0 faces; agrees with UI `faceGlyph(0)='0'` (FateDiceTray.tsx:31). Complies with AC4 and the dice/readout-agreement intent.
2. [VERIFIED][SEC] FateRollPayload required fields + extra='forbid' — evidence: protocol/models.py:1129-1131 (no defaults) under `model_config={'extra':'forbid'}`; fail-loud. Corroborated by security subagent (boundary validation, no client-supplied data).
3. [VERIFIED] Projection emits real gesture+seed — evidence: fate_projection.py:216-217; wiring test `test_projection_emits_a_real_throw_params_gesture` asserts a non-degenerate ThrowParams + int seed.
4. [VERIFIED] Handler per-turn seed — evidence: fate_action.py generate_dice_seed(`{genre}:{world}:{player}`, interaction), identical keying to dice_throw.py:201; per-turn uniqueness drives UI re-throw.
5. [VERIFIED] UI replay parity — evidence: FateDiceTray.tsx:48 `replayThrowParams(roll.throw_params, roll.seed, D6_RADIUS)` mirrors InlineDiceTray.tsx:264; throwParams/rollKey now wired (was `null`/`0`). dice-lib exports both symbols (index.ts:15,48).
6. [LOW] rollKey keyed off `roll.seed` rather than a monotonic counter — re-throw relies on per-turn seed uniqueness (interaction-keyed); worst case is a cosmetic no-reanimate on an (unlikely) same-player same-interaction double-roll. Non-blocking. FateDiceTray.tsx:62.
7. [MEDIUM][SILENT] room-None drops the roll (logs error, returns []) — PRE-EXISTING, not in 125-4's changed lines, logs loudly; deferred as out-of-scope with a tracked Improvement finding. fate_action.py.
8. [LOW][SILENT] `_fallback_seed` optional default — deliberate, documented, TEA-test-required; downgraded with rationale, tracked as non-blocking Improvement. fate_projection.py.
9. [SEC] Security subagent clean — no attacker-controllable data reaches other clients; seed is an FNV-1a hash of server-owned state; broadcast is a public dice animation (perception-safe).
10. [VERIFIED] No stale docs — Dev updated the dF.ts header comment and the FateDiceTray "idle pickup row" comment to match the new behavior; new docstrings added. [DOC] self-assessed (analyzer disabled).

**Dispatch tags:** [SEC] clean (subagent). [SILENT] 2 deferred (subagent). [EDGE] self-assessed — seed u64 precision matches the accepted DICE_RESULT pattern, dice tuple fixed-arity, `_fallback_seed` min=1; no unhandled boundary. [TEST] self-assessed — assertions are concrete (faces, gesture components, seed type, JSON round-trip, re-throw-differs); the two "guard" tests are transitional per TEA's note, not vacuous. [TYPE] self-assessed — typed fields, no escapes, pyright/tsc clean. [DOC] self-assessed — comments updated, no stale docs. [SIMPLE] self-assessed — tiny helper + constant, reuse over duplication, no over-engineering. [RULE] self-assessed — see Rule Compliance above.

### Devil's Advocate
Let me argue this is broken. **Could the dice show the wrong faces?** Yes — and this is the sharpest critique: the 3D dice tumble from a constant gesture + seed and settle on whatever physics produces, NOT on `roll.dice`. A player could see the 3D dice read `+ + − 0` while the text readout says `+ + 0 −`. For a legibility story aimed at Sebastien/Jade, contradictory dice are arguably *worse* than idle dice. **Verdict on that:** it's a real concern, but (a) the text readout remains the authoritative surface and is unchanged, (b) exact-face fidelity requires a DiceScene "settle-to-predetermined-faces" capability that is explicitly out of 125-4's dice-lib (label-only) scope, and (c) TEA and Dev both flagged it as a follow-up. The story's stated ACs (emit throw_params/seed; pass throwParams through) are fully met. This is a scope boundary, not a defect in the delivered scope — recorded as a finding for Architect/Keith to rule on. **Could a malicious client forge a roll?** No — throw_params is a server constant and seed is server-derived from the authenticated player id (not inbound msg.player_id, which is spoof-rejected at fate_action.py:71-76); security subagent confirmed. **Could a huge u64 seed break the client?** It loses precision as a JS number, but that's the identical situation the live DICE_RESULT path already runs (InlineDiceTray passes diceResult.seed), so no new risk. **What if two identical rolls fire in one interaction?** Same seed → same rollKey → no re-throw (cosmetic only); requires same player + same interaction, which the per-action interaction counter prevents. **What if room is None?** Pre-existing loud-logged drop, unchanged. None of these rise to Critical/High within the delivered scope.

### Verdict rationale
All ACs met, GREEN across three repos, security clean, faithful to existing patterns, wired end-to-end with production consumers (FatePanel/FateConflictSurface/GameBoard). The two silent-failure findings are pre-existing/out-of-scope or deliberate-and-documented; the exact-face-fidelity question is an explicitly-scoped follow-up. No Critical/High.

**Data flow traced:** FATE_ACTION → `dispatch_fate_action` → `FateOutcome` → `build_fate_roll_payload(outcome, seed=generate_dice_seed(...))` → `FateRollPayload{throw_params, seed}` → `room.broadcast(FateRollMessage)` → client `useStateMirror` → `FateDiceTray` → `replayThrowParams(...)` → `DiceScene{throwParams, rollKey}`. Safe: every field is server-authoritative; the new fields are animation-only.
**Pattern observed:** server→client replay-animation parity with DICE_RESULT/InlineDiceTray — fate_projection.py + FateDiceTray.tsx mirror the established dice path.
**Error handling:** required fields fail loud at the pydantic boundary; the one pre-existing room-None drop logs at error level.

**Handoff:** To SM (Vizzini) for finish-story.