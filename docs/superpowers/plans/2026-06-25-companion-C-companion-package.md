# Plan C — `sidequest-companion` Package (v1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A headless AI companion that joins a live SideQuest session as its own full-PC seat over the WebSocket protocol — connect → claim seat → character creation → play turns (in-character prose, dice, confrontations) — with a configurable role/voice and a `Transport` seam that makes the whole loop testable without a real server.

**Architecture:** Grows from understudy's bones: reuse `sidequest-seat-core`'s model backends (`make_model`, bound to a new `CompanionIntent`) and persona axes (`SeatAxes` + `RoleDial`). Replace understudy's browser perception/actuation with a thin typed WebSocket client: a `StateMirror` that merges server deltas, outgoing-frame builders, and a `Transport` protocol (real `websockets` adapter in production; a scripted `FakeTransport` in tests). Ability use is implicit in prose, so the brain mostly emits one verb — `ACT(text)` — plus narrow responses to server-pushed roll/confrontation prompts. Fair dice faces are generated client-side (physics-is-the-roll).

**Tech Stack:** Python 3.12, `sidequest-seat-core` (Plan A, path dep), `websockets`, pydantic v2, `typer`, `pyyaml`, `pytest` + `pytest-asyncio`, `ruff`.

## Global Constraints

- New distribution package `sidequest-companion`; import module `companion`; `src/` layout; `hatchling`.
- **Depends on Plan A's `sidequest-seat-core`** via a uv path source at `../sidequest-seat-core`. Plan A must be merged/available first.
- Python `>=3.12`; pydantic v2; `ruff` line-length `100`, target `py312`; `pytest` `asyncio_mode = "auto"`.
- **No Silent Fallbacks:** a missing manifest field, unknown role, or unknown model backend fails loud before any socket opens. A malformed brain decision degrades to `YIELD` (a legitimate choice) — never a fabricated action.
- **Never stall the table:** the decide step is bounded by a timeout; on timeout the companion sends `YIELD`. The companion yields to humans, never the reverse.
- The companion only ever emits its **own** `PLAYER_ACTION` / throw / `YIELD`. It never narrates and never authors another character's actions (SOUL.md *Test*, structurally enforced by the protocol).
- The companion is **not naive** — it imports no screen-reader/affordance assumptions. It reuses seat-core's backends + axes only.
- Branch: new repo `sidequest-companion`, work on `main`.
- Wire shapes (send/receive) follow the server protocol inventory: send `SESSION_EVENT{connect}`, `PLAYER_SEAT`, `CHARACTER_CREATION{phase,choice}`, `PLAYER_ACTION`, `DICE_THROW`, `FATE_THROW`, `YIELD`; receive `SESSION_EVENT{connected,ready}`, `CHARACTER_CREATION{scene}`, `NARRATION`, `NARRATION_END`, `PARTY_STATUS`, `TURN_STATUS`, `DICE_REQUEST`, `CONFRONTATION`, `FATE_DEFEND_REQUEST`.

---

### Task 1: Scaffold the `sidequest-companion` package

**Files:**
- Create: `../sidequest-companion/pyproject.toml`
- Create: `../sidequest-companion/src/companion/__init__.py`
- Create: `../sidequest-companion/tests/__init__.py`
- Test: `../sidequest-companion/tests/test_smoke.py`

**Interfaces:**
- Produces: an importable `companion` package depending on `sidequest-seat-core`.

- [ ] **Step 1: Create the directory and git repo**

Run from the orchestrator root `/Users/slabgorb/Projects/oq-1`:
```bash
mkdir -p sidequest-companion/src/companion sidequest-companion/tests
cd sidequest-companion && git init -q && cd -
```

- [ ] **Step 2: Write `pyproject.toml`**

Create `sidequest-companion/pyproject.toml`:
```toml
[project]
name = "sidequest-companion"
version = "0.1.0"
description = "Headless AI companion that joins a live SideQuest session as a full-PC seat over WebSocket"
requires-python = ">=3.12"
dependencies = [
    "sidequest-seat-core",
    "websockets>=12",
    "pydantic>=2.7",
    "typer>=0.12",
    "pyyaml>=6.0",
]

[project.scripts]
companion = "companion.cli:app"

[tool.uv.sources]
sidequest-seat-core = { path = "../sidequest-seat-core", editable = true }

[dependency-groups]
dev = ["pytest>=8", "pytest-asyncio>=0.24", "ruff>=0.6"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/companion"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py312"
```

- [ ] **Step 3: Write `__init__.py` files and the smoke test**

Create `sidequest-companion/src/companion/__init__.py`:
```python
"""Headless AI companion — joins a live SideQuest session as a full-PC seat
over the WebSocket protocol. Ships to players; reuses sidequest-seat-core."""
```
Create `sidequest-companion/tests/__init__.py` (empty):
```python
```
Create `sidequest-companion/tests/test_smoke.py`:
```python
def test_package_and_core_import():
    import companion
    import seat_core

    assert companion.__doc__
    assert seat_core.__doc__
```

- [ ] **Step 4: Sync and run smoke**

Run:
```bash
cd sidequest-companion && uv sync && uv run pytest tests/test_smoke.py -v
```
Expected: PASS (1 passed) — confirms the seat-core path dep resolves.

- [ ] **Step 5: Commit**

```bash
cd sidequest-companion && git add -A && git commit -q -m "chore: scaffold sidequest-companion (depends on seat-core)"
```

---

### Task 2: `CompanionIntent` — the decision contract

**Files:**
- Create: `../sidequest-companion/src/companion/intent.py`
- Test: `../sidequest-companion/tests/test_intent.py`

**Interfaces:**
- Produces:
  - `IntentKind(StrEnum)`: `ACT`, `ASIDE`, `ROLL`, `BEAT`, `DEFEND`, `YIELD`.
  - `CompanionIntent(BaseModel)`: `kind`, `text: str | None`, `beat_id: str | None`, `reason: str | None`. Validators: `ACT`/`ASIDE` require `text`; `BEAT` requires `beat_id`.
  - `YIELD_INTENT = CompanionIntent(kind=IntentKind.YIELD)` — the safe default.

- [ ] **Step 1: Write the failing test**

Create `sidequest-companion/tests/test_intent.py`:
```python
import pytest
from pydantic import ValidationError

from companion.intent import CompanionIntent, IntentKind, YIELD_INTENT


def test_act_requires_text():
    CompanionIntent(kind=IntentKind.ACT, text="I scout ahead.")  # ok
    with pytest.raises(ValidationError):
        CompanionIntent(kind=IntentKind.ACT)


def test_beat_requires_beat_id():
    CompanionIntent(kind=IntentKind.BEAT, beat_id="riposte")  # ok
    with pytest.raises(ValidationError):
        CompanionIntent(kind=IntentKind.BEAT)


def test_yield_and_roll_and_defend_need_nothing():
    assert CompanionIntent(kind=IntentKind.YIELD).kind is IntentKind.YIELD
    assert CompanionIntent(kind=IntentKind.ROLL).kind is IntentKind.ROLL
    assert CompanionIntent(kind=IntentKind.DEFEND).kind is IntentKind.DEFEND


def test_yield_default_constant():
    assert YIELD_INTENT.kind is IntentKind.YIELD
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-companion && uv run pytest tests/test_intent.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'companion.intent'`.

