# WN combat owns the full action set — design / disposition

- **Date:** 2026-06-20
- **Author:** Architect (brainstorm with Keith)
- **Status:** approved (disposition), production work tracked in **epic-152**
- **Related:** ADR-143 (Bind the Ruleset, Don't Balance It), ADR-142, ADR-114, epic-108 (de-nativization), story 106-2 (defensive reprisal), story 108-8 (attack synthesis), story 125-8 (test-debt cleanup)

## TL;DR

Story 125-8 was filed as "test debt — ~88 stale WWN-combat tests send stripped beat
ids; restore them." Triage proved the premise **wrong**: the dominant root is a **live
production combat outage**, not stale tests. 108-3 stripped every native combat beat off
WWN `hp_depletion` defs; 108-8 synthesized **only `attack`**. `cast_spell`, `brace`, and
`break_contact` were stripped but **never synthesized**, so in WWN combat today a player
can attack and use an item but **cannot cast a spell, brace, or disengage** — red since
108-3 landed (~2026-06-15), across `caverns_and_claudes`, `elemental_harmony`,
`heavy_metal`, `barsoom`.

**Keith ruling (2026-06-20, corrected after a WWN SRD reading — see "Course correction"
below):** `cast` IS a real WWN action → route it to the WWN spell spine. But `brace` /
`break_contact` are the *native* 106-2 reprisal-mitigation model — **shaping native into
the SRD**, the exact ADR-143 trap. WWN defines defense as **Armor Class manipulation**, so
the fix is to **remove** the native scaffolding and add the **genuine WWN defensive
actions** (Total Defense, Fighting Withdrawal). Owned by new **epic-152**. 125-8 stays as
test-debt for the genuinely-stale subset.

## Measurement (ground truth, not the story's estimate)

Targeted run of the WWN/WN-combat files (Postgres + `SIDEQUEST_GENRE_PACKS` set):
**97 passed, 71 failed, 20 skipped, 3 errors.** The 71+3 are **multiple distinct roots**,
only one of which is "stripped beats" (per-bucket counts below are approximate — the
measurement had minor cross-category overlap, e.g. a cast failure surfacing on both the
dice and `apply_beat` paths):

| Root | Count | Nature |
|---|---|---|
| `DICE unknown beat_id` (empty WN pool) | 47 + 3 err | de-nativization mechanism — see below |
| chargen `[None×6]` (`test_cc_chargen_e2e`, `test_class_signature_wiring`) | 10 | **separate** — stale test (brittle 2-choice-scene walk); class selection intact → story 152-3 |
| loader asserts old native beats present | 3 | stale assertion — flip to de-nativized reality |
| sealed-round wire fires no WN spans | 4 | stale beat id (commit can't seal) |
| e2e chargen protocol (`CHARACTER_CREATION` vs `ERROR`) | 4 | **separate** — protocol drift |
| misc assertion | 3 | mixed (defensive) |
| Fate-SRD catalog load (`GenreLoadError fate srd`) | 1 | **separate** — Fate srd-on-disk, unrelated to WN combat |
| deprecated-world skips (`test_chargen_dispatch`) | 20 skip | **separate** — stale skip for retired world |

## The de-nativization mechanism

`dispatch/dice.py`:

```
:390  if is_item_use_beat(...):        -> item-use transient intercept (works)
:414  if isinstance(ruleset, WithoutNumberRulesetModule) and is_wn_action_beat(id):
:415      beat = wn_action_beat(id)    -> synthesizes ONLY "attack"
:417  else: beat = next(b for b in cdef.beats ...)  -> cdef.beats == [] (108-3 stripped)
:420      raise DiceDispatchError("unknown beat_id ... available: []")
```

`beat_filter._WN_ACTION_BEAT_IDS == frozenset({"attack"})`. So `cast_spell`, `brace`,
`break_contact` (and `move`) reach `:417`, find an empty pool, and raise **before any
round runs**. The cast spine (`:440–488`) and the defensive-reprisal engine
(`_defensive_posture_for_reprisal`) **both still exist and are correct** — they are simply
**unreachable** because the action can't be committed. The 108-8 `attack` proof passes 5/5,
confirming the round machinery itself is healthy.

## Doctrine ruling — and a course correction

- **`cast`** — plainly a real WWN action; casting in combat must work. Route it to the WWN
  spell spine (152-2). Settled.
- **`brace` / `break_contact`** — first ruled "synthesize them into the round" (2026-06-20),
  which was **wrong** and was caught before any code shipped. Keith: *"why are we trying to
  shape native into SRD?"* He was right. Synthesizing `brace` as `BeatKind.brace, base:1` with
  mitigation from `resolve_tier_deltas`, and `break_contact` as a whole-attack-canceller, and
  the **per-beat reprisal** the mitigation patches — **none of those exist in WWN.** That is the
  exact ADR-143 / SOUL "Bind, Don't Balance" trap: porting native mechanics into a bound ruleset.

### What WWN actually says about defense (WWN SRD)

| Native (106-2) | WWN SRD |
|---|---|
| `brace` → flat HP mitigation via `resolve_tier_deltas(base:1)` | **Total Defense** (§2.4.4, Instant Action): give up your Main Action → **+2 Melee & Ranged AC + immune to Shock** until your next turn. Resolved by raising AC so the attack *misses* — there is no damage-reduction number |
| `break_contact` → **prevents the opponent's whole attack** | **Fighting Withdrawal** (§2.4.4, Main Action): disengage so a following **Run** provokes **no free attack**; it does **not** cancel the opponent's own-turn attack |
| **per-beat opponent reprisal** (what `brace` mitigates) | **§2.4.1**: side-initiative; the opponent attacks **once, on its own turn**. No per-beat reprisal exists |

**Corrected ruling (2026-06-20):** **remove** the native defensive-reprisal scaffolding from
the WWN path and add the genuine WWN defensive verbs — **Total Defense** (+2 AC, Shock immunity,
resolved by the existing AC math) and **Fighting Withdrawal / Run** (avoid the free attack on
flee). The opponent's attack on its slot vs the defender's (possibly Total-Defense-boosted) AC
*is* the model. `test_106_2` is **rewritten** to WWN semantics, not kept as a native RED spec.

## Decomposition — the boundary that assigns each test

**Principle:** a test belongs to the *production* epic if making it green needs **new
engine code**; it belongs to *test-debt* (125-8) if it goes green on **current `main` by a
pure test edit** (swap `committed_blow`/`strike`→`attack`, or flip a loader assertion to
the de-nativized reality).

### epic-152 — production synthesis (RED specs already written + failing)

- **152-1** — **WWN defensive actions.** *Remove* the native defensive-reprisal scaffolding
  (`_defensive_posture_for_reprisal` brace tier-delta mitigation + `break_contact` prevent) from
  the WWN path, and *add* the genuine WWN verbs: **Total Defense** (commit → +2 Melee/Ranged AC
  + Shock immunity until next turn, via the existing AC math) and **Fighting Withdrawal / Run**
  (wire the deferred `move` action; disengage avoids the free attack on a flee, does not cancel
  the opponent turn). **Rewrite** `tests/integration/test_106_2_wwn_defensive_reprisal.py` to WWN
  semantics (AC bump / Shock immunity / free-attack-on-flee), not native mitigation. Magnitudes
  are SRD-verbatim (+2 AC, Shock immunity) — nothing invented.
- **152-2** — Synthesize the **cast** WN action (`cast_spell`). Route a wwn `cast_spell`
  commit to the existing cast spine *before* the cdef lookup (model on the `is_item_use_beat`
  intercept); mirror on the `apply_beat` path. RED spec:
  `tests/integration/test_dice_path_spell_cast_102_2.py`,
  `test_wwn_{caverns,elemental_harmony,heavy_metal}_dispatch.py`,
  `test_wwn_scene_harness_fixture_proof.py`.

Both preserve 108-8's invariants: closed allowlist (a bogus id still raises) and the
`isinstance(ruleset, WithoutNumberRulesetModule)` gate (a native pack's authored
`attack`/`brace` resolves on the native engine, no `wwn.native_scaffolding_suppressed`).

### 125-8 — test-debt (epic-125), goes green by pure edit

`test_102_4_*` (sealed_round, dead_premise, family_smoke, npc_ally_barrier, wire_wiring),
`test_108_1` (native scaffolding cut), `test_108_5` (flavor rider), `test_wwn_shock_kill_observability`,
`test_reprisal_wn_lethality_e2e`, `test_wwn_heavy_metal_combat`, plus the 3 loader
assertion-flips (`test_class_abilities_loader`, `test_elemental_harmony_loads_wwn`,
`test_heavy_metal_loads_wwn_classes`). All swap stale offensive ids to `attack` or flip a
loader assertion; ~33 tests. **125-8's AC1 must change** — it can no longer require the full
WWN-combat suite green; the synthesis-gated tests are now owned by epic-152 and the separate
roots are filed elsewhere. Remaining red in 125-8's scope is loud-skipped with an epic-152 /
follow-up story ref, never a silent xfail.

### Separate roots — triage and file (NOT epic-152, NOT beat-strip)

- **chargen `[None×6]` (10 tests)** — **TRIAGED 2026-06-20: stale test, NOT a regression.**
  The WWN chargen has two choice-scenes (`the_calling` with `class_hint`; `the_trade` with 6
  `class_hint`-less background choices); the test's walk naively requires every choice-scene to
  be the class scene and dies on `the_trade`. Class selection content is intact
  (`char_creation.yaml:23/29/35`). Also carries de-nativization-coupled `class_moves`
  assertions → the player-facing surface of epic-152's action set. **Homed in story 152-3**
  (depends_on 152-2). No urgent production bug.
- **e2e chargen protocol (4)** — `CHARACTER_CREATION`/`SESSION_EVENT` where `ERROR`/`CHARACTER_CREATION`
  expected. Protocol drift; its own story.
- **Fate-SRD catalog load (1)** — `test_wwn_spell_catalog_load::test_non_wwn_pack_with_spells_file_does_not_load_catalog`
  raises `GenreLoadError: ruleset 'fate' requires rulesets/fate/srd/`. Fate-srd path; relate
  to epic-126/ADR-144, its own story.
- **deprecated-world skips (20)** — `test_chargen_dispatch` skips on a retired
  `caverns_sunden` world binding. Stale-skip cleanup.

## Why this respects "don't regress features" — and "bind, don't balance"

Two failure modes were live here, and the boundary above guards both:

1. **Burying a real outage** (don't regress features): forcing the `cast` tests green by
   weakening assertions would have hidden that WWN combat spellcasting is broken. So `cast`
   stays red until the *feature* is restored (152-2); only genuinely-stale ids are edited (125-8).
2. **Restoring the wrong thing** (bind, don't balance): the `brace`/`break_contact` tests
   encode a *native* model (tier-delta mitigation, attack-cancellation, per-beat reprisal) that
   WWN doesn't have. "Make the tests pass" would have re-imported native mechanics into the WWN
   binding — the ADR-143 trap. So those tests are **rewritten to WWN semantics** (Total Defense
   AC bump, Fighting Withdrawal), not made green against the native model. A red test is not
   always a thing to restore; sometimes it's a thing to retire or rewrite.

## Open question for execution

`move` is named in the 108-8 action-set list (`attack / move / item-use / cast`) but has no
failing test in this sweep. Out of scope here; synthesize only if a consumer needs it (YAGNI).
