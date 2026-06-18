---
story_id: "151-3"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 151-3: [NARRATOR] action_rewrite → IntentRouter pre-pass — retire the sidecar field, rewire visibility_classifier (ADR-150 step 3)

## Story Details
- **ID:** 151-3
- **Jira Key:** (not configured)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-18T20:54:42Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-18T20:12:56Z | 2026-06-18T20:14:32Z | 1m 36s |
| red | 2026-06-18T20:14:32Z | 2026-06-18T20:33:43Z | 19m 11s |
| green | 2026-06-18T20:33:43Z | 2026-06-18T20:47:01Z | 13m 18s |
| review | 2026-06-18T20:47:01Z | 2026-06-18T20:54:42Z | 7m 41s |
| finish | 2026-06-18T20:54:42Z | - | - |

## Sm Assessment

**Routing:** tdd (phased) → handoff to **tea** for RED phase.

**Story:** 151-3 — move `action_rewrite` (you/named/intent) off the narrator sidecar and onto the pre-narration `IntentRouter`, then rewire `visibility_classifier` to read the pre-pass value. ADR-150 step 3. Single repo: `sidequest-server` (base branch `develop`).

**Why now / independence:** No `depends_on`. Per context, this is independent of the extractor work (151-2/4/5) and can run in parallel. Closes a real ordering hazard — today the field is emitted *by* the narrator but *feeds* visibility classification that runs *after* the narrator, so the turn emitting the field is the one whose visibility it gates.

**Atomicity invariant (call out to TEA/Dev):** retire the sidecar emission in the *same* change that lights the pre-pass emission — never two producers for one field. Keep the `omitted → "unspecified"` default fallback as the loud net during transition.

**ACs to cover (RED targets):**
1. IntentRouter emits `action_rewrite` (you/named/intent) from the raw player action.
2. `visibility_classifier` (`:124-129`) reads the pre-pass value; classification no longer depends on the post-narration sidecar.
3. OTEL span `intent_router.action_rewrite` fires.
4. Retirement guard: `output_only.md` PART 2 no longer instructs the field; `NarrationTurnResult`/`_extract_game_patch_json` no longer parses it.
5. Full suite (with content) green.

**Test discipline:** fixture-based tests only — no live-content coupling (per epic-151 description and project memory on no-content-in-unit-tests).

**Gates checked:** merge gate clear (no open server PRs); no in-progress/in-review stories; Jira not configured (skipped, not an error).

## TEA Assessment

**Tests Required:** Yes
**Reason:** Behavioral migration of a structured field across the pre/post-narrator seam with retirement + provenance + new OTEL — exactly the kind of wiring that "looks done" while silently dark. Fixture-based only (epic-151 discipline; no live content).

**Test Files:**
- `tests/agents/test_action_rewrite_intent_router_prepass.py` (NEW) — AC1 producer (`DispatchPackage.action_rewrite` from `decompose`), AC3 `intent_router.action_rewrite` span (emitted true/false loud net), AC4 `output_only.md` retirement.
- `tests/agents/test_orchestrator.py` (EDITED) — AC4 parse retirement (`extract_structured_from_response` no longer surfaces it; inverted the legacy `test_extract_structured_extracts_action_rewrite`), AC4 result-level retirement + legacy extraction-warning retired (inverted `test_run_narration_turn_warns_missing_action_rewrite`), **AC2 wiring/provenance** (`test_result_action_rewrite_sourced_from_pre_pass_not_game_patch`). Field-stays guard (`test_action_rewrite_still_present`) confirmed green.
- `tests/agents/test_narrator_sdk_hybrid_split.py` (EDITED) — removed the now-retired game_patch-sourced `action_rewrite` presentation assertions (contract migration; other presentation fields untouched — they move in 151-4/5).

**Tests Written:** 9 failing (RED) covering AC1–AC4 + 1 guard green. AC5 (full suite green) is the green/verify gate.
**Status:** RED — verified each failure is for the right reason (feature absent): `DispatchPackage` has no `action_rewrite` field (schema_invalid / AttributeError / extra_forbidden), no `intent_router.action_rewrite` span fires, game_patch parse + extraction-absent warning + `output_only.md` instruction all still live.

