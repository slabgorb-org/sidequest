# Story 114-8 Context

## Title
mutant_wasteland — re-stat inventory against the AWN schema (trauma die/shock), fix genre scrap_armor mitigation

## Metadata
- **Story ID:** 114-8
- **Type:** story
- **Points:** 3
- **Priority:** p3
- **Workflow:** tdd
- **Repos:** server, content
- **Epic:** 114 — SRD-sourced inventory — bind the equipment catalog, don't author it (inventory audit 2026-06-14)
- **Depends on:** 114-1 (Design ADR — SRD-sourced inventory model, schema extensions, licensing policy) — **done**

## Problem
Source: `docs/inventory-audit-2026-06-14.md` (rows for mutant_wasteland). mutant_wasteland binds the **AWN** (Ashes Without Number) ruleset, but its inventory is hand-authored bespoke gear with an AWN-*shaped* envelope rather than gear stated against the AWN equipment schema. Three concrete defects:

1. **Inventory not stated against the AWN schema.** AWN weapons should carry `trauma_die` + `trauma_rating` (the AWN/CWN trauma model) and melee `shock`; armor should carry `ac`/`trauma_target_mod`. Current entries are tuned by hand to "look right." (System Strain *is* already wired for mutant_wasteland implants — that part is good; don't regress it.)
2. **Genre `scrap_armor` has no mitigation.** It provides no AC / `trauma_target_mod`, so wearing it does nothing mechanically.
3. **`power_glove` broken artifact ref.** Chargen offers `power_glove`, but the world catalog (which replaces the genre catalog wholesale) dropped it → fallback-to-weapon regression. The catalog the chargen path reads must carry a (de-genericized) `power_glove`.

## Licensing constraint (HARD — load-bearing)
**AWN free edition carries NO open license** (© 2025, all rights reserved). Per the epic doctrine and ADR-145: **derive / re-stat against the AWN schema — do NOT reproduce AWN tables verbatim.** This is the SWN/AWN "derive, don't copy" lane, distinct from the WWN/CWN "CC0, copy verbatim" lane. Re-statting means matching the *schema and mechanical shape*, with SideQuest-original item names/flavor.

## AWN schema (from audit + 114-1 ADR)
Shared Without-Number item schema: `{name, damage, attribute, encumbrance, cost, tech_level?, traits[]}` plus category extras:
- **Weapon:** `damage, range, cost, magazine, attribute, encumbrance, trauma_die, trauma_rating, tech_level` (melee adds `shock`)
- **Armor:** `ac, encumbrance, trauma_target_mod, subtle, cost, tech_level`
- **Cyberware:** `system_strain` (already wired — preserve)

Confirm exact field names against the 114-1 ADR (ADR-145) and the server `CatalogItem` model before authoring.

## Technical Approach (hints — TEA/Dev refine)
- **Server side:** verify the `CatalogItem` / inventory model supports `trauma_die`, `trauma_rating`, `shock`, and armor `trauma_target_mod`. If absent, extending the model (and the AWN/CWN mitigation read path) is the server slice. Add OTEL on any new mitigation/trauma resolution so the GM panel can confirm the fix fires (project OTEL principle).
- **Content side:** re-stat `genre_packs/mutant_wasteland` inventory (genre baseline) and the affected world catalog against the AWN schema; give `scrap_armor` real mitigation; restore `power_glove` to the world catalog.
- **⚠ Wiring tension to RESOLVE during red/green:** SM notes (memory) say world `inventory.yaml` is engine-unwired (crunch loads genre-tier only), yet this audit row says mutant_wasteland's world catalog "replaces genre wholesale" and *dropped* `power_glove` from chargen. These cannot both be true. **TEA must write a wiring test that proves which tier actually loads for mutant_wasteland** before authoring the fix — otherwise a world-catalog edit may no-op. (cf. CLAUDE.md "Verify Wiring, Not Just Existence".)

## Scope
- **In scope:** mutant_wasteland AWN inventory re-stat (genre baseline + affected world), `scrap_armor` mitigation, `power_glove` restoration, any server schema/mitigation support these require, OTEL coverage, wiring test.
- **Out of scope:** other packs (114-7 space_opera, 114-10/12/13, Fate quartet 114-9), verbatim WWN/CWN extraction, the SRD→inventory extraction tool.

## Acceptance Criteria (candidate — TEA to finalize in RED)
1. mutant_wasteland weapons load with AWN-schema fields (`trauma_die`, `trauma_rating`, melee `shock`); a test asserts representative entries carry these.
2. `scrap_armor` provides real mitigation (AC and/or `trauma_target_mod`) and a test proves the mitigation is applied in resolution (not just present in YAML).
3. `power_glove` is offered at chargen AND resolves from the catalog the chargen path reads (no fallback-to-weapon); a wiring test proves the loaded tier carries it.
4. AWN items are SideQuest-original (derived), not verbatim AWN tables (licensing).
5. `load_genre_pack` for mutant_wasteland still loads clean; System Strain wiring for implants is not regressed.
6. New mitigation/trauma resolution emits OTEL spans verifiable on the GM panel.
7. Full server suite + content validation green (set `SIDEQUEST_DATABASE_URL` and `SIDEQUEST_GENRE_PACKS`; baseline pre-existing failures, treat only new failures as regressions).

---
_Enriched by SM from `docs/inventory-audit-2026-06-14.md` + epic-114 meta. The sprint YAML carries no description/AC block; TEA owns final AC definition in the RED phase._
