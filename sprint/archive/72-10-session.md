---
story_id: "72-10"
jira_key: ""
epic: "72"
workflow: "trivial"
---
# Story 72-10: observation_pending gate-ordering assert

## Story Details
- **ID:** 72-10
- **Jira Key:** (none — SideQuest personal project)
- **Workflow:** trivial
- **Repos:** sidequest-server
- **Slug:** gate-ordering-assert
- **Assignee:** slabgorb
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-05-31T04:23:51Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-31T00:00:00Z | 2026-05-31T04:04:15Z | 4h 4m |
| implement | 2026-05-31T04:04:15Z | 2026-05-31T04:17:04Z | 12m 49s |
| review | 2026-05-31T04:17:04Z | 2026-05-31T04:23:51Z | 6m 47s |
| finish | 2026-05-31T04:23:51Z | - | - |

## Sm Assessment

**Setup complete — routing to Dev (trivial workflow, implement phase).**

- **Scope:** 1-point regression-guard chore in `sidequest-server`. Add a behavioral runtime invariant + OTEL violation span enforcing that `_apply_npc_observation_gate` runs before `_auto_mint_prose_only_npcs` in `_apply_narration_result_to_snapshot`. Today the ordering is comment-enforced only.
- **Context:** Full story context at `sprint/context/context-story-72-10.md` — verified seams, three derived behavioral ACs, and the critical project rule (NO source-text wiring test; assertion must be behavioral/OTEL/reflection, mirroring the 71-9 migration).
- **Critical guardrail for Dev:** Do NOT grep `narration_apply.read_text()` or assert source ordering. Drive the real apply path; assert via runtime invariant + dedicated `npc.*` violation span. Extend `tests/server/test_npc_observation_gate.py` using existing `otel_capture` / `_pending_member` / `_mention` helpers.
- **Out of scope:** Any gate/mint *logic* change, pool-cap (72-6), drift/reconcile (72-1/72-2/72-7). Only the ordering guard + its span.
- **No Jira** (personal project). Branch `feat/72-10-gate-ordering-assert` off sidequest-server develop.

## Design Deviations

### Dev (implementation)
- No deviations from spec. The story context blessed either placement (head-of-minter or the call site); I chose the **call site** in `_apply_narration_result_to_snapshot` (between the gate and mint calls) rather than the minter head, because `_auto_mint_prose_only_npcs` has 30+ direct test callers in `tests/server/test_npc_auto_mint_from_prose.py` that legitimately seed `observation_pending=True` members in isolation — a head-of-minter assert would false-fire on those. The call-site placement is reachable only from the real apply path, exactly matching AC1's "reachable from the real apply path" requirement, and leaves the isolated minter unit tests untouched. This is the placement the context's "at (or just before) the mint call" wording anticipates, so it is not a deviation.

### Reviewer (audit)
- **Call-site placement (not minter-head)** → ✓ ACCEPTED by Reviewer: verified the rationale is correct. `_auto_mint_prose_only_npcs` has 30+ direct unit-test callers (`tests/server/test_npc_auto_mint_from_prose.py`) that seed pending members in isolation; a head-of-minter assert would false-fire on every one. The call-site placement is reachable only from the real apply path (`_apply_narration_result_to_snapshot`), satisfies AC1's "reachable from the real apply path", and is the placement the context's "at (or just before) the mint call" wording anticipates. Sound engineering, correctly not a deviation.
- No undocumented deviations found. The implementation matches all three derived ACs and stays within scope (no gate/mint logic change).

## Delivery Findings

### Dev (implementation)
- No upstream findings. The seams documented in `context-story-72-10.md` were accurate (modulo line-number drift — gate/mint call site is now narration_apply.py:2998/3013, comment at 2989–2996, not the cited ~2503/~2518). Existing span/helper patterns in `telemetry/spans/npc.py` and the `otel_capture`/`_pending_member`/`_mention` test helpers were reused as directed; no new telemetry mechanism invented.

