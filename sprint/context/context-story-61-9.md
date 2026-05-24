---
parent: context-epic-61.md
workflow: tdd
---

# Story 61-9: Commit to SDK narrator: remove legacy output_only prose and claude -p/Ollama narrator paths

## Business Context

The runaway-Valley incident (epic 61 §Overview) burned ~$313 in 48 hours partly because the narrator prompt carries dual prose paths — one for the Anthropic SDK tool-use backend and one for the legacy `claude -p` / Ollama text-completion backends — that must be maintained in lockstep. ADR-101 made `anthropic_sdk` the production default (`SIDEQUEST_LLM_BACKEND`); ADR-102 moved structured output from JSON sidecars to native tool-use. The legacy `output_only.md` (~3,610 tokens, byte-identical to pre-E1.5-A behavior) now ships with **zero live consumer** but doubles the maintenance surface of every narrator-prompt change and forces every tool-routing test to gate twice.

The deeper risk is silent divergence: the legacy prose instructs the model to emit a FULL sidecar covering 8 categories that the SDK path zeroes (because tool-use owns those categories). The moment any operator flipped `SIDEQUEST_LLM_BACKEND=claude_cli` against the current SDK prose, the model would be told to call tools it does not have — a textbook **NO-FALLBACK violation** per project memory. Removing the dead path eliminates the divergence-by-construction and cuts maintenance cost on every future narrator-prompt change in this epic (61-10, 61-11, **61-12** — the 50% prose compaction that lands after this story renames the file).

Customer-facing impact: zero. Narrator output is unchanged. This is a maintenance-surface and correctness story, not a feature.

## Technical Guardrails

**From epic 61 architecture:** every change to narrator prompt construction must preserve ADR-098 §Decision ("prompt size is bounded by section selection") and ADR-110 §Phase B (allowlist DROP discipline). 61-9 does not touch snapshot fields or section selection; the rules are referenced only to confirm this story does NOT reopen them.

**Files in scope (server repo, all paths under `sidequest-server/`):**

| File | Change |
|------|--------|
| `sidequest/agents/narrator_prompts/output_only.md` | DELETE (legacy prose) |
| `sidequest/agents/narrator_prompts/output_only_sdk.md` | RENAME to `output_only.md` (SDK prose keeps the canonical name tests already know) |
| `sidequest/agents/narrator_prompts/__init__.py` | DROP `NARRATOR_OUTPUT_ONLY` const; RENAME `NARRATOR_OUTPUT_ONLY_SDK` → `NARRATOR_OUTPUT_ONLY` |
| `sidequest/agents/narrator.py:252-301` (`build_output_format`) | DROP `tool_backend` kwarg + remove the gating branch; always emit SDK prose |
| `sidequest/agents/orchestrator.py:1465` | DROP `tool_backend` kwarg at call site |
| `sidequest/agents/orchestrator.py:2225-2233` | Collapse telemetry `tool_backend` conditional (now always `True`) — **DECISION REQUIRED, see below**. |
| `sidequest/agents/llm_factory.py` | Add `purpose: Literal["narrator", "tool"]` kwarg (default `"narrator"`) to `build_llm_client()`. RAISE LOUD (`NarratorBackendRetired(LlmClientError)` or `UnknownBackend`) when `purpose == "narrator"` AND env is `claude` / `ollama`. Tool callers pass `purpose="tool"`. Gate fires at construction, NOT at narrator-build time. |
| `sidequest/server/app.py:105` | Narrator factory site — already defaults to `purpose="narrator"`; no change beyond honoring the new kwarg. |
| `sidequest/server/websocket_session_handler.py:1205` | Drop bare `ClaudeClient` default or replace with `lambda: build_llm_client(purpose="narrator")`. The `claude_client_factory` parameter still flows through but its local default is a fallback that AC-3 forbids. |
| `sidequest/dungeon/session_integration.py:155` | Call as `build_llm_client(purpose="tool")` to opt out of the narrator gate. |

**DECISION LOCKED — OTEL span at `orchestrator.py:2225-2233`: OPTION (a).**

User decision 2026-05-24: keep the span, drop the `tool_backend` attribute, hard-wire `guardrails_skipped` and `bytes_saved` as constants. Span survives as a cheap "migration engaged" dashboard signal.

RED tests for this surface assert:
- The narrator-emit OTEL span at line 2225-2233 still emits (same span name).
- `attrs.get("tool_backend")` returns `None` (attribute removed, not set to a constant).
- `attrs.get("guardrails_skipped")` equals the full `GUARDRAIL_NAMES` set (hard-wired constant).
- `attrs.get("bytes_saved")` equals `TOTAL_PROSE_BYTES` (hard-wired constant).
- 57-4 tests at lines 476-477, 520-521 — DELETE the `tool_backend is True/False` assertions; KEEP the span-emission assertion; ADD assertions for the two constants if not already present.