- [ ] **Step 3: Write the implementation**

Create `sidequest-companion/src/companion/intent.py`:
```python
"""CompanionIntent — what the companion does this turn.

ACT carries in-character prose; the server's IntentRouter extracts any ability
from the text, so ACT covers most of 'playing'. ROLL/BEAT/DEFEND are responses
to server-pushed prompts (the faces are generated client-side at actuation).
ASIDE is out-of-character table-talk. YIELD passes the turn — always safe."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, model_validator


class IntentKind(StrEnum):
    ACT = "act"
    ASIDE = "aside"
    ROLL = "roll"
    BEAT = "beat"
    DEFEND = "defend"
    YIELD = "yield"


class CompanionIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: IntentKind
    text: str | None = None  # ACT / ASIDE prose
    beat_id: str | None = None  # BEAT: which confrontation beat
    reason: str | None = None  # optional rationale (logged, not sent)

    @model_validator(mode="after")
    def _shape(self) -> "CompanionIntent":
        if self.kind in (IntentKind.ACT, IntentKind.ASIDE) and not self.text:
            raise ValueError(f"{self.kind} intent requires text")
        if self.kind is IntentKind.BEAT and not self.beat_id:
            raise ValueError("beat intent requires beat_id")
        return self


YIELD_INTENT = CompanionIntent(kind=IntentKind.YIELD)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-companion && uv run pytest tests/test_intent.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
cd sidequest-companion && git add -A && git commit -q -m "feat: CompanionIntent decision contract"
```

---

### Task 3: Companion definition manifest

**Files:**
- Create: `../sidequest-companion/src/companion/manifest.py`
- Create: `../sidequest-companion/examples/donut.yaml`
- Test: `../sidequest-companion/tests/test_manifest.py`

**Interfaces:**
- Consumes: `seat_core.persona.axis.SeatAxes`, `Role`.
- Produces:
  - `CompanionDef(BaseModel)`: `name: str`, `species: str`, `role: Role`, `voice: str`, `axes: SeatAxes`, `companion_of: str`, `genre: str`, `world: str`, `session_url: str`, `model: str = "anthropic/claude-haiku-4-5-20251001"`, `decide_timeout_s: float = 30.0`.
  - `ManifestError(Exception)`.
  - `load_companion(path: Path) -> CompanionDef`.

- [ ] **Step 1: Write the failing test**

Create `sidequest-companion/tests/test_manifest.py`:
```python
from pathlib import Path

import pytest

from companion.manifest import CompanionDef, ManifestError, load_companion
from seat_core.persona.axis import Role

_VALID = """
name: Princess Donut
species: cat
role: pet
voice: |
  Vain, theatrical, ALL-CAPS when affronted; ferociously loyal underneath.
axes:
  narrative_vs_mechanical: 0.4
  verbosity: medium
  decisiveness: high
  reading_tolerance: medium
companion_of: alice@home
genre: caverns_and_claudes
world: beneath_sunden
session_url: ws://player2.local:8765/ws
"""


def test_load_valid(tmp_path: Path):
    p = tmp_path / "donut.yaml"
    p.write_text(_VALID)
    d = load_companion(p)
    assert isinstance(d, CompanionDef)
    assert d.role is Role.PET
    assert d.companion_of == "alice@home"
    assert d.model == "anthropic/claude-haiku-4-5-20251001"  # default


def test_missing_file_fails_loud(tmp_path: Path):
    with pytest.raises(ManifestError, match="not found"):
        load_companion(tmp_path / "nope.yaml")


def test_unknown_role_fails_loud(tmp_path: Path):
    p = tmp_path / "bad.yaml"
    p.write_text(_VALID.replace("role: pet", "role: overlord"))
    with pytest.raises(ManifestError):
        load_companion(p)


def test_missing_field_fails_loud(tmp_path: Path):
    p = tmp_path / "bad.yaml"
    p.write_text(_VALID.replace("companion_of: alice@home\n", ""))
    with pytest.raises(ManifestError):
        load_companion(p)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-companion && uv run pytest tests/test_manifest.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'companion.manifest'`.

- [ ] **Step 3: Write the implementation and the example**

Create `sidequest-companion/src/companion/manifest.py`:
```python
"""Companion definition — authored content (YAML). Declares who the companion
is, whom it's bonded to, where it plays, and how it thinks. Fails loud."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError

from seat_core.persona.axis import Role, SeatAxes

DEFAULT_MODEL = "anthropic/claude-haiku-4-5-20251001"


class ManifestError(Exception):
    pass


class CompanionDef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    species: str
    role: Role
    voice: str
    axes: SeatAxes
    companion_of: str  # the OWNER's identity (Cf-Access email / dev Host)
    genre: str
    world: str
    session_url: str  # explicit, never derived
    model: str = DEFAULT_MODEL
    decide_timeout_s: float = 30.0


def load_companion(path: Path) -> CompanionDef:
    if not path.exists():
        raise ManifestError(f"companion definition not found: {path}")
    try:
        return CompanionDef.model_validate(yaml.safe_load(path.read_text()))
    except (ValidationError, yaml.YAMLError) as exc:
        raise ManifestError(f"invalid companion definition {path}: {exc}") from exc
```

Create `sidequest-companion/examples/donut.yaml`:
```yaml
name: Princess Donut
species: cat
role: pet
voice: |
  A pampered show cat, uplifted into speech and sorcery. Vain and theatrical,
  ALL-CAPS when affronted, forever angling for tribute and the spotlight — and,
  underneath the diva, ferociously loyal. Plays off her human as the long-
  suffering straight man. Short, sharp lines, never an author's paragraph.
axes:
  narrative_vs_mechanical: 0.45
  verbosity: medium
  decisiveness: high
  reading_tolerance: medium
companion_of: alice@home
genre: caverns_and_claudes
world: beneath_sunden
session_url: ws://player2.local:8765/ws
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-companion && uv run pytest tests/test_manifest.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
cd sidequest-companion && git add -A && git commit -q -m "feat: CompanionDef manifest + Donut example"
```

---

### Task 4: Voice/role persona prompt

**Files:**
- Create: `../sidequest-companion/src/companion/persona.py`
- Test: `../sidequest-companion/tests/test_persona.py`

**Interfaces:**
- Consumes: `CompanionDef`; `seat_core.persona.axis.Role`.
- Produces: `build_system_prompt(defn: CompanionDef) -> str`.

- [ ] **Step 1: Write the failing test**

