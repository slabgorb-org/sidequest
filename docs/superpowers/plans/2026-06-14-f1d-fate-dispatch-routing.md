# F1d — Fate Dispatch Routing + End-to-End Wiring — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the Fate engine into live dispatch — a `FATE_ACTION` message routes a player's Fate action to `fate_conflict.run_fate_exchange`, selected by `isinstance(module, FateRulesetModule)` exactly as WN combat is gated by `isinstance(module, WithoutNumberRulesetModule)`. Native and WN paths are untouched, and an end-to-end wiring test proves a Fate-bound pack reaches the exchange through the real registry + handler.

**Architecture:** Fate's action vocabulary (four actions + 4dF) is fundamentally different from the beat+d20 `DICE_THROW` path, so F1d adds a dedicated, non-shoehorned channel: a `FATE_ACTION` `GameMessage` carrying a `FateActionPayload`, a `FateActionHandler` registered in the `_MESSAGE_HANDLERS` registry, and a `dispatch_fate_action` entry in `fate_conflict.py`. The routing decision is an `isinstance(ruleset, FateRulesetModule)` guard at the dispatch entry (resolved from the bound pack via the real `get_ruleset_module`), mirroring the WN `isinstance` gate in `dispatch_dice_throw`. `dispatch_fate_action` computes the sealed roll through F1a's primitive, seals via F1c's `seal_fate_commit`, and fires `run_fate_exchange` when the barrier closes — concede routes to F1c's `concede_in_conflict`.

**Tech Stack:** Python 3.14, pydantic v2 (discriminated-union `GameMessage`), pytest (`-n0`), OpenTelemetry SDK, `uv`. **All paths below are under `sidequest-server/`.** Branch off `develop` (gitflow); feature branch `feat/f1d-fate-dispatch`.

**Decision of record:** ADR-144. **Design:** `docs/superpowers/specs/2026-06-14-fate-core-binding-replaces-native-design.md` §4.1–§4.2 + §7. **Depends on:** F1a, F1b, **F1c** (`seal_fate_commit`, `fate_barrier_closed`, `run_fate_exchange`, `concede_in_conflict`, `FateConflictError`) merged.

---

## F1 slice map (context — this plan is F1d only)

| Slice | Scope | Status |
|-------|-------|--------|
| F1a | Resolution primitive + module registration + OTEL | merged (prereq) |
| F1b | Fate character facet + fate-point economy | merged (prereq) |
| F1c | `fate_conflict.py` exchange engine | merged (prereq) |
| **F1d** | Dispatch routing by `isinstance(module, FateRulesetModule)` + end-to-end wiring | **this plan** |

F1d closes F1: after this, a `ruleset: fate` pack's combat is fully reachable from a player message through the real handler → dispatch → exchange. The narrator action-classifier (F2), the UI (F3), and pack content (F4) build on top.

---

## Routing model (read before coding)

- **WN precedent.** WN combat reuses the `DICE_THROW` message because it is still beat+d20 — the routing is `wn_sealed_round = ... and isinstance(ruleset, WithoutNumberRulesetModule) and ...` inside `dispatch_dice_throw` (`server/dispatch/dice.py:671`). The `isinstance` against the bound module class is the routing decision (ADR-117 — no genre string branches).
- **Why Fate gets its own channel (not a `DICE_THROW` branch).** A Fate action is `{overcome, create_advantage, attack, concede}` + a skill + 4dF — it has no `beat_id` and no d20 face. Forcing it through `DiceThrowPayload` would be a shoehorn (the handoff forbids it). So F1d adds a `FATE_ACTION` message; the message type selects the channel and `dispatch_fate_action` guards it with `isinstance(ruleset, FateRulesetModule)`.
- **Native/WN untouched.** `DICE_THROW` still routes to `dispatch_dice_throw`; the native and WN engines are not modified. A `FATE_ACTION` under a non-Fate pack fails loud (No Silent Fallbacks) — it is a config/client bug, not a fallback.
- **End-to-end proof.** The wiring net is OTEL-span + runtime-registry assertions through the **real** registry and handler (per server CLAUDE.md "No Source-Text Wiring Tests"): (1) a `fate`-slug pack resolves to `FateRulesetModule` and routes to `run_fate_exchange` (the `fate.exchange.resolved` span fires); (2) the `FATE_ACTION` message type is wired to `FateActionHandler` in the registry; (3) the handler drives `dispatch_fate_action` end-to-end (encounter state changes); (4) a non-Fate ruleset is rejected loud.

---

