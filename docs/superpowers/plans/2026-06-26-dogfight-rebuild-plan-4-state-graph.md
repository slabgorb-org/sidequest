# Dogfight Rebuild — Plan 4: Full Relative-Position State Graph Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the dogfight from a single-table duel into the Ace of Aces relative-position **state graph** (ADR-153 §3): multiple per-state interaction tables (`merge`, `tail_chase`, `beam`, `overhead`, `scissors`, `overshoot`), a current-state tracked on the encounter, cell-driven transitions between states across turns, and extend-and-return as a true transition back to `merge`.

**Architecture:** Today the engine is single-table-per-duel — one `interaction_table` on the def, no `current_state` on the encounter, no `next_state` on cells; `interactions_tail_chase.yaml` is authored but orphaned; extend-and-return resets the *descriptor* within the same table. This plan adds: (1) a **table registry** (`interaction_tables` keyed by state id) on the ConfrontationDef, loaded via multiple `_from:` pointers; (2) a **`next_state`** field on the cell; (3) a **`dogfight_state`** field on the encounter; (4) resolver/caller logic that selects the current state's table, applies the cell, and transitions `dogfight_state` to the cell's `next_state` for the next turn; (5) the four new state tables as content. The cells still carry geometry + `gun_solution` only (firewall, ADR-153 §2); resolution stays SWN.

**Tech Stack:** Python 3.12 / pydantic v2 / FastAPI (sidequest-server), YAML genre packs (sidequest-content), pytest + pytest-xdist (`-n0` for OTEL-span tests), OpenTelemetry spans.

## Global Constraints

- **Depends on Plan 1 (firewall) merged.** Independent of Plan 3 (opponent brain) — they touch different surfaces and can land in either order.
- **Firewall (ADR-153 §2):** cells carry geometry + `gun_solution` + (new) `next_state` only. No damage, no dial. Resolution is SWN.
- **No silent fallbacks (CLAUDE.md):** an unknown `next_state` (no table for it) fails loud, never silently stays in the current state.
- **Back-compat:** a def with only the legacy single `interaction_table` (e.g. any other pack that ever declares a sealed-letter confrontation) keeps working — the registry falls back to `{starting_state: interaction_table}`.
- **Resume-safe:** `dogfight_state` is serialized on the encounter so a reload resumes mid-graph in the correct state.
- **OTEL:** the state transition each turn emits a span so the GM panel sees the graph move (`dogfight.state_transition` with from/to).
- **Branching:** sidequest-server + sidequest-content target `develop`; branch `feat/158-40-dogfight-state-graph`.

---

## Task 1: Add `next_state` to `InteractionCell` and a table registry to `ConfrontationDef`

**Files:**
- Modify: `sidequest-server/sidequest/genre/models/rules.py` (`InteractionCell`: add `next_state`; `ConfrontationDef`: add `interaction_tables`)
- Test: `sidequest-server/tests/genre/test_state_graph_models.py`

