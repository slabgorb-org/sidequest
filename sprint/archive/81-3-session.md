---
story_id: "81-3"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 81-3: Feed PacingHint into TurnContext so the [PACING] injection fires

## Story Details
- **ID:** 81-3
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** 81-2 (feat/81-2-tension-tracker-producer) — must pull latest develop post-merge

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-03T18:28:26Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-03T00:00:00Z | 2026-06-03T18:00:11Z | 18h |
| red | 2026-06-03T18:00:11Z | 2026-06-03T18:11:47Z | 11m 36s |
| green | 2026-06-03T18:11:47Z | 2026-06-03T18:17:49Z | 6m 2s |
| spec-check | 2026-06-03T18:17:49Z | 2026-06-03T18:19:31Z | 1m 42s |
| verify | 2026-06-03T18:19:31Z | 2026-06-03T18:21:54Z | 2m 23s |
| review | 2026-06-03T18:21:54Z | 2026-06-03T18:27:26Z | 5m 32s |
| spec-reconcile | 2026-06-03T18:27:26Z | 2026-06-03T18:28:26Z | 1m |
| finish | 2026-06-03T18:28:26Z | - | - |

## Story Context

**ADR-025 Runtime Bug Fix (Consumer/Bridge Side)**

**ROOT CAUSE:** TurnContext.pacing_hint (declared sidequest/agents/orchestrator.py:728 as 'PacingHint | None = None') is never set. The sole TurnContext construction site (sidequest/server/session_helpers.py:1158) omits it, so it is None every turn. The orchestrator's [PACING] injection (orchestrator.py:2648-2653, 'if context.pacing_hint is not None: register_pacing_section(...)') therefore never fires, and the narrator never receives a pacing hint.

**TECHNICAL APPROACH:**
1. At TurnContext construction in session_helpers.py:1158, derive the hint from the session TensionTracker (81-2) via `tracker.pacing_hint(thresholds)` using the genre's DramaThresholds.
2. Pass the derived pacing_hint into TurnContext so the orchestrator's [PACING] injection (orchestrator.py:2648-2653) fires.
3. Add a watcher/OTEL event to record the computed pacing hint per turn (GM-panel observable).
4. Add a prompt-assembly test asserting the [PACING] section appears in the narrator prompt when pacing_hint is set.
5. Add an end-to-end integration test: TensionTracker → TurnContext.pacing_hint → [PACING] in narrator prompt.

**OUT OF SCOPE (Deferred):**
- Quiet-turn pre/post game-state diff (ADR-025 future enhancement)
- Accelerator/decelerator keyword scan stubbed at sidequest/game/trope_tick.py:226-230

**Acceptance Criteria:**
- TurnContext construction derives pacing_hint from session TensionTracker + genre's DramaThresholds; pacing_hint is non-None on turns where accumulated tension warrants a hint.
- The orchestrator [PACING] injection actually fires (orchestrator.py:2648-2653 register_pacing_section): a prompt-assembly test asserts the assembled narrator prompt contains the pacing-hint section when pacing_hint is set.
- A watcher/OTEL event records the computed pacing hint per turn, GM-panel observable.
- End-to-end wiring test: TensionTracker → TurnContext.pacing_hint → [PACING] section in narrator prompt; test fails on current code (hint always None). Full suite green (just server-test).

## Sm Assessment

**Routing:** tdd (phased) → TEA for red phase.

**Why this story now:** Only p1 left in the backlog after 81-2 (the producer) merged to sidequest-server develop on 2026-06-03. 81-3 is the consumer/bridge half of the same ADR-024/025 wiring pair; with 81-2 live, its dependency (an accumulating per-session TensionTracker on `_SessionData`, fed via `websocket_session_handler.py`) is now satisfied. Completing 81-3 closes the dual-track pacing signal end-to-end — the exact "built, unit-tested, never wired" anti-pattern the project's wiring doctrine exists to catch.

**Scope is tight and well-bounded.** Single repo (sidequest-server). The fix is a bridge at one construction site (`session_helpers.py:1158`) deriving `tracker.pacing_hint(thresholds)` from the genre's `DramaThresholds` and passing it into `TurnContext`. Deferred work (quiet-turn diff, accelerator/decelerator keyword scan at `trope_tick.py:226-230`) is explicitly out of scope per the story.

**TEA focus for red:** The load-bearing failing test is the end-to-end wiring assertion — TensionTracker → `TurnContext.pacing_hint` → `[PACING]` section present in the assembled narrator prompt — which must fail on current code (hint always None). Pair it with the prompt-assembly assertion and the per-turn OTEL/watcher emit (GM panel is the lie detector per project doctrine).

