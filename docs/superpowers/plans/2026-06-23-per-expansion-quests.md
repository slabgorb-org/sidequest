# Per-Expansion Quests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Seed one deterministic quest per dungeon *expansion*, project it into the ADR-137 player-facing quest spine so the Quests tab shows it, and resolve it when the expansion's signature beat fires.

**Architecture:** The per-expansion quest is a `ComplicationThread(kind="quest", payload.scope="expansion")` in the dungeon complication ledger (the source of truth — reuse `DungeonStore.open_thread`/`resolve_thread`). A frontier observer reconciles open expansion-quest threads into `GameSnapshot.quest_log` as `QuestEntry` rows (id `dungeon:exp{N}`) when the party enters the expansion; the existing `_maybe_emit_quests` then carries them to the Quests tab. Resolution generalizes the existing trope-resolution handshake. Objective text is deterministic (filled from a theme `quest_template`); the narrator flavors the prose at surface (ADR-106 Amendment C).

**Tech Stack:** Python 3 / pydantic v2 / sqlite (dungeon ledger) / OpenTelemetry spans / pytest (+pytest-asyncio, pytest-xdist).

**Source spec:** `docs/superpowers/specs/2026-06-23-per-expansion-quests-design.md`

## Global Constraints

- **No LLM on the materialize path** (ADR-106 Amendment C, 2026-06-23). Objective text is deterministic; prose is the narrator's at surface. No `complete_with_tools` call originates from `dungeon/`.
- **No Silent Fallbacks** (CLAUDE.md). If a signature kind cannot bind, degrade *loudly* to `reach_deep` with a `severity="warning"` span — never a silent skip.
- **No Source-Text Wiring Tests** (server CLAUDE.md). Prove wiring with OTEL span assertions and fixture-driven behavior tests, never by grepping source.
- **Determinism** — same `campaign_seed` + same expansion ⇒ identical quest (title/objective/binding).
- **Namespaced quest ids** — projected entries use id `dungeon:exp{N}`; the projection NEVER reads or mutates non-`dungeon:` entries (the drive-spine quest `seed_drive` and narrator-recorded quests are untouched).
- **Test command:** `uv run pytest tests/dungeon/<file> -v` (in-memory sqlite, no Postgres needed for these; 30 s per-test timeout via `addopts`). Serial debug: add `-n0`.
- **Pydantic models in this domain use** `model_config = ConfigDict(extra="forbid")` to match `DungeonTheme`/`SetPiece`.

---

### Task 1: Theme `quest_template` schema

**Files:**
- Modify: `sidequest/dungeon/themes.py` (add `ExpansionQuestTemplate` model near `SetPiece`/`NarratorFlavor`; add field to `DungeonTheme` after `set_pieces`, line ~217)
- Test: `tests/dungeon/test_theme_quest_template.py`

**Interfaces:**
- Produces: `ExpansionQuestTemplate(signature: Literal["big_bad","set_piece","reach_deep"], title: str, objective: str, set_piece_id: str | None = None)`; `DungeonTheme.quest_template: ExpansionQuestTemplate | None = None`.

- [ ] **Step 1: Write the failing test**

```python
# tests/dungeon/test_theme_quest_template.py
import pytest
from pydantic import ValidationError
from sidequest.dungeon.themes import DungeonTheme

_BASE = {
    "id": "bone_crypt", "display_name": "Bone Crypt",
    "generator_class": "structured",
    "interior": {"algorithm": "roomcorridor", "params": {}},
    "depth_band": {"min": 0.0, "max": 50.0},
    "narrator": {"register": "grim", "flavor": "ossuary", "motifs": ["bone"]},
}

def test_quest_template_parses_big_bad():
    theme = DungeonTheme.model_validate(
        {**_BASE, "quest_template": {
            "signature": "big_bad",
            "title": "The {theme} Stirs",
            "objective": "Something rules the {theme}. Find it and end it.",
        }}
    )
    assert theme.quest_template is not None
    assert theme.quest_template.signature == "big_bad"

def test_quest_template_optional():
    theme = DungeonTheme.model_validate(_BASE)
    assert theme.quest_template is None

def test_quest_template_rejects_unknown_signature():
    with pytest.raises(ValidationError):
        DungeonTheme.model_validate(
            {**_BASE, "quest_template": {"signature": "boss_rush", "title": "x", "objective": "y"}}
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/dungeon/test_theme_quest_template.py -v`
Expected: FAIL — `DungeonTheme` has no `quest_template` attr / `extra="forbid"` rejects it.

- [ ] **Step 3: Add the model + field**

In `sidequest/dungeon/themes.py`, add near the other nested models:

```python
class ExpansionQuestTemplate(BaseModel):
    """Per-expansion quest template (ADR-137 × ADR-106). Deterministic slot
    fill at attach; narrator flavors the prose at surface (Amendment C).

    ``signature`` declares what beat completes the quest:
      - big_bad   : the deepest region's big_bad NPC (hp_depletion resolves)
      - set_piece : the set-piece named by ``set_piece_id`` (trope handshake resolves)
      - reach_deep: the deepest region (frontier transition into it resolves)
    """

    model_config = ConfigDict(extra="forbid")

    signature: Literal["big_bad", "set_piece", "reach_deep"]
    title: str
    objective: str
    set_piece_id: str | None = None  # required iff signature == "set_piece"

    @model_validator(mode="after")
    def _v_set_piece_id(self) -> "ExpansionQuestTemplate":
        if self.signature == "set_piece" and not (self.set_piece_id or "").strip():
            raise ValueError("signature 'set_piece' requires a non-blank set_piece_id")
        return self
```

Add to `DungeonTheme` after `set_pieces`:

```python
    quest_template: ExpansionQuestTemplate | None = None
```

