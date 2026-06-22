# Story 153-18 Context

## Title
[EVROPI-MISSING-PORTRAITS] render+sync 5 missing evropi picker portraits to R2 or drop from the manifest

## Metadata
- **Story ID:** 153-18
- **Type:** chore
- **Points:** 2
- **Priority:** p3
- **Workflow:** trivial
- **Repo:** content
- **Epic:** 153 — Playtest follow-ups (open findings from the 2026-06-20/21 full-stack /sq-playtest sweep)

## Problem Statement

On the `evropi` world (`heavy_metal`, WWN), 5 of 32 character-picker portraits return 404 on
`cdn.slabgorb.com` — the `portrait_manifest.yaml` references entries that were never rendered and
synced to R2. The other 27 render correctly. The affected entries produce broken-image tiles in the
character-picker; selectable portraits still work.

This matches the known 150-13/150-14 caution that `heavy_metal` portraits were "still rendering."
Barsoom's 18 are complete; `evropi` has these 5 gaps. The likely cause is render-local-but-not-synced-to-R2 drift: `render_batch` writes local PNGs; `r2_sync_packs` and `r2_manifest_from_bucket` are separate manual steps and were not run for these 5.

## Repro / Evidence

Source: playtest capture lines 298–306 (`[BUG-LOW / EVROPI-MISSING-PORTRAITS]`).

The five missing portrait slugs (404 on CDN):
- `picker_vaermm_copyist_f01`
- `picker_zked_daggereye_f01`
- `picker_gnome_tunnelwise_f01`
- `picker_half_orc_minehand_m01`
- `picker_antman_scoutdrone_m01`

Path pattern: `genre_packs/heavy_metal/worlds/evropi/assets/portraits/<slug>.png`

Verified by `naturalWidth==0` on the `<img>` elements in the picker during the 2026-06-20/21
full-stack playtest sweep.

## Fix Direction

**Option A (preferred if renders are available locally):** Render the 5 missing portraits and sync
them to R2. Run under the orchestrator-root venv (`uv run --project .`) — render/publish scripts
use the root venv, not the server's. After sync, regenerate/verify the R2 manifest.

**Option B:** If the source prompts are missing or renders are impractical, drop the 5 entries from
`portrait_manifest.yaml` so the picker shows only resolvable portraits (27 entries).

Either way, no silent fallback: every manifest entry must resolve on R2 or be removed.

**Slug note:** `render_common` keeps non-ASCII characters in slugs; `slugify_player_name` drops them.
Verify the 5 missing slugs against a live bucket scan (`r2_manifest_from_bucket` or `aws s3 ls`)
rather than assuming the manifest slug matches the on-disk filename — slug-rule divergence is a
known source of asset mis-keying.

## Acceptance Criteria

1. All 32 `evropi` picker portrait entries in `portrait_manifest.yaml` resolve on R2/CDN with HTTP
   200 (Option A), **OR** the manifest lists only the 27 resolvable portraits with the 5 broken
   entries removed (Option B). No 404s remain.
2. Verified by diffing `portrait_manifest.yaml` entries against a live bucket scan of
   `genre_packs/heavy_metal/worlds/evropi/assets/portraits/` — not by assumption.
3. No `naturalWidth==0` tiles in the `evropi` character-picker after the fix.

## Source

Playtest capture: `/Users/slabgorb/Projects/sq-playtest-pingpong-archive-2026-06-21-epic153-capture.md`, lines 298–306.

## Scope Notes

- Content chore only — no server or UI code changes.
- Render/publish scripts (`render_batch`, `r2_sync_packs`, `r2_manifest_from_bucket`) live in the
  orchestrator root; run with `uv run --project .` (boto3 is in the root venv, not sidequest-server).
- Check which clone the daemon/server launched from before running renders — daemon reads whichever
  `SIDEQUEST_GENRE_PACKS` it launched with; verify you are authoring in the same clone.
- No new portrait prompts need to be authored unless the source prompts are genuinely missing;
  prefer re-rendering existing prompts and syncing over dropping.
