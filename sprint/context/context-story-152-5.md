# Story 152-5 Context

## Title
[BUG] MP WN-round wire: 2nd commit misresolves to the 1st PC's seat (round never fires) + non-hermetic narrator transport on the sealed-commit handler path — unskip `test_mp_wire_first_commit_seals_second_commit_fires_the_round`

## Metadata
- **Story ID:** 152-5
- **Type:** bug
- **Points:** 3
- **Priority:** p2
- **Workflow:** tdd
- **Repo:** server
- **Epic:** 152 — WN combat owns the full WWN action set (completes 108-8)
- **Stack:** sits on the now-complete single-player WN round (152-1/152-2/152-3 done; 152-4 canceled-stale)

## Problem
Once the `committed_blow → attack` swap (108-8 / 125-8) let the **first** MP commit
SEAL the sealed-commit barrier, a two-player WN round at the **wire level** exposed two
separate latent roots — both currently quarantined behind `@pytest.mark.skip(reason=_MP_WIRE_BLOCKED)`:

1. **2nd commit misresolves to the 1st PC's seat.** The second player's `DICE_THROW`
   (player-2 → "Vex Calder") resolves to the **first** PC's seat — the round-engine
   sees `"'Rux' has already committed"`, so the sealed-commit **barrier never closes**
   and the round never fires. The production MP seat resolution lives in
   `sidequest/handlers/dice_throw.py` and is supposed to map `player_id → PC` via
   `snapshot.player_seats` (e.g. `{"player-1": "Rux", "player-2": "Vex Calder"}`).
   The bug is that the second commit is attributed to the wrong seat.

2. **Non-hermetic narrator transport on the sealed-commit handler path.** Even with
   `orchestrator.run_narration_turn` stubbed (AsyncMock), the wire/handler path on the
   sealed-commit branch still reaches the **real `claude-agent-sdk` transport** —
   a non-hermetic narrator call. The production path must be isolatable so the wire
   test runs without hitting the live SDK.

## Deliverable (the test IS the spec)
Unskip and make green:
`sidequest-server/tests/integration/test_102_4_wn_round_wire_wiring.py::test_mp_wire_first_commit_seals_second_commit_fires_the_round`
(currently line ~188, `@pytest.mark.skip(reason=_MP_WIRE_BLOCKED)`).

What the test pins (the acceptance behavior):
- Two seated PCs via `snapshot.player_seats = {"player-1": pc_one, "player-2": pc_two}`,
  both as `EncounterActor` + `InitiativeEntry`.
- **After the FIRST commit (player-1):** the barrier stays OPEN — NO `wwn.round.committed`,
  NO `wwn.round.resolved`, NO `encounter.opponent_attack_resolved` span. (A reprisal on
  the first sealed commit is the retired rider behavior.)
- **After the SECOND commit (player-2):** the barrier closes and the round walks **exactly
  once** — `wwn.round.committed` AND `wwn.round.resolved` present, with
  `names.count("wwn.round.resolved") == 1`.
- The whole sequence runs inside the **production chain** (handler → dispatch → wn_round),
  not at dispatch level only (the two-player path was previously proven at dispatch level
  in `test_102_4_wn_sealed_round.py`).

## Technical Approach (pointers — TEA/Dev to refine)
- **Root 1 (seat resolution):** investigate how `dice_throw.py` resolves the committing
  PC from the inbound `player_id`. The fix must make player-2's commit land on player-2's
  seat, not collapse to the first PC. Preserve the existing solo-table behavior (the
  passing solo wire test `test_*solo*` / the AC5 wiring test above must stay green).
- **Root 2 (hermeticity):** find where the sealed-commit handler branch reaches the real
  SDK transport despite the stubbed `run_narration_turn`, and make that seam injectable/
  stubbable the same way the solo wire tests already isolate the narrator (AsyncMock on
  `orchestrator.run_narration_turn`). Do NOT add a silent fallback — keep it fail-loud.
- **OTEL:** the round/opponent spans (`wwn.round.committed`, `wwn.round.resolved`,
  `encounter.opponent_attack_resolved`, `encounter.beat_applied`) are the lie-detector the
  test asserts on. Any new decision (seat resolution) should remain observable; don't
  silence existing spans.

## Invariants to preserve (from epic 108-8 / ADR-143)
- The action allowlist stays **closed** (a bogus beat_id still raises loudly).
- Synthesis is gated on `isinstance(ruleset, WithoutNumberRulesetModule)` — native packs
  unaffected.
- Every defensive/opponent decision emits an OTEL span.
- **Bind, don't balance:** do not reintroduce native beat/dial scaffolding to "make MP
  work" — fix the seat/wire plumbing only.

## Scope
- **In scope:** the two roots above; unskipping the one named MP-wire test; minimal
  seat-resolution + hermeticity fixes in `dice_throw.py` (and the narrator-transport seam).
- **Out of scope:** the opponent-attack synthesis (shipped in 152-1; its sibling
  `_OPPONENT_ATTACK_BLOCKED` quarantine is a separate concern), any native-beat
  reintroduction, balancing.

## Acceptance Criteria
1. `test_mp_wire_first_commit_seals_second_commit_fires_the_round` is **unskipped** and passes.
2. The 2nd MP commit resolves to its own PC's seat; the sealed-commit barrier closes only
   after both seated PCs commit; the round fires **exactly once**.
3. The sealed-commit handler path is **hermetic** under the test's AsyncMock narrator — no
   real `claude-agent-sdk` transport call.
4. No regression: the solo wire tests in the same file and the broader server suite stay
   green (gate on the full suite with content per project doctrine, not a scoped subset).
5. OTEL spans remain the source of truth (no narration-prose verification).

## References
- Skipped test + `_MP_WIRE_BLOCKED` reason: `tests/integration/test_102_4_wn_round_wire_wiring.py:45-67, 188-257`
- Production seam: `sidequest/handlers/dice_throw.py` (MP seat resolution, `snapshot.player_seats`)
- Epic context: `sprint/context/context-epic-152.md` (round walk diagram, invariants, 152-5 entry lines 133-135)
- Design: `docs/superpowers/specs/2026-06-20-wn-full-action-set-design.md`
- ADR-143 (bind, don't balance), ADR-142 (WN core extraction), ADR-116 (a confrontation requires an Other)

---
_Authored by SM (Vizzini) during 152-5 setup, enriching the auto-generated stub from the skipped test + epic-152 context (the sprint YAML carries no description/AC for this bug)._