Ensure `Literal` and `model_validator` are imported at the top of the file (check existing imports; `model_validator` is already used by `DungeonTheme`).

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/dungeon/test_theme_quest_template.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add sidequest/dungeon/themes.py tests/dungeon/test_theme_quest_template.py
git commit -m "feat(dungeon): ExpansionQuestTemplate theme schema (per-expansion quests)"
```

---

### Task 2: OTEL spans — `dungeon.quest.bound` and `dungeon.quest.resolved`

**Files:**
- Create: `sidequest/telemetry/spans/dungeon_quest.py`
- Test: `tests/dungeon/test_dungeon_quest_spans.py`

**Interfaces:**
- Produces: `quest_bound_span(*, expansion_id: int, signature_kind: str, ref_id: str, degraded: bool, _tracer=None, **attrs)`, `quest_resolved_span(*, expansion_id: int, signature_kind: str, resolving_event: str, _tracer=None, **attrs)`; constants `SPAN_QUEST_BOUND = "dungeon.quest.bound"`, `SPAN_QUEST_RESOLVED = "dungeon.quest.resolved"`. Registered in `SPAN_ROUTES` so the GM panel sees them.

- [ ] **Step 1: Write the failing test** (mirror `tests/dungeon/test_setpiece_attach_wiring.py`'s in-memory exporter pattern)

```python
# tests/dungeon/test_dungeon_quest_spans.py
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from sidequest.telemetry.spans.dungeon_quest import (
    quest_bound_span, quest_resolved_span, SPAN_QUEST_BOUND, SPAN_QUEST_RESOLVED,
)

def _capture():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return exporter, provider.get_tracer("test")

def test_quest_bound_span_emits_attributes():
    exporter, tracer = _capture()
    with quest_bound_span(expansion_id=1, signature_kind="reach_deep",
                          ref_id="exp001.r3", degraded=True, _tracer=tracer):
        pass
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == SPAN_QUEST_BOUND
    assert spans[0].attributes["signature_kind"] == "reach_deep"
    assert spans[0].attributes["degraded"] is True

def test_quest_resolved_span_emits():
    exporter, tracer = _capture()
    with quest_resolved_span(expansion_id=1, signature_kind="big_bad",
                            resolving_event="hp_depletion", _tracer=tracer):
        pass
    spans = exporter.get_finished_spans()
    assert spans[0].name == SPAN_QUEST_RESOLVED
    assert spans[0].attributes["resolving_event"] == "hp_depletion"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/dungeon/test_dungeon_quest_spans.py -v`
Expected: FAIL — module `dungeon_quest` does not exist.

- [ ] **Step 3: Create the spans module** (copy the exact style of `telemetry/spans/dungeon_setpiece.py::quest_seed_span` and the `SPAN_ROUTES` registration in `dungeon_persist.py`)

```python
# sidequest/telemetry/spans/dungeon_quest.py
"""dungeon.quest.* spans — per-expansion quest bind + resolve (ADR-137 × ADR-106)."""
from __future__ import annotations
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from opentelemetry import trace
from sidequest.telemetry.spans._base import Span, SpanRoute, SPAN_ROUTES

SPAN_QUEST_BOUND = "dungeon.quest.bound"
SPAN_QUEST_RESOLVED = "dungeon.quest.resolved"

@contextmanager
def quest_bound_span(*, expansion_id: int, signature_kind: str, ref_id: str,
                     degraded: bool, _tracer: trace.Tracer | None = None,
                     **attrs: Any) -> Iterator[trace.Span]:
    with Span.open(SPAN_QUEST_BOUND, {
        "expansion_id": expansion_id, "signature_kind": signature_kind,
        "ref_id": ref_id, "degraded": degraded, **attrs,
    }, tracer_override=_tracer) as span:
        yield span

@contextmanager
def quest_resolved_span(*, expansion_id: int, signature_kind: str,
                        resolving_event: str, _tracer: trace.Tracer | None = None,
                        **attrs: Any) -> Iterator[trace.Span]:
    with Span.open(SPAN_QUEST_RESOLVED, {
        "expansion_id": expansion_id, "signature_kind": signature_kind,
        "resolving_event": resolving_event, **attrs,
    }, tracer_override=_tracer) as span:
        yield span

SPAN_ROUTES[SPAN_QUEST_BOUND] = SpanRoute(
    event_type="state_transition", component="dungeon",
    extract=lambda s: {"expansion_id": s.attributes.get("expansion_id"),
                       "signature_kind": s.attributes.get("signature_kind"),
                       "degraded": s.attributes.get("degraded")},
)
SPAN_ROUTES[SPAN_QUEST_RESOLVED] = SpanRoute(
    event_type="state_transition", component="dungeon",
    extract=lambda s: {"expansion_id": s.attributes.get("expansion_id"),
                       "signature_kind": s.attributes.get("signature_kind"),
                       "resolving_event": s.attributes.get("resolving_event")},
)
```

> Verify the exact import path for `Span`, `SpanRoute`, and `SPAN_ROUTES` against `dungeon_persist.py`'s imports (the extraction shows `Span.open(...)` and a `SPAN_ROUTES` dict with `SpanRoute(...)` — copy its import line verbatim).

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/dungeon/test_dungeon_quest_spans.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add sidequest/telemetry/spans/dungeon_quest.py tests/dungeon/test_dungeon_quest_spans.py
git commit -m "feat(telemetry): dungeon.quest.bound/resolved spans"
```

---

### Task 3: Deterministic signature selection

**Files:**
- Create: `sidequest/dungeon/expansion_quest.py`
- Test: `tests/dungeon/test_expansion_quest_select.py`

**Interfaces:**
- Consumes: `Expansion` (`region_graph/model.py`: `new_nodes: list[RegionNode]` with `.id`, `.depth_score`, `.theme`), `RegionContentManifest` (`big_bad: dict | None`), `ExpansionQuestTemplate` (Task 1).
- Produces:
```python
@dataclass(frozen=True)
class SignatureBinding:
    kind: str            # "big_bad" | "set_piece" | "reach_deep" (effective, post-degrade)
    ref_id: str          # bound element id: region id, or big_bad name, or set_piece id
    anchor_region: str   # the region id the quest anchors to
    title: str
    objective: str
    degraded: bool
def select_signature(*, expansion: Expansion, manifests_by_region: dict[str, RegionContentManifest], template: ExpansionQuestTemplate) -> SignatureBinding: ...
```

- [ ] **Step 1: Write the failing test**

