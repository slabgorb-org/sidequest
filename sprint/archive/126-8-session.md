---
story_id: "126-8"
jira_key: ""
epic: "126"
workflow: "tdd"
---
# Story 126-8: [FATE] Player defense 4dF is determinative (physics-is-the-roll) — the DEFEND barrier (ADR-148/149)

## Story Details
- **ID:** 126-8
- **Jira Key:** (none — Jira not configured)
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 5
- **Priority:** p3
- **Repos:** server, ui

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-19T00:04:44Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-18T19:00:39Z | 2026-06-18T19:05:20Z | 4m 41s |
| red | 2026-06-18T19:05:20Z | 2026-06-18T19:29:28Z | 24m 8s |
| green | 2026-06-18T19:29:28Z | 2026-06-18T23:26:14Z | 3h 56m |
| review | 2026-06-18T23:26:14Z | 2026-06-18T23:46:27Z | 20m 13s |
| green | 2026-06-18T23:46:27Z | 2026-06-18T23:55:48Z | 9m 21s |
| review | 2026-06-18T23:55:48Z | 2026-06-19T00:04:44Z | 8m 56s |
| finish | 2026-06-19T00:04:44Z | - | - |

## Story Context

**The DEFEND half of ADR-148, deliberately deferred from 126-7.** Story 126-7 made the player's PROACTIVE Fate 4dF determinative (FATE_THROW: settled tray faces ARE the roll, server resolves from reported faces). 126-8 brings the player's DEFENSE roll into the same physics-is-the-roll model: today `_roll_defense` / `_seat_opponent_commits` in `sidequest/server/dispatch/fate_conflict.py` still roll the defending player's 4dF SERVER-SIDE with the tray as decoration. When a SEATED Fate PC defends against an attack, the player should physically throw the 4dF and the settled faces resolve the defense (no roll_4df on the player defense path). NPC/opponent rolls stay server-side.

**Per ADR-148 line 146 this is "Story 126-8 / ADR-149"** — the no-roll_4df-on-the-player-path invariant extends from proactive to defense. SOUL: bind the ruleset (Fate ladder math unchanged).

### Acceptance Criteria

1. **Design & Spec:** the complete sealed-commit interaction model is documented in `docs/superpowers/specs/2026-06-18-fate-sealed-commit-interaction-model-design.md` (APPROVED, design complete) + `docs/superpowers/plans/2026-06-18-fate-sealed-commit-defend-server.md` (implementation plan, server-side only; UI surfaces in §8 are a separate follow-up story).

2. **COMMIT barrier (unchanged):** Each seated PC proactively throws 4dF (physics-is-the-roll), locally adjusts (invoke/reroll), submits the FINAL result. Sealed barrier waits for all PCs to submit.

