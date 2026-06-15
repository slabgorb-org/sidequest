# Fate Gear Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bind the four narrative packs (pulp_noir, spaghetti_western, tea_and_murder, wry_whimsy) to `ruleset: fate` and let each pack author starting "gear" that compiles into the existing `FateSheet` as aspects/stunts/permission-aspects — with zero new runtime subsystem and Fate's own refresh economy doing the balancing.

**Architecture:** Fate gear is *authoring data*, not carried inventory. A new strict `GearDef` model (`gear.yaml`, genre + world tier, merged by `id`) declares what each gear grants. At chargen the bound `FateRulesetModule` compiles the chosen class's gear into a fresh `FateSheet` (aspect-gear free; stunt-gear costs refresh), stamps each entry with `source_gear`, and emits one `fate.gear_compiled` OTEL span. `CatalogItem` is never touched; Fate packs drop `inventory.yaml` entirely.

**Tech Stack:** Python 3.14, pydantic v2 (`extra="forbid"` strict models), pytest, uv. Server repo `sidequest-server`; content repo `sidequest-content`. OTEL via the existing `Span.open(...)` helper.

**Source spec:** `docs/superpowers/specs/2026-06-15-fate-gear-model-design.md` (approved 2026-06-15). ADR-144 §D5-seam, ADR-145 §D5.

---

## Planning deviation from the spec (read first)

The spec says "wire each archetype's `gear: [ids]`". The four packs store playable characters heterogeneously — some as `allowed_classes` bare strings in `rules.yaml`, some in `classes.yaml`, with NPC `archetypes.yaml` separate. Scattering a `gear:` field across those files would be non-uniform and fragile. **This plan instead binds gear in one uniform place: a `starting_gear` map in the new `fate:` rules block, keyed by the PC class name** (`allowed_classes` entries). This is functionally identical to the spec's intent (K-i: gear bundled to the chargen pick) and keeps all Fate-gear wiring in `rules.yaml` + `gear.yaml`. No design change — a mechanism refinement justified by the content layout the scouts confirmed.

The Oz **silver shoes stay narrator-placed mid-game** (a `create-an-advantage` aspect), exactly as the spec's worked example specifies — they are loot, not chargen gear, so they are **not** authored in `gear.yaml`.

---

## File Structure

**Server (`sidequest-server`) — Phase A, must land before content:**

| File | Responsibility | Create/Modify |
|------|----------------|---------------|
| `sidequest/genre/models/gear.py` | `GearDef`, `GearGrantAspect`, `GearGrantStunt` strict models | Create |
| `sidequest/game/fate_sheet.py` | `AspectKind += "permission"`; `source_gear` on `Aspect`/`Stunt` | Modify |
| `sidequest/genre/models/rules.py` | `FateConfig` + `fate:` field on `RulesConfig` | Modify |
| `sidequest/genre/models/pack.py` | `gear: list[GearDef]` on `GenrePack` (l.407) + `World` (l.274), mirroring `inventory` | Modify |
| `sidequest/genre/loader.py` | load `gear.yaml` genre (~l.1936) + world (~l.1616) via `_load_yaml_raw_optional` | Modify |
| `sidequest/server/dispatch/gear_resolve.py` | `merge_gear_catalog(baseline, world)` by-`id` union | Create |
| `sidequest/telemetry/spans/fate.py` | `fate_gear_compiled_span(...)` + `SPAN_ROUTES` entry | Modify |
| `sidequest/game/ruleset/base.py` | `compile_fate_sheet(...)` default → `None` (beside `seed_chargen_resources`, l.261) | Modify |
| `sidequest/game/ruleset/fate.py` | `compile_fate_sheet(...)` override (gear → FateSheet + span) | Modify |
| `sidequest/game/builder.py` | `with_gear_catalog`; call `compile_fate_sheet`; set `fate_sheet` at CreatureCore (l.2987) | Modify |
| `sidequest/handlers/connect.py` | merge genre+world gear; `builder.with_gear_catalog(...)` beside `with_chargen_defs` | Modify |
| `sidequest/cli/validate/pack.py` | three Fate-gear invariants, registered in `validate_pack_structure` (l.1244) | Modify |

**Content (`sidequest-content`) — Phase B, depends on Phase A:**

| Pack | Work |
|------|------|
| `pulp_noir` | `rules.yaml` bind `fate` + `fate:` block; delete genre + world `inventory.yaml`; author `gear.yaml` |
| `spaghetti_western` | bind `fate`; delete 3 world `inventory.yaml`; author genre `gear.yaml` |
| `tea_and_murder` | bind `fate`; delete genre + 2 world `inventory.yaml`; author `gear.yaml` |
| `wry_whimsy` | replace `ruleset: native` → `fate`; delete genre `inventory.yaml`; author `gear.yaml` (no silver shoes) |

---

## Phase A — Server engine

### Task 1: `GearDef` content model

**Files:**
- Create: `sidequest/genre/models/gear.py`
- Test: `tests/genre/models/test_gear.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/genre/models/test_gear.py
import pytest
from pydantic import ValidationError

from sidequest.genre.models.gear import GearDef, GearGrantAspect, GearGrantStunt


def test_gear_def_aspect_only():
    g = GearDef.model_validate(
        {"id": "trench_coat", "name": "Trench Coat",
         "grants_aspects": [{"text": "Collar Always Up"}]}
    )
    assert g.id == "trench_coat"
    assert g.grants_aspects[0].kind == "character"   # default
    assert g.grants_stunts == []


def test_gear_def_permission_aspect_kind():
    g = GearDef.model_validate(
        {"id": "badge", "name": "Inspector's Badge",
         "grants_aspects": [{"text": "Authority of the Yard", "kind": "permission"}]}
    )
    assert g.grants_aspects[0].kind == "permission"


def test_gear_def_stunt():
    g = GearDef.model_validate(
        {"id": "custom_38", "name": "Custom .38",
         "grants_stunts": [{"name": "From Cover", "description": "+2 to Shoot from cover."}]}
    )
    assert g.grants_stunts[0].name == "From Cover"


def test_gear_def_flavor_only_is_legal():
    # A hat is a hat — no grants is valid (pure narrative flavor).
    g = GearDef.model_validate({"id": "fedora", "name": "Fedora"})
    assert g.grants_aspects == [] and g.grants_stunts == []


def test_gear_def_rejects_unknown_field():
    # Strict: no priced/weighted/damage fields leak in from the WN paradigm.
    with pytest.raises(ValidationError):
        GearDef.model_validate({"id": "x", "name": "X", "value": 50})


def test_gear_grant_aspect_rejects_bad_kind():
    with pytest.raises(ValidationError):
        GearGrantAspect.model_validate({"text": "x", "kind": "situation"})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/genre/models/test_gear.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'sidequest.genre.models.gear'`

- [ ] **Step 3: Write minimal implementation**

