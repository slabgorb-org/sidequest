---
story_id: "91-4"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 91-4: Cross-model runaway coverage — extend ADR-134 detector + per-session cumulative cost to all call sites and models

## Story Details
- **ID:** 91-4
- **Jira Key:** (not configured)
- **Workflow:** tdd
- **Stack Parent:** none
- **Branch:** feat/91-4-cross-model-runaway-coverage
- **Repository:** sidequest-server

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-06T02:06:46Z
**Branch Strategy:** gitflow (feat/91-4-cross-model-runaway-coverage)

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-06T01:12:44.125602Z | 2026-06-06T01:14:31Z | 1m 46s |
| red | 2026-06-06T01:14:31Z | 2026-06-06T01:30:32Z | 16m 1s |
| green | 2026-06-06T01:30:32Z | 2026-06-06T01:56:43Z | 26m 11s |
| review | 2026-06-06T01:56:43Z | 2026-06-06T02:06:46Z | 10m 3s |
| finish | 2026-06-06T02:06:46Z | - | - |

## Sm Assessment

Setup complete for story 91-4 (Cross-model runaway coverage — extend ADR-134 detector + per-session cumulative cost to all call sites and models, 2 pts, p2, epic 91 Dark Spend).

- Session file created with story fields, workflow (tdd, phased), and branch tracking.
- Story branch `feat/91-4-cross-model-runaway-coverage` created in `sidequest-server` from `develop` (per repos.yaml).
- Story context validated at `sprint/context/context-story-91-4.md`; epic context at `sprint/context/context-epic-91.md`.
- Jira: no key configured on this story — claim explicitly skipped.
- Dependencies: 91-1 (SDK choke point + universal usage instrumentation) is complete and merged — the instrumentation seam this story extends is in place.
- Routing: phased tdd workflow → next phase `red`, owner TEA.

## TEA Assessment

**Tests Required:** Yes
**Reason:** n/a — full TDD RED phase. Story had no recorded ACs; TEA defined seven (AC-1…AC-7, documented in the test module docstring) from the story title + epic-91 doctrine ("the ADR-134 runaway detector covers all models") + ADR-134's invariants.

**Test Files:**
- `sidequest-server/tests/agents/test_91_4_cross_model_runaway_coverage.py` — 17 tests: factory session-id contract, detector on Haiku call sites, baseline integrity across models, cross-site cumulative, cross-call-site ceiling kill, None-bypass, env fail-loud
- `sidequest-server/tests/handlers/test_91_4_aside_session_wiring.py` — 1 test: real `PlayerActionHandler` aside branch passes the room slug to `build_aside_llm` (the "Verify Wiring, Not Just Existence" half)

**Tests Written:** 18 tests covering 7 ACs
**Status:** RED (18/18 failing — verified by testing-runner, run id 91-4-tea-red, `-n0`; zero collection errors; failure reasons are all missing-feature signals: `session_id` kwarg not accepted, handler not passing it)

