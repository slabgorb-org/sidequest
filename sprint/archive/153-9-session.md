---
story_id: "153-9"
jira_key: ""
epic: "153"
workflow: "tdd"
---
# Story 153-9: [FATE-OTHER-SEATING] router names the scene-active antagonist, not a same-surname roster NPC (ADR-116)

## Story Details
- **ID:** 153-9
- **Jira Key:** (no Jira integration)
- **Workflow:** tdd
- **Stack Parent:** none
- **Type:** bug
- **Points:** 3
- **Priority:** p3

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-21T17:29:34Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-21T22:00:00Z | 2026-06-21T16:39:55Z | -19205s |
| red | 2026-06-21T16:39:55Z | 2026-06-21T16:54:26Z | 14m 31s |
| green | 2026-06-21T16:54:26Z | 2026-06-21T17:18:06Z | 23m 40s |
| review | 2026-06-21T17:18:06Z | 2026-06-21T17:29:34Z | 11m 28s |
| finish | 2026-06-21T17:29:34Z | - | - |

## Sm Assessment

**Setup complete — ready for RED phase (TEA / Amos Burton).**

**Story:** Server-side confrontation-seating bug under the Fate Core binding (ADR-144). When the intent router/opponent-seater resolves the Other for a confrontation (ADR-116), it picks a same-surname roster NPC instead of the scene-active antagonist the narrator just described. Violates ADR-116's single-opponent-seater invariant and ADR-139's "mechanically-capable Other" — the combat panel ends up seating the wrong NPC versus the narration.

**Scope:** `server` only. No content/UI changes.

**Technical approach (for TEA + Dev):**
- Root cause per setup research: the roster-fallback selection has no signal marking which NPC is the scene-active antagonist for *this* confrontation, so it matches on surname against `snapshot.npcs`.
- Primary candidate: `sidequest/server/dispatch/encounter_lifecycle.py` — `_resolve_opponent_from_roster()` (~874–947), `instantiate_encounter_from_trigger()` (~1389).
- Secondary: `sidequest/agents/subsystems/confrontation.py` (opponent materialization ~108–136), `sidequest/game/encounter.py` (model).
- Tests: extend `test_opponent_roster_resolution.py`; add a Fate antagonist-surname-collision case; verify against `test_fate_opponent_seating.py`.

**Acceptance criteria:** Captured in `sprint/context/context-story-153-9.md` (5 ACs covering Fate-specific seating preference, narrative-antagonist prioritization over ambient/same-surname roster NPC, dedup, and fallback).

**Checklist:**
- Jira: explicitly skipped — no Jira integration on this story (jira_key empty).
- Story context: written with technical approach, candidate files, and ACs.
- Branch: `feat/153-9-fate-other-seating-scene-active-antagonist` created in sidequest-server.

**Reminder for downstream (OTEL doctrine):** Per CLAUDE.md, the seater fix must emit an OTEL watcher event recording *which* NPC was selected as the Other and *why* (scene-active antagonist vs roster fallback), so the GM panel can verify the seater engaged rather than the narrator improvising.

**Next agent:** TEA (red phase).

## TEA Assessment

**Tests Required:** Yes
**Reason:** n/a (3-pt bug; behavior change to the opponent-seating decision)

**Test Files:**
- `sidequest-server/tests/server/dispatch/test_153_9_fate_other_seating.py` — 4 tests driving the real `instantiate_encounter_from_trigger` seam (2 RED bug-pins + 2 GREEN keys-on-ruleset guards)

**Tests Written:** 4 tests covering 5 ACs (AC-1 audited via AC-2/AC-3/AC-4 behavioral pins; AC-5 = the headline test)
**Status:** RED (2 failing, ready for Dev) — verified via testing-runner (`2 failed, 2 passed`)

**The bug, confirmed end-to-end:** under the live `pulp_noir` Fate pack, a `category=="combat"` confrontation where the router names the scene-active antagonist ("Silas Vance") seats a co-located same-surname statted adversary ("Marguerite Vance") instead — because `_resolve_opponent_from_roster` (the 108-2 reconciliation) is gated only on `confrontation_category != "combat"` (line 939) and has no Fate awareness. Reproduced live before writing the tests.

