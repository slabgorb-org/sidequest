# Story 100-4 Context: Lore POI Section JSON Projection

## Story Metadata
- **Epic:** 100 (Reference pages → React SPA migration)
- **Story ID:** 100-4
- **Title:** Phase 1 — Lore POI section JSON projection (R2 landscape gate server-side)
- **Points:** 3
- **Workflow:** tdd
- **Repository:** sidequest-server
- **Acceptance Criteria:** 5 (see below)

## Problem Statement

The reference lore page today uses server-side HTML rendering. Epic 100 migrates this to a server-projection + React-render architecture: the server emits public JSON (via a firewall projection), React renders it. This story implements the **POI section** of that projection — points of interest (landscape images with metadata) extracted from `history.yaml`, gated on R2 asset availability, and projected as JSON.

The pattern mirrors the already-shipped story 100-3 (Cast section projection): pre-computed R2 slug gate → allowlist projection → server-side CDN URL resolution → wired into the main `build_lore_projection()`.

## Scope

**In Scope:**
- Implement `build_poi_section(entries, *, pack, world, poi_on_r2_slugs) -> dict | None` in `reference_projection.py`
- Gate on R2 landscape manifest via reuse of existing `_gate_poi_slugs_on_manifest()` (already used by reference_renderer)
- Allowlist projection: `slug`, `name`, `region`, `description`, `image_url` only; no keeper fields
- Server-side URL resolution via `resolve_asset_url(poi_image_key(...))`
- Wire into `build_lore_projection()` (append after map section, before generic-YAML sections)
- OTEL spans: `reference_poi_resolved_span` (per resolved image), `reference_poi_not_found_span` (per missing), one census span per POI section
- TDD red-phase contract, green-phase implementation, wiring integration test

**Out of Scope:**
- POI authoring UI (future)
- React component rendering (story 100-11)
- Keeper POI fields or data enrichment (keeper logic stays in YAML)

## Load-Bearing Architecture

This story reuses the projection firewall and gating infrastructure established in story 100-2 (generic-YAML projection) and 100-3 (Cast section projection).

**Data flow:**
```
history.yaml (points_of_interest[])
  ↓ load_points_of_interest()
[{name, slug, region, description, ...}]
  ↓ load_poi_slug_map()
{anchor_slug: verbatim_slug}
  ↓ _gate_poi_slugs_on_manifest(slug_map, pack, world, pack_dir)
frozenset[anchor_slug]  (R2-gated)
  ↓ passed to build_poi_section()
build_poi_section(entries, poi_on_r2_slugs=gated_set)
  ↓ allowlist projection + resolve_asset_url()
{"id": "poi", "label": "Points of Interest", "entries": [...]}
  ↓ appended to build_lore_projection()
["map", "poi", "cast", "generic_yaml", ...]
```

**Firewall (C1 — ADR-135):** Keeper fields (internal notes, draft status, etc.) never cross the JSON boundary. Only explicit allowlisted keys (`slug`, `name`, `region`, `description`, `image_url`) are projected. Future keeper fields are automatically blocked (allowlist pattern, not denylist).

**R2 gate (story 63-8):** Authored POIs are gated on presence in `r2_manifest.json`. An authored-but-not-on-R2 POI silently omits its image (text-only, no broken `<img>` links). If a POI has zero matching entries on R2, the entire POI section returns `None` (no empty array).

**OTEL (ADR-031/090):** Emits observability spans at the gating decision point:
- `reference_poi_resolved_span(slug, pack, world)` — per slug that matched R2
- `reference_poi_not_found_span(slug, pack, world)` — per slug that did not match
- `reference_poi_section_rendered_span(...)` — one census per POI section

## Acceptance Criteria

1. **POIs passing the landscape gate appear in output**
   - Authored POIs whose `poi_image_key(pack, world, slug)` matches an entry in `r2_manifest.json` appear in the POI section
   - Each entry includes resolved fields: `slug`, `name`, `region`, `description`, `image_url` (absolute CDN URL)
   - Test: `test_ratified_poi_appears_in_output`, `test_landscape_url_resolved_when_on_r2`

2. **POIs failing the landscape gate excluded**
   - Authored POIs not present in `r2_manifest.json` do not appear in the projected output
   - A `reference_poi_not_found_span` is emitted per missing landscape key
   - Test: `test_poi_not_on_manifest_is_excluded`, `test_landscape_url_is_null_when_not_on_r2`

3. **Landscape URL resolved server-side (not raw R2 key)**
   - Portrait URLs are absolute CDN URLs via `resolve_asset_url(poi_image_key(...))`
   - Client never receives a raw R2 object key, manifest path, or internal slug form
   - Test: `test_landscape_url_resolved_when_on_r2`, `test_client_never_sees_raw_r2_key_or_path`