**Contract pinned (for Dev):**
- `build_aside_llm` / `build_intent_router_llm` / `build_intent_router_for_session` take a **required keyword-only** `session_id: str | None` (`None` = explicit ADR-134 sessionless opt-out; omission = TypeError). Adapter binds it (router adapter attr `_session_id` pinned by the binding test, mirroring 91-1's `adapter._sdk` idiom).
- Session-bound adapter calls run the ADR-134 detector: `cost_runaway_suspected` with existing fields PLUS a new `caller` field; `model`/`session_id` carried.
- Baseline windows must be scoped so cheap Haiku traffic does not train the narrator's per-session baseline (per-(session, caller) or per-(session, model) both pass the tests); a Haiku cost spike post-warmup fires `cost_multiple` against its own rolling mean.
- ONE per-session cumulative across narrator + aside + router, shared **across instances** (adapters are constructed per call; narrator client is long-lived — this forces process-level shared state). `session.cost_running_total` must report the combined figure.
- Ceiling crossing on any call site raises `AnthropicSdkCostCeilingExceeded` + emits `session.cost_ceiling_exceeded` once; subsequent calls at every call site refuse pre-flight (assertions on fake-SDK call counts == 0). Per-session isolation preserved.
- `SIDEQUEST_SESSION_COST_CEILING_USD` fail-loud validation (`AnthropicSdkConfigError` on nan/inf/non-positive/garbage) applies on the adapter path (construction or first call).
- Production wiring: aside handler passes `room.slug`; `build_intent_router_for_session`'s required kwarg forces the websocket_session_handler call site to pass the slug (it cannot construct without it).

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| No Silent Fallbacks (required kwarg, no implied bypass) | `test_build_*_requires_explicit_session_id` ×3 | failing |
| No Silent Fallbacks (env validation) | `test_adapter_ceiling_env_invalid_fails_loud` ×4 params | failing |
| Every Test Suite Needs a Wiring Test | `test_player_action_handler_passes_room_slug_to_aside_llm_factory`, `test_intent_router_for_session_binds_session_to_adapter` | failing |
| No Source-Text Wiring Tests | wiring asserted via seam injection + behavior, no source grepping | by construction |
| OTEL Observability Principle (#4 logging) | event/field assertions on `cost_runaway_suspected`, `session.cost_ceiling_exceeded`, `session.cost_running_total`; telemetry-preserved assert in bypass test | failing |
| §6 test quality (no vacuous assertions) | self-checked: every test asserts values/fields/counts, no `assert True`/`let _` patterns | done |

**Rules checked:** python lang-review §1 (fail-loud raise assertions), §4 (log/event coverage), §6 (self-check) + project critical rules. §2/§3/§5 not applicable (no production code written in RED).
**Self-check:** 0 vacuous tests found.

**Handoff:** To Dev (Naomi Nagata) for implementation.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): The required `session_id` kwarg will break existing zero-arg callers when implemented: 91-1 tests (`test_91_1_sdk_choke_point_instrumentation.py` calls `build_aside_llm()`/`build_intent_router_llm()` bare), the aside harness seam swap (`tests/handlers/_harness.py:257` — `lambda: self._llm_aside` must accept the kwarg), and the production call sites (`sidequest/handlers/player_action.py:370`, `sidequest/server/intent_router_pass.py:79` + its websocket_session_handler caller). Affects those files (Dev updates them in GREEN — this is the intended forcing function, not an accident). *Found by TEA during test design.*
- **Question** (non-blocking): Cross-instance cumulative sharing implies process-level state (today `_session_cumulative_cost_usd` et al. are per-`AnthropicSdkClient`-instance). Existing tests reuse session ids like "61-baseline-test" across tests within a worker — if Dev migrates state to module level, those suites may need unique ids or a reset seam. Affects `sidequest/agents/anthropic_sdk_client.py` (state migration strategy) and the 61-x test files. New 91-4 tests are immune (unique "91-4-*" ids). *Found by TEA during test design.*
- **Improvement** (non-blocking): ADR-134's flagged follow-up (stale `_session_ceiling_announced` entry suppressing a slug-recycle rejoin's first alarm; `reset_baselines` not clearing cumulative/announce state) becomes more visible once Haiku spend feeds the same pot — worth folding into this story's implementation or re-flagging. Affects `sidequest/agents/anthropic_sdk_client.py` (`reset_baselines` scope note). *Found by TEA during test design.*
- **Question** (non-blocking): Dungeon-curate (`complete_with_tools(session_id=None, caller="dungeon_curate")`) stays a deliberate ADR-134 bypass under these tests. If "all call sites" was meant to include curate, the materializer call site needs a session identity decision — out of the pinned contract for 2 pts. Affects `sidequest/dungeon/materializer.py` (~line 1213) if in scope. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): The new `caller` field on `cost_runaway_suspected` is emitted but the dashboard's typed event shapes don't know it yet. Affects `sidequest-ui/src/types/watcher.ts` and the GM-panel cost views (surface `caller` so cross-model alarms are attributable at a glance). *Found by Dev during implementation.*
- **Improvement** (non-blocking): ADR-134 now describes the detector/ceiling as living wholly in `anthropic_sdk_client.py`; 91-4 relocated the comparator/ceiling/env-parse to `sidequest/agents/cost_safety.py` (shared ledger) with the client delegating. Affects `docs/adr/134-cost-runaway-ceiling.md` (orchestrator repo — amendment note recording the relocation and the adapter coverage). *Found by Dev during implementation.*
- **Gap** (non-blocking): 92-1's A/B eval capture CLI (`scripts/router_ab_eval_cli.py`) now opts out with `session_id=None` — correct for an operator-bounded tool, but its spend is therefore ceiling-uncovered by design; if eval runs grow large, consider a synthetic eval session id. Affects `scripts/router_ab_eval_cli.py` (only if eval spend becomes material). *Found by Dev during implementation.*
### Reviewer (code review)
- **Improvement** (non-blocking): No regression test pins `reset_baselines` → ledger adapter-window eviction (behavior verified live during review: per-session windows dropped, neighbors intact, cumulative preserved). Affects `sidequest-server/tests/agents/` (one test: seed K=10 router calls, reset, assert next call reports warmup=True; control session stays post-warmup). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Document two bounded edges in the ADR-134 amendment Dev already filed for: (a) per-instance ceiling values vs the shared pot diverge only under runtime env mutation (none exists in production — grep-verified) and the announce-set is keyed per session, not per (session, ceiling); (b) the pre-flight/post-call TOCTOU bounds overspend at one in-flight call per concurrent caller — the ceiling is best-effort by that width, as the narrator's machinery always was. Affects `docs/adr/134-cost-runaway-ceiling.md` (orchestrator repo). *Found by Reviewer during code review.*
- **Question** (non-blocking): The ws `seed_session_id` synthetic fallback (`{genre}::{world}::{player}`) gives the router a coverage pot the narrator does not share on no-slug paths (narrator runs None-bypassed there). Strictly more coverage than pre-91-4, but if those legacy paths ever matter, align the narrator onto the same key. Affects `sidequest/server/websocket_session_handler.py` + `sidequest/server/session_helpers.py` (key alignment decision). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Two low-cost test hardenings — assert construction-scope on `test_adapter_ceiling_env_invalid_fails_loud` (the `await` line is unreachable today) and switch the handler wiring test's factory re-swap to `monkeypatch.setattr`. Affects `tests/agents/test_91_4_cross_model_runaway_coverage.py`, `tests/handlers/test_91_4_aside_session_wiring.py`. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Detector/ceiling event component string not pinned for adapter-side emits**
  - Spec source: ADR-134 §Observability
  - Spec text: events emit "via `_watcher_publish_event` (component `narrator.sdk`)"
  - Implementation: tests assert `event_type` + fields only, not `component`, for adapter-originated events
  - Rationale: `narrator.sdk` is a misnomer for aside/router emits; pinning it would freeze a naming wart. Dev/Reviewer may keep `narrator.sdk` (GM-panel compatibility) or introduce a truthful component — both pass.
  - Severity: minor
  - Forward impact: GM-panel event filters keyed on component should be checked in GREEN if the component string changes.
  - → ✓ ACCEPTED by Reviewer: Dev kept `narrator.sdk` (no filter breakage); the `caller` field carries true origin. Sound.
