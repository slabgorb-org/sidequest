---
story_id: "158-7"
jira_key: ""
epic: "158"
workflow: "tdd"
---
# Story 158-7: MP party-split across the seam — co-located party advances to the same region node

## Story Details
- **ID:** 158-7
- **Title:** MP party-split across the seam — co-located party advances to the same region node
- **Type:** bug
- **Points:** 3
- **Priority:** p2
- **Workflow:** tdd
- **Repo:** server
- **Stack Parent:** none

## Problem Statement
When a co-located multi-PC party submits the SAME descent action (narrated as one anchored card, anchor_pc=Groucho), region advance is resolved PER-ACTING-PC, causing co-located players to desync across hops. Repro: session `2026-06-21-beneath_sunden-mp-6c89369d`, turn 3 — both players submitted the same descent ("...steps off into the first chamber of the deep"), narrated as one anchored card. Resulting `pc_regions`: `Groucho: the_dropmouth`, `Harpo: exp001.r2` — the two PCs landed on DIFFERENT region nodes despite acting as a party in the same narrated beat. The split direction is NON-DETERMINISTIC.

## Acceptance Criteria
- When co-located PCs (same source region) act on a shared/anchored descent beat, all co-located party members advance to the SAME destination region node (no per-PC divergence).
- `pc_regions` for co-located party members stays in sync across a shared hop.
- Non-determinism eliminated — the destination must not depend on acting-PC order.
- OTEL: emit a watcher span on the party-advance decision (which PCs advanced together, source region, destination node, anchor) so the GM panel can verify the party moved as a unit.
- Regression test for the MP co-located shared-descent path.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-23T10:06:06Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-23T08:40:16+00:00 | 2026-06-23T08:42:43Z | 2m 27s |
| red | 2026-06-23T08:42:43Z | 2026-06-23T08:56:21Z | 13m 38s |
| green | 2026-06-23T08:56:21Z | 2026-06-23T09:54:09Z | 57m 48s |
| review | 2026-06-23T09:54:09Z | 2026-06-23T10:06:06Z | 11m 57s |
| finish | 2026-06-23T10:06:06Z | - | - |

## Sm Assessment

**Routing:** TDD phased workflow → handoff to TEA (red phase). Server-only bug, 3pts, p2.

