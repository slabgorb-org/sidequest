---
story_id: "164-8"
jira_key: ""
epic: "164"
workflow: "trivial"
---
# Story 164-8: Playtest sunden_descend_trace

## Story Details
- **ID:** 164-8
- **Jira Key:** Not applicable (Jira integration not in use for this story)
- **Workflow:** trivial
- **Type:** chore
- **Points:** 2
- **Epic:** 164 — Mapping Track B — Site system
- **Stack Parent:** none

## Context
This is a playtest-validation gate for story 164-3. The goal is to run the headless scenario `sunden_descend_trace` against a live server and confirm the Track B site cutover works end-to-end before 164-3 can be finished/merged.

**Repos Under Test:** sidequest-server + sidequest-content are EXERCISED (not modified) on branch `feat/164-3-router-sites-movement-cutover-sunden-frontier`; no new branches created for them. Orchestrator is trunk-based (no branching).

## Acceptance Criteria
All of the following must be confirmed by running the playtest scenario:

1. The real intent router emits `enter_site` targeting site "The Deep"
2. Crossing + expansion spans fire: `movement.resolved` with reason `onward_ring_drained`, and `site.enter`
3. NO `movement.unresolved` and NO `dispatch_engagement.movement.mismatch` spans
4. Descriptor-matching holds: player phrasing "down the rope" resolves against site name "The Deep"

**Technical Approach:** Run `/sq-playtest headless scenario sunden_descend_trace` against a live server. Assert that OTEL spans in the watcher output match the criteria above. This is the pre-merge gate for 164-3.

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-07-09T16:25:13Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-09T10:59:26Z | 2026-07-09T11:02:48Z | 3m 22s |
| implement | 2026-07-09T11:02:48Z | 2026-07-09T16:14:22Z | 5h 11m |
| review | 2026-07-09T16:14:22Z | 2026-07-09T16:25:13Z | 10m 51s |
| finish | 2026-07-09T16:25:13Z | - | - |

## SM Assessment

**Setup verdict:** Ready for implement (playtest run). Session + context created; branch footgun avoided.

- **Why this story exists:** 164-3 (RISKY Track B site cutover) is reviewer-APPROVED but its AC-5 integration gate — `just playtest-scenario sunden_descend_trace` — was never run (no live stack in the review session). The 164-3 reviewer explicitly required SM to ensure it runs before merge. 164-8 IS that gate.
- **Ordering (SM-enforced, not gated):** Run 164-8 to a pass FIRST, then finish 164-3. `depends_on` deliberately left unset — setting `depends_on: 164-3` would make the stack-ready gate demand 164-3's PR merge first, which is backwards. Do NOT run the 164-3 finish flow until 164-8 confirms the four ACs.
- **Branch discipline:** server + content are on `feat/164-3-router-sites-movement-cutover-sunden-frontier` (the code under test — content `6a10e14` declares "The Deep"; server carries the router/movement cutover). REPOS was constrained to `orchestrator` (trunk-based) so setup did NOT rebranch the exercised subrepos off develop. Whoever runs the playtest must confirm the stack comes up on this branch, not develop.
- **Prerequisite for implement:** the live stack (server + daemon at minimum) must be running on the 164-3 branch before `/sq-playtest` headless can drive `sunden_descend_trace`. The reviewer flagged the descriptor-matching AC (player "down the rope" vs site name "The Deep") as the one most likely to surface a real bug — watch it.
- **On failure:** a failing AC is a 164-3 rework (back to Dev on the 164-3 branch via /patch or reopen), not a 164-8 code change. 164-8 only records the result.

## Dev Assessment

**FINAL: gate FAILED on first run → root-caused → 164-3 fixed → re-verified live. Cutover now works (PC descends the_dropmouth→entrance→exp005.r1). RESUME SESSION dispositioned all three open items: fix COMMITTED (`1fca4a13`) → handing to review phase; AC-3 residual spun into `164-9`; 52 branch failures investigated → REAL + pre-existing on `develop`, not a 164-3 regression, do not block merge.**

