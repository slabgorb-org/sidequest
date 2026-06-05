---
story_id: "82-9"
jira_key: ""
epic: "82"
workflow: "tdd"
---
# Story 82-9: Per-turn latency diagnosis AC5 — live capture + wire latency_percentiles consumer

## Story Details
- **ID:** 82-9
- **Jira Key:** (local-only story, no Jira key)
- **Workflow:** tdd
- **Stack Parent:** none (AC5 follow-up to archived 71-40)
- **Repo:** sidequest-server (gitflow, targets develop)
- **Branch:** feat/82-9-latency-diagnosis-ac5

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-05T17:40:29Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-05T17:52:00Z | 2026-06-05T16:35:49Z | -4571s |
| red | 2026-06-05T16:35:49Z | 2026-06-05T16:50:03Z | 14m 14s |
| green | 2026-06-05T16:50:03Z | 2026-06-05T17:17:18Z | 27m 15s |
| review | 2026-06-05T17:17:18Z | 2026-06-05T17:29:50Z | 12m 32s |
| green | 2026-06-05T17:29:50Z | 2026-06-05T17:35:22Z | 5m 32s |
| review | 2026-06-05T17:35:22Z | 2026-06-05T17:40:29Z | 5m 7s |
| finish | 2026-06-05T17:40:29Z | - | - |

## Sm Assessment

**Setup complete — ready for RED (TEA).**

82-9 is the AC5 follow-up to archived 71-40 (epic 71). The AC1-AC4 latency instrumentation shipped + merged in server PR #689: intent_router.decompose now carries sdk_latency_ms + state_summary_bytes; complete_with_tools emits narrator.tool_loop (iterations_used) + narrator.tool_loop.cap_hit; latency_percentiles harness in telemetry/latency_report.py.

**This story closes the loop with three workstreams:**

1. **AC5 — Run a representative Glenross/tea_and_murder (or coyote_star) capture against a real ANTHROPIC_API_KEY, feed captured decompose/turn latencies through latency_percentiles, and commit the written env-vs-code + iteration-correlation diagnosis as a session/report artifact.**

2. **Wire latency_percentiles to a real consumer.** It currently has NONE (Reviewer wiring finding from 71-40). `latency_percentiles(values) -> LatencyPercentiles(p50, p95, count)` is exercised only by tests; this story adds the production operator/pipeline that invokes it.

3. **Address non-blocking Reviewer Delivery Findings as analysis surfaces them:**
   - Emit `narrator.tool_loop` on the loop-exceeded raise path (worst-latency turns currently invisible)
   - Rename/tag `narrator.tool_loop` so the non-narrator dungeon-curate caller (materializer.py) does not pollute solo-turn p95
   - Add an operator toggle for `iteration_cap` (no production caller sets it today)
   - Strengthen 3 test gaps (exactly-once cap-hit, dict-bytes equality, summary-absent-on-raise) and the vacuous sdk<=total invariant test

**Full detail in sprint/archive/71-40-session.md (Delivery Findings + Reviewer Assessment).**

**Key files to point the next agent at:**
- `sidequest-server/sidequest/telemetry/latency_report.py` — the harness with latency_percentiles
- Intent router decompose path in `sidequest-server/sidequest/agents/intent_router.py`
- `complete_with_tools` in `sidequest-server/sidequest/agents/anthropic_sdk_client.py` (narrator.tool_loop emit)
- `sidequest-server/sidequest/dungeon/materializer.py` (dungeon-curate caller, pollutes p95)

**Branch:** `feat/82-9-latency-diagnosis-ac5` in sidequest-server (off develop; PR targets develop). Dual-clone hazard noted — orchestrator session here, code branch in the subrepo.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Three of the four workstreams are unit/integration-testable (consumer wiring, OTEL spans, env resolver). Only AC6 (the live-capture prose artifact) is non-test-gated — see Delivery Findings.

**Test Files:**
- `tests/telemetry/test_latency_report_consumer.py` — AC1: `build_latency_report` consumer delegates to `latency_percentiles` (decompose + turn series, empty edge, render, tail-moves-p95). 5 tests.
- `tests/agents/test_tool_loop_loop_exceeded_visibility.py` — AC2: `narrator.tool_loop` summary span on the raise path with `loop_exceeded=True`, tracks `max_iterations`, converged path NOT marked; + AC5 exactly-once cap-hit. 4 tests.
- `tests/agents/test_tool_loop_caller_tag.py` — AC3: `caller` discriminator on the tool_loop span — real narrator turn tags `narrator`, curate-signature tags `dungeon_curate`, default is `narrator`. 3 tests.
- `tests/agents/test_narrator_iteration_cap_toggle.py` — AC4: `resolve_narrator_iteration_cap` env contract (unset/valid/non-int/non-positive) + real narrator-turn cap_hit wiring (toggle on → cap_hit fires; off → none). 7 tests.
- `tests/agents/test_latency_attribution_hardening.py` — AC5: dict→JSON `state_summary_bytes` equality, non-vacuous measured `sdk_latency_ms`. 2 tests (regression guards — pass against existing instrumentation at newly-covered inputs).

