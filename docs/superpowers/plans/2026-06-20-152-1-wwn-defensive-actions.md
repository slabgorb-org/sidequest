# 152-1 — WWN Defensive Actions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the native brace/break_contact reprisal-mitigation in the WWN combat path with the two genuine WWN defensive actions — Total Defense (+2 AC + Shock immunity) and Fighting Withdrawal (clean disengage, no parting attack) — resolved entirely by WWN math.

**Architecture:** WWN combat is a sealed initiative round (`run_wn_round`); the opponent attacks once on its slot via `resolve_opponent_attack(target_ac=...)` (`game/ruleset/without_number.py`). A committed defensive action is a `WnSealedCommit` read at opponent-attack resolution. Total Defense bumps the `target_ac` passed in and suppresses `resolve_shock`; Fighting Withdrawal sets `EncounterActor.withdrawn` without firing the opponent's parting attack. No grid/adjacency model exists or is added — disengage is the abstract `withdrawn` flag.

**Tech Stack:** Python 3.12, pytest (`-n auto`), pydantic v2, OTEL spans. Server repo `sidequest-server`, branch off `develop`.

## Global Constraints

- **Bind, don't balance (ADR-143 / SOUL):** every magnitude is WWN-SRD-verbatim. Total Defense = **+2 Melee & Ranged AC + Shock immunity until the start of your next turn** (WWN SRD §2.4.4). Fighting Withdrawal = **avoid the free attack on flee; does NOT cancel the opponent's own-turn attack** (§2.4.4). Never invent a number; never reproduce the native `resolve_tier_deltas` mitigation.
- **No per-beat reprisal framing:** the opponent attacks once on its initiative slot (§2.4.1). Drop "reprisal" language where touched.
- **108-8 invariants stay green:** the WN synthesis is a closed allowlist gated on `isinstance(ruleset, WithoutNumberRulesetModule)`; a bogus id still raises `DiceDispatchError`; a native pack's authored id resolves on the native engine (no `wwn.native_scaffolding_suppressed`).
- **OTEL on every decision (CLAUDE.md):** the opponent-attack span carries the defender's committed action + the AC delta; a withdrawal emits a span. The GM panel is the lie-detector.
- **Test env:** `SIDEQUEST_TEST_DATABASE_URL=postgresql://$USER@localhost:5432/sidequest_test` and `SIDEQUEST_GENRE_PACKS=/Users/slabgorb/Projects/oq-2/sidequest-content/genre_packs`. Tests use the shared `tests/integration/_wn_round_102_4` harness (`load_pack`, `seat_wn_combat`, `force_initiative`, `dispatch_throw`).

---

## File Structure

- `sidequest/game/beat_filter.py` — WN action synthesis. Add `total_defense` and `fighting_withdrawal` to a defensive synthesis (distinct from the `attack` strike) with the right `BeatKind` and zero damage.
- `sidequest/server/dispatch/dice.py` — the dispatch intercept (`:414`), `_defensive_posture_for_reprisal` (`:1939`, **delete/replace**), `_resolve_opponent_reprisal` (`:2021`, rename concept to opponent-attack, inject Total Defense AC/Shock, gate the parting attack on Fighting Withdrawal).
- `sidequest/game/ruleset/without_number.py` — `resolve_opponent_attack` (`:174`, consume a bumped `target_ac`), `resolve_shock` (`:311`, skippable under immunity). Prefer passing flags from the caller over changing these signatures if a caller-side bump suffices.
- `sidequest/game/encounter.py` — `EncounterActor.withdrawn` (existing) is the disengage substrate; no new field unless a "Total Defense active until next turn" marker is needed in `per_actor_state`.
- `sidequest/telemetry/spans/` — extend the opponent-attack span attrs (`defender_action`, `ac_delta`, `shock_immune`) and add a `wwn.fighting_withdrawal` span.
- `tests/integration/test_106_2_wwn_defensive_reprisal.py` — **rewritten** to WWN semantics (this file is the RED spec; it currently asserts the native model).

---