### Fix applied (164-3 rework, done in the 164-8 implement phase per SM assessment)
- **Root cause:** `enter_site.py`'s frontier-legacy fallback checked `graph.entrance_id`, but `PgDungeonRepository.load_map` (`game/pg/dungeon.py:450`) sets `graph.entrance_id` to the caller-passed `entrance_id` (== `site.entrance_node_id` == `"frontier:entrance"` == the `target` that just failed the membership check). So the fallback was **dead code that could never fire**; every live Sünden descent died at `no_site_entrance` despite the real un-namespaced `"entrance"` node being present (DB confirmed: 7 nodes under `site_id="frontier"`, `entrance` present).
- **Fix (`sidequest-server/sidequest/game/sites/enter_site.py`):** fallback now keys off `seed_bootstrap.ENTRANCE_ID` (`"entrance"`), the real persisted frontier-legacy entrance node, not `graph.entrance_id`.
- **Test-double infidelity fixed (why it shipped green):** `_LegacyEntranceStore` (`tests/game/sites/test_site_resolvers.py`) and `_StoreWithEntrance` (`tests/integration/test_seam_crossing_wiring.py`) hardcoded `RegionGraph(entrance_id="entrance")`, diverging from the real `load_map` (which echoes the passed id). They now mirror the real repo → the frontier-legacy test reproduces the bug (RED) and guards it (GREEN).
- **TDD:** RED confirmed (`test_enter_site_frontier_legacy_binds_seed_entrance` failed on faithful fake) → GREEN after fix. Blast-radius suites (`tests/game/sites`, seam, movement cutover, sunden characterization, dungeon keying/lifecycle): **65 passed, 3 skipped**. Lint + format clean.

### Live re-verification (fixed server, fresh session `2026-07-09-beneath_sunden-44822630`)
- **Descent path (movement.resolved):** `the_dropmouth→entrance` (site crossing) → `entrance→exp001.r2→exp001.r1→exp001.r3→exp004.r1→exp005.r0→exp005.r1`. Final PC region **`exp005.r1`** (deep in dungeon; failed run stayed at `ropefoot` all 14 turns).
- **AC-1 PASS** (crossing via `resolve_enter_site`, fallback bound to `entrance`); **AC-2 PASS** (`movement.resolved` ×7, 6 `onward_ring_drained=True`; `site.enter` fired — Jaeger ops confirms, missing from jsonl only due to Jaeger trace-capture limit); **AC-4 PASS** (descent resolved from the descriptor). `no_site_entrance`=0, `site.enter_unresolved`=0 (both were present in the failed run).
- **AC-3 PARTIAL/caveat:** cutover-failure spans eliminated, but 3 `movement.unresolved reason=ambiguous_descriptor` + 1 `dispatch_engagement.movement.mismatch` (turn 9, `back`) remain — all from the scenario's deliberately-vague phase-2 expansion actions matching multiple real exits in a branched dungeon (`available=[exp001.r0, exp001.r2, exp001.r4]`). Navigation *disambiguation*, not a dead-end (PC kept descending). Arguably correct engine behavior; separate from the site cutover. **DISPOSITIONED (resume session): accepted as arguably-correct current behavior; disambiguation deferred to follow-up story `164-9`.**

