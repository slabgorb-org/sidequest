---
story_id: "153-10"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 153-10: [WWN-OTHER-SEATING] seater prefers pool/narrative antagonist over an ambient MM entity on vague target (ADR-116)

## Story Details
- **ID:** 153-10
- **Jira Key:** (none — Jira not enabled)
- **Workflow:** tdd
- **Stack Parent:** none
- **Assignee:** Keith Avery
- **Repo:** server (sidequest-server)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-21T22:46:51Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-21T21:55:52+00:00 | 2026-06-21T21:58:50Z | 2m 58s |
| red | 2026-06-21T21:58:50Z | 2026-06-21T22:14:37Z | 15m 47s |
| green | 2026-06-21T22:14:37Z | 2026-06-21T22:39:06Z | 24m 29s |
| review | 2026-06-21T22:39:06Z | 2026-06-21T22:46:51Z | 7m 45s |
| finish | 2026-06-21T22:46:51Z | - | - |

## Sm Assessment

**Setup complete — routing to TEA (The Architect) for RED.**

**Story:** 153-10 [WWN-OTHER-SEATING] — bug. Under a Worlds Without Number binding, when a player issues a *vague* attack target ("I attack the guard", no specific named NPC), the single confrontation seater (ADR-116) reaches for an ambient Monster Manual entity instead of preferring an antagonist that already exists in the narrative / NPC pool. This is the WWN sibling of the CWN-OTHER-SEATING family.

**Scope:** server-only (sidequest-server). 3pt, `tdd` phased workflow.

**Technical breadcrumbs for the next agents (not implementation by SM):**
- ADR-116 "A Confrontation Requires an Other" governs the single opponent-seater invariant.
- 126-32a precedent: the seater runs BEFORE the post-narrator `_apply_npc_mentions` NPC mint, so a prior-turn antagonist lives in `npc_pool`, not `snapshot.npcs` — the seater must consult the pool when resolving a vague target.
- The MM-cache staleness family (the_circuit 48-HP Wheelman; auto-purge fix) is adjacent context but a distinct bug — this story is about *source preference* in the seater, not cache coherence.
- Likely fix locus: the WWN seater path's Other-source selection ordering (prefer pool/narrative antagonist over MM ambient on a vague/unnamed target).

**TEA focus for RED:** author a failing test that, under a WWN ruleset with an existing pool/narrative antagonist and a vague unnamed attack target, asserts the seater seats the pool antagonist (not a freshly-minted ambient MM entity). Cover the wiring: the seater is actually invoked on the production confrontation path, not just unit-tested in isolation.

**Gate:** session at orchestrator root ✓, fields set ✓, context written (sprint/context/context-story-153-10.md) ✓, branch `feat/153-10-wwn-other-seating-prefer-pool-antagonist` created off server `develop` ✓. Jira intentionally skipped (not enabled for this project). Merge gate clear (0 in-progress / 0 in-review at setup).

## TEA Assessment

### Red Phase (test writing)

**Tests Required:** Yes
**Reason:** behavioral bug fix — the seater's source-preference is wrong; needs a pinned contract.

**Test File:**
- `sidequest-server/tests/server/dispatch/test_153_10_wwn_other_seating.py` — 4 tests driving the REAL `instantiate_encounter_from_trigger` seam with the live WWN pack `caverns_and_claudes` (modeled on the 153-9 Fate sibling `test_153_9_fate_other_seating.py`).

**ACs defined by TEA** (sprint YAML + story context carried none — see Design Deviations):
- **AC-1** — under WWN, a router-named scene-active antagonist living in `snapshot.npc_pool` is seated as the Other over a co-located ambient Monster-Manual bestiary entity in `snapshot.npcs`. (the "vague target → MM grab" defect)
- **AC-2** — the decline-the-MM-grab decision is observable: `encounter.roster_resolution_skipped` fires naming the declined MM entity; the 108-2 `encounter.opponent_resolved_from_roster` resolve span does NOT fire; the seated Other shows on `participant.joined`.
- **AC-3** — an exactly-named ambient MM entity is still seated (no over-correction).
- **AC-4** — with NO pool antagonist, the ambient MM entity is still conscripted (108-2 / ADR-059 preserved — keys on a pool antagonist existing, not a blanket disable).