### Task 0: Rewrite test_106_2 to WWN semantics (RED spec)

This file currently asserts the native model (tier-delta mitigation, whole-attack prevention). Rewrite it to assert WWN behavior. These tests define every later task.

**Files:**
- Test: `tests/integration/test_106_2_wwn_defensive_reprisal.py` (full rewrite)

**Interfaces:**
- Consumes: `_wn_round_102_4` harness (`load_pack("heavy_metal")`, `seat_wn_combat`, `force_initiative`, `dispatch_throw`), `otel_capture`.
- Produces: the behavioral contract Tasks 1–3 implement — beat ids `"total_defense"`, `"fighting_withdrawal"`, `"attack"`; span `encounter.opponent_attack_resolved` attrs `defender_action`, `ac_delta`, `shock_immune`; span `wwn.fighting_withdrawal`.

- [ ] **Step 1: Write the WWN Total Defense test (AC bump)**

```python
def test_total_defense_raises_ac_so_a_base_hitting_attack_misses(monkeypatch):
    """WWN SRD 2.4.4: Total Defense gives +2 Melee/Ranged AC until next turn.
    Pin the opponent's d20 so the swing HITS at the defender's base AC but MISSES
    at base+2 — proving the defense is AC math, not damage mitigation."""
    pack, snap, enc = _solo_wwn_combat()           # PC vs one blade, heavy_metal (wwn)
    force_initiative(enc, [(_OPP, 9), (_PC, 2)])    # opponent acts first
    base_ac = snap.find_creature_core(_PC).armor_class
    # Pin the opponent's to-hit to exactly base_ac (a hit at base, a miss at base+2).
    monkeypatch.setattr("random.randint", lambda a, b: base_ac if (a, b) == (1, 20) else a)
    hp0 = _pc_hp(snap)
    dispatch_throw(pack=pack, snap=snap, enc=enc, character_name=_PC, player_id="p1",
                   beat_id="total_defense")
    assert _pc_hp(snap) == hp0, (
        "a committed Total Defense must raise AC by +2 so the pinned-to-base swing misses; "
        f"PC took damage anyway ({hp0} -> {_pc_hp(snap)})"
    )
```

- [ ] **Step 2: Write the Total Defense Shock-immunity test**

```python
def test_total_defense_grants_shock_immunity(monkeypatch, otel_capture):
    """Shock chips on a MISS when Melee AC <= shock_ac; Total Defense makes the
    defender immune to Shock until their next turn (no chip even on a miss)."""
    pack, snap, enc = _solo_wwn_combat()
    force_initiative(enc, [(_OPP, 9), (_PC, 2)])
    monkeypatch.setattr("random.randint", lambda a, b: a)   # opponent rolls min → a miss
    hp0 = _pc_hp(snap)
    dispatch_throw(pack=pack, snap=snap, enc=enc, character_name=_PC, player_id="p1",
                   beat_id="total_defense")
    assert _pc_hp(snap) == hp0, "Total Defense must suppress Shock chip damage on a miss"
    span = _one(spans_named(otel_capture, "encounter.opponent_attack_resolved"))
    assert dict(span.attributes).get("shock_immune") is True
```

- [ ] **Step 3: Write the OTEL span test (defender_action + ac_delta)**

```python
def test_total_defense_surfaces_on_opponent_attack_span(monkeypatch, otel_capture):
    pack, snap, enc = _solo_wwn_combat()
    force_initiative(enc, [(_OPP, 9), (_PC, 2)])
    monkeypatch.setattr("random.randint", lambda a, b: b)
    dispatch_throw(pack=pack, snap=snap, enc=enc, character_name=_PC, player_id="p1",
                   beat_id="total_defense")
    attrs = dict(_one(spans_named(otel_capture, "encounter.opponent_attack_resolved")).attributes)
    assert attrs.get("defender_action") == "total_defense"
    assert int(attrs.get("ac_delta", 0)) == 2
```

- [ ] **Step 4: Write the Fighting Withdrawal test (clean disengage, no parting attack)**