**Branch:** `feat/81-3-pacing-hint-turncontext` off latest origin/develop (81-2 already merged). No Jira key for this project — claim skipped.

## TEA Assessment

**Tests Required:** Yes
**Reason:** ADR-025 runtime-bug fix with a behavioral, observable contract.

**Test Files:**
- `sidequest-server/tests/server/test_pacing_hint_turn_context_wiring.py` — the consumer/bridge wiring for the per-session pacing hint (6 tests).

**Tests Written:** 6 tests covering ACs 1, 3, 4 (AC2 pre-covered — see below).
**Status:** RED — 5 failing (ready for Dev), 1 intended green regression-guard.

**What's RED on develop (the new, untested surface):**
| Test | AC | Fails because (develop) |
|------|----|--------------------------|
| `test_build_turn_context_derives_pacing_hint_from_session_tracker` | 1 | `_build_turn_context` omits `pacing_hint` → None |
| `test_pacing_hint_uses_genre_drama_thresholds_not_hardcoded` | 1 | hint None; also pins thresholds come from the pack (mutant_wasteland 0.67→Streaming vs defaults→Sentence) |
| `test_pacing_hint_falls_back_to_defaults_when_pack_has_no_thresholds` | 1 | hint None; pins None-thresholds → `DramaThresholds()` (caverns has no pacing.yaml) |
| `test_build_turn_context_emits_pacing_hint_span` | 3 | no `pacing.*` OTEL span fires (other `<domain>.<event>` spans confirm the channel works) |
| `test_end_to_end_tracker_drives_pacing_section_in_prompt` | 4 | hint None → guard skips `register_pacing_section` → `## Pacing Guidance` absent from rendered prompt |

**Intended green (regression guard, not a RED driver):**
- `test_neutral_tracker_is_handled_without_error` — fresh tracker builds without raising; if a hint is set it must match the tracker's own computation (can't be fabricated). Green on develop because None is already handled; guards a future crash on the neutral path.

**RED verified directly** (`uv run pytest <file> -n0`): 5 failed / 1 passed, each failure at its intended assertion — not collection/fixture errors. Verified directly rather than via `testing-runner` to protect this session file (known clobber of `.session/{story}-session.md`).

### Rule Coverage

| Rule (lang-review/python.md) | Test(s) / Action | Status |
|------|---------|--------|
| #6 Test quality | All 6 tests assert concrete values (equality on `PacingHint`, `delivery_mode`, `target_sentences`, `drama_weight` attr, prompt substring); no `assert True`, no truthy-only, no skips; mocks target `_SessionData` deps not patch-where-defined | self-check pass |
| #1 Silent exception swallowing | Bridge derive path must not silently swallow (81-2's driver wraps in try/except + `logger.exception`); `test_neutral_tracker_is_handled_without_error` asserts no-crash on the happy/neutral path | Dev watch-item |
| #3 Type annotations at new seam | Dev adds a `pacing.*` span emit + threshold resolution; annotate the new helper/attrs | Dev watch-item |

**Rules checked:** #6 directly enforced by the test suite; #1/#3 flagged for Dev (the bridge is an internal helper, so most boundary rules are N/A).
**Self-check:** 0 vacuous tests (every test asserts a concrete value or a no-raise behavioral contract).

**Handoff:** To Dev (Agent Smith) for GREEN.

**GREEN guidance for Dev:**
1. At `session_helpers.py` `_build_turn_context` (the `return TurnContext(...)` at ~1158), derive `hint = sd.tension_tracker.pacing_hint(sd.genre_pack.drama_thresholds or DramaThresholds())` and pass `pacing_hint=hint`.
2. Emit a `pacing.hint_computed` OTEL span (suggest `SPAN_PACING_HINT` in `telemetry/spans/`, mirroring `SPAN_NPC_WORKING_SET`) with `drama_weight` / `target_sentences` / `delivery_mode` attributes. The AC3 test matches any `pacing`-prefixed span carrying a numeric `drama_weight`, so the exact suffix is your call.
3. Do NOT touch `register_pacing_section` or the `[PACING]` format (works once a hint arrives). Do NOT re-open quiet-turn diff / trope_tick keyword scan (deferred).
4. Whether the neutral hint is set or suppressed-to-None is your design call — both pass; if set, it must equal the tracker's computation.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/server/session_helpers.py` — `_build_turn_context` derives `pacing_hint` from `sd.tension_tracker.pacing_hint(sd.genre_pack.drama_thresholds or DramaThresholds())`, emits the pacing span, and passes `pacing_hint=` into `TurnContext`. (+`DramaThresholds`/`pacing_hint_span` imports)
- `sidequest/telemetry/spans/pacing.py` (new) — `SPAN_PACING_HINT` + `SpanRoute` (GM-panel, `tension` component) + `pacing_hint_span` helper.
- `sidequest/telemetry/spans/__init__.py` — re-export `from .pacing import *`.

