# Story 153-20 Context

## Title
[TOOTHLESS-DETECTOR-DRIFT] teach the seating toothless-detector about the WN SRD unarmed floor so it stops false-flagging weaponless WN opponents as invulnerable

## Metadata
- **Story ID:** 153-20
- **Type:** bug
- **Points:** 2
- **Priority:** p3
- **Workflow:** tdd
- **Repo:** server
- **Epic:** 153 — Playtest follow-ups (open findings from the 2026-06-20/21 full-stack /sq-playtest sweep)

## Problem Statement

Story 153-1 wired `opponent_damage` / `damage_spec` onto the CWN opponent reprisal beat so
landed hits actually ablate player HP. After that fix, there is a residual drift: the
confrontation-seating toothless-detector — `_opponent_reprisal_damage_resolvable` in
`sidequest/server/dispatch/encounter_lifecycle.py` — still does not know about the Without
Number SRD **unarmed floor**.

The detector checks three priority slots for a damage source:
1. `cdef.opponent_damage` — authored enemy weapon.
2. Strike beat `damage_override` — natural-attack spec on a `damage_channel=="strike"` beat.
3. Opponent core inventory weapon — an item dict carrying a `damage` field.

A weaponless WN opponent (no authored `opponent_damage`, no strike-beat override, no
inventory weapon) fails all three checks and is flagged **toothless/invulnerable at seat
time**, causing the encounter to be suppressed or degraded before it ever runs. But the WN
SRD gives unarmed attacks a real damage floor — the opponent is NOT actually invulnerable;
the detector is simply unaware of the SRD fallback.

This is the seating-detector sibling of 153-1's damage-spec wiring: 153-1 fixed the runtime
reprisal path; this story fixes the pre-seat detector that shadows it.

## Repro / Evidence

- **Source finding:** playtest capture lines 246–254 (`CWN-OPPONENT-REPRISAL-NO-DAMAGE`)
  — on-foot combat in `the_circuit`, opponent hits land but player takes 0 HP; combined
  with no `damage_spec`, combat is unlosable and a slog.
- **153-1** diagnosed the runtime reprisal gap; a follow-up code review surfaced that the
  at-seat toothless-detector uses the same priority list and has the same WN unarmed
  blind spot.
- **Detector location:** `sidequest/server/dispatch/encounter_lifecycle.py`,
  `_opponent_reprisal_damage_resolvable` (lines 231–267); the span it drives:
  `encounter_opponent_toothless_span` (`sidequest/telemetry/spans/encounter.py`).
- **Test file to extend:** `tests/server/test_opponent_toothless_detector.py`.

## Fix Direction

Teach `_opponent_reprisal_damage_resolvable` (or the calling seating path) a fourth
check: **if the pack's ruleset is a WN family binding (`swn`/`wwn`/`cwn`/`awn`) and the
opponent has no authored damage source in slots 1–3, resolve to the WN SRD unarmed
damage floor instead of returning `False`**. The function should return `True` for a
weaponless WN opponent (it CAN deal damage — via the SRD unarmed floor), not `False`
(toothless). Defer to the WN SRD numbers exactly (ADR-143: bind the ruleset, don't
balance it); do not invent or hand-tune an unarmed value.

The fix is a targeted extension of the existing detector, not a rewrite. The conservative
false-toothless bias noted in the existing docstring remains correct for non-WN rulesets
(where there is no SRD unarmed guarantee); the WN case simply adds a real damage floor to
the decision tree.

## Acceptance Criteria

1. **Weaponless WN opponent is NOT flagged toothless.** Given a WN-ruleset pack (`swn`,
   `wwn`, `cwn`, or `awn`) and an opponent with no `opponent_damage`, no strike-beat
   `damage_override`, and no inventory weapon, `_opponent_reprisal_damage_resolvable`
   returns `True` (the opponent resolves to the SRD unarmed floor, not invulnerable).
   The WN SRD unarmed value used is taken directly from the ruleset binding — not
   authored or invented by the server.

2. **Non-WN behavior is unchanged.** For a non-WN ruleset (Fate, native/dial) with the
   same weaponless opponent, the detector still returns `False` (toothless), preserving
   the existing conservative bias. The fix is WN-gated, not universal.

3. **OTEL / watcher-span AC.** The `encounter_opponent_toothless_span` span that fires
   on detector evaluation carries a `ruleset` field and (when the WN unarmed floor
   applies) an `unarmed_floor` field, so the GM panel can confirm the floor resolved
   rather than a false-toothless flag. The span already fires in the existing path —
   the AC is that it carries the new discriminating fields when the WN unarmed case
   applies.

4. **Wiring / integration-test AC.** A test in `tests/server/test_opponent_toothless_detector.py`
   drives a weaponless WN opponent (e.g., CWN ruleset, no authored damage source) through
   the real `_opponent_reprisal_damage_resolvable` call path — not a mocked wrapper — and
   asserts: (a) the detector returns `True` (not toothless), and (b) the span fires with
   the `unarmed_floor` field populated. This proves the WN unarmed awareness is live through
   the real detector seam, not only as a unit test on the new branch.

## Source
- Playtest capture (`sq-playtest-pingpong-archive-2026-06-21-epic153-capture.md`) lines 246–254 — `[BUG / CWN-OPPONENT-REPRISAL-NO-DAMAGE]`
- Sibling story: 153-1 (runtime damage_spec wiring)
- Detector: `sidequest/server/dispatch/encounter_lifecycle.py` — `_opponent_reprisal_damage_resolvable`
- Test file: `tests/server/test_opponent_toothless_detector.py`
- WN SRD unarmed floor (bind the ruleset, ADR-143)

## Scope Notes

In scope:
- Extend `_opponent_reprisal_damage_resolvable` to return `True` for a weaponless WN opponent (SRD unarmed floor).
- OTEL span fields to distinguish the unarmed-floor case.
- Integration test through the real detector path.

Out of scope:
- Runtime reprisal damage dispatch (covered by 153-1).
- Balancing or inventing unarmed damage numbers (ADR-143: defer to the SRD).
- Non-WN rulesets — their conservative false-toothless behavior is unchanged.