**Patterns to follow:**

- **NO-FALLBACK (project memory `feedback_no_fallbacks_hard`).** The narrator-with-legacy-backend path is being retired with **zero backstop**. Do not introduce a "degraded → silent alternative path"; fail LOUD (raise + surfaced error message). No `if backend != "anthropic_sdk": warn(...) ; return SdkClient(...)` shenanigans.
- **No content-coupled tests (`feedback_no_content_coupled_tests`).** Tests should assert prose-content equivalence on `NARRATOR_OUTPUT_ONLY` after the rename. They should NOT load live `genre_packs/*` to assert SDK-only behavior at runtime.
- **One mechanism per problem (`feedback_one_mechanism_per_problem`).** Do not introduce a second detection path for "is this a narrator caller?" beyond what already exists in `llm_factory.py`. Architect §B identifies the chokepoint; use it.

**ADR amendments required (post-implementation, doc-only):**

- ADR-101 amendment: legacy narrator backends (`claude_cli`, `ollama`) are retired for narration as of this story. `claude -p` remains available for non-narrator callers (e.g. dungeon `curate`).
- This amendment is a **doc deliverable** (Tech Writer surface). NOT a code AC. Flag in review-phase Delivery Findings; do not block green on it.

**Dependencies / sequencing:**

- 61-12 (50% prose compaction) is sequenced AFTER 61-9. 61-9 renames `output_only_sdk.md` → `output_only.md`; 61-12 then compacts the renamed file. No live coordination needed — 61-12 is `backlog` and will not start until 61-9 ships.
- 61-10 (promote 6 byte-static sections to System bucket) and 61-11 (scene-gate genre prose) are independent of this story's surface; they touch `prompt_framework/bucket.py`, not `narrator_prompts/`.

## Scope Boundaries

**In scope:**

- Delete legacy `output_only.md`; rename `output_only_sdk.md` → `output_only.md`.
- Refactor `narrator_prompts/__init__.py`, `narrator.py`, `orchestrator.py` to drop `tool_backend` kwarg and the gating branch (always SDK prose).
- Add loud-fail gate in `llm_factory.py` for narrator construction with `claude_cli` / `ollama` backend.
- Rewrite or delete narrator/magic tests that parameterized over `tool_backend`; preserve every assertion that survives the dual-backend collapse.
- Verify full server test suite passes (`uv run pytest -v`).
- ZERO references to `NARRATOR_OUTPUT_ONLY_SDK` remain in production code or tests (the const is renamed, not duplicated).

**Out of scope:**

- **Prose content edits to the renamed file.** Compaction belongs to 61-12; this story is a pure refactor + dead-path deletion. Byte-for-byte the SDK prose ships unchanged (modulo the filename). 61-12 must re-anchor any in-flight draft against the post-61-9 file.
- **Removing `claude_client.py` outright.** The class stays for `ab_eval_harness.py` (offline A/B eval CLI; Architect §A) — note that the dungeon `curate` path described in the story memo is *already SDK-only in practice* because it calls `complete_with_tools` (Architect §A) — but `ClaudeClient` itself stays for the harness.
- **Tool-use protocol changes.** ADR-102's tool surface is unchanged. We are deleting the LEGACY-text-completion prose; the SDK tool contract is untouched.
- **Snapshot or section-selection changes.** Epic 61's other stories own that surface (61-2, 61-10, 61-11).
- **ADR-101 amendment authoring.** Out-of-scope as a code AC; flagged for Tech Writer review-phase handling.
- **Renaming the `claude_client` parameter across `dungeon/*.py` to `tool_client` / `sdk_client`.** Boy-scout opportunity flagged by Architect §A — low-cost but not blocking. Defer or fold in only if green is otherwise clean.
- **Removing the OllamaClient class itself** — the gate is on `purpose="narrator"`; the class can stay as dead code for future re-introduction if anyone wants Ollama as a tool backend. Mark `# Retired as narrator backend per story 61-9 / ADR-101 amendment` near the import to head off rediscovery confusion.

## AC Context

**AC-1: File rename + delete.** Two filesystem operations: `git rm sidequest/agents/narrator_prompts/output_only.md` and `git mv sidequest/agents/narrator_prompts/output_only_sdk.md sidequest/agents/narrator_prompts/output_only.md`. Verifiable by `git status` and `ls sidequest/agents/narrator_prompts/`. Test must assert the file at the canonical path contains SDK-shape prose (tool-use directive language, the `<full_sidecar>` zeroed-categories block is GONE).

