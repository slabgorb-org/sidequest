---
story_id: "152-1"
jira_key: null
epic: "152"
workflow: "tdd"
---
# Story 152-1: [ENGINE] WWN defensive actions — remove the native brace/break_contact reprisal-mitigation; add Total Defense (+2 AC/Shock immunity) + Fighting Withdrawal/Run disengage (WWN SRD 2.4.4)

## Story Details
- **ID:** 152-1
- **Jira Key:** (no Jira integration)
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 5
- **Priority:** p1

## Acceptance Criteria
- Native defensive scaffolding is removed from the WWN path: `_defensive_posture_for_reprisal`'s brace tier-delta mitigation + break_contact full-prevent no longer run under a WithoutNumberRulesetModule binding; the opponent attacks once on its slot vs the defender's AC (no per-beat reprisal model).
- A committed Total Defense raises the defender's Melee & Ranged AC by +2 and grants Shock immunity until the start of their next turn (WWN SRD 2.4.4), via the existing AC math — an opponent attack that hits at base AC misses under Total Defense, and Shock is suppressed.
- A committed Fighting Withdrawal + Run avoids the free melee attack a flee would otherwise provoke (WWN SRD 2.4.4); it does NOT cancel the opponent's own-turn attack.
- test_106_2_wwn_defensive_reprisal is REWRITTEN to assert WWN semantics (AC bump, Shock immunity, free-attack-on-flee) — not native tier-delta mitigation or whole-attack prevention; no native magnitude reproduced.
- OTEL: the opponent-attack span carries the defender's committed WWN action (e.g. total_defense) and the AC delta applied, so the GM panel sees the defense fire. 108-8 invariants stay green (closed allowlist; native packs' authored ids resolve on the native engine).
- All magnitudes are WWN-SRD-verbatim (+2 AC, Shock immunity); nothing invented; no content changes.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-20T18:16:33Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-20T16:44:59Z | 2026-06-20T16:47:03Z | 2m 4s |
| red | 2026-06-20T16:47:03Z | 2026-06-20T17:36:28Z | 49m 25s |
| green | 2026-06-20T17:36:28Z | 2026-06-20T17:57:49Z | 21m 21s |
| review | 2026-06-20T17:57:49Z | 2026-06-20T18:06:56Z | 9m 7s |
| red | 2026-06-20T18:06:56Z | 2026-06-20T18:10:16Z | 3m 20s |
| green | 2026-06-20T18:10:16Z | 2026-06-20T18:12:23Z | 2m 7s |
| review | 2026-06-20T18:12:23Z | 2026-06-20T18:16:33Z | 4m 10s |
| finish | 2026-06-20T18:16:33Z | - | - |

## Sm Assessment

**Routing decision:** New work, clean state — story 152-1 was `backlog`, no active session, no archived session. Confirmed it is NOT a stale/already-done reactivation (a recurring trap). A `plan(152-1)` commit (22fc3acc) and a design doc (`docs/superpowers/specs/2026-06-20-wn-full-action-set-design.md`) exist; both are the technical source of truth for the RED/GREEN agents.

**Scope (server-only, TDD/phased):** This is the ADR-143 doctrine story made concrete. The original 152-1 framing (synthesize native brace/break_contact + restore 106-2 reprisal-mitigation) was itself the trap — porting native mechanics into the WWN binding. Keith corrected it 2026-06-20. The work is: (1) REMOVE native defensive-reprisal scaffolding from the WWN path, (2) ADD WWN Total Defense via existing AC math (+2 AC / Shock immunity), (3) ADD Fighting Withdrawal/Run disengage, (4) REWRITE test_106_2_wwn_defensive_reprisal to WWN semantics. All magnitudes SRD-verbatim; no invented numbers; no content changes.

**Guardrails for downstream agents:**
- This is a REMOVE-native-then-ADD-SRD story. If TEA/Dev catches itself tuning, converting, or gating a native mechanic to "make it work with" WWN — STOP. That's the trap the story exists to delete.
- Preserve 108-8 invariants: closed allowlist (bogus ids still raise) + `isinstance(WithoutNumberRulesetModule)` gate so native packs stay on the native engine.
- OTEL is the lie detector here: the opponent-attack span MUST carry the defender's committed action + AC delta, per the OTEL Observability Principle. A green test with no span is not done.
- Per Without-Number wiring checklist: watch the 3 commonly-omitted touchpoints (spans `__init__` re-export, `dice.py` downed-seam guard + `_physical_save_target_for` isinstance — WwnConfig extends Swn NOT Cwn → tuple, OTEL span-assertion tests).

**Verification expectation:** Gate the full server suite against the known ~258-269 hermeticity baseline (set `SIDEQUEST_DATABASE_URL`); any failure outside that baseline in the blast radius is a regression. Do not panic at the raw count.

