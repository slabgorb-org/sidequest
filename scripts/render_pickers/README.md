# Picker Portrait Render Runbook

Per-world render scripts for the 2026-07 picker-portrait expansion. **Run these at
your leisure** — nothing renders until you invoke a script.

## What each script does

`render_one.sh <genre> <world>` runs the full pipeline for one world:

1. `generate_portrait_images.py --genre <g> --world <w>` — renders portraits. A
   **non-`--force`** run **skips images already on R2**, so only the *newly-authored*
   picker faces render.
2. `r2_sync_packs.py --files <new PNGs>` — uploads just the new files to R2.
3. `r2_manifest_from_bucket.py` — rebuilds the committed `r2_manifest.json` index.

The thin per-world wrappers (`<genre>__<world>.sh`) just call `render_one.sh` with
that world's args. `all.sh` runs every world in sequence.

## How to run

```bash
# Prereq: the media daemon must be WARM.  (from orchestrator root)
just daemon            # if not already running

# One world:
scripts/render_pickers/wry_whimsy__oz.sh

# A whole pack (run its worlds):
scripts/render_pickers/space_opera__coyote_star.sh
scripts/render_pickers/space_opera__perseus_cloud.sh
scripts/render_pickers/space_opera__aureate_span.sh

# Everything that's been authored:
scripts/render_pickers/all.sh
```

## Standing rules (baked into the scripts)

- **Daemon must be warm** — these call the render daemon; start it with `just daemon`.
- **Always `uv run python`** (the scripts do this) — never bare `python3`; the
  render/R2 scripts import `boto3` from the orchestrator `uv` env.
- **Idempotent** — a world already fully rendered is a clean no-op. Safe to re-run.
- **Renders only new faces** — existing portraits already on R2 are skipped.

## Readiness — which worlds are authored & reviewed

Only run a world once its authoring is ✅. Running a not-yet-authored world is a
harmless no-op (no new faces exist), but there's nothing to render.

| Pack | Worlds | Status |
|------|--------|--------|
| wry_whimsy | oz, wonderland, gulliver | ✅ ready |
| space_opera | coyote_star, perseus_cloud, aureate_span | ✅ ready |
| spaghetti_western | dust_and_lead, five_points, the_real_mccoy | ⏳ in review |
| heavy_metal | barsoom, long_foundry, evropi | ⬜ pending |
| elemental_harmony | burning_peace, shattered_accord | ⬜ pending |
| tea_and_murder | glenross, blackthorn_moor | ⬜ pending |
| mutant_wasteland | seaboard_of_saints, flickering_reach | ⬜ pending |
| caverns_and_claudes | beneath_sunden | ⬜ pending |
| neon_dystopia | franchise_nations | ⬜ pending |
| pulp_noir | annees_folles | ⬜ pending |
| road_warrior | the_circuit | ⬜ pending |

> This table is updated as packs complete. `✅ ready` = authored, validated, and
> review-passed; safe to render.
