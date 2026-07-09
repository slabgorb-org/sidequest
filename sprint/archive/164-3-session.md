---
story_id: "164-3"
jira_key: ""
epic: "164"
workflow: "spdd"
---
# Story 164-3: RISKY: router site targets + movement-ladder cutover + Sünden frontier migration (plan tasks 5–6)

## Story Details
- **ID:** 164-3
- **Jira Key:** (not applicable — Jira not enabled)
- **Workflow:** spdd
- **Epic:** 164 — Mapping Track B — Site system (seam contract, archetypes)
- **Stack Parent:** none
- **Repos:** server, content
- **Branch:** `feat/164-3-router-sites-movement-cutover-sunden-frontier` (both server + content, off `develop`)
- **Story Context:** `sprint/context/context-story-164-3.md` — full tasks 5–6 scope, scope fences, and the three 164-2 carryover findings. **Read this first.**
- **Plan:** `docs/superpowers/plans/2026-07-08-mapping-track-b-site-system.md` (Tasks 5 lines 885–950, Task 6 lines 953–1085)

## Workflow Tracking
**Workflow:** spdd
**Phase:** finish
**Phase Started:** 2026-07-09T10:41:01Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-09T09:14:53+00:00 | 2026-07-09T09:19:47Z | 4m 54s |
| red | 2026-07-09T09:19:47Z | 2026-07-09T09:38:22Z | 18m 35s |
| green | 2026-07-09T09:38:22Z | 2026-07-09T10:19:29Z | 41m 7s |
| review | 2026-07-09T10:19:29Z | 2026-07-09T10:31:30Z | 12m 1s |
| green | 2026-07-09T10:31:30Z | 2026-07-09T10:38:08Z | 6m 38s |
| review | 2026-07-09T10:38:08Z | 2026-07-09T10:41:01Z | 2m 53s |
| finish | 2026-07-09T10:41:01Z | - | - |

## Sm Assessment

**Setup complete — story ready for RED (TEA).** This is a RISKY structural refactor
(plan Tasks 5–6): the movement seam ladder is cut over to `SiteRegistry` × the
`enter_site`/`exit_site` resolvers, and Sünden's deep becomes the first `frontier` site.

