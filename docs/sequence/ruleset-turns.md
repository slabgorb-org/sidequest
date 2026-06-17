# Ruleset Turn Sequences — Without Number & Fate

> **Last updated:** 2026-06-17 (ADR-117 RulesetModule seam; ADR-143 WN owns the
> round; ADR-144 Fate Core binding; ADR-113 intent router; ADR-074 determinative
> dice; Story 126-7 the Fate player-throw target).
>
> Module paths reference `sidequest-server/sidequest/` (Python).

Every genre pack now binds **one** published ruleset — a **Without Number**
module (`wwn` / `cwn` / `swn` / `awn`) or **Fate Core** (`fate`). **There is no
native turn flow.** The old dial/beat/metric engine is *removed* from a bound
ruleset's path, not layered under it and tuned to fit — binding the ruleset *is*
the balance decision (SOUL: *Bind the Ruleset, Don't Balance It*; ADR-143, ruled
2026-06-14).

Two things are **identical** across both families, so read this once:

1. **The intent router runs in front of both** (ADR-113). Every turn opens with
   the same submit-and-wait barrier (ADR-036), then
   `execute_intent_router_pre_narrator_pass` (a Haiku pass) decomposes the action
   into a `DispatchPackage` and `run_dispatch_bank` fires the matching subsystems
   (confrontation, magic, movement, npc_agency, scenario_clue) **engine-first**,
   mutating the snapshot *before* the narrator prompt is built. Only then does
   `run_narration_turn` (Anthropic SDK, unified narrator) run.

2. **Dice are determinative** (ADR-074): **the player throws the die and the
   settled physics faces ARE the roll.** The server resolves the action from the
   reported faces; **server-side RNG rolls only for NPCs/opponents**, which have
   no client to throw. The WN family already works this way; Story **126-7**
   brings Fate into line (see the callout under the Fate diagram).

What **diverges** is mechanical resolution — the ruleset module behind the
ADR-117 seam (`isinstance` gate; no fallback between modules):

| | Without Number | Fate Core |
|---|---|---|
| Player roll | `2d6` + attribute mod + skill vs target number | `4dF` + skill vs difficulty / opposed Defend |
| Action surface | WN action / beat tile → `roll_dice` (ADR-074) | Fate action tile → `FATE_ACTION` |
| Narrator tools (ruleset-gated) | `wn_attack`, `wn_skill_check`, `wn_save`, `roll_dice` | `propose_fate_compel` (+ `FATE_STATE` surface) |
| Sealed-commit ledger | `encounter.wn_commits` (one Main Action/round) | `encounter.fate_commits` (one proactive action/exchange) |
| Resolution order | `1d8 + DEX` initiative (`run_wn_round`) | Notice (physical) / Empathy (mental) (`run_fate_exchange`) |
| Lethality substrate | ablative HP / system_strain / Shock / Trauma | stress tracks + consequences → *taken out* |
| Reactive defense | opponent attacks at its own initiative slot | target rolls Defend (Athletics/Will) — **no** full-defense stance |
| Player-facing state msg | `PARTY_STATUS`, `CONFRONTATION` | `FATE_STATE` (reactive, change-gated, fate-pack-only) |

A **mechanical turn is a two-leg cycle**, the same shape in both families:

- **Leg 1 — Offer.** The natural-language action runs the shared front; the
  narrator sets the scene and *offers* a mechanical action (a WN action tile / a
  Fate action tile).
- **Leg 2 — Resolve.** The player selects the action and **throws the
  determinative die**; the throw resolves in its own handler
  (`dispatch_dice_throw` / `FateActionHandler`), **seals** onto the commit
  ledger, and when the barrier closes walks the ordered exchange. The resolving
  handler then **re-enters `_execute_narration_turn`** so the narrator describes
  the outcome from the mechanical truth (`narrator_hints`), never improvised.

