---
story_id: "75-6"
jira_key: "75-6"
epic: "epic-75"
workflow: "tdd"
---
# Story 75-6: Universal retrieval: card sync/reproject hook wired to 75-1 accretion trigger (ADR-118)

## Story Details
- **ID:** 75-6
- **Jira Key:** 75-6 (no Jira integration)
- **Workflow:** tdd
- **Stack Parent:** 75-4 (EntityCard model + projectors + typed store)
- **Epic:** RAG Retrieval Layer — Restore Accretion, Budgeted Selection, Universal Retrieval Design

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-01T18:31:36Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-01 | 2026-06-01T16:58:00Z | 16h 58m |
| red | 2026-06-01T16:58:00Z | 2026-06-01T18:02:38Z | 1h 4m |
| green | 2026-06-01T18:02:38Z | 2026-06-01T18:12:00Z | 9m 22s |
| spec-check | 2026-06-01T18:12:00Z | 2026-06-01T18:14:51Z | 2m 51s |
| verify | 2026-06-01T18:14:51Z | 2026-06-01T18:20:09Z | 5m 18s |
| review | 2026-06-01T18:20:09Z | 2026-06-01T18:29:59Z | 9m 50s |
| spec-reconcile | 2026-06-01T18:29:59Z | 2026-06-01T18:31:36Z | 1m 37s |
| finish | 2026-06-01T18:31:36Z | - | - |

## Sm Assessment

**Routing decision:** Selected 75-6 over the p1 lore stories (65-8/65-9) for **epic momentum** — 75-4 (EntityCard model + projectors) and 75-5 (retrieve_turn_context floor+fill) shipped in the last two commits, so the ADR-118 mental model is warm. The one-tier priority gap is outweighed by avoiding a cold context switch into the lore-render subsystem.

**Dependencies verified clear:** 75-1 (runtime lore accretion, merged), 75-2 (budgeted NPC floor, merged), 75-4 + 75-5 (merged). 75-6 is the next link — it closes the mutation loop so the universal-retrieval index stays fresh when entity state changes.

**Scope (this story):** Wire a dirty-flag → reproject → re-embed pipeline into the per-turn `accrete_for_turn()` path so mutated NPCs/locations/factions get fresh EntityCards. Emit `accretion.entity_sync` OTEL span so the GM panel can verify the index is being kept current. Out of scope: the floor (75-2), index storage (75-4), GM-panel surface (75-7), total-budget unification (75-7).

**Acceptance:** The story YAML carries no template ACs — the authoritative spec is the Implementation Contract + Test Design Guardrails below. TEA should derive the RED tests from those guardrails (reproject determinism, dirty-flag trigger, round-trip embedding, the next-turn wiring test, OTEL span emission, loud-failure on missing entity, zero-byte-leak on no-dirty).

**Doctrine watch:** No Silent Fallbacks — a non-projectable entity must fail loud with an OTEL failure span, never a stub card. Verify Wiring — `sync_entity_cards()` must be reachable from the production turn-build path, with at least one integration test proving it.

