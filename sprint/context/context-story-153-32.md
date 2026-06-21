# Story Context: 153-32 — Knowledge/Journal Is Client-Reactive-Only; Decide Whether Server known_facts Must Persist

## Story Metadata
- **Story ID:** 153-32
- **Epic:** 153 (Playtest follow-ups — open findings from the 2026-06-20/21 full-stack /sq-playtest sweep)
- **Type:** Bug / **Decision** (decision-first — investigation gates implementation)
- **Points:** 2
- **Workflow:** trivial
- **Repositories:** sidequest-server
- **Priority:** P3
- **Related:** 153-24 (room-state persistence) — shares the "cold reload-from-save" concern
- **Distinct from:** the glenross CLUE-JOURNAL item (mystery clue-graph) — **do not merge**

## Problem Statement

After 3 turns the Knowledge/Journal UI shows 6 entries, but a forensics snapshot shows
`characters[].known_facts` is **empty** for both PCs, and `/timeline` has **no KNOWLEDGE
event kind** (only `NARRATION` + `SCRAPBOOK_ENTRY`). The Journal is a **client-reactive
projection** derived from per-turn narration `footnotes` (the "knowledge" payload); the
server-side `known_facts` store is unwritten for non-scenario worlds.

This is **a question, not necessarily a bug.** The narration stream carries per-turn
`footnotes` and the client builds the Journal reactively (ADR-136-style reactive
projection / ADR-133 streaming accumulator). But two things never happen on a world
without a scenario clue graph:
1. `known_facts` on the character snapshot is never written from the narration stream.
2. No KNOWLEDGE timeline event is emitted.

The decision this story must settle: **is server `known_facts` SUPPOSED to be populated
from the narration knowledge stream** — so (a) the narrator can be fed what the player
knows, and (b) the Journal survives a cold reload-from-DB rather than only a
replay-rebuild — **or is client-reactive-only the intended design (ADR-136/ADR-100), in
which case close WONTFIX?**

## Root Cause Direction (current data flow — established by investigation)

The investigation already mapped the live flow; the story's job is to **decide**, then
implement-or-document:

- **`footnotes` are narrator-owned and forwarded to the UI.** Per the ADR-150 amendment
  (2026-06-20), `footnotes` is the "player's knowledge/journal feed — a GENERATIVE /
  authorial narrator output." The handler forwards them into `NarrationPayload.footnotes`;
  the client's `useStateMirror` accumulates them into `knowledge[]`. This is the 6-entry
  Journal.
- **`known_facts` IS a server-persisted field and IS rehydrated on cold reload** — but it
  is **only written via two paths**, neither of which is the general narration stream:
  1. `consume_clue_footnotes` (scenario_clue_intake) mints a `KnownFact` **only when a
     footnote's `fact_id` resolves to a scenario clue node.** On a world with **no
     scenario clue graph** (`scenario_state is None`) this is a no-op — exactly
     `beneath_sunden` / non-mystery worlds, which is why `known_facts` is empty there.
  2. The `WorldStatePatch.discovered_facts` lane (`session.py`) and the narrator
     `commit_known_fact` tool — both are deliberate, not the default footnote path.
- **The narrator is NOT pre-fed `known_facts`.** It reads them on demand via the
  `query_known_facts` tool; there is no `known_facts` section injected into the prompt by
  default. So today, "what the player knows" (the 6 Journal entries) is **not** guaranteed
  to be in the narrator's context.
- **Cold reload:** the server snapshot rehydrates `Character.known_facts` from Postgres
  (so whatever was written survives), but the **client Journal is rebuilt from narration**,
  not from a server knowledge store. On a non-scenario world the persisted `known_facts`
  is empty, so a cold reload-from-save would show an empty Journal until new narration
  arrives (the `/replay` backfill is the only repopulation path, and its wiring on resume
  is part of what AC 1 must confirm).

