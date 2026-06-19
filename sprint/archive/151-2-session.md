---
story_id: "151-2"
jira_key: ""
epic: "151"
workflow: "tdd"
---
# Story 151-2: [NARRATOR] Post-narration Haiku sidecar extractor — shadow mode + sidecar_extraction.* OTEL + lie-detector (ADR-150 step 2)

## Story Details
- **ID:** 151-2
- **Jira Key:** (none — Jira not configured for this project)
- **Workflow:** tdd
- **Stack Parent:** none (independent story)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-18T23:57:46Z
**Round-Trip Count:** 2

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-18T22:54:58.988235Z | 2026-06-18T22:58:39Z | 3m 40s |
| red | 2026-06-18T22:58:39Z | 2026-06-18T23:11:47Z | 13m 8s |
| green | 2026-06-18T23:11:47Z | 2026-06-18T23:28:12Z | 16m 25s |
| review | 2026-06-18T23:28:12Z | 2026-06-18T23:38:16Z | 10m 4s |
| green | 2026-06-18T23:38:16Z | 2026-06-18T23:48:41Z | 10m 25s |
| review | 2026-06-18T23:48:41Z | 2026-06-18T23:54:01Z | 5m 20s |
| green | 2026-06-18T23:54:01Z | 2026-06-18T23:55:45Z | 1m 44s |
| review | 2026-06-18T23:55:45Z | 2026-06-18T23:57:46Z | 2m 1s |
| finish | 2026-06-18T23:57:46Z | - | - |

## Technical Approach

Per ADR-150, this story implements the post-narration extraction pass (step 2 of the sidecar-accounting migration):

**Scope:** Build the skeleton of the post-extractor in shadow mode — no fields cut over yet, but the infrastructure and lie-detector watching are in place from day one.

**Key Components:**
1. **New `CallType` or reuse `CLASSIFICATION`** — route a Haiku forced-tool-use call through the existing model routing (`agents/model_routing.py`)
2. **AsideResolver-shaped extractor** (`agents/sidecar_extractor.py` or similar) — reads narrator prose, emits structured bucket-B fields via `emit_tool` protocol (ADR-102)
3. **OTEL instrumentation** — emit `sidecar_extraction.run`, `sidecar_extraction.{field}`, `sidecar_extraction.mismatch` spans (per ADR-31 discipline)
4. **No-fallbacks retry** — bounded retry on Haiku failure; fall through to existing catch-loops as the loud net
5. **Shadow mode wiring** — extractor runs after narrator but output is *not yet* applied; only the lie-detector watches for mismatches
6. **Wiring test** — synthetic turn through the full pipeline (router → narrator stub → **extractor → narration_apply**); assert extractor is reachable and OTEL spans fire

**Out of scope:** Field cutover (151-4, 151-5); output_only.md shrink (151-6); playtest validation (151-7).

**Testing:** Fixture-based only. Synthetic prose fixtures drive the real extractor; assert emitted fields and OTEL spans. No live-content coupling.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): The epic-151 context is HOLLOW at HEAD — story 151-1's
  finish ceremony (commit `9084a7a0`) regenerated `context-epic-151.md` into a
  19-line skeleton, clobbering the authored 143-line version from `975f5797`
  (the same recurring `pf context create` regression that hit the story context).
  Affects `sprint/context/context-epic-151.md` (restore from `975f5797` so the
  field-partition table + build-sequence are not lost). I read the rich version
  from git to do this story. *Found by TEA during test design.*
- **Improvement** (non-blocking): AC6 wiring is covered two ways — reflection
  (`websocket_session_handler.__dict__` contains the runner) + behavioral reach
  (the runner emits `sidecar_extraction.run`) — but no test drives a full WS turn
  end-to-end, because the post-narration seam is inline in the handler (not a
  standalone function). Affects `tests/agents/test_sidecar_extractor.py`; the
  ADR-150 step-6 playtest gate (story 151-7) is the place to confirm the extractor
  actually fires on a live turn. *Found by TEA during test design.*
