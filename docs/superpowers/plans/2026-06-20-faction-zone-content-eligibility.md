# Faction / Zone-Scoped Content Eligibility — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **In the Pennyfarthing workflow, each Task below maps to one pf story (157-2 … 157-7) and runs through its own wire-first/trivial cycle (TEA writes the failing test, Dev makes it green, Reviewer gates). The test code here is the intended behavior TEA should realize, not a substitute for the per-story RED phase.**

**Goal:** Stop cross-zone content bleed in multi-region worlds (the gulliver 4th-voyage Yahoo on the 1st-voyage Lilliput shore) by scoping creature/NPC/trope/seed eligibility to the faction-group that controls the party's current region.

**Architecture:** One pure module (`game/zone_eligibility.py`) owns a resolver (current region → `controlled_by`) and a predicate; four existing draw/inject seams call it; authored cartography NPCs are push-staged on region entry; a strict load-time validator forbids untagged pooled content in a zoned world. The eligibility key is the already-authored `Region.controlled_by` — no new cartography.

**Tech Stack:** Python 3 / pydantic v2 / pytest (`uv run pytest`); sidequest-server engine; sidequest-content YAML.

**Spec:** `docs/superpowers/specs/2026-06-20-faction-zone-content-eligibility-design.md`. **ADR:** ADR-059 amendment (2026-06-20).

## Global Constraints

- **No Silent Fallbacks / No Stubs / No half-wired features** (sidequest-server CLAUDE.md). Strictness is enforced by the load validator (`GenreLoadError`), never by silently dropping content.
- **Eligibility key is `Region.controlled_by`** (exact string). Sentinel `"*"` = world-global. No new cartography fields; no `factions.yaml` registry (YAGNI — `controlled_by` already encodes membership).
- **Runtime predicate is permissive on untagged content; the validator (Task 6) lands LAST**, after all four zoned worlds (gulliver/oz/wonderland/the_circuit) are fully tagged — so `develop` never carries a zoned world that fails to load. No feature flags.
- **OTEL on every subsystem decision** (CLAUDE.md OTEL Principle): persisted, round-stamped watcher events (`zone_eligibility.filtered`, `zone_eligibility.cast_staged`) — NOT live-only agent-pipeline spans.
- **Tests are fixture-driven behavior + OTEL span assertions. Never grep production source as a wiring assertion** (CLAUDE.md "No Source-Text Wiring Tests").
- **Faction resolution always goes through `snapshot.region_for()` / `pc_regions`**, never the free-text `current_location` string (which may be a POI/scene string, not a region slug).
- **Server tests:** `SIDEQUEST_DATABASE_URL=SIDEQUEST_TEST_DATABASE_URL=postgresql://slabgorb@localhost:5432/sidequest_test uv run pytest -n0 <path>`. Scope `ruff` to changed files only.
- **Branching:** sidequest-server → `develop`; orchestrator (ADR/docs) → `main`.

---

### Task 1: `zone_eligibility` core module (maps to story 157-2, part 1)

The pure keystone. No game-state mutation, no I/O — just the resolver + predicate + zoned-world detection. Everything else calls this.

**Files:**
- Create: `sidequest-server/sidequest/game/zone_eligibility.py`
- Test: `sidequest-server/tests/game/test_zone_eligibility.py`

**Interfaces:**
- Consumes: `GameSnapshot.region_for(perspective=...) -> str | None`, `GameSnapshot.pc_regions: dict[str,str]`; a world's `CartographyConfig.regions: dict[str, Region]` with `Region.controlled_by: str | None`.
- Produces:
  - `WORLD_GLOBAL = "*"`
  - `world_is_zoned(cartography) -> bool`
  - `active_factions(snapshot, cartography, *, perspective: str | None = None) -> set[str]`
  - `is_eligible(content_factions: list[str], active: set[str], *, zoned: bool) -> bool`

