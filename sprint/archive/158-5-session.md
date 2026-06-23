---
story_id: "158-5"
jira_key: ""
epic: "158"
workflow: "tdd"
---
# Story 158-5: Persist known_facts server-side — Journal/Knowledge currently renders client-only

## Story Details
- **ID:** 158-5
- **Title:** Persist known_facts server-side — Journal/Knowledge currently renders client-only
- **Jira Key:** (not assigned)
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 3
- **Priority:** p2
- **Type:** bug
- **Repo:** server (sidequest-server)

## Workflow Tracking
**Workflow:** tdd
**Phase:** red
**Phase Started:** 2026-06-23T06:12:17Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-23T06:08:09Z | 2026-06-23T06:12:17Z | 4m 8s |
| red | 2026-06-23T06:12:17Z | - | - |

## CRITICAL FORK — TEA Must Resolve First

This story hinges on answering a **binary question** before writing RED tests:

**Is the "Knowledge Gained" UI group sourced from ephemeral `footnotes` (by-design non-persisted per ADR-100 amendment, commit 24978b88, story 153-32) or from genuine `KnownFacts` (which SHOULD persist)?**

### If Footnotes (Ephemeral)
- **Finding:** The UI labels a non-persisted narrator footnote as "Knowledge Gained", creating a false expectation that the knowledge survives a reload.
- **Bug:** This is a UI naming/expectation mismatch, not a save persistence bug.
- **Scope:** Story may need rescoping — the server is working as designed (two-channel architecture: ephemeral UI footnotes + durable `known_facts`).
- **Reference:** ADR-100 Section "Amendment (2026-06-22, story 153-32)" documents the deliberate absence of a general footnote→known_facts route. The design is: narrator emits `footnotes` for ephemeral UI display, OR explicitly calls `commit_known_fact()` for durable storage.

### If KnownFacts (Durable)
- **Bug:** Facts sourced from `KnownFacts` (via narrator `commit_known_fact()` tool, `WorldStatePatch.discovered_facts`, or scenario clue hook) are not being persisted to the save snapshot.
- **Scope:** Server-side persistence gap; this is a real bug.
- **Fix:** Ensure durable paths are actually writing to `characters[].core.known_facts` in the save snapshot and emitting OTEL on write.

### Investigation Directive for TEA
1. Review ADR-100 architecture and the 153-32 amendment (commit 24978b88).
2. Trace the "Knowledge Gained" UI label back to its source: does it come from `NarrationPayload.footnotes` or from `JOURNAL_RESPONSE` with durable `known_facts`?
3. In the playtest snapshot, check which writer produced the UI entries: was it per-turn narrator footnotes (ephemeral), or the scenario clue hook / `commit_known_fact` tool (durable)?
4. Document the finding with evidence (code trace + test logic) in the RED phase.
5. If the source is durable `KnownFacts`, proceed with standard TDD (RED → GREEN → review).
6. If the source is ephemeral `footnotes`, flag for scope clarification — it may be a UI UX issue (misleading "Knowledge Gained" label) rather than a persistence bug.

## Technical Architecture Context

### The Two-Channel Journal Design (ADR-100)

**Ephemeral Channel (Component 2):**
- Per-turn narrator `footnotes` extracted and forwarded via `NarrationPayload.footnotes`
- Rendered reactively in UI's `KnowledgeJournal` component
- **Deliberately does not write to `Character.known_facts`** (by design)
- Source of truth: `useStateMirror.ts` state accumulator

**Durable Channel (Component 3):**
- Canonical `Character.known_facts: list[KnownFact]` persisted in PostgreSQL save snapshot
- Writers (only these three):
  1. Narrator's `commit_known_fact()` tool (deliberate, tooling-based)
  2. `WorldStatePatch.discovered_facts` (declarative in narrator output)
  3. Scenario clue hook `consume_clue_footnotes()` (ADR-100 Seam A/B; only fires on `fact_id` match to clue graph)
- On cold reload: `pg/snapshot.load_snapshot()` rehydrates persisted facts and feeds into `_generate_recap`
- On-demand read: `query_known_facts()` tool for narrator context (replaces ad-hoc blocks in prompt)

