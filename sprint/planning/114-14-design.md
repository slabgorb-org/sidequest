# Story 114-14 — Design Spec (Architect → TEA/Dev)

**Enforce ADR-145 D3: a fail-loud "no genre-tier bespoke" loader validator for
WN-family packs, AND make the three declared-bespoke packs genre-clean.**
Epic 114 · 13pt · p2 · tdd · repos: content + server · depends_on 114-8.

> SCOPE REVISED 2026-06-15 after measuring the real tree. Keith ruled twice:
> (1) "validator now + migrate all 3 [declared-bespoke] packs, no allow-list, no
> split brain, No Silent Fallbacks"; (2) when the iceberg turned out to be 79
> non-verbatim items across 4 SRD-bound packs, **"narrow this story, file the
> rest as epic."** → This story = the validator + the **23 declared-bespoke**
> items across 3 packs. The **56 unprovenanced** items (caverns_and_claudes 31,
> road_warrior 25) are **epic 119** (verbatim-only sweep + validator upgrade).

## The rule this story enforces (and the rule it does NOT)

Measured genre-tier inventory state (2026-06-15):

| pack | ruleset | items | verbatim | bespoke | no-prov | this story |
|------|---------|-------|----------|---------|---------|-----------|
| mutant_wasteland | awn | 17 | 5 | **12** | 0 | **fix all 12** |
| neon_dystopia | cwn | 72 | 66 | **6** | 0 | **fix all 6** |
| road_warrior | cwn | 96 | 66 | **5** | 25 | **fix the 5**; 25→epic 119 |
| caverns_and_claudes | wwn | 99 | 68 | 0 | 31 | **untouched** → epic 119 |
| elemental_harmony | wwn | 68 | 68 | 0 | 0 | ✅ already clean (the target pattern) |
| heavy_metal | wwn | 68 | 68 | 0 | 0 | ✅ already clean |
| space_opera | swn | — | — | — | — | ✅ no genre inventory (world-tier) |
| pulp_noir/tea_and_murder/wry_whimsy/spaghetti_western | native | — | — | — | — | **EXEMPT** (no SRD to be verbatim from) |

**THE VALIDATOR (this story) = "no genre-tier `provenance.mode == 'bespoke'` in a
WN-family pack."** It does NOT require provenance *presence* and does NOT require
*verbatim-only* — that stricter rule is epic 119, and enforcing it now would break
caverns (31) + road_warrior (25). Because the narrow rule only rejects *declared*
bespoke, caverns and road_warrior's unprovenanced items pass → those packs keep
loading → no split-brain in the bespoke dimension; the no-provenance dimension is
uniformly deferred to 119.

- **Gate to WN-family rulesets** (`awn`/`cwn`/`wwn`/`swn`). NATIVE packs are exempt
  — their genre inventory is authored content (no SRD), and genre-tier bespoke is
  legitimate homebrew there (protects native-pack/Jade authoring). Verified:
  `spaghetti_western` fixture is `ruleset: native`.
- **Fail loud**, naming the offending id(s). No allow-list, no warning-and-continue
  (No Silent Fallbacks — Keith, claude.md).
- Seam: `sidequest/genre/loader.py` (a new `_validate_*` helper called from
  `load_genre_pack`, alongside `_validate_confrontation_beats` et al., raising
  `PackError`). `ItemProvenance` is `models/inventory.py:152`
  (`mode: Literal["verbatim","derived","bespoke"]`). The existing 114-3 provenance
  *presence* contract is test-level only (NOT loader-enforced — pulp_noir loads
  with 0 provenance), so this loader check is net-new; place it as a sibling
  validator. Epic 119 upgrades it to verbatim-only.

## ⚠ Load-bearing wiring trap: world-replaces-genre kits

`resolve_inventory` (`server/dispatch/inventory_resolve.py`) merges `item_catalog`
non-droppably (genre ∪ world) **but takes `starting_equipment` / `starting_gold` /
`currency` from the world WHOLESALE when the world ships an inventory.yaml**
(`resolved = world_inv.model_copy(update={"item_catalog": merged})`). Therefore:

> **The instant you create a `worlds/<w>/inventory.yaml`, that world STOPS
> inheriting the genre `starting_equipment`/`starting_gold`/`currency`.** A new
> world inventory that omits them ships every class an EMPTY kit (silent chargen
> break). Every NEW world inventory.yaml below MUST copy the genre
> `starting_equipment` + `starting_gold` + `currency` verbatim (adjust only if the
> world genuinely wants a different kit).

This is why `flickering_reach`/`franchise_nations`/`the_circuit` (which today have
NO inventory.yaml and inherit genre kits) need the FULL kit block, not just the
moved items. `seaboard_of_saints` already ships its own kits/gold/currency
(verified lines 16/392/423) — it's self-contained.

## Per-pack migration (the 23 declared-bespoke)

