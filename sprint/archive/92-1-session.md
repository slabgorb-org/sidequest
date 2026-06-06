---
story_id: "92-1"
jira_key: ""
epic: "92"
workflow: "tdd"
---

# Story 92-1: A/B eval: Haiku vs local qwen on real captured Intent Router corpus (48-4 harness; acceptance threshold on DispatchPackage classification agreement + latency budget)

## Story Details
- **ID:** 92-1
- **Jira Key:** N/A (no Jira)
- **Workflow:** tdd
- **Stack Parent:** none
- **Repos:** sidequest-server
- **Branch Strategy:** gitflow (feat/92-1-ab-eval-haiku-qwen-intent-router)
- **Branch Created:** 2026-06-05

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-06T00:50:55Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-05 | 2026-06-06T00:09:32Z | 24h 9m |
| red | 2026-06-06T00:09:32Z | 2026-06-06T00:21:16Z | 11m 44s |
| green | 2026-06-06T00:21:16Z | 2026-06-06T00:34:33Z | 13m 17s |
| review | 2026-06-06T00:34:33Z | 2026-06-06T00:39:16Z | 4m 43s |
| red | 2026-06-06T00:39:16Z | 2026-06-06T00:42:03Z | 2m 47s |
| green | 2026-06-06T00:42:03Z | 2026-06-06T00:47:01Z | 4m 58s |
| review | 2026-06-06T00:47:01Z | 2026-06-06T00:50:55Z | 3m 54s |
| finish | 2026-06-06T00:50:55Z | - | - |

> **Note (Dev):** the `92-1-dev-green-full` testing-runner invocation clobbered this
> session file with its run report (known failure mode — memory
> `feedback_testing_runner_clobbers_session`). Reconstructed verbatim from the
> in-context copies of the SM/TEA edits plus the phase-history update.

## Sm Assessment