```python
# sidequest/genre/models/gear.py
"""Fate gear model (ADR-144 §D5, ADR-145 §D5). Fate has no equipment economy:
gear is authoring data that compiles into a FateSheet at chargen as aspects /
stunts / permission-aspects. This model is deliberately separate from
CatalogItem (inventory.py) — the WN priced catalog and Fate gear never share a
model. See docs/superpowers/specs/2026-06-15-fate-gear-model-design.md.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class GearGrantAspect(BaseModel):
    """An aspect a gear item places on the sheet. ``kind="permission"`` is the
    P-i narrator-read permission aspect — never an engine gate."""

    model_config = {"extra": "forbid"}

    text: str
    kind: Literal["character", "permission"] = "character"


class GearGrantStunt(BaseModel):
    """A stunt a gear item grants. A Fate stunt costs exactly 1 refresh (SRD),
    so cost is the stunt COUNT against the pack's ``free_stunts`` allotment —
    enforced by the refresh invariant in the content validator, not a field."""

    model_config = {"extra": "forbid"}

    name: str
    description: str = ""


class GearDef(BaseModel):
    """A piece of Fate starting gear. Compiles into FateSheet entries at chargen.
    No value/weight/damage fields exist here — Fate has no economy."""

    model_config = {"extra": "forbid"}

    id: str
    name: str
    description: str = ""
    grants_aspects: list[GearGrantAspect] = Field(default_factory=list)
    grants_stunts: list[GearGrantStunt] = Field(default_factory=list)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/genre/models/test_gear.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add sidequest/genre/models/gear.py tests/genre/models/test_gear.py
git commit -m "feat(114-10): GearDef Fate gear content model (ADR-144 D5)"
```

---

### Task 2: FateSheet deltas — `permission` aspect kind + `source_gear` traceability

**Files:**
- Modify: `sidequest/game/fate_sheet.py` (`AspectKind` ~line 28; `Aspect` ~36-44; `Stunt` ~47-54)
- Test: `tests/game/test_fate_sheet_gear_fields.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/game/test_fate_sheet_gear_fields.py
from sidequest.game.fate_sheet import Aspect, Stunt


def test_permission_is_a_valid_aspect_kind():
    a = Aspect(text="Authority of the Yard", kind="permission")
    assert a.kind == "permission"


def test_aspect_carries_source_gear_backref():
    a = Aspect(text="Collar Always Up", kind="character", source_gear="trench_coat")
    assert a.source_gear == "trench_coat"


def test_aspect_source_gear_defaults_none():
    a = Aspect(text="Hard-Boiled", kind="high_concept")
    assert a.source_gear is None


def test_stunt_carries_source_gear_backref():
    s = Stunt(name="From Cover", description="+2 Shoot from cover.", source_gear="custom_38")
    assert s.source_gear == "custom_38"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/game/test_fate_sheet_gear_fields.py -v`
Expected: FAIL — `ValidationError` on `kind="permission"` (not in Literal) and unexpected keyword `source_gear`.

- [ ] **Step 3: Write minimal implementation**

In `sidequest/game/fate_sheet.py`, add `"permission"` to the `AspectKind` literal:

```python
AspectKind = Literal[
    "high_concept", "trouble", "character", "situation",
    "consequence", "boost", "permission",
]
```

Add `source_gear` to `Aspect` (after `free_invokes`):

```python
class Aspect(BaseModel):
    """A free-text Fate aspect. ``free_invokes`` is the count of unused free
    invocations on it (create-advantage and consequences grant these)."""

    model_config = {"extra": "forbid"}

    text: str
    kind: AspectKind
    free_invokes: int = 0
    source_gear: str | None = None  # ADR-144 D5: id of the GearDef this compiled
                                     # from; None for hand-authored aspects.
```

Add `source_gear` to `Stunt`:

```python
class Stunt(BaseModel):
    """A named stunt. The mechanical effect is authored as content (F2/F4); the
    engine spine in F1 only needs to carry the name/description."""

    model_config = {"extra": "forbid"}

    name: str
    description: str = ""
    source_gear: str | None = None  # ADR-144 D5: id of the GearDef this compiled from.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/game/test_fate_sheet_gear_fields.py tests/game/test_fate_sheet.py -v`
Expected: PASS (new tests pass; existing `test_fate_sheet.py` still green — defaults preserve back-compat).

- [ ] **Step 5: Commit**

```bash
git add sidequest/game/fate_sheet.py tests/game/test_fate_sheet_gear_fields.py
git commit -m "feat(114-10): permission aspect kind + source_gear backref on FateSheet"
```

---

### Task 3: `FateConfig` + `fate:` block on `RulesConfig`

**Files:**
- Modify: `sidequest/genre/models/rules.py` (add `FateConfig` near `SwnConfig` ~line 832; add `fate` field on `RulesConfig` ~line 1093 beside `swn`/`cwn`/`wwn`/`awn`)
- Test: `tests/genre/models/test_fate_rules_config.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/genre/models/test_fate_rules_config.py
from sidequest.genre.models.rules import FateConfig, RulesConfig


def test_fate_config_defaults_srd_3_3():
    fc = FateConfig()
    assert fc.base_refresh == 3 and fc.free_stunts == 3
    assert fc.starting_gear == {}


def test_fate_config_starting_gear_map_by_class():
    fc = FateConfig.model_validate(
        {"base_refresh": 3, "free_stunts": 3,
         "starting_gear": {"Detective": ["trench_coat", "snub_revolver"]}}
    )
    assert fc.starting_gear["Detective"] == ["trench_coat", "snub_revolver"]


def test_rules_config_accepts_fate_block():
    rc = RulesConfig.model_validate(
        {"ruleset": "fate", "fate": {"base_refresh": 3, "free_stunts": 3,
                                     "starting_gear": {"Detective": ["trench_coat"]}}}
    )
    assert rc.ruleset == "fate"
    assert rc.fate is not None and rc.fate.starting_gear["Detective"] == ["trench_coat"]


def test_rules_config_fate_block_optional():
    rc = RulesConfig.model_validate({"ruleset": "native"})
    assert rc.fate is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/genre/models/test_fate_rules_config.py -v`
Expected: FAIL — `ImportError: cannot import name 'FateConfig'`.

- [ ] **Step 3: Write minimal implementation**

In `sidequest/genre/models/rules.py`, add near `SwnConfig` (~line 832):

```python
class FateConfig(BaseModel):
    """Fate Core ruleset binding block (ADR-144). Present only when
    ``ruleset == "fate"``. ``starting_gear`` maps a PC class name (an
    ``allowed_classes`` entry) to the GearDef ids the class is built with —
    the K-i archetype-bundled binding. ``base_refresh``/``free_stunts`` default
    to the SRD 3/3 and feed the content validator's refresh invariant."""

    model_config = {"extra": "forbid"}

    base_refresh: int = 3
    free_stunts: int = 3
    starting_gear: dict[str, list[str]] = Field(default_factory=dict)
```

Add the field on `RulesConfig` beside `swn`/`cwn`/`wwn`/`awn` (~line 1093):

```python
    fate: FateConfig | None = None      # Present only when ruleset == "fate"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/genre/models/test_fate_rules_config.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add sidequest/genre/models/rules.py tests/genre/models/test_fate_rules_config.py
git commit -m "feat(114-10): FateConfig rules block (base_refresh, free_stunts, starting_gear)"
```

