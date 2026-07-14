# Narrative

## Problem Statement
Problem: Design a lightweight bounded-site interior path — a genre-default/minimal cookbook (or light generator) so tavern/vault archetypes materialize from YAML without the megadungeon cookbook/corpus/themes/world_register stack; fix movement.py uncaught FileNotFoundError on missing interior content. Unblocks 164-7 (Track B B2 e2e).. Why it matters: a defect was impacting functionality.

## What Changed
We implemented: Design a lightweight bounded-site interior path — a genre-default/minimal cookbook (or light generator) so tavern/vault archetypes materialize from YAML without the megadungeon cookbook/corpus/themes/world_register stack; fix movement.py uncaught FileNotFoundError on missing interior content. Unblocks 164-7 (Track B B2 e2e)..
This delivers the following capabilities:
  - ADR authored (or spec amendment to 2026-07-08-three-tier-mapping-design.md) specifying a lightweight bounded-site interior path that materializes a bounded site from archetype YAML WITHOUT requiring a world-local megadungeon cookbook/corpus/themes/world_register stack.
  - The design keeps a new archetype authorable as pure content (Jade/SOUL doctrine: 'archetype = YAML, never engine coupling') and does NOT generate genre-mismatched dungeon interiors (monster spawns / cookbook 'races') in non-dungeon worlds like a tea_and_murder pub.
  - The design specifies how movement.py enter_site (bounded) fails LOUD-but-recoverable when interior content/config is absent — fixing the current uncaught load_cookbook FileNotFoundError that crashes run_movement_dispatch (movement.py:562-613 catches only GenreLoadError/SeamCrossingError).
  - 164-7 (tavern+vault e2e) is re-planned against the designed path — its tasks 13–14 become authorable and its handler/scenario tests reach GREEN under the new approach.

## Why This Approach
This approach addresses the root cause rather than symptoms.

## Before/After
Before: The system exhibited incorrect behavior that affected users.
After: Design a lightweight bounded-site interior path — a genre-default/minimal cookbook (or light generator) so tavern/vault archetypes materialize from YAML without the megadungeon cookbook/corpus/themes/world_register stack; fix movement.py uncaught FileNotFoundError on missing interior content. Unblocks 164-7 (Track B B2 e2e). — the issue has been resolved and verified with tests.
