# Dogfight Rebuild — Plan 2: Router → Seater → Lifecycle Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the three `space_opera` dogfight *lifecycle* findings from the 2026-06-25 `coyote_star` playtest: a ship-combat verb that the IntentRouter declines must still **dispatch the dogfight seater** and **degrade loudly** instead of leaving the narrator to grind to a `max_turns` crash (158-29); a **resolved/husk-reaped** dogfight must never **resurrect** the same turn (158-30); and the **dogfight-shot replay** must narrate the resolved gun pass, not re-emit the prior turn's prose (158-35).

**Architecture:** Per [ADR-153](../../adr/153-ace-of-aces-dogfight-positioning-swn-resolution.md) §7 (the router → seater → lifecycle contract). This is the layer **above** Plan 1: Plan 1 made the *seater* correct (a `sealed_letter_lookup` dogfight resolves via SWN `hp_depletion` and seats a frame-default ship opponent when none is named); Plan 2 makes the *path into and out of* that seater honest. Three independent server seams: (1) the IntentRouter pre-narrator pass force-dispatches the dogfight when dogfight verbs hit but no confrontation routed and no fight is live; (2) the encounter-lifecycle husk-reap leaves a one-turn marker so the seater refuses to re-seat a duel reaped *this same turn* (a reaped duel stays reaped); (3) the dogfight-shot dice-replay narration anchors the narrator to the `[DOGFIGHT_SHOT_RESOLVED]` outcome. The existing `run_dogfight_dispatch` already degrades loudly via the `dogfight.dispatch.rejected` span — Plan 2 wires the router *to* it, it does not reinvent the degradation.

**Tech Stack:** Python 3.12 / pydantic v2 / FastAPI WebSocket (sidequest-server), pytest + pytest-xdist (`uv run pytest`, `-n auto` default; `-n0` for serial), OpenTelemetry spans. Server-only; no content or UI changes.

## Global Constraints

- **DEPENDS ON Plan 1 being merged first.** Task 1's force-dispatch relies on the seater seating a *frame-default* ship opponent when the router names none (Plan 1 Task 3). On a checkout where Plan 1 has not landed, Task 1's wiring test will surface a `NoOpponentAvailableError` reject instead of a seat. Confirm `instantiate_encounter_from_trigger` seats a default opponent for a no-named-opponent dogfight (Plan 1 Task 3) before starting — `grep -n "frame_default\|opponent_default_stats" sidequest/server/dispatch/encounter_lifecycle.py`.
- **No silent fallbacks / no stubs** (CLAUDE.md). Every refusal to seat, re-seat, or carry an encounter fails *observably* — an OTEL span and/or a watcher event, never a silent skip.
- **The firewall is doctrine** (ADR-153 §2): nothing in Plan 2 calls `apply_beat` or touches a native dial. The dogfight resolves via SWN `hp_depletion`; Plan 2 only governs routing and lifecycle.
- **OTEL is the lie detector** (CLAUDE.md, ADR-153 §8): assert on spans / watcher events, never on narration source text.
- **No source-text wiring tests** (sidequest-server/CLAUDE.md). Never `read_text()` a production module and grep it as an assertion. Use OTEL span assertions, fixture-driven behavior tests, or a function's returned value (a prompt builder's output given an input is a *behavior* test, not a source grep).
- **The 158-41 boundary.** The *general* "narrator `max_turns` must degrade, not wedge the session" robustness fix is a SEPARATE story (158-41) and is **out of scope**. Plan 2 guarantees only that the *dogfight path* degrades: the router seats the dogfight (so the narrator gets a real engine), and a dogfight that cannot seat emits a loud span. Do not touch the Anthropic SDK loop / `AnthropicSdkLoopExceeded` / `disconnect_save` here.
- **Branching:** `sidequest-server` targets `develop` (github-flow). Feature branch `feat/dogfight-rebuild-lifecycle`.
- **Serial test runs for OTEL span-count tests** (`project_server_test_otel_deadlock`): run span-assertion suites with `-n0`.

---

## Task 1: Router force-dispatches the dogfight seater on a dogfight-verb miss (158-29)

**The disambiguation (resolved from code, was open in the story):** the 158-29 crash is a **dispatch-key-miss, not a dispatch-then-reject.** At `intent_router_pass.py:897` the guard `if verb_hits and not conf_types and not _encounter_active:` only *logs* `intent_router.confrontation_verb_unrouted` — the router's LLM `decompose()` emitted **no** confrontation dispatch, so `run_dispatch_bank` never calls `run_dogfight_dispatch`, no engine seats, and the narrator is handed a raw ship-combat action it grinds into a `max_turns` crash. The contract (ADR-153 §7): when dogfight verbs hit and nothing routed, the router must *force-dispatch* the dogfight seater. `run_dogfight_dispatch` then seats it (Plan 1 frame-default) or rejects loud via `dogfight.dispatch.rejected`.

**The over-fire gate (a real calibration decision).** The dogfight def's authored `intent_verbs` include generic single words (`lock`, `gun`, `engage`) — "lock the door" lexically hits `dogfight:lock`. Force-dispatching on *any* lexical hit would seat a phantom dogfight on a non-combat action (exactly the convincing-prose-with-no-backing failure the OTEL lie-detector exists to catch). So the force-dispatch fires only on a **strong** ship-combat signal: a hit on an *unambiguous* dogfight verb (`dogfight`/`intercept`/`pursue`/`missile`), **or** ≥2 *distinct* dogfight-verb hits. The repro action "bring guns online, lock a firing solution" → `gun` + `lock` = 2 distinct hits → force-dispatches. "lock the door" → 1 generic hit → does not. This gate is the calibration point; it is intentionally conservative (a missed force-dispatch degrades to today's behavior, a wrong one mis-seats a fight).

