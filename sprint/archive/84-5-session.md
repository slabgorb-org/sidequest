---
story_id: "84-5"
jira_key: ""
epic: "84"
workflow: "tdd"
---

# Story 84-5: WI-2 Lifecycle-aware scope

**Title:** WI-2 Lifecycle-aware scope — dormant quest/trope indexing + active→floor routing; per-type active/dormant predicate (amends ADR-118 §D2; quest source = epic 77, trope = ADR-128)

**Points:** 5
**Epic:** 84 (ADR-118 Amendment — Unified Pertinence Scorer & Tiered Forgetting)
**Workflow:** tdd
**Repository:** sidequest-server
**Branch:** feat/84-5-lifecycle-aware-scope

## Story Details

This is the 5th story in the Epic 84 peloton (final planned). Prior stories landed on develop:
- 84-1 (WI-1): Unified pertinence scorer + present-scene invariant + drama-gated embed
- 84-4 (WI-6): OTEL per-card reason decomposition + retrieval.universal span attributes
- 84-2 (WI-5): Alias resolution + Npc.aliases accretion-fed mention matching
- 84-3 (WI-4): Relationship card projector + EntityType.RELATIONSHIP floor-companion

**Technical Goal:**
Implement the lifecycle-aware index scope amendment to ADR-118 (§A2). The amendment distinguishes ACTIVE entities (quests/tropes under tension, apply whether named or not) from DORMANT ones (notes, indexed for lookup by relevance). Each entity type declares an **active/dormant predicate** so they route correctly:

- **Active quests/tropes** → FLOOR (hard invariant: always included, never budgeted out)
- **Dormant quests/tropes** → INDEX (retrieved by pertinence like other entities)
- **Relationships** → INDEX (always index-side, never floor)
- **NPCs/Locations/Factions** → INDEX (unchanged from prior stories)

## Workflow Tracking

**Workflow:** tdd
**Phase:** red
**Phase Started:** 2026-06-05 09:24:08 UTC

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| red | 2026-06-05 09:24:08 UTC | - | - |

## Dependency Assessment

### CRITICAL FINDINGS

**1. QUEST SUBSTRATE (epic 77, ADR-137) — NOT BLOCKED**

✓ **EXISTS AND LIVE:** Quest substrate is fully implemented and merged to develop.
- `QuestEntry` model exists with `status: str = "active"` field (session.py)
- `quest_log: dict[str, QuestEntry]` is on `GameSnapshot`
- Tools: `record_quest` and `set_stakes` (ADR-102 tool-use, 77-2) are shipped
- Narrator can create/update quests directly
- Quests have an active/dormant predicate via the `status` field

**Decision:** Quest substrate is ready for indexing. The predicate is simple: `status != "completed"` = active, `status == "completed"` = dormant. (Note: current code uses string statuses like "active", "completed", "dormant" — exact enum values must be verified during implementation.)

---

**2. TROPE SUBSTRATE (ADR-128, epic 22/45-27) — NOT BLOCKED**

✓ **EXISTS AND LIVE:** Trope lifecycle and governor are fully implemented.
- `TropeState` model exists with `status: str = "dormant"` field (session.py)
- `active_tropes: list[TropeState]` is on `GameSnapshot`
- Trope states have `status` values: "dormant", "progressing" (the active state per ADR-128)
- Temporal governor in `trope_tuning.py` caps simultaneous active tropes at 3
- Trope tick (`trope_tick.py`) manages the dormant→progressing→resolved lifecycle

**Decision:** Trope substrate is ready for indexing. The predicate is: `status == "progressing"` = active, all others (including "dormant" and "resolved") = dormant.

---

**3. ENTITY CARD INFRASTRUCTURE (75-4, ADR-118 §D3) — PARTIALLY READY**

✓ **INDEX LAYER EXISTS:**
- `EntityCard` model defined with `entity_type` field
- `EntityType` enum has: NPC, LOCATION, FACTION, RELATIONSHIP
- `EntityStore` typed index with `add`, `upsert`, `query_by_type`, `query_by_similarity`
- Per-type projectors exist: `project_npc_card`, `project_relationship_card`, `project_faction_card`, `project_location_card`

✗ **MISSING: Quest and Trope projectors**
- NO `project_quest_card` function yet
- NO `project_trope_card` function yet
- These MUST be created as part of this story

---

