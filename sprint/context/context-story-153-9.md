# Story 153-9: [FATE-OTHER-SEATING] router names the scene-active antagonist, not a same-surname roster NPC

## Bug Summary

Under the Fate ruleset binding, when a player's action references a target by name (or vaguely), the confrontation router/opponent-seater incorrectly selects a same-surname roster NPC instead of the scene-active antagonist who should be seated as the Other. This violates ADR-116 ("A Confrontation Requires an Other") and breaks the single-opponent-seater invariant.

## Expected Behavior

Per ADR-116, a confrontation requires a single, mechanically-capable Other. When the router names an opponent in `params["opponent"]` (e.g., a narration-established antagonist like "Captain Blackwind"), the seater must:

1. First check if that name matches a **scene-active antagonist** (the opponent already seated in the encounter, or a narrative-only character established in THIS conflict's context).
2. Only if no exact match exists, fall back to the roster-resolution logic in `_resolve_opponent_from_roster` to find a co-located statted adversary.

Under a Fate binding, the scene-active antagonist should take absolute priority — it IS the Other the player is engaging. Roster NPCs are only consulted when no narrative antagonist has been established.

## Bug Behavior

The current `_resolve_opponent_from_roster` logic (lines 874–947 in `sidequest/server/dispatch/encounter_lifecycle.py`) returns None when it encounters a name that already exists in `snapshot.npcs` (line 908: `if any(n.core.name == threat_name for n in snapshot.npcs): return None`). This is correct for **deduplication** — don't create a duplicate. However, the rest of the seating pipeline doesn't prioritize the scene-active antagonist.

When a player references a target in ambiguous terms (or when the router extracts a name from the narration), and that name could resolve to EITHER:
- A scene-active antagonist (the NPC the narrator just described as the enemy)
- A same-surname roster NPC at the location

...the seater may pick the roster NPC because the roster-resolution fallback searches `snapshot.npcs` without distinguishing between "the antagonist this narration is about" and "an ambient NPC with a matching name."

## Root Cause

The seating logic (particularly in `_resolve_opponent_from_roster` and the upstream code that calls it) does not have a way to **mark which NPC is the scene-active antagonist** for THIS conflict. The narrator establishes an antagonist in the prose, but the seater has no signal that says "this NPC is the focal enemy of this turn."

For Fate, the scene-active antagonist is the one who is narratively opposed to the player in THIS confrontation. If there's a roster NPC with the same surname, the seater must still prefer the narrative antagonist because the conflict is ABOUT engaging that character.

## Acceptance Criteria

1. **AC-1:** The seating logic in `encounter_lifecycle.py` (especially `_resolve_opponent_from_roster` and `instantiate_encounter_from_trigger`) is audited for Fate-specific seating. If the opponent is already established as a **narrative antagonist** in the snapshot, the seater names THAT opponent, not a same-surname roster NPC.

2. **AC-2:** Under Fate, when the router names an opponent that matches a narrative antagonist (a name that appears in `snapshot.encounter.actors` if an encounter is already active, or a name that was just added to `snapshot.npcs` by the narrator), that narrative antagonist is seated as the Other — regardless of whether a same-surname roster NPC exists elsewhere.

3. **AC-3:** Roster-resolution deduplication continues to work: if the router names an opponent that is ALREADY a roster NPC (not a narrative-only invention), seat that roster NPC directly.

4. **AC-4:** When no narrative antagonist exists and no exact roster match is found, the fallback to ambient co-located adversaries (the current 108-2 behavior) still applies — but only for non-Fate confrontations (per the current guard at line 939).

5. **AC-5:** Tests verify that under Fate, a scene-active antagonist with a surname-matching roster NPC is seated correctly (the narrative antagonist is named as the Other, not the roster NPC).

## Candidate Implementation Files

- **Primary:** `sidequest/server/dispatch/encounter_lifecycle.py`
  - `_resolve_opponent_from_roster()` (lines 874–947) — the roster-resolution logic that may prefer roster NPCs over narrative antagonists
  - `instantiate_encounter_from_trigger()` (likely around line 1389 and the opponent-seating section) — the entry point where the opponent-naming decision is made
  - The materialized-threat handling (lines 125–136 in `sidequest/agents/subsystems/confrontation.py`) — where the router's opponent name enters the seating pipeline

- **Secondary:** `sidequest/game/encounter.py`
  - Review the `StructuredEncounter` model to see if there's a way to mark the "scene-active antagonist" or if one needs to be added

- **Tests:**
  - `tests/server/test_opponent_roster_resolution.py` — extend with a Fate-specific case
  - `tests/server/dispatch/test_fate_opponent_seating.py` — may already have seating tests; verify Fate logic
  - May need a new test case: "Fate confrontation with scene-active antagonist sharing surname with roster NPC"

## Related ADRs and Stories

- **ADR-116** — Participant Membership Invariant, Single Opponent-Seater, End-on-No-Other
- **ADR-139** — Confrontation Integrity Invariants (Mechanically-Capable Other, Dispatch Applicability Gate)
- **ADR-144** — Fate Core Binding Replaces the Native Ruleset
- **Story 108-2** — the 108-2 roster-resolution work that introduced `_resolve_opponent_from_roster`
- **Story 150-2** — the 150-2 "Defect A" that gated roster resolution to combat-only confrontations

## Key Code References

- `sidequest/server/dispatch/encounter_lifecycle.py:874` — `_resolve_opponent_from_roster()` function
- `sidequest/server/dispatch/encounter_lifecycle.py:1389` — opponent-seating entry point in `instantiate_encounter_from_trigger()`
- `sidequest/agents/subsystems/confrontation.py:108-136` — router opponent materialization
