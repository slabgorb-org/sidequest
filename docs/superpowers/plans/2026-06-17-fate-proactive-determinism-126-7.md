# Fate Proactive 4dF Determinism (Story 126-7) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make a player's *proactive* Fate (4dF) action resolve from the dice the player physically threw in the 3D tray — the settled faces ARE the roll — while NPC rolls stay server-side.

**Architecture:** Mirror the live d20 physics-is-the-roll path. A new client→server `FATE_THROW` message carries the action intent + the 4 settled dF faces + the throw gesture. The server resolves the action from those faces (never `roll_4df` on the player path) and broadcasts `FATE_ROLL` echoing the thrower's gesture so every seat replays the same tumble. NPC/opponent rolls and *player defense* rolls remain server-side (defense is Story 126-8). Fate ladder math is unchanged (SOUL: bind the ruleset).

**Tech Stack:** Python 3 / pydantic v2 / FastAPI / pytest (server); React + TypeScript / Vite / vitest (ui); Three.js + Rapier dice-lib (existing dF `DieKind`, reused).

**Spec:** `docs/superpowers/specs/2026-06-17-fate-determinative-rolls-design.md` · **ADR:** ADR-148.

**Repos / branches:** `sidequest-server` (`feat/126-7-fate-4df-determinative`, base `develop`), `sidequest-ui` (`feat/126-7-fate-4df-determinative`, base `develop`).

**Test env note:** server handler/dispatch tests need `SIDEQUEST_DATABASE_URL=postgresql://$USER@localhost:5432/sidequest_test` (provision via `just pg-up`). Pure protocol/resolution unit tests do not.

---

## File Structure

**Server (`sidequest-server/sidequest/`)**
- `protocol/enums.py` — add `MessageType.FATE_THROW` (modify; near `FATE_ACTION` ~line 88).
- `protocol/fate.py` — add `FateThrowPayload` (modify; beside `FateActionPayload` line 18).
- `protocol/messages.py` — add `FateThrowMessage` + register in the `GameMessage` union (modify; `FateActionMessage` line 1360, union `_Phase1Variant` ~1750–1799).
- `game/ruleset/fate_resolution.py` — extract `_build_outcome`, add `resolve_action_from_faces` (modify; `resolve_action` line 99, `roll_4df` line 89).
- `game/ruleset/fate.py` — add `FateRulesetModule.resolve_action_from_faces` wrapper (modify; `resolve_action` line 194).
- `telemetry/spans/fate.py` — add `source` kwarg to `fate_action_resolved_span` (modify; line 211).
- `game/ruleset/fate_projection.py` — `build_fate_roll_payload` accepts a `throw_params` override (modify; line 196, `_DEFAULT_FATE_THROW` line 178).
- `server/dispatch/fate_conflict.py` — `dispatch_fate_action` resolves the player's proactive action from reported faces; reroll on player path = accounting only (modify; line 734).
- `handlers/fate_throw.py` — **create** `FateThrowHandler` (mirrors `handlers/fate_action.py`).
- `server/websocket_session_handler.py` — register `"FATE_THROW"` in the handler registry (modify; ~line 509/517–530).

**UI (`sidequest-ui/src/`)**
- `types/protocol.ts` — add `MessageType.FATE_THROW` (modify; `FATE_ACTION` line 116).
- `types/payloads.ts` — add `FateThrowPayload` + `FateThrowMessage` (modify; `FateRollPayload` line 574).
- `App.tsx` — add `handleFateThrow` send (modify; `handleFateAction` line 1976, `handleDiceThrow` line 1870).
- `components/FateConflictSurface.tsx` — roll verbs mount the throw tray and defer send until settle; non-roll verbs unchanged (modify; `FateActionInput` line 39).
- `dice/FateDiceTray.tsx` — thrower mode (capture 4 dF faces → submit) + keep spectator replay-and-snap (modify; `replayThrowParams` line 46, `onAllSettle` no-op line 64).

**No dice-lib change** — the dF `DieKind` (`dieRegistry.ts`, `dF.ts` `readDFValue`, the `0` label) is consumed as-is.

---

## SERVER

### Task 1: `FATE_THROW` protocol message

**Files:**
- Modify: `sidequest-server/sidequest/protocol/enums.py`
- Modify: `sidequest-server/sidequest/protocol/fate.py`
- Modify: `sidequest-server/sidequest/protocol/messages.py`
- Test: `sidequest-server/tests/protocol/test_fate_throw_payload.py` (create)

- [ ] **Step 1: Write the failing test**