**Handoff:** TDD phased → TEA (RED phase). Branch `feat/75-6-universal-retrieval-card-sync` is live; work lands in `sidequest-server` (base: develop).

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (blocking): The session's Implementation Contract under-specifies two wiring facts a live code read surfaced. (1) `_SessionData.entity_store` is a `default_factory=EntityStore` that is **never populated** — `project_npc_card`/`project_faction_card`/`project_location_card` have zero production callers, so 75-5's `retrieve_turn_context` queries an empty store every turn today. 75-6's sync is therefore also the *first seeder*, not just a refresher. (2) The embed worker drains lore only — `lore_embed.dispatch_worker`/`run_worker` call `pending_embedding_ids`/`embed_pending_fragments` on `sd.lore_store`, never `sd.entity_store`. Reprojected cards stay `embedding_pending=True` forever and are invisible to `query_by_similarity` (which skips `embedding is None`). 75-6 MUST extend the drain (or add a sibling entity-embed dispatch). Affects `sidequest/server/dispatch/lore_embed.py` (or new `entity_embed` dispatch) and the turn seam in `websocket_session_handler.py:~1255`. *Found by TEA during test design.*
- **Question** (non-blocking): NPC sync source — the floor (75-5 `build_npc_working_set`) reads BOTH `snapshot.npcs` (stateful `Npc`) and `snapshot.npc_pool` (`NpcPoolMember`), but `project_npc_card` only accepts `NpcPoolMember`. RED tests pin the contract on `npc_pool` (deterministically projectable). Dev/Architect must decide whether stateful `snapshot.npcs` and faction/location sources are also synced in v1 (ADR-118 permits an NPC+faction-first v1 with location deferral logged). If stateful `Npc` is in scope, the projector needs a path for it. Affects `sidequest/game/entity_sync.py` + `sidequest/game/entity_card.py`. *Found by TEA during test design.*
- **Improvement** (non-blocking): On a content-changed upsert, the stale embedding vector remains searchable (with the old vector) until re-embedded, since the tests only assert `embedding_pending` re-arms — they do not assert the old embedding is nulled. If a stale vector surfacing for one turn is unacceptable, nulling `embedding` on content change is the stricter choice (at the cost of one turn unsearchable). Left as a Dev judgment call; flag for Reviewer. Affects `EntityStore.upsert` in `sidequest/game/entity_store.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): The production entity-embed drain (the `lore_embed.run_worker`/`dispatch_worker` extension that calls `embed_pending_entity_cards(sd.entity_store)`) has **no dedicated dispatch-level test**. `embed_pending_entity_cards` is unit-tested standalone (`test_synced_card_is_embeddable_and_then_retrievable`), and the two-turn integration test proves the *store content* refreshes — but neither proves the production worker actually embeds entity cards, because the daemon is unavailable in tests (the worker gracefully skips). A fixture-driven test injecting a fake daemon client into the dispatched worker would close this. Affects `tests/server/dispatch/test_lore_embed.py` (add an entity-drain case). *Found by Dev during implementation.*
- **Gap** (non-blocking): Only `snapshot.npc_pool` is synced. Stateful `snapshot.npcs` (`Npc`), factions, and locations are **not** projected into the store — so `query_by_similarity` can only ever return pool NPCs, not scene-stateful NPCs, factions, or locations. This matches the RED-test scope (TEA's Question finding) and ADR-118's permitted NPC-first v1, but the universal index is not yet "universal." Follow-up: extend `sync_entity_cards` to the other sources (needs a projector path for `Npc` and a faction/location source decision). Affects `sidequest/game/entity_sync.py` + `sidequest/game/entity_card.py`. *Found by Dev during implementation.*

### TEA (test verification)
- No additional upstream findings during test verification. Simplify pass (reuse/quality/efficiency) surfaced only two zero-risk improvements (both applied: per-type-counter docs, redundant-encode extraction); no new behavioral gaps. *Found by TEA during test verification.*

### Reviewer (code review)
- **Gap** (non-blocking, top follow-up): The `dispatch_worker` `if not pending and not entity_pending: return` gate has no dedicated regression test — a revert of the `entity_pending` clause would leave all 20 tests GREEN while silently breaking entity-only-turn embedding. Affects `tests/server/dispatch/test_entity_sync_dispatch.py` (add: seed a pool member, accrete no lore, call `lore_embed.dispatch_worker`, assert `sd.embed_task is not None`). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Three test assertions are loose (python.md #6): `assert result.embedded >= 1` on a one-card fixture → `== 1`; the `any(ref.strip()=="" ...)` `failed_refs` guard → exact `== ['   ']`; the skipped-path watcher test omits `assert events[0][1]["op"] == "synced"`. Affects `tests/game/test_entity_sync.py`, `tests/server/dispatch/test_entity_sync_dispatch.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `embed_pending_entity_cards` does not replicate the lore worker's `expected_dim` guard, so a daemon model-dimension change mid-session could write a stale-dim vector. Self-heals via `EntityStore.requeue_dimension_mismatched` (every retrieval turn), but parity is cleaner. Affects `sidequest/game/entity_embedding.py` + `EntityStore.update_embedding`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `logger.warning(..., exc)` in the embed text-too-large branch logs the exception object; safe today (daemon byte-cap message carries no content) but a future content-bearing `ValueError` would leak to logs — log `type(exc).__name__` only (apply to the lore sibling too). Affects `sidequest/game/entity_embedding.py`, `sidequest/game/lore_embedding.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `dispatch_worker` passes lore-only `len(pending)` as `pending_count`, so the lore `completed` watcher event reports `pending_at_dispatch=0` on entity-only-pending turns (the `entity_embedding.completed` event carries the real counts). Affects `sidequest/server/dispatch/lore_embed.py`. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Embed-drain entry named `embed_pending_entity_cards`**
  - Spec source: .session/75-6-session.md, Implementation Contract §"Re-embed" / context-story-75-6.md, Technical Guardrails
  - Spec text: "Write the card to EntityStore with embedding_pending=True, joining the daemon's embedding queue (same mechanism as lore)."
  - Implementation: The read-back test imports a concrete `sidequest.game.entity_embedding.embed_pending_entity_cards(store, *, client=...)`, mirroring `lore_embedding.embed_pending_fragments`. The spec named the *mechanism* but not the symbol.
  - Rationale: A RED test must import a concrete callable. Chose the idiomatic lore-sibling name. Dev MAY generalize `embed_pending_fragments` to both stores instead, but must keep this symbol importable (alias) or update the test with a follow-up deviation.
  - Severity: minor
  - Forward impact: Dev owns the final embed-drain shape; one test couples to the name.
- **NPC sync source scoped to `npc_pool` in tests**
  - Spec source: context-story-75-6.md, AC Context (AC-1) + Assumptions
  - Spec text: "collects the turn's projectable entities (NPCs from npc_pool, factions from world state, locations from the normalized source 75-5 reads)"
  - Implementation: RED tests exercise only `snapshot.npc_pool` (NpcPoolMember). Stateful `snapshot.npcs`, factions, and locations are NOT asserted — raised as a Delivery Findings Question instead.
  - Rationale: `project_npc_card` only accepts `NpcPoolMember`; faction/location sources are a dev decision. Encoding a guess as a test would create false RED. Testing the precisely-pinnable contract + flagging the open question is the disciplined split.
  - Severity: minor
  - Forward impact: Dev must decide multi-source coverage; tests assert NPC-pool baseline + per-type counts that *allow* (don't require) factions/locations.
- **Observability asserted via watcher event, not a raw OTEL span exporter**
  - Spec source: SOUL "OTEL Observability Principle" / session Implementation Contract §OTEL Spans (`accretion.entity_sync`)
  - Spec text: "Emit OTEL span: accretion.entity_sync with counts ... the GM panel can verify sync fired."
  - Implementation: Tests assert the `_watcher_publish` state_transition event (field=`entity_sync`, carrying reprojected count + outcome), mirroring `test_lore_accretion_dispatch.py`, rather than installing an in-memory span exporter and asserting span attributes.
  - Rationale: The full parallel server suite has a known OTEL span-count deadlock (project memory); the lore sibling proves observability through the watcher stream. Dev still emits the `accretion.entity_sync` span (the watcher event is the test-observable proxy).
  - Severity: minor
  - Forward impact: Reviewer should confirm the actual OTEL span is emitted alongside the watcher event (the test only pins the watcher).
- **Watcher contract pinned: field=`entity_sync`, component=`retrieval`**
  - Spec source: ADR-090 (`accretion.*` span family) / session §OTEL Spans
  - Spec text: span name `accretion.entity_sync`; component/field not specified for the watcher event.
  - Implementation: Tests require watcher `field="entity_sync"` and `component="retrieval"` (lore used `component="lore"`).
  - Rationale: GM-panel grouping needs a stable component; `retrieval` matches the ADR-118 universal-retrieval layer. Dev may rename with a logged deviation + test update.
  - Severity: minor
  - Forward impact: GM-panel filter keys on these strings.

### Dev (implementation)
- **Production embed-drain via extending `lore_embed`, not a sibling dispatch**
  - Spec source: context-story-75-6.md, Scope Boundaries (In scope)
  - Spec text: "Extending the embed-worker drain (`lore_embed`) to also drain `sd.entity_store` ... OR a sibling entity-embed dispatch"
  - Implementation: Chose the extension. `run_worker` now drains lore then entities (`embed_pending_entity_cards`); `dispatch_worker`'s gate fires when EITHER store has pending cards. The lore path is byte-identical before the new entity block.
  - Rationale: Reuses the existing fire-and-forget task slot (`sd.embed_task`) + double-dispatch gate; a sibling dispatch would need a new `_SessionData` task field + cleanup handling for no behavioral gain. Lower surface, isolated failure (entity drain wrapped separately so it cannot drop lore telemetry).
  - Severity: minor
  - Forward impact: One shared worker drains both stores; a future per-store concurrency split would need to re-separate them.
- **NPC sync source limited to `snapshot.npc_pool`**
  - Spec source: context-story-75-6.md, Scope Boundaries (In scope) — "NPCs from `npc_pool`, factions from world state, locations from the normalized source"
  - Spec text: lists factions + locations as sync sources alongside npc_pool.
  - Implementation: `sync_entity_cards` projects only `snapshot.npc_pool`. Stateful `snapshot.npcs`, factions, and locations are not synced.
  - Rationale: TEA's RED tests pin only the npc_pool contract (the only deterministically-projectable source — `project_npc_card` takes `NpcPoolMember`; faction/location sources are an open decision raised as TEA's Question finding). Implementing the minimal tested contract; broader sources are a logged follow-up (ADR-118 permits NPC-first v1).
  - Severity: minor
  - Forward impact: The universal index holds pool NPCs only until a follow-up extends sources — captured as a Dev Delivery Finding.
