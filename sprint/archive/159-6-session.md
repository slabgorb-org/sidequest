---
story_id: "159-6"
jira_key: ""
epic: "159"
workflow: "tdd"
---
# Story 159-6: Relocate seat_core into sidequest-understudy (reverse standalone-repo extraction)

## Story Details
- **ID:** 159-6
- **Jira Key:** N/A (Jira not configured for this project)
- **Workflow:** tdd
- **Stack Parent:** 159-1 (Extract sidequest-seat-core)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-25T19:39:26Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-25T19:13:31Z | 2026-06-25T19:15:33Z | 2m 2s |
| red | 2026-06-25T19:15:33Z | 2026-06-25T19:21:35Z | 6m 2s |
| green | 2026-06-25T19:21:35Z | 2026-06-25T19:30:14Z | 8m 39s |
| review | 2026-06-25T19:30:14Z | 2026-06-25T19:39:26Z | 9m 12s |
| finish | 2026-06-25T19:39:26Z | - | - |

## Story Context

**Type:** refactor
**Points:** 2
**Repos:** sidequest-understudy
**Branch:** feat/159-6-relocate-seat-core-into-understudy
**Branch Strategy:** gitflow (feat/159-6-relocate-seat-core-into-understudy)

### Acceptance Criteria
1. seat_core package + its tests live inside sidequest-understudy. Default target: top-level sidequest-understudy/src/seat_core/ with import name 'seat_core' unchanged (minimal churn); Architect may choose understudy.seat_core instead — document the choice in the session.
2. understudy's pyproject.toml packages seat_core in-tree; NO '../sidequest-seat-core' path dependency exists anywhere in the repo.
3. All 34 seat_core tests pass within understudy's pytest suite, AND understudy's pre-existing test suite stays green (regression gate).
4. The standalone sidequest-seat-core/ repo is removed and its entry in the orchestrator .gitignore is deleted.
5. Plan A and the companion spec are updated to reflect seat_core's new home; 159-2/159-4/159-5 are re-scoped or annotated to drop the path-dep assumption, with the companion-vs-understudy coupling question flagged for the Architect.

### Decision Notes
Decision (Keith, 2026-06-25): seat_core should live INSIDE sidequest-understudy, not as its own repo. This reverses Plan A's standalone-extraction decision delivered in 159-1. Move the seat_core package + its 34 tests out of the local standalone repo sidequest-seat-core and into sidequest-understudy, then delete the standalone repo (and its orchestrator .gitignore entry).

**RIPPLE:** Stories 159-2/159-4/159-5 assumed a '../sidequest-seat-core' uv path dependency — they must be re-scoped. 159-2 ('Migrate understudy onto seat-core') largely dissolves once seat_core is in-tree; the companion (159-4/5) can no longer import seat_core as an independent shared package, so the Architect must decide whether the shipping companion depends on understudy or seat_core stays independently importable.

### Reference Documents
- Spec: docs/superpowers/specs/2026-06-25-companion-seat-design.md
- Plan A: docs/superpowers/plans/2026-06-25-companion-A-seat-core.md

## Sm Assessment

Setup clean: session, context, and branch (`feat/159-6-relocate-seat-core-into-understudy` in sidequest-understudy) all in place. Routing to TEA for the RED phase.

**Nature of the work.** This is a reverse-extraction: 159-1 pulled seat_core out into a standalone repo; Keith decided 2026-06-25 it should live in-tree in understudy instead. So this is a *move + delete-the-old-repo* refactor, not new feature code. The 34 seat_core tests already exist — they move with the package.

**TDD framing for a relocation.** RED is not "write new failing tests." It's: stand the 34 seat_core tests up inside understudy's pytest suite so they fail because seat_core is not yet in-tree (no `../sidequest-seat-core` path dep). GREEN is the actual move — package into `src/seat_core/`, wire pyproject to package it in-tree, tests go green, understudy's pre-existing suite stays green (regression gate, AC#3).

