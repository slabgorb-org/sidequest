---
story_id: "158-15"
jira_key: ""
epic: "158"
workflow: "tdd"
---
# Story 158-15: QUESTS not re-emitted on connect/resume — mirror the FATE_STATE bootstrap re-emit so the Quests tab survives reload/reconnect

## Story Details
- **ID:** 158-15
- **Jira Key:** (none — YAML-based sprints)
- **Workflow:** tdd
- **Repo:** server
- **Stack Parent:** none
- **Type:** bug
- **Points:** 2
- **Priority:** p2

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-24T08:48:52Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-24T08:25:18.219588+00:00 | 2026-06-24T08:27:05Z | 1m 46s |
| red | 2026-06-24T08:27:05Z | 2026-06-24T08:33:42Z | 6m 37s |
| green | 2026-06-24T08:33:42Z | 2026-06-24T08:40:03Z | 6m 21s |
| review | 2026-06-24T08:40:03Z | 2026-06-24T08:48:52Z | 8m 49s |
| finish | 2026-06-24T08:48:52Z | - | - |

## Branch Strategy
**Branch Strategy:** gitflow (feat/158-15-quests-reemit-connect-resume)

## Sm Assessment

**Disposition:** Set up and routed to TEA (RED) — clean, well-understood fix.

**Root-cause class (recurring, 4th instance):** The `_State.Playing` resume bootstrap in `sidequest-server/sidequest/server/connect.py` does not re-emit something a per-turn emitter emits — so it vanishes after reconnect/reload. Same class already fixed for FATE_STATE, LOCATION_DESCRIPTION, and FATE_DEFEND_REQUEST (153-7). Here the casualty is the QUESTS payload → the Quests tab goes blank on reload.

**Approach (for TEA/Dev):** Mirror the FATE_STATE bootstrap re-emit. `_maybe_emit_fate_state` is the reference; add the parallel `_maybe_emit_*` for QUESTS next to the existing resume re-emits. RED writes a failing test proving QUESTS is not re-emitted on reconnect today; GREEN adds the helper. **Wiring test required** — prove the re-emit fires through the production connect/resume path, not just in isolation.

**Scope:** server-only, 2pt, no Jira (YAML sprints). Branch targets `develop`.

## TEA Assessment

**Tests Required:** Yes

**Test Files:**
- `tests/server/test_quests_resume.py` — integration-level resume re-emit tests (real wry_whimsy/oz content pack + real `WebSocketSessionHandler` connect path), mirroring `test_fate_state_resume.py`.

**Tests Written:** 2 tests covering AC1–AC4.
- `test_slug_resume_emits_quests_before_first_turn` — **RED** (fails today): seeds a resumable SOLO session with a persisted quest spine (quest + anchor + stakes), drives a real `connect`, asserts a `QuestsMessage` is in the bootstrap carrying the *persisted* spine (stakes, title, anchor). This is the AC2/AC3 behavioral proof AND the AC4 production-path wiring test in one — it fails purely on `assert quest_msgs` (QUESTS absent from bootstrap), confirming the gap.
- `test_slug_resume_empty_quest_spine_emits_no_quests` — **guard** (green today, must stay green): an empty quest spine must emit NO QUESTS on resume, pinning the wire-parity omission contract so the Dev fix routes through the gated `_maybe_emit_quests` (`_is_empty_spine` no-op) rather than blanket-broadcasting an empty frame on every resume.

**Status:** RED (1 failing as designed + 1 guard green).

**Verification note:** Ran pytest **directly** (`uv run pytest -n0`) rather than via the `testing-runner` subagent — known reliability issues (testing-runner fabricates per-test prose and clobbers the session file). Result is trustworthy ground truth: `1 failed, 1 passed`. The empty-spine guard passing proves imports/fixtures/connect-handler/resume all work, isolating the failure to the genuine bug.

### Rule Coverage

| Rule (python.md) | Test(s) / How enforced | Status |
|------|---------|--------|
| #6 Test quality | Both tests assert specific values (`active_stakes ==`, title-in-set, `== []`) — no vacuous `assert True`/truthy-only; the lone `assert quest_msgs` guards an index and is immediately followed by typed value checks | enforced |
| #9 Async/await | Both `@pytest.mark.asyncio`; `await handler.handle_message(...)` — no missing await, no blocking call in async | enforced |
| #3 Type annotations | Test fns + helpers fully annotated (`-> None`, `tmp_path: Path`, `monkeypatch: pytest.MonkeyPatch`) | enforced |
| #10 Import hygiene | Explicit imports, no star imports | enforced |

