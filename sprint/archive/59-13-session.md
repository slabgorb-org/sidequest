---
story_id: "59-13"
jira_key: null
epic: "59"
workflow: "tdd"
---
# Story 59-13: Chase confrontation write-back — apply beat metric delta, transition Setup->active, seat opponent (INERT-chase dual-dial frozen 0/7)

## Story Details
- **ID:** 59-13
- **Epic:** 59 (Intent Router — Mechanical-Engagement Spine)
- **Jira Key:** N/A (sprint-YAML only, no Jira for SideQuest)
- **Workflow:** tdd
- **Repos:** sidequest-server
- **Priority:** P1
- **Points:** 5
- **Type:** bug
- **Stack Parent:** none (independent story)

## Story Context

**Category:** Mechanical-engagement spine restoration (Epic 59)

**Problem:** Chase confrontations (opposed_check type) fail to execute write-back logic on beat metric deltas. After the intent router dispatches a chase confrontation and instantiates a StructuredEncounter, the engine computes beat selections and mechanics but never applies the resulting state delta back to the snapshot. Symptoms:
- Chase dual-dial frozen at 0/7 (no progress visible in UI)
- Opponent seat empty (NPC not placed on the encounter)
- State transitions fail (Setup→active phase never fires)
- OTEL shows `chase.advance()` call but no `encounter.updated` span post-engagement

**Root cause location:** The confrontation handler (subsystems/confrontation.py) invokes `advance_confrontation()` (narration_apply.py) which delegates to the engaged subsystem's `.advance()` method, but the handler does NOT consume the returned `BeatChangeSet` (or equivalent mutation result) and apply it back to the snapshot BEFORE returning. Compare with confrontation write-back shapes used in resolved (victory/defeat) encounters — the resolved path DOES snapshot-patch the state, but mid-engagement write-back is missing.