- [ ] **Step 1: Write the failing test** — `tests/game/test_zone_eligibility.py`

```python
import pytest
from sidequest.game.zone_eligibility import (
    WORLD_GLOBAL, world_is_zoned, active_factions, is_eligible,
)

class _Region:
    def __init__(self, controlled_by): self.controlled_by = controlled_by

class _Carto:
    def __init__(self, regions): self.regions = regions

def _carto(**regions):  # {region_id: controlled_by}
    return _Carto({rid: _Region(cb) for rid, cb in regions.items()})

def test_world_is_zoned_true_when_any_controlled_by():
    assert world_is_zoned(_carto(a="the_lilliput_court", sea=None)) is True

def test_world_is_zoned_false_when_no_controlled_by():
    assert world_is_zoned(_carto(a=None, b=None)) is False

def test_is_eligible_unzoned_world_always_true():
    assert is_eligible([], set(), zoned=False) is True
    assert is_eligible(["whatever"], {"x"}, zoned=True) is False  # control: zoned filters

def test_is_eligible_unresolvable_region_permissive():
    assert is_eligible(["the_houyhnhnm_assembly"], set(), zoned=True) is True

def test_is_eligible_world_global_sentinel():
    assert is_eligible([WORLD_GLOBAL], {"the_lilliput_court"}, zoned=True) is True

def test_is_eligible_untagged_permissive():
    assert is_eligible([], {"the_lilliput_court"}, zoned=True) is True

def test_is_eligible_tagged_match():
    assert is_eligible(["the_lilliput_court"], {"the_lilliput_court"}, zoned=True) is True

def test_is_eligible_tagged_mismatch_excluded():
    assert is_eligible(["the_houyhnhnm_assembly"], {"the_lilliput_court"}, zoned=True) is False

def test_active_factions_perspective():
    class _Snap:
        pc_regions = {"Gulliver": "the_yahoo_field"}
        def region_for(self, *, perspective=None):
            return self.pc_regions.get(perspective) if perspective else None
    carto = _carto(the_yahoo_field="the_houyhnhnm_assembly", the_lilliput_shore="the_lilliput_court")
    assert active_factions(_Snap(), carto, perspective="Gulliver") == {"the_houyhnhnm_assembly"}

def test_active_factions_split_party_union():
    class _Snap:
        pc_regions = {"A": "the_yahoo_field", "B": "the_lilliput_shore"}
        def region_for(self, *, perspective=None): return None  # split → consensus None
    carto = _carto(the_yahoo_field="the_houyhnhnm_assembly", the_lilliput_shore="the_lilliput_court")
    assert active_factions(_Snap(), carto, perspective=None) == {
        "the_houyhnhnm_assembly", "the_lilliput_court",
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `SIDEQUEST_DATABASE_URL=SIDEQUEST_TEST_DATABASE_URL=postgresql://slabgorb@localhost:5432/sidequest_test uv run pytest -n0 tests/game/test_zone_eligibility.py -v`
Expected: FAIL — `ModuleNotFoundError: sidequest.game.zone_eligibility`.

- [ ] **Step 3: Write the module**