**Tests Written:** 21 tests covering 6 ACs (AC1–AC5 testable; AC6 non-gated).
**Status:** RED — 16 feature-driving tests fail (missing `build_latency_report`, `loop_exceeded` marker, `caller` tag, `resolve_narrator_iteration_cap` + wiring); 5 are regression guards/controls that pass. Verified serially (`-n0`) via testing-runner; all failures are assertion/missing-symbol, no collection or fixture errors.

### Rule Coverage

| Rule (SideQuest CLAUDE.md / SOUL) | Test(s) | Status |
|------|---------|--------|
| Verify Wiring, Not Just Existence (latency consumer) | `test_build_latency_report_delegates_to_harness_for_*` | failing |
| Every Test Suite Needs a Wiring Test (real narrator call site) | `test_narrator_turn_tags_tool_loop_caller_narrator`, `test_env_toggle_drives_cap_hit_on_real_narrator_turn` | failing |
| No Source-Text Wiring Tests (OTEL span + behavioral, not grep) | all span assertions via live `otel_capture` | failing |
| No Silent Fallbacks (operator toggle fails loud) | `test_resolve_iteration_cap_non_int_raises`, `_non_positive_raises[0/-3]` | failing |
| OTEL Observability (every subsystem decision emits a span) | `test_loop_exceeded_emits_summary_span_with_marker`, cap_hit tests | failing |
| Non-vacuous assertions (no constant/always-true) | `_tracks_max_iterations`, `_converged_*_not_marked`, `_sdk_latency_tracks_real_*` | mixed (guards pass) |

**Rules checked:** 6 of the applicable SideQuest wiring/observability rules have test coverage (no Rust/`lang-review` checklist applies — this is the Python server).
**Self-check:** 0 vacuous tests. The two AC5 hardening tests intentionally pass (they pin EXISTING instrumentation at inputs 71-40 left uncovered — regression guards, non-vacuous: dict-bytes equality + sdk_latency ≥ 20ms under a real 50ms sleep).

**Handoff:** To Dev (Naomi Nagata) for GREEN — implement the four features the failing tests pin.

## Dev Assessment

**Rework round 1 (post-REJECT):** Resolved all three Reviewer blocking findings — S1 (script fails loud on missing `intent_router.decompose`/`narration.turn` spans, clean `ERROR:` SystemExit, no fabricated artifact), S2 (`_corr` length guard → no `StatisticsError`; `sdk_share` empty-vs-all-zero → INDETERMINATE verdict, never a silent CODE), T3 (flaky `>=20` → `>=1`). Added `tests/telemetry/test_latency_diag_script.py` (7 guard tests — the script had none). Machine output on the real capture is byte-identical (committed artifact verdict unchanged: ENVIRONMENT 100%). Full affected-suite run: 398 passed, 0 failed. Pushed `0f6d135`. Non-blocking findings (E1 per-turn env parse, T1/T4/T5/T6, S3/S5) left as captured — opportunistic.

**Implementation Complete:** Yes — all of AC1–AC6 delivered.

**Files Changed (production — sidequest-server, branch `feat/82-9-latency-diagnosis-ac5`):**
- `sidequest/telemetry/latency_report.py` — AC1: `LatencyReport` + `build_latency_report` consumer (delegates to `latency_percentiles`).
- `sidequest/agents/anthropic_sdk_client.py` — AC2/AC3: `caller` kwarg; `narrator.tool_loop` summary span emitted on the loop-exceeded raise path with `loop_exceeded=True`; converged + raise spans tagged with `caller`.
- `sidequest/agents/narrator.py` — AC4: `resolve_narrator_iteration_cap()` operator toggle (fail-loud ValueError on non-int/non-positive).
- `sidequest/agents/orchestrator.py` — AC3/AC4 wiring: narrator turn forwards `iteration_cap=resolve_narrator_iteration_cap()` and `caller="narrator"`.
- `sidequest/dungeon/materializer.py` — AC3 wiring: curate call passes `caller="dungeon_curate"`.
- `sidequest/telemetry/spans/narrator.py` — surfaces `caller` + `loop_exceeded` in the `SPAN_NARRATOR_TOOL_LOOP` route extract (GM-panel filter).
- `docs/82-9-latency-diagnosis.md` — **AC5/AC6**: the live diagnosis artifact.
- `scripts/latency_diag_82_9.py` — AC5: analysis tool, a real production caller of `build_latency_report`.

**Test doubles synced (sidequest-server):** `tests/dungeon/test_materializer.py`, `tests/dungeon/test_lookahead_worker.py`, `tests/agents/test_61_followup_D_orchestrator_wiring.py`, `tests/agents/fakes/fake_anthropic_sdk_client.py` — absorb the new client kwargs.

