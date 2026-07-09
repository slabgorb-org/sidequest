# Story 163-1 Context

## Title
Server: map.yaml treatment layer — models, loader, protocol block, emission + OTEL (plan tasks 1,3–7)

## Overview
Implement the server-side map.yaml treatment layer for genre-true main-map presentations. Per-world map.yaml declares a treatment (raster PD scans w/ provenance, orrery, dag fallback, generated); server loads it, populates the MAP_UPDATE protocol payload, emits OTEL watcher events. Implements spec **docs/superpowers/specs/2026-07-08-three-tier-mapping-design.md §2** via plan **docs/superpowers/plans/2026-07-08-mapping-track-a-main-map-treatments.md** tasks 1, 3–7.

## Metadata
- **Story ID:** 163-1
- **Epic ID:** 163
- **Repo:** server (sidequest-server)
- **Points:** 5
- **Priority:** p1
- **Workflow:** spdd (Superpower Driven Development — phased TDD)

## Acceptance Criteria (from plan tasks 1,3–7)

### Task 1: Sync & Verify Baseline
- [ ] Pull origin/develop on sidequest-server and verify 158-50 (course/clock router wiring) is shipped
- [ ] 158-50 wiring test `test_course_router_summary_wiring.py` passes green (proves fold is complete, no re-implementation)

### Task 3: MapTreatmentConfig + MapProvenance Models
- [ ] `MapProvenance` model with fields: source, date, archive, pd_basis
- [ ] `MapTreatmentConfig` model with fields: treatment (Literal enum), image (optional), provenance (optional MapProvenance), node_anchors (dict), style_hints (dict)
- [ ] Both models have `extra="forbid"` (fail loud on unknown keys)
- [ ] Comprehensive test coverage (raster full shape, dag treatment needs no image/provenance, unknown kind fails, extra key fails)
- [ ] Exported from sidequest.genre.models

### Task 4: Load map.yaml into World.map_treatment
- [ ] `_load_map_treatment(world_path) -> MapTreatmentConfig | None` loader function
- [ ] Absent map.yaml → returns None (dag fallback by design)
- [ ] Malformed map.yaml → MapTreatmentConfig.model_validate raises (no silent fallback)
- [ ] `World` model gains field: `map_treatment: MapTreatmentConfig | None = None`
- [ ] Loader calls _load_map_treatment in world leaf loader and passes map_treatment to World construction
- [ ] Real-pack load test verifies World field initializes cleanly (production wiring)

### Task 5: Protocol — CartographyTreatmentWire + treatment field on CartographyMapPayload
- [ ] `CartographyTreatmentWire` protocol base model with fields: kind (str), image_url (optional str), node_anchors (dict), style_hints (dict)
- [ ] `CartographyMapPayload` gains field: `treatment: CartographyTreatmentWire | None = None`
- [ ] Payload serializes/deserializes correctly with treatment included
- [ ] Comprehensive test coverage

### Task 6: Populate payload.treatment from World.map_treatment
- [ ] `_build_cartography_map_message` signature updated with `genre_slug: str = ""` param
- [ ] Build `CartographyTreatmentWire` from `world.map_treatment` before return
- [ ] Resolve `map.yaml` image path to CDN/local URL via `resolve_asset_url`
- [ ] Add treatment to CartographyMapPayload
- [ ] Call site in map_emit.py passes genre_slug param
- [ ] Test coverage includes: no treatment (None), raster treatment with full shape (kind, image_url, anchors, style_hints)
- [ ] Real-pack load test verifies end-to-end treatment wiring

### Task 7: Emit map.treatment_emitted OTEL Span
- [ ] After payload.treatment is populated, publish `map.treatment_emitted` event via `_watcher_publish`
- [ ] Event fires only when `msg.payload.treatment is not None`
- [ ] Event fields: world (string), treatment_kind (string), region_count (int), anchor_count (int), has_image (bool)
- [ ] Component: "location"
- [ ] Event reaches turn_telemetry via publish_event (GM panel lie-detector)
- [ ] Test coverage: capture test verifies span fires when treatment present, DB-readback wiring test proves production reachability

## Technical Approach

### Spec Reference
**docs/superpowers/specs/2026-07-08-three-tier-mapping-design.md**
- **§2 Main Map Treatments:** The cartography graph stays coordinate-free and semantic (CartographyConfig); presentation is a separate optional per-world layer loaded from worlds/<slug>/map.yaml into a new World.map_treatment. No map.yaml → d3-dag fallback (by design). Treatment kinds: raster (PD scans w/ provenance), orrery (existing orbital path), dag (fallback), generated (invented-geography seeded SVG).

### Plan Reference
**docs/superpowers/plans/2026-07-08-mapping-track-a-main-map-treatments.md**
- **Task 1:** Sync develop, verify 158-50 (course/clock) already shipped, cut branches
- **Task 3:** Models for map.yaml declaration (MapProvenance, MapTreatmentConfig)
- **Task 4:** Loader to populate World.map_treatment from worlds/<world>/map.yaml
- **Task 5:** Protocol wire format (CartographyTreatmentWire) and payload field
- **Task 6:** Emission: build CartographyTreatmentWire from World.map_treatment, populate MAP_UPDATE payload
- **Task 7:** Observability: OTEL map.treatment_emitted span to turn_telemetry

### Implementation Order (TDD)
1. **Red phase (TEA):** Write failing tests for all tasks
2. **Green phase (DEV):** Implement models → loader → protocol → emission → OTEL in task order
3. **Wiring tests:** Every subsystem includes production-reachability test (no silently-passing unit tests with synthetic fixtures alone)
4. **No silent fallbacks:** Malformed map.yaml fails loud at load; absent map.yaml → dag fallback (by design); raster without provenance/anchors → validator error

### Key Constraints
- Sync develop FIRST (local is 75 commits behind origin/develop)
- Branch/commit in subrepo (server target = develop)
- Task 2 (weed-whack dead cartography models) is story 163-2, already done
- Tasks 8–11 (validator, content) are stories 163-3/163-4
- No new unit tests for content completeness (anchor coverage, provenance) — that belongs in the pack validator (CI-gated path via just content-validate-all)
- OTEL span must reach turn_telemetry via publish_event, not Jaeger alone

## Background
Epic 163 implements three-tier mapping (world/site/battle) per spec §1-5. This story covers the server-side treatment layer (§2) for main-map presentations (Track A). Without this, the Map tab shows a generic d3-dag graph regardless of genre; with it, raster PD scans (Glenross OS sheet, Années Folles Baedeker) and other genre-true visuals become possible. The mechanical bindings (controlled_by, weather_zone, NPC/landmark pins) already live on the cartography graph and will be surfaced in the UI treatment components (stories 163-4/163-5).

---
_Generated by `pf context create story 163-1` from the sprint YAML and plan tasks 1,3–7._
