---
story_id: "152-5"
jira_key: ""
epic: "152"
workflow: "tdd"
---
# Story 152-5: [BUG] MP WN-round wire: 2nd commit misresolves to the 1st PC's seat (round never fires) + non-hermetic narrator transport on the sealed-commit handler path — unskip test_mp_wire_first_commit_seals_second_commit_fires_the_round

## Story Details
- **ID:** 152-5
- **Jira Key:** (none — orchestrator YAML tracking)
- **Workflow:** tdd
- **Stack Parent:** none
- **Type:** bug
- **Points:** 3
- **Priority:** p2

## Story Summary

Multiplayer WN-round wiring test is currently skipped (`@pytest.mark.skip(reason=_MP_WIRE_BLOCKED)`). Two latent roots block the unskip:

1. **2nd MP DICE_THROW commit misresolves to 1st PC's seat:** The sealed-commit barrier never closes, round never fires. Root: `sidequest-server/sidequest/handlers/dice_throw.py` reads `snapshot.player_seats` mapping `player_id→PC`, but the 2nd commit carries a different player_id than the 1st, causing seat resolution to look up the wrong PC.

2. **Non-hermetic narrator transport on sealed-commit handler path:** The wire path reaches the real SDK narrator transport on the sealed-commit handler, violating test hermiticity.

**Test location:** `sidequest-server/tests/integration/test_102_4_wn_round_wire_wiring.py:190` (`test_mp_wire_first_commit_seals_second_commit_fires_the_round`)

**Repo:** `sidequest-server` (server only, 3 pts)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-20T23:10:11Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-20T22:15:50Z | 2026-06-20T22:19:36Z | 3m 46s |
| red | 2026-06-20T22:19:36Z | - | - |

## Sm Assessment

**Routing:** tdd (phased) → next phase **red**, next agent **TEA (Fezzik)**.

**Why this is real, not stale (premise verified):** I read the live skipped test
(`tests/integration/test_102_4_wn_round_wire_wiring.py:188-257`) and its quarantine
constants (`_MP_WIRE_BLOCKED`, lines 56-67). The skip is current and the two roots are
documented in-code by the author who quarantined them — this is NOT a stale-premise bug.
The story explicitly sits on the now-complete single-player WN round (152-1/-2/-3 done;
152-4 canceled-stale), and the test only became reachable once the `committed_blow→attack`
swap let the first commit seal. The premise holds.

**Two roots (both in `sidequest/handlers/dice_throw.py` blast radius):**
1. 2nd MP commit (`player-2`/"Vex Calder") misresolves to the 1st PC's seat ("'Rux' has
   already committed") → sealed-commit barrier never closes → round never fires. Production
   MP seat resolution maps `player_id → PC` via `snapshot.player_seats`.
2. The sealed-commit handler path reaches the real `claude-agent-sdk` transport despite the
   stubbed `run_narration_turn` — non-hermetic. Needs an injectable narrator seam matching
   how the solo wire tests already isolate it.

**Deliverable:** unskip + green `test_mp_wire_first_commit_seals_second_commit_fires_the_round`
without regressing the solo wire tests in the same file. Full ACs and span-level expectations
are in `sprint/context/context-story-152-5.md`.

**Guardrails for TEA/Dev:** ADR-143 — fix the seat/wire plumbing only; do NOT reintroduce
native beat/dial scaffolding to "make MP work." Keep the action allowlist closed and the
`isinstance(WithoutNumberRulesetModule)` synthesis gate intact. OTEL spans are the source of
truth — verify the barrier/round via `wwn.round.committed`/`wwn.round.resolved`/
`encounter.opponent_attack_resolved`, never narration prose. Gate on the full server suite
with content, not a scoped subset.

## TEA Assessment

**Tests Required:** Yes (the deliverable IS the test) — but the RED phase overturned the story's premise.

**Phase:** finish → **finding: this is test-debt, not a production bug.** Both quarantined roots
are test-construction. **Zero production code changed.** The corrected test passes against
unchanged production and is hermetic.

