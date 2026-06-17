# Story 119-5: 119-3 transport-port cleanup (OQ-17)

## Story Metadata
- **ID:** 119-5
- **Title:** 119-3 transport-port cleanup (OQ-17): remove or re-home the now-vestigial Intent-Router cache-floor guard and restore coverage
- **Epic:** 119 - Narrator inference: move off API-key PAYG onto the free subscription
- **Points:** 3
- **Priority:** p2
- **Type:** refactor
- **Workflow:** tdd
- **Status:** backlog

## Story Summary

After 119-3's port to claude-agent-sdk (which emits no cache_control markers), several Intent-Router cache-floor components are now vestigial and uncovered by tests. The story requires cleanup of:

1. `IntentRouterCacheFloorError` exception
2. `HAIKU_CACHEABLE_PREFIX_FLOOR_TOKENS` constant
3. `_INTENT_ROUTER_CACHE_TTL` constant
4. `_estimate_intent_router_prefix_tokens()` function
5. `build_intent_router_llm()` floor check (llm_factory.py:646-667)

The test suite `test_haiku_cache_control.py` was deleted during 119-3's full-replace.

## Acceptance Criteria

1. **Vestigial guard decision:** Either delete the guard wholesale OR re-home it onto an SDK-exposed cache signal, with a test asserting the chosen behavior (No Silent Fallbacks per SOUL principles).

2. **atexit cleanup:** Register an atexit cleanup for `_neutral_cwd()`'s mkdtemp temp dir (anthropic_sdk_client.py:156, one empty dir per process leak).

3. **Gated live isolation smoke test:** Add a gated LIVE isolation smoke test since AC1 contamination regression (from 119-3) mocks the query seam and cannot catch a real-SDK context-absorption regression. Gate scripts/spike_119_3_agentsdk_subscription.py in ops/CI.

## Dependencies & Blockers

- **Depends on:** 119-3 (transport port, already completed 2026-06-16)
- **No blockers:** Ready to proceed

## Key Modules & Files

- `sidequest-server/sidequest/agents/llm_factory.py` (cache floor check, build_intent_router_llm)
- `sidequest-server/sidequest/agents/anthropic_sdk_client.py` (_neutral_cwd, temp dir cleanup)
- `sidequest-server/tests/agents/` (test suites, formerly test_haiku_cache_control.py)
- `scripts/spike_119_3_agentsdk_subscription.py` (live isolation smoke test harness)

## Notes

- The agent-SDK path does not emit cache_control markers, making the old cache-floor guards unable to trigger
- This is live-but-uncovered code (tests were deleted in 119-3)
- SOUL principle: No Silent Fallbacks — the cleanup must be explicit and tested
