# Story 158-30: Dogfight lifecycle — region drift must not resurrect a resolved/reaped duel

**Story ID:** 158-30  
**Epic:** 158 (Dogfight rebuild per ADR-153 — Ace of Aces positioning, SWN resolution, force-dispatch)  
**Points:** 3  
**Priority:** p1  
**Workflow:** tdd  
**Repos:** sidequest-server  
**Status:** backlog

---

## Story Summary

Fix the dogfight lifecycle to prevent resurrection of a resolved/reaped encounter. Per ADR-153 Plan 2 (Router → Seater → Lifecycle), a dogfight that is husk-reaped at turn start must stay reaped — never re-seat the same turn, which soft-locks the player into ship maneuvers on foot after a resolved duel.

**2026-06-25 playtest finding:** After a dogfight resolved (active=False) in a space_opera session, a normal non-combat action in the same region re-summoned it. `encounter.husk_reaped` correctly cleared the resolved encounter at turn start, but later the SAME turn `encounter.continued_same_region_drift` (location label drift Kestrel→Cold Contact) re-attached it and reset `structured_phase` from Resolution→Setup; the player was soft-locked into ship-maneuver beats while on foot in a derelict with Enter disabled. Two lifecycle rules disagreed (husk_reaped clear vs drift keep-alive) and drift won — the fix makes husk_reaped win for resolved/reaped encounters.

---

## Architecture & Patterns

### ADR-153 Plan 2 (Router → Seater → Lifecycle Contract)

Per [ADR-153 §7](../../docs/adr/153-ace-of-aces-dogfight-positioning-swn-resolution.md), the dogfight rebuild has three independent server seams:

1. **Router force-dispatch (158-29):** IntentRouter pre-narrator pass force-dispatches the dogfight when dogfight verbs hit but no confrontation routed and no fight is live.
2. **Lifecycle guard (158-30 — THIS STORY):** encounter-lifecycle husk-reap leaves a one-turn marker so the seater refuses to re-seat a duel reaped *this same turn* (a reaped duel stays reaped).
3. **Shot narration (158-35):** dogfight-shot dice-replay narration anchors to the `[DOGFIGHT_SHOT_RESOLVED]` outcome.

### The Bug: Two Rules Disagree

**Current behavior:**
- `reap_resolved_encounter_husk` (`encounter_lifecycle.py:142`) clears a resolved dogfight at turn start: `snapshot.encounter = None`
- *Same turn*, `continued_same_region_drift` (`narration_apply.py:4944`) carries over the encounter from the prior-turn state (because `snapshot.encounter` is None after husk-reap, the drift guard is satisfied, and a fresh dogfight re-seats)
- Result: `structured_phase` resets from Resolution→Setup, player sees ship-maneuver beats while on foot (phase mismatch).

**Root cause:** Husk-reap clears with no memory that this type was just reaped, so the re-seat is unguarded. The drift continue-ladder has a `not resolved` gate (`narration_apply.py:4838`) but that gate is on the *old* encounter pre-clear, not the *new* re-seat post-clear.

### The Fix: One-Turn Reaped Marker

Add a transient snapshot field `husk_reaped_this_turn: tuple[str, int] | None` that stamps `(encounter_type, interaction_turn)` when husk-reap clears. Add a seater guard in `instantiate_encounter_from_trigger` that refuses to seat an `encounter_type` reaped this same turn.

**Why this works:**
- The marker is keyed by both type AND turn number, so a stale marker from a prior turn is inert
- A genuinely-fresh dogfight (never reaped this turn) still seats normally — the created_turn fresh-this-turn exemption is preserved
- The husk-reaped-this-turn guard fires BEFORE the drift continue-ladder ever runs, stopping the re-seat at source
- Result: a resolved duel stays resolved; the drift continue-ladder never sees a resurrected encounter

### Per-Field Merge Strategies (ADR-121)

This story modifies two fields:
- `GameSnapshot.husk_reaped_this_turn` (new transient state field, defaults to None, never durable)
- Behavior: `instantiate_encounter_from_trigger` returns None for a type reaped this turn

Durability: The `husk_reaped_this_turn` marker is **per-turn transient state** — it exists only during the current turn's dispatch and is cleared at turn boundary. It is NOT written to saved games (`snapshot.encounter` is the durable state; the marker is a per-turn gate).

---

## Acceptance Criteria

### AC1: Transient Marker Field on GameSnapshot

**File:** `sidequest-server/sidequest/game/session.py`

Add the field to the `GameSnapshot` class/model:

```python
# ADR-153 §7 (158-30): the (encounter_type, turn) of a husk reaped THIS turn.
# Lets the seater refuse to re-seat a duel that was just reaped — a reaped
# duel stays reaped (no Resolution→Setup resurrection). Keyed by turn so a
# stale marker from a prior turn is inert; transient, not durable canon.
husk_reaped_this_turn: tuple[str, int] | None = None
```

- Type: `tuple[str, int] | None`; elements are `(encounter_type: str, turn: int)` where `turn` is the interaction-turn number from `snapshot.turn_manager.interaction`
- Default: `None`
- **Not durable:** This field is never written to or restored from save files; it is purely per-turn state

