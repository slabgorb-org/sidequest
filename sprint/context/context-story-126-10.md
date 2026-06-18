# Story 126-10: [PERF/FATE] intent_router_pass 37-81s spikes on Fate worlds

## Story Details
- **Story ID:** 126-10
- **Epic:** 126 (Fate Core playtest follow-ups — annees_folles eval)
- **Type:** bug
- **Points:** 3
- **Priority:** p2
- **Workflow:** tdd

## Description

Secondary finding from the 126-9 latency dig (bisect, MEDIUM confidence). SEPARATE mechanism from 126-9's narrator extended-thinking regression — this one is prompt bloat, not thinking.

### Symptom
intent_router_pass phase spikes to 37-81s on a SINGLE call (phase_call_counts=1, so NOT thrash) on Fate worlds — observed on pulp_noir/annees_folles (one session avg 162s/turn). Non-Fate worlds show ~4-6s baseline for the same phase.

### Mechanism
- `intent_router_pass.py:364-365` injects `build_fate_projection` (the shared narrator/router projector at ~line 234: PC skills + ALL live aspects) into the router state_summary ONLY when `pack.rules.ruleset=='fate'`
- This enlarges the router prompt
- The router's single Haiku call is structured (output_format set, llm_factory.py:399-405) so #919 already disabled ITS thinking — thinking-off (126-9) will NOT fix this
- On the bloated Fate prompt the structured call intermittently can't land the finalize inside the mandatory max_turns=2 floor → error_max_turns fragility, surfacing as a slow single call

### Why Separate from 126-9
- 126-9 fixes the narrator (agent_duration_ms, the dominant cost, HIGH confidence, thinking-off)
- This story is the router-phase Fate prompt bloat (MEDIUM confidence, needs the trim)
- Do 126-9 first; re-measure; this may shrink once general load drops, but the Fate prompt is the structural lever

### Lever
Trim `build_fate_projection` for the ROUTER prompt (the router likely needs far less than the narrator — PC skills maybe, not every live aspect). Confirm empirically on annees_folles turn_telemetry before/after.

## Acceptance Criteria

1. **Quantify the Fate router-prompt bloat:** measure intent_router_pass + state_summary size on annees_folles turns vs a non-Fate world (turn_telemetry / GM-panel intent_router.decompose spans)

2. **Trim build_fate_projection for the router prompt** so intent_router_pass on Fate worlds returns to ~baseline (~4-6s) without breaking Fate routing accuracy

3. **No error_max_turns fragility** on Fate turns after the trim (the structured call finalizes within max_turns=2)

4. **Verified before/after** on a fresh annees_folles 2-seat understudy run (turn_telemetry numbers)

## Technical Context

### Key Files
- `sidequest-server/sidequest/server/intent_router_pass.py` (lines 364-365 inject build_fate_projection)
- `sidequest-server/sidequest/agents/intent_router.py` (line ~234 build_fate_projection definition)
- `sidequest-server/sidequest/game/llm_factory.py` (lines 399-405 router structured output_format)

### Related Stories
- **126-9** (merged): narrator latency restore — thinking-off disables narrator extended thinking
- **ADR-144**: Fate Core Binding Replaces the Native Ruleset
- **ADR-113**: Intent Router — Mechanical-Engagement Spine

### Investigation Notes
- Turn telemetry is in Postgres; use GM-panel intent_router.decompose spans for state_summary size analysis
- The router is a single Haiku call with structured output; thinking is disabled by #919
- The fragility is prompt bloat → max_turns=2 finalize barrier → intermittent slowness
- This is distinct from 126-9 (narrator thinking-off) and requires independent measurement/fix

## Repo & Workflow
- **Repo:** sidequest-server
- **Branch Strategy:** gitflow (develop is default)
- **Workflow:** tdd (RED → GREEN → review)
