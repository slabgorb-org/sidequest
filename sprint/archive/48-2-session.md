---
story_id: "48-2"
jira_key: ""
epic: "48"
workflow: "tdd"
---
# Story 48-2: Validate SIDEQUEST_LLM_BACKEND=ollama end-to-end + audit OllamaClient num_ctx pattern

## Story Details
- **ID:** 48-2
- **Jira Key:** (none — SideQuest does not use Jira)
- **Workflow:** tdd (5 phases: setup → red → green → review → finish)
- **Epic:** 48 (Local-LLM Workstream — Inference, Fine-Tune, and Evaluation)
- **Stack Parent:** none (independent story)
- **Points:** 3
- **Type:** chore

## Acceptance Criteria
1. **AC1:** One full playtest turn through the Ollama backend completes
2. **AC2:** OTEL span confirms `agent.backend="ollama"`
3. **AC3:** Latency budget within 3x of Claude baseline
4. **AC4:** OllamaClient num_ctx pattern reviewed; fixed via Modelfile load-time config if per-request pattern is present

## Story Context

**Dependency:** 48-1 (completed 2026-05-06)
- Ollama 0.23.1 installed locally on M3 Ultra (Mac Studio)
- qwen2.5:7b-instruct and qwen3-coder:30b models loaded
- Review finding: Ollama defaults to model's native context (262144 for qwen3-coder)
- Per-request num_ctx override forces KV cache reload (~28s/call observed)
- **Action for this story:** Audit OllamaClient for same per-request pattern; fix via Modelfile load-time config if present

**Spec:**
- docs/superpowers/specs/2026-05-06-local-qwen-code-editor-design.md
- docs/superpowers/specs/2026-05-06-local-qwen-code-editor-as-installed.md

**Key findings from 48-1 review:**
- Ollama 0.23.x built-in Claude integration can route Claude Code itself to local Ollama-hosted model
- qwen-code CLI uses `http://localhost:11434/v1` with contextWindowSize 262144
- No per-request num_ctx override in final config

**Validation scope (AC1-AC3):**
- Full playtest turn with SIDEQUEST_LLM_BACKEND=ollama env var set
- Narrator and decomposer round-trips must complete
- OTEL spans must tag with agent.backend="ollama"
- Latency must be ≤3x Claude baseline (narrator typically ~5-8s on Claude, so target ≤15-24s on Ollama/Qwen7B)
- Degraded-response paths (simulated Ollama errors) must fire correctly

**Audit scope (AC4):**
- Review sidequest-server/sidequest/agents/ollama_client.py
- Search for per-request num_ctx in OpenAI-compat options
- If found: fix via Modelfile load-time config instead
- May result in separate PR if fix is needed

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-05-12T20:04:50Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-12 | 2026-05-12T19:11:30Z | 19h 11m |
| red | 2026-05-12T19:11:30Z | 2026-05-12T19:17:46Z | 6m 16s |
| green | 2026-05-12T19:17:46Z | 2026-05-12T19:22:14Z | 4m 28s |
| spec-check | 2026-05-12T19:22:14Z | 2026-05-12T19:23:29Z | 1m 15s |
| verify | 2026-05-12T19:23:29Z | 2026-05-12T19:30:16Z | 6m 47s |
| review | 2026-05-12T19:30:16Z | 2026-05-12T19:39:27Z | 9m 11s |
| red | 2026-05-12T19:39:27Z | 2026-05-12T19:45:14Z | 5m 47s |
| green | 2026-05-12T19:45:14Z | 2026-05-12T19:49:22Z | 4m 8s |
| spec-check | 2026-05-12T19:49:22Z | 2026-05-12T19:51:15Z | 1m 53s |
| verify | 2026-05-12T19:51:15Z | 2026-05-12T19:53:50Z | 2m 35s |
| review | 2026-05-12T19:53:50Z | 2026-05-12T20:03:02Z | 9m 12s |
| spec-reconcile | 2026-05-12T20:03:02Z | 2026-05-12T20:04:50Z | 1m 48s |
| finish | 2026-05-12T20:04:50Z | - | - |

## Sm Assessment

**Workflow choice:** tdd — story has well-defined acceptance criteria with both behavioral (full Ollama turn, OTEL backend tag, latency budget) and structural (OllamaClient num_ctx audit) outcomes. 3 points fits comfortably in tdd's five-phase cadence; the audit half is amenable to a focused test-first sweep over `OllamaClient` call sites.

**Repos:** server only. Single-repo scope — `sidequest-server/sidequest/agents/ollama_client.py` is the audit target; OTEL plumbing and degraded-path tests also land in server.

**Branch:** `feat/48-2-validate-ollama-backend-e2e` created in `sidequest-server/` against `develop`. Orchestrator stays on the existing branch.

**Open questions for TEA / Dev:**
- AC1's "full playtest turn" — TEA decides whether this is best modeled as an automated integration test (preferred, with Ollama mocked or running in CI) or whether AC1 is a manual playtest checkbox plus narrower unit-level integration coverage.
- AC3 latency budget vs Claude baseline — needs a measured Claude baseline number to compare against. If no recent measurement exists, TEA may want to defer AC3 to a manual check or capture a baseline as part of RED.
- AC4 audit may discover the fix isn't needed (no per-request `num_ctx` pattern present). If found and fixed, follow the story's "separate PR if needed" guidance.

**Risk:** Real Ollama dependency in tests. Prefer fake/mocked OllamaClient backend at the boundary; reserve real-Ollama validation for a single end-to-end smoke. Memory note: stale venv shebangs across clones — if `ModuleNotFoundError` shows up during test runs, check `.venv/bin/` shebang per `feedback_stale_venv_shebangs.md`.

**No Jira.** Per project memory, SideQuest does not use Jira. All `pf sprint` invocations must omit `--jira`.

## TEA Assessment

**Phase:** finish
**Tests Required:** Yes — validation story still needs regression guards + Dev-deliverable RED items
**Status:** RED (15 tests; 13 pinning current behavior, 2 failing to drive Dev work)

### What Is RED (Dev must make GREEN)

1. **`test_ac3_latency_comparison_script_exists_and_is_invocable`** — fails because `sidequest-server/scripts/ollama_latency_check.py` (or `scripts/ollama_latency_check.py`) does not yet exist. Required behavior: invokable with `--help` (exit 0), help text mentions "latency". Script body should compare an Ollama-backend call against a recorded Claude baseline and report ≤3x budget pass/fail. AC3.

2. **`test_ac4_audit_outcome_documented_in_as_installed_spec`** — fails because `docs/superpowers/specs/2026-05-06-local-qwen-code-editor-as-installed.md` does not yet reference story 48-2. Required: the doc must contain the string `48-2`, mention `OllamaClient`, and include an audit conclusion phrase (any of: "no per-request", "no num_ctx", "audit conclusion", "audit outcome", "audit complete"). The existing line 60 follow-up note is the natural place to extend — turn the prospective note into a concluded one. AC4.

### What Is Already Green (regression guards / wiring pins)

| AC | Tests | Why Already Green |
|----|-------|-------------------|
| AC1 | `test_ac1_factory_ollama_send_stateless_roundtrips_end_to_end`, `test_ac1_factory_ollama_send_with_session_supports_multi_turn`, `test_ac1_factory_default_ollama_url_when_env_unset` | Factory + `OllamaClient` already implemented (48-1). Tests pin the wiring; manual playtest still required for the live end-to-end. |
| AC2 | `test_ac2_send_with_model_emits_agent_call_span_with_backend_ollama`, `test_ac2_send_with_session_emits_session_span_with_backend_ollama`, `test_ac2_send_stateless_emits_session_span_with_backend_ollama`, `test_ac2_factory_built_client_spans_tag_agent_backend_ollama` | `OllamaClient` already passes `backend="ollama"` to `agent_call_span` / `agent_call_session_span`. Tests pin the GM-panel "lie detector" attribute. |
| AC3 | `test_ac3_span_records_request_duration_observable_via_otel` | OTEL Span context manager records start/end times. Test asserts duration ≥ simulated network delay. |
| AC4 | `test_ac4_send_with_model_request_body_has_no_num_ctx_anywhere`, `test_ac4_send_with_session_request_body_has_no_num_ctx_anywhere`, `test_ac4_send_stateless_request_body_has_no_num_ctx_anywhere`, `test_ac4_ollama_client_source_has_no_num_ctx_reference` | Audit conclusion: `OllamaClient` currently sends `{"model", "prompt"/"messages", "stream"}` only — no `options.num_ctx`. Source file has zero `num_ctx` references. Tests pin this as a regression guard against the 48-1 KV-cache-reload finding. |
| Wiring | `test_wiring_create_app_default_client_factory_is_build_llm_client` | `create_app` defaults `claude_client_factory` to `build_llm_client`; this binds the `SIDEQUEST_LLM_BACKEND` env-var to production reality. |

### Test File

- `sidequest-server/tests/agents/test_ollama_backend_e2e_48_2.py` — 15 tests

### Rule Coverage (python.md lang-review checklist)

| Rule | Test(s) | Status |
|------|---------|--------|
| #1 silent exceptions | (existing test_ollama_client.py covers `OllamaClientError` raise paths; new tests use distinct fake_http) | covered upstream |
| #2 mutable defaults | not applicable — OllamaClient ctor uses `dict | None = None` pattern correctly | n/a |
| #3 type annotations | new tests preserve full annotations on helpers | passing |
| #4 logging | not applicable — new tests don't add logging; existing `history_cap_exceeded` warning covered in test_ollama_client.py | n/a |
| #5 path handling | new tests use `pathlib.Path` throughout (no string path concat); `read_text(encoding="utf-8")` always specified | passing |
| #6 test quality | every test has a meaningful assertion comparing a specific value; no `assert True`, no truthy-only checks on critical values, no `let _` equivalents | self-checked ✓ |
| #7 resource leaks | `_FakeHttpResponse` implements `__enter__`/`__exit__`; subprocess.run has `timeout=` | passing |
| #8 unsafe deserialization | new tests use `json.loads` on test-controlled bytes only | passing |
| #9 async pitfalls | `asyncio.run` used at call sites; no blocking inside async (the fake_http's `time.sleep` runs inside `asyncio.to_thread` per OllamaClient design) | passing |
| #10 import hygiene | no star imports, no circular imports (verified by collection) | passing |
| #11 input validation | not applicable at test layer — covered by existing factory test (`UnknownBackend`) | covered upstream |
| #12 dependency hygiene | no new deps introduced | n/a |
| #13 fix-introduced regressions | meta — no fixes applied yet, dev pass will re-scan | dev phase |

**Rules checked:** 13/13 applicable lang-review rules either covered by new tests or explicitly noted as upstream/n/a.
**Self-check:** 0 vacuous assertions found in new test file.

### Test Run Summary

```
collected 15 tests
passed:  13
failed:  2  (test_ac3_latency_comparison_script_exists_and_is_invocable,
              test_ac4_audit_outcome_documented_in_as_installed_spec)
duration: 0.24s
```

### Handoff Notes for Dev

- **Branch:** already on `feat/48-2-validate-ollama-backend-e2e` in `sidequest-server/`.
- **Two RED items map to two concrete deliverables:**
  1. Create `sidequest-server/scripts/ollama_latency_check.py` (the test accepts either `sidequest-server/scripts/` or orchestrator `scripts/` — pick `sidequest-server/scripts/` since the script is server-specific). Must support `--help` (exit 0, help text contains "latency"). Suggested body: compare a single `send_stateless` call through `build_llm_client()` against a stored or measured Claude baseline; emit pass/fail vs the 3x budget.
  2. Edit `docs/superpowers/specs/2026-05-06-local-qwen-code-editor-as-installed.md`. The existing line ~60 note ("Worth a follow-up when SideQuest's Ollama backend is exercised") should be extended with an "Audit conclusion — story 48-2" subsection that records:
     - that `OllamaClient` was reviewed,
     - that no per-request `num_ctx` was found in either `/api/generate` or `/api/chat` request bodies,
     - that regression guards are now in place in `tests/agents/test_ollama_backend_e2e_48_2.py`.
- **Manual playtest evidence:** the GREEN handoff also needs operator-captured evidence that AC1 + AC3's numeric budget were satisfied against a real Ollama instance. Record turn timing and an OTEL `agent.call.session` span snapshot in this session file's Delivery Findings under `### Dev (implementation)` before exiting GREEN.

**Handoff:** To Dev for implementation.

## Dev Assessment

**Implementation Complete:** Yes
**Tests:** 15/15 passing (GREEN)
**Branch:** `feat/48-2-validate-ollama-backend-e2e` in `sidequest-server/` (pushed to origin)
**Orchestrator:** `main` (pushed to origin) — single doc commit for AC4 audit conclusion

### Files Changed

| Repo | File | Purpose |
|------|------|---------|
| sidequest-server | `scripts/ollama_latency_check.py` (new, +159) | AC3 operator-facing latency-comparison script; supports `--help` exit 0, `--baseline-claude-s` for 3x budget verdict, distinct exit codes for PASS/FAIL/unreachable |
| sidequest-server | `tests/agents/test_ollama_backend_e2e_48_2.py` (ruff-format) | Whitespace-only changes from `ruff format` after RED commit |
| orchestrator | `docs/superpowers/specs/2026-05-06-local-qwen-code-editor-as-installed.md` (+14 lines) | Audit conclusion subsection appended below line 60's prospective follow-up note |

