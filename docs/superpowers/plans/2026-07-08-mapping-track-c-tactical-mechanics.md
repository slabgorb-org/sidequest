# Track C: Tactical Mechanics (ADR-096 v2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn ADR-096's display-only tactical grid into *enforced* mechanics behind the ruleset seam: a pure adjudication library over ASCII masks (C1), Without-Number binding enforcement with OTEL and player-visible math (C2), and a Fate zone projection (C3). The mask is truth; enforcement lives in the `RulesetModule` binding, never in native combat code (ADR-117/143). C1/C2 run against **existing** cavern grids (`beneath_sunden` runtime caverns + static cavern rooms) with **no dependency on Track B**.

**Architecture:** A new pure `sidequest/game/tactical/` package holds cell math over the `#`/`.` mask string — no IO, no clock, no random (C1). The bound Without-Number ruleset module (`without_number.py`) supplies SRD-sourced movement/reach/range facts *once* (not per world) and calls the pure library from the confrontation-resolution chokepoint `dispatch_dice_throw` (C2). Durable per-actor cell positions live additively in `EncounterActor.per_actor_state['cell']`; dispatch outcomes update them. Every adjudication emits an OTEL span that reaches `turn_telemetry` via `publish_event` (the movement-span mirror pattern), and echoes onto additive protocol fields the UI renders as legible math. The Fate binding consumes the same grid coarsened into contiguous-cell-cluster zones (C3). The ADR-153 dogfight relative-position model is untouched.

**Tech Stack:** Python 3.12 / FastAPI / pydantic v2 (server, `uv`-managed); React 18 / TypeScript / Vitest (`sidequest-ui`). OTEL via `sidequest/telemetry/spans/` + `publish_event`. PostgreSQL (ADR-115) — but Track C adds **no** DDL (positions ride the already-persisted encounter; echoes are wire-only).

## Global Constraints

- **Repos & branch.** Work in `sidequest-server/` and `sidequest-ui/` (subrepos of `/Users/slabgorb/Projects/oq-3`). Branch off `develop`: `git checkout -b feat/mapping-track-c-tactical`. **Create the branch in its OWN Bash call before any commit** — the pf hook rejects `git commit` while on `develop`/`main` even in a compound command. Subrepo PRs target `develop`.
- **Test commands.** Server: `cd sidequest-server && uv run pytest <path> -v` (default `-n auto`). **OTEL span-count / span-sink tests must run `-n0`** (the `TracerProvider` is a process-global singleton; xdist workers contaminate span counts). Lint: `cd sidequest-server && uv run ruff check <touched files>`; format only touched files (`uv run ruff format <files>` — never bare `ruff format .`, it reformats ~167 files). UI: `cd sidequest-ui && npx vitest run <path>`.
- **TDD strictly.** Every task: failing test (complete code) → run (see it fail) → minimal impl (complete code) → run (see it pass) → commit. C1 is a PURE library (no IO, no snapshot, no random) — table-driven tests with property-ish edge cases (diagonals, walls, out-of-bounds, zero-budget). No placeholders anywhere; repeat code rather than say "similar to Task N".
- **Enforcement in the BINDING, not native code.** No new native combat rules. The WN module consumes exact cells; the Fate binding consumes zones. Movement/reach/range facts are authored ONCE on `WithoutNumberRulesetModule` (SRD-sourced), never re-derived per world (the flat-13 bug class). **Dogfight (ADR-153) is untouched.**
- **No-grid = no-grid rules (a scope boundary, NOT a silent fallback).** Enforcement fires only when both actors carry a `per_actor_state['cell']` (a tactical grid is active). When positions are absent (region-mode worlds, non-cavern scenes), combat resolves exactly as today and the seam emits `tactical.enforcement.skipped` (reason `no_grid`) so the GM panel sees the deliberate skip. This preserves all existing WN combat behaviour.
- **Wiring tests.** Every suite includes a wiring test proving production reachability (imported + called from a non-test path). C1's wiring test lives in the C2 enforcement task (the WN binding imports and calls the library from `dispatch_dice_throw`). No source-text greps as behaviour assertions — use OTEL-span / fixture-driven behaviour tests (CLAUDE.md "No Source-Text Wiring Tests"). UI suites include a MobileTabView reachability check where a tab is touched (none new here — enhance existing).
- **OTEL reaches `turn_telemetry`.** New spans (`tactical.move.validated`, `tactical.move.denied`, `tactical.aoe.cells`, `tactical.enforcement.skipped`, `tactical.positions.seated`, `tactical.zone.projected`, `tactical.zone.move`) MUST call `publish_event` (directly or via the `_mirror_*_to_sink` pattern in `spans/movement.py`) — a bare `Span.open` reaches Jaeger/live panel only, NOT the DB. Every new `SPAN_*` constant needs a `SPAN_ROUTES` entry or `FLAT_ONLY_SPANS` membership or `tests/telemetry/test_routing_completeness.py` fails.
- **Verify mechanics, never narration.** Verification steps assert spans/state/return values, not prose.
- **Additive protocol only.** All echo fields have empty defaults so Track B's `SITE_MAP` cutover cannot collide. `TACTICAL_GRID` keeps its shape and gains optional fields.
- **Known pre-existing failures (do not block on these):** ~13 server tests fail vs content `develop` (WWN migration); OTEL span-count tests need `-n0`; a stale `MessageType` count test (54-vs-55). Classify these pre-existing.

---

## Task 0: Branch setup (run once, before Task 1)

**Files:** none (git only).

**Interfaces:** produces the `feat/mapping-track-c-tactical` branch off `develop` in `sidequest-server`. The `sidequest-ui` work (Task 10) branches the same way when reached.

Steps:

- [ ] Confirm the server subrepo is on `develop` and clean: `cd sidequest-server && git branch --show-current && git status --short`.
- [ ] Create the feature branch **in its own Bash call** (the pf hook rejects a `git commit` issued while on `develop`/`main`, even inside a compound command that first checks out a branch): `cd sidequest-server && git checkout -b feat/mapping-track-c-tactical`.
- [ ] When Task 10 (UI) is reached, do the same in the UI subrepo: `cd sidequest-ui && git checkout -b feat/mapping-track-c-tactical` (its own Bash call, before the Task 10 commit).

---

## Task 1: C1 — pure module scaffold, mask parsing, Chebyshev distance

**Files:**
- Create `sidequest-server/sidequest/game/tactical/__init__.py`
- Create `sidequest-server/sidequest/game/tactical/adjudication.py` (this task: header + `Cell`, `parse_mask`, `in_bounds`, `is_floor`, `chebyshev_distance`, `neighbors`)
- Create `sidequest-server/tests/game/tactical/__init__.py`
- Create `sidequest-server/tests/game/tactical/test_adjudication_core.py`

**Interfaces:**
- Produces: `Cell = tuple[int, int]`; `parse_mask(mask: str) -> list[str]`; `in_bounds(rows: list[str], cell: Cell) -> bool`; `is_floor(rows: list[str], cell: Cell) -> bool`; `chebyshev_distance(a: Cell, b: Cell) -> int`; `neighbors(rows: list[str], cell: Cell) -> list[Cell]`.
- Consumes: nothing (pure). Mask shape matches `TacticalGridPayload.mask` (`'.'`=floor, `'#'`=wall, rows `\n`-joined; `sidequest/protocol/models.py:1317`).

Steps:

- [ ] Write the failing test file `tests/game/tactical/test_adjudication_core.py`:
```python
from sidequest.game.tactical.adjudication import (
    chebyshev_distance,
    in_bounds,
    is_floor,
    neighbors,
    parse_mask,
)

# 5x5: wall border, 3x3 floor interior, a wall pillar at (2,2).
MASK = "#####\n#...#\n#.#.#\n#...#\n#####"


def test_parse_mask_rows():
    rows = parse_mask(MASK)
    assert len(rows) == 5
    assert rows[0] == "#####"
    assert rows[1] == "#...#"


def test_is_floor_and_walls():
    rows = parse_mask(MASK)
    assert is_floor(rows, (1, 1))
    assert not is_floor(rows, (0, 0))  # wall
    assert not is_floor(rows, (2, 2))  # pillar
    assert not is_floor(rows, (9, 9))  # out of bounds


def test_in_bounds_edges():
    rows = parse_mask(MASK)
    assert in_bounds(rows, (0, 0))
    assert in_bounds(rows, (4, 4))
    assert not in_bounds(rows, (5, 0))
    assert not in_bounds(rows, (0, -1))


def test_chebyshev_diagonal_equals_orthogonal():
    assert chebyshev_distance((0, 0), (3, 0)) == 3
    assert chebyshev_distance((0, 0), (3, 3)) == 3  # diagonal same cost
    assert chebyshev_distance((1, 1), (1, 1)) == 0


def test_neighbors_excludes_walls_and_pillar():
    rows = parse_mask(MASK)
    ns = set(neighbors(rows, (1, 1)))
    assert (2, 1) in ns and (1, 2) in ns and (2, 2) not in ns  # pillar excluded
    assert (0, 0) not in ns  # wall excluded
    # centre-adjacent floor cell has the pillar removed from its 8 neighbours
    assert (2, 2) not in set(neighbors(rows, (3, 3)))
```
- [ ] Run: `cd sidequest-server && uv run pytest tests/game/tactical/test_adjudication_core.py -v` — expect **collection/import error** (module does not exist yet).
- [ ] Create `sidequest/game/tactical/__init__.py` (empty package marker — one line docstring only) and `tests/game/tactical/__init__.py` (empty).
- [ ] Create `sidequest/game/tactical/adjudication.py` with the minimal implementation:
```python
"""Pure tactical-grid adjudication over an ASCII mask (ADR-096 v2, Track C1).

The mask is truth: '#'=wall, '.'=floor, rows newline-separated (the
``TacticalGridPayload.mask`` shape). Every function is pure — no IO, no clock,
no random — and works in CELL units. The ruleset binding (Track C2/C3) supplies
the cell scale (metres per cell) and per-actor movement budgets; this library
never knows a ruleset. Coordinate convention matches ``dungeon/tactical.py`` and
the UI ``cellMath.ts``: cell = (x, y), x is column, y is row, origin top-left.
"""

from __future__ import annotations

Cell = tuple[int, int]

FLOOR_CHAR = "."
WALL_CHAR = "#"

_STEPS: tuple[Cell, ...] = (
    (1, 0), (-1, 0), (0, 1), (0, -1),
    (1, 1), (1, -1), (-1, 1), (-1, -1),
)


def parse_mask(mask: str) -> list[str]:
    """Split a newline mask into rows — the canonical grid form for this module."""
    return mask.split("\n")


def in_bounds(rows: list[str], cell: Cell) -> bool:
    x, y = cell
    return 0 <= y < len(rows) and 0 <= x < len(rows[y])


def is_floor(rows: list[str], cell: Cell) -> bool:
    """True iff ``cell`` is in-bounds and a floor ('.') cell."""
    if not in_bounds(rows, cell):
        return False
    x, y = cell
    return rows[y][x] == FLOOR_CHAR


def chebyshev_distance(a: Cell, b: Cell) -> int:
    """King-move distance: ``max(|dx|, |dy|)``. Diagonals cost as orthogonals."""
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def neighbors(rows: list[str], cell: Cell) -> list[Cell]:
    """The 8 king-move floor neighbours of ``cell`` (walls/off-map excluded)."""
    x, y = cell
    out: list[Cell] = []
    for dx, dy in _STEPS:
        n = (x + dx, y + dy)
        if is_floor(rows, n):
            out.append(n)
    return out
```
- [ ] Run: `cd sidequest-server && uv run pytest tests/game/tactical/test_adjudication_core.py -v` — expect **PASS**.
- [ ] Lint: `cd sidequest-server && uv run ruff check sidequest/game/tactical/ tests/game/tactical/` and `uv run ruff format sidequest/game/tactical/ tests/game/tactical/`.
- [ ] Commit:
```bash
cd sidequest-server
git add sidequest/game/tactical/__init__.py sidequest/game/tactical/adjudication.py tests/game/tactical/__init__.py tests/game/tactical/test_adjudication_core.py
git commit -m "feat(tactical): C1 pure grid module — mask parse, Chebyshev, neighbours"
```

---

## Task 2: C1 — movement (reachable flood + path cost)

