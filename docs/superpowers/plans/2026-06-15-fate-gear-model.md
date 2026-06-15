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
| `sidequest/genre/models/genre_pack.py` (+ world config) | `gear: list[GearDef]` field, mirroring `inventory` | Modify |
| `sidequest/genre/loader.py` | load `gear.yaml` at genre + world tier | Modify |
| `sidequest/server/dispatch/gear_resolve.py` | `merge_gear_catalog(baseline, world)` by-`id` union | Create |
| `sidequest/telemetry/spans/fate.py` | `fate_gear_compiled_span(...)` | Modify |
| `sidequest/game/ruleset/fate.py` | `compile_chargen_sheet(...)` (gear → FateSheet + span) | Modify |
| `sidequest/game/builder.py` | resolve merged gear catalog; set `fate_sheet` at CreatureCore build | Modify |
| `sidequest/cli/validate/pack.py` | three Fate-gear invariants | Modify |

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
- Modify: `sidequest/genre/loader.py` (genre load ~line 1936 next to `inventory`; world load ~line 1616), and the genre/world config models that hold `inventory` to also hold `gear`
- Test: `tests/server/dispatch/test_gear_resolve.py`

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

- [ ] **Step 5: Write the loader-wiring test**

```python
# append to tests/server/dispatch/test_gear_resolve.py
from pathlib import Path

from sidequest.genre.loader import load_genre_pack  # adjust to the real loader entry


def test_loader_reads_genre_gear_yaml(tmp_path: Path):
    pack = tmp_path / "demo_pack"
    (pack / "worlds").mkdir(parents=True)
    (pack / "rules.yaml").write_text("ruleset: fate\nfate:\n  starting_gear: {}\n")
    (pack / "gear.yaml").write_text(
        "- id: trench_coat\n  name: Trench Coat\n"
        "  grants_aspects:\n    - text: Collar Always Up\n"
    )
    loaded = load_genre_pack(pack)               # adjust to actual signature
    assert any(g.id == "trench_coat" for g in loaded.rules_gear())  # see Step 6 accessor
```

> NOTE: `load_genre_pack` and the gear accessor name must match the real loader
> entry point. Confirm the genre-pack load function and how `inventory` is exposed
> on the loaded object (scout located genre inventory at `loader.py:1936`), then
> mirror it for `gear`.

- [ ] **Step 6: Wire the loader (mirror `inventory`)**

In `sidequest/genre/loader.py`, beside the genre inventory load (~line 1936):

```python
from sidequest.genre.models.gear import GearDef

# genre tier (~line 1936, next to the inventory load):
gear: list[GearDef] = _load_yaml_list_optional(path / "gear.yaml", GearDef)
```

```python
# world tier (~line 1616, next to world_inventory):
world_gear: list[GearDef] = _load_yaml_list_optional(
    world_path / "gear.yaml", GearDef
)
```

Add a `gear: list[GearDef] = Field(default_factory=list)` field to the genre-pack
config model and the world config model that already carry `inventory` (follow the
exact class that holds `inventory: InventoryConfig | None`). If a list-optional
loader helper does not exist, add one mirroring `_load_yaml_optional` that returns
`[]` for an absent file and validates each entry as `GearDef`.

