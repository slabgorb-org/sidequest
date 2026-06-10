---
story_id: "102-7"
jira_key: ""
epic: "102"
workflow: "tdd"
---
# Story 102-7: AWN (Ashes Without Number) module live wiring for mutant_wasteland — bind the AWN RulesetModule + content per spec 2026-06-05-ashes-without-number-mutant-wasteland-design.md; prove AWN combat + lethality fire live (mirrors heavy_metal/WWN). Repos: server,content.

## Story Details
- **ID:** 102-7
- **Jira Key:** (none — personal project, sprint YAML only)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** green
**Phase Started:** 2026-06-10T19:27:36Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-10T18:57:59Z | 2026-06-10T18:59:31Z | 1m 32s |
| red | 2026-06-10T18:59:31Z | 2026-06-10T19:27:36Z | 28m 5s |
| green | 2026-06-10T19:27:36Z | - | - |

## Repository & Branch Configuration
- **Repos:** server (feat/102-7-awn-mutant-wasteland-live-wiring), content (feat/102-7-awn-mutant-wasteland-live-wiring)
- **Branch Strategy:** gitflow (feat/102-7-awn-mutant-wasteland-live-wiring off develop)

## Sm Assessment

Setup complete and verified. Story 102-7 binds the AWN (Ashes Without Number) RulesetModule + content for mutant_wasteland per spec `docs/superpowers/specs/completed/2026-06-05-ashes-without-number-mutant-wasteland-design.md`, mirroring the heavy_metal/WWN wiring proven in 102-1/102-2/102-3 (server PRs #801/#806/#805, all merged to develop).

- **Repos:** server + content; feature branches `feat/102-7-awn-mutant-wasteland-live-wiring` created off develop in both.
- **Jira:** explicitly skipped — personal project, sprint YAML only.
- **Context:** `sprint/context/context-story-102-7.md` + `context-epic-102.md` present.
- **Key prior art for TEA:** the WN module wiring checklist (spans `__init__` re-export, `dice.py` downed-seam guard + `_physical_save_target_for` isinstance, OTEL span-assertion tests) and the hp_depletion calibration-test migration pattern (filter dial_threshold; opponent_default_stats needs all six ability scores).
- **Acceptance proof:** AWN combat + lethality must fire LIVE (OTEL-verified), not just unit-tested — "wired, not just existing" is the epic's whole point.

Routing to TEA (Fezzik) for RED phase.

## TEA Assessment

**Tests Required:** Yes
**Phase:** green — COMPLETE (verified by testing-runner, RUN_ID 102-7-tea-red)

**Scope determination (load-bearing):** The story title says "prove AWN combat +
lethality fire live" — but combat + lethality strike/shock/trauma/reprisal-downed
paths are ALREADY live and span-proven (epic 88 + 102-1: `test_awn_combat_dispatch.py`,
`test_mutant_wasteland_combat_dispatch.py`, `test_reprisal_wn_downed_seam.py` — all 77
pre-existing tests pass). The genuinely unwired live surface, measured this session, is
the pack's MARQUEE mechanic: **mutations (the pack's magic)**. AWN Plan 2 shipped the
entire engine (PR #781) but: no `mutations.yaml` in the pack (catalog=None → every
session emits `mutation.init_skipped`), no free-play dispatch route (`magic_working`
knows only pact-working + the WWN cast spine), no beat-path route (the `mutant_ability`
beat is bare narration), no narrator context block, and `magic.yaml` double-truth
unretired. RED scope = Plan 2 spec (2026-06-09-awn-plan2-mutations-design.md) Story B
remainder + Story C + the live production proofs, mirroring 102-2/102-3's spell work.

**Test Files (5, on `feat/102-7-awn-mutant-wasteland-live-wiring`, commits 18206fef + bc9431e5):**
- `tests/agents/test_beat_selection_mutation_id_102_7.py` — BeatSelection.mutation_id sidecar contract (spell_id mirror, 5 tests)
- `tests/server/test_102_7_mutation_beat_use_ops.py` — mutation_resolution-marked beats route through use_ops on the apply path (4 tests, synthetic pack per P2-4)
- `tests/server/test_102_7_freeplay_mutation_magic_working.py` — free-play "I use my X" routes magic_working → mutation engine: gate, bank (id + display name), refusal-is-engagement, failed premise, native safety, real pre-narrator-pass wiring test (8 tests)
- `tests/integration/test_102_7_mutant_wasteland_mutations_live.py` — content-gated real pack: catalog binds, mutant_classes ⊆ archetypes, magic.yaml retirements, beat marker, chargen seam seeds, full production-path live proof (7 tests)
- `tests/mutation/test_102_7_context_builder.py` — narrator mutation context block static/volatile + TurnContext/build_narrator_prompt wiring (7 tests)