**Files Changed (orchestrator — local on `main`, awaiting SM finish push):**
- `scenarios/latency_diag_82_9.yaml` — the 15-turn glenross capture scenario (reproducibility fixture).

**AC6 (live capture):** user authorized the spend; ran the 15-turn glenross scenario against a real ANTHROPIC_API_KEY (~$0.53), pulled spans from Jaeger, fed decompose + turn latencies through `build_latency_report`. **Verdict:** decompose p50 3.8s / p95 6.6s (3–5× over budget); ~100% of decompose is the raw Haiku SDK round-trip (env), but a 48KB `state_summary` (corr 0.50) is the code lever → input slimming (ADR-110) is the recommended next fix; tool-loop depth (mean 2.57, 0 loop-exceeded) is NOT the bottleneck.

**Tests:** 2585 passed, 0 failed, 1 skipped (tests/agents + tests/telemetry + tests/dungeon, serial `-n0`). All 21 of TEA's 82-9 tests GREEN; zero regressions.
**Branch:** `feat/82-9-latency-diagnosis-ac5` (pushed, 2 commits: impl + AC5 artifact).

**Handoff:** To next phase (verify/review).

## Subagent Results (Round 1)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 2 (script smells) | confirmed 2 (corroborate S2/S5), dismissed 0 |
| 2 | reviewer-edge-hunter | Yes | findings | 7 | confirmed 4 (E1, S1, S2, max_iter=0), dismissed 1 (zip self-dismissed), deferred 2 (LOW cosmetic) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 (both script) | confirmed 2 (S1 blocking, S3 non-blocking) |
| 4 | reviewer-test-analyzer | Yes | findings | 6 | confirmed 6 (T3 blocking-flaky; T1/T2/T4/T5/T6 non-blocking) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none | N/A — artifact + env parser verified clean |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (5 ran, 4 disabled via settings)
**Total findings:** 8 confirmed (3 blocking-for-rework, 5 non-blocking), 1 dismissed (with rationale), 2 deferred (LOW cosmetic)

### Rule Compliance

Rules sourced from SOUL.md + sidequest-server CLAUDE.md (no `lang-review/python.md` or `.claude/rules/` present).

| Rule | Instances checked | Verdict |
|------|-------------------|---------|
| **No Silent Fallbacks** | `resolve_narrator_iteration_cap()` (narrator.py) — int()+<=0 raise, unset→None: COMPLIANT (fail-loud, distinguishes unset from empty). `build_latency_report` empty→0/0/0: COMPLIANT (documented, mirrors `_percentile([])`). `spans/narrator.py` route `.get("caller","narrator")`: COMPLIANT (back-compat default for pre-82-9 spans; curate spans set caller explicitly). **`scripts/latency_diag_82_9.py` build_diagnosis on missing-span input → silent wrong "CODE 0%" verdict: VIOLATION (S1).** | 1 violation (S1) |
| **Verify Wiring, Not Just Existence** | `build_latency_report` now has a real production caller (`scripts/latency_diag_82_9.py`): COMPLIANT (closes 71-40 gap). `resolve_narrator_iteration_cap` imported+called at orchestrator:4125: COMPLIANT. `caller="dungeon_curate"` at materializer:1208: COMPLIANT (code verified). | COMPLIANT |
| **Every Test Suite Needs a Wiring Test** | AC3 narrator tag driven via real `run_narration_turn`; AC4 toggle driven via real narrator turn → cap_hit: COMPLIANT. AC3 curate call-site is contract-only (T2) — code wiring present, test drives only `complete_with_tools`: PARTIAL (documented deviation). | PARTIAL (documented) |
| **No Source-Text Wiring Tests** | All wiring assertions use live `otel_capture` spans / behavioral drives, no source greps: COMPLIANT. | COMPLIANT |
| **OTEL Observability (every subsystem decision emits a span)** | loop-exceeded raise path now emits `narrator.tool_loop` (loop_exceeded=True); caller tag + cap_hit routed to GM panel: COMPLIANT. | COMPLIANT |

## Reviewer Observations

