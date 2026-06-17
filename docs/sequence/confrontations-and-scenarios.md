# Confrontations and Scenarios

> ⚠️ **STALE — historical reference only.** This document describes the **native
> Rust beat/metric confrontation engine**, which has been **removed**. Every pack
> now binds a published ruleset (Without Number or Fate); combat resolves through
> `run_wn_round` / `run_fate_exchange`, not the dial/beat dispatch shown below
> (SOUL: *Bind the Ruleset, Don't Balance It*; ADR-143/-144). For the current turn
> resolution see **[`ruleset-turns.md`](./ruleset-turns.md)**. The **Scenario
> System** section (clue graph, belief state, gossip) below is still
> forward-looking design; the beat-dispatch and file-reference sections are
> superseded.

> Genre-defined encounter engine with beat-based resolution and metric tracking.
> ConfrontationDefs in genre packs define available beats; StructuredEncounter tracks runtime state.

## Confrontation Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Setup : narrator emits confrontation type
    Setup --> Opening : beat 1
    Opening --> Escalation : beats 2-4
    Escalation --> Climax : beat 5+
    Climax --> Resolution : threshold crossed OR resolution beat
    Resolution --> [*] : encounter cleared

    Resolution --> Setup : escalates_to defined\n(e.g. standoff → combat)
```

## Beat Selection Sequence (BeatSelection mode)

```mermaid
sequenceDiagram
    participant P as Player (UI)
    participant S as Server (lib.rs)
    participant BD as Beat Dispatch (beat.rs)
    participant E as StructuredEncounter
    participant CD as ConfrontationDef
    participant N as Narrator (Claude)
    participant O as Orchestrator

    Note over P,O: Phase 1 — Encounter Initiation

    N-->>O: game_patch { confrontation: "standoff" }
    O->>CD: find_confrontation_def("standoff")
    CD-->>O: ConfrontationDef { beats, metric, secondary_stats }
    O->>E: StructuredEncounter::from_confrontation_def(&def)
    Note over E: metric.current = starting<br/>phase = Setup, beat = 0

    Note over P,O: Phase 2 — Player Beat Selection

    P->>S: BeatSelection { beat_id: "intimidate", actor: "player" }
    S->>CD: validate beat_id exists in def.beats
    S->>E: apply_beat("intimidate", &def)
    Note over E: metric += beat.metric_delta<br/>beat += 1, phase updated
    S->>S: OTEL: encounter.player_beat_received
    S->>S: Convert to synthetic PlayerAction:<br/>"[BEAT_RESOLVED] Intimidate (PRESENCE): tension 5 → 8"

    Note over P,O: Phase 3 — Narrator Resolves Turn

    S->>N: claude -p (narrator with beat outcome in context)
    N-->>O: ActionResult { narration, beat_selections: [NPC beats] }

    Note over P,O: Phase 4 — NPC Beat Dispatch

    loop For each NPC beat_selection
        O->>BD: dispatch_beat_selection(ctx, npc_beat_id)
        BD->>CD: validate beat_id
        BD->>E: apply_beat(npc_beat_id, &def)
        BD->>BD: OTEL: encounter.beat_dispatched
    end

    Note over P,O: Phase 5 — Resolution Check

    alt Metric crossed threshold OR resolution beat
        E->>E: resolved = true, phase = Resolution
        alt escalates_to defined
            E->>E: escalate_to_combat()
            Note over E: New encounter begins
        else No escalation
            Note over E: Encounter complete
        end
    else Below threshold
        Note over E: Continue to next turn
    end

    S-->>P: NARRATION + NARRATION_END
    S-->>P: Confrontation payload (updated beats, metric)
```

## Beat Application Mechanics

```mermaid
flowchart TD
    BEAT[apply_beat called] --> LOOKUP[Find beat in ConfrontationDef]
    LOOKUP --> APPLY[metric.current += beat.metric_delta]
    APPLY --> CLAMP{direction == Ascending<br/>AND current < 0?}
    CLAMP -->|Yes| ZERO[Clamp to 0]
    CLAMP -->|No| INC[beat counter += 1]
    ZERO --> INC

    INC --> RESOLVE{Resolution check}
    RESOLVE -->|beat.resolution == true| DONE[resolved = true<br/>phase = Resolution]
    RESOLVE -->|threshold crossed| DONE
    RESOLVE -->|Neither| PHASE[Update phase by beat#]

    PHASE --> B0{beat 0}
    PHASE --> B1{beat 1}
    PHASE --> B24{beats 2-4}
    PHASE --> B5{beat 5+}
    B0 --> SETUP[Setup]
    B1 --> OPEN[Opening]
    B24 --> ESC[Escalation]
    B5 --> CLIMAX[Climax]

    subgraph Threshold Check
        direction LR
        ASC[Ascending: current ≥ threshold_high]
        DESC[Descending: current ≤ threshold_low]
        BIDI[Bidirectional: either threshold]
    end
```

## Resolution Modes (ADR-077)

```mermaid
flowchart LR
    subgraph BeatSelection["BeatSelection (default)"]
        BS1[Narrator picks beats each turn]
        BS2[Sequential resolution]
    end

    subgraph SealedLetterLookup["SealedLetterLookup (ADR-077)"]
        SL1[All actors commit privately]
        SL2[per_actor_state tracks choices]
        SL3[Interaction table resolves cross-product]
    end
```

**BeatSelection** is the standard mode — narrator emits beat choices and they're applied sequentially.

**SealedLetterLookup** is for simultaneous-commit encounters (dogfights, card games, duels) where secrecy matters. Each `EncounterActor` has `per_actor_state: HashMap<String, Value>` for tracking committed choices.

## ConfrontationDef Structure (genre pack rules.yaml)

```
ConfrontationDef
├── confrontation_type: "standoff"
├── label: "Tense Standoff"
├── category: "social" | "combat" | "pre_combat" | "movement"
├── resolution_mode: BeatSelection | SealedLetterLookup
├── metric: MetricDef
│   ├── name: "tension"
│   ├── direction: "ascending"
│   ├── starting: 0
│   ├── threshold_high: 10
│   └── threshold_low: null
├── beats: Vec<BeatDef>
│   ├── id: "intimidate"
│   ├── label: "Intimidate"
│   ├── metric_delta: +3
│   ├── stat_check: "PRESENCE"
│   ├── risk: "They might call your bluff"
│   ├── reveals: "Their true allegiance"
│   ├── resolution: false
│   ├── effect: "Target visibly shaken"
│   ├── narrator_hint: "Describe the power dynamic shifting"
│   └── gold_delta: null
├── secondary_stats: Vec<SecondaryStatDef>
├── escalates_to: "combat"
└── mood: "tension"
```

## Scenario System (Epic 7 — partial)

Scenarios are fully modeled in `sidequest-genre` but not yet wired into the orchestrator/dispatch loop.

```mermaid
flowchart TD
    SP[ScenarioPack] --> ROLES[PlayerRole assignments]
    SP --> CLUE[ClueGraph<br/>dependency tracking]
    SP --> PACE[Pacing<br/>act structure + pressure events]
    SP --> NPC[ScenarioNpc<br/>behavior branches by guilt state]
    SP --> ATM[AtmosphereMatrix<br/>weather variants]

    subgraph ClueGraph
        C1[ClueNode: physical evidence] --> C2[ClueNode: testimony]
        C2 --> C3[ClueNode: behavioral tell]
        C1 -.->|red_herring| RH[Red Herring]
        C3 -->|implicates| SUSPECT[Suspect ID]
    end

    subgraph NPC Behavior
        GUILTY[when_guilty<br/>truth, cover_story, evidence]
        INNOCENT[when_innocent<br/>actual_activity, suspicions]
    end
```

**Not yet wired:** Clue discovery routing, accusation handling, NPC guilt branching, scenario event broadcasting.

## Key Files

| File | Purpose | LOC |
|------|---------|-----|
| `sidequest-genre/src/models/rules.rs` | ConfrontationDef, BeatDef, MetricDef, ResolutionMode | — |
| `sidequest-genre/src/models/scenario.rs` | ScenarioPack, ClueGraph, PlayerRole | — |
| `sidequest-game/src/encounter.rs` | StructuredEncounter, apply_beat(), EncounterPhase | 617 |
| `sidequest-server/src/dispatch/beat.rs` | dispatch_beat_selection() | 194 |
| `sidequest-server/src/dispatch/state_mutations.rs` | Post-resolution state changes | 436 |
| `sidequest-server/src/lib.rs` | BeatSelection message dispatch, validation | — |
| `sidequest-agents/src/orchestrator.rs` | BeatSelection in ActionResult, narrator context | 1,445 |

## OTEL Events

| Event | When |
|-------|------|
| `encounter.player_beat_received` | Player selects a beat (beat_id, metric before/after) |
| `encounter.beat_applied` | Beat applied to encounter (metric delta, phase) |
| `encounter.beat_dispatched` | NPC beat dispatched (stat_check, resolver) |
| `encounter.stat_check_resolved` | Stat check completed |
| `encounter.resolved` | Encounter resolved (beats_total, outcome) |
| `encounter.phase_transition` | Phase changed (old_phase, new_phase) |
| `encounter.escalation_started` | Encounter escalated (from_type, to_type) |
| `encounter.gold_delta` | Gold changed on resolution beat |