## File structure (F1d)

- **Modify** `sidequest/protocol/enums.py` — add `FATE_ACTION` to `MessageType`.
- **Create** `sidequest/protocol/fate.py` — `FateActionPayload`.
- **Modify** `sidequest/protocol/messages.py` — `FateActionMessage` variant + add to `_Phase1Variant`.
- **Modify** `sidequest/server/dispatch/fate_conflict.py` — add `dispatch_fate_action` + `FateDispatchResult`.
- **Create** `sidequest/handlers/fate_action.py` — `FateActionHandler` + `HANDLER`.
- **Modify** `sidequest/server/websocket_session_handler.py` — register `FATE_ACTION` in `_MESSAGE_HANDLERS`.
- **Create** `tests/protocol/test_fate_action_message.py` — payload + union parse tests.
- **Create** `tests/server/dispatch/test_fate_dispatch_routing.py` — `dispatch_fate_action` routing + fail-loud + barrier + concede.
- **Create** `tests/server/test_fate_action_handler_wiring.py` — registry membership + handler end-to-end.

---

## Task 1: `FATE_ACTION` message type + payload + union variant

**Files:**
- Modify: `sidequest/protocol/enums.py`
- Create: `sidequest/protocol/fate.py`
- Modify: `sidequest/protocol/messages.py`
- Test: `tests/protocol/test_fate_action_message.py`

- [ ] **Step 1: Write the failing test**

Create `tests/protocol/test_fate_action_message.py`:

```python
from __future__ import annotations

import pytest
from pydantic import ValidationError

from sidequest.protocol.enums import MessageType
from sidequest.protocol.fate import FateActionPayload
from sidequest.protocol.messages import FateActionMessage, GameMessage


def test_payload_defaults_and_required():
    p = FateActionPayload(request_id="r1", action="attack", skill="Fight", target="Thug")
    assert p.action == "attack"
    assert p.difficulty == 0
    assert p.invoke_aspect == ""
    assert p.aspect_text == ""


def test_payload_rejects_unknown_action():
    with pytest.raises(ValidationError):
        FateActionPayload(request_id="r1", action="parry", skill="Fight")


def test_concede_is_a_valid_action_value():
    p = FateActionPayload(request_id="r1", action="concede", skill="")
    assert p.action == "concede"


def test_message_parses_through_the_discriminated_union():
    wire = {
        "type": "FATE_ACTION",
        "payload": {
            "request_id": "r1",
            "action": "create_advantage",
            "skill": "Notice",
            "difficulty": 2,
            "aspect_text": "Pinned Down",
        },
        "player_id": "p1",
    }
    msg = GameMessage.model_validate(wire)
    assert isinstance(msg.root, FateActionMessage)
    assert msg.root.type == MessageType.FATE_ACTION
    assert msg.root.payload.aspect_text == "Pinned Down"
    assert msg.root.player_id == "p1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/protocol/test_fate_action_message.py -n0 -q`
Expected: FAIL — `ImportError: cannot import name 'FateActionPayload' from 'sidequest.protocol.fate'`

- [ ] **Step 3: Add the enum value**

In `sidequest/protocol/enums.py`, add `FATE_ACTION` to `MessageType` immediately after the `CHECK_THROW` entry (keep it near the other player-submission verbs):

```python
    # ADR-144: a Fate-bound pack's player action (one of the four Fate actions or
    # a concession). Routed to FateActionHandler → fate_conflict, gated by
    # isinstance(ruleset, FateRulesetModule). Distinct from DICE_THROW (beat+d20).
    FATE_ACTION = "FATE_ACTION"
```

- [ ] **Step 4: Create the payload**

Create `sidequest/protocol/fate.py`:

```python
"""Fate Core wire payloads (ADR-144 F1d).

``FateActionPayload`` is the player's submission on the Fate channel — one of the
four Fate actions (or a concession), the skill used, and the opposition shape
(active ``target`` or passive ``difficulty``). The 4dF roll is the server's job
(``FateRulesetModule.resolve_action``); the client submits the INTENT, not faces
(unlike DICE_THROW's physics-is-the-roll). The F3 UI and F2 narrator both emit
this message.
"""

from __future__ import annotations

from typing import Literal

from sidequest.protocol.base import ProtocolBase


class FateActionPayload(ProtocolBase):
    """Client -> server: a Fate action to seal (or a concession).

    - ``action``: the three proactive actions plus ``concede`` (concede is
      pre-roll and routes to ``concede_in_conflict``, never to the commit ledger).
    - ``skill``: the skill name used (empty for ``concede``).
    - ``target``: the opposed participant for an ACTIVE action (the engine rolls
      their defense); ``None`` for a passive action.
    - ``difficulty``: the passive opposition value when ``target`` is ``None``.
    - ``invoke_aspect``: an aspect text to invoke for +2 before the roll (spends a
      free invoke or a fate point — server-side via the F1b economy).
    - ``aspect_text``: the situation aspect a ``create_advantage`` intends to place.
    """

    request_id: str
    action: Literal["overcome", "create_advantage", "attack", "concede"]
    skill: str = ""
    target: str | None = None
    difficulty: int = 0
    invoke_aspect: str = ""
    aspect_text: str = ""
```