```python
# tests/dungeon/test_expansion_quest_select.py
from sidequest.dungeon.region_graph.model import Expansion, RegionNode
from sidequest.dungeon.themes import ExpansionQuestTemplate
from sidequest.game.cookbook.models import RegionContentManifest
from sidequest.dungeon.expansion_quest import select_signature

def _node(rid, depth, theme="bone_crypt"):
    return RegionNode(id=rid, expansion_id=1, theme=theme, depth_score=depth)

def _manifest(big_bad):
    return RegionContentManifest(race="undead", cr_band="mid", size_budget={},
        wandering_table=[], loot_table=[], special_rooms=[], big_bad=big_bad)

def _exp():
    return Expansion(expansion_id=1,
        new_nodes=[_node("exp001.r0", 10.0), _node("exp001.r1", 30.0)], new_edges=[])

def test_big_bad_binds_deepest_region_with_big_bad():
    tpl = ExpansionQuestTemplate(signature="big_bad", title="The {theme} Stirs",
                                 objective="End the {big_bad}.")
    b = select_signature(expansion=_exp(),
        manifests_by_region={"exp001.r0": _manifest(None),
                             "exp001.r1": _manifest({"name": "Bone Tyrant"})},
        template=tpl)
    assert b.kind == "big_bad"
    assert b.ref_id == "Bone Tyrant"
    assert b.anchor_region == "exp001.r1"
    assert b.objective == "End the Bone Tyrant."
    assert b.title == "The bone_crypt Stirs"
    assert b.degraded is False

def test_big_bad_degrades_to_reach_deep_when_absent():
    tpl = ExpansionQuestTemplate(signature="big_bad", title="t", objective="o")
    b = select_signature(expansion=_exp(),
        manifests_by_region={"exp001.r0": _manifest(None), "exp001.r1": _manifest(None)},
        template=tpl)
    assert b.kind == "reach_deep"
    assert b.anchor_region == "exp001.r1"   # deepest
    assert b.degraded is True

def test_reach_deep_binds_deepest_region():
    tpl = ExpansionQuestTemplate(signature="reach_deep", title="t", objective="reach the deep")
    b = select_signature(expansion=_exp(), manifests_by_region={}, template=tpl)
    assert b.kind == "reach_deep"
    assert b.ref_id == "exp001.r1"
    assert b.degraded is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/dungeon/test_expansion_quest_select.py -v`
Expected: FAIL — module/function missing.

- [ ] **Step 3: Implement `select_signature`**

```python
# sidequest/dungeon/expansion_quest.py
"""Per-expansion quest lifecycle (ADR-137 × ADR-106): select signature beat,
seed a ledger thread, project into quest_log, resolve on the beat.
Deterministic — no LLM (Amendment C)."""
from __future__ import annotations
from dataclasses import dataclass
from sidequest.dungeon.region_graph.model import Expansion
from sidequest.dungeon.themes import ExpansionQuestTemplate
from sidequest.game.cookbook.models import RegionContentManifest

@dataclass(frozen=True)
class SignatureBinding:
    kind: str
    ref_id: str
    anchor_region: str
    title: str
    objective: str
    degraded: bool

def _deepest(expansion: Expansion):
    # depth_score may be None pre-attach; treat None as -inf so attached nodes win.
    return max(expansion.new_nodes, key=lambda n: (n.depth_score if n.depth_score is not None else float("-inf")))

def _fill(text: str, *, theme: str, big_bad: str, anchor: str) -> str:
    return (text.replace("{theme}", theme).replace("{big_bad}", big_bad)
                .replace("{anchor}", anchor))

def select_signature(*, expansion: Expansion,
                     manifests_by_region: dict[str, RegionContentManifest],
                     template: ExpansionQuestTemplate) -> SignatureBinding:
    deepest = _deepest(expansion)
    theme = deepest.theme

    if template.signature == "big_bad":
        # deepest region (by depth_score) that rolled a big_bad
        candidates = sorted(
            (n for n in expansion.new_nodes
             if (manifests_by_region.get(n.id) or _empty()).big_bad),
            key=lambda n: (n.depth_score or float("-inf")), reverse=True)
        if candidates:
            node = candidates[0]
            bb = manifests_by_region[node.id].big_bad or {}
            name = str(bb.get("name", "")).strip() or "the master of this place"
            return SignatureBinding(kind="big_bad", ref_id=name, anchor_region=node.id,
                title=_fill(template.title, theme=theme, big_bad=name, anchor=node.id),
                objective=_fill(template.objective, theme=theme, big_bad=name, anchor=node.id),
                degraded=False)
        # No big_bad rolled — loud degrade to reach_deep (caller emits the span).
        return _reach_deep(template, deepest, theme, degraded=True)

    if template.signature == "set_piece":
        sp = (template.set_piece_id or "").strip()
        return SignatureBinding(kind="set_piece", ref_id=sp, anchor_region=deepest.id,
            title=_fill(template.title, theme=theme, big_bad="", anchor=deepest.id),
            objective=_fill(template.objective, theme=theme, big_bad="", anchor=deepest.id),
            degraded=False)

    return _reach_deep(template, deepest, theme, degraded=False)

def _reach_deep(template, deepest, theme, *, degraded):
    return SignatureBinding(kind="reach_deep", ref_id=deepest.id, anchor_region=deepest.id,
        title=_fill(template.title, theme=theme, big_bad="", anchor=deepest.id),
        objective=_fill(template.objective, theme=theme, big_bad="", anchor=deepest.id),
        degraded=degraded)

def _empty() -> RegionContentManifest:
    return RegionContentManifest(race="", cr_band="", size_budget={}, wandering_table=[],
        loot_table=[], special_rooms=[], big_bad=None)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/dungeon/test_expansion_quest_select.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add sidequest/dungeon/expansion_quest.py tests/dungeon/test_expansion_quest_select.py
git commit -m "feat(dungeon): deterministic per-expansion signature selection"
```

---

### Task 4: `seed_expansion_quest` — open the ledger thread

**Files:**
- Modify: `sidequest/dungeon/expansion_quest.py`
- Test: `tests/dungeon/test_expansion_quest_seed.py`

**Interfaces:**
- Consumes: `select_signature` (Task 3), `quest_bound_span` (Task 2), `DungeonStore.open_thread` + `ComplicationThread` (`persistence.py`).
- Produces: `seed_expansion_quest(*, campaign_seed: int, expansion: Expansion, manifests_by_region, template: ExpansionQuestTemplate, store, started_at_depth_score: float) -> str` (returns the thread_id; opens one `ComplicationThread(kind="quest", payload={"scope":"expansion", "expansion_id":..., "signature_kind":..., "ref_id":..., "anchor_region":..., "title":..., "objective":...})`).