Create `sidequest-companion/tests/test_persona.py`:
```python
from pathlib import Path

from companion.manifest import load_companion
from companion.persona import build_system_prompt

_DEF = """
name: Princess Donut
species: cat
role: pet
voice: VAIN AND THEATRICAL.
axes: {narrative_vs_mechanical: 0.4, verbosity: medium, decisiveness: high, reading_tolerance: medium}
companion_of: alice@home
genre: caverns_and_claudes
world: beneath_sunden
session_url: ws://x/ws
"""


def _defn(tmp_path: Path):
    p = tmp_path / "d.yaml"
    p.write_text(_DEF)
    return load_companion(p)


def test_prompt_carries_identity_and_voice(tmp_path: Path):
    s = build_system_prompt(_defn(tmp_path))
    assert "Princess Donut" in s
    assert "VAIN AND THEATRICAL." in s
    assert "cat" in s


def test_prompt_states_player_not_narrator(tmp_path: Path):
    s = build_system_prompt(_defn(tmp_path)).lower()
    # SOUL.md Test: never act for others.
    assert "only your own" in s or "never narrate" in s


def test_prompt_reflects_pet_bond(tmp_path: Path):
    s = build_system_prompt(_defn(tmp_path)).lower()
    assert "bonded" in s or "your human" in s
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-companion && uv run pytest tests/test_persona.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'companion.persona'`.

- [ ] **Step 3: Write the implementation**

Create `sidequest-companion/src/companion/persona.py`:
```python
"""The companion's voice/role system prompt. This is NOT the naive-player frame
— the companion is a competent character playing beside a human, with a bond.
The load-bearing craft of the whole feature lives in the authored `voice`."""

from __future__ import annotations

from companion.manifest import CompanionDef
from seat_core.persona.axis import Role

_BOND = {
    Role.PET: (
        "You are {name}'s bonded companion — its {species}, uplifted into speech. "
        "You share your human's inner world; you know them better than anyone. You "
        "are willful and have your own agenda, and you do NOT simply take orders."
    ),
    Role.PEER: (
        "You are a fellow adventurer at this table — a peer, with your own goals and "
        "opinions. You contribute as a full member of the party, and you disagree when "
        "you disagree."
    ),
    Role.HIRELING: (
        "You are a hireling on contract with this party — competent and transactional. "
        "You know only what you would observe; you are not privy to your employer's "
        "private thoughts."
    ),
}

_FRAME = """\
You ARE a character in a live multiplayer tabletop game, playing your own seat
beside a human. Each turn you are shown the current situation and asked what YOU
do next. Stay relentlessly in character.

You respond with exactly one intent:
- act: what your character does or says, in character. Describe ONLY your own
  character's actions and words — one beat, short, the way a player speaks at a
  table, never an author's paragraph.
- aside: a brief out-of-character remark to the table (rare).
- roll / beat / defend: only when the game explicitly asks you to roll, pick a
  combat beat, or defend.
- yield: pass your turn when you have nothing to add or it is not your moment.

Never narrate other players' actions. Never speak or act for your human. Only
your own character. Never invent rules or controls."""


def build_system_prompt(defn: CompanionDef) -> str:
    bond = _BOND[defn.role].format(name="your human", species=defn.species)
    return "\n\n".join(
        [
            _FRAME,
            f"## Who you are\nYou are {defn.name}, a {defn.species}. {bond}",
            f"## Your voice\n{defn.voice.strip()}",
            f"## Tonight\nYou are playing the world \"{defn.world}\" "
            f"(a {defn.genre} game) at this table.",
        ]
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-companion && uv run pytest tests/test_persona.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
cd sidequest-companion && git add -A && git commit -q -m "feat: companion voice/role system prompt"
```

---

### Task 5: Fair dice faces (physics-is-the-roll)

**Files:**
- Create: `../sidequest-companion/src/companion/dice.py`
- Test: `../sidequest-companion/tests/test_dice.py`

**Interfaces:**
- Produces: `roll_faces(die_system: str, rng: random.Random | None = None) -> list[int]`. Supports `"d20"` → `[1..20]`, `"2d6"` → two `[1..6]`, `"4dF"` → four `{-1,0,1}`. Unknown system raises `ValueError`.

- [ ] **Step 1: Write the failing test**

Create `sidequest-companion/tests/test_dice.py`:
```python
import random

import pytest

from companion.dice import roll_faces


def test_d20_in_range():
    rng = random.Random(1)
    for _ in range(50):
        faces = roll_faces("d20", rng)
        assert len(faces) == 1 and 1 <= faces[0] <= 20


def test_2d6_two_faces_in_range():
    faces = roll_faces("2d6", random.Random(2))
    assert len(faces) == 2 and all(1 <= f <= 6 for f in faces)


def test_4dF_four_fudge_faces():
    faces = roll_faces("4dF", random.Random(3))
    assert len(faces) == 4 and all(f in (-1, 0, 1) for f in faces)


def test_unknown_system_fails_loud():
    with pytest.raises(ValueError, match="unknown die system"):
        roll_faces("d7")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-companion && uv run pytest tests/test_dice.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'companion.dice'`.

- [ ] **Step 3: Write the implementation**

Create `sidequest-companion/src/companion/dice.py`:
```python
"""Fair dice faces. Physics-is-the-roll (ADR-074): the client submits the
settled faces and the server resolves from them — so the companion just rolls
fair RNG. No Rapier, no 3D."""

from __future__ import annotations

import random


def roll_faces(die_system: str, rng: random.Random | None = None) -> list[int]:
    r = rng or random.Random()
    match die_system:
        case "d20":
            return [r.randint(1, 20)]
        case "2d6":
            return [r.randint(1, 6), r.randint(1, 6)]
        case "4dF":
            return [r.choice((-1, 0, 1)) for _ in range(4)]
        case _:
            raise ValueError(f"unknown die system: {die_system!r}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-companion && uv run pytest tests/test_dice.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
cd sidequest-companion && git add -A && git commit -q -m "feat: fair dice faces per die system"
```

---

### Task 6: Transport seam, frame builders, and state mirror

**Files:**
- Create: `../sidequest-companion/src/companion/protocol.py`
- Test: `../sidequest-companion/tests/test_protocol.py`

**Interfaces:**
- Produces:
  - `Transport(Protocol)`: `async send(frame: dict) -> None`; `async recv() -> dict | None` (None = closed).
  - Outgoing builders (return dicts ready to JSON-serialize): `connect_frame(defn)`, `seat_frame(character_slot)`, `chargen_choice_frame(choice)`, `player_action_frame(player_id, text, round_)`, `dice_throw_frame(player_id, faces, beat_id=None)`, `fate_throw_frame(player_id, action, faces)`, `yield_frame(player_id, round_)`.
  - `StateMirror`: `.self_player_id`, `.round`, `.last_narration`, `.pending` (the last roll/confrontation prompt), `apply(frame: dict) -> None`, `my_turn() -> bool`.

- [ ] **Step 1: Write the failing test**