```python
# tests/protocol/test_fate_throw_payload.py
import pytest
from pydantic import ValidationError

from sidequest.protocol.fate import FateThrowPayload
from sidequest.protocol.dice import ThrowParams
from sidequest.protocol.messages import GameMessage
from sidequest.protocol.enums import MessageType

_TP = {"velocity": [0.0, 4.0, -1.0], "angular": [0.5, 0.5, 0.5], "position": [0.5, 0.5]}


def _payload(**over):
    base = {
        "request_id": "r1",
        "action": "overcome",
        "skill": "Athletics",
        "throw_params": _TP,
        "face": [-1, 0, 1, 1],
    }
    base.update(over)
    return base


def test_valid_payload_parses():
    p = FateThrowPayload(**_payload())
    assert p.face == (-1, 0, 1, 1)
    assert isinstance(p.throw_params, ThrowParams)


def test_rejects_wrong_face_count():
    with pytest.raises(ValidationError):
        FateThrowPayload(**_payload(face=[0, 0, 0]))


def test_rejects_out_of_range_face():
    with pytest.raises(ValidationError):
        FateThrowPayload(**_payload(face=[0, 0, 0, 2]))


def test_rejects_extra_field():
    with pytest.raises(ValidationError):
        FateThrowPayload(**_payload(bonus=99))


def test_routes_in_game_message_union():
    msg = GameMessage.model_validate(
        {"type": "FATE_THROW", "payload": _payload(), "player_id": "p1"}
    )
    assert msg.root.type == MessageType.FATE_THROW
    assert msg.root.payload.face == (-1, 0, 1, 1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/protocol/test_fate_throw_payload.py -v`
Expected: FAIL — `ImportError: cannot import name 'FateThrowPayload'`.

- [ ] **Step 3: Add the enum value**

In `sidequest/protocol/enums.py`, beside `FATE_ACTION = "FATE_ACTION"`:

```python
    FATE_THROW = "FATE_THROW"
```

- [ ] **Step 4: Add `FateThrowPayload`**

In `sidequest/protocol/fate.py` (it already imports `ProtocolBase`; add `from sidequest.protocol.dice import ThrowParams` and `from pydantic import model_validator` if not present):

```python
class FateThrowPayload(ProtocolBase):
    """Player-thrown proactive Fate action (ADR-148). The four settled dF faces
    ARE the roll — the server resolves from them and never calls roll_4df on this
    path. ``throw_params`` is the gesture for spectator replay (animation only)."""

    request_id: str
    action: Literal["overcome", "create_advantage", "attack"]
    skill: str = ""
    target: str | None = None
    difficulty: int = 0
    invoke_aspect: str = ""
    invoke_mode: Literal["bonus", "reroll"] = "bonus"
    aspect_text: str = ""
    player_action: str = ""
    throw_params: ThrowParams
    face: tuple[int, int, int, int]

    @model_validator(mode="after")
    def _validate_faces(self) -> "FateThrowPayload":
        if len(self.face) != 4:
            raise ValueError("Fate throw must report exactly 4 dF faces")
        for f in self.face:
            if f not in (-1, 0, 1):
                raise ValueError("each dF face must be -1, 0, or +1")
        return self
```

> Note: `face: tuple[int, int, int, int]` already enforces exactly-4 at the pydantic layer; the validator adds the value-range check and a clearer message (defense in depth).

- [ ] **Step 5: Add `FateThrowMessage` and register in the union**

In `sidequest/protocol/messages.py`, beside `FateActionMessage` (line 1360):

```python
class FateThrowMessage(ProtocolBase):
    type: Literal[MessageType.FATE_THROW] = MessageType.FATE_THROW
    payload: FateThrowPayload
    player_id: str = ""
```

Add the import for `FateThrowPayload` next to the existing `FateActionPayload` import, and add `| FateThrowMessage` to the `_Phase1Variant` union (beside `| FateActionMessage`, ~line 1780).

- [ ] **Step 6: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/protocol/test_fate_throw_payload.py -v`
Expected: PASS (5 tests).

- [ ] **Step 7: Commit**

```bash
cd sidequest-server
git add sidequest/protocol/enums.py sidequest/protocol/fate.py sidequest/protocol/messages.py tests/protocol/test_fate_throw_payload.py
git commit -m "feat(126-7): FATE_THROW protocol message (faces-authoritative wire)"
```

---

### Task 2: Resolution split — `resolve_action_from_faces`

**Files:**
- Modify: `sidequest-server/sidequest/game/ruleset/fate_resolution.py`
- Test: `sidequest-server/tests/ruleset/test_fate_resolution_from_faces.py` (create)

- [ ] **Step 1: Write the failing test**

```python
# tests/ruleset/test_fate_resolution_from_faces.py
import random

from sidequest.game.ruleset.fate_resolution import (
    resolve_action,
    resolve_action_from_faces,
)
from sidequest.game.ruleset.fate import Opposition  # adjust import if Opposition lives elsewhere


def test_from_faces_matches_equivalent_rng_roll():
    opp = Opposition(value=1, kind="passive")
    out = resolve_action_from_faces(
        skill_rating=3, opposition=opp, faces=(1, 1, 0, -1), invoke_bonus=0
    )
    # roll_total = 1+1+0-1 = 1 ; ladder_total = 1 + 3 = 4
    assert out.roll_total == 1
    assert out.ladder_total == 4
    assert out.dice == (1, 1, 0, -1)


