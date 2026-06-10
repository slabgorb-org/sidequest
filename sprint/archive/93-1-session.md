---
story_id: "93-1"
jira_key: ""
epic: "93"
workflow: "tdd"
---
# Story 93-1: Haiku archetype inference unblocks all-freeform chargen

> **Recovery note (2026-06-10, Dev phase):** a testing-runner subagent overwrote this
> session file with its test-run report (the known clobber hazard). Reconstructed
> verbatim from in-context copies; the only loss should be formatting drift.

## Story Details
- **ID:** 93-1
- **Epic:** 93
- **Jira Key:** (not configured; Jira integration disabled for this project)
- **Points:** 5
- **Priority:** p2
- **Workflow:** tdd
- **Repos:** sidequest-server

## Story Summary
Resolve the all-freeform chargen hard-block with a Haiku one-shot archetype inference. When the archetype gate would BLOCK with missing_axes_with_pack_axes — i.e., the pack declares base_archetypes/archetype_constraints but the accumulated jungian_hint/rpg_role_hint pair is incomplete — AND the player supplied freeform answers, run a single Haiku call over the accumulated freeform text to infer the missing axis value(s), constrained to the pack's valid enum values.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-10T06:21:24Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-10T04:42:51Z | 2026-06-10T04:44:29Z | 1m 38s |
| red | 2026-06-10T04:44:29Z | 2026-06-10T05:13:05Z | 28m 36s |
| green | 2026-06-10T05:13:05Z | 2026-06-10T05:58:20Z | 45m 15s |
| review | 2026-06-10T05:58:20Z | 2026-06-10T06:06:27Z | 8m 7s |
| red | 2026-06-10T06:06:27Z | 2026-06-10T06:09:48Z | 3m 21s |
| green | 2026-06-10T06:09:48Z | 2026-06-10T06:17:18Z | 7m 30s |
| review | 2026-06-10T06:17:18Z | 2026-06-10T06:21:24Z | 4m 6s |
| finish | 2026-06-10T06:21:24Z | - | - |

## Development Context

**Branch Strategy:** gitflow (feat/93-1-haiku-archetype-inference)
**Stack Parent:** none (stack root)

### Acceptance Criteria

1. Heavy_metal/barsoom chargen answered ENTIRELY via freeform (origins+crucible+obligation+the_road in the 'describe in your own words' box): Create Character succeeds — no 'archetype resolution failed (missing_axes_with_pack_axes)'.

2. The inferred jungian_hint and rpg_role_hint are each one of the pack's declared axis values (out-of-enum Haiku output is rejected, not coerced).

3. When a preset already set ONE axis and freeform must supply the other, inference fills only the missing axis and leaves the preset-set one untouched.

4. When the gate would block AND there is no freeform text to infer from, chargen still fails loud with the existing error (no archetype invented, no pack-default fallback).

5. A chargen.archetype_inferred OTEL span fires on every inference with attrs: inferred_axes, jungian_hint, rpg_role_hint, source='freeform', and is visible on the GM panel (Observability Principle — lie detector distinguishes inferred vs preset-accumulated).

6. Wiring test: the inference path is reachable from the production chargen build/gate flow (not just unit-callable) — a test drives the all-freeform build end-to-end and asserts the span + resolved archetype.

7. Haiku call accounts to the session cost ledger and respects the ADR-134 ceiling (no unmetered caller).

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): the autouse `_default_archetype_hints` fixture in `tests/server/conftest.py` silently stamps `hero`/`tank` onto ANY builder whose hints are both None, which masked the [BAR-1] all-freeform block during test design — any future server test about the both-None hint state will be silently un-blocked the same way.
  Affects `sidequest-server/tests/server/conftest.py` (consider an opt-out marker/fixture instead of requiring closure-surgery; `test_93_1_archetype_inference.py::_disable_default_hint_stamping` documents the current workaround).
  *Found by TEA during test design.*
- **Question** (non-blocking): story context AC2 says the error should read "archetype inference failed (invalid_enum_value)" while its technical sketch raises "archetype resolution failed (inference_invalid)". Tests pin only the load-bearing part (an ErrorMessage whose text contains "inference", distinguishable from the plain missing-axes block); Dev may choose either wording.
  Affects `sidequest-server/sidequest/server/websocket_handlers/chargen_mixin.py` (pick one error string).
  *Found by TEA during test design.*
- **Improvement** (non-blocking): barsoom has no name-entry scene (name comes from lobby player_name), so the "name-scene text is not inference fodder" rule is untestable on this substrate; if a heavy_metal world gains a name scene, add a test that the name answer alone does not trigger inference.
  Affects `sidequest-server/tests/server/test_93_1_archetype_inference.py` (future coverage note).
  *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): with a live `ANTHROPIC_API_KEY` in the developer environment, four 45-6 pumblestone gate tests were making REAL billed Anthropic API calls once the 93-1 inference seam landed (missing axes + freeform fodder → real Haiku call → gate passed). Fixed in this story with the autouse `_no_real_anthropic_sdk` hermeticity guard in `tests/server/conftest.py` (third leg alongside `_mock_claude_client` and `_stub_intent_router_factory`) plus inference stubs in the four gate tests; flagging so Reviewer scrutinizes the guard and so other repos' suites get the same audit.
  Affects `sidequest-server/tests/server/conftest.py` (guard added — review for completeness).
  *Found by Dev during implementation.*
- **Gap** (non-blocking): `tests/protocol/test_api_contract_aside.py` fails on this checkout because `orc-quest/docs/api-contract.md` no longer exists (removed/moved by the reference-SPA migration on the orchestrator side). Pre-existing, unrelated to 93-1; the contract test needs repointing at the new reference location.
  Affects `sidequest-server/tests/protocol/test_api_contract_aside.py` (repoint at the reference SPA source or restore the doc).
  *Found by Dev during implementation.*
