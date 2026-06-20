---
story_id: "125-8"
jira_key: ""
epic: null
workflow: "tdd"
---
# Story 125-8: [TEST DEBT] Restore the WWN/WN-combat test suite after 108-3 de-nativization — ~88 stale tests send stripped combat beats

## Story Details
- **ID:** 125-8
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none
- **Branch:** feat/125-8-restore-wwn-combat-test-suite
- **Branch Strategy:** gitflow (feat/125-8-restore-wwn-combat-test-suite)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-20T16:23:28Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-20T12:04:45Z | 2026-06-20T12:07:03Z | 2m 18s |
| red | 2026-06-20T12:07:03Z | 2026-06-20T15:59:54Z | 3h 52m |
| green | 2026-06-20T15:59:54Z | 2026-06-20T16:03:54Z | 4m |
| review | 2026-06-20T16:03:54Z | 2026-06-20T16:23:28Z | 19m 34s |
| finish | 2026-06-20T16:23:28Z | - | - |

## Sm Assessment

**Routing:** TDD / phased. setup → **red (TEA/Fezzik)** → green (Dev) → review → finish. Repo: `server` only. Branch `feat/125-8-restore-wwn-combat-test-suite` created and checked out.

**Setup hygiene:** Activation falsely primed a phantom IN_PROGRESS on **59-15** — that story is archived/done (`sprint/archive/59-15-session.md`, Jun 3) and "not found" in the sprint. Removed the stale leftover `sprint/.session/59-15-session.md` so the prime stops reactivating it. Merge gate clear (no open server PRs). All repos pulled and up to date before start.

