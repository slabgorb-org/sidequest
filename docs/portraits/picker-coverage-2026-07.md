# Player-Picker Portrait Coverage — 2026-07 Expansion

**Effort:** Per-World Picker Portrait Expansion
([spec](../superpowers/specs/2026-07-06-picker-portrait-expansion-design.md) ·
[plan](../superpowers/plans/2026-07-06-picker-portrait-expansion.md))

**Status (2026-07-08): partial / interim.** 6 of 11 packs expanded (16 worlds,
**+113 new picker faces**). The remaining 5 packs (6 worlds) were **not** touched
this pass and stand at their 2026-07-06 baseline — see
[Deferred](#deferred-not-expanded-this-pass). Content-only authoring into the
already-shipped picker mechanism (Epic 66); no engine/UI/daemon code changed.

Counts are `type: player_picker` entries per world — before (spec baseline
2026-07-06) → after (manifest census 2026-07-08). No plot content: cultures,
archetypes, and counts only (spoiler rule).

## Validation (Task 13)

- `just content-validate-all` → **11/11 packs PASS, 0 errors.** No
  `player_picker backdrop_poi ... does not match any known POI slug` errors and no
  `player_picker is missing required fields` warnings anywhere.
- Picker-`id` uniqueness across all 22 worlds → **no duplicates.**

## Expanded this pass (6 packs · 16 worlds · +113 faces)

| World | before | after | new | gap addressed | cultures now covered |
|-------|-------:|------:|----:|---------------|----------------------|
| wry_whimsy/oz | 18 | 25 | +7 | Culture → **portal-outsider doctrine**: enrich the single outsider pool, no native cultures | kansas_1900 |
| wry_whimsy/wonderland | 20 | 27 | +7 | Volume/demographic (outsider pool) | victorian_english |
| wry_whimsy/gulliver | 18 | 25 | +7 | Volume/demographic (outsider pool) | georgian_british |
| space_opera/coyote_star | **10** | 20 | +10 | Thin world → full culture coverage | broken_drift, free_miners, hegemonic, tsveri, voidborn |
| space_opera/perseus_cloud | 18 | 23 | +5 | Variety top-up | spacer, thari, yulan |
| space_opera/aureate_span | 18 | 23 | +5 | Variety top-up | cinder_collective, crystalline_choir, makhani, span_aristocracy, vaal_kesh |
| spaghetti_western/five_points | **15** | 22 | +7 | Thin world → full coverage | anglo_american_nativist, black_american, german, irish_catholic, jewish |
| spaghetti_western/dust_and_lead | 18 | 23 | +5 | Variety top-up | ndé, sangre_anglo, sangre_frontera |
| spaghetti_western/the_real_mccoy | 18 | 24 | +6 | Variety top-up | black_american, eastern_european_slavs, german, irish_catholic, jewish, scots_irish_presbyterian, welsh |
| heavy_metal/long_foundry | 17 | 22 | +5 | Variety top-up | astran, kragmoor, orvinnic, perault, thessil |
| heavy_metal/barsoom | 18 | 24 | +6 | Variety top-up | first_born, green_martian, lotharian, red_martian, thern, yellow_martian |
| heavy_metal/evropi | **33** | 38 | +5 | Archetype — genuine gaps only (was high-water mark) | 15 cultures (aldkin … zkęd) |
| elemental_harmony/shattered_accord | **16** | 32 | +16 | Thin → full 8-culture coverage | ember_isles, iron_peaks, jade_kingdoms, lotus_provinces, monsoon_courts, saffron_reaches, sky_temples, tide_reaches |
| elemental_harmony/burning_peace | 18 | 23 | +5 | Variety top-up | burning_peace_ember_isles, emishi_northern_people, nanban_visitors |
| tea_and_murder/glenross | 18 | 30 | +12 | Variety (deep top-up) | colonial_names, english_gentry, highland_scots, industrial_north_names, london_professional_names, servant_class_names |
| tea_and_murder/blackthorn_moor | 18 | 23 | +5 | Variety top-up | english_gentry, household_staff, mill_folk |

**New faces total: 113** — the render-cost figure. A non-`--force` render skips
anything already on R2, so this count is exactly the new work the daemon must do.

### Per-pack subtotals

| Pack | worlds | new faces |
|------|-------:|----------:|
| wry_whimsy | 3 | +21 |
| space_opera | 3 | +20 |
| spaghetti_western | 3 | +18 |
| elemental_harmony | 2 | +21 |
| tea_and_murder | 2 | +17 |
| heavy_metal | 3 | +16 |

## Deferred — not expanded this pass (5 packs · 6 worlds)

At 2026-07-06 baseline; new authoring is future work (Tasks 8–12 of the plan).

| World | pickers (baseline = current) | gap type (from spec) |
|-------|-----------------------------:|----------------------|
| mutant_wasteland/seaboard_of_saints | 20 | Variety top-up |
| mutant_wasteland/flickering_reach | 18 | Fill any culture < 3 / archetype at 0 (spoilable world) |
| caverns_and_claudes/beneath_sunden | 19 | Volume/demographic (single culture surface_folk) |
| neon_dystopia/franchise_nations | 19 | Variety — cliché risk high |
| pulp_noir/annees_folles | 19 | Variety top-up (period-specific) |
| road_warrior/the_circuit | 20 | Archetype floor |

## Doctrine applied

- **wry_whimsy portal-outsider (Keith, 2026-07-06).** Oz/wonderland/gulliver
  pickers use the world's single outsider culture only (kansas_1900 /
  victorian_english / georgian_british). Native-land pickers are a bug, not a
  coverage gap. The census confirms compliance: each of the three worlds shows
  exactly one culture. See `.pennyfarthing/sidecars/gm-decisions.md`.
- **No new archetypes.** Every added face names an already-existing archetype.
- **Specificity over cliché.** Faces are reference-stacked and genre-true, matching
  each culture's documented aesthetic — no "generic fantasy man #4."

## Rendering

Per-world render scripts live in `scripts/render_pickers/` (idempotent — a
non-`--force` run skips faces already on R2). Render at leisure; the daemon must
serve the same workspace whose content was authored (`render_one.sh` preflights
this — see the workspace-mismatch gotcha in `.pennyfarthing/sidecars/gm-gotchas.md`).