**Tests:** Full server suite **9887 passed / 365 skipped / 0 failed** (`uv run pytest`, run directly to protect this session file per the known `testing-runner` clobber). The 6 story tests: 6/6 GREEN (the 5 prior RED + the neutral guard). Adjacent suites confirmed green: `test_orchestrator_pacing_wiring.py`, `test_routing_completeness.py`. Lint/format/pyright clean on changed files.

**AC status:**
- AC1 (derive + genre thresholds + None-fallback + neutral) — GREEN
- AC2 (guard/injection) — pre-covered + strengthened end-to-end by AC4
- AC3 (GM-panel-observable OTEL span) — GREEN, routed to the panel
- AC4 (tracker → bridge → `## Pacing Guidance` in rendered prompt) — GREEN

**Wiring confirmed:** the bridge lives in the real production `_build_turn_context` (the sole `TurnContext` construction site, called per turn from the handler) — not a test-only path. No-half-wired: producer (81-2) → consumer (81-3) → orchestrator injection is now end-to-end.

**Branch:** `feat/81-3-pacing-hint-turncontext` (pushed to origin).

**Handoff:** To Reviewer (The Merovingian).

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None requiring resolution

Verified the diff (`git diff develop`: +22 session_helpers, +65 spans/pacing.py, +1 __init__, +322 test) against all four ACs in context-story-81-3.md:

- **AC1 (derive + set):** `_build_turn_context` derives `sd.tension_tracker.pacing_hint(sd.genre_pack.drama_thresholds or DramaThresholds())` and stamps it on `TurnContext`. Thresholds sourced from the **pack** (honors "Crunch in the Genre, Flavor in the World" — pacing breakpoints are genre-tier mechanics). Aligned.
- **AC2 (injection fires):** `register_pacing_section`/`[PACING]` format untouched per the story's explicit boundary; pre-covered by `test_orchestrator_pacing_wiring.py` and strengthened end-to-end by AC4. Aligned.
- **AC3 (observable):** `SPAN_PACING_HINT` ("pacing.hint_computed") emitted from the bridge and **routed** (`SpanRoute`, `tension` component) — so it reaches the GM-panel typed feed, not just raw OTEL. Spec's "watcher/OTEL event" is satisfied; routing-completeness lint green. Aligned.
- **AC4 (e2e wiring):** tracker → real `_build_turn_context` → `## Pacing Guidance` in the rendered prompt; was RED on develop, now GREEN; full suite 9887/0. Aligned.

**On the three logged deviations** (always-set-vs-None, default-thresholds fallback, span-vs-watcher): each falls **within** the spec's permissive language ("may legitimately be None", "DramaThresholds are resolvable… small in-scope addition", "watcher/OTEL event"). They are transparency notes, not drift — no resolution required (Option A, already documented).

**Architectural notes (non-blocking, no mismatch):**
- The pacing span fires every turn unconditionally (incl. drama_weight 0.0), consistent with the `npc.working_set` "fires-every-turn" precedent and the OTEL "every subsystem decision emits" doctrine. Sound. The Dev finding already flags the quiet-turn token cost as a future micro-opt.
- This completes the ADR-024/025 producer→consumer→injection chain (81-2 → 81-3 → orchestrator), moving those ADRs from the epic-81 "built-not-wired" set toward live. A future docs pass could update their DRIFT/partial status — out of scope here.

**Decision:** Proceed to review (next phase: TEA verify).

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 4 (session_helpers.py bridge block, spans/pacing.py, spans/__init__.py, test file)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | clean | No duplication — `pacing.py` mirrors the `npc.working_set` span pattern exactly; bridge matches sibling OTEL emits in `_build_turn_context`; `__init__` re-export is the mandated integration; SpanRoute boilerplate is unavoidable per-domain. |
| simplify-quality | clean | Correct naming, no dead code/unused imports, comprehensive behavioral tests with no vacuous assertions; `with pacing_hint_span(...): pass` confirmed intentional (point-span convention). |
| simplify-efficiency | clean | No over-engineering; empty-body span `with` is idiomatic OTEL; per-turn emit is by-design per the OTEL doctrine; test fixtures reused correctly, not bloat. |

