# F1c — `fate_conflict.py` Exchange Engine — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up `fate_conflict.py` — the Fate Core exchange engine that mirrors `wn_round.py` one tier over: sides + zones + Notice/Empathy turn order, a sealed submit-and-wait barrier, the proactive Fate actions (overcome / create-advantage / attack) + reactive defend, shifts → stress/consequence absorption, taken-out vs concede — every decision emitting an OTEL lie-detector span.

**Architecture:** A Fate confrontation reuses the **same MP substrate** `wn_round` uses — the ADR-036 sealed submit-and-wait barrier expressed as a per-encounter sealed-commit ledger. F1c adds a `FateSealedCommit` ledger (`encounter.fate_commits`) alongside the WN one (`encounter.wn_commits`), a `seal_fate_commit` / barrier-closed pair that mirror `seal_wn_commit` / `wn_barrier_closed`, and `run_fate_exchange` that walks committed actors in Notice/Empathy order and resolves each action through the F1a resolution primitive + the F1b stress/consequence mutators. The engine resolves *committed* actions (PC actions; opponent actions are committed by the F2 narrator — F1c does not author opponent AI). Native/WN paths are untouched.

**Tech Stack:** Python 3.14, pydantic v2, pytest (`-n0`), OpenTelemetry SDK, `uv`. **All paths below are under `sidequest-server/`.** Branch off `develop` (gitflow); feature branch `feat/f1c-fate-conflict`.

**Decision of record:** ADR-144. **Design:** `docs/superpowers/specs/2026-06-14-fate-core-binding-replaces-native-design.md` §4.2 + §6 + §7. **Depends on:** F1a (`FateRulesetModule.resolve_action`, `Opposition`, `spans/fate.py`) and **F1b** (`FateSheet`, `mark_stress`, `take_consequence`, `earn_fate_point`, the economy spans) merged.

---

## F1 slice map (context — this plan is F1c only)

| Slice | Scope | Status |
|-------|-------|--------|
| F1a | Resolution primitive + module registration + OTEL | merged (prereq) |
| F1b | Fate character facet + fate-point economy | merged (prereq) |
| **F1c** | `fate_conflict.py` exchange engine (sides, zones, turn order, four actions, stress/consequences, taken-out/concede) | **this plan** |
| F1d | Dispatch routing + end-to-end wiring | next plan |

F1c is independently testable through the **real registered** `FateRulesetModule` driving a constructed encounter + snapshot — no genre pack required (the fate spans are fixed `fate.*`, not slug-parametrized, so the engine needs no `GenrePack`). F1d wires the dispatch entry that calls `run_fate_exchange` in production.

---

## The exchange model (read before coding — this is the contract)

`wn_round.py` is the template: a barrier holds until every seated PC commits, then a single walk resolves the round in a persisted order, clearing the ledger. F1c mirrors it with Fate semantics:

- **The actions.** Three are *proactive* and committed: `overcome`, `create_advantage`, `attack`. **Defend** is *reactive* — the engine rolls it for the target when an attack resolves (SRD: defense is opposed). These are the Fate Core actions; there is **no** separate `full_defense` action. "Full/total defense" (forgo your action for +2 to defenses) is a d20/Pathfinder import, **not** in the Fate SRD — removed per Keith's standing "remove all native ruleset" ruling (SOUL: *Bind the Ruleset, Don't Balance It*).
- **Opposition (design §4.2 / F1a `Opposition`).** *Active*: the action names a `target`; the engine rolls the target's defense and `shifts = attacker_ladder_total − defender_ladder_total`. *Passive*: the action names a `difficulty`; `shifts = attacker_ladder_total − difficulty`.
- **The attacker's roll is sealed at commit time** (4dF + skill + any invoke bonus → `ladder_total`), exactly as WN seals the to-hit. The defender's reactive roll happens at the attacker's resolution slot.
- **Attack → absorb.** `shifts ≥ 1` hits for that many shifts; the target absorbs via **one** stress box (SRD: one per hit) plus any consequence slots. Unabsorbed ⇒ **taken out**. `shifts == 0` (tie) grants the defender a **boost** (a situation aspect with one free invoke). `shifts < 0` is a clean miss.
- **Create-advantage** places a **situation aspect on the encounter** with one free invoke (two on Succeed-with-Style, `shifts ≥ 3`); a tie places a boost.
- **Concede** is player-initiated, *pre-roll*, and is NOT one of the committed actions: it withdraws the actor on their terms and earns 1 fate point + 1 per consequence taken this conflict (SRD).
- **Zones** are represented (the encounter carries `zones`; an actor's zone lives in `EncounterActor.per_actor_state["zone"]`) and recorded on spans. Movement-as-overcome and zone-gated range are narrator/content concerns (F2/F4) — F1c does **not** invent a range/movement balancing subsystem (SOUL: *Bind the Ruleset, Don't Balance It*).
- **Opponent actions** are committed by the F2 narrator in production (and seeded directly in tests). The barrier waits on **PCs only** (mirrors WN: engine-driven allies/opponents don't seal). F1c resolves whatever is committed.

---

## File structure (F1c)

- **Modify** `sidequest/game/encounter.py` — add `FateSealedCommit`; add `fate_commits`, `situation_aspects`, `zones` fields to `StructuredEncounter`.
- **Modify** `sidequest/telemetry/spans/fate.py` — add six exchange span helpers + their `SPAN_ROUTES`.
- **Modify** `sidequest/telemetry/spans/__init__.py` — extend the fate re-export.
- **Create** `sidequest/server/dispatch/fate_conflict.py` — `FateConflictError`, `seal_fate_commit`, `fate_waiting_actors`, `fate_barrier_closed`, `fate_turn_order`, `absorb_shifts`, `run_fate_exchange`, `concede_in_conflict`, `FateExchangeResult`.
- **Create** `tests/game/test_fate_commit_model.py` — `FateSealedCommit` + encounter-field tests.
- **Create** `tests/server/dispatch/test_fate_conflict.py` — barrier, turn order, absorption, full exchange, taken-out, concede + OTEL wiring.

---

## Task 1: `FateSealedCommit` + encounter fields

**Files:**
- Modify: `sidequest/game/encounter.py`
- Test: `tests/game/test_fate_commit_model.py`

- [ ] **Step 1: Write the failing test**

Create `tests/game/test_fate_commit_model.py`:

```python
from __future__ import annotations

import pytest
from pydantic import ValidationError

from sidequest.game.encounter import EncounterMetric, FateSealedCommit, StructuredEncounter
from sidequest.game.fate_sheet import Aspect


def _enc() -> StructuredEncounter:
    return StructuredEncounter(
        encounter_type="duel",
        category="combat",
        player_metric=EncounterMetric(name="p", threshold=10),
        opponent_metric=EncounterMetric(name="o", threshold=10),
    )


def test_fate_sealed_commit_shape():
    c = FateSealedCommit(
        actor="Sleuth",
        action="attack",
        skill="Fight",
        target="Thug",
        ladder_total=6,
        dice=(1, 1, 0, -1),
    )
    assert c.action == "attack"
    assert c.difficulty == 0
    assert c.aspect_text == ""


def test_fate_sealed_commit_rejects_unknown_action():
    with pytest.raises(ValidationError):
        FateSealedCommit(actor="x", action="parry", skill="Fight")  # not one of the four


def test_encounter_carries_empty_fate_ledgers_by_default():
    enc = _enc()
    assert enc.fate_commits == []
    assert enc.situation_aspects == []
    assert enc.zones == []


def test_encounter_with_fate_state_round_trips_json():
    enc = _enc()
    enc.zones = ["The Bar", "The Alley"]
    enc.fate_commits.append(
        FateSealedCommit(
            actor="Sleuth", action="attack", skill="Fight", target="Thug",
            ladder_total=5, dice=(1, 1, 0, -1),
        )
    )
    enc.situation_aspects.append(Aspect(text="Spilled Whiskey", kind="situation", free_invokes=1))

    restored = StructuredEncounter.model_validate_json(enc.model_dump_json())
    assert restored.zones == ["The Bar", "The Alley"]
    assert restored.fate_commits[0].target == "Thug"
    # the 4-tuple coerces back from the JSON list (non-default values prove it)
    assert restored.fate_commits[0].dice == (1, 1, 0, -1)
    assert restored.situation_aspects[0].text == "Spilled Whiskey"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/game/test_fate_commit_model.py -n0 -q`
Expected: FAIL — `ImportError: cannot import name 'FateSealedCommit' from 'sidequest.game.encounter'`

- [ ] **Step 3: Add the model + fields**

In `sidequest/game/encounter.py`:

Add the import near the other `sidequest.game.*` imports at the top:

```python
from sidequest.game.fate_sheet import Aspect
```

Add the `FateSealedCommit` model immediately after the `WnSealedCommit` class:

```python
class FateSealedCommit(BaseModel):
    """One sealed Fate action in an exchange (ADR-144 F1c).

    Mirrors :class:`WnSealedCommit` one tier over. A proactive Fate action seals
    here until every seated PC has committed; ``run_fate_exchange`` consumes and
    clears the ledger. The attacker's 4dF roll is resolved AT COMMIT TIME (like
    the WN to-hit): ``ladder_total`` = 4dF + skill + invoke bonus, ``dice`` the
    raw faces. The reactive defense roll happens at the actor's slot.

    ``action`` is one of the three proactive Fate actions; ``defend`` is
    reactive (the engine rolls it for an attack's target) and is never a
    committed value. There is no ``full_defense`` action — not in the Fate SRD.
    Opposition is ACTIVE when ``target`` is set (the engine rolls that actor's
    defense) or PASSIVE when ``difficulty`` is set (a set number on the ladder).
    ``aspect_text`` carries the situation aspect a create-advantage means to
    place.
    """

    model_config = {"extra": "forbid"}

    actor: str
    action: Literal["overcome", "create_advantage", "attack"]
    skill: str
    target: str | None = None
    difficulty: int = 0
    ladder_total: int = 0
    dice: tuple[int, int, int, int] = (0, 0, 0, 0)
    aspect_text: str = ""
```

Add the three fields to `StructuredEncounter`, immediately after the `wn_commits` field (keep the Fate ledger grouped with the WN one):

```python
    fate_commits: list[FateSealedCommit] = Field(default_factory=list)
    """ADR-144 F1c: the Fate sealed-commit ledger for the CURRENT exchange.
    Proactive actions seal here until every live seated PC has committed; the
    exchange walk consumes and clears it. Always empty for native/WN encounters
    and between Fate exchanges (sibling to ``wn_commits``)."""
    situation_aspects: list[Aspect] = Field(default_factory=list)
    """ADR-144 F1c: scene-scoped Fate aspects placed by create-advantage (and
    boosts from ties). Distinct from character/consequence aspects, which live on
    the actor's FateSheet. Cleared on scene end (F2/F3 lifecycle)."""
    zones: list[str] = Field(default_factory=list)
    """ADR-144 F1c: named Fate zones for this scene (reuses the encounter as the
    spatial notion — design §4.2 / open-Q3). An actor's current zone lives in
    ``EncounterActor.per_actor_state['zone']``. Empty for non-Fate encounters."""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/game/test_fate_commit_model.py -n0 -q`
Expected: PASS (all 4 tests)

- [ ] **Step 5: Guard against regressions in the encounter suite**

Run: `uv run pytest tests/game/ -n0 -q -k "encounter"`
Expected: PASS — the legacy-metric rejector and existing encounter tests are unaffected (the new fields are additive with defaults).

- [ ] **Step 6: Commit**

```bash
git add sidequest/game/encounter.py tests/game/test_fate_commit_model.py
git commit -m "feat(fate): FateSealedCommit ledger + situation aspects + zones on encounter (ADR-144 F1c)"
```

---

## Task 2: Exchange OTEL span helpers

**Files:**
- Modify: `sidequest/telemetry/spans/fate.py`
- Modify: `sidequest/telemetry/spans/__init__.py`
- Test: covered by Task 5's wiring assertions (spans exercised through `run_fate_exchange`).

- [ ] **Step 1: Add the span helpers + routes**

Append to `sidequest/telemetry/spans/fate.py` (the route-import added in F1b is already present):

```python
# --- F1c: conflict exchange spans (GM panel = lie detector) ------------------
SPAN_ROUTES["fate.exchange.committed"] = SpanRoute(
    event_type="state_transition",
    component="fate",
    extract=lambda span: {
        "field": "exchange_committed",
        "committed_actors": (span.attributes or {}).get("committed_actors", ""),
    },
)
SPAN_ROUTES["fate.exchange.order"] = SpanRoute(
    event_type="state_transition",
    component="fate",
    extract=lambda span: {
        "field": "exchange_order",
        "order": (span.attributes or {}).get("order", ""),
        "skill": (span.attributes or {}).get("skill", ""),
    },
)
SPAN_ROUTES["fate.exchange.resolved"] = SpanRoute(
    event_type="state_transition",
    component="fate",
    extract=lambda span: {
        "field": "exchange_resolved",
        "resolution_order": (span.attributes or {}).get("resolution_order", ""),
        "resolved": (span.attributes or {}).get("resolved", False),
    },
)
SPAN_ROUTES["fate.aspect.created"] = SpanRoute(
    event_type="state_transition",
    component="fate",
    extract=lambda span: {
        "field": "aspect_created",
        "actor": (span.attributes or {}).get("actor", ""),
        "aspect": (span.attributes or {}).get("aspect", ""),
        "free_invokes": (span.attributes or {}).get("free_invokes", 0),
    },
)
SPAN_ROUTES["fate.taken_out"] = SpanRoute(
    event_type="state_transition",
    component="fate",
    extract=lambda span: {
        "field": "taken_out",
        "actor": (span.attributes or {}).get("actor", ""),
        "by": (span.attributes or {}).get("by", ""),
        "shifts": (span.attributes or {}).get("shifts", 0),
    },
)
SPAN_ROUTES["fate.conceded"] = SpanRoute(
    event_type="state_transition",
    component="fate",
    extract=lambda span: {
        "field": "conceded",
        "actor": (span.attributes or {}).get("actor", ""),
        "fate_points_earned": (span.attributes or {}).get("fate_points_earned", 0),
    },
)


def fate_exchange_committed_span(
    *, committed_actors: str, _tracer: trace.Tracer | None = None, **attrs: Any
) -> None:
    """Emit ``fate.exchange.committed`` — the sealed-commit barrier closed."""
    attributes: dict[str, Any] = {
        "field": "exchange_committed",
        "committed_actors": committed_actors,
        **attrs,
    }
    with Span.open("fate.exchange.committed", attributes, tracer_override=_tracer):
        pass


def fate_exchange_order_span(
    *, order: str, skill: str, _tracer: trace.Tracer | None = None, **attrs: Any
) -> None:
    """Emit ``fate.exchange.order`` — Notice/Empathy turn order for the exchange."""
    attributes: dict[str, Any] = {
        "field": "exchange_order",
        "order": order,
        "skill": skill,
        **attrs,
    }
    with Span.open("fate.exchange.order", attributes, tracer_override=_tracer):
        pass


def fate_exchange_resolved_span(
    *, resolution_order: str, resolved: bool, _tracer: trace.Tracer | None = None, **attrs: Any
) -> None:
    """Emit ``fate.exchange.resolved`` — the exchange walk finished. ``resolved``
    is whether the confrontation itself ended this exchange."""
    attributes: dict[str, Any] = {
        "field": "exchange_resolved",
        "resolution_order": resolution_order,
        "resolved": resolved,
        **attrs,
    }
    with Span.open("fate.exchange.resolved", attributes, tracer_override=_tracer):
        pass


def fate_aspect_created_span(
    *, actor: str, aspect: str, free_invokes: int, _tracer: trace.Tracer | None = None, **attrs: Any
) -> None:
    """Emit ``fate.aspect.created`` — create-advantage placed a situation aspect
    (or a boost) with ``free_invokes`` free invocations."""
    attributes: dict[str, Any] = {
        "field": "aspect_created",
        "actor": actor,
        "aspect": aspect,
        "free_invokes": free_invokes,
        **attrs,
    }
    with Span.open("fate.aspect.created", attributes, tracer_override=_tracer):
        pass


def fate_taken_out_span(
    *, actor: str, by: str, shifts: int, _tracer: trace.Tracer | None = None, **attrs: Any
) -> None:
    """Emit ``fate.taken_out`` — an actor's stress+consequences could not absorb a
    hit and they are out of the conflict."""
    attributes: dict[str, Any] = {
        "field": "taken_out",
        "actor": actor,
        "by": by,
        "shifts": shifts,
        **attrs,
    }
    with Span.open("fate.taken_out", attributes, tracer_override=_tracer):
        pass


def fate_conceded_span(
    *, actor: str, fate_points_earned: int, _tracer: trace.Tracer | None = None, **attrs: Any
) -> None:
    """Emit ``fate.conceded`` — a player conceded (pre-roll), leaving on their
    terms and earning fate points."""
    attributes: dict[str, Any] = {
        "field": "conceded",
        "actor": actor,
        "fate_points_earned": fate_points_earned,
        **attrs,
    }
    with Span.open("fate.conceded", attributes, tracer_override=_tracer):
        pass
```

- [ ] **Step 2: Extend the package re-export**

In `sidequest/telemetry/spans/__init__.py`, extend the fate re-export block (added/updated in F1b) to include the six new helpers:

```python
from sidequest.telemetry.spans.fate import (
    fate_action_resolved_span,
    fate_aspect_created_span,
    fate_aspect_invoked_span,
    fate_compel_accepted_span,
    fate_compel_offered_span,
    fate_consequence_taken_span,
    fate_exchange_committed_span,
    fate_exchange_order_span,
    fate_exchange_resolved_span,
    fate_point_delta_span,
    fate_stress_applied_span,
    fate_taken_out_span,
    fate_conceded_span,
)
```

- [ ] **Step 3: Verify imports + routing lint**

Run: `uv run python -c "from sidequest.telemetry.spans import fate_exchange_resolved_span, fate_taken_out_span; print('ok')"`
Expected: prints `ok`

Run: `uv run pytest tests/telemetry/test_routing_completeness.py -n0 -q`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add sidequest/telemetry/spans/fate.py sidequest/telemetry/spans/__init__.py
git commit -m "feat(fate): conflict exchange OTEL span helpers and routes (ADR-144 F1c)"
```

---

## Task 3: Barrier + turn-order helpers

**Files:**
- Create: `sidequest/server/dispatch/fate_conflict.py`
- Test: `tests/server/dispatch/test_fate_conflict.py`

- [ ] **Step 1: Write the failing test**

Create `tests/server/dispatch/test_fate_conflict.py`:

```python
from __future__ import annotations

import pytest

from sidequest.game.character import Character
from sidequest.game.creature_core import CreatureCore
from sidequest.game.encounter import EncounterActor, EncounterMetric, StructuredEncounter
from sidequest.game.fate_sheet import FateSheet
from sidequest.game.session import GameSnapshot
from sidequest.server.dispatch.fate_conflict import (
    FateConflictError,
    fate_barrier_closed,
    fate_turn_order,
    fate_waiting_actors,
    seal_fate_commit,
)


class _FixedRng:
    """A deterministic stand-in for random.Random: every 4dF face is ``value``."""

    def __init__(self, value: int = 0) -> None:
        self._value = value

    def choice(self, seq):
        return self._value


def _pc(name: str, skills: dict[str, int]) -> Character:
    core = CreatureCore(
        name=name, description="d", personality="p", fate_sheet=FateSheet(skills=skills)
    )
    return Character(core=core, char_class="Agent", race="Human", backstory="b")


def _enc(actors: list[EncounterActor], *, category: str = "combat") -> StructuredEncounter:
    return StructuredEncounter(
        encounter_type="duel",
        category=category,
        player_metric=EncounterMetric(name="p", threshold=10),
        opponent_metric=EncounterMetric(name="o", threshold=10),
        actors=actors,
    )


def test_barrier_waits_on_pcs_then_closes():
    enc = _enc(
        [
            EncounterActor(name="Vesska", role="lead", side="player"),
            EncounterActor(name="Brakka", role="muscle", side="player"),
            EncounterActor(name="Thug", role="foe", side="opponent"),
        ]
    )
    snap = GameSnapshot(
        genre_slug="fate_test",
        characters=[_pc("Vesska", {"Fight": 3}), _pc("Brakka", {"Fight": 2})],
        encounter=enc,
    )
    assert set(fate_waiting_actors(encounter=enc, snapshot=snap)) == {"Vesska", "Brakka"}
    assert fate_barrier_closed(encounter=enc, snapshot=snap) is False

    seal_fate_commit(
        encounter=enc, actor=enc.find_actor("Vesska"), action="attack", skill="Fight",
        target="Thug", ladder_total=5,
    )
    assert fate_waiting_actors(encounter=enc, snapshot=snap) == ["Brakka"]
    assert fate_barrier_closed(encounter=enc, snapshot=snap) is False

    seal_fate_commit(
        encounter=enc, actor=enc.find_actor("Brakka"), action="overcome", skill="Athletics",
        difficulty=1, ladder_total=2,
    )
    assert fate_barrier_closed(encounter=enc, snapshot=snap) is True


def test_double_commit_fails_loud():
    enc = _enc([EncounterActor(name="Vesska", role="lead", side="player")])
    snap = GameSnapshot(genre_slug="fate_test", characters=[_pc("Vesska", {"Fight": 3})], encounter=enc)
    seal_fate_commit(encounter=enc, actor=enc.find_actor("Vesska"), action="overcome", skill="Athletics", difficulty=2, ladder_total=4)
    with pytest.raises(FateConflictError):
        seal_fate_commit(encounter=enc, actor=enc.find_actor("Vesska"), action="attack", skill="Fight", target="x", ladder_total=4)


def test_turn_order_uses_notice_for_physical_empathy_for_mental():
    enc_actors = [
        EncounterActor(name="Quick", role="a", side="player"),
        EncounterActor(name="Slow", role="b", side="opponent"),
    ]
    physical = _enc(enc_actors, category="combat")
    snap = GameSnapshot(
        genre_slug="fate_test",
        characters=[_pc("Quick", {"Notice": 4, "Empathy": 1})],
        npcs=[],
        encounter=physical,
    )
    # Seat the opponent as an NPC so find_creature_core resolves its sheet.
    from sidequest.game.session import Npc

    snap.npcs.append(
        Npc(core=CreatureCore(name="Slow", description="d", personality="p", fate_sheet=FateSheet(skills={"Notice": 2, "Empathy": 5})))
    )
    assert fate_turn_order(encounter=physical, snapshot=snap, mental=False) == ["Quick", "Slow"]
    # Mental conflict flips it: Slow's Empathy 5 beats Quick's Empathy 1.
    assert fate_turn_order(encounter=physical, snapshot=snap, mental=True) == ["Slow", "Quick"]
```

> Confirm the `Npc` constructor signature while implementing (it composes a `CreatureCore` like `Character`). If `Npc` requires extra fields, add them — do not work around a missing field.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/server/dispatch/test_fate_conflict.py -n0 -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'sidequest.server.dispatch.fate_conflict'`

- [ ] **Step 3: Write the module (barrier + order)**

Create `sidequest/server/dispatch/fate_conflict.py`:

```python
"""Fate Core conflict exchange (ADR-144 F1c) — mirrors wn_round.py one tier over.

A Fate confrontation rides the SAME MP substrate as the WN sealed round: the
ADR-036 submit-and-wait barrier, expressed as a per-encounter sealed-commit
ledger (``encounter.fate_commits``, sibling to ``wn_commits``). Every seated PC
seals one proactive action; when the last commit arrives the exchange walks the
committed actors in Notice (physical) / Empathy (mental) order and resolves each
action through the F1a resolution primitive + the F1b stress/consequence
mutators. Defense is reactive — the engine rolls it for an attack's target.
Opponent actions are committed by the F2 narrator (F1c authors no opponent AI);
the barrier waits on PCs only (mirrors WN: engine-driven actors don't seal).

Every decision emits a ``fate.*`` OTEL span (the GM-panel lie detector). Native
and WN dispatch are untouched — this is a parallel engine selected by dispatch
(F1d) via ``isinstance(module, FateRulesetModule)``.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass

from sidequest.game.encounter import (
    EncounterActor,
    EncounterPhase,
    FateSealedCommit,
    StructuredEncounter,
)
from sidequest.game.fate_sheet import Aspect, FateSheet
from sidequest.game.ruleset.fate import FateRulesetModule
from sidequest.game.ruleset.fate_resolution import Opposition
from sidequest.game.session import GameSnapshot
from sidequest.telemetry.spans import (
    fate_aspect_created_span,
    fate_conceded_span,
    fate_exchange_committed_span,
    fate_exchange_order_span,
    fate_exchange_resolved_span,
    fate_taken_out_span,
)
from sidequest.telemetry.watcher_hub import publish_event as _watcher_publish

logger = logging.getLogger(__name__)

#: SRD defense skills, by conflict track. Refinable per genre as content (F4).
_DEFENSE_SKILL = {"physical": "Athletics", "mental": "Will"}
#: SRD initiative skills, by conflict track.
_ORDER_SKILL = {"physical": "Notice", "mental": "Empathy"}


class FateConflictError(ValueError):
    """A Fate exchange could not be resolved (double commit, attack with no
    target, a target without a Fate sheet, ...). Fail loud — No Silent
    Fallbacks (ADR-144 / SOUL.md)."""


def seal_fate_commit(
    *,
    encounter: StructuredEncounter,
    actor: EncounterActor,
    action: str,
    skill: str,
    target: str | None = None,
    difficulty: int = 0,
    ladder_total: int = 0,
    dice: tuple[int, int, int, int] = (0, 0, 0, 0),
    aspect_text: str = "",
) -> None:
    """Seal one participant's proactive action onto the exchange ledger.

    Mirrors ``seal_wn_commit``. A double commit in the same exchange is a client
    bug, rejected loudly: Fate action economy is one proactive action per actor
    per exchange.
    """
    if any(c.actor == actor.name for c in encounter.fate_commits):
        raise FateConflictError(
            f"{actor.name!r} has already committed an action this exchange — "
            "the Fate exchange seals one action per participant"
        )
    encounter.fate_commits.append(
        FateSealedCommit(
            actor=actor.name,
            action=action,  # validated against the four-action Literal by pydantic
            skill=skill,
            target=target,
            difficulty=difficulty,
            ladder_total=ladder_total,
            dice=dice,
            aspect_text=aspect_text,
        )
    )
    _watcher_publish(
        "state_transition",
        {
            "field": "encounter",
            "op": "fate_commit_sealed",
            "actor": actor.name,
            "action": action,
            "target": target or "",
            "committed_actors": ", ".join(c.actor for c in encounter.fate_commits),
            "source": "fate_action",
        },
        component="encounter",
    )


def _seated_pc_names(snapshot: GameSnapshot) -> set[str]:
    """PC names (``snapshot.characters``). Mirrors wn_round: only human-controlled
    PCs seal an action and hold the barrier; engine-driven NPC allies/opponents
    (in ``snapshot.npcs``) never seal."""
    return {ch.core.name for ch in snapshot.characters}


def fate_waiting_actors(
    *, encounter: StructuredEncounter, snapshot: GameSnapshot
) -> list[str]:
    """Player-side PCs the barrier is still waiting on. Mirrors
    ``wn_waiting_actors``: skip withdrawn, downed (no Fate sheet ⇒ counted as
    waiting), already-committed, and non-PC (ally) actors."""
    pc_names = _seated_pc_names(snapshot)
    committed = {c.actor for c in encounter.fate_commits}
    waiting: list[str] = []
    for a in encounter.actors:
        if a.side != "player" or a.withdrawn or a.name in committed:
            continue
        if a.name not in pc_names:
            continue  # engine-driven ally — never seals
        waiting.append(a.name)
    return waiting


def fate_barrier_closed(*, encounter: StructuredEncounter, snapshot: GameSnapshot) -> bool:
    """True when every live, seated player-side PC has committed an action."""
    return not fate_waiting_actors(encounter=encounter, snapshot=snapshot)


def fate_turn_order(
    *, encounter: StructuredEncounter, snapshot: GameSnapshot, mental: bool
) -> list[str]:
    """Seated, non-withdrawn participant names ordered by the conflict's
    initiative skill (Notice physical / Empathy mental), highest first. Ties keep
    seating order (Python's sort is stable)."""
    skill = _ORDER_SKILL["mental" if mental else "physical"]

    def rating(name: str) -> int:
        core = snapshot.find_creature_core(name)
        sheet = core.fate_sheet if core is not None else None
        return sheet.skills.get(skill, 0) if sheet is not None else 0

    seated = [
        a for a in encounter.actors if not a.withdrawn and a.side in ("player", "opponent")
    ]
    return [a.name for a in sorted(seated, key=lambda a: rating(a.name), reverse=True)]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/server/dispatch/test_fate_conflict.py -n0 -q`
Expected: PASS (3 tests: barrier, double-commit, turn order)

- [ ] **Step 5: Commit**

```bash
git add sidequest/server/dispatch/fate_conflict.py tests/server/dispatch/test_fate_conflict.py
git commit -m "feat(fate): exchange barrier + Notice/Empathy turn order (ADR-144 F1c)"
```

---

## Task 4: Shift absorption (orchestrates the F1b mutators)

**Files:**
- Modify: `sidequest/server/dispatch/fate_conflict.py`
- Test: `tests/server/dispatch/test_fate_conflict.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/server/dispatch/test_fate_conflict.py`:

```python
def test_absorb_uses_one_stress_box_when_it_covers_the_hit():
    from sidequest.game.ruleset import get_ruleset_module
    from sidequest.server.dispatch.fate_conflict import absorb_shifts

    module = get_ruleset_module("fate")
    sheet = FateSheet()  # physical boxes [1,2]; consequences open
    survived = absorb_shifts(
        module=module, sheet=sheet, track="physical", shifts=2, actor="Hero", source="Thug"
    )
    assert survived is True
    assert sheet.stress["physical"].boxes[1].checked is True  # the value-2 box
    assert all(c.aspect is None for c in sheet.consequences)  # no consequence needed


def test_absorb_combines_one_box_plus_consequences():
    from sidequest.game.ruleset import get_ruleset_module
    from sidequest.server.dispatch.fate_conflict import absorb_shifts

    module = get_ruleset_module("fate")
    sheet = FateSheet()  # best single box = 2; consequences 2/4/6/8
    survived = absorb_shifts(
        module=module, sheet=sheet, track="physical", shifts=5, actor="Hero", source="Thug"
    )
    assert survived is True
    # 5 shifts: largest box (2) + mild consequence (2) leaves 1 → moderate (4) covers it.
    assert sheet.stress["physical"].boxes[1].checked is True
    filled = [c.level for c in sheet.consequences if c.aspect is not None]
    assert filled == ["mild", "moderate"]
    # The consequence text is a real, descriptive default naming the source.
    mild = next(c for c in sheet.consequences if c.level == "mild")
    assert "Thug" in mild.aspect.text


def test_absorb_returns_false_when_capacity_exhausted():
    from sidequest.game.ruleset import get_ruleset_module
    from sidequest.server.dispatch.fate_conflict import absorb_shifts

    module = get_ruleset_module("fate")
    sheet = FateSheet()
    # Pre-deplete: check every stress box, fill every consequence slot.
    for b in sheet.stress["physical"].boxes:
        b.checked = True
    for c in sheet.consequences:
        c.aspect = Aspect(text="old wound", kind="consequence", free_invokes=0)
    survived = absorb_shifts(
        module=module, sheet=sheet, track="physical", shifts=1, actor="Hero", source="Thug"
    )
    assert survived is False  # nothing left to absorb with → taken out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/server/dispatch/test_fate_conflict.py -n0 -q -k "absorb"`
Expected: FAIL — `ImportError: cannot import name 'absorb_shifts'`

- [ ] **Step 3: Add `absorb_shifts`**

Append to `sidequest/server/dispatch/fate_conflict.py`:

```python
def absorb_shifts(
    *,
    module: FateRulesetModule,
    sheet: FateSheet,
    track: str,
    shifts: int,
    actor: str,
    source: str,
    _tracer=None,
) -> bool:
    """Absorb a ``shifts``-shift hit into ``track`` stress + consequences.

    SRD: a hit may be absorbed by AT MOST ONE stress box plus any number of
    consequence slots. Prefer the smallest single stress box that covers the
    whole hit; otherwise spend the largest available box to shave the hit and
    fill consequence slots smallest-first for the remainder. Returns ``True`` if
    fully absorbed (actor survives), ``False`` if capacity is exhausted (the
    caller takes them out). Delegates the atomic marks to the F1b mutators so
    each emits its own ``fate.stress.applied`` / ``fate.consequence.taken`` span.
    """
    remaining = shifts
    stress_track = sheet.stress.get(track)

    # One stress box (SRD: one per hit). Smallest box that alone covers the hit;
    # else the largest available box to shave it.
    if stress_track is not None:
        covering = [b for b in stress_track.boxes if not b.checked and b.value >= remaining]
        chosen = (
            min(covering, key=lambda b: b.value)
            if covering
            else max(
                (b for b in stress_track.boxes if not b.checked),
                key=lambda b: b.value,
                default=None,
            )
        )
        if chosen is not None:
            module.mark_stress(
                sheet=sheet, track=track, box_value=chosen.value, actor=actor, _tracer=_tracer
            )
            remaining = max(0, remaining - chosen.value)

    # Consequences, smallest-first, until the hit is covered.
    for slot in sorted(
        (c for c in sheet.consequences if c.aspect is None), key=lambda c: c.value
    ):
        if remaining <= 0:
            break
        module.take_consequence(
            sheet=sheet,
            level=slot.level,
            aspect_text=f"{slot.level.title()} consequence inflicted by {source}",
            actor=actor,
            _tracer=_tracer,
        )
        remaining = max(0, remaining - slot.value)

    return remaining <= 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/server/dispatch/test_fate_conflict.py -n0 -q -k "absorb"`
Expected: PASS (3 absorption tests)

- [ ] **Step 5: Commit**

```bash
git add sidequest/server/dispatch/fate_conflict.py tests/server/dispatch/test_fate_conflict.py
git commit -m "feat(fate): shift absorption over stress + consequences (ADR-144 F1c)"
```

---

## Task 5: `run_fate_exchange` + `concede_in_conflict` (the walk)

**Files:**
- Modify: `sidequest/server/dispatch/fate_conflict.py`
- Test: `tests/server/dispatch/test_fate_conflict.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/server/dispatch/test_fate_conflict.py`:

```python
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


def _otel():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return exporter, provider.get_tracer("test")


def _seal_attack(enc, snapshot, module, attacker, skill_rating, target, *, skill="Fight"):
    # Compute the attacker's sealed roll deterministically (FixedRng(0) → 4dF=0).
    outcome = module.resolve_action(
        skill_rating=skill_rating, opposition=Opposition(value=0, kind="active"), rng=_FixedRng(0)
    )
    seal_fate_commit(
        encounter=enc, actor=enc.find_actor(attacker), action="attack", skill=skill,
        target=target, ladder_total=outcome.ladder_total, dice=outcome.dice,
    )


def test_attack_hits_and_target_absorbs_survives():
    from sidequest.game.session import Npc
    from sidequest.game.ruleset import get_ruleset_module
    from sidequest.game.ruleset.fate_resolution import Opposition
    from sidequest.server.dispatch.fate_conflict import run_fate_exchange

    module = get_ruleset_module("fate")
    enc = _enc(
        [
            EncounterActor(name="Hero", role="lead", side="player"),
            EncounterActor(name="Thug", role="foe", side="opponent"),
        ]
    )
    hero = _pc("Hero", {"Fight": 4, "Notice": 3})
    snap = GameSnapshot(genre_slug="fate_test", characters=[hero], encounter=enc)
    snap.npcs.append(
        Npc(core=CreatureCore(name="Thug", description="d", personality="p", fate_sheet=FateSheet(skills={"Athletics": 1, "Notice": 1})))
    )
    _seal_attack(enc, snap, module, "Hero", 4, "Thug")  # ladder_total 4; defense 1 → shifts 3

    exporter, tracer = _otel()
    result = run_fate_exchange(encounter=enc, snapshot=snap, ruleset=module, rng=_FixedRng(0), _tracer=tracer)

    thug_sheet = snap.find_creature_core("Thug").fate_sheet
    assert thug_sheet.stress["physical"].boxes[1].checked is True  # absorbed 3 via box2 + mild
    assert enc.find_actor("Thug").withdrawn is False  # survived
    assert enc.resolved is False
    names = [s.name for s in exporter.get_finished_spans()]
    assert "fate.exchange.committed" in names
    assert "fate.exchange.order" in names
    assert "fate.exchange.resolved" in names
    assert not enc.fate_commits  # ledger cleared


def test_attack_takes_out_a_depleted_target_and_resolves():
    from sidequest.game.session import Npc
    from sidequest.game.ruleset import get_ruleset_module
    from sidequest.server.dispatch.fate_conflict import run_fate_exchange

    module = get_ruleset_module("fate")
    enc = _enc(
        [
            EncounterActor(name="Hero", role="lead", side="player"),
            EncounterActor(name="Thug", role="foe", side="opponent"),
        ]
    )
    snap = GameSnapshot(genre_slug="fate_test", characters=[_pc("Hero", {"Fight": 4})], encounter=enc)
    thug_sheet = FateSheet(skills={"Athletics": 1})
    for b in thug_sheet.stress["physical"].boxes:
        b.checked = True
    for c in thug_sheet.consequences:
        c.aspect = Aspect(text="old wound", kind="consequence", free_invokes=0)
    snap.npcs.append(Npc(core=CreatureCore(name="Thug", description="d", personality="p", fate_sheet=thug_sheet)))
    _seal_attack(enc, snap, module, "Hero", 4, "Thug")  # shifts 3, target cannot absorb

    exporter, tracer = _otel()
    run_fate_exchange(encounter=enc, snapshot=snap, ruleset=module, rng=_FixedRng(0), _tracer=tracer)

    assert enc.find_actor("Thug").withdrawn is True
    assert enc.resolved is True
    assert enc.outcome == "opponent_yielded"  # all opponents out → player victory label
    names = [s.name for s in exporter.get_finished_spans()]
    assert "fate.taken_out" in names


def test_create_advantage_places_a_situation_aspect():
    from sidequest.game.ruleset import get_ruleset_module
    from sidequest.server.dispatch.fate_conflict import run_fate_exchange

    module = get_ruleset_module("fate")
    enc = _enc([EncounterActor(name="Hero", role="lead", side="player")])
    snap = GameSnapshot(genre_slug="fate_test", characters=[_pc("Hero", {"Notice": 3})], encounter=enc)
    outcome = module.resolve_action(skill_rating=3, opposition=Opposition(value=0, kind="passive"), rng=_FixedRng(0))
    seal_fate_commit(
        encounter=enc, actor=enc.find_actor("Hero"), action="create_advantage", skill="Notice",
        difficulty=2, ladder_total=outcome.ladder_total, aspect_text="Pinned Down",
    )  # shifts = 3 - 2 = 1 → 1 free invoke

    exporter, tracer = _otel()
    run_fate_exchange(encounter=enc, snapshot=snap, ruleset=module, rng=_FixedRng(0), _tracer=tracer)

    assert [a.text for a in enc.situation_aspects] == ["Pinned Down"]
    assert enc.situation_aspects[0].free_invokes == 1
    names = [s.name for s in exporter.get_finished_spans()]
    assert "fate.aspect.created" in names


def test_attack_that_misses_deals_no_damage():
    from sidequest.game.session import Npc
    from sidequest.game.ruleset import get_ruleset_module
    from sidequest.server.dispatch.fate_conflict import run_fate_exchange

    module = get_ruleset_module("fate")
    enc = _enc(
        [
            EncounterActor(name="Hero", role="lead", side="player"),
            EncounterActor(name="Rival", role="foe", side="opponent"),
        ]
    )
    snap = GameSnapshot(genre_slug="fate_test", characters=[_pc("Hero", {"Fight": 1})], encounter=enc)
    # Rival's Athletics 3 defense beats Hero's Fight 1 attack → shifts -2 (clean miss).
    snap.npcs.append(Npc(core=CreatureCore(name="Rival", description="d", personality="p", fate_sheet=FateSheet(skills={"Athletics": 3}))))
    _seal_attack(enc, snap, module, "Hero", 1, "Rival")

    run_fate_exchange(encounter=enc, snapshot=snap, ruleset=module, rng=_FixedRng(0))

    rival_sheet = snap.find_creature_core("Rival").fate_sheet
    assert all(not b.checked for b in rival_sheet.stress["physical"].boxes)  # clean miss: no damage


def test_concede_withdraws_and_earns_fate_points():
    from sidequest.game.ruleset import get_ruleset_module
    from sidequest.server.dispatch.fate_conflict import concede_in_conflict

    module = get_ruleset_module("fate")
    enc = _enc([EncounterActor(name="Hero", role="lead", side="player")])
    sheet = FateSheet(fate_points=1)
    sheet.consequences[0].aspect = Aspect(text="Twisted Ankle", kind="consequence", free_invokes=1)
    hero = _pc("Hero", {"Fight": 2})
    hero.core.fate_sheet = sheet
    snap = GameSnapshot(genre_slug="fate_test", characters=[hero], encounter=enc)

    exporter, tracer = _otel()
    earned = concede_in_conflict(encounter=enc, snapshot=snap, ruleset=module, actor="Hero", _tracer=tracer)

    assert earned == 2  # 1 base + 1 consequence taken this conflict
    assert sheet.fate_points == 3
    assert enc.find_actor("Hero").withdrawn is True
    assert "fate.conceded" in [s.name for s in exporter.get_finished_spans()]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/server/dispatch/test_fate_conflict.py -n0 -q -k "attack or create_advantage or concede or miss"`
Expected: FAIL — `ImportError: cannot import name 'run_fate_exchange'`

- [ ] **Step 3: Implement the walk + concede + resolution helper**

Append to `sidequest/server/dispatch/fate_conflict.py`:

```python
@dataclass(frozen=True)
class FateExchangeResult:
    """What one exchange walk produced. ``resolution_order`` is the comma-joined
    token sequence walked (already on the ``fate.exchange.resolved`` span);
    ``narrator_hints`` are the mechanical-truth lines for the F2 narrator."""

    resolution_order: str
    resolved: bool
    narrator_hints: list[str]


def _roll_defense(
    *,
    ruleset: FateRulesetModule,
    snapshot: GameSnapshot,
    defender: str,
    mental: bool,
    rng: random.Random,
    _tracer=None,
) -> int:
    """Roll the target's reactive defense (4dF + defense skill) and return the
    ladder total. Emits ``fate.action_resolved`` for the defense roll (the GM
    panel sees the defender's number)."""
    core = snapshot.find_creature_core(defender)
    sheet = core.fate_sheet if core is not None else None
    skill = _DEFENSE_SKILL["mental" if mental else "physical"]
    rating = sheet.skills.get(skill, 0) if sheet is not None else 0
    outcome = ruleset.resolve_action(
        skill_rating=rating,
        opposition=Opposition(value=0, kind="active"),
        rng=rng,
        actor=defender,
        _tracer=_tracer,
    )
    return outcome.ladder_total


def _maybe_resolve_side_cleared(encounter: StructuredEncounter) -> None:
    """End the confrontation when one side is wholly withdrawn (ADR-116/-139).
    Uses the encounter's documented outcome labels: ``opponent_yielded`` (player
    victory) / ``yielded`` (player loss)."""
    if encounter.resolved:
        return
    players = [a for a in encounter.actors if a.side == "player"]
    opponents = [a for a in encounter.actors if a.side == "opponent"]
    if opponents and all(a.withdrawn for a in opponents):
        encounter.resolved = True
        encounter.outcome = "opponent_yielded"
        encounter.structured_phase = EncounterPhase.Resolution
    elif players and all(a.withdrawn for a in players):
        encounter.resolved = True
        encounter.outcome = "yielded"
        encounter.structured_phase = EncounterPhase.Resolution


def run_fate_exchange(
    *,
    encounter: StructuredEncounter,
    snapshot: GameSnapshot,
    ruleset: FateRulesetModule,
    rng: random.Random,
    round_number: int = 0,
    _tracer=None,
) -> FateExchangeResult:
    """Resolve one sealed Fate exchange in Notice/Empathy order.

    Walks the committed actors; per actor resolves the committed action (overcome
    / create-advantage / attack). Attacks roll the
    target's defense, compute shifts, and absorb via stress/consequences →
    taken-out when capacity is exhausted. Emits ``fate.exchange.committed`` →
    ``fate.exchange.order`` → ``fate.exchange.resolved`` (the GM-panel polygraph).
    Clears the ledger — commits never leak into the next exchange.
    """
    committed = ", ".join(c.actor for c in encounter.fate_commits)
    fate_exchange_committed_span(committed_actors=committed, _tracer=_tracer)

    mental = encounter.category == "social"
    order = fate_turn_order(encounter=encounter, snapshot=snapshot, mental=mental)
    fate_exchange_order_span(
        order=", ".join(order),
        skill=_ORDER_SKILL["mental" if mental else "physical"],
        _tracer=_tracer,
    )

    commits = {c.actor: c for c in encounter.fate_commits}
    walked: list[str] = []
    hints: list[str] = []

    for name in order:
        walked.append(name)
        actor_obj = encounter.find_actor(name)
        if actor_obj is None or actor_obj.withdrawn:
            continue
        commit = commits.get(name)
        if commit is None:
            # No proactive action sealed for this slot (e.g. an opponent the
            # narrator did not commit). Reactive defense only.
            continue
        if encounter.resolved:
            continue

        if commit.action == "attack":
            _resolve_attack(
                encounter=encounter, snapshot=snapshot, ruleset=ruleset, commit=commit,
                mental=mental, rng=rng, hints=hints, _tracer=_tracer,
            )
        elif commit.action == "create_advantage":
            _resolve_create_advantage(
                encounter=encounter, snapshot=snapshot, ruleset=ruleset, commit=commit,
                mental=mental, rng=rng, hints=hints, _tracer=_tracer,
            )
        elif commit.action == "overcome":
            _resolve_overcome(
                encounter=encounter, snapshot=snapshot, ruleset=ruleset, commit=commit,
                mental=mental, rng=rng, hints=hints,
            )

    encounter.fate_commits.clear()
    encounter.narrator_hints.extend(hints)
    resolution_order = ", ".join(walked)
    fate_exchange_resolved_span(
        resolution_order=resolution_order, resolved=encounter.resolved, _tracer=_tracer
    )
    _watcher_publish(
        "state_transition",
        {
            "field": "encounter",
            "op": "fate_exchange_resolved",
            "resolution_order": resolution_order,
            "encounter_type": encounter.encounter_type,
            "resolved": encounter.resolved,
            "source": "fate_exchange",
        },
        component="encounter",
    )
    return FateExchangeResult(
        resolution_order=resolution_order, resolved=encounter.resolved, narrator_hints=hints
    )


def _opposition_total(
    *, ruleset, snapshot, commit, mental, rng, _tracer
) -> int:
    """The opposition value for a committed action: an ACTIVE target's rolled
    defense, or the PASSIVE ``difficulty``."""
    if commit.target is not None:
        return _roll_defense(
            ruleset=ruleset, snapshot=snapshot, defender=commit.target,
            mental=mental, rng=rng, _tracer=_tracer,
        )
    return commit.difficulty


def _resolve_attack(
    *, encounter, snapshot, ruleset, commit, mental, rng, hints, _tracer
) -> None:
    if commit.target is None:
        raise FateConflictError("an attack must name a target (No Silent Fallbacks)")
    target_core = snapshot.find_creature_core(commit.target)
    if target_core is None or target_core.fate_sheet is None:
        raise FateConflictError(
            f"attack target {commit.target!r} has no Fate sheet to defend with"
        )
    defense_total = _roll_defense(
        ruleset=ruleset, snapshot=snapshot, defender=commit.target,
        mental=mental, rng=rng, _tracer=_tracer,
    )
    shifts = commit.ladder_total - defense_total
    track = "mental" if mental else "physical"
    if shifts <= 0:
        if shifts == 0:
            # SRD: a tied attack hands the defender a boost.
            boost = Aspect(
                text=f"Momentum vs {commit.actor}", kind="boost", free_invokes=1
            )
            encounter.situation_aspects.append(boost)
            fate_aspect_created_span(
                actor=commit.target, aspect=boost.text, free_invokes=1, _tracer=_tracer
            )
        hints.append(
            f"{commit.actor}'s attack on {commit.target} did not connect (shifts={shifts})."
        )
        return
    survived = absorb_shifts(
        module=ruleset, sheet=target_core.fate_sheet, track=track, shifts=shifts,
        actor=commit.target, source=commit.actor, _tracer=_tracer,
    )
    if survived:
        hints.append(
            f"{commit.target} absorbs {commit.actor}'s {shifts}-shift hit "
            "(stress/consequences)."
        )
        return
    target_actor = encounter.find_actor(commit.target)
    if target_actor is not None:
        target_actor.withdrawn = True
    fate_taken_out_span(actor=commit.target, by=commit.actor, shifts=shifts, _tracer=_tracer)
    hints.append(
        f"{commit.target} is TAKEN OUT by {commit.actor} ({shifts} unabsorbed shifts)."
    )
    _maybe_resolve_side_cleared(encounter)


def _resolve_create_advantage(
    *, encounter, snapshot, ruleset, commit, mental, rng, hints, _tracer
) -> None:
    opposition = _opposition_total(
        ruleset=ruleset, snapshot=snapshot, commit=commit,
        mental=mental, rng=rng, _tracer=_tracer,
    )
    shifts = commit.ladder_total - opposition
    if shifts >= 1:
        free = 2 if shifts >= 3 else 1  # Succeed-with-Style → two free invokes
        aspect = Aspect(
            text=commit.aspect_text or f"Advantage by {commit.actor}",
            kind="situation",
            free_invokes=free,
        )
        encounter.situation_aspects.append(aspect)
        fate_aspect_created_span(
            actor=commit.actor, aspect=aspect.text, free_invokes=free, _tracer=_tracer
        )
    elif shifts == 0:
        boost = Aspect(
            text=commit.aspect_text or f"Fleeting Opening by {commit.actor}",
            kind="boost",
            free_invokes=1,
        )
        encounter.situation_aspects.append(boost)
        fate_aspect_created_span(
            actor=commit.actor, aspect=boost.text, free_invokes=1, _tracer=_tracer
        )
    else:
        hints.append(f"{commit.actor}'s create-advantage failed (shifts={shifts}).")


def _resolve_overcome(
    *, encounter, snapshot, ruleset, commit, mental, rng, hints
) -> None:
    opposition = _opposition_total(
        ruleset=ruleset, snapshot=snapshot, commit=commit,
        mental=mental, rng=rng, _tracer=None,
    )
    shifts = commit.ladder_total - opposition
    if shifts >= 1:
        hints.append(f"{commit.actor} overcomes the obstacle (shifts={shifts}).")
    elif shifts == 0:
        hints.append(f"{commit.actor} overcomes at a minor cost (tie).")
    else:
        hints.append(f"{commit.actor} fails to overcome (shifts={shifts}).")


def concede_in_conflict(
    *,
    encounter: StructuredEncounter,
    snapshot: GameSnapshot,
    ruleset: FateRulesetModule,
    actor: str,
    _tracer=None,
) -> int:
    """Player-initiated concession (pre-roll): the actor leaves on their terms,
    withdrawing and earning 1 fate point + 1 per consequence taken this conflict
    (SRD). Returns the fate points earned. Fails loud without a Fate sheet."""
    core = snapshot.find_creature_core(actor)
    if core is None or core.fate_sheet is None:
        raise FateConflictError(f"{actor!r} has no Fate sheet to concede with")
    filled = sum(1 for c in core.fate_sheet.consequences if c.aspect is not None)
    earned = 1 + filled
    for _ in range(earned):
        ruleset.earn_fate_point(
            sheet=core.fate_sheet, reason="concede", actor=actor, _tracer=_tracer
        )
    actor_obj = encounter.find_actor(actor)
    if actor_obj is not None:
        actor_obj.withdrawn = True
    fate_conceded_span(actor=actor, fate_points_earned=earned, _tracer=_tracer)
    _maybe_resolve_side_cleared(encounter)
    return earned
```

> The four action resolvers (`_resolve_attack`, `_resolve_create_advantage`, `_resolve_overcome`) and `_opposition_total` are module-level functions referenced by `run_fate_exchange`. They are defined after it in the file; Python resolves them at call time, so ordering is fine — but keep them in the same module.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/server/dispatch/test_fate_conflict.py -n0 -q`
Expected: PASS (all exchange tests — attack-survives, taken-out + resolve, create-advantage, clean miss, concede, plus Tasks 3–4 tests)

- [ ] **Step 5: Commit**

```bash
git add sidequest/server/dispatch/fate_conflict.py tests/server/dispatch/test_fate_conflict.py
git commit -m "feat(fate): run_fate_exchange walk + four actions + taken-out/concede (ADR-144 F1c)"
```

---

## Task 6: Gate — lint, format, types, suites

**Files:** none (verification only)

- [ ] **Step 1: Lint the changed files (scoped)**

Run: `uv run ruff check sidequest/game/encounter.py sidequest/server/dispatch/fate_conflict.py sidequest/telemetry/spans/fate.py sidequest/telemetry/spans/__init__.py tests/game/test_fate_commit_model.py tests/server/dispatch/test_fate_conflict.py`
Expected: `All checks passed!`

- [ ] **Step 2: Format the changed files (scoped)**

Run: `uv run ruff format sidequest/game/encounter.py sidequest/server/dispatch/fate_conflict.py sidequest/telemetry/spans/fate.py sidequest/telemetry/spans/__init__.py tests/game/test_fate_commit_model.py tests/server/dispatch/test_fate_conflict.py`
Expected: unchanged or reformatted in place (commit any reformat).

- [ ] **Step 3: Type check**

Run: `uv run pyright sidequest/game/encounter.py sidequest/server/dispatch/fate_conflict.py sidequest/telemetry/spans/fate.py`
Expected: `0 errors`

- [ ] **Step 4: Run the fate + encounter + routing suites**

Run: `uv run pytest tests/server/dispatch/test_fate_conflict.py tests/game/test_fate_commit_model.py tests/game/ruleset/ tests/telemetry/test_routing_completeness.py -n0 -q`
Expected: PASS — F1a/F1b fate tests still green, the new exchange suite passes, routing lint green, no encounter/ruleset regressions.

- [ ] **Step 5: Regression sweep on the encounter + WN round (no cross-contamination)**

Run: `uv run pytest tests/integration/test_102_4_wn_sealed_round.py -n0 -q`
Expected: PASS — the WN sealed round is untouched (the new `fate_commits` ledger is additive; `wn_commits` and the WN walk are unchanged).

- [ ] **Step 6: Commit any fixups**

```bash
git add -p
git commit -m "chore(fate): lint/format/type fixups (ADR-144 F1c)"
```

---

## Self-review (done against the spec)

- **Spec §4.2 coverage:** sides + zones + Notice/Empathy order — Tasks 1/3; sealed barrier (same ADR-036 substrate, sibling ledger) — Task 3; actions (overcome/create-advantage/attack + reactive defend) — Task 5; active vs passive opposition (`_opposition_total`) — Task 5; shifts→stress/consequences — Task 4; taken-out — Task 5; concede — Task 5; create-advantage→situation aspect with free invokes — Task 5. ✓
- **Spec §6 OTEL:** `fate.exchange.committed/order/resolved`, `fate.aspect.created`, `fate.taken_out`, `fate.conceded` — Task 2; defense rolls reuse F1a `fate.action_resolved`; stress/consequence marks reuse F1b spans. All GM-panel-routed. ✓
- **Spec §7 wiring + properties:** an exchange resolves attack→stress→consequence→taken-out — Task 5; concede path — Task 5; create-advantage places an aspect with a free invoke — Task 5; clean miss deals no damage — Task 5; absorption property (absorbed ≤ capacity else taken-out) — Task 4. Driven through the **real registered** `FateRulesetModule` with OTEL-span assertions, not source greps. ✓
- **Mirror fidelity (handoff):** `seal_fate_commit`/`fate_barrier_closed`/`run_fate_exchange` mirror `seal_wn_commit`/`wn_barrier_closed`/`run_wn_round`; the ledger is a sibling of `wn_commits`; the PC-vs-ally barrier discrimination mirrors `wn_waiting_actors`. ✓
- **No Stubbing / No Silent Fallbacks:** `FateConflictError` on every impossible state (double commit, attack without target, target without a sheet, concede without a sheet); consequence text is a real descriptive default, not a placeholder. ✓
- **Don't balance (SOUL):** zones are represented + recorded, not turned into a range/movement balancing subsystem; opponent AI is the F2 narrator's job, not invented here. ✓
- **Routing-lint safety:** new spans use literal keys + `SPAN_ROUTES` (no `SPAN_*` constants). ✓
- **Native/WN untouched:** the Fate ledger/aspects/zones are additive encounter fields; the WN round suite still passes — Task 6 Step 5. ✓
- **Placeholder scan:** none — every code/command step is concrete.
- **Type consistency:** `FateSealedCommit`, `FateConflictError`, `FateExchangeResult`, `seal_fate_commit`, `fate_waiting_actors`, `fate_barrier_closed`, `fate_turn_order`, `absorb_shifts`, `run_fate_exchange`, `concede_in_conflict` and all span helpers are named identically across tasks. ✓
- **Out of F1c scope (correct):** the dispatch entry + protocol message + handler routing (F1d), the narrator action classifier + opponent AI (F2), the UI (F3), content skill lists (F4).
