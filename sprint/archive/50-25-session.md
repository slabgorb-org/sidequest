---
story_id: "50-25"
jira_key: (SideQuest is personal — no Jira)
epic: "50"
workflow: "tdd"
---
# Story 50-25: Out-of-band aside channel — finish half-wired player→GM table-talk (ADR-107)

## Story Details
- **ID:** 50-25
- **Epic:** 50
- **Type:** Feature
- **Workflow:** TDD
- **Priority:** P1
- **Points:** 8
- **Status:** Active

## Context & Specification

This story finishes the half-wired `aside` feature. During the 2026-05-17 Beneath Sünden multiplayer playtest (5 players), a recurring issue emerged (F6): players used the action box to ask GM clarifying questions — `"I am very short and don't know how to swim. Will I be able to wade or must I be carried?"` — and each question **consumed a turn** and was **fully narrated** because `aside: bool` exists in the payload but has no server-side branching logic. It flows through the ADR-036 barrier and narrator identically to in-fiction actions, advancing world state.

### Half-wired State

- **Present:** UI toggle (`InputBar` "(…)" → aside placeholder), `aside: bool` on `PLAYER_ACTION`, peer mirror via `ActionRevealPayload.aside`, distinct `player-aside` segment rendering, combat-bracket stripping in the handler.
- **Missing:** any server branch on `aside` — the flag is ignored, asides flow directly to narration.
- **Doc lie:** `docs/api-contract.md` claims `aside:true` = "(not narrated)" *and* "broadcast identically to in-character text" — contradictory and both false.

### Design Spec

Complete specification: `docs/superpowers/specs/2026-05-17-aside-channel-design.md`

**Architecture (Approach A):**
1. Branch at `handlers/player_action.py` entry, **before** the ADR-036 submit-and-wait barrier
2. Never touch `SessionRoom.pending_actions`, dispatch lock, turn counter, or world state
3. Resolve via read-only `AsideResolver` — no write path, structurally cannot mutate the world
4. Answer as GM out-of-character (1-3 plain sentences) from the character's existing knowledge
5. Broadcast `ASIDE_ANSWER` to all seats (table-visible, per ADR-036 2026-05-03 amendment)
6. Emit routed `aside.resolve` span for OTEL auditing

**Answer Policy (Grounded GM Ruling):**
- *Capability/perception* — answerable from character sheet + region description (what they see/can do)
- *Rules/genre* — answerable from genre pack rulebook surface (the Sebastien lane)
- *Recap* — answerable from recent narration window + inventory
- **Refused:** hidden world state ("Is it trapped?", "What's behind the arch?") → "You'd have to check — that's an action."
- **Grounded:** answer must list the state keys used (character.size, region.water_depth, etc.) — the lie-detector trail

**Cost:** ADR-101 routing — asides are lowest-drama input → cheapest/fastest tier (Haiku).

### Implementation Plan

Complete task-driven plan: `docs/superpowers/plans/2026-05-17-aside-channel.md`

10 TDD tasks (no placeholders, all carry wiring tests):
1. Server protocol — `ASIDE_ANSWER` message type + payload
2. Server telemetry — routed `aside.resolve` span
3. Server — read-only `AsideResolver` with GM-craft policy
4. Server — branch on `aside` before the ADR-036 barrier
5. Server — mandatory MP wiring test (the centerpiece — all 7 guarantees)
6. UI — `ASIDE_ANSWER` message type + narrative stream routing
7. UI — `gm-aside` segment kind + InputBar copy
8. Docs — correct `api-contract.md` lie + guard test
9. ADR-107 — document the decision (cross-ref ADR-036, 063, 082, 101, SOUL)
10. Cross-repo verification gate + PRs

## Acceptance Criteria

1. **Aside consumes no turn:** no `narrative_log` row, no `scrapbook_entries` row, no turn/round advance, zero world patch. (Proven by `tests/handlers/test_aside_channel_wiring.py`)
2. **Multiplayer safety:** aside never counts toward the ADR-036 barrier; asker still owes their real action; other players' submissions unaffected.
3. **Server answers OOC via read-only `AsideResolver`:** `ASIDE_ANSWER` broadcast to ALL seats (table-visible).
4. **Answer policy enforced:** capability/rules/recap answered and grounded; hidden-state refused with "You'd have to check"; unparseable LLM → loud `resolver_error`, never invents lore.
5. **Routed `aside.resolve` OTEL span fires every aside** with attributes: `asker_id`, `outcome`, `grounded_on[]`, `model`, `latency_ms`. Visible in GM panel.
6. **UI gm-aside segment:** OOC answer rendered as `gm-aside` kind in narrative scroll, paired with the question, same visual register as `player-aside`.
7. **API contract corrected + ADR-107 authored:** `docs/api-contract.md` no longer contains "(not narrated)" or "broadcast identically" contradiction. ADR-107 cross-references ADR-036, 063, 082, 101, SOUL.
8. **Mandatory MP wiring test green:** test drives real `PLAYER_ACTION{aside:true}` through real handler, asserts all 7 guarantees (no turn record, MP barrier independence, broadcast scope, span fired).

## Story Context

### Technical Approach

**Key guarantee:** "No turn consumed" is enforced structurally (the resolver has no write path), not by remembering not to use one. The aside branch must sit at the earliest moment the server knows `aside=true` — the `handlers/player_action.py` entry — before any turn-state enqueue.

**Resolver Contract:** a read-only view of state (character summary, region description, inventory, rulebook, recent narration window) is handed to `AsideResolver.resolve(question)`. The resolver returns `AsideResolution` with `answer`, `outcome ∈ {answered, refused_hidden_state, refused_would_advance, ungrounded_declined, resolver_error}`, and `grounded_on[]` (audit trail). The resolver has **no methods that mutate** — this is verified by structural inspection (`dir(AsideResolver)` should contain only `resolve`).

**OTEL Auditing:** every aside emits `aside.resolve` span routed to the GM panel. Span attributes carry the full decision record: asker, question, answer, grounding sources, outcome, model tier, latency. An aside with `outcome=answered` but empty `grounded_on[]` is an ungrounded aside — the lie detector catches it. An aside with `outcome=resolver_error` indicates the LLM call failed.

