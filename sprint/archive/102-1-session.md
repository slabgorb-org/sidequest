---
story_id: "102-1"
jira_key: ""
epic: "102"
workflow: "tdd"
---
# Story 102-1: PC-death runs the WN downed seam — fire {ruleset}.mortal_injury/.shock on the reprisal/lethality path so a dying PC emits WN lethality spans (today only player-drops-opponent runs run_cwn_wwn_downed_seam; opponent-drops-player at _resolve_opponent_reprisal -> post_resolution_lethality applies a generic verdict=dead with no wwn.*). AC5b combat-half blocker. Server only; OTEL span assertion + reprisal-lethal fixture.

## Story Details
- **ID:** 102-1
- **Jira Key:** (none)
- **Workflow:** tdd
- **Repos:** server
- **Branch:** feat/102-1-pc-death-wn-downed-seam
- **Stack Parent:** none

## Sm Assessment

Setup complete and verified. Story 102-1 (5 pts, p1, tdd) targets the server repo only:
PC-death must run the WN downed seam so a dying PC emits `{ruleset}.mortal_injury`/`.shock`
spans on the reprisal/lethality path. Today only the player-drops-opponent direction runs
`run_cwn_wwn_downed_seam`; the opponent-drops-player direction
(`_resolve_opponent_reprisal` → `post_resolution_lethality`) applies a generic
`verdict=dead` with no `wwn.*` spans. This is the AC5b combat-half blocker for epic 102.

- Session file created, branch `feat/102-1-pc-death-wn-downed-seam` cut (orchestrator;
  server work branches per repos.yaml with base `develop`).
- Story context written at `sprint/context/context-story-102-1.md` with technical
  approach and ACs.