**Risk to flag loudly — destructive deletion.** AC#4 deletes the standalone `sidequest-seat-core` repo and its orchestrator `.gitignore` entry. That is irreversible-ish. Dev MUST confirm the full package + all 34 tests (and any uncommitted/local-only work in that repo) are migrated and green in understudy BEFORE removing the standalone repo. Verify the old repo has nothing un-migrated, not just that the new location works.

**Architect decision points are deferred with defaults, not blocked.** AC#1 gives a default (top-level `src/seat_core/`, import name `seat_core` unchanged) and allows `understudy.seat_core` as an alternative — take the default for minimal churn unless a concrete reason surfaces; document any deviation. AC#5's companion-vs-understudy coupling question (159-2/159-4/159-5 re-scope) is a doc/annotation task and a flag for the Architect — it does not block the code move. Don't expand this 2-pt story into re-architecting the companion; annotate and move on.

## TEA Assessment

### Red Phase (test writing)

**Tests Required:** Yes (focused wiring/structural tests; the 34 seat_core unit tests travel with the package as existing coverage — not recreated)
**Reason:** This is a relocation/refactor with existing coverage. The 34 seat_core tests already pass in the standalone repo and move with the package during GREEN. RED here proves the *relocation end-state* — the new invariant that didn't exist before: seat_core wired in-tree, no path dependency, tests carried across.

**Test File:**
- `sidequest-understudy/tests/test_seat_core_relocation.py` — 6 relocation wiring/structural tests

**Tests Written:** 6 tests covering ACs #1, #2, #3 (AC#4 deferred to Reviewer — see deviation; AC#5 is a docs task, not code).
**Status:** RED — 5 failing, 1 guard passing (no path dep), 0 collection errors. Baseline: 84 pre-existing understudy tests green.

| Test | AC | RED result |
|------|----|-----------|
| `test_seat_core_importable` | #1 | FAIL — `ModuleNotFoundError: seat_core` |
| `test_seat_core_is_in_tree` | #1/#2 | FAIL — import error (in-tree path unverifiable until moved) |
| `test_seat_core_public_surface_importable` | #3 | FAIL — deep imports (core, persona.axis, llm.factory) absent |
| `test_pyproject_packages_seat_core_in_tree` | #1 | FAIL — wheel packages = `['src/understudy']`, missing `src/seat_core` |
| `test_no_standalone_seat_core_path_dependency` | #2 | PASS (guard — green from start; blocks Dev from wiring an external uv path source instead of moving in-tree) |
| `test_seat_core_tests_relocated` | #3 | FAIL — 7 seat_core test modules not yet in understudy/tests |

### Rule Coverage

**Rules checked:** N/A for new-code rules. No Python lang-review checks apply — this story authors **no new code surface** (no validated constructors, new types, or APIs). seat_core's internal logic is unchanged and carries its own 34 tests (incl. the load-bearing guards: `ClaudePModel` key-stripping, `AnthropicModel` true-token metering, factory prefix dispatch, axis bound validation). The relocation must not alter those — AC#3's regression gate (all 34 pass in the new location) is the enforcement.
**Self-check:** 0 vacuous tests. Every test has a meaningful assertion with a failure message; no `assert True`, no `let _ =`, no always-None checks. The one always-green test (`test_no_standalone_seat_core_path_dependency`) is an intentional regression guard, not vacuous — it asserts a real invariant Dev could violate.

**Handoff:** To Dev (Naomi Nagata) for the GREEN move.

