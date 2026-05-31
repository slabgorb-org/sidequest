---
story_id: "75-3"
jira_key: ""
epic: "75"
workflow: "architecture"
---

# Story 75-3: [DESIGN] Universal RAG retrieval layer — index + retrieve NPCs/locations per turn (ADR)

## Story Details

- **ID:** 75-3
- **Title:** [DESIGN] Universal RAG retrieval layer — index + retrieve NPCs/locations per turn (ADR)
- **Jira Key:** (none — no Jira integration)
- **Epic:** 75 — RAG Retrieval Layer — Restore Accretion, Budgeted Selection, Universal Retrieval Design
- **Workflow:** architecture (STEPPED)
- **Points:** 3
- **Priority:** p2
- **Stack Parent:** none (singleton story)

## Workflow Tracking

**Workflow:** architecture
**Workflow Type:** stepped
**Phase:** setup
**Phase Started:** 2026-05-31T03:30:26Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-31T03:30:26Z | - | - |

## Story Context & Design Brief

### Verification Source

Scout audit completed 2026-05-30, verified against Rust origin
(`github.com/slabgorb/sidequest-api`) and current Python tree (`sidequest-server`).
This brief is grounded in code fact, not status badges.

### KEY FINDING: The Lore RAG Is Real and Fires Every Turn

The lore RAG is **NOT** dead in Python. Real wiring confirmed:

- **Entry:** `websocket_session_handler.py:2449` → `_retrieve_lore_for_turn()`
- **Embedding:** `lore_embedding.py:276` → `retrieve_lore_context()` (real MiniLM-L6-v2 384-dim embeddings via daemon)
- **Injection:** `orchestrator.py:2096` (AttentionZone.Valley) → narrator prompt
- **Index:** live `LoreStore.query_by_similarity()` — per-turn retrieval works
- **Query tool:** `query_lore.py` tool is wired as a secondary pull path (docstring saying "not wired" is **stale**)
- **Context threading:** `lore_store` threaded into `ToolContext` (`session_helpers.py:1159`)

**BUT:** The RAG is **LORE-ONLY** and **STARVING** (only static seed facts, no per-turn accretion).

### Epic 75 Overview: Three Interleaved Stories

This epic addresses **three threads** uncovered by the Rust audit:

**75-1 (Restoration):** Port `accumulate_and_persist_lore` (Rust `lore_sync.rs:26-120`)
- Rust re-fed the RAG every turn with narrator-discovered facts
- Python dropped this: runtime facts flow through `commit_known_fact.py` / `query_known_facts.py`
- Those facts are **NEVER embedded**, so the index is starving on discovered lore
- **Reuse:** Live embedding pipeline + `LoreStore` already do real vector retrieval
- **Story 75-1 is separate;** this story does NOT implement accretion

**75-2 (Restoration):** Port budgeted NPC working-set selection (Rust `npc_context.rs:11-86`)
- Rust bounded NPC prompt cost by **SELECTION**, not eviction
- Scene-present NPCs (last_seen ≤ 2 turns) got full profiles
- Others got name + role; unreferenced NPCs got compact names only
- Python dropped this: `orchestrator.py:682` / `session_helpers.py:1179` load `npc_pool` **verbatim**
- This made "cap the pool" (72-6, now cancelled) look necessary — **wrong framing** (eviction violates Diamonds-and-Coal / Living World)
- **No NPC is ever deleted;** bounding is selection-only
- **Story 75-2 is separate;** this story does NOT implement budgeted selection

**75-3 (THIS STORY — NET-NEW DESIGN):** Universal retrieval layer for lore + locations/POIs + NPCs + factions + events
- NPCs and locations were **NEVER RAG-indexed** in either Rust or Python
- They have always been snapshot-carried: full `npc_pool` blob, full `location_list` blob, dumped into narrator context each turn
- **The vision:** A truly **universal** retrieval layer where lore + locations + NPCs + factions + events are all:
  - **Indexed** (embedded into a shared vector store)
  - **Retrieved per turn** by relevance (not snapshot-dumped in full)
  - **Budgeted** against token limits
  - **Persisted** so retrieval reflects the running world

### Critical Design Questions (This Story Must Answer)

The ADR must make clear decisions on:

1. **Persistence of record:**
   - Do NPCs/locations move to queryable Postgres rows (system-of-record), or stay snapshot-carried with a retrieval index layered on top?
   - Implications: consistency, update paths, durability, query flexibility

2. **What gets indexed/embedded (beyond lore):**
   - NPCs? (names, roles, dispositions, goals, relevant facts)
   - Locations/POIs? (names, descriptions, mechanical properties, linked NPCs)
   - Factions? (goals, members, resources, attitudes toward party)
   - Events? (what happened, who was involved, consequences)
   - Inventory? (party and/or NPC possessions, mechanical relevance)
   - All of the above? Subset?