- [ ] **Step 1: Write the failing test**

```python
# tests/dungeon/test_expansion_quest_seed.py
import sqlite3
from sidequest.dungeon.persistence import DungeonStore
from sidequest.dungeon.region_graph.model import Expansion, RegionNode
from sidequest.dungeon.themes import ExpansionQuestTemplate
from sidequest.dungeon.expansion_quest import seed_expansion_quest

def _store():
    conn = sqlite3.connect(":memory:"); conn.row_factory = sqlite3.Row
    s = DungeonStore(conn); s.ensure_schema(); return conn, s

def _exp():
    return Expansion(expansion_id=2,
        new_nodes=[RegionNode(id="exp002.r0", expansion_id=2, theme="bone_crypt", depth_score=40.0)],
        new_edges=[])

def test_seed_opens_one_expansion_quest_thread():
    conn, store = _store()
    tpl = ExpansionQuestTemplate(signature="reach_deep", title="The {theme} deepens",
                                 objective="Descend to the heart of the {theme}.")
    tid = seed_expansion_quest(campaign_seed=77, expansion=_exp(), manifests_by_region={},
        template=tpl, store=store, started_at_depth_score=40.0)
    conn.commit()
    threads = store.open_threads()
    assert len(threads) == 1
    t = threads[0]
    assert t.thread_id == tid
    assert t.kind == "quest"
    assert t.payload["scope"] == "expansion"
    assert t.payload["expansion_id"] == 2
    assert t.payload["objective"] == "Descend to the heart of the bone_crypt."

def test_seed_is_deterministic_thread_id():
    conn1, s1 = _store(); conn2, s2 = _store()
    tpl = ExpansionQuestTemplate(signature="reach_deep", title="t", objective="o")
    a = seed_expansion_quest(campaign_seed=77, expansion=_exp(), manifests_by_region={}, template=tpl, store=s1, started_at_depth_score=40.0)
    b = seed_expansion_quest(campaign_seed=77, expansion=_exp(), manifests_by_region={}, template=tpl, store=s2, started_at_depth_score=40.0)
    assert a == b
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/dungeon/test_expansion_quest_seed.py -v`
Expected: FAIL — `seed_expansion_quest` missing.

- [ ] **Step 3: Implement** (append to `expansion_quest.py`)

```python
import hashlib
from sidequest.dungeon.persistence import ComplicationThread
from sidequest.telemetry.spans.dungeon_quest import quest_bound_span

def _expansion_quest_thread_id(campaign_seed: int, expansion_id: int) -> str:
    h = hashlib.blake2b(f"{campaign_seed}:{expansion_id}:expansion_quest".encode(), digest_size=8)
    return f"q.exp{expansion_id}.{h.hexdigest()}"

def seed_expansion_quest(*, campaign_seed: int, expansion: Expansion,
                         manifests_by_region: dict[str, RegionContentManifest],
                         template: ExpansionQuestTemplate, store,
                         started_at_depth_score: float) -> str:
    b = select_signature(expansion=expansion, manifests_by_region=manifests_by_region, template=template)
    thread_id = _expansion_quest_thread_id(campaign_seed, expansion.expansion_id)
    with quest_bound_span(expansion_id=expansion.expansion_id, signature_kind=b.kind,
                          ref_id=b.ref_id, degraded=b.degraded):
        store.open_thread(ComplicationThread(
            thread_id=thread_id, origin_region_id=b.anchor_region, kind="quest", status="open",
            started_at_depth_score=started_at_depth_score,
            payload={"scope": "expansion", "expansion_id": expansion.expansion_id,
                     "signature_kind": b.kind, "ref_id": b.ref_id,
                     "anchor_region": b.anchor_region, "title": b.title, "objective": b.objective},
        ))
    return thread_id
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/dungeon/test_expansion_quest_seed.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add sidequest/dungeon/expansion_quest.py tests/dungeon/test_expansion_quest_seed.py
git commit -m "feat(dungeon): seed_expansion_quest opens an expansion-scoped ledger thread"
```

---

### Task 5: Projection — reconcile open expansion-quest threads into `quest_log`

**Files:**
- Modify: `sidequest/dungeon/expansion_quest.py`
- Test: `tests/dungeon/test_expansion_quest_projection.py`

**Interfaces:**
- Consumes: `DungeonStore.open_threads()`, `GameSnapshot.quest_log` (`game/session.py`: `dict[str, QuestEntry]`), `QuestEntry(title, objective, status, anchor_id)`.
- Produces: `reconcile_dungeon_quests_into_log(*, snapshot: GameSnapshot, store, reached_expansion_ids: set[int]) -> int` (writes/updates `QuestEntry` id `dungeon:exp{N}` for each open expansion-quest thread whose expansion is in `reached_expansion_ids`; returns count projected). Idempotent; only touches `dungeon:` ids.

- [ ] **Step 1: Write the failing test**

```python
# tests/dungeon/test_expansion_quest_projection.py
import sqlite3
from sidequest.dungeon.persistence import DungeonStore, ComplicationThread
from sidequest.game.session import GameSnapshot, QuestEntry
from sidequest.dungeon.expansion_quest import reconcile_dungeon_quests_into_log

def _store():
    conn = sqlite3.connect(":memory:"); conn.row_factory = sqlite3.Row
    s = DungeonStore(conn); s.ensure_schema(); return conn, s

def _thread(exp_id, region):
    return ComplicationThread(thread_id=f"q.exp{exp_id}.x", origin_region_id=region,
        kind="quest", status="open", started_at_depth_score=10.0,
        payload={"scope": "expansion", "expansion_id": exp_id, "signature_kind": "reach_deep",
                 "ref_id": region, "anchor_region": region, "title": "Go deep",
                 "objective": "Reach the bottom."})

def test_projection_writes_namespaced_entry_when_reached():
    conn, store = _store(); store.open_thread(_thread(1, "exp001.r2")); conn.commit()
    snap = GameSnapshot(genre_slug="caverns_and_claudes", world_slug="beneath_sunden")
    n = reconcile_dungeon_quests_into_log(snapshot=snap, store=store, reached_expansion_ids={1})
    assert n == 1
    entry = snap.quest_log["dungeon:exp1"]
    assert entry.objective == "Reach the bottom."
    assert entry.status == "active"
    assert entry.anchor_id == "exp001.r2"

def test_projection_skips_unreached_expansion():
    conn, store = _store(); store.open_thread(_thread(2, "exp002.r0")); conn.commit()
    snap = GameSnapshot(genre_slug="caverns_and_claudes", world_slug="beneath_sunden")
    n = reconcile_dungeon_quests_into_log(snapshot=snap, store=store, reached_expansion_ids=set())
    assert n == 0
    assert "dungeon:exp2" not in snap.quest_log

def test_projection_never_touches_non_dungeon_entries():
    conn, store = _store(); store.open_thread(_thread(1, "exp001.r0")); conn.commit()
    snap = GameSnapshot(genre_slug="caverns_and_claudes", world_slug="beneath_sunden")
    snap.quest_log["seed_drive"] = QuestEntry(title="My Drive", objective="x", status="active")
    reconcile_dungeon_quests_into_log(snapshot=snap, store=store, reached_expansion_ids={1})
    assert snap.quest_log["seed_drive"].title == "My Drive"  # untouched
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/dungeon/test_expansion_quest_projection.py -v`
Expected: FAIL — function missing.

