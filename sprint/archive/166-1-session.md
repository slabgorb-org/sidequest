---
story_id: "166-1"
jira_key: ""
epic: "166"
workflow: "spdd"
---
# Story 166-1: Confrontation: flee beat + lethal opponent reprisal double-resolve the same round → 'you escaped / are alive' narration over a 0-HP FALLEN PC; player_dead flag desync + flee location-move commits on death (ADR-139 win-condition liveness / seated-actor HP durability). Loss-path only; clean player_victory is coherent.

## Story Details
- **ID:** 166-1
- **Jira Key:** (none — Jira integration skipped for this story)
- **Workflow:** spdd
- **Epic:** 166 (Playtest fixes — /sq-playtest findings (2026-07-10, mutant_wasteland + elemental_harmony))
- **Stack Parent:** none (not a stacked story)
- **Points:** 5
- **Priority:** p1

## Workflow Tracking
**Workflow:** spdd
**Phase:** finish
**Phase Started:** 2026-07-11T12:20:19Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-11T10:55:12Z | 2026-07-11T10:57:40Z | 2m 28s |
| red | 2026-07-11T10:57:40Z | 2026-07-11T11:22:48Z | 25m 8s |
| green | 2026-07-11T11:22:48Z | 2026-07-11T11:42:17Z | 19m 29s |
| review | 2026-07-11T11:42:17Z | 2026-07-11T11:54:39Z | 12m 22s |
| red | 2026-07-11T11:54:39Z | 2026-07-11T12:04:32Z | 9m 53s |
| green | 2026-07-11T12:04:32Z | 2026-07-11T12:12:55Z | 8m 23s |
| review | 2026-07-11T12:12:55Z | 2026-07-11T12:20:19Z | 7m 24s |
| finish | 2026-07-11T12:20:19Z | - | - |

## Story Context

### Bug Summary
A confrontation-resolution sequence desync occurs when a player character's Flee beat and a lethal opponent reprisal resolve in the same round. The Flee resolves successfully after the opponent reprisal has already depleted the character to 0 HP and resolved the encounter as opponent_victory, resulting in contradictory narration ("you escaped" / "are alive" prose over a 0-HP, mortally-wounded character who has already lost).

### Mechanical OTEL Sequence (Repro: 2026-07-10, slug flickering_reach-f69d51db, turn 9)
1. `dice.throw_resolved` — Player rolls for attack: outcome=Fail, beat_id=attack
2. `dice.opponent_reprisal_hit` — Opponent counterattacks: damage=2, hp_after=0/10
3. `hp_depletion.resolved` — HP threshold breach: outcome=opponent_victory, down_side=player
4. `dice.opponent_reprisal_resolved_encounter` — Encounter resolved: outcome=opponent_victory, hp=0/10
5. `post_resolution_lethality.applied` — Lethality gate: verdict=dead, hp=0
6. `dice.throw_resolved` — Flee beat STILL resolves: outcome=CritSuccess, beat_id=flee, **resolved_encounter=True** ← double-resolution

### Settled-State Incoherence
- `encounter.resolved=True`, `outcome=opponent_victory`
- Character status: "Downed — dead (mortally wounded)", `stabilizable=false`
- BUT: `character_locations` moved by Flee ("Blind Reach — Canyon Rim")
- AND: `player_dead=False` (desync with status)

### Root Cause (Suspected)
Beat-commit pipeline lacks a **win-condition liveness gate**. Once HP hits 0 and the encounter resolves opponent_victory in the same round, subsequent player beats (e.g., Flee) should NOT resolve. The pipeline currently allows post-death beat resolution, and the narrator is prompted with BOTH lethal-depletion and escape-success results, so prose honors both contradictory outcomes.

### Acceptance Criteria

1. **Win-Condition Liveness Gate**: Once a character's HP reaches 0 and the encounter resolves with `outcome=opponent_victory` in the same round, no further player beat may resolve that round. Blocked beats must emit a watcher event (e.g., `beat.blocked_by_liveness_gate`) so the GM panel can verify the gate engages.

2. **Flee Location Commit Guard**: Flee's `character_locations` movement must NOT commit if the character died the same round (post-lethality-verdict check).

3. **player_dead Synchronization**: The `player_dead` flag must match the character's "downed/dead" status. If a character is marked "dead (mortally wounded)", `player_dead` must be `True`.

4. **Narration Coherence**: The narrator must not be prompted with contradictory beat results. Once an encounter resolves opponent_victory due to lethal HP depletion, the prompt context must exclude post-death player beats, so narration reflects the down/dead state, not escape.

5. **Regression Guard (Clean Path)**: The `player_victory` path (player wins confrontation; opponent reaches 0 HP) must remain fully coherent. No double-resolution or flag desync.

