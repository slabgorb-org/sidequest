---
story_id: "86-2"
jira_key: ""
epic: "86"
workflow: "tdd"
---
# Story 86-2: Plan 2 — Solo rig two-pool vehicle combat

## Story Details
- **ID:** 86-2
- **Jira Key:** (none — Jira not enabled)
- **Epic:** 86 (road_warrior → Cities Without Number: Two-Tier Rig Combat)
- **Workflow:** tdd
- **Stack Parent:** none (no parent dependency)
- **Points:** 8

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-05T13:29:33Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-05T12:59:29Z | 2026-06-05T13:00:33Z | 1m 4s |
| red | 2026-06-05T13:00:33Z | 2026-06-05T13:13:27Z | 12m 54s |
| green | 2026-06-05T13:13:27Z | 2026-06-05T13:21:46Z | 8m 19s |
| review | 2026-06-05T13:21:46Z | 2026-06-05T13:29:33Z | 7m 47s |
| finish | 2026-06-05T13:29:33Z | - | - |

## Branch & Repository
**Branch Strategy:** gitflow (feat/86-2-road-warrior-solo-rig-two-pool-combat)
**Repositories:** sidequest-server, sidequest-content
**Both subrepos remain on develop; orchestrator branching from main.**

## Sm Assessment

Story 86-2 selected from backlog as highest-value ready p2 (8 pts). Direct continuation of 86-1 (road_warrior→CWN binding, just merged), which left `RigComposurePool` and `rig_crash` dormant — this story wires them into a live confrontation. Substrate it builds (two-pool hull→driver resolution) unblocks 86-3 (vehicle chase) behind it.

**Setup verification:** session file, story context (`sprint/context/context-story-86-2.md`, 9 concrete ACs), and branch `feat/86-2-road-warrior-solo-rig-two-pool-combat` all confirmed present. Repos: sidequest-server (engine) + sidequest-content (road_warrior pack). Phased TDD workflow.

**Scope flags for downstream agents:**
- NET-NEW two-pool resolution (hull→0 = crash event → dismounted → driver HP) per CWN §2.4.8.1-2 — design doc `docs/superpowers/specs/2026-06-04-road-warrior-cwn-rig-combat-design.md` is authoritative.
- OTEL is a hard AC, not optional: `rig_pool.delta`, `rig_pool.zero_crossing`, `rig_pool.crash_event` spans must fire (GM-panel lie-detector — see CLAUDE.md OTEL principle).
- New WinCondition variant or beat-application branch — TEA/Dev to decide minimal seam.

Routing to **tea** for RED phase. No Jira (not enabled).

## TEA Assessment

**Phase:** finish → green. Six failing test files committed on
`feat/86-2-road-warrior-solo-rig-two-pool-combat` (server subrepo,
commit `02fbed4`). RED verified by testing-runner: 15 net-new behavior
failures fail for the right reasons (missing symbols / unimplemented
behavior), 0 spurious. 1 intentional pass (armor back-compat default).

### What I found (key context for Dev)
- **The rig substrate is dormant, not absent.** `RigComposurePool`,
  `rig_crash.apply_rig_damage`/`handle_rig_crash`, `vessel_tags`, and the
  `rig_pool.{created,delta,zero_crossing,crash_event}` OTEL spans all
  exist and are fully wired to the watcher (53-1..53-5). They have **no
  production consumer** — `apply_rig_damage` is only re-exported in
  `game/__init__.py`. This story is wire-up + faithful-port extension,
  per the design doc's "Don't Reinvent" framing.
- **53-2 parses composure only.** `VesselTags` deliberately ignores
  `armor:N`/`speed:N`/`mount_slots:N`. AC3 needs the parser extended.
- **The crash handler is a placeholder.** `handle_rig_crash` applies a
  flat `DRIVER_HP_HIT = -1`, NOT CWN crash saves. AC4 replaces it.