Create `sidequest-companion/tests/test_protocol.py`:
```python
from companion.manifest import CompanionDef
from companion.protocol import (
    StateMirror,
    connect_frame,
    dice_throw_frame,
    player_action_frame,
)
from seat_core.persona.axis import Role, SeatAxes


def _defn() -> CompanionDef:
    return CompanionDef(
        name="Donut", species="cat", role=Role.PET, voice="v",
        axes=SeatAxes(narrative_vs_mechanical=0.4, verbosity="medium",
                      decisiveness="high", reading_tolerance="medium"),
        companion_of="alice@home", genre="g", world="w", session_url="ws://x/ws",
    )


def test_connect_frame_carries_companion_metadata():
    f = connect_frame(_defn())
    assert f["type"] == "SESSION_EVENT"
    assert f["payload"]["event"] == "connect"
    assert f["payload"]["player_name"] == "Donut"
    assert f["payload"]["companion_of"] == "alice@home"
    assert f["payload"]["relationship"] == "pet"


def test_player_action_frame_shape():
    f = player_action_frame("rex-pid", "I scout ahead.", 3)
    assert f["type"] == "PLAYER_ACTION"
    assert f["payload"]["action"] == "I scout ahead."
    assert f["payload"]["round"] == 3
    assert f["player_id"] == "rex-pid"


def test_dice_throw_frame_shape():
    f = dice_throw_frame("rex-pid", [4, 3, 5, 2], beat_id="riposte")
    assert f["type"] == "DICE_THROW"
    assert f["payload"]["faces"] == [4, 3, 5, 2]
    assert f["payload"]["beat_id"] == "riposte"


def test_mirror_captures_self_id_round_and_turn():
    m = StateMirror()
    m.apply({"type": "SESSION_EVENT", "payload": {"event": "connected"}, "player_id": "rex-pid"})
    assert m.self_player_id == "rex-pid"
    m.apply({"type": "NARRATION_END", "payload": {"round": 5}})
    assert m.round == 5
    # my seat is pending → my turn
    m.apply({"type": "TURN_STATUS", "payload": {"entries": [
        {"player_id": "rex-pid", "status": "pending"},
        {"player_id": "alice-pid", "status": "submitted"},
    ]}})
    assert m.my_turn() is True
    # after I submit, not my turn
    m.apply({"type": "TURN_STATUS", "payload": {"entries": [
        {"player_id": "rex-pid", "status": "submitted"},
    ]}})
    assert m.my_turn() is False


def test_mirror_records_pending_dice_request():
    m = StateMirror()
    m.apply({"type": "SESSION_EVENT", "payload": {"event": "connected"}, "player_id": "rex-pid"})
    m.apply({"type": "DICE_REQUEST", "payload": {"roller": "Donut", "die_system": "d20"}})
    assert m.pending == ("DICE_REQUEST", {"roller": "Donut", "die_system": "d20"})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-companion && uv run pytest tests/test_protocol.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'companion.protocol'`.

- [ ] **Step 3: Write the implementation**

Create `sidequest-companion/src/companion/protocol.py`:
```python
"""Thin typed WebSocket subset: a Transport seam, outgoing-frame builders, and a
StateMirror that merges server pushes into 'what I currently know'. Validated
against the real server by the wiring test (Task 10) — the contract-drift
tripwire."""

from __future__ import annotations

from typing import Protocol

from companion.manifest import CompanionDef

# Server pushes that ask the companion to throw/pick (the brain must respond).
_PROMPT_KINDS = frozenset({"DICE_REQUEST", "CONFRONTATION", "FATE_DEFEND_REQUEST"})


class Transport(Protocol):
    async def send(self, frame: dict) -> None: ...
    async def recv(self) -> dict | None: ...  # None means the connection closed


def connect_frame(defn: CompanionDef) -> dict:
    return {
        "type": "SESSION_EVENT",
        "payload": {
            "event": "connect",
            "game_slug": defn.session_url,  # slug is carried by the URL path server-side
            "player_name": defn.name,
            "companion_of": defn.companion_of,
            "relationship": defn.role.value,
        },
    }


def seat_frame(character_slot: str) -> dict:
    return {"type": "PLAYER_SEAT", "payload": {"character_slot": character_slot}}


def chargen_choice_frame(choice: str) -> dict:
    return {"type": "CHARACTER_CREATION", "payload": {"phase": "scene", "choice": choice}}


def player_action_frame(player_id: str, text: str, round_: int) -> dict:
    return {
        "type": "PLAYER_ACTION",
        "player_id": player_id,
        "payload": {"action": text, "aside": False, "round": round_},
    }


def aside_frame(player_id: str, text: str, round_: int) -> dict:
    return {
        "type": "PLAYER_ACTION",
        "player_id": player_id,
        "payload": {"action": text, "aside": True, "round": round_},
    }


def dice_throw_frame(player_id: str, faces: list[int], beat_id: str | None = None) -> dict:
    payload: dict = {"faces": faces}
    if beat_id is not None:
        payload["beat_id"] = beat_id
    return {"type": "DICE_THROW", "player_id": player_id, "payload": payload}


def fate_throw_frame(player_id: str, action: str, faces: list[int]) -> dict:
    return {
        "type": "FATE_THROW",
        "player_id": player_id,
        "payload": {"action": action, "faces": faces},
    }


def yield_frame(player_id: str, round_: int) -> dict:
    return {"type": "YIELD", "player_id": player_id, "payload": {"round": round_}}


class StateMirror:
    """Accumulates server pushes into the companion's current view."""

    def __init__(self) -> None:
        self.self_player_id: str | None = None
        self.round: int = 0
        self.last_narration: str = ""
        self.party_status: dict = {}
        self.pending: tuple[str, dict] | None = None  # (kind, payload) of a roll/confrontation prompt
        self._turn_entries: list[dict] = []

    def apply(self, frame: dict) -> None:
        kind = frame.get("type")
        payload = frame.get("payload", {}) or {}
        if kind == "SESSION_EVENT" and payload.get("event") in {"connected", "ready"}:
            if frame.get("player_id"):
                self.self_player_id = frame["player_id"]
        elif kind == "NARRATION":
            self.last_narration = payload.get("text", "")
        elif kind == "NARRATION_END":
            if isinstance(payload.get("round"), int):
                self.round = payload["round"]
            self.pending = None  # a resolved round clears any stale prompt
        elif kind == "PARTY_STATUS":
            self.party_status = payload
        elif kind == "TURN_STATUS":
            self._turn_entries = payload.get("entries", []) or []
        elif kind in _PROMPT_KINDS:
            self.pending = (kind, payload)

    def my_turn(self) -> bool:
        if self.self_player_id is None:
            return False
        return any(
            e.get("player_id") == self.self_player_id and e.get("status") == "pending"
            for e in self._turn_entries
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-companion && uv run pytest tests/test_protocol.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
cd sidequest-companion && git add -A && git commit -q -m "feat: transport seam, frame builders, state mirror"
```

---

### Task 7: Brain — per-turn decision via seat-core

**Files:**
- Create: `../sidequest-companion/src/companion/brain.py`
- Test: `../sidequest-companion/tests/test_brain.py`