- **Stale-vector-on-change left searchable (TEA Improvement finding resolved as: keep)**
  - Spec source: Delivery Findings → TEA Improvement (non-blocking)
  - Spec text: "nulling `embedding` on content change is the stricter choice (at the cost of one turn unsearchable)"
  - Implementation: `upsert` re-arms `embedding_pending=True` but does NOT null the old embedding; the card stays searchable with its prior vector for the one turn until the worker re-embeds.
  - Rationale: A one-turn-stale vector (still semantically close — same NPC, shifted attitude band) is strictly better for retrieval than one turn of total invisibility. The re-embed lands next turn. Minimal change, matches the tests (which assert the re-arm, not a null).
  - Severity: minor
  - Forward impact: If a content change can be drastic enough that the stale vector misleads retrieval, revisit; flagged for Reviewer.

### Reviewer (audit)

All seven logged deviations audited — every one ACCEPTED:

- **TEA — `embed_pending_entity_cards` symbol name** → ✓ ACCEPTED: idiomatic lore-sibling name; Dev implemented it as specified. No divergence.
- **TEA — NPC sync scoped to `npc_pool` in tests** → ✓ ACCEPTED: only deterministically-projectable source; ADR-118 permits NPC-first v1. Source coverage recorded as a follow-up.
- **TEA — observability via watcher event, not raw OTEL span exporter** → ✓ ACCEPTED: mirrors `test_lore_accretion_dispatch.py`; avoids the known OTEL-deadlock; the production span IS still emitted by `sync_for_turn`.
- **TEA — watcher contract `field=entity_sync`, `component=retrieval`** → ✓ ACCEPTED: stable GM-panel grouping; `retrieval` correctly names the ADR-118 layer.
- **Dev — production embed-drain via extending `lore_embed` (not a sibling dispatch)** → ✓ ACCEPTED: lower surface, reuses the existing task slot + double-dispatch gate; lore path is byte-identical before the new entity block. (The untested `entity_pending` gate that this introduces is recorded as the top non-blocking follow-up.)
- **Dev — NPC sync source limited to `snapshot.npc_pool`** → ✓ ACCEPTED: agrees with TEA's test scope + ADR-118 NPC-first v1; the universal index is "NPC-only" until the logged follow-up.
- **Dev — stale embedding kept searchable on content change (TEA Improvement resolved as keep)** → ✓ ACCEPTED: a one-turn-stale same-NPC vector beats one turn of invisibility; sound, re-embed lands next turn.

**Undocumented deviations found:** None. The edge/silent/security findings are latent telemetry/robustness nits (all sibling-consistent), not spec divergences. Every spec deviation is explicitly accounted for.

### Architect (reconcile)

**Manifest review.** Audited all 7 logged deviations (4 TEA + 3 Dev) against the canonical spec sources — both exist and are accurately quoted:
- `sprint/context/context-story-75-6.md` (16.9 KB, recovered during RED) — the test-strategy spec.
- `.session/75-6-session.md` Implementation Contract — the higher-authority spec.
Each entry has all 6 fields, a real spec-source path, an implementation description matching the shipped code, and an accurate forward-impact. No field gaps, no inaccurate quotes.

**Forward-impact for sibling stories (the load-bearing item):** the **source-coverage deviation** (sync covers `snapshot.npc_pool` only; stateful `Npc`, factions, and locations deferred) is the one with real downstream reach. It is logged twice (TEA Question + Dev Gap + Dev deviation) and is consistent with ADR-118's permitted NPC-first v1. **75-7** (OTEL/GM-panel surface) and **75-8** (e2e) must treat the universal index as *NPC-only* until a follow-up wires the remaining sources — the `entity_sync.{location,faction}_count` span attributes will read 0 until then (documented, stable schema). This is the single deviation a downstream author must not miss.

**AC deferral verification:** No-op — the story carried no template ACs and no formal AC accountability/deferral table; all 10 derived AC obligations (context §AC Context) were implemented and tested. The Reviewer's 5 follow-ups are **Delivery Findings** (Improvements/coverage), not spec deviations, and are correctly filed there — none belongs in this manifest.

**No additional deviations found.** The manifest is complete and definitive.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Net-new behavior (mutation-loop reproject + store upsert + embed drain + turn wiring) — not a chore bypass.

