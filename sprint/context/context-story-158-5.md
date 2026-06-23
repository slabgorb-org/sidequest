# Story 158-5: Persist known_facts server-side — Journal/Knowledge currently renders client-only

**Story ID:** 158-5  
**Epic:** 158 (Playtest sweep follow-ups: WWN combat seating, narrator grounding, roster/map/MP polish)  
**Points:** 3  
**Priority:** p2  
**Workflow:** tdd  
**Repos:** sidequest-server  
**Status:** backlog  
**Type:** bug

---

## Story Summary

The playtest sweep (2026-06-22, session `697cbc14` on caverns_and_claudes/beneath_sunden) surfaced a suspected persistence gap: the UI's Knowledge/Journal panel displays "Knowledge Gained · N item(s)" entries across turns, but a debug snapshot shows `characters[0].core.known_facts: []` and top-level `known_facts: None` in the PostgreSQL save. Knowledge appears to render reactively in the client but doesn't persist.

**Critical nuance:** This story's scope depends on **one binary question** that TEA must resolve before writing RED tests:

> **Are the "Knowledge Gained" UI entries sourced from ephemeral `footnotes` (by-design non-persisted per ADR-100 amendment, story 153-32) or from durable `KnownFacts`?**

- **If footnotes:** The "Knowledge Gained" label is misleading (it should say "Temporarily Learned" or similar) — this is a UI naming issue, not a save bug.
- **If KnownFacts:** There is a real persistence gap where durable facts are not being written to the snapshot.

TEA's RED phase **must start by answering this question** with code evidence (trace the UI component back to its data source, then check what's writing that source).

---

## Architecture & Design Context

### Two-Channel Journal Architecture (ADR-100)

The SideQuest journal is built on a **deliberately two-channel design** documented in ADR-100:

#### Channel 1: Ephemeral UI Feed
- **Source:** Narrator emits `footnotes` in the `game_patch` JSON block each turn
- **Path:** `footnotes` → extracted and coerced into typed `Footnote` models → packaged into `NarrationPayload.footnotes` → broadcast through `EventLog` and `ProjectionFilter` → UI's `useStateMirror` accumulates a `knowledge[]` array
- **Storage:** Client-side state accumulator only; does NOT write to `Character.known_facts`
- **Durability:** Does NOT survive a cold reload (no footnote replay-backfill on resume)
- **Contract:** Narrator prompt (`agents/narrator_prompts/output_only.md`) makes this explicit: "emit footnotes here AND call `commit_known_fact` when the fact should be durably known"
- **OTEL signal:** Feed channel emits `state_transition` (field=`footnotes`) watcher event via `_watcher_publish` + `state.footnote_fact_id_minted`

#### Channel 2: Durable Server-Side Store
- **Source:** `Character.known_facts: list[KnownFact]` — the canonical, persistent journal stored per character in PostgreSQL
- **Writers (only these three):**
  1. **Narrator's `commit_known_fact()` tool** — deliberate, tooling-based writes
  2. **`WorldStatePatch.discovered_facts`** — declarative patch-based writes in narrator output
  3. **Scenario clue hook `consume_clue_footnotes()`** — ADR-100 Seam A/B; only fires when `fact_id` matches a clue in the bound scenario graph
- **Storage:** Persisted in the PostgreSQL save snapshot (`characters[].core.known_facts`)
- **Durability:** Survives cold reload; `pg/snapshot.load_snapshot()` rehydrates facts and feeds them into `_generate_recap`
- **OTEL signal:** Durable mints emit `tool.write.commit_known_fact` dispatch span or `SPAN_SCENARIO_ADVANCE` (for clue discoveries)

### The Historical Decision (153-32, commit 24978b88)

Story 153-32 resolved a **non-persistence observation** on beneath_sunden: after three turns, the UI Journal showed six entries, yet `snapshot.characters[].known_facts` was empty. The decision:

