---
story_id: "153-32"
jira_key: ""
epic: "153"
workflow: "trivial"
---
# Story 153-32: [KNOWLEDGE-CLIENT-REACTIVE-ONLY] decide and wire whether server known_facts must persist (narrator context + cold-reload survival) or confirm client-reactive-by-design per ADR-136

## Story Details
- **ID:** 153-32
- **Jira Key:** (none)
- **Workflow:** trivial
- **Stack Parent:** none
- **Repositories:** sidequest-server

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-22T12:11:40Z
**Round-Trip Count:** 2

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-22T11:39:53Z | 2026-06-22T11:39:53Z | instant |
| implement | 2026-06-22T11:39:53Z | 2026-06-22T11:52:47Z | 12m 54s |
| review | 2026-06-22T11:52:47Z | 2026-06-22T12:01:18Z | 8m 31s |
| finish | 2026-06-22T12:01:18Z | 2026-06-22T12:02:05Z | 47s |
| implement | 2026-06-22T12:02:05Z | 2026-06-22T12:07:14Z | 5m 9s |
| review | 2026-06-22T12:07:14Z | 2026-06-22T12:11:40Z | 4m 26s |
| finish | 2026-06-22T12:11:40Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Improvement** (non-blocking): The genuinely-open durability item — the UI Journal does not survive a cold reload-from-DB on any world (no footnote replay-backfill on resume) — is owned by ADR-100 Seam C feeder stories 50-14..50-17 (`JOURNAL_RESPONSE`). Confirmed still unwired. Affects `sidequest-server/sidequest/hooks/useStateMirror.ts` (UI) + a missing `JOURNAL_REQUEST` server handler (no rehydrate-from-`known_facts` path on resume). *Found by Dev during implementation.*
- **Question** (non-blocking): The narrator's adherence to the prompt's "call `commit_known_fact` when the fact should be durably known" instruction was not measured here; if playtests show the durable store staying thin on non-scenario worlds, that is a narrator prompt-tuning question (not an architecture gap), separate from this WONTFIX. Affects `sidequest-server/sidequest/agents/narrator_prompts/output_only.md`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (blocking): The deliverable's GM-panel observability claim names a non-existent span `state.footnotes_forwarded` (it is a `logger.info` label at `websocket_session_handler.py:1775`, not a watcher event). The real feed events are `state_transition` (field=footnotes, line 1779) and `state.footnote_fact_id_minted` (line 1758). Affects `sidequest-server/sidequest/server/websocket_session_handler.py` (new comment), `docs/adr/100-journal-pipeline-coherence.md` (2026-06-22 amendment), and this session's Decision Record AC-2 paragraph (correct the event name in all three). *Found by Reviewer during code review.* **→ RESOLVED in round-2 rework (verified closed by Reviewer + comment-analyzer against the delta; corrected to `state_transition`/field=footnotes + `state.footnote_fact_id_minted`).**
- No new upstream findings during round-2 re-review.

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

1 deviation

- **Documentation landed in the orchestrator repo (ADR-100) + server repo (seam comment), not the story's declared `repos: server` only**
  - Rationale: ADR-100 is the self-declared "front door for journal stories" and the correct home for the controlling contract; the forensics-reader-facing comment belongs at the server seam. Branch B's AC-3 explicitly sanctions "a short note in ADR-136 and/or ADR-100, and/or a code comment at the footnotes-forwarding seam," which spans both repos.
  - Severity: minor
  - Forward impact: none — documentation-only; SM should expect a 2-repo finish (orchestrator ADR + session, server seam comment).

## Dev Assessment

**Implementation Complete:** Yes (decision-first story — verdict (B) Client-reactive-by-design / WONTFIX; documentation, no behavior change)