**Files:**
- Create: `sidequest-server/sidequest/telemetry/spans/__addition__` — add ONE span to the existing `sidequest/telemetry/spans/dogfight.py`
- Modify: `sidequest-server/sidequest/server/intent_router_pass.py` (new injector `force_dispatch_dogfight_on_verb_miss`, called in `execute_intent_router_pre_narrator_pass` after the classification block ~line 915, before the gates ~line 968)
- Test: `sidequest-server/tests/server/test_intent_router_dogfight_force_dispatch.py`

**Interfaces:**
- Consumes: `_confrontation_verb_hits(action, pack) -> list[str]` (returns `f"{type}:{verb}"`, `intent_router_pass.py:186`), `_confrontation_types_emitted(package) -> list[str]` (`intent_router_pass.py:172`), `_resolve_dogfight_type(pack) -> str | None` (`sidequest/agents/subsystems/dogfight.py:58`), `SubsystemDispatch(subsystem: str, params: dict)` (`sidequest/protocol/dispatch.py:106`), `DispatchPackage.per_player[].dispatch: list[SubsystemDispatch]` + `.player_id: str` (`dispatch.py:204/206`).
- Produces: `force_dispatch_dogfight_on_verb_miss(package, *, snapshot, pack, action, player_name) -> bool` — injects one `SubsystemDispatch(subsystem="dogfight", params={"type": <dogfight_type>})` into the submitting player's `per_player` entry and returns `True` when it force-dispatched; emits `dogfight.forced_dispatch`. `dogfight_forced_dispatch_span(*, encounter_type, verb_hits)` (new span helper).

- [ ] **Step 1: Branch the server repo**

```bash
cd sidequest-server && git checkout develop && git pull && git checkout -b feat/dogfight-rebuild-lifecycle
```

- [ ] **Step 2: Add the `dogfight.forced_dispatch` span**

In `sidequest/telemetry/spans/dogfight.py`, alongside the existing `dogfight_dispatch_span` / `dogfight_dispatch_rejected_span` (the file already defines `SPAN_DOGFIGHT_DISPATCH` at line 277 and its helper), add a sibling span name + context-manager helper, matching the file's exact idiom (`Span.open(...)`):

```python
SPAN_DOGFIGHT_FORCED_DISPATCH = "dogfight.forced_dispatch"


@contextmanager
def dogfight_forced_dispatch_span(
    *,
    encounter_type: str,
    verb_hits: str,
    _tracer: trace.Tracer | None = None,
    **attrs: Any,
) -> Iterator[trace.Span]:
    """Router force-dispatched the dogfight seater on a dogfight-verb miss
    (ADR-153 §7 / 158-29): dogfight verbs hit, the LLM router emitted no
    confrontation dispatch, no fight was live — so the engine is seated FIRST
    rather than leaving the narrator a raw ship-combat action to grind."""
    with Span.open(
        SPAN_DOGFIGHT_FORCED_DISPATCH,
        {"encounter_type": encounter_type, "verb_hits": verb_hits, **attrs},
        tracer_override=_tracer,
    ) as span:
        yield span
```

Add `dogfight_forced_dispatch_span` and `SPAN_DOGFIGHT_FORCED_DISPATCH` to the module's `__all__`. (Confirm the import block at the top of `dogfight.py` already has `contextmanager`, `Iterator`, `Any`, `trace`, `Span` — it does, the existing helpers use them.)

- [ ] **Step 3: Write the failing test for the injector**

Create `sidequest-server/tests/server/test_intent_router_dogfight_force_dispatch.py`. Build a synthetic `space_opera`-shaped pack carrying a `sealed_letter_lookup` combat dogfight def (reuse `tests/fixtures/dogfight_playtest_encounter.py` factories — read the file for the actual factory names; it constructs a real dogfight pack/snapshot), an empty `DispatchPackage` (no confrontation dispatch), and a snapshot with no active encounter. Assert the injector force-dispatches on a strong signal and refrains on a weak/ambiguous one.

```python
import pytest

from sidequest.protocol.dispatch import DispatchPackage, SubsystemDispatch
from sidequest.server.intent_router_pass import force_dispatch_dogfight_on_verb_miss
from tests.fixtures.dogfight_playtest_encounter import (
    make_dogfight_pack,        # synthetic space_opera-shaped pack w/ a sealed_letter dogfight def
    make_empty_snapshot,       # PC seated, no NPCs, no encounter
)


def _empty_package(player_id: str) -> DispatchPackage:
    # One per_player entry for the submitting seat, zero dispatches.
    from sidequest.protocol.dispatch import PerPlayerDispatch
    return DispatchPackage(
        turn_id="t1",
        per_player=[PerPlayerDispatch(player_id=player_id, dispatch=[])],
        cross_player=[],
    )


def test_force_dispatches_on_strong_dogfight_signal():
    pack = make_dogfight_pack()
    snapshot = make_empty_snapshot(pc_name="Pilot")
    package = _empty_package(player_id="Pilot")

    fired = force_dispatch_dogfight_on_verb_miss(
        package,
        snapshot=snapshot,
        pack=pack,
        action="bring guns online, lock a firing solution",  # gun + lock = 2 distinct hits
        player_name="Pilot",
    )

    assert fired is True
    injected = [d for pd in package.per_player for d in pd.dispatch if d.subsystem == "dogfight"]
    assert len(injected) == 1
    # type points at the pack's sealed-letter dogfight so run_dogfight_dispatch seats it.
    assert injected[0].params.get("type")


def test_does_not_force_dispatch_on_weak_single_generic_verb():
    pack = make_dogfight_pack()
    snapshot = make_empty_snapshot(pc_name="Pilot")
    package = _empty_package(player_id="Pilot")

    fired = force_dispatch_dogfight_on_verb_miss(
        package, snapshot=snapshot, pack=pack,
        action="lock the door behind me",  # 1 generic hit, no ship-combat intent
        player_name="Pilot",
    )

    assert fired is False
    assert not [d for pd in package.per_player for d in pd.dispatch if d.subsystem == "dogfight"]


def test_does_not_force_dispatch_when_a_fight_is_already_live():
    pack = make_dogfight_pack()
    snapshot = make_empty_snapshot(pc_name="Pilot")
    # Seat a live (unresolved) encounter so the verb match is an in-fight beat, not a miss.
    from tests.fixtures.dogfight_playtest_encounter import seat_live_dogfight
    seat_live_dogfight(snapshot)
    package = _empty_package(player_id="Pilot")

    fired = force_dispatch_dogfight_on_verb_miss(
        package, snapshot=snapshot, pack=pack,
        action="intercept and gun the bandit", player_name="Pilot",
    )

    assert fired is False
```

