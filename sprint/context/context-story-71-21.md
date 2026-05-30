---
parent: context-epic-71.md
workflow: tdd
---

# Story 71-21: perseus_cloud one-sided combat — beat_selection has no server-driven enemy-attack path (resolve_opponent_attack)

## Business Context

A `perseus_cloud` (space_opera / SWN) playtest surfaced that personal combat is
**one-sided**: the player's strike resolves server-side with full mechanical
backing (d20-vs-AC to-hit, server-rolled damage, ablative-HP depletion), but the
**opponent never takes a server-driven attack turn**. Any "enemy attacks you"
beat today is pure narrator prose with **zero mechanical backing** — no to-hit
roll, no damage roll, no HP delta. The player effectively cannot lose a personal
fight through mechanics.

This is a direct hit on two load-bearing doctrines:

- **Gaslight-the-narrator / OTEL lie-detector** — narration without a backing
  mechanical decision and an OTEL span is exactly the "Claude winging it" failure
  the GM panel exists to catch. An enemy that "shoots back" in prose but never
  rolls is the canonical violation.
- **Sebastien + Jade's missing crunch** (playgroup mandate) — these are the
  mechanics-first players who carried a 140-turn game on narrative *while feeling
  the absence of crunch*. A combat that can't actually threaten the player is the
  crunch failing to fire. The opponent's roll must be visible in the player-facing
  dice overlay.

The fix is **wiring, not invention**: the mechanical primitive
`ruleset.resolve_opponent_attack(...)` already exists, returns a typed
`OpponentAttackOutcome`, is unit-tested, and is the SWN module's implementation
of "the opponent takes a server-driven attack turn." It currently has **zero
production callers**. 71-21 wires it into the per-turn combat path so the seated
opponent reprises mechanically after the player acts.

## Technical Guardrails

**Resolution mode matters.** perseus_cloud / space_opera personal combat uses
`resolution_mode: beat_selection` with `hp_depletion` win condition (SWN ablative
HP, ADR-114). The live player-strike path is therefore the **`beat_selection`
branch of `dispatch_dice_throw`** in `sidequest/game/.../server/dispatch/dice.py`
(branch at `dice.py:489-739`), **not** the `opposed_check` branch in
`narration_apply.py`. Do not be misled by `narration_apply._resolve_opposed_check_branch`
(`narration_apply.py:4318+`) — that path *does* apply an opponent strike, but only
for `opposed_check` mode off a narrator-emitted beat. It is out of scope here.

**The seam to wire (load-bearing).** Append an opponent-reprisal block at the
**tail of the `beat_selection` branch** of `dispatch_dice_throw`, after the
player's `apply_beat`/`apply_beat_hp_channel` (≈ `dice.py:684-712`) and before
the function returns `DiceThrowOutcome` (`dice.py:923`). Sequence:
1. Find the seated opponent: `_opposite_side_first_actor(encounter, "player")`
   (already imported, used at `dice.py:650`) → resolve `CreatureCore` via
   `snapshot.find_creature_core(...)`.
2. Server-roll a d20; call `ruleset.resolve_opponent_attack(...)` with the
   opponent's `attack_bonus`/`combat_skill`/`stat_check` and the **player's** AC
   as `target_ac`.
3. On `hit`: resolve opponent damage via `ruleset.resolve_damage(beat=<opponent
   strike beat>)` and apply to the **player's** `CreatureCore` via
   `apply_beat_hp_channel(target=player_core, channel="strike", …)`.
4. Run `check_hp_depletion` / the downed seam (`beat_kinds.py:822-832`,
   `run_cwn_wwn_downed_seam` at `dice.py:704`) so the player can actually lose.
5. Broadcast the opponent's DICE_REQUEST/DICE_RESULT pair (mirror
   `dice.py:557-633`) so the enemy's roll is visible in the player-facing overlay.