**Files Changed:**
- `docs/adr/100-journal-pipeline-coherence.md` (orchestrator) — 2026-06-22 amendment recording the WONTFIX decision and the two-channel contract (footnotes = ephemeral feed; `known_facts` = deliberate writers only).
- `sidequest-server/sidequest/server/websocket_session_handler.py` (server) — comment-only addition after the `consume_clue_footnotes` call documenting the deliberate absence of a general footnote→`known_facts` route, so the next forensics reader is not surprised by empty `known_facts` on a non-scenario world.
- `.session/153-32-session.md` — Decision Record (AC 1 investigation answers with file+line evidence; AC 2 verdict + rationale).

**Tests:** 376/376 passing, 12 skipped (GREEN) — journal/known_facts/footnotes/scenario-clue subset; touched handler imports cleanly. Comment-only change, no behavior change (AC 4 Branch B: current behavior confirmed unchanged).

**Branch:** `feat/153-32-knowledge-client-reactive-only` (orchestrator + server)

**Rework (round 2, 2026-06-22):** Addressed the Reviewer's confirmed [MEDIUM][DOC] finding. Corrected the misnamed observability event in all three artifacts: the feed channel is observable via the `state_transition` (field=footnotes) watcher event + `state.footnote_fact_id_minted` through `_watcher_publish` — `state.footnotes_forwarded` is a `logger.info` label, not a watcher event. Fixed in `websocket_session_handler.py` (comment), `docs/adr/100-journal-pipeline-coherence.md` (amendment), and the Decision Record AC-2 paragraph above. Added an explicit "logger.info label, not a watcher event" note in each so the next reader doesn't repeat the conflation. Re-verified: ruff clean, import clean, 376/376 green (RUN_ID `153-32-dev-green-rework`). No behavior change.

**Handoff:** To review (Chrisjen Avasarala / Reviewer). Note for Reviewer: this is a decision/WONTFIX — the deliverable is the recorded verdict + contract, not a code behavior change. The story title's "per ADR-136" is corrected in the decision: ADR-100 (not ADR-136) is the controlling ADR for the player knowledge journal.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Documentation landed in the orchestrator repo (ADR-100) + server repo (seam comment), not the story's declared `repos: server` only**
  - Spec source: epic-153.yaml story 153-32 (`repos: server`)
  - Spec text: "repos: server"
  - Implementation: The durable by-design contract was recorded in `docs/adr/100-journal-pipeline-coherence.md` (orchestrator repo, where the feature branch lives) plus a local seam comment in `sidequest-server/.../websocket_session_handler.py` (server repo).
  - Rationale: ADR-100 is the self-declared "front door for journal stories" and the correct home for the controlling contract; the forensics-reader-facing comment belongs at the server seam. Branch B's AC-3 explicitly sanctions "a short note in ADR-136 and/or ADR-100, and/or a code comment at the footnotes-forwarding seam," which spans both repos.
  - Severity: minor
  - Forward impact: none — documentation-only; SM should expect a 2-repo finish (orchestrator ADR + session, server seam comment).

### Reviewer (audit)
- **Documentation landed in orchestrator (ADR-100) + server (seam comment), not `repos: server` only** → ✓ ACCEPTED by Reviewer: sound. ADR-100 is the self-declared "front door for journal stories" and the correct durable home for the contract; the forensics-reader comment belongs at the server seam. AC-3 Branch B explicitly sanctions "a short note in ADR-136 and/or ADR-100, and/or a code comment at the footnotes-forwarding seam," which spans both repos. The `repos: server` field was set at setup before the decision determined where docs land. SM: expect a 2-repo finish.
- No undocumented deviations found by Reviewer.

## Decision Record (153-32) — AC 1 (investigation) + AC 2 (verdict)

**Verdict: (B) Client-reactive-by-design / WONTFIX.** The per-turn narration
`footnotes` stream is the ephemeral journal feed by design; there is deliberately
no general footnote → `known_facts` route. Controlling ADR is **ADR-100** (the
story title's "per ADR-136" is a misattribution — ADR-136 governs the NPC
relationship surface, not the player knowledge journal). No behavior change.