**Interfaces:**
- Produces: `InteractionCell.next_state: str | None`; `ConfrontationDef.interaction_tables: dict[str, InteractionTable]` (keyed by each table's `starting_state`).

- [ ] **Step 1: Write the failing test**

Create `sidequest-server/tests/genre/test_state_graph_models.py`:

```python
from sidequest.genre.models.rules import InteractionCell, InteractionTable, ConfrontationDef


def test_cell_accepts_next_state():
    c = InteractionCell(pair=["straight", "loop"], red_view={}, blue_view={}, next_state="tail_chase")
    assert c.next_state == "tail_chase"


def test_cell_next_state_defaults_none():
    c = InteractionCell(pair=["straight", "straight"], red_view={}, blue_view={})
    assert c.next_state is None


def test_confrontation_def_holds_table_registry():
    merge = InteractionTable(version="1", starting_state="merge",
                             cells=[InteractionCell(pair=["a", "b"], red_view={}, blue_view={})])
    d = ConfrontationDef(type="dogfight", label="x", category="combat",
                         resolution_mode="sealed_letter_lookup",
                         interaction_tables={"merge": merge})
    assert d.interaction_tables["merge"].starting_state == "merge"
```

- [ ] **Step 2: Run to confirm failure**

Run: `cd sidequest-server && uv run pytest tests/genre/test_state_graph_models.py -v -n0`
Expected: FAIL — `next_state` rejected by `extra: forbid`; `interaction_tables` unknown.

- [ ] **Step 3: Add the fields**

In `sidequest/genre/models/rules.py`:

`class InteractionCell` — add after `narration_hint`:
```python
    next_state: str | None = None  # ADR-153: relative-position state to transition INTO next turn (None = stay)
```

`class ConfrontationDef` — add beside `interaction_table`:
```python
    interaction_tables: dict[str, InteractionTable] = Field(default_factory=dict)
```

- [ ] **Step 4: Run to confirm pass**

Run: `cd sidequest-server && uv run pytest tests/genre/test_state_graph_models.py -v -n0`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
cd sidequest-server && git checkout develop && git pull && git checkout -b feat/158-40-dogfight-state-graph
git add sidequest/genre/models/rules.py tests/genre/test_state_graph_models.py
git commit -m "feat(dogfight): InteractionCell.next_state + ConfrontationDef.interaction_tables registry (ADR-153)"
```

---

## Task 2: Loader — resolve a list of per-state table `_from:` pointers into the registry

Extend the loader so the dogfight def can declare a list of state tables, each via `_from:`, resolved into `interaction_tables` keyed by each table's `starting_state`. Keep the single `interaction_table` (merge) working and auto-register it.

**Files:**
- Modify: `sidequest-server/sidequest/genre/loader.py` (`_load_rules_config`, where `interaction_table`'s `_from:` resolves)
- Test: `sidequest-server/tests/genre/test_state_graph_loader.py`

**Interfaces:**
- Consumes: a content shape `interaction_tables: [{_from: dogfight/interactions_merge.yaml}, ...]`.
- Produces: `cdef.interaction_tables == {"merge": <table>, "tail_chase": <table>, ...}`.

- [ ] **Step 1: Read the existing `_from:` resolution**

```bash
cd sidequest-server && sed -n '260,340p' sidequest/genre/loader.py
```
Note the exact function + how it rejects absolute paths / parent traversal / nested `_from:`. The new resolution reuses that helper.

- [ ] **Step 2: Write the failing test (fixture pack with two state tables)**

Create `sidequest-server/tests/genre/test_state_graph_loader.py`. Use the existing SWN test pack (`tests/fixtures/packs/swn_test_pack/`) — it already has `dogfight/` tables. Point its dogfight def at an `interaction_tables` list and assert both states load:

```python
from sidequest.genre.loader import load_genre_pack_from_dir  # confirm the dir-loader entrypoint
from pathlib import Path


def test_loads_multiple_state_tables(tmp_path):
    # Arrange: the swn_test_pack dogfight def declares interaction_tables: [merge, tail_chase].
    pack = load_genre_pack_from_dir(Path("tests/fixtures/packs/swn_test_pack"))
    d = next(c for c in pack.rules.confrontations if c.confrontation_type == "dogfight")
    assert set(d.interaction_tables) >= {"merge", "tail_chase"}
    assert d.interaction_tables["tail_chase"].starting_state == "tail_chase"
```

(Confirm the dir-loader name; the existing dogfight content loading test in `tests/genre/` shows the entrypoint. Edit `tests/fixtures/packs/swn_test_pack/.../rules.yaml`'s dogfight def to use `interaction_tables: [{_from: dogfight/interactions_mvp.yaml}, {_from: dogfight/interactions_tail_chase.yaml}]` as part of this step.)

- [ ] **Step 3: Run to confirm failure**

Run: `cd sidequest-server && uv run pytest tests/genre/test_state_graph_loader.py -v -n0`
Expected: FAIL — `interaction_tables` not resolved from the `_from:` list (empty dict).

- [ ] **Step 4: Resolve the list in the loader**

In `_load_rules_config`, after the existing single-`interaction_table` resolution, add: if `conf` has an `interaction_tables` list, resolve each entry's `_from:` (reusing the same pointer helper), parse each into the InteractionTable shape, and build a dict keyed by each resolved table's `starting_state`. Also: if a def has a single `interaction_table` and no `interaction_tables`, auto-register `{table.starting_state: table}` so back-compat holds. Fail loud on a duplicate `starting_state` key or a missing `starting_state`.

```python
        # ADR-153 state graph: a dogfight may declare a LIST of per-state tables,
        # each via _from:. Resolve each and key by its starting_state. Back-compat:
        # a single interaction_table auto-registers as {its starting_state: it}.
        tables_spec = conf.get("interaction_tables")
        if tables_spec:
            resolved_tables = {}
            for entry in tables_spec:
                t = _resolve_from_pointer(entry, pack_dir)   # same helper as interaction_table
                state = t.get("starting_state")
                if not state:
                    raise GenreLoadError(f"interaction_tables entry missing starting_state: {entry}")
                if state in resolved_tables:
                    raise GenreLoadError(f"duplicate interaction_tables starting_state: {state!r}")
                resolved_tables[state] = t
            conf["interaction_tables"] = resolved_tables
        elif conf.get("interaction_table"):
            it = conf["interaction_table"]
            conf["interaction_tables"] = {it["starting_state"]: it}
```

(Use the real helper name found in Step 1 for `_resolve_from_pointer`; match `GenreLoadError`'s actual name.)

- [ ] **Step 5: Run to confirm pass**

Run: `cd sidequest-server && uv run pytest tests/genre/test_state_graph_loader.py -v -n0`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd sidequest-server && git add sidequest/genre/loader.py tests/genre/test_state_graph_loader.py tests/fixtures/packs/swn_test_pack/
git commit -m "feat(dogfight): loader resolves per-state interaction_tables registry via _from: list (ADR-153)"
```

---

## Task 3: Track current state on the encounter (`dogfight_state`)

**Files:**
- Modify: `sidequest-server/sidequest/game/encounter.py` (`StructuredEncounter`: add `dogfight_state`)
- Test: `sidequest-server/tests/game/test_encounter_dogfight_state.py`

**Interfaces:**
- Produces: `StructuredEncounter.dogfight_state: str | None` (None for non-dogfight; the entry state id for a dogfight), serialized for resume-safety.

- [ ] **Step 1: Write the failing test**

Create `sidequest-server/tests/game/test_encounter_dogfight_state.py`:

```python
from sidequest.game.encounter import StructuredEncounter


def test_dogfight_state_defaults_none():
    enc = StructuredEncounter(encounter_type="dogfight", win_condition="hp_depletion")
    assert enc.dogfight_state is None


def test_dogfight_state_roundtrips_on_serialize():
    enc = StructuredEncounter(encounter_type="dogfight", win_condition="hp_depletion")
    enc.dogfight_state = "tail_chase"
    restored = StructuredEncounter.model_validate(enc.model_dump())
    assert restored.dogfight_state == "tail_chase"
```

(Confirm `StructuredEncounter`'s constructor kwargs against `encounter.py`; adjust if `win_condition` is set differently.)

- [ ] **Step 2: Run to confirm failure**

Run: `cd sidequest-server && uv run pytest tests/game/test_encounter_dogfight_state.py -v -n0`
Expected: FAIL — no `dogfight_state` field.

- [ ] **Step 3: Add the field**

In `sidequest/game/encounter.py`, `class StructuredEncounter`, add beside the other per-variant fields (near `secondary_stats`):

```python
    dogfight_state: str | None = None  # ADR-153: current relative-position state id (merge/tail_chase/beam/...)
```

- [ ] **Step 4: Run to confirm pass**

Run: `cd sidequest-server && uv run pytest tests/game/test_encounter_dogfight_state.py -v -n0`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
cd sidequest-server && git add sidequest/game/encounter.py tests/game/test_encounter_dogfight_state.py
git commit -m "feat(dogfight): track current relative-position state on the encounter (ADR-153)"
```

---

## Task 4: Resolver surfaces `next_state`; set `dogfight_state` at instantiation

The pure resolver reads the chosen cell's `next_state` and returns it on the outcome. Extend-and-return returns the entry state. Instantiation stamps the entry `dogfight_state`.

**Files:**
- Modify: `sidequest-server/sidequest/server/dispatch/sealed_letter.py` (`SealedLetterOutcome.next_state`; resolver sets it; extend-and-return returns entry state)
- Modify: `sidequest-server/sidequest/server/dispatch/encounter_lifecycle.py` (sealed-letter instantiation: stamp `enc.dogfight_state` = the def's entry state)
- Test: `sidequest-server/tests/server/dispatch/test_sealed_letter_next_state.py`

**Interfaces:**
- Consumes: `InteractionCell.next_state` (Task 1), `enc.dogfight_state` (Task 3).
- Produces: `SealedLetterOutcome.next_state: str | None`.

- [ ] **Step 1: Write the failing test**

Create `sidequest-server/tests/server/dispatch/test_sealed_letter_next_state.py`:

```python
from sidequest.game.encounter import EncounterActor, StructuredEncounter
from sidequest.genre.models.rules import InteractionCell, InteractionTable
from sidequest.server.dispatch.sealed_letter import resolve_sealed_letter_lookup


def _enc():
    enc = StructuredEncounter(encounter_type="dogfight", win_condition="hp_depletion")
    enc.actors = [EncounterActor(name="PC", role="red", side="player"),
                  EncounterActor(name="Ace", role="blue", side="opponent")]
    return enc


def test_outcome_carries_cell_next_state():
    table = InteractionTable(version="1", starting_state="merge", maneuvers_consumed=["straight", "loop"],
        cells=[InteractionCell(pair=["straight", "loop"], red_view={"gun_solution": False},
                               blue_view={"gun_solution": False}, next_state="tail_chase")])
    out = resolve_sealed_letter_lookup(_enc(), {"red": "straight", "blue": "loop"}, table)
    assert out.next_state == "tail_chase"


def test_outcome_next_state_none_when_cell_stays():
    table = InteractionTable(version="1", starting_state="merge", maneuvers_consumed=["straight"],
        cells=[InteractionCell(pair=["straight", "straight"], red_view={}, blue_view={})])
    out = resolve_sealed_letter_lookup(_enc(), {"red": "straight", "blue": "straight"}, table)
    assert out.next_state is None
```

- [ ] **Step 2: Run to confirm failure**

Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_sealed_letter_next_state.py -v -n0`
Expected: FAIL — `SealedLetterOutcome` has no `next_state`.

- [ ] **Step 3: Add `next_state` to the outcome + set it in the resolver**

In `sidequest/server/dispatch/sealed_letter.py`:
- Add `next_state: str | None = None` to the `SealedLetterOutcome` dataclass.
- In `resolve_sealed_letter_lookup`, after the cell is looked up and deltas applied, set the outcome's `next_state = cell.next_state`.
- In `_maybe_apply_extend_and_return`: when the reset fires, the outcome's `next_state` should be the entry state `"merge"` (the geometry reset IS a transition back to merge). Have the resolver set `next_state = "merge"` when `_maybe_apply_extend_and_return` returns True (extend-and-return wins over a cell `next_state`).

(Confirm the `SealedLetterOutcome` field list + where the cell is resolved against the current code — quote with `sed -n '60,230p' sidequest/server/dispatch/sealed_letter.py` first.)

- [ ] **Step 4: Stamp the entry state at instantiation**

In `sidequest/server/dispatch/encounter_lifecycle.py`, in the sealed-letter instantiation branch (where the red/blue actors are seated, ~line 1805+), after the encounter is built set:

```python
            # ADR-153: a dogfight starts in its registry's entry state (the
            # def's single starting_state; "merge" by default). Resume-safe.
            enc.dogfight_state = (
                cdef.interaction_table.starting_state
                if cdef.interaction_table is not None
                else next(iter(cdef.interaction_tables), None)
            )
```

- [ ] **Step 5: Run to confirm pass**

Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_sealed_letter_next_state.py -v -n0`
Expected: PASS (2 tests).

- [ ] **Step 6: Commit**

```bash
cd sidequest-server && git add sidequest/server/dispatch/sealed_letter.py sidequest/server/dispatch/encounter_lifecycle.py tests/server/dispatch/test_sealed_letter_next_state.py
git commit -m "feat(dogfight): resolver surfaces next_state; instantiation stamps entry dogfight_state (ADR-153)"
```

---

## Task 5: Select the current-state table + apply the transition each turn (the state machine)

Wire the graph in the sealed-letter apply path: pick the table for `enc.dogfight_state` from the registry, resolve against it, then advance `enc.dogfight_state` to the outcome's `next_state`. Emit the `dogfight.state_transition` span. Fail loud on an unknown target state.

**Files:**
- Modify: `sidequest-server/sidequest/server/narration_apply.py` (sealed-letter branch, where `cdef.interaction_table` is passed to `resolve_sealed_letter_lookup`, ~line 6095)
- Modify: `sidequest-server/sidequest/telemetry/spans/dogfight.py` (new `dogfight_state_transition_span`)
- Test: `sidequest-server/tests/server/dispatch/test_dogfight_state_machine.py`

**Interfaces:**
- Consumes: `cdef.interaction_tables` (Task 2), `enc.dogfight_state` (Task 3), `SealedLetterOutcome.next_state` (Task 4).

- [ ] **Step 1: Add the state-transition span**

In `sidequest/telemetry/spans/dogfight.py`, add (mirroring `dogfight_cell_resolved_span`):

```python
SPAN_DOGFIGHT_STATE_TRANSITION = "dogfight.state_transition"

@contextmanager
def dogfight_state_transition_span(*, from_state: str, to_state: str, **attrs: Any) -> Iterator[trace.Span]:
    with Span.open(SPAN_DOGFIGHT_STATE_TRANSITION,
                   {"from_state": from_state, "to_state": to_state, **attrs}) as span:
        yield span
```

- [ ] **Step 2: Write the failing state-machine test**

Create `sidequest-server/tests/server/dispatch/test_dogfight_state_machine.py`: drive two sealed-letter turns through the real apply path; turn 1's cell carries `next_state="tail_chase"`, assert turn 2 resolves against the tail_chase table (a tail_chase-only cell outcome) and `enc.dogfight_state == "tail_chase"`, with a `dogfight.state_transition` span (merge→tail_chase).

```python
def test_duel_transitions_merge_to_tail_chase(span_exporter):
    snap, pack = make_seated_dogfight_snapshot()   # dogfight def with interaction_tables {merge, tail_chase}
    assert snap.encounter.dogfight_state == "merge"
    # Turn 1: a merge cell whose next_state is tail_chase.
    _drive_sealed_letter_turn(snap, pack, red_maneuver="straight", blue_maneuver="loop")
    assert snap.encounter.dogfight_state == "tail_chase"
    spans = [s for s in span_exporter.get_finished_spans() if s.name.endswith("state_transition")]
    assert any(s.attributes.get("to_state") == "tail_chase" for s in spans)
```

(Requires the merge table's `[straight, loop]` cell to carry `next_state: tail_chase` — authored in Task 6; for this unit test, the fixture pack's tables must include that transition. Build the fixture to do so.)

- [ ] **Step 3: Run to confirm failure**

Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_dogfight_state_machine.py -v -n0`
Expected: FAIL — the apply path always uses `cdef.interaction_table` (merge); `dogfight_state` never changes.

- [ ] **Step 4: Wire the state machine at the apply seam**

In `sidequest/server/narration_apply.py`, in the sealed-letter branch, replace the `cdef.interaction_table` argument to `resolve_sealed_letter_lookup` (line ~6098) with the current-state table, and apply the transition after:

```python
                # ADR-153 state graph: resolve against the CURRENT state's table.
                current_state = enc.dogfight_state or (
                    cdef.interaction_table.starting_state if cdef.interaction_table else None
                )
                active_table = cdef.interaction_tables.get(current_state) or cdef.interaction_table
                if active_table is None:
                    raise ValueError(
                        f"dogfight {enc.encounter_type!r}: no interaction table for "
                        f"state {current_state!r} (registry: {sorted(cdef.interaction_tables)})"
                    )

                sl_outcome = resolve_sealed_letter_lookup(
                    enc, commits, active_table,
                    geometry_modifiers=geo_mods, shot_inputs=shot_inputs, swn_cfg=pack.rules.swn,
                )

                # Advance the graph for next turn (fail loud on an unknown target).
                if sl_outcome.next_state and sl_outcome.next_state != current_state:
                    if sl_outcome.next_state not in cdef.interaction_tables:
                        raise ValueError(
                            f"dogfight cell transitions to unknown state "
                            f"{sl_outcome.next_state!r} (registry: {sorted(cdef.interaction_tables)})"
                        )
                    with dogfight_state_transition_span(
                        from_state=current_state or "", to_state=sl_outcome.next_state
                    ):
                        pass
                    enc.dogfight_state = sl_outcome.next_state
```

(This replaces the existing `sl_outcome = resolve_sealed_letter_lookup(...)` call at ~6095-6102 — quote that block first with `sed -n '6090,6125p'` and edit in place. Import `dogfight_state_transition_span`.)

- [ ] **Step 5: Run to confirm pass + no regression**

```bash
cd sidequest-server && uv run pytest tests/server/dispatch/test_dogfight_state_machine.py tests/server/dispatch/test_sealed_letter_dispatch_integration.py -v -n0
```
Expected: PASS. Single-table back-compat holds: a def with only `interaction_table` registers `{merge: it}`, `current_state` is merge, `active_table` is it, no transition fires.

- [ ] **Step 6: Commit**

```bash
cd sidequest-server && git add sidequest/server/narration_apply.py sidequest/telemetry/spans/dogfight.py tests/server/dispatch/test_dogfight_state_machine.py
git commit -m "feat(dogfight): state-machine apply — select per-state table + transition dogfight_state, OTEL (ADR-153)"
```

---

## Task 6: Content — author the full graph (states + transitions)

Author the four new state tables and wire transitions across all six. Rename the merge table for clarity and register all via the `interaction_tables` list. Cells carry geometry + `gun_solution` + `next_state` only (firewall).

**Files:**
- Modify: `sidequest-content/genre_packs/space_opera/rules.yaml` (dogfight def → `interaction_tables: [_from each]`)
- Modify: `sidequest-content/genre_packs/space_opera/dogfight/interactions_mvp.yaml` (merge; add `next_state` to cells)
- Modify: `sidequest-content/genre_packs/space_opera/dogfight/interactions_tail_chase.yaml` (add `next_state`)
- Create: `interactions_beam.yaml`, `interactions_overhead.yaml`, `interactions_scissors.yaml`, `interactions_overshoot.yaml`
- Modify: `sidequest-content/genre_packs/space_opera/dogfight/descriptor_schema.yaml` (promote beam/overhead from `future` to `mvp`; add scissors/overshoot)

- [ ] **Step 1: Branch content**

```bash
cd sidequest-content && git checkout develop && git pull && git checkout -b feat/158-40-dogfight-state-graph
```

- [ ] **Step 2: Wire the registry in the def**

In `genre_packs/space_opera/rules.yaml`, dogfight def — replace the single `interaction_table: {_from: dogfight/interactions_mvp.yaml}` with:

```yaml
    interaction_tables:
      - _from: dogfight/interactions_mvp.yaml          # starting_state: merge (entry)
      - _from: dogfight/interactions_tail_chase.yaml   # starting_state: tail_chase
      - _from: dogfight/interactions_beam.yaml
      - _from: dogfight/interactions_overhead.yaml
      - _from: dogfight/interactions_scissors.yaml
      - _from: dogfight/interactions_overshoot.yaml
```

(The first-listed table's `starting_state` is the entry state via Task 4's `next(iter(...))` — keep `interactions_mvp.yaml` (merge) first.)

- [ ] **Step 3: Add `next_state` transitions to the existing two tables**

In `interactions_mvp.yaml` and `interactions_tail_chase.yaml`, add a `next_state:` to each cell that should change the relative position (a clean tail entry → `tail_chase`; a head-on pass that opens → stays/`merge`; a mutual hard turn → `scissors`; a vertical reversal → `overhead`; an overshoot → `overshoot`). Cells where the geometry stays in the same state omit `next_state`. Example (merge `[straight, loop]` — Blue loops onto Red's six):

```yaml
  - pair: [straight, loop]
    name: "Blue reverses onto Red's six"
    next_state: tail_chase          # Blue is now the pursuer
    red_view: { target_bearing: "06", target_range: close, target_aspect: tail_on, closure: closing, gun_solution: false }
    blue_view: { target_bearing: "12", target_range: gun, target_aspect: tail_on, closure: closing, gun_solution: true }
    narration_hint: >-
      Blue pulls into a screaming vertical reversal and comes down on Red's
      exhaust. Tail chase — Blue has the gun.
```

- [ ] **Step 4: Author the four new state tables**

Create each of `interactions_beam.yaml`, `interactions_overhead.yaml`, `interactions_scissors.yaml`, `interactions_overshoot.yaml` with the same shape as `interactions_mvp.yaml`: `version`, `starting_state: <state>`, `maneuvers_consumed: [straight, bank, loop, kill_rotation]`, and a full 16-cell `cells:` grid (every `(red, blue)` pair). Each cell carries `red_view`/`blue_view` (geometry + `gun_solution`), `narration_hint`, and `next_state` where the position changes. Geometry only — no damage (firewall). Author the transitions so the graph is connected and returns toward `merge` via extend-and-return (the resolver handles the reset). Tag cells `[dull|exciting|lopsided|confusing|calibrated]` for the calibration pass (ADR-077 risk note).

(This is the bulk of the content work. Follow the merge/tail_chase authoring voice. The interaction-table validator requires all pairs unique and a non-empty cell list.)

- [ ] **Step 5: Promote the descriptor schema states**

In `dogfight/descriptor_schema.yaml`, under `starting_states`, change `beam` and `overhead` from `status: future` to `status: mvp` and add `scissors` + `overshoot` entries with their `initial_descriptor` blocks (mirror the merge/tail_chase shape).

- [ ] **Step 6: Validate the pack loads with the full registry**

```bash
cd /Users/slabgorb/Projects/oq-3/sidequest-server && SIDEQUEST_GENRE_PACKS=../sidequest-content/genre_packs uv run python -c "
from sidequest.genre.loader import load_genre_pack
d = next(c for c in load_genre_pack('space_opera').rules.confrontations if c.confrontation_type=='dogfight')
print('states', sorted(d.interaction_tables))
assert set(d.interaction_tables) == {'merge','tail_chase','beam','overhead','scissors','overshoot'}
# Every next_state referenced by any cell must have a table (no dead transitions):
targets = {c.next_state for t in d.interaction_tables.values() for c in t.cells if c.next_state}
missing = targets - set(d.interaction_tables)
assert not missing, f'cells transition to states with no table: {missing}'
print('OK — graph closed')
"
```
Expected: `OK — graph closed`.

- [ ] **Step 7: Commit (content)**

```bash
cd sidequest-content && git add genre_packs/space_opera/rules.yaml genre_packs/space_opera/dogfight/
git commit -m "feat(space_opera): full dogfight state graph — beam/overhead/scissors/overshoot + transitions (ADR-153)"
```

---

## Task 7: End-to-end wiring + graph-closure validator guard

Prove the graph moves across a real multi-turn duel, and guard graph-closure (no cell transitions to a state with no table) in the pack validator so a future authoring error fails loud.

**Files:**
- Test: `sidequest-server/tests/server/dispatch/test_dogfight_graph_e2e.py`
- Modify: `sidequest-server/sidequest/cli/validate.py` (graph-closure check) + its test

- [ ] **Step 1: Write the e2e test (live content)**

Create `tests/server/dispatch/test_dogfight_graph_e2e.py`: load the real space_opera pack, seat a dogfight, drive maneuver pairs that walk merge→tail_chase→(another state), asserting `enc.dogfight_state` follows the authored `next_state` each turn and the resolved cell each turn comes from the current state's table. Assert `dogfight.state_transition` spans fire in order.

- [ ] **Step 2: Add the graph-closure validator rule**

In `sidequest/cli/validate.py` confrontation loop, for any def with `interaction_tables`, assert every cell `next_state` has a registered table (mirror the loader-time check). Add a synthetic-pack unit test that a dangling `next_state` is rejected.

```python
        if cdef.interaction_tables:
            states = set(cdef.interaction_tables)
            for st, table in cdef.interaction_tables.items():
                for cell in table.cells:
                    if cell.next_state and cell.next_state not in states:
                        errors.append(
                            f"dogfight {cdef.confrontation_type!r} state {st!r}: cell "
                            f"{cell.pair} transitions to unknown state {cell.next_state!r}"
                        )
```

- [ ] **Step 3: Run e2e + validator + the live pack through validate, serially**

```bash
cd sidequest-server && uv run pytest tests/server/dispatch/test_dogfight_graph_e2e.py tests/cli/test_validate.py -k "graph or dogfight" -n0 -q
SIDEQUEST_GENRE_PACKS=../sidequest-content/genre_packs uv run python -m sidequest.cli.validate space_opera
```
Expected: tests PASS; live pack validates clean.

- [ ] **Step 4: Lint + commit**

```bash
cd sidequest-server && uv run ruff check sidequest/server/narration_apply.py sidequest/server/dispatch/sealed_letter.py sidequest/genre/loader.py sidequest/cli/validate.py tests/server/dispatch/test_dogfight_graph_e2e.py
git add tests/server/dispatch/test_dogfight_graph_e2e.py sidequest/cli/validate.py tests/cli/test_validate.py
git commit -m "test+validate(dogfight): e2e state-graph walk + graph-closure guard (ADR-153)"
```

---

## Self-Review

**Spec coverage (ADR-153 §3):** multiple per-state tables → Tasks 1-2 (model + loader). current-state tracking → Task 3. cell→next-state transitions → Tasks 1 (field) + 4 (resolver) + 5 (apply). extend-and-return as transition to merge → Task 4 Step 3. beam/overhead/scissors/overshoot content → Task 6. The hardcoded `_MERGE_STARTING_GEOMETRY` descriptor-schema TODO is addressed by Task 6 Step 5 (schema states promoted) — note the constant remains the extend-and-return reset target; if it must be schema-driven, that is a follow-up. Firewall held: cells carry geometry + gun_solution + next_state only.

**Placeholder scan:** Task 6 Step 4 ("author the four 16-cell tables") is real, bounded content work with a known shape (mirrors the two existing tables) — not a code placeholder. The "confirm helper/loader-entrypoint name" notes are bounded located reads. No "TODO/TBD" left in code steps.

**Type consistency:** `InteractionCell.next_state: str | None`, `ConfrontationDef.interaction_tables: dict[str, InteractionTable]`, `StructuredEncounter.dogfight_state: str | None`, `SealedLetterOutcome.next_state: str | None`, and `dogfight_state_transition_span(from_state, to_state)` are consistent across Tasks 1-7. The registry is keyed by each table's `starting_state` everywhere (loader, instantiation, apply, validator).
