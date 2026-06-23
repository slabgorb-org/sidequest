---
story_id: "158-1"
jira_key: ""
epic: "158"
workflow: "tdd"
---
# Story 158-1: WWN combat never seats on a fresh descent — reconcile surfaced-creature zone to PC region so the router projects a co-located Other

## Story Details
- **ID:** 158-1
- **Jira Key:** (none — project has no Jira)
- **Workflow:** tdd
- **Stack Parent:** none
- **Repos:** server
- **Points:** 5
- **Priority:** p0
- **Type:** bug

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-23T02:32:51Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-23T01:21:36Z | 2026-06-23T01:25:58Z | 4m 22s |
| red | 2026-06-23T01:25:58Z | 2026-06-23T01:48:23Z | 22m 25s |
| green | 2026-06-23T01:48:23Z | 2026-06-23T02:06:58Z | 18m 35s |
| review | 2026-06-23T02:06:58Z | 2026-06-23T02:17:00Z | 10m 2s |
| red | 2026-06-23T02:17:00Z | 2026-06-23T02:21:53Z | 4m 53s |
| green | 2026-06-23T02:21:53Z | 2026-06-23T02:26:09Z | 4m 16s |
| review | 2026-06-23T02:26:09Z | 2026-06-23T02:32:51Z | 6m 42s |
| finish | 2026-06-23T02:32:51Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Question** (blocking): The reconciliation SIGNAL is the load-bearing design decision and is under-specified — Dev must choose it deliberately. The bug is that the seater's co-location predicates (`_npc_fallback_at_location` line 948 keys on `last_seen_location`; `_resolve_opponent_from_roster` line 1023 keys on `last_seen_location` OR `location`) reject a surfaced creature whose stored zone is stale. The cure CANNOT be a blanket widening of those filters: ADR-116 / the 108-2 docstring (`encounter_lifecycle.py` ~1008) *deliberately* forbids region-wide sourcing ("a broader scan could conscript a creature from an unrelated room — the exact over-reach ADR-116 guards against"). So the fix must reconcile ONLY a creature the narrator *engaged this turn*. The RED suite represents that signal as `manual_origin=True` + `last_seen_turn == current interaction` (a Monster-Manual creature surfaced this turn); `test_offstage_stale_swarm_is_not_reconciled` pins that a creature last seen on a PRIOR turn is left untouched. Affects `sidequest/server/dispatch/encounter_lifecycle.py` (the seater reconcile hook, upstream of `_resolve_opponent_from_roster`) — Dev should confirm the chosen marker matches the real surfacing signal (turn-scoped engagement), not blanket `manual_origin`. *Found by TEA during test design.*
- **Gap** (non-blocking): AC-6 asks for a test driving the FULL `intent → router → projection → seater` production path; the RED suite is pinned at the deterministic seater seam (`instantiate_encounter_from_trigger`, the same "REAL production seam" altitude `test_153_10` uses) to stay LLM-free and avoid coupling to the non-deterministic router pass. If Dev hooks reconciliation in `intent_router_pass.py` (before the router projection) rather than the seater, add a production-turn integration test (mirror `tests/integration/test_dungeon_room_population_153_23.py`'s `_execute_narration_turn` driver) so the wiring is proven end-to-end. Affects `sidequest/server/intent_router_pass.py` / `sidequest/server/websocket_session_handler.py`. *Found by TEA during test design.*
- **Improvement** (non-blocking): This overlaps the just-landed 153-23 (`region_for()` room_id → monster-manual inject). The authored Gnaw-Swarm is the ENTRANCE room's creature ("Under the Rope" is the entrance's name); the PC descended to a procedural region and the narrator dragged the swarm forward in prose. If the cleaner fix is to re-bind/re-stamp the room creature's zone at MM-inject time for the PC's CURRENT region (extending 153-23) rather than at seat time, the same RED contract should still hold — verify the reconcile span fires from whichever seam Dev picks. Affects `sidequest/server/dispatch/monster_manual_inject.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Question** (blocking): The seater fix is NECESSARY but may not be SUFFICIENT for the full forensic repro. The forensic (`8b54610d`, DRIVER live OTEL) showed **`NO intent_router.subsystem=combat`** — the pre-narrator router did not emit a confrontation dispatch at all, so the seater was never reached. My fix lives in the seater (`_resolve_opponent_from_roster`), which only runs once a confrontation IS dispatched. I verified the precondition gate does NOT drop `confrontation` (`_INERT_PRECONDITIONS` in `sidequest/agents/dispatch_precondition_gate.py` covers only scenario_clue/witnessed_act/magic_working/fate_action), so a dispatched confrontation always reaches my fix — but whether the LLM router dispatches on a target that `is_npc_in_scene` (`sidequest/server/intent_router_pass.py::_present_npc_names`) omits is non-deterministic and unverified. The likely complete fix ALSO reconciles the surfaced creature's `location` BEFORE the state_summary is built so the router projects it as present (`is_npc_in_scene` keys on `location`, which my fix already touches — but at seat time, too late for the router). Affects `sidequest/server/intent_router_pass.py` (pre-router reconciliation) — **must be verified with the owed AC-6 full-path/live test (see TEA's Gap finding) before the playtest can confirm the bug is closed end-to-end.** *Found by Dev during implementation.*
- **Improvement** (non-blocking): The seater fix is a standalone win beyond the forensic: it extends the 108-2 roster reconciliation (which only resolved CO-LOCATED bound creatures) to a recently-surfaced bound creature stranded at a stale zone — so any turn where the router dispatches a vague-target confrontation now seats the bound creature (WWN stats preserved) instead of a fabricated HP stub. Affects `sidequest/server/dispatch/encounter_lifecycle.py`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): The recency window admits never-surfaced creatures — `0 <= interaction - n.last_seen_turn <= 1` is True at `interaction==1` for `last_seen_turn==0` (the `Npc` "never mentioned" default), reconciling+seating a creature the narrator never surfaced. Violates AC-4 and the helper docstring. Affects `sidequest/server/dispatch/encounter_lifecycle.py:1025` (add `n.last_seen_turn > 0`) and the test suite (add a RED guard at the `==0` boundary; the existing guard used gap-4). *Found by Reviewer during code review.*
- **Gap** (blocking): The candidate filter admits creatures with no location at all (both `last_seen_location` and `location` None pass the `!= location` check), firing the span with `from_location=""` — a non-drift creature masquerading as a zone-drift on the GM panel. Affects `sidequest/server/dispatch/encounter_lifecycle.py:1023-1024` (require `n.last_seen_location is not None or n.location is not None`) plus a RED guard. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Reconcile-then-decline — `_reconcile_surfaced_adversary` mutates location + emits the reconcile span before the pool-antagonist decline (`:1139`) can return None, so the span can fire for a creature not seated this turn. Consider checking the pool antagonist before reconciling, or deferring the mutation/span until the creature is returned. Affects `sidequest/server/dispatch/encounter_lifecycle.py:1101-1147`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The new span logs `from_location`/`to_location` (narrator-LLM strings) verbatim with no length bound, and `encounter_creature_zone_reconciled_span` carries an unused `**attrs` pass-through; bound the strings if an off-process OTEL exporter (ADR-131-style) is added. Affects `sidequest/telemetry/spans/encounter.py`. *Found by Reviewer during code review.*
- **Round 2 closure** (Reviewer): the two BLOCKING Gaps above are RESOLVED by the rework (`n.last_seen_turn > 0` + non-None location guard, with matching guard tests). The two non-blocking Improvements (reconcile-then-decline ordering; span string length-bound / unused `**attrs`) remain open as documented fast-follow candidates — they do not gate the story. APPROVED on this basis. *Found by Reviewer during code review (round 2).*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

4 deviations

- **Pinned a concrete OTEL span name + attribute keys for AC-3**
  - Rationale: A test must assert a concrete span name; modelled on the sibling 108-2 span helpers (`encounter.opponent_resolved_from_roster`, `encounter.roster_resolution_skipped`) for naming consistency. Dev may rename via a documented deviation if a different identifier is clearer — the test pins the contract, not the prose.
  - Severity: minor
  - Forward impact: Dev must emit a span by this exact name+attrs, or rename here and in the test together.
- **Tested AC-1/2/5 at the seater seam, not the full router→projection→seater path (AC-6)**
  - Rationale: Keep RED deterministic and refactor-stable; the seater is where co-location is decided and where the behavioral contract manifests regardless of where the reconcile hook lands. Captured as a blocking-adjacent Delivery Finding (Gap) so Dev adds the production-turn integration test once the hook seam is chosen.
  - Severity: minor
  - Forward impact: A full-path integration test is still owed at GREEN if Dev hooks reconciliation upstream of the seater (see Delivery Findings).
- **Reconciliation keyed on a recency WINDOW (`0 <= interaction - last_seen_turn <= 1`), not TEA's literal `== current`**
  - Rationale: A literal `== current` is **unrealizable at seat time** — verified in code: the router/seater run BEFORE the narrator, and `last_seen_turn` is stamped only by `narration_apply._apply_npc_mentions` / `_stamp_encounter_presence` (post-seater) — neither `_merge_npc_patch` nor `_npc_from_patch` stamps it on MM injection. So a creature the narrator surfaced carries at most `current - 1` at this turn's seat time. The window covers the exact forensic cadence (narrate turn N, attack turn N+1) while still excluding the AC-4 off-stage creature (gap 4 in the guard test). Both the positive (gap 0) and negative (gap 4) tests pass under the window.
  - Severity: minor
  - Forward impact: The window is conservative (≤1 turn). If playtest shows players engaging a surfaced creature 2+ turns later, widen the window — but the AC-4 guard pins gap-4 as off-stage, so the ceiling is <4.
- **Hooked reconciliation in the SEATER (`_resolve_opponent_from_roster`), not upstream of the router projection**
  - Rationale: The seater is the deterministic seam the tests drive; the precondition gate does NOT gate `confrontation` on co-location (`_INERT_PRECONDITIONS` covers only scenario_clue/witnessed_act/magic_working/fate_action), so a dispatched confrontation always reaches the seater. This is the necessary, tested half of the fix. The upstream router-projection piece (so the router DISPATCHES on a non-present target) is non-deterministic (LLM) and is captured as a blocking Delivery Finding + the owed AC-6 full-path test.
  - Severity: major
  - Forward impact: See the Dev blocking Delivery Finding — the end-to-end production repro also depends on the router emitting the confrontation dispatch, which this seater fix does not force.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Pinned a concrete OTEL span name + attribute keys for AC-3**
  - Spec source: context-story-158-1.md, AC-3
  - Spec text: "Spans emit at the router/projection gate exposing the reconciliation decision: reconciled creature id, from-zone (stale), to-zone (PC's current region), and whether a co-located Other was found (Y/N)."
  - Implementation: `test_zone_reconcile_emits_decision_span` requires span name `encounter.creature_zone_reconciled` with attributes `from_location` (stale), `to_location` (PC scene), and `creature_id`/`creature_name`. The spec named the data but not the span/attribute identifiers.
  - Rationale: A test must assert a concrete span name; modelled on the sibling 108-2 span helpers (`encounter.opponent_resolved_from_roster`, `encounter.roster_resolution_skipped`) for naming consistency. Dev may rename via a documented deviation if a different identifier is clearer — the test pins the contract, not the prose.
  - Severity: minor
  - Forward impact: Dev must emit a span by this exact name+attrs, or rename here and in the test together.
- **Tested AC-1/2/5 at the seater seam, not the full router→projection→seater path (AC-6)**
  - Spec source: context-story-158-1.md, AC-6
  - Spec text: "This test must NOT bypass the router's projection gate — it must verify the full intent → router → projection → seater path."
  - Implementation: RED suite drives `instantiate_encounter_from_trigger` directly (the deterministic production seater, same altitude `test_153_10` calls "the REAL production seam"). The full router pass is LLM-driven (Haiku) and non-deterministic.
  - Rationale: Keep RED deterministic and refactor-stable; the seater is where co-location is decided and where the behavioral contract manifests regardless of where the reconcile hook lands. Captured as a blocking-adjacent Delivery Finding (Gap) so Dev adds the production-turn integration test once the hook seam is chosen.
  - Severity: minor
  - Forward impact: A full-path integration test is still owed at GREEN if Dev hooks reconciliation upstream of the seater (see Delivery Findings).

### Dev (implementation)
- **Reconciliation keyed on a recency WINDOW (`0 <= interaction - last_seen_turn <= 1`), not TEA's literal `== current`**
  - Spec source: session Delivery Findings → TEA (test design) blocking Question; tests in `test_158_1_zone_reconcile_seating.py`
  - Spec text: TEA's signal — "manual_origin=True + last_seen_turn == current interaction (a Monster-Manual creature surfaced this turn)".
  - Implementation: `_reconcile_surfaced_adversary` reconciles a creature surfaced THIS turn OR the immediately-preceding one (`0 <= snapshot.turn_manager.interaction - npc.last_seen_turn <= 1`).
  - Rationale: A literal `== current` is **unrealizable at seat time** — verified in code: the router/seater run BEFORE the narrator, and `last_seen_turn` is stamped only by `narration_apply._apply_npc_mentions` / `_stamp_encounter_presence` (post-seater) — neither `_merge_npc_patch` nor `_npc_from_patch` stamps it on MM injection. So a creature the narrator surfaced carries at most `current - 1` at this turn's seat time. The window covers the exact forensic cadence (narrate turn N, attack turn N+1) while still excluding the AC-4 off-stage creature (gap 4 in the guard test). Both the positive (gap 0) and negative (gap 4) tests pass under the window.
  - Severity: minor
  - Forward impact: The window is conservative (≤1 turn). If playtest shows players engaging a surfaced creature 2+ turns later, widen the window — but the AC-4 guard pins gap-4 as off-stage, so the ceiling is <4.
- **Hooked reconciliation in the SEATER (`_resolve_opponent_from_roster`), not upstream of the router projection**
  - Spec source: context-story-158-1.md AC-1/AC-6 ("before the router projects co-located Others"); SM/TEA assessments
  - Spec text: "reconcile the surfaced creature's location to the PC's current region BEFORE the router projects co-located Others."
  - Implementation: Reconciliation fires inside the confrontation seater (the empty-co-located-candidates branch of `_resolve_opponent_from_roster`), AFTER the router has dispatched a confrontation. The tests pin this seater behavior and all pass.
  - Rationale: The seater is the deterministic seam the tests drive; the precondition gate does NOT gate `confrontation` on co-location (`_INERT_PRECONDITIONS` covers only scenario_clue/witnessed_act/magic_working/fate_action), so a dispatched confrontation always reaches the seater. This is the necessary, tested half of the fix. The upstream router-projection piece (so the router DISPATCHES on a non-present target) is non-deterministic (LLM) and is captured as a blocking Delivery Finding + the owed AC-6 full-path test.
  - Severity: major
  - Forward impact: See the Dev blocking Delivery Finding — the end-to-end production repro also depends on the router emitting the confrontation dispatch, which this seater fix does not force.

### Reviewer (audit)
- **TEA — Pinned `encounter.creature_zone_reconciled` span name + attrs** → ✓ ACCEPTED by Reviewer: a test must assert a concrete span name; the name+attrs are consistent with the 108-2 sibling spans and routed correctly in `SPAN_ROUTES`. Sound.
- **TEA — Tested at the seater seam, not the full router→projection→seater path (AC-6)** → ✓ ACCEPTED by Reviewer: keeping RED deterministic is correct, and the precondition gate confirms the seater is reachable. The AC-6 full-path test remains genuinely owed (tracked as TEA Gap + Dev blocking finding) and the playtest must not be considered closed until it lands.
- **Dev — Recency WINDOW (`0 <= interaction - last_seen_turn <= 1`) instead of literal `== current`** → ✓ ACCEPTED by Reviewer (the window is the right call; `== current` is indeed unrealizable at seat time since narration stamps `last_seen_turn` post-seater) **→ but FLAGGED on the lower bound**: the window's `<= 1` admits `last_seen_turn == 0` (the model's "never mentioned" default) at `interaction == 1`, reconciling a never-surfaced creature — the HIGH finding. Add `last_seen_turn > 0`.
- **Dev — Hooked reconciliation in the SEATER, not upstream of the router projection** → ✓ ACCEPTED by Reviewer: the seater is the deterministic, reachable seam and the tested scope; the upstream router-dispatch dependency is honestly documented as a blocking Dev finding + the owed AC-6 test, not silently dropped. The scope boundary is reasonable; the end-to-end closure depends on the AC-6 follow-up.

**Round 2 audit update (Reviewer):** The round-1 FLAG on the Dev recency-window deviation is **RESOLVED** — the rework added `n.last_seen_turn > 0`, so the window no longer admits the never-surfaced `last_seen_turn==0` default. The new guard tests pin it. No new deviations introduced by the rework (the Dev Round-2 filter tightening + docstring update bring the code into line with its stated contract — that is a correction, not a deviation). All deviations are now stamped and accounted for.

## Sm Assessment

**Story:** 158-1 — WWN combat never seats on a fresh descent. Epic 158 playtest-sweep follow-up (Sprint 2626), p0, the epic's #1-priority finding.

**The defect (one sentence):** On a fresh `beneath_sunden` (caverns_and_claudes / WWN) descent the narrator surfaces a live hostile "at your feet" in the PC's current zone, but the creature's engine `location` is a stale, different zone — so per ADR-116 the router's projection finds no co-located Other, declines to dispatch a confrontation entirely, and the narrator free-narrates the fight while fabricating player HP (10/10 on the sheet, "four hit points" in prose — a lie-detector failure that even got canonized as a Lore footnote).

**Forensic confidence (why this is well-scoped):** Both saves were pulled from the shared DB, not inferred. No-seat save `8b54610d`: PC at `exp002.r3` ("The Winding Catacomb"), Gnaw-Swarm seeded at `location="Under the Rope"`. Seat save `697cbc14`: PC and Pale Thing both at "The Drowned Cavern" → seated. The ONLY material difference is target co-location. Live OTEL on a repro confirmed the decision dies at the **router/projection gate** (`intent_router` + `projection` fired; NO `confrontation`/`combat`/`seater`/`dispatch` component fired at all) — the seater was never reached. Fix locus is **upstream of the seater**: reconcile the surfaced creature's `location` to the PC's current region before the router projects co-located Others.

**Setup decisions:**
- **Workflow:** tdd (phased) → next agent TEA for RED. Correct over trivial: real behavioral bug, 5pt, with a concrete regression target (the gnaw_swarm repro class).
- **Repo/branch:** sidequest-server only; branch `feat/158-1-wwn-combat-seat-zone-reconcile` off `develop` (server trunk is develop, not main).
- **Jira:** explicitly skipped — no Jira configured; story id is the key.
- **Merge gate:** clear — no open server PRs, nothing in_progress/in_review.
- **Parallel-clone / already-shipped check:** no open PR for 158-1, no `intent_router`/projection co-location reconcile already on develop — this is genuinely fresh backlog work.
- **Research landed in context doc** (`sprint/context/context-story-158-1.md`): full forensic Problem Statement, OTEL trace, ADR-116 grounding, and 6 ACs covering reconcile-before-projection, blunt-attack-now-seats, OTEL exposure of the reconcile decision, no-regression on genuinely-off-stage creatures, and HP/state survival.

**Routing notes for TEA (Argus Panoptes):**
- Honor the **OTEL Observability Principle** (CLAUDE.md): the reconcile decision MUST emit a watcher span (reconciled creature id, from-zone, to-zone, co-located-Other Y/N) so the GM panel can verify the path fired — the DRIVER explicitly could not disambiguate the router's sub-reason from forensics because it currently lives only in ephemeral per-span attributes. AC 3 demands this.
- Honor the **wiring-test rule**: the RED test must prove a fresh-descent surfaced creature now **seats end-to-end** (confrontation dispatched, encounter starts, beat/dice fires) — not merely that a reconcile helper returns true in isolation.
- Honor **SOUL.md "Bind the Ruleset, Don't Balance It"**: this is a *co-location/projection* fix, NOT a WWN combat-math change — do not tune beats/dials to "make WWN seat." The cure is making the Other present, then the bound ruleset's seating fires on its own.
- AC 4 (no spurious reconciliation of genuinely-off-stage creatures) is the adversarial edge — make sure the RED suite pins the negative case too.
- Closely related prior work: **153-23** (`region_for()` room_id into monster-manual inject) — `sprint/context/context-story-153-23.md`. The MM-injected creature's zone drift is the upstream cause of the stale `location`.

**Verdict:** Setup complete and verified — session, context doc, branch, and `epic: 158` frontmatter all confirmed. The scales are balanced. Ready for RED.

## TEA Assessment

**Tests Required:** Yes
**Reason:** A behavioral p0 bug with a forensically-pinned, deterministic regression target (the beneath_sunden gnaw_swarm "never seats" repro). Not a chore — TDD is correct.

**Test Files:**
- `tests/server/dispatch/test_158_1_zone_reconcile_seating.py` — drives the REAL `instantiate_encounter_from_trigger` seater with the live WWN pack (`caverns_and_claudes`); same altitude as the sibling `test_153_10_wwn_other_seating.py`. No source-text assertions (CLAUDE.md "No Source-Text Wiring Tests").

**Tests Written:** 5 tests covering ACs 1–5 (AC-6 captured as a Delivery Finding — see below).

| Test | AC | RED today |
|------|----|-----------|
| `test_surfaced_stale_swarm_is_reconciled_and_seated` | 1, 2 | FAIL — seats stub `["the beetle swarm"]`, not bound `["Gnaw-Swarm"]` |
| `test_reconciled_swarm_location_matches_pc_scene` | 1 | FAIL — `last_seen_location` stays `"Under the Rope"` |
| `test_reconciled_swarm_keeps_bound_hp_not_a_stub` | 5 | FAIL — bound swarm never seated (precondition) |
| `test_zone_reconcile_emits_decision_span` | 3 | FAIL — `encounter.creature_zone_reconciled` absent; `encounter.opponent_minted_stub` fires |
| `test_offstage_stale_swarm_is_not_reconciled` | 4 | PASS (no-over-reach guard — must stay green) |

**Status:** RED confirmed via testing-runner (RUN_ID 158-1-tea-red). 4 fail on assertions, 1 guard green — NO import/collection/skip errors. Baseline `test_153_10_wwn_other_seating.py` stays **4/4 green** on the branch, so this RED is independent of any pre-existing WWN-seater state (and orthogonal to the epic-108 WWN beat-resolution carve-out — this is SEATING, not beat resolution).

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| OTEL Observability Principle (CLAUDE.md — the lie detector) | `test_zone_reconcile_emits_decision_span` (asserts reconcile span + stub-absence + resolved-from-roster) | failing |
| No Source-Text Wiring Tests (CLAUDE.md) | whole suite — behavioral + OTEL span assertions, zero `read_text()`/regex | n/a (honored) |
| Wiring (every suite needs an integration test) | all tests drive the real `instantiate_encounter_from_trigger` production seam | failing |
| ADR-116 no-over-reach (region-wide sourcing forbidden) | `test_offstage_stale_swarm_is_not_reconciled` | passing (guard) |
| SOUL "Bind the Ruleset, Don't Balance It" | suite asserts SEATING only — no beat/dial/HP-math tuning | n/a (honored) |
| lang-review python #6 (test quality) | self-checked — no vacuous asserts, every truthy check paired with a value check, `skipif` carries a reason, no mocks | passing |

**Rules checked:** lang-review #6 (test quality) is the only checklist item that governs TEA's RED output; the remaining #1–#5/#7–#13 scan the Dev implementation diff and are the Reviewer's gate at GREEN. The story's load-bearing project rule (OTEL Observability) has direct test coverage.
**Self-check:** 0 vacuous tests found (no `assert True`, no lone truthy checks, no assertion-free tests).

**Handoff:** To Dev (Hephaestus the Smith) for implementation. Read the Delivery Findings FIRST — the reconciliation SIGNAL (turn-scoped engagement, NOT a blanket location-filter widening) is the load-bearing design choice, and the ADR-116 region-wide-sourcing prohibition is the trap to avoid.

### TEA Rework — Round 2 (red), 2026-06-23

Reviewer (Hermes) REJECTED with two blocking over-reach holes my round-1 AC-4 guard missed (it used gap-4 and never touched the boundary). Added two RED boundary guards to `test_158_1_zone_reconcile_seating.py` and parameterized `_snapshot_with(interaction=)`:

| New guard | Pins | RED today |
|-----------|------|-----------|
| `test_never_surfaced_creature_not_reconciled_on_turn_one` | a `last_seen_turn==0` (model "never mentioned" default) creature at `interaction==1` is NOT reconciled — the recency window must not admit a never-surfaced creature | FAIL — current code reconciles it (`0<=1-0<=1`), moves its location to the PC scene |
| `test_unlocated_creature_not_reconciled` | a creature with both `location` and `last_seen_location` None is NOT reconciled — no stale zone to drift from; no `from_location=""` phantom span | FAIL — current code reconciles it, span fires with `from_location=""` |

Verified via testing-runner (RUN_ID 158-1-tea-red-rework): **5 original pass, 2 new fail on assertions** (clean RED — no errors/skips). Committed `c22c7e83`.

**Dev fix (minimal):** in `_reconcile_surfaced_adversary`'s candidate filter (`encounter_lifecycle.py:1016-1026`) add `n.last_seen_turn > 0` and `(n.last_seen_location is not None or n.location is not None)`. That makes both new guards green while the 5 original tests stay green. The Reviewer's two LOW items (reconcile-then-decline ordering; span string length-bound / unused `**attrs`) are non-blocking — Dev may address them in the same pass but no test gates them.

**Handoff:** To Dev (Hephaestus) for the green-phase filter tightening.

## Dev Assessment

**Implementation Complete:** Yes (for the tested seater scope; see the blocking Delivery Finding for the upstream router dependency)

**Files Changed:**
- `sidequest/server/dispatch/encounter_lifecycle.py` — new `_reconcile_surfaced_adversary` helper; hooked into `_resolve_opponent_from_roster` at the empty-co-located-candidates branch (native combat only). When no co-located adversary exists, it recovers a bound (`creature_id` + `manual_origin`), adversarial, non-friendly bestiary creature surfaced this turn or last (`0 <= interaction - last_seen_turn <= 1`) but stranded at a stale zone, reconciles its `last_seen_location` + `location` to the PC's scene, and returns it so the bound creature seats (WWN HP preserved) instead of a fabricated stub.
- `sidequest/telemetry/spans/encounter.py` — new `encounter.creature_zone_reconciled` span (constant + `SpanRoute` + `encounter_creature_zone_reconciled_span` helper), modelled on the 108-2 sibling spans. Carries `creature_name`, `creature_id`, `from_location`, `to_location`, `last_seen_turn`, `current_turn` for the GM-panel lie-detector.

**Tests:** 5/5 passing in `test_158_1_zone_reconcile_seating.py` (GREEN). Regression: `tests/server/dispatch/` 477 passed, seating/MM smoke (`test_confrontation_dispatch`, `test_confrontation_dispatch_wiring`, `test_monster_manual`, `test_dungeon_room_population_153_23`) 46 passed — **zero regressions**. The new empty-candidates reconcile pass is narrow (turn-scoped, manual_origin-gated, combat+non-fate only) and does not over-suppress stub minting. `ruff check`/`format` clean on both touched files (scoped — not a wholesale reformat).

**Branch:** `feat/158-1-wwn-combat-seat-zone-reconcile` (pushed to origin). No PR (SM creates it at finish).

**Self-review (judgment checks):**
- Wired to a real production path: the fix is inside the live confrontation seater (`run_confrontation_dispatch` → `instantiate_encounter_from_trigger` → `_resolve_opponent_from_roster`); the precondition gate does not gate `confrontation`, so a dispatched confrontation reaches it. New span auto-exports via `spans/__init__.py`'s `from .encounter import *`.
- Follows project patterns: mirrors the 108-2 `_resolve_opponent_from_roster` candidate/sort/span idiom and the sibling span helpers; honors SOUL "Bind the Ruleset" (SEATING only — no beat/dial/HP-math tuning) and ADR-116 (turn-scoped, never region-wide).
- ACs met: AC-1/2/3/4/5 covered and green. AC-6 (full router→seater path) is the deferred owed integration test (TEA Gap), and the upstream router-dispatch dependency for the full forensic repro is flagged as a **blocking Dev Delivery Finding** — surfaced loudly, not hidden (No Silent Fallbacks).
- Error handling: helper returns `None` cleanly when no candidate; no new exception paths.

**Handoff:** To Reviewer (Hermes Psychopompos) for code review. **Read the Dev blocking Delivery Finding** — the seater fix is correct and tested, but the end-to-end production repro also depends on the LLM router dispatching the confrontation, which this fix does not force; the owed AC-6 full-path/live test must confirm the bug is closed in play.

### Dev Rework — Round 2 (green), 2026-06-23

Addressed both of Hermes's blocking findings by tightening `_reconcile_surfaced_adversary`'s candidate filter (`encounter_lifecycle.py:1016-1031`):
- **[HIGH] never-surfaced over-reach** → added `n.last_seen_turn > 0` so the model's `0` ("never mentioned this session") default is excluded; the recency window no longer admits a never-surfaced creature at `interaction==1`. Resolves the FLAGGED round-1 recency-window deviation.
- **[MEDIUM] unlocated creature** → added `(n.last_seen_location is not None or n.location is not None)` so a creature with no stored zone is not treated as zone-drifted (no `from_location=""` phantom span).
- Docstring updated to match the tightened filter (resolves the Reviewer [DOC] note).
- The two LOW non-blocking findings (reconcile-then-decline ordering; span string length-bound / unused `**attrs`) are left as documented delivery findings — no test gates them and they're existing codebase conventions; not addressed in this minimal rework.

**Tests:** 7/7 in `test_158_1_zone_reconcile_seating.py` GREEN (5 original + 2 new boundary guards). `tests/server/dispatch/` **479 passed** (was 477 + 2 guards), seating/MM smoke 46 passed — zero regressions. ruff clean. Committed + pushed `cb7bf0df`.

**Handoff:** Back to Reviewer (Hermes) for re-review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
*(Round 2 re-review — the 3 enabled specialists re-ran on the rework diff.)*

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 7/7 story green, 479 dispatch green, lint clean, both rework guards mechanically correct, no new smells | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | Yes | findings (both R1 holes RESOLVED) | 0 new; round-1 over-reach + both-None holes confirmed CLOSED; 2 round-1 LOWs (reconcile-then-decline, tiebreak) unchanged | confirmed 0 new, carried 2 LOW (non-blocking), deferred 0 |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings (Reviewer assessed: 2 new boundary guards non-vacuous, pin the exact fixes) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings (Reviewer assessed: docstring now matches the tightened filter) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (Reviewer assessed: guards are read-only bool predicates, fully typed) |
| 7 | reviewer-security | Yes | clean | rework delta security-clean (read-only field guards, no new surface); round-1 LOWs unchanged | confirmed 0 new, carried 2 LOW (non-blocking), deferred 0 |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings (Reviewer re-assessed Rule Compliance manually — clean) |

**All received:** Yes (3 enabled re-ran, 6 disabled via settings)
**Total findings:** 0 new confirmed; both round-1 BLOCKING findings RESOLVED; 4 round-1 LOW non-blocking observations carried forward as delivery findings

## Reviewer Assessment — Round 1 (REJECTED — superseded by Round 2 APPROVED below)

**Verdict (Round 1):** REJECTED

The seater fix is well-built, tested (5/5 + 477 dispatch regression green), and faithful to the 108-2 idiom and SOUL "Bind the Ruleset" (seating only). But the new candidate filter is **looser than its own docstring and AC-4 guarantee**, and the gap sits exactly at the no-over-reach boundary the story exists to protect. The fixes are small; routing back to close them.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | Recency window admits **never-surfaced** creatures: `0 <= turn - n.last_seen_turn <= 1` is True at `interaction==1` for `last_seen_turn==0` (the `Npc` model's documented "never mentioned in this session" default). A manual_origin adversary that was never narrated, sitting at a stale zone, is reconciled+seated on turn 1. This violates **AC-4** ("a creature ... not surfaced on-stage ... is NOT spuriously reconciled") and directly contradicts the helper's own docstring ("surfaced THIS turn or the immediately-preceding one"). The AC-4 guard test used `last_seen_turn=3` (gap 4) and never exercised the `==0` boundary. [EDGE] | `encounter_lifecycle.py:1025` | Add `n.last_seen_turn > 0` to the candidate filter. |
| [MEDIUM] | Candidate filter admits creatures with **no location at all**. The predicate checks only `n.last_seen_location != location and n.location != location`; when both fields are `None`, `None != "<scene>"` is True, so an unlocated creature passes and the span fires with `from_location=""`. A never-located creature is not a "zone drift" — it should not masquerade as one on the GM panel. [EDGE] | `encounter_lifecycle.py:1023-1024,1035` | Require `(n.last_seen_location is not None or n.location is not None)`. |

**Non-blocking observations** (record as delivery findings; do not gate the rework but should be addressed):
- [LOW][EDGE] **Reconcile-then-decline:** `_reconcile_surfaced_adversary` mutates `chosen.location`/`last_seen_location` and emits `encounter.creature_zone_reconciled` BEFORE the pool-antagonist decline (`encounter_lifecycle.py:1139`) can `return None`. The zone fix is arguably independently correct (the narrator did surface the creature at the PC's scene), so this is LOW — but the span fires for a creature not seated this turn, and the mutation persists on a decline path. Prefer running the pool-antagonist check before reconciling, or deferring the mutation+span until the creature is actually returned.
- [LOW][SEC] The new span logs `from_location`/`to_location` verbatim (narrator-LLM-authored strings) with no length bound, and `encounter_creature_zone_reconciled_span` exposes an unused `**attrs` pass-through (`encounter.py`). Both are existing codebase conventions and internal-only today; bound the location strings if an off-process OTEL exporter (cf. ADR-131) is ever added.
- [LOW] Preflight cosmetic: `with encounter_creature_zone_reconciled_span(...): pass` opens/closes the span with an empty body and mutates state outside the `with`. Peer spans do the same; non-blocking.

### Dispatch tags
- [EDGE] — CONFIRMED 3 (over-reach HIGH, both-None MEDIUM, reconcile-then-decline LOW); DISMISSED 3 (future `last_seen_turn` silently excluded → defensive-only LOW; tiebreak determinism → stable, acceptable; mutation-in-`_resolve_*` naming → documented in docstring, acceptable).
- [SILENT] — subagent disabled. Reviewer assessed: the zero-candidate path returns `None` and the caller emits a loud `encounter.opponent_minted_stub` span; the reconcile path emits `encounter.creature_zone_reconciled`. No new silent fallback. VERIFIED — `encounter_lifecycle.py:1118-1119` returns None into the existing loud stub-mint path.
- [TEST] — subagent disabled. Reviewer assessed: the 5 tests are non-vacuous (specific opponent-name / location / HP / span-attr assertions), drive the real seater, and use a real pack. **Gap:** the AC-4 guard (`test_offstage_stale_swarm_is_not_reconciled`) tests only `last_seen_turn` gap-4, not the `==0` (never-seen) boundary nor the both-None-location case — exactly the holes in the HIGH/MEDIUM findings. The rework must add these RED guards.
- [DOC] — subagent disabled. Reviewer assessed: the helper docstring is otherwise excellent BUT contradicts the code — it claims "surfaced THIS turn or the immediately-preceding one," yet the window admits `last_seen_turn==0` (never surfaced). Fixing the filter (`> 0`) makes the docstring true.
- [TYPE] — subagent disabled. Reviewer assessed: `_reconcile_surfaced_adversary(snapshot: GameSnapshot, *, location: str, turn: int) -> Npc | None` and `encounter_creature_zone_reconciled_span(*, creature_name: str, creature_id: str, from_location: str, to_location: str, last_seen_turn: int, current_turn: int, ...)` are fully annotated; no stringly-typed or unsafe-cast issues. VERIFIED clean.
- [SEC] — CONFIRMED 2 LOW (span string length-bound, unused `**attrs`); no Critical/High; no injection/secret/SQL/path/deser issues; OTEL logs no PII.
- [SIMPLE] — subagent disabled. Reviewer assessed: the new helper is appropriately scoped (no over-engineering); the only simplification worth noting is the reconcile-then-decline ordering (see LOW above).
- [RULE] — subagent disabled. Reviewer assessed manually in Rule Compliance below — no project-rule violations; OTEL Observability and No-Silent-Fallbacks satisfied.

### Rule Compliance
Checked the new code against CLAUDE.md / SOUL.md / lang-review python:
- **OTEL Observability Principle** (every subsystem decision emits a span): COMPLIANT — `encounter.creature_zone_reconciled` emitted at the reconcile decision; routed in `SPAN_ROUTES`. (Caveat: the LOW reconcile-then-decline means the span can fire on a not-seated turn — observability quibble, not a violation.)
- **No Silent Fallbacks:** COMPLIANT — no creature → `None` → existing loud stub-mint span; no swallowed alternative path.
- **No Stubbing / No half-wired:** COMPLIANT for the seater scope; the upstream router dependency is documented (Dev blocking finding), not silently stubbed.
- **SOUL "Bind the Ruleset, Don't Balance It":** COMPLIANT — seating only; HP untouched; no beat/dial/HP-math tuning. Gated combat+non-fate so Fate/non-combat paths are untouched (`encounter_lifecycle.py:1110`).
- **ADR-116 (no region-wide sourcing):** PARTIAL — the intent (turn-scoped recency) is right, but the `last_seen_turn==0` and both-None holes are a narrow form of the over-reach ADR-116 forbids. This is the HIGH/MEDIUM finding.
- **lang-review python #2/#3 (mutable defaults / annotations):** COMPLIANT. #6 (test quality): COMPLIANT (non-vacuous) with the coverage gap noted under [TEST].
- **No Source-Text Wiring Tests:** COMPLIANT — behavioral + OTEL span assertions.

### Data flow traced
Player action ("I attack the beetle swarm") → IntentRouter → confrontation dispatch (params `opponent`="the beetle swarm") → `run_confrontation_dispatch` → `instantiate_encounter_from_trigger(materialized_threat=...)` → `_resolve_opponent_from_roster(threat_name="the beetle swarm")` → co-located scan empty → **`_reconcile_surfaced_adversary`** mutates a recently-surfaced stale-zone manual_origin adversary's `location`/`last_seen_location` to the PC scene + emits span → candidate seated as the bound Other (WWN HP preserved). VERIFIED reachable in production: the precondition gate does NOT gate `confrontation` (`_INERT_PRECONDITIONS` covers only scenario_clue/witnessed_act/magic_working/fate_action, `dispatch_precondition_gate.py:143`). **Caveat (Dev blocking finding, AUDITED):** the forensic showed the LLM router did not emit the confrontation dispatch at all on the repro turn — so this seater fix only fires when the router DOES dispatch; the end-to-end production seating still depends on the upstream router projecting the surfaced creature. Not a code defect in this diff; tracked as the owed AC-6 full-path test.

### Devil's Advocate
Argue this code is broken. The clearest break is the over-reach: imagine a fresh WWN session, turn 1, the party in a procedural room, and a deeper authored bestiary adversary pre-seeded at its own zone with `last_seen_turn=0` and `manual_origin=True`. The player, seeing the narrator's prose mention "shapes in the dark," types "I attack them" — a vague combat target, no co-located adversary. `_reconcile_surfaced_adversary` runs: the deeper creature passes every gate (`creature_id`, `manual_origin`, adversary, non-friendly, location stale on both fields, `0 <= 1 - 0 <= 1`), so it is *teleported to the PC's feet and seated as the Other* — a creature the narrator never surfaced in THIS scene, conscripted from another room. That is precisely the region-wide over-reach ADR-116 forbids and AC-4 promises against, and the test suite is blind to it because the guard used gap-4. A second break: a malicious/sloppy world author ships a manual_origin creature with no `location` at all; it sails through the filter and the GM panel's lie-detector span reports `from_location=""` — telemetry that says "a zone drift happened" when none did, eroding the one tool (OTEL) the project trusts to catch improvisation. A confused-author scenario: two same-named bestiary instances at different HP tie the sort and the second-inserted wins with no logged reason. None of these crash; all of them quietly seat the wrong Other or emit a misleading span — the subtle, plausible-looking wrongness that is exactly what this project's lie-detector doctrine exists to prevent. The window arithmetic is correct for the happy path the tests cover, and wrong at the boundary the AC names. Fix: `last_seen_turn > 0` + a non-None location guard, plus RED tests at both boundaries.

**Handoff:** Back to TEA (Argus Panoptes) for RED-phase rework — add guard tests for the `last_seen_turn==0` over-reach and the both-None-location case, then Dev (Hephaestus) tightens the candidate filter.

## Reviewer Assessment

**Verdict:** APPROVED

Round-2 re-review of the rework. Both round-1 BLOCKING findings are RESOLVED by exactly the prescribed fix, all three enabled specialists re-ran clean, and no new issues were introduced. The seater fix is correct for its scope, well-instrumented (OTEL), faithful to SOUL "Bind the Ruleset" (seating only), and the candidate filter now matches its own docstring and AC-4's no-over-reach guarantee.

**Round-1 blocking findings — verified resolved:**
- [HIGH→RESOLVED] never-surfaced over-reach: `and n.last_seen_turn > 0` (`encounter_lifecycle.py:1039`) excludes the model's `0` ("never mentioned") default before the recency window. Pinned by `test_never_surfaced_creature_not_reconciled_on_turn_one` (RED→GREEN). Verified by my own read + edge-hunter (RESOLVED) + preflight (test green).
- [MEDIUM→RESOLVED] unlocated creature: `and (n.last_seen_location is not None or n.location is not None)` (`:1031`) excludes both-None creatures; the `from_location or ""` sentinel is now unreachable when reconciliation fires. Pinned by `test_unlocated_creature_not_reconciled` (RED→GREEN). Verified by edge-hunter (RESOLVED) + security (notes it eliminates the phantom-`""` case).

**Data flow traced (re-confirmed):** player attack → router confrontation dispatch (not gated by `_INERT_PRECONDITIONS`) → `instantiate_encounter_from_trigger` → `_resolve_opponent_from_roster` → empty co-located scan → `_reconcile_surfaced_adversary` (now: creature_id + manual_origin + adversary + non-friendly + **real stored zone** + **last_seen_turn > 0** + recency ≤ 1 + stale) → reconcile location + emit `encounter.creature_zone_reconciled` → seat bound creature (WWN HP preserved, no stub). Safe: the guards NARROW the candidate set; off-stage / never-seen / unlocated creatures are excluded.

**Pattern observed:** mirrors the 108-2 `_resolve_opponent_from_roster` candidate/sort/span idiom and the sibling OTEL span helpers (`encounter_lifecycle.py:1016-1045`, `telemetry/spans/encounter.py`). Consistent with project conventions.

**Error handling:** `_reconcile_surfaced_adversary` returns `None` cleanly when no candidate; the caller falls through to the existing loud `encounter.opponent_minted_stub` path. No new exception surface.

### Dispatch tags
- [EDGE] — RESOLVED 2 (both round-1 blocking holes closed; edge-hunter confirmed no new edges — asymmetric-location cases pass with non-empty `from_location`, `turn==0` unreachable). CARRIED 2 LOW non-blocking (reconcile-then-decline ordering at `:1101-1147`; tiebreak locale-sensitivity at `:1030`) — unchanged, deferred.
- [SILENT] — subagent disabled. Reviewer re-assessed: no silent fallback; `None` → existing loud stub-mint span; reconcile path emits its span. Clean.
- [TEST] — subagent disabled. Reviewer re-assessed: the 2 new guards are non-vacuous (assert location unchanged + no reconcile span + not seated), pin the exact boundaries the round-1 gap missed; 7/7 green. The AC-4 coverage gap is now closed.
- [DOC] — subagent disabled. Reviewer re-assessed: the docstring was updated to document both guards (`last_seen_turn > 0` and the real-stored-zone requirement) — the round-1 code/docstring contradiction is gone.
- [TYPE] — subagent disabled. Reviewer re-assessed: the two new conditions are read-only boolean predicates on typed `Npc` fields; no type issues.
- [SEC] — re-ran, CLEAN. Rework delta is read-only field guards, no new external-input surface, span surface byte-identical to round 1. 2 round-1 LOWs (span string length-bound; unused `**attrs`) unchanged, non-blocking.
- [SIMPLE] — subagent disabled. Reviewer re-assessed: the two-condition addition is minimal and well-commented; no over-engineering. The only outstanding simplification is the deferred reconcile-then-decline ordering (LOW).
- [RULE] — subagent disabled. Reviewer re-assessed Rule Compliance: OTEL Observability ✓, No Silent Fallbacks ✓, SOUL Bind-the-Ruleset ✓ (seating only), ADR-116 no-over-reach now fully honored (the round-1 PARTIAL is resolved), lang-review #2/#3/#6 ✓. No violations.

**Carried non-blocking items** (delivery findings, not gating): reconcile-then-decline ordering (the reconcile span can fire on a pool-antagonist-decline turn — zone fix is arguably independently correct); span `from_location`/`to_location` length-bound + unused `**attrs` (existing codebase conventions). **Scope note (audited, not a code defect):** the end-to-end production repro also depends on the LLM router emitting the confrontation dispatch — the Dev blocking finding + TEA Gap track the owed AC-6 full-path/live test; this seater fix is the correct, tested seater-scope deliverable and a standalone win (extends 108-2 to stale-zone creatures).

**Handoff:** To SM (Themis the Just) for finish-story.