**4. RETRIEVAL ORCHESTRATION (75-5, ADR-118 §D4) — READY BUT NEEDS EXTENSION**

✓ **FLOOR+FILL SELECTION EXISTS:**
- `retrieve_turn_context` orchestration in `retrieval_orchestration.py` is live
- Pertinence scorer in `pertinence.py` ranks candidates by signal: mention/here/recency/sim
- `present_scene` hard invariant already enforced (candidates sorted with present_scene first)
- `by_type` dictionary in retrieval result already groups by `EntityType`

✗ **MISSING: Active/dormant routing logic**
- Current code retrieves and scores all indexed cards
- NO conditional logic to route active quests/tropes to the floor
- NO separate active-quest/active-trope floor selection
- This routing must be added to `retrieve_turn_context` or a new active-floor builder

---

**5. ENTITY SYNC (75-6, ADR-118 §D2) — NEEDS EXTENSION**

✓ **CURRENT SCOPE:**
- `sync_entity_cards` in `entity_sync.py` projects NPCs, relationships, factions, locations
- Deterministic, idempotent upserts with dirty-flag re-embedding support
- Comprehensive OTEL observability via `EntitySyncResult`

✗ **MISSING: Quest/trope sync logic**
- NO loop over `snapshot.quest_log` to project quest cards
- NO loop over `snapshot.active_tropes` to project dormant-only trope cards
- These must be added with the same guards (blank name / blank content rejects, silent-fallback free)
- Honest per-type counters (`quest_count`, `trope_count`) need to be added to `EntitySyncResult`

---

## Buildable Subset and Scope

**84-5 is NOT blocked. Full scope is achievable:**

1. ✓ Define `EntityType.QUEST` and `EntityType.TROPE` enum values
2. ✓ Write `project_quest_card(quest_entry: QuestEntry) -> EntityCard`
3. ✓ Write `project_trope_card(trope_state: TropeState, trope_def: TropeDefinition) -> EntityCard`
4. ✓ Extend `EntitySyncResult` with `quest_count` and `trope_count` tallies
5. ✓ Extend `sync_entity_cards` to project quests (all statuses) and dormant-only tropes
6. ✓ Extend `retrieve_turn_context` to separate active quests/tropes into a separate floor tier
7. ✓ Add `active_quest_floor` and `active_trope_floor` to the retrieval result
8. ✓ Add OTEL observability: per-type counts, active→floor routing decision spans

**Deferred (explicitly out of scope):**
- §A3 tiered projection/lazy demotion/vector-shedding (WI-3)
- Per-genre governor override (ADR-128 deferred note)
- `consult_notes` mid-turn retrieval tool (ADR-118 A3 footnote, deferred)

## Design Notes

### Active/Dormant Predicates

**Quests (from ADR-137):**
- ACTIVE: `quest_log[id].status` in {"active", "progressing", ...} (any non-completed)
- DORMANT: `status == "completed"` or equivalent
- _Note:_ Exact enum values must be verified in `session.py` — code review will confirm the predicate.

**Tropes (from ADR-128):**
- ACTIVE: `trope.status == "progressing"` (under tension)
- DORMANT: `trope.status` in {"dormant", "resolved"} (at rest or past)

**Relationships (from 84-3, §A2):**
- Always index-side (never floor) — related NPC's presence/mention pulls the relationship card in

### Floor Composition

The floor has three tiers (ranking as `present_scene` override):

1. **Scene-present NPCs/Locations** (floor from 84-1, via 75-2 working-set selection)
2. **Active Quests** (new: route all active quests to the floor)
3. **Active Tropes** (new: route all active tropes to the floor)

The three are ranked together (by `present_scene` invariant), then the fill pulls non-active types by pertinence up to the budget.

### Projector Content Guidance

**Quest card content** (for embedding):
- Title, objective, current status
- Keep it compact — quests are notes, not full lore

**Trope card content** (for embedding):
- Trope name, description, current progress
- Key beats already fired (for context)
- Keep it compact — tropes are notes too

**Dormant-only filtering:**
- Completed quests are never presented mid-turn (the floor never pulls them)
- Resolved/dormant tropes are never presented mid-turn
- On recall (a player says "what happened with X quest?"), retrieval will pull the dormant version if it's referenced by name

## Testing Strategy

