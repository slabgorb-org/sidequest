---
story_id: "158-43"
jira_key: ""
epic: "158"
workflow: "tdd"
---
# Story 158-43: Authored quest offer never mints into quest_log — anchor-crossing acceptance for self-directed seeds

## Story Details
- **ID:** 158-43
- **Jira Key:** (none — sprint YAML tracked)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-07-02T13:18:57Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-02T07:52:00Z | 2026-07-02T12:34:25Z | 4h 42m |
| red | 2026-07-02T12:34:25Z | 2026-07-02T12:52:48Z | 18m 23s |
| green | 2026-07-02T12:52:48Z | 2026-07-02T13:10:16Z | 17m 28s |
| review | 2026-07-02T13:10:16Z | 2026-07-02T13:18:57Z | 8m 41s |
| finish | 2026-07-02T13:18:57Z | - | - |

## Technical Approach (Approved — Keith 2026-07-02)

### Problem Statement (Corrected)

ADR-146 (landed 2026-06-14) built the deterministic authored-offer mint pipeline: `stash_quest_offers` → Intent Router classifies accept/decline → `mint_quest_offer` mints a QuestEntry with NO narrator tool call, firing a `quest.seeded` span. The original "narrator must call record_quest and doesn't" framing is obsolete.

**The REAL bug:** ADR-146's Intent Router `quest_offer` prompt is written for GIVER-HOOK offers ("yeah, I'll take the job"). It does not cover SELF-DIRECTED / giver-less seeds (`giver: ""`) like beneath_sunden's `the_unspent_hold`, whose world-author comment says "acceptance is the descent, not a yes to anyone." The player descends the Dropmouth; the router classifies the turn as `movement`; nothing tells the engine that undertaking the objective is acceptance; the offer sits in `pending_quest_offers` forever and never reaches `quest_log`.

### Approved Design: Anchor-Crossing Deterministic Backstop

Amend **ADR-146** (NOT ADR-117) with the anchor-crossing deterministic mint trigger:

- When a seated PC TRANSITIONS INTO the seed's `anchor` region, the engine mints the offer via the existing idempotent `mint_quest_offer` with `source="anchor_crossed"`, `confidence=1.0`. No LLM in the loop for the failing case. The router's verbal-acceptance path is retained unchanged; first-writer-wins reconciles the two (as it already does against narrator `record_quest`).
- **Trigger scope:** ANY anchor-bearing seed — giver-less AND giver-hook offers that carry an anchor mint on crossing.
- **Router extension:** DEFERRED. Deterministic anchor path ONLY for this story — do not extend the Intent Router prompt. The failing case is fully covered by the deterministic path; keeps token cost flat.
- **Decline edge:** RESPECT THE DECLINE. A consumed/declined offer stays gone; anchor-crossing does NOT resurrect it.
- **First-placement exclusion:** spawning INTO the anchor region at turn 0 must NOT mint — acceptance requires a genuine region *transition* (from_region truthy), not first placement.

### Hook Points

- `sidequest-server/sidequest/game/quest_offer.py` — new `mint_on_anchor_crossing(snapshot, *, pc_name, from_region, to_region)`: scan `pending_quest_offers` for a seed whose `anchor == to_region`; if found, `from_region` truthy, and offer not already declined/consumed, call existing `mint_quest_offer` with `source="anchor_crossed"`.
- `sidequest-server/sidequest/game/session.py` — call it from the `pc_region` genuine-change block in `_apply_world_patch_inner`, adjacent to the existing `notify_region_transition` call, so ALL transition paths (movement dispatch, seam descent via `game/seams/deep_descent.py`, procedural relocation) are covered.
- `sidequest-server/sidequest/telemetry/spans/state_patch.py` (~line 280) — extend `quest_seeded_span` `source` vocabulary to include `anchor_crossed` (with `confidence=1.0`). OTEL principle: the GM panel must distinguish "Haiku classified a yes" (`router_accept`) from "engine watched the crossing" (`anchor_crossed`).

## Acceptance Criteria

1. A seated PC transitioning INTO a seed's `anchor` region mints the authored offer into `quest_log` with no narrator/LLM call, and the player sees the quest.
2. The `quest.seeded` OTEL span fires with `source="anchor_crossed"`, `confidence=1.0` on the anchor-mint path (GM-panel observable).
3. Spawning/first-placement into the anchor region (from_region empty) does NOT mint.
4. A previously declined/consumed offer is NOT resurrected by anchor-crossing.
5. First-writer-wins: if the router verbal path or narrator `record_quest` already minted, the anchor path does not double-mint.
6. Regression guard: existing giver-hook verbal-acceptance router path still mints as before (ADR-146 behavior unchanged).