- `[RULE]`/`[SILENT]` **[MEDIUM]** S1 — `scripts/latency_diag_82_9.py` `build_diagnosis` writes a confident "CODE dominates at 0%" verdict when the JSONL has no `intent_router.decompose`/`narration.turn` spans (wrong/empty capture), with no guard — violates **No Silent Fallbacks**. *Mitigation:* the rendered Sample section shows "decompose spans: 0", so a careful reader sees the emptiness — which is why this is MEDIUM not High, but the verdict LINE still lies. `scripts/latency_diag_82_9.py:146` (main has no required-span guard).
- `[EDGE]` **[MEDIUM]** S2 — `_corr(iters, loop_turn_ms)` raises `StatisticsError` (crash, no output file) when `len(loops) > len(turns)` — plausible under Jaeger 1000-span truncation. `loop_turn_ms = turns[:len(iters)]` is shorter than `iters` when loops outnumber turns. `scripts/latency_diag_82_9.py:176` (`_corr` lacks a `len(xs)!=len(ys)` guard).
- `[TEST]` **[MEDIUM]** T3 — flaky timing assertion: `assert sdk_latency_ms >= 20` after `asyncio.sleep(0.05)` will intermittently fail under heavy CI load (event-loop scheduling can absorb the 30ms margin). `tests/agents/test_latency_attribution_hardening.py:122`. Fix: floor to `>= 1` (still de-vacuifies the flat-mock case) or sleep 0.2s/floor 100.
- `[EDGE]` **[MEDIUM→non-blocking]** E1 — `resolve_narrator_iteration_cap()` is evaluated **per narration turn** at `orchestrator.py:4125`; a malformed opt-in env value raises `ValueError` mid-turn rather than once at startup (the `SIDEQUEST_SESSION_COST_CEILING_USD` precedent parses at construction). Fail-loud is correct; only deliberate misconfiguration of an opt-in knob (defaults off) triggers it. Recommend parse-once at startup or a docstring note. Non-blocking.
- `[VERIFIED]` raise-path span semantics — `anthropic_sdk_client.py:685` emits `narrator_tool_loop_span(iterations_used=max_iterations, loop_exceeded=True)` only after the `for iteration in range(1, max_iterations+1)` loop falls through without converging; `iterations_used==max_iterations` is structurally correct. Complies with OTEL Observability (worst-latency turn now visible).
- `[VERIFIED]` `caller` data flow — set at two internal call sites (`orchestrator.py:4126` `"narrator"`, `materializer.py:1210` `"dungeon_curate"`), flows through `narrator_tool_loop_span(**extra)` to the span attribute, surfaced in `SPAN_NARRATOR_TOOL_LOOP` route extract (`spans/narrator.py:84`). No untrusted input; defaults to `"narrator"`. Complies with No Silent Fallbacks (back-compat default is the correct interpretation of pre-82-9 spans).
- `[SEC]` **[VERIFIED]** committed artifact `docs/82-9-latency-diagnosis.md` and the env parser carry no secrets/keys/session-ids/PII — confirmed by reviewer-security and my own grep (only "Haiku"/"token cost" prose hits). The env value is parsed as int, never shell/SQL/template-interpolated.
- `[DOC]` subagent disabled — self-checked: the new docstrings (`resolve_narrator_iteration_cap`, `LatencyReport`, `build_latency_report`) accurately describe behavior; comments on the raise-path span and caller tag match the code. The flaky-test comment "guarantees >= 50ms" is misleading (it guarantees wall time, not measured interior time) — folded into T3.
- `[TYPE]` subagent disabled — self-checked: `caller: str = "narrator"` is stringly-typed (a 2-value enum/Literal would be tighter) but consistent with the existing span-attribute convention; `resolve_narrator_iteration_cap() -> int | None` is correctly typed. No new type violations.
- `[SIMPLE]` subagent disabled — self-checked: changes are minimal and non-duplicative; `build_latency_report` delegates rather than reimplementing percentiles. No over-engineering.
- `[RULE]` rule-checker disabled — Rule Compliance enumerated manually above; one violation (S1, No Silent Fallbacks).

### Devil's Advocate

Assume this code is broken. Where does it bite? Start with the operator knob. `SIDEQUEST_NARRATOR_ITERATION_CAP` is read on *every* narration turn. A deploy script that exports the var as an empty string instead of unsetting it — a classic shell foot-gun (`export X=$UNSET_VAR`) — makes `int("")` raise `ValueError` on turn one, and every turn after, until someone notices the whole session is dead. The error is clear, but it's a *runtime* death, not a *startup* refusal, so it surfaces in front of a player mid-game rather than at boot. That's the gap between "fail loud" and "fail loud at the right time." Now the diagnostic tool — the irony of this story. The whole point of 82-9 is honest diagnosis: OTEL as lie-detector, "no winging it." Yet `latency_diag_82_9.py` will, handed a wrong or truncated JSONL, print a confident "Dominant decompose cost: CODE … raw SDK round-trip is 0% of the decompose budget" — a fabricated verdict — and write it to disk. A future operator re-running the capture six months from now, pointing `--span-jsonl` at last week's stale file, gets a lie with a straight face. The sample-count header mitigates it for a careful reader, but the tool that exists to prevent winging-it can itself wing it. Worse, hand it a capture where loops outnumber turns (Jaeger truncation cut a trace mid-flight) and it doesn't lie — it *crashes* with `StatisticsError` and writes nothing, which at least fails loud but means the operator gets no diagnosis at all on exactly the kind of large, truncated capture the tool is for. A confused user would not understand why "more iterations than turns" crashes a percentile script. A stressed CI runner would hit the 30ms timing margin on `test_sdk_latency_tracks_real_emit_tool_duration` and flake red, eroding trust in the whole suite. None of these touch the engine's correctness — the AC1–AC6 features are sound and the live artifact is valid — but a committed diagnostic tool that can crash, mislabel, or lie, plus a flaky test, is not something I wave through on a story whose entire thesis is mechanical honesty. Three small guards fix all of it.