- **Question** (non-blocking): The structured-output representation for the list
  bucket-B fields (`items_*`, `npcs_present`, `companions_*`) is Dev's choice
  (typed models vs `list[dict]`). Tests assert scalars (`gold_change`,
  `scene_mood`), lengths, and the mismatch path to stay representation-agnostic —
  but if Dev validates `npcs_present` into typed `NpcMention`, the seed mismatch
  witness must read each mention's `.name`. Affects
  `sidequest/agents/sidecar_extractor.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): The shadow extractor now fires a live Haiku
  `emit_tool` call once per non-empty-narration turn (caller=`sidecar_extraction`,
  on the ADR-134 ceiling). GREEN verified the unit/routing/sibling suites + a
  cross-module import smoke-check, but NOT a full WS-turn end-to-end run — the
  runner is non-fatal (catches all, returns None) and the wiring is reflection-
  verified, so it cannot crash a turn, but real mismatch-rate behavior is
  unproven. Affects `sidequest/server/websocket_session_handler.py` (the
  ADR-150 step-6 playtest gate, story 151-7, is where live shadow behavior +
  the per-turn cost delta should be measured). *Found by Dev during implementation.*
- **Question** (non-blocking): The epic-151 context at HEAD is still the hollow
  skeleton (TEA's Gap finding above) — restoring `context-epic-151.md` from
  `975f5797` would give the 151-4/5 cutover stories the field-partition table.
  Affects `sprint/context/context-epic-151.md`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): The per-turn live extractor prompt has no narration length
  cap, unlike the sibling `post_narration_classifier` (`_MAX_NARRATION_CHARS=4_000`).
  Affects `sidequest/agents/sidecar_extractor.py` (`_build_user_prompt` / `extract`
  — add a `_MAX_NARRATION_CHARS` truncation before the SDK call). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The shadow runner's outer `except Exception`
  (`sidecar_extractor.py:334`) logs `watcher_crashed` but emits no OTEL span, unlike
  the sibling `run_dispatch_engagement_watcher` (which fires
  `dispatch_engagement_watcher_crashed_span`). Affects `sidequest/agents/sidecar_extractor.py`
  (+ a crashed-span helper in `telemetry/spans/sidecar_extraction.py`) — the GM panel
  is blind to a runner crash. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The seed mismatch witness reads only
  `npc_pool`+`npcs`; an `encounter.actors` opponent not yet promoted would trip a
  false-positive mismatch span. Affects `sidequest/agents/sidecar_extractor.py`
  (`_known_npc_names`) — widen the engine-cast source when `npcs_present` cuts over
  in 151-5. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Pinned the module path and public symbol names**
  - Spec source: context-story-151-2.md, Technical Guardrails; ADR-150 §Decision step 2
  - Spec text: "modeled on the existing AsideResolver (agents/aside_resolver.py) and routed through the existing CallType.CLASSIFICATION → claude-haiku-4-5 ladder"
  - Implementation: pinned `sidequest/agents/sidecar_extractor.py` and symbols `SidecarExtractor` / `.extract` / `SidecarExtractorLLM` / `SidecarExtractionFailure` / `run_sidecar_extraction_watcher` / `BUCKET_B_FIELDS`, mirroring the sibling `intent_router.py` + `dispatch_engagement_watcher.py` naming
  - Rationale: TDD requires concrete imports; the spec fixed the shape and route but not the names
  - Severity: minor
  - Forward impact: Dev may rename via a Delivery Finding; 151-4/151-5 reference `BUCKET_B_FIELDS` as the canonical field list
- **Pinned a two-layer split: a core pass that raises + a non-fatal shadow runner**
  - Spec source: ADR-150 §No-fallbacks discipline + §Ordering; context AC5
  - Spec text: "extraction failure ... emits an ERROR span, gets one bounded retry, and on second failure surfaces an explicit GM-panel error — the existing per-field catch-loops remain as the loud safety net"
  - Implementation: `SidecarExtractor.extract()` raises `SidecarExtractionFailure` after 2 attempts (mirrors `IntentRouter.decompose`); `run_sidecar_extraction_watcher()` catches it, emits the loud span, and NEVER raises into the WS turn pipeline (mirrors `run_dispatch_engagement_watcher`'s non-fatal contract)
  - Rationale: reconciles "explicit error" (the core pass) with "post-narration observability must not crash the turn after the prose already broadcast" (the runner) — both are live precedents
  - Severity: minor
  - Forward impact: none
- **Pinned the seed mismatch witness to engine-owned `npcs_present` membership**
  - Spec source: ADR-150 §Telemetry (the `sidecar_extraction.mismatch` example) + §Decision ("npcs_present.side/membership is owned by the engine the IntentRouter already engaged")
  - Spec text: "when the extractor's output disagrees with what the engine/state already holds (e.g. extractor reports an item the inventory mutation could not match)"
  - Implementation: the RED witness fires `sidecar_extraction.mismatch` when an extracted `npcs_present` name is absent from the engine-owned snapshot cast (`npc_pool`). The ADR's *item* example needs an applied inventory mutation to diff against — shadow mode applies nothing, so there is no item delta yet; engine-owned NPC membership is the cleanest witness available to the skeleton
  - Rationale: an extractor-invented NPC name the engine never seated is the textbook "two readers of one prose disagree" the ADR describes, and membership is explicitly engine-owned
  - Severity: minor
  - Forward impact: 151-4 (items) and 151-5 (npcs/cosmetic) add their own per-field witnesses as each field cuts over; the skeleton seeds exactly one
- **Pinned the per-field span-name form and the failure span name**
  - Spec source: ADR-150 §Telemetry
  - Spec text: "sidecar_extraction.{field} — per-field emitted/empty, on the extraction pass" and "extraction failure ... emits an ERROR span"
  - Implementation: per-field spans are named `sidecar_extraction.{field}` (e.g. `sidecar_extraction.gold_change`) carrying an `emitted: bool` attribute, mirroring `dispatch_engagement.{subsystem}`; the ERROR span is `sidecar_extraction.failed`, mirroring `intent_router.failed`
  - Rationale: literal reading of `{field}` as the span name + sibling naming precedent
  - Severity: minor
  - Forward impact: none

### Dev (implementation)
- **Added an empty-narration cost guard not required by any test**
  - Spec source: SOUL "Cost Scales with Drama"; ADR-150 §Ordering; sibling `post_narration_classifier` gating precedent
  - Spec text: "A quiet walk through town is cheap … don't spend cycles on nothing"
  - Implementation: `run_sidecar_extraction_watcher` returns `None` without calling the LLM when `narration.strip()` is empty
  - Rationale: shadow mode fires once per turn in production; a prose-less turn has nothing to read, so a live Haiku call would burn cycles for nothing — matches the unseeded classifier's non-empty-narration gating. All tested paths use non-empty prose, so no test exercises the guard
  - Severity: minor
  - Forward impact: none (151-7 playtest validates live behavior)
- **Kept the list bucket-B fields as raw `dict` payloads, not typed models**
  - Spec source: context-story-151-2.md AC1; TEA Delivery Finding (Question)
  - Spec text: "returns a validated structured object for the bucket-B field set"
  - Implementation: `SidecarExtraction.npcs_present` / `items_*` / `companions_added` / `footnotes` are `list[dict[str, Any]]` (the `emit_tool` shape), not typed `NpcMention`/`CatalogItem`; the mismatch witness reads `mention["name"]`
  - Rationale: shadow mode applies nothing, so typing the payloads is the cutover stories' job as each field migrates into `narration_apply` — minimalist discipline (no abstraction a test requires)
  - Severity: minor
  - Forward impact: 151-4 (items) / 151-5 (npcs/cosmetic) type their fields as they cut over; the witness must keep reading `name` whatever the representation
- **Confirmed TEA's per-field-span pin by NOT registering 11 per-field SPAN_ constants**
  - Spec source: ADR-150 §Telemetry; project `tests/telemetry/test_routing_completeness.py`
  - Spec text: "sidecar_extraction.{field} — per-field emitted/empty"
  - Implementation: only the 3 load-bearing spans (`run`/`mismatch`/`failed`) are `SPAN_` constants with typed `SPAN_ROUTES`; the 11 per-field spans are dynamically named (`sidecar_extraction.{field}`) and ride the always-on `agent_span_close` fan-out
  - Rationale: 11 per-field typed routes would be GM-panel noise; the run/mismatch spans carry the typed signal. Dynamic names also keep them out of the routing-completeness lint without leaving them unrouted-by-mistake
  - Severity: minor
  - Forward impact: none

### Reviewer (audit)
- TEA **module path + symbol names** → ✓ ACCEPTED: mirrors the sibling `intent_router.py` / `dispatch_engagement_watcher.py` naming; `BUCKET_B_FIELDS` as the single source of truth is good discipline.
- TEA **two-layer split (core raises / non-fatal runner)** → ✓ ACCEPTED: faithful to the live ADR-113 lineage; both layers verified loud (security + silent-failure subagents concur).
- TEA **seed mismatch witness (npcs_present membership)** → ✓ ACCEPTED with note: sound for the shadow skeleton, but the witness reads only `npc_pool`+`npcs` — a freshly-seated `encounter.actors` opponent could trip a false-positive `sidecar_extraction.mismatch` span. Non-blocking for shadow; flagged as a Delivery Finding for the 151-5 cutover.
- TEA **per-field span-name form + failed span name** → ✓ ACCEPTED: matches `dispatch_engagement.{subsystem}` / `intent_router.failed`.
- Dev **empty-narration cost guard** → ✓ ACCEPTED: sound, mirrors the sibling classifier — but it emits nothing observable (silent-failure [LOW]); add a `logger.debug` so "skipped" ≠ "never ran".
- Dev **list bucket-B fields as raw dict** → ✓ ACCEPTED: correct for shadow (applies nothing); typing is the cutover stories' job.
- Dev **per-field spans without SPAN_ constants** → ✓ ACCEPTED: run/mismatch/failed carry typed routes; per-field rides `agent_span_close`. Routing-completeness green.
- **UNDOCUMENTED deviation (Reviewer-found):** the extractor feeds `narration` to the Haiku prompt with NO length cap, deviating from the established sibling pattern `post_narration_classifier._MAX_NARRATION_CHARS = 4_000` (which truncates before its SDK call for exactly this reason) — neither TEA nor Dev logged this. Spec/rule: python.md #11 (bound freeform fodder at boundaries) + the sibling precedent. → ✗ **FLAGGED** — Severity: High (see Reviewer Assessment). The bound is a required boundary control on a per-turn live call shipping to production.

## Story Context

This is ADR-150 step 2 of the epic. Sibling stories:
- **151-1** (DONE): Cache-promote `narrator_output_only` to `STABLE_SECTION_NAMES`
- **151-3** (DONE): Migrate `action_rewrite` to IntentRouter pre-pass
- **151-4** (BACKLOG, depends_on 151-2): Transactional field cutover (items, gold, companions)
- **151-5** (BACKLOG, depends_on 151-2): `npcs_present.side` + async cosmetic fields

**Branch:** `feat/151-2-haiku-sidecar-extractor-shadow` (sidequest-server develop)

## Sm Assessment

**Selection rationale:** 151-2 is the only unblocked story in the active p2 epic-151 chain (`depends_on: null`); 151-4/5/6/7 all transitively depend on it. It's the keystone — the cutover stories have nothing to cut over to until this extractor exists. Higher priority than the ready 150-x playtest stories (p2/p3 trivial) and the p3 tech-debt items.

**Gates verified:**
- Merge gate clear — no open PRs across any of the six subrepos.
- No in-progress / in-review stories competing.
- Jira not configured for this project → claim skipped (not an error, matches 151-1/151-3 precedent).
- Single repo: `sidequest-server` only, base branch `develop` (per repos.yaml — not main).

**Setup correction (logged for the record):** sm-setup's `pf context create` regenerated `sprint/context/context-story-151-2.md` as a hollow skeleton (committed as `a278f5ee`), clobbering the rich authored guardrails/ACs from `975f5797`. I restored the authored 68-line version and re-committed it (`ae52501b` on `main`, local — push deferred to the user / finish ceremony per the orchestrator main-push hook). TEA reads the restored rich context, which carries the ADR-150 step-2 OTEL span spec, shadow-mode constraints, and AC context.

**Handoff:** Phased `tdd` workflow → TEA owns the RED phase. The 6 ACs in the context doc (structured output, shadow/no-mutation, spans fire, lie-detector mismatch, no-silent-fallback, wiring test) are the RED targets. Emphasis for TEA: AC3/AC4/AC6 must assert OTEL spans by **driving a synthetic turn**, not source-grep — and the wiring test must prove the extractor is *reached* through the real pipeline (orchestrator → narrator stub → extractor), per the project's "every test suite needs a wiring test" rule.

## TEA Assessment

**Tests Required:** Yes
**Reason:** ADR-150 step-2 foundation — net-new extractor component with 6 ACs and OTEL/no-fallbacks discipline. Not a chore-bypass candidate.

**Test File:**
- `sidequest-server/tests/agents/test_sidecar_extractor.py` — 19 failing tests, all 6 ACs + python.md rule coverage. Fixture-based (no content coupling); OTEL-span assertions via the `otel_capture` fixture; reflection-based wiring (no source-text grep).

**Tests Written:** 19 tests covering 6 ACs.
**Status:** RED (verified by `testing-runner`, run-id `151-2-tea-red`) — file collects cleanly; all 19 fail with `ModuleNotFoundError`/`ImportError` on `sidequest.agents.sidecar_extractor` (the expected missing-module reason). Zero spurious failures.

### AC Coverage

| AC | Tests | Status |
|----|-------|--------|
| AC1 structured emit_tool output (no JSON parse) | `test_extract_returns_validated_object_with_bucket_b_fields`, `test_extract_forces_emit_tool_with_a_schema`, `test_extract_passes_narration_prose_into_the_user_prompt`, `test_bucket_b_field_set_is_the_eleven_canonical_fields` | failing |
| AC2 shadow / no mutation | `test_extract_does_not_mutate_the_snapshot`, `test_run_watcher_returns_extraction_without_applying_it` | failing |
| AC3 run + per-field spans | `test_extract_emits_run_span_with_attributes`, `test_extract_emits_per_field_span_emitted_true_for_present_field`, `test_extract_emits_per_field_span_emitted_false_for_empty_field` | failing |
| AC4 mismatch lie-detector | `test_mismatch_span_fires_when_extractor_invents_an_npc`, `test_no_mismatch_span_when_extraction_agrees_with_state` | failing |
| AC5 no-fallbacks (ERROR span + retry-once + explicit raise) | `test_extract_retries_once_then_raises_on_persistent_failure`, `test_extract_recovers_on_retry`, `test_extract_retries_on_schema_invalid_output_then_raises`, `test_run_watcher_surfaces_failure_as_span_without_crashing` | failing |
| AC6 wiring | `test_run_sidecar_extraction_watcher_is_reachable_and_emits`, `test_runner_wired_into_session_handler` | failing |

### Rule Coverage

| Rule (python.md / CLAUDE.md / SOUL) | Test(s) | Status |
|------|---------|--------|
| #1 silent-exceptions / No Silent Fallbacks | `test_extract_retries_once_then_raises_on_persistent_failure`, `test_run_watcher_surfaces_failure_as_span_without_crashing` | failing |
| #6 test-quality (self-check) | n/a — own tests reviewed in Phase C (below) | — |
| #9 async pitfalls | `test_public_pass_and_runner_are_coroutines` | failing |
| #10 import hygiene (`__all__`) | `test_module_declares_all` | failing |
| Every Test Suite Needs a Wiring Test | `test_runner_wired_into_session_handler`, `test_run_sidecar_extraction_watcher_is_reachable_and_emits` | failing |
| No Source-Text Wiring Tests | wiring uses `wsh.__dict__` reflection + behavioral span assertion, never a source grep | enforced |
| OTEL Observability Principle | AC3/AC4 span assertions; quiet/consistent turn emits no mismatch span | failing |

**Rules checked:** 5 of the 13 lang-review checks are materially applicable to a net-new async LLM-pass module (#1, #6, #9, #10, plus the CLAUDE.md wiring/OTEL rules); #2/#5/#7/#8/#11/#12 are not exercised by this diff (no mutable defaults, no resource handles, no deserialization of untrusted input, no deps, no path handling).
**Self-check (Phase C):** 0 vacuous assertions — every test pins a concrete value (span name + `emitted` bool, `await_count == 2`, `model_dump()` equality, `pytest.raises`, set equality), never a bare truthy/`is_some` check. Lint-clean (`ruff format` + `ruff check` pass).

**Interface pins:** Module path, public symbol names, the two-layer (raises / non-fatal) split, the seed mismatch witness, and the per-field/`failed` span names are TEA-pinned for RED — see Design Deviations → TEA for the 6-field rationale on each. The span names, the eleven bucket-B fields, the `emit_tool`/retry-once/shadow contract, and the wiring requirement are fixed by the ADR/context, not by TEA.

**Handoff:** To Dev (Inigo Montoya) for GREEN. Build `sidequest/agents/sidecar_extractor.py` to turn the 19 tests green, then wire `run_sidecar_extraction_watcher` into `websocket_session_handler.py` at the existing post-narration watcher seam (alongside `run_dispatch_engagement_watcher`, ~line 1155) — shadow mode, applies nothing.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/agents/sidecar_extractor.py` (NEW) — `SidecarExtractor.extract()` (forced `emit_tool` Haiku pass, one bounded retry, explicit `SidecarExtractionFailure`), `SidecarExtraction` pydantic model (11 bucket-B fields), `SidecarExtractorLLM` Protocol, `BUCKET_B_FIELDS` canonical tuple, `detect_sidecar_extraction_mismatch` (seed npcs_present witness), and the non-fatal shadow runner `run_sidecar_extraction_watcher`.
- `sidequest/telemetry/spans/sidecar_extraction.py` (NEW) — `sidecar_extraction.run` / `.mismatch` / `.failed` `SPAN_` constants + typed `SPAN_ROUTES` (GM-panel), plus the per-field span helper (dynamic `sidecar_extraction.{field}` names) and the ERROR-status failed-span helper.
- `sidequest/telemetry/spans/__init__.py` — `from .sidecar_extraction import *` (alphabetical), so the new spans enter the package namespace and the routing-completeness lint.
- `sidequest/agents/llm_factory.py` — `_SidecarExtractorLlm` adapter + `build_sidecar_extractor_llm` on the live `CallType.CLASSIFICATION → claude-haiku-4-5` rung (caller=`sidecar_extraction`, ADR-134 ceiling); `SidecarExtractorLLM` added to the `TYPE_CHECKING` block.
- `sidequest/server/websocket_session_handler.py` — imports `run_sidecar_extraction_watcher` + `build_sidecar_extractor_llm`; `await`s the runner at the post-narration seam (after `run_fate_engagement_watcher`), shadow mode, applies nothing.