```python
"""Faction/zone-scoped content eligibility (epic-157, ADR-059 amendment).

The eligibility key is the already-authored ``Region.controlled_by``. A world
is "zoned" iff any region declares one. In a zoned world, pooled content
(creatures/tropes/seeds) is eligible only where the party's current region's
``controlled_by`` is among the content's ``factions`` (exact match), or the
content is world-global (``"*"``). The runtime predicate is PERMISSIVE on
untagged content; the load validator forbids untagged pooled content in a
zoned world, so the permissive branch is dead code in production.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from sidequest.game.session import GameSnapshot
    from sidequest.genre.models.world import CartographyConfig

WORLD_GLOBAL = "*"


def world_is_zoned(cartography) -> bool:
    """True iff any region declares a non-empty ``controlled_by``."""
    return any(getattr(r, "controlled_by", None) for r in cartography.regions.values())


def active_factions(snapshot, cartography, *, perspective: str | None = None) -> set[str]:
    """Resolve the faction-group(s) controlling the party's current region.

    Resolution is via ``region_for``/``pc_regions`` (the canonical region), never
    the free-text current_location. Split party (region_for → None, perspective
    None): UNION of every seated PC's region controlled_by. Returns ∅ when no
    region resolvable (pre-bind / malformed turn) — callers treat ∅ as permissive.
    """
    def _cb(region_id: str | None) -> str | None:
        if not region_id:
            return None
        region = cartography.regions.get(region_id)
        return getattr(region, "controlled_by", None) if region else None

    region_id = snapshot.region_for(perspective=perspective)
    if region_id is not None:
        cb = _cb(region_id)
        return {cb} if cb else set()
    # perspective given but unresolved, OR split party → union of all seated PCs
    if perspective is not None:
        return set()
    out: set[str] = set()
    for rid in snapshot.pc_regions.values():
        cb = _cb(rid)
        if cb:
            out.add(cb)
    return out


def is_eligible(content_factions: list[str], active: set[str], *, zoned: bool) -> bool:
    """Whether content is eligible given the active faction-group(s)."""
    if not zoned:
        return True
    if not active:
        return True  # region unresolvable → do not suppress
    if WORLD_GLOBAL in content_factions:
        return True
    if not content_factions:
        return True  # untagged → permissive (validator forbids this in a zoned world)
    return bool(set(content_factions) & active)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `... uv run pytest -n0 tests/game/test_zone_eligibility.py -v`
Expected: PASS (all 10).

- [ ] **Step 5: Commit**

```bash
git add sidequest-server/sidequest/game/zone_eligibility.py sidequest-server/tests/game/test_zone_eligibility.py
git commit -m "feat(157-2): zone_eligibility resolver + predicate (pure core)"
```

---

### Task 2: Seam 1 — creature/encounter injection filter + factions propagation (story 157-2, part 2; the headline fix)

**Files:**
- Modify: `sidequest-server/sidequest/game/monster_manual.py` (add `factions` to `ManualEncounter` and `ManualNpc`; thread through `add_encounter`/`add_npc`)
- Modify: `sidequest-server/sidequest/server/dispatch/pregen.py` (`_generate_encounter` stamps `factions` = union of source bestiary entries' `factions`)
- Modify: `sidequest-server/sidequest/genre/models/bestiary.py` (add `factions: list[str]` to `BestiaryEntry`)
- Modify: `sidequest-server/sidequest/server/dispatch/monster_manual_inject.py` (`_npc_patches_for_encounters` filters by `is_eligible`)
- Create: `sidequest-server/sidequest/telemetry/spans/zone_eligibility.py` (the watcher event)
- Test: `sidequest-server/tests/server/test_zone_eligibility_creature_seam.py`

**Interfaces:**
- Consumes: `zone_eligibility.{active_factions, is_eligible, world_is_zoned}`; `ManualEncounter.factions: list[str]`; `BestiaryEntry.factions: list[str]`.
- Produces: `zone_eligibility_filtered_span(subsystem, content_id, content_factions, active_factions, region)` (context-manager span, watcher-routed, persisted).

- [ ] **Step 1: Add the `factions` field to the models** (`bestiary.py`, then `monster_manual.py`)

```python
# bestiary.py — BestiaryEntry (extra="allow", so additive is safe)
factions: list[str] = Field(default_factory=list)
```
```python
# monster_manual.py — ManualEncounter AND ManualNpc
factions: list[str] = Field(default_factory=list)
```
Thread `factions` through `MonsterManual.add_encounter(self, data, tier, terrain_tags, *, factions=None)` and `add_npc(..., *, factions=None)` (default `None` → `[]`; existing callers unchanged).

- [ ] **Step 2: Write the failing wiring test** — synthetic zoned world, Houyhnhnm encounter, party in Lilliput → no Yahoo patch

```python
# test_zone_eligibility_creature_seam.py — fixture-driven behavior + OTEL
def test_houyhnhnm_encounter_excluded_on_lilliput_shore(zoned_world_fixture, capture_spans):
    manual = zoned_world_fixture.manual_with_encounter(
        enemy_name="Yahoo", factions=["the_houyhnhnm_assembly"], tier=2,
    )
    snapshot = zoned_world_fixture.snapshot(pc_region="the_lilliput_shore")  # controlled_by the_lilliput_court
    patches = monster_manual_inject._npc_patches_for_encounters(
        manual, snapshot, cartography=zoned_world_fixture.cartography, in_combat=False,
        perspective=zoned_world_fixture.pc_name,
    )
    assert not any(p.name == "Yahoo" for p in patches)            # excluded
    assert capture_spans.fired("zone_eligibility.filtered", subsystem="creature", content_id="Yahoo")