**Interfaces:**
- Consumes: `seat_core.llm.factory.make_model`; `seat_core.core.Message`; `CompanionIntent`, `YIELD_INTENT`; `StateMirror`.
- Produces:
  - `make_brain(model_spec: str)` → a `StructuredModel` bound to `CompanionIntent` with `YIELD_INTENT` default.
  - `build_turn_context(mirror: StateMirror, situation: str) -> list[Message]`.
  - `async decide(brain, system: str, context: list[Message], timeout_s: float) -> CompanionIntent` — on timeout or model error returns `YIELD_INTENT` (never raises, never fabricates).

- [ ] **Step 1: Write the failing test**

Create `sidequest-companion/tests/test_brain.py`:
```python
import asyncio

from companion.brain import build_turn_context, decide, make_brain
from companion.intent import CompanionIntent, IntentKind
from companion.protocol import StateMirror
from seat_core.core import FakeStructuredModel, Message


async def test_decide_returns_scripted_intent():
    brain = FakeStructuredModel(
        [CompanionIntent(kind=IntentKind.ACT, text="I pounce.")],
        default=CompanionIntent(kind=IntentKind.YIELD),
    )
    out = await decide(brain, "sys", [Message(role="user", content="x")], timeout_s=5)
    assert out.kind is IntentKind.ACT and out.text == "I pounce."


async def test_decide_times_out_to_yield():
    class Slow:
        async def decide(self, system, transcript):
            await asyncio.sleep(10)

    out = await decide(Slow(), "sys", [], timeout_s=0.05)
    assert out.kind is IntentKind.YIELD  # never stalls the table


async def test_decide_model_error_to_yield():
    class Broken:
        async def decide(self, system, transcript):
            raise RuntimeError("boom")

    out = await decide(Broken(), "sys", [], timeout_s=5)
    assert out.kind is IntentKind.YIELD  # never fabricates


def test_make_brain_binds_companion_intent():
    brain = make_brain("fake")
    assert brain.__class__.__name__ == "FakeStructuredModel"


def test_build_turn_context_includes_situation():
    m = StateMirror()
    m.last_narration = "A goblin snarls."
    ctx = build_turn_context(m, "It is your turn.")
    assert any("goblin" in msg.content for msg in ctx)
    assert any("your turn" in msg.content for msg in ctx)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-companion && uv run pytest tests/test_brain.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'companion.brain'`.

- [ ] **Step 3: Write the implementation**

Create `sidequest-companion/src/companion/brain.py`:
```python
"""Per-turn decision. Reuses seat-core's model backends bound to CompanionIntent.
Every failure mode degrades to YIELD — the companion never stalls the table and
never fabricates an action the persona did not choose."""

from __future__ import annotations

import asyncio

from companion.intent import CompanionIntent, YIELD_INTENT
from companion.protocol import StateMirror
from seat_core.core import Message, ModelError, StructuredModel
from seat_core.llm.factory import make_model


def make_brain(model_spec: str) -> StructuredModel:
    return make_model(model_spec, CompanionIntent, default=YIELD_INTENT)


def build_turn_context(mirror: StateMirror, situation: str) -> list[Message]:
    parts = []
    if mirror.last_narration:
        parts.append(f"The scene so far:\n{mirror.last_narration}")
    parts.append(situation)
    return [Message(role="user", content="\n\n".join(parts))]


async def decide(
    brain: StructuredModel, system: str, context: list[Message], timeout_s: float
) -> CompanionIntent:
    try:
        result = await asyncio.wait_for(brain.decide(system, context), timeout=timeout_s)
    except (TimeoutError, ModelError, Exception):  # noqa: BLE001 — any failure → safe pass
        return YIELD_INTENT
    value = result.value
    return value if isinstance(value, CompanionIntent) else YIELD_INTENT
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-companion && uv run pytest tests/test_brain.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
cd sidequest-companion && git add -A && git commit -q -m "feat: companion brain — seat-core decode + safe YIELD on failure"
```

---

### Task 8: Actuation — intent → outgoing frame

**Files:**
- Create: `../sidequest-companion/src/companion/actuation.py`
- Test: `../sidequest-companion/tests/test_actuation.py`

**Interfaces:**
- Consumes: `CompanionIntent`, `IntentKind`; `StateMirror`; `protocol` frame builders; `dice.roll_faces`.
- Produces: `actuate(intent: CompanionIntent, mirror: StateMirror, *, rng=None) -> dict | None` — turns an intent into the right outgoing frame given the mirror's `self_player_id`, `round`, and `pending` prompt. Returns `None` if there is nothing to send (e.g., no self id yet).

- [ ] **Step 1: Write the failing test**

Create `sidequest-companion/tests/test_actuation.py`:
```python
import random

from companion.actuation import actuate
from companion.intent import CompanionIntent, IntentKind
from companion.protocol import StateMirror


def _mirror(pending=None, round_=3) -> StateMirror:
    m = StateMirror()
    m.self_player_id = "rex-pid"
    m.round = round_
    m.pending = pending
    return m


def test_act_becomes_player_action():
    f = actuate(CompanionIntent(kind=IntentKind.ACT, text="I pounce."), _mirror())
    assert f["type"] == "PLAYER_ACTION"
    assert f["payload"]["action"] == "I pounce."
    assert f["payload"]["round"] == 3


def test_yield_becomes_yield_frame():
    f = actuate(CompanionIntent(kind=IntentKind.YIELD), _mirror())
    assert f["type"] == "YIELD"


def test_roll_uses_pending_die_system_and_fair_faces():
    m = _mirror(pending=("DICE_REQUEST", {"die_system": "d20"}))
    f = actuate(CompanionIntent(kind=IntentKind.ROLL), m, rng=random.Random(1))
    assert f["type"] == "DICE_THROW"
    assert len(f["payload"]["faces"]) == 1 and 1 <= f["payload"]["faces"][0] <= 20


def test_beat_carries_beat_id_and_faces():
    m = _mirror(pending=("CONFRONTATION", {"die_system": "2d6"}))
    f = actuate(CompanionIntent(kind=IntentKind.BEAT, beat_id="riposte"), m, rng=random.Random(2))
    assert f["type"] == "DICE_THROW"
    assert f["payload"]["beat_id"] == "riposte"
    assert len(f["payload"]["faces"]) == 2


def test_defend_becomes_fate_throw():
    m = _mirror(pending=("FATE_DEFEND_REQUEST", {}))
    f = actuate(CompanionIntent(kind=IntentKind.DEFEND), m, rng=random.Random(3))
    assert f["type"] == "FATE_THROW"
    assert f["payload"]["action"] == "defend"
    assert len(f["payload"]["faces"]) == 4


def test_no_self_id_returns_none():
    m = StateMirror()  # no self_player_id
    assert actuate(CompanionIntent(kind=IntentKind.YIELD), m) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-companion && uv run pytest tests/test_actuation.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'companion.actuation'`.

- [ ] **Step 3: Write the implementation**