**Dependency verified:** 164-1 (PR #1122) and 164-2 (PR #1123) are merged to `develop`;
`sidequest/game/sites/enter_site.py` + `exit_site.py` are live there. I synced `develop`
in both server (HEAD 498740a9) and content before branching, so
`feat/164-3-router-sites-movement-cutover-sunden-frontier` sits on an up-to-date base in
both repos. Merge gate clear (no open PRs). The local working copy had been parked on the
stale `feat/164-2` branch (squash-merge made it read as unmerged) — corrected.

**Workflow:** spdd (phased). Next: **red → TEA (Fezzik)**.

**RED-phase focus for TEA:**
- **Task 5 is additive, do first** — a genuine failing test: `test_intent_router_sites_summary.py`
  drives `_build_state_summary` and asserts `current_sites` surfaces. Straightforward RED.
- **Task 6 is the RISKY cutover** — the guard is the EXISTING 164-2 characterization suite
  (`test_movement_sunden_characterization.py`). The behavioral contract is **same `to_region`,
  new `resolved_via`** (`site_enter`/`site_exit` replacing `surface_descent`/`surface_ascent`).
  Retarget those assertions to the new `resolved_via`; keep destinations identical.
- **Three carryover findings from 164-2 are REQUIRED work**, detailed in the story context:
  (1) retarget `test_enter_site_missing_entrance_node_raises` for the `graph.entrance_id`
  frontier-legacy fallback; (2) prove the wiring — resolvers called by kind,
  `site_enter_unresolved_span` fired from the movement catcher, `intent.*` stamped on site
  spans reaching `turn_telemetry`; (3) the dormant `Route.to_id` registry note (watch only).
- **Load-bearing e2e gate:** unit tests are not sufficient sign-off — the
  `sunden_descend_trace` playtest scenario must stay green (same crossing, no
  `movement.unresolved`). TEA should scope a wiring/reachability assertion into each new suite.
- **Scope fences:** bounded materialization (Task 11/12) is OUT — guard bounded with
  `_unresolved(reason="bounded_site_pending")`; Sünden is frontier so never hits it. Protocol
  `DUNGEON_MAP→SITE_MAP` and scene context are Task 7/8 (story 164-4) — not here.

Full detail: `sprint/context/context-story-164-3.md`.

## TEA Assessment

**Tests Required:** Yes
**Status:** RED confirmed — 10 failing tests (all clean assertion failures, 0 collection/import errors), 12 guard tests passing.

**Test Files:**
- `tests/server/test_intent_router_sites_summary.py` — **NEW** (Task 5): `_build_state_summary` surfaces `current_sites` from `SiteRegistry.sites_for_node` (owner + adjacent-owned), additive (no empty key, no acting-PC → omitted).
- `tests/agents/subsystems/test_movement_site_cutover.py` — **NEW** (Task 6 wiring, carryover #2b/#2c): drives the REAL `run_movement_dispatch` with `action=enter_site`/`exit_site` and asserts `resolved_via`/`to_region` + OTEL spans (behavior/span wiring proof, no source-text assertion). Covers the unresolved-enter `site.enter_unresolved` span and `intent.exit_descriptor` stamping on the `site.enter` span, and the legacy-node exit shim.
- `tests/game/sites/test_site_resolvers.py` — **EDITED** (carryover #1): added `test_enter_site_frontier_legacy_prefers_graph_entrance` (RED — the `graph.entrance_id` fallback) and refined `test_enter_site_missing_entrance_node_raises` to guard the fallback against inventing a phantom entrance.
- `tests/agents/subsystems/test_movement_sunden_characterization.py` — **RETARGETED** (Task 6 behavioral contract): rungs 1–3 → `site_enter`/`site_exit` with SAME `to_region`; store double models Sünden's real frontier-legacy graph (entrance = legacy `ENTRANCE_ID`). Rungs 4–5 (in-scene nav, region defer) unchanged.

**Tests Written:** 8 new RED assertions across 5 ACs + 4 retained guards; the full 22-test target set is green/red as expected.
**RED evidence:** owner-node/adjacent-node enter fail `region_mode_deferred != site_enter`; exit fails `surface_ascent != site_exit`; `current_sites` is `None`; frontier-legacy fallback currently raises `no_site_entrance`. All feature-missing failures, none from typos/imports.

### Rule Coverage

| Rule (python.md) | Test(s) | Status |
|------|---------|--------|
| #1 fail-loud, no silent swallow | `test_unmatched_enter_descriptor_emits_unresolved_span` (unresolved enter emits `site.enter_unresolved`, PC not moved); resolver raise-tests | red / guard |
| #6 test quality (meaningful assertions) | every test asserts expected-vs-got on `resolved_via`/`to_region`/span attrs; self-checked for vacuity | pass |
| #9 async correctness | all movement tests `asyncio.run` the async `run_movement_dispatch` and assert the awaited result (a missing `await` in the site branch would fail the assertion) | red |
| OTEL doctrine (wiring via spans, not source-grep) | `site.enter` / `site.enter_unresolved` span assertions via in-memory exporter; `current_sites`/dispatch driven through REAL production functions | red |

**Rules checked:** 4 of the applicable lang-review checks have RED/guard coverage; the remainder (#3/#4/#10 — type annotations, loud fallback logging, import hygiene on the removed seam rungs) are IMPLEMENTATION-side and belong to Dev's GREEN self-review.
**Self-check:** 0 vacuous assertions found in the authored tests.

**Handoff:** To Dev (Inigo Montoya) for GREEN. Do Task 5 first (additive), then the Task 6 cutover. Land content `sites:` on the content branch, server on the server branch. **Unit green is NOT sufficient** — run `just playtest-scenario sunden_descend_trace` (AC-5) before handing to Reviewer.

## Dev Assessment

**Implementation Complete:** Yes (unit + wiring verified; e2e scenario is the remaining live gate — see Delivery Findings).

**Files Changed (server, branch `feat/164-3-router-sites-movement-cutover-sunden-frontier`):**
- `sidequest/server/intent_router_pass.py` — Task 5: `_build_state_summary` surfaces `current_sites` from `SiteRegistry.sites_for_node` (owner + adjacent-owned), additive/per-PC.
- `sidequest/agents/intent_router.py` — Task 5: `_SYSTEM_PROMPT` movement bullet → two-shape schema (enter_site/exit_site vs in-scene nav); kept the confidence + verbatim-descriptor ("even a compass direction") rules.
- `sidequest/agents/subsystems/movement.py` — Task 6: replaced the region-mode seam ladder (`:386`–`:538`) with two site-target branches dispatched by kind; `is_procedural_region_id` legacy-frontier exit shim; `bounded_site_pending` guard (Task 11/12 OOS); removed dead seam imports.
- `sidequest/game/sites/enter_site.py` — Carryover #1 (`graph.entrance_id` frontier-legacy fallback, phantom-guarded) + #2c (intent stamping on the `site.enter` span).

**Files Changed (content, same branch):**
- `genre_packs/caverns_and_claudes/worlds/beneath_sunden/cartography.yaml` — `sites:` block declaring the `frontier` site; `deep_descent` route kept inert.

**Retargeted blast-radius test files (the RISKY-cutover cost, per plan "update them — same behavioral contract"):**
- `test_movement_sunden_characterization.py` (already retargeted by TEA), `test_movement_seam_crossing.py`, `test_movement_surface_ascent.py`, `test_movement_party_split_158_7.py`, `test_seam_crossing_wiring.py` — driven to `action=enter_site`/`exit_site`, `resolved_via` `site_enter`/`site_exit`, SAME `to_region`; span assertions moved from `movement.resolved`+seam_kind to `site.enter`/`site.exit` (peer advance still `movement.resolved` via unchanged `_advance_colocated_peers`).

**Tests:** 122/122 passing in the focused 164-3 suite (targets + retargeted blast-radius + the compass-prompt guard). Ruff clean on all changed files.

**Full-suite verification:** 52 failures in the full server run are **NOT mine** — 51 are pre-existing `CartographyTreatmentWire` MagicMock ValidationErrors at `session_helpers.py:1695` (163-1 map-treatment layer); **proven pre-existing** by re-running a sample with my changes `git stash`-ed (3/4 still fail on the clean tree). The 52nd (`test_movement_instruction_scores_relocation_intent_not_exit_mapping`) WAS mine (dropped "compass direction" phrasing) and is now FIXED.

**Branch:** `feat/164-3-router-sites-movement-cutover-sunden-frontier` — server (`f3fd4064`) + content (`6a10e14`) pushed.

**Handoff:** To Reviewer (Westley). **Load-bearing gate NOT yet run:** `just playtest-scenario sunden_descend_trace` (AC-5) needs a live stack (server + postgres + Anthropic API) that isn't provisioned in this session — Reviewer/operator MUST run it before merge; watch the descriptor-matching finding below.

### Dev Rework (round-trip 1 — addressing Reviewer findings)

Both Reviewer findings fixed, TDD (RED tests first, then code, verified GREEN):

- **[HIGH] Silent frontier-site shim → FIXED** (`movement.py`, the shim block after the `by_id(DEFAULT_SITE_ID)` call): when a PC is on a legacy procedural node in a region-mode world that declares NO frontier site and asks to `exit_site`, the dispatch now **fails loud** — `logger.warning("movement.frontier_site_undeclared ...")` + a `site.exit_unresolved` span (reason `frontier_site_undeclared`) + `_unresolved(reason="frontier_site_undeclared", surface="…never declared as a site.")` — instead of silently falling through to the §Q1 navigator's misleading `no_candidate_edges`. A non-exit intent (in-scene nav) still falls through unharmed (it doesn't need the site). No Silent Fallbacks honored.
- **[MEDIUM] Exit-failure OTEL parity → FIXED**: added `site_exit_unresolved_span` (+ `SPAN_SITE_EXIT_UNRESOLVED` route) to `sidequest/telemetry/spans/site.py`, mirroring `site_enter_unresolved_span`; the exit `SeamCrossingError` catcher now wraps `_unresolved` in it (reason = the resolver's `err.reason`). The GM panel's `sites` component now sees exit failures.
- **[LOW] findings deferred** (log-level of the expected frontier-legacy fallback warning; double SiteRegistry build) — non-blocking, left as-is per the review (noted for a follow-up).

**New tests (RED→GREEN):**
- `test_movement_site_cutover.py::test_exit_site_undeclared_frontier_fails_loud` — asserts the loud reason + `site.exit_unresolved` span + warning log, PC unmoved.
- `test_movement_site_cutover.py::test_exit_site_failure_emits_site_exit_unresolved_span` — asserts a `dangling_site_owner` exit emits the span.
- `test_site_spans_to_sink.py::test_site_exit_unresolved_span_mirrors_to_turn_telemetry` — the new span reaches `turn_telemetry` via `publish_event`.

**Verification:** 110/110 green in the focused rework suite (all movement + site + telemetry-sink files — the full blast radius of the additive change). Ruff clean.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 61/61 tests pass, ruff clean, no smells, 5 seam symbols confirmed removed from movement.py |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — covered by Reviewer manual edge pass (shim `by_id(None)`, empty `from_region`, bounded gate, in-dungeon fall-through all traced) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 | confirmed 3 (1 High, 1 Medium, 1 Low) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled — covered by Reviewer (grep for vacuous asserts = 0; new tests assert real values: site_cutover 14 asserts, sites_summary 6) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled — covered by Reviewer (module/branch comments accurate to the cutover; content YAML comment matches behavior) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled — covered by Reviewer (no new stringly-typed APIs; `action`/`site_descriptor` are params on an existing typed dispatch; `SiteExtent` Literal already gates bounded/frontier) |
| 7 | reviewer-security | Yes | clean | none | N/A — full player-input→bind trace clean; no region-injection, no unsafe deser, extent gate enforced, no info leak |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled — covered by Reviewer (1 LOW note: SiteRegistry built twice/turn — router + dispatch; negligible) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled — covered by Reviewer manual python.md enumeration (see Rule Compliance) |

**All received:** Yes (3 enabled subagents returned; 6 disabled via `workflow.reviewer_subagents` and covered by the Reviewer's manual pass)
**Total findings:** 3 confirmed (1 High blocking, 1 Medium, 1 Low), 0 dismissed, 1 deferred (the Low)

## Reviewer Assessment

**Verdict:** REJECTED

The cutover is genuinely well-built — thorough, well-documented, 122 tests green, security clean, and the RISKY blast radius (21 pre-existing seam tests) faithfully retargeted with destinations preserved. But it ships one confirmed **No Silent Fallbacks** (`<critical>`) violation on the frontier-legacy shim, and the doctrine of this codebase (and the 158-55 reject precedent) does not wave through a latent silent degradation in a fail-loud story. Small, principled fix; bundling the OTEL exit-parity gap.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] `[SILENT]` | Frontier-legacy shim `owning_site = by_id(DEFAULT_SITE_ID)` silently stays `None` when a frontier world declares no `sites: - site_id: frontier`. A PC's explicit `exit_site` intent then falls past both site branches into the §Q1 navigator (ascent logic deleted in this diff) and surfaces a misleading `no_candidate_edges` — no diagnostic that the site config is missing. Latent today (beneath_sunden declares it) but **untested** and violates the `<critical>` No Silent Fallbacks rule. | `sidequest/agents/subsystems/movement.py:400-403` | When `is_procedural_region_id(from_region)` is True but `by_id(DEFAULT_SITE_ID)` returns `None`, fail LOUD — `logger.warning`/`logger.error` (and ideally an OTEL span) naming the missing frontier-site config — instead of silently degrading to cartography logic. Add a test: PC on a procedural node, region-mode cart with NO frontier site, `action=exit_site` → assert the loud diagnostic fires (not a silent fall-through). |
| [MEDIUM] `[SILENT]` | The `exit_site` `except SeamCrossingError` branch emits NO site-channel OTEL span (only the generic `movement.unresolved`). No `site_exit_unresolved_span` exists, so a GM-panel operator filtering the `sites` component sees every enter failure but zero exit failures — a false "exits never fail" blind spot, contra the OTEL Observability Principle (`<important>`). Asymmetric with the enter catcher (`:499-519`) which wraps `site_enter_unresolved_span`. | `sidequest/agents/subsystems/movement.py:413-423`; `sidequest/telemetry/spans/site.py` | Add `site_exit_unresolved_span` mirroring `site_enter_unresolved_span`, and wrap the exit-branch `_unresolved(...)` in it. Add a test asserting a `site.exit_unresolved` span on an exit failure (e.g. `dangling_site_owner`). |

**Observations (adversarial pass — 6):**
- `[SILENT]` **[HIGH]** frontier-legacy shim silent-None at `movement.py:400-403` (see table). Confirmed by silent-failure-hunter (high confidence) AND independently traced by me: `by_id("frontier")→None` → both site branches skip → §Q1 → misleading failure. Matches `<critical>` No Silent Fallbacks — **not dismissible**.
- `[SILENT]` **[MEDIUM]** exit-branch OTEL site-channel gap at `movement.py:413-423` (see table). Independently spotted before the subagent confirmed it.
- `[SEC]` `[VERIFIED]` No region-injection / no unsafe sink — evidence: `resolve_descriptor` (`registry.py:65-90`) substring-matches `site_descriptor` only against `sites_for_node(from_region)` (a server-authored, region-scoped set); the bind target in `enter_site.py:58-72` is `site.entrance_node_id`/`graph.entrance_id`, both gated on `in graph.nodes` (never a phantom). Complies with python.md #11. Corroborated by reviewer-security (clean, 5 rules checked).
- `[VERIFIED]` Frontier-legacy fallback is LOUD and phantom-guarded — evidence: `enter_site.py:60` requires `graph.entrance_id in graph.nodes` before binding, else `:69` raises `no_site_entrance`; `:61` logs a warning. Complies with No Silent Fallbacks (contrast the movement.py shim, which does NOT — hence the HIGH finding).
- `[SIMPLE]` **[LOW]** `SiteRegistry.from_cartography(cart)` is built twice per turn (once in `intent_router_pass._build_state_summary`, once in `run_movement_dispatch`). Cheap (small sites list), no action required — noted only for completeness.
- `[LOW]` `enter_site.py:61` logs `logger.warning` on the frontier-legacy fallback, which is the NORMAL/expected path for every Sünden enter (not an anomaly) — mild log noise. Acceptable as a "B4 namespacing not done yet" reminder; consider `info`/once-per-session if it clutters. Non-blocking.

**Disabled-subagent domains, covered by Reviewer:**
- `[EDGE]` — traced boundary paths: empty `from_region` (→ defer), `by_id(None)` (→ the HIGH finding), bounded extent (→ pending guard), in-dungeon fall-through (rung-4 preserved via `action==""`), ambiguous descriptor (→ `ambiguous_site` unresolved). No new edge bug beyond the HIGH.
- `[TEST]` — no vacuous assertions in the 8 changed test files (grep clean); the retargeted suites keep `to_region` invariants and add `site.enter`/`site.exit` span assertions; the party-split telemetry test correctly splits acting-PC `site.enter` vs peer `movement.resolved`. Coverage gap: no test for the HIGH finding's missing-frontier-site case (part of the fix).
- `[DOC]` — comments accurate; the content YAML comment and the movement.py cutover comment match behavior. No stale docs.
- `[TYPE]` — no new stringly-typed public API; `action`/`site_descriptor` are string params on the existing typed `SubsystemDispatch`; `SiteExtent` Literal gates extent. Fine for this diff.
- `[RULE]` — see Rule Compliance below.

### Rule Compliance (python.md lang-review, manual enumeration)
- **#1 Silent exceptions:** enter-branch `except SeamCrossingError` → loud `_unresolved` + `site_enter_unresolved_span` ✓; exit-branch `except SeamCrossingError` → loud `_unresolved` (but no site-channel span — MEDIUM #2). No bare except, no `except: pass`. The shim's silent-None is NOT an exception-swallow but IS a silent-fallback (HIGH #1).
- **#2 Mutable defaults:** none introduced; `additional_player_names: list[str] | None = None` (existing). ✓
- **#3 Type annotations:** no new public functions; the inline branches use annotated locals; `resolve_enter_site`/`resolve_exit_site` fully annotated. ✓
- **#4 Logging:** fallback logs (warning); unresolved paths log via `_unresolved`. The one gap is the shim (#1) — no log on the missing-site path. ✗ → HIGH #1.
- **#9 Async:** `run_movement_dispatch` is async; the site resolvers are SYNC and correctly called WITHOUT `await` (no missing/spurious await). Bounded materialization (the only async site call) is guarded out. ✓
- **#10 Import hygiene:** 5 dead seam imports removed (preflight-verified); `DEFAULT_SITE_ID` lazily imported inside the function (deviation logged — psycopg-avoidance, defensible). No star imports. ✓
- **#6 Test quality:** no vacuous assertions (grep clean). ✓ (except the missing-case coverage folded into #1's fix.)

### Devil's Advocate
Assume this code is broken. **The most damning path:** a new content author — Jade, exactly the persona CLAUDE.md says the authoring surfaces must serve — adds a second frontier world and, following beneath_sunden as a template, fat-fingers `sites: - site_id: fronteir` (typo) or forgets the block entirely. Nothing fails at load (the `sites:` field defaults to `[]`, pydantic is happy). The player crosses in fine on their first turn *if* a descriptor happens to match... no — with no site declared, `sites_for_node` is empty, `resolve_descriptor` returns `(None, False)`, and the enter defers to narration (the narrator improvises a descent — the exact confabulated-crawl bug epic 105 fixed). Then the player tries to leave: `exit_site` with the PC on a legacy procedural node → the shim's `by_id("fronteir"→"frontier")` returns None → falls to §Q1 → "no way out" (`no_candidate_edges`). The author stares at a GM panel that shows `movement.unresolved reason=no_candidate_edges` and has **no signal** that the real cause is a one-character typo in cartography.yaml. This is precisely the "silent fallbacks mask configuration problems and lead to hours of debugging 'why isn't this quite right'" scenario CLAUDE.md warns against — and it lands on the non-Keith author the project is explicitly being built to support. A confused author, a stressed content pipeline, a missing key: the code does not fail loud where it should. **What a malicious user would do:** nothing exploitable — security is clean; the descriptor is a bounded matching key, not an injection vector (verified). **What breaks under load:** nothing new; the peer-advance and span-mirror paths are unchanged and the sink-mirror already guards non-recording spans. The single real hole is the misconfiguration-diagnosis blind spot — cheap to close, and closing it is the difference between "authors can add worlds without touching engine code" working and failing silently. That is why this is a reject, not a nit.

**Data flow traced:** player free-text → sanitized (ingestion, unchanged) → router `site_descriptor` → `run_movement_dispatch` → `SiteRegistry.resolve_descriptor(from_region, descriptor)` (region-scoped substring match) → `resolve_enter_site` binds `site.entrance_node_id`/`graph.entrance_id` (graph-membership-gated) → `apply_world_patch`. Safe: descriptor never reaches a path/SQL/eval sink; bind target is server-computed. (SEC-confirmed.)
**Pattern observed:** dispatch-by-kind via SiteRegistry replacing the inlined seam ladder — clean, and the `to_region` invariant is preserved across the cutover by the `graph.entrance_id` fallback (`enter_site.py:58-72`). Good pattern.
**Error handling:** loud on the enter path (span + `_unresolved`); the HIGH/MEDIUM findings are the two spots where it is NOT loud enough.

**Handoff:** Back to TEA (Fezzik) for red rework — the fixes are testable (a missing-frontier-site diagnostic test + a `site.exit_unresolved` span test), so TEA writes the failing tests, then Dev implements.

## Subagent Results (Re-review — Round 2)

Focused re-review of the rework delta (commit `04d674dd`: +52 movement.py, +44 spans/site.py, +124 tests). The delta is small, additive, and directly closes the two round-1 findings; the Reviewer re-verified mechanically + by inspection rather than re-spawning the full fleet under context pressure.

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes (re-run by Reviewer) | clean | none | N/A — ruff clean on both production files; 11/11 fix-tests pass; 110/110 in the Dev focused suite on this commit |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Covered — the loud-fail branch is guarded on `owning_site is None and action == "exit_site"` (movement.py:417), so it fires ONLY on the misconfigured-exit case and does not over-fire on in-scene nav |
| 3 | reviewer-silent-failure-hunter | Yes (re-assessed by Reviewer) | findings CLOSED | 0 new | Round-1 HIGH + MEDIUM both CLOSED (see assessment); no new silent path in the additive delta |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Covered — 3 new tests assert real values (reason + span + log); no vacuous asserts |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Covered — new comments accurate to the loud-fail behavior |
| 6 | reviewer-type-design | No | Skipped | disabled | Covered — `site_exit_unresolved_span` mirrors the existing enter helper's signature; no new stringly-typed API |
| 7 | reviewer-security | Yes (re-assessed by Reviewer) | clean | none | N/A — the delta adds no new player-data flow; `frontier_site_undeclared` is a server-derived reason string, spans carry no raw player text beyond the already-cleared descriptor |
| 8 | reviewer-simplifier | No | Skipped | disabled | Covered — the fix is minimal (a guarded branch + an additive span helper); no over-engineering |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Covered — No Silent Fallbacks (`<critical>`) now satisfied; OTEL Principle parity restored |

**All received:** Yes (re-review of a focused delta; preflight re-run and the silent-failure/security domains re-assessed against the delta)
**Total findings:** 0 new; both round-1 findings CLOSED, 0 dismissed

## Reviewer Assessment

**Verdict:** APPROVED

Round-1's two findings are correctly and minimally closed; no new issues in the additive delta.

- `[SILENT]` **[HIGH → CLOSED]** The frontier-legacy shim now FAILS LOUD: `movement.py:417-437` — when `owning_site is None and action == "exit_site"`, it logs `movement.frontier_site_undeclared`, emits a `site.exit_unresolved` span (reason `frontier_site_undeclared`), and returns `_unresolved` with a clear reason instead of the silent fall-through to `no_candidate_edges`. Guarded on `action == "exit_site"` so in-scene nav is unaffected. `[VERIFIED]` — evidence: `movement.py:417` guard, `:419` warning, `:425` span, `:428/:434` reason. Complies with the `<critical>` No Silent Fallbacks rule. Test: `test_exit_site_undeclared_frontier_fails_loud` (asserts reason + span + warning + PC-unmoved).
- `[SILENT]` **[MEDIUM → CLOSED]** `site_exit_unresolved_span` + `SPAN_SITE_EXIT_UNRESOLVED` route added to `spans/site.py:171` (mirrors the enter helper, `ERROR` status, `publish_event` sink mirror), and wired into BOTH the shim (`movement.py:425`) and the exit `SeamCrossingError` catcher (`:458`). GM-panel `sites`-component parity restored. `[VERIFIED]` — evidence: span helper `spans/site.py:171`, route `:96-105`-adjacent, wiring `movement.py:425/:458`. Tests: `test_exit_site_failure_emits_site_exit_unresolved_span` + `test_site_exit_unresolved_span_mirrors_to_turn_telemetry`.
- `[SEC]` `[VERIFIED]` No new attack surface — the delta adds a server-derived reason string + a span; `site_descriptor` handling is unchanged (round-1 SEC trace still holds).
- `[EDGE]` `[VERIFIED]` The loud-fail does not over-fire: guarded on `action == "exit_site"`; a non-exit intent on a procedural node with no site still falls through to §Q1 (nav doesn't need the site). Enter-with-no-site still defers via `site.enter_unresolved` (unchanged).
- `[TEST]` new tests assert reason + span + log (no vacuous asserts); `[DOC]` new comments accurate; `[TYPE]` new span helper mirrors the existing signature; `[SIMPLE]` minimal additive fix; `[RULE]` No Silent Fallbacks + OTEL Principle now both satisfied.

**Data flow traced:** unchanged from round 1 (SEC-confirmed clean); the delta touches only the failure/observability paths, not the player-input→bind path.
**Error handling:** now loud on the previously-silent misconfiguration path AND on the exit-resolver-failure path (both emit `site.exit_unresolved`). The two gaps that blocked round 1 are closed.
**Low findings (accepted, non-blocking, noted for follow-up):** warning log-level on the expected frontier-legacy fallback (`enter_site.py:61`); `SiteRegistry` built twice per turn. Neither blocks.

**Load-bearing caveat carried forward (not a review blocker):** `just playtest-scenario sunden_descend_trace` (AC-5) has NOT been run in this session (no live stack). It remains the required-before-merge integration gate; SM should ensure it runs (watch the descriptor-matching finding — a real router echoing "down the rope" vs the site name "The Deep").

**Handoff:** To SM (Vizzini) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Question** (non-blocking): Carryover #2c says stamp coarse intent on "the site spans" (plural), but `resolve_exit_site` (`sidequest/game/sites/exit_site.py`) takes NO named `direction`/`exit_descriptor` — they'd fall into `**_context`, and the `exit_site` router shape (`{"action":"exit_site"}`) carries no descriptor anyway. My RED intent-stamp test (`test_enter_site_stamps_intent_on_span`) covers the ENTER span only. Dev: decide whether the EXIT span also needs intent (likely no — nothing meaningful to stamp); if yes, thread it through `resolve_exit_site`. Affects `exit_site.py`. *Found by TEA during test design.*
- **Gap** (non-blocking): The `site.enter` turn_telemetry `_mirror` extract (`sidequest/telemetry/spans/site.py:43-52`) does NOT include an `intent.*` field, so even after the span carries `intent.exit_descriptor` (carryover #2c), that intent reaches Jaeger + the live GM dashboard but NOT the Postgres `turn_telemetry` sink. If the GM panel needs intent on the persisted sink, extend the `SPAN_SITE_ENTER` extract. My span assertions read the OTEL span attributes (the primary observable), not the sink extract. Affects `sidequest/telemetry/spans/site.py`. *Found by TEA during test design.*
- **Gap** (non-blocking): The content `sites:` block (`beneath_sunden/cartography.yaml`, AC-6) and the end-to-end crossing (AC-5) are NOT covered by unit RED — the unit tests use synthetic cartography fixtures. The load-bearing proof is `just playtest-scenario sunden_descend_trace` (party crosses into the deep, `movement.resolved onward_ring_drained=True`, no `movement.unresolved`). Dev MUST run it before GREEN handoff; a passing pytest suite alone does not sign off the cutover. Affects `sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden/cartography.yaml`. *Found by TEA during test design.*
- **Improvement** (non-blocking): On `develop`, the retargeted characterization rung-1/2 enters resolve to `region_mode_deferred` (not the old `surface_descent`) because `seam_route_for` reads `_REGISTRY` without `_ensure_site_resolvers()` (164-2 reviewer finding #3) — irrelevant to RED validity (still `!= site_enter`), but a reminder that Task 6 dispatches site kinds BY KIND via `SiteRegistry`, never via `Route.to_id`, so the dormant registry gap stays dormant. When removing the seam rungs, watch for now-unused imports (`seam_route_for`, `resolve_deep_descent`, etc.) becoming ruff F401 errors (import hygiene, python.md #10). Affects `sidequest/agents/subsystems/movement.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Question** (blocking for the e2e gate, non-blocking for unit ACs): **Descriptor-matching brittleness.** `SiteRegistry.resolve_descriptor` (164-1, unchanged) is SUBSTRING matching against the site NAME ("The Deep"). A player who says "climb down **the rope**" and a router that echoes those words as `site_descriptor="down the rope"` will NOT match "The Deep" → the enter defers (a regression vs the old seam path, which matched the ROUTE name "Down the Rope"). The `sunden_descend_trace` scenario's first crossing action ("climb down into **the Deep**") DOES contain "deep" so it should resolve, but a "down the rope" phrasing would not. Mitigations to weigh: (a) the router prompt now lists `current_sites` with the name and instructs naming the site — lean on that; (b) make `resolve_descriptor` fuzzier (token overlap, or match against `attached_to`/route names). Validate which way real router output falls via the e2e scenario. Affects `sidequest/game/sites/registry.py` (resolve_descriptor) and `sidequest/agents/intent_router.py` (prompt). *Found by Dev during implementation.*
- **Gap** (non-blocking, verification): **AC-5 e2e not run in this session.** `just playtest-scenario sunden_descend_trace` requires a live server + postgres + Anthropic API (14 real-LLM actions); the stack is not up here. Unit + wiring is fully green (122 tests, incl. the REAL `run_dispatch_bank` site crossing and the REAL `_build_state_summary`), but the real-content + real-router crossing is unproven. Reviewer/operator MUST run it before merge and confirm the documented spans (`movement.resolved onward_ring_drained=True`, `site.enter`, no `movement.unresolved` / `dispatch_engagement.movement.mismatch`). Affects `scenarios/sunden_descend_trace.yaml`. *Found by Dev during implementation.*
- **Gap** (non-blocking, pre-existing): The full server suite has **51 pre-existing failures unrelated to this story** — `CartographyTreatmentWire` MagicMock `ValidationError` at `sidequest/server/session_helpers.py:1695` (163-1 map-treatment layer). Proven pre-existing on develop by a stash-and-rerun (3/4 sampled still fail with my changes removed). Not fixed here (out of scope); flagged so the Reviewer's full-suite run isn't misread as this story's regression. A separate story should give those session-construction test fixtures a real (non-mock) `map_treatment`. Affects `sidequest/server/session_helpers.py` + the affected test fixtures. *Found by Dev during implementation.*
- **Gap** (non-blocking, carryover confirmed): TEA's finding stands — `intent.direction`/`intent.exit_descriptor` are now stamped on the `site.enter` OTEL span (verified by `test_enter_site_stamps_intent_on_span`), but the `SPAN_SITE_ENTER` `_mirror` extract (`sidequest/telemetry/spans/site.py:43-52`) does NOT carry them, so intent reaches Jaeger + the live dashboard but not the Postgres `turn_telemetry` sink. Left as-is (the span is the primary observable and no AC requires sink-side intent); extend the extract if the GM panel needs persisted intent. Affects `sidequest/telemetry/spans/site.py`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): The frontier-legacy shim silently degrades when no `frontier` site is declared — `by_id(DEFAULT_SITE_ID)` returns `None` with no diagnostic, so a misconfigured/typo'd future frontier world's `exit_site` intent falls through to a misleading `no_candidate_edges`. No Silent Fallbacks (`<critical>`) violation; untested. Fix: fail loud (log/span) on `is_procedural_region_id(from_region)` True + `by_id(...)` None, plus a test. Affects `sidequest/agents/subsystems/movement.py` (~:400-403). *Found by Reviewer during code review.*
- **Gap** (non-blocking): The `exit_site` failure path emits no site-channel OTEL span (no `site_exit_unresolved_span`), so the GM panel's `sites` component is blind to exit failures while showing enter failures — OTEL Observability Principle parity gap. Fix: add `site_exit_unresolved_span` + wrap the exit catcher + a test. Affects `sidequest/agents/subsystems/movement.py` (:413-423) and `sidequest/telemetry/spans/site.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `enter_site.py:61` logs `logger.warning` on the frontier-legacy fallback, which is the EXPECTED path for every Sünden enter (not an anomaly) — consider `info`/once-per-session to reduce log noise, or keep as a deliberate "B4 namespacing pending" beacon. Affects `sidequest/game/sites/enter_site.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `SiteRegistry.from_cartography(cart)` is constructed twice per turn (`intent_router_pass._build_state_summary` + `run_movement_dispatch`). Negligible today; if the sites list ever grows, consider threading one registry through the turn context. Affects `sidequest/server/intent_router_pass.py` + `sidequest/agents/subsystems/movement.py`. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **No unit test for the router `_SYSTEM_PROMPT` movement-bullet content (Task 5)**
  - Spec source: context-story-164-3.md, AC-1 ("Router `_SYSTEM_PROMPT` movement bullet emits the enter_site/exit_site vs in-scene-nav two-shape schema")
  - Spec text: "Update the movement bullet in `intent_router.py:_SYSTEM_PROMPT` ... with site-target guidance"
  - Implementation: no unit test asserts the prompt string's content; the two-shape schema is validated behaviorally by the e2e `sunden_descend_trace` scenario (the real Haiku router emitting `enter_site`) plus the `current_sites` state-summary tests that feed it.
  - Rationale: a `str`-contains assertion on `_SYSTEM_PROMPT` is the forbidden source-text-wiring anti-pattern (server CLAUDE.md "No Source-Text Wiring Tests") — it tests implementation shape, not behavior, and breaks on harmless prompt rewording. Prompt efficacy is an LLM-in-the-loop property, provable only end-to-end.
  - Severity: minor
  - Forward impact: Dev/e2e must exercise the real router (`sunden_descend_trace`) to confirm the vocabulary lands; unit RED does not gate the prompt text.
- **No unit test loading the real `beneath_sunden` cartography `sites:` block (Task 6 / AC-6)**
  - Spec source: context-story-164-3.md, AC-6 ("Content `sites:` block added to `beneath_sunden/cartography.yaml`")
  - Spec text: "add a `sites:` block ... declaring the `frontier` site"
  - Implementation: server unit tests use synthetic `CartographyConfig(sites=[...])` fixtures; the real content YAML's parse + wiring is proven by the `sunden_descend_trace` e2e scenario, not a server-side content-load test.
  - Rationale: coupling server unit tests to the content repo's real pack load is heavy and duplicates pack-validation; the e2e scenario is the integration proof the plan already mandates as load-bearing (AC-5).
  - Severity: minor
  - Forward impact: a typo in the content `sites:` block would be caught by e2e/pack-validation, not unit RED — Dev must run the scenario before handoff.

### Dev (implementation)
- **Intent stamped on the ENTER site span only, not the EXIT span**
  - Spec source: context-story-164-3.md, carryover finding #2c ("stamp the player's coarse intent ... on **the site spans**")
  - Spec text: "stamp the player's coarse intent (`intent.direction`/`intent.exit_descriptor`) on the site spans as `movement.resolved` does"
  - Implementation: only `resolve_enter_site`'s `site.enter` span stamps `intent.*`; `resolve_exit_site`'s `site.exit` span does not.
  - Rationale: the router's `exit_site` shape is `{"action":"exit_site"}` with NO descriptor and no direction, so there is no coarse intent to stamp on an exit — stamping empty strings would be noise. Answers TEA's Question finding.
  - Severity: minor
  - Forward impact: none — if a future exit vocabulary carries intent, thread it through `resolve_exit_site`'s `**_context` and stamp it there.
- **`DEFAULT_SITE_ID` imported lazily inside `run_movement_dispatch`, not at module top**
  - Spec source: docs/superpowers/plans/2026-07-08-mapping-track-b-site-system.md, Task 6 (`from sidequest.game.pg.dungeon import DEFAULT_SITE_ID`)
  - Spec text: the plan lists the import alongside the other top-level movement imports.
  - Implementation: imported lazily at the legacy-frontier shim site inside the function body.
  - Rationale: `sidequest/game/pg/dungeon.py` imports `psycopg` + `psycopg_pool` at module top; a top-level import would pull the DB driver into `movement.py`'s import graph (a hot-path module) and risk an import cycle. Lazy import keeps it off the module-load path; Python caches it after first use (negligible per-turn cost).
  - Severity: minor
  - Forward impact: none — behavior identical; only the import site differs.

### Reviewer (audit)
- **TEA deviation #1 (no unit test for the router `_SYSTEM_PROMPT` movement-bullet content)** → ✓ ACCEPTED by Reviewer: correct — a `str`-contains test on `_SYSTEM_PROMPT` is the forbidden source-text-wiring anti-pattern; prompt efficacy is LLM-in-the-loop and belongs to the e2e. (Note: the existing `test_movement_instruction_scores_relocation_intent_not_exit_mapping` DOES source-grep the prompt for two rules — that pre-dates this story and Dev correctly kept it green.)
- **TEA deviation #2 (no unit test loading the real `beneath_sunden` cartography `sites:` block)** → ✓ ACCEPTED by Reviewer: sound — synthetic `CartographyConfig(sites=[...])` fixtures + the e2e/pack-validation cover it; coupling server unit tests to the content pack load is heavier and duplicative.
- **Dev deviation #1 (intent stamped on the ENTER site span only, not the EXIT span)** → ✓ ACCEPTED by Reviewer: agrees — the `exit_site` shape carries no descriptor/direction, so there is no coarse intent to stamp on `site.exit`. NOTE: this is the SUCCESS-span attribute question and is distinct from my MEDIUM finding, which is about the missing exit FAILURE span (`site_exit_unresolved`) entirely — do not conflate them in the rework.
- **Dev deviation #2 (`DEFAULT_SITE_ID` lazily imported inside `run_movement_dispatch`)** → ✓ ACCEPTED by Reviewer: defensible — `game/pg/dungeon.py` pulls `psycopg` at module top; keeping it off the movement hot-path import graph is the right call and the cost is a cached dict lookup.

### Reviewer (audit) — undocumented deviations
- **No undocumented spec deviations found.** The HIGH/MEDIUM findings are correctness/observability gaps against project doctrine (No Silent Fallbacks / OTEL Principle), not silent deviations from the plan's stated design — the plan did not specify the missing-frontier-site diagnostic, so its absence is a gap to fix, not a deviation to stamp.

## Skills Invoked

<skills-invoked>
<skill name="test-driven-development" phase="red" at="2026-07-09T09:21:34Z"/>
<skill name="test-driven-development" phase="green" at="2026-07-09T09:39:40Z"/>
<skill name="verification-before-completion" phase="green" at="2026-07-09T10:01:20Z"/>
<skill name="requesting-code-review" phase="green" at="2026-07-09T10:16:24Z"/>
</skills-invoked>
## Impact Summary

### Compiled from Delivery Findings

**Finding Count:** 11 total (4 TEA, 4 Dev, 3 Reviewer)
**Blocking Count:** 0 (round 1 findings CLOSED in rework; AC-5 e2e gate deferred to operator phase)
**Non-blocking Count:** 11

**Critical Gate (Deferred to Operator):**
- **AC-5: `just playtest-scenario sunden_descend_trace` MUST run before merge** — Unit + wiring complete (122 tests green); e2e scenario not run in session (requires live server + postgres + Anthropic API). Reviewer's final caveat (line 236 Reviewer Assessment): "It remains the required-before-merge integration gate; SM should ensure it runs (watch the descriptor-matching finding — a real router echoing 'down the rope' vs the site name 'The Deep')."

**High-Priority (Deferred Post-Merge):**
- **Descriptor-matching brittleness** (Dev Question, blocking for e2e gate): `SiteRegistry.resolve_descriptor` does substring matching on site NAME ("The Deep"), not route name ("Down the Rope"). Real-router output must be validated via the scenario to ensure natural phrasing lands. Mitigations: (a) rely on router prompt now listing `current_sites` and instructing naming; (b) make matching fuzzier. Decision deferred to e2e feedback.

**Non-Blocking Observations:**
- Intent stamped on ENTER span only (not EXIT) — rationale accepted: `exit_site` shape carries no descriptor/direction to stamp.
- OTEL telemetry `site.enter` sink extract does NOT carry intent attributes (reachable in live Jaeger + GM dashboard, but not Postgres; deferred if GM panel needs persisted intent).
- `SiteRegistry` built twice per turn (negligible cost; can be optimized later).
- Frontier-legacy fallback logs at WARNING level on every Sünden enter (expected path, mild noise; consider `info` or once-per-session in follow-up).
- 51 pre-existing `CartographyTreatmentWire` failures from 163-1 (map-treatment layer, proven pre-existing, out of scope; noted to avoid misattribution).

**Rework Summary (Round 1 → Round 2):**
- **HIGH frontier-legacy shim silent degradation** (line 162–165) → ✓ CLOSED: now fails loud with `site.exit_unresolved` span + reason + warning log when frontier site not declared.
- **MEDIUM exit-failure OTEL parity** (line 166–167) → ✓ CLOSED: added `site_exit_unresolved_span` mirroring `site_enter_unresolved_span`; wired into both shim and SeamCrossingError catcher.
- Both fixes verified by new tests; 110/110 green in rework suite.

**Spec Deviations (All Accepted by Reviewer):**
1. No unit test for router `_SYSTEM_PROMPT` movement bullet — rationale: source-text-wiring anti-pattern; prompt validated via e2e.
2. No server unit test loading real `beneath_sunden/cartography.yaml` — rationale: synthetic fixtures + e2e + pack-validation cover it; avoids duplicative content coupling.
3. Intent stamped on ENTER span only — rationale: `exit_site` shape carries no descriptor/direction; accepted.
4. `DEFAULT_SITE_ID` lazily imported (not top-level) — rationale: avoids `psycopg` import in hot-path module; accepted.