---

### Task 4: Load + merge `gear.yaml` (genre + world tier)

**Files:**
- Create: `sidequest/server/dispatch/gear_resolve.py`
- Modify: `sidequest/genre/models/pack.py` — add `gear: list[GearDef]` to `GenrePack` (field block at line 407, beside `inventory: InventoryConfig | None`) and to `World` (field block at line 274, beside its `inventory`)
- Modify: `sidequest/genre/loader.py` — genre `gear.yaml` load beside the genre inventory load (~line 1936); world `gear.yaml` load beside `world_inventory` (~line 1616). Use the existing `_load_yaml_raw_optional(path) -> Any | None` (loader.py:197) + list-comprehension validation (the pattern used for `archetypes.yaml` at loader.py:1851-1855). There is **no** generic list-loader helper — do not invent one; use the raw+comprehension pattern.
- Test: `tests/server/dispatch/test_gear_resolve.py`

**Loader entry point (pinned):** `load_genre_pack(path: Path | str) -> GenrePack` at `loader.py:1814`. The loaded `GenrePack` exposes genre inventory as `pack.inventory`; worlds as `pack.worlds[world_slug]` (`World` objects) with `world.inventory`. After this task the same objects expose `pack.gear` and `world.gear`.

- [ ] **Step 1: Write the failing test (the by-id merge)**

```python
# tests/server/dispatch/test_gear_resolve.py
from sidequest.genre.models.gear import GearDef
from sidequest.server.dispatch.gear_resolve import merge_gear_catalog


def _g(id_, name, **kw):
    return GearDef.model_validate({"id": id_, "name": name, **kw})


def test_world_adds_new_gear():
    baseline = [_g("trench_coat", "Trench Coat")]
    world = [_g("zoot_suit", "Zoot Suit")]
    merged = merge_gear_catalog(baseline, world)
    assert [g.id for g in merged] == ["trench_coat", "zoot_suit"]  # baseline order first


def test_world_overrides_same_id_presentation():
    baseline = [_g("trench_coat", "Trench Coat", description="standard")]
    world = [_g("trench_coat", "Oilskin", description="world reskin")]
    merged = merge_gear_catalog(baseline, world)
    assert len(merged) == 1
    assert merged[0].name == "Oilskin" and merged[0].description == "world reskin"


def test_empty_world_returns_baseline():
    baseline = [_g("trench_coat", "Trench Coat")]
    assert merge_gear_catalog(baseline, []) == baseline
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_gear_resolve.py -v`
Expected: FAIL — `ModuleNotFoundError: ... gear_resolve`.

- [ ] **Step 3: Write the merge implementation**

```python
# sidequest/server/dispatch/gear_resolve.py
"""Genre→world merge for Fate gear (ADR-144 D5). Mirrors the paradigm-neutral
by-id union of inventory_resolve.merge_inventory_catalog, minus the verbatim
mechanical-lock (Fate gear has no SRD mechanical envelope — it is bespoke
flavor; a world may override any field). Baseline order preserved; world-added
ids follow."""

from __future__ import annotations

from sidequest.genre.models.gear import GearDef


def merge_gear_catalog(baseline: list[GearDef], world: list[GearDef]) -> list[GearDef]:
    by_id: dict[str, GearDef] = {g.id: g for g in baseline}
    added: list[GearDef] = []
    for w in world:
        if w.id in by_id:
            by_id[w.id] = w   # world wholly overrides a same-id gear (all-flavor model)
        else:
            added.append(w)
    return list(by_id.values()) + added
```

- [ ] **Step 4: Run merge test — verify pass**

Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_gear_resolve.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Add the `gear` field to the config models**

In `sidequest/genre/models/pack.py`, add to `GenrePack` (beside `inventory: InventoryConfig | None = None` at line 407):

```python
from sidequest.genre.models.gear import GearDef  # top of file
# ...
    gear: list[GearDef] = Field(default_factory=list)   # ADR-144 D5 Fate gear
```

And the identical field to `World` (beside its `inventory` at line 274):

```python
    gear: list[GearDef] = Field(default_factory=list)
```

- [ ] **Step 6: Write the loader-wiring test**

```python
# append to tests/server/dispatch/test_gear_resolve.py
from pathlib import Path

from sidequest.genre.loader import load_genre_pack


def test_loader_reads_genre_gear_yaml(tmp_path: Path):
    pack = tmp_path / "demo_pack"
    (pack / "worlds").mkdir(parents=True)
    (pack / "rules.yaml").write_text("ruleset: fate\nfate:\n  starting_gear: {}\n")
    (pack / "gear.yaml").write_text(
        "- id: trench_coat\n  name: Trench Coat\n"
        "  grants_aspects:\n    - text: Collar Always Up\n"
    )
    loaded = load_genre_pack(pack)
    assert any(g.id == "trench_coat" for g in loaded.gear)
```

> If `load_genre_pack` requires other mandatory pack files to load a bare fixture,
> reuse the minimal-pack fixture from an existing loader test in
> `tests/genre/` (search `load_genre_pack(` in tests) rather than hand-rolling one.

- [ ] **Step 7: Wire the loader (mirror the `archetypes.yaml` raw pattern)**

In `sidequest/genre/loader.py`, beside the genre inventory load (~line 1936):

```python
from sidequest.genre.models.gear import GearDef  # top of loader.py

# genre tier (~line 1936, next to the inventory load):
_gear_raw = _load_yaml_raw_optional(path / "gear.yaml")
gear: list[GearDef] = (
    [GearDef.model_validate(g) for g in _gear_raw] if isinstance(_gear_raw, list) else []
)
# ... pass gear=gear into the GenrePack(...) construction alongside inventory=...
```

```python
# world tier (~line 1616, next to world_inventory):
_world_gear_raw = _load_yaml_raw_optional(world_path / "gear.yaml")
world_gear: list[GearDef] = (
    [GearDef.model_validate(g) for g in _world_gear_raw]
    if isinstance(_world_gear_raw, list) else []
)
# ... pass gear=world_gear into the World(...) construction alongside inventory=...
```

- [ ] **Step 8: Run loader test — verify pass**

Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_gear_resolve.py -v`
Expected: PASS (all)

- [ ] **Step 9: Commit**

```bash
git add sidequest/server/dispatch/gear_resolve.py sidequest/genre/loader.py \
        sidequest/genre/models/pack.py tests/server/dispatch/test_gear_resolve.py
git commit -m "feat(114-10): load + merge gear.yaml (genre+world by-id union)"
```

---

### Task 5: `fate.gear_compiled` OTEL span

**Files:**
- Modify: `sidequest/telemetry/spans/fate.py` (mirror `fate_point_delta_span` ~line 114)
- Test: `tests/telemetry/test_fate_gear_compiled_span.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/telemetry/test_fate_gear_compiled_span.py
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from sidequest.telemetry.spans.fate import fate_gear_compiled_span


def _recording_tracer():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return provider.get_tracer("test"), exporter