**Multiplayer Boundary:** an aside arriving mid-round (even while another player's turn is dispatching) cannot collide because it shares **zero mutable turn state** with the barrier. Concurrency-safe by exclusion, not by locking. The asker's pending-action slot is untouched; the barrier still waits for their real action if unsubmitted.

### Code Branches

Per `repos.yaml` and the story description:
- **Orchestrator (`.`):** base `main` → `feat/50-25-aside-channel`
- **sidequest-server:** base `develop` → `feat/50-25-aside-channel`
- **sidequest-ui:** base `develop` → `feat/50-25-aside-channel`

All three `feat/50-25-aside-channel` branches are based **cleanly off their correct bases** (orchestrator off `main`, server + ui off `develop`), 0 commits beyond base, clean working trees — verified by SM. The sidequest-ui repo previously had uncommitted terminal-emphasis WIP; SM parked it as a reversible checkpoint commit (`e42c0bb`) on its own `fix/terminal-emphasis-legibility` branch (reverse with `git reset --soft HEAD~1` on that branch) and recut the 50-25 UI branch off `develop`. TEA needs no special handling here — the slate is clean.

## Workflow Tracking

**Workflow:** TDD
**Phase:** finish
**Phase Started:** 2026-05-18T05:52:33Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-18 | 2026-05-18T04:25:17Z | 4h 25m |
| red | 2026-05-18T04:25:17Z | 2026-05-18T04:35:54Z | 10m 37s |
| green | 2026-05-18T04:35:54Z | 2026-05-18T05:06:51Z | 30m 57s |
| spec-check | 2026-05-18T05:06:51Z | 2026-05-18T05:09:20Z | 2m 29s |
| verify | 2026-05-18T05:09:20Z | 2026-05-18T05:15:55Z | 6m 35s |
| review | 2026-05-18T05:15:55Z | 2026-05-18T05:24:45Z | 8m 50s |
| red | 2026-05-18T05:24:45Z | 2026-05-18T05:29:52Z | 5m 7s |
| green | 2026-05-18T05:29:52Z | 2026-05-18T05:39:53Z | 10m 1s |
| spec-check | 2026-05-18T05:39:53Z | 2026-05-18T05:41:39Z | 1m 46s |
| verify | 2026-05-18T05:41:39Z | 2026-05-18T05:44:58Z | 3m 19s |
| review | 2026-05-18T05:44:58Z | 2026-05-18T05:50:37Z | 5m 39s |
| spec-reconcile | 2026-05-18T05:50:37Z | 2026-05-18T05:52:33Z | 1m 56s |
| finish | 2026-05-18T05:52:33Z | - | - |

## Sm Assessment

**Setup Complete:** Yes
**Story:** 50-25 — Out-of-band aside channel (ADR-107), 8 pts, p1, workflow `tdd` (phased)
**Repos:** sidequest-server, sidequest-ui, orchestrator

**Branches (all `feat/50-25-aside-channel`, verified by SM — 0 commits beyond base, clean tree):**
- orchestrator → base `main` (08a7dc8)
- sidequest-server → base `develop` (d42e9be)
- sidequest-ui → base `develop` (ef359da)

**Setup correction:** sm-setup initially cut the UI branch off `fix/terminal-emphasis-legibility` because that repo carried uncommitted terminal-emphasis WIP. SM parked the WIP as a reversible checkpoint commit (`e42c0bb`, reverse: `git reset --soft HEAD~1`) on its own `fix/terminal-emphasis-legibility` branch and recut the 50-25 UI branch cleanly off `develop`. No unrelated commits ride the 50-25 branches.

**Spec runway:** Design spec (`docs/superpowers/specs/2026-05-17-aside-channel-design.md`) and 10-task TDD plan (`docs/superpowers/plans/2026-05-17-aside-channel.md`) both present and pointed at in the context — TEA has authoritative sources for the RED phase.

**Handoff:** To Radar (TEA) for the RED phase — write failing tests for all 8 ACs, centered on the mandatory MP wiring test (`test_aside_channel_wiring.py`).

## TEA Assessment

**Tests Required:** Yes
**Reason:** 8-pt p1 feature with 8 ACs and a spec-mandated centerpiece wiring test. No chore bypass.

**Test Files:**
- `sidequest-server/tests/protocol/test_aside_payload.py` — 3 tests: `ASIDE_ANSWER` enum member, `AsideAnswerPayload` roundtrip, safe defaults (plan Task 1, ACs 3/7)
- `sidequest-server/tests/protocol/test_enums.py` — bumped enum-count pin `test_message_type_complete_count` 48→49 + ADR-107 changelog line (plan Task 1 Step 6)
- `sidequest-server/tests/telemetry/test_aside_span.py` — 2 tests: `aside.resolve` is routed in `SPAN_ROUTES`, extractor pulls attributes (plan Task 2, AC-5)
- `sidequest-server/tests/agents/test_aside_resolver.py` — 5 tests: capability answered+grounded, hidden-state refused, policy-in-system-prompt, unparseable→loud `resolver_error`, **no write surface** (structural) (plan Task 3, AC-4)
- `sidequest-server/tests/handlers/test_aside_channel_wiring.py` — **the centerpiece**: all 7 out-of-band guarantees in a 3-player MP room (plan Task 5, spec §7, ACs 1/2/3/6/8)
- `sidequest-server/tests/protocol/test_api_contract_aside.py` — doc-contract guard: `api-contract.md` no longer lies about asides (plan Task 8, AC-7)
- `sidequest-ui/src/__tests__/asideChannel.test.ts` — 2 tests: `ASIDE_ANSWER` known type, renders `gm-aside` not narration `text` (plan Tasks 6/7, AC-6)

**Tests Written:** 14 server test functions + 1 modified pin + 2 UI specs, covering all 8 ACs
**Status:** RED (failing — verified by testing-runner, RUN_ID 50-25-tea-red)

**RED verification (all 8 failure signatures match expected — no vacuous test, no unexpected pass, no collection/syntax error):**

| File | First failure | Right reason? |
|------|---------------|---------------|
| test_aside_payload.py | ImportError `AsideAnswerPayload` | ✓ |
| test_aside_span.py | ModuleNotFoundError `spans.aside` | ✓ |
| test_aside_resolver.py | ModuleNotFoundError `agents.aside_resolver` | ✓ |
| test_aside_channel_wiring.py | ImportError `tests.handlers._harness` | ✓ (planned — Dev factors harness in GREEN) |
| test_api_contract_aside.py | AssertionError `"(not narrated)"` present | ✓ |
| test_enums.py pin | AssertionError `48 == 49` | ✓ |
| asideChannel.test.ts (×2) | `ASIDE_ANSWER` undefined; no `gm-aside` | ✓ |

### Rule Coverage

`.claude/rules/` is empty; rubric = `.pennyfarthing/gates/lang-review/{python,typescript}.md` + SOUL.md + the spec's lie-detector mandate.

| Rule | Test(s) | Status |
|------|---------|--------|
| python.md — no vacuous assertions (`assert True`, truthy-only, no-assertion) | every test asserts concrete values/sets/counts; self-checked | n/a (self-check passed) |
| python.md — error paths must be loud (No Silent Fallbacks) | `test_unparseable_llm_output_declines_loudly_not_improvises` (asserts `resolver_error` + non-empty msg + empty `grounded_on`) | failing |
| python.md — input validation (empty/whitespace) | **GAP** — spec §6 empty-aside rejection has no test (logged as deviation + Delivery Finding for Dev to cover in the Task 5 harness) | not covered |
| SOUL/spec — read-only resolver has no write path | `test_resolver_has_no_write_surface` (structural: `dir()` == `["resolve"]`) | failing |
| spec §6 — OTEL lie-detector: every aside emits a routed span | `test_aside_resolve_is_routed` + wiring `room.spans_named("aside.resolve")` | failing |
| spec §3/§7 — out-of-band: no turn/world/barrier mutation | wiring test guarantees 1–5 | failing |
| spec §5 — `ASIDE_ANSWER` is its own typed segment, not `NARRATION` | UI `segs.every(s => s.kind !== "text")` + `gm-aside` present | failing |
| typescript.md — bind to real exported symbols, no invented API | UI test uses real `buildSegments`/`GameMessage` (deviation logged) | failing |

**Rules checked:** 7 of 7 applicable lang-review/SOUL rules have RED coverage; 1 (empty-aside input validation) is an explicit, flagged GAP for Dev — not silently dropped.
**Self-check:** 0 vacuous tests found (all assertions check specific values; the one `assert res.answer` is paired with specific `outcome`/`grounded_on` asserts — a deliberate non-empty contract, not a truthy stand-in).

**Handoff:** To Major Winchester (Dev) for the GREEN phase — implement plan Tasks 1–9. Start with Task 5's `tests/handlers/_harness.py` (factored from the sibling MP handler test, no behavior change) so the centerpiece can fail-then-pass on its real assertions, and add the empty/whitespace-aside case (Delivery Finding Gap) while building it.

## Dev Assessment

**Implementation Complete:** Yes — plan Tasks 1–9, all 8 ACs.

**Files Changed:**
- `sidequest-server/sidequest/protocol/enums.py` — `MessageType.ASIDE_ANSWER`
- `sidequest-server/sidequest/protocol/messages.py` — `AsideAnswerPayload` + typed `AsideAnswerMessage` + `_Phase1Variant` union arm
- `sidequest-server/sidequest/telemetry/spans/aside.py` (new) + `spans/__init__.py` — routed `aside.resolve` span
- `sidequest-server/sidequest/agents/aside_resolver.py` (new) — read-only `AsideResolver`, no write surface
- `sidequest-server/sidequest/agents/llm_factory.py` — `build_aside_llm()` single-shot Haiku adapter (ADR-101)
- `sidequest-server/sidequest/handlers/player_action.py` — full aside branch before the ADR-036 barrier (replaces the half-wired combat-strip-only block)
- `sidequest-server/tests/handlers/_harness.py` (new) — real-handler MP harness; `tests/handlers/test_aside_channel_wiring.py` centerpiece + empty-aside case; `tests/protocol/test_aside_payload.py`, `tests/protocol/test_api_contract_aside.py`, `tests/telemetry/test_aside_span.py`, `tests/agents/test_aside_resolver.py`; `tests/protocol/test_enums.py` (pin 49); `tests/server/test_combat_brackets.py` (obsolete aside→narrator test deleted, tombstoned)
- `sidequest-ui/src/types/protocol.ts`, `src/App.tsx`, `src/lib/narrativeSegments.ts`, `src/components/narrativeRenderers.tsx`, `src/components/InputBar.tsx`, `src/__tests__/asideChannel.test.ts`
- `docs/api-contract.md` (lie corrected), `docs/adr/107-out-of-band-aside-channel.md` (new), `docs/adr/{README,SUPERSEDED,DRIFT}.md` + `CLAUDE.md` (regenerated index)

**Tests:** GREEN (verified, RUN_ID 50-25-dev-green-final)
- sidequest-server: `ruff check .` clean; pytest **6211 passed / 0 failed / 400 skipped**
- sidequest-ui: `tsc --noEmit` clean; eslint 0 errors; vitest **1436 passed / 0 failed**
- Centerpiece `test_aside_is_out_of_band_in_mp` drives the REAL handler — all 7 out-of-band guarantees green; empty-aside §6 gap now covered.

**Branches (pushed):** `feat/50-25-aside-channel` — sidequest-server (base develop), sidequest-ui (base develop), orchestrator (base main).

**Wiring:** The aside branch is reachable from the real `PLAYER_ACTION` dispatch (`PlayerActionHandler.handle`), broadcasts via the real `SessionRoom.broadcast`, emits a routed OTEL span the GM panel consumes, and the UI routes `ASIDE_ANSWER` into the real narrative stream as a `gm-aside` segment. Non-test consumers confirmed end-to-end.

**Handoff:** To Colonel Potter (Reviewer) for code review.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None (4 logged Dev deviations + 1 TEA gap-closure reviewed; all Minor, all sound)

**Structural gate:** PASS — AC coverage present in Dev Assessment, implementation-complete asserted, TEA + Dev deviation subsections well-formed (6-field).

**Per-AC substantive check (spec §1–§9 vs code):**
- AC-1 no turn/world: aside branch returns at handler L279/280; barrier enqueue (`record_pending_action` L394, `submit_input` L408) is strictly below — **verified in code**, not just asserted. Centerpiece asserts all 4 sub-guarantees against real state. Aligned.
- AC-2 MP barrier independence: branch precedes the barrier block entirely; centerpiece proves `pending_player_ids == {Katia,Donut}` with barrier unfired. Aligned.
- AC-3 read-only resolver + table broadcast: `AsideResolver` public surface is `resolve` only; imports are `json`/`dataclasses`/`Protocol` — **structurally no write path** (verified). Broadcast `exclude_socket_id=None` = all seats. Aligned.
- AC-4 answer policy: system prompt + `_VALID_OUTCOMES` enforcement + 5 units (capability/refusal/policy-in-prompt/loud-resolver_error/no-write-surface). Aligned.
- AC-5 routed span: `aside.resolve` in `SPAN_ROUTES` (state_transition/aside), all 5 attrs set in-span; unit + centerpiece assert. Aligned.
- AC-6 UI gm-aside: typed `ASIDE_ANSWER`, narrative-stream route, `gm-aside` segment + renderer at the same OOC register as `player-aside`, InputBar copy. vitest green. Aligned.
- AC-7 doc-lie + ADR-107: guard test green (in the 6211); ADR-107 authored with cross-refs 036/063/082/101/104-105/SOUL. Aligned.
- AC-8 mandatory wiring test: drives the **real** `PlayerActionHandler.handle()` (real room/snapshot/barrier/store/pack); only the orthogonal narrator is stubbed and even it performs the real `record_interaction`. The lie-detector is genuine, not fabricated. Aligned.

**Deviation review (substance, not just structure):**
- Dev#1 `AsideAnswerMessage` + union arm — Extra-in-code (Minor). The plan's abstract `_broadcast_msg` had no concrete codebase form; a discriminated-union arm is *mandatory* for (de)serialization and mirrors `PlayerSpeechMessage` exactly. **Resolution A (accept)** — this is the correct realization of the spec's "mirror the real broadcast path."
- Dev#2 `build_aside_llm` single-shot adapter — Different-approach (Minor, internal). Plan premised a tier builder that does not exist; `AnthropicSdkClient` only exposes a tool-use loop. A minimal single-shot Haiku adapter is the right ADR-101 realization, not narrator-client reinvention. **Resolution A (accept).**
- Dev#3 harness built from scratch — Different-approach (Minor). Plan's factor-source (sibling MP fixture) does not exist; every handler test is MagicMock-based. A real-objects harness is the *only* faithful way to satisfy spec §7. **Resolution A (accept)** — verified the harness drives real code.
- Dev#4 deleted obsolete `test_aside_player_action_strips_brackets_before_narrator` — Removed (Minor). It pinned the exact pre-ADR-107 aside→narrator behaviour this story removes; ADR-107 documents the change; combat-strip-still-applies is re-covered by the wiring suite. **Resolution A (accept)** — removing a test that asserts superseded behaviour is correct hygiene; mocking a key to keep it green would have buried the contract change.
- TEA gap-closure (empty-aside §6) — Extra-in-code that *closes* a spec gap. **Resolution C/A (accept).**
- `pf validate adr` tool/schema mismatch — not a 50-25 deliverable defect (affects ADR-104/105/106 identically; ADR-107 valid against the commit-enforced ADR-088 schema). **Resolution D (defer)** to a separate validator-hygiene story; already a non-blocking Delivery Finding.

**Decision:** Proceed to review. No Option-B hand-back — every deviation is a sound engineering response to a plan whose premises did not match the real codebase, all logged, all Minor, zero Critical/Major, both architectural keystones (branch-before-barrier, no-write-resolver) verified in code.

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 13 (server source + harness + UI; orchestrator docs excluded as non-code)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 6 findings | 0 high · 2 medium (extract `_broadcast_peer_event`; extract `_build_aside_read_view`) · 4 low (cross-language payload sync + span/harness patterns flagged *acceptable* by the teammate itself) |
| simplify-quality | 1 finding | **1 high** — vacuous `assert room.turn_round() == room.turn_round()` self-comparison in the empty-aside test |
| simplify-efficiency | 5 findings | 0 high · 2 medium (inline `_AsideLlm`; broaden resolver `except` tuple) · 3 low (prompt f-string verbosity; inventory isinstance helper; harness dict consolidation) |

**Applied:** 1 high-confidence fix — `tests/handlers/test_aside_channel_wiring.py` empty-aside test now captures `turn_before` and asserts `turn_round() == turn_before` (the no-turn-advance guarantee is now actually checked, not a tautology). Committed `5e48776`, pushed; targeted regression 12/12 green.

**Flagged for Review (medium — NOT auto-applied, per protocol; with TEA judgement):**
- *Extract `_broadcast_peer_event` / `_build_aside_read_view` helpers* (reuse): premature abstraction — each has exactly one consumer and the handler deliberately mirrors the reviewed `_broadcast_player_speech_to_party` pattern (Architect Resolution-A). Extraction would add indirection without a second caller. Recommend Reviewer concur: defer until a real second consumer exists.
- *Inline `_AsideLlm`* (efficiency): rejected with rationale — the class is the `AsideLLM` Protocol implementation AND the `build_aside_llm` test seam; its `__init__` performs the loud `ANTHROPIC_API_KEY` check (No Silent Fallbacks). Collapsing to a bare function would lose the typed seam the wiring harness monkeypatches. Not ceremony.
- *Broaden resolver `except (JSONDecodeError, ValueError, KeyError, TypeError)` → `except Exception`* (efficiency): rejected with rationale — the narrow tuple is *intentional*. Broadening would swallow genuine programming errors (the opposite of No Silent Fallbacks); the precise tuple catches exactly the parse/validation failure modes and lets unexpected errors propagate loud. Keeping as-is is the safer contract.

**Noted (low):** cross-language `AsideAnswerPayload` sync is intentional protocol-boundary duplication; span-route lambda + harness setup follow canonical/isolated patterns — no action.
**Reverted:** 0.

**Overall:** simplify: applied 1 fix (high-confidence vacuous-assertion repair); 2 medium reuse-extractions and 2 medium efficiency suggestions reviewed and held with documented rationale.

**Quality Checks:** server ruff clean + full suite GREEN (Dev RUN_ID 50-25-dev-green-final: 6211/0/400; the single applied fix is test-internal and re-verified 12/12); UI tsc clean + vitest 1436/0. Quality-pass gate evaluated at exit.

**Handoff:** To Colonel Potter (Reviewer) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 smells; server 6211/0/400 ruff clean; ui 1436/0 tsc/eslint clean | N/A (mechanical baseline only — does not exonerate logic) |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — Reviewer performed edge analysis directly (found the HIGH) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — Reviewer performed silent-failure analysis directly (found the HIGH) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — Reviewer performed test-gap analysis directly |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — Reviewer checked comments/docstrings directly |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — Reviewer checked type design directly |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings — Reviewer performed security analysis directly |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — verify-phase simplify already ran (TEA) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — Reviewer enumerated rule compliance directly |

**All received:** Yes (1 enabled returned; 8 disabled via `workflow.reviewer_subagents`, pre-filled, non-blocking)
**Total findings:** 3 confirmed (1 HIGH, 1 MEDIUM, 1 LOW), 0 dismissed, 0 deferred — all from Reviewer's own analysis (thematic subagents disabled; preflight clean is mechanical only)

## Reviewer Assessment

**Verdict:** APPROVED (RT1 re-review — see "## Reviewer Assessment — RT1 Re-Review" below; the RT0 **REJECTED** record that follows is the preserved audit history, every finding now verified resolved.)

---
**RT0 verdict (historical, superseded by RT1 APPROVED):** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] [SILENT][EDGE] | LLM **call** failure/timeout is uncaught. `await self._llm.complete()` sits inside the `try` but `except` only catches `(json.JSONDecodeError, ValueError, KeyError, TypeError)`. `anthropic.APITimeoutError`/`APIConnectionError`/`APIStatusError` and `asyncio.TimeoutError` subclass none of these → the exception propagates out of `resolve()` and out of the handler aside branch (which does **not** wrap `resolve()` in try/except — only a `with tracer()` block), crashing the `PLAYER_ACTION` handler. **Directly violates spec §6**: "Resolver LLM call **fails/times out** → loud gm-aside … outcome=resolver_error. No turn is lost." The single most-likely production failure (LLM timeout) is unhandled. | `sidequest-server/sidequest/agents/aside_resolver.py:88-101` (handler aside branch `player_action.py` ~256-270 also lacks a defensive wrap) | Catch the LLM-call transport/timeout failure modes (e.g. `anthropic.APIError`, `asyncio.TimeoutError`, `OSError`/`httpx` transport) **in addition to** the parse errors, route to `outcome=resolver_error`. Do NOT use a bare `except Exception` (over-corrects, swallows real bugs) — enumerate the call-failure exception classes explicitly. |
| [MEDIUM] [SILENT] | No logging anywhere in `aside_resolver.py` — spec §6 mandates "+ **ERROR-level log**" on resolver failure. The `resolver_error` branch returns the message but emits zero log, so an LLM failure is invisible to ops and Sebastien's GM-panel lie-detector (CLAUDE.md OTEL principle). Compounds the HIGH: a failure would be both uncaught *and* unlogged. | `sidequest-server/sidequest/agents/aside_resolver.py:101-106` | Add `logger.error(...)` (module logger) on the resolver_error path with the exception detail; keep it loud per No-Silent-Fallbacks. |
| [LOW] | Inconsistent graceful-degradation: the aside branch calls `_resolve_acting_character_name(sd_aside, session._room)` **unguarded**, while the normal path (`player_action.py` ~237-249) wraps the identical call in try/except with a `player_name` fallback (`session.acting_name_resolve_failed … falling_back_to`). An aside crashes where a normal action degrades. | `sidequest-server/sidequest/handlers/player_action.py` ~211 | Mirror the normal-path try/except + `player_name` fallback for the aside branch's acting-name resolution. |

