# Story 97-3: Dice banner DC has two sources of truth

## Story Metadata
- **ID:** 97-3
- **Type:** Bug
- **Points:** 3
- **Workflow:** tdd
- **Repositories:** server, ui
- **Status:** backlog

## Summary
The pre-roll TARGET banner DC displays a client-side formula, while the server resolves against its own effective difficulty. These can diverge in certain rulesets (particularly SWN/hp_depletion packs), breaking the player-facing math surface that Sebastien and Jade rely on.

## Problem Statement
Measured in ping-pong dice entry FIXER notes (ui #352):
- **Client-side DC:** `App.tsx` calculates `rawDc = clamp(10 + |beat.base|*2, 10..30)` in `handleBeatSelect`
- **Server-side DC:** Server computes its own effective difficulty independently
- **Divergence:** In SWN/hp_depletion packs, these can differ (e.g., Chico total=12 outcome=Fail vs displayed DC 12)
- **Impact:** Players can't trust the banner; the resolution math is opaque to mechanics-first players (CLAUDE.md: "expose the math behind mechanical resolution")

## Acceptance Criteria
1. The displayed pre-roll target equals the difficulty the server resolves against for both native and hp_depletion rulesets
2. `dice.throw_resolved` difficulty matches the banner the player saw (verifiable in one screenshot+log pair)

## Related Documentation
- **ADR-074:** Dice Resolution Protocol — Player-Facing Rolls via WebSocket
- **CLAUDE.md § Sebastien/Jade:** "expose the math behind mechanical resolution (dice rolls, beat selection, ability costs, advancement deltas) so he doesn't have to guess what just happened"
- **PR ui #352:** Ping-pong 2026-06-07 dice entry FIXER notes
- **PR server #741:** Related dice/difficulty backend observations

## Implementation Notes
The fix requires choosing one of two approaches:
1. **Beat commit round-trip:** Include server-computed DC in the beat-commit response, so the client banner reflects server truth before roll
2. **Pre-roll correction:** Server sends authoritative difficulty to client before roll, client updates banner

Either way, the server must be the single source of truth for DC. Player-facing surfaces (CLAUDE.md principle: mechanics-first players must see the math) demand this consistency.
