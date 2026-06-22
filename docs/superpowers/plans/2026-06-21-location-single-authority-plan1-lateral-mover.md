# Location Single-Authority — Plan 1: Engine-Authoritative Lateral Region Travel

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give region-mode worlds an engine-authoritative mover for *lateral* cartography travel (oz: `munchkin_country → the_emerald_city`; beneath_sünden surface: `ropefoot → the_dropmouth`), so the engine — not the narrator's parsed scene title — resolves the move and emits a `movement.resolved` OTEL span.

**Architecture:** Add a deterministic cartography-adjacency resolver to the `movement` subsystem's region-mode block, mirroring the existing §Q1 procedural room-graph navigator. It matches the player's `exit_descriptor` against the current region's `adjacent` neighbors and crosses through the **existing** per-PC chokepoint `snapshot.apply_world_patch(WorldStatePatch(pc_region={pc: target}))`. This is purely **additive** — it does not yet remove the narration title-scrape (that is Plan 2). It resolves what it can and falls back to the existing `region_mode_deferred` for everything else, so there is zero regression risk.

**Tech Stack:** Python 3 / FastAPI server (`sidequest-server`), pytest (`-n0` for serial OTEL-span tests), OpenTelemetry in-memory span capture, `uv` runner.

## Global Constraints

- **Region-mode only.** This code path is gated behind `_is_region_mode(cart)` (`cartography.navigation_mode == NavigationMode.region`). Room-graph / dungeon worlds are untouched. (verbatim: `movement.py:208 _is_region_mode`)
- **The chokepoint is the only writer.** Region changes go through `snapshot.apply_world_patch(WorldStatePatch(pc_region={player_name: target_id}))`. **Never** assign `snapshot.current_region` or `snapshot.pc_regions[...]` directly. (verbatim invariant: `session.py:1600` "Movement NEVER sets `current_region`; it sets `pc_region`.")
- **No Silent Fallbacks.** A genuinely ambiguous lateral intent fails loud via `_unresolved(..., reason="ambiguous_region_exit", ...)`. The resolver never guesses which neighbor was meant.
- **OTEL on every decision.** A successful lateral cross emits exactly one `movement.resolved` span with `resolved_via="region_lateral"` and `edge_kind="cartography_adjacent"`. (CLAUDE.md OTEL Observability Principle — the GM panel is the lie detector.)
- **Additive, not subtractive.** This plan removes nothing. On no-match it returns the existing `_defer_region_mode(...)` so non-travel intents and unmatched moves behave exactly as today.
- **Run OTEL-span tests serially.** `uv run pytest -n0 ...` for any test that asserts span counts (see memory: full parallel `tests/server/` OTEL runs can deadlock; movement tests are in `tests/agents/` but keep span tests `-n0` for determinism).

---

## File Structure

- `sidequest/agents/subsystems/movement.py` — **Modify.** Add the pure helper `_resolve_cartography_lateral(...)` near the other resolvers (after `_resolve`, ~line 810). Wire it into `run_movement_dispatch`'s region-mode block, replacing the bare `_defer_region_mode` return at the `if not _in_dungeon:` branch (~line 416).
- `tests/agents/subsystems/test_movement_lateral.py` — **Create.** Unit tests for the pure helper + dispatch-level integration tests, reusing the fixture conventions in the sibling `test_movement_seam_crossing.py`.

Both files change together (resolver + its wiring + its tests) and live in the same subsystem. No other files are touched in Plan 1.

---

## Task 1: The pure cartography-lateral resolver

A deterministic, side-effect-free function that picks the adjacent region a lateral intent names — or reports ambiguity / no-match. Splitting it from the wiring (Task 2) lets a reviewer judge the matching algorithm in isolation.

**Files:**
- Modify: `sidequest/agents/subsystems/movement.py` (add function after `_resolve`, which ends ~line 810)
- Test: `tests/agents/subsystems/test_movement_lateral.py` (create)

**Interfaces:**
- Consumes: `_tokens(text: str) -> set[str]` (existing helper in `movement.py`, used by `_resolve` at line 706); the `CartographyConfig` model from `sidequest.genre.models.world` whose `.regions` is `dict[str, Region]` and each `Region` has `.name: str` and `.adjacent: list[str]`.
- Produces: `_resolve_cartography_lateral(*, cart, from_region: str, exit_descriptor: str, direction: str, discovered_regions: list[str]) -> tuple[str | None, str, bool, list[str], str]` returning `(target_id, resolved_via, ambiguous, candidate_ids, surface)`. This signature is consumed by Task 2.