**Dev guidance (GREEN):**
1. `git mv`/move `sidequest-seat-core/src/seat_core/` → `sidequest-understudy/src/seat_core/`; move the 7 test modules + `tests/__init__.py` into understudy's tests tree (location-tolerant — my test searches `tests/` recursively; a `tests/seat_core/` subdir is fine and keeps them grouped).
2. Add `src/seat_core` to understudy pyproject `[tool.hatch.build.targets.wheel].packages`; seat_core's runtime deps (pydantic, anthropic, httpx) are ALREADY in understudy's deps — no additions needed. Do NOT add a `[tool.uv.sources]` path entry (the guard test forbids it).
3. `uv sync` so the editable install exposes `seat_core`, then run the full suite: my 6 relocation tests + all 34 seat_core tests + the 84 pre-existing understudy tests must be green (AC#3 regression gate).
4. **Then** delete the standalone `sidequest-seat-core/` repo and remove line `sidequest-seat-core/` from the orchestrator `.gitignore` (currently line 9). SM flagged this loudly: confirm nothing un-migrated remains in the standalone repo (it has uncommitted `.pytest_cache`/`.ruff_cache` but those are ignored; the only real content is src + tests + pyproject — all moving) BEFORE deleting.
5. AC#5: annotate Plan A + the companion spec + 159-2/159-4/159-5 to drop the `../sidequest-seat-core` path-dep assumption and flag the companion-vs-understudy coupling question for the Architect. Docs only — do not re-architect.

## Dev Assessment

**Implementation Complete:** Yes
**Approach:** Took AC#1's documented default — top-level `src/seat_core/`, import name `seat_core` unchanged (minimal churn). No `understudy.seat_core` nesting. The package was moved byte-identical (verified via `diff -rq` before deleting the source); no internal code changed.

**Files Changed:**

_sidequest-understudy_ (branch `feat/159-6-relocate-seat-core-into-understudy`, pushed):
- `src/seat_core/**` (9 files) — package moved in-tree (core, llm/{factory,anthropic,ollama,claude_p}, persona/axis)
- `tests/seat_core/**` (8 files) — the 34 unit tests, grouped as a subpackage (location-tolerant per TEA's recursive search)
- `pyproject.toml` — added `src/seat_core` to `[tool.hatch.build.targets.wheel].packages`; no deps added (pydantic/anthropic/httpx already present); NO `[tool.uv.sources]` path entry

_orchestrator_ (`main`, trunk-based — committed `b09ffb8b`):
- `.gitignore` — removed the `sidequest-seat-core/` line (AC#4)
- `docs/superpowers/plans/2026-06-25-companion-A-seat-core.md` — reversal banner (AC#5)
- `docs/superpowers/specs/2026-06-25-companion-seat-design.md` — packaging-amended banner (AC#5)
- standalone `sidequest-seat-core/` repo **deleted** (AC#4; was gitignored, so not a tracked change)
- `sprint/epic-159.yaml` — 159-2/159-4/159-5 re-scoped via `pf sprint story update` (AC#5); left uncommitted for SM's finish ceremony (sprint metadata)

**Tests:** 124/124 passing (GREEN) — 6 relocation wiring + 34 relocated seat_core + 84 pre-existing understudy. `tests/wiring/` (playwright, needs a browser) excluded, matching TEA's baseline. Moved code is ruff-clean.

**AC coverage:**
- AC#1 ✓ in-tree `src/seat_core/`, import name unchanged
- AC#2 ✓ packaged in-tree, no path dependency (guard test green)
- AC#3 ✓ 34 seat_core + pre-existing suite green
- AC#4 ✓ standalone repo deleted + `.gitignore` entry removed (Reviewer verifies manually per TEA deviation)
- AC#5 ✓ Plan A + spec annotated, 159-2/4/5 re-scoped

**Branch:** feat/159-6-relocate-seat-core-into-understudy (pushed)

**Handoff:** To TEA for the verify phase (simplify + quality-pass), then Reviewer.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (124 tests green; lint clean on all touched files) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — domain checked manually (see [EDGE]) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — domain checked manually (see [SILENT]) |
| 4 | reviewer-test-analyzer | Yes | findings | 6 | confirmed 3 (new test file, LOW/MED), deferred 3 (byte-identical moved code, out of scope) |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 | confirmed 1 (LOW doc), dismissed 2 (with rationale) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — domain checked manually (see [TYPE]) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings — domain checked manually (see [SEC]) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — domain checked manually (see [SIMPLE]) |
| 9 | reviewer-rule-checker | Yes | findings | 1 real (LOW) + 1 informational (pre-existing) | confirmed 1, informational 1 |

**All received:** Yes (4 enabled returned; 5 disabled via `workflow.reviewer_subagents`)
**Total findings:** 5 confirmed (all LOW/MEDIUM, non-blocking), 3 deferred (pre-existing moved code), 2 dismissed (with rationale), 1 informational

## Reviewer Assessment

**Verdict:** APPROVED

Story 159-6 is a *reverse-extraction relocation*: `seat_core` (the charter-neutral seat brain — schema-generic LLM backends + persona axes) moves byte-identical from the now-deleted standalone `sidequest-seat-core` repo into `sidequest-understudy/src/seat_core/` as an in-tree package, with its 34 unit tests. The bulk of the 885-line diff is the move itself (already reviewed/tested in 159-1); the genuinely new authored surface is one pyproject line and TEA's 102-line relocation test. All five ACs are met, all load-bearing invariants survived the move, and 124/124 tests are green. No Critical or High findings.

**Data flow traced:** a per-turn decision flows `manifest model spec → make_model(spec, output_model) → {Anthropic|Ollama|ClaudeP}.decide(system, transcript) → parse/validate → DecideResult(value, input_tokens, output_tokens)`. Safe because structured output is forced at the API layer (Anthropic `tool_choice`, Ollama JSON-schema `format`, ClaudeP `--output-format json` + strict `parse_structured`), never regex-scraped from prose; every error path raises `ModelError`/`ValueError` loudly — no silent fallback (`factory.py:30`, `core.py:49-53`, `claude_p_model.py:53-58`, `ollama_model.py:39-41`, `anthropic_model.py:45-55`).

**Observations (dispatch-tagged):**
- `[VERIFIED]` AC#4 standalone repo deletion — evidence: `ls sidequest-seat-core` → "No such file or directory"; `grep seat-core .gitignore` → no match. The destructive step was done *after* Dev verified (`diff -rq`, logged) that src/ and tests/ were byte-identical to the source and the source repo was git-clean. Complies with SM's loud destructive-deletion flag.
- `[VERIFIED]` AC#1/#2 in-tree wiring — evidence: `seat_core.__file__` resolves to `…/sidequest-understudy/src/seat_core/__init__.py`; pyproject wheel packages `["src/understudy", "src/seat_core"]`; no `[tool.uv.sources]` entry exists. Complies with the no-path-dependency AC.
- `[RULE]` `tests/test_seat_core_relocation.py:84` — `PYPROJECT.read_text()` missing `encoding="utf-8"` (Python checklist rule #5, CWE-838). CONFIRMED (rule match, cannot dismiss); severity **LOW** — pyproject.toml is UTF-8 by PEP-517 spec and is a repo-local file, not user input. One-line fix recommended, non-blocking. (rule-checker)
- `[TEST]` `test_seat_core_is_in_tree` — `REPO_ROOT in pkg_path.parents` is broader than intended: it also passes for a wheel installed into the in-repo `.venv/…/site-packages/seat_core` or a nested clone. CONFIRMED severity **MEDIUM** — currently passes *correctly* (understudy uses an editable install → `__file__` points at `src/`) and is backstopped by `test_pyproject_packages_seat_core_in_tree`, so the false-green is latent, not active. One-line hardening: `pkg_path.is_relative_to(REPO_ROOT / "src")`. Non-blocking. (test-analyzer; I independently flagged the same gap.)
- `[TEST]` `test_seat_core_public_surface_importable` — no explicit `assert` (Python checklist rule #6). CONFIRMED (rule match) severity **LOW** — downgraded with rationale: the `from seat_core… import …` lines ARE the failure signal (a missing/renamed symbol raises ImportError → test fails), so it is a functioning import-smoke test, not vacuous. rule-checker independently judged it compliant on the same reasoning. Adding `assert callable(make_model)` etc. would satisfy the letter of the rule. Non-blocking.
- `[TEST]` `test_seat_core_tests_relocated` — basename-set check would pass for stub/empty test files. CONFIRMED severity **LOW** — mitigated: the full 124-green suite proves the moved files are real (they collect and pass). Non-blocking.
- `[DOC]` `tests/test_seat_core_relocation.py:6` — docstring "They fail RED until Dev performs the move; they pass GREEN once seat_core lives under understudy's src/" describes the TDD lifecycle, which reads oddly in the merged tree where impl+tests land together. CONFIRMED severity **LOW** — it is accurate as a description of *how the tests were built* (TEA RED → Dev GREEN), just not of the final snapshot. Non-blocking. (comment-analyzer)
- `[DOC]` Plan A "PARTIALLY REVERSED" banner wording — DISMISSED: the banner body explicitly disambiguates ("Tasks below that scaffold a standalone repo … are historical — read them for the package's internal shape … not for its location or packaging"). "Partially" is accurate precisely because the internal design is preserved while packaging is fully reversed — which is what the analyzer's own suggested rewrite says. Low confidence; self-clarifying.
- `[DOC]` epic-159.yaml `159-4 depends_on: 159-1` now semantically loose — DISMISSED: 159-1 delivered the seat_core package (still exists, relocated), so the dependency on a *completed* prerequisite is still valid; the *new* blocker (Architect coupling decision) is captured in the re-scope description per AC#5, which is exactly what the AC asked for. The `depends_on` field accuracy was not in this story's scope. Noted informationally for the Architect.
- `[EDGE]` (subagent disabled — checked manually) — boundary paths: empty transcript (`FakeStructuredModel` returns default; backends send a valid messages array), missing API usage cache fields (`getattr(usage, …, 0) or 0` — no crash, `anthropic_model.py:54-55`), missing Ollama content key (`KeyError/TypeError → ModelError`), claude_p non-zero exit and non-JSON envelope (both → `ModelError`). No unhandled boundary found.
- `[SILENT]` (subagent disabled — checked manually) — traced every error path in `core.py` + all four backends: each raises `ModelError`/`ValueError` with context; no bare `except`, no `except…pass`, no `contextlib.suppress`, no default-returning fallback. Compliant with the project's emphatic No-Silent-Fallbacks rule.
- `[TYPE]` (subagent disabled — checked manually) — `SeatAxes`/`RoleDial` are pydantic `BaseModel` with `extra="forbid"` and bounded `Field(ge/le)`; `Role` is a `StrEnum` with explicit values; `Level` is a `Literal`. Public boundaries fully annotated (rule-checker corroborates: 0 annotation violations on public surfaces). No stringly-typed APIs.
- `[SEC]` (subagent disabled — checked manually) — `ClaudePModel` launches a fixed argv (no `shell=True`, no interpolated shell string) and strips `ANTHROPIC_API_KEY`/`ANTHROPIC_ADMIN_KEY` from the child env so it can never silently bill the metered API; no SQL, no HTML output, no `eval`/`pickle`/unsafe-yaml. `tomllib`/`json.loads` operate on repo-local/LLM output validated by pydantic. No injection surface.
- `[SIMPLE]` (subagent disabled — checked manually) — the change is a straight move + a 1-line pyproject edit + a focused 6-test relocation file. No dead code, no over-engineering, no premature abstraction. `FakeStructuredModel` is the sanctioned `fake` test lane (per understudy CLAUDE.md), not a stub.

### Rule Compliance (Python checklist — exhaustive, corroborated by rule-checker over 89 instances)

| Rule | Applicable instances | Result |
|------|----------------------|--------|
| #1 Silent exception swallowing | 12 | ✓ all raise loudly (ModelError/ValueError); no swallow |
| #2 Mutable default args | 7 | ✓ None defaults + in-body init; `list(script)` defensive copy |
| #3 Type annotations at boundaries | 14 | ✓ public surfaces fully annotated; private `_` helpers exempt |
| #4 Logging coverage/correctness | 8 | ✓ N/A — no logging module; errors surface as exceptions (by design) |
| #5 Path handling | 4 | ✗ 1 LOW — `read_text()` missing `encoding=` at relocation test:84 |
| #6 Test quality | 34 | ✓ no vacuous asserts; correct mock targets; 1 LOW import-smoke (no explicit assert) confirmed above |
| #7 Resource leaks | 5 | ✓ `with` for file I/O; clients are injected instance-state (intentional lifetime) |
| #8 Unsafe deserialization | 8 | ✓ no pickle/eval/unsafe-yaml; json/tomllib on non-user-controlled input + pydantic validation |
| #9 Async pitfalls | 8 | ✓ all `decide()` await async clients; no blocking calls, no missing awaits |
| #10 Import hygiene | 9 | ✓ explicit imports; no star; no cycle; `__init__` exports via submodules |
| #11 Input validation at boundaries | 4 | ✓ fixed subprocess argv; pydantic validation; loud unknown-backend |
| #12 Dependency hygiene | 6 | ⓘ lower-bound-only pins are PRE-EXISTING — not touched by this diff (informational) |
| #13 Fix-introduced regressions | 1 | ✓ only new lines are pyproject packages + relocation test; no regressions |

**Project invariants (SOUL.md / CLAUDE.md / seat-core design) — all COMPLIANT:**
- No Silent Fallbacks ✓ · No Stubbing ✓ (`FakeStructuredModel` is the sanctioned fake lane)
- ClaudePModel strips `ANTHROPIC_API_KEY` + `ANTHROPIC_ADMIN_KEY` and passes the scrubbed env to the subprocess ✓ (`claude_p_model.py:19,23,50`)
- AnthropicModel meters true input `input_tokens + cache_read + cache_creation` ✓ (`anthropic_model.py:54-58`)
- Backends generic over a pydantic output model bound at construction ✓ · structured output forced at API layer, never regex-from-prose ✓

### Devil's Advocate

Suppose this is broken. The loudest worry on a *delete-the-source-repo* story is data loss: did the move actually carry everything, or did Dev delete the standalone repo with un-migrated work inside it? I checked this directly rather than trusting the assessment — `diff -rq` parity was logged, the source repo was `git status`-clean, and the only non-migrated files were repo scaffolding (`pyproject.toml`, `uv.lock`, `.gitignore`) that understudy already supplies. The 34 tests now run and pass *in their new home*, which is the real proof the package arrived intact, not just that some files copied. So the destructive step is sound.

Second worry: does "in-tree" actually hold, or is the green a lie from an install artifact? This is where `test_seat_core_is_in_tree` is genuinely weak — `REPO_ROOT in parents` would also be satisfied by a wheel sitting in the repo-local `.venv`. A confused future maintainer who switches understudy to a non-editable install could get a green test while seat_core is NOT in `src/`. Today it's safe (editable install → `__file__` is `src/seat_core`, and the pyproject-packages test pins `src/seat_core`), so the risk is latent, not active — hence MEDIUM and non-blocking, with a one-line `is_relative_to(REPO_ROOT/"src")` fix recommended. A stressed filesystem or odd `PYTHONPATH` doesn't change correctness here because the assertion is path-identity, not I/O.

Third: a malicious or careless config. The backends take a model-spec string from the manifest; could it inject? `make_model` only `partition("/")`s it and dispatches by a closed `match` — an unknown backend raises `ValueError`, never silently defaults, and the spec is never shell-interpolated (ClaudeP uses a fixed argv). The one place untrusted-ish text reaches a subprocess is the *prompt* on stdin, which is data, not argv. The API-key scrub is the real security load-bearer and it survived the move verbatim. Fourth: what if pyproject has unexpected fields? The relocation test reads it with `tomllib` (safe, read-only) and only indexes known keys; a malformed file fails loud at parse. Net: the worst realistic failure is a future false-green if someone changes the install mode — captured as a MEDIUM finding — not a correctness or safety defect in what shipped.

**Pattern observed:** byte-identical relocation with a focused wiring-test harness that proves the *seam* (in-tree import, packaging, no path-dep, tests carried across) rather than re-testing already-covered internals — correct altitude for a move. at `tests/test_seat_core_relocation.py`.
**Error handling:** uniformly fail-loud — `ModelError`/`ValueError` on every bad path; no swallow, no silent default. evidence: `core.py:49-54`, `factory.py:27-31`.

**Handoff:** To SM (Camina Drummer) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): AC#2 ("no path dependency") is already vacuously satisfied — understudy never had a `../sidequest-seat-core` path dep because 159-2 (migrate-onto) was never implemented; understudy still uses its own parallel `brain/llm` backends. Affects `sidequest-understudy/src/understudy/brain/` (the relocation drops seat_core in alongside understudy's existing, unrelated brain — they are NOT unified by this story; that's the dissolved 159-2 / future companion work). *Found by TEA during test design.*
- **Question** (non-blocking): After this move, understudy will contain two parallel backend implementations (`understudy.brain.llm.*` and `seat_core.llm.*`). The companion-vs-understudy coupling decision (AC#5, deferred to Architect) determines whether/when these converge. Affects Plan A + `docs/superpowers/specs/2026-06-25-companion-seat-design.md`. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): Pre-existing lint debt in `sidequest-understudy/tests/test_reconnect.py` — 2 ruff E402 (module-level import not at top of file, lines 53-54; deliberate late imports after fixture/function defs). Unrelated to seat_core; untouched by this story; left as-is per minimalist scope. Affects `sidequest-understudy/tests/test_reconnect.py` (move imports to top or add a per-file `# noqa: E402` if the verify-phase quality gate flags it). *Found by Dev during implementation.*
- **Confirm** TEA's coexistence finding: understudy now holds two parallel backend stacks (`understudy.brain.llm.*` and the in-tree `seat_core.llm.*`). This is intentional for 159-6 (relocation only); convergence is the dissolved-159-2 / Architect-coupling question, not this story. No new action. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `tests/test_seat_core_relocation.py` has three LOW/MEDIUM test-hardening opportunities worth a quick follow-up touch — (1) `test_seat_core_is_in_tree` should assert `pkg_path.is_relative_to(REPO_ROOT / "src")` instead of `REPO_ROOT in parents` (current check also passes for a `.venv` site-packages install); (2) `test_seat_core_public_surface_importable` should add explicit `assert callable(make_model)` / `issubclass(SeatAxes, BaseModel)` probes to satisfy Python-checklist rule #6; (3) `read_text()` at line 84 should pass `encoding="utf-8"` (rule #5). All currently pass correctly and are backstopped by the 124-green suite — none blocks. Affects `sidequest-understudy/tests/test_seat_core_relocation.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Three pre-existing test-quality items in the *moved* (byte-identical) seat_core tests — `test_factory.py` couples to class `__name__` strings; `test_ollama.py` asserts the `Ping` schema shape inside a shared transport fixture; `test_claude_p.py` lacks a direct "JSON envelope missing `result` key" case. Carried over from 159-1, out of scope for a relocation; logged for a future test-quality pass. Affects `sidequest-understudy/tests/seat_core/`. *Found by Reviewer during code review.*
- **Question** (non-blocking): `epic-159.yaml` keeps `159-4 depends_on: 159-1`, whose original deliverable (the standalone repo) was deleted by 159-6. The dependency on the *completed* 159-1 still holds (seat_core exists, relocated) and the new Architect-coupling blocker is captured in the re-scope description, so no change is required — but the Architect may want to retarget `depends_on` when picking up 159-4. Affects `sprint/epic-159.yaml`. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 2 findings (1 Gap, 0 Conflict, 0 Question, 1 Improvement)
**Blocking:** None

- **Gap:** AC#2 ("no path dependency") is already vacuously satisfied — understudy never had a `../sidequest-seat-core` path dep because 159-2 (migrate-onto) was never implemented; understudy still uses its own parallel `brain/llm` backends. Affects `sidequest-understudy/src/understudy/brain/`.
- **Improvement:** Pre-existing lint debt in `sidequest-understudy/tests/test_reconnect.py` — 2 ruff E402 (module-level import not at top of file, lines 53-54; deliberate late imports after fixture/function defs). Unrelated to seat_core; untouched by this story; left as-is per minimalist scope. Affects `sidequest-understudy/tests/test_reconnect.py`.

### Downstream Effects

Cross-module impact: 2 findings across 2 modules

- **`sidequest-understudy/src/understudy`** — 1 finding
- **`sidequest-understudy/tests`** — 1 finding

### Deviation Justifications

1 deviation

- **AC#4 (delete standalone repo + remove orchestrator .gitignore entry) not covered by an automated test**
  - Rationale: Wrong-layer coupling. An in-repo test must not depend on the orchestrator's directory layout. The in-repo-appropriate guard for "no leftover coupling" (`test_no_standalone_seat_core_path_dependency`) IS written and passing.
  - Severity: minor
  - Forward impact: Reviewer must manually confirm the standalone `sidequest-seat-core/` repo is gone and `.gitignore` line `sidequest-seat-core/` is removed before approving.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **AC#4 (delete standalone repo + remove orchestrator .gitignore entry) not covered by an automated test**
  - Spec source: context-story-159-6.md / session AC#4
  - Spec text: "The standalone sidequest-seat-core/ repo is removed and its entry in the orchestrator .gitignore is deleted."
  - Implementation: No pytest assertion written for AC#4. The story branch and test suite live in sidequest-understudy; a test there asserting orchestrator-level cross-repo state (`../.gitignore`, absence of a sibling repo dir) would only pass when understudy is nested inside the orchestrator checkout — it breaks in a standalone/CI clone of understudy. Reviewer verifies AC#4 manually.
  - Rationale: Wrong-layer coupling. An in-repo test must not depend on the orchestrator's directory layout. The in-repo-appropriate guard for "no leftover coupling" (`test_no_standalone_seat_core_path_dependency`) IS written and passing.
  - Severity: minor
  - Forward impact: Reviewer must manually confirm the standalone `sidequest-seat-core/` repo is gone and `.gitignore` line `sidequest-seat-core/` is removed before approving.

### Dev (implementation)
- No deviations from spec. Took AC#1's documented default (top-level `src/seat_core/`, import name `seat_core` unchanged); package moved byte-identical (no internal change); no path dependency introduced (AC#2). Test location (`tests/seat_core/` subpackage) is unspecified by the AC and satisfies TEA's location-tolerant assertion — an implementation choice, not a spec deviation.

### Reviewer (audit)
- **TEA's "AC#4 not covered by an automated test"** → ✓ ACCEPTED by Reviewer: the wrong-layer-coupling rationale is correct — an understudy-resident test asserting orchestrator-level state (`../.gitignore`, sibling-repo absence) would break in a standalone clone. I verified AC#4 manually instead: `ls sidequest-seat-core` → absent; `grep seat-core .gitignore` → no match. The in-repo guard (`test_no_standalone_seat_core_path_dependency`) is the right in-scope substitute and is green.
- **Dev's "No deviations from spec" + `tests/seat_core/` location choice** → ✓ ACCEPTED by Reviewer: took the documented AC#1 default; byte-identical move (confirmed by 34 tests passing in-place); no path dep. The `tests/seat_core/` subpackage location is unspecified by the AC and satisfies the location-tolerant relocation test — agrees with author reasoning.
- No undocumented deviations found. The implementation matches all five ACs; the only divergence from Plan A is the *intended* reversal (standalone → in-tree) that is the entire point of story 159-6, fully documented in the doc banners and re-scope annotations.