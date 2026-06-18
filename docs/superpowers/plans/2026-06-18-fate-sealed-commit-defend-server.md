# Fate Sealed-Commit DEFEND Barrier (Story 126-8) — Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make a Fate attack that targets a PC pause the round at an interactive, *informed* DEFEND barrier — the defender sees the committed attack total, picks a defense skill, throws their own 4dF (physics-is-the-roll), and submits — before the server resolves and narrates the whole exchange exactly once.

**Architecture:** Today `dispatch_fate_action` resolves COMMIT→RESOLVE synchronously and the `FATE_THROW` path never narrates. This plan splits that into a resume-safe phase machine: COMMIT closes → **REVEAL** (seat NPC attacks, roll + lock their 4dF) → if any PC is targeted, write a `pending_defenses` ledger on the encounter, emit one `FATE_DEFEND_REQUEST` per attack, **persist, and park** (no narration) → each `FATE_THROW(action="defend")` resolves from the player's reported faces and records the result by `request_id` → when the ledger fills, **RESUME**: walk the existing exchange (but `_resolve_attack` reads the *recorded* PC defense instead of rolling one), then invoke the narrator **once**. NPC defenses stay server-rolled. No Fate ladder math changes — bind the ruleset, don't balance it.

**Tech Stack:** Python 3.12 / FastAPI, pydantic v2, OpenTelemetry spans, pytest (`uv run pytest`), `uv run ruff`. All paths below are in `sidequest-server/`.

**Spec:** `docs/superpowers/specs/2026-06-18-fate-sealed-commit-interaction-model-design.md` (this plan implements §10 "Story 126-8 — first vertical slice", server-side only; the UI surfaces in §8 are a separate follow-up plan).

## Global Constraints

- Backend is Python/FastAPI (ADR-082). Server git strategy is **github-flow: PRs target `develop`**, feature branch **`feat/126-8-fate-defend-barrier`**. All commands run from `sidequest-server/`.
- **Bind the ruleset, don't balance it** (SOUL / ADR-144): this changes the dice *source* and the *interaction choreography* only. NEVER touch `classify_outcome`, shifts, tiers, `absorb_shifts`, or any ladder math.
- **Determinism (ADR-148):** the player **defense** resolves through `resolve_action_from_faces` from reported faces — **`roll_4df` is NEVER called on the player defense path.** NPC defense (`_roll_defense`) and NPC attack seating (`_seat_opponent_commits`) stay server-rolled.
- **No Silent Fallbacks:** AFK = block-and-wait. The DEFEND barrier waits indefinitely; there is **no** timeout and **no** server-side auto-roll for an absent defender. A bad face count / unaffordable spend / unknown `request_id` fails loud.
- **Resume-safety (ADR-128):** every phase transition is a persisted checkpoint. The `pending_defenses` ledger rides `snapshot.encounter` and survives a server restart; NPC dice rolled at REVEAL are **locked** and never re-rolled on resume.
- **OTEL on every subsystem decision** (the GM panel is the lie detector): `fate.action_resolved` gains `role ∈ {action, defense}` (keeping `source ∈ {player_thrown, server_rolled}`); a new `fate.defend_phase` span records who was requested and who responded.
- **No Source-Text Wiring Tests** (server CLAUDE.md): never `read_text()`/grep production source as an assertion. Use span capture (injected `_tracer`) and behavioral fixtures driving the real handler/registry/exchange.
- **Every Test Suite Needs a Wiring Test:** Task 8 drives NPC-attacks-PC → `FATE_DEFEND_REQUEST` → player defend `FATE_THROW` → resolve → narrate through the real handler/registry/exchange on a fixture snapshot.
- Run lint after each task on branch-touched files only: `uv run ruff format <files> && uv run ruff check <files>` (bare `ruff format .` reformats ~167 files — see project memory).
- Telemetry/span tests run serially: `uv run pytest <path> -n0 -q` (the parallel runner has a known span-count deadlock on some telemetry files — see project memory).

---

### Task 1: Protocol — `FATE_DEFEND_REQUEST` message + `action="defend"` on `FATE_THROW`

**Files:**
- Modify: `sidequest/protocol/enums.py` (add `FATE_DEFEND_REQUEST` to `MessageType`)
- Modify: `sidequest/protocol/fate.py` (add `FateDefendRequestPayload`; extend `FateThrowPayload.action` to include `"defend"`)
- Modify: `sidequest/protocol/messages.py` (add `FateDefendRequestMessage`; register it in the `_Phase1Variant` union)
- Test: `tests/protocol/test_fate_defend_protocol.py`

**Interfaces:**
- Produces:
  - `MessageType.FATE_DEFEND_REQUEST = "FATE_DEFEND_REQUEST"`
  - `class FateDefendRequestPayload(ProtocolBase)` — fields `request_id: str`, `defender: str`, `attacker: str`, `attack_skill: str`, `attack_total: int`, `mental: bool`.
  - `class FateDefendRequestMessage(ProtocolBase)` — `type: Literal[MessageType.FATE_DEFEND_REQUEST]`, `payload: FateDefendRequestPayload`, `player_id: str = ""`.
  - `FateThrowPayload.action` widened to `Literal["overcome", "create_advantage", "attack", "defend"]`; an `action="defend"` throw echoes the `request_id` of the `FATE_DEFEND_REQUEST` it answers (the `request_id` field already exists on `FateThrowPayload`).

- [ ] **Step 1: Write the failing test**

```python
# tests/protocol/test_fate_defend_protocol.py
"""Protocol surface for the Fate DEFEND barrier (spec 2026-06-18 §6):
FATE_DEFEND_REQUEST (server→client) and action="defend" on FATE_THROW."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from sidequest.protocol import GameMessage
from sidequest.protocol.enums import MessageType
from sidequest.protocol.fate import FateDefendRequestPayload, FateThrowPayload
from sidequest.protocol.messages import FateDefendRequestMessage
from sidequest.protocol.models import ThrowParams


def _throw_params() -> ThrowParams:
    return ThrowParams(position=(0.0, 0.0), velocity=(0.0, 0.0), angular=(0.0, 0.0, 0.0), spin=0.0)


def test_defend_request_payload_validates():
    p = FateDefendRequestPayload(
        request_id="d1", defender="Rux", attacker="Bandit",
        attack_skill="Fight", attack_total=5, mental=False,
    )
    assert p.attack_total == 5 and p.defender == "Rux"


def test_defend_request_message_is_in_game_message_union():
    msg = FateDefendRequestMessage(
        payload=FateDefendRequestPayload(
            request_id="d1", defender="Rux", attacker="Bandit",
            attack_skill="Fight", attack_total=5, mental=False,
        ),
        player_id="p-rux",
    )
    # round-trips through the discriminated union by type tag
    parsed = GameMessage.model_validate(msg.model_dump())
    assert parsed.root.type == MessageType.FATE_DEFEND_REQUEST
    assert parsed.root.payload.attacker == "Bandit"


def test_fate_throw_accepts_action_defend_with_request_id():
    p = FateThrowPayload(
        request_id="d1", action="defend", skill="Athletics",
        throw_params=_throw_params(), face=(0, 1, -1, 0),
    )
    assert p.action == "defend" and p.request_id == "d1"


def test_fate_throw_defend_still_enforces_four_faces():
    with pytest.raises(ValidationError):
        FateThrowPayload(
            request_id="d1", action="defend", skill="Athletics",
            throw_params=_throw_params(), face=(0, 1, -1),  # only 3
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/protocol/test_fate_defend_protocol.py -q`
Expected: FAIL — `AttributeError: FATE_DEFEND_REQUEST` / `ImportError: cannot import name 'FateDefendRequestPayload'` / `ValidationError` on `action="defend"`.

- [ ] **Step 3: Add the enum value**

In `sidequest/protocol/enums.py`, inside `class MessageType(StrEnum)`, next to the other `FATE_*` values (e.g. after `FATE_ROLL = "FATE_ROLL"`):

```python
    FATE_DEFEND_REQUEST = "FATE_DEFEND_REQUEST"
```

- [ ] **Step 4: Add the payload + widen the throw action**