**The gap, stated precisely:** on a world without a scenario clue graph, per-turn
`footnotes` build the client Journal but are **never routed into server `known_facts`**.
That is by-design *if* the Journal is meant to be ephemeral/reactive (ADR-136), or a
half-wired pipeline *if* `known_facts` is meant to be the durable backing store for the
narrator + cold reload (ADR-100's KnownFacts/JOURNAL_RESPONSE intent).

## Acceptance Criteria

1. **Investigation AC — answer the three load-bearing questions in writing (in the PR /
   story notes), with file+line evidence:**
   1. **Is the narrator fed `known_facts` today?** Confirm whether the narrator prompt
      includes a per-player knowledge section by default, or only the on-demand
      `query_known_facts` tool. (Evidence: `orchestrator.py` / `prompt_framework` prompt
      assembly; the `query_known_facts` tool.)
   2. **Does an in-dungeon save survive a cold reload-from-DB with its Journal intact, or
      only via narration replay?** Drive a non-scenario world (e.g. `beneath_sunden`) a
      few turns, confirm the UI Journal has entries while `snapshot.characters[].known_facts`
      is empty, then exercise the cold load path (`pg/snapshot.load_snapshot`) and report
      whether the Journal repopulates from a server store, from `/replay`, or not at all on
      resume.
   3. **Is the empty `known_facts` specific to no-scenario-graph worlds?** Confirm the
      scenario path (`consume_clue_footnotes`) DOES write `known_facts` on a mystery world
      (e.g. glenross) and that the gap is the absence of a non-scenario footnote→known_facts
      route — establishing this is a general-knowledge gap, not a scenario-system bug.

2. **Decision AC — record the verdict with rationale, citing ADR-136 and ADR-100:**
   - Choose **(A) Persist** — route the narration `footnotes` knowledge stream into server
     `known_facts` (so the narrator context survives and the Journal survives cold reload),
     **or** **(B) Client-reactive-by-design / WONTFIX** — confirm the Journal is an
     intentional ephemeral reactive projection (ADR-136) and that durable knowledge is
     reserved for the scenario-clue path (ADR-100). The verdict must reconcile with the
     ADR-150 amendment that made `footnotes` narrator-owned, and with ADR-100's stated
     KnownFacts/JOURNAL_RESPONSE pipeline (which is `partial` — note which seams are live
     vs deferred).

3. **Conditional implement-or-document AC (branch on AC 2):**
   - **If (A) Persist:** route non-scenario `footnotes` into `Character.known_facts`
     (reuse the existing `KnownFact` model and the existing forwarding seam in the handler
     — do not invent a parallel store), so that after N turns
     `snapshot.characters[].known_facts` is non-empty on a non-scenario world and survives
     a cold reload. Emit a KNOWLEDGE-equivalent forensic/timeline event **only if** the
     decision says the timeline should record knowledge (reuse the existing
     `append_event(kind=...)` event-kind plumbing — do not add a new system). Include the
     wiring proof in AC 4.
   - **If (B) WONTFIX:** document the client-reactive-by-design contract where it belongs
     (a short note in ADR-136 and/or ADR-100, and/or a code comment at the
     `footnotes`-forwarding seam) so the next forensics reader is not surprised by empty
     `known_facts`. Close the story as WONTFIX with the rationale. No code behavior change.

4. **Validation / wiring AC (applies to branch A; for branch B, the wiring proof is the
   documentation landing):**
   - **Branch A:** an integration test drives the real narration-apply path on a
     non-scenario world fixture, asserts that emitted `footnotes` land in
     `Character.known_facts` (behavior, not source-grep — see server CLAUDE.md "No
     Source-Text Wiring Tests"), and that the facts survive a serialize→`load_snapshot`
     round-trip. If a KNOWLEDGE timeline event was added, assert it via the forensic
     reader / OTEL span, not by grepping the handler.
   - **Branch B:** the WONTFIX decision and the by-design contract are recorded in the ADR
     and/or the seam comment; no test change required beyond confirming current behavior is
     unchanged.

## Key Code Areas to Investigate

**The `known_facts` model + write paths:**
- `sidequest-server/sidequest/game/character.py` (~lines 35–62, 119) — `class KnownFact`
  (`content`, `confidence` Literal `Certain/Suspected/Rumored/Discovered`, `source`,
  `learned_turn`, `fact_id`, `category`) and `Character.known_facts: list[KnownFact]`.
  The docstring states "narrator uses known_facts for context" — the intent is durable.
- `sidequest-server/sidequest/server/dispatch/scenario_clue_intake.py` —
  `consume_clue_footnotes` (~lines 34–87): mints `KnownFact` **only when**
  `fn.fact_id in clue_ids` and `scenario_state is not None`. This is the sole footnote→
  known_facts route today, and it no-ops on non-scenario worlds.
- `sidequest-server/sidequest/game/session.py` — `DiscoveredFact` (~lines 442–451, 570)
  and `_apply_world_patch_inner` (~lines 1737–1744): the `WorldStatePatch.discovered_facts`
  lane into `known_facts`.
- `sidequest-server/sidequest/agents/tools/commit_known_fact.py` — narrator-driven write.
- `sidequest-server/sidequest/agents/tools/query_known_facts.py` — on-demand narrator
  read (this is how/whether the narrator currently "sees" what the player knows).

**The footnotes forwarding seam (where branch-A routing would attach):**
- `sidequest-server/sidequest/server/websocket_session_handler.py` (~lines 1712–1841) —
  builds `forwarded_footnotes`, emits `state.footnotes_forwarded`, calls
  `consume_clue_footnotes(...)`, and packs `footnotes=forwarded_footnotes` into the
  `NarrationPayload`. This is the single choke point where every per-turn footnote is in
  scope — the natural attach point for a non-scenario known_facts route.
- `sidequest-server/sidequest/agents/orchestrator.py` (~lines 1341–1365) — `footnotes` is
  narrator-owned (ADR-150 amendment comment); the source of the per-turn knowledge.

**Client Journal (confirm reactive-only):**
- `sidequest-ui/src/hooks/useStateMirror.ts` — accumulates `knowledge[]` from
  `msg.payload.footnotes` on each `NARRATION`; hardcodes `confidence:'Suspected'` /
  `source:'Observation'` (ADR-100 acknowledged "load-bearing lies"); has a dormant
  `JOURNAL_RESPONSE` handler whose sender is dark.
- `sidequest-ui/src/components/KnowledgeJournal.tsx`, `src/providers/GameStateProvider.tsx`
  (`knowledge: KnowledgeEntry[]`).

**Timeline / event kinds (for the KNOWLEDGE-event question):**
- `sidequest-server/sidequest/game/pg/forensic.py` (~lines 223–267) — `build_timeline`;
  aggregates `event_kind_counts`. Existing kinds via `append_event(kind=...)` include
  `NARRATION`, `SCRAPBOOK_ENTRY`, `STATE_UPDATE`, `CHAPTER_MARKER`, `DOOMED`,
  `SECRET_NOTE`, encounter kinds — **no KNOWLEDGE kind**. A KNOWLEDGE event would emit at
  the footnote-intake seam.
- `sidequest-server/sidequest/server/rest.py` — the `/timeline` debug endpoint.

**Cold reload-from-save (shared with 153-24):**
- `sidequest-server/sidequest/game/pg/snapshot.py` (~lines 119–209) — `load_snapshot`;
  rehydrates `snapshot.characters[].known_facts` and feeds `_generate_recap`. Confirms
  what is persisted (known_facts) vs what is replayed (the client Journal).
- `sidequest-server/sidequest/game/pg/save_repository.py` (~lines 177–209) — `load`.

**ADRs to read and cite in the decision:**
- `docs/adr/100-journal-pipeline-coherence.md` (**partial**) — the canonical map:
  footnotes → known_facts → JOURNAL_RESPONSE → UI, seams A/B (live, scenario path) vs
  seam C (half-wired: no `JOURNAL_RESPONSE` sender; UI ignores narrator `fact_id`;
  `confidence:'Suspected'` hardcode). This ADR is the strongest evidence that durable
  `known_facts` is *intended*, with the general-stream wiring deferred.
- `docs/adr/136-player-facing-relationship-surface.md` — reactive projection + claims-only
  belief firewall; scoped to **NPC** beliefs/relationships, NOT player `known_facts`.
  Citing it for "client-reactive-by-design" requires care: it governs the relationship
  surface, not the knowledge surface — weigh whether it actually sanctions an ephemeral
  player Journal or whether ADR-100 is the controlling ADR here.

## Technical Notes

- **Reuse-first:** branch A must route through the existing `KnownFact` model and the
  existing `forwarded_footnotes` choke point + `append_event` kind plumbing. Do **not**
  add a parallel knowledge store or a new event system. The ADR-150 amendment already
  made `footnotes` narrator-owned and generative — branch A is "also persist what's
  already generated," not a new pipeline.
- **The hard question for branch A is confidence/source fidelity.** Scenario clues mint
  `confidence:'Discovered', source:'ScenarioClue'`; the UI hardcodes `'Suspected'/
  'Observation'`. A non-scenario persist route must pick a defensible default (likely the
  `KnownFact` model default `confidence:'Certain', source:'GameEvent'`, or carry the
  footnote's own fields) — decide and document, don't silently inherit the UI's lie.
- **`learned_turn`** should be stamped from `snapshot.turn_manager.interaction` (matching
  `consume_clue_footnotes`), not 0.
- **Dedup:** footnotes carry `fact_id`; the persist route must dedup on `fact_id` across
  turns so a re-mentioned fact does not duplicate (mirror the UI's `seenFactIds` and the
  scenario `is_new` check).
- **Spoiler firewall (ADR-105):** any persisted player knowledge stays player-side; this
  story does not touch NPC belief_state or the claims-only firewall.
- **Dependency with 153-24:** both stories hinge on "what survives a cold reload-from-DB."
  If 153-24 is reworking the snapshot/load path, coordinate so the knowledge decision lands
  consistently with the room-state persistence model (same `pg/snapshot.py` load path).

## Story Scope

This is a **decision-first** story. In scope:
- The investigation (AC 1) and the recorded decision (AC 2).
- **Either** wiring the non-scenario `footnotes`→`known_facts` route + cold-reload survival
  (branch A) **or** documenting the client-reactive-by-design contract and closing WONTFIX
  (branch B) — not both.

Out of scope:
- The glenross mystery CLUE-JOURNAL clue-graph item (separate; do not merge).
- The ADR-100 seam-C half-wiring (`JOURNAL_RESPONSE` sender, UI `fact_id` dedup,
  retiring the `confidence:'Suspected'` hardcode) — those are their own feeder stories;
  touch only what the chosen branch requires.
- NPC belief_state / relationship surface (ADR-136 NPC side).
- Room-state persistence mechanics (153-24), beyond coordinating on the shared cold-reload
  load path.