**Decision:** Setup complete, branch created, context written. Hand off to TEA (Fezzik) for RED. No blockers.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Engine-behavior story; AC4 explicitly mandates rewriting the test file.

**Test File:** `sidequest-server/tests/integration/test_106_2_wwn_defensive_reprisal.py` — full REWRITE from the native brace/break_contact reprisal-mitigation model to genuine WWN defense (Total Defense / Fighting Withdrawal / Run). Drives the production `dispatch_dice_throw → run_wn_round` seam on the real heavy_metal (`ruleset: wwn`) pack. Removed the 3 native `_defensive_posture_for_reprisal` unit tests (they pinned the scaffolding AC1 deletes); kept the SWN no-regression guard.

**Tests Written:** 10 tests covering all 6 ACs.
**Status:** RED (verified — see below). Ready for Dev (Inigo Montoya).

| AC | Test(s) | Status |
|----|---------|--------|
| AC1 opponent attacks once on its slot (synthesized opponent strike) | `test_wwn_opponent_attacks_on_its_slot_with_a_synthesized_strike` | failing (assert: PC lost 0 — reprisal skipped) |
| AC1 native flat-mitigation removed | `test_total_defense_is_not_flat_mitigation_a_real_hit_takes_full_damage` | failing |
| AC2 Total Defense +2 AC flips a marginal hit to a miss | `test_total_defense_flips_a_marginal_hit_to_a_miss` | failing |
| AC2 Total Defense Shock immunity | `test_total_defense_grants_shock_immunity` | failing (DiceDispatchError: unknown beat_id 'total_defense') |
| AC3 plain Run provokes a free attack | `test_plain_run_provokes_a_free_opportunity_attack` | failing (unknown beat_id 'run') |
| AC3 Fighting Withdrawal avoids the free attack | `test_fighting_withdrawal_avoids_the_free_attack` | failing (unknown beat_id 'fighting_withdrawal') |
| AC3 neither cancels the opponent's own-turn attack | `test_fighting_withdrawal_does_not_cancel_the_opponent_own_turn_attack` | failing |
| AC4 rewrite to WWN semantics | (the whole file) | done |
| AC5 OTEL span carries committed action + AC delta | `test_total_defense_span_carries_committed_action_and_ac_delta` | failing |
| AC5 wiring through the real WWN sealed walk | `test_total_defense_round_resolves_through_the_wwn_sealed_walk` | failing |
| AC6 SRD-verbatim magnitudes (+2 AC) | asserted in the AC2 tests (`ac_delta==2`, `target_ac==base+2`) | n/a |
| no-regression (scope-pin) | `test_swn_sibling_without_initiative_keeps_legacy_reprisal_no_raise` | **passing** (green-by-design) |

### Rule Coverage

| Rule (lang-review/python.md) | How the suite enforces it | Status |
|------|---------|--------|
| Tests must have meaningful (non-vacuous) assertions | every test asserts a specific value (HP loss == 8, `target_ac == base+2`, `ac_delta == 2`, exact span counts) — no `assert True`/truthy-only | ok |
| `@pytest.mark.skip(if)` needs a reason | `pytestmark = skipif(..., reason="sidequest-content not on disk")` | ok |
| `mock.patch` on the correct target | `monkeypatch.setattr("random.randint", ...)` patches the global RNG the dispatch consumes (matches the existing 102-4/108-8 suite) | ok |
| No Silent Fallbacks / fail-loud (closed allowlist) | the new ids stay a CLOSED allowlist — a bogus id still raises `DiceDispatchError` (guarded by `test_108_8::test_unknown_action_id_under_zero_beats_still_raises`, kept green) | ok (108-8) |

**Rules checked:** the test-quality + fail-loud subset above. The remaining lang-review checks (type annotations, error-path logging, resource `with`, injection) govern Dev's GREEN production code, not this test file.
**Self-check:** 0 vacuous tests (reviewed every assertion for specific-value checks).

**Wiring test:** `test_total_defense_round_resolves_through_the_wwn_sealed_walk` (asserts `wwn.round.resolved`) + every behavioral test drives the real `dispatch_dice_throw` entry — not unit calls.

**Handoff:** To Dev (Inigo Montoya) for GREEN. See `## Design Deviations` → TEA for the two major scope expansions (Keith-ruled) and `## Delivery Findings` → TEA for the blocking opponent-strike-synthesis precondition + the new span/allowlist contract.

### Rework R1 (TEA — red, post-review)

**Reviewer REJECT (1 MEDIUM + 2 LOW):** added one RED test for the MEDIUM:
- `test_run_does_not_re_attack_a_fleer_downed_mid_flight` — two blades vs a 6-HP fleer; the first opportunity attack downs the PC, so exactly ONE `opportunity_attack` span must fire. **RED verified: 2 spans** (the opportunity loop re-attacks the downed fleer — it lacks the `encounter.resolved`/fleer-downed guard the own-turn slot has at `wn_round.py:290`/`:360`). Other 10 tests stay green (11 total: 10 pass, 1 RED).