def test_houyhnhnm_encounter_included_in_houyhnhnm_land(zoned_world_fixture):
    manual = zoned_world_fixture.manual_with_encounter(
        enemy_name="Yahoo", factions=["the_houyhnhnm_assembly"], tier=2,
    )
    snapshot = zoned_world_fixture.snapshot(pc_region="the_yahoo_field")  # controlled_by the_houyhnhnm_assembly
    patches = monster_manual_inject._npc_patches_for_encounters(
        manual, snapshot, cartography=zoned_world_fixture.cartography, in_combat=False,
        perspective=zoned_world_fixture.pc_name,
    )
    assert any(p.name == "Yahoo" for p in patches)                # included

def test_unzoned_world_no_filtering(unzoned_world_fixture):
    # control: a world with no controlled_by behaves exactly as today
    ...
```

- [ ] **Step 3: Run to verify it fails**

Run: `... uv run pytest -n0 tests/server/test_zone_eligibility_creature_seam.py -v`
Expected: FAIL — `_npc_patches_for_encounters` doesn't accept `cartography`/`perspective`, no filtering, Yahoo present.

- [ ] **Step 4: Implement the filter + span**

In `_npc_patches_for_encounters`, before materializing each encounter's patch, resolve once per call: `zoned = world_is_zoned(cartography)`, `active = active_factions(snapshot, cartography, perspective=perspective)`. For each encounter, if `not is_eligible(encounter.factions, active, zoned=zoned)`: emit `zone_eligibility_filtered_span(subsystem="creature", content_id=<enemy name or encounter id>, content_factions=encounter.factions, active_factions=sorted(active), region=snapshot.region_for(perspective=perspective))` and `continue`. Thread `cartography`/`perspective` from the single caller (`websocket_session_handler.py:843` area) — it already has `sd.genre_pack` and the turn perspective.
In `pregen._generate_encounter`, set the new encounter's `factions` to the sorted union of `factions` across the bestiary entries it sampled.

- [ ] **Step 5: Run to verify it passes; ruff changed files; commit**

```bash
SIDEQUEST_DATABASE_URL=... uv run pytest -n0 tests/server/test_zone_eligibility_creature_seam.py tests/game/test_zone_eligibility.py -v
uv run ruff check sidequest/game/zone_eligibility.py sidequest/game/monster_manual.py sidequest/server/dispatch/pregen.py sidequest/server/dispatch/monster_manual_inject.py sidequest/genre/models/bestiary.py sidequest/telemetry/spans/zone_eligibility.py
git add -A && git commit -m "feat(157-2): scope creature injection by region controlled_by (Seam 1)"
```

---

### Task 3: Seam 2 — NPC walk-on origin-stamp + authored-cast push-staging on region entry (story 157-3)

**Files:**
- Modify: `sidequest-server/sidequest/game/monster_manual.py` (`mark_active` stamps `factions` from the current region's `controlled_by` in a zoned world)
- Modify: `sidequest-server/sidequest/server/dispatch/monster_manual_inject.py` (`available_at_location` / generated-NPC surfacing consults `is_eligible`)
- Create: `sidequest-server/sidequest/game/region_cast_staging.py` (the frontier observer that stages authored cartography NPCs)
- Modify: wherever the server registers session-lifetime hooks (server startup / app wiring) to `register_frontier_observer(stage_region_cast)` once
- Test: `sidequest-server/tests/server/test_region_cast_staging.py`

**Interfaces:**
- Consumes: `frontier_hook.register_frontier_observer`, `notify_region_transition(snapshot, *, pc_name, from_region, to_region)`; `zone_eligibility.*`; a region's `entities: list[LocationEntity]` where `binding.kind == "npc"`.
- Produces: `stage_region_cast(*, snapshot, pc_name, from_region, to_region) -> None`; `zone_eligibility_cast_staged_span(region, npc_names)`.

> **Concurrency constraint (hard requirement):** `frontier_hook._OBSERVERS` is a **module-global** registry. `stage_region_cast` MUST resolve the pack/cartography from the *snapshot it is handed* (`snapshot.genre_slug`, `snapshot.world_slug`) — never from a per-session captured closure — or a transition in session A would stage using session B's pack. Register the observer ONCE at startup, not per session. Staging is idempotent (skip NPCs already active/in pool).

- [ ] **Step 1: Failing test** — entering Mildendo stages the Lilliput court

```python
def test_entering_region_stages_authored_npc_cast(zoned_world_fixture, capture_spans):
    snap = zoned_world_fixture.snapshot(pc_region="the_lilliput_shore")
    from sidequest.game.region_cast_staging import stage_region_cast
    stage_region_cast(snapshot=snap, pc_name=zoned_world_fixture.pc_name,
                      from_region="the_lilliput_shore", to_region="mildendo_capital")
    staged = {n.name for n in snap.npc_pool}
    assert {"the Emperor of Lilliput", "Reldresal, the Principal Secretary"} <= staged
    assert capture_spans.fired("zone_eligibility.cast_staged", region="mildendo_capital")

