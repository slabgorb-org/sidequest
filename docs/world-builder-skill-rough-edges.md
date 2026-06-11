# sq-world-builder — Rough Edges Backlog

Living list of where the `sq-world-builder` skill (`.claude/commands/sq-world-builder.md`,
`.claude/agents/world-builder.md`, `.pennyfarthing/workflows/world-builder/steps/*`)
is stale, wrong, or silent for the **post-port / AWN-era mechanics**. Started
2026-06-11 while authoring story 103-7 (Seaboard of Saints cultures + factions +
Cryptic-Alliance). Grouped by theme; severity in brackets.

---

## A. Port-era path & tooling drift (commands that fail outright)

1. **[BLOCKER] Hardcoded `keithavery` / oq-1 paths.** step-01 drift-check loop and
   step-07 validate block use `/Users/keithavery/Projects/oq-1/...`. On this
   machine it's `slabgorb` / oq-2. These bash blocks fail. (cf. memory
   `reference_playtest_paths`.) Make paths relative / env-derived.

2. **[BLOCKER] `sidequest-validate` is the dead Rust CLI.** step-07's "hard gate"
   runs `cargo run -p sidequest-validate` against the Rust binary. The server was
   ported to Python (ADR-082); that validator is historical. The real gate is the
   Python `validate` CLI **and** `load_genre_pack`.

3. **[FIX] Drift-check assumes oq-1 ↔ sidequest-content `.claude/agents/` parity**
   with wrong paths; revisit whether that mirror is still how specialists are
   discovered.

## B. Naming doctrine is WRONG for historical / real-Earth worlds (the big one)

4. **[BLOCKER] "Every name through the conlang" stated as an absolute.** The
   command file, step-01 §3 (CRITICAL), step-06 prereq #5 ("conlang IS the voice
   gatekeeper"), step-06 §7 naming-threading check, and step-07 §7 naming audit
   all force Markov conlang for **every** name and treat real names as
   "English-descriptive slip-throughs" to be rewritten by conlang. This directly
   contradicts Keith's standing directive (`project_historical_worlds_use_word_lists`):
   real-Earth/historical worlds — **Seaboard of Saints**, spaghetti_western,
   tea_and_murder, pulp_noir, neon_dystopia — name NPCs from **curated real
   period word lists sampled directly via `names_file:`**, NOT Markov. The skill
   would push an author to Markov-generate Italian / Wampanoag / Dutch /
   Dominican names → garble ("Gawainwen Boyer"). Fix: split the doctrine —
   *invented/fantasy/sci-fi → conlang Markov (`corpora:`); real-Earth/historical →
   curated `names_file:` lists*. Make the naming audit aware of `names_file:`
   cultures and STOP flagging real names.

5. **[FIX] `cultures.yaml` single pack-level file is assumed.** step-01 and the
   step-06 ownership table give conlang `worlds/{world}/cultures.yaml`. The live
   convention is a **`cultures/` DIRECTORY, one YAML per culture** (flickering_reach,
   five_points, annees_folles, …). Loader supports both, but the directory is the
   current pattern and what 103-7 ships.

6. **[FIX] No `names_file:` vs `corpora:` slot guidance anywhere.** This is THE
   key naming decision for a new culture and the skill is silent. Document the two
   slot shapes, when to curate a word list vs. train Markov, where curated lists
   live (`corpus/shared/*.txt`, one name per line), and that big Gutenberg-book
   corpora (`italian.txt`, `spanish.txt`) are Markov training sets, NOT usable as
   `names_file`.

## C. The new AWN-era mechanics are entirely absent from the skill

7. **[BLOCKER] Saints / `saints.yaml` / SaintRegistry.** No step, no ownership-table
   entry, no schema, no "curate to AWN genre mutation IDs + loud ID validation"
   note. A world-builder run would never produce saints.yaml or know it binds to
   genre-tier mutation IDs.

8. **[BLOCKER] Stocks / `stocks.yaml`.** The multi-path chargen entry layer
   (Saint-Marked / Wild / Sleeper / Animal / Plant / Synthetic) is invisible.

9. **[FIX] Cryptic-Alliance faction tags.** The faction model (writer owns
   lore.yaml factions) has no concept of `joinable` / `chargen_tie` /
   starting-item tokens / the `# AWN Plan 7 Enclave retrofit hook`. In 103-7 the
   wiring (item_hint → inventory → narrator opening reaction; no PC faction field,
   no disposition engine for ties in v1) had to be reverse-engineered from server
   code. Document the v1 content-tag pattern.