### Commits

- `sidequest-server` (`feat/48-2-validate-ollama-backend-e2e`):
  - `054ab64` test: add failing tests for 48-2 Ollama backend validation + audit (TEA)
  - `a9b3419` feat(48-2): add ollama_latency_check script for AC3 manual playtest (Dev)
- `orchestrator` (`main`):
  - `d4d95ec` docs(48-2): record OllamaClient num_ctx audit conclusion (AC4) (Dev)

### Test Run Summary

```
sidequest-server tests/agents/test_ollama_backend_e2e_48_2.py
collected 15 tests
passed:  15
failed:  0
duration: 0.25s
```

Adjacent suites unchanged: `tests/agents/test_ollama_client.py` (10/10) and `tests/agents/test_llm_factory.py` (5/5) both still passing — no regressions.

### Self-Review Checklist

- [x] Code is wired to a real consumer — `build_llm_client` is the production entry point used by `sidequest/server/app.py:102`; the test `test_wiring_create_app_default_client_factory_is_build_llm_client` pins that wiring.
- [x] Code follows project patterns — late import inside script body keeps `--help` fast; argparse with descriptive help; distinct exit codes per failure mode (no silent fallback per CLAUDE.md).
- [x] All acceptance criteria met (with one operator-side caveat — see Delivery Findings below):
  - AC1: 3 tests verify factory → OllamaClient → send_stateless / send_with_session roundtrip end-to-end.
  - AC2: 4 tests verify `agent.backend="ollama"` on every span emission path.
  - AC3: OTEL span duration observable + operator script in place; numeric 3x verdict happens during manual playtest.
  - AC4: 4 regression-guard tests + as-installed spec records the no-fix-needed audit outcome.
- [x] Error handling: script catches broad Exception with `# noqa: BLE001` and a comment explaining why (operator triage tool, distinguish via exit code, not exception type).
- [x] Lint clean: `ruff check` + `ruff format` pass; pyright reports 0 errors on both new files.
- [x] No emoji introduced in code or docs (per project memory).

### Python Lang-Review Self-Check (`gates/lang-review/python.md`)

| # | Check | Outcome |
|---|-------|---------|
| 1 | Silent exception swallowing | Script catches Exception with explicit `# noqa: BLE001` + comment explaining the operator-tool rationale; surfaces `msg` to stderr; returns distinct exit code (2). Not silent. |
| 2 | Mutable default arguments | None introduced. |
| 3 | Type annotation gaps at boundaries | `main(argv: list[str] | None = None) -> int`, `_measure_one_call(model, system_prompt, user_prompt) -> float`, `_build_parser() -> ArgumentParser` all annotated. |
| 4 | Logging | Script uses `print(... file=sys.stderr)` for errors (operator-facing CLI, not a service log path); appropriate for a one-shot tool. |
| 5 | Path handling | No file I/O in the script. Tests use `pathlib.Path` + `encoding="utf-8"`. |
| 6 | Test quality | TEA's RED self-check carried forward; Dev added no new tests. |
| 7 | Resource leaks | No file/socket/lock opened. |
| 8 | Unsafe deserialization | None. |
| 9 | Async pitfalls | `asyncio.run` used at top level; no blocking inside coroutine; `await` present on `send_stateless`. |
| 10 | Import hygiene | No star imports; late import of `build_llm_client` inside `_measure_one_call` is intentional (keeps `--help` cheap and tolerant of partial venv installs). |
| 11 | Input validation at boundaries | argparse type-checks numeric args (`type=float`); no eval/exec/SQL surface. |
| 12 | Dependency hygiene | No new deps. |
| 13 | Fix-introduced regressions | n/a — Dev's two diffs are net-new files, not modifications of audited code paths. |

### Manual Playtest Status (operator obligation)

