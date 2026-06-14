# F1b — Fate Character Facet + Fate-Point Economy — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give a Fate-bound creature a Fate-shaped character sheet (aspects, skills, stunts, refresh, fate points, stress tracks, consequence slots) carried *alongside* the d20 `CreatureCore`, plus the full fate-point economy and the stress/consequence atomic mutators — every economy delta and every mark emitting an OTEL lie-detector span.

**Architecture:** `FateSheet` is pure, inert data (mirrors `SystemStrainPool` / `SpellcastingState`): it hangs off `CreatureCore` as an optional facet (`fate_sheet: FateSheet | None`), exactly like `system_strain` / `spellcasting` / `rig_pool`, so it round-trips through the existing `GameSnapshot.model_dump_json()` save path with **no Alembic migration**. All *rules* — spend/earn/refresh, invoke, compel, mark stress, take consequence, and their OTEL spans — live as methods on `FateRulesetModule` (created in F1a), exactly as `SystemStrainPool`'s rules live on `CwnRulesetModule.apply_system_strain`. The d20 stats/`HpPool` are untouched (a Fate creature simply *also* has this facet — no shoehorning).

**Tech Stack:** Python 3.14, pydantic v2, pytest (`-n0` for these), OpenTelemetry SDK, `uv`. **All paths below are under `sidequest-server/`.** Branch off `develop` (gitflow); feature branch `feat/f1b-fate-character-facet`.

**Decision of record:** ADR-144. **Design:** `docs/superpowers/specs/2026-06-14-fate-core-binding-replaces-native-design.md` §4.3 + §6. **Depends on:** F1a (`FateRulesetModule`, `fate_resolution.py`, `spans/fate.py`) merged.

---

## F1 slice map (context — this plan is F1b only)

| Slice | Scope | Status |
|-------|-------|--------|
| F1a | Resolution primitive + module registration + OTEL | merged (prereq) |
| **F1b** | Fate character facet (aspects, skills, stunts, refresh, fate points, stress, consequences) + fate-point economy | **this plan** |
| F1c | `fate_conflict.py` exchange engine | next plan |
| F1d | Dispatch routing by `isinstance(module, FateRulesetModule)` + end-to-end wiring | next plan |

F1b is independently testable and mergeable: it adds a data facet + economy methods reachable through the **real registered** `FateRulesetModule` and the **real** snapshot serializer. There is no conflict engine yet (F1c consumes the stress/consequence mutators; F1d wires a dispatch entry). That is intentional.

---

## Design boundaries (read before coding)

- **F1b owns:** the `FateSheet` data model, the fate-point economy (refresh/spend/earn/invoke/compel), and the **atomic** stress/consequence mutators (`mark_stress` checks ONE box; `take_consequence` fills ONE slot → it becomes an aspect). Each emits a span.
- **F1c owns (NOT here):** the *orchestration* — given an attack's shifts, decide which boxes/slots absorb it and whether the target is taken out. F1c calls F1b's atomic mutators. **Situation aspects** placed by create-advantage live on the *encounter* (F1c), not on the `FateSheet`.
- **Already done in F1a (do NOT redo):** `FateRulesetModule.awards_native_turn_xp` returns `False` (Fate advances by milestones). F1b relies on it; it adds no XP logic.

---

## File structure (F1b)

- **Create** `sidequest/game/fate_sheet.py` — `Aspect`, `Stunt`, `StressBox`, `StressTrack`, `Consequence`, `FateSheet`, `CONSEQUENCE_VALUES`. Pure data.
- **Modify** `sidequest/game/creature_core.py` — add the optional `fate_sheet: FateSheet | None = None` facet.
- **Modify** `sidequest/telemetry/spans/fate.py` — add six economy/facet span helpers + their `SPAN_ROUTES`.
- **Modify** `sidequest/telemetry/spans/__init__.py` — extend the F1a fate re-export to include the new helpers.
- **Modify** `sidequest/game/ruleset/fate.py` — add `FateEconomyError` + the economy and stress/consequence methods on `FateRulesetModule`.
- **Create** `tests/game/test_fate_sheet.py` — pure model tests + persistence round-trip.
- **Create** `tests/game/ruleset/test_fate_economy.py` — economy + mutator behavior + OTEL wiring through the real registered module.

---

## Task 1: The `FateSheet` pure-data facet

**Files:**
- Create: `sidequest/game/fate_sheet.py`
- Test: `tests/game/test_fate_sheet.py`

- [ ] **Step 1: Write the failing test**

Create `tests/game/test_fate_sheet.py`:

```python
from __future__ import annotations

from sidequest.game.fate_sheet import (
    CONSEQUENCE_VALUES,
    Aspect,
    Consequence,
    FateSheet,
    StressBox,
    StressTrack,
    Stunt,
)


def test_default_sheet_has_srd_baseline():
    sheet = FateSheet()
    # SRD baseline: refresh 3, fate points start at refresh.
    assert sheet.refresh == 3
    assert sheet.fate_points == 3
    # Two stress tracks, each two boxes valued 1 and 2.
    assert [b.value for b in sheet.stress["physical"].boxes] == [1, 2]
    assert [b.value for b in sheet.stress["mental"].boxes] == [1, 2]
    assert all(not b.checked for b in sheet.stress["physical"].boxes)
    # Four consequence slots, SRD shift-values, all open.
    assert [c.level for c in sheet.consequences] == ["mild", "moderate", "severe", "extreme"]
    assert [c.value for c in sheet.consequences] == [2, 4, 6, 8]
    assert all(c.aspect is None for c in sheet.consequences)


def test_consequence_values_table():
    assert CONSEQUENCE_VALUES == {"mild": 2, "moderate": 4, "severe": 6, "extreme": 8}


def test_all_aspects_includes_filled_consequences_only():
    sheet = FateSheet(
        aspects=[
            Aspect(text="Last Honest Cop in Vice", kind="high_concept"),
            Aspect(text="Can't Resist a Sob Story", kind="trouble"),
        ]
    )
    # An open consequence slot contributes no aspect.
    assert [a.text for a in sheet.all_aspects()] == [
        "Last Honest Cop in Vice",
        "Can't Resist a Sob Story",
    ]
    # Fill the mild slot — it now surfaces as an aspect.
    sheet.consequences[0].aspect = Aspect(
        text="Cracked Ribs", kind="consequence", free_invokes=1
    )
    assert [a.text for a in sheet.all_aspects()] == [
        "Last Honest Cop in Vice",
        "Can't Resist a Sob Story",
        "Cracked Ribs",
    ]


def test_models_reject_unknown_fields():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Aspect(text="x", kind="trouble", bogus=1)  # extra=forbid
    with pytest.raises(ValidationError):
        Stunt(name="x", bogus=1)
    with pytest.raises(ValidationError):
        StressBox(value=1, bogus=1)
    with pytest.raises(ValidationError):
        StressTrack(boxes=[], bogus=1)
    with pytest.raises(ValidationError):
        Consequence(level="mild", value=2, bogus=1)
    with pytest.raises(ValidationError):
        FateSheet(bogus=1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/game/test_fate_sheet.py -n0 -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'sidequest.game.fate_sheet'`

- [ ] **Step 3: Write minimal implementation**

Create `sidequest/game/fate_sheet.py`:

```python
"""Fate Core character facet — pure data (ADR-144 F1b, design §4.3).

A Fate-shaped sheet carried ALONGSIDE the d20 CreatureCore — it does NOT replace
stats/HpPool. A Fate-bound creature simply ALSO has this facet, mirroring how CWN
chrome adds ``system_strain`` and WWN adds ``spellcasting``. The model is inert:
the fate-point economy, stress marking, consequence-taking, and aspect invocation
— with their OTEL spans — live on ``FateRulesetModule`` (fate.py), exactly as
``SystemStrainPool``'s rules live on ``CwnRulesetModule.apply_system_strain``.

Faithful to the Fate Core SRD (Evil Hat, CC-BY):
- aspects: free-text phrases (high concept, trouble, others) — the LLM-narrator
  synergy ADR-144 turns on.
- skills: name -> ladder rating (the ladder int lives in fate_resolution.py).
- stunts: named special rules (the mechanical effect is content/F2; stored here).
- refresh / fate_points: the per-session economy.
- stress: physical + mental tracks of checkable boxes.
- consequences: mild(2)/moderate(4)/severe(6)/extreme(8) slots; a FILLED slot
  becomes an aspect (SRD: a consequence is an aspect with a free invoke for the
  attacker who inflicted it).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

AspectKind = Literal[
    "high_concept", "trouble", "character", "situation", "consequence", "boost"
]
ConsequenceLevel = Literal["mild", "moderate", "severe", "extreme"]
StressTrackName = Literal["physical", "mental"]

#: SRD consequence slot shift-values. A filled slot absorbs this many shifts.
CONSEQUENCE_VALUES: dict[str, int] = {"mild": 2, "moderate": 4, "severe": 6, "extreme": 8}


class Aspect(BaseModel):
    """A free-text Fate aspect. ``free_invokes`` is the count of unused free
    invocations on it (create-advantage and consequences grant these)."""

    model_config = {"extra": "forbid"}

    text: str
    kind: AspectKind
    free_invokes: int = 0


class Stunt(BaseModel):
    """A named stunt. The mechanical effect is authored as content (F2/F4); the
    engine spine in F1 only needs to carry the name/description."""

    model_config = {"extra": "forbid"}

    name: str
    description: str = ""


class StressBox(BaseModel):
    """One checkable stress box of a fixed ``value``."""

    model_config = {"extra": "forbid"}

    value: int
    checked: bool = False


class StressTrack(BaseModel):
    """An ordered list of stress boxes (physical or mental)."""

    model_config = {"extra": "forbid"}

    boxes: list[StressBox] = Field(default_factory=list)


class Consequence(BaseModel):
    """One consequence slot. ``aspect is None`` ⇒ open; a set ``aspect`` ⇒ filled
    (and the consequence is now an invokable aspect). ``value`` is the SRD
    absorption value for the slot's level (see ``CONSEQUENCE_VALUES``)."""

    model_config = {"extra": "forbid"}

    level: ConsequenceLevel
    value: int
    aspect: Aspect | None = None


def _default_stress() -> dict[str, StressTrack]:
    return {
        "physical": StressTrack(boxes=[StressBox(value=1), StressBox(value=2)]),
        "mental": StressTrack(boxes=[StressBox(value=1), StressBox(value=2)]),
    }


def _default_consequences() -> list[Consequence]:
    return [
        Consequence(level="mild", value=CONSEQUENCE_VALUES["mild"]),
        Consequence(level="moderate", value=CONSEQUENCE_VALUES["moderate"]),
        Consequence(level="severe", value=CONSEQUENCE_VALUES["severe"]),
        Consequence(level="extreme", value=CONSEQUENCE_VALUES["extreme"]),
    ]


class FateSheet(BaseModel):
    """The Fate-shaped facet on a CreatureCore (pure data; rules on FateRulesetModule).

    Skill/aspect/stunt CONTENT is authored per genre (F4) and seeded at chargen
    (F2/F4); F1b ships the SRD baseline so a creature constructed without content
    is a valid, empty Fate sheet (refresh 3, two two-box stress tracks, four open
    consequence slots).
    """

    model_config = {"extra": "forbid"}

    aspects: list[Aspect] = Field(default_factory=list)
    skills: dict[str, int] = Field(default_factory=dict)
    stunts: list[Stunt] = Field(default_factory=list)
    refresh: int = 3
    fate_points: int = 3
    stress: dict[str, StressTrack] = Field(default_factory=_default_stress)
    consequences: list[Consequence] = Field(default_factory=_default_consequences)

    def all_aspects(self) -> list[Aspect]:
        """Every aspect on the sheet: character aspects + FILLED-consequence
        aspects. Open consequence slots contribute nothing. (Situation aspects
        live on the encounter, not here — F1c.)"""
        return [*self.aspects, *(c.aspect for c in self.consequences if c.aspect is not None)]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/game/test_fate_sheet.py -n0 -q`
