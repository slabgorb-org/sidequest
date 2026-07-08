# Per-World Picker Portrait Expansion — Design

**Date:** 2026-07-06
**Author:** GM
**Status:** Draft — awaiting Keith review
**Type:** Content expansion (genre-pack `portrait_manifest.yaml`) + operator render runbook

---

## Goal

Give players a richer, more representative set of faces to choose from at
character creation. Today most worlds ship ~18 `player_picker` portraits; the
distribution is often lopsided (Oz offers 18 Kansas faces and **zero** for any
of its five Ozian cultures). Expand each world's picker set to cover **its
specific gap** — culture, archetype, or demographic — and deliver a series of
**per-world render scripts Keith runs at his leisure**, since the render is the
expensive, daemon-bound part.

The picker *mechanism* is already shipped (Epic 66,
`2026-05-26-player-portrait-selection.md`, in `plans/completed/`): the server
carries `Character.portrait_ref`, a REST roster endpoint serves pickers, the
daemon has the `portrait_in_location` camera preset, and the UI renders a
`PortraitPanel` grid. **This design authors content into that mechanism. It adds
no engine code.**

## Motivating example (real)

`wry_whimsy/oz` has six cultures — `emerald`, `gillikin`, `kansas_1900`,
`munchkin`, `quadling`, `winkie` — but every one of its 18 picker portraits is
`kansas_1900`. A player who wants to *be* an Ozian (a Munchkin, a Winkie, an
Emerald City native) has no face to pick. A playgroup member's complaint —
"I wanted to be from somewhere other than Kansas" — is this gap, made concrete.

## Current state (baseline, 2026-07-06)

22 live worlds, all with a `portrait_manifest.yaml`. Picker counts:

| World | pickers | World | pickers |
|-------|--------:|-------|--------:|
| caverns_and_claudes/beneath_sunden | 19 | space_opera/aureate_span | 18 |
| elemental_harmony/burning_peace | 18 | space_opera/coyote_star | **10** |
| elemental_harmony/shattered_accord | **16** | space_opera/perseus_cloud | 18 |
| heavy_metal/barsoom | 18 | spaghetti_western/dust_and_lead | 18 |
| heavy_metal/evropi | **33** | spaghetti_western/five_points | **15** |
| heavy_metal/long_foundry | 17 | spaghetti_western/the_real_mccoy | 18 |
| mutant_wasteland/flickering_reach | 18 | tea_and_murder/blackthorn_moor | 18 |
| mutant_wasteland/seaboard_of_saints | 20 | tea_and_murder/glenross | 18 |
| neon_dystopia/franchise_nations | 19 | wry_whimsy/gulliver | 18 |
| pulp_noir/annees_folles | 19 | wry_whimsy/oz | 18 |
| road_warrior/the_circuit | 20 | wry_whimsy/wonderland | 20 |
| | | (heavy_metal/evropi is the current high-water mark) |

## Non-goals

- **No new archetypes.** "Archetype-rich worlds need more archetypes" means
  *picker faces for archetypes that already exist* — not authoring net-new
  archetypes. New archetypes are mechanics/crunch and are **Keith's call**;
  they are out of scope here. If a world genuinely lacks an archetype the
  playgroup wants, that is a separate, Keith-signed-off task.
- **No engine, UI, or daemon code.** The mechanism is shipped. This is YAML
  content plus operator shell scripts wrapping existing render tooling.
- **No re-rendering of existing portraits.** New faces only. A non-`--force`
  render skips anything already on R2.
- **No changes to NPC portraits.** Only `type: player_picker` entries.

---

## The method: a per-world coverage audit

For each world, build a coverage matrix from three axes and diff it against the
existing `player_picker` entries:

1. **Culture** — every stem in `worlds/<world>/cultures/*.yaml` (or the world's
   `cultures.yaml`). A culture with zero picker faces is a hard gap.
2. **Archetype** — the distinct archetypes a player can select at chargen (world
   `archetypes.yaml` + pack archetypes). An archetype with zero picker faces is a
   coverage gap.
3. **Demographics** — sex spread (male / female, plus **non-binary where the
   culture warrants** — aliens, constructs, the deliberately ambiguous, following
   the existing `picker_tsveri_liaison_nb01` precedent), with intentional variety
   in apparent age and build.

The *shape* of each world's gap dictates what gets authored:

| Gap type | Signature | Example | Fix |
|----------|-----------|---------|-----|
| **Culture** | picker faces cluster in 1–2 cultures | Oz (18/18 Kansas) | Author faces for the missing cultures |
| **Archetype** | many distinct archetypes, few covered | `the_circuit`, `evropi` | Cover archetypes with no picker face |
| **Volume / demographic** | coverage is even but thin/generic | `beneath_sunden` | More faces per slot; vary age/build/presentation |
| **Thin world** | well below the ~18 norm | `coyote_star` (10), `five_points` (15) | Bring up to full coverage |

Most worlds exhibit a mix; the audit is per-world, not one-size-fits-all.

## Allocation rule: floors + variety fill

Not a culture × archetype cross-product (that explodes — Oz alone would be
6 × 5 = 30 cells per sex). Instead, the new set for a world is the **union** of
three floors:

- **Culture floor** — every culture gets **≥ 3–4** picker faces, with a sex mix.
- **Archetype floor** — every distinct chargen archetype appears on **≥ 1**
  picker face somewhere in the world (distributed across cultures, not
  cross-producted).
- **Variety fill** — within each culture's faces, deliberately vary apparent
  age, build, and gender presentation so the grid offers genuine choice rather
  than one template recolored.

Because the final count is the union of these floors, **culture-rich or
archetype-rich worlds naturally grow larger** and thin/generic worlds grow
modestly — honoring "no ceiling, right-size per world" without an arbitrary cap.
Rough projection: Oz ≈ 18 → ~26; `coyote_star` ≈ 10 → ~20; `beneath_sunden`
≈ 19 → ~28. Total new faces across 22 worlds: **~200–350** (the render-cost
driver).

---

## Authoring discipline (schema + style)

New entries follow the shipped picker pattern (see
`mutant_wasteland/flickering_reach/portrait_manifest.yaml` for the reference
form) and the `PortraitManifestEntry` model in
`sidequest-server/.../genre/models/pack.py`.

**Slug derivation (load-bearing):** the catalog slug is
`entry.id or slugify(entry.name)` — the single shared derivation used by the
render script (`generate_portrait_images._slugify_name`), the REST roster
endpoint, and `Character.portrait_ref`. New entries use an **explicit `id`** to
remove ambiguity.

Each new entry:

```yaml
  - id: picker_<culture>_<archetype>_<sex><nn>   # explicit, canonical slug
    name: picker <culture> <archetype> <sex><nn> # human-spaced mirror of id
    role: <world-appropriate role label>
    type: player_picker
    culture: <culture filename stem>             # must match a real culture
    archetype: <real archetype name>             # world or pack archetype
    sex: <male | female | nonbinary>
    backdrop_poi: <real POI slug>                # verified against r2_manifest.json
    appearance: >-
      <~50 tokens, ONE person, face + upper body only>
```

Rules:

- **Terse `appearance`, ~50 tokens, ONE person, face and upper body only.** No
  POI/scene prose in `appearance` — a second wide description triggers the
  Z-Image split-montage failure. The backdrop comes from `backdrop_poi`, not
  from the appearance text.
- **`culture` must be a real culture stem** and **`archetype` a real archetype.**
  These drive the UI soft-suggest; a typo silently mis-suggests.
- **`backdrop_poi` must be a real, rendered POI slug** for that world, verified
  against `r2_manifest.json` (not a slugified display name — see the
  `cover_poi` 404 gotcha). Spread backdrops across the world's POIs so the grid
  isn't monotonous.
- **Specificity over cliché.** Reference-stacked, genre-true faces — never
  "generic fantasy man #4." Match each world's established aesthetic and the
  culture's documented look. Mutations/nonhuman traits stated matter-of-fact,
  warranted by the culture, never as horror.
- **Genre truth.** A `pulp_noir` face does not read like a `space_opera` face.

## Backdrop POI assignment

For each world, enumerate its rendered POI slugs from `r2_manifest.json` (or
`history.yaml`) and assign each new picker a backdrop, round-robin across the
available POIs, biased so a culture's faces sit against POIs that culture would
plausibly inhabit. Reuse existing slugs only — this design renders **no new
POIs**.

---

## Deliverables

1. **Authored picker YAML** — new `player_picker` entries appended to each of the
   22 world `portrait_manifest.yaml` files, grouped under a clearly commented
   "PLAYER PICKER PORTRAITS — 2026-07 expansion" block so the additions are
   reviewable as a unit.
