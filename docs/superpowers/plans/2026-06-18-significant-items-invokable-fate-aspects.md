# Significant Items → Invokable Fate Aspects — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a significant item *acquired during play* in a Fate-bound pack become an invokable aspect on the player's `FateSheet` — closing the gap where only chargen gear got that treatment.

**Architecture:** A new narrow module (`fate_item_promotion.py`) appends a matched item's authored aspects onto the *live* `FateSheet` without re-deriving the fate-point economy (the chargen compiler can't be reused — it resets `refresh`/`fate_points`). It is called from the `items_gained` apply path, gated on the recipient having a Fate sheet. A new `fate.item_promoted` OTEL span is the GM-panel lie-detector. Phase 1 = authored-catalog gear (aspects + permissions; stunts deferred). Phase 2 = narrator on-the-fly promotion (one capped aspect).

**Tech Stack:** Python 3.12 / FastAPI server, pydantic v2 models, OpenTelemetry spans, pytest (`uv run pytest`, `-n auto` default), `uv run ruff`.

## Global Constraints

- Backend is Python/FastAPI (ADR-082). Server git strategy is **github-flow: PRs target `develop`**, feature branches `feat/{description}`. Work on `feat/fate-item-aspects`.
- **No Silent Fallbacks** — fail loud; a deferred/skipped grant is *logged in the span*, never silently dropped.
- **No Stubbing** — no empty shells; every file added has a real consumer.
- **Don't Reinvent — Wire Up What Exists** — reuse the live `FateSheet`/`Aspect`/`invoke_aspect`/projection machinery; add only the promotion seam.
- **Every Test Suite Needs a Wiring Test** — Task 3 drives the real `_apply_narration_result_to_snapshot` and asserts the promoted aspect reaches both the sheet and the `FATE_STATE` projection.
- **No Source-Text Wiring Tests** — never `read_text()`/grep production source as an assertion. Use behavioral fixture-driven tests (Task 3) and OTEL-span capture via an injected `_tracer` (Task 1/2).
- **OTEL on every subsystem decision** — the promotion path emits `fate.item_promoted` (GM panel = lie detector).
- Run lint after each task: `uv run ruff format <files> && uv run ruff check <files>` (format only branch-touched files — bare `ruff format .` reformats ~167 files; see project memory).
- All commands run from `sidequest-server/`.

---

### Task 1: `fate.item_promoted` OTEL span

**Files:**
- Modify: `sidequest/telemetry/spans/fate.py` (add a `SPAN_ROUTES` entry, an emitter, and an `__all__` entry — mirror the existing `fate.gear_compiled` block at lines 655–669 and `fate_gear_compiled_span` at 1101–1134).
- Test: `tests/telemetry/test_fate_item_promoted_span.py`

**Interfaces:**
- Produces: `fate_item_promoted_span(*, actor: str, item_id: str, item_name: str, aspect_text: str, source: str, aspects_added: int, stunts_deferred: int, deduped: bool, _tracer: trace.Tracer | None = None, **attrs) -> None` and `SPAN_ROUTES["fate.item_promoted"]` (component `"fate"`, event_type `"state_transition"`).

- [ ] **Step 1: Write the failing test**

```python
# tests/telemetry/test_fate_item_promoted_span.py
"""The fate.item_promoted span (GM panel = lie detector): a gained item became
an invokable aspect on the FateSheet, or was a logged dedup no-op."""

from __future__ import annotations

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from sidequest.telemetry.spans._core import SPAN_ROUTES
from sidequest.telemetry.spans.fate import fate_item_promoted_span


class _FakeSpan:
    def __init__(self, attributes: dict) -> None:
        self.attributes = attributes


def test_item_promoted_route_registered_and_maps_fields():
    route = SPAN_ROUTES["fate.item_promoted"]
    assert route.component == "fate"
    assert route.event_type == "state_transition"
    fields = route.extract(
        _FakeSpan(
            {
                "actor": "Dorothy",
                "item_id": "narrator:silver_shoes",
                "item_name": "Silver Shoes",
                "aspect_text": "The Silver Shoes of the Dead Witch",
                "source": "catalog",
                "aspects_added": 1,
                "stunts_deferred": 0,
                "deduped": False,
            }
        )
    )
    assert fields["source"] == "catalog"
    assert fields["aspects_added"] == 1
    assert fields["stunts_deferred"] == 0
    assert fields["deduped"] is False


def test_item_promoted_emitter_fires_named_span():
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("test")

    fate_item_promoted_span(
        actor="Dorothy",
        item_id="narrator:silver_shoes",
        item_name="Silver Shoes",
        aspect_text="The Silver Shoes of the Dead Witch",
        source="catalog",
        aspects_added=1,
        stunts_deferred=0,
        deduped=False,
        _tracer=tracer,
    )

    spans = exporter.get_finished_spans()
    assert [s.name for s in spans] == ["fate.item_promoted"]
    assert spans[0].attributes["source"] == "catalog"
    assert spans[0].attributes["item_id"] == "narrator:silver_shoes"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/telemetry/test_fate_item_promoted_span.py -n0 -q`