(If `make_dogfight_pack`/`make_empty_snapshot`/`seat_live_dogfight` are not present with these names, read `tests/fixtures/dogfight_playtest_encounter.py` and use/extend its real factories. The invariant under test: a strong dogfight signal with no live fight injects exactly one `dogfight` dispatch; a weak signal or a live fight injects none.)

- [ ] **Step 4: Run the test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/server/test_intent_router_dogfight_force_dispatch.py -v -n0`
Expected: FAIL with `ImportError: cannot import name 'force_dispatch_dogfight_on_verb_miss'`.

- [ ] **Step 5: Implement the injector**

In `sidequest/server/intent_router_pass.py`, add the injector near the other module-level helpers (after `_confrontation_verb_hits`, ~line 220). It mirrors `inject_environment_clock`'s pattern (a deterministic post-decompose injection into the package):

```python
# ADR-153 §7 (158-29): the unambiguous ship-combat verbs. A hit on one of
# these, OR ≥2 distinct dogfight-verb hits, is a strong-enough signal to seat
# the dogfight when the LLM router emitted no confrontation dispatch. The
# generic singles (lock/gun/engage) alone are NOT — "lock the door" must never
# seat a fight (the over-fire / phantom-encounter risk).
_STRONG_DOGFIGHT_VERBS = frozenset({"dogfight", "intercept", "pursue", "missile"})


def force_dispatch_dogfight_on_verb_miss(
    package: DispatchPackage,
    *,
    snapshot: GameSnapshot,
    pack: GenrePack | None,
    action: str,
    player_name: str,
) -> bool:
    """Seat the dogfight when ship-combat verbs hit but the router routed nothing.

    The 158-29 contract (ADR-153 §7): a dogfight-verb match with no confrontation
    dispatch and no live fight must DISPATCH the seater — not log-and-continue and
    leave the narrator a raw ship-combat action to grind into a max_turns crash.
    Gated on a strong signal (see ``_STRONG_DOGFIGHT_VERBS``) so a generic verb on
    a non-combat action cannot phantom-seat a fight. Returns True when it injected
    a dogfight dispatch. Fail-loud / observable: emits ``dogfight.forced_dispatch``.
    """
    from sidequest.agents.subsystems.dogfight import _resolve_dogfight_type
    from sidequest.telemetry.spans.dogfight import dogfight_forced_dispatch_span

    dogfight_type = _resolve_dogfight_type(pack) if pack is not None else None
    if not dogfight_type:
        return False  # pack authors no sealed-letter dogfight — nothing to seat.

    enc = snapshot.encounter
    if enc is not None and not getattr(enc, "resolved", False):
        return False  # a live fight: the verb match is an in-fight beat, not a miss.

    if _confrontation_types_emitted(package):
        return False  # the router already routed a confrontation — not a miss.

    # Dogfight-verb hits only (``type:verb`` where type == the dogfight type).
    hits = [
        h for h in _confrontation_verb_hits(action, pack) if h.startswith(f"{dogfight_type}:")
    ]
    verbs = {h.split(":", 1)[1] for h in hits}
    strong = bool(verbs & _STRONG_DOGFIGHT_VERBS) or len(verbs) >= 2
    if not strong:
        return False

    # Inject into the submitting seat's per_player entry (create one if the LLM
    # emitted no per_player slot — mirrors inject_environment_clock's handling).
    dispatch = SubsystemDispatch(subsystem="dogfight", params={"type": dogfight_type})
    target = next((pd for pd in package.per_player if pd.player_id == player_name), None)
    if target is None:
        from sidequest.protocol.dispatch import PerPlayerDispatch

        target = PerPlayerDispatch(player_id=player_name, dispatch=[])
        package.per_player.append(target)
    target.dispatch.append(dispatch)

    with dogfight_forced_dispatch_span(
        encounter_type=dogfight_type, verb_hits=",".join(sorted(verbs))
    ):
        pass
    logger.info(
        "intent_router.dogfight_forced_dispatch type=%s verbs=%s action_len=%d — "
        "dogfight verbs hit, router routed no confrontation, no live fight; seating "
        "the dogfight so the narrator is not left to grind (ADR-153 §7 / 158-29)",
        dogfight_type,
        ",".join(sorted(verbs)),
        len(action),
    )
    return True
```

(Confirm `DispatchPackage`, `SubsystemDispatch`, `GameSnapshot`, `GenrePack`, and `logger` are already imported at the top of `intent_router_pass.py` — `DispatchPackage` and `logger` are used throughout; add the `SubsystemDispatch` import to the existing `from sidequest.protocol.dispatch import ...` line if absent.)

- [ ] **Step 6: Run the injector test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/server/test_intent_router_dogfight_force_dispatch.py -v -n0`
Expected: PASS (all three cases).