- [ ] **Step 5: Add the message variant + register it in the union**

In `sidequest/protocol/messages.py`:

Add the payload import near the other protocol-payload imports (find the `from sidequest.protocol.dice import (...)` block and add this line after it):

```python
from sidequest.protocol.fate import FateActionPayload
```

Add the `FateActionMessage` class immediately after `DiceThrowMessage` (around line 1276):

```python
class FateActionMessage(ProtocolBase):
    """GameMessage::FateAction — a Fate-bound pack's player action (ADR-144)."""

    type: Literal[MessageType.FATE_ACTION] = MessageType.FATE_ACTION
    payload: FateActionPayload
    player_id: str = ""
```

Add `FateActionMessage` to the `_Phase1Variant` union (after the `DiceThrowMessage` entry around line 1659):

```python
    | DiceThrowMessage
    | FateActionMessage
```

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest tests/protocol/test_fate_action_message.py -n0 -q`
Expected: PASS (all 4 tests)

- [ ] **Step 7: Guard the protocol suite (the union must still parse every type)**

Run: `uv run pytest tests/protocol/ -n0 -q`
Expected: PASS — the additive union variant breaks no existing discriminated-union parse.

- [ ] **Step 8: Commit**

```bash
git add sidequest/protocol/enums.py sidequest/protocol/fate.py sidequest/protocol/messages.py tests/protocol/test_fate_action_message.py
git commit -m "feat(fate): FATE_ACTION message type + FateActionPayload + union variant (ADR-144 F1d)"
```

---

## Task 2: `dispatch_fate_action` — the routing entry

**Files:**
- Modify: `sidequest/server/dispatch/fate_conflict.py`
- Test: `tests/server/dispatch/test_fate_dispatch_routing.py`

- [ ] **Step 1: Write the failing test**

Create `tests/server/dispatch/test_fate_dispatch_routing.py`:

```python
from __future__ import annotations

import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from sidequest.game.character import Character
from sidequest.game.creature_core import CreatureCore
from sidequest.game.encounter import EncounterActor, EncounterMetric, StructuredEncounter
from sidequest.game.fate_sheet import Aspect, FateSheet
from sidequest.game.ruleset import get_ruleset_module
from sidequest.game.session import GameSnapshot, Npc
from sidequest.protocol.fate import FateActionPayload
from sidequest.server.dispatch.fate_conflict import (
    FateConflictError,
    dispatch_fate_action,
)


class _FixedRng:
    def __init__(self, value: int = 0) -> None:
        self._value = value

    def choice(self, seq):
        return self._value


def _otel():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return exporter, provider.get_tracer("test")


def _pc(name: str, skills: dict[str, int]) -> Character:
    core = CreatureCore(
        name=name, description="d", personality="p", fate_sheet=FateSheet(skills=skills)
    )
    return Character(core=core, char_class="Agent", race="Human", backstory="b")


def _depleted_thug() -> Npc:
    sheet = FateSheet(skills={"Athletics": 0})
    for b in sheet.stress["physical"].boxes:
        b.checked = True
    for c in sheet.consequences:
        c.aspect = Aspect(text="old wound", kind="consequence", free_invokes=0)
    return Npc(core=CreatureCore(name="Thug", description="d", personality="p", fate_sheet=sheet))


def _solo_combat():
    enc = StructuredEncounter(
        encounter_type="duel",
        category="combat",
        player_metric=EncounterMetric(name="p", threshold=10),
        opponent_metric=EncounterMetric(name="o", threshold=10),
        actors=[
            EncounterActor(name="Hero", role="lead", side="player"),
            EncounterActor(name="Thug", role="foe", side="opponent"),
        ],
    )
    snap = GameSnapshot(genre_slug="fate_test", characters=[_pc("Hero", {"Fight": 4})], encounter=enc)
    snap.npcs.append(_depleted_thug())
    return snap, enc