Expected: FAIL — `KeyError: 'fate.item_promoted'` and `ImportError: cannot import name 'fate_item_promoted_span'`.

- [ ] **Step 3: Add the route + emitter + `__all__` entry**

In `sidequest/telemetry/spans/fate.py`, add this `SPAN_ROUTES` entry next to the other route literals (e.g. just after the `fate.gear_compiled` route block ending at line 669):

```python
# --- Significant-item promotion span (spec 2026-06-18; GM panel = lie detector) -
# A gained item was promoted to an invokable aspect on the FateSheet (or a logged
# dedup no-op). The GM-panel evidence that "the silver shoes are magic" is real
# mechanical backing (an aspect that adds +2), not narrator improvisation.
# ``source`` ∈ {"catalog", "narrator", ""}; ``stunts_deferred`` records any matched
# gear stunts NOT applied mid-game (the refresh-economy deferral). Literal key (no
# SPAN_* constant) — the routing-completeness lint only inspects SPAN_* constants.
SPAN_ROUTES["fate.item_promoted"] = SpanRoute(
    event_type="state_transition",
    component="fate",
    extract=lambda span: {
        "field": "item_promoted",
        "actor": (span.attributes or {}).get("actor", ""),
        "item_id": (span.attributes or {}).get("item_id", ""),
        "item_name": (span.attributes or {}).get("item_name", ""),
        "aspect_text": (span.attributes or {}).get("aspect_text", ""),
        "source": (span.attributes or {}).get("source", ""),
        "aspects_added": (span.attributes or {}).get("aspects_added", 0),
        "stunts_deferred": (span.attributes or {}).get("stunts_deferred", 0),
        "deduped": bool((span.attributes or {}).get("deduped", False)),
    },
)
```

Add this emitter next to `fate_gear_compiled_span` (after line 1134):

```python
def fate_item_promoted_span(
    *,
    actor: str,
    item_id: str,
    item_name: str,
    aspect_text: str,
    source: str,
    aspects_added: int,
    stunts_deferred: int,
    deduped: bool,
    _tracer: trace.Tracer | None = None,
    **attrs: Any,
) -> None:
    """Emit ``fate.item_promoted`` — a significant item gained in play became an
    invokable aspect on the FateSheet (spec 2026-06-18). ``source`` is "catalog"
    (matched authored gear) or "narrator" (on-the-fly promotion); ``deduped`` is
    True for a re-grant of an already-promoted item (a logged no-op, never a
    silent skip); ``stunts_deferred`` counts matched-gear stunts NOT applied
    mid-game. The GM-panel lie-detector that found loot has real mechanical
    backing, not just narrator flavor."""
    attributes: dict[str, Any] = {
        "field": "item_promoted",
        "actor": actor,
        "item_id": item_id,
        "item_name": item_name,
        "aspect_text": aspect_text,
        "source": source,
        "aspects_added": aspects_added,
        "stunts_deferred": stunts_deferred,
        "deduped": deduped,
        **attrs,
    }
    with Span.open("fate.item_promoted", attributes, tracer_override=_tracer):
        pass
```

Add `"fate_item_promoted_span"` to the `__all__` list (keep it alphabetically near `fate_harm_routed_span`).

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/telemetry/test_fate_item_promoted_span.py -n0 -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add sidequest/telemetry/spans/fate.py tests/telemetry/test_fate_item_promoted_span.py
git commit -m "feat(fate): add fate.item_promoted OTEL span for item→aspect promotion"
```

---

### Task 2: `fate_item_promotion.py` — the catalog promoter (Phase 1)

**Files:**
- Create: `sidequest/game/ruleset/fate_item_promotion.py`
- Test: `tests/game/test_fate_item_promotion.py`

**Interfaces:**
- Consumes: `Aspect`, `FateSheet` (`sidequest.game.fate_sheet`); `GearDef` (`sidequest.genre.models.inventory`); `_slugify` (`sidequest.game.item_catalog_resolution`); `fate_item_promoted_span` (Task 1).
- Produces:
  - `@dataclass(frozen=True) class ItemPromotionResult` with fields `promoted: bool`, `aspects_added: int`, `source: str`, `stunts_deferred: int`, `deduped: bool`.
  - `match_gained_gear(item_id: str, item_name: str, gear_defs: list[GearDef]) -> GearDef | None`
  - `promote_gained_item(*, sheet: FateSheet, item_id: str, item_name: str, gear_defs: list[GearDef], actor: str = "", _tracer=None) -> ItemPromotionResult` — **Task 4 extends this with a `narrator_aspect: str | None = None` keyword.**

- [ ] **Step 1: Write the failing tests**

```python
# tests/game/test_fate_item_promotion.py
"""Significant items gained in play promote to invokable Fate aspects (spec
2026-06-18). Phase 1: authored-catalog gear → aspects + permissions; stunts
deferred; dedup; the promoted aspect is mechanically real (+2 on a 4dF roll)."""