```python
def test_fighting_withdrawal_disengages_without_a_parting_attack(monkeypatch, otel_capture):
    """WWN SRD 2.4.4: a Fighting Withdrawal lets you leave without the free attack
    a plain flee would provoke. The PC withdraws and takes ZERO damage."""
    pack, snap, enc = _solo_wwn_combat()
    force_initiative(enc, [(_OPP, 9), (_PC, 2)])
    monkeypatch.setattr("random.randint", lambda a, b: b)   # max rolls: a parting attack WOULD hit
    hp0 = _pc_hp(snap)
    dispatch_throw(pack=pack, snap=snap, enc=enc, character_name=_PC, player_id="p1",
                   beat_id="fighting_withdrawal")
    assert _pc_hp(snap) == hp0, "Fighting Withdrawal must avoid the parting attack (zero HP loss)"
    assert snap.find_encounter_actor(_PC).withdrawn is True
    assert spans_named(otel_capture, "wwn.fighting_withdrawal")
```

- [ ] **Step 5: Write the plain-flee contrast test (a flee provokes the parting attack)**

```python
def test_plain_flee_provokes_the_parting_attack(monkeypatch):
    """Contrast: leaving WITHOUT a Fighting Withdrawal (a bare 'move'/flee) provokes
    the opponent's free attack as you go — so the +2-AC-and-clean-exit of Fighting
    Withdrawal is meaningful, not always-on."""
    pack, snap, enc = _solo_wwn_combat()
    force_initiative(enc, [(_OPP, 9), (_PC, 2)])
    monkeypatch.setattr("random.randint", lambda a, b: b)   # the parting attack hits
    hp0 = _pc_hp(snap)
    dispatch_throw(pack=pack, snap=snap, enc=enc, character_name=_PC, player_id="p1",
                   beat_id="move")
    assert _pc_hp(snap) < hp0, "a plain flee must provoke the opponent's parting attack"
```

- [ ] **Step 6: Delete the native-model tests in this file**

Remove `test_brace_*`, `test_break_contact_prevents_*`, `test_undefended_strike_span_reports_zero_mitigation`, and the `_defensive_posture_for_reprisal` posture-helper tests (`test_posture_helper_*`). They assert the native model being removed. Keep `test_swn_sibling_without_initiative_keeps_legacy_reprisal_no_raise` only if the SWN legacy path is untouched by this story (it is — scope is the WWN binding); otherwise move it to an SWN-owned file. Update module docstring to cite WWN SRD §2.4.4 and ADR-143.

- [ ] **Step 7: Run to verify RED**

Run: `uv run pytest tests/integration/test_106_2_wwn_defensive_reprisal.py -q`
Expected: the 5 new tests FAIL (unknown beat_id `total_defense`/`fighting_withdrawal`/`move`; no `ac_delta`/`shock_immune`/`wwn.fighting_withdrawal`).

- [ ] **Step 8: Commit**

```bash
git add tests/integration/test_106_2_wwn_defensive_reprisal.py
git commit -m "test(152-1): rewrite 106-2 to WWN defensive semantics (RED) — Total Defense, Fighting Withdrawal"
```

---

### Task 1: Remove the native defensive-reprisal scaffolding from the WWN path

**Files:**
- Modify: `sidequest/server/dispatch/dice.py` — delete `_defensive_posture_for_reprisal` (`:1939-2018`) and its call in `_resolve_opponent_reprisal` (`:2100`), replacing the call with a Task-2/3 hook (stub returns "no modifier" for now so the opponent attack resolves plainly).

**Interfaces:**
- Produces: `_resolve_opponent_reprisal` no longer applies `brace`/`break_contact` mitigation; the opponent's attack resolves vs the defender's base AC. The `defender_commit` parameter is retained (Tasks 2/3 read it).

