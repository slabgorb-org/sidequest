---
story_id: "162-5"
jira_key: ""
epic: "162"
workflow: "tdd"
---
# Story 162-5: flickering_reach content reconciliation

## Story Details
- **ID:** 162-5
- **Epic:** 162 — NPC origin consolidation
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 2
- **Type:** bug
- **Priority:** p2

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-07-06T02:35:33Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-06T00:44:16Z | 2026-07-06T00:46:25Z | 2m 9s |
| red | 2026-07-06T00:46:25Z | 2026-07-06T01:02:59Z | 16m 34s |
| green | 2026-07-06T01:02:59Z | 2026-07-06T01:40:31Z | 37m 32s |
| review | 2026-07-06T01:40:31Z | 2026-07-06T02:00:38Z | 20m 7s |
| green | 2026-07-06T02:00:38Z | 2026-07-06T02:18:45Z | 18m 7s |
| review | 2026-07-06T02:18:45Z | 2026-07-06T02:35:33Z | 16m 48s |
| finish | 2026-07-06T02:35:33Z | - | - |

## Story Context

### Technical Summary
The flickering_reach world has two content reconciliation issues blocking V4 verification (NPC-generation inventory spec §5, V4 gate):

1. **18 phantom creature refs in encounter_tables.yaml:** References to creature IDs that don't exist in the bestiary. Originally authored against an abandoned form-name scheme; only `silo_eye` and `glass_touched_mount` resolve. ~90% of authored encounters are unspawnable.

2. **creatures.yaml divergent stat blocks:** flickering_reach maintains a full parallel stat block in creatures.yaml that diverges from its bestiary (example: `silo_eye` has L8/hp36/ac16/2d6 in creatures.yaml vs tier[3,4]/hp30/ac14/1d8+2 in bestiary). Per ADR-155, creatures.yaml is render-only (image generation overrides), not a runtime source.

**V4 Gate (from spec):** Confirm whether the native-path encountergen (`_collect_creatures_from_yaml` in `encountergen.py:231`) still reads creatures.yaml stats at runtime. If yes, the divergent stat block is live ammunition. If no, it's dead content and should be removed per "No Stubbing" principle.

### Acceptance Criteria
- [ ] **AC1:** All 18 phantom creature IDs in `flickering_reach/encounter_tables.yaml` are remapped to valid bestiary creature IDs or confirmed as intentionally removed encounters
- [ ] **AC2:** `flickering_reach/creatures.yaml` divergent stat blocks are verified as render-only or removed per ADR-155 and No Stubbing
- [ ] **AC3:** V4 gate verification complete: Confirm native-path encountergen behavior (does `_collect_creatures_from_yaml` read stat blocks at runtime in current code?)
- [ ] **AC4:** Test wiring confirms the reconciliation — at least one integration test demonstrating correct creature resolution for flickering_reach encounters

