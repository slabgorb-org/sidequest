# Story Context: 116-4 — F2c — Create-Advantage Rendering + Fate Honesty Lie-Detector

**Story ID:** 116-4  
**Epic:** 116 (ADR-144 F2: Fate Core Narrator / Intent-Router Integration)  
**Points:** 5  
**Priority:** p1  
**Workflow:** tdd  
**Repo:** sidequest-server  
**Branch base:** develop  
**Depends On:** 116-2 (F2b — Aspects-as-prompt + invoke surfacing)

---

## Story Summary

Close two critical gaps in the Fate Core → narrator pipeline (F2):

1. **Silent-success problem:** When a create-advantage action succeeds, the engine appends a situation aspect and fires `fate.aspect.created` — but the narrator never hears about the success. Only failure appends a narrator hint. Result: the advantage exists in state but the prose doesn't mention it.

2. **Narrator honesty problem:** The narrator can claim a Fate outcome (an advantage created, a foe taken out) that the engine state doesn't show, with zero mechanical backing. This is the core failure the GM-panel lie-detector (OTEL watcher) exists to catch.

This story surfaces create-advantage successes into narrator hints and the prompt, and adds a `fate_engagement_watcher` to detect and emit `fate.narration.mismatch` when prose claims an outcome the engine state doesn't show.

---

## Technical Approach

### Task 1: Create-Advantage Success Rendering

**What:** Close the narrator-silent-on-success gap by appending a success narrator hint (mirroring the existing failure-hint pattern).

**Where:** `sidequest/game/fate_conflict.py`, `_resolve_create_advantage()` method (lines 550-592).

**Details:**
- On success (shifts > 0), append a narrator_hint naming the created aspect and free-invoke count: `"{actor} created an advantage: {aspect.text} ({free_invoke_count} free invoke(s))."`
- This mirrors the failure-hint style already present at lines 571-577.
- The hint surfaces to the prompt via existing `encounter_render.py:44-45` plumbing (encounter summary includes narrator hints).
- Confirm live `encounter.situation_aspects` are visible to the narrator prompt as in-play scene aspects via the F2b `fate_state` section.

**Design references:**
- Existing failure hint: fate_conflict.py:571-577
- Hint rendering: encounter_render.py:44-45 (`render_encounter_summary`)
- F2b prompt sections: `docs/superpowers/specs/2026-06-14-fate-core-binding-replaces-native-design.md §4.5`

### Task 2: Fate Engagement Watcher (Honesty Lie-Detector)

**What:** Detect when prose claims a Fate outcome (advantage created / foe taken out) that the engine state does not show, and emit `fate.narration.mismatch` OTEL span.

**Architecture:** Mirror the existing `dispatch_engagement_watcher` (dispatch_engagement_watcher.py:371-410):

1. **Pure detection function:** `detect_fate_narration_mismatch(*, narration: str, snapshot: GameSnapshot, package: DispatchPackage | None) -> list[FateNarrationMismatch]`
   - Read **authoritative state** from snapshot: `encounter.situation_aspects`, actor `withdrawn` flags, `encounter.fate_commits`
   - Compare prose claims against state, not against OTEL spans (spans are ephemeral; state is durable)
   - Two witness checks (conservative):
     - `_check_create_advantage_claim(narration, snapshot) -> str | None` — if prose asserts a new advantage was created but `situation_aspects` has no matching aspect, return evidence string
     - `_check_taken_out_claim(narration, snapshot) -> str | None` — if prose asserts a foe is out but no actor is `withdrawn`, return evidence string

2. **Wrapper function:** `run_fate_engagement_watcher(*, narration, package, snapshot, tracer=None) -> None`
   - Calls pure detection function
   - Emits `fate.narration.mismatch` OTEL span per mismatch (non-fatal try/except; watcher crashes do not break turns)
   - Matches dispatch watcher's contract

3. **Wiring:** Post-narration handler at websocket_session_handler.py:1141-1157
   - Add beside existing `run_improvised_combat_watcher` call
   - Pass narration from `result.narration` (or empty string), `package`, `snapshot`

**Design references:**
- Mirror template: dispatch_engagement_watcher.py:371-410, especially `_check_*_engaged` pattern
- Existing watcher wiring: websocket_session_handler.py:1141-1157 (improvised-combat watcher)
- OTEL span emit pattern: `dispatch_engagement_mismatch_span` (telemetry/spans/...)
- Plan details: docs/superpowers/plans/2026-06-14-f2c-fate-advantage-honesty.md §2-4

