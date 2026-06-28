# Story 158-49 Context

## Title
Forced-dispatch dogfight (158-29/§7) crashes the SWN resolver: WWN STR/DEX default beats from beat_filter handed to SWN attack_params (KeyError stat 'STR') -> ws disconnect + confrontation soft-lock

## Metadata
- **Story ID:** 158-49
- **Type:** bug
- **Points:** 3
- **Priority:** p1
- **Workflow:** tdd
- **Repo:** sidequest-server
- **Epic:** Playtest sweep follow-ups: WWN combat seating, narrator grounding, roster/map/MP polish

## Problem
Found in the 2026-06-27 GM /sq-playtest dogfight verification (solo space_opera/coyote_star, SWN, player "Moe", slug 2026-06-27-coyote_star-5cd27aa6).

A weapons-hot intercept of a 240t freighter did NOT get router-classified (intent_router.confrontation_verb_unrouted, verbs intercept/lock/gun/missile) and seated a dogfight via the FORCED-DISPATCH fallback (intent_router.dogfight_forced_dispatch, 158-29 / ADR-153 §7). The seated "Fighter Duel" offered the beat menu: Attack (STR) / Total Defense (DEX) / Fighting Withdrawal (DEX) / Run (DEX), all DC 10. Committing "Attack (STR)" crashed the server websocket and permanently soft-locked the confrontation ("Committed — waiting for the round to resolve…", beats disabled, unrecoverable on reconnect).

CRASH (server log ~/.sidequest/logs/sidequest-server.log):
  ERROR ws.unexpected_error error="stat 'STR' not in stat block ['Cunning','Influence','Intellect','Physique','Reflex','Resolve'] — content/attribute_map bug (SWN module no longer falls back to a neutral 10)"
  KeyError ... → session.disconnect_save → ws.room_teardown_close_store
  Traceback: dice_throw.py:338 handle → dispatch/dice.py:581 dispatch_dice_throw
    → ruleset/without_number.py:178 attack_params → :161 stat_modifier → :125 _stat(stats,"STR") → KeyError

ROOT CAUSE (code): the forced-dispatch dogfight surfaces the WWN-flavored DEFAULT beat pool from sidequest/game/beat_filter.py (stat_check="STR" ~line 223, "DEX" ~line 240; comments cite "WWN SRD §2.4.4 Total Defense"). coyote_star binds SWN, whose stat block is Physique/Reflex/Intellect/Cunning/Influence/Resolve — NO STR/DEX. without_number.py._stat correctly refuses a silent neutral-10 fallback and raises. So a WWN-default beat menu is being handed to the SWN resolver. The dogfight def itself is authored correctly (space_opera/rules.yaml: resolution_mode: sealed_letter_lookup, interaction_table: dogfight/interactions_mvp.yaml, strike-fighter frame hp 8/AC 16) — the bug is the forced-dispatch seating substituting beat_filter's WWN defaults.

RELATED structural findings from the same forced-dispatch seating (filed to ping-pong 2026-06-27 14:17; may extend sibling stories rather than this one — SM/Keith call):
  - NO sealed-letter maneuvers / no positioning graph: snapshot encounter has zones:[], structured_phase:"Setup"; UI shows the generic beats above instead of Throttle Up/Break Right/loop/kill_rotation from interactions_mvp.yaml. Overlaps 158-40 (dogfight relative-position graph).
  - WRONG Other: blue actor is "Gengineered Killer", a coyote_star/bestiary.yaml Monster-Manual ground creature (not in npc_pool/npcs), seated as the ship. This is the 158-34 §6 ship-scale firewall symptom leaking through the forced-dispatch door — the firewall at encounter_lifecycle.py:1721 gates on npcs_present (router/location doors only) and does not cover forced-dispatch's default-opponent selection. The just-merged test_dogfight_router_named_scale.py closes only the router-NAMED door. Extends 158-34.

Evidence screenshots (oq-3): playtest-shots/dogfight-002-wrong-other-gengineered-killer.png, playtest-shots/dogfight-003-str-crash-softlock.png.

Scope of THIS story: stop the crash + soft-lock. A seated SWN dogfight must hand the SWN resolver a ruleset-valid beat/maneuver set (or fail loud at SEAT time, not at dice resolution). The wrong-Other and missing-maneuver items can be split to 158-34/158-40 if Keith prefers.

## Technical Approach

### RESCOPED — PR #510 Merged 2026-06-27 21:21

The documented root cause (`KeyError stat 'STR'`) is now **partially stale**:

- **Pre-#510 issue:** space_opera bound SWN, but the stat block used flavor names (Physique/Reflex/Cunning/Influence instead of STR/DEX/CON/INT/WIS/CHA). So `without_number._stat(stats,"STR")` raised KeyError.
- **Post-#510:** PR #510 (158-51, WN-attribute canonicalization) merged to origin/develop, dropping flavor names across all Without-Number packs. space_opera now uses the canonical STR/DEX/CON/INT/WIS/CHA stat block. The literal KeyError should resolve.
- **Feature branch setup:** This branch is cut from fresh origin/develop, so it **includes #510**.

**Therefore the RED test must:**
1. Reproduce a forced-dispatch SWN dogfight (solo space_opera/coyote_star, verbs intercept/lock/gun/missile per ADR-153 §7).
2. Observe what happens **post-#510**: it may no longer crash at dice-throw time, OR may crash on a different stat-checking path, OR may "succeed" but hand the SWN resolver the WRONG beat set (beat_filter's WWN defaults instead of SWN-valid or sealed-letter maneuvers).
3. The acceptance criteria below are what the feature should achieve regardless of whether #510 already fixed the literal KeyError.

_Approach hints to be refined by TEA/Dev. The story title above defines the intended behavior._

## Scope
- In scope: the behavior described by the story title.
- Out of scope: unrelated changes.

## Acceptance Criteria
- RED behavior test: a seated SWN dogfight whose beat carries a non-SWN stat_check (e.g. STR) no longer reaches without_number.attack_params with an invalid stat — committing the first dogfight beat must NOT raise KeyError and must NOT tear down the websocket. Drive the real DICE_THROW dispatch; assert no exception + confrontation advances (not a source-grep).
- The forced-dispatch (158-29) dogfight beat/maneuver menu under an SWN binding contains only ruleset-valid options — SWN-valid stat_checks (Physique/Reflex/...) or the ADR-153 sealed-letter maneuvers (no personal stat_check) — never beat_filter.py's WWN STR/DEX default pool.
- No silent fallback (CLAUDE.md): if the seater cannot build a valid SWN/sealed-letter beat set it fails loud at SEAT time, not at dice-resolution time — the player is never handed an un-committable/crashing menu.
- A committed dogfight beat resolves without disconnecting; the confrontation is never left in a permanent 'Committed — waiting for the round to resolve…' soft-lock. Verify via reconnect/replay that the round either resolves or the menu re-enables.
- OTEL: the seat path emits a span recording which beat/maneuver set + ruleset was attached to the seated dogfight, so the GM panel can confirm SWN packs receive SWN/sealed-letter beats (lie-detector for this class of mismatch).
- Regression guard: the existing SWN ground/personal combat path (already green) still resolves; the fix must not break non-dogfight SWN beats.

---
_Generated by `pf context create story 158-49` from the sprint YAML._
