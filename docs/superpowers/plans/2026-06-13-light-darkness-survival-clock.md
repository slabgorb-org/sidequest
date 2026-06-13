# Light & Darkness — Generic Environmental Survival Clock — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Beneath Sünden's dark a *mechanism* — a tracked, per-beat-depleting `light` resource pool whose exhaustion applies a deterministic −2 penalty to every roll, killing by degrees (the failed find-the-rope-back roll) instead of by narrator improvisation.

**Architecture:** Light is a content-declared `ResourcePool`. A server-injected `environment_clock` dispatch burns it one unit per time-advancing turn in an unlit region (deterministic, not LLM-classified). Exhaustion applies a `Status` carrying a new `roll_modifier: int` field, which is summed into the roll modifier at the ruleset chokepoint (`attack_params`) and threaded into skill-check/save resolution. A confidence-gated relight intent consumes a torch charge and clears the penalty. The narrator is gaslit via the snapshot; the UI reads the pool reactively.

**Tech Stack:** Python 3 / FastAPI / pydantic v2 (server), YAML (content), React/TypeScript (ui). pytest, vitest.

---

## Scope reality vs. the approved spec (READ FIRST)

The 2026-06-13 design (`docs/superpowers/specs/2026-06-13-light-darkness-survival-clock-design.md`) is approved, but a pre-plan code audit found two of its "reuse" claims are actually "build":

