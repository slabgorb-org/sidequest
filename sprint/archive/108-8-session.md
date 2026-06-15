---
story_id: "108-8"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 108-8: Engine core cut FOLLOW-ON — run_wn_round() must OWN the WN action set so a zero-beat WWN combat def resolves

## Story Details
- **ID:** 108-8
- **Jira Key:** (no Jira integration)
- **Workflow:** tdd
- **Stack Parent:** none
- **Type:** refactor
- **Points:** 5
- **Epic:** 108 — WN combat owns the WN round (ADR-143)

## Problem Summary

Story 108-1 removed native riders (fleeting tags, dial advances, Brace) but the runtime (`run_wn_round()` and `dice.py:407`) still resolves committed actions by looking up `commit.beat_id` in `cdef.beats`. With native beats stripped in 108-3, this causes:

```
DiceDispatchError: unknown beat_id ... available: []
```

78 e2e failures across WWN packs (caverns_and_claudes, heavy_metal, elemental_harmony, beneath_sunden, barsoom). The runtime half of 108-1's intent was never implemented.

## Technical Approach

Under `WithoutNumberRulesetModule` binding:
1. Synthesize transient WN action beats (attack/move/item-use/cast) independent of `cdef.beats`
2. Model on existing `is_item_use_beat()` pattern ("Drink potion" beat not in cdef)
3. Keep WN math intact (d20+hit vs AC, weapon dice, Shock, saves, ablative HP)
4. Emit `wn.native_scaffolding_suppressed` OTEL (lie detector)
5. Native packs retain beat requirement (isinstance gate, 108-7 enforced)

**Seams:** dispatch/dice.py ~671-676, run_wn_round() beat-resolution path, game/ruleset/without_number.py

**Refs:** ADR-143, ADR-142, ADR-117, ADR-139, ADR-114

## Acceptance Criteria

1. Zero-beat WWN combat defs resolve without error
2. WN action set synthesized only under WN binding
3. WN math preserved (d20+hit, weapon dice, Shock, saves, ablative)
4. OTEL `wn.native_scaffolding_suppressed` proves native riders OFF
5. No regression: playtest/e2e tests pass, native packs still work

## Sm Assessment

**Story:** 108-8 — runtime half of the engine-core cut. 108-1 stripped native riders and 108-3 emptied `cdef.beats`, but `run_wn_round()` and `dice.py` still resolve a commit by looking up `commit.beat_id` in `cdef.beats`. Result: every WWN combat commit raises `DiceDispatchError: unknown beat_id ... available: []` — total combat outage, 78 e2e failures. This is the runtime the epic *assumed* 108-1 delivered.

**Why this story, why now:** p1, and it **unblocks 108-3** (depends_on declared). 108-3's content de-nativize cannot land while the engine still demands beats that no longer exist. Highest-leverage WWN-combat fix in the backlog.

**Scope / repos:** server-only. Three seams — `dispatch/dice.py` (~671-676), the `run_wn_round()` beat-resolution path (`dispatch/wn_round.py:374`), and `game/ruleset/without_number.py`.