def test_from_faces_applies_invoke_bonus():
    opp = Opposition(value=0, kind="passive")
    out = resolve_action_from_faces(
        skill_rating=2, opposition=opp, faces=(0, 0, 0, 0), invoke_bonus=2
    )
    assert out.ladder_total == 4  # 0 + 2 + 2


def test_rng_path_unchanged():
    opp = Opposition(value=0, kind="passive")
    out = resolve_action(skill_rating=1, opposition=opp, rng=random.Random(7))
    assert -4 <= out.roll_total <= 4
    assert out.ladder_total == out.roll_total + 1
```

> If `Opposition` is not importable from `fate`, find its real module with
> `cd sidequest-server && grep -rn "class Opposition" sidequest/` and fix the import.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/ruleset/test_fate_resolution_from_faces.py -v`
Expected: FAIL — `ImportError: cannot import name 'resolve_action_from_faces'`.

- [ ] **Step 3: Refactor and add the faces variant**

In `sidequest/game/ruleset/fate_resolution.py`, replace the body of `resolve_action` (line 99) so the classify/build step is shared, and add the faces sibling:

```python
def _build_outcome(
    dice: tuple[int, int, int, int],
    *,
    skill_rating: int,
    opposition: Opposition,
    invoke_bonus: int,
) -> FateOutcome:
    roll_total = sum(dice)
    ladder_total = roll_total + skill_rating + invoke_bonus
    shifts, tier = classify_outcome(ladder_total, opposition.value)
    return FateOutcome(
        dice=dice,
        roll_total=roll_total,
        ladder_total=ladder_total,
        opposition=opposition.value,
        shifts=shifts,
        tier=tier,
    )


def resolve_action(
    *,
    skill_rating: int,
    opposition: Opposition,
    rng: random.Random,
    invoke_bonus: int = 0,
) -> FateOutcome:
    """NPC path: roll 4dF server-side."""
    return _build_outcome(
        roll_4df(rng),
        skill_rating=skill_rating,
        opposition=opposition,
        invoke_bonus=invoke_bonus,
    )


def resolve_action_from_faces(
    *,
    skill_rating: int,
    opposition: Opposition,
    faces: tuple[int, int, int, int],
    invoke_bonus: int = 0,
) -> FateOutcome:
    """Player path: resolve from the client's settled dF faces (ADR-148). Never
    touches an rng."""
    if len(faces) != 4 or any(f not in (-1, 0, 1) for f in faces):
        raise ValueError(f"invalid dF faces: {faces!r}")
    return _build_outcome(
        tuple(faces),
        skill_rating=skill_rating,
        opposition=opposition,
        invoke_bonus=invoke_bonus,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/ruleset/test_fate_resolution_from_faces.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Run the existing Fate resolution tests for regression**

Run: `cd sidequest-server && uv run pytest tests/ruleset/ -k fate -v`
Expected: PASS (the refactor preserves behavior).

- [ ] **Step 6: Commit**

```bash
cd sidequest-server
git add sidequest/game/ruleset/fate_resolution.py tests/ruleset/test_fate_resolution_from_faces.py
git commit -m "feat(126-7): resolve_action_from_faces (player path, no rng)"
```

---

### Task 3: Module wrapper + OTEL `source` attribute

**Files:**
- Modify: `sidequest-server/sidequest/telemetry/spans/fate.py`
- Modify: `sidequest-server/sidequest/game/ruleset/fate.py`
- Test: `sidequest-server/tests/ruleset/test_fate_module_from_faces_span.py` (create)

- [ ] **Step 1: Write the failing test (OTEL span assertion)**

```python
# tests/ruleset/test_fate_module_from_faces_span.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from sidequest.game.ruleset.fate import FateRulesetModule, Opposition


def _exporter():
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return exporter


def test_from_faces_emits_player_thrown_source():
    exporter = _exporter()
    mod = FateRulesetModule()
    mod.resolve_action_from_faces(
        skill_rating=2,
        opposition=Opposition(value=1, kind="passive"),
        faces=(1, 0, -1, 1),
        actor="Rux",
    )
    spans = [s for s in exporter.get_finished_spans() if s.name == "fate.action_resolved"]
    assert spans, "fate.action_resolved span not emitted"
    assert spans[-1].attributes.get("source") == "player_thrown"
```

> Confirm the span name and the existing attribute-setting style by reading
> `sidequest/telemetry/spans/fate.py` around line 211 before editing.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/ruleset/test_fate_module_from_faces_span.py -v`
Expected: FAIL — `AttributeError: 'FateRulesetModule' object has no attribute 'resolve_action_from_faces'`.

- [ ] **Step 3: Add the `source` kwarg to the span helper**