**Tests Written:** 4 tests covering 4 ACs.
**Status:** RED — verified directly (`uv run pytest -n0`), **2 failed / 2 passed**:
- `test_wwn_seats_pool_antagonist_over_ambient_mm_entity` — **FAIL** (red): `got ['Mistos Warden'] != ['Daggereye Skirmisher']`. AC-1, the headline bug.
- `test_wwn_decline_mm_grab_emits_decision_span` — **FAIL** (red): `encounter.opponent_resolved_from_roster` fired (MM grab), `roster_resolution_skipped` absent. AC-2, OTEL lie-detector.
- `test_wwn_exact_mm_target_is_still_seated` — **PASS** (green guard). AC-3.
- `test_wwn_conscripts_mm_entity_when_no_pool_antagonist` — **PASS** (green guard). AC-4.

The two green guards are intentional — they constrain the fix from over-correcting (mirrors the 153-9 structure: Tests 3 & 4 there are also already-green guards). The two RED tests fail for the RIGHT reason (the MM grab), confirmed by the assertion messages, not a fixture error.

> **Verification note:** ran `pytest -n0` directly rather than via the `testing-runner` subagent — that subagent is known to clobber the session file and hallucinate per-test GREEN (trust counts only). Ground-truth counts above are from direct invocation.

### Root cause located for Dev (Agent Smith)

- **Target function:** `_resolve_opponent_from_roster` in `sidequest/server/dispatch/encounter_lifecycle.py` (~line 874-961). Its candidate filter is `n.creature_id is not None` over `snapshot.npcs` ONLY (line 917-924) — a *person* pool antagonist (no `creature_id`, living in `snapshot.npc_pool`) is invisible, so an ambient bestiary mob wins by default. It must consult `snapshot.npc_pool` (non-creature members) and prefer a scene-active antagonist that matches the router-named threat BEFORE returning a bestiary `candidates[0]`.
- **Proven precedent to mirror:** the Fate seater `_seed_fate_opponents` (~line 481-496) already does the pool consultation for 126-32a — `next((m for m in snapshot.npc_pool if m.name == actor.name and not m.is_creature), None)` + `_promote_pool_member_to_npc` / `_seed_invented_npc_identity` from `narration_apply`. The WN/native fix is the sibling of that.
- **OTEL contract (AC-2):** when declining the MM grab in favour of a pool antagonist, emit `encounter.roster_resolution_skipped` with `declined_name=<MM entity name>` (same span the 153-9 Fate decline uses) — and do NOT fire `encounter.opponent_resolved_from_roster`.
- **Likely also needed:** promote the preferred pool member to a backing `Npc` (carry identity/disposition, not a hollow stub) so the seated Other isn't a fabricated phantom beside the cast member the player engaged — `_seed_combat_hp_depletion_to_npcs` (~line 270) currently has no `npc_pool` consultation either. AC-1 asserts only the seated NAME, so the minimal decline-in-`_resolve_opponent_from_roster` satisfies it; the promotion is the complete fix (Dev's call).

### Rule Coverage

Applicable lang-review checks (`.pennyfarthing/gates/lang-review/python.md`) — this is a TEST-only change, so the test-facing rules apply:

| Rule | Test(s) / Action | Status |
|------|------------------|--------|
| #6 Test quality (no vacuous assertions) | self-check grep + manual review — every test asserts specific actor lists / span names / attributes; no `assert True`, no truthy-only, no `assert result`, no `@pytest.mark.skip` w/o reason | pass |
| #6 Test quality (real seam, not source-text) | tests drive the production `instantiate_encounter_from_trigger` with a live WWN pack — OTEL span assertions + behavioral actor assertions (CLAUDE.md "No Source-Text Wiring Tests" honored) | pass |
| Wiring test (CLAUDE.md "Every Test Suite Needs a Wiring Test") | the tests ARE the integration/wiring test — they exercise the real entry point end-to-end, proving the seater is reachable and mis-seats today | pass |
| Lint (ruff check + format) | scoped to the changed file only — `ruff check` clean, `ruff format` applied | pass |

**Rules checked:** 4 of 4 applicable (test-change scope — production-code rules #1-#5, #7-#13 apply to Dev's GREEN diff, not this test file).
**Self-check:** 0 vacuous tests found.

**Handoff:** To Dev (Agent Smith) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/sidequest/server/dispatch/encounter_lifecycle.py` — two gated, additive branches in the native seating path (no native-mechanic balancing — pure source-preference fix).

**The fix (complete, mirrors the Fate seater — not a name-only half-fix):**
1. **`_resolve_opponent_from_roster`** — before returning an ambient bestiary `candidates[0]`, decline the conscription when the router-named threat matches a non-creature `snapshot.npc_pool` member (the scene-active person antagonist). Emits `encounter.roster_resolution_skipped` (`reason="pool_antagonist"`, `declined_name=<mob>`); does NOT fire `encounter.opponent_resolved_from_roster`. Applies in combat too (a named scene antagonist outranks an ambient mob regardless of category).
2. **`_seed_combat_hp_depletion_to_npcs`** — in the `created` (un-backed opponent) branch, before fabricating a hollow ephemeral stub, check `snapshot.npc_pool` for a matching non-creature member and **promote** it via `_promote_pool_member_to_npc` + `_seed_invented_npc_identity` (carrying narrated identity + hostile disposition), then seed content hp/AC. This avoids minting a phantom of the same name beside the real cast member — the native sibling of the Fate seeder's 126-32a promotion. A genuine fabrication (no pool match) still fires the `minted_stub` lie-detector span unchanged. `pool_origin` now rides the `npc.edge_published` span so the GM panel distinguishes "promoted the cast member" from "fabricated a stub".

**Scope note (why part 2, not just part 1):** AC-1 asserts only the seated NAME, which part 1 alone satisfies. But part-1-only would fire the *misleading* `minted_stub` span ("fabricated... author the encounter's adversary") for an antagonist that WAS authored, and flatten its hostile disposition to neutral — violating the OTEL lie-detector principle (CLAUDE.md) and recreating the exact 126-32a phantom defect on the WN path. Promotion is the correct completion of "prefer the pool antagonist," follows the existing Fate precedent, and is surgical (gated on a pool match in the `created` branch only).

**Tests:** 4/4 passing (GREEN) — verified directly (`uv run pytest -n0`):
- `test_wwn_seats_pool_antagonist_over_ambient_mm_entity` (AC-1) ✅
- `test_wwn_decline_mm_grab_emits_decision_span` (AC-2) ✅
- `test_wwn_exact_mm_target_is_still_seated` (AC-3 guard) ✅
- `test_wwn_conscripts_mm_entity_when_no_pool_antagonist` (AC-4 guard) ✅

**Regression:** dispatch dir + core seating units = **531 passed** (153-9 Fate sibling, 108-2 roster resolution, materialize, friendly/presence seating, dogfight, table, sealed-letter, toothless detector all hold). WWN/SWN integration batch **20/20 green under CI config (`-n auto`)**. Full server suite under `-n auto`: **13826 passed, 2 failed** — both proven NOT mine:
- `test_watcher_events::test_publish_event_shape` — cross-test `-n auto` flake (the file is **20/20 green in isolation**; global watcher state, same fixture-pollution class as a rare serial-mode `otel_capture` flake I also saw in `test_space_opera_melee_e2e` — that one is a verified no-op for my change since its pool is empty, ~3% only under `-n0`, and is **5/5 green under `-n auto`**).
- `test_beneath_sunden_room_binding_107_2::test_distinct_rooms_bind_distinct_creatures` — **PRE-EXISTING**: fails with my change stashed; the WIP `beneath_sunden` world only authors one room (`{'entrance': ['gnaw_swarm']}`), a content-drift issue unrelated to seating code.

**Quality:** `ruff check` clean, `ruff format` clean, `pyright` introduced **0 new errors** (14 pre-existing both with and without my change).

**Branch:** `feat/153-10-wwn-other-seating-prefer-pool-antagonist` (pushed).

**Handoff:** To Reviewer (The Merovingian) for review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (5 advisory notes) | confirmed 0, dismissed 0, deferred 0 — all 5 notes resolved as VERIFIED-correct or consistent-with-scope |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (domain covered manually — see [EDGE] in assessment) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings (domain covered manually — see [SILENT] in assessment) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings (domain covered manually — see [TEST] in assessment) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings (domain covered manually — see [DOC] in assessment) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (domain covered manually — see [TYPE] in assessment) |
| 7 | reviewer-security | Yes | clean | 0 | confirmed 0, dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (domain covered manually — see [SIMPLE] in assessment) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings (domain covered manually — see [RULE] in assessment) |

**All received:** Yes (2 enabled subagents returned; 7 disabled via `workflow.reviewer_subagents`, their domains covered manually)
**Total findings:** 0 confirmed, 0 dismissed, 0 deferred (2 LOW observations of my own — see assessment; neither blocks)

## Reviewer Assessment

**Verdict:** APPROVED

Cause and effect, traced end to end. The change is a pure **source-preference** fix in the native confrontation seater — which NPC is seated as the Other — with zero native-mechanic balancing (ADR-143 respected). It is the WN/native sibling of the Fate seater's 126-32a pool consultation.

**Data flow traced:** player vague-attack → intent router names a free-string threat (`materialized_threat.name`) → `instantiate_encounter_from_trigger` → `_resolve_opponent_from_roster`: if `threat_name` matches a non-creature `snapshot.npc_pool` member, **decline** the bestiary conscription (emit `encounter.roster_resolution_skipped reason=pool_antagonist`, return None) → caller seats the router-named threat (`seating_source=materialized`) → `_seed_combat_hp_depletion_to_npcs`: the un-backed opponent is **promoted** from the pool (`_promote_pool_member_to_npc` + `_seed_invented_npc_identity`, content hp/AC) carrying identity + hostile disposition → the seated Other IS the cast member, non-ephemeral, durable. Safe because every branch is loud (OTEL spans), the exact-match guard short-circuits genuine roster targets, and the candidate list is proven non-empty before `candidates[0]`.

**Observations (no rubber-stamp — 12, incl. 5 VERIFIED):**
- [VERIFIED] Promoted antagonist is **non-ephemeral** so it survives the post-fight husk-reaping (`encounter_lifecycle.py:148-169` reaps only `npc.ephemeral`; `_promote_pool_member_to_npc` builds with default `ephemeral=False`) — cast continuity, the SOUL "Living World" intent, and identical to the Fate 126-32a promotion. Evidence: `narration_apply.py:1464-1478`.
- [VERIFIED] Hostile disposition survives promotion: `_promote_pool_member_to_npc` carries `member.disposition` (-25 in test) and emits `npc_spawn_disposition_span(provenance="carried_from_pool")` — `narration_apply.py:1477,1485-1491`. The antagonist seats hostile, not flattened to neutral.
- [VERIFIED] `candidates[0]` is safe — the new guard sits after `if not candidates: return None` (`encounter_lifecycle.py:925-926`), so the list is non-empty. No IndexError.
- [VERIFIED] `pool_origin` is reset per loop iteration (`encounter_lifecycle.py:323`, immediately after the per-actor `created`), so one actor's promotion never leaks onto the next. Always emitted on the edge span (`""` when not promoted).
- [VERIFIED] Deferred import of `_promote_pool_member_to_npc`/`_seed_invented_npc_identity` mirrors the existing `_seed_fate_opponents` deferred import (circular-import avoidance, established pattern) — `encounter_lifecycle.py:486-489` vs the new block.
- [SEC] Clean — security subagent confirmed no new injection/sanitization path: `threat_name`/`pool_member.name`/`pool_origin` are LLM-minted identity strings already in the snapshot, used for equality match + internal GM-panel-only OTEL attributes; the narrator-name-to-prompt route is the pre-existing NPC-roster path, not introduced here (ADR-047 not newly violated).
- [SILENT] No silent fallback — both new branches are loud: the decline emits `roster_resolution_skipped` naming the refused mob; the non-promotion path still fires `minted_stub`. Fail-loud preserved (CLAUDE.md).
- [TEST] Independent pass: 0 vacuous assertions, 13 meaningful assertions, drives the REAL `instantiate_encounter_from_trigger` seam with a live WWN pack; 2 RED-for-the-bug + 2 green guards. No source-text wiring tests.
- [TYPE] Types consistent (`pool_origin: str`, `pool_member: NpcPoolMember | None` guarded with `is not None`); pyright introduced 0 new errors (14 pre-existing both ways).
- [DOC] Comments are accurate and cite the correct lineage (126-32a, 153-9, 108-2, ADR-059, ADR-116); the old fabrication comment correctly moved into the `else` branch and was updated to note the pool-promotion attempt upstream. No stale/misleading docs.
- [SIMPLE][LOW] The pool-consultation pattern now exists in 3 inline copies (Fate seeder + WN resolver-decline + WN hp-seeder-promotion). Acceptable for this story (matches the existing inline style); Dev logged a non-blocking finding to extract a shared helper. Not a blocker.
- [EDGE][LOW] The new decline is placed BEFORE the existing fate/non-combat decline, so a Fate-or-non-combat confrontation that ALSO has a pool-matching threat now emits `reason="pool_antagonist"` instead of `"fate_binding"`/`"non_combat"`. Both decline → identical seating outcome; only the OTEL `reason` attribute differs, and no test asserts the reason. Harmless attribution nuance.
- [EDGE][LOW] Exact-string name match (`m.name == threat_name`) — a truly-vague partial/plural target ("Daggereyes" vs "Daggereye Skirmisher") would miss and fall back to the MM path. Consistent with the existing top-of-function exact-match guard and with Dev's logged non-blocking follow-up (the `materialized_threat=None` truly-vague path). The ACs + playtest repro are the router-named-pool-antagonist case; scope-limited by design, not a regression.

### Rule Compliance (python lang-review checklist, enumerated against the diff)

| # | Rule | Applies? | Verdict |
|---|------|----------|---------|
| 1 | Silent exception swallowing | yes | PASS — no try/except added; both branches emit loud spans; no bare except |
| 2 | Mutable default arguments | no new defs with defaults | PASS |
| 3 | Type annotation gaps at boundaries | internal helpers (exempt) | PASS — no new public boundary |
| 4 | Logging coverage/correctness | no error paths added | PASS — observability is via OTEL spans (project mechanism) |
| 5 | Path handling | N/A | PASS |
| 6 | Test quality | yes | PASS — 0 vacuous, real-seam, green guards |
| 7 | Resource leaks | `with span:` context managers | PASS — correct context-manager use |
| 8 | Unsafe deserialization | none | PASS |
| 9 | Async pitfalls | sync function | PASS |
| 10 | Import hygiene | deferred import | PASS — function-level import mirrors `_seed_fate_opponents` (circular-import avoidance), not a star import |
| 11 | Input validation at boundaries | yes | PASS — names are in-snapshot identity strings, not raw boundary input (confirmed by [SEC]) |
| 12 | Dependency hygiene | no deps changed | PASS |
| 13 | Fix-introduced regressions | yes | PASS — no checked bug re-introduced; regression suite GREEN |

### Devil's Advocate

Let me argue this code is broken. **Claim 1: it seats a phantom.** Counter: traced — the promotion path runs `_promote_pool_member_to_npc` (carries name/pronouns/appearance/disposition/`pool_origin`) then `_seed_invented_npc_identity`, and the result is non-ephemeral, so it is a real persistent cast member, not a husk; the husk-reaper (`:148-169`) skips it. **Claim 2: a stressed router emits a near-but-not-exact name and the fix silently does nothing.** Partly true — exact-match means "Daggereyes" ≠ "Daggereye Skirmisher" falls back to the MM path. But that is identical to the pre-existing top-of-function exact-match contract; it is not a *new* silent fallback (the MM path is the documented behavior and still emits its own spans), and Dev logged the truly-vague follow-up. No *regression*, and no silent substitution — every outcome is observable. **Claim 3: duplicate-named opponents promote twice.** `by_name` is built once before the loop, so two same-named opponent actors would both see `created=True` and both append — BUT this is the pre-existing behavior of the fabrication branch too (my change preserves, not introduces, it), and the seating sources (single materialized_threat, or unique-named location fallback) do not produce duplicate-named opponents in practice. **Claim 4: `_seed_invented_npc_identity` clobbers a re-encountered NPC's learned identity.** Counter: it is called on a FRESH promotion (`npc.ocean is None`), guards on `drawn_from=="narrator_invented"`, and explicitly does not re-touch disposition; on a re-entry the opponent is already in `snapshot.npcs` so `created=False` and the promotion branch never runs. **Claim 5: the OTEL `reason` flip breaks the Fate lie-detector.** Counter: 153-9 asserts `declined_name` only, the regression suite is GREEN (17/17), and the seating outcome is unchanged. **Claim 6: a malicious player injects via the antagonist name.** Counter: [SEC] confirmed the name is narrator/router-minted and only reaches internal OTEL attrs + the pre-existing NPC-roster prompt path; no new external surface. Conclusion: the devil finds only scope-limits already logged as non-blocking, not defects.

**Pattern observed:** correct mirror of the Fate seater's pool-consultation (`_seed_fate_opponents`, 126-32a) onto the WN/native path — `encounter_lifecycle.py` `_resolve_opponent_from_roster` (decline) + `_seed_combat_hp_depletion_to_npcs` (promote).
**Error handling:** fail-loud preserved — `roster_resolution_skipped` on decline, `minted_stub` on genuine fabrication, `npc_spawn_disposition_span`/`npc_edge_published(pool_origin=...)` on promotion. No swallowed errors.
**Handoff:** To SM (Morpheus) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): the native/WN seater duplicates a defect the Fate path already fixed (126-32a / 153-9) — neither `_resolve_opponent_from_roster` nor `_npc_fallback_at_location` consults `snapshot.npc_pool`, while `_seed_fate_opponents` does. Affects `sidequest/server/dispatch/encounter_lifecycle.py` (a shared pool-consultation helper would prevent the next ruleset path from re-introducing the same "ambient adversary over scene antagonist" bug). *Found by Dev during implementation: the fix here is the THIRD copy of the pool-consultation pattern (Fate seater + WN resolver-decline + WN hp-seeder-promotion). A shared `_match_pool_antagonist(snapshot, name)` helper is worth extracting next time a ruleset path needs it.*
- **Improvement** (non-blocking): the `_npc_fallback_at_location` truly-vague path (`materialized_threat=None`) still consults only `snapshot.npcs`, so a pool antagonist could still be missed when the router names NOTHING (vs the router-named-pool-antagonist case this story fixes). Affects `sidequest/server/dispatch/encounter_lifecycle.py::_npc_fallback_at_location`. Not in scope here (the playtest repro and the ACs are the router-named-threat path); flagging for a possible follow-up. *Found by Dev during implementation.*
- **Improvement** (non-blocking): `test_watcher_events::test_publish_event_shape` and `test_space_opera_melee_e2e::test_melee_resolves_on_hp_depletion_with_otel` are rare cross-test flakes under serial/global-OTEL-fixture ordering (both green in isolation and under `-n auto`); the shared `otel_capture` / watcher-global pattern has a test-isolation weakness. Not introduced by this story. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): the WN/native opponent seater now consults `snapshot.npc_pool` in two of three sourcing paths (router-named via `_resolve_opponent_from_roster`, and backing via `_seed_combat_hp_depletion_to_npcs`), but the truly-vague `materialized_threat=None` location-fallback path (`_npc_fallback_at_location`) still scans only `snapshot.npcs`. A scene-active pool antagonist could still be missed when the router names NOTHING. Affects `sidequest/server/dispatch/encounter_lifecycle.py::_npc_fallback_at_location`. Out of scope here (ACs + playtest repro are the router-named case; Dev already logged this); flagging for a possible follow-up story. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the pool-consultation pattern is now inlined in three places (Fate `_seed_fate_opponents`, WN `_resolve_opponent_from_roster`, WN `_seed_combat_hp_depletion_to_npcs`). A shared `_match_pool_antagonist(snapshot, name)` helper would prevent the next ruleset path from re-introducing the "ambient adversary over scene antagonist" defect. Affects `sidequest/server/dispatch/encounter_lifecycle.py`. *Found by Reviewer during code review (corroborates Dev's finding).*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

3 deviations

- **Defined the acceptance criteria from the story title + playtest evidence**
  - Rationale: no ACs existed; the title + playtest evidence + the directly-parallel 153-9 fix unambiguously define the contract.
  - Severity: minor
  - Forward impact: none — Dev/Reviewer should validate these ACs match Keith's intent for the WN seater (they are TEA-authored, not Keith-authored).
- **Pinned the OTEL decline span name as a contract (`encounter.roster_resolution_skipped`)**
  - Rationale: `_resolve_opponent_from_roster` is the natural fix locus and already emits this span on its Fate/non-combat decline branch — reusing it keeps the GM-panel lie-detector consistent across ruleset paths.
  - Severity: minor
  - Forward impact: if Dev implements the pool-preference at a different layer, they must still emit a decline span there (the test pins the observable, per the OTEL principle).
- **Implemented the COMPLETE fix (decline + pool promotion), not the test-minimal decline-only**
  - Rationale: decline-only would seat a hollow ephemeral stub of the antagonist's name and fire the MISLEADING `minted_stub` lie-detector span ("fabricated... author the encounter's adversary") for an antagonist that WAS authored, and flatten its hostile disposition to neutral — recreating the 126-32a phantom defect on the WN path and violating the OTEL principle + CLAUDE.md "No half-wired features." This is the correct completion of the story intent, not scope creep (it follows the existing Fate precedent and is gated on a pool match).
  - Severity: minor
  - Forward impact: none — the promotion only fires for a router-named, un-backed, non-creature pool member; all other opponent paths (bound creature, exact roster match, genuine fabrication) are unchanged.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Defined the acceptance criteria from the story title + playtest evidence**
  - Spec source: context-story-153-10.md ("No acceptance criteria recorded in the sprint YAML — TEA to define during the RED phase")
  - Spec text: story title "[WWN-OTHER-SEATING] seater prefers pool/narrative antagonist over an ambient MM entity on vague target (ADR-116)"
  - Implementation: derived AC-1..AC-4 from the title + the original playtest repro in `sprint/archive/150-14-session.md` ("Mistos Warden 23/23 over the Daggereyes ... vague target → MM grab") and `150-12-session.md`, mirroring the 153-9 Fate sibling's AC structure.
  - Rationale: no ACs existed; the title + playtest evidence + the directly-parallel 153-9 fix unambiguously define the contract.
  - Severity: minor
  - Forward impact: none — Dev/Reviewer should validate these ACs match Keith's intent for the WN seater (they are TEA-authored, not Keith-authored).
- **Pinned the OTEL decline span name as a contract (`encounter.roster_resolution_skipped`)**
  - Spec source: CLAUDE.md OTEL Observability Principle + 153-9 sibling (`test_153_9_fate_other_seating.py`)
  - Spec text: "Every backend fix that touches a subsystem MUST add OTEL watcher events"
  - Implementation: AC-2 asserts the WN decline reuses the SAME span the Fate decline emits (`encounter.roster_resolution_skipped`, `declined_name` attr) rather than inventing a new name.
  - Rationale: `_resolve_opponent_from_roster` is the natural fix locus and already emits this span on its Fate/non-combat decline branch — reusing it keeps the GM-panel lie-detector consistent across ruleset paths.
  - Severity: minor
  - Forward impact: if Dev implements the pool-preference at a different layer, they must still emit a decline span there (the test pins the observable, per the OTEL principle).

### Dev (implementation)
- **Implemented the COMPLETE fix (decline + pool promotion), not the test-minimal decline-only**
  - Spec source: TEA Assessment "Root cause located for Dev" + story title "prefer pool/narrative antagonist"
  - Spec text: "AC-1 asserts only the seated NAME, so the minimal decline-in-`_resolve_opponent_from_roster` satisfies it; the promotion is the complete fix (Dev's call)."
  - Implementation: added BOTH the resolver decline (part 1) AND the hp-seeder pool promotion (part 2, mirroring `_seed_fate_opponents`), rather than only the decline that the tests strictly require.
  - Rationale: decline-only would seat a hollow ephemeral stub of the antagonist's name and fire the MISLEADING `minted_stub` lie-detector span ("fabricated... author the encounter's adversary") for an antagonist that WAS authored, and flatten its hostile disposition to neutral — recreating the 126-32a phantom defect on the WN path and violating the OTEL principle + CLAUDE.md "No half-wired features." This is the correct completion of the story intent, not scope creep (it follows the existing Fate precedent and is gated on a pool match).
  - Severity: minor
  - Forward impact: none — the promotion only fires for a router-named, un-backed, non-creature pool member; all other opponent paths (bound creature, exact roster match, genuine fabrication) are unchanged.

### Reviewer (audit)
- **TEA: "Defined the acceptance criteria from the story title + playtest evidence"** → ✓ ACCEPTED by Reviewer: sound. No ACs existed in the YAML; AC-1..AC-4 are faithfully derived from the title + the 150-14/150-12 playtest repro + the directly-parallel 153-9 Fate sibling. The two green guards (AC-3/AC-4) correctly fence the fix from over-correcting.
- **TEA: "Pinned the OTEL decline span name as a contract (`encounter.roster_resolution_skipped`)"** → ✓ ACCEPTED by Reviewer: correct — reusing the existing Fate/non-combat decline span keeps the GM-panel lie-detector consistent across ruleset paths, and `_resolve_opponent_from_roster` is the natural (and actual) fix locus. (Note: the new combat-path decline emits `reason="pool_antagonist"`, a new value on the same span — a benign attribution addition, logged as [EDGE][LOW] in my assessment.)
- **Dev: "Implemented the COMPLETE fix (decline + pool promotion), not the test-minimal decline-only"** → ✓ ACCEPTED by Reviewer: this was the right call, not scope creep. Decline-only would seat a hollow stub of the antagonist's name, fire the *misleading* `minted_stub` span for an antagonist that WAS authored, flatten its hostile disposition to neutral, and let the husk-reaper quarantine it — recreating the 126-32a phantom defect on the WN path and violating the OTEL lie-detector principle + CLAUDE.md "No half-wired features." The promotion mirrors the proven Fate precedent and is surgically gated on a pool match in the `created` branch only.
- No undocumented deviations found — the diff matches the logged design exactly.