Expected: PASS (all 4 tests)

- [ ] **Step 5: Commit**

```bash
git add sidequest/game/fate_sheet.py tests/game/test_fate_sheet.py
git commit -m "feat(fate): FateSheet pure-data character facet (ADR-144 F1b)"
```

---

## Task 2: Attach the facet to `CreatureCore` + persistence round-trip

**Files:**
- Modify: `sidequest/game/creature_core.py`
- Test: `tests/game/test_fate_sheet.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/game/test_fate_sheet.py`:

```python
def test_creature_core_carries_optional_fate_sheet():
    from sidequest.game.creature_core import CreatureCore

    # Absent by default — a non-Fate creature is unchanged (None facet).
    core = CreatureCore(name="Mook", description="thug", personality="surly")
    assert core.fate_sheet is None

    # Present when a Fate creature is built.
    fate_core = CreatureCore(
        name="Sleuth",
        description="a tired detective",
        personality="dogged",
        fate_sheet=FateSheet(
            aspects=[Aspect(text="Last Honest Cop in Vice", kind="high_concept")],
            skills={"Investigate": 4, "Notice": 3},
        ),
    )
    assert fate_core.fate_sheet is not None
    assert fate_core.fate_sheet.skills["Investigate"] == 4


def test_fate_sheet_round_trips_through_snapshot_json():
    # The facet rides CreatureCore, which is serialized inside GameSnapshot via
    # model_dump_json()/model_validate (sidequest/game/pg/snapshot.py) — so a
    # JSON round-trip on CreatureCore proves the save path with NO migration.
    from sidequest.game.creature_core import CreatureCore

    core = CreatureCore(
        name="Sleuth",
        description="a tired detective",
        personality="dogged",
        fate_sheet=FateSheet(
            aspects=[Aspect(text="Owes the Mob a Favor", kind="trouble")],
            skills={"Notice": 3},
            fate_points=2,
        ),
    )
    core.fate_sheet.consequences[0].aspect = Aspect(
        text="Twisted Ankle", kind="consequence", free_invokes=1
    )
    core.fate_sheet.stress["physical"].boxes[1].checked = True

    restored = CreatureCore.model_validate_json(core.model_dump_json())
    assert restored.fate_sheet == core.fate_sheet
    assert restored.fate_sheet.consequences[0].aspect.text == "Twisted Ankle"
    assert restored.fate_sheet.stress["physical"].boxes[1].checked is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/game/test_fate_sheet.py::test_creature_core_carries_optional_fate_sheet -n0 -q`
Expected: FAIL — `pydantic_core.ValidationError: ... Extra inputs are not permitted [fate_sheet]` (the field does not exist yet; `extra="forbid"` rejects it).

- [ ] **Step 3: Add the facet field**

In `sidequest/game/creature_core.py`, add the import alongside the other `sidequest.game.*` facet imports near the top (after the `from sidequest.game.system_strain import SystemStrainPool` line):

```python
from sidequest.game.fate_sheet import FateSheet
```

Then add the optional field to `CreatureCore`, immediately after the `rig_pool` field (keep it grouped with the other optional facets — `system_strain`, `effort`, `spellcasting`, `rig_pool`):

```python
    # Fate Core facet (ADR-144 F1b). None for every non-Fate creature; populated
    # for a Fate-bound pack's creatures. Carried ALONGSIDE the d20 stats/HpPool
    # (mirrors system_strain/spellcasting/rig_pool — an optional facet), so it
    # round-trips through GameSnapshot.model_dump_json with no Alembic migration.
    # Rules + spans live on FateRulesetModule; this is inert data.
    fate_sheet: FateSheet | None = None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/game/test_fate_sheet.py -n0 -q`
Expected: PASS (all 6 tests)

- [ ] **Step 5: Guard against an import cycle / broad regression**

`fate_sheet.py` imports only pydantic, so `creature_core → fate_sheet` adds no cycle. Confirm the import resolves and the broad creature-core suite is green:

Run: `uv run python -c "from sidequest.game.creature_core import CreatureCore; print(CreatureCore(name='a', description='b', personality='c').fate_sheet)"`
Expected: prints `None`

Run: `uv run pytest tests/game/ -n0 -q -k "creature_core or character or snapshot"`
Expected: PASS — no regressions in the creature/snapshot suites.

- [ ] **Step 6: Commit**

```bash
git add sidequest/game/creature_core.py tests/game/test_fate_sheet.py
git commit -m "feat(fate): carry FateSheet as an optional CreatureCore facet (ADR-144 F1b)"
```

---

## Task 3: Economy + facet OTEL span helpers