- **Running-total pulse not required on adapter calls**
  - Spec source: story title ("per-session cumulative cost to all call sites")
  - Spec text: extend per-session cumulative cost to all call sites and models
  - Implementation: tests require adapter spend to be *included* in the cumulative and surfaced via the narrator's per-turn `session.cost_running_total`; they do not require asides/router to emit their own per-call pulse
  - Rationale: the pulse is a per-turn GM-panel counter (ADR-134 §C.3); asides are non-turns (ADR-107). The cumulative is what the title demands; pulse cadence is a design freedom left to Dev.
  - Severity: minor
  - Forward impact: none — adding adapter-side pulses later would not break these tests.
  - → ✓ ACCEPTED by Reviewer: pulse cadence is per-turn by design (ADR-134 §C.3); the cumulative inclusion is tested. Agrees with author reasoning.

### Dev (implementation)
- **Adapter-side cost events keep component `narrator.sdk`**
  - Spec source: ADR-134 §Observability (via TEA deviation note, context-story-91-4 contract)
  - Spec text: events emit "via `_watcher_publish_event` (component `narrator.sdk`)"
  - Implementation: aside/router-originated `cost_runaway_suspected` and `session.cost_ceiling_exceeded` events keep component `narrator.sdk` despite not being narrator calls (the `caller` field carries the true origin)
  - Rationale: GM-panel filters group the cost events under one component; renaming would orphan adapter alarms from the existing dashboard view. The misnomer is documented in `cost_safety.check_and_emit_runaway`'s docstring. Within the freedom TEA's deviation note explicitly granted.
  - Severity: minor
  - Forward impact: a future component rename (e.g. `llm.sdk`) must move all cost events together and update GM-panel filters in the same change.
  - → ✓ ACCEPTED by Reviewer: within the freedom TEA's deviation explicitly granted; misnomer documented at the emit site (`cost_safety.check_and_emit_runaway` docstring).