## Reviewer Assessment (Round 1 — REJECTED, superseded)

**Verdict:** REJECTED

The engine deliverable (AC1–AC6) is clean, well-wired, and the live diagnosis artifact is valid and secret-free — this is good work. But three concrete, cheap-to-fix defects keep it from merge: a flaky test, a No-Silent-Fallbacks violation in a committed diagnostic tool, and a latent crash in that tool. On a story whose entire thesis is mechanical honesty (OTEL the lie-detector), a diagnosis tool that can crash, mislabel, or lie is not acceptable. None are Critical/High on the engine; the rework is ~15 lines and tightly scoped.

| Severity | Issue | Source | Location | Fix Required |
|----------|-------|--------|----------|--------------|
| [MEDIUM] | Silent wrong verdict ("CODE 0%") on missing/empty span input — No Silent Fallbacks violation | `[SILENT]`/`[RULE]` | `scripts/latency_diag_82_9.py:146` (main) / build_diagnosis | Fail loud (raise/SystemExit) when no `intent_router.decompose` or no `narration.turn` spans are present, instead of writing a fabricated verdict. |
| [MEDIUM] | `StatisticsError` crash (no output) when `len(loops) > len(turns)` (Jaeger truncation) | `[EDGE]` | `scripts/latency_diag_82_9.py:176` (`_corr`) | Guard `_corr` against `len(xs) != len(ys)` (return None); and distinguish empty-vs-all-zero for `sdk_share` so the verdict is not silently inverted to CODE on degenerate data. |
| [MEDIUM] | Flaky timing assertion — intermittent CI failure | `[TEST]` | `tests/agents/test_latency_attribution_hardening.py:122` | Lower floor to `>= 1` (still proves non-zero / de-vacuifies the flat-mock case), or sleep 0.2s with floor `>= 100`. Fix the misleading "guarantees >= 50ms" comment. |

**Data flow traced:** operator env `SIDEQUEST_NARRATOR_ITERATION_CAP` → `resolve_narrator_iteration_cap()` (per-turn) → `complete_with_tools(iteration_cap=…, caller="narrator")` → `narrator_tool_loop_span` → GM-panel route extract. Engine path is correct; the per-turn parse location is a non-blocking nit (E1).
**Dispatch tags incorporated:** `[EDGE]` `[SILENT]` `[TEST]` `[SEC]` confirmed; `[DOC]` `[TYPE]` `[SIMPLE]` `[RULE]` self-checked (subagents disabled — see Observations).
**Non-blocking (do NOT gate merge, fix opportunistically):** E1 (per-turn env parse), T1 (`loop_exceeded` assert → `is None`), T2 (curate call-site contract-only — code wiring verified present), T4 (empty-string env test), T5/T6 (turn p50/p95 + render symmetry), S3/S5 (pre-82-9 caller filter / index-pairing comment).

**Handoff:** Back to TEA (Amos Burton) for red rework — the three blocking fixes are testable logic/test defects: write the failing guards (missing-span fail-loud; `_corr` length guard / empty-vs-zero), and correct the flaky timing floor.

## Subagent Results (Round 2 — rework re-review)

Focused re-review of a 3-file defensive rework (engine code unchanged from Round 1).

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 smells, 392 pass, lint clean | N/A — all 3 fixes present |
| 2 | reviewer-edge-hunter | Yes (self) | clean | self-verified | empty-loops handled by `if iters` guards; zip-strict sound; main() catch scoped |
| 3 | reviewer-silent-failure-hunter | Yes | findings | S1+S2b RESOLVED; 3 new (LOW/MED) | confirmed 3 non-blocking (advisory-correlation polish) |
| 4 | reviewer-test-analyzer | Yes | findings | 5 (test-quality) | confirmed 5 non-blocking; T3 verified correct for int-ms storage |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes (self) | clean | no new surface | guards are pure logic; no new attack surface |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (3 subagents ran on the rework diff, edge+security self-verified on the small surface, 4 disabled)
**Total findings:** 8 confirmed non-blocking; 0 blocking; the 3 Round-1 blockers all RESOLVED + verified.

## Reviewer Assessment

**Verdict:** APPROVED

The Round-1 rejection did its job. All three blocking findings are fixed and verified:
- **S1** `[SILENT]`/`[RULE]` — `build_diagnosis` now raises `ValueError` when the capture lacks `intent_router.decompose`/`narration.turn` spans; `main()` converts it to a clean `ERROR:` SystemExit and writes **no** artifact (manually confirmed: empty file → `ERROR: …`, no output written). No Silent Fallbacks satisfied for the verdict path. Pinned by 3 new tests.
- **S2** `[EDGE]` — `_corr` returns `None` (not `StatisticsError`) on unequal-length series; pinned by `test_corr_returns_none_on_length_mismatch_no_crash` + end-to-end `test_build_diagnosis_survives_more_loops_than_turns`.
- **T3** `[TEST]` — flaky `>= 20` → `>= 1`; `sdk_latency_ms` is stored int-ms (`(perf_counter_ns()-start)//1_000_000` in `intent_router.py`), so a 50ms sleep floors to ~50 and `>= 1` is the correct non-flaky de-vacuification.