**The Bridge (Seam C — Not Yet Implemented):**
- Server `JOURNAL_REQUEST` handler → `JOURNAL_RESPONSE` (should emit canonical `known_facts`)
- UI `useStateMirror` consumption of `JOURNAL_RESPONSE` (respect narrator-supplied `Footnote.fact_id`, drop synthetic id manufacture)
- This seam is owned by feeder stories 50-14..50-17 (not this story's scope)

### OTEL Requirement

If this story implements `KnownFacts` persistence, the write path **must** emit an OTEL span:
- Span name: `tool.write.commit_known_fact` (if via tool) or `state_transition` with `field=known_facts` (if via patch)
- Attributes: `fact_count`, `character_id`, `source` (e.g., "commit_known_fact", "world_patch", "scenario_clue")
- Purpose: GM panel can verify the persist write fired and observe the actual fact count minted

Per CLAUDE.md: *"Every backend fix that touches a subsystem MUST add OTEL watcher events so the GM panel can verify the fix is working."*

## Suggested Acceptance Criteria (TEA will Refine)

1. **Determine and document the source** of the "Knowledge Gained" UI group with evidence:
   - Code trace showing whether the source is `footnotes` or durable `KnownFacts`
   - Test case demonstrating the gap

2. **IF the source is durable `KnownFacts`:**
   - Facts committed during a turn are persisted to the save snapshot (`characters[].core.known_facts`)
   - Facts survive a cold reload / snapshot reload
   - The persistence write path emits an OTEL span for observability

3. **Wiring test (proves reachability):**
   - Integration test confirming the persistence path is reachable from the production turn-resolution flow
   - Not just unit-tested in isolation; verifies end-to-end from narration handler to save write

4. **IF the source is ephemeral `footnotes`:**
   - Document the discrepancy (UI label mismatch)
   - Flag for scope clarification or UI UX fix (renaming, rephrase)

## Sm Assessment

**Themis the Just — setup weighed and balanced.**

Story 158-5 is a p2 server bug from the 2026-06-22 `beneath_sunden` solo playtest (session `697cbc14`): the UI shows "Knowledge Gained · N items" on narration cards, but the Postgres save reports `known_facts: []` / `None`. Classic lie-detector territory — the journal may be improvised client-side while the engine knows nothing.

**Why this is not a straight bug, and why setup carries a binary fork:** Commit `24978b88` (story 153-32) documents a *deliberate* absence of a general footnote→known_facts route. So an empty `known_facts` alongside a populated UI Journal is, on non-scenario worlds, working as designed (ADR-100's two-channel model: ephemeral `footnotes` for UI display vs. durable `KnownFacts` for persistence). The very first investigative step — owned by TEA in RED — must determine which channel feeds the UI label before a single test is written. The context document and the CRITICAL FORK section above make this the gating decision.

**Routing rationale:**
- **Workflow:** tdd (phased) → next phase **red**, owner **TEA** (Argus Panoptes). Correct for a 3-pt bug whose fix shape is genuinely unknown until the fork is resolved — TDD's RED phase *is* the investigation vehicle here.
- **Repo:** server only; branch `feat/158-5-persist-known-facts-server-side` cut from `develop` (gitflow), checked out clean.
- **OTEL doctrine flagged:** if the durable-KnownFacts path is the real gap, the persist write must emit a watcher span (per CLAUDE.md). Captured in context + ACs.
- **No Jira** (integration disabled for this project); session `jira_key: ""`.

**Merge-gate note:** open server PR #1057 (`feat/dungeon-region-population`, non-draft) is a separate dungeon-region feature from a parallel clone — not epic 158, not blocking; prime returned `NEW_WORK_STATE`.

**Verdict:** Setup complete and verified (session + context + branch all present). Handing to TEA for the RED phase. TEA's first obligation is the footnotes-vs-KnownFacts determination — do not write tests against a persistence gap that may not exist by design.

## Delivery Findings

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)

- **Conflict** (blocking): The story premise — "known_facts renders client-only / needs server-side persistence" — is a **misdiagnosis**. The durable persistence path is fully wired and proven working; there is no server persistence gap to fix. The fork resolves to **EPHEMERAL / by-design**. Affects the story scope itself (158-5 as written has no server work). *Found by TEA during test design.*

**Fork determination — EPHEMERAL (footnotes), by design. Evidence:**

1. **The per-narration-card "Knowledge Gained · N items" badge is the ephemeral footnote channel (ADR-100 Channel 1).**
   - `sidequest-ui/src/components/narrativeRenderers.tsx:62` renders `<span>Knowledge Gained</span>` inside the `FootnoteList` helper (`data-testid="world-facts"`), fed by `segment.footnotes` per narration card.
   - Confirmed by its own test: `narrativeRenderers.test.tsx:21` — "uses 'Knowledge Gained' header on the **footnote aside**."
   - This is what the DRIVER saw "on every narration card" in session 697cbc14. It is intentionally client-reactive and does not persist.

2. **The durable known_facts persistence path is fully wired AND proven by a passing reload test.**
   - `commit_known_fact` tool (`agents/tools/commit_known_fact.py:144-145`) appends to `pc.known_facts` then calls `ctx.repository.save(snapshot)`, emitting `tool.write.commit_known_fact` OTEL attrs (:147-150).
   - `tests/agents/tools/test_commit_known_fact.py:134 test_writes_fact_and_persists_across_reload` commits a fact, **reloads from the repository**, and asserts `len(pc.known_facts) == 1` with all fields intact across reload (:162-171). Non-vacuous, end-to-end.
   - Snapshot serializes `known_facts` (`character.py:119` field; `pg/snapshot.py:187`).
   - **Seam C is implemented** (context doc said it wasn't): `handlers/journal_request.py` (story 50-14) emits `JOURNAL_RESPONSE` from `character.known_facts`, tested in `tests/handlers/test_journal_request_handler.py`. The UI consumer (`useStateMirror.ts:149-180`) reconciles footnote-seeded entries against `JOURNAL_RESPONSE` by `fact_id`.

3. **Why `known_facts` was empty on beneath_sunden — correct two-channel behavior.**
   - `websocket_session_handler.py:1821-1843` is the verbatim 153-32 / commit `24978b88` decision: the scenario-clue seam is the ONLY footnote→known_facts route, gated on a clue-graph `fact_id` match. There is **intentionally no general "persist every footnote" branch.**
   - beneath_sunden has no scenario clue graph, and the narrator never called `commit_known_fact` / emitted a `discovered_facts` patch. No deliberate writer fired → empty store → **working as designed.**

- **Improvement** (non-blocking): The genuine latent concern is narrator *behavior*, not persistence plumbing: the narrator emits "Knowledge Gained" footnotes every turn but commits **none** of them durably, so on reload/recap the engine knows nothing the player learned. Closing this gap means having the narrator/dispatch selectively call the existing `commit_known_fact` tool — but that re-opens the deliberate 153-32 "no auto-persist-every-footnote" decision and is a different story shape (server prompt/dispatch, likely >3pts). Surfaced to user for a scope decision rather than silently expanding 158-5. *Found by TEA during test design.*

**RED action:** Held — no failing tests written, because there is no real persistence bug to drive (per SM directive: "do not write tests against a persistence gap that may not exist by design"). Awaiting user scope decision before exit.

## TEA Assessment

**Argus Panoptes — the hundred eyes traced every channel; the fork is closed.**

**Tests Required:** No
**Reason:** RED phase resolved the SM's gating fork to **EPHEMERAL / by-design**. There is no server persistence gap — the durable `known_facts` path is fully wired and already proven by a passing end-to-end reload test (`tests/agents/tools/test_commit_known_fact.py:134`). Writing a failing test against working, by-design code would be a fabricated RED. Per the SM directive ("do not write tests against a persistence gap that may not exist by design"), no tests were written.

**Determination (full evidence in Delivery Findings → TEA):**
- The per-narration-card "Knowledge Gained · N items" badge is the ephemeral footnote channel (ADR-100 Channel 1), intentionally client-only (`narrativeRenderers.tsx:62`).
- The durable channel persists end-to-end: `commit_known_fact` → `repository.save` → snapshot → reload → `JOURNAL_RESPONSE` (Seam C / 50-14, live). Proven by passing tests.
- `known_facts` empty on beneath_sunden = no deliberate writer fired on a no-scenario world = two-channel design working as designed (153-32 / `websocket_session_handler.py:1821-1843`).

**User scope decision (2026-06-23):** *Close as by-design.* The literal "persist known_facts server-side" scope has nothing to build. Story marked `canceled` (not `done` — no deliverable; crediting 3pts would misstate velocity). The latent narrator-commit-behavior concern and the UI-label-clarity option were presented and **not** elected; not filed as new stories.

**Status:** Closed by-design. No PR, no server commits (branch was empty → deleted). Session archived as the investigation record.
**Handoff:** None — story terminated. Returning coordination to Themis (SM) for sprint accounting.

## Design Deviations

### TEA (test design)
- **No RED tests written — story closed as by-design.**
  - Spec source: context-story-158-5.md, AC1–AC4 (RED phase test obligations)
  - Spec text: "TEA's RED phase must start by answering [the footnotes-vs-KnownFacts fork] with code evidence... If durable: write `test_known_facts_persistence_gap`."
  - Implementation: Fork resolved to EPHEMERAL/by-design with code+test evidence; no failing test authored because no real persistence bug exists. User elected to close the story as by-design.
  - Rationale: A RED test must encode a genuine desired behavior change. The persistence path already works (passing reload test); fabricating a failing test against by-design code violates TDD honesty and the SM's explicit directive.
  - Severity: major (changes the story outcome from "implement" to "close")
  - Forward impact: 158-5 canceled; the narrator-commit-behavior improvement remains an open, unfiled concern (see Delivery Findings → TEA Improvement) should the user wish to pursue it later.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->