A genuine AC1 end-to-end and AC3 numeric ≤3x verdict require a live Ollama instance. Ollama is **not reachable on the machine that ran this implementation** (`curl http://localhost:11434/api/tags` → HTTP 000) — per project memory, the Ollama daemon lives on the Mac Studio M3 Ultra (Keith's primary machine). The operator-side playtest is captured as a non-blocking Delivery Finding below; Reviewer can either wait for the playtest snapshot or merge contingent on the operator-evidence-after-merge pattern.

**Handoff:** To Reviewer.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned (with three pre-logged TEA deviations covering interpretive choices around testability)
**Mismatches Found:** 0 new (3 deviations already disclosed by TEA, all minor/behavioral)

### Substantive AC Walk-through

| AC | Spec | Code | Verdict |
|----|------|------|---------|
| AC1 — "one full playtest turn through the Ollama backend" | A live narrator turn that produces narration + state patches via Ollama | Three automated tests assert env→factory→`OllamaClient.send_stateless` roundtrip (the narrator's canonical post-ADR-098 hot path) with mocked HTTP; live narrator turn deferred to operator playtest evidence. | **Aligned** — the testable layer is the LLM-client boundary; everything above it (orchestrator → prompt build → state patch) is already covered by existing narrator/orchestrator tests that don't care which LLM backend services the call. The deviation log accurately discloses the interpretation. |
| AC2 — `agent.backend="ollama"` on OTEL span | OTEL span must carry the backend attribute | Four tests pin `agent.backend="ollama"` on `agent.call` and `agent.call.session` spans across `send_with_model`, `send_with_session`, `send_stateless`, and factory-built paths. | **Aligned** — exact match. The factory-built variant is a particularly good defensive test against future refactors. |
| AC3 — "latency budget within 3x of Claude baseline" | Numeric runtime budget vs Claude baseline | OTEL-duration observability test + operator-facing `scripts/ollama_latency_check.py` (exit codes for PASS/FAIL/unreachable) running against a live Ollama on the M3 Ultra. | **Aligned via deferred operator step** — the numeric verdict is honestly hard to assert in CI without committing an arbitrary Claude baseline. The script makes the verdict reproducible and the deferred-evidence pattern is well-disclosed. |
| AC4 — "num_ctx pattern reviewed; fixed if present" | Audit; conditional fix | Audit performed: no per-request num_ctx pattern in either `/api/generate` or `/api/chat` body construction. Four regression guards (3 runtime body-shape + 1 static source scan) pin the negative invariant. Audit outcome written into as-installed spec. | **Aligned** — the conditional clause ("fixed if present") is honored: no fix needed because no problem found. The regression guards convert a one-time audit into a permanent property. |

### Reuse-First Sanity Check

- **`OllamaClient`** reused without modification — exactly as 48-1 shipped it. ✓
- **`build_llm_client` factory** reused — the env-var → backend chain is unchanged. ✓
- **OTEL `agent_call_span` / `agent_call_session_span`** reused — `backend="ollama"` was already plumbed through at construction time. ✓
- **`otel_capture` test fixture** reused from `tests/agents/conftest.py:63` — no new test infrastructure invented. ✓
- **`_FakeHttpResponse` test helper** is a new local class, but it deliberately mirrors the existing pattern in `tests/agents/test_ollama_client.py:33` rather than importing it. Minor duplication; acceptable for test isolation (each test file owning its fixtures keeps coupling low).
- **`scripts/ollama_latency_check.py`** is new infrastructure but justified: no existing latency-comparison tool in the codebase; the closest neighbor (`scripts/playtest_dashboard.py` in orchestrator) is an OTEL visualizer, not a benchmarking tool. New file scope is one focused operator concern. ✓

### Design Quality Observations (non-blocking, for Reviewer awareness)

1. **`client._http = ...` private-slot injection in tests** — the test file accesses `OllamaClient`'s private `_http` attribute via `# noqa: SLF001`. This is consistent with the existing `test_ollama_client.py` pattern (which uses the public `http_fn=` constructor parameter instead). For the factory-built tests where the client is already constructed, the private-slot swap is the only seam available. A future refactor could expose a `with_http(fn) -> Self` builder on `OllamaClient`, but it's not required by this story.

2. **Late import of `build_llm_client` inside `_measure_one_call`** — comment explains the rationale (cheap `--help`, partial-venv tolerance). Worth noting for Reviewer that this is intentional, not an oversight.

3. **Broad `except Exception` in the script** — `# noqa: BLE001` is annotated with operator-tool rationale (distinguish failure modes via exit code, not exception type). The python lang-review check #1 (silent exception swallowing) explicitly allows this when justified, and the script forwards `str(exc)` to stderr. Honest pattern.

### Decision

**Proceed to verify** (next phase: TEA simplify + quality-pass).

No hand-back to Dev required. The three TEA deviations are accurately disclosed, the implementation honors the spirit of every AC, and the operator-deferred items (AC1 live playtest, AC3 numeric verdict) are correctly captured as non-blocking Delivery Findings rather than swept under the rug.

## TEA Assessment (verify phase)

**Phase:** finish
**Status:** GREEN confirmed, simplify findings triaged, regression check clean for 48-2 scope

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 2 (`scripts/ollama_latency_check.py`, `tests/agents/test_ollama_backend_e2e_48_2.py`)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 2 findings | (a) `_generate_body` could reuse `_ok_generate_body` from `test_ollama_client.py` — medium confidence; (b) `_FakeHttpResponse` divergence vs `test_ollama_client.py:33` — low confidence, justified by AC3 latency simulation |
| simplify-quality | 1 finding | Docstring documented exit code 3 that `main()` never returns — high confidence |
| simplify-efficiency | 1 finding | `_walk_for_key` recursion overkill for Ollama's flat protocol — medium confidence |

**Applied:** 1 high-confidence fix
- `scripts/ollama_latency_check.py` — removed inaccurate exit-code-3 documentation; clarified that argparse's own SystemExit handles bad CLI args. Commit `d254694`. Net change: +7 / -5 lines.

**Flagged for Review (medium-confidence, not auto-applied):**
- **`_generate_body` reuse opportunity** (reuse, line 70): Cross-module test dependency would shave ~7 lines but introduce coupling between two test files in `tests/agents/`. Keeping it inlined preserves test-isolation; Reviewer may decide otherwise.
- **`_walk_for_key` recursion** (efficiency, line 112): The recursive scan defends against future code paths that nest `num_ctx` inside `options.*` (Ollama's protocol doesn't currently support nesting, but a future shim could). The cost is 8 lines of code for a permanent regression guard against a known production incident (28s KV-cache reload from 48-1). I judge the defensive depth proportionate to the risk; Reviewer may collapse if disagreeing.

**Noted (low-confidence, observation only):**
- `_FakeHttpResponse` divergence — `tests/agents/test_ollama_backend_e2e_48_2.py:50` extends the older `test_ollama_client.py:33` version with a `_delay_s` parameter for latency simulation (used by `test_ac3_span_records_request_duration_observable_via_otel`). Pulling the latency feature into the old class would be dead code for the existing suite; pulling the old class into the new file would lose the AC3-specific feature. Architect previously noted this is acceptable test-isolation duplication. Concur.

**Reverted:** 0 — the single applied fix is a documentation-only change. Re-run of `tests/agents/test_ollama_backend_e2e_48_2.py` after the fix: 15/15 still passing.

**Overall:** simplify: applied 1 fix

### Quality Checks

- `ruff check` on changed files: All checks passed.
- `pyright`: 0 errors, 0 warnings on both new files.
- `pytest tests/agents/test_ollama_backend_e2e_48_2.py tests/agents/test_ollama_client.py tests/agents/test_llm_factory.py`: **30/30 passing** (15 new + 15 adjacent, no regressions in the Ollama-client neighbourhood).

### Wider Project Test State (non-blocking)

`just check-all` reported 5 failures in `tests/genre/test_victoria_class_kits.py`. These are **pre-existing on develop** — verified via `git diff develop HEAD -- tests/genre/test_victoria_class_kits.py` returning empty (story 48-2 made zero changes to that file or its dependencies). The failures originate from story 49-4's `test_victoria_class_kits` wiring commit (`3ebbf0e`) and are not in 48-2's scope. Captured as a non-blocking Delivery Finding for whoever owns the Victoria genre pack.

**Handoff:** To Reviewer for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — preflight 0 smells, 15/15 tests pass, ruff/pyright clean |
| 2 | reviewer-edge-hunter | No | skipped | N/A | Disabled via `workflow.reviewer_subagents.edge_hunter=false`; edge-flavour overlap covered by rule-checker (negative-baseline AC) |
| 3 | reviewer-silent-failure-hunter | No | skipped | N/A | Disabled via `workflow.reviewer_subagents.silent_failure_hunter=false`; silent-failure-flavour overlap covered by rule-checker (late import → ModuleNotFoundError defer) |
| 4 | reviewer-test-analyzer | Yes | findings | 6 | confirmed 4, downgraded 1, dismissed 1 |
| 5 | reviewer-comment-analyzer | Yes | findings | 4 | confirmed 4 |
| 6 | reviewer-type-design | No | skipped | N/A | Disabled via `workflow.reviewer_subagents.type_design=false`; type-flavour overlap covered by rule-checker (missing return types on test helpers) |
| 7 | reviewer-security | No | skipped | N/A | Disabled via `workflow.reviewer_subagents.security=false`; security-flavour overlap covered by rule-checker (input validation gap on `--baseline-claude-s`) |
| 8 | reviewer-simplifier | No | skipped | N/A | Disabled via `workflow.reviewer_subagents.simplifier=false`; simplicity-flavour overlap covered by TEA's verify-phase simplify fan-out (1 fix already applied) |
| 9 | reviewer-rule-checker | Yes | findings | 5 | confirmed 4, downgraded 1 |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled per settings)
**Total findings:** 12 confirmed, 1 dismissed (with rationale), 0 deferred

## Rule Compliance (python.md lang-review + CLAUDE.md additionals)

Exhaustive per-rule walk of every changed item against every applicable rule:

| Rule | Items checked | Compliant | Violations | Severity (worst) |
|------|---------------|-----------|------------|------------------|
| #1 silent exceptions | 3 (`main()`, `_post_generate`, `_post_chat`) | 2 | 1 — exit-code 2 conflates `UnknownModel`/`UnknownBackend` with unreachability | [MEDIUM] |
| #2 mutable defaults | 8 — script + OllamaClient + test helpers | 8 | 0 | — |
| #3 type annotations at boundaries | 12 (functions/methods/test helpers) | 10 | 2 — `_capture_http`, `_find_span` missing return types (load-bearing test DI seam) | [LOW] |
| #4 logging | 5 (OllamaClient logger + script stderr) | 5 | 0 | — |
| #5 path handling | 6 (test pathlib usage, script no-IO) | 6 | 0 | — |
| #6 test quality | 15 tests | 13 | 2 — wiring test is source-text grep; AC2 backend assertion lacks failure message (low) | [HIGH] (wiring) |
| #7 resource leaks | 4 (HTTP context managers, fake context manager) | 4 | 0 | — |
| #8 unsafe deserialization | 4 (json/subprocess) | 4 | 0 | — |
| #9 async pitfalls | 6 (asyncio.run, to_thread, fake sleep) | 6 | 0 | — |
| #10 import hygiene | 6 (top-level + late import) | 5 | 1 — late import defers `ModuleNotFoundError` past `--help` | [HIGH] |
| #11 input validation at boundaries | 5 (argparse, model resolver, env vars) | 4 | 1 — `--baseline-claude-s` accepts negatives → guaranteed PASS | [HIGH] |
| #12 dependency hygiene | 1 (no new deps) | 1 | 0 | — |
| #13 fix-introduced regressions | 3 | 3 | 0 | — |
| CLAUDE.md "No Silent Fallbacks" | 4 (factory raises, session raises, exit 2, late import) | 2 | 2 — exit 2 ambiguity (medium) + late import (high) | [HIGH] |
| CLAUDE.md "No Stubbing" | 5 (full impls) | 5 | 0 | — |
| CLAUDE.md "Don't Reinvent" | 2 (script uses factory, OllamaClient reuses types) | 2 | 0 | — |
| CLAUDE.md "Verify Wiring, Not Just Existence" | 2 (script wiring, factory wiring) | 1 | 1 — wiring test is a source grep, not a wiring guarantee | [HIGH] |
| CLAUDE.md "Every Test Suite Needs a Wiring Test" | 1 | 1 (exists) but quality fails rule | 1 — overlaps with above; the test exists but doesn't fulfil the rule's intent | [HIGH] (same fix) |
| CLAUDE.md "OTEL Observability" | 3 (two spans + four AC2 tests) | 3 | 0 | — |

**Aggregate:** 87 items checked across 19 rules. 7 violations (4 [HIGH], 2 [MEDIUM], 1 [LOW]) all concentrated in two files: the latency script and the test file. Production code (`OllamaClient`, `llm_factory`, `server.app`) has zero violations.

## Devil's Advocate

The Queen of Hearts paces. *Off with their heads!* But first, let's prosecute properly.

This story claims to validate the Ollama backend end-to-end and audit `num_ctx`. The audit half is genuinely solid — the production `OllamaClient` is clean, the regression guards are real, the as-installed doc records the conclusion. **That half I would approve.** The script and the test file, however, are where the prosecution starts.

The script is supposed to give the operator a verdict: did Ollama-on-this-machine meet the 3x latency budget? Imagine an operator who runs it after a fresh Ollama install. They mistype: `--baseline-claude-s -1.5`. They get `PASS`. Confident, they merge a follow-up that promotes Ollama as the daily-driver narrator backend. That's not a hypothetical — argparse accepts the negative without a guard, the budget math then produces a negative ceiling, and `elapsed <= negative` is always false... wait, no, `elapsed <= negative_budget` is always false, so verdict becomes FAIL, not PASS. Let me re-read line 149: `verdict = "PASS" if elapsed <= budget else "FAIL"`. Negative budget → negative right-hand side → `elapsed > budget` always → FAIL. So a negative baseline produces a guaranteed *FAIL*, not a guaranteed PASS. **Correction to rule-checker finding #11**: the failure mode is "always FAIL," not "always PASS." Still wrong (operator gets a misleading verdict from a typo) but the direction is reversed. Updating the finding severity from [HIGH] to [MEDIUM] — a misleading FAIL is annoying but it's a loud failure, not a silent success. The Queen pauses. *Hmph.*

The wiring test is the bigger problem. Look at it as a saboteur. I delete `build_llm_client` entirely, replace it with a lambda inline at the call site: `... else (lambda: ClaudeClient())`. The test as written greps for the string `"else build_llm_client"` — it would FAIL on the source change. Good. But now I keep the import line *and* keep the string `else build_llm_client` somewhere — say, in a comment — while routing the actual factory through a different path. Test passes. Wiring broken. The finding holds: the test is brittle for the wrong reasons (refactor-fragile) but ALSO insufficient (a malicious or careless edit can satisfy the string without satisfying the wiring).

Now the AC1 stateless test. What does it actually prove? The mock returns a `_chat_body("narrator reply")` and the test asserts `response.text == "narrator reply"`. Stateless does NOT verify that the `system_prompt` argument was concatenated with `user_message` and sent — it could be dropped entirely and the mock would still return the fixed `"narrator reply"`. So an "AC1 send_stateless roundtrips" green light tells us: env→factory→OllamaClient→HTTP-mock returns a response. It does *not* tell us: the system prompt actually reached Ollama. For a story whose explicit purpose is regression-guard, that's a load-bearing gap.

The four lying docstrings are individually mild but collectively concerning. `_measure_one_call` claims its env-var set is "defence-in-depth" when it's actually the *sole* set. The as-installed doc claims the `/api/chat` body has `messages` without noting the system+user merge. The except-block comment claims to distinguish argparse failures from runtime failures via exit codes when argparse never enters the except block. Each is one wrong sentence; together they form a pattern of writing comments aspirationally rather than descriptively. The Diamonds-and-Coal principle says detail signals importance — these comments lavish detail on rationale that doesn't match the code.

What would a senior reviewer DO with this? Send it back. The fixes are 30-60 minutes of careful test+script edits. The production code is fine. The story's intent — regression-guards + audit conclusion — survives intact once the guards actually guard.

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Source | Issue | Location | Fix Required |
|----------|--------|-------|----------|--------------|
| [HIGH] | [TEST] [RULE] | Wiring test is a source-text grep, not a behavioural assertion — violates CLAUDE.md "Verify Wiring, Not Just Existence" | `tests/agents/test_ollama_backend_e2e_48_2.py:234-256` | Replace source-text greps with: `from sidequest.server.app import create_app; app = create_app(); assert app.state.claude_client_factory is build_llm_client`. Test must fail if the factory is genuinely unwired, pass otherwise. |
| [HIGH] | [TEST] | AC1 `test_ac1_factory_ollama_send_stateless_roundtrips_end_to_end` never verifies the system+user message collapse — regression guard claim is theatre | `tests/agents/test_ollama_backend_e2e_48_2.py:128-163` | Pass a `captured_bodies` list through `_capture_http`. After the call, assert `captured[0]["messages"]` contains one user-role entry whose content includes both the system-prompt text and the user-message text. This is the actual stateless contract per `ollama_client.py:178-186`. |
| [HIGH] | [RULE] | Late import of `build_llm_client` defers `ModuleNotFoundError` to call time, masking broken-environment failures past `--help` — violates "No Silent Fallbacks" | `scripts/ollama_latency_check.py:117` | Move `from sidequest.agents.llm_factory import build_llm_client` to module top level. The argparse-`--help`-cost rationale doesn't hold (argparse parses regardless of import location); the partial-venv-tolerance rationale actively violates fail-loudly. |
| [HIGH] | [RULE] [SEC]-flavour | `--baseline-claude-s` accepts negative floats with no validation — produces nonsensical verdict (always FAIL with negative budget; potentially misleading either way) | `scripts/ollama_latency_check.py:71-79` | After parsing, add: `if args.baseline_claude_s is not None and args.baseline_claude_s <= 0: parser.error("--baseline-claude-s must be > 0")`. The argparse `type=` accepts whatever float() does, including `-1.5`, `0.0`, and `nan`. |
| [MEDIUM] | [DOC] | `_measure_one_call` docstring claims env-var set is "defence-in-depth re-assert" but `main()` never sets it — function is the sole assignment, claim is false | `scripts/ollama_latency_check.py:111-115` | Replace the docstring's "Caller already does this; this function re-asserts it for defence-in-depth" with "Sets SIDEQUEST_LLM_BACKEND unconditionally — this is the sole assignment. The late import follows so the env var is in place before the factory reads it." |
| [MEDIUM] | [DOC] | As-installed audit doc describes `/api/chat` body for `send_stateless` as `{"model", "messages", "stream": False}` without noting that `send_stateless` merges `system_prompt` into a single user-role message — misleads readers about the actual wire format | `docs/superpowers/specs/2026-05-06-local-qwen-code-editor-as-installed.md` (`Audit conclusion — story 48-2` subsection) | Append a parenthetical to the `/api/chat` row: "(note: `send_stateless` merges `system_prompt` into the user message as a single combined string before calling `send_with_session`; the `messages` array therefore contains one user-role entry, not a separate `system`+`user` pair)." |
| [MEDIUM] | [DOC] | Inline `# noqa: BLE001` comment claims to distinguish "unreachable" from "bad args" via exit code, but argparse errors fire pre-`main()` and never enter this except block — the claimed distinction is illusory | `scripts/ollama_latency_check.py:131-136` | Remove the "Distinguish 'unreachable' from 'bad args' via exit code for scripted callers" sentence. The module docstring (lines 37-38) already clarifies that argparse handles its own exits; the inline comment can simply read "Surface the raw cause string to operator stderr; exit 2 covers any send_stateless failure." |
| [MEDIUM] | [RULE] | `except Exception` exit-code 2 lumps `UnknownModel`/`UnknownBackend` (configuration errors) with network unreachability — scripted callers cannot distinguish — violates "fail loudly AND accurately" | `scripts/ollama_latency_check.py:124-136` | Either (a) catch `OllamaClientError` (network/transport) for exit 2 and a separate `(UnknownModel, UnknownBackend)` for exit 3 with a documented "configuration error" label, OR (b) update docstring and epilog to honestly say exit 2 is "any pre-verdict failure" rather than implying it means unreachability. Option (a) preferred; (b) acceptable if the operator only ever reads stderr. |
| [MEDIUM] | [TEST] | AC3 span-duration floor `delay * 0.5` is too loose — would pass even if span timing recorded only 25% of actual elapsed time, missing instrumentation-placement bugs | `tests/agents/test_ollama_backend_e2e_48_2.py:355-360` | Tighten floor to `delay * 0.8` (48ms floor for the 60ms simulated delay). Still tolerant of scheduler jitter, but catches a span that closed before the blocking call returned. |
| [MEDIUM] | [TEST] | AC1 URL test reaches into private `_base_url` instead of asserting observable behavior — implementation coupling | `tests/agents/test_ollama_backend_e2e_48_2.py:213-225` | Make a `send_stateless` call against a `_capture_http` fake, then assert the captured `req.full_url` starts with `DEFAULT_OLLAMA_URL`. Tests the URL that would actually be hit, not the internal storage form. |
| [MEDIUM] | [TEST] | Missing negative test for `build_llm_client` raising `UnknownBackend` on unrecognised value — factory's no-silent-fallback guarantee is unguarded in this suite | `tests/agents/test_ollama_backend_e2e_48_2.py` (new test, anywhere in the AC1 block) | Add: `def test_ac1_factory_raises_unknown_backend_on_bad_value(monkeypatch): monkeypatch.setenv(ENV_BACKEND, "groq"); with pytest.raises(UnknownBackend): build_llm_client()`. The factory's loud-failure contract is explicit in `llm_factory.py:27-29` and deserves a guard. |
| [MEDIUM] | [DOC] | Stale comment treats LocalDM as an active consumer of `send_with_session` when LocalDM is dormant per ADR comment in `sidequest/agents/local_dm.py` and project memory | `tests/agents/test_ollama_backend_e2e_48_2.py:166-172` | Replace "LocalDM and any future stateful caller use send_with_session" with "Any future stateful caller (LocalDM preprocessor is dormant per 2026-04-28 spec)". Or drop the LocalDM mention entirely. |
| [LOW] | [TYPE]-flavour [RULE] | `_capture_http()` missing return type annotation; inner `fake(req)` closure missing `req` type; `_find_span()` missing both | `tests/agents/test_ollama_backend_e2e_48_2.py:94-109, 259-265` | Add annotations: `_capture_http(...) -> Callable[[Any], _FakeHttpResponse]`, `def fake(req: Any) -> _FakeHttpResponse:`, `_find_span(exporter: InMemorySpanExporter, name: str) -> Span | None`. Test-helper exemption in rule #3 technically applies, but these are load-bearing test DI seams. |
| [LOW] | [TEST] | `test_ac4_send_stateless_request_body_has_no_num_ctx_anywhere` is acknowledged as redundant with the session-path test; adds no independent coverage | `tests/agents/test_ollama_backend_e2e_48_2.py:444-456` | Either remove or document the specific code path it guards that the session test does not. Dismissed lightly — defensive copy-paste is acceptable when the test cost is negligible. *Dismissed unless Dev prefers to remove.* |
| [LOW] | [SIMPLE]-flavour (TEA verify already addressed) | `_walk_for_key` recursive scan is overkill for Ollama's flat protocol | `tests/agents/test_ollama_backend_e2e_48_2.py:112-120` | TEA's verify phase already flagged and judged this proportionate to the 28s KV-cache-reload regression risk. No change requested. *Defer to TEA's judgment.* |

**Tag inventory** (gate requires presence of all 8):
- `[EDGE]` — N/A (subagent disabled); edge-flavour overlap captured under negative-baseline finding tagged `[SEC]`-flavour
- `[SILENT]` — N/A (subagent disabled); silent-failure-flavour overlap captured under late-import finding tagged `[RULE]`
- `[TEST]` — wiring grep, AC1 missing body verify, AC3 loose floor, URL private-slot, missing UnknownBackend negative, AC4 stateless redundancy
- `[DOC]` — `_measure_one_call` lying docstring, as-installed merge elision, except-block false distinction, LocalDM stale
- `[TYPE]` — N/A (subagent disabled); type-flavour overlap captured under missing return-type annotations finding tagged `[RULE]`
- `[SEC]` — N/A (subagent disabled); security-flavour overlap captured under `--baseline-claude-s` validation gap tagged `[RULE]`
- `[SIMPLE]` — N/A (subagent disabled); simplicity-flavour overlap was handled by TEA verify-phase simplify fan-out (1 fix already applied; no Reviewer-new simplifier finding)
- `[RULE]` — late import (No Silent Fallbacks + #10), negative baseline (#11), exit-code 2 conflation (#1), missing return annotations (#3); covered above

**Production code:** Zero findings. `OllamaClient`, `llm_factory`, `server.app`, and the as-installed doc's audit substance are sound. The audit conclusion finding holds — the regression-guard half of this story is real.

**Test infrastructure + operator script:** Where the prosecution lives. The story's regression-guard premise is undermined by tests that don't guard (wiring is a string-grep, AC1 stateless never checks the body) and an operator script that defers env failures and accepts negative baselines.

**Estimated rework:** 30-60 minutes of focused test + script + doc edits. No production code touched. No new dependencies. The 4 HIGH items have a clear, contained fix list.

**Dismissed:** AC4 stateless body redundancy — defensive copy-paste, low cost; documented in the test docstring; leave to Dev's discretion.

**Deferred to TEA's verify-phase judgment:** `_walk_for_key` recursion depth (TEA already considered + approved this).

**Handoff:** Back to Dev (via TEA red rework — findings are testable, several add new tests).

## TEA Assessment (red rework — round-trip 1)

**Phase:** finish (rework after Reviewer rejection)
**Round-Trip Count:** 1
**Status:** RED — 16/19 passing, 3 failing tests drive Dev's remaining work

### What Is Now RED for Dev (3 failing tests)

1. **`test_ac3_script_imports_build_llm_client_at_module_top_level`** — addresses Reviewer's [HIGH] "late import defers ModuleNotFoundError past --help" finding. Test ast-parses `scripts/ollama_latency_check.py` and asserts the `from sidequest.* import …` statement is a direct child of the Module body, not nested inside `_measure_one_call`. **Dev fix:** move `from sidequest.agents.llm_factory import build_llm_client` from inside `_measure_one_call` to the top of the script (after the stdlib imports).

2. **`test_ac3_script_rejects_zero_or_negative_baseline_claude_s`** — addresses Reviewer's [HIGH] "negative baseline produces nonsensical verdict" finding. Test imports the script via `importlib.util` and asserts `main(["--baseline-claude-s", "-1.5"])` and `main(["--baseline-claude-s", "0"])` both raise `SystemExit`. **Dev fix:** after `args = _build_parser().parse_args(argv)`, add a guard such as
   ```python
   if args.baseline_claude_s is not None and args.baseline_claude_s <= 0:
       _build_parser().error("--baseline-claude-s must be > 0")
   ```
   (or refactor to a custom argparse `type=` callable that calls `argparse.ArgumentTypeError`).

3. **`test_ac4_audit_outcome_notes_send_stateless_system_user_merge`** — addresses Reviewer's [MEDIUM] "as-installed doc elides merge" finding. Test asserts the as-installed audit conclusion mentions the system+user merge with any of these phrases: `merges system_prompt` / `merge system_prompt` / `merged into` / `single user` / `one user-role` / `single combined` / `user-role entry`. **Dev fix:** append a parenthetical to the `/api/chat` row in `docs/superpowers/specs/2026-05-06-local-qwen-code-editor-as-installed.md`'s `Audit conclusion — story 48-2` subsection, per the Reviewer's exact wording suggestion.

### Reviewer Findings Not Directly Tested (Dev still must fix)

The following [MEDIUM] findings are pure prose corrections that mechanical tests cannot enforce without becoming brittle. **Dev must apply these in addition to the three RED-driven changes:**

| Severity | Finding | File | Action |
|----------|---------|------|--------|
| [MEDIUM] | `_measure_one_call` docstring's "defence-in-depth re-assert" claim is false — `main()` never sets the env var; this function is the sole assignment | `scripts/ollama_latency_check.py:111-115` | Rewrite docstring per Reviewer Assessment's exact suggestion. |
| [MEDIUM] | Inline `# noqa: BLE001` comment claims to "distinguish 'unreachable' from 'bad args' via exit code" but argparse errors fire pre-`main()` | `scripts/ollama_latency_check.py:131-136` | Remove the false-distinction sentence; replace with a one-line comment per Reviewer's suggestion. |
| [MEDIUM] | Exit-code 2 conflates `UnknownModel`/`UnknownBackend` (config errors) with network unreachability | `scripts/ollama_latency_check.py:124-136` | Dev chooses: (a) split codes — catch `(UnknownModel, UnknownBackend)` for exit 3 + `OllamaClientError` for exit 2 + update docstring/epilog; OR (b) keep single code 2 but update docstring/epilog to honestly say "any pre-verdict failure" rather than implying unreachability. Option (a) is the Reviewer's preferred resolution. |

### Reviewer Findings Resolved by TEA in This Round

| Severity | Finding | Resolution |
|----------|---------|------------|
| [HIGH] | Wiring test is a source-text grep | Replaced with `assert app.state.claude_client_factory is build_llm_client` after `create_app()` call. Behavioural identity check. |
| [HIGH] | AC1 stateless test never verifies the system+user message collapse | Added `captured_bodies` capture + assertions that `messages` is a single user-role entry containing both system and user text. |
| [MEDIUM] | AC3 floor `delay * 0.5` too loose | Tightened to `delay * 0.8`. Test still passes. |
| [MEDIUM] | URL test reaches into private `_base_url` | Replaced with `captured_requests` inspection: assert `req.full_url` starts with `DEFAULT_OLLAMA_URL`. |
| [MEDIUM] | Missing `UnknownBackend` negative test | Added `test_ac1_factory_raises_unknown_backend_on_bad_value`. |
| [MEDIUM] | LocalDM stale docstring | Updated `test_ac1_factory_ollama_send_with_session_supports_multi_turn` docstring to note LocalDM is dormant. |
| [LOW] | Missing return type annotations on `_capture_http`, `_find_span` | Added `Callable[[Request], _FakeHttpResponse]` and `Any | None` annotations; inner `fake(req: Request)` also annotated. |

### Reviewer Findings Dismissed (Re-confirmed)

| Finding | Rationale for keeping |
|---------|----------------------|
| [LOW] AC4 stateless body redundancy | The Reviewer themselves dismissed this. Defensive copy-paste cost is negligible; the test's docstring already acknowledges the redundancy. Keeping. |
| `_walk_for_key` recursion depth | Reviewer deferred to TEA's verify-phase judgment, which kept it. No change. |

### Test File Stats

- **Before:** 15 tests, 518 lines
- **After:** 19 tests, ~750 lines (3 new RED-driving tests + 1 new UnknownBackend negative + significant body/wiring/URL test rewrites)
- **Lint/type-check:** `ruff check` and `pyright` both clean.
- **Test run:** 16 passing, 3 failing (the intended RED state).

### Handoff Notes for Dev

Three test failures translate to three concrete changes:

1. **`scripts/ollama_latency_check.py`** — move sidequest import to top, add `--baseline-claude-s` validation guard.
2. **`docs/superpowers/specs/2026-05-06-local-qwen-code-editor-as-installed.md`** — append the merge-note parenthetical to the AC4 audit conclusion.
3. **`scripts/ollama_latency_check.py` (additional, no test guard)** — three prose fixes per the Reviewer-Findings-Not-Directly-Tested table above (`_measure_one_call` docstring, `# noqa: BLE001` inline comment, exit-code documentation/split).

Estimated rework: 15-30 minutes.

**Handoff:** To Dev for green.

## Dev Assessment (green rework — round-trip 1)

**Implementation Complete:** Yes
**Round-Trip Count:** 1
**Tests:** 19/19 passing in story file (was 16/19 at handoff); 34/34 in adjacent Ollama-client neighbourhood — no regressions
**Branch:** `feat/48-2-validate-ollama-backend-e2e` in `sidequest-server/` (pushed: commit `455bf56`)
**Orchestrator:** `main` (pushed: commit `d7bf993`)

### Files Changed (round-trip 1)

| Repo | File | Change |
|------|------|--------|
| sidequest-server | `scripts/ollama_latency_check.py` | (1) Moved `build_llm_client` + `UnknownBackend` + `OllamaClientError` + `UnknownModel` imports to module top level. (2) Added `parser.error()` for non-positive `--baseline-claude-s`. (3) Split exit codes: `(UnknownModel, UnknownBackend)` → 3, `OllamaClientError` → 2, bare `Exception` → 2 (with explanatory comment). (4) Rewrote `_measure_one_call` docstring to drop the false "defence-in-depth re-assert" claim. (5) Replaced the false-distinction sentence in the `# noqa: BLE001` inline comment with an honest "operator-facing tool: surface unexpected failures verbatim" note. (6) Updated module docstring and argparse epilog to match the new exit-code taxonomy. |
| sidequest-server | `tests/agents/test_ollama_backend_e2e_48_2.py` | Added `isinstance(req.data, bytes)` guard in `_capture_http`'s `fake()` to satisfy pyright now that the helper has tight type annotations (urllib's `req.data` is the broad `ReadableBuffer` union but `OllamaClient` always passes bytes). |
| orchestrator | `docs/superpowers/specs/2026-05-06-local-qwen-code-editor-as-installed.md` | Appended the merge-note parenthetical to the AC4 audit conclusion's `/api/chat` row, noting that `send_stateless` folds `system_prompt` into a single user-role message rather than producing a `[system, user]` pair. |

### Reviewer Findings — Resolution Status

| Severity | Finding | Resolution (this round) |
|----------|---------|-------------------------|
| [HIGH] | Wiring test is source-text grep | ✓ Resolved in TEA round (behavioural `is` check on `app.state.claude_client_factory`) |
| [HIGH] | AC1 stateless never verifies system+user collapse | ✓ Resolved in TEA round (body capture + assertions on merged messages array) |
| [HIGH] | Late import defers `ModuleNotFoundError` past `--help` | ✓ Resolved here — imports at module top level (commit `455bf56`) |
| [HIGH] | `--baseline-claude-s` accepts negatives | ✓ Resolved here — `parser.error()` for ≤ 0 (commit `455bf56`) |
| [MEDIUM] | `_measure_one_call` lying docstring | ✓ Resolved here — rewrote to honest "sole assignment, not a defence-in-depth re-assert" |
| [MEDIUM] | As-installed doc elides merge | ✓ Resolved here — parenthetical added (commit `d7bf993` on orchestrator main) |
| [MEDIUM] | Inline `# noqa: BLE001` false distinction | ✓ Resolved here — replaced with "operator-facing tool: surface unexpected failures verbatim" |
| [MEDIUM] | Exit-code 2 conflates config errors with unreachability | ✓ Resolved here — split codes (config → 3, transport → 2) with `UnknownModel`/`UnknownBackend` catch; docstring + epilog updated |
| [MEDIUM] | AC3 floor `delay * 0.5` too loose | ✓ Resolved in TEA round (tightened to `delay * 0.8`) |
| [MEDIUM] | URL test private-slot coupling | ✓ Resolved in TEA round (observable `full_url` assertion) |
| [MEDIUM] | Missing `UnknownBackend` negative test | ✓ Resolved in TEA round (new test added) |
| [MEDIUM] | LocalDM stale docstring | ✓ Resolved in TEA round |
| [LOW] | Missing return type annotations on test helpers | ✓ Resolved in TEA round |
| [LOW] | AC4 stateless body redundancy | Dismissed by Reviewer themselves; left as-is |
| (TEA verify) | `_walk_for_key` recursion depth | Reviewer deferred to TEA's verify-phase judgement; left as-is |

**All Reviewer Critical/High items resolved. All Medium items resolved or explicitly addressed. Low items either resolved or formally dismissed.**

### Test Run Summary

```
sidequest-server tests/agents/test_ollama_backend_e2e_48_2.py
collected 19 tests
passed:  19
failed:  0
duration: 0.57s

Adjacent suites (no regressions):
- tests/agents/test_ollama_client.py: 10/10
- tests/agents/test_llm_factory.py:    5/5
```

### Self-Review Checklist

- [x] All Reviewer-flagged Critical/High issues resolved (4 of 4).
- [x] All Reviewer-flagged Medium issues resolved or formally dismissed (8 of 8 — 7 resolved, 1 deferred per Reviewer instruction).
- [x] Lint clean: `ruff check` passes; `pyright` reports 0 errors, 0 warnings.
- [x] No regressions: 34/34 tests in the Ollama-client neighbourhood still pass.
- [x] No new test gaps introduced — the type-annotation tightening added one `isinstance` runtime guard, not test coverage holes.
- [x] No emoji introduced in code or docs.
- [x] Script remains operator-facing — top-level imports change does not break the `--help` invocation path (verified: `uv run python scripts/ollama_latency_check.py --help` exits 0, mentions "latency").
- [x] Exit-code split preserves operator semantics — stderr labels distinguish "config error" vs "ollama error" vs "unexpected error" so the operator can triage even before reading exit code.

### Manual Playtest Status (still operator obligation, unchanged from round 0)

The script now has tighter exit-code semantics, so the operator's playtest evidence should record:
- The elapsed time from `ollama elapsed: <N>s` stdout line.
- The verdict line (`claude baseline: …` row) if `--baseline-claude-s` is supplied.
- The exit code returned by the script (now in `{0, 1, 2, 3}` with documented meanings).

Captured in the Delivery Findings (operator follow-up section) for the M3 Ultra run.

**Handoff:** To Reviewer for re-review.

## Architect Assessment (spec-check — round-trip 1)

**Spec Alignment:** Aligned. Reviewer's round-0 rejection items all resolved, no new drift introduced by the rework.
**Mismatches Found:** 0 new (round-0 drift was test-quality, not spec-drift; round-1 fixes preserved spec semantics)

### Substantive Verification of Round-1 Fixes

I spot-checked every Reviewer [HIGH] / [MEDIUM] finding against the head of the branch (commits `06b8424` test rework + `455bf56` script rework + `d7bf993` orchestrator doc):

| Severity | Reviewer Finding | Fix Verified At | Verdict |
|----------|-----------------|------------------|---------|
| [HIGH] | Wiring test is source-text grep | `test_ollama_backend_e2e_48_2.py:271` — `assert app.state.claude_client_factory is factory_under_test` after `create_app()` call | ✓ Real behavioural identity check; would catch a refactor that satisfies a string match but breaks wiring |
| [HIGH] | AC1 stateless never verifies system+user merge | `test_ollama_backend_e2e_48_2.py:194-217` — `captured_bodies` array inspected after `send_stateless`, asserts single user-role entry contains both `system_text` and `user_text` substrings | ✓ Genuinely catches user_message drop or system_prompt drop |
| [HIGH] | Late import defers ModuleNotFoundError | `ollama_latency_check.py:56-57` — `from sidequest.agents.llm_factory import UnknownBackend, build_llm_client` + `from sidequest.agents.ollama_client import OllamaClientError, UnknownModel` at module top level | ✓ Broken sidequest install now surfaces at script load |
| [HIGH] | `--baseline-claude-s` accepts negatives | `ollama_latency_check.py:150-151` — `if args.baseline_claude_s is not None and args.baseline_claude_s <= 0: parser.error(...)` | ✓ `parser.error()` raises `SystemExit(2)` before any backend call |
| [MEDIUM] | Exit code 2 conflates config errors with unreachability | `ollama_latency_check.py:155-170` — three-way split: `(UnknownModel, UnknownBackend) → 3`, `OllamaClientError → 2`, bare `Exception → 2` with distinct stderr labels | ✓ Reviewer's preferred option (a) chosen; documented in module docstring and argparse epilog |
| [MEDIUM] | `_measure_one_call` lying docstring | `ollama_latency_check.py:99-107` — rewritten to "Sets `SIDEQUEST_LLM_BACKEND=ollama` unconditionally before invoking the factory — this is the sole assignment, not a defence-in-depth re-assert. The caller (main()) does not pre-set the env var." | ✓ Docstring now matches code reality |
| [MEDIUM] | As-installed doc elides merge | `docs/.../2026-05-06-...-as-installed.md` — `/api/chat` row now appended with: "(Note: `send_stateless` merges `system_prompt` into the user message as a single combined string before calling `send_with_session`; the `messages` array therefore contains one user-role entry, not a separate `system`+`user` pair. This matters for Ollama models whose behavior differs between role types — but is orthogonal to the `num_ctx` audit.)" | ✓ Substantive disclosure that doesn't undermine the audit's primary conclusion |
| [MEDIUM] | Inline `# noqa: BLE001` false distinction | `ollama_latency_check.py:166-170` — false-distinction sentence removed; replaced with "operator-facing tool: surface unexpected failures verbatim" and a code comment explaining the bare-Exception fallback | ✓ Comment no longer over-promises |
| [MEDIUM] | AC3 floor `delay * 0.5` too loose | `test_ollama_backend_e2e_48_2.py:456` — `delay * 0.8` | ✓ Tightened; tests still pass |
| [MEDIUM] | URL test private-slot coupling | `test_ollama_backend_e2e_48_2.py:236-264` — observable `req.full_url` assertion via `captured_requests` | ✓ Implementation-agnostic |
| [MEDIUM] | Missing `UnknownBackend` negative test | `test_ollama_backend_e2e_48_2.py:267-281` — `test_ac1_factory_raises_unknown_backend_on_bad_value` | ✓ New test pins the no-silent-fallback contract |
| [MEDIUM] | LocalDM stale docstring | `test_ollama_backend_e2e_48_2.py:209-213` — "LocalDM preprocessor is dormant per the 2026-04-28 spec" | ✓ Honest |
| [LOW] | Missing return type annotations | `test_ollama_backend_e2e_48_2.py:104` (`_capture_http -> Callable[[Request], _FakeHttpResponse]`) and `:325` (`_find_span(exporter: Any, name: str) -> Any | None`) | ✓ Annotated |
| [LOW] | AC4 stateless body redundancy | Dismissed by Reviewer themselves | — |

### Reuse-First Sanity Check (round-1 changes only)

- `UnknownModel`, `UnknownBackend`, `OllamaClientError` — all imported from existing `sidequest.agents.*` modules; no parallel error taxonomy invented. ✓
- The `EXIT_*` constants are local to the script (4 module-level integers); they document semantics rather than introducing a new error-code framework. Acceptable for a CLI tool. ✓
- The `isinstance(req.data, bytes)` runtime assertion in `_capture_http`'s fake closure is a defensive narrowing for pyright, not new abstraction. ✓

### Design Quality Observations (non-blocking, for Reviewer awareness)

1. **Bare `Exception` in `except` still returns `EXIT_OLLAMA_TRANSPORT`** — the round-1 fix kept the broad fallback to exit-code 2 with an "unexpected error" stderr label. The Reviewer's option (a) was strictly about distinguishing `(UnknownModel, UnknownBackend)` from other errors, and that distinction is now in place. Lumping unknown errors with transport failures under exit-2 is documented behavior. If this becomes a problem in operator practice, a future "exit 4 = unknown failure" split is trivial; not warranted yet.

2. **`parser.error("--baseline-claude-s must be > 0 (got: {x})")` uses f-string format** — earlier `.format(...)` form was rejected by `ruff` rule UP032 (auto-fix recommended f-string). Dev applied the auto-fix. No behaviour change.

3. **Argparse's exit code 2 overlaps with `EXIT_OLLAMA_TRANSPORT = 2`** — documented in the script's module docstring under "Note". Operators distinguish by reading stderr (argparse prints "usage: …"; `main()` prints "[ollama_latency_check] …"). This is a known argparse limitation, not a Dev oversight; subclassing `ArgumentParser` to remap its exit code would be over-engineering.

### Decision

**Proceed to verify.** No hand-back to Dev required. All Reviewer-rejected items resolved with substantive fixes (not just commentary). The implementation now honors both the original ACs AND the meta-rule that regression guards must actually guard.

**Handoff:** TEA verify (simplify + quality-pass on the new diff).

## TEA Assessment (verify phase — round-trip 1)

**Phase:** finish (round-trip 1)
**Status:** GREEN confirmed, simplify fan-out clean, no regressions

### Simplify Report (round-trip 1)

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 2 (`scripts/ollama_latency_check.py` post-rework, `tests/agents/test_ollama_backend_e2e_48_2.py` post-rework)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 4 findings (all low confidence) | EXIT_* could be IntEnum (script); `_load_latency_script` overlaps with `scripts/tests/test_playtest_split.py:_import_module` pattern (test); `isinstance(req.data, bytes)` runtime narrowing is a candidate shared helper if it spreads (test); script's error-handling hierarchy is intentionally isolated from production. All self-dismissed in the agent's own analysis. |
| simplify-quality | clean / 0 findings | All new docstrings (script `_measure_one_call`, inline `# noqa: BLE001`, module docstring exit-code section) are accurate against code reality. All new tests have substantive assertions; no vacuous claims. |
| simplify-efficiency | clean / 0 findings | EXIT_* constants justified (typo-prevention + documentation). Three-arm `except` split required by Reviewer's option (a). `_load_latency_script()` via `importlib.util` is the correct tool — `subprocess` cannot catch `SystemExit` in-process. `captured_requests` parameter avoids redundant hand-rolled closures. `_walk_for_key` recursion necessary for nested-key audit. |

**Applied:** 0 high-confidence fixes (none surfaced this round).

**Flagged for Reviewer (low-confidence, not auto-applied):**
- **`EXIT_* → IntEnum` (reuse, low):** Project has an `IntEnum` precedent in `.pennyfarthing/scripts/workflow/check.py:CheckStatus`. Converting the four `EXIT_*` constants in `ollama_latency_check.py` would align with that pattern. Cost: ~4 lines of code change + import. Benefit: marginal — script is small, single-file, never imported by anything. Reviewer may pull this trigger if they value consistency strictly; I judge it over-precision for a one-off operator tool.
- **`_load_latency_script()` vs `_import_module()` precedent (reuse, low):** Both helpers solve "load a non-package Python script for in-process testing." The `_import_module` variant in `scripts/tests/test_playtest_split.py` mutates `sys.path`; `_load_latency_script` uses the cleaner `importlib.util.spec_from_file_location` form. Unifying would mean writing one helper in a shared `test_utils.py` module — not warranted for two callers. The simplify-reuse agent agreed.

**Noted (low-confidence, observation only):**
- `_walk_for_key` recursion depth — re-flagged for completeness; same disposition as round-0 (kept; Reviewer deferred to TEA's judgment).
- The `isinstance(req.data, bytes)` runtime narrowing was introduced this round to satisfy pyright. It's a local test concern; flagging a "shared helper" only matters if the pattern spreads.

**Reverted:** 0.

**Overall:** simplify: clean (0 changes applied; 4 low-confidence findings flagged for Reviewer judgement).

### Quality Checks

- `ruff check` on changed files: All checks passed.
- `pyright` on changed files: 0 errors, 0 warnings.
- `pytest tests/agents/test_ollama_backend_e2e_48_2.py tests/agents/test_ollama_client.py tests/agents/test_llm_factory.py`: **34/34 passing**.

### Wider Project Test State (non-blocking, unchanged from verify round 0)

The same 5 pre-existing Victoria failures in `tests/genre/test_victoria_class_kits.py` remain. Still not introduced by 48-2 (the file is untouched on this branch). Already captured in Delivery Findings.

### Round-Trip Health

Sprint round-trip count: **1**. The Reviewer's rejection drove substantive improvements:
- Wiring test went from string-grep to behavioural identity check.
- AC1 stateless test now verifies the system+user merge that the implementation actually performs.
- Operator script no longer silently masks `ModuleNotFoundError` past `--help`.
- Negative `--baseline-claude-s` now fails loudly via `parser.error`.
- Exit-code taxonomy split for honest operator triage.
- Four prose lies in comments/docs corrected.

Net result: a sharper regression-guard test suite + a more diagnosable CLI tool, at the cost of one Reviewer round-trip. Worth it.

**Handoff:** To Reviewer for re-review (round 2).

## Subagent Results (round 2)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 19/19 tests, ruff/pyright clean, all round-1 fixes mechanically confirmed |
| 2 | reviewer-edge-hunter | No | skipped | N/A | Disabled via `workflow.reviewer_subagents.edge_hunter=false` |
| 3 | reviewer-silent-failure-hunter | No | skipped | N/A | Disabled |
| 4 | reviewer-test-analyzer | Yes | findings | 4 new | confirmed 4 (all Medium severity per Reviewer scale); all round-0 test findings verified resolved |
| 5 | reviewer-comment-analyzer | Yes | findings | 2 new | confirmed 1 (scope-out for future story), dismissed 1 low-confidence nit; all round-0 comment findings verified resolved |
| 6 | reviewer-type-design | No | skipped | N/A | Disabled |
| 7 | reviewer-security | No | skipped | N/A | Disabled |
| 8 | reviewer-simplifier | No | skipped | N/A | Disabled; TEA verify round-2 simplify fan-out already ran (clean) |
| 9 | reviewer-rule-checker | Yes | clean | 0 violations | All 6 round-0 violations resolved with line-level evidence; 1 advisory note on `--budget-multiplier` (operator-CLI, not security-rule territory) |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 5 confirmed (all Medium/Low severity per Reviewer scale), 1 dismissed, 0 deferred

## Rule Compliance (round 2 — full re-walk)

Rule-checker exhaustively verified all 13 python.md checks + 5 CLAUDE.md additionals against the post-rework diff:

| Rule | Instances | Compliant | Violations | Notes |
|------|-----------|-----------|------------|-------|
| #1 silent exceptions | 3 | 3 | 0 | Three explicit `except` arms in `main()`, broad `Exception` arm has `# noqa: BLE001` + rationale + stderr surfacing |
| #2 mutable defaults | 9 | 9 | 0 | All None/immutable defaults |
| #3 type annotations | 12 | 12 | 0 | **Round-0 violations on `_capture_http`, `fake()`, `_find_span` resolved** |
| #4 logging | 2 | 2 | 0 | Script intentionally uses `print(... stderr)` as CLI |
| #5 path handling | 7 | 7 | 0 | pathlib + `encoding="utf-8"` everywhere |
| #6 test quality | 15 | 15 | 0 | No vacuous assertions; wiring test now uses identity check (round-0 fix) |
| #7 resource leaks | 4 | 4 | 0 | No context-manager omissions |
| #8 unsafe deserialization | 2 | 2 | 0 | `importlib.util.exec_module` loads a fixed repo-internal path; not untrusted input |
| #9 async pitfalls | 5 | 5 | 0 | `time.sleep()` inside `_FakeHttpResponse.read()` runs in `asyncio.to_thread()` worker |
| #10 import hygiene | 5 | 5 | 0 | **Round-0 violation (late `build_llm_client` import) resolved** — now at module top level |
| #11 input validation | 5 | 5 | 0 | **Round-0 violation (negative baseline) resolved** — `parser.error()` for ≤ 0. Advisory: `--budget-multiplier` has no range check (non-security; operator-only CLI) |
| #12 dependency hygiene | 1 | 1 | 0 | No new deps |
| #13 fix-introduced regressions | 6 | 6 | 0 | Round-1 fixes reviewed against rules #1-12; no new violations |
| CLAUDE.md No Silent Fallbacks | 4 | 4 | 0 | **Round-0 violation (late import masks ModuleNotFoundError) resolved** |
| CLAUDE.md No Stubbing | 3 | 3 | 0 | — |
| CLAUDE.md Verify Wiring | 1 | 1 | 0 | **Round-0 violation (source-grep wiring test) resolved** — `assert resolved is factory_under_test` identity check |
| CLAUDE.md OTEL Observability | 5 | 5 | 0 | AC2 + AC3 span tests in place |
| CLAUDE.md No half-wired features | 2 | 2 | 0 | `build_llm_client` wired in `create_app` + wiring test confirms |

**Aggregate:** 91 items checked, 0 violations, all 6 round-0 violations resolved.

## Devil's Advocate (round 2)

The Queen of Hearts paces again. *Could this still be broken?*

The wiring test went from "string `else build_llm_client` appears somewhere in app.py" to `app.state.claude_client_factory is build_llm_client`. Could the new version pass for the wrong reason? Only if `app.state.claude_client_factory` were somehow the literal function object `build_llm_client` while the actual runtime used a different callable. That would require `app.py` to store `build_llm_client` on state but use a different factory elsewhere — which would itself be a bug, but a different bug than the wiring test claims to guard. The test is narrow but honest about what it tests. Acceptable.

The AC1 stateless body test now asserts a single user-role message containing both system and user text via substring inclusion. Could it pass for the wrong reason? If `ollama_client.py` started sending the system text alone in a single user message and dropping the user_message, the `user_text in only_message["content"]` assertion would fail. If it sent only user_message dropping system, `system_text in only_message["content"]` would fail. If it sent `[system, user]` two-role messages, `len(messages) == 1` would fail. The three assertions cover the three regressions that matter. Tight.

The negative-baseline guard — the test_analyzer correctly noted the zero case lacks an `exc_info.value.code != 0` assertion. A regression to `sys.exit(0)` for zero would slip through. *But* such a regression would be very strange to introduce, and the `parser.error()` call in Dev's implementation explicitly raises `SystemExit(2)` not `SystemExit(0)`. The test as written catches the realistic regression (failing to call `parser.error()` at all, which would let `main()` proceed to network calls and return 1/2). The missed `code != 0` check is a polish item, not a load-bearing gap.

The AC4 source-scan self-defeat — *this* is the cleverest finding the Queen has heard all night. `test_ac4_ollama_client_source_has_no_num_ctx_reference` greps `ollama_client.py` for the literal string `num_ctx`. Its docstring tells future maintainers that comments referencing this test by name are fine — but the test's own name contains `num_ctx`. A diligent maintainer who follows the docstring's guidance would break the test. The test currently passes because no such comment exists today. It's a documentation foot-gun, not a runtime bug. The three behavioral body-shape tests already cover the regression. The static scan is belt-and-suspenders with a self-inconsistent docstring. Worth a Medium-severity flag for follow-up, but not blocking.

What else might break? The pre-existing 5 Victoria failures remain pre-existing. The `--budget-multiplier` lacks a range guard — but that's operator-only impact (a negative multiplier would produce a wrong verdict, not a security hole). The `subprocess.run` and `importlib.util.exec_module` paths in tests both load fixed repo-internal targets — not user input. The `time.sleep()` in `_FakeHttpResponse.read()` runs in a worker thread via `asyncio.to_thread` — correct per Ollama's call structure.

The Queen sets down the pipe. *No more heads need rolling tonight.*

## Reviewer Assessment (round 2)

**Verdict:** APPROVED
**Round-Trip Count:** 1 (Dev's first rework cycle was successful)

### Round-0 Findings — Resolution Confirmed (with line-level evidence)

| Severity | Round-0 Finding | Resolution Line | Verified |
|----------|-----------------|-----------------|----------|
| [HIGH] | Wiring test was source-text grep | `test:524-545` — `assert resolved is factory_under_test` identity check | ✓ |
| [HIGH] | AC1 stateless never verified system+user merge | `test:349-420` — `captured_bodies` inspected, single user-role entry asserted with both substrings | ✓ |
| [HIGH] | Late import defers ModuleNotFoundError past --help | `ollama_latency_check.py:62-63` — `from sidequest.agents.* import ...` at module top | ✓ |
| [HIGH] | `--baseline-claude-s` accepts negatives | `ollama_latency_check.py:156-157` — `parser.error()` for ≤ 0 | ✓ |
| [MEDIUM] | `_measure_one_call` lying docstring | `ollama_latency_check.py:100-108` — rewritten to honest "sole assignment, not defence-in-depth" | ✓ |
| [MEDIUM] | As-installed doc elides send_stateless merge | `docs/.../as-installed.md` `/api/chat` row — parenthetical added | ✓ |
| [MEDIUM] | Inline `# noqa: BLE001` false distinction | `ollama_latency_check.py:171-176` — false-distinction sentence removed | ✓ |
| [MEDIUM] | Exit-code 2 conflated config/transport | `ollama_latency_check.py:161-176` — Reviewer's option (a): `(UnknownModel, UnknownBackend) → 3`, `OllamaClientError → 2`, `Exception → 2` | ✓ |
| [MEDIUM] | AC3 floor `delay * 0.5` too loose | `test:662` — tightened to `delay * 0.8` | ✓ |
| [MEDIUM] | URL test private-slot coupling | `test:495-498` — observable `req.full_url` assertion | ✓ |
| [MEDIUM] | Missing `UnknownBackend` negative test | `test:502-515` — new `test_ac1_factory_raises_unknown_backend_on_bad_value` | ✓ |
| [MEDIUM] | LocalDM stale docstring | `test:209-213` — "dormant per 2026-04-28 spec" | ✓ |
| [LOW] | Missing return type annotations | `_capture_http :310`, `fake() :316`, `_find_span :553` | ✓ |
| [LOW] | AC4 stateless redundancy | Reviewer previously dismissed | — |

**All 14 round-0 items addressed. Production code untouched (audit conclusion stands).**

### New Findings This Round (all Medium/Low severity — non-blocking)

| Source | Severity | Issue | Location | Recommended Follow-up |
|--------|----------|-------|----------|----------------------|
| `[TEST]` | [MEDIUM] | AC4 static source-scan test has a self-inconsistent docstring: it instructs future maintainers to "reference this test by name" in comments, but the test's own name (`test_ac4_ollama_client_source_has_no_num_ctx_reference`) contains the bare token `num_ctx` being scanned for. A diligent maintainer following the guidance would break the test. Currently passes because no such comment exists. | `tests/agents/test_ollama_backend_e2e_48_2.py:635-650` | Either (a) rename the test to omit `num_ctx`, OR (b) rewrite the docstring to drop the self-defeating recommendation (and rely on the three behavioral body-shape tests as the canonical guard), OR (c) scope the source-scan to non-comment lines. Not blocking — the behavioral guards already cover the regression. |
| `[TEST]` | [MEDIUM] | `test_ac3_script_rejects_zero_or_negative_baseline_claude_s` zero-case lacks an explicit `exc_info.value.code != 0` assertion (the negative case has one). A regression to `sys.exit(0)` for zero would slip through. | `test:~790` | Add `assert exc_info.value.code != 0` to the zero-case `pytest.raises` block. Tiny diff. |
| `[TEST]` | [LOW] | `_load_latency_script()` hardcodes one script path; the existence test accepts two. If the script moved to the orchestrator's `scripts/`, the existence test would still pass while in-process tests would error. | `test:~711` | Mirror the two-path search OR collapse to a single canonical location. |
| `[TEST]` | [LOW] | Hermeticity: if the baseline-validation guard regressed from `<= 0` to `< 0`, the zero case would hit `asyncio.run` → real network. | `test:~790` | Patch `asyncio.run` to raise a sentinel in the sub-tests. |
| `[DOC]` | [MEDIUM] (scope-out) | `OllamaClient.send_stateless` docstring (`ollama_client.py:176`) doesn't mention the user-role merge, even though the new test/doc commentary explicitly documents it. The production docstring is the only place that omits the contract. | `sidequest/agents/ollama_client.py:176-186` (NOT in this story's diff) | Out of 48-2's scope (touches production code from 48-1). File a follow-up story to update the production docstring. Captured below as a Delivery Finding. |
| `[DOC]` | [LOW] (dismissed) | `_load_latency_script()` docstring "script lives in `sidequest-server/scripts/`" — accurate as filesystem fact, but the function resolves `repo_root` via `parents[3]` from the test file, which is the orchestrator root. Minor framing ambiguity. | `test:~711` | Dismissed — the path math is correct and the docstring is technically accurate. |
| `[RULE]` | (advisory) | `--budget-multiplier` accepts arbitrary floats with no range check; a negative multiplier would produce a wrong verdict. | `ollama_latency_check.py:91-96` | Not a security-rule violation (operator-only CLI), but consistent with the baseline guard. Optional follow-up: add the same `parser.error()` pattern. |

**Tag inventory** (gate requires all 8):
- `[EDGE]` — N/A (subagent disabled; edge-flavour overlap covered by `[TEST]` zero-case finding above)
- `[SILENT]` — N/A (subagent disabled; silent-failure-flavour overlap covered by `[RULE]` — late-import fix already verified resolved)
- `[TEST]` — 4 new findings: AC4 source-scan self-inconsistency, zero-case assert gap, `_load_latency_script` path divergence, hermeticity
- `[DOC]` — 2 new findings: scope-out on `OllamaClient.send_stateless` docstring, dismissed `_load_latency_script` framing
- `[TYPE]` — N/A (subagent disabled; type-flavour all resolved in round-0 fixes per rule-checker)
- `[SEC]` — N/A (subagent disabled; `--budget-multiplier` advisory captured under `[RULE]`)
- `[SIMPLE]` — N/A (subagent disabled; TEA verify round-2 simplify fan-out clean)
- `[RULE]` — 0 new violations (all 6 round-0 violations resolved with evidence); 1 advisory on `--budget-multiplier`

### Decision

**APPROVED for merge.** All round-0 [HIGH] and [MEDIUM] findings resolved with line-level evidence. The 5 new findings this round are all Medium/Low severity (test-craft polish + 1 scope-out for a future story). The story has substantively improved through the rework cycle: regression guards now actually guard, the operator script fails loudly on misconfiguration, comments match code reality.

**Handoff:** To SM for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): Story context files (`sprint/context/context-story-48-2.md`, `context-epic-48.md`) were never generated by sm-setup despite the gate's recovery_config calling for it. The `pf validate context-story` command also returned `Unknown validator(s)` — the validator name appears wrong in the CLI. Affects `pf validate` and `sm-setup` recovery pipeline (`gates/sm-setup-exit`). Session file's Story Context section was rich enough to substitute for missing context, so RED phase proceeded.
  *Found by TEA during test design.*
- **Improvement** (non-blocking): The 48-1 audit-conclusion note in `docs/superpowers/specs/2026-05-06-local-qwen-code-editor-as-installed.md:60` describes the OllamaClient num_ctx follow-up in prospective terms ("Worth a follow-up when SideQuest's Ollama backend is exercised"). For story 48-2 to be archivable, that note should be updated in place to record the AC4 conclusion (no per-request num_ctx found, regression guards in place). Test `test_ac4_audit_outcome_documented_in_as_installed_spec` enforces this. Affects `docs/superpowers/specs/2026-05-06-local-qwen-code-editor-as-installed.md` (append an "Audit conclusion — story 48-2" subsection).
  *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): Manual playtest evidence for AC1 ("one full playtest turn through the Ollama backend") and AC3's numeric ≤3x baseline verdict still need to be captured by the operator on the M3 Ultra (where Ollama actually runs). Ollama is not reachable from the implementing machine (`curl http://localhost:11434/api/tags` → HTTP 000). The infrastructure is now in place to capture the evidence: run `python sidequest-server/scripts/ollama_latency_check.py --baseline-claude-s <N>` against a live Ollama, paste the elapsed/ratio/verdict line into this finding, and ideally also paste one `agent.call.session` span snapshot from the GM panel showing `agent.backend="ollama"`. Affects `.session/48-2-session.md` / archive (Delivery Findings → append operator-captured evidence) before story finish.
  *Found by Dev during implementation.*