**Fix direction handed to Dev (Naomi):** decline the roster conscription under a Fate binding — the Fate sibling of the 150-2 non-combat decline. `_resolve_opponent_from_roster` runs at line 1389, BEFORE `is_fate` is computed (line 1671); the gate must either be passed into the helper or applied at the call site. Either location is fine — the tests pin observable behavior through the public seam, not the helper signature. The 108-2 reconciliation stays intact for non-Fate combat (ADR-059: preserve bound bestiary HP — meaningless under Fate, which resolves on FateSheet stress).

**OTEL contract (Test 2):** the decline must emit a decision span. Test 2 expects reuse of the existing `encounter.roster_resolution_skipped` span (with `declined_name="Marguerite Vance"`) — the same span the 150-2 non-combat decline already emits — and asserts the 108-2 `encounter.opponent_resolved_from_roster` span does NOT fire. If Dev emits a Fate-specific decline span under a different name, update Test 2's span-name assertion to match (the load-bearing half — "resolve span absent" — is name-agnostic).

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| OTEL Observability Principle (CLAUDE.md) / python #4 logging | `test_fate_decline_to_conscript_emits_decision_span` | failing |
| Wiring test (CLAUDE.md "Every Test Suite Needs a Wiring Test") | all 4 drive real `instantiate_encounter_from_trigger`; Test 2 asserts the span fires through the production seam | failing/passing |
| python #6 test quality (meaningful assertions, no vacuous) | self-check: all assert exact lists / span attrs; `skipif` carries a reason | pass |
| Keys-on-ruleset (no blanket disable) | `test_non_fate_combat_still_conscripts_colocated_adversary` | passing |

