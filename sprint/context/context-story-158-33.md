# Story 158-33 Context

## Title
Monster Manual cross-world bestiary bleed — MM injection seeds sibling-world creatures (long_foundry into barsoom); scope pre-gen to the current world's bestiary

## Metadata
- **Story ID:** 158-33
- **Type:** bug
- **Points:** 2
- **Priority:** p2
- **Workflow:** tdd
- **Repo:** server,content
- **Epic:** Playtest sweep follow-ups: WWN combat seating, narrator grounding, roster/map/MP polish

## Problem
Playtest finding (pingpong 2026-06-25, heavy_metal/barsoom, session 2026-06-25-barsoom-84c17bdf). Snapshot npcs[] (all manual_origin=True, ADR-059 MM-seeded) includes Foundry Automaton, Grave Knight, Knight of the Ashen Banner, authored ONLY in sibling world genre_packs/heavy_metal/worlds/long_foundry/bestiary.yaml (lines 102/136/155), NOT in barsoom's (correctly canon: Banth, White Ape, Apt, Calot, Thern Zealot, Plant-Man, Kaldane, Sith). monster_manual.injected world=barsoom patches=7 confirms they entered barsoom's MM injection. Player-visible: Salensus Oll's 'Throw him the Knight' latched the long_foundry Knight of the Ashen Banner as the Barsoom arena champion, a Genre/World-Truth break (SOUL: Crunch in Genre, Flavor in World). Root: MM pre-gen pulling from a genre-wide or sibling-world creature pool instead of being scoped to the CURRENT world bestiary. Selective bleed (3 Barsoom-flavored seeds came through fine). CROSS-CHECK whether 158-21..25 WWN bestiary curation changed MM source scoping. Memory: MM cache ~/.sidequest/manuals/<genre>_<world>.json keyed by genre+world. Repos: server (MM scoping) + content (verify world-ownership).

## Technical Approach
_Approach hints from SM context discovery — TEA/Dev to confirm and refine. The
story title above defines the intended behavior._

**Server seam (repo: sidequest-server):**
- `sidequest/game/monster_manual.py` — the persistent MM model (ADR-059). Cache
  at `~/.sidequest/manuals/{genre}_{world}.json`, keyed by genre+world. Seeding
  samples a bestiary (see the note around L354-364 about re-seeding "via the
  correct bestiary path" — a prior bleed of pre-bestiary-binding output).
- `sidequest/server/dispatch/pregen.py` — the seeding pass. `_seed_authored_npcs`
  reads `pack.worlds[world].authored_npcs`; the encountergen invocation already
  passes `--world`. `_encounter_factions` joins bestiary factions by enemy name.
  **Inspect which bestiary object the NPC/encounter seeding samples** — the
  current-world `effective_bestiary` vs an unscoped genre/sibling pool.
- `sidequest/genre/loader.py` — there are TWO bestiary tiers: a **genre-tier**
  pack-root `bestiary.yaml` (≈L2491) and an OPTIONAL **world-tier** `bestiary.yaml`
  (≈L1689), merged **world-over-genre** as `GenrePack.effective_bestiary`
  (L1686-1689). Likely root: seeding reads the genre-tier (or a union of all
  worlds') bestiary instead of `effective_bestiary` scoped to the CURRENT world.
  Selective bleed (3 Barsoom-flavored seeds came through fine) fits a partial-merge
  / wrong-tier source rather than a total scoping failure.
- OTEL: `sidequest/telemetry/spans/monster_manual.py` emits `monster_manual.injected`
  (the `world=barsoom patches=7` span that caught this). Per the OTEL principle,
  the fix should make world-scoping legible here (e.g. surface source-world or a
  rejected-foreign-creature count) so the GM panel proves the scope held.

**Content seam (repo: sidequest-content):**
- Confirm world-ownership: `genre_packs/heavy_metal/worlds/long_foundry/bestiary.yaml`
  (Foundry Automaton / Grave Knight / Knight of the Ashen Banner, L102/136/155)
  vs `genre_packs/heavy_metal/worlds/barsoom/bestiary.yaml` (Banth, White Ape, Apt,
  Calot, Thern Zealot, Plant-Man, Kaldane, Sith) vs the genre-tier
  `genre_packs/heavy_metal/bestiary.yaml`. Determine whether any sibling creatures
  leaked up into the genre-tier (content fix) or whether the leak is purely in
  server source scoping (server fix). Content invariants → pack validator, NOT
  unit tests.

**Cross-check:** Did stories 158-21..25 (WWN bestiary curation) change MM source
scoping? Inspect their diffs before assuming this is a longstanding bug.

## Scope
- In scope: scope MM pre-gen NPC/encounter seeding to the current world's
  `effective_bestiary` so sibling-world creatures never enter another world's MM;
  OTEL legibility for the scoping decision; content/validator verification of
  world-ownership.
- Out of scope: changing ADR-059 architecture, the MM cache key/layout, or
  WWN bestiary content itself; broader narrator-grounding work (other 158-3x stories).

## Acceptance Criteria
_Draft for TEA to confirm/replace during RED — derive failing tests from these._
1. MM pre-gen for `heavy_metal/barsoom` seeds NPCs/encounters drawn **only** from
   barsoom's `effective_bestiary`; none of the long_foundry-only creatures
   (Foundry Automaton, Grave Knight, Knight of the Ashen Banner) appear in
   barsoom's Manual `npcs[]`/`encounters[]`.
2. The legitimate barsoom canon (Banth, White Ape, Apt, Calot, Thern Zealot,
   Plant-Man, Kaldane, Sith) is still seeded — the fix scopes, it does not empty
   the pool (no regression to the 87-4 silently-empty-pool failure mode).
3. A regression test proves the world-scoping seam directly: seeding world A from
   a genre with a sibling world B (B-only creatures) yields a Manual containing
   no B-only creatures. (Use synthetic fixture packs — beware the
   `materialize()`-pollutes-real-content trap: monkeypatch any real-content
   resolver to tmp.)
4. `monster_manual.injected` OTEL span makes the scoping verifiable from the GM
   panel (source world / foreign-creature rejection legible).
5. Content/validator check confirms world-ownership of the heavy_metal bestiaries
   (sibling creatures stay in their own world tier).

---
_Generated by `pf context create story 158-33` from the sprint YAML._
