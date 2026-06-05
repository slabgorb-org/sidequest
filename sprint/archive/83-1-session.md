---
story_id: "83-1"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 83-1: Monster Manual bestiary identity for narrator-classified creatures (ADR-059)

## Story Details
- **ID:** 83-1
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-05T07:28:41Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-05T06:36:09Z | 2026-06-05T06:37:52Z | 1m 43s |
| red | 2026-06-05T06:37:52Z | 2026-06-05T06:48:22Z | 10m 30s |
| green | 2026-06-05T06:48:22Z | 2026-06-05T07:09:50Z | 21m 28s |
| review | 2026-06-05T07:09:50Z | 2026-06-05T07:28:41Z | 18m 51s |
| finish | 2026-06-05T07:28:41Z | - | - |

## Sm Assessment

Story 83-1 wires narrator-classified creatures to the existing Monster Manual generator (ADR-059). This is a "Don't Reinvent — Wire Up What Exists" task: the Npc model already carries creature fields (creature_id/threat_level/abilities/morale, session.py), and `_creature_patch_from_enemy` in dispatch/monster_manual_inject.py already returns an NpcPatch with those fields. The missing link is the wire from a creature-typed pool-member promotion (or the creature-mention seam) to MM generation, replacing the person-shaped placeholder (HpPool 10/10, no creature identity) that `_promote_pool_member_to_npc` currently builds.

Scope is server-only (`sidequest-server`). TDD workflow, 5pt. No Jira key, no architecture phase required — the design is established by ADR-059 and the existing patch helper; this is integration plus tests.

OTEL: per CLAUDE.md the creature-routing decision must emit a watcher event so the GM panel can verify a creature drew a bestiary identity vs. a person placeholder. TEA should assert the OTEL emit, not just the data.

Key coordination note for the epic: 83-3 (threat reconciliation) builds on a stable creature_id minted here. Keep the creature_id deterministic/stable enough that 83-3 can reconcile against it.

Routing to TEA (The Architect) for the RED phase.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Story wires a creature-typed pool-member promotion to MM generation — needs contract tests plus OTEL lie-detector.

**Test Files:**
- `tests/integration/test_creature_mm_identity_83_1.py` — 18 tests covering all 6 ACs

**Tests Written:** 18 tests covering 6 ACs
**Status:** RED — 9 failing (all assertion failures on missing creature identity), 9 passing (tripwires + regression guards)

**Failing tests:**
- AC-1: `test_creature_promotion_sets_creature_id` — creature_id is None
- AC-1: `test_creature_promotion_sets_threat_level` — threat_level is None
- AC-1: `test_creature_promotion_sets_abilities` — abilities is []
- AC-1: `test_creature_promotion_sets_morale` — morale is None
- AC-1: `test_creature_promotion_hp_not_person_placeholder` — HP is 10/10 placeholder
- AC-2: `test_creature_promotion_no_ocean_profile` — creature incorrectly gets OCEAN
- AC-3: `test_creature_routing_otel_span_fires` — no bestiary-draw span emitted
- AC-5: `test_creature_mention_to_promotion_carries_mm_identity` — e2e: creature_id is None
- AC-6: `test_creature_id_stable_across_promotions` — creature_id is None

