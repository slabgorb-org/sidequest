# Plan B — Server Bond + Perception Seam Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Teach `sidequest-server` to recognize a connected seat as a *companion bonded to a human* and to scope its perception by type — a bonded **pet** receives its owner's private routes (`NARRATION_SEGMENT`, `SECRET_NOTE`); a **hireling** does not.

**Architecture:** Three small, well-contained additions. (1) `SessionRoom` gains a companion-bond registry keyed on the *owner's identity* (what a config can name; `player_id`s are server-minted). (2) The `SESSION_EVENT{connect}` handshake carries optional companion metadata; the connect handler registers the bond and emits an OTEL span, defaulting **closed** (unknown relationship → no widening). (3) At fan-out, a tiny `expand_visibility_for_companions` helper widens an owner-private event's `_visibility.visible_to` to include that owner's bonded pets **before** projection runs — so the existing firewall in `CoreInvariantStage` is untouched; we only grow the authorized recipient set, which is exactly "a pet shares its owner's view." The per-recipient `invariant.secret_routed` lie-detector span already covers the result.

**Tech Stack:** Python 3.12, FastAPI, pydantic v2, OpenTelemetry watcher hub, `pytest` (`-n auto`), `ruff`, `pyright`.

## Global Constraints

- This work lives entirely in `sidequest-server`. Branch off `develop` onto `feat/companion-bond-seam` (server targets `develop`; never commit to it directly).
- Python `>=3.12`; pydantic v2; `ruff` line-length matches repo config; `pyright` must stay clean.
- Tests run under `pytest -n auto` (xdist) by default; use `-n0` only for local debugging.
- **No Silent Fallbacks:** an unknown/malformed companion relationship resolves **closed** — treated as a non-widening seat (hireling-equivalent) and logged loudly via an OTEL span. Never default to `pet`.
- **OTEL mandate:** every bond decision emits a watcher span — `companion.bond_resolved` (connect) and `companion.routed_as_pet` (fan-out widening). The GM panel is the lie detector.
- **No Source-Text Wiring Tests** (server CLAUDE.md): wiring is proven by fixture-driven behavior + OTEL span assertions, never by grepping production source.
- The firewall in `sidequest/game/projection/invariants.py` is **not weakened**: pet-widening only *adds* an authorized recipient; the structural exclusion for everyone else is unchanged.
- Companion bonds key on **owner identity** (Cf-Access email or dev Host, per ADR-119) — never on `player_id`, which the companion cannot know.

---

### Task 1: `SessionRoom` companion-bond registry

**Files:**
- Modify: `sidequest-server/sidequest/server/session_room.py`
- Test: `sidequest-server/tests/server/test_companion_bond_registry.py`

**Interfaces:**
- Produces (on `SessionRoom`):
  - `CompanionRelationship(StrEnum)`: `PET="pet"`, `PEER="peer"`, `HIRELING="hireling"`.
  - `parse_companion_relationship(raw: str | None) -> CompanionRelationship | None` — returns the enum for an exact match, `None` otherwise (caller treats `None` as non-widening).
  - `register_companion_bond(companion_player_id: str, owner_identity: str, relationship: CompanionRelationship) -> None`.
  - `companion_owner_identity(companion_player_id: str) -> str | None` — owner identity iff the bond is a PET; else `None`.
  - `pets_of(owner_player_id: str) -> list[str]` — companion `player_id`s bonded as PET to the identity currently mapped to `owner_player_id`.

- [ ] **Step 1: Create the feature branch**

Run:
```bash
cd sidequest-server && git checkout develop && git pull --ff-only && git checkout -b feat/companion-bond-seam
```

- [ ] **Step 2: Write the failing test**