### Regression check + 52-failure investigation (RESUME SESSION — env-vs-real answered)
- Full server suite: 13360 passed, **52 failed** — verified **pre-existing on `feat/164-3` @ 04d674dd** (identical failures with my 3-file change stashed). Files: `test_dungeon_room_population_153_23` (5), `test_turn_span_wiring` (2), `test_tension_tracker_turn_wiring` (3), `test_lull_escalation_turn_wiring` (2), `test_turn_record_wiring` (2), `test_pregen_bestiary_90_1` (1), + others.
- **Env-vs-real verdict (investigated per SM disposition): REAL + deterministic + inherited from `develop` — NOT environmental (no DB/server pollution), NOT a 164-3 regression.** Proof: (a) all named failing test files + `sidecar_extractor.py` + both conftests are **byte-identical to `develop`** (`git diff develop...HEAD` empty); the branch is only 4 commits ahead and its sole turn-pipeline change is `intent_router.py`/`intent_router_pass.py` (both faked by an autouse fixture). (b) Swapping develop's pipeline files into the tree reproduces the **same 5 failures identically**.
- **Two failure classes, both pre-existing test debt on `develop`:**
  - **Class A — sidecar-transport hermeticity:** the turn-pipeline wiring tests (`turn_span`, `turn_record`, `tension_tracker`, `lull_escalation`) reach the real `claude-agent-sdk query()` because the autouse conftest fakes `build_llm_client` but **not** the sidecar `query` path → `sidecar_extraction.failed reason=transport … must be hermetic`.
  - **Class B — `CartographyTreatmentWire` ValidationError (×10):** pydantic "3 validation errors" in `test_dungeon_room_population_153_23`, schema/fixture drift from the 163-1 map treatment layer (test file byte-identical to develop; 164-3 touches no cartography/treatment code).
- **Bottom line: these 52 do NOT block the 164-3 merge** (inherited from the base branch, unrelated to this delta). They are genuine develop-level test debt worth their own cleanup — see the Delivery Finding below.

### State / next steps (SM disposition — RESOLVED this session)
- **Fix COMMITTED** on `feat/164-3` (server repo) as `1fca4a13` — `fix(164-3): bind frontier-legacy site entrance to persisted ENTRANCE_ID` (3 files: `enter_site.py` + 2 test doubles). Re-verified GREEN before commit (12 passed on the two modified test files). Working tree clean. **Not pushed** — re-review is an internal phase (no GitHub PR exists for the branch).
- **164-3 re-review REQUIRED before merge:** 164-3 was reviewer-APPROVED at `04d674dd`; `1fca4a13` is a post-approval delta. Handing 164-8 to its **review** phase (Reviewer / Westley) so the delta is re-reviewed — this IS the "commit + re-review now" disposition.
- **AC-3 residual → follow-up story CREATED:** `164-9` (feature, p2, tdd, server) — "Ambiguous-descriptor navigation disambiguation in branched dungeons." The AC-3 residual is accepted as arguably-correct current behavior; disambiguation is deferred to 164-9.
- Live stack (Jaeger + fixed server) left UP for any further checks.

---
_Original first-run failure record (kept for the audit trail):_

**Gate result (first run): ❌ FAIL — all four ACs failed. 164-3 must NOT be merged (before fix).**

**What ran:** `scripts/playtest.py --scenario scenarios/sunden_descend_trace.yaml --span-jsonl … --fresh` against a live traced stack (server + content on `feat/164-3-…` @ 04d674dd, Jaeger OTLP + `SIDEQUEST_WATCHER_AS_SPANS=1`). Exit 0 → 1597 spans captured (9 `narration.turn`). Session `2026-07-09-beneath_sunden-d5359794`. Full evidence report: scratchpad `164-8-playtest-verdict.md`.

**Headline:** the PC **never left the starting region `ropefoot`** across all 14 actions. The site-enter cutover never engaged mechanically; the narrator improvised a descent the engine never backed.