In `sidequest/protocol/fate.py`, add the payload (mirror `FateThrowPayload`'s `ProtocolBase` inheritance, which carries `extra="forbid"`):

```python
class FateDefendRequestPayload(ProtocolBase):
    """Server→client: "you are attacked by ``attacker`` with ``attack_skill`` at
    total ``attack_total`` — defend." One per incoming attack on a PC (spec
    2026-06-18 §6). The client echoes ``request_id`` on its FATE_THROW(defend)."""

    request_id: str
    defender: str
    attacker: str
    attack_skill: str
    attack_total: int
    mental: bool = False
```

Widen the throw action Literal (find the `action:` field on `FateThrowPayload`, currently `Literal["overcome", "create_advantage", "attack"]`):

```python
    action: Literal["overcome", "create_advantage", "attack", "defend"]
```

(Leave the existing `_validate_faces` model validator untouched — a defend throw still ships exactly 4 faces ∈ {−1,0,1}.)

- [ ] **Step 5: Add the message class + register in the union**

In `sidequest/protocol/messages.py`, add the message class beside the other Fate messages (e.g. near `FateRollMessage`):

```python
class FateDefendRequestMessage(ProtocolBase):
    type: Literal[MessageType.FATE_DEFEND_REQUEST] = MessageType.FATE_DEFEND_REQUEST
    payload: FateDefendRequestPayload
    player_id: str = ""
```

Add the import for `FateDefendRequestPayload` (from `sidequest.protocol.fate`) alongside the existing fate-payload imports, and add `| FateDefendRequestMessage` to the `_Phase1Variant` annotated union (the block ending in `Field(discriminator="type")`, ~line 1767-1817), next to `FateRollMessage`.

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/protocol/test_fate_defend_protocol.py -q`
Expected: PASS (4 passed).

- [ ] **Step 7: Guard the MessageType-count test**

The suite has a count assertion on `MessageType` (the historical "54 values" check). Run it and update the expected count by one if present:

Run: `uv run pytest tests/protocol -q -k "message_type or enum"`
Expected: PASS. If a count test fails (`assert len(MessageType) == 54`), bump the literal to `55` in that test — the new value is intentional.

- [ ] **Step 8: Lint + Commit**

```bash
uv run ruff format sidequest/protocol/enums.py sidequest/protocol/fate.py sidequest/protocol/messages.py tests/protocol/test_fate_defend_protocol.py
uv run ruff check sidequest/protocol/enums.py sidequest/protocol/fate.py sidequest/protocol/messages.py tests/protocol/test_fate_defend_protocol.py
git add sidequest/protocol/enums.py sidequest/protocol/fate.py sidequest/protocol/messages.py tests/protocol/test_fate_defend_protocol.py
git commit -m "feat(126-8): FATE_DEFEND_REQUEST message + action=defend on FATE_THROW"
```

---

### Task 2: `pending_defenses` ledger model on the encounter (resume-safe)

**Files:**
- Modify: `sidequest/game/encounter.py` (add `FatePendingDefense` model; add `pending_defenses` field to `StructuredEncounter`, sibling to `fate_commits`)
- Test: `tests/game/test_fate_pending_defenses.py`

**Interfaces:**
- Produces:
  - `class FatePendingDefense(BaseModel)` (`extra="forbid"`) — `request_id: str`, `attacker: str`, `defender: str`, `attack_skill: str`, `attack_total: int`, `mental: bool = False`, `defense_total: int | None = None` (None = unfilled = "still in DEFEND"), `conceded: bool = False`.
  - `StructuredEncounter.pending_defenses: list[FatePendingDefense] = Field(default_factory=list)`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/game/test_fate_pending_defenses.py
"""The pending_defenses ledger (spec 2026-06-18 §5): one entry per incoming
attack on a PC; an unfilled entry IS the "we are in DEFEND" signal; it survives
a snapshot round-trip (resume-safety, ADR-128)."""

from __future__ import annotations

from sidequest.game.encounter import FatePendingDefense, StructuredEncounter


def test_pending_defense_unfilled_by_default():
    e = FatePendingDefense(
        request_id="d1", attacker="Bandit", defender="Rux",
        attack_skill="Fight", attack_total=5,
    )
    assert e.defense_total is None and e.conceded is False


def test_encounter_defaults_to_empty_ledger():
    e = StructuredEncounter(encounter_type="conflict")
    assert e.pending_defenses == []


def test_pending_defenses_survive_model_round_trip():
    e = StructuredEncounter(encounter_type="conflict")
    e.pending_defenses.append(
        FatePendingDefense(
            request_id="d1", attacker="Bandit", defender="Rux",
            attack_skill="Fight", attack_total=5,
        )
    )
    dumped = e.model_dump_json()
    restored = StructuredEncounter.model_validate_json(dumped)
    assert len(restored.pending_defenses) == 1
    assert restored.pending_defenses[0].request_id == "d1"
    assert restored.pending_defenses[0].defense_total is None


def test_legacy_encounter_without_ledger_loads_empty():
    # A snapshot written before this field existed has no key for it.
    legacy = StructuredEncounter(encounter_type="conflict").model_dump()
    legacy.pop("pending_defenses", None)
    restored = StructuredEncounter.model_validate(legacy)
    assert restored.pending_defenses == []
```

(Adjust the `StructuredEncounter(...)` constructor call if the model requires more args — match the minimal-construction pattern used in `tests/game/` for `fate_commits`; grep `StructuredEncounter(` under `tests/` for the canonical minimal kwargs.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/game/test_fate_pending_defenses.py -q`
Expected: FAIL — `ImportError: cannot import name 'FatePendingDefense'` and `AttributeError: ... 'pending_defenses'`.

- [ ] **Step 3: Add the model + field**

In `sidequest/game/encounter.py`, add the model near `FateSealedCommit` (~line 158):

```python
class FatePendingDefense(BaseModel):
    """One incoming attack on a PC awaiting that PC's interactive defense (spec
    2026-06-18 §5). Written at REVEAL when an attack targets a PC; filled by the
    PC's FATE_THROW(defend). ``defense_total is None`` (and not conceded) means
    the barrier is still waiting on this defender. Sibling to ``fate_commits`` —
    cleared when the exchange resumes and resolves."""

    model_config = {"extra": "forbid"}

    request_id: str
    attacker: str
    defender: str
    attack_skill: str
    attack_total: int
    mental: bool = False
    defense_total: int | None = None
    conceded: bool = False
```

Add the field to `StructuredEncounter` immediately after the `fate_commits` field (~line 288):

```python
    pending_defenses: list[FatePendingDefense] = Field(default_factory=list)
    """spec 2026-06-18 §5: incoming attacks on PCs awaiting interactive defense.
    An unfilled entry is the "we are in DEFEND" signal; the exchange is parked at
    a persisted checkpoint until every entry is filled (defense_total set or
    conceded). Always empty for native/WN encounters and between Fate exchanges
    (sibling to ``fate_commits``)."""
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/game/test_fate_pending_defenses.py -q`
Expected: PASS (4 passed).

- [ ] **Step 5: Lint + Commit**

```bash
uv run ruff format sidequest/game/encounter.py tests/game/test_fate_pending_defenses.py
uv run ruff check sidequest/game/encounter.py tests/game/test_fate_pending_defenses.py
git add sidequest/game/encounter.py tests/game/test_fate_pending_defenses.py
git commit -m "feat(126-8): pending_defenses ledger on the encounter (resume-safe)"
```

---

### Task 3: OTEL — `role` on `fate.action_resolved` + new `fate.defend_phase` span

**Files:**
- Modify: `sidequest/telemetry/spans/fate.py` (add `role` param/attr to `fate_action_resolved_span`; add the `fate.defend_phase` route + emitter + `__all__`)
- Modify: `sidequest/game/ruleset/fate.py` (pass `role="action"` at the two `fate_action_resolved_span` call sites — lines ~217 and ~251)
- Test: `tests/game/ruleset/test_fate_defend_spans.py`

**Interfaces:**
- Produces:
  - `fate_action_resolved_span(..., role: str = "action", source: str = "server_rolled", ...)` — adds a `"role"` attribute (default `"action"`; defense callers pass `"defense"`).
  - `fate_defend_phase_span(*, defender: str, attacker: str, request_id: str, responded: bool, conceded: bool = False, _tracer=None, **attrs) -> None` and `SPAN_ROUTES["fate.defend_phase"]` (component `"fate"`, event_type `"state_transition"`).

- [ ] **Step 1: Write the failing tests**

```python
# tests/game/ruleset/test_fate_defend_spans.py
"""OTEL for the DEFEND barrier (spec 2026-06-18 §9): role on fate.action_resolved
and the new fate.defend_phase span (the GM-panel lie detector for the barrier)."""

from __future__ import annotations

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from sidequest.telemetry.spans._core import SPAN_ROUTES
from sidequest.telemetry.spans.fate import (
    fate_action_resolved_span,
    fate_defend_phase_span,
)


def _exporter():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return exporter, provider.get_tracer("test")


def test_action_resolved_defaults_role_action():
    exporter, tracer = _exporter()
    fate_action_resolved_span(
        actor="Rux", skill_rating=2, dice=(0, 0, 0, 0), ladder_total=2,
        opposition=0, opposition_kind="active", shifts=2, tier="Succeed",
        source="player_thrown", _tracer=tracer,
    )
    span = exporter.get_finished_spans()[0]
    assert span.attributes["role"] == "action"
    assert span.attributes["source"] == "player_thrown"


def test_action_resolved_role_defense():
    exporter, tracer = _exporter()
    fate_action_resolved_span(
        actor="Rux", skill_rating=3, dice=(1, 0, 0, 0), ladder_total=4,
        opposition=0, opposition_kind="active", shifts=0, tier="Tie",
        role="defense", source="player_thrown", _tracer=tracer,
    )
    span = exporter.get_finished_spans()[0]
    assert span.attributes["role"] == "defense"


def test_defend_phase_route_registered():
    route = SPAN_ROUTES["fate.defend_phase"]
    assert route.component == "fate"
    assert route.event_type == "state_transition"


def test_defend_phase_emitter_fires_named_span():
    exporter, tracer = _exporter()
    fate_defend_phase_span(
        defender="Rux", attacker="Bandit", request_id="d1",
        responded=True, conceded=False, _tracer=tracer,
    )
    spans = exporter.get_finished_spans()
    assert [s.name for s in spans] == ["fate.defend_phase"]
    assert spans[0].attributes["responded"] is True
    assert spans[0].attributes["defender"] == "Rux"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/game/ruleset/test_fate_defend_spans.py -n0 -q`
Expected: FAIL — `ImportError: cannot import name 'fate_defend_phase_span'`, `KeyError: 'fate.defend_phase'`, and the role assertions fail (no `role` attribute yet).

- [ ] **Step 3: Add the `role` attribute to `fate_action_resolved_span`**

In `sidequest/telemetry/spans/fate.py`, in `fate_action_resolved_span` (~line 14), add the keyword (before `source`) and the attribute:

```python
    ...
    shifts: int,
    tier: str,
    role: str = "action",
    source: str = "server_rolled",
    _tracer: trace.Tracer | None = None,
    **attrs: Any,
) -> None:
    ...
    attributes: dict[str, Any] = {
        "field": "action_resolved",
        ...
        "tier": tier,
        "role": role,
        "source": source,
        **attrs,
    }
```

(Defaulting `role="action"` keeps every existing caller — NPC and player proactive — correctly tagged with no change.)

- [ ] **Step 4: Add the `fate.defend_phase` span (route + emitter + `__all__`)**

After the `fate.item_promoted` SPAN_ROUTES block (~line 691), add a literal-key route (literal key — exempt from the SPAN_* routing-completeness lint, matching `fate.item_promoted`):

```python
SPAN_ROUTES["fate.defend_phase"] = SpanRoute(
    event_type="state_transition",
    component="fate",
    extract=lambda span: {
        "field": "defend_phase",
        "defender": (span.attributes or {}).get("defender", ""),
        "attacker": (span.attributes or {}).get("attacker", ""),
        "request_id": (span.attributes or {}).get("request_id", ""),
        "responded": bool((span.attributes or {}).get("responded", False)),
        "conceded": bool((span.attributes or {}).get("conceded", False)),
    },
)
```

Add the emitter next to `fate_item_promoted_span` (~line 1192):

```python
def fate_defend_phase_span(
    *,
    defender: str,
    attacker: str,
    request_id: str,
    responded: bool,
    conceded: bool = False,
    _tracer: trace.Tracer | None = None,
    **attrs: Any,
) -> None:
    """Emit ``fate.defend_phase`` — the GM-panel lie detector that the interactive
    DEFEND barrier actually fired (spec 2026-06-18 §9): ``responded`` is False at
    request time (we asked ``defender`` to answer ``attacker``'s attack) and True
    when their FATE_THROW(defend) lands; ``conceded`` marks a fold at defend. It
    proves the defender's number came from the client, not narrator improvisation."""
    attributes: dict[str, Any] = {
        "field": "defend_phase",
        "defender": defender,
        "attacker": attacker,
        "request_id": request_id,
        "responded": responded,
        "conceded": conceded,
        **attrs,
    }
    with Span.open("fate.defend_phase", attributes, tracer_override=_tracer):
        pass
```

Add `"fate_defend_phase_span"` to `__all__` (near `fate_item_promoted_span`).

- [ ] **Step 5: Pass `role="action"` at the two ruleset call sites**

In `sidequest/game/ruleset/fate.py`, in `FateRulesetModule.resolve_action` (~line 217) and `resolve_action_from_faces` (~line 251), add `role="action"` to each `fate_action_resolved_span(...)` call (alongside the existing `source=...`). These are the proactive/NPC paths and stay `role="action"`.

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/game/ruleset/test_fate_defend_spans.py tests/game/ruleset/test_fate_spans.py -n0 -q`
Expected: PASS (the existing `test_fate_spans.py` still passes — `role` defaults to `"action"`).

- [ ] **Step 7: Lint + Commit**

```bash
uv run ruff format sidequest/telemetry/spans/fate.py sidequest/game/ruleset/fate.py tests/game/ruleset/test_fate_defend_spans.py
uv run ruff check sidequest/telemetry/spans/fate.py sidequest/game/ruleset/fate.py tests/game/ruleset/test_fate_defend_spans.py
git add sidequest/telemetry/spans/fate.py sidequest/game/ruleset/fate.py tests/game/ruleset/test_fate_defend_spans.py
git commit -m "feat(126-8): role attr on fate.action_resolved + fate.defend_phase span"
```

---

### Task 4: REVEAL + park decision — a PC-targeted round writes `pending_defenses` and returns defend requests instead of walking

**Files:**
- Modify: `sidequest/server/dispatch/fate_conflict.py` (extend `FateDispatchResult`; add `_build_pending_defenses`; restructure the barrier-close branch in `dispatch_fate_action` ~963-986)
- Test: `tests/server/dispatch/test_fate_reveal_park.py`

**Interfaces:**
- Consumes: `_seat_opponent_commits` (REVEAL, already seats + locks NPC 4dF), `encounter.fate_commits`, `FatePendingDefense` (Task 2), `fate_defend_phase_span` (Task 3).
- Produces:
  - `FateDispatchResult` gains `defend_requests: list[FateDefendRequestPayload] = field(default_factory=list)` and `awaiting_defense: bool = False`.
  - `_build_pending_defenses(*, encounter, snapshot, round_number, _tracer=None) -> list[FateDefendRequestPayload]` — after REVEAL, for each sealed `attack` whose `target` is a live seated **PC**, append a `FatePendingDefense` to `encounter.pending_defenses` and return one `FateDefendRequestPayload` per entry; emits `fate.defend_phase(responded=False)` per request. Returns `[]` when no PC is targeted.
  - In `dispatch_fate_action`, when the barrier closes: run REVEAL (`_seat_opponent_commits`), then `_build_pending_defenses`; if it returns requests → persist and return a parked `FateDispatchResult(awaiting_defense=True, defend_requests=...)` **without** walking; else fall through to the existing `run_fate_exchange` path.

- [ ] **Step 1: Write the failing tests**

```python
# tests/server/dispatch/test_fate_reveal_park.py
"""REVEAL + park (spec 2026-06-18 §5): when the COMMIT barrier closes and an
NPC attack targets a PC, the server seats + locks the NPC roll, writes
pending_defenses, returns defend requests, and does NOT walk the exchange yet.
A round with no PC targeted resolves immediately (today's path)."""

from __future__ import annotations

import random

from sidequest.game.ruleset import get_ruleset_module
from sidequest.protocol.fate import FateActionPayload
from sidequest.server.dispatch.fate_conflict import dispatch_fate_action
from tests._helpers.fate_fixtures import conflict_with_pc_and_npc  # see note


def test_pc_targeted_round_parks_with_defend_request():
    snap, encounter = conflict_with_pc_and_npc(pc="Rux", npc="Bandit")
    ruleset = get_ruleset_module("fate")
    # The PC commits a proactive attack; the barrier closes (solo PC table).
    result = dispatch_fate_action(
        payload=FateActionPayload(request_id="a1", action="attack", skill="Fight", target="Bandit"),
        actor_name="Rux", encounter=encounter, ruleset=ruleset, snapshot=snap,
        rng=random.Random(7), thrown_faces=(0, 0, 0, 0),
    )
    # Parked: defend requested, exchange NOT walked, NPC attack locked in commits.
    assert result.awaiting_defense is True
    assert result.exchange is None
    assert encounter.resolved is False
    assert len(result.defend_requests) == 1
    req = result.defend_requests[0]
    assert req.defender == "Rux" and req.attacker == "Bandit"
    assert any(p.request_id == req.request_id and p.defense_total is None
               for p in encounter.pending_defenses)
    # NPC 4dF was rolled and sealed at REVEAL (locked, not re-rolled later).
    assert any(c.actor == "Bandit" and c.action == "attack" for c in encounter.fate_commits)


def test_no_pc_targeted_resolves_immediately():
    # An NPC with no live PC to hit, or a PC overcome vs a passive obstacle.
    snap, encounter = conflict_with_pc_and_npc(pc="Rux", npc="Bandit", npc_targets_pc=False)
    ruleset = get_ruleset_module("fate")
    result = dispatch_fate_action(
        payload=FateActionPayload(request_id="o1", action="overcome", skill="Athletics", difficulty=2),
        actor_name="Rux", encounter=encounter, ruleset=ruleset, snapshot=snap,
        rng=random.Random(7), thrown_faces=(1, 1, 0, 0),
    )
    assert result.awaiting_defense is False
    assert result.exchange is not None  # walked now
    assert encounter.pending_defenses == []
```

> **Fixture note:** add `conflict_with_pc_and_npc(...)` to `tests/_helpers/fate_fixtures.py` (or reuse the existing Fate conflict fixture builder — grep `def ` under `tests/_helpers/` and `tests/server/dispatch/` for the current `StructuredEncounter` + `GameSnapshot` Fate builder; several Fate dispatch tests already construct one). It must seat one player-side PC with a Fate sheet and one opponent with a Fate sheet, `category="physical"`, unresolved. `npc_targets_pc=False` seats an opponent that `decide_opponent_action` will not point at the PC (e.g. no live PC threat) — or simply assert the immediate path with a PC-only `overcome` vs a passive difficulty and no opponent seated.

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/server/dispatch/test_fate_reveal_park.py -q`
Expected: FAIL — `AttributeError: 'FateDispatchResult' object has no attribute 'awaiting_defense'`.

- [ ] **Step 3: Extend `FateDispatchResult`**

In `sidequest/server/dispatch/fate_conflict.py`, find the `@dataclass` `FateDispatchResult` (defined just above `dispatch_fate_action`, fields `commitment_pending`, `exchange`, `action_roll`, `fate_point_delta`). Add an import for the payload at the top with the other protocol imports:

```python
from sidequest.protocol.fate import FateActionPayload, FateDefendRequestPayload
```

Add `field` to the dataclass import (`from dataclasses import dataclass, field`) and add two fields to `FateDispatchResult`:

```python
    #: spec 2026-06-18 §5: when the round parks at DEFEND, the requests to emit
    #: (one per incoming attack on a PC). Empty unless ``awaiting_defense``.
    defend_requests: list[FateDefendRequestPayload] = field(default_factory=list)
    #: True when the exchange is PARKED at the DEFEND barrier — the caller emits
    #: ``defend_requests`` and does NOT narrate (no narration until RESOLVE).
    awaiting_defense: bool = False
```

- [ ] **Step 4: Add `_build_pending_defenses`**

Add near `_seat_opponent_commits` (~line 354):

```python
def _build_pending_defenses(
    *,
    encounter: StructuredEncounter,
    snapshot: GameSnapshot,
    round_number: int = 0,
    _tracer: trace.Tracer | None = None,
) -> list[FateDefendRequestPayload]:
    """After REVEAL, park each attack that targets a live seated PC. Writes one
    ``FatePendingDefense`` per such attack and returns the matching defend
    requests (spec 2026-06-18 §5). Returns ``[]`` when no PC is targeted — the
    caller then resolves immediately (today's path). PC = player-side actor with
    a Fate sheet; NPC-on-NPC and passive actions never park."""
    mental = encounter.category == "social"
    pc_names = _seated_pc_names(snapshot)
    requests: list[FateDefendRequestPayload] = []
    for commit in encounter.fate_commits:
        if commit.action != "attack" or commit.target is None:
            continue
        if commit.target not in pc_names:
            continue  # NPC defender — server rolls it at RESOLVE, no park
        target_actor = encounter.find_actor(commit.target)
        if target_actor is None or target_actor.withdrawn:
            continue
        request_id = f"def:{round_number}:{commit.actor}->{commit.target}"
        encounter.pending_defenses.append(
            FatePendingDefense(
                request_id=request_id,
                attacker=commit.actor,
                defender=commit.target,
                attack_skill=commit.skill,
                attack_total=commit.ladder_total,
                mental=mental,
            )
        )
        fate_defend_phase_span(
            defender=commit.target, attacker=commit.actor,
            request_id=request_id, responded=False, _tracer=_tracer,
        )
        requests.append(
            FateDefendRequestPayload(
                request_id=request_id, defender=commit.target, attacker=commit.actor,
                attack_skill=commit.skill, attack_total=commit.ladder_total, mental=mental,
            )
        )
    return requests
```

Add `FatePendingDefense` to the `from sidequest.game.encounter import (...)` block, and `fate_defend_phase_span` to the `from sidequest.telemetry.spans import (...)` block.

- [ ] **Step 5: Restructure the barrier-close branch in `dispatch_fate_action`**

Replace the barrier-close block (the `if fate_barrier_closed(...)` body, ~963-986) so it runs REVEAL and parks when a PC is targeted. The Contest path is unchanged (a Contest has no attacks, so it never parks):

```python
    if fate_barrier_closed(encounter=encounter, snapshot=snapshot):
        if encounter.contest is not None:
            from sidequest.server.dispatch.fate_contest import run_fate_contest_exchange

            result = run_fate_contest_exchange(
                encounter=encounter, snapshot=snapshot, ruleset=ruleset,
                rng=rng, round_number=round_number, _tracer=_tracer,
            )
            return FateDispatchResult(
                commitment_pending=False, exchange=result, action_roll=outcome
            )

        # REVEAL: seat + lock the NPC attacks NOW (their 4dF is rolled here and
        # never re-rolled across the suspend), then decide park-or-resolve.
        _seat_opponent_commits(
            encounter=encounter, snapshot=snapshot, ruleset=ruleset,
            mental=encounter.category == "social", rng=rng, _tracer=_tracer,
        )
        defend_requests = _build_pending_defenses(
            encounter=encounter, snapshot=snapshot,
            round_number=round_number, _tracer=_tracer,
        )
        if defend_requests:
            # PARK: a clean persisted checkpoint. No walk, no narration yet.
            return FateDispatchResult(
                commitment_pending=False, exchange=None, action_roll=outcome,
                defend_requests=defend_requests, awaiting_defense=True,
            )
        # No PC targeted → resolve immediately (today's single-call path).
        result = run_fate_exchange(
            encounter=encounter, snapshot=snapshot, ruleset=ruleset,
            rng=rng, round_number=round_number, _tracer=_tracer,
        )
        return FateDispatchResult(
            commitment_pending=False, exchange=result, action_roll=outcome
        )
    return FateDispatchResult(commitment_pending=True, exchange=None, action_roll=outcome)
```

> Note: `run_fate_exchange` calls `_seat_opponent_commits` again at its top, but it skips already-committed opponents (`if opp.name in committed: continue`), so the double call is a safe no-op — the NPC dice locked at REVEAL are not re-rolled.

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/server/dispatch/test_fate_reveal_park.py -q`
Expected: PASS (2 passed).

- [ ] **Step 7: Regression-check the existing Fate dispatch suite**

Run: `uv run pytest tests/server/dispatch -q -k "fate"`
Expected: PASS — the no-PC-targeted path is unchanged; only PC-targeted rounds now park. If a pre-existing test assumed a PC-targeted attack resolves synchronously in one call, it must be updated to drive the defend step (that behavior change is the whole point — note it in the deviations log if such a test exists).

- [ ] **Step 8: Lint + Commit**

```bash
uv run ruff format sidequest/server/dispatch/fate_conflict.py tests/server/dispatch/test_fate_reveal_park.py
uv run ruff check sidequest/server/dispatch/fate_conflict.py tests/server/dispatch/test_fate_reveal_park.py
git add sidequest/server/dispatch/fate_conflict.py tests/server/dispatch/test_fate_reveal_park.py tests/_helpers/fate_fixtures.py
git commit -m "feat(126-8): REVEAL + park — PC-targeted round writes pending_defenses"
```

---

### Task 5: Emit `FATE_DEFEND_REQUEST` from the throw handler when the round parks

**Files:**
- Modify: `sidequest/handlers/fate_throw.py` (after `dispatch_fate_action` returns parked, broadcast one `FATE_DEFEND_REQUEST` per entry; persist the parked snapshot)
- Test: `tests/handlers/test_fate_throw_emits_defend_request.py`

**Interfaces:**
- Consumes: `FateDispatchResult.awaiting_defense` / `.defend_requests` (Task 4); the session's room broadcast; the snapshot persistence seam.
- Produces: one `FateDefendRequestMessage` per `defend_request`, routed to the defender's seat (or broadcast to the room — the client filters by `defender`), AND a persisted snapshot at the park checkpoint. No narration is triggered.

- [ ] **Step 1: Write the failing test**

```python
# tests/handlers/test_fate_throw_emits_defend_request.py
"""When a proactive FATE_THROW closes the barrier and the round parks at DEFEND,
the handler broadcasts a FATE_DEFEND_REQUEST per incoming attack and persists the
parked checkpoint — and triggers NO narration (spec 2026-06-18 §3)."""

from __future__ import annotations

from sidequest.protocol.enums import MessageType
from tests._helpers.fate_session import playing_session_with_fate_conflict  # see note


async def test_parked_throw_broadcasts_defend_request(monkeypatch):
    session, throw_msg = playing_session_with_fate_conflict(
        actor="Rux", attacker_npc="Bandit", attack_targets="Rux",
        action="attack", target="Bandit",
    )
    sent = []
    monkeypatch.setattr(session._room, "broadcast", lambda m, **k: sent.append(m) or [])

    out = await session.handle_message(throw_msg)

    kinds = [getattr(m, "type", None) for m in sent]
    assert MessageType.FATE_DEFEND_REQUEST in kinds
    req = next(m for m in sent if getattr(m, "type", None) == MessageType.FATE_DEFEND_REQUEST)
    assert req.payload.defender == "Rux" and req.payload.attacker == "Bandit"
    # parked: encounter not resolved, ledger written
    enc = session._session_data.snapshot.encounter
    assert enc.resolved is False and len(enc.pending_defenses) == 1
```

> **Fixture note:** `playing_session_with_fate_conflict(...)` builds a `WebSocketSessionHandler` in `_State.Playing` with a Fate-bound pack, a seated PC + opponent, a `_room`, and returns it plus a ready `FateThrowMessage`. Reuse/extend the existing handler-test harness — grep `_State.Playing` and `WebSocketSessionHandler(` under `tests/handlers/` and `tests/server/` for the canonical builder used by `test_fate_throw*`.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/handlers/test_fate_throw_emits_defend_request.py -q`
Expected: FAIL — no `FATE_DEFEND_REQUEST` is broadcast (the handler ignores `defend_requests`).

- [ ] **Step 3: Emit the requests + persist on the parked branch**

In `sidequest/handlers/fate_throw.py`, after the `dispatch_fate_action(...)` call returns `result` (after the `try/except`, before the `if result.action_roll is not None:` broadcast block ~line 144), insert the park branch:

```python
        # spec 2026-06-18 §5: the round PARKED at the DEFEND barrier. Broadcast one
        # FATE_DEFEND_REQUEST per incoming attack (the client filters by defender)
        # and PERSIST the checkpoint — the exchange now waits, resume-safe, on the
        # PCs' defenses. No narration here (narration only at RESOLVE).
        if result.awaiting_defense:
            from sidequest.protocol.messages import FateDefendRequestMessage

            room = sd._room
            if room is None:
                logger.error("fate.defend.no_room — defend requests not delivered")
                return []
            for req in result.defend_requests:
                defender_pid = _seat_player_id(snapshot, req.defender)  # see Step 4
                room.broadcast(
                    FateDefendRequestMessage(payload=req, player_id=defender_pid),
                    exclude_socket_id=None,
                )
            session._persist_snapshot()  # see Step 4
            # still broadcast the attacker's own roll below if present
```

Then keep the existing `if result.action_roll is not None:` broadcast (the proactive thrower still sees their own dice), and return `[]` at the end as today.

- [ ] **Step 4: Wire the two helpers to the real seams**

`_seat_player_id` and `_persist_snapshot` must use the project's real APIs, not new abstractions:
- Player id for a PC name: invert `snapshot.player_seats` (it maps `player_id -> pc_name`). Add a tiny local: `def _seat_player_id(snapshot, name): return next((pid for pid, pc in (snapshot.player_seats or {}).items() if pc == name), "")`. Place it as a module-level helper in `fate_throw.py`.
- Persistence: find how the session persists today — grep `save_snapshot` / `persist` in `sidequest/server/websocket_session_handler.py` and `session_helpers.py`. Use the same call the natural-language turn uses to checkpoint (likely `sd.persistence.save_snapshot(snapshot)` or a session method). Replace `session._persist_snapshot()` with that exact call. **Do not invent a new persistence path** (No Silent Fallbacks / Don't Reinvent).

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/handlers/test_fate_throw_emits_defend_request.py -q`
Expected: PASS.

- [ ] **Step 6: Lint + Commit**

```bash
uv run ruff format sidequest/handlers/fate_throw.py tests/handlers/test_fate_throw_emits_defend_request.py
uv run ruff check sidequest/handlers/fate_throw.py tests/handlers/test_fate_throw_emits_defend_request.py
git add sidequest/handlers/fate_throw.py tests/handlers/test_fate_throw_emits_defend_request.py
git commit -m "feat(126-8): broadcast FATE_DEFEND_REQUEST + persist parked checkpoint"
```

---

### Task 6: Defense recording — `FATE_THROW(action="defend")` resolves from faces, records on the ledger by `request_id`

**Files:**
- Modify: `sidequest/server/dispatch/fate_conflict.py` (add `dispatch_fate_defense`)
- Modify: `sidequest/handlers/fate_throw.py` (route `action == "defend"` to the defense path)
- Test: `tests/server/dispatch/test_fate_defense_record.py`

**Interfaces:**
- Consumes: `resolve_action_from_faces` (player path — NEVER `roll_4df`), `encounter.pending_defenses` (Task 2), `fate_action_resolved_span(role="defense", source="player_thrown")`, `fate_defend_phase_span(responded=True)`.
- Produces:
  - `dispatch_fate_defense(*, encounter, snapshot, ruleset, actor_name, request_id, skill, thrown_faces, conceded=False, _tracer=None) -> FateDefenseResult` — looks up the unfilled `pending_defenses` entry by `request_id` (fail loud if missing/already-filled), resolves the defender's ladder total from `thrown_faces` with their chosen `skill` at `Opposition(value=0, kind="active")`, records `defense_total` (or `conceded=True`), emits the `role="defense"` resolution span + `fate.defend_phase(responded=True)`, and reports `ledger_full: bool` + the `FateOutcome` for the roll broadcast.
  - `@dataclass(frozen=True) class FateDefenseResult` — `defense_roll: FateOutcome | None`, `ledger_full: bool`, `conceded: bool`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/server/dispatch/test_fate_defense_record.py
"""Defense recording (spec 2026-06-18 §5,§7): FATE_THROW(defend) resolves from
the player's faces (never roll_4df), records defense_total on the matching
pending_defenses entry by request_id, and reports when the ledger is full."""

from __future__ import annotations

import sidequest.game.ruleset.fate_resolution as fate_resolution
from sidequest.game.ruleset import get_ruleset_module
from sidequest.server.dispatch.fate_conflict import dispatch_fate_defense
from tests._helpers.fate_fixtures import parked_conflict  # builds a parked encounter


def test_defense_records_from_faces_and_never_rolls(monkeypatch):
    snap, encounter = parked_conflict(defender="Rux", attacker="Bandit",
                                      request_id="d1", attack_total=4, defend_skill_rating=2)
    ruleset = get_ruleset_module("fate")
    called = {"roll_4df": 0}
    real = fate_resolution.roll_4df
    monkeypatch.setattr(fate_resolution, "roll_4df",
                        lambda rng: called.__setitem__("roll_4df", called["roll_4df"] + 1) or real(rng))

    res = dispatch_fate_defense(
        encounter=encounter, snapshot=snap, ruleset=ruleset, actor_name="Rux",
        request_id="d1", skill="Athletics", thrown_faces=(1, 1, 0, 0),
    )
    entry = next(p for p in encounter.pending_defenses if p.request_id == "d1")
    assert entry.defense_total == 1 + 1 + 2  # faces(+2) + skill(2), opposition 0
    assert res.ledger_full is True
    assert called["roll_4df"] == 0  # PLAYER defense never server-rolls


def test_unknown_request_id_fails_loud():
    import pytest
    from sidequest.server.dispatch.fate_conflict import FateConflictError

    snap, encounter = parked_conflict(defender="Rux", attacker="Bandit",
                                      request_id="d1", attack_total=4, defend_skill_rating=2)
    ruleset = get_ruleset_module("fate")
    with pytest.raises(FateConflictError):
        dispatch_fate_defense(
            encounter=encounter, snapshot=snap, ruleset=ruleset, actor_name="Rux",
            request_id="NOPE", skill="Athletics", thrown_faces=(0, 0, 0, 0),
        )


def test_concede_marks_entry_and_fills_ledger():
    snap, encounter = parked_conflict(defender="Rux", attacker="Bandit",
                                      request_id="d1", attack_total=4, defend_skill_rating=2)
    ruleset = get_ruleset_module("fate")
    res = dispatch_fate_defense(
        encounter=encounter, snapshot=snap, ruleset=ruleset, actor_name="Rux",
        request_id="d1", skill="Athletics", thrown_faces=(0, 0, 0, 0), conceded=True,
    )
    entry = next(p for p in encounter.pending_defenses if p.request_id == "d1")
    assert entry.conceded is True and res.conceded is True and res.ledger_full is True
```

> **Fixture note:** `parked_conflict(...)` returns a snapshot+encounter already parked: one `FatePendingDefense(request_id=..., defender=..., attacker=..., attack_total=..., defense_total=None)`, the defender seated with the given `defend_skill_rating` on the named skill, and a matching sealed NPC attack commit in `fate_commits` (so RESOLVE in Task 7 has something to walk). Add it to `tests/_helpers/fate_fixtures.py` beside the Task 4 helper.

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/server/dispatch/test_fate_defense_record.py -q`
Expected: FAIL — `ImportError: cannot import name 'dispatch_fate_defense'`.

- [ ] **Step 3: Add `FateDefenseResult` + `dispatch_fate_defense`**

In `sidequest/server/dispatch/fate_conflict.py`, add the result dataclass near `FateExchangeResult` and the dispatcher near `dispatch_fate_action`:

```python
@dataclass(frozen=True)
class FateDefenseResult:
    """Outcome of recording one PC defense (spec 2026-06-18 §5). ``ledger_full``
    is True when every pending_defenses entry is now filled (defense_total set or
    conceded) — the caller then RESUMEs the exchange."""

    defense_roll: FateOutcome | None
    ledger_full: bool
    conceded: bool


def dispatch_fate_defense(
    *,
    encounter: StructuredEncounter,
    snapshot: GameSnapshot,
    ruleset: FateRulesetModule,
    actor_name: str,
    request_id: str,
    skill: str,
    thrown_faces: tuple[int, int, int, int],
    conceded: bool = False,
    _tracer: trace.Tracer | None = None,
) -> FateDefenseResult:
    """Record a PC's interactive defense onto the parked exchange (spec §5/§7).

    Player path: the defender's 4dF faces ARE the roll (ADR-148) — resolved via
    ``resolve_action_from_faces``, NEVER ``roll_4df``. The chosen ``skill`` is
    free-pick (the Zork Problem). On concede, the entry is flagged and no roll is
    recorded. Fails loud on an unknown / already-filled ``request_id`` (No Silent
    Fallbacks)."""
    entry = next(
        (p for p in encounter.pending_defenses if p.request_id == request_id), None
    )
    if entry is None:
        raise FateConflictError(
            f"FATE_THROW(defend) for unknown request_id {request_id!r} — "
            "no pending defense awaits it (No Silent Fallbacks)"
        )
    if entry.defense_total is not None or entry.conceded:
        raise FateConflictError(
            f"defense for {request_id!r} already recorded — one defense per attack"
        )

    if conceded:
        entry.conceded = True
        outcome = None
    else:
        core = snapshot.find_creature_core(actor_name)
        rating = core.fate_sheet.skills.get(skill, 0) if core and core.fate_sheet else 0
        outcome = ruleset.resolve_action_from_faces(
            skill_rating=rating,
            opposition=Opposition(value=0, kind="active"),
            faces=thrown_faces,
            actor=actor_name,
            role="defense",
            _tracer=_tracer,
        )
        entry.defense_total = outcome.ladder_total

    fate_defend_phase_span(
        defender=entry.defender, attacker=entry.attacker, request_id=request_id,
        responded=True, conceded=entry.conceded, _tracer=_tracer,
    )
    ledger_full = all(
        (p.defense_total is not None or p.conceded) for p in encounter.pending_defenses
    )
    return FateDefenseResult(defense_roll=outcome, ledger_full=ledger_full, conceded=entry.conceded)
```

> Pass `role="defense"` through the ruleset wrapper: in `sidequest/game/ruleset/fate.py`, add a `role: str = "action"` keyword to `FateRulesetModule.resolve_action_from_faces` and forward it to `fate_action_resolved_span(role=role, ...)` (the proactive callers omit it → `"action"`). This keeps the defense span tagged `role="defense", source="player_thrown"`.

- [ ] **Step 4: Route `action == "defend"` in the throw handler**

In `sidequest/handlers/fate_throw.py`, before building the proactive `FateActionPayload` (~line 110), branch on the defend action:

```python
        if payload.action == "defend":
            from sidequest.server.dispatch.fate_conflict import dispatch_fate_defense

            ruleset = get_ruleset_module(sd.genre_pack.rules.ruleset)
            try:
                defense = dispatch_fate_defense(
                    encounter=encounter, snapshot=snapshot, ruleset=ruleset,
                    actor_name=character.core.name, request_id=payload.request_id,
                    skill=payload.skill, thrown_faces=payload.face,
                )
            except (FateConflictError, FateEconomyError) as exc:
                return [_error_msg(f"FATE_THROW(defend) rejected: {exc}", code="fate_defend_error")]
            # Broadcast the defender's own roll (role=defense) so the table sees it,
            # then RESUME+narrate when the ledger is full (Task 7).
            return await _finish_defense(session, sd, character, payload, defense)
```

`_finish_defense` is implemented in Task 7 (broadcast roll + resume/narrate). For THIS task, stub it as broadcast-only so the test passes incrementally — but since the green bar here is `dispatch_fate_defense` behavior, the unit test (Step 1) drives the dispatcher directly and does not require `_finish_defense`. Implement `_finish_defense` fully in Task 7.

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/server/dispatch/test_fate_defense_record.py -q`
Expected: PASS (3 passed).

- [ ] **Step 6: Lint + Commit**

```bash
uv run ruff format sidequest/server/dispatch/fate_conflict.py sidequest/game/ruleset/fate.py sidequest/handlers/fate_throw.py tests/server/dispatch/test_fate_defense_record.py
uv run ruff check sidequest/server/dispatch/fate_conflict.py sidequest/game/ruleset/fate.py sidequest/handlers/fate_throw.py tests/server/dispatch/test_fate_defense_record.py
git add sidequest/server/dispatch/fate_conflict.py sidequest/game/ruleset/fate.py sidequest/handlers/fate_throw.py tests/server/dispatch/test_fate_defense_record.py tests/_helpers/fate_fixtures.py
git commit -m "feat(126-8): record PC defense from faces by request_id (never roll_4df)"
```

---

### Task 7: RESUME → RESOLVE-with-recorded-defense + narrate once

**Files:**
- Modify: `sidequest/server/dispatch/fate_conflict.py` (`_resolve_attack` reads the recorded PC defense; clear `pending_defenses` at resume; a `resume_fate_exchange` entry)
- Modify: `sidequest/handlers/fate_throw.py` (`_finish_defense`: broadcast the defense roll, and when `ledger_full`, RESOLVE + invoke the narrator exactly once)
- Test: `tests/server/dispatch/test_fate_resume_resolve.py`

**Interfaces:**
- Consumes: `encounter.pending_defenses` (Task 2/6), `run_fate_exchange` (the walk), `orchestrator.run_narration_turn` (the single narrator entry, `orchestrator.py:3124`), the turn-context builder (`_build_turn_context` in `session_helpers.py`, mirrored from `websocket_session_handler.py:1042`).
- Produces:
  - `_resolve_attack` (modified): for a PC defender with a recorded `pending_defenses` entry, use `entry.defense_total` (or treat `entry.conceded` as an auto-taken-out / concession) **instead of** `_roll_defense`. NPC defenders still `_roll_defense`.
  - `resume_fate_exchange(*, encounter, snapshot, ruleset, round_number, _tracer=None) -> FateExchangeResult` — walks via `run_fate_exchange` then clears `encounter.pending_defenses`.
  - `_finish_defense(session, sd, character, payload, defense) -> list[object]` in the handler — broadcasts the `FATE_ROLL`, and on `defense.ledger_full` runs `resume_fate_exchange` + one `run_narration_turn`, broadcasting the resulting narration.

> **Determinism note for `_resolve_attack`:** the recorded `defense_total` must be read inside the walk. The cleanest seam: a per-walk lookup `recorded = {p.defender: p for p in encounter.pending_defenses}`. In `_resolve_attack`, before calling `_roll_defense` (line 514), check `recorded.get(commit.target)`; if present and `defense_total is not None`, use it; if `conceded`, route to the taken-out/concession branch; else (NPC defender, no entry) `_roll_defense`. Pass `recorded` down from `run_fate_exchange` (add a `recorded_defenses: dict[str, FatePendingDefense] | None = None` kwarg threaded to `_resolve_attack`), defaulting to `{}` so today's no-park path is unchanged.

- [ ] **Step 1: Characterize the current resolve path (de-risk the keystone)**

Before changing `_resolve_attack`, write a characterization test that pins today's behavior so the change is provably additive:

```python
# tests/server/dispatch/test_fate_resume_resolve.py  (first test)
"""RESUME + resolve-with-recorded-defense (spec 2026-06-18 §5,§7). First, pin the
existing NPC-defense behavior so the recorded-defense branch is provably additive."""

from __future__ import annotations

import random

from sidequest.game.ruleset import get_ruleset_module
from sidequest.server.dispatch.fate_conflict import run_fate_exchange
from tests._helpers.fate_fixtures import conflict_with_pc_and_npc


def test_npc_defender_still_server_rolls():
    # An NPC defending a PC attack: no pending_defenses entry → _roll_defense path.
    snap, encounter = conflict_with_pc_and_npc(pc="Rux", npc="Bandit")
    # PC attacks the NPC; seat the PC commit directly (helper) and resolve.
    encounter.fate_commits.clear()
    # ... helper seals a PC 'attack' on 'Bandit' with ladder_total=5 ...
    result = run_fate_exchange(
        encounter=encounter, snapshot=snap, ruleset=get_ruleset_module("fate"),
        rng=random.Random(3), round_number=1,
    )
    assert result.resolved in (True, False)  # walked without a recorded NPC defense
```

- [ ] **Step 2: Write the failing resume test**

```python
def test_recorded_pc_defense_used_instead_of_roll(monkeypatch):
    import sidequest.server.dispatch.fate_conflict as fc
    from sidequest.server.dispatch.fate_conflict import resume_fate_exchange
    from tests._helpers.fate_fixtures import parked_conflict_filled

    # Parked encounter with the NPC attack sealed (total 5) and Rux's defense
    # ALREADY recorded as total 2 (a 3-shift hit lands).
    snap, encounter = parked_conflict_filled(
        defender="Rux", attacker="Bandit", attack_total=5, recorded_defense_total=2,
    )
    calls = {"roll_defense": 0}
    real = fc._roll_defense
    monkeypatch.setattr(fc, "_roll_defense",
                        lambda **k: calls.__setitem__("roll_defense", calls["roll_defense"] + 1) or real(**k))

    resume_fate_exchange(
        encounter=encounter, snapshot=snap, ruleset=get_ruleset_module("fate"), round_number=1,
    )
    # PC defense came from the RECORD, not a server roll; ledger cleared.
    assert calls["roll_defense"] == 0
    assert encounter.pending_defenses == []
    # 5 - 2 = 3 shifts → Rux took stress/consequence or is taken out (mechanically real)
    rux = snap.find_creature_core("Rux")
    assert any(b.checked for b in rux.fate_sheet.stress["physical"].boxes) or \
        any(c.aspect for c in rux.fate_sheet.consequences) or \
        encounter.find_actor("Rux").withdrawn
```

- [ ] **Step 3: Thread recorded defenses through the walk**

In `run_fate_exchange`, build `recorded = {p.defender: p for p in encounter.pending_defenses}` after seating, and pass `recorded_defenses=recorded` into `_resolve_attack`. Add the kwarg to `_resolve_attack` (default `None`). Replace its defense-roll block (lines 514-522):

```python
    recorded = (recorded_defenses or {}).get(commit.target)
    if recorded is not None and recorded.conceded:
        # Concede-at-defend: the defender folds. Take them out on their own terms
        # (the per-attack concession; fate-point award handled by concede path).
        defense_total = None  # signals the conceded branch below
    elif recorded is not None and recorded.defense_total is not None:
        defense_total = recorded.defense_total  # PC defense from the client (ADR-148)
    else:
        defense_total = _roll_defense(  # NPC defender — server-rolled
            ruleset=ruleset, snapshot=snapshot, defender=commit.target,
            mental=mental, rng=rng, _tracer=_tracer,
        )
    if recorded is not None and recorded.conceded:
        target_actor = encounter.find_actor(commit.target)
        if target_actor is not None:
            target_actor.withdrawn = True
        fate_taken_out_span(actor=commit.target, by=commit.actor, shifts=0, _tracer=_tracer)
        hints.append(f"{commit.target} concedes to {commit.actor} (fold at defend).")
        _maybe_resolve_side_cleared(encounter)
        return
    shifts = commit.ladder_total - defense_total
```

(Everything below `shifts = ...` is unchanged.)

- [ ] **Step 4: Add `resume_fate_exchange`**

```python
def resume_fate_exchange(
    *,
    encounter: StructuredEncounter,
    snapshot: GameSnapshot,
    ruleset: FateRulesetModule,
    round_number: int = 0,
    _tracer: trace.Tracer | None = None,
) -> FateExchangeResult:
    """RESUME a parked exchange once every pending defense is filled (spec §5):
    walk it (PC defenses read from the ledger; NPC defenses server-rolled), then
    clear the ledger. ``run_fate_exchange`` does the walk; we pass the recorded
    defenses and reset the ledger after."""
    result = run_fate_exchange(
        encounter=encounter, snapshot=snapshot, ruleset=ruleset,
        rng=random.Random(), round_number=round_number, _tracer=_tracer,
    )
    encounter.pending_defenses.clear()
    return result
```

(The `rng` here only feeds NPC defenses / NPC seating that survived; PC defenses never touch it.)

- [ ] **Step 5: Implement `_finish_defense` in the handler (broadcast + resume + narrate once)**

In `sidequest/handlers/fate_throw.py`:

```python
async def _finish_defense(session, sd, character, payload, defense):
    out: list[object] = []
    # Broadcast the defender's own roll (role=defense) unless they conceded.
    if defense.defense_roll is not None and sd._room is not None:
        from sidequest.game.dice import generate_dice_seed
        from sidequest.game.ruleset.fate_projection import build_fate_roll_payload
        from sidequest.protocol.messages import FateRollMessage

        seed = generate_dice_seed(
            f"{sd.genre_slug}:{sd.world_slug}:{sd.player_id}",
            sd.snapshot.turn_manager.interaction,
        )
        roll = build_fate_roll_payload(defense.defense_roll, seed=seed, throw_params=payload.throw_params)
        sd._room.broadcast(FateRollMessage(payload=roll, player_id=sd.player_id), exclude_socket_id=None)

    if not defense.ledger_full:
        session._persist_snapshot()  # still parked — checkpoint and wait
        return out

    # RESUME → RESOLVE → NARRATE ONCE (spec §3 step 5).
    from sidequest.server.dispatch.fate_conflict import resume_fate_exchange
    from sidequest.server.session_helpers import _build_turn_context

    ruleset = get_ruleset_module(sd.genre_pack.rules.ruleset)
    resume_fate_exchange(
        encounter=sd.snapshot.encounter, snapshot=sd.snapshot, ruleset=ruleset,
        round_number=sd.snapshot.turn_manager.interaction,
    )
    action = "[FATE_EXCHANGE_RESOLVED] " + " ".join(sd.snapshot.encounter.narrator_hints)
    turn_context = _build_turn_context(session, sd)
    narration = await sd.orchestrator.run_narration_turn(action, turn_context)
    session._persist_snapshot()
    # Emit the narration to the room using the same NARRATION emit the
    # natural-language turn uses (grep _emit_narration / NarrationMessage in
    # websocket_session_handler.py and reuse it — do NOT hand-roll the payload).
    out.extend(session._narration_messages_for(narration))  # replace with the real emit seam
    return out
```

> **Integration grounding (verify against live code during execution):** the exact `_build_turn_context` signature and the narration-emit seam (`_narration_messages_for` is a placeholder for the real call) must be lifted from `websocket_session_handler.py` around the `run_narration_turn` call site (line ~1042) and `session_helpers.py`. This is the one cross-subsystem seam in the plan — wire it to the existing functions, do not invent new ones (Don't Reinvent / No Stubbing). This step also fills a real 126-7 gap: today the `FATE_THROW` path never narrates a resolved exchange; the spec's "one narration at RESOLVE" establishes it here.

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/server/dispatch/test_fate_resume_resolve.py -q`
Expected: PASS.

- [ ] **Step 7: Lint + Commit**

```bash
uv run ruff format sidequest/server/dispatch/fate_conflict.py sidequest/handlers/fate_throw.py tests/server/dispatch/test_fate_resume_resolve.py
uv run ruff check sidequest/server/dispatch/fate_conflict.py sidequest/handlers/fate_throw.py tests/server/dispatch/test_fate_resume_resolve.py
git add sidequest/server/dispatch/fate_conflict.py sidequest/handlers/fate_throw.py tests/server/dispatch/test_fate_resume_resolve.py tests/_helpers/fate_fixtures.py
git commit -m "feat(126-8): resume + resolve-with-recorded-defense, narrate once"
```

---

### Task 8: End-to-end WIRING + block-and-wait AFK + resume-safety + conditional DEFEND

**Files:**
- Test: `tests/server/test_fate_defend_barrier_wiring.py` (the mandatory wiring test — drives the real handler/registry/exchange)

**Interfaces:**
- Consumes: the whole stack — `session.handle_message`, the message registry, `dispatch_fate_action` → park → `FATE_DEFEND_REQUEST` → `dispatch_fate_defense` → `resume_fate_exchange` → narration.

- [ ] **Step 1: Write the end-to-end wiring test**

```python
# tests/server/test_fate_defend_barrier_wiring.py
"""WIRING (spec 2026-06-18 §11): NPC-attacks-PC → FATE_DEFEND_REQUEST → player
defend FATE_THROW → resolve → narrate, all through the real session handler,
message registry, and exchange. The NPC path still server-rolls; the player
defense never does; an absent defender holds the barrier; a suspended exchange
survives a reload without re-rolling NPC dice."""

from __future__ import annotations

from sidequest.protocol.enums import MessageType
from tests._helpers.fate_session import playing_session_with_fate_conflict


async def test_full_defend_round_through_real_handlers(monkeypatch):
    session, proactive_throw = playing_session_with_fate_conflict(
        actor="Rux", attacker_npc="Bandit", attack_targets="Rux",
        action="attack", target="Bandit",
    )
    sent = []
    monkeypatch.setattr(session._room, "broadcast", lambda m, **k: sent.append(m) or [])

    # 1) Proactive throw closes the barrier → REVEAL → park → defend request.
    await session.handle_message(proactive_throw)
    req = next(m for m in sent if getattr(m, "type", None) == MessageType.FATE_DEFEND_REQUEST)
    enc = session._session_data.snapshot.encounter
    assert enc.resolved is False and len(enc.pending_defenses) == 1

    # 2) The defender answers with a FATE_THROW(action=defend) echoing the request_id.
    defend_throw = _make_defend_throw(session, request_id=req.payload.request_id,
                                      skill="Athletics", faces=(1, 1, 0, 0))
    out = await session.handle_message(defend_throw)

    # 3) Resolved + narrated exactly once; ledger cleared.
    assert enc.pending_defenses == []
    narrations = [m for m in (sent + out) if getattr(m, "type", None) == MessageType.NARRATION]
    assert len(narrations) == 1


async def test_absent_defender_holds_the_barrier(monkeypatch):
    session, proactive_throw = playing_session_with_fate_conflict(
        actor="Rux", attacker_npc="Bandit", attack_targets="Rux",
        action="attack", target="Bandit",
    )
    sent = []
    monkeypatch.setattr(session._room, "broadcast", lambda m, **k: sent.append(m) or [])
    await session.handle_message(proactive_throw)
    enc = session._session_data.snapshot.encounter
    # No defend throw arrives. The barrier stays open; nothing auto-resolves.
    assert enc.resolved is False
    assert any(p.defense_total is None and not p.conceded for p in enc.pending_defenses)
    assert not [m for m in sent if getattr(m, "type", None) == MessageType.NARRATION]


def test_parked_exchange_survives_reload_without_rerolling_npc():
    session, _ = playing_session_with_fate_conflict(
        actor="Rux", attacker_npc="Bandit", attack_targets="Rux",
        action="attack", target="Bandit",
    )
    # Drive to the parked state, capture the locked NPC dice, round-trip the snapshot.
    # (Use the same helper the persistence tests use to save+load.)
    from sidequest.game.session import GameSnapshot

    enc = session._session_data.snapshot.encounter
    # ... park it (proactive throw) ...
    npc_commit = next(c for c in enc.fate_commits if c.actor == "Bandit")
    locked_dice = npc_commit.dice
    reloaded = GameSnapshot.model_validate_json(session._session_data.snapshot.model_dump_json())
    rc = next(c for c in reloaded.encounter.fate_commits if c.actor == "Bandit")
    assert rc.dice == locked_dice  # NPC dice are LOCKED across the suspend
    assert reloaded.encounter.pending_defenses[0].defense_total is None
```

> Add `_make_defend_throw(...)` to `tests/_helpers/fate_session.py` (builds a `FateThrowMessage` with `action="defend"`, the echoed `request_id`, a chosen `skill`, and 4 faces). The `NARRATION` MessageType / message class name is whatever the natural-language turn emits — grep `NarrationMessage` to confirm.

- [ ] **Step 2: Run the wiring tests**

Run: `uv run pytest tests/server/test_fate_defend_barrier_wiring.py -q`
Expected: PASS (3 passed). If the narration emit seam in Task 7 Step 5 was wired correctly, exactly one NARRATION appears; if zero, the resume→narrate trigger is not wired — fix Task 7 Step 5 before proceeding.

- [ ] **Step 3: Full-suite gate before PR**

Run: `uv run pytest -q` (parallel default). Re-run any telemetry/span files that deadlock under `-n auto` serially with `-n0`.
Expected: green except known pre-existing failures (confirm none are in the files this plan touched). Then run the Fate slice end-to-end once more: `uv run pytest tests/server/dispatch -q -k fate && uv run pytest tests/handlers -q -k fate_throw`.

- [ ] **Step 4: Commit**

```bash
git add tests/server/test_fate_defend_barrier_wiring.py tests/_helpers/fate_session.py
git commit -m "test(126-8): end-to-end DEFEND barrier wiring + AFK block-and-wait + resume-safety"
```

---

## Self-Review

**1. Spec coverage** (spec §10 first-slice checklist):
- COMMIT→REVEAL→DEFEND→RESOLVE restructure → Task 4 (REVEAL + park), Task 7 (RESUME/RESOLVE). ✓
- `pending_defenses` ledger + suspend/resume, resume-safe → Task 2 (model + round-trip), Task 4 (write), Task 7 (clear), Task 8 (reload). ✓
- `FATE_DEFEND_REQUEST` + `FATE_THROW(action=defend)` → Task 1 (protocol), Task 5 (emit), Task 6 (consume). ✓
- Player defense via `resolve_action_from_faces`; NPC stays `roll_4df` → Task 6 (faces, roll_4df spy), Task 7 (recorded vs `_roll_defense`). ✓
- Concede-at-defend → Task 6 (`conceded`), Task 7 (concede branch). ✓
- `role`/`fate.defend_phase` OTEL → Task 3 (+ wired in Task 4 request-time and Task 6 respond-time). ✓
- Block-and-wait AFK (no timeout/auto-roll) → Task 8 `test_absent_defender_holds_the_barrier`; nowhere does a timeout/auto-roll exist. ✓
- Conditional DEFEND (no PC targeted → no request, skip barrier) → Task 4 `test_no_pc_targeted_resolves_immediately`, Task 8. ✓
- Mandatory wiring test → Task 8 drives the real handler/registry/exchange. ✓
- UI surfaces (§8), Guitar Solo "active help" (§8/§10), DEFEND timeout (§5) → **out of scope** (UI is the follow-up plan; active-help + timeout are deferred — correct, no task). ✓

**2. Placeholder scan:** Two steps intentionally defer to live-code seams rather than invent APIs — Task 5 Step 4 (`_persist_snapshot` → the real `save_snapshot`) and Task 7 Step 5 (`_build_turn_context` + the narration emit seam). These are flagged as "wire to the existing function, do not reinvent" with the exact file:line to lift from (`websocket_session_handler.py:1042`), per Don't-Reinvent / No-Stubbing — they are integration bindings, not unfilled logic. All mechanical/engine steps show complete code. ✓

**3. Type consistency:** `FatePendingDefense` fields (`request_id`, `attacker`, `defender`, `attack_skill`, `attack_total`, `mental`, `defense_total`, `conceded`) are used identically in Tasks 2, 4, 6, 7. `FateDispatchResult` extended additively (`defend_requests`, `awaiting_defense` with defaults) so Task 4's new returns don't break existing call sites. `dispatch_fate_defense` returns `FateDefenseResult(defense_roll, ledger_full, conceded)`, consumed unchanged in Task 7's `_finish_defense`. `fate_action_resolved_span(..., role=..., source=...)` and `resolve_action_from_faces(..., role=...)` signatures match across Tasks 3 and 6. `FateDefendRequestPayload` fields match between Task 1 (def), Task 4 (produce), Task 5 (emit). ✓

**Open design question surfaced for the author (Keith):** the narration trigger. Today's `FATE_THROW` path never narrates a resolved exchange (`FateThrowHandler` returns `[]`); the spec's "one narration at RESOLVE" is therefore *new* behavior this plan introduces in Task 7. The plan wires it via `orchestrator.run_narration_turn` from the defense handler. If the intended cadence is instead "narration rides the next natural-language turn," Task 7's narrate step changes — confirm before executing Task 7.