**Dev's GREEN scope (3 items):**
1. [MEDIUM] Guard the opportunity-attack loop in `wn_round.py` (break/skip once `encounter.resolved` or the fleer's core drops ≤0) so this test goes green.
2. [LOW] Document the `opp_core is None` → "treated as live" parity with `_first_live_actor` at `wn_round.py:402` (keep behavior).
3. [LOW] Update the stale `move`-deferred comment at `beat_filter.py:118-120`.

**No new deviations** — the rework test implements the Reviewer's MEDIUM finding directly.
**Handoff:** To Dev (Inigo) for the guard + 2 doc fixes.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (server only):**
- `sidequest/game/beat_filter.py` — added the closed WN defensive/move action allowlist (`total_defense`/`fighting_withdrawal`/`run`); `is_wn_flee_action` / `is_wn_nonoffensive_action` helpers; `wn_action_beat` synthesizes the new ids as non-strike `BeatKind.push` beats (the `attack` strike path unchanged).
- `sidequest/server/dispatch/dice.py` — rewrote `_defensive_posture_for_reprisal` to the WWN AC posture (`total_defense` → +2 AC + Shock immunity; brace tier-delta + break_contact prevent REMOVED); `_resolve_opponent_reprisal` now synthesizes the opponent's WN strike on a zero-beat def (so it attacks once on its slot), applies the +2 AC + explicit Shock immunity, deals FULL damage on a connecting hit (no flat mitigation), removed the whole-attack-prevent block, and the span/watcher carry `defender_beat` + `ac_delta` + `source` (`opponent_reprisal` | `opportunity_attack`). Removed now-dead imports (`BeatKind`, `resolve_tier_deltas`).
- `sidequest/server/dispatch/wn_round.py` — player-slot non-offensive intercept: `run` provokes one free `source="opportunity_attack"` from each adjacent live opponent; `run`/`fighting_withdrawal` set `withdrawn`; `total_defense` holds; each emits a MECHANICAL-TRUTH narrator hint + a `wn_nonoffensive_action` OTEL watcher event.

**Tests:** 17/17 GREEN (test_106_2 10/10 + test_108_8 7/7).
**Regression:** blast-radius subsystem run (13 files) = **74 passed, 6 skipped, 6 failed**; all 6 failures are `unknown beat_id 'cast_spell'` in `test_dice_path_spell_cast_102_2.py`, confirmed pre-existing on HEAD~1 and owned by **story 152-2** (cast synthesis). No new failures from 152-1.
**Branch:** `feat/152-1-wwn-defensive-actions` (pushed to slabgorb-org/sidequest-server).

**Self-review:**
- ✅ Wired end-to-end: behavior is reached from the production `dispatch_dice_throw → run_wn_round` seam (the wiring test asserts `wwn.round.resolved`); not unit-only.
- ✅ Follows project patterns: synthesis mirrors the existing `is_item_use_beat` / `wn_action_beat("attack")` intercepts; WWN-gated via `isinstance(WithoutNumberRulesetModule)`.
- ✅ All 6 ACs met (see TEA Assessment AC↔test table — all now green).
- ✅ OTEL: every defensive decision emits a span/watcher event (opponent-attack span `ac_delta`+`source`; `wn_nonoffensive_action` event) — the GM-panel lie detector.
- ✅ 108-8 invariants intact (closed allowlist; isinstance gate; native packs unaffected).

**Handoff:** To Reviewer (Westley) for code review.

### Rework R1 (Dev — green, post-review)

Addressed the Reviewer REJECT (1 MEDIUM + 2 LOW), 2 files:
- **[MEDIUM]** `wn_round.py` opportunity-attack loop now breaks once `encounter.resolved` OR the fleer's core drops ≤0 — a fleer downed by the first opportunity attack is no longer re-attacked by the remaining opponents (no duplicate resolution close). Mirrors the own-turn slot guard. Makes `test_run_does_not_re_attack_a_fleer_downed_mid_flight` green.
- **[LOW]** `wn_round.py:402` — added the `opp_core is None` → "treated as live" parity comment citing `_first_live_actor` (behavior unchanged).
- **[LOW]** `beat_filter.py:118-120` — updated the stale `move`-deferred comment to reflect that 152-1 implemented `run`/`fighting_withdrawal`/`total_defense`.

**Tests:** test_106_2 **11/11** (incl. the new guard test); test_108_8 7/7; blast-radius re-run **57 passed / 0 failed / 6 expected skips**. Branch pushed (`055b3765`).
**Handoff:** Back to Reviewer (Westley) for re-review.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (blocking): The opponent never attacks on the current zero-beat WWN combat def — `_resolve_opponent_reprisal` finds no strike beat in the empty `cdef.beats` and skips (`no_strike_beat`, measured PC_LOST=0 under MAX rolls). Affects `sidequest/server/dispatch/dice.py` (`_resolve_opponent_reprisal` must WN-synthesize the opponent's strike, mirroring `wn_action_beat("attack")`, so the opponent attacks once on its slot vs the defender's AC). Precondition for every AC2/AC3 behavioral test. *Found by TEA during test design.*
- **Gap** (non-blocking): Story sizing — 152-1 as scoped by Keith (full flee/Run opportunity-attack mechanic + opponent-strike synthesis) is materially larger than its 5-pt framing and the design doc's defender-only framing. The design doc `docs/superpowers/specs/2026-06-20-wn-full-action-set-design.md` should be amended (its "Open question" YAGNI stance on `move` is now superseded). Affects sprint sizing + the design doc. *Found by TEA during test design.*
- **Improvement** (non-blocking): New span/contract values this story introduces, for Dev to honor and Reviewer to check: span `source="opportunity_attack"` (free attack on flee) vs the existing `source="opponent_reprisal"` (own-turn slot); span `ac_delta` (=2 under Total Defense) and boosted `target_ac`; new closed-allowlist WN action ids `total_defense`/`fighting_withdrawal`/`run`. Affects `sidequest/server/dispatch/dice.py` + `sidequest/game/beat_filter.py` (`_WN_ACTION_BEAT_IDS`) + the opponent-attack span emit. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): `cast_spell` is still unsynthesized on the zero-beat WWN combat def — `test_dice_path_spell_cast_102_2.py` is 6/6 RED with `DiceDispatchError: unknown beat_id 'cast_spell' ... available: []` (confirmed pre-existing on HEAD~1, NOT caused by 152-1). This is exactly **story 152-2**'s scope (route a wwn `cast_spell` commit to the cast spine before the cdef lookup, mirroring the item-use intercept). Affects `sidequest/server/dispatch/dice.py` + `wn_round.py`. *Found by Dev during implementation.*
- **Improvement** (non-blocking): The new WWN action ids (`total_defense`/`fighting_withdrawal`/`run`) need a player-facing surface (the UI action menu / `wn_attack`-style narrator tool) so players can actually commit them — this story wires the engine resolution only. A follow-up should expose them in `sidequest-ui` (the WN action panel) and/or the narrator tool list. Affects `sidequest-ui` action panel + the narrator tool surface. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): The opportunity-attack loop has no `encounter.resolved`/target-downed guard — a fleer downed by the first opportunity attack is re-attacked by remaining opponents in a multi-opponent flee. Affects `sidequest/server/dispatch/wn_round.py:391-419` (mirror the own-turn `encounter.resolved` guard; add a multi-opponent flee test). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Document the `opp_core is None` → "treated as live" parity with `_first_live_actor` at `wn_round.py:402` to prevent a future maintainer silently diverging the two liveness rules. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Stale comment at `sidequest/game/beat_filter.py:118-120` describes the `move`/disengage action as "deferred" — 152-1 implemented it; update the comment. *Found by Reviewer during code review.*
- **Resolution** (re-review R1): all three Round-0 findings above are FIXED and re-verified (guard + new passing test; both doc fixes); re-review subagents (preflight/silent-failure/security) all CLEAN. No new findings. *Confirmed by Reviewer during re-review.*

