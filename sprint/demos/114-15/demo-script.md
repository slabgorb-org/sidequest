# Demo Script — Story 114-15

## Scene 1: Setup (30 sec)

**Presenter says:** "Problem: space_opera ship weapons — give the bespoke dogfight weapon a D3-legal home so multifocal_laser stops re-duplicating across all 3 worlds. 114-7 review follow-up: a bespoke ship weapon (multifocal_laser, 1d4/AP20, ship-weapon) is referenced by the genre-tier rules.yaml dogfight (player_weapon/opponent_weapon, resolved by dogfight_shot.py against resolve_inventory(world).item_catalog), but ADR-145 D3 forbids bespoke at the genre tier — so 114-7 had to copy it identically into aureate_span/coyote_star/perseus_cloud. Resolve the home: preferred = SWN-source ship/vehicle weapons VERBATIM from the SWN starship weapons schema (mode=verbatim makes them genre-tier-legal, single source, no per-world dup); alt = a dedicated ship-weapon catalog/tier the dogfight resolves against; or accept the dup. Architect/TEA picks in RED. Then de-duplicate the 3 worlds and add a regression test that the dogfight weapon resolves with armor_piercing intact.. Why it matters: a defect was impacting functionality."

**Show:** The issue as users experienced it

## Scene 2: Act 1 (2 min)

**Presenter says:** "We implemented: space_opera ship weapons — give the bespoke dogfight weapon a D3-legal home so multifocal_laser stops re-duplicating across all 3 worlds. 114-7 review follow-up: a bespoke ship weapon (multifocal_laser, 1d4/AP20, ship-weapon) is referenced by the genre-tier rules.yaml dogfight (player_weapon/opponent_weapon, resolved by dogfight_shot.py against resolve_inventory(world).item_catalog), but ADR-145 D3 forbids bespoke at the genre tier — so 114-7 had to copy it identically into aureate_span/coyote_star/perseus_cloud. Resolve the home: preferred = SWN-source ship/vehicle weapons VERBATIM from the SWN starship weapons schema (mode=verbatim makes them genre-tier-legal, single source, no per-world dup); alt = a dedicated ship-weapon catalog/tier the dogfight resolves against; or accept the dup. Architect/TEA picks in RED. Then de-duplicate the 3 worlds and add a regression test that the dogfight weapon resolves with armor_piercing intact.."

**Show:** ## Demo Script — space_opera ship weapons — give the bespoke dogfight weapon a D3-legal home so multifocal_laser stops re-duplicating across all 3 worlds. 114-7 review follow-up: a bespoke ship weapon (multifocal_laser, 1d4/AP20, ship-weapon) is referenced by the genre-tier rules.yaml dogfight (player_weapon/opponent_weapon, resolved by dogfight_shot.py against resolve_inventory(world).item_catalog), but ADR-145 D3 forbids bespoke at the genre tier — so 114-7 had to copy it identically into aureate_span/coyote_star/perseus_cloud. Resolve the home: preferred = SWN-source ship/vehicle weapons VERBATIM from the SWN starship weapons schema (mode=verbatim makes them genre-tier-legal, single source, no per-world dup); alt = a dedicated ship-weapon catalog/tier the dogfight resolves against; or accept the dup. Architect/TEA picks in RED. Then de-duplicate the 3 worlds and add a regression test that the dogfight weapon resolves with armor_piercing intact.

### Scene 1: Setup (30 sec)
**Presenter says:** "Today we're going to show you what we built for space_opera ship weapons — give the bespoke dogfight weapon a D3-legal home so multifocal_laser stops re-duplicating across all 3 worlds. 114-7 review follow-up: a bespoke ship weapon (multifocal_laser, 1d4/AP20, ship-weapon) is referenced by the genre-tier rules.yaml dogfight (player_weapon/opponent_weapon, resolved by dogfight_shot.py against resolve_inventory(world).item_catalog), but ADR-145 D3 forbids bespoke at the genre tier — so 114-7 had to copy it identically into aureate_span/coyote_star/perseus_cloud. Resolve the home: preferred = SWN-source ship/vehicle weapons VERBATIM from the SWN starship weapons schema (mode=verbatim makes them genre-tier-legal, single source, no per-world dup); alt = a dedicated ship-weapon catalog/tier the dogfight resolves against; or accept the dup. Architect/TEA picks in RED. Then de-duplicate the 3 worlds and add a regression test that the dogfight weapon resolves with armor_piercing intact.."
**Show:** The project overview

### Scene 2: Demo (1 min)
**Presenter says:** "Let me show you the changes."
**Show:** The implementation in action

### Scene 3: Closing (30 sec)
**Presenter says:** "That's space_opera ship weapons — give the bespoke dogfight weapon a D3-legal home so multifocal_laser stops re-duplicating across all 3 worlds. 114-7 review follow-up: a bespoke ship weapon (multifocal_laser, 1d4/AP20, ship-weapon) is referenced by the genre-tier rules.yaml dogfight (player_weapon/opponent_weapon, resolved by dogfight_shot.py against resolve_inventory(world).item_catalog), but ADR-145 D3 forbids bespoke at the genre tier — so 114-7 had to copy it identically into aureate_span/coyote_star/perseus_cloud. Resolve the home: preferred = SWN-source ship/vehicle weapons VERBATIM from the SWN starship weapons schema (mode=verbatim makes them genre-tier-legal, single source, no per-world dup); alt = a dedicated ship-weapon catalog/tier the dogfight resolves against; or accept the dup. Architect/TEA picks in RED. Then de-duplicate the 3 worlds and add a regression test that the dogfight weapon resolves with armor_piercing intact. — shipped and verified."

## Scene 3: Act 2 (1 min)

**Presenter says:** "Before: The system exhibited incorrect behavior that affected users.
After: space_opera ship weapons — give the bespoke dogfight weapon a D3-legal home so multifocal_laser stops re-duplicating across all 3 worlds. 114-7 review follow-up: a bespoke ship weapon (multifocal_laser, 1d4/AP20, ship-weapon) is referenced by the genre-tier rules.yaml dogfight (player_weapon/opponent_weapon, resolved by dogfight_shot.py against resolve_inventory(world).item_catalog), but ADR-145 D3 forbids bespoke at the genre tier — so 114-7 had to copy it identically into aureate_span/coyote_star/perseus_cloud. Resolve the home: preferred = SWN-source ship/vehicle weapons VERBATIM from the SWN starship weapons schema (mode=verbatim makes them genre-tier-legal, single source, no per-world dup); alt = a dedicated ship-weapon catalog/tier the dogfight resolves against; or accept the dup. Architect/TEA picks in RED. Then de-duplicate the 3 worlds and add a regression test that the dogfight weapon resolves with armor_piercing intact. — the issue has been resolved and verified with tests."

**Show:** The fix in action, the problem is now resolved

## Scene 4: Closing (30 sec)

**Presenter says:** "The issue is fixed and users can now proceed without problems."

**Show:** The system working correctly after the fix