- Jira: not configured for this project — claim explicitly skipped.
- Sprint YAML: 102-1 marked in_progress via pf CLI.
- Workflow is phased tdd → handoff to TEA (O'Brien) for RED: failing OTEL span
  assertion + reprisal-lethal fixture per the story's test requirements.

No blockers. No upstream findings at setup time.

## TEA Assessment

**Tests Required:** Yes
**Reason:** n/a (5-pt p1 bug; story title mandates "OTEL span assertion + reprisal-lethal fixture")

**Test Files:**
- `sidequest-server/tests/server/test_reprisal_wn_downed_seam.py` — synthetic-pack dispatch suite
  (MagicMock pack + real RulesConfig + real LethalityPolicy, no content dependency); drives
  `dispatch_dice_throw` so the player's strike triggers the forced-hit/forced-miss opponent
  reprisal that drops (or chips) the PC
- `sidequest-server/tests/integration/test_reprisal_wn_lethality_e2e.py` — real heavy_metal pack
  (ruleset: wwn, lethality pc=dead) seated via `instantiate_encounter_from_trigger`; the AC5b
  combat-half proof shaped like the 2026-06-10 long_foundry playtest kill

**Tests Written:** 8 tests covering 6 ACs (TEA-defined; story YAML carried none — see Design Deviations)

| AC | Behavior pinned | Test(s) |
|----|-----------------|---------|
| AC1 | Reprisal kill in a wwn pack (lethal verdict) → exactly one `wwn.mortal_injury.declared`, actor=PC (exactly-one also guards double-fire across the reprisal close + post_resolution_lethality call sites) | `test_wwn_reprisal_kill_declares_mortal_injury_for_pc`, e2e heavy_metal test |
| AC2 | WN seam is ADDITIVE: Mortal Injury death-clock status AND generic Downed status AND `encounter.post_resolution_lethality` decision=lethal_down | `test_wwn_reprisal_kill_attaches_death_clock_alongside_generic_downed` |
| AC3 | Traumatic Hit scene + failed Physical save → `wwn.major_injury.roll` actor=PC, save_made=False, Major Injury Scar | `test_wwn_reprisal_traumatic_scene_failed_save_rolls_major_injury` |
| AC4 | Reprisal MISS with Shock-rated `opponent_damage` → `wwn.shock.applied`, exact 3-HP chip, `state_patch.hp`, no mortal injury, encounter unresolved | `test_wwn_reprisal_miss_applies_shock_chip_to_pc` |
| AC5 | Capability gate: swn pack (no trauma config) → zero `*.mortal_injury.declared`, no crash, generic verdict still applies | `test_swn_reprisal_kill_emits_no_wn_lethality_span` (passing negative control) |
| AC6 | Non-lethal verdict (`defeated`) → PC recovers to 1-HP floor, NO death clock/status; AWN rides free via AwnConfig⊂CwnConfig | `test_wwn_non_lethal_verdict_recovers_pc_without_death_clock` (passing negative control), `test_awn_reprisal_kill_declares_mortal_injury_for_pc` |

**Status:** RED (verified by testing-runner, run 102-1-tea-red, serial `-n0` per the OTEL
span-test deadlock constraint): **6 FAILED on the intended final span/status assertions,
2 PASSED (negative controls that guard regressions once the seam lands), 0 fixture/collection
ERRORS.** Committed on `sidequest-server` branch `feat/102-1-pc-death-wn-downed-seam`
(base develop) at `8006fac6`.

**Determinism strategy:** the reprisal d20, downed-seam save, and damage faces all roll via the
shared `random` module (dice.py / downed_seam.py / damage_roll.py), so ONE monkeypatched
`randint` governs the whole path; arg-dispatching fakes force hit-then-failed-save and
hit-with-min-damage sequences without touching any roll seam. The player's own check uses the
thrown `face=[…]`, never rng.

### Rule Coverage

| Rule | How covered | Status |
|------|-------------|--------|
| CLAUDE.md "No Source-Text Wiring Tests" | All wiring assertions are OTEL-span + fixture-driven behavior (patterns 1+2 from the rule); zero `read_text()` greps | complied |
| CLAUDE.md "Every Test Suite Needs a Wiring Test" | Both files drive the production `dispatch_dice_throw`; e2e additionally seats via the production `instantiate_encounter_from_trigger` on the real pack | complied |
| OTEL Observability Principle | The entire suite IS the lie-detector: span name + actor + save_made + decision/verdict attrs asserted | complied |
| No Silent Fallbacks | AC5 pins the capability gate stays silent-but-correct for swn WITHOUT crashing, while the generic verdict still applies (absence is visible via post_resolution_lethality) | failing (by design) |
| lang-review python #6 test quality | Self-check done: every test asserts specific span counts, attrs, HP values, or status texts; no `assert True`, no `let-it-pass` patterns; negative controls assert concrete state (hp==1, span lists empty) | complied |
| lang-review python #2 mutable defaults / #3 annotations | Test helpers use immutable defaults and annotate the stateful fake; module-level fixtures are constants | complied |

**Rules checked:** 6 of 6 applicable rules have coverage. **Self-check:** 0 vacuous tests found.

**Handoff:** To Julia (Dev) for GREEN. The epic context names the seam: the reprisal close
(`dice.py:1383` already has `ruleset`, `cdef`, `pack`, `snapshot`, `encounter` in scope) and/or
`post_resolution_lethality` — wire `run_cwn_wwn_downed_seam` (or its equivalent) for the downed
PC; build nothing that exists. Note the e2e test loads sidequest-content from disk and skips
cleanly when absent.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/sidequest/server/dispatch/dice.py` — the reprisal close (hp_depletion →
  resolution surfacing → `apply_post_resolution_lethality` → CHARACTER_INCAPACITATED) is
  extracted verbatim into a new shared helper `_close_reprisal_depletion`, which now also runs
  `run_cwn_wwn_downed_seam(actor_side="opponent")` AFTER the genre verdict — a LETHAL down
  emits `{ruleset}.mortal_injury.declared` (+ `major_injury.roll` on a traumatic-scene failed
  save) for the dying PC; a non-lethal recovery (1-HP floor) gates the seam off via its own
  hp>0 check; the config-capability gate keeps native/swn silent. The reprisal MISS branch now
  applies the WN Shock chip (`cdef.opponent_damage` or beat-resolved spec → `ruleset.resolve_shock`
  vs the PC's AC → `apply_beat_hp_channel` + INFO log + MECHANICAL TRUTH directive) and runs the
  SAME close helper (a chip can kill), instead of returning untouched.
- `sidequest-server/sidequest/server/post_resolution_lethality.py` — module docstring
  reconciled (the documented reprisal asymmetry is now closed; past tense + pointer to 102-1).
- `sidequest-server/sidequest/server/dispatch/downed_seam.py` — docstring now names all three
  callers (strike path, WWN cast path, reprisal close).

**Tests:** 8/8 story tests passing; 58/58 across the story + seam-adjacent suites
(reprisal e2e, awn combat dispatch, wwn heavy_metal combat, post_resolution_lethality
unit+wiring, toothless detector, disengage resolution), run serially per the OTEL xdist
constraint. Full server suite: 11359 passed / 7 failed — all 7 verified pre-existing and
unrelated (4 corpus audits, 90-4 scene_harness constraint, missing api-contract doc path,
swn_test_pack bestiary fixture); zero 102-1 regressions.
**Branch:** `feat/102-1-pc-death-wn-downed-seam` (sidequest-server, base develop) — pushed.
Commits: `8006fac6` (tests, TEA) + `3e9575e3` (implementation).

**Branch-repair note (for Reviewer transparency):** the server checkout's branch silently
flipped back to `feat/102-8-doc-drift-cleanup` mid-phase (dual-clone/hook hazard), so the
implementation commit initially landed there as `f935cb2f`. Repaired without improvisation:
cherry-picked onto `feat/102-1-pc-death-wn-downed-seam` (`3e9575e3`), reset local 102-8 back
to its prior head `466f7005` (the misplaced commit had never been pushed to its remote), and
re-verified GREEN on the repaired branch with the branch name asserted inside the test run.

**Handoff:** To verify phase (O'Brien/TEA — simplify + quality-pass).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (tests 8/8 GREEN serial, ruff clean on all 5 changed files, tree clean, correct branch, 0 debug code; 155 repo-wide format drifts pre-existing on develop) | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 7 | confirmed 2 (deferred), dismissed 5 |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — domain covered by my own pass (see observations O4, O7) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — covered (observation O8: shock-kill and multi-PC scenarios untested; matched to deferred findings) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — covered (observation O9: helper docstring overstatement, Low) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — covered (player_core param unannotated in a private helper; module-style consistent; no stringly-typed APIs introduced) |
| 7 | reviewer-security | Yes | findings | 3 | confirmed 0, dismissed 2 (factual evidence), deferred 1 (pre-existing prompt-injection pattern → Delivery Finding) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — covered (helper extraction REDUCES duplication; no dead code added) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — covered exhaustively in Rule Compliance below |

**All received:** Yes (3 enabled returned; 6 disabled via settings, domains self-covered)
**Total findings:** 2 confirmed (both deferred Medium with follow-up Delivery Finding), 7 dismissed (with rationale), 1 deferred (pre-existing pattern → Delivery Finding)

### Finding adjudication

**Confirmed (deferred, Medium, non-blocking):**
- `[EDGE]` **Multi-PC partial-down: WN death-clock targets the FIRST non-withdrawn player-side actor.** `run_cwn_wwn_downed_seam` resolves the downed defender via `_opposite_side_first_actor` (beat_kinds.py:406-428 — filters `withdrawn` only, NOT hp). In MP WN combat: PC1 drops (partial-down, fight continues per ADR-139 liveness) → seam declares PC1's Mortal Injury (WN-correct — dying mid-fight); when PC2 later drops and the encounter resolves, the close's seam call targets candidates[0]=PC1 again → duplicate Mortal Injury status/span on PC1, none for PC2. Mirrors the strike path's pre-existing single-defender idiom; unreachable in single-PC play (first down resolves immediately; exactly-one pinned by AC1). Follow-up filed in Delivery Findings.
- `[EDGE]` **Multi-PC partial-down: no generic lethality adjudication until resolution.** A PC downed while a party-mate stands gets no Downed/Recovering status (`apply_post_resolution_lethality` gates on `enc.resolved` — pre-existing, untouched by this diff; the NEW seam actually improves the WN case by declaring the death clock immediately). Same follow-up.

**Dismissed (with evidence):**
- `[EDGE]` resolve_damage actor_core possibly None (shock branch, dice.py:1209) — identical unguarded pattern on the pre-existing hit path (dice.py:1278); the NPC is seated by the production seam before any reprisal; exposure unchanged.
- `[EDGE]` `int(player_core.armor_class)` coercion — identical expression pre-exists at dice.py:1129 (`target_ac`); pydantic coerces at the model boundary.
- `[EDGE]` `physical_save_target_for` raise propagating from the close — fail-loud is the REQUIRED behavior (CLAUDE.md No Silent Fallbacks: "never silently try an alternative... default"); the suggested catch-log-continue would violate it. Reachability: the reprisal pre-gates on `opponent_stats` (dice.py:1113-1120) and the PC branch reads chargen-complete `Character.stats`.
- `[EDGE]` "taken out of the fight" vs "taken to the brink" directive tension on non-lethal verdicts — both directives pre-exist (moved verbatim into the helper); the resolution directive is accurate (the FIGHT ended); not introduced by this diff.
- `[EDGE]` shock directive appended before the close (rollback on raise) — same ordering as the pre-existing hit path (hit directive at dice.py:1345 precedes its close); uniform fail-loud semantics.
- `[SEC]` "Shock chip invisible to the GM panel / OTEL rule violation" — **factually incorrect premise**: `resolve_shock` emits `wwn.shock.applied` (asserted by AC4's test) and `SPAN_ROUTES[SPAN_WWN_SHOCK_APPLIED]` (spans/wwn.py:77-88) routes it into a `state_transition` watcher event consumed at watcher.py:100-102, alongside `state_patch.hp` from `apply_beat_hp_channel` and the always-on `encounter.opponent_attack_resolved(hit=False)`. The strike path's shock block (dice.py:694-738) likewise has NO explicit `_watcher_publish` — exact parity. The hit path's `opponent_damage_roll_resolved` event documents a damage ROLL (faces/total); a Shock chip rolls nothing. Not a rule violation; residual nicety (persisted ENCOUNTER_OPPONENT_ATTACK row for chips) noted as Low in Delivery Findings.
- `[SEC]` static `session_id` in the e2e test — test-only; identical convention in pre-existing fixtures (`"hm-wwn-session"`, `"reprisal-session"`); the seed seeds dice ANIMATION, not resolution.

**Deferred (pre-existing pattern, out of 102-1 scope):**
- `[SEC]` Unsanitized character/NPC names interpolated into `next_turn_directives` (prompt-injection surface, CWE-74) — the new shock directive (dice.py:1246) is one more site of the established pattern (hit path dice.py:1345, post_resolution_lethality directives, et al.); ADR-047 sanitization exists for action text but names bypass it at chargen. Filed as a Delivery Finding for a dedicated sweep.

### Rule Compliance

| Rule | Instances checked | Verdict |
|------|-------------------|---------|
| No Silent Fallbacks | shock-spec resolution (chip==0 is a normal rules outcome, not a config absence; the seating-time toothless detector + hit-path `damage_spec_missing` WARNING cover the authoring-gap case loudly); capability gates return-early with routed-span visibility upstream; `physical_save_target_for` raises on absence | compliant |
| OTEL Observability Principle | every new decision emits: shock → `wwn.shock.applied` (routed) + `state_patch.hp`; PC death → `{ruleset}.mortal_injury.declared` / `{ruleset}.major_injury.roll` (routed) + existing `post_resolution_lethality` span; reprisal attempt span unchanged | compliant |
| Don't Reinvent — Wire Up What Exists | the fix IS wiring: `run_cwn_wwn_downed_seam`, `resolve_shock`, `apply_beat_hp_channel`, `apply_post_resolution_lethality` all pre-existing; zero new mechanics implemented | compliant |
| Verify Wiring / Wiring Test | dispatch-level tests drive production `dispatch_dice_throw`; e2e seats the real heavy_metal pack via `instantiate_encounter_from_trigger` | compliant |
| No Source-Text Wiring Tests | all assertions are OTEL-span/state/fixture-driven; zero source greps | compliant |
| No Stubbing / no half-wired | shock branch falls through to the full depletion close (a chip-kill gets the same death surface); both reprisal channels share `_close_reprisal_depletion` | compliant |
| lang-review python #1 (silent exceptions) | zero new try/except in the diff | compliant |
| lang-review python #2 (mutable defaults) | no new defaults; helper is keyword-only | compliant |
| lang-review python #3 (annotations) | helper params annotated except `player_core` (private helper — exempt per rule text) | compliant |
| lang-review python #4 (logging) | INFO on shock chip (lazy %s formatting), INFO on resolution close; WARNING paths untouched | compliant |
| lang-review python #6 (test quality) | every test asserts concrete spans/attrs/HP/status; negative controls assert concrete state | compliant |

### Observations (≥5)

- O1 `[VERIFIED]` Ordering contract: genre verdict before WN seam — dice.py:1505 (`apply_post_resolution_lethality`) precedes dice.py:1516 (`run_cwn_wwn_downed_seam`); the seam's hp>0 gate (downed_seam.py:145) makes a non-lethal 1-HP recovery suppress the death clock. Pinned by `test_wwn_non_lethal_verdict_recovers_pc_without_death_clock`. Complies with SOUL.md Genre Truth.
- O2 `[VERIFIED]` Exactly-one mortal injury on the single-PC kill turn — one seam call site on the player side (the close); the strike-path call (dice.py:760) targets the OPPOSITE side (`actor_side=actor.side`). Pinned by AC1's `len(spans)==1`.
- O3 `[VERIFIED]` Capability gating — `isinstance(cfg, (CwnConfig, WwnConfig))` at downed_seam.py:137-139 keeps swn/native silent (AC5 negative control); `resolve_shock` base returns 0 (base.py:178-180) so non-WN misses chip nothing.
- O4 `[VERIFIED]` No swallowed errors introduced — zero new try/except; `DiceDispatchError` propagation from the close matches the strike path's fail-loud contract.
- O5 `[VERIFIED]` Data flow traced (see below) — no payload field reaches the new code unvalidated beyond pre-existing exposure.
- O6 `[EDGE]` (deferred Medium) multi-PC partial-down duplicate/missed death-clock targeting — see adjudication above.
- O7 `[EDGE]` (deferred Medium) multi-PC partial-down generic-lethality gap — pre-existing, see adjudication.
- O8 `[TEST]` (Low) untested-but-wired: shock-chip-kills-PC path (the close handles it; no fixture drives it) and multi-PC scenarios — natural fixtures for the follow-up story.
- O9 `[DOC]` (Low) `_close_reprisal_depletion` docstring says "a recovering PC never gets a Mortal Injury death clock" — precise only at resolution; in an MP partial-down there is no verdict yet and the seam (correctly, per WN rules) declares the clock mid-fight. Tighten wording in the follow-up.
- O10 `[VERIFIED]` Pattern: helper extraction (`_close_reprisal_depletion`) is the same anti-drift consolidation the project used for `run_cwn_wwn_downed_seam` itself (downed_seam.py module docstring) — good pattern, correctly applied.

**Data flow traced:** `DiceThrowPayload.face/beat_id` (untrusted client) → `dispatch_dice_throw` validation → player beat → `_resolve_opponent_reprisal` (server-rolled d20, server stats) → miss branch: content-authored `cdef.opponent_damage` (load-validated DamageSpec) → `resolve_shock` integer chip → `apply_beat_hp_channel` (mitigation 0, channel "strike") → `check_hp_depletion` (reads HP only) → verdict from load-mandatory `lethality_policy` → seam reads `Character.stats` (chargen-authored). No client-controlled value influences the chip amount, the verdict, or the save target; client `face` only affects the PLAYER's own beat. Safe.

**Wiring:** UI-facing surfaces unchanged (CHARACTER_INCAPACITATED built by the same `build_incapacitated_message`); GM panel receives the new spans through the established `SPAN_ROUTES` → watcher.py bridge — no UI change needed for this server-only story.

**Error handling:** failure modes (missing config → gated no-op with upstream visibility; missing stats → loud `DiceDispatchError`; missing policy → existing `no_policy` warning span) all preserve the project's fail-loud doctrine.

### Devil's Advocate

Assume this is broken. The most dangerous claim is "the seam runs AFTER the verdict, so non-lethal genres are safe." But the verdict only exists when the encounter RESOLVES — in multiplayer, a PC can be chipped or shot to 0 while a party-mate stands, the encounter stays live (ADR-139), and the seam fires with no verdict at all: a `defeated`-verdict pack (elemental_harmony is wwn-bound!) would stamp "dies in 6 rounds unless stabilized" on a PC its genre promises never to kill, and when the fight later resolves, that PC is recovered to 1 HP still wearing a death-clock Scar nobody clears. A confused table reads two contradictory truths. Second: the first-actor targeting means in that same MP fight the WRONG PC can be adjudicated — the already-dying PC1 gets a second clock while PC2's death goes unmarked; the GM panel then shows one mortal_injury span and a career GM "verifying" AC5b could be looking at the wrong actor's death. Third: a malicious player names their PC with an injection payload and every directive this diff writes carries it into the narrator prompt — the new shock directive widens that surface. Fourth: the shock branch resolves `resolve_damage` on EVERY miss now; a content pack whose resolve_damage raises on a weird beat would turn every whiffed enemy swing into a hard ERROR. Each of these is real; my judgment is that the first two are the genuine Mediums I deferred (MP+WN+partial-down is not the playgroup's current configuration and the single-PC AC5b path is airtight), the third is a pre-existing pattern filed for a sweep, and the fourth would equally break the pre-existing hit path (same expression) so this diff adds no new failure class. Nothing here rises to blocking — but the follow-up story is not optional polish; elemental_harmony MP play WILL hit the no-verdict death-clock case eventually.

## Reviewer Assessment

**Verdict:** APPROVED

**Specialist findings incorporated:**
- [EDGE] (Medium, deferred w/ follow-up finding): multi-PC partial-down — `run_cwn_wwn_downed_seam` first-actor targeting can duplicate PC1's Mortal Injury and miss PC2's at `downed_seam.py:141`; generic lethality stays resolution-gated at `post_resolution_lethality.py:198`. Unreachable single-PC (AC1 pins exactly-one). 5 other [EDGE] findings dismissed with line-level evidence (see adjudication).
- [SEC] (deferred, pre-existing pattern): unsanitized character/NPC names in narrator directives (new shock site dice.py:1246 mirrors pre-existing dice.py:1345) — filed as Delivery Finding for an ADR-047 chargen-name sweep. The "shock invisible to GM panel" [SEC] claim was dismissed on factual evidence: `wwn.shock.applied` is SPAN_ROUTES-routed at watcher.py:100-102, exact parity with the strike path's shock block.

**Data flow traced:** DiceThrowPayload → dispatch → reprisal → shock/damage → depletion → verdict → WN seam (safe — no client-controlled value reaches chip amount, verdict, or save target; see Observations)
**Pattern observed:** anti-drift helper consolidation `_close_reprisal_depletion` at dice.py:1404, mirroring the project's own `downed_seam` consolidation precedent
**Error handling:** fail-loud preserved end-to-end (DiceDispatchError propagation; gated no-ops are span-visible upstream; no new try/except)
**Conditions:** none blocking. Two deferred Mediums (multi-PC partial-down death-clock targeting + generic-lethality gap) filed as a follow-up Delivery Finding — recommend a sibling story in epic 102 or 90-series.
**Handoff:** To SM (Winston Smith) for finish-story (PR creation + merge per finish flow).

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-10T16:40:09Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-10T00:00:00Z | 2026-06-10T16:05:00Z | 16h 5m |
| red | 2026-06-10T16:05:00Z | 2026-06-10T16:19:51Z | 14m 51s |
| green | 2026-06-10T16:19:51Z | 2026-06-10T16:32:36Z | 12m 45s |
| review | 2026-06-10T16:32:36Z | 2026-06-10T16:40:09Z | 7m 33s |
| finish | 2026-06-10T16:40:09Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Question** (non-blocking): the reprisal Shock path (AC3) only fires live if a pack's
  `cdef.opponent_damage` authors `shock`/`shock_ac` ratings. heavy_metal's Blade-work
  `opponent_damage` may not carry a Shock rating today, so the new code path could be
  live-but-dormant on the AC5b pack.
  Affects `sidequest-content/genre_packs/heavy_metal/rules.yaml` (consider authoring a
  Shock rating on the opponent weapon if WWN melee fidelity is wanted live).
  *Found by TEA during test design.*
- **Improvement** (non-blocking): once the seam lands, the module docstring of
  `sidequest/server/post_resolution_lethality.py` (which currently documents the
  reprisal asymmetry as a known gap) must be updated or it becomes doc-drift —
  feeds 102-8's reconciliation.
  Affects `sidequest-server/sidequest/server/post_resolution_lethality.py` (docstring).
  *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): the server checkout's git branch flipped from the story branch back
  to `feat/102-8-doc-drift-cleanup` mid-phase with no agent-issued checkout — likely the
  dual-clone/branch-hook hazard already on record; cost a cherry-pick + branch reset to repair.
  Affects `.pennyfarthing` branch hooks / dual-clone workflow (subrepo branch should be pinned
  or re-asserted around subagent runs).
  *Found by Dev during implementation.*
- **Improvement** (non-blocking): the full-suite baseline carries 7 pre-existing failures on
  develop (4 heavy_metal/Sestayty corpus-audit underpopulation, the 90-4 scene_harness
  `actors=` constraint, a missing `docs/api-contract.md` path expectation, swn_test_pack
  missing bestiary.yaml) — worth a sweep story so real regressions stand out.
  Affects `sidequest-server/tests` (baseline hygiene).
  *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (non-blocking): multi-PC partial-down WN lethality — `run_cwn_wwn_downed_seam` targets `_opposite_side_first_actor` (withdrawn-filtered, not hp-filtered), so in MP a second player-side kill duplicates the first downed PC's Mortal Injury and misses the second PC's; and a PC downed mid-fight in a non-lethal-verdict wwn pack (elemental_harmony) gets a death-clock Scar that no later recovery clears. Recommend a sibling story: per-PC death-clock targeting + partial-down lethality sweep + MP fixtures (the shock-kill path is also wired-but-untested).
  Affects `sidequest-server/sidequest/server/dispatch/downed_seam.py` (defender selection) and `sidequest-server/sidequest/server/post_resolution_lethality.py` (resolution-gated adjudication).
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking): character/NPC names are interpolated unsanitized into `next_turn_directives` narrator strings across the dispatch (pre-existing pattern; the new shock directive adds one more site) — a chargen-time `sanitize_player_text()` pass on names would close the CWE-74 surface at the source.
  Affects `sidequest-server/sidequest/game` (character builder name intake) per ADR-047.
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking, Low): a persisted ENCOUNTER_OPPONENT_ATTACK row for reprisal Shock chips (op-style `_watcher_publish` mirroring `opponent_damage_roll_resolved`) would give the ADR-124 forensic census the chip's authoring event; the live GM panel already sees `wwn.shock.applied` via SPAN_ROUTES.
  Affects `sidequest-server/sidequest/server/dispatch/dice.py` (shock branch).
  *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **TEA defined the acceptance criteria (story YAML carried none)**
  - Spec source: context-story-102-1.md ("No acceptance criteria recorded — TEA to define during the RED phase") + story title + context-epic-102.md (gap 1, seam map, invariants)
  - Spec text: "fire {ruleset}.mortal_injury/.shock on the reprisal/lethality path so a dying PC emits WN lethality spans … OTEL span assertion + reprisal-lethal fixture"
  - Implementation: Six behavioral ACs pinned at the dispatch level (see TEA Assessment) — lethal-kill mortal-injury span, additive death-clock + Downed statuses, traumatic-save major-injury, reprisal-miss Shock chip, SWN capability gate, AWN free-ride — plus a real heavy_metal e2e proof
  - Rationale: dispatch-level OTEL/behavior assertions pin the contract without pinning Dev's internal seam choice (post_resolution_lethality vs reprisal close), per the epic's "behavior, not interface" reuse-first invariant
  - Severity: minor
  - Forward impact: Dev/Reviewer should treat the test docstring contract as the AC list
- **Non-lethal genre verdict suppresses the WN death clock (ordering pinned)**
  - Spec source: context-epic-102.md (102-1 "extends post_resolution_lethality to also run the WN module's lethality surface"); SOUL.md Genre Truth
  - Spec text: spec is silent on the non-lethal interaction; the title only covers "a dying PC"
  - Implementation: `test_wwn_non_lethal_verdict_recovers_pc_without_death_clock` pins that a `defeated`-verdict pack (e.g. elemental_harmony, also wwn-bound) recovers the PC to the 1-HP floor with NO `wwn.mortal_injury.declared` and no Mortal Injury status — i.e. the genre verdict applies before/over the WN seam
  - Rationale: a "dies in N rounds" death clock on a PC the genre policy just recovered to 1 HP contradicts both the verdict and the recovered HP; the existing seam's hp>0 gate makes verdict-first the natural ordering
  - Severity: minor
  - Forward impact: if Architect wants WN mortal injury even on non-lethal verdicts, this test (and the ordering) must be consciously reversed
- **"{ruleset}.shock" interpreted as the opponent's Shock chip on a reprisal MISS**
  - Spec source: story title; context-epic-102.md gap 1
  - Spec text: "fire {ruleset}.mortal_injury/.shock on the reprisal/lethality path"
  - Implementation: `test_wwn_reprisal_miss_applies_shock_chip_to_pc` requires a missed reprisal with a Shock-rated `opponent_damage` to chip the PC (wwn.shock.applied + state_patch.hp + exact 3-HP chip)
  - Rationale: Shock is the signature WN melee rule (a miss still chips) and the only `.shock` surface that exists; the strike path already applies it player→opponent, so symmetry demands opponent→PC
  - Severity: minor
  - Forward impact: if Dev/Reviewer judge reprisal-Shock out of 102-1 scope, drop/defer that one test explicitly rather than silently skipping it
- **AWN test accepts either cwn.* or awn.* mortal-injury slug**
  - Spec source: context-epic-102.md invariant "The slug is honest" vs test_awn_combat_dispatch.py precedent (asserts cwn.* for awn)
  - Spec text: "Spans, saves, and GM panel show the binding module's slug (awn, not cwn)"
  - Implementation: `test_awn_reprisal_kill_declares_mortal_injury_for_pc` asserts a `*.mortal_injury.declared` span for the PC under EITHER slug
  - Rationale: honest-slug rework is 102-7/later scope; pinning cwn.* would break on that story, pinning awn.* would fail this one for the wrong reason
  - Severity: minor
  - Forward impact: 102-7 should tighten this assertion to awn.* when slugs become honest

### Dev (implementation)
- **WN seam wired at the reprisal close, not inside post_resolution_lethality**
  - Spec source: context-epic-102.md, Key files table ("post_resolution_lethality.py — 102-1 extends this to also run the WN module's lethality surface")
  - Spec text: "102-1 extends this [post_resolution_lethality] to also run the WN module's lethality surface"
  - Implementation: `run_cwn_wwn_downed_seam` is called from the new `_close_reprisal_depletion` helper in `dispatch/dice.py`, immediately AFTER `apply_post_resolution_lethality` — not from inside `post_resolution_lethality.py`
  - Rationale: the downed seam needs `ruleset` and `cdef`, both already in scope at the reprisal close but absent from `apply_post_resolution_lethality`'s signature; widening that single-purpose policy module's interface for a caller-side concern would couple it to dispatch types. TEA's tests explicitly pinned behavior at the dispatch level and allowed either seam ("Dev may wire the seam from post_resolution_lethality or from the reprisal close")
  - Severity: minor
  - Forward impact: none — the ordering contract (genre verdict first, WN seam second) is enforced and tested at the dispatch level
- **Reprisal Shock falls through to the full depletion close**
  - Spec source: TEA test `test_wwn_reprisal_miss_applies_shock_chip_to_pc` (only asserts chip + spans + unresolved encounter)
  - Spec text: test requires the chip, the spans, and `enc.resolved is False` for a 12-HP PC
  - Implementation: after a Shock chip the code runs the same `_close_reprisal_depletion` as the hit path (depletion check, verdict, WN seam, death surface) rather than returning immediately
  - Rationale: a Shock chip can drop a low-HP PC to 0; returning early would recreate the exact EH-2 "parked at 0/10" bug class on a new channel ("no half-wired features"). The close is no-op-safe above 0 HP, so the tested 12→9 case is unaffected
  - Severity: minor
  - Forward impact: a future shock-kill is already handled and observable (same span/status/banner stack as a damage kill)

### Reviewer (audit)
- **TEA: "TEA defined the acceptance criteria"** → ✓ ACCEPTED by Reviewer: story YAML carried none; the six ACs faithfully decompose the title + epic gap 1, and the dispatch-level pinning is the right altitude.
- **TEA: "Non-lethal genre verdict suppresses the WN death clock (ordering pinned)"** → ✓ ACCEPTED by Reviewer: correct at resolution (Genre Truth outranks the module table). Note the MP partial-down case has no verdict yet and the seam correctly fires mid-fight — captured as a deferred Medium + follow-up finding, not a flaw in this deviation.
- **TEA: "{ruleset}.shock interpreted as the opponent's Shock chip on a reprisal MISS"** → ✓ ACCEPTED by Reviewer: the story title names `.shock`; this is the only `.shock` surface that exists, and the strike path's symmetry demands it.
- **TEA: "AWN test accepts either cwn.* or awn.* mortal-injury slug"** → ✓ ACCEPTED by Reviewer: pragmatic bridge until the honest-slug rework; consistent with test_awn_combat_dispatch.py precedent.
- **Dev: "WN seam wired at the reprisal close, not inside post_resolution_lethality"** → ✓ ACCEPTED by Reviewer: keeps the policy module free of dispatch types; TEA's contract explicitly allowed either seam; ordering enforced at the call site and tested.
- **Dev: "Reprisal Shock falls through to the full depletion close"** → ✓ ACCEPTED by Reviewer: returning early would recreate the EH-2 parked-at-0 bug class on a new channel; the close is no-op-safe above 0 HP.