**Data flow traced:** `PLAYER_ACTION{aside:true}` → `PlayerActionHandler.handle` (player_action.py:188 branch, before the ADR-036 barrier ✓ architecturally correct) → `strip_combat_brackets` → empty-guard → `AsideReadView` (real snapshot reads) → `AsideResolver.resolve` → **[HIGH] here: a timeout/API error escapes uncaught** → (happy path) `AsideAnswerMessage` → `room.broadcast(exclude_socket_id=None)` table-wide → returns. The architectural keystones are sound (branch precedes barrier at L188 vs barrier L394; resolver has no write surface — imports `json`/`dataclasses`/`Protocol` only). The defect is purely the error-path contract, not the design.

**Pattern observed:** the resolver_error catch was deliberately narrowed by Dev/TEA (verify-phase efficiency finding "broaden except" was dismissed "narrow tuple intentional"). That dismissal is **incorrect** — it optimized against swallowing programming bugs but missed that spec §6 *requires* catching the LLM-call-failure mode. Per Reviewer rules, a finding matching a spec requirement is confirmed, not dismissible by author judgment. The fix is targeted (enumerate call-failure classes), not a bare `except`.

**Tag coverage (gate-required):**
- [EDGE] — CONFIRMED (HIGH): LLM-timeout boundary unhandled (`aside_resolver.py:88`).
- [SILENT] — CONFIRMED (HIGH + MEDIUM): uncaught call failure + zero logging on the error path.
- [TEST] — CONFIRMED gap: `test_aside_resolver.py::test_unparseable_llm_output_declines_loudly_not_improvises` only feeds *malformed JSON*; **no test exercises a *raising* `complete()`** (timeout/API error). The suite's green status masks the HIGH. TEA must add a raising-LLM case in rework.
- [DOC] — none: docstrings/comments accurate; ADR-107 cross-refs correct; stale RED docstring already corrected in green.
- [TYPE] — none: `AsideAnswerPayload`/`AsideResolution`/`AsideReadView` are typed dataclasses/pydantic; `AsideAnswerMessage` correctly added to the discriminated union; outcome constrained by `_VALID_OUTCOMES`. No stringly-typed leakage.
- [SEC] — none: read-only resolver (no write surface, structurally verified); broadcast rides existing room fan-out (ADR-104/105 untouched); no injection surface (LLM output is parsed as JSON, not eval'd); no secret leakage (API key only via env, fails loud if absent).
- [SIMPLE] — none new: verify-phase simplify already applied the one high-confidence fix; the held medium items (helper extraction, `_AsideLlm` inline) are correctly held — single consumers / typed test seam.
- [RULE] — CONFIRMED (the HIGH is also a SOUL/CLAUDE "No Silent Fallbacks" + spec-§6 rule violation): an uncaught LLM failure is the opposite of failing loud-and-graceful; the fix must be loud (log) AND graceful (resolver_error), not crash.

### Rule Compliance
- **No Silent Fallbacks (SOUL/CLAUDE):** VIOLATION on the resolver error path (HIGH+MEDIUM) — must be loud (log) and not crash. All other new code complies (handler returns typed `_error_msg` on empty aside; `build_aside_llm` fails loud on missing key).
- **Read-only resolver (spec §3):** COMPLIANT — `AsideResolver` public surface = `resolve` only; imports `json`/`dataclasses`/`Protocol`; structurally no write path (verified in spec-check, re-verified).
- **Branch before barrier (spec §3):** COMPLIANT — branch at player_action.py:188, returns ≤ L280; barrier enqueue L394+.
- **Every test suite needs a wiring test (CLAUDE.md):** COMPLIANT — `test_aside_channel_wiring.py` drives the real handler; but the resolver unit suite has the [TEST] gap above (no raising-LLM case).
- **OTEL on every subsystem decision (CLAUDE.md):** PARTIAL — `aside.resolve` span fires on success/parse-error, but a *call failure* currently crashes before/around span attribute-set and emits no log (ties to HIGH+MEDIUM).
- **lang-review python.md — error paths must have logger.error/warning:** VIOLATION — the resolver_error path has no logger (MEDIUM finding).
- **lang-review python.md — no vacuous assertions:** COMPLIANT — the one vacuous self-comparison was caught and fixed in verify (`5e48776`).

### Devil's Advocate
Assume this code is broken. A player on a flaky hotel-wifi MP session types an aside the instant the Anthropic API has a 503 or the request exceeds the client timeout. `_AsideLlm.complete()` raises `anthropic.APIStatusError`/`APITimeoutError`. `AsideResolver.resolve()`'s `except` tuple does not list it → it propagates. The handler aside branch has no try/except around `res = await AsideResolver(...).resolve(...)` (only `with tracer()`), so it propagates into `PlayerActionHandler.handle()` → an unhandled exception on a `PLAYER_ACTION` frame. Best case the WS dispatcher logs `ws.unexpected_error` and the player's aside silently dies with no GM answer and no "ask again" — *worse* than the pre-ADR-107 behaviour, because at least the old path narrated *something*. Worst case it interacts with the MP barrier/dispatch error handling and the table stalls. The spec's whole §6 promise — "No turn is lost; ask again" — evaporates exactly when it matters most (network trouble). A confused user sees their question vanish. Sebastien's GM panel shows no `aside.resolve` outcome and no error log — the lie-detector is blind to the failure, which is the precise anti-pattern CLAUDE.md's OTEL principle exists to prevent. Could a malicious user trigger it deliberately? They can't force an API error, but they *can* submit asides rapidly to raise the odds of hitting a rate-limit (429, an `APIStatusError`) — a cheap way to crash other players' handler frames if the exception isn't contained. The empty-aside path is correctly hardened; the *failure* path is the soft underbelly. This is not theoretical — LLM timeouts are routine, and the dismissed verify finding was a warning shot. Conclusion: the design is sound; the error contract is incomplete and must be closed before this ships. Verdict stands: REJECT.

**Handoff:** Back to TEA (Radar) for RED rework — write the failing test (raising `complete()` → expect `resolver_error`, no exception escapes the handler, ERROR log emitted), then Dev closes the contract.

## TEA Assessment (red rework RT1)

**Tests Required:** Yes — rework to pin the Reviewer HIGH + MEDIUM (spec §6 LLM-call-failure contract).
**Round-trip:** review RT1 (reject → red).

**Test Files (changed):**
- `tests/agents/test_aside_resolver.py` — added `_RaisingLLM` + 4 failing tests: timeout→`resolver_error` (no propagate); connection-error→`resolver_error`; resolver-failure emits an ERROR log (spec §6); parse-failure path *also* emits an ERROR log (was silent).
- `tests/handlers/_harness.py` — added `raising_aside_llm(exc)` (an `AsideLLM` whose `complete()` raises).
- `tests/handlers/test_aside_channel_wiring.py` — added end-to-end §6 test: a raising LLM must NOT crash the real `PlayerActionHandler.handle()`; degrades to a table-visible `ASIDE_ANSWER`, span fires, no turn lost (asker still owes their action).

**Status:** RED — verified by testing-runner (RUN_ID 50-25-tea-red-rework): 5 new tests FAIL for the exact right reasons (uncaught `TimeoutError`/`ConnectionError`; no ERROR log; handler `submit()` raises); 7 pre-existing aside tests still GREEN (no collateral breakage from the import/harness edits); ruff clean.

**Scope discipline:** Targeted at the blocking HIGH (resolver call-failure contract) + MEDIUM (ERROR log), plus the §6 "no turn lost" end-to-end guarantee. The Reviewer's LOW (unguarded `_resolve_acting_character_name` in the aside branch) is non-blocking/Improvement — not pinned with a failing test this round; left as the standing Delivery Finding for Dev's discretion. Tests assert the *spec-named* failure modes (timeout, connection) decline gracefully — they do **not** mandate a bare `except Exception` (the Reviewer explicitly warned against over-correcting; Dev must enumerate call-failure classes).

**Deviations:** No new spec deviations — these tests directly encode spec §6 as the Reviewer interpreted it; nothing diverges from the spec. See `### TEA (test design)`.

**Handoff:** To Major Winchester (Dev) for GREEN rework — catch the LLM call-failure classes in `AsideResolver.resolve()` → `resolver_error`, add the spec §6 `logger.error` on the resolver_error path (both call-failure and parse-failure), and ensure the handler aside branch contains the failure (degrade, never crash). Five tests flip GREEN together.

## Dev Assessment (green rework RT1)

**Implementation Complete:** Yes — Reviewer HIGH + MEDIUM + LOW all closed.
**Round-trip:** review RT1 (reject → red → green).

**Files Changed:**
- `sidequest-server/sidequest/agents/aside_resolver.py` — added module `logger`; split `resolve()` into (a) a broad catch scoped to the single `await self._llm.complete()` I/O call → `resolver_error` + `logger.error` (HIGH: LLM timeout/connection/API failure no longer escapes; decoupled — no anthropic import), and (b) the existing narrow `except (JSONDecodeError, ValueError, KeyError, TypeError)` for parse/validation, now also `logger.error` (MEDIUM: spec §6 ERROR log on both error paths; resolver was previously silent). A genuine programming bug still propagates (narrow except preserved).
- `sidequest-server/sidequest/handlers/player_action.py` — wrapped the aside-branch `_resolve_acting_character_name` in try/except with a `player_name` fallback, mirroring the established normal-path guard (LOW: an aside now degrades like a real action instead of crashing).

**Tests:** GREEN (verified, RUN_ID 50-25-dev-green-rework)
- Full server suite **6216 passed / 0 failed / 400 skipped**; `ruff check .` clean.
- The 5 previously-RED tests now PASS: `test_llm_timeout_declines_loudly_does_not_propagate`, `test_llm_connection_error_declines_loudly`, `test_resolver_failure_emits_error_log`, `test_malformed_output_still_logs_error`, `test_aside_llm_failure_does_not_crash_handler_no_turn_lost`.
- UI untouched this rework (was 1436/0 tsc/eslint clean; no UI change needed — the defect was server-side error contract).

**Deviation logged:** One — the scoped broad `except Exception` at the LLM I/O boundary vs the Reviewer's literal "enumerate the classes" guidance, with full architectural rationale (resolver is Protocol-decoupled; enumerating anthropic classes would couple it to one backend; the scoped boundary-catch honours the Reviewer's actual concern because parse/validation keeps its narrow except). See `### Dev (implementation)` → flagged for Reviewer concurrence on re-review.

