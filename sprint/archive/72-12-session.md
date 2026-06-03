---
story_id: "72-12"
jira_key: ""
epic: "72"
workflow: "tdd"
---

# Story 72-12: Presence-stamp opponent/participant last_seen beyond combat seams (opposed_check social + participant_joined) — 'presence means presence'

## Story Details

- **ID:** 72-12
- **Epic:** 72 — NPC Identity Hardening
- **Jira Key:** (none — Jira not enabled)
- **Workflow:** tdd
- **Type:** bug
- **Priority:** p3
- **Points:** 3
- **Stack Parent:** none
- **Repos:** sidequest-server

## Summary

Extend the presence-stamping implementation from story 72-8 to two additional encounter seams:

1. **opposed_check social confrontations** — when an NPC is a seated opponent in a non-combat opposed-check (e.g. a social persuasion roll against an NPC), their `last_seen_turn` and `last_seen_location` must be stamped at engagement resolution.
2. **participant_joined events** — when an NPC joins an existing encounter as a participant (e.g. a location-fallback NPC joining mid-combat), their presence must be stamped at the moment they seat.

**Doctrine:** "presence means presence" — any time an NPC is a seated opponent or joins as a participant, their presence must be stamped (last_seen_turn + location), regardless of whether it's a combat seam.

## Lineage

This story builds directly on **72-8: "Stamp last_seen_turn/location on encounter presence, not just prose mention"** (DONE, 2026-06-01). Story 72-8 established the pattern and wired it to two existing seams:

- `_seed_combat_hp_depletion_to_npcs` — the hp_depletion opponent seam
- `_publish_combat_edge_to_npcs` — the legacy dial-threshold opponent seam

Both now stamp recency and surface the stamped values on the `npc.edge_published` OTEL span.

**72-12 extends this pattern** to two additional seams that 72-8 did not cover:

1. Opposed-check social resolution (the `_resolve_opposed_check_branch` path in `narration_apply.py`)
2. Participant-joined seating (the `participant_joined_span` emission in `encounter_lifecycle.py`)

**Sibling story 72-13** (not this story) handles the hp_depletion presence-stamp wiring test — keep scope separate.

## Sm Assessment

**Routing:** tdd workflow, setup → red. Next agent: TEA (RED phase).

**Why this story, why now:** Selected by Operator. 3pt server-only bug extending the DONE 72-8 presence-stamp pattern to two uncovered seams (opposed_check social + participant_joined). Low blast radius — additive stamping on existing dispatch paths, with 72-8 as a proven reference implementation to mirror.

**Scope guardrails for the pipeline:**
- Two seams only — `opposed_check` social resolution and `participant_joined` seating. Do NOT absorb 72-13's hp_depletion wiring test.
- OTEL is load-bearing (epic-72 doctrine: "every leg needs OTEL"). Each new stamp must ride a watcher span so the GM panel can verify it fired — AC2 and AC4 exist specifically for this. A passing unit test without an OTEL assertion does not satisfy the epic.
- Wiring test required: the stamp must be reachable from the production dispatch path, not just unit-tested in isolation (AC1/AC3 are the production-wiring ACs).
- No Silent Fallbacks: when location can't be resolved, stamp the turn only and freeze location — never invent one (AC5).
- Backward compat: 72-8 seams must not regress (AC6).

**Open question for TEA/Dev (not blocking):** the resolve-gate accepted the embedded session context (no standalone `sprint/context/` doc was written). If TEA's RED gate demands a standalone context-story file, the recovery pipeline (`create_context`, type: story) is wired to generate it — don't halt, recover.

**Test reference:** 72-8's passing suite (`tests/server/dispatch/test_72_8_presence_last_seen_stamp.py`) is the pattern to clone for both new seams.

## Technical Approach

### Seam 1: opposed_check Social Confrontations

**File:** `sidequest/server/narration_apply.py`, function `_resolve_opposed_check_branch`

**Current behavior:** The opposed_check branch resolves the opponent's beat, applies damage if strike damage applies, and calls `apply_beat` for both sides. The opponent NPC is mutated (HP/dial advanced) but its `last_seen_turn` / `last_seen_location` are never stamped.

**Fix:**

1. After finding the opponent actor and confirming they are a seated NPC (via `snapshot.npcs` lookup), stamp their presence:
   - Advance `last_seen_turn` to the current turn
   - Set `last_seen_location` to the acting player's location (if resolved), otherwise leave it frozen (No Silent Fallbacks)
2. Emit an OTEL span to surface the stamped values so the GM panel can verify the stamp fired

**Pattern (from 72-8):**

```python
# Resolve party location (the player's perspective).
party_location = party_location_func(acting_character_name)

# Find the opponent NPC.
opp_npc = snapshot.find_npc(opponent_actor.name)
if opp_npc:
    # Stamp presence.
    opp_npc.last_seen_turn = turn
    if party_location:
        opp_npc.last_seen_location = party_location
    
    # Emit OTEL (add to npc_edge_published span or participant_joined span).
    with npc_edge_published_span(..., last_seen_turn=turn, last_seen_location=party_location):
        pass
```

### Seam 2: participant_joined Events

**File:** `sidequest/server/dispatch/encounter_lifecycle.py`, function that fires `participant_joined_span`

**Current behavior:** The `participant_joined_span` is emitted as a guard span when an actor seats into an encounter. The span surfaces the actor's name, side, and source, but does NOT stamp the actor's `last_seen_turn` / `last_seen_location` if the actor is an NPC.

**Fix:**

1. After seating an actor and emitting the `participant_joined_span`, check if the actor is a roster NPC (in `snapshot.npcs` or `snapshot.npc_pool`)
2. If so, stamp their presence:
   - Advance `last_seen_turn` to the current turn
   - Set `last_seen_location` to the seating player's location (if resolved), otherwise leave frozen
3. Add the stamped values as attributes on the `participant_joined_span` itself so the GM panel sees the stamp alongside the seating event

**Pattern:**

```python
with participant_joined_span(
    encounter_type=encounter_type,
    name=actor.name,
    side=actor.side,
    source=source,
    # NEW: presence-stamp attributes if actor is an NPC
    last_seen_turn=turn,
    last_seen_location=party_location,
):
    # Inside the span context, also update the NPC record
    if is_npc(actor.name, snapshot):
        npc = find_npc(actor.name, snapshot)
        npc.last_seen_turn = turn
        if party_location:
            npc.last_seen_location = party_location
```

## Acceptance Criteria

### AC1: opposed_check social stamps presence WITHOUT prose mention (production wiring path)

An NPC seated as an opponent in an opposed_check social confrontation (e.g. persuasion roll) gets `last_seen_turn` advanced to the encounter turn and `last_seen_location` set to the acting PC's location, even if the narrator never name-drops them in prose.

**Test:** Drive the production handshake (narrator selection → `_resolve_opposed_check_branch`), confirm the opponent NPC's `last_seen_turn` and `last_seen_location` are stamped.

### AC2: opposed_check stamp rides npc_edge_published span (OTEL lie-detector)

The stamped recency is surfaced as attributes (`last_seen_turn`, `last_seen_location`) on the existing `npc.edge_published` span so the GM-panel lie-detector can confirm presence-stamping fired.

**Test (OTEL assertion):** Drive an opposed_check, emit the `npc.edge_published` span, and assert the span carries the correct `last_seen_turn` and `last_seen_location` attributes.

### AC3: participant_joined stamps presence on seating (production wiring path)

An NPC seated as a participant (e.g. location-fallback join) gets `last_seen_turn` and `last_seen_location` stamped at the moment the `participant_joined_span` fires. The presence-stamp reflects the turn and location of the seating, not a prior prose mention.

**Test:** Drive `instantiate_encounter_from_trigger` with location fallback, confirm the participant NPC's `last_seen_turn` and `last_seen_location` are stamped.

### AC4: participant_joined stamp on span (OTEL lie-detector)

The stamped recency is surfaced as attributes (`last_seen_turn`, `last_seen_location`) on the `participant_joined_span` itself, distinct from the side/source attributes already present.

**Test (OTEL assertion):** Drive a location-fallback participant join, emit the `participant_joined_span`, and assert the span carries the correct `last_seen_turn` and `last_seen_location` attributes.

### AC5: no resolved location stamps turn, not location (edge case, mirrors 72-8 AC3)

When `party_location` returns `None` (the acting PC has no resolved location), the presence stamp advances `last_seen_turn` but must NOT overwrite `last_seen_location` with a bogus/empty value — it stays frozen at whatever it last was (No Silent Fallbacks, mirrors the prose path in 72-8).