3. **REVEAL → DEFEND barrier (new):** When the barrier closes, the server seats + locks the NPC attacks (their 4dF rolled NOW at REVEAL and never re-rolled across the suspend). If any PC is targeted by an attack, write `pending_defenses` ledger (one entry per incoming attack on a PC), emit one `FATE_DEFEND_REQUEST` per entry, **persist the checkpoint, and park** (no narration). If no PC targeted, resolve immediately (today's path).

4. **Defense recording (new):** Each `FATE_THROW(action="defend")` resolves the defender's 4dF from the REPORTED FACES (deterministic, via `resolve_action_from_faces` — **no `roll_4df` on the player defense path**), records `defense_total` on the matching pending_defenses entry by `request_id`, emits `role="defense"` OTEL span. A concession marks the entry conceded and fills the ledger.

5. **RESOLVE → NARRATE (unchanged for Fate logic, new for parked resume):** When the ledger fills, the server resumes: walk the existing exchange (but `_resolve_attack` reads the *recorded* PC defense instead of rolling one), resolve every mechanic (shifts, stress/consequences, created aspects, taken-out), and invoke the narrator **once** to render the whole woven exchange as a single cinematic beat. NPC defenses stay server-rolled (`roll_4df`). Fate ladder math is untouched — bind the ruleset, don't balance it.

6. **Protocol:** 
   - New `FATE_DEFEND_REQUEST` message (server→client): carries `request_id`, `defender`, `attacker`, `attack_skill`, `attack_total`, `mental`.
   - Extended `FATE_THROW`: `action` widened to include `"defend"` (alongside `"overcome"`, `"create_advantage"`, `"attack"`); a defend throw echoes the `request_id` of the request it answers.

7. **Resume-safety (ADR-128):** every phase transition is a persisted checkpoint. The `pending_defenses` ledger rides `snapshot.encounter` and survives a server restart; NPC dice rolled at REVEAL are locked and never re-rolled on resume. No server-side auto-roll for an absent defender; block-and-wait per SOUL doctrine.

8. **OTEL (lie detector):**
   - `fate.action_resolved` gains `role ∈ {action, defense}` (keeping `source ∈ {player_thrown, server_rolled}`). GM panel confirms a player defense came from the client and an NPC defense came from the server RNG.
   - New `fate.defend_phase` span: who was requested to defend, who responded, conceded flag — confirms the DEFEND barrier fired and was not improvised.

9. **Wiring (mandatory, end-to-end):** NPC-attacks-PC → `FATE_DEFEND_REQUEST` → player defend `FATE_THROW` → resolve → narrate, all through the real handler/registry/exchange on a fixture snapshot (not a unit stub); confirm the NPC path still server-rolls. No source-text wiring tests; span capture over grepping production code.

### Technical Approach (from approved spec + server plan)

**Architecture:** Today `dispatch_fate_action` resolves COMMIT→RESOLVE synchronously. This story splits that into a **resume-safe phase machine**:
1. COMMIT closes → **REVEAL** (seat NPC attacks, roll + lock their 4dF) 
2. → if any PC targeted, write `pending_defenses` ledger, emit `FATE_DEFEND_REQUEST`, **persist and park** 
3. → each `FATE_THROW(action="defend")` records the defense by `request_id`
4. → when ledger fills, **RESUME**: walk the exchange (reading recorded PC defenses), then narrate once

**Key decisions:**
- Contested asymmetry: attacker commits first (blind), defender reacts second (fully informed with incoming attack total).
- Narrator cadence: exactly one narration call per round at RESOLVE (floor); drama spikes may earn one extra beat (deferred).
- Local adjust loop: client-owned for every player roll (proactive and defense) — reroll means client throws again, server validates spend on submit.
- Bind the ruleset, don't balance it: no changes to `classify_outcome`, shifts, tiers, or ladder math.

**Implementation slicing (from server plan):**
- Task 1: Protocol — `FATE_DEFEND_REQUEST` message + `action="defend"` on `FATE_THROW`.
- Task 2: `pending_defenses` ledger model on the encounter (resume-safe).
- Task 3: OTEL — `role` on `fate.action_resolved` + new `fate.defend_phase` span.
- Task 4: REVEAL + park decision — when barrier closes, seat NPC attacks, write pending_defenses, return defend requests or resolve.
- Task 5: Emit `FATE_DEFEND_REQUEST` from the throw handler when round parks; persist parked checkpoint.
- Task 6: Defense recording — `FATE_THROW(action="defend")` resolves from faces, records on ledger by `request_id`.
- Task 7: Resume and walk — when ledger full, resume the exchange, resolve with recorded PC defenses, emit OTEL, narrate once.
- Task 8 (end-to-end wiring test): NPC-attacks-PC → park → defend → resume → narrate, through real handler/registry.

**Server files to touch:**
- `sidequest/protocol/enums.py`, `fate.py`, `messages.py` (protocol)
- `sidequest/game/encounter.py` (pending_defenses ledger)
- `sidequest/telemetry/spans/fate.py`, `sidequest/game/ruleset/fate.py` (OTEL)
- `sidequest/server/dispatch/fate_conflict.py` (REVEAL + park + defense recording + resume)
- `sidequest/handlers/fate_throw.py` (route defend action, emit defend request, persist)

**Testing strategy:** Mirrors 2026-06-17 design § 10. Every test asserts determinism (player defense via `resolve_action_from_faces`, no `roll_4df` on player path), wire validation (payload schemas), conditional DEFEND (only if PC targeted), resume-safety (exchange survives checkpoint), OTEL firing, and end-to-end wiring through real handlers.

## Sm Assessment

**Routing decision: hand off to TEA (Amos Burton) for the RED phase.**

- **Scope is clean and inherited.** 126-8 is the DEFEND half of ADR-148, deliberately carved off from 126-7. The proactive side (126-7) is **done**, so the precedent (`FATE_THROW` faces-are-the-roll, `resolve_action_from_faces`, no `roll_4df` on the player path) already exists in the codebase for TEA/Dev to mirror. No `depends_on` was set, but the prerequisite is satisfied in fact.
- **Design is already approved and committed** (commit `1f09b1be`): the interaction-model spec and the task-by-task server plan (8 tasks, ~570 LOC prod / ~500 LOC test). TEA does not need a design phase — the technical approach and the 9 ACs are written into the context above. The plan is the source of test slicing.
- **Load-bearing invariants for RED** (the lie-detector ACs): (1) player defense resolves from reported faces, **never** `roll_4df` on the player defense path; (2) NPC/opponent defenses **stay** server-rolled; (3) DEFEND barrier is conditional — only parks when a PC is actually targeted; (4) resume-safe — `pending_defenses` rides `snapshot.encounter`, NPC dice locked at REVEAL never re-roll; (5) OTEL `role ∈ {action, defense}` + `fate.defend_phase` span must fire. AC-9 demands an **end-to-end wiring test through the real handler/registry/exchange**, not unit stubs — flagging this now so it isn't deferred.
- **SOUL guardrail:** "Bind the ruleset, don't balance it." Zero changes to `classify_outcome`, shifts, tiers, or ladder math. If implementation drifts toward retuning Fate math, that's out of scope — kick it back.
- **Repos:** server + ui; branches `feat/126-8-fate-defend-barrier` created on both from `develop`. Server plan is server-only; the UI defense-throw tray (§8) is explicitly a separate follow-up, not this story.
- **Jira:** not configured for this project — claim/transition steps skipped intentionally, not a break.

No blockers. Next phase: **red** / next agent: **tea**.

## TEA Assessment

**Tests Required:** Yes
**Tests Written:** 28 tests across 8 files + 2 reusable fixtures, covering all 12 AC clusters + the load-bearing project rules.
**Status:** RED (verified by testing-runner) — failing for the right reason (missing production), with 2 intentional green safety-nets.

**Test Files:**
- `tests/protocol/test_fate_defend_protocol.py` — FATE_DEFEND_REQUEST payload/message in the GameMessage union + `action="defend"` on FATE_THROW; boundary validation (4 faces, dF range, `extra="forbid"`). (6)
- `tests/game/test_fate_pending_defenses.py` — `FatePendingDefense` model + `pending_defenses` field; snapshot round-trip + legacy-load (resume-safety). (4)
- `tests/game/ruleset/test_fate_defend_spans.py` — `role` on `fate.action_resolved` + `fate.defend_phase` span/route (run `-n0`). (5)
- `tests/server/dispatch/test_fate_reveal_park.py` — PC-targeted round parks (writes ledger, returns requests, no walk); no-PC-targeted resolves immediately. (2)
- `tests/server/dispatch/test_fate_defense_record.py` — `dispatch_fate_defense` records from faces (never roll_4df), ledger_full, concede; loud on unknown/already-filled request_id. (4)
- `tests/server/dispatch/test_fate_resume_resolve.py` — characterization (current NPC server-rolls, **green**) + recorded-PC-defense-used-not-rolled + ledger cleared + real mechanical effect. (2)
- `tests/handlers/test_fate_throw_emits_defend_request.py` — real handler broadcasts FATE_DEFEND_REQUEST on park, no narration. (1)
- `tests/server/test_fate_defend_barrier_wiring.py` — **mandatory end-to-end net**: registry tripwire (**green**) + full NPC→park→defend→resume→narrate-once + AFK-holds-barrier + parked-reload-locks-NPC-dice. (4)
- Fixtures: `tests/_helpers/fate_fixtures.py` (`conflict_with_pc_and_npc`, `parked_conflict`, `parked_conflict_filled`), `tests/_helpers/fate_session.py` (`playing_session_with_fate_conflict`, `_make_defend_throw`, counting `FakeOrchestrator`).

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| No Silent Fallbacks (#1) — loud on bad request_id | `test_unknown_request_id_fails_loud`, `test_already_filled_request_id_fails_loud` | failing (RED) |
| No Silent Fallbacks — block-and-wait AFK, no auto-roll | `test_absent_defender_holds_the_barrier` | failing (RED) |
| Input validation at boundary (#11) | `test_defend_request_payload_forbids_extra_fields`, `test_fate_throw_defend_still_enforces_four_faces`, `test_fate_throw_defend_rejects_out_of_range_face` | failing (RED) |
| OTEL on every subsystem decision (project) | `test_action_resolved_defaults_role_action`, `test_action_resolved_role_defense`, `test_defend_phase_route_registered`, `test_defend_phase_emitter_fires_named_span`, `test_defend_phase_request_time_unanswered` | failing (RED) |
| ADR-148 determinism — player defense NEVER roll_4df | `test_defense_records_from_faces_and_never_rolls`, `test_recorded_pc_defense_used_instead_of_roll`, wiring source-split | failing (RED) |
| Resume-safety (ADR-128) — ledger survives, NPC dice locked | `test_pending_defenses_survive_model_round_trip`, `test_legacy_encounter_without_ledger_loads_empty`, `test_parked_exchange_survives_reload_without_rerolling_npc` | failing (RED) |
| Every suite needs a wiring test (project) | `test_full_defend_round_through_real_handlers` (RED) + `test_fate_throw_is_registered_to_its_handler` (green) | mixed |
| Bind the ruleset, don't balance it (SOUL) | `test_recorded_pc_defense_used_instead_of_roll` (Fate shift math = `attack_total - defense_total`, unchanged) | failing (RED) |
| Test quality (#6) — meaningful assertions | all (counts via `== N`, never truthy-list; specific value checks) | self-checked |

**Rules checked:** 4 of the 13 lang-review checks are directly testable as new behavior for this feature (#1 loud failure, #6 test quality, #11 input validation) + the project OTEL/determinism/resume/wiring principles. The remaining checks (#2 mutable defaults, #3/#4 annotations/logging, #5 paths, #7 resource leaks, #8 deserialization, #9 async, #10 imports, #12 deps, #13 fix-regressions) are Dev-side self-review concerns Dev applies during GREEN, not new-AC test surface.
**Self-check:** 0 vacuous tests — every assertion checks a specific value; the 2 always-green tests are a documented characterization safety-net + the registry reflection net, not accidental passes.

**RED-state verification (testing-runner):** the 2 safety-nets PASS; every other failure traces to a missing not-yet-added symbol/attribute (`FateDefendRequestPayload`/`Message`, `FatePendingDefense`/`pending_defenses`, `fate_defend_phase_span`/`role`, `FateDispatchResult.awaiting_defense`, `dispatch_fate_defense`, `resume_fate_exchange`) — zero fixture-construction errors.

**Handoff:** To Dev (Naomi Nagata) for GREEN — implement the 8-task server plan to turn these RED. Resolve the narration-cadence Question before wiring `_finish_defense` (Task 7).

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (production):**
- `sidequest/protocol/{enums,fate,messages}.py` — `FATE_DEFEND_REQUEST` enum/payload/message + `action="defend"` on `FateThrowPayload` (Task 1).
- `sidequest/game/encounter.py` — `FatePendingDefense` model + `StructuredEncounter.pending_defenses` ledger (Task 2).
- `sidequest/telemetry/spans/fate.py`, `sidequest/game/ruleset/fate.py` — `role` attr on `fate.action_resolved` + `fate.defend_phase` span/route (Task 3).
- `sidequest/server/dispatch/fate_conflict.py` — REVEAL+park decision, `_build_pending_defenses`, `dispatch_fate_defense`, `resume_fate_exchange` (Tasks 4/6/7); **this session** added an additive optional `rng` param on `resume_fate_exchange` (testability — production default unchanged).
- `sidequest/handlers/fate_throw.py` — defend-action routing, `FATE_DEFEND_REQUEST` broadcast + checkpoint on park, `_finish_defense` delegating narration to the session (Task 5/7).
- `sidequest/server/websocket_session_handler.py` — **this session** added `_narrate_resolved_fate_exchange(sd, action)`: the dice-replay narration seam (`_build_turn_context` + `_execute_narration_turn(suppress_intent_router=True)`).

**Files Changed (tests):**
- `tests/_helpers/fate_session.py` — minimal SimpleNamespace harness + faked `_narrate_resolved_fate_exchange` (Option A; reverted the heavy `_build_turn_context` scaffolding).
- `tests/_helpers/fate_fixtures.py` — `resolve_parked_defenses` two-phase driver + `_faces_for_sum`.
- 10 pre-126-8 Fate tests migrated to the two-phase DEFEND-barrier contract (see Design Deviations).
- `tests/protocol/test_enums.py` — 58→59.

**Tests:** Story 126-8 suite + all Fate regression GREEN — `pytest -k fate` → **588 passed, 1 skipped**. Span file (`-n0`) → 5 passed. The one previously-failing wiring test (`test_full_defend_round_through_real_handlers`) now passes. The flakiness-prone migrated test (`test_handler_drives_dispatch_end_to_end`, internal `random.Random()`) ran 25/25 green.

**Pre-existing branch failures (NOT 126-8):** the full suite shows 88 failures (WN combat beat-pool empty, Fate SRD reference content not provisioned into test temp fixtures, one stale `build_async_anthropic` narrator-backend test). **Verified pre-existing** by stashing ALL uncommitted work and reproducing them identically on the clean branch HEAD — content-provisioning/environment failures on `develop`, not introduced by this story. See Delivery Findings.

**Branch:** `feat/126-8-fate-defend-barrier` (pushed)

**Handoff:** To verify phase (TEA / Amos Burton).

### Dev Assessment (rework — review round 1)

Addressed the Reviewer's REJECTED verdict:
- **FIXED (blocking) — Reviewer HIGH #1 (missing defender authorization):** `dispatch_fate_defense` now rejects a defend throw whose `actor_name != entry.defender` (`fate_conflict.py`), with a RED test (`test_defend_throw_from_non_defender_is_rejected`).
- **FIXED — Reviewer MEDIUM #2 (NPC defense role mis-tag, AC-8):** added a `role` param to the server `resolve_action`; `_roll_defense` passes `role="defense"`. Two new span tests.
- **FIXED — Reviewer LOW (defense-in-depth):** `_resolve_attack` now FAILS LOUD if a PC defense entry reaches RESOLVE unfilled (instead of silently server-rolling a player's defense).
- **FIXED — Reviewer LOW (simplify + doc):** threaded `ruleset` through `_finish_defense` (no redundant `get_ruleset_module`); reworded the "double-narration prevention" docstring/comment to locate the exactly-once guarantee at the caller's `ledger_full` gate.
- **DEFERRED (documented, see Design Deviations):** concede-at-defend wire (AC-4 vs AC-6 spec inconsistency — SM/Architect decision); `ADR-148/149` citations (needs an Architect to author the DEFEND-barrier ADR); private-helper type annotations (lang-review #3 exempts private helpers); the TEA test-completeness improvements (partial-fill / defense-wins unit tests).

**Tests after rework:** `pytest -k fate` → **591 passed, 1 skipped** (588 + 3 new: 1 auth + 2 NPC-role). Span file (`-n0`) → 7 passed. Lint + format clean on touched files.

## Subagent Results (Round 1 — superseded by Round 2 below)

Enabled per `workflow.reviewer_subagents`: preflight, test_analyzer, comment_analyzer, rule_checker. The other five are disabled via settings (pre-filled below). I ran my own edge/silent/type/security/simplify analysis to cover the disabled domains — and the blocking finding (#1 below) came out of that self-analysis (Devil's Advocate), which the disabled `security`/`edge_hunter` subagents would otherwise have surfaced.

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (588 fate pass / 1 skip, lint clean, 0 new smells, 2 pre-existing TODOs) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — covered by my own analysis |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — covered by my own analysis |
| 4 | reviewer-test-analyzer | Yes | findings | 9 | confirmed 9 (Low/Med), dismissed 0 |
| 5 | reviewer-comment-analyzer | Yes | findings | 4 | confirmed 4, dismissed 0 |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — covered by my own analysis |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings — covered by my own analysis (found the blocking #1) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — covered by my own analysis |
| 9 | reviewer-rule-checker | Yes | findings | 5 | confirmed 5, dismissed 0 |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 1 High, 3 Medium, ~8 Low — all confirmed; 0 dismissed.

## Reviewer Assessment (Round 1 — REJECTED, superseded by Round 2 below)

**Verdict:** REJECTED

The core feature — physics-is-the-roll player defense, the sealed-commit DEFEND barrier, resume-and-narrate-once — is well-built and thoroughly tested, and the load-bearing project rules pass (see Rule Compliance / VERIFIEDs). But the defend handler is missing a server-side **defender-authorization check**, which in a multiplayer table lets one authenticated player fill (and grief) another player's defense and lock the real defender out. That is a `[HIGH]` integrity gap and it blocks.

### Findings

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| `[HIGH]` `[SEC]` | **Missing defender authorization on the defend path.** `dispatch_fate_defense` matches the pending entry by client-supplied `request_id` ONLY — it never verifies the authenticated actor (`character.core.name`, resolved from the seat map) is that entry's `defender`. In MP, player A can send `FATE_THROW(action="defend", request_id=<B's request>)`; the server resolves the defense with **A's skill + A's thrown faces** (`find_creature_core(actor_name=A)`) and records it onto **B's** `pending_defenses` entry, then rejects B's own throw as "already recorded." The request_id is derivable (`def:{round}:{attacker}->{target}`), so it is trivially reachable. Inconsistent with the ADR-119 `player_id` spoof-rejection 20 lines up in the SAME handler. | `sidequest/server/dispatch/fate_conflict.py:1170` (`dispatch_fate_defense`) / `sidequest/handlers/fate_throw.py:260` (`_handle_defend`) | Verify `entry.defender == character.core.name`; reject loudly (FateConflictError / `_error_msg`) on mismatch, mirroring the existing player_id spoof-rejection. Add a RED test: player A's defend throw against B's request_id is rejected and B's entry stays unfilled. |
| `[MEDIUM]` `[RULE]` | **NPC defense rolls are mis-tagged `role="action"`.** `_roll_defense` → `ruleset.resolve_action(...)`, which hardcodes `role="action"` in the `fate.action_resolved` span. AC-8 requires an NPC defense to be `role="defense", source="server_rolled"` so the GM panel can distinguish an NPC's defense from its proactive action. Player-side roles are correct; only the NPC defense path is wrong. Undocumented deviation from AC-8. | `sidequest/game/ruleset/fate.py:226` (server `resolve_action`); `_roll_defense` at `sidequest/server/dispatch/fate_conflict.py:578` | Add a `role: str = "action"` param to `resolve_action` (mirror `resolve_action_from_faces`); pass `role="defense"` from `_roll_defense`. Add an NPC-defense-role span test. |
| `[MEDIUM]` `[RULE]` | **Concede-at-defend is implemented but unwired — dead code.** `dispatch_fate_defense(conceded=...)`, the `_resolve_attack` concede branch, the `ledger_full ... or p.conceded` clause, and `FatePendingDefense.conceded` exist and are unit-tested, but NO production caller ever passes `conceded=True` (the only caller, `_handle_defend`, does not) and `FateThrowPayload(action="defend")` has no concede field. AC-4 ("a concession marks the entry conceded and fills the ledger") has no wire (AC-6 gap). Hits the project's "No half-wired features / Dead code is worse than no code" rule. | `sidequest/server/dispatch/fate_conflict.py:611,1182`; `sidequest/game/encounter.py` (`FatePendingDefense.conceded`) | Reconcile AC-4 vs AC-6: either add a defend-concession wire (a `concede` flag on the defend throw + handler plumbing) OR formally defer concede-at-defend and REMOVE the dead `conceded` branches. SM/spec decision. |
| `[MEDIUM]` `[DOC]` | **`ADR-148/149` citations reference the wrong ADR.** ADR-149 is "Ruleset-Tier SRD Reference Content," not the DEFEND barrier; no DEFEND-barrier ADR was ever authored. 9 production files (24 occurrences) cite `ADR-148/149`. The story's References planned "ADR-149: Fate Defend Follow-up Barrier (to be authored in this story)" but 149 was already taken. | `sidequest/{game/encounter.py, handlers/fate_throw.py, server/dispatch/fate_conflict.py, telemetry/spans/fate.py, protocol/*, server/websocket_session_handler.py}` | Author the DEFEND-barrier ADR under a free number and update the citations, OR drop `/149` and cite the approved spec directly. |
| `[LOW]` `[DOC]` | **"double-narration prevention" docstring overstatement.** `_narrate_resolved_fate_exchange` (and the `_finish_defense` RESUME comment) claim `_execute_narration_turn` "owns double-narration prevention." It does not — there is no double-invocation guard in `_execute_narration_turn`; "narrate exactly once" is enforced by the CALLER's `ledger_full` gate in `_finish_defense`. Persistence / husk-reaping / fan-out claims ARE accurate. | `sidequest/server/websocket_session_handler.py:3478`; `sidequest/handlers/fate_throw.py:327` | Reword: locate the "exactly once" guarantee at the `ledger_full` caller-gate, not the callee. |
| `[LOW]` `[SILENT]` | **`_resolve_attack` else-branch silently server-rolls an unfilled PC defense.** When `recorded is not None` but `defense_total is None and not conceded`, the code falls to `else: _roll_defense(...)` — server-rolling a PC's defense (the exact backdoor 126-8 closes). Unreachable today (gated by `ledger_full` before resume), but it is a No-Silent-Fallbacks defense-in-depth gap that would activate the wrong path if `run_fate_exchange` were ever called with a partial ledger. | `sidequest/server/dispatch/fate_conflict.py:619-622` | Guard: if a PC ledger entry is unfilled at resume, fail loud rather than server-roll. |
| `[LOW]` `[SIMPLE]` | **Redundant `get_ruleset_module` lookup.** `_finish_defense` re-resolves the ruleset (`:333`) already resolved in `_handle_defend` (`:258`); the result is not threaded through — two registry lookups per defend turn. | `sidequest/handlers/fate_throw.py:258,333` | Thread the `ruleset` from `_handle_defend` into `_finish_defense`. |
| `[LOW]` `[TYPE]` | **Untyped params on the new private dispatch helpers.** `_handle_defend`/`_finish_defense`/`_seat_player_id` params (`sd`, `snapshot`, `encounter`, `character`, `payload`) are implicit `Any`. Rule #3 exempts private helpers, but the surrounding handler methods in this file ARE annotated — file convention favors annotating. | `sidequest/handlers/fate_throw.py:239,282,344` | Annotate (`sd: _SessionData`, `snapshot: GameSnapshot`, `encounter: StructuredEncounter`, `character: Character`, `payload: FateThrowPayload`). |
| `[LOW]` `[TEST]` | **Test-completeness gaps** (test-analyzer): the wiring test stubs `_narrate_resolved_fate_exchange` (Dev-documented) so the real seam isn't exercised end-to-end; no unit test for the two-defender partial-fill `ledger_full=False` boundary; no "defense wins" (recorded_defense ≥ attack → no harm) test on the recorded path; `test_handler_drives_dispatch_end_to_end` doesn't assert the FATE_ACTION handler emits NO defend-request (the gap stays invisible); two tautological construction/default tests. | `tests/server/test_fate_defend_barrier_wiring.py`, `tests/server/dispatch/test_fate_defense_record.py`, `test_fate_resume_resolve.py`, `tests/server/test_fate_action_handler_wiring.py` | Add the partial-fill + defense-wins tests; assert the FATE_ACTION no-defend-request gap explicitly. |
| `[LOW]` | **`FateActionHandler` park gap is dormant** (Dev-flagged). Traced to ground: the live UI sends only `concede`/`compel_*` on `FATE_ACTION`, both of which `return` in `dispatch_fate_action` BEFORE the REVEAL+park code (`:62`, `:78`); roll verbs go via `FATE_THROW` → `FateThrowHandler`. So `FateActionHandler` cannot reach `awaiting_defense` from the live UI. | `sidequest/handlers/fate_action.py` | Optional hardening: have `FateActionHandler` reject roll-verb actions (now owned by `FATE_THROW`) or mirror the park handling, for defense-in-depth. |

### Rule Compliance

Enumerated against the Python lang-review checklist (13) + server CLAUDE.md / SOUL.md project rules:

- **#1 Silent exceptions** — VERIFIED. `dispatch_fate_defense` raises `FateConflictError` loud on unknown (`:1172`) and already-filled (`:1177`) request_id; `_handle_defend` (`:269`) and `handle` (`:151`) catch specifically + log warning + return `_error_msg`. No bare/swallowing except. One Low defense-in-depth gap: `_resolve_attack` else silently server-rolls an unfilled PC entry (`:619-622`, unreachable).
- **#3 Type annotations** — Low gap: `_handle_defend`/`_finish_defense`/`_seat_player_id` params untyped (rule exempts private helpers; file convention annotates). All public/boundary additions (`resolve_action_from_faces` role, span params, `dispatch_fate_defense`, `resume_fate_exchange`, `_narrate_resolved_fate_exchange`) ARE annotated.
- **#4 Logging** — VERIFIED. New error path `fate.defend.broadcast_no_room` at `error` (programming error); `fate.defend.dispatch_error` at `warning` (client-driven rejection — correct level); lazy `%` form; no sensitive data.
- **#6 / #18 / #22 Test quality + wiring + no-source-grep** — VERIFIED with Low gaps. Wiring tests exist and drive the REAL handler/registry (`test_fate_defend_barrier_wiring.py`, `test_fate_throw_emits_defend_request.py`); no `read_text()`/regex-on-source; registry reflection is the legitimate exception. Gaps: stubbed narration seam, missing partial-fill/defense-wins tests, two tautological tests.
- **#9 Async** — VERIFIED. `_handle_defend`/`_finish_defense`/`_narrate_resolved_fate_exchange` all correctly `await`ed; no blocking calls, no missing awaits.
- **#10 Imports** — VERIFIED (lazy in-function imports are the established cycle-break pattern). One Low: redundant `get_ruleset_module`.
- **#11 / #21 Input validation** — VERIFIED. `FateThrowPayload` face validator fires for `action="defend"` (4 faces, dF range); `FateDefendRequestPayload` + `FatePendingDefense` use `extra="forbid"`; request_id failures raise loud. **BUT the authorization dimension is NOT validated** — the defend throw is not checked against the request's `defender` (finding #1, HIGH).
- **No Silent Fallbacks (project)** — VERIFIED on the request_id paths (loud raises). `_seat_player_id` empty-string is documented + safe (client filters by `defender`). One Low (`_resolve_attack` else).
- **No Stubbing / Dead code (project)** — VIOLATION (Medium): the concede-at-defend branches are dead in the live path (finding #3).
- **Don't Reinvent / Verify Wiring (project)** — VERIFIED. `_narrate_resolved_fate_exchange` reuses the real `_execute_narration_turn` seam (mirrors `DiceThrowHandler`); every new symbol (`dispatch_fate_defense`, `resume_fate_exchange`, `_build_pending_defenses`, `_narrate_resolved_fate_exchange`) has a production consumer.
- **OTEL Observability (project)** — VERIFIED with one Medium gap: `fate.defend_phase` span fires at request (`responded=False`) and response (`responded=True`), is routed in `SPAN_ROUTES`, and is in `__all__`; `role` added to `fate.action_resolved`. Gap: NPC defense `role` mis-tagged (finding #2).
- **Bind the Ruleset, Don't Balance It (SOUL)** — VERIFIED. `fate_resolution.py` not in the diff (`classify_outcome`/shifts/tiers untouched). `_resolve_attack` shift math `shifts = commit.ladder_total - defense_total` is UNCHANGED — only the SOURCE of `defense_total` (recorded vs rolled) changed. No native-mechanic tuning.

### Data Flow Traced

A player's defend throw: client `FATE_THROW(action="defend", request_id, face)` → `FateThrowHandler.handle` (authenticated `sd.player_id`; inbound `player_id` spoof-rejected) → `_handle_defend` → `dispatch_fate_defense(actor_name=character.core.name, request_id, thrown_faces)` → `resolve_action_from_faces(role="defense")` (NEVER `roll_4df` on the player path — VERIFIED) → records `defense_total` on the matching entry → on `ledger_full`, `_finish_defense` → `resume_fate_exchange` (recorded PC defense read; NPC defense server-rolled) → `_resolve_attack` (shift math unchanged) → `_narrate_resolved_fate_exchange` → `_execute_narration_turn(suppress_intent_router=True)`. **The flow is safe for face/skill provenance but NOT for defender identity:** the `request_id`→entry match is unauthenticated, so the actor who throws need not be the entry's defender (finding #1).

### Devil's Advocate

Assume this is broken. The strongest attack is the one above: the `request_id` is the server's own derivable string (`def:{round}:{attacker}->{target}`), broadcast to the whole table, and `dispatch_fate_defense` trusts it to belong to whoever sent it. A bored or hostile seated player simply answers a teammate's defense with garbage faces; the teammate is hit and then locked out ("already recorded"). The codebase's own ADR-119 posture — the `player_id` spoof-rejection sitting in the same handler — proves the team treats client-supplied identity as untrusted, yet the defend path trusts a client-supplied request_id implicitly. Even absent malice, a UI bug that emits the wrong request_id, or two near-simultaneous defend throws racing on the same socket, corrupts the wrong entry silently. Second attack surface: the AFK defender. AC-7 is explicit "block-and-wait, no auto-roll," which is correct doctrine — but it means a single non-responding seat freezes the entire table indefinitely with no GM-override surface server-side; that is a deliberate design choice (never rush a slow typist, per Alex) but it is also a denial-of-progress with no escape hatch, and worth a product conversation. Third: the concede-at-defend dead code is a latent trap — a future contributor sees `dispatch_fate_defense(conceded=...)` tested and green and assumes the feature is live, wiring UI to a path that the protocol can't actually express. Fourth: a confused player throwing before the FATE_DEFEND_REQUEST renders sends a defend with a stale/empty request_id → loud rejection (safe). Fifth: huge/zero inputs — faces are validated to {-1,0,1}×4 at the pydantic boundary, so no overflow; `attack_total` is an int with no upper bound, but it only flows into ladder subtraction (no allocation/iteration), so no DoS. The mechanics themselves are sound; the integrity gap is identity, not math.

### Handoff

Back to TEA (Amos Burton) for a RED test on the blocking authorization finding, then Dev (Naomi Nagata) to make it green. The blocking finding is a testable logic/authorization bug → `review → red → rework`.

## Subagent Results

Round 2 — re-review of the rework diff (`git diff c7ebf64b..HEAD`, 6 files / 143 lines) that resolved the Round-1 REJECT. Same enabled set (preflight, test_analyzer, comment_analyzer, rule_checker); the five disabled are pre-filled. My own Devil's Advocate covered the disabled edge/security/silent domains.

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (591 fate pass / 1 skip, span 7 pass, lint+format+tree clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled — covered by my own Devil's Advocate |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled — covered by my own analysis |
| 4 | reviewer-test-analyzer | Yes | findings | 3 (all LOW) | confirmed 3, dismissed 0 |
| 5 | reviewer-comment-analyzer | Yes | clean | none (Round-1 "lying docstring" resolved) | N/A |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled — covered by my own analysis |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled — covered by my own analysis |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled — covered by my own analysis |
| 9 | reviewer-rule-checker | Yes | findings | 2 (1 Med, 1 Low) | confirmed 2, dismissed 0 |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 0 Critical, 0 High, 1 Medium, ~4 Low — all confirmed; 0 dismissed.

## Reviewer Assessment

**Verdict:** APPROVED

The Round-1 blocking `[HIGH]` finding (missing defender authorization) is **fixed correctly and meaningfully tested**, and every other Round-1 finding is resolved or reasonably deferred. No Critical/High remain. One new `[MEDIUM]` (an OTEL watcher-event gap on the auth rejection) and a few `[LOW]`s are non-blocking — logged as fast-follows. Approving.

### Verification of the Round-1 fixes

- `[SEC]` `[VERIFIED]` **Authorization fix is correct.** `dispatch_fate_defense` raises `FateConflictError` when `entry.defender != actor_name` (`fate_conflict.py:1196`) — placed AFTER the unknown-request_id guard and BEFORE both the already-filled guard and ANY state mutation (`entry.conceded = True` at `:1207`), and before `find_creature_core(actor_name)` (`:1211`) so an impostor with no sheet hits the guard, not a NoneType. `actor_name` is `_handle_defend`'s `character.core.name`, resolved from the authenticated `sd.player_id`/seat map — NOT client text. Fails loud → `_error_msg`. Test `test_defend_throw_from_non_defender_is_rejected` reaches the guard and asserts the victim's entry stays unfilled (rule-checker + test-analyzer both confirmed the guard ordering and that the test is genuine, not a NoneType pass).
- `[RULE]` `[VERIFIED]` **AC-8 NPC role fixed.** Server `resolve_action` gained `role: str = "action"` (annotated); `_roll_defense` passes `role="defense"` (`fate_conflict.py:275`). The default preserves all NPC-proactive callers (`_seat_opponent_commits`, `dispatch_fate_action` pass no `role` → `"action"`). `role` flows only to `fate_action_resolved_span` — the `resolve_action` free function and shift math are untouched (Bind the Ruleset holds). Two new span tests, one driving the real production `_roll_defense`.
- `[SILENT]` `[VERIFIED]` **Defense-in-depth guard.** `_resolve_attack` now raises loud on an unfilled PC entry (`elif recorded is not None`) instead of silently server-rolling a player's defense; the `else` (no entry = genuine NPC) still server-rolls. Correct distinction; unreachable at `ledger_full` resume, so no legit-path impact.
- `[SIMPLE]` `[VERIFIED]` **Redundant lookup removed.** `ruleset` is threaded from `_handle_defend` into `_finish_defense`; the duplicate `get_ruleset_module` is gone. No behavior change.
- `[DOC]` `[VERIFIED]` **"Lying docstring" resolved.** The reworded `_narrate_resolved_fate_exchange` docstring + `_finish_defense` comment correctly locate the exactly-once guarantee at the caller's `ledger_full` gate (comment-analyzer: clean — confirmed `_execute_narration_turn` has no double-invocation guard and the narrate path is reached only when `ledger_full` first flips True).
- `[TYPE]` Private-helper params (`_handle_defend`/`_finish_defense`/`_seat_player_id`) left untyped — lang-review #3 exempts private helpers; the new public `role` param IS annotated. Accepted deferral.
- `[EDGE]` `[VERIFIED]` **No new edge hole** (my Devil's Advocate): the auth guard cannot break a legitimate defender (`entry.defender` derives from the same PC name `_handle_defend` resolves from the authenticated seat); the `role` default preserves proactive callers; the `elif` is unreachable at `ledger_full`. 591 passing tests confirm no legit-path regression.

### New / residual findings (all non-blocking)

| Severity | Issue | Location | Fix |
|----------|-------|----------|-----|
| `[MEDIUM]` `[RULE]` | **The authorization rejection emits no OTEL watcher event.** The sibling `player_id` spoof-rejection (`fate_throw.py:77-91`) emits `publish_event(op="fate_throw_player_id_spoof_rejected")`; the new defend-authorization rejection only logs at WARNING, so the GM panel (the lie detector) cannot see a cross-seat defense attempt — exactly the kind of subsystem-security decision the OTEL principle says MUST emit a watcher event. Non-blocking: the guard FUNCTIONS and logs; the gap is GM-panel telemetry (observability), which the severity table classes as Medium. But it is the strongest residual finding and should be the first fast-follow. | `sidequest/handlers/fate_throw.py:269-271` (the `except FateConflictError` branch) | Emit `publish_event("state_transition", {field:"session_binding", op:"fate_defend_authorization_rejected", defender, actor, request_id, recovery:"auth_identity_enforced", source:"fate_defend"}, component="session", severity="warning")`, mirroring the spoof-rejection. |
| `[LOW]` `[TEST]` | `test_defend_throw_from_non_defender_is_rejected` uses `pytest.raises(FateConflictError)` with no `match=` — a future guard-reorder could make it pass while the auth guard is dead. | `tests/server/dispatch/test_fate_defense_record.py` | Add `match="authorization"` (the production message already contains the word) — zero cost. |
| `[LOW]` `[TEST]` | `test_npc_server_defense_tags_role_defense` uses `next(gen)` for the span (opaque `StopIteration` on 0 spans) and lacks the `isinstance(..., FateRulesetModule)` guard its sibling test has. | `tests/game/ruleset/test_fate_defend_spans.py` | Use `spans = [...]; assert len(spans) == 1; span = spans[0]`; add the isinstance assert. |
| `[LOW]` `[TEST]` | `test_npc_server_action_defaults_role_action` calls `resolve_action` directly (proves the default exists, not that a production action caller omits `role`). Acceptable unit test; a production-caller companion would be stronger. | `tests/game/ruleset/test_fate_defend_spans.py` | Optional: add a production NPC-action-path companion mirroring the defense test. |

Deferred from Round 1 (documented as Dev deviations, accepted): concede-at-defend AC-4/AC-6 inconsistency (SM/Architect decision); `ADR-148/149` citations (Architect to author the DEFEND ADR); TEA test-completeness (partial-fill / defense-wins unit tests). These remain non-blocking Delivery Findings.

### Data flow re-traced (post-fix)

`FATE_THROW(action="defend", request_id, face)` → `FateThrowHandler.handle` (authenticated `sd.player_id`; inbound `player_id` spoof-rejected) → `_handle_defend` (resolves `character` from the authenticated seat) → `dispatch_fate_defense(actor_name=character.core.name, ...)` → **authorization: `entry.defender != actor_name` → reject loud** → `resolve_action_from_faces(role="defense")` (never `roll_4df`) → record `defense_total` → on `ledger_full`, `_finish_defense(ruleset=...)` → `resume_fate_exchange` (recorded PC defense; NPC server-rolled with `role="defense"`) → `_resolve_attack` (shift math unchanged; loud on unfilled PC entry) → `_narrate_resolved_fate_exchange`. The identity gap from Round 1 is closed: only the authenticated defender can fill their own entry.

### Devil's Advocate (round 2)

The Round-1 attack — player A answering B's defend request — now fails loud at `dispatch_fate_defense`, and A cannot lock B out (B's entry stays unfilled). The remaining adversarial angles are weaker: (1) The auth rejection is invisible to the GM panel (the Medium above) — a determined griefer can spam rejected defend throws and the operator sees only Python WARNING logs, not a lie-detector signal; mitigated by the WARNING log but worth the watcher event. (2) The AFK-defender denial-of-progress (block-and-wait, no timeout) persists from Round 1 — deliberate per AC-7/SOUL, still no server-side GM-override surface; a product question, not a regression. (3) Name-identity: the whole Fate exchange keys on PC names (`commit.actor`/`target`/`entry.defender`), so a duplicate PC name would confuse the auth check — but name collisions are a pre-existing, system-wide assumption, not introduced here. (4) The new `elif` raise in `_resolve_attack` could in theory fire if a future caller invokes `run_fate_exchange` with a partially-filled ledger — but that now fails LOUD (the intended No-Silent-Fallbacks behavior), which is strictly safer than the prior silent server-roll. No new break found; the rework is a net hardening.

### Handoff

To SM (Camina Drummer) for finish-story.

## Delivery Findings

No upstream findings.

### TEA (test design)
- **Question** (non-blocking): The narration-on-resume **cadence** is an open design question the server plan flagged for the author (plan Self-Review: today's `FATE_THROW` path never narrates a resolved exchange; "one narration at RESOLVE" is NEW behavior — "confirm before executing Task 7"). The RED tests encode the AC's observable (`run_narration_turn` invoked exactly once at RESOLVE) via an orchestrator spy. *Confirm the cadence (narrate-from-the-defend-handler vs narration-rides-the-next-NL-turn) before wiring `_finish_defense`.* *Found by TEA during test design.*
- **Gap** (non-blocking): The plan's narration/persistence seams reference signatures that differ from live code — `_build_turn_context(session, sd)` is actually `_build_turn_context(sd, *, room=...)` (`session_helpers.py:634`) and reads `sd.genre_pack.rules.confrontations`; the natural-language turn persists via `self._room.save()` / `sd.repository.save(snapshot)` (`websocket_session_handler.py:1551`) and emits narration via `NarrationMessage(...)` (`:2944`). Affects `sidequest/handlers/fate_throw.py` (`_finish_defense` must bind to these REAL seams, not invent new ones — Don't Reinvent / No Stubbing). The wiring harness sets `genre_pack.rules.confrontations=[]`; if `_build_turn_context` needs more session state than the SimpleNamespace double provides, enrich the harness rather than stub the seam. *Found by TEA during test design.*
- **Gap** (non-blocking): `tests/protocol/test_enums.py` asserts `len(MessageType) == 58`; adding `FATE_DEFEND_REQUEST` makes it 59. Affects `tests/protocol/test_enums.py` (Dev bumps the literal to 59 — it is intentional; not covered by the new RED tests). *Found by TEA during test design.*
- **Improvement** (non-blocking): The span file `tests/game/ruleset/test_fate_defend_spans.py` must run serially (`-n0`) — the parallel runner has a known span-count deadlock on telemetry files (project memory). Affects the CI/local run command for that file only. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): 88 pre-existing branch failures unrelated to 126-8 — WN combat beat-pool comes up empty (`beat id(s) [...] not in pool`, `available: []`), Fate `rulesets/fate/srd/` reference content is not provisioned into the test temp fixtures (`GenreLoadError ... requires reference content under rulesets/fate/srd/`), and `tests/server/test_app.py::test_create_app_uses_build_llm_client_by_default` expects a `build_async_anthropic` symbol that no longer exists. **Verified pre-existing**: `git stash` of ALL uncommitted work → identical failures on the clean branch HEAD (RED commit). Root cause is content-tier provisioning (content repo on develop `b1b10b7` ships Fate SRD at top-level `rulesets/`; the genre-pack test fixtures don't copy that tier into their temp dirs) + one stale narrator-backend test — environment, not server dispatch/handler code. Affects `tests/genre/*`, `tests/integration/*wn*`, `tests/server/test_app.py`. *Found by Dev during implementation.*
- **Gap** (non-blocking): `FateActionHandler` (`sidequest/handlers/fate_action.py`) does NOT handle the 126-8 DEFEND-barrier park — on `result.awaiting_defense` it broadcasts the proactive roll but emits no `FATE_DEFEND_REQUEST` and persists no parked checkpoint (unlike `FateThrowHandler`). A player on the legacy server-rolled FATE_ACTION path would park without ever being asked to defend (stuck barrier). Acceptable only if FATE_ACTION is being retired in favor of FATE_THROW (physics-is-the-roll); otherwise it needs the same `awaiting_defense` branch FateThrowHandler has. Affects `sidequest/handlers/fate_action.py`. *Found by Dev during implementation.*
- **Improvement** (non-blocking): `test_full_defend_round_through_real_handlers` stubs `_narrate_resolved_fate_exchange` on the SimpleNamespace session double, so the method's real body (`_build_turn_context` + `_execute_narration_turn`) is not exercised end-to-end. A follow-up integration test with a fuller session (or a real `WebSocketSessionHandler`) would close the gap; the body mirrors the dice-replay precedent, which IS covered elsewhere. Affects `tests/server/test_fate_defend_barrier_wiring.py`. *Found by Dev during implementation.*
- **Note** (non-blocking): the UI defense-throw tray remains the deferred follow-up per spec §8 (this is a server-only story). *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): Missing defender authorization on the defend path — `dispatch_fate_defense` matches the parked entry by client-supplied `request_id` only and never verifies the authenticated actor is that entry's `defender`, so in MP one player can fill/grief another's defense (with their own dice + skill) and lock the real defender out. Affects `sidequest/server/dispatch/fate_conflict.py:1170` / `sidequest/handlers/fate_throw.py:260` (verify `entry.defender == character.core.name`, reject loud on mismatch — mirror the ADR-119 player_id spoof-rejection in the same handler; add a RED test). *Found by Reviewer during code review.*
- **Gap** (non-blocking): NPC defense rolls emit `fate.action_resolved` with `role="action"` instead of `role="defense"` (AC-8) — `_roll_defense` → `resolve_action` hardcodes the role. Affects `sidequest/game/ruleset/fate.py:226` (add a `role` param to `resolve_action`; pass `role="defense"` from `_roll_defense`; add a span test). *Found by Reviewer during code review.*
- **Conflict** (non-blocking): AC-4 requires a defend-time concession but AC-6 provides no wire for it, so the server-side concede-at-defend machinery (`dispatch_fate_defense(conceded=...)`, the `_resolve_attack` concede branch, `FatePendingDefense.conceded`) is dead code in the live path. Affects `sidequest/server/dispatch/fate_conflict.py:611,1182` + `sidequest/game/encounter.py` (reconcile AC-4/AC-6: wire it or remove the dead branches — SM/spec decision). *Found by Reviewer during code review.*
- **Gap** (non-blocking): The `ADR-148/149` co-citation in 9 production files references the wrong ADR — ADR-149 is "Ruleset-Tier SRD Reference Content," not the DEFEND barrier, which was never authored. Affects `sidequest/{game/encounter.py,handlers/fate_throw.py,server/dispatch/fate_conflict.py,telemetry/spans/fate.py,protocol/*,server/websocket_session_handler.py}` (author the DEFEND-barrier ADR under a free number and update citations, or drop `/149` and cite the approved spec). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The `_narrate_resolved_fate_exchange` docstring + `_finish_defense` RESUME comment claim `_execute_narration_turn` "owns double-narration prevention," but the exactly-once guarantee is the caller's `ledger_full` gate, not a guard in the callee. Affects `sidequest/server/websocket_session_handler.py:3478`, `sidequest/handlers/fate_throw.py:327` (reword to locate the guarantee at the caller). *Found by Reviewer during code review.* [RESOLVED in rework — comment-analyzer round 2 confirmed accurate.]
- **Gap** (non-blocking, round 2): The new defend-path authorization rejection emits no OTEL watcher event, unlike the sibling `player_id` spoof-rejection (`fate_throw.py:77-91`, `publish_event(op="fate_throw_player_id_spoof_rejected")`). The OTEL principle requires a watcher event on this subsystem-security decision so the GM panel can see a cross-seat defense attempt; today it only logs at WARNING. Affects `sidequest/handlers/fate_throw.py:269-271` (emit `publish_event("state_transition", {op:"fate_defend_authorization_rejected", ...}, component="session", severity="warning")`). Strongest residual finding — recommend as the first fast-follow. *Found by Reviewer during code review (round 2).*
- **Improvement** (non-blocking, round 2): Two LOW test-quality nits on the rework tests — `test_defend_throw_from_non_defender_is_rejected` should add `match="authorization"` to `pytest.raises`; `test_npc_server_defense_tags_role_defense` should use a list + `len==1` instead of `next(gen)` and add an `isinstance(..., FateRulesetModule)` guard. Affects `tests/server/dispatch/test_fate_defense_record.py`, `tests/game/ruleset/test_fate_defend_spans.py`. *Found by Reviewer during code review (round 2).*

## Design Deviations

### TEA (test design)
- **"Narrate once at RESOLVE" asserted via an orchestrator spy, not the full NarrationMessage pipeline**
  - Spec source: context-story-126-8.md, AC "Resume and walk" ("invoke the narrator **once** to render the entire woven exchange"); server plan Task 7 Step 5.
  - Spec text: "After resolution, invoke the narrator once to render the entire woven exchange."
  - Implementation: the end-to-end wiring test (`test_full_defend_round_through_real_handlers`) asserts `sd.orchestrator.run_narration_turn` was awaited exactly once (a counting `FakeOrchestrator`), rather than asserting a `NARRATION` message broadcast through `_build_turn_context` + the real emit seam.
  - Rationale: the narration-on-resume trigger is an explicit OPEN design question the plan flagged for the author (plan Self-Review: "confirm before executing Task 7"), and the emit seam rides the heavy `_build_turn_context(sd, *, room=...)` + `websocket_session_handler.py:2944` pipeline that the lightweight SimpleNamespace harness can't faithfully drive. The spy pins the AC's observable (exactly-one narrator call) without coupling the RED test to a contested/heavy seam.
  - Severity: minor
  - Forward impact: Dev wires `_finish_defense` to call the real narration seam; if the author confirms a different cadence (narration rides the next NL turn), this assertion is updated. See Delivery Findings.
- **Handler/wiring tests drive `HANDLER.handle(session, msg)` on a SimpleNamespace double, not `session.handle_message(...)`**
  - Spec source: server plan Tasks 5 & 8 (test code), reconciled against `tests/server/test_fate_throw_handler_wiring.py`.
  - Spec text: plan test code calls `await session.handle_message(throw_msg)`.
  - Implementation: tests call the real `FateThrowHandler.handle(session, msg)` directly with the canonical `SimpleNamespace` session double + `SessionRoom` queue drain, and assert registry wiring separately via `WebSocketSessionHandler._message_handler_for("FATE_THROW")` (the legitimate reflection net).
  - Rationale: the canonical Fate handler-wiring harness (126-7's `test_fate_throw_handler_wiring.py`) uses exactly this shape; a SimpleNamespace has no `handle_message`, so the plan's call would fail for the wrong reason. This still exercises the real handler/registry/exchange (AC-9) without standing up a full `WebSocketSessionHandler`.
  - Severity: minor
  - Forward impact: none — Dev's production handler is unchanged; the harness just calls the real entry point.
- **Plan test-code API shapes corrected to live signatures (non-substantive)**
  - Spec source: server plan test snippets (Tasks 1, 2, 7).
  - Spec text: `ThrowParams(position=.., velocity=.., angular=.., spin=0.0)`; `StructuredEncounter(encounter_type="conflict")`; `_build_turn_context(session, sd)`.
  - Implementation: used `ThrowParams(velocity:(f,f,f), angular:(f,f,f), position:(f,f))` from `sidequest.protocol.dice` (no `spin`); `StructuredEncounter(...)` with the required `player_metric`/`opponent_metric`; documented the real `_build_turn_context(sd, *, room=...)` signature for Dev.
  - Rationale: the plan's snippets carried aspirational/incorrect signatures; copying verbatim would have produced fixture-construction failures (wrong RED reason) instead of missing-production failures.
  - Severity: trivial
  - Forward impact: none.

### Dev (implementation)
- **Narration at RESOLVE delegated to a new session method (`_narrate_resolved_fate_exchange`), mirroring the dice-replay precedent — not the hand-rolled `run_narration_turn` the RED spy implied**
  - Spec source: context-story-126-8.md AC-5 "Resume and walk"; TEA Delivery Finding "Question" on narration cadence.
  - Spec text: "invoke the narrator **once** to render the whole woven exchange" / "narrate once at RESOLVE."
  - Implementation: added `WebSocketSessionHandler._narrate_resolved_fate_exchange(sd, action)` = `_build_turn_context(sd, lore_context, room=self._room)` + `_execute_narration_turn(sd, action, turn_context, suppress_intent_router=True)` — the EXACT seam `DiceThrowHandler` uses to narrate a server-resolved mechanical replay (`[BEAT_RESOLVED]`/`[DOGFIGHT_SHOT_RESOLVED]`). `_finish_defense` resolves mechanically (`resume_fate_exchange`) then delegates to it. Cadence Question resolved as narrate-once-at-RESOLVE (the AC, highest authority). Reverted the hand-rolled `run_narration_turn` + manual `NarrationMessage` broadcast (it reinvented the emit seam, losing husk-reaping / double-narration-prevention / persist-via-emit — Don't Reinvent).
  - Rationale: production runs the REAL narration seam; the lightweight wiring harness stubs the one session method (the stub boundary sits ABOVE `_build_turn_context`, keeping the SimpleNamespace double minimal). Chosen over inlining (Option B), which would have required enriching the harness to drive `_build_turn_context`+`_execute_narration_turn` (whack-a-mole) and still stub a session method.
  - Severity: minor
  - Forward impact: the real method body is not exercised by the wiring test (stubbed) — see Delivery Findings (follow-up integration test).
- **Migrated 10 pre-existing Fate tests from the removed inline-server-rolled-PC-defense behavior to the two-phase DEFEND-barrier contract**
  - Spec source: context-story-126-8.md AC-3/AC-4/AC-5.
  - Spec text: "If any PC is targeted by an attack, write `pending_defenses` ledger ... and park"; "no `roll_4df` on the player defense path."
  - Implementation: the prior-session REVEAL+park restructure makes `dispatch_fate_action` PARK whenever a live seated PC is attacked, so 10 tests across 8 files asserting single-call inline resolution (`exchange is not None`, `Thug.withdrawn`, inline stress on the PC) began failing. Migrated each to drive proactive→park→`resolve_parked_defenses`→resume and assert the SAME resolved outcome; added a shared `resolve_parked_defenses` driver to `tests/_helpers/fate_fixtures.py`. **User approved "migrate, drive full resolution"** (AskUserQuestion). Files: `test_fate_opponent_seating.py`(2), `test_fate_dispatch_routing.py`(1), `test_fate_harm_routing.py`(1), `test_fate_action_dispatch.py`(1), `test_fate_action_handler_wiring.py`(1), `test_fate_classifier_wiring.py`(1), `test_fate_player_action_narrator_118_6.py`(2), `test_fate_throw_handler_wiring.py`(1).
  - Rationale: these tests encoded behavior the story explicitly REMOVES; deleting loses coverage, leaving them red blocks GREEN. Driving full resolution preserves their original end-to-end assertions through the new flow.
  - Severity: minor (test-only beyond the additive rng param below)
  - Forward impact: `resolve_parked_defenses` is the canonical way to drive a parked Fate exchange in tests going forward.
- **Added an optional `rng` param to `resume_fate_exchange` (production), default-unchanged**
  - Spec source: none (testability; `resume_fate_exchange` is new this story).
  - Spec text: n/a.
  - Implementation: `resume_fate_exchange(..., rng: random.Random | None = None)` → fresh `random.Random()` when None (production NPC defenses stay genuinely random — unchanged), letting tests pass a seeded rng so surviving NPC defense rolls at RESUME are deterministic.
  - Rationale: without it, migrated tests depending on whether the PC's attack beats the NPC's RESUME-time defense were ~1–8% flaky; the param removes the flake while leaving production behavior identical (the live handler calls it without `rng`).
  - Severity: trivial
  - Forward impact: none.

### Reviewer (audit)

**TEA deviations:**
- **"Narrate once at RESOLVE" asserted via an orchestrator spy** → ✓ ACCEPTED by Reviewer: sound given the heavy seam; Dev wired the real `_execute_narration_turn` in production. Residual: the wiring test still stubs the seam — tracked as a `[LOW][TEST]` finding + a follow-up integration test (Delivery Findings), not a deviation reversal.
- **Handler/wiring tests drive `HANDLER.handle(session, msg)` on a SimpleNamespace double** → ✓ ACCEPTED by Reviewer: matches the canonical 126-7 harness; rule-checker confirmed these are behavioral, not source-grep, wiring tests.
- **Plan test-code API shapes corrected to live signatures** → ✓ ACCEPTED by Reviewer: trivial, non-substantive.

**Dev deviations:**
- **Narration delegated to `_narrate_resolved_fate_exchange` (dice precedent)** → ✓ ACCEPTED by Reviewer: reuses the real seam (Don't-Reinvent — rule-checker confirmed); the `suppress_intent_router=True` + ledger_full gate are correct. Caveat: the docstring's "double-narration prevention" claim is imprecise — logged as a `[LOW][DOC]` finding (the guarantee is the caller's ledger_full gate, not the callee).
- **Migrated 10 pre-126-8 Fate tests to the two-phase contract** → ✓ ACCEPTED by Reviewer: user-approved, preserves coverage (test-analyzer confirmed the migrations were NOT weakened — Thug-withdrawn / stress-applied / resolved-span assertions retained); `resolve_parked_defenses` is a clean shared driver.
- **Added optional `rng` to `resume_fate_exchange`** → ✓ ACCEPTED by Reviewer: additive, production default unchanged; the right fix for the deterministic-NPC-resume-roll flakiness.

**Undocumented deviations found by Reviewer:**
- **NPC defense roll tagged `role="action"` not `role="defense"`:** Spec said AC-8 `role ∈ {action, defense}` with NPC defense = `role="defense", source="server_rolled"`; code emits `role="action"` for NPC defenses (`fate.py:226` via `_roll_defense`). Not documented by Dev/TEA. Severity: M. (Delivery Finding + Findings table #2.)
- **Concede-at-defend implemented but unwired (dead code):** AC-4 requires a defend concession; the server machinery exists and is unit-tested but has no production caller / protocol wire (AC-6 gap). Not documented. Severity: M. (Delivery Finding + Findings table #3.)
- **Missing defender authorization on the defend path:** not a spec deviation per se (the spec assumes the defender answers their own request) but an unspecified, unguarded trust boundary — the implementation trusts client `request_id` to belong to the actor. Severity: H (blocking). (Findings table #1.)
- **`ADR-148/149` citations reference the wrong ADR** (149 is SRD content; the DEFEND-barrier ADR was never authored). Not documented. Severity: M. (Delivery Finding.)

### Dev (rework — review round 1)
- **Added server-side defender authorization on the defend path (resolves Reviewer HIGH #1)**
  - Spec source: Reviewer Assessment Findings #1 (HIGH, blocking); ADR-119 authenticated-identity / player-vs-character split.
  - Spec text: "verify `entry.defender == character.core.name`; reject loudly on mismatch."
  - Implementation: `dispatch_fate_defense` now raises `FateConflictError` when `entry.defender != actor_name` (between the unknown-request_id and already-filled guards) — a seated player can only answer their OWN defend request. `_handle_defend` already passes the authenticated `character.core.name`. Added `test_defend_throw_from_non_defender_is_rejected` (Mallory's throw against Rux's request is rejected; Rux's entry stays unfilled).
  - Rationale: the request_id is client-supplied and derivable, so without this the wrong PC could fill/grief another's defense and lock the real defender out. Mirrors the ADR-119 player_id spoof-rejection in the sibling FATE_THROW handler.
  - Severity: blocking fix
  - Forward impact: none — strictly additive guard + test.
- **NPC server-rolled defenses now tagged `role="defense"` (resolves Reviewer MEDIUM, AC-8)**
  - Spec source: AC-8 ("`role ∈ {action, defense}`"); Reviewer Findings #2.
  - Spec text: "NPC defense = `role=\"defense\", source=\"server_rolled\"`."
  - Implementation: added a `role: str = "action"` param to the server `resolve_action` (mirrors `resolve_action_from_faces`); `_roll_defense` passes `role="defense"`. Added `test_npc_server_defense_tags_role_defense` + `test_npc_server_action_defaults_role_action`.
  - Rationale: lets the GM panel distinguish an NPC defense from an NPC proactive action — closing the AC-8 lie-detector gap. Ladder math untouched (only the span tag).
  - Severity: minor fix
  - Forward impact: none.
- **Concede-at-defend left implemented-but-unwired (DEFERRED — not removed, not wired)**
  - Spec source: AC-4 ("a concession marks the entry conceded and fills the ledger") vs AC-6 (no defend-concession wire); Reviewer Findings #3 (Conflict, "SM/spec decision").
  - Spec text: AC-4 mandates server behavior AC-6 provides no protocol field for.
  - Implementation: left the server-side concede machinery (`dispatch_fate_defense(conceded=...)`, `_resolve_attack` concede branch, `FatePendingDefense.conceded`) + its unit test as a forward-looking, tested seam. Did NOT remove it (would drop AC-4 coverage + break TEA's `test_concede_marks_entry_and_fills_ledger`) and did NOT invent an AC-6 protocol field (scope creep / spec change).
  - Rationale: this is a spec inconsistency (AC-4 vs AC-6), not a Dev defect — the right resolution is an SM/Architect decision to either add the defend-concession protocol field (a follow-up story) or formally defer concede-at-defend and remove the branches. Flagged for that decision, not unilaterally resolved.
  - Severity: minor (deferred)
  - Forward impact: a follow-up must wire OR remove concede-at-defend; until then `conceded` is reachable only from tests.
- **`ADR-148/149` citations left as-is (DEFERRED to an Architect/doc follow-up)**
  - Spec source: Reviewer Findings (MEDIUM doc).
  - Spec text: "author the DEFEND-barrier ADR under a free number and update citations, or drop `/149`."
  - Implementation: left the 9 files' `ADR-148/149` citations unchanged this round.
  - Rationale: authoring the DEFEND-barrier ADR is an Architect task, and mechanically rewriting 24 comments mid-rework adds churn/risk without resolving the underlying gap (the ADR still wouldn't exist). Tracked as a Delivery Finding for an Architect/doc pass.
  - Severity: minor (deferred)
  - Forward impact: doc traceability remains wrong until the ADR is authored.
- **Private dispatch-helper params left untyped (`_handle_defend`/`_finish_defense`/`_seat_player_id`)**
  - Spec source: Reviewer Findings (LOW); lang-review #3.
  - Spec text: lang-review #3 — "Internal/private helpers are exempt."
  - Implementation: kept the `_`-prefixed helpers' params untyped, matching the existing style of these private dispatch helpers; only threaded `ruleset` (also untyped) through `_finish_defense` to drop the redundant `get_ruleset_module` lookup.
  - Rationale: rule #3 explicitly exempts private helpers; annotating would require 6 new TYPE_CHECKING imports for a Low/exempt finding. Kept the rework focused on the blocking + AC fixes.
  - Severity: trivial (deferred)
  - Forward impact: none.

### Reviewer (audit — round 2)

Audit of the Dev rework deviations (`### Dev (rework — review round 1)` above):
- **Added server-side defender authorization** → ✓ ACCEPTED: correct, loud, ordered before any mutation, on the authenticated `character.core.name`; tested. Resolves the Round-1 blocker.
- **NPC server defenses tagged `role="defense"` (AC-8)** → ✓ ACCEPTED: default preserves NPC-proactive callers; ladder math untouched; tested via the production `_roll_defense`.
- **Concede-at-defend left implemented-but-unwired (DEFERRED)** → ✓ ACCEPTED: the Dev correctly declined to unilaterally remove tested code or invent an AC-6 wire; this is a genuine AC-4/AC-6 spec inconsistency for SM/Architect. Remains a non-blocking Delivery Finding.
- **`ADR-148/149` citations left as-is (DEFERRED)** → ✓ ACCEPTED: authoring the DEFEND-barrier ADR is an Architect task; mechanical comment-churn mid-rework adds risk without resolving the gap. Remains a non-blocking Delivery Finding.
- **Private-helper params left untyped (DEFERRED)** → ✓ ACCEPTED: lang-review #3 explicitly exempts private helpers.

**New undocumented item found in round 2:** the auth rejection emits no OTEL watcher event (the sibling spoof-rejection does). Severity: M, non-blocking. Logged as a Delivery Finding (round 2); recommended as the first fast-follow. Not a spec deviation — an observability completeness gap on the new guard.

## References

- **Approved Spec:** `docs/superpowers/specs/2026-06-18-fate-sealed-commit-interaction-model-design.md` — the complete sealed-commit interaction model (both proactive and defense).
- **Approved Server Plan:** `docs/superpowers/plans/2026-06-18-fate-sealed-commit-defend-server.md` — task-by-task implementation plan for the server-side work (8 tasks: protocol, ledger, OTEL, reveal+park, emit requests, defense recording, resume+walk, end-to-end wiring).
- **Related ADRs:**
  - ADR-148: Player Fate Rolls Are Physics-Is-The-Roll (proactive; live) — 126-7 implemented the proactive side.
  - ADR-149: Fate Defend Follow-up Barrier (to be authored in this story).
  - ADR-036 / ADR-129: sealed-commit turn model.
  - ADR-074: Dice Resolution Protocol (physics-is-the-roll).
  - ADR-144: Fate Core Binding Replaces the Native Ruleset.
  - ADR-107: Out-of-band aside channel (compels).
  - ADR-128: resume-safe randomness (resume-safety precedent).
- **SOUL Principles:** "The Guitar Solo," "Cost Scales with Drama," "The Zork Problem," "Bind the Ruleset, Don't Balance It."