### mutant_wasteland (12 bespoke → 0)
- **Genre `inventory.yaml`:** delete the 6 RELICS (`power_glove`, `datapad`,
  `growth_wand`, `purifier`, `mystery_compass`, `ancient_artifact`). AWN-source the
  6 survival/tool items (`water_canteen`, `rad_pills`, `medkit_crude`, `glow_rod`,
  `tool_kit_basic`, `geiger_clicker`) verbatim from the AWN SRD general/medical/
  survival/light gear → `mode=verbatim, srd=awn, license=wn-free, srd_ref`
  (reskinned names OK, D1). Net genre = 11 items, 100% AWN-verbatim. (If a survival
  item has truly no AWN analog, MOVE it to both worlds instead — log a deviation.)
- **`worlds/flickering_reach/inventory.yaml` (NEW):** the 6 relics (bespoke) **+ a
  full copy of the genre `starting_equipment`+`starting_gold`+`currency`** (the
  trap). flickering_reach's kits reference survival ids that stay at genre → resolve
  via the merge.
- **`worlds/seaboard_of_saints/inventory.yaml`:** stamp the 5 existing artifacts
  `provenance: {mode: bespoke}`; ADD `ancient_artifact` (bespoke). Already self-
  contained on kits — just verify kit ids still resolve.

### neon_dystopia (6 bespoke → 0; single world `franchise_nations`)
- **Genre `inventory.yaml`:** delete the 6 bespoke (`smart_pistol`, `katana`,
  `mantis_blades`, `cyberdeck`, `optical_camo`, `data_chip`). Net genre = 66, 100%
  CWN-verbatim.
- **`worlds/franchise_nations/inventory.yaml` (NEW):** the 6 items (bespoke) **+ a
  full copy of genre `starting_equipment`+`starting_gold`+`currency`** (eddies).
  Kits reference `smart_pistol`(4 classes)/`cyberdeck`(Netrunner)/`optical_camo`
  (Ghost) → resolve via merge. No char_creation item_hints in this pack.

### road_warrior (5 declared-bespoke → 0; single world `the_circuit`)
- **Genre `inventory.yaml`:** delete the 5 declared-bespoke (`tire_iron`, `chain`,
  `sawed_off_shotgun`, `crossbow`, `pistol`). **LEAVE the 25 unprovenanced items**
  (rig parts, mount weapons, survival, rig-tier vessels) at genre — epic 119.
  Net genre = 91 (66 verbatim + 25 no-prov), 0 bespoke → validator passes.
- **`worlds/the_circuit/inventory.yaml` (NEW):** the 5 items (bespoke) **+ a full
  copy of genre `starting_equipment`+`starting_gold`+`currency`** (Fuel). Kits
  reference the 5 moved items AND the 25 still-genre items → all resolve in the
  merged catalog. No char_creation item_hints in this pack.
- These were deliberately authored bespoke ("iconic improvised" weapons) — MOVE
  them, don't re-source (preserve identity). Re-sourcing any is a logged deviation.

## Acceptance criteria (RED test plan)

1. **Validator exists + fails loud (RED driver):** `load_genre_pack` on a synthetic
   WN-family pack whose genre `item_catalog` has a `mode: bespoke` item RAISES,
   naming the id. (Vehicle: tmp-copy `swn_test_pack`, inject genre inventory.yaml.)
2. **World-tier bespoke is legal (guard):** same synthetic pack with the bespoke
   item at the WORLD tier loads clean.
3. **Native packs are exempt (boundary guard):** a synthetic NATIVE pack
   (tmp-copy `spaghetti_western`) with a genre `mode: bespoke` item loads clean.
4. **No genre-tier bespoke (RED driver):** for each of mutant_wasteland,
   neon_dystopia, road_warrior, no genre `item_catalog` item is `mode: bespoke`.
   (Fails today: 12/6/5.)
5. **mutant_wasteland relics resolve per world (guard):** `resolve_inventory(pack,
   w)` contains all 6 relic ids for BOTH flickering_reach and seaboard_of_saints.
6. **mutant_wasteland chargen artifacts (wiring):** each char_creation `item_hint`
   (growth_wand/datapad/purifier/power_glove/mystery_compass) upgrades to its
   catalog category via `apply_starting_loadout` in BOTH worlds (datapad→tool,
   power_glove→weapon), NOT the category:weapon stub.
7. **starting_equipment resolves per migrated world (the trap guard):** for
   flickering_reach, franchise_nations, the_circuit — `apply_starting_loadout` with
   `resolve_inventory(pack, w)` yields non-empty kits for every class and every kit
   id resolves (no `chargen.starting_equipment_missing` / minimal stub).
8. **mutant_wasteland survival is AWN-sourced (RED driver):** the 6 survival ids
   that remain at genre carry `mode=verbatim, srd=awn, license=wn-free, srd_ref`
   (or, if moved, are absent from genre and present in both worlds).
9. **Full regression green:** all WN-family packs load clean (`SIDEQUEST_GENRE_PACKS`
   + `SIDEQUEST_DATABASE_URL`); record the pre-existing baseline-fail list first.

## Doctrine
ADR-145 D1/D3/D4 (D4a no-endorsement, D4b SRD-only). ADR-140 + epic 113. SOUL +
claude.md: "No Silent Fallbacks", "No half-wired features", "Verify Wiring, Not
Just Existence", "Crunch in the Genre, Flavor in the World", "Bind the Ruleset,
Don't Balance It". Deferred verbatim-only sweep = **epic 119**.