- [ ] **Step 1: Write the failing unit tests**

Create `tests/agents/subsystems/test_movement_lateral.py`:

```python
"""Engine-authoritative lateral cartography travel (region-mode worlds).

Plan 1 of the location single-authority effort. The movement subsystem
resolves a lateral region-to-region move (oz: munchkin_country ->
the_emerald_city) against the cartography adjacency graph, instead of
deferring it to the narration title-scrape. Additive: unmatched intents
still defer.
"""

from __future__ import annotations

import asyncio
import types

import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

import sidequest.telemetry.spans as spans_module
from sidequest.agents.subsystems.movement import (
    _resolve_cartography_lateral,
    run_movement_dispatch,
)
from sidequest.game.session import GameSnapshot
from sidequest.genre.models.world import CartographyConfig, NavigationMode, Region, Route
from sidequest.protocol.dispatch import SubsystemDispatch, VisibilityTag


def _oz_cartography_with_road() -> CartographyConfig:
    """oz-shaped region-mode world with TWO adjacent regions and no seam."""
    return CartographyConfig(
        starting_region="munchkin_country",
        navigation_mode=NavigationMode.region,
        regions={
            "munchkin_country": Region(
                name="Munchkin Country",
                summary="The land of the Munchkins.",
                description="A cheerful pastoral region.",
                adjacent=["the_emerald_city"],
            ),
            "the_emerald_city": Region(
                name="The Emerald City",
                summary="The green capital.",
                description="The Wizard's city.",
                adjacent=["munchkin_country"],
            ),
        },
        routes=[
            Route(
                name="Yellow Brick Road",
                description="The road to the Emerald City.",
                from_id="munchkin_country",
                to_id="the_emerald_city",  # NOT a registered seam kind
            ),
        ],
    )


def test_lateral_resolver_matches_named_neighbor():
    cart = _oz_cartography_with_road()
    target, via, ambiguous, candidates, surface = _resolve_cartography_lateral(
        cart=cart,
        from_region="munchkin_country",
        exit_descriptor="head to the Emerald City",
        direction="deeper",
        discovered_regions=["munchkin_country"],
    )
    assert target == "the_emerald_city"
    assert via == "region_lateral"
    assert ambiguous is False
    assert candidates == ["the_emerald_city"]


def test_lateral_resolver_no_overlap_is_no_match():
    cart = _oz_cartography_with_road()
    target, via, ambiguous, _candidates, _surface = _resolve_cartography_lateral(
        cart=cart,
        from_region="munchkin_country",
        exit_descriptor="I sit down and rest",
        direction="deeper",
        discovered_regions=["munchkin_country"],
    )
    assert target is None
    assert ambiguous is False


def test_lateral_resolver_back_uses_recency():
    cart = _oz_cartography_with_road()
    # PC is in the_emerald_city, came from munchkin_country (in discovered).
    target, via, ambiguous, _candidates, _surface = _resolve_cartography_lateral(
        cart=cart,
        from_region="the_emerald_city",
        exit_descriptor="",
        direction="back",
        discovered_regions=["munchkin_country", "the_emerald_city"],
    )
    assert target == "munchkin_country"
    assert via == "region_back"
    assert ambiguous is False


def test_lateral_resolver_ambiguous_two_way_tie_fails_loud():
    cart = CartographyConfig(
        starting_region="crossroads",
        navigation_mode=NavigationMode.region,
        regions={
            "crossroads": Region(
                name="Crossroads",
                summary="A fork.",
                description="Two green roads diverge.",
                adjacent=["green_hill", "green_dale"],
            ),
            "green_hill": Region(name="Green Hill", summary="", description=""),
            "green_dale": Region(name="Green Dale", summary="", description=""),
        },
        routes=[],
    )
    target, _via, ambiguous, _candidates, surface = _resolve_cartography_lateral(
        cart=cart,
        from_region="crossroads",
        exit_descriptor="the green way",  # 'green' ties both neighbors
        direction="deeper",
        discovered_regions=["crossroads"],
    )
    assert target is None
    assert ambiguous is True
    assert "Which way?" in surface


def test_lateral_resolver_no_adjacency_is_no_match():
    cart = CartographyConfig(
        starting_region="island",
        navigation_mode=NavigationMode.region,
        regions={"island": Region(name="Island", summary="", description="")},
        routes=[],
    )
    target, _via, ambiguous, candidates, _surface = _resolve_cartography_lateral(
        cart=cart,
        from_region="island",
        exit_descriptor="anywhere",
        direction="deeper",
        discovered_regions=["island"],
    )
    assert target is None
    assert ambiguous is False
    assert candidates == []
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd sidequest-server && uv run pytest -n0 tests/agents/subsystems/test_movement_lateral.py -k "lateral_resolver" -v`
Expected: FAIL — `ImportError: cannot import name '_resolve_cartography_lateral'`.

