---
story_id: "157-2"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 157-2: [ENGINE] zone_eligibility core + factions tag + creature inject filter (Seam 1)

## Story Details
- **ID:** 157-2
- **Jira Key:** (none — YAML-only epic)
- **Workflow:** tdd
- **Stack Parent:** 157-1 (design phase complete)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-21T00:48:31Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-20T23:25:59Z | 2026-06-20T23:28:01Z | 2m 2s |
| red | 2026-06-20T23:28:01Z | 2026-06-20T23:42:06Z | 14m 5s |
| green | 2026-06-20T23:42:06Z | 2026-06-21T00:05:45Z | 23m 39s |
| review | 2026-06-21T00:05:45Z | 2026-06-21T00:19:10Z | 13m 25s |
| green | 2026-06-21T00:19:10Z | 2026-06-21T00:33:55Z | 14m 45s |
| review | 2026-06-21T00:33:55Z | 2026-06-21T00:48:31Z | 14m 36s |
| finish | 2026-06-21T00:48:31Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

### TEA (test design)
- **Gap** (blocking): The pregen seed-time union-stamp that POPULATES `encounter.factions` (= union of source bestiary entries' `factions`) is required by the design but has no RED unit test (CLI-bound — see Design Deviations).
  Affects `sidequest/server/dispatch/pregen.py` (`seed_manual` / `_generate_encounter` / the `manual.add_encounter(...)` call at ~L464 must thread `factions`). Without it, production `encounter.factions` is always empty and Seam 1's filter is a no-op in real play even though the seam tests pass on synthetic tagged encounters.
  *Found by TEA during test design.*
- **Improvement** (non-blocking): The injection seam currently resolves combat/zone state from the free-text `current_location` string; per the design's "Resolution note", zone eligibility MUST resolve from `snapshot.region_for(perspective)` → region `controlled_by`, NOT `current_location` (which may be a POI/scene string). The new `zone_eligibility.active_factions(snapshot, pack, *, perspective)` owns this; the seam passes the snapshot.
  Affects `sidequest/server/dispatch/monster_manual_inject.py` (`_npc_patches_for_encounters` / `inject` wiring).
  *Found by TEA during test design.*
- **Question** (non-blocking): The expected `pack`→cartography accessor in `active_factions` was chosen as `pack.worlds[snapshot.world_slug].cartography` to match the established `pregen._seed_authored_npcs` convention (`pack.worlds[slug]`, `World.cartography`). If Dev resolves cartography through a different/layered accessor (e.g. an `effective_cartography`), update the unit-test pack stand-in accordingly — none exists today (only `effective_cultures/archetypes/bestiary`).
  Affects `sidequest/game/zone_eligibility.py` (new) + `tests/game/test_zone_eligibility.py`.
  *Found by TEA during test design.*

### Dev (implementation)
- **Resolved** (TEA blocking finding): the pregen union-stamp IS implemented — `pregen.seed_manual` now resolves `pack.effective_bestiary(world)` once and stamps `encounter.factions` = union of the source enemies' bestiary factions (join by name). Production encounters are now tagged; Seam 1 has real data to filter on. Verified for real by 157-5.
- **Confirmed** (TEA Question finding): the `pack`→cartography accessor is `pack.worlds[snapshot.world_slug].cartography`, exposed as the shared `zone_eligibility.cartography_for`. There is no `effective_cartography` (only effective_cultures/archetypes/bestiary), so no layered accessor was needed.
- **Gap** (non-blocking, PRE-EXISTING — not introduced by 157-2): 7 tests fail on a separate ADR-145/114-15 inventory-provenance validator at *pack load*, NOT on anything 157-2 touched: `test_pregen_fail_loud_90_5.py` (3), `test_pregen_combat_gate.py` (1), `tests/cli/test_encountergen_bestiary_90_1.py` (3). Error: "genre-tier baseline carries non-verbatim unprovenanced item(s) [ancient_artifact, crossbow_salvage, …]: a 'swn' pack's genre catalog … must be mode=verbatim (ADR-145 D3)". Offending items live in `tests/fixtures/packs/test_genre/inventory.yaml`; the validator (`sidequest/game/inventory_resolve.py`) + fixture both last changed 2026-06-15 (#895 "114-15") — 5 days BEFORE this branch's base (9d7303fa, 2026-06-20). My changeset touches zero inventory/validator/fixture files (verified via `git status`), and the failure is upstream of every line I changed. Fixing it is an ADR-145 provenance judgment (verbatim vs derived for those salvage items) on a shared fixture, out of scope for 157-2.
  Affects `tests/fixtures/packs/test_genre/inventory.yaml` (genre-tier inventory items need ADR-145 `mode:` provenance for the SWN-pack validator). Recommend a small ADR-145 fixture-hygiene story.
  *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): The pregen union-stamp `_encounter_factions` (populates production `encounter.factions`) has zero test coverage — all pregen tests stub `effective_bestiary→(None)`. A join/union regression ships green and re-opens the gulliver bleed. The "CLI-bound" excuse is false for this pure helper.
  Affects `sidequest/server/dispatch/pregen.py` + `tests/server/dispatch/test_pregen.py` (add direct `_encounter_factions` unit tests + `add_encounter(factions=)` threading). *Found by Reviewer during code review.*
- **Gap** (non-blocking): Untested invariants — `"*"` sentinel through `inject()`, out-of-combat filter-before-cap ordering, `FLAT_ONLY_SPANS` registration of `SPAN_ZONE_ELIGIBILITY_FILTERED` (+ import the constant instead of re-declaring it), the filtered-span forensic attribute shape (assert `content_id`/`content_factions`/`active_factions` by key), and `world_is_zoned(None)`.
  Affects `tests/server/dispatch/test_zone_eligibility_seam.py` + `tests/game/test_zone_eligibility.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `world_is_zoned` docstring overclaims a cache that doesn't exist; `inject()` redundantly resolves cartography + region twice/turn. Either add the per-world cache the docstring promises, or correct the docstring and resolve once.
  Affects `sidequest/game/zone_eligibility.py:39` + `sidequest/server/dispatch/monster_manual_inject.py:557-559`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Stale "FAIL today / RED tests" docstrings (impl ships in the same diff) + `otel_capture` test params lack typed annotations.
  Affects `tests/game/test_zone_eligibility.py`, `tests/server/dispatch/test_zone_eligibility_seam.py`. *Found by Reviewer during code review.*

#### Reviewer (code review — round 2, re-review)
- **Improvement** (non-blocking): The seed-path wiring `seed_manual → effective_bestiary → _encounter_factions → add_encounter(factions=)` is unit-tested in pieces but no test drives `seed_manual` end-to-end with a non-`None` bestiary asserting the union actually lands on `ManualEncounter.factions`; the e2e fixture test (`test_e2e_seed_fixture_world_populates_manual`) asserts only the `enemies` list shape. The design names content story **157-5** ("tag gulliver … verify no Yahoo bleed") as the e2e proof — 157-5's acceptance MUST assert `encounter.factions` is actually stamped (and a real Yahoo is filtered), not merely that the narration doesn't mention a Yahoo. Affects `tests/server/dispatch/test_pregen.py` + the 157-5 acceptance. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `ManualNpc.factions` carries no runtime data yet — its docstring describes the **157-3** origin-stamp-on-activation mechanism in present tense as if shipped. 157-3 (the NPC injection seam) is the consumer; it should both implement the origin-stamp and correct the docstring to drop the present-tense overclaim. Affects `sidequest/game/monster_manual.py` (`ManualNpc.factions`) + story 157-3. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

3 deviations

- **No RED unit test for the pregen factions-stamp (encounter.factions = union of source bestiary factions)**
  - Rationale: that path is encountergen-**CLI**-driven (`_run_cli_capturing_json(encountergen_main, ...)`); a RED test would require either invoking the gated CLI or heavily mocking seed_manual internals (the enemy→bestiary-entry back-mapping is not a stable seam). Its end-to-end effect is the explicit acceptance proof of content story **157-5** ("tag gulliver … verify no Yahoo bleed").
  - Severity: minor
  - Forward impact: Dev MUST still implement the union-stamp per the design (otherwise production `encounter.factions` is always empty and Seam 1 has nothing to filter on). Captured as a blocking Delivery Finding for Dev + flagged for Reviewer. Verified for real in 157-5.
- **Pregen factions-stamp joins enemy→bestiary by NAME, not creature_id**
  - Rationale: the design assumed a "source bestiary entries" link without specifying the key; the only one that exists in the encountergen output is the name. Native packs (no bestiary) / unmatched names → empty (eligible everywhere).
  - Severity: minor
  - Forward impact: if a future story adds `creature_id` to the encountergen enemy block, switch the join to id for robustness against name collisions. Verified end-to-end by 157-5's no-bleed proof.
- **Added a 4th public helper `cartography_for(snapshot, pack)` to zone_eligibility**
  - Rationale: directly serves the design's "no seam re-derives anything"; additive, no behavior change.
  - Severity: trivial
  - Forward impact: 157-3/157-4 should reuse `cartography_for` rather than re-implementing the pack→cartography lookup.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

### TEA (test design)
- **No RED unit test for the pregen factions-stamp (encounter.factions = union of source bestiary factions)**
  - Spec source: 2026-06-20-faction-zone-content-eligibility-design.md, "Seam 1" + "Story breakdown" (157-2 = "Manual propagation")
  - Spec text: "`_generate_encounter()` (pregen) stamps an encounter's `factions` = union of its source bestiary entries' `factions`."
  - Implementation: Tests pin the `factions` FIELD on `BestiaryEntry`/`ManualEncounter`/`ManualNpc` and the Seam-1 *consumption* of `encounter.factions` (via `inject()`), but do NOT unit-test the seed-time union computation in `pregen.seed_manual`/`_generate_encounter`.
  - Rationale: that path is encountergen-**CLI**-driven (`_run_cli_capturing_json(encountergen_main, ...)`); a RED test would require either invoking the gated CLI or heavily mocking seed_manual internals (the enemy→bestiary-entry back-mapping is not a stable seam). Its end-to-end effect is the explicit acceptance proof of content story **157-5** ("tag gulliver … verify no Yahoo bleed").
  - Severity: minor
  - Forward impact: Dev MUST still implement the union-stamp per the design (otherwise production `encounter.factions` is always empty and Seam 1 has nothing to filter on). Captured as a blocking Delivery Finding for Dev + flagged for Reviewer. Verified for real in 157-5.
  - → ✗ **FLAGGED by Reviewer:** the *premise* (encountergen-CLI-bound, "not a stable seam") did not survive implementation. Dev extracted a pure `_encounter_factions(data, bestiary)` helper that is trivially unit-testable WITHOUT the CLI — so the "can't RED-test it" justification no longer holds, and the helper shipped with zero coverage. This is the HIGH blocking finding in the Reviewer Assessment. The RED tests TEA deferred are now required (and cheap). 157-5's e2e proof is a good *additional* check but is not a substitute for unit coverage of the join/union logic (a decorated-name regression would pass 157-5's single happy path but break real worlds).

### Dev (implementation)
- **Pregen factions-stamp joins enemy→bestiary by NAME, not creature_id**
  - Spec source: 2026-06-20-faction-zone-content-eligibility-design.md, "Seam 1"
  - Spec text: "`_generate_encounter()` (pregen) stamps an encounter's `factions` = union of its source bestiary entries' `factions`."
  - Implementation: `pregen._encounter_factions(data, bestiary)` unions by matching each enemy's `name` (case-insensitive) to `BestiaryEntry.name`, because `encountergen.generate_enemy_from_bestiary` sets `class_="creature"` and carries NO `creature_id`/id — the enemy name (copied verbatim from `entry.name`) is the only stable join key back to the bestiary.
  - Rationale: the design assumed a "source bestiary entries" link without specifying the key; the only one that exists in the encountergen output is the name. Native packs (no bestiary) / unmatched names → empty (eligible everywhere).
  - Severity: minor
  - Forward impact: if a future story adds `creature_id` to the encountergen enemy block, switch the join to id for robustness against name collisions. Verified end-to-end by 157-5's no-bleed proof.
  - → ✓ **ACCEPTED by Reviewer:** name is genuinely the only join key (rule-checker + comment-analyzer confirmed encountergen emits no creature_id; `class_="creature"` literal). Sound choice. CAVEAT (Devil's Advocate #1): the join is fragile to a future encountergen name-decoration change and MUST be pinned by the missing `_encounter_factions` unit test (see HIGH finding) so a silent drop-to-untagged regression is caught.
- **Added a 4th public helper `cartography_for(snapshot, pack)` to zone_eligibility**
  - Spec source: same design, "The four application seams" ("a thin call into a new `zone_eligibility.py`. No seam re-derives anything.")
  - Spec text: lists `world_is_zoned` / `active_factions` / `is_eligible`.
  - Implementation: also exposed `cartography_for(snapshot, pack)` (was going to be private) so Seam 1 — and the 157-3/157-4 seams — resolve the world's cartography through ONE accessor instead of re-deriving `pack.worlds[slug].cartography` each.
  - Rationale: directly serves the design's "no seam re-derives anything"; additive, no behavior change.
  - Severity: trivial
  - Forward impact: 157-3/157-4 should reuse `cartography_for` rather than re-implementing the pack→cartography lookup.
  - → ✓ **ACCEPTED by Reviewer:** directly serves the design's "no seam re-derives anything." Additive, no behavior change, no new public-API risk. Good call.

### Reviewer (audit)
- **Seam 1 resolves the active faction party-globally (`perspective=None`), not per-perspective:** Spec said (design "Seam 1" / "Active-faction resolver") creature injection is a *per-perspective* seam that "passes the perspective"; code calls `active_factions(snapshot, pack)` with no perspective, yielding the party UNION. Not logged by Dev. Severity: LOW. → ✓ ACCEPTED with rationale: `inject()` materializes into a SHARED `snapshot.npcs` (it cannot filter per-recipient there), so the union is the only coherent choice — and it is the *more permissive* one (fail-toward-showing). For a single-zone party (the common case + the gulliver bug) union == per-perspective, so the fix is unaffected. Forward note for 157-3 (the NPC seam, same file): decide perspective-threading deliberately and consistently; if true per-recipient creature/NPC filtering is ever wanted it needs ADR-105 broadcast-layer work, out of scope here.
- **Out-of-combat filter-before-cap ordering** is a real behavioral invariant Dev introduced (documented in the `_npc_patches_for_encounters` docstring) but did not call out as a deviation/decision and did not test. Severity: LOW (logged as a MEDIUM test-coverage finding, not a spec deviation). No stamp needed beyond the test requirement.

#### Reviewer (audit — round 2, re-review)
- **TEA's FLAGGED "can't RED-test `_encounter_factions`" deviation → ✓ RESOLVED.** The round-0 FLAG required the deferred RED tests once the pure `_encounter_factions(data, bestiary)` helper was extracted. The rework (`148875b8`) added 8 direct unit tests + the `add_encounter(factions=)` threading test. The flagged premise is now fully retired — the join/union/sort/no-match/None-bestiary/malformed-row paths all execute. No outstanding FLAG.
- **New undocumented deviation (Dev, round 1): the `inject()` efficiency-gating change.** The rework rewrote the unconditional `zone_active = active_factions(snapshot, pack)` into the gated `if zoned and combat_encounters and manual is not None:` form (empty `set()`/`""` defaults otherwise). Dev mentioned it only as a one-line [LOW] efficiency pairing, not as a logged Design Deviation. → ✓ **ACCEPTED by Reviewer (audit):** I walked every branch — the empty defaults are a provable no-op (`is_eligible` short-circuits permissive on `zoned=False`; `_npc_patches_for_encounters` is itself gated `if combat_encounters else []`; `manual is None` skips the whole block). Behavior-preserving for the 11 single-zone worlds and every pre-bind/quiet turn; the exclusion path on a zoned/combat turn is unchanged. Sound. Severity: trivial (no spec impact). Forward note: 157-3 (the NPC seam in the same file) should reuse the now-resolved `zoned/active/region` locals rather than re-deriving.

## Sm Assessment

**Story:** 157-2 — zone_eligibility core + factions tag + creature inject filter (Seam 1).
First implementation slice of epic-157. Design (157-1) is complete; ADR-059 amendment
is accepted. This is the foundational seam that 157-3 and 157-4 build on.

**Scope (server only):**
- New module `sidequest/game/zone_eligibility.py`:
  - `is_eligible(content_factions, active_factions, *, zoned)` — core predicate.
  - `active_factions(snapshot, pack, *, perspective=None)` — split-party-safe resolver.
- Add `factions: list[str]` to `BestiaryEntry` and `ManualEncounter`.
- Wire into Seam 1: `monster_manual_inject._npc_patches_for_encounters()`.
- OTEL: emit `zone_eligibility.filtered` on each exclusion (lie-detector for the GM panel —
  this is a Keith/dev observability emit, not a player-facing surface).

**Key invariants for TEA to pin in RED:**
- Untagged content with `zoned=False` stays eligible everywhere (no regression for
  single-region worlds — the default must not silently exclude).
- Reference fixture: the Yahoo encounter (Houyhnhnm faction) is FILTERED OUT when the
  party is in Lilliput, INCLUDED when in Houyhnhnm-land.
- Split-party: `active_factions` must resolve per-perspective, not collapse the party to
  one zone.
- **No silent fallbacks** — an unrecognized/missing faction config must fail loudly, not
  default-allow. (Strict load validation itself is 157-7; here just don't paper over it.)

**Doctrine flags:** OTEL emit is mandatory per the project's lie-detector principle — every
subsystem decision (each exclusion) must be observable. Watch for the No-Stubbing rule:
`zone_eligibility.py` must be wired into the inject path in THIS story, not left as a
standalone module for a later seam.

**Handoff:** Phased/tdd → TEA (Amos Burton) for RED. No Jira (YAML-only epic). No
permission gates on tdd.

---
## TEA Assessment

**Tests Required:** Yes
**Status:** RED (failing — ready for Dev)

**Test Files:**
- `sidequest-server/tests/game/test_zone_eligibility.py` — pure-logic core: `world_is_zoned`, the `is_eligible` truth table (8 cases), the split-party-safe `active_factions` resolver, and the additive `factions` content tag on `BestiaryEntry`/`ManualEncounter`/`ManualNpc` (default-empty + per-instance isolation).
- `sidequest-server/tests/server/dispatch/test_zone_eligibility_seam.py` — Seam 1 wiring: drives the real `inject()`, asserts the Houyhnhnm Yahoo is dropped on the Lilliput shore (and present in Houyhnhnm-land), selective filtering, untagged-permissive, unzoned/unresolvable do-not-suppress, and the `zone_eligibility.filtered` OTEL span (fires on exclusion, silent when eligible).

**Tests Written:** 30 (20 core + 10 seam) covering the design spec's contract for 157-2.

**RED verified (Machine Shop / testing-runner):**
- `test_zone_eligibility.py` → collection ERROR: `ModuleNotFoundError: sidequest.game.zone_eligibility` (the module doesn't exist yet — correct RED).
- `test_zone_eligibility_seam.py` → 9/9 fail at fixture construction: `ManualEncounter` rejects `factions=` (`extra_forbidden`) because the field isn't added yet — correct RED at the model-contract layer. Once `factions` lands, the behavior + span tests drive the filter (the headline `test_inject_drops_wrong_zone_encounter` / `test_inject_filters_selectively_*` / `test_inject_emits_filtered_span_*` are the go-green targets; the unzoned/unresolvable/untagged/in-zone tests are regression guards).
- Collection sanity: no fixture/import bugs introduced; failures are 100% feature-absence, not test-infra.

### Rule Coverage (.pennyfarthing/gates/lang-review/python.md)

| Rule | Test(s) | Status |
|------|---------|--------|
| #2 mutable default args | `test_bestiary_entry_factions_not_shared_between_instances`, `test_manual_encounter_factions_not_shared_between_instances` | RED |
| #1 no silent fallback (fail toward showing, not silent-empty) | `test_is_eligible_unresolvable_region_does_not_suppress`, `test_inject_unresolvable_region_does_not_suppress`, `test_active_factions_*_is_empty` | RED |
| OTEL principle (every subsystem decision emits a span) | `test_inject_emits_filtered_span_on_exclusion`, `test_inject_no_filtered_span_when_eligible`, `test_inject_no_filtered_span_in_unzoned_world` | RED |
| No source-text wiring tests (behavior + span, not grep) | entire `test_zone_eligibility_seam.py` (drives real `inject()`) | RED |
| #6 test quality (meaningful assertions, no vacuous) | self-checked all 30 — every test asserts a concrete value/membership/span | pass |
| Additive-field back-compat (no regression for the 11 unzoned worlds) | `test_world_is_zoned_false_*`, `test_is_eligible_unzoned_world_*`, `test_inject_unzoned_world_does_not_filter` | RED/guard |

**Rules checked:** 6 of the applicable lang-review concerns have explicit test coverage; the remainder (#3 type annotations, #4 logging, #5 paths, #7 resources, #8 deserialization, #9 async, #10 imports, #11/#12 input/dep hygiene) are not exercised by this story's surface (pure predicate + pydantic field + sync seam, no I/O / async / untrusted input).
**Self-check:** 0 vacuous tests written.

**Handoff:** To Dev (Naomi Nagata) for GREEN — see the three Delivery Findings (one BLOCKING: the pregen union-stamp must be implemented even though it has no RED test; its real proof is content story 157-5).

---
## Dev Assessment

**Implementation Complete:** Yes
**Branch:** feat/157-2-zone-eligibility-core (pushed to origin)

**Files Changed:**
- `sidequest/game/zone_eligibility.py` (new) — `world_is_zoned`, `is_eligible` (permissive predicate), split-party-safe `active_factions`, shared `cartography_for`.
- `sidequest/telemetry/spans/zone_eligibility.py` (new) + `spans/__init__.py` — `zone_eligibility.filtered` flat-only span.
- `sidequest/genre/models/bestiary.py` — `factions: list[str]` on `BestiaryEntry`.
- `sidequest/game/monster_manual.py` — `factions` on `ManualEncounter` + `ManualNpc`; `add_encounter` threads `factions`.
- `sidequest/server/dispatch/monster_manual_inject.py` — Seam 1: `inject()` resolves zoned/active/region once (from `snapshot.region_for`, not `current_location`); `_npc_patches_for_encounters` filters each candidate encounter via `is_eligible` (before the out-of-combat cap) and emits `zone_eligibility.filtered` per exclusion.
- `sidequest/server/dispatch/pregen.py` — `_encounter_factions` + `seed_manual` stamps `encounter.factions` = union of source bestiary factions (join by enemy name).
- `tests/server/dispatch/test_pregen.py` — `_stub_pack` gains `effective_bestiary` (a real `GenrePack` method the stub was missing; matches its existing `effective_cultures`/`effective_archetypes` stubs).

**Tests:** 130/130 GREEN for the story + regression surface (the 2 new files, `test_monster_manual_inject.py`, and the `test_pregen*` / `test_bestiary*` / `test_world_bestiary_content` regression set). Ruff clean on all changed files.

**Out of scope (pre-existing, documented as a Delivery Finding):** 7 ADR-145/114-15 inventory-provenance test failures at pack load (`test_pregen_fail_loud_90_5`, `test_pregen_combat_gate`, `test_encountergen_bestiary_90_1`) — validator + fixture predate this branch by 5 days; my changeset touches none of that path. Verified via causal trace + git timestamps (a clean-develop worktree run was blocked by a missing `claude_agent_sdk` in the throwaway venv, an env artifact).

**Self-review:**
- [x] Wired end-to-end: `inject()` (production turn path) calls the predicate; `seed_manual` (production seed path) populates the tag; the span fires on exclusion. Not a standalone module.
- [x] Follows project patterns (additive pydantic field, flat-only span, `pack.worlds[slug]` accessor convention, getattr-guarded pack reads).
- [x] No silent fallbacks: unzoned/unresolvable are *deliberate* permissive branches (design decision), not error-masking; pack-None already guarded.
- [x] All in-scope ACs met (module + field + Seam 1 + OTEL + the blocking pregen stamp).

**Handoff:** To Reviewer (Chrisjen Avasarala) for code review.

---
## Subagent Results (Round 1 — superseded)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (130 pass, ruff clean, pyright 0 errors) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — reviewer-covered (see [EDGE]) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — reviewer-covered + rule-checker #1 (see [SILENT]) |
| 4 | reviewer-test-analyzer | Yes | findings | 6 | confirmed 6, dismissed 0, deferred 0 |
| 5 | reviewer-comment-analyzer | Yes | findings | 6 | confirmed 4, dismissed 2 (low/noise), deferred 0 |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — covered by rule-checker #3 (see [TYPE]) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings — reviewer-covered (see [SEC]) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — reviewer-covered (see [SIMPLE]) |
| 9 | reviewer-rule-checker | Yes | findings | 1 (74 instances checked) | confirmed 1 (LOW), dismissed 0 |

**All received:** Yes (4 enabled returned; 5 disabled via `workflow.reviewer_subagents`, domains covered by reviewer)
**Total findings:** 8 confirmed actionable (1 High, 5 Medium, several Low), 2 dismissed as noise, 0 deferred

---
## Rule Compliance (Round 1 — superseded)

reviewer-rule-checker enumerated 74 instances across the 13 lang-review checks + 5 project rules (A1–A5). I confirmed its pass against the diff. Summary:

- **#1 Silent exceptions** — COMPLIANT. `zone_eligibility.py` is pure (no try/except). `_encounter_factions` uses isinstance guards, no swallowing. The new `pack.effective_bestiary(world)` call in `seed_manual` runs OUTSIDE the pre-existing broad `except` and propagates loud.
- **#2 Mutable defaults** — COMPLIANT. All three new `factions` fields use `Field(default_factory=list)`; `add_encounter(factions=None)` then `list(factions or [])`. Verified by the per-instance-isolation tests.
- **#3 Type annotations** — 1 LOW. `pack: Any` in `zone_eligibility` is a justified duck-typed boundary (GenrePack in prod / SimpleNamespace in tests). LOW: `otel_capture` params at `test_zone_eligibility_seam.py:199,221,233` use `# type: ignore[no-untyped-def]` (specific code present) without a typed annotation — comparable fixtures elsewhere annotate `InMemorySpanExporter`.
- **#4 Logging** — COMPLIANT. Exclusion logs at INFO (correct level for a subsystem decision), lazy %-format, no PII.
- **#5 Paths / #7 Resources / #8 Deserialization / #9 Async / #11 Input-validation / #12 Deps** — COMPLIANT (no new I/O, locks, untrusted deserialization, async, or deps; `_encounter_factions` thoroughly isinstance-guards the encountergen dict).
- **#6 Test quality** — COMPLIANT for the tests that exist (no vacuous asserts; identity/equality/membership checks). The issue is COVERAGE, not quality — see [TEST].
- **#10 Imports** — COMPLIANT. `from .zone_eligibility import *` matches the established `spans/__init__.py` pattern; TYPE_CHECKING guards on GameSnapshot/CartographyConfig/Bestiary; no circular risk.
- **A1 No Silent Fallbacks** — COMPLIANT *by documented design*: the permissive branches (empty active → eligible, untagged → eligible, unzoned → eligible, None cartography → ∅) are the epic-157 runtime-permissive decision with strictness deferred to the 157-7 load validator; each is documented in the module + function docstrings.
- **A2 Wire it fully** — COMPLIANT. `zone_eligibility` + the span have non-test consumers (`inject`/`_npc_patches_for_encounters`). `ManualNpc.factions` carries no runtime data yet (157-3 origin-stamp target) — documented cross-story, not an accidental stub.
- **A3 OTEL** — COMPLIANT. `zone_eligibility.filtered` fires once per exclusion, FLAT_ONLY-registered (matching sibling spans).
- **A4 Sebastien misattribution** — COMPLIANT; this diff *removed* the old "Sebastien's GM panel" wording from `_npc_patches_for_encounters` → "the GM panel". Good.
- **A5 Genre-rulebook / world-cast** — COMPLIANT.

---
## Reviewer Assessment (Round 1 — superseded)

**Verdict:** REJECTED

The implementation is **correct** — across reviewer-preflight (130 green, ruff + pyright clean), reviewer-rule-checker (74 instances, no real violations), and my own line-by-line read, I found **no correctness, security, or silent-fallback bug**. The logic, wiring, and OTEL are sound. I am rejecting on **test coverage of load-bearing new logic**, which this project treats as first-class (CLAUDE.md "Every Test Suite Needs a Wiring Test"; TEA's own *blocking* delivery finding on this exact mechanism).

### Blocking + actionable findings

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| **[HIGH]** `[TEST]` | The pregen union-stamp `_encounter_factions` — the mechanism that POPULATES production `encounter.factions` (the data Seam 1 filters on) — has **zero** coverage. Every `test_pregen.py` test stubs `effective_bestiary → (None,"stub")` and the e2e fixture has no bestiary, so the name-match / multi-enemy union / sorted-output logic NEVER runs; a regression (wrong join key, no union) ships green. The TEA-era "CLI-bound, can't unit-test" rationale is **false** for the extracted pure `_encounter_factions(data, bestiary)` helper. `add_encounter(factions=)` threading is likewise untested. | `sidequest/server/dispatch/pregen.py` `_encounter_factions`; `tests/server/dispatch/test_pregen.py` | Direct unit tests: (1) enemy name matches entry → its factions included; (2) multiple enemies → union; (3) no match → `[]`; (4) `None` bestiary → `[]`; (5) output sorted. Plus assert `MonsterManual.add_encounter(..., factions=[...])` stamps `ManualEncounter.factions`. |
| [MEDIUM] `[TEST]` | `"*"` world-global sentinel never exercised through the real `inject()` seam (only the `is_eligible` unit). | `tests/server/dispatch/test_zone_eligibility_seam.py` | Add `test_inject_star_sentinel_is_eligible_everywhere`. |
| [MEDIUM] `[TEST]`/`[EDGE]` | The documented out-of-combat "filter BEFORE the cap" ordering invariant is untested — all 9 seam tests use `in_combat=True`. A regression to cap-before-filter would not be caught. | `tests/server/dispatch/test_zone_eligibility_seam.py` | Add an `in_combat=False` test: `(_OUT_OF_COMBAT_ENCOUNTER_LIMIT+1)` wrong-zone encounters ahead of one in-zone → assert the in-zone one still surfaces. |
| [MEDIUM] `[TEST]` | No test asserts `SPAN_ZONE_ELIGIBILITY_FILTERED ∈ FLAT_ONLY_SPANS`, and the seam test **redefines** the span name as a local literal instead of importing it (a rename in the module wouldn't fail any test — the GM-panel persistence-routing contract is unguarded). | `tests/server/dispatch/test_zone_eligibility_seam.py:30` | Import the constant from `sidequest.telemetry.spans.zone_eligibility`; add a zero-setup `assert ... in FLAT_ONLY_SPANS`. |
| [MEDIUM] `[TEST]` | `test_inject_emits_filtered_span_on_exclusion` only asserts `subsystem`+`region` by key; `content_id`/`content_factions`/`active_factions` are checked solely via `_attrs_mention` (scans ALL values for the slug) — a mis-named key carrying the slug would pass. The forensic span shape the GM panel depends on is half-verified. | `tests/server/dispatch/test_zone_eligibility_seam.py:199` | Assert the three remaining attrs by key. |
| [LOW] `[DOC]` | `world_is_zoned` docstring claims "Computed once per loaded world by callers **and cached**" — there is **no cache**; it is recomputed every `inject()`. Actively misleading (describes the exact optimization that's absent). | `sidequest/game/zone_eligibility.py:39` | Reword to "computed per `inject()` call and passed downstream" — or add the cache. |
| [LOW] `[DOC]` | Stale "they FAIL today / RED tests" docstrings (the impl ships in the same diff). | `tests/game/test_zone_eligibility.py`, `tests/server/dispatch/test_zone_eligibility_seam.py` | Reword to present-tense contract description. |
| [LOW] `[SIMPLE]` | `inject()` resolves `cartography_for` twice (once inside `active_factions`, once via `world_is_zoned(cartography_for(...))`) and calls `snapshot.region_for()` twice (consensus + `region` var) → 2 redundant `region_query` spans/turn; zone context is also computed when `manual is None`/combat-disabled (unused). | `sidequest/server/dispatch/monster_manual_inject.py:557-559` | Resolve cartography once, reuse `region`; gate the computation on `combat_encounters and manual is not None`. (Pairs with the "cached" doc fix.) |
| [LOW] `[TYPE]`/`[RULE]` | `otel_capture` test params use `# type: ignore[no-untyped-def]` without a typed annotation. | `tests/server/dispatch/test_zone_eligibility_seam.py:199,221,233` | Annotate `InMemorySpanExporter`, drop the ignore. |
| [LOW] `[TEST]` | `world_is_zoned(None)` (a real production input via `cartography_for`) untested. | `tests/game/test_zone_eligibility.py` | One-line `assert world_is_zoned(None) is False`. |

### Dispatch-tag coverage
- `[TEST]` (test-analyzer): 6 confirmed — the coverage cluster above; the `_encounter_factions` gap is the blocker.
- `[DOC]` (comment-analyzer): 4 confirmed (cached overclaim, 2× stale RED docstrings, the `_encounter_factions` "no creature_id" wording — qualified-accurate, LOW). Dismissed 2 as noise: the spans-docstring "lie-detector" attribution is CORRECT (not a finding), and the `ManualEncounter.factions` attribution nit is cosmetic.
- `[RULE]`/`[TYPE]` (rule-checker): 1 LOW (otel_capture annotation); 74 instances otherwise compliant.
- `[EDGE]` (subagent disabled — reviewer-covered): enumerated below + Devil's Advocate; the one real gap (OOC filter ordering) is folded into [TEST].
- `[SILENT]` (subagent disabled — reviewer-covered + rule-checker #1): no swallowed errors; permissive returns are documented design, not error-masking — verified each branch is intentional with a doc rationale.
- `[SEC]` (subagent disabled — reviewer-covered): no auth/tenant/injection/deserialization surface. Inputs are internal authored content (faction slugs from `controlled_by`, region ids from `pc_regions`); no untrusted free-text reaches the predicate. CLEAN.
- `[SIMPLE]` (subagent disabled — reviewer-covered): the LOW double-resolve redundancy above.

### Observations (≥5)
1. `[VERIFIED]` `is_eligible` truth table matches the design exactly — `zone_eligibility.py:59-69`: unzoned→True, empty-active→True, `"*"`→True, untagged→True, else intersection. Complies with A1 (permissive-by-design, documented).
2. `[VERIFIED]` Split-party union is correct — `active_factions` uses `region_for()` consensus then falls to a per-seat union over `player_seats`/`pc_regions` (`zone_eligibility.py:126-140`); `None` is never added to the set (`if faction:` guard). Matches `test_active_factions_split_party_is_union` + the hub-`None` test.
3. `[VERIFIED]` Seam-1 filter runs BEFORE the out-of-combat slice (`monster_manual_inject.py:359-385`) so a wrong-zone encounter can't starve an in-zone one — correct order. (But untested — see [TEST] MEDIUM.)
4. `[VERIFIED]` Data flow end-to-end: seed path `seed_manual → effective_bestiary → _encounter_factions(by name) → add_encounter(factions=)` populates the tag; turn path `inject → active_factions/world_is_zoned (from region_for, not current_location) → is_eligible → drop + zone_eligibility.filtered span`. Fully wired (A2).
5. `[SEC] [VERIFIED]` No untrusted-input surface; faction/region identifiers are internal authored content; no SQL/eval/yaml/pickle/subprocess. CLEAN.
6. `[SIMPLE]` redundant cartography/region_for resolution (LOW, above).
7. `[TEST]` the load-bearing union-stamp is entirely unexercised (HIGH, above).

### Devil's Advocate
Assume this is broken. **First**: the union-stamp could silently mis-join. `_encounter_factions` matches `enemy["name"].lower()` against `BestiaryEntry.name.lower()`. encountergen copies `entry.name` verbatim *today* — but nothing pins that, and no test would catch a future encountergen change that decorates the name (e.g. "Yahoo Brute (elite)"), which would silently drop the faction tag → the Yahoo becomes untagged → permissive → **the exact gulliver bleed this story exists to fix returns, with all tests green**. That is the precise failure the missing `_encounter_factions` test must lock. **Second**: a content author typos a faction (`the_houyhnhm_assembly`). In the 157-2→157-6 window (before the 157-7 referential validator) the runtime sees a tagged-wrong-zone item and *silently excludes it everywhere* — content vanishes with no loud signal. The design accepts this (permissive-untagged + strict-validator-last), but it is a real sharp edge until 157-7 lands; the rejection note should make 157-7's urgency explicit. **Third**: MP split-party — `inject()` calls `active_factions` with `perspective=None` (party union), not per-recipient, so a creature eligible for player A's zone materializes into the shared snapshot player B also sees. For hostile creatures in a shared scene this is acceptable (and more permissive = safer), but it's an undocumented divergence from the design's "per-perspective seam" language (logged below). **Fourth**: a confused operator reads "Computed once per loaded world and cached," assumes caching exists, and builds on that — the docstring lies. **Fifth**: `content_id = encounter.label` is non-unique (two "1x Yahoo Brute (tier 2)" encounters collide in forensics) — cosmetic, but worth knowing. None of these are correctness bugs in the committed code *today*; the first is a latent regression the missing test would prevent, which is why coverage here is blocking, not optional.

**Handoff:** Back to TEA (Amos Burton) for RED rework — the findings are testable (missing coverage on load-bearing logic + untested invariants). Doc/efficiency LOWs to be cleaned in the green that follows.

---
## Dev Assessment (rework — round-trip 1)

**Implementation Complete:** Yes — all Reviewer findings addressed.
**Branch:** feat/157-2-zone-eligibility-core (pushed: 148875b8)

**Reviewer findings → resolution:**
- **[HIGH] `_encounter_factions` zero coverage** → FIXED. Added 8 direct unit tests (`tests/server/dispatch/test_pregen.py`): matched-entry factions, case-insensitive join, multi-enemy union+sort, no-name-match→[], None-bestiary→[], malformed-enemy-rows tolerance, untagged-entry→[]; plus `test_add_encounter_threads_factions_onto_manual_encounter` + default-empty. The function is pure `(data, bestiary)` — the old "CLI-bound" premise was indeed false.
- **[MEDIUM] `"*"` sentinel at the seam** → FIXED (`test_inject_star_sentinel_is_eligible_everywhere`).
- **[MEDIUM] out-of-combat filter-before-cap ordering** → FIXED (`test_inject_out_of_combat_limit_applied_after_filter`: cap+1 wrong-zone ahead of one in-zone, `in_combat=False`, asserts the in-zone one still surfaces).
- **[MEDIUM] FLAT_ONLY_SPANS registration + local-literal span** → FIXED: imported `SPAN_ZONE_ELIGIBILITY_FILTERED` + `FLAT_ONLY_SPANS` from the production modules (dropped the local literal); added `test_filtered_span_is_flat_only_registered`.
- **[MEDIUM] half-vacuous span assertion** → FIXED: `test_inject_emits_filtered_span_on_exclusion` now asserts `content_id`/`content_factions`/`active_factions` by key (removed the value-scanning `_attrs_mention` helper).
- **[LOW] `world_is_zoned` "cached" overclaim** → FIXED (docstring corrected — no cache; cheap per-inject pass). Paired efficiency fix: `inject()` now resolves the active-faction set + region ONLY for a zoned/combat/manual-bound turn (skips the region query for unzoned/quiet turns) — eliminates the double-resolve on the common path.
- **[LOW] stale "RED/FAIL today" docstrings** → FIXED in both test files.
- **[LOW] `otel_capture` annotations** → FIXED (`InMemorySpanExporter`, ignores dropped).
- **[LOW] `world_is_zoned(None)`** → FIXED (one-line unit).
- **ruff I001** (import sort in `test_zone_eligibility.py`, surfaced by preflight) → FIXED.

**Tests:** 105/105 GREEN (story + regression: `test_zone_eligibility`, `test_zone_eligibility_seam`, `test_pregen`, `test_monster_manual_inject`); +14 new tests this round. Ruff clean across all changed files.

**Type-check note (deliberate, consistent-with-baseline):** pyright reports 11 nominal errors on `_FakeSessionData → inject(sd)` in the seam test (duck-typed fixture). The established sibling `test_monster_manual_inject.py` carries **40** of the identical class on develop, and pyright is **not** in any gate (`just server-check`/`pf check` = ruff + pytest). Adding `# type: ignore` would make the new file inconsistent with the accepted pattern, so left as-is.

**Out of scope (unchanged):** the pre-existing ADR-145/114-15 inventory-fixture failures (Dev delivery finding above) — still recommend a small fixture-hygiene story.

**Handoff:** To Reviewer (Chrisjen Avasarala) for re-review.

---
## Subagent Results

Re-review (round-trip 1). Subagents re-run against the full branch diff vs base
`9d7303fa`; special focus on the rework commit `148875b8` (the production-code
efficiency change rode along with the test additions).

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (105 pass, 0 fail, 0 skip; ruff clean) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via `workflow.reviewer_subagents` — reviewer-covered (see [EDGE]) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled — reviewer-covered + rule-checker #1 (see [SILENT]) |
| 4 | reviewer-test-analyzer | Yes | findings | 5 (+ all 6 round-0 gaps verified CLOSED) | confirmed 0 blocking; 3 non-blocking improvements, 2 belt-and-suspenders noted |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 (+ 2 round-0 doc fixes verified accurate) | confirmed 2 non-blocking + 1 low; 0 blocking |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled — covered by rule-checker #3 (see [TYPE]) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled — reviewer-covered (see [SEC]) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled — reviewer-covered (see [SIMPLE]) |
| 9 | reviewer-rule-checker | Yes | findings | 5 (97 instances checked, incl. #13 fix-regression meta) | confirmed 3 LOW + 1 informational; 0 blocking |

**All received:** Yes (4 enabled returned; 5 disabled via `workflow.reviewer_subagents`, domains covered by reviewer + Devil's Advocate)
**Total findings:** 0 blocking — the round-0 [HIGH] coverage gap is verified CLOSED and all 5 round-0 [MEDIUM]/[LOW]s closed; ~8 non-blocking (forward test-coverage improvements + doc polish + 3 LOW rule items + 1 informational efficiency note), 0 deferred

### Round-0 finding verification (the reason for the round-1 reject)
Every round-0 finding independently verified CLOSED by test-analyzer **and** my own read of `/tmp/157-2-full.diff`:
- **[HIGH] `_encounter_factions` zero coverage → CLOSED.** 8 direct unit tests (`test_pregen.py`): matched-entry, case-insensitive join, multi-enemy union+sort (concrete value), no-name-match→[], None-bestiary→[], malformed-row tolerance, untagged-entry→[]; + `test_add_encounter_threads_factions_onto_manual_encounter` exercises the real `add_encounter(factions=)` production path. Not vacuous, not stubbed.
- **[MEDIUM] `"*"` sentinel through real `inject()` → CLOSED** (`test_inject_star_sentinel_is_eligible_everywhere`).
- **[MEDIUM] OOC filter-before-cap ordering → CLOSED** (`test_inject_out_of_combat_limit_applied_after_filter`: cap+1 wrong-zone ahead of one in-zone, `in_combat=False`, in-zone still surfaces, no Wrong* surface).
- **[MEDIUM] FLAT_ONLY registration + canonical import → CLOSED** (imports `SPAN_ZONE_ELIGIBILITY_FILTERED` + `FLAT_ONLY_SPANS` from production; `test_filtered_span_is_flat_only_registered`).
- **[MEDIUM] half-vacuous span assertion → CLOSED** (`content_id`/`content_factions`/`active_factions` now asserted by key; value-scanning `_attrs_mention` helper deleted).
- **[LOW] `world_is_zoned(None)` → CLOSED**; **[LOW] cached-docstring overclaim → CLOSED** (comment-analyzer confirmed accurate); **[LOW] stale RED docstrings → CLOSED**; **[LOW] `otel_capture` annotations → CLOSED** (`InMemorySpanExporter`).

---
## Rule Compliance

reviewer-rule-checker enumerated **97 instances** across the 13 python lang-review
checks + 5 project rules (A1–A5), including the #13 fix-introduced-regression
meta-scan of commit `148875b8`. I confirmed its pass and independently walked the
load-bearing branches. Summary:

- **#1 Silent exceptions** — COMPLIANT. `zone_eligibility.py` is pure (no try/except); `_encounter_factions` uses `isinstance` guards, skips malformed rows without swallowing; the new `effective_bestiary()` call sits outside the pre-existing broad `except` and propagates loud.
- **#2 Mutable defaults** — COMPLIANT. All three `factions` fields use `Field(default_factory=list)`; `add_encounter(factions=None)` → `list(factions or [])`. Per-instance isolation tested.
- **#3 Type annotations** — COMPLIANT at production boundaries (`pack: Any` is the justified duck-typed accessor convention). 2 LOW in test code (`_bestiary` helper / `_Pack.__init__` untyped) — consistent with the accepted duck-typed test-fixture pattern; pyright is in no gate.
- **#4 Logging** — COMPLIANT. Exclusion logs at INFO (correct for a subsystem decision), lazy %-format, no PII.
- **#5 Paths / #7 Resources / #8 Deserialization / #9 Async / #11 Input-validation / #12 Deps** — COMPLIANT (no new I/O, locks, untrusted deserialization, async, untrusted-input surface, or deps).
- **#6 Test quality** — COMPLIANT. 31 added tests enumerated; every one asserts a concrete value/membership/registry/span by key. No vacuous asserts, no mock-on-wrong-target, no all-same-path parametrize. The earlier coverage gap is the thing the rework fixed.
- **#10 Imports** — COMPLIANT. Star-import of `zone_eligibility` matches the `spans/__init__.py` pattern; TYPE_CHECKING guards correct; no circular risk (`game` does not import `monster_manual_inject`). 1 LOW (test-helper `SimpleNamespace` import inside `__init__`) + 1 LOW (no `__all__` on the span module, consistent with its neighbors).
- **#13 Fix-introduced regressions** — COMPLIANT. The `inject()` gating change is behavior-preserving across all four branches (verified independently — see Devil's Advocate). The fix also *improved* import hygiene (canonical span constant instead of the local literal) and *removed* the round-0 "Sebastien's GM panel" misattribution.
- **A1 No Silent Fallbacks** — COMPLIANT by documented design: the permissive branches (empty active / untagged / unzoned / None cartography → eligible) are the epic-157 runtime-permissive decision with strictness deferred to the 157-7 load validator; each is documented in module + function docstrings. Not error-masking.
- **A2 Wire it fully** — COMPLIANT. `zone_eligibility` + the span have non-test consumers (`inject`/`_npc_patches_for_encounters`/`seed_manual`). `ManualNpc.factions` is the 157-3 origin-stamp target (documented cross-story, not an accidental stub).
- **A3 OTEL** — COMPLIANT. `zone_eligibility.filtered` fires once per exclusion, BEFORE the in_combat cap (so it fires out-of-combat too), FLAT_ONLY-registered, full forensic attribute shape pinned by key.
- **A4 Sebastien misattribution** — COMPLIANT; the fix commit *removed* the old "Sebastien's GM panel" wording → "the GM panel". (Aligns with CLAUDE.md: GM-panel/OTEL is a Keith/dev observability surface, not a Sebastien feature.)
- **A5 Genre-rulebook / world-cast** — COMPLIANT. Faction slugs are world-authored `controlled_by` values; genre stays the rulebook (ADR-140).

---
## Reviewer Assessment

**Verdict:** APPROVED *(re-review — round-trip 1)*

**Why approved:** In round 0 I established the implementation was **correct** (no
correctness/security/silent-fallback bug across preflight, rule-checker, and my own
read) and rejected on **one [HIGH]**: zero coverage of the `_encounter_factions`
union-stamp — the seed-time mechanism that POPULATES the `encounter.factions` data
Seam 1 filters on — plus a cluster of [MEDIUM]/[LOW] invariant/doc gaps. The rework
closes **all** of them with genuine, concrete, keyed tests that exercise real
production paths (not vacuous, not stubbed), verified by test-analyzer **and** my own
diff read. Preflight is green (105/105, ruff clean). No Critical/High remains, so per
the project severity rubric this APPROVES.

**The load-bearing re-review check (the production change that rode along):** the fix
commit didn't only add tests — it rewrote `inject()` to gate active-faction/region
resolution behind `if zoned and combat_encounters and manual is not None`. I walked
every branch myself rather than trusting the meta-scan: the empty `set()`/`""`
defaults are a provable no-op because (a) `is_eligible` short-circuits permissive on
`zoned=False` (`zone_eligibility.py:59-69`), (b) `_npc_patches_for_encounters` is
itself gated `if combat_encounters else []` (`monster_manual_inject.py:585`), and
(c) `manual is None` skips the whole block (`:569`). No path runs the encounter
filter with a wrongly-empty `active` on a zoned world. Behavior-preserving. ✓

**Data flow traced:** seed path `seed_manual → effective_bestiary → _encounter_factions(join by enemy name) → add_encounter(factions=)` populates the tag; turn path `inject → world_is_zoned/active_factions (from snapshot.region_for, NOT current_location) → is_eligible → drop wrong-zone + emit zone_eligibility.filtered` — fully wired end-to-end, non-test consumers present (A2).

**Pattern observed:** Seam-1 filter runs BEFORE the out-of-combat slice (`monster_manual_inject.py:360-382`) so a wrong-zone encounter can't starve an in-zone one, and the exclusion span fires before the cap so it's emitted regardless of `in_combat`. Correct order, now pinned by `test_inject_out_of_combat_limit_applied_after_filter`.

**Error handling:** permissive branches are deliberate, documented design (epic-157), not error-masking; `cartography_for`→None and `_encounter_factions`→[] are the guarded pre-bind/native-pack paths; the pre-existing broad `except` in `ensure_loaded` re-raises `EncounterSeedError` above the catch (rule-checker #1, unchanged by this diff).

### Dispatch-tag coverage
- `[TEST]` (test-analyzer): all 6 round-0 gaps verified CLOSED with concrete keyed assertions exercising production code. New findings are **non-blocking, forward-looking**: (1) no `seed_manual` e2e test stamps `factions` through a real bestiary — the design assigns that proof to **157-5** (captured as a Delivery Finding so 157-5's acceptance asserts the stamp, not just no-bleed prose); (2) the OOC ordering test could also assert the exclusion-span count, and (3) the `"*"` test could assert span-absence — both **belt-and-suspenders**, since I verified the span emission is structurally independent of `in_combat` (so a span-gating regression is impossible by construction). None blocking.
- `[DOC]` (comment-analyzer): the 2 round-0 doc fixes (`world_is_zoned` "cached" overclaim; stale "RED tests" docstrings) landed and are now accurate. New non-blocking: (1) `inject()`'s public docstring doesn't mention the new zone filtering (it's a public seam — worth a line); (2) `ManualNpc.factions` describes the unshipped 157-3 origin-stamp in present tense (Delivery Finding to 157-3); (3) LOW — the `:553` "will actually field encounters this turn" comment slightly implies `in_combat` gates resolution when the gate is actually `combat_encounters` (pack-level). Doc polish, non-blocking.
- `[RULE]` (rule-checker): 97 instances, 0 real violations — 3 LOW (test-helper untyped `_bestiary`; `SimpleNamespace` import inside `_Pack.__init__`; no `__all__` on the span module, consistent with neighbors) + 1 informational (`cartography_for` runs every `inject()` to compute `zoned` — by design, cheap single-pass).
- `[TYPE]` (subagent disabled — covered via rule-checker #3): production boundaries fully annotated; `pack: Any` is the justified duck-typed accessor convention; test-fixture untyped helpers match the accepted pyright posture (pyright in no gate). CLEAN beyond the LOWs above.
- `[EDGE]` (subagent disabled — reviewer-covered + Devil's Advocate): the one real edge (OOC filter-before-cap ordering) is now tested; the gating-branch enumeration above is the edge pass on the new production code.
- `[SILENT]` (subagent disabled — reviewer-covered + rule-checker #1): no swallowed errors; permissive returns are documented design, each branch intentional with a doc rationale.
- `[SEC]` (subagent disabled — reviewer-covered): no auth/tenant/injection/deserialization surface. Inputs are internal authored content (faction slugs from `controlled_by`, region ids from `pc_regions`); no untrusted free-text reaches the predicate. CLEAN.
- `[SIMPLE]` (subagent disabled — reviewer-covered): the rework *reduced* redundancy (round-0's double cartography/region resolve is gone). Remaining informational: `cartography_for` per-`inject()` to compute `zoned` — negligible, by design.

### Observations (≥5)
1. `[VERIFIED]` `is_eligible` truth table matches the design exactly — `zone_eligibility.py:59-69`: unzoned→True, empty-active→True, `"*"`→True, untagged→True, else intersection. Complies with A1 (permissive-by-design, documented).
2. `[VERIFIED]` The fix-commit `inject()` gating is behavior-preserving — branch walk at `monster_manual_inject.py:558-587` (proof above). Complies with #13.
3. `[VERIFIED]` Exclusion span fires BEFORE the in_combat cap — `monster_manual_inject.py:360-380` precedes the `limit=` slice at `:382`; emission independent of `in_combat`. Complies with A3.
4. `[VERIFIED] [TEST]` The round-0 [HIGH] is genuinely closed — `test_pregen.py` calls `_encounter_factions(...)` directly with a real `Bestiary` and asserts the sorted union by value; `test_add_encounter_threads_factions_onto_manual_encounter` proves the value lands on `ManualEncounter.factions`. Complies with #6 + "Every Test Suite Needs a Wiring Test".
5. `[VERIFIED] [SEC]` No untrusted-input surface; faction/region identifiers are internal authored content; no SQL/eval/yaml/pickle/subprocess. CLEAN.
6. `[VERIFIED] [DOC]` `world_is_zoned` docstring now accurately states "there is no persistent cache today" — `zone_eligibility.py` (comment-analyzer confirmed; the round-0 lie is gone).
7. `[MEDIUM→non-blocking] [TEST]` `seed_manual` end-to-end factions-stamp proof is deferred to 157-5 (Delivery Finding logged).

### Devil's Advocate
Assume it is still broken. **The smuggled optimization is the live threat.** A reviewer who saw "round-0 was a coverage reject" could approve on green tests alone and miss that the fix rewrote the seam's resolution path. So I attacked it: could the gated `zone_active=set()`/`region=""` default ever reach the encounter filter on a zoned world and wrongly suppress nothing — or wrongly suppress everything? For suppression to be *wrong*, `_npc_patches_for_encounters` must run with an empty `active` on a zoned world that has eligible-but-mismatched content. But the filter only runs when `combat_encounters` is true (`:585`) and `manual is not None` (`:569`) — and those are exactly two of the three conditions that *also* gate `zone_active` resolution (`:561`). The only gap would be a zoned world where `combat_encounters` is true and `manual` is set but the guard didn't populate `zone_active` — impossible, because the guard's condition is a strict superset of the filter's. The third path (`zoned=False`) makes `is_eligible` permissive regardless of `active`. So no wrong-suppression path exists. **Second**: does the span go dark out-of-combat? No — emission precedes the cap and is independent of `in_combat`; verified structurally, so test-analyzer's worry can't bite. **Third**: the name-join fragility I flagged round 0 (a future encountergen name-decoration silently untags content → gulliver bleed returns) is now *locked* by `test_encounter_factions_match_is_case_insensitive` + `_includes_matched_entry_factions` — a decoration change breaks those tests loudly. **Fourth**: the unshipped `ManualNpc.factions` (157-3) is dead data today, but it's documented cross-story and read by nothing, so it can't misbehave — it's deferred, not stubbed. **Fifth**: a faction typo still silently excludes content everywhere until the 157-7 referential validator lands — a real sharp edge the design accepts; I re-flag 157-7's urgency rather than block here. None of these are correctness bugs in the committed code. The round-0 blocker is genuinely resolved and the rework introduced no regression.

**Handoff:** To SM (Camina Drummer) for finish-story. No Critical/High; all round-0 findings closed and verified; residual items captured as non-blocking Delivery Findings for 157-3 / 157-5 / 157-7.