- **Improvement** (non-blocking): The operator latency-check script depends on a Claude baseline number that does not exist anywhere committed in the repo — the operator must measure it themselves or pull a figure from playtest logs. A natural follow-up (small, well-scoped) is a one-time "freeze a Claude baseline" run that writes `sidequest-server/data/claude_baseline_seconds.json` (or similar) so future runs of `ollama_latency_check.py` can default to it. Out of scope for 48-2; worth tracking. Affects future story (or 48-2 stretch goal): commit a Claude-baseline number measured on a representative narrator turn.
  *Found by Dev during implementation.*
- **Question** (non-blocking): The story's "Acceptance: ... fixed if present (separate PR if needed)" clause assumes the audit might find a fix. It didn't — current `OllamaClient` is clean. No follow-up PR needed for the audit itself; the regression guards in `tests/agents/test_ollama_backend_e2e_48_2.py` cover the future-regression case. Reviewer should confirm this interpretation matches the story author's intent. Affects: this story's review (Reviewer decision).
  *Found by Dev during implementation.*

### TEA (test verification)
- **Gap** (non-blocking): `just check-all` reports 5 pre-existing test failures in `tests/genre/test_victoria_class_kits.py` (`test_victoria_loads`, `test_victoria_has_seven_class_kits`, `test_victoria_kit_items_exist_in_inventory`, `test_victoria_doctor_kit_guarantees_signature_items`, `test_victoria_doctor_chargen_produces_signature_items_end_to_end`). Confirmed not introduced by 48-2: `git diff develop HEAD -- tests/genre/test_victoria_class_kits.py` is empty; the test file was last touched in story 49-4 (`3ebbf0e`). Affects `sidequest-server/tests/genre/test_victoria_class_kits.py` and likely the Victoria genre pack data the tests load. Not blocking 48-2 — the failures predate this branch — but should be triaged in a separate story. Suggested follow-up: spawn `/patch` or file a new story to investigate.
  *Found by TEA during test verification.*