**AC results:**
- **AC-1 (router emits `enter_site` → "The Deep"): FAIL.** Router emitted region `move deeper` (`intent.direction=deeper`); when a site attempt occurred (descriptor `'the Deep'`), the entrance set was `available=[]`. No successful `enter_site`.
- **AC-2 (`movement.resolved` `onward_ring_drained` + `site.enter`): FAIL.** Neither ever fired (absent from Jaeger ops list). Instead `site.enter_unresolved` + `movement.unresolved`.
- **AC-3 (NO `movement.unresolved` / NO `dispatch_engagement.movement.mismatch`): FAIL.** `movement.unresolved` ×2 (`reason=no_site_entrance`), `dispatch_engagement.movement.mismatch` ×9 (`evidence: "router dispatched movement; PC did not relocate"`).
- **AC-4 (descriptor "down the rope"/"the Deep" → "The Deep"): FAIL.** descriptor `'the Deep'` → `available=[]`; `"Down the Rope"` routed as region `deeper`.

**Root cause (CORRECTED — initial geometry hypothesis was wrong):** The descriptor "the Deep" DOES resolve to the frontier site from ropefoot — `movement.py:492 site_registry.resolve_descriptor(from_region=ropefoot, "the Deep")` returns the site (not None, not ambiguous). Registry + `attached_to` geometry are fine. The `available=[]` in the log is a hardcoded placeholder for this error class (`movement.py:567`), NOT a "no entrances" signal. The ACTUAL failure: `movement.py:540 resolve_enter_site` → `enter_site.py:59-72` loads `dungeon_repository.load_map(entrance_id=site.entrance_node_id, site_id=…)` and finds the site's `entrance_node_id` is NOT in the graph AND there is no usable `graph.entrance_id` → raises `no_site_entrance` = *"The interior of The Deep has not yet formed."* Per the resolver docstring, the entrance node is "expected to already exist — a frontier site was bootstrapped at connect; this resolver only binds, never generates." **The connect-time frontier bootstrap never produced a bindable entrance node** for the site's procedural interior — so the first rung of the descent (surface→interior seam) fails, and every later turn falls back to region "move deeper" onto a surface with no downward node → mismatch ×9. Fix is a 164-3 rework at the connect-time frontier-interior bootstrap / entrance-node materialization (the surface-cartography ↔ procedural-dungeon seam), NOT the router and NOT the site geometry.

**Lie-detector:** `movement.region_mode from_region=ropefoot` on all 9 turns while `narrator.location_drift_repaired … new_from_title='Sünden Deep — The Shaft'` with `current_region='ropefoot'` — convincing prose, zero mechanical backing (OTEL Principle catch).

**Files Changed:** none (validation-only chore; no server/content code touched — the failing ACs are a 164-3 rework per the SM assessment).
**Branch:** none (orchestrator trunk-based). server+content unmodified on `feat/164-3-…`.
**Handoff:** To SM (Vizzini) — BLOCKING finding: 164-3 must not merge; route 164-3 to rework. Live stack (Jaeger + server) left up pending disposition.

## Delivery Findings

No upstream findings at setup.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Gap** (blocking): 164-3 Track B site cutover does not resolve at runtime. The descriptor "the Deep" DOES resolve to the frontier site from ropefoot (registry/geometry fine), but `resolve_enter_site` raises `no_site_entrance` ("The interior of The Deep has not yet formed") — the site's `entrance_node_id` is absent from the loaded dungeon graph and there is no usable `graph.entrance_id`. The connect-time frontier-interior bootstrap never produced a bindable entrance node, so `site.enter`/`movement.resolved` never fire, the PC stays at `ropefoot` all 14 turns, and the narrator improvises an unbacked "Sünden Deep" descent (region drift-repair with `current_region=ropefoot`). Affects `sidequest-server`: the connect-time frontier bootstrap / entrance-node materialization at the surface-cartography ↔ procedural-dungeon seam (`sidequest/dungeon/seed_bootstrap.py`, `sidequest/game/sites/enter_site.py:59-72`, `sidequest/server/session_helpers.py` dungeon region-projection). *Found by Dev during 164-8 playtest gate — blocks 164-3 merge.*
- **Improvement** (non-blocking): `scripts/playtest.py` imports `rich`, which is not declared in `sidequest-server/pyproject.toml` (nor its `dev` extra); `just playtest-scenario` fails with `ModuleNotFoundError: No module named 'rich'`. Ran via `uv run --with rich`. Affects `sidequest-server/pyproject.toml` (add `rich` to dev deps). *Found by Dev during 164-8 playtest gate.*
- **Gap** (non-blocking): `develop` carries **52 deterministic test failures** in two classes — (A) turn-pipeline wiring tests (`test_turn_span_wiring`, `test_turn_record_wiring`, `test_tension_tracker_turn_wiring`, `test_lull_escalation_turn_wiring`) reach the real `claude-agent-sdk query()` because the autouse conftest fakes `build_llm_client` but not the sidecar `query` path; (B) `test_dungeon_room_population_153_23` raises `CartographyTreatmentWire` pydantic ValidationError (×10) from 163-1 map-treatment-layer schema/fixture drift. Both inherited by `feat/164-3` (do not block its merge) but they mask real regression signal on the base branch. Affects `sidequest-server` (`tests/server/conftest.py` — add an autouse sidecar `query` fake; the 163-1 `CartographyTreatmentWire` emitter/fixtures). *Found by Dev during 164-8 env-vs-real investigation — recommend a dedicated develop test-debt cleanup story (not created; SM/PM planning call).*