### AC2: Stamp the Marker When Husk is Reaped

**File:** `sidequest-server/sidequest/server/dispatch/encounter_lifecycle.py`

In `reap_resolved_encounter_husk` (~line 205), at the clear site where `snapshot.encounter = None`, stamp the marker BEFORE clearing:

```python
snapshot.husk_reaped_this_turn = (enc.encounter_type, turn)
snapshot.encounter = None
```

- Stamps only when a husk is actually reaped (`enc is not None` and not on dice-replay)
- Records the type and turn number for the seater guard (AC3)
- Observable: the existing `husk_reaped` watcher event fires; the new guard will also emit `reseat_refused_husk_reaped` when the marker prevents a re-seat

### AC3: Guard the Seater Against Same-Turn Re-Seat

**File:** `sidequest-server/sidequest/server/dispatch/encounter_lifecycle.py`

In `instantiate_encounter_from_trigger` (~line 1486), in the guard region just after the existing resolved-same-type guard (~lines 1560–1561), add:

```python
# ADR-153 §7 (158-30): a duel husk-reaped THIS turn stays reaped — refuse to
# re-seat it the same turn (the husk_reaped clear must win over a same-turn
# re-dispatch / drift keep-alive, else a resolved dogfight resurrects in Setup
# and soft-locks the player into ship maneuvers on foot). Keyed by turn so a
# genuinely-fresh dogfight on a LATER turn still seats (created_turn exemption).
reaped = snapshot.husk_reaped_this_turn
if (
    reaped is not None
    and reaped[0] == encounter_type
    and reaped[1] == snapshot.turn_manager.interaction
):
    _watcher_publish(
        "state_transition",
        {
            "field": "encounter",
            "op": "reseat_refused_husk_reaped",
            "encounter_type": encounter_type,
            "turn": str(snapshot.turn_manager.interaction),
            "source": "seater",
        },
        component="encounter",
    )
    return None
```

- Checks `(type, turn)` tuple match: only refuses if the type matches AND the turn matches
- Returns `None` (no encounter seated) on a match
- Emits a watcher event `reseat_refused_husk_reaped` to make the refusal observable (per CLAUDE.md)
- Falls through to normal seating for a fresh dogfight (never reaped this turn)

### AC4: Test — Reproduction of the Bug

**File:** `sidequest-server/tests/server/dispatch/test_dogfight_husk_no_resurrect.py`

Write a test that reproduces the 158-30 bug and verifies the fix:

```python
def test_reaped_dogfight_does_not_reseat_same_turn():
    # Seat + resolve a dogfight (simulating prior dice-replay turn).
    pack = make_dogfight_pack()
    snapshot = make_empty_snapshot(pc_name="Pilot")
    enc = seat_live_dogfight(snapshot)
    enc.resolved = True
    enc.outcome = "player_victory"
    turn = snapshot.turn_manager.interaction

    # Turn start on the next NORMAL turn: husk-reap clears the resolved dogfight.
    reaped = reap_resolved_encounter_husk(snapshot, is_dice_replay=False, turn=turn)
    assert reaped is True
    assert snapshot.encounter is None

    # SAME turn: a re-seat attempt of the just-reaped type must be refused —
    # a reaped duel stays reaped (no Resolution→Setup resurrection).
    result = instantiate_encounter_from_trigger(
        snapshot=snapshot, pack=pack, encounter_type=enc.encounter_type,
        player_name="Pilot", npcs_present=[], genre_slug="space_opera",
    )
    assert result is None
    assert snapshot.encounter is None
```

- **Current behavior (FAILS):** result is not None, snapshot.encounter is a fresh dogfight in Setup phase
- **Expected behavior (PASSES):** result is None, snapshot.encounter stays None

### AC5: Test — Fresh Dogfight Still Seats When Not Reaped This Turn

**File:** `sidequest-server/tests/server/dispatch/test_dogfight_husk_no_resurrect.py`

Verify the created_turn exemption: a genuinely-fresh dogfight (never reaped this turn) seats normally:

```python
def test_fresh_dogfight_still_seats_when_not_reaped_this_turn():
    # No prior encounter, no reaped marker: a dogfight seats normally.
    pack = make_dogfight_pack()
    snapshot = make_empty_snapshot(pc_name="Pilot")
    
    result = instantiate_encounter_from_trigger(
        snapshot=snapshot, pack=pack, encounter_type="dogfight",
        player_name="Pilot", npcs_present=[], genre_slug="space_opera",
    )
    assert result is not None
    assert snapshot.encounter is not None
```

- **Expected:** Always passes (no regression)

### AC6: Integration — No Husk-Reap Regression

**Test suite:** `sidequest-server/tests/server/dispatch/test_encounter_husk_reap.py` and related encounter-lifecycle suites.

Run the existing husk-reap and encounter-seating tests to verify no regression:

```bash
cd sidequest-server && uv run pytest tests/server/dispatch -k "husk or seat or dogfight or lifecycle" -n0 -q
```

- **Expected:** All pass (except pre-existing failures on `develop`)

### AC7: Observability — Watcher Events