**Ruleset gate — capability, not string.** `RulesetModule.resolve_opponent_attack`
is defined on the ABC (`game/ruleset/base.py:84`) and **raises
`NotImplementedError` by default** (fail-loud, correct). SWN implements it
(`game/ruleset/swn.py:88`); `native.py` intentionally does **not** (dial/opposed
rulesets resolve the opponent through the opposed branch). Gate the new call on
**`hp_depletion` win condition + module capability**, mirroring the existing
`wwn`/`cwn` gates at `dice.py:324,506`. Do **not** gate narrowly on
`pack.rules.ruleset == "swn"` — gate on capability so wwn/cwn (whose configs
extend Swn) inherit it. Resolve the module via `get_ruleset_module(pack.rules.ruleset)`
(already in `dice.py:293`). MEMORY trap: `WwnConfig extends Swn NOT Cwn` → watch
`isinstance` tuples.

**OTEL (lie-detector requirement, non-negotiable).** Spans live in
`sidequest/telemetry/spans/encounter.py` and `.../state_patch.py`.
- **Reuse:** `apply_beat_hp_channel` already emits `state_patch.hp`
  (`spans/state_patch.py:74`) on every HP delta — the player taking damage will
  already light the GM panel.
- **Add one new span** for the opponent's **to-hit decision** (so a real reprisal
  is distinguishable from narrator improv): an
  `encounter.opponent_attack_resolved`-style span carrying `attacker`, `target`,
  `d20`, `modifier`, `attack_total`, `target_ac`, `hit`. Model on
  `encounter_opposed_roll_resolved_span` (`encounter.py:494`) /
  `encounter_beat_applied_span` (`encounter.py:400`).

**Beat engine reference.** Player beat menu: `beat_filter.beats_available_for`
(`game/beat_filter.py:35`) — player-side only, do not extend for the opponent.
Beat application: `apply_beat` (`beat_kinds.py:385`), HP channel
`apply_beat_hp_channel` (`beat_kinds.py:198`). Existing primitive (do not
reimplement): `OpponentAttackOutcome` (`game/ruleset/resolution.py:18` — its
docstring already cites this bug), tested in
`tests/game/ruleset/test_swn_module.py:101,123`.

**Opponent stats source.** `sidequest-content/genre_packs/space_opera/rules.yaml`
personal-combat `opponent_default_stats` (≈ line 329) carries `armor_class: 12`;
strike beats (`shoot`, `overload`) carry `attack_bonus: 1`, `combat_skill: 1`,
`damage_channel: strike`, `damage_override`. Opponent seating / HP at
instantiation: `server/dispatch/confrontation.py:237-244` (core_resolver under
`hp_depletion`). The **player's** AC (needed as the opponent's `target_ac`) comes
from the player's `CreatureCore` — confirm it carries `armor_class`.

## Scope Boundaries

**In scope:**
- Wire `ruleset.resolve_opponent_attack(...)` into the `beat_selection` /
  `hp_depletion` combat path so the seated opponent takes a **server-driven,
  mechanically-backed** attack turn (d20 to-hit vs player AC, server-rolled
  damage, player HP depletion) after the player's beat resolves.
- A minimal "select the opponent's strike beat" helper (pick the opponent's first
  eligible `damage_channel: strike` beat — perseus_cloud opponents have exactly
  one, `shoot`). Reuse `resolve_damage(beat=…)` so damage stays content-authored.
- The opponent to-hit OTEL span + DICE_REQUEST/DICE_RESULT broadcast for the
  player-facing overlay.
- Capability-gated ruleset dispatch (SWN fires; native stays fail-loud).
- If (and only if) perseus_cloud `opponent_default_stats` lacks the ability score
  the opponent strike beat's `stat_check` references, add that content row
  (cross-repo touch — see Assumptions).

**Out of scope:**
- The `opposed_check` resolution path (`narration_apply.py:4318+`) — it already
  applies a (narrator-picked, tier-based) opponent beat; touching it risks
  double-applying. 71-21 is scoped to `beat_selection`/`hp_depletion` only.
- A general opponent "beat AI" / tactical beat-selection. Pick the strike beat;
  do not build decision logic for `overload` vs `shoot` etc.
- Multi-opponent / multi-actor reprisal ordering beyond the single seated Other
  (ADR-116). One opponent reprise per player beat for this story.