- [ ] **Step 7: Run loader test — verify pass**

Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_gear_resolve.py -v`
Expected: PASS (all)

- [ ] **Step 8: Commit**

```bash
git add sidequest/server/dispatch/gear_resolve.py sidequest/genre/loader.py \
        sidequest/genre/models/*.py tests/server/dispatch/test_gear_resolve.py
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

If the module maintains a `SPAN_ROUTES`/`SpanRoute` registry (scout noted one ~lines 50-330), add a route entry for `"fate.gear_compiled"` following the neighboring entries so the GM panel surfaces it.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/telemetry/test_fate_gear_compiled_span.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add sidequest/telemetry/spans/fate.py tests/telemetry/test_fate_gear_compiled_span.py
git commit -m "feat(114-10): fate.gear_compiled OTEL span"
```

---

### Task 6: `FateRulesetModule.compile_chargen_sheet` — gear → FateSheet

**Files:**
- Modify: `sidequest/game/ruleset/fate.py` (add method; imports `Stunt`, `fate_gear_compiled_span`, `GearDef`, `FateConfig`)
- Test: `tests/game/ruleset/test_fate_gear_compile.py`

**Contract:** `compile_chargen_sheet(*, class_name, fate_cfg, gear_catalog) -> FateSheet`.
Builds a fresh `FateSheet(refresh=fate_cfg.base_refresh, fate_points=fate_cfg.base_refresh)`,
looks up `fate_cfg.starting_gear.get(class_name, [])`, resolves each id against
`gear_catalog` (fail loud on unknown id), appends each grant as an `Aspect`/`Stunt`
stamped with `source_gear`, debits refresh by the number of stunt-grants beyond
`free_stunts`, and emits one span per gear item.

- [ ] **Step 1: Write the failing test**

```python
# tests/game/ruleset/test_fate_gear_compile.py
import pytest

from sidequest.genre.models.gear import GearDef
from sidequest.genre.models.rules import FateConfig
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


def test_compiles_aspects_and_permission_free():
    mod = FateRulesetModule()
    cfg = FateConfig(base_refresh=3, free_stunts=3,
                     starting_gear={"Detective": ["trench_coat", "badge"]})
    sheet = mod.compile_chargen_sheet(class_name="Detective", fate_cfg=cfg,
                                      gear_catalog=_catalog())
    texts = {(a.text, a.kind, a.source_gear) for a in sheet.aspects}
    assert ("Collar Always Up", "character", "trench_coat") in texts
    assert ("Authority", "permission", "badge") in texts
    assert sheet.refresh == 3   # aspect-gear and permission-gear are free


def test_stunt_gear_debits_refresh_beyond_free_allotment():
    mod = FateRulesetModule()
    # free_stunts=0 => the single stunt-gear costs 1 refresh.
    cfg = FateConfig(base_refresh=3, free_stunts=0,
                     starting_gear={"Detective": ["custom_38"]})
    sheet = mod.compile_chargen_sheet(class_name="Detective", fate_cfg=cfg,
                                      gear_catalog=_catalog())
    assert any(s.name == "From Cover" and s.source_gear == "custom_38" for s in sheet.stunts)
    assert sheet.refresh == 2


def test_unknown_gear_id_fails_loud():
    mod = FateRulesetModule()
    cfg = FateConfig(starting_gear={"Detective": ["nonexistent"]})
    with pytest.raises(KeyError):
        mod.compile_chargen_sheet(class_name="Detective", fate_cfg=cfg, gear_catalog=_catalog())


def test_class_with_no_gear_returns_baseline_sheet():
    mod = FateRulesetModule()
    cfg = FateConfig(base_refresh=3, starting_gear={})
    sheet = mod.compile_chargen_sheet(class_name="Drifter", fate_cfg=cfg, gear_catalog=_catalog())
    assert sheet.aspects == [] and sheet.stunts == [] and sheet.refresh == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/game/ruleset/test_fate_gear_compile.py -v`
Expected: FAIL — `AttributeError: 'FateRulesetModule' object has no attribute 'compile_chargen_sheet'`.

- [ ] **Step 3: Write minimal implementation**

In `sidequest/game/ruleset/fate.py` add imports and the method:

```python
from sidequest.game.fate_sheet import Aspect, FateSheet, Stunt  # add Stunt
from sidequest.genre.models.gear import GearDef
from sidequest.genre.models.rules import FateConfig
from sidequest.telemetry.spans.fate import fate_gear_compiled_span
```

```python
    def compile_chargen_sheet(
        self,
        *,
        class_name: str,
        fate_cfg: FateConfig,
        gear_catalog: list[GearDef],
    ) -> FateSheet:
        """Build a chargen FateSheet by compiling the chosen class's starting
        gear into aspects/stunts (ADR-144 D5). Aspect-gear and permission-gear
        are free; stunt-gear beyond ``free_stunts`` debits refresh (Bind the
        Ruleset, Don't Balance It). Emits one span per gear item. Skills and
        non-gear aspects are F4 — not seeded here."""
        by_id = {g.id: g for g in gear_catalog}
        sheet = FateSheet(refresh=fate_cfg.base_refresh, fate_points=fate_cfg.base_refresh)
        stunt_count = 0
        for gear_id in fate_cfg.starting_gear.get(class_name, []):
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
                if stunt_count > fate_cfg.free_stunts:
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
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add sidequest/game/ruleset/fate.py tests/game/ruleset/test_fate_gear_compile.py
git commit -m "feat(114-10): FateRulesetModule.compile_chargen_sheet (gear -> FateSheet)"
```

---

### Task 7: Builder wiring — attach the compiled FateSheet at chargen

**Files:**
- Modify: `sidequest/game/builder.py` (hold merged gear catalog near pack content; set `fate_sheet` in the `CreatureCore(...)` build ~line 2986-3000)
- Test: `tests/game/test_builder_fate_gear_wiring.py`

**This is the wiring test the suite requires** — it proves gear reaches a built character through the real builder, not just the module in isolation.

- [ ] **Step 1: Write the failing wiring test**

```python
# tests/game/test_builder_fate_gear_wiring.py
"""Wiring test: a Fate-pack character built through CharacterBuilder carries a
FateSheet whose aspects came from the class's starting_gear. Uses a minimal
in-memory fate pack fixture."""
import pytest

from sidequest.game.builder import CharacterBuilder  # adjust to the real entry


@pytest.mark.fate_pack_fixture  # see fixture note in Step 3
def test_built_fate_character_has_gear_aspects(minimal_fate_pack):
    builder = CharacterBuilder(pack=minimal_fate_pack)   # adjust constructor
    char = builder.build_for_class("Detective")          # adjust to the real build API
    sheet = char.core.fate_sheet
    assert sheet is not None
    assert any(a.source_gear == "trench_coat" for a in sheet.aspects)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/game/test_builder_fate_gear_wiring.py -v`
Expected: FAIL — `char.core.fate_sheet is None` (builder doesn't compile gear yet).

- [ ] **Step 3: Wire the builder**

Where pack/world inventory is resolved for the builder, also resolve the merged
gear catalog once and hold it:

```python
from sidequest.game.ruleset.fate import FateRulesetModule
from sidequest.server.dispatch.gear_resolve import merge_gear_catalog

# near where self._rules / world content is established in __init__:
self._gear_catalog = merge_gear_catalog(
    self._pack.gear,                       # genre-tier gear (Task 4 field)
    getattr(self._world, "gear", []),      # world-tier gear, [] if no world/gear.yaml
)
```

At the `CreatureCore(...)` construction (~line 2986-3000), compute the fate sheet
and pass it (the `fate_sheet` field already exists on `CreatureCore`):

```python
_fate_sheet = None
if isinstance(self._ruleset, FateRulesetModule):
    if self._rules.fate is None:
        raise ValueError(
            "ruleset 'fate' requires a 'fate:' block in rules.yaml "
            "(No Silent Fallbacks)"
        )
    _fate_sheet = self._ruleset.compile_chargen_sheet(
        class_name=_resolved_class_name,   # the chosen allowed_classes entry
        fate_cfg=self._rules.fate,
        gear_catalog=self._gear_catalog,
    )

character = Character(
    core=CreatureCore(
        # ... existing fields ...
        spellcasting=wwn_spellcasting,
        fate_sheet=_fate_sheet,            # NEW
    ),
    # ...
)
```

> Confirm the exact local that holds the chosen class name (`_resolved_class_def`
> is in scope at the seed-resources call ~line 2866; use its name field, or the
> accumulated class choice). Bind `_resolved_class_name` to that string.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/game/test_builder_fate_gear_wiring.py -v`
Expected: PASS

- [ ] **Step 5: Run the broader builder + ruleset suite for regressions**

Run: `cd sidequest-server && uv run pytest tests/game/ -k "builder or ruleset or fate" -v`
Expected: PASS (no WN/native regressions — the fate branch is isinstance-gated).

- [ ] **Step 6: Commit**

```bash
git add sidequest/game/builder.py tests/game/test_builder_fate_gear_wiring.py
git commit -m "feat(114-10): wire compiled FateSheet into chargen builder (isinstance-gated)"
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

Wire the three into the pack-validate aggregator alongside the existing checks
(follow how `_validate_history_trope_refs` results are collected).

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

Run: `cd sidequest-server && uv run ruff check sidequest/genre/models/gear.py sidequest/game/ruleset/fate.py sidequest/cli/validate/pack.py sidequest/server/dispatch/gear_resolve.py`
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
> "test" is `sidequest-validate <pack>` going green. Run the server from Phase A's
> branch (the validator must include the new checks).

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
(adjust to the real validate entry point — confirm via `uv run sidequest-validate --help`)
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

Run the validator (or `just` recipe if one exists) over `pulp_noir`, `spaghetti_western`, `tea_and_murder`, `wry_whimsy`. Expected: all green, zero `fate-gear:` errors.

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

**Placeholder scan:** Phase-A tasks carry real test + impl code. Two flagged confirmations (loader entry-point name in Task 4; chosen-class local + builder gear-catalog hold-point in Task 7) are genuine "match the real symbol" notes, not deferred work — the surrounding code is complete. Phase-B gear.yaml bodies are illustrative-but-author-complete recipes (content authoring, validator-gated) — acceptable since content is not unit-tested.

**Type consistency:** `GearDef`/`GearGrantAspect`/`GearGrantStunt` (Task 1) used identically in Tasks 4, 6, 8. `FateConfig.base_refresh/free_stunts/starting_gear` (Task 3) used in Tasks 6, 7, 8. `compile_chargen_sheet(*, class_name, fate_cfg, gear_catalog)` (Task 6) called with the same kwargs in Task 7. `fate_gear_compiled_span(*, archetype, gear_id, aspects_placed, stunts_added, refresh_before, refresh_after)` (Task 5) called identically in Task 6. `source_gear` (Task 2) set in Task 6, asserted in Tasks 6, 7. Consistent.
