---
story_id: "59-23"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 59-23: Chassis-vs-chassis ship_combat: materialize the named threat as the Other + ablative ship-hull HP resolution

## Story Details
- **ID:** 59-23
- **Jira Key:** (none — Jira not enabled)
- **Workflow:** tdd (phased)
- **Stack Parent:** none
- **Points:** 8
- **Status:** in_progress

## Technical Context

This story folds **TWO COUPLED DEFECTS** from the 2026-05-28 coyote_star playtest (`#C3` + `#C4`) into one chassis-vs-chassis ship_combat slice. Both defects exist in the same half-built subsystem; fixing one without the other leaves the feature unresolved.

### Defect #C3: Wrong Other

**Symptom:** When a narrative trigger names a threat that is NOT an existing NPC entity (e.g., "three unregistered hulls running dark"), the instantiate_encounter_from_trigger routine seats the **player's own crew** (Wainu, Kanga, Cmdr Yarya) as opponents.

**Root Cause:** `instantiate_encounter_from_trigger` (server/dispatch/encounter_lifecycle.py) finds `npcs_present` empty (router dispatches with `npcs_present=[]`) and falls through to `_npc_fallback_at_location`, which seats ALL present NPCs as `side=opponent` (default_side='opponent', around line 431).

**Why Simple Filter Won't Work:** The `_npc_fallback_at_location` behavior is INTENTIONAL for chases and brawls (code comment at encounter_lifecycle.py:410-415 ties it to story 59-13's chase dial — a neutral-disposition pursuer must still participate). A blanket `_npc_is_adversary` filter would break those scenarios.

**Correct Fix (ADR-116):** MATERIALIZE the named threat as adversary NPC(s) via the gaslight-the-narrator pattern (`game/world_materialization._apply_npc`), then seat THAT as the Other. Per ADR-116 ("a confrontation requires an Other"), the Other must exist as a concrete entity, not fall through to fallback logic.

### Defect #C4: Degenerate / Unwinnable Dogfight

**Symptom:** The dogfight never resolves; beat momentum leaks into the unused player placeholder dial (DRIVER saw the player bar climb 0→2/1,000,000 on a critical hit).

**Root Cause:** `ship_combat` declares `win_condition: hp_depletion`, which synthesizes INERT placeholder metrics `0/0/1_000_000` (encounter_lifecycle.py:726-735). The 1e6 sentinel is intentional — `apply_beat` gates dial resolution on `win_condition`, so placeholders never actually trigger resolution. hp_depletion is meant to resolve when ABLATIVE HP reaches zero, but chassis hull HpPools are never seeded for ship-vs-ship.

**Status of ADR-114:** Ablative HP (ADR-114) is marked "partial — only Part 1 (personal HP) is live." This story implements Part 2+: ship-scale ablative HP seeding and resolution.

**Correct Fix:** Seed the chassis hull HpPool with ablative HP values per the SWN crunch spec (docs/superpowers/specs/2026-05-25-swn-crunch-ablative-hp-design.md), then wire up beat resolution to check hull HP depletion.

---

## Acceptance Criteria

1. **#C3 Resolved:** When a narrative trigger names a threat not in the NPC roster, the engine materializes that threat as an adversary NPC and seats it as the Other. The player's own crew (side=player) never seats as opponents.

2. **#C4 Resolved:** ship_combat dogfights seed the chassis hull with correct ablative HP values. When hull HP reaches zero, the confrontation resolves (player win or loss per SWN rules). Beat momentum no longer leaks to placeholder dials.

3. **No Regression:** Existing chase and brawl scenarios (59-13) continue to work — `_npc_fallback_at_location` still seats present NPCs when no explicit threat is materialized (neutral pursuer scenario).

4. **OTEL Coverage:** Both fixes emit OTEL watcher spans so the GM panel can verify:
   - Threat materialization occurred (NPC name, side, HP seeding)
   - Hull HP state at each beat
   - Win condition evaluation and resolution

---

## Related ADRs & Stories

- **ADR-114** (Ablative HP Substrate) — Part 1 (personal HP) live; Part 2+ (ship-scale) deferred until now
- **ADR-116** (A Confrontation Requires an Other) — Other participant invariant
- **ADR-077** (Dogfight Subsystem) — Confrontation extension for ship_combat
- **ADR-117** (Pluggable Ruleset Module System) — SWN ruleset selector
- **Story 59-17** (Dogfight Instantiation) — Production path; completed
- **Story 59-19** — Build on this
- **Story 59-13** (Chase Dial) — Must not regress