In `sidequest/telemetry/spans/fate.py`, give `fate_action_resolved_span(...)` a new keyword `source: str = "server_rolled"` and set it as a span attribute alongside the existing `dice`/`ladder_total`/etc. (match the existing `span.set_attribute(...)` style in that function).

- [ ] **Step 4: Add the module wrapper**

In `sidequest/game/ruleset/fate.py`, beside `resolve_action` (line 194), import `resolve_action_from_faces` from `fate_resolution` and add:

```python
def resolve_action_from_faces(
    self,
    *,
    skill_rating: int,
    opposition: Opposition,
    faces: tuple[int, int, int, int],
    invoke_bonus: int = 0,
    actor: str = "",
    _tracer: "trace.Tracer | None" = None,
) -> FateOutcome:
    """Player path — resolve from thrown faces and emit the lie-detector span
    tagged source=player_thrown (ADR-148)."""
    outcome = resolve_action_from_faces(
        skill_rating=skill_rating,
        opposition=opposition,
        faces=faces,
        invoke_bonus=invoke_bonus,
    )
    fate_action_resolved_span(
        actor=actor,
        skill_rating=skill_rating,
        outcome=outcome,
        source="player_thrown",
        # ...match the exact kwargs the existing resolve_action wrapper passes...
    )
    return outcome
```

Also add `source="server_rolled"` to the existing `resolve_action` wrapper's `fate_action_resolved_span(...)` call so the NPC path is explicitly tagged.

> Read the existing `fate_action_resolved_span(...)` call inside `resolve_action`
> (line ~205–215) and mirror its exact argument list — do not invent kwargs.

- [ ] **Step 5: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/ruleset/test_fate_module_from_faces_span.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd sidequest-server
git add sidequest/telemetry/spans/fate.py sidequest/game/ruleset/fate.py tests/ruleset/test_fate_module_from_faces_span.py
git commit -m "feat(126-7): FateRulesetModule.resolve_action_from_faces + source OTEL attr"
```

---

### Task 4: Echo the thrower's gesture in `build_fate_roll_payload`

**Files:**
- Modify: `sidequest-server/sidequest/game/ruleset/fate_projection.py`
- Test: `sidequest-server/tests/ruleset/test_fate_projection_throw_params.py` (create)

- [ ] **Step 1: Write the failing test**

```python
# tests/ruleset/test_fate_projection_throw_params.py
from sidequest.game.ruleset.fate_projection import build_fate_roll_payload, _DEFAULT_FATE_THROW
from sidequest.game.ruleset.fate_resolution import resolve_action_from_faces
from sidequest.game.ruleset.fate import Opposition
from sidequest.protocol.dice import ThrowParams


def _outcome():
    return resolve_action_from_faces(
        skill_rating=2, opposition=Opposition(value=0, kind="passive"), faces=(1, 0, 0, -1)
    )


def test_defaults_to_synthesized_throw_for_npc():
    payload = build_fate_roll_payload(_outcome(), seed=42)
    assert payload.throw_params == _DEFAULT_FATE_THROW