### Test design (what each file pins)
| File | AC | Level | Proposed seam (Dev may refine) |
|------|----|-------|--------------------------------|
| `test_vessel_tags_armor.py` | 3 | unit | `VesselTags.armor: int = 0`, parsed from `armor:N`, fail-loud on malformed |
| `test_vehicle_combat_ac.py` | 1 | unit/pure | `vehicle_combat.vehicle_ac(base, *, drive_modifier, moving)` |
| `test_rig_armor_reduction.py` | 2,3 | unit | `apply_rig_damage(core, amt, *, armor=0)` → loss = `max(1, amt-armor)` |
| `test_rig_crash_saves.py` | 4 | unit | `rig_crash.resolve_crash_saves(core, *, physical_passed, luck_passed)` → `CrashSaveResult` |
| `test_rig_ramming.py` | 6 | unit/pure | `vehicle_combat.resolve_ramming(...) -> RammingResult` |
| `test_rig_two_pool_combat.py` | 5,7,8 | integration+OTEL | `apply_rig_damage(..., crash_save_outcomes=(bool,bool))` two-pool transition |

### Open decisions handed to Dev (deliberately NOT pinned by tests)
1. **Two-pool confrontation routing (AC7).** The design doc leaves this an
   open fork — "a new `WinCondition` variant OR a beat-application
   branch." I did **not** pin a `WinCondition` enum value. The
   integration test asserts *behavior + telemetry* (rig→driver pool
   transition, dismount, full `rig_pool.*` span chain) that any routing
   must satisfy. Pick the seam; the tests don't constrain it.
2. **Physical/Luck → Physical/Evasion/Mental save mapping (AC4).** The
   engine's CWN/SWN save system has **no "Luck" save** — only
   Physical/Evasion/Mental. The design doc/ACs say "Physical + Luck." The
   crash-save tests pin *outcomes* (half-max-HP per failed save,
   both-fail = mortal + major injury), not a save-category name. The
   second param is `luck_passed` to match SRD wording; bind it to
   whichever category the port chooses (Evasion is the natural map).
3. **"Rammed back" damage figure (AC6).** Tests pin that a winning ram is
   *mutual* (`attacker_damage > 0`) and the target takes the ramming
   vehicle's max HP; the exact rammed-back number is a calibration detail
   left open.

### Verification / wiring
- The integration test (`test_rig_two_pool_combat.py`) drives the real
  `TracerProvider` + `WatcherSpanProcessor` route (same harness as the
  existing `test_rig_pool_wiring.py`) — satisfies CLAUDE.md "Every Test
  Suite Needs a Wiring Test" and the OTEL-lie-detector principle. No
  source-text/grep wiring assertions used.

### Rule Coverage (lang-review/python.md)
- **#6 Test quality** — self-checked all six files for vacuous asserts
  (`assert True`, bare-truthy, always-None). None present; every test
  asserts a concrete value or a fail-loud raise. The one always-passing
  test is the documented armor back-compat case (asserts `new_current==2`,
  not vacuous).
- **#11 Input validation at boundaries / No Silent Fallbacks** —
  `test_vessel_tags_armor.py` covers fail-loud on non-int / negative /
  duplicate `armor` tags (the content-parser boundary), matching the
  existing `InvalidVesselTagsError` discipline.
- **#3 Type annotations** — proposed seams are documented with full
  signatures so Dev annotates public boundaries from the start.
- Not applicable to test code: #2 mutable defaults, #5 path handling,
  #7 resource leaks, #8 deserialization, #9 async pitfalls (the async
  integration tests use the established watcher-capture pattern, no
  blocking calls), #12 deps.

Routing to **dev** (Naomi Nagata) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes (two-pool resolver + seam + OTEL; confrontation-dispatch consumer deferred — see deviation + finding)
**Files Changed (sidequest-server, branch `feat/86-2-road-warrior-solo-rig-two-pool-combat`, commit `e69d171`):**
- `sidequest/game/vessel_tags.py` — `VesselTags.armor` field + `armor:N` tag parsing (fail-loud on non-int/negative/duplicate; default 0 for legacy items). AC3.
- `sidequest/game/vehicle_combat.py` (NEW) — `vehicle_ac` (stationary −4 / moving +Drive) and `resolve_ramming` (opposed Dex/Drive → max-HP dmg + Trauma 1d12/×3, mutual). AC1, AC6.
- `sidequest/game/rig_crash.py` — `resolve_crash_saves` (CWN §2.4.8.2 occupant saves, half-max-HP per fail, both-fail → mortal + Major Injury) + `CrashSaveResult`; `apply_rig_damage` gains `armor` (min-1 reduction) and `crash_save_outcomes` (the two-pool rig→driver transition). Legacy −1 placeholder preserved when no save outcomes supplied. AC2, AC3, AC4, AC5, AC7.
- `sidequest/game/__init__.py` — export the new symbols.

