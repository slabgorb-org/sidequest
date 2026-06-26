# Dogfight Rebuild — Plan 3: Opponent Brain Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the dogfight NPC ace's per-turn maneuver **motivated** (driven by its disposition/goal), **gated** (only legal, energy-affordable maneuvers), and **never fatal** (a deterministic disposition-derived fallback commits a legal maneuver instead of raising when the narrator omits the opponent's choice) — implementing ADR-153 §4.

**Architecture:** The narrator already picks the opponent's maneuver (it emits a `beat_selection` for every actor; the sealed-letter resolver maps each to a role). This plan keeps the narrator as the *chooser* but (1) surfaces the opponent ace's stance pre-narrator so the choice is goal-driven, (2) validates/clamps the committed maneuver to the legal+affordable set at resolution time, and (3) substitutes a deterministic disposition-derived maneuver when the narrator's blue commit is missing or illegal — instead of the current `ValueError`. The selection logic is a pure, unit-testable function; the wiring lives at the sealed-letter seam. Resolution stays SWN (firewall, ADR-153 §2): the brain only picks a *maneuver*, never geometry or damage.

**Tech Stack:** Python 3.12 / pydantic v2 / FastAPI (sidequest-server), YAML genre packs (sidequest-content), pytest + pytest-xdist (`-n0` for OTEL-span tests), OpenTelemetry spans.

## Global Constraints

- **Depends on Plan 1 (firewall) being merged** — the dogfight def is `hp_depletion`, no native dial.
- **Firewall (ADR-153 §2):** the brain picks a maneuver id only. It never composes geometry (the cross-product table does) and never resolves damage (SWN does).
- **No silent fallbacks / no stubs** (CLAUDE.md): a substituted or fallback maneuver is *loud and observable* (OTEL span carries `source`), never a silent default.
- **Resume-safe randomness** (ADR-128): no `Math.random`/`Date.now`; any tie-break is seeded from the encounter turn so a replay is identical.
- **Bind the Ruleset** (SOUL.md / ADR-143): the brain is a *positioning* decision; it adds no resolution math.
- **OTEL is the lie detector:** every committed opponent maneuver emits a span with its `source` (narrator | fallback | substituted) and the motivating attitude.
- **Branching:** sidequest-server targets `develop`; branch `feat/158-39-dogfight-opponent-brain`. Live motivation signal = `Npc.disposition.attitude()` (`sidequest/game/disposition.py`); pilot tiers (`pilot_skills.yaml`) are authored-but-dead — do not depend on them.

---

## Task 1: Load maneuver metadata (class + energy cost) so the brain can gate affordability

The legal maneuver ids live in `interaction_table.maneuvers_consumed`, but the per-maneuver **class** and **energy_cost** (in `dogfight/maneuvers_mvp.yaml`) are authored-but-not-loaded. The brain needs cost (to gate affordability) and class (to express attitude). Load them onto the ConfrontationDef via the existing `_from:` pattern.

**Files:**
- Modify: `sidequest-server/sidequest/genre/models/rules.py` (add `ManeuverDef` model + `maneuvers` field on `ConfrontationDef`)
- Modify: `sidequest-server/sidequest/genre/loader.py` (resolve a `maneuvers` `_from:` pointer like `interaction_table`)
- Modify: `sidequest-content/genre_packs/space_opera/rules.yaml` (dogfight def: `maneuvers: {_from: dogfight/maneuvers_mvp.yaml}`)
- Test: `sidequest-server/tests/genre/test_maneuver_loading.py`

**Interfaces:**
- Produces: `ConfrontationDef.maneuvers: list[ManeuverDef]` where `ManeuverDef(id: str, maneuver_class: str, energy_cost: int)`.

- [ ] **Step 1: Confirm maneuvers_mvp.yaml is not already loaded (bounded read)**

```bash
cd /Users/slabgorb/Projects/oq-3/sidequest-server && grep -rn "maneuvers_mvp\|maneuver_class\|energy_cost\|ManeuverDef" sidequest/genre/ sidequest/server/dispatch/sealed_letter.py
```
Expected: no `ManeuverDef`/`energy_cost` loading today (only the interaction table loads). If a loader path already exists, adapt Steps 3-4 to it.