- [ ] **Step 7: Wire the injector into the pre-narrator pass**

In `execute_intent_router_pre_narrator_pass`, call the injector AFTER the confrontation-classification block (which ends ~line 915 with the `confrontation_verb_unrouted` log) and BEFORE the unregistered-subsystem gate (`run_unregistered_subsystem_gate`, ~line 968). Placing it here lets the injected `dogfight` dispatch pass both gates (it is a *registered* subsystem, and has no precondition) and reach `run_dispatch_bank`:

```python
        # ADR-153 §7 (158-29): when dogfight verbs hit but the LLM router emitted
        # no confrontation dispatch and no fight is live, SEAT the dogfight here so
        # the narrator gets a real engine instead of grinding a raw ship-combat
        # action into a max_turns crash. The general "narrator max_turns must
        # degrade" robustness gap is tracked separately (158-41); this only
        # guarantees the dogfight path seats-or-degrades-loud.
        force_dispatch_dogfight_on_verb_miss(
            package, snapshot=snapshot, pack=pack, action=action, player_name=player_name
        )
```

Add `force_dispatch_dogfight_on_verb_miss` to the module `__all__` list (line ~1047).

- [ ] **Step 8: Commit**

```bash
cd sidequest-server && git add sidequest/telemetry/spans/dogfight.py sidequest/server/intent_router_pass.py tests/server/test_intent_router_dogfight_force_dispatch.py
git commit -m "fix(dogfight): router force-dispatches the seater on a dogfight-verb miss — degrade loud, never grind (158-29, ADR-153)"
```

---

## Task 2: A husk-reaped dogfight stays reaped — no same-turn resurrection (158-30)

**The mechanism (from code).** A dogfight resolves on its dice-replay shot turn; `reap_resolved_encounter_husk` (`encounter_lifecycle.py:142`) deliberately skips reaping on `is_dice_replay=True` (line 164) so the just-resolved fight can be narrated. On the *next* normal turn, husk-reap runs (`is_dice_replay=False`) and clears the resolved dogfight (`snapshot.encounter = None`, line 205) — correct. The bug (158-30): *that same turn*, the resolved dogfight is **re-seated** — the seater's existing guards (`encounter_lifecycle.py:1540` "live encounter → None"; `1560` "resolved SAME type still on snapshot → None") both pass once the husk is gone (`snapshot.encounter is None`), so a fresh dogfight seats (`structured_phase=EncounterPhase.Setup`, line 2057 — the "Resolution→Setup reset" the playtest saw), and the location-drift continue-ladder (`narration_apply.py:4944`) then keeps the re-seat alive, soft-locking the player into ship maneuvers on foot. "Two lifecycle rules disagree (husk_reaped clear vs drift keep-alive) and drift wins" — because the husk-reap leaves no memory that the type was just reaped, so the re-seat is unguarded.

**The fix (ADR-153 §7: "a reaped duel stays reaped"; "respect the created_turn fresh-this-turn exemption").** Have the husk-reap stamp a one-turn marker `(encounter_type, turn)` on the snapshot when it clears a husk, and add a seater guard: refuse to seat an `encounter_type` that was husk-reaped *this same turn*. A genuinely-fresh dogfight (never reaped this turn) still seats normally — the guard keys on the reaped type + the current turn, so a stale marker from a prior turn is inert. This kills the re-seat at the source; the drift continue-ladder then never sees a resurrected encounter.

**Files:**
- Modify: `sidequest-server/sidequest/game/session.py` (add the transient `husk_reaped_this_turn: tuple[str, int] | None` field to the snapshot — find the `GameSnapshot` dataclass/model)
- Modify: `sidequest-server/sidequest/server/dispatch/encounter_lifecycle.py` (stamp it in `reap_resolved_encounter_husk` ~line 205; read it in the `instantiate_encounter_from_trigger` guard region ~lines 1540–1561)
- Test: `sidequest-server/tests/server/dispatch/test_dogfight_husk_no_resurrect.py`

**Interfaces:**
- Consumes: `reap_resolved_encounter_husk(snapshot, *, is_dice_replay, turn) -> bool`, `instantiate_encounter_from_trigger(...)`, `snapshot.encounter`, `snapshot.turn_manager.interaction`.
- Produces: `snapshot.husk_reaped_this_turn: tuple[str, int] | None`; behavior — `instantiate_encounter_from_trigger` returns `None` (no re-seat) for a type reaped on the current turn.

- [ ] **Step 1: Write the failing reproduction test**

Create `sidequest-server/tests/server/dispatch/test_dogfight_husk_no_resurrect.py`. Seat + resolve a dogfight, husk-reap it on a normal turn, then attempt to re-seat the same type that same turn — assert no resurrection.