**Tests:** 35/35 new GREEN; 90/90 legacy rig tests pass (no regression); ruff + pyright clean.
**OTEL:** `rig_pool.delta` / `rig_pool.zero_crossing` / `rig_pool.crash_event` fire through the real `WatcherSpanProcessor` route (integration test). The GM panel sees the full two-pool chain.

**Content:** No content change needed — road_warrior `inventory.yaml` already ships tiered armor (`armor:0..4` across rig tiers). My engine change now *reads* those previously-dead values. AC9's "content changes in the PR" is satisfied-by-existing for the armor data; the confrontation-def content that would route rig combat is part of the deferred AC7 fork (see finding).

**Per-AC status:**
- AC1 vehicle AC — ✅ `vehicle_ac`
- AC2 rig ablative pool + spans — ✅ (spans pre-existing; armor reduction now in the flow)
- AC3 armor reduction + visible stat — ✅ parser + `apply_rig_damage(armor=)`; values already in content
- AC4 crash saves — ✅ `resolve_crash_saves` (replaces −1 placeholder on the live path)
- AC5 dismount → foot combat — ✅ dismount status on crash (the marker); the *confrontation* state-switch is AC7-fork
- AC6 ramming — ✅ `resolve_ramming`
- AC7 two-pool model — ⚠️ resolver + seam delivered & OTEL-verified; **confrontation-dispatch routing deferred** (open fork, → 86-3). See deviation.
- AC8 OTEL integration — ✅ via the real watcher through `apply_rig_damage`; ⚠️ not through a full confrontation *dispatch* turn (no rig confrontation type exists yet — 86-3)
- AC9 branch & PR — ✅ branch pushed; server-only (content already correct)