### Reviewer (code review)
- **Improvement** (non-blocking): the frontier-legacy fallback (`sidequest/game/sites/enter_site.py:65`) is gated on `ENTRANCE_ID in graph.nodes`, not on `site.extent == "frontier"`. It is now correct + reachable-only-by-the-frontier-site today (frontier `site_id` authored exactly once), but it is *extent-blind*: a future bounded site authored with `site_id == "frontier"` (== `DEFAULT_SITE_ID`, `game/pg/dungeon.py:87`) whose real interior never materialized would silently bind to Sünden's legacy `entrance` node instead of raising `no_site_entrance`. No validator forbids that `site_id` collision (`SiteDecl.site_id` is unconstrained `str`, `genre/models/world.py:203`). Affects `sidequest/game/sites/enter_site.py:65` (gate on `site.extent == "frontier"`) and/or genre-pack load validation (reject `site_id == DEFAULT_SITE_ID` for non-frontier extents). *Found by Reviewer during code review — corroborated by silent-failure-hunter + security specialists.*
- **Improvement** (non-blocking): the fallback decision is observable only via `logger.warning` (`enter_site.py:66`), not on the `site_enter_span` — `resolved_via` is caller-passed and identical for primary-bind vs fallback-bind, so the GM panel cannot tell that a Sünden entry resolved via the legacy fallback (which, with B4 namespacing deferred, is *every* Sünden entry). Maps to the OTEL Observability Principle. Affects `sidequest/game/sites/enter_site.py:66` + `sidequest/telemetry/spans/site.py` (stamp `entrance_fallback` and route it through `SPAN_ROUTES` so it mirrors to the sink). *Found by Reviewer during code review — corroborated by silent-failure-hunter.*
- **Improvement** (non-blocking): the delta renamed `test_enter_site_frontier_legacy_prefers_graph_entrance` → `test_enter_site_frontier_legacy_binds_seed_entrance` but left a now-orphaned cross-reference and a stale mechanism description in the sibling `test_enter_site_missing_entrance_node_raises` docstring (`tests/game/sites/test_site_resolvers.py:185` — references the renamed test and still describes the old `graph.entrance_id` fallback). Affects `tests/game/sites/test_site_resolvers.py:184-188` (update the docstring). *Found by Reviewer during code review — comment-analyzer was disabled; caught by hand.*

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Applied the 164-3 fix within the 164-8 implement phase (rather than only recording the gate result)**
  - Spec source: 164-8 SM Assessment ("On failure: a failing AC is a 164-3 rework … 164-8 only records the result")
  - Spec text: "a failing AC is a 164-3 rework (back to Dev on the 164-3 branch via /patch or reopen), not a 164-8 code change. 164-8 only records the result."
  - Implementation: With the operator's explicit direction (chose "fix it now, re-run the gate"), diagnosed + fixed the root cause in `sidequest-server` (`game/sites/enter_site.py` + 2 test doubles) on the `feat/164-3` branch, then re-ran the 164-8 gate to green.
  - Rationale: Operator directed the fix while the live repro was hot and isolated to one `load_map` fallback; fixing in-place avoided losing the reproduction. The change lands on `feat/164-3` (the code under test), not a 164-8 deliverable — so it is a 164-3 rework, just performed during 164-8's run.
  - Severity: minor
  - Forward impact: 164-3 gains a post-approval delta (3 files) that must be committed + re-reviewed before merge; 164-8's own deliverable (the validation report) is unchanged.