def test_fate_bound_ruleset_routes_to_the_exchange():
    snap, enc = _solo_combat()
    ruleset = get_ruleset_module("fate")  # real registry: a "fate"-slug pack resolves here
    payload = FateActionPayload(request_id="r1", action="attack", skill="Fight", target="Thug")
    exporter, tracer = _otel()

    result = dispatch_fate_action(
        payload=payload, actor_name="Hero", encounter=enc, ruleset=ruleset,
        snapshot=snap, rng=_FixedRng(0), _tracer=tracer,
    )

    # Solo barrier closes immediately → the exchange ran (routed to fate_conflict).
    assert result.commitment_pending is False
    assert result.exchange is not None
    names = [s.name for s in exporter.get_finished_spans()]
    assert "fate.exchange.resolved" in names
    assert enc.find_actor("Thug").withdrawn is True  # depleted target taken out
    assert enc.resolved is True


def test_non_fate_ruleset_is_rejected_loud():
    snap, enc = _solo_combat()
    native = get_ruleset_module("native")  # NOT a FateRulesetModule
    payload = FateActionPayload(request_id="r1", action="attack", skill="Fight", target="Thug")
    with pytest.raises(FateConflictError):
        dispatch_fate_action(
            payload=payload, actor_name="Hero", encounter=enc, ruleset=native,
            snapshot=snap, rng=_FixedRng(0),
        )


def test_unclosed_barrier_seals_and_pends():
    enc = StructuredEncounter(
        encounter_type="duel",
        category="combat",
        player_metric=EncounterMetric(name="p", threshold=10),
        opponent_metric=EncounterMetric(name="o", threshold=10),
        actors=[
            EncounterActor(name="Hero", role="lead", side="player"),
            EncounterActor(name="Ally", role="muscle", side="player"),
            EncounterActor(name="Thug", role="foe", side="opponent"),
        ],
    )
    snap = GameSnapshot(
        genre_slug="fate_test",
        characters=[_pc("Hero", {"Fight": 4}), _pc("Ally", {"Fight": 2})],
        encounter=enc,
    )
    snap.npcs.append(_depleted_thug())
    ruleset = get_ruleset_module("fate")
    payload = FateActionPayload(request_id="r1", action="attack", skill="Fight", target="Thug")

    result = dispatch_fate_action(
        payload=payload, actor_name="Hero", encounter=enc, ruleset=ruleset, snapshot=snap, rng=_FixedRng(0)
    )

    assert result.commitment_pending is True  # Ally has not committed
    assert result.exchange is None
    assert enc.fate_commits[0].actor == "Hero"  # sealed, not resolved
    assert enc.find_actor("Thug").withdrawn is False


def test_concede_routes_to_concession_not_the_ledger():
    enc = StructuredEncounter(
        encounter_type="duel",
        category="combat",
        player_metric=EncounterMetric(name="p", threshold=10),
        opponent_metric=EncounterMetric(name="o", threshold=10),
        actors=[EncounterActor(name="Hero", role="lead", side="player")],
    )
    hero = _pc("Hero", {"Fight": 2})
    hero.core.fate_sheet.fate_points = 1
    snap = GameSnapshot(genre_slug="fate_test", characters=[hero], encounter=enc)
    ruleset = get_ruleset_module("fate")
    payload = FateActionPayload(request_id="r1", action="concede", skill="")
    exporter, tracer = _otel()

    result = dispatch_fate_action(
        payload=payload, actor_name="Hero", encounter=enc, ruleset=ruleset,
        snapshot=snap, rng=_FixedRng(0), _tracer=tracer,
    )

    assert result.commitment_pending is False
    assert not enc.fate_commits  # concede never seals
    assert enc.find_actor("Hero").withdrawn is True
    assert hero.core.fate_sheet.fate_points == 2  # earned 1 (no consequences yet)
    assert "fate.conceded" in [s.name for s in exporter.get_finished_spans()]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/server/dispatch/test_fate_dispatch_routing.py -n0 -q`
Expected: FAIL — `ImportError: cannot import name 'dispatch_fate_action' from 'sidequest.server.dispatch.fate_conflict'`

- [ ] **Step 3: Add `dispatch_fate_action`**

In `sidequest/server/dispatch/fate_conflict.py`:

Add the imports the dispatch entry needs (near the top, with the other imports):

```python
from sidequest.game.ruleset.base import RulesetModule
from sidequest.game.ruleset.fate_resolution import Opposition
```

> `FateRulesetModule` is already imported in F1c. `Opposition` may already be imported (F1c's `_roll_defense` uses it) — keep a single import.

Append to the module:

```python
@dataclass(frozen=True)
class FateDispatchResult:
    """What one FATE_ACTION dispatch produced. ``commitment_pending`` mirrors the
    WN ``DiceThrowOutcome.commitment_pending`` idiom: True when the action sealed
    and the barrier is still open; False when this action fired the exchange (or
    was a concession). ``exchange`` is the walk's result, or None when pending /
    conceded."""

    commitment_pending: bool
    exchange: FateExchangeResult | None


