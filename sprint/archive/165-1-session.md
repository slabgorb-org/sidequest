---
story_id: "165-1"
jira_key: ""
epic: "165"
workflow: "spdd"
---
# Story 165-1: Pure tactical library: mask parse, Chebyshev, movement flood, reach/range/LOS/AoE (plan tasks 0–3)

## Story Details
- **ID:** 165-1
- **Jira Key:** (no Jira integration)
- **Workflow:** spdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** spdd
**Phase:** finish
**Phase Started:** 2026-07-08T23:43:08Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-08T23:04:32Z | 2026-07-08T23:07:22Z | 2m 50s |
| red | 2026-07-08T23:07:22Z | 2026-07-08T23:18:59Z | 11m 37s |
| green | 2026-07-08T23:18:59Z | 2026-07-08T23:31:22Z | 12m 23s |
| review | 2026-07-08T23:31:22Z | 2026-07-08T23:43:08Z | 11m 46s |
| finish | 2026-07-08T23:43:08Z | - | - |

## Sm Assessment

**Setup complete — routing to TEA (Amos Burton) for the RED phase.**

- **Workflow decision:** Story YAML tags `workflow: superpowers`, not a registered pf workflow. Settled Keith decision (2026-07-08, `sm-decisions.md`): epics 163/164/165 run as **`spdd`** (phased: setup → red → green → review → finish). The written plan is per-phase reference material, not a separate executing-plans run. Not re-asked.
- **Scope:** Server-only, and **purely additive**. This is plan **Tasks 0–3** = the C1 pure cell-math library. No enforcement, no protocol, no UI, no OTEL in this story — those land in siblings 165-2/3/4/5. New pure package `sidequest/game/tactical/` over the `#`/`.` mask string: **no IO, no clock, no random.**
- **Branch:** `feat/165-1-pure-tactical-library` off `develop` (verified: server `origin/HEAD → origin/develop`, no local `main`). Note the plan names the branch `feat/mapping-track-c-tactical`; per-story pf convention overrides — base is `develop`, which is correct. Task 0 (branch setup) is therefore already done.
- **Merge gate:** Clear (0 in-progress, 0 in-review, no blocking PRs).
- **Jira:** Skipped — no Jira integration (`[no jira]`).

**For TEA (RED phase) — the plan is your test source; transcribe, don't author:**
1. **Pre-written test bodies exist.** Plan Tasks 1–3 ship *complete* failing-test code (I confirmed the Task 1 block at plan lines 54–113). RED = transcribe each test file, run it, SEE it fail. Files:
   - Task 1 → `tests/game/tactical/test_adjudication_core.py` (`parse_mask`, `in_bounds`, `is_floor`, `chebyshev_distance`, `neighbors`) against `sidequest/game/tactical/adjudication.py`.
   - Task 2 → movement (reachable flood + path cost) — consumes Task 1 primitives.
   - Task 3 → reach / range / line-of-sight / AoE templates.