### AC 1 — the three load-bearing questions, answered with file+line evidence

**Q1. Is the narrator fed `known_facts` today?**
No — not by default. There is no prompt section that injects `known_facts`; the
only access is the on-demand `query_known_facts` tool, which by its own docstring
*"Replaces ad-hoc `known_facts` blocks dumped into the narrator prompt"*
(`sidequest-server/sidequest/agents/tools/query_known_facts.py:5-9`). A grep of
`sidequest/agents/` for `known_facts` finds zero prompt-assembly injections — only
the two tools (`query_known_facts.py`, `commit_known_fact.py`) and the ADR-150
comment in `orchestrator.py:1346`. So "what the player knows" reaches the narrator
only if it calls `query_known_facts`, and on a non-scenario world that returns the
(empty) durable store — by design.

**Q2. Does an in-dungeon save survive a cold reload-from-DB with its Journal intact,
or only via narration replay?**
Durable `known_facts` survives; the ephemeral UI Journal feed does not.
`pg/snapshot.load_snapshot` (`sidequest-server/sidequest/game/pg/snapshot.py:119-209`)
rehydrates `GameSnapshot` (including `characters[].known_facts`, line 187) and feeds
it into `_generate_recap` (lines 188-190). There is **no footnote/journal
replay-backfill on resume** — a grep for replay+journal paths finds only the
dice-resolution re-entry (`narration_apply.py`) and `_REPLAY_SKIP_KINDS`
(`session_handler.py:154`), neither of which re-emits per-turn footnotes. So on a
non-scenario world the client's reactive `knowledge[]` rebuilds only from *new*
narration after reload; the prior feed is gone. (This is the genuinely-open
durability item, owned by ADR-100 Seam C feeder stories 50-14..50-17 — out of scope
here.)

**Q3. Is the empty `known_facts` specific to no-scenario-graph worlds?**
Yes. `consume_clue_footnotes`
(`sidequest-server/sidequest/server/dispatch/scenario_clue_intake.py:51-86`) returns
immediately when `scenario_state is None` (line 52-53) and otherwise mints a
`KnownFact` **only** when `fn.fact_id` resolves to a `ClueNode` in the bound
`clue_graph` (lines 55-86). So on a mystery world (e.g. glenross) footnotes whose
`fact_id` matches a clue DO write `known_facts` (`confidence='Discovered'`,
`source='ScenarioClue'`); on a no-scenario-graph world the same call is a no-op.
This establishes a **general-knowledge route gap by design**, not a scenario-system
bug.

### AC 2 — verdict with rationale, reconciling ADR-150 and ADR-100

The footnote/`commit_known_fact` split is an **explicit authored contract**, not an
accident. The narrator prompt
(`sidequest-server/sidequest/agents/narrator_prompts/output_only.md:84-89`) tells
the model: *footnotes* are "the player's journal feed; include generously," and are
"Distinct from `commit_known_fact` (which durably commits to party knowledge) — emit
footnotes here AND call `commit_known_fact` when the fact should be durably known."
Branch A (auto-persist every footnote) would **collapse the exact distinction the
prompt establishes**, flooding the durable store with the "include generously" feed
and defeating the narrator's Diamonds-&-Coal judgment of what is worth keeping.

- **Reconciled with the ADR-150 amendment (2026-06-20):** that amendment restored
  `footnotes` to *narrator-owned / generative* precisely because the never-invent
  extractor returned `[]` and starved the scenario clue intake on mystery worlds
  (`orchestrator.py:1343-1347`). It makes footnotes an *authorial narration output*
  — the journal-feed analogue of prose, which is likewise not persisted to
  `known_facts`. It does not create a mandate to persist the feed.