Create `sidequest-server/tests/server/test_companion_bond_registry.py`:
```python
"""Unit tests for the SessionRoom companion-bond registry (Plan B Task 1)."""

from __future__ import annotations

from sidequest.server.session_room import (
    CompanionRelationship,
    SessionRoom,
    parse_companion_relationship,
)


def test_parse_relationship_exact_match_or_none():
    assert parse_companion_relationship("pet") is CompanionRelationship.PET
    assert parse_companion_relationship("hireling") is CompanionRelationship.HIRELING
    assert parse_companion_relationship("peer") is CompanionRelationship.PEER
    assert parse_companion_relationship("sidekick") is None  # unknown → None (default-closed)
    assert parse_companion_relationship(None) is None


def test_pet_bond_resolves_owner_and_pets():
    room = SessionRoom()
    room.set_player_identity("owner-pid", "alice@home")
    room.register_companion_bond("rex-pid", "alice@home", CompanionRelationship.PET)

    assert room.companion_owner_identity("rex-pid") == "alice@home"
    assert room.pets_of("owner-pid") == ["rex-pid"]


def test_hireling_bond_does_not_widen():
    room = SessionRoom()
    room.set_player_identity("owner-pid", "alice@home")
    room.register_companion_bond("gus-pid", "alice@home", CompanionRelationship.HIRELING)

    assert room.companion_owner_identity("gus-pid") is None  # hireling: no owner-private view
    assert room.pets_of("owner-pid") == []  # hireling is not a pet


def test_pets_of_unknown_owner_is_empty():
    room = SessionRoom()
    assert room.pets_of("nobody-pid") == []
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/server/test_companion_bond_registry.py -v`
Expected: FAIL with `ImportError: cannot import name 'CompanionRelationship'`.

- [ ] **Step 4: Add the enum + parser near the top of `session_room.py`**

In `sidequest-server/sidequest/server/session_room.py`, immediately before the `class _Seat:` definition (currently around line 122), add:
```python
class CompanionRelationship(StrEnum):
    """How an AI companion seat relates to its bonded human. Only PET widens
    perception to the owner's private routes; PEER/HIRELING are vanilla seats."""

    PET = "pet"
    PEER = "peer"
    HIRELING = "hireling"


def parse_companion_relationship(raw: str | None) -> CompanionRelationship | None:
    """Exact-match a wire string to a relationship. Unknown/None -> None so the
    caller fails CLOSED (treats it as a non-widening seat) — never a pet."""
    if raw is None:
        return None
    try:
        return CompanionRelationship(raw)
    except ValueError:
        return None
```
If `StrEnum` is not already imported in this file, add `from enum import StrEnum` to the existing imports.

- [ ] **Step 5: Add the bond field to `SessionRoom`**

In the `SessionRoom` dataclass field block (alongside `_player_identities: dict[str, str] = field(default_factory=dict)`, around line 169), add:
```python
    # Companion bonds: companion player_id -> (owner_identity, relationship).
    # Keyed by the companion's player_id; the OWNER is named by identity
    # (Cf-Access email / dev Host) because a companion cannot know the owner's
    # server-minted player_id. Resolved to live player_ids at fan-out time.
    _companion_bonds: dict[str, tuple[str, "CompanionRelationship"]] = field(
        default_factory=dict
    )
```

- [ ] **Step 6: Add the registry methods to `SessionRoom`**

Add these three methods to the `SessionRoom` class (next to `set_player_identity`):
```python
    def register_companion_bond(
        self, companion_player_id: str, owner_identity: str, relationship: CompanionRelationship
    ) -> None:
        """Record that ``companion_player_id`` is bonded to the human identified
        by ``owner_identity`` as ``relationship``. Room-only and ephemeral."""
        self._companion_bonds[companion_player_id] = (owner_identity, relationship)

    def companion_owner_identity(self, companion_player_id: str) -> str | None:
        """Owner identity iff this companion is a PET (the only widening role)."""
        bond = self._companion_bonds.get(companion_player_id)
        if bond is None or bond[1] is not CompanionRelationship.PET:
            return None
        return bond[0]

    def pets_of(self, owner_player_id: str) -> list[str]:
        """Companion player_ids bonded as PET to the identity currently mapped
        to ``owner_player_id``. Empty if the owner has no resolved identity."""
        owner_identity = self._player_identities.get(owner_player_id)
        if owner_identity is None:
            return []
        return [
            cid
            for cid, (ident, rel) in self._companion_bonds.items()
            if rel is CompanionRelationship.PET and ident == owner_identity
        ]
```

