---
story_id: "117-6"
jira_key: ""
epic: "117"
workflow: "tdd"
---
# Story 117-6: Un-seeded narrator-objective classifier

## Story Details
- **ID:** 117-6
- **Jira Key:** (none — Jira not configured)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-15T11:43:36Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-15T10:56:38Z | 2026-06-15T11:00:41Z | 4m 3s |
| red | 2026-06-15T11:00:41Z | 2026-06-15T11:10:45Z | 10m 4s |
| green | 2026-06-15T11:10:45Z | 2026-06-15T11:20:55Z | 10m 10s |
| review | 2026-06-15T11:20:55Z | 2026-06-15T11:30:00Z | 9m 5s |
| green | 2026-06-15T11:30:00Z | 2026-06-15T11:36:17Z | 6m 17s |
| review | 2026-06-15T11:36:17Z | 2026-06-15T11:43:36Z | 7m 19s |
| finish | 2026-06-15T11:43:36Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

### TEA (test design)
- **Gap** (blocking): No factory exists to build the classifier's `ObjectiveClassifierLLM`. Affects `sidequest/agents/llm_factory.py` (Dev must add a `build_*` builder mirroring `build_intent_router_llm` at line 602 — a forced single-tool `emit_tool` Haiku-via-SDK adapter — and call it from `websocket_session_handler.py::_execute_narration_turn` to construct the `llm` passed to `run_unseeded_objective_classifier_watcher`). The injectable LLM is faked in tests; production needs the real adapter wired or the watcher can never fire. *Found by TEA during test design.*
- **Gap** (blocking): AC-4 (ADR-146 addendum + cost analysis) has no automated test and is a doc deliverable. Affects `docs/adr/ADR-146*` / a new spec under `docs/superpowers/specs/`. Dev/Architect must document the per-turn Haiku classification cost and the activation policy (the tests pin the cheap gates — skip on minted quest / router-seeded / empty narration — but the "drama-tier / always-on" policy from AC-4 is a written decision, not a test). *Found by TEA during test design.*
- **Question** (non-blocking): Precedence between the new classifier and the retained keyword backstop on the SAME un-seeded turn is left to Dev. The sync `run_unminted_objective_watcher` keyword path and the new async classifier could both beep. AC-3 says "prefer the classifier; keyword is emergency backstop only" — tests do NOT pin no-double-fire (too handler-scoped to drive deterministically in RED). Affects `websocket_session_handler.py` post-narration block (Dev decides whether the classifier path suppresses the keyword backstop, e.g. only run the keyword path when the classifier LLM is unavailable). *Found by TEA during test design.*
- **Improvement** (non-blocking): The 117-4 router-backed seeded path emits the span without a `detection_method`, so once the field defaults to `"keyword"` it will mislabel router-backed spans as keyword. Affects `sidequest/agents/dispatch_engagement_watcher.py::run_unminted_objective_watcher` (a follow-up could tag the router path `detection_method="router"`). AC-2 only requires classifier-vs-keyword, so this is out of 117-6 scope but worth a follow-up so the GM panel isn't misled. *Found by TEA during test design.*

