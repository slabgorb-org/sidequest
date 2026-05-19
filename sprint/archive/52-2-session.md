---
story_id: "52-2"
jira_key: null
epic: "52"
workflow: "tdd"
---

# Story 52-2: Materializer Emits ADR-096 Mask + Derived Block Per Region

## Story Details

- **ID:** 52-2
- **Jira Key:** (none — SideQuest is personal project per feedback_playtest_no_jira.md)
- **Workflow:** tdd
- **Stack Parent:** none
- **Epic:** 52 — Wire Procedural Megadungeon Output to the ADR-096 Cavern Renderer Pipeline
- **Points:** 3
- **Repos:** sidequest-server

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-05-19T11:15:29Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-19T08:00:00Z | 2026-05-19T10:47:42Z | 2h 47m |
| red | 2026-05-19T10:47:42Z | 2026-05-19T10:55:23Z | 7m 41s |
| green | 2026-05-19T10:55:23Z | 2026-05-19T10:59:39Z | 4m 16s |
| spec-check | 2026-05-19T10:59:39Z | 2026-05-19T11:01:29Z | 1m 50s |
| verify | 2026-05-19T11:01:29Z | 2026-05-19T11:09:30Z | 8m 1s |
| review | 2026-05-19T11:09:30Z | 2026-05-19T11:13:44Z | 4m 14s |
| spec-reconcile | 2026-05-19T11:13:44Z | 2026-05-19T11:15:29Z | 1m 45s |
| finish | 2026-05-19T11:15:29Z | - | - |

## Acceptance Criteria

| AC | Context |
|----|---------|
| Mask emitted per region | One `RegionMask` per generated region in a full materialization run; test coverage in `test_materializer.py` |
| Mask bytes are ASCII | Mask contains only valid wall/floor characters; verified in tests |
| SHA256 computed | `mask_sha` is 64-char hex string, deterministic for same grid |
| BlockInfo derived | `cell_width=28` (ADR-096), `grid_width`/`grid_height` match source grid |
| OTEL span emitted | `dungeon.materialize.mask` child span under main span, with attributes (`grid_width`, `grid_height`, `mask_sha`) |
| Non-test consumers | Materializer invoked from real session path (not just unit tests); wiring test in `test_materializer_wiring.py` |

## Sm Assessment

Story is the gateway for the 52-series cavern-renderer chain (52-2 → 52-3 → 52-4 → 52-5). Materializer currently has the documented Plan-5-API gap at line 56 — it builds the grid but never emits the mask + derived block. This story fills that exact gap so persistence (52-3), PNG sidecar (52-4), and UI wiring (52-5) have something real to consume.

**Scope is contained:** one file (`sidequest/dungeon/materializer.py`), one new `_emit_mask` function inside the fill stage, one OTEL child span. Data model shapes (`RegionMask` / `BlockInfo`) are specified in Technical Notes.

**Risk surface:** ADR-096 mandates cell_width=28; tests must lock that constant. SHA256 must be deterministic across runs. OTEL span must nest under `dungeon.materialize` per ADR-031 conventions. No silent fallbacks on empty/malformed grids — fail loudly.

**TDD handoff to TEA (Radar):** Tests come first. Cover the six ACs in the table above, plus the wiring-test rule (non-test consumer reachable through real session path). Materializer is invoked from `world_materialization`/dungeon session bootstrapping — verify that path actually exercises the new emit.

## Delivery Findings

(Agents append findings below this line as they discover upstream blockers or gaps.)

- No upstream findings yet.

### TEA (test design)
- No upstream findings during test design. Story scope (session + context-story-52-2.md) is internally consistent; the materializer's documented Plan-5-API gap (materializer.py:56) cleanly justifies the new emit step; existing fill stage already opens the `dungeon.materialize.fill` span we nest under. ADR-096 §2 cell-stepped math contract is the authoritative source for `cell_width=28`. No conflicts between session scope, story context, epic context, or ADR-096/106.

### TEA (test verification)
- **Improvement** (non-blocking): External sibling repo `~/Projects/dice-lib/src/DiceTray.tsx` line 11 has a TypeScript error (`TS1484: 'Root' is a type and must be imported using a type-only import when 'verbatimModuleSyntax' is enabled`). It surfaces during `just check-all`'s `client-typecheck` step but is **outside the 52-2 diff** (story 52-2 is Python-only in `sidequest-server`). Pre-existing; should be tracked as its own dice-lib fix in a separate story. *Found by TEA during test verification.*

## TEA Assessment

**Tests Required:** Yes
**Status:** RED (12 failing tests committed, ready for Dev)

**Test Files:**
- `tests/dungeon/test_materializer.py` — added `TestStageEmitMask` class (11 tests) at line 3503+
- `tests/dungeon/test_materializer_wiring.py` — added `test_mask_emit_fires_from_real_materialize_pipeline` (1 wiring test)

**Tests Written:** 12 tests covering all 6 ACs + No-Silent-Fallback rule + frozen-dataclass invariant

| AC | Tests |
|----|-------|
| Mask emitted per region | `test_emit_mask_attaches_region_mask_to_each_fill` |
| Mask bytes are ASCII | `test_emit_mask_bytes_are_ascii_walls_and_floors_only` |
| SHA256 computed | `test_emit_mask_sha256_is_64_hex_lowercase_and_deterministic` |
| BlockInfo derived | `test_block_info_cell_width_is_adr096_canonical_28`, `test_block_info_dimensions_match_source_grid` |
| OTEL span emitted | `test_dungeon_materialize_mask_span_emitted_per_region`, `test_mask_span_nests_under_fill_span`, `test_mask_span_routed_for_gm_panel` |
| Non-test consumers (wiring) | `test_mask_emit_fires_from_real_materialize_pipeline` |