**Files:**
- Modify: `sidequest/telemetry/spans/fate.py`
- Modify: `sidequest/telemetry/spans/__init__.py`
- Test: covered by Task 4/5's wiring tests (spans exercised through the real module).

- [ ] **Step 1: Add the span helpers + routes**

Append to `sidequest/telemetry/spans/fate.py` (F1a created this file with `fate_action_resolved_span`). Add the route-registry import near the top **if not already present** (F1a imported only `Span`), then append the helpers + their routes:

At the top of the file, after the existing `from sidequest.telemetry.spans.span import Span` line, add:

```python
from sidequest.telemetry.spans._core import SPAN_ROUTES, SpanRoute
```

At the **bottom** of the file, append:

```python
# --- F1b: fate-point economy + facet spans (GM panel = lie detector) ---------
# Registered as typed state_transition routes so the GM panel surfaces each
# economy delta and each stress/consequence mark in a typed tab (not just the
# always-on agent_span_close fan-out). Literal keys, no SPAN_* constants — the
# routing-completeness lint (tests/telemetry/test_routing_completeness.py) only
# inspects SPAN_* module constants, so these need no FLAT_ONLY entry.
SPAN_ROUTES["fate.fate_point.delta"] = SpanRoute(
    event_type="state_transition",
    component="fate",
    extract=lambda span: {
        "field": "fate_point_delta",
        "actor": (span.attributes or {}).get("actor", ""),
        "reason": (span.attributes or {}).get("reason", ""),
        "before": (span.attributes or {}).get("before", 0),
        "after": (span.attributes or {}).get("after", 0),
    },
)
SPAN_ROUTES["fate.aspect.invoked"] = SpanRoute(
    event_type="state_transition",
    component="fate",
    extract=lambda span: {
        "field": "aspect_invoked",
        "actor": (span.attributes or {}).get("actor", ""),
        "aspect": (span.attributes or {}).get("aspect", ""),
        "free": (span.attributes or {}).get("free", False),
        "mode": (span.attributes or {}).get("mode", ""),
    },
)
SPAN_ROUTES["fate.compel.offered"] = SpanRoute(
    event_type="state_transition",
    component="fate",
    extract=lambda span: {
        "field": "compel_offered",
        "actor": (span.attributes or {}).get("actor", ""),
        "aspect": (span.attributes or {}).get("aspect", ""),
    },
)
SPAN_ROUTES["fate.compel.accepted"] = SpanRoute(
    event_type="state_transition",
    component="fate",
    extract=lambda span: {
        "field": "compel_accepted",
        "actor": (span.attributes or {}).get("actor", ""),
        "aspect": (span.attributes or {}).get("aspect", ""),
    },
)
SPAN_ROUTES["fate.stress.applied"] = SpanRoute(
    event_type="state_transition",
    component="fate",
    extract=lambda span: {
        "field": "stress_applied",
        "actor": (span.attributes or {}).get("actor", ""),
        "track": (span.attributes or {}).get("track", ""),
        "box_value": (span.attributes or {}).get("box_value", 0),
    },
)
SPAN_ROUTES["fate.consequence.taken"] = SpanRoute(
    event_type="state_transition",
    component="fate",
    extract=lambda span: {
        "field": "consequence_taken",
        "actor": (span.attributes or {}).get("actor", ""),
        "level": (span.attributes or {}).get("level", ""),
        "aspect": (span.attributes or {}).get("aspect", ""),
    },
)


def fate_point_delta_span(
    *,
    actor: str,
    reason: str,
    before: int,
    after: int,
    _tracer: trace.Tracer | None = None,
    **attrs: Any,
) -> None:
    """Emit ``fate.fate_point.delta`` — one fate-point change with its reason."""
    attributes: dict[str, Any] = {
        "field": "fate_point_delta",
        "actor": actor,
        "reason": reason,
        "before": before,
        "after": after,
        **attrs,
    }
    with Span.open("fate.fate_point.delta", attributes, tracer_override=_tracer):
        pass


def fate_aspect_invoked_span(
    *,
    actor: str,
    aspect: str,
    free: bool,
    mode: str,
    fate_points_after: int,
    _tracer: trace.Tracer | None = None,
    **attrs: Any,
) -> None:
    """Emit ``fate.aspect.invoked`` — an aspect invoked for +2 or a reroll.
    ``free`` distinguishes a free invocation from a fate-point-paid one."""
    attributes: dict[str, Any] = {
        "field": "aspect_invoked",
        "actor": actor,
        "aspect": aspect,
        "free": free,
        "mode": mode,
        "fate_points_after": fate_points_after,
        **attrs,
    }
    with Span.open("fate.aspect.invoked", attributes, tracer_override=_tracer):
        pass


def fate_compel_offered_span(
    *,
    actor: str,
    aspect: str,
    _tracer: trace.Tracer | None = None,
    **attrs: Any,
) -> None:
    """Emit ``fate.compel.offered`` — the narrator proposed a compel (no economy
    change until accepted)."""
    attributes: dict[str, Any] = {
        "field": "compel_offered",
        "actor": actor,
        "aspect": aspect,
        **attrs,
    }
    with Span.open("fate.compel.offered", attributes, tracer_override=_tracer):
        pass


def fate_compel_accepted_span(
    *,
    actor: str,
    aspect: str,
    fate_points_after: int,
    _tracer: trace.Tracer | None = None,
    **attrs: Any,
) -> None:
    """Emit ``fate.compel.accepted`` — a compel accepted (earns one fate point)."""
    attributes: dict[str, Any] = {
        "field": "compel_accepted",
        "actor": actor,
        "aspect": aspect,
        "fate_points_after": fate_points_after,
        **attrs,
    }
    with Span.open("fate.compel.accepted", attributes, tracer_override=_tracer):
        pass


def fate_stress_applied_span(
    *,
    actor: str,
    track: str,
    box_value: int,
    _tracer: trace.Tracer | None = None,
    **attrs: Any,
) -> None:
    """Emit ``fate.stress.applied`` — one stress box checked to absorb a hit."""
    attributes: dict[str, Any] = {
        "field": "stress_applied",
        "actor": actor,
        "track": track,
        "box_value": box_value,
        **attrs,
    }
    with Span.open("fate.stress.applied", attributes, tracer_override=_tracer):
        pass


def fate_consequence_taken_span(
    *,
    actor: str,
    level: str,
    aspect: str,
    _tracer: trace.Tracer | None = None,
    **attrs: Any,
) -> None:
    """Emit ``fate.consequence.taken`` — a consequence slot filled (becomes an
    aspect). ``aspect`` is the consequence's free-text."""
    attributes: dict[str, Any] = {
        "field": "consequence_taken",
        "actor": actor,
        "level": level,
        "aspect": aspect,
        **attrs,
    }
    with Span.open("fate.consequence.taken", attributes, tracer_override=_tracer):
        pass
```