A quiet, non-mechanical turn (a walk through town, a conversation) collapses to
Leg 1 only — front + narration, no dice (*Cost Scales with Drama*).

---

## Without Number turn

`wwn` / `cwn` / `swn` / `awn` — `WithoutNumberRulesetModule` + `wn_round.py`.

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontSize':'22px'}, 'sequence': {'actorFontSize':22, 'messageFontSize':20, 'noteFontSize':19, 'wrap':true}}}%%
sequenceDiagram
    autonumber
    actor Player
    participant UI as UI (React)<br/>App.tsx / InlineDiceTray
    participant WS as WebSocket
    participant H as Handler<br/>_execute_narration_turn
    participant R as Intent Router (Haiku)<br/>+ dispatch bank
    participant N as Narrator (SDK)<br/>run_narration_turn
    participant WN as WN Module<br/>wn_round.py
    participant W as OTEL Watcher

    Note over Player,W: LEG 1 — natural-language action & offer

    Player->>UI: types action, Enter
    UI->>WS: PLAYER_ACTION { action }
    WS->>H: parse → _execute_narration_turn
    Note over H: InputCollection — submit_input()<br/>barrier (solo fires now; MP waits for all PLAYING seats)
    H-->>UI: TURN_STATUS { active }
    H-->>UI: THINKING

    rect rgba(120,160,220,0.15)
    Note over H,R: IntentRouting (ADR-113) — engine-first
    H->>R: execute_intent_router_pre_narrator_pass(snapshot, pack, action)
    Note over R: Haiku → DispatchPackage<br/>run_dispatch_bank fires confrontation / magic /<br/>movement / npc_agency — mutates snapshot
    R->>W: intent_router + dispatch spans (OTEL only)
    R-->>H: DispatchPackage (engines engaged)
    end

    rect rgba(160,200,160,0.15)
    Note over H,N: AgentExecution
    H->>N: run_narration_turn(context)
    Note over N: WN-gated tools: wn_attack /<br/>wn_skill_check / wn_save / roll_dice
    N-->>H: NarrationResult { narration, hints, offered WN action }
    N->>W: agent / prompt spans
    end

    H-->>UI: NARRATION (scene + offered WN action: attack / skill / save)
    H-->>UI: NARRATION_END { state_delta } · PARTY_STATUS

    Note over Player,W: LEG 2 — player throws the determinative die

    Note over Player,UI: player picks a WN action tile and throws
    H-->>UI: DICE_REQUEST { request_id, throw_params (2d6), target_number }
    Note over UI: Rapier 3D dice roll — physics settles faces
    UI->>WS: DICE_THROW { request_id, face[], beat_id }
    WS->>H: handlers/dice_throw.py → dispatch_dice_throw
    Note over H,WN: resolve FROM reported faces:<br/>2d6 + attr mod + skill vs target (ruleset.attack_params /<br/>check_params). Player faces ARE the roll — server rolls nothing here.

    alt skill check / save (single roll)
        Note over H,WN: outcome tier applied; no sealed round
    else combat beat (sealed round)
        Note over WN: seal_wn_commit — one Main Action / round
        alt barrier still open (MP)
            H-->>UI: TURN_STATUS { submitted } (waiting on other PCs)
        else barrier closed
            WN->>WN: run_wn_round — walk 1d8 + DEX initiative
            loop each initiative slot
                Note over WN: 0-HP / withdrawn → skip (§6)
                Note over WN: opponent slot → server rolls attack vs PC AC<br/>+ server-rolled damage → PC HP (NPC = server roll)
                Note over WN: PC slot → apply beat: damage (secondary dice,<br/>server-rolled) → HP / system_strain / Shock / Trauma
                Note over WN: dead premise → narrator hint, NO mechanical resolve,<br/>NO auto-retarget (SOUL: The Test)
            end
            WN->>W: wn.round.committed / initiative / resolved spans
        end
        H-->>WS: DICE_RESULT(s) + incapacitation surfaces
        WS-->>UI: broadcast to room (every seat sees the dice stream)
    end

    Note over H: dispatch_dice_throw RETURNS via<br/>session._execute_narration_turn(...) — re-enter to narrate
    H->>N: run_narration_turn("[BEAT_RESOLVED] …", + hints / HP truth)
    N-->>H: NarrationResult
    H-->>UI: NARRATION (honest mechanical outcome)
    H-->>UI: NARRATION_END { state_delta } · PARTY_STATUS
    opt encounter resolved
        H-->>UI: CONFRONTATION { active: false }
    end
    Note over H: repository.save (Postgres) · TurnRecord → Watcher