**Plus rule-coverage tests:**
- `test_region_mask_dataclass_shape_exists` — locks the field set
- `test_empty_grid_raises_loudly_no_silent_fallback` — CLAUDE.md No-Silent-Fallback rule
- `test_region_fill_is_still_frozen_after_mask_field_added` — preserves frozen+slots discipline on RegionFill

### Rule Coverage (Python lang-review checklist)

| Rule | Test(s) | Status |
|------|---------|--------|
| #1 Silent exception swallowing | `test_empty_grid_raises_loudly_no_silent_fallback` | failing |
| #6 Test quality (no vacuous assertions) | All — specific value checks throughout | failing |
| #14 No-silent-fallback (CLAUDE.md, project-specific) | `test_empty_grid_raises_loudly_no_silent_fallback` | failing |

Rules #2 (mutable defaults), #3 (type annotations), #4 (logging), #5 (paths), #7 (resource leaks), #8 (unsafe deserialization), #9 (async pitfalls), #10 (import hygiene), #11 (input validation), #12 (dependency hygiene), #13 (fix regressions) — N/A to this story's surface area (pure in-memory dataclass + bytes + sha + OTEL span; no I/O, no async at this seam, no external input, no new deps).

**Self-check:** No vacuous assertions. Every test asserts on a specific value or specific exception kind, not on truthiness. The frozen-instance test uses `pytest.raises(dataclasses.FrozenInstanceError)` (specific exception class). The wiring test asserts `attrs.get("cell_width") == 28` (specific) and `isinstance(..., int)` (locked type), not truthy presence.

### Test Design Notes for Dev (Major Winchester)

**Data model placement:** The story context says `RegionMask`/`BlockInfo` may live in `materializer.py` or a new `sidequest/dungeon/mask.py` module. Either is fine — the tests import from `sidequest.dungeon.materializer` (re-export from there if you put the classes elsewhere). The shape contract is fixed by `test_region_mask_dataclass_shape_exists`.

**Mask format:** The ASCII test allows `#`, `.`, and `\n`. You can ship rows joined by `\n` or as one flat byte sequence — both pass. Pick whichever serializes cleanly for 52-3 (persistence BLOB) and 52-4 (PNG generator).

**SHA derivation:** `mask_sha = hashlib.sha256(mask_bytes).hexdigest()`. The test verifies this exact relationship (the bytes are the input).

**Span placement:** Open `dungeon_materialize_mask_span(...)` INSIDE `_stage_fill`, once per region, inside the `dungeon_materialize_fill_span` context. The parent-span test will fail if you open it at module scope or before the fill span.

**Span helper:** You'll need to add `dungeon_materialize_mask_span` + `SPAN_DUNGEON_MATERIALIZE_MASK` constant + `SPAN_ROUTES` entry in `sidequest/telemetry/spans/dungeon_materialize.py`. Mirror the existing `dungeon_materialize_fill_span` helper pattern.

**RegionFill mutation:** Add `mask: RegionMask | None = None` as a defaulted field (preserves frozen+slots). The existing `_curate_inputs` helpers construct RegionFill without a mask — they'll keep working with the default None. `_stage_fill` will populate it as a non-None for every fill it produces (asserted by `test_emit_mask_attaches_region_mask_to_each_fill`).

**No-silent-fallback:** `_emit_mask([])` and `_emit_mask([[]])` must both raise `ValueError` with a message containing one of "empty"/"grid"/"cells".

**Handoff:** To Dev for GREEN phase.

## Design Deviations

(Agents append deviations below this line as they encounter spec drift during implementation.)

- No deviations yet.

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- No deviations from spec.

### TEA (verify)
- No deviations from spec.

### Architect (spec-check)
- **`_emit_mask` signature: `(grid: Grid)` instead of `(fill: RegionFill)`**
  - Spec source: sprint/context/context-story-52-2.md, "Code Changes" section, line 60
  - Spec text: "Add `_emit_mask(fill: RegionFill) -> RegionMask` helper function — Takes the `Grid` from `fill` and extracts the mask"
  - Implementation: `_emit_mask(grid: Grid) -> RegionMask` — takes `Grid` directly; called from `_stage_fill` after `generate_interior` returns the grid but BEFORE the `RegionFill` is constructed
  - Rationale: `RegionFill.mask` is the new field added in this story, so `RegionFill` now depends on `RegionMask`. Passing `RegionFill` into `_emit_mask` would create a chicken-and-egg construction order (build a half-populated `RegionFill` just to extract its grid, then re-construct with the mask). The narrower `Grid` input also makes `_emit_mask` testable in isolation. The spec's own clarifying text "Takes the Grid from fill" signals that the grid is the real input.
  - Severity: trivial
  - Forward impact: none — `_emit_mask` is module-private; no downstream code calls it directly

### Architect (reconcile)