**Rules checked:** OTEL/observability + test-quality + wiring are the rules applicable to a seating-decision bug-fix; input-validation/path/async/deserialization rules (#3/#5/#7-#13) do not apply to this change surface.
**Self-check:** 0 vacuous tests found.

**Handoff:** To Dev (Naomi Nagata) for the GREEN implementation.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/sidequest/server/dispatch/encounter_lifecycle.py` — (1) `_resolve_opponent_from_roster` takes a new `is_fate: bool` param; its 150-2 decline gate is extended to `confrontation_category != "combat" or is_fate`, with a `reason` attr (`fate_binding` / `non_combat`) on the existing `encounter.roster_resolution_skipped` lie-detector span; (2) `is_fate` is resolved ONCE at the seating seam (just before the `materialized_threat` block) and passed to the helper + reused by the downstream 126-30 Fate de-nativization branch (removing the duplicate computation); (3) docstring updated to record the Fate/non-combat decline.

**Tests:** GREEN
- Story tests: `tests/server/dispatch/test_153_9_fate_other_seating.py` — 4/4 passing.
- Regression: `tests/server/test_opponent_roster_resolution.py` + `tests/server/dispatch/test_fate_opponent_seating.py` — 18/18 passing (the helper signature + gate change is exercised; 108-2 native-combat reconciliation preserved).
- Lint: `ruff check encounter_lifecycle.py` clean.

**OTEL:** the decline emits `encounter.roster_resolution_skipped` with `declined_name` + `reason="fate_binding"` so the GM panel sees the engine refused the ambient adversary (CLAUDE.md OTEL principle); the 108-2 `encounter.opponent_resolved_from_roster` span is correctly absent under Fate.

**Branch:** `feat/153-9-fate-other-seating-scene-active-antagonist` (pushed to origin).

**⚠ PRE-EXISTING RED BASELINE (not introduced by 153-9):** the full server suite has **37 failures** on `develop` that predate this story, spanning unrelated subsystems (chargen wiring, lore RAG, spellcasting payloads, premise loader, encountergen/pregen bestiary, app LLM-client default, WWN-content beat de-nativization). My change is isolated to `encounter_lifecycle.py` and the 22 seating-related tests all pass — none of the 37 are in this change's blast radius. Verified root causes include epic-157's `effective_bestiary` stub drift (`test_pregen_*` SimpleNamespace stubs not updated for the new `pack.effective_bestiary(world)` call at `pregen.py:494`, commit `0f199b0f`/#1002) and a stale `strike`-beat assertion in `test_sealed_letter_dispatch_integration.py` (CAC combat was WWN-de-nativized → `cdef.beats == set()`). **Operator (2026-06-21) approved a focused handoff** — these are tracked as a blocking Delivery Finding for separate triage, not fixed in 153-9.

**Handoff:** To Reviewer (Chrisjen Avasarala) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (22/22 targeted green, ruff clean, 14 pyright errors all PRE-EXISTING outside the diff) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 3 (1 high, 1 med, 1 low) | confirmed 3 (all non-blocking), dismissed 0, deferred 0 |
| 5 | reviewer-comment-analyzer | Yes | findings | 2 (1 high-conf, 1 med) | confirmed 2 (non-blocking), dismissed 0, deferred 0 |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 2 (both low, test-only) | confirmed 0 (rule-exempt), dismissed 2 with rationale, deferred 0 |

**All received:** Yes (4 returned + 5 disabled-via-settings)
**Total findings:** 4 confirmed non-blocking, 2 dismissed (with rationale), 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

The production fix is correct, surgical, and isolated to one file. It is the right fix for [FATE-OTHER-SEATING] and it follows the established 150-2 decline pattern faithfully ("Bind the Ruleset" doctrine). The confirmed findings are all MEDIUM/LOW test-quality and doc-accuracy polish — none is a production correctness, security, or error-handling defect (no Critical/High severity), so none blocks. They are logged as non-blocking Delivery Findings for a fast follow-up.

### Observations

- `[VERIFIED]` **`is_fate` scoping is sound — no UnboundLocalError path.** Defined unconditionally at function-body level (`encounter_lifecycle.py:1391`); all uses (`:1413`, `:1692`, `:1872`) are textually after it within the same function. Proven by passing tests on BOTH branches: `test_fate_seats_named_antagonist...` drives the full Fate path (is_fate=True through 1692/1872), `test_non_fate_combat...` drives the non-Fate path (is_fate=False). Complies with the No-Silent-Fallbacks rule (the `bool(pack and pack.rules and ...)` None-chain degrades to False/non-Fate, preserving prior behavior, not masking a config error).
- `[VERIFIED]` **Gate logic correct + non-Fate path untouched.** `if confrontation_category != "combat" or is_fate:` (`:952`) declines non-combat (any ruleset) OR any category under Fate; native combat (`is_fate=False, category=="combat"`) still reaches `return candidates[0]`. Confirmed by `test_non_fate_combat_still_conscripts_colocated_adversary` (green) + the 13 pre-existing `test_opponent_roster_resolution.py` tests (green). Complies with ADR-059 (108-2 reconciliation preserved for native combat) and ADR-143/144 (Fate removes, not balances).
- `[VERIFIED]` **Exact-match dedup precedes the gate.** `if any(n.core.name == threat_name ...): return None` at `:912` fires before the new gate at `:952`, so an exactly-named roster Other is seated regardless of `is_fate` — the Fate gate cannot over-correct against legitimate targeting. Evidence: `:912` ordering + `test_fate_exact_roster_target_is_still_seated` green.
- `[RULE]` **All 13 Python lang-review rules clean on production code** (rule-checker). New `is_fate: bool` param annotated (#3); decline emits the OTEL lie-detector span, no swallow (#1/#4); no mutable defaults, star imports, unsafe deserialization, or resource leaks. `reason=` flows through `encounter_roster_resolution_skipped_span(**attrs)` (`telemetry/spans/encounter.py:1113`) — no signature mismatch.
- `[TEST]` **MEDIUM — `test_fate_decline_to_conscript_emits_decision_span` does not assert the `reason` attribute.** The production span carries `reason="fate_binding"` — the discriminator between the Fate decline and the 150-2 non-combat decline, and the OTEL legibility the story is *about*. The test asserts `declined_name` but not `reason`, so a misclassified `reason="non_combat"` on a Fate combat would still pass. The BEHAVIOR is correct (verified by rule-checker + my read of `:957`); only the test coverage of it is incomplete. Non-blocking. (`test_153_9_fate_other_seating.py:~226`)
- `[TEST]` **MEDIUM — `test_fate_exact_roster_target_is_still_seated` is a non-discriminating guard.** It cannot go RED on a 153-9 revert: the `:912` exact-match short-circuit precedes the new gate, so the test passes with or without the fix. It is a legitimate regression guard (exact-targeting must keep working under Fate) but adds no discriminating power for the delta. Acceptable as a guard; noted. Non-blocking.
- `[DOC]` **MEDIUM (high-confidence) — the just-edited `_resolve_opponent_from_roster` docstring omits the no-location `None` return.** The `Returns ... None` enumeration (`:894`) was edited in THIS diff to list the None cases but skips the `if not location: return None` path at `:915-916`. In a lie-detector-culture project, an incomplete just-edited docstring is worth fixing. Non-blocking (doc-only, no behavior impact).
- `[DOC]` **LOW — the "same-surname 'Marguerite Vance'" comment (`:945`) overframes the mechanism.** The conscription predicate is purely location + `creature_id` + adversarial disposition; names are never compared. The surname is the playtest manifestation, not the cause. Could mislead a future reader into thinking the fix involves name-matching. Non-blocking.
- `[EDGE]` (subagent disabled — assessed by Reviewer) **No new boundary defects.** Checked: `pack=None`/`pack.rules=None` → `is_fate=False` (safe, prior behavior); Fate contest/sealed-letter → declines conscription correctly (Fate seeds the FateSheet, not creature_id hp, so no stat loss); the `reason` value for a Fate NON-combat decline reports `fate_binding` though 150-2 also applies — minor observability ambiguity, not a defect.
- `[SILENT]` (subagent disabled — assessed by Reviewer) **No swallowed errors / silent fallbacks.** The decline path emits `encounter.roster_resolution_skipped` (loud lie-detector), not a silent return. The `bool(...)` None-chain is a defined-behavior default to non-Fate, not a masked failure.
- `[TYPE]` (subagent disabled — assessed by Reviewer) **Type contract sound.** New `is_fate: bool` is a required keyword-only param (no silent default); single caller passes it; return type unchanged.
- `[SEC]` (subagent disabled — assessed by Reviewer) **No security surface.** Engine-internal seating decision; no auth, no user-input parsing, no tenant data, no injection sink. `ruleset` is validated pack YAML.
- `[SIMPLE]` (subagent disabled — assessed by Reviewer) **Change is minimal and de-duplicating.** It removes the duplicate `is_fate` computation rather than adding complexity; the gate is a one-clause extension. No over-engineering.

### Rule Compliance

Mapped to `.pennyfarthing/gates/lang-review/python.md` (rule-checker exhaustive pass, cross-verified):
- **#1 silent exceptions** — compliant: decline emits a span, no bare except; test helpers catch `PackNotFound` specifically.
- **#3 type annotations** — compliant on production (`is_fate: bool`); one LOW test-helper (`_combat_encounter_type(pack)`) unannotated but private → rule's internal-helper exemption applies → dismissed.
- **#4 logging/observability** — compliant: OTEL span is the canonical mechanism (CLAUDE.md OTEL Principle); the decision is GM-panel-legible.
- **#6 test quality** — production assertions are specific (`== ["Silas Vance"]`, span name presence/absence, `declined_name`); `skipif` carries a reason. The two LOW nits (`assert enc is not None` without a message) are not vacuous (checking a specific value) → dismissed. The `reason`-not-asserted gap is logged as a MEDIUM non-blocking improvement, above.
- **#2/#5/#7-#13** — not applicable to this change surface (no mutable defaults, paths, resources, deserialization, async, imports, dep changes) — verified clean by rule-checker.

### Devil's Advocate

Suppose this fix is broken. The most plausible attack is on the `is_fate` hoist: the author deleted the downstream computation at the old `:1671` and now relies on a single definition at `:1391`. If ANY control-flow path reached the downstream `seat_as_fate_conflict = is_fate and ...` (`:1692`) or the `cdef.category == "combat" and not is_fate` gate (`:1872`) WITHOUT executing `:1391`, that would be an `UnboundLocalError` in production — a crash on every Fate combat instantiation, far worse than the original bug. I hunted for that path: `:1391` is at function-body indentation, unconditional, after the early `return None` guards (active-encounter `:1244`, resolved-same-type `:1263`, table_resolution `:1274`) and before every downstream use. There is no nested `def` between `:1391` and `:1872` that would rebind scope, and no branch re-enters the function below `:1391`. The passing tests close it empirically: a Fate combat instantiation (`test_fate_seats_named_antagonist...`) runs `:1391 → :1692 → :1872` with `is_fate=True` and does not raise; a non-Fate combat (`test_non_fate_combat...`) runs the same span with `is_fate=False`. Second attack: does declining conscription under Fate strand a genuinely-statted Other? No — under Fate the Other's combat capability comes from `_seed_fate_opponents` (FateSheet stress), not the conscripted creature's `creature_id` hp (ADR-143/144), so seating the router-named threat loses nothing the Fate engine uses. Third attack: a confused GM sees `reason="fate_binding"` on a Fate *social* decline where 150-2 also applies — a labeling ambiguity, but not a wrong decision (the engine genuinely declined; the span genuinely fired). Fourth: `pack=None` → `is_fate=False` → conscription proceeds as before — not a silent failure, just the pre-existing path. None of these uncovers a blocking defect. The fix holds.

**Data flow traced:** router names threat → `materialized_threat` (NpcMention) → `instantiate_encounter_from_trigger` computes `is_fate` from `pack.rules.ruleset` → `_resolve_opponent_from_roster(is_fate=is_fate)` → under Fate the gate declines (returns None, emits `encounter.roster_resolution_skipped`) → `materialized_threat` seated as-is (`seating_source="materialized"`) → the router-named scene-active antagonist reaches the combat panel, not a conscripted ambient adversary. Safe.

**Pattern observed:** Faithful extension of the 150-2 non-combat-decline pattern (`encounter_lifecycle.py:952`) — same span, same return-None shape, gated on the Fate binding instead of re-engineered. Good pattern adherence.

**Error handling:** Defensive `bool(pack and pack.rules and pack.rules.ruleset == "fate")` None-chain; decline path is loud (OTEL), not silent. Correct.

**Pre-existing baseline confirmed:** Per preflight, the 22 targeted tests are green and all 14 pyright errors + the full-suite's 37 failures are PRE-EXISTING on develop, outside this diff's blast radius. This change introduces zero of them. Carried forward as the Dev's blocking Delivery Finding (separate triage; Operator-approved focused handoff).

**Handoff:** To SM (Camina Drummer) for finish-story.

## Delivery Findings

No upstream findings

### TEA (test design)
- **Improvement** (non-blocking): The story-context root cause ("the seater has no signal marking which NPC is the scene-active antagonist") is broader than the reproduced defect. The live repro is narrower: `_resolve_opponent_from_roster` conscripts ANY co-located `creature_id`-statted adversary under Fate combat because the 108-2 reconciliation is gated on category only, not on the Fate binding. The minimal correct fix is to decline conscription under Fate (mirror the 150-2 non-combat decline), not to build a new "scene-active antagonist marker." Affects `sidequest/server/dispatch/encounter_lifecycle.py` (`_resolve_opponent_from_roster` ~line 939 gate and/or its caller ~line 1389). *Found by TEA during test design.*
- **Question** (non-blocking): Under Fate, should the 108-2 reconciliation be declined for ALL categories (combat + non-combat), collapsing the Fate path into the existing 150-2 decline regardless of category? The tests only pin the combat case (the repro), but a Fate-binding gate that subsumes the category gate would be the cleaner invariant. Dev's call. Affects `sidequest/server/dispatch/encounter_lifecycle.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (blocking): `develop` has a large pre-existing red baseline — **37 failures** in the full server suite, unrelated to 153-9 and unrelated to each other, that will block the full-suite `tests-pass`/`dev-exit`/quality gates for ANY story. Confirmed root causes so far: (a) epic-157 `effective_bestiary` stub drift — `0f199b0f`/#1002 added `pack.effective_bestiary(world)` at `pregen.py:494` and updated `test_pregen.py`'s stub but NOT the `_stub_pack` SimpleNamespaces in `test_pregen_fail_loud_90_5.py` / `test_pregen_combat_gate.py` (fix: add `effective_bestiary=lambda _world: (None, "stub")`); (b) WWN beat de-nativization — `test_sealed_letter_dispatch_integration.py::test_legacy_beat_selection_path_still_works` asserts a `strike` beat in the live `caverns_and_claudes` combat confrontation, but `cdef.beats == set()` (the WWN binding removed native beats per ADR-143) — a stale assertion. The remaining ~32 span chargen wiring/lore RAG/spellcasting payload/premise loader/encountergen/app-default tests and need triage. Affects multiple repos/epics — NOT fixable within 153-9's scope. Operator approved a focused handoff (2026-06-21). *Found by Dev during implementation (broad regression sweep).*
- **Improvement** (non-blocking): `_resolve_opponent_from_roster`'s decline span now carries a `reason` attr (`fate_binding`/`non_combat`). If other call paths surface a third decline reason later, keep the attr exhaustive so the GM panel can always distinguish WHY a co-located adversary was refused. Affects `sidequest/server/dispatch/encounter_lifecycle.py`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `test_fate_decline_to_conscript_emits_decision_span` should also assert `attrs.get("reason") == "fate_binding"` — the span's `reason` is the discriminator between the Fate decline and the 150-2 non-combat decline (the OTEL legibility this story is about), and a misclassified `non_combat` reason on a Fate combat would currently pass. Behavior is correct; only the test coverage of it is incomplete. Affects `tests/server/dispatch/test_153_9_fate_other_seating.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the just-edited `_resolve_opponent_from_roster` docstring (`Returns ... None` enumeration) omits the no-location early return (`if not location: return None`). Add the fourth `None` case so the docstring matches the code. Affects `sidequest/server/dispatch/encounter_lifecycle.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the `# ... the seater grabs the same-surname "Marguerite Vance"` comment frames the bug as a name-match, but the conscription predicate is purely location + `creature_id` + disposition (names never compared). Clarify that same-surname is the playtest manifestation, not the mechanism, to avoid misleading a future reader. Affects `sidequest/server/dispatch/encounter_lifecycle.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `test_fate_exact_roster_target_is_still_seated` cannot go RED on a 153-9 revert (the exact-match short-circuit precedes the new gate) — a fine regression guard but with no discriminating power for the delta; if strengthened, give it two co-located adversaries (one exactly-named, one same-surname) under Fate and assert the exact-named is seated AND the skip span is absent. Affects `tests/server/dispatch/test_153_9_fate_other_seating.py`. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

5 deviations

- **New dedicated test file instead of extending the two named files**
  - Rationale: `test_opponent_roster_resolution.py` is WWN-fixture-scoped (108-2) and `test_fate_opponent_seating.py` tests exchange-time attacks in `fate_conflict.py`, not instantiation-time seating. The Fate seating contract is a distinct concern with a different fixture strategy (live Fate pack); a focused file is more discoverable and keeps the WWN/Fate fixtures uncoupled.
  - Severity: minor
- **Tests drive the live `pulp_noir` content pack (skipif-guarded), not a synthetic fixture**
  - Rationale: there is NO `ruleset: fate` fixture pack anywhere under `tests/fixtures/` (the `spaghetti_western` fixture is `ruleset: dial`), and the full Fate seating path needs a valid `fate:` config block to complete without crashing. Authoring a minimal Fate fixture in RED is high-risk; the assertions here are structural seating logic (named-Other vs conscripted-Other), not content-detail-dependent, so live-content drift cannot turn them red.
  - Severity: minor
  - Forward impact: if a minimal Fate fixture pack lands later, these tests should migrate to it (remove the skipif)
- **No test for the "antagonist already in `snapshot.encounter.actors`" sub-case of AC-2**
  - Rationale: `instantiate_encounter_from_trigger` returns `None` when an unresolved encounter already exists (line 1244), so the "already-active encounter" sub-case is unreachable through this seam — testing it here would assert on a no-op. The reachable, production-real path is the narrator-named threat at instantiation, which is what manifested in the playtest.
  - Severity: minor
  - Forward impact: if Dev finds a separate re-seating path for an already-active encounter, that path needs its own coverage
- **Implemented a minimal Fate-binding decline gate, not a new "scene-active antagonist marker"**
  - Rationale: the reproduced defect (TEA Improvement finding) is narrower than the story's root-cause framing — the 108-2 reconciliation is category-gated, not Fate-gated, so under Fate it conscripts an ambient adversary. Declining conscription under a Fate binding (mirroring the 150-2 non-combat decline) is the minimal correct fix and matches AC-4 ("the fallback applies only for non-Fate confrontations"). A new antagonist marker is unnecessary scope. The router-named threat IS the scene-active antagonist — once conscription is declined, it is seated directly.
  - Severity: minor
  - Forward impact: none — no new model field; the seating contract is unchanged for non-Fate packs
- **Fate decline applies to ALL categories, subsuming the category gate (answers TEA's open Question)**
  - Rationale: "Bind the Ruleset" (ADR-143/144) — a Fate conflict never resolves on bound-creature hp regardless of category, so there is never a bound-hp value to preserve. A single Fate gate is the cleaner invariant than per-category special-casing.
  - Severity: minor

## Design Deviations

### TEA (test design)
- **New dedicated test file instead of extending the two named files**
  - Spec source: context-story-153-9.md, "Candidate Implementation Files → Tests"
  - Spec text: "extend `test_opponent_roster_resolution.py` with a Fate-specific case; verify `test_fate_opponent_seating.py`"
  - Implementation: added `tests/server/dispatch/test_153_9_fate_other_seating.py`; left the two named files untouched
  - Rationale: `test_opponent_roster_resolution.py` is WWN-fixture-scoped (108-2) and `test_fate_opponent_seating.py` tests exchange-time attacks in `fate_conflict.py`, not instantiation-time seating. The Fate seating contract is a distinct concern with a different fixture strategy (live Fate pack); a focused file is more discoverable and keeps the WWN/Fate fixtures uncoupled.
  - Severity: minor
  - Forward impact: none
- **Tests drive the live `pulp_noir` content pack (skipif-guarded), not a synthetic fixture**
  - Spec source: story 96-1 doctrine (server tests should not couple to live content packs)
  - Spec text: "validators validate content; tests test fixtures"
  - Implementation: `instantiate_encounter_from_trigger` is driven with the real `pulp_noir` Fate pack via `find_pack_path`, guarded by `pytest.mark.skipif` when content is absent — the same pattern as `tests/integration/test_121_2_pulp_noir_fate_migration.py`
  - Rationale: there is NO `ruleset: fate` fixture pack anywhere under `tests/fixtures/` (the `spaghetti_western` fixture is `ruleset: dial`), and the full Fate seating path needs a valid `fate:` config block to complete without crashing. Authoring a minimal Fate fixture in RED is high-risk; the assertions here are structural seating logic (named-Other vs conscripted-Other), not content-detail-dependent, so live-content drift cannot turn them red.
  - Severity: minor
  - Forward impact: if a minimal Fate fixture pack lands later, these tests should migrate to it (remove the skipif)
- **No test for the "antagonist already in `snapshot.encounter.actors`" sub-case of AC-2**
  - Spec source: context-story-153-9.md, AC-2
  - Spec text: "a name that appears in `snapshot.encounter.actors` if an encounter is already active"
  - Implementation: only the "narrator-named antagonist + co-located same-surname roster NPC" path is tested (via `materialized_threat`)
  - Rationale: `instantiate_encounter_from_trigger` returns `None` when an unresolved encounter already exists (line 1244), so the "already-active encounter" sub-case is unreachable through this seam — testing it here would assert on a no-op. The reachable, production-real path is the narrator-named threat at instantiation, which is what manifested in the playtest.
  - Severity: minor
  - Forward impact: if Dev finds a separate re-seating path for an already-active encounter, that path needs its own coverage

### Dev (implementation)
- **Implemented a minimal Fate-binding decline gate, not a new "scene-active antagonist marker"**
  - Spec source: context-story-153-9.md, "Root Cause"
  - Spec text: "The seating logic does not have a way to **mark which NPC is the scene-active antagonist** for THIS conflict."
  - Implementation: extended the existing 150-2 decline gate in `_resolve_opponent_from_roster` to `if confrontation_category != "combat" or is_fate:` (passing a new `is_fate` param), instead of adding a scene-active-antagonist marker to the encounter/snapshot model.
  - Rationale: the reproduced defect (TEA Improvement finding) is narrower than the story's root-cause framing — the 108-2 reconciliation is category-gated, not Fate-gated, so under Fate it conscripts an ambient adversary. Declining conscription under a Fate binding (mirroring the 150-2 non-combat decline) is the minimal correct fix and matches AC-4 ("the fallback applies only for non-Fate confrontations"). A new antagonist marker is unnecessary scope. The router-named threat IS the scene-active antagonist — once conscription is declined, it is seated directly.
  - Severity: minor
  - Forward impact: none — no new model field; the seating contract is unchanged for non-Fate packs
- **Fate decline applies to ALL categories, subsuming the category gate (answers TEA's open Question)**
  - Spec source: session `## Delivery Findings` → TEA Question
  - Spec text: "Under Fate, should the 108-2 reconciliation be declined for ALL categories (combat + non-combat)?"
  - Implementation: yes — under a Fate binding the combined gate `category != "combat" or is_fate` declines for every category (non-combat via the category clause, combat via `is_fate`). The decline span's `reason` attr reports `fate_binding` whenever `is_fate`, so the GM panel distinguishes the Fate decline from the non-combat decline.
  - Rationale: "Bind the Ruleset" (ADR-143/144) — a Fate conflict never resolves on bound-creature hp regardless of category, so there is never a bound-hp value to preserve. A single Fate gate is the cleaner invariant than per-category special-casing.
  - Severity: minor
  - Forward impact: none

### Reviewer (audit)
- **TEA #1 (new dedicated test file)** → ✓ ACCEPTED by Reviewer: sound — `test_opponent_roster_resolution.py` is WWN-fixture-scoped and `test_fate_opponent_seating.py` covers exchange-time attacks; a dedicated file keeps the Fate seating contract and its live-pack fixture strategy uncoupled and discoverable.
- **TEA #2 (live `pulp_noir` pack via skipif)** → ✓ ACCEPTED by Reviewer: no `ruleset: fate` fixture pack exists; the `test_121_2` precedent is established; assertions are structural seating logic, not content-detail-dependent, so live-content drift cannot redden them. The skipif carries a reason (lang-review #6 compliant).
- **TEA #3 (no test for the `encounter.actors` sub-case of AC-2)** → ✓ ACCEPTED by Reviewer: `instantiate_encounter_from_trigger` returns `None` when an unresolved encounter exists (`:1244`), so that sub-case is unreachable through this seam — testing it would assert on a no-op. The reachable narrator-named path is the one that manifested in playtest.
- **Dev #1 (minimal Fate-decline gate, not a scene-active-antagonist marker)** → ✓ ACCEPTED by Reviewer: the reproduced defect is narrower than the story's root-cause framing; declining conscription under the Fate binding (mirroring 150-2) is the minimal correct fix and matches AC-4. A new model field would be unjustified scope.
- **Dev #2 (Fate decline applies to ALL categories)** → ✓ ACCEPTED by Reviewer: correct per "Bind the Ruleset" — a Fate conflict never uses bound-creature hp regardless of category, so the single Fate gate subsuming the category gate is the cleaner invariant. Answers TEA's open Question; the `reason="fate_binding"` attr keeps the two decline paths legible.

_No undocumented deviations found — the production change matches the spec/ACs as logged._