**Wiring:** `test_aside_llm_failure_does_not_crash_handler_no_turn_lost` proves end-to-end (real handler): a raising LLM degrades to a table-visible `ASIDE_ANSWER`, the `aside.resolve` span still fires, and no turn is lost — spec §6's full promise, verified through real code.

**Handoff:** To Major Houlihan (Architect) for spec-check re-validation.

## Architect Assessment (spec-check RT1)

**Spec Alignment:** Aligned (the RT1 gap — spec §6 LLM-call-failure contract — is now closed)
**Mismatches Found:** None. 1 Dev deviation reviewed → ACCEPTED.

**Structural gate:** PASS — assessment present, AC coverage intact, deviation subsections well-formed.

**Substantive re-check (verified in code, not from the assessment):**
- **Spec §6 — "Resolver LLM call fails/times out → resolver_error + ERROR-level log. No turn is lost."** Now COMPLIANT. `aside_resolver.py` splits `resolve()`: a broad catch scoped to the single `await self._llm.complete()` call → `resolver_error` + `logger.error(reason=llm_call_failed, exc_info=True)`; a separate narrow `except (JSONDecodeError, ValueError, KeyError, TypeError)` for parse/validation → `resolver_error` + `logger.error(reason=malformed_output, exc_info=True)`. End-to-end "no turn lost" proven by `test_aside_llm_failure_does_not_crash_handler_no_turn_lost` driving the real handler (degrades to a table-visible `ASIDE_ANSWER`, span fires, asker still owes their action). Was the RT1 blocking gap; closed.
- **Spec §3 — read-only, Protocol-decoupled resolver.** Still COMPLIANT and now *defended*: zero `anthropic` import in `aside_resolver.py` (only a rationale comment). The resolver remains LLM-agnostic per spec ("the LLM is injected behind a Protocol").
- **Reviewer LOW** — aside-branch `_resolve_acting_character_name` now try/except + `player_name` fallback (player_action.py:214-225), mirroring the normal path. Closed.
- **AC-4** ("unparseable LLM → loud resolver_error, never invents lore") — strictly *strengthened*: now also covers the call-failure mode per §6. No AC regressed. All 8 ACs remain aligned.