- **OTEL span nests under `dungeon.materialize.fill`, not directly under `dungeon.materialize`**
  - Spec source: sprint/context/context-story-52-2.md, "Code Changes" section, line 67
  - Spec text: "Add child span `dungeon.materialize.mask` under the main `dungeon.materialize` span"
  - Implementation: The `dungeon.materialize.mask` span is opened inside the `for node in expansion.new_nodes` loop in `_stage_fill`, which itself runs inside the live `dungeon.materialize.fill` span context (`materializer.py:1792-1793`). OTEL's active-span context auto-parents, so the mask span becomes a **grandchild** of `dungeon.materialize` (parent = fill span), not a direct child.
  - Rationale: The mask emit is conceptually part of the fill stage's per-region work — it derives ADR-096 bytes from the just-generated grid. Nesting under the fill span (not the parent materialize span) accurately reflects the call hierarchy. The "child of main span" language in the spec was a simplification; the test `test_mask_span_nests_under_fill_span` (line 3807+) explicitly asserts the fill-span parentage, so this nesting is the locked, tested contract. The spec-check Architect Assessment noted this in passing ("the session's 'child span under main span' phrasing has been satisfied by a grandchild relationship that better reflects the call hierarchy") — formalizing it here as a proper deviation entry for the audit trail.
  - Severity: trivial
  - Forward impact: none — the span still appears in the `dungeon.materialize.*` subtree the GM panel renders; `SPAN_ROUTES` registration is unaffected; downstream stories (52-3/4/5) do not depend on the parent-span identity, only on the `mask_sha`/`grid_width`/`grid_height`/`cell_width` attributes which are routed identically regardless of parent.

### Architect (reconcile) — AC Accountability Verification

All 6 ACs DONE; no ACs deferred or descoped. Verified by cross-referencing Reviewer's per-AC rule-by-rule table against the story context AC list:

| AC | Status | Evidence |
|----|--------|----------|
| Mask emitted per region | DONE | `_stage_fill` line 744 calls `_emit_mask`; verified by `test_emit_mask_attaches_region_mask_to_each_fill` |
| Mask bytes are ASCII | DONE | `_MASK_WALL=b"#"`, `_MASK_FLOOR=b"."`, `_MASK_ROW_SEP=b"\n"` locked alphabet; verified by `test_emit_mask_bytes_are_ascii_walls_and_floors_only` |
| SHA256 computed | DONE | `mask_sha = hashlib.sha256(mask_bytes).hexdigest()` line 382; verified by `test_emit_mask_sha256_is_64_hex_lowercase_and_deterministic` |
| BlockInfo derived | DONE | `cell_width=ADR096_CELL_WIDTH=28`; verified by `test_block_info_cell_width_is_adr096_canonical_28` + `test_block_info_dimensions_match_source_grid` |
| OTEL span emitted | DONE | `dungeon_materialize_mask_span` per region with routed attrs + SPAN_ROUTES entry; verified by 3 tests (`test_dungeon_materialize_mask_span_emitted_per_region`, `test_mask_span_nests_under_fill_span`, `test_mask_span_routed_for_gm_panel`) |
| Non-test consumers | DONE | `test_mask_emit_fires_from_real_materialize_pipeline` drives real `materialize()` and asserts mask spans fire from the production path |

No AC deferral records found in the session — ac-completion gate did not flag any deferred ACs during Dev exit. All 6 ACs complete.

### Architect (reconcile) — Cross-Reference with Reviewer's Devil's-Advocate Notes

Reviewer flagged two **LOW** defense-in-depth concerns:
1. Ragged grid not validated (silent malformation on non-uniform rows)
2. `cell == WALL else FLOOR` fallthrough on unknown cell states

Neither is a deviation from spec — the spec didn't require these guards; both are future-hardening concerns. Per spec-reconcile scope, these are NOT logged as deviations. They are appropriately recorded in the Reviewer Assessment as future-hardening notes; a follow-up story can add them when a third cell state or non-uniform generator actually materializes.

### Architect (reconcile) — Forward Impact on Sibling Stories

Cross-referenced the implementation against the dependency chain 52-3 → 52-4 → 52-5 → 55-1:

- **52-3 (Persistence: mask-BLOB column + loader):** ✓ unblocked. `RegionMask.mask_bytes` is a `bytes` object directly writable to a `BLOB` column; `mask_sha` is the natural dedupe key for shared cavern-renderer cache rows.
- **52-4 (Server emits cavern PNG sidecar from runtime mask):** ✓ unblocked. The locked ASCII alphabet (`#`/`.`/`\n`) is straightforward to parse into a wall/floor matrix for PIL/Pillow rendering; `block.cell_width=28` provides the pixel multiplier.
- **52-5 (UI tactical grid wiring):** ✓ unblocked. `BlockInfo` provides `grid_width`/`grid_height` for canvas sizing and `cell_width=28` for token positioning; `mask_sha` doubles as the cavern_image_url cache key.
- **55-1 (Procedural Cavern Description+Manifest):** ✓ partially unblocked. 52-2's mask is necessary but not sufficient — 55-1 also depends on 52-3 (persistence) and 54-2/54-3 (manifest schema/validator). 52-2 closes its half of the gate.

Implementation enables every sibling story that listed 52-2 as a dependency. No forward-impact regressions.

## Dev Assessment

**Phase:** finish
**Status:** GREEN — all 12 RED tests now passing, no regressions in 303-test adjacent suite

### Files Changed

| File | Change |
|------|--------|
| `sidequest/dungeon/materializer.py` | Added `ADR096_CELL_WIDTH=28` constant, `BlockInfo`, `RegionMask` dataclasses, `_emit_mask(grid: Grid) -> RegionMask` helper; added defaulted `mask: RegionMask \| None = None` field to `RegionFill`; wired `_emit_mask` + `dungeon_materialize_mask_span` into `_stage_fill` per-region loop |
| `sidequest/telemetry/spans/dungeon_materialize.py` | Added `SPAN_DUNGEON_MATERIALIZE_MASK` constant, `SPAN_ROUTES` entry (lie-detector extractor surfaces region_id / grid_width / grid_height / cell_width / mask_sha), `dungeon_materialize_mask_span(...)` context-manager helper |

### Implementation Decisions

