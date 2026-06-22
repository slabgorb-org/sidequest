# Sünden Static→Procedural Crossing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the working `ropefoot → entrance` crossing (attempt #8), make the movement engine visible in saves, and close the two narrow remaining bugs — on ONE branch, no epic.

**Architecture:** The crossing already works (attempt #8, commit `711365e0`, 37 passing tests, live-verified 2026-06-22 — `resolved_via=surface_descent_adjacent`). This plan does NOT re-architect anything. It (1) lands #8 cleanly onto develop, (2) routes movement decisions into the `turn_telemetry` DB sink so the engine stops looking dead in saves — the root cause that defeated 8 prior attempts, (3) denies the narrator's `apply_world_patch` escape hatch from writing `/current_region` in region-mode worlds (kills the live clobber race), and (4) makes the dungeon lookahead expand the current node's ring before declaring `no_candidate_edges`. No "single-authority" doctrine. No `narration_apply` surgery. Nothing touches oz/wonderland/gulliver or the orbital path.

**Tech Stack:** Python 3 / FastAPI, `uv`-managed; pytest (xdist `-n auto` default); OTEL spans + `turn_telemetry` Postgres sink; ADR-106 procedural dungeon; ADR-113 intent-router engine-first dispatch.

**Source of truth for the diagnosis:** `docs/superpowers/specs/2026-06-22-sunden-crossing-FINDINGS.md`. The two earlier notes in that directory (`2026-06-21-location-single-authority-design.md`, `2026-06-22-static-procedural-crossing-design.md`) are WRONG — reasoned from saves, not a live run. Do not follow them.

## Global Constraints

- **Repo:** `sidequest-server`. Branch off `develop`; PRs target `develop` (github-flow). One branch for all four tasks: `feat/sunden-crossing-land-and-observe`.
- **Branch-creation hook:** the protected-branch PreToolUse hook rejects `git commit` while on `develop`/`main` even if `checkout -b` precedes it in the same Bash call (evaluated pre-run). Always run `git checkout -b ...` as its OWN Bash call, before any commit.
- **Pull before push:** parallel clones (oq-1..oq-4) share these repos. `git pull --rebase` before pushing; expect collisions.
- **Ruff:** format ONLY branch-touched files (`uv run ruff format <file>`), never bare `ruff format .` (it reformats ~167 files and displaces noqa directives).
- **Tests:** `uv run pytest <path> -v`. The full parallel suite deadlocks ~18 OTEL span-count tests (pre-existing) — run any telemetry/span-count test file with `-n0`.
- **Pre-existing red (do NOT attribute to this work):** ~13 server failures vs current content `develop` (WWN migration + seaboard promotion); `test_message_type_complete_count` 54-vs-55 (QUESTS). Classify pre-existing; do not block.
- **OTEL Observability Principle (CLAUDE.md):** every subsystem decision emits a span. Movement already emits Jaeger spans; Task 2 adds the missing DB-sink emit so the GM panel / saves can see them.
- **No Silent Fallbacks / fail loud (SOUL.md, CLAUDE.md):** every new branch either resolves loudly or fails loudly — never a silent stay-put or invented region.

---

### Task 1: Land the working crossing (attempt #8)

Attempt #8 is one clean commit (`711365e0`) with 37 passing tests. It does NOT touch `narration_apply.py` (the "151× churn" the findings doc warned about was branch *exploration history*, not this commit). Cherry-pick it; do not merge the whole branch.

**Files (touched by the cherry-pick — for reference, do not hand-edit):**
- Modify: `sidequest/agents/subsystems/movement.py` (+48: the `direction == "deeper"` adjacency-descent block, inserted after the owned-seam block ~line 300)
- Modify: `sidequest/game/seams/registry.py` (new `seam_route_via_adjacency`)
- Modify: `sidequest/game/seams/__init__.py` (export it)
- Modify: `sidequest/server/intent_router_pass.py` (`_build_state_summary`: `seam_route_for(...) or seam_route_via_adjacency(...)`)
- Modify: `sidequest/server/websocket_handlers/chargen_mixin.py` (MP joiner inherits `pc_regions` from a seated peer)
- Test: `tests/game/test_seam_registry.py`, `tests/agents/subsystems/test_movement_seam_crossing.py`, `tests/server/test_intent_router_region_exits.py`

**Interfaces:**
- Produces: `seam_route_via_adjacency(cartography: CartographyConfig | None, region_id: str) -> Route | None` — the UNIQUE adjacent owner's seam route, or `None` (no adjacent owner OR more than one — No Silent Fallbacks). Consumed by Task 4's reasoning about which regions own seams.

- [ ] **Step 1: Create the branch (own Bash call)**

```bash
cd sidequest-server && git fetch origin && git checkout develop && git pull --rebase origin develop
```

- [ ] **Step 2: Branch off develop**

```bash
cd sidequest-server && git checkout -b feat/sunden-crossing-land-and-observe
```

- [ ] **Step 3: Cherry-pick attempt #8**

```bash
cd sidequest-server && git cherry-pick 711365e0
```

Expected: clean apply. If `movement.py` conflicts (the lateral-mover PR #1029 may have landed nearby), resolve by KEEPING both blocks — the `direction == "deeper"` adjacency block belongs in the region-mode branch right after the owned-seam (`seam_route is not None`) handling and before the Story-105-3 reverse-seam block. The two blocks are independent (adjacency block ~line 300 region-mode; lateral block ~line 430 surface-cartography). Match the diff in `git show 711365e0`.

- [ ] **Step 4: Run #8's tests — they already exist and must pass**

Run:
```bash
cd sidequest-server && uv run pytest tests/game/test_seam_registry.py tests/agents/subsystems/test_movement_seam_crossing.py tests/server/test_intent_router_region_exits.py -v
```
Expected: PASS (37 tests). Key cases: `test_surface_adjacent_descent_crosses_to_entrance` (resolves via `surface_descent_adjacent`, PC rebound to entrance), `test_surface_adjacent_non_deeper_does_not_cross` (lateral camp moves defer, don't teleport), `test_seam_route_via_adjacency_ambiguous_returns_none`.

- [ ] **Step 5: No commit needed (cherry-pick already committed it). Verify the log.**

Run:
```bash
cd sidequest-server && git log --oneline -1
```
Expected: `fix(dungeon): make ADR-106 procedural megadungeon reachable from the surface seam`

---

### Task 2: Mirror movement spans into `turn_telemetry` (the observability fix)

**This is the fix that ends "the engine looks dead in saves."** Movement spans (`movement.resolved`/`unresolved`/`region_mode`) reach Jaeger via `Span.open` but NEVER the `turn_telemetry` Postgres sink — zero `component='movement'` rows exist across the entire table, ever. `magic`/`confrontation`/`census` land in the sink because they call `publish_event(...)`. Do this SECOND so every later fix is verifiable from saves, not just live Jaeger.

**Design — one choke point, NOT a per-call-site chase.** There are SEVEN movement emit sites across FOUR files: `movement.py:700` (navigator), `:1010` (region-mode defer), `:1044` (unresolved), `:450` (cartography-lateral — only present if PR #1029 lands; NOT on this branch), `narration_apply.py:4357` (narrator-path movement), and the two seam resolvers — `seams/deep_descent.py:55` (**the actual `ropefoot → entrance` crossing**) and `seams/surface_ascent.py:68` (reverse). Editing each site is exactly how a fix half-lands and drifts. Instead, every one of them flows through the THREE context managers in `telemetry/spans/movement.py` (`movement_resolved_span`, `movement_unresolved_span`, `movement_region_mode_span`). Mirror to the DB sink INSIDE those three helpers, reusing each span's existing `SPAN_ROUTES` extract — one file, covers every site (present and future), zero field drift.

**Files:**
- Modify: `sidequest/telemetry/spans/movement.py` (one `_mirror_movement_span_to_sink` helper + one line in each of the 3 context managers + a module-level `publish_event` import)
- Test: `tests/telemetry/test_movement_telemetry_sink.py` (create)

**Interfaces:**
- Consumes: `SPAN_ROUTES[name].extract(span) -> dict`, `.event_type`, `.component` (already defined in this file). `publish_event(event_type, fields, *, component=..., tx=None, event_seq=None)` from `sidequest.telemetry.watcher_hub` — imported at MODULE level (verified cycle-free: `watcher_hub` has no top-level `telemetry.spans` import). `Span.open` yields the OTEL SDK span; its `.attributes` is the same dict the `SPAN_ROUTES` extracts read at on_end and is populated by the caller's `set_attribute` calls — readable after the `with` block closes.
- Produces: every `movement.resolved`/`movement.unresolved`/`movement.region_mode` span now also writes one `turn_telemetry` row with `component='movement'` (`tx=None`, NULL `event_seq` — movement fires in the ADR-113 engine-first pass, before the turn event frame, so there is no `SaveTransaction` to ride). The `room.discovered` / `room.transition_tick` spans are intentionally NOT mirrored — they are the room axis (153-24), not the region-movement decisions the findings doc targets; keep scope narrow.

- [ ] **Step 1: Write the failing test**

Create `tests/telemetry/test_movement_telemetry_sink.py`. The test drives the context managers directly and asserts each mirrors into the `publish_event` DB-sink path with `component='movement'`. **It MUST run under a recording SDK tracer** (so `set_attribute` records and `span.attributes` is non-empty) — use the same in-memory-exporter fixture the movement subsystem tests use (`capture_spans`); under a NoOp tracer `span.attributes` is empty and the assertions are vacuous. If `capture_spans` is not a global conftest fixture, replicate its in-memory `TracerProvider` + `SimpleSpanProcessor(InMemorySpanExporter)` setup in a local fixture.

```python
"""Movement spans must mirror into the turn_telemetry DB sink, not just Jaeger.

Root cause behind 8 failed crossing attempts (2026-06-22 findings): movement
reaches Jaeger via Span.open but never turn_telemetry, so a firing engine reads
as DEAD in saves. Every movement emit site flows through these 3 context
managers, so mirroring there covers the subsystem, narration_apply, AND both
seam resolvers (deep_descent = the real ropefoot->entrance crossing).
"""
import sidequest.telemetry.spans.movement as mv


def test_resolved_span_mirrors_to_sink(monkeypatch, capture_spans):
    published: list[tuple] = []
    monkeypatch.setattr(mv, "publish_event", lambda et, fields, **kw: published.append((et, fields, kw)))

    with mv.movement_resolved_span(pc_name="Groucho", from_region="ropefoot", to_region="entrance") as span:
        span.set_attribute("resolved_via", "surface_descent_adjacent")
        span.set_attribute("edge_kind", "surface_descent")

    assert published, "movement.resolved did not mirror into the turn_telemetry sink"
    event_type, fields, kw = published[0]
    assert event_type == "state_transition"
    assert kw.get("component") == "movement"
    assert fields["op"] == "movement.resolved"
    assert fields["from_region"] == "ropefoot"
    assert fields["to_region"] == "entrance"
    assert fields["resolved_via"] == "surface_descent_adjacent"


def test_unresolved_span_mirrors_to_sink(monkeypatch, capture_spans):
    published: list[tuple] = []
    monkeypatch.setattr(mv, "publish_event", lambda et, fields, **kw: published.append((et, fields, kw)))

    with mv.movement_unresolved_span(pc_name="Groucho", reason="no_candidate_edges", from_region="exp002.r2") as span:
        span.set_attribute("available_exits", [])

    assert published, "movement.unresolved did not mirror into the sink"
    _, fields, kw = published[0]
    assert kw.get("component") == "movement"
    assert fields["op"] == "movement.unresolved"
    assert fields["reason"] == "no_candidate_edges"
```

- [ ] **Step 2: Run it to confirm it fails**

Run:
```bash
cd sidequest-server && uv run pytest tests/telemetry/test_movement_telemetry_sink.py -v -n0
```
Expected: FAIL — `AssertionError: movement.resolved did not mirror into the turn_telemetry sink` (the context managers only open Jaeger spans today; they never call `publish_event`).

- [ ] **Step 3: Add the module import + mirror helper**

In `sidequest/telemetry/spans/movement.py`, add the module-level import near the existing imports (cycle-free — confirmed):

```python
from sidequest.telemetry.watcher_hub import publish_event
```

Add the helper after the `SPAN_ROUTES` registrations, before the context-manager helpers:

```python
def _mirror_movement_span_to_sink(span_name: str, span: trace.Span) -> None:
    """Mirror a finished movement span into the turn_telemetry DB sink.

    Movement spans reach Jaeger via Span.open but never the turn_telemetry
    Postgres sink — a firing engine reads as DEAD in saves (the 2026-06-22 root
    cause behind 8 failed crossing attempts). EVERY movement emit site flows
    through the three context managers below — the subsystem navigator, the
    region-mode defer, the unresolved path, narration_apply's movement, AND both
    seam resolvers (deep_descent = the real ropefoot->entrance crossing,
    surface_ascent = the reverse) — so mirroring HERE covers all of them with no
    per-site edits and no field drift: we reuse the SAME SPAN_ROUTES extract the
    GM-panel dashboard uses. tx defaults to None -> the out-of-frame sink (NULL
    event_seq); movement fires in the ADR-113 engine-first pass, before the turn
    event frame, so there is no SaveTransaction to ride.
    """
    route = SPAN_ROUTES.get(span_name)
    if route is None:
        return
    publish_event(route.event_type, route.extract(span), component=route.component)
```

- [ ] **Step 4: Call the mirror in each of the 3 context managers**

After the `with Span.open(...)` block closes (span ended → attributes final) in each helper, add the mirror line. `movement_resolved_span`:
```python
    with Span.open(
        SPAN_MOVEMENT_RESOLVED,
        {
            "pc_name": pc_name,
            "from_region": from_region,
            "to_region": to_region,
            **attrs,
        },
        tracer_override=_tracer,
    ) as span:
        yield span
    _mirror_movement_span_to_sink(SPAN_MOVEMENT_RESOLVED, span)
```
`movement_unresolved_span` (the `set_status(ERROR)` stays before `yield`; mirror after the `with`):
```python
    ) as span:
        span.set_status(Status(StatusCode.ERROR, reason))
        yield span
    _mirror_movement_span_to_sink(SPAN_MOVEMENT_UNRESOLVED, span)
```
`movement_region_mode_span`:
```python
    ) as span:
        yield span
    _mirror_movement_span_to_sink(SPAN_MOVEMENT_REGION_MODE, span)
```
(Do NOT add the mirror to `room_discovered_span` / `room_transition_tick_span` — out of scope, different axis.)

- [ ] **Step 5: Run the test to confirm it passes (and movement subsystem tests stay green)**

Run:
```bash
cd sidequest-server && uv run pytest tests/telemetry/test_movement_telemetry_sink.py tests/agents/subsystems/test_movement_seam_crossing.py -v -n0
```
Expected: PASS (new mirror tests + the Task 1 crossing tests still green — the crossing test asserts exactly one `movement.resolved` span, which the mirror does not duplicate in Jaeger).

- [ ] **Step 6: Format + commit**

```bash
cd sidequest-server && uv run ruff format sidequest/telemetry/spans/movement.py tests/telemetry/test_movement_telemetry_sink.py && uv run ruff check sidequest/telemetry/spans/movement.py
git add sidequest/telemetry/spans/movement.py tests/telemetry/test_movement_telemetry_sink.py
git commit -m "fix(telemetry): mirror movement spans into turn_telemetry (DB sink, not just Jaeger)

Movement spans reached Jaeger via Span.open but never the turn_telemetry
Postgres sink — zero component='movement' rows existed across the whole table,
so a firing engine read as DEAD in saves. This is the observability gap behind
8 failed crossing attempts (2026-06-22 findings). Every movement emit site
(subsystem navigator, region-mode defer, unresolved, narration_apply, AND both
seam resolvers — incl. the real ropefoot->entrance crossing) flows through the
3 context managers, so mirror to the sink there via the existing SPAN_ROUTES
extract — one choke point, no per-site drift.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Bug A — deny narrator region-writes in region-mode/seam worlds

Every descend turn the narrator calls the `apply_world_patch` escape hatch on `/current_region` — turn 1 it targeted `exp001.r0` while the engine targeted `entrance`. The engine won this run, but it is a live race that historically split the party (session 14812). The title-scrape path is ALREADY fenced for region-mode worlds (`region.entry_rejected: sub_location_in_region_mode_world`); the remaining hole is the TOOL. Deny `/current_region` in the tool's allowlist when the world is region-mode. Reuse the EXACT predicate `narration_apply.py` already uses (`cartography.navigation_mode == NavigationMode.region`) — do not invent a new one.

**Files:**
- Modify: `sidequest/agents/tools/apply_world_patch.py` (region-mode guard before the patch dispatch)
- Test: `tests/agents/tools/test_apply_world_patch.py` (add cases; create file if absent)

**Interfaces:**
- Consumes: `ctx.repository.load().snapshot` (already in the tool). Needs pack+world cartography to detect region-mode. The snapshot carries `world_slug`; the pack is reachable via `ctx` — confirm the accessor in `ToolContext` (the narrator tools already read pack-derived data; follow the existing accessor on `ctx`). The predicate, copied verbatim from `narration_apply.py:4218`:
  ```python
  from sidequest.genre.models.world import NavigationMode
  is_region_mode = (cart is not None
      and getattr(cart, "navigation_mode", None) == NavigationMode.region)
  ```
- Produces: a recoverable error (NOT fatal) when `/current_region` is written in a region-mode world — the narrator re-plans, the engine owns the region. Mirrors the existing unsupported-path rejection (`ToolResult.error(..., recoverable=True)`).

- [ ] **Step 1: Write the failing test**

Add to `tests/agents/tools/test_apply_world_patch.py` (create if it does not exist). Construct a region-mode world snapshot + a non-region world snapshot via the existing tool-test fixtures (follow the patterns already used by other `tests/agents/tools/` tests for building `ToolContext`).

```python
import pytest
from sidequest.agents.tools.apply_world_patch import apply_world_patch, ApplyWorldPatchArgs


@pytest.mark.asyncio
async def test_current_region_denied_in_region_mode_world(region_mode_tool_ctx):
    """Bug A: the narrator's escape hatch must not write /current_region in a
    region-mode/seam world — the engine owns the region there. Recoverable
    rejection (the narrator re-plans), NOT a fatal abort."""
    res = await apply_world_patch(
        ApplyWorldPatchArgs(path="/current_region", value="exp001.r0",
                            reason="narrator tries to set region"),
        region_mode_tool_ctx,
    )
    assert res.is_error
    assert res.recoverable is True
    assert "region-mode" in res.error.lower() or "engine" in res.error.lower()
    # and the snapshot's current_region is unchanged
    assert region_mode_tool_ctx.repository.load().snapshot.current_region != "exp001.r0"


@pytest.mark.asyncio
async def test_current_region_allowed_in_non_region_world(plain_tool_ctx):
    """Non-region-mode worlds keep the existing /current_region escape hatch."""
    res = await apply_world_patch(
        ApplyWorldPatchArgs(path="/current_region", value="the_market",
                            reason="ordinary region set"),
        plain_tool_ctx,
    )
    assert not res.is_error


@pytest.mark.asyncio
async def test_location_still_allowed_in_region_mode_world(region_mode_tool_ctx):
    """The denial is scoped to /current_region — /location (scene heading) is
    still a legitimate narrator write in a region-mode world."""
    res = await apply_world_patch(
        ApplyWorldPatchArgs(path="/location", value="The Dropmouth — First Chamber",
                            reason="scene heading"),
        region_mode_tool_ctx,
    )
    assert not res.is_error
```

- [ ] **Step 2: Run to confirm failure**

Run:
```bash
cd sidequest-server && uv run pytest tests/agents/tools/test_apply_world_patch.py -v -n0
```
Expected: FAIL — `test_current_region_denied_in_region_mode_world` (today the tool writes `/current_region` unconditionally). The other two should already pass (guarding the scope).

- [ ] **Step 3: Add the region-mode guard**

In `sidequest/agents/tools/apply_world_patch.py`, after `field_name = _SUPPORTED_PATHS.get(args.path)` and the OTEL attribute writes, before the `if field_name is None:` rejection, add the scoped denial. Resolve cartography from the pack+world the same way `narration_apply` does:

```python
    # Bug A (2026-06-22 findings): in a region-mode/seam world the ENGINE owns
    # current_region (the movement subsystem crosses the static→procedural seam
    # engine-first, ADR-113). The narrator writing /current_region here is a live
    # race that historically split the party (session 14812). The title-scrape
    # path is already fenced (region.entry_rejected: sub_location_in_region_mode_world);
    # this closes the matching hole in the escape-hatch TOOL. Scoped to
    # /current_region — /location, /time_of_day, /atmosphere stay open. Recoverable:
    # the narrator re-plans, it does not abort the turn.
    if args.path == "/current_region":
        from sidequest.genre.models.world import NavigationMode

        world_obj = ctx.pack.worlds.get(snapshot.world_slug) if ctx.pack is not None else None
        cart = getattr(world_obj, "cartography", None) if world_obj is not None else None
        if cart is not None and getattr(cart, "navigation_mode", None) == NavigationMode.region:
            ctx.otel_span.set_attribute("tool.world_patch.region_write_denied", True)
            return ToolResult.error(
                "path '/current_region' is engine-owned in a region-mode world; "
                "the movement subsystem crosses the seam engine-first. The narrator "
                "must not set the region here — narrate the descent in prose instead.",
                recoverable=True,
            )
```

If `ctx` does not expose `.pack`, use the accessor the other narrator tools use to reach the pack/world (grep `tests/agents/tools/` and a sibling tool such as `apply_damage.py` for the `ToolContext` field name; thread it the same way). The predicate itself is fixed; only the cartography accessor adapts to `ToolContext`.

- [ ] **Step 4: Run to confirm pass**

Run:
```bash
cd sidequest-server && uv run pytest tests/agents/tools/test_apply_world_patch.py -v -n0
```
Expected: PASS (all three).

- [ ] **Step 5: Format + commit**

```bash
cd sidequest-server && uv run ruff format sidequest/agents/tools/apply_world_patch.py tests/agents/tools/test_apply_world_patch.py && uv run ruff check sidequest/agents/tools/apply_world_patch.py
git add sidequest/agents/tools/apply_world_patch.py tests/agents/tools/test_apply_world_patch.py
git commit -m "fix(narrator): deny apply_world_patch /current_region in region-mode worlds

The escape-hatch tool wrote /current_region every descend turn, racing the
engine seam crossing (session 14812 split the party). The title-scrape path was
already fenced for region-mode worlds; this closes the matching hole in the TOOL
with the same NavigationMode.region predicate. Scoped to /current_region;
recoverable rejection (narrator re-plans).

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Bug B — expand the current node's ring before declaring `no_candidate_edges`

At `exp002.r2` the engine reported `no_candidate_edges from=exp002.r2 direction=deeper` though the narrator described four exits. Root cause: turn 2 jumped `entrance → exp002.r2` via `descriptor_fallback_depth_delta` (skipping `exp001`), so the next ring around `exp002.r2` was never materialized — `project_region(graph, "exp002.r2", palette)` yields zero exits, and the `if not candidates:` guard (`movement.py:612`) fails loud. The lookahead must keep ahead of the descent: when the current node has no projected exits but the frontier rooted there has unmaterialized edges, sync-expand that ring and re-project before failing. Model on the existing §Q3 `_sync_materialize` (`movement.py:959`), which already reuses the worker's `_materialize_edge` path.

**Files:**
- Modify: `sidequest/agents/subsystems/movement.py` (new `_sync_expand_ring` helper + use at the `not candidates` guard ~line 612)
- Test: `tests/agents/subsystems/test_movement_lookahead_depth.py` (create)

**Interfaces:**
- Consumes: `_sync_materialize`'s building blocks — `dungeon_store.load_frontier()` (→ frontier edges with `.from_region_id`), `lookahead_handle._materialize_edge(...)`, `dungeon_store.load_map(entrance_id=_ENTRANCE_ID)`. `project_region(graph, from_region, palette) -> proj` (`.exits`).
- Produces: `_sync_expand_ring(*, lookahead_handle, dungeon_store, from_region, snapshot) -> bool` — materializes ALL frontier edges rooted at `from_region`, returns True iff at least one new node was added. Used only to recover from an empty projection; never moves the PC itself.

- [ ] **Step 1: Confirm which guard fires (instrument, don't guess)**

Run the live repro and read the spans (from Jaeger jsonl, NOT turn_telemetry):
```bash
cd sidequest-server && uv run --with rich --with pillow python3 ../scripts/playtest.py \
  --scenario ../scenarios/sunden_descend_trace.yaml --span-jsonl /tmp/sunden_descend.spans.jsonl --fresh
```
Confirm the failing span is `movement.unresolved reason=no_candidate_edges from=exp002.r2`. Then confirm in code whether it is the `if not candidates:` branch (`movement.py:612`, empty projection) or the `if resolved is None:` branch (`movement.py:648`, candidates existed but `_resolve` matched none). The fix below targets the empty-projection branch (612); if (and only if) the firing branch is 648, the candidates exist and the fix is in `_resolve`'s `deeper` matching instead — note that and adjust the test target accordingly.

- [ ] **Step 2: Write the failing test**

Create `tests/agents/subsystems/test_movement_lookahead_depth.py`. Build a dungeon kit whose current region (`exp002.r2`) has NO materialized exits but DOES have a frontier edge rooted there (model on `_StoreWithDeepGraph` / `_StoreWithEntrance` in `test_movement_seam_crossing.py`; add a store variant `_StoreWithUnexpandedRing` whose `load_map` returns `exp002.r2` with no out-edges and whose `load_frontier` returns one edge `exp002.r2 -> exp003.rN`).

```python
"""Bug B (2026-06-22 findings): the engine ran dry one room deeper. After a
depth-delta jump to exp002.r2, that node's ring was never materialized, so
'deeper' resolved to no_candidate_edges while the narrator improvised four
exits. The engine must expand the current node's ring before failing loud."""
from tests.agents.subsystems.test_movement_seam_crossing import _run, _movement


def test_deeper_expands_current_ring_then_resolves(capture_spans, unexpanded_ring_kit):
    kit = unexpanded_ring_kit
    out = _run(
        run_movement_dispatch(
            _movement("deeper", "press deeper"),
            snapshot=kit.snapshot,
            player_name="Groucho",
            dungeon_store=kit.store,
            palette=kit.palette,
            pack=kit.pack,
            lookahead_handle=kit.lookahead_handle,
        )
    )
    # The ring is expanded and the move resolves — NOT no_candidate_edges.
    assert out.data.get("resolved_via") not in (None,), out.data
    unresolved = [s for s in capture_spans.get_finished_spans()
                  if s.name == "movement.unresolved"]
    assert not unresolved, f"engine ran dry instead of expanding the ring: {[s.attributes for s in unresolved]}"
```

- [ ] **Step 3: Run to confirm failure**

Run:
```bash
cd sidequest-server && uv run pytest tests/agents/subsystems/test_movement_lookahead_depth.py -v -n0
```
Expected: FAIL — `movement.unresolved` fires with `reason=no_candidate_edges` (the ring is never expanded).

- [ ] **Step 4: Add the ring-expansion helper**

In `sidequest/agents/subsystems/movement.py`, add next to `_sync_materialize`:

```python
async def _sync_expand_ring(
    *,
    lookahead_handle: LookaheadWorkerHandle | None,
    dungeon_store: DungeonStore,
    from_region: str,
    snapshot: GameSnapshot,
) -> bool:
    """Materialize EVERY frontier edge rooted at ``from_region`` so the current
    node's outgoing ring exists BEFORE we resolve a move from it.

    Bug B (2026-06-22): a depth-delta jump can land the PC on a node whose ring
    was never materialized (the lookahead fell behind the descent). Rather than
    fail loud with no_candidate_edges on a node the narrator is actively
    describing exits from, expand the ring here and let the caller re-project.
    Returns True iff the materialized map grew. Reuses the worker's own
    ``_materialize_edge`` path (no parallel materialize mechanism), mirroring
    ``_sync_materialize``. NOT a silent fallback: if expansion adds nothing the
    caller STILL fails loud — this only recovers a genuinely-unexpanded ring.
    """
    if lookahead_handle is None:
        return False
    before = len(dungeon_store.load_map(entrance_id=_ENTRANCE_ID).nodes)
    rooted = [fe for fe in dungeon_store.load_frontier() if fe.from_region_id == from_region]
    for fe in rooted:
        try:
            await lookahead_handle._materialize_edge(fe, snapshot=snapshot)  # noqa: SLF001 — one worker path
        except Exception:  # noqa: BLE001 — one bad edge must not abort the whole ring
            logger.warning("movement.ring_expand_edge_failed from=%s edge=%r", from_region, fe, exc_info=True)
    after = len(dungeon_store.load_map(entrance_id=_ENTRANCE_ID).nodes)
    return after > before
```

Confirm `_materialize_edge`'s exact parameters against `_sync_materialize`'s call at `movement.py:983` and match them (the frontier-edge object + `snapshot`); adjust the call above to the real signature.

- [ ] **Step 5: Use it at the empty-projection guard**

Replace the `if not candidates:` block at `movement.py:612` so it expands the ring and re-projects ONCE before failing loud:

```python
    if not candidates:
        # Bug B: the current node's ring may simply be unmaterialized (a
        # depth-delta jump outran the lookahead). Expand it once and re-project
        # before failing loud — the narrator is describing real exits here.
        grew = await _sync_expand_ring(
            lookahead_handle=lookahead_handle,
            dungeon_store=dungeon_store,
            from_region=from_region,
            snapshot=snapshot,
        )
        if grew:
            graph = dungeon_store.load_map(entrance_id=_ENTRANCE_ID)
            proj = project_region(graph, from_region, palette)
            candidates = [
                e for e in proj.exits if (not e.hidden) or (e.to_region_id in discovered_routes)
            ]
            available_ids = [e.to_region_id for e in candidates]
    if not candidates:
        return _unresolved(
            snapshot=snapshot,
            player_name=player_name,
            reason="no_candidate_edges",
            from_region=from_region,
            direction=direction,
            exit_descriptor=exit_descriptor,
            available=available_ids,
            surface=f"{player_name} finds no such way from here.",
        )
```

(Confirm `graph` is the variable holding the loaded map in scope above line 602's `project_region(graph, ...)`; reload it from `dungeon_store.load_map` after expansion so the new nodes are visible.)

- [ ] **Step 6: Run to confirm pass**

Run:
```bash
cd sidequest-server && uv run pytest tests/agents/subsystems/test_movement_lookahead_depth.py tests/agents/subsystems/test_movement_seam_crossing.py -v -n0
```
Expected: PASS (ring expands and resolves; crossing tests still green).

- [ ] **Step 7: Format + commit**

```bash
cd sidequest-server && uv run ruff format sidequest/agents/subsystems/movement.py tests/agents/subsystems/test_movement_lookahead_depth.py && uv run ruff check sidequest/agents/subsystems/movement.py
git add sidequest/agents/subsystems/movement.py tests/agents/subsystems/test_movement_lookahead_depth.py
git commit -m "fix(dungeon): expand the current node's ring before no_candidate_edges

A depth-delta jump (entrance -> exp002.r2, skipping exp001) outran the lookahead,
so 'deeper' from exp002.r2 hit an unmaterialized ring and the engine ran dry while
the narrator improvised four exits. Sync-expand the frontier rooted at the current
region and re-project once before failing loud (No Silent Fallbacks: still fails
if expansion adds nothing). Models the existing §Q3 _sync_materialize.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Live end-to-end verification + mark the superseded notes

Prove the whole crossing is now observable in saves (not just Jaeger), then close out the two wrong design notes so attempt #9 never starts from them.

**Files:**
- Modify: `docs/superpowers/specs/2026-06-21-location-single-authority-design.md` (SUPERSEDED banner)
- Modify: `docs/superpowers/specs/2026-06-22-static-procedural-crossing-design.md` (SUPERSEDED banner)

- [ ] **Step 1: Restart the server on the new branch and run the live trace**

Server must be restarted (the running process holds attempt #8's loaded code; this branch adds Tasks 2–4). From the orchestrator root with the server rebooted on `feat/sunden-crossing-land-and-observe`:
```bash
cd sidequest-server && uv run --with rich --with pillow python3 ../scripts/playtest.py \
  --scenario ../scenarios/sunden_descend_trace.yaml --span-jsonl /tmp/sunden_descend.spans.jsonl --fresh
```
Expected: turn 1 `movement.resolved ropefoot → entrance resolved_via=surface_descent_adjacent`; turn 3 resolves (no `dispatch_engagement.movement.mismatch`).

- [ ] **Step 2: Confirm movement now lands in turn_telemetry (the Task 2 proof)**

Query `turn_telemetry` for the new session and assert `component='movement'` rows exist (the whole point — these were ZERO before):
```bash
psql "$SIDEQUEST_DATABASE_URL" -c "select component, event_type, payload->>'op' as op from turn_telemetry where component='movement' order by id desc limit 10;"
```
Expected: ≥1 `movement` row (`movement.resolved` / `movement.unresolved`). If empty, Task 2 is not wired — stop and fix before claiming done.

- [ ] **Step 3: Confirm no parallel narrator region-write (the Task 3 proof)**

In the jsonl, confirm turn 1 has NO `tool.write.apply_world_patch path=/current_region` succeeding (it should now be `region_write_denied`), and the DB ledger shows `ropefoot → entrance` via the engine.

- [ ] **Step 4: Mark the two superseded notes**

Add to the very top of BOTH `docs/superpowers/specs/2026-06-21-location-single-authority-design.md` and `docs/superpowers/specs/2026-06-22-static-procedural-crossing-design.md`:

```markdown
> **⚠️ SUPERSEDED / WRONG — DO NOT FOLLOW.** Reasoned from saves and code, not a
> live run; wrong on the central facts. Superseded by
> `2026-06-22-sunden-crossing-FINDINGS.md` and implemented by
> `../plans/2026-06-22-sunden-crossing.md`. Kept for history only.
```

- [ ] **Step 5: Commit the doc hygiene (orchestrator repo, targets `main`)**

```bash
cd /Users/slabgorb/Projects/oq-3 && git add docs/superpowers/specs/2026-06-21-location-single-authority-design.md docs/superpowers/specs/2026-06-22-static-procedural-crossing-design.md docs/superpowers/plans/2026-06-22-sunden-crossing.md
git commit -m "docs(plan): sünden crossing — land #8 + observe + 2 narrow bugs; mark wrong notes SUPERSEDED

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 6: Push the server branch + open the PR (targets develop)**

```bash
cd sidequest-server && git pull --rebase origin develop && git push -u origin feat/sunden-crossing-land-and-observe
gh pr create -R slabgorb-org/sidequest-server --base develop \
  --title "fix(dungeon): land the sünden surface→procedural crossing + make movement observable" \
  --body "Lands attempt #8 (surface_descent_adjacent), routes movement into turn_telemetry (the observability gap behind 8 attempts), denies the narrator /current_region race in region-mode worlds, and expands the current ring before no_candidate_edges. Diagnosis: docs/superpowers/specs/2026-06-22-sunden-crossing-FINDINGS.md. Plan: docs/superpowers/plans/2026-06-22-sunden-crossing.md."
```

---

## Self-Review

**Spec coverage** (against the FINDINGS doc "narrow path forward"):
1. Keep/merge attempt #8 → **Task 1** (cherry-pick `711365e0`). ✓
2. Bug A — scoped region-write denial on `apply_world_patch` → **Task 3**. ✓
3. Bug B — lookahead keeps ahead of the descent → **Task 4**. ✓
4. Telemetry gap — movement → `turn_telemetry` via `publish_event` → **Task 2**. ✓
5. Scope discipline — no single-authority, no `narration_apply` surgery, no oz/wonderland/gulliver/orbital touch → honored (each task is one telemetry-span file / movement subsystem / one tool / two doc banners). ✓

**Placeholder scan:** Task 3's `ctx` pack accessor and Task 4's `_materialize_edge` signature are the two spots where the dev confirms an exact accessor/signature against a named sibling (`narration_apply.py:4218` predicate is fixed; only the accessor adapts). These are "confirm against this exact reference," not "figure it out" — acceptable, and flagged inline. No TBD/TODO/"handle edge cases" left.

**Type consistency:** Task 2's `_mirror_movement_span_to_sink` reuses each span's `SPAN_ROUTES[name].extract`/`.event_type`/`.component` verbatim — no hand-listed field set to drift. `seam_route_via_adjacency` signature matches Task 1's cherry-picked code. `_sync_expand_ring` mirrors `_sync_materialize`'s `(lookahead_handle, dungeon_store, from_region, snapshot)` shape.

**Ordering rationale:** Task 2 (telemetry) lands BEFORE Bugs A/B so every later fix is verifiable from saves, not just live Jaeger — directly answering the 8-attempt blind spot.

**Pre-flight findings (resolved before execution):** (1) PR #1029 (lateral mover) is NOT in `develop`, so `movement.py:450` does not exist on this branch — Task 2's choke-point design is immune (it never references that site). (2) The actual crossing span is emitted in `seams/deep_descent.py`, not the movement subsystem — Task 2's original per-site enumeration would have missed it; the choke-point design covers it. Both are why Task 2 was rewritten from per-site to the 3-context-manager mirror.