**Test:** Drive both seams with an unresolved location, assert `last_seen_turn` advances and `last_seen_location` is unchanged.

### AC6: no regression on existing 72-8 seams

The hp_depletion and dial-threshold presence-stamp paths (72-8, already live) continue to fire and emit OTEL correctly. Existing 72-8 tests stay green.

**Test:** Run the full 72-8 test suite (`test_72_8_presence_last_seen_stamp.py`).

## Design Deviations

### TEA (test design)
- **Opposed_check tests run against the real `tea_and_murder` content pack, not a synthetic fixture pack**
  - Spec source: context-story-72-12 / session "Test Pattern (from 72-8)"
  - Spec text: 72-8's pattern uses a synthetic `tests/fixtures/packs/test_genre` snapshot + `_make_npc`
  - Implementation: Seam-1 and Seam-2 tests load the real `tea_and_murder` pack and drive its authored `social_duel` cdef (guarded by `pytest.mark.skipif` when the content pack is absent), mirroring `tests/server/test_glenross_social_duel_opposed_check.py`
  - Rationale: the synthetic fixture pack has no `opposed_check` confrontation with authored beats + `opponent_default_stats`; `resolve_opposed_check`/`resolve_opponent_modifier` fail loud without them, so an opposed_check social seam cannot be exercised on the synthetic pack. The real-content + skipif pattern is the established precedent for this seam.
  - Severity: minor
  - Forward impact: these 6 tests skip in any environment without the content sibling checked out; the 72-8 combat-seam tests (synthetic) remain the always-on coverage.
- **AC6 (no regression on 72-8 combat seams) is covered by the existing 72-8 suite, not a new duplicate test**
  - Spec source: context-story-72-12, AC6
  - Spec text: "Run the full 72-8 test suite (`test_72_8_presence_last_seen_stamp.py`)."
  - Implementation: no new AC6 test authored; the RED run verifies `test_72_8_presence_last_seen_stamp.py` stays GREEN (6 passed) alongside the 6 failing 72-12 tests. Dev/verify re-runs both files.
  - Rationale: re-implementing the 72-8 assertions here would duplicate coverage and drift from the canonical suite; AC6 is a regression guard satisfied by keeping that suite green.
  - Severity: minor
  - Forward impact: none — AC6 is enforced by running both files in the same suite.
- **Review rework: AC3/AC4 location proof handled via a router-named test, NOT the Reviewer's literal `_STALE_LOC` fixture fix**
  - Spec source: Reviewer Assessment (review phase), HIGH finding on AC3/AC4
  - Spec text (Reviewer): "Init the NPC with `location=_STALE_LOC` in both AC3 and AC4 ... so they now prove the stamp wrote the new value."
  - Implementation: Reverted AC3/AC4 to co-located `location=_HALL` and instead added `test_participant_joined_router_named_stamps_location` (router-named, `_STALE_LOC`→assert `_HALL`) to carry the location-write proof.
  - Rationale: applying the literal fix broke the tests with `NoOpponentAvailableError` — the location-FALLBACK seating path (`_npc_fallback_at_location`) only seats an NPC whose `last_seen_location` ALREADY equals the player's location, so a fallback-seated NPC is co-located *by construction* and its location cannot differ before/after. The Reviewer's underlying concern (seam-2 location-write unverified) is valid and is now genuinely covered by the router-named test where co-location is not required; AC3/AC4's discriminating proof for the fallback path is the TURN advance, documented inline. (Receiving-code-review discipline: verified the suggested fix before implementing, found it incorrect, addressed the real concern.)
  - Severity: minor
  - Forward impact: none — coverage strengthened (7 tests, 2×2 seating-source × location-resolved matrix closed).

### Dev (implementation)
- **Reused the 72-8 stamp primitive `_stamp_encounter_presence` instead of routing Seam 1 through `_publish_combat_edge_to_npcs`**
  - Spec source: session Delivery Findings → TEA (test design), Gap finding on AC2
  - Spec text: "Cleanest wiring: route the opponent presence-stamp through the existing `encounter_lifecycle._publish_combat_edge_to_npcs`, which already both stamps `last_seen_*` AND emits `npc.edge_published`."
  - Implementation: the opposed_check branch (`_resolve_opposed_check_branch`) calls the smaller shared primitive `_stamp_encounter_presence(opp_npc, ...)` and emits `npc_edge_published_span(...)` directly, rather than calling `_publish_combat_edge_to_npcs` wholesale.
  - Rationale: `_publish_combat_edge_to_npcs` OVERWRITES the opponent's `core.hp` pool from the dial (`npc.core.hp.max = threshold; current = max(1, threshold - dial)`) — a combat-specific mutation that is wrong for a non-combat social duel (it would reset Sir Iain's HP to the barbs-landed dial). Reusing only the stamp primitive + span gets AC1+AC2 (same span family, same write discipline) with no spurious HP side effect. The span still surfaces the social dial as its `current`/`max` (inverted, same convention) so the GM-panel pool view stays honest.
  - Severity: minor
  - Forward impact: none — same span name (`npc.edge_published`) and same `_stamp_encounter_presence` discipline as the combat seams; the AC2 test asserts the span + attrs, which pass.
- **Seam 2 presence stamp fires for ALL roster-NPC actors at seating, any side (not only opponents)**
  - Spec source: context-story-72-12, AC3 + doctrine "presence means presence"
  - Spec text: "An NPC seated as a participant (e.g. location-fallback join) gets last_seen_turn/location stamped."
  - Implementation: the `participant_joined` loop stamps every seated actor that resolves to a `snapshot.npcs` entry, regardless of `side` (player-side PCs are not in `snapshot.npcs`, so they no-op naturally). It does not filter to `side == "opponent"` the way the combat seams do.
  - Rationale: doctrine is presence, not hostility — an allied/neutral NPC joining a parley is just as "present" and must not be mis-evicted by 72-6's prune. Stamping any roster NPC is the literal reading of "presence means presence."
  - Severity: minor
  - Forward impact: combat opponents are stamped here at seating AND re-stamped by the 72-8 combat seams below with the same turn + location — consistent value, no double-advance (verified: 72-8 suite stays green).