- [ ] **Step 2: Write the failing test**

Create `sidequest-server/tests/genre/test_maneuver_loading.py`:

```python
from sidequest.genre.models.rules import ManeuverDef


def test_maneuver_def_fields():
    m = ManeuverDef(id="loop", maneuver_class="offensive", energy_cost=30)
    assert m.id == "loop"
    assert m.maneuver_class == "offensive"
    assert m.energy_cost == 30


def test_maneuver_def_defaults_zero_cost():
    m = ManeuverDef(id="straight", maneuver_class="passive", energy_cost=-5)
    assert m.energy_cost == -5  # negative = recovery
```

- [ ] **Step 3: Run to confirm failure**

Run: `cd sidequest-server && uv run pytest tests/genre/test_maneuver_loading.py -v -n0`
Expected: FAIL — `ImportError: cannot import name 'ManeuverDef'`.

- [ ] **Step 4: Add the model + field**

In `sidequest/genre/models/rules.py`, near `InteractionTable`:

```python
class ManeuverDef(BaseModel):
    """A dogfight maneuver's positioning metadata (ADR-153). Class drives the
    opponent brain's attitude preference; energy_cost gates affordability.
    The maneuver's GEOMETRY effect lives in the interaction table, not here."""

    model_config = {"extra": "ignore"}  # maneuvers_mvp.yaml carries flavor fields we don't consume

    id: str
    maneuver_class: str = Field(alias="class")
    energy_cost: int = 0
```

In `class ConfrontationDef`, add beside `interaction_table`:

```python
    maneuvers: list[ManeuverDef] = Field(default_factory=list)
```

- [ ] **Step 5: Resolve the `maneuvers` `_from:` pointer in the loader**

In `sidequest/genre/loader.py`, find where `interaction_table`'s `_from:` is resolved (`_load_rules_config`, ~line 267-321) and add the same resolution for a `maneuvers` key whose YAML carries a top-level `maneuvers:` list. Mirror the existing pointer code exactly (same absolute-path / traversal / nested-`_from:` rejection). After resolving the sub-file, set `conf["maneuvers"] = resolved_yaml["maneuvers"]`.

- [ ] **Step 6: Wire the content pointer**

In `sidequest-content/genre_packs/space_opera/rules.yaml`, in the `- type: dogfight` def, add:

```yaml
    maneuvers:
      _from: dogfight/maneuvers_mvp.yaml
```

- [ ] **Step 7: Run unit test + load the live pack**

```bash
cd sidequest-server && uv run pytest tests/genre/test_maneuver_loading.py -v -n0
SIDEQUEST_GENRE_PACKS=../sidequest-content/genre_packs uv run python -c "
from sidequest.genre.loader import load_genre_pack
d = next(c for c in load_genre_pack('space_opera').rules.confrontations if c.confrontation_type=='dogfight')
print({m.id: (m.maneuver_class, m.energy_cost) for m in d.maneuvers})
assert {m.id for m in d.maneuvers} == {'straight','bank','loop','kill_rotation'}
print('OK')
"
```
Expected: prints the maneuver map and `OK`. (`maneuvers_mvp.yaml` uses `class:` + `energy_cost:` keys — the `alias='class'` handles it; `extra='ignore'` drops the flavor fields.)

- [ ] **Step 8: Commit (both repos)**

```bash
cd sidequest-content && git checkout develop && git pull && git checkout -b feat/158-39-dogfight-opponent-brain
git add genre_packs/space_opera/rules.yaml && git commit -m "feat(space_opera): load dogfight maneuver metadata (class + energy cost) for the opponent brain (ADR-153)"
cd ../sidequest-server && git checkout develop && git pull && git checkout -b feat/158-39-dogfight-opponent-brain
git add sidequest/genre/models/rules.py sidequest/genre/loader.py tests/genre/test_maneuver_loading.py
git commit -m "feat(dogfight): ManeuverDef + maneuvers _from: loader for the opponent brain (ADR-153)"
```

---

