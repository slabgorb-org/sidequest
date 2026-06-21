---
story_id: "153-1"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 153-1: [CWN-OPPONENT-REPRISAL-NO-DAMAGE] wire damage_spec onto the CWN opponent reprisal beat so landed hits ablate player HP

## Story Details
- **ID:** 153-1
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 3
- **Type:** bug
- **Repos:** server

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-21T12:28:56Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-21T11:52:50Z | 2026-06-21T11:55:40Z | 2m 50s |
| red | 2026-06-21T11:55:40Z | 2026-06-21T12:07:13Z | 11m 33s |
| green | 2026-06-21T12:07:13Z | 2026-06-21T12:22:37Z | 15m 24s |
| review | 2026-06-21T12:22:37Z | 2026-06-21T12:28:56Z | 6m 19s |
| finish | 2026-06-21T12:28:56Z | - | - |

## Sm Assessment

**Setup complete.** Story 153-1 ([CWN-OPPONENT-REPRISAL-NO-DAMAGE]) is ready for the RED phase.

- **Workflow:** tdd (phased) → setup (SM) → red (TEA) → green (Dev) → review → finish
- **Repos:** server (sidequest-server, targets `develop`)
- **Branch:** `feat/153-1-cwn-reprisal-damage` (cut from develop HEAD `bc293233`, clean tree)
- **Story context:** `sprint/context/context-story-153-1.md`

**Scope — a well-bounded WIRING fix, NOT a balance change.** A CWN opponent reprisal to-hit succeeds but the beat carries no `damage_spec`, so the player takes 0 HP (`dice.opponent_reprisal_damage_spec_missing` warning; player HP stuck at 10/10 across a full fight — combat is unlosable). Wire the opponent's weapon `damage_spec` through the reprisal so landed hits ablate player HP. **Fix template:** the SWN path already does this correctly (`opponent_attack_resolved` → on-hit `opponent_damage_roll_resolved` rolling the weapon damage_spec 1d6 → player HP ablates); the CWN path is missing that wiring. Distinct from epic-108's WWN empty-beat-pool — here the beat-pool AND player-side ablation are healthy; only the opponent→player damage channel is dead. No silent 0-damage fallback ("No Silent Fallbacks"); add an OTEL span on the reprisal-damage resolution (OTEL Observability Principle) so the GM panel can verify a landed hit now ablates HP.

**Handoff → TEA (RED):** write a failing test reproducing a CWN opponent reprisal landing but dealing 0 HP, plus a regression guard that the SWN/WWN reprisal damage paths stay green (SWN-COMBAT-GREEN must not regress).

## Tea Assessment

**Tests Required:** Yes
**Test File:** `sidequest-server/tests/integration/test_153_1_cwn_reprisal_unarmed_floor.py` (committed `09381f3b`)
**Tests Written:** 11 (5 RED behavior + 6 GREEN regression guards)
**Status:** RED confirmed (`uv run pytest -n0`, serial) — 5 failed / 6 passed

**Root cause (confirmed read-only).** The damage cascade `resolve_damage_spec_from_beat_and_actor` (`game/ruleset/combat_rules.py`) has exactly one unarmed floor: **priority 4 = `pack.rules.unarmed_damage`**. Grep proves **no content pack authors it** (`unarmed_damage` is a `rules.py:1254` model field, zero hits in `genre_packs/*/rules.yaml`). So a weaponless WN opponent — no `beat.damage_override`, no inventory weapon, no genre floor — resolves to `None`, and the reprisal HIT path (`dispatch/dice.py:2285`) logs `dice.opponent_reprisal_damage_spec_missing` and deals 0 HP. SWN only survives this because its `combat` cdef *authors* `opponent_damage`; road_warrior's CWN `combat` cdef does **not**. `wn_action_beat`'s own docstring promises a weaponless WN attack resolves "from the actor's inventory **or the genre unarmed floor**" — a floor that is never populated.

