---
story_id: "71-23"
jira_key: ""
epic: "71"
workflow: "tdd"
---
# Story 71-23: Solo narration streaming — wire messages.stream into existing UI delta path

## Story Details
- **ID:** 71-23
- **Epic:** 71 (Playtest bugfix — uncovered findings, coyote_star MP 2026-05-27)
- **Jira Key:** (none — no Jira integration)
- **Workflow:** tdd
- **Type:** bug/feature
- **Points:** 5
- **Priority:** p2
- **Repos:** sidequest-server, sidequest-ui
- **Stack Parent:** none

## Problem Statement

Solo narration streaming is **partially implemented and unwired**. The server
emits `NarrationDelta` messages (streaming narration chunks) during text
generation, but the client's UI does not consume them. The client's
`useStateMirror` and narration accumulation paths (ADR-133) are ready to
receive streaming deltas, but the WebSocket message wiring is incomplete.

**What exists:**
- Server: `NarrationDelta` payload type defined (messages.py:303-317)
- Server: Narrator agent emits streaming deltas during Anthropic SDK streaming
- Client: `useStateMirror` hook prepared to merge `state_delta` from messages (ADR-133)
- Client: `NarrationScroll` component exists (ready to consume narration deltas)

**What's missing:**
- Server: Route `NarrationDelta` messages through the WebSocket handler + emit path
- UI: Consume `NarrationDelta.payload.delta` (streaming text chunks) in the
  narration accumulator, displaying them progressively as they arrive
- UI: Integration test that asserts streaming deltas are captured and displayed

This is a **pure wiring task** — connect two already-built subsystems across
the WebSocket boundary.

## Technical Approach

### Phase 1: Server-Side Wiring (sidequest-server)

1. **Identify the streaming narration emission point**
   - Find where the Anthropic SDK's streaming response is consumed
   - Locate the loop that processes `event.type == "content_block_delta"`
   - Verify the delta text is available (it will be)

2. **Emit `NarrationDelta` to the WebSocket**
   - Construct a `NarrationDelta` message from the streaming chunk
   - Emit it directly to the active session's WebSocket (no event-log persistence —
     these are ephemeral per ADR-133)
   - Handle buffering/batching if needed (do not emit per-character; chunk
     naturally on SDK boundaries)

3. **Route handling**
   - `NarrationDelta` bypasses the `GameMessage` discriminated union (it uses
     `kind`, not `type`) and the event log — it is delivered live during streaming
   - Ensure the handler does not attempt to persist or event-source the delta
   - Verify per-session isolation (only the active player session receives the
     delta, not all connected sockets)

4. **OTEL observability**
   - Emit a `narration.delta.sent` span with the chunk length when each delta
     is emitted
   - Emit a `narration.delta.stream.started` span when streaming begins
   - Emit a `narration.delta.stream.ended` span when the canonical `narration`
     event lands (end-of-stream marker)

### Phase 2: Client-Side Wiring (sidequest-ui)

1. **Extend the WebSocket message handler**
   - The existing `useWebSocket` hook handles `GameMessage` discriminated
     union; add a handler path for `NarrationDelta` (kind-based dispatch)
   - Parse the incoming `NarrationDelta.payload.delta` string

2. **Accumulate into the narration buffer**
   - The narration buffer (ADR-133 Narration Accumulator, `NarrationScroll`)
     currently waits for the full canonical `narration` text
   - Extend the buffer to accumulate streaming deltas **before** the canonical
     text arrives
   - When a `NarrationDelta` arrives, append its text to a running `streamingText`
     accumulator (reset on new turn)
   - When the canonical `narration` message lands, verify it matches the
     accumulated streaming text (or log a mismatch)

3. **Display streaming text progressively**
   - Render the accumulated `streamingText` in real-time as deltas arrive
   - Once the canonical `narration` message lands, replace with the authoritative
     text (should be identical if streaming completed cleanly)
   - No double-rendering: if the canonical text arrived and was already
     displayed, the swap is a no-op

4. **Integration test**
   - Fixture: a playtest session with a live narrator
   - Assert: a turn produces at least one `narration.delta` message before the
     canonical `narration` message
   - Assert: the UI accumulates the delta text and displays it in the scroll
   - Assert: the final text matches the canonical narration (or log the divergence)

## Acceptance Criteria

1. Server emits `NarrationDelta` messages during Anthropic SDK streaming; each
   delta carries a text chunk (payload.delta) and the turn_id
2. Server does NOT event-log `NarrationDelta` (ephemeral, live delivery only)
3. Server emits OTEL spans for streaming lifecycle (started, per-delta, ended)
4. Client WebSocket handler routes incoming `NarrationDelta` (kind-based dispatch)
5. Client narration accumulator builds `streamingText` from arriving deltas,
   replacing it with the canonical text when the `narration` event lands
6. Client renders the accumulated text in the NarrationScroll in real-time
   (streaming text visible before canonical arrival)
7. **Integration test:** a playtest fixture exercises the streaming path
   end-to-end (server emits deltas → client accumulates → text displays); test
   asserts at least one delta message and matching final text
8. Full test suite passes (unit + integration); no regressions in narration
   buffer or state mirror paths

## Context: Related ADRs and Story References

- **ADR-133** (Client State Reconciliation v2): Documents the full-replay mirror
  and streaming-narration accumulator pattern. `useStateMirror` is idempotent;
  streaming deltas are accumulated separately.
- **ADR-076** (Narration Protocol Collapse): Post-TTS narration has two messages:
  `Narration` (full text + footnotes) and `NarrationEnd` (turn marker). Streaming
  deltas (`NarrationDelta`) are a **new addition** to this protocol (they were
  dormant/TTS-only before).