1. **`RegionMask.mask_bytes` format:** ASCII rows joined by `\n` (one byte per cell + newline between rows). The bytes are computed in one pass with a `bytearray` accumulator (no list-comprehension intermediate, no string concat). Wall = `#`, floor = `.`.
2. **`FLOOR` vs explicit `0` check:** The emit reads `cell == WALL` (single comparison). Ruff flagged the unused `FLOOR` import after the first draft; removed it. The fall-through is `_MASK_FLOOR` so anything-not-WALL becomes floor — matches the grid convention (only two cell states exist).
3. **Empty-grid guard:** `if not grid or not grid[0]` catches `[]`, `[[]]`, and `[[], [], ...]`. Single ValueError raised; the call site is inside `_stage_fill`'s `try/except ValueError` so the failure surfaces on the fill span automatically (same idiom the other fill failure modes already use).
4. **Span placement:** `dungeon_materialize_mask_span` opens INSIDE the `for node in expansion.new_nodes` loop, AFTER `_emit_mask` returns. That guarantees (a) the parent context is the live `dungeon.materialize.fill` span the existing helper opened upstream, and (b) the routed attributes carry the real `mask_sha` (computed) rather than a forward-declared placeholder. Body is `pass` — the span is a point-event marker, the mask object is the durable artifact.
5. **`RegionFill.mask` default `None`:** Preserves `_curate_inputs` / `_curate_inputs_two_regions` test helpers that construct `RegionFill` directly without going through fill. Production fills produced by `_stage_fill` always carry a non-None mask (asserted by `test_emit_mask_attaches_region_mask_to_each_fill`). No backward-compat shim — just a defaulted optional field.

### Test Results

| Suite | Result |
|-------|--------|
| `TestStageEmitMask` (11 tests) | 11 pass |
| `test_mask_emit_fires_from_real_materialize_pipeline` (wiring) | pass |
| `tests/dungeon/test_materializer.py` (full) + `test_materializer_wiring.py` + `tests/telemetry/` | 303 pass, 0 fail, 0 skip |

### Lint

`uv run ruff check sidequest/dungeon/materializer.py sidequest/telemetry/spans/dungeon_materialize.py` — all checks passed.

### Wiring Verification

The wiring test (`test_mask_emit_fires_from_real_materialize_pipeline`) drives the **real** `materialize()` coordinator with a real `DungeonStore`, real cookbook bundle, real palette + graph, and the project's `_reflecting_sdk_client` shim (the only mock — the curation subprocess). It asserts:
- `dungeon.materialize.mask` spans are present in the OTEL output
- Routed extractor returns `cell_width == 28`
- `mask_sha` is non-None
- `grid_width` / `grid_height` are integers

Mask spans fire from the production path, not from a test seam. Downstream stories (52-3 persistence, 52-4 PNG sidecar, 52-5 UI wiring) have a concrete `RegionMask` to consume.

**Handoff:** To TEA (Radar) for verify phase (simplify + quality-pass).

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned (one trivial signature deviation logged)
**Mismatches Found:** 1 (trivial)

### Mismatch 1 — `_emit_mask` signature

- **Category:** Different behavior (signature only — behavior identical)
- **Type:** Cosmetic
- **Severity:** Trivial
- **Spec:** Story context `Code Changes` section states "Add `_emit_mask(fill: RegionFill) -> RegionMask` helper function ... Takes the `Grid` from `fill` and extracts the mask"
- **Code:** `_emit_mask(grid: Grid) -> RegionMask` — takes the `Grid` directly
- **Recommendation:** **A — Update spec.** The code's choice is materially better. The fill stage builds the `grid` BEFORE constructing the `RegionFill`; passing the `Grid` directly avoids a forward-reference loop (`RegionFill` depends on `RegionMask` via its new field, so taking `RegionFill` would create a chicken-and-egg construction order). The narrower input also makes `_emit_mask` testable in isolation without manufacturing a full `RegionFill`. The spec's wording "Takes the Grid from fill" itself signals that the grid is the real input.

### AC Coverage Verification

| AC | Code Aligned? | Evidence |
|----|---------------|----------|
| Mask emitted per region | ✓ | `_stage_fill` line ~750: calls `_emit_mask(grid)` per `node in expansion.new_nodes` |
| Mask bytes are ASCII | ✓ | `_MASK_WALL = b"#"`, `_MASK_FLOOR = b"."`, `_MASK_ROW_SEP = b"\n"` — locked alphabet |
| SHA256 computed | ✓ | `hashlib.sha256(mask_bytes).hexdigest()` — derived from bytes, not fabricated |
| BlockInfo derived | ✓ | `cell_width=ADR096_CELL_WIDTH=28`, `grid_width=len(grid[0])`, `grid_height=len(grid)` |
| OTEL span emitted | ✓ | `dungeon_materialize_mask_span` opens inside fill loop with routed attrs; entry in `SPAN_ROUTES` |
| Non-test consumers | ✓ | `test_mask_emit_fires_from_real_materialize_pipeline` drives real `materialize()` coordinator; mask spans fire from production path |

### Architectural Soundness

- **Reuse-first compliance:** Implementation reuses the existing `Span.open` / `SPAN_ROUTES` / OTEL plumbing patterns mirroring `dungeon_materialize_fill_span` exactly. No new infrastructure. No new patterns. No new abstractions.
- **Frozen-dataclass discipline preserved:** `RegionMask` / `BlockInfo` / `RegionFill` all stay `frozen=True, slots=True` — the existing materializer value-object idiom.
- **No-Silent-Fallbacks compliance:** `_emit_mask` raises loudly on empty grid; the call site is inside the existing `try/except ValueError` so the failure surfaces on the fill span via the documented error-marker idiom — no new error path.
- **Constant placement:** `ADR096_CELL_WIDTH=28` is module-private to materializer.py for now, which is correct — no downstream consumer exists yet (52-3/4/5 will read `block.cell_width` from the `RegionMask`, not the constant directly).
- **OTEL span placement:** Nested inside `dungeon.materialize.fill` is the architecturally correct choice — the mask emit is conceptually part of the fill stage's work, not a peer stage. The session's "child span under main span" phrasing has been satisfied by a grandchild relationship that better reflects the call hierarchy.