**Tests Written:** 31 total. **Status: RED** — 28 failing in the intended
missing-feature shapes (`BeatSelection` has no `mutation_id`; `BeatDef` forbids
`mutation_resolution`; gate drops magic_working on mutation-only surface;
`pack.mutations is None`; `sidequest.mutation.context_builder` missing). The ~3
passers are EXPLICIT regression guards (gate-drops-with-no-surface, native-pack
safety) designed to pass now and keep passing. Zero harness bugs per testing-runner.
Pre-existing AWN/mutation suites: 77/77 pass — work is additive.

### Rule Coverage

| Rule (CLAUDE.md) | Test(s) | Status |
|------|---------|--------|
| Every Test Suite Needs a Wiring Test | `test_pre_narrator_pass_routes_freeplay_mutation` (real gates + bank), `test_production_path_mutation_use_fires_spans_and_strain` (real pack + real apply path), `test_narrator_pre_prompt_contains_mutation_context_when_state_present` | failing (RED) |
| No Source-Text Wiring Tests | all wiring proven via OTEL spans + state deltas; only the §6.3 retirement test is file-shaped (content-state fact, documented in-test) | n/a |
| OTEL Observability Principle | every engagement path asserts `awn.mutation.used/refused/acquired`; chargen visibility asserted | failing (RED) |
| No Silent Fallbacks | `test_marked_beat_without_mutation_id_is_loud_and_inert`, `test_freeplay_unknown_working_is_failed_premise` (loud refusal, no improv-no-cost) | failing (RED) |
| Vacuous-test self-check | every test asserts spans + state values (no `is not None`-only, no `let _`); regression guards assert exact gate/dispatch lists | done |

**Env for GREEN:** full suite with `SIDEQUEST_DATABASE_URL` + `SIDEQUEST_GENRE_PACKS`
set (content-gated tests SKIP without the latter — a skip is NOT a pass for this story).

**Handoff:** To Dev (Inigo Montoya) for GREEN — engine wiring on the server branch,
`mutations.yaml` + retirements + beat marker on the content branch
(`feat/102-7-awn-mutant-wasteland-live-wiring` exists in both repos).

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): the dice path (player-CLICKED beat commit) has no mutation
  selection — the 102-2 mirror for mutations needs `DiceThrowPayload.mutation_id` +
  a UI mutation picker, but 102-7's repos are server,content (no ui).
  Affects `sidequest-ui` + `sidequest/protocol/dice.py` (follow-up story mirroring
  102-2's spell-picker half; the narrator-driven apply path and free-play path are
  covered by this story). *Found by TEA during test design.*
- **Question** (non-blocking): `MutationState` has `reset_scene/reset_day` usage-counter
  hooks but no production caller was located resetting them at scene end / rest —
  without a caller, per-scene mutations exhaust permanently.
  Affects `sidequest/mutation/state.py` (Dev: wire the reset at the scene/rest seam in
  GREEN or confirm an existing caller). *Found by TEA during test design.*
- **Question** (non-blocking): chargen guided MP SPEND (Plan 2 §5.5 — player picks
  positives after negatives roll) has no flow; `seed_character_mutations` rolls
  negatives + banks MP only. Affects `sidequest/mutation/chargen.py` + chargen UI
  (likely its own story; RED tests seed positives directly and don't pin the spend
  flow). *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): `TurnContext.magic_state` has NO production populator —
  `_build_turn_context` (sidequest/server/session_helpers.py) never passes it, so the
  orchestrator's magic-context block (orchestrator.py ~2257) appears to fire only in
  tests; pact-working worlds may be narrating without the magic block.
  Affects `sidequest/server/session_helpers.py` (add `magic_state=snapshot.magic_state`
  after verifying no double-injection via another seam). The new mutation fields ARE
  populated there (102-7 wired them), which is how the gap surfaced.
  *Found by Dev during implementation.*
- **Improvement** (non-blocking): negative-mutation `attr_penalties` and `modifiers`
  (e.g. `system_strain_max: -2`) are catalog data with chargen acquisition but no
  stat-application seam — penalties don't yet flow to character stats/strain max.
  Affects `sidequest/mutation/chargen.py` / `sidequest/game/builder.py` (apply
  machine-readable negative effects at seed time; a Plan 2 follow-up).
  *Found by Dev during implementation.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **"First scene use free, +1 Strain after" powers modeled as flat strain_cost 1, at_will**
  - Spec source: AWN Free Edition p.21-25 (via 2026-06-09-awn-plan2-mutations-design.md §4.4)
  - Spec text: "After the first use of this mutation in a scene, additional uses add 1 System Strain"
  - Implementation: the engine's PositiveMutationDef models flat `strain_cost` + usage period; the ~12 escalating-cost powers carry `strain_cost: 1, usage: at_will`, each effect text noting the source cadence
  - Rationale: never cheaper than the source (costs stay visible — the crunch doctrine); a per-scene-escalation cost model is an engine extension no test pins and Plan 1-2 didn't build
  - Severity: minor
  - Forward impact: a future mutation-economy story could add `first_use_free_per_scene` to the model; content rows are ready to migrate