**Deviation review:**
- **Dev RT1 deviation — scoped broad `except Exception` at the I/O call vs the Reviewer's literal "enumerate the call-failure classes"** → ✓ **ACCEPTED (Resolution A — implementation reveals the architecturally-correct approach).** Rationale: spec §6 mandates the *outcome* (call failure → `resolver_error` + ERROR log), not the *catch mechanism*. Enumerating `anthropic.APITimeoutError`/`APIConnectionError`/`APIStatusError` in the resolver would force `import anthropic`, coupling the spec-mandated Protocol-decoupled resolver to one backend AND under-catching any other `AsideLLM` implementation's failures — an architectural regression. The chosen pattern (broad catch scoped to the *single external I/O call*; narrow precise except retained for parse/validation logic) is the canonical "broad at the boundary, precise for logic" idiom and fully honors the Reviewer's *actual* concern: a genuine programming bug in the parse block (e.g. `AttributeError`) is outside the broad scope and still propagates loudly. The Reviewer's literal wording was over-specified for a decoupled component; the book was wrong here and the Dev correctly departed from it. If the Reviewer wants literal enumeration on re-review, the only architecturally-valid locus is the `_AsideLlm` *adapter* (`llm_factory.py`, which legitimately imports anthropic) normalizing `anthropic.APIError` upstream — the resolver's boundary-catch stays regardless. Flagged in `### Dev (implementation)` for Reviewer concurrence.

**Decision:** Proceed to verify. Spec §6 contract closed and verified in code; the sole deviation is the architecturally-superior realization, accepted with rationale; decoupling preserved; no AC regressed; no Option-B hand-back.

## TEA Assessment (verify RT1)

**Phase:** finish (round-trip 1)
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Scope:** RT1 rework delta only (`aside_resolver.py` split try/except + logging, `player_action.py` aside acting-name guard, `_harness.py` raising fake + the new rework tests) — the full story diff was already fan-out simplified in the first verify; re-fanning it would only re-surface already-reviewed/held items. Right-sized to the ~50-LOC surgical fix.

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | clean | 0 — dual try/except correct-by-design; `_RESOLVER_ERROR_ANSWER` already extracted; handler guards are context-specific defensive boundaries, not duplication |
| simplify-quality | clean | 0 — §6 ERROR logging with `exc_info=True` + structured `reason=`; all new rework test assertions meaningful (no vacuous self-comparisons) |
| simplify-efficiency | clean | 0 — split try/except is the accepted decoupled design (not re-flagged per scope note); guards minimal; `_RaisingAsideLlm` a conventional test double |

**Applied:** 0 (all clean). **Flagged:** 0. **Reverted:** 0.
**Overall:** simplify: clean.

**Quality Checks:** server full suite GREEN (Dev RUN_ID 50-25-dev-green-rework: 6216/0/400) + ruff clean; UI untouched this rework (1436/0, tsc/eslint clean). Quality-pass gate evaluated at exit.

**Handoff:** To Colonel Potter (Reviewer) for re-review — the RT1 fix closes the spec §6 LLM-call-failure contract; the one Dev deviation (scoped boundary-catch) is Architect-accepted and flagged for Reviewer concurrence.

## Subagent Results — RT1 Re-Review

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | server 6216/0/400, ruff clean, 0 smells; all 5 rework tests pass | N/A (mechanical baseline) |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — Reviewer re-verified the rework edge (LLM raise) in code |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled — Reviewer re-verified the silent-failure fix (broad I/O catch + ERROR log) in code |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled — verify RT1 simplify-quality (clean) covered the new test quality |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled — Reviewer read the new rationale comments directly (accurate) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled — no type-surface change in the rework |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled — fix narrows a crash path; no new attack surface |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled — verify RT1 simplify (reuse/quality/efficiency) all clean |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled — Reviewer re-checked No-Silent-Fallbacks + spec §6 directly |

**All received:** Yes (1 enabled returned; 8 disabled via `workflow.reviewer_subagents`, non-blocking)
**Total findings:** 0 new; 3 prior (RT0 HIGH/MEDIUM/LOW) all confirmed RESOLVED in code.

## Reviewer Assessment — RT1 Re-Review

**Verdict:** APPROVED

