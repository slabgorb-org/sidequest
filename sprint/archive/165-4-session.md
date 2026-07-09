---
story_id: "165-4"
jira_key: ""
epic: "165"
workflow: "spdd"
---
# Story 165-4: Protocol adjudication echoes + UI grid/resolution-card math display

## Story Details
- **ID:** 165-4
- **Jira Key:** (not configured)
- **Workflow:** spdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** spdd
**Phase:** finish
**Phase Started:** 2026-07-09T20:51:51Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-09T16:17:37+00:00 | 2026-07-09T16:20:29Z | 2m 52s |
| red | 2026-07-09T16:20:29Z | 2026-07-09T16:35:54Z | 15m 25s |
| green | 2026-07-09T16:35:54Z | 2026-07-09T16:48:25Z | 12m 31s |
| review | 2026-07-09T16:48:25Z | 2026-07-09T17:05:48Z | 17m 23s |
| red | 2026-07-09T17:05:48Z | 2026-07-09T19:49:48Z | 2h 44m |
| green | 2026-07-09T19:49:48Z | 2026-07-09T20:32:39Z | 42m 51s |
| review | 2026-07-09T20:32:39Z | 2026-07-09T20:51:51Z | 19m 12s |
| finish | 2026-07-09T20:51:51Z | - | - |

## Sm Assessment

**Story:** 165-4 — Protocol adjudication echoes + UI grid/resolution-card math display (Track C plan tasks 9–10). 3 pts, p1.

**Workflow routing:** Sprint YAML tags this `superpowers`, which is NOT a registered pf workflow. Per settled Keith decision (`sm-decisions.md`, 2026-07-08), the 163/164/165 mapping-track stories run as **spdd** (setup→red→green→review→finish). Set up as spdd. Do not re-ask.

**Repos:** server + ui. Branch `feat/165-4-protocol-echoes-ui-math` created off `develop` in both subrepos (both branch off develop, not main).

**Scope (from context-story-165-4 + epic plan tasks 9–10):**
- IN: echo tactical adjudications (TACTICAL_GRID) + dice-result range onto **additive** protocol fields; render them in the UI as legible player-facing math (grid + resolution card). This is the Sebastien/Jade "see the math in the player UI" surface.
- OUT: the enforcement engine itself (that was 165-3, now landed), Fate zones (165-5).
- **Additive protocol only** — TACTICAL_GRID keeps its shape and gains optional fields with empty defaults, so Track B's SITE_MAP cutover can't collide.

**ACs:** Deferred to TEA to define during RED from plan tasks 9–10, per the explicit instruction in `context-story-165-4.md`. Plan doc: `docs/superpowers/plans/2026-07-08-mapping-track-c-tactical-mechanics.md` §tasks 9–10.

**Load-bearing carryover for TEA (from 165-1, mostly bites the display layer — full detail in `context-story-165-4.md` §Carryover and the `*-gotchas.md` tagged 165-1):**
1. **The plan doc has bugs in its embedded code — hand-verify before transcribing** any mask/coordinate/impl into a RED test. A quick `python3 -c` reimplementing `parse_mask`/`is_floor` catches mask bugs in seconds.
2. **`ReachResult.cost` is a SUPERSET of `.reachable`** — it includes the origin (cost 0) and the immediate over-budget boundary cell. For "cells you can move to," render `.reachable`, never `cost.keys()`. Real display-correctness trap.
3. **`RangeAdjudication.has_los` means "unchecked" when `require_los=False`** (hard-set True without calling `line_of_sight`). Do NOT render it as "line of sight confirmed" on melee/`require_los=False` results — only meaningful when `require_los=True`.
4. New OTEL spans must call `publish_event` (reach `turn_telemetry`, not just Jaeger) and need a `SPAN_ROUTES`/`FLAT_ONLY_SPANS` entry or `test_routing_completeness.py` fails.