- [ ] **Step 7: Run the test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/server/test_companion_bond_registry.py -v`
Expected: PASS (4 passed).

- [ ] **Step 8: Commit**

```bash
cd sidequest-server && git add -A && git commit -q -m "feat(companion): SessionRoom bond registry (identity-keyed, pet-only widening)"
```

---

### Task 2: `SESSION_EVENT{connect}` carries companion metadata

**Files:**
- Modify: `sidequest-server/sidequest/protocol/messages.py` (`SessionEventPayload`, around line 332)
- Test: `sidequest-server/tests/protocol/test_session_event_companion_fields.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `SessionEventPayload` gains `companion_of: str | None = None` and `relationship: str | None = None`.

- [ ] **Step 1: Write the failing test**

Create `sidequest-server/tests/protocol/test_session_event_companion_fields.py`:
```python
"""SessionEventPayload carries optional companion-bond metadata (Plan B Task 2)."""

from __future__ import annotations

from sidequest.protocol.messages import SessionEventPayload


def test_connect_payload_defaults_have_no_companion_fields():
    p = SessionEventPayload(event="connect", game_slug="abc", player_name="Alice")
    assert p.companion_of is None
    assert p.relationship is None


def test_connect_payload_accepts_companion_fields():
    p = SessionEventPayload(
        event="connect",
        game_slug="abc",
        player_name="Donut",
        companion_of="alice@home",
        relationship="pet",
    )
    assert p.companion_of == "alice@home"
    assert p.relationship == "pet"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/protocol/test_session_event_companion_fields.py -v`
Expected: FAIL — pydantic rejects the unknown `companion_of`/`relationship` kwargs (model is extra-forbid) OR the attribute is missing.

- [ ] **Step 3: Add the two fields to `SessionEventPayload`**

In `sidequest-server/sidequest/protocol/messages.py`, inside `class SessionEventPayload` (after the existing `game_slug: str | None = None` field, around line 358), add:
```python
    # Companion-bond metadata (Plan B). Present only when the connecting seat is
    # an AI companion. ``companion_of`` is the OWNER's identity (Cf-Access email
    # or dev Host), not a player_id. ``relationship`` is "pet" | "peer" |
    # "hireling"; an unknown value resolves closed (non-widening) server-side.
    companion_of: str | None = None
    relationship: str | None = None
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/protocol/test_session_event_companion_fields.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
cd sidequest-server && git add -A && git commit -q -m "feat(companion): SESSION_EVENT connect carries companion_of + relationship"
```

---

### Task 3: Connect handler registers the bond + emits `companion.bond_resolved`

**Files:**
- Modify: `sidequest-server/sidequest/handlers/connect.py` (add helper near `bind_player_identity` ~line 249; call it in `ConnectHandler.handle` after `room.connect(...)` ~line 465)
- Test: `sidequest-server/tests/handlers/test_companion_bond_connect.py`

**Interfaces:**
- Consumes: `SessionRoom.register_companion_bond`, `parse_companion_relationship`, `CompanionRelationship` (Task 1); `SessionEventPayload.companion_of/relationship` (Task 2); `_watcher_publish` (already imported in `connect.py:69`).
- Produces: `bind_companion_bond(room, player_id, payload) -> None`.

- [ ] **Step 1: Write the failing test**