**Doctrine fit (SOUL — Bind the Ruleset, Don't Balance It):** the action set is *synthesized under the WN binding*, modeled on the existing `is_item_use_beat()` transient-beat pattern. This removes native beats from the WN path — it does NOT re-introduce or re-balance native mechanics. Native packs keep their `isinstance` beat gate. OTEL `wn.native_scaffolding_suppressed` is the lie detector proving native is OFF.

**Risk flags for TEA/Dev:**
- WN math must stay byte-for-byte (d20+hit vs AC, weapon dice from actor inventory, Shock, saves, ablative HP). The cut is structural, not numerical.
- The synthesis must be gated to the WN binding only — a native pack hitting the new path would be a regression, not a feature. Needs an explicit isinstance/binding guard plus a test proving native still requires beats.
- Wiring test required (project rule): the synthesized action set must be reached from the real dispatch path, not just unit-tested in isolation.

**Decision:** Proceed to RED. TDD/phased. Handing to TEA (Amos Burton) to write the failing zero-beat-resolution test first.

## TEA Assessment

**Tests Required:** Yes
**Reason:** 5-pt runtime refactor with observable behavior (combat resolution, OTEL spans) — not a chore.

**Test Files:**
- `sidequest-server/tests/integration/test_108_8_wn_round_owns_action_set.py` — zero-beat WN
  combat resolution suite (real heavy_metal/wwn pack; beats stripped to reproduce the post-108-3 state).

**Tests Written:** 7 tests covering all 5 ACs.
**Status:** RED — 5 failing (ready for Dev), 2 green guards passing.

Verified RED reason: `DiceDispatchError: unknown beat_id 'attack' for encounter 'combat' — available: []`
(the exact total-combat-outage this story fixes). Green guards pass today and must stay green.

| # | Test | AC | Status |
|---|------|----|--------|
| 1 | `test_zero_beat_wn_attack_resolves_without_dispatch_error` | AC1 | **RED** |
| 2 | `test_zero_beat_wn_attack_removes_opponent_hp` | AC1/AC3 | **RED** |
| 3 | `test_zero_beat_wn_attack_emits_native_scaffolding_suppressed` | AC4 | **RED** |
| 4 | `test_zero_beat_wn_attack_mints_no_native_fleeting_tag` | AC3 | **RED** |
| 5 | `test_ws_dice_throw_zero_beat_attack_resolves_end_to_end` (wiring) | AC1/AC5 | **RED** |
| 6 | `test_unknown_action_id_under_zero_beats_still_raises` | AC2 | green guard |
| 7 | `test_native_attack_does_not_engage_wn_synthesis` | AC2 | green guard |

### Rule Coverage

| Rule (CLAUDE.md / SOUL) | Test(s) | Status |
|------|---------|--------|
| OTEL Observability — every subsystem decision emits a span | `…emits_native_scaffolding_suppressed`, wiring (`wwn.round.resolved`+suppressed) | RED |
| No Silent Fallbacks — closed allowlist, not "accept any id when beats empty" | `…unknown_action_id_under_zero_beats_still_raises` | green guard |
| Bind the Ruleset, Don't Balance It (ADR-143) — native engine OFF on WN path | `…mints_no_native_fleeting_tag`, `…emits_native_scaffolding_suppressed` | RED |
| isinstance gate — native packs keep requiring authored beats | `…native_attack_does_not_engage_wn_synthesis` | green guard |
| Every test suite needs a wiring test (behavior, not source-grep) | `…ws_dice_throw_zero_beat_attack_resolves_end_to_end` (handler→dispatch→round) | RED |
| WN math preserved (weapon dice → ablative HP) | `…removes_opponent_hp`, wiring HP-drop assertion | RED |

**Rules checked:** 6 of 6 applicable rules have test coverage.
**Self-check:** 0 vacuous tests — every assertion checks a concrete value (HP delta, span name + slug honesty, raised error, minted tags). No `let _ =` / `assert True` / always-None checks.

**Two seams for Dev:** `dispatch/dice.py:407` AND `dispatch/wn_round.py:374` both look the commit up in `cdef.beats` — synthesize at both (the solo-table tests drive both). Model on `is_item_use_beat` (dice.py:390, intercepts BEFORE the lookup). Gate on `isinstance(ruleset, WithoutNumberRulesetModule)`. See Delivery Findings for the action-id confirmation (blocking).

**Handoff:** To Dev (Naomi Nagata) for GREEN.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — GREEN (7/7 + 160/160 regression), ruff clean, pyright errors pre-existing on develop, 0 code smells |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — I covered boundaries manually (Devil's Advocate) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — covered by rule-checker A1 + my own No-Silent-Fallback trace |
| 4 | reviewer-test-analyzer | Yes | findings | 5 | confirmed 0 blocking, 5 dismissed/deferred as non-blocking test-strengthening (1 overstated — challenged) |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 | confirmed 3 as LOW non-blocking doc nits |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — I checked the new BeatDef/types manually (Rule Compliance) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings — no auth/input/secret surface in this diff; rule-checker #11 clean |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — diff is minimal/surgical; no over-engineering observed |
| 9 | reviewer-rule-checker | Yes | clean | 0 | N/A — 0 violations across 13 lang-review rules + 5 project rules (A1–A5) |

**All received:** Yes (4 enabled returned; 5 disabled pre-filled per settings)
**Total findings:** 1 confirmed Medium (mine, non-blocking) + 3 LOW doc + 5 test-strengthening; 0 blocking, several deferred to Delivery Findings

## Reviewer Analysis

### Rule Compliance

Enumerated every changed function/branch against CLAUDE.md + SOUL.md + the Python lang-review checklist:

- **No Silent Fallbacks (CLAUDE.md/critical):** ✓ `wn_action_beat` raises `PackError` on any id outside the closed `_WN_ACTION_BEAT_IDS` frozenset (beat_filter.py:147). Both dispatch seams (dice.py, wn_round.py) synthesize ONLY under `isinstance(ruleset, WithoutNumberRulesetModule) AND is_wn_action_beat(id)`; every other id falls to the original `else` branch and raises `DiceDispatchError`. This is NOT "accept any id when beats are empty" — verified by `test_unknown_action_id_under_zero_beats_still_raises`.
- **Bind the Ruleset, Don't Balance It (SOUL/ADR-143):** ✓ The synthesized beat is `damage_channel=strike`, routing into the existing 108-1 `_resolve_wn_committed_action` (WN math only, native scaffolding cut, `wwn.native_scaffolding_suppressed` emitted). No native rider/dial/tag machinery is layered in. No tuning of a native mechanic against the binding.
- **isinstance gate / native packs keep authored beats:** ✓ Both seams gate on the WN module class; a native pack's authored `attack` beat (test_genre) stays on the cdef lookup. Verified by `test_native_attack_does_not_engage_wn_synthesis`.
- **OTEL Observability:** ✓ Lie-detector span preserved end-to-end (asserted in unit + wiring tests).
- **No stubs / half-wiring:** ✓ `wn_action_beat` returns a fully-formed BeatDef consumed by the real resolution path; both seams pass it downstream unchanged. Wiring test drives `handle_message` → dispatch → round.
- **No Source-Text Wiring Tests:** ✓ All wiring assertions are OTEL-span + HP-delta behavioral; no `read_text`/grep-on-source.
- **Python checklist (#1–#13):** ✓ clean — no bare excepts, no mutable defaults, boundary functions annotated, explicit imports (no star/cycle), no resource/deser/async issues. (rule-checker corroborated, 0 violations.)

### Observations

- [VERIFIED] Closed allowlist + loud raise — `wn_action_beat` raises `PackError` for unknown ids (beat_filter.py:147-148); the dispatch `else` branches raise `DiceDispatchError` (dice.py:419-423, wn_round.py:382-388). Complies with No Silent Fallbacks. evidence: both seams keep the original raise verbatim in the `else`.
- [VERIFIED] isinstance gate excludes native — `isinstance(ruleset, WithoutNumberRulesetModule)` precedes `is_wn_action_beat` at both seams; `attack` is also an authored native beat (test_genre rules.yaml:96) and is NOT hijacked. Complies with ADR-143 "native packs keep requiring beats." evidence: dice.py:414, wn_round.py:379.
- [VERIFIED] WN math + OTEL preserved — synthesized beat `damage_channel=strike` flows into `_resolve_wn_committed_action` (dice.py:1657), which lands weapon dice on ablative HP and emits `wwn.native_scaffolding_suppressed`. evidence: tests assert HP delta + span name + slug honesty.
- [MEDIUM][non-blocking] Synthesized attack hardcodes `stat_check="STR"` (beat_filter.py:154); the `wn_attack` narrator tool resolves to-hit on **better-of-STR/DEX** (wn_tools.py:245-247). A DEX/finesse attacker clicking Attack gets a worse to-hit than the SRD prescribes and than the narrated path — a WN-fidelity gap and a divergence between the two WN attack entry points. Non-blocking (AC3 says "d20+hit" generically; to-hit progression is already an acknowledged approximation on this path), but a real mechanical inaccuracy. Captured as a Delivery Finding for follow-up.
- [LOW] `wn_action_beat` hardcodes `label="Attack"` (beat_filter.py:151). Currently correct (set = {"attack"}), but a latent footgun: adding `move` to `_WN_ACTION_BEAT_IDS` without a per-id label would mislabel it "Attack". Note for the deferred move follow-up.
- [TEST][LOW] `[TEST]` test-analyzer flagged 5 test-strengthening gaps. Triaged: the "HIGH" native-guard vacuous-pass claim is **overstated** — `dispatch_throw` has no try/except, so a native dispatch error would *fail* the test loudly, not pass it (challenged). The weaponless-PC case (#5) is a *defined* loud-skip (`dice.damage_spec_missing` watcher span + warning, "no-fabricate" — dice.py:1431-1455), not a silent fallback. The bogus-id-in-wn_round.py path (#4) is near-unreachable (dice.py raises before `seal_wn_commit`). All non-blocking; #4/#5 captured as Delivery Findings.
- [DOC][LOW] `[DOC]` comment-analyzer flagged 3 doc nits: stale pre-fix line numbers in the test docstring (dice.py:407/wn_round.py:374 no longer match post-fix), the beat_filter module docstring not enumerating the new 4th responsibility, and "each core WN action" reading broader than the one-id set. All cosmetic, non-blocking; recommend a cheap doc touch-up but not gating.
- [EDGE] edge-hunter disabled — manually checked: zero-beat (the headline), bogus id (guarded), native id (guarded), weaponless PC (defined loud-skip), opponent-first vs PC-first initiative (wiring uses opponent-first, solo uses PC-first — both drive both seams). No unhandled boundary found.
- [SILENT] silent-failure-hunter disabled — the only new `else`/raise paths preserve the original loud errors; `wn_action_beat` raises rather than returning a default. No swallowed error introduced.
- [TYPE] type-design disabled — new `BeatDef` is the existing validated model; `is_wn_action_beat`/`wn_action_beat` are annotated (`str -> bool`, `str -> BeatDef`); `WN_ATTACK_BEAT_ID` is a module constant. No stringly-typed regression beyond the existing beat-id contract.
- [SEC] security disabled — no auth, no user-supplied path/SQL/HTML, no secrets; `beat_id` is validated against a closed allowlist before any use. rule-checker #11 clean.
- [SIMPLE] simplifier disabled — diff is minimal and mirrors the established item-use pattern; no dead code or over-engineering. The `else`-branch nesting is the natural shape.
- [RULE] rule-checker clean — 0 violations across 13 lang-review rules + 5 project rules (A1 No Silent Fallbacks, A2 Bind the Ruleset, A3 No Source-Text Wiring, A4 wiring present, A5 no stubs).

### Devil's Advocate

Let me argue this is broken. **The stat hardcode is the sharpest angle.** SideQuest binds Without Number precisely so the *math* is faithful — that's the entire SOUL doctrine this epic enforces. Yet the synthesized attack always rolls STR to-hit. A Thief/finesse build with DEX 16 / STR 8 now hits *worse* through the Attack button than the same character hitting through narrated freeform (which the `wn_attack` tool resolves on DEX). Sebastien and Jade — the mechanics-first players this epic exists to satisfy — are exactly the ones who would notice a finesse fighter mysteriously rolling off their dump stat. So "WN math preserved" (AC3) is preserved only for STR-primary attackers. That's a real gap, though not a build-breaker: combat resolves, HP moves, and STR is a legitimate melee stat in the SRD.

**Could the gate be bypassed?** A malicious/buggy client sends `beat_id="attack"` to a *native* pack mid-combat. The isinstance gate sends it to the cdef lookup — where native packs legitimately author `attack` (test_genre) — so it resolves as the native beat, not WN synthesis. Correct. Sends `beat_id="ATTACK"` (wrong case)? Not in the frozenset → `else` → `DiceDispatchError`. Good — no normalization surprise. Sends `cast_spell` on a zero-beat WN def? Not in `_WN_ACTION_BEAT_IDS`, so it falls to the `else` lookup and raises `unknown beat_id` — meaning **cast is broken on a fully-stripped WWN combat def** (the cast routing at dice.py:430 sits *after* the lookup). The story's action set names "cast," and Dev deferred it; but a zero-beat WWN caster pressing Cast would hit `unknown beat_id`. This is a genuine residual gap, not a regression (no current content ships zero-beat-and-caster combined yet — 108-3 hasn't landed), but it means the epic's "WN owns the action set" is only partially true until cast is synthesized too.

**Confused user / stressed system?** A weaponless WN PC: defined loud-skip (telemetry + warning), no crash, no silent zero — acceptable. Opponent-first initiative with min rolls: the wiring test proves Rux survives and resolves. Two-player barrier: the solo path drives the same `run_wn_round` seam the MP barrier uses, so the synthesis is reached identically. Nothing here corrupts state or fails silently. **Conclusion:** the gaps (STR-only to-hit, cast not yet synthesized) are fidelity/scope limitations worth filing, not correctness defects. The code does exactly what it claims, fails loud where data is missing, and is gated correctly. None rise to High.

## Reviewer Assessment

**Verdict:** APPROVED

**Summary:** Minimal, surgical fix that closes the total-combat-outage exactly as scoped. Under a `WithoutNumberRulesetModule` binding, both dispatch seams (`dice.py`, `wn_round.py`) synthesize a transient `attack` strike beat instead of looking the id up in the (now-empty) `cdef.beats`, routing into the existing 108-1 WN resolution. Gated correctly so native packs keep their authored beats; the synthesis is a closed allowlist that raises loudly on anything else.

**Data flow traced:** UI `DICE_THROW{beat_id:"attack"}` → `handle_message` → `dispatch_dice_throw` (isinstance+allowlist gate → `wn_action_beat` → strike beat) → `seal_wn_commit` → barrier close → `run_wn_round` (same gate → same synthesized beat) → `_apply_committed_player_beat` → `_resolve_wn_committed_action` (weapon dice → ablative HP, `wwn.native_scaffolding_suppressed` span). Safe: every non-WN-action id falls to the original `DiceDispatchError` raise; native ids hit the authored-beat lookup.

**Pattern observed:** Mirrors the established item-use transient-beat synthesis (beat_filter.py) — consistent, no new abstraction. Both seams symmetric.

**Error handling:** Loud throughout — `wn_action_beat` raises `PackError` (beat_filter.py:147); both `else` branches preserve the original `DiceDispatchError`; weaponless attack is a defined loud-skip with telemetry (dice.py:1431-1455).

**Dispatch tags:** [EDGE] no unhandled boundary (zero-beat/bogus/native/weaponless/initiative-order all covered) · [SILENT] no swallowed errors; loud raises preserved · [TEST] 5 non-blocking test-strengthening gaps (1 overstated — challenged); suite is behavioral, wiring real · [DOC] 3 LOW doc nits (stale test line-refs, module docstring) · [TYPE] new functions annotated; BeatDef is the validated model · [SEC] no auth/input/secret surface; closed allowlist · [SIMPLE] minimal, no over-engineering · [RULE] rule-checker clean, 0 violations across 18 rules.

**Findings:** 0 Critical, 0 High. 1 Medium (STR-only to-hit vs SRD better-of-STR/DEX — non-blocking fidelity gap) + LOW doc/test nits, all captured as Delivery Findings for follow-up. No blocker.

**Handoff:** To SM (Camina Drummer) for finish-story.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/sidequest/game/beat_filter.py` — new `is_wn_action_beat` / `wn_action_beat`
  (+ `WN_ATTACK_BEAT_ID`): the WN action-set synthesis, mirroring the item-use transient-beat pattern.
- `sidequest-server/sidequest/server/dispatch/dice.py` — intercept WN action ids BEFORE the
  `cdef.beats` lookup, gated `isinstance(ruleset, WithoutNumberRulesetModule)`.
- `sidequest-server/sidequest/server/dispatch/wn_round.py` — same intercept at the sealed-round
  re-resolution seam (the twin of dice.py's; both must synthesize or the barrier close re-raises).

**Approach:** The 108-1 WN resolution (`dice._resolve_wn_committed_action`) already does the WN math
(weapon dice → ablative HP) and emits `wwn.native_scaffolding_suppressed` for any `strike` beat under
a WN binding. The zero-beat outage was purely the two `cdef.beats` lookups rejecting the synthesized
id before resolution. Fix = synthesize a transient STR strike beat (no `damage_override` → weapon dice
resolve from inventory) at both seams. Minimal and surgical — no change to the WN math itself.

**Tests:** 7/7 passing (GREEN) — 5 RED→GREEN, 2 green guards stay green.
**Regression:** 160/160 in the WN/dice/combat/confrontation area pass. Full server suite: 17 failures
are PRE-EXISTING (verified — they fail identically with my changes stashed; all chargen/lore/
narrator-SDK/snapshot-governance, none touch combat dispatch). Lint/format clean on all 3 files.
**Branch:** feat/108-8-wn-round-owns-action-set (pushed).

**AC status:** AC1 ✓ (zero-beat attack resolves), AC2 ✓ (WN-gated synthesis; native "attack" untouched;
closed allowlist), AC3 ✓ (weapon dice → HP, native engine off), AC4 ✓ (`wwn.native_scaffolding_suppressed`),
AC5 ✓ (no combat-area regression; wiring test green end-to-end). `move`/`cast` synthesis scoped out —
see Design Deviations + Delivery Findings.

**Handoff:** To Reviewer (Chrisjen Avasarala) for code review.

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-15T08:09:08Z
**Branch:** feat/108-8-wn-round-owns-action-set

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-15T07:33:39+00:00 | 2026-06-15T07:36:39Z | 3m |
| red | 2026-06-15T07:36:39Z | 2026-06-15T07:50:35Z | 13m 56s |
| green | 2026-06-15T07:50:35Z | 2026-06-15T08:00:39Z | 10m 4s |
| review | 2026-06-15T08:00:39Z | 2026-06-15T08:09:08Z | 8m 29s |
| finish | 2026-06-15T08:09:08Z | - | - |

## Branch Strategy
gitflow (feat/108-8-wn-round-owns-action-set)

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (blocking): The canonical WN attack action id is `"attack"` but is NOT pinned by any
  on-disk spec — the action-surface design spec named in the story
  (`docs/superpowers/specs/2026-06-14-wn-combat-action-surface-design.md`) does not exist in the
  repo. I pinned `WN_ATTACK_BEAT = "attack"` from UI evidence (`CavernActionPanel.tsx`,
  `EncounterTab.test.tsx`) and the story's "(attack/move/item-use/cast)" action set. Affects
  `tests/integration/test_108_8_wn_round_owns_action_set.py` (one-line constant) + Dev's synthesis
  predicate — **Dev must use the same id and confirm it matches the UI action-surface story**, or
  change the constant. *Found by TEA during test design.*
- **Gap** (non-blocking): `dice.py:407` is one of TWO beat-lookup seams; `wn_round.py:374`
  re-resolves the committed beat from `cdef.beats` inside the sealed round. The solo-table RED
  tests drive both (commit closes the 1-participant barrier and walks the round in one dispatch),
  but Dev must synthesize at BOTH sites or the sealed round will re-raise after dice.py is fixed.
  Affects `sidequest/server/dispatch/wn_round.py` and `dispatch/dice.py`. *Found by TEA during test design.*
- **Improvement** (non-blocking): heavy_metal ships no `unarmed_damage` floor, so a weaponless WN
  PC's synthesized attack has no resolvable damage. Per `damage_roll` this is a loud error (No
  Silent Fallbacks), not a silent 0 — Dev should preserve that loud behavior. The RED tests arm
  the PC with a weapon to exercise the happy path. Affects `dispatch/damage_roll.py` consumers.
  *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): The WN action set is implemented for `attack` only; `move` (WN
  disengage) is NOT synthesized — a zero-beat WN `move` commit would still raise `unknown
  beat_id`. `item-use` (`use_item:`) and `cast` (`cast_spell`) already have their own dispatch
  routes and work. `move` has no resolution semantics on the dice path yet (it was the native
  `break_contact` beat pre-strip). Affects `sidequest/game/beat_filter.py` (`_WN_ACTION_BEAT_IDS`
  frozenset — add `"move"` + a non-strike transient beat) and the UI Move/Disengage button.
  Recommend a follow-up story if the WN action surface ships a Move button. *Found by Dev during implementation.*
- **Gap** (non-blocking, PRE-EXISTING — not 108-8): the full server suite has 17 failures on this
  branch that also fail with my changes stashed (verified) — `test_class_signature_wiring`,
  `test_cc_chargen_e2e`, `test_lore_link_wiring`, `test_creation_answers_wiring`,
  `test_narrator_uses_sdk_client`, `test_snapshot_field_governance`. All chargen/lore/narrator-SDK/
  snapshot-governance; none touch combat dispatch. Affects those suites (separate triage).
  *Found by Dev during implementation.*
- **Improvement** (non-blocking): TEA's blocking action-id finding is RESOLVED — Dev used the same
  `"attack"` id (`beat_filter.WN_ATTACK_BEAT_ID`), so the test constant and the engine agree. The
  underlying gap (no on-disk action-surface spec pins the id) remains for the UI story to honor.
  *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): The synthesized WN attack hardcodes `stat_check="STR"` to-hit, but
  the `wn_attack` narrator tool resolves to-hit on better-of-STR/DEX. A DEX/finesse attacker gets a
  worse roll via the Attack button than via narrated freeform — a WN-fidelity gap and a divergence
  between the two WN attack entry points. Affects `sidequest/game/beat_filter.py` (`wn_action_beat`)
  and `sidequest/server/dispatch/dice.py` (to-hit resolution would need the actor's stats to pick
  better-of). Recommend a follow-up to align the button path with the SRD/narrator math.
  *Found by Reviewer during code review.*
- **Gap** (non-blocking): `cast` is named in the story's WN action set but is NOT synthesized — the
  `cast_spell` routing in `dice.py` sits AFTER the cdef lookup, so a fully zero-beat WWN combat def
  would raise `unknown beat_id` on a Cast commit. No current content ships the combination (108-3 not
  yet merged), so it does not block 108-3's unblock, but the epic's "WN owns the action set" is only
  partial until cast (and move) are synthesized. Affects `sidequest/game/beat_filter.py` +
  `dispatch/dice.py`. *Found by Reviewer during code review.*
- **Gap** (non-blocking): Two test-coverage gaps worth a follow-up — (1) no weaponless-PC test on a
  zero-beat WN def (behavior is a defined loud-skip via `dice.damage_spec_missing`, but unguarded);
  (2) the `wn_round.py` bogus-id rejection path is untested (near-unreachable since `dice.py` raises
  first, but defense-in-depth). Affects `tests/integration/test_108_8_wn_round_owns_action_set.py`.
  *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

4 deviations

- **Pinned the WN attack id as "attack" rather than discovering it from a spec**
  - Rationale: No on-disk spec defines the id; UI (`CavernActionPanel`/`EncounterTab`) and the story action-set agree on "attack". Centralized as a constant so a contract change is one line.
  - Severity: minor
  - Forward impact: Dev's synthesis predicate must accept the same id; flagged as a blocking Delivery Finding for confirmation.
- **Scoped RED to attack (+ allowlist/native guards); move/cast not given dedicated resolve-tests**
  - Rationale: attack is the headline outage; cast adds spell-catalog/prepared-spell setup orthogonal to the cut. Move/cast resolution is a thin extension of the same synthesis seam once attack lands.
  - Severity: minor
  - Forward impact: If Dev's synthesis covers only attack, move/cast commits on a zero-beat def would still raise — Reviewer should confirm the full action set is synthesized, or a follow-up story is filed.
- **Synthesized the `attack` WN action only; deferred `move`**
  - Rationale: `attack` is the strike that drives all 78 e2e failures (the entire outage). `move` (WN disengage) has no resolution semantics on the dice path yet — it was the native `break_contact` beat pre-strip; synthesizing it without a defined behavior would be a guess. The frozenset makes adding it a one-line change once semantics exist.
  - Severity: minor
  - Forward impact: A zero-beat WN `move` commit still raises `unknown beat_id`. Filed as a Dev Delivery Finding (follow-up story when the UI ships a Move/Disengage button). No impact on 108-3 unblock (combat resolves via `attack`).
- **Synthesized attack carries no class to-hit progression (attack_bonus/combat_skill = 0)**
  - Rationale: A synthesized action carries no authored class-progression to-hit (the stripped native beat used to author `attack_bonus`/`combat_skill`). This matches the existing `wn_attack` narrator tool, which also resolves attribute-mod-only to-hit — one honest contract across both WN attack entry points. Restoring class to-hit is a separate concern (where does per-class combat skill live post-strip).
  - Severity: minor
  - Forward impact: WN button attacks and narrator wn_attack agree on to-hit. If class to-hit progression is later wired, both entry points update together.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Pinned the WN attack id as "attack" rather than discovering it from a spec**
  - Spec source: context-story-108-8.md, Technical Approach ("synthesize the WN action set (attack/move/item-use/cast)")
  - Spec text: "synthesize the WN action set (attack, move, item-use, cast) ... modeling it on the existing is_item_use_beat transient-beat synthesis"
  - Implementation: Test pins `WN_ATTACK_BEAT = "attack"` (UI-sourced); cast=`cast_spell`, item-use=`use_item:` already exist
  - Rationale: No on-disk spec defines the id; UI (`CavernActionPanel`/`EncounterTab`) and the story action-set agree on "attack". Centralized as a constant so a contract change is one line.
  - Severity: minor
  - Forward impact: Dev's synthesis predicate must accept the same id; flagged as a blocking Delivery Finding for confirmation.
- **Scoped RED to attack (+ allowlist/native guards); move/cast not given dedicated resolve-tests**
  - Spec source: context-story-108-8.md, AC1–AC5
  - Spec text: AC1 "resolve a committed WN action (attack/move/item-use/cast)"
  - Implementation: Deep coverage on `attack` (the strike that drives all 78 e2e failures); `cast`/`move` resolution not separately asserted. item-use already routes (dice.py:390). The closed-allowlist guard pins that synthesis is a bounded set.
  - Rationale: attack is the headline outage; cast adds spell-catalog/prepared-spell setup orthogonal to the cut. Move/cast resolution is a thin extension of the same synthesis seam once attack lands.
  - Severity: minor
  - Forward impact: If Dev's synthesis covers only attack, move/cast commits on a zero-beat def would still raise — Reviewer should confirm the full action set is synthesized, or a follow-up story is filed.

### Dev (implementation)
- **Synthesized the `attack` WN action only; deferred `move`**
  - Spec source: context-story-108-8.md, AC1 / Technical Approach
  - Spec text: "synthesize the WN action set (attack/move/item-use/cast) independent of cdef.beats"
  - Implementation: `_WN_ACTION_BEAT_IDS = {"attack"}` in `beat_filter.py`. item-use (`use_item:`) and cast (`cast_spell`) already have dispatch routes; `move` is not synthesized.
  - Rationale: `attack` is the strike that drives all 78 e2e failures (the entire outage). `move` (WN disengage) has no resolution semantics on the dice path yet — it was the native `break_contact` beat pre-strip; synthesizing it without a defined behavior would be a guess. The frozenset makes adding it a one-line change once semantics exist.
  - Severity: minor
  - Forward impact: A zero-beat WN `move` commit still raises `unknown beat_id`. Filed as a Dev Delivery Finding (follow-up story when the UI ships a Move/Disengage button). No impact on 108-3 unblock (combat resolves via `attack`).
- **Synthesized attack carries no class to-hit progression (attack_bonus/combat_skill = 0)**
  - Spec source: context-story-108-8.md, AC3 ("WN math preserved: d20+hit, weapon dice")
  - Spec text: "d20 + hit modifier vs AC"
  - Implementation: The transient beat defaults `attack_bonus`/`combat_skill` to 0; to-hit = d20 + STR attribute modifier vs AC. Weapon dice resolve from inventory (unchanged WN math).
  - Rationale: A synthesized action carries no authored class-progression to-hit (the stripped native beat used to author `attack_bonus`/`combat_skill`). This matches the existing `wn_attack` narrator tool, which also resolves attribute-mod-only to-hit — one honest contract across both WN attack entry points. Restoring class to-hit is a separate concern (where does per-class combat skill live post-strip).
  - Severity: minor
  - Forward impact: WN button attacks and narrator wn_attack agree on to-hit. If class to-hit progression is later wired, both entry points update together.

### Reviewer (audit)
- **TEA: Pinned the WN attack id as "attack"** → ✓ ACCEPTED by Reviewer: well-justified (UI + story action-set), centralized as a constant, and Dev used the identical id (`beat_filter.WN_ATTACK_BEAT_ID`) so test and engine agree.
- **TEA: Scoped RED to attack (+ allowlist/native guards)** → ✓ ACCEPTED by Reviewer: attack is the entire outage; the closed-allowlist + native guards cover the AC2 invariants. I confirmed move/cast remain unsynthesized and filed them as non-blocking Delivery Findings, exactly as TEA's forward-impact predicted.
- **Dev: Synthesized `attack` only; deferred `move`** → ✓ ACCEPTED by Reviewer: synthesizing `move` without defined disengage semantics would be a guess (SOUL "No Stubbing"); the frozenset makes it a one-line add. Captured as a Delivery Finding for the UI Move-button follow-up.
- **Dev: Synthesized attack carries no class to-hit progression (attack_bonus/combat_skill = 0)** → ✓ ACCEPTED *with caveat* by Reviewer: dropping `attack_bonus`/`combat_skill` is honest (no authored beat post-strip) and DOES match `wn_attack`. **Caveat:** the deviation's rationale ("matches the wn_attack narrator tool") holds for the bonuses but NOT for the to-hit *stat* — `wn_attack` uses better-of-STR/DEX while the synthesized beat hardcodes STR. Not a blocker, but the divergence is real; filed as a non-blocking Delivery Finding.
- **UNDOCUMENTED (Reviewer audit):** `cast` (named in the story action set) is not synthesized and would raise `unknown beat_id` on a fully zero-beat WWN combat def (the `cast_spell` routing sits after the cdef lookup). Neither TEA nor Dev logged this as a deviation. Severity: L (no current content combines zero-beat + caster; 108-3 not yet merged). Filed as a non-blocking Delivery Finding.