### Forward Impact on 52-3 / 52-4 / 52-5

- **52-3 (persistence):** Has the `mask_bytes` (BLOB-writable) and `mask_sha` (dedupe key) ready to read off `RegionFill.mask`. The `RegionFill -> commit` thread will need work in 52-3 to actually persist; the data is now available where it wasn't before.
- **52-4 (PNG sidecar):** Has `mask_bytes` in the locked ASCII alphabet (`#`/`.`/`\n`) — straightforward to parse into a wall/floor matrix for PIL/Pillow rendering. `block.cell_width=28` is the px multiplier.
- **52-5 (UI tactical grid):** Has `BlockInfo` for token placement (`cell_width=28`, `grid_width`/`grid_height` for canvas sizing). The `mask_sha` doubles as the cavern image URL cache key.

**Decision:** Proceed to review. The single trivial signature deviation is logged below. No blocking findings.

## Technical Notes

### Data Model Shape

The materializer must produce:

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

### Integration Point

**File:** `sidequest/dungeon/materializer.py`

1. **Fill stage (stage 2 of 5):** After grid generation, emit the mask
2. **New function:** `_emit_mask(fill: RegionFill) -> RegionMask`
   - Extract grid from fill
   - ASCIIify the cell-state
   - Compute SHA256
   - Derive BlockInfo
3. **OTEL span:** `dungeon.materialize.mask` child span, logged with:
   - `grid_width` (int)
   - `grid_height` (int)
   - `cell_width` (int, typically 28)
   - `mask_sha` (str)

### Downstream Dependencies

- **52-3 (Persistence):** expects `RegionMask` with blob-writable `mask_bytes`
- **52-4 (PNG Sidecar):** expects `mask_sha` for deduplication + PNG generation
- **52-5 (UI Wiring):** expects `block` for token positioning, movement validation, AoE evaluation

### Key References

- **ADR-096 §2:** "Cell-stepped math is canonical. Tokens occupy one cell; movement is N cells per turn; reach is Chebyshev radius `speed/5`; AoE is evaluated cell-by-cell against the mask. The PNG is the visual; the mask is the truth."
- **ADR-106 §10 (spec item 6):** "Async look-ahead materializer, committed in one transaction"
- **Materializer docstring (line 56):** "Mask persistence is a documented Plan-5-API gap."
- **CLAUDE.md (OTEL Observability Principle):** "Every backend fix that touches a subsystem MUST add OTEL watcher events so the GM panel can verify the fix is working."

### No Silent Fallbacks

Per project CLAUDE.md:
- If grid has no cells → fail loudly, don't emit empty mask
- If ASCIIification fails → raise exception with context, don't skip
- If SHA256 fails → raise exception, don't use placeholder
- No fallback defaults; the mask is required truth for downstream stages

### Testing Strategy (RED Phase)

1. **Unit tests:** `test_materializer.py`
   - `test_emit_mask_ascii_format()` — verify wall/floor character set
   - `test_emit_mask_sha256_deterministic()` — same grid → same hash
   - `test_block_info_derived_correctly()` — cell_width, dimensions match
   - `test_full_materialization_includes_mask()` — mask is part of output

2. **OTEL wiring test:** `test_materializer_wiring.py`
   - Verify `dungeon.materialize.mask` span is emitted
   - Verify span attributes are set
   - Verify the span nests under `dungeon.materialize` parent

3. **Integration test (non-test consumer):**
   - Materializer invoked from real session lifecycle (not mocked)
   - Mask is accessible downstream to persistence/PNG stages

## References

- Epic 52 context: `/Users/slabgorb/Projects/oq-2/sprint/context/context-epic-52.md`
- Story context: `/Users/slabgorb/Projects/oq-2/sprint/context/context-story-52-2.md`
- Materializer docstring: `sidequest-server/sidequest/dungeon/materializer.py` lines 1–131
- ADR-096: `docs/adr/096-cavern-renderer-revival.md`
- ADR-106: `docs/adr/106-runtime-procedural-jaquaysed-megadungeon.md`

## TEA Assessment (verify phase)

**Phase:** finish
**Status:** GREEN confirmed; simplify-applied; ready for Reviewer

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 4 (`materializer.py`, `dungeon_materialize.py`, `test_materializer.py`, `test_materializer_wiring.py`)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 3 findings | OTEL boilerplate (high), palette/expansion (med), `_stage_fill` invocation pattern (med) — all dismissed: match existing sibling TestStageFill convention |
| simplify-quality | 3 findings | `BlockInfo`/`RegionMask` missing from `__all__` (med, applied); 2× local `SPAN_DUNGEON_MATERIALIZE_MASK` redefinition (low, applied) |
| simplify-efficiency | clean | No findings — single-pass bytearray accumulator over the grid; SHA-256 called once; no N+1 patterns |

**Applied:** 3 fixes (1 medium-confidence `__all__` export, 2 low-confidence import consolidations)
**Flagged for Review:** 0
**Noted as dismissed:** 3 (reuse — convention-match; explained below)
**Reverted:** 0

**Overall:** simplify: applied 3 fixes; 3 dismissed with rationale

#### Why the high-confidence reuse finding was dismissed

