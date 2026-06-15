# Story 114-14 Context

## Title
Relocate mutant_wasteland genre-tier bespoke to world tier; enforce ADR-145 D3 genre-baseline-verbatim

## Metadata
- **Story ID:** 114-14
- **Type:** story
- **Points:** 5
- **Priority:** p2
- **Workflow:** tdd
- **Repo:** content,server
- **Epic:** 114 — SRD-sourced inventory (ADR-145; bind the catalog, don't author it)
- **Depends on:** 114-8 (done)

## Authoritative design
**Read `sprint/planning/114-14-design.md` first** — the Architect (The Man in Black)
authored a full, *measured* design spec (verified against the real tree, not
asserted). It carries the verified ground truth, the decision, the validator
design, the wiring-trap checklist, and the RED test plan. Background:
`sprint/archive/114-8-session.md` (Delivery Findings).

## Problem
114-8 re-sourced mutant_wasteland's standard gear **verbatim from the AWN SRD** but
left **12 non-AWN `mode: bespoke` items at the GENRE tier** as a documented holding
state. ADR-145 D3 is explicit: the genre baseline is **verbatim-SRD only**;
**bespoke is a WORLD-tier privilege**; a genre-tier bespoke item is a "hard error."
Keith ruled (2026-06-15) these items move to the world tier. This story finishes
that placement *and* makes it self-defending. Same move as ADR-140 / epic 113.

The 12 genre-tier `mode: bespoke` items today:
- **Pre-war RELICS (no AWN analog → genuinely bespoke):** `power_glove`, `datapad`,
  `growth_wand`, `purifier`, `mystery_compass`, `ancient_artifact`
- **Generic survival/medical/tool gear:** `water_canteen`, `rad_pills`,
  `medkit_crude`, `glow_rod`, `tool_kit_basic`, `geiger_clicker`

## Technical Approach (decision — adopts the recommended default)
Net target: **genre `inventory.yaml` = 100% verbatim AWN; relics = world tier.**

- **(A) RELICS → WORLD tier as bespoke (both worlds).** `flickering_reach` has NO
  `inventory.yaml` today → CREATE one carrying the 6 relics (+ `provenance:
  {mode: bespoke}`). `seaboard_of_saints` already carries the 5 chargen artifacts
  (114-2) but **unstamped** → stamp `provenance: {mode: bespoke}`; ADD
  `ancient_artifact`.
- **(B) GENERIC survival/tool gear → PREFER AWN-source verbatim AT GENRE.** AWN is
  itself post-apocalyptic (has radiation rules) → analogs almost certainly exist
  for canteen/rad-meds/medkit/light/toolkit/rad-detector. Source verbatim
  (reskinned name, `mode=verbatim`, `srd=awn`, `license=wn-free`, `srd_ref`) so they
  stay at the genre tier — NOT duplicated across worlds. Only an item with **truly
  no AWN analog** moves to the world tier (both worlds). Blindly moving genre-
  universal gear to both worlds re-introduces the duplication epic 114 exists to
  kill — AWN-sourcing is the D3-clean, anti-duplication outcome.
- **D3 enforcement — EXTEND, don't reinvent.** ADR-145 says the **114-3 validator
  already enforces genre-tier provenance _presence_** (any mode) — which is why
  114-8's bespoke genre items load clean today. Add **one branch**: a genre-tier
  baseline `item_catalog` item's `provenance.mode` MUST be in `{verbatim, derived}`,
  **never `bespoke`** — fail loud, name the offending id (No Silent Fallbacks).
  World-tier bespoke stays legal. Put it where 114-3's presence check lives
  (`sidequest-server/sidequest/genre/loader.py` ~:1623 / `models/pack.py`).
  `ItemProvenance` is at `sidequest/genre/models/inventory.py:152`. Resolver:
  `sidequest/server/dispatch/inventory_resolve.py` (`resolve_inventory`, the 114-11
  non-droppable by-id merge).

## Scope
- **In scope:** content edits to `genre_packs/mutant_wasteland/inventory.yaml`
  (remove all 12 bespoke; AWN-source survival gear), new
  `worlds/flickering_reach/inventory.yaml` (6 relics), edits to
  `worlds/seaboard_of_saints/inventory.yaml` (stamp 5 artifacts + add
  ancient_artifact); server D3 validator branch + tests.
- **Out of scope:** balancing/tuning bound AWN mechanics (Bind, Don't Balance);
  the Salvage-vs-credit economy question (Keith, separate); stamping seaboard's own
  whaling gear unless the validator scope demands it (world-tier bespoke is legal,
  presence optional during migration per ADR-145 D3).

## Acceptance Criteria
1. **No genre-tier mutant_wasteland item has `provenance.mode == "bespoke"`** (genre
   baseline verbatim-only). Fails today (12 bespoke) — the RED headline.
2. **Per world (flickering_reach AND seaboard_of_saints):** `resolve_inventory(pack,
   world)` contains all 6 relic ids (regression guard vs the power_glove
   fallback-to-weapon bug).
3. **Chargen artifact resolution (BOTH worlds):** each `char_creation` `item_hint`
   artifact (growth_wand, datapad, purifier, power_glove, mystery_compass) resolves
   to its correct catalog category (datapad/etc → tool, power_glove → weapon), NOT
   the `category: weapon` minimal-stub fallback.
4. **starting_equipment resolution (BOTH worlds):** every class kit id resolves
   against the merged catalog — no `chargen.starting_equipment_missing` / minimal
   stub.
5. **D3 validator:** a synthetic genre pack with a `mode: bespoke` baseline item
   raises the new loader error (fail-loud); a world-tier bespoke item does NOT.
6. **AWN-sourced survival gear** carries `mode=verbatim`, `srd=awn`,
   `license=wn-free`, `srd_ref`.
7. `load_genre_pack(mutant_wasteland)` loads clean; full regression sweep green
   (set `SIDEQUEST_GENRE_PACKS` + `SIDEQUEST_DATABASE_URL`; record the pre-existing
   baseline-fail list first — anything new is a regression).

## Wiring traps (verify each — silent-break sites)
1. flickering_reach has no `inventory.yaml` → CREATE it or relics vanish at chargen.
2. Both worlds hit char_creation's 5 item_hint artifacts → both resolved catalogs
   must carry them.
3. seaboard's 5 artifacts are unstamped → stamp them; add ancient_artifact.
4. seaboard declares its own `starting_equipment`/`starting_gold` (world-replaces) →
   verify kit ids still resolve.
5. genre `starting_equipment` references survival ids → AWN-sourcing-at-genre keeps
   them resolving; moving any to world tier breaks the genre kit for flickering_reach.
6. `resolve_inventory` must show all 6 relics in the resolved catalog per world.

## Doctrine
ADR-145 D1/D3/D4 (+ D4a no-endorsement, D4b SRD-only). ADR-140 (genre=rulebook,
world=catalog) + epic 113. SOUL: "Crunch in the Genre, Flavor in the World",
"Verify Wiring, Not Just Existence", "No Silent Fallbacks", "Bind the Ruleset,
Don't Balance It".

---
_Enriched by SM from the Architect's design spec (`sprint/planning/114-14-design.md`)._
