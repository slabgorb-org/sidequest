# Solo Sealed Action Turn — Sequence

> **Last updated:** 2026-06-08 (narrator=Anthropic SDK ADR-101; Postgres ADR-115; TurnManager barrier; ADR-113 intent router)
>
> Module paths reference `sidequest-server/sidequest/` (Python). The pre-port
> Rust crate paths in earlier revisions of this document have been retired —
> see `docs/adr/082-port-api-rust-to-python.md` and the translation table in
> `docs/adr/README.md`.

One complete action turn in **solo play**. The submit-and-wait barrier
(`TurnManager.submit_input()`, `sidequest/game/turn.py:90`) is architecturally
present on every turn but collapses to a no-op when only one PLAYING player is in
the session — `submit_input()` fires on the first submission because
`len(submitted) >= player_count` is immediately satisfied. See
[`multiplayer-sealed-turns.md`](./multiplayer-sealed-turns.md) for the full
multiplayer variant. (The "sealed-letter" name is historical — the barrier waits,
but action text is peer-visible during the wait per ADR-036 amendment 2026-05-03;
hidden-submission "sealed visibility" is reserved for PvP and not implemented.)

## Diagram

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontSize':'22px'}, 'sequence': {'actorFontSize':22, 'messageFontSize':20, 'noteFontSize':19, 'wrap':true}}}%%
sequenceDiagram
    autonumber
    actor Player
    participant UI as UI (React)<br/>App.tsx / InputBar
    participant WS as WebSocket
    participant Handler as WebSocketSessionHandler<br/>_execute_narration_turn
    participant Router as Intent Router (Haiku)<br/>intent_router_pass.py
    participant Narr as Narrator<br/>(Anthropic SDK, ADR-101)<br/>orchestrator.run_narration_turn
    participant Apply as State Apply<br/>narration_apply.py / dispatch/
    participant Watcher as OTEL Watcher

    Player->>UI: Types action, presses Enter
    Note over UI: optimistic push of action<br/>into messages; input locked

    UI->>WS: PLAYER_ACTION { action, aside:false }
    WS->>Handler: pydantic parse → dispatch → _execute_narration_turn

    Note over Handler: TurnPhase.InputCollection<br/>turn_manager.submit_input(player_id)<br/>solo: 1 PLAYING player → barrier fires immediately

    Handler-->>WS: TURN_STATUS { status:"active", entries[] }
    WS-->>UI: TURN_STATUS

    Handler-->>WS: THINKING (eager, pre-LLM)
    WS-->>UI: THINKING
    Note over UI: setThinking(true)

    rect rgba(120,160,220,0.15)
    Note over Handler,Router: TurnPhase.IntentRouting (ADR-113)
    Handler->>Router: execute_intent_router_pre_narrator_pass(snapshot, pack, action)
    Note over Router: Haiku-via-SDK → DispatchPackage<br/>run_dispatch_bank fires matching subsystems<br/>(confrontation / magic / scenario_clue / npc_agency / movement)
    Router->>Watcher: intent_router spans (OTEL only — no wire message)
    Router-->>Handler: DispatchPackage (engines already engaged)
    end

    rect rgba(160,200,160,0.15)
    Note over Handler,Narr: TurnPhase.AgentExecution
    Handler->>Narr: orchestrator.run_narration_turn(context)
    Note over Narr: Anthropic SDK narrator (unified, ADR-067)<br/>tool-use structured output (ADR-102)
    Narr-->>Handler: NarrationResult { narration, footnotes,<br/>state_delta, tool calls, intent }
    Narr->>Watcher: agent / prompt spans { tokens, intent }
    end

    opt Narrator called roll_dice() tool (ADR-074)
        Handler-->>WS: DICE_REQUEST { request_id, throw_params, beat_id }
        WS-->>UI: DICE_REQUEST
        Note over UI: Rapier 3D dice overlay rolls,<br/>physics settles faces
        UI->>WS: DICE_THROW { request_id, face[], beat_id }
        WS->>Handler: handlers/dice_throw.py resolves beat + dice
        Handler-->>WS: DICE_RESULT { resolved_total, outcome }
        WS-->>UI: DICE_RESULT
    end

    rect rgba(220,200,150,0.15)
    Note over Handler,Apply: TurnPhase.StatePatch
    Handler->>Apply: _apply_narration_result_to_snapshot(...)
    Note over Apply: location / inventory / trope tick /<br/>per-stage dispatch handlers mutate snapshot
    Handler->>Handler: turn_manager.record_interaction()<br/>(round + interaction both advance — ADR-051)
    end

    rect rgba(200,160,200,0.15)
    Note over Handler,UI: TurnPhase.Broadcast

    Handler-->>WS: NARRATION { text, state_delta, footnotes, seq }
    WS-->>UI: NARRATION (persisted to EventLog)
    Note over UI: setThinking(false); append to messages

    Handler-->>WS: NARRATION_END { state_delta, party_members, turn_number }
    WS-->>UI: NARRATION_END (transient, ADR-027)
    Note over UI: useStateMirror folds state_delta<br/>into GameStateProvider

    Handler-->>WS: PARTY_STATUS { members[], resources }
    WS-->>UI: PARTY_STATUS

    opt Location changed
        Handler-->>UI: CHAPTER_MARKER { location }
    end
    opt New render queued
        Handler-->>UI: IMAGE { url, render_id, tier }
    end
    opt Item depleted
        Handler-->>UI: ITEM_DEPLETED { item_name, remaining_before }
    end

    Note over Handler: delta = compute_delta(before, after)<br/>→ typed state-change messages per changed field
    Handler-->>UI: (typed state-change messages)
    end

    Note over Handler: repository.save(snapshot) / room.save()<br/>→ PgSaveRepository (Postgres, ADR-115)
    Handler->>Watcher: TurnRecord — snapshot before/after, delta, intent, tokens
