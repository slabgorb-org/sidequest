# Spaghetti-Western Contest→Conflict Escalation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give spaghetti_western a Standoff that resolves as a Fate **Contest** and escalates *in place* to a Fate **Conflict** (gunfight) when someone draws, carrying the standoff's tactical edge as the Conflict's opening position — and correct the taxonomy so the Gunfight is a Conflict, not a Contest.

**Architecture:** The escalation is a single new pure-transition function, `escalate_contest_to_conflict`, that flips one live encounter from Contest to Conflict without re-seating it (encounter identity preserved). It is triggered by reusing the *existing* attack-in-Contest rejection point in `dispatch_fate_action`: an `attack` in a Contest that authors `escalates_to` calls the transition instead of raising. The standoff's situation aspects already live on `encounter.situation_aspects`, so "carrying the aspects" is simply *not clearing them*; the only minted state is a `Got the Drop` boost. A new `fate.contest.escalated` OTEL span is the GM-panel proof. Poker's "reset, not flip" needs **no engine work** — it is an ordinary end-encounter / seat-encounter scene change, guarded only by a negative test.

**Tech Stack:** Python 3 / FastAPI / pydantic v2 (`sidequest-server`); YAML genre pack (`sidequest-content`); pytest (`uv run pytest`, parallel via `-n auto`); OpenTelemetry spans via the project `Span.open` + `SPAN_ROUTES` registry.

## Global Constraints

- **HARD DEPENDENCY / EXECUTION BLOCKER:** This builds on the Fate Contest binding, which lives on branch `feat/fate-contest-binding` in **both** `sidequest-server` and `sidequest-content` and is **NOT yet merged to `develop`**. It provides `ContestState`, `run_fate_contest_exchange`, `run_fate_exchange`, the `encounter.contest` field, the contest-mode seeding, and the spaghetti_western Gunfight-as-Contest content. **Do not begin implementation until both `feat/fate-contest-binding` PRs are merged to `develop`.** Every file/line reference below is as it exists on `feat/fate-contest-binding`.
- **Branch targets (gitflow):** `sidequest-server` and `sidequest-content` both target `develop`. Feature branch `feat/{description}`; PRs target `develop`. (Per `.pennyfarthing/repos.yaml`.)
- **No Silent Fallbacks:** an escalation request on a non-contest / non-Fate encounter, or a Contest-attack with no `escalates_to`, fails loud (raises) — never silently no-ops.
- **No Stubbing / No half-wired features:** the escalation must be reachable from the real FATE_ACTION dispatch path, proven by a behavioral wiring test.
- **OTEL Observability Principle:** the escalation is a subsystem decision and MUST emit a span (`fate.contest.escalated`) so the GM panel can verify it fired and *what* carried. The narrator must not be able to claim "he got the drop" with no mechanical backing.
- **No Source-Text Wiring Tests:** wiring is proven by OTEL span assertions or fixture-driven behavior — never by grepping production source. (`sidequest-server/CLAUDE.md`.)
- **Reuse, don't reinvent:** ADR-116's Other-invariant (`_requires_opponent` already returns True for `contest`), the Conflict engine (`run_fate_exchange`), `situation_aspects` storage, the inline boost primitive (`Aspect(..., kind="boost", free_invokes=1)`), and the `fate.contest.*` span family are all reused as-is.

## Design Decisions (amendments to the 2026-06-17 spec)

Reconnaissance found two of the spec's mechanical assumptions incompatible with the real Fate dispatch path. Both were re-decided 2026-06-17 (Keith, option 1 on each). Log these as deviations from `docs/superpowers/specs/2026-06-17-spaghetti-western-contest-conflict-escalation-design.md`:

- **DEVIATION 1 — escalation trigger.** Spec §"Trigger wiring" said the `draw` *beat* with `escalates: true` fires escalation. That cannot work: Fate confrontations do not traverse the beat/`apply_beat` path (they route through `dispatch_fate_action`), and `BeatDef` is `model_config = {"extra": "forbid"}` (`sidequest/genre/models/rules.py:118`), so `escalates: true` would fail pack load. **Resolution:** the player's `draw` intent maps to the Fate `attack` action. In a Contest, `attack` is *already* rejected loud (`fate_conflict.py:779`). That rejection point becomes the escalation hook, gated on the confrontation's *existing* `escalates_to` field (`ConfrontationDef.escalates_to`, `rules.py:447` — the Standoff already authors `escalates_to: combat`). Content-driven, author-declared, no schema change, no new payload.
- **DEVIATION 2 — "got the drop → acts first."** Spec §mechanic-4 said the drop-getter "acts first in the Conflict's initiative." The Fate Conflict engine walks in Notice/Empathy skill order, **not** the 1d8+DEX `initiative` list (`encounter.py:276`, which is SWN/WN-only). **Resolution:** represent the drop purely as the carried `Got the Drop` **boost** (a single free invoke). The free invoke *is* the mechanical edge and is genuine Fate; no initiative reordering is invented.

---

## File Structure

**`sidequest-server` (targets `develop`):**