- [ ] **Step 3: Implement the pure resolver**

In `sidequest/agents/subsystems/movement.py`, add this function immediately after `_resolve` (which ends at line ~810, the `return None, "depth_delta", False` line):

```python
def _resolve_cartography_lateral(
    *,
    cart,
    from_region: str,
    exit_descriptor: str,
    direction: str,
    discovered_regions: list[str],
) -> tuple[str | None, str, bool, list[str], str]:
    """Resolve a LATERAL region-mode move against the current region's
    cartography neighbors. Returns (target_id, resolved_via, ambiguous,
    candidate_ids, surface).

    The cartography-graph twin of ``_resolve`` (which resolves the procedural
    room graph). The router emits only coarse directions
    (deeper/back/toward_exit) plus the player's verbatim ``exit_descriptor``;
    a lateral move carries its target in the descriptor (oz: "head to the
    Emerald City"). Match the descriptor's tokens against each adjacent
    region's id + display name; a unique top score wins, a top-2 tie is
    ambiguous (fail loud), no overlap is a no-match (caller defers — this is
    additive, Plan 1). ``back`` with no descriptor resolves to the
    most-recently-prior discovered neighbor. NEVER guesses (No Silent
    Fallbacks).
    """
    region = getattr(cart, "regions", {}).get(from_region)
    if region is None:
        return None, "region_lateral", False, [], ""
    candidate_ids = sorted(n for n in (getattr(region, "adjacent", ()) or []))
    if not candidate_ids:
        return None, "region_lateral", False, [], ""

    # "back" with no descriptor → most-recently-prior discovered neighbor.
    if direction == "back" and not exit_descriptor.strip():
        recency = {rid: i for i, rid in enumerate(discovered_regions)}
        prior = [c for c in candidate_ids if c in recency]
        if prior:
            prior.sort(key=lambda c: -recency[c])
            return prior[0], "region_back", False, candidate_ids, ""
        return None, "region_lateral", False, candidate_ids, ""

    if not exit_descriptor.strip():
        return None, "region_lateral", False, candidate_ids, ""

    want = _tokens(exit_descriptor)
    scored: list[tuple[int, str]] = []
    regions_map = getattr(cart, "regions", {})
    for cid in candidate_ids:
        neighbor = regions_map.get(cid)
        surface_tokens = _tokens(cid)
        if neighbor is not None:
            surface_tokens = surface_tokens | _tokens(str(getattr(neighbor, "name", "") or ""))
        score = len(want & surface_tokens)
        if score > 0:
            scored.append((score, cid))
    if not scored:
        return None, "region_lateral", False, candidate_ids, ""
    scored.sort(key=lambda s: (-s[0], s[1]))
    if len(scored) >= 2 and scored[0][0] == scored[1][0]:
        ways = ", ".join(
            str(getattr(regions_map.get(cid), "name", cid) or cid) for _, cid in scored
        )
        return (
            None,
            "region_lateral",
            True,
            candidate_ids,
            f"{from_region} could go more than one way: {ways}. Which way?",
        )
    return scored[0][1], "region_lateral", False, candidate_ids, ""
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd sidequest-server && uv run pytest -n0 tests/agents/subsystems/test_movement_lateral.py -k "lateral_resolver" -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Lint + format the touched files**

Run: `cd sidequest-server && uv run ruff check sidequest/agents/subsystems/movement.py tests/agents/subsystems/test_movement_lateral.py && uv run ruff format sidequest/agents/subsystems/movement.py tests/agents/subsystems/test_movement_lateral.py`
Expected: clean (no errors; format leaves files unchanged or reformats only the new lines).

- [ ] **Step 6: Commit**

```bash
cd sidequest-server
git add sidequest/agents/subsystems/movement.py tests/agents/subsystems/test_movement_lateral.py
git commit -m "feat(movement): pure cartography-lateral resolver (region-mode adjacency)"
```

---

## Task 2: Wire the lateral resolver into the dispatch (engine crosses, emits span)

Insert the resolver into `run_movement_dispatch`'s region-mode block so a matched lateral intent crosses via the chokepoint and emits a `movement.resolved` span. Unmatched intents still defer (additive). A reviewer could accept Task 1's matcher but reject this wiring (placement, span shape, defer fallback), so it is its own task.

**Files:**
- Modify: `sidequest/agents/subsystems/movement.py` (the `if not _in_dungeon:` branch in the region-mode block, currently lines 416-423)
- Test: `tests/agents/subsystems/test_movement_lateral.py` (add dispatch-level tests)

**Interfaces:**
- Consumes: `_resolve_cartography_lateral(...)` (Task 1); the existing `movement_resolved_span(pc_name, from_region, to_region)` context manager (`movement.py` imports it from `sidequest.telemetry.spans`); `_unresolved(...)`, `_defer_region_mode(...)`, `WorldStatePatch`, `SubsystemOutput` (all in scope in `movement.py`).
- Produces: a `movement.resolved` span with `resolved_via="region_lateral"` / `edge_kind="cartography_adjacent"`, and a `SubsystemOutput(data={"to_region", "from_region", "resolved_via"})`.

- [ ] **Step 1: Write the failing dispatch tests**

Append to `tests/agents/subsystems/test_movement_lateral.py`:

```python
def _run(coro):
    return asyncio.run(coro)