> Note: F1a's `fate.action_resolved` span has no route (it is currently flat in the watcher fan-out). Leaving it as-is is intentional for F1b scope; a route can be added when the F2 narrator surfaces it.

- [ ] **Step 2: Extend the package re-export**

In `sidequest/telemetry/spans/__init__.py`, F1a added a targeted line `from sidequest.telemetry.spans.fate import fate_action_resolved_span`. Replace it with the full set so the new helpers are importable as `from sidequest.telemetry.spans import fate_point_delta_span`:

```python
from sidequest.telemetry.spans.fate import (
    fate_action_resolved_span,
    fate_aspect_invoked_span,
    fate_compel_accepted_span,
    fate_compel_offered_span,
    fate_consequence_taken_span,
    fate_point_delta_span,
    fate_stress_applied_span,
)
```

- [ ] **Step 3: Verify imports + routing lint**

Run: `uv run python -c "from sidequest.telemetry.spans import fate_point_delta_span, fate_consequence_taken_span; print('ok')"`
Expected: prints `ok`

Run: `uv run pytest tests/telemetry/test_routing_completeness.py -n0 -q`
Expected: PASS — the new routes target the known `state_transition` event type; no `SPAN_*` constant was added, so nothing is unrouted.

- [ ] **Step 4: Commit**

```bash
git add sidequest/telemetry/spans/fate.py sidequest/telemetry/spans/__init__.py
git commit -m "feat(fate): economy + facet OTEL span helpers and routes (ADR-144 F1b)"
```

---

## Task 4: Fate-point economy methods on `FateRulesetModule`

**Files:**
- Modify: `sidequest/game/ruleset/fate.py`
- Test: `tests/game/ruleset/test_fate_economy.py`

- [ ] **Step 1: Write the failing test**

Create `tests/game/ruleset/test_fate_economy.py`:

```python
from __future__ import annotations

import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from sidequest.game.fate_sheet import Aspect, FateSheet
from sidequest.game.ruleset import get_ruleset_module
from sidequest.game.ruleset.fate import FateEconomyError


def _exporter():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return exporter, provider.get_tracer("test")


def _names(exporter):
    return [s.name for s in exporter.get_finished_spans()]


def test_spend_decrements_and_emits_delta_span():
    module = get_ruleset_module("fate")  # production resolution path
    sheet = FateSheet(fate_points=3)
    exporter, tracer = _exporter()

    after = module.spend_fate_point(sheet=sheet, reason="invoke", actor="Sleuth", _tracer=tracer)

    assert after == 2
    assert sheet.fate_points == 2
    assert "fate.fate_point.delta" in _names(exporter)
    span = next(s for s in exporter.get_finished_spans() if s.name == "fate.fate_point.delta")
    assert span.attributes["reason"] == "invoke"
    assert span.attributes["before"] == 3
    assert span.attributes["after"] == 2


def test_spend_with_zero_points_fails_loud():
    module = get_ruleset_module("fate")
    sheet = FateSheet(fate_points=0)
    with pytest.raises(FateEconomyError):
        module.spend_fate_point(sheet=sheet, reason="invoke", actor="Sleuth")


def test_earn_increments_and_emits_delta_span():
    module = get_ruleset_module("fate")
    sheet = FateSheet(fate_points=1)
    exporter, tracer = _exporter()

    after = module.earn_fate_point(sheet=sheet, reason="concede", actor="Sleuth", _tracer=tracer)

    assert after == 2
    assert "fate.fate_point.delta" in _names(exporter)


def test_refresh_raises_to_refresh_value_not_lowers():
    module = get_ruleset_module("fate")
    # Below refresh → rises to refresh.
    low = FateSheet(refresh=3, fate_points=1)
    assert module.refresh_fate_points(sheet=low, actor="Sleuth") == 3
    assert low.fate_points == 3
    # Above refresh (banked from compels) → keeps the higher total (SRD: refresh
    # never reduces fate points).
    high = FateSheet(refresh=3, fate_points=5)
    assert module.refresh_fate_points(sheet=high, actor="Sleuth") == 5


def test_invoke_uses_free_invocation_before_spending():
    module = get_ruleset_module("fate")
    sheet = FateSheet(
        fate_points=2,
        aspects=[Aspect(text="High Ground", kind="situation", free_invokes=1)],
    )
    exporter, tracer = _exporter()

    bonus = module.invoke_aspect(
        sheet=sheet, aspect_text="High Ground", mode="bonus", actor="Sleuth", _tracer=tracer
    )

    assert bonus == 2  # +2 for a bonus invoke
    assert sheet.fate_points == 2  # free invoke spent no fate point
    assert sheet.aspects[0].free_invokes == 0  # the free invoke was consumed
    span = next(s for s in exporter.get_finished_spans() if s.name == "fate.aspect.invoked")
    assert span.attributes["free"] is True


def test_invoke_without_free_invocation_spends_a_fate_point():
    module = get_ruleset_module("fate")
    sheet = FateSheet(
        fate_points=2,
        aspects=[Aspect(text="Dogged", kind="character", free_invokes=0)],
    )
    bonus = module.invoke_aspect(sheet=sheet, aspect_text="Dogged", mode="bonus", actor="Sleuth")
    assert bonus == 2
    assert sheet.fate_points == 1  # paid one fate point


def test_invoke_unknown_aspect_fails_loud():
    module = get_ruleset_module("fate")
    sheet = FateSheet(fate_points=2)
    with pytest.raises(FateEconomyError):
        module.invoke_aspect(sheet=sheet, aspect_text="Nonexistent", mode="bonus", actor="x")


def test_accept_compel_earns_a_point_and_emits_both_spans():
    module = get_ruleset_module("fate")
    sheet = FateSheet(fate_points=1)
    exporter, tracer = _exporter()

    after = module.accept_compel(
        sheet=sheet, aspect_text="Owes the Mob a Favor", actor="Sleuth", _tracer=tracer
    )

    assert after == 2
    names = _names(exporter)
    assert "fate.compel.accepted" in names
    assert "fate.fate_point.delta" in names  # the earn rides the delta span too
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/game/ruleset/test_fate_economy.py -n0 -q`
Expected: FAIL — `ImportError: cannot import name 'FateEconomyError' from 'sidequest.game.ruleset.fate'`