**Fix contract (server, doctrine).** The Without Number ruleset core must supply its **SRD unarmed-strike floor** as the LAST resort (a positive `DamageSpec`), so a weaponless WN opponent's landed hit always ablates HP — per SOUL "Defer to SRD for mechanics" (don't hand-balance a number) and "No Silent Fallbacks" (don't silently deal 0). The floor must NOT override an equipped weapon (priority 1–3) or an authored `pack.rules.unarmed_damage` (priority 4), and must NOT leak into the non-WN `dial`/`fate` paths. Tests pin the **behavior** (floor exists + is positive; reprisal ablates HP + emits `opponent_damage_roll_resolved`, never `opponent_damage_spec_missing`) — NOT the exact die (Dev picks the SRD value, e.g. WN unarmed 1d2).

**Where to implement (suggestion, Dev's call):** `WithoutNumberRulesetModule.resolve_damage` (`game/ruleset/without_number.py:276`) — fall back to the WN SRD unarmed spec when `resolve_damage_spec_from_beat_and_actor(...)` returns `None`. WN core so all four siblings inherit (ADR-142). The reprisal seam (`dispatch/dice.py:2282`) already calls `ruleset.resolve_damage(...)` — no dispatch change needed, and its `opponent_damage_roll_resolved` watcher op already fires once a spec resolves (OTEL Observability Principle satisfied by the existing seam).

### Rule Coverage

| Rule (SOUL / CLAUDE.md / lang-review) | Test(s) | Status |
|---|---|---|
| No Silent Fallbacks (silent-exceptions) — no silent 0-damage hit | `test_cwn_weaponless_reprisal_ablates_player_hp` (asserts no `opponent_damage_spec_missing`) | failing |
| OTEL Observability — landed reprisal emits a damage span/op | `test_cwn_weaponless_reprisal_ablates_player_hp` (asserts `opponent_damage_roll_resolved`) | failing |
| Every Test Suite Needs a Wiring Test | `test_cwn_weaponless_reprisal_ablates_player_hp` (drives real `_resolve_opponent_reprisal` + road_warrior pack) | failing |
| Defer to SRD (don't hand-balance) — floor exists, die unpinned | `test_wn_weaponless_strike_resolves_srd_unarmed_floor[swn/cwn/wwn/awn]` | failing |
| Bind the Ruleset — floor at WN core, all siblings | parametrized `[swn/cwn/wwn/awn]` | failing |
| fix-regressions — weapon wins over floor | `test_wn_armed_strike_uses_weapon_not_unarmed_floor[*]` | passing (guard) |
| fix-regressions — floor doesn't leak to non-WN | `test_non_wn_ruleset_has_no_unarmed_floor` | passing (guard) |
| fix-regressions — authored pack floor wins | `test_authored_pack_unarmed_damage_wins_over_srd_floor` | passing (guard) |
| test-quality (no vacuous assertions) | self-check below | n/a |

**Rules checked:** 8 of 13 lang-review checks applicable; the load-bearing ones (silent-exceptions, test-quality, logging, fix-regressions) + the 3 SOUL/CLAUDE.md project rules all have coverage.
**Self-check:** 0 vacuous assertions — every test asserts a specific value (HP strictly decreases; spec non-None AND min-damage ≥ 1; `dice == "2d6"`; explicit op present/absent). The wiring test guards its own validity with a hit-precondition assert so it can't vacuously pass on a missed reprisal.

**Handoff:** To Dev (Agent Smith) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/sidequest/game/ruleset/without_number.py` — added `SRD_UNARMED_DICE = "1d2"` class constant + a last-resort fallback in `WithoutNumberRulesetModule.resolve_damage`: when the existing cascade (`resolve_damage_spec_from_beat_and_actor`) returns `None`, return `DamageSpec(dice=self.SRD_UNARMED_DICE)`. WN core → all four siblings (swn/cwn/wwn/awn) inherit; dial/fate have their own `resolve_damage` and are untouched. (16 insertions, 1 deletion.)

**Approach (exactly TEA's contract).** Implemented the WN SRD unarmed-strike floor at the ruleset core. `1d2` is the WWN/SWN/CWN SRD unarmed value and is a system-native **parity die** (the validator explicitly allows d2, backed by a real d6). The floor is the LAST resort — an equipped weapon (priority 1–3) and an authored `pack.rules.unarmed_damage` (priority 4) both still win (regression guards green). The reprisal seam (`dice.py`) and its `opponent_damage_roll_resolved` OTEL op needed **no change** — they already fire once a spec resolves (Don't-Reinvent / Verify-Wiring).

**Scope note for Reviewer (not a deviation):** because the fix lands at the shared `resolve_damage` seam (the location TEA directed), the SRD floor applies symmetrically — a weaponless **player** strike now also deals 1d2 (previously a latent 0-damage `damage_spec_missing` on the player's own strike too). This is SRD-correct (an unarmed character deals 1d2, not 0) and confirmed non-regressing by the full combat suite.

**Tests:** 11/11 story tests GREEN (`test_153_1_cwn_reprisal_unarmed_floor.py`). Regression: 90/90 targeted combat/ruleset/reprisal tests across CWN/SWN/WWN/AWN green. Full suite: with-impl **84 failed / 13617 passed** vs clean-develop baseline **83 failed / 13606 passed** — passed +11 (exactly my 11 tests); the single +1 failure is `test_schema_at_head_check::test_behind_head_db_fails_loud`, a parallel-DB-state flake that **passes 6/6 in isolation** with my impl present (an Alembic schema-at-head check cannot be affected by a damage-resolution edit). The 83 baseline failures are all pre-existing/environmental (chargen subprocess, pregen/ADR-145 fixture, lore-RAG-needs-daemon, epic-157 content-tagging). ruff + pyright clean on the changed file (the 3 pre-existing pyright errors on lines 171/759/1054 are unrelated and present on develop).

**Branch:** `feat/153-1-cwn-reprisal-damage` (pushed, `7792069e`). Test commit `09381f3b`.

**Handoff:** To next phase (verify/review).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 actionable (2 content-skip guards noted) | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | Yes | Skipped (disabled) | N/A | Disabled via settings — domain assessed by Reviewer ([EDGE]) |
| 3 | reviewer-silent-failure-hunter | Yes | Skipped (disabled) | N/A | Disabled via settings — domain assessed by Reviewer ([SILENT]) |
| 4 | reviewer-test-analyzer | Yes | Skipped (disabled) | N/A | Disabled via settings — domain assessed by Reviewer ([TEST]) |
| 5 | reviewer-comment-analyzer | Yes | Skipped (disabled) | N/A | Disabled via settings — domain assessed by Reviewer ([DOC]) |
| 6 | reviewer-type-design | Yes | Skipped (disabled) | N/A | Disabled via settings — domain assessed by Reviewer ([TYPE]) |
| 7 | reviewer-security | Yes | clean | 0 (trusted-constant surface) | confirmed 0, dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | Yes | Skipped (disabled) | N/A | Disabled via settings — domain assessed by Reviewer ([SIMPLE]) |
| 9 | reviewer-rule-checker | Yes | Skipped (disabled) | N/A | Disabled via settings — domain assessed by Reviewer ([RULE]) |

**All received:** Yes (preflight + security ran; 7 disabled via `workflow.reviewer_subagents` and assessed inline by the Reviewer)
**Total findings:** 1 confirmed (Medium, non-blocking — toothless-detector drift), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

The change is minimal (16 lines), exactly the spec-directed fix, fully tested, and green across the combat/ruleset surface. One Medium (non-blocking) observability finding is documented for follow-up; no Critical/High issues.

**Data flow traced:** a weaponless WN opponent's landed reprisal → `_resolve_opponent_reprisal` (dice.py:2282) → `cdef.opponent_damage or ruleset.resolve_damage(...)` → (post-fix) `WithoutNumberRulesetModule.resolve_damage` returns the SRD floor `DamageSpec(dice="1d2")` → `apply_beat_hp_channel` ablates player HP → `opponent_damage_roll_resolved` watcher op fires. Safe: the floor is built from a trusted class constant (`SRD_UNARMED_DICE`), never player input.

**Observations (cause → effect):**
- `[VERIFIED]` Last-resort ordering — `resolve_damage` returns the cascade result when non-None and only falls through to the floor on `None` (without_number.py:284-294). Equipped weapon (priority 1–3) and authored `pack.rules.unarmed_damage` (priority 4) both still win — proven by `test_wn_armed_strike_uses_weapon_not_unarmed_floor` and `test_authored_pack_unarmed_damage_wins_over_srd_floor` (both green). Not a balance-tuning of the bound ruleset; it binds the SRD unarmed default.
- `[VERIFIED][SEC]` Trusted-constant surface — `DamageSpec(dice=self.SRD_UNARMED_DICE)` is constructed from a class constant `"1d2"`; no player/NPC/pack-YAML value flows into it (security subagent: clean). `"1d2"` is a validator-whitelisted parity die (inventory.py:108-111) so construction cannot raise.
- `[VERIFIED][TYPE]` Return contract honored — base `resolve_damage -> DamageSpec | None`; the WN override now never returns `None`, a narrowing that is type-compatible. dial/fate define their OWN `resolve_damage` (dial.py:71, fate.py:542) and are untouched — no leak to non-WN (`test_non_wn_ruleset_has_no_unarmed_floor` green).
- `[VERIFIED][EDGE]` Beat-channel scoping — both production strike callers gate on `damage_channel == "strike"` (player strike dice.py:1450; reprisal opponent_beat filtered to strike at dice.py:2042). The floor cannot give 1d2 to a non-strike move/defense action. The miss-path Shock (dice.py:2185) reads the floor spec but `resolve_shock` returns 0 for `shock<=0` (the 1d2 floor has shock=0) — so a missed unarmed reprisal still chips nothing. Correct.
- `[VERIFIED][TEST]` Test quality (analyzer disabled — assessed) — every test asserts a specific value (HP strictly decreases; spec non-None AND min-damage ≥ 1; `dice == "2d6"`; explicit watcher op present/absent); the wiring test guards validity with a hit-precondition assert (`_MaxRng` forces the d20) so it can't vacuously pass on a missed reprisal; parametrized across all four WN siblings. No vacuous assertions.
- `[VERIFIED][SIMPLE]` Minimal, no over-engineering — a class constant + a 3-line fallback at the one correct seam (WN core). Reuses the existing cascade, reprisal seam, and `opponent_damage_roll_resolved` OTEL op (no reimplementation; "Don't Reinvent / Verify Wiring").
- `[MEDIUM][SILENT][DOC]` **Toothless-detector drift (the one real finding).** `_opponent_reprisal_damage_resolvable` (encounter_lifecycle.py:231-267) independently mirrors damage priorities 1–3 and **does not consult the WN unarmed floor**; its docstring promises it "agrees with the runtime path EXACTLY (no drift)." Post-fix, a weaponless WN opponent deals 1d2 at runtime, but the seating-time detector still fires `encounter_opponent_toothless_span` with the now-false rationale "*every enemy reprisal will land for 0 HP (the player is invulnerable)*" (line 398-411). This is a false-positive observability span, not a gameplay bug — combat is correct. The detector's own comment blesses conservative false-positives ("never a silent miss"), and the signal (no authored `opponent_damage`) is still a useful content-authoring nudge, so this is **non-blocking**. Recorded as a delivery finding for a follow-up (teach the detector about the WN floor, or reword its rationale from "0 HP / invulnerable" to "falls back to SRD unarmed 1d2"). The parallel `dice.damage_spec_missing` warnings (player dice.py:1463, reprisal dice.py:2292) are now dead for WN — that is the intended effect of the fix, not a regression.

### Rule Compliance

| Rule | Applies to | Verdict |
|------|-----------|---------|
| Bind the Ruleset, Don't Balance It (SOUL/ADR-143) | the SRD floor | COMPLIANT — binds the SRD unarmed default at the WN core; not a hand-balanced native mechanic |
| Defer to SRD for mechanics | `SRD_UNARMED_DICE = "1d2"` | COMPLIANT — WWN/SWN/CWN SRD unarmed value, cited in the docstring; system-native parity die |
| No Silent Fallbacks (CLAUDE.md, critical) | `resolve_damage` fallback | COMPLIANT at runtime (replaces a silent 0-damage with an explicit cited default). Observability caveat → the toothless-detector drift finding above |
| Don't Reinvent / Verify Wiring (CLAUDE.md) | reprisal seam + OTEL op | COMPLIANT — reuses the existing seam + `opponent_damage_roll_resolved`; no reimplementation |
| Every Test Suite Needs a Wiring Test | test file | COMPLIANT — `test_cwn_weaponless_reprisal_ablates_player_hp` drives the real `_resolve_opponent_reprisal` |
| OTEL Observability Principle | reprisal decision | COMPLIANT (damage op fires); the toothless span is the drift finding |
| lang-review python (silent-exceptions, mutable-defaults, type-annotations, test-quality) | diff | COMPLIANT — no bare except, no mutable default (immutable `str` const), `SRD_UNARMED_DICE: str` typed, assertions meaningful |

`[RULE]` rule-checker disabled — enumerated the applicable rules above by hand; no violations.

### Devil's Advocate

Argue the code is broken. **First:** the symmetric application changes combat balance silently — every weaponless WN combatant on every WN pack (7 packs) now deals 1d2 where it dealt 0, including bestiary creatures that authors deliberately left weaponless. Could a "harmless" ambient creature now chip the PC and skew the encountergen difficulty calibration? Mitigation: 1d2 is the SRD floor (the *minimum* meaningful damage), the full combat suite (44 regression + 90 targeted) is green, and SOUL says a weaponless combatant *should* deal unarmed damage — 0 was the bug. **Second:** the toothless detector now lies on the GM panel — the lie-detector is SideQuest's core trust mechanism, and a false "player invulnerable" alarm is exactly the kind of thing that erodes Keith's confidence in the panel. This is real, hence the documented finding; but it over-warns (false positive), which the detector's design explicitly tolerates, so it is not blocking. **Third:** the dead `damage_spec_missing` branch — could a future non-WN ruleset or a non-strike caller still need `None`? dial/fate keep their own `resolve_damage`, and both strike callers gate on the strike channel, so `None` remains reachable for legitimately-non-WN/non-strike paths; the branch is defensive, not dead-in-all-cases. **Fourth:** could `"1d2"` break the 3D dice overlay (no d2 mesh)? No — the parity-die mechanism (backed by a d6, even→1/odd→2) is purpose-built for exactly this and the validator whitelists it. **Fifth:** a sibling whose SRD unarmed differs (AWN mutant natural attacks?) — the constant is overridable per sibling, so this is extensible, not locked. Net: the fix is correct; the only genuine issue is the observability drift, captured as a finding.

**Pattern observed:** clean last-resort fallback at the ruleset core, inherited by siblings (ADR-142) — `without_number.py:284-294`.
**Error handling:** no new error paths; `DamageSpec` construction is from a validated constant.
**Handoff:** To SM for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): No content pack authors `pack.rules.unarmed_damage`, yet `wn_action_beat`'s contract promises a "genre unarmed floor" — so EVERY weaponless WN opponent across all 7 WN packs (not just road_warrior/the_circuit) silently deals 0 HP on a landed reprisal. Affects `sidequest/game/ruleset/without_number.py` / `combat_rules.py` (the WN-core SRD floor fixes all four siblings at once). *Found by TEA during test design.*
- **Question** (non-blocking): The board hypothesizes this shares a root with the WWN-COMBAT-NARRATOR-LEAK "unbacked damage" half (a sibling 153-x story). Dev/Reviewer should confirm whether the WN SRD floor also closes that — but note epic-108's empty-beat-pool (WWN combat never seats beats) is a DISTINCT issue, out of scope here. Affects `sidequest/server/dispatch/dice.py` (reprisal damage seam). *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): The WN SRD floor now means every WN pack gets correct weaponless-strike damage WITHOUT authoring `pack.rules.unarmed_damage` — but the `combat_rules.py` priority-4 comment and `wn_action_beat` docstring still describe the per-pack floor as the only source. A docs/comment pass could note the WN-core fallback. Affects `sidequest/game/ruleset/combat_rules.py` (comment only). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): The seating-time toothless detector `_opponent_reprisal_damage_resolvable` drifts from the runtime after 153-1 — it mirrors damage priorities 1–3 only and ignores the new WN unarmed floor, so it still fires `encounter_opponent_toothless_span` (with rationale "every enemy reprisal will land for 0 HP / the player is invulnerable") for weaponless WN opponents that now actually deal 1d2. False-positive observability span, combat is correct. Affects `sidequest/server/dispatch/encounter_lifecycle.py:231-414` (teach the detector about the WN floor, OR reword the rationale to "no authored opponent_damage; falls back to SRD unarmed 1d2"). Good candidate for a follow-up story under epic-153. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec. Tests cover each SM-scoped AC direction (HP ablation, no missing-spec, OTEL op, SWN/WWN no-regress) plus the doctrine guards; the SRD die value is intentionally left unpinned for Dev (spec says "per the ruleset, not a hand-balanced number").

### Dev (implementation)
- No deviations from spec. Implemented exactly the TEA-directed fix (`WithoutNumberRulesetModule.resolve_damage` SRD floor, WN core, all four siblings) with the minimal change. Chose `1d2` (the SRD unarmed value / system-native parity die) for the unpinned die. The fix landing at the shared `resolve_damage` seam means it applies symmetrically to weaponless player strikes too — this is the inherent, SRD-correct consequence of the spec-directed location, not a deviation (noted for the Reviewer in the Dev Assessment).

### Reviewer (audit)
- **TEA "No deviations from spec"** → ✓ ACCEPTED by Reviewer: tests faithfully encode the SM-scoped ACs + doctrine guards; leaving the die value unpinned was correct.
- **Dev "No deviations from spec" + symmetric-scope note** → ✓ ACCEPTED by Reviewer: the symmetric application to weaponless player strikes is the inherent, SRD-correct consequence of fixing at the TEA-directed `resolve_damage` seam — agrees with author reasoning, not a deviation.
- **Undocumented consequence (not a spec deviation):** the change drifts the seating-time toothless detector from the runtime (it ignores the new floor). Surfaced as a Medium non-blocking finding + a Reviewer delivery finding for follow-up — combat correctness is unaffected, so it does not flag the deviation set.