---
story_id: "158-28"
jira_key: ""
epic: "158"
workflow: "tdd"
---
# Story 158-28: WWN combat is narration-only — confrontation never seats, narrator confabulates kills with zero mechanical backing (IntentRouter combat-verb routing + opponent seater)

## Story Details
- **ID:** 158-28
- **Jira Key:** (none — Jira disabled)
- **Workflow:** tdd
- **Stack Parent:** none
- **Priority:** P1
- **Points:** 5
- **Type:** bug
- **Repository:** server
- **Branch:** feat/158-28-wwn-combat-seats

## Branch Strategy
**Branch Strategy:** gitflow (feat/158-28-wwn-combat-seats)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-25T22:46:16Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-25T20:45:30Z | 2026-06-25T20:46:55Z | 1m 25s |
| red | 2026-06-25T20:46:55Z | 2026-06-25T22:17:48Z | 1h 30m |
| green | 2026-06-25T22:17:48Z | 2026-06-25T22:38:51Z | 21m 3s |
| review | 2026-06-25T22:38:51Z | 2026-06-25T22:46:16Z | 7m 25s |
| finish | 2026-06-25T22:46:16Z | - | - |

## Sm Assessment

**Setup complete — ready for RED phase (Igor/TEA).**

**What this story is:** A P1 playtest finding. Post-#1072 the WWN combat crash is gone, but combat is now *narration-only*: a player attacks, the narrator narrates a KILL, while ground truth shows `encounter=null`, `total_beats_fired=0`, the creature untouched, and no Other seated. Plus a weapon-confab symptom (narrator invents a "mace" against a long-blade kit). Reproduced cleanly on two unrelated worlds (beneath_sunden + barsoom/helium, plain non-region world), which **rules out** literary-phrasing brittleness and the zone/location-reconcile theory from 158-1/158-2. The defect is fundamental to the WWN combat dispatch/seater path: the router classifies and the encounter subsystem is reached once, but no `ENCOUNTER_STARTED` is ever created.

**Doctrine guardrail (load-bearing — flag for Igor and Ponder):** This is ADR-143 ground. The real fix is the combat-**seats** path so a confrontation seats and the **WN ruleset owns resolution**. Do **not** balance, tune, convert, or gate native mechanics (dials, beats, edge/fleeting-tags, auto-reprisal) to "make them work with" WWN — that's the dead end we keep re-walking. Binding the ruleset *is* the balance decision.

**Lie-detector ACs (the OTEL must prove the fix, not the prose):**
1. After an attack, `encounter != null` (a confrontation actually seats).
2. Beats fire (`total_beats_fired > 0`).
3. Creature HP changes via mechanical resolution (roll/beat/encounter — not a narrator apply-path mutation).
4. Weapon is sourced from the PC's inventory, not confabulated.
5. `max_turns` exhaustion degrades loudly (ADR-006), not crash+wedge.

**Routing notes:**
- Single repo: **server** only. Branch `feat/158-28-wwn-combat-seats` off `develop` (gitflow — do NOT target main).
- Relevant ADRs surfaced in context: ADR-143, ADR-116/139 (confrontation integrity, the mechanically-capable Other, dispatch applicability gate), ADR-113 (IntentRouter spine), ADR-123 (mechanical-engagement pipeline), ADR-006 (graceful degradation).
- Every subsystem decision on the seating path MUST emit OTEL watcher events — the GM panel is how we tell the seater fired versus Claude winging it. Tests should assert on those spans.

**Assessment:** Well-scoped, well-evidenced, single-repo. No blockers. Handing to Igor for RED.

## TEA Assessment

**Tests Required:** Yes
**Status:** RED (2 failing + 1 regression guard passing) — verified by testing-runner (RUN_ID 158-28-tea-red).

**Test File:**
- `tests/agents/test_wwn_combat_seats_158_28.py` — deterministic, content-independent (synthetic WWN pack), drives the **production** `run_dispatch_bank` → `run_confrontation_dispatch`.

### ⚠️ PIVOTAL FINDING — the story's root-cause hypothesis was wrong (reproduced + proven)

I followed Carrot's "reproduce first" steer. The reproduction **overturns the story's premise**. The opponent seater is **NOT broken**.

**What I proved (one authorized live IntentRouter probe + deterministic repros against the real `heavy_metal/barsoom` pack):**
1. Given a `confrontation` dispatch naming the Banth + a statted player, `instantiate_encounter_from_trigger` **seats cleanly** — `encounter.confrontation_initiated` + `encounter.initiative_rolled` fire, the Other is minted, HP is reachable. The seater is whole.
2. **The real bug is a router→registry vocabulary mismatch.** The LIVE router emits `subsystem="combat"` for a **blunt** verb ("I attack the banth with my long-sword") — but `combat` is **not a registered subsystem** (the engager is `confrontation`; "combat" is only a confrontation *type*). `run_dispatch_bank` finds no handler, logs `subsystems.unknown subsystem=combat`, and **silently continues** → nothing seats → the narrator confabulates a kill (a **No-Silent-Fallbacks** violation). **Literary** phrasing ("I lunge … driving my long-sword at its throat") happens to emit `subsystem="confrontation"` and seats fine. Live probe output is recorded below.