## ADR Work

The story includes drafting the **ADR-146 amendment** ("Anchor-Crossing Acceptance — a Deterministic Second Mint Trigger"). The amendment must state plainly that ADR-146 originally covered only giver-hook offers and did not cover self-directed / giver-less seeds — this is closing that gap, not a redesign.

## Sm Assessment

Setup complete and gate-ready. Design call was routed to the Architect and **approved by Keith 2026-07-02** — anchor-crossing deterministic backstop amending ADR-146 (all four shaping forks locked: any-anchor-bearing scope, deterministic-path-only, respect-the-decline, transition-only exclusion). The story's original premise ("narrator must call record_quest") is stale; the corrected problem statement and approved technical approach are captured above, so TEA inherits a complete spec, not a guess.

**Routing:** phased `tdd` → **TEA (RED phase)**. Write failing tests covering all six ACs before handing to Dev. Note AC-2 (the `quest.seeded` span with `source="anchor_crossed"`, `confidence=1.0`) is the OTEL lie-detector requirement — the mint decision must be GM-panel observable, so the RED suite must assert the span, not just the quest_log entry. Story also carries the ADR-146 amendment as a deliverable.

Keith flagged (legitimately) that this patches something ADR-146 was meant to complete — the amendment must say plainly that 146 covered only giver-hook offers and never self-directed / giver-less seeds. Not a redesign; a gap closure.

## TEA Assessment

**Tests Required:** Yes
**Reason:** n/a (bug fix with six behavioral ACs and an OTEL lie-detector requirement)

**Test Files:**
- `sidequest-server/tests/game/test_anchor_crossing_mint.py` — full RED suite: `mint_on_anchor_crossing` unit contract, `apply_world_patch(pc_region=...)` choke-point wiring, `quest.seeded` `source="anchor_crossed"` span, exclusions (first-placement, decline, first-writer-wins, cap), real beneath_sunden `the_unspent_hold` playtest case, AC-6 router regression guard.

**Tests Written:** 20 tests covering 6 ACs (12 unit, 6 wiring, 1 real-content e2e, 1 AC-6 regression)
**Status:** RED (verified by testing-runner, RUN_ID `158-43-tea-red`: the module fails collection with `ImportError: cannot import name 'mint_on_anchor_crossing'` — the intended RED; rest of suite 3,872 passed / 0 failed / 17 skipped, zero collateral). Committed `d3c80786` on `feat/158-43-authored-quest-anchor-mint`.

**Contract defined for Dev (Naomi):**
- `sidequest/game/quest_offer.py` — `mint_on_anchor_crossing(snapshot, *, pc_name, from_region, to_region)` (keyword-only); scans `pending_quest_offers` for `anchor == to_region`; mints via existing `mint_quest_offer` only when `from_region` truthy; must not match `anchor="" == to_region=""`.
- `sidequest/game/session.py` — call it inside the `pc_region` genuine-change block (beside `notify_region_transition`); the `current_region` spawn-anchor branch must NOT mint.
- Span: `quest.seeded` with `source="anchor_crossed"`, `confidence=1.0`; the router path's span must stay `source="authored_seed"` with the router's confidence (AC-6 pinned).
- Cap overflow must stay loud and never consume the offer.

### Rule Coverage

| Rule (lang-review/python.md) | Test(s) | Status |
|------|---------|--------|
| #1 silent exceptions / fail loud | `test_cap_overflow_fails_loud_and_offer_survives`, `test_first_placement_does_not_mint` (no silent consume) | failing (RED) |
| #6 test quality (no vacuous asserts) | all 20 assert specific values (span attrs, titles, exact counts); falsy-input pair folded into one test to avoid a same-path parametrize | self-checked |
| #9 async pitfalls | `test_declined_offer_is_not_resurrected_by_crossing` awaits the real async dispatch handler (asyncio_mode=auto) | failing (RED) |
| #11 input validation at boundaries | `test_empty_to_region_never_matches_empty_anchor` (garbage-input guard on the seam) | failing (RED) |
| Every-suite-needs-a-wiring-test (CLAUDE.md) | 6 `apply_world_patch` choke-point tests + real-content `test_beneath_sunden_unspent_hold_descent_mints` | failing (RED) |

