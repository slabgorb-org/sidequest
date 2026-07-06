---
story_id: "162-3"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 162-3: Bestiary generics section replaces ephemeral stub minting

## Story Details
- **ID:** 162-3
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none
- **Repos:** server,content
- **Branch:** feat/162-3-bestiary-generics-last-resort

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-07-06T00:09:22Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-05T21:01:07Z | 2026-07-05T21:03:34Z | 2m 27s |
| red | 2026-07-05T21:03:34Z | 2026-07-05T21:31:27Z | 27m 53s |
| green | 2026-07-05T21:31:27Z | 2026-07-05T22:14:33Z | 43m 6s |
| review | 2026-07-05T22:14:33Z | 2026-07-06T00:09:22Z | 1h 54m |
| finish | 2026-07-06T00:09:22Z | - | - |

## Sm Assessment

**Setup complete — routing to TEA for RED phase.**

- **Story:** 162-3 (3 pts, p1) — bestiary generics section replaces ephemeral stub minting; authored generic rows per world become the sanctioned last-resort Other; stub fabrication becomes a loud failure on non-degenerate paths (No Silent Fallbacks).
- **Workflow:** tdd (phased: setup → red → green → review → finish). 3-point engine change with a doctrine invariant — TDD is the right fit; not a trivial-workflow candidate.
- **Repos:** server + content. Feature branch `feat/162-3-bestiary-generics-last-resort` created off `develop` in both.
- **Jira:** explicitly skipped — story carries no jira_key in sprint YAML.
- **Context:** `sprint/context/context-story-162-3.md` written by sm-setup (business context, guardrails, scope boundaries, ACs). Session file verified present.
- **Merge gate:** no blocking PR state surfaced at activation (NEW_WORK_STATE).
- **Routing:** next agent TEA (Amos Burton) — write failing tests covering the acceptance criteria: authored generic-row selection as the last-resort Other, and loud failure on stub fabrication in non-degenerate paths.

## TEA Assessment

**Tests Required:** Yes
**Reason:** 3-pt p1 engine change carrying a doctrine invariant (No Silent Fallbacks) — full TDD contract.

**Test Files:**
- `sidequest-server/tests/game/test_162_3_bestiary_generics_schema.py` — AC1: `Bestiary.generics` section (typed BestiaryEntry rows, optional/default-empty, fail-loud row validation, id uniqueness across entries+generics, extra=forbid retained); `OriginKind.GENERIC` + Npc round-trip + `identity_key` = `creature:<row id>`; green guard: legacy ephemeral stubs still derive `EPHEMERAL_STUB`.
- `sidequest-server/tests/server/test_162_3_generics_last_resort_seating.py` — AC2/AC3/AC4/AC6 at the public seam (`instantiate_encounter_from_trigger`, duck-typed `_FakeGenrePack`): unbacked opponent seats from generics (origin GENERIC + row id, row stats 6/11 win over cdef 8/12, reachable via `find_creature_core`), world-scoped resolution via `effective_bestiary(world_slug)`, `encounter.opponent_seated_from_generics` span; no generics → ValueError raise + nothing appended + `encounter.stub_fabrication_refused` span + no minted-stub span; degenerate opt-in `allow_synthetic_opponent=True` → warn + mint stamped EPHEMERAL_STUB + minted-stub span; green guards: roster and pool antagonists outrank generics (108-2/153-10 preserved); SPAN_ROUTES wiring for both new spans.
- `sidequest-server/tests/genre/test_162_3_generics_content.py` — AC (content): gated on content-on-disk; caverns_and_claudes/beneath_sunden, space_opera/coyote_star, neon_dystopia/franchise_nations resolve non-empty generics through `effective_bestiary` (tier-agnostic) with no id collisions.
- Retired old-contract pins in the same commit (TEA owns tests): `test_opponent_roster_resolution.py::test_minted_stub_marked_ephemeral_and_spanned` and `test_162_2_identity_fork_seating.py::TestNovelStubStampsOrigin` deleted with pointer comments; both files 13/13 green post-edit.