> **Client-reactive-by-design (WONTFIX).** There is **intentionally NO general "persist every footnote" route**. By ADR-100, per-turn footnotes are the ephemeral journal feed; the durable store is written only by deliberate paths (scenario clue hook, `commit_known_fact` tool, `WorldPatches.discovered_facts`). So an empty `known_facts` with a populated UI Journal on a no-scenario-graph world is the two-channel design working as designed.

The decision is recorded at the exact point a forensics reader would look (in `websocket_session_handler.py` after the `consume_clue_footnotes` seam), so future readers are not surprised.

### The Seam That's Still Open (Seam C — Not This Story's Scope)

The **durability question for the UI** is owned by ADR-100 Seam C (not 158-5):

- **Server side:** Implement a `JOURNAL_REQUEST` handler that emits `JOURNAL_RESPONSE` populated from the canonical `character.known_facts`
- **UI side:** `useStateMirror` must drop the synthetic `${turn}-${marker}` id manufacture and consume narrator-supplied `Footnote.fact_id` when present; respect `confidence` and `source` from the server's `KnownFact` model
- **Owner:** Feeder stories 50-14 through 50-17 (not this epic; part of ADR-087 post-port restoration plan)

---

## The Playtest Finding (2026-06-22 Session 697cbc14)

**Repro:** 
1. Play caverns_and_claudes/beneath_sunden on a solo PC descent
2. Each turn's narration displays "Knowledge Gained · N item(s)" in the UI
3. After 3 turns, the Knowledge panel accumulates 6+ entries
4. Call `GET /api/debug/save/<slug>/snapshot` and inspect:
   - `snapshot.characters[0].core.known_facts: []` (empty)
   - `snapshot.known_facts: None` (null)
5. **Observation:** Knowledge renders reactively in the client, but the server snapshot carries no persistent record

**Lie-detector framing:** The journal appears improvised client-side. The engine doesn't actually "know" these facts in the durable store.

---

## Investigation Directive for TEA (RED Phase Entry)

Before writing tests, TEA must trace the bug to its source:

### Step 1: Determine Data Source (Code Trace)
- Open `sidequest-ui/src/components/NarrationCards/KnowledgeJournal.tsx` (or equivalent)
- Trace the "Knowledge Gained" label back to its data field: is it sourced from `state.footnotes` or from `state.known_facts`?
- Search `sidequest-ui/src/hooks/useStateMirror.ts` for where `knowledge` is accumulated — does it come from `NarrationPayload.footnotes` or from `JOURNAL_RESPONSE`?

### Step 2: Verify the Playtest Snapshot
- Reproduce the 697cbc14 session (beneath_sunden solo descent, 3+ turns)
- Capture the debug snapshot: `GET /api/debug/save/<slug>/snapshot`
- Check: does `characters[0].core.known_facts` contain the UI's displayed entries?

### Step 3: Determine Writer
- If the UI shows entries but `characters[].core.known_facts` is empty:
  - **Option A (ephemeral):** Entries come from per-turn `footnotes` (Channel 1); no writer is expected → this is by design
  - **Option B (durable):** Entries come from `KnownFacts` (Channel 2); a writer (narrator tool, patch, or clue hook) failed to fire or didn't persist → this is a bug

### Step 4: Document Finding in RED Test
Write a test that reproduces the condition and asserts the expected behavior:
- If ephemeral: `test_knowledge_journal_footnotes_ephemeral_by_design` — verify that footnotes do NOT write to known_facts
- If durable: `test_known_facts_persistence_gap` — verify the durable path is broken and needs fixing

---

## Acceptance Criteria

### AC1: Determine Source and Document
- [ ] Code trace showing whether "Knowledge Gained" UI entries are sourced from `footnotes` or `KnownFacts`
- [ ] Reference code locations: UI component + useStateMirror hook + underlying narrator/narrator_handler paths
- [ ] Test demonstrating the condition with evidence (snapshot dump, assertion on actual vs expected)