def dispatch_fate_action(
    *,
    payload,
    actor_name: str,
    encounter: StructuredEncounter | None,
    ruleset: RulesetModule,
    snapshot: GameSnapshot,
    rng: random.Random,
    round_number: int = 0,
    _tracer=None,
) -> FateDispatchResult:
    """Route a player's Fate action to the exchange engine (ADR-144 F1d).

    The routing decision is ``isinstance(ruleset, FateRulesetModule)`` — exactly
    how ``dispatch_dice_throw`` gates WN combat on ``WithoutNumberRulesetModule``.
    A FATE_ACTION under a non-Fate ruleset is a config/client bug, rejected loud
    (No Silent Fallbacks). Concede is pre-roll and routes to
    ``concede_in_conflict``; the three proactive actions seal via
    ``seal_fate_commit`` and fire ``run_fate_exchange`` when the barrier closes.
    """
    if not isinstance(ruleset, FateRulesetModule):
        raise FateConflictError(
            f"FATE_ACTION dispatched under non-Fate ruleset "
            f"{type(ruleset).__name__!r}; the Fate channel is only valid for a "
            "pack bound 'ruleset: fate' (No Silent Fallbacks — ADR-144)"
        )
    if encounter is None or encounter.resolved:
        raise FateConflictError("FATE_ACTION requires an active, unresolved encounter")
    actor_obj = encounter.find_actor(actor_name)
    if actor_obj is None:
        raise FateConflictError(f"{actor_name!r} is not seated in this encounter")

    # Concession is pre-roll, non-committing.
    if payload.action == "concede":
        concede_in_conflict(
            encounter=encounter, snapshot=snapshot, ruleset=ruleset, actor=actor_name, _tracer=_tracer
        )
        return FateDispatchResult(commitment_pending=False, exchange=None)

    core = snapshot.find_creature_core(actor_name)
    if core is None or core.fate_sheet is None:
        raise FateConflictError(f"{actor_name!r} has no Fate sheet to act with")

    # Optional pre-roll invoke (+2; spends a free invoke or a fate point — F1b).
    invoke_bonus = 0
    if payload.invoke_aspect:
        invoke_bonus = ruleset.invoke_aspect(
            sheet=core.fate_sheet,
            aspect_text=payload.invoke_aspect,
            mode="bonus",
            actor=actor_name,
            _tracer=_tracer,
        )

    # All three proactive actions seal the attacker's 4dF roll now (mirrors WN
    # sealing the to-hit at commit); concede already returned above. Defense is
    # reactive — the engine rolls it for the target at resolution, never a
    # committed action (there is no full_defense — not in the Fate SRD).
    rating = core.fate_sheet.skills.get(payload.skill, 0)
    outcome = ruleset.resolve_action(
        skill_rating=rating,
        opposition=Opposition(
            value=payload.difficulty,
            kind="active" if payload.target is not None else "passive",
        ),
        rng=rng,
        invoke_bonus=invoke_bonus,
        actor=actor_name,
        _tracer=_tracer,
    )
    ladder_total, dice = outcome.ladder_total, outcome.dice

    seal_fate_commit(
        encounter=encounter,
        actor=actor_obj,
        action=payload.action,
        skill=payload.skill,
        target=payload.target,
        difficulty=payload.difficulty,
        ladder_total=ladder_total,
        dice=dice,
        aspect_text=payload.aspect_text,
    )

    if fate_barrier_closed(encounter=encounter, snapshot=snapshot):
        result = run_fate_exchange(
            encounter=encounter,
            snapshot=snapshot,
            ruleset=ruleset,
            rng=rng,
            round_number=round_number,
            _tracer=_tracer,
        )
        return FateDispatchResult(commitment_pending=False, exchange=result)
    return FateDispatchResult(commitment_pending=True, exchange=None)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/server/dispatch/test_fate_dispatch_routing.py -n0 -q`
Expected: PASS (4 tests: routes-to-exchange, fail-loud, pends, concede)

- [ ] **Step 5: Commit**

```bash
git add sidequest/server/dispatch/fate_conflict.py tests/server/dispatch/test_fate_dispatch_routing.py
git commit -m "feat(fate): dispatch_fate_action routing entry (isinstance gate) (ADR-144 F1d)"
```

---

## Task 3: `FateActionHandler` + registry wiring

**Files:**
- Create: `sidequest/handlers/fate_action.py`
- Modify: `sidequest/server/websocket_session_handler.py`
- Test: `tests/server/test_fate_action_handler_wiring.py`

- [ ] **Step 1: Write the failing test**

Create `tests/server/test_fate_action_handler_wiring.py`:

```python
"""Wiring net for the FATE_ACTION channel (ADR-144 F1d).

Two assertions, neither a source grep (server CLAUDE.md):
  1. Registry membership — the FATE_ACTION message type resolves to the real
     FateActionHandler singleton (runtime registry check, the legitimate
     reflection exception).
  2. End-to-end — driving HANDLER.handle on a Fate-bound fake session reaches
     dispatch_fate_action → run_fate_exchange (encounter state changes).
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

from sidequest.game.character import Character
from sidequest.game.creature_core import CreatureCore
from sidequest.game.encounter import EncounterActor, EncounterMetric, StructuredEncounter
from sidequest.game.fate_sheet import Aspect, FateSheet
from sidequest.game.session import GameSnapshot, Npc
from sidequest.handlers.fate_action import HANDLER as FATE_HANDLER
from sidequest.protocol.fate import FateActionPayload
from sidequest.protocol.messages import FateActionMessage
from sidequest.server.session_handler import _State
from sidequest.server.websocket_session_handler import WebSocketSessionHandler


def test_fate_action_is_registered_to_its_handler():
    # The registry is built lazily on first lookup; force it via the resolver.
    handler = WebSocketSessionHandler._message_handler_for("FATE_ACTION")
    assert handler is FATE_HANDLER


def _pc(name: str, skills: dict[str, int]) -> Character:
    core = CreatureCore(
        name=name, description="d", personality="p", fate_sheet=FateSheet(skills=skills)
    )
    return Character(core=core, char_class="Agent", race="Human", backstory="b")


def _depleted_thug() -> Npc:
    sheet = FateSheet(skills={"Athletics": 0})
    for b in sheet.stress["physical"].boxes:
        b.checked = True
    for c in sheet.consequences:
        c.aspect = Aspect(text="old wound", kind="consequence", free_invokes=0)
    return Npc(core=CreatureCore(name="Thug", description="d", personality="p", fate_sheet=sheet))


def test_handler_drives_dispatch_end_to_end():
    enc = StructuredEncounter(
        encounter_type="duel",
        category="combat",
        player_metric=EncounterMetric(name="p", threshold=10),
        opponent_metric=EncounterMetric(name="o", threshold=10),
        actors=[
            EncounterActor(name="Hero", role="lead", side="player"),
            EncounterActor(name="Thug", role="foe", side="opponent"),
        ],
    )
    snap = GameSnapshot(genre_slug="fate_test", characters=[_pc("Hero", {"Fight": 4})], encounter=enc)
    snap.npcs.append(_depleted_thug())

    # Minimal fake session: the handler reads _state, _session_data (snapshot,
    # genre_pack.rules.ruleset, player_id), and snapshot.player_seats.
    sd = SimpleNamespace(
        snapshot=snap,
        genre_pack=SimpleNamespace(rules=SimpleNamespace(ruleset="fate")),
        genre_slug="fate_test",
        world_slug="test_world",
        player_id="p1",
    )
    session = SimpleNamespace(_state=_State.Playing, _session_data=sd)

    msg = FateActionMessage(
        payload=FateActionPayload(request_id="r1", action="attack", skill="Fight", target="Thug"),
        player_id="p1",
    )

    out = asyncio.run(FATE_HANDLER.handle(session, msg))

    assert out == []  # broadcast/narration is F2/F3; the handler routes + mutates state
    assert enc.find_actor("Thug").withdrawn is True  # dispatch → exchange ran end-to-end
    assert enc.resolved is True
```

> While implementing, confirm `WebSocketSessionHandler._message_handler_for` is the resolver name (it is the method documented at the registry block, `websocket_session_handler.py:489`). If the registry is reached by a differently-named method, target that — the goal is a runtime registry lookup, not a source grep.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/server/test_fate_action_handler_wiring.py -n0 -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'sidequest.handlers.fate_action'`

- [ ] **Step 3: Create the handler**

Create `sidequest/handlers/fate_action.py`:

```python
"""FateActionHandler — handles FATE_ACTION messages (ADR-144 F1d).