## Impact Summary

**Upstream Effects:** 1 findings (1 Gap, 0 Conflict, 0 Question, 0 Improvement)
**Blocking:** 1 BLOCKING items — see below

**BLOCKING:**
- **Gap:** The opportunity-attack loop has no `encounter.resolved`/target-downed guard — a fleer downed by the first opportunity attack is re-attacked by remaining opponents in a multi-opponent flee. Affects `sidequest/server/dispatch/wn_round.py:391-419`.


### Downstream Effects

- **`sidequest/server/dispatch`** — 1 finding

### Deviation Justifications

4 deviations

- **Fighting Withdrawal scoped to the FULL flee/Run opportunity-attack mechanic**
  - Rationale: Keith ruled (2026-06-20, /pf-work session) FULL scope over the minimal "negative-only" reading. The engine has no flee/free-attack concept today, so this is net-new.
  - Severity: major
  - Forward impact: 152-1 is materially larger than its 5-pt framing; design doc should be amended. New span-`source` contract value `opportunity_attack` is established here.
- **Opponent-strike synthesis pulled into 152-1**
  - Rationale: Keith ruled (2026-06-20) to include it in 152-1; without it NO defensive action is demonstrable end-to-end.
  - Severity: major
  - Forward impact: defenses are untestable through the real round until this lands; it is a precondition for every AC2/AC3 behavioral test.