### AC2: If Source is KnownFacts (Durable) — Fix the Persistence Gap
- [ ] Facts committed via narrator tools / patches / clue hooks are persisted to `characters[].core.known_facts` in the PostgreSQL snapshot
- [ ] Facts survive a cold reload / snapshot re-entry
- [ ] All writers (at least the active one) emit an OTEL span for observability

### AC3: Wiring Test (Proves Reachability)
- [ ] Integration test verifying the persistence path is reachable from the production turn-resolution flow
- [ ] Not just unit-tested in isolation; verifies end-to-end from turn dispatch → writer invocation → snapshot persist
- [ ] Fixture: scenario with at least one narrator fact-commit or patch-discovery

### AC4: OTEL Observability
- [ ] If persistence is implemented, the write path emits a clear OTEL span:
  - **Span name:** `tool.write.commit_known_fact` (if via tool) or `state_transition` with `field=known_facts` (if via patch) or `SPAN_SCENARIO_ADVANCE` (if clue hook)
  - **Attributes:** `fact_count`, `character_id`, `source` (e.g., "commit_known_fact", "world_patch", "scenario_clue")
  - **Purpose:** GM panel can verify the write fired and observe the actual fact count

### AC5: If Source is Footnotes (Ephemeral) — Document and Flag
- [ ] Document the two-channel design and why "Knowledge Gained" is a non-durable ephemeral label
- [ ] Flag for scope clarification: is this a UI UX issue (misleading label) or a user expectation mismatch?
- [ ] May be out of scope for this story; recommend to SM for potential rescoping or companion UI story

---

## Testing Strategy

### RED Phase (TEA)

1. **Investigation test:** Reproduce the playtest snapshot condition
   - Scenario: beneath_sunden solo descent, 3+ turns
   - Assert: UI shows Knowledge entries, snapshot shows empty `known_facts`
   - Determine: are entries from `footnotes` or `KnownFacts`?

2. **Source tracing test:**
   - Unit test: `test_knowledge_journal_ui_data_source` — verify the UI's knowledge array is built from `footnotes` or `JOURNAL_RESPONSE`
   - Check: does narrator emit facts via tool/patch on the test scenario?

3. **Snapshot verification test:**
   - Load the test scenario, capture snapshot after 3 turns
   - Assert on `snapshot.characters[0].core.known_facts` — should match UI if source is durable, should be empty if source is ephemeral

### GREEN Phase (Dev)

**Depends on TEA's findings:**

- **If durable:** Implement the missing persistence write (locate which writer failed, repair it, emit OTEL)
- **If ephemeral:** Document the design; optionally add a UI label clarity improvement (e.g., rename "Knowledge Gained" to "Observed" or add a "?" icon explaining ephemeral nature)

### Wiring Test (Integration, GREEN Phase)

- Full turn-resolution flow with the writer(s) enabled
- Verify persistence to snapshot
- Assert OTEL span fired
- Cold reload test: snapshot rehydrated, facts present in `_generate_recap`

---

## Related Stories & Dependencies

### Dependencies
- **No hard blockers.** This story is isolated; it fixes a detection issue.

### Related Architecture Stories
- **ADR-100 Seam A/B (story 50-5):** Scenario clue hook writer (uses `consume_clue_footnotes`)
- **ADR-100 Seam C (stories 50-14..50-17):** Server `JOURNAL_REQUEST` handler + UI `JOURNAL_RESPONSE` consumption
- **ADR-100 Amendment (story 153-32, commit 24978b88):** Documents the deliberate two-channel design

### Content References
- **Playtest session:** `/Users/slabgorb/Projects/sq-playtest-pingpong.md` (2026-06-22, session 697cbc14, DATA-ODDITY section)
- **Debug snapshot path:** `GET /api/debug/save/<slug>/snapshot` (server endpoint)

---

## Constraints & Assumptions