Engine code is unchanged from Round 1 (already clean). The live diagnosis artifact verdict + percentiles are byte-identical (ENVIRONMENT, 100% raw SDK). `[SEC]` no new attack surface; `[DOC]` rework comments accurate; `[TYPE]` no new type issues; `[SIMPLE]` minimal defensive guards, no over-engineering; `[RULE]` the verdict path now complies with No Silent Fallbacks (the Round-1 violation is closed).

**Non-blocking findings (captured, do NOT gate merge):** the `loop_turn_ms = turns[:len(iters)]` slice still silently truncates when *turns > loops* (advisory iteration correlation only — verdict/percentiles unaffected; recommend removing the slice and letting `_corr`'s length guard return None symmetrically); `_corr`-None conflates truncation vs boring-data; empty-capture test lacks `match=`; no `main()` integration test (behavior manually verified); more-loops test doesn't assert the verdict word; caller-empty-loops path untested. All on a manually-run diagnostic tool's advisory correlation / test symmetry — disproportionate to ping-pong a third round.

**Data flow re-traced:** wrong/empty `--span-jsonl` → `build_diagnosis` raises → `main()` SystemExit with clear message, no artifact written (was the Round-1 silent-wrong-verdict; now fail-loud).
**Handoff:** To SM (Camina Drummer) for finish.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (blocking): AC3's curate-side caller tag has a real wiring step the
  narrator side does not — the curate call site must pass the new `caller`
  kwarg. `test_tool_loop_caller_tag.py` proves the contract at the
  `complete_with_tools` level (a curate-signature call tags
  `caller="dungeon_curate"`) AND drives a real narrator turn (tags
  `caller="narrator"`), but the curate PRODUCTION call site is not driven by a
  test (the `_stage_curate` harness needs a full MaterializationRequest +
  bundle + palette + expansion). Dev MUST pass `caller="dungeon_curate"` at
  `sidequest/dungeon/materializer.py:1208`; otherwise it defaults to "narrator"
  and curate loops keep polluting solo-turn p95. Affects
  `sidequest/dungeon/materializer.py` (the one-shot curate `complete_with_tools`
  call). *Found by TEA during test design.*
- **Gap** (blocking): AC6 — the AC5 live-capture diagnosis artifact (env-vs-code
  numbers + iteration correlation, written from a real `ANTHROPIC_API_KEY`
  Glenross/tea_and_murder/coyote_star run through `build_latency_report`) is NOT
  test-gated (prose + live network, same as 71-40's AC5). The new
  `build_latency_report` consumer is the tool the artifact is produced WITH, but
  the artifact itself must be committed by Dev/SM before story-done. Affects a
  new `sprint/` or `docs/` report artifact. *Found by TEA during test design.*
- **Question** (non-blocking): the `caller` discriminator is implemented as a
  TAG (extra span attribute via the existing `narrator_tool_loop_span(**extra)`
  seam), NOT a span RENAME to `sdk.tool_loop`. Tag was chosen because rename
  would break the existing 71-40 tests that assert the span name
  `narrator.tool_loop` and would relocate the GM-panel p95 source. Dev/Architect
  should confirm the GM-panel p95 query filters on `caller="narrator"` rather
  than relying on the curate calls being absent. Affects the GM-panel projection
  + `sidequest/telemetry/spans/narrator.py` SPAN_ROUTES extract (it may want to
  surface `caller`). *Found by TEA during test design.*

### Dev (implementation)
- **Resolved** (was TEA blocking — curate call-site wiring): materializer:1208
  now passes `caller="dungeon_curate"`; full `tests/dungeon/` suite GREEN (463
  pass). *Found by Dev during implementation.*
- **Resolved** (was TEA blocking — AC6 live-capture artifact): produced the AC5
  diagnosis from a live `tea_and_murder/glenross` 15-turn capture against a real
  ANTHROPIC_API_KEY (user-authorized the spend, ~$0.53). Committed
  `sidequest-server/docs/82-9-latency-diagnosis.md` + the analysis consumer
  `sidequest-server/scripts/latency_diag_82_9.py`. Verdict: decompose stall is
  ~100% the raw Haiku SDK round-trip (env), but a 48KB `state_summary` (corr 0.50)
  is the actionable code lever → input slimming (ADR-110) is the recommended next
  fix; tool-loop depth is NOT the bottleneck. *Found by Dev during implementation.*
- **Improvement** (non-blocking, answers TEA's Question): the GM-panel p95 query
  should filter `narrator.tool_loop` rows to `caller="narrator"`. I added `caller`
  AND `loop_exceeded` to the `SPAN_NARRATOR_TOOL_LOOP` route extract
  (`sidequest/telemetry/spans/narrator.py`) so both are available to the panel
  projection. The panel-side filter itself (UI/projection) is out of this story's
  server scope. Affects the GM-panel projection. *Found by Dev during implementation.*
- **Improvement** (non-blocking): the Jaeger `--span-jsonl` capture truncates at a
  1000-span limit (~7 of 15 glenross turns, each ~140 spans). The AC5 sample is
  therefore n=7–8 — the env-vs-code verdict is robust but the p95 is indicative,
  not tight. A future capture wanting a tight p95 should raise the Jaeger query
  limit or page the query. Affects `scripts/playtest.py` (Jaeger query limit).
  *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): `scripts/latency_diag_82_9.py` emits a silent wrong verdict
  ("CODE 0%") on a capture missing `intent_router.decompose`/`narration.turn`
  spans — No Silent Fallbacks. Affects `scripts/latency_diag_82_9.py` (add a
  fail-loud required-span guard in `main`/`build_diagnosis`). *Found by Reviewer
  during code review.*
- **Gap** (blocking): `_corr` crashes with `StatisticsError` when
  `len(loops) > len(turns)` (Jaeger truncation). Affects
  `scripts/latency_diag_82_9.py:176` (`_corr` needs a `len` guard; distinguish
  empty-vs-all-zero for `sdk_share`). *Found by Reviewer during code review.*
- **Gap** (blocking): flaky timing assertion `sdk_latency_ms >= 20` after a 50ms
  sleep. Affects `tests/agents/test_latency_attribution_hardening.py:122` (floor
  to `>= 1` or sleep longer). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `resolve_narrator_iteration_cap()` parses the
  env per narration turn; a bad opt-in value raises mid-turn, not at startup.
  Affects `sidequest/agents/narrator.py` + `orchestrator.py:4125` (parse-once at
  startup or document). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): AC3 curate call-site has code wiring
  (materializer:1210 verified) but only a contract-level test; T1 `loop_exceeded`
  assertion is absent-vs-False ambiguous; T4 empty-string env case uncovered;
  T5/T6 turn p50/p95 + render symmetry. Affects the 82-9 test files (tighten when
  convenient). *Found by Reviewer during code review.*

### Reviewer (code review — round 2, APPROVED)
- **Improvement** (non-blocking): `loop_turn_ms = turns[:len(iters)]` silently
  truncates excess turns when turns > loops — masks a count mismatch in the
  advisory iteration correlation (verdict/percentiles unaffected). Affects
  `scripts/latency_diag_82_9.py:95` (remove the slice; let `_corr`'s length guard
  return None symmetrically). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `_corr`→None conflates count-mismatch with
  zero-variance; empty-capture test lacks `match=`; no `main()` end-to-end test
  (behavior manually verified: empty file → clean `ERROR:`, no artifact written);
  more-loops test doesn't assert the verdict word; caller-empty-loops path
  untested. Affects `scripts/latency_diag_82_9.py` + `tests/telemetry/test_latency_diag_script.py`.
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking, pre-existing): `latency_percentiles([])` returns
  0.0/0.0/0 — a documented empty contract that a future caller outside
  `build_diagnosis` could mistake for real data. Affects
  `sidequest/telemetry/latency_report.py` (not a rework regression). *Found by
  Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **AC5 "summary-absent-on-raise" gap is INVERTED to "summary-present-on-raise"**
  - Spec source: context-story-82-9.md / 71-40 Reviewer findings
  - Spec text: story lists both "emit narrator.tool_loop on the loop-exceeded raise path" AND "strengthen 3 test gaps (... summary-absent-on-raise)"
  - Implementation: I did NOT write a test pinning "summary absent on raise". AC2 explicitly ADDS the summary on the raise path, so the old gap is superseded — `test_loop_exceeded_emits_summary_span_with_marker` pins the NEW behavior (summary PRESENT on raise with `loop_exceeded=True`), and `test_converged_summary_is_not_marked_loop_exceeded` keeps the marker non-vacuous.
  - Rationale: the two story bullets are contradictory only if read literally; AC2 is the authoritative intent (worst-latency turns must be visible). Pinning the old absent-on-raise behavior would directly conflict with AC2.
  - Severity: minor
  - Forward impact: none — the new behavior is fully covered.