**Test Files:**
- `tests/game/test_entity_sync.py` — 12 unit tests: `EntityStore.upsert` (insert/no-op/replace+rearm/no-DuplicateEntityId), `sync_entity_cards` (empty-store seed, skip-on-unchanged, reproject-only-mutated, within-band no-op, loud-failure-no-stub, empty/idempotent), and the embed read-back via `embed_pending_entity_cards`.
- `tests/server/dispatch/test_entity_sync_dispatch.py` — 8 wiring tests: `sync_for_turn` projects pool→store, watcher observability (field/outcome/component), handler delegate guard, **real-turn production wiring** (empty→populated), **two-turn refresh** of a band-crossing mutation, no-dirty skip, and failure isolation.

**Tests Written:** 20 tests covering the 10 derived AC obligations (context-story-75-6.md §AC Context) + 5 paranoia cases.
**Status:** RED (20 failed, 0 passed, clean missing-implementation — verified by testing-runner, RUN_ID `75-6-tea-red`). No collection errors, no fixture mismatches.

### Rule Coverage

| Rule (python.md) | Test(s) | Status |
|------------------|---------|--------|
| #1 Silent exception swallowing | `test_sync_for_turn_does_not_propagate_exception` (failure isolated + surfaced as `op="failed"`, not silently swallowed) | failing |
| #6 Test quality (meaningful assertions) | All — assert content/pending-flag/store-membership/outcome values, never bare truthiness; self-check pass below | failing |
| SOUL: No Silent Fallbacks | `test_unprojectable_entity_fails_loud_no_stub_card` (failed count + `outcome="partial"`, NO stub card) | failing |
| SOUL: OTEL lie-detector | `test_sync_for_turn_emits_watcher_event` (reprojected count + outcome observable) | failing |
| ADR-118 §D2 determinism / no churn | `test_within_band_wiggle_does_not_rearm`, `test_resync_unchanged_roster_is_a_clean_skip` | failing |
| Project doctrine: wiring test mandatory | `test_narration_turn_syncs_entity_cards`, `test_second_turn_refreshes_mutated_card` (reachable from `_execute_narration_turn`) | failing |

