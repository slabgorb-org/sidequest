---
story_id: "117-5"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 117-5: Coherence — project the accepted quest's lore into a tracked picture

## Story Details
- **ID:** 117-5
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** 117-3 (depends_on)
- **Points:** 5
- **Repo:** server

## Workflow Tracking
**Workflow:** tdd
**Phase:** setup
**Phase Started:** 2026-06-15T03:21:45Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-15T03:21:45Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Reviewer (code review)
- **Gap** (blocking): Empty-string `anchor_id` is not treated as "no anchor". `_related_lore_for_anchor` (`game/projection/quests.py:52`) guards only `if anchor_id is None`, so `anchor_id == ""` falls through to `clue_ids_by_anchor.get("", ())` and coheres any clue keyed under `""`. Empirically reproduced: a quest with `anchor_id=""` + a clue node with `locations=[""]` pulls that clue's discovered fact under the wrong quest. Reachable because `quest_offer.mint` (`game/quest_offer.py:103`) stores `anchor_id=seed.anchor` even when `QuestSeed.anchor==""`, and a narrator `record_quest` can emit an empty anchor. Fix: change the guard to `if not anchor_id:` (and ideally skip `if not body_id` empty elements when indexing at `quests.py:84`, plus mirror at the `anchor_owner` loop `quests.py:117`). *Found by Reviewer during code review.*
- **Gap** (non-blocking): OTEL `lore_count` is dropped from the typed `quests.emitted` event. `_maybe_emit_quests` (`server/websocket_handlers/quests_emit.py`) sets `lore_count` on the span, but the route extractor (`telemetry/spans/quests.py:22-28`) projects only quest_count/anchor_count/has_stakes/changed — so the typed `state_transition` event the GM panel consumes lacks `lore_count`. It survives only on the flat `agent_span_close` firehose. Extend the `extract` lambda to include `lore_count` for parity with its siblings, so the projection's lie-detector is visible on the structured quest event. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): No test asserts the source-filter is load-bearing as a *discriminator*. A `GameEvent` fact whose `fact_id` collides with a real clue id is correctly excluded today (verified empirically), but a future refactor dropping the `source != "ScenarioClue"` check would not be caught — add a colliding-fact_id exclusion test. Also no test asserts `lore_count` on the emit span, and none covers the empty-string-anchor case above. *Found by Reviewer during code review.*

### Dev (implementation)
- **Gap** (non-blocking): The new `related_lore` field reaches the wire but the UI does NOT render it. `sidequest-ui/src/types/payloads.ts` `QuestLogEntry` has no `related_lore` field, and `QuestsPanel.tsx` renders only title/status/objective/anchor-resolution — the cohered lore is silently dropped at the client. Keith won't SEE the coherence until a follow-up UI story adds (1) `related_lore: QuestLoreEntry[]` to the TS interface and (2) a render branch under each quest entry. Server-only story per brief, so logged for a follow-up decision.