- **test_106_2 native unit tests on `_defensive_posture_for_reprisal` dropped, not ported**
  - Rationale: AC1 removes the brace/break_contact branches; keeping unit tests on them would pin the very scaffolding the story deletes.
  - Severity: minor
  - Forward impact: none — replaced by behavioral WWN tests through the real dispatch seam.
- **Synthesized defensive/move beats use `BeatKind.push`**
  - Rationale: a valid, non-strike, non-`angle` kind is needed for the BeatDef to construct; `push` ("pursue a discrete narrative goal — flee/disengage") is the closest fit.
  - Severity: minor
  - Forward impact: none — the kind carries no WWN-path semantics; a future UI/menu surface for these actions reads the id/label, not the kind.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Fighting Withdrawal scoped to the FULL flee/Run opportunity-attack mechanic**
  - Spec source: context-story-152-1.md AC3 + design doc `docs/superpowers/specs/2026-06-20-wn-full-action-set-design.md` (152-1 entry says "wire the deferred move action; disengage avoids the free attack on a flee"; its "Open question" flags `move` as YAGNI — an internal contradiction).
  - Spec text: "A committed Fighting Withdrawal + Run avoids the free melee attack a flee would otherwise provoke; it does NOT cancel the opponent's own-turn attack."
  - Implementation: RED tests pin a NEW opportunity-attack mechanic — a plain `run` (flee) commit provokes one free opponent attack (`encounter.opponent_attack_resolved` with `source="opportunity_attack"`); `fighting_withdrawal` suppresses it; neither cancels the opponent's own-turn slot attack (`source="opponent_reprisal"`).
  - Rationale: Keith ruled (2026-06-20, /pf-work session) FULL scope over the minimal "negative-only" reading. The engine has no flee/free-attack concept today, so this is net-new.
  - Severity: major
  - Forward impact: 152-1 is materially larger than its 5-pt framing; design doc should be amended. New span-`source` contract value `opportunity_attack` is established here.
- **Opponent-strike synthesis pulled into 152-1**
  - Spec source: context-story-152-1.md AC1 ("the opponent attacks once on its slot vs the defender's AC"); not mentioned in the design doc.
  - Spec text: "the opponent attacks once on its slot vs the defender's AC (no per-beat reprisal model)."
  - Implementation: RED test requires the opponent to attack on the current zero-beat WWN combat def. MEASURED today: `_resolve_opponent_reprisal` finds no strike beat in the empty `cdef.beats` and SKIPS (`dice.opponent_reprisal_skipped reason=no_strike_beat`, PC_LOST=0 under max rolls). Dev must synthesize the opponent's WN strike (mirror of `wn_action_beat("attack")`) so there is an attack to defend against.
  - Rationale: Keith ruled (2026-06-20) to include it in 152-1; without it NO defensive action is demonstrable end-to-end.
  - Severity: major
  - Forward impact: defenses are untestable through the real round until this lands; it is a precondition for every AC2/AC3 behavioral test.
- **test_106_2 native unit tests on `_defensive_posture_for_reprisal` dropped, not ported**
  - Spec source: context-story-152-1.md AC4 ("REWRITTEN to assert WWN semantics ... not native tier-delta mitigation or whole-attack prevention").
  - Spec text: "REWRITE test_106_2_wwn_defensive_reprisal to WWN semantics."
  - Implementation: the old file's 4 still-passing tests (`test_posture_helper_*` direct-calling the brace/push helper, asserting tier-delta mitigation + push-prevents) are REMOVED — they pin the native model AC1 deletes. The SWN-sibling no-regression guard is KEPT.
  - Rationale: AC1 removes the brace/break_contact branches; keeping unit tests on them would pin the very scaffolding the story deletes.
  - Severity: minor
  - Forward impact: none — replaced by behavioral WWN tests through the real dispatch seam.

### Dev (implementation)
- **Synthesized defensive/move beats use `BeatKind.push`**
  - Spec source: TEA tests (test_106_2) + context-story-152-1.md (no BeatKind specified).
  - Spec text: the tests pin behavior (AC posture, opportunity attack, disengage) and the span/id contract, not the BeatKind.
  - Implementation: `wn_action_beat` synthesizes `total_defense`/`fighting_withdrawal`/`run` as `BeatKind.push` (no `strike` channel, no `target_tag` — `BeatKind.angle` would have required one). The kind is inert on the WWN path: run/fighting_withdrawal are intercepted before the strike resolver and total_defense's effect is the AC posture.
  - Rationale: a valid, non-strike, non-`angle` kind is needed for the BeatDef to construct; `push` ("pursue a discrete narrative goal — flee/disengage") is the closest fit.
  - Severity: minor
  - Forward impact: none — the kind carries no WWN-path semantics; a future UI/menu surface for these actions reads the id/label, not the kind.