def test_generated_walkon_stamped_with_region_faction(zoned_world_fixture):
    manual = zoned_world_fixture.manual_with_generated_npc(name="A Fishwife", factions=[])
    manual.mark_active("A Fishwife", location="the_lilliput_shore",
                       faction="the_lilliput_court")  # zoned → stamp
    npc = manual.find_npc_by_exact_name("A Fishwife")
    assert npc.factions == ["the_lilliput_court"]
```

- [ ] **Step 2: Run to verify it fails**

Run: `... uv run pytest -n0 tests/server/test_region_cast_staging.py -v`
Expected: FAIL — `region_cast_staging` module missing; `mark_active` has no `faction` kwarg.

- [ ] **Step 3: Implement**
- `mark_active(self, name, location, *, faction=None)`: when `faction` is provided and the NPC's `factions` is empty, set `npc.factions = [faction]` (origin-stamp). Caller in inject passes the current region's `controlled_by` only in a zoned world.
- `region_cast_staging.stage_region_cast`: resolve cartography from `snapshot.genre_slug`/`world_slug` via the pack loader cache; read `cartography.regions[to_region].entities`; for each `e.binding and e.binding.kind == "npc"`, materialize/activate the bound NPC into `snapshot.npc_pool` (mark active, set `last_seen`/activated_location), skipping any already present (idempotent). Emit `zone_eligibility_cast_staged_span(region=to_region, npc_names=[...])`.
- Register once at startup: `register_frontier_observer(stage_region_cast)`.

- [ ] **Step 4: Run to verify it passes; add the cross-fire guard test; ruff; commit**

```python
def test_staging_resolves_pack_from_snapshot_not_capture(two_world_fixture):
    # Fire transition for world A's snapshot; assert it stages A's cast, never B's
    ...
