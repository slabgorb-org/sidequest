# Story 126-37: [ENGINE] De-nativize Fate confrontation RESOLUTION

## Story Metadata
- **Story ID:** 126-37
- **Epic ID:** 126
- **Title:** [ENGINE] De-nativize Fate confrontation RESOLUTION — extend fate_conflict to the downstream dial guards (apply_beat suppression + advance_confrontation refusal + narration_apply beat-drop)
- **Type:** refactor
- **Points:** 3
- **Priority:** p2
- **Workflow:** tdd
- **Repos:** server
- **Stack Parent:** 126-30 (de-nativize SEATING)

## Acceptance Criteria

1. Under `ruleset=='fate'`, suppress native beat mechanics in the downstream resolution guards: `apply_beat` (beat selection/application), `advance_confrontation` (phase advancement), and `narration_apply` (beat-drop). Extend the `fate_conflict` branch pattern from 126-30's seating to these three resolution paths.
2. A Fate conflict resolves through Fate mechanics only (4dF + ladder + stress/consequence ablation) with NO native beat application, NO native phase advancement dial guards, and NO native beat drops in narration.
3. Preserve invariants and ADR-143 doctrine (Bind the Ruleset, Don't Balance It):
   - The native dial/beat mechanics are REMOVED for Fate, not tuned to coexist (no hybrid seating).
   - NPC resolution still uses server-rolled 4dF (unchanged from 126-7/126-8).
   - The sealed-commit loop (ADR-129/151) is unchanged.
4. Add server tests asserting each guard (apply_beat, advance_confrontation, narration_apply) correctly suppresses native beats for Fate confrontations while WN confrontations retain native mechanics (cross-ruleset validation).
5. Verify end-to-end: drive a Fate conflict to harm resolution in pulp_noir/annees_folles; confirm OTEL spans show only Fate mechanics (fate.action_resolved, fate.stress_applied, fate.consequence_applied), NO native beat spans (beat_selected, beat_applied, confrontation_advanced).

## Context

### Why This Story Exists

Story 126-30 de-nativized Fate confrontation **SEATING** — the upstream entry point where conflicts are instantiated. This story (126-37) extends the same de-nativization to the **downstream RESOLUTION** dial guards where beats are applied and phases advance. Per ADR-143 (Bind the Ruleset, Don't Balance It), the bound ruleset engine must *replace* the native one for what it covers — not layer on top.

126-30 fixed the seating half; 126-37 completes the downstream half so a Fate conflict never touches native beat mechanics from seat to resolve.

### Technical Architecture

**Key files** (follow-up to 126-30):
- `sidequest/server/dispatch/fate_conflict.py` — Fate resolution orchestrator; where fate_conflict branching already exists (126-30 added the seating branch; 126-37 extends it to resolution paths)
- `sidequest/server/game/confrontation.py` — apply_beat and advance_confrontation — must gate these on `ruleset=='fate'` and route to Fate-specific paths
- `sidequest/server/game/narration_apply.py` — beat-drop in narration — must suppress native beat selection from the narrator prompt for Fate conflicts

**Invariants to preserve** (do NOT relax):
- The sealed-commit loop (ADR-129/151) — one action per participant per exchange is unchanged
- NPC rolls stay server-side (126-7/126-8 invariant)
- The win signal is opponent stress + consequence fill toward taken-out (126-30 established)
- No hybrid seating: Fate and native mechanics are mutually exclusive on a seated conflict

### Related Stories

- **126-30:** De-nativize SEATING (upstream, merged) — the entry point for conflict instantiation
- **126-16, 126-8, 126-7:** Fate conflict/defense mechanics (upstream dependencies, merged)
- **126-31:** Render opponent stress track + win-meter (UI-side rendering, parallel downstream)

### References

- **sq-playtest-pingpong** (`~/Projects/sq-playtest-pingpong.md`) — 150-1/150-2 task log with Fate findings
- **ADR-143** — Bind the Ruleset, Don't Balance It (doctrine)
- **ADR-144** — Fate Core binding replaces the native ruleset
- **ADR-129** — N-seat sealed-commit loop
- **ADR-151** — Fate DEFEND follow-up barrier
- **126-30 session file:** `.session/126-30-session.md` — reference for seating-side patterns

## Technical Approach

### Phase 1: Apply-Beat Suppression

**File:** `sidequest/server/game/confrontation.py` (apply_beat function)

1. Check if the current confrontation's ruleset is Fate (`cdef.ruleset=='fate'` or the active EncounterRuleset)
2. If Fate: short-circuit apply_beat and return early (no native beat application)
3. If native (WN): proceed with the existing beat selection/application logic
4. Add OTEL span to confirm the gate fired (fate.apply_beat_suppressed or similar)

### Phase 2: Advance-Confrontation Refusal

**File:** `sidequest/server/game/confrontation.py` (advance_confrontation function)

1. Check if the confrontation is Fate-bound
2. If Fate: do NOT advance phases via the native dial guard; Fate phase advancement is driven by stress/consequence fill toward taken-out (out of scope here, already in fate_conflict.py)
3. If native: proceed with existing phase advancement
4. Add OTEL span to confirm the gate fired

### Phase 3: Narration-Apply Beat-Drop

**File:** `sidequest/server/game/narration_apply.py` (beat-selection in narrator prompt)

1. When building the narrator prompt state (the section that instructs "pick a beat from available_beats"), check if the active encounter is Fate-bound
2. If Fate: do NOT include the available_beats selector in the narrator prompt; Fate narration is not beat-gated
3. If native: include beats as today
4. Add OTEL span or a logger event to confirm the gate fired

### Phase 4: Testing Strategy

**Unit tests:**
- `test_apply_beat_suppressed_for_fate()` — assert apply_beat returns early/no-op for Fate, while native confrontations apply beats normally
- `test_advance_confrontation_gated_for_fate()` — assert advance_confrontation skips native phase guards for Fate
- `test_narration_prompt_excludes_beats_for_fate()` — assert the narrator prompt omits available_beats for Fate (test the gate logic, not the narrator output)

**Integration tests:**
- `test_fate_conflict_resolution_no_native_beats()` — drive a real Fate conflict to harm/resolution and capture OTEL spans; assert no beat_selected/beat_applied/confrontation_advanced spans fire, while fate.* and confrontation.* spans do

**Cross-ruleset validation:**
- Each test should exercise both Fate and WN to prove the gate branches correctly

## Implementation Notes

- Reuse the `fate_conflict` branch pattern from 126-30 (check `cdef.ruleset=='fate'` or equivalent)
- Add minimal OTEL instrumentation for the gate (log when suppression fires, not just silent early return)
- Do NOT change NPC resolution or sealed-commit logic
- Do NOT touch the UI; all changes are server-side

## Notes

- This is the follow-on to 126-30; the two stories complete the "Bind the Ruleset" cleanup for Fate seating and resolution
- Related sidecar gotchas and 126-30/126-16 sessions are reference data (SM handoff materials in `.pennyfarthing/sidecars/`)
- Post-merge: coordinate with GM/content on whether Fate packs' confrontations.yaml should carry native dial/beat defs at all (out of scope here, content decision)
