# Story 126-30: [ENGINE] De-nativize Fate confrontation SEATING

## Story Metadata
- **Story ID:** 126-30
- **Epic ID:** 126
- **Title:** [ENGINE] De-nativize Fate confrontation SEATING — under ruleset=='fate' seat a standoff/conflict directly as a Fate contest (4dF + ladder, four actions, ablative stress); do NOT seat or feed native beats / a tension dial
- **Type:** refactor
- **Points:** 5
- **Priority:** p2
- **Workflow:** tdd
- **Repos:** server

## Acceptance Criteria

1. Under `ruleset=='fate'`, seat a standoff/conflict as a pure Fate contest (Fate mechanics only). Do NOT seat native beat_defs, native tension dials, or any beat-based mechanics alongside Fate.
2. The win signal is the opponent's stress + consequence fill toward taken-out (per ADR-144), NOT the vestigial `opponent_metric.tension` dial.
3. Preserve invariants — do NOT relax:
   - `compute_dc` NotImplementedError (ADR-144 safety net) — Fate confrontations do NOT use native DC-based resolution.
   - `decide_opponent_action` sheet-required guard (#966) — NPC opponents must have a Fate sheet bound before seating.
4. Add a server test asserting a Fate confrontation seats without native beat_defs and uses only Fate mechanics (OTEL span proof: FATE_ROLL + fate.* + confrontation.* spans present; no native beat spans).
5. Verify the seating fix integrates end-to-end: seat a real Fate conflict in a Fate pack (e.g. grab/attack an NPC in pulp_noir/annees_folles) and confirm GM panel shows Fate mechanics only (no native tension dial).

## Context

### Why This Story Exists

The 2026-06-19 full-stack Fate Core evaluation playtest (150-1/150-2) confirmed the Fate conflict spine fires end-to-end, but revealed that seating still feeds *both* Fate mechanics *and* native beat definitions. Per ADR-143 (Bind the Ruleset, Don't Balance It) and ADR-144 (Fate Core binding), the bound ruleset engine must *replace* the native one for what it covers — not layer on top.

This is the upstream seating half of the Bind-the-Ruleset cleanup that PR #964 only partially did:
- **#964 (merged):** Gated the native overlay from co-rendering with FATE_STATE
- **126-30 (this story):** De-nativize seating so a Fate confrontation seats with Fate mechanics only, no native beats

The win signal is the opponent's stress + consequence fill toward taken-out, NOT the vestigial `opponent_metric.tension` dial.

### Technical Architecture

**Key files** (from epic context):
- `server/dispatch/encounter_lifecycle.py` — seating orchestrator, entry point for `should_emit_native_confrontation` gate
- `server/dispatch/confrontation.py` — apply confrontation logic, where the native-vs-Fate branching must happen
- `game/ruleset/fate.py` — Fate ruleset module; `compute_dc` NotImplementedError is the ADR-144 safety net

**Invariants to preserve** (do NOT relax):
- The `compute_dc` NotImplementedError (ADR-144 safety net) — Fate confrontations do NOT use native DC-based resolution
- The `decide_opponent_action` sheet-required guard (#966) — NPC opponents must have a Fate sheet bound before seating
- The sealed-commit guard (ADR-129/151) — the one-action-per-participant-per-exchange invariant

### Related Stories

- **126-29:** Gate proactive action tiles on sealed-commit state (UI-side gating for resumed conflicts)
- **126-31:** Render opponent stress track + win-meter (UI-side rendering, uses server projection from #973)
- **126-32:** NPC identity + culture routing fix (binding seam; large/risky)

### References

- **sq-playtest-pingpong** (`~/Projects/sq-playtest-pingpong.md`) — 150-1/150-2 task log, SM TRIAGE table
- **ADR-143** — Bind the Ruleset, Don't Balance It (doctrine)
- **ADR-144** — Fate Core binding replaces the native ruleset
- **ADR-129** — N-seat sealed-commit loop
- **ADR-151** — Fate DEFEND follow-up barrier

## Testing Strategy

1. **Unit test:** Assert that a Fate confrontation initializes without native beat_defs; only Fate mechanics emit.
2. **Integration test:** Seat a real Fate conflict in a Fate pack (pulp_noir/annees_folles) and verify OTEL spans show FATE_ROLL + fate.* + confrontation.* (no native beat spans).
3. **GM panel verification:** Confirm the live conflict shows Fate stress/consequences only, no native tension dial.

## Notes

- This is the first story in the Fate confrontation correctness cluster (126-29…126-30).
- PR #964 and PR #973 (merged) are upstream; this story picks up where they left off.
- Jira: no Jira key — sprint YAML only.