2. **Pure-library edge cases are the point** (Global Constraint, plan line 15): diagonals (Chebyshev, not Manhattan), walls, out-of-bounds, zero-budget flood. Table-driven.
3. **Wiring test is DEFERRED by design — do not block on it.** Plan line 18 states explicitly: *"C1's wiring test lives in the C2 enforcement task"* (that's sibling **165-3**, where the WN binding imports + calls the library from `dispatch_dice_throw`). This story has no production consumer yet, by design. The CLAUDE.md wiring rule is satisfied downstream, not here. Reviewer: note this, don't fail 165-1 for missing production call sites.
4. **Test command:** `cd sidequest-server && uv run pytest tests/game/tactical/ -v` (`-n auto` fine — no OTEL span-count tests in this story, so the `-n0` caveat doesn't apply here).
5. **Pre-existing failures to classify, not fix** (plan line 22): ~13 server tests fail vs content `develop` (WWN migration); a stale `MessageType` 54-vs-55 count test. Don't block on these.

Authoritative deliverable detail: **Tasks 0–3** in `docs/superpowers/plans/2026-07-08-mapping-track-c-tactical-mechanics.md` (spec §3: `docs/superpowers/specs/2026-07-08-three-tier-mapping-design.md`).

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking — already corrected in the test, but the plan doc still carries it): The plan's Task-2 test `test_movement_cost_straight_and_diagonal` asserts `movement_cost([(1,1),(2,2)], "###\n#..\n#..") is None` with the comment "(2,2) wall", but `(2,2)` is a **floor** cell in that mask (`rows[2][2] == '.'`), so the plan's own GREEN `movement_cost` returns `1`, not `None` — the assertion can never pass against correct code. Affects `docs/superpowers/plans/2026-07-08-mapping-track-c-tactical-mechanics.md` (Task 2 test block, ~line 233) — the plan mask should be `"###\n#..\n#.#"` (wall at `(2,2)`). Fixed in the transcribed test; **the plan doc should be corrected** so siblings/authors don't re-copy the broken mask. *Found by TEA during test design.*

### Dev (implementation)
- **Conflict** (non-blocking — resolved in this story's impl; plan doc still carries it): The plan's Task-2 `cells_reachable` implementation gates recording in `ReachResult.cost` on `nc <= budget`, so over-budget cells never enter the cost map — but the plan's own Task-2 test `test_reachable_difficult_terrain_doubles_cost` asserts `r.cost[(3,1)] == 3` for an over-budget cell (`KeyError` against the transcribed impl). Affects `docs/superpowers/plans/2026-07-08-mapping-track-c-tactical-mechanics.md` (Task 2 `cells_reachable`, ~plan lines 262–289) — the plan impl should record the true min cost for every relaxed cell and filter `reachable` by budget (as the shipped code now does). Fixed in this story; **the plan doc should be corrected** so siblings 165-2..165-5 don't re-copy the under-baked flood. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): The plan's transcribed C1 tests leave three real branches dark — `movement_cost(difficult=…)` (an independent difficult-terrain impl from `cells_reachable`'s), `line_of_sight` endpoint-exclusion (`ray[1:-1]`), and `aoe_burst(require_los=False)`. Affects `sidequest/game/tactical/adjudication.py` (add coverage for these when the library is next touched — ideally folded into **165-2/165-3** which extend/wire this module). Code verified correct by reading; these are regression-guard gaps, not bugs. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `adjudicate_reach`'s `mode: str` is documented as a closed `'melee'|'ranged'` set but is unvalidated — an unknown mode silently yields the "range" noun and is echoed back (mild No-Silent-Fallbacks tension; impact is cosmetic-only, no wrong adjudication). Affects `sidequest/game/tactical/adjudication.py:234-250` — tighten to `Literal["melee","ranged"]` (also strengthens typing) when **165-3** consumes it. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `ReachResult` docstring understates `cost` — it is a superset of `reachable`'s keys (includes origin at 0 and the over-budget boundary). Affects `sidequest/game/tactical/adjudication.py:66-68` — clarify the docstring so consumers don't read `cost.keys()` as the reachable set. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Corrected a broken mask in the transcribed movement test**
  - Spec source: docs/superpowers/plans/2026-07-08-mapping-track-c-tactical-mechanics.md, Task 2 test `test_movement_cost_straight_and_diagonal` (~line 233)
  - Spec text: `assert movement_cost([(1, 1), (2, 2)], "###\n#..\n#..") is None  # (2,2) wall in this mask`
  - Implementation: changed the mask to `"###\n#..\n#.#"` so `(2,2)` is actually a wall; comment updated to "(2,2) is a wall here"
  - Rationale: In the plan's mask `(2,2)` is floor, so the plan's own GREEN `movement_cost` returns `1`, not `None` — the assertion contradicts the implementation and can never pass. The stated intent ("diagonal step onto a wall is illegal → None") is preserved by making the target cell a wall. Transcribing verbatim would plant a permanent GREEN-blocking failure.
  - Severity: minor
  - Forward impact: The plan doc still contains the broken mask; siblings/authors copying that block must apply the same fix. Logged as a Delivery Finding.