def test_gear_compiled_span_records_attributes():
    tracer, exporter = _recording_tracer()
    fate_gear_compiled_span(
        archetype="Detective",
        gear_id="custom_38",
        aspects_placed=["Collar Always Up"],
        stunts_added=["From Cover"],
        refresh_before=3,
        refresh_after=2,
        _tracer=tracer,
    )
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    s = spans[0]
    assert s.name == "fate.gear_compiled"
    assert s.attributes["gear_id"] == "custom_38"
    assert s.attributes["refresh_debited"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/telemetry/test_fate_gear_compiled_span.py -v`
Expected: FAIL — `ImportError: cannot import name 'fate_gear_compiled_span'`.

- [ ] **Step 3: Write minimal implementation**

Append to `sidequest/telemetry/spans/fate.py`, mirroring `fate_point_delta_span`:

```python
def fate_gear_compiled_span(
    *,
    archetype: str,
    gear_id: str,
    aspects_placed: list[str],
    stunts_added: list[str],
    refresh_before: int,
    refresh_after: int,
    _tracer: trace.Tracer | None = None,
    **attrs: Any,
) -> None:
    """Emit ``fate.gear_compiled`` — one gear item materialized onto a sheet at
    chargen. The GM panel lie-detector reads this to prove gear actually fired."""
    attributes: dict[str, Any] = {
        "field": "gear_compiled",
        "archetype": archetype,
        "gear_id": gear_id,
        "aspects_placed": list(aspects_placed),
        "stunts_added": list(stunts_added),
        "refresh_before": refresh_before,
        "refresh_after": refresh_after,
        "refresh_debited": refresh_before - refresh_after,
        **attrs,
    }
    with Span.open("fate.gear_compiled", attributes, tracer_override=_tracer):
        pass
```

**Mandatory:** span helpers in this module MUST register a route in `SPAN_ROUTES`
(`SpanRoute` from `sidequest/telemetry/spans/_core.py`) — calling `Span.open` alone
does not surface the typed event to the GM panel. Add, beside the existing
`SPAN_ROUTES["fate.fate_point.delta"] = SpanRoute(...)` entry (fate.py:50):

```python
SPAN_ROUTES["fate.gear_compiled"] = SpanRoute(
    event_type="state_transition",
    component="fate",
    extract=lambda span: {
        "field": "gear_compiled",
        "archetype": (span.attributes or {}).get("archetype", ""),
        "gear_id": (span.attributes or {}).get("gear_id", ""),
        "refresh_debited": (span.attributes or {}).get("refresh_debited", 0),
    },
)
```

Extend the Step 1 test to assert the route is registered:

```python
def test_gear_compiled_route_registered():
    from sidequest.telemetry.spans._core import SPAN_ROUTES
    assert "fate.gear_compiled" in SPAN_ROUTES
    assert SPAN_ROUTES["fate.gear_compiled"].component == "fate"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/telemetry/test_fate_gear_compiled_span.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add sidequest/telemetry/spans/fate.py tests/telemetry/test_fate_gear_compiled_span.py
git commit -m "feat(114-10): fate.gear_compiled OTEL span"
```

---

### Task 6: `compile_fate_sheet` — base no-op + `FateRulesetModule` override (gear → FateSheet)

**Files:**
- Modify: `sidequest/game/ruleset/base.py` — add a default `compile_fate_sheet(...) -> FateSheet | None` returning `None` (mirrors the `seed_chargen_resources` default at base.py:261, so the builder calls it unconditionally with no isinstance branch and no Fate import)
- Modify: `sidequest/game/ruleset/fate.py` — override it (imports `Stunt`, `GearDef`, `fate_gear_compiled_span`)
- Test: `tests/game/ruleset/test_fate_gear_compile.py`

**Contract:** `compile_fate_sheet(*, rules: RulesConfig, class_name: str, gear_catalog: list[GearDef]) -> FateSheet | None`.
Base returns `None` (non-Fate rulesets seed no sheet). The Fate override reads
`rules.fate` (raising `ValueError` if absent — No Silent Fallbacks), builds a fresh
`FateSheet(refresh=fate.base_refresh, fate_points=fate.base_refresh)`, looks up
`fate.starting_gear.get(class_name, [])`, resolves each id against `gear_catalog`
(fail loud on unknown id), appends each grant as an `Aspect`/`Stunt` stamped with
`source_gear`, debits refresh for stunt-grants beyond `free_stunts`, and emits one
span per gear item. Taking `rules` (not `FateConfig`) keeps the base signature
paradigm-neutral, exactly like `seed_chargen_resources(*, rules, ...)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/game/ruleset/test_fate_gear_compile.py
import pytest

from sidequest.genre.models.gear import GearDef
from sidequest.genre.models.rules import RulesConfig
from sidequest.game.ruleset.fate import FateRulesetModule


def _catalog():
    return [
        GearDef.model_validate({"id": "trench_coat", "name": "Trench Coat",
                                "grants_aspects": [{"text": "Collar Always Up"}]}),
        GearDef.model_validate({"id": "badge", "name": "Badge",
                                "grants_aspects": [{"text": "Authority", "kind": "permission"}]}),
        GearDef.model_validate({"id": "custom_38", "name": "Custom .38",
                                "grants_stunts": [{"name": "From Cover"}]}),
    ]


def _rules(starting_gear, *, base_refresh=3, free_stunts=3):
    return RulesConfig.model_validate(
        {"ruleset": "fate", "fate": {"base_refresh": base_refresh,
                                     "free_stunts": free_stunts,
                                     "starting_gear": starting_gear}}
    )


def test_compiles_aspects_and_permission_free():
    sheet = FateRulesetModule().compile_fate_sheet(
        rules=_rules({"Detective": ["trench_coat", "badge"]}),
        class_name="Detective", gear_catalog=_catalog(),
    )
    texts = {(a.text, a.kind, a.source_gear) for a in sheet.aspects}
    assert ("Collar Always Up", "character", "trench_coat") in texts
    assert ("Authority", "permission", "badge") in texts
    assert sheet.refresh == 3   # aspect-gear and permission-gear are free


def test_stunt_gear_debits_refresh_beyond_free_allotment():
    # free_stunts=0 => the single stunt-gear costs 1 refresh.
    sheet = FateRulesetModule().compile_fate_sheet(
        rules=_rules({"Detective": ["custom_38"]}, free_stunts=0),
        class_name="Detective", gear_catalog=_catalog(),
    )
    assert any(s.name == "From Cover" and s.source_gear == "custom_38" for s in sheet.stunts)
    assert sheet.refresh == 2


def test_unknown_gear_id_fails_loud():
    with pytest.raises(KeyError):
        FateRulesetModule().compile_fate_sheet(
            rules=_rules({"Detective": ["nonexistent"]}),
            class_name="Detective", gear_catalog=_catalog(),
        )


def test_missing_fate_block_fails_loud():
    rules = RulesConfig.model_validate({"ruleset": "fate"})  # no fate: block
    with pytest.raises(ValueError):
        FateRulesetModule().compile_fate_sheet(
            rules=rules, class_name="Detective", gear_catalog=_catalog())


def test_class_with_no_gear_returns_baseline_sheet():
    sheet = FateRulesetModule().compile_fate_sheet(
        rules=_rules({}), class_name="Drifter", gear_catalog=_catalog())
    assert sheet.aspects == [] and sheet.stunts == [] and sheet.refresh == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/game/ruleset/test_fate_gear_compile.py -v`
Expected: FAIL — `AttributeError: 'FateRulesetModule' object has no attribute 'compile_fate_sheet'`.

- [ ] **Step 3a: Add the base default (`base.py`, beside `seed_chargen_resources` ~line 261)**

```python
    def compile_fate_sheet(self, *, rules, class_name, gear_catalog):
        """Fate gear → FateSheet at chargen. Default: None (non-Fate rulesets
        seed no Fate sheet). Only FateRulesetModule overrides. ADR-144 D5."""
        return None
```

- [ ] **Step 3b: Write the Fate override (`fate.py`)**

Add imports and the method:

```python
from sidequest.game.fate_sheet import Aspect, FateSheet, Stunt  # add Stunt
from sidequest.genre.models.gear import GearDef
from sidequest.telemetry.spans.fate import fate_gear_compiled_span
```

```python
    def compile_fate_sheet(
        self,
        *,
        rules,
        class_name: str,
        gear_catalog: list[GearDef],
    ) -> FateSheet:
        """Compile the chosen class's starting gear into a fresh FateSheet
        (ADR-144 D5). Aspect-gear and permission-gear are free; stunt-gear beyond
        ``free_stunts`` debits refresh (Bind the Ruleset, Don't Balance It). Emits
        one span per gear item. Skills/non-gear aspects are F4 — not seeded here."""
        fate = rules.fate
        if fate is None:
            raise ValueError(
                "ruleset 'fate' requires a 'fate:' block in rules.yaml "
                "(No Silent Fallbacks)"
            )
        by_id = {g.id: g for g in gear_catalog}
        sheet = FateSheet(refresh=fate.base_refresh, fate_points=fate.base_refresh)
        stunt_count = 0
        for gear_id in fate.starting_gear.get(class_name, []):
            if gear_id not in by_id:
                raise KeyError(
                    f"starting_gear for class {class_name!r} references unknown "
                    f"gear id {gear_id!r} (no GearDef in the merged catalog)"
                )
            gear = by_id[gear_id]
            placed_aspects: list[str] = []
            for ga in gear.grants_aspects:
                sheet.aspects.append(Aspect(text=ga.text, kind=ga.kind, source_gear=gear_id))
                placed_aspects.append(ga.text)
            added_stunts: list[str] = []
            refresh_before = sheet.refresh
            for gs in gear.grants_stunts:
                sheet.stunts.append(
                    Stunt(name=gs.name, description=gs.description, source_gear=gear_id)
                )
                added_stunts.append(gs.name)
                stunt_count += 1
                if stunt_count > fate.free_stunts:
                    sheet.refresh = max(1, sheet.refresh - 1)  # SRD floor 1
            fate_gear_compiled_span(
                archetype=class_name,
                gear_id=gear_id,
                aspects_placed=placed_aspects,
                stunts_added=added_stunts,
                refresh_before=refresh_before,
                refresh_after=sheet.refresh,
            )
        sheet.fate_points = sheet.refresh  # start with fate points == refresh (SRD)
        return sheet
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/game/ruleset/test_fate_gear_compile.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add sidequest/game/ruleset/base.py sidequest/game/ruleset/fate.py \
        tests/game/ruleset/test_fate_gear_compile.py
git commit -m "feat(114-10): compile_fate_sheet base no-op + Fate override (gear -> FateSheet)"
```

---

### Task 7: Builder wiring — inject the gear catalog, set `fate_sheet` at build

**Architecture (pinned):** `CharacterBuilder` (`builder.py:986`) takes **no pack/world**
— its `__init__(self, scenes, rules, backstory_tables=None, *, rng=None)` (line 994)
holds only `self._rules` and the bound `self._ruleset = get_ruleset_module(rules.ruleset)`
(line 1041). World-tier catalogs are resolved in `sidequest/handlers/connect.py` and
injected via fluent `with_*()` methods (`with_classes`:1111, `with_chargen_defs`:1117,
`with_equipment_tables`:1101). We follow that exact pattern: add `with_gear_catalog`,
resolve+inject the merged gear in `connect.py`, and call `self._ruleset.compile_fate_sheet`
(unconditional — base returns `None`) at the `CreatureCore(...)` build site.

**Files:**
- Modify: `sidequest/game/builder.py` — `__init__` default `self._gear_catalog: list[GearDef] = []`; add `with_gear_catalog`; set `fate_sheet` in the `CreatureCore(...)` block (lines 2987-3000)
- Modify: `sidequest/handlers/connect.py` — merge genre+world gear, call `with_gear_catalog`, beside the existing `with_chargen_defs(...)` wiring
- Test: `tests/game/test_builder_fate_gear_wiring.py`

**This is the wiring test the suite requires** — it proves gear reaches a built
character through the real `build()` path, not just the module in isolation.

- [ ] **Step 1: Write the failing wiring test**

```python
# tests/game/test_builder_fate_gear_wiring.py
"""Wiring test: a character built through CharacterBuilder.build() under a fate
ruleset carries a FateSheet whose aspects came from the class's starting_gear.

Reuse the scene/choice fixture scaffold from an existing builder test — search
tests/game/ for `CharacterBuilder(` and `.build(` and copy its scene setup +
apply_choice calls that select a class. The NEW assertions are the last 3 lines."""
from sidequest.genre.models.gear import GearDef
from sidequest.genre.models.rules import RulesConfig
from sidequest.game.builder import CharacterBuilder


def test_built_fate_character_has_gear_aspects(<reused scene fixture args>):
    rules = RulesConfig.model_validate(
        {"ruleset": "fate",
         "fate": {"base_refresh": 3, "free_stunts": 3,
                  "starting_gear": {"Detective": ["trench_coat"]}}}
    )
    gear = [GearDef.model_validate(
        {"id": "trench_coat", "name": "Trench Coat",
         "grants_aspects": [{"text": "Collar Always Up"}]})]
    builder = (
        CharacterBuilder(scenes=<reused scenes>, rules=rules)
        .with_classes(<a class list whose display_name == "Detective">)
        .with_gear_catalog(gear)
    )
    # ... apply_choice(...) calls from the reused fixture that set class_hint=Detective ...
    char = builder.build("Sam Spade")
    assert char.core.fate_sheet is not None
    assert any(a.source_gear == "trench_coat" for a in char.core.fate_sheet.aspects)
```

> The `<reused ...>` placeholders are filled by copying an existing builder test's
> fixture — do not hand-invent scenes. The class string the builder resolves is
> `class_str = acc.class_hint or self._default_class or "Fighter"` (builder.py:2449),
> matched against `ClassDef.display_name` at line 2804. The fixture's class choice
> must set `class_hint` to a class whose `display_name == "Detective"`.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/game/test_builder_fate_gear_wiring.py -v`
Expected: FAIL — `AttributeError: 'CharacterBuilder' object has no attribute 'with_gear_catalog'`.

- [ ] **Step 3a: Add the fluent method + default (builder.py)**

In `__init__` (beside the other `self._<catalog>` defaults, ~lines 1083+):

```python
from sidequest.genre.models.gear import GearDef  # top of builder.py
# ...
        self._gear_catalog: list[GearDef] = []
```

Add the method beside `with_classes` (~line 1111):

```python
    def with_gear_catalog(self, gear: list[GearDef]) -> CharacterBuilder:
        """Attach the merged genre+world Fate gear catalog (ADR-144 D5). Read in
        build() by the bound ruleset's compile_fate_sheet. Empty for non-Fate
        packs (harmless — the base compile_fate_sheet returns None)."""
        self._gear_catalog = list(gear)
        return self
```

- [ ] **Step 3b: Set `fate_sheet` at the CreatureCore build site (builder.py:2987-3000)**

Just before the `core=CreatureCore(...)` construction, compute the sheet
(unconditional call; base returns `None` for non-Fate rulesets — no isinstance):

```python
        _fate_sheet = self._ruleset.compile_fate_sheet(
            rules=self._rules,
            class_name=class_str,          # builder.py:2449 — the chosen class
            gear_catalog=self._gear_catalog,
        )
```

Add the field to the existing `CreatureCore(...)` kwargs (after `spellcasting=wwn_spellcasting,`):

```python
        core=CreatureCore(
            name=name,
            description=(f"{indefinite_article(race_str).capitalize()} {race_str} {class_str}"),
            personality=acc.personality_trait or "Determined",
            level=1,
            xp=0,
            inventory=Inventory(items=items, gold=0),
            statuses=[],
            hp=hp,
            system_strain=system_strain,
            effort=wwn_effort,
            spellcasting=wwn_spellcasting,
            acquired_advancements=[],
            fate_sheet=_fate_sheet,        # NEW (ADR-144 D5)
        ),
```

- [ ] **Step 3c: Wire the merge in connect.py (`sidequest/handlers/connect.py`)**

Beside the existing `with_chargen_defs(...)` call, resolve the merged gear and inject it:

```python
from sidequest.server.dispatch.gear_resolve import merge_gear_catalog
# ...
        _world = genre_pack.worlds.get(world_slug) if world_slug else None
        _gear_catalog = merge_gear_catalog(
            genre_pack.gear,
            _world.gear if _world is not None else [],
        )
        builder = builder.with_gear_catalog(_gear_catalog)
```

> Match the local names already in scope in connect.py for the loaded `genre_pack`
> and `world_slug` (grep `with_chargen_defs(` in connect.py to find the exact site
> and the surrounding variable names).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/game/test_builder_fate_gear_wiring.py -v`
Expected: PASS

- [ ] **Step 5: Run the broader builder + ruleset suite for regressions**

Run: `cd sidequest-server && uv run pytest tests/game/ -k "builder or ruleset or fate" -v`
Expected: PASS. Non-Fate packs build unchanged — `compile_fate_sheet` returns `None`
for them, so `fate_sheet=None` (the CreatureCore default), identical to today.

- [ ] **Step 6: Commit**

```bash
git add sidequest/game/builder.py sidequest/handlers/connect.py \
        tests/game/test_builder_fate_gear_wiring.py
git commit -m "feat(114-10): inject gear catalog + set fate_sheet at chargen build"
```

---

### Task 8: Content validator — three Fate-gear invariants

**Files:**
- Modify: `sidequest/cli/validate/pack.py` (add three check functions; call them from the pack-validate aggregator)
- Test: `tests/cli/validate/test_fate_gear_invariants.py`

Invariants (all fail-loud, per No Silent Fallbacks):
1. **no-inventory-under-fate** — a `ruleset: fate` pack (genre or any world) shipping an `inventory.yaml` is a hard error (paradigm mismatch).
2. **dangling-gear-id** — every id in `rules.fate.starting_gear[*]` must resolve in the merged genre+world `gear.yaml` catalog.
3. **refresh-balance** — for each class in `starting_gear`, the count of stunt-grants across its gear must not exceed `free_stunts` unless `base_refresh - (stunts - free_stunts) >= 1` (i.e. refresh stays ≥ 1); report the offending class.

- [ ] **Step 1: Write the failing tests**

```python
# tests/cli/validate/test_fate_gear_invariants.py
from pathlib import Path

from sidequest.cli.validate.pack import (
    check_no_inventory_under_fate,
    check_gear_ids_resolve,
    check_fate_refresh_balance,
)


def _write(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def test_inventory_under_fate_is_error(tmp_path: Path):
    pack = tmp_path / "p"
    _write(pack / "rules.yaml", "ruleset: fate\nfate: {}\n")
    _write(pack / "inventory.yaml", "item_catalog: []\n")
    errs = check_no_inventory_under_fate(pack)
    assert errs and "inventory.yaml" in errs[0]


def test_no_inventory_under_fate_passes_when_absent(tmp_path: Path):
    pack = tmp_path / "p"
    _write(pack / "rules.yaml", "ruleset: fate\nfate: {}\n")
    assert check_no_inventory_under_fate(pack) == []


def test_dangling_gear_id_is_error(tmp_path: Path):
    pack = tmp_path / "p"
    _write(pack / "rules.yaml",
           "ruleset: fate\nfate:\n  starting_gear:\n    Detective: [ghost_item]\n")
    _write(pack / "gear.yaml", "- id: trench_coat\n  name: Trench Coat\n")
    errs = check_gear_ids_resolve(pack)
    assert errs and "ghost_item" in errs[0]


def test_refresh_balance_violation(tmp_path: Path):
    # base_refresh 3, free_stunts 0, three stunt-gears => refresh would be 0 (<1).
    pack = tmp_path / "p"
    _write(pack / "rules.yaml",
           "ruleset: fate\nfate:\n  base_refresh: 3\n  free_stunts: 0\n"
           "  starting_gear:\n    Heavy: [g1, g2, g3]\n")
    _write(pack / "gear.yaml",
           "- id: g1\n  name: G1\n  grants_stunts: [{name: A}]\n"
           "- id: g2\n  name: G2\n  grants_stunts: [{name: B}]\n"
           "- id: g3\n  name: G3\n  grants_stunts: [{name: C}]\n")
    errs = check_fate_refresh_balance(pack)
    assert errs and "Heavy" in errs[0]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd sidequest-server && uv run pytest tests/cli/validate/test_fate_gear_invariants.py -v`
Expected: FAIL — `ImportError` on the three new check functions.

- [ ] **Step 3: Implement the three checks**

```python
# in sidequest/cli/validate/pack.py
from sidequest.genre.models.gear import GearDef
from sidequest.genre.models.rules import RulesConfig


def _load_rules(pack_dir) -> RulesConfig | None:
    p = pack_dir / "rules.yaml"
    if not p.is_file():
        return None
    data, err = _read_yaml(p, "rules")
    if err or data is None:
        return None
    return RulesConfig.model_validate(data)


def _merged_gear_ids(pack_dir) -> set[str]:
    ids: set[str] = set()
    for gpath in [pack_dir / "gear.yaml", *(pack_dir / "worlds").glob("*/gear.yaml")]:
        if not gpath.is_file():
            continue
        data, err = _read_yaml(gpath, "gear")
        if err or not isinstance(data, list):
            continue
        for entry in data:
            try:
                ids.add(GearDef.model_validate(entry).id)
            except Exception:
                pass  # model-validation errors surface via _validate_list_of_model
    return ids


def check_no_inventory_under_fate(pack_dir) -> list[str]:
    rules = _load_rules(pack_dir)
    if rules is None or rules.ruleset != "fate":
        return []
    errs: list[str] = []
    for inv in [pack_dir / "inventory.yaml", *(pack_dir / "worlds").glob("*/inventory.yaml")]:
        if inv.is_file():
            errs.append(
                f"fate-gear: {inv} present under a ruleset:fate pack — Fate has no "
                f"equipment economy; delete inventory.yaml (ADR-144 D5)"
            )
    return errs


def check_gear_ids_resolve(pack_dir) -> list[str]:
    rules = _load_rules(pack_dir)
    if rules is None or rules.ruleset != "fate" or rules.fate is None:
        return []
    known = _merged_gear_ids(pack_dir)
    errs: list[str] = []
    for cls, ids in rules.fate.starting_gear.items():
        for gid in ids:
            if gid not in known:
                errs.append(
                    f"fate-gear: class {cls!r} starting_gear references unknown "
                    f"gear id {gid!r} (no GearDef in genre/world gear.yaml)"
                )
    return errs


def check_fate_refresh_balance(pack_dir) -> list[str]:
    rules = _load_rules(pack_dir)
    if rules is None or rules.ruleset != "fate" or rules.fate is None:
        return []
    # map gear id -> stunt count
    stunt_counts: dict[str, int] = {}
    for gpath in [pack_dir / "gear.yaml", *(pack_dir / "worlds").glob("*/gear.yaml")]:
        if not gpath.is_file():
            continue
        data, err = _read_yaml(gpath, "gear")
        if err or not isinstance(data, list):
            continue
        for entry in data:
            try:
                g = GearDef.model_validate(entry)
                stunt_counts[g.id] = len(g.grants_stunts)
            except Exception:
                pass
    cfg = rules.fate
    errs: list[str] = []
    for cls, ids in cfg.starting_gear.items():
        total_stunts = sum(stunt_counts.get(gid, 0) for gid in ids)
        net = cfg.base_refresh - max(0, total_stunts - cfg.free_stunts)
        if net < 1:
            errs.append(
                f"fate-gear: class {cls!r} has {total_stunts} stunt-gears with "
                f"free_stunts={cfg.free_stunts}/base_refresh={cfg.base_refresh}, "
                f"driving refresh to {net} (<1). Reduce stunt-gear or raise refresh."
            )
    return errs
```

Register the three in the aggregator `validate_pack_structure(pack_dir: Path,
schema_path: Path) -> tuple[list[str], list[str]]` (`pack.py:1244`), beside the
existing `all_errors.extend(...)` calls (the content-validation block at ~1302-1309):

```python
    all_errors.extend(check_no_inventory_under_fate(pack_dir))
    all_errors.extend(check_gear_ids_resolve(pack_dir))
    all_errors.extend(check_fate_refresh_balance(pack_dir))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd sidequest-server && uv run pytest tests/cli/validate/test_fate_gear_invariants.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add sidequest/cli/validate/pack.py tests/cli/validate/test_fate_gear_invariants.py
git commit -m "feat(114-10): content validator invariants for Fate gear"
```

---

### Task 9: Phase-A regression gate

- [ ] **Step 1: Run the server lint + format on touched files**

Run: `cd sidequest-server && uv run ruff check sidequest/genre/models/gear.py sidequest/game/ruleset/fate.py sidequest/game/ruleset/base.py sidequest/game/builder.py sidequest/handlers/connect.py sidequest/cli/validate/pack.py sidequest/server/dispatch/gear_resolve.py sidequest/genre/loader.py sidequest/genre/models/pack.py`
Expected: no errors.

- [ ] **Step 2: Run the full fate + builder + validate + genre suites**

Run: `cd sidequest-server && uv run pytest tests/game/ruleset tests/genre tests/telemetry/test_fate_gear_compiled_span.py tests/cli/validate tests/game/test_builder_fate_gear_wiring.py -v`
Expected: PASS. (Note from project memory: full parallel `tests/server/` can deadlock ~18 OTEL span-count tests — run any server-dispatch span tests with `-n0` if they hang.)

- [ ] **Step 3: Commit (if any lint fixes)**

```bash
git add -A && git commit -m "chore(114-10): phase-A lint/format cleanup"
```

---

## Phase B — Content migration (`sidequest-content`)

> Phase B has **no unit tests** — content invariants are checked by the pack
> validator (Task 8), per the project rule "no content in unit tests." Each task's
> "test" is `uv run python -m sidequest.cli.validate pack <pack_dir>` (run from
> `sidequest-server`, on Phase A's branch so the validator includes the new checks)
> going green.

**Per-pack recipe (apply to Tasks 10–13):**
1. `rules.yaml`: set `ruleset: fate` and add a `fate:` block (`base_refresh`, `free_stunts`, `starting_gear` keyed by each `allowed_classes` entry).
2. Delete every `inventory.yaml` (genre + worlds) and remove `starting_gold`/`currency` references.
3. Author `gear.yaml` at the genre tier (shared signature gear) — and world tier only where a world needs distinct gear.
4. Validate.

### Task 10: Migrate `pulp_noir`

**Files (content repo):**
- Modify: `genre_packs/pulp_noir/rules.yaml`
- Delete: `genre_packs/pulp_noir/inventory.yaml`, `genre_packs/pulp_noir/worlds/annees_folles/inventory.yaml`
- Create: `genre_packs/pulp_noir/gear.yaml`

- [ ] **Step 1: Add the fate binding to `rules.yaml`**

Add (the pack currently declares no `ruleset:` — it defaulted to native):

```yaml
ruleset: fate
fate:
  base_refresh: 3
  free_stunts: 3
  starting_gear:
    Detective: [trench_coat, snub_revolver, dog_eared_casebook]
    Brawler: [brass_knuckles, lucky_jaw]
    Grifter: [forged_papers, silver_tongue]
    Soldier of Fortune: [service_pistol, scarred_nerve]
    Scholar: [pocket_reference, keen_eye]
    Smuggler: [false_bottom_case, harbor_contacts]
    Performer: [stage_presence, concealed_derringer]
```

- [ ] **Step 2: Author `genre_packs/pulp_noir/gear.yaml`**

Each entry grants an aspect (free) or a stunt (refresh-priced). Example shape — author the full set referenced above:

```yaml
- id: trench_coat
  name: Trench Coat
  description: Collar up, belt cinched, the city's weather worn as armor.
  grants_aspects:
    - text: Collar Always Up
- id: snub_revolver
  name: Snub-Nose .38
  description: Five shots, close work, no questions.
  grants_stunts:
    - name: Close Work
      description: "+2 to Shoot when your target is in the same zone."
- id: dog_eared_casebook
  name: Dog-Eared Casebook
  grants_aspects:
    - text: I've Seen This Case Before
      kind: permission
# ... author every id referenced in starting_gear ...
```

Keep each class's **stunt-gear count ≤ free_stunts (3)** so the refresh invariant holds.

- [ ] **Step 3: Delete inventory files**

```bash
cd sidequest-content
git rm genre_packs/pulp_noir/inventory.yaml \
       genre_packs/pulp_noir/worlds/annees_folles/inventory.yaml
```

- [ ] **Step 4: Validate**

Run: `cd sidequest-server && uv run python -m sidequest.cli.validate pack ../sidequest-content/genre_packs/pulp_noir`
(entry: `sidequest/cli/validate/__main__.py:35` registers the `pack` command.)
Expected: no `fate-gear:` errors; no dangling gear ids; refresh balanced.

- [ ] **Step 5: Commit**

```bash
cd sidequest-content
git add genre_packs/pulp_noir
git commit -m "feat(114-10): migrate pulp_noir to ruleset:fate + gear.yaml"
```

### Task 11: Migrate `spaghetti_western`

Same recipe. `allowed_classes`: Gunslinger, Bounty Hunter, Outlaw, Drifter, Gambler, Marshal. Delete the **three** world `inventory.yaml` (`dust_and_lead`, `five_points`, `the_real_mccoy`); author one genre-tier `gear.yaml`. Western signature gear (e.g. `iron_on_hip` → stunt "Fastest Draw"; `long_coat` → aspect; `marshals_star` → permission aspect). Validate the pack, then commit `git add genre_packs/spaghetti_western`.

### Task 12: Migrate `tea_and_murder`

Same recipe. `allowed_classes`: Governess, Detective, Society, Doctor, Industrialist, Explorer, Clergyman. Note `combat_encounters: false` stays — gear here is overwhelmingly aspect/permission flavor (`calling_cards` → permission aspect "You Are Someone Here"; `doctors_bag` → permission; `keen_observation` → stunt). Delete genre + both world `inventory.yaml` (`glenross`, `blackthorn_moor`). Validate, commit `git add genre_packs/tea_and_murder`.

### Task 13: Migrate `wry_whimsy` (replace explicit `native`; Oz silver shoes stay narrator-placed)

Same recipe, with two specifics:
- `rules.yaml` currently has an **explicit `ruleset: native`** (line 17) — replace it with `ruleset: fate` and update the locked-decisions comment block.
- `allowed_classes`: Curious Child, Practical Servant, Earnest Scholar, Weary Soldier, Wayward Dreamer, Stubborn Skeptic. Gear is whimsical aspect flavor (`sensible_shoes` → aspect "An Anchor From Home"; `keepsake_from_home` → aspect; `borrowed_courage` → permission aspect).
- **Do NOT author the silver shoes in `gear.yaml`.** They are mid-game loot the Oz narrator places via create-an-advantage (spec worked example). The existing Oz `lore.yaml`/`archetypes.yaml` references to the silver shoes stay as narrative content — leave them untouched.
- Delete genre `inventory.yaml` (no world inventories exist).
- Validate, commit `git add genre_packs/wry_whimsy`.

### Task 14: Full content gate + push

- [ ] **Step 1: Validate all four packs**

Run, from `sidequest-server`, for each of `pulp_noir`, `spaghetti_western`, `tea_and_murder`, `wry_whimsy`:
`uv run python -m sidequest.cli.validate pack ../sidequest-content/genre_packs/<pack>`
Expected: all green, zero `fate-gear:` errors.

- [ ] **Step 2: Run the server test suite against the migrated content**

Run: `cd sidequest-server && uv run pytest -k "fate or builder or validate" -v`
Expected: PASS. (Project memory: some pre-existing WWN/seaboard fixture failures are unrelated — classify pre-existing, don't block.)

- [ ] **Step 3: Commit any final fixes and stop for review**

Phase B PRs target the content repo's `develop` branch (per repos.yaml). Server PR targets `develop`. Do not push to `main`.

---

## Self-Review

**Spec coverage:**
- `gear.yaml` schema (A2-i) → Task 1 ✓
- permission as aspect kind (P-i) → Task 2 ✓
- `source_gear` traceability → Tasks 2, 6 ✓
- `ruleset: fate` binding + `fate:` block → Task 3 ✓
- genre/world by-id merge (paradigm-neutral) → Task 4 ✓
- gear compiles into FateSheet at chargen (A) → Tasks 6, 7 ✓
- refresh invariant (aspect free / stunt costs refresh, K-i) → Tasks 6 (runtime), 8 (validator) ✓
- `fate.gear_compiled` OTEL span → Task 5 ✓
- no-inventory-under-fate hard error → Task 8 ✓
- drop inventory.yaml / starting_gold / currency for the 4 packs → Tasks 10–13 ✓
- silver shoes narrator-placed, NOT in gear.yaml → Task 13 ✓
- out-of-scope (F4 skills/aspects, UI, native deletion) → not in any task ✓
- mid-game acquisition needs no mechanism → no task (correct; nothing to build) ✓

**Placeholder scan:** All integration symbols are now pinned to exact file:line (loader entry `load_genre_pack` l.1814; config classes `GenrePack` l.407 / `World` l.274; builder `__init__` l.994, `class_str` l.2449, CreatureCore block l.2987; chargen wiring in `handlers/connect.py` beside `with_chargen_defs`; aggregator `validate_pack_structure` l.1244; `SPAN_ROUTES` registration; validate command `python -m sidequest.cli.validate pack`). The remaining `<reused scene fixture>` markers in the Task 7 wiring test are an explicit instruction to copy an existing builder test's scene scaffold (real, in-tree) — not invented work; the new assertions are spelled out. Phase-B `gear.yaml` bodies are author-complete recipes (content authoring is validator-gated, not unit-tested per project rule).

**Type consistency:** `GearDef`/`GearGrantAspect`/`GearGrantStunt` (Task 1) used identically in Tasks 4, 6, 7, 8. `FateConfig.base_refresh/free_stunts/starting_gear` (Task 3) read in Tasks 6, 8. `compile_fate_sheet(*, rules, class_name, gear_catalog)` — base no-op (Task 6, base.py) + Fate override (Task 6, fate.py) — called identically in Task 7. `with_gear_catalog(gear: list[GearDef])` (Task 7) matches the merge output of `merge_gear_catalog` (Task 4). `fate_gear_compiled_span(*, archetype, gear_id, aspects_placed, stunts_added, refresh_before, refresh_after)` (Task 5) called identically in Task 6. `source_gear` (Task 2) set in Task 6, asserted in Tasks 6, 7. Consistent.
