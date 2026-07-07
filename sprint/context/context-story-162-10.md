# Story 162-10 Context

## Title
162-2 non-blocking follow-ups: unified-resolver adoption at remaining seams (mention-path, pool-member lookup, Fate seeder, edge-publish by_name); decoy-roster hardening for canonicalization tests; participant.joined pre-rename telemetry; NpcMention rebind via dataclasses.replace; two comment corrections; diacritic-leg seat integration test

## Metadata
- **Story ID:** 162-10
- **Type:** chore
- **Points:** 2
- **Priority:** p2
- **Workflow:** tdd
- **Repo:** server
- **Epic:** 162 — NPC origin consolidation — one identity, one arbiter, derived Monster Manual

## Problem

Story 162-2 landed the unified identity resolver (`resolve_roster_npc`) and identity-keyed dedup/seating at production seams, closing the two-names-one-enemy fork. The Reviewer filed five non-blocking follow-ups during round-2 code review (sprint/archive/162-2-session.md, lines 355–359), and Dev and TEA identified two additional resolver-adoption gaps (lines 64 & 76) that were deferred from the original story scope as low-risk minimalist greenfield.

This story bundles those six deferred improvements into a single follow-up pass, hardening the resolver wiring, improving test coverage, and fixing observability leaks.

## Technical Approach

### 1. Unified-Resolver Adoption at Remaining Seams
**File anchors:** sprint/archive/162-2-session.md:64,76

Adopt `resolve_roster_npc` at four remaining seams that still use exact-match `by_name` dicts:

#### a. Narrator-mention path: `_apply_npc_mentions` (narration_apply.py)
- **Current:** exact/casefold/comma-inverted/invented_from legs all build their own `by_name` dicts
- **Target:** wire `resolve_roster_npc` (or a pool sibling) into all four mention-matching legs so prose names resolving via alias/invented_from are identity-keyed, matching the seater behavior
- **Implementation:** swap exact/casefold dicts for resolver calls; reuse the same resolution order (canonical > alias > invented_from)
- **Testing:** resolver unit tests cover the primitive; integration test via real narration_apply harness if path is modified

#### b. Seeder pool-member lookup: `NpcPoolMember` leg in seeder (encounter_lifecycle.py)
- **Current:** `m.name == actor.name` exact match on authored actor names against pool member names
- **Target:** adopt `resolve_roster_npc` so authored-vs-pool matching is identity-keyed and respects aliases
- **Implementation:** one-line cutover mirroring the hp_depletion seeder (encounter_lifecycle.py ~L395)
- **Testing:** resolver unit tests; wiring verified by existing seeder tests

#### c. Fate seeder: `_seed_fate_opponents` (encounter_lifecycle.py ~L595)
- **Current:** builds a `by_name` dict keyed on exact creature.name for Fate seat resolution
- **Target:** adopt `resolve_roster_npc` so Fate opponents are identity-keyed
- **Implementation:** one-line cutover, same as (a)
- **Testing:** resolver units; wiring reuses existing Fate seeder test harness

#### d. Edge-publish by_name: `_publish_combat_edge_to_npcs` (encounter_lifecycle.py ~L808)
- **Current:** builds exact-match `by_name` dict from roster for binding edge-state updates to NPCs
- **Target:** adopt `resolve_roster_npc` for identity-keyed edge binding
- **Implementation:** one-line cutover, same pattern
- **Testing:** resolver units; edge-publish wiring tested by existing confrontation tests

**Triage note:** The two Fate/edge-publish seams have no observed fork and no failing tests; they are safe-to-defer low-risk seams. The mention-path and pool-member gaps have failing tests filed by TEA; dev addresses the logic path, reviewer verifies no new regressions.

### 2. Decoy-Roster Hardening for Canonicalization Tests
**File anchors:** sprint/archive/162-2-session.md:355

**Issue:** The three canonicalization tests (`TestSeatNameCanonicalization`) use single-entry rosters, so "canonicalize to the npc the resolver matched" vs. "canonicalize to whatever is in the roster" are indistinguishable — a wrong-npc rename would pass silently.

**Fix:** Add a decoy NPC to each test's roster (a creature with a name similar to but distinct from the target, or a second unrelated creature), and assert that the seated actor is the SPECIFIC creature matched by the resolver, not just any creature in the roster.

**Tests affected:**
- `test_alias_named_actor_seats_canonical_creature`
- `test_case_variant_actor_does_not_mint_twin`
- `test_instantiate_with_recorded_alias_threat_resolves_and_seats_canonical`

**Acceptance:** Each test explicitly verifies `actor.core.creature_id == expected_creature.creature_id` or equivalent identity assertion, not roster-size magic.

### 3. Participant.joined Pre-Rename Telemetry
**File anchors:** sprint/archive/162-2-session.md:356, encounter_lifecycle.py:2075-2124

**Issue:** On the explicit-`npcs_present` path, `participant.joined` and init-span `combatant_names` emit before the seeder renames the actor to canonical (line 2075 initialization computes names before the rename at line 1796+), so the GM panel briefly sees the stale alias before later spans correct it.

**Fix:** Move or defer the `participant.joined` event emission / init-span name collection to after the seeder's canonicalization pass, or pre-compute canonical names on the npcs_present path.

**Testing:** Trace the seeder's path through the fixture pack (real combatant confrontation with alias-named threat) and verify `participant.joined` / combatant_names spans arrive with canonical names (match the `identity.resolved` + `npc.edge_published` canonical binding).

### 4. NpcMention Rebind via dataclasses.replace
**File anchors:** sprint/archive/162-2-session.md:359, encounter_lifecycle.py:1800-1805