10. **[FIX] `char_creation.yaml` (world-tier chargen) not owned by anyone.** The
    world chargen flow — stock step, `requires_stock` branch scenes, the
    cryptic_alliance step, `mechanical_effects` keys the builder actually reads
    (`class_hint` / `race_hint` / `item_hint` / `background` / `pronoun_hint` /
    `saint_id` / `stock_id`; there is NO `faction_hint`) — is a first-class surface
    now and the skill never mentions it. ADR-140: a world char_creation REPLACES
    the genre wholesale.

11. **[FIX] `items.yaml` (world items catalog) not in ownership table.** Implants,
    faction tokens, named_items live here. Note: the **chargen loadout catalog comes
    from genre `inventory.yaml`, not world `items.yaml`** — world `item_hint` ids
    fall back to a minimal inventory dict, so faction-token rich descriptions in
    world items.yaml are read by narrator/retrieval, not by the loadout upgrade.

12. **[BLOCKER] `world.yaml` + `draft: true` lifecycle is absent.** The skill never
    tells the author to ship a new world `draft: true`, never explains that the
    loader **silently skips draft worlds** (so namegen / `load_genre_pack` won't
    see the world at all), and never ties the draft flip to the asset gate. This is
    load-bearing (memory: `project_validate_pack_vs_loader_gaps`).

## D. Validation guidance is stale / insufficient

13. **[FIX] Validator PASS ≠ pack loads.** step-07 treats `sidequest-validate` 0/0
    as the structural gate. Only `load_genre_pack` catches enum fields, the
    draft-skip, and the unified Opening schema (memory
    `project_validate_pack_vs_loader_gaps`). Make `load_genre_pack` the gate.

14. **[FIX] Draft worlds can't be validated via the documented path.** Because the
    loader skips `draft:true`, a step-07 pack load won't include the new world. The
    skill needs a draft-bypass validation recipe (103-7 used a `_load_yaml`
    monkeypatch that forces `world.yaml` `draft=False` in-memory, then full-loads
    and runs namegen + slug checks; see `.archive/validate_seaboard_103_7.py`).

15. **[FIX] `openings.yaml` unified-schema gotcha unmentioned.** The world Opening
    schema (`triggers.mode` solo/MP, `establishing_narration`,
    `first_turn_invitation`) differs from the simple genre shape and parses hollow
    if authored wrong (memory). writer owns openings.yaml but gets no warning.

16. **[NIT] NPCs live under `authored_npcs`** — no guidance for the author.

## E. Structural / convention gaps

17. **[FIX] `legends.yaml` vs `legends/` directory.** Ownership table says
    `worlds/{world}/legends.yaml`; flickering_reach uses a `legends/` DIRECTORY.
    Same single-file-vs-directory drift as cultures.

18. **[FIX] No `bestiary.yaml` / `encounter_tables.yaml` ownership.** The world-tier
    bestiary repoint (memory `project_world_tier_bestiary_resolution`) makes
    `worlds/<slug>/bestiary.yaml` + `encounter_tables.yaml` real authoring
    surfaces; not in the table (103-6 shipped both).

19. **[FIX] `theme.yaml` is styling, not flavor** (memory
    `project_theme_yaml_is_styling_not_flavor`). Required `display_font_family` +
    `dinkus` glyphs or the reference page 500s. Not surfaced.

20. **[NIT] Reference-page anchor stability** = name stability. Renaming a culture /
    faction / legend breaks every inbound reference-page link (no `slug:` override).
    Warn the author before renames.

## F. Process gaps for the new world model

21. **[FIX] Slug-consistency cross-checks missing.** step-06 §7 checks cartography
    adjacency + routes but NOT the new cross-file slug references the AWN mechanics
    add: faction `region:` ⊆ cartography region ids; saint `patron_regions` ⊆
    region ids; culture region bindings; chargen `saint_id`/`stock_id` ⊆
    saints/stocks registries; `chargen_tie.starting_item` ⊆ a real item id. (103-7
    AC4 is exactly this.)

22. **[FIX] OTEL span assertions for new subsystems.** Project OTEL principle
    demands every subsystem emit a watcher span; step-08 playtest should assert
    `awn.saint.applied` / `awn.stock.applied` fire, not just "content plays well."

---

### Suggested fix priority
- **First:** B-4 (naming doctrine), C-12 (draft lifecycle), C-7/8 (saints/stocks),
  A-1/A-2 (dead paths/validator) — these make the skill actively wrong for any
  AWN-era or historical world.
- **Second:** the ownership-table additions (C-10/11, E-17/18), validation gate
  (D-13/14), slug cross-checks (F-21).
- **Polish:** the NITs.
