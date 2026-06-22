# Story 153-6 Context

## Title
[SWN-DOGFIGHT-UNREACHABLE] wire ADR-077 dogfight to IntentRouter dispatch

## Metadata
- **Story ID:** 153-6
- **Type:** bug
- **Points:** 5
- **Priority:** p3
- **Workflow:** tdd
- **Repo:** server
- **Epic:** 153 — Playtest follow-ups (open findings from the 2026-06-20/21 full-stack /sq-playtest sweep)

## Problem Statement

The ADR-077 dogfight subsystem (`sidequest/game/dogfight_shot.py`, dogfight refs in
`encounter_lifecycle.py` / `narration_apply.py`) is implemented but **not reachable from
natural-language ship combat**. There is no dogfight/ship-combat dispatch in
`agents/subsystems/` and no dogfight reference in `agents/intent_router.py`. As a result,
a player who sets up unambiguous ship-vs-ship combat gets a narrator improvisation
(the contact flees / prose only) with **zero encounter starts** — the dogfight engine is
never engaged.

This is the direct sibling of 153-5 (SWN-ORBITAL-COURSE-INERT, already fixed): same
"implemented-but-unreachable" shape, same wiring gap against the IntentRouter subsystem bank
(ADR-113), same SWN space-scale scope.

## Repro / Evidence

**Session:** `2026-06-21-coyote_star-2cb11877`, world `space_opera/coyote_star` (swn).

**Turns:**
1. Detected a dark hostile contact → "paint the contact with targeting radar — full lock"
2. "Bring the Kestrel to combat attitude, drives hot… if it twitches a weapon port we fire first"

**Result:** narrator responded with prose — contact broke off ("attitude thrusters… breaking
for the Drift"). **`encounter_events: 0`**. No dogfight started; no structured ship-combat
encounter.

**Code confirmation (grep-verified):**
- `agents/intent_router.py` — zero references to dogfight
- `agents/subsystems/` — no dogfight subsystem dispatch module
- `game/dogfight_shot.py` — exists; dogfight hooks exist in `encounter_lifecycle.py` /
  `narration_apply.py` — none reachable from the turn flow via IntentRouter

**Caveat (from board):** bounded 2-turn attempt; dogfight may still be reachable from a
scripted scenario encounter. From the unscripted player seat, deliberate ship combat produces
only narrator prose.

## Fix Direction

Wire the ADR-077 dogfight into the IntentRouter subsystem bank (ADR-113), using 153-5's
orbital-course wiring as the pattern:

1. Add a dogfight/ship-combat dispatch subsystem in `agents/subsystems/` that recognises
   ship-combat intents (hostile contact + combat attitude / weapon lock / engage language).
2. Register the subsystem in `agents/intent_router.py` so a matching intent routes to the
   ADR-077 dogfight seating path instead of being handed to the narrator as free narration.
3. Emit a watcher span on dispatch (dogfight-dispatch event) so the GM panel can confirm the
   engine fired, not the narrator.

Do not redesign the ADR-077 dogfight engine itself — the engine exists and is the wiring
that is missing.

## Acceptance Criteria

1. **Natural-language ship-combat intent seats a dogfight.** An unambiguous ship-combat
   action ("targeting lock", "combat attitude", "weapons hot", similar) through the normal
   turn path routes through IntentRouter and starts a structured dogfight encounter
   (`encounter_events > 0`, dogfight seated, `in_conflict=True`). The narrator no longer
   de-escalates or improvises unilaterally when combat intent is unambiguous.

2. **OTEL / watcher-span AC.** Dispatching to the dogfight subsystem emits a
   `dogfight.dispatch` (or equivalent) watcher span the GM panel can observe — confirming the
   engine was engaged, not that the narrator improvised ship combat. Absent this span,
   in-conflict dogfight narration is unverifiable.

3. **IntentRouter registration is live-wired (integration AC).** A test drives a
   natural-language ship-combat intent through the real IntentRouter path — not by calling the
   subsystem in isolation — and asserts: (a) the dogfight subsystem fires, (b) a dogfight
   encounter is seated, and (c) the dispatch watcher span is emitted. This proves the
   subsystem is registered and reachable from the production dispatch path, not just that the
   subsystem works in isolation.

4. **Sibling orbital-course path is not regressed.** The 153-5 IntentRouter wiring for
   orbital course / clock (ADR-130) continues to pass after this change.

5. **No silent fallback.** If the dogfight subsystem is unable to seat a dogfight (missing
   encounter preconditions, no valid opponent, etc.) it fails loudly (logged event with reason)
   rather than silently passing control back to the narrator with no indication of why the
   engine did not engage.

## Source

- Board capture lines 857–867 (SWN-DOGFIGHT-UNREACHABLE finding)
- Board capture lines 874–890 (SWN-series driver summary for FIXER)
- ADR-077 (Dogfight Subsystem via StructuredEncounter Extension)
- ADR-113 (Intent Router — Mechanical-Engagement Spine)
- Story 153-5 (SWN-ORBITAL-COURSE-INERT — sibling, already wired; use as pattern)

## Scope Notes

In scope:
- IntentRouter subsystem registration for dogfight dispatch
- Watcher span for dogfight-dispatch verifiability on the GM panel
- Integration test through the real IntentRouter path

Out of scope:
- ADR-077 dogfight engine internals (rounds, shots, damage resolution) — the engine exists
- Scripted/scenario-triggered dogfight paths — those may already work; this story covers the
  natural-language / narrator-turn route
- Other SWN space-scale gaps (153-5 orbital course, 153-8 resolution-beat-no-exit)