## Task 2: Pure deterministic opponent-maneuver policy

A pure function: given the opponent's attitude, the legal maneuvers (with class + cost), and current energy, pick a maneuver. Motivation = attitude → class preference. Affordability = energy gate. Tie-break = turn seed (resume-safe). No I/O, fully unit-testable.

**Files:**
- Create: `sidequest-server/sidequest/game/dogfight_brain.py`
- Test: `sidequest-server/tests/game/test_dogfight_brain.py`

**Interfaces:**
- Produces: `select_opponent_maneuver(*, attitude: str, maneuvers: list[ManeuverDef], energy: int, turn_seed: int) -> str` — returns a maneuver id guaranteed to be in `maneuvers` and affordable (or the cheapest if none preferred is affordable).

- [ ] **Step 1: Write the failing test**

Create `sidequest-server/tests/game/test_dogfight_brain.py`:

```python
from sidequest.game.dogfight_brain import select_opponent_maneuver
from sidequest.genre.models.rules import ManeuverDef

MANEUVERS = [
    ManeuverDef(id="straight", **{"class": "passive"}, energy_cost=-5),
    ManeuverDef(id="bank", **{"class": "evasive"}, energy_cost=5),
    ManeuverDef(id="loop", **{"class": "offensive"}, energy_cost=30),
    ManeuverDef(id="kill_rotation", **{"class": "offensive_space_only"}, energy_cost=5),
]


def test_hostile_prefers_offensive_when_affordable():
    pick = select_opponent_maneuver(attitude="hostile", maneuvers=MANEUVERS, energy=60, turn_seed=1)
    assert pick in {"loop", "kill_rotation"}


def test_hostile_falls_back_to_cheaper_offensive_when_loop_unaffordable():
    # energy 10 can't afford loop(30) but can afford kill_rotation(5)
    pick = select_opponent_maneuver(attitude="hostile", maneuvers=MANEUVERS, energy=10, turn_seed=1)
    assert pick == "kill_rotation"


def test_friendly_prefers_evasive_or_recovery():
    pick = select_opponent_maneuver(attitude="friendly", maneuvers=MANEUVERS, energy=60, turn_seed=1)
    assert pick in {"bank", "straight"}


def test_no_affordable_offensive_falls_back_to_cheapest_legal():
    # energy 0: only straight (recovers) and... bank(5)/kill_rotation(5) unaffordable at 0
    pick = select_opponent_maneuver(attitude="hostile", maneuvers=MANEUVERS, energy=0, turn_seed=1)
    assert pick == "straight"  # the only maneuver with cost <= 0


def test_deterministic_for_same_seed():
    a = select_opponent_maneuver(attitude="neutral", maneuvers=MANEUVERS, energy=60, turn_seed=7)
    b = select_opponent_maneuver(attitude="neutral", maneuvers=MANEUVERS, energy=60, turn_seed=7)
    assert a == b


def test_always_returns_a_legal_maneuver():
    ids = {m.id for m in MANEUVERS}
    for att in ("hostile", "neutral", "friendly"):
        for e in (0, 5, 30, 60):
            assert select_opponent_maneuver(attitude=att, maneuvers=MANEUVERS, energy=e, turn_seed=3) in ids
```

- [ ] **Step 2: Run to confirm failure**

Run: `cd sidequest-server && uv run pytest tests/game/test_dogfight_brain.py -v -n0`
Expected: FAIL — module does not exist.

- [ ] **Step 3: Implement the pure policy**

Create `sidequest/game/dogfight_brain.py`:

```python
"""Deterministic opponent-maneuver policy for the dogfight (ADR-153 §4).

Pure positioning decision: pick a maneuver id from the legal+affordable set,
weighted by the opponent ace's disposition attitude. NO geometry, NO damage
(firewall). Resume-safe: deterministic given (attitude, maneuvers, energy,
turn_seed) — the tie-break is seeded, never Math.random.

This is the DETERMINISTIC FALLBACK + the legality reference. The narrator is
the primary chooser (ADR-153 §4); this fires when the narrator omits or picks
an illegal opponent maneuver, and as the floor under a skipped narrator pass.
"""

from __future__ import annotations

from sidequest.genre.models.rules import ManeuverDef

# Attitude → ordered class preference. An ace out for blood presses offense; a
# pilot trying to live breaks and recovers; neutral balances.
_PREFERENCE: dict[str, tuple[str, ...]] = {
    "hostile": ("offensive", "offensive_space_only", "evasive", "passive"),
    "neutral": ("evasive", "offensive", "offensive_space_only", "passive"),
    "friendly": ("evasive", "passive", "offensive", "offensive_space_only"),
}


def _affordable(m: ManeuverDef, energy: int) -> bool:
    # A recovery maneuver (negative cost) is always affordable; a spend needs the budget.
    return m.energy_cost <= 0 or energy >= m.energy_cost


def select_opponent_maneuver(
    *, attitude: str, maneuvers: list[ManeuverDef], energy: int, turn_seed: int
) -> str:
    """Pick a legal, affordable maneuver id weighted by attitude. Always returns
    an id present in ``maneuvers`` (falls back to the cheapest legal maneuver if
    no preferred class is affordable)."""
    if not maneuvers:
        raise ValueError("opponent brain: no legal maneuvers to choose from")
    order = _PREFERENCE.get(attitude, _PREFERENCE["neutral"])
    affordable = [m for m in maneuvers if _affordable(m, energy)]
    pool = affordable or maneuvers  # if nothing affordable, consider all (cheapest wins below)

    for cls in order:
        candidates = sorted((m for m in pool if m.maneuver_class == cls), key=lambda m: m.id)
        if candidates:
            return candidates[turn_seed % len(candidates)].id
    # No class matched preference (unknown classes): cheapest by cost, then id.
    cheapest = sorted(pool, key=lambda m: (m.energy_cost, m.id))
    return cheapest[0].id
```

- [ ] **Step 4: Run to confirm pass**

Run: `cd sidequest-server && uv run pytest tests/game/test_dogfight_brain.py -v -n0`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
cd sidequest-server && git add sidequest/game/dogfight_brain.py tests/game/test_dogfight_brain.py
git commit -m "feat(dogfight): deterministic disposition-weighted opponent-maneuver policy (ADR-153)"
```

---

## Task 3: Wire the legality gate + fallback into the sealed-letter seam + OTEL source

At the sealed-letter resolution seam (`narration_apply.py` ~6048-6095), after `commits` is built: if the blue (opponent) commit is missing OR not a legal maneuver, substitute the policy's pick instead of raising. Stamp the OTEL `dogfight.maneuver_committed` span with a `source` (`narrator` | `fallback` | `substituted`) and the motivating attitude.

**Files:**
- Modify: `sidequest-server/sidequest/server/narration_apply.py` (sealed-letter branch, ~6048-6095)
- Modify: `sidequest-server/sidequest/telemetry/spans/dogfight.py` (`dogfight_maneuver_committed_span`: add `source` + `attitude` attrs)
- Test: `sidequest-server/tests/server/dispatch/test_opponent_brain_wiring.py`

**Interfaces:**
- Consumes: `select_opponent_maneuver` (Task 2), `cdef.maneuvers` (Task 1), `Npc.disposition.attitude()`.

- [ ] **Step 1: Add `source`/`attitude` attrs to the maneuver-committed span**

In `sidequest/telemetry/spans/dogfight.py`, extend `dogfight_maneuver_committed_span` to accept optional `source: str = "narrator"` and `attitude: str = ""` keyword args and include them in the span attributes dict (mirror the existing attr-passing pattern). Confirm current signature: `grep -n "def dogfight_maneuver_committed_span" sidequest/telemetry/spans/dogfight.py`.

- [ ] **Step 2: Write the failing wiring test**

Create `sidequest-server/tests/server/dispatch/test_opponent_brain_wiring.py`. Drive a sealed-letter turn where the narrator emits ONLY the player's (red) maneuver; assert the opponent (blue) gets a committed maneuver from the policy and the encounter resolves (no `ValueError`), with the OTEL span carrying `source="fallback"`. Use the dogfight fixtures + span exporter (`grep -rln "get_finished_spans" tests/`).

```python
from tests.fixtures.dogfight_playtest_encounter import make_seated_dogfight_snapshot  # PC+opponent seated, pack attached


