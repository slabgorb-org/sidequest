# Dogfight Rebuild — Plan 1: Firewall + Opponent Seating Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make a seated `space_opera` dogfight resolve correctly through the bound SWN engine by removing the native energy-dial graft from the content def and seating a ship/chassis opponent (never a co-located ground creature) — resolving playtest findings 158-31 (mechanically inert / hollow dial) and 158-34 (ground creature seated as the enemy ship).

**Architecture:** Per [ADR-153](../../adr/153-ace-of-aces-dogfight-positioning-swn-resolution.md), the dogfight is an Ace-of-Aces positioning subsystem feeding bound SWN resolution, with a firewall: positioning emits geometry + `gun_solution` only; SWN owns hull/hit/kill; **win = `hp_depletion`**. The resolution machinery already exists (`resolve_dogfight_shots` → `check_hp_depletion`; `_seed_combat_hp_depletion_to_npcs` seeds the opponent frame). This plan makes the content def internally consistent and closes the one seating gap that lets a personal-scale creature stand in for the enemy ship.

**Tech Stack:** Python 3.12 / pydantic v2 / FastAPI WebSocket (sidequest-server), YAML genre packs (sidequest-content), pytest + pytest-xdist (`uv run pytest`, `-n auto` default; `-n0` for serial), OpenTelemetry spans.

## Global Constraints

