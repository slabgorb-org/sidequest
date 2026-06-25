---
story_id: "159-1"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 159-1: Extract sidequest-seat-core (schema-generic backends + persona axes)

## Story Details
- **ID:** 159-1
- **Jira Key:** (none — Jira not enabled for this project)
- **Workflow:** tdd
- **Stack Parent:** none (build order root)
- **Repos:** sidequest-seat-core (new repo, created in Task 1)

## Context & Scope

This story **creates a brand-new charter-neutral package** that will be shared by `sidequest-understudy` (test harness) and the future companion (ship). The package holds **data models + model backends only** — no prompts, no naivety, no WebSocket, no browser.

**Plan A scope (Tasks 1–7):**
1. Scaffold `sidequest-seat-core` package (pyproject, src layout, smoke test)
2. Core primitives: `Message`, `ModelError`, `DecideResult`, `parse_structured`, `StructuredModel` protocol, `FakeStructuredModel`
3. `AnthropicModel` — generic over output model, with prompt caching; meters true input volume
4. `OllamaModel` — generic over output model (JSON `format`)
5. `ClaudePModel` — generic, schema-in-prompt; **MUST strip API keys** from child env (bills the plan, fails loud)
6. `make_model` factory
7. Persona axes — `SeatAxes`, `Role`, `RoleDial`

**Plan document:** `docs/superpowers/plans/2026-06-25-companion-A-seat-core.md`
Contains the full specification, TDD test plans, and implementation steps for each task.

**Tech Stack:**
- Python ≥3.12, pydantic v2, anthropic SDK, httpx, uv (path source), hatchling
- pytest + pytest-asyncio (asyncio_mode = "auto")
- ruff line-length 100, target py312
- New repo at `/Users/slabgorb/Projects/oq-1/sidequest-seat-core` (sibling to understudy)

**Branch Strategy:** 
Working directly on `main` of the new repo (no feature branch—this is creation, not a patch). The repo will be initialized with `git init` in Task 1, Step 1.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-25T17:34:59Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-25T17:01:05Z | 2026-06-25T17:04:41Z | 3m 36s |
| red | 2026-06-25T17:04:41Z | 2026-06-25T17:17:04Z | 12m 23s |
| green | 2026-06-25T17:17:04Z | 2026-06-25T17:24:22Z | 7m 18s |
| review | 2026-06-25T17:24:22Z | 2026-06-25T17:34:59Z | 10m 37s |
| finish | 2026-06-25T17:34:59Z | - | - |

## Implementation Notes for TEA

**RED Phase Setup:**
The plan document (`docs/superpowers/plans/2026-06-25-companion-A-seat-core.md`) contains **pre-written failing tests** for each of Tasks 1–7. TEA should drive the RED phase directly from the plan:
- Task 1: smoke test (test_smoke.py)
- Task 2: core primitives (test_core.py)
- Task 3: AnthropicModel (test_anthropic.py)
- Task 4: OllamaModel (test_ollama.py)
- Task 5: ClaudePModel (test_claude_p.py)
- Task 6: make_model factory (test_factory.py)
- Task 7: persona axes (test_axis.py)

Each task has **Step 1: Write the failing test**, **Step 2: verify it fails**, **Step 3: implementation**, **Step 4: verify it passes** — the standard TDD cycle.

**New Repo Notes:**
- The `sidequest-seat-core` directory does NOT exist yet; Task 1, Step 1 creates it with `mkdir -p ... && git init`
- Work directly on `main` (no feature branch)
- Acceptance: full pytest suite (all 14 tests) passes, ruff lint clean, import works

## Sm Assessment

**Setup verified (Camina Drummer, SM):**
- Session file present at canonical root `.session/159-1-session.md`; story context at `sprint/context/context-story-159-1.md`. Both confirmed.
- Jira: none — SideQuest tracks in `pf sprint` YAML only. Correctly skipped (not missing bookkeeping).
- Workflow: `tdd` (phased) → next phase `red`, owner TEA (Amos Burton).

