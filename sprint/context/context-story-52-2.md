---
parent: context-epic-52.md
---

# Story 52-2: Materializer Emits ADR-096 Mask + Derived Block Per Region

## Business Context

The ADR-106 runtime procedural megadungeon is fully stubbed at the substrate level:
the maze-maker family is ported, the region graph generator exists, depth scoring
is live, set-pieces are shaped. But the entire stack is inert — zero production
consumers until the materializer bridges the gap.

This story closes that gap at the materializer's **emit** seam. The materializer
must serialize one ADR-096-shaped mask per generated region and capture the
cell-grid structure so downstream persistence (52-3), PNG rendering (52-4), and
UI wiring (52-5) have something concrete to work with.

**What this story owns:**
- Mask generation from the filled interior grid (stage 2 output)
- One mask per region, persisted as a data shape in the materializer's output
- OTEL `dungeon.materialize.mask` span tracking the derivation
- A derived `block` field (cell width, origin coordinates, etc.) needed for validation and UI binding

**What this story does NOT own:**
- Persistence to disk / database (that's 52-3)
- PNG rendering from the mask (that's 52-4)
- UI consumption and wiring (that's 52-5)

## Technical Scope

### Input
- `RegionFill` from the **fill stage** of materialization (stage 2 output)
- The `Grid` object describing cell boundaries, wall/floor topology

### Output Shape
```python
@dataclass
class RegionMask:
    """ADR-096 mask + derived block info for a single region."""
    grid: Grid               # The source grid (cells, dimensions)
    mask_bytes: bytes        # ASCII mask as bytes (# = wall, . = floor, etc.)
    mask_sha: str           # SHA256 of mask_bytes for deduplication + OTEL tracking
    block: BlockInfo        # Derived from grid: cell_width, origin_x, origin_y, etc.

@dataclass
class BlockInfo:
    """ADR-096 block metadata for cell-stepped math."""
    cell_width: int         # Pixels per cell (typically 28 from ADR-096)
    grid_width: int         # Cells wide
    grid_height: int        # Cells tall
    origin_x: int           # Base coordinate
    origin_y: int           # Base coordinate
```

### Code Changes

**File: `sidequest/dungeon/materializer.py`**
- Import or define `RegionMask` and `BlockInfo` dataclasses
- Add `_emit_mask(fill: RegionFill) -> RegionMask` helper function
  - Takes the `Grid` from `fill` and extracts the mask
  - Converts grid cell-state to ASCII mask (using whatever existing cell representation the grid has)
  - Computes SHA256 of the mask bytes
  - Derives `BlockInfo` from grid dimensions
  - Returns `RegionMask`
- Integrate into the **fill stage** (after grid generation, before curate)
  - Add child span `dungeon.materialize.mask` under the main `dungeon.materialize` span
  - Log `grid_width`, `grid_height`, `cell_width`, `mask_sha` to the span
- Attach the `RegionMask` to the `RegionFill` or return it alongside so downstream stages have it

**File: `sidequest/dungeon/persistence.py`** (minimal)
- Define the `RegionMask` and `BlockInfo` dataclasses here (shared location)
- OR import from a new `sidequest/dungeon/mask.py` module if the definition is substantial

**Acceptance Criteria Context**

| AC | Test / Verification |
|----|---------------------|
| Mask emitted per region | `test_materializer.py`: one `RegionMask` per generated region in a full materialization run |
| Mask bytes are ASCII | `test_materializer.py`: verify mask contains only `#` and `.` (or the defined wall/floor chars) |
| SHA256 computed | `test_materializer.py`: verify `mask_sha` is 64-char hex, deterministic for same grid |
| BlockInfo derived | `test_materializer.py`: verify `cell_width=28`, `grid_width`/`grid_height` match grid |
| OTEL span emitted | `test_materializer.py`: verify `dungeon.materialize.mask` span exists with attrs |
| Non-test consumers | `test_materializer_wiring.py`: materializer invoked from real session path emits mask |

## Context: Existing Grid Model

The `Grid` class (in `sidequest/dungeon/interiors/grid.py` or similar) already
captures the cellular structure:
- Cell dimensions (cell count per axis, pixel size per cell)
- Wall/floor topology (which cells are passable)
- Existing ASCIIification or drawable representation

**Your task:** extract this into the ADR-096 mask format.

## References

- **ADR-096 (Cavern Renderer Revival):** mask format contract, cell-stepped math
- **ADR-106 (Runtime Procedural Jaquaysed Megadungeon):** overall architecture, stage decomposition
- **Materializer docstring (lines 1–131):** pipeline stages, OTEL spine
- **Epic 52 vision:** seam architecture layers 1–5

## Notes

- The mask is immutable per region and frozen in the Expansion once materialized
  (no re-derivation on reload)
- OTEL is mandatory per ADR-106 §12 and project CLAUDE.md
- Wiring test in `test_materializer_wiring.py` proves the mask stage is live,
  not stubbed; until that test passes, the entire 52-1–52-5 epic is unfinished
- No silent fallbacks: if the grid has no cells, if ASCIIification fails, if
  SHA256 computation fails — fail loudly with clear error messages
