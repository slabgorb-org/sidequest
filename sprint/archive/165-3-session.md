---
story_id: "165-3"
jira_key: ""
epic: "165"
workflow: "spdd"
---
# Story 165-3: Enforcement wiring: turn_telemetry spans, dispatch_dice_throw reach/range gate, seat positions (plan tasks 6–8)

<skills-invoked>
<skill name="test-driven-development" phase="red" at="2026-07-09T10:44:24Z"/>
<skill name="test-driven-development" phase="red" at="2026-07-09T13:08:00Z"/>
<skill name="test-driven-development" phase="green" at="2026-07-09T11:06:30Z"/>
<skill name="verification-before-completion" phase="green" at="2026-07-09T11:20:00Z"/>
<skill name="requesting-code-review" phase="green" at="2026-07-09T11:30:00Z"/>
<skill name="test-driven-development" phase="green" at="2026-07-09T13:22:00Z"/>
<skill name="verification-before-completion" phase="green" at="2026-07-09T13:44:00Z"/>
<skill name="requesting-code-review" phase="green" at="2026-07-09T13:45:00Z"/>
</skills-invoked>

## Story Details
- **ID:** 165-3
- **Jira Key:** (none)
- **Workflow:** spdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** spdd
**Phase:** finish
**Phase Started:** 2026-07-09T14:05:07Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-09T10:32:47Z | 2026-07-09T10:34:46Z | 1m 59s |
| red | 2026-07-09T10:34:46Z | 2026-07-09T11:06:17Z | 31m 31s |
| green | 2026-07-09T11:06:17Z | 2026-07-09T11:55:13Z | 48m 56s |
| review | 2026-07-09T11:55:13Z | 2026-07-09T12:15:53Z | 20m 40s |
| red | 2026-07-09T12:15:53Z | 2026-07-09T13:20:54Z | 1h 5m |
| green | 2026-07-09T13:20:54Z | 2026-07-09T13:48:31Z | 27m 37s |
| review | 2026-07-09T13:48:31Z | 2026-07-09T14:05:07Z | 16m 36s |
| finish | 2026-07-09T14:05:07Z | - | - |

## Sm Assessment

**Setup complete — handing to TEA (Amos) for the RED phase.**

- **Workflow:** `superpowers` tag → run as **`spdd`** (settled Keith decision, `.pennyfarthing/sidecars/sm-decisions.md`). Phases: setup(sm) → red(tea) → green(dev) → review(reviewer) → finish(sm).
- **Repo:** server only. Branch `feat/165-3-enforcement-wiring` off `develop` (server has no local `main`).
- **Plan reference:** `docs/superpowers/plans/2026-07-08-mapping-track-*.md` (Track C), tasks **6–8**. It is reference material per phase, NOT an `executing-plans` run. **The plan doc has bugs in its embedded code — hand-verify before transcribing.**

**What this story is:** the story that **binds C1 into production**. The WN ruleset module imports `sidequest.game.tactical.adjudication` and calls the reach/range + movement gates from `dispatch_dice_throw`. Enforcement lives in the **binding**, not native combat (ADR-117/143 — bind, don't balance).

**AC definition is TEA's job in RED.** The context (`sprint/context/context-story-165-3.md`) leaves ACs to be derived from plan tasks 6–8. Non-negotiable: **THIS STORY OWNS C1's PRODUCTION WIRING TEST** — an integration/wiring test that reaches `game.tactical` from a real `dispatch_dice_throw` path (fixture-driven behavior or OTEL-span, per CLAUDE.md "No Source-Text Wiring Tests"), not more unit tests on `adjudication.py`.

**THREE BLOCKERS carried from 165-2 — the facts being wired are inert landmines. Read the context §"Carryover from 165-2" in full. Resolve each BEFORE the dispatch gate calls the method:**
1. **`RANGE_BAND_CELLS` keys match nothing in real content** — table keyed on categorical bands (`rifle`/`pistol`/…) but real `range_band` exists only on `CatalogItem` as `"N/N"` numeric strings; there's no `DamageSpec.range_band`. Do NOT wire the range gate to real weapon specs until an `"N/N"`→band translation exists. Format mismatch, not field-selection.
2. **Two silent fallbacks in `without_number.py`** violate No-Silent-Fallbacks: `weapon_range_cells` (`:178`) caps unknown band at rifle (should fail loud); `combat_move_cells` (`:168`) turns explicit `move=0` into full default (use `is None`). Same fix family as tightening `adjudicate_reach(mode)` → `Literal["melee","ranged"]`.
3. **`seat_actor_cells` collides player-overflow with opponents** and mis-routes neutrals (`seating.py:36-51`). Task 8 must define multi-player/neutral seating semantics before seeding real MP encounters — Keith's playgroup is multiplayer.

**Also close 165-1 coverage gaps while consuming the library:** `movement_cost(difficult=…)`, `line_of_sight` endpoint-exclusion, `aoe_burst(require_los=False)` untested. Gate on `ReachResult.reachable`/the verdict — **`.cost` is a superset of `.reachable`**. No-grid = no-grid: gate fires only when both actors carry `per_actor_state['cell']`; else resolve as today and emit `tactical.enforcement.skipped` (reason `no_grid`) — scope boundary, not a silent fallback. New spans MUST call `publish_event` (reach `turn_telemetry`) and need a `SPAN_ROUTES`/`FLAT_ONLY_SPANS` entry or `tests/telemetry/test_routing_completeness.py` fails.

Full detail: `sprint/context/context-story-165-3.md`, `sprint/archive/165-{1,2}-session.md`, and the tea/dev/reviewer `*-gotchas.md` (tagged 165-1/165-2).

## TEA Assessment

**Phase:** finish — **Tests Required:** Yes
**Skill attested:** `test-driven-development` (see `<skills-invoked>`).
**Status:** RED — ready for Dev (Naomi). **8 failing + 12 collection-blocked (2 new modules) + 24 passing controls.**

Every test hand-verified against the REAL API — the plan doc's embedded code has bugs (SM warned; I found one live: Task 6's snippet omits the recording-tracer fixture, so its mirror never fires — my test installs `capture_spans`). **I write tests only; the plan's embedded IMPL is Dev's reference, not authoritative.**

**Test files (7):**
- `tests/game/ruleset/test_wn_tactical_binding.py` (+3, −1 replaced) — BLOCKERs 1, 2a, 2b
- `tests/game/tactical/test_seating.py` (+2) — BLOCKER 3 (MP seat collision)
- `tests/game/tactical/test_reach_range_aoe.py` (+3) — mode fail-loud (RED) + 2 characterization (green)
- `tests/telemetry/test_tactical_telemetry_sink.py` (new, 7) — Task 6 spans mirror + routing + package-wiring
- `tests/server/dispatch/test_dice_tactical_enforcement.py` (new, 5) — Task 7 `_enforce_tactical_reach` contract
- `tests/server/dispatch/test_encounter_position_seating.py` (new, 2) — Task 8 seat-at-instantiation + no-op control
- `tests/integration/test_dice_tactical_enforcement_wiring.py` (new, 1) — **the load-bearing wiring test this story owns**

**AC coverage by task:**
- **Task 6 (spans → turn_telemetry):** 5 span mirrors via `publish_event` + routing-completeness + package-namespace wiring. RED = module `spans/tactical.py` missing (collection error).
- **Task 7 (reach gate in dispatch):** `_enforce_tactical_reach` melee in/out, no-grid skip (returns None, NOT a silent fallback), missing-mask skip, non-WN capability gate. These reach `game.tactical` through the REAL WN ruleset binding, not adjudication.py in isolation. RED = helper missing.
- **Task 7 WIRING (owned by this story):** a real `dispatch_dice_throw` WN strike must CALL `_enforce_tactical_reach` — spy-based, refactor-stable, content-gated on the proven heavy_metal harness. RED verified: `assert []` — the real strike dispatch ran to completion and never touched the gate (165-2 shipped it inert).
- **Task 8 (seat at instantiation):** actors seated with cells from `RegionTactical` anchors + a no-grid no-op control. RED = `instantiate_encounter_from_trigger` has no seating path (see BLOCKING finding on `dungeon_store` plumbing).