**Scope (authoritative = Plan A doc, Tasks 1–7):** `docs/superpowers/plans/2026-06-25-companion-A-seat-core.md`
Extract a charter-neutral `sidequest-seat-core` package: scaffold (T1) → core primitives `Message`/`ModelError`/`DecideResult`/`parse_structured`/`StructuredModel`/`FakeStructuredModel` (T2) → `AnthropicModel` w/ prompt caching + true-input metering (T3) → `OllamaModel` (T4) → `ClaudePModel` w/ API-key stripping (T5) → `make_model` factory (T6) → persona axes `SeatAxes`/`Role`/`RoleDial` (T7). **Tasks 8–9 belong to 159-2 (depends_on 159-1) — out of scope here.**

**New-repo bootstrap (TEA/Dev must know):**
- `sidequest-seat-core` does NOT exist yet and is NOT in `.pennyfarthing/repos.yaml`. Plan A Task 1 `git init`s it at `/Users/slabgorb/Projects/oq-1/sidequest-seat-core` (sibling subrepo of `sidequest-understudy`).
- Work directly on `main` of the fresh repo — there is **no feature branch** for this story. Branch creation against the not-yet-existing repo was intentionally skipped; not a setup defect.

**TEA entry note:** Plan A already contains pre-written failing tests for each task (every task's "Step 1: Write the failing test" + "Step 2: verify it fails"). Drive RED from the plan. Acceptance: new package builds, imports, and full `pytest` suite green standalone; ruff line-length 100 / py312; pytest `asyncio_mode=auto`. Doctrine guardrails: backends generic over a pydantic output model bound at construction (structured output forced at API/runtime, never regex-parsed from prose); `ClaudePModel` strips `ANTHROPIC_API_KEY`/`ANTHROPIC_ADMIN_KEY` (fail loud, no silent API spend); `AnthropicModel` meters `input_tokens + cache_read + cache_creation`.

## TEA Assessment

**Phase:** finish (Amos Burton)
**Tests Required:** Yes
**Reason:** New package extraction with explicit behavioral contracts (schema-generic backends, env-key-stripping, metering, persona-axis validation). Not a chore bypass.

**New repo created:** `/Users/slabgorb/Projects/oq-1/sidequest-seat-core` (`git init` on `main`, per plan). RED committed: `1595e3c`.

**Test Files (all RED):**
- `tests/test_smoke.py` — package import + docstring (Task 1)
- `tests/test_core.py` — `parse_structured`, `Message`, `DecideResult`, `FakeStructuredModel` (Task 2)
- `tests/test_anthropic.py` — `AnthropicModel` tool-forcing, prefix caching, true-input metering (Task 3)
- `tests/test_ollama.py` — `OllamaModel` JSON-format decide + metering (Task 4)
- `tests/test_claude_p.py` — `ClaudePModel` key-stripping + subprocess wiring (Task 5)
- `tests/test_factory.py` — `make_model` dispatch + loud failures (Task 6)
- `tests/test_axis.py` — `SeatAxes`/`Role`/`RoleDial` validation + perception scope (Task 7)

**Tests Written:** 31 tests across 7 files (14 transcribed from the plan + 17 TEA adversarial/error-path/wiring additions).
**Status:** RED verified — `uv run pytest`: `test_smoke` FAILS on `assert seat_core.__doc__` (None); the other 6 modules error on collection with `ModuleNotFoundError` (`seat_core.core`, `seat_core.llm.*`, `seat_core.persona.axis` not yet written). Env synced with `uv sync` (anthropic 0.112, pydantic 2.13, pytest 9.1, pytest-asyncio 1.4, asyncio_mode=auto).

### Harness boundary (what Dev must implement for GREEN)
TEA created ONLY test infrastructure: `pyproject.toml`, `.gitignore`, empty package markers (`src/seat_core/__init__.py` — deliberately **no docstring** so smoke stays red — plus `llm/__init__.py`, `persona/__init__.py`), `tests/__init__.py`, and the test files. **No feature logic.** Dev's GREEN = write the implementation modules + the package docstring exactly per Plan A Tasks 1–7:
- `src/seat_core/__init__.py` docstring (Task 1) → smoke green
- `src/seat_core/core.py` (Task 2)
- `src/seat_core/llm/anthropic_model.py` (Task 3)
- `src/seat_core/llm/ollama_model.py` (Task 4)
- `src/seat_core/llm/claude_p_model.py` (Task 5)
- `src/seat_core/llm/factory.py` (Task 6)
- `src/seat_core/persona/axis.py` (Task 7)

The plan's "Step 3: Write the implementation" blocks are the exact target. All 31 tests were authored to pass against that verbatim implementation.

### Rule Coverage (.pennyfarthing/gates/lang-review/python.md)

| Rule | Test(s) | Status |
|------|---------|--------|
| #1 silent exception swallowing | `test_parse_structured_raises_on_prose`/`_bad_shape`/`_empty_string`; `test_anthropic_no_tool_use_block_raises_model_error`; `test_anthropic_invalid_tool_input_raises_model_error`; `test_ollama_garbage_raises_model_error`; `test_ollama_missing_message_content_raises_model_error`; `test_claude_p_nonzero_exit_raises_model_error`; `test_claude_p_non_json_envelope_raises_model_error` | RED (collection) |
| #8 unsafe deserialization | model output parsed → pydantic-validated, never trusted: `test_parse_structured_*`, ollama/anthropic invalid-shape tests | RED |
| #9 async/await | all `decide()` paths awaited; `test_claude_p_decide_launches_claude_without_api_key` exercises async subprocess wiring | RED |
| #11 input validation / secrets | **keystone:** `test_claude_p_scrubs_api_keys_from_child_env` (unit) **and** `test_claude_p_decide_launches_claude_without_api_key` (proves the scrubbed env is actually wired into the subprocess, not just defined) | RED |
| #6 test quality | self-check below | n/a |

**Rules checked:** 4 of 13 lang-review rules are materially applicable to this charter-neutral data/backend package (no logging, no path handling, no SQL/HTML, no API handlers, no resource-manager-less I/O — backends take injected clients); all 4 have explicit coverage. Remaining rules (#2 mutable defaults, #3 type annotations, #4 logging, #5 paths, #7 resource leaks, #10 imports, #12 deps, #13 fix-regressions) are Dev/Reviewer static concerns, not RED behaviors.
**Self-check:** 0 vacuous tests — every test asserts a specific value or `pytest.raises(...)`; no `assert True`, no `let _ =`, no truthy-on-always-None.

**Handoff:** To Naomi Nagata (Dev) for GREEN — implement Plan A Tasks 1–7 `src/seat_core/*.py` until `uv run pytest` is all-green (31 passed).

## Dev Assessment

**Implementation Complete:** Yes (Naomi Nagata)
**Approach:** Transcribed Plan A Tasks 1–7 "Step 3: Write the implementation" blocks verbatim — minimalist, no abstraction beyond what the 31 tests demand.

**Files Changed (in `sidequest-seat-core`, all new except `__init__.py`):**
- `src/seat_core/__init__.py` — package docstring (Task 1) → smoke green
- `src/seat_core/core.py` — `Message`, `ModelError`, `DecideResult`, `StructuredModel` protocol, `parse_structured`, `FakeStructuredModel` (Task 2)
- `src/seat_core/llm/anthropic_model.py` — `AnthropicModel`: tool-forced output, `cache_control` prefix, true-input metering (`input + cache_read + cache_creation`) (Task 3)
- `src/seat_core/llm/ollama_model.py` — `OllamaModel`: `/api/chat` with JSON-schema `format` (Task 4)
- `src/seat_core/llm/claude_p_model.py` — `ClaudePModel`: `_plan_env()` strips `ANTHROPIC_API_KEY`/`ANTHROPIC_ADMIN_KEY`, **wired** into `create_subprocess_exec(..., env=_plan_env())` (Task 5)
- `src/seat_core/llm/factory.py` — `make_model` dispatch, loud `ValueError` on unknown backend (Task 6)
- `src/seat_core/persona/axis.py` — `SeatAxes` (extra="forbid", 0..1 bound), `Role` (StrEnum), `RoleDial.perception_scope` (Task 7)

**Tests:** 34/34 passing (GREEN) — `uv run pytest -q`, re-verified on the clean committed tree. Ruff clean (`ruff check .`). No debug code. (TEA's "31 tests" → 34 pytest items after a 2-value parametrize.)
**Branch:** `feat/159-1-seat-core` (commit `66fd1f1`, atop RED `1595e3c`). **Not pushed** — see Delivery Findings (the new repo has no remote yet).

**Wiring self-check:** Every backend is generic over the bound `output_model` (constructor-bound, used in `decide`); `make_model` constructs all four real backends; structured output is forced at the API/runtime layer in every backend (never regex/prose). The security keystone — `ClaudePModel.decide` passing the scrubbed env to the subprocess — is proven by `test_claude_p_decide_launches_claude_without_api_key`, not just by `_plan_env` existing. No half-wired surface: this package has no production consumer yet by design (159-2 migrates understudy onto it; 159-4/5 add the companion), so its "wiring" is its own green public API, which the factory + per-backend tests exercise end to end.

**Handoff:** To Chrisjen Avasarala (Reviewer) for review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 smells; 34/34 pytest green; ruff clean; tree clean | N/A (mechanical — confirms GREEN) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — edge analysis performed by Reviewer (see `[EDGE]`) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — silent-failure analysis performed by Reviewer (see `[SILENT]`) |
| 4 | reviewer-test-analyzer | Yes | findings | 6 | confirmed 6 at LOW/MED (non-blocking polish), 0 blocking, 0 dismissed |
| 5 | reviewer-comment-analyzer | Yes | findings | 4 | confirmed 4 at LOW/MED (doc polish), 0 blocking, 0 dismissed |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — type analysis performed by Reviewer (see `[TYPE]`) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings — **security analysis performed by Reviewer; keystone verified at source** (see `[SEC]`) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — simplify analysis performed by Reviewer (see `[SIMPLE]`) |
| 9 | reviewer-rule-checker | Yes | findings | 9 | confirmed 9 (4× rule#3 LOW, 2× rule#7 MED, 3× rule#10 LOW); 0 blocking; rule-matching findings downgraded-with-rationale, NOT dismissed |

**All received:** Yes (4 enabled returned with results; 5 disabled pre-filled and self-covered)
**Total findings:** 0 confirmed blocking (Critical/High); ~13 confirmed non-blocking (Medium/Low) for follow-up or acceptance; 0 dismissed.

## Reviewer Assessment

**Verdict:** APPROVED

A clean, minimalist extraction that faithfully implements Plan A Tasks 1–7. 34/34 tests green, ruff clean. The security-critical control (the `ClaudePModel` API-key scrub) is genuinely **wired and proven**, not merely defined. No Critical/High issues. The findings below are Medium/Low quality improvements appropriate for follow-up; none block a v1 charter-neutral library whose consumers arrive in 159-2/4/5.

**Data flow traced (untrusted model output → validated value):** A backend receives `system: str` + `transcript: list[Message]` → calls the model → the raw output is forced/parsed structurally (`AnthropicModel` via a `tool_use` block; `OllamaModel`/`ClaudePModel` via `parse_structured`) → `pydantic.model_validate` → `DecideResult.value`. Untrusted LLM text is **schema-validated, never trusted as prose**; on any mismatch a `ModelError` is raised (safe because there is no fallback path that fabricates a value). Secret flow: `os.environ` → `_plan_env()` strips `ANTHROPIC_API_KEY`/`ANTHROPIC_ADMIN_KEY` → that scrubbed dict is the `env=` of `create_subprocess_exec` (safe because the API-key never reaches the `claude -p` child, so it bills the plan, not the metered API).

### Observations (tagged by source)

1. `[SEC]` `[VERIFIED]` **Security keystone correct and wired** — `claude_p_model.py:50` passes `env=_plan_env()` to `create_subprocess_exec` (call at :39); `_plan_env()` (:22-23) excludes `_API_KEY_VARS` (:19 = both keys). Proven by `test_claude_p_decide_launches_claude_without_api_key` (correct monkeypatch target on the `asyncio` module; captures the env kwarg; cannot pass vacuously — test-analyzer concurred). Complies with lang-review #11 and SOUL "No Silent Fallbacks."
2. `[SEC]` `[MEDIUM]` **`_API_KEY_VARS` may be incomplete** — only `ANTHROPIC_API_KEY`/`ANTHROPIC_ADMIN_KEY` are scrubbed. If the `claude` CLI also honors `ANTHROPIC_AUTH_TOKEN` (SDK bearer auth) or `ANTHROPIC_BASE_URL`-routed billing, those could re-introduce metered billing. Scoped to the plan's two vars deliberately; raised as a non-blocking Question for the plan author to confirm the CLI's env precedence.
3. `[SILENT]` `[VERIFIED]` **Every error path fails loud** — `parse_structured` (`core.py` JSONDecodeError/ValidationError→ModelError), `AnthropicModel` (no-tool-block :46, bad-input :50), `OllamaModel` (missing-content :41), `ClaudePModel` (nonzero-exit :54, non-JSON :58). No bare except, no swallow, no silent default. Rule-checker #1 = 0 violations.
4. `[EDGE]` `[VERIFIED]` **Metering edge cases handled** — `AnthropicModel` no-cache-fields → `getattr(...,0) or 0` (:54-55, tested); `OllamaModel` absent counts → `.get(...,0)` (tested). Boundary values 0.0/1.0 valid, below-range rejected on `SeatAxes` (tested).
5. `[RULE]` `[MEDIUM]` **Async clients lack a close/shutdown lifecycle** — `AnthropicModel` (`anthropic_model.py:28`) and `OllamaModel` (`ollama_model.py:23`) store a default-constructed `anthropic.AsyncAnthropic()` / `httpx.AsyncClient(timeout=300.0)` with no `aclose()`/async-context. Matches lang-review #7 → CONFIRMED, downgraded to Medium (NOT dismissed): the client is a deliberately long-lived per-seat resource reused across turns (pooling is the intent — the opposite of the per-call leak #7 targets), and the production path injects a caller-managed client (`client=None` is a convenience fallback). A clean `aclose()`/`__aenter__/__aexit__` is a worthwhile follow-up but not a correctness defect; no consumer constructs-and-discards these.
6. `[EDGE]` `[MEDIUM]` **No timeout on `AnthropicModel`/`ClaudePModel`** — `OllamaModel` sets `timeout=300.0`, but `AnthropicModel` uses SDK defaults and `ClaudePModel.decide` `await proc.communicate()` waits indefinitely. A hung `claude -p` subprocess or stalled API call blocks the seat. Mitigated at the orchestration layer (understudy/companion run loops carry wall-clock guards) and matches the plan's impl. Non-blocking; note for 159-4/5 hardening.
7. `[TYPE]` `[VERIFIED]` **Generic-over-output-model is construction-bound, return type is `BaseModel`** — `DecideResult.value: BaseModel` (not `Generic[T]`), so the bound model isn't reflected in the static return type. Acceptable v1 design (the plan's choice); callers `isinstance`/trust the bound model. Structural `Protocol` conformance of all four backends verified.
8. `[DOC]` `[LOW]` **Docstring polish** — `StructuredModel` Protocol and `DecideResult` lack docstrings (the central public contract + metering surface); `AnthropicModel` docstring says "sums cached and uncached" while the code sums three billing fields; `axis.py` module docstring mentions an "autonomy/bond axis" not present on `RoleDial` (that's later-story scope). Non-blocking; worth a doc pass.
9. `[TEST]` `[LOW]` **Test-strength nits on already-strong coverage** — `tests/test_ollama.py` `_transport` checks `body['format']['properties']['kind']` truthily rather than asserting the exact `Ping.model_json_schema()`; missing cases for bare ``` fence, `claude_p` valid-envelope-without-`result`, and asserting `claude_p` bare-spec defaults model-id to `haiku`. Current 34-test suite already exceeds the plan's 14; these are optional hardening.
10. `[SIMPLE]` `[VERIFIED]` **No over-engineering / dead code** — each backend ~50 lines, no speculative abstraction, no unused code. Minimalist discipline honored.
11. `[RULE]` `[LOW]` **Style/hygiene** — missing `__all__` on `core.py`/`factory.py`/`axis.py` (rule #10) and missing `-> None` on the four `__init__` methods (rule #3 literal). CONFIRMED at LOW (NOT dismissed): ruff — the gated linter — passes; `-> None` on `__init__` is near-universal convention; `__all__` omission is common for small packages with a clear module layout. Optional polish.

### Rule Compliance (.pennyfarthing/gates/lang-review/python.md, exhaustive via reviewer-rule-checker + Reviewer)

| Rule | Applicable instances | Verdict |
|------|----------------------|---------|
| #1 silent exception swallowing | 6 (all try/except re-raise ModelError) | COMPLIANT |
| #2 mutable default arguments | 8 signatures | COMPLIANT (None/str/required only) |
| #3 type annotations at boundaries | 14 | 4 LOW deviations (`__init__` missing `-> None`); params + non-init returns fully typed |
| #4 logging | 0 (no logging import) | N/A |
| #5 path handling | 0 (no path/open) | N/A |
| #6 test quality | 29 test items | COMPLIANT (0 vacuous; correct monkeypatch target; 6 LOW polish nits) |
| #7 resource leaks | 4 | 2 MED (async clients, no aclose) — confirmed, downgraded w/ rationale |
| #8 unsafe deserialization | 5 json paths | COMPLIANT (validated via pydantic; no pickle/eval/yaml/shell) |
| #9 async/await | 8 | COMPLIANT (all awaited; exec form; no blocking calls) |
| #10 import hygiene | 12 | 3 LOW (missing `__all__`); no star/circular imports |
| #11 input validation / secrets | 4 | COMPLIANT (key-scrub wired; loud `ValueError`/`ModelError`; exec not shell) |
| #12 dependency hygiene | 6 deps | COMPLIANT (lower-bounds; test deps in dev group; httpx over requests) |
| #13 fix-introduced regressions | 0 (new package) | N/A |

SOUL "No Silent Fallbacks" + "No Stubbing": COMPLIANT — `make_model` raises `ValueError` on unknown backend (`factory.py:31`), all backends fail loud, and `StructuredModel`'s `...` body is correct Protocol syntax (not a stub).

### Devil's Advocate

Suppose this code is broken. The most dangerous claim is the security one: "`claude -p` never sees an API key." `_plan_env()` only strips two names. The `anthropic` SDK also honours `ANTHROPIC_AUTH_TOKEN`; if the `claude` CLI consults it (or `ANTHROPIC_BASE_URL` routes to a metered proxy), a user with that var set would silently bill the API — the exact harm this story exists to prevent, passing all tests because the tests only assert the two known names are gone. That is the one finding I would most want the plan author to confirm before trusting the control in the wild (logged non-blocking). Second: robustness. `ClaudePModel.decide` awaits `proc.communicate()` with no timeout — a wedged `claude` subprocess hangs the seat forever; `AnthropicModel` likewise relies on SDK defaults. A confused or adversarial model that streams forever, or a network black hole, stalls the turn. Third: `parse_structured`'s fence regex `^```(?:json)?\s*|\s*```$` with `re.MULTILINE` strips any line starting with a fence — if a model legitimately returns JSON whose string value contains a line like ```` ```py ````, the regex could corrupt the payload mid-content; in practice models emit one outer fence, so this is theoretical. Fourth: type erosion — `DecideResult.value: BaseModel` means a backend could return a *different* pydantic model than the bound `output_model` and nothing at the type layer or runtime would catch it (each backend validates against its own `output_model`, so this only bites a future buggy backend). Fifth: resource exhaustion — the never-closed async clients would matter if any consumer constructed backends in a loop; today none does, so it sleeps. A confused user can't reach this package directly (no CLI/UI); a malicious *model* is the only adversary, and every model output funnels through pydantic validation or a forced tool schema. **Net:** the realistic failure modes are the unscrubbed-auth-var (security, low-likelihood, logged) and the missing timeouts (robustness, orchestration-mitigated) — both non-blocking for a v1 extraction, both worth a follow-up. Nothing rises to data corruption, injection, or a broken core contract.

**Handoff:** To Camina Drummer (SM) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): `sidequest-seat-core` is not registered in `.pennyfarthing/repos.yaml`, so pf test/lint/finish tooling and the branch-protection hook don't yet know it. Affects `.pennyfarthing/repos.yaml` (add a `seat-core` entry: path `sidequest-seat-core`, language python, test_command `pytest`, lint_command `ruff check .`, default_branch `main`). Not required for this story's RED/GREEN (the repo runs standalone via `uv run pytest`), but 159-2 binds it as a `../sidequest-seat-core` uv path dep and SM finish will need it. *Found by TEA during test design.*
- **Improvement** (non-blocking): `uv sync` resolved Python **3.14** (plan's stated stack is 3.12; `requires-python = ">=3.12"` so 3.14 is in-spec). All constructs used (`StrEnum`, `match`, `X | None`, frozen dataclass) work on 3.14 and the suite collects cleanly. Affects `sidequest-seat-core/pyproject.toml` (pin a `.python-version` or tighten `requires-python` only if a specific interpreter is desired — otherwise no action). *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking, for SM/finish): `sidequest-seat-core` is a local-only git repo with **no remote** (`git init`, no `origin`), so the standard Dev "git push" step and the SM finish PR-creation step have no target. Affects the SM finish flow + `.pennyfarthing/repos.yaml` (the repo needs a GitHub remote created and a `seat-core` repos.yaml entry before a PR can be opened/merged; until then the GREEN work lives on local `feat/159-1-seat-core`). Compounds TEA's repos.yaml-registration finding above — both must be resolved before finish. *Found by Dev during implementation.*
- **Question** (non-blocking): RED (`1595e3c`) landed on `main` (the hook allowed it during the red phase) but GREEN had to go on a feature branch (hook now blocks `main`). So `main` currently holds failing tests until `feat/159-1-seat-core` merges back. Affects the seat-core repo's `main` (finish/merge must fast-forward `feat/159-1-seat-core` → `main` to make `main` green). Standard feature-branch flow, just noting the transient red-on-main. *Found by Dev during implementation.*

### Reviewer (code review)
- **Question** (non-blocking): Confirm whether `claude -p` honours credential env vars beyond `ANTHROPIC_API_KEY`/`ANTHROPIC_ADMIN_KEY` (e.g. `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_BASE_URL`). Affects `sidequest-seat-core/src/seat_core/llm/claude_p_model.py` (`_API_KEY_VARS` may need to grow to fully guarantee the plan-billing invariant). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Add a clean async-client lifecycle (`aclose()` / `__aenter__`/`__aexit__`) to `AnthropicModel` and `OllamaModel`, and a timeout to `AnthropicModel` + `ClaudePModel.decide` (Ollama already has 300s). Affects `sidequest-seat-core/src/seat_core/llm/{anthropic_model,ollama_model,claude_p_model}.py`. Best folded into 159-4/5 hardening when a real run loop owns the backends. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Doc + hygiene polish — docstrings on `StructuredModel`/`DecideResult`, precise Anthropic-metering wording (sums three fields), trim the `axis.py` autonomy/bond mention to current scope, and consider `__all__` on the public modules. Affects `sidequest-seat-core/src/seat_core/{core.py,llm/anthropic_model.py,persona/axis.py}`. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **TEA created the package harness (Task 1 scaffold) during RED**
  - Spec source: Plan A `docs/superpowers/plans/2026-06-25-companion-A-seat-core.md`, Task 1 (Scaffold) + SM assessment "no feature branch / Task 1 git init"
  - Spec text: "Task 1: Scaffold the sidequest-seat-core package … Step 1 mkdir + git init … Step 2 pyproject.toml … Step 3 __init__.py files … Step 4 smoke test"
  - Implementation: TEA performed the repo `git init`, `pyproject.toml`, `.gitignore`, empty package markers (`src/seat_core/__init__.py` **without** docstring, `llm/__init__.py`, `persona/__init__.py`), and `tests/__init__.py` — i.e. only the infrastructure required to RUN pytest. No `src/seat_core/*.py` feature module and no package docstring were written; those remain Dev's GREEN work.
  - Rationale: A from-scratch package has no RED state until pytest can collect and execute. The harness is a precondition of demonstrating RED, which is TEA's phase output. The empty top-level `__init__.py` keeps the smoke test red (asserts `__doc__`) so Dev's first GREEN step is meaningful.
  - Severity: minor
  - Forward impact: Dev's GREEN must NOT re-create pyproject/markers; Dev adds module bodies + the package docstring only. The plan's Task 1 "Step 5 expected PASS" no longer applies in isolation (smoke goes green when Dev adds the docstring in the same GREEN pass).
- **Test suite expanded beyond the plan's enumerated tests (14 → 31)**
  - Spec source: Plan A Tasks 2–7 "Step 1: Write the failing test" blocks; lang-review `.pennyfarthing/gates/lang-review/python.md` #1/#8/#9/#11
  - Spec text: each task lists a specific failing-test file (14 tests total); impl blocks promise ModelError on bad output, env-key stripping, and true-input metering
  - Implementation: transcribed all 14 plan tests verbatim, then added 17 TEA tests covering stated-but-untested error paths (AnthropicModel no-tool-block / invalid-input → ModelError, no-cache-field metering; OllamaModel missing-content / absent-counts; ClaudePModel nonzero-exit / non-JSON → ModelError; parse_structured empty-string; FakeStructuredModel empty-script; factory bare-claude_p; SeatAxes extra-forbid / bounds / bad-literal; Role StrEnum value) and the security keystone — `test_claude_p_decide_launches_claude_without_api_key`, which asserts the scrubbed env is actually wired into the subprocess call, not merely defined.
  - Rationale: TEA mandate is rule-enforcement + paranoia, not AC-transcription alone. Every added test passes against the plan's verbatim "Step 3" implementation (verified by inspection), so GREEN scope is unchanged — Dev still implements only the plan's impl blocks.
  - Severity: minor
  - Forward impact: none — Dev implements the plan's impl verbatim; the extra tests harden the same surface, they don't widen it.

### Dev (implementation)
- **GREEN committed on a feature branch, not `main`**
  - Spec source: Plan A "Global Constraints" + SM/TEA assessments
  - Spec text: "seat-core repo branch: work on `main` (new repo)" / "Work directly on `main` of the fresh repo — there is no feature branch"
  - Implementation: Created `feat/159-1-seat-core` off `main` and committed GREEN (`66fd1f1`) there; `main` keeps only the RED commit (`1595e3c`).
  - Rationale: The `pf` branch-protection PreToolUse hook BLOCKS commits to `main` ("Cannot commit to protected branch 'main'. Create a feature branch first"). The plan's "work on main" ideal is operationally incompatible with the hook, which is non-negotiable mid-flight. A feature branch is harmless for a local-only repo and yields a clean impl-only review diff (`main..feat` = the 7 implementation files).
  - Severity: minor
  - Forward impact: SM finish must merge `feat/159-1-seat-core` → `main` (fast-forward) to land GREEN on `main` and clear the transient red-on-main. No code impact on 159-2/4/5.

### Reviewer (audit)
- **TEA: package harness created during RED** → ✓ ACCEPTED by Reviewer: sound — a from-scratch package has no runnable RED state without pyproject + package markers; TEA wrote zero feature logic (the empty docstring-less `__init__` correctly keeps the smoke test red). Agrees with author reasoning.
- **TEA: test suite expanded 14 → 31** → ✓ ACCEPTED by Reviewer: the 17 additions are error-path/wiring/boundary tests for contracts the plan's own impl promises; verified all pass against the verbatim impl (34/34 green), so GREEN scope was not widened. This is exactly the rule-enforcement TEA is for — the `claude_p` env-wiring test in particular is load-bearing.
- **Dev: GREEN on a feature branch, not `main`** → ✓ ACCEPTED by Reviewer: forced by the `pf` branch-protection hook (operationally non-negotiable); harmless for a local-only repo and yields a cleaner impl-only review diff. Correctly logged with the forward-impact note that finish must fast-forward `feat → main`. No undocumented deviations found beyond these three.