Create `sidequest-server/tests/handlers/test_companion_bond_connect.py`:
```python
"""bind_companion_bond registers a pet bond and emits the OTEL span; an unknown
relationship fails closed (no bond) but still emits a span (Plan B Task 3)."""

from __future__ import annotations

from sidequest.handlers.connect import bind_companion_bond
from sidequest.protocol.messages import SessionEventPayload
from sidequest.server.session_room import SessionRoom


def _payload(**kw) -> SessionEventPayload:
    return SessionEventPayload(event="connect", game_slug="abc", **kw)


def test_pet_bond_registered_and_span_emitted(monkeypatch):
    spans: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        "sidequest.handlers.connect._watcher_publish",
        lambda name, fields, **_kw: spans.append((name, fields)),
    )
    room = SessionRoom()
    room.set_player_identity("rex-pid", "donut.local")

    bind_companion_bond(
        room, "rex-pid", _payload(player_name="Donut", companion_of="alice@home", relationship="pet")
    )

    assert room.companion_owner_identity("rex-pid") == "alice@home"
    names = [n for n, _ in spans]
    assert "companion.bond_resolved" in names
    fields = next(f for n, f in spans if n == "companion.bond_resolved")
    assert fields["relationship"] == "pet"
    assert fields["resolved"] is True


def test_unknown_relationship_fails_closed_and_emits_span(monkeypatch):
    spans: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        "sidequest.handlers.connect._watcher_publish",
        lambda name, fields, **_kw: spans.append((name, fields)),
    )
    room = SessionRoom()

    bind_companion_bond(
        room, "x-pid", _payload(player_name="X", companion_of="alice@home", relationship="overlord")
    )

    assert room.companion_owner_identity("x-pid") is None  # no pet bond
    fields = next(f for n, f in spans if n == "companion.bond_resolved")
    assert fields["resolved"] is False  # default-closed


def test_non_companion_connect_is_a_noop(monkeypatch):
    called: list[str] = []
    monkeypatch.setattr(
        "sidequest.handlers.connect._watcher_publish",
        lambda name, fields, **_kw: called.append(name),
    )
    room = SessionRoom()
    bind_companion_bond(room, "alice-pid", _payload(player_name="Alice"))  # no companion fields
    assert called == []  # ordinary player connect emits no companion span
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/handlers/test_companion_bond_connect.py -v`
Expected: FAIL with `ImportError: cannot import name 'bind_companion_bond'`.

- [ ] **Step 3: Add `bind_companion_bond` to `connect.py`**

In `sidequest-server/sidequest/handlers/connect.py`, immediately after the `bind_player_identity` function (ends around line 273), add:
```python
def bind_companion_bond(
    room: "SessionRoom", player_id: str, payload: "SessionEventPayload"
) -> None:
    """Register an AI companion's bond from the connect handshake.

    A no-op for ordinary players (no ``companion_of``). For a companion, the
    relationship is parsed exactly; an unknown value resolves CLOSED — no bond
    is registered (the seat behaves as a non-widening hireling) — and the span
    records ``resolved=False`` so the GM panel sees the rejection, never a
    silent grant of the owner's private view."""
    from sidequest.server.session_room import (
        parse_companion_relationship,
        CompanionRelationship,
    )

    owner_identity = (payload.companion_of or "").strip()
    if not owner_identity:
        return  # ordinary player connect

    relationship = parse_companion_relationship(payload.relationship)
    resolved = relationship is not None
    if relationship is not None:
        room.register_companion_bond(player_id, owner_identity, relationship)

    _watcher_publish(
        "companion.bond_resolved",
        {
            "field": "companion.bond_resolved",
            "player_id": player_id,
            "owner_identity": owner_identity,
            "relationship": payload.relationship,
            "resolved": resolved,
        },
        component="companion",
        severity="info" if resolved else "warning",
    )
```

- [ ] **Step 4: Call it from `ConnectHandler.handle` after `room.connect(...)`**

In `sidequest-server/sidequest/handlers/connect.py`, inside `ConnectHandler.handle`, immediately after the `room.connect(player_id, socket_id=session._socket_id)` call (around line 465), add:
```python
                    bind_companion_bond(room, player_id, payload)
```
Match the surrounding indentation exactly (the `room.connect(...)` call sits inside the `with mp_slug_connect_span(...)` block).

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/handlers/test_companion_bond_connect.py -v`
Expected: PASS (3 passed).

- [ ] **Step 6: Commit**

```bash
cd sidequest-server && git add -A && git commit -q -m "feat(companion): connect handler registers bond + emits companion.bond_resolved"
```

---

### Task 4: Pet-widening at fan-out — `expand_visibility_for_companions`

**Files:**
- Modify: `sidequest-server/sidequest/server/emitters.py` (add helper; call it after the envelope is built in `emit_event`, ~line 598)
- Test: `sidequest-server/tests/server/test_companion_visibility_expand.py`

**Interfaces:**
- Consumes: `MessageEnvelope`; `VISIBILITY_GATED_KINDS` from `sidequest.game.projection.invariants`; `SessionRoom.pets_of` (Task 1); `_watcher_publish`.
- Produces: `expand_visibility_for_companions(envelope: MessageEnvelope, room: "SessionRoom" | None) -> MessageEnvelope`.

- [ ] **Step 1: Write the failing test**

Create `sidequest-server/tests/server/test_companion_visibility_expand.py`:
```python
"""expand_visibility_for_companions widens owner-private events to bonded pets,
leaves everything else untouched, and emits companion.routed_as_pet (Plan B T4)."""

