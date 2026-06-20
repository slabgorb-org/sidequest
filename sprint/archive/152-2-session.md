---
story_id: "152-2"
jira_key: null
epic: "152"
workflow: "tdd"
---
# Story 152-2: [ENGINE] Synthesize the cast WN action (cast_spell) so casting resolves on a zero-beat WWN combat def — route the synthesized cast to the existing wwn cast spine

## Story Details
- **ID:** 152-2
- **Jira Key:** (no Jira integration)
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 5
- **Priority:** p1
- **Repos:** server
- **Type:** bug

## Acceptance Criteria
- A cast_spell commit (with spell_id) on a zero-beat WWN hp_depletion combat def resolves through the wwn cast spine (wwn.spell.cast span), not DiceDispatchError 'unknown beat_id'.
- Cast outcome is independent of the d20 face; a killing cast resolves the encounter and suppresses reprisal; a no-casts-remaining cast is refused-but-recorded (refused=True), not a generic stat throw (test_dice_path_spell_cast_102_2).
- The dice path and the apply_beat path reach the SAME cast spine (parity test green); narration_apply no longer raises ValueError 'cast_spell' on a zero-beat def.
- Cast routes through the WWN module on the real caverns_and_claudes / elemental_harmony / heavy_metal packs (per-pack dispatch tests green).
- All existing spine guards stay loud (missing spell_id raises, unknown spell_id raises, cast on an opposed_check cdef raises); no content changes.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-20T19:36:43Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-20T19:00:00Z | - | - |
| red | 2026-06-20T19:00:00Z | 2026-06-20T19:07:25Z | 7m 25s |
| green | 2026-06-20T19:07:25Z | 2026-06-20T19:25:50Z | 18m 25s |
| review | 2026-06-20T19:25:50Z | 2026-06-20T19:36:43Z | 10m 53s |
| finish | 2026-06-20T19:36:43Z | - | - |

## Sm Assessment

**Routing decision:** New work, clean state — story 152-2 is `backlog`, no active session, no archived session. This is a prerequisite for story 152-3 (chargen test reconciliation) and completes epic-152's full WWN action synthesis (following 152-1's defensive actions). 152-1 landed on 2026-06-20; 152-2 has already-written RED specs (failing as expected).

**Scope (server-only, TDD/phased):** Cast synthesis is parallel to 152-1 (synthesis of Total Defense / Fighting Withdrawal). The work is: route a `cast_spell` commit to the existing WWN cast spine BEFORE the cdef beat lookup, mirroring the `is_item_use_beat` transient intercept (dice.py:390) and the attack synthesis (dice.py:414). The spine + validations already exist and work correctly; this story makes them reachable on a zero-beat def. Mirror the fix on the apply_beat path.

**RED spec (already written, failing):** tests/integration/test_dice_path_spell_cast_102_2.py (spell cast resolution via wwn.spell.cast span), tests/integration/test_wwn_{caverns,elemental_harmony,heavy_metal}_dispatch.py (cast routes through the wwn module on real packs), tests/integration/test_wwn_scene_harness_fixture_proof.py (cast_spell ablates hp). All are confirmed red with DiceDispatchError 'unknown beat_id cast_spell'.

**Guardrails for downstream agents:**
- Model the fix on the existing `is_item_use_beat` (dice.py:390-393) and `is_wn_action_beat` attack synthesis (dice.py:414-416) patterns — WN-gated, transient intercept before the cdef lookup.
- Do NOT weaken the cast spine guards: spell_id required, catalog membership validation, opposed-check refusal all stay loud.
- Preserve 152-1 invariants: closed allowlist (bogus ids still raise) + `isinstance(WithoutNumberRulesetModule)` gate (native packs resolve on native engine).
- Per the OTEL Observability Principle: the wwn.spell.cast span must fire for every cast attempt; the GM panel is the lie detector.

**Verification expectation:** Gate the full server suite against the known ~258-269 hermeticity baseline; any failure outside that baseline in the blast radius is a regression.

**Decision:** Setup complete, branch created, context written. Hand off to TEA for RED.

## TEA Assessment

### Red Phase (test writing)

**Tests Required:** Yes (RED spec already written; TEA audited, measured, and strengthened it)
**Reason:** n/a