**Applied:** 0 high-confidence fixes
**Flagged for Review:** 0 medium-confidence findings
**Noted:** 0 low-confidence observations
**Reverted:** 0

**Overall:** simplify: clean

**Quality Checks:** All passing — tree clean (no simplify commits), ruff clean on all 4 changed files, story suite 6/6 green (re-confirmed); full server suite was 9887/0 at green. No regression detection needed (no fixes applied).

**Handoff:** To Reviewer (The Merovingian) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (9887 passed/0 failed, 0 smells, pyright clean) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — covered by Reviewer |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — covered by Reviewer |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — covered by Reviewer + verify-phase simplify-quality |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — covered by Reviewer |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — covered by Reviewer |
| 7 | reviewer-security | Yes | clean | none (5 rules checked, 0 violations) | N/A |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — verify phase ran reuse/quality/efficiency, all clean |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — covered by Reviewer Rule Compliance below |

**All received:** Yes (2 enabled subagents returned clean; 7 disabled via `workflow.reviewer_subagents`, domains covered by Reviewer)
**Total findings:** 0 confirmed, 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

I traced every cause to every effect. The change is 22 lines of bridge + a 65-line span module mirroring an established pattern; both enabled subagents returned clean and my own pass across the disabled subagents' domains found nothing blocking.

