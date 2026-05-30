---
parent: context-epic-74.md
workflow: tdd
---

# Story 74-1: Loader refactor — genre-tier flavor becomes world-tier/optional (no genre flavor)

## Business Context

The genre tier must become **mechanics only** (epic 74). Today the genre-pack loader
*hard-requires* the flavor files (`lore`, `cultures`, `archetypes`, `theme`,
`visual_style`, `audio`) at the genre tier — `_load_yaml(path / "X.yaml", …)` raises
`GenreLoadError` if any is missing. That requirement is the single blocker to deleting
genre-tier flavor: you cannot remove the files until the loader stops demanding them and
the world tier becomes authoritative. This story removes that blocker. It delivers no new
player-visible feature on its own; it is the structural enabler for the per-world content
migration and for the correctness win behind the whole epic — flavor that fits the world
instead of a one-size-genre default that's wrong for divergent worlds (Dust & Lead vs the
Real McCoy).

## Technical Guardrails

**Key files to modify:**
- `sidequest-server/sidequest/genre/loader.py` — `load_genre_pack` (genre tier) and
  `_load_single_world` (world tier). Genre flavor loads move from required → optional;
  add/confirm world-tier loaders for `theme`, `visual_style`, `audio`.
- `sidequest-server/sidequest/game/lore_seeding.py` (`:220-230`) — stop seeding genre lore
  once world lore is authoritative (today both are merged into the LoreStore).
- `sidequest-server/sidequest/game/world_grounding_loader.py` (`:47`) — `load_pack_weather`
  → read `world_dir/weather.yaml` instead of `pack_dir/weather.yaml`.
- Consumers already world-preferring (verify, then drop the genre fallback):
  `cli/namegen/namegen.py:267-281`, `server/dispatch/culture_context.py:53-66`,
  `genre/archetype/shim.py:117-158`.
- `theme`/`visual_style`/`audio` consumers that currently read the genre object:
  reference-chrome + connect-time theme load, the portrait/POI render pipeline, and
  `_resolve_audio_urls` — repoint to the world object.

**Patterns to follow:**
- Required-but-loud world surfaces: mirror `visibility_baseline` / `lethality_policy`
  loading in `loader.py` — a world missing a now-required flavor file fails *loud* at load
  (No Silent Fallbacks), never a silent default.
- OTEL: emit a `state_transition` watcher event per world-tier flavor load, mirroring the
  existing `world_items` (`loader.py:_load_world_items`) and `genre_pack` (`loader.py`
  end-of-`load_genre_pack`) spans, so the GM panel can prove world-tier loading fired.
- Wiring test: each moved surface needs an integration test proving the world-tier load
  reaches its consumer (CLAUDE.md "Every Test Suite Needs a Wiring Test"); prefer OTEL-span
  or fixture-driven behavior tests, NOT source-text grep assertions.

**What NOT to touch:**
- The trope engine (`trope_tick.py`, `session_helpers.py:1103`) — moving tropes to the
  world tier is a **separate story** (engine change + per-world deck authoring).
- `prompts.yaml` / `beat_vocabulary.yaml` — boundary cases pending Keith's ruling.
- The mechanics files (rules, progression, axes, classes, inventory, etc.) — they stay.
- Deleting the genre-tier flavor files themselves — that's the per-world migration story,
  after worlds are self-sufficient.

## Scope Boundaries

**In scope:**
- Make genre-tier `lore`, `cultures`, `archetypes`, `theme`, `visual_style`, `audio`
  loads **optional** in `load_genre_pack` (no `GenreLoadError` when absent).
- Add world-tier loaders for `theme`, `visual_style`, `audio` (these have none today);
  switch `weather` to world-tier.
- Make the world tier authoritative for all of the above; drop the genre fallback path
  for cultures/archetypes; stop genre lore seeding.
- Loud-fail when a world lacks a surface the engine genuinely needs (mirror
  visibility_baseline/lethality_policy).
- OTEL spans + wiring tests for each moved surface.
- Update the `validate pack` `extensions:` schema/manifest expectations to match the new
  tier placement.

**Out of scope:**
- Trope engine reading world tropes + per-world trope decks (separate story).
- Authoring the actual world-tier flavor content for packs that lack it (per-world
  migration story) — though `space_opera/perseus_cloud` archetypes must be authored before
  the archetype fallback is dropped, or that world breaks.
- Deleting genre-tier flavor files (post-migration).
- `prompts.yaml` / `beat_vocabulary.yaml` (boundary ruling).

## AC Context

1. **Genre flavor loads are optional.** A genre pack whose root lacks `lore.yaml`,
   `cultures.yaml`, `archetypes.yaml`, `theme.yaml`, `visual_style.yaml`, `audio.yaml`
   loads without error. *Test:* a fixture pack with those files absent loads; assert no
   `GenreLoadError` and the `GenrePack` is assembled.
2. **World tier is authoritative + loud.** With a world selected, the world's flavor is
   used; genre flavor is not consulted. A world missing a required surface fails loud at
   load. *Test:* fixture world with its own theme/visual_style/audio → consumer sees the
   world values (assert via the consumer, not the file); a world missing a required
   surface raises a clear load error naming the file.
3. **Lore is world-only.** Genre lore is no longer seeded; the narrator's LoreStore for a
   world contains only world lore. *Test:* drive `seed_world_lore`; assert no
   `lore_genre_*` fragments remain when genre lore seeding is removed.
4. **Weather reads world tier.** `load_pack_weather`→world equivalent reads
   `world_dir/weather.yaml`. *Test:* world weather file present → grounding tool returns
   it; pack-root weather is ignored.
5. **OTEL proves it.** Each world-tier flavor load emits a `state_transition` watcher
   event. *Test:* assert the spans fire on a fixture world load.
6. **All 10 live packs still load + validate** with their current files in place (the
   refactor is backward-compatible until content actually moves). *Test:* `validate pack`
   green across all live packs; full server suite passes.

## Assumptions

- Existing world-tier loaders for `lore`/`cultures`/`archetypes` (already in
  `_load_single_world`) are sufficient; only `theme`/`visual_style`/`audio`/`weather` need
  new world-tier loaders.
- Making genre flavor optional is backward-compatible: live packs keep their genre files
  until the migration story, so this refactor can land before any content moves.
- `perseus_cloud` is the only live world relying on the genre archetype fallback; dropping
  the fallback requires authoring its archetypes (tracked as a migration dependency, not
  in this story).
- The `validate pack` `extensions:` construct is validation-only (not read at runtime),
  so adjusting it cannot affect the running engine.

> If any assumption proves wrong during implementation, log it as a Design Deviation and
> notify SM — wrong assumptions are the #1 source of scope creep.