simplify-reuse flagged the OTEL setup pattern (`exporter, original_tracer_fn, _spans_mod = _setup_otel_task3(); try: ...; finally: _spans_mod.tracer = original_tracer_fn`) as repeated boilerplate across 7 of the 11 new tests with high confidence. Inspection of the sibling `TestStageFill` class (immediately above `TestStageEmitMask` in the same file) shows the SAME inline pattern repeated across ~8 of its tests (lines 944, 1011, 1044, 1079, 1113, 1149, 1176, 1209). Extracting a pytest fixture for only the new tests would create an inconsistency where half the file uses the fixture and the other half uses the inline pattern. The right resolution is a future module-wide refactor story, not a partial conversion in 52-2. Logged as a `# refactor candidate` opportunity for whoever next touches the materializer test suite at scope.

### Quality Checks

| Gate | Result |
|------|--------|
| `ruff check` on all 4 touched files | pass |
| `uv run pytest` (server full: 6484 tests) | pass, 396 skipped, 0 fail |
| Story-targeted: `TestStageEmitMask` + wiring test + `TestStageFill` + telemetry suite | 256 pass, 0 fail |
| `npm run lint` (sidequest-ui) | 1 pre-existing warning (App.tsx, outside 52-2 diff) |
| `npx tsc -b` (sidequest-ui) | **fails on external `~/Projects/dice-lib/src/DiceTray.tsx:11` — pre-existing, outside 52-2 diff, logged as a non-blocking Delivery Finding** |

The dice-lib TS error is in a sibling repo entirely outside `oq-2`/this story's scope. Story 52-2 is Python-only in `sidequest-server`. Reverting the simplify fixes would not change that (those touched only Python). No regression introduced by 52-2.

**Handoff:** To Reviewer (Colonel Potter) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 67 targeted tests pass, ruff clean, 0 code smells, 0 dead imports |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (`workflow.reviewer_subagents.edge_hunter=false`) — Reviewer covers manually |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — Reviewer covers manually (see [SILENT-MANUAL] in observations) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — Reviewer covers manually (TEA self-checked; tests have specific assertions) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — Reviewer reviewed docstrings inline |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — Reviewer covers (`frozen=True, slots=True` discipline preserved) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings — N/A surface: no user input, no I/O, no auth |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — verify-phase TEA already ran simplify trio with 3 dismissed (convention-match) + 3 applied |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — Reviewer enumerates python.md rules manually below |

**All received:** Yes (1 enabled subagent returned + 8 disabled-via-settings)
**Total findings:** 0 confirmed Critical/High, 2 LOW defense-in-depth notes (non-blocking), 0 dismissed-with-rationale, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVE

**Story 52-2 — Materializer emits ADR-096 mask + derived block per region**
3 commits ahead of develop, 4 files changed (+662 −1), 67 targeted tests pass, ruff clean, 6484-test server suite green.

### Rule Compliance (Python lang-review checklist, per `.pennyfarthing/gates/lang-review/python.md`)

Exhaustive enumeration of each numbered rule applied to the 52-2 diff:

| Rule | Code Element Checked | Verdict |
|------|---------------------|---------|
| **#1 Silent exception swallowing** | `_emit_mask` raises ValueError loudly (line 348-353); `_stage_fill`'s outer `try/except ValueError` catches and re-raises after `span.set_attribute("error", str(exc))` — the documented lie-detector idiom, never swallows | ✓ Compliant |
| **#2 Mutable default arguments** | `BlockInfo(origin_x: int = 0, origin_y: int = 0)` — ints are immutable; `RegionFill.mask: RegionMask \| None = None` — None is immutable | ✓ Compliant |
| **#3 Type annotations** | All new public surface fully annotated: `_emit_mask(grid: Grid) -> RegionMask`, all dataclass fields typed, helper `dungeon_materialize_mask_span` has full kwarg annotations + Iterator return type | ✓ Compliant |
| **#4 Logging** | No `logger.*` calls added; the OTEL `dungeon.materialize.mask` span IS the surface (per ADR-031 / CLAUDE.md "OTEL is the lie-detector") | ✓ Compliant — correct choice |
| **#5 Path handling** | N/A — no file paths in the diff | ✓ N/A |
| **#6 Test quality** | TEA self-checked; spot verified: `test_emit_mask_sha256_is_64_hex_lowercase_and_deterministic` uses `int(fill_a.mask.mask_sha, 16)` (raises on non-hex — meaningful), `test_block_info_cell_width_is_adr096_canonical_28` asserts `== 28` (specific), `test_empty_grid_raises_loudly_no_silent_fallback` uses `pytest.raises(ValueError, match="empty\|grid\|cells")` (specific exception + message). No `assert True`, no `let _ =`, no untargeted truthiness | ✓ Compliant |
| **#7 Resource leaks** | No `open()`, no `Session()`, no `sqlite3.connect()`, no `Lock()` in the new code. The `with dungeon_materialize_mask_span(...): pass` block IS a context manager — auto-cleanup | ✓ Compliant |
| **#8 Unsafe deserialization** | No `pickle`, no `yaml.load`, no `eval`, no `exec`, no `subprocess(shell=True)`, no untrusted `json.loads`. The only data crossing is the in-memory Grid → bytes | ✓ Compliant |
| **#9 Async pitfalls** | `_emit_mask` is sync. `_stage_fill` is sync. The span helper is sync. No async added; no `gather`, no `asyncio.sleep`, no blocking-in-async | ✓ Compliant |
| **#10 Import hygiene** | New imports are explicit (`WALL, Grid`, `dungeon_materialize_mask_span`, `SPAN_DUNGEON_MATERIALIZE_MASK`). `BlockInfo` and `RegionMask` added to `__all__`. No star imports. No new circular imports (verified — `_emit_mask` only depends on already-imported `hashlib`, `WALL`, `Grid`) | ✓ Compliant |
| **#11 Input validation** | `_emit_mask` validates non-empty grid loudly at line 348-353 (covers `[]`, `[[]]`, and `None` short-circuit). Input is internal-only (Grid from generator), but validation is still present | ✓ Compliant |
| **#12 Dependency hygiene** | No new deps. `hashlib` is stdlib | ✓ Compliant |
| **#13 Fix-introduced regressions** | N/A — initial implementation, not a fix | ✓ N/A |
| **#14 State cleanup ordering** | N/A — no one-shot queue/buffer + side-effect pattern | ✓ N/A |