def test_missing_blue_maneuver_uses_disposition_fallback(span_exporter):
    snap, pack = make_seated_dogfight_snapshot(opponent_disposition=-40)  # hostile
    # Narrator emitted only the player's maneuver (red); blue omitted.
    result = _drive_sealed_letter_turn(snap, pack, red_maneuver="straight", blue_maneuver=None)

    enc = snap.encounter
    blue = next(a for a in enc.actors if a.side == "opponent")
    # Blue committed a legal maneuver via the fallback (no ValueError raised).
    assert blue.per_actor_state  # geometry applied -> a cell resolved -> both commits were present

    spans = span_exporter.get_finished_spans()
    committed = [s for s in spans if s.name.endswith("maneuver_committed")]
    blue_span = next(s for s in committed if s.attributes.get("role") == "blue")
    assert blue_span.attributes.get("source") == "fallback"
    assert blue_span.attributes.get("attitude") == "hostile"
```

(Build `_drive_sealed_letter_turn` to invoke the real sealed-letter apply path in `narration_apply` with a synthetic `NarrationTurnResult` carrying the given beat_selections — model it on the existing `tests/server/dispatch/test_sealed_letter_dispatch_integration.py` driver.)

- [ ] **Step 3: Run to confirm failure**

Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_opponent_brain_wiring.py -v -n0`
Expected: FAIL — today a missing blue commit raises `ValueError` ("missing 'blue' key") before any fallback.

- [ ] **Step 4: Wire the gate + fallback at the seam**

In `sidequest/server/narration_apply.py`, in the sealed-letter branch right after `commits` is built (after line ~6057, before the `resolve_sealed_letter_lookup` call ~6095):

```python
        # ADR-153 §4 opponent brain: the narrator is the primary chooser, but the
        # engine guarantees the opponent always commits a LEGAL maneuver. If the
        # narrator omitted blue, or picked a maneuver not in the table's legal set,
        # substitute a deterministic disposition-weighted pick (loud via OTEL).
        from sidequest.game.dogfight_brain import select_opponent_maneuver

        blue_actor = enc.find_actor_by_role("blue")
        if blue_actor is not None and cdef.maneuvers:
            legal_ids = set(cdef.interaction_table.maneuvers_consumed) if cdef.interaction_table else set()
            legal_maneuvers = [m for m in cdef.maneuvers if not legal_ids or m.id in legal_ids]
            blue_commit = commits.get("blue")
            narrator_legal = blue_commit is not None and (not legal_ids or blue_commit in legal_ids)
            if not narrator_legal:
                opp_npc = next((n for n in snapshot.npcs if n.core.name == blue_actor.name), None)
                attitude = opp_npc.disposition.attitude().value if opp_npc is not None else "neutral"
                energy = int(blue_actor.per_actor_state.get("viewer_energy", 60))
                source = "substituted" if blue_commit is not None else "fallback"
                commits["blue"] = select_opponent_maneuver(
                    attitude=attitude,
                    maneuvers=legal_maneuvers,
                    energy=energy,
                    turn_seed=snapshot.turn_manager.interaction,
                )
                with dogfight_maneuver_committed_span(
                    actor=blue_actor.name,
                    maneuver=commits["blue"],
                    role="blue",
                    source=source,
                    attitude=attitude,
                ):
                    pass
```

(Confirm `enc.find_actor_by_role` exists — the resolver uses role lookup; if the accessor is named differently, use the same one the resolver uses. Import `dogfight_maneuver_committed_span` at the call site or module top.)

- [ ] **Step 5: Run to confirm pass + no regression on the existing sealed-letter integration**

```bash
cd sidequest-server && uv run pytest tests/server/dispatch/test_opponent_brain_wiring.py tests/server/dispatch/test_sealed_letter_dispatch_integration.py -v -n0
```
Expected: PASS. The existing integration (narrator emits both commits) still uses the narrator's blue pick (`source="narrator"`, unchanged) because `narrator_legal` is true.