**Data model:**
```python
@dataclass(frozen=True)
class FateNarrationMismatch:
    subsystem: str  # "create_advantage" | "taken_out"
    claim: str      # the prose excerpt claiming the outcome
    reason: str     # why it mismatches state
```

---

## Acceptance Criteria

1. **Create-advantage success hint:**
   - `_resolve_create_advantage` appends a narrator hint on success (shifts > 0)
   - Hint text: `"{actor} created an advantage: {aspect_text} ({free_invoke_count} free invoke(s))."`
   - Existing create-advantage resolution tests still pass (regression: walk math untouched)
   - Live situation_aspects are visible in the prompt (assertion test against `encounter_render.py` output)

2. **Fate engagement watcher:**
   - `detect_fate_narration_mismatch` returns empty list when prose makes no claim or claim matches state
   - Returns a `FateNarrationMismatch` per detected mismatch (create_advantage or taken_out)
   - `run_fate_engagement_watcher` emits `fate.narration.mismatch` span per mismatch
   - Watcher is non-fatal: internal exception does not propagate to turn flow (emits crashed span instead)
   - False-positive discipline: benign combat prose (no explicit create/taken-out claim) produces no mismatch

3. **Wiring & integration:**
   - Watcher is invoked from post-narration seam (websocket_session_handler.py:1141-1157)
   - Integration test drives fixture turn and asserts span fires
   - Full test suite passes; existing dispatch + improvised-combat watchers unaffected

4. **OTEL:**
   - New span: `fate.narration.mismatch` (spec: docs/superpowers/specs/2026-06-14-fate-core-binding-replaces-native-design.md §6)
   - Attributes: `subsystem` (create_advantage | taken_out), `claim` (prose evidence), `reason`
   - `event_type="state_transition"`, `component="fate"`

---

## Scope & Constraints

- **New files:** `sidequest/agents/fate_engagement_watcher.py` (mirrored from dispatch watcher)
- **Modified files:** fate_conflict.py (append success hint), websocket_session_handler.py (wire watcher), telemetry/spans/... (add span emit + SPAN_ROUTES entry)
- **Test files:** `tests/agents/test_fate_engagement_watcher.py` (mirror dispatch watcher tests: pure + wrapper + wiring), `tests/server/dispatch/test_fate_conflict.py` (add create-advantage success hint test)
- **Deferred (out of scope):** richer claim matching (invoke/compel/concede), auto-correction (re-prompt on mismatch), per-turn aspect delta (stricter "created this turn" check)

---

## Dependencies

- **F1c (merged):** Provides `situation_aspects`, `fate.aspect.created` span, `fate.taken_out` span, `_resolve_create_advantage`, narrator hints infra
- **F2a (merged):** Fate action classifier, FATE_ROUTING_RULES
- **F2b (merged):** Fate prompt sections (fate_state), `_build_fate_summary`, invoke + compel proposal. F2c renders into F2b's prompt-section seam.

---

## Test Strategy

1. **No source-text wiring tests.** Wiring proven by driving the post-narration seam and asserting `fate.narration.mismatch` span fires (not source grep).
2. **False-positive discipline.** Tests include benign prose that must NOT flag; witnesses err toward under-flagging.
3. **Non-fatal contract.** Test forces internal watcher error; asserts turn survives + emits crashed span.
4. **F1c walk unchanged.** Create-advantage resolution math untouched; existing tests stay green.

---

## Definition of Done

- [x] Create-advantage success hint appended to narrator_hints on success
- [x] Live situation aspects visible in prompt
- [x] `fate_engagement_watcher` detects mismatches and emits `fate.narration.mismatch` span
- [x] Watcher wired post-narration beside existing watchers
- [x] Non-fatal contract: watcher crashes do not break turns
- [x] Full test suite green; baseline unchanged
- [x] No false positives on benign prose

---

## References

- **Plan:** docs/superpowers/plans/2026-06-14-f2c-fate-advantage-honesty.md
- **Design:** docs/superpowers/specs/2026-06-14-fate-core-binding-replaces-native-design.md §4.5, §5, §6
- **ADR-144:** Fate Core Binding Replaces Native Ruleset
- **Decomposition:** docs/superpowers/plans/2026-06-14-f2-narrator-intent-router-integration.md (F2c slice)
- **Mirror template:** dispatch_engagement_watcher.py (witness pattern, wiring, span emit)