**Wiring test (CLAUDE.md "Every Test Suite Needs a Wiring Test"):** `test_result_action_rewrite_sourced_from_pre_pass_not_game_patch` drives the real `run_narration_turn` with both a game_patch `action_rewrite` "lie" AND a pre-pass `dispatch_package.action_rewrite`, and asserts the pre-pass value wins on the assembled result — proving the field is reachable from the production pre-pass path, not just constructed in isolation.

### Rule Coverage
| Rule (`.pennyfarthing/gates/lang-review/python.md`) | Test(s) | Status |
|------|---------|--------|
| #6 Test quality — meaningful assertions, no vacuous truthy checks | all 9 (assert specific field values + span `emitted` bool + `is None`) | RED |
| #4 Logging correctness — retired warning no longer fires | `test_run_narration_turn_no_longer_warns_action_rewrite_absent_from_extraction` | RED |
| OTEL Observability Principle (CLAUDE.md) — every subsystem decision emits a span | `test_decompose_emits_action_rewrite_span_when_present` / `…_marks_absent` | RED |
| No Source-Text Wiring Tests (CLAUDE.md) — behavior/span/artifact-content, never source grep | output_only.md check is a plain-substring assertion on the contract ARTIFACT (AC4 deliverable), not a production-source grep; all others are behavioral | RED |