```
```bash
git add -A && git commit -m "feat(157-3): NPC walk-on origin-stamp + authored-cast staging on region entry (Seam 2)"
```

---

### Task 4: Seams 3 & 4 — trope activation gate + seed-deck draw filter (story 157-4)

**Files:**
- Modify: `sidequest-server/sidequest/genre/models/tropes.py` (`factions: list[str]` on `TropeDefinition` AND `SeedTrope` — **required before any trope/seed yaml can carry it; both are `extra="forbid"`**)
- Modify: `sidequest-server/sidequest/game/trope_tick.py` (`_gate_activations` consults `is_eligible`)
- Modify: `sidequest-server/sidequest/game/seed_deck.py` (`draw(self, *, eligible=None)`)
- Modify: `sidequest-server/sidequest/game/seed_tick.py` (build the `eligible` closure from `active_factions`/`is_eligible`; pass to `draw`)
- Test: `sidequest-server/tests/game/test_zone_eligibility_trope_seed.py`

**Interfaces:**
- Consumes: `zone_eligibility.*`; `TropeDefinition.factions`, `SeedTrope.factions`.
- Produces: `SeedDeck.draw(*, eligible: Callable[[SeedTrope], bool] | None = None)` — when given, skips seeds for which `eligible(seed)` is False (ordering/resume unchanged).

- [ ] **Step 1: Failing tests**

```python
def test_seed_deck_draw_skips_ineligible():
    from sidequest.game.seed_deck import SeedDeck
    from sidequest.genre.models.tropes import SeedTrope
    seeds = [SeedTrope(id="houyhnhnm_decree", name="x", factions=["the_houyhnhnm_assembly"]),
             SeedTrope(id="endian_war", name="y", factions=["the_lilliput_court"])]
    deck = SeedDeck("wry_whimsy", "gulliver", "sess1", seeds)
    drawn = deck.draw(eligible=lambda s: "the_lilliput_court" in s.factions)
    assert drawn.id == "endian_war"

def test_trope_gate_excludes_wrong_zone(zoned_world_fixture, capture_spans):
    # dormant Houyhnhnm trope + party in Lilliput → not activated; span fired
    ...
