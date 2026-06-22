# Story 153-12 Context

## Title
[SWN-RESOLUTION-BEAT-NO-EXIT] resolution beat offers a non-lethal confrontation exit under hp_depletion

## Metadata
- **Story ID:** 153-12
- **Type:** bug
- **Points:** 2
- **Priority:** p3
- **Workflow:** tdd
- **Repo:** server
- **Epic:** 153 — Playtest follow-ups (open findings from the 2026-06-20/21 full-stack /sq-playtest sweep)

## Problem Statement

Under `hp_depletion` combat (WN binding — win_condition=hp_depletion, sentinel 1,000,000 dial
thresholds, dials disabled), a ✦-marked **resolution beat** (e.g. "Fall Back") that succeeds
does not end the confrontation. The player can commit the beat, receive an `ENCOUNTER_BEAT_APPLIED`
event with `beat=retreat tier=CritSuccess`, and then remain fully trapped in the encounter — no
`ENCOUNTER_ENDED` fires, the beat pool is still shown, and the conflict stays `in_conflict=True`.

The ✦ marker is supposed to signal a non-lethal confrontation exit path (disengage / withdraw /
fall back), but the HP model has no coded exit path for a succeeded resolution beat — so ✦ is
effectively decorative under WN.

## Repro / Evidence

**Source:** capture lines 818–826; positive SWN-COMBAT-GREEN context lines 804–816.

**Session:** `2026-06-21-aureate_span-cbc50cd0` — world `space_opera/aureate_span` (swn).
**Confrontation:** Firefight, Sable (Officer, 10 HP, AC 13) vs Pelä-menäy (Vaal-Kesh agent, 48 HP).

**Beat pool (from capture line 808):**
- Take Cover (Resolve/brace)
- Shoot (Physique/strike)
- Overload Weapon (Physique/strike, cost: weapon jams)
- **Fall Back (Reflex/push, resolution beat ✦)** — DC 10

**Observed:** Player commits Fall Back → `ENCOUNTER_BEAT_APPLIED beat=retreat tier=CritSuccess`.
No `ENCOUNTER_ENDED` / confrontation-transition event fires. Confrontation remains active
(player still 4/10 HP, beat pool still rendered).

**Root cause direction:** The `hp_depletion` win condition disables the native dial-threshold
exit path. A resolution beat's success has no alternative code path to end or transition out of
the confrontation, so it no-ops after applying the beat. The engine never calls
`end_confrontation` / equivalent on a succeeded resolution beat under this win condition.

## Fix Direction

Wire the resolution-beat success path so a succeeded ✦ resolution beat (e.g. `retreat`-category
beat) **ends the confrontation as a non-lethal exit** under `hp_depletion`. Concretely:

- After `ENCOUNTER_BEAT_APPLIED` resolves a ✦ beat at Success or CritSuccess tier, the engine
  should transition the confrontation to ended (the combatant withdrew / disengaged), not
  re-enter the round loop.
- This is the WN equivalent of a successful Disengage / Full Retreat action from the SRD action
  economy — honor that; do not invent a new native dial mechanic or lethality threshold to gate it.
- ADR-143 ("Bind the Ruleset, Don't Balance It"): do not hand-balance a new mechanic; model the
  WN SRD disengage result faithfully.
- The confrontation end triggered by a succeeded resolution beat is a **non-lethal** end
  (no hp_depletion win, no loss — the engagement dissolved), distinct from the hp-drain win
  condition path.

## Acceptance Criteria

1. **Succeeded resolution beat ends the confrontation (non-lethal exit).** When a player commits
   a ✦-marked resolution beat (e.g. Fall Back / retreat) and the outcome is Success or
   CritSuccess, the confrontation ends: `ENCOUNTER_ENDED` (or the canonical confrontation-end
   event) fires, `in_conflict` becomes `False`, and the beat pool is no longer offered.

2. **Failed resolution beat does not end the confrontation.** A Failure or CritFail outcome on
   the same ✦ beat leaves the confrontation active — the player attempted to withdraw and could
   not; combat continues normally. No exit fires on a failed attempt.

3. **Non-lethal exit is distinct from hp-depletion win.** The end triggered by a succeeded
   resolution beat must not record a hp-depletion win/loss for either party. The engagement
   dissolved; no combatant was defeated. Downstream handlers (e.g. loot, defeat consequences)
   must not treat this as a win-condition end.

4. **WN SRD action economy honored; no native dial invented.** The fix does not add a new dial
   threshold, lethality-track dial, or native beat-mechanic to gate the exit. The resolution
   beat maps directly to the SRD disengage/withdraw result — a successful disengage ends the
   fight on the disengaging party's terms.

5. **Observability: watcher span marks confrontation-end-on-exit.** When the confrontation ends
   via a succeeded resolution beat, a watcher span fires indicating the non-lethal exit path
   (e.g. a `confrontation.end` / `encounter.ended` event carrying `reason=resolution_beat` or
   equivalent), so the GM panel can distinguish a resolution-beat exit from an hp-depletion win.

6. **Wiring / integration-test AC.** A test drives the full path — commit a ✦ resolution beat
   at Success tier in an active `hp_depletion` confrontation — through the real beat-application
   and confrontation-resolution seam (not by calling the exit helper in isolation), and asserts:
   (a) `ENCOUNTER_ENDED` fires (or the confrontation is marked ended), (b) `in_conflict` is
   `False` afterwards, and (c) the exit-reason watcher span fired. This test must be reachable
   from the production dispatch path.

## Source

- Capture lines 818–826 (SWN-RESOLUTION-BEAT-NO-EXIT bug) and 804–816 (SWN-COMBAT-GREEN
  context confirming the beat pool and hp_depletion combat are live).
- **ADR-114** — Ablative HP Substrate; `hp_depletion` win condition, sentinel dial thresholds,
  WN-owns-the-round shape.
- **ADR-116** — A Confrontation Requires an Other; confrontation-end mechanics and
  end-on-no-other invariant; the non-lethal exit sits alongside the hp-depletion path here.
- **ADR-143** — WN binding replaces native combat engine; bind the SRD, do not balance native.

## Scope Notes

In scope:
- Wire the resolution-beat success path to end the confrontation (non-lethal exit) under
  `hp_depletion` win conditions.
- Emit the exit-reason watcher span on confrontation-end-via-resolution-beat.
- Tests proving the path is live through the real beat-dispatch/confrontation seam.

Out of scope:
- Resolution beats under non-`hp_depletion` win conditions (dial-threshold, Fate, etc.) — do
  not regress them; verify no cross-mode breakage.
- Opponent / NPC resolution beats (if any) — the player-side exit path is the reported gap.
- Beat-pool authoring or DC calibration (the 48-HP vs 10-HP skew noted in SWN-COMBAT-GREEN is
  a separate calibration note, not a bug here).