- **"Once per week" / "once per game session" cadences approximated as per_day**
  - Spec source: AWN p.24 (Redundant Organs), p.22-24 (Intuitive Leap, Predictive Analysis)
  - Spec text: "Once per week…" / "Once per game session…"
  - Implementation: `usage: per_day` (the engine's longest period); effect text carries the true cadence for the narrator to honor
  - Rationale: the engine has per_scene/per_day only; per_day is the closest never-looser-than-daily fit and the narrator register enforces the rest
  - Severity: minor
  - Forward impact: none mechanical until a calendar-aware usage period exists
- **Stigma d12 uses the Textures column only**
  - Spec source: AWN p.17 (four d12 columns: Textures/Appearance/Animal Influence/Plant Influence)
  - Spec text: d12 table with four flavor columns
  - Implementation: StigmaTables.flavor is a single 12-entry list (engine schema); the Textures column ships, the other three are narrator improvisation space (noted in the YAML header)
  - Rationale: schema fixed by Plan 2 Story A (d6/d6/d12 validator); one column is faithful to the roll mechanic
  - Severity: minor
  - Forward impact: none — a flavor-table extension is content-schema work if ever wanted
- **mutant_classes chosen by archetype fiction (Trader/Elder/Beastkin)**
  - Spec source: AWN p.16 ("PCs become mutants by choosing the Mutant Edge" — any class)
  - Spec text: mutancy is an Edge any character may take
  - Implementation: the engine gates chargen seeding by class membership in `mp_economy.mutant_classes`; the three archetypes whose descriptions are mutant-fictioned (Wasteland Trader's "commercially useful mutation", Village Elder's "mutation prestige", the uplifted Beastkin Scout) are in; Ruin Diver/Tech Cultist (baseline humans) and Wandering Synth (a machine) are out
  - Rationale: ADR-097 class-mechanical-surface is the seam Plan 2 §5.5 names; pack archetypes have no Edge picker yet
  - Severity: minor
  - Forward impact: a chargen Edge-style mutation opt-in for the human classes is future content/UX work
- **testing-runner corrected 3 RED fixture values (commit c6774016)**
  - Spec source: TEA RED suite, tests/agents/test_beat_selection_mutation_id_102_7.py
  - Spec text: fixtures passed `outcome: "success"` (lowercase)
  - Implementation: `RollOutcome` enum values are capitalized; the lowercase literal raises in `from_dict` regardless of 102-7's changes (masked at RED by the earlier missing-field TypeError). Fixture inputs corrected to "Success"; assertions untouched
  - Rationale: harness bug, not contract weakening — reviewed by Dev (diff inspected)
  - Severity: minor
  - Forward impact: none

### TEA (test design)
- **RED scope centers mutations, not combat/lethality re-proof**
  - Spec source: story title (102-7, sprint/epic-102.yaml)
  - Spec text: "prove AWN combat + lethality fire live (mirrors heavy_metal/WWN)"
  - Implementation: no new combat/lethality strike-path tests; RED covers the mutation
    system's live wiring (Plan 2 Story B remainder + Story C + production proofs)
  - Rationale: combat + lethality are already live and span-proven (epic 88, 102-1; 77
    pre-existing tests pass, incl. the awn reprisal downed seam) — re-testing green
    paths is duplication; mutations are the measured unwired surface, and they are the
    pack's magic, exactly mirroring what 102-2/102-3 wired for heavy_metal/WWN
  - Severity: minor
  - Forward impact: none — if Reviewer wants a literal re-proof, the existing suites are
    the evidence
- **TEA pinned mechanism details the spec left open**
  - Spec source: 2026-06-09-awn-plan2-mutations-design.md §6.3
  - Spec text: "gains a `mutation_resolution: true` marker (or equivalent wiring the
    Dev story defines)"
  - Implementation: tests pin `BeatDef.mutation_resolution: bool`,
    `BeatSelection.mutation_id` (spell_id precedent), and refusal reason
    `beat_no_mutation_id` (cast_spell_no_spell_id mirror)
  - Rationale: TDD needs a concrete contract; the established 47-10/102-2 sidecar
    pattern makes this the lowest-risk shape. Dev may substitute an equivalent with a
    logged deviation + test adjustment
  - Severity: minor
  - Forward impact: protocol field names become the public contract for the future UI
    dice-path story
- **Free-play mutations reuse magic_working's param shape**
  - Spec source: epic 102 overview (gap #3) + 102-3 param contract
  - Spec text: 102-3 defined `params={"actor", "spell"}` for WN free-play casts
  - Implementation: mutation free-play rides the SAME subsystem + params (the working
    as typed under the `spell` key); the handler resolves against the mutation catalog
    when the snapshot's surface is mutation_state
  - Rationale: the router already classifies "magical ability usage" as magic_working;
    a parallel category would need router prompt changes and double-classification
    risk — the handler is the right resolution point
  - Severity: minor
  - Forward impact: if a future pack carries BOTH spellcasting and mutations on one PC,
    the handler needs a disambiguation rule (catalog-hit order); flagged in test
    docstring

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->