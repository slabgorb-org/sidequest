# Demo Script — Story 164-10

## Scene 1: Setup (30 sec)

**Presenter says:** "Problem: Design a lightweight bounded-site interior path — a genre-default/minimal cookbook (or light generator) so tavern/vault archetypes materialize from YAML without the megadungeon cookbook/corpus/themes/world_register stack; fix movement.py uncaught FileNotFoundError on missing interior content. Unblocks 164-7 (Track B B2 e2e).. Why it matters: a defect was impacting functionality."

**Show:** The issue as users experienced it

## Scene 2: Act 1 (2 min)

**Presenter says:** "We implemented: Design a lightweight bounded-site interior path — a genre-default/minimal cookbook (or light generator) so tavern/vault archetypes materialize from YAML without the megadungeon cookbook/corpus/themes/world_register stack; fix movement.py uncaught FileNotFoundError on missing interior content. Unblocks 164-7 (Track B B2 e2e)..
This delivers the following capabilities:
  - ADR authored (or spec amendment to 2026-07-08-three-tier-mapping-design.md) specifying a lightweight bounded-site interior path that materializes a bounded site from archetype YAML WITHOUT requiring a world-local megadungeon cookbook/corpus/themes/world_register stack.
  - The design keeps a new archetype authorable as pure content (Jade/SOUL doctrine: 'archetype = YAML, never engine coupling') and does NOT generate genre-mismatched dungeon interiors (monster spawns / cookbook 'races') in non-dungeon worlds like a tea_and_murder pub.
  - The design specifies how movement.py enter_site (bounded) fails LOUD-but-recoverable when interior content/config is absent — fixing the current uncaught load_cookbook FileNotFoundError that crashes run_movement_dispatch (movement.py:562-613 catches only GenreLoadError/SeamCrossingError).
  - 164-7 (tavern+vault e2e) is re-planned against the designed path — its tasks 13–14 become authorable and its handler/scenario tests reach GREEN under the new approach."

**Show:** ## Demo Script — Design a lightweight bounded-site interior path — a genre-default/minimal cookbook (or light generator) so tavern/vault archetypes materialize from YAML without the megadungeon cookbook/corpus/themes/world_register stack; fix movement.py uncaught FileNotFoundError on missing interior content. Unblocks 164-7 (Track B B2 e2e).

### Scene 1: Setup (30 sec)
**Presenter says:** "Today we're going to show you what we built for Design a lightweight bounded-site interior path — a genre-default/minimal cookbook (or light generator) so tavern/vault archetypes materialize from YAML without the megadungeon cookbook/corpus/themes/world_register stack; fix movement.py uncaught FileNotFoundError on missing interior content. Unblocks 164-7 (Track B B2 e2e).."
**Show:** The project overview

### Scene 2: Demo (1 min)
**Presenter says:** "Here's what this delivers:"
**Show:** ADR authored (or spec amendment to 2026-07-08-three-tier-mapping-design.md) specifying a lightweight bounded-site interior path that materializes a bounded site from archetype YAML WITHOUT requiring a world-local megadungeon cookbook/corpus/themes/world_register stack.
**Show:** The design keeps a new archetype authorable as pure content (Jade/SOUL doctrine: 'archetype = YAML, never engine coupling') and does NOT generate genre-mismatched dungeon interiors (monster spawns / cookbook 'races') in non-dungeon worlds like a tea_and_murder pub.
**Show:** The design specifies how movement.py enter_site (bounded) fails LOUD-but-recoverable when interior content/config is absent — fixing the current uncaught load_cookbook FileNotFoundError that crashes run_movement_dispatch (movement.py:562-613 catches only GenreLoadError/SeamCrossingError).
**Show:** 164-7 (tavern+vault e2e) is re-planned against the designed path — its tasks 13–14 become authorable and its handler/scenario tests reach GREEN under the new approach.

### Scene 3: Closing (30 sec)
**Presenter says:** "That's Design a lightweight bounded-site interior path — a genre-default/minimal cookbook (or light generator) so tavern/vault archetypes materialize from YAML without the megadungeon cookbook/corpus/themes/world_register stack; fix movement.py uncaught FileNotFoundError on missing interior content. Unblocks 164-7 (Track B B2 e2e). — shipped and verified."

## Scene 3: Act 2 (1 min)

**Presenter says:** "Before: The system exhibited incorrect behavior that affected users.
After: Design a lightweight bounded-site interior path — a genre-default/minimal cookbook (or light generator) so tavern/vault archetypes materialize from YAML without the megadungeon cookbook/corpus/themes/world_register stack; fix movement.py uncaught FileNotFoundError on missing interior content. Unblocks 164-7 (Track B B2 e2e). — the issue has been resolved and verified with tests."

**Show:** The fix in action, the problem is now resolved

## Scene 4: Closing (30 sec)

**Presenter says:** "The issue is fixed and users can now proceed without problems."

**Show:** The system working correctly after the fix