- **No other deviations** — the id contract (`total_defense`/`fighting_withdrawal`/`run`), the span fields (`defender_beat`, `ac_delta`, `source=opportunity_attack|opponent_reprisal`), the +2 AC / Shock-immunity magnitudes, and the opponent-strike synthesis were implemented exactly as TEA's RED suite specified.

### Reviewer (audit)
- **TEA: Fighting Withdrawal → full flee/Run opportunity-attack mechanic** → ✓ ACCEPTED: Keith-ruled (2026-06-20) over the minimal reading; resolves the design-doc self-contradiction in favor of the SRD. Sound.
- **TEA: Opponent-strike synthesis pulled into 152-1** → ✓ ACCEPTED: required by AC1 ("opponent attacks once on its slot"); measured precondition (reprisal was skipping on the zero-beat def). Correct call.
- **TEA: native `_defensive_posture_for_reprisal` unit tests dropped** → ✓ ACCEPTED: those tests pinned the exact scaffolding AC1 deletes; behavioral WWN tests through the real seam are the right replacement. The SWN no-regression guard was correctly kept.
- **Dev: synthesized defensive/move beats use `BeatKind.push`** → ✓ ACCEPTED: `angle` would require a `target_tag` (BeatDef validator); `push` is non-strike, no `target_tag`, and inert on the WWN path (verified — only `damage_channel` is read there). Reasonable.
- **Dev: "No other deviations"** → ✓ ACCEPTED: confirmed against the diff — the id/span/magnitude contract matches TEA's RED suite.
- **No UNDOCUMENTED deviations found** — the implementation matches the logged scope; the REJECT findings are correctness/doc gaps within scope, not undocumented spec divergences.

## Technical Notes

### Design Document
- **Location:** `docs/superpowers/specs/2026-06-20-wn-full-action-set-design.md`
- **Key Ruling (Keith, 2026-06-20):** Do NOT shape native mechanics into the SRD binding (ADR-143 trap). Remove the native defensive-reprisal scaffolding and add the genuine WWN defensive actions: Total Defense (Instant Action, +2 AC + Shock immunity) and Fighting Withdrawal/Run (disengage to avoid free attack on flee).

### Execution Path

**REMOVE from WWN path:**
1. `_defensive_posture_for_reprisal()` brace tier-delta mitigation handler
2. `break_contact` prevent-whole-attack logic
3. Per-beat reprisal model (the opponent attacks once on its own initiative, not per-beat)