**What this story is:** Pure TEST DEBT cleanup. ~88 failures + 3 errors across ~34 server test files in the WWN/WN-combat area, **all PRE-EXISTING on origin/develop** (predate this branch's merge-base). Root cause: epic-108's 108-3 de-nativization (content `34612bf`) stripped native combat beats from WWN combat pools; the WN round now supplies the action set (`is_wn_action_beat`, only `attack`). Stale tests still send `strike/committed_blow/...` and fail-loud at the loader (`loader.py:900`) or dispatch (`dice.py:420`).

**Load-bearing constraint (Keith, verbatim): "be sure not to regress features."** Encoded as **AC2** — each fixed test must exercise the CURRENT de-nativized WN combat path (synthesized WN action beats, or empty `encounter_beat_choices` for WN classes), **NOT** a trivial assertion-weakening to force green. Many of these tests assert real WN-round behavior (sealed-commit order, reprisal, initiative, shock-kill); gutting those assertions to go green = regressing coverage and is rejected. AC1 forbids silent xfail (loud skip + linked story only). AC3 keeps it test-only (any prod change → Delivery Finding + re-scope).

**Risk TEA/Dev must manage:** overlaps active epic-108 WN-round work (ADR-143/114 still "partial") — coordinate before sweeping so fixes don't collide with or pre-empt that story's own test updates. Reference pattern for pure data-swap cases: `tests/genre/test_classes_yaml_loader.py` (fixed under 126-37 — hardcoded `[strike,brace,break_contact]` → `[]`, which the loader exempts for WN classes per 108-7). Use it only where the case is genuinely a data swap, not where behavior is asserted.

## Architect Re-Scope (2026-06-20) — READ BEFORE EDITING TESTS

The SM Assessment above is now PARTIALLY SUPERSEDED. Triage (brainstorm with Keith) proved the failures are **multiple roots**, not one stale-beat root — and the cast/brace/break_contact failures are a **live production combat outage**, not stale tests. **The story ACs in the YAML were rewritten** to a narrowed scope; trust the YAML ACs, not "AC1 = full suite green."

- **OUT of 125-8 → epic-152** (production synthesis; the failing tests are 152's RED spec, leave them red / loud-skip with ref, **do not weaken**): `test_106_2_wwn_defensive_reprisal` (brace/break_contact → **152-1**), `test_dice_path_spell_cast_102_2` + `test_wwn_{caverns,elemental_harmony,heavy_metal}_dispatch` cast tests + the cast case in `test_wwn_scene_harness_fixture_proof` (cast → **152-2**).
- **OUT of 125-8 → separate stories** (not beat-strip): chargen `[None×6]` (`test_cc_chargen_e2e`, `test_class_signature_wiring`), e2e protocol (`test_chargen_e2e`), Fate-SRD (`test_wwn_spell_catalog_load`), deprecated-world skips (`test_chargen_dispatch`).
- **IN 125-8** (pure-edit-green only): the `committed_blow`/`strike`→`attack` swaps + the 3 loader assertion-flips. See AC list + `docs/superpowers/specs/2026-06-20-wn-full-action-set-design.md`.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)

- **Gap** (blocking, for epic-152): The WN opponent attack is **skipped entirely** under de-nativized WWN combat — a live combat outage parallel to the cast/brace outages 152 already owns, but NOT yet captured by any 152 story. `_resolve_opponent_reprisal` (`sidequest/server/dispatch/dice.py:2065-2074`, called per opponent slot from `sidequest/server/dispatch/wn_round.py:291`) requires an authored strike beat in `cdef.beats`; 108-3 stripped that pool empty and 108-8 synthesized **only the player's** `attack`, never the opponent's. So the round logs `opponent_reprisal_skipped reason=no_strike_beat` and the Other deals zero damage. Affects `dice.py` (synthesize the opponent's strike beat, parallel to `beat_filter.wn_action_beat`/108-8). This is a **prerequisite for 152-1** (its defensive-action rework assumes the opponent attack resolves) and also pre-existing-breaks `tests/integration/test_106_4_item_use_beat.py::test_item_use_costs_the_round_opponent_still_attacks` (outside 125-8 scope; confirmed pre-existing red on clean develop via stash). *Found by TEA during test design.*
- **Gap** (non-blocking, separate follow-up story): `tests/integration/test_102_4_wn_round_wire_wiring.py::test_mp_wire_first_commit_seals_second_commit_fires_the_round` — once the `committed_blow`→`attack` fix lets the first commit seal, the **second MP commit misresolves to the first PC's seat** (`'Rux' has already committed`) so the barrier never closes and the round never fires; the wire path also reaches the **real claude-agent-sdk transport** (non-hermetic narrator on the sealed-commit handler path). Affects `sidequest/handlers/dice_throw.py` seat resolution and/or test hermeticity (`session_handler_factory` wire path). Needs an MP-seat-resolution / wire-hermeticity follow-up; not a pure-edit test-debt item. Loud-skipped. *Found by TEA during test design.*
- **Improvement** (non-blocking): the design doc's 125-8 "pure-edit-green" bucket over-counted. By its OWN partition principle ("needs new engine code → production epic"), the 6 loud-skipped tests belong to a production epic (5 → finding #1 opponent-attack synthesis; 1 → finding #2 MP-wire). The genuinely-pure-edit subset is ~55 tests, all now green. Affects `docs/superpowers/specs/2026-06-20-wn-full-action-set-design.md` (decomposition table). *Found by TEA during test design.*

### Dev (implementation)

- **Gap** (blocking, for epic-152): Corroborated TEA Finding #1 during green verification — the WN opponent attack is skipped under de-nativized WWN combat (`opponent_reprisal_skipped reason=no_strike_beat`, `dice.py:2069` ← `wn_round.py:291`); the Other deals zero damage. This is a genuine production outage requiring opponent-attack synthesis (parallel to 108-8's player synthesis), out of scope for 125-8 (AC3). Affects `sidequest/server/dispatch/dice.py`. *Found by Dev during implementation.*
- No other upstream findings during implementation. Confirmed AC3: `git diff origin/develop` is **tests-only** (0 production files), so no production change was made or needed — the green-phase implementation set is empty by design (test-debt; the production code is already correct).

<!-- Reviewer: append-only below this marker. -->

### Reviewer (code review)

- **Improvement** (non-blocking): the caverns de-nativization flip (`tests/genre/test_class_abilities_loader.py:27` `test_caverns_and_claudes_warrior_has_no_native_combat_beat_post_denativization`) asserts only the **negative** `committed_blow not in warrior.encounter_beat_choices`, but its docstring claims "the Warrior keeps only its NON-combat (chase/social) choices." That positive claim is unverified — I loaded the pack and confirmed the warrior currently retains 5 real non-combat beats (`['sprint','barricade','talk_up_the_haul','flash_the_coin','walk_toward_the_door']`), so the assertion is **non-vacuous today**, but a future total-erasure of `encounter_beat_choices` would keep it green. The two sibling flips set a higher bar (`beat_ids == set()`, `casters_with_magic == _CASTER_IDS`). Affects `tests/genre/test_class_abilities_loader.py` (add one positive assertion that `encounter_beat_choices` is non-empty / names the surviving chase+social beats). Cheapest folded into epic-152's unskip pass. *Found by Reviewer during code review (corroborates silent-failure-hunter SF-1).*
- **Gap** (non-blocking, process): the 6th loud-skip (`test_102_4_wn_round_wire_wiring.py:188` `_MP_WIRE_BLOCKED`) references a generic "follow-up" with no story id, unlike the 5 opponent-attack skips that cite `epic-152`. TEA's Delivery Finding #2 (MP-seat misresolution + non-hermetic wire transport) is the source but no story is filed yet. Affects the sprint backlog — **SM should file the MP-seat/wire-hermeticity follow-up story and the skip reason should then cite its id** so the deferred production gap doesn't fall off the radar. AC3 correctly scopes the production fix OUT of 125-8; this is purely a tracking action. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)

- **Damage-pinned tests need an equipped weapon, not just a beat-id swap**
  - Spec source: context-story-125-8.md AC2; design doc "125-8 — test-debt (epic-125), goes green by pure edit" (`committed_blow`/`strike`→`attack` swap)
  - Spec text: "All swap stale offensive ids to `attack` or flip a loader assertion"
  - Implementation: the damage-pinned tests (dead_premise, shock, reprisal, heavy_metal_combat, sealed_round kills) also required arming the synthetic PCs with a 2d6 weapon item dict, because heavy_metal ships **no `unarmed_damage` floor** — a bare synthesized `attack` resolves no damage spec (`damage_spec_missing`) and ablates 0 HP. Added a shared `HM_WEAPON` (2d6) + `arm_pc()` to the harness (mirrors the already-green `test_108_8`'s local `_WEAPON`/`_arm_pc`). 2d6 reproduces the pre-strip `committed_blow` `damage_override` so all deterministic kill math (2 at min / 12 at max) holds verbatim.
  - Rationale: this exercises the CURRENT de-nativized path (weapon dice via the synthesized attack, `resolve_damage` priority 2) per AC2 — NOT an assertion-weakening. Re-adding a beat to `cdef.beats` would have been re-nativization and is rejected. Still test-only (AC3).
  - Severity: minor
  - Forward impact: none (additive harness helpers; `make_pc` default unchanged, so `test_108_8` and the disposition/instantiation consumers are unaffected)

- **6 tests loud-skipped instead of made green (opponent-attack production gap)**
  - Spec source: context-story-125-8.md AC1; design doc 125-8 bucket (which listed `test_reprisal_wn_lethality_e2e`, `test_wwn_heavy_metal_combat`, the sealed-round opponent-ordering + dead-premise actor-dropped + the ws_dice_throw wire test as pure-edit-green)
  - Spec text: "Each fixed test exercises the CURRENT de-nativized WN combat path … not a trivial assertion-weakening to force green" / "any remaining red is documented … with a loud skip + linked story, never a silent xfail"
  - Implementation: 5 of those tests cannot go green by a pure edit — they need the opponent attack to fire, which is the `no_strike_beat` production gap (Delivery Finding #1, epic-152); the 6th (`test_mp_wire_*`) hits a separate MP-seat/hermeticity root (#2). All 6 are `@pytest.mark.skip`-ped with a story-referencing reason (loud skip, never xfail).
  - Rationale: AC3 forbids production change; AC2 forbids re-nativizing (seeding a beat back) to fake green. Loud-skip + linked story is the AC1-prescribed mechanism for genuinely-blocked-on-unshipped-behavior.
  - Severity: minor (scope correction, fully documented)
  - Forward impact: epic-152 unskips the 5 opponent-attack tests when it lands the opponent-attack synthesis; the MP-wire follow-up unskips the 6th.

- **Loader tests rewritten/renamed beyond a one-line "flip"**
  - Spec source: design doc "the 3 loader assertion-flips (`test_class_abilities_loader`, `test_elemental_harmony_loads_wwn`, `test_heavy_metal_loads_wwn_classes`)"
  - Spec text: "flip a loader assertion"
  - Implementation: `test_class_abilities_loader` and `test_heavy_metal_loads_wwn_classes` were renamed and their bodies rewritten (not a single-line flip): the de-nativized invariant is "committed_blow/cast_spell absent from the combat pool" + the caster gate re-expressed on the surviving `class.magic_access`/`wwn_magic` surface (preserving the caster/non-caster coverage the stripped `cast_spell` `class_filter` carried). `test_elemental_harmony_loads_wwn` assertion #5 is the simple flip (combat pool empty).
  - Rationale: a bare inversion would lose the caster-gate coverage; re-expressing it on the live surface keeps coverage intact per AC2 (no weakening).
  - Severity: minor
  - Forward impact: none

### Dev (implementation)

- No deviations from spec. This is a test-debt story whose production code is already correct (108-3/108-8 shipped), so TEA's test edits made the in-scope suite green and there was **no implementation work** for the green phase — the correct outcome, not a deviation. Verified GREEN independently (61 passed, 6 skipped, 0 failed), confirmed the working tree is clean and the diff is tests-only (AC3), and pushed the branch. Did NOT implement the opponent-attack synthesis or MP-wire fixes (out of scope per AC3; owned by epic-152 / a follow-up — see Delivery Findings).

### Reviewer (audit)

- **"Damage-pinned tests need an equipped weapon, not just a beat-id swap" (TEA)** → ✓ ACCEPTED by Reviewer: sound and faithful to AC2. Arming a 2d6 weapon makes the synthesized `attack` resolve real weapon dice (`resolve_damage` priority 2), reproducing the pre-108-3 `committed_blow` 2d6 override deterministically (2 min / 12 max) — this *exercises* the de-nativized path rather than weakening an assertion. Re-adding a beat to `cdef.beats` would have been re-nativization (rejected per ADR-143). Verified `make_pc` default is unchanged so `arm_pc` is purely additive (no blast radius onto `test_108_8` or the disposition/instantiation consumers).
- **"6 tests loud-skipped instead of made green (opponent-attack production gap)" (TEA)** → ✓ ACCEPTED by Reviewer: the opponent-attack gap is a genuine production outage (I confirmed `_resolve_opponent_reprisal` requires an authored strike beat in `cdef.beats`, which 108-3 stripped; 108-8 synthesized only the player's `attack`). AC3 forbids the production fix here; loud-skip + linked story (`epic-152`) is the AC1-prescribed mechanism. All 6 are real `@pytest.mark.skip` with reason strings (no silent xfail) — verified by preflight `-rs` audit. (See my non-blocking process finding re: the 6th skip's missing story id.)
- **"Loader tests rewritten/renamed beyond a one-line flip" (TEA)** → ✓ ACCEPTED by Reviewer: re-expressing the caster gate on the live `magic_access`/`wwn_magic` surface preserves the coverage the stripped `class_filter` carried. The heavy_metal rewrite is rigorous (`casters_with_magic == _CASTER_IDS`, a set equality I verified at line 49). The caverns rewrite is the one place the rigor dipped to a bare negative — captured as my non-blocking Improvement finding, not a deviation reversal.
- **Dev "No deviations from spec"** → ✓ ACCEPTED by Reviewer: correct. Test-debt with already-correct production code → empty green-phase implementation set is the right outcome, independently re-verified (diff tests-only, tree clean).

## TEA Assessment

**Phase:** finish (test-debt restoration)
**Tests Required:** Yes (this IS the work — test edits; the production code is already correct)
**Status:** GREEN for the in-scope subset; 6 loud-skipped (blocked, documented). **No RED for Dev** — see "Handoff" below.

### What changed (13 test files, server only — AC3: zero production change)

| File | Change |
|------|--------|
| `tests/integration/_wn_round_102_4.py` (shared harness) | `HM_STRIKE_BEAT` `committed_blow`→`attack`; added `HM_WEAPON` (2d6) + `arm_pc()` |
| `tests/genre/test_class_abilities_loader.py` | flip → de-nativized: `committed_blow` absent from Warrior choices + combat pool |
| `tests/genre/test_elemental_harmony_loads_wwn.py` | flip → Martial Exchange combat pool empty (cast_spell stripped) |
| `tests/genre/test_heavy_metal_loads_wwn_classes.py` | flip → Blade-work pool empty; caster gate re-expressed via `magic_access`/`wwn_magic` |
| `tests/integration/test_102_4_wn_family_smoke.py` | `_combat_shape` falls back to synthesized `attack` when pool empty (keeps swn/cwn/awn) |
| `tests/integration/test_102_4_wn_sealed_round.py` | arm PCs (2d6); **1 loud-skip** (opponent ordering) |
| `tests/integration/test_102_4_wn_round_wire_wiring.py` | local `_STRIKE_BEAT`→`attack`; **2 loud-skips** (opponent-attack + MP-wire) |
| `tests/integration/test_102_4_dead_premise.py` | arm PCs (2d6); **1 loud-skip** (actor-dropped) |
| `tests/integration/test_108_1_wn_native_scaffolding_cut.py` | arm PC; "RED today" docstring corrected (108-1 shipped) |
| `tests/integration/test_108_5_wn_flavor_rider.py` | arm PC; "RED today" docstring corrected (108-5 shipped) |
| `tests/integration/test_wwn_shock_kill_observability.py` | `_STRIKE_BEAT`/literal→`attack` (PC already armed w/ longsword) |
| `tests/integration/test_reprisal_wn_lethality_e2e.py` | arm `_make_dying_pc`; **1 loud-skip** (reprisal kill) |
| `tests/integration/test_wwn_heavy_metal_combat.py` | arm `_make_attacker`; **1 loud-skip** (opponent reprisal) |

### Verification (targeted runs — full-suite reruns deliberately avoided per cost-runaway history)

- **In-scope 14 files:** baseline 38 failed + 3 errors → **61 passed, 6 skipped, 0 failed, 0 errors**.
- **Harness-consumer regression sweep** (the shared harness I edited): `test_108_8` (the 108-8 invariant 152-1 depends on) + lethality_arbiter + table_instantiation + disposition/affinity/levelup/npc-identity/pool tests = **all green (106 passed across two batches)**. Only non-green is `test_106_4_item_use_beat::test_item_use_costs_the_round_opponent_still_attacks` — **confirmed pre-existing red on clean develop via `git stash`** (same opponent-attack gap, outside 125-8 scope). **Zero regressions.**
- `ruff check` + `ruff format --check`: clean on all 13 files.

### Rule Coverage (the load-bearing constraints for this story)

| Rule | How honored |
|------|-------------|
| AC2 — exercise the CURRENT de-nativized path, no assertion-weakening (Keith: "don't regress features") | Damage-pinned tests arm a 2d6 weapon so the synthesized `attack` resolves real weapon dice (not a gutted assertion); loader flips re-express the caster gate on the live `magic_access` surface; family_smoke uses the synthesized `attack`. No re-nativizing (no beat re-added to `cdef.beats`). |
| AC1 — loud skip + linked story, never silent xfail | 6 `@pytest.mark.skip(reason=...)` with epic-152 / follow-up refs; verified the skip reasons print under `-rs`. Zero `xfail`. |
| AC3 — test-only; production change → Delivery Finding + re-scope | Zero production files touched (diff is `tests/` only). The opponent-attack gap is logged as a blocking Delivery Finding for epic-152, not fixed here. |
| AC4 — coordinate with epic-152, don't pre-empt its RED specs | 152-1/152-2/152-3-owned files (`test_106_2`, cast dispatch/spell-cast/scene-harness, chargen-surface) left untouched; `HM_STRIKE_BEAT` blast radius verified to NOT touch them. |
| Test quality — no vacuous assertions | Preserved every meaningful assertion; the `arm_pc` weapon keeps `removed_plain > 0` / kill / range assertions real, not trivially true. |

### Handoff note (READ — this is test-debt, not feature-TDD)

The production code for the in-scope tests is **already correct** (108-3/108-8 shipped), so restoring the tests makes them **GREEN immediately** — there is **nothing for Dev to implement**. The red→green collapse is expected for test-debt. Dev's green phase = **verify the in-scope suite is green** (commands above); **do NOT** implement the opponent-attack synthesis or MP-wire fixes — those are out of scope (AC3) and owned by epic-152 / a follow-up (Delivery Findings #1, #2). If Dev/Reviewer agree there is no implementation work, advance to review.

**Handoff:** To Dev (green) — verify-only; see Handoff note.
## Dev Assessment

**Implementation Complete:** N/A — **no implementation required** (test-debt; production code already correct per 108-3/108-8). The green phase is verify-only, as TEA's handoff stated. Per minimalist discipline + AC3, I added zero production code.

**Files Changed (this phase):** none (TEA's commit `1ab2443` is the only change; tests-only).

**Verification (independent, on the committed state):**
- In-scope 14 files: **61 passed, 6 skipped, 0 failed, 0 errors** (re-confirmed Fezzik's result on `1ab2443`).
- `git diff origin/develop`: **13 files, all under `tests/`** — 0 production files (AC3 ✓).
- Working tree clean; branch `feat/125-8-restore-wwn-combat-test-suite` pushed to `origin`.

**Scope discipline:** did NOT implement the opponent-attack synthesis (Delivery Finding #1, epic-152) or the MP-wire fix (#2). Those are production gaps owned elsewhere; touching them would violate AC3 and SOUL "Bind the Ruleset, Don't Balance It" (the opponent-attack synthesis is the WN engine's job, not a native patch). They remain loud-skipped with story refs (AC1).

**Self-review:** tests green ✓ · tree clean ✓ · no debug code (test-only diff) ✓ · correct branch ✓ · all in-scope ACs met (AC1 loud-skips, AC2 no-weakening, AC3 test-only, AC4 epic-152 files untouched) ✓.

**Handoff:** To Reviewer (Westley) for code review of the test changes.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 3 (all low) | confirmed 3 (all low/non-blocking), dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings (boundary cases covered manually — see [EDGE]) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 (2 med, 1 low) | confirmed 1 (downgraded → non-blocking improvement), reframed 1 (process/tracking), confirmed 1 low |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings (test quality covered manually — see [TEST]) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings (docstrings covered manually — see [DOC]) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (test-only diff, no type surface — see [TYPE]) |
| 7 | reviewer-security | Yes | clean | none | N/A — clean |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings (DRY surfaced by preflight — see [SIMPLE]) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings (AC rule enumeration done manually — see Rule Compliance) |

**All received:** Yes (3 enabled subagents returned; 6 disabled via `workflow.reviewer_subagents` are pre-filled Skipped and do not block the gate)
**Total findings:** 0 confirmed Critical/High · 0 Medium-blocking · 5 non-blocking (1 coverage-improvement, 1 process/tracking, 3 LOW DRY/completeness) · 0 dismissed-without-rationale · 0 deferred

### Rule Compliance

Story-governing rules enumerated against the full changed surface (13 files):

- **AC1 — loud skip + linked story, never silent xfail.** All 6 skips are real `@pytest.mark.skip(reason=...)` with story-referencing strings; zero `xfail`; reasons print under `-rs` (preflight-verified). VIOLATION? No — but 5 cite `epic-152` and the 6th cites a generic "follow-up" with no id (non-blocking process finding; SM to file the story).
- **AC2 — exercise the CURRENT de-nativized path; NO trivial assertion-weakening (Keith: "don't regress features").** Enumerated every flipped/edited assertion: `test_elemental_harmony` #5 → `beat_ids == set()` (exact, strong); `test_heavy_metal` → `[b.id ...] == []` + `casters_with_magic == _CASTER_IDS` (set equality, line 49 — strong, preserves the caster gate); `_combat_shape` → imports the production `WN_ATTACK_BEAT_ID` and is exercised both ways (heavy_metal empty-pool branch + swn/cwn/awn authored-strike branch, FAMILY confirmed); damage-pinned tests arm a real 2d6 weapon so kill math is genuine, not gutted; `test_wwn_shock_kill` anchor assertion is a **pre-existing range** `0 < hp_after < 10` (UNCHANGED — holds for old 10→7 and new 10→8; not a weakening). **One soft spot:** `test_class_abilities_loader` caverns flip is a bare negative — non-vacuous against current data (5 real choices, loaded & confirmed) but below the siblings' bar (non-blocking Improvement).
- **AC3 — test-only; production change → Delivery Finding + re-scope.** `git diff origin/develop...HEAD --stat` = 13 files, all under `tests/`, 0 production (preflight CONFIRMED). The opponent-attack and MP-wire production gaps are logged as Delivery Findings, not patched. Compliant.
- **AC4 — coordinate with epic-152; don't pre-empt its RED specs.** The 152-owned files (`test_106_2`, cast dispatch/spell-cast/scene-harness, chargen-surface) are untouched by this diff. `HM_STRIKE_BEAT` blast radius is `test_108_1`, `test_108_5`, the harness — all in-diff; `test_108_8` (the 152-1-depended-on invariant) imports neither `HM_STRIKE_BEAT` nor `arm_pc` (uses its own local `_WEAPON`/`_arm_pc`) — verified isolated. Compliant.
- **No-secrets / no-live-prod-coupling / hermetic-transport** (security subagent): clean. Pack-slug references are intentional genre-calibration tests gated by `_has_real_content()`; no new non-hermetic transport opened (the one MP-wire path is loud-skipped).

### Devil's Advocate

Suppose this diff is quietly broken. The most dangerous shape for a test-debt PR is *green-by-deception*: tests that pass because they stopped asserting anything, dressed in confident docstrings. So I attacked the assertions, not the prose. The caverns flip is the clearest candidate — a positive `committed_blow in choices` became a negative `committed_blow not in choices`, and a negative-existence check is the canonical vacuous-pass: it would survive an empty list. A malicious or careless future edit that wipes the warrior's `encounter_beat_choices` entirely would leave this test green while the docstring still swears the warrior "keeps its non-combat choices." I refused to take that on faith and loaded the pack: the warrior genuinely carries five chase/social beats today, so the assertion currently bites — but the coverage gap is real enough to log. Second attack: the loud-skips could be a dumping ground for failures the author simply couldn't be bothered to fix. I traced the opponent-attack skip to source — `_resolve_opponent_reprisal` truly requires an authored strike beat that 108-3 stripped, and 108-8 only ever synthesized the *player's* attack — so the Other dealing zero damage is a genuine production outage, not a test artifact; skipping is correct and the fix is out of scope by AC3. Third attack: the harness constant swap (`committed_blow`→`attack`) could silently corrupt an unrelated consumer. I enumerated every importer — three files, all in the diff — and confirmed the 152-critical `test_108_8` is insulated by its own local helpers. Fourth: arming PCs could *over*-fix, making damage tests pass for the wrong reason. But the 2d6 weapon reproduces the exact pre-strip override under pinned rng, so the deterministic 2/12 kill choreography is preserved verbatim, not loosened. What would a confused maintainer misread? The MP-wire skip's "follow-up" with no story id — easy to lose. That earns a process finding. Net: the deceptions I hunted for aren't here; what remains is one loose-but-currently-honest assertion and some DRY drift. None clears the Critical/High bar.

## Reviewer Assessment

**Verdict:** APPROVED

This is an exemplary test-debt restoration. The in-scope suite is GREEN (preflight: 48 passed, 6 skipped, 0 failed; TEA's broader 14-file run: 61 passed, 6 skipped), the diff is strictly tests-only (AC3), ruff is clean, and the load-bearing AC2 constraint ("don't regress features / no assertion-weakening") is honored across 12 of 13 files with genuine, non-vacuous assertions. The 6 loud-skips are correctly scoped to real, corroborated production gaps (opponent-attack synthesis → epic-152; MP-seat/wire-hermeticity → follow-up) and use the AC1-prescribed mechanism. No Critical or High findings.

**Data flow traced:** player `DICE_THROW` → synthesized WN `attack` (no `damage_override`) → `resolve_damage` priority 2 draws the equipped 2d6 weapon dict → opponent HP ablates → `state_patch.hp` span fires. Verified the tests arm PCs precisely because heavy_metal ships no `unarmed_damage` floor, so this path is exercised authentically (not stubbed to 0).

**Pattern observed:** de-nativization invariant flips done right — `tests/genre/test_elemental_harmony_loads_wwn.py:65` (`beat_ids == set()`) and `tests/genre/test_heavy_metal_loads_wwn_classes.py:246` (`casters_with_magic == _CASTER_IDS`) re-express stripped coverage on the live surface with exact equalities rather than loose negatives.

**Error handling:** N/A for production paths (test-only); the loud-skip-on-blocked-behavior pattern is the correct "failure" handling and is implemented as real `@pytest.mark.skip` reasons, not silent dodges (`tests/integration/test_102_4_wn_sealed_round.py:218` et al).

Dispatch-tag synthesis (3 enabled subagents + 6 disabled covered manually):

- **[EDGE]** (disabled) — manually checked boundaries: empty beat pool (`cdef.beats == []`) feeds the `_combat_shape` fallback; unarmed-PC-deals-0 is precisely why `arm_pc` exists; min/max rng pins bound the kill math. No unhandled edge.
- **[SILENT]** (silent-failure-hunter) — SF-1 caverns vacuous-negative-on-future-erasure → CONFIRMED, downgraded to non-blocking Improvement (non-vacuous vs current data, verified). SF-2 MP-wire skip "converts a defect to deferred debt" → reframed as a process/tracking finding (AC3 scopes the fix out; the gap is a real, logged Delivery Finding). SF-3 `_combat_shape` could pick an authored beat on content drift → LOW, the WN/empty-pool branch is the one under test and is exercised.
- **[TEST]** (disabled) — covered in AC2 enumeration above: assertions are non-vacuous; the shock-kill range assertion is pre-existing/unchanged; the caster-gate equality is real.
- **[DOC]** (disabled) — docstrings checked: 108-1/108-5 "RED today"→"STATUS shipped" corrections are accurate (those specs shipped). LOW: `test_102_4_wn_round_wire_wiring.py:354` `_STRIKE_BEAT` comment ("the span fires regardless") reads slightly stale now that both round-walking tests in that file are skipped — harmless, not blocking.
- **[TYPE]** (disabled) — test-only diff, no type/newtype/serde surface. N/A.
- **[SEC]** (security subagent) — clean: no secrets, no new non-hermetic transport, pack-slug coupling is the sanctioned calibration carve-out.
- **[SIMPLE]** (disabled; DRY surfaced by preflight) — LOW: `blade_2d6` weapon dict duplicated inline in 2 files + `HM_WEAPON` (intentional — different construction paths); `_OPPONENT_ATTACK_BLOCKED` defined 5× with minor wording drift; `HM_STRIKE_BEAT`/`HM_OPPONENT_HP` missing from `__all__`. None blocking; optional consolidation into the shared harness.
- **[RULE]** (disabled; enumerated manually) — see Rule Compliance: AC1–AC4 all compliant; AC2 has one non-blocking soft spot (caverns flip).

**Non-blocking follow-ups (captured in Delivery Findings):**
1. Strengthen the caverns flip with a positive assertion that the warrior retains its non-combat choices (fold into epic-152's unskip pass).
2. SM to file the MP-seat/wire-hermeticity follow-up story (TEA Delivery Finding #2) so the 6th skip can cite a real id.

**Handoff:** To SM (Vizzini) for finish-story.