**Issue:** Manual field-copy on NpcMention rebind (the head-check rebind at line 1800-1805) drops `is_new`, `is_creature`, `disengaged`, `is_place` flags. Today this is inert (the ship-scale filter runs pre-rebind), but it's a latent trap for future consumers.

**Fix:** Use `dataclasses.replace(mention, name=canonical_name)` instead of manual field copy.

**Testing:** Behavioral: the rebound NpcMention preserves all flags; wiring: verify the rebind event still fires and the mention still resolves to the same creature.

### 5. Two Comment Corrections
**File anchors:** sprint/archive/162-2-session.md:357, encounter_lifecycle.py:1791-1793

**Issue:** Two comment lines overclaim:
- Comment claims "case-variant rebind emits `identity.resolved` span" — this is false (canonical-leg hits don't span by design; only alias/invented_from legs span)
- Comment claims "'edge publish' resolves via `find_creature_core`" — false (edge-publish uses its own by_name dict, not find_creature_core)

**Fix:** Correct the comments to accurately describe the actual code path.

**Verification:** Inspection of the corrected lines + confirmation against the actual code behavior.

### 6. Diacritic-Leg Seat Integration Test
**File anchors:** sprint/archive/162-2-session.md:365 (approved findings reference line 88 of 162-2 spec)

**Issue:** 162-2's diacritic-folding fix (normalize_name now uses `fold_to_ascii`) was tested at the unit level (origin_model tests) and tested on the resolver's alias-resolution path. Seat-seaming integration coverage is missing: an NPC with a diacritical name in the roster, seated via prose with the ASCII variant, should resolve to the canonical creature (not mint a stub).

**Fix:** Add an integration test that:
1. Stages a roster with a diacritical-name creature (e.g., "Veyra Solnë")
2. Stages a confrontation threat named via ASCII prose (e.g., "Veyra Solne")
3. Verifies the threat resolves and seats the canonical creature (no stub mint)
4. Verifies the identity.resolved span fires with the correct creature_id

**Test file:** tests/server/test_162_2_identity_fork_seating.py or a new diacritic-specific integration class

**Coverage:** This covers the full resolve → seat → HP-seed → reachability path with diacritic normalization end-to-end.

## Acceptance Criteria

**AC1 — Unified-resolver adoption:** All four remaining seams (mention-path, pool-member, Fate seeder, edge-publish) adopt `resolve_roster_npc` and pass resolver-adoption wiring tests.
- Mention-path: `_apply_npc_mentions` wired to resolver (red test, green implementation)
- Pool-member: seeder's NpcPoolMember leg wired (unit + wiring test)
- Fate seeder: `_seed_fate_opponents` by_name dict replaced (unit + wiring test)
- Edge-publish: `_publish_combat_edge_to_npcs` by_name dict replaced (unit + wiring test)
- Verification: existing seeder / confrontation tests remain green; new wiring tests pass

**AC2 — Decoy-roster hardening:** All three canonicalization tests include a decoy NPC and assert the specific creature (by creature_id), not roster cardinality.
- Tests: `test_alias_named_actor_seats_canonical_creature`, `test_case_variant_actor_does_not_mint_twin`, `test_instantiate_with_recorded_alias_threat_resolves_and_seats_canonical`
- Verification: mutant creature_ids in the roster should cause test failures (mutation testing confirms each test is sensitive to identity mismatch)

**AC3 — Participant.joined pre-rename telemetry:** participant.joined and init-span combatant_names emit with canonical actor names on the npcs_present path.
- Trace: explicit-npcs_present confrontation with alias-named threat
- Verification: participant.joined span attributes + combatant_names match the identity.resolved canonical binding; no stale-alias events precede the canonical binding

**AC4 — NpcMention rebind via dataclasses.replace:** The head-check rebind uses `dataclasses.replace(mention, name=canonical_name)` and preserves all flags.
- Code inspection: encounter_lifecycle.py:1800-1805 uses replace, not manual field copy
- Behavioral test: a rebound mention with flags (e.g., is_creature=True) preserves the flags after rebind
- Verification: the rebind event fires and the mention resolves to the canonical creature

**AC5 — Two comment corrections:** encounter_lifecycle.py:1791-1793 comments are accurate (no false claims about span emission or resolution path).
- Verification: inspection against the actual code path (canonical-leg hits don't span; edge-publish uses by_name, not find_creature_core)
- Reviewer confirms during code review

**AC6 — Diacritic-leg seat integration test:** A diacritical-name creature in the roster is resolved and seated correctly when the prose threat uses the ASCII variant.
- Test: diacritical creature (e.g., "Veyra Solnë") rosters; prose threat "Veyra Solne" → resolves canonical creature, no stub mint
- Verification: identity.resolved span fires; find_creature_core(actor.name) reachable; no ephemeral stub spawned

**Ruff format check:** Verify whether tests/server/test_162_2_identity_fork_seating.py still needs formatting (line 358 / 162-2 findings); if already clean per ruff format --diff, drop this item from ACs.

## Success Definition

- All six improvements land in a single commit or a logically grouped series
- New tests red-fail before implementation, green-pass after
- Resolver wiring reuses one code path (`resolve_roster_npc`) across all four seams
- Decoy-roster tests catch identity-mismatch mutations
- Telemetry trace shows canonical names on participant.joined
- Comments accurately reflect code behavior
- Diacritic resolution test covers the full seat → reachability path
- Full test suite passes; ruff/pyright clean
- No new regressions in confrontation / seeder / narration_apply paths

---
_Generated by `pf context create story 162-10` from the sprint YAML and 162-2 session review findings._
