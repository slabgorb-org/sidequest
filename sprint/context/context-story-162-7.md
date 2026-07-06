# Story Context: 162-7

## Story
- **ID:** 162-7
- **Title:** All-sources-one-scene wiring test + understudy identity-split hunt: integration test spawning from every source asserting one identity per creature; understudy scenario flags two-names-one-enemy as a finding
- **Type:** chore
- **Points:** 2
- **Workflow:** tdd
- **Repos:** s, e, r, v, e, r, ,, u, n, d, e, r, s, t, u, d, y

## Acceptance Criteria

### Server (sidequest-server)
- Integration/wiring test enumerates all seven spawn sources (2026-07-05 spec)
- For each source, spawns a creature and asserts ONE creature_id (no identity forks)
- Prose names recorded as aliases (not new identities)
- Test fails loudly if any source produces duplicate identity
- Test is reachable from production code paths (wiring verified)

### Understudy (sidequest-understudy)
- Playtest scenario detects "two-names-one-enemy" (same enemy under two names)
- Flags as CONFIRMED/BEHAVIORAL finding
- Finding emitted in understudy report
- Bot perceives as naive player (screen-reader visibility only)

## Epic Context

Part of **Epic-162: NPC origin consolidation — one identity, one arbiter, derived Monster Manual**

### Foundation (162-1 through 162-6, all complete)
1. 162-1: Derive-don't-cache Monster Manual (content-sha + session-seed keyed pool)
2. 162-2: Identity by id (not name) — kills two-names-one-enemy via Origin + alias ledger
3. 162-3: Bestiary generics replace ephemeral stub minting
4. 162-4: Origin-precedence ADR (Green Room) — authored > room-bound > region-population > MM pool > narrator mint
5. 162-5: flickering_reach content reconciliation (18 phantom refs remapped)
6. 162-6: space_opera bestiary de-triplication (12-entry collapse)

**This story (162-7):** Verification capstone — wiring test asserting all sources → one identity

### Reference
- `docs/superpowers/specs/2026-07-05-npc-generation-inventory.md` — Seven spawn paths
- `docs/adr/004-lazy-genre-binding.md` — Origin/provenance semantics
- `docs/adr/121-layered-content-resolution.md` — Layered content resolution