```

---

## Fate Core turn

`fate` — `FateRulesetModule` + `fate_conflict.py`. Bound for the
detective/social genres (`pulp_noir`, `tea_and_murder`, `wry_whimsy`,
`spaghetti_western`).

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontSize':'22px'}, 'sequence': {'actorFontSize':22, 'messageFontSize':20, 'noteFontSize':19, 'wrap':true}}}%%
sequenceDiagram
    autonumber
    actor Player
    participant UI as UI (React)<br/>FateConflictSurface / FateDiceTray
    participant WS as WebSocket
    participant H as Handler<br/>_execute_narration_turn
    participant R as Intent Router (Haiku)<br/>+ dispatch bank
    participant N as Narrator (SDK)<br/>run_narration_turn
    participant FA as FateActionHandler<br/>dispatch_fate_action
    participant FE as Fate Engine<br/>fate_conflict.py
    participant W as OTEL Watcher

    Note over Player,W: LEG 1 — natural-language action & offer (shared front)

    Player->>UI: types action, Enter
    UI->>WS: PLAYER_ACTION { action }
    WS->>H: parse → _execute_narration_turn
    Note over H: InputCollection — submit_input()<br/>barrier (solo fires now; MP waits for all PLAYING seats)
    H-->>UI: TURN_STATUS { active }
    H-->>UI: THINKING

    rect rgba(120,160,220,0.15)
    Note over H,R: IntentRouting (ADR-113) — engine-first
    H->>R: execute_intent_router_pre_narrator_pass(snapshot, pack, action)
    Note over R: Haiku → DispatchPackage<br/>run_dispatch_bank fires confrontation / scenario_clue /<br/>npc_agency — mutates snapshot
    R->>W: intent_router + dispatch spans (OTEL only)
    R-->>H: DispatchPackage (engines engaged)
    end

    rect rgba(160,200,160,0.15)
    Note over H,N: AgentExecution
    H->>N: run_narration_turn(context)
    Note over N: Fate-gated tool: propose_fate_compel<br/>(four actions surfaced via the tile UI)
    N-->>H: NarrationResult { narration, hints }
    N->>W: agent / prompt spans
    end

    H-->>UI: NARRATION (scene + offered Fate actions)
    Note over H: _maybe_emit_fate_state — reactive, change-gated,<br/>fate-pack-only (aspects, fate points, stress/consequences,<br/>conflict, pending compel)
    H-->>UI: FATE_STATE { characters, scene_aspects, conflict }

    Note over Player,W: LEG 2 — player throws the determinative 4dF

    Note over Player,UI: player picks a tile — Overcome / Create an Advantage /<br/>Attack (Defend is reactive — no full-defense stance), skill,<br/>target, optional invoke
    UI->>WS: FATE_ACTION { action, skill, target, difficulty, invoke_aspect, invoke_mode }
    WS->>FA: FateActionHandler.handle (auth identity = seat)
    Note over FA,FE: dispatch_fate_action — isinstance(FateRulesetModule)

    rect rgba(220,180,120,0.18)
    Note over UI,FE: 126-7 TARGET — player throw is determinative<br/>(see callout). Today the server rolls 4dF itself; that path is torn out.
    FA-->>UI: request 4dF throw { throw_params (4× dF), seed }
    Note over UI: FateDiceTray throws 4 Fudge dice — physics settles faces
    UI->>WS: report settled faces + throw_params + seed (DiceThrowPayload analog)
    WS->>FA: resolve FROM reported faces
    end

    Note over FA,FE: ladder_total = Σ(4dF) + skill (+invoke +2 / reroll)<br/>seal_fate_commit — one proactive action / exchange
    FA-->>WS: FATE_ROLL { dice, ladder_total, shifts, tier }
    WS-->>UI: broadcast to room (the band sees the soloist's roll)

    alt barrier still open (MP)
        Note over FE: commitment_pending — waiting on other PCs
    else barrier closed
        FE->>FE: run_fate_exchange
        Note over FE: seat opponent commits — decide_opponent_action<br/>(NPC 4dF = server roll)
        FE->>FE: walk Notice (physical) / Empathy (mental) order
        loop each committed actor
            Note over FE: attack → target rolls reactive Defend (4dF + Athletics/Will);<br/>shifts = ladder − defense; ≤0 miss / tie→boost;<br/>>0 absorb into stress + consequences → TAKEN OUT when exhausted
            Note over FE: create_advantage → situation aspect (+free invokes;<br/>2 on succeed-with-style)
            Note over FE: overcome → success / tie-at-a-cost / fail
        end
        FE->>W: fate.exchange.committed / order / resolved · aspect.created · taken_out spans
    end

    opt compel (ADR-144 F3e — pre-roll, non-committing)
        N-->>UI: propose_fate_compel → PendingCompel rides FATE_STATE
        Player->>WS: FATE_ACTION { compel_accept | compel_refuse }
        WS->>FE: resolve_compel → fate point +1 accept / −1 refuse
    end

    Note over H: re-enter _execute_narration_turn — narrate the outcome
    H->>N: run_narration_turn(+ narrator_hints / mechanical truth)
    N-->>H: NarrationResult
    H-->>UI: NARRATION (honest mechanical outcome)
    H-->>UI: NARRATION_END · FATE_STATE (updated)
    Note over H: repository.save (Postgres) · TurnRecord → Watcher
```

