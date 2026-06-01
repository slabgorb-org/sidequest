---
story_id: 75-4
jira_key: ""
epic: 75
workflow: tdd
---

# Story 75-4: Universal retrieval: EntityCard model + per-type projectors (NPC/location/faction) + typed store generalization (ADR-118)

## Story Details

- **ID:** 75-4
- **Epic:** 75 — RAG Retrieval Layer
- **Points:** 5
- **Priority:** p2
- **Jira Key:** (none — this is a personal project)
- **Workflow:** tdd
- **Stack Parent:** 75-2 (budgeted NPC working-set selection)
- **Depends On:** 75-2 ✓ (done 2026-06-01)
- **Unlocks:** 75-5 (retrieve_turn_context orchestration), 75-6 (card sync/reproject hook)

## Acceptance Criteria

1. **EntityCard model defined and implemented** — structural sibling of `LoreFragment` with:
   - `id` (stable: "npc:borin", "loc:black_hart", "faction:tide_syndicate")
   - `entity_type` ("npc" | "location" | "faction")
   - `entity_ref` (back-pointer, no data ownership)
   - `content` (embeddable text projection)
   - `token_estimate` (computed from content length)
   - `embedding` / `embedding_pending` / `embedding_retry_count` (identical to `LoreFragment`)
   - `metadata` (provenance, last_seen turn, region, disposition tier, etc.)

2. **Per-type projectors wired** — each entity type provides `to_card()` that renders embeddable content:
   - **NPC** → name, role, pronouns, disposition tier, goals, key facts (from `NpcPoolMember`/`Npc`)
   - **Location/POI** → name, description, mechanical properties, linked NPCs (from room graph / materialization / PG promotion)
   - **Faction** → goals, attitude toward party, notable members/resources (from faction state)
   - Projectors handle diffuse location sources (room graph vs. materialization vs. PG promotion)

3. **Typed store generalization** — extend the `LoreStore` machinery to a universal index:
   - Define a store that holds `EntityCard`s alongside or as a typed category within the existing `LoreStore`
   - Reuse embedding worker, `cosine_similarity`, `query_by_similarity`, dimension-mismatch requeue, daemon MiniLM-L6-v2 path
   - Category-style filtering (cf. `LoreStore.query_by_category`) keeps entity-type queries clean
   - No new embedding model, no schema migration — one unified machinery, typed by `entity_type`

4. **No wiring to retrieval orchestration yet** — this story is the foundation layer only:
   - `EntityCard` and projectors exist and are tested in isolation
   - The typed store can be queried by type, with embedding support
   - No per-turn retrieval loop yet (that is 75-5)
   - No dirty-flag sync hook yet (that is 75-6)

5. **Tests cover all entity types** — unit tests for each projector:
   - NPC card projection (name, role, disposition, goals)
   - Location/POI card projection (from different sources)
   - Faction card projection
   - Card construction and token estimation
   - Store add/query by type and similarity
   - Embedding worker read-back (already exists for LoreFragment; verify it works for EntityCard)

6. **Wiring test included** — verify the store is reachable from production code:
   - Create a synthetic scenario with NPCs, locations, factions
   - Construct cards for each
   - Add them to the store
   - Query by type and verify retrieval works
   - Assert the store can be instantiated and used in a real game context (not just unit test isolation)

7. **OTEL spans prepared (no wiring yet)** — span definitions ready for 75-5:
   - Define `card_reproject_count`, `stale_card_count` span attributes (per ADR-118 D5)
   - Define `retrieval.universal` span structure (emitted by 75-5, attributes pre-defined now)
   - Telemetry hooks stubbed for per-type retrieval counts (filled in by 75-5)

## Technical Approach

### File Structure

The implementation adds:

- **`sidequest/game/entity_card.py`** (new) — `EntityCard` model, per-type projectors
  - `EntityCard` class (Pydantic BaseModel, mirroring `LoreFragment`)
  - `NpcCardProjector`, `LocationCardProjector`, `FactionCardProjector` classes with `to_card()` methods
  - Card ID generation conventions (e.g., `f"npc:{npc.id}"`)
  - Content projection templates (turn into embeddable prose without metadata leakage)

- **`sidequest/game/entity_store.py`** (new OR extend `lore_store.py`) — typed store
  - Option A: New `EntityStore` class (mirror `LoreStore` but hold `EntityCard`s)
  - Option B: Extend `LoreStore` to be polymorphic (hold both `LoreFragment` and `EntityCard`)
  - Recommendation: **Option A** (separate store) for clarity; they share the same embedding machinery via a common interface
  - Methods: `add(card)`, `query_by_type()`, `query_by_similarity()`, `update_embedding()`, total_tokens accessors
  - Save/load round-trips cards with embeddings intact

- **Tests** — `tests/game/test_entity_card.py`, `tests/game/test_entity_store.py`
  - Projector unit tests (card content generation)
  - Store add/query/similarity tests
  - Embedding worker round-trip (mocked daemon)
  - Wiring test from a real game context (synthesize a scenario, construct cards, query them)

### Reuse Points

1. **Embedding machinery** — The daemon MiniLM worker and `update_embedding()` callback already exist in `lore_embedding.py`:
   - `embed_pending_fragments()` → `daemon_client.embed()`
   - `LoreStore.update_embedding()` → write-back path
   - Extend `embed_pending_fragments()` to also consume `EntityCard`s with `embedding_pending=True` (or make it polymorphic on entity type)

2. **Cosine similarity** — `LoreStore.query_by_similarity()` already computes rankings:
   - Add a `EntityStore.query_by_similarity()` method that reuses the same cosine math
   - Add optional `entity_type_filter` parameter to narrow results

3. **Metadata handling** — `LoreFragment.metadata` is already a string-keyed dict:
   - `EntityCard.metadata` follows the same pattern
   - Use keys like `last_seen_turn`, `disposition_tier`, `location_region`, `source` for provenance

### Design Decisions

1. **Card content projection must be deterministic** — same NPC state → same card content every time (for embeddings to remain fresh after updates)
   - Sorting (NPC names in goals, faction members alphabetically) prevents embedding churn from random order
   - Turn-to-turn immutability is enforced by the dirty-flag sync in 75-6 (not this story)