**Project-specific rules (CLAUDE.md):**

| Rule | Verdict |
|------|---------|
| No Silent Fallbacks | ✓ Empty grid raises loudly; `cell == WALL else FLOOR` is the documented binary contract |
| No Stubbing | ✓ Full implementation; no placeholder shells |
| Don't Reinvent — Wire Up What Exists | ✓ Reuses existing `Span.open`, `SpanRoute`, `bytearray.extend`, `hashlib.sha256`; no new infrastructure |
| Verify Wiring | ✓ `test_mask_emit_fires_from_real_materialize_pipeline` drives `materialize()` end-to-end |
| Every Test Suite Needs a Wiring Test | ✓ Present at `test_materializer_wiring.py:307+` |
| OTEL Observability Principle | ✓ `dungeon.materialize.mask` span emitted per region, routed in `SPAN_ROUTES`, lie-detector attrs (region_id/grid_width/grid_height/cell_width/mask_sha) surfaced for GM panel |

### Observations

1. **[VERIFIED] No silent fallback on empty grid** — evidence: `_emit_mask` `materializer.py:347-353` raises `ValueError`; `_stage_fill` outer `except ValueError` `materializer.py:761-765` sets span error attribute then re-raises. Complies with CLAUDE.md "No Silent Fallbacks" rule.
2. **[VERIFIED] OTEL span nests correctly under fill stage** — evidence: `_stage_fill` is itself wrapped in `dungeon_materialize_fill_span` context at `materializer.py:1792`; the per-region loop body opens `dungeon_materialize_mask_span` at `materializer.py:744`. OTEL active-span context auto-parents. Confirmed at runtime by `test_mask_span_nests_under_fill_span` asserting `mask_span.parent.span_id == fill_span.context.span_id`.
3. **[VERIFIED] SHA-256 derived from bytes, not fabricated** — evidence: `materializer.py:382` computes `mask_sha = hashlib.sha256(mask_bytes).hexdigest()`; test at `test_materializer.py:3704+` recomputes `hashlib.sha256(fill_a.mask.mask_bytes).hexdigest()` independently and asserts equality.
4. **[VERIFIED] Grid identity preserved (no defensive copy)** — evidence: `materializer.py:388` returns `RegionMask(grid=grid, ...)` passing the same object; test at `test_materializer.py:3603-3606` asserts `fill.mask.grid is fill.grid` — locks the invariant against future "defensive copy" drift.
5. **[VERIFIED] `cell_width=28` is locked at constant, not derived** — evidence: `ADR096_CELL_WIDTH = 28` at `materializer.py:316`; `BlockInfo(cell_width=ADR096_CELL_WIDTH, ...)` at line 386. Test at `test_block_info_cell_width_is_adr096_canonical_28` exercises 4 generator types and asserts `cell_width == 28` for each.
6. **[VERIFIED] Wiring test exercises production path** — `test_mask_emit_fires_from_real_materialize_pipeline` at `test_materializer_wiring.py:319-388` calls the real `materialize()` coordinator with real `DungeonStore`, real cookbook bundle, real palette+graph; only mock is `_reflecting_sdk_client` (curation subprocess, the documented seam). Asserts via OTEL spans — never calls `_emit_mask` directly. Genuinely proves wiring per CLAUDE.md "Verify Wiring, Not Just Existence".
7. **[VERIFIED] `frozen=True, slots=True` discipline preserved** — `BlockInfo`, `RegionMask` both `@dataclass(frozen=True, slots=True)` at lines 320, 339. `RegionFill` keeps the same decorator. Test `test_region_fill_is_still_frozen_after_mask_field_added` asserts `pytest.raises(dataclasses.FrozenInstanceError)` on field reassignment.
8. **[VERIFIED] No tenant isolation needed** — single-tenant personal-project codebase; SOUL.md / CLAUDE.md has no tenant rules. The materializer operates on internally-generated grids; zero user input crosses the seam.
9. **[VERIFIED] Span span-route registration** — `SPAN_DUNGEON_MATERIALIZE_MASK` in `SPAN_ROUTES` at `dungeon_materialize.py:110-127`. Test `test_mask_span_routed_for_gm_panel` confirms registration + extractor component is `"dungeon"`. Prevents the Plan-7-Task-2 "set-but-not-routed" defect class.
10. **[LOW][SILENT-MANUAL] Ragged grid not validated** — `_emit_mask` derives `BlockInfo.grid_width=len(grid[0])` from row 0 only; if a future generator produces `[[0,0],[0]]` (ragged), the mask bytes would have row lengths 2+1 but `BlockInfo` would claim 2×2. The mask would be silently malformed without raising. **Why not blocking:** all current generators in `interiors/` (`braid.py`, `cellular.py`, `depthfirst.py`, `prim.py`, `roomcorridor.py`) produce uniform grids by construction (carve operations preserve dimensions); the input is internal-only; the determinism test would catch drift. Defense-in-depth would be a one-line `all(len(r) == len(grid[0]) for r in grid)` guard. Recommend tracking as a future hardening note, not blocking this PR.
11. **[LOW][SILENT-MANUAL] `cell == WALL else FLOOR` fallthrough on unknown cell states** — if a future generator introduces a third cell-state (door, water, lava), it would silently become floor in the mask. **Why not blocking:** the `Grid` type contract is binary today (`FLOOR=0`, `WALL=1` per `interiors/grid.py`); a third state would require a generator-side change that would surface at integration. Recommend a docstring note or an `assert cell in {FLOOR, WALL}` guard for future-proofing — but again, future-hardening, not 52-2-blocking.
12. **[OBS] `with dungeon_materialize_mask_span(...): pass` pattern** — `materializer.py:745-752` opens a context manager with an empty body. Looks unusual but is correct: the span needs `__enter__`/`__exit__` to fire (matches `dungeon_materialize_fill_span` and all sibling helpers — they're all `@contextmanager`). A short comment "point-event span; body intentionally empty" would aid future readers but isn't required.
13. **[OBS] `_make_request_task3` and `_reflecting_sdk_client` cross-imported from `tests.dungeon.test_materializer` into `test_materializer_wiring.py`** — existing pattern (`_attach_pack`, `_real_cookbook_bundle`, `_commit_palette`, `_seed_graph_themed`, `_fresh_snapshot`, `_otel_in_memory`, `_materialize_full` all already cross-imported pre-52-2). Not new debt; matches the established cross-test-file helper sharing convention.

### Tenant Isolation Audit

N/A — SideQuest is a single-tenant personal-project codebase. No SOUL.md tenant rules exist. Verified: no `TenantId` types, no `tenant_id` fields, no auth contexts referenced anywhere in the 52-2 diff.

### Devil's Advocate

What would a malicious user do? Story 52-2 has zero user-input surface — the grid is generated by deterministic seeded generators (`generate_interior`); the only consumers of `_emit_mask` are inside `_stage_fill`, never reachable from a network handler. Attack surface is empty. The mask bytes are never echoed back to a client unsanitized; they go to OTEL spans (operator-only) and (in 52-3, future) into a BLOB column.

What would a confused contributor break?

A future Dev could "defensively copy" the grid into `RegionMask.grid` to "protect against mutation". The `is fill.grid` identity assertion in `test_emit_mask_attaches_region_mask_to_each_fill` would catch it immediately. Good.

A future Dev could change `cell == WALL` to `cell != FLOOR` (or vice-versa). For the binary grid the behavior is identical, so no test would catch it. But if anyone adds a third cell state (a `DOOR=2` or `WATER=2`), the two formulations diverge silently. That's the `[LOW][SILENT-MANUAL] cell == WALL else FLOOR fallthrough` finding above — defense-in-depth recommendation, not a 52-2 blocker.

A future Dev could change `cell_width=28` to a config-driven value. The test asserts `== 28` for 4 generator types and would catch the regression. Good.

A future generator could produce a ragged grid (e.g., a half-completed cellular pass). `_emit_mask` would silently emit a malformed mask (rows of unequal lengths) while `BlockInfo` lies about the grid being uniform. The `mask_sha` would still be deterministic for the malformed bytes — downstream consumers (52-3/4/5) would propagate the malformation. That's the `[LOW][SILENT-MANUAL] Ragged grid` finding above. Defense-in-depth — track for hardening, not 52-2-blocking.

What happens if OTEL is misconfigured? `Span.open` is a hardened helper. If OTEL is broken, the span doesn't fire but the materializer still produces correct masks (the `mask` object is the durable artifact; the span is observability). ADR-006 graceful-degradation is preserved.

What happens if `hashlib.sha256` collides between regions? Different region_ids → different grids by determinism (different blake2b seeds → different cellular outputs). Pigeonhole says collision is astronomically improbable for 49×49 grids. And if two regions DO happen to produce identical grids → identical `mask_sha` is the **intended** dedupe behavior for 52-3 BLOB sharing.

What if `mask_bytes` is empty? Cannot happen — `_emit_mask` raises before reaching the bytearray construction if `not grid or not grid[0]`. The narrow guard window (grid is `[[1]]` — single 1-cell wall) still produces non-empty bytes (`b"#"`).

What if a contributor copy-pastes the `with ...: pass` pattern thinking it's a no-op and removes it? The mask span would never fire; the test `test_dungeon_materialize_mask_span_emitted_per_region` would fail. The lie-detector wiring test would also catch it. Good defense.

What if Python version changes `hashlib.sha256` output format? `hexdigest()` is spec-stable across CPython versions and platforms (always 64 lowercase hex chars). Test asserts both length and `int(sha, 16)` validity. Locked.

Conclusion: the devil's advocate found no critical issues, only the same two LOW defense-in-depth notes already flagged.

### Verdict Rationale

- 12 RED tests committed before implementation; all GREEN after.
- Full python.md rule checklist enumerated and verdict per rule documented.
- All 6 ACs from story context have direct test coverage.
- All 6 CLAUDE.md project rules (No Silent Fallbacks, No Stubbing, Don't Reinvent, Verify Wiring, Wiring Test, OTEL Observability) verified compliant.
- Wiring test drives the real production `materialize()` coordinator, not a stub.
- Two LOW defense-in-depth notes (ragged grid, third cell-state fallthrough) are recommendations for future hardening, not 52-2 blockers.
- Architect's spec-check passed with one trivial signature deviation (logged, rationale sound).
- TEA's verify-phase simplify trio: 3 fixes applied + 3 high/medium-confidence findings dismissed with sibling-convention rationale (which I concur with).
- Devil's advocate found no additional concerns.

**APPROVE.** Ready for merge to `develop`.

**Handoff:** To SM (Hawkeye) for finish ceremony — PR creation, merge to `develop`, archive session, complete story.