- **Gap** (non-blocking): a testing-runner subagent overwrote `.session/93-1-session.md` with its run report mid-story (recurring hazard already in project memory) and also committed directly to the feature branch (`a6f2942a`) — the commit was reviewed after the fact and kept, but runner subagents should be report-only.
  Affects `.session/93-1-session.md` (reconstructed) and testing-runner discipline (prompts now say report-only).
  *Found by Dev during implementation.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Inference function signature uses `base=` + `constraints=` instead of the sketch's `pack_constraints=`**
  - Spec source: context-story-93-1.md, "Inference Implementation" sketch
  - Spec text: "infer_archetype_from_freeform(freeform_text=..., pack_constraints=pack.archetype_constraints, existing_hints=...)"
  - Implementation: tests pin keyword-only `freeform_text`, `base` (BaseArchetypes), `constraints` (ArchetypeConstraints), `existing_hints`, `session_id`
  - Rationale: the sketch references `pack_constraints.jungian_axis.enum`, which does not exist on the real `ArchetypeConstraints` model; the valid axis ids live on `BaseArchetypes.jungian[*].id` / `.rpg_roles[*].id`. The pinned shape mirrors the existing `resolve_archetype(base=, constraints=)` seam, and `session_id` is required by the 91-4 keyword-only cost-coverage doctrine
  - Severity: minor
  - Forward impact: Dev implements to the test-pinned signature; story context sketch is illustrative pseudocode