- [ ] **Step 6: Commit**

```bash
cd sidequest-server && git add sidequest/server/narration_apply.py sidequest/telemetry/spans/dogfight.py tests/server/dispatch/test_opponent_brain_wiring.py
git commit -m "feat(dogfight): legality gate + disposition fallback for opponent maneuver, OTEL source (ADR-153)"
```

---

## Task 4: Motivate the narrator's pick — surface the opponent ace's stance pre-narrator

So the narrator's *primary* pick (the common path) is goal-driven rather than improvised, surface the opponent ace's disposition/stance as a narrator directive before narration, mirroring `npc_agency`. This is the "make the narrator's choice motivated" half of ADR-153 §4 (Task 3 is the engine floor).

**Files:**
- Modify: `sidequest-server/sidequest/agents/subsystems/dogfight.py` (`run_dogfight_dispatch`: emit a stance directive when seating/continuing a dogfight)
- Test: `sidequest-server/tests/agents/subsystems/test_dogfight_dispatch_wiring.py` (extend)

**Interfaces:**
- Consumes: `Npc.disposition.attitude()`, `SubsystemOutput(directives=[...])`.
- Produces: a `NarratorDirective` naming the opponent's stance + maneuver tendency.

- [ ] **Step 1: Write the failing test**

Extend `tests/agents/subsystems/test_dogfight_dispatch_wiring.py` with a test asserting `run_dogfight_dispatch` returns a directive describing the opponent's stance when the seated opponent has a hostile disposition:

```python
async def test_dogfight_dispatch_emits_opponent_stance_directive():
    snap, pack = make_dogfight_dispatch_fixture(opponent_disposition=-50)  # hostile ace
    out = await run_dogfight_dispatch(
        _dispatch(opponent="Red Baron"), snapshot=snap, pack=pack, player_name="Pilot",
    )
    assert any("stance" in d.payload.lower() or "press" in d.payload.lower() for d in out.directives)
```

(Use the fixture factory the file already uses; add the `opponent_disposition` knob.)

- [ ] **Step 2: Run to confirm failure**

Run: `cd sidequest-server && uv run pytest tests/agents/subsystems/test_dogfight_dispatch_wiring.py -k stance -v -n0`
Expected: FAIL — no stance directive emitted today.

- [ ] **Step 3: Emit the stance directive on a successful seat**

In `sidequest/agents/subsystems/dogfight.py`, in `run_dogfight_dispatch` after the encounter seats successfully (just before the final `dogfight_dispatch_span` / `return SubsystemOutput()`), resolve the opponent NPC's attitude and return a directive:

```python
    from sidequest.agents.subsystems import NarratorDirective  # confirm import path/name

    opp = next((n for n in snapshot.npcs if n.core.name == (threat_name or "")), None)
    stance = opp.disposition.attitude().value if opp is not None else "hostile"
    _tendency = {
        "hostile": "presses the attack — favors aggressive reversals even at an energy cost",
        "neutral": "flies a balanced fight — breaks when threatened, takes shots when offered",
        "friendly": "is trying to disengage — favors evasive breaks and energy recovery",
    }.get(stance, "flies to its disposition")
    directive = NarratorDirective(
        kind="must_honor",
        payload=(
            f"The enemy ace's stance (disposition toward the player: {stance}) {_tendency}. "
            f"Pick its maneuver consistent with that stance from the legal maneuver menu."
        ),
        visibility=dispatch.visibility,
    )
    with dogfight_dispatch_span(encounter_type=enc_type, opponent=threat_name):
        pass
    return SubsystemOutput(directives=[directive])
```

(Confirm `NarratorDirective`'s constructor + `SubsystemOutput`'s `directives` field against `npc_agency.py` and `subsystems/__init__.py`; match the exact kinds/fields they use.)

- [ ] **Step 4: Run to confirm pass + no regression**