### Reviewer (code review)
- No upstream findings. The single review finding (test file fails `ruff format --check`) is a local format fix, not an upstream gap.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (sidequest-server):**
- `sidequest/telemetry/spans/npc.py` — new `SPAN_NPC_OBSERVATION_GATE_ORDER_VIOLATION` constant + `SpanRoute` (state_transition / npc_registry, mirroring the purge route) + `npc_observation_gate_order_violation_span` context-manager helper (severity="warning", carries `pending_count` / `pending_names` / `turn_number`). Auto-exported via the package's `from .npc import *`.
- `sidequest/server/narration_apply.py` — new `ObservationGateOrderError(RuntimeError)` + `_assert_observation_gate_preceded_mint(*, snapshot, turn_num)` guard, wired into `_apply_narration_result_to_snapshot` **between** the gate call (2998) and the mint call (3013). Behavioral invariant: the gate resolves every prior-turn `observation_pending` member (promote or purge), so a surviving pending member at the mint call site proves the gate did not run first → emit the violation span, then raise. Imports the new span helper.
- `tests/server/test_npc_observation_gate.py` — new Group H (8 tests): catalog/route/export/extract wiring (4), AC1 end-to-end (monkeypatch the gate to a no-op on the real apply path → raises + 1 violation span, severity=warning, names the survivor), AC2 (normal apply → no raise, zero violation spans, pipeline outcome undisturbed), plus direct-invocation arms of the guard for AC1 (raise+span on surviving pending) and AC2 (silent no-op on a clean/ratified pool).

**Design (why call-site, not minter-head):** see Design Deviations above — placement chosen to be reachable from the real apply path without false-firing the 30+ isolated `_auto_mint_prose_only_npcs` unit tests.

**ACs:**
- **AC1 (wrong order fails loud):** ✅ `test_mint_reached_without_gate_raises_and_emits_violation_span` + `test_assert_guard_raises_and_spans_on_direct_invocation`.
- **AC2 (correct order passes cleanly):** ✅ `test_normal_apply_emits_no_order_violation_span` + `test_assert_guard_passes_silently_when_no_pending_survives`; existing `test_apply_narration_result_runs_gate_before_auto_mint` still green (pipeline outcome unchanged).
- **AC3 (violation observable in OTEL):** ✅ dedicated `npc.observation_gate_order_violation` span, severity=warning (mirrors `npc.observation_gate_purged`), asserted via `otel_capture`.

**Tests:**
- Targeted: `tests/server/test_npc_observation_gate.py` — **40/40 passing** (8 new + 32 existing).
- Full server suite: **9261 passed, 360 skipped.** The 2 `tests/cli/validate/` failures (`test_all_live_packs_pass_content_validation`, `test_all_live_packs_pass_cross_reference_lint`) are **pre-existing baseline** — content-pack schema/cross-ref validators tracked under open epic-64 stories (64-15/16/17); measured in isolation and confirmed unrelated to this diff (diff is 3 NPC-pipeline/telemetry files, no path to content validation).
- Guard false-fire check: NO occurrence of `ObservationGateOrderError` / `observation_gate_order_violation` / `_assert_observation_gate_preceded_mint` anywhere in the full-suite output.
- `ruff check` clean on all 3 changed files.

**Branch:** `feat/72-10-gate-ordering-assert` (sidequest-server), pushed.

**Handoff:** To review phase (Colonel Potter / Reviewer).

---

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 (ruff format on test file) | confirmed 1, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — domain assessed by Reviewer |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — domain assessed by Reviewer |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — domain assessed by Reviewer |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — domain assessed by Reviewer |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — domain assessed by Reviewer |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings — domain assessed by Reviewer |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — domain assessed by Reviewer |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — domain assessed by Reviewer (python.md checklist run manually) |

**All received:** Yes (1 enabled subagent returned; 8 disabled via `workflow.reviewer_subagents`, their domains assessed directly below)
**Total findings:** 1 confirmed (LOW), 0 dismissed, 0 deferred

Preflight detail: ruff_check CLEAN on all 3 files; pyright 0 new errors in diff hunks (32 pre-existing in narration_apply.py, none overlapping the diff ranges); test file 40/40 GREEN; no debug prints / bare excepts / TODOs. One blocking item: `tests/server/test_npc_observation_gate.py` fails `ruff format --check`.

## Rule Compliance

Checked the diff against `.pennyfarthing/gates/lang-review/python.md` (13 checks) + CLAUDE.md/SOUL.md rules. Exhaustive enumeration of every new symbol:

- **#1 Silent exception swallowing** — COMPLIANT. No bare excepts, no swallowed exceptions in the diff. The guard *raises* `ObservationGateOrderError`; verified via AST that the sole enclosing `try` of the apply call (`websocket_session_handler.py` try@658, body 659–2221) has **zero except handlers** (try/finally), so the raise propagates uncaught — genuinely fail-loud, not swallowed.
- **#3 Type annotations at boundaries** — COMPLIANT. `_assert_observation_gate_preceded_mint(*, snapshot: GameSnapshot, turn_num: int) -> None` fully annotated, keyword-only. `npc_observation_gate_order_violation_span(*, pending_count: int, pending_names: str, turn_number: int, ...) -> Iterator[trace.Span]` annotated. `ObservationGateOrderError(RuntimeError)` — domain exception, not `raise RuntimeError(str)`.
- **#4 Logging coverage AND correctness** — COMPLIANT. Single `logger.warning(...)` uses lazy `%s/%d/%r` args (not f-string), severity=warning matches the span severity (AC3-mandated, mirrors `observation_gate_purged`). No sensitive data logged (internal NPC role-names only).
- **#6 Test quality** — COMPLIANT. 8 new tests, all with specific-value assertions (`== 1`, `== 2`, `== "warning"`, `in str(...)`); none vacuous. `monkeypatch.setattr(narration_apply, "_apply_npc_observation_gate", ...)` patches **where used** (correct target), not where defined. AC2 test verifies no-false-fire AND pipeline outcome preserved.
- **#10 Import hygiene** — COMPLIANT. New import inserted alphabetically into the existing `from sidequest.telemetry.spans import (...)` block. The `from .npc import *` in the spans package `__init__` is **pre-existing architecture** (every span module is star-imported there by design), not introduced by this diff; the new constant/helper auto-export through it consistently with all siblings.
- **#11 Input validation / #8 deserialization / #7 resource leaks / #9 async** — N/A. No user input, no deserialization, no file/network resources, no async in the diff. The span context-manager is used with `with` (no leak).
- **CLAUDE.md "No Source-Text Wiring Tests"** — COMPLIANT. Zero `read_text()`/source-grep assertions; all behavioral/OTEL. This was the load-bearing rule for the story and it is honored.
- **CLAUDE.md "No Silent Fallbacks"** — COMPLIANT. The guard is the embodiment of this rule (turns a silent gate no-op into a loud raise + span).
- **CLAUDE.md OTEL Observability Principle** — COMPLIANT. New `npc.observation_gate_order_violation` span defined, routed (`state_transition`/`npc_registry`), and asserted in tests.

## Reviewer Observations