**AC-2: `build_output_format` signature.** Inspect `narrator.py:252-301`. The new signature has NO `tool_backend` parameter; the gating branch is removed; the function returns the SDK prose unconditionally. Caller-site at `orchestrator.py:1465` passes no `tool_backend`. Test must call `build_output_format()` with no kwargs and assert the returned string is SDK prose. Test must also confirm via `inspect.signature(NarratorAgent.build_output_format)` that `tool_backend` is not in the parameter list (compile-time-style assertion).

**AC-3: `llm_factory.py` loud-fail via `purpose` kwarg.** This is the load-bearing AC. The mechanism (architect-confirmed) is a `purpose: Literal["narrator", "tool"]` kwarg on `build_llm_client()` (default `"narrator"`). Three cases must hold simultaneously:

1. `build_llm_client(purpose="narrator")` with `SIDEQUEST_LLM_BACKEND=claude` raises a typed error (recommended: `NarratorBackendRetired(LlmClientError)`) containing the backend name AND a remediation pointer ("ADR-101: SDK is the sole narrator backend").
2. `build_llm_client(purpose="narrator")` with `SIDEQUEST_LLM_BACKEND=ollama` raises the same typed error.
3. `build_llm_client(purpose="tool")` with `SIDEQUEST_LLM_BACKEND` set to `claude` or `ollama` raises the same loud error (Architect §A: those backends do not implement `complete_with_tools`, so they can never satisfy a tool caller either — fail at config boundary, not at first method call). Concretely: only `anthropic_sdk` is a viable backend for any caller; the gate just stops pretending otherwise.

Default-case happy paths to assert:
- `build_llm_client()` (no kwarg) with `SIDEQUEST_LLM_BACKEND=anthropic_sdk` (or unset) → returns a narrator-capable `ToolingLlmClient`.
- `build_llm_client(purpose="tool")` with same env → returns a `ToolingLlmClient` for dungeon curate / lookahead worker.

Architectural note (Architect §B, rejected alternative): a runtime `isinstance` check at narrator-build time is REJECTED. It shifts the error from a config boundary to a deep call site; the existing `isinstance(self._client, ToolingLlmClient)` at `orchestrator.py:2225` IS the degraded path AC-3 wants gone. Test that this `isinstance` branch no longer chooses prose (either by inspection or by asserting `build_output_format` ignores client type).

Non-narrator callers (Architect §A enumeration):
- `sidequest/dungeon/materializer.py` + `sidequest/dungeon/lookahead_worker.py` — receive client via `session_integration.py`. Variable is named `claude_client` but the runtime contract calls `complete_with_tools` (SDK-only). **Already SDK-only in practice.** Boy-scout opportunity: rename param to `tool_client` (Dev-flagged, not blocking).
- `sidequest/agents/ab_eval_harness.py` — offline A/B eval CLI. Constructs `ClaudeClient` directly, bypasses `build_llm_client()`. Unaffected by the factory gate; survives untouched.
- All other importers of `claude_client.py` are narrator callers and are retired by AC-2.

**AC-4: Test parameterization collapse.** Architect §E classifies each test file precisely — TEA should write RED tests against this classification:

| Test file | Classification | Action |
|-----------|----------------|--------|
| `test_narrator_output_format_backend_gate.py` | Single-purpose file; its entire raison d'être is asserting legacy-vs-SDK divergence (5 backend-gated tests + a few "sentinels mutually exclusive" tests, NOT pytest.mark.parametrize) | **DELETE.** Salvageable invariants (e.g. SDK-prose contains the tool-field allowlist at lines 211-275) move to `test_narrator.py` or a new `test_narrator_output_format.py` — but those are not backend-gated and don't need this file's frame. |
| `test_50_24_player_check_seam.py` | Branch among many; uses a `_composed_output_format(*, tool_backend: bool)` helper, with one explicit comparison test at line 179 (`test_player_check_rule_is_sdk_path_specific_not_legacy_only`) | **REWRITE.** Drop `tool_backend` kwarg from the helper; delete the line-179 comparison test; the rest stand. |
| `test_57_4_recency_guardrails_migration.py` | Branch among many; heavy `@pytest.mark.parametrize` over `GUARDRAIL_NAMES`. "Legacy preservation (AC3)" tests at lines 499-556 + OTEL `tool_backend` attribute assertions at 476-477, 520-521 | **REWRITE.** Keep SDK-side guardrail-migration tests; DELETE the legacy-preservation tests; rewrite OTEL assertions per the **DECISION REQUIRED** above (option (a) → assert attribute absent; option (b) → assert span absent). Dev also updates module docstring (lines 9-12, 22-25) which explicitly names `claude -p` / Ollama. |
| `test_50_24_dice_contract_parity.py` | Already SDK-only (5 `NARRATOR_OUTPUT_ONLY_SDK` refs, no legacy branch) | **MECHANICAL CONSTANT RENAME only.** `NARRATOR_OUTPUT_ONLY_SDK` → `NARRATOR_OUTPUT_ONLY`. Not in scope for branch-pruning. |
| `test_narrator.py` | Branch among many; 8 `build_output_format` references; current default is `tool_backend=False` (legacy prose) | **MECHANICAL VERIFY.** Calls keep working after AC-2 removes the kwarg, but the assertions currently target legacy prose. After rename, the renamed const points to SDK prose — TEA must RUN this file, not just inspect. Likely passes (SDK is structurally compatible), but the SDK prose at line 152 `test_build_output_format_content_contains_game_patch` could phrase the rule differently. |
| `test_47_9_innate_proactive.py` (tests/magic/) | Imports `NARRATOR_OUTPUT_ONLY` with 11 references; asserts the CRITICAL MAGIC RULE prose | **MECHANICAL VERIFY — HIGHEST RISK.** Architect §D flags this as the most likely test to break post-rename: the legacy CRITICAL MAGIC RULE phrasing may not be byte-identical between `output_only.md` (legacy) and `output_only_sdk.md` (SDK). TEA must RUN this file post-rename. If assertions break, Dev updates phrase-match strings to the SDK spelling, NOT skip/xfail. |
| `test_narrator_pre_prompt.py` (tests/magic/), `test_narrator_prompt.py`, `test_50_2_confrontation_trigger_prompt.py` | Single-import each of `NARRATOR_OUTPUT_ONLY` | Same MECHANICAL VERIFY discipline — run them, expect them to still pass against the SDK prose; if any assertion fails, update the phrase to match the new spelling. |

**AC-1 silent flip risk (Architect §D).** Before the rename, `NARRATOR_OUTPUT_ONLY = _load("output_only.md")` = legacy prose. After the rename, the legacy file is gone and the SDK prose is loaded into the same constant name. The constant name is unchanged but its content silently flips. The 4 magic-suite tests above plus `test_narrator.py` will all dereference a different string post-rename — most should pass (SDK prose is a superset of the legacy invariants), but TEA MUST run them to confirm rather than infer.

**AC-5: Zero `NARRATOR_OUTPUT_ONLY_SDK` references.** Verifiable by `git grep -nE 'NARRATOR_OUTPUT_ONLY_SDK'` returning empty in the worktree post-implementation. Test surface: add a CI-style grep assertion in the test suite (or rely on import-time `AttributeError` — the const simply does not exist after rename). Full suite must pass.

**AC-6: ADR-101 amendment.** Doc deliverable, not a code AC. Captured in **Out of scope** above — Tech Writer surface; flag in review-phase Delivery Findings. Verification by `grep -n 'claude -p\|ollama' docs/adr/101-*.md` showing the amendment section exists with today's date and a link to this story's session/PR.

## Assumptions

- **Architect tandem observations are load-bearing for §A, §B, §C, §E.** This context document was drafted before the architect backseat completed. TEA must read `.session/61-9-tandem-architect.md` before writing tests; the §C blast-radius list and §B chokepoint mechanism are the authoritative source for which production sites need test coverage. If the tandem failed to spawn or produced incomplete observations, TEA must grep `claude_client`, `tool_backend`, and `NARRATOR_OUTPUT_ONLY_SDK` directly across `sidequest-server/sidequest/**` and `sidequest-server/tests/**` before declaring the blast radius bounded.
- The worktree at `sidequest-server/.worktrees/story-61-9-sdk-commit` is freshly branched off `origin/develop` (verified at setup). Uncommitted edits on the main `develop` checkout (`narrator_guardrails.py`, `combat_rules.md`, `dialogue_rules.md`) are NOT in this worktree and do not affect this story.
- `claude -p` retains a single non-narrator consumer (dungeon `curate`). Architect §A confirms or expands this set; if other narrator-shaped callers exist that the description missed, log as a Design Deviation.
- The SDK prose at `output_only_sdk.md` is current and correct (per recent commit `bbd78ec` — "narrator prompt compaction + SDK commitment"). 61-9 does NOT validate prose content; only the wiring around it.
- pytest collection on the worktree's venv succeeds after `uv sync` (no stale shebang per project memory `feedback_stale_venv_shebangs`).

If any of these assumptions proves wrong during RED phase, log under `## Design Deviations → ### TEA (test design)` in the session file with the 6-field format.