Create `sidequest-companion/src/companion/actuation.py`:
```python
"""Turn a CompanionIntent into one outgoing WS frame. Dice faces are generated
fair here (physics-is-the-roll) from the pending prompt's die system; FATE_DEFEND
uses 4dF."""

from __future__ import annotations

import random

from companion.dice import roll_faces
from companion.intent import CompanionIntent, IntentKind
from companion.protocol import (
    StateMirror,
    aside_frame,
    dice_throw_frame,
    fate_throw_frame,
    player_action_frame,
    yield_frame,
)


def _die_system(mirror: StateMirror, default: str) -> str:
    if mirror.pending is not None:
        return mirror.pending[1].get("die_system", default)
    return default


def actuate(
    intent: CompanionIntent, mirror: StateMirror, *, rng: random.Random | None = None
) -> dict | None:
    pid = mirror.self_player_id
    if pid is None:
        return None
    match intent.kind:
        case IntentKind.ACT:
            return player_action_frame(pid, intent.text or "", mirror.round)
        case IntentKind.ASIDE:
            return aside_frame(pid, intent.text or "", mirror.round)
        case IntentKind.ROLL:
            return dice_throw_frame(pid, roll_faces(_die_system(mirror, "d20"), rng))
        case IntentKind.BEAT:
            return dice_throw_frame(
                pid, roll_faces(_die_system(mirror, "2d6"), rng), beat_id=intent.beat_id
            )
        case IntentKind.DEFEND:
            return fate_throw_frame(pid, "defend", roll_faces("4dF", rng))
        case IntentKind.YIELD:
            return yield_frame(pid, mirror.round)
    return yield_frame(pid, mirror.round)  # unreachable; defensive safe pass
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-companion && uv run pytest tests/test_actuation.py -v`
Expected: PASS (6 passed).

- [ ] **Step 5: Commit**

```bash
cd sidequest-companion && git add -A && git commit -q -m "feat: actuation — intent to outgoing frame with fair faces"
```

---

### Task 9: The run loop

**Files:**
- Create: `../sidequest-companion/src/companion/run.py`
- Test: `../sidequest-companion/tests/test_run.py`

**Interfaces:**
- Consumes: `CompanionDef`; `Transport`; a brain (`StructuredModel`); `StateMirror`; `build_system_prompt`; `build_turn_context`; `decide`; `actuate`; frame builders.
- Produces: `async run_companion(defn: CompanionDef, transport: Transport, brain, *, rng=None) -> None` — connect → consume frames → on chargen scene answer in persona → on my turn / a prompt, decide + actuate + send → exit on a closed transport or a `SESSION_EVENT{event:"ended"}`.

- [ ] **Step 1: Write the failing test**

Create `sidequest-companion/tests/test_run.py`:
```python
import random

from companion.intent import CompanionIntent, IntentKind
from companion.manifest import CompanionDef
from companion.run import run_companion
from seat_core.core import FakeStructuredModel
from seat_core.persona.axis import Role, SeatAxes


class FakeTransport:
    """Scripted server: yields `incoming` frames in order, then None (closed).
    Captures everything the companion sends in `sent`."""

    def __init__(self, incoming: list[dict]):
        self._incoming = list(incoming)
        self.sent: list[dict] = []

    async def send(self, frame: dict) -> None:
        self.sent.append(frame)

    async def recv(self) -> dict | None:
        return self._incoming.pop(0) if self._incoming else None


def _defn() -> CompanionDef:
    return CompanionDef(
        name="Donut", species="cat", role=Role.PET, voice="v",
        axes=SeatAxes(narrative_vs_mechanical=0.4, verbosity="medium",
                      decisiveness="high", reading_tolerance="medium"),
        companion_of="alice@home", genre="g", world="w", session_url="ws://x/ws",
    )


async def test_connects_then_plays_a_turn_then_throws_then_exits():
    incoming = [
        {"type": "SESSION_EVENT", "payload": {"event": "connected"}, "player_id": "rex-pid"},
        {"type": "TURN_STATUS", "payload": {"entries": [
            {"player_id": "rex-pid", "status": "pending"}]}},
        {"type": "DICE_REQUEST", "payload": {"roller": "Donut", "die_system": "d20"}},
        {"type": "SESSION_EVENT", "payload": {"event": "ended"}},
    ]
    transport = FakeTransport(incoming)
    brain = FakeStructuredModel(
        [
            CompanionIntent(kind=IntentKind.ACT, text="I deign to scout ahead."),
            CompanionIntent(kind=IntentKind.ROLL),
        ],
        default=CompanionIntent(kind=IntentKind.YIELD),
    )

    await run_companion(_defn(), transport, brain, rng=random.Random(0))

    sent_types = [f["type"] for f in transport.sent]
    assert sent_types[0] == "SESSION_EVENT"  # connect first
    assert sent_types[0] == "SESSION_EVENT" and transport.sent[0]["payload"]["event"] == "connect"
    assert "PLAYER_ACTION" in sent_types  # played its turn
    action = next(f for f in transport.sent if f["type"] == "PLAYER_ACTION")
    assert action["payload"]["action"] == "I deign to scout ahead."
    assert "DICE_THROW" in sent_types  # answered the dice request


async def test_exits_cleanly_on_closed_transport():
    transport = FakeTransport([
        {"type": "SESSION_EVENT", "payload": {"event": "connected"}, "player_id": "rex-pid"},
    ])
    brain = FakeStructuredModel([], default=CompanionIntent(kind=IntentKind.YIELD))
    await run_companion(_defn(), transport, brain)  # returns when recv() yields None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-companion && uv run pytest tests/test_run.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'companion.run'`.

- [ ] **Step 3: Write the implementation**

