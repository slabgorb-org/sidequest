# Story 126-6: [CHORE] Downgrade intent_router.confrontation_verb_unrouted from WARNING

## Story Summary
Telemetry noise cleanup. The `intent_router.confrontation_verb_unrouted` log statement fires at WARNING level for a correct-suppression case (the router matched authored intent_verbs but intentionally declined to emit a confrontation dispatch — expected behavior). Downgrade this path to DEBUG or INFO; preserve WARNING only for genuinely unexpected unrouted verbs if such a case is distinguishable.

## Technical Approach
1. Locate the log statement in `sidequest/server/intent_router_pass.py` (lines ~812-819)
2. Identify the condition that triggers the warning: `verb_hits and not conf_types`
3. Change `logger.warning(...)` to `logger.info(...)` (or `logger.debug(...)` for even lower visibility)
4. Verify there are no other call sites for this log pattern
5. Run affected test suite to ensure no regressions

## Key Details
- **File:** `sidequest-server/sidequest/server/intent_router_pass.py`
- **Line range:** ~812-819
- **Current behavior:** Logs at WARNING when the router matches intent_verbs but declines dispatch
- **Desired behavior:** Log at INFO/DEBUG for the correct-suppression case; preserve WARNING for unexpected cases
- **Context:** Story 59-30, sq-playtest 2026-06-07 standoff seat seam analysis identified this as noise

## Acceptance Criteria
- [x] intent_router.confrontation_verb_unrouted no longer logs at WARNING for the correct-suppression case (downgraded to INFO or DEBUG)
- [x] Genuinely unexpected-unrouted cases, if distinguishable, still log at WARNING
- [x] No regression in related tests or downstream telemetry

## Related Stories / Context
- Epic 126: Fate Core playtest follow-ups (2026-06-16/17)
- Story 59-30: Classification-result observability
- Related: Story 91-2 (intent router call budget)