### Context References
- **Spec:** docs/superpowers/specs/2026-07-05-npc-generation-inventory.md (§5, V4 gate)
- **Related ADR:** ADR-155 (Bestiary-Derived Creature Images — bestiary.yaml is the single source of truth)
- **Related Stories:** 162-1 (Derive-don't-cache Monster Manual), 162-2 (Identity by id, not name), 162-3 (Bestiary generics replace ephemeral stub minting)
- **Comparison:** seaboard_of_saints resolves 100% — use as clean example

### Branch Strategy
**Branch Strategy:** gitflow (feat/162-5-flickering-reach-content-reconciliation)

## Sm Assessment

**Setup complete — routing to TEA (Amos Burton) for RED phase.**

**What this story is:** The flickering_reach world content-reconciliation follow-up to the completed bestiary consolidation (162-1/2/3). Pure content-repo work (sidequest-content, gitflow off `develop`). Two defects plus a code-inspection gate:

1. **18 phantom encounter-table creature refs** — `flickering_reach/encounter_tables.yaml` references creature IDs that don't exist in the bestiary (only `silo_eye` and `glass_touched_mount` resolve today; ~90% of authored encounters are unspawnable). These must be remapped to real bestiary ids or confirmed as intentional removals.
2. **Divergent creatures.yaml stat block** — flickering_reach keeps a full parallel stat block that diverges from the bestiary. Per ADR-155, creatures.yaml is render-only (image overrides), not a runtime stat source.

**The load-bearing gate (V4):** AC3 must be settled *first*, because it determines whether AC2 is a deletion or a demotion. Confirm whether the native encountergen path (`_collect_creatures_from_yaml`, encountergen.py ~231 in sidequest-server) still reads creatures.yaml stats at runtime. If it does, the divergent block is live ammunition and reconciliation must reconcile the numbers; if it doesn't, the block is dead content and goes per "No Stubbing." This is a read-only code inspection on the server repo — the *fix* lands in content, but the gate answer lives in server code.

**Doctrine that governs the fix:**
- **No Silent Fallbacks / No Stubbing** — phantom refs must resolve to real ids or be honestly removed; don't leave dead stat blocks.
- **ADR-155** — bestiary.yaml is the single source of truth; creatures.yaml demotes to optional render-only override.
- **AC4 (wiring test)** — at least one integration test proving flickering_reach encounter creatures actually resolve end-to-end. `seaboard_of_saints` resolves 100% — use it as the clean-example baseline.

**Scope guardrails for TEA/Dev:** This is content reconciliation, not engine work. Do not tune the native combat engine or rebalance stats to "make it work" (Bind-the-Ruleset doctrine, ADR-143). The bestiary ids are the truth; the encounter table conforms to them.

**Assessment:** Well-scoped 2-pt bug. ACs are testable and ordered (V4 gate → stat-block disposition → ref remap → wiring test). No dependency/stack gate (no `depends_on`). Merge gate clear. Ready for RED.

## TEA Assessment

### Red Phase (test writing)

**Tests Required:** Yes
**Status:** RED (verified via testing-runner, serial `-n0`: **4 failed / 2 passed**, 6 collected, 0 skipped, 0 errors — every failure is genuine feature-absence, zero harness/import/collection bugs)

**V4 gate — SETTLED: YES.** flickering_reach's runtime *does* resolve creatures.yaml stats. `encountergen.main()` (`cli/encountergen/encountergen.py:788-805`): given `--world` + a non-empty `creatures.yaml`, it samples creatures.yaml and returns EnemyBlocks via `creature_to_enemy_block` (reading hp/ac/damage) **before** the documented `effective_bestiary` path. `server/dispatch/pregen.py:214` invokes `encountergen_main` in-process with `--world`, so the divergent block is **live ammunition** — a spawned silo_eye carries hp30, not the bestiary's hp36. Per the story's own V4=YES branch, AC2 is therefore a **reconcile** (make creatures.yaml numbers equal the bestiary), not a strip.

**Test Files (sidequest-server, commit `0f6c0142` on `feat/162-5-flickering-reach-content-reconciliation`):**
- `tests/genre/test_162_5_flickering_reach_reconciliation.py` — AC1 (every encounter ref ⊆ effective_bestiary ids; 18/20 phantom → RED), AC2 (creatures.yaml combat fields absent-or-equal to bestiary; 9/10 shared ids diverge on hp → RED), AC4 wiring (every ref resolves to a stat-carrying `BestiaryEntry` via the runtime accessor → RED), plus a GREEN positive control (`seaboard_of_saints` resolves 100%).
- `tests/cli/test_162_5_encountergen_v4.py` — V4 characterization pin (`_collect_creatures_from_yaml` reads flickering_reach creatures.yaml → GREEN, tripwire), and the behavioral tie (spawned `EnemyBlock.hp` must equal bestiary hp → RED). The RED behavioral tie is what forces AC2 to reconcile rather than strip (a stripped field spawns at hp-default 4, still ≠ bestiary).

**Tests Written:** 6 (4 RED covering AC1/AC2/AC4/V4-runtime + 2 labeled GREEN guards) across 4 ACs.

**RED census (from testing-runner):** AC1 — 18 phantom refs `[alkali_worm, bone_kite, canopy_striker, canyon_leech, dust_strider, gene_reject, glass_crawler, maintenance_drone, psychic_frog, root_puppet, rust_louse, scrap_lurker, signal_moth, spore_shambler, static_hound, thorn_singer, vault_growth, wire_rat]`; resolvable roster is the 10 world-bestiary ids. V4-runtime — 9/10 shared ids diverge on hp (silo_eye 30→36, glass_touched_mount 14→18, peace_speaker 8→18, protocol_sentinel 22→27, signal_chorus 1→13, tangle_mouth 25→22, tithe_born 6→22, understory_hand 10→9, echo_frog 1→4); `dust_drinker` already matches (4=4).

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #6 test quality (no vacuous asserts) | every test has a non-vacuous guard (refs/shared/bestiary non-empty) + specific-value asserts; 2 green guards labeled | pass (self-check) |
| #3 type annotations at boundaries | all test fns `-> None`; helpers annotated (`_dice`, `_encounter_creature_refs`, ...) | pass |
| #5 path handling | `pathlib.Path` + `read_text(encoding="utf-8")`; no string path concat | pass |
| #8 unsafe deserialization | `yaml.safe_load` (never `yaml.load`) | pass |
| No Source-Text Wiring Tests (server CLAUDE.md) | tests drive behavior — `effective_bestiary`, `_collect_creatures_from_yaml`, `creature_to_enemy_block` — zero source-text grepping | pass |

**Rules checked:** 4 of 13 lang-review checks applicable to this diff (gated read-only YAML/loader tests) have coverage; #1/#2/#4/#7/#9-#13 not applicable (no exception handling, mutable defaults, logging, resources, async, imports, boundaries, deps, or fixes in these tests).
**Self-check:** 0 vacuous tests found.

**GREEN guidance for Dev (Naomi Nagata):**
- **AC1 is not 18 trivial renames.** 20 distinct refs vs 10 world-bestiary ids; ~11 refs have no bestiary equivalent (`static_hound, maintenance_drone, bone_kite, dust_strider, wire_rat, scrap_lurker, canyon_leech, alkali_worm, glass_crawler, rust_louse, vault_growth`). Some map cleanly (`signal_moth→signal_chorus`, `psychic_frog→echo_frog`, `canopy_striker→tangle_mouth`, `gene_reject→tithe_born`, `root_puppet/spore_shambler/thorn_singer→understory_hand/peace_speaker`). The remainder force a call: promote a creatures.yaml ecology entry (`static_singer`, `conclave_remnant`, `bone_saint`) into a bestiary combat block, or cut the encounter (AC1 accepts "intentionally removed").
- **AC2/V4:** reconcile creatures.yaml `hp`/`ac`/`damage` to the bestiary for the 10 shared ids (9 hp diverge; `dust_drinker` already matches). Do NOT strip the stats — V4=YES means a stripped creatures.yaml spawns hp-default husks.
- **Content edits land in sidequest-content** (`feat/162-5-...`, already checked out); the server test branch is already committed.

**Handoff:** To Dev for GREEN — content reconciliation in sidequest-content (encounter_tables remap + creatures.yaml stat reconcile), driven by the RED tests on the server branch.

## Dev Assessment

**Implementation Complete:** Yes
**Approach:** Hybrid (user-selected via AskUserQuestion) — expand the world bestiary + remap synonyms + drop the terrain hazard.

**Files Changed (sidequest-content, commit `2ce8059` on `feat/162-5-flickering-reach-content-reconciliation`, pushed):**
- `genre_packs/mutant_wasteland/worlds/flickering_reach/bestiary.yaml` — world roster **10 → 16**. Promoted `static_singer` + `conclave_remnant` from creatures.yaml (combat numbers shared verbatim); authored `scrap_lurker`, `bone_kite`, `wire_rat`, `canyon_leech` on the AWN foe ladder (L1→+2/hp4 … L4→+6/hp18) so every recurring encounter creature has a real stat block.
- `genre_packs/.../flickering_reach/encounter_tables.yaml` — remapped all 18 phantom refs to real bestiary ids (signal_moth→signal_chorus, psychic_frog→echo_frog, canopy_striker→tangle_mouth, gene_reject→tithe_born, root_puppet/spore_shambler/thorn_singer→peace_speaker, glass_crawler/alkali_worm/rust_louse→dust_drinker, dust_strider→glass_touched_mount, maintenance_drone→conclave_remnant, static_hound→static_singer); dropped the single `vault_growth` encounter (crystalline terrain hazard, not a foe).
- `genre_packs/.../flickering_reach/creatures.yaml` — reconciled the 10 shared-id combat blocks (hp/max_hp/ac + damage dice) to the bestiary per ADR-155; flavor text preserved. (static_singer/conclave_remnant needed no change — the bestiary was authored to their numbers.)

**AC status:**
- **AC1** ✓ every encounter `creature:` ref resolves to a bestiary id (0 phantom; verified refs ⊆ 16-entry roster).
- **AC2** ✓ creatures.yaml no longer diverges from the bestiary (all shared-id combat fields match).
- **AC3 (V4)** ✓ settled YES and encoded as a permanent test; divergence removed so the live encountergen path now spawns bestiary-true stats.
- **AC4** ✓ every ref resolves to a stat-carrying `BestiaryEntry` through `effective_bestiary` (wiring test green).

**Tests:** 6/6 story tests PASS (`-n0`). Regression sweep **1280 passed / 0 failed / 75 skipped** across `tests/cli/test_encountergen.py`, `tests/genre/`, monster-manual, encounter, and mutant_wasteland/flickering_reach integration suites — no regressions.
**Branches:** `feat/162-5-flickering-reach-content-reconciliation` pushed in **both** sidequest-content (`2ce8059`, the fix) and sidequest-server (`0f6c0142`, TEA's tests).

**Server-side V4 note (not fixed here, by design):** the real ADR-155 violation is `encountergen.main()`'s creatures.yaml early-return reading creatures.yaml *instead of* `effective_bestiary`. After this reconcile the numbers match, so the early-return is now harmless — but it's still the wrong source. Left as the standing server follow-up (TEA's finding; epic-162 D6). Not in this content story's scope (SOUL "Bind the Ruleset" / no engine work here).

**Handoff:** To TEA (Amos Burton) for the verify phase (simplify + quality-pass).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (6/6 tests pass, bestiary loads 16 entries, ruff clean; applied 1 cosmetic yoda-flip to a test) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 7 | confirmed 5 (1 high, 3 med, 1 low), deferred 2 low (synthetic-fixture / control-mutation — optional) |
| 5 | reviewer-comment-analyzer | Yes | findings | 8 | confirmed 6 (1 high, 1 med, 4 low), deferred 2 (low text-consistency) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | 0 violations / 19 rules / 96 instances (1 minor non-violating note: conclave_remnant hp) | confirmed 0, noted 1 low |

**All received:** Yes (4 ran, 5 disabled via `workflow.reviewer_subagents`)
**Total findings:** 1 high + 6 medium + 6 low confirmed; 4 deferred/low-optional; rule-checker clean (0 violations).

## Reviewer Assessment

**Verdict:** REJECTED

The reconciliation is *mechanically* complete and correct — AC1 (0 phantom refs), AC2 (rule-checker verified all 12 shared ids match the bestiary exactly), and AC3/V4 (settled + pinned) are solid, and the whole thing is rule-clean (0 violations across 19 rules). But two things block merge: (1) the consolidation left **encounter narration describing a different creature than the one that spawns** — a Genre-Truth defect in Keith's one fully-spoilable playtest world, exactly what a 40-year GM notices instantly; and (2) **AC4 is not the wiring/integration test it claims to be** — `encounter_tables.yaml` has no runtime consumer, so the test proves a static cross-file invariant (a near-duplicate of AC1) and carries a dead assertion. Cheap to fix, in-scope, and the difference between "IDs resolve" and "the content is play-ready."

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] `[DOC]` | 5 encounters remapped onto `dust_drinker` still narrate "multiple crawlers" / "a colony of rust lice" / "the worms are feeding" / "a glass crawler at the boundary" — but `dust_drinker` is a limbless, sacred, harmless dust-bladder. And `echo_frog`'s prose says "Not an encounter. An atmosphere." while it is now a wired spawnable encounter (counts [10,30]/[3,6]). The narrator would describe the wrong creature. Genre-Truth violation. | `encounter_tables.yaml:73,77,140,165,175`; `creatures.yaml` echo_frog (`:600`) | Rewrite the consolidated situation blocks to describe the spawned creature (or the situations that map onto `dust_drinker`); reconcile `echo_frog` prose to its wired-encounter reality |
| [MEDIUM] `[TEST]` | `test_ac4_encounters_spawnable_through_effective_bestiary` is named/documented as a wiring test ("the accessor the live MM injection / seater / materializer use"), but `encounter_tables.yaml` is read by NO production path (`loader.py` never parses it; `pregen._generate_encounter` passes only `--genre/--world/--count/--tier`; `WorldGraphNode.encounter_table_key` is declared, never read). It's a content invariant ≈ AC1, plus a dead `if entry.hp < 1 or entry.armor_class < 1` branch (BestiaryEntry enforces `Field(ge=1)`, so it can never fire). | `test_162_5_flickering_reach_reconciliation.py:228,248` | Reframe AC4 as a content-invariant test (the genuine wiring test is the V4 `creature_to_enemy_block` tie); remove the dead branch |
| [MEDIUM] `[DOC]` | Prose/stat contradiction: `dust_drinker` weakness "Physically helpless" and `echo_frog` "Physically helpless" / "fragile" now sit on creatures with real 1d6 / 1d4 attacks (the reconcile bumped them from `0 (harmless)`). "Physically helpless" is reserved elsewhere for genuinely attack-less creatures (`resonance_grazer`). | `creatures.yaml:229,593,595` | Soften/rewrite the "physically helpless/harmless" prose to match the reconciled combat numbers |
| [MEDIUM] `[DOC]` | Possible mis-remap: `thorn_singer`→`peace_speaker`, but the situation ("an unpruned thorn singer… a tree that shouldn't be humming… bone pile") reads as a sessile plant-trap — `tangle_mouth` ("we prune them", lure-scent) fits better than a mobile reanimated corpse. | `encounter_tables.yaml:613` | Verify intended id; if `peace_speaker` is right, drop the tree/pruning framing |
| [MEDIUM] `[TEST]` | Coverage gaps: the V4 behavioral tie asserts `enemy.hp` only — `creature_to_enemy_block` never sets `EnemyBlock.armor_class` on the native path (folds AC into `weaknesses`), so an ac/damage-read regression ships silently. AC2's damage check is gated on `c_dice and b_dice`, forgiving the "bestiary damage None, creatures asserts a dice" divergence the header forbids. | `test_162_5_encountergen_v4.py:107`; `test_162_5_flickering_reach_reconciliation.py:213` | Assert AC (parse `"AC {n}"` from weaknesses) in the V4 tie; mirror AC2's damage gating on hp/ac (flag when `c_dice` present and `b_dice` None-or-mismatch) |
| [LOW] `[DOC]` | Stale docstrings: both test files still say "(GATED, RED)" / "RED today" / "silo_eye hp30 vs hp36" — the content fix landed on the same branch and all 6 tests are GREEN. | `test_162_5_flickering_reach_reconciliation.py:1,33`; `test_162_5_encountergen_v4.py:1,20,85` | Update docstrings to the GREEN regression-guard end-state |
| [LOW] `[DOC]` | `bestiary.yaml` reconciled-fauna comment cites ADR-155 to justify keeping *combat numbers* in sync, but ADR-155 governs creature-*image* production (SSOT for id/name/description/tags), not hp/ac/damage. | `bestiary.yaml:256` | Drop/correct the ADR-155 citation (or cite ADR-121 per-field merge / state the practical rule) |
| [LOW] `[RULE]` | `conclave_remnant` hp 16 at L3 is ~15-18% above the file's own ~4.5/HD convention (attack_bonus/save are exact ladder matches). Authorial texture, not a violation. | `bestiary.yaml` conclave_remnant | Optional: trim toward ~13-14, or accept as armored-machine texture |
| [LOW] `[DOC]` | `signal_moth`→`signal_chorus` remap leaves situation text "a cloud of signal moths" (same creature, old common name). | `encounter_tables.yaml:42` | Optional consistency pass |

**Subagent dispatch coverage:** `[EDGE]` — N/A (disabled); `[SILENT]` — N/A (disabled); `[TEST]` — 5 confirmed (AC4-not-wiring, dead branch, V4 hp-only, AC2 asymmetry, gated-only); `[DOC]` — 6 confirmed (situation/creature mismatch, echo_frog contradiction, dust_drinker prose, thorn_singer remap, stale docstrings, ADR-155 citation); `[TYPE]` — N/A (disabled); `[SEC]` — N/A (disabled, and no security surface: content YAML + read-only fixture tests, no auth/input/secrets); `[SIMPLE]` — N/A (disabled); `[RULE]` — 0 violations (rule-checker clean, 1 low note).

### Rule Compliance

Rules enumerated against the changed code (SOUL.md, sidequest-content/CLAUDE.md, ADR-155, python lang-review). Backstopped by reviewer-rule-checker (clean).

- **ADR-155 (bestiary is single source of truth; creatures.yaml render-only, non-divergent):** 12 shared ids (conclave_remnant, dust_drinker, echo_frog, glass_touched_mount, peace_speaker, protocol_sentinel, signal_chorus, silo_eye, static_singer, tangle_mouth, tithe_born, understory_hand) — ALL match hp/ac/damage-dice exactly. **COMPLIANT.** (Caveat: the story treats ADR-155 as also governing runtime stat sync; ADR-155's text is scoped to image production — see [DOC] finding. The substantive rule — no divergence — holds.)
- **No Silent Fallbacks:** all 54 encounter refs resolve to a real bestiary id; the unresolvable `vault_growth` was deleted, not masked. **COMPLIANT.**
- **No Stubbing:** all 6 new bestiary entries carry full stats + role + 2-3 abilities + description. No skeletons. **COMPLIANT.**
- **Bind the Ruleset, Don't Balance It (AWN foe ladder):** 6 new entries — wire_rat(L1 +2/hp4), canyon_leech(L2 +3/hp9), static_singer(L2 +3/hp10), scrap_lurker(L3 +4/hp13), conclave_remnant(L3 +4/hp16), bone_kite(L4 +6/hp18). attack_bonus/save exact ladder matches; hp within convention (conclave_remnant +2-3 high — LOW note). No new balance system invented. **COMPLIANT.**
- **BestiaryEntry model (required fields, unique ids):** 16/16 load through the real pydantic model, 0 ValidationError, 0 duplicate ids. **COMPLIANT.**
- **Genre Truth / The Test (SOUL):** **VIOLATION** — consolidated encounter narration describes creatures that don't match the spawned id (HIGH finding). This is the block.
- **Verify Wiring, Not Just Existence / Every Test Suite Needs a Wiring Test (CLAUDE.md):** the suite DOES have a genuine wiring test (V4 `creature_to_enemy_block` drives real production code); AC4's *self-labeling* as the wiring test is inaccurate (MEDIUM finding). No source-text wiring tests present. **PARTIAL** — real wiring covered by V4, AC4 mislabeled.
- **python lang-review (13 checks):** rule-checker verified all applicable checks pass on both test files (type annotations, pathlib+encoding, yaml.safe_load, no vacuous asserts beyond the flagged dead branch). **COMPLIANT** (dead-branch is the one [TEST] exception).

### Devil's Advocate

Argue this ships broken. A party crosses the Przyå Dust. The narrator reads encounter row 3: *"A colony of rust lice has found your camp. Your cookware is developing a fine orange patina. Tiny movement in the powder caked on your gear."* It then instantiates a `dust_drinker` — which this world's own bestiary and lore describe as a limbless, organless, **sacred** dust-bladder that Drifters will execute you for harming, symbiotic with their mounts. So the narration promises metal-eating vermin and the mechanical entity is a revered keystone organism. Keith — a forty-year GM — reads that seam in one beat and the illusion dies. Worse, `echo_frog`: its own record says *"Not an encounter. An atmosphere. The narrator should describe the dusk chorus… It should never be comfortable"* — yet the encounter table now lists it, difficulty trivial, count [10,30], as something to fight. The narrator receives contradictory marching orders and does what a cornered narrator always does: improvises, unbacked — the precise "winging it" the OTEL lie-detector exists to expose. On the test side, false confidence: AC4 is named a wiring test "demonstrating correct creature resolution," but nothing in the running server reads `encounter_tables.yaml` — so a future change that breaks a (nonexistent) consumer sails through green, and a reader trusts a wiring guarantee that was never made. Its degenerate-stat guard `hp < 1 or armor_class < 1` is unreachable — pydantic's `Field(ge=1)` rejects such an entry at parse, so the branch can never catch the husk regression its comment claims. The V4 tie checks only HP; a bug where `creature_to_enemy_block` reads the wrong `ac`/`damage` key ships with a green suite. None of this is a crash or a security hole — but for a *content-reconciliation* story whose entire purpose is coherence, shipping encounters whose narration lies about the monster is the defect, not a nitpick.

**Data flow traced:** `encounter_tables.yaml creature:` ref → (no runtime consumer today) → the reconciliation's real runtime effect is `creatures.yaml` → `pregen._generate_encounter` → `encountergen.main` creatures.yaml branch → `creature_to_enemy_block` → `EnemyBlock` (now bestiary-true HP; V4 test guards this). The bestiary roster → `effective_bestiary` → MM inject / seater / materializer (real consumers). Safe mechanically; incoherent narratively (HIGH).

**Handoff:** Back to Dev (Naomi Nagata) for green rework — content coherence (situation prose + echo_frog/dust_drinker reconcile + thorn_singer remap check + ADR-155 comment) and the trivial test fixes (stale docstrings, dead AC4 branch); coordinate the V4-ac / AC2-asymmetry test enhancements with TEA if pursued.

## Dev Assessment (Rework — Round 1)

**Implementation Complete:** Yes (addresses Reviewer REJECT)
**Commits:** content `1315f67`, server `15c0999b` (both pushed to `feat/162-5-flickering-reach-content-reconciliation`)

**Findings resolved:**
- **[HIGH] situation/creature mismatch** → rewrote every consolidated encounter's `situation:` prose to describe the spawned creature: the 7 `dust_drinker` encounters now narrate Przyå Dust-Drinkers (ash-coloured drift-ambusher, caustic brine) instead of crawlers/rust lice/worms; the 3 `dust_strider`→`glass_touched_mount` encounters describe the feral seven-limbed bioluminescent mount.
- **[HIGH] echo_frog "Not an encounter" contradiction** → reconciled `echo_frog` `notes` ("primarily an atmosphere… the mourning croak is its only real mechanical bite") and `weaknesses` ("individually near-harmless — weight is psychic, not physical") to its wired-encounter reality; same for `dust_drinker` ("no active attack — but its hide weeps a caustic brine that burns…").
- **[MEDIUM] thorn_singer mis-remap** → remapped the 2 `thorn_singer` refs `peace_speaker`→`tangle_mouth` (sessile "pruning/tree/bone-pile" lure = tangle-mouth) and aligned prose; also renamed the `canopy_striker`→`tangle_mouth` prose ("strikers"→"tangle-mouths") and `static_hound`→`static_singer` prose ("static hounds"→"static singers").
- **[MEDIUM] AC4 not-a-wiring-test + dead branch** → renamed to `test_ac4_encounters_resolve_through_effective_bestiary`, reframed docstring as a content-referential invariant (encounter_tables.yaml has no runtime consumer; the V4 tie is the genuine wiring test), removed the unreachable `hp<1/ac<1` branch (pydantic `ge=1`).
- **[MEDIUM] V4 hp-only + AC2 asymmetry** → V4 tie now also asserts AC (parsed from `EnemyBlock.weaknesses` "AC {n}"); AC2 damage check now flags a dice value creatures.yaml asserts that the bestiary doesn't match (incl. bestiary-None).
- **[LOW] stale RED docstrings / ADR-155 comment** → both test files' docstrings updated to the GREEN regression-guard end-state; bestiary reconciled-fauna comment corrected (ADR-155 = render demotion; the bestiary owns the stats; numbers kept identical by hand).
- **[LOW] conclave_remnant hp (~15-18% over ladder)** → left at 16 (matches the promoted creatures.yaml value; armored-machine texture; attack_bonus/save are exact ladder). Non-blocking, accepted.
- **[LOW] signal_moth prose** → left ("glass-winged moths" is accurate to signal_chorus per the bestiary description). `root puppet`/`shambler` prose also left — accurate descriptors of peace_speaker (a root-puppeted, shambling reanimated corpse), not a category mismatch.

**Tests:** 6/6 story tests PASS (`-n0`); ruff clean on both test files; YAML loads (16 bestiary entries); regression **1189 passed / 0 failed / 74 skipped**.

**Handoff:** Back to Reviewer (Chrisjen Avasarala) for re-review.

## Subagent Results (Re-review — Round 2)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (6/6 green, ruff+pyright clean, YAML loads 16, trees clean) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | clean | 2 low (all 4 prior findings resolved, mutation-verified) | confirmed 0 blocking; 2 low noted (AC-parse coupling fails-loud; two-layer divergence) |
| 5 | reviewer-comment-analyzer | Yes | findings | 6 (graded 2 high / 2 med / 2 low); original HIGH confirmed RESOLVED | 0 blocking — 2 "high" downgraded to MEDIUM (Challenged, rationale below); all documented as non-blocking follow-ups |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | 0 violations / 17 rules (ADR-155 12/12 exact unchanged, 0 phantom, 16 entries/0 dup, ruff+pyright clean) | N/A |

**All received:** Yes (4 ran, 5 disabled via `workflow.reviewer_subagents`)
**Total findings:** Original blocking HIGH (dust_drinker/echo_frog narration) **RESOLVED** (test + mutation verified). Re-review surfaced pre-existing two-file definition seams + one self-inflicted comment-nuance — 0 Critical/High by reviewer judgment; all captured as non-blocking follow-ups.

## Reviewer Assessment (Re-review — Round 2)

**Verdict:** APPROVED

The round-1 blocker is genuinely fixed, and I verified it three independent ways (not just Dev's claim): comment-analyzer's grep sweep found **zero** phantom/mismatched terms as `creature:` refs; test-analyzer **mutation-tested** every assertion (flipped `silo_eye.ac` 16→14 and a phantom ref, confirmed AC1/AC2/AC4/V4 catch them, reverted clean); rule-checker confirmed ADR-155 12/12 exact-match is **byte-for-byte unchanged** from the prior pass (the rework is prose-only) and the tests are ruff+pyright clean. Every encounter now names a bestiary-backed creature whose narration matches the authoritative definition. ACs 1–4 are met and test-verified GREEN.

**Challenged — comment-analyzer graded two findings HIGH; I downgrade both to MEDIUM (non-blocking), with rationale:**
- `[DOC]` **tangle_mouth reads as mobile in 3 encounters, sessile in 2.** Downgraded because the mobile encounters (canopy_striker→tangle_mouth) match the **bestiary** role ("canopy apex predator… climbs and ambushes from the canopy" — the authoritative combat/spawn source), and the sessile ones (thorn_singer→tangle_mouth) match creatures.yaml. Each encounter matches a *valid* definition of the spawned creature — unlike round-1's dust_drinker, whose "rust lice" narration matched *no* definition. The true defect is a **pre-existing** bestiary↔creatures.yaml contradiction in tangle_mouth's own definition (both files shipped that way before epic 162); reconciling it is a creature-definition pass, not this reconciliation story's scope. Deferred (see Delivery Findings).
- `[DOC]` **bestiary.yaml comment says "render-only per ADR-155" which the story's own V4 test contradicts (creatures.yaml is a live spawn source).** Real and self-inflicted in the rework, but comment-only impact and its practical thrust ("keep the numbers synced") is correct. Downgraded to MEDIUM; deferred as a should-fix follow-up (a future author could be misled). Not worth a third full review round on a 2-pt story.

**Confirmed non-blocking (deferred follow-ups):**
- `[DOC]` (MEDIUM) dust_drinker `description` ("no limbs… deflated bladder") and echo_frog (`damage: 1d4 (bite)` with no bite ability, prose "harmless") still contradict their bestiary combat roles — a **pre-existing** bestiary↔ecology description split this story surfaced; the *weakness* bullets were reconciled, the descriptions were not (out of scope).
- `[DOC]` (LOW) signal_chorus encounter says "moths/wings" (bestiary licenses "glass-winged moths" — pre-existing); "root puppet"/"shambler" peace_speaker nicknames unconfirmed but plausible faction slang.
- `[TEST]` (LOW) V4 AC-parse couples to the exact `"AC {n}"` weakness format — but drives the real `creature_to_enemy_block`, so a format change fails loudly (acceptable).

**Subagent dispatch coverage:** `[EDGE]` N/A (disabled); `[SILENT]` N/A (disabled); `[TEST]` clean — 4 prior findings resolved + mutation-verified, 2 LOW noted; `[DOC]` original HIGH resolved; 2 called-HIGH downgraded to MEDIUM + deferred, 3 LOW; `[TYPE]` N/A (disabled); `[SEC]` N/A (disabled; content YAML + read-only tests, no security surface); `[SIMPLE]` N/A (disabled); `[RULE]` 0 violations / 17 rules.

**Data flow traced:** encounter `creature:` ref → all resolve to a bestiary-backed id → runtime spawn via creatures.yaml→`creature_to_enemy_block` (V4 path, bestiary-true stats) and the roster via `effective_bestiary`. Narration now matches the authoritative creature definition. Safe.

**Rule Compliance (re-verified):** ADR-155 stat-sync 12/12 exact (unchanged); No Silent Fallbacks / No Stubbing (0 phantom, full entries); Bind-the-Ruleset AWN ladder unchanged (prose-only rework); BestiaryEntry model 16/16 load, 0 dup; python lang-review clean (ruff+pyright). The remaining `[DOC]` items are content-prose coherence, not rule violations (no rule requires bestiary role prose to match creatures.yaml ecology prose; the STATS — which ADR-155/the reconcile govern — do match).

**Handoff:** To SM (Camina Drummer) for finish. **Blocking-for-finish reminder:** story is scoped `repos: content` but spans **server + content** (branches `feat/162-5-flickering-reach-content-reconciliation` in both; content `1315f67`, server `15c0999b`) — SM must set `repos: server,content` so both PRs merge.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)

- **Conflict** (blocking for finish): Story is SM-scoped `repos: content`, but the work requires a **server branch too** — content-referential tests have no home in sidequest-content (no root pytest/justfile; only per-tool venvs) and AC4/V4 need the server genre loader + encountergen. RED tests are committed on `feat/162-5-flickering-reach-content-reconciliation` in **sidequest-server** (`0f6c0142`); the branch also exists in sidequest-content. The story repos should be `server,content` (mirroring sibling 162-3). Affects `sprint/epic-162.yaml` / session `**Repos:**` (SM to widen to `server,content` so the finish flow, which reads REPOS, sees both branches/PRs). *Found by TEA during test design.*
- **Question** (non-blocking): V4=YES exposes that the real ADR-155 violation is server-side — `encountergen.main()`'s creatures.yaml early-return (`cli/encountergen/encountergen.py:788-805`) reads creatures.yaml stats *instead of* `effective_bestiary`, contradicting its own docstring. 162-5's content reconcile removes the *divergence* but leaves creatures.yaml as a live (now-redundant) stat source. The correct end-state is deleting the early-return so encountergen reads only the bestiary. Recommend a follow-up **server** story (fits epic-162 D6 / seating-stack diet). Affects `sidequest-server/sidequest/cli/encountergen/encountergen.py` (remove creatures.yaml sampling branch). *Found by TEA during test design.*
- **Improvement** (non-blocking): The pack validator (`sidequest-server/sidequest/cli/validate/pack.py`) has no encounter_tables→bestiary referential-integrity check — that gap is why 18 phantom refs shipped undetected. A validate rule would prevent regression across all worlds (seaboard/flickering + per-room `encounter_creatures`). Affects `sidequest/cli/validate/pack.py` (add cross-ref lint). *Found by TEA during test design.*
- **Improvement** (non-blocking): SM assessment/context has the silo_eye stat attribution reversed — it reads "L8/hp36/ac16/2d6 in creatures.yaml vs tier[3,4]/hp30/ac14 in bestiary," but the RED output confirms the opposite (L8/hp36 is in **bestiary.yaml**; tier[3,4]/hp30 is in **creatures.yaml**). Substance (divergence) unaffected. Affects `.session/162-5-session.md` / `sprint/context/context-story-162-5.md` (doc note only). *Found by TEA during test design.*

### Dev (implementation)

- **Conflict** (blocking for finish, reaffirms TEA): the fix spans **two repos** — content fix on `feat/162-5-flickering-reach-content-reconciliation` in **sidequest-content** (`2ce8059`, pushed) and tests on the same branch in **sidequest-server** (`0f6c0142`, pushed). Session `**Repos:**` says `content` only. Affects `sprint/epic-162.yaml` / session repos field (SM must set `server,content` so the finish flow opens/merges both PRs). *Found by Dev during implementation.*
- **Improvement** (non-blocking): the dropped `vault_growth` encounter was a crystalline-terrain battery-drain hazard, not a foe. Its atmosphere would be better carried by a Vault Echo **location description** (ADR-109) than a creature encounter. Affects `genre_packs/mutant_wasteland/worlds/flickering_reach/` (optional future location-desc authoring). *Found by Dev during implementation.*
- **Improvement** (non-blocking): `understory_hand` and `protocol_sentinel` remain in the bestiary but are now **unreferenced by encounter_tables** (no encounter fiction matched a lone root-tendril grab or a vault-security automaton). They are still reachable via the MM pool / opponent-seater / other spawn paths, so this is intentional, not dead content — noted for the Reviewer so it isn't flagged as an orphan. *Found by Dev during implementation.*

### Reviewer (code review)

- **Gap** (non-blocking, epic-level): `encounter_tables.yaml` has **no runtime consumer** anywhere (server/loader never parses it; `pregen._generate_encounter` passes no per-ref creature; `WorldGraphNode.encounter_table_key` is declared but never read; only an unrelated docstring in `game/cookbook/assemble.py` mentions it). So the "18 phantom refs" were never a live crash — they were dormant. The reconciliation is correct and future-proofing, but the file's authored encounters (situation/behavior/weight/difficulty design) currently drive nothing at runtime. Affects `sidequest/genre/` (a real consumer, or an explicit "authoring-only" designation, is a decision for epic-162). *Found by Reviewer during code review.*
- **Conflict** (blocking for finish, reaffirms TEA/Dev): story is scoped `repos: content` but spans server+content (tests on the server branch). SM must set `repos: server,content` before finish so both PRs are opened/merged. Affects `sprint/epic-162.yaml`. *Found by Reviewer during code review.*

### Dev (rework)

- **No new upstream findings during rework.** The epic-level Gap the Reviewer raised — `encounter_tables.yaml` has no runtime consumer — stands as-is (out of scope for this content story; a decision for epic-162). All other Reviewer findings were fixed in this branch (see Dev Assessment (Rework)). *Found by Dev during rework.*

### Reviewer (re-review)

- **Improvement** (non-blocking, should-fix): the `bestiary.yaml` reconciled-fauna comment (`:10-18`) says creatures.yaml is "render-only per ADR-155", but this story's own V4 test proved the native encountergen path reads creatures.yaml as a **live spawn source** (before `effective_bestiary`). Reword to reflect V4 (stats kept synced because creatures.yaml is read live; divergence is live ammunition, not cosmetic). Affects `genre_packs/mutant_wasteland/worlds/flickering_reach/bestiary.yaml`. *Found by Reviewer during re-review.*
- **Gap** (non-blocking, pre-existing): flickering_reach has bestiary combat-role ↔ creatures.yaml ecology-description contradictions that predate epic 162 and are broader than this story's stat reconcile — `tangle_mouth` (bestiary "canopy apex predator, climbs/ambushes" vs creatures.yaml "sessile, IS the terrain"), `dust_drinker` (bestiary "ambush scavenger, grasping mouthparts" vs creatures.yaml "no limbs, deflated bladder"), `echo_frog` (`damage: 1d4` + `attack_bonus: 2` vs prose "harmless", no bite ability). A focused follow-up should reconcile each creature's role/description prose across the two files. Affects `flickering_reach/{bestiary.yaml,creatures.yaml}`. *Found by Reviewer during re-review.*
- **Conflict** (blocking for finish, reaffirmed): story is scoped `repos: content` but spans server+content — SM must set `repos: server,content` (branches in both: content `1315f67`, server `15c0999b`) before finish. Affects `sprint/epic-162.yaml`. *Found by Reviewer during re-review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **RED tests authored in sidequest-server, not the story-scoped content repo**
  - Spec source: `.session/162-5-session.md` Story Details (`**Repos:** content`) + Branch Strategy (`gitflow (feat/162-5-... in content)`)
  - Spec text: "Repos: content"
  - Implementation: RED tests written in `sidequest-server/tests/genre/` and `sidequest-server/tests/cli/` on a new `feat/162-5-flickering-reach-content-reconciliation` branch in the server repo; the content-repo branch carries no RED-phase changes (content authoring is GREEN work).
  - Rationale: sidequest-content has no test runner (no root pytest/justfile; only per-tool venvs), and AC4/V4 require the server genre loader (`effective_bestiary`) and encountergen (`_collect_creatures_from_yaml`). Mirrors sibling story 162-3 (same epic, `repos: server,content`), which put content-referential tests in the server repo gated on content-on-disk.
  - Severity: minor (test location; no behavior change)
  - Forward impact: story repos must widen to `server,content` before finish (branch already exists in both repos); the finish flow reads REPOS. Logged as a blocking-for-finish Delivery Finding for SM.
- **AC2 encoded as "absent-or-equal" rather than strict removal**
  - Spec source: `.session/162-5-session.md` AC2 ("verified as render-only **or removed** per ADR-155")
  - Spec text: "creatures.yaml divergent stat blocks are verified as render-only or removed"
  - Implementation: the AC2 file-level test passes if each shared-id combat field is EITHER absent (render-only) OR equal to the bestiary (reconciled); the separate V4 behavioral test additionally forbids the *consequence* of stripping under V4=YES (a spawned husk at hp-default), so the pair steers Dev to reconcile.
  - Rationale: honors AC2's literal "render-only or removed" wording while the V4=YES finding (native path reads creatures.yaml) makes a bare strip actively harmful; the story's own V4 branch prescribes "reconcile the numbers."
  - Severity: minor
  - Forward impact: none — either acceptable end-state (reconcile; or strip + a future server fix that stops reading creatures.yaml) satisfies the suite once the server early-return is addressed.

### Dev (implementation)
- **Expanded the world bestiary (10→16) rather than pure remap-to-existing**
  - Spec source: `.session/162-5-session.md` story title / AC1 ("18 phantom creature IDs … remapped to valid bestiary creature IDs or confirmed as intentionally removed")
  - Spec text: "remapped to real bestiary ids"
  - Implementation: promoted `static_singer` + `conclave_remnant` from creatures.yaml and authored 4 new AWN-ladder blocks (`scrap_lurker`, `bone_kite`, `wire_rat`, `canyon_leech`) in `worlds/flickering_reach/bestiary.yaml`, then pointed the encounter refs at the expanded roster.
  - Rationale: 6 recurring, fiction-distinct creatures (static_hound×5, scrap_lurker×4, bone_kite×4, wire_rat×3, canyon_leech×2) had no honest match among the original 10; pure remap would either break Genre Truth (wire_rat→signal_chorus) or force removing ~40% of encounters. User selected the Hybrid approach via AskUserQuestion.
  - Severity: moderate (adds authored content beyond a literal "remap", but within "content reconciliation" scope and explicitly user-approved)
  - Forward impact: world bestiary is now 16 entries; `understory_hand` + `protocol_sentinel` are unreferenced by encounter_tables (reachable via other spawn paths — see Delivery Findings).
- **Dropped the `vault_growth` encounter instead of remapping it**
  - Spec source: `.session/162-5-session.md` AC1 ("or confirmed as intentionally removed encounters")
  - Spec text: "confirmed as intentionally removed encounters"
  - Implementation: removed the single Vault Echo `vault_growth` encounter block from encounter_tables.yaml.
  - Rationale: it is a passive crystalline terrain hazard (battery drain, `behavior: passive`), not a combatant — no bestiary creature fits, and authoring a "creature" for terrain would be dishonest. User-approved in the Hybrid option.
  - Severity: minor
  - Forward impact: Vault Echo table drops from 7 to 6 encounters; the hazard flavor is a candidate for a location description (Delivery Finding).

### Reviewer (audit)

- **TEA — RED tests authored in sidequest-server, not the content repo** → ✓ **ACCEPTED**: correct call; content has no test runner and AC4/V4 need the server loader + encountergen. Mirrors 162-3. Repo-scope widening tracked as a blocking-for-finish delivery finding.
- **TEA — AC2 encoded as "absent-or-equal"** → ✓ **ACCEPTED with note**: the reasoning is sound and matches AC2's wording. However the *damage* leg's gating (`c_dice and b_dice`) is asymmetric with the hp/ac legs and forgives a real "bestiary-None vs creatures-asserts-dice" divergence — flagged as a [TEST] MEDIUM finding to tighten (not a reversal of the deviation).
- **Dev — Expanded the world bestiary (10→16) rather than pure remap** → ✓ **ACCEPTED**: user-selected (Hybrid, AskUserQuestion); Genre-Truth-justified (6 recurring creatures had no honest match); rule-checker confirms AWN-ladder adherence and model validity. The `understory_hand`/`protocol_sentinel` orphans are fine (seated via other paths).
- **Dev — Dropped the `vault_growth` encounter** → ✓ **ACCEPTED**: it is terrain (passive crystalline hazard), not a foe; AC1 explicitly permits intentional removal; user-approved. Relocating the flavor to a location description is a reasonable non-blocking follow-up.

*(Note: the REJECT is not a reversal of any logged deviation — the deviations are sound. The block is execution-quality: narration/creature incoherence from the consolidation, and AC4's test not being the wiring test it claims. See the Reviewer Assessment severity table.)*

### Dev (rework)
- No new deviations from spec. The rework addressed Reviewer findings only; the one remap change — `thorn_singer` `peace_speaker`→`tangle_mouth` — is a correction of the earlier consolidation to better match the creature's behavior (sessile lure), per the Reviewer's [MEDIUM] finding, not a new deviation. The bestiary-expansion and vault_growth-removal deviations (above) are unchanged and remain ACCEPTED.

### Reviewer (re-review audit)
- **Dev (rework) — `thorn_singer` remap peace_speaker→tangle_mouth** → ✓ **ACCEPTED**: correct call — the sessile "pruning/tree/bone-pile lure" fits tangle_mouth's creatures.yaml ecology. (It does surface tangle_mouth's pre-existing bestiary↔ecology mobile-vs-sessile split, filed as a non-blocking Gap in Delivery Findings — not a reason to reverse the remap; the alternatives fit worse.)
- All prior deviations (TEA repo-placement, TEA AC2-shape, Dev bestiary-expansion, Dev vault_growth-removal) remain **ACCEPTED** — unchanged by the rework. No new spec deviations introduced.