**RT0 findings — closure verified in code (not on the assessment's word):**
- **[HIGH] [SILENT][EDGE] — RESOLVED.** `aside_resolver.py:104-114`: the `await self._llm.complete()` call is now wrapped in its own `try/except Exception` scoped to that single I/O call → returns `resolver_error`. Any LLM timeout/connection/API failure is contained; the handler builds an `ASIDE_ANSWER` from `resolver_error` and returns before the barrier → no handler crash, no turn lost. Spec §6 satisfied end-to-end (proven by `test_aside_llm_failure_does_not_crash_handler_no_turn_lost` driving the real handler).
- **[MEDIUM] [SILENT] — RESOLVED.** `logger.error(..., exc_info=True)` with structured `reason=llm_call_failed` / `reason=malformed_output` on **both** error paths. The resolver is no longer silent; GM-panel/ops can see the failure (CLAUDE.md OTEL principle).
- **[LOW] — RESOLVED.** `player_action.py:214-225`: aside-branch `_resolve_acting_character_name` now `try/except` with `player_name` fallback, mirroring the normal path.

**Tag coverage (gate-required):**
- [EDGE] — RESOLVED: LLM-raise boundary now caught (verified `aside_resolver.py:104`).
- [SILENT] — RESOLVED: I/O failure contained + ERROR-logged on both paths.
- [TEST] — RESOLVED: the masking gap is closed — 5 rework tests (raising-LLM unit + end-to-end handler) green; verify RT1 simplify-quality confirmed assertions meaningful.
- [DOC] — none: the new rationale comments accurately describe the decoupled-boundary design; no stale docs.
- [TYPE] — none: no type-surface change; `AsideResolution`/`_VALID_OUTCOMES` unchanged.
- [SEC] — none: the change strictly *narrows* a crash/availability path; no new surface; no secret handling change.
- [SIMPLE] — none: verify RT1 simplify (reuse/quality/efficiency) all returned clean on the delta.
- [RULE] — RESOLVED: the No-Silent-Fallbacks / spec-§6 violation is closed — failure is now loud (ERROR log) AND graceful (resolver_error), never a crash; the narrow parse-except is retained so genuine programming bugs still propagate (my original concern honored).

**Deviation concurrence:** The Dev RT1 deviation (scoped `except Exception` at the I/O boundary vs my literal RT0 "enumerate the call-failure classes") — I **CONCUR** with the Architect's ✓ ACCEPTED. My RT0 wording was the right instinct against a whole-method bare-except, but for a Protocol-decoupled resolver (spec mandate: "LLM injected behind a Protocol"), enumerating `anthropic.*` would force an `import anthropic` architectural violation and under-catch other implementations. The realized pattern — broad catch scoped to the *single external call*, narrow precise except retained for parse/validation logic — is the canonical "broad at the boundary, precise for logic" idiom and fully satisfies my actual concern (a real logic bug like `AttributeError` still propagates loud). Spec §6 binds the *outcome*, which is now correct. Firm but fair: the engineering reality produced a better fix than the one I prescribed.

**Data flow re-traced:** `PLAYER_ACTION{aside}` → handler L188 (before barrier ✓) → resolver; on LLM failure → broad I/O catch → `resolver_error` + ERROR log → handler builds `ASIDE_ANSWER` → `room.broadcast(exclude_socket_id=None)` → returns; turn/barrier/world untouched. No path now crashes the handler.

**Devil's Advocate (RT1):** The flaky-wifi 503/timeout scenario from RT0 now resolves correctly — `complete()` raises → caught at the boundary → player sees the loud "ask again", the `aside.resolve` span fires with `outcome=resolver_error`, ops see the ERROR log, no turn lost, no table stall. The rapid-aside rate-limit (429) attack is neutralized: an `APIStatusError` is just another exception caught at the boundary. Could the broad catch now hide a real resolver bug? No — resolver logic lives in the second try whose narrow `except (JSONDecodeError, ValueError, KeyError, TypeError)` does not catch `AttributeError`/`NameError`, so a genuine bug still surfaces. No new failure mode introduced; the fix is minimal and well-scoped. Verdict stands: APPROVED.

**Handoff:** To Hawkeye (SM) for the finish phase. **DO NOT merge PRs** — SM handles PR creation and merge.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

### TEA (test design)
- **Gap** (non-blocking): Spec §6 requires empty/whitespace aside text to be rejected at the handler with a typed `ERROR` and **no resolver call**, but neither the plan nor the RED suite covers it. Affects `sidequest-server/tests/handlers/_harness.py` + `tests/handlers/test_aside_channel_wiring.py` (Dev should add an empty/whitespace-aside case asserting typed `ERROR`, resolver/LLM NOT called, no `aside.resolve` span — when factoring the Task 5 harness). *Found by TEA during test design.*
- **Improvement** (non-blocking): The plan's `api-contract.md` correction (Task 8) and ADR-107 (Task 9) live in the **orchestrator** repo, but no orchestrator branch is recorded in the SM session and the orchestrator is on `feat/50-25-aside-channel` off `main` — Dev must ensure the Task 8/9 doc commits land on the orchestrator feature branch, not `main`. Affects `docs/api-contract.md`, `docs/adr/107-out-of-band-aside-channel.md` (commit on the orchestrator `feat/50-25-aside-channel` branch). *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): `pf validate adr` reports errors for ADR-107 (missing bold-key `**Status:**`/`**Date:**`/`**Author:**` *body* fields), but ADR-104/105/106 produce the **identical** errors — the validator enforces a legacy bold-key body style while every modern ADR uses the ADR-088 YAML-frontmatter schema (which is what the commit hook + `regenerate_adr_indexes.py` actually enforce, and which loaded ADR-107 cleanly with correct status/tag routing). Pre-existing tool/schema mismatch, NOT an ADR-107 defect. Affects `scripts/` ADR validator vs `docs/adr/*` (the `pf validate adr` validator should be reconciled to the ADR-088 schema, or retired, in a separate hygiene story). *Found by Dev during implementation.*
- **Improvement** (non-blocking): `AnthropicSdkClient` exposes only `complete_with_tools` (a tool-use loop); there is no generic per-model / single-shot completion seam, so ADR-107's Haiku aside path needed its own minimal `AsyncAnthropic` adapter (`_AsideLlm` in `llm_factory.py`). Other future low-drama single-shot LLM call sites will hit the same gap. Affects `sidequest-server/sidequest/agents/llm_factory.py` (consider a shared single-shot per-model helper if a second consumer appears — not warranted for one caller now). *Found by Dev during implementation.*
- **RT1 GREEN-rework: no new upstream findings.** All three Reviewer RT1 findings (HIGH uncaught LLM call failure, MEDIUM missing ERROR log, LOW unguarded acting-name) are closed in code and verified GREEN (6216/0/400). One judgment-call divergence from the Reviewer's literal fix wording is logged as a Dev deviation (scoped boundary-catch vs enumerate) for Reviewer concurrence. *Found by Dev during RT1 rework.*

### Reviewer (code review)
- **Gap** (blocking): Resolver does not honor spec §6's "LLM call fails/times out → resolver_error, no turn lost" — `await self._llm.complete()` raises (timeout/API/connection) escape the narrow `except` and crash the `PLAYER_ACTION` handler. Affects `sidequest-server/sidequest/agents/aside_resolver.py:88-101` (catch call-failure exception classes → `resolver_error`; the handler aside branch around `player_action.py:256-270` should also be defensible). *Found by Reviewer during code review.*
- **Gap** (blocking): Spec §6 requires an ERROR-level log on resolver failure; `aside_resolver.py` has no logging at all. Affects `sidequest-server/sidequest/agents/aside_resolver.py:101-106` (add module `logger.error` on the resolver_error path). *Found by Reviewer during code review.*
- **Gap** (non-blocking): Resolver unit suite has no test where `complete()` *raises* (only malformed-JSON) — the gap that masked the blocking finding. Affects `sidequest-server/tests/agents/test_aside_resolver.py` (TEA add a raising-LLM case in RED rework). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): aside branch's `_resolve_acting_character_name` is unguarded vs the normal path's try/except+fallback. Affects `sidequest-server/sidequest/handlers/player_action.py` ~211. *Found by Reviewer during code review.*
- **RT1 re-review: no new upstream findings.** All three RT0 findings verified RESOLVED in code (HIGH+MEDIUM at `aside_resolver.py:104-141`, LOW at `player_action.py:214-225`); preflight GREEN 6216/0; deviation concurred with Architect. Story is APPROVED. *Found by Reviewer during RT1 re-review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

### TEA (test design)
- **UI test bound to real `buildSegments` builder, not the plan's `messageToSegments` stub**
  - Spec source: docs/superpowers/plans/2026-05-17-aside-channel.md, Task 6 Step 1
  - Spec text: "`import { messageToSegments } from \"../lib/narrativeSegments\";` ... Use the real exported segment-builder name (grep narrativeSegments.ts ... it may be `messageToSegments` or similar). Adjust the import to match."
  - Implementation: Test imports `buildSegments(messages: GameMessage[])` (the real export) and calls it with a single-element array; `GameMessage` typed `{ type, payload, player_id }`. Added `as Record<string,string>` / `as string` casts so the file runs under vitest AND tolerates `tsc --noEmit` while `MessageType.ASIDE_ANSWER` and the `"gm-aside"` kind do not yet exist.
  - Rationale: The plan explicitly instructed adapting to the real builder name; `messageToSegments` does not exist. Casts keep the test runnable in RED without weakening it — both assertions still fail on real behaviour (verified: undefined member, no gm-aside segment).
  - Severity: minor
  - Forward impact: none — Dev binds the real `MessageType.ASIDE_ANSWER` + `gm-aside` case (plan Tasks 6/7); the casts become inert once the symbols exist.