**Fix has two complementary halves (Ponder + possibly Leonard to weigh in):**
- **Deterministic (this suite drives it):** the bank must not silently drop a combat classification into a phantom kill — route `combat`→the confrontation engine (or otherwise make a combat-classified action seat). This is the bank-robustness safety net.
- **Live-eval (NOT deterministically unit-testable — the suite stubs the router by design):** tighten the router prompt so blunt combat verbs emit `subsystem="confrontation"` with `params.type="combat"`, never `subsystem="combat"`. Validate via the opt-in `SIDEQUEST_VERIFY_*` live path + playtest.

### Scope correction — 4 of the 5 story-proposed OTEL spans are REDUNDANT (one mechanism per problem)

Per Carrot's "reuse existing spans" steer, I verified the existing observability vocabulary. The story context's "Lie-Detector OTEL Assertions" proposed 5 new spans; the codebase already has the mechanism for four:

| Story-proposed span | Already exists — reuse | Status |
|---|---|---|
| `dispatch_engagement.confrontation.seated` | `encounter.confrontation_initiated` | redundant |
| `dispatch_engagement.confrontation.beats_fired` | `encounter.beat_applied` | redundant |
| `confrontation.hp_change` | `state_patch.hp` | redundant |
| `narrator.max_turns_exceeded` (AC5) | `narrator.tool_loop` (`loop_exceeded=True`) + typed `AnthropicSdkLoopExceeded` | redundant — AC5 already degrades loudly (the 2026-06-22 auth-misdirection was already fixed) |
| `narrator.combat_weapon_extracted` (AC4) | weapon already grounded **mechanically** via `combat_rules.resolve_weapon_damage_spec` + `dice.py` lie-detector spans (1543/1558) | mechanical grounding done; narrator-PROSE confab ("mace" vs long-blade) is a **narration-grounding** concern = live-eval |

**Net:** the deterministic story collapses to **AC1 (make blunt attacks seat)** + the bank-robustness safety net. AC2/AC3 already resolve once seated (existing WN round + existing spans — the guard pins the precondition). AC4/AC5 are already handled or are live-eval. **No new spans authored** (would violate `one mechanism per problem`).

### Tests written

| Test | AC | RED? | Pins |
|---|---|---|---|
| `test_blunt_attack_combat_classification_seats_a_confrontation` | AC1 | **RED** (AssertionError: encounter stays None) | the bug — `subsystem="combat"` must seat, not be silently dropped |
| `test_confrontation_classification_seats_cleanly_regression_guard` | AC1/AC3 | PASS (guard) | the seater works + the Other's HP is reachable (AC2/AC3 precondition) |
| `test_combat_seat_with_unresolvable_initiative_degrades_loudly` | AC5/ADR-006 | **RED** (uncaught ValueError) | a seat whose initiative can't resolve must degrade loudly, not raise an uncaught exception from the handler |

### Rule Coverage

| Rule (CLAUDE.md / SOUL) | Test | Status |
|---|---|---|
| No Silent Fallbacks (bank must not drop a combat classification into a phantom kill) | `test_blunt_attack…seats` (asserts no `unknown_subsystem` decision + a seat) | RED |
| OTEL lie-detector (drive flow, assert span) — reuse existing spans | guard asserts `encounter.confrontation_initiated` + `encounter.initiative_rolled` fire | PASS |
| Every Test Suite Needs a Wiring Test (no source-text grep) | all tests drive the production `run_dispatch_bank`; span assertions, not `read_text()` | ✓ |
| Bind the Ruleset, Don't Balance It (ADR-143) | tests pin the WN seat/round; no native dial tuning introduced | ✓ |
| Graceful Degradation (ADR-006) | `test_combat_seat…degrades_loudly` | RED |

**Self-check:** No vacuous assertions; every test asserts a load-bearing condition. No `assert True` / `let _ =` / always-None checks.

### Live router probe — evidence (authorized one-shot, subscription pool, no PAYG key)

```
ACTION 'I attack the banth with my long-sword.'         → subsystems=['combat']         SEATS=False  (the bug)
ACTION 'I lunge at the banth, driving my long-sword …'  → subsystems=['confrontation']  conf=0.95    SEATS=True
```
Registered subsystems: `[confrontation, course, distinctive_detail_hint, dogfight, environment_clock, equip, fate_action, magic_working, movement, npc_agency, quest_offer, reflect_absence, scenario_clue, witnessed_act]` — **`combat` is absent.**