**Observations (≥5):**
- `[SEC]` Security subagent clean — confirmed `pacing_thresholds = sd.genre_pack.drama_thresholds or DramaThresholds()` is the DramaThresholds model's documented optional-with-defaults (`extra="ignore"`, "Missing fields fall back to defaults"), NOT a silent fallback masking misconfig; span emits only `drama_weight`/`target_sentences`/`delivery_mode`/`escalation_present` — `escalation_beat` content string deliberately reduced to a bool, so no PII/secret leakage. `pacing.py:25-36`.
- `[VERIFIED]` Cannot raise on the happy or neutral path — `TensionTracker.pacing_hint()` (tension_tracker.py:359) is total (pure math, always returns a `PacingHint`); `sd.tension_tracker` is a `_SessionData` default_factory field (always present, 81-2); `sd.genre_pack` is non-optional (`session_state.py:196`) and already dereferenced extensively above the new code. Evidence: full suite 9887/0 + `test_neutral_tracker_is_handled_without_error` green.
- `[SILENT]` No swallowed errors / silent fallbacks introduced — no `try/except`, no bare `except`, no `suppress()`. The `or DramaThresholds()` is a documented default, not an error-masking branch. (lang-review #1 — compliant.)
- `[TYPE]` `str(pacing_hint.delivery_mode)` is correct — `DeliveryMode` is a `StrEnum` (tension_tracker.py:106), so `str()` yields the value (`"Streaming"`), not `"DeliveryMode.Streaming"`. Span attributes are primitive (float/int/str/bool) — OTEL-safe; `escalation_present` is a bool precisely because OTEL rejects `None`. `pacing.py:48-64`.
- `[TEST]` Test quality strong (test-analyzer disabled; verified directly): concrete-value assertions throughout (PacingHint equality, `delivery_mode`, `target_sentences`, span `drama_weight` attr, prompt substrings); the genre-thresholds test carries a discriminator-sanity assertion (defaults→Sentence vs pack→Streaming) that prevents a false pass; no vacuous `assert True`/truthy-only/skips. Neutral test is a conditional guard (green on develop, by design).
- `[DOC]` Comments accurate — the bridge comment and `pacing.py` docstring correctly describe behavior, the producer→consumer relationship (81-2/81-3), and the OTEL intent; no stale references introduced.
- `[SIMPLE]` Verify-phase simplify (reuse/quality/efficiency) all clean; the `with pacing_hint_span(...): pass` point-span emission mirrors `npc_working_set_span` and sibling spans in the same function — idiomatic, not over-engineered.
- `[EDGE]` Boundary cases covered — high drama (0.9→Streaming/5 sentences), boundary drama (0.67 straddling pack-vs-default delivery), absent pacing.yaml (None→defaults), and neutral (0.0) all have tests; `target_sentences` is bounded 1–6 by the producer (unit-tested upstream). The only unbounded-by-this-PR input (pack-authored thresholds) is operator content, pydantic-validated.
- `[RULE]` See Rule Compliance below — all 13 applicable lang-review checks pass.

**Data flow traced:** `sd.tension_tracker` (per-session, fed each turn by 81-2's `_drive_session_tension_tracker`) → `pacing_hint(thresholds)` → `TurnContext.pacing_hint` (`session_helpers.py:1169-1170`) → orchestrator guard `if context.pacing_hint is not None` → `register_pacing_section` → `## Pacing Guidance` in the rendered prompt (proven by AC4 e2e). Parallel branch: same hint → `pacing.hint_computed` span → `SpanRoute` → GM-panel `state_transition`/`tension` feed. Safe: no user input on either path; all values internally computed.

**Pattern observed:** New-span-domain pattern (`SPAN_X` + `SPAN_ROUTES[...]` + `*_span` contextmanager + `from .X import *`) followed exactly per `npc.py`; routing-completeness lint green at `pacing.py:25`.

**Error handling:** No failure modes introduced — pure computation + span emission; the contextmanager guarantees span close. Null/None inputs structurally impossible (see `[VERIFIED]`).

### Rule Compliance (lang-review/python.md, exhaustive)

| # | Rule | Instances in diff | Verdict |
|---|------|-------------------|---------|
| 1 | Silent exception swallowing | 0 try/except added; `or DramaThresholds()` documented default | Compliant |
| 2 | Mutable default arguments | `pacing_hint_span` has no mutable defaults; `attributes` dict built fresh per call | Compliant |
| 3 | Type annotations at boundaries | `pacing_hint_span` fully annotated (kw-only params, `Iterator[trace.Span]` return) | Compliant |
| 4 | Logging coverage/correctness | No logging needed — the span IS the observability (OTEL principle) | Compliant (N/A) |
| 5 | Path handling | No path ops | N/A |
| 6 | Test quality | Concrete assertions, no vacuous/skip, discriminator sanity | Compliant |
| 7 | Resource leaks | `with` contextmanager closes the span deterministically | Compliant |
| 8 | Unsafe deserialization | Only pydantic-validated YAML at startup (operator content) | Compliant (N/A) |
| 9 | Async pitfalls | bridge sync; AC4 test awaits `build_narrator_prompt` correctly | Compliant |
| 10 | Import hygiene | `from .pacing import *` is the mandated spans-package convention (every domain module); session_helpers imports explicit | Compliant |
| 11 | Input validation at boundaries | No external input reaches the new code | Compliant (N/A) |
| 12 | Dependency hygiene | No dependency changes | N/A |
| 13 | Fix-introduced regressions | Full suite 9887/0 — no regression | Compliant |

### Devil's Advocate

Argue the code is broken. **Attack 1 — the `or` fallback hides a real config error.** If a pack author *intends* tuned pacing but ships a malformed `pacing.yaml`, `_load_yaml_optional` could return None and the bridge would silently use defaults, masking the typo. Rebuttal: `_load_yaml_optional` validates via pydantic and would raise on a malformed file (not return None); None only occurs on an *absent* file, which is the documented "no pacing authored" state. caverns_and_claudes proves absence is normal. Not a defect — but I logged a non-blocking content finding so absence is visible. **Attack 2 — the span fires every turn, flooding the GM panel and inflating cost.** On a 140-turn session that's 140 pacing spans, each adding a `## Pacing Guidance` section (even "Drama level: 0%") to the prompt. Rebuttal: this is the OTEL doctrine ("every subsystem decision emits") and matches `npc.working_set` which also fires every turn; the token cost is a handful of characters and is already flagged as a non-blocking future micro-opt. Behavior is correct, not broken. **Attack 3 — `str(delivery_mode)` could serialize as `"DeliveryMode.Streaming"` and poison the GM-panel field.** Rebuttal: verified `DeliveryMode` is `StrEnum`, whose `__str__` returns the bare value; the AC3 test reads the attribute back and the routing extract passes it through — a malformed string would not break anything anyway (it's display-only telemetry). **Attack 4 — a confused player/dev sees pacing guidance contradicting the scene.** Rebuttal: the hint is derived from real tension state (HP stakes + gambler's ramp) fed by 81-2; the span is the lie detector that makes exactly this auditable — the feature *adds* legibility, doesn't remove it. **Attack 5 — race/concurrency.** The tracker is per-session and turn processing is serialized; no shared mutable state added; 9887 tests pass. No race. Nothing in the devil's advocate pass rises to a blocking defect.

**Handoff:** To SM for finish-story.

## Delivery Findings

No upstream findings — 81-2 (TensionTracker producer) is merged to develop and ready for integration.

### Dev (implementation)
- **Improvement** (non-blocking): the pacing section now renders on every turn, including dead-quiet turns (drama_weight 0.0 → "Target ~1 sentence(s). Drama level: 0%."). Harmless but adds a few prompt tokens per quiet turn; if prompt-byte pressure ever matters, suppress hints below a drama floor (or skip the section at drama_weight 0.0). Affects `sidequest-server/sidequest/server/session_helpers.py` (`_build_turn_context`) / `sidequest/agents/prompt_framework/core.py` (`register_pacing_section`). *Found by Dev during implementation.*

### TEA (test design)
- **Improvement** (non-blocking): the existing `tests/agents/test_orchestrator_pacing_wiring.py` docstring/refs still cite the historical story `42-3` for the now-live ADR-024/025 pacing wiring; a future doc pass could re-anchor it to 81-2/81-3. Affects `sidequest-server/tests/agents/test_orchestrator_pacing_wiring.py` (comment-only). *Found by TEA during test design.*
- **Gap** (non-blocking): `caverns_and_claudes` (the default test/dev pack) ships no `pacing.yaml`, so `drama_thresholds` is None — the pacing feature only produces meaningful (non-trivial) hints there via HP-driven stakes. If the playgroup's default world wants tuned pacing, authoring a `caverns_and_claudes/pacing.yaml` is content-side follow-up. Affects `sidequest-content/genre_packs/caverns_and_claudes/` (no engine change). *Found by TEA during test design.*

### Reviewer (code review)
- **Improvement** (non-blocking): ADR-024 (dual-track tension) and ADR-025 (pacing detection) are now wired end-to-end (producer 81-2 → consumer 81-3 → orchestrator injection); a docs pass could lift their DRIFT/partial status in `docs/adr/DRIFT.md` and the server CLAUDE.md ADR table. Affects `orc-quest/docs/adr/DRIFT.md` (status-only, no code). *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 3 findings (1 Gap, 0 Conflict, 0 Question, 2 Improvement)
**Blocking:** None

- **Improvement:** the existing `tests/agents/test_orchestrator_pacing_wiring.py` docstring/refs still cite the historical story `42-3` for the now-live ADR-024/025 pacing wiring; a future doc pass could re-anchor it to 81-2/81-3. Affects `sidequest-server/tests/agents/test_orchestrator_pacing_wiring.py`.
- **Gap:** `caverns_and_claudes` (the default test/dev pack) ships no `pacing.yaml`, so `drama_thresholds` is None — the pacing feature only produces meaningful (non-trivial) hints there via HP-driven stakes. If the playgroup's default world wants tuned pacing, authoring a `caverns_and_claudes/pacing.yaml` is content-side follow-up. Affects `sidequest-content/genre_packs/caverns_and_claudes/`.
- **Improvement:** ADR-024 (dual-track tension) and ADR-025 (pacing detection) are now wired end-to-end (producer 81-2 → consumer 81-3 → orchestrator injection); a docs pass could lift their DRIFT/partial status in `docs/adr/DRIFT.md` and the server CLAUDE.md ADR table. Affects `orc-quest/docs/adr/DRIFT.md`.

### Downstream Effects

Cross-module impact: 3 findings across 3 modules

- **`orc-quest/docs/adr`** — 1 finding
- **`sidequest-content/genre_packs`** — 1 finding
- **`sidequest-server/tests/agents`** — 1 finding

### Deviation Justifications

5 deviations

- **AC2 (prompt-assembly guard/injection) is not re-tested — it is pre-covered.**
  - Rationale: Avoids redundant coupling; the new failing surface is the bridge + emit, not the injection.
  - Severity: minor
- **When `pack.drama_thresholds` is None, the bridge resolves `DramaThresholds()` defaults (not a fail-loud).**
  - Rationale: A fail-loud here would break the default pack; the type's defaults are the intended absent-pacing behavior.
  - Severity: minor
  - Forward impact: Dev should resolve `pack.drama_thresholds or DramaThresholds()` at the construction site.
- **AC3 observability asserted as an OTEL span (`pacing.*`), not a watcher_hub event.**
  - Rationale: Match the emission convention already live in this function; refactor-stable behavioral assertion per "No Source-Text Wiring Tests".
  - Severity: minor
  - Forward impact: Dev adds a `pacing.hint_computed` span (suggest `SPAN_PACING_HINT` in `telemetry/spans/`) emitted from the bridge with drama_weight/target_sentences/delivery_mode attributes.
- **Pacing hint is always set (never None), so `[PACING]` now fires every turn.**
  - Rationale: Simplest correct code (TEA confirmed both designs pass). ADR-025's intent is that the narrator receives pacing guidance every turn; always-on is the honest reading. Suppression-to-None would be a token micro-optimization with no behavioral benefit.
  - Severity: minor
  - Forward impact: A truly quiet turn adds a small "Target ~1 sentence(s). Drama level: 0%." section to the prompt (~tokens). If prompt-byte pressure ever matters, a drama floor could suppress trivial hints — see Delivery Finding.
- **SPAN_PACING_HINT routed to GM panel under the `tension` component.**
  - Rationale: Matches the npc.working_set span convention and satisfies the routing-completeness lint; component grouping keeps the dual-track + pacing signals together for the dev.
  - Severity: minor
  - Forward impact: none.

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **AC2 (prompt-assembly guard/injection) is not re-tested — it is pre-covered.**
  - Spec source: context-story-81-3.md, AC-2
  - Spec text: "Test at the prompt-assembly layer: assert the section is present when a hint is set and absent when it is None (proving the guard still works)."
  - Implementation: The orchestrator-side guard + `register_pacing_section` injection is already exhaustively covered by `tests/agents/test_orchestrator_pacing_wiring.py` (present-registers, none-omits, Late zone, escalation beat, directive in rendered prompt). The story explicitly forbids touching `register_pacing_section`/the `[PACING]` format. Rather than duplicate, AC4's end-to-end test strengthens the present-case through the *real* `_build_turn_context` bridge; the None-case guard remains owned by the existing suite.
  - Rationale: Avoids redundant coupling; the new failing surface is the bridge + emit, not the injection.
  - Severity: minor
  - Forward impact: none
- **When `pack.drama_thresholds` is None, the bridge resolves `DramaThresholds()` defaults (not a fail-loud).**
  - Spec source: context-story-81-3.md, Assumptions + AC-1
  - Spec text: "DramaThresholds are resolvable from the active genre pack's config at the construction site" / "the hint may legitimately be None ... assert the system handles both without error."
  - Implementation: `caverns_and_claudes` (the default test pack) ships no `pacing.yaml`, so `pack.drama_thresholds` is None. Tests assert the bridge uses `DramaThresholds()` defaults in that case. This is the model's own documented contract ("Loaded from an optional pacing.yaml. Missing fields fall back to defaults"), so it is a *designed default*, not a silent fallback masking misconfiguration — the feature must work on caverns.
  - Rationale: A fail-loud here would break the default pack; the type's defaults are the intended absent-pacing behavior.
  - Severity: minor
  - Forward impact: Dev should resolve `pack.drama_thresholds or DramaThresholds()` at the construction site.
- **AC3 observability asserted as an OTEL span (`pacing.*`), not a watcher_hub event.**
  - Spec source: context-story-81-3.md, AC-3
  - Spec text: "A watcher/OTEL event records the per-turn computed pacing hint so the GM panel can verify it."
  - Implementation: `_build_turn_context` already emits OTEL spans via `sidequest.telemetry.spans` (`SPAN_NPC_WORKING_SET`, `dungeon_region_projection_span`); the closest analog wiring test in the same function (`test_budgeting_wired_into_build_turn_context`) asserts a `SPAN_*` via `otel_capture`. Test asserts a span named `pacing.*` carrying a `drama_weight` attribute. (81-2's producer used watcher_hub for `tension:round_observed`; the per-function convention here is the span.)
  - Rationale: Match the emission convention already live in this function; refactor-stable behavioral assertion per "No Source-Text Wiring Tests".
  - Severity: minor
  - Forward impact: Dev adds a `pacing.hint_computed` span (suggest `SPAN_PACING_HINT` in `telemetry/spans/`) emitted from the bridge with drama_weight/target_sentences/delivery_mode attributes.

### Dev (implementation)
- **Pacing hint is always set (never None), so `[PACING]` now fires every turn.**
  - Spec source: context-story-81-3.md, AC-1
  - Spec text: "when the tracker has no meaningful signal (fresh session / neutral state), the hint may legitimately be None — assert the system handles both without error."
  - Implementation: `_build_turn_context` unconditionally sets `pacing_hint = tracker.pacing_hint(thresholds)`. `pacing_hint()` is total (always returns a `PacingHint`), so the field is non-None even on a dead-quiet turn (drama_weight 0.0 → Instant, 1 sentence). The orchestrator guard is left intact and now passes every turn.
  - Rationale: Simplest correct code (TEA confirmed both designs pass). ADR-025's intent is that the narrator receives pacing guidance every turn; always-on is the honest reading. Suppression-to-None would be a token micro-optimization with no behavioral benefit.
  - Severity: minor
  - Forward impact: A truly quiet turn adds a small "Target ~1 sentence(s). Drama level: 0%." section to the prompt (~tokens). If prompt-byte pressure ever matters, a drama floor could suppress trivial hints — see Delivery Finding.
- **SPAN_PACING_HINT routed to GM panel under the `tension` component.**
  - Spec source: context-story-81-3.md, AC-3
  - Spec text: "A watcher/OTEL event records the per-turn computed pacing hint so the GM panel can verify it."
  - Implementation: New `sidequest/telemetry/spans/pacing.py` defines `SPAN_PACING_HINT = "pacing.hint_computed"` with a `SpanRoute(event_type="state_transition", component="tension", ...)` so the span reaches the GM-panel typed feed (not just raw OTEL), grouped with 81-2's `tension:round_observed`. `escalation_present` is emitted as a bool (OTEL attributes reject None).
  - Rationale: Matches the npc.working_set span convention and satisfies the routing-completeness lint; component grouping keeps the dual-track + pacing signals together for the dev.
  - Severity: minor
  - Forward impact: none.

### Reviewer (audit)
- **TEA — AC2 not re-tested (pre-covered)** → ✓ ACCEPTED by Reviewer: `test_orchestrator_pacing_wiring.py` genuinely covers the guard/injection (present + None) and the story forbids touching `register_pacing_section`; AC4 strengthens the present-case through the real bridge. Sound.
- **TEA / Dev — `pack.drama_thresholds or DramaThresholds()` default-fallback** → ✓ ACCEPTED by Reviewer: confirmed (with reviewer-security) this is the DramaThresholds model's documented optional-with-defaults, not a silent fallback masking misconfig; `_load_yaml_optional` raises on malformed YAML and returns None only on genuine absence. caverns_and_claudes (the default pack) requires this path.
- **TEA — AC3 asserted as OTEL span, not watcher_hub** → ✓ ACCEPTED by Reviewer: matches the emission convention already live in `_build_turn_context` (`npc.working_set`); the span is *routed* via `SpanRoute` so it reaches the GM-panel typed feed — the watcher/OTEL intent of the AC is satisfied, not bypassed.
- **Dev — pacing hint always set (never None), `[PACING]` fires every turn** → ✓ ACCEPTED by Reviewer: within AC1's permissive "may legitimately be None" language; aligns with ADR-025's intent that the narrator receives pacing guidance every turn and the OTEL "every decision emits" doctrine. Per-turn token cost is captured as a non-blocking finding, not a defect.
- **Dev — SPAN_PACING_HINT routed under `tension` component** → ✓ ACCEPTED by Reviewer: correct grouping with 81-2's `tension:round_observed`; `event_type="state_transition"` is in the known set; routing-completeness lint green; `escalation_present` as bool correctly avoids OTEL's None-attribute rejection.
- No undocumented deviations found — the diff matches the logged deviations exactly.

### Architect (reconcile)

**Existing entries verified** (spec source exists, spec text is an accurate quote, implementation description matches the merged code, forward impact accurate, all 6 fields present):
- TEA #1 (AC2 not re-tested) — verified: `context-story-81-3.md` AC-2 text quoted accurately; `test_orchestrator_pacing_wiring.py` confirmed to cover guard present/absent. Complete.
- TEA #2 / Dev #1 (`drama_thresholds or DramaThresholds()` default) — verified: AC-1/Assumptions text accurate; matches `session_helpers.py:1169`; reviewer-security independently confirmed it is documented optional-with-defaults, not a silent fallback. Complete.
- TEA #3 / Dev #2 (AC3 as routed OTEL span) — verified: AC-3 text accurate; matches `spans/pacing.py` (`SPAN_PACING_HINT` + `SpanRoute`, `state_transition`/`tension`); routing-completeness lint green. Complete.
- Dev #1 (hint always set, never None) — verified: AC-1 "may legitimately be None" quoted accurately; matches the unconditional `pacing_hint=pacing_hint`; within spec's permissive language. Complete.

All six fields are present and substantive on every entry; no field corrections needed.

**AC deferral check:** No ACs were deferred — AC1–AC4 are all DONE (AC2 satisfied by the pre-existing suite + AC4). No-op.

- No additional deviations found. The merged diff (`git diff develop`: session_helpers bridge, spans/pacing.py, __init__ re-export, test file) introduces no spec divergence beyond the four entries above, all of which fall within the story's stated permissive language and were stamped ACCEPTED by the Reviewer.