- **Enum-count pin `test_message_type_complete_count` bumped 48→49 during RED (existing test modified)**
  - Spec source: docs/superpowers/plans/2026-05-17-aside-channel.md, Task 1 Step 6
  - Spec text: "If a test asserts a fixed `len(MessageType)` ... bump it by 1 ... this is an intentional addition, not a regression."
  - Implementation: Bumped the pin to 49 now (RED) with an ADR-107 changelog line, rather than leaving the bump for Dev/GREEN. It currently fails `assert 48 == 49` and goes green when Dev adds `ASIDE_ANSWER`.
  - Rationale: Ties the intentional enum addition to the wire contract as a RED assertion (TDD: the count is a spec claim). Avoids a spurious "regression"-looking failure surfacing mid-GREEN.
  - Severity: minor
  - Forward impact: none — Dev adds the enum member; the pin turns green with the rest of Task 1.
- **Mandatory MP wiring test fails on `ImportError: tests.handlers._harness` (not a feature-gap assertion)**
  - Spec source: docs/superpowers/plans/2026-05-17-aside-channel.md, Task 5 harness note
  - Spec text: "if `tests/handlers/_harness.py` does not exist, factor the 3-player MP setup out of the existing sibling handler test into that module in this step (small refactor, no behavior change)."
  - Implementation: The wiring test imports `make_mp_room`/`submit`/`fake_aside_llm` from `tests.handlers._harness`, which does not exist; it currently errors on import. The 7-guarantee assertion body is fully written per spec §7.
  - Rationale: Per the plan, `_harness.py` is a GREEN deliverable Dev factors from the sibling MP handler test (e.g. `tests/handlers/test_player_action_speech_broadcast.py`). Hand-rolling a session harness in RED would contradict the plan and the "reuse the sibling fixture" instruction. ImportError is the correct, planned RED state for a not-yet-wired feature.
  - Severity: minor
  - Forward impact: blocking-by-design for Dev — Task 5 GREEN MUST create `tests/handlers/_harness.py` (factored, no behavior change) before this centerpiece can fail-then-pass on its real assertions. Called out explicitly in the assessment so it is not mistaken for an incomplete test.
- **No RED test for empty/whitespace aside-text rejection (spec §6 behaviour untested)**
  - Spec source: docs/superpowers/specs/2026-05-17-aside-channel-design.md §6 (Error Handling)
  - Spec text: "Empty/whitespace aside text → rejected at the handler with a typed `ERROR`, no resolver call."
  - Implementation: No unit covers this. It lives in the handler (`if not question: return [_error_msg(...)]`, plan Task 4) — the resolver never sees it, so a resolver unit cannot exercise it, and the handler-level wiring test (`_harness`) does not yet exist at RED.
  - Rationale: The plan supplies no test for this branch and the only seam that can drive it (the MP handler harness) is a GREEN deliverable. Hand-rolling a one-off handler harness in RED solely for this would duplicate the `_harness` Dev must build for Task 5.
  - Severity: minor
  - Forward impact: Dev — when building `tests/handlers/_harness.py` (Task 5), add an empty/whitespace-aside case asserting a typed `ERROR` and that the resolver/LLM was NOT called and no `aside.resolve` span fired. Also raised as a Delivery Finding (Gap) so Reviewer enforces it.