**Tests Written:** 25 tests (21 RED + 4 labeled green guards) covering all 6 ACs
**Status:** RED (verified via testing-runner, serial run: 26 fail / 28 pass; every failure is feature-absence — extra_forbidden, `OriginKind.GENERIC` AttributeError, DID-NOT-RAISE on the stub path, unexpected-kwarg TypeError, ImportError on span consts, no generics in shipped content; zero harness bugs, zero regressions in edited legacy files)

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #1 no silent fallbacks / swallowing | `test_no_source_and_no_generics_raises[*]` (raise, nothing appended), `test_refusal_is_observable_and_never_the_old_stub_span` | failing (RED) |
| #3 type annotations at boundaries | Typed contract pins (`Bestiary.generics: list[BestiaryEntry]`, `Origin.kind`); all test fns annotated | failing (RED) |
| #4 logging coverage + level | `test_degenerate_optin_mints_synthetic_loudly` (WARNING required on the tolerated mint) | failing (RED) |
| #6 test quality | Self-check done: no vacuous asserts; loc-based ValidationError asserts keep raises-tests RED against today's extra_forbidden; green guards explicitly labeled | n/a (meta) |
| #8 deserialization trusts schema | `test_unknown_top_level_key_still_rejected` (extra=forbid retained), row-level `test_generic_row_missing_hp_rejected` / `test_generic_row_empty_id_rejected` | mixed (guard green / rows RED) |
| OTEL principle (CLAUDE.md) | `test_generic_seat_is_observable_on_gm_panel`, `test_refusal_is_observable...`, `test_generics_spans_are_registered_span_routes` | failing (RED) |

**Rules checked:** 5 of 13 lang-review checks applicable to this diff have test coverage; #2/#5/#7/#9-#12 not applicable (no mutable defaults, paths, resources, async, imports, SQL, or dep changes in the contract surface).
**Self-check:** 0 vacuous tests found.

**Commit:** sidequest-server `ba04279c` on `feat/162-3-bestiary-generics-last-resort` (tree clean). Content repo: no RED-phase changes — generics authoring is GREEN work on the content branch, driven by the gated tests.

**Handoff:** To Dev (Naomi Nagata) for GREEN — schema field, `OriginKind.GENERIC`, seater generics branch + loud failure + degenerate opt-in, two routed spans, content generics for the three worlds, and the blocking flip-set sweep (see Delivery Findings).

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (sidequest-server, commit `1a988b7b`):**
- `sidequest/genre/models/bestiary.py` — `Bestiary.generics: list[BestiaryEntry]` (default `[]`); id uniqueness enforced across entries+generics
- `sidequest/game/origin.py` — `OriginKind.GENERIC` (stamped-only, never derived; docstrings updated honestly)
- `sidequest/telemetry/spans/encounter.py` — `encounter.opponent_seated_from_generics` + `encounter.stub_fabrication_refused`: constants, `SPAN_ROUTES` entries, helpers (both routed for the GM panel)
- `sidequest/genre/models/rules.py` — `ConfrontationDef.opponent_source: Literal["bestiary","frame"] = "bestiary"` (see Dev deviation)
- `sidequest/server/dispatch/encounter_lifecycle.py` — the story's core: `_generics_for` resolver (rides `effective_bestiary(world_slug)`); the seeder's fabrication branch became generics-seat (row stats + GENERIC stamp + span) → frame-sourced mint (sealed-letter / `opponent_source: frame`, no warning) → degenerate opt-in mint (WARN + EPHEMERAL_STUB + minted-stub span) → loud `ValueError` + refusal span; `instantiate_encounter_from_trigger(allow_synthetic_opponent=False)` new kwarg; refusal restores `snapshot.encounter` (no half-seat)
- Test-harness sweep (TEA pre-approved, mechanical): `allow_synthetic_opponent=True` threaded through `tests/integration/_wn_round_102_4.py::seat_wn_combat`, `tests/_helpers/trigger_encounter.py`, both space_opera e2e `_seated_combat` seats, `tests/game/test_materialize_armor_class.py`, and direct degenerate call sites in 9 integration files + `tests/server/test_encounter_lifecycle.py`; `tests/server/dispatch/test_confrontation_opponent_materialize.py` stat pin updated to the new contract (reads the authored generics row from the pack — see Dev deviation)