**Tests:** 19/19 story tests passing (GREEN, run-id `151-2-dev-green`). Sibling regression guard green: routing-completeness 2/2, `test_dispatch_engagement_watcher` + `test_intent_router` 56/56. Cross-module import smoke-check confirms no circular import and the handler namespace carries both the runner and the builder (the AC6 reflection wiring). `ruff format` + `ruff check` clean on all five files.

**Verification scope:** Owning module + span routing + sibling suites + import wiring. NOT run: a full WS-turn end-to-end (heavy + baseline-noisy from the unstubbed sibling LLM watchers). The runner is non-fatal by construction (catches all → returns None) and the import wiring is reflection-verified, so it cannot crash a turn; live shadow behaviour + the per-turn cost delta are deferred to the 151-7 playtest gate (logged as a Dev Delivery Finding, echoing TEA's).

**Branch:** `feat/151-2-haiku-sidecar-extractor-shadow` (pushed to origin).

**Handoff:** To Reviewer (Westley) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (GREEN: 19/19 + 2/2 + 470/470; lint clean; 0 smells introduced) | N/A — confirmed wiring at handler:1223/1226 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — domain reviewed manually (gold_change=0 edge, witness false-positive) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 | confirmed 3 (1 medium, 2 low), dismissed 0 |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — test quality reviewed manually (19 tests non-vacuous; truncation-test gap noted) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — docstrings spot-checked manually (accurate) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — types reviewed manually (list[dict] intentional for shadow) |
| 7 | reviewer-security | Yes | findings | 1 (+ 5 verified-good) | confirmed 1 (HIGH), dismissed 0 |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — simplicity reviewed manually (unused snapshot param intentional/documented) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — rule enumeration done manually (see Rule Compliance) |

**All received:** Yes (3 enabled specialists returned; 6 disabled via `workflow.reviewer_subagents` and reviewed manually)
**Total findings:** 5 confirmed (1 High, 1 Medium [SEC/SILENT], 1 Medium [RULE/manual], 2 Low), 0 dismissed, plus several VERIFIED-good

## Rule Compliance

Manual enumeration (rule_checker disabled) against `python.md` + CLAUDE.md/SOUL, every applicable instance in the diff:

- **python.md #1 silent exceptions / No Silent Fallbacks** — `extract()` TimeoutError/transport/schema-invalid branches each emit an ERROR span + log before continue/raise (✓); `run_sidecar_extraction_watcher` inner `except SidecarExtractionFailure` logs ERROR + returns None (✓ non-fatal); outer `except Exception` logs ERROR with `exc_info` (✓ loud) **but emits no span** — OTEL-completeness gap vs sibling (MEDIUM, see assessment). `_SidecarExtractorLlm.emit_tool` raises `LlmClientError` on empty output (✓). **No bare excepts; both broad excepts are scoped + `noqa: BLE001`-annotated at real I/O/observability boundaries.**
- **python.md #3 type annotations at boundaries** — all public signatures annotated (`extract`, `run_sidecar_extraction_watcher`, `emit_tool`, builders) (✓).
- **python.md #4 logging coverage/levels** — error paths use `logger.warning`/`logger.error` correctly; failed-span at `StatusCode.ERROR` (✓). Minor: schema_invalid double-logs (LOW).
- **python.md #8 unsafe deserialization** — only `SidecarExtraction.model_validate(tool_input)` (pydantic) on the SDK-structured dict; no `json.loads`/`eval`/`exec`/`pickle`/`yaml.load` on raw text (✓, security-confirmed).
- **python.md #9 async** — `extract` + `run_sidecar_extraction_watcher` are coroutines, awaited correctly at the handler seam (✓, test-pinned).
- **python.md #10 import hygiene** — `__all__` declared; `from .sidecar_extraction import *` is alphabetical; no circular import (smoke-checked) (✓).
- **python.md #11 input validation at boundaries** — **VIOLATION:** narration prose is unbounded into the SDK prompt (`_build_user_prompt:138`), unlike the sibling `_MAX_NARRATION_CHARS=4_000`. HIGH (see assessment).
- **CLAUDE.md No Source-Text Wiring Tests** — the wiring test uses `wsh.__dict__` reflection + behavioral span assertion, never a source grep (✓).
- **CLAUDE.md OTEL Observability Principle** — run/per-field/mismatch/failed spans cover the success + failure decisions (✓); the runner-crash path is the one gap (MEDIUM).
- **CLAUDE.md Don't Reinvent / Verify Wiring** — reuses the live `CallType.CLASSIFICATION` rung + `_call_haiku_sdk` + `emit_tool` lineage; preflight confirmed the runner is *called* at handler:1223, not just imported (✓).
- **ADR-134 cost ceiling** — `_SidecarExtractorLlm` threads `session_id`+`ceiling_usd` through `_call_haiku_sdk`, `caller="sidecar_extraction"` (✓, security-confirmed).
- **ADR-105 perception firewall** — extractor reads only `result.narration` (public-safe) + engine-owned cast; `private_prose_segments` untouched (✓, security-confirmed).

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] [SEC][RULE] | Unbounded narration into the per-turn live Haiku prompt (CWE-400; python.md #11; deviates from the sibling `_MAX_NARRATION_CHARS=4_000` precedent). Ships to prod in shadow on every turn — a real per-turn token-cost vector in a cost-*reduction* epic. ADR-134 ceiling only kills *after* billing, not a pre-call gate. | `sidecar_extractor.py:138` `_build_user_prompt` (+`extract:170`) | Add `_MAX_NARRATION_CHARS = 4_000` (module scope) and truncate before the prompt, mirroring `post_narration_classifier.py:51,131-137` (log when truncating). |
| [MEDIUM] [RULE] | Runner outer `except Exception` logs `watcher_crashed` but emits no OTEL span — GM panel blind to a runner crash, unlike the sibling `dispatch_engagement_watcher` (`dispatch_engagement_watcher_crashed_span` at 521/624/766). Violates the OTEL Observability Principle for the crash path. | `sidecar_extractor.py:334` | Emit a crashed span in the outer except (add a `sidecar_extraction.watcher_crashed` helper to `telemetry/spans/sidecar_extraction.py`, mirror the sibling). |
| [MEDIUM] [SILENT] | `schema_invalid` stores `type(exc).__name__` in `last_failure`, so the raised `SidecarExtractionFailure` loses pydantic field detail (inconsistent with timeout/transport which keep `str(exc)`). Not silent (logged), but the propagated exception is under-informative. | `sidecar_extractor.py:195` | `last_failure = ("schema_invalid", str(exc))`. |
| [LOW] [SILENT] | `schema_invalid` double-logs (via `_emit_failed` *and* a standalone `logger.warning`) — timeout/transport log once. | `sidecar_extractor.py:~201` | Drop the standalone `logger.warning` (fold detail into `_emit_failed`). |
| [LOW] [SILENT] | Empty-narration early-return emits nothing observable — "skipped" indistinguishable from "never ran". | `sidecar_extractor.py:~311` | Add a `logger.debug` on the early return. |

**Observations (tagged):**
- [SEC] [HIGH] — narration unbounded into the live SDK prompt — `sidecar_extractor.py:138`. Confirmed against the sibling precedent + python.md #11. **Blocking.**
- [SILENT] [MEDIUM] — raised `SidecarExtractionFailure` drops pydantic detail on schema_invalid — `:195`.
- [RULE] [MEDIUM] — runner crash path emits no span (OTEL Observability Principle) — `:334`. (Manual rule-check; rule_checker disabled.)
- [SILENT] [LOW] — schema_invalid double-log; [SILENT] [LOW] — empty-narration silent skip.
- [EDGE] (manual) [MEDIUM, non-blocking] — `_known_npc_names` omits `encounter.actors`, a false-positive mismatch source for 151-5; [LOW] `gold_change=0` → `emitted=True`.
- [TEST] (manual) [VERIFIED] — the 19 tests are non-vacuous (concrete value/`await_count`/`model_dump()`/`pytest.raises`/set-equality assertions); the only coverage gap is the missing narration-truncation test (the HIGH finding).
- [TYPE] (manual) [VERIFIED] — `SidecarExtraction` list-as-`dict[str,Any]` is an intentional shadow-mode choice; scalars typed `int|None`/`str|None`.
- [SIMPLE] (manual) [VERIFIED] — `extract()`'s unused `snapshot` is documented "reserved for grounding"; pinned by the test API. Acceptable.
- [DOC] (manual) [VERIFIED] — docstrings accurate, including the honest "applies nothing" shadow framing.
- [SEC] [VERIFIED] — ADR-134 ceiling wired (`session_id`+`ceiling_usd` through `_call_haiku_sdk`, `caller="sidecar_extraction"`); no unsafe deserialization; ADR-105 firewall intact (reads only `result.narration`).
- [VERIFIED] wiring — preflight confirmed `run_sidecar_extraction_watcher` is *called* at `websocket_session_handler.py:1223` (+ builder at 1226), not just imported.

### Devil's Advocate

Suppose this code is broken. The most dangerous turn is the longest one: a player engineers a verbose action in a prose-heavy genre, the Opus narrator emits a multi-thousand-token paragraph, and `run_sidecar_extraction_watcher` ships every character of it to Haiku as input — uncapped — on *this* turn and every future turn the table runs long. The session's ADR-134 ceiling eventually trips, but only after the tokens are already billed, and the player experiences it as the session dying mid-scene. The sibling classifier already learned this lesson (`_MAX_NARRATION_CHARS=4_000`); this code re-opens the hole the lesson closed — in the very epic whose thesis is "spend the narrator's cycles on prose, not bookkeeping; cut ~4k uncached tokens/turn." Shipping an unbounded *new* per-turn call is the epic contradicting itself. Now suppose the extractor's own mismatch detector throws (a malformed `npcs_present` dict, a `None` where a dict was expected): the outer `except` swallows it to a log line with no span, so the GM panel — the project's stated lie-detector — shows a clean turn while the lie-detector itself is dead. A confused operator reading the panel concludes the extractor is healthy when it crashed. And the raised `SidecarExtractionFailure` on a persistent schema fault tells that operator only "ValidationError" with no field name, so even the logs are a notch less useful than the timeout path. None of these corrupt state (shadow mode applies nothing — the one genuine safety the design earns), but two of them blind the very observability surface the story exists to populate, and one is a cost-DoS vector in a cost story. That is enough to send it back.

**Verdict rationale:** One High (rule-matching, precedent-backed, undismissable) → REJECT. The findings are testable (truncation bound, crashed-span emission) → red rework.

**Handoff:** Back to TEA (Fezzik) for red rework — add the failing tests (narration truncation; runner-crash span), then Dev implements all five fixes.
## Dev Assessment — Rework Round 1

**Rework Complete:** Yes — all 5 Reviewer findings addressed (the 1 blocking + 4 bundled).

**Fixes:**
- [HIGH] **Narration length bound** — added `_MAX_NARRATION_CHARS = 4_000` (`sidecar_extractor.py`); `extract()` truncates over-long narration before the prompt with a LOUD `logger.warning`, mirroring `post_narration_classifier.py:51,131-137`.
- [MEDIUM] **Runner crashed-span** — added `sidecar_extraction.watcher_crashed` `SPAN_` constant + typed route + `sidecar_extraction_watcher_crashed_span` helper (`telemetry/spans/sidecar_extraction.py`); the runner's outer `except` now emits it (ERROR status), mirroring `dispatch_engagement_watcher_crashed_span`.
- [MEDIUM] **schema_invalid detail** — `last_failure = ("schema_invalid", str(exc))` so the raised `SidecarExtractionFailure` carries pydantic field detail (parity with timeout/transport).
- [LOW] **double-log** — removed the standalone `logger.warning` in the schema_invalid branch (`_emit_failed` already logs+spans once).
- [LOW] **empty-narration** — added a `logger.debug` on the early-return so "skipped (cost gate)" ≠ "never ran".

**New tests (2, both GREEN):**
- `test_extract_truncates_overlong_narration_before_the_sdk_call` — a `> _MAX_NARRATION_CHARS` narration is truncated off the prompt (tail marker absent, char count ≤ cap), and the call still fires on the head.
- `test_run_watcher_emits_crashed_span_on_unexpected_error` — monkeypatches `detect_sidecar_extraction_mismatch` to raise; asserts one `sidecar_extraction.watcher_crashed` span (error_type=RuntimeError) and NO raise.

**Tests:** 21/21 story tests passing (run-id `151-2-dev-green-rt1`); routing-completeness 2/2 (the new span is routed); sibling regression 470/470. 493 total, 0 failures. `ruff format` + `ruff check` clean.

**Non-blocking findings deferred (Reviewer agreed):** the `encounter.actors` mismatch false-positive (→ 151-5 cutover) and the full WS-turn end-to-end run (→ 151-7 playtest gate) remain as logged Delivery Findings.

**No new deviations** introduced by the rework (the fixes implement Reviewer findings + follow the sibling precedents).

**Branch:** `feat/151-2-haiku-sidecar-extractor-shadow` (pushing the rework commit).

**Handoff:** Back to Reviewer (Westley) for re-review.
## Reviewer Re-review (Round 2)

### Subagent Results (round 2 — rework delta `38f40542..HEAD`)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 (I001 lint) + tests GREEN (21/21, routing 2/2, sibling 470/470) | confirmed 1 (lint, blocking-gate) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled — delta reviewed manually |
| 3 | reviewer-silent-failure-hunter | Yes | clean | 0 (all 3 round-1 findings RESOLVED; new crashed-span fix correct) | N/A |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled — 2 new tests reviewed manually (concrete asserts) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled |
| 7 | reviewer-security | Yes | clean | 0 (HIGH narration-bound RESOLVED; no new issues) | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled — manual: python.md #11 now satisfied |

**All received:** Yes (3 enabled returned; 6 disabled)
**Total findings:** 1 confirmed (lint-only, blocking the `ruff check` gate), 0 dismissed

### Reviewer Assessment — Re-review

**Verdict:** REJECTED (lint-only)

**Round-1 findings — re-verification:**
- [SEC] [HIGH] narration bound → **RESOLVED**: `_MAX_NARRATION_CHARS = 4_000` (`sidecar_extractor.py:73`), truncated at `:178-184` *before* the prompt and the retry loop so both attempts use the bounded value; loud `logger.warning`. Security subagent confirmed, no new issues.
- [SILENT] [MEDIUM] schema_invalid detail → **RESOLVED** (`:215` now `str(exc)`).
- [SILENT] [LOW] double-log → **RESOLVED** (standalone warning removed).
- [SILENT] [LOW] empty-narration log → **RESOLVED** (`:328` `logger.debug`).
- [RULE] [MEDIUM] runner crashed-span → **RESOLVED**: `sidecar_extraction.watcher_crashed` SPAN_ constant + typed route + ERROR-status helper; outer except emits it. Silent-failure subagent confirmed loud + non-fatal.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [LOW, gate-blocking] [TEST] | `I001` unsorted-import block in the new crashed-span test — fails `ruff check` (which `just server-check`/check-all runs, so it blocks the SM finish). Auto-fixable. | `tests/agents/test_sidecar_extractor.py:485-486` | `uv run ruff check --fix tests/agents/test_sidecar_extractor.py`, then re-commit. |

**Observations (tagged):**
- [SEC] [VERIFIED] HIGH resolved — bound applied before the retry loop; ADR-134/ADR-105/deserialization unchanged.
- [SILENT] [VERIFIED] all 3 nits resolved + crashed-span loud/non-fatal (one acceptable residual: a throwing OTEL tracer would re-raise after the log already fired — OTEL SDK is no-throw, acceptable).
- [TEST] [LOW] the only blocker — an import-sort lint in the test I requested last round.
- [EDGE]/[TYPE]/[SIMPLE]/[DOC]/[RULE] (manual, subagents disabled) — no new issues in the 130-line delta; the delta is confined to the flagged areas + 2 tests.

### Devil's Advocate

Could I be waving through a real problem as "just lint"? The I001 is cosmetic in isolation, but it is a *hard* `ruff check` failure, and `just server-check` runs `ruff check .` — so approving here would hand the SM a story that fails check-all at the finish gate, bouncing it back messier than a clean green-rework now. The substantive risks are genuinely closed: the cost-DoS vector is bounded at 4k chars on both attempt paths (verified by the security pass reading the control-flow, not just the constant's existence), the crashed-span closes the last OTEL blind spot, and the failure exception now carries field detail. Nothing in the 130-line delta touches state application (still shadow), the firewall, or the cost ceiling. The one thing a skeptic would push on — "does truncation hide a real upstream bug where narration is wrongly huge?" — is answered: the truncation logs the original length loudly before capping, so an anomalous length is visible on the panel, not swallowed. The lint is the only thing standing between this and approval.

**Handoff:** Back to Dev (Inigo Montoya) for a lint-only green rework — `ruff check --fix` the test import block, re-commit, re-review.
## Dev Assessment — Rework Round 2 (lint-only)

**Fix:** `ruff check --fix` sorted the import block in `test_run_watcher_emits_crashed_span_on_unexpected_error` (I001), then `ruff format`. No logic change.

**Verify:** `ruff check` + `ruff format --check` both clean on all three 151-2 files; story suite 21/21 green. Committed `b5c684d9`, pushed.

**No new deviations.**

**Handoff:** Back to Reviewer (Westley) for re-review.
## Subagent Results

(Round 3 — re-review of the lint-only delta `1b9e538b..HEAD`, 8 lines in one test file: import sort + format wrap, zero logic.)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 — verified inline by Reviewer: `ruff check` PASS, `ruff format --check` clean, 23/23 (21 story + 2 routing) green | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled |
| 3 | reviewer-silent-failure-hunter | Yes | clean | 0 — round-2 verdict carried (all 3 nits + crashed-span verified resolved); round-3 delta is import-sort only, no logic | N/A |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled |
| 7 | reviewer-security | Yes | clean | 0 — round-2 verdict carried (HIGH narration-bound verified resolved); round-3 delta touches no logic | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled |

**All received:** Yes (preflight verified inline; security + silent-failure round-2 clean verdicts carried over a zero-logic import-sort delta)
**Total findings:** 0 — the round-2 lint blocker (I001) is resolved.

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** player action → narrator prose (`result.narration`, public-safe per ADR-105) → `run_sidecar_extraction_watcher` (bounded to 4 000 chars) → Haiku `emit_tool` → `SidecarExtraction.model_validate` → `sidecar_extraction.*` OTEL. Shadow mode applies nothing to the snapshot — verified safe (no state mutation, no firewall breach, ADR-134 ceiling on the live call).

**Resolution summary (across 3 rounds):**
- [SEC] [HIGH] unbounded narration → RESOLVED (`_MAX_NARRATION_CHARS=4_000`, truncated before both attempt paths, loud log) — security subagent verified control-flow, not just the constant.
- [RULE] [MEDIUM] runner crash blind to GM panel → RESOLVED (`sidecar_extraction.watcher_crashed` ERROR span + typed route).
- [SILENT] [MEDIUM] schema_invalid detail loss → RESOLVED (`str(exc)`); [SILENT] [LOW] double-log + [LOW] empty-narration log → RESOLVED.
- [TEST] [LOW, gate-blocking] I001 import sort → RESOLVED (`ruff check` + `format --check` clean).
- [EDGE] [MEDIUM, non-blocking] `encounter.actors` mismatch false-positive → deferred to 151-5 (Delivery Finding); [TYPE]/[SIMPLE]/[DOC] — no issues (list[dict] intentional for shadow; `snapshot` documented reserved; docstrings accurate).

**Pattern observed:** faithful reuse of the live ADR-113 lineage — `SidecarExtractor` mirrors `IntentRouter` (forced `emit_tool`, retry-once, explicit raise), `run_sidecar_extraction_watcher` mirrors `run_dispatch_engagement_watcher` (non-fatal, crashed-span), the live `CallType.CLASSIFICATION` Haiku rung + ADR-134 ceiling reused (`llm_factory.py`). Wiring confirmed *called* at `websocket_session_handler.py:1223` (preflight round 1), not just imported.

**Error handling:** every failure path is loud — `extract()` raises `SidecarExtractionFailure` after one bounded retry with an ERROR span per attempt; the runner catches, emits a loud span, and stays non-fatal (`websocket_session_handler.py:1223`). No silent fallback (verified by the silent-failure specialist).

**Tests:** 23 green (21 story incl. truncation + crashed-span, 2 routing-completeness); 470 sibling regression green (round 2); lint clean.

**Handoff:** To SM (Vizzini) for finish-story.