### Dev (implementation)
- **Added typed `AsideAnswerMessage` + discriminated-union entry (beyond plan Task 1's enum+payload)**
  - Spec source: plan Task 1 / Task 4 (`_broadcast_msg(MessageType.ASIDE_ANSWER, AsideAnswerPayload(...))`)
  - Spec text: "find how `NARRATION` is broadcast room-wide in this handler / the session room and mirror it … Do not invent a new broadcast path."
  - Implementation: The real room broadcast path takes typed `*Message` models registered in the `_Phase1Variant` discriminated union (e.g. `TurnStatusMessage`, `PlayerSpeechMessage`), not a generic `(MessageType, payload)` tuple. Added `AsideAnswerMessage(ProtocolBase)` + a `| AsideAnswerMessage` arm in the union, and broadcast via the real `room.broadcast(msg, exclude_socket_id=None)` mirroring `_broadcast_player_speech_to_party`.
  - Rationale: Mirrors the real, reviewed broadcast pattern exactly (the plan's abstraction had no concrete codebase form); a discriminated-union arm is mandatory for the message to (de)serialize.
  - Severity: minor
  - Forward impact: none — purely additive to the union; UI side already added the sibling `ASIDE_ANSWER` type (Task 6).
- **`build_aside_llm()` is a new single-shot Haiku adapter, not a wrap of an existing tier builder**
  - Spec source: plan Task 4 Step 3
  - Spec text: "If a Haiku-tier client builder exists, add a thin `build_aside_llm()` … If the factory exposes a generic per-model builder, wrap it."
  - Implementation: `llm_factory.py` exposes only `build_llm_client()` (env-routed, tool-use loop); no Haiku-tier or per-model builder exists. Added `_AsideLlm` — a minimal `AsyncAnthropic` single-shot adapter (model `claude-haiku-4-5-20251001`, `max_tokens=512`) satisfying the resolver's `AsideLLM`. Fails loudly if `ANTHROPIC_API_KEY` unset (No Silent Fallbacks).
  - Rationale: ADR-101 per-call routing + SOUL "Cost Scales with Drama" — an aside is lowest-drama, cheapest tier, no tool-use loop. Distinct call site, not a narrator-client reinvention.
  - Severity: minor
  - Forward impact: Reviewer — the production aside path requires `ANTHROPIC_API_KEY`; the wiring tests inject `fake_aside_llm` via the real `build_aside_llm` factory seam (no live call in tests).
- **Task 5 harness built from scratch driving the real handler; not factored from a sibling MP fixture**
  - Spec source: plan Task 5 harness note
  - Spec text: "if `tests/handlers/_harness.py` does not exist, factor the 3-player MP setup out of the existing sibling handler test into that module (small refactor, no behavior change)."
  - Implementation: No sibling MP-room fixture exists — every `tests/handlers/` test is `MagicMock`-based (`test_player_action_speech_broadcast.py` mocks the room; `test_action_reveal.py` mocks session/snapshot). Built `_harness.py` from scratch: real `SessionRoom(MULTIPLAYER)` + real `GameSnapshot`/`TurnManager`/`SqliteStore` + loaded `caverns_and_claudes` pack + real `_SessionData`, driving the real `PlayerActionHandler.handle()`. Only the orthogonal narrator is stubbed (`_StubSession._execute_narration_turn` performs the *real* `turn_manager.record_interaction()` the production narrator does post-barrier, so round-advance is faithful); the aside path is 100% real.
  - Rationale: The plan's factor-source does not exist; a faithful real-handler harness is the only way to satisfy spec §7's "drive the real `PLAYER_ACTION{aside:true}` path" without fabricating the lie-detector centerpiece.
  - Severity: minor
  - Forward impact: Reviewer — verify the harness faithfully drives real code (it does: real room/snapshot/barrier/broadcast/span; only LLM prose skipped, with the real counter side effect preserved).
- **Deleted obsolete test `test_aside_player_action_strips_brackets_before_narrator` (tests/server/test_combat_brackets.py)**
  - Spec source: spec §1 + ADR-107 (the behavior change itself)
  - Spec text: "Missing: any server branch on `aside` — asides flow through the ADR-036 barrier and the full narrator path identically to in-fiction actions."
  - Implementation: That test asserted `aside=True` still reaches `run_narration_turn` after a bracket strip — the exact half-wired behaviour ADR-107 removes. Under ADR-107 an aside never reaches the narrator. Deleted it (left an explanatory tombstone comment); combat-strip-still-applies is now covered by `test_aside_channel_wiring.py` (centerpiece + combat-bracket-only→ERROR). The sibling `test_non_aside_player_action_does_not_strip` is unchanged and still valid.
  - Rationale: Mocking `ANTHROPIC_API_KEY` to keep it passing would preserve a superseded contract and bury the behaviour change (anti-pattern). Per "delete dead code in the same PR", an obsolete test pinning removed behaviour is removed alongside the change.
  - Severity: minor
  - Forward impact: none — the removed behaviour is intentionally gone; ADR-107 documents it.
- **GREEN-rework RT1: scoped broad `except Exception` at the LLM I/O call instead of the Reviewer's literal "enumerate the call-failure classes"**
  - Spec source: Reviewer Assessment (review RT1) fix guidance — `aside_resolver.py:88-101`
  - Spec text: "Catch the LLM-call transport/timeout failure modes … in addition to the parse errors … Do NOT use a bare `except Exception` (over-corrects, swallows real bugs) — enumerate the call-failure exception classes explicitly."
  - Implementation: Split `resolve()` into two trys. The `await self._llm.complete()` call is wrapped in `except Exception` **scoped to that single external call only**; JSON parse/validation keeps its narrow precise `except (json.JSONDecodeError, ValueError, KeyError, TypeError)`. Both paths emit `logger.error(..., exc_info=True)`.
  - Rationale: `AsideResolver` is deliberately decoupled from the concrete LLM behind the `AsideLLM` Protocol (spec: "The LLM is injected behind a Protocol"). Enumerating `anthropic.APITimeoutError`/`APIConnectionError`/`APIStatusError` would force the resolver to `import anthropic` — an architectural violation that couples the Protocol-agnostic resolver to one backend, and would still under-catch any other `AsideLLM` implementation's failures. A broad catch *scoped to the single I/O boundary call* satisfies the Reviewer's actual concern (don't mask resolver-logic bugs) because the parse/validation block keeps its narrow typed except, so a genuine programming bug (e.g. `AttributeError`) still propagates loudly. This is the standard "broad at the I/O boundary, precise for logic" pattern, not the whole-method bare-except anti-pattern the Reviewer warned against. Documented inline with `# noqa: BLE001` + rationale.
  - Severity: minor
  - Forward impact: Reviewer re-review — if the Reviewer still wants literal enumeration, the correct locus is the `_AsideLlm` *adapter* in `llm_factory.py` (which legitimately imports anthropic) normalizing `anthropic.APIError` → a domain error; the resolver's decoupled boundary-catch would remain. Flagged for Reviewer concurrence.

### Reviewer (audit)

Stamps on logged deviations:
- **Dev#1 `AsideAnswerMessage` + union arm** → ✓ ACCEPTED by Reviewer: the discriminated-union arm is mandatory for (de)serialization and mirrors `PlayerSpeechMessage` exactly; correct realization of "mirror the real broadcast path."
- **Dev#2 `build_aside_llm` single-shot adapter** → ✓ ACCEPTED by Reviewer: no tier builder existed; minimal `AsyncAnthropic` adapter is the right ADR-101 realization and fails loud on missing key. (Note: its error *propagation* is the subject of a separate Reviewer finding — the adapter itself is sound; the resolver's failure to catch its raises is the defect.)
- **Dev#3 harness built from scratch** → ✓ ACCEPTED by Reviewer: verified it drives the real `PlayerActionHandler.handle()` (real room/snapshot/barrier/store/pack); only orthogonal narrator stubbed with the real `record_interaction` side effect preserved. Faithful, not fabricated.
- **Dev#4 deleted obsolete `test_aside_player_action_strips_brackets_before_narrator`** → ✓ ACCEPTED by Reviewer: it pinned the exact pre-ADR-107 aside→narrator behaviour this story removes; deletion (tombstoned) is correct hygiene; behaviour re-covered by the wiring suite.
- **TEA test-design deviations (buildSegments bind / enum-pin bump / harness ImportError-RED / empty-aside gap)** → ✓ ACCEPTED by Reviewer: all sound, plan-anticipated, and the empty-aside gap was correctly closed in green.
- **Verify-phase efficiency finding "broaden resolver `except`" (held by TEA/Dev with rationale "narrow tuple intentional")** → ✗ FLAGGED by Reviewer: the held rationale is wrong. The narrow tuple does not catch the LLM-**call**-failure mode that **spec §6 explicitly mandates** routing to `resolver_error`. A finding that matches a spec requirement is confirmed, not dismissible by author judgment. Escalated to the HIGH finding in the Reviewer Assessment. (Fix is targeted enumeration of call-failure classes, NOT the bare `except Exception` the efficiency subagent loosely suggested.)

Undocumented deviation TEA/Dev did not log:
- **Resolver error contract is narrower than spec §6:** Spec §6 says "Resolver LLM call **fails/times out** → loud gm-aside … + ERROR-level log + outcome=resolver_error. No turn is lost." Code (`aside_resolver.py:88-106`) only handles malformed-*output* errors (JSON/validation) and emits **no log**; an LLM **call** failure/timeout escapes uncaught and the resolver_error path is silent. Spec said graceful+logged on call failure; code crashes+silent. Severity: **HIGH** (blocking) for the uncaught-call-failure; **MEDIUM** for the missing ERROR log. Not previously documented as a deviation by TEA or Dev — surfaced by Reviewer adversarial analysis. Drives the REJECT. → **RT1 RESOLVED:** verified closed in code (`aside_resolver.py:104-141` split try + `logger.error` on both paths); the prior RT0 REJECT is discharged.

RT1 re-review stamps:
- **Dev RT1 deviation — scoped broad `except Exception` at the I/O call vs RT0 "enumerate the classes"** → ✓ ACCEPTED by Reviewer (RT1): I **concur** with the Architect's acceptance. Spec §6 binds the outcome (call failure → `resolver_error` + ERROR log), not the catch mechanism; enumerating `anthropic.*` would force an `import anthropic` architectural violation in the Protocol-decoupled resolver and under-catch other `AsideLLM` implementations. The scoped-broad-at-I/O-boundary + narrow-precise-for-logic pattern fully honors my RT0 concern (a real logic bug still propagates via the retained narrow except). My RT0 literal wording was over-specified for a decoupled component — corrected here, fair and final.

### Architect (reconcile)

**Definitive deviation manifest — story 50-25 (ADR-107 out-of-band aside channel).** Audit sources loaded: story context (session-embedded Context & Specification + 8 ACs), epic context (epic-50 — pingpong-archive cleanup; no per-story planning doc beyond the spec/plan cited inline), PRD/spec `docs/superpowers/specs/2026-05-17-aside-channel-design.md` + plan `docs/superpowers/plans/2026-05-17-aside-channel.md` (both verified present), sibling-story ACs (epic-50 stories are independent — no shared AC surface with 50-25), in-flight logs (`### TEA (test design)` ×4, `### Dev (implementation)` ×5), AC accountability table.

**Existing-entry verification (no rewrites; corrections annotated inline if any):**
- All 4 TEA + 5 Dev entries carry the full 6 fields (Spec source / Spec text / Implementation / Rationale / Severity / Forward impact). Spec-source paths resolve to real files (the spec + plan above; `tests/...`, `sidequest/...` paths confirmed in the diff). Quoted spec text checked against the actual spec/plan — accurate. Implementation descriptions match the merged code (re-verified the resolver split-try, the `AsideAnswerMessage` union arm, the harness, the obsolete-test deletion). Forward-impact statements accurate (all "none"/local except the RT1 scoped-except, correctly flagged for Reviewer concurrence — now obtained). **No inaccurate or under-filled entry found; no annotation required.**
- Reviewer audit (RT0 stamps + the undocumented HIGH it surfaced + RT1 RESOLVED/concur stamps) is internally consistent with the Dev RT1 fix and the two Architect spec-check assessments (RT0 Aligned, RT1 Aligned).

**AC deferral verification:** All 8 ACs were implemented and verified (Dev Assessment "all 8 ACs"; Reviewer RT1 APPROVED). The AC accountability table records **zero** DEFERRED/DESCOPED ACs — this step is a no-op (nothing to cross-check against Reviewer findings).

**Missed deviations:** None. The implementation tracked the spec/plan tightly; every judgment departure is already logged with rationale. Specifically checked and confirmed *not* deviations: spec §5's "MAY be journaled to a separate lightweight aside log" is explicitly optional — the chosen non-implementation is spec-permitted, not a divergence; spec §9 out-of-scope items (private/sealed asides, aside-driven world change, TTS) were all respected; the `AsideAnswerPayload` field set and `MessageType.ASIDE_ANSWER` literal are server/UI-consistent.

- No additional deviations found.

**Manifest summary for the boss:** One story, one review round-trip. The RT0 REJECT was a genuine spec-§6 gap (uncaught LLM-call failure + missing ERROR log) the Reviewer's adversarial pass caught after green/spec-check/verify and a clean preflight all missed — the system worked as designed. RT1 closed it with an architecturally-superior, decoupling-preserving fix; the sole mechanism-level deviation from the Reviewer's literal guidance was independently judged sound by Architect and concurred by Reviewer. All deviations Minor, fully logged, zero Critical/Major outstanding, zero AC deferrals. The story is audit-clean from this session file alone.

## References

- **Spec:** `docs/superpowers/specs/2026-05-17-aside-channel-design.md`
- **Plan:** `docs/superpowers/plans/2026-05-17-aside-channel.md`
- **Related ADRs:** ADR-036 (multiplayer barrier), ADR-063 (aside handler, Rust era), ADR-082 (port), ADR-101 (narrator LLM routing), ADR-107 (this feature — to be authored)
- **Playtest Finding:** Beneath Sünden 2026-05-17 MP, F6 — players burning turns on clarification questions
- **Port Drift:** ADR-082 Python port dropped the Rust `handle_aside()` seam to a 10-line combat-strip; this story restores the full seam