**TDD order:**
1. Unit: quest/trope projectors (project_quest_card, project_trope_card)
2. Unit: entity_sync extension (sync_entity_cards includes quests/tropes)
3. Unit: active/dormant routing in retrieve_turn_context
4. Integration: full e2e (game action → sync → retrieval → narrator receives active entities in floor, dormant in fill)
5. OTEL wiring: per-card spans, active→floor routing decision, per-type counters

**Test fixtures:**
- A quest in "active" state + one in "completed" state
- A trope in "progressing" state + one in "dormant" state
- Verify sync projects both but retrieval separates them
- Verify floor always includes active, fill includes dormant

**Wiring test (per CLAUDE.md mandate):**
- End-to-end: player action → execute_intent_router_pre_narrator_pass → entity_sync + retrieve_turn_context → narrator receives typed sections (active_quest_floor, active_trope_floor, retrieved_quests, retrieved_tropes)

## TEA Assessment

**Tests Required:** Yes
**Reason:** Two net-new EntityTypes (the fail-loud trap, twice) + a routing predicate whose whole job is to avoid double-rendering an already-rendered floor — every AC needs failing coverage, and the active/dormant routing has a real correctness hazard.

**LOAD-BEARING INVESTIGATION FINDING (the inverted 84-3 trap):** Active quests AND active tropes ALREADY reach the narrator prompt today:
- Active tropes (`status=="progressing"`) render via `trope_tick.select_foreground_tropes(snapshot.active_tropes)` → `TurnContext.pending_trope_context` (Early) + `active_trope_summary` (Valley `active_tropes` section, `orchestrator.py:2283-2293`). This IS §A2 "active trope rides the floor" — already live, via the trope engine, NOT retrieval.
- Active quests: the whole `quest_log` is in `_STATE_SUMMARY_KEYS` (`session_helpers.py:225`) → dumped into the `state_summary` `<game_state>` section (`orchestrator.py:2119-2124`).
- **Consequence:** §A2 "active→floor reaches narrator" is ALREADY satisfied. 84-5's net-new work is the **DORMANT→INDEX side** + a routing PREDICATE that ensures only DORMANT quests/tropes are projected (active ones are NOT indexed → no double-render). This is the OPPOSITE of the 84-3 dead-projector failure: here the risk is double-rendering, not dead-rendering. AC-8 pins "active reaches prompt via existing path AND is not in the index" (with a dormant control so it can't pass vacuously).

**Predicates (verified against models):** Quest `status == "completed"` → DORMANT (else ACTIVE). Trope `status == "progressing"` → ACTIVE (else DORMANT, incl. "dormant"/"resolved"). The ADR-128 governor caps progressing at 3, so the active trope set is bounded by construction (AC-9).

**SIGNAL_APPLICABILITY decision:** QUEST = `{mention, recency, sim}`, TROPE = `{mention, recency, sim}` — **NOT `here`** (a quest/trope is not physically present like an NPC; a dormant note surfaces by name/topical-similarity, decayed by recency). Both need the full 3-registration (enum + `_ID_NAMESPACE` + `SIGNAL_APPLICABILITY`) or `score_card` fails loud — AC-4 canaries both + the guard-still-fails-loud lock.

**Test Files (6, all RED):**
- `tests/game/test_lifecycle_predicates.py` — `quest_is_dormant`/`trope_is_dormant` (AC-1). 6 tests.
- `tests/game/test_quest_trope_card_projector.py` — `project_quest_card`/`project_trope_card` (AC-2/3). 10 tests.
- `tests/game/test_quest_trope_entity_type.py` — QUEST+TROPE 3-registration + fail-loud guard (AC-4). 9 tests.
- `tests/game/test_lifecycle_sync_routing.py` — DORMANT-ONLY sync + counts + active-not-indexed + governor cap (AC-5/9). 7 tests.
- `tests/game/test_dormant_retrieval.py` — dormant→retrieval surfaces + new fields (AC-6). 6 tests.
- `tests/server/test_lifecycle_render_wiring.py` — dormant→prompt render + active-not-double-rendered + OTEL + 2 e2e (AC-7/8/10/11). 9 tests.

**Tests Written:** 47 covering AC-1…AC-11 (AC-12 = GREEN-gate). **Status:** RED — 41 failing, 0 passing.
- Clean feature-absence: `ModuleNotFoundError` (`lifecycle_scope`), `ImportError` (`project_quest/trope_card`), `AttributeError` (`EntityType.QUEST/TROPE`, `EntitySyncResult.quest/trope_count`), `TypeError` (`sync_entity_cards(tropes=)` kwarg), `AssertionError` (enum/field presence). No typos/fixture bugs.
- AC-8 active-not-indexed tests HARDENED with a dormant control (the dormant sibling MUST be indexed), so "active absent from index" can't pass vacuously by quest/trope indexing being dead.