from __future__ import annotations

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from sidequest.game.fate_sheet import FateSheet
from sidequest.game.ruleset import get_ruleset_module
from sidequest.game.ruleset.fate_item_promotion import (
    ItemPromotionResult,
    match_gained_gear,
    promote_gained_item,
)
from sidequest.game.ruleset.fate_resolution import Opposition, resolve_action_from_faces
from sidequest.genre.models.inventory import GearDef, GearGrantAspect, GearGrantStunt


def _slippers() -> GearDef:
    return GearDef(
        id="silver_shoes",
        name="Silver Shoes",
        grants_aspects=[
            GearGrantAspect(text="The Silver Shoes of the Dead Witch", kind="character")
        ],
    )


def test_catalog_gear_promotes_aspect_with_back_link():
    sheet = FateSheet(skills={"Fight": 1})
    res = promote_gained_item(
        sheet=sheet,
        item_id="narrator:silver_shoes",
        item_name="Silver Shoes",
        gear_defs=[_slippers()],
        actor="Dorothy",
    )
    assert res == ItemPromotionResult(
        promoted=True, aspects_added=1, source="catalog", stunts_deferred=0, deduped=False
    )
    aspect = next(a for a in sheet.aspects if a.text == "The Silver Shoes of the Dead Witch")
    assert aspect.kind == "character"
    assert aspect.free_invokes == 0  # never free power; invoking costs a fate point
    assert aspect.source_gear == "narrator:silver_shoes"  # back-link is the item id


def test_permission_kind_is_preserved():
    gear = GearDef(
        id="ruby_lens",
        name="Ruby Lens",
        grants_aspects=[GearGrantAspect(text="Can See In The Dark", kind="permission")],
    )
    sheet = FateSheet()
    promote_gained_item(
        sheet=sheet, item_id="ruby_lens", item_name="Ruby Lens", gear_defs=[gear], actor="X"
    )
    assert sheet.aspects[0].kind == "permission"


def test_matched_gear_stunts_are_deferred_not_applied():
    gear = GearDef(
        id="click_heels",
        name="Charmed Heels",
        grants_aspects=[GearGrantAspect(text="Charmed Heels", kind="character")],
        grants_stunts=[GearGrantStunt(name="Click Three Times", description="Teleport home")],
    )
    sheet = FateSheet()
    res = promote_gained_item(
        sheet=sheet, item_id="click_heels", item_name="Charmed Heels", gear_defs=[gear], actor="X"
    )
    assert res.aspects_added == 1
    assert res.stunts_deferred == 1
    assert sheet.stunts == []  # the stunt was NOT applied (refresh-economy deferral)


def test_no_gear_match_is_not_promoted():
    sheet = FateSheet()
    res = promote_gained_item(
        sheet=sheet, item_id="narrator:banjo", item_name="Banjo", gear_defs=[_slippers()], actor="X"
    )
    assert res.promoted is False
    assert res.aspects_added == 0
    assert sheet.aspects == []


def test_second_grant_of_same_item_is_a_dedup_noop():
    sheet = FateSheet()
    promote_gained_item(
        sheet=sheet, item_id="narrator:silver_shoes", item_name="Silver Shoes",
        gear_defs=[_slippers()], actor="X",
    )
    res2 = promote_gained_item(
        sheet=sheet, item_id="narrator:silver_shoes", item_name="Silver Shoes",
        gear_defs=[_slippers()], actor="X",
    )
    assert res2.deduped is True
    assert res2.promoted is False
    assert len([a for a in sheet.aspects if a.source_gear == "narrator:silver_shoes"]) == 1


def test_match_gained_gear_mirrors_conservative_matching():
    gear_defs = [_slippers()]
    assert match_gained_gear("narrator:silver_shoes", "Silver Shoes", gear_defs) is not None
    assert match_gained_gear("", "silver shoes", gear_defs) is not None  # case-folded name
    assert match_gained_gear("", "Silver", gear_defs) is None  # no fuzzy/partial match


def test_promoted_aspect_is_mechanically_real_plus_two():
    sheet = FateSheet(skills={"Fight": 1}, fate_points=3)
    promote_gained_item(
        sheet=sheet, item_id="narrator:silver_shoes", item_name="Silver Shoes",
        gear_defs=[_slippers()], actor="Dorothy",
    )
    module = get_ruleset_module("fate")
    bonus = module.invoke_aspect(
        sheet=sheet, aspect_text="The Silver Shoes of the Dead Witch", actor="Dorothy"
    )
    assert bonus == 2
    out = resolve_action_from_faces(
        skill_rating=1, opposition=Opposition(value=0, kind="passive"),
        faces=(0, 0, 0, 0), invoke_bonus=bonus,
    )
    assert out.ladder_total == 3  # skill 1 + faces 0 + invoke +2