from __future__ import annotations

import json

from sidequest.game.projection.envelope import MessageEnvelope
from sidequest.server.emitters import expand_visibility_for_companions
from sidequest.server.session_room import CompanionRelationship, SessionRoom


def _segment(visible_to) -> MessageEnvelope:
    return MessageEnvelope(
        kind="NARRATION_SEGMENT",
        payload_json=json.dumps({"text": "psst", "_visibility": {"visible_to": visible_to}}),
        origin_seq=1,
    )


def _room_with_pet() -> SessionRoom:
    room = SessionRoom()
    room.set_player_identity("owner-pid", "alice@home")
    room.register_companion_bond("rex-pid", "alice@home", CompanionRelationship.PET)
    return room


def test_pet_added_to_owner_private_segment(monkeypatch):
    spans: list[str] = []
    monkeypatch.setattr(
        "sidequest.server.emitters._watcher_publish",
        lambda name, fields, **_kw: spans.append(name),
    )
    out = expand_visibility_for_companions(_segment(["owner-pid"]), _room_with_pet())
    visible_to = json.loads(out.payload_json)["_visibility"]["visible_to"]
    assert set(visible_to) == {"owner-pid", "rex-pid"}
    assert "companion.routed_as_pet" in spans


def test_no_pet_means_unchanged_envelope():
    room = SessionRoom()
    room.set_player_identity("owner-pid", "alice@home")  # no companion bonds
    env = _segment(["owner-pid"])
    out = expand_visibility_for_companions(env, room)
    assert out.payload_json == env.payload_json


def test_all_sentinel_is_left_untouched():
    env = _segment("all")
    out = expand_visibility_for_companions(env, _room_with_pet())
    assert json.loads(out.payload_json)["_visibility"]["visible_to"] == "all"


def test_non_gated_kind_is_left_untouched():
    env = MessageEnvelope(kind="NARRATION", payload_json=json.dumps({"text": "hi"}), origin_seq=1)
    out = expand_visibility_for_companions(env, _room_with_pet())
    assert out is env


def test_none_room_is_noop():
    env = _segment(["owner-pid"])
    assert expand_visibility_for_companions(env, None) is env
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/server/test_companion_visibility_expand.py -v`
Expected: FAIL with `ImportError: cannot import name 'expand_visibility_for_companions'`.

- [ ] **Step 3: Add the helper to `emitters.py`**

In `sidequest-server/sidequest/server/emitters.py`, add this function near the other module-level helpers (e.g. after `_emit_recipient_dropped`, around line 80):
```python
def expand_visibility_for_companions(
    envelope: "MessageEnvelope", room: "SessionRoom | None"
) -> "MessageEnvelope":
    """Widen an owner-private event's ``_visibility.visible_to`` to include the
    owner's bonded PETs, BEFORE projection runs.

    This is the ONLY companion change to perception: the firewall in
    CoreInvariantStage is untouched; we only add an authorized recipient (a pet
    shares its owner's view). Only list-valued visible_to on a visibility-gated
    kind is widened — the ``"all"`` sentinel and non-gated kinds pass through
    unchanged. Returns the same envelope object when nothing is added."""
    from sidequest.game.projection.envelope import MessageEnvelope as _Envelope
    from sidequest.game.projection.invariants import VISIBILITY_GATED_KINDS

    if room is None or envelope.kind not in VISIBILITY_GATED_KINDS:
        return envelope
    payload = json.loads(envelope.payload_json)
    viz = payload.get("_visibility")
    visible_to = viz.get("visible_to") if isinstance(viz, dict) else None
    if not isinstance(visible_to, list):
        return envelope

    added: list[str] = []
    widened = list(visible_to)
    for owner_pid in visible_to:
        for pet_pid in room.pets_of(owner_pid):
            if pet_pid not in widened:
                widened.append(pet_pid)
                added.append(pet_pid)
                _watcher_publish(
                    "companion.routed_as_pet",
                    {
                        "field": "companion.routed_as_pet",
                        "pet_player_id": pet_pid,
                        "owner_player_id": owner_pid,
                        "kind": envelope.kind,
                    },
                    component="companion",
                )
    if not added:
        return envelope
    payload["_visibility"]["visible_to"] = widened
    return _Envelope(
        kind=envelope.kind,
        payload_json=json.dumps(payload),
        origin_seq=envelope.origin_seq,
    )
