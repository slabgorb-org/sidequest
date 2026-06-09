# Story 98-1: C1 Content — split perseus_cloud orbits.yaml into systems/<id>.yaml, delete fake root, author yula

**Story ID:** 98-1  
**Epic:** ADR-141 Two-Scale Spatial Model (Epic 98)  
**Workflow:** tdd  
**Type:** refactor  
**Points:** 3  
**Repo:** sidequest-content  
**Status:** Ready for RED phase

---

## Story Purpose

Implement the **content-authoring slice** of ADR-141 (accepted 2026-06-08): split the existing monolithic `perseus_cloud/orbits.yaml` (140 bodies) into per-system files. Delete the fabricated `perseus_cloud` primary tier. Author the `yula` system as the first per-system orrery file, serving as a concrete model for the per-system file schema.

This story is pure **YAML content refactoring** — no code changes. It unblocks S1 (server loader rewrite) by providing a real per-system file to load from.

---

## Context from ADR-141

**Two-Scale Spatial Model:**
1. **Galactic/campaign view** — `cartography.yaml` nodes-and-edges graph (systems as nodes, jump edges)
2. **Local view** — Per-system orrery (the `systems/<id>.yaml` file drilled into from the current node)

**Current problem:** `perseus_cloud/orbits.yaml` models a star cluster as a single fake solar system:
- One fabricated root primary `perseus_cloud` (type: star, label "PERSEUS CLOUD")
- 34 real systems hung off it as children
- Orrery renderer faithfully drew this as 34 stars-as-planets on one disc — unreadable, illegible

**Solution:** One file per system. The fake root is deleted. Each system file has its own single parent-less primary.

**Scope:** `yula` only. Other 34 systems authored on demand (Diamonds and Coal principle — ADR-014).

---

## Acceptance Criteria

### AC1: yula.yaml created with correct body hierarchy
File: `sidequest-content/genre_packs/space_opera/worlds/perseus_cloud/systems/yula.yaml`

**Bodies to include:**
1. `yula` — Primary star (root, **no parent field**)
   - `type: star`
   - `semi_major_au: 8.343`
   - `period_days: 8801.8`
   - `epoch_phase_deg: 209.7`
   - `label: "YULA"`
2. `yula_2` — Habitat (parent: yula)
   - `type: habitat`
   - `parent: yula`
   - `semi_major_au: 0.45`
   - `period_days: 110.3`
   - `epoch_phase_deg: 344`
   - `label: "YULA"`
3. `lisbon` — Habitat (parent: yula_2)
4. `mclaughlin_13` — Habitat (parent: yula_2)
5. `thule_7` — Habitat (parent: yula_2)

**Verification:**
- File exists and is valid YAML
- 5 bodies total
- All parent references correct (yula_2/lisbon/etc. parent to yula or yula_2, **not** to perseus_cloud)
- Orbital mechanics fields present and exact (period_days, epoch_phase_deg unchanged from source)

### AC2: Fabricated perseus_cloud primary is deleted
- Remove the entry at orbits.yaml:17 (type: star, label "PERSEUS CLOUD")
- Verify no remaining bodies have `parent: perseus_cloud`
- Grep check: `grep -r "parent: perseus_cloud" genre_packs/space_opera/worlds/` should return zero matches (outside the deleted orbits.yaml)

### AC3: Calendar linkage preserved
- `systems/yula.yaml` includes:
  ```yaml
  clock:
    epoch_days: 0
  ```
- Each body carries `period_days` and `epoch_phase_deg` (exact values from source)
- These feed ADR-130 orbital clock math; no transformation

### AC4: orbits.yaml decision documented
- **Option A (preferred):** Delete orbits.yaml entirely (server story S1 will decide loader tolerance)
- **Option B:** Empty it to a stub comment documenting the split
- Include decision note in session file; coordinate with S1 story if unclear

### AC5: Other systems remain unwritten
- No new files for akkad, forma, amanta, etc.
- A system without a `systems/<id>.yaml` file is a valid (unscripted) jump destination
- No stubs or skeleton files (no stubbing principle)

---

## Technical Details

### Source Data
**Current orbits.yaml structure:**
- Version: 0.1.0
- Clock: `epoch_days: 0`
- Travel: `realism: narrative`
- 140 bodies total

**yula subtree:**
- Primary: `yula` (star)
- Direct child: `yula_2` (habitat)
- Grandchildren: `lisbon`, `mclaughlin_13`, `thule_7` (habitats, parented to yula_2)

### File Schema (per ADR-141)
```yaml
version: "0.1.0"

clock:
  epoch_days: <global campaign day offset>

travel:
  realism: narrative

bodies:
  <system_root>:
    type: star
    label: "..."
    semi_major_au: <float>
    period_days: <float>
    epoch_phase_deg: <float>
  <child_1>:
    parent: <parent_body_id>
    type: habitat
    # ... fields
```

**Key invariant:** One body has **no `parent` field** (system root). All others have `parent`.

### Cartography Integration (no change)
`cartography.yaml` `regions.yula` already declares adjacencies:
```yaml
yula:
  adjacent: ['amanta', 'nimia', 'terma']
```
System orrery file does not modify this.

### ADR-130 Integration
- Clock is global (one per campaign)
- Each body's position computed from global `epoch_days` + local `period_days` + `epoch_phase_deg`
- Per-system file structure is transparent to calendar math

---

## Testing Approach (RED phase)

### File structure tests
- File loads as valid YAML
- `yula` body has no parent field
- `yula_2` parents to `yula`; others parent to `yula_2`
- `clock.epoch_days` and all `period_days`/`epoch_phase_deg` match source

### Removal tests
- No body has `parent: perseus_cloud`
- `orbits.yaml` decision (deleted or stubbed) matches S1 requirement

### Wiring test (CLAUDE.md mandate)
- Once S1 lands, loader resolves `systems/yula.yaml` when party is in yula region
- Not just isolated YAML validity; full end-to-end wiring

---

## Related Stories

**Dependencies:**
- **Blocks:** S1 story (98-2) — Server loader needs real yula.yaml to test against
- **Blocked by:** None

**Related:** U1 (98-3), S2 (98-5), C2 (98-4) all depend on this content

---

## Implementation Notes

- No code changes (YAML only)
- No new server/UI wiring (that's S1/U1)
- yula is a concrete model; other systems authored on demand
- File location: `sidequest-content/genre_packs/space_opera/worlds/perseus_cloud/systems/yula.yaml`
- Ensure directory exists before writing file

