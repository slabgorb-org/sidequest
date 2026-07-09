---
story_id: "165-2"
jira_key: ""
epic: "165"
workflow: "spdd"
---
# Story 165-2: Positions as combat state + WN SRD movement/reach/range facts on the binding (plan tasks 4–5)

## Story Details
- **ID:** 165-2
- **Jira Key:** (none)
- **Workflow:** spdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** spdd
**Phase:** finish
**Phase Started:** 2026-07-09T09:44:23Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-09T09:10:15+00:00 | 2026-07-09T09:12:15Z | 2m |
| red | 2026-07-09T09:12:15Z | 2026-07-09T09:23:29Z | 11m 14s |
| green | 2026-07-09T09:23:29Z | 2026-07-09T09:30:41Z | 7m 12s |
| review | 2026-07-09T09:30:41Z | 2026-07-09T09:44:23Z | 13m 42s |
| finish | 2026-07-09T09:44:23Z | - | - |

## SM Assessment

**Story:** 165-2 — Positions as combat state + WN SRD movement/reach/range facts on the binding (plan tasks 4–5). 3pts, p1, server-only, epic 165 (Mapping Track C).

**Workflow decision:** Sprint YAML tags this `superpowers`, which is NOT a registered pf workflow. Per Keith's settled 2026-07-08 decision (`sm-decisions.md`), these mapping-track stories run as **spdd** (phased: setup→red→green→review→finish). Set up as spdd; do not re-litigate.