def test_echoes_player_throw_params_when_supplied():
    tp = ThrowParams(velocity=(0.0, 5.0, -2.0), angular=(1.0, 0.0, 0.0), position=(0.3, 0.7))
    payload = build_fate_roll_payload(_outcome(), seed=42, throw_params=tp)
    assert payload.throw_params == tp
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/ruleset/test_fate_projection_throw_params.py -v`
Expected: FAIL — `TypeError: build_fate_roll_payload() got an unexpected keyword argument 'throw_params'`.

- [ ] **Step 3: Add the `throw_params` override**

In `sidequest/game/ruleset/fate_projection.py`, change the signature (line 196) and the construction (line 219):

```python
def build_fate_roll_payload(
    outcome: FateOutcome,
    *,
    seed: int | None = None,
    throw_params: ThrowParams | None = None,
) -> FateRollPayload:
    ...
    return FateRollPayload(
        ...
        throw_params=throw_params if throw_params is not None else _DEFAULT_FATE_THROW,
        seed=seed if seed is not None else _fallback_seed(outcome.dice),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/ruleset/test_fate_projection_throw_params.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
cd sidequest-server
git add sidequest/game/ruleset/fate_projection.py tests/ruleset/test_fate_projection_throw_params.py
git commit -m "feat(126-7): build_fate_roll_payload echoes thrower gesture"
```

---

### Task 5: `dispatch_fate_action` resolves player action from faces

**Files:**
- Modify: `sidequest-server/sidequest/server/dispatch/fate_conflict.py`
- Test: `sidequest-server/tests/server/test_fate_dispatch_from_faces.py` (create)

> Read `dispatch_fate_action` (line 734) and the player-path call to
> `ruleset.resolve_action(...)` (line ~858) plus the `invoke_mode == "reroll"`
> branch before editing. Keep `_seat_opponent_commits` (287) and `_roll_defense`
> (243) on `rng` — those are NPC/defense and stay server-side in 126-7.

- [ ] **Step 1: Write the failing test (spy: no roll_4df on player path)**

```python
# tests/server/test_fate_dispatch_from_faces.py
import sidequest.game.ruleset.fate_resolution as fr
from sidequest.server.dispatch.fate_conflict import dispatch_fate_action
# ... import the minimal fixtures/builders used by existing fate_conflict tests ...


def test_player_action_uses_faces_not_roll_4df(monkeypatch, fate_conflict_fixture):
    called = {"n": 0}
    real = fr.roll_4df
    monkeypatch.setattr(fr, "roll_4df", lambda rng: called.__setitem__("n", called["n"] + 1) or real(rng))

    result = dispatch_fate_action(
        **fate_conflict_fixture(action="overcome", skill="Athletics"),
        thrown_faces=(1, 1, 0, 0),
    )
    assert result.action_roll is not None
    assert result.action_roll.dice == (1, 1, 0, 0)
    assert result.action_roll.roll_total == 2
    assert called["n"] == 0  # player path NEVER calls roll_4df
```

> `fate_conflict_fixture` is a stand-in: model it on the setup already used by the
> existing `tests/server/test_fate_*` dispatch tests (snapshot + ruleset + actor).
> If no such helper exists, build the minimal snapshot inline as those tests do.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && SIDEQUEST_DATABASE_URL=postgresql://$USER@localhost:5432/sidequest_test uv run pytest tests/server/test_fate_dispatch_from_faces.py -v`
Expected: FAIL — `TypeError: dispatch_fate_action() got an unexpected keyword argument 'thrown_faces'`.

- [ ] **Step 3: Thread `thrown_faces` through the player path**

In `dispatch_fate_action` (line 734), add a `thrown_faces: tuple[int, int, int, int] | None = None` parameter. Where the player action currently rolls (line ~858):

```python
if thrown_faces is not None:
    outcome = ruleset.resolve_action_from_faces(
        skill_rating=rating,
        opposition=opposition,
        faces=thrown_faces,
        invoke_bonus=invoke_bonus,
        actor=actor_name,
    )
else:
    # legacy/non-player callers (kept for now) — server rolls
    outcome = ruleset.resolve_action(
        skill_rating=rating, opposition=opposition, rng=rng,
        invoke_bonus=invoke_bonus, actor=actor_name,
    )
```

For the `invoke_mode == "reroll"` branch on the **player** path: do NOT call resolve a second time — the client already re-threw and `thrown_faces` are the final faces. Apply only the fate-point/aspect accounting that the reroll branch performs today (keep the accounting, drop the re-roll). Leave the non-player branch untouched.

> The `thrown_faces is None` branch is a transitional path for existing internal
> callers, not a player backdoor — the player path always arrives via
> `FateThrowHandler` (Task 6) with faces. It is removed when 126-8 lands and no
> server-rolled player path remains.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && SIDEQUEST_DATABASE_URL=postgresql://$USER@localhost:5432/sidequest_test uv run pytest tests/server/test_fate_dispatch_from_faces.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd sidequest-server
git add sidequest/server/dispatch/fate_conflict.py tests/server/test_fate_dispatch_from_faces.py
git commit -m "feat(126-7): dispatch_fate_action resolves player action from thrown faces"
```

---

### Task 6: `FateThrowHandler` + registry + end-to-end wiring

**Files:**
- Create: `sidequest-server/sidequest/handlers/fate_throw.py`
- Modify: `sidequest-server/sidequest/server/websocket_session_handler.py`
- Test: `sidequest-server/tests/server/test_fate_throw_handler_wiring.py` (create)

> Read `handlers/fate_action.py` end-to-end first — `FateThrowHandler` mirrors it,
> swapping the intent-only dispatch for a faces-bearing dispatch and passing the
> client `throw_params` into `build_fate_roll_payload`.

- [ ] **Step 1: Write the failing wiring test (real handler + registry → FATE_ROLL)**

```python
# tests/server/test_fate_throw_handler_wiring.py
from sidequest.protocol.messages import GameMessage
from sidequest.protocol.enums import MessageType
# ... reuse the session/room fixtures the existing fate_action handler test uses ...


def test_fate_throw_roundtrips_to_fate_roll(fate_session):  # fixture: live session + room
    msg = GameMessage.model_validate({
        "type": "FATE_THROW",
        "player_id": fate_session.player_id,
        "payload": {
            "request_id": "r1", "action": "overcome", "skill": "Athletics",
            "throw_params": {"velocity": [0, 4, -1], "angular": [0.5, 0.5, 0.5], "position": [0.5, 0.5]},
            "face": [1, 1, 0, -1],
        },
    }).root

    handler = fate_session.handler_for(MessageType.FATE_THROW)  # exercises the real registry
    import asyncio
    asyncio.run(handler.handle(fate_session.session, msg))

    broadcast = fate_session.last_broadcast(MessageType.FATE_ROLL)
    assert broadcast is not None
    assert broadcast.payload.dice == (1, 1, 0, -1)            # authoritative thrown faces
    assert broadcast.payload.throw_params.velocity == (0.0, 4.0, -1.0)  # thrower gesture echoed
```

> Model `fate_session` on the existing FATE_ACTION handler test's fixtures
> (`grep -rln "FATE_ACTION" tests/`). The point is to drive the message through
> the **registry-resolved** handler, not to call the handler class directly.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && SIDEQUEST_DATABASE_URL=postgresql://$USER@localhost:5432/sidequest_test uv run pytest tests/server/test_fate_throw_handler_wiring.py -v`
Expected: FAIL — handler/registry has no `FATE_THROW` entry.

- [ ] **Step 3: Create `FateThrowHandler`**

`sidequest/handlers/fate_throw.py` — mirror `handlers/fate_action.py`, but extract the faces and gesture from the payload and pass them through:

```python
# (mirror imports from handlers/fate_action.py)

class FateThrowHandler:
    async def handle(self, session, msg) -> list[object]:
        payload = msg.payload  # FateThrowPayload
        # ... mirror FateActionHandler.handle setup: resolve sd, snapshot, actor ...
        result = dispatch_fate_action(
            # ... same args FateActionHandler passes from a FateActionPayload ...
            thrown_faces=payload.face,
        )
        if result.action_roll is not None:
            roll_seed = generate_dice_seed(
                f"{sd.genre_slug}:{sd.world_slug}:{acting_player_id}",
                snapshot.turn_manager.interaction,
            )
            payload_out = build_fate_roll_payload(
                result.action_roll, seed=roll_seed, throw_params=payload.throw_params,
            )
            room.broadcast(FateRollMessage(payload=payload_out, player_id=acting_player_id),
                           exclude_socket_id=None)
        return []


HANDLER = FateThrowHandler()
```

> Build the `dispatch_fate_action` argument list by copying it verbatim from
> `FateActionHandler.handle` (the FateActionPayload fields map 1:1 onto
> FateThrowPayload's intent fields) and appending `thrown_faces=payload.face`.

- [ ] **Step 4: Register in the handler registry**

In `sidequest/server/websocket_session_handler.py`, in `_message_handler_for()`'s registry (~line 517–530), add:

```python
        "FATE_THROW": __import__(
            "sidequest.handlers.fate_throw", fromlist=["HANDLER"]
        ).HANDLER,
```

> Match the existing lazy-import registration style used for the other handlers in
> that dict (e.g. how `"FATE_ACTION"` is registered) — do not introduce a new
> import pattern.

- [ ] **Step 5: Run test to verify it passes**

Run: `cd sidequest-server && SIDEQUEST_DATABASE_URL=postgresql://$USER@localhost:5432/sidequest_test uv run pytest tests/server/test_fate_throw_handler_wiring.py -v`
Expected: PASS.

- [ ] **Step 6: Run the full server gate**

Run: `cd sidequest-server && uv run ruff check . && SIDEQUEST_DATABASE_URL=postgresql://$USER@localhost:5432/sidequest_test uv run pytest -q`
Expected: no new failures vs. the known baseline (read tracebacks in the Fate blast radius; ignore the documented pre-existing failures).

- [ ] **Step 7: Commit**

```bash
cd sidequest-server
git add sidequest/handlers/fate_throw.py sidequest/server/websocket_session_handler.py tests/server/test_fate_throw_handler_wiring.py
git commit -m "feat(126-7): FateThrowHandler wired into registry (e2e FATE_THROW->FATE_ROLL)"
```

---

## UI

### Task 7: `FATE_THROW` message type + send path

**Files:**
- Modify: `sidequest-ui/src/types/protocol.ts`
- Modify: `sidequest-ui/src/types/payloads.ts`
- Modify: `sidequest-ui/src/App.tsx`
- Test: `sidequest-ui/src/__tests__/fateThrow.test.ts` (create)

- [ ] **Step 1: Write the failing test**

```ts
// src/__tests__/fateThrow.test.ts
import { describe, it, expect, vi } from "vitest";
import { MessageType } from "../types/protocol";
import { makeFateThrowMessage } from "../lib/fateThrow"; // small pure builder (Step 3)

describe("FATE_THROW", () => {
  it("builds a wire message with authoritative faces + gesture", () => {
    const msg = makeFateThrowMessage({
      request_id: "r1",
      action: "overcome",
      skill: "Athletics",
      throw_params: { velocity: [0, 4, -1], angular: [0.5, 0.5, 0.5], position: [0.5, 0.5] },
      face: [1, 0, -1, 1],
    });
    expect(msg.type).toBe(MessageType.FATE_THROW);
    expect(msg.payload.face).toEqual([1, 0, -1, 1]);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-ui && npx vitest run src/__tests__/fateThrow.test.ts`
Expected: FAIL — cannot resolve `../lib/fateThrow` / `MessageType.FATE_THROW`.

- [ ] **Step 3: Add the type, payload, and a pure builder**

`src/types/protocol.ts` — add to `MessageType` beside `FATE_ACTION`:

```ts
  FATE_THROW: "FATE_THROW",
```

`src/types/payloads.ts` — beside `FateRollPayload` (line 574):

```ts
export interface FateThrowPayload {
  request_id: string;
  action: "overcome" | "create_advantage" | "attack";
  skill?: string;
  target?: string | null;
  difficulty?: number;
  invoke_aspect?: string;
  invoke_mode?: "bonus" | "reroll";
  aspect_text?: string;
  player_action?: string;
  throw_params: DiceThrowParams;
  face: number[]; // exactly 4, each -1/0/+1
}

export interface FateThrowMessage extends BaseMessage {
  type: typeof MessageType.FATE_THROW;
  payload: FateThrowPayload;
}
```

`src/lib/fateThrow.ts` (create) — a pure builder so the wire shape is unit-testable:

```ts
import { MessageType } from "../types/protocol";
import type { FateThrowMessage, FateThrowPayload } from "../types/payloads";

export function makeFateThrowMessage(
  payload: FateThrowPayload,
  playerId = "",
): FateThrowMessage {
  return { type: MessageType.FATE_THROW, payload, player_id: playerId };
}
```

`src/App.tsx` — add `handleFateThrow` (mirror `handleDiceThrow` at line 1870 and `handleFateAction` at line 1976):

```ts
const handleFateThrow = useCallback(
  (payload: FateThrowPayload) => {
    if (!sessionBound) return;
    send(makeFateThrowMessage(payload));
  },
  [sessionBound, send],
);
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-ui && npx vitest run src/__tests__/fateThrow.test.ts`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd sidequest-ui
git add src/types/protocol.ts src/types/payloads.ts src/lib/fateThrow.ts src/App.tsx src/__tests__/fateThrow.test.ts
git commit -m "feat(126-7): FATE_THROW message type + send path"
```

---

### Task 8: Fate tray thrower mode + conflict-surface wiring

**Files:**
- Modify: `sidequest-ui/src/dice/FateDiceTray.tsx`
- Modify: `sidequest-ui/src/components/FateConflictSurface.tsx`
- Test: `sidequest-ui/src/__tests__/fateDiceTrayThrow.test.tsx` (create)

> Read `src/dice/DiceOverlay.tsx:142-160` (the d20 `handleSettle → onThrow(wireParams,
> faces)` pattern) and `FateDiceTray.tsx:46,64` before editing. Thrower mode copies
> the DiceOverlay pattern for the dF `DieKind`; spectator mode keeps the existing
> `replayThrowParams` + snap.

- [ ] **Step 1: Write the failing test**

```tsx
// src/__tests__/fateDiceTrayThrow.test.tsx
import { describe, it, expect, vi } from "vitest";
import { render } from "@testing-library/react";
import { FateDiceTray } from "../dice/FateDiceTray";

// Mock DiceScene so we can drive onAllSettle deterministically without WebGL.
vi.mock("@local/dice-lib", async (orig) => {
  const actual = await orig<typeof import("@local/dice-lib")>();
  return {
    ...actual,
    DiceScene: ({ onAllSettle }: any) => {
      // simulate a physics settle on 4 dF faces
      setTimeout(() => onAllSettle([1, 0, -1, 1]), 0);
      return null;
    },
  };
});

describe("FateDiceTray thrower mode", () => {
  it("submits the settled faces via onThrow", async () => {
    const onThrow = vi.fn();
    render(
      <FateDiceTray
        mode="thrower"
        action="overcome"
        skill="Athletics"
        requestId="r1"
        onThrow={onThrow}
        ruleset="fate"
      />,
    );
    await new Promise((r) => setTimeout(r, 5));
    expect(onThrow).toHaveBeenCalledTimes(1);
    const [payload] = onThrow.mock.calls[0];
    expect(payload.face).toEqual([1, 0, -1, 1]);
    expect(payload.action).toBe("overcome");
  });
});
```

> Adjust the mock import specifier to match how `FateDiceTray` imports `DiceScene`
> today (the scout found `@local/dice-lib`; confirm in the file). The new props
> (`mode`, `action`, `skill`, `requestId`, `onThrow`) are added in Step 3.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-ui && npx vitest run src/__tests__/fateDiceTrayThrow.test.tsx`
Expected: FAIL — `FateDiceTray` has no thrower mode / `onThrow` prop.

- [ ] **Step 3: Add thrower mode to `FateDiceTray`**

Extend the props (keep the existing spectator props):

```ts
export type FateDiceTrayProps =
  | { mode?: "spectator"; roll: FateRollPayload; ruleset: string; genreSlug?: string }
  | {
      mode: "thrower";
      action: "overcome" | "create_advantage" | "attack";
      skill: string;
      requestId: string;
      target?: string | null;
      difficulty?: number;
      ruleset: string;
      genreSlug?: string;
      onThrow: (payload: FateThrowPayload) => void;
    };
```

In thrower mode, render `DiceScene` with the dF `DieKind` and `throwParams === null`
initially (so the player gets the interactive pickup/throw), and capture the settle —
mirror `DiceOverlay.handleSettle`, converting scene `ThrowParams` → wire `DiceThrowParams`:

```ts
const handleAllSettle = useCallback(
  (faces: number[], params: ThrowParams) => {
    onThrow({
      request_id: requestId,
      action,
      skill,
      target,
      difficulty,
      throw_params: {
        velocity: params.linearVelocity,
        angular: params.angularVelocity,
        position: [params.position[0] + 0.5, (params.position[2] + 0.8) / 1.6],
      },
      face: faces,
    });
  },
  [requestId, action, skill, target, difficulty, onThrow],
);
```

Keep spectator mode exactly as today (`replayThrowParams(roll.throw_params, roll.seed, D6_RADIUS)` + snap, `0` label preserved).

> If `DiceScene`'s `onAllSettle` does not currently surface the throw `params`,
> capture the local `pendingLocalParams` the way `DiceOverlay`/`InlineDiceTray` do
> (scout: `DiceOverlay.tsx:142-160`) and read them in the settle callback rather
> than threading them through `onAllSettle`.

- [ ] **Step 4: Wire the conflict surface to mount thrower mode for roll verbs**

In `src/components/FateConflictSurface.tsx`, when the player selects a roll verb
(`overcome`/`create_advantage`/`attack`), mount `FateDiceTray` in `mode="thrower"` and
pass `onThrow={handleFateThrow}` (threaded from `App.tsx`) instead of sending
`FATE_ACTION`. Non-roll verbs (`concede`/`compel_accept`/`compel_refuse`) keep sending
`FATE_ACTION` synchronously as today.

- [ ] **Step 5: Run test to verify it passes**

Run: `cd sidequest-ui && npx vitest run src/__tests__/fateDiceTrayThrow.test.tsx`
Expected: PASS.

- [ ] **Step 6: Run the UI gate**

Run: `cd sidequest-ui && npx vitest run && npm run lint`
Expected: PASS / no new failures.

- [ ] **Step 7: Commit**

```bash
cd sidequest-ui
git add src/dice/FateDiceTray.tsx src/components/FateConflictSurface.tsx src/__tests__/fateDiceTrayThrow.test.tsx
git commit -m "feat(126-7): Fate tray thrower mode submits settled dF faces"
```

---

## Self-Review

**1. Spec coverage (126-7 scope only):**
- Player roll determinative → Tasks 2, 5 (resolve_action_from_faces; dispatch from faces; spy asserts no roll_4df). ✓
- Client→server message → Task 1 (`FATE_THROW`, 4 faces ∈{−1,0,1}, extra=forbid, in union). ✓
- Interactive throw (UI) → Task 8 (thrower mode captures settled faces). ✓
- NPC server-side → Tasks 2/5 leave `resolve_action(rng)` + `_seat_opponent_commits`/`_roll_defense` untouched. ✓
- Spectator consistency → Task 4 (echo thrower gesture) + Task 8 (spectator replay+snap kept). ✓
- OTEL `source` → Task 3. ✓
- Wiring + no-revert → Task 6 (e2e through registry); 125-4 fields/label preserved (Tasks 4, 8). ✓
- *Out of 126-7 scope, by design:* player defense determinism (Story 126-8) — `_roll_defense` deliberately untouched.

**2. Placeholder scan:** No "TBD"/"handle edge cases"/"similar to". The two soft spots — `fate_conflict_fixture` (Task 5) and `fate_session` (Task 6) — point at existing FATE_ACTION test fixtures to copy, with a grep to locate them; they are real instructions, not placeholders.

**3. Type consistency:** `FateThrowPayload.face` is `tuple[int,int,int,int]` server-side / `number[]` (len 4) on the wire/TS — consistent with how d20 uses `face: list[int]`/`number[]`. `resolve_action_from_faces` signature identical across Tasks 2/3/5. `build_fate_roll_payload(..., throw_params=)` used in Task 4 and consumed in Task 6. `makeFateThrowMessage`/`FateThrowPayload` consistent across Tasks 7/8.

---

## Notes for the executor

- This is the **proactive** half. Player *defense* rolls stay server-side here — that is Story **126-8** (the DEFEND follow-up barrier), designed in the spec. Do not touch `_roll_defense`/`_seat_opponent_commits`.
- After GREEN, this returns to the pf `bdd` workflow: the RED phase (Fezzik/TEA) and GREEN phase (Inigo/Dev) own the cycle; this plan is the detailed guide they execute against. Reviewer + SM finish close it out (PR per repo to `develop`).
- ADR-148 flips `status: accepted` / `implementation-status: live` when this lands.
