# Story Context: 153-31 — Environmental Darkness Status: Wrong Severity Tier and created_turn=0

## Story Metadata
- **Story ID:** 153-31
- **Epic:** 153 (Playtest follow-ups — open findings from the 2026-06-20/21 full-stack /sq-playtest sweep)
- **Type:** Bug (cosmetic)
- **Points:** 1
- **Workflow:** trivial
- **Repositories:** sidequest-server
- **Priority:** P3

## Problem Statement

When the environment clock drives a region to full dark, descent applies a status:

```
{ text: 'Plunged into darkness — every action is harder.',
  severity: 'Wound', roll_modifier: -2,
  source: 'environment_clock', created_turn: 0 }
```

Two **cosmetic** oddities (the −2 mechanical effect itself is correct and backed):

1. **An environmental darkness penalty is tiered as severity `Wound`.** It is not a
   wound. `Wound` is the injury tier (clears at session end / with rest). An ambient
   light-state penalty reading as a bodily injury is misleading on the player's status
   surface.
2. **`created_turn` is `0`** even though the status is applied on round 3. The status
   is constructed without passing `created_turn`, so it defaults to `0`. (Note the
   ADR-051 two-tier counter: round vs interaction — the status is applied well after
   turn 0, so the stamp is plainly wrong.)

## Root Cause Direction

In `_ensure_darkness_penalty` the `Status(...)` is constructed with
`severity=StatusSeverity.Wound` and **no** `created_turn` argument (so it defaults to
`0` per the model). Both are local to the single construction site. The fix:

- **(a) Severity:** stop tagging the environmental penalty as an injury. The
  `StatusSeverity` enum has four values — `Scratch`, `Wound`, `Scar`, `Boon` — and
  **no environmental / ambient category**. The design decision in this story is whether
  to (i) reuse an existing non-injury tier (e.g. `Scratch`, the lightest, scene-bounded
  tier) or (ii) add a dedicated non-injury environmental tier to the enum. Reuse-first
  doctrine favors (i) unless the recovery cadence of `Scratch` is semantically wrong for
  an ambient state (a darkness penalty should lift when the region is relit, not "at
  scene end"). Confirm the cadence semantics before choosing; if neither existing tier
  fits the "lifts on relight" lifecycle, a minimal new tier is justified.
- **(b) created_turn:** stamp the real current turn/round. The `snapshot` is in scope
  at the dispatch entry and carries `snapshot.turn_manager`; pass
  `snapshot.turn_manager.interaction` (the canonical monotonic forensic marker used by
  the other status-creation sites) into the `Status(...)` constructor.

## Acceptance Criteria

1. **Environmental darkness status no longer reads as a wound/injury:**
   - The darkness `Status` is no longer constructed with `severity=StatusSeverity.Wound`.
   - It carries a non-injury severity/category that does not present as a bodily injury
     on the player status surface (either an existing non-injury tier or a new dedicated
     environmental tier — decided per the Root Cause notes, with the choice justified in
     the PR).
   - If a new enum value is added, it is added in exactly one place
     (`StatusSeverity` in `game/status.py`) and any recovery-cadence / clearing logic
     keyed on severity handles it (the darkness penalty must still be cleared on
     relight, as it is today — relight removal must not regress).

2. **created_turn reflects the real turn at application time:**
   - The darkness `Status` is constructed with `created_turn=snapshot.turn_manager.interaction`
     (or the equivalent canonical current-turn accessor in scope), not the implicit `0`.
   - A status applied on round/interaction N stamps N, not 0.

3. **The −2 mechanical effect is unchanged:**
   - `roll_modifier` stays `-2`; `source` stays `'environment_clock'`; the penalty is
     applied/removed under the same light-floor / relight conditions as today. This is a
     cosmetic-fields-only change.

4. **Relight removal and idempotence still hold:**
   - Re-running the environment-clock tick while already dark does not duplicate the
     status; relighting the region still removes it. (Covered by the existing
     `test_environment_clock` suite — must stay green.)

5. **Validation / wiring AC (OTEL):**
   - The existing `light.tick` span continues to fire with
     `penalty_applied=True` on the turn the darkness status is newly added — drive an
     environment-clock tick to the light floor and assert the span fires (per the
     existing `test_environment_clock_otel.py` shape). This proves the construction site
     is still reached after the edit. (Pure cosmetic field edits would not normally
     require new OTEL, per the server CLAUDE.md "Not needed for cosmetic changes" carve-out;
     reuse the existing span as the wiring assertion rather than adding a new one.)

## Key Code Areas to Investigate

**Construction site (the fix lives here):**
- `sidequest-server/sidequest/agents/subsystems/environment_clock.py`
  - `_ensure_darkness_penalty` (~lines 45–64) — builds the `Status(...)` with
    `severity=StatusSeverity.Wound` and no `created_turn`. Constants nearby:
    `DARKNESS_STATUS_TEXT`, `DARKNESS_STATUS_SOURCE = "environment_clock"`,
    `DARKNESS_PENALTY = -2`.
  - `run_environment_clock_dispatch` (~line 203) — the dispatch entry; `snapshot` is in
    scope here and is threaded to `_ensure_darkness_penalty`. Confirm/thread
    `snapshot.turn_manager` so the construction site can read the current turn.

**Status model + severity enum:**
- `sidequest-server/sidequest/game/status.py`
  - `class StatusSeverity(str, Enum)` (~lines 36–42) — values: `Scratch`, `Wound`,
    `Scar`, `Boon`. The decision in AC 1 (reuse vs add) lives here.
  - `class Status(BaseModel)` (~lines 45–104) — fields: `text`, `severity`,
    `absorbed_shifts`, `created_turn` (default 0), `created_in_encounter`,
    `incapacitating`, `stabilizable`, `source`, `roll_modifier`. `extra="forbid"`.

**Current-turn accessor:**
- `sidequest-server/sidequest/game/turn.py`
  - `TurnManager` (~lines 44–158); `interaction` (monotonic, never resets — the canonical
    forensic marker the other status sites use) and `round` (display counter, ADR-051).
    Accessors `get_interaction()` / `get_round()`.

**Reference: how other sites stamp created_turn (mirror their pattern):**
- `sidequest-server/sidequest/agents/tools/apply_status.py` (~line 102) — `created_turn=ctx.turn_number`
- `sidequest-server/sidequest/server/post_resolution_lethality.py` (~lines 251, 287) — `created_turn=turn`
- `sidequest-server/sidequest/server/dispatch/dice.py` (~line 1566) — `created_turn=round_number`

**Severity-keyed clearing/recovery logic (check before adding/reusing a tier):**
- Search `game/status.py` and callers for where severity drives clearing cadence and
  where the darkness status is removed on relight (`environment_clock.py` relight path),
  to ensure a non-injury tier still clears on relight.

**Tests:**
- `sidequest-server/tests/agents/subsystems/test_environment_clock.py` — burn / reconcile
  / relight / idempotence (must stay green).
- `sidequest-server/tests/server/test_environment_clock_injection.py` (~line 366) — also
  constructs a darkness `Status` for setup with `StatusSeverity.Wound` and no
  `created_turn`; **update this fixture** to match the new severity/created_turn so it
  doesn't enshrine the old shape.
- `sidequest-server/tests/agents/subsystems/test_environment_clock_otel.py` — `light.tick`
  / `light.relit` span assertions (the wiring proof for AC 5).
- `sidequest-server/tests/agents/test_narrator_sees_light_state.py` — narrator darkness
  awareness (sanity check, should stay green).

## Technical Notes

- **Low-risk, narrowly-scoped.** The cleanest version touches one construction site plus
  the enum (if a new tier is chosen) and the one test fixture that hard-codes
  `StatusSeverity.Wound`.
- **ADR-051 (two-tier turn counter):** `round` and `interaction` advance in lockstep in
  current production; `interaction` is the canonical monotonic marker used elsewhere for
  fact/item discovery chronology — prefer it for `created_turn` to match sibling sites.
- **`StatusSeverity` is a `str` Enum** (`Scratch`/`Wound`/`Scar`/`Boon`). If adding a
  value, follow the existing `str, Enum` + `# noqa: UP042` convention in `status.py`, and
  verify the player-facing status surface and any reference-page rendering handle the new
  value (no `extra="forbid"` blow-up downstream).
- **No silent fallback:** if the relight/clear logic keys on `severity in {Wound, Scar}`
  or similar, the new/reused tier must be explicitly included so the darkness penalty
  still clears on relight — do not let it silently persist.

## Story Scope

This story is a **cosmetic correction** of two fields on the `environment_clock`
darkness status. It does NOT:
- Change the −2 mechanical penalty, its source tag, or the light-floor / relight
  conditions that apply and remove it.
- Touch any other status source (`apply_status`, lethality, dice, beats) beyond
  mirroring their `created_turn` pattern.
- Rework the `StatusSeverity` recovery model beyond what AC 1 requires to make the
  chosen non-injury tier clear correctly.
- Add new OTEL spans (reuse the existing `light.tick` span as the wiring proof).