**Related stories:**
- 59-4: Confrontation cutover (wiring the router into the pipeline)
- 59-7: Wire three LocalDM subsystems (npc_agency, distinctive_detail, reflect_absence) — added dispatch wiring but no mid-engagement beat write-back
- 59-11: Retire redundant dispatch-bank second run (left the first run's BankResult in-scope; that carry-through is pre-req for this story)

**Design constraint:** Chase is a stateful opposed_check subsystem living in sidequest/game/confrontation/chase.py. Its `.advance()` method returns a beat mutation (likely per ADR-024 or subsystem internal contract). The handler must:
1. Call `.advance()` (already happens)
2. Inspect the returned beat delta
3. Apply the delta to the encounter's beat pool on the snapshot (MISSING)
4. Emit OTEL span for the beat-write-back (visibility to GM panel)

**Acceptance criteria:**
- Synthetic fixture: dispatch a chase confrontation → handler calls `.advance()` and seat the opponent → snapshot post-call shows updated beat dialwith opponent seated and beat pool populated (not 0/7)
- Behavioral: multi-turn chase progression shows increasing beat count and beat-pool state-machine transitions in OTEL encounter.beat_delta spans
- Live session: run a space_opera dogfight (which uses chase mechanics per ADR-077 or pack config) and verify dual-dial animates in UI (not frozen)
- OTEL wiring test: beat write-back emits encounter.beat_delta span (existing telemetry family), chase_advance span includes before/after beat state, lethality arbiter can read post-write-back state

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-05-26T14:44:36Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-26T13:31:00Z | 2026-05-26T13:32:43Z | 1m 43s |
| red | 2026-05-26T13:32:43Z | 2026-05-26T14:20:05Z | 47m 22s |
| green | 2026-05-26T14:20:05Z | 2026-05-26T14:30:19Z | 10m 14s |
| spec-check | 2026-05-26T14:30:19Z | 2026-05-26T14:32:41Z | 2m 22s |
| verify | 2026-05-26T14:32:41Z | 2026-05-26T14:39:27Z | 6m 46s |
| review | 2026-05-26T14:39:27Z | 2026-05-26T14:43:38Z | 4m 11s |
| spec-reconcile | 2026-05-26T14:43:38Z | 2026-05-26T14:44:36Z | 58s |
| finish | 2026-05-26T14:44:36Z | - | - |

## Sm Assessment

**Routing:** tdd / phased → TEA (RED phase). Merge gate clear (no open PRs across any repo). Branch `feat/59-13-chase-confrontation-writeback` created off sidequest-server/develop. Story context satisfied by embedded Story Context section.

**Hypothesis flag (load-bearing — do NOT treat the session's root cause as verified):**
- The root cause ("handler doesn't consume the returned `BeatChangeSet` from `.advance()` in `narration_apply.py`") is the setup agent's hypothesis. TEA/Dev must confirm it with a logged request/response on the real pack before building the fix around it. Measure, don't assert.
- **Chase is `opposed_check`.** Per prior wiring-trap experience, combat/chase-mutation fixes must wire the `narration_apply` (opposed_check) path, not just `dispatch_dice_throw` (simple-DC). A dispatch-only fix no-ops in real play.
- AC1's synthetic fixture is necessary but **not sufficient**. The opposed e2e must be driven against the real pack — AC3's live space_opera dogfight (chase mechanics per ADR-077) is the actual lie-detector. Confirm the dual-dial animates and OTEL `encounter.beat_delta` fires.
- Emit OTEL on the beat write-back (OTEL Observability Principle) so the GM panel can verify the dial moved for mechanical reasons, not narrator improv.

## Architect Assessment (design — out-of-band, ADR-116)

**Summoned by user mid-RED for a design pass; user authority overrode the phase router. Returning to TEA after capturing the decision.**

**What measurement found (Igor's probes, `tests/server/test_chase_writeback_probe.py`):**
- Chase beat **write-back works** — opponent dial 0→2, phase Setup→Opening — when an opponent is seated. The story's stated root cause (handler doesn't consume `BeatChangeSet`) is **false**.
- Real defect: chase **instantiates with no opponent seated** → opponent beats skip → dial frozen at 0.

**Larger problem:** the engine has no enforced concept of *who is in the confrontation*. Membership primitives already exist (`actors`/`side`/`withdrawn`); what's missing is opponent **entry discipline**, the **"needs an Other" invariant**, and opponent-**exit→resolve** (the mirror of `yield_action`'s player path).

**Decision — ADR-116 "A Confrontation Requires an Other"** (`docs/adr/116-confrontation-requires-an-other.md`). User rulings: "solo ≠ opponentless," race-against-time = narration (not a confrontation), **Fork A = room-only sourcing**, **Wild Card #9 = end-on-no-Other accepted**. Reuse-first: no new participant type.

**59-13 re-scoped to the ADR-116 *movement slice*** — see corrected `sprint/context/context-story-59-13.md`:
1. Single opponent-seater: chase with no named opponent → seat from room `snapshot.npcs` (NPCs + bestiary mobs) as `side="opponent"`.
2. Generalize the `NoOpponentAvailableError` guard to `movement` (raise → narrator prose). **Do NOT** flip `social`/`pre_combat` (staged follow-up; protect `victoria`/`tea_and_murder`).
3. End-on-no-Other for chase (reuse `opponent_alive_count`).
4. OTEL `participant.joined`/`participant.left`. Update `EncounterActor.side` docstring.

**Notes for TEA (Igor):** Use `load_genre_pack(_FIXTURE_PACK)` (test_genre has chase), NOT the conftest combat-only pack. The stale `chase_*_goal10.json` fixtures use the rejected legacy `metric` shape — build encounters in-code. Prove wiring via OTEL/fixture behavior, never source-grep. My probe file is throwaway evidence — convert to proper RED tests or delete; don't ship it as-is.

## TEA Assessment

**Tests Required:** Yes
**Test File:** `sidequest-server/tests/server/test_chase_opponent_seating.py` — 7 tests covering ADR-116's 4 ACs.
**Status:** RED (7 failed, lint-clean, committed `0286d82`). Throwaway probe `test_chase_writeback_probe.py` deleted.

**RED verified for the right reasons (not import errors):**
| AC | Test | Fails because (today) |
|----|------|----------------------|
| AC1 | `test_chase_seats_room_npc_as_opponent` | `actors=[(Sam,player),(Road Raider,**neutral**)]` — pursuer seated neutral |
| AC1 | `test_chase_seats_bestiary_mob_as_opponent` | mob (`creature_id`) seated neutral |
| AC1 | `test_chase_opponent_seating_emits_participant_joined_span` | no `participant.joined` span exists |
| AC2 | `test_chase_with_empty_room_raises_no_opponent` | `DID NOT RAISE` — movement exempt from guard |
| AC2 | `test_chase_with_empty_room_does_not_create_one_sided_encounter` | `actors=[(Sam,player)]` only |
| AC3 | `test_chase_dial_advances_after_production_seating` | opponent dial frozen at 0 (beat skipped: neutral_actor) |
| AC4 | `test_chase_resolves_when_last_opponent_withdraws` | encounter not resolved on last-opponent-withdraw (seam unwired). **Isolated** via direct encounter construction so it fails for its own reason, not AC1's. |

### Rule Coverage
| Rule (CLAUDE.md / SOUL) | Test | Status |
|------|------|--------|
| No Silent Fallbacks | `..._raises_no_opponent` / `..._does_not_create_one_sided_encounter` (one-sided chase must fail loud) | failing |
| Every suite needs a wiring test | `..._emits_participant_joined_span` / AC3 end-to-end through production `instantiate_encounter_from_trigger` + `_apply_narration_result_to_snapshot` | failing |
| No Source-Text Wiring Tests | wiring proven via OTEL span + fixture-driven behavior, never source-grep | satisfied |
| OTEL Observability Principle | `participant.joined` (AC1) + `participant.left` (AC4) membership spans | failing |
| Gaslighting / one roster | AC1 mob test uses `creature_id` (bestiary) seated from same `snapshot.npcs` | failing |

**Self-check:** every test has a meaningful assertion (concrete `side`/dial/resolved values, span presence). No vacuous `is_some()`/`assert True`. AC4 de-coupled from AC1.

**Handoff:** To Dev (Ponder) for GREEN — implement ADR-116 movement slice.

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report
**Teammates:** reuse, quality, efficiency · **Files Analyzed:** 4 (diff-scoped)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | clean | join/left span symmetry + guard-span repetition judged intentional (consistent with the spans module / OTEL discipline) |
| simplify-quality | clean | naming/types/architecture/error-handling all conform; spans wired to production paths |
| simplify-efficiency | clean | no over-engineering; per-actor join spans & double opponent filter are intentional observability/clarity |

**Applied:** 0 simplify fixes (all clean).
**Carry-forward fixes applied this phase:**
1. `EncounterActor.side` docstring reconciled with ADR-116 §2 (spec-check carry-forward) — commit `c519dbd`.
2. `_validate_side` return typed `ActorSide` (was `str`) — cleared 2 latent pyright errors surfaced when ruff-format pulled the seating loop into the diff — commit `a1eb619`.

**Overall:** simplify: clean.

**Regression checks:** ruff clean; pyright clean on changed files (0 errors, was 2); targeted regression suites green (encounter lifecycle/actors/apply, sealed-letter, apply_beat, confrontation dispatch, story = 98 + 47 passed across runs). Full-suite 14 failures remain pre-existing/unrelated (61-14/61-15/59-16/64-7), unchanged by this story.

**Handoff:** To Reviewer (Granny Weatherwax) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 smells; 7 story + 446 encounter/confrontation tests GREEN; lint clean | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | clean | 0 (No-Silent-Fallbacks ✓, perception/broadcast ✓, OTEL payload ✓) | confirmed 0, dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received: Yes** (2 enabled subagents returned; 7 disabled via settings).

## Reviewer Assessment (Granny Weatherwax)

**Verdict: APPROVE.** Both enabled subagents clean; my own adversarial read found two non-blocking limitations, neither introduced as a regression.

**Subagent adjudication:** preflight GREEN (7 story + 446 suite, 0 smells, lint clean); **[SEC]** reviewer-security returned `status: clean`, 0 findings — verified No-Silent-Fallbacks on all 4 new branches (guard raises, defensive `getattr` is attribute access not a fallback path, `_npc_fallback` returns `([],False)` with span decoration, `seating_source` default is not a path-masking default), no new broadcast/perception surface (`_resolve_if_no_opponent_remains` is a pure snapshot mutation — no `room.broadcast`/`GameMessage`), and the new `participant.joined`/`participant.left` OTEL spans carry only shared-world membership (encounter_type/name/side/source/reason) — no per-player private fields or secrets (ADR-104/105). Nothing to confirm/dismiss from either subagent.

**Reviewer's own findings (both non-blocking):**
1. **`_resolve_if_no_opponent_remains` is category-agnostic** (Low — scope/behavior). It resolves *any* encounter (combat included) when all opponents are withdrawn, not only chase — broader than the story's "movement slice" wording. *Decision: ACCEPT.* It's consistent with ADR-116 §4's general intent, is correct behavior (an encounter with no live Other should end), the player-yield path doesn't trip it (it withdraws player-side actors), and the full suite (8105) showed no regression. Belt-and-suspenders alongside dial-threshold resolution. Logged as a Dev deviation candidate but not a defect.
2. **Location fallback seats *all* co-located NPCs as `opponent`** for adversarial confrontations (Low — pre-existing limitation). A friendly/companion NPC in the room during a chase would be mis-sided as a pursuer. *Decision: ACCEPT / defer.* This is the **pre-existing** combat-fallback behavior (`_npc_fallback_at_location` already did this for combat), merely extended to movement; ADR-116 Fork A explicitly deferred richer sourcing (bestiary/encounter-table, side-aware filtering). Flagged as a delivery finding for the follow-up, not a blocker for this story.
3. *(security note)* `**attrs` pass-through on the new span helpers — pre-existing codebase pattern, no call site abuses it. Future-hardening only.

**Rule compliance:** No Silent Fallbacks ✓ (guard raises, no silent one-sided chase). OTEL Observability Principle ✓ (participant.joined/left + existing init/metric spans cover every membership decision). No Source-Text Wiring Tests ✓ (tests drive production functions + assert OTEL/behavior). Reuse-first ✓ (no new participant type; reuses actors/side/withdrawn + yield-mirror). ADR-116 staged rollout honored ✓ (movement only; social/pre_combat untouched).

**Decision:** Approve → advance to spec-reconcile (Architect), then SM finish (SM creates + merges the subrepo PR; ADR-116 + sprint artifacts committed in the orchestrator).

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

No upstream findings at setup.

### TEA (test design)
- **Conflict** (non-blocking): Story's original root cause ("beat write-back broken / handler doesn't consume BeatChangeSet") is **false** — measured: write-back works when an opponent is seated. Re-scoped to ADR-116 movement slice. Affects `sprint/context/context-story-59-13.md` (corrected by Architect) — Dev should ignore the original write-back framing.
- **Gap** (non-blocking): `_npc_fallback_at_location` seats non-combat opponents as `side="neutral"`, violating the `EncounterActor.side` "engine never infers it" docstring. Affects `sidequest/server/dispatch/encounter_lifecycle.py` (seat adversarial movement opponents as `opponent`; reconcile the docstring per ADR-116 §2).
- **Gap** (non-blocking): end-on-no-Other has no production seam — `opponent_alive_count` is computed in `confrontation_lifecycle_detector` but nothing flips `resolved` on opponent withdrawal. Affects the post-apply path (mirror `server/dispatch/yield_action.py`'s player-side resolver). Dev chooses the hook location; AC4 asserts the outcome, not the API.
- **Improvement** (non-blocking): stale chase fixtures `tests/fixtures/encounters/chase_*_goal10.json` use the rejected legacy single-`metric` shape (only `tests/game/test_encounter.py` touches them). Candidate for deletion in a cleanup story.

### Dev (implementation)
- **Improvement** (non-blocking): ADR-116's `_is_adversarial` + opponent-seating likely fixes sibling **59-16** (dogfight `snap.encounter is None` via production path) and is the natural home for **social/pre_combat** guard generalization. Affects `sidequest/server/dispatch/encounter_lifecycle.py` (extend `_ADVERSARIAL_CATEGORIES` after validating victoria/tea_and_murder). *Found by Dev during implementation.*
- **Gap** (non-blocking): 14 full-suite failures are pre-existing and tracked (61-14 ×8, 61-15 ×1, 59-16 ×1, 64-7 ×4) — not introduced here. Noted so the verify/review phase doesn't attribute them to 59-13. *Found by Dev during implementation.*

### TEA (test verification)
- **Improvement** (non-blocking): `_validate_side` returned `str` assigned to `EncounterActor.side: ActorSide` at two seating sites — latent pyright debt (pyright isn't in the standard `server-check` gate). Fixed in this phase (return typed `ActorSide`, commit `a1eb619`). Affects `sidequest/server/dispatch/encounter_lifecycle.py`. *Found by TEA during test verification.*

### Reviewer (code review)
- **Gap** (non-blocking): `_npc_fallback_at_location` seats *all* co-located `snapshot.npcs` as `side="opponent"` for adversarial confrontations — a friendly/companion NPC in the room during a chase/combat would be mis-sided as a pursuer. Pre-existing combat-fallback behavior extended to movement; ADR-116 Fork A deferred side-aware/bestiary sourcing. Affects `sidequest/server/dispatch/encounter_lifecycle.py` (`_npc_fallback_at_location` — filter by disposition or exclude player-side companions when richer sourcing lands). *Found by Reviewer during code review.*

## Architect Assessment (spec-check)

**Spec Alignment:** Drift detected (1 minor mismatch)
**Mismatches Found:** 1

- **`EncounterActor.side` docstring not reconciled** (Missing in code — Cosmetic/doc, Minor)
  - Spec: ADR-116 §2 + `context-story-59-13.md` In-scope: "Update the `EncounterActor.side` docstring to match the engine-seats-opponents reality."
  - Code: `sidequest/game/encounter.py:104` still reads *"Set at instantiation from the narrator's payload; engine never infers it"* — now false, since `_npc_fallback_at_location` seats adversarial opponents (engine-assigned side). Dev assessment did not list the docstring among files changed.
  - Recommendation: **B — fix code, routed forward to the verify phase.** It's a one-paragraph docstring edit; a backward bounce to Dev (green) is mechanically awkward (Dev can't re-enter an architect-owned phase cleanly) and disproportionate for a Minor doc-only drift. TEA's verify phase is next and its quality pass *is* permitted to edit source — Igor should reconcile the docstring there. **Carry-forward item for verify (see below).**

**⚠️ Carry-forward to verify (TEA):** edit `sidequest/game/encounter.py:104` `EncounterActor.side` docstring — replace "Set at instantiation from the narrator's payload; engine never infers it" with language reflecting ADR-116 §2: the narrator's payload sets side when present, and the engine seats adversarial opponents (combat/movement) from the location roster via `_npc_fallback_at_location`. Without this, the comment-analyzer reviewer will flag the stale invariant.

**AC alignment (substance):** AC1 (adversarial fallback side + `participant.joined`), AC2 (guard generalized to movement → raise → prose), AC3 (green end-to-end dial advance), AC4 (`_resolve_if_no_opponent_remains` + `participant.left`) all implemented and verified green. Staged rollout honored (`_ADVERSARIAL_CATEGORIES = {combat, movement}`; social/pre_combat untouched). Dev deviations (`outcome="opponent_withdrew"`, join-span for all actors) are reasonable — accept (Option A).

**Decision:** Proceed to verify (TEA). One Minor doc-drift carried forward for TEA's quality pass to fix in-place (no backward Dev bounce). No behavioral mismatches — code matches the ADR-116 contract.

## Dev Assessment

**Implementation Complete:** Yes
**Tests:** 7/7 story tests passing (GREEN). Surrounding encounter/confrontation/lifecycle suites: 67/67 green. Full suite: 8105 passed, 14 failed — **all 14 pre-existing and unrelated** (61-14 ×8 output-token compaction, 61-15 ×1 cache attribution, 59-16 ×1 dogfight production-path, 64-7 ×4 namegen corpora; counts match the sprint-research baseline exactly; none touch the seating/narration-apply/spans paths I changed).
**Branch:** `feat/59-13-chase-confrontation-writeback` (pushed, commit `acafa13`).

**Files Changed:**
- `sidequest/server/dispatch/encounter_lifecycle.py` — `_is_adversarial()` helper + `_ADVERSARIAL_CATEGORIES`; `_npc_fallback_at_location` param `is_combat`→`adversarial` seats opponents as `side="opponent"` for combat+movement; empty-opponent guard generalized combat→adversarial; `participant.joined` emitted per seated actor with `source`.
- `sidequest/server/narration_apply.py` — `_resolve_if_no_opponent_remains()` (end-on-no-Other), called at the end of `_apply_narration_result_to_snapshot`; emits `participant.left`.
- `sidequest/telemetry/spans/encounter.py` — `participant.joined` / `participant.left` span constants, routes, and emit context-managers.
- `tests/server/test_chase_opponent_seating.py` — 7 tests (TEA).

**ADR-116 staged rollout honored:** only `movement` newly enforced (combat already was); `social`/`pre_combat` intentionally NOT flipped (protects victoria/tea_and_murder). The bestiary-mob source works because mobs already live in `snapshot.npcs` (`creature_id`).

**Wiring:** `participant.joined` fires from the production `instantiate_encounter_from_trigger`; `participant.left`/resolution from production `_apply_narration_result_to_snapshot`. Both reachable end-to-end (the AC tests drive the real functions, not mocks).

**Handoff:** To Architect (spec-check) → TEA (verify).

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

No design deviations at setup.

### TEA (test design)
- **Tested against corrected (ADR-116) scope, not the original session framing**
  - Spec source: `.session/59-13-session.md` original Story Context (lines 20-47, pre-correction)
  - Spec text: "Root cause location: The confrontation handler ... does NOT consume the returned `BeatChangeSet` ... mid-engagement write-back is missing."
  - Implementation: Tests target opponent **seating** (`instantiate_encounter_from_trigger`) per ADR-116, not write-back. Measurement (probe) proved write-back works.
  - Rationale: original root cause was disproven by measurement; Architect re-scoped via ADR-116 and corrected `context-story-59-13.md` (higher authority than the original embedded framing).
  - Severity: major (changes the fix location and ACs)
  - Forward impact: combat seating (45-18) unaffected; social/pre_combat guard generalization deferred to a follow-up; sibling 59-16 (dogfight instantiation) may overlap the seating seam.
- **AC4 uses direct encounter construction instead of the production instantiation path**
  - Spec source: `sprint/context/context-story-59-13.md`, AC4
  - Spec text: "when the last opponent withdraws, the encounter resolves (+ a `participant.left` span)."
  - Implementation: AC4 test builds the `StructuredEncounter` with an opponent pre-seated rather than calling `trigger_encounter` (which is broken until AC1).
  - Rationale: isolates AC4 so it fails for its own reason (resolution unwired), not the AC1 seating precondition — otherwise AC4 would be a redundant restatement of AC1.
  - Severity: minor
  - Forward impact: none — Dev still wires the real seam; the test asserts the observable outcome.

### Dev (implementation)
- **end-on-no-Other resolves with `outcome="opponent_withdrew"`**
  - Spec source: `sprint/context/context-story-59-13.md`, AC4 + `docs/adr/116-confrontation-requires-an-other.md` §4
  - Spec text: "the encounter resolves (`resolved=True`, `outcome` reflecting the disposition)"
  - Implementation: set `outcome="opponent_withdrew"`, `structured_phase=Resolution`. The documented outcome vocabulary (`StructuredEncounter` docstring) is `player_victory|opponent_victory|resolution_beat:<id>|yielded` — `opponent_withdrew` is a new value.
  - Rationale: an opponent leaving is not a dial-threshold victory; misreporting it as `player_victory` would lie to outcome consumers. `outcome` is a free-form `str` and the AC asserts only `resolved is True` + the span.
  - Severity: minor
  - Forward impact: any consumer that switches on `outcome` literals must tolerate `opponent_withdrew` (none found keying on exhaustive outcome values; the yield path already introduced the non-victory value `yielded`).
- **`participant.joined` emitted for ALL seated actors, not only opponents**
  - Spec source: `context-story-59-13.md`, AC1
  - Spec text: "seating an opponent emits a `participant.joined` ... carrying the side"
  - Implementation: the emit loop fires for every seated actor (player + opponents), `source="seat"` for player-side else the seating source.
  - Rationale: membership is membership — a per-actor join record is more useful on the GM panel and avoids a special-case branch. AC asserts an opponent-side join exists, which holds.
  - Severity: trivial
  - Forward impact: none.
### Architect (reconcile)
- **end-on-no-Other is category-agnostic (applies to combat, not only chase)**
  - Spec source: `sprint/context/context-story-59-13.md` Scope Boundaries + `docs/adr/116-confrontation-requires-an-other.md` §4
  - Spec text: "End-on-no-Other for chase: when `opponent_alive_count` hits 0 via withdrawal, resolve the encounter." (story scope scoped the line to chase; ADR-116 §4 states the rule generally)
  - Implementation: `_resolve_if_no_opponent_remains` runs on every `_apply_narration_result_to_snapshot` and resolves ANY active encounter whose opponent-side actors are all withdrawn — combat included, not gated to `encounter_type=="chase"`.
  - Rationale: the rule is intrinsically general (an encounter with no live Other should end); gating to chase would be an artificial special-case and leave combat able to soft-lock on all-opponents-withdrawn. Consistent with ADR-116 §4 (the higher-authority general statement). Full suite (8105) showed no regression; player-yield withdraws player-side actors so it does not trip this.
  - Severity: minor
  - Forward impact: combat/social encounters now also end-on-no-Other; this is the intended ADR-116 §4 behavior reaching those categories early (ahead of the staged guard rollout, which is a separate concern — the guard governs INSTANTIATION, this governs RESOLUTION). No consumer regression observed.
- All other TEA + Dev deviation entries reviewed: spec sources exist, quoted spec text is accurate, implementation descriptions match the code, all 6 fields present. No corrections needed.