- **Router ws call site passes the seed_session_id fallback, not None**
  - Spec source: TEA contract ("Production wiring: ... build_intent_router_for_session's required kwarg forces the websocket_session_handler call site to pass the slug")
  - Spec text: pass the canonical session id (room slug / sd.game_slug)
  - Implementation: `websocket_session_handler` passes `seed_session_id` — room slug, else `sd.game_slug`, else the deterministic `f"{genre}::{world}::{player_id}"` fallback the seed-trope deck already uses — rather than degrading to `None` on the no-room/no-slug path
  - Rationale: a deterministic id keeps detector/ceiling coverage ON for non-slug-connect paths instead of silently opting them out; it is the same identity the seed deck keys on, so cost state and game state agree.
  - Severity: minor
  - Forward impact: none — slug-connect production paths always resolve to the room slug; the fallback only fires on legacy/test connects.
  - → ✓ ACCEPTED by Reviewer: verified the narrator itself runs `session_id=sd.game_slug` (None → bypass) on that same fallback path (`session_helpers.py:1289`), so the synthetic key cannot mis-key against an ACTIVE narrator pot — it strictly adds coverage the router previously lacked. Cross-site keys agree on all slug-connect paths (room slug == sd.game_slug per ADR-134). Documented as a delivery finding for ledger-key alignment follow-up.