- [ ] **Step 3: Add the economy methods**

In `sidequest/game/ruleset/fate.py`:

Extend the F1a span import to pull in the new helpers (F1a imported `fate_action_resolved_span`):

```python
from sidequest.telemetry.spans import (
    fate_action_resolved_span,
    fate_aspect_invoked_span,
    fate_compel_accepted_span,
    fate_compel_offered_span,
    fate_consequence_taken_span,
    fate_point_delta_span,
    fate_stress_applied_span,
)
```

Add a `TYPE_CHECKING` import for `FateSheet` near the top (the module already imports from `fate_resolution`; add the sheet types):

```python
from sidequest.game.fate_sheet import Aspect, FateSheet
```

Above the class, add the fail-loud error:

```python
class FateEconomyError(ValueError):
    """A Fate economy operation violated the rules (no fate point to spend, an
    already-checked stress box, a filled consequence slot, an unknown aspect).
    Fail loud — No Silent Fallbacks (ADR-144 / SOUL.md)."""
```

Add these methods to `FateRulesetModule` (place them after `resolve_action`, before the fail-loud d20 surface block):

```python
    # --- Fate-point economy (rules + spans; FateSheet is inert data) ----------

    def spend_fate_point(
        self, *, sheet: FateSheet, reason: str, actor: str = "", _tracer=None
    ) -> int:
        """Debit one fate point. Fails loud at zero (No Silent Fallbacks)."""
        if sheet.fate_points <= 0:
            raise FateEconomyError(
                f"{actor or 'actor'} has no fate point to spend (reason={reason!r})"
            )
        before = sheet.fate_points
        sheet.fate_points -= 1
        fate_point_delta_span(
            actor=actor, reason=reason, before=before, after=sheet.fate_points, _tracer=_tracer
        )
        return sheet.fate_points

    def earn_fate_point(
        self, *, sheet: FateSheet, reason: str, actor: str = "", _tracer=None
    ) -> int:
        """Credit one fate point (compel accepted, concession)."""
        before = sheet.fate_points
        sheet.fate_points += 1
        fate_point_delta_span(
            actor=actor, reason=reason, before=before, after=sheet.fate_points, _tracer=_tracer
        )
        return sheet.fate_points

    def refresh_fate_points(self, *, sheet: FateSheet, actor: str = "", _tracer=None) -> int:
        """Session refresh: raise fate points UP to refresh; never reduce a
        higher banked total (SRD)."""
        before = sheet.fate_points
        sheet.fate_points = max(sheet.fate_points, sheet.refresh)
        fate_point_delta_span(
            actor=actor, reason="refresh", before=before, after=sheet.fate_points, _tracer=_tracer
        )
        return sheet.fate_points

    def invoke_aspect(
        self,
        *,
        sheet: FateSheet,
        aspect_text: str,
        mode: str = "bonus",
        actor: str = "",
        _tracer=None,
    ) -> int:
        """Invoke an aspect for ``mode`` ('bonus' → +2, 'reroll' → reroll). Uses a
        free invocation if the aspect has one; otherwise spends a fate point.
        Returns the numeric bonus (2 for 'bonus', 0 for 'reroll' — the reroll
        itself is the caller's/F1c's job). Fails loud on an unknown aspect."""
        aspect = next((a for a in sheet.all_aspects() if a.text == aspect_text), None)
        if aspect is None:
            raise FateEconomyError(
                f"{actor or 'actor'} cannot invoke unknown aspect {aspect_text!r}"
            )
        free = aspect.free_invokes > 0
        if free:
            aspect.free_invokes -= 1
        else:
            self.spend_fate_point(sheet=sheet, reason="invoke", actor=actor, _tracer=_tracer)
        fate_aspect_invoked_span(
            actor=actor,
            aspect=aspect_text,
            free=free,
            mode=mode,
            fate_points_after=sheet.fate_points,
            _tracer=_tracer,
        )
        return 2 if mode == "bonus" else 0

    def offer_compel(self, *, aspect_text: str, actor: str = "", _tracer=None) -> None:
        """Surface that the narrator proposed a compel (no economy change). The
        OTEL span lets the GM panel see the offer even when the player declines."""
        fate_compel_offered_span(actor=actor, aspect=aspect_text, _tracer=_tracer)

    def accept_compel(
        self, *, sheet: FateSheet, aspect_text: str, actor: str = "", _tracer=None
    ) -> int:
        """Accept a compel: earn one fate point + emit the compel span."""
        after = self.earn_fate_point(sheet=sheet, reason="compel", actor=actor, _tracer=_tracer)
        fate_compel_accepted_span(
            actor=actor, aspect=aspect_text, fate_points_after=after, _tracer=_tracer
        )
        return after
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/game/ruleset/test_fate_economy.py -n0 -q`
Expected: PASS (all 8 economy tests)

