---
story_id: "158-31"
jira_key: ""
epic: "158"
workflow: "tdd"
---
# Story 158-31: Dogfight firewall — resolve via SWN hp_depletion; DELETE the native dial + beats (ADR-153 Plan 1)

## Story Details
- **ID:** 158-31
- **Jira Key:** (none — Jira integration disabled)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-27T10:56:13Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-27T08:52:33Z | 2026-06-27T08:54:27Z | 1m 54s |
| red | 2026-06-27T08:54:27Z | 2026-06-27T10:13:16Z | 1h 18m |
| green | 2026-06-27T10:13:16Z | 2026-06-27T10:47:13Z | 33m 57s |
| review | 2026-06-27T10:47:13Z | 2026-06-27T10:56:13Z | 9m |
| finish | 2026-06-27T10:56:13Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

- **Gap (non-blocking):** Story `repos` field lists only `server`, but the Plan-1 implementation spans **two** subrepos — `sidequest-content` (rewrite the dogfight ConfrontationDef) and `sidequest-server` (ship-scale seating gate, default opponent, HP-resolution wiring, validator guard). Downstream agents should branch/PR in both subrepos under `feat/dogfight-rebuild-firewall`.

### TEA (test design)
- **Conflict (non-blocking):** ADR-153 §6 inverts the **currently-GREEN** Story 59-17 dispatch tests in `sidequest-server/tests/server/dispatch/test_dogfight_instantiation_production_path.py` (verified: all 4 pass on `develop`). The plan never listed these as needing updates. Per Keith's 2026-06-27 decision I rewrote 3 of them to the §6 contract (co-located NPC never conscripted; frame-default always seats; no refusal). Logged as a Design Deviation below. Dev: these are §7/Plan-2-adjacent (dispatch layer) but Plan-1's seater change forces them — confirm GREEN after Tasks 2+3.
- **Gap (non-blocking):** The **synthetic `swn_test_pack` fixture** dogfight def *also* carries the 158-31 contradiction (`resolution_mode: sealed_letter_lookup` + `win_condition: dial_threshold`, at `tests/fixtures/packs/swn_test_pack/rules.yaml:550`). Plan Task 1 only fixes the *live* space_opera pack. The new Task-5 validator (`validate_rules_in_pack`) would flag the fixture if ever walked over `tests/fixtures/packs`. Affects `tests/fixtures/packs/swn_test_pack/rules.yaml` (migrate to `hp_depletion`, OR scope the validator to live packs). Not blocking — the validator unit test uses a `tmp_path` synthetic, and the seating tests don't depend on the fixture's win_condition.
- **Gap (non-blocking):** `instantiate_encounter_from_trigger` leaks cross-test state on the **uncaught `SealedLetterArityError`** path under `-n0` (it sets `snapshot.encounter = enc` ~line 1625, before the arity gate ~1833). In RED this makes `test_dogfight_default_opponent` perturb later dogfight dispatch tests in a serial run (each is still RED; testing-runner conflated the failure messages). It **resolves post-green** (Plan 1 makes the dogfight seat-from-frame, so no test hits the arity-raise). Affects `sidequest-server/sidequest/server/dispatch/encounter_lifecycle.py` — Dev should confirm the serial dogfight suite is clean after green; consider gating the arity check *before* mutating `snapshot.encounter`. *Found by TEA during test design.*
- **Question (non-blocking):** Task-3's `test_dogfight_default_opponent` asserts the frame-default opponent's durability via `snapshot.find_creature_core(name).hp.max == 8` — this requires the seater to **mint an `Npc` core** from `opponent_default_stats` (the plan's claimed `_seed_combat_hp_depletion_to_npcs` behavior). If GREEN puts frame HP only in `per_actor_state["frame_hp"]` and mints no core, the assertion fails for a real reason: Dev must wire the minted core (the duel needs a resolvable opponent core anyway). *Found by TEA during test design.*

### Dev (implementation)
- **RESOLVED (TEA's Question):** `_seed_combat_hp_depletion_to_npcs` (runs for `win_condition == hp_depletion` combat) DOES mint a backing `Npc` core from `opponent_default_stats` for an unbacked opponent — `find_creature_core("Fighter Duel").hp.max == 8` holds. `test_dogfight_default_opponent` is GREEN. No further action.
- **Gap (non-blocking):** The loud reject-when-truly-unseatable path for a **frameless** dogfight def (no `opponent_default_stats`) now has NO test — the two former reject tests were re-pointed to the §6 frame-default seat (a framed dogfight always seats). All live dogfight defs carry a frame, so this is currently unreachable, but the §7 router→seater "degrade loudly, never wedge" contract (`dogfight.dispatch.rejected`) belongs to **Plan 2 / 158-29** — it should add a frameless-def reject test. Affects `sidequest-server/sidequest/server/dispatch/encounter_lifecycle.py` (the No-Opponent guard) + a Plan-2 test. *Found by Dev during implementation.*
- **Improvement (non-blocking):** The Pilot "Threading the Needle" ability was re-scoped to "Once per chase" (the dangling `bank` dogfight-beat reference was removed). The rebuilt dogfight is beats-less, so the ability no longer offers a dogfight re-fly. Plans 3–4 (dogfight maneuver selection / opponent brain) should decide whether the Pilot's signature re-fly extends to dogfight maneuvers (interaction-table cells) and re-author the ability accordingly. Affects `sidequest-content/genre_packs/space_opera/classes.yaml`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement (non-blocking):** `cdef.label or "Enemy Fighter"` (encounter_lifecycle.py:1763) is a cosmetic display default on a required `str` field. Accepted as-is (mechanical identity is guarded; matches plan spec). Optional cleanup: either add a content invariant that `label` is non-empty (then use `cdef.label` directly) OR keep the default with an inline "cosmetic, not a config fallback" note. Affects `sidequest-server/sidequest/server/dispatch/encounter_lifecycle.py`. *Found by Reviewer during code review.*
- **Gap (non-blocking):** The new `validate/rules.py` checks `win_condition`/native-dial but NOT frame presence — a `sealed_letter_lookup` combat def missing `opponent_default_stats` passes the validator yet fails loud only at runtime (arity guard). Consider adding a validator check that a sealed-letter combat carries an `opponent_default_stats` frame, or fold it into Plan 2's §7 router→seater work. Affects `sidequest-server/sidequest/cli/validate/rules.py`. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

6 deviations

- **Rewrote 3 currently-green Story 59-17 dispatch tests to the ADR-153 §6 contract**
  - Rationale: Plan-1's seater change (Tasks 2–3) drives `run_confrontation_dispatch`; these tests encode the pre-§6 "seat the co-located pilot / refuse when none" contract that §6 deliberately supersedes, so Plan-1 cannot land green without updating them. The plan omitted them from its test accounting (logged as a Delivery Finding). Keith approved this scope on 2026-06-27 (AskUserQuestion: "Per ADR-153 §6; update the 59-17 tests").
  - Severity: major (inverts the contract of accepted, currently-passing tests, incl. removing the ADR-116 "refuse one-sided" behavior in favor of "frame-default IS the Other")
  - Forward impact: ADR-116 for the dogfight path is now satisfied by the def frame, not by a scene NPC. A future change that wants a *named* scene opponent must route it via `npcs_present` (the §7 router→seater contract, Plan 2 / 158-29) — not the deleted location fallback.
- **Included a passing (non-RED) wiring test in the RED commit**
  - Rationale: the firewall (resolve via hp_depletion, never a dial sweep) is the load-bearing invariant of the whole story; omitting its OTEL proof to satisfy "every RED test must fail first" would be worse. RED for the story is established by the other 6 failing tests + 2 erroring validator tests.
  - Severity: minor
  - Forward impact: none — it guards against a future reintroduction of a native dial sweep on the dogfight path.
- **Exempted the sealed-letter dogfight from `_roll_and_persist_initiative`**
  - Rationale: a sealed-letter dogfight is a simultaneous-commit duel resolved by `resolve_dogfight_shots` (geometry + caller-injected d20s) — it has no WN 1d8+DEX turn order and never consumes a persisted initiative. On develop the dogfight was `dial_threshold` and never reached this block; the hp_depletion migration newly triggered it, and it fails loud requiring a PC ability-score lookup the dogfight doesn't use (10 tests regressed on `player actor … not found … cannot resolve DEX`). Exempting it is the root-cause fix, not fixture surgery.
  - Severity: minor (production behavior change, but the dogfight never used WN initiative)
  - Forward impact: Plans 3–4 (dogfight maneuver/opponent-brain) own any dogfight-specific initiative if one is ever wanted; the WN round path is unaffected.
- **Migrated the synthetic `swn_test_pack` fixture dogfight to hp_depletion (not just the live pack)**
  - Rationale: the seating/default-opponent tests load the synthetic fixture (no live content in pytest); the opponent-core minting that `test_dogfight_default_opponent` asserts only fires under `win_condition == hp_depletion`. Leaving the fixture at `dial_threshold` would make it diverge from the live pack and fail the test (TEA flagged this as a Delivery Finding; it proved load-bearing).
  - Severity: minor
  - Forward impact: none — fixture now mirrors the live pack.
- **Removed the orphaned dogfight beats from the Pilot class `encounter_beat_choices` + stale ability prose (both packs)**
  - Rationale: a class `encounter_beat_choices` referencing a beat id removed from rules.yaml fails pack load (`PackError: class 'Pilot' encounter_beat_choices references beat id(s) … not in pool`). The plan's Task 1 Step 2 only checked the sealed-letter *maneuver menu* (interaction table), not the class beat-choice surface.
  - Severity: minor
  - Forward impact: the Pilot's signature ability no longer claims a dogfight re-fly; how the rebuilt dogfight maneuver re-fly works is Plans 3–4 (Delivery Finding below).
- **Updated 3 more superseded sibling tests to the §6/§2 contract (beyond TEA's 3)**
  - Rationale: these encode the pre-§6 "dogfight refuses / keeps a 30-threshold dial" contract that §6/§2 supersede; they surfaced during GREEN (in files TEA didn't touch — exercised via `run_dispatch_bank` / live-YAML calibration). Same reconciliation TEA did for the 3 dispatch tests; the two-npc arity guard stays GREEN (still valid).
  - Severity: major (inverts accepted, currently-passing test contracts)
  - Forward impact: the loud reject-when-truly-unseatable path (a *frameless* dogfight def) now has no test — it is the §7 router→seater contract (Plan 2 / 158-29). See Delivery Finding.

## Sm Assessment

**Routing decision:** User requested 158-29 (Plan 2). On lookup, 158-29's own description requires Plan 1 (firewall, 158-31) be built first, then a live `/sq-playtest` repro before Plan 2 is worked. 158-31 was still `backlog`. User confirmed (2026-06-27) to build **158-31 Plan 1 first**. This story is that prerequisite.

**Scope (from `docs/superpowers/plans/2026-06-26-dogfight-rebuild-plan-1-firewall-seating.md`):** Five tasks —
1. `sidequest-content`: rewrite the space_opera dogfight ConfrontationDef — set `win_condition: hp_depletion`, **DELETE** the native energy dial (`player_metric`/`opponent_metric`) and the `beats` list.
2. `sidequest-server`: enforce ship-scale seating (no ground creature as the enemy ship — closes finding 158-34).
3. `sidequest-server`: provide a default opponent derived from the frame.
4. `sidequest-server`: wire/verify resolution through the existing SWN HP path (`resolve_dogfight_shots` → `check_hp_depletion`).
5. `sidequest-server`: pack-validator rule guarding the new contract.

**DOCTRINE GUARDRAIL (load-bearing — do not violate):** The native dial is being **REMOVED, not repaired.** Do NOT "fix" the zero dial-delta or the one-beat threshold check. Per SOUL *Bind the Ruleset, Don't Balance It* (ADR-143): the SWN engine replaces the native engine for what it covers; we do not tune native mechanics to fit a bound ruleset. If TEA/Dev catches themselves balancing, converting, or gating the native dial — **stop.**

**OTEL:** Per the project observability principle, the seating/degradation decisions on this path must emit watcher events so the GM panel can verify the firewall actually engages (158-26 already added course/dogfight span-name coverage). TEA should assert on these spans where the path is exercised.

**Workflow:** tdd (phased). Next phase: `red` → Igor (TEA) writes failing tests first. Session + story context + epic context all present; Jira disabled (empty key) so claim step skipped intentionally.

## TEA Assessment

**Tests Required:** Yes
**Status:** RED verified (each test confirmed failing/erroring in isolation; develop confirmed green for the rewritten tests)

**Test Files:**
- `tests/fixtures/dogfight_playtest_encounter.py` — added 4 factories: `make_dogfight_pack` (loads synthetic swn_test_pack), `make_empty_snapshot`, `make_snapshot_with_npc` (co-located NPCs), `make_seated_dogfight` (seated PC+opponent cores + edge_resolver). No live-pack content in pytest (`feedback_no_content_in_unit_tests`).
- `tests/server/dispatch/test_dogfight_seating_scale.py` — §6: a co-located *ground* creature is never seated as the enemy ship (158-34). **RED** (today seats "Gengineered Killer").
- `tests/server/dispatch/test_dogfight_default_opponent.py` — §6: no router-named/located Other → seat a default-from-frame ship, core HP 8. **RED** (today raises `SealedLetterArityError`).
- `tests/server/dispatch/test_dogfight_hp_depletion_wiring.py` — §2 firewall OTEL proof: seated dogfight resolves via `hp_depletion`, never `dial_threshold_sweep`. **PASSES** (regression lock — engine already resolves via `check_hp_depletion`).
- `tests/cli/test_dogfight_firewall_validator.py` — Task 5: `validate_rules_in_pack` rejects sealed_letter combat that isn't hp_depletion (the 158-31 contradiction) + accepts the compliant shape + CLI-registration wiring. **RED** (module `sidequest.cli.validate.rules` absent → ModuleNotFoundError; `rules` not in CLI group).
- `tests/server/dispatch/test_dogfight_instantiation_production_path.py` — 3 tests rewritten to §6 + docstring (see Design Deviation). **RED** (today seats the co-located NPC / refuses).

**Tests Written:** 10 test functions + 4 fixtures, covering the single AC (ADR-153 Plan 1 firewall + §6 seating) across all 5 plan tasks. Status: RED (6 fail, 2 error, 2 pass-by-design).

**RED verification (testing-runner `158-31-tea-red`, serial `-n0`):** 6 FAILED + 2 ERROR (validator module absent) + 2 PASSED (the hp_depletion firewall lock + the explicit-`npcs_present` guard — both must stay green). Verified each in isolation: no test false-passes; the rewritten production-path tests are confirmed green on `develop` (so they are genuine RED here, not pre-existing failures). One serial-ordering artifact noted as a Delivery Finding (resolves post-green).

### Rule Coverage (lang-review/python.md)

| Rule | Test(s) / measure | Status |
|------|-------------------|--------|
| #6 Test quality — meaningful assertions | every assertion checks a specific value (actor name, `core.hp.max == 8`, span `source` attr, `out.data == {}`); no `assert True`/bare-truthy | pass |
| #6 Test quality — no vacuous tests | self-checked; the wiring test asserts span presence AND `source` value AND a negative (`!= dial_threshold_sweep`) | pass |
| #8 Unsafe deserialization | validator test writes `rules.yaml` and the validator reads it via `yaml.safe_load` (mirrors `validate.audio`), never `yaml.load` | pass (contract for Dev) |
| CLAUDE.md — every suite needs a wiring test | `test_dogfight_hp_depletion_wiring` (OTEL behavior) + `test_rules_validator_registered_in_cli` (click-registry, not source-text) | pass |
| CLAUDE.md — No Source-Text Wiring Tests | firewall proven via OTEL span assertion; CLI wiring via registry interrogation — no `read_text()`/regex-on-source | pass |

**Rules checked:** 5 of 13 lang-review rules are applicable to test-only changes (the rest target production code Dev will write). **Self-check:** 0 vacuous tests found.

**Handoff:** To Ponder Stibbons (Dev) for GREEN — implement plan Tasks 1–5. Heed the doctrine guardrail (delete the native dial, don't repair it) and the 4 Delivery Findings (esp. the minted-core requirement for default-opponent and the serial-ordering artifact that must be clean post-green).

## Dev Assessment

**Implementation Complete:** Yes
**Tests:** GREEN — 77/77 across the full changed surface (story tests + 3 updated dispatch tests + 3 updated sibling tests + calibration + pack-load + dogfight-shot + integration). Blast-radius regression sweep: 839 passed / 0 failed / 27 skipped (DB-fixture skips, unrelated). RED's two pass-by-design guards (hp_depletion wiring lock + explicit-`npcs_present`) stayed green throughout.

**Files Changed:**

_sidequest-server_ (branch `feat/dogfight-rebuild-firewall`, pushed):
- `sidequest/server/dispatch/encounter_lifecycle.py` — §6 seater: (Task 2) sealed-letter skips the personal location fallback; (Task 3) seats a default enemy ship from `opponent_default_stats` when no Other is router-named; exempts the sealed-letter dogfight from `_roll_and_persist_initiative` (keeps `_seed_combat_hp_depletion_to_npcs` for the opponent core).
- `sidequest/cli/validate/rules.py` (new) — `validate_rules_in_pack` / `validate_packs` / `main`: rejects a `sealed_letter_lookup` combat that isn't `hp_depletion` (Task 5).
- `sidequest/cli/validate/__main__.py` — registers the `rules` subcommand (wiring).
- `tests/fixtures/packs/swn_test_pack/rules.yaml` + `classes.yaml` — fixture dogfight migrated to hp_depletion + Pilot beat-choice/ability cleanup (mirrors the live pack).
- `tests/agents/subsystems/test_dogfight_dispatch_wiring.py`, `tests/server/dispatch/test_sealed_letter_dispatch_integration.py`, `tests/genre/test_confrontation_calibration.py` — 3 superseded sibling tests updated to the §6/§2 contract (see deviations).

_sidequest-content_ (branch `feat/dogfight-rebuild-firewall`, pushed):
- `genre_packs/space_opera/rules.yaml` (Task 1) — dogfight `win_condition: hp_depletion`, native dial + beats deleted.
- `genre_packs/space_opera/classes.yaml` — Pilot `encounter_beat_choices` / ability cleanup (orphaned dogfight beats).

**Plan coverage:** Task 1 (content def + fixture) ✓ · Task 2 (ship-scale gate) ✓ · Task 3 (default-from-frame opponent + minted core) ✓ · Task 4 (hp_depletion OTEL wiring lock) ✓ green · Task 5 (validator + CLI registration) ✓. Live `space_opera` validates clean through `validate rules` (0 errors).

**Doctrine:** Native dial REMOVED, not repaired (SOUL "Bind the Ruleset" / ADR-143). The dogfight resolves through the existing SWN HP path; no dial/beat mechanic was tuned to fit.

**Self-review:** Code wired end-to-end (validator registered in the CLI group; seater changes reachable via `run_confrontation_dispatch`); follows the existing validator + seater patterns; AC met; fail-loud preserved (frameless dogfight still hits the No-Opponent guard).

**Handoff:** To Granny Weatherwax (Reviewer). Scrutiny points: (1) the 6 superseded-test contract inversions (3 TEA + 3 Dev) — confirm each reflects ADR-153 §6/§2 and Keith's 2026-06-27 ruling, not test-gaming; (2) the `_roll_and_persist_initiative` exemption for sealed-letter; (3) the §7 frameless-reject coverage gap deferred to Plan 2 (158-29).

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Rewrote 3 currently-green Story 59-17 dispatch tests to the ADR-153 §6 contract**
  - Spec source: ADR-153 §6 (Opponent is a ship/chassis, never a co-located creature); plan `docs/superpowers/plans/2026-06-26-dogfight-rebuild-plan-1-firewall-seating.md` Tasks 2–3
  - Spec text: "the co-located-NPC fallback can never fire for it … A dogfight requires an Other (ADR-116): if no hostile chassis can be sourced or instantiated, fail loud rather than seat a wrong-scale stand-in" — and Task 2 Step 4: "Story 59-17 enabled the fallback for sealed-letter … Task 3 replaces that with a default-from-frame opponent."
  - Implementation: rewrote `test_dogfight_instantiates_via_router_dispatch_with_scene_opponent` → `…_does_not_conscript_colocated_npc_seats_frame_default`; `…_without_any_opponent_refuses_one_sided` → `…_with_no_scene_opponent_seats_frame_default`; `…_with_only_a_bystander_present_refuses` → `…_with_only_a_bystander_seats_frame_default_not_bystander`. Updated the module docstring. Left `test_dogfight_instantiates_when_opponent_passed_explicitly` unchanged (explicit path is unaffected, stays green).
  - Rationale: Plan-1's seater change (Tasks 2–3) drives `run_confrontation_dispatch`; these tests encode the pre-§6 "seat the co-located pilot / refuse when none" contract that §6 deliberately supersedes, so Plan-1 cannot land green without updating them. The plan omitted them from its test accounting (logged as a Delivery Finding). Keith approved this scope on 2026-06-27 (AskUserQuestion: "Per ADR-153 §6; update the 59-17 tests").
  - Severity: major (inverts the contract of accepted, currently-passing tests, incl. removing the ADR-116 "refuse one-sided" behavior in favor of "frame-default IS the Other")
  - Forward impact: ADR-116 for the dogfight path is now satisfied by the def frame, not by a scene NPC. A future change that wants a *named* scene opponent must route it via `npcs_present` (the §7 router→seater contract, Plan 2 / 158-29) — not the deleted location fallback.
- **Included a passing (non-RED) wiring test in the RED commit**
  - Spec source: plan Task 4; CLAUDE.md "Every Test Suite Needs a Wiring Test" / "No Source-Text Wiring Tests"
  - Spec text: "prove the firewall … the `encounter.resolved` span fires with `source='hp_depletion'` … This test PASSES against the current engine; it locks the firewall against regression."
  - Implementation: `test_dogfight_hp_depletion_wiring.py::test_dogfight_resolves_via_hp_depletion` passes today (the engine already resolves via `check_hp_depletion`). It is a regression lock, not a red→green test.
  - Rationale: the firewall (resolve via hp_depletion, never a dial sweep) is the load-bearing invariant of the whole story; omitting its OTEL proof to satisfy "every RED test must fail first" would be worse. RED for the story is established by the other 6 failing tests + 2 erroring validator tests.
  - Severity: minor
  - Forward impact: none — it guards against a future reintroduction of a native dial sweep on the dogfight path.

### Dev (implementation)
- **Exempted the sealed-letter dogfight from `_roll_and_persist_initiative`**
  - Spec source: plan Tasks 2–4 (did not mention initiative); ADR-153 §2 firewall; SOUL "Bind the Ruleset, Don't Balance It"
  - Spec text: plan is silent on `_roll_and_persist_initiative` — it predates the discovery that migrating the dogfight to hp_depletion pulls it into the generic WN hp_depletion combat-seeding block.
  - Implementation: gated the `_roll_and_persist_initiative(...)` call in `encounter_lifecycle.py` (~line 2228) on `cdef.resolution_mode != ResolutionMode.sealed_letter_lookup`. The dogfight still gets `_seed_combat_hp_depletion_to_npcs` (opponent core for hp_depletion); it skips WN initiative.
  - Rationale: a sealed-letter dogfight is a simultaneous-commit duel resolved by `resolve_dogfight_shots` (geometry + caller-injected d20s) — it has no WN 1d8+DEX turn order and never consumes a persisted initiative. On develop the dogfight was `dial_threshold` and never reached this block; the hp_depletion migration newly triggered it, and it fails loud requiring a PC ability-score lookup the dogfight doesn't use (10 tests regressed on `player actor … not found … cannot resolve DEX`). Exempting it is the root-cause fix, not fixture surgery.
  - Severity: minor (production behavior change, but the dogfight never used WN initiative)
  - Forward impact: Plans 3–4 (dogfight maneuver/opponent-brain) own any dogfight-specific initiative if one is ever wanted; the WN round path is unaffected.
- **Migrated the synthetic `swn_test_pack` fixture dogfight to hp_depletion (not just the live pack)**
  - Spec source: plan Task 1 (named only the live `space_opera` pack)
  - Spec text: "in the space_opera dogfight ConfrontationDef set win_condition: hp_depletion and DELETE the native energy dial … and the beats list."
  - Implementation: applied the same change to `tests/fixtures/packs/swn_test_pack/rules.yaml` (+ the Pilot `encounter_beat_choices`/ability cleanup in its `classes.yaml`).
  - Rationale: the seating/default-opponent tests load the synthetic fixture (no live content in pytest); the opponent-core minting that `test_dogfight_default_opponent` asserts only fires under `win_condition == hp_depletion`. Leaving the fixture at `dial_threshold` would make it diverge from the live pack and fail the test (TEA flagged this as a Delivery Finding; it proved load-bearing).
  - Severity: minor
  - Forward impact: none — fixture now mirrors the live pack.
- **Removed the orphaned dogfight beats from the Pilot class `encounter_beat_choices` + stale ability prose (both packs)**
  - Spec source: plan Task 1 (named only the dogfight def block)
  - Spec text: Task 1 deletes the dogfight `beats:` list; it did not enumerate the class-side consumer.
  - Implementation: removed `straight/bank/loop/kill_rotation` from the `Pilot` class `encounter_beat_choices` and dropped the dangling `bank` from the "Threading the Needle" ability's `mechanical_effect` (re-scoped to "Once per chase") in `genre_packs/space_opera/classes.yaml` and the fixture twin.
  - Rationale: a class `encounter_beat_choices` referencing a beat id removed from rules.yaml fails pack load (`PackError: class 'Pilot' encounter_beat_choices references beat id(s) … not in pool`). The plan's Task 1 Step 2 only checked the sealed-letter *maneuver menu* (interaction table), not the class beat-choice surface.
  - Severity: minor
  - Forward impact: the Pilot's signature ability no longer claims a dogfight re-fly; how the rebuilt dogfight maneuver re-fly works is Plans 3–4 (Delivery Finding below).
- **Updated 3 more superseded sibling tests to the §6/§2 contract (beyond TEA's 3)**
  - Spec source: ADR-153 §6/§2; Keith ruling 2026-06-27 ("Per ADR-153 §6; update the 59-17 tests")
  - Spec text: §6 "the co-located-NPC fallback can never fire for it"; §2 firewall removes the native dial.
  - Implementation: `test_sealed_letter_dispatch_integration.py::test_dogfight_instantiation_rejects_zero_npcs` → `…_seats_default_ship_from_frame` (zero npcs now seats a frame default, not arity-reject); `test_dogfight_dispatch_wiring.py::test_dogfight_no_opponent_rejects_loud` → `…_seats_frame_default` (framed dogfight seats via the dispatch bank, no reject span); `test_confrontation_calibration.py::test_sealed_letter_thresholds_unchanged` → `test_sealed_letter_combat_has_no_native_dial` (asserts the firewall: a sealed-letter combat carries no player_metric/opponent_metric and is hp_depletion), removing the now-dead `SEALED_LETTER_THRESHOLD` constant.
  - Rationale: these encode the pre-§6 "dogfight refuses / keeps a 30-threshold dial" contract that §6/§2 supersede; they surfaced during GREEN (in files TEA didn't touch — exercised via `run_dispatch_bank` / live-YAML calibration). Same reconciliation TEA did for the 3 dispatch tests; the two-npc arity guard stays GREEN (still valid).
  - Severity: major (inverts accepted, currently-passing test contracts)
  - Forward impact: the loud reject-when-truly-unseatable path (a *frameless* dogfight def) now has no test — it is the §7 router→seater contract (Plan 2 / 158-29). See Delivery Finding.

### Reviewer (audit)
- **TEA: rewrote 3 Story 59-17 dispatch tests to §6** → ✓ ACCEPTED by Reviewer: verified against ADR-153 §6 ("the co-located-NPC fallback can never fire for it") + Keith's 2026-06-27 AskUserQuestion ruling. The rewrites assert positive §6 behavior (frame-default seated, co-located NPC NOT seated) — not weakened "no-error" checks. `test_dogfight_instantiates_when_opponent_passed_explicitly` correctly left unchanged. Not test-gaming.
- **TEA: included a passing (non-RED) wiring test** → ✓ ACCEPTED: the hp_depletion OTEL lock is the load-bearing firewall proof (CLAUDE.md "every suite needs a wiring test" / "No Source-Text Wiring Tests"). A passing characterization test is correct here; RED was established by the other 8 tests.
- **Dev: exempted sealed-letter from `_roll_and_persist_initiative`** → ✓ ACCEPTED: verified — `_seed_combat_hp_depletion_to_npcs` runs unconditionally (encounter_lifecycle.py:2219) and only `_roll_and_persist_initiative` is gated (line ~2237). A simultaneous-commit dogfight (resolve_dogfight_shots, caller-injected d20s) genuinely has no WN turn order. Root-cause fix, not fixture surgery. Silent-failure-hunter independently confirmed the seeding still runs.
- **Dev: migrated the swn_test_pack fixture to hp_depletion** → ✓ ACCEPTED: required — the opponent-core minting `test_dogfight_default_opponent` asserts only fires under hp_depletion (verified: `_seed_combat_hp_depletion_to_npcs` gated at line 2206). Fixture now mirrors the live pack; preflight confirms both load `hp_depletion`.
- **Dev: removed orphaned dogfight beats from the Pilot class + ability prose** → ✓ ACCEPTED: required for pack load (a class `encounter_beat_choices` referencing a deleted beat is a load-time `PackError`). Verified only the Pilot referenced them; chase/ship beats (burn/asteroid_thread/microjump/evasive_maneuver) correctly retained. Preflight pack-load GREEN.
- **Dev: updated 3 more superseded sibling tests to §6/§2** → ✓ ACCEPTED: same §6/§2 supersession as TEA's, in files exercised via `run_dispatch_bank`/live-YAML calibration that TEA couldn't see at RED. Verified the calibration repurpose is NON-VACUOUS (space_opera's dogfight is a real sealed-letter combat it checks) and the two-npc arity guard stays GREEN. The `SEALED_LETTER_THRESHOLD` removal is clean (no other consumer).

## Story Context

**Overview:** Remove the native energy-dial graft from the dogfight confrontation definition and make it resolve correctly via the bound SWN engine's `hp_depletion` mechanism. This closes findings 158-31 (mechanically inert dial) and 158-34 (ground creature seated as the enemy ship).

**Implementation Plan:** See `docs/superpowers/plans/2026-06-26-dogfight-rebuild-plan-1-firewall-seating.md` — five tasks across `sidequest-content` (rewrite the dogfight def) and `sidequest-server` (enforce ship-scale seating, add default opponent, wire HP resolution, add validator guard).

**Architecture Reference:** ADR-153 (Ace-of-Aces dogfight with Ace-of-Aces positioning feeding bound SWN resolution; firewall = positioning emits geometry + gun_solution only; SWN owns hull/hit/kill).

**Branch Strategy:** trunk-based for orchestrator (branching skipped — work happens on main). Subrepos (sidequest-server, sidequest-content) use gitflow with shared feature branches: `feat/dogfight-rebuild-firewall` per plan spec.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (73/73 tests pass; validator 0 errors/11 packs; 3 pre-existing E402 in tests/dungeon/conftest.py — not this diff) | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 (label-or-default MED; fixture None-resolver LOW) | confirmed 1 (downgraded to LOW), dismissed 1 |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — covered by Reviewer (test-quality enumerated below) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none | confirmed 0, dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — covered by Reviewer (Rule Compliance below) |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 1 confirmed (LOW), 1 dismissed (with rationale), 0 deferred

### Rule Compliance (lang-review/python.md + CLAUDE.md/SOUL.md)

Enumerated against every changed Python symbol (`encounter_lifecycle.py` seater branches, `validate/rules.py`, `validate/__main__.py`, updated tests):

| Rule | Instances checked | Verdict |
|------|-------------------|---------|
| #1 Silent exception swallowing | `rules.py` catches `(UnicodeDecodeError, yaml.YAMLError)` specifically → records `RULES_LOAD_FAILURE` (not swallowed) | compliant |
| #3 Type annotations at boundaries | `validate_rules_in_pack(pack_dir: Path) -> ValidationResult`, `validate_packs(list[Path]) -> ValidationResult`, `main(...) -> None` all annotated | compliant |
| #5 Path handling | `pack_dir / "rules.yaml"` (pathlib); `read_text(encoding="utf-8")` explicit; `click.Path(exists=True, file_okay=False, path_type=Path)` | compliant |
| #6 Test quality (test_analyzer OFF — Reviewer-covered) | all updated tests assert specific values (encounter not None, opponent count==1, actor names, span names, `core.hp.max==8`); calibration repurpose verified non-vacuous (checks space_opera's real dogfight); no `assert True`/bare-truthy; two-npc arity guard retained | compliant |
| #8 Unsafe deserialization | `yaml.safe_load` (never `yaml.load`); test fixtures use `tmp_path`+`write_text`, no pickle/eval | compliant |
| #10 Import hygiene | explicit imports; `__all__` on `rules.py`; no star imports; function-local `NpcMention` import mirrors existing seater pattern | compliant |
| #11 Input validation at boundaries | CLI `--genre-packs-root` validated by `click.Path(exists=True, file_okay=False)` | compliant |
| No Silent Fallbacks (CLAUDE.md <critical>) | frame-default branch only fires with `cdef.opponent_default_stats`; frameless def → arity guard fails loud (verified). One cosmetic `or "Enemy Fighter"` display-default — see [SILENT] below | 1 LOW note, else compliant |
| Bind the Ruleset, Don't Balance It (SOUL/ADR-143) | native dial (player_metric/opponent_metric/beats) DELETED, not tuned; resolves via SWN hp_depletion | compliant |
| OTEL observability (CLAUDE.md) | frame-default seat rides the existing `participant.joined` span (source="frame_default"); hp_depletion resolution emits `encounter.resolved` source=hp_depletion (wiring test locks it) | compliant |

**Rules checked:** 10 applicable rule classes, every changed symbol enumerated. **Self-check:** 0 vacuous tests, 0 source-text wiring tests.

### Observations

- [VERIFIED] The two seater branches are mutually exclusive — location-fallback requires `resolution_mode != sealed_letter_lookup` (encounter_lifecycle.py:1729), frame-default requires `== sealed_letter_lookup` (:1748). No overlap, no double-seat.
- [VERIFIED] A frameless sealed-letter dogfight fails loud — the frame-default `elif` requires `cdef.opponent_default_stats` (:1749); when absent, `npcs_present` stays `[]` and the sealed-letter arity guard raises `SealedLetterArityError` (:1825-1837). Confirmed by silent-failure-hunter + security subagent + my trace.
- [VERIFIED] The dogfight opponent core is seeded — `_seed_combat_hp_depletion_to_npcs` runs at :2219 (mints `Npc` core, hp from `opponent_default_stats`=8); only `_roll_and_persist_initiative` is gated out at :2237. `test_dogfight_default_opponent` (find_creature_core.hp.max==8) GREEN.
- [VERIFIED] Doctrine honored — `space_opera/rules.yaml` deletes `player_metric`/`opponent_metric`/`beats`, sets `win_condition: hp_depletion`; no dial tuned to fit (SOUL Bind-the-Ruleset). Preflight: both packs load hp_depletion.
- [VERIFIED] Validator wired end-to-end — `rules` registered in the CLI group (`__main__.py` `cli.add_command(rules_main, name="rules")`); `test_rules_validator_registered_in_cli` asserts `"rules" in cli.commands`; preflight ran `python -m sidequest.cli.validate rules` → 0 errors over 11 live packs. Not a source-text wiring test.
- [SILENT] `cdef.label or "Enemy Fighter"` (encounter_lifecycle.py:1763) — **LOW** (downgraded from silent-failure-hunter's MED). `ConfrontationDef.label` is a required `str` (rules.py:476), so the `or` only triggers on the degenerate empty-string case; it is a cosmetic DISPLAY default for a generated frame-default opponent, NOT a fallback masking a load-bearing config error (the opponent's mechanical identity — hp/ac — comes from `opponent_default_stats`, which IS guarded and fails loud when absent). It also matches the plan's Task 3 spec verbatim. Accepted as a deliberate cosmetic default; non-blocking. Optional follow-up logged as a Delivery Finding.
- [SILENT] (dismissed) Fixture `make_seated_dogfight._resolver` returns `None` for unknown names (tests/fixtures/dogfight_playtest_encounter.py) — **DISMISSED**: this IS the documented resolver contract — `check_hp_depletion` explicitly handles a None core (`if core is None: continue`, hp_depletion.py:73-74), and it mirrors the canonical `test_resolve_dogfight_shots.py` (`lambda n: cores.get(n)`) and production `frame_hp_resolver`. Not a defect.
- [SEC] (clean) No injection/deserialization/path surface — `yaml.safe_load` + explicit encoding + `click.Path` validation; content-derived names reach only internal game state, no sensitive sink. reviewer-security: 0 findings.
- [TEST] (Reviewer-covered, test_analyzer disabled) The 6 contract-inverted tests assert positive §6/§2 behavior and are non-vacuous; the wiring test + validator registration test are refactor-stable (OTEL span / click-registry, not source grep).
- [EDGE]/[DOC]/[TYPE]/[SIMPLE]/[RULE] — subagents disabled; covered by Reviewer's own Rule Compliance + Devil's Advocate enumeration. No edge/type/complexity/rule violations found in the changed symbols.

### Devil's Advocate

Assume this is broken. The loudest worry: a dogfight now **always** seats — a framed def can never refuse — so the engine will conjure a generic "Fighter Duel" out of empty space. A narrator stages a named ace ("Vulture dives at you"); the router fails to pass the name via `npcs_present`; the player engages and fights a faceless frame default instead of Vulture. That is a real Diamonds-and-Coal / Living-World regression — but it is the **accepted Plan-1 scope**: ADR-153 §7 (router *naming* the opponent) is Plan 2 (158-29), and Keith ruled to proceed per §6 on 2026-06-27. Not a Plan-1 defect; the named-opponent path still works when the router does pass `npcs_present`. Next: an empty-string `label` → "Enemy Fighter" (the LOW finding) — cosmetic, mechanical identity intact. Next: `opponent_default_stats: {}` (truthy-looking but empty) → falsy in Python, so the frame-default `elif` is skipped → arity guard fails loud; and even if it seated, `cdef.opponent_hp is None` → the sealed-letter HP-seeding block raises `ValueError` (frame HP missing). Both fail loud — good. Next: name collision — two dogfights in one scene both label "Fighter Duel"? `_seed_combat_hp_depletion_to_npcs` does a by-name lookup and would reuse the existing Npc; an edge case but not corrupting. Next: a confused author removes `opponent_default_stats` from the live def → pack still loads, but a dogfight then fails loud at seat time (arity) AND the new validator flags nothing (the validator checks win_condition, not frame presence) — a small gap, but the runtime fail-loud covers it. Next: did the contract inversions hide a real regression? The blast-radius sweep (839 passed/0 failed) and preflight (73/73) say no; the two-npc arity guard and the explicit-`npcs_present` path stayed green, proving the fail-loud and named-opponent paths are intact. Nothing here rises to Critical/High.

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** a ship-combat verb → `run_confrontation_dispatch` → `instantiate_encounter_from_trigger` with `npcs_present=[]` → sealed-letter skips the personal location fallback (:1729) → frame-default `elif` seats `NpcMention(cdef.label, side="opponent")` from `opponent_default_stats` (:1746-1767) → `_seed_combat_hp_depletion_to_npcs` mints the opponent core hp=8 (:2219) → duel resolves via `resolve_dogfight_shots` → `check_hp_depletion` emits `encounter.resolved` source=`hp_depletion`. Safe: the co-located creature is never reachable as the Other (158-34 closed); a frameless def fails loud (ADR-116 preserved).

**Pattern observed:** the new `validate/rules.py` faithfully mirrors the existing `validate/audio.py` submodule (local Issue/ValidationResult, `validate_<domain>_in_pack` + `validate_packs` + click `main`, raw `yaml.safe_load` of rules.yaml) and is registered in the CLI group like its siblings — `sidequest/cli/validate/__main__.py:36`.

**Error handling:** load failures → `RULES_LOAD_FAILURE` (not swallowed); frameless/zero-opponent dogfight → loud `SealedLetterArityError`; missing frame HP → loud `ValueError` at seat time — all fail-loud per No-Silent-Fallbacks.

**Subagent dispatch:** [EDGE] disabled — Reviewer-covered (Devil's Advocate boundary enumeration, no issue) · [SILENT] 1 confirmed LOW (`label` cosmetic default), 1 dismissed (resolver None is the documented contract) · [TEST] disabled — Reviewer-covered (6 inversions verified meaningful + non-vacuous) · [DOC] disabled — comments updated coherently with the change (verified in diff) · [TYPE] disabled — Reviewer-covered (annotations present, no stringly-typed regressions) · [SEC] clean (0 findings) · [SIMPLE] disabled — Reviewer-covered (validator mirrors sibling, no over-engineering) · [RULE] disabled — Reviewer-covered (10 rule classes enumerated, compliant).

**Findings:** 0 Critical, 0 High, 0 Medium, 1 Low (cosmetic label default — non-blocking, optional follow-up). Pre-existing lint debt (E402 in tests/dungeon/conftest.py) is not this diff's.

**Handoff:** To Captain Carrot Ironfoundersson (SM) for finish-story.