def test_emits_item_promoted_span():
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    sheet = FateSheet()
    promote_gained_item(
        sheet=sheet, item_id="narrator:silver_shoes", item_name="Silver Shoes",
        gear_defs=[_slippers()], actor="Dorothy", _tracer=provider.get_tracer("t"),
    )
    spans = exporter.get_finished_spans()
    assert [s.name for s in spans] == ["fate.item_promoted"]
    assert spans[0].attributes["source"] == "catalog"
    assert spans[0].attributes["aspects_added"] == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/game/test_fate_item_promotion.py -n0 -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'sidequest.game.ruleset.fate_item_promotion'`.

- [ ] **Step 3: Write the module**

```python
# sidequest/game/ruleset/fate_item_promotion.py
"""Promote a significant item gained in play to an invokable Fate aspect (spec
2026-06-18-significant-items-invokable-fate-aspects-design.md).

The runtime sibling of chargen's ``compile_gear_onto_sheet``. It is deliberately
SEPARATE: the chargen compiler rebuilds the whole refresh/fate-point economy from
scratch (``sheet.fate_points = refresh_after``), which is destructive mid-session.
This promoter appends authored aspects/permissions onto a LIVE sheet WITHOUT
touching ``refresh``/``fate_points``. Matched-gear STUNTS are deferred (they debit
refresh — a milestone-advancement decision) and only counted, never applied.

The match mirrors ``resolve_gained_item_dict``'s conservative exact discipline
(id → slug → case-folded name); a partial name never binds. The back-link is the
inventory item's id on ``Aspect.source_gear`` (and the dedup key), so the GM panel
traces the aspect to the item and a re-grant is a logged no-op."""

from __future__ import annotations

from dataclasses import dataclass

from opentelemetry import trace

from sidequest.game.fate_sheet import Aspect, FateSheet
from sidequest.game.item_catalog_resolution import _slugify
from sidequest.genre.models.inventory import GearDef
from sidequest.telemetry.spans.fate import fate_item_promoted_span


@dataclass(frozen=True)
class ItemPromotionResult:
    """Outcome of a promotion attempt. ``promoted`` is True iff an aspect was
    actually appended (the inventory ``promoted`` flag tracks this)."""

    promoted: bool
    aspects_added: int
    source: str
    stunts_deferred: int
    deduped: bool


def match_gained_gear(
    item_id: str, item_name: str, gear_defs: list[GearDef]
) -> GearDef | None:
    """Conservative exact match of a gained item against the Fate gear set —
    mirrors ``resolve_gained_item_dict`` (id → slug → case-folded name). Never
    fuzzy: "Silver" must not bind "Silver Shoes"."""
    if not gear_defs:
        return None
    name = " ".join(str(item_name or "").split())
    raw_id = str(item_id or "").strip()
    if raw_id.startswith("narrator:"):
        raw_id = raw_id[len("narrator:") :]
    by_id = {g.id: g for g in gear_defs}
    match = by_id.get(raw_id) if raw_id else None
    if match is None and name:
        slug = _slugify(name)
        match = by_id.get(slug)
    if match is None and name:
        by_name = {g.name.strip().casefold(): g for g in gear_defs}
        match = by_name.get(name.casefold())
    return match