- [ ] **Step 5: Commit**

```bash
git add sidequest/game/ruleset/fate.py tests/game/ruleset/test_fate_economy.py
git commit -m "feat(fate): fate-point economy methods + OTEL on FateRulesetModule (ADR-144 F1b)"
```

---

## Task 5: Stress + consequence atomic mutators

**Files:**
- Modify: `sidequest/game/ruleset/fate.py`
- Test: `tests/game/ruleset/test_fate_economy.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/game/ruleset/test_fate_economy.py`:

```python
def test_mark_stress_checks_the_named_box_and_emits_span():
    module = get_ruleset_module("fate")
    sheet = FateSheet()
    exporter, tracer = _exporter()

    absorbed = module.mark_stress(
        sheet=sheet, track="physical", box_value=2, actor="Sleuth", _tracer=tracer
    )

    assert absorbed == 2  # a value-2 box absorbs 2 shifts
    assert sheet.stress["physical"].boxes[1].checked is True
    assert sheet.stress["physical"].boxes[0].checked is False
    assert "fate.stress.applied" in _names(exporter)


def test_mark_stress_already_checked_fails_loud():
    module = get_ruleset_module("fate")
    sheet = FateSheet()
    module.mark_stress(sheet=sheet, track="physical", box_value=1, actor="Sleuth")
    with pytest.raises(FateEconomyError):
        module.mark_stress(sheet=sheet, track="physical", box_value=1, actor="Sleuth")


def test_mark_stress_unknown_track_or_box_fails_loud():
    module = get_ruleset_module("fate")
    sheet = FateSheet()
    with pytest.raises(FateEconomyError):
        module.mark_stress(sheet=sheet, track="spiritual", box_value=1, actor="x")
    with pytest.raises(FateEconomyError):
        module.mark_stress(sheet=sheet, track="physical", box_value=9, actor="x")


def test_take_consequence_fills_slot_becomes_aspect_with_free_invoke():
    module = get_ruleset_module("fate")
    sheet = FateSheet()
    exporter, tracer = _exporter()

    absorbed = module.take_consequence(
        sheet=sheet,
        level="moderate",
        aspect_text="Dislocated Shoulder",
        actor="Sleuth",
        _tracer=tracer,
    )

    assert absorbed == 4  # moderate absorbs 4 shifts
    moderate = next(c for c in sheet.consequences if c.level == "moderate")
    assert moderate.aspect is not None
    assert moderate.aspect.text == "Dislocated Shoulder"
    assert moderate.aspect.kind == "consequence"
    assert moderate.aspect.free_invokes == 1  # SRD: free invoke for the attacker
    # The filled consequence now surfaces in all_aspects().
    assert "Dislocated Shoulder" in [a.text for a in sheet.all_aspects()]
    assert "fate.consequence.taken" in _names(exporter)


def test_take_consequence_already_filled_fails_loud():
    module = get_ruleset_module("fate")
    sheet = FateSheet()
    module.take_consequence(sheet=sheet, level="mild", aspect_text="Bruised", actor="x")
    with pytest.raises(FateEconomyError):
        module.take_consequence(sheet=sheet, level="mild", aspect_text="Again", actor="x")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/game/ruleset/test_fate_economy.py -n0 -q -k "stress or consequence"`
Expected: FAIL — `AttributeError: 'FateRulesetModule' object has no attribute 'mark_stress'`

- [ ] **Step 3: Add the mutators**

Add these methods to `FateRulesetModule` (after the economy methods, still before the d20 surface block):