- **Improvement** (non-blocking): `pf check` doesn't exist as a `pf` subcommand on this install (`Error: No such command 'check'.` from `pf check`). The TEA verify workflow documents this as the project-agnostic regression check entry point. Either the docs are aspirational or this install is missing the `check` group. The fallback `just check-all` works (and is what I used). Affects `pennyfarthing-dist/agents/tea.md` (or the `pf` CLI itself if `check` was meant to be wired). Not 48-2's problem — just a pipeline-tooling note.
  *Found by TEA during test verification.*

### Reviewer (code review)
- **Gap** (blocking for THIS story): Two regression-guard tests that don't actually guard (`test_wiring_create_app_default_client_factory_is_build_llm_client` is a source-text grep; `test_ac1_factory_ollama_send_stateless_roundtrips_end_to_end` never captures the outbound `messages` body). Affects `tests/agents/test_ollama_backend_e2e_48_2.py` — both tests need real behavioural assertions before merge. Project rule "Verify Wiring, Not Just Existence" is directly violated by the wiring test.
  *Found by Reviewer during code review.*
- **Gap** (blocking for THIS story): Operator script defers `ModuleNotFoundError` past `--help` and accepts negative `--baseline-claude-s` values. Affects `scripts/ollama_latency_check.py` — move import to top level, add post-parse baseline validation.
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking, general): Reviewer subagent toggles disable `edge_hunter`, `silent_failure_hunter`, `type_design`, `security`, `simplifier` (5 of 9). The rule-checker happened to surface most of those flavours this round, but the coverage is fragile — if rule-checker had been disabled too, the `--baseline-claude-s` and late-import findings would have been missed by an all-disabled-thematic-subagents review. Affects `.pennyfarthing/config.local.yaml` (consider re-enabling some thematic subagents, or document the reliance on rule-checker as backstop). Not 48-2's problem.
  *Found by Reviewer during code review.*