**Rules checked:** Applicable lang-review rules (#1 exception handling, #6 test quality) + SOUL (No Silent Fallbacks, OTEL) + ADR-118 §D2 have test coverage. Rules #2–#5, #7, #8 (mutable defaults, type-annotation gaps, path handling, resource leaks, unsafe deserialization) are not exercised by this story's surface — no file I/O, no deserialization, no mutable-default-prone signatures introduced by the tests; they apply to the *implementation* and are the Dev/Reviewer self-check.
**Self-check:** 0 vacuous tests. Every test asserts a concrete value (card content, `embedding_pending` state, store membership, watcher payload fields, result counts/outcome). No `assert True`, no bare truthiness, no `is None` on always-None.

**Handoff:** To Agent Smith (Dev) for implementation. Implement (in dependency order): `EntityStore.upsert` → `sidequest/game/entity_sync.py` (`sync_entity_cards` + `EntitySyncResult`) → `sidequest/game/entity_embedding.py` (`embed_pending_entity_cards`) → `sidequest/server/dispatch/entity_sync.py` (`sync_for_turn`) + extend the embed-worker drain → wire `_sync_entity_cards_for_turn` into `_execute_narration_turn` between accretion (`:1255`) and the embed dispatch (`:1260`). **Read the two blocking Delivery Findings first** — the store is unseeded today and the embed worker does not drain entities; both are 75-6's job.

## Dev Assessment

**Implementation Complete:** Yes — all 20 RED tests now GREEN, both blocking TEA findings addressed.

**Files Changed:**
- `sidequest/game/entity_store.py` — added `upsert` (reproject-safe insert/no-op/replace+rearm) + `mark_embedding_failed`.
- `sidequest/game/entity_sync.py` *(new)* — `sync_entity_cards` sweep + `EntitySyncResult` (counts + derived `outcome`); loud failure on unprojectable entity, no stub card.
- `sidequest/game/entity_embedding.py` *(new)* — `embed_pending_entity_cards`, the entity-store drain (sibling of `embed_pending_fragments`, shares `EmbedWorkerResult`, graceful daemon-skip).
- `sidequest/server/dispatch/entity_sync.py` *(new)* — `sync_for_turn`: emits `accretion.entity_sync` span + `entity_sync` watcher event (component=`retrieval`); failure isolated/swallowed.
- `sidequest/server/dispatch/lore_embed.py` — `run_worker` now drains the entity store after lore (isolated try/except, own `entity_embedding` watcher event); `dispatch_worker` gate fires when either store has pending cards.
- `sidequest/server/websocket_session_handler.py` — added `_sync_entity_cards_for_turn` delegate; wired it into `_execute_narration_turn` between lore accretion (`:1255`) and the embed dispatch.

**Both blocking TEA findings resolved:** (1) store is now seeded — `sync_for_turn` runs every turn from the production path; (2) the embed worker now drains `sd.entity_store`, so reprojected cards become similarity-searchable.

**Tests:** 74/74 passing (20 new + 54 regression across entity_store, entity_card, lore_embed, lore_accretion). pyright 0 errors; ruff clean; retrieval_orchestration consumer suite 19/19.
**Branch:** `feat/75-6-universal-retrieval-card-sync` (pushed to origin).

**Handoff:** To verify phase (The Architect — simplify + quality-pass). Two non-blocking Dev findings flagged for verify/review: the production entity-embed drain lacks a fake-daemon dispatch test, and only `npc_pool` is synced (factions/locations/stateful NPCs are a follow-up).

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned (with logged, justified deviations)
**Mismatches Found:** 3 — all pre-logged by TEA/Dev; none blocking.

**AC coverage:** All 10 derived AC obligations (context-story-75-6.md §AC Context) are implemented and covered by the 20 GREEN tests — verified one-to-one. The named deliverable ("card sync/reproject hook wired to the 75-1 accretion trigger") is present and correctly seated: `_sync_entity_cards_for_turn` fires from `_execute_narration_turn` between lore accretion and the embed dispatch.

**Architectural soundness:** Reuse-first, as the design demanded. Reproject reuses the live `project_npc_card`, the `EmbedWorkerResult` telemetry type, the daemon MiniLM/cosine path, and `EntityStore`'s existing worker contract — zero new infrastructure invented. The `upsert` content-equality dirty-key correctly leverages the projection determinism 75-4 guarantees (a band change reprojects different content → re-arm; a within-band int wiggle projects identical content → no churn). The embed-worker extension reuses the existing fire-and-forget task slot + double-dispatch gate rather than forking a parallel worker. **The seam is correct and generalizes**: adding faction/location/stateful-NPC sources later is a loop extension in `sync_entity_cards`, not a redesign.

**Mismatches:**
- **Source coverage is NPC-pool-only** (Missing in code — Behavioral, Major)
  - Spec: context §Scope "In scope" lists NPCs from `npc_pool`, factions from world state, locations from the normalized source.
  - Code: `sync_entity_cards` iterates `snapshot.npc_pool` only; `EntitySyncResult.faction_count`/`location_count` are present but always 0.
  - Recommendation: **D — Defer.** ADR-118 §D2 explicitly permits an NPC-first v1 with deferral logged, and TEA scoped the RED tests to `npc_pool` (the only deterministically-projectable source; faction/location runtime sources are an open decision). Adding untested source coverage now would violate TDD. The index is functionally "NPC-only" until a follow-up — a real *Living World* caveat worth surfacing to 75-7/75-8 planning, but the mechanism is complete. Logged by both TEA (Question) and Dev (Gap + deviation).
- **Production entity-embed drain lacks a dispatch-level test** (Extra in code — Behavioral, Minor)
  - Spec: context §In scope requires the embed worker to drain `entity_store`.
  - Code: `lore_embed.run_worker`/`dispatch_worker` now drain `sd.entity_store`; `embed_pending_entity_cards` is unit-tested standalone, but the *production* drain wiring has no fake-daemon dispatch test (daemon is unavailable in tests → worker skips).
  - Recommendation: **D — Defer to verify/review.** Belongs to TEA's verify phase or a follow-up: a fixture-injected fake daemon client through the dispatched worker closes it. Logged by Dev.
- **Stale embedding kept searchable on content change** (Ambiguous spec → assumption — Behavioral, Minor)
  - Spec: TEA Improvement flagged nulling the embedding as the stricter option.
  - Code: `upsert` re-arms `embedding_pending` but keeps the prior vector for the one turn until re-embed.
  - Recommendation: **C — Accept.** A one-turn-stale same-NPC vector (attitude band shifted) is strictly better for retrieval than one turn of invisibility; re-embed lands next turn. Sound assumption, logged by Dev.

**Decision:** Proceed to review (verify phase). No code hand-back — all three deltas are non-blocking, logged, and architecturally justified.

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed (20/20 after simplify; ruff + pyright clean)

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 6 (entity_store.py, entity_sync.py, entity_embedding.py, dispatch/entity_sync.py, lore_embed.py, websocket_session_handler.py)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | clean | The lore-sibling parallelism (entity_sync↔lore_accretion, entity_embedding↔lore_embedding) is load-bearing per ADR-118 §D3; error-isolation blocks are doctrine-required (No Silent Fallbacks). No extractable duplication. |
| simplify-quality | 2 findings (medium) | `EntitySyncResult.location_count`/`faction_count` always 0 and undocumented — ambiguous between scaffolding and dead code (No-Stubbing). |
| simplify-efficiency | 1 finding (medium) | `len(card.content.encode("utf-8"))` computed twice in `entity_embedding.py`'s text-too-large handler. |

**Applied:** 2 fixes (both medium-confidence but zero-behavioral-risk, so applied rather than deferred):
1. `entity_sync.py` — documented the three per-type counters in `EntitySyncResult`: `location_count`/`faction_count` are honest **zero** reproject measurements (NPC-first v1; faction/location sync deferred per logged deviation), present so the `entity_sync.{npc,location,faction}_count` span schema stays stable across the follow-up. Reframes them as true zero-counts, not stubs — resolving the No-Stubbing concern.
2. `entity_embedding.py` — extracted `content_bytes` local in the text-too-large handler (was computed twice).

**Flagged for Review:** 0 medium findings left open (both resolved by documentation/extraction).
**Noted:** 0 low-confidence observations.
**Reverted:** 0.

**Overall:** simplify: applied 2 fixes

**Quality Checks:** ruff (check + format) clean; pyright 0 errors; targeted suite 20/20 GREEN (RUN_ID `75-6-tea-verify`). No regression from the simplify edits.
**Handoff:** To The Merovingian (Reviewer) for code review.

### Delivery Findings Capture

- No additional upstream findings during test verification. (The two non-blocking Dev findings — the production entity-embed drain's missing fake-daemon dispatch test, and NPC-pool-only source coverage — stand for Reviewer's attention; the simplify pass surfaced nothing new.)

---

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (20/20 GREEN, ruff/format/pyright clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 11 (1 withdrawn) | confirmed 0 blocking, 9 LOW/non-blocking, dismissed 1 |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 4 | confirmed 0 blocking (4 LOW, all sibling-consistent) |
| 4 | reviewer-test-analyzer | Yes | findings | 6 (1 confirmed-clean) | confirmed 4 non-blocking (1 strong follow-up + 3 assertion-tightenings), 1 clean |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | findings | 1 (LOW) | confirmed 1 non-blocking; ADR-047 sanitization boundary VERIFIED intact |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (5 enabled returned, 4 disabled)
**Total findings:** 0 confirmed blocking, ~15 confirmed non-blocking, 1 dismissed (with rationale)

## Reviewer Analysis

### Rule Compliance

Enumerated the changed code against every applicable project rule (CLAUDE.md `<critical>` rules, SOUL.md, server CLAUDE.md, python.md lang-review):

- **No Silent Fallbacks** — `sync_entity_cards` catches `(ValueError, ValidationError)` *specifically* (not bare), counts the failure, records `failed_refs`, logs WARNING, and surfaces `outcome="partial"`. `sync_for_turn`'s `except Exception` is turn-isolation (mirrors `accrete_for_turn`) with a loud `op="failed"` watcher + `logger.exception`. Embed-loop failures each log + mark + (span event or break). **COMPLIANT** — every failure path is observable.
- **No Stubbing / dead code** — `location_count`/`faction_count` are honest zero measurements (documented in the verify pass), not stubs. **COMPLIANT.**
- **OTEL Observability** — `sync_for_turn` emits `accretion.entity_sync` span + `entity_sync` watcher event with reproject/unchanged/failed counts + outcome; embed worker emits `entity_embedding` watcher. The GM-panel lie-detector can see every sync decision. **COMPLIANT** (one LOW nit: failure path emits watcher-only, no span — watcher satisfies the principle).
- **Verify Wiring / No half-wired features / Every Test Suite Needs a Wiring Test** — `_sync_entity_cards_for_turn` is called from `_execute_narration_turn:1262` (non-test consumer); two integration tests prove the sync path end-to-end (empty→populated, mutation refresh). The embed drain is wired in `lore_embed` and the embed function is unit-tested. **COMPLIANT at the suite level** — *but* the `dispatch_worker` `entity_pending` gate (the embed-dispatch wiring) lacks a dedicated regression test (see [TEST] finding — non-blocking per severity rubric, strong follow-up).
- **No Source-Text Wiring Tests** — test-analyzer confirmed all wiring guards are behavior/call-capture/state-inspection based; no source-text greps. **COMPLIANT.**
- **ADR-047 Prompt Injection Sanitization** — security VERIFIED 75-6 adds no path from `EntityStore` to the narrator prompt; `retrieve_turn_context._sanitize_card` remains the sole choke-point. Embedding sends content to the daemon for vectorization only (same trust boundary as lore). **COMPLIANT.**
- **python.md #1 (exception handling)** — specific catches, loud logging. **COMPLIANT.** **#6 (test quality)** — 3 assertions are loose (`>= 1` on a 1-card fixture; over-broad `failed_refs` guard; unasserted `op`) → confirmed non-blocking tightenings.

### Observations (evidence-cited)

1. `[VERIFIED]` Production wiring is real, not test-only — `_execute_narration_turn` (`websocket_session_handler.py:1262`) calls `self._sync_entity_cards_for_turn(sd)` → delegate at `:2999` → `entity_sync.sync_for_turn`. Between lore accretion and embed dispatch, exactly per spec.
2. `[VERIFIED]` `upsert` dirty-key is content-equality leveraging 75-4 projection determinism — `entity_store.py`: new→insert+True; content-equal→no-op+False (embedding preserved); content-changed→replace+rearm+True. Correct against all 4 upsert tests.
3. `[SEC][LOW]` `entity_embedding.py:~128` logs the `ValueError` object via `%s`; safe today (the only reachable `ValueError` is the daemon byte-cap message, no content), but a future content-bearing `ValueError` would leak. Mirrors lore. Defense-in-depth — recommend logging `type(exc).__name__` in both siblings (follow-up).
4. `[EDGE][MEDIUM→non-blocking]` `embed_pending_entity_cards` does not replicate the lore worker's `expected_dim` guard, so a daemon model-dim change mid-session could write a stale-dim vector. **Self-heals**: `EntityStore.requeue_dimension_mismatched` runs every retrieval turn (75-5), nulls + re-arms the mismatch next turn (worst case: one turn of a harmless 0.0-scoring card). Recommend mirroring `expected_dim` for parity (follow-up).
5. `[EDGE/SILENT][LOW]` retry_count telemetry reports the **post-increment** count (`mark_embedding_failed` is called before the read) — the two hunters disagreed on direction; actual is post-increment. Mirrors `lore_embedding.py` exactly; "retry_count=N after N failures" is defensible. Fixing only entity would diverge the siblings. Non-blocking.
6. `[EDGE][LOW]` `mark_embedding_failed` bare `self.cards[card_id]` could `KeyError` if a card were evicted mid-worker — but **no removal path exists** on `EntityStore` (`upsert` replaces, never deletes); unreachable. Mirrors lore.
7. `[EDGE][LOW]` `dispatch_worker` passes lore-only `len(pending)` as `pending_count`; on entity-only-pending turns the lore `completed` event shows `pending_at_dispatch=0` (the `entity_embedding.completed` event carries the real counts). Cosmetic telemetry imprecision — I flagged this independently too.
8. `[TEST][non-blocking, strong follow-up]` The `dispatch_worker` `if not pending and not entity_pending: return` gate has no dedicated test — a revert of the `entity_pending` clause would leave all 20 tests green while silently breaking entity-only-turn embedding. Precise cheap fix exists (seed pool member, no lore, call `dispatch_worker`, assert `sd.embed_task is not None`). Classified Medium (missing edge case) per the severity table — see verdict reasoning.

### Devil's Advocate

Argue this code is broken. **The embed-dispatch gate is the soft underbelly.** The whole story exists to keep the retrieval index fresh, yet the one line that makes an *entity-only* turn embed (`not pending and not entity_pending`) is untested — a careless refactor reverts it to `if not pending: return` and entity embedding silently dies for any turn that reprojects a cast change without discovering a lore fact (a *common* case: an NPC's disposition shifts during pure dialogue). Retrieval would then serve stale or unembedded cards forever, and the narrator would lose cast awareness — exactly the *Living World* failure 75-6 was meant to prevent — with zero test or alarm. **The dimension race is the second soft spot:** a malicious or unlucky daemon model swap mid-session lets the entity worker write a wrong-dim vector; only the every-turn `requeue_dimension_mismatched` saves it, and if a future change moved that requeue behind a condition, the self-heal evaporates and cards orphan. **A confused operator** reading the GM panel sees `lore_embedding.completed pending_at_dispatch=0 embedded=0` on an entity-only turn and concludes "the worker did nothing," missing that entity cards were the dispatch reason — a telemetry lie by omission. **A stressed input:** an NPC pool member whose `name` is somehow `None` (legacy import, untyped dict) raises `AttributeError` from `_slug`, which `sync_entity_cards`'s `(ValueError, ValidationError)` catch misses — it escapes to `sync_for_turn`'s broad guard, so the *whole* sweep is attributed as failed with no `failed_refs` entry pinpointing the culprit. **Verdict of the devil:** none of these corrupt state or crash a turn; each is either self-healing, unreachable given Pydantic typing, cosmetic, or a (real, cheap) missing regression guard. The strongest is the untested dispatch gate — which I am recording as the top follow-up, not a blocker, because the wiring itself is present and correct and the sync path *is* wiring-tested end-to-end.

## Reviewer Assessment

**Verdict:** APPROVED

**Subagent findings incorporated (tagged by source):**
- `[EDGE]` (edge-hunter) — dimension-guard parity gap (self-heals via every-turn requeue), `mark_embedding_failed` KeyError (unreachable — no eviction path), lore-only `pending_count` telemetry, `member.name=None` AttributeError (Pydantic-prevented). All confirmed non-blocking.
- `[SILENT]` (silent-failure-hunter) — retry_count post-increment telemetry (mirrors lore, defensible), card-dropped silent `continue` (no removal path), failure-path watcher-only-no-span (watcher satisfies the lie-detector), post-try `as_dict()` unguarded (mirrors lore). All confirmed non-blocking, every failure path observable.
- `[SEC]` (security) — ADR-047 sanitization boundary VERIFIED intact (no store→prompt path bypasses `_sanitize_card`); one LOW `logger.warning(..., exc)` defense-in-depth nit (safe today). No vulnerabilities.
- `[TEST]` (test-analyzer) — untested `dispatch_worker` `entity_pending` gate (top non-blocking follow-up), 3 loose assertions (python.md #6 tightenings), monkeypatch targets confirmed correct, no source-text wiring tests. Recorded as non-blocking follow-ups.

**Verdict reasoning (the rejection I weighed):** test-analyzer rated the untested `dispatch_worker` `entity_pending` gate HIGH/block-worthy, and the project's wiring-test culture is intense — I genuinely considered REJECT. I land on APPROVE because: (a) **no Critical/High *code* defect** exists — every High-rated subagent finding is, on analysis, unreachable (KeyError: no eviction path), self-healing (dim race: every-turn requeue), or sibling-consistent (retry_count semantics); (b) the project severity table classifies a **missing edge-case test as Medium (non-blocking)**, and the wiring-test `<critical>` rule is *satisfied at the suite level* — the sync path has two end-to-end integration tests and the new code has a real production consumer; (c) the code is correct, fully wired, lint/type/test green, and the ADR-047 security boundary is verified intact. The dispatch-gate regression test is a real, cheap, valuable add — recorded as the **top non-blocking follow-up** for TEA, not buried.

**Data flow traced:** player action → `_execute_narration_turn` → `_sync_entity_cards_for_turn` → `sync_entity_cards` projects `npc_pool` → `EntityStore.upsert` (dirty-keyed) → pending cards → `dispatch_worker` → `run_worker` → `embed_pending_entity_cards` → daemon vector → `update_embedding`. Prompt-bound exit is only `retrieve_turn_context`, which sanitizes (ADR-047). Safe.
**Pattern observed:** faithful lore-sibling mirroring (entity_sync↔lore_accretion, entity_embedding↔lore_embedding) — ADR-118 §D3 reuse mandate honored; `websocket_session_handler.py:1262`.
**Error handling:** loud + isolated throughout; turn survives every failure with an observable watcher event (`entity_sync.py`, `dispatch/entity_sync.py:~52`).

**Non-blocking follow-ups (recorded in Delivery Findings):**
| Severity | Item | Location | Recommendation |
|----------|------|----------|----------------|
| [MEDIUM] | `dispatch_worker` `entity_pending` gate untested — silent-revert risk | `tests/server/dispatch/` | TEA add: entity-only turn → `assert sd.embed_task is not None` |
| [LOW] | 3 loose test assertions (`>=1`→`==1`; exact `failed_refs`; assert `op`) | `tests/game/test_entity_sync.py`, `test_entity_sync_dispatch.py` | Tighten per python.md #6 |
| [LOW] | entity embed worker lacks `expected_dim` parity with lore | `entity_embedding.py` / `entity_store.update_embedding` | Mirror lore's dim guard (self-heals today via requeue) |
| [LOW] | `logger.warning(..., exc)` could leak future content-bearing ValueError | `entity_embedding.py` + lore sibling | Log `type(exc).__name__` only |
| [LOW] | lore `completed` telemetry shows `pending_at_dispatch=0` on entity-only turns | `lore_embed.py:192` | Add `entity_pending` to the event |

**Handoff:** To SM for finish-story.

---

## Technical Context

### Story Purpose

**Continuation of ADR-118 Universal Retrieval Layer.** 

75-4 and 75-5 built the foundation:
- **75-4:** EntityCard model + per-type projectors (NPC/location/faction) + typed store that generalizes the lore RAG machinery.
- **75-5:** retrieve_turn_context orchestration — floor (from 75-2 budgeted NPC selection) + fill (semantic top-k retrieval) under a per-turn token budget.

**75-6 closes the mutation loop.** Runtime facts are accreted into the lore RAG every turn (75-1, merged) via `accrete_for_turn`. NPCs, locations, and factions are now *indexed* via EntityCard (75-4/75-5), but the index is **static**. When a fact is discovered or an NPC's state mutates (e.g., disposition changes, location visited for the first time), the EntityCard must be **reprojected and re-embedded** so the narrator sees the updated cast, not a stale snapshot.

**The story wires the dirty-flag mutation trigger into the per-turn accretion pathway** — when lore is accreted, EntityCards for mentioned NPCs/locations also sync, reproject, and re-embed, keeping the index fresh.

### Dependency Chain

```
75-1 (merged) — runtime lore accretion + embedding
    ↓
75-2 (merged) — budgeted NPC floor selection
    ↓
75-4 (merged) — EntityCard + projectors + typed store
    ↓
75-5 (merged) — retrieve_turn_context orchestration
    ↓
75-6 (THIS) — card sync/reproject hook wired to 75-1 accretion trigger
    ↓
75-7 (future) — OTEL instrumentation + GM panel surface
    ↓
75-8 (future) — end-to-end integration test
```

### Key Concepts

- **Dirty-flag mutation:** When an entity's state changes (NPC disposition, location discovery, faction membership), a marker is set indicating the EntityCard must be recomputed.
- **Accretion trigger:** Every turn, 75-1 calls `accrete_for_turn`, which mints and embeds new lore fragments from discovered facts.
- **Reproject seam:** When accretion fires, 75-6 invokes the per-type projector (`to_card()`) on any entity that was mentioned or mutated that turn, producing a fresh EntityCard with updated content.
- **Re-embed:** The fresh card is written to the EntityStore with `embedding_pending=True`, joining the daemon's embedding queue (same mechanism as lore).
- **Round-trip:** On save/load, newly embedded cards (both lore and entity) preserve their embeddings so replay doesn't re-embed.

### Acceptance Criteria (from epic YAML)

The story YAML lists no explicit acceptance criteria in the template form. **The technical spec lives in the session file itself, below.**

### Out of Scope (Per 75-5 Context)

- The floor itself (75-2) — already merged.
- Retrieval index storage (75-4) — already merged.
- OTEL GM-panel surface (75-7).
- Per-turn *total* budget unification (lore + entities) — 75-7 follow-up.

## Implementation Contract

### Wiring Points

1. **Accretion trigger entry:** `accrete_for_turn()` in `sidequest/game/lore_accretion.py` (or equivalent post-75-1 module).
   - Already calls `embed_pending_fragments()` to queue lore for the daemon.
   - **Add:** after lore accretion completes, invoke the entity-sync pipeline.

2. **Dirty-flag collection:** Identify which entities (NPCs, locations, factions) were touched this turn.
   - Source: facts discovered (`fact.subject` / `fact.object` may reference an NPC or location).
   - Source: state mutations (disposition changes, location visits, etc.) that set dirty flags.
   - **Contract:** A function `collect_dirty_entities(turn_context, discovered_facts)` returns a set of entity refs (npc IDs, location IDs, faction IDs) that need reproject.

3. **Reproject seam:** For each dirty entity, call its projector and generate a fresh EntityCard.
   - **Contract:** A function `sync_entity_cards(dirty_entities, game_state)` that:
     - For each entity ID, look up the current state (from `npc_pool`, `location_graph`, `faction_registry`, etc.).
     - Call the appropriate `to_card()` projector.
     - Write the card to `EntityStore` with `embedding_pending=True`.
     - **Emit OTEL span:** `accretion.entity_sync` with counts of reprojected NPCs/locations/factions.
   - **Loud failure:** If an entity cannot be projected (state not found, projector raises), log and emit OTEL failure, do NOT silently skip.

4. **Integration with 75-1 accretion:** The `accrete_for_turn()` call in the turn-build path invokes both:
   - `embed_pending_fragments()` (lore, 75-1).
   - `sync_entity_cards()` (entities, 75-6).
   - Both operate on the same `game_state` snapshot, so mutations are coherent.

### Test Design Guardrails

- **Reproject determinism:** Calling `to_card()` twice on unchanged entity state yields identical cards (same embedding hash).
- **Dirty-flag reproject:** An entity with a dirty flag set triggers reproject; one without does not.
- **Round-trip embedding:** Cards reprojected this turn are persisted with their embeddings; on load, they round-trip unchanged (no re-embed on replay).
- **Wiring test:** A turn is played; a fact is discovered that mentions an NPC; the NPC's EntityCard is queried at the start of the next turn; the old card (from 75-4 seeding) is gone, the new card (with updated content from this turn's reproject) is retrievable.
- **OTEL span fires:** `accretion.entity_sync` is emitted with entity counts; the GM panel can verify sync fired.
- **Loud failure:** If a referenced NPC is not in `npc_pool` (corrupted state), the sync pipeline logs a detailed error, does NOT silently emit a stub card.
- **Zero-byte-leak:** If no entities are dirty this turn, `sync_entity_cards()` is not called; no empty batch is written.

### OTEL Spans

Per ADR-118 and the project observability principle, **every subsystem decision must be observable**.

**Span: `accretion.entity_sync`**
- **When:** Emitted once per turn, after `embed_pending_fragments()` (lore).
- **Attributes:**
  - `entity_sync.npc_count` — number of NPCs reprojected.
  - `entity_sync.location_count` — number of locations reprojected.
  - `entity_sync.faction_count` — number of factions reprojected.
  - `entity_sync.total_count` — sum of the above.
  - `entity_sync.outcome` — `"success"`, `"partial"` (some entities failed to project), or `"skipped"` (no dirty entities).
  - `entity_sync.failed_projections` — count of entities that failed to project (and were logged).
  - If `outcome` is `"partial"` or failure flags are set, include a `error_log` attribute with a short summary.

### SOUL / Doctrine Alignment

- **No Silent Fallbacks:** If an entity cannot be projected, fail loudly with a detailed OTEL span and log, never silently skip.
- **Diamonds and Coal (Living World):** Entity state is the system-of-record; cards are a derived projection. Mutation propagates to the index via reproject.
- **Verify Wiring:** The `sync_entity_cards()` call must be reachable from the production turn-build path, not isolated in a test.
- **OTEL Lie-Detector:** The GM panel must see `accretion.entity_sync` spans to verify the index is being kept fresh.

### Related ADRs

- **ADR-118 (Universal Retrieval Layer)** — the master design. Section D2 (dirty-flag reproject) governs the mutation loop.
- **ADR-047 (Prompt Injection Sanitization)** — EntityCard.content carries player-influenced text and is sanitized at injection (75-5). Reproject does NOT re-sanitize (sanitization is a one-time event at the player boundary, not a per-turn re-pass).
- **ADR-002 (SOUL)** — Diamonds and Coal, Living World, Graceful Degradation.
- **ADR-090 (OTEL Dashboard Restoration)** — defines the `accretion.*` span family.