### Repro Steps
1. Start a WWN confrontation (e.g., "Wasteland Brawl") at low player HP (≤2 above opponent's per-hit damage).
2. Fail an attack roll, triggering opponent reprisal.
3. Opponent reprisal deals ≥ player remaining HP, dropping player to 0.
4. In the same round, commit a Flee beat with a high roll (e.g., CritSuccess).
5. Observe: Flee resolves despite encounter already resolved; narration contradicts HP state; `player_dead ≠ character.status`.

### Source Documentation
- **Ping-pong file:** `/Users/slabgorb/Projects/sq-playtest-pingpong.md` (line ~118: "[BUG] Flee beat and lethal opponent reprisal double-resolve the same round"; line ~85: "[DIAG] Clean player_victory path is fully coherent")
- **Screenshot:** `.sq-playtest-screenshots/010-narration-alive-but-0hp-downed.png` (shows banner + contradictory prose over 0-HP character)
- **Doctrine:** ADR-139 (Confrontation Integrity Invariants — win-condition liveness, seated-actor HP durability; currently marked *partial*)

## Sm Assessment

**Story readiness:** READY. This is a p1 confrontation-integrity bug with unusually strong documentation — a full OTEL mechanical sequence, settled-state snapshot, suspected root cause, deterministic repro, and an isolation diagnosis (clean player_victory path confirmed coherent, so the defect is loss-path-only). Context is compiled above from the playtest ping-pong file; the next agent should not need to re-derive the failure mode.

**Workflow decision:** Sprint YAML workflow field read `superpowers`, which is not a registered workflow. Resolved to `spdd` (Superpower Driven Development) — the literal name match ("superpowers skill attestation") and the workflow used by recent sibling stories 163-8 and 164-6. Phased workflow: setup → red → green → review → finish.

**Jira:** Skipped — no Jira key on the story; Jira integration not enabled for this project.

**Branch:** `feat/166-1-flee-reprisal-double-resolve` created in sidequest-server (repos: server only; no UI/content changes anticipated — the fix is in the beat-commit pipeline and narrator prompt assembly).

**Routing:** Handoff to TEA for RED phase. The five acceptance criteria above are each independently testable; AC-1 (liveness gate) and AC-5 (player_victory regression guard) are the load-bearing pair. Per project OTEL doctrine, the liveness-gate decision must emit a watcher event so the GM panel can verify the gate engages — the RED phase should include a test asserting that emission.

<skills-invoked>
<skill name="test-driven-development" phase="red" at="2026-07-11T10:58:33Z"/>
<skill name="test-driven-development" phase="green" at="2026-07-11T11:26:00Z"/>
<skill name="verification-before-completion" phase="green" at="2026-07-11T11:38:00Z"/>
<skill name="requesting-code-review" phase="green" at="2026-07-11T11:44:00Z"/>
<skill name="test-driven-development" phase="red" at="2026-07-11T11:56:00Z"/>
<skill name="test-driven-development" phase="green" at="2026-07-11T12:06:00Z"/>
<skill name="verification-before-completion" phase="green" at="2026-07-11T12:12:00Z"/>
<skill name="requesting-code-review" phase="green" at="2026-07-11T12:13:00Z"/>
</skills-invoked>

## TEA Assessment

**Tests Required:** Yes
**Reason:** p1 bug fix; TDD RED phase per spdd workflow.

**Test Files:**
- `sidequest-server/tests/integration/test_166_1_flee_reprisal_double_resolve.py` — 7 tests driving the production dispatch (`dispatch_dice_throw`), the sealed WN round walk, the lethality seam (`apply_post_resolution_lethality`), and the narration-apply seam (`_apply_narration_result_to_snapshot`) on the REAL mutant_wasteland pack (skip-guarded when sidequest-content is absent).

**Tests Written:** 7 tests covering 5 ACs — 6 RED on story assertions, 1 green regression guard (AC-5).
**Status:** RED (verified by testing-runner RUN_ID 166-1-tea-red-2: `6 failed, 1 passed`; all failures on STORY assertions, all preconditions green).

**Forensic reconstruction (load-bearing for Dev — the bug is NOT where the pingpong log suggests):**
The engine never double-applied the flee. `dice.throw_resolved` logs at dispatch TAIL (dice.py:1299), so the pingpong's events 2–6 are ONE dispatch: the sealed walk ran the opponent's slot first (reprisal kill → `opponent_victory` → lethality verdict=dead), then correctly SKIPPED the dead fleer's slot (`wn_round.py:271`, `reason=actor_downed`), and the tail log's `resolved_encounter=True` reads the post-reprisal state. The defects are at four seams:
1. **Silent slot-skip (AC-1/AC-4):** the `actor_downed` skip emits no `beat_id` on its watcher event and appends NO narrator hint (contrast the `dead_premise` branch, wn_round.py:338) — so the dispatch replay text "Flee → CritSuccess" reaches the narrator unopposed → escape prose over a corpse.
2. **Legacy-path directive collision (AC-4):** on the no-initiative path, `_emit_player_beat_resolution_close` (dice.py:2280 branch) appends "…STILL STANDING; the fight continues" AFTER the reprisal close already appended "has RESOLVED" — two contradictory MECHANICAL TRUTH directives in one prompt.
3. **`player_dead` never written (AC-3):** `GameSnapshot.player_dead` (session.py:1117) has zero production writers; `combat_player_dead_span` (telemetry/spans/combat.py) has zero callers. Wire-up-what-exists.
4. **Ungated location commit (AC-2):** `_apply_narration_result_to_snapshot` (narration_apply.py:4235) commits `result.location` with no death gate — the narrator's escape prose relocated the corpse.

### Rule Coverage

| Rule / Doctrine | Test(s) | Status |
|------|---------|--------|
| ADR-139 liveness gate observable (OTEL principle) | `test_sealed_walk_blocked_flee_emits_gate_event_with_beat_id` | failing |
| Narrator prompt coherence, sealed walk (AC-4) | `test_sealed_walk_skipped_flee_surfaces_mechanical_truth_to_narrator` | failing |
| player_dead wiring, e2e + span (AC-3, wiring test) | `test_reprisal_kill_sets_player_dead_flag_end_to_end` | failing |
| player_dead wiring, owning seam (AC-3) | `test_lethal_verdict_sets_player_dead_and_emits_span` | failing |
| No Silent Fallbacks — dead-PC location refusal (AC-2) | `test_dead_pc_location_move_does_not_commit` | failing |
| Contradictory-directive ban, legacy path (AC-4) | `test_legacy_reprisal_kill_appends_no_fight_continues_directive` | failing |
| Clean player_victory regression (AC-5) | `test_player_victory_clean_path_stays_coherent` | passing (guard) |
| lang-review #6 test quality | self-check below | done |

**Rules checked:** every test asserts specific values with diagnostic messages; no mocks except the shared-RNG monkeypatch (patched where used: `sidequest.server.dispatch.dice.random.randint`) and the watcher-recorder wrappers (forwarding, patched per consuming module). Wiring requirement satisfied: 5 of 7 tests drive production entry points end-to-end.
**Self-check:** 0 vacuous assertions found. Every FAIL-expected assert carries a message naming the production seam and the playtest evidence.

**Determinism:** one arg-dispatching `randint` fake — `(1,20)→20` (opponent to-hit always hits), all else → minimum (opponent damage floor = 1, exactly killing the 1-HP PC; PC's 2d6+50 blade guarantees the AC-5 kill). Player d20 uses thrown `face=[20]`, never rng. (102-1 heavy_metal pattern.)

**Handoff:** To Dev (Naomi Nagata) for GREEN. Suggested fix seams, in test order: wn_round.py slot-skip (event beat_id + narrator hint), dice.py `_emit_player_beat_resolution_close` (suppress the fight-continues anchor when `encounter.resolved`), post_resolution_lethality.py (set `player_dead` + fire `combat_player_dead_span` when the last player-side PC takes a lethal down — solo semantics; see Delivery Findings for the MP question), narration_apply.py location gate (refuse + loud OTEL for a dead actor).

### TEA Assessment — rework round 1 (2026-07-11)

**Input:** Reviewer REJECTED with findings R1 (HIGH), R2/R3/R4 (MEDIUM), R5 (LOW). R1/R3/R5 are TEA's; R2 needed a RED test; R4 (docstring) is Dev's.

**Tests added/changed** (`test_166_1_flee_reprisal_double_resolve.py`, now 12 tests):
- **R2 (the round's true RED — fails on story assertion):** `test_partial_down_hint_must_not_claim_fight_close_while_live` — MP partial-down (Harpo killed at the opponent's slot, Chico standing, fight LIVE per ADR-139) → the actor_downed LIVENESS GATE hint must not instruct "the fight's close". Fails today with the misdirecting hint quoted in the assert output.
- **R1a (pin, passes):** `test_targeted_commit_after_kill_lands_on_dead_premise_gate` — discovery: `seal_wn_commit` pins a premise target for every non-item-use beat, so a targeted post-kill commit lands on `wn_dead_premise` (which already carries beat_id + hint) BEFORE the resolved-encounter gate. Pinned.
- **R1b (pin, passes):** `test_resolved_slot_skip_emits_event_and_hint_for_untargeted_commit` — the shipped-untested `wn_slot_skipped_encounter_resolved` branch pinned via its reachable shape: an untargeted drink commit (`use_item:*`, target=None) blocked by prior resolution — event with beat_id + LIVENESS GATE hint + potion not consumed.
- **R3a/R3b (pins, pass):** location-gate AND-conjunction boundaries — alive+incapacitating PC MAY move (carried); 0-HP-no-status transient MAY move. The gate fires only on the durable death state.
- **R5:** narrator-truth assertion now keys on the structural "LIVENESS GATE" prefix alongside the negation markers.

**Status:** REWORK RED verified (testing-runner RUN_ID 166-1-tea-red-rework1c: `1 failed, 11 passed` — the 1 failure on the R2 story assertion, preconditions green).

**Handoff:** To Naomi (Dev) for green — R2 production fix (condition the actor_downed hint tail on `encounter.resolved`) + R4 (run_wn_round docstring bullet for the resolved-slot branch).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (suite 14,966 passed; pre-existing/flaky classifications verified; changed files lint clean; wiring verified) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 3 | confirmed 2, confirmed-at-lower-severity 1, dismissed 0 |
| 5 | reviewer-comment-analyzer | Yes | findings | 1 | confirmed 1 |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | none (18 rules, 46 instances, 0 violations; both doctrine questions traced and resolved compliant) | N/A |

**All received:** Yes (4 enabled returned: 2 with findings, 2 clean; 5 disabled via settings)
**Total findings:** 5 confirmed (4 from subagents + 1 from Reviewer's own diff read), 0 dismissed, 0 deferred

### Rule Compliance

Rubric: `.pennyfarthing/gates/lang-review/python.md` (13 checks) + CLAUDE.md server doctrine (5 rules). The rule-checker enumerated every changed block against every applicable check — 18 rules, 46 instances, 0 violations. Reviewer spot-verification of the load-bearing calls:

- **#1 silent exceptions:** only `except PackNotFound → pytest.skip(reason)` in the test file — specific type, loud skip. Compliant.
- **#4 logging:** all four new log sites use lazy `%s` formatting; the location refusal logs at `warning` (matches the file's loud-refusal convention), skips at `info` (matches sibling slot_skipped logs). Compliant.
- **#6 test quality:** all 7 tests assert specific values; monkeypatch targets patched where used; skips carry reasons. Compliant (coverage GAP is a separate finding, below — quality of what exists is sound).
- **No Silent Fallbacks:** every new refusal/skip emits log + watcher event; the dice.py anchor suppressions emit nothing at the suppression point but the `encounter.resolved` transition they defer to is always announced first by `_close_reprisal_depletion` (`op="resolved"` + RESOLVED directive) earlier in the same dispatch — traced by rule-checker, confirmed by Reviewer at dice.py:1103→1132 call order. Compliant.
- **OTEL principle:** all four new decision branches emit (2× wn_round watcher events with beat_id, 1× location-refusal event, 1× `combat.player_dead` span whose pre-registered SPAN_ROUTES entry auto-bridges to the GM panel). Compliant.
- **Don't Reinvent:** `combat_player_dead_span` is the pre-existing helper wired up, not a duplicate. Compliant.
- **Verify Wiring:** all four seams have non-test production callers (dispatch_dice_throw at dice.py:1043/1132, websocket_session_handler → `_apply_narration_result_to_snapshot`, `_close_reprisal_depletion` → `apply_post_resolution_lethality`). Compliant — with the one exception recorded as finding R1: the new `wn_slot_skipped_encounter_resolved` branch has production callers but ZERO test coverage, violating "Every Test Suite Needs a Wiring Test."
- **Tenant isolation audit:** N/A — this codebase has no tenant model; seat identity is server-authenticated upstream (`sd.player_id`, story 118-9) and none of the changed code reads client-controlled identity.

### Devil's Advocate

Assume this fix is broken. The narrator is an LLM: the LIVENESS GATE hint and the "Flee → CritSuccess" replay text now COEXIST in one prompt, and we are betting the hint wins the attention war. Nothing structurally removes the celebratory replay text on the sealed path — if the model narrates the escape anyway, the player sees the same contradiction; the hint is mitigation, not proof, and only a live playtest (or the pinned directives being consumed downstream in `render_encounter_summary`, which the pre-handoff review verified is on the prompt path) supports it. Second: the `actor_downed` hint tells the narrator to "narrate their fall **and the fight's close**" — in an MP partial-down (PC A dead, PC B alive, fight LIVE per ADR-139's one-down≠party-defeat rule) that instruction is flatly false and would coach the narrator to end a fight the engine keeps open. That is a real misdirection this diff introduces on a reachable MP path. Third: the untested `wn_slot_skipped_encounter_resolved` branch — every line of it was written this morning and no test has ever executed it; if `commit.beat_id` were somehow None-shaped or the hint format wrong, the suite would not notice. Fourth: `player_dead` never resets — a future revive/reroll path that forgets to clear it leaves a permanently-dead session; today the NEW CHARACTER flow may bypass it, but nothing pins that. Fifth: the location gate requires hp≤0 AND incapacitating — a narrator moving an unconscious-but-alive PC (carried by the party) is legitimately allowed, but nothing tests that the gate does NOT over-fire there; loosen the AND in a refactor and the suite stays green. The first concern is accepted risk (directive-based mitigation is this codebase's established narrator-truth mechanism); the second and third are findings below.

### Reviewer Observations (checklist evidence)

1. `[VERIFIED]` Data flow traced end-to-end: DICE_THROW(flee) → `dispatch_dice_throw` seal (dice.py:1033) → `run_wn_round` opponent slot → `_resolve_opponent_reprisal` → `_close_reprisal_depletion` (resolves + lethality + RESOLVED directive) → `apply_post_resolution_lethality` sets `player_dead` + `combat.player_dead` span (post_resolution_lethality.py:354-370) → player slot skipped with beat_id event + hint (wn_round.py:271-306) → hints reach the prompt via `render_encounter_summary` (encounter_render.py:44, verified on-path by pre-handoff review) → narrator result → dead-PC location gate refuses the move (narration_apply.py:4181-4213). Complies with No Silent Fallbacks + OTEL principle at every hop.
2. `[VERIFIED]` The dice.py suppression guards read `encounter.resolved` (authoritative live state), not the stale `encounter_resolved` param — dice.py:2240,2289; the reprisal deliberately does not fold into the param (pre-existing NOTE at dice.py:1114-1120). Correct signal choice.
3. `[VERIFIED]` `player_dead` flip is scoped `if incapacitations:` (lethal-only) and requires zero standing seated player-side PCs; non-lethal recovery (floor to 1 HP) can never trip it — post_resolution_lethality.py:354-358 vs the recover branch at :282. Complies with AC-3 without over-firing on `player_victory` (early return at :203).
4. `[VERIFIED]` Location gate placed AFTER drift-repair so a title-derived repaired location is gated too (narration_apply.py:4171 comment + order), and clearing `result.location` chokes every downstream consumer (all read `result.location` inside the following `if` block — rule-checker grep 4215-4900).
5. `[TEST][HIGH]` + `[MEDIUM]`/`[DOC]` findings — see severity table in the assessment.
6. Pattern observed (good): the LIVENESS GATE hint reuses the `dead_premise` narrator-hint contract (wn_round.py:343-349) rather than inventing a new channel — consistent with Don't Reinvent.

## Delivery Findings

No upstream findings at setup.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): mutant_wasteland's `flee` beat carries no `resolution: true` (✦) marker, so a SUCCEEDED Flee never ends the fight via the 153-12 WN Disengage exit and every flee eats a reprisal even on CritSuccess — the content-side half of why the playtest PC died mid-escape.
  Affects `sidequest-content/genre_packs/mutant_wasteland/rules.yaml` (add the ✦ marker or rule the omission intentional — content repo, outside this story's server scope).
  *Found by TEA during test design.*
- **Question** (non-blocking): `GameSnapshot.player_dead` multi-seat semantics are undefined — the RED tests pin the solo shape (last player-side PC lethally down → True). Whether MP means "all seats dead" or "any seat dead" needs an Architect/PM ruling before the flag drives UI beyond the death banner.
  Affects `sidequest/game/session.py` (field contract documentation).
  *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): two pre-existing test failures on the branch base — `tests/server/test_companion_brain_telemetry_passthrough.py::{test_emit_endpoint_forwards_session_slug_and_severity_to_hub,test_emit_endpoint_daemon_path_unchanged}` fail identically with the 166-1 changes stashed (spy captures `render_assets.mount_remounted` init events instead of the test payload).
  Affects `sidequest-server/tests/server/test_companion_brain_telemetry_passthrough.py` (test isolation: the watcher-hub spy needs a clean slate or event filtering — ADR-154 area).
  *Found by Dev during implementation.*
- **Improvement** (non-blocking): three MP-deferred edges of the 166-1 invariants, flagged by the pre-handoff review, should be lifted into the ADR-139 multi-seat design story so they are not rediscovered from source: (a) `player_dead` ignores party PCs alive but unseated in the killing encounter; (b) `combat.player_dead` fires one span per simultaneous multi-PC down against one flag flip; (c) the dead-PC location gate covers the acting character only — the MP cohort-follow loop could still relocate a co-located corpse when a survivor is the actor.
  Affects `sidequest/server/post_resolution_lethality.py`, `sidequest/server/narration_apply.py` (MP semantics, all solo-correct today).
  *Found by Dev during implementation.*
- **Gap** (non-blocking): 4 pre-existing repo-wide ruff errors in files untouched by this branch (`tests/dungeon/conftest.py` 3× E402, `tests/telemetry/test_tactical_telemetry_sink.py` 1× I001).
  Affects those two test files (lint hygiene; 1 auto-fixable).
  *Found by Dev during implementation.*

### Dev (implementation — rework round 1)
- **Gap** (non-blocking): a committed Flee seals with a pinned premise target, so in a multi-opponent fight where the pinned (first) opponent dies before the fleer's slot, the flee lands on dead-premise and `withdrawn` is never set — the PC who intended to disengage stays seated in melee. Pre-existing behavior (unchanged by 166-1), surfaced by the R1a pin.
  Affects `sidequest/server/dispatch/wn_round.py` (dead-premise vs nonoffensive-disengage interplay — decide whether a dead-premise flee should still withdraw; MP/multi-opponent design call).
  *Found by Dev during implementation.*

### Reviewer (code review)
- **Question** (non-blocking): `player_dead` has no reset writer — a future revive / NEW-CHARACTER / new-session-from-save path must clear it or a session stays permanently dead; nothing pins the reroll flow against the flag today.
  Affects `sidequest/game/session.py` + the reroll/CHARACTER_INCAPACITATED flow (define the reset contract when the flag grows consumers).
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the sealed-path replay text still celebrates the unapplied beat ("Flee → CritSuccess") and coherence rests on the LIVENESS GATE hint outweighing it in the prompt — worth a targeted /sq-playtest re-run of the original repro (low-HP flee into lethal reprisal, mutant_wasteland/flickering_reach) to verify the prose lands right before the pingpong entry is marked fixed.
  Affects playtest verification workflow (pingpong entry "[BUG] Flee beat and lethal opponent reprisal double-resolve" stays `fixed`, not `verified`, until then).
  *Found by Reviewer during code review.*

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/server/dispatch/wn_round.py` — the `actor_downed` and player-slot `encounter_resolved` skips now carry the blocked commit's `beat_id` on their watcher events (the latter previously emitted no event at all) and append a LIVENESS GATE narrator hint mirroring the dead_premise contract (AC-1, AC-4 sealed path).
- `sidequest/server/dispatch/dice.py` — the two fight-continues anchors in `_emit_player_beat_resolution_close` are gated on `not encounter.resolved`, so a same-dispatch reprisal resolution can no longer share a prompt with a "STILL STANDING" claim (AC-4 legacy path).
- `sidequest/server/post_resolution_lethality.py` — a lethal down leaving no seated player-side PC standing sets `GameSnapshot.player_dead` and fires `combat_player_dead_span` per incapacitation (both previously had zero production writers/callers) (AC-3).
- `sidequest/server/narration_apply.py` — dead-PC location gate: a narrator-emitted location change for a 0-HP PC with an incapacitating status is refused loudly (warning log + `location_move_refused_actor_dead` watcher event) by clearing `result.location` ahead of the commit block, placed after drift-repair so repaired locations are gated too (AC-2).

**Tests:** 7/7 story tests passing (GREEN; testing-runner RUN_ID 166-1-dev-green, re-verified post-commit as 166-1-dev-green-final and again after the docs amend). Full suite: 14,965 passed, 341 skipped; 4 failures triaged — 2 pre-existing (fail with changes stashed; logged as Delivery Finding), 2 parallel-run interference (pass serially, testing-runner RUN_ID 166-1-dev-green-serial-recheck).
**Lint:** changed files clean (`ruff check` + format); 4 pre-existing repo-wide errors in untouched files (logged as Delivery Finding).
**Branch:** `feat/166-1-flee-reprisal-double-resolve` (pushed, HEAD dbaed454).
**Pre-handoff review (superpowers:requesting-code-review):** independent reviewer verdict "Ready to merge" — zero Critical, zero Important, four Minor (all deferred-MP territory; the one actionable — an underselling scope comment on the `player_dead` check — was fixed in dbaed454, the rest captured as Delivery Findings).
**Process note:** formal RED/GREEN/full-suite verifications ran through testing-runner; two diagnostic micro-runs (the stash-bisect proving the telemetry failures pre-exist, and the post-amend doc-only re-verification) ran pytest directly for stash-coordination reasons.

**Handoff:** To Chrisjen Avasarala (Reviewer) for the review phase.

### Dev Assessment — rework round 1 (2026-07-11)

**Implementation Complete:** Yes — all five review findings addressed.
**Files Changed (production, commit 41a42cf6):**
- `sidequest/server/dispatch/wn_round.py` — (R2) the actor_downed LIVENESS GATE hint tail now reads the authoritative `encounter.resolved` at hint-build time: "the fight's close" only when resolved, "the fight continues around them" in a live partial-down; (R4) `run_wn_round` docstring gains bullets for both blocked-slot gates, including the dead-premise-shadow reachability note.
(R1/R3/R5 were TEA's test-side deliveries this round; no other production change.)

**Tests:** 12/12 story tests passing + 19 neighboring walk/reprisal tests clean (testing-runner RUN_ID 166-1-dev-green-rework1, HEAD 41a42cf6). The R2 test was verified genuinely RED at base dbaed454 by the rework reviewer.
**Lint:** clean (ruff check + format on the changed file).
**Branch:** pushed (HEAD 41a42cf6).
**Pre-handoff review (superpowers:requesting-code-review, rework diff dbaed454..41a42cf6):** verdict "Ready to merge" — zero Critical/Important; two Minor out-of-scope observations, one logged as a Delivery Finding below.

**Handoff:** To Chrisjen (Reviewer) for re-review.

## Reviewer Assessment

**Verdict:** APPROVED (re-review 2026-07-11 after rework round 1 — see the re-review addendum below; the round-0 verdict was REJECTED on one HIGH test gap, since closed)

### Round 0 verdict (2026-07-11, superseded): REJECTED (one HIGH test gap; small, well-scoped rework — the production design itself is sound)

| Severity | Tag | Issue | Location | Fix Required |
|----------|-----|-------|----------|--------------|
| [HIGH] | [TEST] | New production branch shipped with ZERO test coverage: the `wn_slot_skipped_encounter_resolved` liveness-gate branch (watcher event + LIVENESS GATE hint for a LIVE player whose slot arrives after resolution) is never executed by any test — empirically verified by instrumenting the watcher path across the whole suite (only `wn_slot_skipped_downed` fires, ×3). Violates CLAUDE.md "Every Test Suite Needs a Wiring Test" (critical, non-dismissable) and the spdd TDD contract (production code without a failing test first). | `sidequest/server/dispatch/wn_round.py:382-410` | Add a RED-first test: two seated player-side PCs, PC-A's earlier slot resolves the fight while PC-B (alive, hp>0) holds a sealed commit → assert `wn_slot_skipped_encounter_resolved` fires with PC-B's beat_id and the narrator hint carries the did-not-resolve truth. |
| [MEDIUM] | [EDGE]* | The `actor_downed` LIVENESS GATE hint instructs "narrate their fall **and the fight's close**" unconditionally — in an MP partial-down (downed PC's slot skipped while the fight stays LIVE for a surviving PC, ADR-139's own one-down≠party-defeat rule) this coaches the narrator to close a fight the engine keeps open. (*Reviewer's own diff read; edge-hunter disabled.) | `sidequest/server/dispatch/wn_round.py:298-306` | Condition the tail on `encounter.resolved` (e.g. "...narrate their fall" + append "and the fight's close" only when resolved), or split the hint. |
| [MEDIUM] | [TEST] | The dead-PC location gate's AND-conjunction (hp≤0 AND incapacitating) has no boundary pins: gate must NOT over-fire on an alive-but-incapacitated PC (a carried unconscious PC is a legitimate narrator move), and the hp-0-no-status half is unpinned. A refactor loosening AND→OR stays green today. | `sidequest/server/narration_apply.py:4184-4188` / test file | Add two boundary tests: hp>0 + incapacitating status → move ALLOWED; hp=0 + no status → pin the intended contract. |
| [MEDIUM] | [DOC] | `run_wn_round`'s docstring enumerates the per-slot skip branches but omits the newly narrator-visible resolved-slot branch — the docstring contract now under-describes the walk. | `sidequest/server/dispatch/wn_round.py:~221-231` | Add the fourth bullet (resolved-before-slot → event + hint, no mechanical resolution). |
| [LOW] | [TEST] | `_NOT_RESOLVE_MARKERS` couples the narrator-truth test to negation phrasing; a legitimate rewording false-fails. The hint already carries a stable `LIVENESS GATE (ADR-139):` prefix. | `tests/integration/test_166_1_flee_reprisal_double_resolve.py:73` | Optionally assert the stable prefix alongside (or instead of) the marker set, or document the markers as the frozen vocabulary contract. |

**Subagent coverage tags:** [TEST] test-analyzer (2 confirmed high/medium + 1 low above); [DOC] comment-analyzer (1 confirmed); [RULE] rule-checker — clean, 18 rules / 46 instances / 0 violations (notably: the dice.py anchor suppressions are NOT a silent fallback — the deferred-to `encounter.resolved` transition is always announced earlier by `_close_reprisal_depletion`; and `combat_player_dead_span` is a genuine wire-up of an existing helper); [EDGE] edge-hunter disabled — Reviewer's own edge finding recorded above; [SILENT] silent-failure-hunter disabled — covered by rule-checker's No-Silent-Fallbacks pass (5 instances, 0 violations); [TYPE] type-design disabled — no new signatures/types in the diff (rule-checker #3: 0 instances); [SEC] security disabled — no new external-input boundary (rule-checker #11: 0 instances; no tenant model, seat identity server-authenticated upstream); [SIMPLE] simplifier disabled — diff is 4 inline blocks + guards, no new abstractions to simplify.

**Data flow traced:** DICE_THROW(flee) → seal → walk (reprisal kill → lethality → player_dead + span → slot skip w/ beat_id + hint) → prompt via render_encounter_summary → narrator result → dead-PC location refusal. Safe because every hop emits (log + watcher/span) and the refusal chokes all downstream consumers of `result.location`.
**Pattern observed:** LIVENESS GATE hint reuses the dead_premise narrator-hint contract at wn_round.py:343-349 (good — Don't Reinvent).
**Error handling:** refusals are loud (warning log + severity=warning event at narration_apply.py:4189-4211); no new exception paths; idempotency preserved (`_already_handled` gate keeps the player_dead block from double-firing).
**What was verified good:** all 5 ACs have passing tests on the paths they cover; suite 14,966 passed with pre-existing/flaky failures independently confirmed; changed files lint clean; all four seams have production callers.

**Handoff:** Back through the rework loop — findings are testable, so RED first: Amos (TEA) writes the missing branch test + boundary pins (R1, R3, R5), then Naomi (Dev) applies the hint-tail fix and docstring bullet (R2, R4) and makes it all green.

### Re-review addendum (rework round 1, HEAD 41a42cf6) — APPROVED

Finding-by-finding closure, verified against the rework diffs (`2587f12e..e339ba6b` tests, `41a42cf6` production) read directly by the Reviewer:

| Finding | Status | Evidence |
|---------|--------|----------|
| R1 [HIGH] untested branch | **CLOSED — exceeded** | Two pins instead of one: `test_resolved_slot_skip_emits_event_and_hint_for_untargeted_commit` empirically executes the branch (asserts exactly one `wn_slot_skipped_encounter_resolved` event with the blocked beat_id — the test fails if the branch never fires), and `test_targeted_commit_after_kill_lands_on_dead_premise_gate` pins the newly-discovered shadow: `seal_wn_commit` pins a premise target for every non-item-use beat, so a targeted post-kill commit lands on `wn_dead_premise` first. TEA's deviation correctly shows the Reviewer's suggested flee fixture could not reach the branch — the item-use shape is the right one. |
| R2 [MEDIUM] hint claims fight close | **CLOSED** | Production conditional `_aftermath` reads the authoritative `encounter.resolved` at hint-build time (wn_round.py:303-322); at a downed slot, resolution can only have settled at an earlier slot, so the read is never stale. The pinning test was verified genuinely RED at base dbaed454 (rework reviewer, independent). |
| R3 [MEDIUM] location-gate boundaries | **CLOSED** | Both AND-conjunct falsifiers pinned: alive+incapacitating → move allowed (carried PC); 0-HP-no-status transient → move allowed. |
| R4 [MEDIUM] walk docstring | **CLOSED** | `run_wn_round` docstring now enumerates all four slot outcomes including both blocked-slot gates and the dead-premise-shadow reachability note. |
| R5 [LOW] marker coupling | **CLOSED** | Narrator-truth assertion re-keyed on the structural "LIVENESS GATE" prefix alongside the negation markers. |

**Re-review verification:** story file 12/12 (`166-1-dev-green-rework1`); full suite at HEAD 41a42cf6 (`166-1-reviewer-rework-gate`): 14,971 passed, 3 failed — all pre-existing (2× companion_brain telemetry, 1× bestiary parallel-flake serially confirmed passing). No new regressions. Round-0 subagent fan-out stands for the base diff; the rework delta was reviewed directly by the Reviewer plus Dev's independent pre-handoff reviewer ("Ready to merge", which verified R2's RED-at-base and R1b's seal/ordering premises against source).

**Data flow traced:** unchanged from round 0 (the rework alters one hint string + docstring + tests).
**Pattern observed:** the two-pin partition of the blocked-slot space (dead-premise vs resolved-skip, keyed on pinned-target survival) at wn_round.py:373/399 — now documented in the docstring.
**Error handling:** unchanged; the conditional hint has no failure path (both branches produce a complete sentence).

**Handoff:** To Drummer (SM) for finish-story — PR creation + merge is SM's (Reviewer does not merge).

## Design Deviations

No deviations logged at setup.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **AC-1 tested as observability contract, not a new mechanical gate**
  - Spec source: .session/166-1-session.md, AC-1
  - Spec text: "no further player beat may resolve that round … blocked beats must emit a watcher event"
  - Implementation: Static trace showed the mechanical gate already exists and held during the playtest (sealed walk skips downed slots, wn_round.py:271; dispatch entry rejects post-resolution throws, dice.py:493) — the flee never mechanically applied. Tests therefore pin the missing OBSERVABLE half: the skip event must carry `beat_id`, and the skip must surface to the narrator.
  - Rationale: Re-asserting a gate that already passes would be a vacuous RED; the playtest failure was the gate's silence, not its absence.
  - Severity: minor
  - Forward impact: Dev should not build a second resolution gate — wire observability + narrator truth onto the existing skips.
- **AC-2 widened from "died the same round" to "any mechanically dead PC"**
  - Spec source: .session/166-1-session.md, AC-2
  - Spec text: "Flee's location move must NOT commit if the character died the same round"
  - Implementation: `test_dead_pc_location_move_does_not_commit` gates on the durable death state (0 HP + incapacitating Downed status) rather than same-round timing.
  - Rationale: The location commit happens in the narration-apply seam, which has no round-scoped view; the durable-state gate is a strict superset of the AC and is the only enforceable contract at that seam.
  - Severity: minor
  - Forward impact: none — same-round deaths are covered by the superset.

### TEA (test design — rework round 1)
- **Reviewer R1 pin delivered via the item-use shape, not the suggested flee fixture**
  - Spec source: Reviewer Assessment, finding R1
  - Spec text: "two seated player-side PCs ... PC-B still alive with a live sealed commit → assert wn_slot_skipped_encounter_resolved fires with PC-B's beat_id"
  - Implementation: Two pins — the suggested flee fixture actually lands on `wn_dead_premise` (seal pins a premise target for every non-item-use beat and the dead-premise check precedes the resolved gate), so R1a pins that shadow and R1b pins the resolved-skip branch via an untargeted drink commit.
  - Rationale: The reviewer's literal fixture cannot reach the branch; the two-pin split covers both partitions of the blocked-slot space and documents the shadow.
  - Severity: minor
  - Forward impact: none — future ✦ nobody-died resolutions are the other reachable shape and remain covered by R1b's branch pin.

### Dev (implementation)
- **AC-1 implemented as observability on existing gates, not a new resolution gate**
  - Spec source: .session/166-1-session.md, AC-1
  - Spec text: "no further player beat may resolve that round … blocked beats must emit a watcher event (e.g., `beat.blocked_by_liveness_gate`)"
  - Implementation: No new gate built — the walk's existing `actor_downed` / `encounter_resolved` skips gained `beat_id` on their events (ops `wn_slot_skipped_downed` / `wn_slot_skipped_encounter_resolved`, not the AC's example name) plus narrator hints.
  - Rationale: Follows TEA's forensic finding (the mechanical gate already existed and held) and TEA's logged deviation; the AC's event name was illustrative ("e.g.") and the tests accept any skip/block/liveness op carrying the beat_id.
  - Severity: minor
  - Forward impact: none — GM-panel consumers should key on the two skip ops.
- **AC-4 solved by suppressing the contradictory anchor, not rewriting the replay text**
  - Spec source: .session/166-1-session.md, AC-4
  - Spec text: "the prompt context must exclude post-death player beats"
  - Implementation: The dispatch replay text still carries the committed beat + tier on the legacy path (where the beat genuinely applied before the reprisal); coherence comes from suppressing the fight-continues anchors once `encounter.resolved` is True, leaving the reprisal close's RESOLVED + lethality directives unopposed, and (sealed path) from the LIVENESS GATE hint stating the beat never resolved.
  - Rationale: On the legacy path the beat DID mechanically apply pre-reprisal — excluding it from the prompt would misreport the round; removing the contradiction while the death directives dominate satisfies the AC's intent ("narration reflects the down/dead state") and is what the tests pin.
  - Severity: minor
  - Forward impact: none.

### Reviewer (audit)
- **TEA: "AC-1 tested as observability contract, not a new mechanical gate"** → ✓ ACCEPTED by Reviewer: the forensic trace is correct (the mechanical gates pre-exist at wn_round.py:271/364 and dice.py:493); re-asserting them would be vacuous RED. Sound.
- **TEA: "AC-2 widened from 'died the same round' to 'any mechanically dead PC'"** → ✓ ACCEPTED by Reviewer: the narration-apply seam has no round-scoped view; the durable-state superset is the only enforceable contract there.
- **Dev: "AC-1 implemented as observability on existing gates, not a new resolution gate"** → ✓ ACCEPTED by Reviewer: consistent with TEA's deviation; the AC's event name was illustrative. HOWEVER the second half of this implementation (the `wn_slot_skipped_encounter_resolved` branch) shipped without any test — that gap is finding R1, not a flaw in the deviation's reasoning.
- **Dev: "AC-4 solved by suppressing the contradictory anchor, not rewriting the replay text"** → ✓ ACCEPTED by Reviewer: on the legacy path the beat genuinely applied pre-reprisal; excluding it would misreport the round. The directive + hint mechanism is this codebase's established narrator-truth channel. Accepted with the Devil's-Advocate caveat that hint-vs-replay-text is mitigation, not proof — playtest verification remains the real gate.
- **TEA (rework r1): "Reviewer R1 pin delivered via the item-use shape, not the suggested flee fixture"** → ✓ ACCEPTED by Reviewer: the deviation is correct and the Reviewer's suggested fixture was wrong — a targeted flee lands on the dead-premise gate before the resolved gate (seal pins a premise target for every non-item-use beat). The two-pin partition is better coverage than what was asked for.