def _movement(direction: str, descriptor: str = "") -> SubsystemDispatch:
    return SubsystemDispatch(
        subsystem="movement",
        params={"direction": direction, "exit_descriptor": descriptor},
        idempotency_key="mv-lateral",
        confidence=1.0,
        visibility=VisibilityTag(visible_to="all"),
    )


def _pack_with_cartography(world_slug: str, cartography: CartographyConfig):
    world = types.SimpleNamespace(cartography=cartography)
    return types.SimpleNamespace(worlds={world_slug: world})


@pytest.fixture
def capture_spans(monkeypatch):
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    local = provider.get_tracer("test-movement-lateral")
    monkeypatch.setattr(spans_module, "tracer", lambda: local)
    return exporter


def test_dispatch_lateral_move_crosses_engine_side(capture_spans):
    cart = _oz_cartography_with_road()
    pack = _pack_with_cartography("oz", cart)
    snap = GameSnapshot(
        genre_slug="wry_whimsy",
        world_slug="oz",
        pc_regions={"Dorothy": "munchkin_country"},
        player_seats={"p1": "Dorothy"},
    )
    out = _run(
        run_movement_dispatch(
            _movement("deeper", "follow the road to the Emerald City"),
            snapshot=snap,
            player_name="Dorothy",
            dungeon_store=None,
            palette=None,
            pack=pack,
        )
    )
    assert out.data["resolved_via"] == "region_lateral", out.data
    assert out.data["to_region"] == "the_emerald_city"
    assert snap.region_for(perspective="Dorothy") == "the_emerald_city", (
        "engine must move the PC via apply_world_patch, not defer to narration"
    )
    resolved = [s for s in capture_spans.get_finished_spans() if s.name == "movement.resolved"]
    assert len(resolved) == 1
    attrs = resolved[0].attributes or {}
    assert attrs["resolved_via"] == "region_lateral"
    assert attrs["edge_kind"] == "cartography_adjacent"


def test_dispatch_unmatched_lateral_still_defers(capture_spans):
    cart = _oz_cartography_with_road()
    pack = _pack_with_cartography("oz", cart)
    snap = GameSnapshot(
        genre_slug="wry_whimsy",
        world_slug="oz",
        pc_regions={"Dorothy": "munchkin_country"},
        player_seats={"p1": "Dorothy"},
    )
    out = _run(
        run_movement_dispatch(
            _movement("deeper", "I look around the meadow"),
            snapshot=snap,
            player_name="Dorothy",
            dungeon_store=None,
            palette=None,
            pack=pack,
        )
    )
    assert out.data["resolved_via"] == "region_mode_deferred", out.data
    assert snap.region_for(perspective="Dorothy") == "munchkin_country", (
        "an unmatched intent must not move the PC (additive: defer, don't fail)"
    )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd sidequest-server && uv run pytest -n0 tests/agents/subsystems/test_movement_lateral.py -k "dispatch_lateral or dispatch_unmatched" -v`
Expected: FAIL — `test_dispatch_lateral_move_crosses_engine_side` fails with `resolved_via == "region_mode_deferred"` (the move currently defers; the engine does not yet cross).

- [ ] **Step 3: Wire the resolver into the region-mode block**

In `sidequest/agents/subsystems/movement.py`, find this block (currently lines 416-424):

```python
        if not _in_dungeon:
            return _defer_region_mode(
                snapshot=snapshot,
                player_name=player_name,
                from_region=from_region,
                direction=direction,
                exit_descriptor=exit_descriptor,
            )
        # In-dungeon: fall through to the §Q1 navigator below.