- **No silent fallbacks / no stubs** (CLAUDE.md). Every failure to seat or resolve fails loud and observably (OTEL span + log).
- **The firewall is doctrine** (ADR-153 §2): the dogfight path never calls `apply_beat` and never touches a dial. Positioning emits geometry + `gun_solution` + to-hit modifier only; SWN owns hull/hit/kill.
- **Bind the Ruleset, Don't Balance It** (SOUL.md / ADR-143): do not reintroduce or tune a native dial/beat mechanic on the dogfight path.
- **Branching:** both `sidequest-content` and `sidequest-server` target `develop` (github-flow). Feature branch `feat/dogfight-rebuild-firewall` in each.
- **OTEL is the lie detector** (CLAUDE.md): a seated dogfight that resolves must emit `encounter.resolved` with `source=hp_depletion`; assert on spans, never on source text.
- **No content in unit tests** (project rule `feedback_no_content_in_unit_tests`): pytest constructs synthetic fixtures; content invariants (the live pack's dogfight def shape) belong in the pack validator, not pytest.

---

## Task 1: Content — make the dogfight def internally consistent (firewall)

Rewrite the `space_opera` `dogfight` ConfrontationDef so it resolves via SWN HP, not a native energy dial. Remove `win_condition: dial_threshold`, the `player_metric`/`opponent_metric` energy dials, and the vestigial native `beats:` list. Keep `resolution_mode: sealed_letter_lookup`, the SWN frame stats (`opponent_default_stats`/`player_default_stats`), `geometry_modifiers`, and the weapons.

**Files:**
- Modify: `sidequest-content/genre_packs/space_opera/rules.yaml` (the `- type: dogfight` ConfrontationDef)
- Verify: `sidequest-content/genre_packs/space_opera/dogfight/interactions_mvp.yaml`, `interactions_tail_chase.yaml`

- [ ] **Step 1: Branch the content repo**

```bash
cd sidequest-content && git checkout develop && git pull && git checkout -b feat/dogfight-rebuild-firewall
```

- [ ] **Step 2: Confirm the player maneuver menu does NOT come from `beats:` before deleting them**

The sealed-letter resolver maps the player's committed selection (`sel.beat_id`) to a role; the legal *maneuver menu* must come from the interaction table's `maneuvers_consumed` (or `maneuvers_mvp.yaml`), not the def's `beats:` list. Confirm this is a bounded, located read — do NOT delete `beats:` until confirmed:

```bash
cd /Users/slabgorb/Projects/oq-3/sidequest-server && grep -rn "maneuvers_consumed\|available_maneuvers\|maneuver_menu\|\.beats" sidequest/agents/encounter_render.py sidequest/server/dispatch/sealed_letter.py sidequest/agents/orchestrator.py | head -30
```
Expected: the maneuver options surfaced to the player derive from the interaction table / `maneuvers_consumed`, not `cdef.beats`. If — and only if — a code path builds the dogfight maneuver menu from `cdef.beats`, STOP and convert that path to read `maneuvers_consumed` first (out of scope here; raise it), then return. Otherwise proceed: `beats:` is the vestigial native graft and is safe to remove.

- [ ] **Step 3: Rewrite the dogfight def**

In `genre_packs/space_opera/rules.yaml`, the `- type: dogfight` block. Set `win_condition: hp_depletion` and DELETE the `player_metric:`, `opponent_metric:`, and `beats:` blocks. The block should read (preserving the existing `intent_verbs`, frame stats, `geometry_modifiers`, and weapon ids):

```yaml
  - type: dogfight
    label: Fighter Duel
    # Spec 2026-05-20 confrontation-intent-validator
    intent_verbs: [dogfight, intercept, pursue, engage, lock, missile, gun]
    on_intent_mismatch: reprompt
    category: combat
    resolution_mode: sealed_letter_lookup
    # ADR-153: Ace of Aces positioning feeds bound SWN resolution. The maneuver
    # cross-product (interactions_*.yaml) is POSITIONING ONLY; SWN owns hull/hit/
    # kill. Win = hp_depletion on the strike-fighter frame HP. NO native dial:
    # the energy metrics + beats that used to live here were the
    # Bind-the-Ruleset doctrine violation (SOUL.md / ADR-143) and are removed.
    win_condition: hp_depletion
    opponent_weapon: multifocal_laser
    player_weapon: multifocal_laser
    opponent_default_stats:
      Physique: 10
      Reflex: 10
      Intellect: 10
      Cunning: 10
      Resolve: 10
      # SWN strike-fighter frame + gunnery (reserved combat-seed keys)
      hp: 8
      armor_class: 16
      armor: 5
      dexterity: 12
      pilot_skill: 1
      attack_bonus: 1
    player_default_stats:
      hp: 8
      armor_class: 16
      armor: 5
      pilot_skill: 0
      attack_bonus: 0
    geometry_modifiers:
      aspect:
        tail_on: 2
        quartering: 1
        crossing: -1
        head_on: -2
      range:
        gun: 2
        close: 0
        medium: -2
        far: -4
```

- [ ] **Step 4: Confirm the interaction tables carry no residual damage keys**

The `InteractionCell`/`InteractionTable` models carry no damage fields (geometry + `gun_solution` only). Confirm the YAML has no stray damage keys left from ADR-077's MVP:

```bash
cd sidequest-content && grep -n "hit_severity\|damage_increments\|starting_hull" genre_packs/space_opera/dogfight/interactions_mvp.yaml genre_packs/space_opera/dogfight/interactions_tail_chase.yaml
```
Expected: no output. (If any appear, delete those lines — cells carry geometry + `gun_solution` only, per the firewall.)

- [ ] **Step 5: Validate the pack loads with the new def shape**

From the server repo, load the pack and assert the dogfight def resolves to the SWN-HP shape:

```bash
cd /Users/slabgorb/Projects/oq-3/sidequest-server && SIDEQUEST_GENRE_PACKS=../sidequest-content/genre_packs \
  uv run python -c "
from sidequest.genre.loader import load_genre_pack
p = load_genre_pack('space_opera')
d = next(c for c in p.rules.confrontations if c.confrontation_type=='dogfight')
print('resolution_mode', d.resolution_mode)
print('win_condition', d.win_condition)
print('player_metric', d.player_metric)
print('opponent_metric', d.opponent_metric)
print('beats', d.beats)
print('opponent_hp', d.opponent_hp, 'opponent_ac', d.opponent_armor_class)
assert str(d.resolution_mode)=='sealed_letter_lookup'
assert str(d.win_condition)=='hp_depletion'
assert d.player_metric is None and d.opponent_metric is None
assert d.beats == []
assert d.opponent_hp == 8 and d.opponent_armor_class == 16
print('OK')
"
```
Expected: ends with `OK`. (Confirm the loader entrypoint name with `grep -rn "def load_genre_pack\|def load_pack" sidequest/genre/loader.py` if the import errors.) The `opponent_hp`/`opponent_armor_class` accessors read `opponent_default_stats["hp"]`/`["armor_class"]`.

- [ ] **Step 6: Commit (content repo)**

```bash
cd sidequest-content && git add genre_packs/space_opera/rules.yaml genre_packs/space_opera/dogfight/
git commit -m "feat(space_opera): dogfight resolves via SWN hp_depletion — drop native energy dial + beats (ADR-153)"
```

---

## Task 2: Server — treat `sealed_letter_lookup` as ship-scale so the personal-creature fallback can't seat the enemy ship

Finding 158-34: a ship dogfight bound a co-located Monster-Manual *ground* creature ("Gengineered Killer") as the enemy vessel, because the seater's location fallback fires for any type not in `_SHIP_SCALE_CONFRONTATION_TYPES` (which holds only `{"ship_combat"}`). A sealed-letter dogfight is inherently ship-scale: its opponent is a ship/chassis sourced from the def's frame or a router-named contact (Task 3), never the player's co-located crew or an ambient ground creature.

**Files:**
- Modify: `sidequest-server/sidequest/server/dispatch/encounter_lifecycle.py:1719` (the location-fallback gate)
- Test: `sidequest-server/tests/server/dispatch/test_dogfight_seating_scale.py`

**Interfaces:**
- Consumes: `ResolutionMode.sealed_letter_lookup` (`sidequest.genre.models.rules`), `instantiate_encounter_from_trigger(...)` (`sidequest.server.dispatch.encounter_lifecycle`).
- Produces: behavior — a `sealed_letter_lookup` dogfight never seats a co-located personal creature via the location fallback.

- [ ] **Step 1: Branch the server repo**

```bash
cd sidequest-server && git checkout develop && git pull && git checkout -b feat/dogfight-rebuild-firewall
```

- [ ] **Step 2: Write the failing test**

Create `sidequest-server/tests/server/dispatch/test_dogfight_seating_scale.py`. It builds a synthetic snapshot with a co-located hostile *ground* creature, dispatches a sealed-letter dogfight with no named opponent, and asserts that creature is NOT seated as the dogfight opponent. (Construct the synthetic pack/snapshot the same way `tests/fixtures/dogfight_playtest_encounter.py` does — import its helpers; adjust kwargs to the current constructors if they drifted.)

```python
import pytest

from sidequest.genre.models.rules import ResolutionMode
from sidequest.server.dispatch.encounter_lifecycle import (
    instantiate_encounter_from_trigger,
    NoOpponentAvailableError,
    SealedLetterArityError,
)
from tests.fixtures.dogfight_playtest_encounter import (
    make_dogfight_pack,        # synthetic space_opera-shaped pack w/ a sealed_letter dogfight def
    make_snapshot_with_npc,    # snapshot helper; seats one PC + the given NPCs at a location
)


def test_sealed_letter_dogfight_does_not_seat_colocated_ground_creature():
    # A hostile PERSONAL-scale creature shares the scene (the 158-34 "Gengineered
    # Killer"). A ship dogfight must NOT conscript it as the enemy vessel.
    pack = make_dogfight_pack()
    snapshot = make_snapshot_with_npc(
        pc_name="Pilot",
        npcs=[("Gengineered Killer", {"role": "hostile", "is_creature": True})],
    )
    with pytest.raises((NoOpponentAvailableError, SealedLetterArityError)):
        instantiate_encounter_from_trigger(
            snapshot=snapshot,
            pack=pack,
            encounter_type="dogfight",
            player_name="Pilot",
            npcs_present=[],          # router named no opponent
            genre_slug="space_opera",
        )
    # The ground creature was never seated as the blue (opponent) actor.
    assert snapshot.encounter is None
```

(If `make_dogfight_pack`/`make_snapshot_with_npc` don't exist with these names, read `tests/fixtures/dogfight_playtest_encounter.py` and use/extend its actual factory functions. The assertion that matters: the co-located ground creature is not seated as the dogfight opponent.)

- [ ] **Step 3: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_dogfight_seating_scale.py -v -n0`
Expected: FAIL — today the location fallback seats the ground creature as the opponent (no raise; `snapshot.encounter` is non-None with the creature as blue).

- [ ] **Step 4: Make `sealed_letter_lookup` ship-scale at the fallback gate**

In `sidequest/server/dispatch/encounter_lifecycle.py`, the `elif` at line 1719 currently reads:

```python
    elif not npcs_present and cdef.confrontation_type not in _SHIP_SCALE_CONFRONTATION_TYPES:
```

Change it so a sealed-letter (dogfight) confrontation also skips the personal-NPC location fallback — its opponent comes from the def frame (Task 3) or a router-named contact, never the ambient location grab:

```python
    elif (
        not npcs_present
        and cdef.confrontation_type not in _SHIP_SCALE_CONFRONTATION_TYPES
        # ADR-153: a sealed-letter dogfight is ship-scale — its Other is a
        # ship/chassis from the def frame or a router-named contact, never the
        # personal-scale location fallback (158-34: a ground creature was
        # conscripted as the enemy vessel). Story 59-17 enabled the fallback for
        # sealed-letter to let a dogfight seat at all; Task 3 replaces that with
        # a default-from-frame opponent, which is the correct ship-scale source.
        and cdef.resolution_mode != ResolutionMode.sealed_letter_lookup
    ):
```

Confirm `ResolutionMode` is imported at the top of `encounter_lifecycle.py` (it is used elsewhere — `grep -n "ResolutionMode" sidequest/server/dispatch/encounter_lifecycle.py`); add the import if absent.

- [ ] **Step 5: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_dogfight_seating_scale.py -v -n0`
Expected: PASS — with the fallback skipped and no named opponent, the No-Opponent / arity guard raises (the ground creature is never seated). Task 3 then makes the dogfight seat a real ship opponent instead of raising.

- [ ] **Step 6: Commit**

```bash
cd sidequest-server && git add sidequest/server/dispatch/encounter_lifecycle.py tests/server/dispatch/test_dogfight_seating_scale.py
git commit -m "fix(dogfight): sealed-letter is ship-scale — never seat a personal location-fallback creature (158-34, ADR-153)"
```

---

## Task 3: Server — seat a default ship opponent from the def frame when a dogfight names no Other

A dogfight requires an Other (ADR-116). After Task 2, a dogfight with no router-named contact raises instead of grabbing a creature. Per ADR-153 §6, source the opponent from the def's `opponent_default_stats` frame: synthesize a default enemy fighter so the duel always seats a ship — its hull/AC then come from the existing `_seed_combat_hp_depletion_to_npcs` path.

**Files:**
- Modify: `sidequest-server/sidequest/server/dispatch/encounter_lifecycle.py` (in `instantiate_encounter_from_trigger`, the ship-scale + no-materialized-threat branch around lines 1718–1734)
- Test: `sidequest-server/tests/server/dispatch/test_dogfight_default_opponent.py`

**Interfaces:**
- Consumes: `cdef.opponent_default_stats` / `cdef.opponent_hp` / `cdef.opponent_armor_class`, `NpcMention` (`sidequest.agents.orchestrator`), `_seed_combat_hp_depletion_to_npcs`.
- Produces: behavior — a ship-scale dogfight with no named/located Other seats one opponent-side actor whose backing core HP equals `opponent_default_stats["hp"]`.

- [ ] **Step 1: Write the failing test**

Create `sidequest-server/tests/server/dispatch/test_dogfight_default_opponent.py`:

```python
from sidequest.server.dispatch.encounter_lifecycle import instantiate_encounter_from_trigger
from tests.fixtures.dogfight_playtest_encounter import make_dogfight_pack, make_empty_snapshot


def test_dogfight_seats_default_ship_opponent_from_frame_when_none_named():
    # No router-named opponent, no co-located Other: the dogfight still seats an
    # enemy ship sourced from the def frame (ADR-116 + ADR-153 §6).
    pack = make_dogfight_pack()           # dogfight def: opponent_default_stats.hp == 8
    snapshot = make_empty_snapshot(pc_name="Pilot")

    enc = instantiate_encounter_from_trigger(
        snapshot=snapshot,
        pack=pack,
        encounter_type="dogfight",
        player_name="Pilot",
        npcs_present=[],
        genre_slug="space_opera",
    )

    assert enc is not None
    opponents = [a for a in enc.actors if a.side == "opponent"]
    assert len(opponents) == 1
    # The seated opponent's backing core HP came from the def frame.
    core = snapshot.find_creature_core(opponents[0].name)
    assert core is not None
    assert core.hp.max == 8
```

(Use the actual fixture factory names from `tests/fixtures/dogfight_playtest_encounter.py`; add `make_empty_snapshot` there if it doesn't exist — a snapshot with the PC seated and no NPCs.)

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_dogfight_default_opponent.py -v -n0`
Expected: FAIL — after Task 2 the no-named-opponent path raises (no Other seated), so `instantiate_encounter_from_trigger` raises instead of returning an encounter.

- [ ] **Step 3: Synthesize the default opponent from the frame**

In `sidequest/server/dispatch/encounter_lifecycle.py`, replace the fall-through comment block after the fallback `elif` (currently lines 1731–1733: "ship-scale + no materialized threat: leave npcs_present empty so the No-Opponent guard below fails loud") with a default-from-frame seat for sealed-letter dogfights:

```python
    elif (
        not npcs_present
        and cdef.resolution_mode == ResolutionMode.sealed_letter_lookup
        and cdef.opponent_default_stats
    ):
        # ADR-153 §6: a sealed-letter dogfight with no router-named contact and
        # no located Other still requires an enemy ship (ADR-116). Source it from
        # the def frame: a generic enemy fighter whose hull/AC come from
        # opponent_default_stats via _seed_combat_hp_depletion_to_npcs downstream.
        # This is the ship-scale replacement for Story 59-17's personal location
        # fallback (removed for sealed-letter in Task 2). Marked materialized so the
        # participant.joined span records a frame-default seat, not a roster one.
        from sidequest.agents.orchestrator import NpcMention as _NpcMention

        seating_source = "frame_default"
        npcs_present = [
            _NpcMention(
                name=cdef.label or "Enemy Fighter",
                role="hostile",
                side="opponent",
            )
        ]
    # else (non-sealed-letter ship-scale + no materialized threat): leave
    # npcs_present empty so the No-Opponent guard below fails loud — a crewed ship
    # fight needs an enemy ship, and the player's own crew are never it.
```

(Place this `elif` AFTER the existing `elif not npcs_present and ... resolution_mode != sealed_letter_lookup` from Task 2, BEFORE the No-Opponent guard. The downstream `_seed_combat_hp_depletion_to_npcs` mints the backing `Npc` core from `opponent_default_stats` for an opponent actor lacking an `Npc` — its existing "minted stub" branch — so the frame HP/AC reach the duel.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_dogfight_default_opponent.py -v -n0`
Expected: PASS — one opponent actor seated, backing core HP `max == 8` from the frame.

- [ ] **Step 5: Re-run Task 2's test (no regression)**

Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_dogfight_seating_scale.py -v -n0`
Expected: Reconsider the Task 2 assertion in light of Task 3. With a default-from-frame opponent, a dogfight with a co-located ground creature now seats the FRAME opponent (not the creature) instead of raising. Update `test_dogfight_seating_scale.py` so the invariant is "the ground creature is not the seated opponent" rather than "raises":

```python
    enc = instantiate_encounter_from_trigger(
        snapshot=snapshot, pack=pack, encounter_type="dogfight",
        player_name="Pilot", npcs_present=[], genre_slug="space_opera",
    )
    opponents = [a for a in enc.actors if a.side == "opponent"]
    assert len(opponents) == 1
    assert opponents[0].name != "Gengineered Killer"   # the ground creature was NOT conscripted
```
Run both seating tests: `uv run pytest tests/server/dispatch/test_dogfight_seating_scale.py tests/server/dispatch/test_dogfight_default_opponent.py -v -n0`
Expected: PASS (both).

- [ ] **Step 6: Commit**

```bash
cd sidequest-server && git add sidequest/server/dispatch/encounter_lifecycle.py tests/server/dispatch/test_dogfight_seating_scale.py tests/server/dispatch/test_dogfight_default_opponent.py
git commit -m "feat(dogfight): seat default ship opponent from def frame when none named (ADR-116/153)"
```

---

## Task 4: Server — end-to-end wiring test: a seated dogfight resolves via SWN hp_depletion

CLAUDE.md mandates a wiring test that drives the production path and asserts on OTEL, not source text. Prove the firewall: a seated dogfight where an NPC gun solution ablates the PC frame HP to 0 resolves via `hp_depletion`, and the `encounter.resolved` span fires with `source="hp_depletion"` — never `dial_threshold_sweep` or a `resolution_beat`.

**Files:**
- Test: `sidequest-server/tests/server/dispatch/test_dogfight_hp_depletion_wiring.py`

**Interfaces:**
- Consumes: `resolve_dogfight_shots` (`sidequest.game.dogfight_shot`), `GunSolution` (`sidequest.server.dispatch.sealed_letter`), `frame_hp_resolver` (`sidequest.server.narration_apply`), the in-memory span exporter fixture.

- [ ] **Step 1: Write the failing/forcing test**

Create `sidequest-server/tests/server/dispatch/test_dogfight_hp_depletion_wiring.py`. Build a seated dogfight encounter with the PC frame at 1 HP and an NPC gun solution that hits; resolve shots; assert the encounter resolves via `hp_depletion` and the span fired. (Reuse the span-capture fixture other telemetry tests use — find it with `grep -rln "InMemorySpanExporter\|span_exporter\|get_finished_spans" tests/`.)

```python
from sidequest.game.dogfight_shot import resolve_dogfight_shots
from sidequest.server.dispatch.sealed_letter import GunSolution
from sidequest.game.ruleset.resolution import AttackRollParams
from sidequest.genre.models.inventory import DamageSpec
from tests.fixtures.dogfight_playtest_encounter import (
    make_seated_dogfight,     # returns (encounter, edge_resolver) with PC+NPC frames seated
)


def test_dogfight_resolves_via_hp_depletion(span_exporter):
    # PC frame at 1 HP; NPC has a guaranteed-hit gun solution -> hull to <=0 ->
    # hp_depletion resolves the duel (NOT a dial or a resolution_beat).
    enc, edge_resolver = make_seated_dogfight(pc_hp=1, npc_hp=8)
    npc_role = next(a.role for a in enc.actors if a.side == "opponent")
    pc_name = next(a.name for a in enc.actors if a.side == "player")

    gs = GunSolution(
        shooter_role=npc_role,
        shooter_name=next(a.name for a in enc.actors if a.side == "opponent"),
        target_role=next(a.role for a in enc.actors if a.side == "player"),
        target_name=pc_name,
        attack=AttackRollParams(modifier=10, target_number=0),  # always hits
        weapon=DamageSpec(dice="1d4", armor_piercing=20),
        weapon_name="multifocal laser",
        target_armor=0,
        geometry_modifier=0,
    )

    res = resolve_dogfight_shots(
        encounter=enc,
        gun_solutions=[gs],
        d20_by_shooter={npc_role: 20},
        edge_resolver=edge_resolver,
    )

    assert res.depletion is not None
    assert enc.resolved is True
    assert enc.outcome == "opponent_victory"

    spans = span_exporter.get_finished_spans()
    resolved = [s for s in spans if s.name.endswith("encounter.resolved") or s.name == "encounter.resolved"]
    assert resolved, "encounter.resolved span must fire"
    assert any(s.attributes.get("source") == "hp_depletion" for s in resolved)
    # Firewall: never resolved by a dial sweep or a resolution beat.
    assert all(s.attributes.get("source") != "dial_threshold_sweep" for s in resolved)
```

(Confirm the span name + `source` attribute against `sidequest/telemetry/spans/encounter.py` `encounter_resolved_span`. Add `make_seated_dogfight` to the fixtures module if absent — it seats one PC actor + one opponent actor with backing cores at the given HP and returns an `edge_resolver` mapping actor name → core, mirroring `frame_hp_resolver`.)

- [ ] **Step 2: Run the test**

Run: `cd sidequest-server && uv run pytest tests/server/dispatch/test_dogfight_hp_depletion_wiring.py -v -n0`
Expected: PASS — the firewall machinery already resolves via HP (this test locks it against regression). If it FAILS because `enc.outcome` differs or no span fired, that is a real wiring gap surfaced by the content change — fix the seam before proceeding (do not weaken the assertion).

- [ ] **Step 3: Run the full dogfight + encounter-lifecycle suites (no regression)**

Run serially to avoid the known OTEL span-count xdist deadlock (`project_server_test_otel_deadlock`):

```bash
cd sidequest-server && uv run pytest tests/server/dispatch tests/game/test_dogfight_shot_inputs.py tests/game/test_dogfight_shot_math.py tests/agents/subsystems/test_dogfight_dispatch_wiring.py -n0 -q
```
Expected: PASS, except any failures already pre-existing on `develop` (verify a suspected pre-existing failure against `develop` in the main checkout before attributing it to this change — `project_wwn_content_breaks_server_fixtures`).

- [ ] **Step 4: Lint**

```bash
cd sidequest-server && uv run ruff check sidequest/server/dispatch/encounter_lifecycle.py tests/server/dispatch/test_dogfight_seating_scale.py tests/server/dispatch/test_dogfight_default_opponent.py tests/server/dispatch/test_dogfight_hp_depletion_wiring.py
```
Expected: `All checks passed!`

- [ ] **Step 5: Commit**

```bash
cd sidequest-server && git add tests/server/dispatch/test_dogfight_hp_depletion_wiring.py
git commit -m "test(dogfight): wiring — seated dogfight resolves via hp_depletion (OTEL), firewall locked (ADR-153)"
```

---

## Task 5: Pack validator — assert the live dogfight def shape (content invariant)

Per `feedback_no_content_in_unit_tests`, the live pack's dogfight shape is a content invariant — it belongs in the pack validator, not pytest. Add a validator check that any `sealed_letter_lookup` combat confrontation resolves via `hp_depletion` and carries no native dial/beats (so the 158-31 contradiction can never reappear in content).

**Files:**
- Modify: the genre-pack validator (find it: `grep -rn "def validate" sidequest/cli/validate.py sidequest/genre/` — the pack/world validator entrypoint)
- Test: the validator's own unit test (synthetic packs only)

- [ ] **Step 1: Locate the validator and its severity model**

```bash
cd sidequest-server && grep -rn "def validate\|ValidationError\|severity\|add_error\|add_warning" sidequest/cli/validate.py | head -20
```
Expected: surfaces the validator entrypoint and how it reports errors/warnings. Note the function that iterates confrontation defs.

- [ ] **Step 2: Write the failing validator test (synthetic pack)**

In the validator's test module (e.g. `tests/cli/test_validate.py` — confirm path), add a synthetic pack whose `dogfight` def declares `resolution_mode: sealed_letter_lookup` + `win_condition: dial_threshold` (the 158-31 contradiction) and assert the validator flags it:

```python
def test_validator_rejects_sealed_letter_with_dial_win(make_pack):
    pack = make_pack(confrontations=[{
        "type": "dogfight", "label": "Fighter Duel", "category": "combat",
        "resolution_mode": "sealed_letter_lookup", "win_condition": "dial_threshold",
        "interaction_table": {"version": "1", "starting_state": "merge",
                              "cells": [{"pair": ["a", "b"], "red_view": {}, "blue_view": {}}]},
    }])
    errors = run_validator(pack)   # use the validator's actual entrypoint/return shape
    assert any("sealed_letter" in e and "hp_depletion" in e for e in errors)
```

(Adapt `make_pack`/`run_validator` to the validator's real fixtures + return shape found in Step 1.)

- [ ] **Step 3: Run to confirm it fails**

Run: `cd sidequest-server && uv run pytest tests/cli/test_validate.py -k sealed_letter -v -n0`
Expected: FAIL — no such check yet.

- [ ] **Step 4: Add the validator rule**

In the confrontation-def loop of the validator, add (matching the file's existing error-reporting idiom):

```python
        # ADR-153: a sealed-letter dogfight is bound-ruleset combat — it must
        # resolve via hp_depletion, never a native dial. Reject the 158-31
        # contradiction (sealed_letter_lookup + dial_threshold) at validation.
        if (
            str(cdef.resolution_mode) == "sealed_letter_lookup"
            and cdef.category == "combat"
            and str(cdef.win_condition) != "hp_depletion"
        ):
            errors.append(
                f"confrontation {cdef.confrontation_type!r}: sealed_letter_lookup "
                f"combat must use win_condition=hp_depletion (ADR-153 firewall), "
                f"got {cdef.win_condition!r}"
            )
```

- [ ] **Step 5: Run to confirm it passes; run the live pack through the validator**

```bash
cd sidequest-server && uv run pytest tests/cli/test_validate.py -k sealed_letter -v -n0
SIDEQUEST_GENRE_PACKS=../sidequest-content/genre_packs uv run python -m sidequest.cli.validate space_opera
```
Expected: unit test PASS; the live `space_opera` pack validates clean (Task 1 already made its dogfight `hp_depletion`).

- [ ] **Step 6: Commit**

```bash
cd sidequest-server && git add sidequest/cli/validate.py tests/cli/test_validate.py
git commit -m "feat(validate): reject sealed-letter combat that isn't hp_depletion (ADR-153 firewall)"
```

---

## Self-Review

**Spec coverage (against ADR-153):**
- §2 firewall (hp_depletion, drop native dial/beats) → Task 1 (content) + Task 4 (wiring proof) + Task 5 (validator guard).
- §6 opponent = ship/chassis, never co-located creature → Task 2 (ship-scale gate) + Task 3 (default-from-frame).
- §2 "cells carry geometry only" → Task 1 Step 4 (confirm no residual damage keys; the models already carry no damage fields).
- Findings 158-31 (inert/hollow dial) → Tasks 1+4. 158-34 (ground creature seated) → Tasks 2+3.
- **Out of scope for Plan 1 (deferred to later plans):** 158-30 (resurrect via drift) + 158-35 (narration desync) → Plan 2 (lifecycle/router, needs live repro). 158-29 (router decline → max_turns crash) → Plan 2 + the general narrator-robustness item. Opponent brain → Plan 3. Full state graph → Plan 4.

**Placeholder scan:** The two "confirm the fixture factory names / validator entrypoint" notes (Task 2/3/5) are bounded, located reads (one fixtures module, one validator file), not open TODOs — flagged inline per the skill's allowance.

**Type consistency:** `instantiate_encounter_from_trigger(... encounter_type, player_name, npcs_present, genre_slug ...)` matches the real signature (encounter_lifecycle.py:1486). `ResolutionMode.sealed_letter_lookup`, `cdef.opponent_hp`/`opponent_armor_class`, `resolve_dogfight_shots(encounter=, gun_solutions=, d20_by_shooter=, edge_resolver=)`, and `GunSolution(shooter_role, shooter_name, target_role, target_name, attack, weapon, weapon_name, target_armor, geometry_modifier)` all match the extracted current code.