4. **Keeper fields excluded (security firewall)**
   - The allowlist projection uses explicit keys only; no `**entry` splat
   - Only 5 keys cross the boundary: `slug`, `name`, `region`, `description`, `image_url`
   - Internal POI fields (draft flags, keeper notes, unused metadata) never appear in JSON
   - Test: `test_keeper_poi_fields_never_cross_the_boundary`, `test_poi_carries_only_allowlisted_keys`

5. **POI section wired into build_lore_projection output**
   - `build_lore_projection()` appends the POI section after the map section (not after cast; see story 100-2 shape)
   - The POI section appears in the full lore projection JSON when a POI-bearing world is projected
   - Section ID is `"poi"`, label is `"Points of Interest"`, entries are the allowlist projection
   - Returns `None` when no POI survives the R2 gate (empty → omitted from sections array)
   - Test: `test_lore_projection_includes_poi_section`, `test_lore_projection_omits_poi_when_no_manifest`, integration OTEL census

## Test Files

**New test file:** `tests/server/test_reference_poi_projection.py`

Test groups (mirroring 100-3 structure):
1. **Fixture setup** — `_world_dir_with_poi` (parallel to `_world_dir_with_cast`) seeds a minimal world with POI data and R2 manifest
2. **Landscape gate** — `test_poi_on_manifest_appears`, `test_poi_not_on_manifest_excluded`
3. **URL resolution** — `test_landscape_url_resolved_when_on_r2`, `test_landscape_url_is_null_when_not_on_r2`, `test_client_never_sees_raw_r2_key`
4. **Keeper firewall** — `test_keeper_poi_fields_never_cross_boundary`, `test_poi_carries_only_allowlisted_keys`
5. **Wiring** — `test_lore_projection_includes_poi_section`, `test_lore_projection_omits_poi_when_no_manifest`, OTEL census

## Implementation Notes

**Reusable pieces from the codebase:**
- `load_points_of_interest(world_dir)` — loads POI list from history.yaml (reference_renderer.py:1127)
- `load_poi_slug_map(world_dir)` — derives `{anchor_slug: verbatim_slug}` map (reference_renderer.py:1158)
- `_gate_poi_slugs_on_manifest(slug_map, pack, world, pack_dir)` — existing R2 gate (reference_renderer.py:1242)
- `poi_image_key(pack, world, slug)` — helper to construct R2 key (reference_presenters.py)
- `load_r2_manifest_keys(manifest_path)` — manifest loader with fail-loud semantics (reference_renderer.py:1205)
- `resolve_asset_url(key)` — CDN URL resolver (asset_urls.py)

**New symbols:**
- `build_poi_section(entries, *, pack, world, poi_on_r2_slugs) -> dict | None` in `reference_projection.py`
- OTEL spans in `telemetry/spans/reference.py`:
  - `reference_poi_resolved_span(slug, pack, world)`
  - `reference_poi_not_found_span(slug, pack, world)`
  - `reference_poi_section_rendered_span(...)` (census)

**Allowlist projection (security-bearing):**
```python
{
    "slug": poi_slug,
    "name": str(entry.get("name", "")),
    "region": entry.get("region"),
    "description": entry.get("description"),
    "image_url": resolved_url,
}
```

No `**entry` splat. Future keeper POI fields are automatically excluded.

## Related Stories

- **100-1** (done) — ADR-135 amendment (spec foundation)
- **100-2** (done) — Generic-YAML section projection (firewall reuse model)
- **100-3** (done) — Cast section projection (identical pattern, landscape gate is POI parallel)
- **100-5** (backlog) — Timeline section projection
- **100-6** (backlog) — Rules page JSON projection
- **100-8+** (backlog) — React SPA routes and theme integration

## References

- **Spec:** `docs/superpowers/specs/2026-06-08-reference-pages-react-migration-design.md` (epic spec)
- **Load-bearing ADR:** ADR-135 (Reference Pages Are a Public Table Tool) — the firewall doctrine
- **Constraint C1:** Keeper fields never cross JSON boundary via allowlist projection and firewall reuse
- **Story 100-3 session:** `sprint/archive/100-3-session.md` — identical pattern, ready to reuse
- **Reference modules:**
  - `sidequest/server/reference_projection.py` — this module's home (build_lore_map_section, build_cast_section mirrors)
  - `sidequest/server/reference_renderer.py` — POI loaders, gate, existing code
  - `sidequest/server/reference_presenters.py` — poi_image_key helper
  - `sidequest/telemetry/spans/reference.py` — OTEL span definitions