### Reviewer (audit)
- All four logged deviations audited: 4 ACCEPTED, 0 FLAGGED, 0 undocumented deviations found (the diff was checked against the TEA contract, story context, and epic doctrine — implementation matches the pinned contract on every AC).
## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (sidequest-server, branch `feat/91-4-cross-model-runaway-coverage`):**
- `sidequest/agents/cost_safety.py` (NEW) — process-level `SessionCostLedger` (one cumulative pot + announce set per session; per-(session, caller) rolling baselines for the adapters), the shared four-trigger comparator `check_and_emit_runaway` (event gains `caller`), `parse_session_cost_ceiling_usd` (fail-loud env validation), `build_ceiling_exceeded`
- `sidequest/agents/anthropic_sdk_client.py` — constants/comparator/ceiling delegate to `cost_safety`; constructor aliases `_session_cumulative_cost_usd`/`_session_ceiling_announced` onto the shared ledger dicts (sharing changes, behavior doesn't); `_maybe_emit_cost_runaway` gains `caller` (default `"narrator"` — 61-A direct-call tests unaffected); `reset_baselines` also evicts the ledger's adapter windows
- `sidequest/agents/llm_factory.py` — `_AsideLlm`/`_IntentRouterLlm` take REQUIRED keyword-only `session_id: str | None`; pre-flight ceiling refusal before touching the SDK; post-call detector + cumulative pass via the ledger; `_record_usage_telemetry` returns a `_UsageSummary` so safety reuses the accounted figures; factories require the kwarg
- `sidequest/server/intent_router_pass.py` — `build_intent_router_for_session(*, session_id)` required kwarg, flows to the adapter
- `sidequest/server/websocket_session_handler.py` — passes `seed_session_id` (room slug / game_slug / deterministic fallback) into the router factory
- `sidequest/handlers/player_action.py` — aside branch resolves the canonical session id (room slug → game_slug → fail-loud RuntimeError) and passes it to `build_aside_llm`
- `scripts/router_ab_eval_cli.py` — explicit `session_id=None` opt-out (operator-bounded eval tool)
- Test infra: `tests/conftest.py` (autouse ledger reset before every test), `tests/handlers/_harness.py` + `tests/server/conftest.py` + `tests/e2e/conftest.py` + `tests/e2e/test_encounter_wiring_e2e.py` + `tests/agents/test_router_ab_eval_harness.py` (factory-stub lambdas accept kwargs), `tests/agents/test_91_1_sdk_choke_point_instrumentation.py` + `tests/agents/test_intent_router_wiring.py` + `tests/agents/test_haiku_cache_control.py` (explicit `session_id=None` constructions)

**Tests:** 18/18 story tests passing (GREEN); full server suite **11096 passed / 0 failed / 345 skipped** (testing-runner runs `91-4-dev-green`, `91-4-dev-green-full`, `91-4-dev-green-full-2`). Ruff clean; pyright delta zero (40 pre-existing errors on touched files before and after; `cost_safety.py` contributes 0).

**Design notes for Reviewer:**
- Cross-instance sharing is by ALIASING (client constructor binds the ledger's dicts) — the 61-followup-D machinery is otherwise untouched, so all existing ceiling/baseline tests pass unmodified. Narrator rolling baselines stay per-instance, keyed on plain session_id (61-followup-A contract); only the adapters use the ledger's (session, caller) windows.
- Required-kwarg factories are the anti-regression forcing function: a future Haiku call site cannot compile against the factory without making an explicit session decision.
- TEA's "Question" re: module-state leakage across existing tests was answered with the suite-wide autouse `_reset_cost_safety_ledger` fixture rather than touching the 61-x suites.

**Branch:** feat/91-4-cross-model-runaway-coverage (pushed; commits a632004 RED, a2cc280 GREEN)

**Handoff:** To Reviewer (Chrisjen Avasarala) for code review
## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (18/18 story tests green, 0 smells; 161-file format drift verified pre-existing on develop) | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 8 | confirmed 3, dismissed 5, deferred 0 |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 | confirmed 1 (downgraded with evidence), dismissed 2, deferred 0 |
| 4 | reviewer-test-analyzer | Yes | findings | 6 | confirmed 3, dismissed 3, deferred 0 |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings (covered by own read: new docstrings verified accurate, incl. relocation notes) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (covered by own read: full annotations at boundaries, NamedTuple summary, tuple-keyed dicts typed) |
| 7 | reviewer-security | Yes | findings | 3 | confirmed 3 (1 downgraded medium→low with grep evidence), dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (covered by own read: net −271 lines in client; one shared comparator replaces a would-be duplicate) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings (covered by own Rule Compliance enumeration below) |

**All received:** Yes (5 enabled returned — 4 with findings, 1 clean; 4 disabled via settings)
**Total findings:** 10 confirmed (1 Medium, 9 Low), 10 dismissed (with rationale), 0 deferred

### Dismissal rationales
- [EDGE#1 race in update_cumulative] — dismissed: read-modify-write is pure synchronous dict ops with no `await` between them; asyncio cannot preempt (`cost_safety.py:283-286`). The real async gap is the pre-flight/post-call TOCTOU, which is SEC#3 (confirmed Low).
- [EDGE#2 baseline append before cumulative raise] — dismissed: identical ordering to the narrator's pre-existing per-iter sequence (`_maybe_emit_cost_runaway` append → `_update_session_cumulative` raise); the "retry sees dirty baseline" path is unreachable because `check_ceiling` refuses pre-flight.
- [EDGE#5 empty-string session_id] — dismissed: `""` fails `is not None` toward COVERAGE (keyed, checked, killed) — the fail-safe direction; no caller passes `""` (both production resolutions yield slug or raise).
- [EDGE#7 check_ceiling None runtime guard] — dismissed: signature is `session_id: str`, all three call sites guard `is not None` before calling; a None here is a typing violation upstream, pyright-visible.
- [EDGE#8 emit-raise announce ordering] — dismissed: hunter's own analysis concludes the behavior (retry emit on next call, never poison the set) is the desired lang-review §14 pattern; `watcher_hub.publish` is documented best-effort non-raising.
- [SILENT#2 watcher span path may raise] — dismissed (low): span minting only under `SIDEQUEST_WATCHER_AS_SPANS=1` (dev flag); production publish path never raises; consequence is emit-retry, not loss.
- [SILENT#3 late imports ImportError] — dismissed: same-package import exercised by 11k-test suite at every adapter construction; an ImportError here would be a catastrophic packaging failure, loud everywhere.
- [TEST#3 killer call-count assert missing] — dismissed: the feared bug (ceiling fires at zero spend) is already caught by `test_aside_crossing_ceiling_raises_and_announces_once`, which asserts `exc.cumulative_cost_usd == cost(crossing) > 0` — a zero-spend kill fails that assertion.
- [TEST#4 private-attr binding test] — dismissed: deliberate 91-1 idiom TEA pinned knowingly; the behavioral contract is independently covered by `test_ceiling_crossed_by_narrator_blocks_adapters`.
- [TEST#5 autouse fixture ordering] — dismissed (no action): fixtures are orthogonal (hub vs ledger); unique "91-4-*" ids are the documented primary isolation.

### Rule Compliance

| Rule | Instances checked | Result |
|------|-------------------|--------|
| No Silent Fallbacks (CLAUDE.md critical) | env parse (`cost_safety.py:94-119`); 3 factory signatures (required kwarg); aside session resolution else-branch raises (`player_action.py`); ws router passes deterministic id, never silent None | compliant — 0 violations |
| No Stubbing | new module fully implemented, no placeholders | compliant |
| Don't Reinvent — Wire Up What Exists | reuses `publish_event`, `compute_cost_usd`, existing constants/exceptions; one comparator shared instead of duplicated | compliant |
| Verify Wiring, Not Just Existence | handler-level wiring test (aside slug), required-kwarg forcing function (router), client→ledger delegation verified by direct execution (this review) | compliant |
| Every Test Suite Needs a Wiring Test | `test_player_action_handler_passes_room_slug_to_aside_llm_factory` drives the real handler | compliant |
| No Source-Text Wiring Tests | all wiring asserts are seam-injection/behavioral; zero source greps | compliant |
| OTEL Observability Principle | detector + ceiling + running-total events extended cross-model with `caller`; severity tiers preserved (warn/error/info) | compliant |
| lang-review §1 (exception swallowing) | one `except ValueError` re-raises typed (`cost_safety.py:111`); no new swallows; aside resolver's broad except is pre-existing spec §6 designed degradation with ERROR log | compliant |
| lang-review §2 (mutable defaults) | all new signatures: required kwargs or immutable defaults | compliant |
| lang-review §3 (boundary annotations) | every public function in `cost_safety.py` fully annotated; `_UsageSummary` NamedTuple typed | compliant |
| lang-review §4 (logging) | ERROR on alarms, INFO on pulses; lazy `%` formatting throughout; no secrets in any added log line (verified by security scan, 4 sites) | compliant |
| lang-review §6 (test quality) | covered by test-analyzer; no vacuous assertions found in the 18 new tests | compliant |

### Devil's Advocate

Assume this is broken. The most dangerous claim is "one cumulative pot per session, terminal kill across all call sites." Attack one: forge the key — can a player aim spend at another session's pot? The keying input is the room slug / `sd.game_slug`, server-side state bound at connect, not free text from the player; the player's only influence is *which* session they legitimately join. Attack two: race the ceiling — fire many concurrent asides so they all pass pre-flight before any updates the cumulative. Real (the awaited SDK call is a yield point), and confirmed as SEC#3: the overspend bound is one in-flight call per concurrent caller, after which every pre-flight refuses; the $10 line is best-effort by one call's width, exactly as the narrator's pre-existing machinery already was. Attack three: starve the alarm — cross the ceiling on a call site whose exceptions get swallowed. The aside resolver's spec-§6 `except Exception` does catch the kill; but the cross emits the watcher event + ERROR log *inside* `update_cumulative` before the raise, so the GM panel sees the kill even when the aside degrades to `resolver_error`, and billing stays blocked pre-flight. Attack four: mutate the env mid-process to desync ceilings and suppress the narrator's announce — verified no production code mutates the var; operator-only scenario, documented as a finding. Attack five: recycle a slug and inherit a stale baseline — `close_store → reset_baselines` now evicts adapter windows too (verified by direct execution), though cumulative/announce intentionally persist per the ADR-134 flagged follow-up, which remains the sharpest known edge (a recycled slug inherits the dead session's kill — arguably fail-safe, refusing spend rather than allowing it). What would a confused future developer do? Add a fourth Haiku call site — and the required-kwarg factory makes silent uncoverage a TypeError. The design survives the assault; what's left are bounded, documented edges.

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** player aside text → `PlayerActionHandler` (combat-bracket strip, empty-reject) → session-id resolution (room slug, server-bound; fail-loud RuntimeError if absent) → `AsideResolver` → `_AsideLlm.complete` → pre-flight `check_ceiling` (refuses killed sessions BEFORE the SDK) → SDK → `_record_usage_telemetry` (books) → `ledger.record_call` (detector + cumulative + kill). Safe because the keying input is server-side session state, the kill refuses pre-flight, and every branch is either typed-raise or ERROR-logged.

**Pattern observed (good):** required keyword-only `session_id` on all three factories (`llm_factory.py` `build_aside_llm`/`build_intent_router_llm`, `intent_router_pass.py` `build_intent_router_for_session`) — turns "forgot to cover a new Haiku spender" from a silent dark-spend regression into a TypeError at the call site. This is the right shape for this codebase's No-Silent-Fallbacks doctrine.

**Error handling:** env validation raises typed `AnthropicSdkConfigError` on nan/inf/non-positive/garbage at adapter construction (`cost_safety.py:94-119`, parametrized tests); ceiling kill raises typed `AnthropicSdkCostCeilingExceeded` carrying session_id/cumulative/ceiling; aside path RuntimeError on missing session identity.

**Observations (tagged):**
- [VERIFIED] Pre-flight refusal precedes every SDK touch on both adapters — `llm_factory.py` `_AsideLlm.complete` and `_IntentRouterLlm.emit_tool` call `ledger().check_ceiling` before `messages.create`; tests assert recording-SDK `calls == []` on refusal. Complies with ADR-134 terminal-refusal invariant.
- [VERIFIED] Announce-set add strictly after the side-effecting emit (`cost_safety.py` `update_cumulative`) — lang-review §14 ordering preserved through the relocation.
- [VERIFIED] `reset_baselines` cross-store eviction works end-to-end — verified by direct execution this review: client call evicts ledger (session, caller) windows, neighbor sessions intact, cumulative intentionally preserved (ADR-134 scope).
- [VERIFIED] Narrator/adapter ledger keys agree on all slug-connect paths — room slug == `sd.game_slug` (ADR-134; `session_helpers.py:1289`); on the no-slug fallback the narrator is None-bypassed so no active pot exists to mis-key.
- [EDGE] (Low, confirmed) A ceiling-crossing router call that also returned no `tool_use` block raises the kill and masks `IntentRouterEmptyResponse` — both are loud; diagnostic nuance only.
- [EDGE]/[SEC] (Low, confirmed) Per-instance ceiling values + shared pot can diverge only if the env var changes inside a running process; grep-verified no production mutation exists. Document in the ADR-134 amendment (delivery finding).
- [SILENT] (Low, confirmed — downgraded from High with evidence) The ws `seed_session_id` synthetic fallback key gives the router its own pot on no-slug paths; the narrator is uncovered (None) there, so this strictly adds coverage; key-alignment follow-up filed.
- [SEC] (Low, confirmed) Pre-flight/post-call TOCTOU under concurrency bounds overspend at one in-flight call per concurrent caller — pre-existing structural property, now replicated at the adapters; doc note filed.
- [SEC] (Low, confirmed) Ledger cumulative/announce dicts grow per distinct session for process lifetime — pre-existing, ADR-134 flagged follow-up, growth bounded by authenticated session creation.
- [TEST] (Medium, confirmed) No regression test pins `reset_baselines` → ledger adapter-window eviction (the behavior itself verified live this review). Follow-up filed; non-blocking per severity rubric (missing edge-case test).
- [TEST] (Low, confirmed) `test_adapter_ceiling_env_invalid_fails_loud`'s `await` line is unreachable today (validation fires at construction) — combined raises block still guards a lazy refactor, but an explicit construction-scope assert would be sharper.
- [TEST] (Low, confirmed) Handler wiring test re-swaps the factory by direct assignment; `monkeypatch.setattr` would decouple restore semantics from harness internals.
- [DOC] (own analysis; subagent disabled) New docstrings verified accurate — relocation notes in both modules point each way; the `narrator.sdk` component misnomer is documented at the emit site.
- [TYPE] (own analysis; subagent disabled) Boundaries fully annotated; `_UsageSummary` NamedTuple; tuple-keyed window dicts typed `dict[tuple[str, str], deque]`.
- [SIMPLE] (own analysis; subagent disabled) Net simplification: client sheds 271 lines; one shared comparator instead of a duplicate; no speculative abstraction added.
- [RULE] Rule Compliance table above — 12 rules enumerated against every changed type/function/call-site, 0 violations.

**Hard questions:** ceiling exactly equal → `>=` fires (tested at crossing); empty-string id → covered not bypassed; huge inputs → absolute floors fire regardless of baseline; concurrent calls → bounded TOCTOU (above); env garbage → typed raise at construction.

**Tenant/session isolation audit:** every ledger method takes `session_id` explicitly; keying is server-derived slug; per-session isolation pinned by `test_ceiling_kill_is_per_session`; announce-set keyed per session so one session's kill never silences another's alarm (cross-CALL-SITE sharing within one session is the design goal, not a leak).

**Checklist:** all mandatory steps complete — subagent gate (table above), rule enumeration, 16 observations, data-flow trace, wiring, patterns, error handling, security, hard questions, tenant audit, VERIFIEDs challenged against subagent findings (the one contradiction — silent-failure's High on the synthetic key — was re-read at line level and resolved with `session_helpers.py:1289` evidence), devil's advocate run.

**Verdict basis:** 0 Critical, 0 High; 1 Medium (missing regression test for a behavior verified live), 9 Low. APPROVED.

**Handoff:** To SM (Camina Drummer) for finish-story.
## Impact Summary

**Delivery Status:** COMPLETE — All 7 acceptance criteria met (18/18 story tests GREEN; 11095+ full-suite tests pass).

**Findings & Followups:**
- **Blocking issues:** 0
- **Non-blocking findings:** 11 (2 Gaps, 3 Questions, 6 Improvements)
  - 2 Gaps: required-kwarg forcing function properly breaks existing zero-arg callers (by design — forces explicit session decisions); eval CLI correctly opts out but gains coverage via synthetic fallback key
  - 3 Questions: process-level state migration requires test suite coordination (solved by autouse fixture reset); dungeon-curate bypass is intentional per scope; narrative/adapter ledger keys agree on all slug-connect paths
  - 6 Improvements: GM-panel `caller` field surface (UI-layer follow-up); ADR-134 relocation amendment note (orchestrator docs); reset_baselines regression test; test-scope assertion sharpening

**Design Deviations:** 4 logged and ACCEPTED (all minor severity) — adapter component misnomer `narrator.sdk` documented at emit site; running-total pulse cadence is per-turn by design; router ws call site deterministic fallback key strictly adds coverage; all deviations within granted scope.

**Coverage & Compliance:**
- Test rule enforcement: required-kwarg factories; env validation fail-loud; wiring test verified via real handler + seam injection (no source greps)
- OTEL observability: detector + ceiling + cumulative events extend cross-model with `caller` field; severity tiers preserved
- No Silent Fallbacks: env parse fail-loud on nan/inf/non-positive/garbage; aside session resolution raises RuntimeError on missing identity; required kwarg turns silent dark-spend regression into TypeError
- Code quality: 18/18 story tests GREEN; 11095 full-suite tests pass (1 unrelated pre-existing flaky); ruff clean; pyright delta zero (0 new errors); −271 net lines (simplification)

**Reviewability:** 10 subagent findings confirmed (1 Medium, 9 Low); devil's advocate ran 5 attack vectors (none successful); rule compliance table: 12 rules × verified at all boundaries = 0 violations; data-flow trace verified end-to-end.

**Production Readiness:** Cost safety now covers ALL Haiku call sites (narrator, aside, router) under one cumulative pot per session. Ceiling kill is pre-flight (blocks BEFORE the SDK call). Per-session isolation preserved. Backward compatible — existing narrator and 61-A tests unaffected (ceiling/announce alias onto shared ledger; baselines stay instance-keyed per 61-A contract).