```

- [ ] **Step 2: Run to verify it fails** — `SeedTrope`/`TropeDefinition` reject `factions` (extra=forbid) → and `draw` has no `eligible` kwarg.

Run: `... uv run pytest -n0 tests/game/test_zone_eligibility_trope_seed.py -v`

- [ ] **Step 3: Implement**
- Add `factions: list[str] = Field(default_factory=list)` to `TropeDefinition` and `SeedTrope`.
- `SeedDeck.draw(self, *, eligible=None)`: in the loop, `if seed.id in self.drawn_ids: continue`; `if eligible is not None and not eligible(seed): continue`; else draw. (Do **not** add ineligible seeds to `drawn_ids` — they remain drawable when the party moves zones.)
- `seed_tick`: build `eligible = lambda s: is_eligible(s.factions, active_factions(snapshot, cartography, perspective=None), zoned=world_is_zoned(cartography))` and pass to `draw`.
- `trope_tick._gate_activations`: a dormant trope is a candidate only if `is_eligible(trope.factions, active, zoned=zoned)` (compute `active`/`zoned` once per tick); emit `zone_eligibility.filtered` (subsystem="trope") on exclusion.

- [ ] **Step 4: Run to verify it passes; ruff; commit**

```bash
git add -A && git commit -m "feat(157-4): scope trope activation + seed draw by faction-group (Seams 3 & 4)"
```

---

### Task 5: Content — tag gulliver (proof world) (story 157-5)

> Depends on Tasks 1–4 (the `factions` fields + all four seams must exist). This is the end-to-end proof.

**Files (sidequest-content):**
- Modify: `genre_packs/wry_whimsy/worlds/gulliver/bestiary.yaml` (every entry gets `factions:`)
- Modify: `genre_packs/wry_whimsy/worlds/gulliver/tropes.yaml` (every trope gets `factions:`)
- Modify: `genre_packs/wry_whimsy/worlds/gulliver/seed_tropes.yaml` (every seed gets `factions:`)

**Tagging map (from cartography `controlled_by`):**
- Lilliput content → `[the_lilliput_court]` · Brobdingnag → `[the_brobdingnag_crown]` · Laputa/Balnibarbi/Glubbdubdrib/Luggnagg → `[the_lagado_academy]` · Houyhnhnm-land (incl. `yahoo_brute`, `yahoo_pack`) → `[the_houyhnhnm_assembly]` · sea/open-ocean creatures → `[no_one]` · cross-voyage thematic tropes (e.g. `the_satire_turns_on_you`, `the_scale_reveal`) → `["*"]`.

- [ ] **Step 1:** Tag `bestiary.yaml` — each entry's home voyage → its faction. The Yahoo entries → `[the_houyhnhnm_assembly]`.
- [ ] **Step 2:** Tag `tropes.yaml` — zone-specific tropes → their faction; genuine cross-voyage themes → `["*"]`.
- [ ] **Step 3:** Tag `seed_tropes.yaml` — same rule.
- [ ] **Step 4: Verify load + no bleed** — start the server on gulliver; confirm it loads; run a Lilliput-shore turn and assert via `zone_eligibility.filtered` (GM panel / forensics) that `yahoo_brute` is suppressed; confirm the Lilliput court stages in Mildendo (`zone_eligibility.cast_staged`).
- [ ] **Step 5: Commit** (sidequest-content → `develop`)

```bash
git add genre_packs/wry_whimsy/worlds/gulliver/{bestiary,tropes,seed_tropes}.yaml
git commit -m "content(157-5): tag gulliver content by faction (zone-eligibility proof)"
```

---

### Task 6: Content fan-out + strict validator (stories 157-6 then 157-7)

**6a — Content fan-out (157-6, sidequest-content → develop):** repeat Task 5's tagging for **oz** (7 region-factions), **wonderland** (`the_queens_terror`/`the_rigged_game`/`no_one`), **the_circuit** (subculture factions). Each world: tag bestiary + tropes + seed_tropes; verify load + a spot playtest.

**6b — Strict validator (157-7, sidequest-server → develop, LANDS LAST):**
**Files:**
- Modify: `sidequest-server/sidequest/genre/loader.py` (validate after a world loads)
- Create: `sidequest-server/sidequest/genre/zone_validation.py` (`validate_zone_tagging(world_slug, cartography, bestiary, tropes, seed_tropes) -> None`, raises `GenreLoadError`)
- Test: `sidequest-server/tests/genre/test_zone_validation.py`

- [ ] **Step 1: Failing test**

```python
def test_zoned_world_untagged_bestiary_entry_raises(zoned_cartography):
    from sidequest.genre.zone_validation import validate_zone_tagging
    from sidequest.genre.loader import GenreLoadError
    bad = [BestiaryEntry(id="yahoo", name="Yahoo", level=2, hp=9, armor_class=12,
                         attack_bonus=2, factions=[])]  # untagged in a zoned world
    with pytest.raises(GenreLoadError, match="yahoo"):
        validate_zone_tagging("gulliver", zoned_cartography, bestiary=bad, tropes=[], seed_tropes=[])

def test_unknown_faction_reference_raises(zoned_cartography):
    bad = [BestiaryEntry(id="yahoo", name="Yahoo", level=2, hp=9, armor_class=12,
                         attack_bonus=2, factions=["the_houyhnhm_assembly"])]  # typo
    with pytest.raises(GenreLoadError, match="the_houyhnhm_assembly"):
        validate_zone_tagging("gulliver", zoned_cartography, bestiary=bad, tropes=[], seed_tropes=[])

