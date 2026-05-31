---
story_id: "75-1"
jira_key: ""
epic: "75"
workflow: "tdd"
---
# Story 75-1: Restore runtime lore accretion into the RAG — port lore_sync per-turn fact embedding

## Story Details
- **ID:** 75-1
- **Jira Key:** (none — Jira not configured)
- **Epic:** 75 — RAG Retrieval Layer
- **Workflow:** tdd (phased: setup → red → green → spec-check → verify → review → spec-reconcile → finish)
- **Points:** 5
- **Stack Parent:** none (independent)
- **Repository:** sidequest-server (Python FastAPI backend)

## Story Context

### Problem Statement

The lore RAG is **REAL and FIRES EVERY TURN** in the current Python codebase:
- **Retrieval path (live):** `websocket_session_handler.py:2449` → `_retrieve_lore_for_turn` → `sidequest/server/dispatch/lore_embed.py:37` → `lore_embedding.py:276` `retrieve_lore_context`
- **Implementation:** Real MiniLM-L6-v2 384-dim embeddings via the daemon (`sidequest-daemon/sidequest_daemon/media/daemon.py:257-288`)
- **Injection:** Retrieved lore inserted into live narrator prompt at `orchestrator.py:2096` (AttentionZone.Valley)
- **Context threading:** `lore_store` passed through `ToolContext` (session_helpers.py:1159)

However, the index is **STARVING**. The Rust codebase fed discovered facts back into the RAG **every turn** via `accumulate_and_persist_lore` (Rust: `crates/sidequest-server/src/dispatch/lore_sync.rs:26-120`), persisting embedded fragments to the lore store. **Python dropped this accretion loop entirely.**

### Current State (Python)

**Where facts go now:**
- Runtime narrator-discovered facts flow through a **SEPARATE KnownFact system** (`commit_known_fact.py` / `query_known_facts.py`) that is **NEVER embedded into the RAG**
- These facts are persisted as unembedded entries in the journal
- Python only SEEDS the lore RAG at chargen/connect/arc-promotion (`lore_seeding.py`)

**Net effect:**
- The Python RAG index holds only static authored lore
- Per-turn retrieval returns thin results
- The snapshot blob does the heavy lifting instead of runtime retrieval

### What to Restore

This story restores the per-turn accretion path so runtime-discovered facts become embedded, retrievable lore fragments. This is a **RESTORATION** (porting Rust behavior `lore_sync.rs:26-120` into Python), not a new system.

**Reusable infrastructure:**
- Live embedding pipeline: `lore_embedding.py:embed_pending_fragments` (105-268)
- Real retrieval: `lore_embedding.py:retrieve_lore_context` (276)
- Persistence: `lore_store.py:query_by_similarity`
- Daemon: MiniLM embeddings already integrated at `sidequest-daemon/sidequest_daemon/media/daemon.py:257-288`

**Key decision in design:** Whether to (a) bridge the existing KnownFact commits into lore-fragment minting+embedding, or (b) add a parallel accretion hook in post-turn dispatch alongside the existing embed worker dispatch (`_dispatch_embed_worker` at `websocket_session_handler.py:1234`). The red phase will establish the design; either path reuses the live embedding pipeline.

### Related Work

**Related stories (epic 75):**
- 75-2: Budgeted NPC working-set selection (port `npc_context.rs`)
- 75-3: Universal retrieval layer design (ADR — lore+locations+NPCs+factions all retrieved per turn)

**ADRs to keep in view:**
- ADR-048: Lore RAG (live, needs refresh post-port status)
- ADR-100: Journal Pipeline Coherence (KnownFacts + JOURNAL_RESPONSE)
- ADR-087: Post-Port Subsystem Restoration Plan

**Reference code:**
- Rust origin (read-only): `/tmp/sidequest-rust-ref/crates/sidequest-server/src/dispatch/lore_sync.rs:26-120` (or clone github.com/slabgorb/sidequest-api if absent)

## Acceptance Criteria

1. **Runtime facts are embedded fragments:** Runtime narrator-discovered facts (currently KnownFact) are written as embedded, retrievable lore fragments each turn (port the Rust `lore_sync.rs` accretion behavior).

2. **Persistence + round-trip:** Newly accreted fragments are persisted and round-trip embeddings on save/load (no re-embed cost on replay).

3. **OTEL observability:** An OTEL span fires per accretion (fragment minted + embed dispatched) so the GM panel can confirm the RAG is being fed during play. This is mandatory project doctrine: every subsystem decision observable.

4. **Wiring test:** Integration test that plays a turn, commits a KnownFact, and asserts a new embedded fragment is retrievable via `query_by_similarity` on the next turn.

## Sm Assessment

**Setup verdict: READY for RED.** This is a clean restoration, not a net-new build — the highest-confidence kind of story. The retrieval half of the RAG is verified live (scout, 2026-05-30: `websocket_session_handler.py:2449` → `lore_embedding.py:276` → injected at `orchestrator.py:2096`); what was lost in the Rust→Python port is the **accretion** half (`lore_sync.rs:26-120`). All downstream infra the implementation needs already exists and is wired (embedding pipeline `embed_pending_fragments`, `query_by_similarity`, the MiniLM daemon worker, the post-turn `_dispatch_embed_worker` hook). So the work is a bridge, not a foundation.