> ### ⚠️ Fate dice — current vs. target (Story 126-7, p1, backlog)
>
> The shaded leg above is the **target** model. **Today** the Fate path is
> backwards: the server rolls `4dF` itself inside `resolve_action → roll_4df(rng)`
> and decides the outcome, and the 3D `FateDiceTray` is a **post-hoc
> decoration** — it tumbles to physics-determined faces *unrelated* to the
> already-decided result, and can contradict the text readout. That breaks the
> legibility mandate ("the dice should show what was actually rolled").
>
> **126-7 fixes it by construction**, mirroring the d20 / WN path:
> `FATE_ACTION` → server requests a Fate throw → the client throws the four dF
> dice → the client reports the **settled faces + throw_params + seed** (a Fate
> analog of `DiceThrowPayload`) → the server resolves from the reported faces and
> broadcasts. **NPC rolls stay server-side** and broadcast `FATE_ROLL` with
> synthesized `throw_params + seed` for spectator replay (the existing 125-4
> path). The 125-4 groundwork — `FateRollPayload.throw_params` / `seed` and the
> dF `0`-face label — **stays**; what gets torn out is the "server decides, then
> animate" assumption and the server-rolls-for-players path.
>
> **Open design point** (for the 126-7 ADR-144/ADR-074 reconciliation note):
> whether the player Fate throw **reuses** the `DICE_REQUEST` / `DICE_THROW` pair
> with a dF pool (exactly like d20) or introduces a `FATE_THROW` analog. The
> diagram above is drawn at the request→throw→report level so it holds either
> way.

---

## Code path reference