**Rules checked:** 4 of 13 lang-review rules applicable to test design have coverage; the rest (#2/#3/#4/#5/#7/#8/#10/#12/#13) apply to Dev's implementation and fall to the review gate.
**Self-check:** 0 vacuous tests found.

**Handoff:** To Dev (Naomi Nagata) for GREEN — implement `mint_on_anchor_crossing` + session wiring + span vocabulary per the contract above. Story also carries the ADR-146 amendment as a deliverable (not TEA scope).

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/sidequest/game/quest_offer.py` — `mint_quest_offer` gains `source` (default `"authored_seed"` — AC-6 preserved) and `pc_name` span-attr params; new `mint_on_anchor_crossing(snapshot, *, pc_name, from_region, to_region)` scans `pending_quest_offers` for `anchor == to_region`, requires truthy `from_region`/`to_region`, mints ALL matching seeds via the idempotent `mint_quest_offer` with `source="anchor_crossed"`, `confidence=1.0`.
- `sidequest-server/sidequest/game/session.py` — call wired inside the `pc_region` genuine-change block beside `notify_region_transition` (lazy import, same pattern as the frontier hook). The `current_region` spawn-anchor branch deliberately does not call it.
- `sidequest-server/sidequest/telemetry/spans/state_patch.py` — `quest_seeded_span` docstring documents the `anchor_crossed` source + `pc_name` attr. `SPAN_ROUTES` extraction verified source-agnostic — the GM panel gets the new source with zero new plumbing.
- `docs/adr/146-quest-seed-authoring-contract.md` (orchestrator) — Story 158-43 addendum drafted per story deliverable: giver-hook-only gap stated plainly, all four approved forks, mint-all-matching rule, span vocabulary, region-mode Site B known limitation. Indexes regenerated; committed `9a7aade7` on orchestrator main (local; push rides SM finish).

**Tests:** 20/20 story tests passing (GREEN, testing-runner RUN_ID `158-43-dev-green`). Full suite: 14,484 passed / 14 failed — ALL 14 verified pre-existing by re-running the failing subset with the implementation stashed (RUN_ID `158-43-preexist-check`): 9 genuine pre-existing (6 caverns_and_claudes bestiary/encounter-seed, 1 creature image specs, 2 AWN mutation spans) + 5 xdist pool-lifecycle flakes that pass in any smaller batch. Zero failures introduced by this story. Lint/format/pyright clean (2 session.py pyright errors pre-date the change, verified by stash).

**Branch:** `feat/158-43-authored-quest-anchor-mint` (pushed, `c6095ff9`)

**Answers to TEA's open Questions:** (1) same-anchor multi-seed → mint ALL matching (stated in the ADR addendum; rationale: first-match would re-create the stuck-offer bug for the second seed). (2) cap overflow → loud propagation kept, offer never consumed (No Silent Fallbacks; also in the addendum).

**Handoff:** To Reviewer (Chrisjen Avasarala) for code review. DO NOT create a PR — SM owns that in finish.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — domain self-assessed by Reviewer (see assessment) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — domain self-assessed by Reviewer |
| 4 | reviewer-test-analyzer | Yes | findings | 5 | confirmed 5 (2 medium, 3 low), dismissed 0, deferred 0 |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 | confirmed 3 (1 medium, 2 low), dismissed 0, deferred 0 |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — domain self-assessed by Reviewer |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings — domain self-assessed by Reviewer |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — domain self-assessed by Reviewer |
| 9 | reviewer-rule-checker | Yes | clean | none (19 rules × 46 instances, 0 violations) | N/A |

**All received:** Yes (4 enabled returned; 5 disabled pre-filled)
**Total findings:** 8 confirmed, 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

No Critical or High findings. Eight confirmed non-blocking findings (3 medium, 5 low) — all coverage-debt or documentation; none change runtime behavior, none violate a project rule (rule-checker: 0 violations across 19 rules / 46 instances). Captured below and as Delivery Findings for fast-follow.

### Confirmed Findings (non-blocking)

| Severity | Tag | Issue | Location |
|----------|-----|-------|----------|
| [MEDIUM] | [TEST] | Same-anchor multi-seed mint-ALL behavior (Dev's documented deviation, stated in the ADR-146 addendum) is pinned by NO test — a `matching[:1]`/early-`break` regression would silently re-create the exact stuck-offer bug this story fixes. `test_only_the_matching_anchor_offer_mints` uses two DIFFERENT anchors only. | tests/game/test_anchor_crossing_mint.py:260 |
| [MEDIUM] | [TEST] | New `pc_name` span attribute is asserted by NO test — neither `== "Rux"` on the anchor path nor empty on the router path. A dropped/mislabeled attr is invisible to the suite despite being the story's own observability addition. | tests/game/test_anchor_crossing_mint.py:172, :512 |
| [MEDIUM] | [DOC] | quest_offer.py module docstring still describes the router classification as the ONLY mint trigger; `mint_on_anchor_crossing` (exported in `__all__`) is unmentioned at the module front door. | sidequest/game/quest_offer.py:1 |
| [LOW] | [DOC] | `mint_quest_offer` docstring does not document the new `source`/`pc_name` params (only an inline comment near the span call does). | sidequest/game/quest_offer.py:54 |
| [LOW] | [DOC] | session.py comment "spawning into the anchor at turn 0" under-describes the excluded `current_region` branch, which also covers GM teleport and narrator-issued region patches mid-game. | sidequest/game/session.py:1598 |
| [LOW] | [TEST] | `mint_on_anchor_crossing(from_region=X, to_region=X)` (truthy, equal) behavior is unpinned at the unit seam — production is protected only by the caller's `to_region != prev` gate. | tests/game/test_anchor_crossing_mint.py:195 |
| [LOW] | [TEST] | `pytest.raises(Exception)` in the cap test would pass on ANY exception; the implementation raises `ValueError("quest_log cardinality cap...")` — tighten to `pytest.raises(ValueError, match="cardinality cap")`. (TEA wrote it pre-implementation when the type was undecided; the decision has since been made.) | tests/game/test_anchor_crossing_mint.py:348 |
| [LOW] | [EDGE] | `pc_name` is seat-agnostic — no check against `player_seats`. Acceptable today: every producer of `WorldStatePatch.pc_region` (movement.py, deep_descent.py, surface_ascent.py) derives keys from seated PCs, and the field's documented contract is per-PC; same exposure class as the adjacent `notify_region_transition`. | sidequest/game/quest_offer.py:141 |

### Self-Assessed Domains (disabled specialists)

- [EDGE] **Cap raise mid-batch:** with two matching seeds, a cap `ValueError` on the first propagates out of `apply_world_patch` with `pc_regions` already mutated (partial patch apply). Same loud posture as the pre-existing `record_quest` cap; documented in the ADR addendum; TEA's cap test pins offer-survival. Accepted design, not a defect.
- [EDGE] **Mutation-during-iteration:** `matching` list is materialized BEFORE the mint loop (quest_offer.py:174-178), so `mint_quest_offer`'s pop cannot invalidate iteration. Verified safe.
- [SILENT] No swallowed errors introduced: every no-mint path is a specified, tested exclusion (first-placement, no-match, declined, idempotent); the only failure path raises. Verified clean.
- [TYPE] `source: str` (not `Literal`) matches the existing `quest_seeded_span` API and stringly `SPAN_ROUTES` extraction — consistent, not a regression. Keyword-only params enforced on both functions. Verified acceptable.
- [SEC] No new input boundary: `pc_region` values arrive via the validated `WorldStatePatch` pydantic model from internal dispatch; anchor matching is equality on authored content strings; no injection surface, no secrets, no per-player perception change (quest_log is shared-world state; the ADR-104/105 firewall applies downstream, unchanged). No tenant concept in this codebase — the analogous per-player-visibility audit found no change to visibility surfaces. Verified clean.
- [SIMPLE] Implementation is minimal (guard + comprehension + loop over the existing idempotent mint); no dead code, no speculative abstraction. Verified clean.
- [LOW] [SIMPLE] Observation (own): the `SPAN_ROUTES` extract for `quest.seeded` (state_patch.py:113-121) does not pull `pc_name` into the routed GM-panel event — the raw span carries it, the routed feed drops it. One-line extract addition if the panel should show whose crossing minted. Paired with the [TEST] pc_name finding above.

### Rule Compliance

Rule-checker ran all 13 python.md checks plus 6 CLAUDE.md/SOUL.md rules against every changed function/file: **0 violations across 46 instances** ([RULE] clean). Spot-confirmed myself: No Silent Fallbacks (falsy-guard early returns are documented, tested business exclusions, not fallbacks; cap raises loud BEFORE consuming — quest_offer.py:97-102), Verify Wiring (production consumer at session.py:1601 inside `_apply_world_patch_inner`; wiring tests drive the real `apply_world_patch` entry), OTEL Observability (`quest.seeded` with `source="anchor_crossed"`, `confidence=1.0` — GM panel distinguishes engine-watch from router classify; asserted by tests), No Source-Text Wiring Tests (all wiring tests are fixture-driven behavior tests), Cost Scales with Drama (zero LLM in the deterministic path).

### Verification Trace

- **Data flow traced:** authored `anchor: the_dropmouth` (openings.yaml, `extra="forbid"` typed load) → `stash_quest_offers` → `pending_quest_offers` → player movement → movement/seam dispatch → `apply_world_patch(pc_region={pc: region})` → genuine-change gate (`to_region and to_region != prev`, session.py:1572) → `mint_on_anchor_crossing` equality scan → idempotent `mint_quest_offer` → `quest_log`/`quest_anchors`/span → existing QUESTS projection → player's Quests tab. Safe because: no LLM anywhere; the player cannot forge a region transition (movement is engine-validated); the mint is idempotent and cap-bounded.
- **Wiring:** [VERIFIED] `mint_on_anchor_crossing` has exactly one production consumer — session.py:1601 in the `pc_region` genuine-change block — and `deep_descent.py:54` routes the playtest-failing seam descent through that same block via `apply_world_patch(WorldStatePatch(pc_region=...))`. Complies with Verify Wiring + Every-Suite-Needs-a-Wiring-Test (6 choke-point tests + real-content e2e).
- **Pattern observed (good):** lazy import with dependency-inversion rationale extends the identical adjacent `frontier_hook` pattern — session.py:1564-1567.
- **Error handling:** [VERIFIED] falsy `from_region`/`to_region` guard at quest_offer.py:172-173 (tested with "", None, and the `anchor=""` garbage-input case); cap overflow raises `ValueError` before consuming the offer (quest_offer.py:97-102, test pins offer survival). Complies with No Silent Fallbacks.
- **Hard questions:** empty inputs guarded + tested; huge inputs n/a (scan is O(pending offers), capped in practice by authoring); race conditions n/a (per-session serialization via session row locks; single-threaded patch apply); resume safety verified (no new state; no transition fires on resume, so no spurious mint); walk-out-walk-back-in mints once (recross test pins single span).
- **Challenged VERIFIEDs vs subagents:** test-analyzer's same-anchor and pc_name findings contradict no VERIFIED above (both are coverage gaps, not behavior defects — mint-all IS implemented at quest_offer.py:174-190, confirmed by direct read). No contradictions with rule-checker (clean) or preflight (clean).

### Devil's Advocate

Assume this is broken. The sharpest attack: **the narrator escape hatch**. `agents/tools/apply_world_patch.py` lets the narrator emit `pc_region` patches — so a hallucinated relocation into the Dropmouth would fire a mint labeled `anchor_crossed, confidence=1.0`, dressing narrator improvisation in engine-certainty clothing. But the mint follows *canonical state*: if the narrator moved the PC there, the PC genuinely is there and acceptance-by-descent is the authored semantics; the span honestly reports that the engine watched a real state transition. The lie-detector chain still works — a bogus relocation is the narrator's lie, visible in the state-patch spans, not this seam's. Next attack: **the player who declines and then sightsees**. Decline pops the offer; the walk to the Dropmouth mints nothing — respected. But the inverse bites a real player: decline verbally, later genuinely choose the descent — the offer is gone forever. That is pre-existing ADR-146 decline semantics, unchanged here, and it is at least arguable the author intended decline-then-descend to still count as the descent. Worth a designer's eye someday; not this diff's defect. Next: **author anchors a seed at the spawn region** — spawn never mints (tested), so the quest is only reachable by leaving and returning, which may surprise a world author; the ADR addendum documents transition-only, but no content validator warns about anchor==spawn-region. Next: **region renames** — an authored `anchor` that matches no real region id mints never and rots silently in `pending_quest_offers`; nothing validates anchors against the region graph at load. Both content-validation gaps predate this story (anchors already flowed into `quest_anchors` unvalidated) — captured as a Delivery Finding rather than a code defect. Finally, **the same-anchor regression trap**: the one place where this diff's own tests would not catch a behavioral break. That is my strongest finding, and it stands as [MEDIUM].

**Observations count:** 8 confirmed findings + 6 verified-good = 14 (≥5 satisfied).

**Handoff:** To Camina Drummer (SM) for finish-story. Recommend a fast-follow chore for the two [MEDIUM][TEST] gaps + three [DOC] fixes — 30 minutes of work, none blocking.

No upstream findings.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): Region-mode worlds (oz/wonderland/gulliver-style cartography) relocate PCs via the `narration_apply` region-mode block, NOT `apply_world_patch(pc_region=...)` — Story 59-30's movement-witness contract calls this Site B and states region-mode moves apply no patch by design. An anchor-bearing seed in a region-mode world will never mint on crossing under the approved hook placement.
  Affects `sidequest-server/sidequest/server/narration_apply.py` (would need the same mint hook if any region-mode world ever authors an anchored seed; beneath_sunden is dungeon-graph so this story's failing case is unaffected).
  *Found by TEA during test design.*
- **Question** (non-blocking): Two pending seeds sharing the SAME anchor region — the approved design is singular ("a seed whose anchor == to_region"); mint-all vs mint-first is unspecified. Tests pin only the distinct-anchor case.
  Affects `sidequest-server/sidequest/game/quest_offer.py` (Dev should pick a rule and the ADR-146 amendment should state it).
  *Found by TEA during test design.*
- **Question** (non-blocking): Cardinality-cap overflow on the anchor path propagates out of `apply_world_patch` mid-movement-turn (fail-loud per doctrine; pinned by `test_cap_overflow_fails_loud_and_offer_survives` at the unit seam). Confirm loud propagation through the world-patch apply is acceptable, or whether the session hook should pre-check the cap.
  Affects `sidequest-server/sidequest/game/session.py` (`pc_region` block error posture).
  *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): 7 pre-existing content failures in the full server suite — 6× caverns_and_claudes chargen encounter seeding (`EncounterSeedError`: bestiary.yaml missing/misconfigured for the WWN ruleset) + 1× creature image specs (40+ beneath_sunden creatures unrenderable).
  Affects `sidequest-content/genre_packs/caverns_and_claudes` (bestiary.yaml + creature image specs).
  *Found by Dev during implementation.*
- **Gap** (non-blocking): 2 pre-existing server failures — AWN mutation beats not emitting `awn.mutation.used` spans (`test_102_7_mutant_wasteland_mutations_live.py`, `test_103_10_seaboard_e2e.py`). OTEL lie-detector blind spot on the mutation path.
  Affects `sidequest-server/sidequest/mutation` (span emission on the mutation-use dispatch path).
  *Found by Dev during implementation.*
- **Improvement** (non-blocking): 5 tests fail only in the full ~14.8k-test 28-worker xdist run with `psycopg_pool.PoolClosed` (pass in any smaller batch, parallel or serial) — test-isolation pool-lifecycle artifact, verified unrelated to this story by re-running the subset without the change (RUN_ID `158-43-preexist-check`).
  Affects `sidequest-server/tests` (DB pool fixture lifecycle under high xdist concurrency).
  *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): Fast-follow chore bundling the 8 confirmed review findings — same-anchor mint-ALL regression test, `pc_name` span-attr assertions (+ optionally the `SPAN_ROUTES` extract), quest_offer.py module docstring second-trigger mention, `mint_quest_offer` param docs, session.py comment scope wording, `pytest.raises(ValueError, match="cardinality cap")` tightening, `from_region == to_region` unit pin.
  Affects `sidequest-server/tests/game/test_anchor_crossing_mint.py` and `sidequest-server/sidequest/game/quest_offer.py` (~30 minutes, none blocking).
  *Found by Reviewer during code review.*
- **Gap** (non-blocking): No content-load validation that a `quest_seed.anchor` names a real region — a typo'd anchor mints never and the offer rots silently in `pending_quest_offers` (predates this story; anchors already flowed into `quest_anchors` unvalidated). A pack validator warning (anchor not in region graph / anchor == opening spawn region, which can never mint on spawn) would catch both authoring traps.
  Affects `sidequest-content` pack validator / `sidequest-server/sidequest/genre` loader (validator severity model, ADR-126 pattern).
  *Found by Reviewer during code review.*
- **Question** (non-blocking): Decline-then-descend — a verbally declined offer is consumed forever, so a player who later genuinely performs the descent mints nothing. Arguably "acceptance is the descent" survives a verbal decline for self-directed seeds. Pre-existing ADR-146 decline semantics, unchanged by this story; designer call for Keith.
  Affects `sidequest-server/sidequest/agents/subsystems/quest_offer.py` (decline consume-vs-tombstone semantics).
  *Found by Reviewer during code review.*

## Design Deviations

None yet.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Choke-point wiring tests instead of per-producer transition-path tests**
  - Spec source: context-story-158-43.md, Testing Strategy → Integration Tests
  - Spec text: "Test all transition paths: movement dispatch, seam descent, procedural relocation"
  - Implementation: Wiring tests drive `GameSnapshot.apply_world_patch(WorldStatePatch(pc_region=...))` directly — the genuine-change block all three producers route through (verified: `deep_descent.py:54` applies `WorldStatePatch(pc_region=...)`; session.py's own block comment covers both procedural relocation paths) — rather than driving each producer end-to-end
  - Rationale: The hook lands at the shared choke point; driving each producer would re-test plumbing already covered by their own suites (e.g. `test_59_30_region_transition_stamp.py`), not the new seam
  - Severity: minor
  - Forward impact: A transition path that bypasses `apply_world_patch(pc_region=...)` (region-mode `narration_apply` — see Delivery Findings) is invisible to these tests and to the hook itself
- **AC-1 "player sees the quest in the Quests tab" asserted at quest_log truth**
  - Spec source: context-story-158-43.md, AC-1
  - Spec text: "mints the authored offer into quest_log ... player sees the quest in the Quests tab"
  - Implementation: Tests assert the `quest_log` entry (server truth); Quests-tab visibility is not re-asserted
  - Rationale: The tab rides the existing quest_log→QUESTS projection already covered by `tests/server/test_quests_emit*.py`; the mint writes the same substrate every other mint path writes
  - Severity: minor
  - Forward impact: none

### Dev (implementation)
- **Mint ALL same-anchor matching seeds, not first-match**
  - Spec source: .session/158-43-session.md, Hook Points (approved design)
  - Spec text: "scan `pending_quest_offers` for a seed whose `anchor == to_region`; if found ... call existing `mint_quest_offer`" (singular)
  - Implementation: `mint_on_anchor_crossing` mints EVERY pending seed whose anchor matches `to_region`, not just the first
  - Rationale: Two seeds anchored on the same region are both accepted by the crossing; first-match would leave the second seed in exactly the stuck-offer state this story fixes. Resolves TEA's open Question; the rule is stated in the ADR-146 addendum
  - Severity: minor
  - Forward impact: none — each mint flows through the idempotent `mint_quest_offer`; single-match behavior is identical
- No other deviations from spec.

### Reviewer (audit)
- **TEA: Choke-point wiring tests instead of per-producer transition-path tests** → ✓ ACCEPTED by Reviewer: verified `deep_descent.py:54` routes through `apply_world_patch(pc_region=...)` and the session block comment confirms both procedural relocation paths do too; per-producer plumbing has its own suites. Sound.
- **TEA: AC-1 "Quests tab" asserted at quest_log truth** → ✓ ACCEPTED by Reviewer: the QUESTS projection reads `quest_log` and is covered by `tests/server/test_quests_emit*.py`; re-asserting it here would duplicate coverage.
- **Dev: Mint ALL same-anchor matching seeds** → ✓ ACCEPTED by Reviewer: agrees with author reasoning and the rule is stated in the ADR-146 addendum — WITH the caveat that this exact behavior is pinned by no test (confirmed [MEDIUM][TEST] finding; fast-follow).
- **Undocumented (spotted by Reviewer): router-path `quest.seeded` spans now carry a `pc_name=""` attribute.** Spec said extend the `source` vocabulary; the implementation also passes `pc_name` unconditionally into `quest_seeded_span`, so the pre-existing router path's span shape gains an empty attr. Benign — the `SPAN_ROUTES` extract ignores it and no consumer reads it — but it is a span-shape change Dev did not log. Severity: Low. → ✓ ACCEPTED by Reviewer (honest "not plumbed" signal; documented in the span docstring).