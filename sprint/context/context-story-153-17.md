# Story 153-17 Context

## Title
[MISSING-COMBAT-SFX] render+upload road_warrior + heavy_metal sfx_library to R2 or drop the manifest refs

## Metadata
- **Story ID:** 153-17
- **Type:** chore
- **Points:** 3
- **Priority:** p3
- **Workflow:** trivial
- **Repo:** content
- **Epic:** 153 — Playtest follow-ups (open findings from the 2026-06-20/21 full-stack /sq-playtest sweep)

## Problem Statement

Two genre packs reference combat SFX in their audio manifests that are absent on R2/CDN. The
errors fire once per combat SFX trigger — every attack — producing console noise and failed audio
decode on every affected combat action. No gameplay is blocked, but the audio gap is persistent and
affects every table playing these packs.

**road_warrior:** `audio.yaml` declares a full `sfx_library` (engine_start, engine_die,
`metal_impact`, tire_blow, crash, radio_crackle, crowd_roar, fuel_pour, wind, horn_blast). However,
no `audio/sfx/*.ogg` files exist anywhere in the road_warrior pack on R2. Every combat action that
triggers `audio/sfx/metal_impact.ogg` 404s at
`/audio-cdn/genre_packs/road_warrior/audio/sfx/metal_impact.ogg`.

**heavy_metal:** `audio.yaml` references `sfx/sword_clash.ogg` which is absent on CDN/R2 (never
rendered or uploaded). Fires on every combat/attack action in any heavy_metal world (barsoom
confirmed; likely genre-tier `audio.yaml`, so all heavy_metal worlds affected — re-confirm on
evropi/150-14).

## Repro / Evidence

**road_warrior:**
- Session: any the_circuit combat action
- Error: `Failed to load resource: 404 … /audio-cdn/genre_packs/road_warrior/audio/sfx/metal_impact.ogg` + `Unable to decode audio data` (2 console errors/beat)
- Root: full `sfx_library` declared in `audio.yaml`, zero `audio/sfx/*.ogg` files present in the pack on R2

**heavy_metal:**
- Session: barsoom/WWN, any combat/attack action
- Error: `Failed to load resource: 404 … /audio-cdn/genre_packs/heavy_metal/audio/sfx/sword_clash.ogg` + `Unable to decode audio data`
- Root: `sfx/sword_clash.ogg` referenced in manifest but absent on R2 (never rendered/uploaded)

Source: board lines 254–262 (ROAD_WARRIOR-MISSING-SFX) and 340–348 (HEAVY-METAL-MISSING-SFX).

## Fix Direction

Two options — pick one per pack, or the same for both:

**Option A (render + upload):** Render the declared SFX and upload to R2. Use the
orchestrator-root venv (`uv run --project .` — render/publish scripts use the root venv, not
sidequest-server; see project convention). SFX live under `genre_packs/<pack>/audio/sfx/`.

**Option B (drop the refs):** Remove the dangling `sfx_library` / sfx entries from each pack's
`audio.yaml` so no 404 fires. No silent fallback: a manifest ref must resolve on R2 or be removed.

Verify audio manifest coverage by diffing `audio.yaml` paths against a live R2 bucket scan (note:
`r2_audit.py` audio classification is unreliable — verify directly against the bucket, not via the
audit script).

## Acceptance Criteria

1. No combat-SFX 404 errors on road_warrior worlds during combat actions (`metal_impact.ogg` and
   the rest of the declared `sfx_library` either resolve on R2 or are absent from the manifest).
2. No combat-SFX 404 errors on heavy_metal worlds during combat actions (`sword_clash.ogg` either
   resolves on R2 or is removed from the manifest).
3. Every `sfx_library` / sfx ref in road_warrior `audio.yaml` and heavy_metal `audio.yaml`
   resolves on R2 OR has been removed — no dangling refs remain.
4. Verified by diffing the updated manifest paths against a live R2 bucket scan (not r2_audit.py
   alone).

## Source

- Board lines 254–262: `[BUG-LOW / ROAD_WARRIOR-MISSING-SFX — combat SFX 404 on every attack]`
- Board lines 340–348: `[BUG-LOW / HEAVY-METAL-MISSING-SFX — sword_clash.ogg 404 on every combat action]`
- Capture file: `/Users/slabgorb/Projects/sq-playtest-pingpong-archive-2026-06-21-epic153-capture.md`

## Scope Notes

- Content/asset chore only — no engine code changes.
- road_warrior: the entire declared `sfx_library` is absent; scope is the whole library (10 files),
  not just `metal_impact`.
- heavy_metal: `sword_clash.ogg` confirmed; check the full `audio.yaml` sfx section for any other
  missing refs before closing (the board entry notes "Likely affects all heavy_metal worlds" —
  re-confirm evropi).
- r2_audit audio classification is unreliable; verify by direct bucket scan (project convention).
- Out of scope: music tracks, ambience, portrait/POI assets, any server or UI change.