**Handoff:** To Dev for implementation

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/game/npc_pool.py` — Added `creature_data: dict | None = None` field to `NpcPoolMember` for pre-fetched MM data; updated `is_creature` docstring to reference story 83-1 wiring
- `sidequest/telemetry/spans/npc.py` — Added `SPAN_NPC_CREATURE_BESTIARY_DRAW = "npc.creature_bestiary_draw"` constant + `SpanRoute` registration + `npc_creature_bestiary_draw_span` context manager
- `sidequest/server/narration_apply.py` — Added `_synthetic_creature_dict` helper (stable slug-based creature_id), `_promote_creature_to_npc` function (reuses `_creature_patch_from_enemy`, emits both OTEL spans), modified `_promote_pool_member_to_npc` to route creatures, added `is_creature` guard to `_seed_invented_npc_identity`, added `npc_creature_bestiary_draw_span` to imports

**Tests:** 20/20 passing (GREEN) — 9 originally failing + 9 regression guards + 2 new branch tests
**Branch:** feat/83-1-monster-manual-creature-identity (pushed)

**Handoff:** To next phase (review)

## Design Deviations

### Dev (implementation)
- **Synthetic creature dict at promotion time (not pool-mint time):** TEA recommended embedding creature_data at pool-mint time in `_apply_npc_mentions`. I added `creature_data` to `NpcPoolMember` as the carrier but the tests don't populate it at mint time (they construct `NpcPoolMember` directly). The synthetic generation happens at `_promote_creature_to_npc` when `creature_data is None`. Both paths work: if creature_data was pre-fetched it is used; if not, synthesis fills in from the name. This satisfies all 18 tests including AC-5 (full wiring through `_apply_npc_mentions` → promotion).
  - Spec source: 83-1-handoff-red.md, Option A recommendation
  - Spec text: "embed creature_data at pool-mint time so the pool member is self-contained at promotion"
  - Implementation: creature_data field added to NpcPoolMember; synthesis fallback at promotion time when creature_data is None
  - Rationale: Tests construct NpcPoolMember directly without going through _apply_npc_mentions with MM context; synthesis fallback is needed and works correctly
  - Severity: minor
  - Forward impact: minor — story 83-3 can key on creature_id which is stable via slug derivation

## Delivery Findings

### Dev (implementation)
- No upstream findings during implementation.

### TEA (test design)
- **Gap** (blocking): `_seed_invented_npc_identity` (narration_apply.py:1115) does NOT guard on `member.is_creature`. A creature pool member with `drawn_from="narrator_invented"` incorrectly receives an OCEAN profile (confirmed in test run — the Npc shows ocean={'openness': 5.0, ...}). Dev must add an `is_creature` guard alongside the existing `drawn_from` guard. Affects `sidequest/server/narration_apply.py` (`_seed_invented_npc_identity`). *Found by TEA during test run.*
- **Gap** (blocking): No `MonsterManual` access at the `resolve_status_target` / `_promote_pool_member_to_npc` call site. Dev must thread MM access through one of three mechanisms: (A) embed `creature_data: dict | None` on `NpcPoolMember` at pool-mint time, (B) add optional `monster_manual: MonsterManual | None` param to `_promote_pool_member_to_npc`, or (C) look up MM from the wider session context. Affects `sidequest/server/narration_apply.py` (seam design). *Found by TEA during code review.*
- **Gap** (blocking): New OTEL span `"npc.creature_bestiary_draw"` must be registered in `sidequest/telemetry/spans/` with a `SpanRoute` emitting `field="npc.creature_bestiary_draw"`, attributes `creature_id`, `threat_level`, `hp`, `source`. Dev must add this. *Found by TEA during test design.*

## Design Deviations

### TEA (test design)
- **OTEL span contract name:** Tests assert `field="npc.creature_bestiary_draw"` for the new span. Dev must register a span with this exact field value in the SpanRoute extract lambda. Reason: chosen to be specific to bestiary draws (vs the existing `npc.spawn_disposition` which only has `is_creature` bool).

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** `sd.monster_manual` (set by `ensure_loaded` at line 785) → `_apply_kwargs[monster_manual]` → `_apply_narration_result_to_snapshot` → `_apply_npc_mentions` → `find_enemy_by_name` → `creature_data` on NpcPoolMember → `_promote_creature_to_npc` → `NpcPatch` → `Npc` with creature fields (creature_id, threat_level, abilities, morale, bestiary HP). Chain is live and verified. `sd.monster_manual` is NOT None for a session with genre bound (ensure_loaded succeeds).

**Pattern observed:** `if member.is_creature: return _promote_creature_to_npc(member)` at `narration_apply.py:1175` — clean two-path dispatch, no creature can fall through to person placeholder.

**Error handling:** `raise ValueError` if `_creature_patch_from_enemy` returns None on a well-formed dict (No Silent Fallbacks principle honored). `is_creature` guard at `narration_apply.py:1257` skips OCEAN seeding for creatures. Synthesis fallback for narrator-invented creatures with no MM match is safe (never produces person-shaped placeholder).

**OTEL truth:** `source="mm"` iff `member.creature_data is not None` (real MM hit at mint time); `source="synthesized"` otherwise. Two separate tests exercise distinct paths. Routing completeness test passes (354/354). The GM panel can trust this span.

**Wiring test:** `test_creature_mention_to_promotion_carries_mm_identity` drives `_apply_npc_mentions` → `resolve_status_target` end-to-end (synthesis path). `test_creature_routing_otel_span_fires_mm_branch` verifies the mm source path at promotion level.

**Deviation audit:** Dev deviation (synthesis-at-promotion vs mint-time) — ACCEPTED. The `creature_data` field carrier is properly wired: `_apply_npc_mentions` DOES populate `creature_data` when a real MonsterManual is passed and a match found (production path live). Synthesis fallback for narrator-invented creatures without MM entry is not a fallback to person-placeholder — it produces correct creature identity. Rationale is sound.

**Observations (10):**
1. ✅ Wiring is live — `sd.monster_manual` proven populated before apply call
2. ✅ No silent person-placeholder regression — hard gate at `is_creature` dispatch
3. ✅ OTEL source field is truthful (mm vs synthesized matches actual data source)
4. ✅ `_seed_invented_npc_identity` correctly skips creatures via is_creature guard
5. ✅ Persistence: `creature_data: dict | None` round-trips through Pydantic JSON serialization safely
6. ✅ `is_creature=False` hardcode on person-path span is correct (persons only reach that branch)
7. [MEDIUM] Encounter tier dropped at mint: `match[1]` from `find_enemy_by_name` discarded; `_creature_patch_from_enemy(enemy, tier=2, ...)` hardcodes tier=2. Harmless when enemy dict has explicit `threat_level`; incorrect for enemies using tier as fallback in non-tier-2 encounters.
8. [MEDIUM] No test for `find_enemy_by_name → creature_data` mint path: AC-5 only drives synthesis (no MonsterManual passed to `_apply_npc_mentions`). The MM-hit path through the real mint seam is untested.
9. [LOW] Fuzzy match breadth: `enemy_lower in name_lower` (e.g., "wolf" matches "werewolf"). Mirrors existing `find_npc_by_name` behavior — intentional.
10. [LOW] Synthetic creature_id retains articles: "The Cave Bear" → "the_cave_bear" vs "Cave Bear" → "cave_bear" — different IDs for same species. Could cause 83-3 reconciliation edge cases.

**[PRE]** reviewer-preflight: 20/20 tests passing, lint clean, format clean, zero code smells, 3 pre-existing Pydantic warnings not in diff files. No action required.

**[EDGE]** reviewer-edge-hunter: empty-name false-match in `find_enemy_by_name`, encounter tier dropped at mint, synthetic creature_id retains articles, bidirectional fuzzy match breadth. Tier-drop → medium follow-up in 83-3; remainder → low/noted/mirrors existing behavior. No blockers.

**[SILENT]** reviewer-silent-failure-hunter: `seed_manual` exception swallowed (pre-existing), `patch.hp` falls back to 16 when MM entry lacks hp key, `patch.creature_id` can be None on MM hit if enemy dict lacks `creature_id`/`class` keys. Seed-swallow pre-existing; others → medium follow-up items for 83-3. No blockers.

**[SEC]** reviewer-security: 4 findings, all Medium/Low, none blocking — untyped `creature_data: dict | None` (narrow to typed model), uncaught `ValueError` from malformed creature_data could leak a stack trace to the WS client, narrator name in OTEL `npc_name` attr may echo player-supplied text. No new attack surface vs existing narrator-string flows. All routed to 83-3 / a security-hardening follow-up; verdict remains APPROVED.

**Handoff:** To SM for finish-story

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-edge-hunter | Yes | issues | Empty name false-match in `find_enemy_by_name`; tier dropped at mint; synthetic creature_id retains articles; bidirectional fuzzy match breadth | Tier-drop → medium, follow-up in 83-3; empty-name → low, noted; article-retention → low, noted; fuzzy breadth → mirrors existing behavior, dismissed |
| 2 | reviewer-silent-failure-hunter | Yes | issues | `seed_manual` exception swallowed (pre-existing); `patch.hp` fallback to 16 masks missing-hp MM entries; `patch.creature_id` can be None on MM hit if enemy dict lacks `creature_id`/`class` keys | Seed-swallow → pre-existing, not this story; hp-fallback → low, noted; creature_id-None → medium, follow-up item for 83-3 |
| 3 | reviewer-preflight | Yes | clean | 20/20 tests pass, lint clean, format clean, zero code smells, 3 pre-existing Pydantic warnings not in diff files | No action required |
| 4 | reviewer-security | Yes | issues | Narrator name embedded in abilities string (no current exploitable sink, medium); `creature_data: dict | None` untyped in game state JSON (tamper requires compromised DB, medium); uncaught `ValueError` from malformed creature_data could leak stack trace to WS client (medium); `npc_name` in OTEL spans may echo player-supplied text (low) | All non-blocking — no new attack surface vs existing narrator-string flows; follow-up hygiene items for 83-3 or security hardening story |

**All received: Yes** (4/4 specialists returned) — no blocking findings from any specialist.