**Wiring paths (two e2e, AC-11):** ACTIVE → live `_build_turn_context`/`sync_for_turn`: quest reaches prompt via existing `state_summary`, NOT indexed. DORMANT → live `sync_for_turn` indexes a completed quest → `retrieve_turn_context` + render seam surfaces it in the narrator prompt (index→retrieve→render, no dead layer).

**Run command (OTEL-sensitive — serial):**
`uv run pytest -n0 tests/game/test_lifecycle_predicates.py tests/game/test_quest_trope_card_projector.py tests/game/test_quest_trope_entity_type.py tests/game/test_lifecycle_sync_routing.py tests/game/test_dormant_retrieval.py tests/server/test_lifecycle_render_wiring.py`

**Handoff:** To Dev (Naomi) for implementation (GREEN).

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/game/lifecycle_scope.py` (NEW, pure) — `quest_is_dormant` (status=="completed") + `trope_is_dormant` (status!="progressing").
- `sidequest/game/entity_card.py` — `EntityType.QUEST`/`TROPE` + `_ID_NAMESPACE` ("quest"/"trope"); NEW `project_quest_card` (title+objective+status, `quest:<id>`, never-blank) + `project_trope_card` (definition.name+description+status, `trope:<id>`, never-blank); `retrieval.quest_count`/`retrieval.trope_count` added to `UNIVERSAL_RETRIEVAL_SPAN_ATTRS`.
- `sidequest/game/pertinence.py` — `SIGNAL_APPLICABILITY[QUEST]=[TROPE]={mention, recency, sim}` (NOT here). **Only the dict touched — frozen `score_card`/`select_within_budget`/structs untouched.**
- `sidequest/game/entity_sync.py` — DORMANT-GATED quest + trope projection loops (predicate-gated) + `quest_count`/`trope_count` on `EntitySyncResult`; `sync_entity_cards` gains `tropes=` (def-by-id join).
- `sidequest/game/retrieval_orchestration.py` — `by_type` QUEST+TROPE buckets + `retrieved_quests`/`retrieved_tropes` fields + `retrieval.quest_count`/`trope_count` span attrs (all return paths). **Fill scorer calls untouched.**
- `sidequest/server/session_helpers.py` + `sidequest/agents/orchestrator.py` — render `retrieved_quests`/`retrieved_tropes` DORMANT Valley sections (84-3 pattern: render → TurnContext field → Valley registration). Active quest/trope render paths untouched.
- `sidequest/server/dispatch/entity_sync.py` — `_collect_trope_definitions(sd)` → thread `tropes=` into `sync_for_turn`; `quest_count`/`trope_count` on the `accretion.entity_sync` span + watcher event.
- `tests/fixtures/packs/test_genre/tropes.yaml` (via the `caverns_and_claudes` symlink) — added the two trope defs (`the_keeper_stirs`, `extraction_panic`) the AC-8 e2e test seeds (it uses real pack ids absent from the frozen fixture). Test-fixture content, not production.

**2 predicates + 2×3-registration:** `quest_is_dormant`/`trope_is_dormant` (lifecycle_scope.py). QUEST and TROPE each landed all three registrations together (enum+namespace, SIGNAL_APPLICABILITY, retrieval by_type) — both fail-loud canaries (`test_score_card_on_{quest,trope}_does_not_fail_loud`) + the bogus-type guard (`test_bogus_type_still_fails_loud`) green.

**Dormant-gate (active NOT indexed):** the sync quest/trope loops `continue` unless the dormant predicate is True. AC-8 proves it with a dormant CONTROL: a completed quest / resolved trope MUST index while the active/progressing sibling MUST NOT (`quest:q_live`/`trope:the_keeper_stirs` absent from the index; `quest:q_done`/`trope:extraction_panic` present). Active items still reach the prompt via their EXISTING paths (state_summary / trope foreground) — no second render path added.

**Both e2e paths:** ACTIVE → existing path, not indexed (`test_e2e_active_quest_to_prompt`); DORMANT → index→retrieve→render end-to-end (`test_e2e_dormant_quest_index_to_prompt`).

**OTEL:** routing decision on `entity_sync` span + watcher (`quest_count`/`trope_count` = DORMANT indexed count); surfaced count on `retrieval.universal` span (`retrieval.quest_count`/`trope_count`, declared in the contract set so 84-4's bidirectional check stays green).

**Tests:** 41/41 new green. Regression: retrieval+frozen-scorer+84-4-contract+entity_card 76, entity_sync+dispatch+store+84-3 329, orchestrator+session_helpers 30, trope+quest engine 86 — all passed. `ruff` clean; `pyright` clean on changed code (the one `orchestrator.py:3064 send_stream` error is PRE-EXISTING, shifted by this diff, not introduced).
**Branch:** feat/84-5-lifecycle-aware-scope (committed; not pushed — SM finishes).

**Handoff:** To review (Chrisjen Avasarala).

## Delivery Findings

No upstream findings. All prerequisites are live and verified.

### TEA (test design)
- **Gap** (blocking-if-missed, the double-render trap): Active quests/tropes ALREADY render (quests via `state_summary` quest_log dump; active tropes via `trope_tick.select_foreground_tropes`). Dev must NOT route active quests/tropes through a NEW active-render section — that double-renders. The predicate ROUTES: active stays on its existing floor path, only DORMANT gets projected/indexed. AC-8 pins it. Affects `entity_sync.sync_entity_cards` (gate) — do NOT touch the trope/state_summary render paths.
- **Gap** (blocking): the fail-loud 3-registration trap hits TWICE (QUEST + TROPE). Each needs enum + `_ID_NAMESPACE` + `SIGNAL_APPLICABILITY` together or `score_card` raises. Affects `entity_card.py` + `pertinence.py`.
- **Improvement** (non-blocking): the dispatch `sync_for_turn` currently passes `factions=` + `locations=` but NOT `tropes=` (`dispatch/entity_sync.py:199`). Dev must thread `tropes=sd.genre_pack.tropes` through so the TropeDefinition name/description join resolves. The e2e tests use REAL pack trope ids (`the_keeper_stirs`, `extraction_panic`) to exercise this. Affects `dispatch/entity_sync.py`.
- **Improvement** (non-blocking): the trope card needs `TropeDefinition` (TropeState carries only `id`). Join via `sd.genre_pack.tropes` keyed by id — the same join `session_helpers.py:1124` uses. Don't fabricate a name from the id. Affects `project_trope_card` + the sync loop.

### Dev (implementation)
- **Gap** (non-blocking): the frozen test fixture pack (`tests/fixtures/packs/caverns_and_claudes` → symlink to `test_genre`) did NOT contain the real-pack trope ids the AC-8 e2e test seeds (`the_keeper_stirs`, `extraction_panic`); its `tropes.yaml` had only `ruin_fever`/`mutation_tide`/`dead_signal`. I added minimal definitions for the two ids so the dormant-trope definition-join resolves under the autouse `_fixture_pack_search_paths` redirect. Affects `tests/fixtures/packs/test_genre/tropes.yaml`. *Found by Dev during implementation.*
- No blocking upstream findings.

## Design Deviations

None yet.

### TEA (test design)
- No deviations. ACs derive from ADR-118 §A2 (DORMANT-ONLY) + §D2 + ADR-128 + ADR-137 + live investigation (active-already-renders finding, 2× fail-loud chain, dormant-only routing).

### Dev (implementation)
- **Added two trope definitions to the frozen test fixture pack for the AC-8 e2e join**
  - Spec source: context-story-84-5.md, AC-8 / `test_lifecycle_render_wiring.py::test_progressing_trope_renders_via_existing_path_not_retrieval`
  - Spec text: "Use REAL pack trope ids so the TropeDefinition join (name/description) resolves on the live dispatch path."
  - Implementation: the `tests/server/` autouse `_fixture_pack_search_paths` fixture redirects pack loading to the frozen `tests/fixtures/packs/` (a `caverns_and_claudes`→`test_genre` symlink), whose `tropes.yaml` lacked `the_keeper_stirs` / `extraction_panic`. Added minimal (`id`/`name`/`description`/`category`) definitions for both so the dormant-trope projector's definition-join resolves and the dormant CONTROL (`extraction_panic`, resolved) indexes as the test requires.
  - Rationale: the test depends on those ids existing in the loaded pack; under the fixture redirect they were absent. Production `_collect_trope_definitions` was verified correct in isolation (it returns the real pack's 8 tropes including `extraction_panic`); this is a test-fixture data gap, not a production change. Minimal addition — only the two ids the test names, projector-readable fields only.
  - Severity: minor
  - Forward impact: none — test-only fixture content; the production trope source is the live genre pack.

## Reviewer Assessment (84-5, commit c5d3e08)

**Reviewer:** Chrisjen Avasarala (adversarial review, Lap 5 — final gate before epic 84 closes)
**Verdict:** APPROVED — merge-ready. The epic closes. The double-render invariant (the inverted-84-3
trap) holds BY CONSTRUCTION — I proved it empirically. One substantive Should-fix on the quest predicate's
narrowness (documented + deliberate, non-blocking) + two Nits.

**Scope reviewed:** full diff `develop...feat/84-5-lifecycle-aware-scope` (1167 +/2 -): new
`lifecycle_scope.py` (2 predicates), QUEST/TROPE 2×3-registration, dormant-gated sync loops, `retrieved_
quests`/`retrieved_tropes` + render seam, OTEL counts, 2 fixture trope defs, 6 new test files. Verified vs
ADR-118 §A2 (DORMANT-ONLY) + ACs 1-12.

**Verification run (-n0 serial):**
- 84-5 full suite (predicates + projector + entity-type + sync-routing + dormant-retrieval + render-wiring):
  **41 passed**. Regression (84-1/84-2/84-3/84-4 scorer/orchestration/span/relationship/sync/render):
  **87 passed**. Shared-fixture consumer (trope_tick): **23 passed**. `ruff check` (8 files): clean. Tree
  clean; HEAD c5d3e08.

**Adversarial checks (7 axes):**
1. **Double-render invariant — HOLDS BY CONSTRUCTION, proven.** `retrieved_quests`/`retrieved_tropes` can
   only contain cards in the EntityStore; the dormant-gated sync (`if not <type>_is_dormant: continue`)
   never projects an ACTIVE quest / PROGRESSING trope into the store — so an active item physically cannot
   enter the retrieval sections. The render seam reads ONLY `entity_retrieval.retrieved_*` (store-sourced),
   never active state. I drove the full quest status space (active/completed/failed/resolved/in_progress/
   abandoned/blank): ONLY `completed` indexes; all others stay active-floor, absent from the index. No path
   double-renders. AC-8 pins it both ways (active not indexed AND still reaches prompt via state_summary),
   with a non-vacuous control.
2. **Predicate completeness — TROPE clean, QUEST narrow (Should-fix).** TROPE: the real engine status space
   is exactly `{dormant, progressing, resolved}` (trope_tick.py:293/371; default "dormant") — `!= "progressing"`
   is exhaustive and correct (dormant/resolved → index; progressing → floor). The `seeded`/`pending` cases I
   probed don't exist in the engine. QUEST: `== "completed"` ONLY. But the `record_quest` tool status field
   is a FREE-FORM string (record_quest.py:73, `status: str`, max_len 32) and its own description lists
   "active / **completed / failed / resolved**" — so `failed` and `resolved` are REAL narrator-set quest
   statuses (narration_apply.py also writes "resolved" via the trope-handshake quest entry). A `failed`/
   `resolved`/`abandoned` quest is a FINISHED thread that §A2 / the ADR amendment ("a finished quest becomes
   a dormant, lookup-able note") intends to be dormant — but the predicate keeps it ACTIVE-floor forever,
   never indexed, never recall-able as a dormant note, and it keeps consuming state_summary budget as if live
   pressure. NOT a double-render (each quest is in exactly one place), NOT a flood (under-inclusive) — a
   recall-completeness / prompt-staleness gap. See Should-fix #1.
3. **2×3-registration fail-loud + exhaustiveness — CLEAN.** QUEST + TROPE each land enum + `_ID_NAMESPACE` +
   `SIGNAL_APPLICABILITY` atomically. Grepped EVERY `.entity_type` / `EntityType.*` site: `entity_store`
   filters parametric (`==`/`!=`), `by_type.setdefault` generic + now explicitly buckets QUEST/TROPE,
   `pertinence._applicable_signals.get` fail-loud with all 6 types declared, no match/case anywhere, no
   hardcoded N/L/F/R enumeration that misses Q/T. `score_card` on quest/trope cards does not raise; a bogus
   type still raises.
4. **Fixture change — ADDITIVE, no coupling.** 2 minimal trope defs (id/name/description/category) APPENDED
   to the shared `test_genre/tropes.yaml`; no existing def touched. 23 trope-tick consumers + full 84-5 set
   green. The "could've reused 3 existing defs" is a cosmetic preference — dedicated, clearly-labeled test
   fixtures are arguably cleaner than coupling the e2e to incidental defs. Nit, not worth folding.
5. **OTEL honesty — dormant count explicit, active count derivable (Nit).** `quest_count`/`trope_count`
   (span `entity_sync.*` + watcher event) report the DORMANT-indexed count — the routing decision's positive
   output, observable. The ACTIVE count is NOT co-located on this span, but IS observable via existing floor
   telemetry (active quests in `state_summary` / prompt_assembled; active tropes via `trope_tick` spans), so
   a panel can derive "active = quest_log total − dormant indexed." Routing decision is observable; a
   co-located active/dormant split would be cleaner. Nit.
6. **Frozen scorer + 84-4 — INTACT.** `pertinence.py` = 6 +/0 - (ONLY the 2 applicability rows; no
   score_card/select_within_budget/fill-loop logic touched). `retrieval.quest_count`/`trope_count` BOTH
   declared in `UNIVERSAL_RETRIEVAL_SPAN_ATTRS` AND emitted — 84-4's bidirectional contract holds.
7. **Determinism / never-blank / projector / render-to-prompt — VERIFIED.** Sparse title-less quest →
   `"quest:q1 (completed)"` (non-blank); same input → byte-identical content + id (75-6 reproject safe).
   Trope joins the TropeDefinition for name/description (no fabricated name; missing def → loud-skip,
   counted `failed`). Dormant cards reach the ACTUAL narrator prompt via the 84-3 render seam (session_helpers
   `render_entity_section` → `TurnContext.retrieved_entity_quests/tropes` → orchestrator Valley loop) — the
   render-wiring tests assert the section registers with the summary text in content (not a dead struct
   field — the 84-3 lesson is applied). Drove a dormant quest → surfaces in `retrieved_quests` via cosine.

**Findings (none blocking):**

| Severity | Finding | Location |
|----------|---------|----------|
| Should-fix | `quest_is_dormant == (status=="completed")` ONLY. `failed`/`resolved`/`abandoned` are real narrator-set quest statuses (record_quest tool vocabulary) for FINISHED threads that §A2 intends as dormant notes — but they stay active-floor forever, never indexed/recall-able, and keep polluting state_summary as live pressure. Documented + deliberate (session line 144 "any non-completed = active"), no double-render, no flood — but narrower than §A2's "finished quest = dormant note." Recommend `quest_is_dormant = status in {"completed","failed","resolved","abandoned"}` (or a terminal-status set), tracked as a tuning follow-on. | `sidequest/game/lifecycle_scope.py:35` |
| Nit | QUEST/TROPE declare `mention` applicable, but the retrieval fill computes only `sim` per card (mention/recency hardcoded 0 — the 84-1 per-card-signal deferral). So a dormant note surfaces ONLY via cosine, never via a NAMED reference, despite the declared mention applicability. Less acute than it was for relationships (a dormant quest is a topical-recall item; cosine is the primary intended channel), but the declared `mention` is currently aspirational. | `retrieval_orchestration.py` fill loop + `pertinence.py:88-90` |
| Nit | The active quest/trope count is not co-located on the `entity_sync` span (only the dormant count is). Derivable from existing floor telemetry, but a direct active/dormant split would make the routing decision fully self-describing. | `dispatch/entity_sync.py` |

**Deviation audit:** TEA + Dev logged the predicate decisions explicitly (session 144/209) and the asymmetric
quest(snapshot)/trope(param) source seam. The quest-predicate narrowness (Should-fix #1) is documented as a
deliberate "non-completed = active" choice — I'm flagging it as a §A2-completeness gap, not an undocumented
deviation. **ACCEPTED** with the Should-fix tracked.

**Handoff:** To SM for finish-story — **epic 84 closes.** All 6 WI stories landed (84-1 scorer, 84-4 OTEL,
84-2 alias, 84-3 relationship-after-rewire, 84-5 lifecycle scope). The mechanism is correct and the
double-render trap is genuinely avoided. Should-fix #1 (terminal-quest-status dormancy) is the one piece of
unfinished §A2 intent worth a stacked follow-on; it is non-blocking (safe, documented, no double-render).
Merge-ready.
