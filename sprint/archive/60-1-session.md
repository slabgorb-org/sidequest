---
story_id: "60-1"
jira_key: ""
epic: "60"
workflow: "tdd"
---
# Story 60-1: Stop cache-writing the volatile game_state snapshot segment — reposition cache_control breakpoint

## Story Details
- **ID:** 60-1
- **Jira Key:** (none — personal project)
- **Workflow:** tdd
- **Stack Parent:** none
- **Type:** refactor
- **Points:** 3
- **Repos:** sidequest-server

## Story Context

Epic 60 addresses narrator token budget inefficiency. Live playtest on 2026-05-21 revealed that ~77% of per-narrator-call cost is `cache_WRITE` not actual work: a ~12k-token cache breakpoint is re-written to the 5-minute cache on EVERY turn/iteration for the volatile game_state snapshot, which mutates each turn and is therefore never read back.

Cache behavior: stable genre prefix (~11,168 tokens) caches correctly with good hit rates; the snapshot segment thrashes the cache with every turn. Per-call cost ~$0.059, of which ~$0.046 is wasted cache-write premium.

**Scope:** Reposition the prompt template's cache_control breakpoint to exclude the volatile game_state snapshot segment from cache management. The stable prefix (genres, narrative rules, character identity, world constants) should remain cached; only the snapshot (current HP, location, inventory, clock state, NPC locations) should be uncached to avoid wasted writes.

**This complements:**
- 57-3 (ADR-112 stable-zone cache promotion) — which moves more text TO the cache
- 57-5 (ADR-110 snapshot slimming) — which reduces snapshot size
- But this story is distinct: it's about breakpoint placement, not segment size

**Acceptance Criteria:**
1. The cache_control breakpoint is repositioned so the game_state snapshot is NOT cache-written
2. The stable narrative/genre prefix REMAINS in cache_write mode
3. Per-turn OTEL metrics confirm cache_write cost drops by >40% (from ~$0.046 to <$0.027)
4. Playtest verification: run a tea_and_murder turn-sequence and confirm cache cost reduction in dashboard

## Sm Assessment

**Ready for TEA (RED phase).** Setup complete and verified:
- Session at `.session/60-1-session.md` (correct location), branch
  `feat/60-1-snapshot-cache-breakpoint` created in sidequest-server (trunk-based).
- Epic context `sprint/context/context-epic-60.md` and story context
  `sprint/context/context-story-60-1.md` written and validated.
- No Jira (personal project) — Jira claim intentionally skipped.

**Origin:** Discovered during live diagnosis of a 2026-05-21 cost spike. The spike
itself was a duplicate-stack runaway (now fixed in `justfile`); this story is the
*separate* efficiency leak found while watching the clean stack: a `cache_control`
breakpoint sits after the volatile `game_state` snapshot, so ~12k tokens are
cache-written every turn for a guaranteed next-turn miss.

**Key pointers for TEA/Dev:**
- Fix is breakpoint *placement*, not snapshot *size* (≠ ADR-110/57-5) and not
  promoting more static prose (≠ ADR-112/57-3).
- Files: `agents/tooling_protocol.py`, `agents/anthropic_sdk_client.py`,
  `agents/prompt_framework/bucket.py`, `agents/orchestrator.py`.
- OTEL is the lie-detector: `narrator.sdk.usage` logs `cache_read`/`cache_write`/
  `cost_usd`. Success = steady-state `cache_write≈0`, `cache_read>0` still hitting
  the stable prefix, and the delta visible in the GM panel — verified across a
  multi-iteration (tool-loop) turn, not just iter=1.
- Must include a wiring test proving the repositioned assembly is the one sent on
  a real narrator turn (CLAUDE.md: every test suite needs a wiring test).

## Workflow Tracking
**Workflow:** tdd
**Phase:** red
**Phase Started:** 2026-05-21T23:41:52Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-21 | 2026-05-21T23:41:52Z | 23h 41m |
| red | 2026-05-21T23:41:52Z | - | - |

## Delivery Findings

No upstream findings.

## Design Deviations

No deviations logged.