Setup complete for 92-1 (3pt, p1, tdd, chore). Session file created at `.session/92-1-session.md`, story status `in_progress`, feature branch `feat/92-1-ab-eval-haiku-qwen-intent-router` created and checked out in sidequest-server. Story context exists at `sprint/context/context-story-92-1.md` (pulled from origin, authored with epic 92 planning); epic context at `sprint/context/context-epic-92.md`. Jira intentionally skipped — project policy (no Jira on SideQuest). Repos: sidequest-server only. Routing to TEA (Radar O'Reilly) for RED phase.

## TEA Assessment

**Tests Required:** Yes
**Reason:** chore-typed but the deliverable is net-new measured code (corpus schema, harness extension, scoring, CLI) — full TDD, no chore bypass.

**Test Files:**
- `sidequest-server/tests/corpus/test_router_corpus.py` — 9 tests: `RouterCapture` row schema ((action, state_summary) → baseline `DispatchPackage` triple, extra=forbid, empty-action rejection, JSON roundtrip), atomic JSONL `write_captures`/fail-loud `read_captures`, save-path overwrite guard.
- `sidequest-server/tests/agents/test_router_ab_eval_harness.py` — 38 tests: production call-shape wiring (emit_dispatch_package tool name, DispatchPackage schema, `<game_state>`/`<raw_action>` envelope, production `_SYSTEM_PROMPT`), `RouterCorpusCapturer`, dispatch-selection agreement (incl. confrontation-type strictness + no-dispatch-agrees), per-type agreement breakdown (not averaged away), qwen schema-validity rate, nearest-rank latency percentiles, AC4 adjudication (haiku_wrong/both_defensible count FOR qwen), go/no-go gate (agreement threshold + p95 budget + schema-validity floor), per-side failure isolation vs OllamaClientError infra propagation, CLI exit-code taxonomy + operator note, CI-safety AST scan, wiring tests.

**Tests Written:** 47 tests covering 5 ACs (AC1 corpus, AC2 identical-prompts/production-path/determinism, AC3 report, AC4 adjudication, AC5 go/no-go)
**Status:** RED (both files fail at collection: `ModuleNotFoundError: sidequest.corpus.router_corpus`, `ImportError: RouterAbEvalHarness` — verified by testing-runner, correct RED, no syntax errors)
**Commit:** `d9d08111` on `feat/92-1-ab-eval-haiku-qwen-intent-router` (sidequest-server)

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #1 silent exceptions | `test_qwen_schema_invalid_recorded_not_swallowed` | failing (RED) |
| #2 mutable defaults | `test_rule2_no_mutable_default_args`, `test_rule2_result_error_lists_isolated` | failing (RED) |
| #3 boundary annotations | `test_rule3_public_api_fully_annotated` | failing (RED) |
| #5 path handling | `test_write_captures_refuses_save_paths`, encoding-explicit roundtrips | failing (RED) |
| #8 unsafe deserialization | `test_read_captures_rejects_malformed_line`, `test_read_captures_rejects_wrong_shape_line`, `test_cli_malformed_corpus_line_is_config_error` | failing (RED) |
| #9 async pitfalls | `test_rule9_one_side_failure_preserves_other`, `test_ollama_unreachable_propagates_not_recorded` | failing (RED) |
| #11 input validation | `test_router_capture_rejects_empty_action`, `test_latency_percentiles_empty_rejected`, `test_cli_bad_sample_size_is_config_error` | failing (RED) |

**Rules checked:** 7 of 7 applicable lang-review rules have test coverage (#4 logging, #6 test-quality, #10 tenant-context N/A to this surface; self-check below covers #6)
**Self-check:** 0 vacuous tests — every test asserts a concrete value/exception; no `assert True`, no `let _`-equivalents.

**Key design pins for Dev (Major Winchester):**
- **Extend `ab_eval_harness.py`, do not fork** (story guardrail — wiring test enforces module location).
- The harness must drive the **production `IntentRouter.decompose`** path (wiring test pins the exact emit_tool kwargs incl. `intent_router._SYSTEM_PROMPT` identity).
- `OllamaClientError` **propagates** (infra ≠ bad output — exit-4 CLI no-op); `IntentRouterFailure` after bounded retry is **recorded per-side**. Note: `IntentRouter.decompose` currently catches generic exceptions as "transport" — Dev needs the qwen-side adapter/wrapper to let `OllamaClientError` escape (suggested: re-raise from the adapter before/around decompose).
- The 92-2 gate artifact is `report.go_no_go(agreement_threshold_pct, p95_budget_ms, schema_validity_floor_pct)` → `.go`/`.reasons`, evaluated on **adjudicated** agreement via `adjudicated_agreement_pct`.

**Handoff:** To Dev for implementation (GREEN)

## TEA Assessment — Round-Trip 1 (rework RED)

**Tests Required:** Yes
**Reason:** Reviewer [HIGH] — `RouterCorpusCapturer` unwired (no non-test consumer); the AC1 corpus cannot be produced by an operator.

**Test Files:**
- `sidequest-server/tests/agents/test_router_ab_eval_harness.py` — +4 tests (commit `cd4cfe73`): `test_cli_capture_mode_end_to_end_with_real_capturer` (REAL capturer driven through `cli.main(["--capture", ...])` with only the Haiku factory substituted; output re-read via `read_captures`, baseline from the router call, state_summary serialized), `test_cli_capture_missing_prompts_file_is_config_error`, `test_cli_capture_malformed_prompt_row_is_config_error` (rule #8/#11 — no silently skipped rows), `test_cli_capture_backend_failure_is_loud` (non-zero exit + NO partial corpus file — atomic writer).
- Prompt-row contract pinned: JSONL of `{"action", "state_summary" (str|object), "genre", "world", "round_number", "source_save", "event_seq" (optional)}`.

**Status:** RED verified — 4 fail (`SystemExit: 2`, `--capture` flag unknown), remaining 39 harness tests still green (baseline intact).
**Reviewer [MEDIUM] (nondeterminism characterization):** deferred to the operator artifact per the Reviewer's own allowance ("may be satisfied in the operator artifact rather than code; record which") — Dev must note the run-twice/diff procedure in the CLI module docstring or the go/no-go artifact. No CI test pins it.
**Reviewer [LOW]s:** optional, not test-pinned this round.

**Handoff:** To Dev (Major Winchester) for GREEN — implement `--capture` mode wiring `RouterCorpusCapturer` → `write_captures` in `scripts/router_ab_eval_cli.py`.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/corpus/router_corpus.py` (new) — `RouterCapture` row ((action, state_summary) → Haiku-baseline `DispatchPackage`), atomic JSONL `write_captures` with save-overwrite refusal, fail-loud `read_captures` (malformed line raises with file:line context).
- `sidequest/agents/ab_eval_harness.py` (+~490 lines) — router layer extending the 48-4 module: `RouterCorpusCapturer` and `RouterAbEvalHarness` both drive the production `IntentRouter.decompose`; `dispatch_selection_agreement` (subsystem-key sets + confrontation-type sets); `TypeAgreement` per-type tallies; `latency_percentiles` (nearest-rank); `RouterAdjudication` + `RouterAbEvalReport.adjudicated_agreement_pct`; `go_no_go` gate verdict (`RouterGoNoGo`); `QwenRouterLlm` measurement-only prompt-coerced-JSON adapter; `_InfraSensingLlm` wrapper so `OllamaClientError` escapes the router's transport-retry fold (TEA's pin) while `IntentRouterFailure` is recorded per-side.
- `scripts/router_ab_eval_cli.py` (new) — operator CLI: `--corpus-jsonl/--sample-size/--output-md/--qwen-model` + threshold flags; EXIT_PASS=0 / EXIT_CONFIG_ERROR=2 / EXIT_OLLAMA_UNREACHABLE=4 with operator note; appends the go/no-go verdict section when the report supports it; `_DeferredRouterLlm` defers backend construction to first call (corpus/arg validation needs no credentials; env checks still fail loud before any eval work).
- `tests/{game,server,telemetry}/test_lull_escalation*.py` — pre-existing I001 lint debt on develop (`ruff check .` failed); import blocks sorted (3 files, 1 line each).

**Tests:** 48/48 story tests passing; full suite 9883 passed / 0 failed / 1471 skipped (95.6s). `ruff check .` clean; `ruff format --check` clean on all touched files (repo-wide format drift of 162 untouched files is pre-existing and ungated).
**Branch:** feat/92-1-ab-eval-haiku-qwen-intent-router (pushed, commits `d9d08111` RED + `ec15bec4` GREEN)

**Handoff:** To Reviewer (Colonel Potter) for code review

## Dev Assessment — Round-Trip 1 (capture mode)

**Implementation Complete:** Yes
**Files Changed:**
- `scripts/router_ab_eval_cli.py` — `--capture` mode (commit `fd192a9d`): `_PromptRow` pydantic validation (extra=forbid, fail-loud per line via `_read_prompt_rows`), eager `build_intent_router_llm()` construction (credentials check fires before any API spend), real `RouterCorpusCapturer` drive per row, `write_captures` only after ALL rows succeed (no partial corpus — `EXIT_CAPTURE_ERROR=3` on backend failure), `main` split into `_run_capture`/`_run_eval`. Reviewer [MEDIUM] (AC2 nondeterminism characterization) addressed as the documented run-twice/diff operator procedure in the module docstring, per TEA's deferral note.

**Tests:** 52/52 story tests passing (4 new capture tests GREEN); full suite 9887 passed / 0 failed / 1471 skipped; `ruff check .` clean; formatted.
**Branch:** feat/92-1-ab-eval-haiku-qwen-intent-router (pushed: `cd4cfe73` RED + `fd192a9d` GREEN)
**Reviewer [LOW]s:** not taken this round (both explicitly optional; noted for 92-2's gate consumption).

**Handoff:** To Reviewer (Colonel Potter) for re-review

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Conflict** (non-blocking): sm-setup regenerated `sprint/context/context-story-92-1.md` and `context-epic-92.md` from sprint YAML, clobbering the rich authored contexts pulled from origin (200 lines → 31). Restored both via `git checkout --` before test design. Affects `pennyfarthing sm-setup context-creation step` (should skip when a valid context already exists). *Found by TEA during test design.*
- **Gap** (non-blocking): no production capture path persists the router's `(action, state_summary) → DispatchPackage` triples — OTEL decompose spans carry only summaries (`action_length`, 160-char `raw_preview`), and `corpus/miner.py` mines narrator pairs without `state_summary`. The RED suite pins the capture primitive (`RouterCorpusCapturer` driving the real `IntentRouter.decompose`); reconstructing `(action, state_summary)` rows from real saves is operator-layer work Dev must build or document. Affects `sidequest/corpus/router_corpus.py` (net-new) and `sidequest/agents/ab_eval_harness.py` (extension). *Found by TEA during test design.*
- **Question** (non-blocking): `OllamaClient` has no `emit_tool` and reports `supports_tools=False` (confirmed in code) — the qwen side needs a thin measurement-only `IntentRouterLLM` adapter (prompt-coerced JSON → `DispatchPackage.model_validate`). Tests treat the adapter as injectable (any `IntentRouterLLM`); Dev decides whether the thin adapter ships in this story (harness-side only per context) or waits for 92-2. Affects `sidequest/agents/ab_eval_harness.py` or `scripts/router_ab_eval_cli.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Conflict** (non-blocking): the `92-1-dev-green-full` testing-runner invocation clobbered `.session/92-1-session.md` with its run report (known failure mode, memory `feedback_testing_runner_clobbers_session`) — reconstructed from in-context copies. It also auto-fixed 3 unrelated lint-debt files without being asked; the fixes were verified legitimate (develop genuinely fails `ruff check .`) and kept deliberately. Affects `pennyfarthing testing-runner` (should never write the session file or edit source). *Found by Dev during implementation.*
- **Gap** (non-blocking): pre-existing lint debt on develop — `ruff check .` failed with 3× I001 in `tests/{game,server,telemetry}/test_lull_escalation*.py`, meaning `just server-check` was red on develop before this story. Fixed in this PR (1-line import-block sorts). Affects `sidequest-server develop lint gate` (something merged without the gate). *Found by Dev during implementation.*
- **Question** (non-blocking): the live corpus production run (N≥100 rows from real saves + live Haiku baselines, then the qwen A/B on the M3 Ultra) is operator evidence still to be executed — the instrument is built and wired, the evidence run is the remaining AC1/AC3 operator step. The 92-2 gate consumes the resulting report + adjudication. Affects `scripts/router_ab_eval_cli.py` (operator run + artifact commit location TBD). *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): `RouterCorpusCapturer` has no non-test consumer — the CLI evaluates a corpus but cannot create one, so the AC1 "tool to produce them deterministically" is unexecutable by an operator. Affects `scripts/router_ab_eval_cli.py` (add capture mode driving `RouterCorpusCapturer` → `write_captures`, with tests). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): adjudications are keyed by result index; across re-runs or re-ordered corpus files that identity is fragile — a future revision should key on a stable row identity (provenance). Affects `sidequest/agents/ab_eval_harness.py` (`adjudicated_agreement_pct` keying, fine for the frozen 92-1 artifact). *Found by Reviewer during code review.*
- **Question** (non-blocking): the corpus stores `state_summary` as an opaque serialized string; if 82-10 (router prompt slimming) changes the state-summary serialization, captured corpora silently measure a stale prompt shape — the operator artifact should record which serialization the corpus was captured under. Affects `sidequest/corpus/router_corpus.py` (doc note or future schema_version bump policy). *Found by Reviewer during code review.*

### TEA (rework round 1, test design)
- No new upstream findings during rework test design (the round's scope is the Reviewer's [HIGH]; prompt-row contract chosen to match the capturer's existing signature).

### Dev (rework round 1, implementation)
- No upstream findings during rework implementation.

### Reviewer (re-review, round-trip 1)
- No new upstream findings during re-review (two LOW style/polish notes recorded in the assessment, neither rises to a tracked finding).

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Confrontation `opponent` not pinned in the agreement metric** → ✓ ACCEPTED by Reviewer: agrees with author reasoning — opponent names are free text; AC4 adjudication is the right surface for opponent-level disputes. Noted as a LOW observation that set-level semantics also hide duplicate-dispatch count drift.
  - Spec source: context-story-92-1.md, Technical Guardrails / Measure #1
  - Spec text: "and the load-bearing `params` like confrontation `type`/`opponent`"
  - Implementation: `dispatch_selection_agreement` tests pin subsystem-set equality and confrontation `type` equality strictly; opponent identity is NOT asserted
  - Rationale: opponent names are model-phrased free text ("the goblin" vs "goblin chief") — strict string equality would manufacture false disagreements; fuzzy matching is a judgment call better made by Dev/adjudication (AC4's manual adjudication covers opponent-level disputes)
  - Severity: minor
  - Forward impact: if 92-2 wants opponent-level agreement in the gate, add a fuzzy-match metric then
- **Save-replay corpus extraction tested only via the capture primitive** → ✓ ACCEPTED by Reviewer (scope), BUT see [HIGH] finding: the CI/operator test split is sound, yet the capture primitive must still be *invocable by an operator* — today `RouterCorpusCapturer` has no non-test consumer, so the deviation's premise ("operator-evidence") is unexecutable. The finding, not this deviation, carries the fix.
  - Spec source: context-story-92-1.md, AC1 + "capture is likely the bulk of this story"
  - Spec text: "A corpus of N real DispatchPackage prompts is captured ... suggest ≥100, spanning the live dispatch types"
  - Implementation: tests pin `RouterCorpusCapturer` (production `decompose` → `RouterCapture`) and the JSONL schema/IO; the save→(action, state_summary) reconstruction and the N≥100 live corpus are operator-evidence, not CI-asserted
  - Rationale: the live corpus requires real saves + live Haiku calls (M3 Ultra), exactly the operator/CI split the story's TDD note prescribes (mirror of 48-4's exit-4 pattern)
  - Severity: minor
  - Forward impact: Dev documents the corpus-production run in the story artifact; 92-2's gate consumes the report, not CI
- **Latency percentile definition chosen by TEA** → ✓ ACCEPTED by Reviewer: nearest-rank is the right conservative choice; 92-2 must inherit the same definition.
  - Spec source: context-story-92-1.md, Measure #3
  - Spec text: "Latency distribution (p50/p95) — report percentiles, not just the harness's current average"
  - Implementation: tests pin nearest-rank percentiles (ceil(q·n)-th of sorted values), empty input raises ValueError
  - Rationale: the spec names no interpolation method; nearest-rank is deterministic, dependency-free, and conservative (never reports a latency nobody experienced)
  - Severity: minor
  - Forward impact: 92-2's p95 budget inherits the same definition — keep consistent

### Dev (implementation)
- **CLI backends constructed lazily (first emit_tool call), not at script load** → ✓ ACCEPTED by Reviewer: deferred fail-loud is not a silent fallback — env check still raises before any eval work (`scripts/router_ab_eval_cli.py:53-71`); module-top imports preserve the 48-4 fail-at-load doctrine for broken installs. Forward-impact note (92-2 must keep eager factory construction) is correct and load-bearing.
  - Spec source: context-story-92-1.md, TDD note + 48-4 AC5 precedent (`_IntentRouterLlm` "eagerly constructs so the build-time env check fires loudly")
  - Spec text: "the CI-safe unit layer stays fully mocked ... the live A/B is operator-evidence on the M3 Ultra, exactly as the 48-4 CLI already handles"
  - Implementation: `_DeferredRouterLlm` in the CLI defers `build_intent_router_llm()` / `QwenRouterLlm` construction to the first `emit_tool` call; module-top imports still fail loud on a broken install
  - Rationale: `build_intent_router_llm()` raises on missing ANTHROPIC_API_KEY at construction — eager construction would make corpus/argument validation (and the CI-safe CLI tests, which substitute the harness symbol only) require live credentials. Deferred fail-loud, not a fallback: the env check still raises before any eval work.
  - Severity: minor
  - Forward impact: 92-2's production local rung must keep eager fail-loud construction at the factory seam (this deviation is CLI-tooling-only)
- **Lull-escalation lint fixes folded into this PR** → ✓ ACCEPTED by Reviewer: develop's `ruff check .` genuinely fails without them (verified — 3× I001); 1-line cosmetic sorts, no behavior change, gate-unblocking.
  - Spec source: context-story-92-1.md, Scope Boundaries ("Out of scope: unrelated changes")
  - Spec text: "Out of scope: ... unrelated changes"
  - Implementation: 3 one-line I001 import-sort fixes in `tests/*lull_escalation*` files
  - Rationale: `ruff check .` (part of `just server-check`) fails on develop without them — the story's own quality gate cannot pass while they exist; fixing lint debt in-PR mirrors the delete-dead-code-in-same-PR doctrine
  - Severity: minor
  - Forward impact: none — cosmetic, no behavior change

### TEA (rework round 1, test design)
- **Capture-mode prompt rows are a flat JSONL contract, not a save-replay tool** → ✓ ACCEPTED by Reviewer (re-review): the flat-row contract is exactly what the [HIGH] required — an invocable operator surface; save→row extraction feeding the same contract later is the right layering.
  - Spec source: Reviewer Assessment [HIGH] + context-story-92-1.md In-Scope bullet 1
  - Spec text: "the schema + tool to produce them deterministically" / "rows from saves/OTEL"
  - Implementation: tests pin `--capture --prompts-jsonl` consuming flat `(action, state_summary, genre, world, round_number, source_save, event_seq)` rows; the save→prompt-row extraction itself remains operator-prepared input
  - Rationale: the [HIGH] is about the capturer having no invocable surface — the flat-row contract fixes exactly that; save-snapshot reconstruction is a separate engine-aware tool the Reviewer did not require this round (and TEA deviation #2's operator split stands ACCEPTED)
  - Severity: minor
  - Forward impact: if a future story automates save→prompt-row extraction, it feeds this same contract

### Dev (rework round 1, implementation)
- No deviations from spec (implementation matches the rework RED pins exactly; Reviewer [MEDIUM] handled via the docstring procedure TEA's deferral prescribed). → ✓ ACCEPTED by Reviewer (re-review): verified against the rework RED pins and the docstring procedure (run-twice/diff recorded in the go/no-go artifact).

### Reviewer (audit)
- All five logged deviations stamped above (5× ACCEPTED, one with a linked [HIGH] finding). No undocumented deviations found: the diff matches the story context's in-scope list except the capturer entry-point gap, which Dev DID document (delivery finding "live corpus production run ... still to be executed") but under-classified — it is a wiring violation, not just pending operator work. Recorded as the [HIGH] finding below rather than a new deviation entry.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (48/48 green, ruff clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (1 enabled returned clean; 8 disabled via `workflow.reviewer_subagents` settings — their domains were reviewed manually below)
**Total findings:** 4 confirmed, 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** REJECTED

Since 8 specialists are disabled, the domain coverage below is my own line-level analysis (tags mark the domain each observation belongs to): [EDGE] [SILENT] [TEST] [DOC] [TYPE] [SEC] [SIMPLE] [RULE].

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] [RULE] | `RouterCorpusCapturer` has **zero non-test consumers** (verified by grep: only `ab_eval_harness.py:637` definition + test imports). CLAUDE.md: "Verify Wiring, Not Just Existence — check that new code has non-test consumers" and "No half-wired features — connect the full pipeline or don't start." Story context In-Scope bullet 1 requires "the schema + **tool** to produce them deterministically" — a class with no invocable surface is not a tool; the AC1 corpus cannot be produced by an operator without a Python REPL. | `sidequest/agents/ab_eval_harness.py:637`, `scripts/router_ab_eval_cli.py` | Add a capture mode to the CLI (e.g. `--capture --prompts-jsonl <(action,state_summary) rows> --out <corpus.jsonl>`) that drives `RouterCorpusCapturer` → `write_captures`, with CI-safe tests (monkeypatch the capturer/llm symbol, config-error cases). This wires the capturer and makes AC1 executable. |
| [MEDIUM] [EDGE] | AC2's parenthetical — "re-running yields the same report modulo backend nondeterminism (**and that nondeterminism is itself characterized, not hidden**)" — has no instrument support: nothing measures cross-run drift. | `sidequest/agents/ab_eval_harness.py:739` (harness), CLI | Non-blocking for the rework round: either a `--repeat N` CLI flag reporting agreement-pct spread, or an explicit documented operator procedure (run twice, diff reports) in the go/no-go artifact. May be satisfied in the operator artifact rather than code; record which. |
| [LOW] [EDGE] | `adjudicated_agreement_pct` silently ignores adjudication keys that don't index a result (`adjudications.get(i)` — a typo'd index is a no-op). Borderline against fail-loud doctrine for an operator-input surface. | `sidequest/agents/ab_eval_harness.py:541` | Optional: validate `adjudications.keys() ⊆ range(len(results))` and raise on unknown indices. |
| [LOW] [TYPE] | `dispatch_selection_agreement` uses **set** semantics — two confrontation dispatches vs one, same type, reads as agreement. Multiset drift is invisible to the gate metric. | `sidequest/agents/ab_eval_harness.py:446` | Optional now; note in the report artifact. If real corpora show duplicate same-subsystem dispatches, upgrade to multiset comparison in 92-2's gate consumption. |

### Rule Compliance (lang-review/python.md, rule-by-rule over the diff)

- **#1 silent exceptions — COMPLIANT.** `read_captures` catches broadly but re-raises `ValueError` with file:line context (`router_corpus.py:88-104`); `_run_side` catches only `IntentRouterFailure`, re-raises infra via `sensor.infra_error` (`ab_eval_harness.py:766-782`); CLI catches `OllamaClientError`/`LlmClientError` specifically with messages and distinct exit codes (`router_ab_eval_cli.py:124-130`); `write_captures` `except BaseException` cleans tmp then re-raises (`router_corpus.py:83-85`).
- **#2 mutable defaults — COMPLIANT.** All result/report list/dict fields use `field(default_factory=...)`; enforced by `test_rule2_*` (both isolation and signature scans).
- **#3 boundary annotations — COMPLIANT.** Public API fully annotated; enforced by `test_rule3_public_api_fully_annotated`.
- **#4 logging — COMPLIANT.** Per-side invalid logged at info (`ab_eval_harness.py` `router_ab_eval.%s_invalid`); error paths raise rather than log-and-continue; no sensitive data logged; lazy `%s` formatting used.
- **#5 path handling — COMPLIANT.** `pathlib` throughout; every `open`/`read_text`/`write_text` passes `encoding="utf-8"`; `_refuse_save_overwrite` resolves before the containment check (`router_corpus.py:57-68`).
- **#6 test quality — COMPLIANT.** 47 tests, no vacuous assertions (TEA self-check + my spot-read of the per-type, adjudication, and go/no-go tests — each asserts concrete values).
- **#8 unsafe deserialization — COMPLIANT.** Untrusted model output → `DispatchPackage.model_validate` (extra=forbid) inside the production router; corpus lines → `model_validate_json` with loud per-line failure; qwen completion → `_extract_json_object` raises on garbage (`ab_eval_harness.py:723-736`).
- **#9 async pitfalls — COMPLIANT.** Sequential awaits in `eval_capture` (no bare-gather cancellation hazard); per-side isolation + infra propagation tested (`test_rule9_one_side_failure_preserves_other`, `test_ollama_unreachable_propagates_not_recorded`).
- **#11 input validation — COMPLIANT.** Empty corpus raises (`eval_corpus`), empty percentiles raise, CLI validates sample-size/missing-file/malformed-corpus to `EXIT_CONFIG_ERROR`.
- **#10 tenant context — N/A** (no tenant surface in this tooling). **#7 — N/A** (no matching surface in diff).

### Observations (beyond the findings table)

1. **[VERIFIED] [RULE] Production call-shape wiring** — `RouterAbEvalHarness._run_side` and `RouterCorpusCapturer.capture` both construct the real `IntentRouter` (`ab_eval_harness.py:768`, `:662`) and the wiring test pins `emit_tool` kwargs to `tool_name="emit_dispatch_package"`, `tool_schema == DispatchPackage.model_json_schema()`, and the production `_SYSTEM_PROMPT` identity (`tests/agents/test_router_ab_eval_harness.py::test_eval_capture_drives_real_router_call_shape`). Complies with the story guardrail (measure the production path) and the no-source-grep wiring-test rule (fixture-driven, not read_text).
2. **[VERIFIED] [SILENT] Infra vs bad-output separation** — `_InfraSensingLlm` (`ab_eval_harness.py:454`) records `OllamaClientError` and `_run_side` re-raises it `from exc` out of the per-side fold; a daemon outage can never masquerade as a low schema-validity rate and poison the gate metric. Evidence: `test_ollama_unreachable_propagates_not_recorded` + `:766-775`.
3. **[VERIFIED] [SEC] No injection/secret surface** — corpus paths guarded against save-root overwrite (`router_corpus.py:57`), no shell interpolation, no secrets in code; the only env secret (ANTHROPIC_API_KEY) is read by the existing factory, never logged. CLI prints exception text to an operator terminal only.
4. **[VERIFIED] [TEST] Data flow traced end-to-end** — a `RouterCapture` row: JSONL line → `read_captures` validation → `eval_capture` → production `decompose` prompt build (`<game_state>` carries `state_summary` verbatim since it is stored as the serialized string) → both backends → `dispatch_selection_agreement` → report tallies → `go_no_go`. Each hop validates or raises; no silent coercion. The determinism test (`test_eval_corpus_deterministic_rerun`) pins stable aggregation.
5. **[VERIFIED] [SIMPLE] No over-engineering** — the router layer reuses the 48-4 module (guardrail), `TrainingPair` machinery untouched, no speculative abstractions; `QwenRouterLlm` is the thin measurement-only adapter the story context explicitly sanctions ("keep it in the harness, not the live router"), and 92-2 owns the production adapter.
6. **[DOC] Comments accurate** — module docstrings state the 92-1 scope split and the `_DeferredRouterLlm` doctrine correctly; no stale references found in the diff (the 48-4 docstring at module top still describes only the narration layer — acceptable, the §92-1 banner comment marks the extension boundary).

### Devil's Advocate

Argue this code is broken. First, the strongest case: **the story's product is evidence, and the instrument cannot gather it.** An operator sitting at the M3 Ultra tonight has a CLI that *evaluates* a corpus but no way to *create* one — `RouterCorpusCapturer` is reachable only from pytest. They would have to hand-write a Python snippet importing a class from a harness module, constructing `MineProvenance` by hand. That is exactly the "fully implemented but not wired" pattern CLAUDE.md names, and it blocks AC1 — hence the HIGH. Second: suppose qwen reliably emits *two* JSON objects (chat models love trailing commentary); `_extract_json_object` slices first-`{` to last-`}` and `json.loads` fails → recorded invalid. Good — but a model emitting `{"…"} extra prose` *without* a second brace parses fine; trailing prose is silently tolerated. Acceptable (we validate the parsed object strictly), but worth knowing. Third: latency. `_run_side` times the whole `decompose`, including a schema-correction retry — so qwen's p95 absorbs double-round-trips on flaky outputs. Is that dishonest? No — it is the *true* per-turn cost the live path would pay, and the schema-validity metric exposes the cause separately. Fourth: the corpus stores `state_summary` as an opaque string; if 82-10 (router prompt slimming) changes the serialization, old corpora silently measure a *stale* prompt shape. The `schema_version` field exists but nothing ties it to the serialization contract — record in the operator artifact which serialization version the corpus was captured under. Fifth: `adjudications` keyed by integer index is fragile across re-runs if the corpus file is re-ordered — adjudication should reference a stable row identity (provenance) eventually; for the 92-1 artifact, indices over a frozen corpus file are tolerable. None of these overturn the architecture; the first one alone forces the rework round.

**Data flow traced:** corpus JSONL → `read_captures` (validated) → production `IntentRouter.decompose` on both backends → `dispatch_selection_agreement`/validity/latency tallies → `RouterAbEvalReport.go_no_go` (safe because every hop fails loud; no silent coercion anywhere).
**Pattern observed:** good — operator-evidence/CI split with `EXIT_OLLAMA_UNREACHABLE` no-op faithfully mirrors 48-4 (`scripts/router_ab_eval_cli.py:42,124-127`).
**Error handling:** verified per Rule Compliance #1/#8/#11 above.

**Handoff:** Back to TEA (Radar) → Dev (Winchester) for the rework round: wire `RouterCorpusCapturer` into a CLI capture mode with tests ([HIGH]); address or explicitly defer the [MEDIUM] nondeterminism characterization; [LOW]s optional.

## Subagent Results — Re-Review (Round-Trip 1)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 2 (1 MEDIUM, 1 LOW) | confirmed 0, dismissed 1, deferred 0; 1 LOW noted |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (1 enabled returned; 8 disabled via settings — delta reviewed manually)
**Total findings:** 0 confirmed blocking, 1 dismissed (with line evidence), 2 LOW noted

## Reviewer Assessment — Re-Review (Round-Trip 1)

**Verdict:** APPROVED

Scope: the rework delta (`cd4cfe73` RED tests + `fd192a9d` capture mode; 2 files, +246/−14). Manual coverage of the disabled specialists' domains on the delta: [EDGE] [SILENT] [TEST] [DOC] [TYPE] [SEC] [SIMPLE] [RULE].

**Prior findings disposition:**
- **[HIGH] capturer unwired → RESOLVED.** `RouterCorpusCapturer` imported at CLI module top (`scripts/router_ab_eval_cli.py:54-59`) and consumed by `_run_capture` (`:168`); reachable via `--capture` (`:277`). The end-to-end wiring test drives `cli.main(["--capture", ...])` through the REAL capturer with only the Haiku factory substituted, then re-reads the output via `read_captures` — existence AND wiring proven.
- **[MEDIUM] nondeterminism characterization → RESOLVED** as the documented run-twice/diff operator procedure in the module docstring (`:19-23`), within the allowance I gave ("may be satisfied in the operator artifact rather than code; record which"). The go/no-go artifact must record the spread.
- **[LOW]×2 → explicitly not taken**, as permitted (optional).

**Preflight [MEDIUM] DISMISSED (Challenged with line evidence):** preflight claimed `test_cli_capture_backend_failure_is_loud`'s `RuntimeError` escapes uncaught and the test "passes for the wrong reason." Refuted: the production `IntentRouter.decompose` catches every emit_tool exception as a transport failure (`sidequest/agents/intent_router.py:368`), retries, and raises `IntentRouterFailure` (`:427`), which `_run_capture` catches (`router_ab_eval_cli.py:190`) → clean operator message + `EXIT_CAPTURE_ERROR=3`, no traceback. Empirically re-verified: the single test passes with the rc comparison executing (an escaped exception would error the test, not pass it). The test injecting `RuntimeError` is in fact STRONGER than injecting `IntentRouterFailure` — it exercises the production wrap.

**[LOW] noted (non-blocking, for a future tidy):**
1. [SIMPLE] `_write_prompt_rows` test helper re-imports `json as _json` inside the function (module already imports json at top) — style only.
2. [EDGE] an `--out` path tripping `write_captures`' save-root guard surfaces as a raw `ValueError` traceback rather than a clean config error — fail-loud either way; clean catch optional.

**Rule compliance (delta):** #1 ✓ (`_read_prompt_rows` re-raises with file:line; `_run_capture` catches the two production failure types, prints, distinct exit code), #2/#3 ✓ (pydantic `_PromptRow`, annotated), #5 ✓ (pathlib + encoding), #8/#11 ✓ (extra=forbid row validation; missing/empty/malformed → `EXIT_CONFIG_ERROR`; exit codes 0/2/3/4 distinct), #9 ✓ (single `asyncio.run`, sequential capture — partial-corpus impossible by construction: `write_captures` runs only after every row succeeds, and is itself atomic).

**Data flow traced (capture):** prompt-row JSONL → `_PromptRow.model_validate` (forbid) → production `decompose` → validated `DispatchPackage` → `RouterCapture` → atomic `write_captures`; every hop fails loud.
**Pattern observed:** good — eager Haiku construction in capture mode (`:168`) honors the 48-4 fail-before-spend doctrine while eval mode keeps the deferred variant; both documented.
**Error handling:** verified above; crash-with-traceback reserved for genuine programming errors only.

**Handoff:** To SM (Hawkeye) for finish — PR creation + merge + ceremony.