### TEA (test rework — round-trip 1)
- No new upstream findings during rework. Reviewer's verdict was acted on directly; no additional spec gaps surfaced.
  *Found by TEA during test rework.*

### Dev (green rework — round-trip 1)
- No new upstream findings during rework. All Reviewer-flagged items resolved per the resolution table in the Dev Assessment.
  *Found by Dev during implementation.*

### TEA (test verification — round-trip 1)
- No new upstream findings during verify round 1. Simplify fan-out clean (efficiency + quality clean; reuse 4 low-confidence findings all dismissed in-pass). No regressions in adjacent tests.
  *Found by TEA during test verification.*

### Reviewer (code review — round 2)
- **Improvement** (non-blocking, follow-up story): `OllamaClient.send_stateless` docstring in `sidequest-server/sidequest/agents/ollama_client.py:176-186` doesn't mention that it merges `system_prompt` into the user message — the production docstring is now the only place that omits this contract (the test docstring, audit doc, and module-level docstring all document it). File a small follow-up story to update the docstring; out of 48-2's scope since `ollama_client.py` is untouched by this story.
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking, polish): Four test-craft items flagged as non-blocking in the Reviewer Assessment table — the AC4 source-scan docstring self-inconsistency is the most worth addressing; the other three are minor robustness improvements. Affects `tests/agents/test_ollama_backend_e2e_48_2.py` (lines `~635-650`, `~790`, `~711`). Could be batched into a single drive-by patch or deferred.
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking, advisory): `--budget-multiplier` in `scripts/ollama_latency_check.py:91-96` lacks the same `parser.error()` guard the `--baseline-claude-s` argument received. Operator-only impact (wrong verdict, not security). Optional follow-up if any operator hits the foot-gun.
  *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **AC1 "full playtest turn" interpreted as factory→client→send_stateless roundtrip with mocked HTTP, not a live narrator end-to-end test**
  - Spec source: epic-48.yaml AC1 — "one full playtest turn through the Ollama backend"
  - Spec text: "Acceptance: one full playtest turn through the Ollama backend"
  - Implementation: Test exercises `build_llm_client()` → `OllamaClient` → `send_stateless()` (the narrator's canonical post-ADR-098 path) with a fake HTTP responder. The "full narrator turn" pipeline (orchestrator → prompt build → LLM call → state patch) is NOT covered automatically; it stays a manual playtest observation captured as evidence in the session/archive.
  - Rationale: A genuine end-to-end narrator turn requires either a live Ollama (CI-incompatible) or extensive scaffolding to fake the orchestrator's state. The send_stateless roundtrip is the narrowest layer that proves env-var → factory → wire-format → response chain works; the remaining manual playtest is what AC1 actually buys in production.
  - Severity: minor
  - Forward impact: Dev must perform a manual playtest with `SIDEQUEST_LLM_BACKEND=ollama` and a real Ollama instance, then record the evidence (turn timing, OTEL span snapshot) in the session file before review.

- **AC3 latency budget tested as "duration is observable + comparison script exists", not as an asserted numeric threshold**
  - Spec source: epic-48.yaml AC3 — "latency budget within 3x of Claude baseline"
  - Spec text: "latency budget within 3x of Claude baseline"
  - Implementation: One test asserts the OTEL span captures elapsed time for an Ollama request (so the budget is measurable). A second test asserts `scripts/ollama_latency_check.py` exists and responds to `--help`. The numeric `≤3x baseline` is not enforced in CI.
  - Rationale: There is no recorded Claude baseline number in this repo (would need to be captured first), and a CI-side latency assertion would be either trivially fast (mocked) or unreliable (real network). Operator runs the script during playtest; result lands in session evidence.
  - Severity: minor
  - Forward impact: Dev creates the latency-check script; operator captures the manual ≤3x comparison during playtest.

- **AC4 audit conclusion enforced via a doc-update test, not a session-archive test**
  - Spec source: epic-48.yaml AC4 — "OllamaClient num_ctx pattern reviewed; fixed via Modelfile load-time config if per-request pattern is present"
  - Spec text: "Acceptance: ... OllamaClient num_ctx pattern reviewed and fixed if present (separate PR if needed)"
  - Implementation: `test_ac4_audit_outcome_documented_in_as_installed_spec` requires `docs/superpowers/specs/2026-05-06-local-qwen-code-editor-as-installed.md` to reference story 48-2 and contain a written conclusion (e.g., "no per-request" / "audit conclusion"). The as-installed doc already flags the OllamaClient audit as a follow-up at line 60, so this is the natural home.
  - Rationale: The session file is archived to `sprint/archive/` after finish — testing against an archive-bound location is brittle. Updating the standing as-installed doc keeps the audit conclusion discoverable by future maintainers without depending on the sprint lifecycle.
  - Severity: minor
  - Forward impact: Dev must append an "Audit conclusion — story 48-2" subsection to the as-installed doc before tests go GREEN.

### Dev (implementation)
- **Latency-check script committed to `sidequest-server/scripts/` (not orchestrator `scripts/`)**
  - Spec source: TEA handoff note in this session file ("the test accepts either `sidequest-server/scripts/` or orchestrator `scripts/` — pick `sidequest-server/scripts/`")
  - Spec text: TEA explicitly recommended the server location.
  - Implementation: Created `sidequest-server/scripts/ollama_latency_check.py`. Followed TEA's recommendation; the script is server-specific (imports `sidequest.agents.llm_factory.build_llm_client`).
  - Rationale: Matches TEA's recommendation and keeps the script colocated with the code it exercises. Orchestrator `scripts/` is reserved for cross-repo workflow tooling.
  - Severity: none — chose the recommended option
  - Forward impact: none

- **AC4 doc audit conclusion committed directly to orchestrator `main`, not to a feature branch**
  - Spec source: SM Assessment in this session file ("Repos: server only. Single-repo scope")
  - Spec text: "Single-repo scope — `sidequest-server/sidequest/agents/ollama_client.py` is the audit target; OTEL plumbing and degraded-path tests also land in server."
  - Implementation: The AC4 doc update (`docs/superpowers/specs/2026-05-06-local-qwen-code-editor-as-installed.md`) landed in the orchestrator repo on `main` (commit `d4d95ec`), not in `sidequest-server`. SM had only created a feature branch in `sidequest-server/`. The orchestrator pattern observed in recent history (`74459f1 chore(sprint): complete 45-46`) commits doc/sprint changes directly to `main`.
  - Rationale: The audit conclusion's natural home was the existing as-installed spec (TEA deviation choice), which lives in the orchestrator. Creating a parallel orchestrator feature branch for a single 14-line doc append would have been ceremony out of proportion to the change. Existing orchestrator pattern is direct-to-main for doc-only commits.
  - Severity: minor
  - Forward impact: This story's PR review surface is split between two repos. Reviewer needs to look at PR (or branch) `feat/48-2-validate-ollama-backend-e2e` in `sidequest-server` AND commit `d4d95ec` on orchestrator `main`. Both are referenced in the Dev Assessment table.

- **No Claude latency baseline committed alongside the AC3 script**
  - Spec source: epic-48.yaml AC3 — "latency budget within 3x of Claude baseline"
  - Spec text: "Latency must be ≤3x Claude baseline (narrator typically ~5-8s on Claude, so target ≤15-24s on Ollama/Qwen7B)"
  - Implementation: The latency-check script requires the operator to supply `--baseline-claude-s` at run time. No baseline number is committed to the repo.
  - Rationale: Committing a fixed Claude latency number without an empirical measurement run would be invented data. The session-file context lists "5-8s" as a rough range, not a measurement. Better to require an explicit operator-supplied value (or build the baseline-freezing step as a follow-up story) than commit a guess.
  - Severity: minor
  - Forward impact: Operator must measure or remember a Claude baseline when invoking the script. Captured as a Delivery Finding (Improvement, non-blocking).

### TEA (test verification)
- No deviations from spec during verify phase. One high-confidence simplify finding was auto-applied as a pure documentation correction (commit `d254694`); two medium-confidence findings flagged for Reviewer judgement rather than auto-applied; one low-confidence finding dismissed in favour of the Architect's prior assessment.

### TEA (red rework — round-trip 1)
- No new deviations from spec during rework. All Reviewer-flagged test issues were resolved directly per the Reviewer Assessment's `Fix Required` column. Three undisputed Reviewer findings were translated into new RED tests rather than fixed prose-only (Dev's scope: top-level import, negative-baseline validation, as-installed merge note). Two pre-existing TEA deviations (AC1 stateless interpretation, AC3 latency interpretation) remain in force — the Reviewer accepted them in the audit.