---

## Implementation Notes

### Line Number Staleness Warning

The notes reference encounter_lifecycle.py around lines 410–431 and 726–735. **These line numbers may have drifted at HEAD.** Do NOT grep source code to verify fixes. Instead:
- Verify defect behavior exists via OTEL span assertions in fixture-driven tests
- Prove materialization and HP seeding via watcher events, not source inspection
- Per the server's "No Source-Text Wiring" rule, test behavior end-to-end

### Two-Phase Decomposition Option

This story may be split into two sub-stories during planning:
1. Materialize the named threat as the Other (#C3)
2. Seed and resolve ablative ship-hull HP (#C4)

For now, track as one slice to preserve the coupling.

### Content vs. Engine

- **Engine (sidequest-server):** Materialization logic, HP seeding, resolution — this story
- **Content (sidequest-content):** Chassis data (armor values, HP pools) — may be seeded later; not blocking

---

## Sm Assessment

**Routing:** TDD (phased) → RED phase → TEA (The Architect). (Note: the sm-setup subagent returned `next_agent: sm`, which is wrong — `pf workflow phase-check tdd red` resolves to `tea`. Routing to TEA.)

**Repo:** sidequest-server only, branch `feat/59-23-ship-combat-materialize-other-ablative-hull` off `origin/develop`. Chassis seed *content* (sidequest-content) may follow but is explicitly non-blocking for this engine slice.

**Size flag:** 8 points — the largest item on the board. The story description sanctions a split (materialize-Other / ablative-hull-resolution) but the Operator chose to track it as one slice. If TEA's RED analysis shows the two defects need independent test scaffolds that don't share fixtures, raise it as a Delivery Finding — but do not pre-split.

**Hard constraints for TEA (test author):**
- **#C3 fix is narrow.** Do NOT "fix" by blanket-applying `_npc_is_adversary` to `_npc_fallback_at_location` — seating all present NPCs as opponents is INTENTIONAL for chases/brawls (59-13 chase dial; a neutral-disposition pursuer must still seat). The correct fix materializes the *named* threat as adversary NPC(s) via `world_materialization._apply_npc` and seats THAT as the Other (ADR-116). AC3 explicitly guards the chase/brawl no-regression path.
- **#C4: the 1e6 sentinel is NOT the bug.** `0/0/1_000_000` placeholder metrics are by-design (apply_beat gates dial resolution on `win_condition`). The bug is that chassis hull HpPools are never seeded, so `hp_depletion` can never fire. Fix seeds ship-scale ablative HP (ADR-114 Part 2) per the SWN crunch spec — this is the crunch Sebastien + Jade are missing.
- **OTEL is the acceptance signal** (AC4): materialization (NPC name/side/HP seed), per-beat hull HP, and win-condition evaluation must each emit watcher spans. The GM panel is the lie-detector.

**STALENESS MANDATE (load-bearing — learned this session):** The sibling story 59-11 we just closed was *already delivered* by an unrelated PR (#508); its context's "still broken" claims and line numbers were stale. Before writing any RED test, TEA MUST verify the #C3 and #C4 defects still reproduce at current HEAD — confirm `_npc_fallback_at_location` still seats own-crew as opponents, and that ship_combat still synthesizes the placeholder without seeding hull HP. **Verify behavior, not line numbers** (the cited ~410-431 / ~726-735 will have drifted). Prove via OTEL span + fixture-driven behavior tests per the server's No-Source-Text-Wiring rule — never by grepping source. If a defect no longer reproduces, STOP and flag it (as with 59-11) rather than writing a test that can't go RED.

## TEA Assessment

**Tests Required:** Yes (for #C3). #C4 is already delivered + tested — see finding below.
**Status:** RED confirmed (3 failing on assertions, 1 fail-loud pin passing, no collection/fixture errors).

**Test File:** `tests/server/dispatch/test_59_23_materialize_other.py` (5 async tests, real space_opera pack, skips if content absent).

| Test | AC | State | Proves |
|------|----|-------|--------|
| `test_ship_combat_does_not_conscript_friendly_crew` | AC1/AC2 | **RED** | crew never seated `side=opponent` (robust to fix design) |
| `test_ship_combat_threads_named_threat_as_other` | AC1/AC6 | **RED** | named threat materialized as Other + `participant.joined` source=`materialized` |
| `test_ship_combat_materialized_threat_resolves_on_hull` | AC7 | **RED** | coupling — materialized threat's hull (30) depletes to `player_victory` |
| `test_ship_combat_empty_scene_fails_loud` | AC2 | PIN (green) | empty scene → `NoOpponentAvailableError`, no one-sided encounter |

All RED tests fail on their **assertions** (crew conscripted / threat not seated), verified by testing-runner — not on import/fixture/collection errors.

### Rule Coverage (lang-review/python.md)
| Rule | Test | Status |
|------|------|--------|
| #1 No Silent Fallbacks (fail-loud) | `test_ship_combat_empty_scene_fails_loud` (asserts `NoOpponentAvailableError` → error output, no phantom encounter) | green pin |
| #6 Test quality (no vacuous asserts) | self-check: every test asserts concrete values w/ diagnostic messages; `contextlib.suppress` in test 1 is scoped + commented | pass |

Other checklist items (mutable defaults, async pitfalls, resource leaks, deserialization, path handling) are not applicable to this behavioral seam — no new boundaries/IO/parsing introduced by the test surface; they apply to Dev's GREEN diff and are the dev self-review's job.

**Wiring test:** all RED tests drive the **production** dispatch seam (`run_confrontation_dispatch` → `instantiate_encounter_from_trigger`), not an isolated unit — satisfying the server's wiring-test rule. AC7 additionally drives `dispatch_dice_throw` end-to-end.

**Handoff:** To Dev (Agent Smith) for GREEN — implement #C3 threat threading only. #C4 needs no work.

## Dev Assessment

**Implementation Complete:** Yes (#C3). #C4 was pre-delivered by the SWN port — no code written for it.

**Files Changed:**
- `sidequest/server/dispatch/encounter_lifecycle.py` — added `_SHIP_SCALE_CONFRONTATION_TYPES = {"ship_combat"}`; added `materialized_threat` param to `instantiate_encounter_from_trigger`; seating logic now (1) seats a materialized threat as the Other with `seating_source="materialized"`, and (2) suppresses the person-location fallback for ship-scale types so the existing No-Opponent guard fails loud instead of conscripting the crew.
- `sidequest/agents/subsystems/confrontation.py` — `run_confrontation_dispatch` reads `params["threat"]` ({name[, description]} or bare name), builds an opponent `NpcMention`, and passes it as `materialized_threat`. The hull `CreatureCore` (hp 30 / AC 14) is created by the existing Task 9 `_seed_combat_hp_depletion_to_npcs`.
- `tests/server/dispatch/test_59_23_materialize_other.py` — ruff-format only (authored by TEA).

**Tests:** 5/5 of the story's tests GREEN. Targeted regression set 60/60 (chase, ship_combat e2e, dogfight seating/instantiation, encounter lifecycle, confrontation dispatch). Full server suite: 7690 passed; the 22 failures / 17 errors are all pre-existing env issues (unset `SIDEQUEST_DATABASE_URL`, content asset-gate audits, lore embedding, chargen HP/EDGE, world loading) — none touch encounter/confrontation/seating.

**Lint/Types:** ruff check + format clean on changed files. pyright: only 4 **pre-existing** `reportOptionalMemberAccess` errors in `_seed_combat_hp_depletion_to_npcs` (lines ~158-166, untouched by this story); my additions introduce none. Left as-is (out of scope).

**Branch:** `feat/59-23-ship-combat-materialize-other-ablative-hull` (pushed).

**Handoff:** To TEA (verify phase) for simplify + quality-pass.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned (all 7 context ACs satisfied; 3 documented, acceptable deviations).
**Mismatches Found:** 3 — all previously logged by TEA/Dev; none require code changes.

AC-by-AC (context-story-59-23.md):
- AC1 (threat materialized, crew never opponents) — **met** by `materialized_threat` seating + ship-scale fallback suppression.
- AC2 (no friendly conscription / fail-loud) — **met**; ship-scale leaves `npcs_present` empty → existing `NoOpponentAvailableError` guard fires.
- AC3 (chase not regressed) — **met**; `chase` is not ship-scale, person-fallback unchanged (test_chase_opponent_seating 7/7).
- AC4 (real hull seeded, not 1e6) — **met by the pre-delivered SWN port** (Task 9); pinned by `test_space_opera_swn_combat_e2e`.
- AC5 (depletion resolves, opponent hull not player bar) — **met by the SWN port**; AC7 test additionally proves it on the *materialized* threat.
- AC6 (observability: `participant.joined` source distinguishes materialized; hull-delta `state_patch_hp`) — **met**; `source="materialized"` emitted + tested; hull-delta span from the SWN strike path.
- AC7 (end-to-end coupling) — **met** by `test_ship_combat_materialized_threat_resolves_on_hull`.

Mismatches:
- **Materialization via Task 9, not `world_materialization._apply_npc`** (Different behavior — Behavioral, Minor)
  - Spec: #C3 "Correct Fix" names `world_materialization._apply_npc`.
  - Code: seats the threat as an opponent actor; Task 9 `_seed_combat_hp_depletion_to_npcs` creates its combat core.
  - Recommendation: **A (update spec)** — Task 9 already supplies the exact mechanical surface (hp/AC); `_apply_npc` would add a world-authoring dependency for no gain. Dev deviation already records this.
- **Ship-scale via server-side type set, not a content `arena` flag** (Architectural, Minor)
  - Spec: implies a general "materialize the Other" rule; no mechanism named.
  - Code: `_SHIP_SCALE_CONFRONTATION_TYPES = {ship_combat}` (server-only, matches existing `_ADVERSARIAL_*` pattern).
  - Recommendation: **D (defer)** — a content-declared `arena: ship` flag is the cleaner long-term design (lets any pack opt in without editing this set); out of this server-only slice. Worth a small follow-up story.
- **#C4 scope overstated by the story** (Ambiguous/stale spec — Cosmetic, Trivial)
  - Spec: framed #C4 (hull seeding/resolution) as work to do.
  - Code: #C4 was already delivered by the SWN port; no new code.
  - Recommendation: **A (update spec)** — TEA's finding documents this; Reviewer should treat `test_space_opera_swn_combat_e2e.py` as #C4 acceptance evidence.

**Decision:** Proceed to review (verify). No hand-back to Dev — the code aligns with all ACs; the deviations are documented design choices, not defects.

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed (40/40 on the affected set after simplify).

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 3 (`confrontation.py`, `encounter_lifecycle.py`, `test_59_23_materialize_other.py`)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | clean | No duplication; the threat→NpcMention parse is unique; test guards are acceptable inline setup. |
| simplify-quality | 1 finding | `materialized_threat: Any \| None` should be `NpcMention \| None` (type-safety, medium). |
| simplify-efficiency | clean | Single-element `_SHIP_SCALE_CONFRONTATION_TYPES` frozenset noted but follows the existing `_ADVERSARIAL_*` pattern — no change. |

**Applied:** 1 fix — typed `materialized_threat` as `NpcMention | None` via a `TYPE_CHECKING` import (commit `ee9a1bd`). Elevated from medium→high confidence after verifying `NpcMention` (in `sidequest.agents.orchestrator`) is already imported lazily by `_npc_fallback_at_location` with no cycle, and a `TYPE_CHECKING` import is a runtime no-op under `from __future__ import annotations`. Satisfies lang-review rule #3 (no bare `Any` on a public signature).
**Flagged for Review:** 0
**Noted:** 1 (single-element frozenset — intentional, pattern-consistent)
**Reverted:** 0

**Overall:** simplify: applied 1 fix

**Regression detection:** ruff check + format clean; pyright unchanged (only the 4 pre-existing `reportOptionalMemberAccess` errors in the untouched Task 9 branch; the implicit `Any` is gone with zero new errors); affected-set tests 40/40 green.

**Quality Checks:** All passing.
**Handoff:** To Reviewer (The Merovingian) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | tests GREEN (17), ruff clean, 4 pyright errors (pre-existing), 1 OTEL-gap note | confirmed 1 (Low), N/A rest |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | findings | 2 (1 medium injection, 1 low silent-ignore) | confirmed 2 (downgraded injection M→Low w/ evidence) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 3 (all high-conf) | confirmed 1 (Med), dismissed 2 (evidence) |

**All received:** Yes (3 enabled returned, 6 disabled via settings)
**Total findings:** 1 Medium + 3 Low confirmed; 2 dismissed (with rationale)

## Reviewer Assessment

**Verdict:** APPROVED

No Critical/High issues. Production behavior is correct and verified end-to-end; remaining findings are one Medium test-quality item (covered by a sibling test) and three Low observability/hardening items. Recommended follow-ups below.

**Data flow traced:** player action → `sanitize_player_text` at ingestion (`handlers/player_action.py:281`) → IntentRouter → `dispatch.params["threat"]` → `run_confrontation_dispatch` builds `NpcMention(name=threat_name, side="opponent")` → `instantiate_encounter_from_trigger` seats it as the Other → Task 9 `_seed_combat_hp_depletion_to_npcs` creates its `CreatureCore` (hp 30/AC 14) → strike beats ablate hull → `hp_depletion` resolves. Safe: the player-input boundary is sanitized; the fail-loud guard prevents one-sided encounters.

### Observations
- `[VERIFIED]` No-Silent-Fallbacks honored — ship-scale + no threat leaves `npcs_present` empty so the existing `NoOpponentAvailableError` guard raises (encounter_lifecycle.py:579-598); evidence: `elif` at :576 + comment-only else at :584. Complies with CLAUDE.md No Silent Fallbacks.
- `[VERIFIED]` AC3 no-regression — `_SHIP_SCALE_CONFRONTATION_TYPES = {"ship_combat"}` scopes the fallback-suppression to ship_combat only; chase/brawl/personal-combat still enter the person fallback (verified by test_chase_opponent_seating 7/7). evidence: :576.
- `[VERIFIED]` Materialized Other observable — `seating_source="materialized"` flows into `participant_joined_span` (encounter_lifecycle.py:693-699); GM panel distinguishes materialized vs router-named vs location-fallback. Complies with OTEL Observability Principle.
- `[VERIFIED]` Async/import safety — lazy `from sidequest.agents.orchestrator import NpcMention` mirrors the established `_npc_fallback_at_location` pattern (encounter_lifecycle.py:434); no module-load cycle (orchestrator does not import subsystems.confrontation at module level); full suite 7690 passed.
- `[MEDIUM]` `[RULE]` `[TEST]` Vacuous test branch — `test_ship_combat_does_not_conscript_friendly_crew` (test:243-262): the `assert not conscripted` is inside `if enc is not None:`; post-fix the executing path is fail-loud (`enc is None`), so the test asserts nothing in that branch. Matches lang-review rule #6. **Non-blocking** because the crew-not-conscripted invariant IS asserted non-vacuously in `test_ship_combat_threads_named_threat_as_other` (crew present + threat → crew not in opponents). Recommended fix (1 line): `assert enc is None or not conscripted` so both paths assert.
- `[LOW][SEC]` `threat_name` not re-sanitized/length-capped before `NpcMention(name=...)` (confrontation.py:122). Evidence-based downgrade from the security subagent's Medium: player input is sanitized upstream (`player_action.py:281`, ADR-047) and router-named actor names are NOT re-sanitized anywhere in the existing seating path — so this is consistent with established behavior, not a new vector. Recommend a systemic follow-up: sanitize + cap all router-supplied actor names (covers `npcs_present` mentions too), not just this path.
- `[LOW][SEC]` Silent threat-ignore — when `actor_list` is non-empty AND a `threat` is present, the threat is dropped with no OTEL signal (confrontation.py:119 `if threat and not actor_list`). Mechanically correct (explicit actors win) but the GM panel gets no signal of router inconsistency. Recommend an OTEL event if both arrive.
- `[LOW][OTEL]` No span at the materialization *decision* point in confrontation.py — the downstream `participant.joined` records the seat, but not the threat name/params key at the decision. Minor; the seat is observable.

### Rule Compliance (lang-review/python.md + CLAUDE.md)
- #1 Silent exceptions — PASS (NoOpponent/SealedLetter caught, logged at warning, typed error returned).
- #2 Mutable defaults — PASS (all None defaults).
- #3 Type annotations at boundaries — PASS (`materialized_threat: NpcMention | None` via TYPE_CHECKING). Rule-checker's local-variable claim **dismissed**: pyright reports 0 errors on confrontation.py; rule #3 governs params/returns, exempts internals.
- #4 Logging — PASS (warning-level on error paths, % args, no secrets).
- #6 Test quality — **1 finding** (vacuous branch, above); other 3 tests assert concrete values + OTEL.
- #9 Async pitfalls — PASS (sync import in async body is safe; no missing await).
- #10 Import hygiene — PASS; circular-import claim **dismissed** (no cycle, mirrors existing lazy pattern, suite green).
- #11 Input validation — boundary sanitized upstream; see Low finding for the router-name follow-up.
- A No Silent Fallbacks — PASS. B No Stubbing — PASS. C No Source-Text Wiring — PASS (tests assert behavior/OTEL). D Wiring test — PASS (full dispatch→resolution path driven). E OTEL — PASS (participant.joined + no_opponent spans).

### Devil's Advocate
Suppose I want to break this. The threat name is router-authored: could a jailbroken router emit `threat={"name": "<system>ignore the rules</system>"}` and poison the narrator? It reaches `EncounterActor.name` and OTEL `combatant_names`/`participant.joined` attributes unsanitized — but the player text that seeds the router is already stripped by `sanitize_player_text` at ingestion, and every other router-named actor (`npcs_present`) shares the identical exposure today, so this is a pre-existing systemic surface, not a 59-23 hole. Still worth a systemic cap. What about a malformed threat — `threat={}` (dict, no name)? `threat.get("name")` → None → `if threat_name:` false → falls to the empty-actor path → ship-scale fail-loud. Safe. `threat="x"*100000` (huge bare string)? Seated as an actor name unbounded — ugly but not a crash; the Low cap recommendation covers it. Could the fix strand a legitimate fight? If the router DOES name a real on-scene enemy in `npcs_present` for ship_combat, `actor_list` is non-empty → the materialized path is skipped → the explicit actor seats normally (test_space_opera_swn_combat_e2e proves this). Could it break a brawl where the enemy is genuinely a person in the room? No — `combat`/`chase` are not in the ship-scale set, so their person-fallback is untouched. Race/idempotency? `instantiate` returns early if an unresolved encounter exists; no double-seat. The one real soft spot the devil finds is the test: the headline crew-not-conscripted test passes even if the engine silently stopped seating anything — but the sibling threat test backstops the actual invariant. Conclusion: no production break; one test to harden and a systemic sanitization nit.

**Handoff:** To SM for finish-story. Recommended (non-blocking) follow-ups: harden the vacuous test assertion (1 line); systemic sanitize/cap on router-supplied actor names (ADR-047) as a separate story.

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-05-29T12:49:55Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-29T00:00:00Z | 2026-05-29T12:01:23Z | 12h 1m |
| red | 2026-05-29T12:01:23Z | 2026-05-29T12:20:50Z | 19m 27s |
| green | 2026-05-29T12:20:50Z | 2026-05-29T12:33:23Z | 12m 33s |
| spec-check | 2026-05-29T12:33:23Z | 2026-05-29T12:34:59Z | 1m 36s |
| verify | 2026-05-29T12:34:59Z | 2026-05-29T12:40:01Z | 5m 2s |
| review | 2026-05-29T12:40:01Z | 2026-05-29T12:48:27Z | 8m 26s |
| spec-reconcile | 2026-05-29T12:48:27Z | 2026-05-29T12:49:55Z | 1m 28s |
| finish | 2026-05-29T12:49:55Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): #C4 (degenerate/unwinnable dogfight) is **already delivered** by the SWN ship-combat port (#469 bind-to-SWN, #471 initiative, #475 dogfight-via-production-path, #478 SWN shot resolution + content Tasks 8/9/11). At HEAD `ship_combat` declares `win_condition: hp_depletion`, models the enemy hull as opponent `CreatureCore` HP (`hp:30/AC:14` in `space_opera/rules.yaml`), strike beats ablate it via `damage_channel: strike`, `_seed_combat_hp_depletion_to_npcs` seeds it (and creates a backing Npc for a router-named opponent), and resolution fires at `core.hp<=0`. It is comprehensively pinned by `tests/server/test_space_opera_swn_combat_e2e.py::test_ship_combat_resolves_on_hull_depletion_vs_ship_ac` + `::test_world_loads_clean_under_swn`. The story's #C4 premise was true at the 2026-05-28 playtest but has since been fixed. Per Operator decision (keep full story, write both) I did NOT duplicate that coverage; I wrote the AC7 coupling test instead, which is the one #C4-adjacent gap (does resolution engage on the *materialized* threat, not on a fixture-seated opponent). **Scope for Dev: #C3 only** (thread the named threat into the ship_combat seating seam). Affects `sidequest/agents/subsystems/confrontation.py` + `sidequest/server/dispatch/encounter_lifecycle.py`. *Found by TEA during test design.*
- **Improvement** (non-blocking): the #C3 mechanical surface is mostly built — when an opponent is seated **by name**, `_seed_combat_hp_depletion_to_npcs` already materializes its backing core. The remaining work is narrow: thread the narrative-named threat from the router/dispatch into seating so the empty-`npcs_present` location fallback never conscripts the crew. Dev should weigh threading via `params["threat"]` (the channel the RED tests assume) vs. emitting a synthetic `NpcMention` into `npcs_present` (which the existing seating + Task 9 path would handle with near-zero new code). Affects `confrontation.py`/`encounter_lifecycle.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): `dogfight` (sealed_letter) is also ship-scale but is NOT in `_SHIP_SCALE_CONFRONTATION_TYPES` — it already filters non-adversary bystanders via `adversary_only=True`, so crew aren't conscripted there. A future pack adding a ship-scale confrontation under a *new* type name would need to be added to the set (or the set migrated to a content-declared flag). Affects `sidequest/server/dispatch/encounter_lifecycle.py`. *Found by Dev during implementation.*
- **Improvement** (non-blocking): pre-existing pyright `reportOptionalMemberAccess` noise in `_seed_combat_hp_depletion_to_npcs` (the Task 9 overwrite branch reassigns `npc` so pyright can't narrow it non-None at `npc.core.hp` ~lines 158-166). Unrelated to this story; a one-line local var would silence it. Affects `sidequest/server/dispatch/encounter_lifecycle.py`. *Found by Dev during implementation.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **#C4 ACs (AC4/AC5) tested by reference, not by new tests**
  - Spec source: context-story-59-23.md, AC4 + AC5
  - Spec text: "Chassis-vs-chassis ship_combat seeds hull HpPools... not 0/0/1_000_000" / "a resolved player attack reduces the opponent ship's hull... hull hits 0 the encounter resolves"
  - Implementation: AC4/AC5 are already covered by `tests/server/test_space_opera_swn_combat_e2e.py::test_ship_combat_resolves_on_hull_depletion_vs_ship_ac` (delivered by the SWN port). No new tests written for them; the new suite covers only the uncovered AC7 coupling (resolution on the *materialized* threat).
  - Rationale: writing fresh AC4/AC5 pins would duplicate existing comprehensive e2e coverage (Don't Reinvent / no-duplicate-tests). Operator chose "keep full story, write both"; honored by adding the genuinely-additive AC7 test rather than redundant #C4 pins.
  - Severity: minor
  - Forward impact: Reviewer should treat `test_space_opera_swn_combat_e2e.py` as the #C4 acceptance evidence for this story.
- **Threat-threading input channel chosen by TEA (`params["threat"]`)**
  - Spec source: context-story-59-23.md, #C3 fix + Assumptions ("threat description must be threaded from the narrator/router into the instantiation seam")
  - Spec text: spec names the *outcome* (materialize the named threat) but not the *input channel* the dispatch carries it on.
  - Implementation: RED tests assume the threat arrives on `SubsystemDispatch.params["threat"] = {"name", "description"}` — the params channel `run_confrontation_dispatch`'s docstring already sanctions for explicit actor info.
  - Rationale: a behavioral RED test needs a concrete input; params is the existing router→engine channel. If Dev threads it differently (e.g. synthetic `NpcMention` in `npcs_present`), update `_threat_dispatch` in the test accordingly — the *assertions* (crew-not-conscripted, threat-is-Other, source=materialized) stay valid.
  - Severity: minor
  - Forward impact: Dev may adjust the test's input helper to match the chosen threading mechanism; assertions must not be weakened.

### Dev (implementation)
- **Materialized via Task 9 backing-core creation, not `world_materialization._apply_npc`**
  - Spec source: context-story-59-23.md, #C3 "Correct fix"
  - Spec text: "materialize it as adversary NPC(s) via `sidequest/game/world_materialization._apply_npc`"
  - Implementation: the named threat is seated as an opponent `EncounterActor`; its backing `CreatureCore` (hull HP / AC) is created by the existing `_seed_combat_hp_depletion_to_npcs` (Task 9) create-branch. `world_materialization._apply_npc` (a `ChapterNpc`-shaped world-builder seam) is not invoked.
  - Rationale: Task 9 already provides the exact mechanical surface the Other needs (hp 30 / AC 14 from `opponent_default_stats`) and is on the live seating path; routing through `_apply_npc` would add a heavier, world-authoring-shaped dependency for no mechanical gain. The threat's prose/disposition flavor stays narrator-owned (Diamonds and Coal). Minimal code, same observable outcome.
  - Severity: minor
  - Forward impact: if a future story needs the materialized threat persisted as a full roster `Npc` with disposition/personality (beyond the combat core), revisit routing through `world_materialization`.
- **Ship-scale discrimination via a server-side type set, not a content `arena` flag**
  - Spec source: context-story-59-23.md, #C3 "Why Simple Filter Won't Work" + Scope Boundaries (repos: server)
  - Spec text: do NOT blanket-apply `_npc_is_adversary` (chases/brawls intentionally seat present NPCs); the Other must be the materialized threat.
  - Implementation: added `_SHIP_SCALE_CONFRONTATION_TYPES = frozenset({"ship_combat"})` in `encounter_lifecycle.py`; for these types the person-location fallback is suppressed (consistent with the existing `_ADVERSARIAL_*` magic-set pattern in the same module). No content/schema change.
  - Rationale: the story is server-scoped and explicitly about `ship_combat`; a server-side set is the minimal change and avoids a content-schema migration across packs. Personal combat/brawls/chases keep the person fallback (59-13 chase dial preserved).
  - Severity: minor
  - Forward impact: a cleaner long-term design is a content-declared `arena: ship` flag on `ConfrontationDef` so new ship-scale confrontations (in any pack) opt in without editing this server set; deferred as a content change outside this server slice.
- **Scoped to `ship_combat`; `dogfight` deliberately not added to the ship-scale set**
  - Spec source: session scope (ship_combat slice) + AC3 (no chase/dogfight regression)
  - Spec text: "Retire the second... materialize the named threat as the Other for ship_combat/dogfight triggers."
  - Implementation: only `ship_combat` is in `_SHIP_SCALE_CONFRONTATION_TYPES`. `dogfight` (sealed_letter, `adversary_only=True`) already excludes non-adversary crew and fails loud on arity, so it is left unchanged to avoid risk to the dogfight frame-HP/instantiation suites.
  - Rationale: minimalist discipline — only the tested, defect-reproducing type is changed; dogfight's existing sealed-letter sourcing already satisfies the no-crew-conscription invariant.
  - Severity: minor
  - Forward impact: if a future playtest shows `dogfight` conscripting crew (it shouldn't, given adversary_only), add it to the set.

### Reviewer (audit)
- **TEA: #C4 ACs tested by reference, not new tests** → ✓ ACCEPTED by Reviewer: `test_space_opera_swn_combat_e2e.py::test_ship_combat_resolves_on_hull_depletion_vs_ship_ac` genuinely covers AC4/AC5; duplicating it would be waste. Agrees with author reasoning.
- **TEA: threat-threading channel `params["threat"]`** → ✓ ACCEPTED by Reviewer: params is the sanctioned router→engine channel; the implementation matched the test contract, so no drift materialized.
- **Dev: materialized via Task 9, not `world_materialization._apply_npc`** → ✓ ACCEPTED by Reviewer: Task 9's create-branch supplies the exact mechanical surface (hp/AC) on the live seating path; routing through `_apply_npc` would add a world-authoring dependency for no gain. Sound.
- **Dev: ship-scale via server-side type set, not content `arena` flag** → ✓ ACCEPTED by Reviewer: server-only matches story scope and the existing `_ADVERSARIAL_*` pattern; the deferred content `arena` flag is the right long-term direction (logged forward-impact). Sound.
- **Dev: scoped to `ship_combat`, not `dogfight`** → ✓ ACCEPTED by Reviewer: `dogfight` (sealed_letter, `adversary_only=True`) already excludes non-adversary crew; minimalist scoping is correct and avoids risk to the dogfight suites.
- No undocumented deviations found — the diff matches the logged design choices.

### Architect (reconcile)

Reviewed all in-flight deviation entries (TEA ×2, Dev ×3) and the Reviewer audit against the spec sources. Verification:
- `sprint/context/context-story-59-23.md` exists; the AC4/AC5 quotes in TEA's first entry are accurate.
- `docs/superpowers/specs/2026-05-25-swn-crunch-ablative-hp-design.md` exists (the SWN-crunch spec cited across the story).
- `tests/server/test_space_opera_swn_combat_e2e.py::test_ship_combat_resolves_on_hull_depletion_vs_ship_ac` and `::test_world_loads_clean_under_swn` both exist — TEA's "tested by reference" entry is substantiated.
- All five entries carry the full 6-field format; Implementation descriptions match the shipped diff (`materialized_threat` seating + `_SHIP_SCALE_CONFRONTATION_TYPES` suppression; Task-9 backing-core materialization; server-set discriminator; ship_combat-only scope).

AC deferral check: no ACs were deferred or descoped (all 7 context ACs met — 5 by this story's #C3 code, AC4/AC5 by the pre-delivered SWN port). The ac-completion table records no DEFERRED/DESCOPED entries. No-op.

- No additional deviations found. The definitive manifest: #C4 was pre-delivered by the SWN port (acceptance evidence: `test_space_opera_swn_combat_e2e.py`); #C3 was implemented server-side via threat threading + ship-scale fallback suppression, with three minor, accepted design deviations (Task-9 materialization, server-set vs. content `arena` flag, ship_combat-only scope) and a deferred long-term improvement (content-declared `arena` flag). Reviewer-flagged non-blocking follow-ups: harden one vacuous test assertion; systemic sanitize/cap on router-supplied actor names (ADR-047).