### Dev (implementation)
- **`cells_reachable` records the over-budget frontier's true cost**
  - Spec source: docs/superpowers/plans/2026-07-08-mapping-track-c-tactical-mechanics.md, Task 2 `cells_reachable` impl (~plan lines 262–289); binding contract = TEA's Task-2 test `test_reachable_difficult_terrain_doubles_cost`
  - Spec text (plan impl): `if nc <= budget and (n not in cost or nc < cost[n]): cost[n] = nc; frontier.append(n)` … `reachable = frozenset(c for c in cost if c != origin)`
  - Implementation: split the guard — record `cost[n] = nc` on every relaxation (so the immediate over-budget frontier lands in the cost map), append to the frontier only when `nc <= budget`, and filter `reachable` by `cost[c] <= budget`.
  - Rationale: The plan's own Task-2 test asserts `r.cost[(3,1)] == 3` (an over-budget cell) while requiring `(3,1) not in r.reachable`. The transcribed plan impl never records over-budget cells, so `r.cost[(3,1)]` raises `KeyError`. The test is the contract (higher authority than the plan's reference impl) and its semantics are sound: cost = full min-cost map incl. the immediate boundary, reachable = budget-filtered. Minimal change to satisfy it; verified the other three `cells_reachable` tests still pass.
  - Severity: minor
  - Forward impact: none for consumers using `ReachResult.reachable`; consumers reading `ReachResult.cost` now see cells one step past budget (the test-pinned behavior). Plan doc needs the same correction — logged as a Delivery Finding.

### Reviewer (audit)
- **TEA — corrected the broken mask in `test_movement_cost_straight_and_diagonal`** → ✓ ACCEPTED by Reviewer: Verified independently — in `"###\n#..\n#.."` cell `(2,2)` is `rows[2][2] == '.'` (floor), so the plan's own `movement_cost` returns `1`, not `None`; the assertion could never pass. The fix mask `"###\n#..\n#.#"` makes `(2,2)` a wall, preserving the "diagonal onto a wall → None" intent. Sound and correctly logged as an upstream finding against the plan doc.
- **Dev — `cells_reachable` records the over-budget frontier's true cost** → ✓ ACCEPTED by Reviewer: Verified the plan's own Task-2 test (`r.cost[(3,1)] == 3` with `(3,1) not in reachable`) is unsatisfiable by the plan's transcribed impl (`KeyError`), so the test (higher authority) forces the change. Traced the algorithm: over-budget cells are recorded but never appended to the frontier, so the flood still terminates and does not explore past budget+1; `reachable` is correctly re-filtered by `cost[c] <= budget`; the other three `cells_reachable` tests still pass. Semantics are sound. One follow-on: the `ReachResult` docstring should be updated to reflect that `cost` is now a superset of `reachable` (captured as a non-blocking Reviewer delivery finding, not a flag on the deviation itself).
- No undocumented deviations found: the two ruff idiom fixes Dev noted (`zip(strict=False)`, `all(...)` for LOS) are behavior-identical and correctly judged non-deviations; I confirmed both preserve semantics.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Story 165-1 is the C1 pure cell-math library (plan tasks 1–3) — new production behavior across mask parsing, distance, movement, reach/range/LOS/AoE. Full TDD RED phase.

**Test Files:**
- `tests/game/tactical/__init__.py` — test package marker (empty)
- `tests/game/tactical/test_adjudication_core.py` — Task 1: `parse_mask`, `in_bounds`, `is_floor`, `chebyshev_distance`, `neighbors` (5 tests)
- `tests/game/tactical/test_movement.py` — Task 2: `cells_reachable` (flood), `movement_cost`, `adjudicate_move` (7 tests)
- `tests/game/tactical/test_reach_range_aoe.py` — Task 3: `reach_cells`, `line_of_sight`, `adjudicate_reach`, `aoe_burst`, `aoe_line` (7 tests)