- Modify `sidequest/game/encounter.py` — add `escalates_to: str | None` field to `StructuredEncounter` (carries the contest's escalation target so `dispatch_fate_action` can read it without a cdef lookup).
- Modify `sidequest/server/dispatch/encounter_lifecycle.py` — stamp `enc.escalates_to = cdef.escalates_to` at contest seeding.
- Modify `sidequest/telemetry/spans/fate.py` — add `fate_contest_escalated_span(...)` emit fn + register `SPAN_ROUTES["fate.contest.escalated"]`.
- Modify `sidequest/server/dispatch/fate_contest.py` — add `escalate_contest_to_conflict(...)` (the one new mechanic).
- Modify `sidequest/server/dispatch/fate_conflict.py` — add `escalated: bool = False` to `FateDispatchResult`; rewire the attack-in-Contest branch to escalate when `encounter.escalates_to` is set.

**`sidequest-content` (targets `develop`):**

- Modify `genre_packs/spaghetti_western/rules.yaml` — Standoff gains `resolution_mode: contest`; Gunfight loses `resolution_mode: contest` (becomes a Conflict).

**Tests (`sidequest-server/tests/`, matching the existing fate test tree):**

- `tests/game/test_encounter_contest_escalates_to.py` (or extend `tests/game/test_encounter_contest.py`)
- `tests/telemetry/test_fate_contest_escalated_span.py`
- `tests/server/test_fate_contest_escalation.py` (engine + trigger)
- `tests/server/test_fate_contest_escalation_wiring.py` (end-to-end through the handler)
- `tests/genre/test_spaghetti_western_contest_taxonomy.py` (content validation)
- `tests/server/test_poker_violence_reset.py` (negative guard — nothing carries)

---

## Task 1: `escalates_to` on the encounter, stamped at Contest seeding

**Files:**
- Modify: `sidequest/game/encounter.py:292` (add field beside `contest`)
- Modify: `sidequest/server/dispatch/encounter_lifecycle.py:1598-1607` (stamp it in the contest branch)
- Test: `sidequest/tests/game/test_encounter_contest_escalates_to.py`

**Interfaces:**
- Produces: `StructuredEncounter.escalates_to: str | None` — the escalation target type, or `None`. Read by `dispatch_fate_action` (Task 4) and `escalate_contest_to_conflict` (Task 3).

- [ ] **Step 1: Write the failing test**

```python
# sidequest/tests/game/test_encounter_contest_escalates_to.py
"""A contest-mode encounter carries its escalation target so dispatch_fate_action
can decide whether an attack escalates (spec 2026-06-17 §2; DEVIATION 1)."""
from sidequest.game.encounter import StructuredEncounter


def test_structured_encounter_has_escalates_to_default_none():
    enc = StructuredEncounter(
        encounter_type="standoff",
        player_metric={"name": "tension", "current": 0, "threshold": 3},
        opponent_metric={"name": "tension", "current": 0, "threshold": 3},
    )
    assert enc.escalates_to is None


def test_structured_encounter_escalates_to_roundtrips():
    enc = StructuredEncounter(
        encounter_type="standoff",
        player_metric={"name": "tension", "current": 0, "threshold": 3},
        opponent_metric={"name": "tension", "current": 0, "threshold": 3},
        escalates_to="combat",
    )
    assert enc.escalates_to == "combat"
```

> NOTE: confirm the exact `EncounterMetric` construction the other `tests/game/test_encounter_contest.py` tests use and copy it verbatim — the metric field names (`current` vs `starting`) must match the real model.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/game/test_encounter_contest_escalates_to.py -v`
Expected: FAIL — `StructuredEncounter` has no field `escalates_to`; with `extra: forbid` the second test raises a `ValidationError`.

- [ ] **Step 3: Add the field**

In `sidequest/game/encounter.py`, immediately after the `contest` field (line 292) and before `situation_aspects`:

```python
    #: The confrontation this one escalates into (ConfrontationDef.escalates_to),
    #: stamped at Contest seeding. Read by dispatch_fate_action: an ``attack`` in a
    #: Contest with ``escalates_to`` set flips the encounter to a Conflict in place
    #: instead of raising (spec 2026-06-17; DEVIATION 1). None for encounters that
    #: do not escalate.
    escalates_to: str | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/game/test_encounter_contest_escalates_to.py -v`
Expected: PASS.

- [ ] **Step 5: Stamp it at seeding**

In `sidequest/server/dispatch/encounter_lifecycle.py`, inside the existing contest-seeding block (lines 1598-1607), after `enc.contest = ContestState(target=target)` (line 1603), add:

```python
            enc.escalates_to = cdef.escalates_to
```

- [ ] **Step 6: Write the seeding wiring test**

Add to the same test file a test that instantiates a contest-mode encounter through the real lifecycle and asserts `escalates_to` is stamped. Reuse the instantiation fixture the existing `feat/fate-contest-binding` contest seeding test uses (find it in `tests/server/` — the test that asserts `enc.contest` is set after a `resolution_mode: contest` cdef seats). Add an assertion alongside it:

```python
def test_contest_seeding_stamps_escalates_to(<existing fixture params>):
    enc = <instantiate a Standoff cdef with resolution_mode=contest, escalates_to="combat">
    assert enc.contest is not None
    assert enc.escalates_to == "combat"
```

> If the existing seeding test already has a fixture builder for a contest cdef, extend that test module rather than rebuilding the fixture. The contest cdef must set `escalates_to="combat"` and `resolution_mode=ResolutionMode.contest`.

- [ ] **Step 7: Run and verify, then commit**

Run: `cd sidequest-server && uv run pytest tests/game/test_encounter_contest_escalates_to.py tests/server/ -k "contest" -v`
Expected: PASS.

```bash
git add sidequest/game/encounter.py sidequest/server/dispatch/encounter_lifecycle.py tests/game/test_encounter_contest_escalates_to.py
git commit -m "feat(fate): carry escalates_to on the encounter for Contest escalation"
```

---

## Task 2: `fate.contest.escalated` OTEL span

**Files:**
- Modify: `sidequest/telemetry/spans/fate.py` — emit fn after `fate_contest_resolved_span` (line 747); `SPAN_ROUTES` registration after the `fate.contest.resolved` route (line 426)
- Test: `sidequest/tests/telemetry/test_fate_contest_escalated_span.py`

**Interfaces:**
- Produces: `fate_contest_escalated_span(*, encounter_type: str, initiator: str, carried_aspects: list[str], got_drop: str, _tracer: trace.Tracer | None = None, **attrs) -> None` — called by `escalate_contest_to_conflict` (Task 3).

- [ ] **Step 1: Write the failing test**

Model it on the existing `tests/telemetry/test_fate_action_classified_span.py` (same span-capture harness). The test must (a) call the emit fn and assert a span named `fate.contest.escalated` fired with the right attributes, and (b) assert `SPAN_ROUTES` contains the key and its `extract` maps the attributes to a watcher payload.

```python
# sidequest/tests/telemetry/test_fate_contest_escalated_span.py
"""fate.contest.escalated — the GM-panel proof the standoff flipped to a gunfight
and WHAT carried (spec 2026-06-17; OTEL lie-detector)."""
from sidequest.telemetry.spans.fate import fate_contest_escalated_span
from sidequest.telemetry.spans.fate import SPAN_ROUTES
from <span capture harness used by test_fate_action_classified_span> import <capture>


def test_escalated_span_emits_with_carried_set(<capture fixture>):
    fate_contest_escalated_span(
        encounter_type="standoff",
        initiator="The Stranger",
        carried_aspects=["Flinched First", "Sun at His Back"],
        got_drop="The Stranger",
    )
    span = <captured span named "fate.contest.escalated">
    assert span.attributes["from_mode"] == "contest"
    assert span.attributes["to_mode"] == "conflict"
    assert span.attributes["encounter_type"] == "standoff"
    assert span.attributes["initiator"] == "The Stranger"
    assert span.attributes["got_drop"] == "The Stranger"
    assert "Flinched First" in span.attributes["carried_aspects"]


def test_escalated_span_route_registered():
    route = SPAN_ROUTES["fate.contest.escalated"]
    assert route.event_type == "state_transition"
    assert route.component == "fate"
    payload = route.extract(type("S", (), {"attributes": {
        "from_mode": "contest", "to_mode": "conflict", "encounter_type": "standoff",
        "initiator": "The Stranger", "got_drop": "The Stranger",
        "carried_aspects": ["Flinched First"],
    }})())
    assert payload["field"] == "contest_escalated"
    assert payload["initiator"] == "The Stranger"
```

> Copy the exact span-capture fixture/import from `tests/telemetry/test_fate_action_classified_span.py` — do not invent a harness.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/telemetry/test_fate_contest_escalated_span.py -v`
Expected: FAIL — `fate_contest_escalated_span` undefined; `SPAN_ROUTES["fate.contest.escalated"]` KeyError.

- [ ] **Step 3: Add the emit fn**

In `sidequest/telemetry/spans/fate.py`, after `fate_contest_resolved_span` (ends line 747):

```python
def fate_contest_escalated_span(
    *,
    encounter_type: str,
    initiator: str,
    carried_aspects: list[str],
    got_drop: str,
    _tracer: trace.Tracer | None = None,
    **attrs: Any,
) -> None:
    """Emit ``fate.contest.escalated`` — a Standoff Contest flipped in place to a
    Gunfight Conflict (spec 2026-06-17; DEVIATION 1). The GM-panel proof the
    escalation fired and WHAT carried: the situation aspects that rode over and who
    got the drop. Without this a narrator could claim 'he got the drop' with no
    mechanical backing (the Illusionism the OTEL lie-detector exists to catch)."""
    attributes: dict[str, Any] = {
        "field": "contest_escalated",
        "from_mode": "contest",
        "to_mode": "conflict",
        "encounter_type": encounter_type,
        "initiator": initiator,
        "carried_aspects": list(carried_aspects),
        "got_drop": got_drop,
        **attrs,
    }
    with Span.open("fate.contest.escalated", attributes, tracer_override=_tracer):
        pass
```

- [ ] **Step 4: Register the route**

In `sidequest/telemetry/spans/fate.py`, after the `SPAN_ROUTES["fate.contest.resolved"]` block (ends line 426):

```python
SPAN_ROUTES["fate.contest.escalated"] = SpanRoute(
    event_type="state_transition",
    component="fate",
    extract=lambda span: {
        "field": "contest_escalated",
        "encounter_type": (span.attributes or {}).get("encounter_type", ""),
        "initiator": (span.attributes or {}).get("initiator", ""),
        "got_drop": (span.attributes or {}).get("got_drop", ""),
        "carried_aspects": (span.attributes or {}).get("carried_aspects", []),
    },
)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/telemetry/test_fate_contest_escalated_span.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add sidequest/telemetry/spans/fate.py tests/telemetry/test_fate_contest_escalated_span.py
git commit -m "feat(fate): add fate.contest.escalated span + watcher route"
```

---

## Task 3: `escalate_contest_to_conflict` — the in-place transition

**Files:**
- Modify: `sidequest/server/dispatch/fate_contest.py` — add the function (after `run_fate_contest_exchange`, which ends line 233)
- Test: `sidequest/tests/server/test_fate_contest_escalation.py`

**Interfaces:**
- Consumes: `StructuredEncounter.escalates_to` / `.contest` / `.situation_aspects` (Task 1); `Aspect` (`sidequest/game/fate_sheet.py:38`); `fate_contest_escalated_span` (Task 2).
- Produces: `escalate_contest_to_conflict(*, encounter: StructuredEncounter, snapshot: GameSnapshot, initiator: str, _tracer: trace.Tracer | None = None) -> None` — mutates `encounter` in place: clears the contest, relabels the encounter as the gunfight, mints the drop boost, leaves carried aspects, emits the span. Called by `dispatch_fate_action` (Task 4).

- [ ] **Step 1: Write the failing test**

```python
# sidequest/tests/server/test_fate_contest_escalation.py
"""The in-place Contest->Conflict flip (spec 2026-06-17 §"The new mechanic")."""
from sidequest.game.encounter import ContestState, StructuredEncounter
from sidequest.game.fate_sheet import Aspect
from sidequest.server.dispatch.fate_contest import escalate_contest_to_conflict


def _standoff_contest_encounter():
    enc = StructuredEncounter(
        encounter_type="standoff",
        player_metric={"name": "tension", "current": 0, "threshold": 3},
        opponent_metric={"name": "tension", "current": 0, "threshold": 3},
        escalates_to="combat",
    )
    enc.contest = ContestState(target=3, player_victories=1, opponent_victories=0)
    # Aspects placed DURING the standoff (flinch + size_up create_advantage):
    enc.situation_aspects = [
        Aspect(text="Flinched First", kind="situation", free_invokes=1),
        Aspect(text="Sun at His Back", kind="situation", free_invokes=1),
    ]
    return enc


def test_escalation_clears_contest_and_relabels():
    enc = _standoff_contest_encounter()
    escalate_contest_to_conflict(encounter=enc, snapshot=<minimal snapshot fixture>, initiator="The Stranger")
    assert enc.contest is None
    assert enc.encounter_type == "combat"  # relabeled to the gunfight; same object


def test_escalation_carries_aspects_and_mints_drop_boost():
    enc = _standoff_contest_encounter()
    escalate_contest_to_conflict(encounter=enc, snapshot=<minimal snapshot fixture>, initiator="The Stranger")
    texts = [a.text for a in enc.situation_aspects]
    assert "Flinched First" in texts          # the flinch aspect rode over
    assert "Sun at His Back" in texts          # generic situation aspect rode over
    drop = [a for a in enc.situation_aspects if a.kind == "boost" and "Got the Drop" in a.text]
    assert len(drop) == 1
    assert drop[0].free_invokes == 1           # single free invoke (DEVIATION 2: boost IS the drop)
    assert "The Stranger" in drop[0].text
    # free invokes on the carried aspects are intact
    assert all(a.free_invokes == 1 for a in enc.situation_aspects if a.kind == "situation")


def test_escalation_raises_loud_on_non_contest():
    enc = _standoff_contest_encounter()
    enc.contest = None
    import pytest
    with pytest.raises(Exception):  # No Silent Fallbacks
        escalate_contest_to_conflict(encounter=enc, snapshot=<minimal snapshot fixture>, initiator="The Stranger")
```

> Use the same minimal `GameSnapshot` fixture the other `tests/server/` fate-dispatch tests use. If `escalate_contest_to_conflict` ends up not needing `snapshot` (it does no roll and no presence stamp), drop the param here AND in the signature — keep the test and the signature consistent.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/server/test_fate_contest_escalation.py -v`
Expected: FAIL — `escalate_contest_to_conflict` is undefined.

- [ ] **Step 3: Implement the transition**

In `sidequest/server/dispatch/fate_contest.py`, after `run_fate_contest_exchange` (ends line 233). Import `Aspect` and the new span at top of file (match the existing import style); use a lazy import only where a cycle exists.

```python
def escalate_contest_to_conflict(
    *,
    encounter: StructuredEncounter,
    snapshot: GameSnapshot,
    initiator: str,
    _tracer: trace.Tracer | None = None,
) -> None:
    """Flip a Standoff Contest to a Gunfight Conflict in place (spec 2026-06-17).

    The ``draw`` (an ``attack`` action; DEVIATION 1) interrupts the Contest: it does
    NOT have to win it first. The SAME encounter object continues — no tear-down,
    no re-seat (ADR-116's seated Other rides along). Clearing ``contest`` flips
    ``dispatch_fate_action`` to the Conflict engine on the next exchange. Stress is
    fresh (FateSheets untouched — nobody has been shot yet). The standoff's
    ``situation_aspects`` are simply NOT cleared, so the flinch aspect + situation
    aspects carry with their free invokes intact; the drop becomes a ``Got the
    Drop`` boost (DEVIATION 2 — the free invoke IS the edge; no initiative)."""
    if encounter.contest is None:
        raise FateConflictError(
            "escalate_contest_to_conflict called on a non-Contest encounter "
            "(No Silent Fallbacks — a draw-escalation requires an active Contest)"
        )
    if encounter.escalates_to is None:
        raise FateConflictError(
            "escalate_contest_to_conflict called on a Contest with no escalates_to "
            "(config/author bug — this Contest has no violence path)"
        )
    carried = [a.text for a in encounter.situation_aspects]
    # The Contest is over — superseded, not won.
    encounter.contest = None
    # Relabel as the gunfight; same object, identity preserved (panel does not re-seat).
    target_type = encounter.escalates_to
    encounter.encounter_type = target_type
    # The drop: a boost on the initiator (single free invoke). Mirrors the inline
    # boost primitive used by the contest/conflict tie path (fate_contest.py:132).
    encounter.situation_aspects.append(
        Aspect(text=f"Got the Drop ({initiator})", kind="boost", free_invokes=1)
    )
    encounter.narrator_hints.append(
        f"The standoff breaks — iron clears leather. {initiator} has the drop."
    )
    fate_contest_escalated_span(
        encounter_type=target_type,
        initiator=initiator,
        carried_aspects=carried,
        got_drop=initiator,
        _tracer=_tracer,
    )
```

> `FateConflictError` is defined in `fate_conflict.py` and already imported into `fate_contest.py` via its module-level import block (the file already imports from `fate_conflict`). If it is not yet imported there, add it to that existing import — do not create a second error type.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/server/test_fate_contest_escalation.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add sidequest/server/dispatch/fate_contest.py tests/server/test_fate_contest_escalation.py
git commit -m "feat(fate): escalate_contest_to_conflict — in-place Standoff->Gunfight flip"
```

---

## Task 4: Wire the trigger into `dispatch_fate_action`

**Files:**
- Modify: `sidequest/server/dispatch/fate_conflict.py` — `FateDispatchResult` (line 723); the attack-in-Contest branch (lines 778-783)
- Test: extend `sidequest/tests/server/test_fate_contest_escalation.py`

**Interfaces:**
- Consumes: `escalate_contest_to_conflict` (Task 3); `encounter.escalates_to` (Task 1).
- Produces: `FateDispatchResult.escalated: bool` (defaults `False`); an `attack` in an escalating Contest now returns `FateDispatchResult(commitment_pending=False, exchange=None, escalated=True)` instead of raising.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/server/test_fate_contest_escalation.py
import random
import pytest
from sidequest.server.dispatch.fate_conflict import (
    FateConflictError,
    FateDispatchResult,
    dispatch_fate_action,
)


def test_attack_in_escalating_contest_flips_instead_of_raising(<fate fixtures>):
    enc = _standoff_contest_encounter()  # escalates_to="combat", contest set
    # seat player + opponent actors and FateSheets via the shared fate fixture
    result = dispatch_fate_action(
        payload=<FateActionPayload action="attack", skill="Shoot", ...>,
        actor_name="The Stranger",
        encounter=enc,
        ruleset=<FateRulesetModule>,
        snapshot=<snapshot>,
        rng=random.Random(0),
    )
    assert isinstance(result, FateDispatchResult)
    assert result.escalated is True
    assert result.commitment_pending is False
    assert result.exchange is None
    assert enc.contest is None  # flipped


def test_attack_in_non_escalating_contest_still_raises(<fate fixtures>):
    enc = _standoff_contest_encounter()
    enc.escalates_to = None  # a pure nerves Contest with no violence path
    with pytest.raises(FateConflictError):
        dispatch_fate_action(
            payload=<FateActionPayload action="attack", ...>,
            actor_name="The Stranger", encounter=enc,
            ruleset=<FateRulesetModule>, snapshot=<snapshot>, rng=random.Random(0),
        )


def test_attack_after_escalation_routes_to_conflict(<fate fixtures>):
    enc = _standoff_contest_encounter()
    dispatch_fate_action(payload=<attack>, actor_name="The Stranger", encounter=enc,
                         ruleset=<fate>, snapshot=<snapshot>, rng=random.Random(0))
    # contest now None; a follow-up attack must seal/route to the Conflict engine,
    # not raise and not re-escalate.
    result2 = dispatch_fate_action(payload=<attack>, actor_name="The Stranger",
                                   encounter=enc, ruleset=<fate>, snapshot=<snapshot>,
                                   rng=random.Random(0))
    assert result2.escalated is False  # already a Conflict
```

> Reuse the FATE_ACTION fixtures from `tests/server/test_fate_action_handler_wiring.py` / `tests/game/test_fate_opponent.py` for seating actors with Fate sheets and building a `FateActionPayload`. Match their construction exactly.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/server/test_fate_contest_escalation.py -v`
Expected: FAIL — `FateDispatchResult` has no `escalated`; the attack branch still raises for an escalating Contest.

- [ ] **Step 3: Add the `escalated` flag**

In `sidequest/server/dispatch/fate_conflict.py`, in `FateDispatchResult` (after `fate_point_delta`, ~line 740):

```python
    #: True when this action flipped a Standoff Contest to a Gunfight Conflict in
    #: place (spec 2026-06-17; DEVIATION 1) — lets the player surface re-render as a
    #: gunfight. The action neither sealed nor resolved an exchange: the scene
    #: changed mode. False on every ordinary action.
    escalated: bool = False
```

- [ ] **Step 4: Rewire the attack-in-Contest branch**

Replace the existing branch (lines 778-783):

```python
    # spec 2026-06-17 §2: a Contest has no harm — attacks are a Conflict action.
    if encounter.contest is not None and action == "attack":
        raise FateConflictError(
            "'attack' is a Conflict action; this encounter is a Contest (no stress, "
            "no consequences) — use 'overcome' (spec 2026-06-17 §2)"
        )
```

with:

```python
    # spec 2026-06-17 §2 + escalation (DEVIATION 1): a Contest has no harm. An
    # ``attack`` (the player's ``draw``) in a Contest that AUTHORS escalates_to is
    # the in-place flip to the Gunfight Conflict — not an error. A Contest with no
    # escalates_to (a pure nerves contest) still rejects the attack loud.
    if encounter.contest is not None and action == "attack":
        if encounter.escalates_to is not None:
            # Lazy import breaks the fate_conflict <-> fate_contest cycle (mirrors
            # the run_fate_contest_exchange import below).
            from sidequest.server.dispatch.fate_contest import (
                escalate_contest_to_conflict,
            )

            escalate_contest_to_conflict(
                encounter=encounter,
                snapshot=snapshot,
                initiator=actor_name,
                _tracer=_tracer,
            )
            return FateDispatchResult(
                commitment_pending=False, exchange=None, escalated=True
            )
        raise FateConflictError(
            "'attack' is a Conflict action; this encounter is a Contest (no stress, "
            "no consequences) — use 'overcome' (spec 2026-06-17 §2)"
        )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/server/test_fate_contest_escalation.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add sidequest/server/dispatch/fate_conflict.py tests/server/test_fate_contest_escalation.py
git commit -m "feat(fate): draw (attack) escalates an escalating Contest to a Conflict"
```

---

## Task 5: End-to-end wiring test through the real FATE_ACTION handler

**Files:**
- Test only: `sidequest/tests/server/test_fate_contest_escalation_wiring.py`

**Interfaces:**
- Consumes: the real handler at `sidequest/handlers/fate_action.py:112` (or the bank subsystem at `sidequest/agents/subsystems/fate_action.py:102`) — whichever is the production entry the other wiring tests drive.

This task satisfies "Every Test Suite Needs a Wiring Test" and "No Source-Text Wiring Tests": prove the escalation is reachable from the production dispatch path via an OTEL span assertion, not a grep.

- [ ] **Step 1: Write the failing/▸behavioral test**

```python
# sidequest/tests/server/test_fate_contest_escalation_wiring.py
"""Wiring: a draw (attack) on a seated Standoff Contest reaches escalation through
the REAL FATE_ACTION handler, proven by the fate.contest.escalated span (not a
source grep — sidequest-server/CLAUDE.md)."""


def test_escalation_reachable_from_real_handler(<handler fixtures>, <span capture>):
    # Build a session/snapshot with a seated Standoff Contest (resolution_mode
    # contest, escalates_to combat) — reuse the handler harness from
    # tests/server/test_fate_action_handler_wiring.py.
    <drive a FATE_ACTION attack ("I draw!") through the real handler>
    span = <captured span named "fate.contest.escalated">
    assert span is not None
    assert span.attributes["initiator"] == <the acting player>
    assert <the snapshot's encounter>.contest is None
```

> Mirror `tests/server/test_fate_action_handler_wiring.py` for how it constructs the session, seats actors, and invokes the handler. Use the project's span-capture harness (same as Task 2).

- [ ] **Step 2: Run test**

Run: `cd sidequest-server && uv run pytest tests/server/test_fate_contest_escalation_wiring.py -v`
Expected: PASS once Tasks 1-4 are in (the handler already routes FATE_ACTION → `dispatch_fate_action`; this test confirms it end-to-end). If it FAILS, the handler path is not threading `encounter` correctly — fix the wiring, do not weaken the test.

- [ ] **Step 3: Commit**

```bash
git add tests/server/test_fate_contest_escalation_wiring.py
git commit -m "test(fate): wiring — draw escalates through the real FATE_ACTION handler"
```

---

## Task 6: Content — Standoff becomes a Contest, Gunfight becomes a Conflict

**Files:**
- Modify (in `sidequest-content`): `genre_packs/spaghetti_western/rules.yaml` — Standoff def (~lines 196-245); Gunfight def (~lines 359-413)
- Test (in `sidequest-server`): `sidequest/tests/genre/test_spaghetti_western_contest_taxonomy.py`

> Cross-repo: the YAML change lands in `sidequest-content` (branch + PR to its `develop`); the validation test lands in `sidequest-server` and loads the content pack. Both are part of this work.

**Interfaces:**
- Consumes: `ResolutionMode.contest`, the Fate guardrail validator `_fate_packs_have_no_opposed_check` (`sidequest/genre/models/rules.py:1422`).

- [ ] **Step 1: Write the failing validation test**

```python
# sidequest/tests/genre/test_spaghetti_western_contest_taxonomy.py
"""spaghetti_western taxonomy (spec 2026-06-17): Standoff=Contest (escalates),
Gunfight=Conflict, Poker untouched. Model it on tests/genre/test_fate_no_opposed_check.py."""
from sidequest.genre.loader import load_genre_pack
from sidequest.genre.models.rules import ResolutionMode
from <test genre path helper> import genre_pack_path  # tests/_helpers/genre_paths.py


def _cdef(pack, ctype):
    return next(c for c in pack.rules.confrontations if c.confrontation_type == ctype)


def test_standoff_is_a_contest_that_escalates():
    pack = load_genre_pack(genre_pack_path("spaghetti_western"))
    standoff = _cdef(pack, "standoff")
    assert standoff.resolution_mode == ResolutionMode.contest
    assert standoff.escalates_to == "combat"


def test_gunfight_is_a_conflict_not_a_contest():
    pack = load_genre_pack(genre_pack_path("spaghetti_western"))
    gunfight = _cdef(pack, "combat")
    assert gunfight.resolution_mode != ResolutionMode.contest  # routes to the Conflict engine


def test_poker_is_unchanged_table_resolution():
    pack = load_genre_pack(genre_pack_path("spaghetti_western"))
    poker = _cdef(pack, "poker")
    assert poker.resolution_mode == ResolutionMode.table_resolution


def test_pack_loads_without_validator_error():
    # The Fate guardrail (_fate_packs_have_no_opposed_check) must still pass.
    load_genre_pack(genre_pack_path("spaghetti_western"))  # raises on offense
```

> Find the exact genre-path helper in `tests/_helpers/genre_paths.py` and the confrontation-type accessor used by `tests/genre/test_fate_no_opposed_check.py`; copy them verbatim.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/genre/test_spaghetti_western_contest_taxonomy.py -v`
Expected: FAIL — on `feat/fate-contest-binding`, the Standoff is still dial/`beat_selection` (no `resolution_mode: contest`) and the Gunfight is `resolution_mode: contest`.

- [ ] **Step 3: Edit the Standoff def**

In `sidequest-content/genre_packs/spaghetti_western/rules.yaml`, the `standoff` confrontation. Add `resolution_mode: contest` (sibling to `category: pre_combat`); confirm `escalates_to: combat` is present (it is). Set the metric thresholds to a short nerves contest (first-to-3):

```yaml
  - type: standoff
    label: "Standoff"
    intent_verbs: [draw, stare, threaten, intimidate, square, confront]
    on_intent_mismatch: reprompt
    category: pre_combat
    resolution_mode: contest          # spec 2026-06-17: Standoff IS a Fate Contest
    player_metric:
      name: tension
      starting: 0
      threshold: 3                    # first-to-3 victories (was the 0->10 dial)
    opponent_metric:
      name: tension
      starting: 0
      threshold: 3
    # beats size_up / bluff / flinch map to Fate overcome / create_advantage; the
    # `draw` intent maps to the Fate `attack` action, which escalates this Contest
    # in place to the Gunfight Conflict (escalates_to: combat).
    beats:
      # ... existing size_up / bluff / flinch / draw beats unchanged ...
    escalates_to: combat
    mood: standoff
```

> Keep the existing `beats`, `secondary_stats`, and `intent_verbs` as-is — only `resolution_mode` and the two `threshold` values change. Do NOT add an `escalates: true` flag to any beat (BeatDef forbids it; the escalation is trigger-driven via the attack action — DEVIATION 1).

- [ ] **Step 4: Edit the Gunfight def**

In the same file, the `combat` (Gunfight) confrontation: **remove** the `resolution_mode: contest` line and revert the contest-era comment, so it resolves through the Fate **Conflict** engine (`run_fate_exchange` — stress/consequences). Leave `win_condition`/metrics as the Conflict path expects (the Conflict engine resolves taken-out via FateSheets; metrics are inert for Fate). Concretely: delete the `resolution_mode: contest` line that the contest-binding branch added (~line 372), and update the explanatory comment to state the Gunfight is a Conflict, not a Contest.

```yaml
  - type: combat
    label: Gunfight
    intent_verbs: [strike, attack, fight, kill, slay, swing, shoot, hit, stab]
    on_intent_mismatch: reprompt
    category: combat
    # spec 2026-06-17: a Gunfight INFLICTS HARM — it is a Fate Conflict (stress,
    # consequences, taken-out), NOT a Contest. No resolution_mode: contest here;
    # the Fate path routes a combat encounter with contest=None to run_fate_exchange.
    # ... beats (draw / fan_hammer / duck / walk_away) unchanged ...
    mood: combat
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/genre/test_spaghetti_western_contest_taxonomy.py -v`
Expected: PASS (server reads the edited content pack from the shared `sidequest-content` working copy).

- [ ] **Step 6: Commit (both repos)**

```bash
# in sidequest-content
git -C ../sidequest-content add genre_packs/spaghetti_western/rules.yaml
git -C ../sidequest-content commit -m "feat(spaghetti_western): Standoff is a Contest that escalates; Gunfight is a Conflict"
# in sidequest-server
git add tests/genre/test_spaghetti_western_contest_taxonomy.py
git commit -m "test(spaghetti_western): assert Standoff=Contest(escalates), Gunfight=Conflict, Poker untouched"
```

---

## Task 7: Negative guard — Poker→violence resets, nothing carries

**Files:**
- Test only: `sidequest/tests/server/test_poker_violence_reset.py`

The spec is explicit that Poker's "reset, not flip" needs **no engine work** — a poker scene turning violent is an ordinary end-encounter-A / seat-encounter-B scene change via the existing seating path. This task adds the negative guard the spec's Testing section requires: nothing from the poker table leaks into the seated Gunfight, and **no** `fate.contest.escalated` span fires (it is a reset, not a flip).

- [ ] **Step 1: Write the test**

```python
# sidequest/tests/server/test_poker_violence_reset.py
"""Poker -> violence is a RESET, not a flip (spec 2026-06-17). The poker table
encounter ends and a fresh Gunfight Conflict seats; NOTHING carries (no hand
strength, no table aspects) and NO fate.contest.escalated span fires."""
from sidequest.server.dispatch.encounter_lifecycle import reap_resolved_encounter_husk


def test_poker_to_gunfight_carries_nothing(<poker + snapshot fixtures>, <span capture>):
    # 1. Seat a poker table encounter (resolution_mode table_resolution) with a
    #    real table_state (cards, strengths) — reuse tests/server/test_table_resolution_wiring.py.
    <seat poker, deal a hand, stack a cheat>
    # 2. Violence breaks out: end the poker encounter and seat a fresh Gunfight.
    reap_resolved_encounter_husk(snapshot)
    <seat a combat (Gunfight) Conflict encounter via the normal instantiate path>
    gunfight = snapshot.encounter
    # 3. Nothing carried:
    assert gunfight.table_state is None
    assert gunfight.situation_aspects == []        # no table aspects rode over
    assert gunfight.contest is None                # it's a Conflict
    # 4. It was a reset, NOT an escalation:
    assert <no captured span named "fate.contest.escalated">
```

> Reuse the poker seating fixture from `tests/server/test_table_resolution_wiring.py` and the combat-seating path the WN/Fate conflict tests use. This test drives the existing scene-change path — it does not require any new production code.

- [ ] **Step 2: Run test**

Run: `cd sidequest-server && uv run pytest tests/server/test_poker_violence_reset.py -v`
Expected: PASS with no production changes. If `situation_aspects` or `table_state` leak across the husk reap, that is a real reset-cleanliness bug — fix it in the seating/reap path, do not weaken the assertion.

- [ ] **Step 3: Commit**

```bash
git add tests/server/test_poker_violence_reset.py
git commit -m "test(spaghetti_western): poker->violence resets clean (no carry, no escalated span)"
```

---

## Final verification

- [ ] **Run the full fate + genre suites:**

Run: `cd sidequest-server && uv run pytest tests/server/ tests/game/ tests/telemetry/ tests/genre/ -k "fate or contest or escalat or spaghetti or poker" -v`
Expected: all PASS.

- [ ] **Lint + type check:**

Run: `cd sidequest-server && uv run ruff check . && uv run pyright`
Expected: clean.

- [ ] **Full server gate:**

Run: from orchestrator root, `just server-check`
Expected: lint + full test suite PASS.

---

## Self-Review (architect, pre-handoff)

**Spec coverage** (against `docs/superpowers/specs/2026-06-17-spaghetti-western-contest-conflict-escalation-design.md`):
- Taxonomy (Standoff=Contest, Gunfight=Conflict, Poker untouched) → Task 6.
- New mechanic `escalate_contest_to_conflict` (clear contest, bring conflict online same encounter, preserve participants, carry edge, emit span) → Tasks 3 + 4. Carry-the-edge = situation_aspects not cleared (flinch/size-up aspects) + minted Got-the-Drop boost.
- `fate.contest.escalated` span with `{from, to, encounter_type, initiator, carried_aspects, got_drop}` → Task 2.
- Trigger author-declared/content-driven → reuses `escalates_to` (DEVIATION 1; Tasks 1 + 4); the spec's `escalates: true`-on-beat mechanism is rejected as un-authorable (BeatDef `extra: forbid`) and beat-path-incompatible.
- "Acts first" → boost-only (DEVIATION 2; Task 3); the spec's "initiative" is rejected (Fate has no d8 initiative).
- Error/invariants (escalate only from a contest under Fate, Other survives, deterministic carry, poker carries nothing) → Tasks 3 (loud raises) + 7 (negative guard). The Other rides along automatically (same encounter; `_requires_opponent` already seated it).
- Content changes (Standoff `resolution_mode: contest` + thresholds; Gunfight remove contest; Poker unchanged) → Task 6.
- Wiring test (escalation reachable from real beat/dispatch path, not a grep) → Task 5.

**Placeholder scan:** Test bodies contain `<...>` markers ONLY for fixtures whose exact construction must be copied verbatim from a named existing test (e.g. the span-capture harness, the FATE_ACTION payload fixture) — each is annotated with the source file. Production code blocks are complete and copy-paste ready. This is deliberate: inventing a fixture shape that diverges from the existing harness would be the worse failure.

**Type consistency:** `escalate_contest_to_conflict(*, encounter, snapshot, initiator, _tracer)` is defined identically in Task 3 (impl) and called identically in Task 4. `FateDispatchResult.escalated: bool = False` defined in Task 4 matches its assertions. `fate_contest_escalated_span(*, encounter_type, initiator, carried_aspects, got_drop, _tracer)` matches between Task 2 (def), Task 3 (call), and Task 2's tests. `StructuredEncounter.escalates_to: str | None` matches Task 1 (def), Task 3/4 (read), Task 6 (asserted from cdef).

**Open risk to confirm during execution:** whether `escalate_contest_to_conflict` genuinely needs `snapshot` (it does no roll and no presence stamp). If review finds it unused, drop the param from both the signature and the Task 3/4 call sites in the same commit — keep them consistent.