### TEA (test design)
- **Gap** (blocking-for-design): There is NO structural field linking a `KnownFact` to a quest. `KnownFact` (`game/character.py:35`) carries only `content/confidence/source/learned_turn/fact_id/category` — no `anchor_id`, no `quest_id`. The ONLY deterministic join that exists today is the three-hop chain **`QuestEntry.anchor_id` → `ClueNode.locations[]`/`implicates[]` → `KnownFact.fact_id` (for `source=="ScenarioClue"` facts, where 50-14 sets `fact_id == clue_id`)**. Dev must build the projection on this chain. The tests assert exactly this mechanism.
- **Gap** (non-blocking): The chain only coheres **ScenarioClue-sourced** lore. Generic narrator-emitted KnownFacts (`source="GameEvent"`, default uuid4 `fact_id`) have no anchor tie and will NOT surface under any quest — by design (test `test_unrelated_lore_is_not_misattributed` locks this: no false coherence). If the playgroup symptom includes non-scenario lore, that is a SEPARATE follow-up (would need narrator to tag facts with an anchor id, e.g. emit `fact_id == anchor_id` or a new `KnownFact.anchor_id` field). Flagging loudly so Dev does NOT silently broaden the match to fuzzy text to "catch more" — that reintroduces the Zork/keyword anti-pattern ADR-100 rejects. Keep the join structural.
- **Question** (non-blocking): The carrier field on `QuestLogEntry` is Dev's call (`related_lore` assumed; test accessor `_lore_under` also accepts `learned_lore`/`lore`/`known_facts`). `QuestLogEntry` is `extra="forbid"` (`protocol/models.py:893`) so it MUST be a real typed field, and `QuestsPayload`/`QuestLogEntry` are server-owned protocol — adding a field is a UI-contract change (QuestsPanel consumes it). Whatever shape Dev picks, each lore entry needs a readable `.content` (test reads `.content` or falls back to `str(e)`).
- **Improvement** (non-blocking): The accusation walk (`server/dispatch/scenario_accusation.py:106`) still carries a STALE comment claiming "KnownFact does not currently carry an originating clue id" and uses brittle parallel-iteration. 50-14 made `fact_id == clue_id` for ScenarioClue facts, so that fallback is now obsolete. Out of scope for 117-5 but worth a follow-up — and it is the precedent that proves the fact→clue recovery this story inverts.
- **Improvement** (non-blocking): No OTEL span on this projection yet. Per CLAUDE.md OTEL principle, Dev should emit a span when lore is cohered under a quest (e.g. `quest_lore.cohered` with `quest_id`, `lore_count`) so the GM panel can verify the coherence engaged rather than the narrator improvising. The existing `quests.emitted` span (`quests_emit.py:74`) is a candidate to extend with a `lore_count` attribute.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **No AC existed; TEA defined them.** Context-story-117-5.md recorded "No acceptance criteria — TEA to define during RED." Defined 5 ACs (a–e) from the story title + ADR-146 §117-5 pointer ("coheres lore fragments under the now-minted QuestEntry, ADR-053 + ADR-100"): (a) related lore surfaces under its quest, (b) unrelated lore not mis-attributed, (c) multi-quest partition, (d) empty-clean/no-crash, (e) wiring through the real `_maybe_emit_quests` emit path.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/protocol/models.py` - new `QuestLoreEntry` model (fact_id + content); `related_lore: list[QuestLoreEntry]` field added to `QuestLogEntry` (extra="forbid", real typed field — UI-contract change)
- `sidequest/game/projection/quests.py` - structural anchor→clue→fact join in `build_quests_payload`; `_related_lore_for_anchor` helper
- `sidequest/server/websocket_handlers/quests_emit.py` - `lore_count` attribute added to the `quests.emitted` OTEL span + log line

**Join:** For each quest, `anchor_id` → clue nodes whose `locations`/`implicates` contain it → clue ids → discovered `KnownFact`s (across all characters) with `source=="ScenarioClue"` and `fact_id == clue_id` (50-14). Deterministic, structural, no fuzzy text. ScenarioClue-only; generic facts excluded. No scenario_state / no anchor / nothing learned → clean empty list.

**Tests:** 7/7 passing (GREEN), serial `-n0`. Broader quest+projection suites: 365 passed, 8 skipped, no regressions.
**Branch:** feat/117-5-quest-lore-coherence-projection (not pushed)

**UI finding:** QuestsPanel does NOT auto-render `related_lore` — follow-up UI story needed (see Delivery Findings).

**Handoff:** To review.

## Design Deviations

### Dev (implementation)
- No deviations. Field named `related_lore` as TEA assumed; lore-entry shape is `{fact_id, content}` (TEA's `.content` accessor satisfied; `fact_id` added for UI dedup against the KnownFacts surface).

## TEA Assessment

**Tests Required:** Yes
**Reason:** New player-facing projection behavior (lore coherence under quests).

**Test Files:**
- `tests/server/test_quest_lore_coherence.py` — 7 tests, synthetic fixtures only (no content-pack dependency).

**Join mechanism (the crux):** structural three-hop chain
`QuestEntry.anchor_id` → `ClueNode.locations[]`/`implicates[]` (`genre/models/scenario.py:100`)
→ `KnownFact.fact_id` for `source=="ScenarioClue"` facts (`character.py:35`, `fact_id==clue_id` per 50-14
`server/dispatch/scenario_clue_intake.py:83`). Deterministic, refactor-stable, NOT fuzzy text.

**Tests Written:** 7 tests covering 5 ACs:
- `test_related_lore_surfaces_under_its_quest` (a, via locations)
- `test_related_lore_via_implicated_npc_anchor` (a, via implicates)
- `test_unrelated_lore_is_not_misattributed` (b — loose fact + wrong-body clue)
- `test_multiple_quests_partition_their_lore` (c)
- `test_quest_with_no_related_lore_is_clean_empty` + `test_no_scenario_bound_is_clean_empty` (d)
- `test_quests_emitter_broadcasts_lore_end_to_end` (e — WIRING, drives real `_maybe_emit_quests`)

**Status:** RED (7 failed, feature-absence — `QuestLogEntry carries no related-lore field`; all imports resolve, no collection errors). Pre-existing WWN/content-drift failures ignored per brief.

**Commit:** `fe5066dd` on `feat/117-5-quest-lore-coherence-projection` (not pushed).

**Handoff:** To Dev for implementation. Build the coherence on the structural anchor→clue→fact chain; add a typed `related_lore` field to `QuestLogEntry`; emit an OTEL span; keep generic (non-ScenarioClue) facts OUT (no false coherence). Do NOT fall back to fuzzy text matching.

## Reviewer Assessment (round 1 — REJECTED, superseded)

**Verdict:** REJECTED (one blocking defect — single-line fix)

**Data flow traced:** player learns a clue → `scenario_clue_intake` mints `KnownFact(source="ScenarioClue", fact_id==clue_id)` on a Character → `build_quests_payload` indexes `clue_ids_by_anchor` (body id → clue ids, from `ClueNode.locations`/`implicates`) and `facts_by_clue_id` (clue id → discovered fact), then per quest joins `anchor_id → clue ids → facts` into `related_lore` → broadcast on the `QuestsMessage` the UI consumes. Verified end-to-end via the real `_maybe_emit_quests` wiring test and two hand-built probes.

**Pattern observed:** indices built once per call (O(nodes + facts) preprocessing, then O(clues-per-anchor) per quest) — NOT the O(quests × facts × clues) Dev was warned against. `game/projection/quests.py:78-96`. Good.

**Error handling:** missing scenario_state / clue_graph / characters all degrade to clean-empty via `getattr(...)` + `is not None` guards (`quests.py:79-88`). Source filter + partition exactness empirically verified (colliding `GameEvent` fact_id excluded; `None`-anchor quest gets nothing). Production snapshot is always a hydrated `GameSnapshot`, so the bare `node.*`/`fact.*` attribute access is Pydantic-guaranteed — the silent-failure-hunter's AttributeError "blocking" claims are theoretical (dict-backed snapshots don't reach this path) and downgraded to nit.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] blocking | Empty-string `anchor_id` not treated as no-anchor; `if anchor_id is None` lets `""` match clues keyed under `""` (false coherence; empirically reproduced) | `game/projection/quests.py:52` | Change guard to `if not anchor_id:`; ideally `if not body_id: continue` at the index loop (`:84`) and mirror at `anchor_owner` (`:117`) |
| [MEDIUM] non-blocking | Typed `quests.emitted` event drops `lore_count` (extractor omits it); GM panel's structured quest view can't see the projection's lie-detector — only the flat firehose carries it | `telemetry/spans/quests.py:22-28` | Add `lore_count` to the `extract` lambda |
| [LOW] non-blocking | Source-filter discriminator + empty-anchor + emit-span `lore_count` are untested; a refactor dropping `source != "ScenarioClue"` wouldn't be caught | `tests/server/test_quest_lore_coherence.py` | Add a colliding-fact_id exclusion test, an empty-anchor test, and assert the OTEL span attr |
| [LOW] nit | `# type: ignore[arg-type]` on `.get(anchor_id, ())` — default `()` (tuple) mismatches declared `set[str]` value type | `game/projection/quests.py:55` | Use `set()` default, drop the ignore |
| [LOW] nit | Bare `node.*`/`fact.*` access in an `Any`-typed fn; safe in production (hydrated GameSnapshot) but inconsistent with the `getattr(...) or []` style used for the top-level collections | `game/projection/quests.py:84,90` | Optional: defensive `getattr` for consistency |
| [LOW] nit | `clue_graph is not None else []` is dead-defensive — `ScenarioState.clue_graph` has `default_factory=ClueGraph`, never None on a valid instance | `game/projection/quests.py:82` | None needed; harmless |