**Scope (plan tasks 4–5 of `docs/superpowers/plans/2026-07-08-mapping-track-c-tactical-mechanics.md`):**
1. Seat durable per-actor cell positions in `EncounterActor.per_actor_state['cell']` — additive, no new field.
2. Author WN SRD movement/reach/range facts ONCE on `WithoutNumberRulesetModule` (cell scale, per-actor movement budget in cells, melee reach, ranged range) — SRD-sourced, not re-derived per world (that's the flat-13 bug class). These are the inputs the C1 library (`sidequest/game/tactical/adjudication.py`) already consumes: `cells_reachable(budget=…)`, `reach_cells(reach=…)`, `adjudicate_reach(max_cells=…)`.

**Out of scope (do not pull forward):** enforcement wiring at `dispatch_dice_throw` (165-3), turn_telemetry spans (165-3), protocol/UI (165-4), Fate zones (165-5).

**Carryover from 165-1 — TEA/Dev MUST read before writing code (full detail in the story context `## Carryover from 165-1` and epic context §Carryover):**
- `ReachResult.cost` is a SUPERSET of `.reachable` (includes origin@0 + the over-budget boundary). Read `.reachable` for stoppable cells, never `cost.keys()`.
- The plan doc's embedded code has known bugs (mask mislabel + `cells_reachable` cost gap) — fixed in 165-1's actual code but STILL in the doc. Hand-verify every mask/impl against its own test before transcribing tasks 4–5.
- Difficult-terrain is charged on ENTERING a cell (`2 if dest in difficult else 1`) — keep WN "difficult terrain" facts consistent with that.
- Consider closing the 165-1 coverage gap on `movement_cost(difficult=…)` if you're in the library.

**Base branch:** cut from server `develop` at the merged 165-1 PR (`498740a9`) — C1 library is present. Correct base confirmed.

**Handoff:** → TEA (Amos Burton) for RED. TEA defines acceptance criteria + failing tests from plan tasks 4–5 (the story context leaves ACs to the RED phase deliberately).

<skills-invoked>
<skill name="test-driven-development" phase="red" at="2026-07-09T09:21:32Z"/>
<skill name="test-driven-development" phase="green" at="2026-07-09T09:29:01Z"/>
<skill name="verification-before-completion" phase="green" at="2026-07-09T09:29:01Z"/>
<skill name="requesting-code-review" phase="green" at="2026-07-09T09:29:01Z"/>
</skills-invoked>

## TEA Assessment

### Red Phase (test writing)

**Tests Required:** Yes
**Reason:** Two new behavioral units — a pure seat-mapping function (Task 4) and the WN SRD tactical binding + adjudicators (Task 5). Both have contracts worth pinning; neither qualifies for chore bypass.

**Acceptance Criteria** (derived from plan tasks 4–5; the story context deferred ACs to RED):
- **AC1 (Task 4):** `seat_actor_cells(encounter, anchors, *, player_side="player")` seats the entrance anchor on the first player-side actor and creature anchors on opponents in order, writing `EncounterActor.per_actor_state['cell']` as a JSON `[x, y]` list; returns the name→cell map.
- **AC2 (Task 4):** Idempotent — an actor already carrying a `cell` is left untouched and reported as-is; with no anchors nothing is placed; surplus opponents beyond the anchor supply are left unseated (no crash, no stacking).
- **AC3 (Task 5):** WN SRD facts authored ONCE on `WithoutNumberRulesetModule` (`METERS_PER_CELL=1.5`, `DEFAULT_MOVE_METERS=10`, `MELEE_REACH_CELLS=1`, `RANGE_BAND_CELLS`) and inherited by every sibling (swn/wwn/cwn/awn) — never per-world re-derived (the flat-13 bug class).
- **AC4 (Task 5):** `combat_move_cells(core)` floors metres→cells with a min of 1; `weapon_range_cells(spec)` returns `('melee'|'ranged', max_cells)`.
- **AC5 (Task 5):** `adjudicate_tactical_move` / `adjudicate_tactical_reach` delegate to the pure C1 library (`sidequest.game.tactical.adjudication`) — proven by returning C1's `MoveAdjudication`/`RangeAdjudication` types — honouring the Move budget, difficult terrain (charged on ENTER), melee adjacency, and ranged Chebyshev-band + LOS.

**Test Files:**
- `sidequest-server/tests/game/tactical/test_seating.py` — Task 4 (5 tests)
- `sidequest-server/tests/game/ruleset/test_wn_tactical_binding.py` — Task 5 (10 tests)

**Tests Written:** 15 tests covering plan tasks 4–5 (ACs above)
**Status:** RED (failing — ready for Dev). Verified via testing-runner: `test_seating.py` errors at collection with `ModuleNotFoundError: sidequest.game.tactical.seating`; all 10 binding tests fail `AttributeError` on the missing WN methods/constants. No pydantic `ValidationError` on fixtures, no wrong `ImportError` on C1 types, no `AssertionError` — every failure is feature-missing, not test-construction.

**Test values hand-verified against the MERGED C1 library** (per 165-1 carryover — the plan doc's embedded code is not authoritative): `int(10/1.5)=6` move budget; `int(5/1.5)=3` budget for the difficult-terrain case (2 difficult entries × 2 = 4 > 3 → denied, `cells_spent=4`); Chebyshev `(1,1)→(4,1)=3`; Bresenham LOS ray `(1,1)→(5,3)` interior `[(2,1),(3,2),(4,2)]` all floor → `has_los`; singular/plural denial string ("you can move 1 cell").

### Rule Coverage

| Rule (python.md) | Test(s) / Guard | Status |
|------------------|-----------------|--------|
| #6 Test quality (no vacuous asserts) | Self-check: all 15 tests assert specific values (`==`, `isinstance`, `in`, band-table lookups); zero truthy-only / `assert True` | pass |
| #2 Mutable default arguments | `_encounter(actors=None)` uses the None-default + `or [...]` pattern; impl signature `difficult=frozenset()` is immutable-safe (guarded by the difficult-terrain test) | pass |
| No Silent Fallbacks (SOUL/CLAUDE.md) | `test_weapon_range_cells_unknown_band_defaults_to_rifle` documents the fallback; raised as a non-blocking Delivery Finding for fail-loud reconsideration | covered |
| Wiring test (CLAUDE.md "every suite needs one") | `test_adjudicators_return_c1_types` proves the WN binding delegates to the real C1 library; seating writes to the real `EncounterActor.per_actor_state` field | pass |
| No source-text wiring tests (CLAUDE.md) | Wiring proven by return-type/behavior assertions, not `read_text()`/grep of production source | pass |

**Rules checked:** 5 of 8 lang-review rules are applicable to this pure-function/dataclass story (exception-swallowing #1, logging #4, path-handling #5, resource-leak #7, deserialization #8 have no surface here); all applicable checks + the two project wiring rules are covered.
**Self-check:** 0 vacuous tests found.

**Note for Dev (GREEN):** Implement fresh from the tests — do NOT copy the plan doc's embedded impl blindly (it has known bugs per the 165-1 carryover; hand-verify every mask/value). The plan's file paths are a guide, but the WN-binding test lives at `tests/game/ruleset/` (not the plan's `tests/agents/ruleset/`) — see Design Deviations. Adjudicators must DELEGATE to C1, never reimplement grid math.

**Handoff:** To Dev (Naomi Nagata) for implementation.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-server/sidequest/game/tactical/seating.py` (new) — `seat_actor_cells(encounter, anchors, *, player_side="player")`: maps `TokenAnchor` set onto `EncounterActor.per_actor_state['cell']` as a JSON `[x, y]` list; entrance→first player, creature anchors→opponents in order; idempotent; pure over the passed anchors.
- `sidequest-server/sidequest/game/ruleset/without_number.py` (modified) — added SRD tactical facts on `WithoutNumberRulesetModule` (`METERS_PER_CELL=1.5`, `DEFAULT_MOVE_METERS=10`, `MELEE_REACH_CELLS=1`, `RANGE_BAND_CELLS`) + `combat_move_cells`, `weapon_range_cells`, `adjudicate_tactical_move`, `adjudicate_tactical_reach`. The two adjudicators DELEGATE to the pure C1 library (`sidequest.game.tactical.adjudication.adjudicate_move`/`adjudicate_reach`) — this is C1's production wiring. Facts authored once on the base; all four siblings (swn/wwn/cwn/awn) inherit.

**Tests:** 15/15 story tests passing (GREEN) — `test_seating.py` 5/5, `test_wn_tactical_binding.py` 10/10.
**Regression:** 578/578 `tests/game/ruleset/` + `tests/game/tactical/` passing — the shared-base-class change broke no sibling.

**Verification evidence (fresh):**
- Tests: 15/15 target + 578/578 regression (via testing-runner, `-n0`).
- Ruff format + check: clean on all 4 changed files.
- Pyright: 3 errors in `without_number.py` at lines 261/886/1181 are PRE-EXISTING — proven by `git show develop:…` baseline (same 3 errors at 178/803/1098, shifted by the inserted lines). My tactical code adds ZERO new type errors; `seating.py` is type-clean.

**Branch:** `feat/165-2-positions-combat-state-wn-facts` (pushed to origin).

**Scope discipline:** Implemented exactly the tests' contract (plan tasks 4–5). No production call-site wiring (`instantiate_encounter_from_trigger`, `dispatch_dice_throw`) — that is 165-3 per the SM scope. No native-mechanic tuning against the binding (SOUL: Bind the Ruleset).

**Handoff:** To Reviewer (Chrisjen Avasarala) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | GREEN: 15/15 + 578/578, ruff clean, pyright 3 pre-existing (0 new, baseline-verified), 0 smells | confirmed 0 blocking |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (edge cases covered manually + by test-analyzer) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings (silent fallbacks covered by rule-checker + my analysis) |
| 4 | reviewer-test-analyzer | Yes | findings | 8 (2 high, 4 med, 2 low) | confirmed 8, all non-blocking (coverage gaps + doc-overclaim); routed 4 to 165-3 |
| 5 | reviewer-comment-analyzer | Yes | findings | 4 (2 high, 1 med, 1 low) | confirmed 4; the RANGE_BAND_CELLS↔content format mismatch escalated to blocking-for-165-3 |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (type annotations verified clean by rule-checker #3 + pyright) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings (no auth/tenant/injection surface — pure domain methods) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (diff is minimal; no over-engineering observed) |
| 9 | reviewer-rule-checker | Yes | findings | 3 rule (1 high, 1 med, 1 low) + OTEL/wiring observations | confirmed 3; OTEL + wiring absence are deliberate 165-3 scope |

**All received:** Yes (4 ran, 5 disabled via settings)
**Total findings:** 8 confirmed (0 blocking for 165-2), 0 dismissed, 5 routed as blocking-for-165-3 delivery findings

## Reviewer Assessment

**Verdict:** APPROVED

**Summary:** Story 165-2 ships exactly what its scope defines — a pure seat-mapping library (`seating.py`) and SRD tactical facts + C1-delegating adjudicators on `WithoutNumberRulesetModule`, with production wiring, enforcement, OTEL spans, and Fate zones all deliberately deferred to 165-3/4/5. The code is correct and tested in isolation (15/15 story + 578/578 regression, ruff clean, 0 new pyright errors). Every substantive finding is either (a) an inert-until-165-3 concern that cannot misfire while the methods have no production caller, or (b) a low-risk hardening/test-strengthening suggestion. None blocks a facts-only story. Several are escalated as **blocking-for-165-3** so the wiring cannot land blind.

**Observations (9):**
- `[RULE][SILENT]` `weapon_range_cells` swallows an unknown `range_band` → rifle cap (`without_number.py:178`). CONFIRMED real No-Silent-Fallbacks violation — breaks this file's OWN fail-loud convention (`_stat` raises KeyError, `save_params`/`apply_system_strain` raise ValueError). **Non-blocking for 165-2** (method has zero production callers — inert; plan authored the fallback deliberately; TEA surfaced it as an *open* team decision with a pinning test) but **blocking-for-165-3**: resolve fail-loud vs. validated vocabulary before wiring.
- `[DOC][RULE]` `RANGE_BAND_CELLS` categorical keys (`rifle`/`pistol`/…) match NOTHING in real content (`without_number.py:154`). Independently verified: `range_band` exists only on `CatalogItem` (`inventory.py:214`) and every pack authors it as an `"N/N"` numeric string (`"10/100"`, `"100/600"`); there is no `DamageSpec.range_band`. When 165-3 feeds a real spec, every ranged weapon silently collapses to melee or the rifle cap. **Blocking-for-165-3** — needs an `"N/N"`→band translation the codebase lacks.
- `[TEST][DOC][RULE]` `combat_move_cells(move=0)` returns 6, not 0 (`without_number.py:168`) — `getattr(...) or DEFAULT` treats explicit 0 as unset. Latent (no live content sets `move:0`; `mutation/stocks.py:218` would propagate one). → 165-3, trivial `is None` fix.
- `[TEST][DOC]` `seat_actor_cells` collides player-overflow with opponents (`seating.py:36,50`). Reproduced empirically: 2 players + 1 opponent → PlayerB and Opp1 both on `(3,1)`; neutral-side actors also route through the opponent/creature pool and can steal a monster's seat. Inert (no production caller; plan's documented "spill" design; single-player path clean) → 165-3 must define MP/neutral seating semantics.
- `[RULE][TYPE]` `RANGE_BAND_CELLS` is a class-level mutable dict shared by identity across all four singleton siblings (`without_number.py:154`). LOW — read-only, no mutation site exists. Recommend `ClassVar[Mapping[str,int]]` + `MappingProxyType` to enforce the docstring's "authored once" intent by type, not convention.
- `[TEST]` Two tests overclaim in their docstrings: `test_adjudicators_return_c1_types` proves return *type*, not that C1 was called (a reimplementation returning the same dataclasses would pass); `test_tactical_facts_authored_once…` checks value-equality, not inheritance provenance (a sibling copy-pasting `METERS_PER_CELL=1.5` still passes). Non-blocking — behavioral tests (budget math, LOS gating, difficult terrain) indirectly prove delegation, and value-equality catches today's real drift risk. Recommend a `mock.patch` delegation assert + `"METERS_PER_CELL" not in Sibling.__dict__` provenance check for 165-3.
- `[SEC]` subagent disabled; manual audit: no auth, tenant, injection, deserialization, or user-input boundary — these are internal game-engine domain methods several layers from any request/CLI. `[VERIFIED]` no security surface — evidence: `seating.py`/tactical block contain no I/O, no eval/pickle/yaml.load, no SQL, no request handling.
- `[SIMPLE]` subagent disabled; manual: diff is minimal and non-duplicative; adjudicators are thin delegations. `[EDGE]` subagent disabled; boundary conditions (empty anchors, overflow, zero/negative budget, out-of-reach, LOS-blocked) covered by test-analyzer + the C1 library's own edge tests. No over-engineering observed.
- `[VERIFIED]` Adjudicators genuinely DELEGATE to C1 (no stub) — `without_number.py:191-199,212-222` call `adjudicate_move`/`adjudicate_reach` and return unmodified; complies with No-Stubbing and Bind-the-Ruleset (only the WN core is touched; zero native/dial back-pressure). `[VERIFIED]` "authored once" holds — evidence: grep confirms swn/wwn/cwn/awn override none of the four tactical attrs; `test_tactical_facts_authored_once…` proves value-parity at runtime.

**Data flow traced:** two inert paths. (1) `RegionTactical` anchors → `seat_actor_cells` → mutates `EncounterActor.per_actor_state['cell']` (JSON `[x,y]`, resume-safe). (2) `core`/`spec` → `combat_move_cells`/`weapon_range_cells` → `adjudicate_tactical_move`/`_reach` → C1 `adjudicate_move`/`adjudicate_reach`. Neither path has a production caller in this story (verified via grep) — no user-input boundary reached; enforcement is 165-3.

**Error handling:** the two silent fallbacks (unknown band, move=0) are the only failure-mode concerns; both confirmed, both inert, both routed to 165-3. Malformed persisted `cell` (e.g. 1-element list) would `IndexError` in `seat_actor_cells:44`, but that is corrupted-state territory, not a normal path.

**Tenant isolation audit:** N/A — SideQuest is not multi-tenant; no trait method here handles tenant data, no struct carries a tenant field. No violation possible.

### Rule Compliance (python.md, 13 checks + project doctrine)

- **#1 silent exceptions** — no try/except in diff. Clean.
- **#2 mutable defaults** — `player_side="player"` (str), `difficult=frozenset()` (immutable) clean; scalar class attrs clean. `RANGE_BAND_CELLS` class-level dict = literal rule-#2 match → confirmed LOW (read-only, no mutation site, singleton siblings). Downgraded with rationale, NOT dismissed; hardening recommended.
- **#3 type annotations** — all 5 new public signatures fully annotated; return types under `TYPE_CHECKING` + `from __future__ import annotations`. Clean.
- **#4 logging** — neither module imports logging/structlog; out of literal scope. (OTEL doctrine handled separately — deferred to 165-3 Task 6.)
- **#5 path handling** — none. **#7 resource leaks** — none. **#8 unsafe deserialization** — none. **#9 async** — none. **#11 input validation** — no boundary. **#12 dependency hygiene** — no dep changes. **#13 fix-regressions** — additive, 578 green. All clean/no-surface.
- **#6 test quality** — all 15 tests assert specific values; no skips, no vacuous asserts, no mock-target errors. Clean. (Two docstring-overclaims noted as non-blocking [TEST] observations, not rule-#6 violations.)
- **#10 import hygiene** — no star/circular imports; TYPE_CHECKING deferral correct; local method-body imports defensible. `seating.py` lacks `__all__` (literal rule match) but matches house style (81 `sidequest/game/*.py` files lack it) → LOW/non-actionable.
- **No Silent Fallbacks (SOUL/CLAUDE <critical>)** — TWO confirmed (band→rifle, move=0). Not dismissed; downgraded to non-blocking-for-165-2 (inert) + blocking-for-165-3.
- **No Stubbing / Bind-the-Ruleset** — compliant (real C1 delegation; only WN core touched).

### Devil's Advocate

Argue this is broken. First: the story title promises "WN SRD movement/reach/range facts," but the range table is a **Potemkin fact** — `RANGE_BAND_CELLS` is keyed on categorical bands that no weapon in any shipped pack actually uses, and the only field named `range_band` (on `CatalogItem`) carries `"100/600"`-style strings. So the moment 165-3 wires this, a sniper rifle, a thrown knife, and a pistol all resolve to the identical 40-cell "rifle" cap — the mechanical distinction the table exists to provide evaporates, silently, with no error. A mechanics-first player (Sebastien, Jade) would immediately notice every ranged weapon behaves identically and the "SRD-grounded" claim is hollow. Second: a confused content author who writes `range_band: "riffle"` (typo) or a homebrew band (Jade authoring perseus_cloud) gets no error — the weapon silently caps at rifle range. That is exactly the "winging it with zero mechanical backing" the OTEL lie-detector doctrine exists to expose, and these five decision methods emit **zero** spans. Third: in Keith's actual multiplayer playgroup, `seat_actor_cells` stacks the second PC on the first monster's cell — two tokens, one square — and a neutral bystander can shove a real opponent off the grid entirely by consuming its anchor. Fourth: an immobilized creature (`move=0`) sprints the full 6 cells because `0` is falsy. Any one of these, shipped live, is a real player-visible defect.

Rebuttal — why APPROVE anyway: every one of these bites *only when 165-3 wires the methods to a production caller*, and this story deliberately ships them inert (grep confirms zero non-test callers; the epic/plan/SM-scope all defer wiring, spans, and enforcement to 165-3). The code is correct for what 165-2 delivers: the C1 delegation is real, the facts are authored-once and inherited, and 15 tests + 578 regression pass. The disciplined move is not to reject a facts-only story for not doing 165-3's job, nor to unilaterally reverse the plan's documented rifle-fallback on a dead code path — it is to APPROVE and escalate all four wiring-time landmines as **blocking-for-165-3** delivery findings so the next story cannot proceed blind. That is done below.

**Handoff:** To SM (Camina Drummer) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Question** (non-blocking): `weapon_range_cells` silently defaults an unknown `range_band` to the rifle cap (`RANGE_BAND_CELLS.get(band, RANGE_BAND_CELLS["rifle"])`), which masks a content typo against the "No Silent Fallbacks" doctrine. Affects `sidequest/game/ruleset/without_number.py` (`weapon_range_cells` — decide fail-loud on an unregistered band vs. keep the documented rifle fallback). The RED test pins the current documented behavior either way. *Found by TEA during test design.*
- **Improvement** (non-blocking): Production wiring of both units (seating at `instantiate_encounter_from_trigger`, reach/range enforcement at `dispatch_dice_throw`) is explicitly out of scope here (165-3, plan tasks 6–8). This story ships a pure library + inert facts; the end-to-end wiring test that proves they fire in production belongs to 165-3. Affects `sidequest/server/dispatch/` (no change this story — flag so Reviewer does not expect a live call-site here). *Found by TEA during test design.*

### Dev (implementation)
- **Question** (non-blocking): `combat_move_cells` uses `getattr(core, "move", None) or self.DEFAULT_MOVE_METERS`, so a falsy `core.move` (0, or None) silently takes the 10 m SRD default. For None that is intended; for `move == 0` (a truly immobile stock) it silently grants full movement — the same No-Silent-Fallbacks concern TEA raised for `weapon_range_cells`. Affects `sidequest/game/ruleset/without_number.py` (`combat_move_cells` — decide whether `move == 0` should mean "0 cells" rather than defaulting). No test covers `move == 0`; behavior matches the plan. *Found by Dev during implementation.*
- **Improvement** (non-blocking): `without_number.py` carries 3 pre-existing pyright errors (lines 261/886/1181: `stat_modifier` `str|None`, `assign_attributes` override, `commit_effort` duration Literal). Unchanged by this story (baseline-verified). Affects `sidequest/game/ruleset/without_number.py` (cleanup candidate for a typing story, out of scope here). *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking for 165-3): `RANGE_BAND_CELLS` categorical keys (`rifle`/`pistol`/`thrown`/…) match no real content — `range_band` exists only on `CatalogItem` (`sidequest/genre/models/inventory.py:214`) and every pack authors it as an `"N/N"` numeric string (`"10/100"`, `"100/600"`); there is no `DamageSpec.range_band`. When 165-3 wires `weapon_range_cells` to a real spec, every ranged weapon silently resolves to melee or the rifle cap. Affects `sidequest/game/ruleset/without_number.py:154` + 165-3 wiring (needs an `"N/N"`→band translation step that does not exist yet; do not wire ranged reach until it does). *Found by Reviewer during code review.*
- **Conflict** (blocking for 165-3): `weapon_range_cells` silently defaults an unknown `range_band` to the rifle cap (`without_number.py:178`) — a No-Silent-Fallbacks violation that breaks this file's own fail-loud convention (`_stat`/`save_params`/`apply_system_strain` all raise on unknown keys). Inert in 165-2 (no caller); resolve fail-loud vs. validated vocabulary before 165-3 wires it. Affects `sidequest/game/ruleset/without_number.py:178`. *Found by Reviewer during code review.*
- **Improvement** (blocking for 165-3): `combat_move_cells` uses `getattr(core,"move",None) or DEFAULT_MOVE_METERS`, so an explicit `move=0` is silently overridden to full default (`mutation/stocks.py:218` would propagate a `move:0` stock). Latent today (no live content sets 0). Fix with an `is None` check when 165-3 wires movement. Affects `sidequest/game/ruleset/without_number.py:168`. *Found by Reviewer during code review.*
- **Gap** (non-blocking): `seat_actor_cells` collides player-overflow with opponents (empirically: 2 players + 1 opponent → PlayerB and Opp1 both on `(3,1)`) and routes neutral-side actors through the opponent/creature anchor pool (a neutral can steal a monster's seat). Inert (no caller; plan's documented spill design; single-player path clean). Affects `sidequest/game/tactical/seating.py:36-51` — 165-3 must define multi-player/neutral seating semantics. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the tactical decision methods (`combat_move_cells`, `weapon_range_cells`, `adjudicate_tactical_move/_reach`, `seat_actor_cells`) emit zero OTEL spans, unlike every other decision method in `without_number.py`. This is correctly plan Task 6 / 165-3 scope, not a 165-2 gap — flagged so 165-3 adds the spans (OTEL Observability Principle) AND a real production wiring test. Affects `sidequest/telemetry/spans/` + 165-3. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): two tests overclaim in their docstrings — `test_adjudicators_return_c1_types` proves return type not the C1 call (add `mock.patch` delegation assert), and `test_tactical_facts_authored_once…` checks value-equality not inheritance provenance (add `"METERS_PER_CELL" not in Sibling.__dict__`). Behavioral tests already cover the substance; strengthen in a follow-up. Affects `tests/game/ruleset/test_wn_tactical_binding.py:124,141`. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **WN-binding test placed in `tests/game/ruleset/`, not the plan's `tests/agents/ruleset/`**
  - Spec source: `docs/superpowers/plans/2026-07-08-mapping-track-c-tactical-mechanics.md`, Task 5 ("Create `sidequest-server/tests/agents/ruleset/test_wn_tactical_binding.py`")
  - Spec text: test file path under `tests/agents/ruleset/`
  - Implementation: created `tests/game/ruleset/test_wn_tactical_binding.py`
  - Rationale: the module under test is `sidequest/game/ruleset/without_number.py`; every existing WN/ruleset module test already lives in `tests/game/ruleset/` (test_wwn_module.py, test_142_wn_core_extraction.py, …). The plan's `agents/` path is a slip — mirroring the source layout matches convention. `tests/agents/ruleset/` does not exist.
  - Severity: minor
  - Forward impact: none (Dev's GREEN targets the same file; sibling stories 165-3/4/5 reference the same plan and should expect the same path slip)
- **Added 5 paranoid tests beyond the plan's embedded examples**
  - Spec source: plan tasks 4–5 (embedded test blocks)
  - Spec text: 3 seating tests + 5 binding tests
  - Implementation: 5 seating + 10 binding tests — extras cover anchor overflow, JSON-list cell format, min-1 move floor, unknown-band fallback, authored-once sibling inheritance (anti flat-13), difficult-terrain move cost (closes the 165-1 `movement_cost(difficult=)` gap), and C1 return-type delegation
  - Rationale: TEA test-paranoia + the 165-1 carryover explicitly flagged the flat-13 re-derivation risk and the untested difficult-terrain leg
  - Severity: minor
  - Forward impact: none — additive coverage; all fail RED for the same feature-missing reason

### Dev (implementation)
- **Added explicit type annotations to the two adjudicator methods (plan left them bare)**
  - Spec source: `docs/superpowers/plans/2026-07-08-mapping-track-c-tactical-mechanics.md`, Task 5 (embedded impl of `adjudicate_tactical_move` / `adjudicate_tactical_reach`)
  - Spec text: `def adjudicate_tactical_move(self, *, origin, path, core, mask, difficult=frozenset()):` (no parameter or return annotations)
  - Implementation: annotated params as `tuple[int, int]` / `list[tuple[int, int]]` / `object | None` / `str` / `frozenset[tuple[int, int]]` and return types as `MoveAdjudication` / `RangeAdjudication` (imported under `TYPE_CHECKING`; runtime import stays local inside the method)
  - Rationale: lang-review #3 (Python) requires parameter and return annotations; the module has `from __future__ import annotations` so this is zero-runtime-cost and introduces no import cycle
  - Severity: minor
  - Forward impact: none — public method signatures are as the plan intended, just typed
- Otherwise implemented exactly per the tests + plan tasks 4–5 (seating logic and WN facts transcribed and hand-verified against the merged C1 library). No structural or algorithmic deviation.

### Reviewer (audit)
- **TEA — WN-binding test placed in `tests/game/ruleset/` not the plan's `tests/agents/ruleset/`** → ✓ ACCEPTED by Reviewer: correct — the module under test lives in `sidequest/game/ruleset/`, and all existing WN module tests are in `tests/game/ruleset/`. Mirroring source layout is the right convention; the plan's `agents/` path is a slip.
- **TEA — added 5 paranoid tests beyond the plan's examples** → ✓ ACCEPTED by Reviewer: additive coverage (anti-flat-13 inheritance, difficult terrain, overflow, C1 typing) is sound and raised no false REDs. Two of them overclaim in docstrings (see [TEST] observation) but that's a strengthen-later note, not a reason to flag the deviation.
- **Dev — added type annotations to the two adjudicators the plan left bare** → ✓ ACCEPTED by Reviewer: required by lang-review #3; TYPE_CHECKING import under `from __future__ import annotations` is zero-runtime-cost and introduces no cycle (verified). Public signatures are as the plan intended, just typed.
- No UNDOCUMENTED deviations found — the implementation matches the tests and plan tasks 4–5; all divergences from the plan's literal text were logged by TEA/Dev.