- [ ] **Step 1: Run the two native-removal canary assertions** (already in Task 0 — `test_total_defense_*` fail because the native path is gone AND the new path isn't built; confirm no native mitigation remains by a quick grep)

Run: `grep -n "_defensive_posture_for_reprisal\|resolve_tier_deltas" sidequest/server/dispatch/dice.py`
Expected (after edit): no hits.

- [ ] **Step 2: Delete `_defensive_posture_for_reprisal` and its call**

Remove the function body (`:1939-2018`) and replace the call site (`:2100-2120` region) so the opponent attack resolves with `target_ac = base_ac` and Shock per normal — the defensive modifier becomes a new helper `_wwn_defender_modifier(defender_commit) -> DefenderMod` introduced in Task 2 (here, inline a no-op returning base AC / Shock-on).

- [ ] **Step 3: Run — opponent attack resolves plainly, native tests gone**

Run: `uv run pytest tests/integration/test_106_2_wwn_defensive_reprisal.py tests/integration/test_reprisal_wn_lethality_e2e.py -q`
Expected: native-model tests are gone (Task 0 deleted them); the new Total Defense/Withdrawal tests still FAIL (not yet implemented); the plain opponent-attack still fires (lethality e2e green or unchanged).

- [ ] **Step 4: Commit**

```bash
git add sidequest/server/dispatch/dice.py
git commit -m "refactor(152-1): remove native brace/break_contact reprisal-mitigation from the WWN path (ADR-143)"
```

---

### Task 2: Total Defense — +2 AC + Shock immunity

**Files:**
- Modify: `sidequest/game/beat_filter.py` — add `"total_defense"` to a defensive WN action set; synthesize a transient `BeatDef(kind=BeatKind.none, base=0, ...)` carrying no damage (Total Defense deals nothing; it is a posture).
- Modify: `sidequest/server/dispatch/dice.py` — intercept (`:414`) recognizes the defensive action so it can be committed; `_wwn_defender_modifier` returns `ac_delta=+2, shock_immune=True` for a committed `total_defense`; `_resolve_opponent_reprisal` applies them (`target_ac += ac_delta`; skip `resolve_shock` when `shock_immune`). Span carries `defender_action`, `ac_delta`, `shock_immune`.

**Interfaces:**
- Consumes: `WnSealedCommit.beat_id == "total_defense"`; `resolve_opponent_attack(target_ac=...)` (`without_number.py:174`); `resolve_shock` (`:311`).
- Produces: `is_wn_defensive_action(beat_id) -> bool`, `wn_defensive_beat(beat_id) -> BeatDef`; `_wwn_defender_modifier(commit) -> (ac_delta: int, shock_immune: bool, withdraws: bool)`.

- [ ] **Step 1: Run the Total Defense tests to confirm RED**

Run: `uv run pytest tests/integration/test_106_2_wwn_defensive_reprisal.py -k total_defense -q`
Expected: FAIL — `DiceDispatchError: unknown beat_id 'total_defense'`.

- [ ] **Step 2: Add the defensive synthesis in `beat_filter.py`**

```python
WN_TOTAL_DEFENSE_BEAT_ID = "total_defense"
_WN_DEFENSIVE_BEAT_IDS = frozenset({WN_TOTAL_DEFENSE_BEAT_ID})

def is_wn_defensive_action(beat_id: str) -> bool:
    """True iff beat_id is a synthesized WWN defensive action (Total Defense; story 152-1)."""
    return beat_id in _WN_DEFENSIVE_BEAT_IDS

def wn_defensive_beat(beat_id: str) -> BeatDef:
    """Transient BeatDef for a WWN defensive action. Total Defense deals no damage —
    it is a posture that raises AC and grants Shock immunity (WWN SRD 2.4.4), applied
    at opponent-attack resolution, not here. kind=none so it never feeds the strike path."""
    if beat_id not in _WN_DEFENSIVE_BEAT_IDS:
        raise PackError(f"{beat_id!r} is not a synthesizable WN defensive action")
    return BeatDef(id=beat_id, label="Total Defense", kind=BeatKind.none, base=0, stat_check="DEX")
```

- [ ] **Step 3: Recognize the defensive action at the dispatch intercept (`dice.py:414`)**

Extend the WN intercept so a defensive action synthesizes instead of hitting the empty-cdef lookup:

```python
if isinstance(ruleset, WithoutNumberRulesetModule) and is_wn_action_beat(payload.beat_id):
    beat = wn_action_beat(payload.beat_id)
elif isinstance(ruleset, WithoutNumberRulesetModule) and is_wn_defensive_action(payload.beat_id):
    beat = wn_defensive_beat(payload.beat_id)        # seals as the actor's round action; no damage
else:
    beat = next((b for b in cdef.beats if b.id == payload.beat_id), None)
    if beat is None:
        ...  # unchanged: raise DiceDispatchError (closed allowlist invariant)
```

- [ ] **Step 4: Apply the modifier at opponent-attack resolution**

Replace the Task-1 stub with:

```python
def _wwn_defender_modifier(commit: WnSealedCommit | None) -> tuple[int, bool, bool]:
    """(ac_delta, shock_immune, withdraws) for a committed WWN defensive action.
    Total Defense → (+2, True, False). No native tier-deltas. (WWN SRD 2.4.4)"""
    if commit is None:
        return 0, False, False
    if commit.beat_id == "total_defense":
        return 2, True, False
    return 0, False, False
```

In `_resolve_opponent_reprisal`: `ac_delta, shock_immune, _ = _wwn_defender_modifier(defender_commit)`, pass `target_ac = base_ac + ac_delta` into `resolve_opponent_attack`, and gate the `resolve_shock` call on `not shock_immune`. Add `defender_action`, `ac_delta`, `shock_immune` to the `encounter_opponent_attack_resolved_span`.

- [ ] **Step 5: Run the Total Defense tests to GREEN**

Run: `uv run pytest tests/integration/test_106_2_wwn_defensive_reprisal.py -k total_defense -q`
Expected: PASS (AC bump misses the pinned-to-base swing; Shock suppressed; span carries the attrs).

- [ ] **Step 6: Commit**

```bash
git add sidequest/game/beat_filter.py sidequest/server/dispatch/dice.py sidequest/telemetry/spans
git commit -m "feat(152-1): WWN Total Defense — +2 AC + Shock immunity at opponent-attack resolution (SRD 2.4.4)"
```

---

### Task 3: Fighting Withdrawal / Run — clean disengage vs parting attack

**Files:**
- Modify: `sidequest/game/beat_filter.py` — add `"fighting_withdrawal"` and `"move"` to the WN action set (`move` = the deferred disengage from the 108-8 note).
- Modify: `sidequest/server/dispatch/dice.py` — a committed `fighting_withdrawal` sets the actor `withdrawn=True` and SUPPRESSES the opponent's parting attack; a committed `move` (plain flee) sets `withdrawn=True` but FIRES the opponent's parting attack first. Emit `wwn.fighting_withdrawal`.

**Interfaces:**
- Consumes: `EncounterActor.withdrawn` (`encounter.py:126`); the opponent-attack resolver from Task 2.
- Produces: the parting-attack gate — `withdraws=True` from `_wwn_defender_modifier` for both ids, plus a `parting_attack: bool` (False for `fighting_withdrawal`, True for `move`).

- [ ] **Step 1: Run the withdrawal tests to confirm RED**

Run: `uv run pytest tests/integration/test_106_2_wwn_defensive_reprisal.py -k "withdrawal or flee" -q`
Expected: FAIL — unknown beat_id `fighting_withdrawal`/`move`.

- [ ] **Step 2: Add `fighting_withdrawal` + `move` to the defensive synthesis**

Extend `_WN_DEFENSIVE_BEAT_IDS` to include them; `wn_defensive_beat` labels them "Fighting Withdrawal" / "Move" (kind=none, no damage). Extend `_wwn_defender_modifier` to return `withdraws=True` for both, and surface a `parting_attack` flag (False for `fighting_withdrawal`, True for `move`).

- [ ] **Step 3: Wire the withdrawal + parting-attack gate in dispatch**

When the committed action withdraws: set `snap.find_encounter_actor(actor).withdrawn = True`. If `parting_attack` is True, resolve ONE opponent attack against the fleeing actor (reuse the Task-2 opponent-attack path, no Total Defense modifier) BEFORE marking withdrawn; if False (Fighting Withdrawal), skip it. Emit `wwn.fighting_withdrawal` (attrs: actor, parting_attack=False) on a clean withdrawal.

- [ ] **Step 4: Run the withdrawal tests to GREEN**

Run: `uv run pytest tests/integration/test_106_2_wwn_defensive_reprisal.py -k "withdrawal or flee" -q`
Expected: PASS (Fighting Withdrawal → zero HP + withdrawn + span; plain `move` → HP loss from the parting attack).

- [ ] **Step 5: Commit**

```bash
git add sidequest/game/beat_filter.py sidequest/server/dispatch/dice.py sidequest/telemetry/spans
git commit -m "feat(152-1): WWN Fighting Withdrawal vs plain flee — parting-attack gate on the withdrawn substrate (SRD 2.4.4)"
```

---

### Task 4: Full-file green + 108-8 invariant + suite guard

**Files:**
- Test: `tests/integration/test_106_2_wwn_defensive_reprisal.py`, `tests/integration/test_108_8_wn_round_owns_action_set.py`

- [ ] **Step 1: Run the whole rewritten file + the 108-8 invariant guards**

Run:
```bash
uv run pytest tests/integration/test_106_2_wwn_defensive_reprisal.py \
              tests/integration/test_108_8_wn_round_owns_action_set.py -q
```
Expected: all PASS. Specifically `test_unknown_action_id_under_zero_beats_still_raises` and `test_native_attack_does_not_engage_wn_synthesis` stay green — the defensive synthesis is a closed, WN-gated allowlist.

- [ ] **Step 2: Run the targeted WWN-combat neighborhood (no regression)**

Run the Task-0 harness neighbors that touch the opponent-attack path:
```bash
uv run pytest tests/integration/test_102_4_wn_sealed_round.py \
              tests/integration/test_reprisal_wn_lethality_e2e.py \
              tests/integration/test_wwn_heavy_metal_combat.py -q
```
Expected: PASS or unchanged vs the pre-152-1 baseline (these belong to 125-8's attack-swap scope; if any are still red there, that is expected 125-8 work, not a 152-1 regression — confirm the failure mode is `committed_blow`→`attack`, not a defensive-path break).

- [ ] **Step 3: Commit (if any test-only touch-ups)**

```bash
git add -A && git commit -m "test(152-1): full 106-2 green + 108-8 invariant guard"
```

---

## Self-Review

- **Spec coverage:** AC1 (remove native) → Task 1. AC2 (Total Defense +2 AC/Shock immunity) → Task 2. AC3 (Fighting Withdrawal, no cancel of own-turn attack) → Task 3. AC4 (106-2 rewritten to WWN) → Task 0. AC5 (OTEL span carries defender action + AC delta) → Tasks 2/3. AC6 (SRD-verbatim, no content change) → Global Constraints + no content files touched. Covered.
- **Open risk to resolve during execution (not a placeholder — a real unknown):** Task 2 Step 4 assumes the caller can bump `target_ac` without changing `resolve_opponent_attack`'s signature. If the AC is computed *inside* the resolver from `target_core.armor_class`, pass an explicit `ac_bonus`/`shock_immune` through the call instead — both are caller-supplied today, so this is a small signature add, kept minimal. Verify before Step 4 by reading `without_number.py:160-200`.
- **Type consistency:** `_wwn_defender_modifier` returns `(ac_delta:int, shock_immune:bool, withdraws:bool)` in Task 2 and gains a `parting_attack` flag in Task 3 — refactor its return to a small dataclass `DefenderMod` at Task 3 Step 2 so the tuple doesn't grow unwieldy; update the single Task-2 call site.
- **Scope honesty:** Fighting Withdrawal rides the abstract `withdrawn` flag; there is no grid/adjacency model and this plan adds none. "Avoid the parting attack" is the digital analog of "no free attack on flee" — confirm with Keith that abstract-withdraw is the intended fidelity (it matches the engine's existing disengage substrate).