### Reviewer (audit)
- **TEA: Real content pack vs synthetic fixture** → ✓ ACCEPTED by Reviewer: the synthetic fixture pack has no `opposed_check` cdef with authored beats/opponent stats; real `tea_and_murder` + `skipif` is the established precedent (`test_glenross_social_duel_opposed_check.py`). Sound — though note the suite silently skips without the content sibling (acceptable for this repo's dual-clone layout).
- **TEA: AC6 covered by existing 72-8 suite, no new test** → ✓ ACCEPTED by Reviewer: AC6 is a regression guard; re-implementing it would duplicate the canonical suite. RED/GREEN runs both files. Agrees with author reasoning.
- **Dev: Reused `_stamp_encounter_presence` over `_publish_combat_edge_to_npcs`** → ✓ ACCEPTED by Reviewer: the wrapper overwrites `core.hp` from the dial — a real bug on the social path. Reusing the smaller primitive is the correct reuse-first call (also endorsed by Neo at spec-check). Agrees with author reasoning.
- **Dev: Seam 2 stamps any roster-NPC, not only opponents** → ✓ ACCEPTED by Reviewer: literal reading of "presence means presence"; PC-side actors no-op (not in `snapshot.npcs`). Sound.
- No undocumented spec deviations found — the implementation matches the ACs (the rejection is a test-integrity defect, not a spec deviation).
- **(Review 2) TEA: AC3/AC4 location proof via router-named test, not literal `_STALE_LOC` fixture** → ✓ ACCEPTED by Reviewer: the structural discovery is correct — the location-fallback path requires co-location, so `_STALE_LOC` there is impossible. Routing the location-write proof to the router-named path is sound. (The residual span-layer gap is a separate test-coverage finding, not a flaw in this deviation.)
- **(Review 3) No new deviations** — rework #2 extended the router-named proof to the span layer + added consistent `len==1` guards; all prior deviations remain ACCEPTED. APPROVED.

### Architect (reconcile)

Reviewed all logged deviations against the story scope (session), the ACs, epic-72 context, and sibling 72-13 (kept distinct — hp_depletion wiring untouched). All entries are accurate and complete (6 fields each):

- **TEA (test design)** — (1) real `tea_and_murder` content pack + skipif vs synthetic fixture: accurate; the `opposed_check`/`social_duel` cdef genuinely requires authored beats + opponent stats the synthetic pack lacks. (2) AC6 via existing 72-8 suite, no duplicate test: accurate; verified 72-8 stays green every cycle. (3) AC3/AC4 location proof via router-named test, not literal `_STALE_LOC`: accurate and load-bearing — the location-fallback path requires co-location by construction (`_npc_fallback_at_location` filters `last_seen_location == location`), so `_STALE_LOC` there raises `NoOpponentAvailableError`; the proof correctly lives in the router-named path.
- **Dev (implementation)** — (1) reused `_stamp_encounter_presence` over `_publish_combat_edge_to_npcs`: accurate; the wrapper would clobber the social opponent's `core.hp` from the dial. (2) seam-2 stamps any roster-NPC (any side): accurate; literal reading of "presence means presence", PC-side actors no-op.

**AC deferrals:** none — all six ACs (AC1–AC6) are DONE and discriminatingly tested on both the object and OTEL-span layers across both seating sources.

**No additional deviations found.** The implementation matches the ACs; the entire review-rejection history was test-integrity hardening (tautological→discriminating assertions), not spec drift. The two non-blocking production Improvements surfaced in review (silent no-NPC-skip OTEL signal; `opposed_check`+`hp_depletion` dial-inversion guard) are epic-scope follow-ups, correctly out of this 3pt story's scope.

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-03T15:14:19Z
**Round-Trip Count:** 2

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-03 | 2026-06-03T14:10:17Z | 14h 10m |
| red | 2026-06-03T14:10:17Z | 2026-06-03T14:20:36Z | 10m 19s |
| green | 2026-06-03T14:20:36Z | 2026-06-03T14:27:27Z | 6m 51s |
| spec-check | 2026-06-03T14:27:27Z | 2026-06-03T14:29:06Z | 1m 39s |
| verify | 2026-06-03T14:29:06Z | 2026-06-03T14:33:06Z | 4m |
| review | 2026-06-03T14:33:06Z | 2026-06-03T14:42:20Z | 9m 14s |
| red | 2026-06-03T14:42:20Z | 2026-06-03T14:51:25Z | 9m 5s |
| green | 2026-06-03T14:51:25Z | 2026-06-03T14:52:35Z | 1m 10s |
| spec-check | 2026-06-03T14:52:35Z | 2026-06-03T14:53:14Z | 39s |
| verify | 2026-06-03T14:53:14Z | 2026-06-03T14:55:26Z | 2m 12s |
| review | 2026-06-03T14:55:26Z | 2026-06-03T15:01:15Z | 5m 49s |
| red | 2026-06-03T15:01:15Z | 2026-06-03T15:03:28Z | 2m 13s |
| green | 2026-06-03T15:03:28Z | 2026-06-03T15:04:05Z | 37s |
| spec-check | 2026-06-03T15:04:05Z | 2026-06-03T15:04:31Z | 26s |
| verify | 2026-06-03T15:04:31Z | 2026-06-03T15:06:47Z | 2m 16s |
| review | 2026-06-03T15:06:47Z | 2026-06-03T15:12:57Z | 6m 10s |
| spec-reconcile | 2026-06-03T15:12:57Z | 2026-06-03T15:14:19Z | 1m 22s |
| finish | 2026-06-03T15:14:19Z | - | - |

## Delivery Findings

No upstream findings at setup. Agents record observations as they execute.

### TEA (test design)
- **Gap** (non-blocking): the opposed_check resolution branch (`_resolve_opposed_check_branch`) does NOT currently emit a `npc.edge_published` span at all — that span family only fires from the two combat seams in `encounter_lifecycle.py`. AC2 requires the Seam-1 presence stamp to ride `npc.edge_published`, so Dev must ADD that emission on the opposed path. Affects `sidequest/server/narration_apply.py` (`_resolve_opposed_check_branch`, ~line 5355 where `opponent_actor` is resolved). *Cleanest wiring:* route the opponent presence-stamp through the existing `encounter_lifecycle._publish_combat_edge_to_npcs`, which already both stamps `last_seen_*` AND emits `npc.edge_published` (reuses 72-8 — Don't Reinvent). If a different span is genuinely more appropriate for the social seam, log a deviation and update `test_72_12_presence_beyond_combat.py::test_opposed_check_presence_stamp_rides_npc_edge_published_span`. *Found by TEA during test design.*
- **Improvement** (non-blocking): `participant_joined_span` (`spans/encounter.py:535`) already accepts `**attrs`, so AC4 needs only the two kwargs passed at the call site (`encounter_lifecycle.py:1060`) plus the `Npc` mutation in the same loop — no span-signature change required. The session note about "extend signature" is unnecessary. *Found by TEA during test design.*
- **Gap** (non-blocking): the participant_joined seam (loop at `encounter_lifecycle.py:1059`) fires for EVERY seated actor on EVERY encounter type, including combat. Dev must stamp only actors that resolve to a roster `Npc` (skip PC-side / non-roster actors — No Synthetic NPCs), and must not double-stamp combat opponents already handled by the 72-8 seams in a way that produces conflicting turn/location (they share the same `turn`/`party_location`, so a consistent value is expected — see 72-8's `test_present_and_prose_mentioned_same_turn_one_consistent_stamp` for the precedent). *Found by TEA during test design.*

### Dev (implementation)
- No upstream findings during implementation. All three TEA findings were resolved in-band: Seam 1 emits `npc.edge_published` via the shared stamp primitive (not the HP-clobbering wrapper — see Dev deviation); Seam 2 rides `participant.joined` `**attrs` with no signature change; the loop stamps only roster-`Npc` actors and combat opponents stay consistent under the 72-8 re-stamp (72-8 suite green). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): both presence-stamp seams (and the original 72-8 seams) silently no-op with NO OTEL signal when the seated opponent/participant has no backing `Npc` in `snapshot.npcs`. Per the epic-72 "every leg needs OTEL" doctrine, a missing-NPC skip should emit a degraded span (e.g. `source="opposed_check_npc_missing"`) so the GM panel can see the gap rather than silent absence. Affects `sidequest/server/narration_apply.py` (`_resolve_opposed_check_branch` else-of-`opp_npc`) and `encounter_lifecycle.py` (participant loop). Recommend addressing uniformly across all four seams as epic NPC-identity work, not in this 3pt story. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Seam-1 span `current`/`max` dial-inversion gates on `_thresh > 0` rather than `win_condition`; harmless today (no `opposed_check` + `hp_depletion` content) but would misreport the 1,000,000 inert-placeholder pool if such a confrontation is ever authored. Affects `sidequest/server/narration_apply.py:5919`. *Found by Reviewer during code review.*
- **Gap** (blocking, Review 2): seam-2's `participant.joined` span `last_seen_location` is never discriminatingly tested — AC4 is co-located (tautological) and the router-named test omits span capture. Affects `tests/server/dispatch/test_72_12_presence_beyond_combat.py` (add a router-named OTEL span-location assertion). *Found by Reviewer during code review (Review 2).* → **RESOLVED in rework #2** (router-named test now asserts the span discriminatingly).
- **Improvement** (non-blocking, Review 3): AC4's *span* `last_seen_location` assertion is co-located/redundant — add a "co-location invariant" comment to match AC3, for clarity (coverage is complete via the router-named test). Affects `tests/server/dispatch/test_72_12_presence_beyond_combat.py`. *Found by Reviewer during code review (Review 3).*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

5 deviations

- **Opposed_check tests run against the real `tea_and_murder` content pack, not a synthetic fixture pack**
  - Rationale: the synthetic fixture pack has no `opposed_check` confrontation with authored beats + `opponent_default_stats`; `resolve_opposed_check`/`resolve_opponent_modifier` fail loud without them, so an opposed_check social seam cannot be exercised on the synthetic pack. The real-content + skipif pattern is the established precedent for this seam.
  - Severity: minor
  - Forward impact: these 6 tests skip in any environment without the content sibling checked out; the 72-8 combat-seam tests (synthetic) remain the always-on coverage.
- **AC6 (no regression on 72-8 combat seams) is covered by the existing 72-8 suite, not a new duplicate test**
  - Rationale: re-implementing the 72-8 assertions here would duplicate coverage and drift from the canonical suite; AC6 is a regression guard satisfied by keeping that suite green.
  - Severity: minor
  - Forward impact: none — AC6 is enforced by running both files in the same suite.
- **Review rework: AC3/AC4 location proof handled via a router-named test, NOT the Reviewer's literal `_STALE_LOC` fixture fix**
  - Rationale: applying the literal fix broke the tests with `NoOpponentAvailableError` — the location-FALLBACK seating path (`_npc_fallback_at_location`) only seats an NPC whose `last_seen_location` ALREADY equals the player's location, so a fallback-seated NPC is co-located *by construction* and its location cannot differ before/after. The Reviewer's underlying concern (seam-2 location-write unverified) is valid and is now genuinely covered by the router-named test where co-location is not required; AC3/AC4's discriminating proof for the fallback path is the TURN advance, documented inline. (Receiving-code-review discipline: verified the suggested fix before implementing, found it incorrect, addressed the real concern.)
  - Severity: minor
  - Forward impact: none — coverage strengthened (7 tests, 2×2 seating-source × location-resolved matrix closed).
- **Reused the 72-8 stamp primitive `_stamp_encounter_presence` instead of routing Seam 1 through `_publish_combat_edge_to_npcs`**
  - Rationale: `_publish_combat_edge_to_npcs` OVERWRITES the opponent's `core.hp` pool from the dial (`npc.core.hp.max = threshold; current = max(1, threshold - dial)`) — a combat-specific mutation that is wrong for a non-combat social duel (it would reset Sir Iain's HP to the barbs-landed dial). Reusing only the stamp primitive + span gets AC1+AC2 (same span family, same write discipline) with no spurious HP side effect. The span still surfaces the social dial as its `current`/`max` (inverted, same convention) so the GM-panel pool view stays honest.
  - Severity: minor
  - Forward impact: none — same span name (`npc.edge_published`) and same `_stamp_encounter_presence` discipline as the combat seams; the AC2 test asserts the span + attrs, which pass.
- **Seam 2 presence stamp fires for ALL roster-NPC actors at seating, any side (not only opponents)**
  - Rationale: doctrine is presence, not hostility — an allied/neutral NPC joining a parley is just as "present" and must not be mis-evicted by 72-6's prune. Stamping any roster NPC is the literal reading of "presence means presence."
  - Severity: minor
  - Forward impact: combat opponents are stamped here at seating AND re-stamped by the 72-8 combat seams below with the same turn + location — consistent value, no double-advance (verified: 72-8 suite stays green).

## Implementation Notes

### Key Source Files

- **narration_apply.py** — `_resolve_opposed_check_branch` function (line ~5214); search for `opponent_actor` and `apply_beat` calls to locate where NPC mutations happen
- **encounter_lifecycle.py** — `participant_joined_span` emission (line ~1060); the context manager where actors are seated
- **spans/npc.py** — `npc_edge_published_span` definition; current spec for presence-stamp attributes
- **spans/encounter.py** — `participant_joined_span` definition; will need to extend signature to accept `last_seen_turn`/`last_seen_location` as `**attrs`

### Test Pattern (from 72-8)

From `tests/server/dispatch/test_72_8_presence_last_seen_stamp.py`:

```python
def test_dial_presence_stamps_last_seen_without_prose_mention() -> None:
    """Unit test: presence at encounter seam advances last_seen_turn/location"""
    snap = GameSnapshot(...)
    npc = _make_npc("Name", location="Place", turn=old_turn)
    snap.npcs.append(npc)
    
    _publish_combat_edge_to_npcs(...)  # or equivalent path for new seams
    
    assert npc.last_seen_turn == expected_turn
    assert npc.last_seen_location == expected_location

def test_dial_presence_stamp_rides_npc_edge_published_span(otel_capture) -> None:
    """OTEL test: span carries presence-stamp attributes"""
    snap = GameSnapshot(...)
    npc = _make_npc("Name", location="Place", turn=old_turn)
    snap.npcs.append(npc)
    
    _publish_combat_edge_to_npcs(...)  # or equivalent path
    
    edge_spans = [s for s in otel_capture.get_finished_spans() if s.name == "npc.edge_published"]
    assert edge_spans[0].attributes.get("last_seen_turn") == expected_turn
    assert edge_spans[0].attributes.get("last_seen_location") == expected_location
```

### No Silent Fallbacks

- If the acting player has no resolved location, stamp the turn but freeze the location (as in 72-8)
- If the NPC is not found in the snapshot, log + skip (do NOT create a synthetic NPC)
- If the span context manager fails to emit, fail loud (existing infrastructure will surface)

## TEA Assessment

### Red Phase (test writing)

**Tests Required:** Yes
**Reason:** Behavioral story — two new presence-stamp seams + OTEL. Not a chore.

**Test Files:**
- `tests/server/dispatch/test_72_12_presence_beyond_combat.py` — 6 tests across both seams, driven through production call paths (no private-helper calls; no source-text wiring assertions, per server CLAUDE.md).

**Tests Written:** 6 tests covering 6 ACs (AC6 = regression guard, satisfied by the existing 72-8 suite — see Design Deviations).

| AC | Test | Seam | Asserts |
|----|------|------|---------|
| AC1 | `test_opposed_check_social_stamps_presence_without_prose_mention` | opposed_check | NPC `last_seen_turn`→5, `last_seen_location`→hall, no prose mention; via real resolution handshake (wiring) |
| AC2 | `test_opposed_check_presence_stamp_rides_npc_edge_published_span` | opposed_check | a `npc.edge_published` span carries `last_seen_turn`/`last_seen_location` |
| AC3 | `test_participant_joined_stamps_presence_on_seating` | participant_joined | non-combat seating stamps `last_seen_*`; 72-8 combat seams gated OFF (isolation) |
| AC4 | `test_participant_joined_stamp_rides_participant_joined_span` | participant_joined | the NPC's `participant.joined` span carries `last_seen_turn`/`last_seen_location` |
| AC5 | `test_opposed_check_no_resolved_location_stamps_turn_not_location` (seam 1) + `test_participant_joined_no_resolved_location_stamps_turn_not_location` (seam 2) | both | turn advances, `last_seen_location` FROZEN when `party_location` is None (No Silent Fallbacks) |
| AC6 | existing `test_72_8_presence_last_seen_stamp.py` | combat (72-8) | 6 passed in RED run — no regression baseline |

**Status:** RED confirmed (testing-runner, `-n0` serial for OTEL):
- New file: **6 failed** — every failure is a real `last_seen_turn` assertion (stale value `2` persists; feature not implemented). Collection clean (`--collect-only` → 6 collected, 0 errors).
- 72-8 regression: **6 passed** (AC6 baseline intact).

### Rule Coverage

| Rule (python.md) | Test(s) | Status |
|------------------|---------|--------|
| #4 No-Silent-Fallback (unresolved location must not clobber) | both `*_no_resolved_location_stamps_turn_not_location` | failing (RED) |
| #6 Test quality (meaningful, value-specific assertions) | self-check, all 6 | pass — every assert checks a specific value, not a truthy/`is_none` |

**Rules checked:** 2 of 13 lang-review rules are applicable to this small behavioral change; the rest (mutable defaults, unsafe deserialization, async, SQL/path injection, deps) have no surface in a presence-stamp + span-attr change.
**Self-check:** 0 vacuous tests found — no `assert True`, no `let _ =`, no truthy-only checks; OTEL tests assert specific attribute values, AC5 tests assert the frozen location equals the distinct prior value (`The Old Library`, deliberately ≠ the player's hall so a no-op can't pass).

**Handoff:** To Dev (Agent Smith) for GREEN implementation. Wiring guidance in Delivery Findings — prefer reusing `_publish_combat_edge_to_npcs` for the opposed_check seam (stamps + emits `npc.edge_published` in one call).

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/server/narration_apply.py` — Seam 1: `_resolve_opposed_check_branch` now stamps the seated opponent NPC's `last_seen_turn`/`last_seen_location` (via the shared `_stamp_encounter_presence` primitive) and emits a `npc.edge_published` span carrying the stamp, before returning. ~30 added lines before the `return`.
- `sidequest/server/dispatch/encounter_lifecycle.py` — Seam 2: the `participant_joined` loop now resolves the seating turn + location once, and for each seated actor that matches a roster `Npc` stamps presence and passes `last_seen_turn`/`last_seen_location` as `**attrs` on the `participant.joined` span.

**Approach:** Reused 72-8's shared `_stamp_encounter_presence` write-discipline primitive on both seams (single-sourced No-Silent-Fallback rule: turn always advances, location only when resolved). Deliberately did NOT route Seam 1 through `_publish_combat_edge_to_npcs` — it would overwrite the social opponent's `core.hp` from the dial (logged as a Dev deviation).

**Tests:** 6/6 new GREEN; 72-8 regression 6/6 GREEN (AC6); broader sweep (glenross opposed_check + encounter_lifecycle + opposed_check_wiring) 38 passed / 6 skipped / 0 failed. `ruff check` clean on both files. `pyright` errors are all pre-existing in `narration_apply.py` (none on the new lines).

**OTEL:** Both seams emit (AC2 `npc.edge_published`, AC4 `participant.joined`) so the GM-panel lie-detector can confirm presence-stamping fired — epic-72 "every leg needs OTEL" satisfied.

**Branch:** `feat/72-12-presence-stamp-beyond-combat` (pushed)

**Handoff:** To TEA (The Architect) for the verify phase (simplify + quality-pass).

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None (2 pre-logged Dev deviations reviewed and endorsed)

All 6 ACs verified against the diff (`git diff develop...HEAD`):
- AC1/AC2 — Seam 1 (`_resolve_opposed_check_branch`) stamps the seated opponent via `snapshot.npcs` lookup + `_stamp_encounter_presence`, emits `npc.edge_published` with the `last_seen_*` attrs. Reached through the production resolution path (test drives `_apply_narration_result_to_snapshot`, `narration=""` proves the prose-independent path). ✅
- AC3/AC4 — Seam 2 (`instantiate_encounter_from_trigger` participant loop) stamps each seated roster-`Npc` and rides the stamp on `participant.joined` via `**attrs`. Non-combat isolation confirmed (combat-edge seams gate on `cdef.category == "combat"`). ✅
- AC5 — both seams delegate the write to `_stamp_encounter_presence`, which writes location only `if location:`; `party_location()==None` freezes location, advances turn. ✅
- AC6 — 72-8 suite 6/6 green; combat opponents are re-stamped at the 72-8 seams with the same `turn`/`party_location`, so the seating-time stamp is consistent (no double-advance). ✅

**Reviewed deviations (both endorsed — Option A, accept):**
- *Reused `_stamp_encounter_presence` over `_publish_combat_edge_to_npcs`* (Behavioral, Minor): the wrapper overwrites the social opponent's `core.hp` from the dial — a combat-only side effect that would be a genuine bug on the social path. Reusing the smaller primitive is the correct reuse-first call and single-sources the No-Silent-Fallback discipline. Endorsed.
- *Seam 2 stamps any roster-NPC actor, not only opponents* (Behavioral, Minor): this is the literal reading of "presence means presence" — an allied/neutral NPC joining a parley is equally present and must not be mis-evicted by 72-6's prune. PC-side actors no-op (not in `snapshot.npcs`). Endorsed.

**Architectural observations (Trivial — not blocking):**
- Cross-module import of the underscore-private `_stamp_encounter_presence` (encounter_lifecycle → imported into narration_apply) is a soft coupling smell, mitigated by a local in-function import (no module-level cycle). With now **two** consumers beyond its origin (both 72-8 combat seams + this story's two seams), it is approaching Rule-of-Three: a future refactor could promote it to a neutral presence/recency module with a public name. Out of scope for a 3pt bug — **Defer (Option D)**, no action this story.
- The Seam-1 span's `current`/`max` reuse the dial-inversion convention from the dial combat seam (honest GM-panel pool view), with a `core.hp` fallback when no opponent metric exists. Sound; required positional args filled meaningfully rather than with placeholders.

**Decision:** Proceed to review (verify phase, TEA).

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 3 (`narration_apply.py`, `encounter_lifecycle.py`, `test_72_12_presence_beyond_combat.py`)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 2 findings (both low-confidence) | Cross-file + in-loop stamp/emit pattern echoes 72-8; reuse via `_stamp_encounter_presence` is intentional. A future micro-helper (`_emit_npc_recency_on_presence`) is *possible* only if 72-12 proves stable across playtests — extracting now would over-couple fresh logic to the mature 72-8 seams and blur the two distinct span families (`npc.edge_published` vs `participant.joined`). |
| simplify-quality | clean | Local in-function imports match the established `narration_apply` pattern; `_`-prefixed locals consistent with surroundings; no dead/unreachable code; comment density appropriate. |
| simplify-efficiency | clean | The dial-inversion + `core.hp` fallback (Seam 1) is *necessary* — opposed_check (unlike combat) doesn't guarantee an opponent metric. Per-seam `_npc_by_name` rebuild and conditional `_stamp_attrs` splat both mirror the proven 72-8 pattern; micro-optimizing would diverge for negligible gain. |

**Applied:** 0 high-confidence fixes (none surfaced).
**Flagged for Review:** 0 medium-confidence findings.
**Noted:** 2 low-confidence reuse observations (deferred — Rule-of-Three not yet met; revisit if a third consumer appears, consistent with Neo's spec-check note).
**Reverted:** 0.

**Overall:** simplify: clean

**Quality Checks:** All passing — `pytest -n0` 12 passed (6 new 72-12 + 6 regression 72-8), `ruff check` clean on both changed source files, working tree clean. No code modified in the verify phase, so the GREEN state and AC6 regression baseline are unchanged from green/spec-check.

**Handoff:** To Reviewer (The Merovingian) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (12 passed, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 6 | confirmed 0 blocking, deferred 6 (all mirror 72-8 precedent or unreachable) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 | deferred 2 (mirror 72-8 no-op + adjacent line-1191 guard) |
| 4 | reviewer-test-analyzer | Yes | findings | 5 | **confirmed 2 blocking** (1 HIGH, 1 MEDIUM), deferred 3 |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | clean | 0 | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (5 enabled returned, 4 disabled pre-filled)
**Total findings:** 2 confirmed blocking, 0 confirmed non-blocking added, 10 deferred/dismissed with rationale

### Rule Compliance

Project rules checked (`.pennyfarthing/gates/lang-review/python.md`; SOUL.md; server CLAUDE.md):
- **#1 silent exceptions** — no new try/except; no swallow. Compliant.
- **#4 No Silent Fallbacks / logging** — `if location:` freeze is the *intended* discipline (reuses 72-8 `_stamp_encounter_presence`). The two no-op skips (seam-1 `opp_npc is None`, seam-2 non-roster actor) match the accepted 72-8 sibling no-ops (`_publish_combat_edge_to_npcs:360`). Compliant-by-precedent; see deferred [SILENT] for an OTEL-honesty improvement.
- **#6 test quality** — **VIOLATION**: AC3/AC4 tautological location assertions; AC2 dead filter key. See blocking findings.
- **OTEL Observability Principle** — both seams emit spans (`npc.edge_published`, `participant.joined`) carrying the stamp. Compliant for the happy path; the no-NPC skip emits nothing (deferred).
- **No Source-Text Wiring Tests** — tests drive production paths + assert spans/state; no `read_text()`/regex-on-source. Compliant.
- **#2/#3/#5/#7/#8/#9/#10/#11/#12** (mutable defaults / annotations / paths / resources / deserialization / async / imports / input-validation / deps) — no surface in this diff. N/A.

### Observations (tagged)

- `[TEST]` **[HIGH]** Seam-2 location stamping is tautologically asserted — `test_72_12_presence_beyond_combat.py:297` (AC3) and `:325` (AC4) init the NPC `location=_HALL` while the player is also at `_HALL`, so `assert last_seen_location == _HALL` passes even on a no-op stamp. The story's core location-stamp deliverable at the participant_joined seam is **unverified** (only the turn 2→6 is proven). Evidence: line 297 `_make_opponent_npc(location=_HALL, ...)` + line 296 `character_locations[_PLAYER] = _HALL` + line 311 assert.
- `[TEST]` **[MEDIUM]** AC2 span filter uses the wrong attribute key — `:241` filters `(...).get("name") == _OPPONENT`, but `npc_edge_published_span` stores the name under `npc_name` (`telemetry/spans/npc.py` builds `{"npc_name": ...}`; watcher reads `.get("npc_name")`). The comprehension is always `[]`, and `or edge_spans` silently falls back to all spans — a dead filter that passes only because exactly one `npc.edge_published` span fires.
- `[EDGE]` **[LOW, deferred]** Seam-1 dial-inversion (`narration_apply.py:5919`) uses `_thresh > 0` rather than a win_condition gate; an `opposed_check` + `hp_depletion` encounter would show the 1,000,000 inert-placeholder pool. **Verified unreachable** — no content pairs `opposed_check` resolution with `hp_depletion` win_condition (grep clean); `social_duel` carries a real dial (threshold 7). Robustness note only.
- `[EDGE]/[SILENT]` **[LOW, deferred]** Duplicate `core.name` collision in `{n.core.name: n}` (seam 2, `:1073`) and `next(...)` first-match (seam 1, `:5906`). **Pre-existing 72-8 pattern** (`encounter_lifecycle.py:172,355`); an epic-72 identity-hardening theme, out of scope for this 3pt stamp story.
- `[SILENT]` **[LOW, deferred]** `hasattr(snapshot, "turn_manager")` guard (`:1069`) is effectively dead (GameSnapshot always has the field) but **mirrors the adjacent 72-8 code at `:1191`** — local consistency. No production impact.
- `[SILENT]` **[LOW, deferred → Delivery Finding]** Seam-1 `if opp_npc is None` skips stamp AND span with no OTEL signal. Mirrors the accepted 72-8 no-op; materializing a missing social opponent is epic NPC-identity scope. Logged as an Improvement.
- `[VERIFIED]` Seam-1 insertion point is safe — the only non-fall-through paths in `_resolve_opposed_check_branch` are `raise` statements (`narration_apply.py:5284,5302,5310,5326,5357,5363`) that abort the whole turn; `opponent_actor` is guaranteed non-None by the guard at `:5357`. No early `return` skips the stamp. Complies with No-Silent-Fallbacks (raises are loud).
- `[VERIFIED]` `max(1, _thresh - current)` over-cap clamp (`:5923`) mirrors 72-8 `_publish_combat_edge_to_npcs:349` exactly — consistent-by-design, not a new defect.
- `[SEC]` clean — no injection/secrets/PII surface; OTEL attrs are game content (NPC names, in-game locations), `int(getattr(...) or 0)` fails loud on garbage. Confirmed by reviewer-security.
- `[SIMPLE]` n/a — reviewer-simplifier disabled; verify-phase simplify already ran clean (0 high-confidence).
- `[DOC]` n/a — reviewer-comment-analyzer disabled; comments are accurate and explain "why" (preflight noted no doc smells).
- `[TYPE]` n/a — reviewer-type-design disabled; no new public types/signatures (changes are inside existing functions; `dict[str, object]` annotation present).
- `[RULE]` n/a — reviewer-rule-checker disabled; manual Rule Compliance section above covers the lang-review checklist.

### Devil's Advocate

Argue the code is broken. The most damning case: **this story claims to stamp `last_seen_location` at the participant_joined seam, and the test suite never proves it does.** Both AC3 and AC4 seat the NPC with a prior location identical to the player's location (`_HALL`), so a reviewer trusting green checks would certify location-stamping that could be entirely absent — if a future refactor dropped the `_stamp_encounter_presence` call from seam 2, every test would still pass. That is the exact failure mode SideQuest's whole OTEL/lie-detector culture exists to prevent: convincing green with no mechanical backing. A confused maintainer reading AC3 would assume `_HALL` was chosen deliberately (it was not — it was the bug). Compounding it, the AC2 span filter looks like it pins the span to the right NPC but silently matches nothing and falls back to "any span" — so if a second `npc.edge_published` span ever fires earlier in that path (entirely plausible as the engine grows), AC2 would assert a *different* NPC's attributes and either mislead or pass for the wrong reason. A malicious or careless content author who sets `character_locations[player] = ""` would hit the `if location:` falsy path and freeze a stale location silently — defensible per No-Silent-Fallbacks, but untested. Under a stressed roster with duplicate NPC names (epic-72's literal raison d'être), the dict-comprehension drops all but the last duplicate, stamping the wrong record — though that mirrors 72-8 and is the epic's separate problem. The production code, on inspection, actually works; but a test suite that can't tell a working stamp from a no-op on the headline feature is not acceptable on a story whose entire point is presence-stamping. This is a test-integrity rejection, not a code rejection.

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] `[TEST]` | Seam-2 location stamping tautologically asserted — NPC init `location=_HALL` == player loc == expected post-stamp value, so the assertion passes on a no-op. Location stamping at the participant_joined seam is unverified. | `tests/server/dispatch/test_72_12_presence_beyond_combat.py:297` (AC3), `:325` (AC4) | Init the NPC with `location=_STALE_LOC` in both AC3 and AC4 (player stays at `_HALL`); keep the `== _HALL` assertions so they now prove the stamp wrote the new value. |
| [MEDIUM] `[TEST]` | AC2 span filter uses wrong key `.get("name")` (span stores `npc_name`); `or edge_spans` fallback masks the dead filter. | `tests/server/dispatch/test_72_12_presence_beyond_combat.py:241` | Use `.get("npc_name") == _OPPONENT`; drop the `or edge_spans` fallback so a non-match fails loudly. |

Both are test-only fixes — **production code is correct** (verified by read-through + 5 subagents). No source change required. Rework belongs to TEA (red phase: strengthen the failing-then-passing assertions).

**Optional (non-blocking, recommend bundling):** add a router-named + resolved-location seam-2 test to close the 2×2 (seating-source × location-resolved) matrix; the only router-named coverage today is the no-location AC5 case.

**Data flow traced:** opposed_check resolution → `_resolve_opposed_check_branch` finds `opp_npc` in `snapshot.npcs` → `_stamp_encounter_presence` writes turn (always) + location (if resolved) → `npc_edge_published_span` emits — safe; no early return bypasses it.
**Pattern observed:** correct reuse of 72-8's `_stamp_encounter_presence` primitive at both seams (`encounter_lifecycle.py:1078`, `narration_apply.py:5915`).
**Specialist findings incorporated:** `[TEST]` 2 confirmed blocking (tautology + wrong key). `[EDGE]` 6 (hp_depletion placeholder, dup-name collision, hasattr guard — all deferred/unreachable). `[SILENT]` 2 (no-NPC skip OTEL, hasattr default — deferred, mirror 72-8). `[SEC]` clean. `[DOC]`/`[TYPE]`/`[SIMPLE]`/`[RULE]` n/a — disabled.
**Handoff:** Back to TEA (The Architect) for test rework.

> NOTE: This is the Review-1 (REJECTED) assessment. The authoritative final verdict is **APPROVED** — see `## Reviewer Assessment (Review 3)` below.

## TEA Assessment (red rework — review response)

**Phase:** finish (rework after Reviewer REJECT)
**Status:** Both blocking findings resolved; tests strengthened and GREEN.

**Reviewer findings addressed:**
1. **[HIGH] Seam-2 location stamping tautological (AC3/AC4)** — Resolved, but NOT via the literal `_STALE_LOC` fixture swap (that broke seating with `NoOpponentAvailableError`: the location-fallback path requires the NPC to already be co-located). The real concern — seam-2 location-write unverified — is now covered by a NEW `test_participant_joined_router_named_stamps_location` (router-named seating, prior `_STALE_LOC` → assert `_HALL`), where co-location isn't required so the write is genuinely proven. AC3/AC4 keep co-located fixtures with the discriminating TURN assertion and an inline comment explaining the invariant. See the TEA deviation entry.
2. **[MEDIUM] AC2 wrong span-filter key** — Fixed: filter `npc.edge_published` spans on `npc_name` (the real attribute key) and `assert stamped` (fail loud) instead of the masking `or edge_spans` fallback.

**Coverage:** 7 tests (was 6), closing the 2×2 seating-source (location-fallback / router-named) × location-resolved (yes / no) matrix.

**Verification:** `pytest -n0` — 7/7 GREEN on 72-12, 6/6 GREEN on 72-8 regression, `ruff` clean. No production code changed (the implementation was correct; only the tests were strengthened).

**Handoff:** To Dev (Agent Smith) for the green gate (confirm GREEN — no implementation needed).

## Dev Assessment (green rework #2)

**Implementation Complete:** Yes (no production change required) — TEA's Review-2 rework added a span-layer OTEL assertion to the router-named test + an AC2 `len==1` guard, all test-only. Production seams unchanged and correct. 13 passing (7 × 72-12 + 6 × 72-8), ruff clean, tree clean. Handoff to Architect (Neo) for spec-check.

## Dev Assessment (green rework)

**Implementation Complete:** Yes (no production change required)
**Files Changed this cycle:** none — TEA's review rework touched only `tests/server/dispatch/test_72_12_presence_beyond_combat.py`. The production seams (`narration_apply.py`, `encounter_lifecycle.py`) were correct as reviewed; the Reviewer's findings were test-integrity defects, now fixed.

**Tests:** 13 passing (7 × 72-12 + 6 × 72-8 regression), `ruff` clean on all three files, working tree clean.

**Deviations:** No new Dev deviations this cycle (the only deviation in the rework was TEA's, logged under `### TEA (test design)`).

**Handoff:** To Architect (Neo) for spec-check re-validation.

## Architect Assessment (spec-check — rework #2 re-validation)

**Spec Alignment:** Aligned · **Mismatches:** None

Re-validation after Reviewer REJECT #2 + TEA rework. Delta is test-only (`git diff` since prior pass = `test_72_12_presence_beyond_combat.py` only); production seams unchanged and still endorsed. The rework added the discriminating span-layer location assertion to the router-named test (`otel_capture` → `participant.joined` span `last_seen_location == _HALL`, discriminating via `_STALE_LOC` start) plus an AC2 `len==1` guard. This closes the OTEL-coverage gap on the seam-2 span layer without any spec change — the ACs are unchanged and remain satisfied. No drift. **Decision:** Proceed to verify (TEA).

---

## Architect Assessment (spec-check — rework re-validation)

**Spec Alignment:** Aligned
**Mismatches Found:** None

Re-validation after the Reviewer REJECT + TEA red rework. The only delta since the prior spec-check is **test-only** (`test_72_12_presence_beyond_combat.py`); production seams are byte-for-byte unchanged and remain endorsed. Confirmed:
- AC2 now filters `npc.edge_published` on the real `npc_name` key (was a dead `name` filter) — the OTEL verification is now genuine.
- AC3/AC4 reverted to co-located fixtures with an inline invariant comment, and the seam-2 location-WRITE proof relocated to the new `test_participant_joined_router_named_stamps_location`. This is architecturally the *correct* resolution: the location-fallback seating path requires co-location by construction, so the discriminating proof there is the turn advance — TEA's deviation from the Reviewer's literal `_STALE_LOC` suggestion is sound and logged.
- Coverage closed to the full 2×2 (seating-source × location-resolved) matrix.

No spec drift; the ACs are unchanged and the implementation still satisfies them. TEA's rework deviation reviewed and endorsed (Option A).

**Decision:** Proceed to verify (TEA).

## TEA Assessment (verify — rework #2 re-validation)

**Phase:** finish (re-run after rework #2)
**Status:** GREEN confirmed

### Simplify Report
Scope: test-file delta only (production byte-identical, prior simplify-clean verdict carries).
- **simplify-quality:** 1 medium consistency finding — **APPLIED**: AC4 + router-named `participant.joined` span asserts now carry `assert len(iain) == 1`, matching AC2's double-emit guard. Committed (`75dc887`).
- reuse/efficiency: carried clean (no new surface).

**Applied:** 1 (consistency guard). **Reverted:** 0. **Overall:** simplify: applied 1 fix.

**Quality Checks:** GREEN — 13 passing (7 × 72-12 + 6 × 72-8), `ruff` clean, tree clean. Regression re-run after the fix confirmed the `len==1` guards hold (single span per opponent).

**Handoff:** To Reviewer (The Merovingian) — Review 3.

---

## TEA Assessment (verify — rework re-validation)

**Phase:** finish (re-run after review rework)
**Status:** GREEN confirmed

### Simplify Report

Scope: only `test_72_12_presence_beyond_combat.py` changed since the prior clean verify (production seams byte-identical to commit `f54a7ac` — their prior simplify-clean verdict carries forward).

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 1 low | The new `test_participant_joined_router_named_stamps_location` overlaps AC5's router-named setup, but documents an **orthogonal matrix cell** (location-resolved vs unresolved); consolidation would obscure intent. Keep separate — no extraction. |
| simplify-quality | clean | Comments accurate (AC2 `npc_name` key, AC3/AC4 co-location invariant), fail-loud `assert stamped`, naming consistent, no dead code. |
| simplify-efficiency | n/a (carried) | Production unchanged since the prior clean efficiency pass; test delta has no efficiency surface. |

**Applied:** 0 fixes. **Flagged:** 0. **Reverted:** 0.
**Overall:** simplify: clean

**Quality Checks:** GREEN — 13 passing (7 × 72-12 + 6 × 72-8), `ruff` clean on both production files + the test file, working tree clean.

**Handoff:** To Reviewer (The Merovingian) — re-review of the strengthened tests.

## Subagent Results (Review 2)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (13 passed, both prior fixes clean) | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 4 | **confirmed 1 blocking** (span-location gap, HIGH), deferred 3 |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 | confirmed 0 blocking (AC3 bare-message = same gap, folded), deferred 1 |
| 4 | reviewer-test-analyzer | Yes | findings | 3 | prior 2 RESOLVED; **confirmed 1 blocking** (router-named OTEL), 1 deferred |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | clean | 0 | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (5 enabled returned, 4 disabled pre-filled)
**Total findings:** 1 confirmed blocking (corroborated by 3 specialists), 1 medium folded as recommended, rest deferred/dismissed.

**Scope note:** production code is byte-identical to Review 1 (`git diff f54a7ac...HEAD` → test file only); the Review-1 production coverage (edge/silent/security on the seams) stands. This pass re-scopes the diff-based specialists to the test delta.

### Rule Compliance (Review 2)

- **#6 test quality / OTEL Observability Principle** — **VIOLATION (residual)**: seam-2's `participant.joined` span `last_seen_location` is never discriminatingly asserted (AC4 co-located → tautological; router-named test omits the span). AC4's stated purpose ("the stamp rides the span") is only half-delivered for location. Prior AC2/AC3 violations are RESOLVED.
- All other rules: unchanged from Review 1 (production identical) — compliant.

### Observations (tagged)

- `[TEST]`/`[EDGE]` **[HIGH]** Seam-2 OTEL span `last_seen_location` discriminating proof missing — `:380` (AC4) asserts `== _HALL` but the NPC is co-located at `_HALL` (tautological, same class as the original AC3/AC4 object-layer defect); the new router-named test (`:415`) proves the OBJECT write but uses no `otel_capture` and never asserts the `participant.joined` span. Corroborated by edge-hunter (HIGH), test-analyzer (MEDIUM), silent-failure-hunter (HIGH on the related AC3 vacuity). The OTEL span is epic-72's load-bearing lie-detector. Evidence: `:353` inits `location=_HALL`, `:380` asserts span `==_HALL`; `:415-447` has no span capture.
- `[EDGE]` **[MEDIUM, fold-in]** AC2 uses `stamped[0]` without `assert len(stamped) == 1` (`:252`) — a double-emit of `npc.edge_published` for the opponent would hide behind the first element. Cheap guard; bundle with the blocking fix.
- `[TEST]` **[RESOLVED]** Prior AC2 wrong-key finding — now `.get("npc_name")` + fail-loud `assert stamped`, no masking fallback. Verified `:244-252`.
- `[TEST]` **[RESOLVED]** Prior AC3/AC4 object-layer tautology — object-write now discriminatingly proven by AC1 (`:200`→`:209`) and the router-named test (`:429`→`:444`); AC3/AC4 co-location documented.
- `[VERIFIED]` Production unchanged — `git diff f54a7ac...HEAD` is test-only; the seams cleared in Review 1 are intact.
- `[SEC]` clean (reviewer-security) — test-only delta, no secrets/PII; actually removes a silent fallback.
- `[SILENT]` AC2 `or edge_spans` masking fallback removed — confirmed fail-loud now.
- `[SIMPLE]`/`[DOC]`/`[TYPE]`/`[RULE]` n/a — subagents disabled; manual Rule Compliance above; verify-phase simplify ran clean on the test delta.

### Devil's Advocate

Argue the suite still lies. AC4 is titled "the participant_joined presence stamp is surfaced on the span" — yet its `last_seen_location` assertion runs against an NPC already standing in `_HALL`, so the span attribute equals `_HALL` whether the production code wrote it or passed an empty `**attrs`. Strip `_stamp_attrs` from the `participant_joined_span` call entirely and AC4 still goes green on location (only the turn would fail). That is the precise failure mode that earned the first rejection, surviving at the span layer. The new router-named test looked like the fix — but it captures no spans at all, so it cannot see whether the lie-detector actually reports the written location to the GM panel; it only inspects the in-memory object. A maintainer could regress the span emission (e.g. pass the pre-stamp location, or drop the location key) and every test here stays green because the only discriminating location proof lives on the object, not the span. For a story whose AC4 exists specifically to make the span the witness, leaving the witness's location testimony unverified is the same hollow-green the first review rejected. The fix is one test: give the router-named test `otel_capture`, find the `participant.joined` span for the opponent, assert `last_seen_location == _HALL` — discriminating because the NPC starts at `_STALE_LOC`. While there, guard AC2 with `assert len(stamped) == 1` so a double-emit can't hide a stale second span. The production code is almost certainly correct (turn and location ride the same dict, and the turn is proven) — but "almost certainly correct" is what OTEL assertions exist to retire.

## Reviewer Assessment (Review 2)

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] `[TEST]` | Seam-2 OTEL span `last_seen_location` is never discriminatingly asserted — AC4's span location assertion is tautological (co-located `_HALL`), and the router-named test proves only the object write (no span capture). AC4's purpose ("stamp rides the span") is unmet for location; the OTEL lie-detector for location is unverified. | `test_72_12_presence_beyond_combat.py:380` (AC4, tautological) + `:415` (router-named, no span) | Add `otel_capture` to `test_participant_joined_router_named_stamps_location` (NPC starts at `_STALE_LOC`), find the `participant.joined` span for `_OPPONENT`, and `assert last_seen_location == _HALL` — a discriminating span proof. (Equivalently, a new AC4-variant OTEL test for the router-named path.) |
| [MEDIUM] `[EDGE]` | AC2 uses `stamped[0]` without asserting exactly one `npc.edge_published` span for the opponent — a double-emit hides behind the first element. | `test_72_12_presence_beyond_combat.py:252` | Add `assert len(stamped) == 1, ...` before indexing. Bundle with the blocking fix. |

Both are **test-only** fixes — production code is correct and unchanged. Rework belongs to TEA (red).

**Optional polish (non-blocking):** AC3's co-location assertion (`:334`) is a bare `assert` with no message — add a diagnostic string clarifying it's an invariant check, not the write-proof.

**Prior findings:** both RESOLVED and verified. This rejection is the SAME defect class (tautological location proof) surviving at the OTEL-span layer; fixing it converges (object + span both discriminatingly proven, no third layer).

**Handoff:** Back to TEA (The Architect) for the span-location OTEL assertion.

## TEA Assessment (red rework #2 — review response)

**Phase:** finish (rework after Reviewer REJECT #2)
**Status:** Blocking finding resolved; tests GREEN.

**Reviewer Review-2 finding addressed:**
- **[HIGH] Seam-2 span `last_seen_location` not discriminatingly proven** — Fixed: `test_participant_joined_router_named_stamps_location` now takes `otel_capture` and asserts the `participant.joined` span carries `last_seen_location == _HALL`. This is discriminating because the NPC starts at `_STALE_LOC` (≠ `_HALL`), so the span reporting `_HALL` proves the WRITTEN value reached the lie-detector — the span-layer proof AC4's co-located fixture structurally cannot give. The 2×2 matrix is now closed on BOTH the object and span layers.
- **[MEDIUM] AC2 double-emit blind spot** — Fixed: added `assert len(stamped) == 1` before indexing `stamped[0]`.
- **[polish] AC3 bare assertion** — Added a diagnostic message clarifying it is a co-location invariant, not the write-proof.

**Verification:** `pytest -n0` — 7/7 GREEN on 72-12, 6/6 GREEN on 72-8 regression, `ruff` clean. No production code changed (the implementation has been correct throughout; this round closed the last OTEL-coverage gap).

**Handoff:** To Dev (Agent Smith) for the green gate (confirm GREEN — no implementation needed).

## Subagent Results (Review 3)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (13 passed, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 2 (both LOW) | prior HIGH **RESOLVED**; 2 non-blocking (perf + message framing) |
| 3 | reviewer-silent-failure-hunter | Yes | clean | 0 | prior AC3 concern **RESOLVED** |
| 4 | reviewer-test-analyzer | Yes | findings | 1 (MEDIUM) | prior 2 **RESOLVED**; 1 non-blocking (AC4 redundant tautology — coverage exists) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | clean | 0 | N/A (nil surface) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (5 enabled returned, 4 disabled pre-filled)
**Total findings:** 0 blocking; both prior-round blocking findings confirmed RESOLVED; 3 non-blocking (1 medium, 2 low).

### Observations (tagged)

- `[TEST]` **[RESOLVED]** Review-1 object-layer location tautology + Review-2 span-layer location tautology — both now discriminatingly proven: object via AC1 (`_STALE_LOC`→`_HALL`) + router-named test; span via the router-named test's `participant.joined` assertion (`_STALE_LOC`→`_HALL`). Confirmed by test-analyzer + silent-failure + edge-hunter.
- `[TEST]` **[MEDIUM, non-blocking]** AC4's *span* `last_seen_location` assertion (`:393`) is itself tautological (co-located `_HALL`) — but it is **redundant, not a gap**: the span-layer location-write is proven by the router-named test. Recommend (optional) a "co-location invariant" comment on AC4's span assertion to match AC3's treatment. Not blocking — coverage is complete.
- `[EDGE]` **[LOW, non-blocking]** `otel_capture` fixture appends a span processor per use without removing prior ones — performance only under xdist; cannot falsify the `len==1` guards (shut-down exporters reject new exports). Pre-existing fixture pattern (also used by AC2/AC4).
- `[EDGE]` **[LOW, non-blocking]** The `len(stamped)==1` message frames the concern as "double-emit hiding"; if production later emits per-beat, the message would read slightly off. Accurate for the current shape.
- `[SILENT]` clean — all new assertions fail loud on missing keys (`.get()`→`None != expected`); `len==1` guards each protected by a prior `assert <list>` with a diagnostic.
- `[SEC]` clean (nil surface) — test-only delta, OTEL span-count guards + comments.
- `[VERIFIED]` Production byte-identical to Review 1 (`git diff f54a7ac...HEAD` = test file only); the seams cleared with full coverage in Review 1 are intact. 72-8 regression 6/6 green.
- `[SIMPLE]` n/a (disabled) — verify-phase simplify applied the `len==1` consistency guard.
- `[DOC]`/`[TYPE]`/`[RULE]` n/a (disabled) — no public API/type changes; manual Rule Compliance carried from Review 1 (production unchanged).

### Devil's Advocate

Try once more to call it hollow. The remaining complaint is AC4's co-located span-location assertion — but unlike the first two rounds, this is no longer a *missing* proof: the router-named test discriminatingly asserts the `participant.joined` span carries the written `_HALL` from a `_STALE_LOC` start, on both the object and span layers. Strip `_stamp_attrs` from the production `participant_joined_span` call and the router-named span assertion goes red. Drop the `_stamp_encounter_presence` call and the object assertions go red. Break the opposed-check seam and AC1/AC2 go red. Every seam × every layer now has at least one discriminating witness, and the `len==1` guards close the double-emit blind spot the first approval would have missed. The surviving findings are a redundant-but-harmless assertion and a shared-fixture performance note — neither can let a real regression through. Continuing to reject here would be manufacturing process to avoid a decision the evidence already supports. The witness has testified, the testimony is discriminating, and the cause-and-effect closes. Approved.

## Reviewer Assessment (Review 3)

**Verdict:** APPROVED

**Specialist findings incorporated:** `[TEST]` prior tautology findings RESOLVED; 1 non-blocking AC4 redundant assertion. `[EDGE]` prior HIGH (router-named span) RESOLVED; 2 non-blocking LOW (OTEL processor accumulation = perf; `len==1` message framing). `[SILENT]` clean — all new asserts fail loud on missing keys; prior AC3 concern RESOLVED. `[SEC]` clean — nil surface (test-only OTEL guards). `[DOC]`/`[TYPE]`/`[SIMPLE]`/`[RULE]` n/a — subagents disabled; production unchanged since Review 1's full-coverage pass. No blocking findings.

**Prior findings:** all RESOLVED and independently confirmed (Review-1 object tautology + AC2 wrong key; Review-2 span tautology). The suite now proves both seams stamp `last_seen_turn` + `last_seen_location` on both the object and OTEL-span layers, across both seating sources, with discriminating fixtures and double-emit guards.
**Data flow traced:** opposed_check resolution → `_stamp_encounter_presence` → `npc.edge_published` span (AC1/AC2, discriminating); participant seating → `_stamp_encounter_presence` → `participant.joined` span (AC3/AC4 turn + router-named location, discriminating).
**Pattern observed:** clean reuse of 72-8's `_stamp_encounter_presence` primitive at both seams; OTEL lie-detector coverage complete.
**Error handling:** No-Silent-Fallbacks honored (location frozen when unresolved — AC5 both seams); production raises loud on missing pending roll.
**Non-blocking follow-ups (logged in Delivery Findings):** AC4 span-location clarifying comment; the two epic-scope production Improvements from Review 1 (silent no-NPC skip OTEL; opposed_check+hp_depletion dial-inversion guard).
**Handoff:** To Architect (Neo) for spec-reconcile, then SM for finish.

## Exit Protocol

When development is complete:

1. All acceptance criteria green (unit + OTEL span assertions)
2. 72-8 regression tests pass (no breakage to existing seams)
3. Full server test suite green (`just server-test`)
4. Ruff + pyright clean (`just server-check`)
5. Create PR targeting develop with summary linking this story + accepting criteria, ready for code review

---

**Co-Authored-By:** Claude Opus 4.8 (1M context) <noreply@anthropic.com>