```python
from sidequest.server.dispatch.encounter_lifecycle import (
    instantiate_encounter_from_trigger,
    reap_resolved_encounter_husk,
)
from tests.fixtures.dogfight_playtest_encounter import (
    make_dogfight_pack,
    make_empty_snapshot,
    seat_live_dogfight,
)


def test_reaped_dogfight_does_not_reseat_same_turn():
    pack = make_dogfight_pack()
    snapshot = make_empty_snapshot(pc_name="Pilot")
    enc = seat_live_dogfight(snapshot)         # snapshot.encounter is a live dogfight
    enc.resolved = True                        # it resolved (prior dice-replay turn)
    enc.outcome = "player_victory"
    turn = snapshot.turn_manager.interaction

    # Turn start on the next NORMAL turn: husk-reap clears the resolved dogfight.
    reaped = reap_resolved_encounter_husk(snapshot, is_dice_replay=False, turn=turn)
    assert reaped is True
    assert snapshot.encounter is None

    # SAME turn: a re-seat attempt of the just-reaped type must be refused —
    # a reaped duel stays reaped (ADR-153 §7). No Resolution→Setup resurrection.
    result = instantiate_encounter_from_trigger(
        snapshot=snapshot, pack=pack, encounter_type=enc.encounter_type,
        player_name="Pilot", npcs_present=[], genre_slug="space_opera",
    )
    assert result is None
    assert snapshot.encounter is None


def test_fresh_dogfight_still_seats_when_not_reaped_this_turn():
    # The created_turn exemption: a dogfight never reaped this turn seats normally.
    pack = make_dogfight_pack()
    snapshot = make_empty_snapshot(pc_name="Pilot")
    enc = instantiate_encounter_from_trigger(
        snapshot=snapshot, pack=pack, encounter_type="dogfight",
        player_name="Pilot", npcs_present=[], genre_slug="space_opera",
    )
    assert enc is not None
    assert snapshot.encounter is not None
```

(Use the real fixture factory names from `tests/fixtures/dogfight_playtest_encounter.py`. `enc.encounter_type` is the pack's dogfight type. If `seat_live_dogfight` is absent, seat via `instantiate_encounter_from_trigger` with a named opponent and flip `.resolved`.)

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_dogfight_husk_no_resurrect.py -v -n0`
Expected: `test_reaped_dogfight_does_not_reseat_same_turn` FAILS — today the re-seat succeeds (`result is not None`, `snapshot.encounter` is a fresh Setup-phase dogfight), reproducing the resurrection. The second test passes already.

- [ ] **Step 3: Add the transient husk-reaped marker to the snapshot**

In `sidequest/game/session.py`, find the `GameSnapshot` class and add the field (transient per-turn state; default `None`). Place it near `encounter`:

```python
    # ADR-153 §7 (158-30): the (encounter_type, turn) of a husk reaped THIS turn.
    # Lets the seater refuse to re-seat a duel that was just reaped — a reaped
    # duel stays reaped (no Resolution→Setup resurrection). Keyed by turn so a
    # stale marker from a prior turn is inert; transient, not durable canon.
    husk_reaped_this_turn: tuple[str, int] | None = None
```

(Match the surrounding field-declaration idiom — if `GameSnapshot` is a pydantic model use `tuple[str, int] | None = None`; if a dataclass use `field(default=None)`. Confirm with `grep -n "class GameSnapshot" sidequest/game/session.py` and read its field block.)

- [ ] **Step 4: Stamp the marker when a husk is reaped**

In `reap_resolved_encounter_husk` (`encounter_lifecycle.py`), at the clear site (currently line 205, `snapshot.encounter = None`), stamp the marker before clearing:

```python
    snapshot.husk_reaped_this_turn = (enc.encounter_type, turn)
    snapshot.encounter = None
```

- [ ] **Step 5: Guard the seater against a same-turn re-seat**

In `instantiate_encounter_from_trigger`, in the guard region just after the existing resolved-same-type guard (`encounter_lifecycle.py:1560-1561`), add:

```python
    # ADR-153 §7 (158-30): a duel husk-reaped THIS turn stays reaped — refuse to
    # re-seat it the same turn (the husk_reaped clear must win over a same-turn
    # re-dispatch / drift keep-alive, else a resolved dogfight resurrects in Setup
    # and soft-locks the player into ship maneuvers on foot). Keyed by turn so a
    # genuinely-fresh dogfight on a LATER turn still seats (created_turn exemption).
    reaped = snapshot.husk_reaped_this_turn
    if (
        reaped is not None
        and reaped[0] == encounter_type
        and reaped[1] == snapshot.turn_manager.interaction
    ):
        _watcher_publish(
            "state_transition",
            {
                "field": "encounter",
                "op": "reseat_refused_husk_reaped",
                "encounter_type": encounter_type,
                "turn": str(snapshot.turn_manager.interaction),
                "source": "seater",
            },
            component="encounter",
        )
        return None
```

(`_watcher_publish` is already used in this module — `grep -n "_watcher_publish" encounter_lifecycle.py`. The span/event makes the refusal observable per CLAUDE.md, mirroring the `husk_reaped` event the reap emits.)

- [ ] **Step 6: Run the reproduction test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_dogfight_husk_no_resurrect.py -v -n0`
Expected: PASS (both cases) — the re-seat is refused, no resurrection; a fresh dogfight on a clean turn still seats.

- [ ] **Step 7: Run the husk-reap + lifecycle suites (no regression)**

```bash
cd sidequest-server && uv run pytest tests/server/dispatch/test_encounter_husk_reap.py tests/server/dispatch -k "husk or seat or dogfight or lifecycle" -n0 -q
```
Expected: PASS, except failures already pre-existing on `develop` (`project_wwn_content_breaks_server_fixtures` — verify any suspect against `develop` before attributing it here).

- [ ] **Step 8: Commit**

```bash
cd sidequest-server && git add sidequest/game/session.py sidequest/server/dispatch/encounter_lifecycle.py tests/server/dispatch/test_dogfight_husk_no_resurrect.py
git commit -m "fix(dogfight): a husk-reaped duel stays reaped — no same-turn resurrection (158-30, ADR-153)"
```

---

## Task 3: The dogfight-shot replay narrates the resolved gun pass, not stale prose (158-35)

**The mechanism (from code).** When a dogfight shot resolves, `DiceThrowHandler` (`sidequest/handlers/dice_throw.py:253-303`) builds a factual per-shot summary (`_shot_lines`: "Your laser: HIT, 4 dmg to … (hull 4/8)"), sets `enc.narrator_hints += _shot_lines`, synthesizes `replay_text = f"[DOGFIGHT_SHOT_RESOLVED] {_shot_summary}"`, and calls `_execute_narration_turn(sd, replay_text, turn_context, suppress_intent_router=True)`. The narrator is *given* the resolved outcome — but it is not *anchored* to it: the WN "narrate the resolved exchange" directive in `narrator.py` (~line 425) is gated on `is_live_wn_combat`, which a sealed-letter dogfight is not, so the dogfight-shot replay reaches the narrator with no "narrate THIS gun pass, not the prior scene" instruction. Result (158-35): the narrator re-describes the prior turn's sensor sweep and never mentions the maneuver, gun pass, or opponent.

**The fix (trivial, 1pt).** Give the `[DOGFIGHT_SHOT_RESOLVED]` replay its own anchor in the narrator prompt assembly, a sibling of the `[BEAT_RESOLVED]`/WN resolved-exchange directive: when the action begins with `[DOGFIGHT_SHOT_RESOLVED]`, instruct the narrator to narrate the resolved maneuver + gun pass from `enc.narrator_hints` and NOT re-narrate a prior scene. The factual lines already ride in `narrator_hints`; this directive makes them load-bearing.

**Files:**
- Modify: `sidequest-server/sidequest/agents/narrator.py` (the prompt-assembly path — `build_encounter_context` at line 300, and the resolved-exchange directive near line 425; add the sibling `[DOGFIGHT_SHOT_RESOLVED]` branch)
- Test: `sidequest-server/tests/agents/test_dogfight_shot_replay_narration_anchor.py`

**Interfaces:**
- Consumes: the narrator prompt-builder (`build_encounter_context(...)` and/or the action-zone assembly in `narrator.py`), `encounter.narrator_hints: list[str]`, the action string.
- Produces: behavior — for a `[DOGFIGHT_SHOT_RESOLVED]` action, the assembled narrator context/directive carries the resolved-gun-pass anchor (the `narrator_hints` shot lines + a "narrate this resolved exchange" instruction).

- [ ] **Step 1: Locate the resolved-exchange directive**

```bash
cd sidequest-server && grep -n "BEAT_RESOLVED\|narrate the resolved\|resolved exchange\|narrator_hints\|is_live_wn_combat\|def build_encounter_context" sidequest/agents/narrator.py
```
Expected: surfaces `build_encounter_context` (line ~300), the WN resolved-exchange directive (~425, gated on `is_live_wn_combat`), and where `narrator_hints` are folded into the prompt. Identify the exact function that assembles the directive string and returns it (the unit under test).

- [ ] **Step 2: Write the failing prompt-assembly test**

Create `sidequest-server/tests/agents/test_dogfight_shot_replay_narration_anchor.py`. Build the narrator context for a `[DOGFIGHT_SHOT_RESOLVED]` action on a seated dogfight whose `narrator_hints` carry the shot lines; assert the assembled directive/context anchors to the resolved gun pass. This tests the prompt-builder's *return value* given an input (a behavior test of the builder, NOT a source grep — allowed by CLAUDE.md's "No Source-Text Wiring Tests").