**Observations (6):** join is structural/deterministic (no fuzzy text — ADR-100 anti-pattern avoided); ScenarioClue-only scope is real and verified; partition is exact for non-empty anchors; indices are built once (perf fine); QuestLoreEntry is `extra="forbid"` + additive default-factory field (existing QUESTS contract unbroken); dedup-across-characters via `setdefault` keeps first-seen content (fine under 50-14's same-content-per-clue contract). The ONE correctness hole is the empty-string anchor.

**Deviation audit:** Dev "no deviations" — confirmed ACCEPTED. Field named `related_lore` with `{fact_id, content}` shape matches TEA's assumption and `.content` accessor. No undocumented deviations found.

**Handoff:** Back to Dev for the one-line empty-anchor guard fix (`if not anchor_id:`); the OTEL `extract` parity fix and the test additions are non-blocking but recommended in the same pass. UI render gap is a known out-of-scope follow-up (not a reject reason).

## Reviewer Assessment

**Verdict:** APPROVED

**Re-review scope:** focused on fix commit `cf330a75` after the round-1 REJECT (empty-anchor wildcard + OTEL parity).

**1. Empty-anchor wildcard — genuinely closed (two-layer defense, empirically verified across all paths):**
- Guard fix: `_related_lore_for_anchor` now `if not anchor_id: return []` (`game/projection/quests.py:58`) — catches `""` and `None`.
- Index fix: `if not body_id: continue` (`quests.py:91-93`) — empty body ids in `locations[]` OR `implicates[]` are never indexed, so no `""` key exists to match.
- anchor_owner fix: `if entry.anchor_id` (truthy) (`quests.py:129`) — an empty anchor never claims a `QuestAnchorEntry`.
- Probed the full matrix: empty body in locations only / implicates only / both, with `anchor_id==""` and `anchor_id==None` → all cohere `[]` and claim no anchor entry. No path lets `""` act as a wildcard. Either layer alone closes it; both together is robust.

**2. lore_count reaches the typed GM-panel event — confirmed:** `lore_count` added to the `quests.emitted` SpanRoute `extract` lambda (`telemetry/spans/quests.py:27-31`), so the typed `state_transition` event the GM panel consumes now carries it (previously only the flat `agent_span_close` firehose did). The new `test_quests_emitted_span_carries_lore_count` monkeypatches `sidequest.telemetry.spans.tracer` — the exact tracer `Span.open` resolves via `_spans.tracer()` (`spans/span.py:33`) — drives the REAL `_maybe_emit_quests`, and asserts the span carries `lore_count == 1`. Non-vacuous, real wiring.

**3. No new issue from the guard/index changes:** the truthiness guards are strictly narrowing (falsy anchors/body-ids were the bug); non-empty anchors behave identically to before. `test_routing_completeness` still passes after the extract change. 404 passed across the lore + full telemetry suites (`-n0`), lint clean on all three changed files, no regressions.

**Still-open non-blocking items (NOT reject reasons, follow-up):**
- **UI render gap** (Dev's own finding): `sidequest-ui` `QuestLogEntry` TS type + `QuestsPanel.tsx` do not yet render `related_lore`; Keith won't SEE the coherence until a follow-up UI story. Known, out-of-scope for this server-only story.
- **Nits (cosmetic, optional):** `# type: ignore[arg-type]` on `.get(anchor_id, ())` could use a `set()` default; bare `node.*`/`fact.*` access is safe under the hydrated-GameSnapshot production contract but inconsistent with the `getattr(...) or []` style used for top-level collections.

**Deviation audit:** no new deviations; fix matches the prescribed remediation exactly.

**Handoff:** To SM for finish-story.
