---
story_id: "118-1"
jira_key: ""
epic: "118"
workflow: "tdd"
---
# Story 118-1: F3a — FATE_STATE reactive projection + wire message (the spine)

## Story Details
- **ID:** 118-1
- **Jira Key:** none
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-15T10:11:11Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-15T09:32:36Z | 2026-06-15T09:34:50Z | 2m 14s |
| red | 2026-06-15T09:34:50Z | 2026-06-15T09:53:22Z | 18m 32s |
| green | 2026-06-15T09:53:22Z | 2026-06-15T10:03:21Z | 9m 59s |
| review | 2026-06-15T10:03:21Z | 2026-06-15T10:11:11Z | 7m 50s |
| finish | 2026-06-15T10:11:11Z | - | - |

## Sm Assessment

**Repos:** server (sidequest-server, base branch `develop`)
**Branch:** feat/118-1-fate-state-projection
**Jira:** none (jira field null — skip all Jira steps)

**Story:** F3a — the *spine* of epic 118 (F3 Fate Core UI surfaces, ADR-144). First on the critical path F3a→F3b; nothing upstream blocks it. F1 + F2 are done.

**What it is (server-only, NO UI):**
- Promote `build_fate_projection()` into a full client payload: per-PC fate_points/refresh, skills→ladder, all aspects (kind + free-invoke counts), stress boxes, consequence slots; scene situation aspects+boosts; conflict sides/turn order.
- New `FATE_STATE` GameMessage + payload in `protocol/`, modeled on the existing `RELATIONSHIPS`/`QUESTS` reactive projections.
- On-change emitter gated on `pack.rules.ruleset == 'fate'` — Cost-Scales-with-Drama, **NOT** per-turn.
- `fate.projection.emitted` OTEL span.

**Architectural mirror (load-bearing for TEA):** ADR-136 RELATIONSHIPS reactive projection is the template — same reactive full-replace projection shape, same on-change (not per-turn) emit discipline, same player-facing-math mandate (Sebastien/Jade legibility — this is a *player-UI* mandate satisfied by the payload contents, not an OTEL/GM-panel concern).

**Likely files:** `game/ruleset/fate_projection.py`, `game/fate_sheet.py`, `protocol/`, `telemetry/spans/fate.py`.

**Gate watch for TEA:** the `ruleset=='fate'` gate matters — the projection must never fire for WN/native packs (a negative test is warranted). Don't reintroduce a per-turn emit.

**Routing:** TDD/phased → handing off to The Architect (TEA) for the RED phase to define acceptance criteria and write failing tests.

## TEA Assessment

**Phase:** finish
**Tests Required:** Yes
**Reason:** F3a is a 5-pt server feature — a new wire message + a rich projection builder + a reactive emitter. Pure RED→GREEN.

**Test Files:**
- `tests/protocol/test_fate_state_message.py` (8) — `MessageType.FATE_STATE`; `FateStatePayload` + nested `FateCharacterEntry`/`FateSkillEntry`/`FateAspectEntry`/`FateStressBox`/`FateConsequenceEntry`/`FateConflictEntry`/`FateConflictParticipant` (all `extra="forbid"`); `FateStateMessage`; GameMessage union membership + raw-wire discriminator parse.
- `tests/game/ruleset/test_fate_state_projection.py` (14) — `build_fate_state_payload(snapshot)`: points/refresh, skills→ladder (incl. **negative rung** -1→"Poor"), aspects+kind+free_invokes (**named-only**, filled consequences not duplicated), stress boxes (value+checked), consequence open/filled, scene situation aspects **+ boosts**, conflict participants by side in **seating order**, resolved-encounter gate, PC-without-sheet omitted, live-reads-not-frozen, **+ compact `build_fate_projection` regression guard**.
- `tests/server/test_fate_state_emit.py` (8) — `_maybe_emit_fate_state`: happy path, **ruleset gate paired negatives (native + wwn)**, change-gate (unchanged skip / fate-point re-fire), fresh-handler first-emit (reconnect), empty no-op, signature-committed-only-after-broadcast.
- `tests/server/test_fate_state_emit_wiring.py` (5) — `fate.projection.emitted` OTEL span (+ no-span-when-gated-off), emitter imported into AND called from `_execute_narration_turn` (reflection, not source-grep), transient/replay invariant.