- **§4 reuse claim "`init_resource_pools` upserts from the genre pack":** the method exists but has **zero production call sites** — resource pools are dead in live play (verified: 18 calls, all in tests). **Phase 1** wires it for the first time. This resurrects *all* declared pools (e.g. `tea_and_murder`'s `standing`); those declarations carry `decay_per_turn: 0.0`, so the side effect is benign, but it is a real cross-pack change — call it out at review.
- **§7 reuse claim "the dice/resolution layer already reads status effects":** `Status` has **no modifier field** and **no roll site reads statuses**. **Phase 2** adds `roll_modifier: int` to `Status` and wires it through every roll site. This is independently valuable (any future "−N on rolls" status — poisoned, blinded, frightened — reuses it).

**§6.1 firing mechanism** also differs from reality: there is no "exploration beat" taxonomy (`BeatKind` is confrontation-internal), and the precondition gate is snapshot-only/world-coarse. **Phase 3** implements the spec's *intent* (undodgeable, deterministic) via a **different mechanism**: a server-injected dispatch gated on time-advancing dispatch presence. This is a logged deviation from §6.1, honoring §2/§4's "deterministic, not narrator-judged" requirement.

**Phasing / story-split note.** Phases 1 and 2 are reusable infrastructure independent of light. If the team prefers, split them into their own sprint stories (`resource-pool production wiring`, `status roll-modifier`) ahead of the light-clock story (Phases 3–7). The phase boundaries below are drawn so that split is a clean cut — each phase is independently green.

---

## File Structure

### server (`sidequest-server`)
- **Modify** `sidequest/game/status.py` — add `roll_modifier: int = 0` to `Status`; add `status_roll_modifier(core)` helper.
- **Modify** `sidequest/game/ruleset/swn.py` — sum status modifier in `attack_params`; thread `character_core` into `check_params`/`save_params`.
- **Modify** `sidequest/game/ruleset/native.py` — sum status modifier in `attack_params`.
- **Modify** `sidequest/game/ruleset/base.py` (or wherever the `RulesetModule` protocol/ABC lives) — extend `check_params`/`save_params` signatures with optional `character_core`.
- **Modify** `sidequest/server/dispatch/check.py` — fetch acting `CreatureCore`, pass to `check_params`/`save_params`.
- **Modify** `sidequest/server/dispatch/dice.py` — CWN net-run hacking site: add status modifier.
- **Create** `sidequest/game/resource_wiring.py` — `wire_genre_resources(snapshot, pack)` helper (single chokepoint for Phase 1).
- **Modify** session-creation sites to call the helper (anchors in Phase 1).
- **Create** `sidequest/agents/subsystems/environment_clock.py` — the burn-tick + relight subsystem.
- **Modify** `sidequest/agents/subsystems/__init__.py` — register `environment_clock`.
- **Modify** `sidequest/server/intent_router_pass.py` — deterministic injection of the `environment_clock` dispatch.
- **Modify** `sidequest/agents/intent_router.py` — decomposer recognizes torch-lighting intent (Phase 4).
- **Modify** the narrator snapshot/gaslighting assembly — surface `light` pool + darkness status (Phase 7).

### content (`sidequest-content`)
- **Modify** `genre_packs/caverns_and_claudes/rules.yaml` — declare the `light` resource pool.
- **Modify** `genre_packs/caverns_and_claudes/worlds/beneath_sunden/cartography.yaml` — `lit:` flags per region.
- **Verify** `genre_packs/caverns_and_claudes/inventory.yaml` — torch items (already correct; no change).

### ui (`sidequest-ui`)
- **Modify** `src/types/payloads.ts` — `ResourcePoolPayload` already exists; add a `thresholds?` field if the gauge needs it.
- **Modify** `src/components/CharacterPanel.tsx` — light gauge (reuse `FolioEdgeTicks`) + "−2 in the dark" affordance.
- **Verify** `src/App.tsx` PARTY_STATUS handler already lifts `resources` into `partyResources` (it does) — confirm light flows through.

### Test Baseline (run BEFORE starting — record failures)

- [ ] **Step 0: Capture the green baseline**

Run (server):
```bash
cd sidequest-server && SIDEQUEST_DATABASE_URL=postgresql://$USER@localhost:5432/sidequest_test \
  SIDEQUEST_GENRE_PACKS=../sidequest-content/genre_packs uv run pytest -q
```
Record the pre-existing failure list. Per project memory: ~33 phantom `MissingDatabaseUrlError` appear without `SIDEQUEST_DATABASE_URL`; content calibration tests SKIP without `SIDEQUEST_GENRE_PACKS`. Any NEW failure later that is not on this baseline is a regression you own.

---

## PHASE 1 — Resource pools load in production (foundation)

**Why:** Without this, the `light` pool never materializes. Currently dead.

### Task 1.1: Resource-wiring helper

**Files:**
- Create: `sidequest-server/sidequest/game/resource_wiring.py`
- Test: `sidequest-server/tests/game/test_resource_wiring.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/game/test_resource_wiring.py
from sidequest.game.session import GameSnapshot
from sidequest.game.resource_wiring import wire_genre_resources


class _FakeRules:
    def __init__(self, resources):
        self.resources = resources


class _FakePack:
    def __init__(self, resources):
        self.rules = _FakeRules(resources)


def _decl(name, starting, mx):
    # ResourceDeclaration is a pydantic model; build via the real type.
    from sidequest.genre.models.rules import ResourceDeclaration

    return ResourceDeclaration(
        name=name, label=name.title(), min=0.0, max=mx,
        starting=starting, voluntary=False, decay_per_turn=0.0,
    )


def test_wire_populates_declared_pools():
    snap = GameSnapshot()
    pack = _FakePack([_decl("light", 0.0, 6.0)])
    wire_genre_resources(snap, pack)
    assert "light" in snap.resources
    assert snap.resources["light"].current == 0.0
    assert snap.resources["light"].max == 6.0


def test_wire_is_noop_without_pack_or_rules():
    snap = GameSnapshot()
    wire_genre_resources(snap, None)           # no pack
    wire_genre_resources(snap, _FakePack([]))  # empty declarations
    assert snap.resources == {}


def test_wire_preserves_existing_current_on_upsert():
    snap = GameSnapshot()
    pack = _FakePack([_decl("light", 6.0, 6.0)])
    wire_genre_resources(snap, pack)
    snap.resources["light"].current = 2.0  # mid-delve burn
    wire_genre_resources(snap, pack)        # reload
    assert snap.resources["light"].current == 2.0  # preserved, not reset to starting
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/game/test_resource_wiring.py -v`
Expected: FAIL — `ModuleNotFoundError: sidequest.game.resource_wiring`.

- [ ] **Step 3: Write minimal implementation**

```python
# sidequest/game/resource_wiring.py
"""Single chokepoint that materializes a genre pack's declared resource pools
into a snapshot. ADR-033 pools were dead in production before this (init_resource_pools
had no caller); this is the wiring. Idempotent — safe to call on create AND load."""

from __future__ import annotations

from typing import Any

from sidequest.game.session import GameSnapshot


def wire_genre_resources(snapshot: GameSnapshot, pack: Any | None) -> None:
    """Upsert the pack's RulesConfig.resources into snapshot.resources.

    No-op when pack/rules/resources are absent. Preserves existing ``current``
    on upsert (see GameSnapshot.init_resource_pools upsert semantics) so a
    reloaded mid-delve light value is not reset to ``starting``.
    """
    rules = getattr(pack, "rules", None)
    declarations = getattr(rules, "resources", None)
    if not declarations:
        return
    snapshot.init_resource_pools(declarations)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/game/test_resource_wiring.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add sidequest/game/resource_wiring.py tests/game/test_resource_wiring.py
git commit -m "feat(resources): production wiring helper for genre resource pools"
```

### Task 1.2: Call the helper at session-creation sites (the wiring test)

**Files:**
- Modify: `sidequest-server/sidequest/game/chargen_mixin.py` (near the `GameSnapshot(...)` construction, ~1340)
- Modify: `sidequest-server/sidequest/game/world_materialization.py` (`WorldBuilder.build`, ~239, after chapters applied)
- Modify: `sidequest-server/sidequest/server/handlers/connect.py` (~773)
- Test: `sidequest-server/tests/integration/test_resources_wired_on_session_create.py`

- [ ] **Step 1: Write the failing wiring/integration test**

This is the per-CLAUDE.md mandatory wiring test — it proves the helper is reachable from a real session-create path, not just unit-callable.

```python
# tests/integration/test_resources_wired_on_session_create.py
"""Wiring gate: a freshly materialized session for a pack that declares a
resource pool must have that pool populated — proving wire_genre_resources is
actually called in production, not just unit-tested."""
import pytest
from sidequest.game.world_materialization import WorldBuilder
from sidequest.genre.loader import load_genre_pack


@pytest.mark.integration
def test_caverns_world_build_populates_light_pool(tmp_path):
    pack = load_genre_pack("caverns_and_claudes")  # declares `light` after Phase 5
    builder = WorldBuilder(pack=pack, world_slug="beneath_sunden")
    snap = builder.build()
    assert "light" in snap.resources, "light pool not wired on world build"
```

NOTE: this test depends on Phase 5 declaring `light`. Until then, assert against a pool you add temporarily OR mark `xfail(reason="light declared in Phase 5")`. Prefer: land Phase 5's `rules.yaml` declaration FIRST if executing inline, or use a fixture pack. If using subagent-driven execution, reorder so the content declaration (Task 5.1) precedes this test's un-xfail.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && SIDEQUEST_GENRE_PACKS=../sidequest-content/genre_packs uv run pytest tests/integration/test_resources_wired_on_session_create.py -v`
Expected: FAIL — `light` not in `snap.resources` (helper not yet called).

- [ ] **Step 3: Add the call at each construction site**

In `world_materialization.py`, after the chapter-apply loop and before `return snap`:

```python
        snap.world_history = list(applicable)
        from sidequest.game.resource_wiring import wire_genre_resources
        wire_genre_resources(snap, self.pack)  # ADR-033 pools (was dead in prod)
        return snap
```

In `chargen_mixin.py` (first-chargen branch, after `materialized = GameSnapshot(...)` and pack is in scope as `sd.genre_pack`):

```python
        from sidequest.game.resource_wiring import wire_genre_resources
        wire_genre_resources(materialized, sd.genre_pack)
```

In `handlers/connect.py` (the `GameSnapshot(...)` build at ~773, with the bound pack in scope):

```python
        from sidequest.game.resource_wiring import wire_genre_resources
        wire_genre_resources(snap, pack)
```

(Place the import at module top per file convention if inline imports are discouraged there.)

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd sidequest-server && SIDEQUEST_GENRE_PACKS=../sidequest-content/genre_packs uv run pytest tests/integration/test_resources_wired_on_session_create.py -v`
Expected: PASS (after Phase 5's declaration is present).

- [ ] **Step 5: Full-suite regression check + commit**

Run the Step 0 command. Confirm no NEW failures vs baseline (watch packs that declare resources — they now load).
```bash
git add sidequest/game/world_materialization.py sidequest/game/chargen_mixin.py \
        sidequest/server/handlers/connect.py \
        tests/integration/test_resources_wired_on_session_create.py
git commit -m "feat(resources): wire genre resource pools at session-creation sites"
```

---

## PHASE 2 — Status carries a roll modifier; rolls read it (the teeth)

**Why:** §7's "−N flows into every roll for free" is false today. This builds the flow. Reusable for any future "−N on rolls" status.

### Task 2.1: `roll_modifier` field + aggregation helper

**Files:**
- Modify: `sidequest-server/sidequest/game/status.py`
- Test: `sidequest-server/tests/game/test_status_roll_modifier.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/game/test_status_roll_modifier.py
from sidequest.game.status import Status, StatusSeverity, status_roll_modifier


def _status(text, mod):
    return Status(text=text, severity=StatusSeverity.Wound, roll_modifier=mod)


def test_status_defaults_to_zero_modifier():
    s = Status(text="bruised", severity=StatusSeverity.Scratch)
    assert s.roll_modifier == 0


def test_status_roll_modifier_sums_active_statuses():
    class _Core:
        statuses = [_status("in the dark", -2), _status("blessed", 1)]
    assert status_roll_modifier(_Core()) == -1


def test_status_roll_modifier_none_and_empty():
    assert status_roll_modifier(None) == 0
    class _Empty:
        statuses = []
    assert status_roll_modifier(_Empty()) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/game/test_status_roll_modifier.py -v`
Expected: FAIL — `roll_modifier` is not a field (`extra="forbid"` rejects it) and `status_roll_modifier` does not exist.

- [ ] **Step 3: Implement**

In `sidequest/game/status.py`, add the field to `Status`:

```python
class Status(BaseModel):
    """An actor-level lingering cost."""
    model_config = {"extra": "forbid"}

    text: str
    severity: StatusSeverity
    absorbed_shifts: int = 0
    created_turn: int = 0
    created_in_encounter: str | None = None
    incapacitating: bool = False
    roll_modifier: int = 0  # -N/+N applied to ALL rolls while this status is active
```

Add the module-level helper:

```python
def status_roll_modifier(core: object | None) -> int:
    """Sum ``roll_modifier`` across all statuses on a creature core.

    0 when ``core`` is None or carries no statuses. Bonuses and penalties
    stack additively. This is the single aggregation point every roll site
    calls so status-driven modifiers cannot silently no-op at one site.
    """
    if core is None:
        return 0
    statuses = getattr(core, "statuses", None) or []
    return sum(int(getattr(s, "roll_modifier", 0)) for s in statuses)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/game/test_status_roll_modifier.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add sidequest/game/status.py tests/game/test_status_roll_modifier.py
git commit -m "feat(status): roll_modifier field + status_roll_modifier aggregation helper"
```

### Task 2.2: Attack rolls read the status modifier (SWN chokepoint + Native)

**Files:**
- Modify: `sidequest-server/sidequest/game/ruleset/swn.py` (`attack_params`, ~115-124)
- Modify: `sidequest-server/sidequest/game/ruleset/native.py` (`attack_params`, ~72-78)
- Test: `sidequest-server/tests/game/ruleset/test_attack_status_modifier.py`

WWN inherits SWN's `attack_params` unchanged, so this one edit covers SWN/CWN/AWN/WWN attacks and the WN sealed-round walk.

- [ ] **Step 1: Write the failing test**

```python
# tests/game/ruleset/test_attack_status_modifier.py
from sidequest.game.ruleset.swn import SwnRulesetModule
from sidequest.game.ruleset.native import NativeRulesetModule
from sidequest.game.status import Status, StatusSeverity
from sidequest.game.creature_core import CreatureCore


def _dark_core():
    core = CreatureCore(name="Delver")  # adjust required fields per CreatureCore ctor
    core.statuses.append(Status(text="in the dark", severity=StatusSeverity.Wound, roll_modifier=-2))
    return core


def _make_beat():
    # Build the minimal beat object attack_params reads (stat_check, combat_skill, attack_bonus).
    from sidequest.game.beat import Beat  # adjust to the real beat type used by attack_params
    return Beat(stat_check="str", combat_skill=0, attack_bonus=0)


def test_swn_attack_applies_darkness_penalty():
    ruleset = SwnRulesetModule()
    beat = _make_beat()
    stats = {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10}
    lit = ruleset.attack_params(beat=beat, attacker_stats=stats, attacker_core=CreatureCore(name="L"), target_core=None)
    dark = ruleset.attack_params(beat=beat, attacker_stats=stats, attacker_core=_dark_core(), target_core=None)
    assert dark.modifier == lit.modifier - 2


def test_native_attack_applies_darkness_penalty():
    ruleset = NativeRulesetModule()
    beat = _make_beat()
    stats = {"str": 10}
    lit = ruleset.attack_params(beat=beat, attacker_stats=stats, attacker_core=CreatureCore(name="L"), target_core=None)
    dark = ruleset.attack_params(beat=beat, attacker_stats=stats, attacker_core=_dark_core(), target_core=None)
    assert dark.modifier == lit.modifier - 2
```

(Adjust `CreatureCore`/`Beat` construction to the real required fields — read the models first. The assertion shape — `dark == lit - 2` — is the contract.)

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/game/ruleset/test_attack_status_modifier.py -v`
Expected: FAIL — `dark.modifier == lit.modifier` (status not read yet).

- [ ] **Step 3: Implement at both `attack_params`**

`swn.py`:
```python
    def attack_params(self, *, beat, attacker_stats, attacker_core, target_core):
        attr_mod = self.stat_modifier(attacker_stats, beat.stat_check)
        combat_skill = int(getattr(beat, "combat_skill", 0) or 0)
        attack_bonus = int(getattr(beat, "attack_bonus", 0) or 0)
        from sidequest.game.status import status_roll_modifier
        status_mod = status_roll_modifier(attacker_core)
        return AttackRollParams(
            modifier=attack_bonus + combat_skill + attr_mod + status_mod,
            target_number=self.offer_difficulty(beat=beat, target_core=target_core),
        )
```

`native.py`:
```python
    def attack_params(self, *, beat, attacker_stats, attacker_core, target_core):
        attr_mod = self.stat_modifier(attacker_stats, beat.stat_check)
        from sidequest.game.status import status_roll_modifier
        status_mod = status_roll_modifier(attacker_core)
        return AttackRollParams(
            modifier=attr_mod + status_mod,
            target_number=self.compute_dc(beat),
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/game/ruleset/test_attack_status_modifier.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add sidequest/game/ruleset/swn.py sidequest/game/ruleset/native.py \
        tests/game/ruleset/test_attack_status_modifier.py
git commit -m "feat(ruleset): attack rolls read status roll_modifier (SWN chokepoint + Native)"
```

### Task 2.3: Skill checks & saves read the status modifier

**Files:**
- Modify: `sidequest-server/sidequest/game/ruleset/base.py` (protocol/ABC `check_params`/`save_params` signatures — add `character_core=None`)
- Modify: `sidequest-server/sidequest/game/ruleset/swn.py` (`check_params` ~229-244, `save_params` ~246-269)
- Modify: `sidequest-server/sidequest/server/dispatch/check.py` (~71-98 — fetch core, pass it)
- Test: `sidequest-server/tests/game/ruleset/test_check_status_modifier.py`

This is the path that carries the marquee effect — the failed **find-the-rope-back** navigation/search roll.

- [ ] **Step 1: Write the failing test**

```python
# tests/game/ruleset/test_check_status_modifier.py
from sidequest.game.ruleset.swn import SwnRulesetModule
from sidequest.game.status import Status, StatusSeverity
from sidequest.game.creature_core import CreatureCore


def _dark_core():
    core = CreatureCore(name="Delver")
    core.statuses.append(Status(text="in the dark", severity=StatusSeverity.Wound, roll_modifier=-2))
    return core


def test_skill_check_applies_darkness_penalty():
    rs = SwnRulesetModule()
    stats = {"wis": 12}
    base = rs.check_params(stats=stats, attribute="wis", skill_level=1,
                           difficulty_key="normal", label="search", cfg=None,
                           character_core=CreatureCore(name="L"))
    dark = rs.check_params(stats=stats, attribute="wis", skill_level=1,
                           difficulty_key="normal", label="search", cfg=None,
                           character_core=_dark_core())
    assert dark.modifier == base.modifier - 2


def test_check_params_core_defaults_none():
    # back-compat: omitting character_core must not raise and yields no status mod
    rs = SwnRulesetModule()
    p = rs.check_params(stats={"wis": 12}, attribute="wis", skill_level=1,
                        difficulty_key="normal", label="search", cfg=None)
    assert isinstance(p.modifier, int)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/game/ruleset/test_check_status_modifier.py -v`
Expected: FAIL — `check_params` has no `character_core` kwarg (TypeError).

- [ ] **Step 3: Implement**

Add `character_core: object | None = None` to the `check_params` and `save_params` signatures in `base.py` (the protocol/abstract base) AND the SWN implementations. SWN `check_params`:

```python
    def check_params(self, *, stats, attribute, skill_level, difficulty_key, label, cfg,
                     character_core=None):
        attr_mod = self.stat_modifier(stats, attribute)
        from sidequest.game.status import status_roll_modifier
        return CheckRollParams(
            modifier=attr_mod + int(skill_level) + status_roll_modifier(character_core),
            ...  # preserve existing difficulty/label fields
        )
```

SWN `save_params` (and the CWN `"luck"` override in `wwn.py` if it computes a modifier — thread `character_core` through identically):

```python
    def save_params(self, *, stats, save, level, label, cfg, character_core=None):
        from sidequest.game.status import status_roll_modifier
        params = ...  # existing computation
        params.modifier += status_roll_modifier(character_core)
        return params
```

In `dispatch/check.py`, fetch the acting core and pass it (both the `skill_check` and `save` branches):

```python
    character_core = snapshot.find_creature_core(character_name)
    if kind == "skill_check":
        params = ruleset.check_params(stats=character_stats, attribute=attribute,
                                      skill_level=skill_level, difficulty_key=difficulty_key,
                                      label=label, cfg=cfg, character_core=character_core)
    elif kind == "save":
        params = ruleset.save_params(stats=character_stats, save=save, level=level,
                                     label=label, cfg=cfg, character_core=character_core)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/game/ruleset/test_check_status_modifier.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add sidequest/game/ruleset/base.py sidequest/game/ruleset/swn.py \
        sidequest/game/ruleset/wwn.py sidequest/server/dispatch/check.py \
        tests/game/ruleset/test_check_status_modifier.py
git commit -m "feat(ruleset): skill checks and saves read status roll_modifier"
```

### Task 2.4: CWN net-run hacking site reads the status modifier

**Files:**
- Modify: `sidequest-server/sidequest/server/dispatch/dice.py` (~487-499)
- Test: extend `sidequest-server/tests/server/dispatch/test_dice.py` (or the nearest existing hacking test)

- [ ] **Step 1: Write the failing test** — assert a dark hacker's net-run modifier is 2 lower than a lit hacker's, driving the real hacking branch (`cdef.category == "hacking"`). Mirror the existing hacking test fixture; add a `-2` status to the actor core and assert the resolved `modifier` drops by 2.

- [ ] **Step 2: Run** — Expected FAIL (inline modifier ignores statuses).

- [ ] **Step 3: Implement** at `dice.py:~489`:

```python
    int_mod = ruleset.stat_modifier(character_stats, beat.stat_check)
    program_skill = int(beat.combat_skill)
    from sidequest.game.status import status_roll_modifier
    attacker_core = snapshot.find_creature_core(character_name)
    modifier = int_mod + program_skill + status_roll_modifier(attacker_core)
```

- [ ] **Step 4: Run** — Expected PASS.

- [ ] **Step 5: Commit**

```bash
git add sidequest/server/dispatch/dice.py tests/server/dispatch/test_dice.py
git commit -m "feat(ruleset): CWN net-run hacking reads status roll_modifier"
```

---

## PHASE 3 — The deterministic burn tick (`environment_clock`)

**Why:** Burn `light` one unit per time-advancing turn in an unlit region; apply/clear the darkness penalty by reconciling against current state. Deterministic, OTEL-observable, undodgeable by phrasing.

### Task 3.1: The `environment_clock` subsystem (burn + reconcile)

**Files:**
- Create: `sidequest-server/sidequest/agents/subsystems/environment_clock.py`
- Modify: `sidequest-server/sidequest/agents/subsystems/__init__.py` (register)
- Test: `sidequest-server/tests/agents/subsystems/test_environment_clock.py`

Design decisions baked in (deviations from spec §6.1/§7 mechanism, same intent):
- Penalty is **state-reconciled** each tick, not crossing-edge: `light.current == 0` in an unlit region ⇒ ensure exactly one darkness `Status` present; otherwise ensure none. This handles the spec's §12 "starts unlit ⇒ −2 immediately" case (no downward crossing happens when you *begin* at 0) and is resume-safe/idempotent.
- The darkness status is identified by a sentinel `text` (`DARKNESS_STATUS_TEXT`) so reconcile can find/remove exactly its own status without touching combat wounds.

- [ ] **Step 1: Write the failing test**

```python
# tests/agents/subsystems/test_environment_clock.py
import pytest
from sidequest.game.session import GameSnapshot
from sidequest.game.resource_pool import ResourcePool, ResourceThreshold
from sidequest.agents.subsystems.environment_clock import (
    run_environment_clock_dispatch, DARKNESS_STATUS_TEXT, DARKNESS_PENALTY,
)
from sidequest.protocol.dispatch import SubsystemDispatch


def _snap_with_light(current, character_name="Delver"):
    snap = GameSnapshot()
    snap.resources["light"] = ResourcePool(
        name="light", label="Light", current=current, min=0.0, max=6.0,
        voluntary=False, decay_per_turn=0.0,
        thresholds=[
            ResourceThreshold(at=1.0, event_id="guttering", narrator_hint="the torch is dying"),
            ResourceThreshold(at=0.0, event_id="dark", narrator_hint="the dark closes in"),
        ],
    )
    # attach a controllable PC core named character_name (adjust to real chargen helper)
    return snap


def _dispatch(region="entrance", lit=False, character_name="Delver"):
    return SubsystemDispatch(
        subsystem="environment_clock",
        params={"region": region, "lit": lit, "character_name": character_name},
        idempotency_key="environment_clock_1",
        confidence=1.0,
    )


@pytest.mark.asyncio
async def test_burn_decrements_one_in_unlit_region():
    snap = _snap_with_light(6.0)
    out = await run_environment_clock_dispatch(_dispatch(lit=False), snapshot=snap)
    assert snap.resources["light"].current == 5.0
    assert out.data["burned"] is True


@pytest.mark.asyncio
async def test_no_burn_in_lit_region():
    snap = _snap_with_light(6.0)
    await run_environment_clock_dispatch(_dispatch(lit=True), snapshot=snap)
    assert snap.resources["light"].current == 6.0


@pytest.mark.asyncio
async def test_reaching_zero_applies_darkness_penalty_once():
    snap = _snap_with_light(1.0)
    await run_environment_clock_dispatch(_dispatch(lit=False), snapshot=snap)
    core = snap.find_creature_core("Delver")
    dark = [s for s in core.statuses if s.text == DARKNESS_STATUS_TEXT]
    assert len(dark) == 1
    assert dark[0].roll_modifier == DARKNESS_PENALTY  # -2
    # idempotent: a second tick at 0 does not stack a second penalty
    await run_environment_clock_dispatch(_dispatch(lit=False), snapshot=snap)
    dark = [s for s in core.statuses if s.text == DARKNESS_STATUS_TEXT]
    assert len(dark) == 1


@pytest.mark.asyncio
async def test_penalty_cleared_when_region_lit():
    snap = _snap_with_light(0.0)
    await run_environment_clock_dispatch(_dispatch(lit=False), snapshot=snap)  # applies -2
    await run_environment_clock_dispatch(_dispatch(lit=True), snapshot=snap)   # lit ⇒ clear
    core = snap.find_creature_core("Delver")
    assert not [s for s in core.statuses if s.text == DARKNESS_STATUS_TEXT]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/agents/subsystems/test_environment_clock.py -v`
Expected: FAIL — module does not exist.

- [ ] **Step 3: Implement the subsystem**

```python
# sidequest/agents/subsystems/environment_clock.py
"""environment_clock — deterministic per-beat survival-clock burn.

Server-injected (NOT LLM-decomposed) dispatch. Burns the ``light`` pool one
unit per time-advancing turn in an unlit region, and reconciles the darkness
penalty against current state. See docs/superpowers/specs/2026-06-13-light-
darkness-survival-clock-design.md. Mechanism deviates from spec §6.1 (no
exploration-beat taxonomy exists); intent (undodgeable, deterministic) preserved.
"""
from __future__ import annotations

from sidequest.agents.subsystems import SubsystemOutput
from sidequest.game.resource_pool import ResourcePatchOp
from sidequest.game.session import GameSnapshot
from sidequest.game.status import Status, StatusSeverity
from sidequest.protocol.dispatch import SubsystemDispatch

DARKNESS_STATUS_TEXT = "Plunged into darkness — every action is harder."
DARKNESS_PENALTY = -2  # spec §9 default N; tunable later via threshold metadata


def _ensure_darkness_penalty(core) -> bool:
    existing = [s for s in core.statuses if s.text == DARKNESS_STATUS_TEXT]
    if existing:
        return False
    core.statuses.append(
        Status(text=DARKNESS_STATUS_TEXT, severity=StatusSeverity.Wound,
               roll_modifier=DARKNESS_PENALTY)
    )
    return True


def _clear_darkness_penalty(core) -> bool:
    before = len(core.statuses)
    core.statuses[:] = [s for s in core.statuses if s.text != DARKNESS_STATUS_TEXT]
    return len(core.statuses) != before


async def run_environment_clock_dispatch(
    dispatch: SubsystemDispatch, *, snapshot: GameSnapshot,
) -> SubsystemOutput:
    pool = snapshot.resources.get("light")
    if pool is None:
        return SubsystemOutput(directives=[], data={"error": "no_light_pool"})

    lit = bool(dispatch.params.get("lit", False))
    region = dispatch.params.get("region", "")
    character_name = dispatch.params.get("character_name")
    core = snapshot.find_creature_core(character_name) if character_name else None

    data: dict = {"region": region, "lit": lit, "burned": False,
                  "light_current": pool.current, "crossed": None}

    if lit:
        # In a lit region: no burn; clear any darkness penalty.
        if core is not None and _clear_darkness_penalty(core):
            data["penalty_cleared"] = True
        return SubsystemOutput(directives=[], data=data)

    # Unlit region: burn one unit (clamped at min).
    result = pool._apply_and_clamp(ResourcePatchOp.Subtract, 1.0)
    data["burned"] = True
    data["light_current"] = result.new_value
    crossed = [t.event_id for t in result.crossed_thresholds]
    data["crossed"] = crossed or None

    directives = []
    # Reconcile penalty against state (handles start-at-0 with no crossing).
    if core is not None:
        if result.new_value <= pool.min:
            if _ensure_darkness_penalty(core):
                data["penalty_applied"] = True
        else:
            _clear_darkness_penalty(core)

    return SubsystemOutput(directives=directives, data=data)
```

Register in `subsystems/__init__.py`:
```python
from sidequest.agents.subsystems.environment_clock import run_environment_clock_dispatch
# inside _register_defaults / the _REGISTRY literal:
    "environment_clock": run_environment_clock_dispatch,
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/agents/subsystems/test_environment_clock.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add sidequest/agents/subsystems/environment_clock.py \
        sidequest/agents/subsystems/__init__.py \
        tests/agents/subsystems/test_environment_clock.py
git commit -m "feat(environment_clock): deterministic light-burn subsystem with state-reconciled darkness penalty"
```

### Task 3.2: Deterministic injection into the dispatch package

**Files:**
- Modify: `sidequest-server/sidequest/server/intent_router_pass.py` (after precondition gate, before `run_dispatch_bank`, ~671)
- Test: `sidequest-server/tests/server/test_environment_clock_injection.py`

Trigger rule: inject the tick iff (a) a `light` pool exists AND (b) the package contains ≥1 **time-advancing** dispatch. Time-advancing set = `{"movement", "confrontation"}` (conservative; widen via OTEL evidence per §12). This derives the signal from the router's own emission, not from re-judging phrasing.

- [ ] **Step 1: Write the failing test**

```python
# tests/server/test_environment_clock_injection.py
from sidequest.server.intent_router_pass import inject_environment_clock
from sidequest.protocol.dispatch import DispatchPackage, PlayerDispatch, SubsystemDispatch
from sidequest.game.session import GameSnapshot
from sidequest.game.resource_pool import ResourcePool


def _pkg(*subsystems):
    return DispatchPackage(
        turn_id="t1", confidence_global=1.0,
        per_player=[PlayerDispatch(
            player_id="p1", raw_action="x",
            dispatch=[SubsystemDispatch(subsystem=s, params={}, idempotency_key=f"k_{s}",
                                        confidence=1.0) for s in subsystems],
        )],
    )


def _snap_with_light():
    snap = GameSnapshot(current_region="entrance")
    snap.resources["light"] = ResourcePool(name="light", label="Light", current=6.0,
                                            min=0.0, max=6.0, voluntary=False, decay_per_turn=0.0)
    return snap


class _Region(dict):
    pass


class _Pack:
    class _World:
        class _Carto:
            regions = {"entrance": _Region(lit=False)}
        cartography = _Carto()
    worlds = {"beneath_sunden": _World()}


def test_injects_on_movement_turn():
    pkg, snap = _pkg("movement"), _snap_with_light()
    snap.world_slug = "beneath_sunden"
    inject_environment_clock(pkg, snap, _Pack())
    kinds = [d.subsystem for pd in pkg.per_player for d in pd.dispatch]
    assert "environment_clock" in kinds
    clock = next(d for pd in pkg.per_player for d in pd.dispatch if d.subsystem == "environment_clock")
    assert clock.params["lit"] is False
    assert clock.confidence == 1.0


def test_no_inject_on_pure_social_turn():
    pkg, snap = _pkg("npc_agency"), _snap_with_light()
    snap.world_slug = "beneath_sunden"
    inject_environment_clock(pkg, snap, _Pack())
    kinds = [d.subsystem for pd in pkg.per_player for d in pd.dispatch]
    assert "environment_clock" not in kinds


def test_no_inject_without_light_pool():
    pkg = _pkg("movement")
    snap = GameSnapshot(current_region="entrance", world_slug="beneath_sunden")
    inject_environment_clock(pkg, snap, _Pack())
    kinds = [d.subsystem for pd in pkg.per_player for d in pd.dispatch]
    assert "environment_clock" not in kinds
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/server/test_environment_clock_injection.py -v`
Expected: FAIL — `inject_environment_clock` does not exist.

- [ ] **Step 3: Implement the injector + call it**

Add to `intent_router_pass.py`:
```python
TIME_ADVANCING_SUBSYSTEMS = frozenset({"movement", "confrontation"})


def inject_environment_clock(package, snapshot, pack) -> None:
    """Deterministically append an environment_clock tick on time-advancing turns.

    Not LLM-emitted — derives the time-advancing signal from the router's own
    dispatch set so phrasing cannot dodge the burn. No-op when no light pool or
    no time-advancing dispatch is present.
    """
    if snapshot.resources.get("light") is None:
        return
    all_dispatches = [d for pd in package.per_player for d in pd.dispatch] + \
                     [d for ca in package.cross_player for d in ca.dispatch]
    if not any(d.subsystem in TIME_ADVANCING_SUBSYSTEMS for d in all_dispatches):
        return

    region_name = snapshot.current_region or ""
    lit = False
    world = (getattr(pack, "worlds", {}) or {}).get(getattr(snapshot, "world_slug", "") or "")
    carto = getattr(world, "cartography", None)
    region_obj = getattr(carto, "regions", {}).get(region_name) if carto else None
    if region_obj is not None:
        # Region model uses extra="allow"; lit may be attr or dict key.
        lit = bool(getattr(region_obj, "lit", None) if hasattr(region_obj, "lit")
                   else (region_obj.get("lit") if isinstance(region_obj, dict) else False))

    character_name = package.per_player[0].player_id if package.per_player else None
    clock = SubsystemDispatch(
        subsystem="environment_clock",
        params={"region": region_name, "lit": lit, "character_name": character_name},
        idempotency_key=f"environment_clock_{getattr(snapshot.turn_manager, 'interaction', 0)}",
        confidence=1.0,
    )
    if package.per_player:
        package.per_player[0].dispatch.append(clock)
```

At the call site (after `run_dispatch_precondition_gate`, before `run_dispatch_bank`):
```python
    package = run_dispatch_precondition_gate(package=package, snapshot=snapshot)
    inject_environment_clock(package, snapshot, pack)
    bank_result = await run_dispatch_bank(package, context={...})
```

NOTE: `character_name` must resolve to the acting PC's creature-core name. `player_id` may not equal the PC name; read how other subsystems map `player_name`→core in this pass and reuse that mapping rather than assuming. Fix the param to the value `snapshot.find_creature_core(...)` accepts.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/server/test_environment_clock_injection.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add sidequest/server/intent_router_pass.py tests/server/test_environment_clock_injection.py
git commit -m "feat(intent-router): deterministically inject environment_clock tick on time-advancing turns"
```

### Task 3.3: OTEL spans (the lie detector)

**Files:**
- Modify: `sidequest-server/sidequest/agents/subsystems/environment_clock.py`
- Modify: `sidequest-server/sidequest/telemetry/` span definitions (follow the existing subsystem-span pattern, e.g. how `intent_router.dispatch.gated` is emitted)
- Test: `sidequest-server/tests/agents/subsystems/test_environment_clock_otel.py`

Per the project OTEL principle: every subsystem decision emits a span. Emit `light.tick` (attrs: `light.current`, `light.max`, `region`, `lit`, `burned`, `crossed_threshold`, `penalty_applied`) on burn; the relight span `light.relit` is added in Phase 4.

- [ ] **Step 1: Write the failing test** — use the project's span-capture fixture (find how existing subsystem-span tests assert; per memory, the Without-Number wiring checklist requires OTEL span-assertion tests). Assert a `light.tick` span is emitted with `light.current` and `penalty_applied` attributes after a burn to zero.

- [ ] **Step 2: Run** — Expected FAIL (no span emitted).

- [ ] **Step 3: Implement** — wrap the burn body in the tracer span following the established subsystem pattern; set attributes from the `data` dict already assembled.

- [ ] **Step 4: Run** — Expected PASS.

- [ ] **Step 5: Commit**

```bash
git add sidequest/agents/subsystems/environment_clock.py sidequest/telemetry/ \
        tests/agents/subsystems/test_environment_clock_otel.py
git commit -m "feat(otel): light.tick span on environment_clock burn"
```

---

## PHASE 4 — Lighting a torch (intent / confidence-gated)

**Why:** §6.2 — deliberate light management is the meaningful resource decision. Consume a torch charge, set `light = max`, clear the penalty. Fail loudly when no torch remains.

### Task 4.1: Relight handling in the subsystem

**Files:**
- Modify: `sidequest-server/sidequest/agents/subsystems/environment_clock.py` (add a relight entry point or a `mode` param)
- Test: extend `tests/agents/subsystems/test_environment_clock.py`

Decision: handle relight as `params["mode"] == "relight"` within the same subsystem (cohesive — both touch the light pool + darkness status), distinguished from the burn tick (`mode` absent / `"burn"`).

- [ ] **Step 1: Write the failing test**

```python
@pytest.mark.asyncio
async def test_relight_sets_light_to_max_consumes_torch_and_clears_penalty():
    snap = _snap_with_light(0.0)  # dark
    await run_environment_clock_dispatch(_dispatch(lit=False), snapshot=snap)  # penalty on
    # give the PC a torch with one charge (adjust to real inventory model)
    _give_torch(snap, "Delver", charges=1)
    d = SubsystemDispatch(subsystem="environment_clock",
                          params={"mode": "relight", "character_name": "Delver"},
                          idempotency_key="environment_clock_relight_2", confidence=0.9)
    out = await run_environment_clock_dispatch(d, snapshot=snap)
    assert snap.resources["light"].current == snap.resources["light"].max
    core = snap.find_creature_core("Delver")
    assert not [s for s in core.statuses if s.text == DARKNESS_STATUS_TEXT]
    assert out.data["relit"] is True
    assert out.data["torch_charges_remaining"] == 0


@pytest.mark.asyncio
async def test_relight_fails_loudly_with_no_torch():
    snap = _snap_with_light(0.0)
    d = SubsystemDispatch(subsystem="environment_clock",
                          params={"mode": "relight", "character_name": "Delver"},
                          idempotency_key="environment_clock_relight_2", confidence=0.9)
    out = await run_environment_clock_dispatch(d, snapshot=snap)
    assert out.data["error"] == "no_torch"
    assert snap.resources["light"].current == 0.0  # unchanged — no silent fallback
```

- [ ] **Step 2: Run** — Expected FAIL.

- [ ] **Step 3: Implement** — branch at the top of `run_environment_clock_dispatch` on `params.get("mode") == "relight"`: find a `Torch` item (tag `light`) with remaining `consumable` charges on the PC; on success consume one charge, `pool._apply_and_clamp(Set, pool.max)`, clear darkness penalty, set `data["relit"]`/`torch_charges_remaining`; on no torch, return `data["error"] = "no_torch"` and mutate nothing. (Read the real inventory/charge model — `resource_ticks: 6` lives on the torch item; decide whether "charges" maps to item count or `resource_ticks`. Per content audit, the Delver kit has 3 torch items; treat one item = one relight to `max`.)

- [ ] **Step 4: Run** — Expected PASS.

- [ ] **Step 5: Commit**

```bash
git add sidequest/agents/subsystems/environment_clock.py tests/agents/subsystems/test_environment_clock.py
git commit -m "feat(environment_clock): relight consumes a torch, sets light=max, clears darkness; fails loudly with no torch"
```

### Task 4.2: Decomposer recognizes the relight intent + emits the dispatch

**Files:**
- Modify: `sidequest-server/sidequest/agents/intent_router.py` (decomposer prompt + emission for "light/snuff a torch")
- Modify: `sidequest-server/sidequest/agents/subsystems/__init__.py` precondition wiring if needed (relight is confidence-gated, not precondition-inert)
- Test: `sidequest-server/tests/agents/test_intent_router_relight.py`

- [ ] **Step 1: Write the failing test** — feed the router a stub LLM response (follow the existing intent-router test harness — it stubs the tool_use output) and assert that "I light a fresh torch" yields a `per_player[*].dispatch` entry with `subsystem="environment_clock"` and `params["mode"]=="relight"`. (The test asserts the *router contract*, not live LLM behavior.)

- [ ] **Step 2: Run** — Expected FAIL.

- [ ] **Step 3: Implement** — add the relight intent to the decomposer's tool description/instructions so a torch-management action routes to `environment_clock` with `mode=relight`; ensure the validator allows the subsystem name. Keep it confidence-gated (default 0.6) — it is a deliberate intent.

- [ ] **Step 4: Run** — Expected PASS.

- [ ] **Step 5: Commit**

```bash
git add sidequest/agents/intent_router.py sidequest/agents/subsystems/__init__.py \
        tests/agents/test_intent_router_relight.py
git commit -m "feat(intent-router): route torch-lighting intent to environment_clock relight (confidence-gated)"
```

### Task 4.3: `light.relit` OTEL span

- [ ] Add a `light.relit` span (attrs: `light.max`, `torch_charges_remaining`, `region`) on the relight branch, mirroring Task 3.3. Test asserts emission. Commit:
```bash
git commit -m "feat(otel): light.relit span on torch relight"
```

---

## PHASE 5 — Content: declare the pool and the dark

### Task 5.1: Declare the `light` resource pool

**Files:**
- Modify: `sidequest-content/genre_packs/caverns_and_claudes/rules.yaml`
- Test: `sidequest-server/tests/genre/test_caverns_resources.py` (content-validated via loader, not a RED unit; per project doctrine content is validated by `load_genre_pack`)

- [ ] **Step 1: Add the declaration** (after `stat_display_fields`, before `encounter_base_tension`):

```yaml
resources:
  - name: light
    label: Light
    min: 0.0
    max: 6.0          # one torch = 6 time-advancing beats (spec §9)
    starting: 0.0     # descend UNLIT on purpose (spec §5)
    voluntary: false
    decay_per_turn: 0.0   # burn is driven by environment_clock, NOT passive decay
    thresholds:
      - at: 1.0
        event_id: light_guttering
        narrator_hint: "The torch is guttering — its light has minutes left."
        direction: down
      - at: 0.0
        event_id: light_dark
        narrator_hint: "The light is gone. The dark itself closes in."
        direction: down
```

- [ ] **Step 2: Validate via the loader (the real gate per project memory — `validate pack` ≠ loader):**

```bash
cd sidequest-server && SIDEQUEST_GENRE_PACKS=../sidequest-content/genre_packs \
  uv run python -c "from sidequest.genre.loader import load_genre_pack; \
  p=load_genre_pack('caverns_and_claudes'); \
  print([r.name for r in p.rules.resources])"
```
Expected: output includes `light`.

- [ ] **Step 3: Commit (content repo, on its feature branch)**

```bash
cd sidequest-content && git add genre_packs/caverns_and_claudes/rules.yaml
git commit -m "feat(caverns): declare light survival-clock resource pool"
```

### Task 5.2: `lit` flags on Beneath Sünden regions

**Files:**
- Modify: `sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden/cartography.yaml`

- [ ] **Step 1: Add `lit:` to each region.** `ropefoot: lit: true` (the kept fire / surface), `the_dropmouth: lit: true` ("the last lit place"), and every deep/generated region (`entrance` and below) `lit: false`. Example:

```yaml
regions:
  ropefoot:
    name: Ropefoot
    lit: true
    terrain: settlement
    # ...
  the_dropmouth:
    name: The Dropmouth
    lit: true
    terrain: descent
    # ...
  entrance:
    name: The Entrance
    lit: false
    # ...
```

- [ ] **Step 2: Validate via loader** — confirm `load_genre_pack(...).worlds["beneath_sunden"].cartography.regions["entrance"]` exposes `lit == False` (Region uses `extra="allow"`; access via attr or extras bag — confirm which the loader produces and ensure the injector in Task 3.2 reads the matching form).

- [ ] **Step 3: Commit**

```bash
cd sidequest-content && git add genre_packs/caverns_and_claudes/worlds/beneath_sunden/cartography.yaml
git commit -m "feat(beneath_sunden): lit flags — surface lit, the deep dark"
```

### Task 5.3: Verify torch items (no change expected)

- [ ] Confirm `genre_packs/caverns_and_claudes/inventory.yaml` torch item carries `tags: [light, consumable, essential]` and that the Delver starting kit grants 3. No edit unless the relight charge model (Task 4.1) requires a field; if so, add it here and note as a deviation. Commit only if changed.

---

## PHASE 6 — UI: the light gauge

### Task 6.1: Render the light gauge with the −2 affordance

**Files:**
- Modify: `sidequest-ui/src/components/CharacterPanel.tsx`
- Modify: `sidequest-ui/src/types/payloads.ts` (only if a `thresholds?` field is needed on `ResourcePoolPayload`)
- Test: `sidequest-ui/src/__tests__/LightGauge.test.tsx`

`resources` already flows server→`PARTY_STATUS`→`App.tsx` `partyResources`→`CharacterPanel`. Reuse the `FolioEdgeTicks` pip renderer.

- [ ] **Step 1: Write the failing test**

```tsx
// src/__tests__/LightGauge.test.tsx
import { render, screen } from "@testing-library/react";
import { LightGauge } from "../components/CharacterPanel";

test("renders pips for current/max light", () => {
  render(<LightGauge current={4} max={6} torchCharges={2} />);
  expect(screen.getByText(/Light 4\/6/)).toBeInTheDocument();
  expect(screen.getByText(/2 torch/i)).toBeInTheDocument();
});

test("shows the -2 affordance when dark", () => {
  render(<LightGauge current={0} max={6} torchCharges={1} />);
  expect(screen.getByText(/−2 in the dark/)).toBeInTheDocument();
});

test("no -2 affordance when lit", () => {
  render(<LightGauge current={3} max={6} torchCharges={1} />);
  expect(screen.queryByText(/−2 in the dark/)).not.toBeInTheDocument();
});
```

- [ ] **Step 2: Run** — `cd sidequest-ui && npx vitest run src/__tests__/LightGauge.test.tsx` — Expected FAIL (`LightGauge` not exported).

- [ ] **Step 3: Implement** a `LightGauge` component in `CharacterPanel.tsx` that reuses the `FolioEdgeTicks` pip layout (label `"Light"`), adds a torch-count readout, and renders `"−2 in the dark"` when `current === 0`. Wire it into the Status tab beside HP, reading `partyResources["light"]`.

```tsx
export function LightGauge({ current, max, torchCharges }:
  { current: number; max: number; torchCharges: number }) {
  return (
    <div>
      <FolioEdgeTicks current={current} max={max} label="Light" />
      <span>{torchCharges} torch{torchCharges === 1 ? "" : "es"} left</span>
      {current === 0 && <span style={{ color: FOLIO.crimson }}>−2 in the dark</span>}
    </div>
  );
}
```

- [ ] **Step 4: Run** — Expected PASS.

- [ ] **Step 5: Commit (ui repo, feature branch)**

```bash
cd sidequest-ui && git add src/components/CharacterPanel.tsx src/__tests__/LightGauge.test.tsx
git commit -m "feat(ui): light survival gauge with torch count and -2-in-the-dark affordance"
```

---

## PHASE 7 — Narrator gaslighting (prose matches the gauge)

### Task 7.1: Surface light pool + darkness status in the narrator snapshot

**Files:**
- Modify: the narrator snapshot assembly (the function that builds the gaslighting snapshot the narrator sees — find via `world_materialization._apply_npc` neighbors / the snapshot-slimming allowlist, ADR-110)
- Test: `sidequest-server/tests/agents/test_narrator_sees_light_state.py`

- [ ] **Step 1: Write the failing test** — assert the narrator-facing snapshot/serialization includes the `light` pool (current/max) and, when dark, the darkness status text, so guttering/dark/relit prose is state-driven (not invented). Build a snapshot at `light=1` (guttering) and `light=0` (dark) and assert the rendered narrator context contains the corresponding cue/state.

- [ ] **Step 2: Run** — Expected FAIL (light pool not in the narrator allowlist).

- [ ] **Step 3: Implement** — add `resources` (at least `light`) and the active darkness status to the narrator snapshot allowlist/serialization (respect ADR-110 slimming — include only the compact light fields, not the whole pool object if the allowlist is field-pruned). The threshold lore minted by `mint_threshold_lore` on crossings already feeds narrator context; verify the guttering/dark `narrator_hint` strings reach the prompt.

- [ ] **Step 4: Run** — Expected PASS.

- [ ] **Step 5: Commit**

```bash
git add <narrator snapshot file> tests/agents/test_narrator_sees_light_state.py
git commit -m "feat(narrator): gaslight with light pool + darkness status so dark prose is state-driven"
```

---

## Final Verification (before PR)

- [ ] **Server full suite (with content + DB):**
```bash
cd sidequest-server && SIDEQUEST_DATABASE_URL=postgresql://$USER@localhost:5432/sidequest_test \
  SIDEQUEST_GENRE_PACKS=../sidequest-content/genre_packs uv run pytest -q
```
Confirm zero NEW failures vs the Step 0 baseline. Pay attention to any pack that declares resources (now loading for the first time) and to dual-dial / calibration tests (per memory, hp_depletion-style migrations regress `test_<pack>_pack_loads_with_dual_dial_schema` — none expected here, but verify).

- [ ] **UI:** `cd sidequest-ui && npx vitest run`
- [ ] **Lint/format:** `just server-check && just client-lint` (and `uv run ruff format --check .` per memory — the trivial gate does NOT run format-check).
- [ ] **Live OTEL proof (the lie detector):** headless playtest of `caverns_and_claudes/beneath_sunden` — descend unlit, confirm `light.tick` spans fire each move, `light.current` decrements, the darkness `Status` applies at 0, a skill check shows the −2, relight emits `light.relit` and clears the penalty. Per memory: **pull, don't just restart** — the oq-2 server and content trees lag develop independently; bounce both so you measure the new binary, not a stale cache.

---

## Self-Review (completed by author)

**Spec coverage:** §1 problem → Phases 3/5 (light now mechanical). §2 reusable substrate → generic `ResourcePool` + `status_roll_modifier` (any clock/status reuses). §3 ongoing teeth → Phase 2 (−2 on all rolls via status). §4 reuse audit → corrected (init_resource_pools and status-read were dead; Phases 1–2 build them). §5 pool → Task 5.1. §6.1 burn → Phase 3 (mechanism deviation logged). §6.2 relight → Phase 4. §7 consequence → Phase 2 + Task 3.1 reconcile. §8 data flow → Phases 3/4/7. §9 knobs → defaults in 5.1/3.1. §10 surfaces → Phases 6 (UI), 3.3/4.3 (OTEL), 7 (narrator). §11 equipped flag → explicitly out of scope (untouched). §12 risks → addressed: beat taxonomy (conservative whitelist + OTEL), status coupling (Phase 2 wires every site incl. WWN via SWN inheritance), first-descent legibility (state-reconciled penalty + UI affordance + narrator), save migration (init_resource_pools upsert preserves `current`; Task 1.1 test).

**Deviations from spec (log at review):**
1. §4/§7 "reuse status read" → built from scratch (Phase 2). 2. §4 "reuse init_resource_pools" → first production wiring (Phase 1), resurrects all declared pools. 3. §6.1 precondition-gated-on-exploration-beat → server-injected dispatch gated on time-advancing dispatch presence (no beat taxonomy exists); same undodgeable-deterministic intent. 4. Penalty applied by state reconciliation, not solely threshold crossing (handles start-at-0).

**Placeholder scan:** none — every code step shows code; anchors given where exact lines must be confirmed against models the engineer must read (`CreatureCore`/`Beat` ctors, narrator snapshot file, inventory charge model). These are flagged inline as "read the real model," not left as TBD.

**Type consistency:** `roll_modifier: int`, `status_roll_modifier(core)->int`, `DARKNESS_PENALTY=-2`, `wire_genre_resources(snapshot, pack)`, `inject_environment_clock(package, snapshot, pack)`, `run_environment_clock_dispatch(dispatch, *, snapshot)` used consistently across tasks.