**Files:**
- Modify `sidequest-server/sidequest/game/tactical/adjudication.py` (append `ReachResult`, `cells_reachable`, `movement_cost`, `MoveAdjudication`, `adjudicate_move`)
- Create `sidequest-server/tests/game/tactical/test_movement.py`

**Interfaces:**
- Produces: `ReachResult(reachable: frozenset[Cell], cost: dict[Cell, int])`; `cells_reachable(origin, budget, mask, *, difficult=frozenset()) -> ReachResult`; `movement_cost(path: list[Cell], mask, *, difficult=frozenset()) -> int | None`; `MoveAdjudication(valid, cells_spent, cells_budget, reason)`; `adjudicate_move(*, origin, path, budget_cells, mask, difficult=frozenset()) -> MoveAdjudication`.
- Consumes: `parse_mask`, `is_floor`, `neighbors`, `chebyshev_distance` (Task 1).

Steps:

- [ ] Write failing test `tests/game/tactical/test_movement.py`:
```python
from sidequest.game.tactical.adjudication import (
    adjudicate_move,
    cells_reachable,
    movement_cost,
)

# 1x7 corridor of floor between walls (row of ".", wall border top/bottom).
CORRIDOR = "#######\n#.....#\n#######"  # floor cells (1..5, row 1)
# 5x5 open room with wall pillar at (2,2).
ROOM = "#####\n#...#\n#.#.#\n#...#\n#####"


def test_reachable_budget_limits_distance():
    r = cells_reachable((1, 1), 2, CORRIDOR)
    assert (3, 1) in r.reachable  # 2 cells away
    assert (4, 1) not in r.reachable  # 3 cells away, over budget
    assert (1, 1) not in r.reachable  # origin excluded


def test_reachable_zero_budget_empty():
    assert cells_reachable((1, 1), 0, CORRIDOR).reachable == frozenset()


def test_reachable_walls_block():
    # Pillar at (2,2) is never reachable; open cells around it are.
    r = cells_reachable((1, 1), 4, ROOM)
    assert (2, 2) not in r.reachable
    assert (3, 3) in r.reachable


def test_reachable_difficult_terrain_doubles_cost():
    # Entering (3,1) is difficult -> costs 2, so with budget 2 you can still
    # stop on it, but (4,1) beyond it now costs 3 and is out of reach.
    r = cells_reachable((1, 1), 2, CORRIDOR, difficult=frozenset({(3, 1)}))
    assert r.cost[(2, 1)] == 1
    assert r.cost[(3, 1)] == 3  # 1 (to (2,1)) + 2 (enter difficult (3,1))
    assert (3, 1) not in r.reachable  # cost 3 > budget 2


def test_movement_cost_straight_and_diagonal():
    assert movement_cost([(1, 1), (2, 1), (3, 1)], ROOM) == 2
    assert movement_cost([(1, 1), (2, 1)], ROOM) == 1
    # diagonal step is one cell (Chebyshev)
    assert movement_cost([(1, 1), (2, 2)], "###\n#..\n#..") is None  # (2,2) wall in this mask


def test_movement_cost_rejects_non_adjacent_and_walls():
    assert movement_cost([(1, 1), (3, 1)], ROOM) is None  # jump, not adjacent
    assert movement_cost([(1, 1), (2, 2)], ROOM) is None  # (2,2) is the pillar (wall)
    assert movement_cost([(1, 1)], ROOM) == 0  # single floor cell = no move
    assert movement_cost([], ROOM) is None


def test_adjudicate_move_valid_and_denied():
    ok = adjudicate_move(origin=(1, 1), path=[(1, 1), (2, 1), (3, 1)], budget_cells=6, mask=ROOM)
    assert ok.valid and ok.cells_spent == 2 and ok.cells_budget == 6 and ok.reason == ""
    over = adjudicate_move(origin=(1, 1), path=[(1, 1), (2, 1), (3, 1)], budget_cells=1, mask=ROOM)
    assert not over.valid and over.cells_spent == 2 and "1 cell" in over.reason
    bad = adjudicate_move(origin=(1, 1), path=[(1, 1), (3, 1)], budget_cells=6, mask=ROOM)
    assert not bad.valid and bad.cells_spent == 0 and "path" in bad.reason.lower()
```
- [ ] Run: `cd sidequest-server && uv run pytest tests/game/tactical/test_movement.py -v` — expect **fail** (symbols missing).
- [ ] Append to `sidequest/game/tactical/adjudication.py` (add `from dataclasses import dataclass` to the top-of-file imports):
```python
@dataclass(frozen=True)
class ReachResult:
    """Cells an actor can stop on within a movement budget, plus min cost each."""

    reachable: frozenset[Cell]
    cost: dict[Cell, int]


def cells_reachable(
    origin: Cell,
    budget: int,
    mask: str,
    *,
    difficult: frozenset[Cell] = frozenset(),
) -> ReachResult:
    """Dijkstra flood over floor cells from ``origin`` honouring walls and a
    difficult-terrain set (entering a difficult cell costs 2, else 1). ``budget``
    is movement in cells. Zero/negative budget or a non-floor origin -> empty."""
    rows = parse_mask(mask)
    if budget <= 0 or not is_floor(rows, origin):
        return ReachResult(frozenset(), {})
    cost: dict[Cell, int] = {origin: 0}
    frontier: list[Cell] = [origin]
    while frontier:
        # Grids are room-scale; a linear min-scan is simplest and deterministic.
        frontier.sort(key=lambda c: cost[c])
        cur = frontier.pop(0)
        cur_cost = cost[cur]
        for n in neighbors(rows, cur):
            step = 2 if n in difficult else 1
            nc = cur_cost + step
            if nc <= budget and (n not in cost or nc < cost[n]):
                cost[n] = nc
                frontier.append(n)
    reachable = frozenset(c for c in cost if c != origin)
    return ReachResult(reachable, cost)


def movement_cost(
    path: list[Cell],
    mask: str,
    *,
    difficult: frozenset[Cell] = frozenset(),
) -> int | None:
    """Cost in cells of walking ``path`` (adjacent floor cells, origin first).
    ``None`` if empty, or any step is non-adjacent / off-floor. A single floor
    cell is a zero-cost no-move. Entering a difficult cell costs 2, else 1."""
    rows = parse_mask(mask)
    if not path:
        return None
    if len(path) == 1:
        return 0 if is_floor(rows, path[0]) else None
    total = 0
    for a, b in zip(path, path[1:]):
        if not is_floor(rows, a) or not is_floor(rows, b):
            return None
        if chebyshev_distance(a, b) != 1:
            return None
        total += 2 if b in difficult else 1
    return total


@dataclass(frozen=True)
class MoveAdjudication:
    """A ruleset-neutral verdict on one move. ``reason`` is '' when valid."""

    valid: bool
    cells_spent: int
    cells_budget: int
    reason: str


def adjudicate_move(
    *,
    origin: Cell,
    path: list[Cell],
    budget_cells: int,
    mask: str,
    difficult: frozenset[Cell] = frozenset(),
) -> MoveAdjudication:
    """Adjudicate ``path`` against ``budget_cells``. A malformed path is INVALID
    with cells_spent=0 and a legible reason; an over-budget path is INVALID and
    reports the real cost so the denial can read 'that is N cells, you can move
    M'. Never silently corrects."""
    if not path or path[0] != origin:
        return MoveAdjudication(False, 0, budget_cells, "move path must start at the actor's cell")
    cost = movement_cost(path, mask, difficult=difficult)
    if cost is None:
        return MoveAdjudication(False, 0, budget_cells, "illegal move path (crosses a wall or skips a cell)")
    if cost > budget_cells:
        return MoveAdjudication(
            False, cost, budget_cells,
            f"that move is {cost} cells; you can move {budget_cells} "
            f"cell{'s' if budget_cells != 1 else ''} this turn",
        )
    return MoveAdjudication(True, cost, budget_cells, "")
```
- [ ] Run: `cd sidequest-server && uv run pytest tests/game/tactical/test_movement.py -v` — expect **PASS**.
- [ ] Lint + format touched files, then commit:
```bash
cd sidequest-server
git add sidequest/game/tactical/adjudication.py tests/game/tactical/test_movement.py
git commit -m "feat(tactical): C1 movement — reachable flood, path cost, move adjudication"
```

---

## Task 3: C1 — reach, range, line-of-sight, AoE templates

**Files:**
- Modify `sidequest-server/sidequest/game/tactical/adjudication.py` (append `reach_cells`, `line_of_sight`, `RangeAdjudication`, `adjudicate_reach`, `aoe_burst`, `aoe_line`)
- Create `sidequest-server/tests/game/tactical/test_reach_range_aoe.py`

**Interfaces:**
- Produces: `reach_cells(origin, reach, mask) -> frozenset[Cell]`; `line_of_sight(a, b, mask) -> bool`; `RangeAdjudication(in_range, distance_cells, max_cells, mode, has_los, reason)`; `adjudicate_reach(*, origin, target, max_cells, mask, mode, require_los) -> RangeAdjudication`; `aoe_burst(center, radius, mask, *, require_los=True) -> frozenset[Cell]`; `aoe_line(origin, target, mask) -> frozenset[Cell]`.
- Consumes: `parse_mask`, `is_floor`, `chebyshev_distance` (Task 1).

Steps:

- [ ] Write failing test `tests/game/tactical/test_reach_range_aoe.py`:
```python
from sidequest.game.tactical.adjudication import (
    adjudicate_reach,
    aoe_burst,
    aoe_line,
    line_of_sight,
    reach_cells,
)

ROOM = "#####\n#...#\n#.#.#\n#...#\n#####"  # pillar wall at (2,2)
OPEN = "......\n......\n......\n......"  # 6x4 all floor
WALLED = "#######\n#..#..#\n#######"  # wall at (3,1) between (1,1) and (4,1)


def test_reach_cells_adjacent_only_at_reach_1():
    r = reach_cells((1, 1), 1, ROOM)
    assert (2, 1) in r and (1, 2) in r
    assert (3, 1) not in r  # 2 away
    assert (2, 2) not in r  # pillar (wall)
    assert (1, 1) not in r  # origin excluded


def test_reach_cells_zero_reach_empty():
    assert reach_cells((1, 1), 0, ROOM) == frozenset()


def test_line_of_sight_clear_and_blocked():
    assert line_of_sight((1, 1), (4, 1), OPEN) is True
    assert line_of_sight((1, 1), (4, 1), WALLED) is False  # wall at (3,1)


def test_adjudicate_reach_melee_in_and_out():
    hit = adjudicate_reach(origin=(1, 1), target=(2, 1), max_cells=1, mask=ROOM, mode="melee", require_los=False)
    assert hit.in_range and hit.distance_cells == 1 and hit.reason == ""
    miss = adjudicate_reach(origin=(1, 1), target=(3, 3), max_cells=1, mask=ROOM, mode="melee", require_los=False)
    assert not miss.in_range and miss.distance_cells == 2 and "reach" in miss.reason.lower()


def test_adjudicate_reach_ranged_requires_los():
    blocked = adjudicate_reach(origin=(1, 1), target=(4, 1), max_cells=40, mask=WALLED, mode="ranged", require_los=True)
    assert not blocked.in_range and blocked.has_los is False and "sight" in blocked.reason.lower()
    clear = adjudicate_reach(origin=(1, 1), target=(4, 1), max_cells=40, mask=OPEN, mode="ranged", require_los=True)
    assert clear.in_range and clear.has_los is True


def test_aoe_burst_radius_and_los_shadow():
    cells = aoe_burst((2, 1), 1, OPEN)
    assert (2, 1) in cells and (1, 1) in cells and (3, 1) in cells
    # a wall shadows cells behind it from the centre
    shadowed = aoe_burst((1, 1), 3, WALLED)
    assert (4, 1) not in shadowed  # behind the (3,1) wall


def test_aoe_line_stops_at_wall():
    line = aoe_line((1, 1), (5, 1), WALLED)
    assert (1, 1) in line and (2, 1) in line
    assert (4, 1) not in line  # ray stopped by the (3,1) wall
```
- [ ] Run: `cd sidequest-server && uv run pytest tests/game/tactical/test_reach_range_aoe.py -v` — expect **fail**.
- [ ] Append to `sidequest/game/tactical/adjudication.py`:
```python
def reach_cells(origin: Cell, reach: int, mask: str) -> frozenset[Cell]:
    """Floor cells within Chebyshev ``reach`` of ``origin`` (origin excluded).
    Reach is a radius, not a path — walls are excluded from the set but do not
    block (that is what LOS is for). Melee reach = 1."""
    if reach <= 0:
        return frozenset()
    rows = parse_mask(mask)
    ox, oy = origin
    out: set[Cell] = set()
    for y in range(oy - reach, oy + reach + 1):
        for x in range(ox - reach, ox + reach + 1):
            c = (x, y)
            if c != origin and is_floor(rows, c) and chebyshev_distance(origin, c) <= reach:
                out.add(c)
    return frozenset(out)


def _ray_cells(a: Cell, b: Cell) -> list[Cell]:
    """Bresenham cells from ``a`` to ``b`` inclusive (integer supercover-lite)."""
    x0, y0 = a
    x1, y1 = b
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    x, y = x0, y0
    cells = [(x, y)]
    while (x, y) != (x1, y1):
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy
        cells.append((x, y))
    return cells


def line_of_sight(a: Cell, b: Cell, mask: str) -> bool:
    """True iff no wall lies strictly between ``a`` and ``b`` on the ray.
    Endpoints are not tested (a token may stand at cover's edge); off-map is
    blocking."""
    rows = parse_mask(mask)
    ray = _ray_cells(a, b)
    for c in ray[1:-1]:
        if not is_floor(rows, c):
            return False
    return True


@dataclass(frozen=True)
class RangeAdjudication:
    """A ruleset-neutral verdict on whether ``target`` is attackable from
    ``origin``. ``mode`` is 'melee' | 'ranged'; ``reason`` is '' when in range."""

    in_range: bool
    distance_cells: int
    max_cells: int
    mode: str
    has_los: bool
    reason: str


def adjudicate_reach(
    *,
    origin: Cell,
    target: Cell,
    max_cells: int,
    mask: str,
    mode: str,
    require_los: bool,
) -> RangeAdjudication:
    """Adjudicate whether ``target`` is within ``max_cells`` (Chebyshev) and,
    when ``require_los``, has clear line of sight. Reports the real distance so
    a denial reads 'target is N cells away; your reach is M'. Never silently
    corrects."""
    dist = chebyshev_distance(origin, target)
    has_los = line_of_sight(origin, target, mask) if require_los else True
    if dist > max_cells:
        noun = "reach" if mode == "melee" else "range"
        return RangeAdjudication(
            False, dist, max_cells, mode, has_los,
            f"target is {dist} cells away; your {noun} is {max_cells}",
        )
    if require_los and not has_los:
        return RangeAdjudication(False, dist, max_cells, mode, has_los, "no line of sight to the target")
    return RangeAdjudication(True, dist, max_cells, mode, has_los, "")


def aoe_burst(center: Cell, radius: int, mask: str, *, require_los: bool = True) -> frozenset[Cell]:
    """Floor cells within Chebyshev ``radius`` of ``center``, LOS-gated from the
    centre (walls shadow cells behind them). ``center`` included when floor."""
    rows = parse_mask(mask)
    cx, cy = center
    out: set[Cell] = set()
    for y in range(cy - radius, cy + radius + 1):
        for x in range(cx - radius, cx + radius + 1):
            c = (x, y)
            if not is_floor(rows, c) or chebyshev_distance(center, c) > radius:
                continue
            if require_los and c != center and not line_of_sight(center, c, mask):
                continue
            out.add(c)
    return frozenset(out)


def aoe_line(origin: Cell, target: Cell, mask: str) -> frozenset[Cell]:
    """Floor cells along the ray origin->target until a wall stops it (the wall
    cell is excluded). A beam/line template."""
    rows = parse_mask(mask)
    out: set[Cell] = set()
    for c in _ray_cells(origin, target):
        if not is_floor(rows, c):
            break
        out.add(c)
    return frozenset(out)
```
- [ ] Run: `cd sidequest-server && uv run pytest tests/game/tactical/test_reach_range_aoe.py -v` — expect **PASS**. Run the whole C1 suite: `uv run pytest tests/game/tactical/ -v`.
- [ ] Lint + format, then commit:
```bash
cd sidequest-server
git add sidequest/game/tactical/adjudication.py tests/game/tactical/test_reach_range_aoe.py
git commit -m "feat(tactical): C1 reach, LOS raycast, range adjudication, AoE templates"
```

---

## Task 4: Position-as-combat-state — seed actor cells at confrontation seating

**Files:**
- Modify `sidequest-server/sidequest/game/encounter.py` (add a helper `seat_actor_cells` near `StructuredEncounter`; DO NOT add a field — use the existing `EncounterActor.per_actor_state`)
- Create `sidequest-server/sidequest/game/tactical/seating.py` (pure seat-mapping from `RegionTactical` anchors to actors)
- Create `sidequest-server/tests/game/tactical/test_seating.py`

**Interfaces:**
- Produces: `seat_actor_cells(encounter, anchors, *, player_side="player") -> dict[str, Cell]` — assigns entrance anchor to the first player-side actor, creature anchors to opponents in order, writes `actor.per_actor_state['cell'] = [x, y]`, returns the name→cell map. Idempotent (skips actors already carrying a cell). Pure over the passed anchors.
- Consumes: `EncounterActor.per_actor_state` (`sidequest/game/encounter.py:127`), `TokenAnchor` (`sidequest/dungeon/tactical.py:33`).
- Rationale: `per_actor_state` is the established home for per-actor spatial state (Fate `['zone']` slot, dogfight `['target_range']`); no schema/DDL change, resume-safe (rides the persisted encounter).

Steps:

- [ ] Write failing test `tests/game/tactical/test_seating.py`:
```python
from sidequest.dungeon.tactical import TokenAnchor
from sidequest.game.encounter import EncounterActor, EncounterMetric, StructuredEncounter
from sidequest.game.tactical.seating import seat_actor_cells


def _encounter():
    return StructuredEncounter(
        encounter_type="combat",
        player_metric=EncounterMetric(name="tension", threshold=10),
        opponent_metric=EncounterMetric(name="fear", threshold=10),
        actors=[
            EncounterActor(name="Rux", role="combatant", side="player"),
            EncounterActor(name="rope-spider", role="combatant", side="opponent"),
            EncounterActor(name="cave-bat", role="combatant", side="opponent"),
        ],
    )


ANCHORS = [
    TokenAnchor((1, 1), "entrance"),
    TokenAnchor((3, 1), "creature"),
    TokenAnchor((3, 3), "creature"),
]


def test_seats_players_on_entrance_opponents_on_creature_anchors():
    enc = _encounter()
    placed = seat_actor_cells(enc, ANCHORS)
    assert placed["Rux"] == (1, 1)
    assert placed["rope-spider"] == (3, 1)
    assert placed["cave-bat"] == (3, 3)
    assert enc.actors[0].per_actor_state["cell"] == [1, 1]
    assert enc.actors[1].per_actor_state["cell"] == [3, 1]


def test_idempotent_skips_already_seated():
    enc = _encounter()
    enc.actors[0].per_actor_state["cell"] = [4, 4]
    placed = seat_actor_cells(enc, ANCHORS)
    assert placed["Rux"] == (4, 4)  # not overwritten
    assert enc.actors[0].per_actor_state["cell"] == [4, 4]


def test_no_anchors_places_nothing():
    enc = _encounter()
    placed = seat_actor_cells(enc, [])
    assert placed == {}
    assert "cell" not in enc.actors[0].per_actor_state
```
- [ ] Run: `cd sidequest-server && uv run pytest tests/game/tactical/test_seating.py -v` — expect **fail**.
- [ ] Create `sidequest/game/tactical/seating.py`:
```python
"""Seat encounter actors onto tactical-grid cells (ADR-096 v2, Track C2).

Durable per-actor positions live in ``EncounterActor.per_actor_state['cell']``
(a ``[x, y]`` list — JSON-round-trippable, resume-safe via the persisted
encounter). Seeding maps the generator's ``RegionTactical`` anchors onto the
seated actors: the entrance anchor to the first player-side actor, creature
anchors to opponents in seating order. Idempotent — an actor already carrying a
cell keeps it (dispatch outcomes, not re-seating, move a token).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sidequest.dungeon.tactical import TokenAnchor
    from sidequest.game.encounter import StructuredEncounter

Cell = tuple[int, int]


def seat_actor_cells(
    encounter: StructuredEncounter,
    anchors: list[TokenAnchor],
    *,
    player_side: str = "player",
) -> dict[str, Cell]:
    """Assign cells to unseated actors and return the full name->cell map.

    Players draw the entrance anchor first (then spill to creature anchors);
    opponents/neutrals draw creature anchors in order. Actors already carrying a
    ``per_actor_state['cell']`` are left untouched and reported as-is. With no
    anchors, nothing is placed."""
    entrance = [a.cell for a in anchors if a.role == "entrance"]
    creature = [a.cell for a in anchors if a.role == "creature"]
    player_cells = entrance + creature
    opponent_cells = list(creature)

    placed: dict[str, Cell] = {}
    pi = oi = 0
    for actor in encounter.actors:
        existing = actor.per_actor_state.get("cell")
        if existing is not None:
            placed[actor.name] = (int(existing[0]), int(existing[1]))
            continue
        if actor.side == player_side:
            pool, idx = player_cells, pi
            pi += 1
        else:
            pool, idx = opponent_cells, oi
            oi += 1
        if idx < len(pool):
            cell = pool[idx]
            actor.per_actor_state["cell"] = [cell[0], cell[1]]
            placed[actor.name] = cell
    return placed
```
- [ ] Run: `cd sidequest-server && uv run pytest tests/game/tactical/test_seating.py -v` — expect **PASS**.
- [ ] Lint + format, then commit:
```bash
cd sidequest-server
git add sidequest/game/tactical/seating.py tests/game/tactical/test_seating.py
git commit -m "feat(tactical): C2 durable actor cells in per_actor_state via anchor seating"
```

---

## Task 5: C2 — Without-Number binding: SRD movement/reach/range facts + adjudication methods

**Files:**
- Modify `sidequest-server/sidequest/game/ruleset/without_number.py` (add tactical class attrs + `combat_move_cells`, `weapon_range_cells`, `adjudicate_tactical_move`, `adjudicate_tactical_reach` on `WithoutNumberRulesetModule`, `sidequest/game/ruleset/without_number.py:131`)
- Create `sidequest-server/tests/agents/ruleset/test_wn_tactical_binding.py`