Mirrors DiceThrowHandler's entry shape: state guard, resolve the rolling PC from
the seat map, resolve the bound ruleset, and route to ``dispatch_fate_action``
(which isinstance-gates to the Fate engine). Broadcast/narration re-entry is F2/F3
— this handler routes the action and mutates engine state; it returns [].
"""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING

from sidequest.server.session_handler import _State
from sidequest.server.session_helpers import _error_msg

if TYPE_CHECKING:
    from sidequest.protocol import GameMessage
    from sidequest.server.websocket_session_handler import WebSocketSessionHandler

logger = logging.getLogger(__name__)


class FateActionHandler:
    """Resolve a FATE_ACTION from the acting player onto the Fate exchange."""

    async def handle(
        self,
        session: WebSocketSessionHandler,
        msg: GameMessage,
    ) -> list[object]:
        from sidequest.game.ruleset import get_ruleset_module
        from sidequest.server.dispatch.fate_conflict import (
            FateConflictError,
            dispatch_fate_action,
        )

        if session._state != _State.Playing:
            logger.info(
                "session.message_rejected_unbound type=FATE_ACTION state=%s",
                session._state.name,
            )
            return [
                _error_msg(
                    "Cannot process FATE_ACTION: not in Playing state",
                    code="session_unbound",
                )
            ]
        if session._session_data is None:
            return [_error_msg("Internal error: session data missing")]

        sd = session._session_data
        payload = msg.payload  # type: ignore[attr-defined]
        acting_player_id = getattr(msg, "player_id", "") or sd.player_id
        snapshot = sd.snapshot
        encounter = snapshot.encounter

        # Resolve the acting PC from the seat map (MP) then the solo fallback —
        # mirrors DiceThrowHandler so a multi-PC Fate table attributes the action
        # to whoever sent it, not characters[0].
        acting_pc_name = (
            snapshot.player_seats.get(acting_player_id) if snapshot.player_seats else None
        )
        if acting_pc_name is not None:
            character = next(
                (c for c in snapshot.characters if c.core.name == acting_pc_name), None
            )
        else:
            character = snapshot.characters[0] if snapshot.characters else None
        if character is None:
            return [_error_msg("FATE_ACTION: no character to act", code="fate_no_actor")]

        ruleset = get_ruleset_module(sd.genre_pack.rules.ruleset)
        try:
            dispatch_fate_action(
                payload=payload,
                actor_name=character.core.name,
                encounter=encounter,
                ruleset=ruleset,
                snapshot=snapshot,
                rng=random,
                round_number=snapshot.turn_manager.interaction,
            )
        except FateConflictError as exc:
            logger.warning("fate.dispatch_error error=%s", exc)
            return [_error_msg(f"FATE_ACTION rejected: {exc}", code="fate_dispatch_error")]
        return []


HANDLER = FateActionHandler()
```

> `random` (the module) is the `rng` passed in production (matches `dispatch_dice_throw`, which passes `random`). `snapshot.turn_manager.interaction` is the round number the dice handler uses (`dice_throw.py:312`).

- [ ] **Step 4: Register the handler**

In `sidequest/server/websocket_session_handler.py`, in the lazy `_MESSAGE_HANDLERS` builder (around line 489–516):

Add the import alongside the other handler imports:

```python
            from sidequest.handlers.fate_action import HANDLER as FATE_ACTION_HANDLER
```

Add the registry entry (after the `"DICE_THROW": DICE_THROW_HANDLER,` line):

```python
                "FATE_ACTION": FATE_ACTION_HANDLER,
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/server/test_fate_action_handler_wiring.py -n0 -q`
Expected: PASS (registry membership + handler end-to-end)

- [ ] **Step 6: Commit**

```bash
git add sidequest/handlers/fate_action.py sidequest/server/websocket_session_handler.py tests/server/test_fate_action_handler_wiring.py
git commit -m "feat(fate): FateActionHandler + FATE_ACTION registry wiring (ADR-144 F1d)"
```

---

## Task 4: Gate — lint, format, types, suites (+ native/WN untouched)

**Files:** none (verification only)

- [ ] **Step 1: Lint the changed files (scoped)**

Run: `uv run ruff check sidequest/protocol/enums.py sidequest/protocol/fate.py sidequest/protocol/messages.py sidequest/server/dispatch/fate_conflict.py sidequest/handlers/fate_action.py sidequest/server/websocket_session_handler.py tests/protocol/test_fate_action_message.py tests/server/dispatch/test_fate_dispatch_routing.py tests/server/test_fate_action_handler_wiring.py`
Expected: `All checks passed!`

- [ ] **Step 2: Format the changed files (scoped)**

Run: `uv run ruff format sidequest/protocol/enums.py sidequest/protocol/fate.py sidequest/protocol/messages.py sidequest/server/dispatch/fate_conflict.py sidequest/handlers/fate_action.py sidequest/server/websocket_session_handler.py tests/protocol/test_fate_action_message.py tests/server/dispatch/test_fate_dispatch_routing.py tests/server/test_fate_action_handler_wiring.py`
Expected: unchanged or reformatted in place (commit any reformat).

- [ ] **Step 3: Type check**

Run: `uv run pyright sidequest/protocol/fate.py sidequest/protocol/messages.py sidequest/server/dispatch/fate_conflict.py sidequest/handlers/fate_action.py`
Expected: `0 errors`

- [ ] **Step 4: Run the F1d + full fate suites**

Run: `uv run pytest tests/protocol/test_fate_action_message.py tests/server/dispatch/test_fate_dispatch_routing.py tests/server/test_fate_action_handler_wiring.py tests/server/dispatch/test_fate_conflict.py tests/game/ruleset/ tests/telemetry/test_routing_completeness.py -n0 -q`
Expected: PASS — the whole Fate stack (F1a–F1d) green, routing lint green.

- [ ] **Step 5: Prove native/WN dispatch is untouched**

Run: `uv run pytest tests/integration/test_102_4_wn_sealed_round.py tests/protocol/ -n0 -q`
Expected: PASS — WN combat still routes through `dispatch_dice_throw`; the protocol union parses every existing message type. The Fate channel is purely additive.

- [ ] **Step 6: Commit any fixups**

```bash
git add -p
git commit -m "chore(fate): lint/format/type fixups (ADR-144 F1d)"
```

---

## Self-review (done against the spec)

- **Spec §4.1–§4.2 routing:** dispatch selects the Fate engine via `isinstance(ruleset, FateRulesetModule)` — Task 2 — exactly as `dispatch_dice_throw` gates WN on `WithoutNumberRulesetModule`. ✓
- **Non-shoehorn (handoff):** Fate gets its own `FATE_ACTION` message + payload + handler rather than overloading `DiceThrowPayload`'s beat+d20 shape — Task 1/3. ✓
- **Native/WN untouched (handoff):** `DICE_THROW` → `dispatch_dice_throw` unchanged; the Fate channel is additive (new enum value, new union variant, new handler entry); WN round suite passes — Task 4 Step 5. ✓
- **End-to-end wiring (handoff + server CLAUDE.md):** OTEL-span assertion through the real registry (`get_ruleset_module("fate")` → exchange `fate.exchange.resolved`) — Task 2; runtime registry membership (`FATE_ACTION` → `FateActionHandler`) — Task 3; handler-drives-dispatch behavior test (encounter resolves) — Task 3. No source-text greps. ✓
- **No Silent Fallbacks:** a `FATE_ACTION` under a non-Fate ruleset, an unresolved/absent encounter, an unseated actor, or an actor with no Fate sheet all fail loud (`FateConflictError`) — Task 2; the handler surfaces it as a typed client error. ✓
- **OTEL coverage:** the attacker's commit roll emits `fate.action_resolved` (F1a); the exchange emits `fate.exchange.*` (F1c); concede emits `fate.conceded` (F1c) — all reachable through the dispatch entry. ✓
- **Placeholder scan:** none — every code/command step is concrete; the two implementation notes (registry-method name, `Npc` location) point Dev at the real symbol to confirm, not at a TBD.
- **Type consistency:** `FateActionPayload`, `FateActionMessage`, `MessageType.FATE_ACTION`, `dispatch_fate_action`, `FateDispatchResult`, `FateActionHandler`, `HANDLER` are named identically across tasks; `dispatch_fate_action` reuses F1c's `seal_fate_commit` / `fate_barrier_closed` / `run_fate_exchange` / `concede_in_conflict` / `FateConflictError` / `FateExchangeResult` verbatim. ✓
- **Out of F1d scope (correct):** the narrator action-classifier + opponent AI (F2), the UI surfaces + 4dF overlay (F3), the four packs' content + `ruleset: fate` binding (F4), native removal + seam re-cut (F5).
```