### TEA (test verification — round-trip 1)
- No deviations from spec during verify round 1. Simplify fan-out surfaced 4 low-confidence findings; none warranted code changes. Verify round 0 deviation policy carried forward unchanged (no auto-apply for medium/low).

### Dev (green rework — round-trip 1)
- **Exit-code taxonomy split, not deferred** (Reviewer option (a) chosen over (b))
  - Spec source: Reviewer Assessment, [MEDIUM] finding on exit-code conflation, "Option (a) preferred; (b) acceptable if the operator only ever reads stderr."
  - Spec text: "Either (a) catch `OllamaClientError` (network/transport) for exit 2 and a separate `(UnknownModel, UnknownBackend)` for exit 3 with a documented 'configuration error' label, OR (b) update docstring and epilog to honestly say exit 2 is 'any pre-verdict failure' rather than implying unreachability."
  - Implementation: Chose option (a). Caught `(UnknownModel, UnknownBackend)` first → returns `EXIT_CONFIG_ERROR (3)`, then `OllamaClientError` → returns `EXIT_OLLAMA_TRANSPORT (2)`, then bare `Exception` → also returns `EXIT_OLLAMA_TRANSPORT (2)` with an "unexpected error" stderr label. Module docstring + argparse epilog updated to document the new taxonomy.
  - Rationale: The split is the Reviewer-preferred option, gives scripted callers a real signal to triage on, and the stderr labels remain operator-friendly even without consulting exit codes. The cost is two extra imports (`UnknownModel`, `UnknownBackend`) at module level — trivial given they're already in `sidequest.agents.*`.
  - Severity: minor — improves operator semantics, no behavior change for happy path.
  - Forward impact: any scripted caller that previously checked `exit_code == 2` to detect "Ollama down" can now distinguish from configuration errors. No existing in-repo callers exist (the script is new), so no migration concern.