- **Out-of-enum error text pinned loosely, not verbatim**
  - Spec source: context-story-93-1.md, AC-2
  - Spec text: 'Error message is clear: "archetype inference failed (invalid_enum_value)"'
  - Implementation: tests assert an ErrorMessage whose text contains "inference" (case-insensitive), plus not-persisted / not-Playing / no success span / WARNING log
  - Rationale: the story context contradicts itself (AC2 wording vs sketch's "inference_invalid"); pinning a verbatim string would force one side of an internal conflict. The behavioral requirement — a loud, inference-attributed failure distinct from the missing-axes block — is fully pinned
  - Severity: minor
  - Forward impact: Dev picks the final wording; Reviewer should confirm it names inference
- **AC1 "Create Character succeeds" pinned with exactly ONE Haiku call**
  - Spec source: context-story-93-1.md, Implementation Notes (Cost Transparency)
  - Spec text: "Cheap, targeted (single per chargen)"
  - Implementation: wiring test asserts `create.call_count == 1` on the confirm flow
  - Rationale: makes the single-call cost contract executable rather than advisory
  - Severity: minor
  - Forward impact: a retry loop inside the inference would need an explicit spec change and test update

### Dev (implementation)
- **Inference runs BEFORE the 45-6 gate evaluates, not after a blocked verdict**
  - Spec source: context-story-93-1.md, "Technical Approach" sketch
  - Spec text: "Gate detects missing_axes_with_pack_axes AND freeform answers exist" (sketch places inference inside the gate's block branch)
  - Implementation: `_maybe_infer_archetype_from_freeform` checks the would-block predicate (provenance None + resolved None + pack-has-axes) before `_gate_archetype_resolution` runs; on success the gate then evaluates `ok_resolved` normally
  - Rationale: running inference after a blocked verdict would emit the `chargen.archetype_gate_blocked` span + WARNING for a chargen that ultimately ships — a lying lie-detector. The pre-gate intercept keeps gate telemetry truthful on every path
  - Severity: minor
  - Forward impact: none — the gate remains the sole shipper/blocker; inference only changes the state the gate inspects
- **Error wording: "archetype inference failed ({block_reason})" via the existing error code**
  - Spec source: context-story-93-1.md, AC-2 (conflicting wordings, see TEA deviation)
  - Spec text: '"archetype inference failed (invalid_enum_value)"'
  - Implementation: when an inference was attempted and the gate still blocks, the ErrorMessage reads "Character creation incomplete: archetype inference failed ({block_reason}). Please re-run chargen." with the existing `chargen_archetype_unresolved` code; the specific cause (out-of-enum / declined / unresolvable pair / call failure) is in the WARNING log
  - Rationale: keeps the typed error code stable for the UI while naming inference for the operator; the granular cause belongs in logs/OTEL, not the player-facing string
  - Severity: minor
  - Forward impact: none
- **Hermeticity guard added to tests/server/conftest.py (out-of-sketch scope)**
  - Spec source: context-story-93-1.md (no test-infra changes specified)
  - Spec text: n/a — spec silent on test hermeticity
  - Implementation: autouse `_no_real_anthropic_sdk` fixture patches `llm_factory.build_async_anthropic` to raise; `test_app.py::test_create_app_uses_build_llm_client_by_default` patched to install a fake; testing-runner's commit `a6f2942a` (inference stubs in four 45-6 gate tests) reviewed and kept
  - Rationale: the new seam made the real SDK reachable from ordinary WS tests — four tests were observed making live billed API calls on a machine with a real key. Letting that stand violates hermeticity and silently spends money on every dev/CI run
  - Severity: minor
  - Forward impact: any future server test that wants the real SDK must install a fake or deliberately shadow the guard

## Sm Assessment

Setup complete for 93-1 (Haiku archetype inference unblocks all-freeform chargen, 5pt, p2, epic 93).

- **Session file:** created with workflow/phase/repos metadata.
- **Story context:** `sprint/context/context-story-93-1.md` written with technical approach and all 7 ACs from epic 93 YAML (the recurring sm-setup context gap was checked and does not apply — file exists and is populated).
- **Epic context:** `sprint/context/context-epic-93.md` created.
- **Branch:** `feat/93-1-haiku-archetype-inference` cut from `develop` in sidequest-server per repos.yaml.
- **Jira:** explicitly skipped — story has no jira_key in sprint YAML; Jira integration not configured for this story.
- **Merge gate:** clear — no in_progress/in_review stories and no blocking open PRs at research time.
- **Routing:** workflow `tdd` is phased; next phase `red`, owner `tea`. TEA should write failing tests for the 7 ACs including the mandatory wiring test that the inference path is reachable from the production chargen flow.

## TEA Assessment

**Tests Required:** Yes
**Reason:** 5pt TDD feature story — new inference seam, new gate branch, new OTEL span, new cost-ledger caller.

**Test Files:**
- `sidequest-server/tests/server/test_93_1_archetype_inference.py` — 13 tests: WS-driven wiring tests on heavy_metal/barsoom (mirrors the 45-6 gate-test fixture doctrine: per-test PG isolation, real content with skip-if-missing, InMemorySpanExporter on the real tracer), unit contract for `infer_archetype_from_freeform`, span-route registration, ADR-134 ledger/ceiling coverage.

**Tests Written:** 13 tests covering 7 ACs
**Status:** RED (verified twice via testing-runner, `-n0` serial per the OTEL-xdist deadlock note: 12 failing for the right reasons — 8 ImportError on `infer_archetype_from_freeform`, 1 ImportError on `SPAN_CHARGEN_ARCHETYPE_INFERRED`, 3 WS tests blocking with `missing_axes_with_pack_axes` because the inference doesn't exist; 1 passing — the AC4 baseline pin that the no-freeform path already fails loud today). Committed as `fc4e82a5` on `feat/93-1-haiku-archetype-inference`.

**Contract pinned for Dev (Julia):**
- `sidequest.agents.llm_factory.infer_archetype_from_freeform` — async, keyword-only `freeform_text`, `base`, `constraints`, `existing_hints`, `session_id`; returns dict of ONLY newly-inferred axes, `{}` when nothing is missing or Haiku declines (nulls), `None` on out-of-enum or empty freeform; no SDK call when nothing to infer (empty text or nothing missing); SDK obtained via `build_async_anthropic` (the 91-1 single construction site — the tests fake THAT seam); ADR-134 pre-flight `check_ceiling` + post-call `record_call`.
- Confirm-seam wiring in `chargen_mixin.py`: when the 45-6 gate would block with `missing_axes_with_pack_axes` AND real freeform answers exist, infer → resolve the (preset-preserved) pair via `resolve_archetype` → `apply_archetype_resolved` → ship. Out-of-enum → loud ErrorMessage naming inference + WARNING log + nothing persisted. No freeform → existing block untouched, zero SDK calls.
- `SPAN_CHARGEN_ARCHETYPE_INFERRED = "chargen.archetype_inferred"` in `sidequest/telemetry/spans/chargen.py`, registered in `SPAN_ROUTES` with `component="character_creation"`; attrs `inferred_axes` (only the actually-inferred axes), final `jungian_hint`/`rpg_role_hint`, `source="freeform"`; fires ONLY on successful inference.

**Implementation warnings for Dev:**
1. **Apply inferred hints via the resolution path, not by re-deriving `accumulated()`.** The test harness (and the 45-6 doctrine) wraps `CharacterBuilder.accumulated` to control hint state; an implementation that writes inferred values somewhere and then re-reads `accumulated()` will see them clobbered. The story sketch's shape (fill local hint vars → `resolve_archetype` → `apply_archetype_resolved`) is the compatible one.
2. **The autouse `_default_archetype_hints` conftest fixture stamps hero/tank over both-None hints.** The 93-1 tests strip it with `_disable_default_hint_stamping`; don't be confused when an unrelated server test never hits your new branch.
3. "Has freeform answers" should mean hint-bearing freeform scene results (`FreeformInput` entries on `builder._results`), not the name answer — barsoom has no name scene so the tests don't pin this, but worlds with name scenes make it load-bearing (see Delivery Findings).

### Rule Coverage

| Rule (python.md) | Test(s) | Status |
|------|---------|--------|
| #1 silent exceptions / No Silent Fallbacks | `test_out_of_enum_inference_fails_loud`, `test_out_of_enum_returns_none_no_coercion`, `test_null_axes_from_haiku_yield_empty_not_invented_values`, `test_preset_only_missing_axes_still_blocks_without_haiku_call` | failing (last one passing — pins current behavior) |
| #4 logging on error paths | `test_out_of_enum_inference_fails_loud` (WARNING log assertion) | failing |
| #6 test quality (self-check) | every test asserts specific values/messages; no `assert True`, no bare truthiness on always-true values | done |
| #11 input validation at boundaries | enum validation tests (out-of-enum, empty freeform short-circuit) | failing |
| ADR-134 cost coverage | `test_inference_records_to_session_ledger`, `test_inference_respects_hard_ceiling_preflight` | failing |
| OTEL Observability Principle | `test_span_constant_and_gm_panel_route_exist`, span assertions in WS tests | failing |
| CLAUDE.md wiring test | `test_all_freeform_chargen_succeeds_end_to_end` (SDK reachable from production confirm seam, exactly once) | failing |

**Rules checked:** 5 of 13 lang-review rules applicable to test-design phase have coverage; the rest (#2, #3, #5, #7–#10, #12, #13) bind on Dev's implementation diff and are enforced at review.
**Self-check:** 0 vacuous tests found (one `assert create.call_count == 0` family intentionally pins the no-call contract — meaningful, not vacuous).

**Handoff:** To Julia (Dev) for GREEN — implement `infer_archetype_from_freeform`, the chargen_mixin wiring, and the span registration to the pinned contract.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed (sidequest-server, branch `feat/93-1-haiku-archetype-inference`):**
- `sidequest/agents/llm_factory.py` — new `infer_archetype_from_freeform` (single-shot forced-tool Haiku call via the 91-1 construction site; ADR-134 pre-flight ceiling + `record_call` under caller `archetype_inference`; out-of-enum rejects the whole inference; empty fodder / nothing-missing short-circuit with zero SDK calls; bare-string system prompt — deliberately uncached, sub-floor)
- `sidequest/server/websocket_handlers/chargen_mixin.py` — `_maybe_infer_archetype_from_freeform` pre-gate intercept at the confirm seam: would-block predicate → fodder check → infer → fill ONLY missing axes (preset preserved) → resolve via the existing `_resolve_character_archetype` path → emit `chargen.archetype_inferred` span; blocked-after-attempt errors name inference; every failure mode logs WARNING
- `sidequest/game/builder.py` — `freeform_answer_texts()` (revert-safe, name-scene excluded) + `scene_id` stamping in `apply_freeform`
- `sidequest/telemetry/spans/chargen.py` — `SPAN_CHARGEN_ARCHETYPE_INFERRED` + `SPAN_ROUTES` entry (GM-panel routing)
- `tests/server/conftest.py` — autouse `_no_real_anthropic_sdk` hermeticity guard (see Delivery Findings: four gate tests were making REAL billed API calls)
- `tests/server/test_app.py` — fake SDK installed in the factory-resolution test (guard compliance)
- `tests/server/test_45_6_chargen_archetype_gate.py` — `_disable_archetype_inference` stubs in the four pumblestone blocked tests (committed by testing-runner as `a6f2942a`, reviewed and kept; ruff-format pass folded into the feature commit)

**Tests:** 13/13 story tests passing; full server suite 11,258 passed / 348 skipped / 1 failed (`test_api_contract_aside` — pre-existing, orchestrator doc removed by the reference-SPA migration, unrelated)
**Branch:** `feat/93-1-haiku-archetype-inference` (pushed; commits `fc4e82a5` tests, `a6f2942a` gate-test stubs, `12dca843` implementation + guard)

**Handoff:** To The Thought Police (Reviewer) for the review phase (this tdd workflow routes green → review directly).
## Subagent Results (first review pass, 2026-06-10)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (2 content-guard skips noted, acceptable) | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 11 | confirmed 2, dismissed 6, deferred 3 |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | findings | 2 | confirmed 2 (1 downgraded with rationale) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (3 enabled returned; 6 disabled via workflow.reviewer_subagents)
**Total findings:** 4 confirmed (1 HIGH, 1 MEDIUM, 2 LOW), 7 dismissed (with rationale), 3 deferred

### Finding Triage (edge-hunter + security)

Confirmed:
- **[HIGH] [EDGE] Uncaught Anthropic SDK exceptions crash the chargen confirm and drop the WS connection.** `_maybe_infer_archetype_from_freeform` catches only `(LlmClientError, AnthropicSdkCostCeilingExceeded)`; the real `sdk.messages.create` raises `anthropic.APIConnectionError` / `APIStatusError` / `RateLimitError` (base `anthropic.AnthropicError` — NOT in our exception family), and `dict(block.input)` can raise `TypeError` on an SDK shape change. Verified the escape path myself: `websocket.py:133` dispatch has an outer `except Exception → _surface_unexpected` that sends a generic "Server error" frame and then EXITS the receive loop into `finally` teardown — the player is disconnected mid-chargen. The designed behavior (WARNING + loud `archetype inference failed` block, session intact) never engages on the single most likely production failure (a transient API blip). Fix at `chargen_mixin.py` except clause: broaden to cover SDK/transport/shape errors (e.g. `except Exception` with rationale comment, or `anthropic.AnthropicError` + `TypeError` explicitly), log WARNING, return attempted=True.
- **[MEDIUM] [SEC] Unbounded player freeform text joined into the Haiku input.** `CharacterCreationPayload.choice` is an unbounded `str`; uvicorn's WS frame cap (~16MB) is the only limit. python.md #11 (input validated at boundaries — length) violated at `llm_factory.py` user-message build. Severity MEDIUM, not HIGH as the security agent proposed: the model context window caps billable input (~200k tokens ≈ $0.2/call on Haiku — not a multi-dollar ceiling bypass), `record_call` books it and the ceiling kills repeats. BUT an oversized input draws an `APIStatusError 400`, which today rides the HIGH crash path above. Fix: truncate the joined fodder to a fixed bound (e.g. 4,000 chars) before the call, with a log line when truncation fires.
- **[LOW] [SEC] No structural delimiter around player text in the prompt.** ADR-047 role separation IS maintained (system separate, player text in user role) and the forced tool_choice + enum validation cap the blast radius at self-DoS; defense-in-depth suggestion: wrap player text in an XML-style delimiter when fixing the truncation. Non-blocking.
- **[LOW] [EDGE] Pack with non-empty axes objects but EMPTY id lists silently drops the axis from `missing`.** Content misconfiguration surface — belongs in the pack validator (project doctrine: content invariants live in the validator, not runtime), but a WARNING log at the empty-enum branch would aid diagnosis. Non-blocking.

Dismissed (rationale):
- `existing_hints` unknown keys [EDGE low] — the function owns its axis set; `axis_enums` is authoritative and unknown keys cannot alter behavior. Defensive assert is scope creep.
- `resolver_raised` state skips inference [EDGE low] — intentional: a raw pair means presets accumulated BOTH hints; inference must never override preset hints (AC3). Predicate documented in the new code comment.
- session-id composite collision [EDGE low] — verbatim the established intent-router/seed-deck ladder (websocket_session_handler.py:835-841); changing it here would fork the session-identity doctrine.
- `"/"` in archetype id mis-split [EDGE medium] — requires a pack author to ship an id containing `/`; the resolver then raises and the gate blocks loudly (verified: `_resolve_character_archetype` catch → no provenance → blocked). Content-invariant for the pack validator, not runtime code.
- AC3 missing SDK-called assertion [EDGE medium] — AC3 asserts the `chargen.archetype_inferred` span with `inferred_axes == {"rpg_role_hint"}`; that span fires only on the successful inference path, so the test cannot false-pass if stamping is left on (confirm would pass with NO span → assertion fails). Self-protecting.
- empty `_scenes` degenerate [EDGE low] — returns `[]` gracefully; no production path.
- name-scene-is-last invariant [EDGE low] — `_is_name_scene` is pre-existing 93-1-unrelated logic; content invariant, validator lane.

Deferred:
- followup_text excluded from inference fodder [EDGE medium] — genuine design question (hook-prompt answers may carry archetype signal); deferred to Delivery Findings as a non-blocking Improvement rather than blocking this story.
- prompt delimiter hardening [SEC] — folded into the LOW above; do alongside the truncation fix.
- empty-enum WARNING — folded into LOW above.

### Rule Compliance

Rules from `.pennyfarthing/gates/lang-review/python.md` + CLAUDE.md, checked against every changed type/function:

| Rule | Instances checked | Verdict |
|------|-------------------|---------|
| #1 silent exceptions | `infer_archetype_from_freeform` (raises on no-tool-use, returns None loudly on out-of-enum), `_maybe_infer_archetype_from_freeform` except clause, conftest `_refuse` | COMPLIANT on swallowing — but the except clause is too NARROW (the inverse failure; see HIGH) |
| #2 mutable defaults | all new functions keyword-only with no mutable defaults | compliant |
| #3 type annotations at boundaries | `infer_archetype_from_freeform`, `freeform_answer_texts`, `_maybe_infer_archetype_from_freeform` all fully annotated (TYPE_CHECKING imports for genre models per #10) | compliant |
| #4 logging | every failure branch logs WARNING with lazy %s formatting; success logs INFO; no player text, keys, or PII in any format string (verified each of the 6 new log lines) | compliant |
| #6 test quality | 93-1 test file: every test asserts concrete values; the 45-6 stub additions preserve existing assertions; `test_app` fix asserts the same isinstance | compliant |
| #8 unsafe deserialization | `dict(block.input)` consumes SDK-deserialized structures, then enum-validates before use | compliant (shape-change TypeError folded into HIGH fix) |
| #9 async pitfalls | single awaited SDK call; no blocking I/O in the async path; no gather | compliant |
| #10 import hygiene | genre model imports are TYPE_CHECKING-only; mixin uses function-level late-bound imports per the 91-1 doctrine | compliant |
| #11 input validation | freeform emptiness checked; out-of-enum rejected; **length NOT bounded → MEDIUM finding** | VIOLATION (MEDIUM) |
| ADR-134 cost | pre-flight `check_ceiling` + post-call `record_call` under dedicated caller tag; single call per chargen (test-pinned) | compliant |
| OTEL Observability Principle | success span SPAN_ROUTES-registered (component=character_creation); every decision branch logged | compliant |
| No Silent Fallbacks | no coercion, no pack-default, no-fodder path untouched; verified the AC4 test pins it | compliant |

### Devil's Advocate

Assume this code is broken; argue it. A player on hotel Wi-Fi finishes a heartfelt all-freeform chargen on barsoom, hits Create Character — and Anthropic's edge returns a 529. `APIStatusError` is not `LlmClientError`; it sails through the narrow except, through `_chargen_confirmation`, into `websocket.py`'s outer catch, which sends "Server error while processing message" and tears the socket down. The player is disconnected, their chargen state ambiguous, and the carefully designed "archetype inference failed, please re-run chargen" path — the entire point of failing loud at the gate — never ran. Worse, the operator reading the GM panel sees no inference span, no gate-blocked span for this confirm, just a generic ws.unexpected_error: the lie detector is blind exactly when the new subsystem fails. Now the hostile case: Sebastien (mechanics-first, curious) pastes a 40,000-word fanfic into the origins box three times. The join produces ~120k words → the API 400s on context length → same crash path, reproducible at will, a one-player WS-session kill switch. Even below the context cap he can grind $0.15-0.20 per confirm attempt before the cumulative ceiling reacts — cheap per call, but the confirm button is free to press. The confused-user case: Haiku declines both axes; the player sees "archetype inference failed (missing_axes_with_pack_axes)" and has NO idea what to change — the message names the mechanism, not the remedy ("describe your character's calling in more detail"). That's a UX gap (LOW, noted) but not a blocker. The conclusion of the exercise: the two confirmed findings are the same wound — the seam trusts the network and the player input; neither trust is earned. Both surfaced in findings; the rejection stands on them.

### Additional observations (review checklist)

- [VERIFIED] Data flow traced end-to-end: player freeform (`CharacterCreationPayload.choice`) → `apply_freeform` → `SceneResult(FreeformInput, scene_id)` (builder.py:1858-1870) → `freeform_answer_texts()` name-scene-excluded join (builder.py:1902-1927) → user-role Haiku message (llm_factory.py) → forced tool_use → enum validation against `base.jungian[*].id`/`.rpg_roles[*].id` → only-missing-axes dict → preset-preserving merge (`existing or inferred`, chargen_mixin) → raw-pair write → `_resolve_character_archetype` four-tier shim → `apply_archetype_resolved` provenance lockstep → 45-6 gate `ok_resolved`. Safe because player text can only select among pack-declared enum values, and the resolver re-validates the pair. Complies with No Silent Fallbacks + ADR-047 role separation.
- [VERIFIED] Wiring: inference reachable from the production confirm seam — `_chargen_confirmation` calls `_maybe_infer_archetype_from_freeform` before the gate (chargen_mixin.py:832-849); the AC1 wiring test asserts `create.call_count == 1` against the production WS dispatch, not a unit seam.
- [VERIFIED] Preset-never-overridden: `jungian = existing_hints[...] or inferred.get(...)` ordering + the inference function strips non-missing axes; AC3 test adversarially returns both axes and asserts the preset survives.
- [VERIFIED] Gate telemetry stays truthful: inference runs BEFORE the gate, so no `archetype_gate_blocked` span fires for a chargen that ships (Dev deviation #1, audited ACCEPTED below) — evidence: call order at chargen_mixin.py:846-861.
- [VERIFIED] Hermeticity guard: `_no_real_anthropic_sdk` (conftest) raises on unfaked SDK construction; LIFO shadowing preserved for tests installing fakes; full suite green except one pre-existing unrelated failure. The guard caught a real money leak (4 gate tests billing live calls) — good pattern, matches the `_mock_claude_client` / `_stub_intent_router_factory` doctrine.
- [LOW] Player-facing failure message names the mechanism, not the remedy — "archetype inference failed (missing_axes_with_pack_axes)" gives a narrative-first player (Alex) nothing actionable. Suggest future copy pass; non-blocking.

## Reviewer Assessment (rejected 2026-06-10 — superseded by re-review below)

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] [EDGE] | Anthropic SDK/transport/shape exceptions (`anthropic.APIConnectionError`, `APIStatusError`, `RateLimitError`, `TypeError` from `dict(block.input)`) escape the narrow `except (LlmClientError, AnthropicSdkCostCeilingExceeded)`, crash the confirm dispatch, and drop the player's WS connection via websocket.py's outer catch — the designed loud-block path never engages on the most likely production failure | `sidequest/server/websocket_handlers/chargen_mixin.py` (`_maybe_infer_archetype_from_freeform` try/except) | Broaden the catch so ANY inference-seam failure degrades to the WARNING + `inference_attempted=True` loud-block path (e.g. `except Exception` with rationale comment, or explicitly add `anthropic.AnthropicError` and `TypeError`). Add a failing test first: fake SDK whose `messages.create` raises a non-LlmClientError exception → confirm must return the inference-failed ErrorMessage, NOT propagate |
| [MEDIUM] [SEC] | Player freeform fodder joined and sent to Haiku with no length bound (python.md #11) — enables ~$0.2/call grinding and, above the context window, a reproducible 400 that rides the HIGH crash path | `sidequest/agents/llm_factory.py` (user-message build) | Truncate the joined fodder to a fixed bound (e.g. 4,000 chars) before the SDK call, log when truncation fires; wrap player text in a structural delimiter while there (ADR-047 defense-in-depth). Add a test: oversized fodder → call payload bounded |
| [LOW] [EDGE] | Empty axis-id lists on an axis-bearing pack silently drop the axis from inference | `sidequest/agents/llm_factory.py` | Optional WARNING log; primary home is the pack validator. Non-blocking |
| [LOW] [SEC] | No delimiter around player text in the prompt (role separation correct; blast radius self-only) | `sidequest/agents/llm_factory.py` | Fold into the MEDIUM fix. Non-blocking |

Tags coverage: [EDGE] confirmed above; [SEC] confirmed above; [SILENT] subagent disabled — covered by my own pass (No Silent Fallbacks compliant; the defect found is the inverse: too-narrow catch); [TEST] disabled — my pass: suite green, 13 story tests meaningful, 2 content-guard skips acceptable; [DOC] disabled — my pass: new docstrings accurate, no stale comments found in diff; [TYPE] disabled — my pass: boundaries fully annotated, TYPE_CHECKING imports correct; [SIMPLE] disabled — my pass: no dead code; the seam reuses `_resolve_character_archetype` rather than reinventing; [RULE] disabled — covered by the Rule Compliance table above.

**Data flow traced:** player freeform → builder results → name-scene-excluded join → user-role Haiku message (forced tool, enum-validated) → preset-preserving merge → four-tier resolver → provenance-stamped archetype (safe: output constrained to pack enums, resolver re-validates, gate remains sole shipper)
**Pattern observed:** good — pre-gate intercept keeps 45-6 gate telemetry truthful (chargen_mixin.py:832-861); good — hermeticity tripod completed in tests/server/conftest.py
**Error handling:** the defect — external-failure taxonomy not covered at the new seam (HIGH above); everything our own code raises IS handled loudly
**Handoff:** Back through red — O'Brien (TEA) writes the failing tests for the two fixes, Julia (Dev) makes them green. Rework is small and localized.

### Reviewer (audit)

Deviation audit — every logged deviation stamped:

- **TEA: Inference function signature uses `base=` + `constraints=`** → ✓ ACCEPTED by Reviewer: the sketch's `pack_constraints.jungian_axis.enum` does not exist on the real model; mirroring `resolve_archetype(base=, constraints=)` is the correct seam, verified against `archetype_axes.py`/`archetype_constraints.py`.
- **TEA: Out-of-enum error text pinned loosely** → ✓ ACCEPTED by Reviewer: the story context genuinely self-contradicts; the behavioral pin (loud, inference-attributed, distinct from missing-axes) is the right contract. Implementation's final wording names inference — confirmed.
- **TEA: exactly ONE Haiku call pinned** → ✓ ACCEPTED by Reviewer: turns the cost note into an executable contract; agrees with ADR-134 intent.
- **Dev: inference runs BEFORE the gate** → ✓ ACCEPTED by Reviewer: verified the alternative (post-block intercept) would fire `archetype_gate_blocked` spans + WARNINGs for chargens that ship — a lying lie-detector. Pre-gate intercept is strictly better; gate remains sole shipper/blocker.
- **Dev: error wording via existing `chargen_archetype_unresolved` code** → ✓ ACCEPTED by Reviewer: stable typed code for the UI + named mechanism for the operator; granular cause in WARNING logs. (Player-facing remedy copy noted as LOW, non-blocking.)
- **Dev: hermeticity guard added (out-of-sketch scope)** → ✓ ACCEPTED by Reviewer: not scope creep — the new seam created the leak the guard plugs; four tests were observed billing live API calls. Matches the two existing autouse-guard precedents in the same conftest.

No undocumented deviations found beyond the above (the testing-runner's direct commit `a6f2942a` is already disclosed in Dev's Delivery Findings).

### Reviewer (code review)

- **Gap** (blocking): Anthropic SDK/transport exceptions escape the inference seam's narrow except and tear down the player's WS session instead of degrading to the loud chargen block.
  Affects `sidequest-server/sidequest/server/websocket_handlers/chargen_mixin.py` (broaden the catch; TEA to pin with a failing test).
  *Found by Reviewer during code review.*
- **Gap** (non-blocking): player freeform fodder is sent to Haiku with no length bound (python.md #11) — bounded in practice by the model context window, but enables per-call cost grinding and an oversized-context 400 that rides the blocking gap above.
  Affects `sidequest-server/sidequest/agents/llm_factory.py` (truncate joined fodder + structural delimiter; fix alongside the blocking gap).
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking): hook-prompt followup answers (`SceneResult.followup_text`) are excluded from the inference fodder; they may carry archetype signal. Decide and document, or extend `freeform_answer_texts()`.
  Affects `sidequest-server/sidequest/game/builder.py` (documentation or extension).
  *Found by Reviewer during code review.*
## TEA Assessment (rework red, post-rejection)

**Tests Required:** Yes — two failing tests pinning the review findings.
**Test Files:** `tests/server/test_93_1_archetype_inference.py` (appended; commit `da304505`)
- `TestSdkFailureDegradesLoudly::test_transport_error_yields_inference_failed_block_not_crash` — WS-driven: fake SDK raises a non-LlmClientError exception; confirm must RETURN the loud inference-failed ErrorMessage (no persist, no Playing, no success span, WARNING logged) instead of propagating. Pins the [HIGH] [EDGE] finding.
- `TestOversizedFodderBounded` (2 tests) — `_ARCHETYPE_INFERENCE_MAX_FODDER_CHARS` exists in llm_factory (1k–16k sane range); a ~480k-char fodder is truncated before the SDK call (captured user message ≤ bound + 2k overhead), inference still succeeds, truncation logged with "truncat". Pins the [MEDIUM] [SEC] finding.

**Status:** RED verified (testing-runner, -n0): 13 prior tests pass, 3 new tests fail for exactly the expected reasons (transport error propagates; constant ImportError ×2).

### Design Deviations — TEA (rework red)
- No deviations from spec: tests pin the Reviewer's required fixes verbatim (bound range and +2k overhead chosen to avoid over-pinning the exact constant; truncation log pinned on the substring "truncat" only).

**Handoff:** To Julia (Dev) — broaden the inference-seam catch and add the fodder bound + truncation log.
## Dev Assessment (rework green)

**Implementation Complete:** Yes (commit `c31eff82`, pushed)
**Files Changed:**
- `sidequest/agents/llm_factory.py` — `_ARCHETYPE_INFERENCE_MAX_FODDER_CHARS = 4_000`; oversized fodder truncated with a WARNING before the SDK call; player text wrapped in `<player_answers>` delimiter (ADR-047 defense-in-depth, the Reviewer's folded LOW)
- `sidequest/server/websocket_handlers/chargen_mixin.py` — inference-seam catch broadened to `except Exception` (rationale comment in place): ANY failure degrades to WARNING + the loud inference-failed chargen block; the WS session survives

### Design Deviations — Dev (rework green)
- No deviations from spec: both fixes implement the Reviewer's required remediations as written; the 4,000-char bound sits inside the test-pinned sane range (1k–16k).

**Tests:** 16/16 story tests passing; 45-6 gate (14) and test_app (7) passing; full suite 11,261 passed / 348 skipped / 1 pre-existing unrelated failure (api-contract doc)
**Branch:** feat/93-1-haiku-archetype-inference (pushed; head `c31eff82`)

**Handoff:** To The Thought Police (Reviewer) for re-review.
## Subagent Results

Re-review pass (rework delta `12dca843..c31eff82`).

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (3 files, 163+/9-, ruff clean, 16/16 green, zero smells) | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 4 | confirmed 1, dismissed 3 |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | findings | 2 | confirmed 0, downgraded 2 (with rationale) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (3 enabled returned; 6 disabled via workflow.reviewer_subagents)
**Total findings:** 1 confirmed (MEDIUM, non-blocking), 2 downgraded to LOW with rationale, 3 dismissed (with rationale)

### Re-review triage

Confirmed (non-blocking):
- **[MEDIUM] [EDGE] Missing `exc_info=True` on the broadened catch's WARNING.** A logic bug inside `infer_archetype_from_freeform` (pre-SDK) now logs only `str(exc)` with no traceback, making diagnosis harder than the pre-rework narrow catch. One-kwarg fix; recorded as a Delivery Finding for follow-up — does not block (python.md #4 mandates logging on error paths, which exists; traceback completeness is an ops-quality improvement).

Downgraded with rationale (PROJECT-rule-matching findings — downgraded, not dismissed):
- **[LOW] [SEC] "broad except swallows AnthropicSdkCostCeilingExceeded / ADR-134 bypass" — claim verified FALSE in its load-bearing part.** The agent asserted the catch "unblocks the chargen 45-6 gate" and lets a killed session "complete chargen and continue billing." Verified against the code: `check_ceiling` raises PRE-flight, before `build_async_anthropic()` — zero tokens billed; the catch returns `inference_attempted=True`, the character carries no provenance, and the gate BLOCKS (the loud inference-failed ErrorMessage). Re-pressing confirm re-refuses pre-flight, billing nothing. The pre-rework code (first review pass) caught the same exception explicitly and deliberately. ADR-134's hard-kill (no further billing) is fully preserved; only the failure SURFACE differs (chargen block vs terminal-refusal frame), which is the designed behavior for this seam. `AnthropicSdkConfigError` (malformed ceiling env): degraded visibility at this one seam only — the identical parse runs loudly in the intent-router constructor every player turn, so misconfiguration cannot hide. Severity LOW, no action this story.
- **[LOW] [SEC] Delimiter escape via a literal `</player_answers>` in player text.** Real but inconsequential: the worst case is biasing which VALID enum value the model picks for the player's own character — achievable legitimately by simply describing oneself differently (no mechanical advantage; Rule of Cool gate untouched). Forced tool_choice + enum validation remain the actual boundary, as the code comment itself states. Optional escape noted for a future pass.

Dismissed (rationale):
- `== limit` boundary untested [EDGE low] — behaviorally correct by inspection (nothing cut → nothing logged); a boundary test is nice-to-have, not load-bearing.
- all-whitespace-after-truncation [EDGE low] — requires 4,000 leading whitespace chars; the SDK call then returns a declined inference → loud block. No silent path.
- pack-authored `constraint_lines` unsanitized [EDGE low] — pack ids are operator-authored content, not a player surface; content invariants live in the pack validator.

### Devil's Advocate (re-review)

Argue the rework is broken: the broad catch is a rug — under it every future bug in the inference function becomes a WARNING line and a player-facing "inference failed," and nobody will notice a `KeyError` introduced by a refactor until a playtest complains that freeform chargen "never works." That is a real maintenance hazard, and it is exactly why the missing `exc_info=True` matters: without the traceback, the operator cannot distinguish "Anthropic was down" from "we shipped a bug." I confirm that as the MEDIUM. Could the truncation betray a player? A 5,000-char backstory loses its final paragraphs silently from the player's view (the WARNING is operator-facing) — the inferred archetype might miss a late-text twist; but the archetype gate still requires a valid pair, the player sees and confirms the result, and 4,000 chars is far beyond the playgroup's real usage (Alex types slowly; James writes paragraphs, not novellas). Could the delimiter give false confidence? The comment explicitly disclaims it as defense-in-depth, not the boundary. Could the ceiling-as-chargen-block confuse a killed session's player? They get "archetype inference failed" rather than "session over budget" — mildly misleading copy, but a killed session is already terminally refusing every narrator turn, so the player's whole table has stopped; chargen copy is the least of it. Nothing here rises to blocking. The two prior HIGHs are demonstrably fixed by failing-tests-now-green.

## Reviewer Assessment

**Verdict:** APPROVED

**Re-review scope:** rework delta `12dca843..c31eff82` on top of the previously-reviewed base; both prior blocking findings verified remediated by failing-test-first rework:
- [HIGH] [EDGE] resolved — `TestSdkFailureDegradesLoudly` proves a non-LlmClientError SDK exception now degrades to the loud inference-failed block (WS session intact); broadened catch carries a rationale comment and excludes `BaseException` signals (`CancelledError`, `KeyboardInterrupt`) by construction.
- [MEDIUM] [SEC] resolved — `TestOversizedFodderBounded` proves the fodder is truncated to `_ARCHETYPE_INFERENCE_MAX_FODDER_CHARS` (4,000, inside the pinned sane range) BEFORE the SDK call with a WARNING; `<player_answers>` delimiter added (ADR-047 defense-in-depth).

**Data flow traced:** oversized hostile freeform → truncation (logged) → delimited user-role message → forced tool_use → enum validation → preset-preserving merge → resolver → gate (safe: bounded cost, output constrained to pack enums)
**Pattern observed:** good — failing-test-first rework, both fixes commit-paired with their pinning tests (`da304505` red, `c31eff82` green) at sidequest/agents/llm_factory.py and sidequest/server/websocket_handlers/chargen_mixin.py
**Error handling:** any inference-seam failure now degrades to WARNING + loud chargen block; remaining gap is traceback completeness (`exc_info=True`) — MEDIUM, non-blocking, in Delivery Findings
**Tags:** [EDGE] confirmed 1 MEDIUM above; [SEC] 2 downgraded LOW with verification rationale; [SILENT] disabled — my pass: degradation paths all log WARNING, none silent; [TEST] disabled — my pass: 3 rework tests meaningful, 16/16 green; [DOC] disabled — my pass: rationale comments accurate and load-bearing; [TYPE] disabled — my pass: constant typed int, no boundary changes; [SIMPLE] disabled — my pass: delta is minimal, no dead code; [RULE] disabled — Rule Compliance re-checked: python.md #11 now COMPLIANT (length bound), #1/#4 compliant (explicit broad-catch with rationale + WARNING), ADR-134 compliant (pre-flight refusal preserved, zero-billing verified), ADR-047 compliant (role separation + delimiter).
**Handoff:** To Winston Smith (SM) for finish-story

### Reviewer (audit — rework pass)

- **TEA (rework red): "No deviations from spec"** → ✓ ACCEPTED by Reviewer: tests pin the two required fixes without over-pinning the constant (range + overhead allowance is the right looseness).
- **Dev (rework green): "No deviations from spec"** → ✓ ACCEPTED by Reviewer: both remediations implemented as required; the `<player_answers>` delimiter was my own folded LOW, in scope.

### Reviewer (code review — rework pass)

- **Improvement** (non-blocking): add `exc_info=True` to the broadened catch's WARNING in `_maybe_infer_archetype_from_freeform` so non-SDK logic bugs keep their tracebacks (the broad catch otherwise flattens them to one line).
  Affects `sidequest-server/sidequest/server/websocket_handlers/chargen_mixin.py` (one kwarg on the logger.warning call).
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking): optionally escape literal `</player_answers>` in player fodder (or move the pairings hint ahead of the delimiter block) — blast radius today is nil (enum-bounded, self-only), so cosmetic hardening only.
  Affects `sidequest-server/sidequest/agents/llm_factory.py` (prompt construction).
  *Found by Reviewer during code review.*