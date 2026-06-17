---
story_id: "119-5"
jira_key: ""
epic: "119"
workflow: "tdd"
---
# Story 119-5: 119-3 transport-port cleanup (OQ-17): remove or re-home the now-vestigial Intent-Router cache-floor guard and restore coverage

## Story Details
- **ID:** 119-5
- **Jira Key:** (none — SideQuest uses sprint YAML, not Jira)
- **Workflow:** tdd
- **Stack Parent:** none
- **Repos:** server
- **Branch:** feat/119-5-transport-port-cache-floor-cleanup

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-17T06:20:51Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-17T03:34:12Z | 2026-06-17T03:36:25Z | 2m 13s |
| red | 2026-06-17T03:36:25Z | 2026-06-17T05:45:48Z | 2h 9m |
| green | 2026-06-17T05:45:48Z | 2026-06-17T05:58:02Z | 12m 14s |
| review | 2026-06-17T05:58:02Z | 2026-06-17T06:10:13Z | 12m 11s |
| green | 2026-06-17T06:10:13Z | 2026-06-17T06:16:35Z | 6m 22s |
| review | 2026-06-17T06:16:35Z | 2026-06-17T06:20:51Z | 4m 16s |
| finish | 2026-06-17T06:20:51Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): `scripts/spike_119_3_agentsdk_subscription.py` does NOT exist — there are no spike scripts in `scripts/` at all. The story phrasing "gate scripts/spike_119_3_agentsdk_subscription.py in ops/CI" implies it already exists; it does not. Dev must CREATE it net-new (gate-first: check `SIDEQUEST_VERIFY_SUBSCRIPTION_ISOLATION_LIVE` and refuse loudly with a non-zero exit naming the env BEFORE importing the SDK / touching the network), then wire the opt-in CI gate. Affects `scripts/` (new file) + CI config. *Found by TEA during test design.*
- **Gap** (non-blocking): deleting the guard must also delete its OTEL span machinery, or telemetry advertises a guard that no longer runs. Affects `sidequest/telemetry/spans/intent_router.py` (`SPAN_INTENT_ROUTER_CACHE_FLOOR` :87, the field-registry entry :92, `intent_router_cache_floor_span` :611, docstrings :13 and :625) and the import at `sidequest/agents/llm_factory.py:46`. The `_PREFIX_CHARS_PER_TOKEN` calibration constant + the comment block at :340-368 are part of the same dead machinery. *Found by TEA during test design.*
- **Improvement** (non-blocking): line drift in the story — `_neutral_cwd()` is at `anthropic_sdk_client.py:173` (`mkdtemp` at :177, call site :254), not `:156`. No `atexit`/`shutil` import exists in that module yet; AC2 needs both. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): the 92-2 AC7 test `test_cache_floor_guard_not_applied_to_local_path` had its premise removed by this deletion (there is no floor guard on any path now). Updated its docstring to reflect 119-5 and kept the sub-floor monkeypatch as a regression anchor; the assertion (local rung builds the ollama adapter) is still valid. Affects `tests/agents/test_92_2_local_classification_rung.py`. *Found by Dev during implementation.*
- No other upstream findings during implementation.

### Reviewer (code review)
- **Gap** (blocking): the AC3 spike's contamination check silently green-lights on an empty probe reply (`text = result.text or ""` → empty tell-scan → exit 0). Affects `scripts/spike_119_3_agentsdk_subscription.py` (`_run_probe` — guard empty text before the scan; add a unit test). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `_PERSONA_TELLS` includes generic tokens (`orchestrator`, `Claude Code`) that a clean model can emit → false-positive contamination. Affects `scripts/spike_119_3_agentsdk_subscription.py` (restrict to repo-specific markers; add precision tests). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the spike prints the full model reply unconditionally to stdout; on contamination it propagates into CI logs. Affects `scripts/spike_119_3_agentsdk_subscription.py` (print reply on contamination/error branches to stderr only). *Found by Reviewer during code review.*