**Handoff:** To **Ponder Stibbons (Dev)** for GREEN. Primary fix = the bank-robustness seat (deterministic, this suite drives it); complementary fix = router-prompt tightening (live-eval). See Delivery Findings for the secondary defects (bestiary stub-stats; the bank's silent unknown-subsystem drop).

## Dev Assessment

**Implementation Complete:** Yes
**Tests:** 3/3 passing (GREEN). Full server suite: 12838 passed, 1695 skipped, **49 pre-existing failures** (unrelated — confirmed by stashing this fix and re-running: identical 49; spell-cast/`monster_manual_inject` bestiary bleed, 158-33 territory).
**Branch:** `feat/158-28-wwn-combat-seats` (pushed, commit `fdd60282`).

**Files Changed:**
- `sidequest/agents/subsystems/__init__.py` — `run_dispatch_bank` now normalizes a confrontation-type-as-subsystem (`combat`/`negotiation`/`chase`) to the registered `confrontation` engager *before* dispatch (helper `_normalize_confrontation_type_subsystems`), so a misclassified blunt attack seats instead of being silently dropped. Loud: logs each repair + stamps `normalized_from` on the existing `intent_router.subsystem` span + the decision audit. Only rewrites an UNREGISTERED subsystem matching a pack confrontation type (never hijacks a real subsystem).
- `sidequest/server/dispatch/encounter_lifecycle.py` — new typed `InitiativeUnresolvableError(ValueError)`; the missing-DEX initiative guard now raises it (with a loud `_log.warning`) instead of a bare `ValueError`. The player-NOT-FOUND guard stays a fail-loud `ValueError` (genuine roster defect, per its existing comment).
- `sidequest/agents/subsystems/confrontation.py` — `run_confrontation_dispatch` catches `InitiativeUnresolvableError` and degrades loudly (ADR-006): keeps the seat (set before the initiative roll), returns `error="initiative_unresolvable"` the GM panel sees, no turn wedge.
- `sidequest/agents/intent_router.py` — prompt clarification: combat/negotiation/chase are confrontation TYPES (`params.type`), never the subsystem key (root-cause complement; live-eval validated).

**How the fix maps to the ACs:**
- **AC1 (seat):** ✅ deterministic — blunt `subsystem="combat"` now routes to the confrontation engine and seats (`encounter.confrontation_initiated` fires).
- **AC2/AC3 (beats/HP):** ✅ once seated, the existing WN round resolves beats + ablates HP via the already-tested path (`encounter.beat_applied` / `state_patch.hp`); the guard pins the precondition.
- **AC4 (weapon):** mechanical grounding already exists; narrator-prose grounding deferred to live-eval (Delivery Finding).
- **AC5 (degrade loudly):** ✅ max_turns already degrades via `narrator.tool_loop`+`AnthropicSdkLoopExceeded`; the reproduced initiative-crash path now degrades loudly via the typed error.

**Self-review:** Wired into the production `run_dispatch_bank` hot path (not isolated); follows the existing typed-exception-degradation pattern (`NoOpponentAvailableError`/`SealedLetterArityError`); No Silent Fallbacks honored (normalization is loud + observable); ADR-143 honored (no native mechanic tuned against WWN — the seater/WN round are unchanged). Ruff clean on all changed files.

**Handoff:** To **Granny Weatherwax (Reviewer)** for review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (3/3 tests GREEN, ruff clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | N/A — Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 (1 med, 1 med, 1 low) | confirmed 0 blocking, 2 downgraded→LOW (captured as findings), 1 dismissed (pre-existing/out-of-scope) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | N/A — Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | N/A — Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | N/A — Disabled via settings |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | N/A — Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | N/A — Disabled via settings |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 0 confirmed blocking, 2 LOW (non-blocking, captured as Delivery Findings), 1 dismissed (with rationale)

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** player action → IntentRouter (Haiku) → `DispatchPackage` (subsystem=`combat`, params.type=`combat`) → `run_dispatch_bank` → **`_normalize_confrontation_type_subsystems`** rewrites subsystem→`confrontation` (carrying params.type) → `_REGISTRY["confrontation"]` → `run_confrontation_dispatch` → `instantiate_encounter_from_trigger` seats the encounter. Safe because the rewrite is gated on an UNREGISTERED subsystem matching a **pack-authored** confrontation type (closed set), the LLM cannot redirect a registered subsystem, and the production caller passes the real pack (`intent_router_pass.py:996`).

**Pattern observed:** typed-`ValueError`-subclass graceful degradation — `InitiativeUnresolvableError` mirrors the existing `NoOpponentAvailableError`/`SealedLetterArityError` precedent (`confrontation.py:175-191`). Consistent with the codebase.

**Error handling:** the new catch (`confrontation.py:183`) logs at `warning` and returns `SubsystemOutput(data={"error":"initiative_unresolvable"})`; the bank stamps the error code onto the `intent_router.subsystem` span (`__init__.py:405-408`). Seat is preserved (set at `encounter_lifecycle.py:2083`, before the initiative roll at ~2164); no turn wedge (ADR-006).

### Findings (tagged by source)

- `[SILENT]` **LOW (non-blocking):** `_normalize_confrontation_type_subsystems` no-ops when `context["pack"]` is unavailable (pack=None / no confrontation defs). Mitigant: in production the bank is **always** called with `pack` in context (verified `intent_router_pass.py:996`; the dispatch bank runs mid-turn, after world binding), and the unknown-subsystem fall-through **already logs** `subsystems.unknown subsystem=%s` — so the drop is not fully silent. Downgraded from medium; captured as a Delivery Finding (a DEBUG log distinguishing "no pack" from "no match" would aid future debugging).
- `[SILENT]` **LOW (non-blocking):** a degraded (no-initiative) WN seat is hard to distinguish from a legitimate Fate (no-initiative) seat on the GM panel. Mitigant: the silent-failure-hunter itself confirmed the seat is **coherent** (`initiative_preamble()` returns None for empty initiative → no broken prompt), and the degradation **is** observable via the `error="initiative_unresolvable"` span attribute + two `warning` logs. The trigger (a statless player) is near-impossible post-chargen. A dedicated initiative-failure span is a nice-to-have; captured as a Delivery Finding.
- `[SILENT]` **DISMISSED:** `encounter_lifecycle.py:719` empty-initiative silent `return`. Rationale: explicitly **pre-existing** (line unchanged by this diff) and **correct-by-design** — the docstring documents the empty return as the no-op for rulesets with no ordering. Not introduced here.
- `[SEC]` **VERIFIED clean:** no injection/escalation/PII-leak — the rewrite cannot reach a non-`confrontation` handler (the `_REGISTRY` gate), `model_copy` preserves the VisibilityTag firewall (ADR-104/105), and logs carry only game nouns (stat KEY names, not values). Evidence: security subagent + `__init__.py:288-298`.
- `[EDGE]` **(disabled subagent — assessed by Reviewer):** `setdefault("type", d.subsystem)` prefers an existing `params.type` over the subsystem-name trigger. For the real bug both are `combat` (no effect). For contradictory LLM output (subsystem=`combat`, params.type=`negotiation`) it would seat a negotiation — an unlikely self-contradictory input, validated against pack cdefs at seating. LOW, non-blocking.
- `[TEST]` **(disabled subagent — assessed by Reviewer):** the 3 story tests assert load-bearing conditions (seat != None, opponent seated, `encounter.confrontation_initiated` fires, no `unknown_subsystem` decision, no uncaught raise, error outcome). No vacuous assertions. The regression guard correctly pins that the seater is whole.
- `[TYPE]` **(disabled subagent — assessed by Reviewer):** `InitiativeUnresolvableError(ValueError)` is a properly typed domain error (not stringly-typed); `_confrontation_types(pack: Any)` uses `Any` but is a private helper (exempt per python checklist #3).
- `[DOC]` **(disabled subagent — assessed by Reviewer):** docstrings on both new helpers + the exception class are accurate and cite the story; the inline comments at the call sites are correct.
- `[SIMPLE]` **(disabled subagent — assessed by Reviewer):** no over-engineering — the normalization is a single bounded pass; no new spans authored (reuses existing observability per one-mechanism-per-problem).
- `[RULE]` **(disabled subagent — assessed by Reviewer):** see Rule Compliance below — all 13 python-checklist rules pass.

### Rule Compliance (python lang-review checklist + SOUL/CLAUDE.md)

- **#1 Silent exception swallowing** — PASS. `except InitiativeUnresolvableError` is specific, logged at warning, returns an error outcome (not swallowed). No bare except.
- **#2 Mutable defaults** — PASS. No mutable default args in the new helpers.
- **#3 Type annotations at boundaries** — PASS. `_normalize_confrontation_type_subsystems` fully annotated; `_confrontation_types(pack: Any)` is a private helper (exempt).
- **#4 Logging coverage/correctness** — PASS. Error paths log at `warning` (client/LLM-side slip, not a 5xx) using lazy `%s` form; no secrets/PII (stat KEY names only).
- **#5 Path handling** — N/A (no paths).
- **#6 Test quality** — PASS. Meaningful assertions, no skips, no vacuous truthy checks.
- **#7 Resource leaks** — N/A.
- **#8 Unsafe deserialization** — N/A (no pickle/eval/yaml.load/subprocess).
- **#9 Async pitfalls** — PASS. The normalization is a sync pure transform; no blocking calls; no missing awaits.
- **#10 Import hygiene** — PASS. Explicit sorted import of `InitiativeUnresolvableError`; no star imports/cycles introduced.
- **#11 Input validation at boundaries** — PASS. LLM router output is constrained against the pack's closed confrontation-type set; cannot reach a non-confrontation handler.
- **#12 Dependency hygiene** — N/A (no dep changes).
- **#13 Fix-introduced regressions** — PASS. The catch is specific (not broad); the typed exception is correct; full-suite confirmed no NEW failures (49 pre-existing, stash-verified).
- **SOUL "Bind the Ruleset" / ADR-143** — PASS. The fix is pure routing + a degradation guard; the seater, WN round, beats, HP, and initiative math are untouched. No native mechanic was tuned against WWN.
- **OTEL Observability Principle** — PASS. The normalization decision is recorded (`normalized_from` on the existing `intent_router.subsystem` span + decision audit + warning log); the degradation is recorded (error code on the span + logs).

### Devil's Advocate

Let me argue this code is broken. **First attack: the fix doesn't fire in production.** The normalization depends on `context["pack"]` — if the production caller omitted it, the whole fix is a no-op and the test passes while the bug ships. I chased this down: `intent_router_pass.py:992-996` passes `"pack": pack`, and `pack` is the live bound `GenrePack` (used one line earlier by `inject_environment_clock`). The fix is wired. Refuted. **Second attack: a malicious/confused LLM weaponizes the rewrite.** Could a crafted router output route something dangerous to `confrontation`, or hijack another engine? No — the triple gate (`!= confrontation` AND `not in _REGISTRY` AND `in pack types`) means the only reachable target is `confrontation`, and a registered subsystem name can never be rewritten. The worst case is a self-contradictory `subsystem=combat`/`params.type=negotiation` seating a negotiation — odd, but validated against pack cdefs and harmless. Refuted (noted LOW). **Third attack: the degradation corrupts state.** A statless player seats combat, initiative raises, and we keep a half-seated encounter — does the narrator choke or the WN round explode? The silent-failure-hunter verified `initiative_preamble()` returns None for empty initiative, so no `[INITIATIVE ORDER]` garbage reaches the prompt; the seat is coherent and strictly better than the prior uncaught `ValueError` that wedged the turn. The trigger is near-impossible post-chargen anyway. Refuted (noted LOW). **Fourth attack: the prompt change regresses the router.** Four new prose lines could confuse classification of non-combat actions. But no deterministic test asserts on prompt text (the suite stubs the router), the lines are additive and scoped to the confrontation block, and the bank normalization guarantees correctness even if the prompt does nothing. The residual risk is live-eval, which Dev logged as a deviation. **Conclusion:** the genuine residue is two LOW observability refinements and a live-eval prompt change — nothing that corrupts state, leaks data, or wedges a turn. The fix is correct and complete for its deterministic scope.

**Handoff:** To Captain Carrot Ironfoundersson (SM) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Conflict** (non-blocking): The story context's "Lie-Detector OTEL Assertions (Required for Test)" proposes 5 new spans; 4 duplicate existing observability (`encounter.confrontation_initiated`, `encounter.beat_applied`, `state_patch.hp`, `narrator.tool_loop`+`AnthropicSdkLoopExceeded`). Affects `sprint/context/context-story-158-28.md` (the OTEL section should reference the existing spans, not new ones — `one mechanism per problem`). *Found by TEA during test design.*
- **Gap** (non-blocking): The real "never-seats" root cause is the router emitting an **unregistered** `subsystem="combat"` (vs the registered `confrontation`) for blunt combat verbs; `run_dispatch_bank` silently drops unknown subsystems. Affects `sidequest/agents/intent_router.py` (prompt: emit `confrontation` + `params.type=combat`) **and** `sidequest/agents/subsystems/__init__.py` (the unknown-subsystem path must not silently degrade a combat classification to narration-only — No Silent Fallbacks). *Found by TEA during test design.*
- **Improvement** (non-blocking): A combat seat for a player whose stat block lacks DEX raises an uncaught `ValueError` from `_roll_initiative` inside `instantiate_encounter_from_trigger`; `run_confrontation_dispatch` catches only `NoOpponentAvailableError`/`SealedLetterArityError` (the bank's generic catch is the only net, and it leaves a half-seated encounter with no initiative). Affects `sidequest/agents/subsystems/confrontation.py` / `sidequest/server/dispatch/encounter_lifecycle.py` (degrade loudly per ADR-006 with a combat-specific error outcome). *Found by TEA during test design.*
- **Improvement** (non-blocking): The Banth seats with the cdef's generic `opponent_default_stats` (HP 10 / AC 12), **ignoring** its richer bestiary stats (HP 27 / AC 14, atk +6, 2d6) — the apex predator fights like a generic mook (Genre-Truth / Diamonds & Coal). Likely ADR-059/108-2 territory, probably out of this story's scope. Affects the bestiary→seater stat binding in `sidequest/server/dispatch/encounter_lifecycle.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): AC4's narrator-PROSE weapon grounding is not implemented — the weapon is grounded mechanically (`combat_rules.resolve_weapon_damage_spec`) but the narrator can still confabulate a weapon name in prose ("mace" vs long-blade). Affects the narrator prompt/grounding path; validate via live eval + playtest. *Found by Dev during implementation.*
- **Improvement** (non-blocking): The router-prompt clarification (combat/negotiation/chase are TYPES, not subsystem keys) is the root-cause complement to the bank normalization but is NOT deterministically verifiable (the test suite stubs the router). Affects `sidequest/agents/intent_router.py`; needs an opt-in live-router check (`SIDEQUEST_VERIFY_*`) + playtest to confirm blunt verbs now emit `subsystem="confrontation"`. *Found by Dev during implementation.*
- **Improvement** (non-blocking): Pre-existing — the full server suite has **49 failures unrelated to this story** (spell-cast `casts_remaining` not decrementing / `monster_manual_inject.py` `effective_bestiary()` empty-tuple), confirmed by stashing this fix and re-running (same 49). Tracked as bestiary/cast cross-world bleed (158-33 territory). Affects `sidequest/.../monster_manual_inject.py` + WWN cast apply path. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `_normalize_confrontation_type_subsystems` no-ops silently when `context["pack"]` is unavailable (pack=None / no confrontation defs) — distinct from "ran, found no match". In production the pack is always present, but a DEBUG log distinguishing the two cases would aid future debugging. Affects `sidequest/agents/subsystems/__init__.py` (`_normalize_confrontation_type_subsystems`). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): A degraded (no-initiative) WN combat seat is hard to distinguish from a legitimate Fate (no-initiative) seat on the GM panel — currently observable only via the `error="initiative_unresolvable"` span attribute + warning logs. A dedicated initiative-failure span (or reusing `encounter_initiative_rolled_span` with `error=True`) would sharpen the lie-detector. Low priority (the trigger — a statless player — is near-impossible post-chargen). Affects `sidequest/server/dispatch/encounter_lifecycle.py` / `sidequest/agents/subsystems/confrontation.py`. *Found by Reviewer during code review.*
- **Question** (non-blocking): AC4's narrator-PROSE weapon grounding remains open (mechanical grounding exists; the "mace vs long-blade" confab is live-eval). Worth a follow-up story to validate via the live-router path + playtest. Affects the narrator prompt/grounding path. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 2 findings (0 Gap, 1 Conflict, 0 Question, 1 Improvement)
**Blocking:** None

- **Conflict:** The story context's "Lie-Detector OTEL Assertions (Required for Test)" proposes 5 new spans; 4 duplicate existing observability (`encounter.confrontation_initiated`, `encounter.beat_applied`, `state_patch.hp`, `narrator.tool_loop`+`AnthropicSdkLoopExceeded`). Affects `sprint/context/context-story-158-28.md`.
- **Improvement:** `_normalize_confrontation_type_subsystems` no-ops silently when `context["pack"]` is unavailable (pack=None / no confrontation defs) — distinct from "ran, found no match". In production the pack is always present, but a DEBUG log distinguishing the two cases would aid future debugging. Affects `sidequest/agents/subsystems/__init__.py`.

### Downstream Effects

Cross-module impact: 2 findings across 2 modules

- **`sidequest/agents/subsystems`** — 1 finding
- **`sprint/context`** — 1 finding

### Deviation Justifications

7 deviations

- **Did not author the 5 story-proposed OTEL spans; reused existing spans**
  - Rationale: `one mechanism per problem` (load-bearing doctrine, enforced by `test_dispatch_engagement_spans.py`); confirmed by user direction 2026-06-25 ("reuse existing spans").
  - Severity: minor
  - Forward impact: Dev reuses existing spans; the context doc's OTEL section is stale (logged as a Conflict finding).
- **Anchored the core RED test at the dispatch-bank level, not the IntentRouter level**
  - Rationale: The deterministic suite stubs the router by design (`test_102_3_live_router_classification.py`); router classification is only validated by gated live tests. A deterministic test of the router would be a stub asserting against itself.
  - Severity: minor
  - Forward impact: Dev should pair the bank-robustness fix (deterministic) with a router-prompt fix validated by live eval + playtest.
- **No new deterministic behavioral test for AC2 (beats fire) / AC3 (HP delta)**
  - Rationale: Once AC1 routes blunt attacks to the seated path, AC2/AC3 resolve through the already-tested WN round; rebuilding the dice-throw round in this suite would duplicate existing coverage.
  - Severity: minor
  - Forward impact: If Dev's fix changes the WN-round entry, the existing WN-round tests cover the regression; none added here.
- **Implemented a router→registry normalization + handler degradation, NOT a seater rewrite**
  - Rationale: TEA's reproduction overturned the story's root-cause hypothesis — the seater is whole; the defect is the router emitting `subsystem="combat"` (unregistered) which the bank silently dropped.
  - Severity: minor
  - Forward impact: none — AC1 (an attack seats) is satisfied; the seater contract is unchanged.
- **Reused existing OTEL observability; authored no new spans**
  - Rationale: `one mechanism per problem`; 4 of 5 proposed spans duplicate existing observability (TEA Conflict finding + user steer).
  - Severity: minor
  - Forward impact: GM panel reads existing spans; context doc's OTEL section is stale (TEA Conflict finding stands).
- **Did not implement narrator weapon-prose grounding (AC4)**
  - Rationale: Scope — AC4's mechanical half exists; the prose-grounding half is live-eval and outside the deterministic GREEN this story drives. Logged as a Delivery Finding for a follow-up.
  - Severity: minor
  - Forward impact: AC4 prose-grounding remains open as a live-eval/playtest follow-up (Delivery Finding below).
- **Added a router-prompt clarification not driven by a failing deterministic test**
  - Rationale: Addresses the actual root cause (CLAUDE.md "do X, not Y"); low-risk and in the story's named scope. The bank normalization guarantees correctness regardless; the prompt reduces how often the normalization must fire.
  - Severity: minor
  - Forward impact: validate via the opt-in `SIDEQUEST_VERIFY_*` live router path + playtest.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Did not author the 5 story-proposed OTEL spans; reused existing spans**
  - Spec source: context-story-158-28.md, "Lie-Detector OTEL Assertions (Required for Test)"
  - Spec text: "1. dispatch_engagement.confrontation.seated … 5. narrator.max_turns_exceeded … (Required for Test)"
  - Implementation: Tests assert the EXISTING spans (`encounter.confrontation_initiated`, `encounter.initiative_rolled`); no new spans written. 4 of 5 proposed spans duplicate existing observability.
  - Rationale: `one mechanism per problem` (load-bearing doctrine, enforced by `test_dispatch_engagement_spans.py`); confirmed by user direction 2026-06-25 ("reuse existing spans").
  - Severity: minor
  - Forward impact: Dev reuses existing spans; the context doc's OTEL section is stale (logged as a Conflict finding).
- **Anchored the core RED test at the dispatch-bank level, not the IntentRouter level**
  - Spec source: context-story-158-28.md, AC-1 + Title ("IntentRouter combat-verb routing + opponent seater")
  - Spec text: "After an attack, encounter != null … A confrontation MUST be created/seated when the PC attacks a creature in a WWN world."
  - Implementation: The deterministic test feeds the EXACT live-router output (`subsystem="combat"`) through `run_dispatch_bank`; the router-classification half is left to opt-in live eval.
  - Rationale: The deterministic suite stubs the router by design (`test_102_3_live_router_classification.py`); router classification is only validated by gated live tests. A deterministic test of the router would be a stub asserting against itself.
  - Severity: minor
  - Forward impact: Dev should pair the bank-robustness fix (deterministic) with a router-prompt fix validated by live eval + playtest.
- **No new deterministic behavioral test for AC2 (beats fire) / AC3 (HP delta)**
  - Spec source: context-story-158-28.md, AC-2 + AC-3
  - Spec text: "Beats fire mechanically … total_beats_fired > 0 … Creature HP changes … delta must be non-zero."
  - Implementation: The regression guard pins the AC2/AC3 PRECONDITION (encounter seats + the Other's HP is reachable); full beat/HP resolution is already covered by existing WN-round tests (`test_wwn_caverns_dispatch.py` proves HP ablation via `state_patch.hp`).
  - Rationale: Once AC1 routes blunt attacks to the seated path, AC2/AC3 resolve through the already-tested WN round; rebuilding the dice-throw round in this suite would duplicate existing coverage.
  - Severity: minor
  - Forward impact: If Dev's fix changes the WN-round entry, the existing WN-round tests cover the regression; none added here.

### Dev (implementation)
- **Implemented a router→registry normalization + handler degradation, NOT a seater rewrite**
  - Spec source: context-story-158-28.md, "Technical Approach → Fix Strategy 1. Opponent Seater"
  - Spec text: "Wire the `opponent_seater` subsystem to SEAT a Confrontation when a combat intent is routed … Instantiate a Confrontation with the routed creature as the opponent."
  - Implementation: The seater already does this (Igor proved it). The fix is in `run_dispatch_bank` (normalize a confrontation-type subsystem name to the registered `confrontation` engager) + `run_confrontation_dispatch`/`encounter_lifecycle` (degrade loudly on unresolvable initiative). The seater was not touched.
  - Rationale: TEA's reproduction overturned the story's root-cause hypothesis — the seater is whole; the defect is the router emitting `subsystem="combat"` (unregistered) which the bank silently dropped.
  - Severity: minor
  - Forward impact: none — AC1 (an attack seats) is satisfied; the seater contract is unchanged.
- **Reused existing OTEL observability; authored no new spans**
  - Spec source: context-story-158-28.md, "Lie-Detector OTEL Assertions (Required for Test)"
  - Spec text: "1. dispatch_engagement.confrontation.seated … 5. narrator.max_turns_exceeded (new span or extended …)"
  - Implementation: The normalization stamps `normalized_from` on the existing `intent_router.subsystem` span; the seat fires the existing `encounter.confrontation_initiated`; the degradation surfaces `error="initiative_unresolvable"` via the existing bank sub-span error mechanism. No new span constants.
  - Rationale: `one mechanism per problem`; 4 of 5 proposed spans duplicate existing observability (TEA Conflict finding + user steer).
  - Severity: minor
  - Forward impact: GM panel reads existing spans; context doc's OTEL section is stale (TEA Conflict finding stands).
- **Did not implement narrator weapon-prose grounding (AC4)**
  - Spec source: context-story-158-28.md, AC-4 + "Fix Strategy 3. Narration Grounding"
  - Spec text: "Weapon MUST be extracted from PC inventory before narration, passed to the narrator as a constraint … Narrator sees the actual weapon name, not a free choice."
  - Implementation: Not implemented. The weapon is already grounded MECHANICALLY (`combat_rules.resolve_weapon_damage_spec` reads the equipped inventory weapon; `dice.py` lie-detector spans fire on a no-weapon strike). The narrator-PROSE confab ("mace" vs long-blade) is a narration-grounding concern validated by live eval + playtest, not deterministically.
  - Rationale: Scope — AC4's mechanical half exists; the prose-grounding half is live-eval and outside the deterministic GREEN this story drives. Logged as a Delivery Finding for a follow-up.
  - Severity: minor
  - Forward impact: AC4 prose-grounding remains open as a live-eval/playtest follow-up (Delivery Finding below).
- **Added a router-prompt clarification not driven by a failing deterministic test**
  - Spec source: context-story-158-28.md, Title ("IntentRouter combat-verb routing")
  - Spec text: the story names IntentRouter combat-verb routing as a fix target.
  - Implementation: Added one targeted sentence to the confrontation prompt block (combat/negotiation/chase are TYPES, never the subsystem key). Not covered by a deterministic test (the suite stubs the router by design).
  - Rationale: Addresses the actual root cause (CLAUDE.md "do X, not Y"); low-risk and in the story's named scope. The bank normalization guarantees correctness regardless; the prompt reduces how often the normalization must fire.
  - Severity: minor
  - Forward impact: validate via the opt-in `SIDEQUEST_VERIFY_*` live router path + playtest.

### Reviewer (audit)
All seven logged deviations reviewed:
- **TEA — "Did not author the 5 story-proposed OTEL spans; reused existing spans"** → ✓ ACCEPTED: 4 of 5 proposed spans verifiably duplicate existing observability; reuse is the correct `one-mechanism-per-problem` call (user-endorsed).
- **TEA — "Anchored the core RED test at the dispatch-bank level, not the IntentRouter level"** → ✓ ACCEPTED: the deterministic suite stubs the router by design; the bank-level anchor (feeding the exact live-router output) is the only honest deterministic seam.
- **TEA — "No new deterministic behavioral test for AC2/AC3"** → ✓ ACCEPTED: AC2/AC3 resolve through the already-tested WN round once seated; the guard pins the precondition (opponent HP reachable). Rebuilding the dice round would duplicate coverage.
- **Dev — "Implemented a router→registry normalization, NOT a seater rewrite"** → ✓ ACCEPTED: TEA's reproduction proved the seater is whole; the routing fix is the correct root-cause target (and I verified it is production-wired).
- **Dev — "Reused existing OTEL observability; authored no new spans"** → ✓ ACCEPTED: the normalization + degradation are both observable via existing spans/error codes; no redundant span sprawl.
- **Dev — "Did not implement narrator weapon-prose grounding (AC4)"** → ✓ ACCEPTED (with follow-up): mechanical weapon grounding already exists; the prose-confab half is genuinely live-eval and out of deterministic scope. Logged as a Reviewer Question finding for a follow-up story.
- **Dev — "Added a router-prompt clarification not driven by a failing deterministic test"** → ✓ ACCEPTED: in the story's named scope (IntentRouter combat-verb routing), low-risk and additive, and the bank normalization guarantees correctness independent of it. Live-eval validation is the right path.

No undocumented deviations found — TEA and Dev logged every divergence I could identify in the diff.