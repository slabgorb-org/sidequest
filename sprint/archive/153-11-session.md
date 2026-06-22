---
story_id: "153-11"
jira_key: ""
epic: "153"
workflow: "tdd"
---
# Story 153-11: [NARRATOR-EMPTY-NARRATION-DEGRADED] harden empty-prose-on-continuation upstream of the degraded-stall guard

## Story Details
- **ID:** 153-11
- **Jira Key:** (none — no Jira integration)
- **Epic:** 153 (Playtest follow-ups — open findings from the 2026-06-20/21 full-stack /sq-playtest sweep)
- **Workflow:** tdd
- **Type:** Bug
- **Points:** 2
- **Priority:** P3
- **Repository:** sidequest-server (targets `develop`)
- **Stack Parent:** none (not a stacked story)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-22T06:36:41Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-22T06:11:44Z | 2026-06-22T06:14:10Z | 2m 26s |
| red | 2026-06-22T06:14:10Z | 2026-06-22T06:24:38Z | 10m 28s |
| green | 2026-06-22T06:24:38Z | 2026-06-22T06:29:13Z | 4m 35s |
| review | 2026-06-22T06:29:13Z | 2026-06-22T06:36:41Z | 7m 28s |
| finish | 2026-06-22T06:36:41Z | - | - |

## Sm Assessment

Setup complete. Story 153-11 ([NARRATOR-EMPTY-NARRATION-DEGRADED]) is ready for the RED phase.

- **Workflow:** tdd (phased) → setup (SM) → red (TEA) → green (Dev) → review (Reviewer) → finish (SM)
- **Repos:** server (sidequest-server, targets `develop`)
- **Branch:** `feat/153-11-narrator-empty-prose-upstream` (cut from sidequest-server `develop` HEAD, clean tree)
- **Story context:** `sprint/context/context-story-153-11.md`
- **Jira:** none (project uses pf sprint, not live Jira)
- **Merge gate:** clear (no open PRs blocking this repo)

**The finding (epic-153 playtest sweep, 2026-06-20 oz/Fate playtest):** During the full-stack playtest, the narrator returned EMPTY player-facing prose on a continuation turn, which triggered the degraded-stall guard. The guard recovered cleanly (no client hang). However, the ROOT CAUSE (narrator emitting empty prose on a continuation) was never addressed upstream of that guard.