### Dev (implementation)
- **Question** (non-blocking): Double-fire is NOT suppressed (TEA's precedence Question, now decided). On an un-seeded objective turn whose narration ALSO trips a curated `_UNMINTED_OBJECTIVE_MARKERS` phrase, the sync `run_unminted_objective_watcher` (keyword, default `detection_method="keyword"`) AND the async classifier (`detection_method="classifier"`) both beep — two spans for one objective. I chose minimalism: no test requires suppression and the two spans carry distinct `detection_method` so the GM panel can dedupe/prefer the classifier. AC-3's "prefer the classifier, keyword is emergency backstop only" is honored at the *labelling* layer, not by gating one watcher off the other. Affects `sidequest/server/websocket_session_handler.py` post-narration block (a follow-up could run the keyword sync path only when the classifier LLM is unavailable). *Found by Dev during implementation.*
- **Improvement** (non-blocking): The classifier `llm` is built eagerly every turn via `build_unseeded_objective_classifier_llm(...)` even when the watcher's cost gates skip the actual Haiku call. Adapter construction is cheap (SDK ref + ceiling parse, no API call) and matches how `build_intent_router_llm` is constructed per turn, but a lazy build-inside-watcher (behind the gates) would avoid the per-turn allocation. Affects `sidequest/server/websocket_session_handler.py` (only worth it if profiling shows it matters). *Found by Dev during implementation.* *(Note: the ADR-146 cost addendum was committed in the orchestrator repo, commit 3bfb6d97, not on the server feature branch.)*

### Reviewer (code review)
- **Gap** (blocking): `ruff format` fails on `sidequest/server/websocket_session_handler.py:1194` — the `llm=build_unseeded_objective_classifier_llm(session_id=seed_session_id)` arg was hand-wrapped but fits on one line. A failing format gate blocks merge. Fix: `uv run ruff format sidequest/server/websocket_session_handler.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `narration` is sent to Haiku with no length bound; the sibling `infer_archetype_from_freeform` truncates at 4,000 chars. Affects `sidequest/agents/post_narration_classifier.py::classify_unseeded_objective` (a runaway-long narration incurs unbounded input-token cost — Cost Scales with Drama). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The new `_UnseededObjectiveClassifierLlm.emit_tool` accesses `block.name`/`block.input` without narrowing the SDK content union, adding ~20 pyright errors (matches the existing `_IntentRouterLlm` house pattern; develop already carries 40). Affects `sidequest/agents/llm_factory.py` (an `isinstance(block, ToolUseBlock)` narrow fixes it and is strictly more correct than the siblings). *Found by Reviewer during code review.* → *Round 2: Dev kept the robust house-pattern (documented); accepted as LOW debt.*
- **Improvement** (non-blocking, Round 2): The `_extract_unminted_objective` inline comment (`sidequest/telemetry/spans/dispatch_engagement.py:~233`) still describes only two `detection_method` values ("classifier" vs "keyword") — it omits the new "router" value the rework added. The extract CODE is correct (passes through whatever is stored); only the comment is incomplete. A one-line sweep aligns it with the span docstring above. *Found by Reviewer during re-review.*
- **Improvement** (non-blocking, Round 2): The new `test_sync_watcher_tags_router_path_router` would be more mutation-resistant with a premise guard asserting the narration trips ZERO `_UNMINTED_OBJECTIVE_MARKERS` (mirroring `test_fires_on_open_ended_hook_via_classification`), so the span can only fire via the router path. Behaviorally sound as-is; this is belt-and-suspenders. Affects `tests/telemetry/test_unminted_objective_detection_method.py`. *Found by Reviewer during re-review.*

## Impact Summary

**Upstream Effects:** 1 findings (0 Gap, 0 Conflict, 0 Question, 1 Improvement)
**Blocking:** None

- **Improvement:** `narration` is sent to Haiku with no length bound; the sibling `infer_archetype_from_freeform` truncates at 4,000 chars. Affects `sidequest/agents/post_narration_classifier.py::classify_unseeded_objective`.

### Downstream Effects

- **`sidequest/agents`** — 1 finding

### Deviation Justifications

5 deviations

- **Pinned a separate async watcher instead of an inline classify call in the handler**
  - Rationale: keeps the cost gates + non-fatal try/except + span emission testable in isolation (the handler block is huge and async-heavy); matches the established lie-detector watcher pattern so the wiring AST test mirrors 117-4's `test_live_handler_passes_router_package_to_watcher`
  - Severity: minor
  - Forward impact: Dev wires one `await run_unseeded_objective_classifier_watcher(...)` call rather than an inline block; the LLM is built via a factory (see Delivery Findings) not constructed inline
- **Pure classifier takes `narration` + injectable `llm`, not `game_state` + `has_pending_quest_offer`**
  - Rationale: separation of concerns — the classifier is the LLM call (fakeable with an `AsyncMock`, mirrors `IntentRouter(llm=...)`); the watcher owns the gates. `game_state` isn't needed by the prose classifier itself
  - Severity: minor
  - Forward impact: Dev injects the LLM (test parity with intent_router); gating logic is in the watcher, not the classifier
- **Cost gate defers on ANY router `quest_offer` dispatch, not just `accept`**
  - Rationale: a `quest_offer` of any decision means the router classified this turn as SEEDED (quest-related) — it is by definition not the un-seeded/router-silent case the classifier exists for. Deferring on decline too avoids spending a Haiku call on a turn the router already understood, and the sync path already handles decline correctly (stays silent). Broader-but-cheaper and semantically cleaner than mirroring the accept-only helper.
  - Severity: minor
  - Forward impact: none — strictly narrows when the classifier spends a call; no test asserts the decline case either way
- **Rework: tagged the 117-4 sync router path `detection_method="router"` (new third value)**
  - Rationale: the Reviewer offered this as the fix for the honesty MEDIUM; it stops the GM panel mislabeling router-structural hits as keyword. Resolves the TEA-deferred Improvement in the same pass.
  - Severity: minor
  - Forward impact: positive — GM-panel attribution is now correct across all three detection paths
- **Rework: kept the `getattr(block,"type")=="tool_use"` extraction (did NOT add isinstance narrowing)**
  - Rationale: the getattr/`"tool_use"` check is robust to SDK content-union type variants (beta block types) where an `isinstance` against a specific class could silently miss the happy path; matching the established working pattern beats a type-checker-cosmetic change that diverges from siblings. pyright is already non-clean on develop (40 standing errors); this is accepted house-pattern debt, not a regression in behavior.
  - Severity: trivial
  - Forward impact: none — a future repo-wide pass could narrow all four call sites together

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Pinned a separate async watcher instead of an inline classify call in the handler**
  - Spec source: context-story-117-6.md, Technical Approach §2 (Integration Point)
  - Spec text: pseudocode shows an inline `if not game_state.pending_quest_offers: classification = await classify_unseeded_objective(...)` block written directly into `websocket_session_handler.py`
  - Implementation: tests pin a dedicated async `run_unseeded_objective_classifier_watcher(*, narration, snapshot, llm, package, tracer)` in the new module, awaited from the handler — mirroring the existing sync `run_unminted_objective_watcher` / `run_improvised_combat_watcher` / `run_fate_engagement_watcher` post-narration watcher family (websocket_session_handler.py:1146-1186)
  - Rationale: keeps the cost gates + non-fatal try/except + span emission testable in isolation (the handler block is huge and async-heavy); matches the established lie-detector watcher pattern so the wiring AST test mirrors 117-4's `test_live_handler_passes_router_package_to_watcher`
  - Severity: minor
  - Forward impact: Dev wires one `await run_unseeded_objective_classifier_watcher(...)` call rather than an inline block; the LLM is built via a factory (see Delivery Findings) not constructed inline
- **Pure classifier takes `narration` + injectable `llm`, not `game_state` + `has_pending_quest_offer`**
  - Spec source: context-story-117-6.md, Technical Approach §1 (New Classifier Module)
  - Spec text: `async def classify_unseeded_objective(narration, game_state, has_pending_quest_offer) -> UnseededObjectiveClassification`
  - Implementation: the PURE classifier is `classify_unseeded_objective(*, narration, llm)` (decides purely from prose via an injectable `ObjectiveClassifierLLM` `emit_tool` Protocol, ADR-102); the un-seeded/cost gating (`has_pending_quest_offer`, empty quest_log) moves UP into the async watcher where the snapshot/package live
  - Rationale: separation of concerns — the classifier is the LLM call (fakeable with an `AsyncMock`, mirrors `IntentRouter(llm=...)`); the watcher owns the gates. `game_state` isn't needed by the prose classifier itself
  - Severity: minor
  - Forward impact: Dev injects the LLM (test parity with intent_router); gating logic is in the watcher, not the classifier

### Dev (implementation)
- **Cost gate defers on ANY router `quest_offer` dispatch, not just `accept`**
  - Spec source: TEA test `test_watcher_defers_to_seeded_router_path` (tests only the `accept` case) + context-story-117-6.md AC-1 (un-seeded = "no quest_offer present")
  - Spec text: the test injects a `quest_offer accept` package and asserts the classifier defers; the sync 117-4 helper `_package_accepted_quest_offer` gates on `decision == "accept"` only
  - Implementation: the classifier watcher's `_package_has_quest_offer` defers on ANY `quest_offer` dispatch (accept OR decline), not accept-only
  - Rationale: a `quest_offer` of any decision means the router classified this turn as SEEDED (quest-related) — it is by definition not the un-seeded/router-silent case the classifier exists for. Deferring on decline too avoids spending a Haiku call on a turn the router already understood, and the sync path already handles decline correctly (stays silent). Broader-but-cheaper and semantically cleaner than mirroring the accept-only helper.
  - Severity: minor
  - Forward impact: none — strictly narrows when the classifier spends a call; no test asserts the decline case either way
- **Rework: tagged the 117-4 sync router path `detection_method="router"` (new third value)**
  - Spec source: Reviewer MEDIUM finding [DOC] + TEA deferred Improvement (router path mislabel)
  - Spec text: AC-2 requires only classifier-vs-keyword; the router path previously emitted with no method (defaulting to "keyword")
  - Implementation: `run_unminted_objective_watcher` now computes `"router" if _package_accepted_quest_offer(package) else "keyword"`; the span docstring lists three methods. New tests in test_unminted_objective_detection_method.py lock router→"router" and keyword→"keyword".
  - Rationale: the Reviewer offered this as the fix for the honesty MEDIUM; it stops the GM panel mislabeling router-structural hits as keyword. Resolves the TEA-deferred Improvement in the same pass.
  - Severity: minor
  - Forward impact: positive — GM-panel attribution is now correct across all three detection paths
- **Rework: kept the `getattr(block,"type")=="tool_use"` extraction (did NOT add isinstance narrowing)**
  - Spec source: Reviewer LOW finding (pyright +20 on the new emit_tool)
  - Spec text: Reviewer suggested `isinstance(block, ToolUseBlock)` to clear the 20 new pyright errors (optional)
  - Implementation: left the `getattr`-based extraction, consistent with all three sibling adapters (`_IntentRouterLlm`, archetype inference)
  - Rationale: the getattr/`"tool_use"` check is robust to SDK content-union type variants (beta block types) where an `isinstance` against a specific class could silently miss the happy path; matching the established working pattern beats a type-checker-cosmetic change that diverges from siblings. pyright is already non-clean on develop (40 standing errors); this is accepted house-pattern debt, not a regression in behavior.
  - Severity: trivial
  - Forward impact: none — a future repo-wide pass could narrow all four call sites together

### Reviewer (audit)
- **TEA: separate async watcher instead of inline classify** → ✓ ACCEPTED by Reviewer: mirrors the established `run_*_watcher` family; keeps cost gates + non-fatal contract testable. Sound.
- **TEA: pure classifier takes `narration` + injectable `llm`** → ✓ ACCEPTED by Reviewer: matches the `IntentRouter(llm=...)` fakeable seam; clean separation. Sound.
- **Dev: cost gate defers on ANY `quest_offer` (accept OR decline)** → ✓ ACCEPTED by Reviewer: deferring the un-seeded classifier on any router quest signal is strictly cheaper and semantically correct — a quest_offer of any decision is the seeded domain. No test contradicts it.
- **UNDOCUMENTED (Reviewer):** the new `narration_unminted_objective_span` docstring asserts `detection_method="keyword"` (default) represents "the legacy `_UNMINTED_OBJECTIVE_MARKERS` substring backstop" — but the seeded 117-4 router path (`run_unminted_objective_watcher`, dispatch_engagement_watcher.py:~748) calls the span with NO `detection_method`, so router-seeded hits are ALSO tagged `"keyword"`. The docstring overclaims; this divergence was not logged. Severity: M (see finding D3). → **Round 2: RESOLVED** — Dev now tags the router path `"router"` and the docstring lists three methods; rule-checker + comment-analyzer confirm correct.
- **Dev rework: tagged the router path `detection_method="router"`** → ✓ ACCEPTED by Reviewer (Round 2): exactly the honesty fix requested; verified correct (`_package_accepted_quest_offer` gate) with two new locking tests.
- **Dev rework: kept the `getattr` tool_use extraction (no isinstance narrow)** → ✓ ACCEPTED by Reviewer (Round 2): the getattr/`"tool_use"` check is robust to SDK content-union variants and consistent with all three sibling adapters; the +20 pyright errors are accepted house-pattern debt (develop already carries 40), a LOW/optional finding. Sound engineering call.

Story 117-6 follows 117-4 (approved 2026-06-14). Keith ruled Option A: the intent router is pre-narration and player-turn-scoped, so it has NO signal for un-seeded narrator-initiated objectives (no pending_quest_offer). 117-4 hardened the SEEDED path (quest_offer signal) and retained the 13-phrase `_UNMINTED_OBJECTIVE_MARKERS` keyword matcher as a provisional backstop. This story replaces that brittle backstop with a real post-narration classifier so `narration.unminted_objective.suspected` fires on open-ended hooks regardless of phrasing.

**Technical approach:**
1. New `post_narration_classifier.py` module with `classify_unseeded_objective()` Haiku pass
2. Integration: call classifier post-narration in websocket_session_handler.py (after narrator, before emission)
3. OTEL: emit `narration.unminted_objective.suspected` span with detection_method="classifier"
4. Deprecation: mark `_UNMINTED_OBJECTIVE_MARKERS` keyword path as fallback (keep code, add comment)
5. ADR-146 addendum: document cost analysis (Haiku per-turn classification vs. keyword free cost)

See full technical spec at `sprint/context/context-story-117-6.md`.

## Branch Strategy
**Branch Strategy:** gitflow (feat/117-6-unseeded-narrator-objective-classifier)

## OTEL Observability Requirement
Per CLAUDE.md OTEL Observability Principle: every subsystem fix MUST add OTEL events.
- `narration.unminted_objective.suspected` span must emit with detection_method field
- Span routing already exists in SPAN_ROUTES (117-4); verify and enhance routing
- GM panel lie-detector must distinguish classifier path from keyword fallback

## Sm Assessment

**Routing:** TDD (phased) → TEA (Amos Burton) for the RED phase. 8-pt server-only story, no cross-repo coupling, no stack parent.

**Scope is well-bounded by 117-4.** The seeded path is already hardened; this story is squarely the un-seeded backstop replacement. The brittle `_UNMINTED_OBJECTIVE_MARKERS` 13-phrase matcher is the thing to kill — TEA should write failing tests that assert detection on open-ended objective hooks whose phrasing is *deliberately absent* from the keyword list (the noir "discreet job" case is the canonical fixture). That's the test that proves the keyword path can't pass and forces the real classifier.

**Watch items for the RED phase:**
- **Cost-Scales-with-Drama tension.** A per-turn Haiku classification on every narration is a real cost. Tests should pin down *when* the classifier runs — it must not fire on quiet, objective-free narration. A gate (only classify when narration plausibly introduces a hook) is part of the contract, not an afterthought. Sebastien/Jade are mechanics-first players, but this is a Keith/dev observability concern — the GM panel is the consumer, not a player surface.
- **OTEL is acceptance, not garnish.** `narration.unminted_objective.suspected` with `detection_method` (classifier vs keyword-fallback) must be assertable in tests. The GM panel is the lie-detector that proves the classifier engaged rather than Claude improvising.
- **ADR-146 addendum + cost analysis are deliverables**, not optional. Flag to Architect if a design pass is needed before green — but the testable behavior can be specced first.
- **Don't delete the keyword path yet.** Story says it "must ultimately die" — but verify the classifier subsumes it before ripping it out. Demote to fallback in this story; full removal can be a follow-up if the classifier needs soak time.

**No blockers.** Server repo clean on `feat/117-6-...` (base: develop). Handing to TEA.

---

## TEA Assessment

**Tests Required:** Yes
**Status:** RED confirmed — 18 failing by feature-absence, 1 passing (AC-3 keyword-retention guard, must stay green)

**Test Files:**
- `tests/agents/test_unseeded_objective_classifier.py` — pure classifier unit behavior (AC-1), injectable-LLM `AsyncMock` fake mirroring `test_intent_router.py` (no live API)
- `tests/telemetry/test_unminted_objective_detection_method.py` — span carries `detection_method` + SPAN_ROUTES extract surfaces it (AC-2)
- `tests/server/test_unseeded_objective_classifier_wiring.py` — async watcher + cost gates + handler wiring (AC-5) + keyword retention (AC-3)

**Tests Written:** 19 tests covering 5 ACs.

**Coverage map:**
| AC | Tests |
|----|-------|
| AC-1 un-seeded detection via real classification (not keywords) | `test_classifier_module_and_function_exist`, `test_classification_dataclass_shape`, `test_fires_on_open_ended_hook_via_classification` (premise-guards ZERO marker hits), `test_silent_on_quiet_prose`, `test_confidence_is_surfaced_from_llm` |
| AC-2 OTEL span routing + detection_method | `test_span_accepts_and_records_classifier_detection_method`, `test_span_defaults_detection_method_to_keyword_for_legacy_path`, `test_span_route_extract_surfaces_detection_method`, `test_watcher_emits_classifier_span_on_open_ended_hook` |
| AC-3 keyword matcher retained as backstop | `test_keyword_backstop_symbol_retained` (green now, regression guard) |
| AC-4 cost analysis | cheap-gate behavior pinned (`test_empty_narration_skips_llm_call`, `test_watcher_skips_llm_when_quest_already_minted`, `test_watcher_defers_to_seeded_router_path`, `test_watcher_skips_llm_on_empty_narration`); the written ADR addendum/policy is a Dev deliverable — see Delivery Findings |
| AC-5 wiring | `test_classifier_watcher_is_async`, `test_classifier_watcher_imported_into_session_handler`, `test_live_handler_awaits_classifier_watcher` (AST await inspection, not source-grep), `test_watcher_silent_when_classifier_says_no_objective`, `test_watcher_swallows_classifier_failure` (non-fatal contract) |

### Rule Coverage (.pennyfarthing/gates/lang-review/python.md + CLAUDE.md)

| Rule | Test(s) | Status |
|------|---------|--------|
| Every Test Suite Needs a Wiring Test | `test_classifier_watcher_imported_into_session_handler`, `test_live_handler_awaits_classifier_watcher` | failing (RED) |
| No Source-Text Wiring Tests (AST/reflection, not grep) | wiring tests parse the handler AST for an `await` call; module-namespace `__dict__` reflection — no `read_text()` | satisfied |
| No Silent Fallbacks / observability non-fatal | `test_watcher_swallows_classifier_failure` (classifier error caught, turn survives) | failing (RED) |
| Cost Scales with Drama (SOUL) | 4 cost-gate tests assert `emit_tool.await_count == 0` on skip paths | failing (RED) |
| Deterministic LLM tests (no live API) | injectable `ObjectiveClassifierLLM` faked via `AsyncMock`, mirrors `test_intent_router.py` | satisfied |
| Meaningful assertions (no vacuous) | every test asserts a value/attr/await-count, not `is_not None` alone | satisfied |

**Rules checked:** 6 of 6 applicable. **Self-check:** 0 vacuous tests (no `let _ =`/`assert True`/always-None checks).

**Handoff:** To Dev (Naomi Nagata) for GREEN. Two blocking Delivery Findings need attention during implementation: (1) add a `build_*` factory for the classifier LLM in `llm_factory.py` and wire the `await` into `_execute_narration_turn`; (2) write the AC-4 ADR-146 cost addendum. The async-watcher shape and pure-classifier signature deviate from the context pseudocode (see Design Deviations) — these are deliberate, pattern-consistent choices; Dev may adjust with a logged deviation.

---

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (server, on `feat/117-6-unseeded-narrator-objective-classifier`, commit b6db6579):**
- `sidequest/agents/post_narration_classifier.py` (NEW) — `ObjectiveClassifierLLM` Protocol, `UnseededObjectiveClassification` dataclass, async `classify_unseeded_objective` (empty-narration short-circuit, no SDK spend), and async `run_unseeded_objective_classifier_watcher` (cost gates + classifier-tagged span + non-fatal try/except)
- `sidequest/agents/llm_factory.py` — `_UnseededObjectiveClassifierLlm` adapter (bare-string system below cache floor; caller `unseeded_objective_classifier`; ADR-134 ceiling/ledger) + `build_unseeded_objective_classifier_llm` factory
- `sidequest/telemetry/spans/dispatch_engagement.py` — `detection_method` param on `narration_unminted_objective_span` (default `"keyword"`) + surfaced in the SPAN_ROUTES extract
- `sidequest/server/websocket_session_handler.py` — imports + `await run_unseeded_objective_classifier_watcher(...)` in the post-narration block of `_execute_narration_turn`
- `sidequest/agents/dispatch_engagement_watcher.py` — AC-3 deprecation comment on `_UNMINTED_OBJECTIVE_MARKERS` (retained, non-primary backstop, ADR-146 pointer)

**Doc deliverable (orchestrator, on `main`, commit 3bfb6d97):**
- `docs/adr/146-quest-seed-authoring-contract.md` — AC-4 addendum: classifier rationale + cost-analysis table

**Tests:** 472/472 passing (GREEN) — 41 in the 117-6 + pre-existing unminted-objective files, 431 in the telemetry + dispatch-engagement regression sweep. Lint clean (ruff), pyright clean on the new module. No regressions.

**AC status:** AC-1 ✓ (classifier, keyword-free) · AC-2 ✓ (detection_method span + route) · AC-3 ✓ (keyword retained + deprecation comment) · AC-4 ✓ (ADR-146 addendum + cost analysis) · AC-5 ✓ (awaited in handler; AST + reflection wiring tests green)

**Handoff:** To Reviewer (Chrisjen Avasarala). Note two non-blocking findings for review attention: (1) double-fire between the keyword backstop and the classifier is left unsuppressed by design (distinct `detection_method` labels); (2) the ADR-146 addendum lives in the orchestrator repo, not the server feature branch — review it there if checking AC-4.

---

## Subagent Results — Round 1 (REJECTED, superseded by Round 2 below)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 2 (format FAIL, pyright +20) | confirmed 2, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — assessed by Reviewer (see [EDGE]) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — assessed by Reviewer (see [SILENT]) |
| 4 | reviewer-test-analyzer | Yes | findings | 6 | confirmed 2, downgraded 2, deferred 2 |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 | confirmed 1, dismissed 1, downgraded 1 |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — assessed by Reviewer (see [TYPE]) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings — assessed by Reviewer (see [SEC]) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — assessed by Reviewer (see [SIMPLE]) |
| 9 | reviewer-rule-checker | Yes | findings | 4 | confirmed 2, downgraded 1, deferred 1 |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 1 confirmed blocking (HIGH), 3 confirmed non-blocking (MEDIUM), several LOW/deferred

## Reviewer Assessment — Round 1 (REJECTED, superseded by Round 2 below)

**Verdict:** REJECTED

The implementation is well-structured, follows the established Intent Router/`run_*_watcher` patterns faithfully, all 472 tests are green, and ruff *lint* is clean — but a **failing `ruff format` gate** blocks merge, and the review surfaced three MEDIUM correctness/honesty items worth fixing in the same rework pass.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] [PREFLIGHT] | `ruff format` fails — the `llm=build_...(session_id=seed_session_id)` arg is hand-wrapped but fits on one line; failing format gate blocks merge | `sidequest/server/websocket_session_handler.py:1194` | `uv run ruff format sidequest/server/websocket_session_handler.py` |
| [MEDIUM] [TYPE][RULE] | `build_unseeded_objective_classifier_llm` return type is the **private** `_UnseededObjectiveClassifierLlm`; public factory should expose the public Protocol | `sidequest/agents/llm_factory.py:751` | Annotate return as `ObjectiveClassifierLLM` (the Protocol it satisfies) |
| [MEDIUM] [DOC] | Span docstring claims default `detection_method="keyword"` == legacy keyword backstop, but the seeded 117-4 router path also emits with no method → tagged `"keyword"`, mislabeling router hits on the GM panel | `sidequest/telemetry/spans/dispatch_engagement.py` docstring + `dispatch_engagement_watcher.py:~748` | Either tag the router path `detection_method="router"`, or correct the docstring to admit `"keyword"` covers both the literal backstop AND the router-seeded path |
| [MEDIUM] [TEST] | `test_watcher_swallows_classifier_failure` asserts only "does not raise" — does not assert the watcher-crashed OTEL span emits, so it can't tell a silent drop from a surfaced crash (OTEL Observability Principle) | `tests/server/test_unseeded_objective_classifier_wiring.py:~242` | Pass an `InMemorySpanExporter` tracer and assert the crashed span fired with `error_type` |
| [LOW] [SEC][RULE] | `narration` sent to Haiku unbounded; sibling `infer_archetype_from_freeform` truncates at 4,000 chars (cost exposure on runaway narration) | `sidequest/agents/post_narration_classifier.py:~120` | Optional: add a char bound + loud truncation log |
| [LOW] [TYPE] | new `emit_tool` accesses `block.name`/`block.input` without narrowing the SDK union → +20 pyright errors (matches existing house pattern; develop already has 40) | `sidequest/agents/llm_factory.py:~931` | Optional: `isinstance(block, ToolUseBlock)` narrow |

### Findings dispatched by source
- **[PREFLIGHT]** Tests 41/41 green; ruff lint clean; **ruff format FAILS** (handler) → HIGH blocker. Pyright +20 (consistent house pattern) → LOW.
- **[EDGE]** *(disabled — Reviewer assessed)* `[VERIFIED]` Boundary inputs are handled: empty/blank narration short-circuits (`if not narration.strip()`) at `post_narration_classifier.py:120` with `await_count==0`; `None`/missing `quest_log` guarded via `getattr(snapshot, "quest_log", None) or {}` at :184; missing LLM dict keys default via `.get(..., 0.0/False)` at :138-141. No unhandled boundary found.
- **[SILENT]** *(disabled — Reviewer assessed)* `[VERIFIED]` The lone `except Exception` (:208) is the intended non-fatal observability contract — logged at ERROR with `exc_info=True` AND surfaced as a watcher-crashed span. Not a silent swallow. The classifier's own exceptions propagate up to it (no inner suppression).
- **[TEST]** CONFIRMED: crash-span not asserted (MEDIUM, above). DOWNGRADED: `test_keyword_backstop_symbol_retained` is a thin retention guard, but keyword-path *operability* is already covered green by `test_unminted_objective_watcher.py` + `test_unminted_objective_router_backed.py::test_keyword_backstop_fires_when_router_silent` — not a true coverage hole (LOW). DEFERRED: missing-confidence-key / whitespace-narration / extract-default edge tests (LOW polish).
- **[DOC]** CONFIRMED: the `"keyword"` default mislabels the router-seeded path (MEDIUM, above). DOWNGRADED: the deprecation-comment parenthetical ambiguity (LOW — readable in context). DISMISSED: "epic-91 trap" vs "incident" phrasing — paraphrase, not a factual error.
- **[TYPE]** *(disabled — Reviewer assessed)* CONFIRMED via rule-checker: private return type on the public factory (MEDIUM, above). `[VERIFIED]` The `ObjectiveClassifierLLM` Protocol and `UnseededObjectiveClassification` frozen dataclass are sound; LLM dict→dataclass coercion (`bool()`/`float()`) is defensive.
- **[SEC]** *(disabled — Reviewer assessed)* `[VERIFIED]` ADR-047 defense-in-depth present: narration wrapped in `<narration>…</narration>` and forced `tool_choice` is the injection boundary (`post_narration_classifier.py:124-131`). No SQL/eval/pickle/shell. The only gap is the unbounded length (LOW, above) — a cost, not an injection, vector.
- **[SIMPLE]** *(disabled — Reviewer assessed)* `[VERIFIED]` No dead code or over-engineering. `_package_has_quest_offer` is a small local predicate (justified — avoids importing a private cross-module helper). The new adapter mirrors `_IntentRouterLlm` without needless abstraction.
- **[RULE]** CONFIRMED: return-type (#3) and `narration` bound (#11) above. DOWNGRADED: AST wiring test flagged as "source-text" (#6) — accepted: `ast.parse(inspect.getsource(...))` is structural inspection (not the `read_text()`+catastrophic-backtrack-regex the rule targets) and is the SAME pattern as the merged 117-4 `test_live_handler_passes_router_package_to_watcher`. DEFERRED: `llm_factory.py` missing `__all__` (#10) — pre-existing debt, not introduced here.

### Rule Compliance (.pennyfarthing/gates/lang-review/python.md — 13 checks)
- **#1 silent exceptions:** PASS — the single `except Exception` is the logged + spanned non-fatal watcher contract (`noqa: BLE001` justified).
- **#2 mutable defaults:** PASS — all defaults `None`/immutable across the 6 new functions/methods.
- **#3 type annotations:** **FAIL** — public factory returns private `_UnseededObjectiveClassifierLlm` (should be the Protocol). All other signatures annotated.
- **#4 logging:** PASS — error path uses `logger.error(..., exc_info=True)` with `%s` lazy args, correct level (server-internal failure).
- **#5 path handling:** N/A — no file I/O.
- **#6 test quality:** PARTIAL — crash-span assertion missing (MEDIUM); AST wiring test accepted (precedent); minor edge gaps (LOW).
- **#7 resource leaks:** PASS — all spans/SDK calls in `with` context managers.
- **#8 unsafe deserialization:** PASS — `dict(block.input)` is SDK-validated forced tool output, not raw user input.
- **#9 async pitfalls:** PASS — every coroutine awaited (`classify`, `emit_tool`, handler call site); no blocking calls in async; no `gather`.
- **#10 import hygiene:** PARTIAL — `post_narration_classifier.py` has `__all__` ✓; `llm_factory.py` lacks `__all__` (pre-existing, deferred).
- **#11 input validation:** PARTIAL — ADR-047 delimiter + forced tool_choice ✓; no length bound on narration (LOW).
- **#12 dependency hygiene:** PASS — no dependency changes.
- **#13 fix regressions:** N/A — no fixes applied yet.

### Devil's Advocate

Assume this is broken. Start with the GM panel — the whole point of this story is the lie-detector, and the most damning thing I found is that it now *lies about itself*. The seeded 117-4 router path and the new classifier and the legacy keyword backstop all funnel into one span, and only the classifier sets a `detection_method`. So a router-structural hit and a brittle-substring hit are both stamped `"keyword"`. Keith opens the panel, sees `detection_method=keyword`, and concludes the brittle matcher fired when in fact the router caught it structurally — the exact "is the subsystem engaged or is Claude improvising?" question the OTEL principle exists to answer, now answered *wrong*. That's not cosmetic; it's the observability surface misreporting which engine ran. Next, cost: a player can't inject through the forced tool_choice, but a *runaway narrator* (context overflow, a genre with verbose prose) produces multi-thousand-char narration, and unlike `infer_archetype_from_freeform` there's no truncation — every un-seeded objective-eligible turn then bills full narration input on a second Haiku call stacked on top of the router. At a busy table that's real money the cost-observability sprint is supposed to be watching. Then failure modes: kill the Anthropic key mid-session and `emit_tool` raises — the watcher swallows it into a crash span and the turn survives (good), but the *test* doesn't prove the span emits, so a future refactor that drops the span would pass CI and silently blind the panel on every classifier crash. Confused-developer angle: the next person to call `build_unseeded_objective_classifier_llm` sees a return type of a private underscore class and has no idea it's a Protocol-satisfying swap point. And the format gate is red — a small thing, but it means this never passed the full check suite, which makes me wonder what else wasn't run. None of these are data-corruption Criticals, but the format failure is a hard gate, and the `detection_method` mislabel undermines the story's own reason to exist. Back to Dev.

**Handoff:** Back to Dev (Naomi Nagata) for green rework — fix the format gate (HIGH) and the three MEDIUM items (public return type, `detection_method` honesty for the router path, crash-span test assertion). LOW items (narration bound, pyright narrowing) are optional but recommended while you're in there.

---

## Dev Assessment (rework round 1)

**Implementation Complete:** Yes — all Reviewer findings addressed (commit `86d5653a`, pushed).

| Finding | Severity | Resolution |
|---------|----------|------------|
| ruff format fails on handler | HIGH | `ruff format` applied; `format --check` now passes (HIGH cleared) |
| factory returns private type | MEDIUM | returns `ObjectiveClassifierLLM` Protocol (TYPE_CHECKING import); pyright clean on the change |
| `detection_method` mislabels router path | MEDIUM | `run_unminted_objective_watcher` tags `"router"` vs `"keyword"`; docstring lists 3 methods; 2 new tests lock it |
| crash-span not asserted | MEDIUM | `test_watcher_swallows_classifier_failure` now asserts the `dispatch_engagement.watcher.crashed` span emits with `error_type` |
| narration unbounded | LOW | 4,000-char cap + loud truncation log in `classify_unseeded_objective` |
| pyright +20 (getattr) | LOW | **kept** the robust house-pattern getattr extraction (see Design Deviations — rationale: SDK union robustness + sibling consistency; accepted debt) |

**Tests:** 43/43 in the 117-6 set (+2 new router/keyword tests), 455 in the regression sweep — all green. Format + lint clean. `post_narration_classifier.py` pyright clean; `llm_factory.py` 60 (40 pre-existing baseline + 20 accepted house-pattern).

**Handoff:** Back to Reviewer (Chrisjen Avasarala) for re-review.

---

## Subagent Results

*(Re-review Round 2 — after rework commit `86d5653a`)*

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | format PASS, tests green, pyright +20 (accepted) | confirmed 0 blocking |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — assessed by Reviewer (see [EDGE]) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — assessed by Reviewer (see [SILENT]) |
| 4 | reviewer-test-analyzer | Yes | findings | 1 MEDIUM-conf (premise guard), rest sound | confirmed 1 LOW, rest dismissed |
| 5 | reviewer-comment-analyzer | Yes | findings | 1 (stale extract comment) | confirmed 1 LOW |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — assessed by Reviewer (see [TYPE]) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings — assessed by Reviewer (see [SEC]) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — assessed by Reviewer (see [SIMPLE]) |
| 9 | reviewer-rule-checker | Yes | clean | 0 violations / 13 checks | N/A — clean |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 0 blocking; 2 LOW non-blocking (stale extract comment, optional test premise guard) — filed as delivery findings, not gating.

## Reviewer Assessment

**Verdict:** APPROVED

The rework cleanly resolved every Round-1 finding and introduced no regression. The HIGH `ruff format` gate now passes; rule-checker reports **0 violations across all 13 Python checks**; the three MEDIUM items are verified fixed (public Protocol return type via a correct TYPE_CHECKING import with no circular dependency; `detection_method` now honestly tags `"router"` vs `"keyword"` vs `"classifier"`; the crash-span assertion makes the non-fatal contract observable). Two new LOW nits surfaced (a stale two-value inline comment that omits "router" — code correct, comment incomplete; an optional test premise-guard) — both non-blocking, filed as delivery findings. The story meets all five ACs.

**Data flow traced:** player action → narrator prose (`result.narration`) → `_execute_narration_turn` post-narration block → `await run_unseeded_objective_classifier_watcher(narration, snapshot, package, llm)` → cost gates (empty/minted/router-seeded short-circuit, no spend) → `classify_unseeded_objective` (bounded narration, forced-tool Haiku) → on objective-given, `narration.unminted_objective.suspected` span with `detection_method="classifier"` → SPAN_ROUTES → GM panel (component=narrator). Safe: narration is server-generated, delimited (ADR-047) and length-bounded; the forced `tool_choice` is the injection boundary; failures are caught and surfaced as a crash span.

**Pattern observed:** faithful reuse of the `IntentRouter` injectable-LLM seam and the `run_*_watcher` post-narration family — `post_narration_classifier.py:164` mirrors `run_unminted_objective_watcher` discipline (pure gate + non-fatal try/except + span).

**Error handling:** the lone `except Exception` (`post_narration_classifier.py:208`) is logged at ERROR with `exc_info=True` and emits `dispatch_engagement.watcher.crashed` — verified by `test_watcher_swallows_classifier_failure`. Non-fatal by contract; never aborts turn delivery.

### Findings dispatched by source
- **[PREFLIGHT]** format PASS (HIGH cleared), tests 43 + 433 green, lint clean, `post_narration_classifier.py` pyright 0. `llm_factory.py` +20 pyright = accepted house-pattern (LOW).
- **[EDGE]** *(disabled — Reviewer assessed)* `[VERIFIED]` New truncation branch (`post_narration_classifier.py:131`) sits AFTER the empty-check; boundary inputs (empty/blank/over-4000-char/missing-LLM-keys) all handled. No unhandled path.
- **[SILENT]** *(disabled — Reviewer assessed)* `[VERIFIED]` Truncation logs LOUD before slicing (`logger.warning`, no silent drop); the crash path logs + spans. No silent fallback introduced by the rework.
- **[TEST]** Crash-span test now SOUND (prior concern resolved). New router/keyword detection_method tests are behaviorally correct. LOW: add a zero-marker premise guard to the router test for mutation-resistance (filed, non-blocking).
- **[DOC]** Prior docstring overclaim RESOLVED (span docstring lists 3 methods). NEW LOW: `_extract_unminted_objective` inline comment omits "router" (code correct; filed, non-blocking).
- **[TYPE]** *(disabled — Reviewer assessed)* `[VERIFIED]` Return type now the public `ObjectiveClassifierLLM` Protocol; TYPE_CHECKING import is acyclic (post_narration_classifier does not import llm_factory). Rule-checker confirms.
- **[SEC]** *(disabled — Reviewer assessed)* `[VERIFIED]` ADR-047 delimiter + forced tool_choice + the new 4,000-char bound; narration is server-generated. No injection/SQL/eval/pickle. `detection_method` is a telemetry-only attribute (no control-flow/security boundary).
- **[SIMPLE]** *(disabled — Reviewer assessed)* `[VERIFIED]` Rework added no needless abstraction — a ternary, a guarded import, a bounded slice, a strengthened assertion. Minimal and direct.
- **[RULE]** rule-checker CLEAN — 0 violations across 13 checks; all three prior fixes explicitly verified correct.

### Rule Compliance (.pennyfarthing/gates/lang-review/python.md — 13 checks)
rule-checker reports **0 violations / 13 checks / 67 instances** on the rework diff. Spot-confirmed: #1 (non-fatal except justified+logged+spanned), #3 (Protocol return type, acyclic TYPE_CHECKING import), #4 (truncation `logger.warning` lazy %-args, correct level), #9 (all coroutines awaited), #10 (`__all__` on the new module; TYPE_CHECKING import not a runtime cycle), #11 (narration bounded + delimited), #13 (no fix-introduced regression).

### Devil's Advocate

Assume the rework broke something. The most likely place is the new branch I forced into the sync 117-4 watcher: `detection_method = "router" if _package_accepted_quest_offer(package) else "keyword"`. Could this mis-tag? `_package_accepted_quest_offer` returns True only on a `quest_offer` dispatch with `decision == "accept"` — so a decline, a non-quest_offer package, or `None` all fall to `"keyword"`, which is exactly right (a decline that somehow reached the span would be a keyword-substring hit, correctly labelled). The router test proves the positive; the keyword test proves the negative with `package=None`. Could a future edit to the router test's narration silently turn it into a dual-path test? Yes — that's the LOW premise-guard nit, and it's why I filed it, but it cannot make today's code wrong. Next: the TYPE_CHECKING import — if `from __future__ import annotations` were absent, the string annotation would NameError at runtime; but it's present (llm_factory.py:10), and post_narration_classifier has no back-import, so no cycle even at type-check time. The narration bound: could truncating to 4,000 chars drop the objective and cause a false negative? Possible in theory, but the objective hook is in the opening prose by genre convention, and the alternative (unbounded cost on a runaway narrator) is the worse failure for a cost-observability sprint — and it logs loud, so a truncation is visible. The crash test: could it pass while the span silently doesn't emit? No — it filters spans by the exact name and pins `error_type`, both independently falsifiable. The only thing I'd genuinely lose sleep over is the stale `_extract_unminted_objective` comment misleading a GM-panel maintainer into thinking "router" can't appear — but the extract passes the value through regardless, so the panel still shows it; the comment is a documentation lag, not a functional defect. Nothing here rises to High. Approve.

**Handoff:** To SM (Camina Drummer) for finish-story. Two LOW non-blocking findings filed for an optional follow-up sweep (stale extract comment; test premise guard).