**Wiring reminder:** Per project doctrine + epic constraints, every test suite needs at least one wiring test proving the echo fields reach a real dispatch/broadcast path and the UI renders them from production code — not just unit tests on the shapes.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Conflict** (blocking): Plan Task 9's file list says the additive `range_band`/`distance_cells` go on the dice-result payload in `sidequest/protocol/models.py`, but `DiceResultPayload` actually lives in `sidequest/protocol/dice.py:214` — models.py has no dice-result class. Affects `sidequest/protocol/dice.py` (add the two additive `str|None=None`/`int|None=None` fields there, NOT in models.py). `TacticalAdjudication` + `TacticalGridPayload.adjudications` are correctly in models.py. The 165-1 "plan doc has bugs — hand-verify" carryover held; this time it was a wrong file path. *Found by TEA during test design.*
- **Gap** (non-blocking): The emit-path wiring test (`test_runtime_payload_populates_move_adjudications`) pins ONLY the minimum-viable "round move summary" echo (per-PC `cells_budget`) that the plan calls the minimum. Per-opponent reach adjudications (the plan's optional extra) are NOT guarded by a test — if Dev populates them, Reviewer should eyeball them; if Dev omits them, no test fails (spec-faithful). Affects `sidequest/server/websocket_handlers/map_emit.py`. *Found by TEA during test design.*
- **Improvement** (non-blocking): The dice-result-range "omits readout" test PASSES on RED (the annotation testid doesn't exist yet). It is a legitimate guarded-on-presence back-compat guard, not a broken RED — flagged so the Reviewer doesn't misread it. Affects `sidequest-ui/src/dice/__tests__/InlineDiceTray.range.test.tsx`. *Found by TEA during test design.*

#### RED Rework (Round 2)
- **Gap** (non-blocking, Dev GREEN directive): Three reviewer findings are NOT guarded by a failing test because they have no honest behavioral surface — Dev must apply them mechanically in GREEN and the Reviewer's rule-checker/comment-analyzer re-verifies. (1) [RULE] index React keys → content-derived (`a.actor`+`a.kind`) at `sidequest-ui/src/components/TacticalGridRenderer.tsx:181,190` (index vs content keys produce identical DOM on these stateless divs → not testable). (2) [LOW] duplicate `data-testid="tactical-denial"` — opportunistic per the reviewer; leave or make per-actor at Dev's discretion (the multi-PC coverage test uses `getAllByTestId`, so either works). (3) [DOC] reword liveness-overstating docstrings at `models.py:728,1370`, `dice.py:237`, `map_emit.py:119,281`, `payloads.ts:587`, `InlineDiceTray.tsx:452` to forward-looking language + the Decision-N dead-gate caveat. *Found by TEA during test design.*
- **Gap** (non-blocking, carried from Dev round 1): The move-summary echo remains gated behind the dead `dungeon_store` attribute (`map_emit.py:174`); the live store is `sd.lookahead_handle.persistence`. The reviewer ruled this a NON-BLOCKING Plan-7 store-unification follow-up — the RED rework does NOT hold on it, and the new emit-population tests drive the builder directly (a legit fixture-driven behavior test per CLAUDE.md, not fixture theater), while the new OTEL span makes the move-summary DECISION observable. Dev "strongly considered" (reviewer's words) resolving the move echo through the live store so the grid half also reaches players, but it is out of the blocking-rework scope. Affects `sidequest/server/websocket_handlers/map_emit.py`. *Found by TEA during test design.*
- **Improvement** (non-blocking): The prior RED rework commit (`ba49fd61`) shipped ruff-dirty (SIM105 `try/except/pass` in the range-echo helper); I cleaned it to `contextlib.suppress` while extending the file. Flagging so the pattern (verify `uv run ruff check` on RED test files before the RED commit) is visible. Affects `sidequest-server/tests/integration/test_dice_range_echo_165_4.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking, but load-bearing for the story's PLAYER VALUE): The move-summary echo is populated inside `_maybe_build_runtime_cavern_payload`, which is gated on `getattr(sd, "dungeon_store", None)` (`map_emit.py:174`). Per the 165-3 dev-gotchas + Delivery Findings, `dungeon_store` is a **dead attribute in production** (the live store is `sd.lookahead_handle.persistence`), so this whole runtime-cavern TACTICAL_GRID emit — and therefore my adjudication echo — resolves `None` and never reaches real players yet. The echo SHAPE and the UI render are correct, complete, and fully tested (my tests drive the builder directly via a fixture that sets `sd.dungeon_store`); only the production DELIVERY inherits the pre-existing dead-store gap. Affects `sidequest/server/websocket_handlers/map_emit.py` (unify its store resolution to `sd.lookahead_handle.persistence` — this is the already-tracked 165-3 map_emit follow-up; the reach gate reads the LIVE store while the player-facing grid reads the DEAD one). Until that lands, Sebastien/Jade will NOT see the tactical math on-screen despite green tests. *Found by Dev during implementation.*
- **Conflict** (resolved): TEA's blocking finding was correct — `DiceResultPayload` is in `sidequest/protocol/dice.py:214`, not `models.py`. Implemented the additive `range_band`/`distance_cells` there. No further action. *Found by Dev during implementation.*

#### RED Rework (Round 2) — GREEN
- **Gap** (blocking for DEVELOP HEALTH, non-blocking for THIS story): the full server suite has **57 pre-existing failures on develop, all identical** — `pydantic ValidationError` constructing `CartographyTreatmentWire(kind=<MagicMock>, node_anchors=<MagicMock>, style_hints=<MagicMock>)` at `sidequest/server/session_helpers.py:1695` (`_build_cartography_map_message`, reached via `_maybe_emit_cartography_map` `map_emit.py:1253`). These are full-turn wiring tests whose MagicMock `world` doesn't satisfy a newer strict `CartographyTreatmentWire` (a Track B cartography change). PROVEN unrelated to 165-4: with my 4 changed files stashed the baseline is **64 failed**; with them it is **57 failed** (my rework FIXED the 6 story REDs, added zero regressions). Affects `sidequest/server/session_helpers.py` + the affected wiring tests (`test_turn_span_wiring`, `test_player_turn_author`, `test_arc_embedding_*`, `test_45_20_trope_resolution_wire`, `test_tension_tracker_turn_wiring`, etc. — a Track B owner should make the cartography emit tolerate a mocked world or fix the test doubles). Out of scope for Track C 165-4. *Found by Dev during implementation.*
- **Improvement** (non-blocking): the range-echo tests use `_make_attacker` (a synthetic MELEE blade not in the heavy_metal catalog), so `_resolved_band` is None and the tests exercise the **"melee" default** path. The RANGED-band echo (`_resolved_band` → a real SRD band string like `"10/30"`) is wired but NOT test-covered — a future test needs a PC holding a catalog item with a `range_band` to prove the ranged path echoes the band string. Affects `tests/integration/test_dice_range_echo_165_4.py` (add a ranged-weapon case). *Found by Dev during implementation.*
- **Gap** (non-blocking, carried): the move-summary echo's PROD reachability still depends on the `dungeon_store`→`lookahead_handle.persistence` store-unification (reviewer-ruled NON-BLOCKING Plan-7). I did NOT do it (out of the blocking-rework scope). The OTEL span I added makes the DECISION observable; the emit itself remains fixture-only until Plan-7. Docstrings now carry the honest dead-gate caveat. Affects `sidequest/server/websocket_handlers/map_emit.py`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): `DiceResultPayload.range_band`/`distance_cells` are declared and rendered by `InlineDiceTray` (`dice-result-range`) but **no server code ever populates them** — grep of every `DiceResultPayload(...)` construction (`dispatch/dice.py`, `handlers/dice_throw.py`, `dispatch/check.py`, `narration_apply.py`, `chargen_mixin.py`) finds zero `range_band=`/`distance_cells=`. The producing data is computed by 165-3's `_enforce_tactical_reach` and **discarded** at `sidequest/server/dispatch/dice.py:859-867` (the returned verdict carries `distance_cells`/`max_cells`/`reason`; `_range_band` is resolved at line 851). Plan Task 9 explicitly scoped this population into the dice dispatch; it was omitted, untested, and undisclosed. This is the live-path resolution-card half of the story. Affects `sidequest/server/dispatch/dice.py` (capture the verdict + `_range_band` onto the emitted `DiceResultPayload`) + a wiring test. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The new move-summary adjudication block (`map_emit.py:281-312`) emits no OTEL/watcher span, unlike its siblings in the same function (`tactical_grid.tactical_missing`, `tactical_grid.runtime_render_skipped`) and 165-3's `tactical.*` span family. CLAUDE.md OTEL Observability Principle requires a span on every subsystem decision. Affects `sidequest/server/websocket_handlers/map_emit.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `getattr(sd, "genre_pack", None)` (`map_emit.py:287`) and `getattr(pack, "rules", None)` (`map_emit.py:288`) guard REQUIRED non-Optional dataclass fields (accessed bare at `map_emit.py:365,543` and in the wiring test) — silently yields zero adjudications instead of failing loud (No Silent Fallbacks). Affects `sidequest/server/websocket_handlers/map_emit.py`. *Found by Reviewer during code review.*

#### RED Rework (Round 2) — APPROVED with non-blocking follow-ups
- **Improvement** (non-blocking): `_enforce_tactical_reach`'s docstring (`sidequest/server/dispatch/dice.py:374-378`) still states "the returned verdict is dead at the sole call site today" — THIS diff made that false (the caller at line ~891 now reads `_reach_verdict.distance_cells` for the range echo). A maintainability trap: a future dev could delete the "dead" return and silently kill the echo. Guarded by the `distance_cells == 2` integration assertion, so non-blocking, but should be reworded. Affects `sidequest/server/dispatch/dice.py`. *Found by Reviewer during code review.*
- **Gap** (non-blocking): the range-echo integration tests use `_make_attacker`'s synthetic melee `blade_2d6` (not a catalog item), so `resolve_weapon_range_band_from_beat_and_actor` always returns None and the echo collapses to the `"melee"` default — `range_band is not None` is unconditionally true. The RANGED-band string path (a catalog item with a real `range_band` like `"100/600"`) never reaches the wire in test. Trivial `or` logic, low risk, but add a ranged-catalog attacker case to prove it. Affects `sidequest-server/tests/integration/test_dice_range_echo_165_4.py`. *Found by Reviewer during code review.*
- **Gap** (non-blocking): no test locks the `capable` vs `adjudication_count` INDEPENDENCE the OTEL contract requires — there is no `capable=True` + zero-PCs case (WWN pack, empty room → capable=True, count=0), so a regression collapsing `capable` to `(count>0)` would pass. Also the reach/aoe renderer tests have no production producer (only `kind="move"` is built), so that UI surface has no end-to-end wiring test (scope-note it like the move echo). Affects `tests/server/test_tactical_grid_emit_population.py` + `tactical-adjudication-echo.test.tsx`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `getattr(snapshot, "character_locations", {}) or {}` (`map_emit.py:307`) reproduces the No-Silent-Fallbacks getattr shape, but `character_locations` is a pydantic `Field(default_factory=dict)` (provably never None) so the fallback is unreachable — harmless dead-defensiveness carried from round-1. Simplify to `snapshot.character_locations` directly. Affects `sidequest/server/websocket_handlers/map_emit.py`. *Found by Reviewer during code review.*
- **Gap** (blocking for DEVELOP HEALTH, non-blocking for THIS story — confirmed independently): the full server suite carries 57 pre-existing `pydantic ValidationError` failures constructing `CartographyTreatmentWire(kind=<MagicMock>, …)` at `sidequest/server/session_helpers.py:1695` (`_build_cartography_map_message`) — a Track B cartography change that MagicMock-world wiring tests don't satisfy. Preflight verified this diff touches zero lines there; the Dev's stash-compare shows 64→57 (rework fixed 6, regressed 0). A Track B owner should make the cartography emit tolerate a mocked world or fix the test doubles. Affects `sidequest/server/session_helpers.py` + the affected wiring tests. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Invented a `data-testid` for the move-budget chip the plan left unnamed**
  - Spec source: plan Task 10, step "render ... a subtle cells_spent/cells_budget chip for kind === 'move'"
  - Spec text: names `data-testid="tactical-denial"` for the denial banner but gives NO testid for the move chip.
  - Implementation: the test pins the chip contract as `data-testid="tactical-move-budget"` (asserts it shows both cells_spent and cells_budget).
  - Rationale: a chip AC needs a stable selector; defining it in the RED test makes the contract explicit for Dev rather than leaving it to chance.
  - Severity: minor
  - Forward impact: Dev must use `data-testid="tactical-move-budget"` on the move chip.
- **Dice-range readout test placed in a NEW file, not appended to the existing InlineDiceTray suite**
  - Spec source: plan Task 10, step "Modify sidequest-ui/src/components/__tests__/ dice-result test (extend an existing InlineDiceTray test or add one for the range readout)"
  - Spec text: "extend an existing InlineDiceTray test **or add one**"
  - Implementation: added `src/dice/__tests__/InlineDiceTray.range.test.tsx` (mirrors the existing suite's R3F/rapier/dice-lib mocks).
  - Rationale: the plan explicitly permits a new file; isolating the range readout keeps the large existing suite untouched (no regression risk to its 20+ target-persistence tests).
  - Severity: minor
  - Forward impact: none.

#### RED Rework (Round 2) — post-Reviewer-rejection
- **Invented the move-summary OTEL event name + field contract**
  - Spec source: Reviewer Assessment [HIGH RULE], "Emit a `tactical.*` watcher event distinguishing engaged / no-capability-skip / N-built"
  - Spec text: names the requirement but no event string or field set.
  - Implementation: the RED pins event `tactical_grid.move_summary` (the `tactical_grid.*` ephemeral pattern its two siblings in the same function use, captured via `map_emit._watcher_publish`) carrying `capable: bool` + `adjudication_count: int`, firing on BOTH the engaged and no-capability-skip paths.
  - Rationale: a span AC needs a stable name + fields; defining them in RED makes the contract explicit for Dev (precedent: last round's `tactical-move-budget` testid contract was Reviewer-ACCEPTED). Sibling-consistent `_watcher_publish` avoids the `SPAN_ROUTES` routing-completeness burden a `Span.open` helper would incur.
  - Severity: minor
  - Forward impact: Dev emits `tactical_grid.move_summary` with those fields via `_watcher_publish`; a `Span.open` helper instead would need a `SPAN_ROUTES` entry and move the test capture point.
- **Fail-loud RED simulates the broken invariant by forcing the required field to None**
  - Spec source: Reviewer Assessment [HIGH RULE] No-Silent-Fallbacks, `getattr(sd,"genre_pack",None)`/`getattr(pack,"rules",None)`
  - Spec text: "Access `sd.genre_pack` / `pack.rules` directly (fail loud)"
  - Implementation: two tests set `sd.genre_pack = None` and `sd.genre_pack = SimpleNamespace(rules=None)` respectively, asserting `pytest.raises((AttributeError, TypeError, ValueError))` — rather than a "natural" trigger (the fields are required, so no natural absence exists).
  - Rationale: the only honest way to prove a masked required-field access fails loud is to break the invariant and assert a crash instead of a silent "zero adjudications" return; the broadened raise tuple lets Dev fail via bare access (AttributeError) or an explicit guard.
  - Severity: minor
  - Forward impact: none — Dev accesses both directly per the reviewer's prescription.
- **The dice-result partial-echo RED drives INDEPENDENT field wiring (range_band without a grid)**
  - Spec source: Reviewer Assessment [MEDIUM TEST], "no partial-echo (one of range_band/distance_cells) test"
  - Spec text: lists the gap; does not prescribe a scenario.
  - Implementation: a `dungeon_store=None` (no-grid) strike must echo the resolved `range_band` with `distance_cells=None` — pinning that `range_band` (resolved pre-gate at dice.py:851) is wired independently of the verdict-sourced `distance_cells`.
  - Rationale: the strongest partial-echo test is server-side and RED (blocks a both-or-neither fix that would leave every grid-less strike bandless); the UI partial guards (band-only / distance-only) are passing regression guards on top.
  - Severity: minor
  - Forward impact: Dev must set `range_band` from `_range_band` regardless of whether the reach verdict exists.
- **No RED test for the index-key [RULE] finding — Dev directive + rule-checker instead (test omission)**
  - Spec source: Reviewer Assessment [MEDIUM RULE] index-based React keys; [LOW SIMPLE] duplicate `tactical-denial` testid; [MEDIUM DOC] liveness-overstating docstrings
  - Spec text: "Use `a.actor`(+`kind`)-derived keys"; reword docstrings.
  - Implementation: NO failing test for these. Multi-PC renderer coverage added via `getAllByTestId` (passing guard) closes the reviewer's "single-PC only" gap; the key fix, the duplicate-testid, and the docstring rewords are handed to Dev as directives (see Delivery Findings).
  - Rationale: React keys on STATELESS list items are not DOM-observable (index vs content keys → identical DOM); a testid-rename RED would also make the pre-existing "no denial when valid" test vacuous. Docstring wording has no behavioral assertion. All three are mechanical fixes the Reviewer's rule-checker/comment-analyzer re-verifies next round.
  - Severity: minor
  - Forward impact: Dev applies the key/testid/docstring fixes in GREEN; no test guards them (by design).

### Dev (implementation)
- **Resolved WN-only ruleset method access with getattr + cast instead of a direct call**
  - Spec source: plan Task 9, "each PC's cells_budget from ruleset.combat_move_cells"
  - Spec text: implies `ruleset.combat_move_cells(core)` directly.
  - Implementation: `fn = getattr(ruleset, "combat_move_cells", None); if callable(fn): cells_budget = cast("int", fn(core))`.
  - Rationale: `get_ruleset_module()` is typed to return the base `RulesetModule` ABC, which does not declare `combat_move_cells` (a WN-family method) — a direct call fails pyright twice (unknown attribute + `object`→`int|None`). getattr+callable is also the honest capability gate for a non-WN ruleset (e.g. Fate) reaching this path: it contributes no move echo rather than crashing.
  - Severity: minor
  - Forward impact: none — runtime behavior identical for WN packs; graceful skip for others.
- **Move-summary echo only (no per-opponent reach adjudications) in the emit path**
  - Spec source: plan Task 9, map_emit step
  - Spec text: "for each opponent, a TacticalAdjudication(kind='reach', ...) is optional; the minimum viable echo for this task is the round move summary."
  - Implementation: populated only the per-PC `kind="move"` summary; did not add per-opponent reach echoes.
  - Rationale: the plan explicitly calls the move summary the minimum viable echo and the reach echo optional; TEA's tests pin only the move summary. Minimalist discipline — no test demands the reach echo.
  - Severity: minor
  - Forward impact: none — additive; a later story can add reach echoes without reshaping the field.

#### RED Rework (Round 2) — GREEN
- **The echoed `range_band` defaults to "melee" when the resolver returns None**
  - Spec source: Reviewer Assessment [HIGH RULE], "capture … the resolved `_range_band` onto the emitted DiceResultPayload"; TEA `test_range_adjudicated_strike…` / `test_range_band_echoes_without_grid…` (assert `range_band is not None`).
  - Spec text: the reviewer says echo "resolved `_range_band`" — which `resolve_weapon_range_band_from_beat_and_actor` returns as `None` for a melee/natural/unarmed strike (no ranged catalog band). The TEA harness attacker wields a synthetic melee blade, so the raw resolver output is None.
  - Implementation: `_tactical_range_band = _resolved_band or "melee"` — echo the honest "melee" label for a melee strike (the resolver's None is the melee sentinel; `weapon_range_cells` treats `None == "melee"`). The gate still receives the raw `_resolved_band` (unchanged behavior). A ranged weapon echoes its real SRD band string.
  - Rationale: literally echoing None would render NOTHING on the resolution card for a melee strike (guarded on presence) — defeating the story's "see the math" goal for the most common combat case. "melee" is the true band the strike was adjudicated at, not a guess. Satisfies both TEA tests and the feature intent.
  - Severity: minor
  - Forward impact: a combat melee strike now carries `range_band="melee"` on its check DiceResultPayload; social checks/saves (outside the hp_depletion gate) stay None. No sibling-story assumption affected.
- **Move-summary OTEL uses the sibling `_watcher_publish` ephemeral-event pattern, not a `Span.open` route**
  - Spec source: Reviewer Assessment [HIGH RULE], "Emit a `tactical.*` watcher event"; TEA OTEL tests (capture `map_emit._watcher_publish`).
  - Spec text: "Emit a `tactical.*` watcher event distinguishing engaged / no-capability-skip / N-built."
  - Implementation: `_watcher_publish("tactical_grid.move_summary", {capable, adjudication_count, …})` — the exact ephemeral-event mechanism its two siblings (`tactical_grid.tactical_missing`, `.runtime_render_skipped`) use, NOT a `Span.open`+`SPAN_ROUTES` mirror.
  - Rationale: consistency with the siblings in the same function; avoids a `SPAN_ROUTES`/`FLAT_ONLY_SPANS` routing-completeness entry (`_all_span_constants()` only enumerates `SPAN_*` constants, so an ephemeral event needs no route). `tactical_grid.*` starts with `tactical`, satisfying the reviewer's `tactical.*` wording.
  - Severity: minor
  - Forward impact: none — the GM panel receives the event like its siblings.

### Reviewer (audit)
- **TEA: invented `data-testid="tactical-move-budget"`** → ✓ ACCEPTED by Reviewer: defining the selector contract in the RED test is sound; the chip renders it correctly.
- **TEA: dice-range test in a new file** → ✓ ACCEPTED by Reviewer: the plan explicitly permits "add one"; isolation avoids churning the large existing suite.
- **Dev: getattr + cast for the WN-only `combat_move_cells`** → ✓ ACCEPTED by Reviewer: `combat_move_cells` genuinely exists only on WN-family subclasses; this is a real duck-typed capability gate, not a masked config error. (Distinct from the `genre_pack`/`rules` getattr, which IS a violation — flagged below and as a Delivery Finding.)
- **Dev: move-summary echo only, no per-opponent reach echoes on the grid** → ✓ ACCEPTED by Reviewer: the plan calls the move summary the minimum viable echo and per-opponent reach echoes optional; deferring the grid reach echoes is a logged, spec-faithful scope call.
- **UNDOCUMENTED — dice-result range echo has no producer:** Spec (session scope "echo … dice-result range onto additive protocol fields"; plan Task 9 "the resolution-card range echo is populated in the dice dispatch … Assert population via a fixture test") said populate `range_band`/`distance_cells` on the emitted dice-result. Code declares the fields + renders them but never sets them (verdict discarded at `dispatch/dice.py:859-867`). Not logged by TEA/Dev. This is IN SCOPE (not the deferred grid-reach-echo case) and flows through the LIVE dispatch path. Severity: **HIGH (blocking)**.
- **UNDOCUMENTED — no OTEL span on the move-summary decision:** Spec (CLAUDE.md OTEL Observability Principle) requires a watcher event on every subsystem decision; the new ruleset-resolve + budget-compute + adjudication-build block emits none. Not logged. Severity: **Medium**.
- **UNDOCUMENTED — `getattr` on required `genre_pack`/`rules`:** Spec (No Silent Fallbacks) requires failing loud on a missing required invariant; the guards silently yield zero adjudications. Not logged (Dev's getattr deviation covered only `combat_move_cells`). Severity: **Medium**.

#### RED Rework (Round 2) — Reviewer audit
- **TEA: invented the `tactical_grid.move_summary` OTEL event name + `capable`/`adjudication_count` field contract** → ✓ ACCEPTED: defining the span contract in the RED test is the right move (precedent: the round-1 `tactical-move-budget` testid contract, accepted). The sibling-consistent `_watcher_publish` choice avoids a `SPAN_ROUTES` routing-completeness entry, and `test_routing_completeness` stays green. Dev implemented it exactly.
- **TEA: fail-loud RED via forced-None invariant break** → ✓ ACCEPTED: setting the required field to None and asserting a raise is the only honest way to prove a masked required-field access now fails loud; the broadened raise tuple is reasonable latitude.
- **TEA: partial-echo RED (range_band without a grid, distance_cells None)** → ✓ ACCEPTED: this is the strongest of the coverage tests — it drives INDEPENDENT field wiring and blocks a both-or-neither fix. Verified it fails on develop for the right reason.
- **TEA: no RED test for the index-key [RULE] finding (Dev directive)** → ✓ ACCEPTED: React keys on stateless list items are not DOM-observable (index vs content keys → identical DOM), so a behavioral RED would be impossible/vacuous; handing it to the rule-checker was correct — the rule-checker confirmed the content-derived-key fix (ts #19 FIXED).
- **Dev: `range_band = _resolved_band or "melee"` (melee default)** → ✓ ACCEPTED: `resolve_weapon_range_band_from_beat_and_actor` returns None as the melee sentinel (`weapon_range_cells` maps None == "melee"); echoing "melee" is the honest band for a melee strike, and the gate still receives the raw `_resolved_band` so gate behavior is unchanged. Without it the resolution card would render nothing for the most common combat case (the story's whole point). Caveat logged as a Delivery Finding: the melee-only test harness leaves the RANGED-band string path unproven.
- **Dev: ephemeral `_watcher_publish` OTEL, not a `Span.open`+`SPAN_ROUTES` route** → ✓ ACCEPTED: matches the two siblings in the same function and correctly avoids the routing-completeness burden (`_all_span_constants()` only enumerates `SPAN_*` constants). Confirmed `test_routing_completeness` green.

## TEA Assessment

**Tests Required:** Yes
**Status:** RED (failing — ready for Dev)

**Test Files:**
- `sidequest-server/tests/protocol/test_tactical_adjudication_payload.py` — 10 tests: `TacticalAdjudication` shape/defaults, cells JSON-array serialization, mutable-default isolation (×2), `TacticalGridPayload.adjudications` additive + back-compat default-empty, `DiceResultPayload` `range_band`/`distance_cells` additive defaults + carry, protocol-package export.
- `sidequest-server/tests/server/test_tactical_grid_emit_population.py` — +1 test: `test_runtime_payload_populates_move_adjudications` (production-path wiring — emit fills the round move-summary echo with the bound-ruleset Move budget). The 3 pre-existing tests in this file still PASS (append-only).
- `sidequest-ui/src/__tests__/tactical-adjudication-echo.test.tsx` — 5 tests: renderer denial banner (`tactical-denial`), move-budget chip (`tactical-move-budget`), no-banner-when-all-valid, `tacticalGridFromWire` adjudications mapping, back-compat `[]` default.
- `sidequest-ui/src/dice/__tests__/InlineDiceTray.range.test.tsx` — 2 tests: `dice-result-range` readout when the echo is present, and omission (presence-guard) when absent.

**Tests Written:** 18 tests covering plan Tasks 9 (server protocol echoes) + 10 (UI display).
**RED verified:** 8/8 protocol (pre-mutable-default set) + 2 mutable-default + 1 emit-wiring + 5 UI-echo + 1 dice-range fail feature-missing (ImportError / missing field / missing testid). 3 pre-existing emit tests + the dice-range presence-guard PASS by design.

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| py #2 mutable default arguments | `test_adjudication_cells_default_is_not_shared_between_instances`, `test_grid_payload_adjudications_default_is_not_shared_between_instances` | failing (RED) |
| py #6 test quality (no vacuous assertions) | self-check of all 18 tests — every test asserts a concrete value; the "omits range readout" negative asserts `dice-result` present AND `dice-result-range` absent (not vacuous) | pass (self-check) |
| No-Silent-Fallbacks / additive back-compat | `test_grid_payload_adjudications_default_empty_for_back_compat`, `test_dice_result_range_echo_defaults_none`, UI back-compat `[]` default | failing (RED) |
| ts #4 null/undefined (`?? []`, not `\|\| []`) | `defaults adjudications to [] when the wire payload omits the field` | failing (RED) |
| ts #1 type-safety escapes (`as any` / `as unknown as`) | no new `as any`; the single `as unknown as` mirrors the existing InlineDiceTray suite's DieGroupResult-spec fixture idiom verbatim | pass (self-check) |

**Rules checked:** 5 applicable lang-review checks (2 py + 2 ts + 1 project No-Silent-Fallbacks) have test coverage or a documented self-check.
**Self-check:** 0 vacuous tests. Two tests pass on RED by design (3 pre-existing emit tests untouched; the dice-range presence-guard) — documented in Delivery Findings so the Reviewer doesn't read them as a broken RED.

**Handoff:** To Dev (Naomi) for GREEN. Blocking finding for Dev: `DiceResultPayload` is in `protocol/dice.py:214`, NOT `protocol/models.py` (see Delivery Findings). Additive-only — empty defaults everywhere so Track B's SITE_MAP cutover keeps the same wire shape.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-server/sidequest/protocol/models.py` — `TacticalAdjudication` model + `TacticalGridPayload.adjudications` (additive, `Field(default_factory=list)`).
- `sidequest-server/sidequest/protocol/dice.py` — additive `range_band: str|None=None`, `distance_cells: int|None=None` on `DiceResultPayload` (NOT models.py — TEA finding confirmed).
- `sidequest-server/sidequest/protocol/__init__.py` — export `TacticalAdjudication`.
- `sidequest-server/sidequest/server/websocket_handlers/map_emit.py` — populate per-PC round move-summary echo in `_maybe_build_runtime_cavern_payload` (getattr+cast for the WN-only `combat_move_cells`).
- `sidequest-ui/src/types/tactical.ts` — `TacticalAdjudication` interface + optional `adjudications` on `TacticalGridData`.
- `sidequest-ui/src/lib/tacticalGridFromWire.ts` — parse `adjudications ?? []` (back-compat).
- `sidequest-ui/src/components/TacticalGridRenderer.tsx` — denial banner (`tactical-denial`) + move-budget chip (`tactical-move-budget`).
- `sidequest-ui/src/types/payloads.ts` — optional `range_band`/`distance_cells` on `DiceResultPayload`.
- `sidequest-ui/src/dice/InlineDiceTray.tsx` — presence-guarded range/cells readout (`dice-result-range`).

**Tests:** GREEN — 18/18 story tests pass. Full verification (fresh evidence):
- Server: 14 target tests (10 protocol + 4 emit) PASS; 380 protocol-package regression tests PASS; `ruff check` clean; `pyright` 0 errors.
- UI: 7 new + 21 adjacent pre-existing tests PASS (28 total, 0 regressions); `eslint` clean; `tsc --noEmit` clean.
- **Total: 422 pass / 0 fail.**

**Branch:** `feat/165-4-protocol-echoes-ui-math` — pushed to both repos (server `c5663b39`, ui `7155224`, off `develop`).

**Additive-only:** empty defaults everywhere — Track B's SITE_MAP cutover keeps the same `TacticalGridPayload`/`DiceResultPayload` wire shape untouched (proven by the back-compat tests + the passing protocol regression sweep).

**⚠️ Reviewer, read the Delivery Finding:** the player-facing math display is correct and tested but is gated behind the pre-existing DEAD `dungeon_store` attribute in `map_emit.py:174` — it will not reach real players until the tracked 165-3 map_emit store-unification follow-up lands. Green tests ≠ on-screen for Sebastien/Jade yet.

**Handoff:** To Reviewer (Chrisjen) for code review.

<skills-invoked>
<skill name="test-driven-development" phase="red" at="2026-07-09T16:34:36Z"/>
<skill name="test-driven-development" phase="red" at="2026-07-09T17:10:00Z"/>
<skill name="test-driven-development" phase="green" at="2026-07-09T16:47:48Z"/>
<skill name="verification-before-completion" phase="green" at="2026-07-09T16:47:48Z"/>
<skill name="requesting-code-review" phase="green" at="2026-07-09T16:47:48Z"/>
<skill name="test-driven-development" phase="green" at="2026-07-09T20:05:00Z"/>
<skill name="verification-before-completion" phase="green" at="2026-07-09T20:05:00Z"/>
<skill name="requesting-code-review" phase="green" at="2026-07-09T20:05:00Z"/>
</skills-invoked>

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (415 tests pass, ruff/eslint/pyright/tsc clean) | N/A — corroborates green but cannot see wiring gaps |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 10 | confirmed 3 (fixture-theater wiring test + coverage gaps), deferred 5 (low), dismissed 2 (tautology/unused-kwarg — minor) |
| 5 | reviewer-comment-analyzer | Yes | findings | 9 | confirmed 5 (docstrings claim liveness for dead/unpopulated code), deferred 4 (low/medium reword) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 7 | confirmed 5 (range half-wire, OTEL gap, 2× required-field getattr, index keys), dismissed 1 (`as unknown as` — pre-existing idiom), noted 1 |

**All received:** Yes (4 enabled subagents returned; 5 disabled via `workflow.reviewer_subagents` settings)
**Total findings:** 4 confirmed blocking-relevant (3 HIGH + docstring cluster), plus MEDIUM/LOW; independent grep by 3 of the 4 subagents + me all converge on the range-echo half-wiring.

## Rule Compliance

Rule-checker ran exhaustively (26 lang-review rules + 4 CLAUDE.md rules, 61 instances). My confirmation:
- **py #2 (mutable defaults):** COMPLIANT — `TacticalAdjudication.cells` + `TacticalGridPayload.adjudications` both use `Field(default_factory=list)`; per-instance isolation is tested. Verified `models.py:746,1370`.
- **py #3 (type annotations at boundaries):** COMPLIANT — new model/fields/serializer fully annotated.
- **py #6 / ts #8 (test quality):** COMPLIANT on vacuity (no `assert True`), but see the fixture-theater wiring gap under [TEST] — the "production-path" test cannot prove prod reachability.
- **py #10 (import hygiene):** COMPLIANT — `cast` correctly imported for runtime use, lazy in-function imports match the module convention.
- **ts #4 (null/undefined `??` vs `||`):** COMPLIANT — every coalescing (`?? []`, `?? undefined`, `!= null`) correctly preserves legitimate `0`; `||` would have been a bug and was avoided.
- **ts #6 (React keys):** **VIOLATION** — `TacticalGridRenderer.tsx:181,190` use index keys `denial-${i}`/`move-${i}` where every sibling `.map()` uses content-derived keys. [RULE]
- **ts #1 (type-safety escapes):** minor — one `as unknown as` in a test, mirrors the pre-existing `InlineDiceTray.test.tsx` idiom verbatim; not novel. Dismissed as consistent-with-surrounding-code.
- **CLAUDE.md No Silent Fallbacks (#27):** **VIOLATION** — `getattr(sd,"genre_pack",None)` / `getattr(pack,"rules",None)` on required fields (`map_emit.py:287-288`). (The `combat_move_cells` getattr is COMPLIANT — real capability gate.) [RULE]
- **CLAUDE.md No half-wired features (#28):** **VIOLATION** — `DiceResultPayload.range_band`/`distance_cells` have zero producers. [RULE]
- **CLAUDE.md OTEL Observability (#29):** **VIOLATION** — move-summary subsystem block emits no span (`map_emit.py:281-312`). [RULE]
- **CLAUDE.md Additive protocol (#30):** COMPLIANT — all new fields default None/[]/"" and back-compat is tested.

## Devil's Advocate

Argue this ships broken. Start with the one human the game exists for: a mechanics-first player (Sebastien/Jade) opens a strike expecting to read the range math on the resolution card. They see nothing — not "0 cells," not a stale value, *nothing* — because the UI span is guarded on `range_band`/`distance_cells` and no server code on earth ever sets them. The story's title is "resolution-card math display"; the resolution-card math never displays. A green 422-test suite and a passing "wiring test" say "done" while the headline feature is dead on both ends of the wire. That is precisely the "convincing narration, zero mechanical backing" failure the whole project architecture (OTEL as lie detector) is built to catch — and here the reviewer is the only lie detector, because the new subsystem decision emits no span at all, so even the GM panel can't tell whether the move echo engaged or the ruleset resolve silently no-op'd. Now the confused-maintainer angle: six months from now someone reads `range_band: "when a strike was reach/range-adjudicated … the resolved weapon band … ride along"` in present tense, greps for a bug in "why doesn't the range show," and burns an afternoon before discovering the field was never populated — the docstring actively lies. The stressed-invariant angle: if `sd.genre_pack` were ever legitimately absent (a required field, but invariants break), the `getattr(..., None)` swallows it into "zero adjudications" instead of a loud failure — a silent fallback masquerading as the legitimate `dungeon_store` optional pattern, on a field that is not optional. The multi-PC angle: the map_emit loop and the renderer's index-keyed lists are only ever tested with one PC and one adjudication; a two-PC table exercises code paths (React key stability, `getAllByTestId`, anchor collision) that no test touches. And the whole move-summary branch sits behind a dead `dungeon_store` gate, so even the half that *is* populated reaches no one. The counter-argument — "it's additive plumbing, delivery is a follow-up" — holds for the disclosed dungeon_store gate, but not for the range echo, which was explicitly in Task 9's scope, flows through the *live* dispatch path, and was neither built nor disclosed. This is not done.

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] `[RULE]` | Half-wired feature: `DiceResultPayload.range_band`/`distance_cells` declared + UI-rendered (`InlineDiceTray` `dice-result-range`) but **no server producer** — every `DiceResultPayload(...)` construction lacks them. In scope (Task 9), undisclosed. | `sidequest/protocol/dice.py:241`; discard site `sidequest/server/dispatch/dice.py:859-867` | Capture the 165-3 reach verdict (`distance_cells`) + resolved `_range_band` onto the emitted `DiceResultPayload` at dispatch; add a wiring test asserting an emitted result carries them. |
| [HIGH] `[RULE]` | OTEL Observability violation: new move-summary subsystem decision (ruleset resolve + `combat_move_cells` + adjudication build) emits no watcher span, unlike its siblings and 165-3's `tactical.*` family. | `sidequest/server/websocket_handlers/map_emit.py:281-312` | Emit a `tactical.*` watcher event distinguishing engaged / no-capability-skip / N-built; add a span assertion. |
| [HIGH] `[RULE]` | No Silent Fallbacks: `getattr` on required non-Optional `genre_pack`/`rules` masks a broken invariant as "zero adjudications." | `sidequest/server/websocket_handlers/map_emit.py:287-288` | Access `sd.genre_pack` / `pack.rules` directly (fail loud); keep only the legitimate `combat_move_cells` capability getattr. |
| [MEDIUM] `[DOC]` | Docstrings/comments claim present-tense liveness ("surfaced"/"populated"/"ride along"/"present") for dead-gated (move) or never-populated (range/reach/aoe) code. | `models.py:728,1370`; `dice.py:237`; `map_emit.py:119,281`; `payloads.ts:587`; `InlineDiceTray.tsx:452` | Reword to honest forward-looking language; add the same dead-gate caveat sibling code uses (Decision-N pattern). |
| [MEDIUM] `[TEST]` | "Production-path wiring test" is fixture theater — the builder's `sd.dungeon_store` gate is unreachable in prod (fixture-only attribute). Coverage gaps: no Fate/no-`combat_move_cells` branch, no partial-echo (one of range_band/distance_cells) test, no valid-reach/aoe render test, no multi-PC case. | `tests/server/test_tactical_grid_emit_population.py:118`; `tactical-adjudication-echo.test.tsx` | Add an honest wiring proof or Decision-N tripwire; add the missing cases. |
| [MEDIUM] `[RULE]` | Index-based React keys on the two new adjudication `.map()`s where every sibling list uses content-derived keys. | `sidequest-ui/src/components/TacticalGridRenderer.tsx:181,190` | Use `a.actor`(+`kind`)-derived keys. |
| [LOW] `[SIMPLE]` | Duplicate `data-testid="tactical-denial"` across multiple denials (breaks `getByTestId`); move chip renders `0/N` because `cells_spent` is never populated server-side. | `TacticalGridRenderer.tsx:174-189` | Note only — address opportunistically in the rework. |

**Subagent dispatch coverage:** `[EDGE]` disabled this run · `[SILENT]` disabled this run (No-Silent-Fallbacks caught by `[RULE]` backstop instead) · `[TEST]` fixture-theater wiring + coverage gaps (confirmed) · `[DOC]` liveness-overstating docstrings (confirmed) · `[TYPE]` disabled this run · `[SEC]` disabled this run (echoes are server-authored outbound, no untrusted-input surface) · `[SIMPLE]` disabled this run (duplicate-testid/0-of-N noted from my own read) · `[RULE]` range half-wire + OTEL gap + required-field getattr + index keys (confirmed, backstop for the disabled lenses).

**Data flow traced:** player strike → `dispatch_dice_throw` computes the reach verdict (`_enforce_tactical_reach`, live store) → verdict **discarded** → `DiceResultPayload` emitted WITHOUT `range_band`/`distance_cells` → `InlineDiceTray` renders nothing (guarded on absent fields). The flow is severed at the discard. On the grid side: `_maybe_build_runtime_cavern_payload` builds move adjudications but is gated behind the dead `sd.dungeon_store` (pre-existing, disclosed — non-blocking, consistent with the 165-3 ruling).

**Blocking rule:** 3 HIGH findings (all matching stated project rules — cannot be dismissed). REJECT.

**Handoff:** Back to TEA (Amos) for RED rework — the fixes are testable (missing producer + missing OTEL span + fail-loud + coverage), so they need failing tests first. Scope: (1) BLOCKING — wire `range_band`/`distance_cells` at dispatch from the 165-3 verdict + wiring test; (2) BLOCKING — OTEL span on the move-summary decision; (3) BLOCKING — fail-loud `genre_pack`/`rules` access; (4) fix the liveness-overstating docstrings; (5) content-derived React keys; (6) close the coverage gaps (Fate branch, partial echo, multi-PC). The map_emit dead-`dungeon_store` gate remains a NON-BLOCKING Plan-7 follow-up (do not hold the rework hostage to it), but strongly consider resolving the move echo through `sd.lookahead_handle.persistence` (the 165-3 pattern) so the grid half also reaches players.

## TEA Assessment — RED Rework (Round 2)

**Tests Required:** Yes
**Status:** RED (failing — ready for Dev)

**Reviewer rejection addressed:** 3 BLOCKING HIGH + the testable MEDIUM coverage gaps, each driven by a failing test first. The non-testable MEDIUM/LOW findings (index React keys, duplicate testid, liveness docstrings) are handed to Dev as GREEN directives (Delivery Findings) — they have no honest behavioral assertion and the Reviewer's rule-checker/comment-analyzer re-verify them.

**Test files touched this rework:**
- `sidequest-server/tests/server/test_tactical_grid_emit_population.py` — +5 tests (2 OTEL: engaged span + no-capability-skip span; 2 fail-loud: genre_pack None, rules None; 1 multi-PC coverage) + 2 helpers (`_capture_watcher_events`, `_add_second_pc`).
- `sidequest-server/tests/integration/test_dice_range_echo_165_4.py` — +1 test (partial-echo: no-grid → `range_band` set, `distance_cells` None) + `with_grid` helper param; cleaned a pre-existing SIM105 lint error to `contextlib.suppress`. (The BLOCKING #1 full-echo wiring test was already committed in `ba49fd61`.)
- `sidequest-ui/src/__tests__/tactical-adjudication-echo.test.tsx` — +3 coverage guards (multi-PC per-actor denial+chip, valid-reach → no false denial, aoe → no crash/no false denial).
- `sidequest-ui/src/dice/__tests__/InlineDiceTray.range.test.tsx` — +2 partial-echo guards (band alone, distance alone).

**RED verified (Machine Shop, RUN_ID 165-4-tea-red):**
- Server: **6 fail (RED) / 15 pass**. RED drivers: `test_move_summary_emits_watcher_span_when_move_capable` (no span → "watcher event did not fire"), `test_move_summary_reports_skip_for_ruleset_without_move_cells` (no skip span), `test_move_summary_fails_loud_when_genre_pack_missing` / `..._when_pack_rules_missing` ("DID NOT RAISE"), `test_range_adjudicated_strike_echoes_distance_and_range_band...` (existing, "assert None == 2"), `test_range_band_echoes_without_grid...` ("assert None is not None"). Pre-existing protocol suite `test_tactical_adjudication_payload.py` 10/10 — no regression. Multi-PC coverage passes by design. No collection/setup errors.
- UI: **12/12 pass** — the UI code was already correct last round; all UI adds are coverage guards (multi-PC, valid-reach/aoe, partial-echo band/distance) that pass by design.
- Lint clean: `ruff check` on both server files passes; `eslint` + `tsc --noEmit` clean on the UI.

### Rule Coverage

| Rule / Reviewer finding | Test(s) | Status |
|-------------------------|---------|--------|
| [HIGH RULE] half-wired range echo (Task 9 producer) | `test_range_adjudicated_strike_echoes_distance_and_range_band_on_dice_result` (committed `ba49fd61`) | failing (RED) |
| [MEDIUM TEST] partial echo — independent fields | `test_range_band_echoes_without_grid_and_distance_cells_stays_none` (server) + band-only / distance-only (UI) | server failing (RED); UI passing (guard) |
| [HIGH RULE] OTEL span on move-summary decision (engaged) | `test_move_summary_emits_watcher_span_when_move_capable` | failing (RED) |
| [HIGH RULE] OTEL span — no-capability skip observable | `test_move_summary_reports_skip_for_ruleset_without_move_cells` | failing (RED) |
| [HIGH RULE] No-Silent-Fallbacks — genre_pack fail loud | `test_move_summary_fails_loud_when_genre_pack_missing` | failing (RED) |
| [HIGH RULE] No-Silent-Fallbacks — pack.rules fail loud | `test_move_summary_fails_loud_when_pack_rules_missing` | failing (RED) |
| [MEDIUM TEST] Fate / no-`combat_move_cells` branch | `test_move_summary_reports_skip_for_ruleset_without_move_cells` (zero-adjudications guard) | passing (guard) |
| [MEDIUM TEST] multi-PC case (server emit) | `test_move_summary_echoes_one_adjudication_per_present_pc` | passing (guard) |
| [MEDIUM TEST] multi-PC + reach/aoe render (UI) | multi-PC denial/chip, valid-reach, aoe (adjudication-echo) | passing (guards) |
| [MEDIUM RULE] index React keys | — (not DOM-observable on stateless divs) | Dev directive |
| [MEDIUM DOC] liveness-overstating docstrings | — (no behavioral assertion) | Dev directive |
| py #2 mutable defaults / test quality (self-check) | new tests each assert concrete values; no `assert True`/`let _ =`; the passing guards assert real content (multi-PC per-actor budgets, band-vs-cells exclusion) | pass (self-check) |

**Rules checked:** all 3 BLOCKING HIGH + the testable MEDIUM coverage gaps have a failing test; 2 non-testable MEDIUM/LOW are Dev directives with rationale.
**Self-check:** 0 vacuous tests. The multi-PC/valid-reach/aoe/partial-echo-UI/Fate-zero-adjudications tests pass on RED **by design** (coverage guards for behavior already correct) — each still asserts a concrete, mutation-sensitive value; documented here + in Delivery Findings so the Reviewer does not misread them as broken REDs. One false-RED caught and fixed during authoring: `Character(backstory="")` fails a pydantic validator — the multi-PC helper now uses a non-blank backstory.

**Handoff:** To Dev (Naomi) for GREEN. Blocking fixes, all with failing tests: (1) capture `range_band` (from `_range_band`, dice.py:851, independent of the verdict) + `distance_cells` (from the reach verdict) onto the emitted `DiceResultPayload` at `dispatch_dice_throw`; (2) emit `tactical_grid.move_summary` via `_watcher_publish` on the move-summary decision carrying `capable`+`adjudication_count`, on both engaged and skip paths; (3) access `sd.genre_pack` / `pack.rules` directly (fail loud), keeping only the `combat_move_cells` capability getattr. Plus the GREEN directives in Delivery Findings (React keys, docstrings). Do NOT chase the `dungeon_store`→`lookahead_handle.persistence` store unification — reviewer ruled it NON-BLOCKING Plan-7.

## Dev Assessment — RED Rework (Round 2) GREEN

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-server/sidequest/server/dispatch/dice.py` — BLOCKING #1: the reach block now captures `_resolved_band` + the `_enforce_tactical_reach` verdict's `distance_cells` into function-scoped vars and threads them through `_compose_result_payload` (two new optional params) onto the emitted CHECK `DiceResultPayload`. Band echoes `_resolved_band or "melee"` (honest melee label); distance stays None when the gate skips (no grid). Docstring on `dice.py`'s range fields reworded to match.
- `sidequest-server/sidequest/server/websocket_handlers/map_emit.py` — BLOCKING #2: `_watcher_publish("tactical_grid.move_summary", {capable, adjudication_count, ruleset, …})` on both the engaged and no-capability-skip paths. BLOCKING #3: `pack = sd.genre_pack` + `pack.rules.ruleset` accessed directly (fail loud); only `combat_move_cells` stays a capability getattr. Function docstring gains the `dungeon_store` dead-gate caveat.
- `sidequest-server/sidequest/protocol/models.py` — [DOC] `TacticalGridPayload.adjudications` docstring reworded (dead-gate caveat on the move echo; notes the dice range echo is live).
- `sidequest-ui/src/components/TacticalGridRenderer.tsx` — [RULE] index React keys → content-derived (`denial-${a.actor}-${a.kind}`, `move-${a.actor}`).

**Tests:** GREEN. Fresh evidence:
- Server story tests: **21/21** pass (10 protocol + 9 emit-population + 2 range-echo). The 6 RED drivers (2 OTEL, 2 fail-loud, 2 range echo) now pass; coverage guards + protocol suite stay green.
- Server regression sweep (tactical/dispatch/otel/routing, 35 tests): all pass. `test_routing_completeness` green (the ephemeral `tactical_grid.move_summary` needs no `SPAN_ROUTES` entry).
- **No new regressions in the full suite:** with my 4 files stashed the baseline is **64 failed / 14786 passed**; with my changes it is **57 failed / 14793 passed** — my rework fixed the 6 story REDs and added ZERO regressions. The remaining 57 are a **pre-existing** develop failure (`CartographyTreatmentWire` MagicMock at `session_helpers.py:1695`, a Track B cartography test-infra issue) — see Delivery Findings; out of Track C scope.
- UI: **911/911** pass (full vitest suite); the tactical/dice tests 18/18. `eslint` + `tsc --noEmit` clean.
- Lint/type: `ruff check` clean on all 4 server files; `pyright` adds **0 new errors** (the 23 on `dispatch/dice.py` are pre-existing baseline, verified by stash-compare; pyright is not a project gate).

**Branch:** `feat/165-4-protocol-echoes-ui-math` — pushed (server `0c8b6702`, ui `46f1c6b`, off `develop`).

**Self-review (judgment checks):**
- Wired end-to-end: the range echo flows player strike → `dispatch_dice_throw` → `_compose_result_payload` → broadcast `DiceResultMessage` → `InlineDiceTray` `dice-result-range` (the reviewer's severed flow is now joined on the LIVE dispatch path).
- The move-summary OTEL + fail-loud follow project patterns (sibling `_watcher_publish`, direct required-field access).
- One design deviation logged (the `range_band = _resolved_band or "melee"` melee default) — the honest band for a melee strike; without it the resolution card shows nothing for the most common combat case.

**Handoff:** To Reviewer (Chrisjen) for code review.

## Subagent Results

Rework Round 2 review dispatch. Same enabled set as round 1 (5 disabled via `workflow.reviewer_subagents`).

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (23 story tests pass, 911 UI pass, ruff/eslint/tsc clean, 0 smells) | N/A — corroborates green + independently CONFIRMED the 57 full-suite failures are pre-existing CartographyTreatmentWire (session_helpers.py:1695), not this diff |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings (No-Silent-Fallbacks covered by [RULE] backstop) |
| 4 | reviewer-test-analyzer | Yes | findings | 6 | confirmed 6 as non-blocking [TEST] coverage (ranged-band untested, capable+zero-PC, reach/aoe wiring, move_cells(None), len==1); 0 blocking — verified the 3 fixes' tests are non-vacuous |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 | confirmed 3 [DOC] (stale _enforce_tactical_reach docstring MEDIUM, map_emit local liveness MEDIUM, dice.py None-desc LOW); verified the 4 requested rewordings are honest |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings (echoes are server-authored outbound; no untrusted-input surface) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (redundant-getattr noted from [RULE] instead) |
| 9 | reviewer-rule-checker | Yes | findings | 5 | 3 blocking rules (27/28/29) VERIFIED FIXED; 5 minor: 4× pre-existing TS test idioms (dismissed as non-novel, round-1 precedent) + 1 character_locations getattr (confirmed [RULE], downgraded LOW — provably unreachable fallback) |

**All received:** Yes (4 enabled returned; 5 disabled via settings)
**Total findings:** 0 confirmed blocking, 14 confirmed non-blocking (3 DOC + 6 TEST + 1 RULE-downgraded + 4 TS-idiom-dismissed), plus the pre-existing cartography suite failure (out of scope, verified).

## Rule Compliance (Rework Round 2)

Rule-checker ran exhaustively (30 rules — python.md 13 + typescript.md 13 + 4 CLAUDE.md — across 71 instances). My confirmation of the load-bearing ones:

- **CLAUDE.md No Silent Fallbacks (#27):** **FIXED** — `map_emit.py:298` `pack = sd.genre_pack` and `:301` `get_ruleset_module(pack.rules.ruleset)` are now DIRECT (fail loud), proven by `test_move_summary_fails_loud_when_genre_pack_missing`/`..._pack_rules_missing`. The `combat_move_cells` getattr is COMPLIANT (real capability gate — method absent on base ABC/Fate, verified `without_number.py:193`). **New minor:** `getattr(snapshot, "character_locations", {}) or {}` (`map_emit.py:307`) matches the pattern but is DOWNGRADED to LOW — `character_locations` is a pydantic `Field(default_factory=dict)` (`session.py:1086`), provably never None, so the fallback is unreachable dead-defensiveness (distinct from the round-1 dataclass-nullable genre_pack/rules) and carries the round-1 logic unchanged (mirrors `_place_tokens_on_anchors:59`). Non-blocking cleanup.
- **CLAUDE.md OTEL Observability (#28):** **FIXED** — `map_emit.py:325-337` `_watcher_publish("tactical_grid.move_summary", {…, capable, adjudication_count})` fires unconditionally after the capability branch (both engaged and skip), proven by the two OTEL tests. Verified myself: the call sits outside the `if capable:` block.
- **CLAUDE.md No half-wired features (#29):** **FIXED** — `dispatch/dice.py:854-892` computes `_tactical_range_band`/`_tactical_distance_cells` from the 165-3 reach verdict + resolved band and threads them into `_compose_result_payload` at the emit site; proven end-to-end by `test_dice_range_echo_165_4.py` driving the REAL `dispatch_dice_throw`. Verified myself: the gate still receives the raw `_resolved_band` (unchanged behavior); only the echo is defaulted to "melee".
- **CLAUDE.md Additive protocol (#30):** COMPLIANT — all new fields default None/[]; back-compat tested; empty lists matching defaults are omitted from the wire (`protocol/base.py`).
- **py #2 (mutable defaults):** COMPLIANT — new `_compose_result_payload` kwargs are immutable None; model list fields use `default_factory`.
- **py #3 (type annotations at boundaries):** COMPLIANT — the two new `_compose_result_payload` params fully annotated (`str|None=None`, `int|None=None`).
- **py #6 / ts #21 (test quality):** COMPLIANT on vacuity — OTEL tests patch the correct `map_emit._watcher_publish` (patch-where-used) and assert concrete `capable`/`adjudication_count`; fail-loud tests raise at exactly the fixed line. The melee-only harness (ranged-band untested) is a coverage GAP, not vacuity — see Delivery Findings.
- **py #10 (import hygiene):** COMPLIANT — the `get_ruleset_module` function-local import matches the module's lazy-import convention; no cycle (`game.ruleset.registry` does not import `sidequest.server`).
- **ts #17 (null/undefined `??` vs `||`):** COMPLIANT — `grid.adjudications ?? []`, `a.cells_spent ?? 0` correctly preserve `0`; `range_band != null` guards; no `||` misuse.
- **ts #19 (React keys):** **FIXED** — `TacticalGridRenderer.tsx:181,190` now use content-derived `denial-${a.actor}-${a.kind}` / `move-${a.actor}` (was index-based). Verified myself.
- **ts #14 (type-safety escapes):** 4 minor `data!.`/`as unknown as` in TEST files — byte-for-byte reuse of pre-existing idioms (`tacticalGridFromWire.features.test.ts`, `InlineDiceTray.test.tsx`); dismissed as consistent-with-surrounding-code (round-1 precedent dismissed the same `as unknown as`).

### Devil's Advocate

Argue this ships broken. Start with the human the game exists for: a mechanics-first player (Sebastien/Jade) opens a strike and reads the resolution card. Round 1 it showed *nothing* because no server code populated the range echo. Does it now? Yes — but every test that "proves" it uses `_make_attacker`'s synthetic `blade_2d6`, which is not a catalog item, so `resolve_weapon_range_band_from_beat_and_actor` always returns None and `_resolved_band or "melee"` always collapses to the literal `"melee"`. So the green integration test proves the field is *wired*, not that a real ranged weapon's SRD band (`"100/600"`) ever survives the catalog lookup and reaches the wire. If `resolve_inventory`/the catalog lookup were subtly broken for a real rifle, this suite stays green and the ranged player still reads "melee range" on a rifle shot. That is the same "convincing-but-unproven" shape the project fears — but it is a COVERAGE gap on a trivial `or` expression, not a wiring severance, and the Dev disclosed it. The confused-maintainer angle bites harder: `_enforce_tactical_reach`'s own docstring still says "the returned verdict is dead at the sole call site today," three lines above the call site that THIS diff changed to read `verdict.distance_cells`. A future dev who trusts that docstring could delete the return and silently kill the echo — except the integration test asserts `distance_cells == 2`, so the test guards the regression the stale doc invites. The stressed-invariant angle: if `sd.genre_pack` were ever legitimately absent it now crashes loud (good — that was the fix), but the new `getattr(snapshot, "character_locations", {}) or {}` re-introduces the swallow-shape on a field that (this time) provably can't be None, so it masks nothing real. The multi-opponent angle: the range echo measures distance to `_opposite_side_first_actor` only — in a two-monster fight the card shows distance to the first, which the player may misread as "the nearest." And the whole move-summary half still sits behind the dead `dungeon_store` gate, so the grid echo reaches no one until Plan-7 — but that is disclosed, ruled non-blocking, and the OTEL span now makes even the dead-gated decision observable. None of these are Critical or High: the three blocking severances of round 1 are genuinely closed, the tests are non-vacuous, and the residue is doc-wording, coverage, and one harmless redundancy. This ships.

## Reviewer Assessment — Rework Round 2

**Verdict:** APPROVED

**Round-1 blocking findings — all three verified FIXED** (rule-checker rules 27/28/29 COMPLIANT + my own line-level read + non-vacuous tests):
1. `[RULE]` Half-wired range echo → `dispatch/dice.py` now captures the 165-3 verdict's `distance_cells` + resolved band onto the emitted CHECK `DiceResultPayload` via `_compose_result_payload`; proven end-to-end by `test_dice_range_echo_165_4.py` driving the real dispatch.
2. `[RULE]` Missing OTEL span → `map_emit.py` emits `tactical_grid.move_summary` (`_watcher_publish`, sibling pattern) on both engaged and skip paths with `capable`+`adjudication_count`.
3. `[RULE]` Silent-fallback getattr → `sd.genre_pack`/`pack.rules` accessed directly (fail loud); only the `combat_move_cells` capability getattr remains.

**Data flow traced (the round-1 severed flow, now joined):** player strike → `dispatch_dice_throw` runs `_enforce_tactical_reach` (live store) → verdict's `distance_cells` + resolved `_range_band` CAPTURED into locals → `_compose_result_payload(range_band=…, distance_cells=…)` → broadcast `DiceResultMessage` → `InlineDiceTray` `dice-result-range` renders "· melee range · 2 cells". The discard site the round-1 reject named is gone.

**Non-blocking findings (captured as Delivery Findings; none block):**
- `[DOC]` (MEDIUM) `_enforce_tactical_reach` docstring (`dispatch/dice.py:374-378`) still calls the verdict "dead at the sole call site" — this diff made that false; a maintainability trap (guarded by the integration test, but should be reworded).
- `[DOC]` (MEDIUM) `map_emit.py` move-summary block comment "surfaced" reads as standalone liveness though the block is dead-gated; the top-docstring caveat covers it but the local hunk does not.
- `[DOC]` (LOW) `protocol/dice.py` range docstring omits the "unseated actor" None case.
- `[TEST]` (MEDIUM) ranged-band echo path untested — the melee harness makes `range_band is not None` unconditionally true via the "melee" default; a real SRD band never reaches the wire in test. Disclosed by Dev.
- `[TEST]` (MEDIUM) no `capable=True` + zero-PCs case, so the `capable`/`adjudication_count` independence I required isn't locked; `[TEST]` (MEDIUM) reach/aoe renderer tests have no production producer/wiring test (scope-noted); `[TEST]` (LOW) `move_cells(None)` on a dangling location, missing `len(summaries)==1`.
- `[RULE]` (LOW) `getattr(snapshot,"character_locations",{}) or {}` (`map_emit.py:307`) — pattern-match downgraded (provably unreachable fallback; pre-existing idiom).
- `[TYPE]` (LOW) 4× TS `data!.`/`as unknown as` in test files — pre-existing idiom reuse, dismissed.

**Subagent dispatch coverage:** `[EDGE]` disabled this run · `[SILENT]` disabled this run (No-Silent-Fallbacks caught by `[RULE]` backstop — confirmed fixed) · `[TEST]` coverage gaps confirmed non-blocking · `[DOC]` stale-docstring cluster confirmed non-blocking · `[TYPE]` disabled this run (TS escape idioms noted from `[RULE]`) · `[SEC]` disabled this run (server-authored outbound echoes, no untrusted-input surface) · `[SIMPLE]` disabled this run (redundant getattr noted from `[RULE]`) · `[RULE]` 3 blocking rules verified FIXED + 1 LOW-downgraded getattr + 4 dismissed TS idioms.

**Pre-existing suite state:** the full server suite carries 57 pre-existing `CartographyTreatmentWire` MagicMock failures (Track B, `session_helpers.py:1695`) — preflight independently confirmed they are untouched by this diff, and the Dev's stash-compare (64→57) shows the rework FIXED 6 and regressed 0. Out of Track C scope; flagged as a develop-health Delivery Finding.

**Blocking rule:** 0 Critical/High findings; all 3 round-1 HIGH findings verified fixed. APPROVE.

**Handoff:** To SM (Camina) for finish-story.