2. **Embedding pending and retry count are inherited from LoreFragment** — no new worker complexity:
   - `embedding_pending=True` when card is created or marked dirty
   - Daemon worker picks up both `LoreFragment` and `EntityCard` in the same pass
   - `embedding_retry_count` increments per failure; callers can gate on a threshold

3. **Location projectors handle diffuse sources** — a card must be creatable from any of:
   - Room graph (rooms via the `RoomGraph`)
   - Materialization (visited scenes)
   - PG promotion (if locations are ever promoted to rows)
   - Single `LocationCardProjector.to_card()` adapts per source, or multiple typed methods for each source (TBD after scout of location cardinality)

4. **Faction representation** — factions are not fully modeled in the current codebase yet:
   - Cards project from the `Faction` struct in game state (if it exists) or from a simplified sketch
   - If factions are not yet in the snapshot, stub the projector to work on placeholder data for now (no silent fallbacks; if a faction can't be projected, the error is loud)

5. **No eviction, no quota** — unlike the 75-2 working-set selection:
   - The store is append-only (cards added once per entity per session)
   - The embedding worker will process all cards with `embedding_pending=True`, not a subset
   - Per-turn quota is a 75-5 responsibility (the `retrieve_turn_context` budget seam)

### Implementation Order

1. Define `EntityCard` class and validation rules
2. Implement per-type projectors (`NpcCardProjector`, `LocationCardProjector`, `FactionCardProjector`)
3. Create `EntityStore` (or extend `LoreStore`) with add/query/similarity methods
4. Wire embedding worker to handle `EntityCard`s (extend `embed_pending_fragments()` or make it polymorphic)
5. Write unit tests for projectors and store
6. Write integration/wiring test from a real game context
7. Define OTEL span attributes (no emitting yet)

## Upstream Findings

- **LoreStore wiring is live** — embedding worker already fires every turn in production (`websocket_session_handler.py:2449 → lore_embedding.py:276 → orchestrator.py:2096`). No stub code to wake up.
- **Entity data is diffuse** — NPCs live in `NpcPoolMember`, locations scattered across `RoomGraph`/materialization/PG, factions in faction state. Projectors must adapt.
- **No schema migration needed** — EntityCard is in-memory (per ADR-118 D1), not a Postgres promotion. Index lives on top of existing snapshots.
- **Story 75-2 (budgeted working-set) is complete** — this story can assume `NpcPoolMember.last_seen_turn` and the recency logic are in place.

## Deviations

None yet. Check back after RED phase.

## Sm Assessment

**Setup verdict:** Ready for RED. Story is well-scoped foundation work.

- **Dependency gate cleared.** 75-4 depends on 75-2, which is `done` (along with 75-1 and 75-3). Nothing blocks the start. This is the root of the epic-75 universal-retrieval chain: 75-4 → (75-5 ∥ 75-6) → 75-7 → 75-8. Operator explicitly chose the topological run over collapsing the five into one mega-story.
- **Scope boundary is clean.** 75-4 is *foundation only* — EntityCard model + per-type projectors (NPC/location/faction) + typed-store generalization. No per-turn retrieval orchestration (that's 75-5), no dirty-flag reproject hook (75-6), no OTEL emit/GM-panel (75-7), no e2e wiring (75-8). TEA must hold this line: tests should cover the model, projectors, store add/query, and an embedding round-trip — *not* turn orchestration.
- **Reuse over reinvention.** Upstream findings confirm LoreStore embedding machinery is live in production every turn; 75-4 generalizes it rather than building new. Watch for the "Don't Reinvent" principle here — extend `LoreStore`/embedding worker, don't fork it.
- **Wiring-test requirement.** Per project doctrine, the suite needs at least one integration test proving EntityCard projection is reachable from real game context (synthesize scenario → query cards), not just unit-isolated projector tests.
- **Single repo.** sidequest-server only; branch `feat/75-4-universal-retrieval-entity-card` created and clean. No UI/content/daemon surface this slice.

Handoff to The Architect (TEA) for RED.

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-01T12:23:13Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-01 | — | — |

## TEA Assessment

### Red Phase (test writing)

**Tests Required:** Yes
**Reason:** New model + projectors + typed store (5 pts, 7 ACs) — pure new behavior.

**Test Files:**
- `tests/game/test_entity_card.py` — `EntityCard` model (AC-1) + NPC/faction/location projectors (AC-2).
- `tests/game/test_entity_store.py` — typed store add/query/similarity (AC-3), embedding-worker contract + save/load round-trip (AC-5), OTEL attribute-name definitions (AC-7), and the mandatory fixture-driven wiring test (AC-6).

**Tests Written:** 30 tests across 8 classes, covering 7 ACs.
**Status:** RED (clean) — verified by `testing-runner` (RUN_ID `75-4-tea-red`): both files error with `ModuleNotFoundError: No module named 'sidequest.game.entity_card'` / `entity_store` and nothing else. Existing-symbol imports + fixtures separately verified to resolve (`Disposition(-40).attitude() == "hostile"`, `_estimate_tokens("x"*40) == 10`), so RED fails for the right reason.

**Contract handed to Dev (the API these tests pin):**

- `sidequest/game/entity_card.py`
  - `EntityType` — `NPC="npc"`, `LOCATION="location"`, `FACTION="faction"`.
  - `EntityCard(BaseModel, extra="forbid")` — fields `id, entity_type, entity_ref, content (blank-rejected), token_estimate, metadata: dict[str,str], embedding, embedding_pending=True, embedding_retry_count=0` (LoreFragment-sibling worker contract).
  - `EntityCard.new(entity_type, entity_id, content, *, entity_ref=None, metadata=None)` → `id = f"{type}:{entity_id}"`, `token_estimate = lore_store._estimate_tokens(content)` (REUSE, asserted), `entity_ref` defaults to `entity_id`.
  - `project_npc_card(member: NpcPoolMember)` → `id "npc:<name.casefold()>"`, content carries name/role/pronouns + disposition **attitude band** (not raw int), deterministic.
  - `project_faction_card(faction: Faction)` → `id "faction:<name slug>"`, content carries name/summary/disposition.
  - `project_location_card(*, location_id, name, description, mechanical_properties=None, linked_npcs=None)` → `id "loc:<location_id>"`, blank description rejected. **Normalized-view signature** (see deviation).
  - Module constants: `SPAN_CARD_REPROJECT_COUNT="card_reproject_count"`, `SPAN_STALE_CARD_COUNT="stale_card_count"`, `UNIVERSAL_RETRIEVAL_SPAN_ATTRS` containing `retrieval.npc_count` / `retrieval.location_count` / `retrieval.faction_count`. **Names only — DO NOT emit** (75-7's job).
- `sidequest/game/entity_store.py`
  - `DuplicateEntityId(Exception)`; `EntityStore(BaseModel, extra="forbid")` with `cards: dict[str, EntityCard]`.
  - `add` (raises on dup), `query_by_type`, `query_by_similarity(query_embedding, top_k=5, entity_type=None)` reusing `cosine_similarity` (skip un-embedded cards), `update_embedding(id, embedding)` (clears pending, resets retry), `pending_embedding_ids(*, max_retries=None)`, `total_tokens` property, `__len__`.
  - Save/load via pydantic `model_dump_json` / `model_validate_json` round-trips embeddings.

**Reuse mandate for Dev (ADR-118 D3 / *Don't Reinvent*):** import `_estimate_tokens` and `cosine_similarity` from `lore_store`; do NOT re-implement token math or cosine. A test asserts `card.token_estimate == _estimate_tokens(content)` and that similarity scores agree with `cosine_similarity`.

### Rule Coverage

| Lang-review check (python.md) | Test(s) | Status |
|---|---|---|
| #6 Test quality — no vacuous asserts | self-checked; all asserts pin values, not truthiness | passing (self) |
| #11 Input validation at boundary (blank content) | `test_blank_content_is_rejected`, `test_empty_content_is_rejected`, `test_blank_description_rejected` | failing (RED) |
| No Silent Fallbacks (SOUL/server) | blank-content + blank-description loud-fail tests | failing (RED) |
| #3 Type annotations at boundary | enforced via the pinned `.new()` / projector signatures | failing (RED) |
| Wiring test mandate (server CLAUDE.md) | `TestUniversalIndexWiring::test_scenario_entities_project_index_and_retrieve` (fixture-driven, NOT source-grep) | failing (RED) |
| Determinism (ADR-118 D3 dual-rep) | `test_projection_is_deterministic`, faction `test_deterministic` | failing (RED) |
| Duplicate-id no silent overwrite | `test_duplicate_id_raises` (mirrors `DuplicateLoreId`) | failing (RED) |

**Rules checked:** 7 applicable checks have coverage. **Self-check:** 0 vacuous tests (every assert pins a value/membership/raise).

**Handoff:** To Dev (Agent Smith) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/game/entity_card.py` (new) — `EntityType` (StrEnum), `_ID_NAMESPACE`, `EntityCard` (LoreFragment-sibling, blank-content rejection, computed `token_estimate`), `EntityCard.new` factory, `project_npc_card` / `project_faction_card` / `project_location_card`, OTEL attribute-name constants (`SPAN_CARD_REPROJECT_COUNT`, `SPAN_STALE_CARD_COUNT`, `UNIVERSAL_RETRIEVAL_SPAN_ATTRS`).
- `sidequest/game/entity_store.py` (new) — `DuplicateEntityId`, `EntityStore` (typed index: `add` / `query_by_type` / `query_by_similarity(+type filter)` / `update_embedding` / `pending_embedding_ids` / `total_tokens` / `__len__`), reusing `cosine_similarity`.
- `tests/game/test_entity_card.py`, `tests/game/test_entity_store.py` — lint tidy only (tightened blind `Exception` → `ValidationError`; removed stale "module under construction" `# noqa: E402` markers now the modules exist).

**Reuse honored (ADR-118 D3):** `_estimate_tokens` and `cosine_similarity` imported from `lore_store` — no re-implementation. Token-math and cosine agreement are test-asserted.

**Notable implementation decision:** the testing-runner surfaced a real contract bug — my first cut used `EntityType.LOCATION` ("location") directly, producing `location:black_hart`, but ADR-118 D3 / the tests want `loc:black_hart`. Rather than the bypass-the-factory hack that briefly landed, I centralized the id-namespace convention in `_ID_NAMESPACE` (npc→`npc`, location→`loc`, faction→`faction`) so a single `EntityCard.new` path serves every projector. The `entity_type` field stays `"location"`; only the id abbreviates.

**Quality gates:**
- Tests: **33/33 passing** (GREEN) — verified by `testing-runner` (RUN_ID `75-4-dev-green-2`) and a post-lint direct run.
- ruff check: clean · ruff format: clean · pyright: 0 errors, 0 warnings.

**Branch:** `feat/75-4-universal-retrieval-entity-card` (pushed).

**Handoff:** To next phase (spec-check / verify).

### Dev Rework 1 (review reject → green)

Addressed all 6 confirmed Reviewer findings (commit `bd22c53`). All input boundaries now fail loud, matching the model's own `content`-validator precedent:

| Reviewer finding | Severity | Fix |
|---|---|---|
| `_ID_NAMESPACE.get(..., type_str)` silent fallback | HIGH | `EntityCard.new` raises `ValueError` on unknown `entity_type` |
| Blank name → `"npc:"`/`"faction:"` degenerate id | HIGH | `_slug` raises on blank name; `EntityCard.new` also guards blank `entity_id` (location path) |
| Faction projector missing blank-segment filter | MEDIUM | `project_faction_card` uses `" — ".join(seg for seg in segments if seg)` |
| `update_embedding([])` accepts empty vector | MEDIUM | raises `ValueError` on empty embedding |
| `mechanical_properties` projection unverified | MEDIUM | test asserts `"cover: heavy"` in content + `None`-absent case |
| Blank-input raises too broad | MEDIUM | added `match=` to all blank-rejection tests |

Plus recommended: determinism tests pin exact strings (`"Borin — smith — he/him — neutral"`, `"Tide Syndicate — s"`); added a direct `EntityCard.new(EntityType.LOCATION, …)` assertion that the id is `loc:…`.

**Deliberately NOT changed** (Reviewer scoped these forward, do-not-build-now): dimension-mismatch requeue → 75-5/75-6; `card.content` prompt-injection sanitization → explicit 75-5 AC. Their Delivery Findings stand.

**Tests:** 41 passing (was 33; +8 guard tests). ruff clean · format clean · pyright 0 errors.
**Handoff:** Back through spec-check → verify → review.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned (minor drift, all defensible)
**Mismatches Found:** 4 (0 critical, 0 major, 1 minor, 3 trivial) — none require a hand-back to Dev.

Verified structurally (gate passed) and substantively (read all 7 ACs against `entity_card.py` / `entity_store.py` and the 33 tests). The implementation is a faithful, reuse-first realization of ADR-118 §D1–D3: `EntityCard` is a true `LoreFragment` sibling, `_estimate_tokens` + `cosine_similarity` are imported not re-implemented, and the index owns no truth (`entity_ref` back-pointer only). AC-4 confirmed by grep — the only `reproject`/`dirty`/`Valley` tokens are docstrings and the deferred span-name constant; no orchestration logic leaked. No premature production consumers; the fixture-driven wiring test correctly stands in for a consumer at the foundation slice.

- **AC-3 reuse list names "dimension-mismatch requeue"; `EntityStore` omits `requeue_dimension_mismatched` / `mark_embedding_failed`** (Missing in code — Architectural, **Minor**)
  - Spec: AC-3 reuse points list "Reuse embedding worker, `cosine_similarity`, `query_by_similarity`, dimension-mismatch requeue".
  - Code: store reuses cosine + the worker write-back contract but not the requeue/failure guard.
  - Recommendation: **D (defer)** — no 75-4 AC test requires it, and the guard only bites when a *live* daemon changes embedding dimension on a model upgrade. That worker wiring is 75-5/75-6. Dev already forward-flagged it in Delivery Findings. Carry into 75-6 (or 75-5's retrieval pass, which is where `requeue_dimension_mismatched` is called for lore). Logged as a deferred deviation below at reconcile.

- **AC-2 NPC "goals, key facts" not in the projected card** (Missing in code — Behavioral, **Trivial**)
  - Spec: AC-2 NPC → "name, role, pronouns, disposition tier, **goals, key facts**".
  - Code: projects name/role/pronouns/attitude-band; no goals/key-facts.
  - Recommendation: **C (clarify spec)** — `NpcPoolMember` is identity-only (no `goals`/`key_facts` fields; those live on a promoted `Npc`/`BeliefState`). The projector targets the pool member, so the fields don't exist to project. Richer projection from a promoted `Npc` is a natural 75-6 follow-on. No code change.

- **AC-2 Faction "notable members/resources" not projected; `description` unused** (Missing in code — Cosmetic, **Trivial**)
  - Spec: AC-2 Faction → "goals, attitude toward party, **notable members/resources**".
  - Code: projects name/summary/disposition (summary≈goals, disposition≈attitude); omits members/resources and the `description` field.
  - Recommendation: **C (clarify spec)** — the `Faction` model (`genre/models/lore.py`) carries no structured members/resources (only an `extra=allow` bag); summary is the faithful projectable surface. No code change.

- **AC-7 says "telemetry hooks stubbed"; code defines names-only constants** (Different behavior — Cosmetic, **Trivial**)
  - Spec: AC-7 → "Telemetry hooks **stubbed** for per-type retrieval counts".
  - Code: defines attribute-name constants (`SPAN_*`, `UNIVERSAL_RETRIEVAL_SPAN_ATTRS`); no stub hooks.
  - Recommendation: **A (update spec)** — names-only is *more* correct than the AC's wording: the No-Stubbing principle forbids empty hook shells. The code did the right thing. Treat "stubbed" as "name-pinned, not emitted".

**Decision:** Proceed to review (verify next). No Option-B hand-back — every mismatch is Minor/Trivial with a defer/clarify/update resolution, and the one architectural item (requeue) is correctly deferred to the story that wires the live worker.

**Spec-check rework re-pass (after review reject):** Aligned — no new drift. Verified the 6 fail-loud guards are present (`EntityCard.new` unknown-type + blank-id raises, `_slug` blank-name raise, faction blank-segment filter, `update_embedding` empty-vector raise) and that they *tighten* the contract toward the No-Silent-Fallbacks `<critical>` rule rather than diverging from any AC. AC-4 still intact (grep confirms no `retrieve_turn_context`/`requeue_dimension_mismatched` logic — the deferred items were correctly NOT added). The earlier AC-7 "stubbed vs names-only" and AC-2 "goals/members" mismatches are unchanged (still Trivial, resolutions A/C stand). Proceed to verify.

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed (33/33), simplify applied, quality-pass clean.

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 4 (`entity_card.py`, `entity_store.py`, `test_entity_card.py`, `test_entity_store.py`)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | clean | 2 low-confidence notes (intentional reuse of `_estimate_tokens`/`cosine_similarity` confirmed correct; parallel test validation by design) — no action |
| simplify-quality | 3 findings | `total_tokens` property/method parity (high); 2× stale RED-phase test docstrings (high) |
| simplify-efficiency | clean | 1 low-confidence note (`UNIVERSAL_RETRIEVAL_SPAN_ATTRS` frozenset — correct, test-relied-upon) — no action |

**Applied:** 3 high-confidence fixes (commit `d38fb40`)
- `EntityStore.total_tokens`: `@property` → method, restoring call-convention parity with the sibling `LoreStore.total_tokens()` the ADR mandates mirroring; test call site updated.
- Removed now-inaccurate "RED-phase / module does not exist yet" docstrings from both test files (modules are live, tests GREEN).

**Flagged for Review:** 0 medium-confidence findings
**Noted:** 3 low-confidence observations (no action — all confirmed intentional)
**Reverted:** 0

**Overall:** simplify: applied 3 fixes

**Quality Checks:** ruff clean · ruff format clean · pyright 0 errors · 33/33 tests pass (regression check post-simplify).
**Handoff:** To Reviewer (The Merovingian) for code review.

### Verify Rework Re-pass (after review reject + Dev fixes)

Re-ran the 3-way simplify fan-out on the reworked diff (41 tests, +8 guard tests).
- **simplify-reuse: clean** · **simplify-efficiency: clean** (confirmed the new fail-loud guards are intentional defense-in-depth, not over-engineering — the `not in _ID_NAMESPACE` membership check + `[entity_type]` access gives a user-facing error before a bare `KeyError`; the projector-level blank guards layer over the model's `content` validator by design).
- **simplify-quality: 2 findings — 0 applied.**
  - *Dismissed (false positive):* "dead variable `type_str`" — `type_str` **is** used at `entity_card.py:147` (`entity_type=type_str`), and `ruff --select F841` passes clean. The agent misread the return.
  - *Noted (low/cosmetic, no action):* AC-section comment labels in `test_entity_store.py` run AC-7 before AC-6 — comment ordering only; the test names/docstrings are accurate.

**Applied:** 0 (clean re-pass). **Reverted:** 0.
**Quality Checks:** ruff clean · ruff format clean · pyright 0 errors · **41/41 tests pass**.
**Handoff:** To Reviewer (The Merovingian) for the review re-pass.

## Delivery Findings

<!-- Append-only. Never edit or remove another agent's entries. -->

### Dev (implementation)
- **Improvement** (non-blocking): `EntityStore` omits `LoreStore`'s `requeue_dimension_mismatched` and `mark_embedding_failed` — not required by any 75-4 AC and out of this foundation slice. When 75-5/75-6 wire the real daemon embedding worker (which can change vector dimension on model upgrade), the universal index will likely need the same dimension-mismatch requeue guard that lore has (and ADR-118 D5 names `retrieval.dimension_mismatch_count`). Affects `entity_store.py` (add the requeue/failure methods) and 75-5/75-6 wiring. *Found by Dev during implementation.*
- **Note** (non-blocking): the testing-runner subagent edited production source to fix a failing test (the `loc:` prefix) — outside its run-only remit. Caught and replaced with a clean fix during review; re-ran with an explicit read-only instruction. Affects the `testing-runner` helper's guardrails. *Found by Dev during implementation.*

### TEA (test design)
- **Gap** (non-blocking): `sm-setup` created the session file but skipped the standalone `sprint/context/context-story-75-4.md` that the context gate (`pf validate context-story`) and TEA on-activation require. Recovered during this RED phase (committed `57aa3eb`). Affects the `sm-setup` subagent (its setup should always emit the story-context doc, as it does for siblings like 75-2). *Found by TEA during test design.*
- **Improvement** (non-blocking): location entities have no single source class — they are diffuse across room graph / `world_materialization` / PG `location_promotions` (ADR-118 names this risk). The location projector therefore takes a **normalized view** (kwargs) rather than reading the three sources; the per-source adaptation belongs in the 75-5 consumer. Affects `entity_card.py::project_location_card` and 75-5's floor/fill assembly. *Found by TEA during test design.*
- No new upstream findings during test verification — the 3 simplify findings were high-confidence and resolved in-phase (commit `d38fb40`). *Found by TEA during test verification.*

### Reviewer (review)
- **Gap** (blocking-for-75-5, non-blocking-for-75-4): `EntityCard.content` is built from player-influenced fields (NPC/faction names, location descriptions via the Yes-And doctrine) and will reach the narrator prompt when 75-5 wires entity cards into the Valley zone. ADR-047's `sanitize_player_text` fires only at the player WebSocket boundary (`handlers/player_action.py`), not on narrator-context assembly — the existing `LoreFragment` path is unsanitized too, so this is not a 75-4 regression, but 75-4 *widens* the surface to live game state. **75-5 must apply sanitization at the prompt-assembly choke-point as an explicit AC** — do not assume "handled elsewhere." Affects `entity_card.py` projector outputs and 75-5's injection step. *Found by Reviewer during review.*
- **Note** (non-blocking): defense-in-depth hardening deferred — `EntityCard.id` has no character allowlist (a `location_id` with `:`/newline produces an ambiguous id) and `metadata: dict[str,str]` has no size bound. Both mirror the accepted `LoreFragment` posture (not a regression); fold into the prompt-injection hardening pass. *Found by Reviewer during review.*

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No deviations from spec. The location-projector normalized-view shape was already logged by TEA (below) and the tests encode it; implementation matches the test contract exactly. The `_ID_NAMESPACE` (`loc` abbreviation) implements ADR-118 D3's example ids and the AC-2 test assertion `loc:black_hart` — it satisfies spec rather than diverging from it.
- Rework 1 (review reject) introduced no new deviations — the fail-loud guards (`EntityCard.new`/`_slug` raises, faction blank-segment filter, `update_embedding` empty-vector guard) harden input boundaries toward the No-Silent-Fallbacks rule; they tighten the contract, they do not diverge from it.

### TEA (test design)
- **Location projector takes a normalized view, not the diffuse source structs**
  - Spec source: context-story-75-4.md (AC-2 Technical Guardrails — "diffuse location sources"); ADR-118 §D3 / §Consequences
  - Spec text: "the projector adapts per source, since locations are diffuse (room graph, materialization, PG promotion)"
  - Implementation: `project_location_card(*, location_id, name, description, mechanical_properties=None, linked_npcs=None)` projects from a normalized location view; per-source adaptation (reading room_graph / world_materialization / location_promotions) is deferred to the 75-5 consumer.
  - Rationale: no clean location source class exists (`room_graph.py` has no `Room` with name/description; no `PointOfInterest`). ADR-118 §Consequences explicitly permits a v1 that "ships NPCs + factions first and adds locations once the POI sources are consolidated." Keeping the foundation slice's projector source-agnostic avoids inventing a fake uniform source and keeps the card/projection contract clean. The card model and store fully support `entity_type="location"`, so nothing forecloses richer location projection later.
  - Severity: minor
  - Forward impact: 75-5 (floor/fill orchestration) must adapt the three diffuse location sources into the normalized view before calling `project_location_card`. Flagged in Delivery Findings.

### Reviewer (audit)
- **TEA "location normalized-view" deviation → ✓ ACCEPTED by Reviewer:** sound — no clean location source class exists and ADR-118 §Consequences explicitly permits NPCs+factions-first. The card model fully supports `entity_type="location"`, so nothing is foreclosed.
- **Dev "no deviations" → ✓ ACCEPTED by Reviewer:** the `_ID_NAMESPACE` `loc`-abbreviation implements ADR-118 D3's example ids and the AC-2 test contract — it satisfies spec, not diverges.
- **UNDOCUMENTED — input-boundary fail-loud gaps (Reviewer-surfaced):** the EntityCard `content` field fails loud on blank input (validator), but the *id-generation* (`_ID_NAMESPACE.get` fallback, `_slug("")`→`"npc:"`) and the *faction projector* (`" — ".join` without the blank-segment filter location uses) do **not** — they silently accept malformed input. This diverges from the project's No-Silent-Fallbacks `<critical>` rule and from the model's own content-validator precedent. Not logged by TEA/Dev. Severity: **High** (foundation layer; see Reviewer Assessment). → **✓ RESOLVED in rework `bd22c53`:** all boundaries now fail loud (`EntityCard.new` raises on unknown type / blank id, `_slug` on blank name, `update_embedding` on empty vector, faction projector filters blank segments). Verified round-2 review.

### Architect (reconcile)

Reviewed the TEA, Dev, and Reviewer deviation entries above — all accurate, all 6 fields present where required; the TEA "location normalized-view" entry is verified against ADR-118 §Consequences and the live `room_graph.py` (no `Room`/`PointOfInterest` source class). No AC was formally deferred in an AC-accountability table (all 7 were addressed; the divergences below are partial-coverage/forward-scope, not descopes), so the deferral-justification cross-check is a no-op. Three spec-vs-code divergences surfaced during spec-check were never logged as formal deviations — captured here, self-contained, for the audit:

- **AC-3 names "dimension-mismatch requeue" in the reuse list; `EntityStore` omits it**
  - Spec source: `.session/75-4-session.md`, AC-3 (Typed store generalization)
  - Spec text: "Reuse embedding worker, `cosine_similarity`, `query_by_similarity`, dimension-mismatch requeue, daemon MiniLM-L6-v2 path"
  - Implementation: `EntityStore` reuses `cosine_similarity` and the worker write-back contract but does **not** implement `requeue_dimension_mismatched` / `mark_embedding_failed` (the `LoreStore` dimension-mismatch guard).
  - Rationale: the requeue guard only bites when a *live* daemon changes embedding dimension on a model upgrade; 75-4 has no live embedding worker (embeddings are set only via `update_embedding` in tests), so the path cannot fire here. The matching span name `retrieval.dimension_mismatch_count` is already reserved in `UNIVERSAL_RETRIEVAL_SPAN_ATTRS`.
  - Severity: minor
  - Forward impact: **75-5/75-6** (which wire the daemon worker and per-turn retrieval) must add `requeue_dimension_mismatched` to `EntityStore` and call it before similarity queries, emitting `retrieval.dimension_mismatch_count`. Tracked as a Dev Delivery Finding.

- **AC-7 says telemetry hooks are "stubbed"; code defines name-only constants (no stubs)**
  - Spec source: `.session/75-4-session.md`, AC-7 (OTEL spans prepared)
  - Spec text: "Telemetry hooks stubbed for per-type retrieval counts (filled in by 75-5)"
  - Implementation: `entity_card.py` defines attribute-name constants (`SPAN_CARD_REPROJECT_COUNT`, `SPAN_STALE_CARD_COUNT`, `UNIVERSAL_RETRIEVAL_SPAN_ATTRS`) and emits/stubs nothing.
  - Rationale: the No-Stubbing `<critical>` rule forbids empty hook shells; names-only is the correct realization of "prepared but not emitted." The AC's "stubbed" wording predates that constraint — the spec should read "name-pinned, not emitted." Resolution **A (update spec)**.
  - Severity: trivial
  - Forward impact: none — 75-5/75-7 consume the same constant names when they emit.

- **AC-2 lists NPC "goals, key facts" and Faction "notable members/resources"; projectors omit them**
  - Spec source: `.session/75-4-session.md`, AC-2 (Per-type projectors)
  - Spec text: "NPC → name, role, pronouns, disposition tier, goals, key facts"; "Faction → goals, attitude toward party, notable members/resources"
  - Implementation: `project_npc_card` projects name/role/pronouns/attitude-band; `project_faction_card` projects name/summary/disposition. Neither projects goals/key-facts (NPC) or members/resources (faction).
  - Rationale: the source structs lack those fields — `NpcPoolMember` is identity-only (goals/beliefs live on a promoted `Npc`/`BeliefState`), and `Faction` (`genre/models/lore.py`) carries only `name`/`summary`/`description`/`disposition` (no structured members/resources). The projectors render the faithful projectable surface. Resolution **C (clarify spec)**. Richer NPC projection from a promoted `Npc` is a natural 75-6 follow-on.
  - Severity: trivial
  - Forward impact: minor — when 75-6 syncs promoted `Npc` state, the NPC projector can enrich content with goals/key-facts; no contract change required.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (1 flag: no prod consumer) | flag dismissed — AC-4 foundation-only; wiring test stands in |
| 2 | reviewer-edge-hunter | Yes | findings | 12 | confirmed 5, deferred 4, dismissed 3 |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 5 | confirmed 3, deferred 2 |
| 4 | reviewer-test-analyzer | Yes | findings | 11 | confirmed 4, deferred 0, dismissed 7 (low/noted) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | findings | 3 | confirmed 1 (deferred to 75-5), 2 deferred (defense-in-depth) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (5 enabled returned, 4 disabled pre-filled)
**Total findings:** 6 confirmed (2 High, 4 Medium), 6 deferred (documented forward), several dismissed/noted (LoreStore-parity or low)

## Reviewer Assessment

**Verdict:** APPROVED *(round 2 — rework verified; round-1 REJECTED resolved below)*

**Round 2 (rework re-review, commit `bd22c53`).** All 6 confirmed round-1 findings resolved — verified in the actual code, not the commit message:
- `[HIGH][SILENT]` `EntityCard.new` raises on unknown `entity_type` (no more `_ID_NAMESPACE.get` fallback) — entity_card.py:140
- `[HIGH][SILENT][EDGE]` `_slug` raises on blank name; `new` guards blank `entity_id` — entity_card.py:142,168
- `[MEDIUM][EDGE]` `project_faction_card` blank-segment filter (matches location projector) — entity_card.py:203
- `[MEDIUM][SILENT]` `update_embedding` raises on empty `[]` — entity_store.py:113
- `[MEDIUM][TEST]` `mechanical_properties` asserted in content + `None`-absent case — test_entity_card.py
- `[MEDIUM][TEST]` `match=` on every blank-rejection raise — test_entity_card.py

Plus recommended extras landed: determinism tests pin exact strings; a direct `EntityCard.new(EntityType.LOCATION, …)` test asserts the `loc:` id. **41/41 pass; ruff/format/pyright clean.** No new edge surface — the guards are minimal `if not x: raise`, and the 41 tests confirm no valid path broke. The deferred items (dimension-mismatch requeue → 75-5/75-6; `card.content` prompt-injection sanitization → explicit 75-5 AC) were correctly **not** added; their Delivery Findings stand. The round-1 Subagent Results table below is authoritative — the diff is unchanged except the prescribed guards, so no re-run was needed; the rework resolves exactly what the specialists flagged.

**Data flow traced:** projector input (`NpcPoolMember` / `Faction` / normalized location) → `EntityCard.content`+`id` → `EntityStore` index → `query_by_similarity`. Safe: every input boundary now fails loud (blank name/id/content/description, empty embedding, unknown type) — no silent degenerate cards or ids reach the index.
**Pattern observed:** fail-loud-at-the-boundary, now consistent across model (`content` validator), factory (`new`), projectors (`_slug`, description guard), and store (`update_embedding`). — entity_card.py / entity_store.py
**Error handling:** all malformed-input paths raise `ValueError` with specific messages; `DuplicateEntityId` / `KeyError` mirror `LoreStore`.
**Handoff:** To Architect for spec-reconcile, then SM for finish-story.

---

**Round 1 — REJECTED (superseded by round 2 above; retained for audit):**

The implementation is clean, well-structured, and a faithful reuse-first realization of ADR-118 §D1–D3 — preflight is green (33/33, ruff/pyright clean), the reuse mandate is honored, and AC-4 (no orchestration leak) holds. **But this is the *foundation* of the epic-75 waterfall (75-5→75-8 build directly on `EntityCard`/`EntityStore`), and two input boundaries silently accept malformed input in violation of the No-Silent-Fallbacks `<critical>` rule.** The model already establishes the right pattern (the `content` field fails loud on blank); the factory and projectors must match it. These are cheap to fix now and expensive to retrofit after four stories inherit the leaky boundary.

### Rule Compliance

Enumerated against the No-Silent-Fallbacks `<critical>` rule (CLAUDE.md ×2 + SOUL) and python.md lang-review:

| Rule | Instances checked | Verdict |
|------|-------------------|---------|
| **No Silent Fallbacks** — fail loud at the boundary closest to the mistake | `EntityCard.content` validator | ✅ complies (raises on blank) |
| **No Silent Fallbacks** | `EntityCard.new` id-namespace lookup (`_ID_NAMESPACE.get(entity_type, type_str)`) | ❌ **violation** — unknown type silently uses the full type string as namespace (entity_card.py:136) |
| **No Silent Fallbacks** | `_slug("")` → `""` → id `"npc:"`/`"faction:"` (project_npc_card / project_faction_card) | ❌ **violation** — blank name silently produces a degenerate namespaced id |
| **No Silent Fallbacks** | `project_location_card` blank description | ✅ complies (raises) |
| **No Silent Fallbacks** | `project_faction_card` segment assembly (`" — ".join(segments)` w/o blank filter) | ⚠️ partial — blank `summary` yields `"Name — "` that passes the content validator (entity_card.py:183) |
| **No Silent Fallbacks** | `EntityStore.update_embedding` empty `[]` | ⚠️ accepts empty vector → card stuck (entity_store.py:103) |
| **No Silent Fallbacks** | `EntityStore.add` duplicate id | ✅ complies (raises `DuplicateEntityId`) |
| python.md #6 test quality | blank-content/description raises | ⚠️ no `match=` (too broad) |
| python.md #6 test quality | `mechanical_properties` projection | ❌ **unverified** — passed but never asserted in content |
| python.md #8 unsafe deserialization | `model_validate_json` (×2) | ✅ complies (pydantic v2, `extra=forbid`) |
| python.md #3 type annotations at boundary | all public fns/`.new`/projectors | ✅ complies (pyright 0 errors) |
| Reuse-first (ADR-118 D3) | `_estimate_tokens`, `cosine_similarity` | ✅ complies (imported, test-asserted) |

### Observations

- `[HIGH][SILENT]` Silent namespace fallback — `_ID_NAMESPACE.get(entity_type, type_str)` returns a wrong-but-plausible namespace for any unknown `entity_type` instead of raising. Foundation factory; violates No-Silent-Fallbacks. — entity_card.py:136
- `[HIGH][SILENT][EDGE]` Blank/whitespace entity name silently yields degenerate id `"npc:"`/`"faction:"` (`_slug("")`→`""`, no guard); only surfaced later as a spurious `DuplicateEntityId`. — entity_card.py:152,166,181
- `[MEDIUM][EDGE]` `project_faction_card` omits the blank-segment `if seg` filter that `project_location_card` uses; a blank `Faction.summary` produces `"Name — "` content that passes the validator but embeds a degenerate vector. — entity_card.py:183
- `[MEDIUM][EDGE][SILENT]` `EntityStore.update_embedding([])` accepts an empty vector → card has non-`None` embedding, scores 0.0 forever, never re-queued. Reject empty. — entity_store.py:119
- `[MEDIUM][TEST]` `mechanical_properties` projection is unverified — `test_projects_name_description_and_mechanics` passes props but asserts only name/description (present regardless). — test_entity_card.py:195
- `[MEDIUM][TEST]` Blank-content/description raises use bare `pytest.raises(ValueError)` with no `match=` — they pass on any `ValueError` from anywhere in construction. — test_entity_card.py (blank tests)
- `[MEDIUM][SEC]` `EntityCard.content` is assembled from player-influenced fields and will reach the narrator prompt when 75-5 wires it; ADR-047 sanitization fires only at the player WS boundary. Not a 75-4 regression (mirrors the existing `LoreFragment` path) but **widens** the unsanitized surface — deferred to 75-5 as an explicit AC (see Delivery Findings). — entity_card.py:100
- `[LOW][SEC]` `EntityCard.id` has no character allowlist and `metadata` no size bound — defense-in-depth, mirrors accepted `LoreFragment` posture; deferred. — entity_card.py:95,106
- `[VERIFIED]` Reuse honored — `_estimate_tokens`/`cosine_similarity` imported from `lore_store`, not re-implemented; `test_new_computes_token_estimate_from_content` and `test_similarity_ranks_by_cosine` assert agreement. Complies with ADR-118 D3. — entity_card.py:25, entity_store.py:20
- `[VERIFIED]` Save-file round-trip safe — both models `extra=forbid`, all JSON-native fields; `model_validate_json` is pydantic-v2 safe (no pickle/yaml/eval). Complies python.md #8. — entity_store.py
- `[VERIFIED]` AC-4 honored — grep confirms no `retrieve_turn_context`/dirty-flag/Valley logic; only docstrings + the deferred span-name constant. Foundation-only scope intact.
- `[VERIFIED]` Duplicate-id loud-fail — `EntityStore.add` raises `DuplicateEntityId`, mirroring `DuplicateLoreId`; `test_duplicate_id_raises` confirms. — entity_store.py:42

### Devil's Advocate

Argue the code is broken. A confused content author adds a fourth `EntityType` (say `ITEM = "item"`) for a future story but forgets to extend `_ID_NAMESPACE` — there is no test and no runtime guard, so every item card is silently minted as `"item:sword"` while the author *believes* the namespace convention is centralized and enforced. Nothing tells them otherwise until a downstream id-split assumes a 3-way namespace and mis-routes. A malicious or careless player, under the Yes-And doctrine, names an NPC `"   "` (whitespace) or `""`; the pool accepts it (no `min_length`), `project_npc_card` slugs it to `""`, and the card is indexed under id `"npc:"`. The *second* such NPC raises `DuplicateEntityId` — so the failure manifests as a confusing "duplicate" error for two *differently-named* entities, sending a future debugger down the wrong path entirely. A stressed embedding worker (75-5/75-6) hands back an empty vector on a daemon hiccup; `update_embedding([])` happily clears the pending flag, and that card now scores 0.0 against every query forever, invisibly absent from retrieval with no `stale_card_count` signal — the narrator quietly "forgets" an NPC who is standing in the room, the exact *Living World* failure the floor was designed to prevent. A faction authored with an empty `summary` (valid YAML) embeds a near-useless vector that pollutes similarity ranking. And the test suite would catch *none* of this: `mechanical_properties` is passed but never asserted, so the entire mechanics-projection branch could be deleted and the suite stays green; the blank-input `raises` match any `ValueError`, so a regression that raises the *wrong* error for the *wrong* reason still passes. Individually small; collectively, a foundation that fails quiet where the whole project demands it fail loud. That is the case for rejection: fix the boundaries here, once, before four stories trust them.

### Deferred (documented, NOT part of this fix — correctly scoped forward)

- **Dimension-mismatch requeue / `expected_dim`** (edge + silent-failure, High *eventual* impact) — `EntityStore` omits `requeue_dimension_mismatched`. **Cannot fire in 75-4** (no live embedding worker; embeddings only set in tests). Correctly belongs to **75-5/75-6** where the daemon worker is wired (`retrieval.dimension_mismatch_count` already reserved in `UNIVERSAL_RETRIEVAL_SPAN_ATTRS`). Already logged as a Dev Delivery Finding — **do not** add it in this fix cycle.
- **Prompt-injection sanitization of `card.content`** (security, Medium) — content flows from player-influenced fields (Yes-And) and will reach the narrator prompt when 75-5 wires it; ADR-047 only sanitizes player WS input. Matches the existing un-sanitized `LoreFragment` path (not a 75-4 regression). **Must become an explicit 75-5 AC** (choke-point at prompt assembly), not an implicit "handled elsewhere." Logged as a Delivery Finding below.
- **`id` character allowlist + `metadata` size constraints** (security, Low) — defense-in-depth; both mirror the accepted `LoreFragment` posture (not a regression). Defer to a hardening pass alongside the prompt-injection work.

### Required fixes (blocking) — hand back to Dev

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | Silent namespace fallback for unknown `entity_type` | entity_card.py:136 | Replace `_ID_NAMESPACE.get(entity_type, type_str)` with a lookup that **raises** `ValueError(f"unknown entity_type: {entity_type!r}")` on a miss |
| [HIGH] | Blank/whitespace entity name → degenerate id `"npc:"`/`"faction:"` | entity_card.py `project_npc_card`/`project_faction_card` (`_slug`) | Guard blank name: raise `ValueError` (mirror the content-validator boundary). Add a test for the raise |
| [MEDIUM] | Faction projector omits blank-segment filter → degenerate content passes validator | entity_card.py:183 | Use `" — ".join(seg for seg in segments if seg)` (match `project_location_card`) and/or guard blank `summary` |
| [MEDIUM] | `update_embedding([])` accepts empty vector | entity_store.py:119 | Reject empty embedding: `if not embedding: raise ValueError(...)`; add a test |
| [MEDIUM] | `mechanical_properties` projection unverified | test_entity_card.py:195 | Assert the rendered property text appears in `content`; add a `None`-case |
| [MEDIUM] | Blank-input `raises` too broad | test_entity_card.py blank tests | Add `match=` pinning the validator message |

**Recommended while in there (non-blocking):** pin the exact expected string in `test_projection_is_deterministic` (stronger than `f(x)==f(x)`); add a direct `EntityCard.new(EntityType.LOCATION, ...)` assertion that the id is `loc:…`.

**Handoff:** Back to Dev (Agent Smith) for fixes. Do **not** add the deferred items (dimension requeue, prompt-injection sanitization) in this cycle — they are scoped to 75-5/75-6.