def promote_gained_item(
    *,
    sheet: FateSheet,
    item_id: str,
    item_name: str,
    gear_defs: list[GearDef],
    actor: str = "",
    _tracer: trace.Tracer | None = None,
) -> ItemPromotionResult:
    """Promote a just-gained item to aspect(s) on ``sheet`` (Phase 1: catalog).

    Dedup first: a second grant of an already-promoted item is a logged no-op.
    Then match against ``gear_defs`` and append each ``grants_aspects`` entry as a
    character/permission Aspect (free_invokes 0, source_gear=item_id). Stunts on
    the matched gear are counted (``stunts_deferred``) but NOT applied."""
    # Dedup — never re-promote the same inventory item; log it (No Silent Fallbacks).
    if any(a.source_gear == item_id for a in sheet.aspects):
        fate_item_promoted_span(
            actor=actor, item_id=item_id, item_name=item_name, aspect_text="",
            source="", aspects_added=0, stunts_deferred=0, deduped=True, _tracer=_tracer,
        )
        return ItemPromotionResult(
            promoted=False, aspects_added=0, source="", stunts_deferred=0, deduped=True
        )

    gear = match_gained_gear(item_id, item_name, gear_defs)
    if gear is None:
        return ItemPromotionResult(
            promoted=False, aspects_added=0, source="", stunts_deferred=0, deduped=False
        )

    added = 0
    first_text = ""
    for grant in gear.grants_aspects:
        sheet.aspects.append(Aspect(text=grant.text, kind=grant.kind, source_gear=item_id))
        if not first_text:
            first_text = grant.text
        added += 1
    stunts_deferred = len(gear.grants_stunts)

    if added == 0 and stunts_deferred == 0:
        # Matched pure-flavor gear (a hat is a hat) — nothing to grant, no span.
        return ItemPromotionResult(
            promoted=False, aspects_added=0, source="catalog", stunts_deferred=0, deduped=False
        )

    fate_item_promoted_span(
        actor=actor, item_id=item_id, item_name=item_name, aspect_text=first_text,
        source="catalog", aspects_added=added, stunts_deferred=stunts_deferred,
        deduped=False, _tracer=_tracer,
    )
    return ItemPromotionResult(
        promoted=added > 0, aspects_added=added, source="catalog",
        stunts_deferred=stunts_deferred, deduped=False,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/game/test_fate_item_promotion.py -n0 -q`
Expected: PASS (8 passed). If `get_ruleset_module("fate")` errors, confirm the import path with `grep -n "def get_ruleset_module" sidequest/game/ruleset/registry.py` and adjust the import in the test only.

- [ ] **Step 5: Lint + Commit**

```bash
uv run ruff format sidequest/game/ruleset/fate_item_promotion.py tests/game/test_fate_item_promotion.py
uv run ruff check sidequest/game/ruleset/fate_item_promotion.py tests/game/test_fate_item_promotion.py
git add sidequest/game/ruleset/fate_item_promotion.py tests/game/test_fate_item_promotion.py
git commit -m "feat(fate): runtime item→aspect promoter (catalog path, stunts deferred)"
```

---

### Task 3: Wire the promoter into the item-gain path + mandatory wiring test

**Files:**
- Modify: `sidequest/server/narration_apply.py` (insert after the inventory append at line 4821–4822, inside the `for entry in result.items_gained` loop).
- Test: `tests/server/test_fate_item_promotion_wiring.py`

**Interfaces:**
- Consumes: `promote_gained_item` (Task 2); the in-scope locals `pack`, `recipient_char`, `item_dict`.
- Produces: a promoted aspect on `recipient_char.core.fate_sheet` and `item_dict["promoted"] = True`, reachable from the production apply path.

- [ ] **Step 1: Write the failing wiring test**

```python
# tests/server/test_fate_item_promotion_wiring.py
"""WIRING: the production items_gained path promotes a significant catalog item
to an invokable Fate aspect that reaches the FATE_STATE projection and adds +2 to
a real 4dF resolution (spec 2026-06-18). Drives the real
``_apply_narration_result_to_snapshot`` — no source-text assertions."""

from __future__ import annotations

import copy

from sidequest.agents.orchestrator import NarrationTurnResult
from sidequest.game.fate_sheet import FateSheet
from sidequest.game.ruleset import get_ruleset_module
from sidequest.game.ruleset.fate_projection import build_fate_state_payload
from sidequest.game.ruleset.fate_resolution import Opposition, resolve_action_from_faces
from sidequest.genre.models.inventory import GearDef, GearGrantAspect
from sidequest.genre.models.rules import FateConfig
from sidequest.server.narration_apply import _apply_narration_result_to_snapshot
from tests._helpers.session_room import room_for

_ASPECT = "The Silver Shoes of the Dead Witch"


def _slippers_gear() -> GearDef:
    return GearDef(
        id="silver_shoes",
        name="Silver Shoes",
        grants_aspects=[GearGrantAspect(text=_ASPECT, kind="character")],
    )


def test_gained_catalog_item_promotes_to_invokable_aspect(
    snapshot_with_pack, character_named_sam
):
    snap, base_pack = snapshot_with_pack
    sam = character_named_sam
    sam.core.fate_sheet = FateSheet(skills={"Fight": 1}, fate_points=3)  # fate-bound PC
    snap.characters.append(sam)
    snap.turn_manager.record_interaction()

    pack = copy.deepcopy(base_pack)
    pack.worlds = {}  # force genre-tier resolution (see template test, Epic 94 note)
    pack.rules.fate = FateConfig(gear_catalog=[_slippers_gear()])

    result = NarrationTurnResult(
        narration="You lift the silver shoes from the dead witch's feet.",
        items_gained=[{"name": "Silver Shoes", "id": "narrator:silver_shoes"}],
    )
    _apply_narration_result_to_snapshot(
        snap, result, sam.core.name, pack=pack, room=room_for(snap)
    )

    # 1) inventory still holds the item, now flagged promoted
    shoes = next(
        (it for it in sam.core.inventory.items if it.get("name") == "Silver Shoes"), None
    )
    assert shoes is not None and shoes.get("promoted") is True

    # 2) an invokable aspect landed on the sheet, back-linked to the item id
    sheet = sam.core.fate_sheet
    aspect = next((a for a in sheet.aspects if a.text == _ASPECT), None)
    assert aspect is not None
    assert aspect.kind == "character" and aspect.free_invokes == 0
    assert aspect.source_gear == "narrator:silver_shoes"

    # 3) it reaches the player-facing FATE_STATE projection
    payload = build_fate_state_payload(snap)
    sam_entry = next(c for c in payload.characters if c.name == sam.core.name)
    assert any(a.text == _ASPECT for a in sam_entry.aspects)

    # 4) it is mechanically real: invoking adds +2 to a 4dF resolution
    bonus = get_ruleset_module("fate").invoke_aspect(
        sheet=sheet, aspect_text=_ASPECT, actor=sam.core.name
    )
    out = resolve_action_from_faces(
        skill_rating=1, opposition=Opposition(value=0, kind="passive"),
        faces=(0, 0, 0, 0), invoke_bonus=bonus,
    )
    assert out.ladder_total == 3


def test_non_fate_pc_is_untouched(snapshot_with_pack, character_named_sam):
    """A PC with no Fate sheet: items_gained behaves exactly as before — no
    aspect, no promoted flag, no crash."""
    snap, base_pack = snapshot_with_pack
    sam = character_named_sam
    assert sam.core.fate_sheet is None  # the gate signal is absent
    snap.characters.append(sam)
    snap.turn_manager.record_interaction()

    pack = copy.deepcopy(base_pack)
    pack.worlds = {}

    result = NarrationTurnResult(
        narration="You pocket a curious bauble.",
        items_gained=[{"name": "Curious Bauble", "category": "treasure"}],
    )
    _apply_narration_result_to_snapshot(
        snap, result, sam.core.name, pack=pack, room=room_for(snap)
    )

    bauble = next(
        (it for it in sam.core.inventory.items if it.get("name") == "Curious Bauble"), None
    )
    assert bauble is not None
    assert "promoted" not in bauble
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/server/test_fate_item_promotion_wiring.py -n0 -q`
Expected: FAIL — `test_gained_catalog_item_promotes_to_invokable_aspect` fails at assertion 1 (`shoes.get("promoted")` is None; the promoter is not yet wired in). `test_non_fate_pc_is_untouched` should already PASS.

- [ ] **Step 3: Insert the promotion call**

In `sidequest/server/narration_apply.py`, immediately after line 4822 (`added_names.append(str(item_dict["name"]))`), inside the `for entry in result.items_gained or []:` loop, add:

```python
            # ADR-144 / spec 2026-06-18: on a Fate-bound PC, a significant item
            # gained in play promotes to an invokable aspect on the FateSheet.
            # Gate on the recipient HAVING a fate sheet — the same per-character
            # signal the projection uses; a non-Fate PC is untouched. Aspects +
            # permissions only; matched-gear stunts are deferred (counted in the
            # span, not applied). The promoter never touches refresh/fate_points.
            if recipient_char.core.fate_sheet is not None:
                from sidequest.game.ruleset.fate_item_promotion import promote_gained_item

                _fate_cfg = pack.rules.fate if pack is not None else None
                _gear_defs = list(_fate_cfg.gear_catalog) if _fate_cfg is not None else []
                _promo = promote_gained_item(
                    sheet=recipient_char.core.fate_sheet,
                    item_id=str(item_dict["id"]),
                    item_name=str(item_dict["name"]),
                    gear_defs=_gear_defs,
                    actor=recipient_char.core.name,
                )
                if _promo.promoted:
                    item_dict["promoted"] = True
```

(Use the function-local import to match the surrounding style at line 4778.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/server/test_fate_item_promotion_wiring.py -n0 -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Regression-check the existing item-gain path**

Run: `uv run pytest tests/server/test_item_gain_catalog_resolution.py tests/server/test_container_retrieval_state.py -n0 -q`
Expected: PASS (unchanged — the new block only fires when `recipient_char.core.fate_sheet is not None`).

- [ ] **Step 6: Lint + Commit**

```bash
uv run ruff format sidequest/server/narration_apply.py tests/server/test_fate_item_promotion_wiring.py
uv run ruff check sidequest/server/narration_apply.py tests/server/test_fate_item_promotion_wiring.py
git add sidequest/server/narration_apply.py tests/server/test_fate_item_promotion_wiring.py
git commit -m "feat(fate): wire item→aspect promotion into the items_gained apply path"
```

---

### Task 4: Narrator on-the-fly promotion (Phase 2 — the guarded spotlight)

**Files:**
- Modify: `sidequest/game/ruleset/fate_item_promotion.py` (add a `narrator_aspect` keyword to `promote_gained_item`).
- Modify: `sidequest/server/narration_apply.py` (pass `narrator_aspect=` from the entry).
- Test: `tests/game/test_fate_item_promotion.py` (add narrator-path cases); `tests/server/test_fate_item_promotion_wiring.py` (add a narrator-grant wiring case).

**Interfaces:**
- Produces: `promote_gained_item(*, sheet, item_id, item_name, gear_defs, actor="", narrator_aspect: str | None = None, _tracer=None) -> ItemPromotionResult`. When `narrator_aspect` is a non-empty string **and** no catalog gear matched, mint exactly one `Aspect(text=narrator_aspect, kind="character", free_invokes=0, source_gear=item_id)`; `source="narrator"`. Catalog match wins over the narrator hint (authored balance beats improvisation).

- [ ] **Step 1: Write the failing tests (append to `tests/game/test_fate_item_promotion.py`)**

```python
def test_narrator_aspect_mints_one_capped_character_aspect():
    sheet = FateSheet(fate_points=3)
    res = promote_gained_item(
        sheet=sheet, item_id="narrator:locket", item_name="Mysterious Locket",
        gear_defs=[], actor="Dorothy", narrator_aspect="The Locket That Hums Near Magic",
    )
    assert res.source == "narrator"
    assert res.aspects_added == 1
    aspect = sheet.aspects[0]
    assert aspect.kind == "character"
    assert aspect.free_invokes == 0  # narrator can make it TRUE, never STRONG
    assert aspect.source_gear == "narrator:locket"


def test_catalog_match_wins_over_narrator_hint():
    sheet = FateSheet()
    res = promote_gained_item(
        sheet=sheet, item_id="narrator:silver_shoes", item_name="Silver Shoes",
        gear_defs=[_slippers()], actor="X", narrator_aspect="Some Improvised Aspect",
    )
    assert res.source == "catalog"
    assert [a.text for a in sheet.aspects] == ["The Silver Shoes of the Dead Witch"]


def test_blank_narrator_aspect_is_no_promotion():
    sheet = FateSheet()
    for blank in ("", "   ", None):
        res = promote_gained_item(
            sheet=sheet, item_id="narrator:rock", item_name="Rock",
            gear_defs=[], actor="X", narrator_aspect=blank,
        )
        assert res.promoted is False
    assert sheet.aspects == []
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/game/test_fate_item_promotion.py -n0 -q -k "narrator or catalog_match"`
Expected: FAIL — `TypeError: promote_gained_item() got an unexpected keyword argument 'narrator_aspect'`.

- [ ] **Step 3: Add the narrator path**

In `promote_gained_item`, add the keyword and the fallback branch. Change the signature line to:

```python
def promote_gained_item(
    *,
    sheet: FateSheet,
    item_id: str,
    item_name: str,
    gear_defs: list[GearDef],
    actor: str = "",
    narrator_aspect: str | None = None,
    _tracer: trace.Tracer | None = None,
) -> ItemPromotionResult:
```

Then, replace the `if gear is None:` early-return block with a narrator fallback:

```python
    gear = match_gained_gear(item_id, item_name, gear_defs)
    if gear is None:
        # Phase 2: no authored gear → the narrator may promote ONE capped aspect.
        # free_invokes 0, kind character, no stunt possible — the game can make a
        # found thing TRUE, only an author can make it STRONG (Rule of Cool).
        text = (narrator_aspect or "").strip()
        if not text:
            return ItemPromotionResult(
                promoted=False, aspects_added=0, source="", stunts_deferred=0, deduped=False
            )
        sheet.aspects.append(Aspect(text=text, kind="character", source_gear=item_id))
        fate_item_promoted_span(
            actor=actor, item_id=item_id, item_name=item_name, aspect_text=text,
            source="narrator", aspects_added=1, stunts_deferred=0, deduped=False,
            _tracer=_tracer,
        )
        return ItemPromotionResult(
            promoted=True, aspects_added=1, source="narrator", stunts_deferred=0, deduped=False
        )
```

(The catalog branch below it is unchanged.)

- [ ] **Step 4: Run to verify pass**

Run: `uv run pytest tests/game/test_fate_item_promotion.py -n0 -q`
Expected: PASS (11 passed).

- [ ] **Step 5: Pass the narrator hint from the apply path**

In `sidequest/server/narration_apply.py`, in the block added in Task 3, add the `narrator_aspect` argument to the `promote_gained_item(...)` call:

```python
                _promo = promote_gained_item(
                    sheet=recipient_char.core.fate_sheet,
                    item_id=str(item_dict["id"]),
                    item_name=str(item_dict["name"]),
                    gear_defs=_gear_defs,
                    actor=recipient_char.core.name,
                    narrator_aspect=(str(entry.get("grants_aspect", "") or "").strip() or None),
                )
```

- [ ] **Step 6: Add the narrator-grant wiring case (append to `tests/server/test_fate_item_promotion_wiring.py`)**

```python
def test_narrator_grants_aspect_on_invented_item(snapshot_with_pack, character_named_sam):
    """A Fate PC gains an item the narrator invented (no catalog gear), annotated
    with grants_aspect → one capped invokable aspect lands on the sheet."""
    snap, base_pack = snapshot_with_pack
    sam = character_named_sam
    sam.core.fate_sheet = FateSheet(skills={"Will": 2}, fate_points=3)
    snap.characters.append(sam)
    snap.turn_manager.record_interaction()

    pack = copy.deepcopy(base_pack)
    pack.worlds = {}
    pack.rules.fate = FateConfig(gear_catalog=[])  # no authored gear

    result = NarrationTurnResult(
        narration="A locket, warm to the touch, hums as you pocket it.",
        items_gained=[
            {
                "name": "Mysterious Locket",
                "id": "narrator:mysterious_locket",
                "grants_aspect": "The Locket That Hums Near Magic",
            }
        ],
    )
    _apply_narration_result_to_snapshot(
        snap, result, sam.core.name, pack=pack, room=room_for(snap)
    )

    sheet = sam.core.fate_sheet
    aspect = next(
        (a for a in sheet.aspects if a.text == "The Locket That Hums Near Magic"), None
    )
    assert aspect is not None
    assert aspect.kind == "character" and aspect.free_invokes == 0
    assert aspect.source_gear == "narrator:mysterious_locket"
```

- [ ] **Step 7: Run + lint + commit**

```bash
uv run pytest tests/game/test_fate_item_promotion.py tests/server/test_fate_item_promotion_wiring.py -n0 -q
uv run ruff format sidequest/game/ruleset/fate_item_promotion.py sidequest/server/narration_apply.py tests/game/test_fate_item_promotion.py tests/server/test_fate_item_promotion_wiring.py
uv run ruff check sidequest/game/ruleset/fate_item_promotion.py sidequest/server/narration_apply.py tests/game/test_fate_item_promotion.py tests/server/test_fate_item_promotion_wiring.py
git add -A
git commit -m "feat(fate): narrator on-the-fly item promotion (one capped aspect, no stunt)"
```

---

### Task 5: Narrator tool-contract surfacing for `grants_aspect`

**Files:**
- Modify: the narrator tool/schema that documents `items_gained` entries (locate it — start with `grep -rn "items_gained" sidequest/agents/tools/ sidequest/agents/orchestrator.py`).
- Test: covered behaviorally by Task 4's `test_narrator_grants_aspect_on_invented_item`; the *prompt quality* (does the narrator set it appropriately, and only for genuinely significant items) is validated by **playtest**, not a unit test (per project rule: prompt changes are playtest-validated, and "No Source-Text Wiring Tests").

**Interfaces:**
- Consumes: the `grants_aspect` key already consumed by Task 4.
- Produces: the narrator now *knows* it may set `grants_aspect` on a significant found item.

- [ ] **Step 1: Locate the items_gained tool-field documentation**

Run: `grep -rn "items_gained" sidequest/agents/tools/ sidequest/agents/orchestrator.py`
Read the surrounding tool-input description / JSON-schema where each `items_gained` entry's keys (`name`, `id`, `category`, `from_container`, …) are documented to the narrator.

- [ ] **Step 2: Add the optional `grants_aspect` field documentation**

Add an optional `grants_aspect` string field to that entry description, with guardrail guidance copied verbatim:

> `grants_aspect` (optional): for a **genuinely significant** found item only (a named magic item, a relic, a thing the story will lean on), a short Fate aspect phrase the player can invoke — e.g. `"The Silver Shoes of the Dead Witch"`. Leave it OFF for mundane gear (a rope, a banjo, a torch). This grants narrative weight, never a free mechanical bonus: invoking it still costs the player a fate point.

Keep the change to documentation/schema only — the engine guardrails (one aspect, `free_invokes` 0, no stunt) are already enforced in Task 4 by construction.

- [ ] **Step 3: Run the consumption test + full fate suite**

Run: `uv run pytest tests/game/test_fate_item_promotion.py tests/server/test_fate_item_promotion_wiring.py -n0 -q`
Expected: PASS. (No new unit test here — the schema/prompt change is playtest-validated; the consumption path is already proven by Task 4.)

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat(fate): document optional grants_aspect on items_gained for the narrator"
```

- [ ] **Step 5: Full-suite gate before PR**

Run: `uv run pytest -q` (parallel default). If the OTEL span-count deadlock files appear (pre-existing, see project memory), re-run those serially with `-n0`.
Expected: green except known pre-existing failures (WWN-content fixture drift; MessageType count 54-vs-55). Confirm none are in the files this plan touched.

---

## Self-Review

**1. Spec coverage:**
- Trigger model C, catalog-first → Tasks 2/3 (catalog) before Tasks 4/5 (narrator). ✓
- Dual existence, aspect = single invoke-source → Task 2 appends to `sheet.aspects`; item stays in inventory with `promoted` flag (Task 3). ✓
- Power asymmetry (catalog aspects+permissions, stunts deferred; narrator one capped aspect) → Task 2 (`stunts_deferred`, no stunt apply), Task 4 (narrator one aspect, `free_invokes` 0, no stunt path). ✓
- Gate on Fate sheet presence → Task 3 `if recipient_char.core.fate_sheet is not None`; non-Fate untouched test. ✓
- Dedup as logged no-op → Task 2 dedup branch + span; test. ✓
- OTEL `fate.item_promoted` → Task 1 + span tests. ✓
- Projection reaches player → Task 3 assertion 3 (`build_fate_state_payload`). ✓
- +2 into real 4dF resolution → Task 2 + Task 3 assertion 4. ✓
- Mandatory wiring test → Task 3 drives real apply fn. ✓
- Content dependency (gear authored with grants) → named in spec; out of engine scope (no task — correct). ✓
- Open question (lost item → lingering aspect) → deferred in spec; no task — correct. ✓

**2. Placeholder scan:** No "TBD"/"handle edge cases"/"similar to". Task 5 is documentation whose test is explicitly playtest (justified, not a placeholder). All code steps show full code. ✓

**3. Type consistency:** `ItemPromotionResult(promoted, aspects_added, source, stunts_deferred, deduped)` used identically in Tasks 2 and 4. `promote_gained_item` signature extends additively (keyword-only `narrator_aspect` with default) so the Task 3 call site stays valid after Task 4. `Aspect(text, kind, source_gear, free_invokes)` matches `fate_sheet.py:38`. `resolve_action_from_faces(*, skill_rating, opposition, faces, invoke_bonus)` and `Opposition(value, kind)` match `fate_resolution.py`. `invoke_aspect(*, sheet, aspect_text, mode, actor)` matches `fate.py:305`. Span emitter kwargs match the route's `extract`. ✓