- Modifying the player-strike path itself (`dice.py:489-712`) — append after it,
  do not alter it. Do not touch the tested `resolve_opponent_attack` impl.
- native-ruleset packs (no enemy-turn by design — leave the fail-loud).

## AC Context

Expanded, testable acceptance criteria. TEA writes failing tests first.

1. **Opponent reprises mechanically on the beat_selection path.** Given a
   perseus_cloud (SWN, `beat_selection` + `hp_depletion`) personal combat with a
   seated opponent, when the player resolves a strike beat via
   `dispatch_dice_throw`, then `ruleset.resolve_opponent_attack(...)` is called
   for the seated opponent. *Test:* drive the beat_selection branch against the
   real perseus_cloud pack (NOT a synthetic fixture — MEMORY: opposed/real-pack
   wiring trap); assert `resolve_opponent_attack` is invoked with the player as
   target.

2. **Hit applies HP damage to the player.** When the opponent's to-hit roll
   meets/exceeds the player's AC (`hit=True`), then server-rolled damage is
   applied to the player's `CreatureCore` via the HP channel and a `state_patch.hp`
   span fires with a **negative delta on the player**. *Edge:* miss (`hit=False`)
   ⇒ **no** HP span, no HP change.

3. **Player can lose.** When opponent damage drives the player's HP to 0, then
   `check_hp_depletion` resolves the confrontation and `encounter.resolved` fires
   with `source="hp_depletion"` against the player. *Test:* seed player HP low,
   force a hit, assert resolution.

4. **OTEL opponent-attack span fires (lie-detector).** The new
   `encounter.opponent_attack_resolved` span fires on every opponent attack
   attempt (hit or miss) carrying `attacker`, `target`, `d20`, `modifier`,
   `attack_total`, `target_ac`, `hit`. *Test:* assert span present + attributes;
   assert it does NOT fire for native-ruleset packs.

5. **Player-facing overlay sees the enemy roll.** The opponent's
   DICE_REQUEST/DICE_RESULT pair is broadcast so the enemy's to-hit roll is
   visible in the dice overlay (Sebastien/Jade player-facing math). *Test:* assert
   the broadcast frames are emitted for the opponent's roll.

6. **Capability gate holds.** SWN (and capability-compatible wwn/cwn) fire the
   reprisal; native rulesets do **not** (and the ABC default stays a fail-loud
   `NotImplementedError`, never silently skipped). *Test:* native pack ⇒ no
   opponent attack, no `NotImplementedError` swallowed; gate is on capability +
   `hp_depletion`, not on `== "swn"`.

## Assumptions

- **Opponent beat selection = first eligible strike beat.** We assume picking the
  opponent's first `damage_channel: strike` beat (perseus_cloud: `shoot`) is the
  honest, minimal choice — it reuses `resolve_damage(beat=…)` and keeps damage
  content-authored. If a Dev finds perseus_cloud opponents with multiple/ambiguous
  strike beats, log a Design Deviation rather than building beat-AI in this story.
- **Scope is `beat_selection`/`hp_depletion` only.** We assume the `opposed_check`
  path's existing opponent-beat application is sufficient there and must not be
  double-driven. If the playtest repro turns out to be on opposed_check too,
  that's a separate finding — flag it, don't expand scope silently.
- **Content stat completeness (cross-repo risk).** SWN `_stat` fails loud on a
  missing ability key (`swn.py:39-50`, no neutral-10 fallback). We assume
  perseus_cloud `opponent_default_stats` already carries the ability score the
  opponent strike beat's `stat_check` names. **If it does not**, this story gains
  a `sidequest-content` touch: per MEMORY (story_repos_no_cli_flag) the session
  **Repos:** line is authoritative — manually branch `sidequest-content` off
  `develop`, log the YAML/repos mismatch as a deviation, and create+merge a
  content PR at finish. Verify this in RED before assuming server-only.
- **Player CreatureCore carries `armor_class`.** The opponent's `target_ac` is the
  player's AC; we assume the player core exposes `armor_class` at this seam. TEA
  should pin this in a fixture; if absent, it's a blocking finding.