```python
    # --- Stress + consequence atomic mutators (F1c orchestrates absorption) ---

    def mark_stress(
        self, *, sheet: FateSheet, track: str, box_value: int, actor: str = "", _tracer=None
    ) -> int:
        """Check the unused stress box of value ``box_value`` on ``track`` and
        return the shifts it absorbs (== box_value). Fails loud on an unknown
        track, a missing box value, or an already-checked box. Choosing WHICH box
        absorbs a hit is F1c's orchestration; this is the atomic mark."""
        stress_track = sheet.stress.get(track)
        if stress_track is None:
            raise FateEconomyError(
                f"{actor or 'actor'} has no '{track}' stress track "
                f"(have: {sorted(sheet.stress)})"
            )
        box = next(
            (b for b in stress_track.boxes if b.value == box_value and not b.checked), None
        )
        if box is None:
            raise FateEconomyError(
                f"{actor or 'actor'} has no unchecked {track} stress box of value "
                f"{box_value} to mark"
            )
        box.checked = True
        fate_stress_applied_span(actor=actor, track=track, box_value=box_value, _tracer=_tracer)
        return box_value

    def take_consequence(
        self, *, sheet: FateSheet, level: str, aspect_text: str, actor: str = "", _tracer=None
    ) -> int:
        """Fill the ``level`` consequence slot with an aspect and return the
        shifts it absorbs (the slot value). The filled slot BECOMES an aspect with
        one free invoke for the attacker (SRD). Fails loud if the slot is already
        filled or the level is unknown."""
        slot = next((c for c in sheet.consequences if c.level == level), None)
        if slot is None:
            raise FateEconomyError(
                f"{actor or 'actor'} has no '{level}' consequence slot "
                f"(have: {[c.level for c in sheet.consequences]})"
            )
        if slot.aspect is not None:
            raise FateEconomyError(
                f"{actor or 'actor'} {level} consequence is already filled "
                f"({slot.aspect.text!r})"
            )
        slot.aspect = Aspect(text=aspect_text, kind="consequence", free_invokes=1)
        fate_consequence_taken_span(actor=actor, level=level, aspect=aspect_text, _tracer=_tracer)
        return slot.value
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/game/ruleset/test_fate_economy.py -n0 -q`
Expected: PASS (all 13 tests — 8 economy + 5 stress/consequence)

- [ ] **Step 5: Commit**

```bash
git add sidequest/game/ruleset/fate.py tests/game/ruleset/test_fate_economy.py
git commit -m "feat(fate): stress + consequence atomic mutators + OTEL (ADR-144 F1b)"
```

---

## Task 6: Gate — lint, format, types, suites

**Files:** none (verification only)

- [ ] **Step 1: Lint the changed files (scoped — NEVER the repo)**

Run: `uv run ruff check sidequest/game/fate_sheet.py sidequest/game/creature_core.py sidequest/game/ruleset/fate.py sidequest/telemetry/spans/fate.py sidequest/telemetry/spans/__init__.py tests/game/test_fate_sheet.py tests/game/ruleset/test_fate_economy.py`
Expected: `All checks passed!`

- [ ] **Step 2: Format the changed files (scoped)**

Run: `uv run ruff format sidequest/game/fate_sheet.py sidequest/game/creature_core.py sidequest/game/ruleset/fate.py sidequest/telemetry/spans/fate.py sidequest/telemetry/spans/__init__.py tests/game/test_fate_sheet.py tests/game/ruleset/test_fate_economy.py`
Expected: files unchanged or reformatted in place (commit any reformat).

- [ ] **Step 3: Type check**

Run: `uv run pyright sidequest/game/fate_sheet.py sidequest/game/creature_core.py sidequest/game/ruleset/fate.py sidequest/telemetry/spans/fate.py`
Expected: `0 errors`

- [ ] **Step 4: Run the ruleset + fate-facet + routing suites**

Run: `uv run pytest tests/game/ruleset/ tests/game/test_fate_sheet.py tests/telemetry/test_routing_completeness.py -n0 -q`
Expected: PASS — F1a's fate tests still green, the new facet/economy tests pass, routing lint green, no native/WN ruleset regressions.

- [ ] **Step 5: Commit any fixups**

```bash
git add -p
git commit -m "chore(fate): lint/format/type fixups (ADR-144 F1b)"
```

---

## Self-review (done against the spec)

- **Spec §4.3 coverage:** `FateSheet` with aspects / skills / stunts / refresh / fate_points / stress / consequences — Task 1; carried alongside `CreatureCore` (not in stats/HpPool) — Task 2; fate-point economy (refresh/spend/earn/invoke/compel) — Task 4; consequence slot → aspect — Task 5. ✓
- **Spec §6 OTEL:** `fate.fate_point.delta`, `fate.aspect.invoked`, `fate.compel.offered`/`accepted`, `fate.stress.applied`, `fate.consequence.taken` — Task 3 helpers + Task 4/5 emit + routed for the GM panel. (`fate.taken_out` / `fate.conceded` are conflict spans — F1c.) ✓
- **Wiring (server CLAUDE.md):** economy + mutators are exercised through the **real registered** module (`get_ruleset_module("fate")`) with OTEL-span assertions, not source greps — Tasks 4/5. The facet is exercised through the **real** JSON serializer round-trip — Task 2. ✓
- **No Stubbing / No Silent Fallbacks:** the model is inert data; every rules op fails loud (`FateEconomyError`) on an impossible economy/stress/consequence state. ✓
- **No shoehorning (handoff):** the facet is `fate_sheet: FateSheet | None` next to the existing optional facets — d20 `stats`/`HpPool` untouched. ✓
- **No migration:** the facet rides `CreatureCore` JSON inside `GameSnapshot.model_dump_json()` — additive, forward-only (consistent with ADR-144's forward-only saves). ✓
- **Routing-lint safety:** new spans use literal keys + `SPAN_ROUTES` (no `SPAN_*` constants), so `test_routing_completeness` stays green — Task 3. ✓
- **Placeholder scan:** none — every code/command step is concrete.
- **Type consistency:** `FateSheet`, `Aspect`, `Stunt`, `StressBox`, `StressTrack`, `Consequence`, `CONSEQUENCE_VALUES`, `FateEconomyError`, and the six span helpers are named identically across all tasks. ✓
- **Out of F1b scope (correct):** the conflict exchange, situation aspects on the encounter, absorption orchestration, dispatch routing, 4dF UI, content-driven chargen seeding — F1c / F1d / F2 / F3 / F4.
