---
story_id: "126-30"
jira_key: ""
epic: "126"
workflow: "tdd"
---
# Story 126-30: [ENGINE] De-nativize Fate confrontation SEATING

## Story Details
- **ID:** 126-30
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 5
- **Type:** refactor
- **Priority:** p2

## Overview

De-nativize Fate confrontation SEATING. Under `ruleset=='fate'`, seat a standoff/conflict directly as a Fate contest (4dF + ladder, the four actions, ablative stress) — do NOT seat or feed native beats / a tension dial for a Fate confrontation.

**Keith ruling:** 2026-06-19

**Why this matters:** The 2026-06-19 full-stack playtest (150-1/150-2) confirmed the Fate conflict spine fires end-to-end, but revealed that seating still feeds *both* Fate mechanics *and* native beat defs. The win signal is the opponent's stress + consequence fill toward taken-out (ADR-143/144), NOT the vestigial `opponent_metric.tension` dial. This is the upstream seating half of the Bind-the-Ruleset cleanup that #964 only partially did (it gated the native overlay from co-rendering with FATE_STATE but did NOT de-nativize seating — `beat_selections=2` still seats native beat_defs for a Fate confrontation).

## Technical Context

**Parent epic context:** `sprint/context/context-epic-126.md` contains the full Technical Architecture table with key files:
- `server/dispatch/encounter_lifecycle.py` — seating orchestrator
- `server/dispatch/confrontation.py` — `should_emit_native_confrontation` gate
- `game/ruleset/fate.py` — `compute_dc` guard (ADR-144 safety net)

**Doctrine:**
- **ADR-143:** Bind the Ruleset, Don't Balance It — the bound ruleset engine must REPLACE the native one for what it covers, not layer on top.
- **ADR-144:** Fate Core binding replaces the native ruleset — `compute_dc` NotImplementedError is the safety net; the 4dF + ladder conflict engine is the resolution surface.

## Acceptance Criteria