```

Replace it with:

```python
        if not _in_dungeon:
            # --- Engine-authoritative lateral cartography travel (Plan 1). ---
            # A region-mode PC on a surface cartography region moving to an
            # ADJACENT region (oz: munchkin_country -> the_emerald_city). The
            # ONLY mover for this historically was the narration title-scrape
            # (narration_apply.location_update) — the fragile path that let the
            # narrator move the party. Resolve it engine-side against the
            # cartography adjacency graph and cross via the per-PC chokepoint,
            # exactly like the §Q1 dungeon navigator. ADDITIVE: an unmatched
            # intent still defers (the scrape remains the backstop until Plan 2
            # severs it); an AMBIGUOUS intent fails loud (No Silent Fallbacks).
            target_id, via, ambiguous, candidate_ids, surface = _resolve_cartography_lateral(
                cart=cart,
                from_region=from_region,
                exit_descriptor=exit_descriptor,
                direction=direction,
                discovered_regions=list(snapshot.discovered_regions or []),
            )
            if target_id is not None:
                snapshot.apply_world_patch(
                    WorldStatePatch(pc_region={player_name: target_id})
                )
                with movement_resolved_span(
                    pc_name=player_name,
                    from_region=from_region,
                    to_region=target_id,
                ) as span:
                    span.set_attribute("intent.direction", direction)
                    span.set_attribute("intent.exit_descriptor", exit_descriptor)
                    span.set_attribute("resolved_via", via)
                    span.set_attribute("candidate_exits", candidate_ids)
                    span.set_attribute("edge_kind", "cartography_adjacent")
                    span.set_attribute("party_split_after", snapshot.region_for() is None)
                logger.debug(
                    "movement.resolved pc=%s from=%s to=%s via=%s kind=cartography_adjacent",
                    player_name,
                    from_region,
                    target_id,
                    via,
                )
                return SubsystemOutput(
                    data={
                        "to_region": target_id,
                        "from_region": from_region,
                        "resolved_via": via,
                    }
                )
            if ambiguous:
                return _unresolved(
                    snapshot=snapshot,
                    player_name=player_name,
                    reason="ambiguous_region_exit",
                    from_region=from_region,
                    direction=direction,
                    exit_descriptor=exit_descriptor,
                    available=candidate_ids,
                    surface=surface,
                )
            # No lateral match (non-travel intent / flavor descriptor): defer to
            # the existing region-mode path (additive — Plan 1 removes nothing).
            return _defer_region_mode(
                snapshot=snapshot,
                player_name=player_name,
                from_region=from_region,
                direction=direction,
                exit_descriptor=exit_descriptor,
            )
        # In-dungeon: fall through to the §Q1 navigator below.
```

- [ ] **Step 4: Run the new dispatch tests to verify they pass**

Run: `cd sidequest-server && uv run pytest -n0 tests/agents/subsystems/test_movement_lateral.py -k "dispatch_lateral or dispatch_unmatched" -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Run the full lateral + seam-crossing suites for non-regression**

Run: `cd sidequest-server && uv run pytest -n0 tests/agents/subsystems/test_movement_lateral.py tests/agents/subsystems/test_movement_seam_crossing.py -v`
Expected: PASS — all Plan-1 tests green AND every existing `test_movement_seam_crossing.py` test still green. In particular `test_non_seam_region_mode_world_still_defers` stays green (its oz fixture has no `adjacent` neighbors → the lateral resolver returns no-match → defers) and `test_surface_adjacent_non_deeper_does_not_cross` stays green (descriptor "over to the board" matches no neighbor → defers).

- [ ] **Step 6: Lint, format, and commit**