```bash
cd sidequest-server && uv run pytest tests/agents/subsystems/test_dogfight_dispatch_wiring.py -v -n0
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd sidequest-server && git add sidequest/agents/subsystems/dogfight.py tests/agents/subsystems/test_dogfight_dispatch_wiring.py
git commit -m "feat(dogfight): surface opponent ace stance as a narrator directive (ADR-153 §4)"
```

---

## Task 5: End-to-end wiring — a motivated, gated opponent across a multi-turn duel

Prove the brain end-to-end: a hostile ace's maneuvers stay legal+affordable across turns and never wedge the duel, with `dogfight.maneuver_committed` spans showing the source each turn.

**Files:**
- Test: `sidequest-server/tests/server/dispatch/test_opponent_brain_e2e.py`

- [ ] **Step 1: Write the test**

Create `tests/server/dispatch/test_opponent_brain_e2e.py`: seat a dogfight with a hostile ace; drive 3 sealed-letter turns where the narrator omits blue every turn; assert every turn commits a legal blue maneuver, energy never goes negative, and 3 `maneuver_committed` spans with `role="blue"` fire with `source="fallback"`.

```python
def test_three_turn_duel_opponent_never_wedges(span_exporter):
    snap, pack = make_seated_dogfight_snapshot(opponent_disposition=-60)
    legal = set(next(c for c in pack.rules.confrontations
                     if c.confrontation_type == "dogfight").interaction_table.maneuvers_consumed)
    for turn, red in enumerate(["straight", "bank", "loop"], start=1):
        snap.turn_manager.interaction = turn
        _drive_sealed_letter_turn(snap, pack, red_maneuver=red, blue_maneuver=None)
        blue = next(a for a in snap.encounter.actors if a.side == "opponent")
        assert int(blue.per_actor_state.get("viewer_energy", 60)) >= 0
        if snap.encounter.resolved:
            break
    blue_commits = [s for s in span_exporter.get_finished_spans()
                    if s.name.endswith("maneuver_committed") and s.attributes.get("role") == "blue"]
    assert blue_commits, "opponent committed a maneuver each turn"
    assert all(s.attributes.get("source") == "fallback" for s in blue_commits)
```

- [ ] **Step 2: Run + full dogfight suite (serial, OTEL deadlock)**

```bash
cd sidequest-server && uv run pytest tests/server/dispatch/test_opponent_brain_e2e.py tests/game/test_dogfight_brain.py tests/server/dispatch/test_opponent_brain_wiring.py tests/agents/subsystems/test_dogfight_dispatch_wiring.py -n0 -q
```
Expected: PASS (verify suspected pre-existing failures against `develop`).

- [ ] **Step 3: Lint + commit**

```bash
cd sidequest-server && uv run ruff check sidequest/game/dogfight_brain.py sidequest/server/narration_apply.py sidequest/agents/subsystems/dogfight.py tests/server/dispatch/test_opponent_brain_e2e.py
git add tests/server/dispatch/test_opponent_brain_e2e.py
git commit -m "test(dogfight): e2e opponent brain — motivated, gated, never wedges (ADR-153)"
```

---

## Self-Review

**Spec coverage (ADR-153 §4):** narrator picks motivated move → Task 4 (stance directive). Engine gates legality → Task 3 (legal+affordable gate). Deterministic disposition fallback → Tasks 2 (policy) + 3 (wiring). OTEL source/stance → Tasks 3 (span attrs) + 5 (e2e assertion). Firewall preserved (brain picks maneuver only, SWN resolves) → no resolution math added anywhere.

**Placeholder scan:** "confirm accessor/constructor names" notes (Tasks 3/4) are bounded located reads (one file each), not TODOs. Pilot-tier maneuver gating is explicitly out of scope (tiers authored-but-dead) — energy is the live affordability gate; flagged.

**Type consistency:** `ManeuverDef(id, maneuver_class[alias=class], energy_cost)`, `select_opponent_maneuver(*, attitude, maneuvers, energy, turn_seed) -> str`, and `dogfight_maneuver_committed_span(actor, maneuver, role, source, attitude)` are consistent across Tasks 1-5. `Npc.disposition.attitude().value` returns the lowercase string ("hostile"/"neutral"/"friendly") used by the policy's `_PREFERENCE` keys.