```
If `TYPE_CHECKING`-only imports are needed for the annotations, the function uses string annotations and a local import, so no top-level import change is required beyond the existing `json` import (already used in `emitters.py`).

- [ ] **Step 4: Wire it into `emit_event`**

In `sidequest-server/sidequest/server/emitters.py`, in `emit_event`, immediately after the `envelope = MessageEnvelope(...)` construction (the block ending around line 598) and before `status_effects = views.status_effects_by_player(handler)`, add:
```python
                envelope = expand_visibility_for_companions(envelope, room)
```
This widened envelope flows into both `_project_frames` (peers) and the emitter projection below, so a pet recipient passes the existing visibility gate.

- [ ] **Step 5: Run the helper test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/server/test_companion_visibility_expand.py -v`
Expected: PASS (5 passed).

- [ ] **Step 6: Commit**

```bash
cd sidequest-server && git add -A && git commit -q -m "feat(companion): pet-widening of owner-private visibility at fan-out"
```

---

### Task 5: Firewall wiring test — pet sees owner-private, hireling does not

**Files:**
- Test: `sidequest-server/tests/server/test_companion_perception_wiring.py`

**Interfaces:**
- Consumes: `expand_visibility_for_companions` (Task 4); the real `ComposedFilter` projection pipeline; `SessionRoom` (Task 1).

This is the load-bearing wiring test (server CLAUDE.md): it drives the **real** projection pipeline (`ComposedFilter` → `CoreInvariantStage`) against a real `SessionRoom` and the production widening helper, proving the firewall honors the widened recipient set for a pet and still excludes a hireling — plus the OTEL span.

- [ ] **Step 1: Write the wiring test**

Create `sidequest-server/tests/server/test_companion_perception_wiring.py`:
```python
"""WIRING: a bonded pet receives its owner's private NARRATION_SEGMENT through
the REAL projection pipeline; a hireling does not. Proves the widening helper
and the CoreInvariantStage firewall compose correctly (Plan B Task 5).

This is a fixture-driven behavior + OTEL-span test per the server's
'No Source-Text Wiring Tests' rule.
"""

from __future__ import annotations

import json

from sidequest.game.projection.composed import ComposedFilter
from sidequest.game.projection.envelope import MessageEnvelope
from sidequest.game.projection.view import GameStateView
from sidequest.server.emitters import expand_visibility_for_companions
from sidequest.server.session_room import CompanionRelationship, SessionRoom


def _owner_private_segment() -> MessageEnvelope:
    return MessageEnvelope(
        kind="NARRATION_SEGMENT",
        payload_json=json.dumps(
            {"text": "Only Alice senses the trap.", "_visibility": {"visible_to": ["owner-pid"]}}
        ),
        origin_seq=7,
    )


def _included(envelope: MessageEnvelope, player_id: str) -> bool:
    decision = ComposedFilter.with_no_genre_rules().project(
        envelope=envelope, view=GameStateView(), player_id=player_id
    )
    return decision.include


def test_pet_receives_owner_private_segment_and_hireling_does_not(monkeypatch):
    spans: list[str] = []
    monkeypatch.setattr(
        "sidequest.server.emitters._watcher_publish",
        lambda name, fields, **_kw: spans.append(name),
    )
    room = SessionRoom()
    room.set_player_identity("owner-pid", "alice@home")
    room.register_companion_bond("rex-pid", "alice@home", CompanionRelationship.PET)
    room.register_companion_bond("gus-pid", "alice@home", CompanionRelationship.HIRELING)

    widened = expand_visibility_for_companions(_owner_private_segment(), room)

    assert _included(widened, "owner-pid") is True  # the human still sees it
    assert _included(widened, "rex-pid") is True  # the PET shares the owner's view
    assert _included(widened, "gus-pid") is False  # the HIRELING is excluded
    assert _included(widened, "stranger-pid") is False  # an unbonded seat is excluded
    assert "companion.routed_as_pet" in spans  # the firewall decision is observable
```