**RED state — measured (12 failed, 1 passed, 2 skipped):** Confirmed against the running code, not the prose. The story's two-seam claim is real and reproduced:
- **Dice path** (`dice.py:424`): 5 cast tests fail with `DiceDispatchError: unknown beat_id 'cast_spell' — available: []`. Root cause confirmed by reading `dice.py:418` — `cast_spell` is not in `is_wn_action_beat`'s allowlist (`{attack, total_defense, fighting_withdrawal, run}`), so it falls to the `else` empty-cdef lookup and raises BEFORE the (already-correct) cast validations + spine at `dice.py:429-492` / `_resolve_wwn_cast_for_beat`.
- **Apply path** (`narration_apply.py:6326`): the 3 per-pack dispatch tests + the scene-harness cast proof fail with `ValueError: unknown beat_id 'cast_spell'` driving `_apply_narration_result_to_snapshot` on the real caverns/elemental_harmony/heavy_metal packs (AC3's `narration_apply` claim).

**Test Files (5; all integration, all run under default `testpaths=["tests"]`):**
- `tests/integration/test_dice_path_spell_cast_102_2.py` — dice-seam cast spec (AC1/AC2/AC5). 8 live tests for 152-2: 5 cast RED + 3 guard RED (now via `match=`); 1 guard PASS (spell_id-on-non-cast, real); 1 strike test loud-skipped.
- `tests/integration/test_wwn_{caverns,elemental_harmony,heavy_metal}_dispatch.py` — apply-path cast routes through the WWN module on the real packs (AC3/AC4). 1 cast RED each.
- `tests/integration/test_wwn_scene_harness_fixture_proof.py` — hydrated-fixture cast ablates HP (AC1). 1 cast RED + 1 strike test loud-skipped.

**Tests Written:** TEA edits were strengthening, not authoring — the cast spec pre-existed. Converted 4 vacuous guard passes → 3 genuine RED (`match=` on the specific guard message) + 1 genuine PASS (reachable `attack` so the real spell_id guard fires). Loud-skipped 2 stale-native-id strike orphans (committed_blow / elemental_burst) that 125-8 left behind. No production code touched.
**Status:** RED (12 failing on cast routing / guard-message-mismatch — ready for Dev)

**AC → coverage map:**
| AC | Test(s) | Status |
|----|---------|--------|
| AC1 cast resolves via spine (not unknown_beat) | test_cast_beat_with_spell_id_fires_wwn_cast_spine; test_hydrated_wwn_fixture_drives_cast_spell_and_ablates_hp | RED |
| AC2 face-independent / killing cast resolves+suppresses reprisal / no-casts refused | test_cast_outcome_is_independent_of_the_d20_face; test_killing_cast_resolves_encounter_and_suppresses_reprisal; test_cast_with_no_casts_remaining_is_refused_not_generic | RED |
| AC3 dice+apply parity; narration_apply no longer raises | test_cast_parity_with_apply_beat_path (dice↔spine parity); per-pack apply tests exercise the `narration_apply.py:6326` ValueError seam | RED |
| AC4 routes through WWN module on real packs | test_wwn_cast_spell_routes_through_wwn_module_on_real_{caverns,elemental_harmony,heavy_metal} | RED |
| AC5 guards stay loud (missing/unknown spell_id, opposed-check) | test_cast_beat_without_spell_id (match=missing spell_id); test_cast_beat_with_unknown_spell_id (match=unknown spell_id); test_cast_on_opposed_check (match=opposed_check); test_spell_id_on_non_cast_beat (PASS, real guard) | RED (3) + PASS (1) |

### Rule Coverage

| Rule (python lang-review) | Test(s) | Status |
|------|---------|--------|
| #6 Test quality (no vacuous assertions) | All 4 AC5 guard tests strengthened from vacuous-pass to genuine assertion via `match=` / reachable beat | enforced |
| #1 Silent exception swallowing → No Silent Fallbacks (SOUL) | AC5 guards assert a loud typed `DiceDispatchError` (no silent generic-INT fallback) for every malformed cast | failing→pass-post-fix |
| Wiring test (CLAUDE.md: every suite needs one) | Per-pack dispatch tests drive the REAL packs through `dispatch_dice_throw` / `_apply_narration_result_to_snapshot` (production seams), not synthetic fixtures | RED |
| OTEL Observability (CLAUDE.md) | `wwn.spell.cast` span assertions (refused True/False, spell_id, save, damage) pin the GM-panel lie detector on both paths | RED |

**Rules checked:** the applicable lang-review check for a test-design phase is #6 (test quality); directly enforced (4 vacuous tests fixed). #1/No-Silent-Fallbacks is covered by the loud-rejection guards.
**Self-check:** 4 vacuous guard tests found and fixed (3 → match=, 1 → reachable `attack`). 2 stale-id strike orphans loud-skipped (never xfail, never weakened).

**Handoff:** To Dev (Inigo) for implementation. Route `cast_spell` to the cast spine BEFORE the cdef beat lookup on BOTH the dice seam (`dice.py`, model on `is_item_use_beat` @ :394) and the apply seam (`narration_apply.py:6326`). Keep all four AC5 guards reachable on the routed path. Check the third seam (`wn_round.py:459`) per Delivery Findings. No content changes.

## Dev Assessment

**Implementation Complete:** Yes

**Approach:** Added a dedicated, **wwn-gated** transient-beat synthesis `wn_cast_beat()` (modeled on the `is_item_use_beat` intercept, NOT the ruleset-agnostic `is_wn_action_beat` allowlist) and routed a `cast_spell` commit through it BEFORE the cdef beat lookup on **all three** seams that share the broken `synthesize-or-raise` pattern. The cast-shape guards (spell_id/catalog/opposed) and the cast spine (`_resolve_wwn_cast_for_beat`) already existed and were correct — the fix makes them reachable on a zero-beat WWN combat def. `cast_spell` is deliberately kept out of `is_wn_action_beat` so a non-WWN WN pack's `cast_spell` stays a loud unknown-beat raise (No Silent Fallbacks) instead of a synthesize-but-no-resolve no-op.

**Files Changed:**
- `sidequest/game/beat_filter.py` — new `WN_CAST_SPELL_BEAT_ID` constant + `wn_cast_beat()` synthesis (id=cast_spell, push kind, no strike channel, INT stat_check). Additive; `_WN_ACTION_BEAT_IDS` unchanged.
- `sidequest/server/dispatch/dice.py` — `elif` cast intercept at the WN-action synthesis site (dice path).
- `sidequest/server/dispatch/wn_round.py` — same `elif` intercept on the sealed-round barrier walk (MP path; resolves TEA's third-seam finding).
- `sidequest/server/narration_apply.py` — cast synthesis in the legacy beat loop's `beat is None` branch (narrator apply path).

**Tests:** 13/13 cast tests GREEN (dice path 5 cast + 4 guards; per-pack apply 3; scene-harness cast 1) + 2 strike orphans still loud-skipped (0 failed). All four AC5 guards now fire for the right reason (the `match=` strings pass).

**Regression canary (targeted, not full 13k suite — per the no-full-rerun guidance + surgically-gated change):**
- WN-action seams (108-8 closed-allowlist, 152-1 defensive reprisal, 102-4 sealed-round, 106-4 item-use, 108-1 de-nativization, real WWN combat): **62 passed, 5 skipped**.
- Cross-ruleset dispatch incl. non-WWN WN (awn/cwn/road_warrior/mutant_wasteland) + full `tests/server/dispatch/` + beat_filter: **470 passed, 1 pre-existing failure** (proven via stash — see Delivery Findings).
- Broad WN/combat/cast integration sweep: **199 passed, 8 skipped**.
- Total ≈ 744 tests, **zero new regressions**; the one failure (`test_legacy_beat_selection_path_still_works`) reproduces on `develop` without my changes.

**AC verification:**
- AC1 ✓ cast resolves via the spine (`wwn.spell.cast`), no `unknown beat_id`.
- AC2 ✓ face-independent; killing cast resolves + suppresses reprisal; no-casts refused-but-recorded.
- AC3 ✓ dice + apply parity green; `narration_apply` no longer raises `ValueError 'cast_spell'`.
- AC4 ✓ routes through the WWN module on real caverns_and_claudes / elemental_harmony / heavy_metal.
- AC5 ✓ all guards loud (missing/unknown spell_id, opposed-check) — now genuinely exercised; no content changes.

**Branch:** `fix/152-2-cast-spell-synthesis` (pushed)

**Handoff:** To Reviewer (Westley) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 13 passed / 0 failed / 2 skipped; lint+format clean | confirmed 0, dismissed 0 (1 net-new skip = documented loud strike orphan) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — covered by Reviewer ([EDGE] below) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 4 (medium) — cast-spine narrator-path warn-and-return asymmetry | confirmed 1 (deferred non-blocking), dismissed 0; verified the 3 crux questions CLEAN |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — covered by Reviewer ([TEST] below) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — covered by Reviewer ([DOC] below) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — covered by Reviewer ([TYPE] below) |
| 7 | reviewer-security | Yes | findings | 1 (low) — same narrator-path asymmetry; all rules COMPLIANT | confirmed 0 (deferred non-blocking), dismissed 0 |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — covered by Reviewer ([SIMPLE] below) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — covered by Reviewer ([RULE] below) |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`, their domains covered by Reviewer directly)
**Total findings:** 0 confirmed-blocking, 2 deferred non-blocking (cast-spine asymmetry; flavor-pack dice-path stat resolution), 0 dismissed

## Reviewer Assessment

**Verdict:** APPROVED

**Summary:** A clean, surgically-scoped fix. The bug was *reachability* — the cast validations + spine (`_resolve_wwn_cast_for_beat`) already existed and were correct since 102-2; 108-3 stripped `cast_spell` out of `cdef.beats`, so commits hit the empty-cdef raise before the spine. The diff adds a dedicated wwn-gated `wn_cast_beat()` transient synthesis and routes `cast_spell` to it before the cdef lookup on all three seams (dice / sealed-round / narrator-apply). 13 cast tests GREEN; the No-Silent-Fallbacks guard for non-WWN rulesets is preserved; ~744 WN/combat tests show zero new regressions.

**Data flow traced:** client `DICE_THROW(beat_id="cast_spell", spell_id)` → `dispatch_dice_throw` (dice.py:421) → wwn-gated `elif` synthesizes `wn_cast_beat()` → **validation block still runs** (dice.py ~444-492: spell_id required / catalog membership / opposed-check) → `_apply_committed_player_beat` → `is_wwn_cast` recomputed (1419) → cast spine (1726). The synthesized beat does NOT bypass the guards (the `is_wwn_cast` recompute keys off `payload.beat_id`, not the synthesized object). Confirmed by [SEC] + my own read.

**Observations (≥5):**
- [VERIFIED] No guard bypass — the dice-path cast validation block runs *after* synthesis and still enforces spell_id/catalog/opposed; evidence: dice.py:444-492 gate on `is_wwn_cast = payload.beat_id=="cast_spell" and ruleset=="wwn"`, independent of the synthesized `beat`. AC5 tests green with `match=`.
- [VERIFIED] No-Silent-Fallbacks for non-WWN preserved — all three new `elif` branches gate on `ruleset=="wwn"`; a non-WWN `cast_spell` falls to the `else` and raises (`DiceDispatchError`/`ValueError`) exactly as before. Evidence: dice.py:438-444, wn_round.py:476-482, narration_apply.py:6342-6344. Corroborated by [SEC].
- [SEC] No injection/bypass — `spell_id` reaches only `WwnSpellCatalog.get()` (linear `==` scan → KeyError → typed `DiceDispatchError`); `yaml.safe_load` is on server YAML only; `ruleset` is a server-loaded pydantic field (`extra="forbid"`), not client-controlled. CWE-89/78/502/22: none. Verdict COMPLIANT on every rule.
- [SILENT] Cast-spine narrator-path asymmetry (4 guards warn-and-return vs dice-path raise) — **deferred, non-blocking** (see Devil's Advocate + Delivery Findings): the spine is PRE-EXISTING (not in this diff), the guards emit OTEL watcher events (`wwn.cast_spell_no_spell_id` etc.) — which IS the SideQuest "fail loud" mechanism (OTEL Observability Principle: the GM panel is the lie detector), and raising on the narrator path would crash the whole turn on an LLM omission. 152-2 only makes these guards *reachable*; it does not author them.
- [MEDIUM/own-find] Flavor-pack dice-path stat resolution — `wn_cast_beat()` uses canonical `stat_check="INT"`; the dice path's `attack_params`→`stat_modifier`→`_stat(stats, "INT")` does NOT translate canonical→flavor, and elemental_harmony stores flavor-keyed stats (`attribute_map: INTELLIGENCE→Insight`). A *dice-path* cast on elemental_harmony would `KeyError`. **Deferred, non-blocking:** this is the IDENTICAL mechanism as the shipped 152-1 `attack` (`stat_check="STR"`), a pre-existing shared bug in the whole WN synthesized-action set (TEA flagged it as a Question; I confirmed the root cause). 152-2's ACs are met — the per-pack apply tests (which don't stat-roll) pass on all packs incl. elemental_harmony, and the dice cast test passes on canonical-keyed heavy_metal. Not 152-2's to fix.
- [EDGE] Boundary paths checked: missing `pack`/`pack.rules` (the `and pack and pack.rules` short-circuits → falls to `else` → raise); empty cdef (the whole point — synthesis precedes the lookup); cast on opposed_check (guard raises). All handled.
- [TYPE] `wn_cast_beat()` returns a well-typed `BeatDef` mirroring `wn_action_beat`'s shape; `stat_check` is a `str` consistent with the existing synthesis (not a new stringly-typed API). `WN_CAST_SPELL_BEAT_ID` is a typed module constant. No type regressions.
- [TEST] The 4 AC5 guards are non-vacuous (`match=` pins the exact rejection message); the 2 skips are loud `@pytest.mark.skip` with detailed reasons (not xfail, not weakened); per-pack tests drive REAL packs through production seams (wiring tests). Good coverage of both entry points.
- [DOC] New comments/docstrings accurately describe behavior (the `wn_cast_beat` docstring correctly states "inert VEHICLE … real resolution is the cast spine"); the deliberate-omission-from-`is_wn_action_beat` rationale is documented at the constant + each seam. No stale/misleading comments.
- [SIMPLE] The 3-seam `elif` repeats a small gate (acceptable: each seam's gate keys off a different object — `payload.beat_id` / `commit.beat_id` / `sel.beat_id` — so a shared helper would obscure more than it saves). No dead code, no over-engineering.

### Rule Compliance (python lang-review)

| # | Rule | Applies? | Verdict |
|---|------|----------|---------|
| 1 | Silent exception swallowing | Yes | COMPLIANT — new branches raise loudly for non-WWN; the spine warn-and-return emits OTEL (pre-existing, deferred) |
| 2 | Mutable default arguments | No (no new defaults) | N/A |
| 3 | Type annotations at boundaries | Yes | COMPLIANT — `wn_cast_beat() -> BeatDef` annotated |
| 4 | Logging coverage/correctness | Yes | COMPLIANT — `damage_spec_missing` warning is `severity="warning"` (pre-existing); no new error paths unlogged |
| 5 | Path handling | No | N/A |
| 6 | Test quality | Yes | COMPLIANT — `match=` non-vacuous; skips have reasons; no `assert True` |
| 7 | Resource leaks | No | N/A |
| 8 | Unsafe deserialization | Yes | COMPLIANT — no pickle/eval; yaml is server-side safe_load |
| 9 | Async pitfalls | No (sync dispatch) | N/A |
| 10 | Import hygiene | Yes | COMPLIANT — explicit named imports, alphabetized; the function-level `wn_cast_beat` import in narration_apply avoids a heavy top-level dep, no cycle (beat_filter imports nothing from narration_apply) |
| 11 | Input validation at boundaries | Yes | COMPLIANT — client `beat_id`/`spell_id` validated (gate + catalog membership) before mutation |
| 12 | Dependency hygiene | No | N/A |
| 13 | Fix-introduced regressions | Yes | COMPLIANT — canary ~744 tests, 0 new regressions |

SOUL.md "Bind the Ruleset, Don't Balance It": COMPLIANT — cast is *removed* from the native lookup and routed to the WWN spine; no native mechanic is tuned to fit. OTEL Observability Principle: COMPLIANT — `wwn.spell.cast` fires on every cast (the GM-panel lie detector).

### Devil's Advocate

Argue this code is broken. The most damning case: the WWN cast spine on the narrator-apply path *silently swallows* four distinct precondition failures (missing spell_id, no catalog, unknown spell, no caster core) — it warns and returns rather than raising, and 152-2 makes that path newly reachable for WWN combat. A malicious or merely buggy narrator that emits `cast_spell` without a `spell_id` produces a cast that spends nothing, deals nothing, and crashes nothing — the spell simply evaporates, visible only on the GM panel. A confused player would see narration claiming a spell fired with no mechanical effect — precisely the Illusionism the OTEL doctrine exists to catch. Is that not a No-Silent-Fallbacks violation this story drags into the light?

Rebuttal, with evidence: (1) The spine is **pre-existing** — `_resolve_wwn_cast_for_beat` is not in this diff; 152-2 authored none of those four guards. (2) They are **not silent** in the SideQuest sense — each emits a `wwn.cast_spell_*` watcher event, and the project's "fail loud" mechanism *is* OTEL (CLAUDE.md: "The GM panel is the lie detector"), not a Python raise. (3) Raising on the narrator path would crash the entire turn on an LLM omission — strictly worse for the table than a recorded no-op. (4) The client-driven dice path — where a malformed request is an actual bug, not an LLM quirk — *does* raise (AC5, verified). So the asymmetry is a deliberate, documented policy split by trust boundary, not an oversight.

Second attack: could a flavor-renamed pack (elemental_harmony) crash a dice-path cast via the `stat_check="INT"` KeyError? Yes — and I confirmed it. But it is the exact mechanism the shipped 152-1 `attack` already carries; 152-2 neither introduces nor worsens it, and meets all its ACs. Both issues are filed as non-blocking Delivery Findings. Nothing here rises to Critical/High; nothing is introduced-and-unflagged. Verdict stands: APPROVED.

**Handoff:** To SM (Vizzini) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): two strike-regression tests in 152-2's own spec files are orphaned 125-8 stale-id debt — `test_strike_beat_without_spell_id_regression_unchanged` (committed_blow) and `test_hydrated_wwn_fixture_drives_deterministic_strike` (elemental_burst). 108-3 stripped those native beats; 125-8 (the assigned owner) shipped `done` without touching these files (it treated the whole 152-owned cast specs as 152-2's). They are NOT a clean id→`attack` swap: their casters are weaponless and the native beats carried a `damage_override`, so synthesized `attack` resolves no damage (`dice.py` `damage_spec_missing`). Loud-skipped (never xfail) with a ref. Affects `tests/integration/test_dice_path_spell_cast_102_2.py` + `tests/integration/test_wwn_scene_harness_fixture_proof.py` (a follow-up story should arm the caster + use canonical stats to restore strike-DAMAGE coverage). *Found by TEA during test design.*
- **Question** (non-blocking): the synthesized WN `attack` on the elemental_harmony scene-harness fixture raised `KeyError: stat 'STR' not in stat block ['Agility','Endurance','Harmony','Insight','Spirit','Strength']` (canonical `STR` stat_check vs a flavor-keyed stat block) AND `damage_spec_missing` (no weapon, no genre unarmed default). This is likely a fixture artifact (weaponless caster + flavor-keyed fixture stats), but it is worth confirming that real elemental_harmony combat — real characters carrying weapons and canonical-keyed stats — resolves a synthesized `attack` cleanly. If real chars are flavor-keyed at the stat-lookup seam, 108-8/152-1 attack synthesis has a latent gap on flavor-renamed WWN packs. Affects `sidequest/game/ruleset/without_number.py:118` (the no-fallback stat lookup) + the 108-8 attack path. *Found by TEA during test design.*
- **Gap** (non-blocking): a THIRD seam shares the broken `is_wn_action_beat` intercept pattern — `wn_round.py:459` (the sealed-round barrier-closing walk) does `if isinstance(ruleset, WithoutNumberRulesetModule) and is_wn_action_beat(commit.beat_id): ... else: <cdef lookup that raises 'sealed commit names unknown beat_id'>`. `cast_spell` is not in the allowlist, so a cast commit routed through the MP sealed round would raise there too. The story names only the dice path (`dice.py`) and the apply_beat path (`narration_apply.py`); no current test drives a cast through `wn_round`. Dev should confirm whether a cast can reach the sealed-round seam (MP/multi-actor barrier) and mirror the intercept there, or document that cast never routes through `wn_round`. Affects `sidequest/server/dispatch/wn_round.py:459`. *Found by TEA during test design.*

### Dev (implementation)
- **Resolved (not a finding)** — TEA's third-seam Gap (`wn_round.py:459`): a cast CAN reach the sealed-round barrier in MP, so I mirrored the cast intercept there too (not just dice + apply). All three seams now route `cast_spell` through `wn_cast_beat()`. No cast-through-`wn_round` test exists, but the synthesis path is identical to the two covered seams and the 102-4 sealed-round + 108-8 round tests stay green.
- **Gap** (non-blocking): a pre-existing stale test fails on `develop` independent of this story — `tests/server/dispatch/test_sealed_letter_dispatch_integration.py::test_legacy_beat_selection_path_still_works` asserts `"strike" in {b.id for b in cdef.beats}` but CAC combat's `cdef.beats == set()` (108-3 stripped all WWN combat beats). Proven pre-existing by stashing all four production changes and re-running (still fails). Same 108-3 stripped-beat debt family as the loud-skipped strike orphans; a follow-up should swap the stale `strike` assertion to the synthesized `attack` action or assert the de-nativized empty-beats reality. Affects `tests/server/dispatch/test_sealed_letter_dispatch_integration.py:562`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (non-blocking): the synthesized WN action set has a flavor-pack dice-path stat-resolution bug. `wn_cast_beat()` (and `wn_action_beat("attack")`, shipped 152-1) carry a *canonical* `stat_check` (`INT`/`STR`), but the dice path's `attack_params`→`stat_modifier`→`_stat(stats, key)` does NOT translate canonical→flavor, and flavor-renamed WWN packs store flavor-keyed stats (`elemental_harmony` `attribute_map`: `INTELLIGENCE→Insight`, `STRENGTH→Strength`). A `DICE_THROW` cast (or attack) on elemental_harmony therefore raises `KeyError: stat 'INT' not in stat block [...flavor keys]` at `without_number.py:118`. Confirmed by reading the maps + `_stat`; TEA empirically hit it for `attack`. NOT introduced by 152-2 (identical to shipped 152-1 attack) and 152-2's ACs are met (apply-path per-pack tests pass on all packs; dice cast test passes on canonical-keyed heavy_metal). A follow-up should translate the synthesized canonical `stat_check` through `attribute_map` before `_stat` (one fix covering attack + cast uniformly). Affects `sidequest/game/ruleset/without_number.py:110-121` + `wn_action_beat`/`wn_cast_beat`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the WWN cast spine `_resolve_wwn_cast_for_beat` warns-and-returns (watcher event, no raise) on four precondition failures (missing spell_id, no catalog, unknown spell, no caster core), asymmetric with the dice path's loud `DiceDispatchError`. Pre-existing (not in this diff), and the watcher events satisfy the OTEL-as-lie-detector doctrine, but 152-2 makes this path newly reachable for WWN combat. A follow-up should either unify the two entry points or document the narrator-path warn-and-continue as an explicit, named exception to No-Silent-Fallbacks (rationale: raising would crash the turn on an LLM omission). Affects `sidequest/server/narration_apply.py:350-430`. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Strengthened the four AC5 cast-guard tests from vacuous passes to genuine assertions**
  - Spec source: context-story-152-2.md, AC5 ("All existing spine guards stay loud: missing spell_id raises, unknown spell_id raises, cast on an opposed_check cdef raises")
  - Spec text: "All existing spine guards stay loud (missing spell_id raises, unknown spell_id raises, cast on an opposed_check cdef raises)"
  - Implementation: As written, all four guard tests passed VACUOUSLY today — `cast_spell` (and the stale strike id) hit the empty-cdef `unknown beat_id` raise at `dice.py:424` BEFORE reaching the guard each claims to test, so each `pytest.raises(DiceDispatchError)` matched the wrong error. Added `match=` clauses pinning the specific guard message (`missing spell_id`, `unknown spell_id`, `opposed_check`) so three now fail-now/pass-post-fix, and pointed the spell_id-on-non-cast guard at the reachable `attack` beat so it exercises the real guard (passes for the right reason).
  - Rationale: A guard test that passes because of an unrelated upstream raise proves nothing about the guard. Per the TEA vacuous-assertion mandate, these were strengthened so AC5 has real coverage and a fix that bypassed a guard would be caught.
  - Severity: minor
  - Forward impact: Dev's fix must keep all four guards reachable on the routed cast path (not just make the positive cast resolve); the `match=` strings pin the exact messages.
- **Loud-skipped two strike-regression tests instead of restoring them (deferred to a follow-up)**
  - Spec source: context-epic-152.md ("Pure stale-id test-debt … committed_blow/strike->attack swaps … stays in 125-8") + the epic's loud-skip-with-ref convention
  - Spec text: "The 152-owned and separate-root tests are loud-skipped with a story ref (NEVER a silent xfail, NEVER a weakened assertion) until their owning stories land."
  - Implementation: `test_strike_beat_without_spell_id_regression_unchanged` (committed_blow) and `test_hydrated_wwn_fixture_drives_deterministic_strike` (elemental_burst) are stale-native-id orphans physically inside 152-2's cast-spec files. 125-8 (assigned owner) shipped `done` without fixing them. Restoring them is NOT a clean id swap (weaponless casters + native `damage_override` removed → `attack` deals no damage; elemental_harmony flavor-stat KeyError). Loud-skipped with a story-ref reason rather than restored.
  - Rationale: Arming the casters / fixing the flavor-stat path is strike-synthesis work outside 152-2's cast-routing scope. Leaving them red would orphan them permanently (125-8 closed); a loud skip is the epic-sanctioned mechanism and keeps the cast RED clean.
  - Severity: minor
  - Forward impact: strike-DAMAGE regression coverage on these two fixtures is temporarily absent until a follow-up arms the casters (see Delivery Findings); the cast routing fix is unaffected.
### Dev (implementation)
- **Dedicated wwn-gated `wn_cast_beat()` synthesis instead of adding `cast_spell` to the `is_wn_action_beat` allowlist**
  - Spec source: context-story-152-2.md, Technical Approach + SM Assessment ("model on the `is_item_use_beat` transient intercept (dice.py:394) and the attack synthesis (dice.py:414)")
  - Spec text: "route a wwn cast_spell commit to the cast spine BEFORE the cdef beat lookup — model on the is_item_use_beat transient intercept and the attack synthesis"
  - Implementation: Modeled on the `is_item_use_beat` transient-intercept half (a gated `elif` before the cdef lookup) but did NOT add `cast_spell` to `_WN_ACTION_BEAT_IDS` / `is_wn_action_beat` (the "attack synthesis" half). Added a separate `wn_cast_beat()` helper, gated at each seam on `pack.rules.ruleset == "wwn"`.
  - Rationale: `is_wn_action_beat` is ruleset-agnostic (fires for any Without-Number binding), but the cast spine (`_resolve_wwn_cast_for_beat`) is WWN-specific (the non-WWN arm is B/X innate). Adding cast to the agnostic allowlist would let a non-WWN WN pack (swn/cwn/awn) synthesize a cast beat that then silently no-ops (no spine) — a No-Silent-Fallbacks violation. The wwn-gated `elif` keeps a non-WWN `cast_spell` a loud unknown-beat raise.
  - Severity: minor
  - Forward impact: none — `is_wn_action_beat`'s closed allowlist (108-8/152-1 invariant) is unchanged; cast routing is independent.
- **Fixed a THIRD seam (`wn_round.py:459`) beyond the two the story named**
  - Spec source: context-story-152-2.md (names the dice path `dice.py` + the apply path `narration_apply.py`); TEA Delivery Finding (third-seam Gap)
  - Spec text: "route the synthesized cast to the existing wwn cast spine … Mirror the fix on the apply_beat path."
  - Implementation: Also added the cast intercept to the sealed-round barrier walk (`wn_round.py`), which shares the same `is_wn_action_beat`-or-raise pattern, so an MP cast commit reaches the spine instead of raising `sealed commit names unknown beat_id`.
  - Rationale: A cast CAN reach the sealed round in MP combat; fixing only 2 of the 3 identical seams would leave a latent MP cast outage (CLAUDE.md "No half-wired features — connect the full pipeline"). No dedicated test exists for the sealed-round cast (out of the RED spec); covered-by-pattern + existing 102-4/108-8 sealed-round tests stay green.
  - Severity: minor
  - Forward impact: positive — closes the MP cast outage TEA flagged; a follow-up could add an explicit sealed-round cast test.
### Reviewer (audit)
- **TEA: Strengthened the four AC5 cast-guard tests (match=) → ✓ ACCEPTED by Reviewer:** converting vacuous passes into genuine assertions is exactly right; AC5 ("guards stay loud") had zero real coverage before. The `match=` strings pin the correct rejection reason and the fix keeps all four reachable. Sound.
- **TEA: Loud-skipped two strike-regression orphans → ✓ ACCEPTED by Reviewer:** committed_blow/elemental_burst are stripped-native-beat debt 125-8 left behind; restoring them needs weapon/damage-source work outside cast scope. Loud `@pytest.mark.skip` with a named reason (never xfail, never weakened) is the epic-sanctioned mechanism. Filed for follow-up.
- **Dev: Dedicated wwn-gated `wn_cast_beat()` instead of adding cast to `is_wn_action_beat` → ✓ ACCEPTED by Reviewer:** the No-Silent-Fallbacks rationale is correct — the cast spine is WWN-specific, so a ruleset-agnostic allowlist entry would let a non-WWN WN pack synthesize-but-not-resolve. [SEC] + [SILENT] both verified the non-WWN path stays a loud raise. The right call.
- **Dev: Fixed a THIRD seam (wn_round.py) beyond the two the story named → ✓ ACCEPTED by Reviewer:** a cast CAN reach the MP sealed-round barrier; fixing 2 of 3 identical seams would leave a latent MP cast outage (CLAUDE.md "No half-wired features"). Closing TEA's third-seam finding is correct. No regression in the 102-4/108-8 sealed-round tests. A follow-up sealed-round cast test would be nice-to-have but is not blocking.