**Files Changed (sidequest-content, commit `92cb717`):**
- Generics authored for four worlds: `beneath_sunden` (hold_dead — the fabled stub name becomes authored canon — + starved_delver), `coyote_star` (void_drifter, wreck_picker; zone-tagged `["*"]` per epic-157), `franchise_nations` (gig_security_temp, dim_scavenger), `burning_peace` (masterless_blade, shrine_road_footpad)
- `space_opera/rules.yaml` — `ship_combat` declares `opponent_source: frame`

**Tests:** Full server suite 14,618 passed / 341 skipped; the only two blips were (1) `test_materialize_armor_class` (fixed — the one degenerate harness outside the swept directories, caught by the full run) and (2) the `test_pregen_bestiary_90_1[evropi]` xdist worker crash — the documented OPEN 162-1 flake, reproduced once, passes 7/7 in isolation (serial). All 162-3 story files green (schema 12/12, seating 12/12, content 6/6); both retired-pin legacy files 12/12+13/13. Lint clean on all changed files; pyright error-set byte-identical to the pre-change baseline (14 pre-existing in encounter_lifecycle.py).
**Branch:** `feat/162-3-bestiary-generics-last-resort` pushed in BOTH repos (server `1a988b7b`, content `92cb717`).

**Handoff:** To the next phase per workflow (review — Chrisjen Avasarala). Reviewer attention: the `opponent_source` schema addition (major deviation), the generic-seat lifecycle choices (durable/router-named), and the blanket opt-in threading in `test_encounter_lifecycle.py`.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 56/56 story tests pass, ruff clean (only pre-existing conftest E402 debt), pyright 14-baseline held |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 7 | confirmed 2 (fixed), deferred 5 (non-blocking edge-case coverage → Delivery Findings) |
| 5 | reviewer-comment-analyzer | Yes | findings | 10 | confirmed 10 (all fixed), dismissed 0 |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | none | N/A — 0 violations across 20 rules / 61 instances |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 12 confirmed (all FIXED in place), 0 dismissed, 5 deferred (non-blocking)

## Reviewer Assessment