**What I did (systematic-debugging, measure-don't-assert):**
1. Unskipped the test as-is, ran it → captured the real failure (not assumed):
   - `dice_throw.py:94 dice.throw.player_id_spoof_rejected inbound=player-2 authenticated=player-1`
   - `dice_throw.py:353 dice.dispatch_error error='Rux' has already committed a Main Action this round`
   - round never fires → `wwn.round.committed/resolved` absent → assertion fails (root 1)
   - `sidecar_extractor.py:245 ... Test reached the REAL claude-agent-sdk query() transport
     without installing a fake — server tests must be hermetic` (root 2)
2. Traced both roots to production code and the test factory.

**Root 1 — seat misresolution is CORRECT production behavior (ADR-119 / 118-9).**
`dice_throw.py:91` resolves the rolling PC from `sd.player_id` (the server-authenticated,
per-socket identity) as the SOLE source; an inbound `msg.player_id` that disagrees is a
*rejected spoof*. The barrier (`wn_round.seal_wn_commit:81`) keys commits by `actor.name`.
The old test drove BOTH commits through ONE handler (`sd.player_id="player-1"`), so the
second (`player-2`) was rejected as a spoof and re-resolved to "Rux" → double-seal → round
never fires. Real MP gives each player its OWN socket/`sd.player_id` while SHARING the room
snapshot/barrier (factory `existing_room=` path, `tests/conftest.py:526-556`). **Fix = two
handlers sharing one room (the canonical `test_merged_mp_emitter_projection.py:302` pattern),
each with its own authenticated `sd.player_id`.** No production change.

**Root 2 — the non-hermetic call is the SIDECAR EXTRACTOR, not the narrator.**
`run_narration_turn` IS stubbed; the leak is the post-narration sidecar-extraction watcher
(`websocket_session_handler.py:1161` → `run_sidecar_extraction_watcher` → live
`build_sidecar_extractor_llm` → real `claude-agent-sdk query()`). In production it SHOULD
call the real SDK; its fail-loud guard is the correct No-Silent-Fallbacks signal that a
**test** must install a fake. **Fix = stub `run_sidecar_extraction_watcher` (test-only).**
No production change.

**Test Files:**
- `tests/integration/test_102_4_wn_round_wire_wiring.py` — rewrote
  `test_mp_wire_first_commit_seals_second_commit_fires_the_round` to the two-handler
  shared-room MP pattern + sidecar-watcher stub; unskipped; removed the now-dead
  `_MP_WIRE_BLOCKED` constant (delete-dead-code rule).

**Status:** **GREEN already** — `1 passed, 1 skipped` (the unrelated `_OPPONENT_ATTACK_BLOCKED`
solo test stays skipped — out of scope). `ruff check` clean; `ruff format` applied.
No regression in the file. **There is no production implementation for Dev** — production
seat resolution (ADR-119) and the sidecar hermeticity guard are both validated correct.

**Reconciliation with the prior in-code note ("not a test-debt edit"):** consistent, not
contradicted. The note asked for a *Dev investigation* and warned it was "not a *pure-edit*
test-debt" (i.e., not a one-line unskip). Correct — the fix is a substantive test rewrite
(two-handler + sidecar stub), and the investigation it asked for is what concluded "test
construction, production correct."

**Self-check:** every assertion is meaningful (span presence/absence + exact resolved-count).
No vacuous assertions.

**Recommended routing:** see the routing question posed to the user. Because there is no
production change, the GREEN/Dev phase has nothing to implement; the corrected test should
go to the Reviewer (validate the rewrite + the no-production-change claim) and finish.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | No (user-declined this run) | self-assessed | none | Reviewer ran tests/lint/format directly at `da7047dd`: 1 passed / 1 skipped, ruff check clean, format clean, no dead refs |
| 2 | reviewer-edge-hunter | No | Skipped (disabled) | N/A | disabled via `workflow.reviewer_subagents` |
| 3 | reviewer-silent-failure-hunter | No (user-declined this run) | self-assessed | none | Reviewer assessed: sidecar-watcher stub is correct hermeticity, not masking; assertions non-vacuous |
| 4 | reviewer-test-analyzer | No | Skipped (disabled) | N/A | disabled via settings — Reviewer self-assessed test quality (test-only change) |
| 5 | reviewer-comment-analyzer | No | Skipped (disabled) | N/A | disabled via settings |
| 6 | reviewer-type-design | No | Skipped (disabled) | N/A | disabled via settings |
| 7 | reviewer-security | Yes | clean | none | confirmed ADR-119 firewall EXERCISED not bypassed; no secrets/eval/exec/unsafe-deser |
| 8 | reviewer-simplifier | No | Skipped (disabled) | N/A | disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped (disabled) | N/A | disabled via settings |

**All received:** Yes (security returned clean; preflight + silent-failure-hunter user-declined this run and self-assessed by the Reviewer; 6 disabled via settings)
**Total findings:** 0 confirmed, 0 dismissed, 1 deferred (TEA's stale-solo-test follow-up — non-blocking, out of scope)

## Reviewer Assessment

**Verdict:** APPROVED

Test-only change (one file, +111/-44) unskipping and rewriting the MP WN-round wire test. I read the full diff, independently re-ran test/lint/format at the reviewed commit (`da7047dd`), and audited the major design deviation. No rubber-stamp — observations below.

**Observations:**
- `[VERIFIED]` Tests green at the reviewed commit — evidence: `pytest tests/integration/test_102_4_wn_round_wire_wiring.py` → 1 passed, 1 skipped; `ruff check` clean; `ruff format --check` clean. Hermetic — the `sidecar_extraction.failed reason=transport` warnings present in the as-is unskip are gone.
- `[SEC]` (subagent, confirmed) ADR-119/118-9 seat-spoof firewall is correctly **exercised, not bypassed**: `handler_one`(`sd.player_id="player-1"`) ← msg `player-1`; `handler_two`(`sd.player_id="player-2"`) ← msg `player-2`. Both inbound ids MATCH their handler's authenticated identity — no disagreeing `msg.player_id` is used to "make it pass". Evidence: diff lines 119-133, 182, 192.
- `[TEST]` (Reviewer self — test_analyzer disabled) Assertions are meaningful, not vacuous: after-first asserts the **absence** of `wwn.round.committed/resolved` + `encounter.opponent_attack_resolved` (barrier open); after-second asserts the **presence** of `wwn.round.committed` + `wwn.round.resolved` AND exact `count == 1`. Self-validating on seat resolution: if both commits resolved to the same seat (the old bug) the second seal would raise "already committed" and the round would never fire — so a PASS proves the two seats resolved distinctly. Drives the real wire entry (`handle_message`) through the production dispatch→wn_round chain; OTEL spans are the source of truth, not prose. Genuine wiring test.
- `[SILENT]` (Reviewer self — silent-failure-hunter declined) The `run_sidecar_extraction_watcher` no-op stub does NOT mask a production failure: that watcher is a non-fatal post-narration shadow (caught + logged, applies nothing — ADR-150). Stubbing it is hermeticity hygiene, not error-swallowing. The min `random.randint` patch keeps the round deterministic without suppressing any asserted span.
- `[VERIFIED]` Determinism — initiative opponent=9 > pc_one=3 > pc_two=2; min rolls → "misses, nobody drops" so the round resolves exactly once with no encounter-end side-effect; `count == 1` holds. Evidence: diff lines 169-173 + final assertion.
- `[SIMPLE]` (simplifier disabled) Reviewer's own check: dead `_MP_WIRE_BLOCKED` removed; unused imports (`_State`, `make_pc`) dropped; `_room2` intentionally underscore-unused; grep confirms no leftover dead refs. Mirrors the canonical `test_merged_mp_emitter_projection.py` two-handler pattern — no over-engineering.
- `[DOC]` (comment-analyzer disabled) Reviewer's own check: the new docstring accurately describes the two-socket substrate + both roots; no stale references to the removed constant; comments match code.
- `[EDGE]` (edge-hunter disabled) Reviewer's own path check: only branch in the test body is the name-guarded `for ch in snapshot.characters` stat-set loop; both PCs are factory-seated, opponent added explicitly — no unhandled path.
- `[TYPE]` (type-design disabled) N/A — no new types/signatures; reuses existing models (`StructuredEncounter`, `EncounterActor`, `Npc`, `CreatureCore`, `InitiativeEntry`).
- `[RULE]` (rule-checker disabled) Reviewer's own rule pass — see Rule Compliance.

### Rule Compliance
- **No Silent Fallbacks (CLAUDE.md):** production path unchanged; test stubs only a non-fatal shadow watcher — compliant. ✓
- **No Stubbing (production):** no production stubs; the stub is a scoped test monkeypatch — compliant. ✓
- **Every Test Suite Needs a Wiring Test:** this IS the wiring test — `handle_message` → production dispatch → wn_round, asserted via OTEL spans. ✓
- **No Source-Text Wiring Tests (CLAUDE.md):** asserts on OTEL spans + behavior, never on source-text greps. ✓
- **OTEL is the lie detector:** barrier/round verified via `wwn.round.committed`/`wwn.round.resolved`, not narration prose. ✓
- **ADR-119 seat-spoof firewall:** exercised correctly, not weakened. ✓
- **ADR-143 (bind, don't balance):** no native beat/dial scaffolding reintroduced; no production combat-path change. ✓
- **Tests must not point at live content (memory):** `genre="heavy_metal"` is a genre-pack LOAD via the factory (the suite is `skipif` content-on-disk); PCs/opponent are synthetic, no world/save-slug fixture coupling. ✓
- **Delete dead code in the same PR:** `_MP_WIRE_BLOCKED` removed. ✓

### Devil's Advocate
Argue this is broken. (1) "The test passes because production is silently broken and the stubs hide it." Refuted: the assertions are span-presence/absence on the REAL dispatch→wn_round chain; the only thing stubbed is the narrator (`run_narration_turn`) and the non-fatal post-narration sidecar shadow — neither is on the seat-resolution or barrier path. If seat resolution were broken, the second seal would raise and `wwn.round.resolved` would be absent → FAIL. (2) "Two handlers don't really share the barrier — each could see its own snapshot, so the round fires on a 1-PC barrier coincidentally." Refuted: the `existing_room=` factory branch (`tests/conftest.py:526-556`) rebinds `sd_two` against `room.snapshot`, the SAME object as `sd_one.snapshot`; the encounter/`wn_commits` is installed once on `room.snapshot`. If they were separate, the first commit's seal wouldn't be visible to the second handler and `wn_barrier_closed` would still wait → round wouldn't fire on commit two. (3) "The reclassification hides a real MP outage." Refuted: in production each player connects on its own socket with its own Cf-Access `sd.player_id`; the only alternative 'fix' (trusting `msg.player_id`) is the exact 118-9 seat-spoof hole ADR-119 forbids. (4) "min `random.randint` makes it a fair-weather test." Partially conceded — it pins to the no-drop branch, but the assertions are about the round FIRING (spans), not damage values, so determinism is appropriate and does not hide a barrier bug. (5) "It doesn't prove the opponent strikes in MP." Conceded but out of scope — 152-5 pins the seal→fire barrier sequence; the opponent-walk ordering is the (separate, still-skipped) solo test's job, flagged as a follow-up. None of these rises to a blocking defect.

**Data flow traced:** player `DICE_THROW`(`msg.player_id`) → `handle_message` → `DiceThrowHandler` resolves PC from the authenticated `sd.player_id` (per-socket, ADR-119) → `dispatch_dice_throw` → `seal_wn_commit` (keyed by `actor.name`) → barrier → `run_wn_round` → OTEL spans. Two sockets, one shared snapshot/barrier; each socket resolves only its own authenticated seat. Safe.
**Pattern observed:** canonical two-handler shared-room MP test pattern at `test_102_4_wn_round_wire_wiring.py:119-133` (mirrors `test_merged_mp_emitter_projection.py:302`).
**Error handling:** the first-commit pending path and the `DiceDispatchError` double-seal path both exist in production; the test exercises the happy two-commit barrier close.
**Handoff:** To SM (Vizzini) for finish-story.

## Delivery Findings

### TEA (test design)
- **Improvement** (non-blocking): the sibling solo wire test
  `test_ws_dice_throw_runs_the_initiative_ordered_round` is still
  `@pytest.mark.skip(_OPPONENT_ATTACK_BLOCKED)` on the premise that WN opponent-attack
  synthesis is unshipped — but epic-152 context records 152-1 SHIPPED it (152-4
  canceled-stale; `test_wwn_opponent_attacks_on_its_slot_with_a_synthesized_strike` green),
  and my MP test's round walk fires the opponent strike. That skip is likely now stale.
  Affects `tests/integration/test_102_4_wn_round_wire_wiring.py` (the solo test + its
  `_OPPONENT_ATTACK_BLOCKED` constant). Out of scope for 152-5 (which names only the MP
  test); file as a follow-up. *Found by TEA during test design.*

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Reviewer (code review)
- No upstream findings during code review. The change is a clean, hermetic test-only
  correction; production validated correct (ADR-119 firewall + sidecar guard).
- **Improvement** (non-blocking, deferred — endorses TEA's finding): the sibling solo wire
  test `test_ws_dice_throw_runs_the_initiative_ordered_round` is still
  `@pytest.mark.skip(_OPPONENT_ATTACK_BLOCKED)` on a premise that 152-1 already shipped
  (WN opponent-attack synthesis). Affects `tests/integration/test_102_4_wn_round_wire_wiring.py`.
  Out of scope for 152-5; worth a follow-up story to re-enable + retire the constant.
  *Found by Reviewer during code review.*

## Design Deviations

### TEA (test design)
- **Story resolves as test-debt, not a production fix in `dice_throw.py`**
  - Spec source: context-story-152-5.md, "Technical Approach" / "Acceptance Criteria"
  - Spec text: "minimal seat-resolution + hermeticity fixes in `dice_throw.py` (and the
    narrator-transport seam)"; AC2 "The 2nd MP commit resolves to its own PC's seat …";
    AC3 "The sealed-commit handler path is hermetic …"
  - Implementation: NO production change. Root 1 is correct ADR-119 per-socket identity
    (test drove two seats through one socket); root 2 is the sidecar watcher needing a test
    fake (production correctly calls the real SDK). Fixed entirely by rewriting the test to
    the two-handler shared-room MP pattern + stubbing `run_sidecar_extraction_watcher`.
  - Rationale: empirical RED run + code trace proved production seat resolution and the
    sidecar hermeticity guard are both correct; changing `dice_throw.py` to "fix" root 1
    would re-open the 118-9 seat-spoof hole (ADR-119) — forbidden.
  - Severity: major (changes story class bug→test-debt and removes the Dev/GREEN production
    work the context anticipated)
  - Forward impact: GREEN phase has no production implementation; recommend routing the
    corrected (green) test straight to review. Story should be reclassified as test-debt.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Reviewer (audit)
- **TEA deviation "Story resolves as test-debt, not a production fix in `dice_throw.py`"**
  → ✓ **ACCEPTED by Reviewer.** Independently confirmed: (1) re-ran the corrected test at
  `da7047dd` — green + hermetic; (2) the security subagent confirmed the ADR-119/118-9
  seat-spoof firewall is exercised (matching per-socket identities), not bypassed; (3) the
  only alternative "production fix" (trusting `msg.player_id`) would re-open the 118-9
  seat-spoof hole — forbidden by ADR-119; (4) root 2's stub targets a non-fatal post-narration
  shadow watcher (ADR-150), correct test hermeticity, not error-masking. The reclassification
  to test-debt is sound; the corrected test provides genuine wire-level coverage of the real
  two-socket MP path. No production change is the right outcome.
- No undocumented spec deviations found.