**Rules checked:** 4 of 13 lang-review rules are test-applicable in RED. The remaining 8 (#1 silent-except, #2 mutable-defaults, #4 logging, #5 path, #7 resource-leaks, #8 deserialization, #11 input-validation, #12 deps) govern the **production** re-emit code Dev adds in GREEN — deferred to Dev (RED adds no production code).
**Self-check:** 0 vacuous tests found (reviewed both for `let _=` / `assert True` / always-None patterns).

**Handoff:** To Dev (Agent Smith) for GREEN — add a gated `_maybe_emit_quests` call to the `sidequest/handlers/connect.py` resume bootstrap, next to the `_maybe_emit_fate_state` re-emit (line ~1817).

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/handlers/connect.py` — added a gated `_maybe_emit_quests` re-emit to the `_State.Playing` resume bootstrap (`handle()`), immediately after the `_maybe_emit_fate_state` re-emit (~line 1817). Mirrors the FATE_STATE pattern: function-local import + `_maybe_emit_quests(session, snapshot=snapshot, emit_fn=lambda msg, _label: bootstrap_msgs.append(msg))`. **No `sd`/ruleset gate** (QUESTS is genre-agnostic, ADR-137). Passing `session` — the same `WebSocketSessionHandler` the per-turn path passes as `self` — seeds `_last_quests_sig`, so turn 1 won't re-emit an identical frame. Re-uses the existing gated emitter, which already fires the `quests.emitted` OTEL span (lie-detector intact).

**Tests:** 2/2 target passing (GREEN). 41/41 sibling resume/connect/quests regression tests green. Ruff clean on changed files.
**Branch:** feat/158-15-quests-reemit-connect-resume (pushed)

**Verification:** Ran `uv run pytest -n0` directly (testing-runner reliability caveat — fabricates prose / clobbers session). Target file: `2 passed`. Regression set (test_fate_state_resume, test_location_description_resume, test_quests_emit, test_quests_emit_wiring, test_quests_resume, test_session_handler_slug_resumed): `41 passed` with OTEL **enabled** (an interim `OTEL_SDK_DISABLED=true` falsely red-ed two span-assertion tests — removed; the failures were the env flag, not the code). `ruff check` on connect.py + the test: All checks passed.

**Handoff:** To verify phase (TEA — simplify + quality-pass).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (GREEN: 2/2 new + 37/37 regression, ruff clean, 0 smells, strictly additive) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — domain covered by Reviewer self-review, tagged [EDGE] |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — covered by Reviewer self-review, tagged [SILENT] |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — covered by Reviewer self-review, tagged [TEST] |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — covered by Reviewer self-review, tagged [DOC] |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — covered by Reviewer self-review, tagged [TYPE] |
| 7 | reviewer-security | Yes | clean | none (4 rule-groups checked, 0 violations) | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — covered by Reviewer self-review, tagged [SIMPLE] |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — covered by Reviewer self-review, tagged [RULE] |

**All received:** Yes (2 enabled subagents returned clean; 7 disabled via `workflow.reviewer_subagents`, each domain covered by Reviewer self-review)
**Total findings:** 0 confirmed blocking, 0 dismissed, 1 deferred (RELATIONSHIPS sibling resume gap — out of scope for 158-15, filed as a non-blocking delivery finding).

## Reviewer Assessment

**Verdict:** APPROVED

A textbook 4th-instance fix: one gated `_maybe_emit_quests` re-emit added to the `_State.Playing` resume bootstrap, mirroring the `_maybe_emit_fate_state` re-emit directly above it. Minimal, strictly additive (25 prod lines, 0 deletions), reuses the existing gated emitter, and preserves the `quests.emitted` OTEL lie-detector on the resume path.

**Observations (10):**
- `[PRE]` Preflight GREEN — 2/2 new tests, 37/37 regression, ruff clean, 0 smells. (reviewer-preflight, high confidence.)
- `[SEC]` Perception firewall intact — the QUESTS spine is session-global by design (ADR-137; `session.py` quest fields are not player-keyed) and the resume re-emit delivers to the **connecting socket only** via `bootstrap_msgs` (strictly narrower than the per-turn `room.broadcast` fan-out). Read-only projection (`build_quests_payload` is a pure reader), no new injection surface, counts-only logging. (reviewer-security, 4 rule-groups, 0 violations.)
- `[EDGE]` (subagent disabled — Reviewer self-review) `snapshot` None-safety: `snapshot` is dereferenced upstream (`snapshot.player_seats.get(...)` ~connect.py:1700) so it is non-None at the call site; and `_is_empty_spine(None)` is a clean no-op via getattr defaults (`quests_emit.py:42-44`) — double-safe.
- `[SILENT]` (self) The empty-spine early return and the change-signature gate are intentional, documented no-ops (wire-parity omission contract), not silent fallbacks. `emit_fn` commits the signature **only after** the broadcast (`quests_emit.py:98-102`), so a failed emit retries next turn rather than silently skipping a never-delivered frame.
- `[TEST]` (self) Two integration tests assert **specific persisted values** (`active_stakes ==`, title-in-set, anchor-in-set, `== []`) against the real connect handler + real wry_whimsy/oz content pack — behavior, not source-text wiring. The core test IS the AC4 wiring test. No vacuous assertions, no skips.
- `[DOC]` (self) The new 16-line comment is accurate (playtest origin, 4th-instance framing, empty-spine gate, genre-agnostic/no-ruleset-gate, sig-seeding) and matches the surrounding comment density of the FATE_STATE block. No stale/misleading claims.
- `[TYPE]` (self) No new types; reuses typed `QuestsMessage`/`QuestsPayload`. The `_maybe_emit_quests(handler, *, snapshot, emit_fn)` signature is matched correctly — **no `sd`** (unlike fate), consistent with the genre-agnostic emitter.
- `[SIMPLE]` (self) Function-local import + `emit_fn` lambda mirror the established FATE_STATE / LOCATION_DESCRIPTION pattern in this same file (function-local imports avoid a circular import from `websocket_handlers`). No over-engineering.
- `[RULE]` (self) `_SIG_ATTR` isolation verified: quests uses `_last_quests_sig`, fate uses `_last_fate_state_sig` — distinct attributes on the same handler, so the resume seed and per-turn read share `_last_quests_sig` (no double-emit on turn 1) with **no** cross-contamination with fate's signature. python.md enumeration below.
- `[VERIFIED]` OTEL lie-detector intact — the reused `_maybe_emit_quests` fires the `quests.emitted` span on the resume path too (CLAUDE.md OTEL principle); evidence: `quests_emit.py:80-90`.

### Rule Compliance (python.md, enumerated against the diff)

| # | Rule | Verdict |
|---|------|---------|
| 1 | Silent exception swallowing | Compliant — no try/except in the diff |
| 2 | Mutable default arguments | Compliant — no new fn defs with mutable defaults |
| 3 | Type annotation gaps | Compliant — no new public fn; test fns + helpers annotated (`-> None`) |
| 4 | Logging coverage/correctness | Compliant — no new logging; reused emitter logs counts only, no PII |
| 5 | Path handling | Compliant — test uses `pathlib.Path`, no string concat |
| 6 | Test quality | Compliant — specific-value assertions, no vacuous/skip |
| 7 | Resource leaks | Compliant — no `open()`/connections; `asyncio.Queue` only |
| 8 | Unsafe deserialization | Compliant — none; snapshot already deserialized upstream |
| 9 | Async/await pitfalls | Compliant — tests `await handle_message`; no blocking calls |
| 10 | Import hygiene | Compliant — function-local import (intentional, matches file pattern); no star imports |
| 11 | Input validation at boundaries | Compliant — read-only projection of persisted state; no new boundary |
| 12 | Dependency hygiene | N/A — no dependency changes |
| 13 | Fix-introduced regressions | Compliant — 37/37 regression green |

### Devil's Advocate

Argue it is broken. **Double-emit on turn 1?** The strongest attack: if `session` (the `ConnectHandler.handle` param) were NOT the same object the per-turn path passes as `self`, the resume call would seed `_last_quests_sig` on the wrong object and turn 1 would re-broadcast a duplicate QUESTS. This is the one load-bearing assumption. It is refuted: `handle(self, session: WebSocketSessionHandler, ...)` receives the live session handler, and FATE_STATE performs the byte-identical pattern (passing `session`) — proven in 153-7 / `test_fate_state_resume`. Even in the worst case (assumption wrong), the failure is a single duplicate QUESTS frame the UI replaces idempotently — cosmetic, never state corruption. **None crash?** Refuted twice (upstream deref + getattr no-op). **MP cross-player leak?** Refuted — global spine, connecting-socket delivery. **Empty-spine world (beneath_sunden) shows no QUESTS on resume?** That is *correct* behavior (wire-parity omission); 158-16 separately seeds the opening spine — not a defect of this change. **Huge quest text → DoS?** `active_stakes` is length-guarded at the model boundary (`session.py`), per-quest bounded; nothing unbounded enters here. **Ordering (fate before quests, vs per-turn quests before fate)?** Irrelevant — independent reactive frames the UI consumes on separate channels. No avenue produces a Critical/High. The change is correct.

**Sibling observation (non-blocking, deferred):** RELATIONSHIPS is *also* not re-emitted in the resume bootstrap (`grep _maybe_emit_relationships sidequest/handlers/connect.py` → empty), while the per-turn path emits it alongside quests/fate_state — a likely **5th instance** of this exact class. Out of scope for 158-15 (QUESTS-only); filed as a delivery finding so it can be picked up as a sibling story.

**Data flow traced:** persisted `snapshot.quest_log/quest_anchors/active_stakes` (DB) → `build_quests_payload` (pure projection) → `QuestsMessage` → `bootstrap_msgs` → connecting player's socket. Safe: read-only, player-scoped delivery, change-gated.
**Pattern observed:** resume re-emit mirroring per-turn reactive emitter — `sidequest/handlers/connect.py:1823-1845` (the new block) mirrors `:1817-1822` (FATE_STATE).
**Error handling:** empty-spine no-op + post-broadcast sig commit — no swallowed errors, no silent fallback.

**Handoff:** To SM (Morpheus) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): The story context (`context-story-158-15.md`) and the SM Assessment both name the bootstrap file as `sidequest/server/connect.py`, but the real resume bootstrap is `sidequest/handlers/connect.py` (the `sidequest/server/connect.py` path does not exist). The per-turn QUESTS emitter is `sidequest/server/websocket_handlers/quests_emit.py::_maybe_emit_quests(handler, *, snapshot, emit_fn)` — note it takes **no `sd`** (unlike `_maybe_emit_fate_state`, which is ruleset-gated and takes `sd`); QUESTS is genre-agnostic, so the resume helper needs **no** ruleset gate. Affects `sidequest/handlers/connect.py` (Dev's GREEN navigation). *Found by TEA during test design.*

### Dev (implementation)
- No upstream findings during implementation. (Confirmed TEA's path finding: implemented in `sidequest/handlers/connect.py`, not the stale `sidequest/server/connect.py`; per-turn `_maybe_emit_quests` is `sd`-less and genre-agnostic exactly as TEA noted.)

### Reviewer (code review)
- **Improvement** (non-blocking): RELATIONSHIPS is *not* re-emitted in the `_State.Playing` resume bootstrap either — the per-turn path emits relationships/quests/fate_state, but the bootstrap re-emits only fate_state and (now) quests. The Relationships tab likely has the **same** blank-until-turn-1 resume gap — a probable 5th instance of this connect/resume re-emit class. Affects `sidequest/handlers/connect.py` (mirror the same `_maybe_emit_relationships(session, snapshot=snapshot, emit_fn=...)` re-emit). Out of scope for 158-15 (QUESTS-only) — candidate sibling story. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- No deviations from spec.

### Reviewer (audit)
- **TEA: No deviations from spec.** → ✓ ACCEPTED by Reviewer: the test design faithfully mirrors `test_fate_state_resume`; no spec divergence.
- **Dev: No deviations from spec.** → ✓ ACCEPTED by Reviewer: the implementation mirrors the FATE_STATE re-emit exactly (gated emitter, `session` handler for sig-seed, no `sd`/ruleset gate per the genre-agnostic emitter) — matches the story context approach precisely.
- No undocumented deviations spotted: the diff is strictly the QUESTS re-emit + its tests; no scope creep.