```bash
cd sidequest-server
uv run ruff check sidequest/agents/subsystems/movement.py tests/agents/subsystems/test_movement_lateral.py
uv run ruff format sidequest/agents/subsystems/movement.py tests/agents/subsystems/test_movement_lateral.py
git add sidequest/agents/subsystems/movement.py tests/agents/subsystems/test_movement_lateral.py
git commit -m "feat(movement): engine-authoritative lateral region travel (region-mode adjacency, additive)"
```

---

## Self-Review (run against the design note)

1. **Spec coverage (design note §4.A "engine lateral mover"):** Task 1 builds the matcher; Task 2 wires it through the `apply_world_patch` chokepoint and emits the `movement.resolved` span. The design note's §4.A `resolved_via="region_lateral"` and the `ambiguous_region_exit` fail-loud (§8 OTEL table) are both implemented. ✅
2. **Placeholder scan:** every code step contains complete code; every test step has full test bodies and exact `uv run pytest` commands with expected PASS/FAIL. No "TBD"/"handle edge cases". ✅
3. **Type consistency:** `_resolve_cartography_lateral` returns `(target_id, resolved_via, ambiguous, candidate_ids, surface)` in Task 1 and is unpacked in that exact order in Task 2. The dispatch returns `SubsystemOutput(data={...})` matching the sibling resolvers. `region_mode_deferred` is the verbatim defer marker asserted in `test_movement_seam_crossing.py:353`. ✅

**Scope boundary (what Plan 1 deliberately does NOT do):** It does not remove the narration title-scrape, so beneath_sünden's headline descent bug is *not* fully closed by Plan 1 alone — the engine now *can* cross laterally, but the competing narration authority still exists and can still win the race. Closing the bug permanently requires Plan 2 (sever) + Plan 3 (delete). Plan 1's value is real and independently shippable: oz/wonderland/gulliver lateral travel becomes engine-authoritative and observable in the GM panel for the first time, and the foundation for severing is laid with zero regression risk.

---

## The full arc (subsequent plans — NOT executed here)

Plan 1 is the foundation. The remaining work is sequenced and **must** land in order (severing before deletion; consequence-relocation before severing) so no region-mode world or orbital world regresses:

- **Plan 2 — Sever the narrator's region authority + relocate region-transition consequences.** Delete the `current_region`/`pc_regions` writes in `narration_apply.py:4464-4490`; demote the title to a cosmetic label + a new `region.narrator_location_drift` OTEL alarm; and **relocate the orbital consequences I found during recon** — `room.session.bind_region_scope()` (orrery re-center, Story 95-1, `narration_apply.py:4516`) and `_adjudicate_inter_system_jump_for_advance()` (ADR-141 inter-system jump cost, `narration_apply.py:4531`) — onto the engine's region-transition path so they fire from `apply_world_patch`/`region_transitions`, not from a parsed title. **This is the load-bearing fix for both beneath_sünden's descent and perseus_cloud's inter-system jumps**, and it carries the **mis-title wiring test** (narrator returns "Sünden Deep — The Shaft", assert the engine still crossed) as its acceptance gate.
- **Plan 3 — Delete the reconciliation scar tissue + the single-writer tripwire.** Remove the now-unreachable `narration_seam_recovery` (`narration_apply.py:4564-4642`), the §8 drift-strip cross/strip (`:4416-4463`), and 153-21's don't-clobber (`:4316-4382`). Add the runtime single-writer tripwire test asserting every region mutation flows through `apply_world_patch` and a drifted title produces only a `narrator_location_drift` alarm with zero region change.

**REQUIRED design-note amendment before Plan 2:** the design note (`docs/superpowers/specs/2026-06-21-location-single-authority-design.md`) must be amended to cover the **orbital consequence relocation** — `bind_region_scope` and `_adjudicate_inter_system_jump_for_advance` are coupled to the narration region-advance and were not in the note's §4.B. The chokepoint (`snapshot.apply_world_patch`) has no `room`/`pack`/`session` handle, so the consequences cannot move *into* it directly — they need a post-dispatch consequence pass that reads the `region_transitions` receipts the chokepoint stamps. That design decision belongs in the amended note before Plan 2 is planned.

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-06-21-location-single-authority-plan1-lateral-mover.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — dispatch a fresh subagent per task (Task 1, then Task 2), review between tasks, fast iteration. REQUIRED SUB-SKILL: superpowers:subagent-driven-development.

**2. Inline Execution** — execute Task 1 then Task 2 in this session with checkpoints for review. REQUIRED SUB-SKILL: superpowers:executing-plans.

**Which approach?**