**ADD to WWN path:**
1. **Total Defense** — wire as a committed defensive action that raises Melee/Ranged AC by +2 and grants Shock immunity until the start of the next turn. Use the existing AC math (opponent's d20+hit vs boosted AC).
2. **Fighting Withdrawal + Run** — wire the deferred `move` action to enable disengage from melee so a following Run provokes NO free attack per WWN SRD 2.4.4.

**Rewrite test_106_2_wwn_defensive_reprisal:**
- Replace brace-mitigation assertions with AC bump + Shock-immunity proofs
- Replace break_contact-prevent assertions with free-attack-on-flee avoidance proofs
- Remove tier-delta mitigation and whole-attack-prevention patterns
- Assert OTEL spans carry the defender's committed action and AC delta

**Invariants to preserve:**
- 108-8 closed allowlist (bogus ids still raise)
- `isinstance(ruleset, WithoutNumberRulesetModule)` gate (native packs resolve on native engine)
- All magnitudes from WWN SRD (+2 AC, Shock immunity) — nothing invented
- No content changes

### Key Implementation Points
- Magnitudes are **SRD-verbatim** — look up in WWN SRD 2.4.4, never invent
- Preserve `beat_filter._WN_ACTION_BEAT_IDS` allowlist semantics (add new ids if needed)
- OTEL span contract: opponent-attack span must carry `defender_committed_action` and `ac_delta_applied`
- Story 152-2 must land before 152-3 (chargen test reconciliation depends on the full action set)

## Subagent Results

_Re-review round (R1) — after the rework. (Round 0 found 1 MEDIUM + 2 LOW → REJECT; all three are now resolved, see the assessment.)_

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (18 tests GREEN; branch lint+format clean; 3 pre-existing lint hits outside blast radius) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — re-checked the guard manually (no premature break; fleer alive at slot 1) |
| 3 | reviewer-silent-failure-hunter | Yes | clean | none | N/A (guard can't break before the first attack; None-fleer-core proceed is intentional; both arms belt-and-suspenders) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — the new guard test asserts a specific span count (non-vacuous) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — verified the stale `move` comment is now corrected |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — no type changes in the rework |
| 7 | reviewer-security | Yes | clean | none | N/A (guard is a bounded early-exit on live aliases; no double-fire, no unbounded loop, no resolved-state mutation) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — rework is +49/-2; no over-engineering |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — Rule Compliance enumeration (below) unchanged by the rework |

**All received:** Yes (3 enabled returned clean; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 0 new (re-review). Round-0's 3 findings (1 MEDIUM + 2 LOW) all resolved by the rework + the new guard test.

## Rule Compliance

Enumerated against `.pennyfarthing/gates/lang-review/python.md` + SOUL.md + sidequest-server CLAUDE.md, for every changed production symbol:

- **#1 Silent exception swallowing:** No `try/except` added. The non-WWN `no_strike_beat` path still warns + returns `[]` (pre-existing, not introduced; restructured to the `else` of the new isinstance gate — now narrower). `_resolve_opponent_reprisal` keeps its fail-loud warnings. COMPLIANT (with the pre-existing note dismissed).
- **#3 Type annotations at boundaries:** `is_wn_flee_action`/`is_wn_nonoffensive_action` → `(beat_id: str) -> bool`; `wn_action_beat` → `(str) -> BeatDef`; `_wn_nonoffensive_narrator_hint(actor_name: str, beat_id: str) -> str`; `_resolve_opponent_reprisal` new `source: str = "opponent_reprisal"`; `_defensive_posture_for_reprisal(defender_commit: WnSealedCommit | None) -> tuple[str, int, bool]`. All annotated. COMPLIANT.
- **#4 Logging coverage/correctness:** No new error path without logging; the new `wn_nonoffensive_action` decision emits an OTEL watcher event (per the OTEL Observability Principle). COMPLIANT.
- **#6 Test quality:** test_106_2 rewrite — every test asserts specific values (HP==8, target_ac==base+2, ac_delta==2, span counts), `monkeypatch.setattr("random.randint", ...)` patches the correct global target, skipif carries a reason. COMPLIANT (preflight: no vacuous assertions).
- **#2 mutable defaults / #5 paths / #7 resources / #8 deserialization / #9 async / #11 input-validation / #12 deps:** N/A — no mutable defaults, no path/file/IO, no deserialization, no async, no new deps; the only external input (beat_id) flows through a CLOSED allowlist (security-confirmed). COMPLIANT.
- **#10 Import hygiene:** New imports are explicit (no star); no new cycle (wn_round still imports `_resolve_opponent_reprisal` at function level per the existing cycle-proofing). Removed now-dead `BeatKind`/`resolve_tier_deltas` from dice.py. COMPLIANT.
- **SOUL "Bind the Ruleset, Don't Balance It" (ADR-143):** the native brace tier-delta + break_contact prevent are REMOVED, not retuned; defense is pure AC. COMPLIANT (this is the story's thesis).
- **SOUL "No Silent Fallbacks":** closed allowlist (bogus id raises — 108-8 guard green); WWN-gated synthesis; non-WWN still fails loud. COMPLIANT.

## Reviewer Observations

- [VERIFIED] Closed allowlist holds — `wn_action_beat` raises `PackError` on a non-allowlisted id; dispatch + wn_round gate on `is_wn_action_beat`/`is_wn_nonoffensive_action` then raise `DiceDispatchError` on miss. Evidence: `beat_filter.py:204-206`, 108-8's `test_unknown_action_id_under_zero_beats_still_raises` stays green. Complies with No-Silent-Fallbacks.
- [VERIFIED] Native scaffolding fully removed — `grep defense_mitigation|defense_prevent|resolve_tier_deltas|BeatKind` in dice.py is clean; the brace/break_contact branches and their span fields are gone. Complies with ADR-143.
- [VERIFIED] AC math safe — `target_ac = int(player_core.armor_class)` (typed `int=10`) `+ defense_ac_bonus` (2 or 0); no None/overflow path ([SEC] confirmed).
- [MEDIUM][EDGE] Opportunity-attack loop (`wn_round.py:391-419`) has no `encounter.resolved`/fleer-downed guard, unlike the own-turn slot (`wn_round.py:290`, `:360`). In a multi-opponent flee, a fleer downed by the first opportunity attack is still attacked by the remaining opponents, and `_close_reprisal_depletion` re-resolves — duplicate downed-target spans/directives (OTEL-honesty + GM-immersion concern). Multi-opponent combat is mainstream, not an edge.
- [LOW][SILENT] `wn_round.py:402` — the dead-opponent guard `if opp_core is not None and opp_core.hp.current <= 0: continue` treats a coreless opponent as live. This is CORRECT parity with `_first_live_actor` (documented "no resolvable core counts as live") and [SEC]-confirmed as no new exposure — but it reads like an incomplete liveness filter and lacks the explanatory comment.
- [LOW][DOC] `beat_filter.py:118-120` — stale comment: "`move` is the WN disengage action and is deferred (no resolution semantics on the dice path yet — story follow-up)." 152-1 implemented the disengage actions (`run`/`fighting_withdrawal`); the comment now contradicts the code.
- [SILENT] (dismissed) `dice.py` non-WWN `no_strike_beat` return — pre-existing on develop, not introduced by this diff (the diff narrowed it to the non-WWN else-branch, an improvement).
- [TYPE]/[SIMPLE]/[TEST]/[RULE] (subagents disabled) — covered by the manual Rule Compliance enumeration above; no additional findings.

## Devil's Advocate

Assume this code is broken. The most exposed surface is the brand-new opportunity-attack loop, which is the only place the diff resolves an attack *outside* an initiative slot. A career-GM table runs multi-opponent fights constantly — three thugs, a fleeing thief. The thief commits `run`; the loop fires a free attack from every seated opponent against the same `token`. Nothing in the loop checks whether the target is still standing between attacks, and `_resolve_opponent_reprisal` itself never checks `encounter.resolved`. So the first thug drops the thief, and the second and third thugs still "swing" at a corpse — each emitting an `encounter.opponent_attack_resolved` span and each re-running the depletion close. The GM panel (the project's lie-detector) then shows attacks landing on a downed PC and possibly two resolution rows. That is precisely the mechanical tell the whole product exists to avoid. A confused player reading the narration would see "you collapse… and the second blade runs you through… and the third" — contradictory, immersion-breaking. The own-turn slot guards against exactly this with `if encounter.resolved: continue`; the new loop forgot it. Separately, a malicious/stale client can only send ids — the closed allowlist neutralizes that (verified). A coreless opponent (unseeded fixture/content gap) will generate a phantom opportunity attack — intentional per `_first_live_actor`, but undocumented here, so a future maintainer "fixing" it could silently diverge the two liveness rules. And a maintainer reading the `move … deferred` comment would wrongly conclude disengage isn't implemented and could re-implement it. None of these are security or data-corruption issues, but the multi-opponent over-attack is a real correctness + OTEL-honesty gap in mainstream combat, and the project's own rules forbid deferring "the right fix." That is enough to bounce.

## Reviewer Assessment

**Verdict:** APPROVED (re-review R1, after rework)

**Round 0 → REJECTED** (1 MEDIUM + 2 LOW); **Round 1 → APPROVED** — all three resolved:

| Round-0 finding | Resolution (verified) |
|-----------------|------------------------|
| [MEDIUM][EDGE] opportunity-loop lacked the `encounter.resolved`/fleer-downed guard → multi-opponent flee re-attacks a downed fleer | FIXED: `wn_round.py` loop now `break`s once `encounter.resolved` or the fleer's core ≤0 HP. Pinned by the new RED→GREEN test `test_run_does_not_re_attack_a_fleer_downed_mid_flight` (exactly 1 opportunity span). [SILENT]+[SEC] re-review CLEAN: guard reads live aliases, can't break before the first attack, bounded loop, no double-fire. |
| [LOW][SILENT] coreless-opponent "None = live" undocumented | FIXED: comment added at `wn_round.py` citing `_first_live_actor` parity (behavior unchanged). |
| [LOW][DOC] stale `move`-deferred comment | FIXED: `beat_filter.py` comment now states 152-1 implemented `run`/`fighting_withdrawal`/`total_defense`. |

**Re-review dispatch tags:** [EDGE] no premature break / fleer alive at slot 1 (manual, edge-hunter disabled) · [SILENT] re-review CLEAN (guard not a silent drop; None-fleer-core proceed is intentional) · [SEC] re-review CLEAN (bounded early-exit, no unbounded loop / resolved-state mutation) · [TEST] new guard test asserts a specific span count (non-vacuous) · [DOC] stale comment corrected · [TYPE] no type changes in rework · [SIMPLE] rework is +49/-2, no over-engineering · [RULE] Rule Compliance enumeration unchanged, still COMPLIANT.

**Data flow traced:** client `DICE_THROW.beat_id` → `is_wn_action_beat`/closed allowlist → `wn_action_beat` synthesis (WWN-gated) → seal → `run_wn_round` slot walk → `_resolve_opponent_reprisal` (AC posture + opponent-strike synthesis). Safe at every gate; the previously-flagged loop gap is now guarded.
**Pattern observed:** the non-offensive intercept mirrors the `is_item_use_beat` transient-beat pattern, and now also mirrors the own-turn slot's `encounter.resolved` guard — consistent.
**Error handling:** fail-loud preserved (closed allowlist raises on bogus id; non-WWN no-strike still warns; AC math safe). All 6 ACs met; 18 story tests + blast-radius (57 pass / 0 fail / 6 expected skips) green.

**Handoff:** To SM (Vizzini) for finish-story.