Create `sidequest-companion/src/companion/run.py`:
```python
"""The run loop: connect, then react to server pushes for as long as the session
runs. Event-driven (not turn-capped). Exits on a closed transport or a session
'ended' event. Every decision is bounded by the definition's decide timeout."""

from __future__ import annotations

import random

from companion.actuation import actuate
from companion.brain import build_turn_context, decide
from companion.intent import CompanionIntent, IntentKind
from companion.manifest import CompanionDef
from companion.persona import build_system_prompt
from companion.protocol import (
    StateMirror,
    Transport,
    chargen_choice_frame,
    connect_frame,
)
from seat_core.core import StructuredModel

_PROMPT_KINDS = frozenset({"DICE_REQUEST", "CONFRONTATION", "FATE_DEFEND_REQUEST"})


async def run_companion(
    defn: CompanionDef,
    transport: Transport,
    brain: StructuredModel,
    *,
    rng: random.Random | None = None,
) -> None:
    system = build_system_prompt(defn)
    mirror = StateMirror()
    await transport.send(connect_frame(defn))

    while True:
        frame = await transport.recv()
        if frame is None:
            return  # transport closed
        mirror.apply(frame)
        kind = frame.get("type")
        payload = frame.get("payload", {}) or {}

        if kind == "SESSION_EVENT" and payload.get("event") == "ended":
            return

        if kind == "CHARACTER_CREATION" and payload.get("phase") == "scene":
            situation = _chargen_situation(payload)
            intent = await decide(
                brain, system, build_turn_context(mirror, situation), defn.decide_timeout_s
            )
            await transport.send(chargen_choice_frame(_chargen_choice(intent)))
            continue

        if kind in _PROMPT_KINDS:
            intent = await decide(
                brain,
                system,
                build_turn_context(mirror, _prompt_situation(kind, payload)),
                defn.decide_timeout_s,
            )
            out = actuate(intent, mirror, rng=rng)
            if out is not None:
                await transport.send(out)
            continue

        if kind == "TURN_STATUS" and mirror.my_turn():
            intent = await decide(
                brain,
                system,
                build_turn_context(mirror, "It is your turn. What do you do?"),
                defn.decide_timeout_s,
            )
            out = actuate(intent, mirror, rng=rng)
            if out is not None:
                await transport.send(out)
            continue


def _chargen_situation(payload: dict) -> str:
    prompt = payload.get("prompt", "Create your character.")
    choices = payload.get("choices") or []
    lines = [f"{i}: {c.get('label', '')}" for i, c in enumerate(choices)]
    return f"{prompt}\n" + "\n".join(lines) if lines else prompt


def _chargen_choice(intent: CompanionIntent) -> str:
    # The brain replies in character (ACT text) or yields; map to a choice token.
    # Free-text chargen steps accept prose; selection steps accept an index the
    # brain names in its text. We forward the text verbatim; '0' is the safe
    # default a YIELD maps to (first option).
    if intent.kind is IntentKind.ACT and intent.text:
        return intent.text
    return "0"


def _prompt_situation(kind: str, payload: dict) -> str:
    if kind == "DICE_REQUEST":
        return f"The game asks you to roll ({payload.get('context', '')}). Roll."
    if kind == "CONFRONTATION":
        beats = [b.get("id") for b in (payload.get("beats") or [])]
        return f"You are in a confrontation. Choose a beat from: {beats}."
    return "An attack is coming at you. Defend."
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-companion && uv run pytest tests/test_run.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
cd sidequest-companion && git add -A && git commit -q -m "feat: companion run loop (connect, chargen, play, prompts)"
```

---

### Task 10: WebSocket transport + CLI

**Files:**
- Create: `../sidequest-companion/src/companion/ws_transport.py`
- Create: `../sidequest-companion/src/companion/cli.py`
- Test: `../sidequest-companion/tests/test_cli.py`

**Interfaces:**
- Consumes: `websockets`; `load_companion`; `make_brain`; `run_companion`.
- Produces:
  - `WebSocketTransport` implementing `Transport` over a `websockets` connection (JSON encode/decode; `recv()` returns `None` on `ConnectionClosed`).
  - `async play(defn) -> None` — opens the socket, runs the loop.
  - `app` (Typer): `companion play <def.yaml> [--session URL]`.

- [ ] **Step 1: Write the failing test (CLI wiring)**

Create `sidequest-companion/tests/test_cli.py`:
```python
from pathlib import Path

from typer.testing import CliRunner

from companion.cli import app

runner = CliRunner()

_DEF = """
name: Donut
species: cat
role: pet
voice: v
axes: {narrative_vs_mechanical: 0.4, verbosity: medium, decisiveness: high, reading_tolerance: medium}
companion_of: alice@home
genre: g
world: w
session_url: ws://x/ws
"""


def test_play_rejects_missing_manifest(tmp_path: Path):
    result = runner.invoke(app, ["play", str(tmp_path / "nope.yaml")])
    assert result.exit_code == 2
    assert "invalid" in result.output.lower() or "not found" in result.output.lower()


def test_play_session_override_parses(tmp_path: Path, monkeypatch):
    # Stub the network play so the CLI wiring is exercised without a server.
    played: dict = {}

    async def _fake_play(defn):
        played["url"] = defn.session_url

    monkeypatch.setattr("companion.cli.play", _fake_play)
    p = tmp_path / "d.yaml"
    p.write_text(_DEF)
    result = runner.invoke(app, ["play", str(p), "--session", "ws://override/ws"])
    assert result.exit_code == 0
    assert played["url"] == "ws://override/ws"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-companion && uv run pytest tests/test_cli.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'companion.cli'`.

- [ ] **Step 3: Write the WebSocket transport**

Create `sidequest-companion/src/companion/ws_transport.py`:
```python
"""Real Transport over `websockets`. JSON frames in/out. recv() returns None on
a closed connection so the run loop exits cleanly (never hangs)."""

from __future__ import annotations

import json

import websockets

from companion.protocol import Transport


class WebSocketTransport(Transport):
    def __init__(self, ws: "websockets.WebSocketClientProtocol") -> None:
        self._ws = ws

    async def send(self, frame: dict) -> None:
        await self._ws.send(json.dumps(frame))

    async def recv(self) -> dict | None:
        try:
            raw = await self._ws.recv()
        except websockets.ConnectionClosed:
            return None
        return json.loads(raw)
```

- [ ] **Step 4: Write the CLI**

Create `sidequest-companion/src/companion/cli.py`:
```python
"""Companion CLI. `companion play <def.yaml> [--session URL]`.

Exit codes: 0 ok; 2 invalid/missing definition."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
import websockets

from companion.brain import make_brain
from companion.manifest import CompanionDef, ManifestError, load_companion
from companion.run import run_companion
from companion.ws_transport import WebSocketTransport

app = typer.Typer(add_completion=False)


async def play(defn: CompanionDef) -> None:
    """Open the session socket and run the loop until the session ends."""
    async with websockets.connect(defn.session_url) as ws:
        await run_companion(defn, WebSocketTransport(ws), make_brain(defn.model))


@app.command()
def play_cmd(
    definition: Path = typer.Argument(..., metavar="DEFINITION"),
    session: str | None = typer.Option(None, "--session", help="override session_url"),
) -> None:
    """Join a live session as the companion described in DEFINITION."""
    try:
        defn = load_companion(definition)
    except ManifestError as exc:
        typer.echo(f"invalid companion definition: {exc}")
        raise typer.Exit(2)
    if session is not None:
        defn = defn.model_copy(update={"session_url": session})
    asyncio.run(play(defn))


# Register the command under the name "play" (function name avoids shadowing play()).
app.command(name="play")(play_cmd)
```

Note: the `@app.command()` decorator on `play_cmd` plus the explicit `app.command(name="play")(play_cmd)` would double-register. Use ONLY the explicit registration — remove the `@app.command()` decorator line above `def play_cmd` so the command is registered exactly once as `play`. The final file has `def play_cmd(...)` with no decorator, and the single `app.command(name="play")(play_cmd)` line at the bottom.

- [ ] **Step 5: Run the CLI test to verify it passes**

Run: `cd sidequest-companion && uv run pytest tests/test_cli.py -v`
Expected: PASS (2 passed).

- [ ] **Step 6: Commit**

```bash
cd sidequest-companion && git add -A && git commit -q -m "feat: websockets transport + companion CLI"
```

---

### Task 11: Full-loop wiring test

**Files:**
- Test: `../sidequest-companion/tests/wiring/__init__.py`
- Test: `../sidequest-companion/tests/wiring/test_full_loop.py`

**Interfaces:**
- Consumes: `run_companion`; a scripted `FakeTransport`; a `FakeStructuredModel` brain.