### Reviewer (re-review)
- All three round-1 findings resolved in the green rework (verified by re-run subagents + diff inspection). No new upstream findings during re-review. *Found by Reviewer during code review (round 2).*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **AC1 resolved to DELETE the cache-floor guard, not re-home it**
  - Spec source: context-story-119-5.md, AC1 (+ session SM Assessment)
  - Spec text: "Either delete the guard wholesale OR re-home it onto an SDK-exposed cache signal, with a test asserting the chosen behavior"
  - Implementation: Tests pin DELETE — `test_119_5_cache_floor_guard_removed.py` asserts the four symbols (`IntentRouterCacheFloorError`, `HAIKU_CACHEABLE_PREFIX_FLOOR_TOKENS`, `_INTENT_ROUTER_CACHE_TTL`, `_estimate_intent_router_prefix_tokens`) are removed, the build never refuses a sub-floor prefix, and the `intent_router.cache_floor` span no longer fires.
  - Rationale: Measured the SDK path — `_IntentRouterLlm.emit_tool` (llm_factory.py:473-479) drives `build_agent_sdk_options(...)` with `output_format` and ships **no** `cache_control` marker; `claude-agent-sdk` exposes no caller-visible cache-control surface. The re-home target does not exist, so re-homing would be stubbing infrastructure (No Stubbing / Don't Reinvent). DELETE is the only honest option — not a genuine fork, so Architect was not consulted.
  - Severity: minor
  - Forward impact: none — Dev deletes the four symbols + the `cache_floor` OTEL span machinery (see Delivery Findings).
- **Deleted tests/agents/test_91_3_cache_floor_guard.py in the RED commit**
  - Spec source: context-story-119-5.md, Story Summary / Notes
  - Spec text: "The test suite test_haiku_cache_control.py was deleted during 119-3's full-replace" / "live-but-uncovered code (tests were deleted in 119-3)"
  - Implementation: Stale premise — `test_haiku_cache_control.py` WAS deleted by 119-3 (commit f970091e), but `test_91_3_cache_floor_guard.py` SURVIVED and still covered the guard end-to-end. The guard was therefore *covered*, not uncovered. Deleted `test_91_3_cache_floor_guard.py` as part of the removal (it pins the now-removed behavior; it would fail the moment Dev deletes the guard).
  - Rationale: TEA owns test design, including retiring tests of intentionally-removed behavior (Delete dead code in the same PR). The new RED contract expresses the post-removal behavior only.
  - Severity: minor
  - Forward impact: none — deletion already staged in the RED commit.

### Dev (implementation)
- **AC3 ops/CI gate implemented as an env-opt-in, not a dedicated CI job**
  - Spec source: context-story-119-5.md, AC3
  - Spec text: "Gate scripts/spike_119_3_agentsdk_subscription.py in ops/CI."
  - Implementation: The smoke is gated behind `SIDEQUEST_VERIFY_SUBSCRIPTION_ISOLATION_LIVE` (the established SideQuest live-smoke pattern — same shape as `SIDEQUEST_VERIFY_HAIKU_CACHE_LIVE` / the composer Gymnopedie smoke). The script refuses loudly without it; the ops/CI invocation is documented in the script header. No new CI-workflow YAML job was added.
  - Rationale: SideQuest live smokes are gated by opt-in env, not per-smoke CI jobs (there is no precedent CI job for the existing live smokes); a scheduled/triggered CI job is an ops decision outside this repo's test contract. The env-gate IS the gate mechanism the tests pin.
  - Severity: minor
  - Forward impact: minor — if ops wants the smoke on a schedule, a CI job invoking `SIDEQUEST_VERIFY_SUBSCRIPTION_ISOLATION_LIVE=1 python scripts/spike_119_3_agentsdk_subscription.py` (creds unset) can be added later; the script is ready.

### Reviewer (audit)
- **TEA: AC1 resolved to DELETE, not re-home** → ✓ ACCEPTED by Reviewer: verified independently — `_IntentRouterLlm.emit_tool` drives `build_agent_sdk_options(... output_format ...)` with no `cache_control` marker, and the SDK exposes no caller-visible cache surface; re-homing would be stubbing a signal that doesn't exist. DELETE is the only honest option.
- **TEA: deleted test_91_3_cache_floor_guard.py in the RED commit** → ✓ ACCEPTED by Reviewer: the file pinned the now-removed guard end-to-end; retiring it with the behavior is correct (delete dead code in the same PR). The "live-but-uncovered" premise was indeed partially stale.
- **Dev: AC3 ops/CI gate as env-opt-in, not a dedicated CI job** → ✓ ACCEPTED by Reviewer: matches the established SideQuest live-smoke pattern (`SIDEQUEST_VERIFY_HAIKU_CACHE_LIVE`, the composer Gymnopedie smoke); there is no precedent per-smoke CI job, and a scheduled job is an ops decision. The env-gate IS the gate the tests pin. (Note: the gate *mechanism* is sound; the rejection is about the spike's *detection logic*, not its gating.)

## Sm Assessment

**Story 119-5** — transport-port cleanup in `sidequest-server` (3pt, p2, tdd). Setup complete; routing to TEA for the RED phase.

**Setup verified:**
- Session at `.session/119-5-session.md`; branch `feat/119-5-transport-port-cache-floor-cleanup` cut from server `develop`.
- Context at `sprint/context/context-story-119-5.md` is complete (all 3 ACs, key files, dependency on 119-3, No-Silent-Fallbacks note). Parent epic context `context-epic-119.md` present.
- Jira explicitly skipped — SideQuest uses sprint YAML, not Jira.
- Merge gate clear (Status: Available, no blocking PRs).

**Scope — three coupled fixes (all in the agents module):**
1. **Vestigial cache-floor guard (the core decision).** After 119-3's full-replace to claude-agent-sdk, the SDK path emits **no** `cache_control` markers, so `IntentRouterCacheFloorError` / `HAIKU_CACHEABLE_PREFIX_FLOOR_TOKENS` / `_INTENT_ROUTER_CACHE_TTL` / `_estimate_intent_router_prefix_tokens` + the `build_intent_router_llm` floor check (`llm_factory.py:646-667`) guard a trap the code can no longer spring. It is **live-but-uncovered** (119-3 deleted `test_haiku_cache_control.py`). Either **delete wholesale** or **re-home onto an SDK-exposed cache signal** — TEA/Architect's call — and a test must assert the chosen behavior (**No Silent Fallbacks**).
2. **Temp-dir leak.** Register an `atexit` cleanup for `_neutral_cwd()`'s `mkdtemp` dir (`anthropic_sdk_client.py:156`) — one empty dir leaked per process today.
3. **Gated LIVE isolation smoke.** AC1's contamination regression mocks the `query` seam and cannot catch a real-SDK context-absorption regression; gate `scripts/spike_119_3_agentsdk_subscription.py` in ops/CI.

**Note for TEA (Fezzik):** AC1 is a decision point, not a mechanical delete — the failing test should pin whichever behavior is chosen (deletion → assert the guard/constants are gone and the trap can't fire; re-home → assert it fires on a real SDK cache signal). Loop Architect (The Man in Black) in if the delete-vs-rehome call is non-obvious. Watch the full server suite baseline (~258-269 hermeticity-guard pre-existing failures + `SIDEQUEST_DATABASE_URL` env tell) — don't mistake those for regressions.

**Workflow:** tdd → next phase **red**, owner **tea**.

## TEA Assessment

**Tests Required:** Yes
**Reason:** n/a — three behavioral ACs, all testable.

**Test Files:**
- `tests/agents/test_119_5_cache_floor_guard_removed.py` — AC1: the four vestigial cache-floor symbols are removed, the build no longer refuses a sub-floor prefix (behavioral), and no `intent_router.cache_floor` span fires.
- `tests/agents/test_119_5_neutral_cwd_atexit_cleanup.py` — AC2: `_neutral_cwd()` registers an `atexit` cleanup that removes the temp dir; the dir stays process-stable (one registration, no per-call re-leak).
- `tests/agents/test_119_5_subscription_isolation_smoke.py` — AC3: the gated live spike script exists, refuses loudly without the gate, and (opt-in) runs the real-SDK isolation check.
- DELETED `tests/agents/test_91_3_cache_floor_guard.py` — pinned the now-removed guard behavior (see Design Deviations).

**Tests Written:** 10 tests (+1 opt-in gated live) covering 3 ACs
**Status:** RED (verified via testing-runner, run `119-5-tea-red`) — 10 failed, 1 skipped (the gated live smoke). `test_91_3_cache_floor_guard.py` confirmed not collected.

### Rule Coverage

This is a deletion/cleanup story (Python), so the lang-review rubric maps to the project's load-bearing rules rather than type-constructor checks:

| Rule | Test(s) | Status |
|------|---------|--------|
| No Silent Fallbacks (dead guard removed, not dormant) | `test_vestigial_floor_symbol_is_removed` (×4), `test_build_does_not_raise_on_subfloor_prefix` | failing |
| No Silent Fallbacks (dead telemetry removed) | `test_build_emits_no_cache_floor_span` | failing |
| No Silent Fallbacks (gated smoke refuses, never green-lights) | `test_spike_script_refuses_without_live_gate` | failing |
| No resource leak (atexit cleanup wired) | `test_neutral_cwd_registers_atexit_cleanup`, `test_neutral_cwd_is_idempotent_within_a_process` | failing |
| No Source-Text Wiring Tests (behavioral/reflective only) | all of the above (hasattr/build/span/subprocess — no `read_text()` greps) | enforced |
| Every Test Suite Needs a Wiring Test | `test_build_does_not_raise_on_subfloor_prefix` exercises the real `build_intent_router_llm`; `test_spike_script_*` runs the script as CI would | failing/RED |

**Rules checked:** 6 of 6 applicable rules have test coverage.
**Self-check:** 0 vacuous tests — every test asserts a behavior (build result, span absence, dir removal, exit code), not a tautology.

**Decision recorded:** AC1 → DELETE (re-home target does not exist on the SDK path). Full rationale in Design Deviations. Architect not consulted — the evidence made it not a genuine fork.

**Handoff:** To Dev (Inigo Montoya) for GREEN. The three Delivery-Findings gaps (net-new spike script, OTEL span machinery removal, the `:156`→`:173` line drift) are the non-obvious parts of GREEN — read them before starting. Doctrine reminder: this is a transport-port cleanup, NOT a combat/ruleset change — no balancing concerns.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/agents/llm_factory.py` — deleted the four vestigial cache-floor symbols + `_PREFIX_CHARS_PER_TOKEN`, the `build_intent_router_llm` floor-check block, the floor-guard docstring paragraphs, and the `intent_router_cache_floor_span` import (AC1).
- `sidequest/telemetry/spans/intent_router.py` — deleted `SPAN_INTENT_ROUTER_CACHE_FLOOR` + its `SPAN_ROUTES` entry, the `intent_router_cache_floor_span` context manager, and the module-docstring bullet (AC1).
- `sidequest/agents/anthropic_sdk_client.py` — added `import atexit`/`import shutil`, a `_cleanup_agent_sdk_cwd()` callback, and `atexit.register(...)` in `_neutral_cwd()` when the dir is first created (AC2).
- `scripts/spike_119_3_agentsdk_subscription.py` — NEW gate-first live isolation smoke driving a real subscription turn through the production isolation pins, exiting non-zero on repo-context contamination (AC3).
- `tests/agents/test_92_2_local_classification_rung.py` — updated the AC7 docstring (its guard premise was removed; assertion still valid).

**Tests:** 34/34 passing (GREEN) on the touched files + 1 expected SKIP (gated live smoke). Blast-radius regression (`tests/agents/` + `tests/telemetry/`): 1834 passed, 0 failed. Ruff lint + format clean on all changed files.

**Branch:** `feat/119-5-transport-port-cache-floor-cleanup` (pushed to `origin` / slabgorb-org/sidequest-server)

**Self-review:**
- All 3 ACs met (guard removed + tested, atexit cleanup wired + tested, gated smoke created + tested).
- Wiring verified: `_cleanup_agent_sdk_cwd` is registered from the real `_neutral_cwd()` (the production call site at `build_agent_sdk_options:254`); the spike script runs the real `AnthropicSdkClient` (no fake seam).
- No dead code left: grep confirms zero surviving references to any removed symbol across `sidequest/`, `tests/`, `scripts/` (only my own test + the updated 92-2 docstring mention the names).
- No silent fallbacks introduced; the smoke refuses loudly without its gate.

**Handoff:** To Reviewer (Westley) for code review.

### Dev Rework — Review Round 1 (2026-06-17)

Addressed all three Reviewer findings, all in `scripts/spike_119_3_agentsdk_subscription.py`:
- **[HIGH] empty-reply silent green-light** → extracted `_assess_reply(text)`, which now REFUSES (returns 1, prints `INCONCLUSIVE` to stderr) on empty/whitespace-only text instead of scanning an empty string and reporting "OK". The `noop`-tool comment now notes the empty case is caught by the guard.
- **[MEDIUM] tell-list false positives** → dropped the generic tokens (`orchestrator`, `Claude Code`, plus the borderline `Scrum Master`); `_PERSONA_TELLS` is now repo-specific (`Pennyfarthing`, `SideQuest`, `SOUL.md`, `genre pack`, persona proper-names). Extracted pure `_detect_persona_tells(text)`.
- **[LOW] CI-log leak** → the full reply is echoed only on the empty/contaminated stderr branches; the clean path prints just the verdict (no full reply on stdout).

**New tests** (`tests/agents/test_119_5_subscription_isolation_smoke.py`, via an importlib loader): `_assess_reply` empty→refuse, clean(+generic words)→pass, contaminated→fail; `_detect_persona_tells` ignores generic tokens, flags repo markers. Pure helpers, no live SDK.

**Verified:** 39 passed + 1 skip (gated live) on the four story/sibling test files; ruff lint + format clean. Pushed as `b1195f18`. No new spec deviations.

**Handoff:** Back to Reviewer (Westley) for re-review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (1834 pass / 0 fail, lint+format clean, 0 blocking smells) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 (medium: empty-text false-OK) | confirmed 1, dismissed 0, deferred 0 |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings (self-checked: new tests non-vacuous) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings (self-checked: no stale comments) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (N/A — deletion + script, no new type surface) |
| 7 | reviewer-security | Yes | findings | 1 (low: info-leakage to CI logs) | confirmed 1, dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings (self-checked: net-deletion, noop dummy tool noted) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings (self-did Rule Compliance below — no python.md checklist exists) |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 3 confirmed (1 HIGH, 1 MEDIUM, 1 LOW), 0 dismissed, 0 deferred — all in the AC3 spike script.

## Reviewer Assessment

**Verdict:** REJECTED

The AC1 guard removal and AC2 atexit cleanup are clean and correct. All three findings live in the **AC3 spike script** (`scripts/spike_119_3_agentsdk_subscription.py`), whose entire purpose is *reliable* contamination detection — and its detection logic can both false-pass and false-fail.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH][SILENT] | The gated isolation smoke silently reports "OK: no contamination" (exit 0) when the probe reply is empty: `text = result.text or ""` then the tell-scan over `""` finds nothing. A verification tool that passes with **no signal** can't catch the regression it exists to catch — violates the `<critical>` No-Silent-Fallbacks doctrine AND the script's own docstring promise ("refuse loudly rather than green-lighting"). Plausible because the probe passes a `noop` tool, so the model can emit a tool-call and no prose. | `scripts/spike_119_3_agentsdk_subscription.py` — `_run_probe`, the `text = result.text or ""` → `leaked = [...]` path | Guard empty/blank text BEFORE the tell-scan: `if not text.strip(): print(...stderr); return 1`. Add a unit test (mock `AnthropicSdkClient.complete_with_tools` → empty `text`; assert `main()`/`_run_probe` returns non-zero). Consider dropping the `noop` tool (pass `tools=[]`) so the model must answer in prose. |
| [MEDIUM] | `_PERSONA_TELLS` mixes unambiguous repo markers (`Vizzini`, `Morpheus`, `Inigo Montoya`, `Pennyfarthing`, `SOUL.md`) with **generic tokens** — `orchestrator` and `Claude Code` — that a *clean*, isolated model could legitimately emit ("I'm Claude... I can help orchestrate your tasks"). A clean run then trips a false contamination → false exit 1 → operator chases a phantom regression. The smoke is unreliable in the false-alarm direction. | `scripts/spike_119_3_agentsdk_subscription.py` — `_PERSONA_TELLS` tuple | Restrict the tell-list to repo-specific, unambiguous markers (drop `orchestrator`, `Claude Code`). Add a test: a clean-ish reply containing a generic word must NOT be flagged; a reply with a real persona tell MUST be flagged. |
| [LOW][SEC] | The full model reply is printed unconditionally to stdout (`print(f"...probe reply: {text!r}")`); on a contaminated run the absorbed repo context propagates into CI logs via the test failure message (`test_119_5_subscription_isolation_smoke.py` interpolates `proc.stdout`). Low risk (gated, dev-only, private repo). | `scripts/spike_119_3_agentsdk_subscription.py` — the unconditional reply `print` | Print the full reply only on the contamination/error branches (stderr); keep stdout to the pass/fail verdict. Fold into the same rework — no separate test needed. |

### Rule Compliance

(reviewer-rule-checker disabled + no `.pennyfarthing/gates/lang-review/python.md` exists — enumerated against CLAUDE.md/SOUL.md myself.)

- **No Silent Fallbacks** (`<critical>`): VIOLATION — the spike's empty-text path silently green-lights (the [HIGH]). Elsewhere compliant: the guard removal is honest (the trap can't spring on the SDK path), `shutil.rmtree(ignore_errors=True)` is justified at the atexit boundary, the gate refuses loudly without its env.
- **No Stubbing**: compliant — the spike is a real probe through the production `AnthropicSdkClient`; no placeholder/skeleton.
- **Don't Reinvent / Wire Up What Exists**: compliant — atexit cleanup uses stdlib; the spike reuses `AnthropicSdkClient` + `build_agent_sdk_options`.
- **Verify Wiring, Not Just Existence**: compliant — `_cleanup_agent_sdk_cwd` is registered from the real `_neutral_cwd()` (prod call site `build_agent_sdk_options:254`); the atexit test invokes the captured callback and asserts the dir is gone.
- **Every Test Suite Needs a Wiring Test**: compliant — `test_build_does_not_raise_on_subfloor_prefix` drives real `build_intent_router_llm`; the AC3 subprocess test runs the real script.
- **No Source-Text Wiring Tests**: compliant — all new tests are behavioral/reflective (`hasattr`, build result, OTEL span capture, subprocess exit codes); no `read_text()` greps.
- **OTEL Observability**: compliant — the removed `intent_router.cache_floor` span observed a now-deleted subsystem; no remaining subsystem decision is left un-instrumented.
- **Subscription auth invariant** (ADR-101/119-3): compliant — the spike enforces both-creds-unset before any live call; `assert_subscription_auth()` still fires at `build_agent_sdk_options`.

### Observations

- [VERIFIED] AC1 guard fully removed — grep confirms zero references to `IntentRouterCacheFloorError` / `HAIKU_CACHEABLE_PREFIX_FLOOR_TOKENS` / `_INTENT_ROUTER_CACHE_TTL` / `_estimate_intent_router_prefix_tokens` / `_PREFIX_CHARS_PER_TOKEN` across `sidequest/`, `tests/`, `scripts/` (only the absence-assertion test's string literals remain). `llm_factory.py:611+` `build_intent_router_llm` now returns the adapter with no floor check; `json`/`logger` imports still used elsewhere (not orphaned).
- [VERIFIED] AC1 OTEL span machinery removed cleanly — `SPAN_INTENT_ROUTER_CACHE_FLOOR`, its `SPAN_ROUTES` entry, `intent_router_cache_floor_span`, and the module-docstring bullet are gone; `StatusCode` import retained (still used at the decompose/failed spans). No consumer referenced the removed key.
- [VERIFIED] AC2 atexit wiring correct — `anthropic_sdk_client.py` registers `_cleanup_agent_sdk_cwd` exactly once inside `_neutral_cwd()`'s lazy-init guard; cleanup `rmtree(ignore_errors=True)` + resets the global. `shutil.rmtree` does not follow symlinks (CPython 3.8+), no TOCTOU in this threat model (only `_neutral_cwd` writes the global, via `mkdtemp`).
- [SILENT][HIGH] Empty-text false-OK in the spike (see severity table) — confirmed from reviewer-silent-failure-hunter; matches `<critical>` No-Silent-Fallbacks.
- [MEDIUM] Generic tokens in `_PERSONA_TELLS` cause false-positive contamination on clean runs (my own analysis / devil's advocate).
- [SEC][LOW] Unconditional reply print leaks contaminated context to CI logs — confirmed from reviewer-security.
- [TEST] (subagent disabled) Self-checked the three new test files: all assertions are behavioral and non-vacuous (symbol-absence parametrized, build-no-raise, span-absence, atexit register+invoke, subprocess exit/skip). Good.
- [DOC] (subagent disabled) Self-checked comments: Dev already corrected the stranded 92-2 AC7 docstring; `build_intent_router_llm`'s docstring now explains the 119-5 removal; no stale references remain.
- [TYPE] (subagent disabled) N/A — deletion + a CLI script; no new type surface.
- [SIMPLE] (subagent disabled) Net-deletion change; the only added complexity is the `noop` dummy tool in the spike, which the [HIGH] fix may remove.
- [RULE] (subagent disabled) See Rule Compliance above — one No-Silent-Fallbacks violation, rest compliant.

### Devil's Advocate

Assume the spike is broken. The probe builds a turn with a `noop` tool and `tool_dispatch=None`, then asks the model to identify itself. Three failure modes converge on the script's detection logic. **First**, the model is *handed a tool*: a model that decides to call `noop` (or hits the iteration cap calling it) can converge to a `ToolingResult` whose `.text` is empty. The script does `text = result.text or ""` and scans an empty string for tells — finds none — and prints "OK: no contamination", exit 0. The smoke just certified isolation while receiving zero evidence. That is the exact silent-green-light the script's own docstring swears off, and it is *more* likely precisely because a tool was offered. **Second**, in the opposite direction, the tell-list is too eager: `orchestrator` and `Claude Code` are words a perfectly isolated Claude emits in casual self-description ("I'm Claude Code… I can help orchestrate your work"). A clean run trips a false contamination, the script exits 1, and an operator burns an afternoon hunting a regression that never happened — eroding trust in the smoke until someone disables it, which is how safety nets die. **Third**, the diagnostic print is unconditional: a genuinely contaminated reply (containing CLAUDE.md persona text) lands verbatim in stdout, captured into the pytest failure message and shipped to CI logs. For a private repo that is low-stakes, but it is the wrong default for a tool whose job is to surface *contamination*. None of these touch production runtime — the AC1/AC2 changes are clean — but AC3's deliverable is a *detector*, and a detector that both false-passes and false-fails is not done. The fix for all three is small and local to one function; that is why this is a bounce, not a redesign.

## Subagent Results — Round 2 (re-review)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (1839 pass / 0 fail, lint+format clean; all R1 findings confirmed closed) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | clean | none (R1 HIGH empty-text resolved; no new silent failures) | confirmed 0, dismissed 0 |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings (self-checked: 5 new pure-helper tests non-vacuous) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings (self-checked: comments accurate) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (N/A) |
| 7 | reviewer-security | Yes | clean | none (R1 LOW info-leak resolved; importlib loader safe) | confirmed 0, dismissed 0 |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings (self-did Rule Compliance) |

**All received:** Yes (3 enabled re-ran on the reworked diff; 6 disabled via settings)
**Total findings:** 0 new; all 3 round-1 findings confirmed RESOLVED.

## Reviewer Assessment — Round 2 (re-review)

**Verdict:** APPROVED

The green rework resolved all three round-1 findings; both re-run subagents (silent-failure, security) plus preflight returned clean, and I confirmed each fix in the diff.

**Round-1 findings — resolution verified:**
- [SILENT][HIGH] empty-reply silent green-light → **RESOLVED**: `_assess_reply` returns 1 (prints `INCONCLUSIVE` to stderr) on empty/whitespace text before the tell-scan; `_run_probe` routes `result.text or ""` through it. Pinned by `test_assess_reply_empty_is_refusal`.
- [MEDIUM] tell-list false positives → **RESOLVED**: generic tokens (`orchestrator`, `Claude Code`, `Scrum Master`) dropped; `_PERSONA_TELLS` is now repo-specific. Pinned by `test_detect_persona_tells_ignores_generic_tokens` + `test_assess_reply_clean_reply_passes`.
- [SEC][LOW] CI-log leak → **RESOLVED**: the full reply is echoed only on the empty/contaminated stderr branches; the clean path prints just the verdict. Pinned by `test_assess_reply_clean_reply_passes` (`clean not in out`).

**Dispatch tags (round 2):**
- [SILENT] reviewer-silent-failure-hunter: clean — empty-text fix verified, no new swallowed errors.
- [SEC] reviewer-security: clean — info-leak fixed, importlib `exec_module` safe (`main()` under `if __name__ == "__main__"`, SDK imports function-level), cred order + atexit rmtree safe.
- [EDGE]/[TEST]/[DOC]/[TYPE]/[SIMPLE]/[RULE]: subagents disabled via settings; self-assessed — the 5 new pure-helper tests are behavioral/non-vacuous; comments accurate; no new type/complexity/rule issues (the `noop` dummy tool was kept deliberately, with the empty-text guard covering its tool-call-only path).

**Residual (accepted, non-blocking):** [LOW] `_PERSONA_TELLS` retains theme-dependent persona names (`Morpheus`, `Buttercup`) that are common words; a clean self-ID reply emitting one is very unlikely and self-diagnosing (the contaminated branch prints the full reply for the operator to adjudicate). The unambiguous anchors (`Pennyfarthing`, `SideQuest`, `SOUL.md`, `genre pack`) carry the real signal. Acceptable for a gated, opt-in dev smoke.

**Data flow traced:** live probe reply → `result.text or ""` → `_assess_reply` (empty-guard → tell-scan) → exit 0/1. Safe: no path reports a pass without a non-empty, tell-free reply.
**Pattern observed:** pure detection helpers extracted from the impure live call — `scripts/spike_119_3_agentsdk_subscription.py` `_detect_persona_tells`/`_assess_reply` — the canonical "test the pure core, gate the impure shell" shape.
**Error handling:** empty/contaminated → loud non-zero with stderr diagnostics; gate/cred refusals fire before any network; top-level `except` converts any probe failure to exit 1.

**Round-2 deviation audit:** the rework introduced no new spec deviations (the round-1 deviations remain ACCEPTED).

**Handoff:** To SM (Vizzini) for finish-story.