**Open design question deferred to RED/green (correctly, not SM's call):** bridge existing KnownFact commits into fragment minting+embedding (A) vs. a parallel post-turn accretion hook (B). The Architect should weigh this against ADR-100 (KnownFacts/Journal coherence) — KnownFacts are an existing, intentional pipeline, so option A risks double-purposing them; option B risks two parallel fact stores drifting. Tests should pin the chosen seam, not both.

**Risk flags for the test author:**
- *Async embedding.* Embeds are fire-and-forget via the daemon. The AC4 wiring test ("retrievable on the next turn") must not race the embed worker — assert against the deterministic seam (fragment minted + embed dispatched), and gate the "retrievable via `query_by_similarity`" assertion on embed completion, or it will flake. The daemon being down degrades to no-injection (logged + OTEL, not silent) — decide whether the test stubs the embedder or requires a live daemon.
- *OTEL is an AC, not a nicety* (AC3) — per project doctrine the accretion span IS the lie detector that proves the RAG is being fed. The wiring test should assert the span fires, not just that a fragment exists.
- *No silent fallbacks.* If accretion can't embed, it must fail loud / log + OTEL — never silently skip, which would recreate the "starving index" invisibly.

**Verification before done:** AC4's integration test is the mandatory wiring test (component reachable from a real turn path), satisfying the project's "every test suite needs a wiring test" rule. Watch that the fragment actually enters the *same* store `retrieve_lore_context` reads from — not a parallel one.

## TEA Assessment

### Red Phase (test writing)

**Tests Required:** Yes
**Reason:** New runtime behavior (lore accretion) — not a chore bypass.

**Test Files:**
- `tests/game/test_lore_accretion.py` — 14 pure-unit tests: fragment minting (AC1), FactCategory→LoreCategory total mapping (5 parametrized), provenance metadata, idempotency (no `DuplicateLoreId` leak), No-Silent-Fallback blank-content skip, empty-list no-op, embedding round-trip (AC2).
- `tests/server/dispatch/test_lore_accretion_dispatch.py` — 7 wiring tests: import guard, `accrete_for_turn` mints PC facts, AC3 watcher event, dispatch idempotency, handler delegate guard, **production-path turn drive** (proves `_execute_narration_turn` invokes accretion), AC4 end-to-end retrievability (accrete → embed → `query_by_similarity`).

**Tests Written:** 21 tests covering 4 ACs + applicable rules
**Status:** RED (clean) — verified by `testing-runner` (RUN_ID 75-1-tea-red). All failures are `ImportError: cannot import name 'lore_accretion'`. Zero unexpected failures: every existing symbol (`KnownFact`, `LoreStore`, `LoreSource`, `LoreCategory`, `FactCategory`, `DuplicateLoreId`, `NarrationTurnResult`, `_build_turn_context`, `embed_pending_fragments`) and the `session_handler_factory` fixture resolve correctly.

### Rule Coverage

Python lang-review checklist (`.pennyfarthing/gates/lang-review/python.md`) — applicable checks:

| Rule | Test(s) | Status |
|------|---------|--------|
| #1 Silent exceptions (No Silent Fallbacks) | `test_blank_content_fact_is_skipped_explicitly_not_minted`, `test_idempotency_does_not_raise_duplicate_lore_id` | failing (RED) |
| #4 Logging/OTEL coverage (AC3) | `test_accrete_for_turn_emits_watcher_event` | failing (RED) |
| #6 Test quality (meaningful assertions) | self-check done — every test asserts a concrete value, no `assert True`, no truthy-only checks | n/a |
| #9 Async pitfalls | AC4 test awaits `embed_pending_fragments` deterministically via `_FakeClient` (no race on the fire-and-forget worker — per SM risk flag) | failing (RED) |
| Wiring (CLAUDE.md "Every Test Suite Needs a Wiring Test"; "No Source-Text Wiring Tests") | `test_handler_delegate_calls_accrete_for_turn` (delegate spy) + `test_narration_turn_accretes_known_facts` (real turn drive) — behavior/spy based, no source grep | failing (RED) |

**Rules checked:** 5 of 13 lang-review rules apply to this story; all have coverage. (Rules #2/#3/#5/#7/#8/#10/#11/#12 concern surfaces this story doesn't touch — mutable defaults, path/file handling, deserialization, resource leaks, SQL/HTML/input-validation boundaries, deps.)
**Self-check:** 0 vacuous tests (all assertions check concrete values).

**Design call made (see Deviations):** pinned seam **A** (bridge KnownFact → LoreFragment). Dev must implement `sidequest.game.lore_accretion` (`accrete_facts_to_lore`, `fact_category_to_lore_category`, `AccretionResult` with `.accreted`/`.skipped_duplicate`/`.skipped_blank`/`.fragment_ids`) and `sidequest.server.dispatch.lore_accretion.accrete_for_turn(handler, sd)` + handler delegate `_accrete_lore_for_turn`, wired into `_execute_narration_turn` **before** `_dispatch_embed_worker`.

**Handoff:** To Dev (Agent Smith) for GREEN.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (22 green, lint/format/types clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (covered manually — see [EDGE]) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings (covered manually — see [SILENT], drove the HIGH) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings (covered manually — see [TEST]) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings (covered manually — see [DOC]) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (covered manually — see [TYPE]) |
| 7 | reviewer-security | Yes | findings | 3 (2 medium, 1 low) | confirmed 2 (1 blocking-fold, 1 deferred), 1 low noted |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (verify already triaged fragment_ids — see [SIMPLE]) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings (rule-by-rule done manually — see Rule Compliance + [RULE]) |

**All received:** Yes (2 enabled subagents returned; 7 disabled via `workflow.reviewer_subagents`, covered manually)
**Total findings:** 2 confirmed-blocking, 1 deferred, 2 noted (1 low + 1 simplify-declined)

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | Unguarded accretion can crash the player's turn. `_accrete_lore_for_turn(sd)` is invoked with no local try/except, immediately before narration is delivered (line 1236+). Its sibling post-narration side-effects (`session.persist` line 1207, `round_invariant` telemetry line 1217) are each wrapped with explicit `except Exception` + the comment *"must never crash a turn"*. Feeding the RAG is a non-essential side-effect; an exception from `accrete_facts_to_lore` (e.g. the `ValueError` from `fact_category_to_lore_category` when a future `FactCategory` variant is added without updating `_FACT_TO_LORE`) would propagate and abort narration delivery — the player loses the turn's narration. | `sidequest/server/dispatch/lore_accretion.py:accrete_for_turn` (and/or the call site `websocket_session_handler.py:1234`) | Wrap accretion defensively: on exception, `logger.exception` + emit a `_watcher_publish("state_transition", {field:"lore_accretion", op:"failed", error:type}, component="lore", severity="error")` and **continue** — never re-raise. Mirror `run_worker`'s exception handling (`lore_embed.py`). Then narration always delivers. |
| [MEDIUM] | No upper-bound size validation on `fact.content` at the minting boundary (No Silent Fallbacks). Oversized content (> `MAX_EMBED_BYTES`, 32768 UTF-8 bytes) is minted, reaches the embed worker, fails `client.embed`, increments the retry counter, and is then silently dropped by `pending_embedding_ids` once `max_retries` is exceeded — a permanently-unembedded fragment with no minting-site signal. `[SEC]` corroborated. | `sidequest/game/lore_accretion.py:76` | Add a byte-length cap before `LoreFragment.new()`: count `skipped_oversized` on `AccretionResult`, emit it as a `lore.skipped_oversized` span/watcher attribute. Fail loud at the source, not silently downstream. |

**Data flow traced:** player action → `sanitize_player_text` at ingress (`player_action.py:287`) → narrator may call `commit_known_fact` → `KnownFact.content` stored verbatim on `pc.known_facts` → **(75-1)** `accrete_for_turn` mints `LoreFragment(source=GameEvent, content=fact.content)` → embed worker → next-turn `retrieve_lore_context` injects raw into the `<lore>` block of the narrator prompt (`lore_embedding.py:427`). The content is never re-sanitized after ingress (see [SEC] deferred finding).

### Rule Compliance (manual — rule-checker disabled)

Python lang-review checklist (`.pennyfarthing/gates/lang-review/python.md`), enumerated against every function/type in the diff:

- **#1 Silent exceptions:** `except DuplicateLoreId` (lore_accretion.py:84) → counted as `skipped_duplicate`, surfaced in OTEL — COMPLIANT (not silent). `except KeyError` (lore_accretion.py:51) → re-raises `ValueError` — COMPLIANT (fail loud). **However** the *minting boundary* silently lets oversized content fail downstream — flagged [MEDIUM] above as a #1/#11 violation in spirit.
- **#2 Mutable defaults:** `AccretionResult.fragment_ids` uses `field(default_factory=list)` — COMPLIANT. No mutable default args.
- **#3 Type annotations:** all public functions (`fact_category_to_lore_category`, `accrete_facts_to_lore`, `accrete_for_turn`, `_accrete_lore_for_turn`) fully annotated — COMPLIANT.
- **#4 Logging/OTEL:** accretion emits `rag.lore_accreted` span + `lore_accretion` watcher event — COMPLIANT for the happy path; the **failure** path has no logging because it is unguarded — ties to the [HIGH].
- **#6 Test quality:** 22 tests, concrete assertions, no `assert True`/vacuous — COMPLIANT (see [TEST]).
- **#9 Async pitfalls:** `accrete_for_turn` is sync, pure CPU (no blocking I/O in an async path) — COMPLIANT.
- **#10 Import hygiene:** no star imports; `TYPE_CHECKING` guard used correctly in the dispatch module — COMPLIANT.
- **#11 Input validation at boundaries:** blank guarded, but no length bound — flagged [MEDIUM].
- **#8 unsafe deserialization / #5 path / #7 resource leaks / #12 deps:** N/A — none in diff (confirmed by [SEC]).

### Observations

- `[SILENT] [HIGH]` Unguarded accretion crashes the turn — `dispatch/lore_accretion.py:accrete_for_turn` / call site `websocket_session_handler.py:1234`. (Detailed above.)
- `[SEC] [MEDIUM]` Missing size cap at minting boundary — `lore_accretion.py:76`. Confirmed.
- `[SEC] [MEDIUM]` RAG prompt-injection: `fact.content` re-injected into the `<lore>` prompt block without re-sanitization (`lore_embedding.py:427`). **DEFERRED** — this is a pre-existing property of the *entire* lore pipeline (genre-pack, chargen, and arc-promotion fragments all inject raw); 75-1 incrementally widens it by adding a runtime, player-influenced source. The right fix is centralized sanitization of retrieved lore, which belongs to the 75-3 universal-RAG ADR / an ADR-047 extension — not a 75-1 blocker. Logged as a Delivery Finding.
- `[SEC] [LOW]` `pc_name` stored in fragment metadata without a length bound — `dispatch/lore_accretion.py:42`. Defense-in-depth only (metadata is not prompt-injected). Noted; optional cheap truncation could ride along with the rework.
- `[EDGE] [VERIFIED]` Idempotency edges handled — duplicate `fact_id` within one sweep → second `store.add` raises `DuplicateLoreId`, caught, counted (lore_accretion.py:83-86); blank/whitespace content → `skipped_blank` (line 76); empty list → all-zero result (verified by `test_empty_fact_list_is_a_clean_no_op`). Evidence: the every-turn re-sweep is safe because the deterministic `lore_kf_{fact_id}` id + `DuplicateLoreId` guard make re-accretion a no-op.
- `[TEST] [VERIFIED]` Tests are strong and non-vacuous — 22 concrete-assertion tests including a real-turn production-path drive and an accrete→embed→`query_by_similarity` end-to-end. Gap: there is **no test that an accretion exception does not crash the turn** — TEA must add one as part of the [HIGH] rework (red-first).
- `[TYPE] [VERIFIED]` `AccretionResult` is a clean dataclass; `fact_category_to_lore_category` returns `str` (LoreCategory attrs are strings) — consistent with how `LoreFragment.category: str` is typed. No stringly-typed API smell beyond the existing `LoreCategory` string-constants convention (pre-existing, not introduced here).
- `[DOC] [VERIFIED]` Module + function docstrings are accurate and cite the Rust origin and the idempotency/no-silent-fallback rationale. No stale/misleading comments. The wiring comment at `websocket_session_handler.py:1231` correctly explains the before-embed ordering.
- `[SIMPLE]` `AccretionResult.fragment_ids` flagged by verify's efficiency lens as unused-in-prod; declined there with rationale (test-load-bearing, reasonable affordance). I concur — not a finding.
- `[RULE]` See Rule Compliance — the only rule gap is #11/#1 at the minting boundary ([MEDIUM]).

### Devil's Advocate

Assume this code is broken. The most dangerous property is that 75-1 introduces a **new, unguarded, mandatory step into the single most sacred path in the application — turn delivery**. The entire post-narration region is, visibly, a minefield the original authors defused one try/except at a time, each annotated "must never crash a turn." 75-1 walks a fresh mine into the field. A confused future contributor adds `FactCategory.Faction` (very plausible — there's a `LoreCategory.Faction` with no `FactCategory` peer today), forgets to extend `_FACT_TO_LORE`, ships it; now every turn in which the narrator commits a Faction fact raises `ValueError` *before narration is sent*, and the table — Keith's real playgroup — watches their turn vanish with a stack trace instead of prose. The career-GM-fooling bar is obliterated: a human DM never "loses" a turn because they mis-filed a note. The fix is four lines, and the codebase already shows exactly how (run_worker). Not doing it is indefensible.

Second attack: a malicious or careless player who learns the narrator can be steered to "remember" things. They get the narrator to commit a fact whose content is a 50KB wall of text, or contains `</lore><system>` markers. The 50KB fact silently never embeds (drains embed budget, no GM signal) — finding [MEDIUM]. The marker-laden fact rides the RAG into every future prompt — finding [SEC-deferred]. Neither is catastrophic alone, and the injection vector is pipeline-wide rather than 75-1-specific, but they show the minting boundary is too trusting. A stressed filesystem or a daemon outage during embed is already handled gracefully downstream (run_worker swallows) — good — but that very graciousness is what silently buries the oversized-fact failure. The empty-store and blank-fact cases are genuinely clean (verified by tests). Net: the design is sound and faithful to the Rust original; the defects are at the boundaries — error isolation and input bounding — exactly where a restoration tends to under-port the host's defensive conventions.

**Handoff:** Back to Dev (via TEA red-rework) for the [HIGH] defensive wrap + [MEDIUM] size cap. Both are testable (red-first).

## Subagent Results (re-review, post-rework b44f4c8)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (24 green, lint/format/types clean, 0 smells, call-ordering verified) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (covered manually — see [EDGE]) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings (the [HIGH] fix is the silent-failure resolution — see [SILENT]) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings (see [TEST]) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings (docstrings updated — see [DOC]) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (see [TYPE]) |
| 7 | reviewer-security | Yes | findings | 0 new (1 clean note); 2 prior deferred unchanged | confirmed 0 new; deferred unchanged |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (verify re-pass self-reviewed delta clean — see [SIMPLE]) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings (rule check manual — see [RULE]) |

**All received:** Yes (2 enabled subagents returned; 7 disabled via settings, covered manually)
**Total findings:** 0 new blocking; 2 prior blockers RESOLVED; 2 deferred findings unchanged

## Reviewer Assessment (re-review)

**Verdict:** APPROVED

Both prior blockers verified resolved against the rework diff (`580b9c7..b44f4c8`):

- `[SILENT]` **[HIGH] RESOLVED** — `accrete_for_turn` (dispatch/lore_accretion.py:49-80) now wraps the per-PC sweep in `try/except Exception`: on failure it `logger.exception` + emits `_watcher_publish(op="failed", error=type, severity="error", component="lore")` + `return` — never re-raises. The success span/watcher are reached only on the clean path. Matches the sibling "must never crash a turn" guards. A `test_accrete_for_turn_does_not_propagate_accretion_exception` test pins it. The player's turn now survives any accretion fault.
- `[SEC]` **[MEDIUM] RESOLVED** — `accrete_facts_to_lore` (game/lore_accretion.py:97) rejects `fact.content` > `MAX_EMBED_BYTES` at the minting boundary, counted as `skipped_oversized` and surfaced on the span + watcher. `[SEC]` confirmed the boundary operator/constant match the daemon's own check (`client.py:145`) exactly — no off-by-one, no bypass. Oversized content never enters the pending queue, eliminating the silent retry-and-drop drain. `test_oversized_content_is_skipped_at_minting_boundary` pins it.
- `[SEC]` No new security issues; `except` leaks no traceback/message to the client (only `type(exc).__name__`). Two prior deferred findings unchanged: RAG prompt-injection of raw lore (pipeline-wide → 75-3/ADR-047) and `pc_name` metadata length (low) — neither altered by the rework.

**Data flow traced:** narrator `commit_known_fact` → `pc.known_facts` → `accrete_for_turn` (now fault-isolated) → oversized-gated `accrete_facts_to_lore` → `LoreStore` (pending) → embed worker → next-turn `<lore>` injection. Safe: a fault anywhere in accretion degrades to "RAG not fed this turn", narration still delivers.

**Other dispatch tags (manual, subagents disabled):**
- `[EDGE] [VERIFIED]` Boundary at exactly `MAX_EMBED_BYTES` accepted (strict `>`), consistent with daemon. Idempotency/blank/empty edges remain covered. Micro-note: `interaction = snapshot.turn_manager.interaction` is read at line 47 *outside* the try — acceptable (plain int attribute, always present post-narration; not a realistic fault site).
- `[TEST] [VERIFIED]` 24 tests, all concrete assertions; the two new rework tests assert the exact failure-isolation + skip-counting behavior. No vacuous assertions.
- `[DOC] [VERIFIED]` Docstrings updated to describe both the oversized rejection and the turn-survival isolation — accurate, not stale.
- `[TYPE] [VERIFIED]` `AccretionResult` extended with `skipped_oversized: int = 0` — additive, consistent with the result-dataclass convention.
- `[SIMPLE] [VERIFIED]` Delta is minimal/idiomatic (mirrors `run_worker` try/except + the existing blank guard); the `logger` is now genuinely used. No over-engineering.
- `[RULE] [VERIFIED]` No Silent Fallbacks satisfied at both the minting boundary (loud `skipped_oversized`) and the sweep (`op="failed"` + `logger.exception`). lang-review #1/#11 compliant.

### Devil's Advocate (re-review)

Try to break the fix. Can an exception still escape `accrete_for_turn`? Only from the three statements outside the `try`: `sd.snapshot`, `snapshot.turn_manager.interaction`, and `trace.get_tracer(...).start_as_current_span` / the final `_watcher_publish`. The first two are attribute reads on objects the turn already used moments earlier (narration ran against this snapshot) — if they were going to fault, the turn would have died upstream. The tracer/watcher emits are OTEL/watcher infra that is defensive by construction elsewhere in this file. So the realistic fault surface — the accretion sweep itself — is fully contained. Could the broad `except` mask a *different* bug (e.g. a real logic error in `accrete_facts_to_lore`)? It logs the full traceback via `logger.exception` and raises a GM-panel `op="failed"` signal, so the bug is loud, not masked — it just doesn't take the player's turn down with it. Could an attacker exploit the oversized skip to hide a fact? They can make a fact too big to embed (it's skipped + counted, visible on the panel) — but that fact was never going to embed anyway; the change only makes the failure honest and cheap instead of silent and budget-draining. No regression. The rework is sound; the two defects the first pass caught are genuinely closed.

**Handoff:** To Architect for spec-reconcile (APPROVED).

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish (completed)
**Phase Started:** 2026-05-31T04:29:44Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-30 | 2026-05-31T03:42:56Z | 27h 42m |
| red | 2026-05-31T03:42:56Z | 2026-05-31T03:57:10Z | 14m 14s |
| green | 2026-05-31T03:57:10Z | 2026-05-31T04:04:34Z | 7m 24s |
| spec-check | 2026-05-31T04:04:34Z | 2026-05-31T04:07:02Z | 2m 28s |
| verify | 2026-05-31T04:07:02Z | 2026-05-31T04:11:16Z | 4m 14s |
| review | 2026-05-31T04:11:16Z | 2026-05-31T04:18:10Z | 6m 54s |
| red | 2026-05-31T04:18:10Z | 2026-05-31T04:21:50Z | 3m 40s |
| green | 2026-05-31T04:21:50Z | 2026-05-31T04:24:16Z | 2m 26s |
| spec-check | 2026-05-31T04:24:16Z | 2026-05-31T04:24:50Z | 34s |
| verify | 2026-05-31T04:24:50Z | 2026-05-31T04:25:30Z | 40s |
| review | 2026-05-31T04:25:30Z | 2026-05-31T04:28:58Z | 3m 28s |
| spec-reconcile | 2026-05-31T04:28:58Z | 2026-05-31T04:29:44Z | 46s |
| finish | 2026-05-31T04:29:44Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): The `query_lore` tool docstring claims the lore RAG path is "not yet wired / keyword-only fallback" — this is STALE. The per-turn auto path (`retrieve_lore_context` → `orchestrator.py:2096`) is fully live. Affects `sidequest/agents/tools/query_lore.py` (update or delete the misleading docstring). *Found by TEA during test design.*
- **Gap** (non-blocking): No OTEL span constant exists yet for accretion. Dev should add one to `sidequest/telemetry/spans/` and register it in `SPAN_ROUTES` (mirror `SPAN_WORLD_HISTORY_LORE_WRITEBACK` in `spans/world.py`). My AC3 test asserts the GM-panel-facing `_watcher_publish(field="lore_accretion", component="lore")` event (capturable); the span constant is the OTEL-trace complement. *Found by TEA during test design.*
- **Question** (non-blocking): The accretion sweep reads `snapshot.characters[*].known_facts`. In MP (ADR-037, per-player sheets) every seated PC has facts — `accrete_for_turn` should sweep ALL seated PCs, not just `characters[0]` (the exact bug that starved non-host XP in `award_turn_xp`, test_xp_award.py). My dispatch tests use the SP single-PC factory; Dev/verify should confirm MP fan-out. Affects `sidequest/server/dispatch/lore_accretion.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (blocking — for the lore-RAG-wiring suite only, NOT for 75-1): 3 pre-existing failures in `tests/server/test_lore_rag_wiring.py` (`test_cleanup_cancels_in_flight_embed_task`, `test_player_action_drives_full_lore_pipeline`, `test_double_dispatch_skipped_while_worker_running`). `_connect_and_confirm` aborts because a saved `GameSnapshot` fixture carries `manual_origin` on NPCs but the model now forbids extra inputs (`7 validation errors … npcs.N.manual_origin Extra inputs are not permitted`). **Proven pre-existing**: reproduces identically with my 75-1 impl stashed. This is epic-72 / story 72-3 ("MM NPC provenance — NpcPatch manual_origin") territory — a save-schema/fixture drift. Affects `sidequest/game/session.py` (NPC model) or the test save fixture. *Found by Dev during implementation.*
- **Improvement** (non-blocking): Resolved TEA's MP question — `accrete_for_turn` sweeps **all** `snapshot.characters` (per-PC `pc_name` metadata), not just `characters[0]`. Verify should add MP-coverage confirmation; my dispatch tests exercise the SP factory only. Affects `tests/server/dispatch/test_lore_accretion_dispatch.py` (add a 2-seat case). *Found by Dev during implementation.*
- **Improvement** (non-blocking): Addressed TEA's OTEL-span gap by emitting a `rag.lore_accreted` span via the direct-tracer pattern (as `lore_embedding.py` does), NOT a registered `SPAN_ROUTES` constant. If the GM dashboard's route table needs accretion as a first-class routed span, a follow-up should add the constant to `sidequest/telemetry/spans/` + `SPAN_ROUTES`. The capturable `_watcher_publish(field="lore_accretion", component="lore")` event (the GM-panel mechanism) is the primary AC3 signal and is tested. Affects `sidequest/server/dispatch/lore_accretion.py`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking — addressed in this story's rework): Unguarded accretion can crash the player's turn — `accrete_for_turn` lacks the local exception isolation every sibling post-narration side-effect carries. Affects `sidequest/server/dispatch/lore_accretion.py` + call site `websocket_session_handler.py:1234` (wrap, log, emit `op="failed"` watcher event, continue). *Found by Reviewer during code review.* [HIGH]
- **Gap** (blocking — addressed in this story's rework): No size cap on `fact.content` at the minting boundary; oversized content silently fails to embed downstream (No Silent Fallbacks). Affects `sidequest/game/lore_accretion.py:76` (add byte cap + `skipped_oversized` counter/OTEL attr). *Found by Reviewer during code review.* [MEDIUM]
- **Improvement** (non-blocking, deferred to 75-3 / ADR-047): Retrieved lore content (genre-pack, chargen, arc-promotion, and now KnownFact accretion) is injected raw into the narrator's `<lore>` prompt block without re-sanitization after ingress — a pipeline-wide RAG prompt-injection surface that 75-1 incrementally widens with a runtime, player-influenced source. The correct fix is centralized sanitization of retrieved lore, a design decision that belongs to the 75-3 universal-RAG ADR (extends ADR-047). Affects `sidequest/game/lore_embedding.py:427` (`_format_lore_section`) and the lore pipeline broadly. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `pc_name` is stored in fragment metadata without a length bound (`dispatch/lore_accretion.py:42`); defense-in-depth only (metadata is not prompt-injected). Optional cheap truncation could ride along with the rework. *Found by Reviewer during code review.*
- Re-review (b44f4c8): No new upstream findings. The two blocking findings above are RESOLVED; the two deferred Improvements (RAG sanitization → 75-3/ADR-047; pc_name truncation) remain open as future work, not 75-1 blockers. *Found by Reviewer during re-review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Resolved the deferred A-vs-B seam by pinning option A in the test contract**
  - Spec source: context-story-75-1.md, "Key decision in design" (session SM Assessment)
  - Spec text: "Whether to (a) bridge the existing KnownFact commits into lore-fragment minting+embedding, or (b) add a parallel accretion hook ... The red phase will establish the design."
  - Implementation: Tests pin **(A)**. `KnownFact` is Python's canonical runtime-fact carrier (the AC text itself says "Runtime narrator-discovered facts (currently KnownFact) are written as ... lore fragments"), and it is the faithful analog of Rust `lore_sync.rs` which minted from runtime-discovered facts. Option B would create a second parallel fact store that could drift from KnownFacts (the very split-brain epic 72 is fighting). The tests therefore require: a pure `sidequest.game.lore_accretion.accrete_facts_to_lore(store, facts, *, interaction, pc_name) -> AccretionResult` (mirroring `seed_lore_from_arc_promotion`'s result-dataclass + idempotent-by-id minting), `fact_category_to_lore_category(FactCategory) -> str`, and a dispatch wrapper `sidequest.server.dispatch.lore_accretion.accrete_for_turn(handler, sd)` + handler delegate `_accrete_lore_for_turn`.
  - Rationale: TDD red must target a concrete API; deferring the seam to "green" leaves no test to write. Pinning A gives Dev an unambiguous contract while keeping the embedding/retrieval infra untouched (reuse, not rebuild).
  - Severity: minor
  - Forward impact: Dev must implement these exact public names (or update tests in lockstep with a logged deviation). The accretion call must fire in `_execute_narration_turn` BEFORE `_dispatch_embed_worker` so freshly-minted fragments are in the pending queue the same turn.
- **Accreted-fragment id scheme fixed to `lore_kf_{fact_id}`**
  - Spec source: context-story-75-1.md, AC-1 + AC (idempotency implied by "each turn")
  - Spec text: "written as embedded, retrievable lore fragments each turn"
  - Implementation: Tests require a deterministic id `lore_kf_{fact.fact_id}` so the every-turn sweep is idempotent via the store's existing duplicate-id guard (caught and counted as `skipped_duplicate`, never raising `DuplicateLoreId`).
  - Rationale: KnownFact already carries a stable `fact_id` (uuid4 hex, ADR-100 Seam C); reusing it is the natural idempotency key and matches `mint_threshold_lore`'s event-id idempotency.
  - Severity: minor
  - Forward impact: none beyond the id format.
- **Review rework — no new deviations.** The two rework tests enforce the Reviewer's confirmed blockers against established host conventions (turn-survival error isolation à la `run_worker`; loud-at-boundary input bounding). `AccretionResult` gains an additive `skipped_oversized` field — an extension of the existing result-dataclass shape, not a spec deviation.

### Dev (implementation)
- No deviations from spec. Implemented TEA's pinned contract verbatim: `sidequest.game.lore_accretion` (`accrete_facts_to_lore`, `fact_category_to_lore_category`, `AccretionResult`), `sidequest.server.dispatch.lore_accretion.accrete_for_turn`, handler delegate `_accrete_lore_for_turn`, wired into `_execute_narration_turn` immediately before `_dispatch_embed_worker`. The two implementation choices made (sweep all PCs; emit span via direct tracer rather than SPAN_ROUTES) resolve TEA's open findings and satisfy the ACs — they are recorded as Delivery Findings, not spec deviations.

### Reviewer (audit)
- **TEA: pinned seam A (KnownFact → LoreFragment)** → ✓ ACCEPTED by Reviewer: faithful to the Rust `lore_sync` origin and to the AC text; avoids a second parallel fact store (the split-brain epic 72 fights). Sound.
- **TEA: deterministic id `lore_kf_{fact_id}`** → ✓ ACCEPTED by Reviewer: correct idempotency key, reuses the stable `KnownFact.fact_id`, matches `mint_threshold_lore`'s event-id idempotency. Verified the every-turn re-sweep is a safe no-op as a result.
- **Dev: "No deviations from spec"** → ✓ ACCEPTED by Reviewer: implementation matches the pinned contract; the two recorded choices (all-PC sweep, direct-tracer span) are correct AC/finding resolutions, not deviations.
- **Reviewer (audit) — undocumented divergence from host convention:** 75-1 adds a post-narration side-effect (`_accrete_lore_for_turn`) to `_execute_narration_turn` WITHOUT the local exception isolation that every adjacent side-effect in that block carries ("must never crash a turn"). Spec/SM flag said "fail loud … never silently skip" — but "fail loud" must mean log+OTEL+continue, not abort the player's turn. Not logged by TEA/Dev. Severity: HIGH. Drives the REJECT; fix tracked in the Reviewer Assessment severity table. → ✓ **RESOLVED (re-review b44f4c8):** `accrete_for_turn` now isolates faults (log + `op="failed"` watcher + swallow); the convention is honored and the divergence is closed.

### Architect (reconcile)
Audited every deviation entry against the story context, epic context, and the final diff (`develop...HEAD`, commit b44f4c8). All entries verified accurate and complete:
- **TEA "pinned seam A"** — spec source (context-story-75-1.md "Key decision in design") and quoted text accurate; implementation matches (KnownFact→LoreFragment bridge shipped). 6 fields present. ✓
- **TEA "deterministic id `lore_kf_{fact_id}`"** — accurate; the id scheme is exactly as shipped (`_fragment_id`). ✓
- **TEA "review rework — no new deviations"** — accurate; `skipped_oversized` is an additive contract extension, correctly classified as not-a-deviation. ✓
- **Dev "No deviations from spec"** — accurate; the two implementation choices (all-PC sweep, direct-tracer span) are recorded as Delivery Findings, correctly. ✓
- **Reviewer (audit)** — the one undocumented divergence (unguarded accretion vs. the host's "must never crash a turn" convention) was correctly caught, drove the REJECT, and is now stamped RESOLVED. ✓

**No additional deviations found.** The only forward-carrying items are the two **deferred Improvements** (not deviations from *this* story's spec): (1) centralized RAG-content sanitization for the `<lore>` injection path — belongs to **75-3** (universal-RAG ADR) / an ADR-047 extension; (2) `pc_name` metadata length bound (low). Both are logged as Delivery Findings for downstream pickup. AC accountability: all four ACs (AC1 minting, AC2 round-trip, AC3 OTEL, AC4 wiring) are DONE — none deferred or descoped — so no deferral-justification cross-check is required.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/game/lore_accretion.py` (new) — pure minting: `accrete_facts_to_lore` (deterministic `lore_kf_{fact_id}`, idempotent-by-id via the store's `DuplicateLoreId` guard → `skipped_duplicate`, blank-content → `skipped_blank`, no silent fallback), total `fact_category_to_lore_category` map (fails loud on unmapped enum), `AccretionResult`.
- `sidequest/server/dispatch/lore_accretion.py` (new) — `accrete_for_turn(handler, sd)` sweeps **all** seated PCs' `known_facts`, emits `rag.lore_accreted` OTEL span + `lore_accretion` watcher event (AC3).
- `sidequest/server/websocket_session_handler.py` — `_accrete_lore_for_turn` delegate + call wired into `_execute_narration_turn` **before** `_dispatch_embed_worker` (so fresh GameEvent fragments are pending and embed this turn → retrievable next turn).

**Tests:** 22/22 GREEN (RUN_ID 75-1-dev-green). Lint + format clean (ruff). Regression on adjacent suites (`test_lore_embed`, `test_lore_embedding`, `test_lore_store`, `test_lore_seeding`, `test_lore_seeding_arc_promotion`) all pass. 3 failures in `test_lore_rag_wiring.py` **proven pre-existing** (stashed-impl re-run reproduces them) — `manual_origin` NPC-schema drift, logged as a blocking Delivery Finding against the epic-72 surface, not 75-1.

**Branch:** `feat/75-1-restore-runtime-lore-accretion-rag` (pushed)

**Handoff:** To next phase (spec-check / verify).

### Green Phase — Rework (review fixes)

**Implementation Complete:** Yes (both Reviewer blockers fixed)

- **[HIGH] Turn-survival isolation** — `accrete_for_turn` (`dispatch/lore_accretion.py`) now wraps the per-PC sweep in `try/except`: on failure it `logger.exception` + emits a `lore_accretion` `op="failed"` watcher event (`severity="error"`) and returns — never re-raises. Re-added the module `logger` (now used). Matches the `run_worker` / sibling "must never crash a turn" pattern; an accretion bug degrades to "RAG not fed this turn", narration still delivers.
- **[MEDIUM] Oversized cap** — `accrete_facts_to_lore` (`game/lore_accretion.py`) rejects `fact.content` exceeding `MAX_EMBED_BYTES` (imported from `daemon_client.client`) at the minting boundary: new `AccretionResult.skipped_oversized` counter, surfaced as a `lore.skipped_oversized` span attribute + watcher field. Loud at the source instead of silent downstream.
- **Deferred (not in this story):** the pipeline-wide RAG prompt-injection sanitization ([SEC] medium) and `pc_name` truncation ([SEC] low) — logged as Delivery Findings; the sanitization belongs to 75-3/ADR-047.

**Tests:** 24/24 GREEN (RUN_ID 75-1-dev-green-rework), ruff lint + format clean. Changes isolated to the two new modules — no handler/embed-worker surface touched in the rework.

**Branch:** `feat/75-1-restore-runtime-lore-accretion-rag` (pushed, commit b44f4c8)

**Handoff:** To spec-check (Architect) for re-review of the rework.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None blocking (2 minor/trivial observations below)

Per-AC substance check (story context AC-1..AC-4 vs. the diff):

- **AC1 (runtime facts → embedded retrievable fragments each turn):** Aligned. `accrete_for_turn` sweeps every PC's `known_facts` → `accrete_facts_to_lore` mints `GameEvent` `LoreFragment`s (`embedding_pending=True`), wired into `_execute_narration_turn` immediately before `_dispatch_embed_worker` so the existing worker embeds them. Faithful to the Rust `lore_sync` accumulate-and-persist loop.
- **AC2 (persistence + embedding round-trip):** Aligned by reuse. Accreted fragments land in the same `sd.lore_store` that chargen/genre-seeded fragments already persist through (37-33) and that `retrieve_lore_context` reads from — the SM's "same store, not a parallel one" risk flag is satisfied. No new persistence code (correct — the store is already serialized in the snapshot); `LoreStore` JSON round-trip of embeddings is unit-tested.
- **AC3 (OTEL observability):** Aligned. `rag.lore_accreted` span + `lore_accretion` watcher event (`component="lore"`, the GM-panel mechanism, tested). See observation #1 on granularity.
- **AC4 (wiring — turn → fact → retrievable next turn):** Aligned. Real-turn drive test proves `_execute_narration_turn` invokes accretion; a second test proves accrete→embed→`query_by_similarity` retrievability. Behavior/spy based, no source-grep (honors CLAUDE.md).

**Observations (non-blocking):**

1. **AC3 span granularity — per-sweep vs per-fragment** (Ambiguous spec — Behavioral, Trivial). AC3 reads "a span fires per accretion (fragment minted + embed dispatched)." The code emits one `rag.lore_accreted` span per turn-sweep carrying an `accreted` count, and the "embed dispatched" half is covered by the adjacent, pre-existing embed-worker telemetry (`lore_embedding.worker` / dispatch watcher events). This matches the sibling span's granularity (per-run, not per-fragment). **Recommendation: C (clarify spec)** — code unchanged; the per-sweep+count span is the right grain for the GM panel and consistent with the embed worker. No per-fragment span needed.
2. **AC4 test pre-seeds the fact rather than driving a narrator `commit_known_fact` tool call** (Different test strategy — Behavioral, Trivial). The wiring test attaches a `KnownFact` to the PC then drives the turn, instead of having the mock narrator emit the commit tool. This is sound: accretion sweeps existing `known_facts` regardless of provenance, and the idempotent every-turn sweep means a fact committed at any point is accreted no later than the following turn — so commit-vs-accretion ordering can never drop a fact. **Recommendation: A/note** — accept; the strategy is robust and the production commit path is covered transitively.

**Architectural strength noted:** idempotent-by-`fact_id` sweep + party-wide character iteration (ADR-037) means the seam is order-independent and MP-safe by construction, avoiding the single-seat starvation class of bug (`award_turn_xp`).

**Out of scope (not a 75-1 mismatch):** the 3 pre-existing `test_lore_rag_wiring.py` failures (`manual_origin` NPC-schema drift) are correctly logged as a Dev delivery finding against the epic-72 surface; they predate this branch and are not introduced by 75-1.

**Decision:** Proceed to verify (TEA). No hand-back to Dev.

**Spec-check re-review (post-rework, b44f4c8):** Still **Aligned**. The two rework changes — defensive `try/except` isolation in `accrete_for_turn` (HIGH) and the `MAX_EMBED_BYTES` cap + `skipped_oversized` counter in `accrete_facts_to_lore` (MEDIUM) — are robustness fixes that *strengthen* AC1/AC3 alignment (turn-survival + No Silent Fallbacks) without changing the accretion contract or behavior on the happy path. No new mismatches. Proceed to verify.

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 3 (`sidequest/game/lore_accretion.py`, `sidequest/server/dispatch/lore_accretion.py`, the 75-1 additions in `websocket_session_handler.py`)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | clean | No duplication; minting + per-PC iteration + delegate all match established patterns (`mint_threshold_lore`, `award_turn_xp`, `_dispatch_embed_worker`). |
| simplify-quality | clean | Naming/docstrings/types consistent with sibling modules; the two `except` clauses are intentional (idempotency skip + fail-loud re-raise). |
| simplify-efficiency | 1 finding (high) | `AccretionResult.fragment_ids` unused by the production dispatch (only the test suite reads it). Suggested removal. |

**Applied:** 0 high-confidence fixes
**Flagged for Review:** 0
**Noted (declined with rationale):** 1
**Reverted:** 0

**Declined finding — `AccretionResult.fragment_ids`:** Triaged and **not applied**. The field is test-load-bearing (the RED contract asserts `result.fragment_ids == ["lore_kf_…"]` and indexes `[0]` for the AC2 round-trip), and it is a reasonable result affordance mirroring `ArcSeedResult`'s exposure of minted-fragment info. The suggested removal would force tests to recompute the id scheme via `_fragment_id` or reach into `store.fragments` — coupling them to internals and degrading testability — and would break the TEA-authored tests (a regression the verify workflow says to revert). Cost of keeping it is one short list. Net: keep. This is a case where the mechanically-correct "unused in prod" signal is globally wrong.

**Overall:** simplify: clean (1 finding reviewed + declined with rationale; no code change)

**Quality Checks:** Story suite 22/22 GREEN, ruff lint + format clean (Dev green phase, RUN_ID 75-1-dev-green) — no simplify edits applied, so no regression surface introduced in verify. Pre-existing `test_lore_rag_wiring.py` failures (`manual_origin` NPC-schema drift) remain out of scope for 75-1 (logged Delivery Finding).

**Handoff:** To Reviewer (The Merovingian) for code review.

### Verify re-pass (post-rework, b44f4c8)

**Status:** GREEN confirmed (24/24, ruff lint+format clean — dev green-rework RUN_ID 75-1-dev-green-rework).

Rework delta self-reviewed for simplify concerns (≈25 lines across the two existing modules — re-spawning the 3-lens fan-out on a delta already scrutinized by red-rework + spec-check is diminishing returns):
- **reuse:** the `try/except` isolation mirrors `run_worker`'s established pattern; the oversized guard mirrors the existing blank-content guard. No new duplication.
- **quality:** `logger` re-added and now genuinely used (resolves the earlier dead-logger removal); docstrings updated to match behavior; `# noqa: BLE001` carries the "must never crash a turn" rationale consistent with siblings.
- **efficiency:** byte-length check is O(len) once per fact, gated after the cheap blank check; no redundant work. The broad `except Exception` is intentional (turn-survival) — not over-broad error handling to flag.

**Overall:** simplify: clean (delta). **Handoff:** To Reviewer.