- **`isinstance(req.data, bytes)` runtime assertion added to test helper**
  - Spec source: pyright type-check failure introduced by TEA's tightened `Callable[[Request], _FakeHttpResponse]` annotation on `_capture_http`.
  - Spec text: TEA's `_capture_http` return-type annotation pushed `req.data` from `Any` to urllib's `_DataType` union, which pyright then refused to pass to `json.loads`.
  - Implementation: Added `assert isinstance(req.data, bytes), …` before `json.loads(req.data)` to narrow the union for both pyright and runtime safety.
  - Rationale: `OllamaClient._post_generate` / `_post_chat` always serialize their bodies via `json.dumps(...).encode("utf-8")`, so the bytes constraint always holds in practice. The runtime assert documents that contract and gives a useful failure message if the contract ever breaks. Alternative (`# type: ignore[arg-type]`) would have hidden the assumption.
  - Severity: trivial — runtime cost is negligible, the assert is true-by-construction in all current code paths.
  - Forward impact: none.

### Reviewer (audit)

Audit of prior agents' deviation entries:

- **TEA — AC1 stateless roundtrip as testable layer + manual playtest deferred** → ✓ ACCEPTED by Reviewer: the interpretation is sound and explicitly disclosed; however the assertion set must be tightened to actually verify the stateless body collapse (see Reviewer Assessment [HIGH] item). The deviation framing stands; the test implementation falls short of what the framing promised.
- **TEA — AC3 latency budget as "duration observable + comparison script exists"** → ✓ ACCEPTED by Reviewer: the operator-script pattern is the right call for CI-unfriendly latency assertions. Tighten the duration floor (Medium finding) but the architectural deviation is sound.
- **TEA — AC4 audit conclusion via doc-update test** → ✓ ACCEPTED by Reviewer: the as-installed doc IS the right home for the audit conclusion. The doc's prose accuracy needs one parenthetical correction (the `send_stateless` merge elision — Medium finding).
- **Dev — latency-check script in `sidequest-server/scripts/`** → ✓ ACCEPTED by Reviewer: correct location.
- **Dev — AC4 doc commit on orchestrator `main` rather than feature branch** → ✓ ACCEPTED by Reviewer: matches prior orchestrator pattern (74459f1, etc.). PR review surface split is non-blocking; the orchestrator commit is reviewed inline here.
- **Dev — no Claude baseline number committed** → ✓ ACCEPTED by Reviewer: committing an empirically un-measured number would be worse than requiring operator input.

#### Round 2 audit (post-rework)

- **TEA — wiring test as identity check via `app.state.claude_client_factory`** → ✓ ACCEPTED by Reviewer: round-1 rework adopted the recommended `is` check; test now verifies behaviour, not source-text.
- **TEA — AC1 stateless body shape verification** → ✓ ACCEPTED by Reviewer: round-1 rework added the captured-body assertions per the Fix Required column.
- **TEA — AC3 floor tightened to `delay * 0.8`** → ✓ ACCEPTED by Reviewer.
- **TEA — URL test moved to observable `req.full_url`** → ✓ ACCEPTED by Reviewer.
- **TEA — UnknownBackend negative test added** → ✓ ACCEPTED by Reviewer.
- **TEA — LocalDM dormant docstring** → ✓ ACCEPTED by Reviewer.
- **TEA — `_capture_http` / `_find_span` return type annotations** → ✓ ACCEPTED by Reviewer.
- **Dev — exit-code taxonomy split (option (a) over (b))** → ✓ ACCEPTED by Reviewer: the chosen option was the Reviewer's preferred resolution.
- **Dev — `isinstance(req.data, bytes)` runtime assertion in `_capture_http`'s fake** → ✓ ACCEPTED by Reviewer: defensive narrowing for pyright is a clean trade vs `# type: ignore`.

Undocumented deviations Reviewer found:

- **Wiring test is a source-text grep, not a behavioural assertion**
  - Spec source: CLAUDE.md ("Verify Wiring, Not Just Existence") and the test's own name (`test_wiring_create_app_default_client_factory_is_build_llm_client`).
  - Spec text: "Tests passing and files existing means nothing if the component isn't imported, the hook isn't called, or the endpoint isn't hit in production code. Check that new code has non-test consumers."
  - Implementation: Test reads `app.py`'s source as text and asserts two string literals appear in it. The test's docstring acknowledges this is a "source-level check" because "introspecting the resolved default is harder," but the project rule does not exempt difficulty.
  - Rationale: TEA/Dev judged source-text grep acceptable as a documented trade-off.
  - Severity: HIGH — the project rule explicitly forbids existence-only wiring checks; this is the canonical example.
  - Forward impact: Test must be replaced with a behavioural check (`assert app.state.claude_client_factory is build_llm_client`) before merge. The deviation is undocumented in TEA's section; logging here.

- **AC1 stateless test does not verify the system+user message collapse promised by `send_stateless`'s contract**
  - Spec source: TEA's own AC1 deviation framing ("`send_stateless` … is the narrowest layer that proves env-var → factory → wire-format → response chain works").
  - Spec text: TEA promised the test proves the "wire-format" chain. It does not — the request body is never captured or asserted against.
  - Implementation: Test asserts response shape but never inspects the outbound `messages` array.
  - Rationale: The framing in TEA's deviation is more generous than what the test actually verifies. The shortfall was not separately logged.
  - Severity: HIGH — undermines the regression-guard premise.
  - Forward impact: Add body capture + `messages` shape assertion to `test_ac1_factory_ollama_send_stateless_roundtrips_end_to_end`. Same fix-bundle as the wiring test.

### Architect (reconcile)

#### Verification of prior deviation entries (round 0 + round 1)

All TEA/Dev/Reviewer deviation entries were re-checked against the spec sources they cite. Findings:

- **All cited spec paths exist:** `sprint/epic-48.yaml` (AC list), `docs/superpowers/specs/2026-05-06-local-qwen-code-editor-design.md`, `docs/superpowers/specs/2026-05-06-local-qwen-code-editor-as-installed.md`, `CLAUDE.md` ("Verify Wiring, Not Just Existence"), the session file's TEA/Reviewer Assessments, and `sidequest-server/CLAUDE.md` are all present.
- **Quoted spec text is accurate:** TEA's three AC quotes match `sprint/epic-48.yaml` lines 75-82 verbatim. Reviewer's CLAUDE.md quote ("Tests passing and files existing means nothing if the component isn't imported…") matches the orchestrator `CLAUDE.md` source. Dev's Reviewer-instruction quotes match the round-0 Reviewer Assessment table.
- **Implementation descriptions match code reality:** Spot-checked at the diff head (commits `455bf56`, `06b8424`, `d7bf993`, `d254694`, `a9b3419`, `054ab64`). All "Implementation:" lines accurately describe what shipped — the wiring `is` check, the `captured_bodies` assertions, the top-level imports, the `parser.error()` guard, the three-arm exit-code split, the as-installed merge parenthetical, and the four prose corrections all match the code that landed.
- **Forward impacts accurately reflect sibling-story scope:**
  - Epic 48 has three remaining backlog stories: 48-3 (sidequest-train + GGUF deployment, 13 pts), 48-4 (A/B eval harness, 5 pts). Neither depends on 48-2's test-interpretation choices.
  - The manual-playtest deferral (AC1 narrator turn, AC3 numeric ≤3x verdict) is captured as an operator obligation, not a code dependency. 48-3 cannot begin until 48-2's manual playtest produces a baseline measurement against the live Ollama instance — but that's an operational gate, not a test-suite gate.
  - The scope-out `OllamaClient.send_stateless` docstring finding (Reviewer round 2) is a clean follow-up story candidate; no sibling story currently depends on the docstring's content.
- **All 6 required deviation fields present and substantive:** No placeholder text observed in any entry. The TEA round-0 entries each carry the full 6-field shape; Dev round-0 and round-1 entries are full-shape; Reviewer audit lines correctly use the compact stamp format (✓ ACCEPTED / ✗ FLAGGED) per the deviation-format guide.

#### Missed Deviations

After a full re-walk of the diff against the four spec sources (`epic-48.yaml`, design spec, as-installed spec, sibling story ACs):

- **No additional deviations found.**

The Reviewer's two round-0 undocumented-deviation entries (wiring test as source-grep; AC1 stateless missing body verification) were both resolved by round-1's rework, and the Reviewer's round-2 audit lines stamp the rework-deviation entries. The TEA verify-phase rounds correctly logged "no deviations" for both passes since no deviations were introduced during simplify fan-out. Dev's round-1 entries cover the three substantive trade-offs (exit-code split option (a), the runtime `isinstance` narrowing for pyright, and the operator-side Claude-baseline-not-committed call) — none of which were caught by Reviewer as missed.

#### AC Deferral Verification

No ACs DESCOPED. Two ACs have **operator-deferred portions** (not test-deferred — the tests are GREEN; the operator must perform a manual playtest on the M3 Ultra to capture the live evidence):

| AC | Test Coverage | Operator-Deferred Portion | Status |
|----|---------------|---------------------------|--------|
| AC1 | 4 automated tests (env→factory→client→send_stateless roundtrip + body-shape verification + multi-turn + UnknownBackend negative) | A "full playtest turn" through the narrator pipeline on a live Ollama instance | OPERATOR-OBLIGATION (recorded in Delivery Findings) |
| AC2 | 4 automated tests (OTEL `agent.backend="ollama"` on all three OllamaClient surface methods + factory-built path) | None | DONE |
| AC3 | 1 automated test (span duration observable via OTEL) + 2 RED-fix tests now GREEN (script exists + import at module top + negative-baseline guard) | The numeric ≤3x Claude baseline verdict (operator runs `scripts/ollama_latency_check.py --baseline-claude-s <N>` against live Ollama) | OPERATOR-OBLIGATION (recorded in Delivery Findings) |
| AC4 | 4 automated tests (3 body-shape regression guards + 1 source-scan + 1 doc-conclusion check + 1 merge-note check) + audit conclusion in as-installed spec | None | DONE |

Reviewer's round-2 verdict acknowledges the operator-obligation pattern is the correct interpretation of "manual playtest" ACs in this project (consistent with prior 48-1 manual-validation pattern and Keith's playgroup operational reality).

**Handoff:** To SM for finish-story.