- [ ] **Step 2: Run the wiring test**

Run: `cd sidequest-server && uv run pytest tests/server/test_companion_perception_wiring.py -v`
Expected: PASS (1 passed). If `GameStateView()` requires constructor arguments in this codebase, construct it via the test helper the projection suite already uses (grep `tests/` for `GameStateView(` to copy the minimal construction) — the projection only reads `view` for genre rules, which `with_no_genre_rules()` disables, so a default/minimal view suffices.

- [ ] **Step 3: Run the full companion suite + lint + types**

Run:
```bash
cd sidequest-server && uv run pytest tests/server/test_companion_bond_registry.py \
  tests/protocol/test_session_event_companion_fields.py \
  tests/handlers/test_companion_bond_connect.py \
  tests/server/test_companion_visibility_expand.py \
  tests/server/test_companion_perception_wiring.py -v \
  && uv run ruff check sidequest/server/session_room.py sidequest/server/emitters.py \
       sidequest/handlers/connect.py sidequest/protocol/messages.py \
  && uv run pyright sidequest/server/session_room.py sidequest/server/emitters.py
```
Expected: all tests PASS; ruff and pyright clean.

- [ ] **Step 4: Run the existing projection + emitter suites for regressions**

Run:
```bash
cd sidequest-server && uv run pytest tests/ -k "projection or emit or invariant or session_room" -q
```
Expected: PASS — the firewall change only adds a recipient; nothing existing should break.

- [ ] **Step 5: Commit**

```bash
cd sidequest-server && git add -A && git commit -q -m "test(companion): firewall wiring — pet sees owner-private, hireling excluded"
```

---

## Self-Review

**Spec coverage:** Plan B implements the spec's "Component C — Server seam (v1)": the bond registry (Task 1), the connect-handshake metadata (Task 2), the connect-time bond registration with `companion.bond_resolved` (Task 3), the `CompanionVisibilityStage`-equivalent pet-widening with `companion.routed_as_pet` (Task 4), and the bond/perception wiring test (Task 5). Section 5's **default-closed** firewall and the **trust-model boundary** (cooperative-local v1) are honored — unknown relationships never grant pet access.

**Design note vs spec wording:** the spec named a `CompanionVisibilityStage` inside the projection pipeline. Reading the code showed a strictly smaller, safer seam: widen `_visibility.visible_to` *before* projection so `CoreInvariantStage` (the security boundary) is **unmodified** and the existing `invariant.secret_routed` lie-detector span already covers each recipient. This is a deliberate, documented improvement on the spec, not a deviation in behavior — type-scoped perception is delivered.

**Placeholder scan:** No TBD/TODO. Every step shows complete code or an exact insertion with a real anchor (`bind_player_identity`, `room.connect(...)`, the `envelope = MessageEnvelope(...)` build site).

**Type consistency:** `CompanionRelationship` / `parse_companion_relationship` / `register_companion_bond` / `companion_owner_identity` / `pets_of` are used identically across Tasks 1, 3, 4, 5. `expand_visibility_for_companions(envelope, room)` signature matches its one production call site and all tests. Bonds key on **owner identity** throughout; `pets_of` resolves `owner_player_id → identity → pets` consistently.

**Residual wiring gap (flagged honestly):** Task 5 drives the real projection pipeline + production widening helper, but does not drive `emit_event` end-to-end (which needs a full handler/tx scaffold). The production call-site insertion is Task 4 Step 4. A follow-up full `emit_event` integration test modeled on `tests/server/test_location_description_emit.py` (real handler fixture + captured outbound frames) is recommended to close this to the server's strictest wiring bar; it is not required for the seam to function and was kept out of v1 scope to avoid a brittle hand-built scaffold.

**Ambiguity check:** `GameStateView()` construction in Task 5 is guarded with a fallback instruction (copy the projection suite's minimal construction) since the projection only consults `view` for genre rules, which the test disables.