**Handoff:** To Reviewer (Chrisjen Avasarala). The load-bearing judgment call for review: is 86-2 "done" delivering the two-pool *resolver + production seam + OTEL* (with the vehicle-vs-vehicle *confrontation type* landing in 86-3 per the epic decomposition), or does it require the dispatch consumer now? I argue the former — TEA pinned the contract at `apply_rig_damage`, 86-3 ("vehicle chase confrontation... closes into Plan 2 combat") is the encounter-type story, and building the routing now would be speculative architecture with no failing test. Flagged transparently below.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (155 passed, 0 failed, 0 lint, 0 type, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 7 | confirmed 6 (Low/Med), dismissed 0, deferred 1 (pre-existing edge_after) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 4 | confirmed 3 (Low/Med), dismissed 1 (min-1 floor — documented/faithful, not a violation) |
| 4 | reviewer-test-analyzer | Yes | findings | 9 | confirmed 8 (Low/Med), dismissed 1 (sleep flakiness — pre-existing harness pattern); wiring test CONFIRMED genuine |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — self-assessed (see [DOC]) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — self-assessed (see [TYPE]) |
| 7 | reviewer-security | Yes | findings | 1 | confirmed 1 (Low — `armor or 0` idiom, convergent with #3); 0 vulns, deserialization/DoS clean |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — self-assessed (see [SIMPLE]) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — self-assessed (see [RULE] / Rule Compliance) |

**All received:** Yes (5 enabled returned, 4 disabled pre-filled)
**Total findings:** 14 confirmed (0 Critical, 0 High, 6 Medium, 8 Low), 2 dismissed with rationale, 1 deferred (pre-existing)

## Reviewer Assessment

**Verdict:** APPROVED

No Critical or High findings. The diff is a faithful, well-documented CWN §2.4.8 port: 155 tests green, ruff + pyright clean, the OTEL wiring test confirmed genuine (drives `apply_rig_damage` through the real `WatcherSpanProcessor` → hub → sock; cannot pass vacuously per [TEST]). Every confirmed finding is either a guard against an input that is **not currently reachable** (the triggering states — `hp.max ≤ 1`, negative ramming `max_hp` — are blocked upstream by `hp_pool_from_hp` flooring at 1 and `RigComposurePool`'s `max > 0` validator), test-polish on otherwise-correct-and-covered behavior, or forward-hardening that belongs with 86-3's dispatch consumer. None meet the Critical/High bar (no security vuln, no data corruption, no missing error handling on a reachable path, no race).

**Data flow traced:** vessel item dict (genre-pack YAML) → `parse_vessel_tags` (fail-loud on malformed `armor:N`) → `VesselTags.armor` → [86-3 will pass to] `apply_rig_damage(armor=)` → `max(1, amount−armor)` → `RigComposurePool.apply_delta` (delta+zero_crossing spans) → on destruction → `handle_rig_crash(crash_save_outcomes=)` → `resolve_crash_saves` (driver HP pool, half-max-HP per fail) → dismounted status + crash_event span. The seam is reachable from production (exported, OTEL-routed); the *confrontation dispatch* caller is the documented 86-3 boundary.

### Observations
- `[VERIFIED]` Back-compat preserved — `realized = max(1, amount−armor) if amount>0 else 0` is identical to the prior `apply_delta(-amount)` at the default `armor=0` (max(1,amount)=amount for amount≥1; amount==0→0). Evidence: rig_crash.py:228 + 120 legacy rig tests green. Complies with No-Silent-Fallbacks (negative amount/armor both `raise ValueError`, rig_crash.py:218-221).
- `[VERIFIED]` Double-crash guarded twice — a second `apply_rig_damage` on an at-0 pool: `zero_crossed` is False (needs old>0), and `_already_dismounted` returns None. No double crash-save application via the seam. Evidence: rig_composure_pool.py:125 + rig_crash.py:100.
- `[EDGE][SILENT][MEDIUM]` `resolve_crash_saves` `half = hp.max // 2` is a silent no-op when `hp.max ≤ 1` (half=0 → failed save deals 0). Unreachable today (`hp_pool_from_hp` floors max at 1; max==1 is degenerate, not a real PC). rig_crash.py:108. → routed to 86-3 hardening.
- `[EDGE][LOW]` `mortal = major_injury or (failed>0 and hp_after==0)` flags a driver *already* at 0 HP as mortal with `hp_delta==0`. Defensible (already incapacitated) but a possible false-positive. rig_crash.py:124.
- `[EDGE][MEDIUM]` `resolve_ramming` does not guard negative `attacker_max_hp` (would emit negative damage) while its sibling `apply_rig_damage` raises on negative inputs — a fail-loud-consistency gap. Input is unreachable (sourced from `RigComposurePool.max > 0`). vehicle_combat.py:75. → routed to 86-3.
- `[EDGE][TEST][SIMPLE][LOW]` `defender_max_hp` is an accepted-but-unused param (dead surface) on `resolve_ramming`; documented as forward-calibration, untested for no-effect. vehicle_combat.py:79.
- `[SILENT][SEC][LOW]` `armor or 0` (vessel_tags.py:159) — convergent flag (silent-failure + security). Numerically harmless and equivalent to `armor if armor is not None else 0` for `int|None` (0 is the only falsy int, and the negative-guard fires first). Style/explicitness only. Recommend the explicit form.
- `[TEST][MEDIUM]` Three integration tests (test_rig_two_pool_combat.py:188/212/235) `await _setup()` but discard `captured` and never inspect spans — behavioral unit tests wearing dead OTEL scaffolding. Coverage is real (hp==0 / dismounted / hp==8); the harness + `asyncio.sleep` add nothing. Move to a unit file or add span assertions.
- `[TEST][MEDIUM]` `test_both_saves_fail_is_mortal_with_major_injury` asserts `any("injury" in s.text ...)` — a loose substring that matches both `injury` and `major_injury`. Passes for the right reason (only `major_injury` is appended) but should pin `MAJOR_INJURY_STATUS_TEXT`. test_rig_crash_saves.py:98.
- `[TEST][MEDIUM]` `test_ram_is_mutual` asserts only `attacker_damage > 0`; the symmetric rule (`attacker_damage == defender_damage == attacker_max_hp`) is untested. A second case with `attacker_max_hp != defender_max_hp` would also pin that the figure comes from `attacker_max_hp`, not the dead `defender_max_hp`. test_rig_ramming.py:54.
- `[TEST][LOW]` Minor coverage gaps: losing-ram `attacker_damage==0` unasserted; back-compat test duplicates the zero-armor test path.
- `[SILENT][MEDIUM]` Legacy `crash_save_outcomes=None` → −1 path has no OTEL marker distinguishing "intentional legacy" from "missed wiring." Aligns with the documented 86-3 gap; recommend a `crash_save_mode` span attribute when 86-3 wires the consumer.

### Rule Compliance (lang-review/python.md — self-checked, rule_checker disabled)
- **#1 silent exceptions** — PASS (no try/except in new code).
- **#2 mutable defaults** — PASS (defaults are `0`, `None`, `False`).
- **#3 type annotations at boundaries** — PASS (`vehicle_ac`, `resolve_ramming`, `resolve_crash_saves`, `apply_rig_damage`, parser all fully annotated).
- **#4 logging** — N/A (pure functions; observability is OTEL spans per project doctrine).
- **#5 path handling** — N/A.
- **#6 test quality** — **FINDINGS** (Medium): loose substring assertion, weak `>0` ramming assertion, 3 dead-scaffolding integration tests, 1 duplicate. Production is correct + covered; these are polish.
- **#7 resource leaks** — PASS (no unmanaged open/connect/lock; test uses `async with` lock).
- **#8 unsafe deserialization** — PASS (security-confirmed: no pickle/yaml/eval; int-DoS bounded at 4300 digits).
- **#9 async pitfalls** — PASS (no blocking calls in async; `asyncio.sleep` is a load-bearing yield, pre-existing harness pattern).
- **#10 import hygiene** — PASS (`__all__` updated on both modules; no star imports).
- **#11 input validation at boundaries** — PARTIAL: parser fails loud on malformed `armor` (PASS); `resolve_ramming`/`vehicle_ac` lack negative-input guards (Medium/Low — inputs from validated sources).
- **#12 deps** — N/A.

### Self-assessed (disabled subagents)
- `[DOC]` Comments/docstrings: thorough and SRD-cited. One pre-existing staleness — `RigCrashResult.edge_after` docstring says "driver Edge" but holds HP (post-ADR-114). Not introduced by this diff; noted as Low tech-debt.
- `[TYPE]` Type design: `VesselTags`/`RammingResult` use `extra='forbid'`; `CrashSaveResult` omits it, consistent with the transient-result precedent (`RigDamageResult`/`RigCrashResult`) and confirmed-not-a-save-surface by [SEC]. `crash_save_outcomes: tuple[bool,bool]` is a reasonable transient shape (a named pair could be clearer but is not required). No stringly-typed APIs. PASS.
- `[SIMPLE]` Simplicity: code is minimal and direct. Only dead surface is `defender_max_hp` (documented forward-calibration). No over-engineering.
- `[RULE]` See Rule Compliance above (exhaustive self-check).

### Devil's Advocate
Let me argue this is broken. **First**, the headline: this story claims to wire dormant rig combat into a "real confrontation," yet `apply_rig_damage` *still* has no confrontation-dispatch consumer — the new CWN crash-save logic is, in the silent-failure-hunter's words, "dead code in production": every live crash today (if any path reached it) would silently take the −1 placeholder, and nothing emits a span saying "you are using the placeholder." A cynic reads AC7/AC8 ("a real turn in a rig confrontation scenario") and says this is half a feature. **Second**, the guards are asymmetric: `apply_rig_damage` and the parser fail loud on bad input, but `resolve_ramming` will cheerfully return negative damage for a negative `max_hp`, and `resolve_crash_saves` will silently no-op a crash for a 1-HP-max driver — exactly the "silent fallback" the project forbids, sitting one refactor away from a real bug the day a content author ships a weird vessel or a status effect drops max HP to 1. **Third**, the tests flatter themselves: three "integration" tests stand up an OTEL harness and then never look at it, and the mutuality of ramming — a load-bearing SRD claim — is "verified" by `> 0`, which a one-line regression to `attacker_damage = 1` would sail past. A confused future maintainer could read `defender_max_hp` and assume it affects the rammed-back figure; it does nothing.

Now the rebuttal. The dead-code charge is real but **scoped and documented**: TEA deliberately pinned the contract at `apply_rig_damage`, the design doc explicitly leaves the routing an open fork, and 86-3 ("vehicle chase confrontation … closes into Plan 2 combat") is the encounter-type story that consumes this resolver — building the dispatch now would be speculative architecture with no failing test, against minimalist discipline. The unreachable-input guards are genuinely unreachable today (`hp` floored at 1, `RigComposurePool.max > 0` enforced), so they are forward-hardening, not live bugs — correctly routed to 86-3 where content-sourced inputs first flow. The test weaknesses are polish on code that is *otherwise correct and independently covered* (the genuine wiring test fires the full span chain; the unit tests pin the numeric outcomes). None of this corrupts data, leaks information, or breaks a reachable path. The devil finds smells and forward-debt — not a blocker.

**Handoff:** To SM for finish-story.

## Delivery Findings

No upstream findings at setup time.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Gap** (non-blocking): `apply_rig_damage` still has no confrontation-dispatch consumer — it is reachable from production code via `game/__init__` export and the real OTEL path, but no rig/vehicle confrontation *encounter type* calls it during a player turn yet. Affects `sidequest/agents/subsystems/confrontation.py` + `sidequest/server/dispatch/damage_roll.py` (need a vehicle-vs-vehicle routing branch that targets the rig pool and supplies `crash_save_outcomes` from server-rolled saves). This is the AC7 "open architectural fork" and aligns with epic Plan 3 / story 86-3 ("vehicle chase confrontation … closes into Plan 2 combat when vehicles converge") — the encounter-type story that naturally consumes this resolver. *Found by Dev during implementation.*
- **Question** (non-blocking): the CWN second crash save is bound to param `luck_passed` but the engine has no "Luck" save category (only Physical/Evasion/Mental). The natural port maps it to Evasion. When 86-3 wires the dispatch consumer it must roll the second save against a real category — recommend Evasion. Affects the future dispatch caller, not this slice. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `resolve_ramming` and `vehicle_ac` lack the fail-loud negative-input guards their sibling `apply_rig_damage` has (negative `attacker_max_hp` → negative damage; no `base_ac` floor). Inputs are unreachable today (`RigComposurePool.max > 0`), so harden when 86-3 wires the dispatch consumer that sources these from content. Affects `sidequest/game/vehicle_combat.py` (add `ValueError` on negative `*_max_hp`). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `resolve_crash_saves` silently no-ops when `hp.max ≤ 1` (`half = hp.max // 2 = 0`); `mortal` can false-positive for a driver already at 0 HP (`hp_delta == 0`). Unreachable today (`hp_pool_from_hp` floors max at 1). Affects `sidequest/game/rig_crash.py` (guard `half == 0`; gate single-fail `mortal` on `hp_after < hp_before`). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the legacy `crash_save_outcomes=None` → −1 crash path emits no OTEL marker distinguishing "intentional legacy" from "missed wiring." When 86-3 wires the CWN dispatch consumer, add a `crash_save_mode` span attribute (and/or raise loud if `crash_save_outcomes is None` under an active CWN ruleset) so the GM panel can catch a wiring regression. Affects `sidequest/game/rig_crash.py` crash_event span. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): test polish (lang-review #6) — three integration tests (`test_rig_two_pool_combat.py:188/212/235`) set up the OTEL harness but discard `captured`; tighten `test_both_saves_fail_…`'s loose `"injury" in s.text` to pin `MAJOR_INJURY_STATUS_TEXT`; strengthen `test_ram_is_mutual`'s `>0` to the symmetric value and add a `defender_max_hp`-has-no-effect case. Non-blocking — production is correct and independently covered. Affects `tests/game/test_rig_ramming.py`, `tests/game/test_rig_crash_saves.py`, `tests/integration/test_rig_two_pool_combat.py`. *Found by Reviewer during code review.*

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Crash-save category: tests pin outcomes, not a "Luck" save name**
  - Spec source: context-story-86-2.md AC4; design doc §4.1 ("Physical save AND Luck save")
  - Deviation: the engine's CWN/SWN save system exposes only
    Physical/Evasion/Mental (`SwnRulesetModule._SAVE_ATTRS`); there is no
    "Luck" save. Tests assert the *damage/mortal/major-injury outcomes*
    of the two crash saves rather than asserting a `luck` save category.
  - Why: pinning a nonexistent save category would force a wrong impl;
    outcome-level assertions stay faithful to the SRD result while
    leaving the Physical/Luck→Evasion mapping to the port.
  - Scope: `test_rig_crash_saves.py`, `test_rig_two_pool_combat.py`.
  - Risk: low — the `luck_passed` param name preserves SRD intent; Dev
    binds it to a real category. Flagged for Reviewer.
  - Resolution: Dev decides the save-category binding in GREEN; document it.
- **Two-pool resolution: behavior+OTEL pinned, WinCondition routing left open**
  - Spec source: context-story-86-2.md AC7; design doc §5 Plan 2 ("a new `WinCondition` variant OR a beat-application branch")
  - Deviation: no test asserts a specific `WinCondition` enum value or
    confrontation-routing internal. The integration test pins the
    rig→driver pool transition, dismount, and `rig_pool.*` span chain.
  - Why: the design doc explicitly leaves the routing an open
    architectural fork; pinning one fork in a test would pre-empt a Dev
    architecture decision and churn on the other fork.
  - Scope: `test_rig_two_pool_combat.py`.
  - Risk: low — outcome+telemetry assertions hold under either fork.
  - Resolution: Dev chooses the routing in GREEN; tests remain valid.

### Dev (implementation)
- **AC7/AC8 confrontation-dispatch routing deferred to 86-3**
  - Spec source: context-story-86-2.md AC7 ("a single confrontation can encompass both rig and driver damage pools"), AC8 ("Test runs on a real turn in a rig confrontation scenario (not mocked)")
  - Spec text: the two-pool resolution should be reachable from a real rig confrontation turn / dispatch.
  - Implementation: delivered the two-pool *resolver* + production *seam* (`apply_rig_damage` with `armor` + `crash_save_outcomes`) + full `rig_pool.*` OTEL through the real `WatcherSpanProcessor`; the integration test drives this production seam (not a unit mock). Did NOT build a vehicle-vs-vehicle confrontation *encounter type* / dispatch branch that calls the resolver during a player turn.
  - Rationale: the design doc (§5) explicitly leaves the routing an open fork; no failing test drives a specific dispatch shape (TEA pinned the contract at `apply_rig_damage` by deliberate design); building the routing now is speculative architecture against the minimalist-discipline rule. Epic Plan 3 / story 86-3 is the encounter-type story ("vehicle chase confrontation … closes into Plan 2 combat") that consumes this resolver.
  - Severity: minor (scope-boundary; mechanics fully built + tested + OTEL-verified)
  - Forward impact: 86-3 must add the confrontation/dispatch consumer that calls `apply_rig_damage(..., armor=<vessel armor>, crash_save_outcomes=<server-rolled saves>)` and reads `VesselTags.armor` from the seated vessel. Surfaced as a Delivery Finding (Gap).

### Reviewer (audit)
- **TEA: crash-save outcomes pinned, not a "Luck" save name** → ✓ ACCEPTED by Reviewer: sound — the engine's save system is Physical/Evasion/Mental with no Luck category; outcome-level assertions are the faithful way to pin §2.4.8.2 without forcing a nonexistent save. Evasion is the right port target (noted in Dev's Question finding).
- **TEA: two-pool behavior+OTEL pinned, WinCondition routing left open** → ✓ ACCEPTED by Reviewer: matches the design doc's explicit open fork; the integration test asserts outcome+telemetry that any routing satisfies. Correct restraint, not under-specification.
- **Dev: AC7/AC8 confrontation-dispatch routing deferred to 86-3** → ✓ ACCEPTED by Reviewer: the resolver + production seam + real-watcher OTEL are delivered and tested; 86-3 ("vehicle chase confrontation … closes into Plan 2 combat") is the encounter-type story that consumes this. Building the dispatch routing now would be speculative architecture with no failing test, against minimalist discipline. The story scope (resolver+seam) is fully wired — this is a scope boundary, not a half-wire. Forward-hardening items routed to 86-3 as Delivery Findings.
- No undocumented deviations found. The min-1 armor floor and legacy-path preservation are documented in-code and tested; the `defender_max_hp` dead param is documented as forward-calibration.