- **Reconciled with ADR-100 (controlling, `partial`):** Component 2 is "the per-turn
  ephemeral channel"; Component 3 (`known_facts`) is written only by deliberate
  paths; *Alternatives Considered* already rejected a "fourth state-mutation
  pathway" and *Consequences → Negative* mandates "deliberate writers only." Branch A
  is exactly that rejected fourth/indiscriminate writer. The durable-Journal-on-cold-
  reload concern is **Seam C** (half-wired; feeder stories 50-14..50-17), which is
  out of scope for this story.

**Therefore (B) WONTFIX.** The narrator already has the deliberate durable path
(`commit_known_fact`, instructed in the prompt) plus the scenario clue hook and
`WorldStatePatch.discovered_facts`. The forensics "discrepancy" (6 Journal entries,
0 `known_facts`, no `KNOWLEDGE` timeline kind) is the two-channel design working as
intended and is already observable on the GM panel via existing watcher events (feed:
`state_transition` field=footnotes + `state.footnote_fact_id_minted` via `_watcher_publish`;
durable mints: `tool.write.commit_known_fact` dispatch span / `SPAN_SCENARIO_ADVANCE`) —
note `state.footnotes_forwarded` is a `logger.info` label, not a watcher event — so no new
timeline event kind is warranted. Contract recorded in ADR-100 (2026-06-22 amendment) and
at the server forwarding seam.

---

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — lint PASS, import PASS, comment block confirmed inert, 0 code smells |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via `workflow.reviewer_subagents.edge_hunter=false` |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via `workflow.reviewer_subagents.silent_failure_hunter=false` |
| 4 | reviewer-test-analyzer | Yes | clean | none | N/A — WONTFIX invariant already pinned by `test_scenario_clue_intake.py:208` (unit) + `test_narration_clue_discovery_wiring.py:163` (integration); no new test needed |
| 5 | reviewer-comment-analyzer | Yes | findings | 1 | **confirmed 1** (the `state.footnotes_forwarded` "span" mislabel — verified independently below) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via `workflow.reviewer_subagents.type_design=false` |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via `workflow.reviewer_subagents.security=false` |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via `workflow.reviewer_subagents.simplifier=false` |
| 9 | reviewer-rule-checker | Yes | clean | none (1 self-"verification" **challenged**) | 18 rules checked, 0 violations; BUT its claim that `state.footnotes_forwarded` is a "live span" is **wrong** — see Challenge below |

**All received:** Yes (4 returned with results, 5 disabled-and-skipped)
**Total findings:** 1 confirmed, 0 dismissed, 0 deferred

### Challenge: rule-checker vs comment-analyzer (resolved with line-level evidence)