**Doctrine reminder for TEA/Dev:** This is a HARDENING story, not a guard rewrite. The degraded-stall guard already recovers correctly and MUST keep working — do not weaken it. The goal is to handle/prevent empty-prose-on-continuation turns UPSTREAM so the guard is a true last resort, not the primary recovery path. Per CLAUDE.md "No Silent Fallbacks" — fail loud, OTEL-emit, do not silently paper over.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Question** (non-blocking): The context doc's stated intent — "so the guard is a true last resort, not the primary recovery path" — admits TWO designs, and the AC list only commits to one. The ACs (AC2/AC3/AC4) scope the upstream work to **detection + loud cause-categorization (span + watcher event)**; they do NOT require a *reprompt-for-prose recovery* that would actually PREVENT the empty turn. My RED tests pin the detection contract only (the degraded-stall guard stays the recovery path). If Dev/Reviewer read "true last resort" as requiring active upstream recovery (e.g. a toolless re-prompt asking the narrator to narrate the result of its tool actions), that is a larger, separately-scopeable change. Affects `sidequest/agents/orchestrator.py` (`_run_narration_turn_sdk` / `_assemble_turn_result_sdk`). *Found by TEA during test design — flagging the fork so Dev doesn't silently pick one; the 2-pt detection-only reading satisfies every AC.*
- **Gap** (non-blocking): The original finding names THREE empty-prose root causes — "tool-only response / prose in the wrong field." My `cause` taxonomy covers the two cleanly-detectable empties (`tool_only_response`, `no_output`); **"prose in the wrong field"** (e.g. prose buried in a tool argument) is NOT categorized here. Note the SDK client already partially handles one wrong-field case — multiple text blocks collapse to the last with a `narrator.multi_text_block_discarded` span (`anthropic_sdk_client.py:529`). A full wrong-field detector is out of scope for this 2-pt story. Affects `sidequest/agents/orchestrator.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Question** (non-blocking): I implemented the **detection-only** read of TEA's design fork (the AC-satisfying one): the upstream signal names the cause but does NOT reprompt-for-prose, so `_guard_empty_narration` remains the recovery path. If the Reviewer/Keith want the guard to become a *true* last resort (an active toolless re-prompt that re-narrates the tool result so the player rarely sees the stall), that is a separately-scopeable follow-up — the span/event contract added here is the diagnostic foundation it would build on. Affects `sidequest/agents/orchestrator.py` (`_assemble_turn_result_sdk`). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `tests/agents/test_153_11_empty_prose_upstream.py` is not `ruff format`-clean — a single one-element-list line-wrap (~line 358). CI does not gate `ruff format` (server-check/check-all run `ruff check`, not `--check`), so this does not block, but `ruff format tests/agents/test_153_11_empty_prose_upstream.py` should be swept in before/at PR creation so HEAD stays format-clean. Affects `sidequest-server/tests/agents/test_153_11_empty_prose_upstream.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): this file mixes `severity="warn"` (3989/4276/4302) and `severity="warning"` (1254) for watcher events. Not introduced by this story and the GM panel recognizes `"warn"` (the live-subscriber test confirms delivery), but a future cleanup could normalize the vocabulary. Affects `sidequest/agents/orchestrator.py`. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Partial coverage of the finding's named root causes**
  - Spec source: context-story-153-11.md, "Problem" (finding text "tool-only response / prose in the wrong field"); AC2
  - Spec text: "empty-prose-on-continuation is detected UPSTREAM with a loud error/warning + OTEL span"
  - Implementation: The `cause` taxonomy under test is `{tool_only_response, no_output}` — the two cleanly-detectable empties. "Prose in the wrong field" is NOT given a test (logged as a Delivery Finding Gap instead).
  - Rationale: Detecting prose-in-the-wrong-field is materially harder (parsing tool arguments for stranded narration) and the SDK client already loud-handles the multi-text-block variant (`narrator.multi_text_block_discarded`). Scoping to the two empty-categories keeps the 2-pt story honest and still closes the playtest repro (the tool-only continuation).
  - Severity: minor
  - Forward impact: a future story can extend the `cause` enum + add a wrong-field detector without changing the span/event contract.

### Dev (implementation)
- No deviations from spec. Implemented exactly the contract TEA pinned: `_emit_empty_prose_upstream_signal` in `_assemble_turn_result_sdk` (SDK-path-only, upstream of the unchanged `_guard_empty_narration`), emitting the `narrator.empty_prose_upstream` span + `narrator_empty_prose_upstream` watcher event with the agreed names, attributes, causes (`tool_only_response`/`no_output`), `severity="warn"`, and stripped-text keying.

### Reviewer (audit)
- **TEA — "Partial coverage of the finding's named root causes" (cause taxonomy = {tool_only_response, no_output}, wrong-field deferred)** → ✓ ACCEPTED by Reviewer: sound and internally consistent. I adversarially traced the wrong-field case (non-empty `result.text` that extracts to empty narration): it correctly stays guard-only because the signal keys on `result.text.strip()`, and the player surface is still recovered. The 2-pt scope cut is well-reasoned and the contract is forward-extensible (add a `cause` value without breaking the span/event shape).
- **Dev — "detection-only read of the design fork (no reprompt-for-prose recovery)"** → ✓ ACCEPTED by Reviewer: matches the context-doc AC list (AC2/AC3/AC4 = detection + loud + OTEL + watcher; no AC mandates recovery). The degraded-stall guard remains the recovery path, verified intact. Reprompt-for-prose is a legitimately separate, larger follow-up — correctly deferred, not silently dropped.
- No undocumented deviations found. The implementation matches the tests and the documented scope exactly.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Bug-hardening story with observable OTEL/watcher contract — every AC is testable.

**Test Files:**
- `sidequest-server/tests/agents/test_153_11_empty_prose_upstream.py` — 8 tests, SDK-path-driven via `FakeAnthropicSdkClient` + the live `run_narration_turn` entry point.