### Constraints
- Must not break the two-channel design (ephemeral footnotes remain non-persisting by design)
- Must not introduce a third writer of `known_facts` (the "deliberate writers only" discipline governs this)
- OTEL spans must be observable in the GM panel (no debug-only logging)

### Assumptions
- The playtest snapshot 697cbc14 is reproducible (session YAML persisted, scenario deterministic)
- Narrator output (footnotes, tool calls, patches) is being captured correctly in the test fixtures
- ADR-100 amendment (153-32, commit 24978b88) is authoritative for the two-channel design

---

## Touch Points (Code Locations)

### sidequest-server

| File | Change | AC |
|------|--------|----| 
| `sidequest/server/websocket_session_handler.py` | Trace `consume_clue_footnotes` call and narrator handler flow | AC1, AC2 |
| `sidequest/game/character.py` | Verify `known_facts: list[KnownFact]` model and writers | AC1, AC2 |
| `sidequest/game/session.py` | Check `WorldStatePatch.discovered_facts` writer | AC2 |
| `sidequest/agents/tools.py` | Check `commit_known_fact()` tool registration | AC1, AC2 |
| `sidequest/telemetry/spans.py` | Add OTEL span definitions if implementing persistence | AC4 |
| `tests/server/test_known_facts_persistence.py` | New file: RED + GREEN + wiring tests | AC1-AC5 |

### sidequest-ui

| File | Change | AC |
|------|--------|----| 
| `src/components/NarrationCards/KnowledgeJournal.tsx` | Identify UI data source (footnotes vs known_facts) | AC1 |
| `src/hooks/useStateMirror.ts` | Verify knowledge array accumulation logic | AC1 |
| `src/providers/GameStateProvider.tsx` | Check JOURNAL_RESPONSE handling (if implemented) | AC1 |

### sidequest-content

| File | Change | AC |
|------|--------|----| 
| (Test fixtures only) | Use beneath_sunden or tea_and_murder scenarios | AC3 |

---

## Narrative Anchor

Per CLAUDE.md, this story serves:

- **Keith (forever-GM-now-player):** The journal is a core player-facing surface. If knowledge doesn't persist, it breaks immersion and trust in the system — "I thought I learned that." This is a lie-detection issue.
- **James (narrative-first):** Knowledge persistence ties into the journal-as-reference tool — if he cites a fact later and it's gone on reload, the game breaks.
- **Alex (slow typist):** No UI timing impact; affects save/reload behavior, which happens between sessions.
- **Sebastien (mechanics-first):** Wants to see durable knowledge reflected in OTEL spans and the GM panel — mechanical grounding, not improvisation. If facts aren't being written, the lie-detector catches it.

---

## Questions for SM / Stakeholders

1. **Is the beneath_sunden session still available?** (Need to reproduce 697cbc14 for investigation)
2. **Is there a preference for persisting ALL footnotes vs only deliberate `commit_known_fact` calls?** (Depends on TEA's finding; may be a design question, not a bug fix)
3. **Should cold-reload recover the UI Journal?** (That's ADR-100 Seam C, owned by stories 50-14..50-17, but worth confirming scope here)

---

## Related Documents

- **ADR-100:** Journal Pipeline Coherence — Footnotes, KnownFacts, JOURNAL_RESPONSE, and the Scenario Clue Hook
- **ADR-100 Amendment:** 2026-06-22 decision on footnote→known_facts (client-reactive-by-design, no general persistence route)
- **Story 153-32 commit:** `24978b8886c2c75062845f2ceb28f37cfe82959b` — documents the design decision with full context
- **Playtest findings:** `/Users/slabgorb/Projects/sq-playtest-pingpong.md` (DATA-ODDITY section, session 697cbc14)
- **Character model:** `sidequest-server/sidequest/game/character.py` (`KnownFact` definition)
- **Narrator handler:** `sidequest-server/sidequest/server/websocket_session_handler.py` (turn-resolution flow)
- **Epic context:** `sprint/context/context-epic-158.md`