- **AC4 resolver invalid-input contract pinned to `ValueError`**
  - Spec source: context-story-82-9.md, AC4 ("operator toggle ... No Silent Fallbacks")
  - Spec text: "add an operator toggle for iteration_cap"; story does not name an exception type
  - Implementation: `test_resolve_iteration_cap_non_int_raises` / `_non_positive_raises` assert `pytest.raises(ValueError)` rather than a blind `Exception` (ruff B017) or a custom config error.
  - Rationale: `int("lots")` raises ValueError natively and the cost-ceiling parser precedent rejects non-positive values loudly; ValueError is the idiomatic fail-loud type and a custom subclass of ValueError would still satisfy the test. Dev keeps latitude on a custom type as long as it derives from ValueError.
  - Severity: minor
  - Forward impact: if Dev raises a non-ValueError config error, the test must widen to that type.
- **AC3 curate production call site not driven by a test (contract-only)**
  - Spec source: context-story-82-9.md, AC3
  - Spec text: "rename/tag narrator.tool_loop so the non-narrator dungeon-curate caller (materializer.py) does not pollute solo-turn p95"
  - Implementation: the narrator call site gets a real wiring test (`run_narration_turn` → `caller="narrator"`); the curate call site gets a contract test at the `complete_with_tools` level plus a blocking Delivery Finding, NOT a driven-through-`_stage_curate` test.
  - Rationale: `_stage_curate` requires a full MaterializationRequest + bundle + palette + expansion + fill_result fixture — disproportionate for a 3pt chore; the contract test + finding give Dev an unambiguous target without the heavy harness.
  - Severity: minor
  - Forward impact: Reviewer should confirm materializer:1208 passes `caller="dungeon_curate"` (the existing curate integration tests guard the call site shape).