- [LOW][preflight] `tests/server/test_npc_observation_gate.py` fails `ruff format --check` (1 file would be reformatted) — `narration_apply.py` and `npc.py` are already formatted. Confirmed independently. Blocks a clean tree / format gate. Fix: `uv run ruff format tests/server/test_npc_observation_gate.py` + recommit.
- [SILENT][VERIFIED] The `raise ObservationGateOrderError` is NOT swallowed — evidence: AST shows the apply call (`websocket_session_handler.py:872`) is contained only by `try@658` whose handler list is empty (try/finally), so the exception runs the finally and propagates. Additionally, the violation span is `with`-closed (exported) *before* the `raise` executes (`narration_apply.py` guard body), so AC3 observability holds even if a future caller wraps it. Fail-loud claim is accurate.
- [EDGE][VERIFIED] Empty-name edge handled — `pending_names` is built from `m.name` for named members only; the raise message falls back to `'<unnamed>'` and the guard still fires because `pending_count = len(unresolved) > 0` drives the decision, not name presence (`narration_apply.py` guard). A `None` `observation_pending` is treated falsy, symmetric with the gate's own `if not member.observation_pending` (`session_helpers.py:1966`) — no divergence.
- [TYPE][VERIFIED] `ObservationGateOrderError(RuntimeError)` is a named domain exception (not a bare `RuntimeError(msg)`); guard + span helper are fully typed and keyword-only — evidence: `narration_apply.py` def, `npc.py:707+` helper signature.
- [SEC][VERIFIED] No security surface — no untrusted input, SQL, HTML, path, or deserialization in the diff; only internal NPC role-name strings flow into a warning log (`%r`, lazy) and a span attribute. No secrets.
- [SIMPLE][VERIFIED] Minimal and pattern-faithful — the span constant/route/helper mirror the sibling `observation_gate_purged` trio exactly; the guard is ~15 lines, single responsibility. The named exception is justified (documented invariant, catchable/typed), not gold-plating.
- [DOC][VERIFIED] Docstrings/comments accurate — the "immediate, observable crash" characterization in `ObservationGateOrderError` is confirmed true (raise propagates per the AST check). Comment density is high but matches the heavy-comment house style of `narration_apply.py`/`npc.py`.
- [RULE][VERIFIED] python.md checklist passes across all 3 files (see Rule Compliance). The only flagged item is the format reflow (#6-adjacent / clean-tree), already captured as the LOW finding above.
- [TEST][VERIFIED] AC coverage is real and non-coupled: AC1 end-to-end (monkeypatched gate → raise + 1 span) + direct-invocation arm; AC2 normal-apply (no span, no raise, Mother stays pending) + clean-pool arm; AC3 span attributes (severity=warning, pending_count, pending_names). 40/40 green.

## Devil's Advocate

Let me argue this code is broken. **First attack — the guard is a no-op in production and only ever fires in tests.** In correct operation the gate always resolves pending members, so `_assert_observation_gate_preceded_mint` returns at the `if not unresolved` line on every real turn. Is this dead weight? No: that is precisely the design of a regression guard — it is silent until a *future* refactor breaks the order, at which point it fires. The tests prove it fires on the broken-order condition (monkeypatched gate), so the guard is live and exercised, not dead. **Second attack — false positives crash real games.** Could a legitimate production turn leave a pending member surviving the gate and thus crash on a healthy game? Walk the gate: `_apply_npc_observation_gate` iterates `snapshot.npc_pool`, and for every `observation_pending=True` member it either flips the flag to `False` (promote, kept) or drops it (purge). After the loop, `snapshot.npc_pool[:] = survivors` — no `observation_pending=True` member can remain. The only early-return is `if not snapshot.npc_pool: return`, which leaves an empty pool (zero pending). And nothing executes between the gate call and the guard (verified: the guard is inserted immediately after the gate's closing paren). So no healthy turn can trip it — the false-positive crash is impossible given the gate runs first. **Third attack — a confused maintainer reorders and the guard hides it.** If someone moves the mint above the gate, does the guard catch it? Yes — the mint would run first, leaving this turn's fresh mints (and any prior-turn survivors) as pending when the guard runs, firing the span + raise. The guard is positioned to catch exactly the regression it names. **Fourth attack — the exception gets swallowed upstream, defeating "fail loud."** I chased this hard: the apply call's only enclosing `try` is a try/finally with no except, so the raise propagates. Even in the hypothetical where a future caller wraps it in `except Exception`, the span is exported before the raise, so the GM-panel lie-detector still records the violation — the observable signal (the story's actual deliverable) is robust to swallowing. **Fifth attack — stressed filesystem / weird config.** No filesystem, no config, no I/O in this diff; the only state is the in-memory `snapshot.npc_pool`. Nothing here degrades under load. **Conclusion of devil's advocacy:** the logic is sound; the only real defect is cosmetic (format reflow on the test file). No new bug surfaced that the review missed.

## Reviewer Assessment

**Verdict:** APPROVED (lone LOW format finding resolved in-phase)

**Finding history (resolved):**

| Severity | Issue | Location | Resolution |
|----------|-------|----------|------------|
| [LOW] | Test file would be reflowed by `ruff format` | `tests/server/test_npc_observation_gate.py` | ✅ Fixed — `ruff format` applied, commit `b8677ea4`; all 3 files now `ruff format --check` clean; 40/40 still green. |

**Disposition note:** Initial verdict was REJECTED on the format finding, but on inspection the project gates (`just server-check` = lint+test, `check-all`) do **not** run `ruff format --check` — the reflow was cosmetic and ungated, not a true merge blocker. The trivial workflow has no rework edge, so per the user's direction (Doctor, "Approve + apply format") the formatter was run, committed to the branch (`b8677ea4`), and the verdict reconciled to APPROVED. The code was approve-worthy on the merits throughout; only the cosmetic reflow stood between it and a fully clean tree, and that is now applied.

**Why APPROVED:** implementation is correct, in-scope, well-tested (40/40), rule-compliant (python.md 13-check + CLAUDE.md "No Source-Text Wiring Tests" / "No Silent Fallbacks" / OTEL Observability — all honored), with no logic, edge, type, security, or silent-failure findings. Tree is now format-clean.

**Dispatch tags covered:** [EDGE] [SILENT] [TEST] [DOC] [TYPE] [SEC] [SIMPLE] [RULE] — all assessed (preflight live; the eight thematic subagents disabled via settings, domains covered directly above).

**Data flow traced:** `snapshot.npc_pool` (post-gate) → `_assert_observation_gate_preceded_mint` filters `observation_pending` survivors → on violation, names flow into a warning log (`%r`) + span attributes (`pending_count`/`pending_names`/`turn_number`) → `npc.observation_gate_order_violation` span exported → `raise` propagates uncaught (verified: sole enclosing `try@658` is try/finally). Safe: no untrusted input, no secrets, observability fires before the raise.

**Handoff:** To SM (Hawkeye) for finish — PR creation + squash-merge to develop.