**Tests Written:** 8 tests covering 4 ACs
**Status:** RED (5 failing on the missing upstream span/event, 2 passing absence-asserts, 1 coexistence) — verified by testing-runner (run_id 153-11-tea-red): `5 failed, 2 passed`, **no collection/import/fixture errors**. Failures are exactly "expected one `narrator.empty_prose_upstream` span; got 0" and "exactly one `narrator_empty_prose_upstream` event … got 0". The existing symptom guard (`narrator.empty_narration`, orchestrator.py:3353) fires in every RED log, confirming the only gap is the upstream cause signal.

### The contract Dev implements (RED pins these exact names)

Upstream of, and distinct from, `_guard_empty_narration` — SDK-path-only, the natural home is `_assemble_turn_result_sdk` (it already reads `result.text` and receives `result.tool_calls`; runs before the guard in `run_narration_turn`):

- **OTEL span** `narrator.empty_prose_upstream` — attrs: `cause` (`tool_only_response` when `tool_calls>0`, else `no_output`), `tool_call_count`, `raw_len` (len of unstripped `result.text`), `turn_number`.
- **Watcher event** `narrator_empty_prose_upstream` — `component="orchestrator"`, `severity="warn"`, fields carry `cause` + `tool_call_count` (GM-panel lie detector, CLAUDE.md OTEL principle).
- Keys on the **stripped** text (matches the guard's `.strip()` semantics) so whitespace-only prose trips it too.
- The downstream `_guard_empty_narration` is **UNCHANGED** — both spans must coexist on an empty turn; the guard remains the recovery path.

### Test map

| AC | Test | Asserts |
|----|------|---------|
| AC2 | `test_tool_only_continuation_emits_upstream_span` | tool_calls=1 + empty → span `cause=tool_only_response`, tool_call_count=1, raw_len=0, turn_number=2 |
| AC2 | `test_empty_with_no_tools_emits_upstream_span_no_output` | no tools + empty → span `cause=no_output`, tool_call_count=0 |
| AC3 | `test_whitespace_only_continuation_trips_upstream_detection` | whitespace strips to empty → still trips (stripped-empty semantics) |
| AC4 | `test_tool_only_continuation_emits_watcher_event_to_gm_panel` | **wiring**: event reaches a live `watcher_hub` subscriber, severity warn, component orchestrator, fields carry cause |
| AC1 | `test_upstream_detection_coexists_with_degraded_stall_guard` | BOTH `narrator.empty_prose_upstream` AND `narrator.empty_narration` fire; result `is_degraded=True`; "world holds its breath" stall intact |
| — | `test_healthy_sdk_turn_emits_no_upstream_signal` | negative: real prose → no span, no event, not degraded |
| scope | `test_synchronous_empty_turn_does_not_emit_upstream_span` | sync (non-tooling) path does NOT emit the SDK-scoped upstream span; existing guard still recovers it |

### Rule Coverage

| Rule (lang-review/python.md) | Test(s) | Status |
|------|---------|--------|
| #4 Logging coverage+correctness (recoverable → `warn`, not `error`) | `test_tool_only_continuation_emits_watcher_event_to_gm_panel` (asserts `severity=="warn"`) | failing (event absent) |
| #6 Test quality (no vacuous assertions) | self-check (below) | pass |
| Wiring (CLAUDE.md "Every Test Suite Needs a Wiring Test") | `test_tool_only_continuation_emits_watcher_event_to_gm_panel` drives real `run_narration_turn` → live `watcher_hub` subscriber | failing (event absent) |

**Rules checked:** 3 of 8 lang-review rules are applicable to test design here (the rest — silent-except, mutable-default, path-handling, deserialization, resource-leak — govern the *implementation* the Dev writes; flagged for Dev's self-review, not testable pre-implementation).
**Self-check:** 0 vacuous tests. Every test asserts a concrete value (span attribute, event field, exact narration string, or a checked-empty absence with a message) — none use `assert True`, `let _ =`, or bare truthiness.

**Handoff:** To Dev (Inigo Montoya) for the GREEN implementation — add the upstream cause span + watcher event in `_assemble_turn_result_sdk`, leave `_guard_empty_narration` untouched. Read the **Question** finding first (detection-only vs reprompt-recovery fork) — the AC-satisfying read is detection-only.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/sidequest/agents/orchestrator.py` — new `_emit_empty_prose_upstream_signal` method + one call from `_assemble_turn_result_sdk` (after `raw_response = result.text`, before extraction). +74 lines, additive only. `_guard_empty_narration` untouched.

**How it works:** When the SDK assembler sees `result.text` strip to empty, it emits the `narrator.empty_prose_upstream` OTEL span and the `narrator_empty_prose_upstream` watcher event (component=orchestrator, severity=warn), tagging `cause=tool_only_response` when `result.tool_calls` is non-empty, else `cause=no_output`, plus `tool_call_count`/`raw_len`/`turn_number`. It does NOT mutate the result or recover the turn — the degraded-stall guard still runs downstream in `run_narration_turn` and remains the recovery path. SDK-path-only (the synchronous assembler is untouched), so the sync empty turn keeps firing only the existing guard.

**Tests:** 8/8 new tests passing (GREEN) — verified by testing-runner (run_id 153-11-dev-green). No regression: `test_empty_narration_guard.py` (4/4) and `test_narrator_sdk_hybrid_split.py` (15/15) still fully pass — `23 passed` across the blast radius. `ruff check` + `ruff format --check` clean on the changed file.

**Branch:** `feat/153-11-narrator-empty-prose-upstream` (pushed to origin)

**Self-review:**
- [x] Wired: called from the production `_assemble_turn_result_sdk` on the default ADR-101 SDK narrator path; wiring test drives the live `watcher_hub` subscriber.
- [x] Follows project patterns: mirrors `_guard_empty_narration`'s `Span.open(...)` + the orchestrator's existing `publish_event(..., component="orchestrator", severity="warn")` usage; local imports per the file's convention.
- [x] All ACs met: AC1 (guard unchanged, both spans coexist), AC2 (upstream span + cause), AC3 (regression test / whitespace), AC4 (GM-panel watcher event).
- [x] Error handling: N/A — purely observational; no new failure paths (does not raise, does not mutate state).

**Handoff:** To Reviewer (Westley) for code review.
## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 (format) | confirmed 1 (LOW format), dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — covered by my manual edge analysis |
| 3 | reviewer-silent-failure-hunter | Yes | clean | none | N/A |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — covered by my manual test review |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — comments reviewed manually |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — type review done manually |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — simplicity reviewed manually |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — lang-review rules checked manually |

**All received:** Yes (3 enabled returned: preflight, silent-failure-hunter, security; 6 disabled via `workflow.reviewer_subagents` and pre-filled)
**Total findings:** 1 confirmed (LOW — test-file format reflow), 0 dismissed, 0 deferred

## Rule Compliance

Rules checked against `.pennyfarthing/gates/lang-review/python.md`, CLAUDE.md (server), and SOUL.md, enumerated over the one new method + its call site:

- **#1 Silent exception swallowing** — COMPLIANT. `_emit_empty_prose_upstream_signal` has no try/except, no `pass`, no `suppress()`. (Confirmed by [SILENT].)
- **#2 Mutable default arguments** — COMPLIANT. No default args; `fields` is a fresh local dict per call.
- **#3 Type annotations at boundaries** — COMPLIANT. The method is keyword-only `(*, result: ToolingResult, context: TurnContext) -> None` — both params and the return are annotated.
- **#4 Logging coverage + correctness** — COMPLIANT. Uses `logger.warning(...)` (recoverable condition → warn, not error), %-style lazy args (no f-string), no sensitive data (emits `raw_len`, not the text). `severity="warn"` matches this file's convention (orchestrator.py:4276, 4302). (Confirmed by [SEC].)
- **#5 Path handling** — N/A (no filesystem/path code).
- **#6 Test quality** — COMPLIANT. 8 tests, every assertion checks a concrete value (span attrs, event fields, exact narration strings, or checked-empty lists with messages); no `assert True`, no `let _ =`, no truthy-only checks. Negative + scope tests present.
- **#7 Resource leaks** — COMPLIANT. `with Span.open(...)` is a context manager; no unmanaged `open()`/connections/locks.
- **#8 Unsafe deserialization** — N/A (no pickle/yaml.load/eval/exec).
- **CLAUDE.md No Silent Fallbacks** — COMPLIANT and directly served: the change converts a previously-silent empty-text path into a loud span+event+warning.
- **CLAUDE.md OTEL Observability Principle** — COMPLIANT: every empty-prose decision now emits a GM-panel-visible span and watcher event.
- **CLAUDE.md No Source-Text Wiring Tests** — COMPLIANT: the wiring test (`test_tool_only_continuation_emits_watcher_event_to_gm_panel`) drives the real `run_narration_turn` and asserts on a live `watcher_hub` subscriber + OTEL span exporter, not on source text.

## Reviewer Assessment

**Verdict:** APPROVED

**Summary:** A tight, additive 74-line change (one new method `_emit_empty_prose_upstream_signal` + one call site in `_assemble_turn_result_sdk`). It does exactly what the story asks — makes the previously-silent empty-prose-on-continuation path LOUD and categorized (`tool_only_response` / `no_output`), UPSTREAM of and without touching the degraded-stall guard. All three enabled specialists plus my own adversarial pass found no correctness, silent-failure, or security issues. One LOW format-reflow note (non-blocking, CI-ungated).

**Observations (≥5):**
- [VERIFIED] Upstream-vs-guard ordering is correct — `_emit_empty_prose_upstream_signal` is called inside `_assemble_turn_result_sdk` (orchestrator.py:3852), which returns to `run_narration_turn`, which THEN calls `_guard_empty_narration` (orchestrator.py:3297). The cause span fires before the symptom span; both coexist. Evidence: `test_upstream_detection_coexists_with_degraded_stall_guard` asserts both span names present + `is_degraded=True` + intact stall.
- [VERIFIED] Guard not suppressed/replaced — the new method has no `return result`/mutation; it returns `None` and does not early-return the assembler. `result` (ToolingResult) is untouched. Evidence: orchestrator.py:3955-3994; blast-radius `test_empty_narration_guard.py` (4/4) + `test_narrator_sdk_hybrid_split.py` (15/15) still green.
- [VERIFIED] Shared `fields` dict is safe — `Span.open` sets it verbatim via `start_as_current_span(attributes=...)` with no mutation (span.py:34); `publish_event` copies into a new event dict. All four values are `str`/`int` (never None: `turn_number: int = 0` at orchestrator.py:639). No OTEL attribute drop, no aliasing hazard. (Corroborated by [SILENT].)
- [VERIFIED] Cause taxonomy correct — `cause = "tool_only_response" if tool_call_count else "no_output"` (orchestrator.py:3961). The tool-only branch is the documented playtest repro; the no_output branch is the zero-tool empty. Evidence: both branches have dedicated passing tests.
- [VERIFIED] Scope boundary on "prose in the wrong field" is intentional and consistent — the signal keys on `result.text.strip()`, so a non-empty `result.text` that *extracts* to empty narration (wrong-field case) does NOT fire the upstream span and stays guard-only. This exactly matches the TEA/Dev documented deviation; it is a deliberate 2-pt scope cut, not a miss.
- [SILENT] reviewer-silent-failure-hunter: CLEAN — no swallowed errors; `publish_event` fire-and-forget is the established project pattern (ADR-090, ~6 sibling call sites in this file), not a new silent path.
- [SEC] reviewer-security: CLEAN — no info leakage (emits `raw_len`, never the prose/action text), no log-injection (%-style static format), `severity="warn"` correct for a recoverable turn, no DoS (fires ≤1×/turn, early-returns on real prose).
- [TEST] (subagent disabled — manual review): 8 tests, meaningful assertions throughout, includes the mandated wiring test (live watcher subscriber) and a negative + a sync-scope test. No vacuous assertions. GREEN 8/8.
- [EDGE] (subagent disabled — manual analysis): boundary cases covered — empty text, whitespace-only-strips-to-empty, zero-tool empty, real-prose early-return, sync-path scope. No unhandled branch in the 6-line logic body.
- [TYPE] (subagent disabled — manual): keyword-only typed signature; `cause` is a bounded string literal pair (acceptable for an OTEL attribute — OTEL attrs are stringly by nature; not a domain newtype candidate).
- [DOC] (subagent disabled — manual): the new method's docstring is accurate and matches behavior; the inline call-site comment correctly describes intent. No stale/misleading comments.
- [SIMPLE] (subagent disabled — manual): minimal — 6 lines of logic, early-return guard, one dict, two emits. No over-engineering. Mirrors the sibling `_guard_empty_narration` shape.
- [RULE] (subagent disabled — manual rule-by-rule above): all applicable lang-review rules COMPLIANT; see ## Rule Compliance.
- [LOW] [preflight] `ruff format --check` would reformat `tests/agents/test_153_11_empty_prose_upstream.py` — a single one-element-list line-wrap at test line ~358. CI does not gate `ruff format` (server-check/check-all run `ruff check`, not `--check`), so non-blocking. Recommend `ruff format tests/agents/test_153_11_empty_prose_upstream.py` be swept before/at PR creation.

**Data flow traced:** SDK narrator returns `ToolingResult` → `_assemble_turn_result_sdk(result)` reads `result.text`/`result.tool_calls` → `_emit_empty_prose_upstream_signal` (if stripped-empty: emit span + watcher event with cause, no mutation) → assembly continues → `run_narration_turn` → `_guard_empty_narration` recovers the player surface. Safe: the upstream emit is observational only; the recovery path is unchanged.

**Pattern observed:** Sibling-of-`_guard_empty_narration` cause/symptom split — cause categorized at the SDK seam (where tool context exists), symptom recovered downstream (where every consumer reads one field). Good separation. orchestrator.py:3925-3994.

**Error handling:** N/A by design — purely observational, raises nothing, mutates nothing. The one defensive normalization (`result.text or ""`) is harmless and matches the guard's `(result.narration or "")`.

### Devil's Advocate

Suppose I want this broken. First attack: race/duplicate emission. Could the span fire twice for one turn? `_assemble_turn_result_sdk` is invoked exactly once per `_run_narration_turn_sdk`, and the method has no loop — so no. Could it fire on a turn that already recovered elsewhere? The oversized-prompt refuse returns a degraded result BEFORE `complete_with_tools`, so the assembler (and this signal) is never reached on that path — good, no double-degrade. Second attack: a confused GM-panel operator. They see `narrator.empty_prose_upstream` AND `narrator.empty_narration` on the same turn and think it's two separate failures. But that is the intended cause+symptom pairing, documented in both docstrings; the panel's value is precisely seeing the cause next to the symptom. Acceptable. Third attack: the wrong-field case. A narrator that dumps prose inside a tool argument and returns a non-empty `result.text` (e.g. a lone ```game_patch``` fence) will NOT trip the upstream signal — `raw.strip()` is truthy — yet may still extract to empty narration and trip the downstream guard, leaving a symptom with no upstream cause. Is that a hole? No — it is the explicitly deferred "prose in the wrong field" cause (TEA Gap finding + Design Deviation), out of scope for this 2-pt story, and the player surface is still recovered by the guard. Fourth attack: severity-string drift. If the GM panel filters on `"warning"` and we emit `"warn"`, the event could be invisible. But the live-subscriber wiring test confirms the event arrives with `severity="warn"`, and sibling shipped events in this file (4276, 4302) and the panel-bound `narrator_context_missing_ids` use `"warn"` — so the panel recognizes it. Fifth attack: a stressed filesystem / no watcher subscribers — `publish_event` drops silently. But that is the documented lossy-by-design watcher contract (ADR-090), identical to every other event on this turn, and the OTEL span still records the cause for trace exporters. Nothing here corrupts state or hangs the client. The change is observational and additive; the worst realistic failure is a dropped watcher event under a startup race, which is acceptable and pre-existing. No new finding surfaced.

**Handoff:** To SM (Vizzini) for finish-story.