The rule-checker (#9) wrote: *"state.footnotes_forwarded — confirmed live at websocket_session_handler.py:1775, emitted by logger.info immediately before the consume_clue_footnotes call ... All three cited spans exist and are wired."* This is **incorrect** and contradicts the comment-analyzer (#5). The rule-checker conflated a log line with a watcher span. My independent read of `websocket_session_handler.py:1757-1789`:
- Line **1774-1778**: `logger.info("state.footnotes_forwarded count=%d player=%s", ...)` — a **log message**, not a watcher event. The GM panel consumes `_watcher_publish` events, not `logger.info` calls.
- Line **1779-1789**: `_watcher_publish("state_transition", {"field": "footnotes", ...}, component="footnotes")` — **this** is the GM-panel-visible feed event.
- Line **1758-1767**: `_watcher_publish("state.footnote_fact_id_minted", {...}, component="footnotes")` — a second real feed watcher event.

Therefore the comment-analyzer is correct and the rule-checker's "verified" is rejected. The feed channel IS observable on the GM panel — but via `state_transition` (field=footnotes) and `state.footnote_fact_id_minted`, **not** via a span called `state.footnotes_forwarded` (which exists only as a log label). The durable-mint side names (`tool.write.commit_known_fact` at `commit_known_fact.py:42`; `SPAN_SCENARIO_ADVANCE="scenario.advance"` at `telemetry/spans/scenario.py:7`) are accurate.

## Reviewer Assessment

**Verdict:** REJECTED (one confirmed accuracy defect in the deliverable; trivial green-rework)

This is a decision-first WONTFIX story whose **sole deliverable is accurate documentation** of a design contract (AC-2 "record the verdict with rationale"; AC-3 Branch B "document the client-reactive-by-design contract"). The decision itself is **sound and well-evidenced** — I independently verified the load-bearing claims (the two-channel design, the narrator prompt's explicit `footnotes`-vs-`commit_known_fact` contract, the `consume_clue_footnotes` no-op-when-scenario-None gate, the cold-reload `load_snapshot`→`_generate_recap` path, and the ADR-136-is-the-NPC-surface correction). But the recorded contract contains a **factual inaccuracy about the observability surface**, and that inaccuracy is the one thing this story exists to get right.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [MEDIUM][DOC] | The deliverable claims the GM panel distinguishes the two channels "via the `state.footnotes_forwarded` span." There is **no such span** — `state.footnotes_forwarded` is a `logger.info` label (`websocket_session_handler.py:1775`), not a watcher event. The GM-panel-visible feed events are `state_transition` (field=footnotes, line 1779) and `state.footnote_fact_id_minted` (line 1758). The underlying claim (the feed is observable, channels distinguishable) is TRUE; only the event name is wrong. Appears in **both** durable artifacts. | `sidequest-server/sidequest/server/websocket_session_handler.py` (new comment, the `state.footnotes_forwarded span` line) AND `docs/adr/100-journal-pipeline-coherence.md` (2026-06-22 amendment, same phrase). Also in this session's Decision Record AC-2 paragraph. | Replace "the `state.footnotes_forwarded` span (this feed)" with a reference to the real watcher event(s): `state_transition` (field=footnotes) — emitted via `_watcher_publish` at `websocket_session_handler.py:1779` — and/or `state.footnote_fact_id_minted` (line 1758). Note `state.footnotes_forwarded` is a `logger.info` label only, not a watcher span. |

**Why this blocks (a Medium that fails the AC):** Normally a Medium does not block. Here it does, because the inaccuracy *defeats a stated acceptance criterion*: AC-2/AC-3 require the contract to be **accurately recorded**, and the story's own stated purpose is "the next forensics reader is not surprised." A GM or forensics reader who trusts ADR-100 and searches the watcher stream for `state.footnotes_forwarded` finds **nothing** — leaving them more surprised, not less. Worse, the error is enshrined in ADR-100, the self-described "front door for journal stories," so every future journal-story author inherits it. The fix is ~2 lines in each of two files. Per project doctrine ("the GM panel is the lie detector" — CLAUDE.md OTEL principle), shipping a wrong watcher-event name into the permanent architectural record is exactly the class of plausible-but-wrong artifact review exists to catch.

**[EDGE]** N/A — subagent disabled; no boundary-condition surface in a comment+markdown diff (verified: no executable paths added).
**[SILENT]** N/A — subagent disabled; no error-handling code added (comment block is inert, confirmed by preflight).
**[TEST]** Clean — the WONTFIX invariant is already pinned by two existing tests (`test_scenario_clue_intake.py:208`, `test_narration_clue_discovery_wiring.py:163`); a Branch-A reversal could not slip in silently. No new test required.
**[DOC]** **CONFIRMED finding (above)** — the `state.footnotes_forwarded` "span" mislabel in both durable artifacts.
**[TYPE]** N/A — subagent disabled; no types/fields/signatures changed.
**[SEC]** N/A — subagent disabled; no auth/input/tenant surface; player-knowledge stays player-side (spoiler firewall untouched, no behavior change).
**[SIMPLE]** N/A — subagent disabled; the change is the minimal artifact (a comment + an ADR note), no over-engineering.
**[RULE]** Clean on 18 rules (0 violations) — but its `state.footnotes_forwarded`-is-a-live-span self-verification is **rejected** (see Challenge above); the corrected fact does not change any rule verdict.

**Data flow traced:** A player action → narrator emits `footnotes` (generative, ADR-150) → `forwarded_footnotes` built (`websocket_session_handler.py:1725-1789`, emits `state_transition`/field=footnotes + optional `state.footnote_fact_id_minted`) → `consume_clue_footnotes` (mints `known_facts` ONLY on a bound-scenario `fact_id` clue match; no-op otherwise) → `NarrationPayload.footnotes` to UI (ephemeral feed). Durable `known_facts` writes flow only from `commit_known_fact` / `WorldStatePatch.discovered_facts` / the scenario hook. The two channels are genuinely independent and fully wired — confirming the WONTFIX is correct (no half-wired feature).

**Pattern observed:** Correct "document-the-deliberate-absence at the seam" pattern at `websocket_session_handler.py:1802` — the right place for a forensics reader. Marred only by the one wrong event name.

**Handoff:** Back to Dev (Naomi Nagata) for a green rework — correct the watcher-event name in the comment + ADR (and the session Decision Record). No logic, no tests to change.

### Devil's Advocate

Let me argue this code/decision is broken. First, the strongest attack on the *verdict itself*: a critic demands Branch A (persist footnotes) because (a) on a cold reload-from-DB the UI Journal vanishes on non-scenario worlds, and (b) the narrator can't "see" what the player knows because `known_facts` is empty and it isn't pre-fed. Does this sink the WONTFIX? No — and I checked. Branch A would not even fix (a): UI Journal rehydration needs the `JOURNAL_RESPONSE` path (Seam C, stories 50-14..50-17), not facts in `known_facts`; dumping footnotes into `known_facts` would leave the UI rebuild path untouched while flooding the durable store with "coal." For (b), the narrator has `query_known_facts` on demand plus recent narration in its stateless-turn context, and the prompt explicitly instructs `commit_known_fact` for durable facts — so "the narrator is blind" is overstated. The decision survives the attack. Second attack: is there a project rule that *demands* wiring the route ("No half-wired features")? The rule-checker and I both concluded no — the existing channels are each fully wired; the "missing" route is an imagined third connection ADR-100 explicitly rejected, and the genuinely-half-wired bit (Seam C) is correctly deferred and tracked. Third attack — and this one lands: a confused GM, told by ADR-100 that the feed is observable "via the `state.footnotes_forwarded` span," opens the watcher/GM panel, filters for that span name, finds nothing, and concludes the feed is NOT instrumented — the precise opposite of the truth, and the precise opposite of this story's purpose. That is not hypothetical; it is what the wrong name guarantees. A stressed reader debugging an empty-Journal report would waste time chasing a span that doesn't exist. Fourth: could the inaccuracy be "close enough"? No — in a project whose core thesis is that span names are ground truth against narrator improvisation, an architectural record that misnames an observability event is the very failure mode the OTEL principle guards against. The decision is right; the documentation of it is not yet correct. Reject, fix the name, ship.

---

## Subagent Results (Round 2 re-review)

Re-review of the rework delta only (commits orchestrator `4e2f1acb`, server `91b0ddae`). Per re-review discipline: independent preflight run by me (not Dev's RUN_ID), the round-1 finding verified closed against the delta with line evidence, and a fresh comment-analyzer pass to confirm the corrected names are accurate and introduce no new inaccuracy.

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes (self, independent) | clean | none | N/A — I ran `ruff check` (PASS), `py_compile` (OK), `import` (OK) on the changed handler myself |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Carried (round 1) | clean | none | Delta is pure comment/markdown text — zero test surface changed; round-1 result (invariant already pinned by `test_scenario_clue_intake.py:208` + `test_narration_clue_discovery_wiring.py:163`) stands |
| 5 | reviewer-comment-analyzer | Yes (re-run on delta) | clean | none | **Round-1 finding CLOSED** — all 4 corrected names re-verified accurate; no new inaccuracy; conditionality of `state.footnote_fact_id_minted` not misrepresented |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Carried (round 1) | clean | none | Delta is pure comment/markdown text — zero rule surface changed; round-1 result (18 rules, 0 violations) stands |

**All received:** Yes (preflight self-run + comment-analyzer re-run; test/rule carried from round 1 — delta has no test/rule surface; 5 disabled)
**Total findings:** 0 new; round-1's 1 confirmed finding is now CLOSED.

## Reviewer Assessment (Round 2)

**Verdict:** APPROVED

The round-1 [MEDIUM][DOC] finding is **closed**, verified by me against the delta diff (not taken on Dev's word) and independently re-confirmed by the comment-analyzer. The corrected text in all three artifacts now names the real GM-panel watcher events:
- **Feed channel:** `state_transition` (field=footnotes) watcher event via `_watcher_publish` (`websocket_session_handler.py:1779`) + the conditional `state.footnote_fact_id_minted` (`:1758`, gated on `fact_ids_minted_this_turn > 0`).
- **Durable mints:** `tool.write.commit_known_fact` dispatch span (`commit_known_fact.py:42`) / `SPAN_SCENARIO_ADVANCE="scenario.advance"` (`telemetry/spans/scenario.py:7`).
- Each artifact now carries an explicit "`state.footnotes_forwarded` is a `logger.info` label, not a watcher event" note (`:1775`) so the next reader can't repeat the conflation — a net improvement over the original.

The rework introduced **no new inaccuracy** (checked the new "above" spatial reference and the unconditional-vs-gated framing — both correct). Independent preflight clean (ruff PASS, py_compile OK, import OK). The change remains comment + markdown only — no behavior change, no test/rule surface touched, so the round-1 test-analyzer (invariant already pinned) and rule-checker (18 rules, 0 violations) results stand. The underlying decision (WONTFIX) was sound from round 1 and is unchanged.

**[EDGE]** N/A (disabled; no boundary surface in a comment+markdown delta).
**[SILENT]** N/A (disabled; no error-handling code; comment block inert, confirmed by preflight).
**[TEST]** Clean — carried from round 1; WONTFIX invariant already pinned by two existing tests; delta changed no test surface.
**[DOC]** **Round-1 finding CLOSED** — corrected event names verified accurate in all three artifacts; explicit log-label-vs-watcher-event note added.
**[TYPE]** N/A (disabled; no types/signatures changed).
**[SEC]** N/A (disabled; no auth/input/tenant surface; no behavior change).
**[SIMPLE]** N/A (disabled; minimal corrective edit, no over-engineering).
**[RULE]** Clean — carried from round 1 (18 rules, 0 violations); delta changed no rule surface.

**Data flow traced (unchanged, re-confirmed):** player action → narrator `footnotes` (generative) → `forwarded_footnotes` (emits `state_transition`/field=footnotes + optional `state.footnote_fact_id_minted`) → `consume_clue_footnotes` (mints `known_facts` ONLY on a bound-scenario `fact_id` match) → `NarrationPayload.footnotes` to UI. Durable `known_facts` writes flow only from the deliberate paths. Two independent, fully-wired channels — the WONTFIX is correct.

**Pattern observed:** The corrected seam comment (`websocket_session_handler.py:1802+`) now documents the deliberate-absence AND the precise observability surface, with a guard against the exact mislabel that was caught — the right artifact for a forensics reader.

**Deviation audit (round 2):** No new deviations introduced by the rework. The round-1 Dev deviation (docs landed in orchestrator ADR + server seam, not `repos: server` only) remains ✓ ACCEPTED. SM: expect a 2-repo finish (orchestrator: ADR-100 + sprint + reviewer sidecar; server: seam comment).

**Handoff:** To SM (Camina Drummer) for finish-story.