### Reviewer (audit)
- **Applied the 164-3 fix within the 164-8 implement phase** → ✓ **ACCEPTED by Reviewer**: sound. The operator explicitly directed the fix while the live repro was hot; the change landed on `feat/164-3` (the code under test), not on a 164-8 deliverable; the delta was correctly flagged for commit + re-review, which is this review. 164-8's validation report is unchanged. No undocumented deviations found in the delta.

## Subagent Results

Subagent toggles (`workflow.reviewer_subagents`): only `preflight`, `silent_failure_hunter`, `security` enabled; the other six disabled via settings — their domains were covered by hand (see Rule Compliance + observations).

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 12/12 tests GREEN, ruff check+format clean, no circular import, production wiring confirmed |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — boundaries enumerated by hand (see Devil's Advocate) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 (both medium) | confirmed 2, dismissed 0, deferred 0 — extent-blind fallback + OTEL discriminator gap, both non-blocking Medium |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — test quality reviewed by hand (behavioral assertions, faithful doubles; bounded-extent gap noted) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — caught stale sibling-test docstring by hand (test_site_resolvers.py:185) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — no new type surface; `RegionGraph.entrance_id` unvalidated (pre-existing), `ENTRANCE_ID` is a str constant |
| 7 | reviewer-security | Yes | clean | none | N/A — full upstream trace; no injection/traversal/leak; `ENTRANCE_ID` hardcoded; single-tenant |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — delta is minimal (net +17 lines, mostly load-bearing comments); no over-engineering |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — rule compliance run by hand (see Rule Compliance section) |

**All received:** Yes (3 enabled returned; 6 disabled pre-filled as Skipped)
**Total findings:** 5 confirmed (0 Critical, 0 High, 2 Medium, 1 Low, + 2 [VERIFIED-gap] rolled into the Mediums), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

This is a re-review scoped to the **post-approval delta** (commit `1fca4a13`) on top of the already-approved `04d674dd`. The delta is 3 files, net +17 lines. The fix is behaviorally correct, verified live (164-8 gate now PASSES: PC descends `the_dropmouth→entrance→exp005.r1`), tests are GREEN, and it is wired into production. Five confirmed observations, none blocking.

**Data flow traced:** player movement descriptor → `SiteRegistry.resolve_descriptor` (substring filter over content-authored candidates, `registry.py:65`) → `SiteDescriptor` → `resolve_enter_site` (`movement.py:540`) → `load_map(entrance_id=site.entrance_node_id, site_id=site.site_id)` (parameterized Postgres, scoped by `(session_id, site_id)`) → `target` binding → `apply_world_patch(pc_region)` → `site_enter_span`. No player text reaches a node id, SQL fragment, or path (safe — [SEC] confirms).

**Observations (≥5):**
1. `[VERIFIED]` Dead-code diagnosis is airtight — `load_map` (`game/pg/dungeon.py:434`) sets `graph.entrance_id = entrance_id` (caller-passed) unconditionally, and the resolver passes `entrance_id=site.entrance_node_id`; the old `graph.entrance_id in graph.nodes` branch was reached only when `site.entrance_node_id not in graph.nodes`, so it was provably always-False. Fix keys off `ENTRANCE_ID` ("entrance", `seed_bootstrap.py:33`), the real persisted node. Complies with **No Silent Fallbacks** (loud `logger.warning` + real node; else raises). Evidence: `enter_site.py:63-77`, `dungeon.py:434`.
2. `[VERIFIED]` Loud-failure path preserved — `enter_site.py:73-77` still raises `SeamCrossingError(reason="no_site_entrance")` when neither the declared target nor `ENTRANCE_ID` is present; guarded by `test_enter_site_missing_entrance_node_raises`.
3. `[VERIFIED]` Production wiring — `resolve_enter_site` is consumed at `agents/subsystems/movement.py:540` and dispatched via the seam registry (`game/seams/registry.py:45` → `_REGISTRY["enter_site"]`). Non-test consumers confirmed; not a half-wired feature. Complies with **Verify Wiring, Not Just Existence**.
4. `[VERIFIED]` / `[TEST]` Test doubles now faithful — both `_LegacyEntranceStore` and `_StoreWithEntrance` echo `entrance_id=entrance_id`, mirroring the real `load_map`; the frontier-legacy test asserts the PC actually binds to `"entrance"` (`region_for` + `pc_regions`, `test_site_resolvers.py:174-176`), not merely no-raise — so the dead-fallback regression is RED on the faithful double. The changed tests are behavioral/fixture-driven, not source-text greps (complies with **No Source-Text Wiring Tests**). `[TEST]` gap: no test exercises a `bounded`-extent site through the fallback (ties to obs 5).
5. `[SILENT]` `[SEC]` `[RULE]` **[MEDIUM, non-blocking]** Extent-blind fallback (`enter_site.py:65`) — gated on `ENTRANCE_ID in graph.nodes`, not `site.extent == "frontier"`. Since `load_map` scopes nodes by `site_id`, a mis-fire requires a bounded site authored with `site_id == "frontier"` (== `DEFAULT_SITE_ID`); no validator forbids it. **Not reachable in current content** (frontier `site_id` used once — the frontier site itself), and the delta does not make any live behavior wrong. Confirmed (corroborated by silent-failure-hunter + security), **not dismissed** — recommend gating on `site.extent`. Per **No Silent Fallbacks** this is a latent gap, not a live violation, hence Medium.
6. `[SILENT]` **[MEDIUM, non-blocking]** OTEL discriminator gap (`enter_site.py:66`) — the fallback is visible only via `logger.warning`; `site_enter_span` carries no attribute separating fallback-bind from primary-bind. Maps to the **OTEL Observability Principle** → **not dismissed**. Downgraded to Medium with rationale: the fix's *success* IS OTEL-verifiable via the existing `site.enter` span — that is literally how 164-8's AC-2 was confirmed live — so the principle's core intent ("the GM panel can verify the fix is working") is met; the missing piece is a fallback *discriminator*, an enhancement to a firing span. Recommend `span.set_attribute("entrance_fallback", target != site.entrance_node_id)` + `SPAN_ROUTES` mirror.
7. `[DOC]` **[LOW, non-blocking]** Stale sibling-test docstring (`test_site_resolvers.py:185`) — the delta's rename orphaned the cross-reference and left the old `graph.entrance_id` mechanism described. comment-analyzer disabled; caught by hand.

**Remaining dispatch tags:** `[EDGE]` — subagent disabled; four paths enumerated by hand (target-present → primary bind; target-absent + entrance-present → fallback; target-absent + entrance-absent → loud raise; `dungeon_repository is None` → `no_site_store` raise), all covered by tests. `[TYPE]` — subagent disabled; no new type surface in the delta; `RegionGraph.entrance_id` is unvalidated free text (pre-existing, noted by [SILENT]); `ENTRANCE_ID` is a `str` constant. `[SIMPLE]` — subagent disabled; delta is the minimal correct change (net +17, mostly regression-guard comments); no over-engineering.

### Rule Compliance

Enumerated against every rule the delta touches (rule-checker disabled → done by hand):
- **No Silent Fallbacks** — fallback branch (`enter_site.py:65-77`): COMPLIANT for the firing case (loud `warning`, binds a REAL node, else raises loudly). LATENT MEDIUM gap: extent-blind guard could shadow the loud raise for a hypothetical `site_id="frontier"` bounded collision (obs 5) — flagged, not dismissed.
- **OTEL Observability Principle** — PARTIAL: the crossing is spanned and verifiable (`site_enter_span` fires with `to_region`/`extent`/`archetype`/`intent.*`), but the fallback-decision discriminator is absent (obs 6). Medium, not dismissed.
- **No Stubbing** — COMPLIANT: no placeholders/skeletons introduced.
- **Don't Reinvent / Wire Up What Exists** — COMPLIANT: reuses the existing `ENTRANCE_ID` constant and the existing span; wired to movement + seam registry.
- **Every Test Suite Needs a Wiring Test** — COMPLIANT: `tests/integration/test_seam_crossing_wiring.py` is the integration/wiring test.
- **No Source-Text Wiring Tests** — COMPLIANT: assertions are behavioral (region binding), not `read_text()` greps.

### Devil's Advocate

Argue the fix is broken. **Attack 1 — the collision teleport.** Author a bounded tavern in `road_warrior` with `site_id: "frontier"` before its interior materializes (Task 12 is not yet implemented per the resolver docstring). A player enters; `target = "frontier:entrance"` is absent from the graph, but the graph — scoped by `site_id="frontier"` — returns Sünden's persisted nodes including bare `"entrance"`, so the PC is teleported into an unrelated megadungeon's shaft-collar instead of getting the recoverable "interior has not yet formed" error. This is real (obs 5), but it requires a `site_id` collision that no authored content has and that the delta did not create the *possibility* of behaving-wrongly for any existing site. **Attack 2 — the invisible hot path.** Because frontier node-id namespacing is deferred to B4, this "single fallback" fires on *every* Sünden entry, permanently, and the GM panel cannot distinguish it from a primary bind (obs 6). A future regression that made the fallback bind the *wrong* legacy node would be OTEL-silent. Real, but the crossing itself is spanned, so a *total* failure (no crossing) is still caught (it was — the failed 164-8 run showed `site.enter_unresolved`). **Attack 3 — constant drift.** If someone changes `ENTRANCE_ID` in `seed_bootstrap.py` without a migration, persisted `"entrance"` nodes no longer match → fallback misses → loud `no_site_entrance` raise. That fails safe (loud), not silent. **Attack 4 — empty/huge/null.** Empty graph → `ENTRANCE_ID not in nodes` → raise (correct). `dungeon_repository is None` → `no_site_store` raise (correct). Concurrent entries → per-player `pc_region` patch, MP turns serialized (ADR-036), not delta-introduced. **Verdict of the advocate:** every reachable input today resolves correctly or fails loud; the two Mediums are a latent authoring-collision robustness gap and an observability discriminator — neither is live breakage, neither is a security issue, and error handling is present and loud. No Critical or High survives scrutiny.

**Error handling:** three fail-loud raises — `no_site_store` (`enter_site.py:42`), `no_site_entrance` (`:74`), plus `SerializationError` on corrupt payload in `load_map`. All recoverable, none strand the PC in a phantom node.

**Pattern observed:** loud-single-fallback keyed on a real persisted node (`enter_site.py:64-77`) — the intended shape of the No-Silent-Fallbacks rule.

**Handoff:** To SM (Vizzini) for finish-story. The two Medium improvements (extent-gate the fallback + OTEL discriminator) and the Low docstring fix are non-blocking; recommend folding the two `enter_site.py` hardenings into a small follow-up chore (or onto `164-9`, same subsystem) rather than blocking this verified fix.