**Three 165-2 BLOCKERs — enforcement tests (resolve BEFORE the gate calls the method, or ranged/MP ships silently wrong):**
- **B1** `test_weapon_range_cells_reads_real_content_nn_format` — real `"N/N"` metre bands resolve `ranged` with range-tracking cells (RED: both collapse to rifle 40).
- **B2a** `test_weapon_range_cells_garbage_band_fails_loud` — unknown band raises (RED: silent rifle cap). **Replaces** the 165-2 test that pinned the bug.
- **B2b** `test_combat_move_cells_explicit_zero_is_honored_not_defaulted` — `move=0` → 1, not the 6-cell default (RED: `6 != 6`).
- **B3** `test_multiplayer_players_do_not_collide_with_opponents` + `test_mixed_sides_all_seated_cells_unique` — no shared cells across sides (RED: reproduces reviewer's `Vale`+`rope-spider` both on `(3,1)`).

**165-1 carryover closed:** `adjudicate_reach` unknown-mode fail-loud (RED); `line_of_sight` endpoint-exclusion + `aoe_burst(require_los=False)` characterization backfill (green — pin behaviour the gate leans on).

### Rule Coverage (lang-review/python.md)

| Rule | Test(s) | Status |
|------|---------|--------|
| #1 No-Silent-Fallbacks (garbage band) | `test_weapon_range_cells_garbage_band_fails_loud` | failing (RED) |
| #1 No-Silent-Fallbacks (explicit move=0) | `test_combat_move_cells_explicit_zero_is_honored_not_defaulted` | failing (RED) |
| #1 No-Silent-Fallbacks (unknown mode) | `test_adjudicate_reach_rejects_unknown_mode` | failing (RED) |
| #1 No-Silent-Fallbacks (no-grid = deliberate skip span, not silent) | `test_no_grid_skips_enforcement`, `test_enforcement_skipped_mirrors_with_reason` | RED (helper/module missing) |
| Wiring (CLAUDE.md: reach game.tactical from real dispatch; no source-text) | `test_dispatch_dice_throw_invokes_tactical_reach_enforcement` | failing (RED) |
| Wiring (Task 6 package re-export) | `test_tactical_spans_wired_into_package_namespace` | RED (module missing) |
| #6 Test quality (meaningful assertions) | self-check: all assert real values; 0 vacuous | pass |

**Rules checked:** No-Silent-Fallbacks (#1 spirit) is the load-bearing rule for this story — the three blockers + mode-tightening are its enforcement. **Self-check:** 0 vacuous assertions; every test asserts a concrete value or a specific raise.

**Handoff:** To Dev (Naomi) for GREEN. Read the two BLOCKING Delivery Findings first — B1's format decision and the Task-8 `dungeon_store` plumbing are design forks, not mechanical fills.

## Dev Assessment

**Implementation Complete:** Yes — **GREEN**, with the pre-handoff code review's Critical + Important findings resolved so the gate is **live end-to-end**, not half-wired.
**Skills attested (green):** `test-driven-development`, `verification-before-completion`, `requesting-code-review`.

**Tests:** all 20 RED signals green + a new real-caller wiring test. **Story scope: 59 tests pass; regression: 1834 passed** across ruleset/tactical/dispatch/telemetry/subsystems/WWN-integration (1 known **pre-existing** failure — `test_monster_manual_inject.py::test_execute_narration_turn_refreshes_stale_monster_manual`, a `CartographyTreatmentWire` pydantic error + LLM-transport hermeticity, confirmed failing on the pre-change baseline via `git stash`).

**Branch:** `feat/165-3-enforcement-wiring` (pushed).

**Files changed (13 source + 1 test):**
- `game/tactical/adjudication.py` — `adjudicate_reach` fails loud on unknown mode (165-1 tightening).
- `game/ruleset/without_number.py` — B2b `combat_move_cells` is-None (honor `move=0`); B1/2a `weapon_range_cells` + `_range_band_to_cells` (parse real `"N/N"` metre band from `max(short,long)`, keep categorical SRD keys, fail loud on garbage).
- `game/tactical/seating.py` — B3 collision-free side-priority seating (players→opponents→neutrals) over a shared occupancy set.
- `telemetry/spans/tactical.py` (new) + `telemetry/spans/__init__.py` — 5 `tactical.*` spans mirrored into turn_telemetry via `publish_event`; wired into the package.
- `server/dispatch/dice.py` — `_enforce_tactical_reach` + `_resolve_room_mask`; gate wired into `dispatch_dice_throw` (WN-gated, scoped to `hp_depletion` combat, resolves the real weapon `range_band`, distinct skip reasons, aborts an out-of-reach strike before any beat apply/seal); optional `dungeon_store` param.
- `handlers/dice_throw.py` — plumbs `sd.dungeon_store` to the dispatch (mask half of the wire).
- `game/ruleset/combat_rules.py` — `resolve_weapon_range_band_from_beat_and_actor` (surfaces `CatalogItem.range_band` to the gate → ranged uses its SRD band, and BLOCKER 1's N/N support is now reachable in production, not just unit-tested).
- `server/dispatch/encounter_lifecycle.py` — `dungeon_store` kwarg + `_seat_tactical_cells` (seat cells from `RegionTactical` anchors + `tactical.positions.seated` span before the combat return).
- `agents/subsystems/confrontation.py` + `agents/subsystems/dogfight.py` — thread `dungeon_store` (the live seating callers) so seating runs on the **real** creation path (the dispatch-bank context already carried it; the entrypoints dropped it).

**How the two BLOCKING TEA findings were resolved:**
- **B1 (range_band format fork):** `_range_band_to_cells` parses the real `"N/N"` metre format (derive from the larger figure) AND keeps categorical SRD keys for back-compat; garbage fails loud. To reach it from production, `resolve_weapon_range_band_from_beat_and_actor` surfaces the equipped weapon's `CatalogItem.range_band` to the dispatch gate (the missing plumbing the finding named).
- **Task-8 `dungeon_store` plumbing fork:** chose the `dungeon_store=` kwarg on `instantiate_encounter_from_trigger` AND threaded it through the two live subsystem dispatchers via the dispatch bank's context-filter (`_filter_context_for_callable`) — the store was already in the intent-router-pass context, so only the entrypoint params needed declaring.

**Pre-handoff code review (requesting-code-review skill):** a general-purpose reviewer flagged the gate as inert (seating unwired to live callers) + ranged false-denial + over-scoping. All Critical + Important findings fixed this phase (seating threaded, real range_band, combat-scoped, distinct skip reasons, reversed-band robustness). Two Minors accepted as consistent with codebase precedent (see Delivery Findings).

**Handoff:** To Reviewer (Chrisjen) for the formal review phase.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 59 story tests green; 1365 regression + 1 known pre-existing fail; lint/format clean; 1 pre-existing TODO | confirmed 0, dismissed 0 (baseline clean) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — edge domain (softlock) assessed by Reviewer |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — silent-fallback domain (dead `getattr`) assessed by Reviewer + rule-checker |
| 4 | reviewer-test-analyzer | Yes | findings | 12 (2 high, 5 med, 5 low) | confirmed 9, deferred 3 (low nits) |
| 5 | reviewer-comment-analyzer | Yes | findings | 11 (2 high, 4 med, 5 low) | confirmed 6, deferred 5 (doc nits) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — type domain covered by rule-checker #3 |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings — no auth/tenant/injection surface (game-mechanics diff); N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — redundant-import/double-resolution notes assessed by Reviewer |
| 9 | reviewer-rule-checker | Yes | findings | 4 (1 critical regression, 3 type-annotation) | confirmed 4 |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 13 confirmed, 0 dismissed, 8 deferred (low nits)

## Reviewer Assessment

**Verdict:** REJECTED

The blocker fixes (B1/B2a/B2b/B3, mode-tightening) and the telemetry/seating infrastructure are genuinely good — collision-free seating, fail-loud validation, and OTEL mirroring all verified correct. But the story's **headline deliverable — the reach gate on `dispatch_dice_throw` — does not function in production**, and the naive fix for that exposes a combat softlock. Two Criticals, both blocking.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [CRITICAL] `[RULE]``[SILENT]` | **Reach gate is DEAD in production.** `getattr(sd, "dungeon_store", None)` reads a nonexistent attribute — `_SessionData` (`session_state.py:8`) has **no `dungeon_store` field** and it is never assigned in prod; the real store is `sd.lookahead_handle.persistence` (`websocket_session_handler.py:986`). So the mask always resolves `None` → `_enforce_tactical_reach` always skips (`reason=no_grid`) → Task 7 never engages on a real DICE_THROW. A NEW silent fallback of the exact class this story exists to delete. Undetected because the wiring test bypasses `DiceThrowHandler.handle()`'s `sd` resolution. | `handlers/dice_throw.py:382` | Resolve the store the same way `websocket_session_handler.py:986` and `intent_router_pass` do: `_lh = getattr(sd, "lookahead_handle", None); dungeon_store = _lh.persistence if _lh else None`. (The Task-8 seating path already does this correctly via the intent-router context — only the DICE_THROW handler is wrong.) |
| [CRITICAL] `[EDGE]` | **Latent softlock exposed by the fix above.** Once the store resolves, the gate fires — but `seat_actor_cells` (`seating.py:79`) is the ONLY writer of `per_actor_state['cell']` (no move dispatch; `adjudicate_tactical_move` has zero prod callers; narration never updates the cell). Seating places the PC at the entrance anchor and the monster at a non-adjacent creature anchor (`materializer.py:1646` attaches tactical blocks to beneath_sünden rooms). A melee strike → out of reach → `raise DiceDispatchError` → the player can neither strike nor move. First-turn-of-grid-combat softlock. Also breaks the Zork-Problem doctrine: narrated "I charge in and swing" can't update the cell, so it's blocked anyway. Contradicts the plan's own §2 ("never blocks a strike spuriously"). | `dice.py:856-857` | Make the reach gate **observability-only** for v1: emit the validated/denied/skipped spans (GM panel sees "out of reach") but DO NOT `raise` — let the strike proceed until a player-move mechanic exists. The enforcement-abort ships WITH movement (a follow-up). Needs an Architect/SM scope confirmation that 165-3 should not abort given deferred movement. |
| [HIGH] `[TEST]` | The abort (`dice.py:857`) — the story's defining behavior — has **zero end-to-end test coverage**. The wiring test stubs `_enforce_tactical_reach`; unit tests bypass `dispatch_dice_throw`; `_resolve_room_mask` short-circuits on `dungeon_store=None` in every test. This is *why* both Criticals slipped through. | tests | Add a real end-to-end test: seated out-of-reach combat + a real store through the **handler** path, asserting the observed behavior (skip-vs-fire), and one covering the store resolution so a dead attribute fails a test. |
| [HIGH] `[TEST]` | `resolve_weapon_range_band_from_beat_and_actor` has **zero unit tests** — every branch (empty inv, pack None, catalog miss, first-band-None-then-real) unexercised; a bug silently resolves ranged→melee. | `combat_rules.py:139` | Add direct unit tests (fixture `_FakeDungeonStore`/catalog). |
| [HIGH] `[TEST]` | dogfight `dungeon_store` forwarding untested (confrontation has a spy test; dogfight has none — same silent-drop class). | `dogfight.py:151` | Add a dogfight-side forwarding test. |
| [MEDIUM] `[DOC]``[SIMPLE]` | `resolve_weapon_range_band_from_beat_and_actor` docstring claims "the **equipped** weapon" but never checks the `equipped` flag (exists, `commands.py:156`) and never uses its `beat` param (dead param; doesn't honor `beat.damage_override`). Mirrors `resolve_damage_spec`'s imperfection but the docstring is inaccurate. | `combat_rules.py:139` | Honor `equipped`/`beat`, or correct the docstring to "first inventory weapon with a range_band." |
| [MEDIUM] `[TYPE]``[RULE]` | `_enforce_tactical_reach` (zero param annotations + no return type), `_resolve_room_mask` and `_seat_tactical_cells` (untyped `snapshot`/`dungeon_store`/`encounter`) — lang-review #3, load-bearing chokepoints imported by tests. | `dice.py:354,337`, `encounter_lifecycle.py:1706` | Annotate (`GameSnapshot`, `RangeAdjudication | None`, etc.). |
| [MEDIUM] `[TEST]` | Scope-gating (spell_id / net_run / non-hp_depletion) and the `attacker_unseated`/`target_unseated` skip reasons have no tests; no ranged spec driven through `_enforce_tactical_reach`. | tests | Add negatives + a ranged/LOS case. |
| [LOW] `[DOC]` | `tactical.move.validated/denied` spans reused for a stationary **reach** check (`cells_spent=0` / `distance_cells`) — misleading event name; missing param docs for `dungeon_store` on 4 functions; `_seat_tactical_cells` room_id-None is a silent no-op (no span); duplicate comment in wiring test. | `tactical.py`, `dice.py`, `encounter_lifecycle.py` | Rename to `tactical.reach.*` or document the repurposed fields; add param docs. |

**Data flow traced:** player DICE_THROW → `DiceThrowHandler.handle()` (`sd`) → `dispatch_dice_throw(dungeon_store=getattr(sd,"dungeon_store",None))` → **None (dead attribute)** → `_resolve_room_mask` → None → `_enforce_tactical_reach` → skip. The gate is unreachable; the story's core AC is unmet.
**Pattern observed:** the getattr-hides-missing-attr silent fallback was copied from `map_emit.py:174` (which uses the same `getattr(sd,"dungeon_store",None)` guarded by a *source-grep* test — itself a "No Source-Text Wiring Tests" violation that masks whether the runtime path is even live). Don't propagate it.
**Error handling:** the abort is game-state-leak-free (fires before seal/apply — verified `dice.py` ordering), but per Critical #2 it should not abort at all in v1.

### Rule Compliance (lang-review/python.md, via rule-checker + my audit)

- **#1 Silent exceptions:** compliant in the literal sense (no bare except; `contextlib.suppress(DiceDispatchError)` is commented) — BUT the No-Silent-Fallbacks *spirit* is violated by the dead `getattr(sd,"dungeon_store",None)` (Critical #1). `_range_band_to_cells` and `adjudicate_reach` correctly **raise** (the story's own fixes). 
- **#2 Mutable defaults:** compliant — every new kwarg defaults to `None`.
- **#3 Type annotations:** **3 violations** — `_enforce_tactical_reach`, `_resolve_room_mask`, `_seat_tactical_cells` (MEDIUM finding above).
- **#6 Test quality:** assertions are specific (no vacuous), monkeypatch targets are "where used" — but coverage of the production path is absent (HIGH findings).
- **#13 Fix-introduced regressions:** the 4 documented 165-2 fixes are correct and test-pinned; the story introduced a NEW silent fallback (Critical #1).
- Checks #4,#5,#7,#8,#9,#10,#11,#12: no violations (verified — `base64.b64decode` of a server-persisted mask is safe #8; the `_NN_RANGE_RE` regex is anchored, no ReDoS #11; star-import matches package convention #10).
- `[SEC]` VERIFIED — no security surface in this diff: no auth/tenant/injection/secret handling; the only external input is a server-persisted ASCII mask (base64-decoded, not deserialized as code) and content-authored `range_band` strings (regex-validated, fail-loud). Evidence: `dice.py:349` decodes to ASCII; `without_number.py:150` raises on unparseable input.

### Devil's Advocate

This code is broken, and the green test suite is a comfort blanket. The entire story claims to "bind C1 into production" and "wire the reach gate" — yet in a real `beneath_sünden` session the gate is a corpse: `handlers/dice_throw.py` hands `dispatch_dice_throw` a `dungeon_store` pulled from an attribute that does not exist on `_SessionData`, so every strike takes the `no_grid` skip and the enforcement the story is *named after* never runs. 1834 tests pass and prove nothing about the one code path a player actually hits, because every test either calls `dispatch_dice_throw` directly (skipping the handler that fabricates the None) or monkeypatches the enforcement function into a no-op. A stressed reviewer sees "GREEN + wiring test" and stamps it; that is exactly the Illusionism OTEL doctrine exists to catch — convincing surface, zero mechanical backing. Now suppose a diligent Dev "fixes" the attribute to `sd.lookahead_handle.persistence`. The gate wakes up and immediately bricks combat: a melee PC is seated at the entrance, the goblin across the cavern, and the *only* writer of an actor's cell is the seater — no move message exists (§4 of the plan: "no new inbound messages in v1"), narration can't budge the token, and `adjudicate_tactical_move` has no caller. The player's first swing raises `DiceDispatchError("target is 3 cells away; your reach is 1")` and the game is unwinnable. Keith's playgroup — the load-bearing audience — hits this on turn one. A confused player would read the refusal as a bug (it is). A malicious player needs to do nothing; the feature self-immolates. And a mixed-loadout fighter who happens to carry an unequipped pistol is silently reclassified "ranged," so the reach gate that *would* fire skips him instead — an inconsistency nobody can predict from the fiction. The honest v1 is observability-only: seat the tokens, emit the spans, let the GM panel see reach, and do not block a strike until movement exists. Ship enforcement with the verb that resolves it.

**Handoff:** Back to TEA (Amos) for red rework — the fixes are testable (store-resolution through the handler + observability-only behavior + the coverage gaps). TEA writes the pinning tests, then Dev implements.

## TEA Assessment (RED Rework — round 2)

**Phase:** finish (rework) — **Tests Required:** Yes
**Skill attested:** `test-driven-development` (fresh entry in `<skills-invoked>`, this round).
**Status:** RED — ready for Dev (Naomi). **Consolidated run: 2 failed (the two Criticals) + 21 passed (coverage + all pre-existing tests in the 2 edited files intact).** `ruff check` clean on all 5 files.

**Scope:** the reviewer REJECTED the green round with two Criticals. Keith RULED the descope: **observability-only for v1** (`epic-165.yaml` review_findings + session Delivery Findings — the gate engages + emits spans but must NOT abort; enforcement-abort ships later WITH the move verb). These tests pin exactly Keith's instruction to TEA: "an out-of-reach melee strike does NOT raise in v1" + "the store resolves through the real handler path."

**The two RED-drivers (fail now — they ARE the Dev fixes):**
| Test | Pins | RED failure (verified) | GREEN when Dev… |
|------|------|------------------------|-----------------|
| `test_dice_throw_handler_dungeon_store_resolution_165_3.py::test_handler_forwards_lookahead_persistence_store_to_dispatch` | Critical #1 — dead attribute | forwards `dungeon_store=None` (the dead `getattr(sd,"dungeon_store",None)`) | resolves the store from `sd.lookahead_handle.persistence` in `handlers/dice_throw.py:382` |
| `test_dice_reach_observability_165_3.py::test_out_of_reach_strike_does_not_abort_and_still_emits_denied_span` | Critical #2 — softlock | gate emits `tactical.move.denied` AND raises `DiceDispatchError("target is 4 cells away; your reach is 1")` | drops the `raise` at `dice.py:856-857` (keep the span) — observability-only |

**Coverage / regression pins (pass now — close the reviewer's "untested" HIGH/MEDIUM, guard against regressions):**
- `test_dice_throw_handler_..._165_3.py::test_session_data_has_no_dungeon_store_field` — reflection tripwire (CLAUDE.md-blessed): fences off the WRONG fix (adding a `dungeon_store` field to `_SessionData` instead of resolving from `lookahead_handle`).
- `test_dice_reach_observability_165_3.py::test_in_reach_strike_emits_validated_span_and_does_not_abort` — skip-vs-fire symmetry (in-reach → validated span, no abort).
- `test_resolve_weapon_range_band_165_3.py` (7) — HIGH: every branch of `resolve_weapon_range_band_from_beat_and_actor` (empty inv, no actor, pack None, absent catalog, catalog miss, skip-bandless-then-return-banded, id-less row).
- `test_encounter_position_seating.py::test_live_dogfight_dispatch_forwards_dungeon_store_to_seating` — HIGH: dogfight subsystem forwards `dungeon_store` to seating (mirrors the confrontation forwarding test).
- `test_dice_tactical_enforcement.py` (+3) — MEDIUM: distinct `attacker_unseated`/`target_unseated` skip-reason spans + a ranged weapon reaching where melee denies.

**Why the split (see deviations):** the reviewer asked for one e2e through `handle()`; driving `handle()` all the way through a real `dispatch_dice_throw` is too heavy/brittle for a clean RED (TEA gotcha 625). File 1 pins the handler store-forwarding (spy `dispatch_dice_throw` at the source symbol + sentinel-raise); File 2 pins the dispatch abort-behavior on the real dispatch with a real store. Together they cover the whole chain. The observability test asserts BOTH "no reach-abort" AND "denied span still fires" so a Dev cannot "fix" the softlock by disabling the gate (Illusionism guard).

### Rule Coverage (lang-review/python.md)
| Rule | Test(s) | Status |
|------|---------|--------|
| #1 No-Silent-Fallbacks (dead `getattr` masks wrong attr) | `test_handler_forwards_lookahead_persistence_store_to_dispatch` + `test_session_data_has_no_dungeon_store_field` | failing (RED) + guard |
| Wiring (real handler path + real store; no source-text, no stub-spy) | `test_handler_forwards_lookahead_persistence_store_to_dispatch` | failing (RED) |
| Observability (gate engaged, not silently disabled — GM panel lie-detector) | `test_out_of_reach_strike_does_not_abort_and_still_emits_denied_span` (asserts denied span fires) | failing (RED) |
| #6 Test quality (meaningful assertions, real behavior not mocks) | all 5 files — real `_SessionData`, real dispatch, real WN binding | pass |
| #3 Type annotations (untyped chokepoints) | not test-pinnable — pyright gate re-verifies (Delivery Finding) | n/a |

**Self-check:** 0 vacuous assertions. The two RED-drivers were run and hand-verified to fail for the EXACT reviewer-cited reasons (dead-attribute → `None`; reach abort → `DiceDispatchError`), not on a typo/collection error. Coverage tests assert concrete values.

**Handoff:** To Dev (Naomi) for GREEN. Two one-area fixes: (1) `handlers/dice_throw.py:382` resolve the store from `sd.lookahead_handle.persistence` (mirror `websocket_session_handler.py:986`); (2) `dice.py:856-857` drop the `raise` (keep the denied span) — observability-only per Keith's ruling. The coverage tests should stay green throughout; if you rename the reach spans to `tactical.reach.*` (reviewer LOW), update the span-name assertions in lockstep.

## Dev Assessment (GREEN Rework — round 2)

**Implementation Complete:** Yes — **GREEN**. Both reviewer Criticals resolved; pre-handoff review CLEAN (no Critical/Important defects in the diff).
**Skills attested (green, this round):** `test-driven-development`, `verification-before-completion`, `requesting-code-review`.

**The two Criticals — fixed and verified:**
- **Critical #1 (reach gate dead in prod):** `handlers/dice_throw.py` now resolves the dungeon store from `sd.lookahead_handle.persistence` (byte-for-byte the prod pattern at `websocket_session_handler.py:985-987`), not the dead `getattr(sd, "dungeon_store", None)`. `_SessionData` has no such field and nothing in `sidequest/` assigns `sd.dungeon_store`, so the old read always resolved `None`. GREEN: `test_handler_forwards_lookahead_persistence_store_to_dispatch` now passes (store forwarded); the reflection tripwire confirms the field stays absent.
- **Critical #2 (softlock):** the reach gate in `dispatch_dice_throw` (`dice.py`) is now OBSERVABILITY-ONLY — it still calls `_enforce_tactical_reach` (emitting validated/denied/skipped spans) but drops the `_reach_verdict` assignment and the `raise DiceDispatchError`. GREEN: `test_out_of_reach_strike_does_not_abort_and_still_emits_denied_span` passes (denied span fires, no abort). `DiceDispatchError` import is NOT orphaned (raised ~20× elsewhere in dice.py).

**Also fixed (reviewer MEDIUM [DOC]):** the stale `_enforce_tactical_reach` docstring ("caller aborts") and the `resolve_weapon_range_band_from_beat_and_actor` docstring ("equipped weapon" → "first inventory weapon with a range_band; `equipped`/`beat` unused"). A final docstring-precision nit from the pre-handoff review was applied ("the gate EMITS the span; the caller does not read the verdict").

**Files changed (4):**
- `sidequest/handlers/dice_throw.py` — resolve `_dungeon_store` from `lookahead_handle.persistence`; pass it to `dispatch_dice_throw`.
- `sidequest/server/dispatch/dice.py` — reach gate observability-only (drop assignment + `raise`); updated block comment + `_enforce_tactical_reach` docstring.
- `sidequest/game/ruleset/combat_rules.py` — corrected `resolve_weapon_range_band` docstring (behavior unchanged).
- `sidequest/server/dispatch/encounter_lifecycle.py` — no net change (a type annotation was added then reverted; see deviation).

**Deferred (reviewer MEDIUM lang-review #3 — type annotations):** adding annotations to `_enforce_tactical_reach`/`_resolve_room_mask`/`_seat_tactical_cells` surfaces **7 latent pyright errors** (an `object`-typed duck store has no `.load_masks()`; the indirect `skip_reason` guard defeats pyright's narrowing of `a_cell`/`mask`). The code is correct — pyright just can't follow the computed guard. A proper fix is a guard-logic refactor + a store Protocol, out of an observability-only rework's scope. Reverted the annotations; the diff is **pyright-NEUTRAL** (38 baseline errors in these files, unchanged). Logged as a deviation + a non-blocking Delivery Finding.

**Verification (fresh):**
- Rework set: **23/23 pass** (both Criticals green, coverage green).
- Regression (dispatch + combat e2e + tactical + telemetry + handler): **1613 passed**, 1 failed — the pre-existing `test_monster_manual_inject.py::test_execute_narration_turn_refreshes_stale_monster_manual` (`CartographyTreatmentWire` + LLM-transport hermeticity), **confirmed failing on the pre-change baseline via `git stash`** (unrelated to this diff).
- `ruff check` + `ruff format --check`: clean on all changed files. `pyright`: 38 (= baseline, zero introduced).

**Branch:** `feat/165-3-enforcement-wiring` (pushed — `e4481df8`).

**Handoff:** To Reviewer (Chrisjen) for the formal review phase.

## Subagent Results (Review Round 2)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | GREEN: 1570 pass / 1 pre-existing fail / 1 skip; ruff+format+pyright(38=baseline) clean; 0 smells | confirmed 0, dismissed 0 (baseline clean; the 1 fail is the known `test_monster_manual_inject` hermeticity issue, unrelated to changed files) |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — None/boundary domain assessed by Reviewer (VERIFIED: `lookahead_handle=None` and `.persistence=None` both → documented no-grid skip) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled — No-Silent-Fallbacks domain assessed by Reviewer + corroborated by rule-checker (VERIFIED: the fix targets a real field; every skip path emits an OTEL span) |
| 4 | reviewer-test-analyzer | Yes | findings | 2 (1 MEDIUM ranged-e2e coverage gap, 1 LOW substring-classification); **empirically confirmed both Criticals' tests fail on the RED commit, pass on HEAD** | confirmed 2, both non-blocking |
| 5 | reviewer-comment-analyzer | Yes | clean | none | N/A — all docstrings/comments accurate; no stale abort/raise language; no `_reach_verdict` remnants |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled — type-invariant domain covered by rule-checker #3 |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled — no auth/tenant/injection/secret surface (server-persisted ASCII mask, session-scoped dict keys); N/A |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled — dead-return-value + redundant `getattr(sd,"lookahead_handle")` assessed by Reviewer (LOW/cosmetic, matches prod idiom) |
| 9 | reviewer-rule-checker | Yes | findings | 3 (all Rule #3 type-annotation gaps on `_enforce_tactical_reach`/`_resolve_room_mask`/`_seat_tactical_cells`) | confirmed 3, all MEDIUM non-blocking (Dev-deferred; rule exempts private helpers; pyright not gate-wired) |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 5 confirmed (all non-blocking), 0 dismissed, 0 unresolved-blocking

## Reviewer Assessment (Review Round 2)

**Verdict:** APPROVED

Both Criticals from my Round-1 rejection are genuinely resolved — and I did not take the author's word for it. `reviewer-test-analyzer` checked out the RED commit (`47c02460`) into a scratch worktree and ran the two headline tests against the *un-fixed* code: both fail for exactly the claimed reasons (`dungeon_store=None`; `'target is 4 cells away; your reach is 1'` raised), and both pass on HEAD. That is the strongest confirmation a static review can produce.

**Critical #1 (reach gate dead in prod) — FIXED.** `handlers/dice_throw.py:373-374` resolves the store from `sd.lookahead_handle.persistence` (an exact copy of the established idiom at `websocket_session_handler.py:985-987`). `lookahead_handle` IS a real `_SessionData` field (`session_state.py:321`); the old `getattr(sd,"dungeon_store",None)` targeted a field that never existed. `[SILENT]` VERIFIED (Reviewer + rule-checker): the fix is not a new silent fallback — `None` off a non-procedural world flows to `tactical_enforcement_skipped_span(reason="no_grid")`, an OTEL-observable boundary, not a swallowed error.

**Critical #2 (softlock) — FIXED.** `dice.py:857-864` calls `_enforce_tactical_reach(...)` bare; the `_reach_verdict` assignment and the `raise DiceDispatchError` are gone. `[SIMPLE]`/`[RULE]` VERIFIED: no dead local, `DiceDispatchError` still raised 23× elsewhere (import not orphaned), both verdict branches still reachable and tested. `[TEST]` VERIFIED: `test_out_of_reach_strike_does_not_abort_and_still_emits_denied_span` asserts the matched pair (`"tactical.move.denied" in span_names` AND `reach_abort is None`) — a Dev cannot pass it by disabling the gate.

**Data flow traced:** player DICE_THROW → `DiceThrowHandler.handle()` resolves `_dungeon_store = sd.lookahead_handle.persistence` → `dispatch_dice_throw(dungeon_store=_dungeon_store)` → `_resolve_room_mask(snapshot, dungeon_store, character_name)` loads the live mask → `_enforce_tactical_reach` emits the reach span (observability-only, no abort). The chain is live end-to-end; the exact break I rejected on is closed.

**Pattern observed:** the store-resolution fix reuses the movement-subsystem idiom verbatim (`websocket_session_handler.py:986`) — good; consistency over invention. Confirmed via `intent_router_pass.py:1180` that the dispatch-bank context already carries `dungeon_store`, so the subsystem-forwarding wiring is live (not just test-passed).

**Error handling:** the gate's `None` boundaries (no `lookahead_handle`; `.persistence` None; no mask; unseated actor) each resolve to a distinct OTEL skip span, not a swallowed default. No new `except`/`suppress` introduced.

### Findings (all non-blocking — none block the PR)

| Severity | Tag | Issue | Location | Disposition |
|----------|-----|-------|----------|-------------|
| [MEDIUM] | `[TEST]` | No end-to-end test drives a REAL ranged-weapon `CatalogItem` through `dispatch → resolve_weapon_range_band → _enforce_tactical_reach`. The ranged path is proven at two isolated layers (unit range-band + unit `_enforce_tactical_reach` with a synthetic `SimpleNamespace` spec) but not glued; a ranged miswiring at `dice.py:851` would not be caught. | tests | CONFIRM, non-blocking → Delivery Finding. In observability-only v1 a miswire emits a wrong span (no player-facing break); the follow-up ranged test lands with the enforcement-abort story. |
| [MEDIUM] | `[TYPE]``[RULE]` | Rule #3: `_enforce_tactical_reach`, `_resolve_room_mask`, `_seat_tactical_cells` untyped. | `dice.py:337,354`, `encounter_lifecycle.py:1706` | CONFIRM severity, non-blocking. Rule #3's own text exempts private (`_`-prefixed) helpers; Dev deferred with a documented rationale (annotating surfaces 7 latent pyright errors requiring a guard-refactor + store Protocol); `pyright` is not wired into any gate (server-lint = ruff only). Accept the deferral. |
| [LOW] | `[TEST]` | `test_dice_reach_observability_165_3.py` classifies a reach-abort by substring-matching the exception message (`"reach"/"range"/"cell"`) rather than a dedicated exception type — refactor-fragile if the wording changes. | `test_dice_reach_observability_165_3.py` | CONFIRM as LOW → Delivery Finding. A `RangeAdjudication`-tagged exception subtype would be sturdier; harmless today (message verified to contain "reach"). |

### Rule Compliance (lang-review/python.md — my audit + rule-checker backstop)

- **#1 No-Silent-Fallbacks:** compliant. The rework DELETES a dead silent fallback (`getattr(sd,"dungeon_store",None)`) and introduces none. Test-side `contextlib.suppress(DiceDispatchError)` carries an explanatory comment (wiring test); the observability test's `except DiceDispatchError` inspects the message, does not discard it. `[SILENT]` VERIFIED.
- **#2 Mutable defaults:** compliant — 16 changed signatures scanned, all `None` defaults; `RANGE_BAND_CELLS` is a read-only class table.
- **#3 Type annotations:** 3 violations (the MEDIUM above). Rule exempts private helpers; deferred. `[TYPE]` confirmed, non-blocking.
- **#6 Test quality:** compliant — no vacuous assertions, `monkeypatch` targets the source symbol with a comment (correct discipline), identity assertions (`is sentinel_store`), reflection tripwire is CLAUDE.md-blessed. `[TEST]` (2 coverage/robustness notes above).
- **#8 Unsafe deserialization:** compliant — `base64.b64decode` of a server-persisted mask to ASCII, not pickle/yaml/eval. `[SEC]` VERIFIED — no security surface.
- **#10 Import hygiene:** compliant — the `from .tactical import *` matches 11 sibling span modules + `__all__`; the local `resolve_inventory` import is a verified required lazy import (real cycle).
- **#13 Fix-introduced regressions:** compliant — no dead variable, no orphaned import, no unreachable branch from the observability descope. `[EDGE]` VERIFIED (None boundaries) / `[DOC]` VERIFIED (comment-analyzer clean).
- Checks #4,#5,#7,#9,#11,#12: no violations (no new logging/paths/resources/blocking-async/input-boundaries/deps).

### Devil's Advocate

Let me try to break this. The seductive failure mode is that I am reviewing my own rejection being answered, and I *want* it closed — so assume the fix is a mirage. First attack: is `getattr(sd, "lookahead_handle", None)` just the *next* dead attribute, the same bug wearing a new coat? No — I verified `lookahead_handle` is a declared `_SessionData` field (`session_state.py:321`), unlike `dungeon_store` which was never a field; and the movement subsystem has read it this exact way in production for real Beneath Sünden sessions. The `getattr` is stylistically redundant (the field always exists) but targets a real attribute, so it cannot silently resolve `None` the way the old one did — and even if it did, the failure is a documented no-grid skip span, not a corruption. Second attack: does making the store *live* now re-expose the softlock I feared? No — the abort is gone; the gate only emits spans, and the matched-pair test forbids both re-adding the raise and silently disabling the gate. Third attack: the ranged path. Here the code is genuinely thinner than it looks — a real ranged `CatalogItem` never rides the full dispatch chain in any test, so a wrong `actor_core`/`world_slug` at the call site would sail through green. But in observability-only v1 that produces a mislabeled GM-panel span, not a player-facing wrong outcome (the strike proceeds regardless of verdict) — a real gap, correctly sized as MEDIUM and deferred to the enforcement-abort story that will make the ranged verdict load-bearing. Fourth attack: the out-of-diff coherence gap — the player-visible `TACTICAL_GRID` is still emitted from the dead `sd.dungeon_store` in `map_emit.py:174`, so the gate now checks a grid the client may not render. Real, but out of scope, pre-existing, pinned by a lint pending Plan 7, and non-player-breaking in observability-only mode. What would a malicious player do? Nothing — there is no new external input; the mask is server-persisted, the character/room keys are session-scoped. What would a confused player see? In v1, nothing changes for them — the gate is invisible except to the GM panel. Nothing here rises to Critical or High. The rejection was earned; the answer is honest.

**Handoff:** To SM (Camina Drummer) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Conflict** (blocking): `range_band` has a schema-vs-content format mismatch that Dev must resolve to make BLOCKER 1 green. `CatalogItem.range_band` is *documented* categorical (`"rifle"|"pistol"|…`, `inventory.py:214`) but ALL real content authors `"N/N"` metre strings (`"10/30"`…`"600/2400"`, 16 distinct, 8 files), and `DamageSpec` (what `resolve_damage` returns) has NO `range_band` field at all. Affects `sidequest/game/ruleset/without_number.py` (`weapon_range_cells`) AND the dispatch call-site plumbing (`dice.py` — the resolved spec must carry the band to the gate; today it can't). Decide: parse `"N/N"`→cells, OR add a categorical band to `DamageSpec` + a `"N/N"`→band map, OR map at the call site. My RED test is fix-agnostic (ranged + range-tracking, not a pinned formula). *Found by TEA during test design.*
- **Gap** (blocking): the Task-8 seating chokepoint `instantiate_encounter_from_trigger` (`encounter_lifecycle.py`) has NO `dungeon_store` access — the plan says to read `dungeon_store.load_masks()` inside it, but the store is only reachable via `sd.dungeon_store` (`map_emit.py:174`) and `sd` is not in scope there. Dev/Architect must pick the plumbing: add a `dungeon_store=` kwarg (what my RED test pins), thread `sd`, or have the caller seat after instantiation. Affects `sidequest/server/dispatch/encounter_lifecycle.py`. *Found by TEA during test design.*
- **Gap** (non-blocking): Task 7's reach gate must abort the strike with a legible refusal on an out-of-range verdict (reuse the handler's existing denied-throw/refusal channel) and NOT silently retarget (SOUL: The Test). My unit tests assert the verdict shape; the abort-broadcast wiring is Dev's to land and should get its own behavior/OTEL assertion. Affects `sidequest/server/dispatch/dice.py` (`dispatch_dice_throw` call site). *Found by TEA during test design.*
- **Improvement** (non-blocking): Task 6's plan snippet (`docs/.../mapping-track-c-*.md` ~L843) omits the recording-tracer fixture, so its own test would never fire the mirror (`_mirror` skips NonRecordingSpans). My test corrects it with `capture_spans`; Dev should not copy the plan's test verbatim. *Found by TEA during test design.*
- **(RED rework) Improvement** (non-blocking): `resolve_weapon_range_band_from_beat_and_actor` ignores its `equipped` flag AND its `beat` param while the docstring claims "the equipped weapon" — a mixed-loadout PC carrying an *un*equipped ranged weapon is silently reclassified `ranged` (reviewer MEDIUM). I deliberately did NOT pin the `equipped` semantics — it is an OPEN decision (honor `equipped`/`beat` OR correct the docstring). My unit tests pin the CURRENT "first inventory item with a catalog `range_band`" behavior only. Affects `sidequest/game/ruleset/combat_rules.py`. *Found by TEA during test design (rework).*
- **(RED rework) Gap** (non-blocking): span-name coupling — the observability + skip-reason tests assert the CURRENT span names (`tactical.move.validated`, `tactical.move.denied`, `tactical.enforcement.skipped`). The reviewer's LOW finding suggests renaming the reach spans to `tactical.reach.*` (they're stationary reach checks logged under *move* names). If Dev takes the rename, `tests/integration/test_dice_reach_observability_165_3.py` + the skip-reason tests in `test_dice_tactical_enforcement.py` must update in lockstep. Affects `sidequest/telemetry/spans/tactical.py` + those two test files. *Found by TEA during test design (rework).*
- **(RED rework) Gap** (non-blocking): the reviewer's lang-review #3 (untyped `_enforce_tactical_reach`/`_resolve_room_mask`/`_seat_tactical_cells`) is a Dev fix not meaningfully test-pinnable — `pyright` in the review gate re-verifies it. Not covered by a test; noted so it isn't lost. Affects `sidequest/server/dispatch/dice.py`, `sidequest/server/dispatch/encounter_lifecycle.py`. *Found by TEA during test design (rework).*

### Dev (implementation)
- **Improvement** (non-blocking): the reach gate resolves the weapon `range_band` (`resolve_weapon_range_band_from_beat_and_actor`) AND `resolve_damage` later re-resolves the same inventory — two inventory resolutions per WN combat strike. Fine at current scale (mirrors the existing per-strike `resolve_damage` cost and the room-scale `load_masks()` pattern in `map_emit.py`) but a natural single-resolution consolidation. Affects `sidequest/server/dispatch/dice.py`. *Found by Dev during implementation.*
- **Improvement** (non-blocking): `resolve_weapon_range_band_from_beat_and_actor` returns the FIRST equipped weapon carrying a `range_band`, so an actor with both a melee weapon and a holstered ranged weapon reads as ranged (a lenient false-ALLOW — the melee reach gate won't fire). This mirrors the same first-weapon ambiguity in `resolve_damage_spec_from_beat_and_actor` and errs toward not blocking a legitimate action (no regression vs the no-gate baseline). A precise fix needs the beat to name WHICH weapon is used. Affects `sidequest/game/ruleset/combat_rules.py`. *Found by Dev during implementation.*
- **Improvement** (non-blocking): ranged range enforcement is now *reachable* (real `range_band` → `weapon_range_cells` → the ranged/LOS path) but on a room-scale grid a ranged band resolves to a large cell cap, so LOS is the binding constraint and ranged strikes are effectively always in-range unless a wall blocks — which is correct for v1. The player-facing range echo on the resolution card (short/long/beyond bands, penalties) is plan Task 9 / 165-4 territory, not wired here. Affects `sidequest/server/websocket_handlers/map_emit.py` (165-4). *Found by Dev during implementation.*
- **Improvement** (non-blocking): the reach validation reuses `tactical_move_validated_span` / `tactical_move_denied_span` (with `cells_spent=0` on the validated path) — semantically a *reach* check logged under a *move* span name. Cosmetic; the span carries the correct verdict fields for the GM panel. A dedicated `tactical.reach.*` span pair would read cleaner. Affects `sidequest/telemetry/spans/tactical.py`. *Found by Dev during implementation.*
- **(GREEN rework) Gap** (non-blocking): the SAME dead `getattr(sd, "dungeon_store", None)` that Critical #1 fixed still lives in the player-facing grid-emit path — `map_emit.py:174` (`_maybe_build_runtime_cavern_payload`) and `websocket_session_handler.py:1622` (setpiece attach). Both resolve `None` in prod (nothing assigns `sd.dungeon_store`). So the reach gate now loads its mask from the LIVE `lookahead_handle.persistence` while the `TACTICAL_GRID` the player actually sees is emitted from the DEAD attribute — on a procedural world the gate could check a grid the emit path can't render. Out of this rework's scope; `map_emit.py`'s shape is grep-pinned by `tests/dungeon/test_setpiece_attach_wiring.py` pending "Plan 7". Unify the two store resolutions there. Affects `sidequest/server/websocket_handlers/map_emit.py`, `sidequest/server/websocket_session_handler.py`. *Found by Dev during implementation (surfaced by the pre-handoff review).*
- **(GREEN rework) Gap** (non-blocking): reviewer lang-review #3 (type annotations on `_enforce_tactical_reach`/`_resolve_room_mask`/`_seat_tactical_cells`) is DEFERRED — adding them surfaces 7 latent pyright errors (object-typed duck store lacks `.load_masks()`; the indirect `skip_reason` guard defeats narrowing of `a_cell`/`mask`). Proper fix = refactor the guard to explicit early-returns + type the store as a Protocol. Affects `sidequest/server/dispatch/dice.py`, `sidequest/server/dispatch/encounter_lifecycle.py`. *Found by Dev during implementation.*
- **(GREEN rework) Improvement** (non-blocking): the GM panel should label a v1 `tactical.move.denied` span as "reach check failed" (a verdict), NOT "strike blocked" — in observability-only mode the strike proceeds, so a "blocked" label would misread the lie-detector. Affects the GM-panel span rendering (165-4 / dashboard). *Found by Dev during implementation (raised by the pre-handoff review).*

### Reviewer (code review)
- **Gap** (blocking): the reach gate is dead in production — `getattr(sd, "dungeon_store", None)` reads a nonexistent `_SessionData` attribute; the real store is `sd.lookahead_handle.persistence`. Affects `sidequest/handlers/dice_throw.py:382` (resolve via `lookahead_handle` like `websocket_session_handler.py:986`). *Found by Reviewer during code review.*
- **Conflict** (blocking): enforcing reach with an abort while the player-move mechanic is deferred softlocks melee combat (seated actors are non-adjacent, no way to close distance). Affects `sidequest/server/dispatch/dice.py:856`. **SCOPE RULED (Keith, 2026-07-09): OBSERVABILITY-ONLY for v1** — the gate must engage (fix the dead attribute), seat positions, and emit the reach validated/denied/skipped spans for the GM panel, but **must NOT `raise`/abort the strike**. The enforcement-abort ships in a later story WITH the player-move verb. TEA: pin "an out-of-reach melee strike does NOT raise in v1" + the store resolves through the real handler path. *Found by Reviewer during code review.* *Scope ruled by Keith.* *Found by Reviewer during code review.*
- **Gap** (blocking): the enforcement abort + `resolve_weapon_range_band` + `_resolve_room_mask` + dogfight forwarding have no production-path/unit tests. Affects the test suite (add end-to-end handler-path + helper unit coverage). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `resolve_weapon_range_band_from_beat_and_actor` ignores the `equipped` flag and its `beat` param while its docstring claims "equipped weapon"; three new chokepoint helpers are untyped (lang-review #3). Affects `sidequest/game/ruleset/combat_rules.py`, `sidequest/server/dispatch/dice.py`, `sidequest/server/dispatch/encounter_lifecycle.py`. *Found by Reviewer during code review.*
- **(Round 2) RESOLVED:** the three Round-1 blocking findings above are all closed by the rework — Critical #1 (store resolves from `lookahead_handle.persistence`), Critical #2 (gate is observability-only, no abort), and the test-coverage gap (handler-path store test + observability test + range-band units + dogfight forwarding). The docstring inaccuracy was corrected. Empirically verified: both Criticals' tests fail on the RED commit, pass on HEAD. *Confirmed by Reviewer during code review (round 2).*
- **(Round 2) Gap** (non-blocking): no end-to-end test drives a REAL ranged-weapon `CatalogItem` through `dispatch_dice_throw → resolve_weapon_range_band_from_beat_and_actor → _enforce_tactical_reach`; the ranged path is proven only at isolated unit layers. A ranged miswiring at the dispatch call site would not be caught. Non-player-breaking in observability-only v1. Affects the test suite (`sidequest/server/dispatch/dice.py:851` call site). Land the ranged e2e test with the enforcement-abort follow-up. *Found by Reviewer during code review (round 2).*
- **(Round 2) Improvement** (non-blocking): `test_dice_reach_observability_165_3.py` classifies a reach-abort by substring-matching the exception message (`"reach"/"range"/"cell"`) rather than a dedicated exception type — refactor-fragile. A `RangeAdjudication`-tagged `DiceDispatchError` subtype would be sturdier. Affects `tests/integration/test_dice_reach_observability_165_3.py`. *Found by Reviewer during code review (round 2).*
- **(Round 2) Gap** (non-blocking): the same dead `getattr(sd,"dungeon_store",None)` still lives in the player-facing grid-emit path (`map_emit.py:174`, `websocket_session_handler.py:1622`), so the reach gate now reads the LIVE store while the visible `TACTICAL_GRID` is emitted from the DEAD one. Pre-existing, out of this diff, pinned by `test_setpiece_attach_wiring.py` pending Plan 7; non-player-breaking in observability-only v1. Unify the two resolutions in Plan 7. Affects `sidequest/server/websocket_handlers/map_emit.py`. *Confirmed by Reviewer during code review (round 2; also logged by Dev).*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Replaced the 165-2 test that pinned the `weapon_range_cells` silent rifle-fallback**
  - Spec source: `sprint/archive/165-2-session.md` Delivery Findings + `context-story-165-3.md` §Carryover BLOCKER 2a
  - Spec text: 165-2 shipped `test_weapon_range_cells_unknown_band_defaults_to_rifle` asserting an unknown band silently caps at rifle, and filed the fail-loud-vs-keep decision as a Delivery Finding for THIS story to resolve.
  - Implementation: deleted that test; added `test_weapon_range_cells_garbage_band_fails_loud` asserting `pytest.raises(ValueError)` on a genuine garbage band. Kept the categorical `"rifle"` back-compat tests (`test_weapon_range_cells_melee_and_ranged`, `test_tactical_facts_authored_once...`) green.
  - Rationale: No-Silent-Fallbacks (CLAUDE.md/SOUL) — a mistyped weapon range shipping as a 40-cell rifle is exactly the masked-config bug the rule forbids; this story wires the gate, so the finding is now due.
  - Severity: minor
  - Forward impact: Dev's `weapon_range_cells` must fail loud on garbage AND parse real `"N/N"` bands (BLOCKER 1) while preserving categorical `"rifle"`/… back-compat — a three-way branch, not a one-line raise.
- **Two coverage-backfill tests pass green in a RED phase (not new-behavior TDD)**
  - Spec source: `context-story-165-3.md` §Carryover from 165-1 ("close the 165-1 coverage gaps as you consume the library")
  - Spec text: `line_of_sight` endpoint-exclusion and `aoe_burst(require_los=False)` are untested.
  - Implementation: added `test_line_of_sight_excludes_endpoints` + `test_aoe_burst_ignores_los_when_disabled` — they characterize EXISTING (already-shipped 165-1) C1 behaviour, so they pass immediately rather than fail-first.
  - Rationale: the carryover explicitly assigns this backfill to 165-3; they pin behaviour the Task-7 reach gate now depends on (regression guards). The mode-tightening test IS new behaviour and is RED.
  - Severity: trivial
  - Forward impact: none — pure regression guards; clearly labelled as characterization in the file.
- **(RED rework) Split the reviewer's single "end-to-end handler-path" test into two layered tests**
  - Spec source: session Reviewer Assessment, HIGH `[TEST]` ("Add a real end-to-end test: seated out-of-reach combat + a real store through the handler path, asserting the observed behavior, AND one covering the store resolution so a dead attribute fails a test")
  - Spec text: implies one monolithic e2e through `DiceThrowHandler.handle()` with a fully-real `dispatch_dice_throw`, plus a store-resolution test.
  - Implementation: File 1 (`test_dice_throw_handler_dungeon_store_resolution_165_3.py`) drives the REAL `handle()` with the store on `sd.lookahead_handle.persistence` and asserts it forwards to dispatch (pins Critical #1); File 2 (`test_dice_reach_observability_165_3.py`) drives the REAL `dispatch_dice_throw` with a real store + out-of-reach seating and asserts observability-only (pins Critical #2). No single test drives `handle()` all the way through a real dispatch.
  - Rationale: driving `handle()` through a fully-real `dispatch_dice_throw` (damage resolution, room broadcast, confrontation clear) is too heavy/brittle for a clean RED (TEA gotcha 625). The split covers the same chain at the layer each bug actually lives — handler store-forwarding vs dispatch abort-behavior — and each fails cleanly on its own bug.
  - Severity: minor
  - Forward impact: none.
- **(RED rework) Several rework tests pass green in a RED phase (coverage of already-correct code)**
  - Spec source: session Reviewer Assessment, HIGH `[TEST]` (range_band unit coverage, dogfight forwarding) + MEDIUM `[TEST]` (distinct skip-reasons, ranged case)
  - Spec text: these subsystems are "untested" — a coverage gap, not an asserted behavior bug.
  - Implementation: File 3 (7 range_band units), File 4 (dogfight forwarding), File 5 (attacker/target_unseated + ranged) characterize EXISTING correct code, so they pass immediately. Only the two Criticals fail-first.
  - Rationale: the reviewer's asks are a mix of behavior-change (the Criticals — TDD fail-first) and coverage-gap (HIGH/MEDIUM — TDD "add tests for existing code"). Both are legitimate; conflating them would either skip needed coverage or fake-fail correct code.
  - Severity: trivial
  - Forward impact: none — each is labelled as characterization/regression in its file.

### Dev (implementation)
- **Extended the reach gate beyond the plan's "spec=None melee default" to resolve the real weapon range_band + scope to combat**
  - Spec source: `docs/superpowers/plans/2026-07-08-mapping-track-c-tactical-mechanics.md` Task 7 (~L1704), `context-story-165-3.md` §Carryover BLOCKER 1
  - Spec text: "Task 7 reads the weapon's `range_band` via the resolved `spec` (defaulting to melee when absent) … the safe default (melee) is correct for the common cavern case and never blocks a strike spuriously."
  - Implementation: the dispatch `spec` is a `DamageSpec` with NO `range_band`, so a plain melee default would false-DENY ranged strikes once seating went live (surfaced by the pre-handoff review). Added `resolve_weapon_range_band_from_beat_and_actor` to surface `CatalogItem.range_band` and feed a real band to the gate; gate scoped to `cdef.win_condition == "hp_depletion"`.
  - Rationale: "bind C1 into production" + No Silent Fallbacks require the gate to be *correct and live*, not a melee-only stub that breaks ranged. This also makes BLOCKER 1's N/N parser reachable in production rather than dead-code-until-a-follow-up.
  - Severity: minor
  - Forward impact: none for 165-4/5; the range echo on the resolution card (Task 9) remains a clean follow-up. First-weapon ambiguity noted as a non-blocking finding.
- **Wired `dungeon_store` through the two live subsystem dispatchers (beyond the plan's single-chokepoint scope)**
  - Spec source: plan Task 8 (chokepoint `instantiate_encounter_from_trigger`), TEA blocking finding on the missing `dungeon_store` access
  - Spec text: Task 8 modifies only `instantiate_encounter_from_trigger` to seat from `dungeon_store.load_masks()`.
  - Implementation: added the `dungeon_store` kwarg there AND threaded it through `run_confrontation_dispatch` + `run_dogfight_dispatch` (the live callers), so seating actually runs in production. The store was already in the dispatch-bank context; only the entrypoint params needed declaring (the `_filter_context_for_callable` seam wires it).
  - Rationale: the plan's single-file scope leaves the feature half-wired (the pre-handoff review's Critical). "No half-wired features" (CLAUDE.md) requires the full pipeline.
  - Severity: minor
  - Forward impact: none — additive optional params; non-dungeon sessions pass `None` and no-op.
- **(GREEN rework) Reach gate is OBSERVABILITY-ONLY — dropped the abort the plan called for**
  - Spec source: `docs/superpowers/plans/2026-07-08-mapping-track-c-tactical-mechanics.md` Task 7; overridden by `sprint/epic-165.yaml` review_findings + session Delivery Findings (Keith ruling 2026-07-09)
  - Spec text: plan Task 7 — "On a denied verdict the caller aborts the strike with a legible refusal — never silently corrected."
  - Implementation: the caller no longer reads the verdict or raises `DiceDispatchError`; `_enforce_tactical_reach` runs only for its span side-effects. The enforcement-abort ships in a later story WITH the player-move verb.
  - Rationale: with no move mechanic to resolve a denial, an abort softlocks combat on turn one (seating places actors non-adjacent). Keith ruled observability-only for v1 — story/epic scope outranks the (now stale) plan text.
  - Severity: major (changes the headline feature's behavior)
  - Forward impact: the abort + its consuming logic land in the movement follow-up; `_enforce_tactical_reach` already returns the verdict (dead at the call site today) so that story is pure wiring.
- **(GREEN rework) Deferred the reviewer's type-annotation MEDIUM (#3) to keep the diff pyright-neutral**
  - Spec source: session Reviewer Assessment, MEDIUM `[TYPE][RULE]` (lang-review #3)
  - Spec text: annotate `_enforce_tactical_reach`, `_resolve_room_mask`, `_seat_tactical_cells` (untyped chokepoints).
  - Implementation: added annotations, observed +7 pyright errors (object-typed store → no `.load_masks()`; indirect `skip_reason` guard defeats narrowing), then REVERTED them. Diff stays at the 38-error baseline for these files.
  - Rationale: a correct annotation set requires a guard-logic refactor + a store Protocol — out of an observability-only rework's scope. Shipping 7 new pyright errors (or an unbounded type-refactor) is worse than deferring a MEDIUM that already shipped unannotated in round 1.
  - Severity: minor
  - Forward impact: #3 remains open as a non-blocking Delivery Finding; a future typing pass refactors the guard and adds the annotations together.

### Reviewer (audit)
- **TEA — replaced the 165-2 rifle-fallback test** → ✓ ACCEPTED: correct application of No-Silent-Fallbacks; the categorical back-compat tests were preserved.
- **TEA — two green characterization backfill tests** → ✓ ACCEPTED: honestly labeled as characterization of shipped C1; the mode-tightening test IS a real RED.
- **Dev — extended the reach gate to resolve range_band + scope to combat** → ✗ FLAGGED: the intent is right, but the helper ignores `equipped`/`beat` (docstring inaccurate), and the gate it feeds is dead in prod + softlocks on fix. See Critical #1/#2 and the MEDIUM range_band finding.
- **Dev — wired dungeon_store through the two live subsystem dispatchers (seating path)** → ✓ ACCEPTED: the *seating* wiring (confrontation/dogfight → instantiate → _seat_tactical_cells) is verified correct end-to-end (real store resolved in `intent_router_pass`, forwarded via the dispatch-bank context-filter). This deviation is sound.
- **UNDOCUMENTED (Reviewer-spotted):** the DICE_THROW handler's store resolution (`dice_throw.py:382`) uses a DIFFERENT, incorrect pattern (`getattr(sd, "dungeon_store", None)`) than the seating path's correct `lookahead_handle.persistence` — an inconsistency the Dev did not log. Spec/intent: the reach gate loads the room mask. Code: it loads `None`, always. Severity: **Critical** (Critical #1). This is the reason the two halves of the story diverge — seating works, enforcement is dead. → **(Round 2) RESOLVED:** the rework fixes exactly this — `dice_throw.py:373-374` now uses `lookahead_handle.persistence`, matching the seating path. Verified.

**(Round 2 — rework deviations audited):**
- **TEA — split the reviewer's single e2e test into two layered tests (handler store-forwarding + dispatch observability)** → ✓ ACCEPTED: the split covers the full chain at the layer each bug lives; `reviewer-test-analyzer` empirically confirmed both tests fail-first on the RED commit and pass on HEAD. Driving `handle()` through a fully-real dispatch would have been brittle; the decomposition is sound.
- **TEA — coverage tests pass green in a RED phase (characterization of already-correct code)** → ✓ ACCEPTED: honestly labeled; the two genuine RED-drivers (the Criticals) fail-first, the coverage tests close the "untested" findings. Correct application of TDD's "add tests for existing code."
- **Dev — reach gate is OBSERVABILITY-ONLY, dropped the abort the plan called for** → ✓ ACCEPTED: this IS Keith's ruling (`epic-165.yaml` + session Delivery Findings), not a unilateral simplification; story/epic scope outranks the stale plan text. Implementation is clean (no dead code, spans preserved, matched-pair test guards against silent gate-disable).
- **Dev — deferred the type-annotation MEDIUM (#3) to keep the diff pyright-neutral** → ✓ ACCEPTED: Rule #3 exempts private (`_`-prefixed) helpers by its own text; annotating surfaces 7 latent pyright errors requiring a guard-refactor + store Protocol (out of scope); `pyright` is not wired into any gate. Deferring a non-blocking MEDIUM that shipped unannotated in round 1 is the right call; recorded as a Delivery Finding.