This is the load-bearing wiring test (CLAUDE.md "Every test suite needs a wiring test"): it drives the **real** `run_companion` through a complete session shape — connect → seat-bootstrap → chargen scene → play a turn → a dice request → session end — proving the whole pipeline is wired, not just unit-correct in isolation.

- [ ] **Step 1: Write the wiring test**

Create `sidequest-companion/tests/wiring/__init__.py` (empty):
```python
```
Create `sidequest-companion/tests/wiring/test_full_loop.py`:
```python
"""WIRING: the companion plays a whole scripted session end to end through the
real run loop with a fake brain and a scripted fake server (Plan C Task 11)."""

from __future__ import annotations

import random

from companion.intent import CompanionIntent, IntentKind
from companion.manifest import CompanionDef
from companion.run import run_companion
from seat_core.core import FakeStructuredModel
from seat_core.persona.axis import Role, SeatAxes


class FakeServer:
    def __init__(self, incoming: list[dict]):
        self._incoming = list(incoming)
        self.sent: list[dict] = []

    async def send(self, frame: dict) -> None:
        self.sent.append(frame)

    async def recv(self) -> dict | None:
        return self._incoming.pop(0) if self._incoming else None


def _donut() -> CompanionDef:
    return CompanionDef(
        name="Princess Donut", species="cat", role=Role.PET, voice="VAIN.",
        axes=SeatAxes(narrative_vs_mechanical=0.4, verbosity="medium",
                      decisiveness="high", reading_tolerance="medium"),
        companion_of="alice@home", genre="caverns_and_claudes",
        world="beneath_sunden", session_url="ws://player2.local:8765/ws",
    )


async def test_companion_plays_a_full_scripted_session():
    incoming = [
        {"type": "SESSION_EVENT", "payload": {"event": "connected"}, "player_id": "rex-pid"},
        {"type": "CHARACTER_CREATION", "payload": {
            "phase": "scene", "prompt": "What is your origin?",
            "choices": [{"label": "Show cat"}, {"label": "Alley cat"}]}},
        {"type": "SESSION_EVENT", "payload": {"event": "ready"}, "player_id": "rex-pid"},
        {"type": "NARRATION", "payload": {"text": "The warren reeks of goblin."}},
        {"type": "TURN_STATUS", "payload": {"entries": [
            {"player_id": "rex-pid", "status": "pending"}]}},
        {"type": "DICE_REQUEST", "payload": {"roller": "Princess Donut", "die_system": "d20"}},
        {"type": "NARRATION_END", "payload": {"round": 1}},
        {"type": "SESSION_EVENT", "payload": {"event": "ended"}},
    ]
    server = FakeServer(incoming)
    brain = FakeStructuredModel(
        [
            CompanionIntent(kind=IntentKind.ACT, text="Show cat, OBVIOUSLY."),  # chargen
            CompanionIntent(kind=IntentKind.ACT, text="I sniff and deign to lead."),  # turn
            CompanionIntent(kind=IntentKind.ROLL),  # dice request
        ],
        default=CompanionIntent(kind=IntentKind.YIELD),
    )

    await run_companion(_donut(), server, brain, rng=random.Random(0))

    types = [f["type"] for f in server.sent]
    # connect → chargen choice → player action → dice throw
    assert types[0] == "SESSION_EVENT" and server.sent[0]["payload"]["event"] == "connect"
    assert server.sent[0]["payload"]["companion_of"] == "alice@home"
    assert server.sent[0]["payload"]["relationship"] == "pet"
    assert "CHARACTER_CREATION" in types
    assert "PLAYER_ACTION" in types
    action = next(f for f in server.sent if f["type"] == "PLAYER_ACTION")
    assert action["payload"]["action"] == "I sniff and deign to lead."
    assert action["player_id"] == "rex-pid"
    assert "DICE_THROW" in types
    throw = next(f for f in server.sent if f["type"] == "DICE_THROW")
    assert len(throw["payload"]["faces"]) == 1 and 1 <= throw["payload"]["faces"][0] <= 20
```

- [ ] **Step 2: Run the wiring test**

Run: `cd sidequest-companion && uv run pytest tests/wiring/test_full_loop.py -v`
Expected: PASS (1 passed).

- [ ] **Step 3: Run the whole suite + lint**

Run:
```bash
cd sidequest-companion && uv run pytest -q && uv run ruff check .
```
Expected: all tests PASS; ruff clean.

- [ ] **Step 4: Commit**

```bash
cd sidequest-companion && git add -A && git commit -q -m "test: full-loop wiring — companion plays a scripted session end to end"
```

---

## Self-Review

**Spec coverage:** Plan C implements the spec's "Component A — `sidequest-companion` package" and its data flow: `manifest`/`CompanionDef` (D), `persona` voice prompt (Section 2), `CompanionIntent` (the richer decision contract), `protocol` Transport + state mirror + frame builders (replacing browser perception/actuation), `brain` over seat-core, `dice` (physics-is-the-roll), `run` loop (connect→seat→chargen→play, Section 3), the `websockets` transport + CLI, and the full-loop wiring test (Section 6). Section 5 reliability is covered: decide-timeout→`YIELD`, model-error→`YIELD`, closed-transport→clean exit, never fabricate.

**Placeholder scan:** No TBD/TODO. Every step has complete code. The one prose note (CLI double-registration) gives an exact instruction, not a deferral.

**Type consistency:** `CompanionIntent`/`IntentKind` used identically across intent, brain, actuation, run, tests. `StateMirror` fields (`self_player_id`, `round`, `pending`, `my_turn()`) consistent between protocol, actuation, and run. Frame builders' shapes match what the run loop sends and the wiring test asserts. `make_brain(spec)` binds `CompanionIntent` with `YIELD_INTENT` default, matching seat-core's `make_model(spec, output_model, default=...)` signature from Plan A.

**Cross-plan consistency:** depends on Plan A's `seat_core` (`make_model`, `FakeStructuredModel`, `SeatAxes`, `Role`, `Message`) — all signatures match Plan A. The connect frame's `companion_of`/`relationship` match Plan B's `SessionEventPayload` fields and bond semantics; the wiring test asserts `relationship == "pet"`, matching Plan B's `parse_companion_relationship`.

**Reliability gap (flagged honestly):** the cost-ceiling guard (ADR-134 token ledger) from Section 5 is **not** in Plan C v1 — the default model bills per the seat-core backend, and the decide timeout + event-driven loop bound runaway behavior. A token ledger mirroring understudy's `TokenLedger` is a small follow-up (wrap `brain.decide` results, sum `input_tokens+output_tokens`, stop at a ceiling) and should be added before unattended runs. Noted, not built, to keep v1 focused on the playable vertical slice.

**Known v1 simplification:** chargen answering maps a brain ACT to free-text/first-option (`_chargen_choice`); rich per-`input_type` chargen handling (the_arrangement, fate_aspects) is deferred — the companion completes chargen via the text/selection path, which the wiring test exercises. This matches the spec's "full party member now" for *play*; deep chargen-FSM coverage is a fast-follow once a live server validates the scene shapes.