Per CLAUDE.md (OTEL is the lie detector), every seater decision is observable:

- **On husk-reap:** existing `husk_reaped` watcher event fires (no change)
- **On re-seat refusal:** new `reseat_refused_husk_reaped` watcher event fires (observable in GM panel)
- Never silent refusal; every decision is logged

### AC8: No Silent Fallbacks, No Stubs

Per CLAUDE.md critical principles:

- If the marker is set but the turn number is stale, the seater falls through to normal seating (not silent)
- If the marker is set and the turn matches, the seater returns None with an observable watcher event (not silent)
- No placeholder implementations; the fix is complete

---

## Testing Strategy

### 1. Unit Tests (RED phase)

**File:** `sidequest-server/tests/server/dispatch/test_dogfight_husk_no_resurrect.py`

- `test_reaped_dogfight_does_not_reseat_same_turn` — reproduces the 158-30 bug and verifies the fix
- `test_fresh_dogfight_still_seats_when_not_reaped_this_turn` — verifies the created_turn exemption
- Assertion: marker is set/read correctly, seater guard fires/falls through as expected

### 2. Regression Suite (GREEN phase)

Run the encounter-lifecycle and husk-reap suites to verify no regression:

```bash
cd sidequest-server && uv run pytest tests/server/dispatch/test_encounter_husk_reap.py tests/server/dispatch -k "husk or seat or dogfight" -n0 -q
```

- **Expected:** All pass

### 3. Related Plans (Dependency Chain)

**Prerequisite:** Plan 1 (158-31) must be merged first. Plan 1 makes the seater seat a frame-default opponent when none is named; Plan 2 relies on the seater being correct before adding the lifecycle guard.

**Sibling:** Plan 1 Task 3 must complete (frame-default opponent seating) before Plan 2 tests can pass (else `NoOpponentAvailableError` blocks the re-seat test).

**Sibling:** Task 1 (router force-dispatch, 158-29) is independent and can be developed in parallel.

---

## Touch Points (Code Locations)

### sidequest-server

| File | Change | AC |
|------|--------|----| 
| `sidequest/game/session.py` | Add `husk_reaped_this_turn` field to `GameSnapshot` | 1 |
| `sidequest/server/dispatch/encounter_lifecycle.py` | Stamp marker in `reap_resolved_encounter_husk` (~line 205); add seater guard in `instantiate_encounter_from_trigger` (~line 1560) | 2, 3 |
| `tests/server/dispatch/test_dogfight_husk_no_resurrect.py` | New file: reproduction + fresh-dogfight tests | 4, 5 |

### sidequest-content

| File | Change | AC |
|------|--------|----| 
| (None for this story) | Lifecycle is engine-layer, not content-layer | - |

### sidequest-ui

| File | Change | AC |
|------|--------|----| 
| (None for this story) | Lifecycle is backend; GM panel observes via watcher events | - |

---

## Narrative Anchor

Per CLAUDE.md, this story serves:

- **Keith (forever-GM-now-player):** A finished dogfight stays finished. No soft-locks into ship maneuvers after resolving a duel on foot.
- **James (narrative-first):** The phase mismatch (ship beats on foot) breaks immersion; fixing it restores the scene integrity.
- **Alex (slow typist, freeze-prone):** No impact; this is backend lifecycle.
- **Sebastien (mechanics-first):** Dogfight lifecycle is now coherent — reap clears unambiguously; GM panel shows the refusal via watcher events.

---

## Related Documents

- **Epic context:** `sprint/context/context-epic-158.md`
- **Plan 2 spec:** `docs/superpowers/plans/2026-06-26-dogfight-rebuild-plan-2-router-seater-lifecycle.md` (Task 2)
- **ADR-153:** Ace of Aces Dogfight (§7: Router → Seater → Lifecycle contract)
- **Plan 1 (prerequisite):** `docs/superpowers/plans/2026-06-26-dogfight-rebuild-plan-1-firewall-seating.md` (story 158-31)
- **Related stories:** 158-29 (router force-dispatch), 158-31 (seater firewall), 158-35 (shot narration)
- **Game session model:** `sidequest-server/sidequest/game/session.py:GameSnapshot`
- **Encounter lifecycle:** `sidequest-server/sidequest/server/dispatch/encounter_lifecycle.py`
- **Dogfight fixtures:** `sidequest-server/tests/fixtures/dogfight_playtest_encounter.py`

---

## Constraints & Assumptions

### Constraints

- The marker is **transient per-turn state**, never durable (not written to save files)
- The guard fires only on `(type, turn)` tuple match; stale markers from prior turns are inert
- The created_turn exemption is preserved: a fresh dogfight still seats if the marker is absent or the turn is stale
- Observable: every seater decision emits a watcher event (no silent fallback)

### Assumptions

- `GameSnapshot.turn_manager.interaction` is a stable turn counter (int) available throughout the turn
- `reap_resolved_encounter_husk` is called at turn start before any re-seat attempt
- `instantiate_encounter_from_trigger` is called by all seating paths (router force-dispatch, drift continue, etc.) so the guard is universal
- Plan 1 (seater firewall + frame-default opponent) is merged before Plan 2 tests run