2. **Coverage report** — a single markdown table (per world: culture &
   archetype coverage before → after, new face count) so Keith can see exactly
   what each world gained before any render fires.
3. **A series of per-world render scripts** — one runnable script per world (plus
   a master driver and an index/runbook), so Keith renders at his leisure.

## Render-script design (run at leisure)

`generate_portrait_images.py` already supports `--genre <g> --world <w>` and, on
a non-`--force` run, **skips images already on R2** — so a per-world invocation
renders exactly the newly-authored pickers and nothing else. Each per-world
script wraps the full three-step pipeline:

```bash
# scripts/render_pickers/<genre>__<world>.sh   (illustrative shape)
set -euo pipefail
cd <orchestrator-root>
uv run python scripts/generate_portrait_images.py --genre <g> --world <w>   # new faces only
uv run python scripts/r2_sync_packs.py --files <fresh PNG paths>            # upload to R2
uv run python scripts/r2_manifest_from_bucket.py                           # rebuild index
```

Constraints baked into every script:

- **Always `uv run python …`, never bare `python3`** — the render/R2 scripts
  import `boto3`, which lives in the orchestrator's `uv` env. (Bare `python3`
  works under `--force` because `--force` skips the R2 scan, then fails on the
  next non-force run — a trap. The scripts never use bare `python3`.)
- **Per-world isolation** — each script targets one `--genre/--world` so Keith
  can render one world, verify, and move on. A world already rendered is a
  no-op re-run (existing R2 keys are skipped).
- **A master driver** (`render_pickers/all.sh`) runs the per-world scripts in
  sequence for a full sweep, and an index (`render_pickers/README.md`) lists
  each world, its new-face count, and its script.
- The scripts collect the freshly-rendered PNG paths from the render output dir
  to feed `r2_sync_packs.py --files`; the exact glob is settled in the
  implementation plan against the render script's output layout.

> These render scripts are **operator glue** (shell wrappers around existing
> Python tooling), not application source. The GM authors the content and the
> runbook; Keith owns when the renders actually run.

## Sequence

1. Author all new picker YAML across the 22 worlds.
2. Produce the coverage report and the per-world render scripts + runbook.
3. **Keith reviews the specs and coverage report.**
4. Keith runs the render scripts at his leisure (per world or via the master
   driver), which render → sync to R2 → rebuild `r2_manifest.json`.
5. Spot-verify: the new slugs appear in `r2_manifest.json` and the picker grid
   in-game.

---

## Risks & open questions

- **Render cost.** ~200–350 new faces is a large daemon job. Mitigation:
  per-world scripts let Keith spread it out; nothing renders until he chooses.
- **POI backdrop coverage.** A world with few rendered POIs limits backdrop
  variety. Mitigation: round-robin reuse; no new POIs in scope.
- **Culture look drift.** Faces must match each culture's documented aesthetic.
  Mitigation: read each culture file before authoring its faces; specificity
  discipline.
- **Spoiler protection.** Only `mutant_wasteland/flickering_reach` is spoilable.
  Picker authoring needs only public chargen data (cultures, archetypes,
  rendered POI slugs), not plot secrets — so no spoiler exposure. The coverage
  report names cultures/archetypes/POIs only, never plot.
- **Sequencing across 22 worlds.** Large authoring surface. The implementation
  plan will batch worlds (likely by genre pack) with a review checkpoint per
  batch rather than one 22-world megastep.

## Appendix: worked example — Oz

Cultures: `emerald`, `gillikin`, `kansas_1900`, `munchkin`, `quadling`,
`winkie`. Current pickers: 18, all `kansas_1900`, across archetypes
`The Dreamer` (3), `The Innocent` (4), `The Scrapper` (4), `The Surveyor` (3),
`The Wit` (4).

Gap: **culture** — five of six cultures have zero faces. Fix under the
allocation rule: keep the Kansas set, add ≥ 3–4 faces for each of the five
Ozian cultures with a sex mix and archetype spread (each archetype already
appears, so the archetype floor is met by distributing archetypes across the
new culture faces). Projection: 18 → ~26–28. Result: a player can pick a
Munchkin, a Winkie, a Quadling, a Gillikin, or an Emerald City native — not
just a Kansas farmhand.