def test_unzoned_world_untagged_ok(unzoned_cartography):
    validate_zone_tagging("blackthorn_moor", unzoned_cartography,
                          bestiary=[...untagged...], tropes=[], seed_tropes=[])  # no raise

def test_wildcard_and_valid_faction_pass(zoned_cartography):
    ...  # factions=["*"] and factions=["the_houyhnhnm_assembly"] both pass
```

- [ ] **Step 2: Run to verify it fails** (`zone_validation` missing).
- [ ] **Step 3: Implement** — `validate_zone_tagging`: if `not world_is_zoned(cartography)`: return. Else build `valid = {WORLD_GLOBAL} | {r.controlled_by for r in regions if r.controlled_by}`; for each pooled item in (bestiary entries, tropes, seed_tropes): if `not item.factions`: raise `GenreLoadError(f"{world_slug}: pooled content {item.id!r} untagged in a zoned world")`; for each value not in `valid`: raise `GenreLoadError(f"{world_slug}: {item.id!r} references unknown faction {value!r}")`. Call from `loader.py` right after the world's bestiary/tropes/seed_tropes are loaded.
- [ ] **Step 4: Run full genre-load suite** — confirm all four zoned worlds (now fully tagged from 157-5/6) load clean; the 11 unzoned worlds untouched.

Run: `... uv run pytest -n0 tests/genre/ -v`

- [ ] **Step 5: Commit** (server → develop)

```bash
git add -A && git commit -m "feat(157-7): strict load validator for zone tagging (fail-loud)"
```

---

## Self-Review

**1. Spec coverage:**
- Model (`factions` field + sentinel + zoned detection) → Tasks 1, 2 (bestiary), 4 (trope/seed). ✓
- Resolver + predicate + split-party → Task 1. ✓
- Seam 1 creature inject → Task 2. ✓ Seam 2 NPC stamp + staging → Task 3. ✓ Seam 3 trope gate + Seam 4 seed draw → Task 4. ✓
- Strict validator + referential check → Task 6b. ✓
- OTEL `zone_eligibility.filtered`/`.cast_staged` → Tasks 2, 3, 4. ✓
- Content tagging gulliver + fan-out → Tasks 5, 6a. ✓
- Permissive-runtime / validator-last sequencing → encoded in task order + Global Constraints. ✓

**2. Placeholder scan:** Task 5/6a content steps and a few seam test bodies use `...` for fixture wiring that the per-story TEA realizes (fixture-heavy, world-specific). These are intentional pf-workflow handoffs, not logic placeholders — the behavior asserted is concrete (which NPC/creature appears, which span fires). Task 1 (the keystone) and the validator (6b) are fully concrete.

**3. Type consistency:** `factions: list[str]` identical across `BestiaryEntry`/`ManualEncounter`/`ManualNpc`/`TropeDefinition`/`SeedTrope`. `active_factions(snapshot, cartography, *, perspective)` and `is_eligible(content_factions, active, *, zoned)` signatures match across all call sites (Tasks 2/3/4). `SeedDeck.draw(*, eligible=...)` consistent. `WORLD_GLOBAL = "*"` used in predicate (Task 1) and validator (6b). ✓

## Known wrinkles flagged for executors
- **Frontier observer concurrency** (Task 3): module-global registry → resolve pack from snapshot slugs, register once, idempotent staging. Has a dedicated cross-fire test.
- **Encounter faction propagation** (Task 2): an encounter bundles multiple enemies; its `factions` = union of source entries' — a mixed-faction encounter is eligible if ANY member matches. If authors want single-faction encounters, that's a content-authoring discipline, not an engine rule.
- **Validator timing** (Task 6b): must merge only after 157-5/6 tag all four zoned worlds, else those worlds fail to load on `develop`.