- [ ] **Step 3: Implement** (append to `expansion_quest.py`)

```python
from sidequest.game.session import GameSnapshot, QuestEntry

_DUNGEON_QUEST_PREFIX = "dungeon:exp"

def reconcile_dungeon_quests_into_log(*, snapshot: GameSnapshot, store,
                                      reached_expansion_ids: set[int]) -> int:
    projected = 0
    for thread in store.open_threads():
        if thread.kind != "quest" or thread.payload.get("scope") != "expansion":
            continue
        exp_id = thread.payload.get("expansion_id")
        if exp_id not in reached_expansion_ids:
            continue
        qid = f"{_DUNGEON_QUEST_PREFIX}{exp_id}"
        existing = snapshot.quest_log.get(qid)
        title = thread.payload.get("title", "")
        objective = thread.payload.get("objective", "")
        anchor = thread.payload.get("anchor_region")
        if existing is None:
            snapshot.quest_log[qid] = QuestEntry(title=title, objective=objective,
                                                 status="active", anchor_id=anchor)
            if anchor and anchor not in snapshot.quest_anchors:
                snapshot.quest_anchors.append(anchor)
            projected += 1
        elif existing.status not in ("active",):
            continue  # already resolved/closed — don't reopen
    return projected
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/dungeon/test_expansion_quest_projection.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add sidequest/dungeon/expansion_quest.py tests/dungeon/test_expansion_quest_projection.py
git commit -m "feat(dungeon): project expansion-quest threads into quest_log (namespaced)"
```

---

### Task 6: Resolution — resolve an expansion quest on its signature beat

**Files:**
- Modify: `sidequest/dungeon/expansion_quest.py`
- Test: `tests/dungeon/test_expansion_quest_resolve.py`