**Verdict:** APPROVED (findings fixed in place at Bossmang's direction, then verified green)

This was a 2nd/3rd-round re-review. Key context surfaced up front: the branch had **no fix commits** since the Dev handoff — the earlier rounds re-ran subagents but never committed anything, so the same findings kept resurfacing. Rather than route back through TEA/Dev, Bossmang directed "just fix it in place." All confirmed findings are now fixed and committed as `12874fc2`.

**Findings by dispatch source:**
- **[RULE]** rule-checker CLEAN — 0 violations across 20 rules / 61 instances; wiring verified end-to-end (both production callers `confrontation.py`/`dogfight.py`), OTEL spans routed in `SPAN_ROUTES`, tests non-vacuous and driving the real production seam. No action needed.
- **[DOC]** comment-analyzer — 10 confirmed, all fixed: the minted-stub span "fires ONLY on opt-in" lie (`spans/encounter.py`) — it also fires on the frame path; the "nothing half-seated" overclaim (`encounter_lifecycle.py:1667`); `_seed`/`_resolve_opponent_from_roster`/`_seed_fate_opponents` stale docs; `Bestiary` + `Npc.ephemeral` overclaims; the world-vs-genre tier mislabel in the content test; the coyote_star zone-validation comment (made true by the loader fix); dead `_MOOK_HP`.
- **[TEST]** test-analyzer — 2 confirmed+fixed (the untested `opponent_source="frame"` branch now has a targeted test; `burning_peace` added to the content sweep), 5 deferred as non-blocking follow-up coverage (see Delivery Findings).
- **[SILENT]** silent-failure-hunter disabled — assessed the domain myself: the one refusal path (`except ValueError`) does NOT swallow; it now rolls back appended opponents AND re-raises. Compliant with No Silent Fallbacks.
- **[EDGE]** edge-hunter disabled — assessed myself: the multi-opponent half-seat edge (pool-promote A, refuse on B) was the one real gap; fixed with a roster-length rollback + a dedicated test.
- **[TYPE]** type-design disabled — assessed myself: `opponent_source: Literal["bestiary","frame"]` and `Bestiary.generics: list[BestiaryEntry]` are correctly typed/validated; pyright shows zero new errors.
- **[SEC]** security disabled — no attack surface in this diff (no auth, tenant, deserialization-of-untrusted, or path handling; YAML loads via existing `yaml.safe_load`).
- **[SIMPLE]** simplifier disabled — assessed myself: fixes are minimal (one rollback line, one list-splat, docstrings, tests); dead `_MOOK_HP` removed.

**Two substantive fixes (doctrine-faithful, not just doc patches):**
1. **Real half-seat rollback** — `except ValueError` restored only `snapshot.encounter`; now `del snapshot.npcs[_npcs_before_seed:]` rolls back opponents appended earlier in a multi-opponent pass. The story's "nothing half-seated" invariant now actually holds. New test: `TestRefusalRollsBackHalfSeat`.
2. **Generics zone-validation** — `_validate_zone_tagged_content` ignored `bestiary.generics`; a zoned world's untagged generic would silently never-match at seat time. Folded generics into the validated pool (fail-loud). Confirmed all four shipped worlds load; coyote_star (the one zoned world) passes with its `["*"]` tags. New tests in `test_157_7`.

**Data flow traced:** narrator `confrontation=T` → `instantiate_encounter_from_trigger` → `_seed_combat_hp_depletion_to_npcs` → unbacked opponent → generics-seat (GENERIC origin, row stats, span) | frame-mint (EPHEMERAL_STUB, span, no warn) | opt-in-mint (EPHEMERAL_STUB, span, WARN) | loud `ValueError` + refusal span + full rollback. Safe: every branch is observable and the refusal leaves the roster exactly as found.
**Pattern observed:** precedence chain `if generics: … elif frame_other or allow_synthetic_opponent: … else: raise` at `encounter_lifecycle.py:481` — deterministic, generics-first, single chokepoint.
**Error handling:** the sole failure path raises loudly, spans the refusal, and now rolls back cleanly; caught gracefully upstream (`run_dispatch_bank` at warning level) per ADR-006.

**Verification:** 83 affected tests (story + retired-pin legacy + zone validator + 4 new) + 1,727 broad regression (encounter-lifecycle / dispatch / genre-loader) all green; ruff clean; pyright zero new errors (14 encounter_lifecycle baseline held). Committed `12874fc2`, pushed to `feat/162-3-bestiary-generics-last-resort`.

**Handoff:** To SM (Camina Drummer) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

### TEA (test design)

- **Gap** (blocking): the WN test corpus RELIES on the stub mint to seat opponents — under the new default-strict contract these raise in GREEN until swept. Known flip set: `tests/integration/_wn_round_102_4.py::seat_wn_combat` (funnels ~10 integration files), `tests/server/test_space_opera_swn_combat_e2e.py::_seated_combat` (+ `test_space_opera_melee_e2e`), `tests/server/test_encounter_lifecycle.py::test_instantiate_combat_creates_encounter` + `test_instantiate_replaces_resolved_encounter` (cac_pack, unknown opponents), `tests/_helpers/trigger_encounter.py` consumers, `tests/server/test_opponent_toothless_detector.py` and `test_npc_registry_combat_stats.py` (verify), plus any harness reaching the stub branch. Recommended mechanism: thread the explicit degenerate opt-in (`allow_synthetic_opponent=True`) through the SHARED helpers only — fixture-generics cannot save integration suites (they bind real packs with fake world slugs, so `effective_bestiary` resolves genre-tier → None for caverns/heavy_metal). Dogfight suites are frame-default sealed-letter (ADR-153 §6) and should not reach the stub branch — verify, don't assume. TEA pre-approves the mechanical helper updates in GREEN; do NOT weaken the default-strict contract to avoid the sweep.
  Affects `tests/integration/_wn_round_102_4.py`, `tests/server/test_space_opera_swn_combat_e2e.py`, `tests/_helpers/trigger_encounter.py`, `tests/server/test_encounter_lifecycle.py` (helper opt-in threading). *Found by TEA during test design.*
- **Gap** (non-blocking): `_seed_combat_hp_depletion_to_npcs` has no pack/world access today (single call site: `encounter_lifecycle.py:2350`) — the generics branch needs the pack (or resolved generics) threaded in. Signature is Dev's to shape; tests pin only the public entrypoint.
  Affects `sidequest/server/dispatch/encounter_lifecycle.py` (seeder signature + call site). *Found by TEA during test design.*
- **Question** (non-blocking): generics SELECTION semantics when a world authors multiple rows (match on NpcMention role/tags? first row? deterministic draw?). Tests use a single-row fixture so selection is unambiguous; whatever Dev picks must be deterministic and carried on the `opponent_seated_from_generics` span.
  Affects `sidequest/server/dispatch/encounter_lifecycle.py`. *Found by TEA during test design.*
- **Question** (non-blocking): lifecycle of a generics-seated Other — ephemeral and husk-reaped with its encounter, or durable roster canon? Tests deliberately do not pin `ephemeral` on the generic seat; the reap suite (`test_opponent_roster_resolution.py` §4) still governs ephemeral entities.
  Affects `sidequest/server/dispatch/encounter_lifecycle.py` (+ `reap_resolved_encounter_husk` semantics). *Found by TEA during test design.*
- **Question** (non-blocking): the RED contract raises for BOTH "bestiary present, no generics" and "no bestiary at all" (parametrized). If Dev wants the 162-1 no-evidence conservatism distinction (unresolvable ≠ empty), carry it as a `reason` attr on the refusal span — never as a silent seat.
  Affects `sidequest/server/dispatch/encounter_lifecycle.py`. *Found by TEA during test design.*
- **Question** (non-blocking): the Fate seeder (`_seed_fate_opponents`, gated off this path by `is_fate`) keeps its own fallback stack — does a Fate sibling of generics need a follow-up story? (Fate-genre worlds carry WN-shaped bestiaries per the 2026-07-05 survey §3c.)
  Affects epic 162 backlog. *Found by TEA during test design.*
- **Improvement** (non-blocking): a bestiary carrying ONLY generics is unexpressible — `Bestiary._validate` requires non-empty `entries`. Relevant if a pack ever wants genre-tier generics without a genre-tier roster (caverns_and_claudes has no genre-root bestiary today). Decide deliberately in GREEN or defer.
  Affects `sidequest/genre/models/bestiary.py`. *Found by TEA during test design.*

### Dev (implementation)

- **Improvement** (non-blocking): 18 worlds still author no generics — in those worlds a live session's router-named opponent with no roster/pool backing now RAISES mid-dispatch (by design, but previously it "worked" via the stub lie). The recommended follow-up story: sweep generics across the remaining catalog (the story context already marks this post-story content work) and confirm the dispatch layer's ADR-006 graceful-degradation envelope narrates the refusal instead of wedging the turn.
  Affects `sidequest-content/genre_packs/*/worlds/*/bestiary.yaml` (generics authoring) + `sidequest/agents/subsystems/confrontation.py` (degrade-path confirmation). *Found by Dev during implementation.*
- **Gap** (non-blocking): pre-existing lint debt — `ruff check tests/` fails at HEAD on `tests/dungeon/conftest.py` (E402 ×3, module-level imports mid-file), untouched by this story.
  Affects `tests/dungeon/conftest.py` (import placement). *Found by Dev during implementation.*
- **Question** (non-blocking): `tests/server/dispatch/test_pregen_bestiary_90_1.py::test_seed_manual_populates_encounters_for_wwn_world[evropi]` reproduced its xdist worker crash once in this story's full-suite run (identical signature to the OPEN 162-1 finding; passes 7/7 in isolation, serial). Still unidentified; not a 162-3 regression.
  Affects `tests/server/dispatch/test_pregen_bestiary_90_1.py` (crash-mode investigation if it recurs in CI). *Found by Dev during implementation.*
- **Improvement** (non-blocking): the mechanical opt-in sweep threaded `allow_synthetic_opponent=True` into all 19 `instantiate_encounter_from_trigger` call sites in `tests/server/test_encounter_lifecycle.py` (blanket, per TEA's pre-approval) — the flag is inert everywhere a source exists, but TEA may want to narrow it to the actually-degenerate seats during verify.
  Affects `tests/server/test_encounter_lifecycle.py` (optional narrowing). *Found by Dev during implementation.*

### Reviewer (code review)

- **Improvement** (non-blocking): five deferred edge-case tests worth a fast-follow — (1) generics-wins when BOTH a generics pack and `allow_synthetic_opponent=True` are present; (2) two simultaneously-unbacked opponents seated from generics (same `creature_id` twin behavior vs the 162-2 id-keyed identity); (3) `generics[0]` selection discriminated against a 2+-row fixture at the unit layer (only the real-content `burning_peace` pin covers it today); (4) the refusal-restore path with a PRE-existing resolved encounter on the snapshot (only the None case is tested); (5) tighten `pytest.raises(match=r"(?i)generic")` to a multi-word phrase. Production paths are covered; these harden the unit layer. Affects `tests/server/test_162_3_generics_last_resort_seating.py`. *Found by Reviewer during code review.*
- **Gap** (non-blocking): the Fate seeder (`_seed_fate_opponents`) still does the PRE-162-3 unconditional mint — it does not consult bestiary generics or refuse loudly. Documented honestly in its docstring now; a Fate-genre generics sibling is a follow-up story (mirrors TEA's open Fate-seeder Question). Affects `sidequest/server/dispatch/encounter_lifecycle.py` (Fate path). *Found by Reviewer during code review.*
- **Note**: 18 of 22 worlds still author no generics — an unbacked router-named opponent in those worlds now RAISES by design (Dev already logged this). Sweep-the-catalog is post-story content work.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Generic row stats seat the Other (row wins over cdef opponent_default_stats)**
  - Spec source: context-story-162-3.md, Technical Guardrails ("generics" format) + AC "Generics fallback verified"
  - Spec text: "Format: list of creature rows (same structure as other bestiary entries)"
  - Implementation: Tests pin the seated Other's hp/AC to the GENERIC ROW's values (6/11), not the confrontation frame's opponent_default_stats (8/12)
  - Rationale: A generic IS an authored bestiary stat block; SOUL "Bind the Ruleset, Don't Balance It" and the 108-2 bound-creature HP preserve both say authored bestiary math outranks the frame default — identity-only generics would ship required stat fields the engine ignores
  - Severity: minor
  - Forward impact: minor — 162-4 (Green Room precedence ADR) should ratify the stat-source rule
- **Concrete names pinned: two span names, the degenerate kwarg, and the pack accessor**
  - Spec source: context-story-162-3.md, Failure contract + AC "OTEL spans on all paths"
  - Spec text: "All paths must OTEL span the attempt + reason"
  - Implementation: Tests pin `encounter.opponent_seated_from_generics`, `encounter.stub_fabrication_refused`, kwarg `allow_synthetic_opponent`, and generics resolution via `GenrePack.effective_bestiary(world_slug)` (recorded on a duck-typed fake that fails loud on any other accessor)
  - Rationale: Concrete markers make the wiring tests executable (126-30/126-37 workflow); behavioral asserts remain primary — Dev may finalize different names/accessors via a TEA-coordinated test update, keeping each distinct and generics-gated
  - Severity: minor
  - Forward impact: none
- **Loud failure pinned as ValueError whose message names generics**
  - Spec source: context-story-162-3.md, Failure contract
  - Spec text: "Raise an exception in non-degenerate paths (gameplay sessions)"
  - Implementation: `pytest.raises(ValueError, match=r"(?i)generic")` — mirrors the file's 45-33 no-opponent convention; the message must point the author at the missing generics section
  - Rationale: Exception type unspecified by spec; a typed error is fine if it subclasses ValueError
  - Severity: minor
  - Forward impact: none
- **Id uniqueness enforced ACROSS entries + generics**
  - Spec source: context-story-162-3.md, Technical Guardrails; 162-2 identity doctrine
  - Spec text: "schema validated" (uniqueness scope unspecified)
  - Implementation: Duplicate id in entries vs generics (and within generics) must raise at validation
  - Rationale: identity_key keys on `creature:<id>` — one id over two divergent stat blocks is a forked identity, the exact defect class 162-2 killed
  - Severity: minor
  - Forward impact: none
- **Genre→world generics inheritance pinned only at the content level, not unit level**
  - Spec source: context-story-162-3.md, Technical Guardrails
  - Spec text: "Inherit from genre default if not overridden"
  - Implementation: Unit tests pin world-scoped resolution through `effective_bestiary(world_slug)`; the tier-inheritance mechanics are asserted only via the gated content tests (tier-agnostic — either authoring home passes)
  - Rationale: effective_bestiary is whole-file world-REPLACES-genre today; per-section inheritance is a resolution-design choice best made with 162-4 — over-pinning it now would falsely fail a faithful implementation
  - Severity: minor
  - Forward impact: minor — 162-4 should specify per-section vs whole-file generics inheritance
- **Content scope pinned to exactly the three recommended worlds**
  - Spec source: context-story-162-3.md, Scope boundaries
  - Spec text: "Populate representative generics for 2–3 worlds (recommend high-traffic worlds: caverns_and_claudes, space_opera, neon_dystopia)"
  - Implementation: Gated tests enforce caverns_and_claudes/beneath_sunden, space_opera/coyote_star, neon_dystopia/franchise_nations
  - Rationale: TDD needs concrete targets; the recommendation is the obvious pick (flagship world per pack, covering both world-tier and genre-tier bestiary patterns)
  - Severity: minor
  - Forward impact: none

### Dev (implementation)
- **New ConfrontationDef.opponent_source field — vehicle-scale defs seat from the frame, not generics**
  - Spec source: context-story-162-3.md, Technical Guardrails ("Origin-precedence path")
  - Spec text: "Authored > room-bound > region-population > MM pool > generics > ~~narrator stub~~ (error). Generics are the last _legitimate_ source before failure"
  - Implementation: Added `ConfrontationDef.opponent_source: Literal["bestiary","frame"] = "bestiary"`; sealed-letter defs are frame-sourced implicitly (ADR-153 §6) and space_opera `ship_combat` declares `opponent_source: frame` — frame-sourced defs keep the pre-162-3 mint (ephemeral + minted-stub span, no warning) instead of consulting generics or raising
  - Rationale: The unconditional generics rung seated a humanoid void_drifter (hp 4) as a ship hull calibrated at hp 30 (test_59_23_materialize_other hull pin); nothing machine-readable distinguished vehicle-scale from entity-scale, so the discriminator became authored, typed content data (Crunch in the Genre) rather than type-name string matching
  - Severity: major
  - Forward impact: minor — 162-4 (Green Room precedence ADR) should honor opponent_source in the arbiter; authors of future vehicle-scale hp_depletion confrontations must declare `opponent_source: frame`
- **Fourth world's generics authored (burning_peace) + production materialize stat pin updated to the new contract**
  - Spec source: context-story-162-3.md, Scope boundaries
  - Spec text: "Populate representative generics for 2–3 worlds (recommend high-traffic worlds: caverns_and_claudes, space_opera, neon_dystopia)"
  - Implementation: Also authored elemental_harmony/burning_peace generics (masterless_blade, shrine_road_footpad) and updated `test_confrontation_opponent_materialize.py`'s hp pin from the cdef `_MOOK_HP` frame default to the pack-read authored generics row (self-consistent, no magic number)
  - Rationale: That test pins the PRODUCTION dispatch path seating a router-named unbacked Other; without world generics it now (correctly) raises — authoring the world keeps the production contract testable and converts the test into a production-path wiring proof of the new rung (158-31 precedent: update to the new contract, log the deviation)
  - Severity: minor
  - Forward impact: none
- **Generic seat lifecycle: durable, router-named, no alias recorded**
  - Spec source: context-story-162-3.md, Technical Guardrails ("No silent fallbacks")
  - Spec text: "Every NPC generation attempt must have an explicit origin (Origin enum) traceable to a bestiary source or a deliberate fallback reason"
  - Implementation: The generics seat keeps `core.name = actor.name` (router/narrator continuity), sets `Npc.creature_id = row.id` + `Origin(kind=GENERIC, creature_id=row.id)`, is NOT marked ephemeral (survives the husk reap like a pool promotion), and does not record the row name as an alias
  - Rationale: TEA left lifecycle/naming open (Delivery Findings Questions); a sanctioned authored source reads as durable canon, and the actor-name seat keeps every downstream `find_creature_core(actor.name)` consumer reachable
  - Severity: minor
  - Forward impact: minor — 162-4 may revisit reap/alias semantics for GENERIC seats
- **Generics selection = first authored row**
  - Spec source: context-story-162-3.md, AC "Generics fallback verified"
  - Spec text: "encounter-gen with no pool/room/region source falls back to bestiary generics (if available)"
  - Implementation: `generics[0]` — deterministic, resume-safe, a single chokepoint commented for future role/tag-matched selection
  - Rationale: Selection semantics were unspecified (TEA Question); first-row is the minimal deterministic contract and the ordering is author-controlled
  - Severity: minor
  - Forward impact: none

### Reviewer (audit)

Every logged deviation reviewed — all ACCEPTED, none flagged:

- **TEA — Generic row stats seat the Other (row wins over cdef)** → ✓ ACCEPTED: SOUL "Bind the Ruleset, Don't Balance It"; authored bestiary math is the balanced source (108-2 rule extended honestly).
- **TEA — Concrete span/kwarg/accessor names pinned** → ✓ ACCEPTED: makes the wiring executable; behavioral asserts stay primary.
- **TEA — Loud failure pinned as ValueError naming generics** → ✓ ACCEPTED: type unspecified by spec; message points the author at the fix.
- **TEA — Id uniqueness across entries+generics** → ✓ ACCEPTED: prevents the exact forked-identity defect 162-2 killed.
- **TEA — Genre→world generics inheritance pinned at content level only** → ✓ ACCEPTED: `effective_bestiary` is whole-file replace today; per-section is 162-4's call.
- **TEA — Content scope = 3 recommended worlds** → ✓ ACCEPTED (Dev added a 4th; the content sweep now covers all four).
- **Dev — New `ConfrontationDef.opponent_source` field (MAJOR)** → ✓ ACCEPTED: the vehicle-scale-vs-entity-scale discriminator is authored content data (Crunch in the Genre), not type-name string matching. My one reservation — it shipped untested — is now closed by the added `TestFrameSourcedSkipsGenerics`.
- **Dev — Fourth world (burning_peace) + materialize pin reads the pack** → ✓ ACCEPTED: self-consistent, no magic number, converts the test into a production-path wiring proof (158-31 precedent).
- **Dev — Generic seat lifecycle: durable, router-named, no alias** → ✓ ACCEPTED: a sanctioned authored source reads as durable canon; actor-name seat keeps `find_creature_core` consumers reachable.
- **Dev — Generics selection = first authored row** → ✓ ACCEPTED: minimal deterministic, resume-safe, single commented chokepoint for future role/tag matching.