**Rules checked:** 4 of the applicable lang-review/CLAUDE.md rules have test coverage (most python.md rules — mutable defaults, async pitfalls, resource leaks — apply to Dev's GREEN implementation, not these tests).
**Self-check:** 0 vacuous tests (every assertion checks a specific value or span attribute; no `assert True`, no truthy-only checks).

**Handoff:** To Dev (Hephaestus the Smith) for GREEN. See Delivery Findings for the load-bearing provenance-flip wiring (blocking) and the `DispatchPackage.action_rewrite` pydantic-layering note.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/protocol/dispatch.py` — new pydantic `ActionRewrite` model (schema-described you/named/intent) + `DispatchPackage.action_rewrite` field.
- `sidequest/agents/intent_router.py` — emit `intent_router.action_rewrite` span per `decompose`; added prompt step-5 instructing the producer to emit the rewrite from the raw action.
- `sidequest/telemetry/spans/intent_router.py` — `intent_router.action_rewrite` span helper + `SpanRoute` (emitted/intent attrs).
- `sidequest/agents/orchestrator.py` — retired the game_patch parse of `action_rewrite` (extract + assembly) and the absent-warning; `result.action_rewrite` now sourced from `context.dispatch_package.action_rewrite` (the provenance flip).
- `sidequest/agents/narrator_prompts/output_only.md` — removed the `action_rewrite` instruction (PART 2).
- Tests: fixed the AC2 provenance fixture (`bank_result`); inverted `test_narrator.py` + removed the token from `test_61_12` `REQUIRED_TOKENS` (retired-contract updates — see deviations).

**Tests:** 9/9 story tests GREEN. Full `tests/agents/` + `tests/protocol/` = **2338 passed, 43 skipped** (serial `-n0`, per the xdist OTEL-deadlock memory). Server consumers (`test_visibility_classifier`, `test_narration_apply_intent_dispatch`, `test_intent_classified_invariant`, `test_dust_and_lead_horse_replay`) green. `ruff check` + `ruff format` + `pyright` clean on touched modules.

**Branch:** `feat/151-3-action-rewrite-intent-router-prepass` (pushed).

**Wiring verified end-to-end (not just plumbing):** `decompose` (produces `action_rewrite` per prompt + schema) → `execute_intent_router_pre_narrator_pass` → `turn_context.dispatch_package` (`websocket_session_handler.py:1031`) → `_presentation_and_untooled_fields` reads `context.dispatch_package.action_rewrite` → `result.action_rewrite` → `visibility_classifier` / `confrontation_intent_validator` / `narration_apply`. OTEL: `intent_router.action_rewrite` span (emitted true/false).

**Handoff:** To review (Hermes Psychopompos).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — tests GREEN (163 affected), ruff + pyright clean, 0 smells |
| 2 | reviewer-edge-hunter | Yes | findings | 5 | confirmed 4 (all LOW), dismissed 1 |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none | N/A — firewall intact, no injection surface, pydantic-validated |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 4 confirmed (all LOW, non-blocking), 1 dismissed (with rationale), 0 deferred

### Rule Compliance

Lang-review rubric: `.pennyfarthing/gates/lang-review/python.md` (diff is Python + one prompt `.md`).

- **#1 Silent exception swallowing** — COMPLIANT. No new `try/except`. The removed `logger.warning("action_rewrite absent from extraction")` is not a swallow; it is replaced by the `intent_router.action_rewrite` span (`emitted=False`) — an observable loud net (confirmed by reviewer-security). No Silent Fallbacks honored.
- **#3 Type annotations at boundaries** — COMPLIANT. `ActionRewrite` fields typed `str`; `DispatchPackage.action_rewrite: ActionRewrite | None`; `intent_router_action_rewrite_span(*, emitted: bool, intent: str = "")` fully annotated.
- **#4 Logging coverage/correctness** — MINOR DRIFT. `orchestrator.py:1294/1307` `has_action_rewrite` log is now stale (reads the raw narrator patch, which is ignored). [EDGE][LOW], non-blocking.
- **#6 Test quality** — COMPLIANT. Every story test asserts a specific value/span attribute (verified RED phase; preflight green). No vacuous assertions; the inverted output-contract tests assert retirement, not truthiness.
- **#8 Unsafe deserialization** — COMPLIANT. New path uses pydantic `model_validate` only; no pickle/yaml.load/eval (confirmed reviewer-security).
- **#10 Import hygiene** — COMPLIANT. One added import (`intent_router_action_rewrite_span`), alphabetized, no star-imports, no cycle (protocol→nothing-new).
- **#11 Input validation at boundaries** — COMPLIANT. `ActionRewrite`/`DispatchPackage.action_rewrite` inherit `ProtocolBase` (`extra="forbid"`) — LLM tool output is structurally validated; unknown keys raise `ValidationError` → degraded path. Strings unbounded but never reach SQL/shell/prompt (defense-in-depth gap only, per reviewer-security).
- **CLAUDE.md No-Half-Wired / Verify-Wiring** — COMPLIANT. Producer→consumer traced end-to-end: `decompose` (prompt step-5 + schema description make Haiku emit it) → `dispatch_package` (`websocket_session_handler.py:1031`) → `_presentation_and_untooled_fields` → `result.action_rewrite` → 3 consumers. Not schema-acceptance-only.
- **SOUL.md OTEL-is-the-lie-detector** — COMPLIANT with one polish nit: span emitted on every successful decompose; [EDGE-1][LOW] whitespace-only rewrite reports `emitted=True` while consumers `.strip()` to empty — recommend matching `.strip()` semantics.

### Devil's Advocate

Argue this code is broken. **Attack 1 — the perception firewall.** `action_rewrite.named` now comes from an *upstream* Haiku call and drives `visibility_classifier`'s anchor PC. A malicious/confused router could emit `named="Carl"` on Donut's turn, mis-anchoring the 2nd-person POV swap and leaking Donut's framing to Carl. **Rebuttal:** `visibility_classifier._find_pc_in_text(named, pc_roster)` validates `named` against the session roster *and* an unmatched value falls through to prose-scan then `atmospheric` (`visible_to="all"`) — never a per-player private route (reviewer-security confirmed; `private_segments` derive from `secret_routes`, untouched). Worst case is same-session mis-ID degrading to all-players, not a cross-player leak. **Attack 2 — silent data loss on router failure.** When the intent-router pass degrades (`dispatch_package=None`, operator opt-in at `websocket_session_handler.py:1027`), `result.action_rewrite` is now always `None`, where before the narrator could still supply it. **Rebuttal:** on a router-failure turn the whole mechanical spine is already dark and *loud* (`intent_router.failed` ERROR span); `visibility_classifier` prose-scan fallback and `narration_apply`'s `"unspecified"` default cover it gracefully and observably — this is honest degradation, not a silent regression. **Attack 3 — KeyError from the retired key.** Removing `"action_rewrite"` from `extract_structured_from_response`'s return would `KeyError` any reader still doing `extraction["action_rewrite"]`. **Rebuttal:** grep confirms zero remaining readers; the only two (`_presentation_and_untooled_fields`) were rewritten in the same change (atomic cutover). **Attack 4 — span honesty.** A whitespace-only rewrite reports `emitted=True`. **Conceded as [EDGE-1][LOW]** — real but cosmetic; consumers handle it. **Attack 5 — confused-narrator double-source.** Could both the narrator game_patch AND the pre-pass populate the field? **Rebuttal:** `extract_structured_from_response` no longer surfaces the game_patch value at all (one producer); `output_only.md` no longer instructs it. One mechanism. Net: no Critical/High exposure; the firewall and atomicity hold.

## Reviewer Assessment

**Verdict:** APPROVED

**Findings (all LOW / non-blocking):**

| Severity | Tag | Issue | Location |
|----------|-----|-------|----------|
| [LOW] | [EDGE] | Whitespace-only rewrite → span `emitted=True` while consumers `.strip()` to empty (span honesty) | `sidequest/agents/intent_router.py:543` |
| [LOW] | [EDGE] | `has_action_rewrite` log now stale/misleading (reads ignored raw-patch field) | `sidequest/agents/orchestrator.py:1294,1307` |
| [LOW] | [EDGE]/[TYPE] | Two `ActionRewrite` types (protocol pydantic vs orchestrator dataclass) — field-by-field copy could silently drop a future field | `sidequest/agents/orchestrator.py:3608` |
| [LOW] | [DOC] | `extract_structured_from_response` docstring still lists `action_rewrite` as a returned key | `sidequest/agents/orchestrator.py:1279` |
| [LOW] | [DOC] | `_assemble_turn_result_sdk` docstring still lists `action_rewrite` among sidecar presentation fields | `sidequest/agents/orchestrator.py:3693` |

**Dismissed:** [EDGE-4] "action_rewrite span not nested under decompose" — DISMISSED: this matches the established pattern (`intent_router_pass.py:832,888` fire `confrontation_classified`/`witnessed_act_classified` as standalone post-decompose spans; GM-panel correlation is by SpanRoute `component`/`field` + turn attrs, not OTEL trace parentage).

**Subagent tags:** [EDGE] 4 confirmed (above) · [SEC] clean (reviewer-security: firewall intact, no injection surface, pydantic-validated, no unsafe deser) · [SILENT] disabled — assessed myself: the removed warning has a loud-net span replacement, no swallowed errors in the diff · [TEST] disabled — assessed myself: preflight green, assertions specific, retirement-inversions sound · [DOC] 2 confirmed (stale docstrings above) · [TYPE] disabled — assessed myself: the two-ActionRewrite duplication captured as [EDGE]/[TYPE] LOW · [SIMPLE] disabled — assessed myself: change is minimal, no dead code or over-engineering · [RULE] disabled — assessed myself in Rule Compliance above (python.md #1/#3/#4/#6/#8/#10/#11 + CLAUDE.md wiring + SOUL OTEL).

**Data flow traced:** player action → `IntentRouter.decompose` (produces `action_rewrite` via prompt+schema) → `DispatchPackage` → `execute_intent_router_pre_narrator_pass` → `turn_context.dispatch_package` (`websocket_session_handler.py:1031`) → `_presentation_and_untooled_fields` reads `context.dispatch_package.action_rewrite` → `result.action_rewrite` → `visibility_classifier` (roster-validated anchor) / `confrontation_intent_validator` (None-guarded) / `narration_apply` (None-guarded + `"unspecified"` default). Safe — every consumer handles `None`.

**Pattern observed:** atomic cutover (retire game_patch parse + light pre-pass emit in one change; one producer) at `orchestrator.py:1350` + `_presentation_and_untooled_fields` — exemplary; matches ADR-113 discipline.

**Error handling:** `None` action_rewrite handled at all three consumers (`visibility_classifier.py:128`, `confrontation_intent_validator.py:142`, `narration_apply.py:3672/5236`); `"unspecified"` loud-net default preserved (`narration_apply.py:3675`).

**Verified good:**
- [VERIFIED] All 3 consumers None-safe — `visibility_classifier.py:127-129` guards `if action_rewrite is not None`; `confrontation_intent_validator.py:142` `if action_rewrite is None: return None`; `narration_apply.py:3672` getattr-guarded. Complies with No-Silent-Fallbacks (degradation is observable).
- [VERIFIED] `"unspecified"` loud-net default preserved — `narration_apply.py:3675` `classified_intent = _initial_intent or "unspecified"` fires when `result.action_rewrite` is None. The story guardrail's omitted→unspecified requirement holds (it lives in narration_apply, not the retired orchestrator warning).
- [VERIFIED] No dangling `extraction["action_rewrite"]` readers — grep over `sidequest/` returns zero (atomic cutover). Pydantic `extra="forbid"` on `ActionRewrite`/`DispatchPackage` validates LLM output (`dispatch.py:253`).
- [VERIFIED] Span fires exactly once per successful decompose — placed before `return pkg` inside the success branch; tests assert `len(spans) == 1` for both present and absent cases.

**Handoff:** To SM for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (blocking): retiring the game_patch parse of `action_rewrite` (AC4) leaves
  `NarrationTurnResult.action_rewrite` unsourced for its OTHER post-narrator consumers
  unless the orchestrator sources it from the pre-pass. The orchestrator MUST set
  `result.action_rewrite` from `context.dispatch_package.action_rewrite` in
  `_presentation_and_untooled_fields`. Affects `sidequest/agents/orchestrator.py`
  (`_presentation_and_untooled_fields` ~:3593-3610 — read `context.dispatch_package.action_rewrite`
  instead of `extraction["action_rewrite"]`); without it `confrontation_intent_validator.py:142-144`,
  `narration_apply.py:3668-3672` & `:5236-5248`, and `websocket_session_handler.py:2771` go dark
  (No Silent Fallbacks). Pinned by `test_result_action_rewrite_sourced_from_pre_pass_not_game_patch`.
  *Found by TEA during test design.*
- **Question** (non-blocking): `ActionRewrite` is a dataclass in `agents/orchestrator.py`, but the new
  `DispatchPackage.action_rewrite` field lives in `protocol/dispatch.py` (protocol must not import
  agents). Dev must define a pydantic `ActionRewrite` in `sidequest/protocol/dispatch.py` (or shared
  protocol module) for the field. Affects `sidequest/protocol/dispatch.py` (new model + field).
  *Found by TEA during test design.*
- **Improvement** (non-blocking): the guardrail's omitted→`"unspecified"`/default loud-net is preserved
  as the new pre-pass `intent_router.action_rewrite` span with `emitted=False` (the GM-panel loud net),
  replacing the retired `"action_rewrite absent from extraction"` log warning. Affects
  `sidequest/telemetry/spans/intent_router.py` (new span helper + SpanRoute) and
  `sidequest/agents/intent_router.py` (emit in `decompose`). *Found by TEA during test design.*

### Dev (implementation)
- **Resolved** (non-blocking): TEA's blocking provenance-flip finding is implemented —
  `orchestrator._presentation_and_untooled_fields` now sources `result.action_rewrite` from
  `context.dispatch_package.action_rewrite` and the game_patch parse + absent-warning are gone.
  Out-of-scope consumers (`confrontation_intent_validator`, `narration_apply`, `visibility_classifier`)
  verified green; the protocol-layering Question is resolved (new pydantic `ActionRewrite` in
  `sidequest/protocol/dispatch.py`, converted to the orchestrator dataclass at the assembly seam).
  *Found by Dev during implementation.*
- **Improvement** (non-blocking): production `action_rewrite` emission now depends on Haiku honoring the
  new IntentRouter prompt step + schema descriptions; the `intent_router.action_rewrite` span
  (`emitted=True` rate) is the GM-panel signal to watch. The 151-7 playtest gate should confirm the
  real emit-rate. Affects no file (observability note). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): all 5 review findings are LOW and tracked for a trivial cleanup follow-up
  (none blocks the merge). (1) Whitespace-only rewrite reports span `emitted=True` while consumers `.strip()`
  to empty — match `.strip()` semantics. Affects `sidequest/agents/intent_router.py:543`. (2) `has_action_rewrite`
  log is stale/misleading. Affects `sidequest/agents/orchestrator.py:1294,1307`. (3) `extract_structured_from_response`
  + `_assemble_turn_result_sdk` docstrings still list `action_rewrite`. Affects `sidequest/agents/orchestrator.py:1279,3693`.
  (4) Two `ActionRewrite` types (protocol pydantic vs orchestrator dataclass) copied field-by-field — add a guard or
  unify to prevent silent field-drop on future divergence. Affects `sidequest/agents/orchestrator.py:3608` +
  `sidequest/protocol/dispatch.py:253`. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

5 deviations

- **Pinned `action_rewrite`'s pre-pass home to `DispatchPackage.action_rewrite`**
  - Rationale: `decompose` already returns a `DispatchPackage` whose schema IS the forced tool input; adding the field is the lowest-surface home and reuses the existing call (ADR-150 "no new transport/protocol infrastructure").
  - Severity: minor
  - Forward impact: Dev defines `DispatchPackage.action_rewrite` (pydantic) — see Delivery Findings Question.
- **Realized the "rewire visibility_classifier (:124-129)" as an orchestrator provenance-flip, not a literal signature change**
  - Rationale: keeps ALL post-narrator consumers (confrontation_intent_validator, narration_apply, websocket_session_handler) working off one mechanism (the field, now pre-pass-sourced); an explicit visibility-only param would either break those out-of-scope consumers or duplicate the carrier ("one mechanism per problem"). The field's provenance flips post-narration→pre-pass, which satisfies "reads the pre-pass value instead of the post-narration sidecar value."
  - Severity: major
  - Forward impact: if Reviewer/Dev prefers a literal `classify_narration_visibility(action_rewrite=...)` param, `test_result_action_rewrite_sourced_from_pre_pass_not_game_patch` would be re-pointed at the visibility seam. Flagged for the green/review phases.
- **Pinned the `intent_router.action_rewrite` span to `decompose`**
  - Rationale: `decompose` is where the rewrite is produced; co-locating the span with the producer matches the existing `intent_router.decompose`/`.failed` span placement.
  - Severity: minor
  - Forward impact: none.
- **Added an IntentRouter prompt step + schema field-descriptions for `action_rewrite`, beyond the fixture-test minimum**
  - Rationale: CLAUDE.md "No half-wired features" / "Verify Wiring, Not Just Existence" — schema *acceptance* alone is not production wiring; AC1 requires the producer to emit it. Mirrors how every other DispatchPackage field gets both schema + prompt prose.
  - Severity: minor
  - Forward impact: none — additive guidance; the `intent_router.action_rewrite` span (emitted-rate) is the playtest signal (151-7).
- **Updated three pre-existing tests that encoded the retired narrator-sidecar contract + fixed the provenance-test fixture**
  - Rationale: these encode the contract AC4 retires; leaving them would block GREEN. None weakens an assertion — the output-format tests flip to assert retirement; the fixture fix makes a production-valid state.
  - Severity: minor
  - Forward impact: none.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Pinned `action_rewrite`'s pre-pass home to `DispatchPackage.action_rewrite`**
  - Spec source: context-story-151-3.md, Technical Guardrails ("Emit from intent_router.py")
  - Spec text: "produce action_rewrite (you/named/intent) from the player action it already reads"
  - Implementation: Tests assert `decompose` returns the rewrite on `DispatchPackage.action_rewrite` (the existing single Haiku `emit_tool` call carries it — no new model call), rather than a separate return value or a new IntentRouter method.
  - Rationale: `decompose` already returns a `DispatchPackage` whose schema IS the forced tool input; adding the field is the lowest-surface home and reuses the existing call (ADR-150 "no new transport/protocol infrastructure").
  - Severity: minor
  - Forward impact: Dev defines `DispatchPackage.action_rewrite` (pydantic) — see Delivery Findings Question.
- **Realized the "rewire visibility_classifier (:124-129)" as an orchestrator provenance-flip, not a literal signature change**
  - Spec source: context-story-151-3.md, Technical Guardrails + AC2
  - Spec text: "Rewire visibility_classifier.py (:124-129) to read the pre-pass action_rewrite instead of the post-narration sidecar value"
  - Implementation: AC2 is pinned at the orchestrator seam (`result.action_rewrite` sourced from `context.dispatch_package`, game_patch ignored) rather than adding a pre-pass param to `classify_narration_visibility`. visibility_classifier keeps reading `result.action_rewrite` — which is now the pre-pass value. The existing 14 visibility_classifier tests (anchor-from-`result.action_rewrite`) remain the routing-correctness coverage; no new visibility unit test was added.
  - Rationale: keeps ALL post-narrator consumers (confrontation_intent_validator, narration_apply, websocket_session_handler) working off one mechanism (the field, now pre-pass-sourced); an explicit visibility-only param would either break those out-of-scope consumers or duplicate the carrier ("one mechanism per problem"). The field's provenance flips post-narration→pre-pass, which satisfies "reads the pre-pass value instead of the post-narration sidecar value."
  - Severity: major
  - Forward impact: if Reviewer/Dev prefers a literal `classify_narration_visibility(action_rewrite=...)` param, `test_result_action_rewrite_sourced_from_pre_pass_not_game_patch` would be re-pointed at the visibility seam. Flagged for the green/review phases.
- **Pinned the `intent_router.action_rewrite` span to `decompose`**
  - Spec source: context-story-151-3.md AC3 + ADR-150 §Telemetry (line 237)
  - Spec text: "intent_router.action_rewrite — emitted/derived, on the pre-pass"
  - Implementation: Tests drive `IntentRouter.decompose` and assert the span fires there (one per call, `emitted` bool), rather than in `execute_intent_router_pre_narrator_pass`.
  - Rationale: `decompose` is where the rewrite is produced; co-locating the span with the producer matches the existing `intent_router.decompose`/`.failed` span placement.
  - Severity: minor
  - Forward impact: none.

### Dev (implementation)
- **Added an IntentRouter prompt step + schema field-descriptions for `action_rewrite`, beyond the fixture-test minimum**
  - Spec source: context-story-151-3.md, AC1
  - Spec text: "IntentRouter outputs action_rewrite with you/named/intent derived from the player's raw action"
  - Implementation: Added a step-5 instruction in `intent_router._SYSTEM_PROMPT` AND `Field(description=...)` on the protocol `ActionRewrite` fields + `DispatchPackage.action_rewrite`, so production Haiku actually PRODUCES the field. The fixture tests (fake LLM) pass without this.
  - Rationale: CLAUDE.md "No half-wired features" / "Verify Wiring, Not Just Existence" — schema *acceptance* alone is not production wiring; AC1 requires the producer to emit it. Mirrors how every other DispatchPackage field gets both schema + prompt prose.
  - Severity: minor
  - Forward impact: none — additive guidance; the `intent_router.action_rewrite` span (emitted-rate) is the playtest signal (151-7).
- **Updated three pre-existing tests that encoded the retired narrator-sidecar contract + fixed the provenance-test fixture**
  - Spec source: context-story-151-3.md AC4 + the tests TEA wrote
  - Spec text: "output_only.md no longer instructs the field; NarrationTurnResult no longer parses it from game_patch"
  - Implementation: Inverted `test_narrator.py::test_narrator_output_format_keeps_action_rewrite` → `…_retires_action_rewrite`; removed `"action_rewrite"` from `test_61_12_output_format_compaction.py` `REQUIRED_TOKENS` (following that file's own documented 61-14 token-removal protocol, with a banner); added `bank_result=run_dispatch_bank(pkg)` to the AC2 provenance fixture (a present `dispatch_package` requires its `bank_result` — `build_narrator_prompt` fails loud otherwise; the fixture was a half-state, the assertion is unchanged).
  - Rationale: these encode the contract AC4 retires; leaving them would block GREEN. None weakens an assertion — the output-format tests flip to assert retirement; the fixture fix makes a production-valid state.
  - Severity: minor
  - Forward impact: none.

### Reviewer (audit)
- **TEA #1 (action_rewrite home = `DispatchPackage.action_rewrite`)** → ✓ ACCEPTED by Reviewer: lowest-surface home, reuses the single Haiku call, ADR-150-aligned. Verified the field validates under `extra="forbid"`.
- **TEA #2 (provenance-flip over explicit visibility param)** → ✓ ACCEPTED by Reviewer: this is the *correct* design, not just an acceptable one — it keeps all three out-of-scope consumers (visibility_classifier, confrontation_intent_validator, narration_apply) working off one mechanism and closes the ordering hazard for all at once. I verified each consumer reads `result.action_rewrite` and None-handles. The "major" severity flag is appropriate documentation; the choice itself is sound. The alternative (explicit param) would have silently dark-ed the out-of-scope consumers — this design avoids that.
- **TEA #3 (span on `decompose`)** → ✓ ACCEPTED by Reviewer: co-located with the producer, consistent with `intent_router.decompose`/`.failed`.
- **Dev #1 (prompt step + schema descriptions beyond fixture minimum)** → ✓ ACCEPTED by Reviewer: this is REQUIRED wiring, not scope creep — without it the producer is half-wired (No-Half-Wired). Mirrors how every other DispatchPackage field is steered.
- **Dev #2 (updated 3 pre-existing tests + provenance fixture)** → ✓ ACCEPTED by Reviewer: legitimate contract maintenance. The `test_61_12` token removal follows that file's own documented 61-14 protocol; the `bank_result` fixture fix makes a production-valid state without weakening the assertion. None is a quiet test-weakening.

### Reviewer (audit) — undocumented deviations
- None. Every spec divergence was logged by TEA or Dev. The retirement is atomic (one producer), the field stays for out-of-scope consumers, and the guardrail's `"unspecified"` default is preserved in `narration_apply`.