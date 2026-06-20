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

**Keith ruling (2026-06-20):** synthesize `cast` / `brace` / `break_contact` into the
sealed WN round the same way `attack` is (keep 106-2's defensive-reprisal model). Owned
by new **epic-152**. 125-8 stays as test-debt for the genuinely-stale subset.

## Measurement (ground truth, not the story's estimate)

Targeted run of the WWN/WN-combat files (Postgres + `SIDEQUEST_GENRE_PACKS` set):
**97 passed, 71 failed, 20 skipped, 3 errors.** The 71+3 are **multiple distinct roots**,
only one of which is "stripped beats" (per-bucket counts below are approximate — the
measurement had minor cross-category overlap, e.g. a cast failure surfacing on both the
dice and `apply_beat` paths):

| Root | Count | Nature |
|---|---|---|
| `DICE unknown beat_id` (empty WN pool) | 47 + 3 err | de-nativization mechanism — see below |
| chargen `[None×6]` (`test_cc_chargen_e2e`, `test_class_signature_wiring`) | 10 | **separate** — class choices not populated; possibly a real regression |
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

## Doctrine ruling

- **`cast`** — plainly a real feature; casting in combat must work. Synthesize.
- **`brace` / `break_contact`** — these are 106-2's per-beat reprisal *mitigation* (Keith
  ruling 2026-06-13). ADR-143 says the native **per-beat auto-reprisal** is exactly what
  the sealed initiative round *removes*, so there was a genuine fork: retire 106-2 vs.
  carry it forward. **Keith ruled 2026-06-20: carry it forward — synthesize the defensive
  actions into the WN round.** The sealed initiative round remains the sole opponent-attack
  path (Option A, 2026-06-13); a committed defensive action now seals into that round and
  reaches the existing mitigation helper.

## Decomposition — the boundary that assigns each test

**Principle:** a test belongs to the *production* epic if making it green needs **new
engine code**; it belongs to *test-debt* (125-8) if it goes green on **current `main` by a
pure test edit** (swap `committed_blow`/`strike`→`attack`, or flip a loader assertion to
the de-nativized reality).

### epic-152 — production synthesis (RED specs already written + failing)

- **152-1** — Synthesize the **defensive** WN actions (`brace` + `break_contact`). Mint
  transient `BeatKind.brace` / `BeatKind.push` beats under the WN gate; route the committed
  defensive action into the sealed round so it reaches `_defensive_posture_for_reprisal`.
  RED spec: `tests/integration/test_106_2_wwn_defensive_reprisal.py`. (Owns the incidental
  `committed_blow`→`attack` baseline swaps in that file.)
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

- **chargen `[None×6]` (10 tests)** — class choices not populated. **Highest-priority
  triage**: determine stale-fixture vs. real chargen regression before disposition. If real,
  its own bug story.
- **e2e chargen protocol (4)** — `CHARACTER_CREATION`/`SESSION_EVENT` where `ERROR`/`CHARACTER_CREATION`
  expected. Protocol drift; its own story.
- **Fate-SRD catalog load (1)** — `test_wwn_spell_catalog_load::test_non_wwn_pack_with_spells_file_does_not_load_catalog`
  raises `GenreLoadError: ruleset 'fate' requires rulesets/fate/srd/`. Fate-srd path; relate
  to epic-126/ADR-144, its own story.
- **deprecated-world skips (20)** — `test_chargen_dispatch` skips on a retired
  `caverns_sunden` world binding. Stale-skip cleanup.

## Why this respects "don't regress features"

Restoring the `cast`/`brace`/`break_contact` tests to green by weakening their assertions
would have **buried a live combat outage** behind a green suite. The boundary above keeps
every behavioral assertion intact: the synthesis-gated tests stay red until the *feature* is
restored (epic-152), and only the genuinely-stale ids are edited (125-8).

## Open question for execution

`move` is named in the 108-8 action-set list (`attack / move / item-use / cast`) but has no
failing test in this sweep. Out of scope here; synthesize only if a consumer needs it (YAGNI).
