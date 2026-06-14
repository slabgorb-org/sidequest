# Epic 108 Context: WN Combat System Refactor

## Overview
Epic 108 removes native beat scaffolding from Without Number combat and replaces it with a clean WN action system. This is the core architectural cleanup that prevents the native combat engine from bleeding into WN bindings.

## Key Architectural Points

1. **Native beat engine is removed under WN bindings** — no more `apply_beat()` calls, fleeting tags (Opening/Counter Stance), dial advances, or Brace actions in WN combat.

2. **WN action set replaces native beats** — Attack, Use Item, Move/Disengage, Cast. Defense is passive (AC from armor, shield, cover, Foci), not an action.

3. **The WithoutNumberRulesetModule handles all WN combat resolution** — d20 rolls, damage dice, Shock, saves. The seam is at dispatch/dice.py and run_wn_round().

4. **OTEL proves native is OFF** — spans like `wn.native_scaffolding_suppressed` and `wn.action.flavor_rider{affected_mechanics=false}` are lie-detectors that prove the native engine isn't firing.

## Load-Bearing Invariants (preserved)
- ADR-116: Confrontation requires an Other (single room-sourced seater, not narrator-invented)
- ADR-139: Win-condition liveness, HP durability, mechanically-capable Other (authored opponent_damage)
- ADR-114: Ablative HP (Edge replaces old HP dial metric)

## Scope Notes
- **In scope:** WN combat only (hp_depletion)
- **Out of scope:** Dial chase/negotiation confrontations (keep native dial engine even in WN packs)
- **Rollout order:** WWN-first (beneath_sunden in play); heavy_metal/elemental_harmony/barsoom swept the same way; swn/cwn/awn same doctrine, staged

## Stories
- **108-1** (DONE): Engine core cut — remove native apply_beat() from run_wn_round()
- **108-2**: Room-sourced seater (107-2 engine half)
- **108-3**: Content de-nativization (strip beat lists, edge_config)
- **108-4**: ADR-142 doc backfill (housekeeping)
- **108-5**: WN combat player action surface — buttons, flavor rider OTEL
- **108-6**: WWN dying/down window (design open problem — BRAINSTORM-FLAGGED)

## Acceptance Criteria (Epic-level)
- All stories in DONE/DONE status
- All WN combat paths emit native_scaffolding_suppressed OTEL
- Beneath_sunden plays through with WN buttons only (no native beat menu)
- Player action flavor text (chandelier swing) is observably inert via flavor_rider OTEL