**Interfaces:**
- Consumes: `DungeonStore.open_threads()` + `resolve_thread()`, `quest_resolved_span` (Task 2), `GameSnapshot.quest_log`.
- Produces: `resolve_expansion_quests(*, snapshot, store, reached_region_ids: set[str], resolved_trope_ids: list[str], defeated_npc_names: set[str]) -> int` — for each open expansion-quest thread, check whether its signature beat fired:
  - `reach_deep`: `anchor_region in reached_region_ids`
  - `set_piece`: `ref_id in resolved_trope_ids` (the signature set-piece's trope id — see Task 8 note)
  - `big_bad`: `ref_id in defeated_npc_names` (wired in Task 9b; pass `set()` until then)
  Resolves the ledger thread, flips the projected `QuestEntry.status="completed"`, emits `quest_resolved_span`. Returns count resolved.

- [ ] **Step 1: Write the failing test**

```python
# tests/dungeon/test_expansion_quest_resolve.py
import sqlite3
from sidequest.dungeon.persistence import DungeonStore, ComplicationThread
from sidequest.game.session import GameSnapshot, QuestEntry
from sidequest.dungeon.expansion_quest import resolve_expansion_quests

def _store():
    conn = sqlite3.connect(":memory:"); conn.row_factory = sqlite3.Row
    s = DungeonStore(conn); s.ensure_schema(); return conn, s

def _seed_thread(store, exp_id, sig, ref, region):
    store.open_thread(ComplicationThread(thread_id=f"q.exp{exp_id}.x", origin_region_id=region,
        kind="quest", status="open", started_at_depth_score=10.0,
        payload={"scope": "expansion", "expansion_id": exp_id, "signature_kind": sig,
                 "ref_id": ref, "anchor_region": region, "title": "t", "objective": "o"}))

def test_reach_deep_resolves_on_arrival():
    conn, store = _store(); _seed_thread(store, 1, "reach_deep", "exp001.r3", "exp001.r3"); conn.commit()
    snap = GameSnapshot(genre_slug="caverns_and_claudes", world_slug="beneath_sunden")
    snap.quest_log["dungeon:exp1"] = QuestEntry(title="t", objective="o", status="active", anchor_id="exp001.r3")
    n = resolve_expansion_quests(snapshot=snap, store=store, reached_region_ids={"exp001.r3"},
                                 resolved_trope_ids=[], defeated_npc_names=set())
    conn.commit()
    assert n == 1
    assert snap.quest_log["dungeon:exp1"].status == "completed"
    assert store.open_threads() == []   # ledger thread resolved

def test_unfired_beat_does_not_resolve():
    conn, store = _store(); _seed_thread(store, 1, "reach_deep", "exp001.r3", "exp001.r3"); conn.commit()
    snap = GameSnapshot(genre_slug="caverns_and_claudes", world_slug="beneath_sunden")
    snap.quest_log["dungeon:exp1"] = QuestEntry(title="t", objective="o", status="active", anchor_id="exp001.r3")
    n = resolve_expansion_quests(snapshot=snap, store=store, reached_region_ids=set(),
                                 resolved_trope_ids=[], defeated_npc_names=set())
    assert n == 0
    assert snap.quest_log["dungeon:exp1"].status == "active"
    assert len(store.open_threads()) == 1
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/dungeon/test_expansion_quest_resolve.py -v`
Expected: FAIL — function missing.

- [ ] **Step 3: Implement** (append to `expansion_quest.py`)

```python
from sidequest.telemetry.spans.dungeon_quest import quest_resolved_span

def _beat_fired(payload: dict, *, reached_region_ids, resolved_trope_ids, defeated_npc_names) -> str | None:
    kind = payload.get("signature_kind"); ref = payload.get("ref_id", "")
    if kind == "reach_deep" and payload.get("anchor_region") in reached_region_ids:
        return "reach_deep"
    if kind == "set_piece" and ref in resolved_trope_ids:
        return "set_piece"
    if kind == "big_bad" and ref in defeated_npc_names:
        return "hp_depletion"
    return None

def resolve_expansion_quests(*, snapshot: GameSnapshot, store,
                             reached_region_ids: set[str],
                             resolved_trope_ids: list[str],
                             defeated_npc_names: set[str]) -> int:
    resolved = 0
    for thread in store.open_threads():
        if thread.kind != "quest" or thread.payload.get("scope") != "expansion":
            continue
        event = _beat_fired(thread.payload, reached_region_ids=reached_region_ids,
                            resolved_trope_ids=resolved_trope_ids, defeated_npc_names=defeated_npc_names)
        if event is None:
            continue
        exp_id = thread.payload.get("expansion_id")
        with quest_resolved_span(expansion_id=exp_id,
                                 signature_kind=thread.payload.get("signature_kind", ""),
                                 resolving_event=event):
            store.resolve_thread(thread.thread_id)
            entry = snapshot.quest_log.get(f"dungeon:exp{exp_id}")
            if entry is not None:
                entry.status = "completed"
        resolved += 1
    return resolved
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/dungeon/test_expansion_quest_resolve.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add sidequest/dungeon/expansion_quest.py tests/dungeon/test_expansion_quest_resolve.py
git commit -m "feat(dungeon): resolve expansion quests on their signature beat"
```

---

### Task 7: Wire seed into the materializer attach stage

**Files:**
- Modify: `sidequest/dungeon/materializer.py` (the attach stage `_stage_attach`, at/after the per-region `attach_set_piece` loop, inside the same `tx`)
- Test: `tests/dungeon/test_expansion_quest_materializer_wiring.py`

**Interfaces:**
- Consumes: `seed_expansion_quest` (Task 4); the materializer's in-scope `campaign_seed`, the `Expansion`, the per-region manifests it already built in `_stage_design`, the theme palette (`load_theme_palette` result → `DungeonTheme.quest_template`), the `tx` (DungeonStore), and a representative `started_at_depth_score`.
- Produces: exactly one `seed_expansion_quest(...)` call per expansion attach, guarded so it's a no-op when the expansion's theme has no `quest_template`.

- [ ] **Step 1: Read the attach stage**

Read `sidequest/dungeon/materializer.py` around `_stage_attach` and the `attach_set_piece` call site (per extraction §8 the loop lives there). Identify: the variable holding the `Expansion`, the dict of per-region `RegionContentManifest`, how the theme for a region is resolved to a `DungeonTheme`, and the `tx` name.

- [ ] **Step 2: Write the failing wiring test**

Mirror `tests/dungeon/test_setpiece_attach_wiring.py`. Build a synthetic expansion + a theme palette whose theme carries a `quest_template`, drive the real `_stage_attach` (or the smallest real entry that runs it) with an in-memory `DungeonStore`, then assert exactly one open expansion-scoped quest thread exists and a `dungeon.quest.bound` span fired.

```python
# tests/dungeon/test_expansion_quest_materializer_wiring.py
# (fixture skeleton — fill the real _stage_attach entry from Step 1)
def test_attach_seeds_one_expansion_quest_thread():
    # ... build in-memory store, synthetic Expansion w/ theme that has quest_template ...
    # ... call the real attach stage ...
    quest_threads = [t for t in store.open_threads()
                     if t.kind == "quest" and t.payload.get("scope") == "expansion"]
    assert len(quest_threads) == 1
    assert quest_threads[0].payload["expansion_id"] == EXPANSION_ID
```

- [ ] **Step 3: Run to verify it fails**

Run: `uv run pytest tests/dungeon/test_expansion_quest_materializer_wiring.py -v`
Expected: FAIL — no quest thread (seed not yet called).

- [ ] **Step 4: Add the call in `_stage_attach`** (after the set-piece loop, inside `tx`)

```python
from sidequest.dungeon.expansion_quest import seed_expansion_quest
# theme: DungeonTheme for the expansion (resolve via the palette as the stage already does)
if theme.quest_template is not None:
    seed_expansion_quest(
        campaign_seed=campaign_seed, expansion=expansion,
        manifests_by_region=manifests_by_region, template=theme.quest_template,
        store=tx, started_at_depth_score=started_at_depth_score,
    )
```

> Use the variable names found in Step 1. If an expansion spans multiple themes, seed from the deepest region's theme (consistent with `select_signature`'s `_deepest`).

- [ ] **Step 5: Run to verify it passes; then full dungeon suite**

Run: `uv run pytest tests/dungeon/test_expansion_quest_materializer_wiring.py -v`
Expected: PASS.
Run: `uv run pytest tests/dungeon/ -v`
Expected: PASS (no regressions).

- [ ] **Step 6: Commit**

```bash
git add sidequest/dungeon/materializer.py tests/dungeon/test_expansion_quest_materializer_wiring.py
git commit -m "feat(dungeon): seed per-expansion quest at materializer attach"
```

---

### Task 8: Wire projection + resolution into the frontier-transition seam