- **ADR-067** (Unified Narrator Agent): Single narrator agent per action, no
  multi-stage pipeline. The Anthropic SDK streaming happens in this agent.
- **Story 71-5** (MP opening narration): Establishes the POV-swap pattern for
  multiplayer opening; streaming should respect the same per-recipient routing.

## Delivery Findings

(Agents: append findings below this line. Do not edit other agents' entries.)

### TEA (test design)
- **Improvement** (non-blocking): The story is tagged cross-repo (server,ui), but
  the UI half is ALREADY complete and green — `streamingNarration.ts` reducer,
  `useStateMirror` intake (`isNarrationDelta` → `reduceStreamingNarration`), and
  `NarrationScroll` render via `displayTextForTurn`, covered by 41 passing tests
  (Tasks 16/17). No UI changes are in scope. Affects `sidequest-ui` (no change —
  Dev/Reviewer should treat the UI repo as no-op for this story). *Found by TEA
  during test design.*
- **Gap** (non-blocking): `broadcast_delta` is `async def` but its body contains
  NO `await` (only `connected_player_ids()` / `queue.put_nowait()` — all sync).
  The producer seam `on_text_delta: Callable[[str], None]` is SYNC and
  `complete_with_tools` calls it synchronously (anthropic_sdk_client.py:530-531).
  Dev must bridge sync-sink → async-broadcast (await an async sink, schedule a
  task, or make `broadcast_delta` sync) AND ensure deltas are flushed to the room
  queue before `run_narration_turn` returns (the wiring test drains the queue
  post-await). Affects `sidequest/agents/orchestrator.py` +
  `sidequest/agents/anthropic_sdk_client.py` (callback bridging). *Found by TEA
  during test design.*
- **Question** (non-blocking): The streaming SDK call must reconcile token-delta
  streaming with the existing per-iteration cost/ceiling instrumentation
  (`_check_cost_ceiling`, `_maybe_emit_cost_runaway`, `llm_request_span`) — those
  read `response.usage`, which under streaming comes off `get_final_message()`.
  Affects `sidequest/agents/anthropic_sdk_client.py` (`complete_with_tools` loop).
  *Found by TEA during test design.*

### Dev (implementation)
- **Resolved** (TEA's sync→async bridge Gap): the delta sink is `async` and
  `complete_with_tools` now `await`s an awaitable sink, so deltas are enqueued
  to the room before the turn returns (no `create_task` ordering risk). The
  cost/ceiling instrumentation reconciliation (TEA's Question) is satisfied —
  `get_final_message()` returns the same usage/model/stop_reason shape as the
  non-streaming response, so `_maybe_emit_cost_runaway` / `_check_cost_ceiling`
  / `llm_request_span` are unchanged. *Found by Dev during implementation.*
- **Improvement** (non-blocking): `broadcast_delta` fans to ALL sockets in the
  room and is NOT per-recipient filtered (its docstring notes the G10 perception
  deferral). For SOLO (this story) that is exactly the one player — correct. MP
  per-recipient delta redaction (ADR-104/105) remains deferred and is out of
  scope here. Affects `sidequest/server/emitters.py` (future MP work). *Found by
  Dev during implementation.*
- **Gap** (non-blocking, pre-existing — NOT introduced by 71-23): two server
  tests fail on a clean base, confirmed by stash: `test_61_12_output_format_
  compaction::test_output_only_prose_under_byte_budget` (NARRATOR_OUTPUT_ONLY is
  24,784 B vs a 13,800 B budget) and `test_apply_world_patch::test_active_stakes_
  path_applies`. Tracked by backlog story 76-10. Affects
  `sidequest/agents/` content + `tests/agents/tools/test_apply_world_patch.py`.
  *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): SDK streaming fan-out is not gated to solo — raw deltas reach
  all sockets in `>1`-connected MP rooms (firewall+POV breach per handler:1493).
  Affects `sidequest/agents/orchestrator.py` (sink wiring) — gate `on_text_delta` on
  `room` present AND `≤1` connected player. *Found by Reviewer during code review.*
- **Gap** (non-blocking): awaited `on_text_delta` sink has no try/except — a room-API
  exception aborts the whole narrator turn. Affects
  `sidequest/agents/anthropic_sdk_client.py` (wrap sink call, degrade gracefully).
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking, pre-existing): unbounded outbound `asyncio.Queue`
  (`sidequest/server/websocket.py:83`) amplified by per-token enqueues; consider a
  `maxsize` ceiling. Not introduced here. *Found by Reviewer during code review.*

### TEA (rework — round 2)
- **Test added** for Reviewer F1 (HIGH):
  `test_sdk_path_does_not_stream_raw_deltas_in_multiplayer_room` (commit f8f21ac).
  A 2-connected-player room must fan out ZERO raw `NarrationDelta` and report
  `narration.turn.delta_count == 0`; the canonical NARRATION is the MP delivery
  path. RED confirmed — today 4 raw deltas leak (2 chunks × 2 sockets). GREEN =
  gate the sink on solo (`len(room.connected_player_ids()) <= 1`), mirroring
  `websocket_session_handler.py:1493`'s `> 1` check. *Found/added by TEA during
  rework.*
- **Reviewer F2 (MEDIUM, sink try/except)** is NOT separately tested — it is a
  graceful-degradation/robustness hardening best verified by Dev wrapping the
  sink + a targeted unit test if Dev adds one; I did not author a failing test
  for it (hard to provoke deterministically without a misbehaving-room fake, and
  it is non-blocking). Dev should still wrap the awaited sink per the finding.
  *Noted by TEA during rework.*

### Dev (rework — round 2)
- **Reviewer F1 (HIGH) FIXED** (commit a1e66df): added module-level `_room_is_solo(room)`
  in orchestrator.py (duck-typed `connected_player_ids()`, fail-closed → no fan-out
  when count can't be confirmed). The delta sink is now wired ONLY when
  `room is not None and _room_is_solo(room)` (≤1 connected). MP (>1 connected) →
  `on_text_delta=None` → no raw deltas, `delta_count=0`. The TEA MP test passes GREEN.
  *Fixed by Dev during rework.*
- **Reviewer F2 (MEDIUM) FIXED** (commit a1e66df): the `_emit_delta` sink wraps the
  awaited `broadcast_delta` in try/except — logs `sdk_stream.delta_broadcast_failed`
  and continues, so a dead/mid-detach socket cannot abort the narrator turn. `seq`
  advances per attempt (monotonic); `delta_count` counts only successful broadcasts.
  *Fixed by Dev during rework.*
- **Reviewer F3 (LOW, unbounded queue)** — NOT addressed: pre-existing, out of scope
  for 71-23 (tracked separately). *Noted by Dev during rework.*

### Reviewer (re-review — round 2)
- **Improvement** (non-blocking): TOCTOU — `stream_solo` is evaluated once before
  the streaming call; a player joining mid-stream could receive raw deltas. CANNOT
  occur for a real `GameMode.SOLO` game (2nd connect raises `SoloSlotConflict`);
  only reachable for an MP-mode room transiently at 1 player, and benign today
  (narration perception-redactor is a no-op). Fix when MP streaming is built:
  per-chunk re-check `if not _room_is_solo(room): return` in `_emit_delta`. Affects
  `sidequest/agents/orchestrator.py`. *Found by Reviewer during re-review.*
- **Improvement** (non-blocking): `broadcast_delta` re-derives recipients from the
  live room at emit-time; the true MP fix is an explicit `player_ids` allowlist
  (G10). Affects `sidequest/server/emitters.py`. *Found by Reviewer during re-review.*
- **Improvement** (non-blocking): the `_emit_delta` except logs at WARNING but does
  not surface dropped-chunk count to OTEL; add `narration.turn.delta_errors` so the
  GM panel can distinguish "never streamed" from "streamed, some chunks dropped"
  (OTEL completeness; the failure is already logged, so not a silent fallback).
  Affects `sidequest/agents/orchestrator.py`. *Found by Reviewer during re-review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

5 deviations

- **Client streaming tests mock `messages.stream`, not `messages.create(stream=True)`**
  - Rationale: `messages.stream` is the canonical Anthropic async streaming API and
  - Severity: minor
  - Forward impact: Dev may need to adjust the fake SDK surface if a different
- **OTEL signal named `narration.turn.delta_count` (attribute on existing span)**
  - Rationale: The SDK path already opens exactly one `narration.turn` cost-rollup
  - Severity: minor
  - Forward impact: GM-panel/telemetry consumers read `narration.turn.delta_count`;
- **`turn_id` asserted equal to `str(context.turn_number)`**
  - Rationale: Consistency with the only existing producer of NarrationDelta; the
  - Severity: minor
  - Forward impact: GREEN must mint `turn_id = str(turn_number)` on the SDK path.
- **Reshaped `on_text_delta` to accept an async sink (`Callable[[str], Awaitable[None] | None]`)**
  - Rationale: A sync sink cannot await the async `broadcast_delta`; rather than
  - Severity: minor
  - Forward impact: Any other implementer of `ToolingLlmClient` may now supply
- **Streaming triggers only when `on_text_delta` is wired (no hasattr fallback)**
  - Rationale: Preserves AC2 (no-sink path unchanged) and honors No Silent
  - Severity: minor
  - Forward impact: Test fakes that pass `on_text_delta` to the REAL client must

## Design Deviations

(Agents: log spec deviations as they happen — not after the fact. Do not edit other agents' entries.)

### TEA (test design)
- **Client streaming tests mock `messages.stream`, not `messages.create(stream=True)`**
  - Spec source: context-story-71-23.md, Technical Guardrails + Assumptions
  - Spec text: "route the SDK call through `messages.stream` (or `messages.create(stream=True)`)"
  - Implementation: The streaming-shaped fake SDK (`_StreamingFakeSdk`) exposes the
    `messages.stream(...)` async-context-manager surface (async-iterable events +
    `.text_stream` + `get_final_message()`). The `create(stream=True)` alternative
    is not modeled.
  - Rationale: `messages.stream` is the canonical Anthropic async streaming API and
    is named first in the context; the behavioral assertion (incremental deltas) is
    seam-agnostic. If GREEN chooses `create(stream=True)`, the fake's surface needs
    the matching shape — Dev should reconcile and re-log if so.
  - Severity: minor
  - Forward impact: Dev may need to adjust the fake SDK surface if a different
    streaming idiom is chosen; the assertions are unchanged.
- **OTEL signal named `narration.turn.delta_count` (attribute on existing span)**
  - Spec source: CLAUDE.md OTEL Observability Principle; AC context (AC1)
  - Spec text: "Server emits OTEL spans for streaming lifecycle"; "the GM panel is
    the lie detector"
  - Implementation: Rather than add a new span, the wiring test asserts a
    `narration.turn.delta_count` attribute on the already-emitted `narration.turn`
    span — mirroring the established `narration.turn.tool_call_count` /
    `tool_calls_json` attribute convention in the same path.
  - Rationale: The SDK path already opens exactly one `narration.turn` cost-rollup
    span per turn; stamping delta_count there is refactor-stable and is the
    minimal honest GM-panel signal ("did N deltas fan out this turn?"). Avoids a
    redundant lifecycle span. The claude -p path's `narrator.stream.*` spans are
    NOT reused (different, do-not-touch path).
  - Severity: minor
  - Forward impact: GM-panel/telemetry consumers read `narration.turn.delta_count`;
    Dev must use this exact attribute name to satisfy the wiring test.
- **`turn_id` asserted equal to `str(context.turn_number)`**
  - Spec source: context-story-71-23.md, Assumptions
  - Spec text: "`turn_id` is available to stamp on each delta at the
    `broadcast_delta` call site … deltas MUST carry `turn_id`"
  - Implementation: The fan-out test asserts each delta's `turn_id == "3"` for
    `turn_number=3`, matching the claude -p streaming path's minting
    (orchestrator.py:2978, `str(context.turn_number)`).
  - Rationale: Consistency with the only existing producer of NarrationDelta; the
    UI reducer routes by turn_id and the canonical NARRATION carries none, so the
    value must be deterministic and shared. A uuid would break correlation.
  - Severity: minor
  - Forward impact: GREEN must mint `turn_id = str(turn_number)` on the SDK path.

### Dev (implementation)
- **Reshaped `on_text_delta` to accept an async sink (`Callable[[str], Awaitable[None] | None]`)**
  - Spec source: context-story-71-23.md, Assumptions (last paragraph)
  - Spec text: "If the SDK's streaming-with-tools shape differs from
    `on_text_delta`'s simple `(str) -> None` contract … log a Design Deviation
    and notify SM before reshaping the callback."
  - Implementation: Widened the `on_text_delta` parameter type on
    `ToolingLlmClient.complete_with_tools` (tooling_protocol.py), the real
    `AnthropicSdkClient`, and `FakeAnthropicSdkClient` to
    `Callable[[str], Awaitable[None] | None] | None`. The client/fake now `await`
    the sink's result if it is awaitable. This is the bridge TEA flagged: the
    orchestrator sink must `await broadcast_delta` (an async fn), but
    `complete_with_tools` previously called the sink synchronously.
  - Rationale: A sync sink cannot await the async `broadcast_delta`; rather than
    fire-and-forget a task (ordering/flush risk vs. the canonical narration) the
    sink is awaited inline, guaranteeing all deltas are enqueued before the turn
    returns. Sync sinks (e.g. `list.append` in client-unit tests) still work —
    a non-awaitable return is simply not awaited.
  - Severity: minor
  - Forward impact: Any other implementer of `ToolingLlmClient` may now supply
    an async delta sink. No production caller besides the SDK narration path
    passes `on_text_delta`. Backward-compatible for sync sinks.
- **Streaming triggers only when `on_text_delta` is wired (no hasattr fallback)**
  - Spec source: context-story-71-23.md, Scope Boundaries ("In scope: route the
    SDK narrator call through `messages.stream`"); CLAUDE.md No Silent Fallbacks
  - Spec text: "Route the SDK narrator call (`complete_with_tools`) through
    `messages.stream` so `on_text_delta` fires on real token deltas."
  - Implementation: `complete_with_tools` takes the `messages.stream` branch ONLY
    when `on_text_delta is not None`; otherwise it stays on `messages.create`
    (byte-identical to pre-71-23). It does NOT `hasattr(sdk, "stream")`-guard —
    if a sink is wired and the SDK can't stream, it fails loud.
  - Rationale: Preserves AC2 (no-sink path unchanged) and honors No Silent
    Fallbacks — a missing `.stream` surfaces, never silently downgrades.
  - Severity: minor
  - Forward impact: Test fakes that pass `on_text_delta` to the REAL client must
    expose a `.stream` surface (two existing fakes updated accordingly).

### Reviewer (audit)
- TEA — *Client tests mock `messages.stream` not `create(stream=True)`* → ✓ ACCEPTED:
  canonical async streaming surface; behavioral assertion is seam-agnostic; Dev's
  impl used `messages.stream`, so the seam matches.
- TEA — *OTEL signal `narration.turn.delta_count` (attr on existing span)* → ✓ ACCEPTED:
  refactor-stable, matches the `tool_call_count`/`tool_calls_json` convention; minimal
  honest GM-panel signal.
- TEA — *`turn_id == str(context.turn_number)`* → ✓ ACCEPTED: mirrors the only other
  NarrationDelta producer (claude -p path:2978); deterministic correlation key the UI
  reducer needs. (Minor latent: `turn_number==0` → uuid fallback, same as the existing
  path — not a regression.)
- Dev — *Reshaped `on_text_delta` to accept an async sink* → ✓ ACCEPTED: the story
  context pre-authorized reshaping with a logged deviation; awaiting inline (vs
  fire-and-forget task) is the correct choice for flush-before-canonical ordering;
  backward-compatible for sync sinks.
- Dev — *Streaming triggers only when `on_text_delta` wired; no hasattr fallback* →
  ✗ **FLAGGED**: the principle (fail-loud, no silent SDK-capability fallback) is sound
  and ACCEPTED — BUT the entry's framing ("`room=None` skips fan-out … byte-identical")
  obscures that streaming fires for **every non-None room, including `>1`-connected MP
  rooms**, which the story scoped OUT. The solo-only scope was deviated from without
  being logged. See UNDOCUMENTED below + HIGH finding F1.
- **UNDOCUMENTED (Reviewer):** Spec said *"Out of scope: MP streaming … this story is
  solo"* and *"Do NOT touch the MP fan-out perception firewall (ADR-104/105)."* Code
  streams raw deltas via `broadcast_delta` for ANY room with no solo gate, taking the
  exact raw bypass the canonical path (handler:1493) calls a "firewall+POV breach" for
  `>1`-connected rooms. Not logged by TEA/Dev as a scope deviation. **Severity: HIGH**
  — this is the blocking finding; the fix is to enforce the solo scope at the sink.

## Dev Assessment

**Implementation Complete:** Yes
**Tests:** 7/7 new tests GREEN; full server suite **10212 passed**, 343 skipped,
2 failed (both pre-existing/out-of-scope — confirmed via `git stash` against the
clean base; tracked by backlog 76-10).
**Branch:** `feat/71-23-solo-narration-streaming` (sidequest-server) — pushed `c3f1055`.
**UI repo:** no changes — the UI streaming path was already wired + green (per TEA).

**Files Changed (sidequest-server):**
- `sidequest/agents/anthropic_sdk_client.py` — `complete_with_tools` routes through
  `messages.stream` when `on_text_delta` is wired (token-by-token deltas via
  `text_delta` events; completed message via `get_final_message()` so the tool
  loop + cost instrumentation are unchanged). Removed the old post-response
  whole-block `on_text_delta(text)` call. `on_text_delta` widened to accept an
  async sink (awaited if awaitable).
- `sidequest/agents/orchestrator.py` — `run_narration_turn` threads `room` into
  `_run_narration_turn_sdk`; the SDK path builds an async `on_text_delta` sink →
  `broadcast_delta(turn_id=str(turn_number), chunk, seq++)`, gated on `room`
  being present; stamps `narration.turn.delta_count` on the cost span. Updated
  the stale "Task 7 not implemented" comment.
- `sidequest/agents/tooling_protocol.py` — `on_text_delta` type widened to match.
- `tests/agents/fakes/fake_anthropic_sdk_client.py` — fake awaits an awaitable sink.
- `tests/agents/test_anthropic_sdk_client_wiring.py` — fake gained a `.stream`
  surface (combat tool-loop wiring test; its whole-block delta assertion preserved).
- `tests/agents/test_narrator_uses_sdk_client.py` — SDK-path routing spy accepts `room`.

**AC coverage:**
- AC1 (incremental deltas): GREEN — client streams token deltas across iterations;
  orchestrator fans N `NarrationDelta` out to the room, stamped with `turn_id`/seq.
- AC2 (non-streaming unaffected): GREEN — `on_text_delta=None` / `room=None` keep
  the `messages.create` path byte-identical; no deltas; `delta_count=0`.
- AC3 (canonical closes turn / late deltas dropped): already enforced by the UI
  reducer (`reduceStreamingNarration`), covered by existing UI tests.
- Wiring + OTEL: GREEN — room-queue behavioral assertion + `narration.turn.delta_count`
  span attribute (no source-text wiring tests).

**Self-review:** wired end-to-end (run_narration_turn → SDK path → broadcast_delta
→ room queue); follows the claude -p streaming path's turn_id/seq conventions;
No Silent Fallbacks honored (no hasattr-guard); pyright clean except one
pre-existing `send_stream` error in the untouched claude -p path.

**Handoff:** To Reviewer (The Merovingian) — or verify phase if the workflow has one.

## TEA Assessment

**Phase:** finish
**Tests Required:** Yes
**Status:** RED (4 failing — ready for Dev; 3 passing guards)

**Test Files:**
- `sidequest-server/tests/agents/test_sdk_narration_streaming.py` — SDK-narrator
  streaming contract (client + orchestrator layers). SERVER-ONLY.

**Verification of the story before writing tests (The Architect verifies, does not
trust):** I traced every claim in the story context against live code.
- CONFIRMED: `complete_with_tools` runs `messages.create` (non-streaming,
  anthropic_sdk_client.py:357) and fires `on_text_delta(text)` ONCE per iteration
  with whole-block text (:530-531).
- CONFIRMED: the claude -p path (`_run_narration_turn_streaming`) ALREADY wires
  prose deltas → `broadcast_delta` with full `narrator.stream.*` OTEL — this is the
  do-NOT-touch legacy path.
- CONFIRMED the real gap: `run_narration_turn` routes to
  `_run_narration_turn_sdk(action, context)` **without `room`** (orchestrator.py:2898),
  and the SDK path's `complete_with_tools` call (:3997-4010) supplies no
  `on_text_delta` — so `broadcast_delta` is unreachable in solo SDK play.
- CORRECTED the session's scope claim: the UI half is NOT a gap. `useStateMirror`
  already routes `narration.delta` → `reduceStreamingNarration`, and
  `NarrationScroll` renders `displayTextForTurn`. Ran the 5 existing UI streaming
  test files: **41 passed**. No UI work is in scope. (See Delivery Findings.)

**Tests Written:** 7 tests across 2 layers, covering AC1/AC2 + the required wiring
test + the OTEL principle:

| # | Test | AC / Rule | RED reason |
|---|------|-----------|------------|
| 1 | `…streams_token_deltas_not_one_block` | AC1 granularity | got 1 whole-block callback; needs `messages.stream` |
| 2 | `…streaming_preserves_usage_and_model` | AC1 fidelity (guard) | passes now; must hold after GREEN |
| 3 | `…no_sink_unaffected` | AC2 (guard) | passes now; no-sink byte-identical |
| 4 | `…streaming_coexists_with_tool_loop` | AC1 + 26-tool loop | got 1 callback; streaming must span tool iterations |
| 5 | `…fans_out_deltas_to_room` | AC1 fan-out + **WIRING** | got 0 deltas; SDK path unwired to `broadcast_delta` |
| 6 | `…emits_delta_count_on_narration_turn_span` | **OTEL principle** | `narration.turn.delta_count` attr absent |
| 7 | `…no_room_broadcasts_nothing` | AC2 (guard) | passes now; no room → no fan-out |

**Rule Coverage (CLAUDE.md / lang-review):**
| Rule | Test | Status |
|------|------|--------|
| Every Test Suite Needs a Wiring Test | #5 (`run_narration_turn`→`broadcast_delta`→room queue, real `NarrationDelta`) | failing (RED) |
| OTEL Observability Principle (lie-detector) | #6 (`narration.turn.delta_count` span attr) | failing (RED) |
| No Source-Text Wiring Tests | wiring proven by behavior (room-queue drain) + OTEL span, never source grep | satisfied |
| No Silent Fallbacks | #7 + #3 assert no-room/no-sink is explicit no-op, not a swallowed path | passing guards |

**Self-check:** Every test has a meaningful assertion (delta counts, exact
chunk/seq/turn_id values, span attribute values, dispatched tool names). No
vacuous `assert True` / `is_none()`-on-always-None / `let _ =`. The 3 "passing"
tests are deliberate regression guards (fidelity + AC2), not vacuous.

**Handoff:** To Dev (Agent Smith) for GREEN. Implementation lives entirely in
`sidequest-server`: (1) stream `complete_with_tools` via `messages.stream` so
`on_text_delta` fires per token delta while preserving the tool loop + cost
instrumentation; (2) thread `room` into `_run_narration_turn_sdk` and wire an
`on_text_delta` sink → `broadcast_delta` (turn_id=str(turn_number), seq++); (3)
stamp `narration.turn.delta_count`. See Delivery Findings for the sync-sink →
async-broadcast bridge Dev must resolve.

## Sm Assessment

**Routing call (Morpheus, SM):** This is a **wiring story**, not a build. Both
ends already exist — the server defines and emits `NarrationDelta`; the client's
`useStateMirror` + narration accumulator (ADR-133) are built to receive deltas.
The work is connecting `messages.stream` across the WebSocket boundary into the
existing UI delta path, with streaming-lifecycle OTEL on the server side so the
GM panel can confirm deltas are actually firing (not Claude improvising).

**Why this fits TDD/phased:** Cross-repo (server + ui), 5pts, p2. The RED phase
should pin the contract at the seam: (a) server emits at least one delta + a
matching canonical `Narration`, and (b) client accumulates deltas and replaces
with canonical text on landing. The integration test (AC7) is the load-bearing
one — it proves the path end-to-end, satisfying the project's wiring doctrine
("Verify Wiring, Not Just Existence" / "Every Test Suite Needs a Wiring Test").

**Watch-outs for the crew:**
- Per-recipient routing: streaming must respect the same POV/recipient firewall
  as 71-5 (ADR-104/105). A solo soloist's deltas must not leak to other seats.
- No silent fallback: if a delta arrives with no open narration buffer, fail
  loud or define the reconciliation rule explicitly — don't drop silently.
- Branch in each subrepo off its own `develop`; orchestrator stays on `main`.

**Decision:** Hand to TEA (The Architect) for RED. No blockers. Jira skipped —
not configured in this project.

## Subagent Results

Subagent toggles (`workflow.reviewer_subagents`): only `preflight` and `security`
are enabled; the other seven are disabled via settings → pre-filled as Skipped.

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (mechanical) | N/A — confirmed GREEN, 2 pre-existing fails verified on develop |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | findings | 3 (1 high, 1 med, 1 low) | confirmed 2, deferred 1 (pre-existing LOW) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (2 enabled returned; 7 disabled via settings)
**Total findings:** 2 confirmed (1 HIGH blocking, 1 MEDIUM), 1 deferred (LOW, pre-existing)

## Rule Compliance

- **No Silent Fallbacks (CLAUDE.md):** COMPLIANT. The streaming branch is taken
  only when `on_text_delta is not None`; no `hasattr(sdk,"stream")` guard that
  would silently downgrade. `room=None` is an explicit documented branch, not a
  fallback. Evidence: anthropic_sdk_client.py:357 (`if on_text_delta is not None`),
  orchestrator.py:4049 (`_emit_delta if room is not None else None`).
- **OTEL Observability Principle (CLAUDE.md):** COMPLIANT. `narration.turn.delta_count`
  stamped on the existing `narration.turn` span (orchestrator.py:~4053), GM-panel
  signal for streaming engagement. Asserted by test #6.
- **No Source-Text Wiring Tests (sidequest-server CLAUDE.md):** COMPLIANT. Wiring
  proven behaviorally (room-queue drain) + OTEL span attribute, never source grep.
- **Crunch in Genre / Flavor in World; Agency; The Test (SOUL.md):** N/A — this is
  transport/streaming plumbing, no narration-content or player-agency surface.
- **ADR-104/105 Perception Firewall (the load-bearing rule here):** **VIOLATED** for
  `>1`-connected rooms — see HIGH finding F1. The canonical path
  (websocket_session_handler.py:1493-1500) defines the raw, non-projected,
  non-POV-swapped fan-out as "a firewall+POV breach" for MP; the streamed deltas
  take exactly that raw bypass with no solo gate.
- **Ephemeral deltas not event-sourced (messages.py NarrationDelta contract):**
  COMPLIANT — `broadcast_delta` enqueues only, never `emit_event`/EventLog.
- **ADR-047 prompt-injection sanitization:** COMPLIANT — `sanitize_player_text`
  runs in `handlers/player_action.py` before `run_narration_turn`; the streaming
  change alters only the SDK call shape, not prompt assembly. (Confirmed by [SEC].)

## Reviewer Observations

- **[HIGH] ADR-104/105 perception-firewall / POV breach in `>1`-connected (MP) rooms**
  at `sidequest/agents/orchestrator.py:4049` (sink wired whenever `room is not None`)
  → `sidequest/server/emitters.py:994` (`broadcast_delta` fans the *same raw* prose
  to *all* sockets). `run_narration_turn(..., room=self._room)` is called
  unconditionally for every session type (websocket_session_handler.py:898), and the
  SDK backend is the ADR-101 default. The canonical path explicitly treats this raw
  fan-out as **"a firewall+POV breach"** for `len(connected) > 1` and routes through
  projection/POV-swap instead (handler:1493-1500); POV-swap is **active today**. The
  story is scoped **solo-only** ("Out of scope: MP streaming"; "Do NOT touch the MP
  fan-out perception firewall") — but there is **no solo guard**, so the default
  backend now streams raw, non-POV-swapped prose to every player in a shared MP room,
  superseded only afterward by the filtered canonical NARRATION. [SEC, high confidence;
  independently traced by Reviewer.] **Blocks.**
- **[MEDIUM] Sink exception aborts the narrator turn** at
  `sidequest/agents/anthropic_sdk_client.py:~383`. `on_text_delta` is awaited inside
  the `async with messages.stream(...)` loop with no try/except. `broadcast_delta`
  guards `put_nowait` per-socket, but `room.connected_player_ids()` /
  `socket_for_player()` are called bare — a misbehaving/mid-detach room raises,
  propagates out of the stream context, skips `get_final_message()`, and fails the
  whole turn. The non-streaming path has no such failure mode; a dead socket should
  never kill narration. [SEC, medium]. (Note: the claude -p streaming path shares the
  no-try/except shape, but that path is non-default + flag-gated; making it the
  default raises the stakes.)
- **[LOW] Unbounded outbound queue amplified by per-token `put_nowait`** at
  `sidequest/server/websocket.py:83`. Pre-existing (`asyncio.Queue()` no maxsize);
  streaming multiplies enqueue volume per turn. A slow/disconnected client accrues
  deltas without backpressure. [SEC, low] — **deferred** (pre-existing, not introduced
  here; track separately).
- **[VERIFIED] Streaming↔tool-loop coexistence** — `get_final_message()` returns the
  same content/usage/stop_reason/model shape as `messages.create`, so the tool loop,
  cost ceiling (`_check_cost_ceiling`), runaway detector, and `llm_request_span` are
  unchanged. Evidence: anthropic_sdk_client.py:357-396 (branch) feeds the identical
  downstream at :559; test `…streaming_coexists_with_tool_loop` dispatches a tool
  across two streamed iterations. Complies with No-Silent-Fallbacks (no shape drift).
- **[VERIFIED] No double-emit** — the old post-response `on_text_delta(text)` block
  was removed (anthropic_sdk_client.py:559-562); deltas fire only live during the
  stream. Evidence: diff removes lines, test asserts exact chunk list / no
  whole-block delta.
- **[VERIFIED] AC2 non-streaming path byte-identical** — `on_text_delta=None` →
  `messages.create` branch unchanged; `room=None` → no sink, `delta_count=0`, no
  broadcast. Evidence: tests `…no_sink_unaffected`, `…no_room_broadcasts_nothing`
  (both pass); preflight confirms 1706 agents tests green minus 2 pre-existing.
- **[VERIFIED] UI repo is genuinely no-op** — `git log develop..HEAD` in sidequest-ui
  is empty; the streaming reducer/intake/render were pre-wired (41 UI tests green per
  RED phase). No half-wired UI. Complies with "no half-wired features."

### Devil's Advocate

Assume this code ships and breaks. The sharpest break is multiplayer. SideQuest's
whole reason for existing is a narrator good enough to fool a career GM at a *table* —
and tables are multiplayer. The moment two players share a room, this change streams
the raw narrator prose, token by token, to every socket — the exact "raw bypass" the
canonical path at handler:1493 labels a "firewall+POV breach." Picture Jade's table:
the GM narrates a hidden assassin that only the rogue's passive perception caught.
Today the perception *redactor* for narration is a no-op (G10 deferred), so the secret
itself may not leak yet — but the **POV swap is live**. So every non-acting player
watches "You slip the dagger free…" stream across their screen in second person,
addressed to someone else, then snap-replace with the third-person canonical. That is
immersion-breaking at best and, the day G10 ships per-recipient redaction, a silent
secret-info leak at worst — and nothing in this diff will flag that transition, because
the gate the author asked for ("solo only") was never written. A confused player sees
the wrong-POV flicker and assumes a bug. A malicious player watching the stream learns
nothing today, but the firewall hole is now *default-on in production* (no flag),
whereas before it lived only behind the non-default `claude -p` + `SIDEQUEST_NARRATOR_
STREAMING=1`. Second break: robustness. A player rage-quits mid-turn; their socket
detaches. If the room object is mid-mutation when `connected_player_ids()` is called
inside the awaited sink, the exception isn't caught — it unwinds the stream context,
`get_final_message()` never runs, and the *entire* narrator turn dies for *everyone*,
not just the quitter. The non-streaming path shrugged that off. Third: a slow client
(Alex on a weak laptop) never drains its queue; per-token `put_nowait` piles unbounded.
None of these are hypothetical edge cases — they are the primary audience's actual
table. The solo happy-path is correct and well-tested; the failure is that "solo" was
assumed, not enforced.

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] `[SEC]` | SDK streaming fan-out takes the raw, non-POV-swapped/non-projected bypass for `>1`-connected (MP) rooms — the firewall+POV breach the canonical path forbids; story is solo-only with no solo guard | `orchestrator.py:4049` → `emitters.py:994`; reachable via `websocket_session_handler.py:898` | Gate the delta sink on solo: wire `on_text_delta` only when `room` is present AND `≤1` connected player (mirror handler:1493's `len(connected) > 1` check). Honors the story's "solo only" scope and the ADR-105 raw-bypass invariant. |
| [MEDIUM] `[SEC]` | Unhandled exception from the awaited `on_text_delta` sink aborts the entire narrator turn (room API calls unguarded) | `anthropic_sdk_client.py:~383` | Wrap the sink call in try/except that logs and continues, so a dead/mid-detach socket degrades gracefully to non-streaming rather than killing the turn. |

> **Round-2 update:** both findings above are RESOLVED in the rework — see
> "## Reviewer Assessment (re-review — round 2)" below. Final verdict: APPROVED.
> `[SEC]` residuals (TOCTOU race, emit-time recipient derivation, delta_errors OTEL)
> are non-blocking and deferred to G10/MP work.

**Deferred (non-blocking, pre-existing):** [LOW] unbounded outbound queue
(`websocket.py:83`) — amplified by per-token enqueues but not introduced here.

**Data flow traced:** player action → `run_narration_turn(room=self._room)`
(handler:898, all session types) → `_run_narration_turn_sdk` → `_emit_delta`
(fires for any non-None room) → `broadcast_delta` → ALL sockets in room. The
solo-only scope is not enforced anywhere on this path.

**What's right:** the solo happy path is correct, well-tested (7 new tests), lint/
format/pyright-clean, no double-emit, AC2 preserved, tool-loop + cost instrumentation
intact, UI genuinely no-op. The single blocking defect is the missing solo gate.

**Handoff:** Back to TEA (The Architect) — the HIGH finding is testable (an MP room
with `>1` connected players must fan out ZERO raw deltas on the SDK path). Add the
failing test, then Dev gates the sink on solo + wraps the sink for graceful degrade.

## Subagent Results (re-review — round 2)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 8/8 story (MP guard passes), regression 1707/2 pre-existing, lint clean, pyright pre-existing-only |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | findings | 3 (1 med, 2 low) | confirmed prior HIGH closed; 3 residuals deferred as non-blocking delivery findings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (2 enabled returned; 7 disabled via settings)
**Total findings:** 0 confirmed-blocking; prior HIGH F1 + MEDIUM F2 verified RESOLVED;
3 residual non-blocking findings deferred to G10/MP work (see Delivery Findings).

## Reviewer Assessment (re-review — round 2)

**Verdict:** APPROVED

**Prior findings — resolution verified:**
- **F1 (HIGH) RESOLVED:** `_room_is_solo()` (fail-closed) gates the delta sink to
  `≤1` connected; MP (`>1`) → `on_text_delta=None`, zero raw deltas, `delta_count=0`.
  Pinned by `test_sdk_path_does_not_stream_raw_deltas_in_multiplayer_room` (passes).
  Crucially, a genuine `GameMode.SOLO` game rejects a 2nd connect (`SoloSlotConflict`),
  so the story's actual scope is fully firewall-safe.
- **F2 (MEDIUM) RESOLVED:** `_emit_delta` wraps the awaited broadcast in try/except,
  logs `sdk_stream.delta_broadcast_failed` + continues; a dead socket no longer
  aborts the turn. `seq` monotonic per attempt; `delta_count` counts only successes.

**Residual (non-blocking, deferred to G10/MP work) — all from reviewer-security:**
- `[SEC]` TOCTOU mid-turn-join race (orchestrator.py:~4057) — cannot occur in SOLO
  mode (2nd connect → `SoloSlotConflict`); benign today (perception redactor is a
  no-op). [medium confidence, low practical severity]
- `[SEC]` `broadcast_delta` derives recipients from the live room at emit-time
  (emitters.py:~997) — needs an explicit `player_ids` allowlist for G10. [low]
- `[SEC]` `_emit_delta` swallows broadcast failures without a `delta_errors` OTEL
  attribute (orchestrator.py:~4069) — observability completeness; the failure is
  already logged at WARNING with exc_info, so not a silent fallback. [low]

All three are forward-looking, consistent with `broadcast_delta`'s documented
"revisit when G10 ships" caveat. None block: the steady-state firewall is closed and
the solo scope is enforced. The prior blocking `[SEC]` HIGH (raw MP fan-out) is
RESOLVED (verified above).

**Data flow traced:** player action → `run_narration_turn(room=self._room)` →
`_run_narration_turn_sdk` → `stream_solo = room and _room_is_solo(room)` → sink wired
ONLY if solo → `broadcast_delta` (solo room → ≤1 socket). MP → no sink → canonical
projected/POV-swapped NARRATION is the sole MP delivery (unchanged from pre-71-23).

**Pattern observed:** the solo gate mirrors the canonical path's `len(connected) > 1`
firewall check (websocket_session_handler.py) — consistent boundary on both paths.

**Error handling:** sink failures degrade gracefully (logged, turn continues);
`_room_is_solo` fails closed; AC2 (no-sink/no-room) byte-identical and test-guarded.

**Quality gates:** lint clean; pyright clean except the pre-existing `send_stream`
error in the untouched claude -p path; 1707 agents tests pass (2 pre-existing fails,
backlog 76-10); UI repo genuinely no-op.

**Handoff:** To SM (Morpheus) for finish-story.

## Design Deviations — Reviewer re-audit (round 2)

All round-1 deviations remain ✓ ACCEPTED. The round-1 FLAGGED item (Dev's
"streaming triggers only when sink wired" — the obscured MP-scope broadening) is
now **RESOLVED**: the solo gate enforces the solo-only scope the FLAG was about. No
new deviations introduced by the rework (the fix implements the Reviewer finding;
not a spec deviation).

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-04T11:48:34Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-04T00:00:00Z | 2026-06-04T11:01:46Z | 11h 1m |
| red | 2026-06-04T11:01:46Z | 2026-06-04T11:15:46Z | 14m |
| green | 2026-06-04T11:15:46Z | 2026-06-04T11:27:36Z | 11m 50s |
| review | 2026-06-04T11:27:36Z | 2026-06-04T11:36:28Z | 8m 52s |
| red | 2026-06-04T11:36:28Z | 2026-06-04T11:38:41Z | 2m 13s |
| green | 2026-06-04T11:38:41Z | 2026-06-04T11:42:48Z | 4m 7s |
| review | 2026-06-04T11:42:48Z | 2026-06-04T11:48:34Z | 5m 46s |
| finish | 2026-06-04T11:48:34Z | - | - |