3. **Embedding strategy:**
   - One unified embedding model (MiniLM-L6-v2, already live for lore)?
   - Separate models for different entity types?
   - How to handle long descriptions (truncation, chunking, hierarchical)?
   - What metadata travels with embeddings (entity type, ID, provenance)?

4. **Per-turn retrieval + token-budget seam:**
   - Current state: lore RAG auto-fires every turn, retrieved lore injected into prompt at AttentionZone.Valley
   - Extend this to NPCs/locations/factions? Same zone or different zones?
   - Who decides what's "relevant" for a given turn context? LLM-driven query? heuristic? both?
   - How is the budget enforced? (total tokens for all retrieved entities per turn, or separate budgets per type?)
   - Does retrieval replace snapshot-dumping entirely, or do we keep a fallback (e.g., "always include scene-present NPCs in full")?

5. **Interaction with 75-1 (accretion) and 75-2 (budgeted selection):**
   - 75-1 feeds newly discovered facts into lore embeddings — does the universal layer ingest these same accreted facts?
   - 75-2 selects a working-set (scene-present full, others abbreviated) — does universal retrieval **replace** this selection, or does 75-2's selection become the **query** for retrieval?
   - How do the three stories compose? Waterfall (75-1 → 75-2 → 75-3), or independent parallel implementations?

6. **OTEL observability (doctrine mandated):**
   - Every subsystem decision must be observable in the GM panel (ADR-031 / ADR-090 / ADR-103)
   - Retrieval seam must emit spans:
     - Query fired (entity types, token budget, turn context)
     - Entities retrieved (which entities, relevance scores, token cost)
     - Fallback/error paths (query failed, budget exceeded, no relevant entities)
   - So Keith (dev) can verify the retrieval is actually engaging, not Claude just improvising

7. **Implementation story naming:**
   - This story is DESIGN ONLY. No code. The ADR must **name** the follow-on stories that will implement:
     - Universal indexing (embedding NPCs/locations/etc.)
     - Per-turn retrieval wiring
     - Integration with 75-1 and 75-2
     - OTEL instrumentation
     - Tests (unit + integration wiring)

### Related ADRs & Existing Infrastructure

**ADR-048 (Lore RAG Store with Cross-Process Embedding):**
- Defines the live embedding pipeline: `lore_embedding.py` → daemon MiniLM-L6-v2 embeddings
- `LoreStore` backend: in-memory `fragments` dict + Chroma in-process for query
- This is the **exact seam** the universal layer should reuse/extend

**ADR-059 (Monster Manual — Server-Side Pre-Generation via Game-State Injection):**
- Injects game-state snapshots (NPCs, encounters) into narrator prompts at specific AttentionZones
- Currently: full NPC blob at orchestrator.py:682 (AttentionZone.Valley, same as lore)
- Status: marked "dark" (partially implemented)
- Universal layer will supersede/redefine this seam

**ADR-087 (Post-Port Subsystem Restoration Plan):**
- 75-1, 75-2, 75-3 are **restoration + expansion** tasks from this ADR
- Documents what was lost in the Rust→Python port and how to recover it
- This ADR should reference 087 for traceability

**ADR-014 (Diamonds and Coal):**
- **Living World doctrine:** no deletion, only discovery and change
- 75-2 (budgeted selection) explicitly respects this: no NPC eviction, selection only
- Universal layer must also respect: entities move in/out of context by relevance, never by deletion

**Live Infrastructure Already Available:**

- **Lore embedding pipeline:** `lore_embedding.py:embed_pending_fragments()` → daemon MiniLM
- **LoreStore query:** `LoreStore.query_by_similarity(query_text, top_k, filters)` → Chroma vector search
- **Per-turn retrieval wiring:** `websocket_session_handler.py:2449` → `_retrieve_lore_for_turn()` (already hooked every turn)
- **ToolContext threading:** `session_helpers.py:1159` — context passed to narrator tools
- **OTEL instrumentation:** `telemetry/` module with span definitions ready for extension

### What This Story Delivers (ADR Only)

**Acceptance Criteria:**

1. **ADR drafted:** Defines the universal retrieval layer — context types indexed (lore/locations/NPCs/factions/events), embedding strategy, per-turn retrieval+budget seam, and persistence-of-record decision.
2. **ADR reconciles with 048/059/087:** Explicitly states what 75-1 and 75-2 deliver vs. what this design adds on top.
3. **ADR specifies OTEL spans:** The new retrieval seam must emit spans (per doctrine: every subsystem decision observable in the GM panel).
4. **Design names implementation stories:** No code in this story. The ADR must spawn follow-on stories to implement the design.

**Deliverable:** ADR file at `docs/adr/XXX-universal-retrieval-layer.md` (ADR number to be assigned).

## Delivery Findings

No upstream findings at setup phase.

## Design Deviations

No spec deviations at setup phase.

---

**Branch:** `feat/75-3-universal-rag-retrieval-layer-adr` (off `main`)  
**Session Started:** 2026-05-31T03:30:26Z