**Tests Written:** 19 tests covering the full C1 pure-library interface (tasks 1–3).
**Status:** RED — confirmed by testing-runner (`165-1-tea-red`): 0 collected, 3 import errors, `ModuleNotFoundError: No module named 'sidequest.game.tactical'`, exit 1. This is the correct RED: the tests fail because the production module (Dev's GREEN work) does not exist yet.

**Source discipline:** Tests transcribed from the plan's pre-written bodies (plan authority + the settled "transcribe, don't author" doctrine for the 163/164/165 spdd stories). I verified every mask-dependent assertion by hand against the plan's stated GREEN implementation — 18 of 19 are correct; the 1 broken one (`test_movement_cost_straight_and_diagonal`, floor cell mislabeled as a wall) was corrected (see Design Deviations + Delivery Findings). No speculative tests added — extra assertions beyond the spec risk manufacturing false-RED requirements Dev cannot satisfy from the plan.

### Rule Coverage

Applicable lang-review (python.md) checks for a **pure, no-IO / no-clock / no-random / no-async / no-network / no-deps** library:

| Rule | Test(s) | Status |
|------|---------|--------|
| #2 mutable default arguments | `frozenset()` (immutable) defaults exercised via all default-path calls; explicit set via `test_reachable_difficult_terrain_doubles_cost` | failing (module missing) |
| #3 type annotations at boundaries | whole suite drives the fully-typed public interface (`parse_mask`, `cells_reachable`, `adjudicate_move`, `adjudicate_reach`, `aoe_burst`, `aoe_line`) — Dev must preserve annotations in GREEN | failing |
| #6 test quality (no vacuous assertions) | self-checked every test — all assert specific values / membership / `is None`; none use `assert True`, bare truthy, or `_ =` | pass (self-check) |
| #11 input validation / no-silent-correction at boundaries | `test_movement_cost_rejects_non_adjacent_and_walls`, `test_reachable_zero_budget_empty`, `test_reach_cells_zero_reach_empty`, `adjudicate_move`/`adjudicate_reach` denial-reason tests | failing |

**Rules checked:** 4 of 4 applicable checks covered. The other 9 (#1 silent-except, #4 logging, #5 path-handling, #7 resource-leaks, #8 deserialization, #9 async, #10 import-hygiene, #12 deps, #13 fix-regressions) are **N/A** — this module has no IO, no exceptions, no logging, no paths, no resources, no async, no new deps. (#10 `__all__` is a Reviewer nicety for the new package, not test-enforceable at RED.)
**Self-check:** 0 vacuous tests (all transcribed tests carry meaningful assertions).

### Coverage notes for Dev/Reviewer (non-blocking)
Behaviors present in the interface but *not* exercised by the plan's tests (documented, not gaps I'd block on): `line_of_sight` endpoint-exclusion (endpoints never block), `aoe_burst(require_los=False)` path, and ragged-row mask safety (`in_bounds` is per-row, so it's robust). Left untested to stay faithful to the plan's RED spec.

**Wiring test:** Deliberately absent this story — plan Global Constraint (line 18) puts C1's production-reachability test in the C2 enforcement story (**165-3**, WN binding calls the library from `dispatch_dice_throw`). Reviewer: do not fail 165-1 for a missing production consumer.

**Handoff:** To Dev (Naomi Nagata) for GREEN — implement `sidequest/game/tactical/__init__.py` + `adjudication.py` per plan tasks 1–3 until all 19 tests pass.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/game/tactical/__init__.py` — new pure package marker (one-line docstring)
- `sidequest/game/tactical/adjudication.py` — new C1 library: `Cell`, `parse_mask`, `in_bounds`, `is_floor`, `chebyshev_distance`, `neighbors`, `ReachResult`, `cells_reachable`, `movement_cost`, `MoveAdjudication`, `adjudicate_move`, `reach_cells`, `_ray_cells`, `line_of_sight`, `RangeAdjudication`, `adjudicate_reach`, `aoe_burst`, `aoe_line`. Pure — no IO, no clock, no random.
- `tests/game/tactical/test_reach_range_aoe.py` — ruff-format line-wrap only (no logic change; TEA's tests unchanged in behavior)

**Tests:** 19/19 passing (GREEN) — fresh evidence from testing-runner `165-1-dev-green-final`: 19 passed / 0 failed / 0 errors, exit 0.
**Quality:** `ruff check` clean, `ruff format --check` clean, `pyright` 0 errors — all on the touched tactical files.
**Branch:** `feat/165-1-pure-tactical-library` (pushed to origin, tracking set).

**Implementation notes for Reviewer:**
- **One deviation from the plan's transcribed impl** (logged in Design Deviations): `cells_reachable` now records the true min cost for the immediate over-budget frontier in `ReachResult.cost` and filters `reachable` by budget. This was forced by the plan's *own* Task-2 test (`test_reachable_difficult_terrain_doubles_cost`), which the plan's transcribed impl could not pass (`KeyError`). The other 18 tests were satisfied by the plan's code verbatim.
- **Two behavior-identical ruff fixes** to the plan's code: `zip(path, path[1:], strict=False)` (B905) and `line_of_sight` returns `all(...)` (SIM110). No deviation logged — behavior is byte-identical; noted here for transparency.
- **Wiring:** intentionally no production consumer this story (per plan Global Constraint line 18 + TEA note) — C1's production-reachability wiring lands in **165-3** (WN binding calls the library from `dispatch_dice_throw`). This is by design, not a half-wired feature. Please don't fail 165-1 for a missing call site.
- **Scope discipline:** implemented exactly the plan's Task 1–3 interface, no `__all__`/extra abstractions beyond the tests (minimalist). Coverage notes TEA flagged (`line_of_sight` endpoint exclusion, `aoe_burst(require_los=False)`, ragged rows) remain untested — left as-is to stay within story scope.

**Handoff:** To Reviewer (Chrisjen Avasarala) for the review phase.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (19/19 tests green, ruff clean, format clean, pyright 0, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — domain assessed by Reviewer (see [EDGE] below) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — domain assessed by Reviewer + rule-checker #14 (see [SILENT]) |
| 4 | reviewer-test-analyzer | Yes | findings | 9 (coverage gaps + 1 weak assertion + 1 misleading comment) | confirmed 9, dismissed 0, deferred 0 — all MEDIUM/LOW, non-blocking |
| 5 | reviewer-comment-analyzer | Yes | findings | 7 (doc accuracy) | confirmed 7, dismissed 0 — all LOW/MEDIUM, non-blocking |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — domain assessed by Reviewer (see [TYPE]) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings — domain assessed by Reviewer (see [SEC]) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — domain assessed by Reviewer (see [SIMPLE]) |
| 9 | reviewer-rule-checker | Yes | findings | 3 (#10 missing `__all__` ×2 instances, #14 unvalidated `mode`) | confirmed 3, dismissed 0 — LOW, non-blocking |

**All received:** Yes (4 enabled returned; 5 disabled via `workflow.reviewer_subagents`, their domains assessed inline by Reviewer)
**Total findings:** 19 confirmed (all MEDIUM/LOW, non-blocking), 0 dismissed, 3 recorded as delivery findings for follow-up. No Critical/High.

## Reviewer Assessment

**Verdict:** APPROVED

Pure additive C1 cell-math library (`sidequest/game/tactical/adjudication.py`) implementing plan tasks 1–3. 19/19 tests green, ruff/pyright clean. I read every function and hand-verified the algorithms; the code is **correct**. Every finding below is a MEDIUM coverage gap or a LOW doc/style/param nit — none block per the severity rubric (Critical/High only). Nothing dismissed; the load-bearing gaps are tracked as delivery findings.

**Data flow traced:** `mask: str` (the `TacticalGridPayload.mask` shape) → `parse_mask` → `is_floor`/`neighbors`/Dijkstra/Bresenham → pure `ReachResult`/`MoveAdjudication`/`RangeAdjudication`/`frozenset` return values. No IO, no mutation of inputs, no global state. Safe: the module never trusts a cell is in-bounds without `in_bounds` (short-circuit `and` prevents `IndexError`), and every adjudicator returns an explicit invalid verdict with a legible reason rather than correcting bad input.

### Observations

- `[VERIFIED]` **No correctness bugs.** Traced `cells_reachable` termination (over-budget cells recorded but never appended to the frontier → flood still drains; costs are positive ints, strictly-decreasing relaxation → finite re-appends), `in_bounds` short-circuit (no `IndexError` on ragged/empty rows), and `_ray_cells` Bresenham reaches its endpoint for all cases incl. `a==b`. Evidence: `adjudication.py:89-105, 37-39, 200-209`.
- `[EDGE]` (edge-hunter disabled — assessed by Reviewer): Boundary cases are sound — `budget<=0`/`reach<=0`/`radius 0`/`a==b`/empty-mask (`parse_mask("")==[""]`, no floor cells) all handled without crashes. `line_of_sight` on adjacent/same cells → `all([])==True` (LOS trivially clear), matching the docstring. `[VERIFIED]` at `adjudication.py:85, 176, 218, 272-275`.
- `[SILENT]` (silent-failure-hunter disabled — assessed by Reviewer + `[RULE]` #14): The module's fail-loud discipline is real (`movement_cost`→`None`, `adjudicate_*`→invalid verdict with reason, never clamps). **One mild exception:** `adjudicate_reach`'s unvalidated `mode` silently falls to the "range" noun on an unknown value (`adjudication.py:250`). Impact is cosmetic (denial-noun only; the bad value is echoed in `RangeAdjudication.mode` for observability) — LOW, non-blocking, but recorded (can't dismiss a No-Silent-Fallbacks match). Recommend `Literal["melee","ranged"]`.
- `[TEST]` Coverage gaps in the plan's transcribed tests (MEDIUM, non-blocking): `movement_cost(difficult=…)` untested (independent difficult-terrain impl), `line_of_sight` endpoint-exclusion untested, `aoe_burst(require_los=False)` untested, ranged-too-far noun untested, `aoe_burst` radius asserts presence-not-absence, `adjudicate_move` origin-mismatch branch untested, and the `"path" in reason` assertion can't distinguish the two denial branches. Code verified correct; these are regression-guard gaps. Consistent with TEA's own "transcribe, don't author" doctrine + documented coverage notes. Deferred to 165-2/165-3 (delivery finding).
- `[DOC]` `ReachResult` docstring understates `cost` (it's a superset of `reachable` — includes origin + over-budget boundary; `adjudication.py:66-68`) — HIGH-confidence, LOW-severity; recorded. `aoe_burst`/`RangeAdjudication.has_los` docstrings omit the `require_los` knob and its "unchecked=True" meaning (`adjudication.py:266, 223-231`). `in_bounds` is the one undocstringed public fn (`:37`). Comments at `:90` ("linear min-scan" — it's a sort) and `:190` ("supercover-lite" — plain Bresenham) are imprecise. All LOW.
- `[DOC]`/`[TEST]` **The `test_movement.py:32-33` comment contradicts its own assertion** ("you can still stop on it" vs `assert (3,1) not in r.reachable`). Both test-analyzer and comment-analyzer flagged it, HIGH confidence. LOW severity (comment only), but a genuine defect carried verbatim from the plan doc — recommend a 1-line fix here and in the plan.
- `[TYPE]` (type-design disabled — assessed by Reviewer): `mode: str` is stringly-typed (should be `Literal`), and `ReachResult.cost: dict` is a mutable field on a frozen dataclass (attribute frozen, dict contents not). Both LOW — plan-spec'd interface, pure-return-value, no real exploit surface. Frozen dataclasses + `Cell` alias are otherwise good.
- `[SEC]` (security disabled — assessed by Reviewer): `[VERIFIED]` no security surface — pure in-memory math, no auth/tenant/injection/deserialization/secrets/paths. N/A clean.
- `[SIMPLE]` (simplifier disabled — assessed by Reviewer): `WALL_CHAR = "#"` (`:18`) is defined but never referenced anywhere in the repo — mild dead code, but defensible as a documented public sibling of `FLOOR_CHAR` (the mask alphabet; siblings 165-2/3 may consume it). `frontier.sort()` each iteration is O(n²log n) but deliberately simple for room-scale grids (comment acknowledges). LOW.
- `[RULE]` rule-checker: #10 missing `__all__` on the new public module (2 instances) — LOW; consistent with 72% of `sidequest/game/` modules that also omit it, so a nicety not a house-rule violation. #14 covered under [SILENT]. Not dismissed; downgraded to LOW with rationale.

### Rule Compliance (python.md lang-review + SOUL/CLAUDE)

- **#2 mutable defaults:** COMPLIANT — `difficult=frozenset()` (×3) and `require_los=True` are immutable; not the `[]`/`{}` bug. (`:79,112,148,266`)
- **#3 type annotations at boundaries:** COMPLIANT — all 14 public fns + 3 dataclasses fully annotated, no `Any`/`# type: ignore`.
- **#6 test quality:** COMPLIANT with nits — no vacuous assertions; the `"path"` substring assertion is weak (can't distinguish branches) but not vacuous. `[TEST]`
- **#10 import hygiene:** VIOLATION (LOW) — no `__all__`; no star imports, no circular imports. Downgraded (majority-of-siblings omit it).
- **#11 input validation:** N/A for this story — no CLI/API/file boundary; deferred to 165-3's `dispatch_dice_throw` gate.
- **#1/#4/#5/#7/#8/#9/#12/#13:** N/A — pure library, no exceptions/logging/paths/resources/deserialization/async/deps/fix-rescan.
- **SOUL No Silent Fallbacks:** COMPLIANT except the LOW `mode` nit (`[SILENT]`).
- **SOUL Bind the Ruleset:** COMPLIANT — the library is ruleset-neutral (works in cell units, "never knows a ruleset"); the WN/Fate bindings consume it later. No native mechanic being balanced.
- **CLAUDE No Stubbing / Verify Wiring:** COMPLIANT — module is fully implemented (no placeholder bodies). Zero production consumers today is **by design** (plan Global Constraint line 18: C1's wiring test lives in 165-3). `[VERIFIED]` via repo grep: `sidequest.game.tactical` has no non-test importer. Flagged for 165-3 to include the integration/wiring test that reaches this module from a real dispatch path.

### Devil's Advocate

Suppose this library is broken. Where would it bite? **Attack 1 — malformed masks.** A ragged mask (rows of unequal length) or an empty string could `IndexError`. Checked: `in_bounds` uses `0 <= x < len(rows[y])` *after* the short-circuited `0 <= y < len(rows)`, so `rows[y]` is only indexed when `y` is valid, and per-row length handles ragged rows. `parse_mask("")` → `[""]`, and every `is_floor` on it returns False. No crash. **Attack 2 — unbounded flood.** Could `cells_reachable` loop forever or explode memory now that it records over-budget cells? No: over-budget cells are recorded but never appended to `frontier`, so exploration stops at budget+1; a cell re-enters the frontier only on strict cost decrease, bounded below by 0 → finite. Memory is bounded by within-budget cells + their immediate neighbors. **Attack 3 — a confused caller reads `cost.keys()` as reachable.** This is real: the docstring invites it and `cost` now includes unreachable boundary cells. Consequence would be over-permissive movement UI/telemetry. Mitigated: `reachable` is the documented accessor; recorded as a doc finding. **Attack 4 — a typo'd `mode`.** `adjudicate_reach(mode="attack")` → treated as ranged for the noun, echoed back. No wrong in/out-of-range verdict (mode never gates distance/LOS). Cosmetic only; recorded. **Attack 5 — Bresenham asymmetry.** `line_of_sight(a,b)` vs `(b,a)` could disagree if the ray is direction-dependent, letting a shot land one way but not the other. This is a known Bresenham property and untested — but it does not corrupt state, and LOS symmetry is a refinement for a later hardening pass, not a correctness break in this pure library. Net: the devil finds doc-clarity and coverage debt, not a data-corruption or crash path. Verdict stands.

### Verdict rationale

APPROVED. Zero Critical/High. The implementation is correct, green, lint/type-clean, and scoped exactly to plan tasks 1–3. Both logged deviations (TEA mask fix, Dev flood-cost) are independently verified sound and stamped ACCEPTED. The coverage/doc findings are MEDIUM/LOW, tracked as delivery findings for the sibling stories that extend and wire this library (165-2/165-3). Deferred production wiring is by explicit plan design, not a half-wired feature.

**Handoff:** To SM (Camina Drummer) for finish-story.

<skills-invoked>
<skill name="test-driven-development" phase="red" at="2026-07-08T23:15:40Z"/>
<skill name="test-driven-development" phase="green" at="2026-07-08T23:29:37Z"/>
<skill name="verification-before-completion" phase="green" at="2026-07-08T23:29:37Z"/>
<skill name="requesting-code-review" phase="green" at="2026-07-08T23:29:37Z"/>
</skills-invoked>