```python
from sidequest.agents.narrator import build_encounter_context  # or the directive builder found in Step 1
from tests.fixtures.dogfight_playtest_encounter import make_seated_dogfight


def test_dogfight_shot_replay_anchors_to_the_resolved_gun_pass():
    enc, _ = make_seated_dogfight(pc_hp=8, npc_hp=8)
    enc.narrator_hints = ["Your laser: HIT, 4 dmg to Bandit-2 (hull 4/8)"]

    context = build_encounter_context(
        encounter=enc,
        action="[DOGFIGHT_SHOT_RESOLVED] Your laser: HIT, 4 dmg to Bandit-2 (hull 4/8)",
        # plus whatever required kwargs Step 1 reveals (snapshot/pack/etc.)
    )
    rendered = str(context)  # the assembled directive/context text

    # The resolved gun pass is anchored — its factual shot line must be present,
    # and the narrator must be told to narrate THIS exchange (not a prior scene).
    assert "HIT, 4 dmg to Bandit-2" in rendered
    assert "resolved" in rendered.lower()
```

(Adjust `build_encounter_context`'s kwargs to the real signature from Step 1; if the directive is built by a narrower helper than `build_encounter_context`, target that helper directly. `make_seated_dogfight` is the Plan 1 fixture — add it to `tests/fixtures/dogfight_playtest_encounter.py` if absent: one PC actor + one opponent actor with backing cores, returns `(encounter, edge_resolver)`.)

- [ ] **Step 3: Run the test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/agents/test_dogfight_shot_replay_narration_anchor.py -v -n0`
Expected: FAIL — today no `[DOGFIGHT_SHOT_RESOLVED]` branch fires, so the assembled context lacks the resolved-gun-pass anchor.

- [ ] **Step 4: Add the `[DOGFIGHT_SHOT_RESOLVED]` directive**

In the narrator prompt-assembly path identified in Step 1, add a sibling of the WN resolved-exchange directive that fires when the action begins with `[DOGFIGHT_SHOT_RESOLVED]` and the encounter is a sealed-letter dogfight. Fold `enc.narrator_hints` (the shot lines) into the directive and instruct the narrator to render the resolved maneuver + gun pass. Match the file's existing directive idiom:

```python
        if action.startswith("[DOGFIGHT_SHOT_RESOLVED]") and encounter is not None:
            # ADR-153 §7 (158-35): a dice-replay re-entry for a dogfight shot. The
            # mechanics are already applied; the narrator must NARRATE THIS resolved
            # maneuver + gun pass (from narrator_hints), never re-describe the prior
            # scene. Sibling of the WN [BEAT_RESOLVED] resolved-exchange anchor.
            shot_lines = "\n".join(encounter.narrator_hints or [])
            directive_parts.append(
                "This turn resolved a dogfight gun pass. Narrate the maneuver and "
                "these resolved shots — hits, misses, and hull — as a single "
                "cinematic beat. Do NOT re-describe the previous scene:\n"
                f"{shot_lines}"
            )
```

(Use the real accumulator/return variable the function builds — `directive_parts`/`zones`/the returned context object — from Step 1. Keep the directive in the recency zone the WN branch uses so it dominates the prior-narration context.)

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/agents/test_dogfight_shot_replay_narration_anchor.py -v -n0`
Expected: PASS.

- [ ] **Step 6: Lint + commit**

```bash
cd sidequest-server && uv run ruff check sidequest/agents/narrator.py tests/agents/test_dogfight_shot_replay_narration_anchor.py
git add sidequest/agents/narrator.py tests/agents/test_dogfight_shot_replay_narration_anchor.py
git commit -m "fix(dogfight): narrate the resolved gun pass on dice-replay re-entry — no stale prose (158-35, ADR-153)"
```

---

## Task 4: End-to-end wiring — a router-missed dogfight seats and resolves, on OTEL (158-29)

CLAUDE.md mandates a wiring test driving the production path and asserting on OTEL, not source text. Prove the full 158-29 chain: a ship-combat action the IntentRouter declines (no confrontation dispatch) is force-dispatched, `run_dispatch_bank` seats it via `run_dogfight_dispatch` (Plan 1 frame-default opponent), and the spans fire — `dogfight.forced_dispatch` then `dogfight.dispatch`, never an unrouted dead-end. Plus the degraded path: when no dogfight can seat, `dogfight.dispatch.rejected` fires loud and the turn does not crash.

**Files:**
- Test: `sidequest-server/tests/server/test_dogfight_force_dispatch_wiring.py`

**Interfaces:**
- Consumes: `execute_intent_router_pre_narrator_pass(...)` (`intent_router_pass.py`), the `IntentRouter.decompose` stub (return an empty `DispatchPackage` — the router "miss"), the in-memory span exporter fixture, `run_dispatch_bank`.

- [ ] **Step 1: Write the wiring test**

Create `sidequest-server/tests/server/test_dogfight_force_dispatch_wiring.py`. Stub `IntentRouter.decompose` to return a package with NO confrontation dispatch (the router miss — per `project_e2e_encounter_tests_router_driven`, the router pass MUST be stubbed). Drive `execute_intent_router_pre_narrator_pass` with a strong ship-combat action on a no-encounter snapshot; assert the chain via spans + seated state.

```python
import pytest

from sidequest.server.intent_router_pass import execute_intent_router_pre_narrator_pass
from tests.fixtures.dogfight_playtest_encounter import make_dogfight_pack, make_empty_snapshot


@pytest.mark.asyncio
async def test_router_missed_dogfight_force_dispatches_seats_and_emits_spans(
    span_exporter, monkeypatch
):
    pack = make_dogfight_pack()
    snapshot = make_empty_snapshot(pc_name="Pilot")

    # The router "miss": decompose returns an empty package (no confrontation).
    async def _empty_decompose(*, action, state_summary):
        from sidequest.protocol.dispatch import DispatchPackage, PerPlayerDispatch
        return DispatchPackage(
            turn_id="t1",
            per_player=[PerPlayerDispatch(player_id="Pilot", dispatch=[])],
            cross_player=[],
        )
    # Patch the IntentRouter the pass constructs/uses (confirm the seam in Step-0 grep).
    monkeypatch.setattr("sidequest.agents.intent_router.IntentRouter.decompose", _empty_decompose)

    await execute_intent_router_pre_narrator_pass(
        snapshot=snapshot, pack=pack, player_name="Pilot",
        action="intercept the bandit and bring guns online, lock a firing solution",
        # plus the required kwargs the real signature needs (read its header).
    )

    # The dogfight seated through the production bank, not a dead-ended log.
    assert snapshot.encounter is not None
    assert snapshot.encounter.encounter_type == "dogfight"
    assert snapshot.encounter.resolved is False

    spans = {s.name for s in span_exporter.get_finished_spans()}
    assert any(n.endswith("dogfight.forced_dispatch") or n == "dogfight.forced_dispatch" for n in spans)
    assert any(n.endswith("dogfight.dispatch") or n == "dogfight.dispatch" for n in spans)
```

(Read the real `execute_intent_router_pre_narrator_pass` signature header — it takes `snapshot`, `pack`, `player_name`, `action`, plus threading kwargs (`dungeon_store`, `palette`, `orbital_content`, `turn_number`, …); pass the minimal set the no-op-for-dogfight path needs, mirroring an existing intent-router-pass test. Reuse the in-memory `span_exporter` fixture other telemetry tests use — `grep -rln "InMemorySpanExporter\|span_exporter" tests/`.)

- [ ] **Step 2: Run the wiring test**

Run: `cd sidequest-server && uv run pytest tests/server/test_dogfight_force_dispatch_wiring.py -v -n0`
Expected: PASS — the forced dispatch seats a frame-default dogfight (Plan 1) and both spans fire. If it FAILS with a `NoOpponentAvailableError` reject (`dogfight.dispatch.rejected`), Plan 1's default-from-frame seat (Task 3) has not landed in this checkout — confirm Plan 1 is merged (see Global Constraints) before treating it as a Plan 2 defect.

- [ ] **Step 3: Add the degraded-path assertion (loud, no crash)**

Append a second test in the same file: a pack whose dogfight def cannot seat an Other (no frame-default, no named opponent) force-dispatches, then `run_dogfight_dispatch` rejects LOUD — assert `dogfight.dispatch.rejected` fired and the pass returned without raising (the dogfight path degraded; the general max_turns robustness is 158-41, not asserted here).

```python
@pytest.mark.asyncio
async def test_force_dispatch_that_cannot_seat_degrades_loud(span_exporter, monkeypatch):
    pack = make_dogfight_pack(seatable=False)   # dogfight def present but no Other sourceable
    snapshot = make_empty_snapshot(pc_name="Pilot")
    # ... same empty-decompose stub + drive the pass ...
    spans = {s.name for s in span_exporter.get_finished_spans()}
    assert any("dogfight.dispatch.rejected" in n for n in spans)
    assert snapshot.encounter is None   # nothing wrongly seated
```

(If the fixture has no `seatable=False` knob, build a pack whose dogfight def has no `opponent_default_stats` so the frame-default seat is unavailable and the No-Opponent guard raises → `run_dogfight_dispatch` catches it → `dogfight.dispatch.rejected`. The point: the can't-seat path is observably loud, never a silent fall-through.)

- [ ] **Step 4: Run the full dogfight + intent-router suites (no regression)**

```bash
cd sidequest-server && uv run pytest tests/server/test_dogfight_force_dispatch_wiring.py tests/server/test_intent_router_dogfight_force_dispatch.py tests/server/dispatch/test_dogfight_husk_no_resurrect.py tests/agents/test_dogfight_shot_replay_narration_anchor.py tests/agents/subsystems/test_dogfight_dispatch_wiring.py -n0 -q
```
Expected: PASS, except failures already pre-existing on `develop` (verify against `develop` before attributing here).

- [ ] **Step 5: Lint + commit**

```bash
cd sidequest-server && uv run ruff check tests/server/test_dogfight_force_dispatch_wiring.py
git add tests/server/test_dogfight_force_dispatch_wiring.py
git commit -m "test(dogfight): wiring — router-missed dogfight force-dispatches, seats, and emits spans; degrades loud (158-29, ADR-153)"
```

---

## Self-Review

**Spec coverage (against ADR-153 §7):**
- "When the router matches dogfight verbs, it must dispatch the dogfight seater… never leave the narrator to grind the SDK tool loop into a max_turns crash" (158-29) → Task 1 (force-dispatch injector + wiring into the pass) + Task 4 (e2e seats-and-resolves on OTEL). Loud degradation reuses the existing `run_dogfight_dispatch` `dogfight.dispatch.rejected` span → Task 4 Step 3.
- "continued_same_region_drift must carry over only a LIVE encounter; never re-attach a resolved/husk_reaped encounter; respect the created_turn fresh-this-turn exemption" (158-30) → Task 2 (husk-reaped-this-turn marker + seater re-seat guard, keyed by turn so a fresh dogfight on a later turn still seats). The re-seat is the resurrection vector (the drift continue-ladder is already `not resolved`-gated at `narration_apply.py:4838`); blocking the re-seat stops the drift keep-alive from ever seeing a resurrected encounter.
- "Dice-replay / dogfight-shot re-entry narrates the resolved beat, not the prior turn's text" (158-35) → Task 3 (`[DOGFIGHT_SHOT_RESOLVED]` narrator anchor folding `enc.narrator_hints`).
- §8 OTEL: `dogfight.forced_dispatch` (new, Task 1), `dogfight.dispatch` / `dogfight.dispatch.rejected` (existing, asserted in Task 4), `reseat_refused_husk_reaped` watcher event (Task 2). Every Plan 2 decision is observable.

**Out of scope (by ADR / story boundary):** the general "narrator max_turns must degrade, not wedge the session" robustness fix → 158-41 (do not touch the SDK loop / `disconnect_save`). The opponent brain → Plan 3 (158-39). The full relative-position state graph → Plan 4 (158-40). The firewall + frame-default seating → Plan 1 (158-31/158-34), a **prerequisite** of this plan.

**Placeholder scan:** Three bounded "confirm the real name from Step 1 / read the fixtures module" notes (Tasks 1/2/3 fixture factories; Task 3 Step 1 directive-builder location; the `GameSnapshot` field idiom) are *located* reads (one fixtures module, one model class, one directive function), flagged inline per the writing-plans allowance — not open TODOs. They exist because the exact narrator-prompt assembly seam (Task 3) and the dogfight fixture factory names are confirmed at implementation time, not guessed.

**Type consistency:** `force_dispatch_dogfight_on_verb_miss(package, *, snapshot, pack, action, player_name) -> bool` is referenced identically in Task 1 (def + test) and Task 4 (wiring, via the pass). `SubsystemDispatch(subsystem="dogfight", params={"type": ...})` matches `dispatch.py:106` + the `run_dogfight_dispatch` reader (`dogfight.py:101`, `dispatch.params.get("type")`). `_resolve_dogfight_type(pack) -> str | None` matches `dogfight.py:58`. `reap_resolved_encounter_husk(snapshot, *, is_dice_replay, turn) -> bool` and `instantiate_encounter_from_trigger(*, snapshot, pack, encounter_type, player_name, npcs_present, genre_slug, ...)` match the extracted signatures (`encounter_lifecycle.py:142` / `:1486`). `snapshot.husk_reaped_this_turn: tuple[str, int] | None` is set in Task 2 Step 4 and read in Step 5 with the same `(type, turn)` shape. `encounter.narrator_hints: list[str]` matches the `dice_throw.py:288` writer.
