---
story_id: "117-3"
jira_key: ""
epic: "117"
workflow: "tdd"
---
# Story 117-3: Implement deterministic quest-seed minting

## Story Details
- **ID:** 117-3
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** 117-2 (depends_on)
- **Repos:** server, content
- **Branches:** 
  - sidequest-server: feat/117-3-deterministic-quest-seed-minting (develop)
  - sidequest-content: feat/117-3-deterministic-quest-seed-minting (develop)

## Workflow Tracking
**Workflow:** tdd
**Phase:** setup
**Phase Started:** 2026-06-14T23:43:11Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-14T23:43:11Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): ADR-146 §2 describes the wire/router-context shape of `pending_quest_offers` as a list `[{quest_id, title, giver}]`, but the §flow pseudocode + Implementation pointer say `pending_quest_offers: dict[str, QuestSeed]` keyed on `quest_id` (the handler reads `snapshot.pending_quest_offers.get(params["quest_id"])`). These are two different shapes. Tests pin the **dict[str, QuestSeed]** storage shape (the handler's read contract), and assert the offer surfaces `quest_id`/`title`/`giver` (so the router-context list can be projected from it). Dev: if the persisted/wire shape must be the flat list, add a projection from the dict — don't change the handler's keyed-lookup contract the tests pin. Affects `sidequest/game/session.py` (snapshot field) + `sidequest/agents/subsystems/quest_offer.py`.
- **Question** (non-blocking): ADR-146 names the engine seam only as `run_quest_offer_dispatch` (the handler). Tests assume a thin engine module `sidequest/game/quest_offer.py` exposing `stash_quest_offers(snapshot, opening)` + `mint_quest_offer(snapshot, quest_id, *, confidence)` (mirroring `quest_seed.py::seed_quest_spine`), with the handler a thin wrapper that reads `params` and calls `mint_quest_offer`. If Dev co-locates these differently (e.g. minting inside the handler), the import paths in `tests/game/test_quest_offer_minting.py` must move with it. Affects `sidequest/game/quest_offer.py`, `sidequest/agents/subsystems/quest_offer.py`.
- **Improvement** (non-blocking): the `quest.seeded` span needs a `quest_seeded_span(...)` emitter + `SPAN_QUEST_SEEDED`/`SPAN_ROUTES` entry in `sidequest/telemetry/spans/state_patch.py` (mirroring `quest_created_span`), re-exported via the package `import *`. The span-attr test pins `source="authored_seed"`, `anchor_count`, and `confidence` (the router score that crossed the gate) per ADR-146 §4.
- **Improvement** (non-blocking): the cardinality cap (32) is currently a private `_QUEST_LOG_CARDINALITY_CAP` in `agents/tools/record_quest.py`. The `quest_offer` mint must honour the SAME cap (ADR-146 §3). Dev should promote it to a shared constant rather than duplicate the literal, so the two minting paths can't drift.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

No design deviations at setup

### Dev (implementation)
- **`pending_quest_offers` shape:** ADR-146 §2 wire-shape shows a flat list `[{quest_id, title, giver}]` for the router context, but §flow + Implementation pointer + the tests pin storage as `dict[str, QuestSeed]` keyed on `quest_id`. Implemented the dict (TEA's pinned read contract) and PROJECTED the flat list from it where the router needs it (`intent_router_pass.py` surfaces `[{quest_id, title, giver}]` into `<game_state>` from `pending_quest_offers.values()`). No divergence from the handler's keyed-lookup contract — the two ADR shapes are reconciled, dict is the source of truth, list is a projection. (Matches TEA's Delivery Finding guidance.)
- **Cardinality cap home:** ADR-146 §3 says "honour the SAME cap (32, record_quest.py:46)". Promoted the private `_QUEST_LOG_CARDINALITY_CAP` to a shared public `QUEST_LOG_CARDINALITY_CAP` on `game/session.py` (next to `QuestEntry`) and re-pointed `record_quest.py` at it via alias, so both mint paths import one constant and cannot drift. Reason: session.py is the common dependency of both mint paths and already owns `QuestEntry`; a constant on `record_quest.py` would force `quest_offer.py` to import the tool module (heavier graph). No behavioural change to record_quest.
- **`mint_quest_offer` cap-check ordering:** the cap check fires BEFORE the idempotent-`quest_id`-present check is NOT reordered — idempotency is checked first (a re-accept of an already-minted quest no-ops even at the cap, since it adds nothing), then the unknown-offer guard, then the cap (raises before consuming the offer). The cap test fills 32 UNRELATED quests so the floor-boss id is absent → idempotency passes through → cap raises → offer not consumed, exactly as the test pins.
- **Witness count guard updated (not gamed):** `tests/agents/test_59_30_witnesses.py::test_witnesses_count_is_eight...` asserted exactly 8 `_WITNESSES`. ADR-146 §4 MANDATES a 9th (`quest_offer`) witness as one of the three required wiring connections (no half-wiring, CLAUDE.md). Renamed the test to `...is_nine...`, bumped the assertion to 9, and corrected the watcher's own docstring ("eight"→"nine"). This is a real, spec-required connection, not a count-fudge.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Story implements new typed schema + state + router subsystem + minting engine + OTEL span — all behavior, all testable with synthetic fixtures.

**Test Files:**
- `sidequest-server/tests/genre/models/test_quest_seed_model.py` — the `QuestSeed` schema: required fields, defaults, `extra="forbid"` typo rejection, `OpeningTone.quest_seed` typed field + nested-typo propagation.
- `sidequest-server/tests/game/test_quest_offer_minting.py` — the engine seam: stash-from-opening, resume-safe round-trip, accept-mints, fill-don't-clobber stakes, `quest.seeded` span attrs, idempotency (re-accept + narrator front-ran), cardinality-cap fail-loud.
- `sidequest-server/tests/agents/subsystems/test_quest_offer_dispatch_wiring.py` — wiring: `_REGISTRY` registration, **the mandatory end-to-end wiring test** (opening-with-seed → accept through real `run_dispatch_bank` → `quest_log` non-empty → QUESTS projection `quests>=1`), decline-no-mint, low-confidence-gate degrade, unknown-offer no-phantom-mint, engagement `_WITNESSES` registration + mismatch detection + honest-engagement silence.

**Tests Written:** 26 tests across 3 files covering ACs (a)–(g). Router LLM classification is STUBBED — the `quest_offer` `SubsystemDispatch` is injected directly (no LLM runs); all fixtures synthetic (no perseus_cloud / real content).
**Status:** RED — all three files fail at collection on feature-absence imports (`QuestSeed`, `sidequest.game.quest_offer`); confirmed no avoidable/typo import errors (every pre-existing symbol resolves, synthetic `Opening` fixture builds today minus the seed).
**Wiring test present:** Yes — `test_end_to_end_accept_through_bank_mints_and_projects` (drives the real dispatch bank, asserts QUESTS projection quests>=1) + `test_quest_offer_handler_is_registered` + `test_quest_offer_witness_registered`.

**Handoff:** To Dev for implementation (GREEN).

## Implementation Notes

**Story Summary:** Implement deterministic quest-seed minting per ADR-146. An authored opening/seed_trope quest_seed mints a QuestEntry into quest_log on acceptance, emitting quest.created/quest.seeded spans, so QUESTS projects to QuestsPanel without depending on the narrator calling record_quest.

**Scope:** Touches TWO subrepos:
- sidequest-server: Python code implementation (QuestSeed model, quest_offer router subsystem, handler, OTEL span, witness)
- sidequest-content: Perseus_cloud openings.yaml quest_seed authoring (exemplar: floor-boss detective hook)

**Key Requirements (ADR-146):**
1. QuestSeed pydantic sub-model on Opening.tone and seed_trope (schema: quest_id, title, objective, stakes, anchor, giver)
2. quest_offer router subsystem that detects player acceptance and mints QuestEntry deterministically
3. pending_quest_offers state on GameSnapshot (persisted, resume-safe)
4. quest.seeded OTEL span routed through SPAN_ROUTES
5. engagement-watcher witness for quest_offer mismatch detection
6. Perseus_cloud floor-boss detective hook as first quest_seed exemplar

**Test Plan (Wiring Test):**
- Scripted opening → player accepts → quest_log non-empty → quests.emitted quests>=1

**Next Agent:** TEA (red phase) — write failing tests for quest_seed acceptance and minting path

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (sidequest-server):**
- `sidequest/genre/models/narrative.py` — new `QuestSeed` sub-model (extra="forbid") + typed `OpeningTone.quest_seed: QuestSeed | None`
- `sidequest/genre/models/__init__.py` — re-export `QuestSeed`
- `sidequest/game/session.py` — `pending_quest_offers: dict[str, QuestSeed]` on GameSnapshot (resume-safe) + promoted `QUEST_LOG_CARDINALITY_CAP` shared constant
- `sidequest/game/quest_offer.py` — NEW engine seam: `stash_quest_offers` + `mint_quest_offer` (fill-don't-clobber, idempotent, cap-fail-loud, fires `quest.seeded`)
- `sidequest/agents/subsystems/quest_offer.py` — NEW thin handler `run_quest_offer_dispatch` (accept→mint, decline→consume, unknown→mismatch)
- `sidequest/agents/subsystems/__init__.py` — registered `quest_offer` → `run_quest_offer_dispatch` in `_REGISTRY`
- `sidequest/agents/dispatch_engagement_watcher.py` — `quest_offer` witness in `_WITNESSES` + `_DISPATCHED_TYPE_KEY` + corrected count docstring
- `sidequest/agents/tools/record_quest.py` — re-pointed cap at shared constant
- `sidequest/agents/intent_router.py` — `quest_offer` subsystem prompt block
- `sidequest/server/intent_router_pass.py` — surface `pending_quest_offers` into router `<game_state>`
- `sidequest/server/websocket_handlers/opening_helpers.py` — `stash_quest_offers` call at chargen-complete
- `sidequest/telemetry/spans/state_patch.py` — `SPAN_QUEST_SEEDED` + SPAN_ROUTES entry + `quest_seeded_span` emitter
- `sidequest/cli/validate/pack.py` — perseus_cloud quest_seed content-existence invariant (validator, not pytest)
- `tests/agents/test_59_30_witnesses.py` — count guard 8→9 (ADR-146-mandated 9th witness)

**Files Changed (sidequest-content):**
- `genre_packs/space_opera/worlds/perseus_cloud/openings.yaml` — floor-boss detective `quest_seed` on `solo_new_kowloon_arrival`

**Three wiring connections (ADR-146, no half-wiring):** (1) router prompt block + state surfacing, (2) registered handler `quest_offer`→`run_quest_offer_dispatch`, (3) `quest_offer` engagement witness. All three landed.

**Tests:** 29/29 GREEN in the 117-3 suite (`-n0`). No new regressions; 8 pre-existing WWN/content-drift failures unchanged (verified on clean tree).
**Validator:** space_opera PASS (0 errors); perseus_cloud quest_seed invariant enforced (fails loud when seed absent — verified).
**Branch:** feat/117-3-deterministic-quest-seed-minting (both repos, base develop)

**Handoff:** To review.