**What this is:** A narrow MP-semantics bug exposed *by* the now-working seam crossing (PR #1024), not a regression of it. When a co-located party acts on one shared/anchored descent beat, region advance is resolved per-acting-PC, so `pc_regions` desyncs (`Groucho: the_dropmouth` vs `Harpo: exp001.r2`) and the split direction is non-deterministic. The story title commits the semantic decision: **co-located party advances to the same region node.** TEA does not need to re-litigate intended semantics — write the red tests against "party moves as a unit."

**Scope guardrails for the pipeline:**
- Server-only (`sidequest-server`, base `develop`). Do not touch the seam-reachability path (#1024) beyond what's needed to keep co-located members in sync.
- Likely surfaces to investigate (not prescriptive): the per-PC region-advance in the movement/seam-crossing path (`movement.py`) and the narration-apply region-entry path (`narration_apply.py` region.entry / seam crossing). Prior art for `pc_regions` propagation: PR #1024's `chargen_mixin` inheritance (`snapshot.pc_region_inherited`).
- **OTEL is an AC, not optional** (project Observability Principle): the party-advance decision must emit a watcher span (which PCs advanced together, source region, destination node, anchor) so the GM panel can verify the party moved as a unit. A fix with no span is incomplete.
- Determinism is a first-class AC: destination must not depend on acting-PC order. The red suite should include an order-independence assertion, not just a single-path happy case.
- Wiring test required: at least one test must prove the synced-advance path is reachable from a real MP shared-descent turn, not just a unit helper in isolation.

**Source of truth:** `~/Projects/sq-playtest-pingpong.md` — "[BUG] MP party-split across the seam" section. Repro session `2026-06-21-beneath_sunden-mp-6c89369d`, turn 3.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Behavioral bug fix — a co-located party desyncs on a shared region hop. Needs failing tests pinning the decided semantic ("party moves as a unit") before Dev implements.

**Test Files:**
- `sidequest-server/tests/agents/subsystems/test_movement_party_split_158_7.py` — 8 failing tests covering the MP co-located party-advance contract.

**Tests Written:** 8 tests. **Status:** RED (8/8 failing, no collection errors — verified via testing-runner, `uv run pytest … -p no:randomly -n0 -v`).

**Root cause (for Dev):** Region advance is per-acting-PC (`movement.py` `§Q5 split-party`): every path emits `WorldStatePatch(pc_region={player_name: target})` for the ONE acting PC, fanned per-PC by `session.py::_apply_world_patch_inner`. Nothing builds a multi-entry `pc_region` for a co-located party moving together → desync + non-determinism. The co-seated-party signal already exists and is already threaded into the dispatch-bank context (`additional_player_names`), but `run_movement_dispatch` doesn't declare it, so the bank's signature-filter drops it. **Decided contract:** add `additional_player_names: list[str] | None` to `run_movement_dispatch` (mirroring `run_confrontation_dispatch`/`run_dogfight_dispatch`); when the acting PC advances, every peer co-located at the same source region advances to the same destination, across ALL crossing paths (seam descent + adjacent-seam + in-dungeon hop). Emit one per-PC `movement.resolved` span per advanced PC.

**AC → Test map:**

| AC | Test(s) | Status |
|----|---------|--------|
| Co-located party advances to same node (seam descent) | `test_colocated_party_descends_together_surface_adjacent`, `test_colocated_party_descends_together_owned_seam` | failing (TypeError: param absent) |
| Same-node advance on the in-dungeon procedural hop | `test_colocated_party_advances_together_in_dungeon` | failing |
| `pc_regions` consensus after shared hop (not split) | `test_party_region_consensus_after_shared_hop` | failing |
| Determinism — destination independent of acting-PC order | `test_party_advance_is_order_independent` | failing |
| Scope/Agency guard — non-co-located peer NOT dragged | `test_non_colocated_peer_is_not_dragged` | failing |
| OTEL — per-PC `movement.resolved` span per advanced PC | `test_party_advance_emits_per_pc_movement_span` | failing |
| Wiring — reachable through real `run_dispatch_bank` (MP turn) | `test_party_advance_wired_through_dispatch_bank` | failing (AssertionError — strongest RED) |

### Rule Coverage (python-review-checklist)

| Rule | Test(s) | Status |
|------|---------|--------|
| #4 logging/OTEL coverage | `test_party_advance_emits_per_pc_movement_span` (asserts per-PC span fired) | failing |
| #6 test quality | self-checked — every test asserts concrete values (region ids, span pc_names/to_region), guards against "nobody moved" false pass; no `assert True`/truthy-only | pass |
| #3 type annotations | test helpers annotated (`-> RegionGraph`, `-> dict[str, str]`, etc.) | pass |
| #9 async/await | movement is async; all calls go through `asyncio.run` via `_run` | pass |

**Rules checked:** 4 of 13 lang-review rules apply to a movement-coordination test (the rest — deserialization, paths, resource leaks, deps, input-validation — are N/A to this test surface and to the Dev change locus). **Self-check:** 0 vacuous tests found.

**Wiring test present:** Yes — `test_party_advance_wired_through_dispatch_bank` drives the real `run_dispatch_bank` so the fix must thread `additional_player_names` end-to-end, not just accept a hand-call (satisfies CLAUDE.md "Every Test Suite Needs a Wiring Test" + "No Source-Text Wiring Tests").

**Handoff:** To Dev (Naomi Nagata) for GREEN.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Question** (non-blocking): The co-mover signal `additional_player_names` (already threaded by `run_dispatch_bank`) is "all OTHER seated PCs," NOT "those who chose to move together this turn." The 158-7 tests encode the story's decided semantic — a co-located peer advances WITH the party. A peer who explicitly chose to STAY but is still co-located is not distinguished by this signal and would be dragged. The repro is the both-moved case, so the fix is correct for 158-7; the per-peer-intent refinement is a genuine future story, not this one. Affects `sidequest/agents/subsystems/movement.py` (no change needed now — flagged for Dev/Reviewer awareness so the scope isn't widened by accident). *Found by TEA during test design.*
- **Improvement** (non-blocking): The advance fan-out must cover EVERY crossing path, not only the in-dungeon `_resolve`. Co-located peers must also sync across the seam resolvers (`sidequest/game/seams/deep_descent.py`, `surface_ascent.py`, and the `surface_descent_adjacent` path in `movement.py`) — each currently applies a per-PC `WorldStatePatch(pc_region={player_name: ...})`. The two seam-descent tests + the in-dungeon test pin all three surfaces, so a fix that only handles one will stay RED. Affects `sidequest/game/seams/*.py` and `sidequest/agents/subsystems/movement.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): Pre-existing telemetry-mirror crash unmasked while verifying 158-7. `telemetry/spans/movement.py::_mirror_movement_span_to_sink` read `span.attributes` on a `NonRecordingSpan` and raised `AttributeError` OUT of `run_movement_dispatch` whenever no recording `TracerProvider` was installed — breaking every movement/seam test that didn't set up a tracer (5 such tests were red on develop). Fixed here (guard the mirror). Affects `sidequest/telemetry/spans/movement.py` (fixed). *Found by Dev during implementation.*
- **Gap** (non-blocking): Pre-existing full-suite flake — `watcher_hub` `_process_session_slug` / `_telemetry_sink` process-globals survive a test (ContextVar resets, the global does not), so an integration test leaked a `session_slug` into `test_publish_event_shape`/`test_refusal_payload_round_trips`. Fixed by extending the autouse isolation guard to the slug and re-exporting it into `tests/integration/`. Affects `tests/server/conftest.py` + `tests/integration/conftest.py` (fixed). *Found by Dev during implementation.*
- **Conflict** (non-blocking, OUT OF SCOPE — flagged per user scope decision 2026-06-23): ~6-8 pre-existing WWN cast-spell (ADR-143), AWN mutation (ADR-102), and ship-combat/dogfight integration tests fail non-deterministically in the full `-n auto` suite (the failing SET shifts run-to-run) AND assert behavior the in-flight WN-combat engine intentionally drops (`wn_combat_beat_dropped_engine_owns_round`, narration_apply.py). These are epic-108 (WN-owns-the-round) territory, NOT 158-7 — proven pre-existing (fail identically on base; all pass in isolation/their own directory). They were deliberately left unfixed. Affects `tests/integration/test_wwn_*_dispatch.py`, `test_102_5/102_7/103_10`, `test_59_23_materialize_other.py`, narration_apply WN-combat path — *a dedicated cleanup/epic-108 story.* *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): Two of the six `_advance_colocated_peers` call sites have no co-located-party test — `surface_ascent` (reverse seam) and the lateral cartography path. The helper is identical at all six sites and the descent/in-dungeon paths are well-covered, so risk is low, but a future change could break party-advance on ascent/lateral undetected. Affects `tests/agents/subsystems/test_movement_party_split_158_7.py` (add `test_colocated_party_ascends_together` + a lateral-move variant). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `test_party_advance_emits_per_pc_movement_span` asserts the peer spans fire with the right `pc_name`/`to_region` but NOT the `party_advance=True` / `anchor_pc` attributes that satisfy AC-4's "which PCs advanced together + anchor." The attributes ARE emitted by `_advance_colocated_peers`; the test just doesn't pin them. Strengthen the OTEL lie-detector assertion. Affects `tests/agents/subsystems/test_movement_party_split_158_7.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `_FakeHandle.drain()` increments a `drain_calls` counter (docstring: "counted so a test can assert it was awaited") but no test asserts it — dead instrumentation. Either drop the counter (plain `pass`) or assert `handle.drain_calls == 1` in the in-dungeon materialize test. Affects `tests/agents/subsystems/test_movement_dispatch.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The witness-count test asserts `len(_WITNESSES) == 11` but not that `dogfight` specifically is the new key — a different 11th registration would pass. Add `assert "dogfight" in _WITNESSES` to mirror the existing `movement`/`course` key checks. Affects `tests/agents/test_59_30_witnesses.py`. *Found by Reviewer during code review.*
- **Question** (non-blocking): Telemetry guard comment at `telemetry/spans/movement.py` lists "a dropped sampling decision" as a production-realistic NonRecordingSpan cause; in production `init_tracer` uses a `ParentBased(ALWAYS_ON)` root with no remote parent, so sampling cannot drop a movement span unless an external `OTEL_TRACES_SAMPLER` is set. Minor comment-precision; the guard itself is correct. Affects `sidequest/telemetry/spans/movement.py`. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Tests encode a specific fix mechanism the story left open (the `additional_player_names` param contract)**
  - Spec source: context-story-158-7.md (AC "to be defined by TEA"); session SM Assessment ("write the red tests against 'party moves as a unit'")
  - Spec text: "co-located party advances to the same region node" (semantic decided; mechanism not prescribed)
  - Implementation: The RED suite pins a concrete contract — `run_movement_dispatch` gains `additional_player_names: list[str] | None`, and co-located peers (same source region) advance to the acting PC's destination. Chosen because it is the EXISTING co-seated-party idiom (`run_confrontation_dispatch`/`run_dogfight_dispatch` already declare it; the bank already threads it signature-filtered) — the minimal, wiring-consistent change.
  - Rationale: TDD RED must commit to a contract for the tests to be greenable. This is the lowest-surface-area option and reuses live plumbing rather than inventing a new param/event. The bank-level wiring test backstops the unit contract.
  - Severity: minor
  - Forward impact: Dev should implement the param-based contract (not a snapshot-only derive that omits the param), or the unit tests' `additional_player_names=` kwarg will not be accepted. If Dev has a strong reason to diverge, the bank-wiring test (`test_party_advance_wired_through_dispatch_bank`) is the authoritative behavioral pin and the unit kwargs can be reconciled.

### Dev (implementation)
- **Scope expanded beyond the 158-7 AC at user direction (fix pre-existing test failures, not just the feature)**
  - Spec source: 158-7 story scope (MP party-split) + user directive 2026-06-23 ("fix the failures as part of this … expand scope") and AskUserQuestion answer ("Safe ones only")
  - Spec text: 158-7 ACs cover only the co-located party-advance behavior
  - Implementation: Also fixed (a) the `_mirror_movement_span_to_sink` NonRecordingSpan crash, (b) the `_FakeHandle.drain` double, (c) the `watcher_hub` session_slug/sink full-suite flake (conftest isolation guard + integration re-export), (d) the dispatch-engagement witness count docstring (10→11). Deliberately did NOT touch the WWN/mutation/ship-combat combat-engine failures (epic-108) per the user's "Safe ones only" choice.
  - Rationale: The movement/seam telemetry crash was the "dance" blocking honest 158-7 verification (regression-vs-pre-existing was indistinguishable). User explicitly authorized the expansion. The combat-engine cliff (epic-108) was scoped out as too large/risky for a 3-pt bugfix.
  - Severity: minor
  - Forward impact: Reviewer should review the conftest isolation guard + telemetry-mirror guard as deliberate, user-sanctioned scope. The remaining full-suite WWN/mutation/ship-combat failures are pre-existing and out of scope (see Delivery Findings) — they are NOT a 158-7 regression.

### Reviewer (audit)
- **TEA: tests encode the `additional_player_names` param contract the story left open** → ✓ ACCEPTED by Reviewer: the chosen mechanism is the established co-seated-party idiom (confrontation/dogfight already declare the param; the bank threads it signature-filtered), and the bank-level wiring test pins it independently of the unit kwargs. Lowest-surface-area, wiring-consistent. Sound.
- **Dev: scope expanded beyond the 158-7 AC (telemetry-mirror crash, session_slug flake, witness docstring, `_FakeHandle.drain`)** → ✓ ACCEPTED by Reviewer: explicitly user-directed ("fix the failures … expand scope", AskUserQuestion "Safe ones only"). The telemetry-mirror guard and conftest isolation fixes are genuine root-cause fixes (a telemetry side-channel must never crash the dispatch; a process-global binding must be reset between tests), zero production-behavior change on the recording path, and the combat-engine cliff was correctly scoped OUT. Proportionate and well-documented.
- **No undocumented deviations found.** The diff matches the logged contract: `_advance_colocated_peers` advances ONLY co-located peers (Agency-safe per `test_non_colocated_peer_is_not_dragged`), the param defaults to `None` (back-compat for all existing callers), and the telemetry/conftest changes are confined to the documented surfaces.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/agents/subsystems/movement.py` — `run_movement_dispatch` gains `additional_player_names`; new `_advance_colocated_peers` helper fans the acting PC's destination to co-located seated peers across all 6 advance sites (owned-seam, adjacent-seam, surface-ascent, lateral, room-graph surface→deep, in-dungeon hop), each peer emitting its own `movement.resolved` span.
- `sidequest/telemetry/spans/movement.py` — guard `_mirror_movement_span_to_sink` against `NonRecordingSpan` (telemetry side-channel must not crash the dispatch).
- `tests/agents/subsystems/test_movement_party_split_158_7.py` — 8 story tests (all green) + 2 telemetry-mirror robustness regression tests.
- `tests/agents/subsystems/test_movement_dispatch.py` — `_FakeHandle.drain()` added to match the real `LookaheadWorkerHandle`.
- `tests/agents/test_59_30_witnesses.py` — witness count 10→11 (dogfight, 153-6); test renamed `_is_eleven_`.
- `tests/server/conftest.py` — autouse isolation guard now save/restores `_process_session_slug` (+ existing `_telemetry_sink`).
- `tests/integration/conftest.py` — re-export the isolation guard into the integration tree (leak fixed at source).

**Tests:**
- 158-7 story file: **10/10 passing** (8 ACs + 2 mirror-regression).
- The 5 previously-red movement/seam tests: **now green** (telemetry-mirror fix).
- The 2 xdist-flaky tests (`test_publish_event_shape`, `test_refusal_payload_round_trips`) + witness-count test: **now green** (session_slug isolation + docstring).
- Full server suite: ~8 pre-existing WWN/mutation/ship-combat failures remain — **proven pre-existing, out of scope (epic-108)**, deliberately not touched per user scope decision. Zero regressions introduced (all flagged tests pass in isolation + their own directory; my changes touch no confrontation/combat production code).

**Branch:** `feat/158-7-mp-party-split-seam` (pushed to origin).

**Handoff:** To Reviewer (Chrisjen Avasarala) for code review. Key review focus: the conftest test-isolation guard + telemetry-mirror guard are deliberate user-sanctioned scope expansion; the residual full-suite WWN/mutation/ship-combat failures are pre-existing combat-engine (ADR-143/-102, epic-108), NOT a 158-7 regression.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean (GREEN) | 1 (pre-existing pyright) | confirmed 0, dismissed 0, deferred 1 (pre-existing on develop, out of scope) |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (boundary analysis done by Reviewer — see Devil's Advocate) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings (telemetry guard + helper error-paths checked by Reviewer + rule-checker #1) |
| 4 | reviewer-test-analyzer | Yes | findings | 7 | confirmed 5, dismissed 1, deferred 1 |
| 5 | reviewer-comment-analyzer | Yes | findings | 2 | confirmed 2, dismissed 0 |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (type annotations verified via rule-checker #3) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings (input-validation verified via rule-checker #11; no auth/secrets surface) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (simplicity assessed by Reviewer — helper is minimal, one nit: dead `drain_calls` counter) |
| 9 | reviewer-rule-checker | Yes | clean (GATE PASS) | 1 advisory | confirmed 0, dismissed 0, deferred 1 (resolved benign by Reviewer) |

**All received:** Yes (4 enabled returned; 5 disabled pre-filled)
**Total findings:** 7 confirmed (all non-blocking), 2 dismissed (with rationale), 3 deferred (pre-existing / resolved-benign)

## Reviewer Assessment

**Verdict:** APPROVED

No Critical or High issues. The production change is correct, well-scoped, and verified GREEN; every confirmed finding is a non-blocking test-thoroughness or comment-precision improvement, captured as Delivery Findings.

**Data flow traced:** A real MP shared-descent turn → `websocket_session_handler` computes `_acting_player_name` + `_additional_player_names` (all OTHER seated PCs) → `execute_intent_router_pre_narrator_pass` threads both into `run_dispatch_bank` context → the bank signature-filters context to `run_movement_dispatch`'s declared kwargs (now incl. `additional_player_names`) → the acting PC crosses/advances via the seam/§Q1 path → `_advance_colocated_peers` advances every peer whose `pc_regions[peer] == from_region` to the same `to_region`. Safe because the co-location filter is evaluated once upfront (order-stable), excludes the acting PC, and a `None`/missing peer entry never matches a non-empty `from_region`. Verified by `test_party_advance_wired_through_dispatch_bank` (real bank path) + `test_non_colocated_peer_is_not_dragged` (Agency guard).

**Observations:**
- `[VERIFIED]` All 6 `_advance_colocated_peers` call sites pass the acting PC's PRE-move `from_region` (captured at movement.py:323 for the region-mode block, movement.py:566 for §Q1) and the resolved `to_region`/`target_id`/`crossing.to_region`. The peer filter excludes the acting PC (already moved to `to_region`) and non-co-located peers. Evidence: movement.py:406-413, 461-468, 521-528, 589-596, 723-730, 893-900 — each call uses the in-scope `from_region`. Complies with the AC "same source region → same destination."
- `[VERIFIED]` Agency / SOUL "The Test": only peers `snapshot.pc_regions.get(name) == from_region` advance (movement.py:314); a split party stays split. Evidence: `test_non_colocated_peer_is_not_dragged` asserts Harpo (at ropefoot) is NOT dragged when Groucho descends from the_dropmouth. The story AC ("co-located party advances to the same node") is the higher-authority spec that intentionally moves co-located peers together; the residual "co-located peer who chose to stay" edge is documented (TEA/Dev Delivery Findings) and product-decided for the cooperative playgroup.
- `[RULE]` rule-checker GATE PASS (13/13 checks). Its one advisory — peer `apply_world_patch` may fire undrained background `notify_region_transition` lookahead tasks — is **resolved BENIGN**: peers co-locate to the acting PC's destination node, whose onward ring the acting PC's own patch/drain already materialized; peer-triggered tasks for that same node are redundant no-ops. Minor efficiency only (N redundant `create_task`s). No correctness impact.
- `[SILENT]` (subagent disabled) Reviewer check: the new telemetry guard `if not hasattr(span, "attributes"): return` (telemetry/spans/movement.py:178) is NOT a silent fallback — it short-circuits a telemetry side-channel on a structurally-unrecordable `NonRecordingSpan` (nothing to mirror), masks no alternative path, and leaves the recording path unchanged. The comment argues this explicitly. A telemetry helper raising into the dispatch it wraps was the real bug; the guard removes it. Confirmed correct.
- `[TEST]` Confirmed (test-analyzer): 2 of 6 call sites untested for party-advance (`surface_ascent`, lateral) + OTEL `party_advance`/`anchor_pc` attributes unasserted + dead `drain_calls` counter + witness-key not pinned. All non-blocking Improvements (see Delivery Findings). DISMISSED test-analyzer's claim that `test_party_advance_is_order_independent` "always passes without the fix" — without the fix the `additional_player_names=` kwarg raises `TypeError` and the peer stays at ropefoot, so it is a genuine RED→GREEN test (the naming nuance is a LOW note).
- `[DOC]` Confirmed (comment-analyzer): the "dropped sampling decision" clause overstates production risk (LOW); the `_advance_colocated_peers` docstring omits the `resolved_via` param (LOW). Both cosmetic, non-blocking.
- `[TYPE]` (subagent disabled) Reviewer check via rule-checker #3: the new public param `additional_player_names: list[str] | None = None` is fully annotated; the helper is private (exempt) but annotated `-> list[str]`. The pre-existing pyright `_SpanLike` vs `Span` nit at telemetry/spans/movement.py:182 is on develop already, not introduced here. Compliant.
- `[SEC]` (subagent disabled) Reviewer check via rule-checker #11: `additional_player_names` is internal dispatch-bank context (not raw user input); peer names are used only as `snapshot.pc_regions` dict keys — no SQL/shell/path-traversal surface. No secrets, no auth, no tenancy in movement coordination. No security concern.
- `[SIMPLE]` (subagent disabled) Reviewer check: `_advance_colocated_peers` is minimal and reused across all 6 sites (no duplication). One simplification nit: the `drain_calls` test-double counter is dead (never asserted) — drop it or assert it.
- `[EDGE]` (subagent disabled) Reviewer boundary analysis: empty/None `additional_player_names` → `(… or [])` → no-op; peer == acting_pc → excluded; peer not in `pc_regions` → `.get()` returns None ≠ from_region → excluded; `to_region` empty → early `return []`. All boundaries safe. See Devil's Advocate.

### Rule Compliance (python-review-checklist + CLAUDE.md/SOUL)
- **#1 silent exceptions:** Compliant. No new try/except; the telemetry `hasattr` guard is a structural null-check, not a swallow.
- **#2 mutable defaults:** Compliant. `additional_player_names: … = None`; used via `(… or [])`.
- **#3 type annotations:** Compliant. Public param annotated; helper annotated though exempt.
- **#4 logging/OTEL:** Compliant. Per-peer `movement.resolved` spans (party_advance/anchor_pc) emitted; debug-level success log with %-format. OTEL Observability Principle satisfied (the party-advance decision is on the GM panel).
- **#6 test quality:** Compliant. 10 tests, specific value assertions, correct mock targets, runtime-reflection witness check (not source grep), real-bank wiring test. (Coverage gaps noted as non-blocking Improvements.)
- **#9 async/await:** Compliant. Helper is sync (only sync calls); correctly invoked without `await` from the async dispatch; `await lookahead_handle.drain()` / `await _sync_materialize(...)` correctly awaited.
- **No Silent Fallbacks / No Stubbing / No Source-Text Wiring Tests / Every Suite Needs a Wiring Test / SOUL Agency:** All compliant (rule-checker additional-rules pass; wiring test present; co-location guard is Agency-safe).

### Devil's Advocate
Suppose I want this broken. The headline attack: drag a player who didn't move. If the table has four PCs and only two descend together as the anchored beat, `additional_player_names` is still "all OTHER seated PCs" — so a fourth PC, co-located at the source but who narrated "I hold the rope," would be teleported into the deep. That violates SOUL's *The Test* on its face. But the story AC and the product owner explicitly chose party-moves-together for this cooperative playgroup (CLAUDE.md: the table doesn't slip notes; the party stays together), and the gap is documented as a follow-up — so it is an accepted product tradeoff, not an undocumented violation. Second attack: re-entrancy. `_advance_colocated_peers` mutates `snapshot.pc_regions` inside a loop while filtering against it — could moving peer A change peer B's co-location verdict? No: `peers` is materialized in one comprehension before any mutation, so the loop is order-stable. Third: the undrained peer lookahead tasks — could the narrator describe a peer arriving in a half-materialized room? No: peers land on the acting PC's destination, whose ring the acting PC already drained; the peer tasks are redundant. Fourth: a confused author binds `additional_player_names` to a stale roster including a despawned PC — `.get()` returns None, excluded, no crash. Fifth: empty/None input → early return. The only real exposure is the documented Agency edge, and it is product-sanctioned. Nothing here corrupts state or crashes a turn.

**Handoff:** To SM (Camina Drummer) for finish-story.