1. Under `ruleset=='fate'`, seat a standoff/conflict as a pure Fate contest (Fate mechanics only). Do NOT seat native beat_defs, native tension dials, or any beat-based mechanics alongside Fate.
2. The win signal is the opponent's stress + consequence fill toward taken-out (per ADR-144), NOT the vestigial `opponent_metric.tension` dial.
3. Preserve invariants — do NOT relax:
   - `compute_dc` NotImplementedError (ADR-144 safety net) — Fate confrontations do NOT use native DC-based resolution.
   - `decide_opponent_action` sheet-required guard (#966) — NPC opponents must have a Fate sheet bound before seating.
4. Add a server test asserting a Fate confrontation seats without native beat_defs and uses only Fate mechanics (OTEL span proof: FATE_ROLL + fate.* + confrontation.* spans present; no native beat spans).
5. Verify the seating fix integrates end-to-end: seat a real Fate conflict in a Fate pack (e.g. grab/attack an NPC in pulp_noir/annees_folles) and confirm GM panel shows Fate mechanics only (no native tension dial).

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Repos:** server
**Branch:** feat/126-30-denativize-fate-seating
**Phase Started:** 2026-06-20T05:39:54Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-20T04:16:55+00:00 | 2026-06-20T04:21:51Z | 4m 56s |
| red | 2026-06-20T04:21:51Z | 2026-06-20T04:50:59Z | 29m 8s |
| green | 2026-06-20T04:50:59Z | 2026-06-20T05:24:59Z | 34m |
| review | 2026-06-20T05:24:59Z | 2026-06-20T05:39:54Z | 14m 55s |
| finish | 2026-06-20T05:39:54Z | - | - |

## SM Assessment

**Story set up:** 126-30 — [ENGINE] De-nativize Fate confrontation SEATING (5pts, p2, refactor, tdd).

**Repo:** server only (sidequest-server). Branch `feat/126-30-denativize-fate-seating` cut off the latest origin/develop (gitflow).

**Source:** sq-playtest ping-pong, "[ENGINE/CRUNCH — KEITH RULING] De-nativize Fate confrontation SEATING" (150-1 annees_folles cross-confirm; first root-caused on 150-2 dust_and_lead via the `beat_selections=2` native-beat-surface finding). This is a **Keith ruling (2026-06-19)**, so the WHAT is decided — the design freedom is in the HOW.

**Scope is narrow and upstream:** #964 already gated the native overlay from co-rendering with FATE_STATE and #966 seeds opponent FateSheets — both merged and verified. This story is the remaining UPSTREAM half: stop *seating* native beat_defs / a tension dial for a Fate confrontation in the first place. It pairs with the already-shipped server PR #973 (opponent projection) and the open UI story 126-31 (win-meter render) — land this seating fix first, then 126-31 draws the meter off opponent stress.

**Guardrails for TEA/Dev (do NOT relax — these are the ADR-144 safety nets, not the bug):**
- `compute_dc` NotImplementedError (game/ruleset/fate.py) stays — it's the tripwire that proves no native DC path is taken.
- `decide_opponent_action` sheet-required guard (#966) stays.
- Per ADR-143/SOUL "Bind the Ruleset, Don't Balance It": the native mechanic is *removed* from the Fate path, not tuned/gated to coexist. If you catch yourself balancing a native dial against Fate, stop.

**Watch-out:** this touches `encounter_lifecycle.py` seating, which is load-bearing for ALL confrontation seating (combat/native packs included). The change must be `ruleset=='fate'`-gated so native-pack seating is untouched — the red tests should assert both: Fate seats Fate-only, AND a native-pack confrontation still seats its beats.

**OTEL:** AC-4 requires the GM-panel lie-detector proof — a Fate seat emits FATE_ROLL + fate.* + confrontation.* spans and NO native beat spans. That span assertion is the wiring test.

**Handoff:** → TEA (Amos Burton) for the red phase. Parent epic context refreshed at `sprint/context/context-epic-126.md`; story context at `sprint/context/context-story-126-30.md`.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Engine behavior change (de-nativize Fate seating) — needs a failing test that pins the de-nativized seating and a regression guard for native packs.

**Test Files:**
- `sidequest-server/tests/server/dispatch/test_fate_seating_denativized_126_30.py` — 4 tests against the real seater (`instantiate_encounter_from_trigger`), real spaghetti_western standoff shape (pre_combat + native `tension` dials + native beats), OTEL span capture via the global provider.

**Tests Written:** 4 tests covering AC-1, AC-2, AC-3, AC-4 (AC-5 = manual GM-panel verify, see deviations)
**Status:** RED (`1 failed, 3 passed` — verified via testing-runner + direct `-n0` run)

- 🔴 `test_fate_standoff_seat_removes_native_tension_dial` — **FAILS** (the RED): a Fate standoff seats on the native dial track (`win_condition='dial_threshold'`, `contest=None`). Drives the fix.
- ✅ `test_fate_standoff_win_signal_is_opponent_stress_not_dial` — pin (AC-2): opponent carries a FateSheet with physical/mental stress tracks (the taken-out win substrate).
- ✅ `test_native_pack_standoff_keeps_native_dial_track` — pin (the watch-out): a `dial` pack keeps its native dial + no Fate opponent seeding → proves the fix must be `ruleset=='fate'`-gated.
- ✅ `test_fate_compute_dc_guard_preserved` — pin (AC-3): `compute_dc` still raises `NotImplementedError` (ADR-144 tripwire).

### Rule Coverage

| Rule (python.md) | Test(s) | Status |
|------|---------|--------|
| #3 type-annotations | all 4 tests `-> None`; `# type: ignore[arg-type]` carries code + comment | pass |
| #6 test-quality (no vacuous assertions) | every test asserts specific values (`win_condition`, `contest`, stress-set, span membership) or `pytest.raises` | pass |
| #1,#2,#5,#7,#8,#9,#11 | N/A — test file has no exception handling, mutable defaults, path/file/resource/deserialization/async/user-input | n/a |

**Rules checked:** 2 of 2 applicable lang-review rules (#3, #6) have coverage; remaining 11 are not applicable to a pure pytest fixture file.
**Self-check:** 0 vacuous assertions found (no `assert True`, no truthy-only `assert result`, no assertion-free tests, no `mock.patch`).

**Quality gate (new file):** ruff format + check clean; pyright 0 errors. Only the test file was added — no production source touched, so the develop baseline failure set is unchanged.

**Handoff:** To Dev (Naomi) for GREEN — gate the native dial/beat seeding in `instantiate_encounter_from_trigger` on `ruleset=='fate'` (see Delivery Findings for the marker-choice Question + the gate-the-whole-combat-block Improvement). Make the RED test green WITHOUT breaking the 3 pins (esp. the native-pack regression pin).

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Question** (non-blocking): The encounter has no dedicated "Fate-resolved" marker distinct from the native dial — a seated Fate standoff carries `win_condition='dial_threshold'` + a live `opponent_metric` exactly like a native encounter. Dev/Architect must pick the de-nativization marker deliberately: seat as a Fate Contest (`enc.contest`), add a Fate win-condition value, or a routing flag. Affects `sidequest/server/dispatch/encounter_lifecycle.py` (the `instantiate_encounter_from_trigger` seating branch ~L1668-1799) and possibly `sidequest/game/encounter.py` (StructuredEncounter). The RED test is HOW-agnostic to accommodate either; tighten it once the marker is chosen. *Found by TEA during test design.*
- **Improvement** (non-blocking): The fix must Fate-gate the ENTIRE native combat-seeding block, not only the dial stamping. `if cdef.category == "combat":` (encounter_lifecycle.py ~L1768-1798) runs `_seed_combat_hp_depletion_to_npcs` + `_roll_and_persist_initiative` (hp_depletion) and `_publish_combat_edge_to_npcs` (dial) with no `ruleset` check — both sub-branches leak native seeding under Fate. (The hp_depletion path was not separately RED-tested: under a Fate pack `_roll_and_persist_initiative` reaches `ruleset_config()` → FateConfig and crashes on a missing DEXTERITY map, so it can't seat cleanly today; gate the whole block for Fate and it's moot.) The regression pin guards against over-removal for native packs. Affects `sidequest/server/dispatch/encounter_lifecycle.py`. *Found by TEA during test design.*
- **Observation** (non-blocking): the native dial leaks because the real `spaghetti_western` standoff (a Fate pack) authors native `tension` dials + native `beats` with `stat_check` in its `confrontations.yaml`. The GM-owned content follow-up (audit whether Fate packs' `confrontations.yaml` should carry native dial/beat defs at all) is downstream of this engine seam — flagged for linkage, already tracked GM-side in the ping-pong. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): the narrator dial-advance tool `advance_confrontation` refuses native dial moves on `win_condition=='hp_depletion'` but NOT on the new `'fate_conflict'`. Harmless today — a Fate conflict's metrics are inert placeholders (threshold 1e6) and `dial_threshold_outcome` returns None for non-dial win conditions, so a stray advance never resolves anything — but a Fate conflict should arguably refuse native dial advances too (a Fate conflict resolves via FATE_ACTION, never this tool). Affects `sidequest/agents/tools/advance_confrontation.py` (add a `fate_conflict` arm beside the `hp_depletion` guard at ~L203). *Found by Dev during implementation.*
- **Question** (non-blocking): AC-5 (live GM-panel end-to-end on a real Fate pack — grab/attack an NPC in pulp_noir/annees_folles, confirm Fate-only mechanics, no native tension dial) is a manual DRIVER verify per TEA's deviation, not automated. The seating-layer behavior + OTEL wiring are now automated (4/4 green); the live-stack confirmation needs a server bounce post-merge. Affects the playtest DRIVER (sq-playtest ping-pong). *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (non-blocking): the de-nativization removes the native dial at SEATING but the **downstream** dial guards do not yet recognize `fate_conflict` the way they recognize `hp_depletion`. (1) `apply_beat` suppresses dial mutation only for `hp_depletion` (`sidequest/game/beat_kinds.py:625`), so a stray narrator beat drifts the inert `fate_stress` dial; (2) `advance_confrontation` refuses only `hp_depletion` (`sidequest/agents/tools/advance_confrontation.py:203`). Impact is cosmetic forensics drift, NOT a false resolution (`dial_threshold_outcome` returns None for `fate_conflict`; native overlay gated off for Fate) — and strictly better than the pre-fix bug (real dial false-resolved at 6/10). Recommended fast-follow: extend the `hp_depletion` dial-suppression + advance-refusal to `fate_conflict`, or drop stray beats on a `fate_conflict` encounter the way the `contest` guard does in `narration_apply`. This is "the downstream half" the dev correctly scoped out of a SEATING story. *Found by Reviewer during code review (corroborated by rule-checker).*
- **Improvement** (non-blocking): the Fate `category=='combat'` seating path is **live content** (spaghetti_western/pulp_noir/wry_whimsy author `category: combat` confrontations) and exercises the new `not is_fate` combat gate, but has no test. Current behavior is correct (Fate combat-contest seats via the contest path, native seeding skipped, no crash); a regression removing the gate would re-leak native seeding (or crash on an `hp_depletion` Fate combat). Recommended: a TEA follow-up test seating a Fate `category=='combat'` confrontation — assert no native edge/hp seeding, no crash, and (for a contest) `enc.contest` set / (for beat_selection) `fate.conflict.seeded` fires. Affects `tests/server/dispatch/`. *Found by Reviewer during code review (corroborated by test-analyzer).*
- **Improvement** (non-blocking): the test file `tests/server/dispatch/test_fate_seating_denativized_126_30.py` is still authored in RED-phase present tense though the tests are GREEN — module title "RED (story 126-30)", section header "# 1 — RED", the "Ground truth" block describing `fate → dial_threshold` as current "the bug", and the test docstring "so this fails (RED)". A quick GREEN-phase doc refresh would keep the wiring test honest for future readers. Affects the test file only (docstrings/comments — no behavior). *Found by Reviewer during code review (corroborated by comment-analyzer).*

## Impact Summary

**Upstream Effects:** 1 findings (0 Gap, 0 Conflict, 0 Question, 1 Improvement)
**Blocking:** None

- **Improvement:** the narrator dial-advance tool `advance_confrontation` refuses native dial moves on `win_condition=='hp_depletion'` but NOT on the new `'fate_conflict'`. Harmless today — a Fate conflict's metrics are inert placeholders (threshold 1e6) and `dial_threshold_outcome` returns None for non-dial win conditions, so a stray advance never resolves anything — but a Fate conflict should arguably refuse native dial advances too (a Fate conflict resolves via FATE_ACTION, never this tool). Affects `sidequest/agents/tools/advance_confrontation.py`.

### Downstream Effects

- **`sidequest/agents/tools`** — 1 finding

### Deviation Justifications

6 deviations

- **RED assertion is a HOW-agnostic disjunction, not one prescribed replacement mechanism**
  - Rationale: the Keith ruling specifies the WHAT, not the marker. The encounter model has no dedicated "Fate-resolved" field today (see Delivery Findings Question), so over-specifying one mechanism would dictate the HOW and could falsely fail a faithful fix. Empirically confirmed RED today (1 failed, 3 passed).
  - Severity: minor
  - Forward impact: minor — if Dev/Architect pick a concrete marker, the assertion can be tightened to it in the verify phase.
- **AC-4 tested at the SEATING layer, not the throw layer (no FATE_ROLL / native beat spans asserted)**
  - Rationale: AC-4's FATE_ROLL/beat-span proof belongs to the in-conflict resolution path, already covered by `test_fate_*` (throw/defend/harm) suites; this story is the seating seam.
  - Severity: minor
- **AC-5 (live GM-panel end-to-end) left as a manual DRIVER verify, not an automated RED test**
  - Rationale: a live GM-panel confirmation is not reproducible in a unit RED test; it is a playtest verify step.
  - Severity: minor
  - Forward impact: none — flagged in Delivery Findings so the DRIVER runs it.
- **De-nativization marker: engine-only `fate_conflict` win_condition + `fate.conflict.seeded` span (NOT a Fate Contest)**
  - Rationale: `dispatch_fate_action` selects Contest-vs-Conflict on `enc.contest is not None`; a stress-based conflict MUST keep `contest=None`, so the marker had to move `win_condition` off `dial_threshold` rather than stamp a contest. A dedicated engine-only win_condition keeps native readers off (they branch on `==dial_threshold`/`==hp_depletion`) without polluting the content authoring vocabulary with a value content never authors.
  - Severity: minor
  - Forward impact: minor — sibling 126-31 (UI win-meter) reads opponent stress (not the metrics) so it is consistent; any FUTURE exhaustive switch over the encounter win_condition Literal must handle `'fate_conflict'` (none exists today — all readers are open `==` checks, audited).
- **Gated the ENTIRE native combat-seeding block on `not is_fate`, beyond the RED test's pre_combat standoff**
  - Rationale: doctrine — under Fate, combat is a Fate conflict (4dF + stress), so native combat seeding is REMOVED, not balanced; also pre-empts the known `_roll_and_persist_initiative` crash (FateConfig carries no DEXTERITY map). The native-pack regression pin guards against over-removal.
  - Severity: minor
  - Forward impact: minor — a Fate pack authoring `category=combat` now seats as a Fate conflict (no native HP/initiative/edge). No live Fate pack authors combat hp_depletion today; the GM-content audit (TEA Observation) is the downstream follow-up.
- **Tightened TEA's HOW-agnostic RED test to the chosen marker + the de-nativization span (a Dev test edit)**
  - Rationale: the new `fate.conflict.seeded` span is a subsystem decision (OTEL Observability Principle) and needs a wiring test ("Every Test Suite Needs a Wiring Test"); the existing test already drives the de-nativized seat, so asserting the span there is the natural, refactor-stable wiring proof — exactly the tightening TEA's deviation pre-authorized for this phase.
  - Severity: minor
  - Forward impact: none — strengthens the guard.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **RED assertion is a HOW-agnostic disjunction, not one prescribed replacement mechanism**
  - Spec source: context-story-126-30.md, AC-1 / AC-2
  - Spec text: "seat a standoff/conflict as a pure Fate contest (Fate mechanics only) … the win signal is the opponent's stress … NOT the vestigial opponent_metric.tension dial"
  - Implementation: `test_fate_standoff_seat_removes_native_tension_dial` fails iff the seat is left on the bare native-dial track — `win_condition == 'dial_threshold' AND contest is None`. It does NOT assert a specific replacement (it passes whether Dev stamps a Fate Contest OR moves the win condition off `dial_threshold`).
  - Rationale: the Keith ruling specifies the WHAT, not the marker. The encounter model has no dedicated "Fate-resolved" field today (see Delivery Findings Question), so over-specifying one mechanism would dictate the HOW and could falsely fail a faithful fix. Empirically confirmed RED today (1 failed, 3 passed).
  - Severity: minor
  - Forward impact: minor — if Dev/Architect pick a concrete marker, the assertion can be tightened to it in the verify phase.
- **AC-4 tested at the SEATING layer, not the throw layer (no FATE_ROLL / native beat spans asserted)**
  - Spec source: context-story-126-30.md, AC-4
  - Spec text: "OTEL span proof: FATE_ROLL + fate.* + confrontation.* spans present; no native beat spans"
  - Implementation: at seating, FATE_ROLL (a 4dF throw-time span) does not fire, and a `pre_combat` standoff seats no native BEAT spans (native beat/edge spans fire only on `category=='combat'` seeding or the payload layer #964 already gated). So the test asserts the seating-layer equivalent: `fate.opponent.seeded` present (Fate resolution engaged) + the native-dial-track data absent + the regression pin (native pack still seeds its dial).
  - Rationale: AC-4's FATE_ROLL/beat-span proof belongs to the in-conflict resolution path, already covered by `test_fate_*` (throw/defend/harm) suites; this story is the seating seam.
  - Severity: minor
  - Forward impact: none
- **AC-5 (live GM-panel end-to-end) left as a manual DRIVER verify, not an automated RED test**
  - Spec source: context-story-126-30.md, AC-5
  - Spec text: "Verify the seating fix integrates end-to-end … confirm GM panel shows Fate mechanics only (no native tension dial)"
  - Implementation: not automated — the seating-layer behavior tests are the automatable proxy; AC-5 is a live-stack GM-panel verification for the DRIVER post-merge (server bounce on a real Fate pack).
  - Rationale: a live GM-panel confirmation is not reproducible in a unit RED test; it is a playtest verify step.
  - Severity: minor
  - Forward impact: none — flagged in Delivery Findings so the DRIVER runs it.

### Dev (implementation)
- **De-nativization marker: engine-only `fate_conflict` win_condition + `fate.conflict.seeded` span (NOT a Fate Contest)**
  - Spec source: context-story-126-30.md AC-1/AC-2; TEA Delivery Finding "Question" (marker choice)
  - Spec text: "seat a standoff/conflict as a pure Fate contest (Fate mechanics only) … the win signal is the opponent's stress … NOT the vestigial opponent_metric.tension dial"
  - Implementation: under `ruleset=='fate'` and `resolution_mode not in (contest, sealed_letter_lookup)`, stamped `enc.win_condition='fate_conflict'` (a NEW engine-only Literal value on StructuredEncounter — NOT a content `WinCondition` enum member) + inert placeholder metrics, and emit a new `fate.conflict.seeded` OTEL span. Did NOT route the conflict through `enc.contest` (the Contest engine is first-to-N victories; a standoff/conflict resolves via the opponent FateSheet stress → taken-out, i.e. the conflict engine keyed on `enc.contest is None`).
  - Rationale: `dispatch_fate_action` selects Contest-vs-Conflict on `enc.contest is not None`; a stress-based conflict MUST keep `contest=None`, so the marker had to move `win_condition` off `dial_threshold` rather than stamp a contest. A dedicated engine-only win_condition keeps native readers off (they branch on `==dial_threshold`/`==hp_depletion`) without polluting the content authoring vocabulary with a value content never authors.
  - Severity: minor
  - Forward impact: minor — sibling 126-31 (UI win-meter) reads opponent stress (not the metrics) so it is consistent; any FUTURE exhaustive switch over the encounter win_condition Literal must handle `'fate_conflict'` (none exists today — all readers are open `==` checks, audited).
- **Gated the ENTIRE native combat-seeding block on `not is_fate`, beyond the RED test's pre_combat standoff**
  - Spec source: TEA Delivery Finding "Improvement" (non-blocking); SOUL "Bind the Ruleset"; ADR-143/144
  - Spec text: "The fix must Fate-gate the ENTIRE native combat-seeding block, not only the dial stamping … both sub-branches leak native seeding under Fate"
  - Implementation: changed `if cdef.category == "combat":` to `if cdef.category == "combat" and not is_fate:`, removing `_seed_combat_hp_depletion_to_npcs` / `_roll_and_persist_initiative` / `_publish_combat_edge_to_npcs` from ALL Fate paths (conflict AND contest), not only the `pre_combat` standoff the RED test exercises.
  - Rationale: doctrine — under Fate, combat is a Fate conflict (4dF + stress), so native combat seeding is REMOVED, not balanced; also pre-empts the known `_roll_and_persist_initiative` crash (FateConfig carries no DEXTERITY map). The native-pack regression pin guards against over-removal.
  - Severity: minor
  - Forward impact: minor — a Fate pack authoring `category=combat` now seats as a Fate conflict (no native HP/initiative/edge). No live Fate pack authors combat hp_depletion today; the GM-content audit (TEA Observation) is the downstream follow-up.
- **Tightened TEA's HOW-agnostic RED test to the chosen marker + the de-nativization span (a Dev test edit)**
  - Spec source: TEA Design Deviation "RED assertion is a HOW-agnostic disjunction"
  - Spec text: "if Dev/Architect pick a concrete marker, the assertion can be tightened to it in the verify phase"
  - Implementation: added to test 1 — `assert enc.win_condition=='fate_conflict'` AND `'fate.conflict.seeded' in names` (the OTEL wiring test for the de-nativization); added to the native-pack pin — `'fate.conflict.seeded' not in names` (ruleset-gating proof). The original HOW-agnostic disjunction assertion is unchanged and still passes; the 3 pins still pass.
  - Rationale: the new `fate.conflict.seeded` span is a subsystem decision (OTEL Observability Principle) and needs a wiring test ("Every Test Suite Needs a Wiring Test"); the existing test already drives the de-nativized seat, so asserting the span there is the natural, refactor-stable wiring proof — exactly the tightening TEA's deviation pre-authorized for this phase.
  - Severity: minor
  - Forward impact: none — strengthens the guard.

### Reviewer (audit)
Every logged deviation reviewed and stamped:
- **TEA — RED assertion is a HOW-agnostic disjunction** → ✓ ACCEPTED by Reviewer: sound; leaving the marker to Dev was correct, and Dev tightened it to the concrete `fate_conflict` marker exactly as the deviation invited. No mechanism was over-specified prematurely.
- **TEA — AC-4 tested at the SEATING layer, not the throw layer** → ✓ ACCEPTED by Reviewer: correct scoping — FATE_ROLL is a throw-time span and a `pre_combat` standoff emits no native BEAT spans at seating, so the seating-layer span proof (`fate.opponent.seeded` + `fate.conflict.seeded` present, native dial absent) is the right wiring assertion for a SEATING story.
- **TEA — AC-5 left as a manual DRIVER verify** → ✓ ACCEPTED by Reviewer: a live GM-panel confirmation is not reproducible in a unit test; the seating-layer behavior tests are the correct automatable proxy. Re-captured as a Delivery Finding so the DRIVER runs it.
- **Dev — de-nativization marker: engine-only `fate_conflict` win_condition + `fate.conflict.seeded` span (NOT a Fate Contest)** → ✓ ACCEPTED by Reviewer: this is the *correct* marker. `dispatch_fate_action` selects Contest-vs-Conflict on `enc.contest is not None`; a stress-based conflict MUST keep `contest=None`, so routing through `enc.contest` would have sent a standoff to the wrong (first-to-N) engine. Moving `win_condition` off `dial_threshold` is right, and the engine-only value (Literal-only, never authored) is verified additive-safe (all readers use open `==` checks).
- **Dev — gated the ENTIRE native combat-seeding block on `not is_fate`** → ✓ ACCEPTED by Reviewer: doctrine-correct (removes native seeding from the Fate path) and pre-empts a real `AttributeError` crash (`_roll_and_persist_initiative` → `FateConfig.attribute_map`). Note: this touches *live* Fate combat confrontations (spaghetti_western `category: combat`), so the absence of a test for that path is captured as a Medium Delivery Finding — the *deviation* is accepted; the *coverage* is the follow-up.
- **Dev — tightened TEA's HOW-agnostic RED test to the chosen marker** → ✓ ACCEPTED by Reviewer: a legitimate OTEL wiring test (drives the real seat, asserts the span fired) that TEA's own deviation pre-authorized; it strengthens the guard and breaks none of the 3 pins.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/server/dispatch/encounter_lifecycle.py` — `instantiate_encounter_from_trigger`: compute `is_fate` / `seat_as_fate_conflict`; under a Fate conflict, remove the native tension dial (inert `fate_stress` placeholder metrics) and stamp `win_condition='fate_conflict'`; emit `fate.conflict.seeded`; gate the entire native combat-seeding block on `not is_fate`.
- `sidequest/game/encounter.py` — added engine-only `"fate_conflict"` to the `StructuredEncounter.win_condition` Literal (+ docstrings; `dial_threshold_outcome` already returns None for it).
- `sidequest/telemetry/spans/fate.py` — new `fate_conflict_seeded_span` + `SPAN_ROUTES["fate.conflict.seeded"]` + `__all__` (the de-nativization GM-panel lie-detector, sibling to `fate.contest.seeded`).
- `tests/server/dispatch/test_fate_seating_denativized_126_30.py` — tightened TEA's HOW-agnostic test to the chosen marker: assert `win_condition=='fate_conflict'` + `fate.conflict.seeded` fires (wiring test); native-pack pin asserts the span is ruleset-gated.

**Marker chosen (TEA's open Question):** a de-nativized Fate standoff/conflict seats with `enc.win_condition='fate_conflict'` (engine-only), `enc.contest is None` (the conflict engine, resolving via the Other's FateSheet stress → taken-out), inert placeholder metrics (native dial removed). A Fate Contest keeps its own `enc.contest` path; sealed-letter is excluded. Native packs are untouched (`is_fate`-gated).

**Tests:** 4/4 passing (GREEN) on `test_fate_seating_denativized_126_30.py`.

**Regression proof:** full server suite captured with-changes vs stashed-baseline (sorted FAILED/ERROR diff) — failure sets IDENTICAL (96 = 96) except the expected RED→GREEN flip of this story's test. The one apparent extra diff (`test_space_opera_swn_combat_e2e::test_firefight_resolves_on_hp_depletion_vs_content_ac`) is xdist-flaky: 3/3 pass in isolation, and my change is a behavioral no-op for non-Fate packs (`is_fate=False` → identical control flow). The dispatch-suite pre-existing failure (`test_legacy_beat_selection_path_still_works`, `'strike' in set()`) fails identically on the stashed baseline (CAC content/fixture issue, not mine).

**Quality gates:** ruff check + format clean on all changed files; pyright 14 errors = 14 baseline errors (zero introduced; all pre-existing, none in edited ranges).

**Branch:** feat/126-30-denativize-fate-seating (to be pushed)

**Handoff:** To verify phase (TEA / Amos Burton) — AC-1..AC-4 automated + OTEL-wired; AC-5 (live GM-panel on a real Fate pack) remains a manual DRIVER step per TEA's deviation (see Delivery Findings).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (4/4 story tests GREEN, telemetry 417 passed, ruff/format clean, pyright 14=14 baseline) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings (edge cases covered by Reviewer: contest/sealed_letter/combat/native branch enumeration) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings (No-Silent-Fallbacks covered by rule-checker rule 14 + Reviewer) |
| 4 | reviewer-test-analyzer | Yes | findings | 5 | confirmed 2 (combat-path gap MED, span/stress-box asserts LOW), dismissed 1 (opposed_check — validator forbids it for Fate), deferred 2 (sealed_letter negative, low value) |
| 5 | reviewer-comment-analyzer | Yes | findings | 8 | confirmed 6 (5× RED-phase stale docstrings LOW, removed_native_dial inconsistency LOW), dismissed 2 (collapsed into the two confirmed clusters) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (Literal addition + win_condition typing covered by rule-checker rule 3/13 + Reviewer) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings (no user-input boundary in diff — reads trusted pack YAML; rule-checker rule 11 confirms no injection vector) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings (change is minimal; inert-metric branch mirrors existing hp_depletion pattern — not over-engineered) |
| 9 | reviewer-rule-checker | Yes | findings | 3 | confirmed 2 (advance_confrontation guard MED, narration_apply beat-path MED — both downstream/out-of-scope), confirmed 1 LOW (`_seat` return annotation — borderline; #3 exempts private helpers) |

**All received:** Yes (4 enabled returned; 5 disabled via `workflow.reviewer_subagents`, domains covered by Reviewer/rule-checker)
**Total findings:** 7 confirmed (3 Medium, 4 Low), 3 dismissed (with rationale), 2 deferred — **zero Critical/High**

## Reviewer Assessment

**Verdict:** APPROVED

The implementation is correct, doctrine-faithful (SOUL "Bind the Ruleset" — the native dial is REMOVED from the Fate path, not balanced), OTEL-wired, and introduces **zero regressions**. Critically, it is **strictly better** than the reported bug: pre-diff a stray beat could advance the real `tension` dial and FALSELY RESOLVE a Fate standoff at threshold (the "observed live at 6/10" finding); post-diff the dial is inert (1e6) and `win_condition='fate_conflict'` routes `dial_threshold_outcome` to `None`, so the dial can no longer resolve the encounter. No Critical/High findings → APPROVE.

**Data flow traced:** a Fate standoff trigger → `instantiate_encounter_from_trigger` (`is_fate`/`seat_as_fate_conflict` gate) → `win_condition='fate_conflict'` + inert `fate_stress` metrics + `_seed_fate_opponents` (opponent FateSheet) + `fate.conflict.seeded` span → FATE_STATE projection reads the **opponent stress** for the win-meter (`fate_projection.py:173-178`), never the inert metrics → safe.

**Pattern observed:** the new `fate_conflict_seeded_span` + `SPAN_ROUTES["fate.conflict.seeded"]` precisely mirror the sibling `fate.contest.seeded` (Span.open + extract-lambda + `__all__`) — wiring up existing infra, not reinventing (`telemetry/spans/fate.py:898-927`).

**Error handling:** the asymmetric-dial guard is preserved (`encounter_lifecycle.py` raises ValueError on exactly-one-of player/opponent metric); the new Fate branch precedes it cleanly; `compute_dc` NotImplementedError tripwire intact (`test_fate_compute_dc_guard_preserved`).

### VERIFIED (evidence + rule compatibility)

- `[VERIFIED]` **`fate_conflict` routes OFF every native `win_condition` reader.** advance_confrontation.py:203, confrontation.py:467, beat_filter.py:239, dice.py:1908 are all `== "hp_depletion"` (skip); narration_apply.py:6494 is `!= "dial_threshold"` → return (suppresses dial advance); `dial_threshold_outcome` (encounter.py:447) is `!= "dial_threshold"` → None. No exhaustive `match`/`isinstance`-on-Literal exists (confirmed by grep + rule-checker rule 13). Complies with the encounter.py Literal-decoupling comment.
- `[VERIFIED]` **Inert `fate_stress` metrics never reach the player win-meter.** `fate_projection.py:159-180` computes the ADR-143 meter from opponent `p.stress` boxes (capacity/used), not `enc.player_metric`/`opponent_metric`/`win_condition`. So the 1e6 placeholders are dead data on the Fate path.
- `[VERIFIED]` **No save-forensics/census branches on `win_condition`** (grep of `game/pg/`, `forensic*`, `save*` empty) — `'fate_conflict'` persists as an opaque string with no exhaustive-switch to break.
- `[VERIFIED]` **Combat-block change is a no-op for native packs.** `cdef.category == "combat" and not is_fate` — `not is_fate` is True for every non-Fate pack → identical control flow; pinned by `test_native_pack_standoff_keeps_native_dial_track` (the diff is byte-equivalent for `dial`/WN packs).
- `[VERIFIED]` **`seat_as_fate_conflict` ∩ contest = ∅, combat gate covers both.** A Fate combat-**contest** (e.g. spaghetti_western `category: combat` + `resolution_mode: contest`) seats via the contest path with the native combat block skipped by `not is_fate`; no double-handling, no crash.
- `[VERIFIED]` **Routing-completeness lint exempts the literal-key SPAN_ROUTES entry.** telemetry suite 417 passed; rule-checker confirms the lint inspects only `SPAN_*` module constants, matching the `fate.contest.seeded` precedent.

### Rule Compliance (Python lang-review + SOUL/CLAUDE)

Rule-checker enumerated 20 rules / 74 instances → 3 violations (all LOW/MEDIUM, below). My independent spot-checks agree:
- **#1 silent-exceptions / #14 No-Silent-Fallbacks:** PASS — `is_fate = bool(pack and pack.rules and ...)` short-circuits to False (not a silent alternate path); inert-metric intent is loudly documented.
- **#3 type-annotations:** `fate_conflict_seeded_span` fully annotated (`-> None`, `**attrs: Any` matches the sibling span family); `_seat()` test helper missing `-> tuple[...]` (LOW — #3 exempts private helpers).
- **#6 test-quality:** PASS — every test has ≥2 specific assertions; no vacuous/skip/wrong-mock.
- **#10 import-hygiene:** PASS — runtime import of `fate_conflict_seeded_span` mirrors the sibling `fate_contest_seeded_span` cycle-avoidance pattern; `__all__` updated alphabetically.
- **#15 No-Stubbing / #16 Don't-Reinvent / #19 OTEL Principle / #20 Bind-the-Ruleset:** PASS — real span, wires existing infra, the de-nativization REMOVES the native dial + native combat seeding (does not coexist).

### Confirmed Findings (all non-blocking)

| Severity | Tag | Issue | Location |
|----------|-----|-------|----------|
| [MEDIUM] | [TEST] | The Fate `category=='combat'` path is **live content** (spaghetti_western/pulp_noir/wry_whimsy author `category: combat` confrontations) and exercises the changed `not is_fate` gate, but has **no test**. Current behavior is correct (contest path + native seeding skipped, no crash), so this is a coverage gap, not a bug. | `encounter_lifecycle.py:1806`; test file |
| [MEDIUM] | [RULE] | `advance_confrontation.py:203` refuses narrator dial-drift only for `hp_depletion`, not `fate_conflict` — the new win_condition makes a forensics-pollution path newly reachable. Mitigated: `dial_threshold_outcome` returns None for `fate_conflict` (no false resolution); impact is cosmetic forensics noise. Dev flagged this in Delivery Findings; rule-checker independently confirmed. **Downstream half.** | `advance_confrontation.py:203` |
| [MEDIUM] | [RULE] | `narration_apply.py` beat path: a stray narrator beat on a `fate_conflict` encounter reaches `apply_beat`, which suppresses dial mutation only for `hp_depletion` (beat_kinds.py:625) — so the inert `fate_stress` dial drifts. Mitigated: native overlay suppressed for Fate (invisible to player) + `dial_threshold_outcome` None (no false resolution) → cosmetic forensics noise. **Downstream half**, explicitly out of scope for a SEATING story. | `narration_apply.py:~5955`, `beat_kinds.py:625` |
| [LOW] | [DOC] | Test file is still written in RED-phase present tense on a now-GREEN test: title "RED (story 126-30)", "# 1 — RED", "Ground truth: seat under fate → dial_threshold (the bug)", test docstring "so this fails (RED)", root-cause "but NOT on pack.rules.ruleset". Misleading to a future reader. | test file:1,18,22,147,156 |
| [LOW] | [DOC] | `fate_conflict_seeded_span` docstring says `removed_native_dial` "always True", but the param is overridable and the SPAN_ROUTES extractor defaults `False` — minor self-inconsistency (harmless; mirrors the flavor_rider "attached always True" precedent). | `fate.py:915,498` |
| [LOW] | [TEST] | Span attribute values (`opponent_count`, `category`) and opponent stress-box capacity are not asserted — a bug in the actor-side filter or an empty-boxes sheet would pass. | test file:387,418 |
| [LOW] | [TYPE] | `_seat(pack)` test helper missing a return annotation (returns a 3-tuple). | test file:119 |

### Dismissed
- **opposed_check de-nativization untested (test-analyzer):** DISMISSED — `_fate_packs_have_no_opposed_check` (rules.py:1521) forbids `opposed_check` for Fate packs at load time, so the state is unreachable.
- **table_resolution not in the exclusion tuple (latent):** DISMISSED — `table_resolution` returns early (encounter_lifecycle.py:~1245) before `seat_as_fate_conflict` is computed, so it never de-nativizes.

### Devil's Advocate

Argue this is broken. **The strongest attack: the de-nativization is half a fix.** This story removes the native dial at SEATING but leaves three downstream native-dial guards (`advance_confrontation.py:203`, `apply_beat` dial-suppression at `beat_kinds.py:625`, and the missing `narration_apply` beat-drop guard that `contest` has) blind to `fate_conflict`. The dev modeled `fate_conflict` on `hp_depletion` ("same belt-and-suspenders") at the seat — but `hp_depletion` ALSO suppresses dial mutation in `apply_beat` and is refused by `advance_confrontation`, and `fate_conflict` inherits NEITHER. So a Fate conflict carries an inert dial that downstream code is still willing to mutate. A malicious or confused narrator emitting a native `beat` (or calling `advance_confrontation`) on a live Fate standoff would drift `fate_stress` 0→N in persisted forensics, exactly the barsoom-2 / 59-26 pollution pattern these guards were built to stop. **Why it does not sink the PR:** (1) it is strictly better than the status quo — pre-diff that same stray beat advanced a *real* threshold-10 dial and could *falsely resolve* the encounter (the reported 6/10 bug); post-diff the threshold is 1e6 and `dial_threshold_outcome` returns None, so the worst case degrades from "false victory" to "cosmetic forensics drift"; (2) the player UI is unaffected — the native overlay is gated off for Fate (`should_emit_native_confrontation`), and FATE_STATE reads opponent stress; (3) for a Fate pack the narrator is routed through the Fate-action classifier, so native beats on a Fate confrontation are an edge case, not the hot path; (4) the story's scope is explicitly SEATING, and the dev correctly named this "the upstream half." A confused user sees nothing wrong; a stressed save file gains a harmless drifting integer. The right resolution is a fast-follow that extends the `hp_depletion` dial-suppression + advance-refusal to `fate_conflict` (or drops stray beats on a `fate_conflict` encounter the way the `contest` guard does) — captured as a blocking-priority **Improvement** in Delivery Findings. Nothing here is a correctness regression, a security hole, or a data-corruption risk.

**Handoff:** To SM (Camina Drummer) for finish-story. The three Medium findings are downstream/coverage follow-ups, not blockers; captured in Delivery Findings.