**Interfaces:**
- Produces (on `WithoutNumberRulesetModule`): class attrs `METERS_PER_CELL: float = 1.5`, `DEFAULT_MOVE_METERS: int = 10`, `MELEE_REACH_CELLS: int = 1`, `RANGE_BAND_CELLS: dict[str, int]`; methods `combat_move_cells(core) -> int`, `weapon_range_cells(spec) -> tuple[str, int]`, `adjudicate_tactical_move(*, origin, path, core, mask, difficult=frozenset()) -> MoveAdjudication`, `adjudicate_tactical_reach(*, attacker_cell, target_cell, spec, mask) -> RangeAdjudication`.
- Consumes: `sidequest.game.tactical.adjudication.adjudicate_move` / `adjudicate_reach` (C1 — **this is C1's wiring into production**), `CreatureCore.move` (metres, `sidequest/game/creature_core.py:128`), `DamageSpec.range_band` when present else melee.
- **SRD grounding note:** `METERS_PER_CELL=1.5` is the ADR-096 5-ft/1.5-m cell. `DEFAULT_MOVE_METERS=10` is the WN SRD default Move (≈10 m) → `int(10/1.5)=6` cells, consistent with the UI's `speed/5` (30 ft ÷ 5). `core.move` (metres, mutant-stock overridable) supersedes when set — no per-world re-derivation. The `RANGE_BAND_CELLS` values are coarse SRD-derived caps: on a room-scale grid (~15–25 cells) pistol/rifle exceed the room, so **LOS is the binding ranged constraint** and the table bites only for `melee`/`thrown`/`shotgun`. See "Grounding limits" at the end for what to confirm against the SRD.

Steps:

- [ ] Write failing test `tests/agents/ruleset/test_wn_tactical_binding.py`:
```python
from types import SimpleNamespace

from sidequest.game.ruleset.registry import get_ruleset_module

ROOM = "#######\n#.....#\n#.....#\n#.....#\n#######"  # 5x3 floor interior


def _wn():
    return get_ruleset_module("wwn")


def test_combat_move_cells_default_and_override():
    wn = _wn()
    assert wn.combat_move_cells(SimpleNamespace(move=None)) == 6  # 10m / 1.5
    assert wn.combat_move_cells(SimpleNamespace(move=15)) == 10  # 15m / 1.5
    assert wn.combat_move_cells(None) == 6  # no core -> default


def test_weapon_range_cells_melee_and_ranged():
    wn = _wn()
    assert wn.weapon_range_cells(SimpleNamespace(range_band=None)) == ("melee", wn.MELEE_REACH_CELLS)
    assert wn.weapon_range_cells(SimpleNamespace(range_band="melee")) == ("melee", 1)
    mode, cells = wn.weapon_range_cells(SimpleNamespace(range_band="rifle"))
    assert mode == "ranged" and cells == wn.RANGE_BAND_CELLS["rifle"]


def test_adjudicate_tactical_move_uses_move_budget():
    wn = _wn()
    core = SimpleNamespace(move=None)  # 6 cells
    ok = wn.adjudicate_tactical_move(origin=(1, 1), path=[(1, 1), (2, 1), (3, 1)], core=core, mask=ROOM)
    assert ok.valid and ok.cells_spent == 2 and ok.cells_budget == 6
    slow = SimpleNamespace(move=1)  # 1m/1.5 -> max(1,0)=1 cell budget
    denied = wn.adjudicate_tactical_move(origin=(1, 1), path=[(1, 1), (2, 1), (3, 1)], core=slow, mask=ROOM)
    assert not denied.valid and "you can move 1 cell" in denied.reason


def test_adjudicate_tactical_reach_melee_out_of_reach():
    wn = _wn()
    spec = SimpleNamespace(range_band=None)  # melee reach 1
    verdict = wn.adjudicate_tactical_reach(attacker_cell=(1, 1), target_cell=(4, 1), spec=spec, mask=ROOM)
    assert not verdict.in_range and verdict.mode == "melee" and verdict.distance_cells == 3


def test_adjudicate_tactical_reach_ranged_los_gate():
    wn = _wn()
    spec = SimpleNamespace(range_band="rifle")
    verdict = wn.adjudicate_tactical_reach(attacker_cell=(1, 1), target_cell=(5, 3), spec=spec, mask=ROOM)
    assert verdict.in_range and verdict.mode == "ranged" and verdict.has_los
```
- [ ] Run: `cd sidequest-server && uv run pytest tests/agents/ruleset/test_wn_tactical_binding.py -v` — expect **fail**.
- [ ] Add to `WithoutNumberRulesetModule` in `sidequest/game/ruleset/without_number.py` (place after the `SRD_UNARMED_DICE` class attr, ~line 139):
```python
    # --- Tactical grid (ADR-096 v2, Track C2) --------------------------------
    # SRD-sourced, authored ONCE on the WN core; every sibling (swn/wwn/cwn/awn)
    # inherits. NOT per-world (the flat-13 re-derivation bug class).
    #: Metres per tactical cell — the ADR-096 5-ft / 1.5-m grid convention.
    METERS_PER_CELL: float = 1.5
    #: WN SRD default combat Move: a Move action covers ~10 m.
    DEFAULT_MOVE_METERS: int = 10
    #: Melee reach in cells (adjacent, incl. diagonal). SRD melee = 1 cell.
    MELEE_REACH_CELLS: int = 1
    #: SRD ranged band -> max cell distance. Room-scale grids (~15-25 cells) make
    #: LOS the binding ranged constraint; this table bites for short weapons.
    #: Confirm the exact figures against the WN SRD weapon range table.
    RANGE_BAND_CELLS: dict[str, int] = {
        "melee": 1, "thrown": 6, "shotgun": 8, "pistol": 20,
        "rifle": 40, "heavy": 60, "near": 6, "far": 40,
    }

    def combat_move_cells(self, core: object | None) -> int:
        """Per-turn Move budget in cells. Reads ``core.move`` (metres, mutant-
        stock overridable) or the SRD default; floors to cells, min 1."""
        move_m = getattr(core, "move", None) or self.DEFAULT_MOVE_METERS
        return max(1, int(move_m / self.METERS_PER_CELL))

    def weapon_range_cells(self, spec: object | None) -> tuple[str, int]:
        """('melee'|'ranged', max_cells) for a resolved weapon ``spec``. A None /
        'melee' band is melee reach; any other band is ranged (LOS-gated), capped
        by the SRD band table (defaulting to rifle for an unknown ranged band)."""
        band = getattr(spec, "range_band", None)
        if band is None or band == "melee":
            return ("melee", self.MELEE_REACH_CELLS)
        return ("ranged", self.RANGE_BAND_CELLS.get(band, self.RANGE_BAND_CELLS["rifle"]))

    def adjudicate_tactical_move(self, *, origin, path, core, mask, difficult=frozenset()):
        """Adjudicate one grid move against the actor's Move budget. Delegates to
        the pure C1 library (this is C1's production wiring)."""
        from sidequest.game.tactical.adjudication import adjudicate_move

        return adjudicate_move(
            origin=origin, path=path, budget_cells=self.combat_move_cells(core),
            mask=mask, difficult=difficult,
        )

    def adjudicate_tactical_reach(self, *, attacker_cell, target_cell, spec, mask):
        """Adjudicate whether ``target_cell`` is attackable from ``attacker_cell``
        with weapon ``spec``. Melee = adjacency; ranged = Chebyshev band + LOS.
        Delegates to the pure C1 library."""
        from sidequest.game.tactical.adjudication import adjudicate_reach

        mode, max_cells = self.weapon_range_cells(spec)
        return adjudicate_reach(
            origin=attacker_cell, target=target_cell, max_cells=max_cells,
            mask=mask, mode=mode, require_los=(mode == "ranged"),
        )
```
- [ ] Run: `cd sidequest-server && uv run pytest tests/agents/ruleset/test_wn_tactical_binding.py -v` — expect **PASS**.
- [ ] Lint + format, then commit:
```bash
cd sidequest-server
git add sidequest/game/ruleset/without_number.py tests/agents/ruleset/test_wn_tactical_binding.py
git commit -m "feat(tactical): C2 WN binding — SRD move/reach/range facts + adjudicators over C1"
```

---

## Task 6: C2 — OTEL spans that reach turn_telemetry

**Files:**
- Create `sidequest-server/sidequest/telemetry/spans/tactical.py`
- Modify `sidequest-server/sidequest/telemetry/spans/__init__.py` (add `from .tactical import *`, `sidequest/telemetry/spans/__init__.py:9-13`)
- Create `sidequest-server/tests/telemetry/test_tactical_telemetry_sink.py`

**Interfaces:**
- Produces span constants `SPAN_TACTICAL_MOVE_VALIDATED = "tactical.move.validated"`, `SPAN_TACTICAL_MOVE_DENIED = "tactical.move.denied"`, `SPAN_TACTICAL_AOE_CELLS = "tactical.aoe.cells"`, `SPAN_TACTICAL_ENFORCEMENT_SKIPPED = "tactical.enforcement.skipped"`, `SPAN_TACTICAL_POSITIONS_SEATED = "tactical.positions.seated"`; context-manager helpers `tactical_move_validated_span(...)`, `tactical_move_denied_span(...)`, `tactical_aoe_cells_span(...)`, `tactical_enforcement_skipped_span(...)`, `tactical_positions_seated_span(...)`; each registers a `SpanRoute` and mirrors to the sink via `publish_event`.
- Consumes: `Span.open` (`sidequest/telemetry/spans/span.py:17`), `SPAN_ROUTES`/`SpanRoute` (`sidequest/telemetry/spans/_core.py:22,44`), `publish_event` (`sidequest/telemetry/watcher_hub.py:712`). Pattern copied verbatim from `spans/movement.py` (`_mirror_movement_span_to_sink`, `movement.py:151`) so spans reach `turn_telemetry`, not just Jaeger.

Steps:

- [ ] Write failing test `tests/telemetry/test_tactical_telemetry_sink.py`:
```python
"""tactical.* spans must MIRROR into the turn_telemetry sink (publish_event),
not just open a Jaeger span. Model: tests/telemetry/test_movement_telemetry_sink.py.
Run with -n0 (span globals are process-shared)."""

from __future__ import annotations

import sidequest.telemetry.spans.tactical as tac


def test_move_validated_mirrors_to_sink(monkeypatch):
    published: list[tuple] = []
    monkeypatch.setattr(tac, "publish_event", lambda et, fields, **kw: published.append((et, fields, kw)))
    with tac.tactical_move_validated_span(actor="Rux", cells_spent=2, cells_budget=6, from_cell=(1, 1), to_cell=(3, 1)):
        pass
    assert published, "tactical.move.validated did not mirror into the turn_telemetry sink"
    et, fields, kw = published[0]
    assert et == "state_transition"
    assert kw["component"] == "tactical"
    assert fields["op"] == "tactical.move.validated"
    assert fields["cells_spent"] == 2 and fields["cells_budget"] == 6


def test_move_denied_mirrors_and_carries_reason(monkeypatch):
    published: list[tuple] = []
    monkeypatch.setattr(tac, "publish_event", lambda et, fields, **kw: published.append((et, fields, kw)))
    with tac.tactical_move_denied_span(actor="Rux", cells_spent=5, cells_budget=1, reason="that move is 5 cells; you can move 1 cell"):
        pass
    assert published, "tactical.move.denied did not mirror to sink"
    _, fields, _ = published[0]
    assert fields["op"] == "tactical.move.denied" and "5 cells" in fields["reason"]


def test_aoe_cells_mirrors(monkeypatch):
    published: list[tuple] = []
    monkeypatch.setattr(tac, "publish_event", lambda et, fields, **kw: published.append((et, fields, kw)))
    with tac.tactical_aoe_cells_span(actor="Rux", template="burst", cell_count=5, radius=1):
        pass
    assert published and published[0][1]["op"] == "tactical.aoe.cells"
    assert published[0][1]["cell_count"] == 5


def test_every_tactical_span_routed():
    from sidequest.telemetry.spans import SPAN_ROUTES
    for name in (
        tac.SPAN_TACTICAL_MOVE_VALIDATED, tac.SPAN_TACTICAL_MOVE_DENIED,
        tac.SPAN_TACTICAL_AOE_CELLS, tac.SPAN_TACTICAL_ENFORCEMENT_SKIPPED,
        tac.SPAN_TACTICAL_POSITIONS_SEATED,
    ):
        assert name in SPAN_ROUTES, f"{name} missing SPAN_ROUTES entry"
```
- [ ] Run: `cd sidequest-server && uv run pytest tests/telemetry/test_tactical_telemetry_sink.py -v -n0` — expect **fail**.
- [ ] Create `sidequest/telemetry/spans/tactical.py`:
```python
"""Tactical-grid adjudication spans (ADR-096 v2, Track C2).

The GM panel is the lie detector: every grid adjudication must be provably
engaged vs improvised. These spans mirror into the turn_telemetry sink via
``publish_event`` (the ``spans/movement.py`` pattern) so a firing engine does
not read as DEAD in saves — a bare ``Span.open`` reaches only Jaeger/live panel.
"""

from __future__ import annotations

import json as _json
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace

from sidequest.telemetry.watcher_hub import publish_event

from ._core import SPAN_ROUTES, SpanRoute
from .span import Span

SPAN_TACTICAL_MOVE_VALIDATED = "tactical.move.validated"
SPAN_TACTICAL_MOVE_DENIED = "tactical.move.denied"
SPAN_TACTICAL_AOE_CELLS = "tactical.aoe.cells"
SPAN_TACTICAL_ENFORCEMENT_SKIPPED = "tactical.enforcement.skipped"
SPAN_TACTICAL_POSITIONS_SEATED = "tactical.positions.seated"


def _attr(field: str):
    return lambda span, f=field: (span.attributes or {}).get(f)


SPAN_ROUTES[SPAN_TACTICAL_MOVE_VALIDATED] = SpanRoute(
    event_type="state_transition",
    component="tactical",
    extract=lambda s: {
        "field": "encounter", "op": "tactical.move.validated",
        "actor": _attr("actor")(s), "cells_spent": _attr("cells_spent")(s),
        "cells_budget": _attr("cells_budget")(s),
        "from_cell": _attr("from_cell")(s), "to_cell": _attr("to_cell")(s),
    },
)
SPAN_ROUTES[SPAN_TACTICAL_MOVE_DENIED] = SpanRoute(
    event_type="state_transition",
    component="tactical",
    extract=lambda s: {
        "field": "encounter", "op": "tactical.move.denied",
        "actor": _attr("actor")(s), "cells_spent": _attr("cells_spent")(s),
        "cells_budget": _attr("cells_budget")(s), "reason": _attr("reason")(s),
    },
)
SPAN_ROUTES[SPAN_TACTICAL_AOE_CELLS] = SpanRoute(
    event_type="state_transition",
    component="tactical",
    extract=lambda s: {
        "field": "encounter", "op": "tactical.aoe.cells",
        "actor": _attr("actor")(s), "template": _attr("template")(s),
        "cell_count": _attr("cell_count")(s), "radius": _attr("radius")(s),
        "cells_json": _attr("cells_json")(s),
    },
)
SPAN_ROUTES[SPAN_TACTICAL_ENFORCEMENT_SKIPPED] = SpanRoute(
    event_type="state_transition",
    component="tactical",
    extract=lambda s: {
        "field": "encounter", "op": "tactical.enforcement.skipped",
        "actor": _attr("actor")(s), "reason": _attr("reason")(s),
    },
)
SPAN_ROUTES[SPAN_TACTICAL_POSITIONS_SEATED] = SpanRoute(
    event_type="state_transition",
    component="tactical",
    extract=lambda s: {
        "field": "encounter", "op": "tactical.positions.seated",
        "seated_count": _attr("seated_count")(s), "room_id": _attr("room_id")(s),
    },
)


def _mirror(span_name: str, span: trace.Span) -> None:
    """Mirror a finished tactical span into the turn_telemetry sink. Skips
    silently for a NonRecordingSpan (no ``attributes``) — a telemetry side
    channel must never crash an adjudication (mirrors ``movement.py``)."""
    route = SPAN_ROUTES.get(span_name)
    if route is None or not hasattr(span, "attributes"):
        return
    publish_event(route.event_type, route.extract(span), component=route.component)


@contextmanager
def tactical_move_validated_span(
    *, actor: str, cells_spent: int, cells_budget: int,
    from_cell: tuple[int, int], to_cell: tuple[int, int],
    _tracer: trace.Tracer | None = None, **attrs: Any,
) -> Iterator[trace.Span]:
    with Span.open(
        SPAN_TACTICAL_MOVE_VALIDATED,
        {"actor": actor, "cells_spent": cells_spent, "cells_budget": cells_budget,
         "from_cell": list(from_cell), "to_cell": list(to_cell), **attrs},
        tracer_override=_tracer,
    ) as span:
        yield span
    _mirror(SPAN_TACTICAL_MOVE_VALIDATED, span)


@contextmanager
def tactical_move_denied_span(
    *, actor: str, cells_spent: int, cells_budget: int, reason: str,
    _tracer: trace.Tracer | None = None, **attrs: Any,
) -> Iterator[trace.Span]:
    from opentelemetry.trace import Status, StatusCode

    with Span.open(
        SPAN_TACTICAL_MOVE_DENIED,
        {"actor": actor, "cells_spent": cells_spent, "cells_budget": cells_budget,
         "reason": reason, **attrs},
        tracer_override=_tracer,
    ) as span:
        span.set_status(Status(StatusCode.ERROR, reason))
        yield span
    _mirror(SPAN_TACTICAL_MOVE_DENIED, span)


@contextmanager
def tactical_aoe_cells_span(
    *, actor: str, template: str, cell_count: int, radius: int,
    cells: list[tuple[int, int]] | None = None,
    _tracer: trace.Tracer | None = None, **attrs: Any,
) -> Iterator[trace.Span]:
    with Span.open(
        SPAN_TACTICAL_AOE_CELLS,
        {"actor": actor, "template": template, "cell_count": cell_count,
         "radius": radius, "cells_json": _json.dumps([list(c) for c in (cells or [])]), **attrs},
        tracer_override=_tracer,
    ) as span:
        yield span
    _mirror(SPAN_TACTICAL_AOE_CELLS, span)


@contextmanager
def tactical_enforcement_skipped_span(
    *, actor: str, reason: str, _tracer: trace.Tracer | None = None, **attrs: Any,
) -> Iterator[trace.Span]:
    with Span.open(
        SPAN_TACTICAL_ENFORCEMENT_SKIPPED,
        {"actor": actor, "reason": reason, **attrs},
        tracer_override=_tracer,
    ) as span:
        yield span
    _mirror(SPAN_TACTICAL_ENFORCEMENT_SKIPPED, span)


@contextmanager
def tactical_positions_seated_span(
    *, seated_count: int, room_id: str, _tracer: trace.Tracer | None = None, **attrs: Any,
) -> Iterator[trace.Span]:
    with Span.open(
        SPAN_TACTICAL_POSITIONS_SEATED,
        {"seated_count": seated_count, "room_id": room_id, **attrs},
        tracer_override=_tracer,
    ) as span:
        yield span
    _mirror(SPAN_TACTICAL_POSITIONS_SEATED, span)


__all__ = [
    "SPAN_TACTICAL_AOE_CELLS", "SPAN_TACTICAL_ENFORCEMENT_SKIPPED",
    "SPAN_TACTICAL_MOVE_DENIED", "SPAN_TACTICAL_MOVE_VALIDATED",
    "SPAN_TACTICAL_POSITIONS_SEATED",
    "tactical_aoe_cells_span", "tactical_enforcement_skipped_span",
    "tactical_move_denied_span", "tactical_move_validated_span",
    "tactical_positions_seated_span",
]
```
- [ ] Add `from .tactical import *  # noqa: F401,F403` to `sidequest/telemetry/spans/__init__.py` alongside the other `from .<domain> import *` lines.
- [ ] Run: `cd sidequest-server && uv run pytest tests/telemetry/test_tactical_telemetry_sink.py tests/telemetry/test_routing_completeness.py -v -n0` — expect **PASS** (routing-completeness confirms every new `SPAN_*` is routed).
- [ ] Lint + format, then commit:
```bash
cd sidequest-server
git add sidequest/telemetry/spans/tactical.py sidequest/telemetry/spans/__init__.py tests/telemetry/test_tactical_telemetry_sink.py
git commit -m "feat(tactical): C2 OTEL — tactical.* spans mirrored into turn_telemetry"
```

---

## Task 7: C2 — wire reach enforcement into dispatch_dice_throw + seat positions

**Files:**
- Modify `sidequest-server/sidequest/server/dispatch/dice.py` (add a reach gate helper `_enforce_tactical_reach` and call it in `dispatch_dice_throw` after target resolution `dice.py:577-586`, before `apply_beat`; seat positions once when the encounter first has a grid)
- Create `sidequest-server/tests/server/dispatch/test_dice_tactical_enforcement.py`

**Interfaces:**
- Produces: `_enforce_tactical_reach(*, ruleset, encounter, actor, target_name, spec, mask, snapshot, tracer=None) -> RangeAdjudication | None` — returns `None` (no enforcement, emit `tactical.enforcement.skipped`) when either actor lacks a `per_actor_state['cell']` or `mask` is None; otherwise runs `ruleset.adjudicate_tactical_reach`, emits `tactical.move.validated` (in-range) or `tactical.move.denied` (out-of-range), and returns the verdict. On a denied verdict the caller aborts the strike with a legible refusal — never silently corrected.
- Consumes: `WithoutNumberRulesetModule.adjudicate_tactical_reach` (Task 5); `EncounterActor.per_actor_state['cell']` (Task 4); `spans/tactical.py` helpers (Task 6); the resolved `mask` (loaded from the room's tactical grid — the enforcement is a no-op when absent). The seam objects (`encounter`, `actor`, `beat`, `snapshot`, resolved `spec` via `resolve_damage`) are all in scope at `dice.py:577-586` per the grounding.
- **Ruleset gate:** only fire for a `WithoutNumberRulesetModule` binding (`isinstance(ruleset, WithoutNumberRulesetModule)`, the capability-gate doctrine of ADR-117's 2026-06-05 amendment) — never on dial/Fate. Fate zone movement is C3.

Steps:

- [ ] Write failing handler test `tests/server/dispatch/test_dice_tactical_enforcement.py`. Use the intent-router autouse stub (already active via `tests/server/conftest.py:493`) so the router does not flake; drive `_enforce_tactical_reach` directly with a synthetic encounter (unit-level, no live turn) plus one end-to-end assertion that the denied verdict blocks the strike:
```python
"""Reach enforcement in dispatch_dice_throw. Unit-drives _enforce_tactical_reach
with synthetic actors carrying per_actor_state['cell']; asserts spans + verdict.
Intent-router is stubbed by the autouse conftest fixture."""

from __future__ import annotations

from types import SimpleNamespace

from sidequest.game.encounter import EncounterActor, EncounterMetric, StructuredEncounter
from sidequest.game.ruleset.registry import get_ruleset_module
from sidequest.server.dispatch.dice import _enforce_tactical_reach

ROOM = "#######\n#.....#\n#.....#\n#.....#\n#######"


def _combat(attacker_cell, target_cell):
    a = EncounterActor(name="Rux", role="combatant", side="player",
                       per_actor_state={"cell": list(attacker_cell)})
    t = EncounterActor(name="rope-spider", role="combatant", side="opponent",
                       per_actor_state={"cell": list(target_cell)})
    return StructuredEncounter(
        encounter_type="combat",
        player_metric=EncounterMetric(name="tension", threshold=10),
        opponent_metric=EncounterMetric(name="fear", threshold=10),
        actors=[a, t],
    )


def test_melee_in_reach_returns_valid_verdict():
    enc = _combat((1, 1), (2, 1))
    verdict = _enforce_tactical_reach(
        ruleset=get_ruleset_module("wwn"), encounter=enc, actor=enc.actors[0],
        target_name="rope-spider", spec=SimpleNamespace(range_band=None),
        mask=ROOM, snapshot=None,
    )
    assert verdict is not None and verdict.in_range


def test_melee_out_of_reach_returns_denied_verdict():
    enc = _combat((1, 1), (5, 3))
    verdict = _enforce_tactical_reach(
        ruleset=get_ruleset_module("wwn"), encounter=enc, actor=enc.actors[0],
        target_name="rope-spider", spec=SimpleNamespace(range_band=None),
        mask=ROOM, snapshot=None,
    )
    assert verdict is not None and not verdict.in_range and "reach" in verdict.reason.lower()


def test_no_grid_skips_enforcement():
    # Actors without a cell -> no grid -> enforcement is a deliberate no-op.
    enc = StructuredEncounter(
        encounter_type="combat",
        player_metric=EncounterMetric(name="tension", threshold=10),
        opponent_metric=EncounterMetric(name="fear", threshold=10),
        actors=[EncounterActor(name="Rux", role="combatant", side="player"),
                EncounterActor(name="rope-spider", role="combatant", side="opponent")],
    )
    verdict = _enforce_tactical_reach(
        ruleset=get_ruleset_module("wwn"), encounter=enc, actor=enc.actors[0],
        target_name="rope-spider", spec=SimpleNamespace(range_band=None),
        mask=None, snapshot=None,
    )
    assert verdict is None  # None == enforcement skipped (combat proceeds as today)


def test_dial_ruleset_not_enforced():
    enc = _combat((1, 1), (5, 3))
    verdict = _enforce_tactical_reach(
        ruleset=get_ruleset_module("dial"), encounter=enc, actor=enc.actors[0],
        target_name="rope-spider", spec=SimpleNamespace(range_band=None),
        mask=ROOM, snapshot=None,
    )
    assert verdict is None  # only WN bindings enforce the grid
```
- [ ] Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_dice_tactical_enforcement.py -v` — expect **fail** (`_enforce_tactical_reach` missing).
- [ ] Add `_enforce_tactical_reach` to `sidequest/server/dispatch/dice.py` (near the other module-level helpers) and call it inside `dispatch_dice_throw` right after `target_core`/`target_name` are resolved (~`dice.py:577-586`) and before the strike applies:
```python
def _enforce_tactical_reach(
    *, ruleset, encounter, actor, target_name, spec, mask, snapshot, tracer=None
):
    """Gate a strike on grid reach/range when a tactical grid is active.

    Returns the RangeAdjudication verdict (in_range True/False), or None when
    enforcement is deliberately skipped: a non-WN ruleset, a missing mask, or
    either actor lacking a per_actor_state['cell']. A skip emits
    ``tactical.enforcement.skipped`` (NOT a silent fallback — the GM panel sees
    the deliberate no-grid boundary). An in-range verdict emits
    ``tactical.move.validated``; an out-of-range verdict emits
    ``tactical.move.denied`` and the caller aborts the strike with the legible
    ``verdict.reason`` (never silently retargets/corrects)."""
    from sidequest.game.ruleset.without_number import WithoutNumberRulesetModule
    from sidequest.telemetry.spans.tactical import (
        tactical_enforcement_skipped_span,
        tactical_move_denied_span,
        tactical_move_validated_span,
    )

    if not isinstance(ruleset, WithoutNumberRulesetModule):
        return None
    target = encounter.find_actor(target_name)
    a_cell = actor.per_actor_state.get("cell")
    t_cell = target.per_actor_state.get("cell") if target is not None else None
    if mask is None or a_cell is None or t_cell is None:
        with tactical_enforcement_skipped_span(actor=actor.name, reason="no_grid", _tracer=tracer):
            pass
        return None

    verdict = ruleset.adjudicate_tactical_reach(
        attacker_cell=(int(a_cell[0]), int(a_cell[1])),
        target_cell=(int(t_cell[0]), int(t_cell[1])),
        spec=spec, mask=mask,
    )
    if verdict.in_range:
        with tactical_move_validated_span(
            actor=actor.name, cells_spent=0, cells_budget=verdict.max_cells,
            from_cell=(int(a_cell[0]), int(a_cell[1])),
            to_cell=(int(t_cell[0]), int(t_cell[1])), _tracer=tracer,
        ):
            pass
    else:
        with tactical_move_denied_span(
            actor=actor.name, cells_spent=verdict.distance_cells,
            cells_budget=verdict.max_cells, reason=verdict.reason, _tracer=tracer,
        ):
            pass
    return verdict
```
  Then at the call site in `dispatch_dice_throw` (after `target_name`/`spec`-resolution, before `ruleset.apply_beat`): resolve the room mask via the existing tactical-grid load path (`sd.dungeon_store.load_masks()[room_id]['mask_bytes_b64']` decoded — the same source `_maybe_build_runtime_cavern_payload` uses; `room_id = snapshot.character_locations.get(character_name)`). Call `_enforce_tactical_reach(...)`; if it returns a verdict with `not verdict.in_range`, short-circuit: broadcast the legible refusal (reuse the handler's `must_narrate`/refusal channel already used for other denied throws) and return WITHOUT applying the beat. The implementing agent wires the mask-load + refusal-broadcast against the existing dice-handler plumbing (both already present in `dice.py`); keep the enforcement OFF when `mask` is unavailable.
- [ ] Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_dice_tactical_enforcement.py -v` — expect **PASS**.
- [ ] Run the existing WN combat dispatch tests to confirm no regression on no-grid combat: `cd sidequest-server && uv run pytest tests/integration/test_wwn_caverns_dispatch.py tests/agents/subsystems/ -v` (classify any of the ~13 known content-drift failures as pre-existing).
- [ ] Lint + format, then commit:
```bash
cd sidequest-server
git add sidequest/server/dispatch/dice.py tests/server/dispatch/test_dice_tactical_enforcement.py
git commit -m "feat(tactical): C2 reach enforcement in dispatch_dice_throw (WN-gated, no-grid skip)"
```

---

## Task 8: C2 — seat positions at encounter instantiation

**Files:**
- Modify `sidequest-server/sidequest/server/dispatch/encounter_lifecycle.py` (call `seat_actor_cells` at the single seating chokepoint `instantiate_encounter_from_trigger`, sourcing anchors from the room's `RegionTactical` when the room has a tactical grid; emit `tactical.positions.seated`)
- Create `sidequest-server/tests/server/dispatch/test_encounter_position_seating.py`

**Interfaces:**
- Produces: encounter instantiation writes `per_actor_state['cell']` for each seated actor when the current room has a tactical grid, and emits `tactical.positions.seated` (seated_count, room_id). No-op (no cells, no span attrs beyond count=0) when the room has no grid.
- Consumes: `seat_actor_cells` (Task 4); `RegionTactical.anchors` loaded from `dungeon_store` (round-tripped via `RegionTactical.from_dict`, `sidequest/dungeon/tactical.py:59`); `tactical_positions_seated_span` (Task 6). Chokepoint: `instantiate_encounter_from_trigger` (`sidequest/server/dispatch/encounter_lifecycle.py`, the single seating site stamped by `created_turn`).

Steps:

- [ ] Write failing test `tests/server/dispatch/test_encounter_position_seating.py` — fixture-driven, reusing the `RegionTactical`+mask shape from `tests/server/tactical_emit_fixtures.py`; assert that after instantiation the seated actors carry cells drawn from the anchors, and that a room without a tactical block seats no cells. (Model the fixture on `build_sd_with_tactical_region`.) Assert the span fired via a monkeypatched capture, not prose.
- [ ] Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_encounter_position_seating.py -v` — expect **fail**.
- [ ] In `instantiate_encounter_from_trigger`, after `snapshot.encounter` is seated and `created_turn` stamped: resolve `room_id = snapshot.character_locations.get(<seating PC>)`; load the room's persisted mask dict via `dungeon_store.load_masks().get(room_id)`; if it carries a `'tactical'` block, build `RegionTactical.from_dict(block['tactical'])`, call `seat_actor_cells(snapshot.encounter, tactical.anchors)`, and emit `tactical_positions_seated_span(seated_count=len(placed), room_id=room_id)`. When there is no tactical block, emit the span with `seated_count=0` (honest: seating ran, grid absent) and place nothing. Guard the whole block so a `dungeon_store`-less session (region-mode) is a clean no-op.
- [ ] Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_encounter_position_seating.py -v` — expect **PASS**.
- [ ] Lint + format, then commit:
```bash
cd sidequest-server
git add sidequest/server/dispatch/encounter_lifecycle.py tests/server/dispatch/test_encounter_position_seating.py
git commit -m "feat(tactical): C2 seat actor cells from RegionTactical anchors at encounter start"
```

---

## Task 9: C2 — protocol echoes (TACTICAL_GRID adjudications + dice-result range)

**Files:**
- Modify `sidequest-server/sidequest/protocol/models.py` (add `TacticalAdjudication` near `TacticalFeature` `models.py:709`; add `adjudications` field to `TacticalGridPayload` `models.py:1305`; add optional `range_band`/`distance_cells` to the dice-result payload)
- Modify `sidequest-server/sidequest/protocol/__init__.py` (export `TacticalAdjudication`)
- Modify `sidequest-server/sidequest/server/websocket_handlers/map_emit.py` (populate `adjudications` from the actors' current cells when building the runtime cavern payload — round echo)
- Create `sidequest-server/tests/protocol/test_tactical_adjudication_payload.py`

**Interfaces:**
- Produces: `TacticalAdjudication(ProtocolBase)` with `actor: str`, `kind: str` (`"move"|"reach"|"aoe"`), `valid: bool`, `cells_spent: int | None = None`, `cells_budget: int | None = None`, `distance_cells: int | None = None`, `max_cells: int | None = None`, `mode: str | None = None`, `reason: str = ""`, `cells: list[tuple[int,int]] = Field(default_factory=list)`; `TacticalGridPayload.adjudications: list[TacticalAdjudication] = Field(default_factory=list)`; dice-result additive `range_band: str | None = None`, `distance_cells: int | None = None`.
- Consumes: `ProtocolBase`, `Field`, `field_serializer` (already imported in `models.py`). **All additive with empty defaults** — Track B's `SITE_MAP` cutover keeps the same `TacticalGridPayload` shape untouched, and every existing protocol/UI test still passes.

Steps:

- [ ] Write failing test `tests/protocol/test_tactical_adjudication_payload.py`:
```python
from sidequest.protocol.models import (
    TacticalAdjudication,
    TacticalGridPayload,
)


def test_adjudication_defaults_and_serialization():
    adj = TacticalAdjudication(actor="Rux", kind="reach", valid=False,
                              distance_cells=3, max_cells=1, mode="melee",
                              reason="target is 3 cells away; your reach is 1",
                              cells=[(2, 1), (3, 1)])
    dumped = adj.model_dump()
    assert dumped["cells"] == [[2, 1], [3, 1]]
    assert dumped["mode"] == "melee"


def test_tactical_grid_payload_adjudications_default_empty():
    p = TacticalGridPayload(room_id="r1", room_name="Cavern", room_type="cavern")
    assert p.adjudications == []  # additive, back-compat with Track B SITE_MAP
    p2 = TacticalGridPayload(
        room_id="r1", room_name="Cavern", room_type="cavern",
        adjudications=[TacticalAdjudication(actor="Rux", kind="move", valid=True,
                                            cells_spent=2, cells_budget=6)],
    )
    assert p2.adjudications[0].cells_spent == 2
```
- [ ] Run: `cd sidequest-server && uv run pytest tests/protocol/test_tactical_adjudication_payload.py -v` — expect **fail**.
- [ ] Add `TacticalAdjudication` after `TacticalFeature` in `models.py`:
```python
class TacticalAdjudication(ProtocolBase):
    """An echoed tactical adjudication for the resolution card / grid (ADR-096 v2).

    Additive echo — lets the client show the math (cells spent vs budget, range
    band, denial reason) without recomputing it. Empty defaults keep the wire
    contract stable for Track B's SITE_MAP cutover.
    """

    actor: str
    kind: str  # "move" | "reach" | "aoe"
    valid: bool
    cells_spent: int | None = None
    cells_budget: int | None = None
    distance_cells: int | None = None
    max_cells: int | None = None
    mode: str | None = None  # "melee" | "ranged"
    reason: str = ""
    cells: list[tuple[int, int]] = Field(default_factory=list)

    @field_serializer("cells")
    def _ser_cells(self, value: list[tuple[int, int]]) -> list[list[int]]:
        return [list(c) for c in value]
```
  Add to `TacticalGridPayload` (after `initiative`): `adjudications: list[TacticalAdjudication] = Field(default_factory=list)` with a docstring noting it is additive. Export `TacticalAdjudication` from `protocol/__init__.py`. Add `range_band: str | None = None` + `distance_cells: int | None = None` to the dice-result payload class (locate it in `protocol/models.py` — the payload with `outcome`/`difficulty`/`total`; confirm the class name and mirror the additive default pattern).
- [ ] In `map_emit.py::_maybe_build_runtime_cavern_payload`, after tokens are placed, build `adjudications` from the encounter actors' current cells — for each opponent, a `TacticalAdjudication(kind="reach", ...)` is optional; the minimum viable echo for this task is the **round move summary** (each PC's `cells_budget` from `ruleset.combat_move_cells`). Keep it small and additive; the resolution-card range echo is populated in the dice dispatch (Task 7's verdict → set `range_band`/`distance_cells` on the emitted dice-result). Assert population via a fixture test extending `tests/server/test_tactical_grid_emit_population.py`.
- [ ] Run: `cd sidequest-server && uv run pytest tests/protocol/test_tactical_adjudication_payload.py tests/server/test_tactical_grid_emit_population.py -v` — expect **PASS**.
- [ ] Lint + format, then commit:
```bash
cd sidequest-server
git add sidequest/protocol/models.py sidequest/protocol/__init__.py sidequest/server/websocket_handlers/map_emit.py tests/protocol/test_tactical_adjudication_payload.py
git commit -m "feat(tactical): C2 additive protocol echoes — TacticalAdjudication + dice-result range"
```

---

## Task 10: C2 — UI: adjudication echo on the grid + resolution card

**Files:**
- Modify `sidequest-ui/src/types/tactical.ts` (add optional `adjudications` to `TacticalGridData`)
- Modify `sidequest-ui/src/lib/tacticalGridFromWire.ts` (parse `adjudications` from `WirePayload`)
- Modify `sidequest-ui/src/components/TacticalGridRenderer.tsx` (render a denial banner + cells-spent/budget from echo)
- Modify `sidequest-ui/src/types/payloads.ts` (`DiceResultPayload`: optional `range_band?`, `distance_cells?`)
- Modify `sidequest-ui/src/dice/InlineDiceTray.tsx` (append range/cells to the `dice-result` readout `InlineDiceTray.tsx:403-453`)
- Create `sidequest-ui/src/__tests__/tactical-adjudication-echo.test.tsx`
- Modify `sidequest-ui/src/components/__tests__/` dice-result test (extend an existing InlineDiceTray test or add one for the range readout)

**Interfaces:**
- Produces: `TacticalGridData.adjudications?: readonly TacticalAdjudication[]` (new optional interface `TacticalAdjudication` in tactical.ts mirroring the server model — `actor`, `kind`, `valid`, `cells_spent?`, `cells_budget?`, `distance_cells?`, `max_cells?`, `mode?`, `reason`, `cells: [number,number][]`); parser maps `adjudications ?? []`; `DiceResultPayload.range_band?: string`, `distance_cells?: number`.
- Consumes: existing `tacticalGridFromWire` (`src/lib/tacticalGridFromWire.ts:38`) fail-loud guard (only the 4 core fields — new optional fields never break older payloads); `InlineDiceTray` result block (`src/dice/InlineDiceTray.tsx:403-453`). **No new tab** — the grid lives in the existing Map tab (MapWidget→Automapper→TacticalGridRenderer) and the echo lives in the existing Confrontation panel, so no `widgetRegistry`/`MobileTabView` dual-registration is needed.

Steps:

- [ ] Write failing vitest `src/__tests__/tactical-adjudication-echo.test.tsx`: render `TacticalGridRenderer` with a `TacticalGridData` fixture carrying `adjudications: [{actor:"Rux", kind:"reach", valid:false, distance_cells:3, max_cells:1, mode:"melee", reason:"target is 3 cells away; your reach is 1", cells:[]}]`; assert a `data-testid="tactical-denial"` node renders the `reason` text. Add a second test that `tacticalGridFromWire` maps a wire payload with `adjudications` into the parsed data (and that a payload WITHOUT `adjudications` yields `adjudications: []`, proving back-compat). Follow the fixture/`data-testid` shape of `src/__tests__/tactical-grid-renderer.test.tsx`.
- [ ] Write/extend the dice-result test: render `InlineDiceTray` (or its result subcomponent) with a `DiceResultPayload` fixture carrying `range_band: "rifle"`, `distance_cells: 4`; assert the `dice-result` readout shows the range band + cells (`data-testid` on the new annotation, e.g. `dice-result-range`).
- [ ] Run: `cd sidequest-ui && npx vitest run src/__tests__/tactical-adjudication-echo.test.tsx` and the dice-result test — expect **fail**.
- [ ] Implement: add the `TacticalAdjudication` interface + optional `adjudications` to `tactical.ts`; map `adjudications ?? []` (converting each wire `cells: [x,y][]` to the internal shape) in `tacticalGridFromWire.ts`; in `TacticalGridRenderer.tsx` render a compact banner for any `adjudication` with `valid === false` (`data-testid="tactical-denial"`, showing `reason`) and a subtle `cells_spent/cells_budget` chip for `kind === "move"`; add `range_band?`/`distance_cells?` to `DiceResultPayload` and append a ` · {range_band} range · {distance_cells} cells` annotation (guarded on presence) to the InlineDiceTray result block with a `data-testid`.
- [ ] Run the two UI tests + the existing tactical wiring test: `cd sidequest-ui && npx vitest run src/__tests__/tactical-adjudication-echo.test.tsx src/__tests__/tactical-grid-runtime-wiring.test.tsx` — expect **PASS** (the runtime-wiring test remains the non-test-consumer guard that `MapWidget` still renders `TacticalGridRenderer` from a wire payload).
- [ ] Lint: `cd sidequest-ui && npx eslint src/components/TacticalGridRenderer.tsx src/lib/tacticalGridFromWire.ts src/dice/InlineDiceTray.tsx src/types/tactical.ts src/types/payloads.ts` (or the repo's `client-lint`). Commit:
```bash
cd sidequest-ui
git add src/types/tactical.ts src/lib/tacticalGridFromWire.ts src/components/TacticalGridRenderer.tsx src/types/payloads.ts src/dice/InlineDiceTray.tsx src/__tests__/tactical-adjudication-echo.test.tsx
git commit -m "feat(tactical): C2 UI — adjudication echo on grid + range/cells on resolution card"
```

---

## Task 11: C3 — pure zone projection (grid → contiguous cell clusters)

**Files:**
- Create `sidequest-server/sidequest/game/tactical/zones.py`
- Create `sidequest-server/tests/game/tactical/test_zones.py`

**Interfaces:**
- Produces: `ZoneProjection(zones: dict[str, frozenset[Cell]], cell_to_zone: dict[Cell, str], adjacency: dict[str, frozenset[str]])`; `project_zones(mask: str) -> ZoneProjection`. Deterministic (stable zone ids `z0, z1, ...` assigned in scan order), pure. Partition strategy: **choke-seeded multi-source flood** — non-chokepoint "core" cells (`>2` orthogonal floor neighbours; the complement of `dungeon/tactical.py::_chokepoints`' `<=2` rule) form zone *seeds* via 8-connected components; then a multi-source BFS over the FULL floor graph assigns EVERY floor cell (chokes included) to its nearest seed-zone, ties breaking to the lowest zone id. This guarantees every floor cell gets a home (no orphaned chokes), reuses the cavern's own bottleneck structure as zone borders (Fate zones = "rooms/areas"; a cavern's necks are exactly those borders), and degenerates cleanly to one zone for an all-choke corridor or an open room.
- Consumes: `parse_mask`, `is_floor`, `neighbors` (C1, Task 1).

Steps:

- [ ] Write failing test `tests/game/tactical/test_zones.py`:
```python
from sidequest.game.tactical.zones import ZoneProjection, project_zones

# A cavern whose middle row is pinched by wall pillars at (2,2) and (4,2),
# leaving a 1-wide choke column at (3,2): a natural multi-zone cavern.
DUMBBELL = (
    "#######\n"
    "#.....#\n"
    "#.#.#.#\n"
    "#.....#\n"
    "#######"
)


def test_projection_is_deterministic():
    a = project_zones(DUMBBELL)
    b = project_zones(DUMBBELL)
    assert a.cell_to_zone == b.cell_to_zone
    assert isinstance(a, ZoneProjection)


def test_every_floor_cell_has_a_zone():
    proj = project_zones(DUMBBELL)
    rows = DUMBBELL.split("\n")
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == ".":
                assert (x, y) in proj.cell_to_zone


def test_open_room_is_one_zone():
    proj = project_zones("#####\n#...#\n#...#\n#####")
    assert len(proj.zones) == 1


def test_adjacency_is_symmetric():
    proj = project_zones(DUMBBELL)
    for z, neigh in proj.adjacency.items():
        for n in neigh:
            assert z in proj.adjacency[n]
```
- [ ] Run: `cd sidequest-server && uv run pytest tests/game/tactical/test_zones.py -v` — expect **fail**.
- [ ] Create `sidequest/game/tactical/zones.py`:
```python
"""Fate zone projection over a tactical mask (ADR-096 v2, Track C3).

Coarsen the same #/. grid the WN binding consumes as exact cells into
contiguous-cell-cluster ZONES the Fate binding consumes. Deterministic + pure:
zone ids are ``z0, z1, ...`` in scan order. Partition strategy: a cavern's own
1-wide chokepoints are the zone borders (a Fate zone is a 'room/area'; a neck is
exactly the border between two areas). Floor minus chokepoints -> connected
components = zone cores; each chokepoint attaches to its lowest-id adjacent zone;
zones are adjacent iff a chokepoint or shared edge touches both.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from sidequest.game.tactical.adjudication import Cell, is_floor, neighbors, parse_mask


def _orth_floor_count(rows: list[str], cell: Cell) -> int:
    x, y = cell
    n = 0
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if is_floor(rows, (x + dx, y + dy)):
            n += 1
    return n


@dataclass(frozen=True)
class ZoneProjection:
    zones: dict[str, frozenset[Cell]]
    cell_to_zone: dict[Cell, str]
    adjacency: dict[str, frozenset[str]]


@dataclass(frozen=True)
class ZoneMoveAdjudication:
    """A Fate-neutral verdict on one zone move (Track C3)."""

    free: bool
    requires_overcome: bool
    from_zone: str
    to_zone: str


def project_zones(mask: str) -> ZoneProjection:
    rows = parse_mask(mask)
    floor: list[Cell] = [
        (x, y) for y, row in enumerate(rows) for x, ch in enumerate(row) if ch == "."
    ]
    if not floor:
        return ZoneProjection({}, {}, {})

    chokes = {c for c in floor if _orth_floor_count(rows, c) <= 2}
    core = [c for c in floor if c not in chokes]

    # Zone SEEDS = 8-connected components of the non-choke core cells (scan order).
    seed_zone: dict[Cell, str] = {}
    zid = 0
    for start in core:
        if start in seed_zone:
            continue
        name = f"z{zid}"
        zid += 1
        stack = [start]
        seed_zone[start] = name
        while stack:
            cur = stack.pop()
            for nb in neighbors(rows, cur):
                if nb in chokes or nb in seed_zone:
                    continue
                seed_zone[nb] = name
                stack.append(nb)

    # Degenerate: an all-choke cavern (1-wide corridor / tiny room) has no cores.
    # Treat the whole floor as one zone so no cell is orphaned.
    if not seed_zone:
        one = {c: "z0" for c in floor}
        return ZoneProjection(
            zones={"z0": frozenset(floor)}, cell_to_zone=one, adjacency={"z0": frozenset()}
        )

    # Assign EVERY floor cell to its nearest seed-zone via multi-source BFS over
    # the full floor graph. All seeds start at layer 0; FIFO layering gives the
    # nearest zone, and seeding the frontier in (zone-id, y, x) order makes ties
    # break to the lowest zone id — deterministic and total.
    zone_of: dict[Cell, str] = dict(seed_zone)
    frontier: deque[Cell] = deque(sorted(seed_zone, key=lambda c: (seed_zone[c], c[1], c[0])))
    while frontier:
        cur = frontier.popleft()
        for nb in neighbors(rows, cur):
            if nb not in zone_of:
                zone_of[nb] = zone_of[cur]
                frontier.append(nb)

    zones: dict[str, set[Cell]] = {}
    for c, z in zone_of.items():
        zones.setdefault(z, set()).add(c)

    # Adjacency: two zones are adjacent iff a cell of one 8-touches a cell of the other.
    adjacency: dict[str, set[str]] = {z: set() for z in zones}
    for c, z in zone_of.items():
        for nb in neighbors(rows, c):
            nz = zone_of.get(nb)
            if nz is not None and nz != z:
                adjacency[z].add(nz)
                adjacency[nz].add(z)

    return ZoneProjection(
        zones={z: frozenset(cs) for z, cs in zones.items()},
        cell_to_zone=dict(zone_of),
        adjacency={z: frozenset(ns) for z, ns in adjacency.items()},
    )
```
- [ ] Run: `cd sidequest-server && uv run pytest tests/game/tactical/test_zones.py -v` — expect **PASS**.
- [ ] Lint + format, then commit:
```bash
cd sidequest-server
git add sidequest/game/tactical/zones.py tests/game/tactical/test_zones.py
git commit -m "feat(tactical): C3 pure Fate zone projection — chokepoint-partition over the mask"
```

---

## Task 12: C3 — Fate binding: wire zone state + zone-move legality + OTEL

**Files:**
- Modify `sidequest-server/sidequest/game/ruleset/fate.py` (add `project_conflict_zones` + `adjudicate_zone_move` to `FateRulesetModule` `fate.py:58`)
- Modify `sidequest-server/sidequest/telemetry/spans/tactical.py` (add `SPAN_TACTICAL_ZONE_PROJECTED` + `SPAN_TACTICAL_ZONE_MOVE` + helpers + routes)
- Create `sidequest-server/tests/agents/ruleset/test_fate_zone_binding.py`

**Interfaces:**
- Produces (on `FateRulesetModule`): `project_conflict_zones(*, encounter, mask, anchors=None, _tracer=None) -> dict[str, str]` — projects zones from `mask` (via C3 `project_zones`), populates `encounter.zones` (the inert slot `encounter.py:350`) with the zone ids, seats each actor's `per_actor_state['zone']` from its `per_actor_state['cell']` (or an anchor fallback), emits `tactical.zone.projected`, returns the name→zone map; `adjudicate_zone_move(*, from_zone, to_zone, projection, _tracer=None) -> ZoneMoveAdjudication` — returns `free=True` for same/adjacent zone (Fate RAW: one zone is a free supplemental move), `free=False, requires_overcome=True` for a non-adjacent (2+) zone move, emitting `tactical.zone.move`.
- Consumes: `sidequest.game.tactical.zones.project_zones` + `ZoneProjection` (C3 Task 11 — **the Fate binding consuming the zone projection**); `StructuredEncounter.zones` + `EncounterActor.per_actor_state['zone']` (the inert Fate slots, `encounter.py:350-353`); new tactical zone spans.
- **Grounding limit (stated, not invented):** Fate has NO `move` action verb (verbs are `overcome`/`create_advantage`/`attack`/`concede`, `fate_action.py:40`) and today's Fate binding consumes NO position/zone state (the slots are inert — zero readers). C3 therefore delivers: the projection, the state population, and the **legality classification** (free vs requires-Overcome) grounded in Fate Core RAW — it does NOT add a new Fate combat verb, and it does NOT rewrite `run_fate_exchange`. A costed zone move surfaces to the player as the existing **Overcome** action (opposition can be zone-derived by a later story); wiring a player-facing zone-move control + narrator-driven zone-cost is a **named follow-up**, explicitly out of C3's scope.

Steps:

- [ ] Add to `sidequest/telemetry/spans/tactical.py`: `SPAN_TACTICAL_ZONE_PROJECTED = "tactical.zone.projected"`, `SPAN_TACTICAL_ZONE_MOVE = "tactical.zone.move"`, their `SPAN_ROUTES` entries (`event_type="state_transition"`, `component="tactical"`, extracting `zone_count`/`from_zone`/`to_zone`/`free`), context-manager helpers `tactical_zone_projected_span(*, zone_count, room_id, ...)` and `tactical_zone_move_span(*, actor, from_zone, to_zone, free, requires_overcome, ...)` each mirroring via `_mirror`, and add all four names to `__all__`.
- [ ] Write failing test `tests/agents/ruleset/test_fate_zone_binding.py`:
```python
from sidequest.game.encounter import EncounterActor, EncounterMetric, StructuredEncounter
from sidequest.game.ruleset.registry import get_ruleset_module
from sidequest.game.tactical.zones import project_zones

DUMBBELL = "#######\n#.....#\n#.#.#.#\n#.....#\n#######"


def _fate_conflict():
    return StructuredEncounter(
        encounter_type="social",
        player_metric=EncounterMetric(name="advantage", threshold=3),
        opponent_metric=EncounterMetric(name="advantage", threshold=3),
        actors=[
            EncounterActor(name="Hero", role="combatant", side="player",
                           per_actor_state={"cell": [1, 1]}),
            EncounterActor(name="Rival", role="combatant", side="opponent",
                           per_actor_state={"cell": [5, 3]}),
        ],
    )


def test_project_conflict_zones_populates_state():
    fate = get_ruleset_module("fate")
    enc = _fate_conflict()
    placed = fate.project_conflict_zones(encounter=enc, mask=DUMBBELL)
    assert enc.zones  # the inert slot is now populated
    assert enc.actors[0].per_actor_state["zone"] in enc.zones
    assert placed["Hero"] == enc.actors[0].per_actor_state["zone"]


def test_adjudicate_zone_move_free_vs_overcome():
    from sidequest.game.tactical.zones import ZoneProjection

    fate = get_ruleset_module("fate")
    # z0 - z1 - z2 line: z0 and z2 are NOT adjacent (2 zones apart).
    proj = ZoneProjection(
        zones={"z0": frozenset({(0, 0)}), "z1": frozenset({(1, 0)}), "z2": frozenset({(2, 0)})},
        cell_to_zone={(0, 0): "z0", (1, 0): "z1", (2, 0): "z2"},
        adjacency={"z0": frozenset({"z1"}), "z1": frozenset({"z0", "z2"}), "z2": frozenset({"z1"})},
    )
    same = fate.adjudicate_zone_move(from_zone="z0", to_zone="z0", projection=proj)
    assert same.free and not same.requires_overcome
    adjacent = fate.adjudicate_zone_move(from_zone="z0", to_zone="z1", projection=proj)
    assert adjacent.free  # SRD: one zone is a free supplemental move
    far = fate.adjudicate_zone_move(from_zone="z0", to_zone="z2", projection=proj)
    assert not far.free and far.requires_overcome
```
- [ ] Run: `cd sidequest-server && uv run pytest tests/agents/ruleset/test_fate_zone_binding.py -v -n0` — expect **fail**.
- [ ] Add to `FateRulesetModule` a `ZoneMoveAdjudication` dataclass (or reuse a small frozen dataclass defined in `zones.py`), `project_conflict_zones`, and `adjudicate_zone_move`:
```python
    def project_conflict_zones(self, *, encounter, mask, anchors=None, _tracer=None):
        """Project the tactical mask into Fate zones, populate ``encounter.zones``
        and each actor's ``per_actor_state['zone']`` (from its cell), and emit
        ``tactical.zone.projected``. Returns name->zone. The Fate binding
        consuming the C3 projection (the inert slots become live)."""
        from sidequest.game.tactical.zones import project_zones
        from sidequest.telemetry.spans.tactical import tactical_zone_projected_span

        proj = project_zones(mask)
        encounter.zones = sorted(proj.zones)
        placed: dict[str, str] = {}
        for actor in encounter.actors:
            cell = actor.per_actor_state.get("cell")
            if cell is None:
                continue
            zid = proj.cell_to_zone.get((int(cell[0]), int(cell[1])))
            if zid is not None:
                actor.per_actor_state["zone"] = zid
                placed[actor.name] = zid
        with tactical_zone_projected_span(zone_count=len(proj.zones), room_id="", _tracer=_tracer):
            pass
        return placed

    def adjudicate_zone_move(self, *, from_zone, to_zone, projection, actor="", _tracer=None):
        """Fate Core RAW zone move: same/adjacent zone is a FREE supplemental
        move; a non-adjacent (2+) zone move REQUIRES an Overcome action. Emits
        ``tactical.zone.move``. This classifies legality only — it does not add a
        Fate 'move' verb; a costed move surfaces via the existing Overcome."""
        from sidequest.game.tactical.zones import ZoneMoveAdjudication
        from sidequest.telemetry.spans.tactical import tactical_zone_move_span

        adjacent = to_zone == from_zone or to_zone in projection.adjacency.get(from_zone, frozenset())
        verdict = ZoneMoveAdjudication(free=adjacent, requires_overcome=not adjacent,
                                       from_zone=from_zone, to_zone=to_zone)
        with tactical_zone_move_span(actor=actor, from_zone=from_zone, to_zone=to_zone,
                                     free=verdict.free, requires_overcome=verdict.requires_overcome,
                                     _tracer=_tracer):
            pass
        return verdict
```
  `ZoneMoveAdjudication(free, requires_overcome, from_zone, to_zone)` is already defined in `zones.py` (Task 11) — import it, do not redefine.
- [ ] Run: `cd sidequest-server && uv run pytest tests/agents/ruleset/test_fate_zone_binding.py tests/telemetry/test_routing_completeness.py -v -n0` — expect **PASS**.
- [ ] Lint + format, then commit:
```bash
cd sidequest-server
git add sidequest/game/ruleset/fate.py sidequest/game/tactical/zones.py sidequest/telemetry/spans/tactical.py tests/agents/ruleset/test_fate_zone_binding.py
git commit -m "feat(tactical): C3 Fate binding — zone projection state + zone-move legality + OTEL"
```

---

## Task 13: C3 — wire Fate zone projection at conflict seating (production reachability)

**Files:**
- Modify `sidequest-server/sidequest/server/dispatch/encounter_lifecycle.py` (when a Fate-bound pack seats a conflict on a room with a tactical grid, call `ruleset.project_conflict_zones` right after `seat_actor_cells` from Task 8)
- Create `sidequest-server/tests/server/dispatch/test_fate_zone_seating_wiring.py`

**Interfaces:**
- Produces: at Fate conflict instantiation on a gridded room, `encounter.zones` is populated and `tactical.zone.projected` fires — the wiring test proving `project_conflict_zones` is reachable from production, not just unit-tested.
- Consumes: `seat_actor_cells` (Task 4/8), `FateRulesetModule.project_conflict_zones` (Task 12), the room mask (Task 8's load path). Gate on `isinstance(ruleset, FateRulesetModule)` (capability gate) so WN/dial packs are untouched.

Steps:

- [ ] Write failing wiring test `tests/server/dispatch/test_fate_zone_seating_wiring.py` — fixture-driven: a Fate-bound pack (e.g. `tea_and_murder`/`glenross` or a synthetic Fate genre pack) seats a conflict in a room with a persisted tactical block; assert `snapshot.encounter.zones` is non-empty after instantiation and the `tactical.zone.projected` span fired (monkeypatched capture). Reuse the mask/`RegionTactical` fixture shape from `tactical_emit_fixtures.py`. Intent-router stubbed by the autouse fixture.
- [ ] Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_fate_zone_seating_wiring.py -v` — expect **fail**.
- [ ] In `instantiate_encounter_from_trigger` (the same site as Task 8), after `seat_actor_cells`, add: `if isinstance(ruleset, FateRulesetModule) and mask is not None: ruleset.project_conflict_zones(encounter=snapshot.encounter, mask=mask)`. (Resolve `ruleset` via `get_ruleset_module(pack.rules.ruleset)`; the mask is already loaded in Task 8's block — extend that block rather than reloading.)
- [ ] Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_fate_zone_seating_wiring.py -v` — expect **PASS**.
- [ ] Run the full new-suite sweep serially for the OTEL pieces: `cd sidequest-server && uv run pytest tests/game/tactical/ tests/agents/ruleset/test_wn_tactical_binding.py tests/agents/ruleset/test_fate_zone_binding.py tests/telemetry/test_tactical_telemetry_sink.py tests/telemetry/test_routing_completeness.py -v -n0`.
- [ ] Lint + format, then commit:
```bash
cd sidequest-server
git add sidequest/server/dispatch/encounter_lifecycle.py tests/server/dispatch/test_fate_zone_seating_wiring.py
git commit -m "feat(tactical): C3 wire Fate zone projection at conflict seating (production reachable)"
```

---

## Grounding limits (stated, not invented)

Read these before implementing — they are the places the plan is deliberately conservative rather than inventing mechanics:

1. **WN range-band cell table is coarse.** `RANGE_BAND_CELLS` (Task 5) is SRD-*shaped* but the exact per-band cell counts are not pinned to a specific WN SRD weapon-range figure. On a room-scale grid (~15–25 cells) pistol/rifle exceed the room, so **LOS is the binding ranged constraint** and the table only bites for `melee`/`thrown`/`shotgun` — which is the mechanically meaningful v1 distinction. Confirm/tune the table against the WN SRD weapon table in a follow-up; do not scatter per-world overrides (flat-13 class).
2. **`DamageSpec.range_band` plumbing.** Task 7 reads the weapon's `range_band` via the resolved `spec` (defaulting to melee when absent). Whether `DamageSpec` itself carries `range_band` or it must be read off the resolved `CatalogItem`/`ItemPayload` (`inventory.py:214`) is a small plumbing detail to confirm against `inventory_resolve.py`; the safe default (melee) is correct for the common cavern case and never blocks a strike spuriously.
3. **Fate movement is not a resolvable verb.** Fate's action set is `overcome/create_advantage/attack/concede` — there is **no `move`**, and today's Fate binding reads no zone state (the `encounter.zones` / `per_actor_state['zone']` slots have zero consumers). C3 wires those slots + a legality classification grounded in Fate Core RAW (1 zone free, further/opposed = Overcome). It does **not** add a Fate move verb, does not rewrite `run_fate_exchange`, and does not build a player-facing zone-move control — those are named follow-ups. C3's honest deliverable is: projection + zone state + legality + OTEL, consumed by the Fate binding.
4. **Movement *validation* (path-cost against budget) is C1-complete but not yet player-invoked on the WN path.** Task 7 enforces *reach/range* on strikes (the load-bearing "can I even hit this" question). A player-initiated tactical *move* action (drag a token N cells, validate against `combat_move_cells`, emit `tactical.move.validated/denied`) needs a new inbound message or a move-intent dispatch — the spec's §4 says "no new inbound messages in v1," so token-move UI is a deferred follow-up. The `adjudicate_tactical_move` adjudicator + spans are built and unit-tested now so that follow-up is pure wiring, not new logic.
5. **AoE is C1-complete but not yet bound to a WN spell/grenade.** `aoe_burst`/`aoe_line` + the `tactical.aoe.cells` span exist and are tested; binding them to a specific WWN spell or CWN grenade template (which weapon/spell fires which template at which cell) is a per-content follow-up, not core Track C.