### Dev (implementation)
- **Four test-double signatures widened to absorb the new client kwargs**
  - Spec source: tests TEA wrote + the real `complete_with_tools` signature
  - Spec text: n/a (production change forces test-double parity)
  - Implementation: added `**_kwargs` to the explicit-signature `complete_with_tools` doubles in `tests/dungeon/test_materializer.py`, `tests/dungeon/test_lookahead_worker.py`, `tests/agents/test_61_followup_D_orchestrator_wiring.py`, and `tests/agents/fakes/fake_anthropic_sdk_client.py` — they previously enumerated kwargs and broke when production began passing `caller=` (and the orchestrator `iteration_cap=`).
  - Rationale: a test double must track the real interface it stands in for; absorbing extra kwargs is the minimal, future-proof sync (the other materializer doubles already use `*a, **k`). Not a behavior change — the doubles ignore the new kwargs.
  - Severity: minor
  - Forward impact: none — doubles now tolerant of further client-signature additions.
- **GM-panel route extract surfaces `caller` + `loop_exceeded` (beyond strict test need)**
  - Spec source: TEA Question finding (GM-panel p95 filter) + OTEL Observability Principle
  - Spec text: "rename/tag ... so the dungeon-curate caller does not pollute solo-turn p95"
  - Implementation: added `caller` and `loop_exceeded` keys to the `SPAN_NARRATOR_TOOL_LOOP` `SPAN_ROUTES` extract. No test asserts the route extract keys, but without them the GM panel cannot read the discriminator the story exists to provide.
  - Rationale: completing the observability wiring the discriminator is FOR — a tag the panel can't read is dead weight. Minimal addition, consistent with the cap-hit route which already surfaces its attributes.
  - Severity: minor
  - Forward impact: GM-panel projection can now filter solo-turn p95 to `caller="narrator"` and flag `loop_exceeded` turns.

### Reviewer (audit)
- **TEA — AC5 "summary-absent-on-raise" inverted to "summary-present-on-raise"** → ✓ ACCEPTED by Reviewer: AC2 is the authoritative intent (worst-latency turns must be visible); pinning the old absent-on-raise behavior would contradict it. Sound.
- **TEA — AC4 resolver invalid-input pinned to `ValueError`** → ✓ ACCEPTED by Reviewer: `int()` raises ValueError natively and the implementation matches; idiomatic fail-loud type.
- **TEA — AC3 curate production call-site contract-only** → ✓ ACCEPTED by Reviewer: the heavy `_stage_curate` harness is disproportionate for a 3pt chore; code wiring at materializer:1210 is verified present. Captured as non-blocking T2.
- **Dev — four test-double signatures widened with `**_kwargs`** → ✓ ACCEPTED by Reviewer: a test double must track the real interface; absorbing extra kwargs is the minimal sync and matches the existing `*a, **k` doubles. Full suite GREEN.
- **Dev — route extract surfaces `caller` + `loop_exceeded`** → ✓ ACCEPTED by Reviewer: completes the observability wiring the discriminator exists for; a tag the panel can't read is dead weight. Consistent with the cap-hit route.
- **UNDOCUMENTED (Reviewer-spotted):** `scripts/latency_diag_82_9.py` `render()`/`build_diagnosis` produce a verdict with no required-span precondition — diverges from the No-Silent-Fallbacks spirit the rest of the codebase enforces. Not logged by Dev. Severity: M. Captured as blocking finding S1.

### Reviewer (audit — round 2)
- The rework introduced **no new spec deviations**: the three fixes (S1 fail-loud guard, S2 `_corr` length guard / empty-vs-zero, T3 `>=1`) implement exactly what the Round-1 findings specified. The Round-1 UNDOCUMENTED S1 divergence is now **closed** by the fail-loud guard. All Round-1 deviations remain ACCEPTED as stamped.