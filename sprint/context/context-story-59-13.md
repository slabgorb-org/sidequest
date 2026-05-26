---
parent: context-epic-59.md
workflow: tdd
---

# Story 59-13: Chase confrontation — seat an opponent so the dial can move (ADR-116 movement slice)

> **Root cause corrected 2026-05-26 (Architect, ADR-116).** The original framing
> ("beat write-back is broken / handler doesn't consume the BeatChangeSet") was
> **disproven by measurement** (`tests/server/test_chase_writeback_probe.py`):
> with an opponent seated, chase beat write-back works and the phase transitions.
> The real defect is upstream — a chase instantiates with **no opponent seated**,
> so opponent beats are skipped and the dial freezes at 0. This story implements
> the **movement slice of ADR-116** ("A Confrontation Requires an Other").

## Business Context

Chase confrontations are a core mechanical-engagement surface for Epic 59. In
playtest, a chase shows the dual-dial frozen at 0 and no opponent — the crunch
Sebastien and Jade specifically miss, and exactly the "narrator improvises a
chase with no mechanical backing" failure the OTEL lie-detector exists to catch.
The fix makes a chase a real contest: an opponent is seated, the dial advances
for mechanical reasons, the phase transitions, and the encounter ends when the
pursuer is gone.

## Technical Guardrails

**The fix is in opponent SEATING, not write-back.** Verified real files:

- `sidequest/server/dispatch/encounter_lifecycle.py` — `instantiate_encounter_from_trigger`
  (seating) and `_npc_fallback_at_location` (room scan). **Primary fix site.**
- `sidequest/agents/subsystems/confrontation.py` — `run_confrontation_dispatch`
  (already catches `NoOpponentAvailableError` and lets the narrator render prose).
- `sidequest/game/encounter.py` — `EncounterActor` (`side`, `withdrawn`),
  `StructuredEncounter`. The `side` docstring says "engine never infers it" —
  ADR-116 §2 updates that contract: the engine legitimately seats opponents for
  adversarial confrontations.
- `sidequest/server/confrontation_lifecycle_detector.py` — already computes
  `opponent_alive_count` (opponent-side, non-withdrawn). Reuse for end-on-no-Other.
- `sidequest/server/dispatch/yield_action.py` — the player-side
  "resolve-when-all-withdrawn" path; **end-on-no-Other is its opponent-side mirror.**
- `sidequest/game/beat_kinds.py` — `apply_beat` (write-back; WORKS, do not change
  the beat math).

**Reuse-first (ADR-116, CLAUDE.md "Don't Reinvent"):** do NOT add a new
participant/membership type. `actors`/`side`/`withdrawn` already model the set.

**Sourcing is room-only (Fork A decided):** when no opponent is named, scan
`snapshot.npcs` at the acting PC's location — NPCs **and** bestiary mobs (same
roster, `bestiary_id` distinguishes them) — and seat as `side="opponent"`.
Bestiary / encounter-table pull is **out of scope** (deferred).

**OTEL (mandatory):** emit `participant.joined{source, side}` at the seating
chokepoint and `participant.left{reason}` on opponent withdrawal, so the GM panel
can verify membership decisions. (Span family naming: follow existing
`encounter_*` span conventions in `sidequest/telemetry/spans/encounter.py`.)

**Testing rule (CLAUDE.md "No Source-Text Wiring Tests"):** prove wiring via OTEL
spans and fixture-driven behavior, never by grepping production source. The
`test_genre` fixture pack (`tests/fixtures/packs/test_genre/rules.yaml`) already
defines a `chase` confrontation (category=movement, beats scramble/shortcut/…)
— use `load_genre_pack(_FIXTURE_PACK)`, not the conftest `synthetic_two_dial_pack`
(combat-only). The stale `chase_*_goal10.json` fixtures use the rejected legacy
single-`metric` shape — do NOT use them; build encounters in-code.

## Scope Boundaries

**In scope (ADR-116 movement slice):**
- Single opponent-seating path that, for a chase with no named opponent, sources
  an opponent from room NPCs/mobs and seats them `side="opponent"`.
- Generalize the `NoOpponentAvailableError` guard to `movement` (chase): if no
  opponent can be sourced, raise (handler renders prose — "race against time").
- End-on-no-Other for chase: when `opponent_alive_count` hits 0 via withdrawal,
  resolve the encounter.
- OTEL `participant.joined` / `participant.left` spans.
- Update the `EncounterActor.side` docstring to match the engine-seats-opponents
  reality (ADR-116 §2).

**Out of scope:**
- `social` / `pre_combat` guard enforcement — **staged follow-up** (validate
  against `victoria` / `tea_and_murder` first; do NOT flip these now).
- Bestiary / encounter-table opponent sourcing (Fork A deferred).
- Mid-scene recruitment (design-for, don't-build).
- Beat write-back math (`apply_beat`) — already correct, do not touch.
- Sibling stories: movement dispatch (59-12), magic (59-14), dogfight
  instantiation (59-16). If overlap appears, log a Delivery Finding.

## AC Context

**AC1 — Chase seats an opponent from the room.** `instantiate_encounter_from_trigger(
encounter_type="chase", npcs_present=[])` with an NPC or bestiary mob present at
the PC's location → the resulting encounter has ≥1 `side="opponent"` actor (NOT
neutral), and a `participant.joined` span fires with the source. Edge cases:
mob (`bestiary_id` set) seats identically to a named NPC; an NPC last-seen
elsewhere is NOT pulled.

**AC2 — No opponent → raise, not a one-sided chase.** Chase with no named
opponent and an empty room → `instantiate_encounter_from_trigger` raises
`NoOpponentAvailableError`; `run_confrontation_dispatch` catches it and returns
the prose-fallback path (no frozen one-sided encounter is created).

**AC3 — Dial moves end-to-end.** A chase instantiated via the production path
(opponent seated per AC1) → advance through `_apply_narration_result_to_snapshot`
→ opponent dial advances off 0 and phase transitions Setup→Opening. (This is the
behavior the story originally wanted, now hung on the corrected seam.)

**AC4 — End-on-no-Other.** With a seated opponent, mark the last opponent
`withdrawn` → encounter resolves (`resolved=True`, `outcome` set) and a
`participant.left{reason}` span fires. Mirrors the player-side `yield_action` rule.

## Assumptions

- `snapshot.npcs` is the single roster for both NPCs and bestiary mobs (confirmed:
  `world_materialization._apply_npc`, `Npc.bestiary_id`). "Seat NPCs and mobs" is
  one query with a filter, not two paths.
- `opponent_alive_count` in `confrontation_lifecycle_detector` is reusable for the
  end-on-no-Other check. If it isn't reachable from the withdrawal seam, log a
  Design Deviation rather than duplicating the count.
- The `test_genre` fixture pack's `chase` def is current and loadable. (Verified.)
- Generalizing the guard to `movement` only (not social/pre_combat) will not
  regress combat or social packs. If a movement pack relies on deferred opponents,
  that's a Design Deviation — surface it, don't silently exempt.