**Tests Written:** 35 tests across 10 ACs.
**Status:** RED — **33 failing** (missing impl: `FateStateMessage`/`FateStatePayload`/`build_fate_state_payload`/`fate_state_emit` module) **+ 2 guards green** (compact `build_fate_projection` contract intact; `FATE_STATE` correctly absent from replay maps). Verified failures are `ImportError`/`ModuleNotFoundError`/wiring-`AssertionError` — missing implementation, not test bugs.

### Acceptance Criteria (TEA-defined, RED)
- **AC1** `MessageType.FATE_STATE` + `FateStateMessage(payload: FateStatePayload, player_id="")` exist and are members of the `GameMessage` discriminated union (routable on the wire).
- **AC2** `FateStatePayload` (+ every nested model) is `extra="forbid"`; an empty payload is well-formed (`characters=[]`, `scene_aspects=[]`, `conflict=None`).
- **AC3** `build_fate_state_payload(snapshot) -> FateStatePayload` projects per-PC `fate_points` + `refresh`, reading live state.
- **AC4** skills carry `rating` AND `ladder` label via `fate_resolution.ladder_name` (negative rungs preserved — no `Field(ge=0)`).
- **AC5** named character aspects carry `kind` + `free_invokes`; filled consequences are NOT duplicated into `aspects`.
- **AC6** stress tracks project as ordered checkable boxes (`value`, `checked`); both `physical`/`mental` present.
- **AC7** four consequence slots project with `level`/`value`/`filled`/`text` (open vs filled).
- **AC8** scene situation aspects + boosts project (with kind + free_invokes), gated on an unresolved encounter.
- **AC9** active conflict projects participants by `side` in seating order; `conflict is None` with no/resolved encounter.
- **AC10** the emitter is `ruleset=='fate'`-gated (never fires for native/WN), change-gated (on-change NOT per-turn), fires `fate.projection.emitted`, is transient, and is wired into `_execute_narration_turn`.

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| Boundary input validation (python #8/#11 — extra=forbid on the wire model) | `test_payload_forbids_unknown_fields`, `test_nested_models_forbid_unknown_fields` | failing |
| No Silent Fallbacks (SOUL — gate must fail loud, not silently emit) | `test_emit_skipped_for_native_pack`, `test_emit_skipped_for_without_number_pack` | failing |
| No stale-skip (commit signature only after delivery) | `test_signature_not_committed_when_emit_raises` | failing |
| Wiring, not existence (CLAUDE.md — reflection, no source-text grep) | `test_emitter_is_wired_into_session_handler`, `test_emitter_is_called_from_narration_turn` | failing |
| OTEL on every subsystem decision (CLAUDE.md — GM-panel lie detector) | `test_emit_fires_fate_projection_emitted_span`, `test_no_span_when_gated_off` | failing |
| One source of truth (compact projection unchanged) | `test_compact_build_fate_projection_contract_is_unchanged` | green (guard) |
| Test quality / no vacuous asserts (python #6) | ladder-label inequality guard inline | n/a |

**Rules checked:** 6 of 6 applicable (the rest of the python lang-review checklist — async, resource leaks, path handling, deserialization — don't apply to a pure pydantic projection + in-memory emitter).
**Self-check:** 0 vacuous tests — every test asserts a specific value; added an explicit vacuity guard on the ladder labels (`Fight.ladder != Notice.ladder`).

**Handoff:** To Agent Smith (Dev) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/protocol/enums.py` — added `MessageType.FATE_STATE`.
- `sidequest/protocol/models.py` — added `FateStatePayload` + 6 nested models (`FateCharacterEntry`/`FateSkillEntry`/`FateAspectEntry`/`FateStressBox`/`FateConsequenceEntry`/`FateConflictEntry`/`FateConflictParticipant`), all `extra="forbid"`.
- `sidequest/protocol/messages.py` — added `FateStateMessage`, imported `FateStatePayload`, added the message to the `GameMessage` (`_Phase1Variant`) discriminated union.
- `sidequest/game/ruleset/fate_projection.py` — added `build_fate_state_payload(snapshot) -> FateStatePayload` (the rich sibling); compact `build_fate_projection` left untouched (one source of truth).
- `sidequest/server/websocket_handlers/fate_state_emit.py` (NEW) — `_maybe_emit_fate_state` (ruleset=='fate'-gated + change-gated reactive emitter, sig committed only after broadcast).
- `sidequest/server/websocket_session_handler.py` — imported + called `_maybe_emit_fate_state` from `_execute_narration_turn` (`sd=sd`, transient `_emit_shared_world_frame` broadcast), beside the quests/relationships emitters.
- `sidequest/telemetry/spans/fate.py` — added `SPAN_FATE_PROJECTION_EMITTED = "fate.projection.emitted"` + a `SPAN_ROUTES` entry + `__all__` export (GM-panel routing).
- `tests/protocol/test_enums.py` — bumped the `MessageType` count guard 55→56 (and corrected the stale "All 46"→"All 56" docstring header) for the intentional FATE_STATE addition.

**Tests:** 35/35 new tests passing (GREEN). Regression-clean — **139 passed** across fate/protocol/telemetry suites (incl. the compact-projection one-source-of-truth guard, the routing-completeness lint, and the sibling quests/relationships emit-wiring tests). New/changed source files are **pyright-clean**; the 28 pre-existing pyright errors in `websocket_session_handler.py` are unchanged by my edits (28 with AND without).

**Branch:** feat/118-1-fate-state-projection (pushed)

**Implementation notes (followed TEA's pinned contract):**
- Aspect display text is presented RAW (TEA finding #1) — the payload feeds the UI (React-escaped), not the narrator prompt; the compact projection remains the sanitized prompt path.
- `fate.projection.emitted` is registered in `SPAN_ROUTES` (TEA finding #2) so the GM panel surfaces the emit and the routing-completeness lint passes.
- Builder lives in `game/ruleset/fate_projection.py` per the story authority (TEA finding #3), co-located with the compact projection.

**Handoff:** To next phase (verify/review per workflow).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (1 structural note) | confirmed 0, dismissed 0, deferred 0 — note resolved as consistent-with-sibling |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings (self-assessed) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings (self-assessed) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings (self-assessed) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings (self-assessed) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (self-assessed) |
| 7 | reviewer-security | Yes | clean | 0 (1 design caveat) | confirmed 0, dismissed 0, deferred 0 — caveat recorded as forward note |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings (self-assessed) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings (self-assessed) |

**All received:** Yes (2 enabled subagents — preflight + security — returned clean; 7 disabled via `workflow.reviewer_subagents`, self-assessed in Rule Compliance + Devil's Advocate below)
**Total findings:** 0 confirmed, 0 dismissed, 0 deferred (2 non-blocking design notes recorded)

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** player-authored aspect text (`FateSheet.aspects` / `encounter.situation_aspects`) → `build_fate_state_payload` → `FateStatePayload` → `FateStateMessage` → `_emit_shared_world_frame` (WebSocket broadcast) → React UI (HTML-escaped). Safe because this wire path NEVER re-enters an LLM prompt: `build_fate_state_payload` has zero callers outside `fate_state_emit.py` (independent grep + `[SEC]` confirm), and the narrator prompt's `context.fate_state` is hardwired to the SANITIZING `build_fate_projection` (session_helpers.py:1261-1264). ADR-047 satisfied by structural isolation.

**Pattern observed:** the projection + emitter mirror the ADR-136 RELATIONSHIPS / ADR-137 QUESTS reactive-projection siblings exactly — builder in the projection layer, `_maybe_emit_*` change-gated on a `model_dump_json()` signature, transient `_emit_shared_world_frame` broadcast, OTEL emit span. `fate_state_emit.py:42-80` follows the SAFER quests ordering (signature committed AFTER broadcast).

**Error handling:** the gate `sd.genre_pack.rules.ruleset != "fate"` returns cleanly (consistent with the unguarded `sd.genre_pack` invariant at wsh:871–1491, incl. the identical read at 1491 preceding the emit at 2390); empty-characters returns a no-op; `emit_fn` exceptions propagate and leave the signature uncommitted so the next turn retries (pinned by `test_signature_not_committed_when_emit_raises`). No swallowed errors.

### Observations

1. `[VERIFIED]` ADR-047 not bypassed — `build_fate_state_payload` raw text never reaches an LLM. Evidence: zero callers outside `fate_state_emit.py`; `context.fate_state = build_fate_projection(...)` (sanitizing) at session_helpers.py:1261-1264. `[SEC]` corroborates with the same trace.
2. `[VERIFIED]` All 8 new wire models carry `model_config = {"extra": "forbid"}` (models.py:966–1071) and `FateStateMessage` inherits it from `ProtocolBase` (base.py:53). Boundary validation intact. `[SEC]` corroborates.
3. `[PRE]` `[LOW]` `Span.open(...)` fires before `emit_fn` (records the projection decision, not delivery) — fate_state_emit.py:62. CONFIRMED consistent with both siblings (quests_emit.py:80→101, relationships_emit.py:82→90). Intentional pattern; self-heals on retry. Non-blocking.
4. `[SEC]` `[LOW]` Global broadcast exposes every seated PC's full Fate sheet to all clients — fate_state_emit.py:70. CONFIRMED correct for the co-op audience: Fate aspects are table-public (Fate Core SRD) and ADR-036 peer-visibility; matches the RELATIONSHIPS/QUESTS broadcast. Forward note: a hidden-sheet/PvP mode (not implemented) would need per-recipient filtering.
5. `[VERIFIED]` Wiring end-to-end — `_maybe_emit_fate_state` imported (wsh:222-224) and called from `_execute_narration_turn` (wsh:2390, `sd=sd`). The reflection test (`test_emitter_is_called_from_narration_turn`) + independent grep confirm.
6. `[VERIFIED]` Transient/replay-safe — `FATE_STATE` absent from `session_handler._KIND_TO_MESSAGE_CLS` and `_REPLAY_SKIP_KINDS` (independent grep). Mirrors LOCATION_DESCRIPTION/QUESTS.
7. `[VERIFIED]` One source of truth preserved — compact `build_fate_projection` untouched (`test_compact_build_fate_projection_contract_is_unchanged` green; `[PRE]` regression 323 passed).
8. `[EDGE]` (self-assessed; edge-hunter disabled) Boundary inputs handled: empty skills/stress/consequences → empty collections; out-of-ladder ratings handled by `ladder_name` (>8 → "Legendary+N", <-2 → "Terrible-N"); resolved encounter → `conflict=None` + `scene_aspects=[]`. No crash paths.
9. `[TEST]` (self-assessed; test-analyzer disabled) 35 tests with meaningful assertions, paired ruleset-gate negatives (native + wwn), a vacuity guard on the ladder labels, and the sig-after-broadcast test. No vacuous assertions.
10. `[TYPE]` (self-assessed; type-design disabled) Wire DTOs use plain `str` for enum-ish fields (`kind`/`level`/`side`) — consistent with the sibling `QuestLogEntry.status: str`; the game layer (`FateSheet`) keeps the strict Literals. Acceptable DTO flattening, not stringly-typed drift.
11. `[DOC]` (self-assessed; comment-analyzer disabled) Docstrings accurate and thorough; the stale "All 46" enum-count header was corrected to "All 56". No misleading comments.
12. `[SIMPLE]` (self-assessed; simplifier disabled) No over-engineering — the builder is a direct projection and the emitter mirrors the sibling. No dead code.
13. `[RULE]` (self-assessed; rule-checker disabled) See Rule Compliance below — all applicable python lang-review + SOUL/CLAUDE rules pass.

### Rule Compliance

Python lang-review checklist (`.pennyfarthing/gates/lang-review/python.md`) + SOUL/CLAUDE rules, enumerated against the diff:

| Rule | Instances | Verdict |
|------|-----------|---------|
| #1 Silent exception swallowing | no `try/except` in new code | PASS |
| #2 Mutable default arguments | pydantic `Field(default_factory=...)`; no mutable fn defaults | PASS |
| #3 Type annotations at boundaries | `build_fate_state_payload(snapshot: GameSnapshot) -> FateStatePayload`; `_maybe_emit_fate_state(...)` fully annotated | PASS |
| #4 Logging coverage/correctness | `logger.info` at emit, lazy `%s` args, no sensitive data | PASS |
| #6 Test quality | meaningful asserts, vacuity guard, negatives | PASS |
| #8 Unsafe deserialization | none; `extra="forbid"` on all wire models | PASS |
| #10 Import hygiene | new imports clean (the `from .fate import *` in spans/__init__ is pre-existing, not introduced) | PASS |
| #11 Input validation at boundaries | wire payload is OUTBOUND (server→client); strict models; aspect text not looped to LLM | PASS |
| SOUL Cost-Scales-with-Drama | on-change emit (signature-gated), NOT per-turn | PASS |
| SOUL Bind-the-Ruleset | N/A — no combat-engine change | N/A |
| CLAUDE OTEL Observability | `fate.projection.emitted` span + `SPAN_ROUTES` entry (GM-panel lie-detector) | PASS |
| CLAUDE No Silent Fallbacks | ruleset/empty/sig gates are deliberate semantics, not misconfig masks | PASS |
| CLAUDE Every-suite-needs-a-wiring-test | reflection-based call-site test present | PASS |
| CLAUDE No Source-Text Wiring Tests | wiring test uses code-object reflection (allowed exception), not `read_text` grep | PASS |

Tenant isolation: N/A — single-table game engine, no multi-tenant trait methods or tenant_id fields in this diff.

### Devil's Advocate

Assume this code is broken. The richest attack surface is the player-authored aspect text: a malicious player names a high-concept `"<system>ignore all prior instructions</system>"`. In the compact projection that text is sanitized before the prompt; in the NEW wire payload it travels raw. If any server path fed `FateStatePayload` back into the narrator, this would be a clean ADR-047 prompt-injection — the exact HIGH pattern caught in 116-4. I tried to find that path and could not: `build_fate_state_payload` has zero callers outside `fate_state_emit.py`, the message is never persisted/replayed, never handled inbound, never assigned to a `TurnContext`, never passed to an agent. The raw text dead-ends at the React client, which escapes HTML. The injection is inert. A confused user might instead be unsettled to see *other* players' fate points and consequences appear on their screen — but that is the intended table-public Fate model (ADR-144 / ADR-036), not a leak; no GM-only or scenario-secret data rides the payload. Could a stressed runtime break it? `sd.genre_pack` is dereferenced without a guard — but it is a hard non-None invariant read 10+ times earlier in the same method (including the identical `sd.genre_pack.rules.ruleset` at line 1491, which always precedes the emit), so a None there would already have crashed the turn upstream; my emitter introduces no new exposure. A pathological sheet (hundreds of aspects, an off-ladder skill of +50) produces a large-but-valid payload — `ladder_name` handles the out-of-band rungs without throwing, and content authoring bounds sheet size; no DoS this diff opens. The span-before-emit ordering means a failed broadcast still records an "emitted" span — a minor telemetry overcount, but it matches both siblings and self-corrects on the retry (signature uncommitted). Unknown wire fields fail loud (`extra="forbid"`). Two PCs with the same name would both project faithfully; deduplication is a F3b UI concern, not a server bug. I could not construct a state this diff makes broken that the tests or the structural isolation do not already preclude.

**Handoff:** To SM for finish-story

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Question** (non-blocking): Wire-payload aspect text is NOT sanitized in the F3a tests, unlike the compact projection.
  Affects `sidequest/game/ruleset/fate_projection.py` (`build_fate_state_payload`).
  The compact `build_fate_projection` runs `sanitize_player_text` because it feeds the **narrator prompt** (ADR-047). The rich `FATE_STATE` payload feeds the **UI display**, not the LLM — so I pinned raw text (preserves player legibility; React escapes HTML). Dev/Reviewer should confirm: if any consumer ever loops this payload's text back into a prompt, it must sanitize at that seam. *Found by TEA during test design.*
- **Improvement** (non-blocking): The `fate.projection.emitted` span will trip the routing-completeness lint if added as a `SPAN_*` module constant.
  Affects `sidequest/telemetry/spans/fate.py` and `tests/telemetry/test_routing_completeness.py`.
  Mirror the quests pattern — register `SPAN_ROUTES["fate.projection.emitted"] = SpanRoute(...)` so the GM panel surfaces the emit (the lint inspects `SPAN_*` constants). *Found by TEA during test design.*
- **Question** (non-blocking): Builder location follows the story, not the sibling convention.
  Affects `sidequest/game/ruleset/fate_projection.py` vs `sidequest/game/projection/`.
  Tests import `build_fate_state_payload` from `game/ruleset/fate_projection` (story-named file, co-located with the compact projection). RELATIONSHIPS/QUESTS builders live in `game/projection/`. If Dev/Architect prefer `game/projection/fate.py` to match siblings, that's a deviation requiring the test import to move. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): `websocket_session_handler.py` carries 28 pre-existing pyright errors (e.g. lines 3360/3369, `subject` on an Optional) unrelated to this story.
  Affects `sidequest/server/websocket_session_handler.py` (Optional-narrowing cleanup).
  Verified my edits add ZERO new errors (28 with AND without my changes); flagging only so the debt is on record. TEA findings #1–#3 were all resolved in this implementation (raw display text; `fate.projection.emitted` SPAN_ROUTES registration; builder kept in `game/ruleset/fate_projection.py` per story authority). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `FateStatePayload` is a global broadcast exposing every seated PC's full Fate sheet (aspects, stress, consequences, fate points) to all connected clients.
  Affects `sidequest/server/websocket_handlers/fate_state_emit.py` (would need a per-recipient filter for a hidden-sheet mode).
  Correct for the current co-op audience (Fate aspects are table-public per Fate Core SRD + ADR-036 peer-visibility; matches the RELATIONSHIPS/QUESTS broadcast) — flagged only so a future PvP/hidden-sheet mode (not implemented) knows it must add per-recipient filtering, consistent with the sealed-visibility deferral in CLAUDE.md. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

3 deviations

- **Additive rich builder, not in-place promotion of `build_fate_projection`**
  - Rationale: the compact projection feeds the router + narrator with an existing "one source of truth" contract (test_fate_projection.py); changing its return type would break those consumers. "Promote" is realized as an additive rich sibling reading the same source, not a breaking in-place change.
  - Severity: minor
  - Forward impact: Dev builds both; Architect may later refactor the compact one to derive from the rich payload (still one source of truth).
- **Conflict "turn order" = seating order**
  - Rationale: Fate turn order is computed per-exchange (Notice/Empathy) at `run_fate_exchange` time and is NOT persisted in snapshot state; seating order IS the engine's tiebreak order (`fate_opponent._live_player_actors`). Projecting a non-persisted initiative would force dishonest re-derivation outside an exchange.
  - Severity: minor
  - Forward impact: F3f (118-6) conflict overlay may surface live exchange order; F3a projects the durable side/seating shape.
- **Character `aspects` = named sheet aspects only (filled consequences not duplicated)**
  - Rationale: a filled consequence IS an invokable aspect (SRD) but the story lists consequence slots as a SEPARATE payload element; listing it in both double-counts it for the UI/invoke control.
  - Severity: minor
  - Forward impact: F3d (118-4) invoke control must read invokable aspects from BOTH `aspects` (free_invokes) and filled `consequences`.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Additive rich builder, not in-place promotion of `build_fate_projection`**
  - Spec source: context-story-118-1.md, story title
  - Spec text: "promote build_fate_projection into a full client payload"
  - Implementation: tests pin a NEW sibling `build_fate_state_payload` returning `FateStatePayload`, plus a regression guard that the existing compact `build_fate_projection` dict contract is UNCHANGED.
  - Rationale: the compact projection feeds the router + narrator with an existing "one source of truth" contract (test_fate_projection.py); changing its return type would break those consumers. "Promote" is realized as an additive rich sibling reading the same source, not a breaking in-place change.
  - Severity: minor
  - Forward impact: Dev builds both; Architect may later refactor the compact one to derive from the rich payload (still one source of truth).
- **Conflict "turn order" = seating order**
  - Spec source: context-story-118-1.md, story title
  - Spec text: "conflict sides/turn order"
  - Implementation: the conflict payload carries participants by side in SEATING order (`encounter.actors` order), not a computed initiative sequence.
  - Rationale: Fate turn order is computed per-exchange (Notice/Empathy) at `run_fate_exchange` time and is NOT persisted in snapshot state; seating order IS the engine's tiebreak order (`fate_opponent._live_player_actors`). Projecting a non-persisted initiative would force dishonest re-derivation outside an exchange.
  - Severity: minor
  - Forward impact: F3f (118-6) conflict overlay may surface live exchange order; F3a projects the durable side/seating shape.
- **Character `aspects` = named sheet aspects only (filled consequences not duplicated)**
  - Spec source: context-story-118-1.md, story title
  - Spec text: "all aspects+kind+free-invoke counts ... consequence slots"
  - Implementation: `FateCharacterEntry.aspects` carries only `sheet.aspects` (named: high_concept/trouble/character); filled-consequence aspects surface in the separate `consequences` list, not duplicated into `aspects`.
  - Rationale: a filled consequence IS an invokable aspect (SRD) but the story lists consequence slots as a SEPARATE payload element; listing it in both double-counts it for the UI/invoke control.
  - Severity: minor
  - Forward impact: F3d (118-4) invoke control must read invokable aspects from BOTH `aspects` (free_invokes) and filled `consequences`.

### Dev (implementation)
- No deviations from spec. Implemented exactly to the TEA-pinned contract (the 35 tests). The three design decisions affecting the shape (additive builder, seating-order conflict participants, named-only aspects) were logged by TEA above and followed verbatim.

### Reviewer (audit)
- **TEA #1 — Additive rich builder, not in-place promotion** → ✓ ACCEPTED by Reviewer: sound; preserves the router/narrator one-source-of-truth (compact `build_fate_projection` verified untouched, regression guard green).
- **TEA #2 — Conflict "turn order" = seating order** → ✓ ACCEPTED by Reviewer: honest projection; live initiative (Notice/Empathy) is computed per-exchange and not persisted, so seating order is the only durable, truthful ordering. F3f can surface live order later.
- **TEA #3 — Character `aspects` = named sheet aspects only** → ✓ ACCEPTED by Reviewer: avoids double-listing filled consequences; F3d invoke control reads both lists per the forward-impact note.
- **Dev — No deviations from spec** → ✓ ACCEPTED by Reviewer: implementation matches the pinned contract; no undocumented divergence found.
- No UNDOCUMENTED deviations found. The wire DTOs flattening source Literals to `str` (`kind`/`level`/`side`) is a faithful, sibling-consistent DTO pattern (`QuestLogEntry.status: str`), not a spec deviation — the story named the fields, not their wire types.