**Files:**
- Modify: `sidequest/dungeon/session_integration.py` (register a frontier observer that closes over the session's `DungeonStore`)
- Test: `tests/dungeon/test_expansion_quest_frontier_wiring.py`

**Interfaces:**
- Consumes: `register_frontier_observer` (`frontier_hook.py`: observer signature `observer(*, snapshot, pc_name, from_region, to_region)`), `reconcile_dungeon_quests_into_log` + `resolve_expansion_quests` (Tasks 5/6), the session `DungeonStore` (available where the look-ahead worker is registered — extraction §1/§8).
- Produces: an observer that, on each region transition, (1) computes the reached expansion id from `to_region` (parse `exp{N}.rM`), (2) reconciles open expansion-quest threads for reached expansions into `quest_log`, (3) resolves any whose `reach_deep`/`set_piece` beat fired this transition. `set_piece`/`big_bad` trope+combat resolution is threaded in Tasks already present (resolved_trope_ids) / deferred (Task 10).

- [ ] **Step 1: Write the failing wiring test**

Register the real observer (via the integration's registration entry point), then call the real `notify_region_transition(snapshot, pc_name=..., from_region=None, to_region="exp001.r0")` and assert a `dungeon:exp1` QuestEntry appears in `snapshot.quest_log`; then transition into the anchor region and assert it flips to `completed`.

```python
# tests/dungeon/test_expansion_quest_frontier_wiring.py
def test_transition_projects_then_resolves():
    # ... in-memory store, seed an expansion-quest thread (reach_deep anchor exp001.r1) ...
    # ... register the integration's frontier observer bound to this store ...
    notify_region_transition(snap, pc_name="Chico", from_region=None, to_region="exp001.r0")
    assert "dungeon:exp1" in snap.quest_log          # projected on entering the expansion
    assert snap.quest_log["dungeon:exp1"].status == "active"
    notify_region_transition(snap, pc_name="Chico", from_region="exp001.r0", to_region="exp001.r1")
    assert snap.quest_log["dungeon:exp1"].status == "completed"  # reach_deep beat fired
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/dungeon/test_expansion_quest_frontier_wiring.py -v`
Expected: FAIL — observer not registered / quest not projected.

- [ ] **Step 3: Implement the observer + register it**

In `session_integration.py`, where the look-ahead worker handle/store is set up, add:

```python
from sidequest.dungeon.expansion_quest import (
    reconcile_dungeon_quests_into_log, resolve_expansion_quests,
)
from sidequest.dungeon.frontier_hook import register_frontier_observer

def _expansion_id_of(region_id: str) -> int | None:
    # region ids look like "exp001.r3"; surface entrance ("entrance") has none.
    if not region_id.startswith("exp"):
        return None
    try:
        return int(region_id.split(".", 1)[0][3:])
    except ValueError:
        return None

def make_expansion_quest_observer(store):
    def _observer(*, snapshot, pc_name, from_region, to_region):
        exp_id = _expansion_id_of(to_region)
        reached_exps = {exp_id} if exp_id is not None else set()
        reconcile_dungeon_quests_into_log(snapshot=snapshot, store=store,
                                          reached_expansion_ids=reached_exps)
        resolve_expansion_quests(snapshot=snapshot, store=store,
                                 reached_region_ids={to_region},
                                 resolved_trope_ids=[], defeated_npc_names=set())
    return _observer
```

Register it (and unregister on detach) alongside the worker registration. Match the existing register/unregister lifecycle in `attach_dungeon_to_session` / `detach_dungeon_from_session`.

- [ ] **Step 4: Run to verify it passes; full dungeon suite**

Run: `uv run pytest tests/dungeon/test_expansion_quest_frontier_wiring.py -v` → PASS
Run: `uv run pytest tests/dungeon/ -v` → PASS

- [ ] **Step 5: Commit**

```bash
git add sidequest/dungeon/session_integration.py tests/dungeon/test_expansion_quest_frontier_wiring.py
git commit -m "feat(dungeon): project+resolve expansion quests on frontier transition"
```

---

### Task 9: `set_piece` resolution via the trope handshake

**Files:**
- Modify: `sidequest/dungeon/session_integration.py` (thread the turn's `resolved_trope_ids` into the observer or its turn-level caller) OR the 45-20 handshake site that already calls `resolve_complications_for_resolved_tropes`.
- Test: extend `tests/dungeon/test_expansion_quest_frontier_wiring.py` (or a new turn-level test)

**Interfaces:**
- Consumes: the per-turn `resolved_trope_ids` list the existing `resolve_complications_for_resolved_tropes(resolved_trope_ids=..., store=...)` already receives (extraction §3).
- Produces: a per-turn call to `resolve_expansion_quests(..., resolved_trope_ids=<that list>, ...)` so a `set_piece`-signature quest whose set-piece trope resolved this turn completes. The `set_piece` template's `set_piece_id` must equal the trope id the signature set-piece carries (document this in Task 11 content).

- [ ] **Step 1: Locate the 45-20 handshake call site**

Find where `resolve_complications_for_resolved_tropes` is invoked per turn (the narrator-turn trope-resolution subscription). That site has both `resolved_trope_ids` and access to the session/store/snapshot.

- [ ] **Step 2: Write the failing test**

Seed a `set_piece`-signature expansion quest with `ref_id="the_keeper_wakes"`; drive the handshake site with `resolved_trope_ids=["the_keeper_wakes"]`; assert the quest flips to `completed`.

- [ ] **Step 3: Add the call** next to the existing `resolve_complications_for_resolved_tropes(...)`:

```python
resolve_expansion_quests(
    snapshot=snapshot, store=store, reached_region_ids=set(),
    resolved_trope_ids=resolved_trope_ids, defeated_npc_names=set(),
)
```

- [ ] **Step 4: Run to verify it passes; full dungeon suite** → PASS

- [ ] **Step 5: Commit**

```bash
git commit -am "feat(dungeon): resolve set_piece-signature expansion quests via trope handshake"
```

---

### Task 10 (PHASED — needs investigation): `big_bad` resolution via combat hp_depletion

**Files:** TBD after Step 1 investigation.
**Test:** `tests/dungeon/test_expansion_quest_big_bad_resolve.py`

**Interfaces:**
- Consumes: the combat `hp_depletion` win-condition event (the event that fires when an NPC reaches 0 HP — `creature_core.py` `HpPool` / the confrontation engine; emits a `state_patch_hp` span per the server CLAUDE.md). `resolve_expansion_quests` already accepts `defeated_npc_names: set[str]`.
- Produces: a per-turn collection of NPC names that hit `hp_depletion` this turn, passed into `resolve_expansion_quests(..., defeated_npc_names=...)`.

- [ ] **Step 1: Investigate** where `hp_depletion` resolves and whether a per-turn "who died" set is already available (grep `hp_depletion`, `state_patch_hp`, the confrontation win-condition path). Do NOT fabricate the hook — confirm it.
- [ ] **Step 2:** Write the failing test (an expansion quest with `signature="big_bad"`, `ref_id="Bone Tyrant"`; simulate the bound NPC's death; assert the quest completes).
- [ ] **Step 3:** Collect defeated NPC names at the resolution site and pass them in.
- [ ] **Step 4:** Run; full dungeon + relevant combat suite → PASS.
- [ ] **Step 5:** Commit.

> If the combat-event hook proves heavier than a sprint task, ship `big_bad` themes against `reach_deep` semantics (the loud degrade path already covers this) and track `big_bad` resolution as a follow-up story. Do not block Tasks 1–9 on it.

---

### Task 11: Author `beneath_sunden` theme `quest_template`s (content)

**Files:**
- Modify: `genre_packs/caverns_and_claudes/worlds/beneath_sunden/themes/*.yaml` (sidequest-content repo)
- Test: a content-validation test that `load_theme_palette(beneath_sunden_dir)` parses and every theme has a `quest_template` (extend an existing pack-load test, or add `tests/dungeon/test_beneath_sunden_quest_templates.py`).

**Interfaces:**
- Consumes: the `quest_template` schema (Task 1). For `set_piece` signatures, `set_piece_id` must equal the trope id the chosen signature set-piece carries (Task 9 contract).

- [ ] **Step 1: Write the failing content test**

```python
# tests/dungeon/test_beneath_sunden_quest_templates.py
from pathlib import Path
from sidequest.dungeon.themes import load_theme_palette

def test_every_beneath_sunden_theme_has_a_quest_template():
    pack_dir = Path("...beneath_sunden")  # resolve via the project's content-path fixture
    palette = load_theme_palette(pack_dir)
    for tid, theme in palette.themes.items():
        assert theme.quest_template is not None, f"theme {tid} missing quest_template"
```

- [ ] **Step 2: Run to verify it fails** → FAIL (themes lack the block).

- [ ] **Step 3: Add a `quest_template` to each theme YAML.** Example for `bone_crypt.yaml`:

```yaml
quest_template:
  signature: reach_deep
  title: "Into the {theme}"
  objective: "The ossuary swallows the lamplight. Find the way down through it."
```

Author per-theme; prefer `reach_deep` (always resolvable) unless a theme has a stable signature set-piece (use `set_piece` + matching `set_piece_id`) or a guaranteed big_bad at its depth band (`big_bad`).

- [ ] **Step 4: Run to verify it passes** → PASS. Also run `uv run pytest tests/dungeon/ -v`.

- [ ] **Step 5: Commit** (in sidequest-content)

```bash
git add genre_packs/caverns_and_claudes/worlds/beneath_sunden/themes/
git commit -m "content(beneath_sunden): per-expansion quest_templates"
```

---

### Task 12: Mandatory end-to-end wiring + determinism test

**Files:**
- Test: `tests/dungeon/test_expansion_quest_e2e.py`

**Interfaces:** Consumes the whole chain (Tasks 1–8).

- [ ] **Step 1: Write the end-to-end test**

Drive the real attach (seed) → real `notify_region_transition` (project) → real transition into the anchor (resolve), asserting on emitted OTEL spans and `quest_log` state, plus a determinism assertion:

```python
# tests/dungeon/test_expansion_quest_e2e.py
def test_seed_project_resolve_and_spans():
    # 1) attach a synthetic expansion (theme has reach_deep quest_template) -> quest.seed + dungeon.quest.bound
    # 2) notify_region_transition into the expansion -> QuestEntry dungeon:expN appears, status=active, QUESTS-emittable
    # 3) notify_region_transition into the anchor region -> status=completed, ledger.resolve + dungeon.quest.resolved
    ...

def test_same_seed_same_quest():
    # materialize the same expansion twice from one campaign_seed; assert identical title/objective/binding (Amendment C parity)
    ...
```

- [ ] **Step 2: Run to verify it fails (before any gaps closed) / passes (after Tasks 1–8)**

Run: `uv run pytest tests/dungeon/test_expansion_quest_e2e.py -v`
Expected: PASS once Tasks 1–8 are in.

- [ ] **Step 3: Run the whole dungeon + quest suites**

Run: `uv run pytest tests/dungeon/ tests/server/test_quests_emit_wiring.py -v`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/dungeon/test_expansion_quest_e2e.py
git commit -m "test(dungeon): e2e per-expansion quest seed->project->resolve + determinism"
```

---

## Self-Review

**1. Spec coverage:**
- §3 signature beat → Task 3 (select), Task 6 (resolve), Task 10 (big_bad phased). ✓
- §4.1 theme template → Task 1, Task 11. ✓
- §4.2 seed at attach → Task 4, Task 7 (wiring). ✓
- §4.3 projection bridge → Task 5, Task 8 (wiring). ✓
- §4.4 resolution → Task 6, Task 8 (reach_deep), Task 9 (set_piece), Task 10 (big_bad). ✓
- §4.5 OTEL → Task 2 (+ reused `quest.seed`/`ledger.*`). ✓
- §7 testing/wiring/determinism → wiring tests in Tasks 7/8, e2e+determinism in Task 12. ✓
- §8 coexistence (namespaced ids, never clobber drive-spine) → Task 5 test. ✓
- **Dependency on 158-15** (resume visibility): not a task here; called out as a cross-story dependency in the spec. Resume re-emit is owned by 158-15. ✓ (no gap — out of scope by design)

**2. Placeholder scan:** Task 7/8/9/10 contain explicit "read/locate/investigate" steps rather than fabricated call sites — this is deliberate: the materializer `_stage_attach` body and the 45-20 handshake site and the hp_depletion hook were NOT captured verbatim in extraction, so inventing exact line edits would be a worse error than directing the implementer to the verified anchor and having them read the surrounding code. Task 10 is explicitly phased with an investigation gate. No `TBD`/`TODO` in the high-confidence tasks (1–6, 12).

**3. Type consistency:** `SignatureBinding` fields (kind/ref_id/anchor_region/title/objective/degraded) are consistent across Tasks 3→4. `seed_expansion_quest` returns `thread_id: str` (Task 4) consumed by no later task by value (threads are re-read from the store). `reconcile_dungeon_quests_into_log` and `resolve_expansion_quests` signatures are consistent between their defining tasks (5/6) and their wiring (8/9). Thread payload keys (`scope`, `expansion_id`, `signature_kind`, `ref_id`, `anchor_region`, `title`, `objective`) are identical across seed (4), projection (5), and resolve (6). Quest id format `dungeon:exp{N}` consistent (5/6/8). ✓