| Step | File |
|---|---|
| Narration turn entry / re-entry | `sidequest/server/websocket_session_handler.py` (`_execute_narration_turn`) |
| Submit-and-wait barrier / phases | `sidequest/game/turn.py` (`TurnManager.submit_input`, `record_interaction`) |
| Intent router (pre-narrator, ADR-113) | `sidequest/server/intent_router_pass.py` (`execute_intent_router_pre_narrator_pass`) + `sidequest/agents/intent_router.py` + `sidequest/agents/subsystems/` (`run_dispatch_bank`) |
| Narrator call | `sidequest/agents/orchestrator.py` (`run_narration_turn`) |
| Ruleset seam (ADR-117) | `sidequest/game/ruleset/base.py` (`RulesetModule`), `registry.py` (`get_ruleset_module`) |
| WN module | `sidequest/game/ruleset/without_number.py` + `wwn.py` / `cwn.py` / `swn.py` / `awn.py` |
| WN narrator tools | `sidequest/agents/tools/wn_tools.py` (`wn_attack`, `wn_skill_check`, `wn_save`) |
| Dice resolve (ADR-074) | `sidequest/handlers/dice_throw.py` → `sidequest/server/dispatch/dice.py` (`dispatch_dice_throw`) |
| WN sealed round | `sidequest/server/dispatch/wn_round.py` (`seal_wn_commit`, `wn_barrier_closed`, `run_wn_round`) |
| Fate module | `sidequest/game/ruleset/fate.py`, `fate_resolution.py` (`resolve_action`, `roll_4df`) |
| Fate action channel | `sidequest/handlers/fate_action.py` (`FateActionHandler`) → `sidequest/server/dispatch/fate_conflict.py` (`dispatch_fate_action`, `run_fate_exchange`, `seal_fate_commit`, `resolve_compel`, `concede_in_conflict`) |
| Fate narrator tool | `sidequest/agents/tools/fate_tools.py` (`propose_fate_compel`) |
| FATE_STATE / FATE_ROLL projection | `sidequest/game/ruleset/fate_projection.py` (`build_fate_state_payload`, `build_fate_roll_payload`) + `sidequest/server/websocket_handlers/fate_state_emit.py` (`_maybe_emit_fate_state`) |
| Fate sheet / opponent AI | `sidequest/game/fate_sheet.py`, `sidequest/game/fate_opponent.py` (`decide_opponent_action`) |
| Wire message enums | `sidequest/protocol/enums.py`, `sidequest/protocol/fate.py` |
| Persistence (Postgres, ADR-115) | `sidequest/game/pg/` (`PgSaveRepository`) |

## OTEL spans (the GM-panel lie detector)

| Family | Spans |
|---|---|
| Shared | `intent_router.decompose`, `dispatch_engagement.{subsystem}.mismatch`, `agent` / `prompt`, `state_patch_hp`, `TurnRecord` |
| Without Number | `wn.round.committed`, `wn.round.initiative`, `wn.round.resolved`, `{slug}.dead_premise`, `cwn.hacking.security_check` (CWN), Trauma / Shock spans |
| Fate | `fate.action_resolved`, `fate.exchange.committed` / `order` / `resolved`, `fate.aspect.created`, `fate.stress.applied`, `fate.consequence.taken`, `fate.taken_out`, `fate.compel.offered`, `fate.aspect.invoked`, `fate.conceded`, `fate.action.flavor_rider`, `fate.projection.emitted`, `fate_roll.broadcast_emitted` |

## See also

- [`solo-turn.md`](./solo-turn.md) — the shared front in solo detail (barrier
  collapse, fan-out paths).
- [`multiplayer-sealed-turns.md`](./multiplayer-sealed-turns.md) — the MP barrier
  both families ride.
- [`confrontations-and-scenarios.md`](./confrontations-and-scenarios.md) —
  **stale**: still documents the removed native Rust beat/metric engine; this doc
  supersedes its turn-resolution content.