```

## Code path reference

| Step | File |
|---|---|
| UI `handleSend` | `sidequest-ui/src/App.tsx` |
| WebSocket reader/dispatch | `sidequest-server/sidequest/server/websocket.py` + `websocket_session_handler.py` |
| Narration turn entry | `sidequest-server/sidequest/server/websocket_session_handler.py` (`_execute_narration_turn`) |
| Turn barrier / phases / counters | `sidequest-server/sidequest/game/turn.py` (`TurnManager.submit_input` :90, `TurnPhase` :25, `record_interaction` :126) |
| Intent Router (pre-narrator, ADR-113) | `sidequest-server/sidequest/server/intent_router_pass.py` (`execute_intent_router_pre_narrator_pass`) + `sidequest/agents/intent_router.py` + `sidequest/agents/subsystems/` (`run_dispatch_bank`) |
| Narrator backend selection | `sidequest-server/sidequest/agents/llm_factory.py:198` (default `anthropic_sdk`, ADR-101) |
| Narrator call | `sidequest-server/sidequest/agents/orchestrator.py:2932` (`run_narration_turn`) |
| Dice request → throw → result (ADR-074) | `sidequest-server/sidequest/handlers/dice_throw.py` |
| State apply | `sidequest-server/sidequest/server/narration_apply.py` (`_apply_narration_result_to_snapshot`) + `server/dispatch/` per-stage handlers |
| Delta broadcast | `sidequest-server/sidequest/game/delta.py:153` (`compute_delta`) |
| Persistence (Postgres, ADR-115) | `sidequest-server/sidequest/game/pg/` (`PgSaveRepository`) via `repository.save(snapshot)` / `room.save()` |
| Wire message enums | `sidequest-server/sidequest/protocol/enums.py` |
| Client message handler | `sidequest-ui/src/App.tsx` + `useGameSocket` |
| Client state mirror | `sidequest-ui/src/hooks/useStateMirror.ts` (ADR-026) |

## Solo vs. multiplayer submit-and-wait

The barrier is the same `TurnManager.submit_input()` on every turn. What collapses
in solo is the *wait*, not the code path:

1. **No wait.** With one PLAYING player, `player_count == 1`, so the first
   `submit_input()` immediately satisfies `len(submitted) >= player_count` and
   advances `TurnPhase.InputCollection → IntentRouting` in the same call.
2. **No peer `TURN_STATUS {status:"submitted"}` round.** The submitted-but-waiting
   acknowledgement only matters when there are other awaiters.
3. **No peer reveal.** Cross-player visibility of action text (ADR-036) is moot
   with a single seat.

So in solo, a turn is:

```
PLAYER_ACTION → TURN_STATUS(active) → THINKING
              → [intent router pass, OTEL only]
              → narrator → [opt DICE_REQUEST/THROW/RESULT]
              → NARRATION → NARRATION_END → PARTY_STATUS
              → (+ CHAPTER_MARKER / IMAGE / ITEM_DEPLETED)
              → typed state-change messages → save (Postgres)
```

The seal / wait / reveal ceremony only exists to keep multiplayer players in sync
and to preserve simultaneous-resolution fairness.

## Message fan-out paths

Two different fan-out paths feed connected clients:

- **Per-connection / acting-player send** — targeted at the player whose turn is
  resolving. Used for `NARRATION`, `NARRATION_END`, and responses tied to the
  acting player. See `server/websocket_session_handler.py`.
- **Session broadcast** (`SessionRoom.broadcast(...)`) — scoped to players in the
  same genre:world session, with optional per-player targeting via the
  projection/perception filter (ADR-104/-105). Used for multiplayer session events
  and typed state-change broadcasts. The `DICE_REQUEST` / `DICE_RESULT` pair is
  broadcast to the room so every socket (the rolling player included) sees the
  same dice stream — see `handlers/dice_throw.py`.
- **Global watcher fan-out** (`/ws/watcher` via `server/watcher.py` +
  `telemetry/watcher_hub.py`) — separate from gameplay traffic; streams OTEL
  telemetry to GM Mode. The intent-router pass and `TurnRecord` emit here only,
  with no corresponding wire message on the gameplay channel.
```