---
story_id: "71-14"
jira_key: ""
epic: ""
workflow: "trivial"
---
# Story 71-14: Test-file pyright cleanup for 71-5 — +13 type-looseness in opening-POV test files + 2 visibility_sidecar alias false-positives (pyright-ignore)

## Story Details
- **ID:** 71-14
- **Jira Key:** (none — personal project)
- **Workflow:** trivial
- **Stack Parent:** none

## Context

This is a pure test-file type-hygiene story (trivial, 1pt, p3). No production code changes — only pyright cleanup in test files for the 71-5 / 71-13 opening-POV work.

**Verified current state:**
- `uv run pyright` on the two opening-POV test files reports **38 errors, 0 warnings** (not clean).
- The exact `visibility_sidecar` false-positives the title names are present: e.g. `tests/server/test_opening_pov_swap_71_5.py:77` and `tests/server/test_opening_emit_event_71_13.py:482/534/586/639` — all `error: No parameter named "visibility_sidecar" (reportCallIssue)`. These are aliases/false-positives that need `# pyright: ignore[reportCallIssue]` (or the correct param/type fix if the alias is real).
- Plus type-looseness errors: e.g. `CharacterCreationMessage` not assignable to `GameMessage`, multiple `reportOptionalMemberAccess` on `None`.

**Affected files (server repo):**
- tests/server/test_opening_pov_swap_71_5.py
- tests/server/test_opening_emit_event_71_13.py

## Acceptance Criteria

1. `uv run pyright` reports 0 errors on tests/server/test_opening_pov_swap_71_5.py and tests/server/test_opening_emit_event_71_13.py
2. The 2 visibility_sidecar reportCallIssue false-positives are resolved via targeted `# pyright: ignore[reportCallIssue]` (or a real param/type fix if the alias is genuinely wrong) — NOT a blanket file-level ignore
3. The ~13 type-looseness errors (CharacterCreationMessage→GameMessage assignment, reportOptionalMemberAccess on None) are resolved with proper narrowing/annotation, not suppression where a real fix is cheap
4. No production (non-test) source files are modified — this is test-file hygiene only
5. No test behavior changes — the tests still assert the same things (pyright-only change)

## Sm Assessment

**Setup complete.** Session, context, ACs, and branch are in place for a trivial (phased) pyright-hygiene story.

- **Repo:** sidequest-server (gitflow, base `develop`)
- **Branch:** `feat/71-14-pyright-cleanup-71-5-opening-pov` (created from develop)
- **Scope:** test-file pyright cleanup ONLY — no production source changes, no behavior changes. Two files: `tests/server/test_opening_pov_swap_71_5.py`, `tests/server/test_opening_emit_event_71_13.py`.
- **Verified entry state (this session):** `uv run pyright` reports 38 errors / 0 warnings across the two files, including the named `visibility_sidecar` `reportCallIssue` false-positives and ~13 type-looseness errors (CharacterCreationMessage→GameMessage, reportOptionalMemberAccess on None).
- **Gate prerequisites:** merge gate clear (0 open PRs across all repos); local test DBs at alembic head (0002). No Jira (personal project).

**Routing:** trivial workflow → `implement` phase → Agent Smith (dev). Dev should make `uv run pyright` clean on both files per the ACs, preferring real narrowing/annotation over suppression, and reserving targeted `# pyright: ignore[reportCallIssue]` for the genuine `visibility_sidecar` alias false-positives. No blanket file-level ignores.

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-05-29T21:50:02Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-29T21:28:24Z | 2026-05-29T21:30:05Z | 1m 41s |
| implement | 2026-05-29T21:30:05Z | 2026-05-29T21:40:25Z | 10m 20s |
| review | 2026-05-29T21:40:25Z | 2026-05-29T21:50:02Z | 9m 37s |
| finish | 2026-05-29T21:50:02Z | - | - |

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `tests/server/test_opening_pov_swap_71_5.py` — pyright cleanup: 1 `_canned_opening` return-type annotation (`list[object]`→`list[NarrationMessage]`), 2 `assert sd is not None`, 1 `assert handler._room is not None`, 3 targeted `# pyright: ignore[reportArgumentType]` (handle_message arg), 1 `# pyright: ignore[reportCallIssue]` (visibility_sidecar), 1 `# pyright: ignore[reportCallIssue, reportArgumentType]` (psycopg dynamic TRUNCATE).
- `tests/server/test_opening_emit_event_71_13.py` — pyright cleanup: `from typing import cast` import, `cast(TracerProvider, current)` in the OTEL `hasattr` branch, 3 `assert sd is not None`, 6 `# pyright: ignore[reportCallIssue]` (visibility_sidecar), 4 `# pyright: ignore[reportArgumentType]` (handle_message arg), 1 `# pyright: ignore[reportCallIssue, reportArgumentType]` (psycopg dynamic TRUNCATE).

**Pyright:** 0 errors / 0 warnings on both files (was 38 errors). 
**Tests:** 10/10 passing (GREEN) — `uv run pytest -n0 tests/server/test_opening_pov_swap_71_5.py tests/server/test_opening_emit_event_71_13.py` against `sidequest_test` (alembic head 0002). No behavior change: the added asserts are always-true narrowing in these fixtures.
**Production source:** none modified (AC4). 
**Branch:** feat/71-14-pyright-cleanup-71-5-opening-pov (pushed)

**Handoff:** To review (The Merovingian).

## Delivery Findings

<!-- Dev appends below -->
### Dev (implementation)
- **Improvement** (non-blocking): `handle_message` is typed `msg: GameMessage` where `GameMessage` is a `RootModel[_Phase1Variant]` wrapper, but every caller (these tests and the wider suite, e.g. `test_45_6_chargen_archetype_gate.py`) passes a bare union *member* (`CharacterCreationMessage`, etc.) which the body actually consumes. The annotation should be the member union (`_Phase1Variant`) or accept members directly. Affects `sidequest/server/websocket_session_handler.py:364` (`handle_message` signature). Until fixed, every member-arg call site needs a `reportArgumentType` suppression. *Found by Dev during implementation.*

<!-- Reviewer appends below -->
### Reviewer (code review)
- **Improvement** (non-blocking): CONFIRMS and reinforces the Dev finding above. Verified the runtime contract at `sidequest/server/websocket_session_handler.py:372` — `handle_message` does `msg_type: str = msg.type  # type: ignore[attr-defined]`, accessing `.type` directly on the bare member. Because `GameMessage` is `RootModel[_Phase1Variant]` (no `.type` on the wrapper), the reviewer-type-design subagent's suggested "fix" (`GameMessage(root=CharacterCreationMessage(...))`) would raise `AttributeError` at runtime and break the suite. The correct production fix is to retype `handle_message(msg: _Phase1Variant)` (the discriminated member union), which would let the 7 test-side `reportArgumentType` ignores be removed across the whole suite. Recommend a dedicated production-scope story. *Found by Reviewer during code review.*

## Design Deviations

<!-- Dev appends below -->
### Dev (implementation)
- **handle_message arg suppressed instead of real-fixed**
  - Spec source: .session/71-14-session.md, AC-3 ("resolved with proper narrowing/annotation, not suppression where a real fix is cheap")
  - Spec text: "The ~13 type-looseness errors ... are resolved with proper narrowing/annotation, not suppression where a real fix is cheap"
  - Implementation: Used targeted `# pyright: ignore[reportArgumentType]` at the 7 `handle_message(CharacterCreationMessage(...))` call sites instead of a type fix.
  - Rationale: The only real fix is widening `handle_message`'s annotation (production code), which AC-4 explicitly forbids ("No production source files are modified"). Targeted per-call suppression is the correct test-scope resolution; logged as a Delivery Finding for a future production story.
  - Severity: minor
  - Forward impact: none — purely a type-suppression; a later production retype of `handle_message` would let these ignores be removed.
- **psycopg dynamic TRUNCATE suppressed instead of psycopg.sql rewrite**
  - Spec source: .session/71-14-session.md, AC-3
  - Spec text: "not suppression where a real fix is cheap"
  - Implementation: Added `# pyright: ignore[reportCallIssue, reportArgumentType]` on the `conn.execute(f"TRUNCATE {names} ...")` line in both files' `_pg_isolation` fixtures.
  - Rationale: The error is psycopg's deliberate `LiteralString` strictness on non-literal SQL. The "real fix" (rewrite to `psycopg.sql.Identifier` composition) is moderately invasive in per-test isolation teardown where a mistake fails the entire file; the table names come from the trusted `pg_tables` catalog. Judged not "cheap" given the breakage risk; targeted suppression is the safer, behavior-preserving choice.
  - Severity: trivial
  - Forward impact: none.

<!-- Reviewer appends below -->
### Reviewer (audit)
- **handle_message arg suppressed instead of real-fixed** → ✓ ACCEPTED by Reviewer: The real fix is production-side (retype `handle_message` off the `GameMessage` RootModel wrapper to the `_Phase1Variant` member union), which AC-4 explicitly forbids ("No production source files are modified"). Independently verified at `websocket_session_handler.py:372` that the bare-member call is the *correct* runtime contract (`msg.type` is read directly), so the per-call targeted ignore is right and the reviewer-type-design "wrap in GameMessage(root=...)" alternative would break runtime. Logged as a delivery finding for a future production story.
- **psycopg dynamic TRUNCATE suppressed instead of psycopg.sql rewrite** → ✓ ACCEPTED by Reviewer: Test-isolation teardown with table names sourced from the trusted `pg_tables` catalog; reviewer-security confirmed zero injection surface. The suppression carries specific codes and silences psycopg's `LiteralString` pedantry, not a runtime defect. A future `psycopg.sql.Identifier` composition would be marginally cleaner but is non-blocking and not "cheap" given the file-wide breakage risk in teardown.
- No undocumented deviations found — the diff matches the logged scope (test-file pyright hygiene only; zero production source).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (GREEN: 10/10 tests, ruff clean, 0 pyright, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Yes | clean | none | N/A |
| 3 | reviewer-silent-failure-hunter | Yes | clean | none | N/A |
| 4 | reviewer-test-analyzer | Yes | findings | 4 (vacuous-assertion, high) | dismissed 4 (load-bearing pyright narrowing, not rule-#6 vacuous; corroborated by rule-checker + edge-hunter; always-true nature is what guarantees AC5) |
| 5 | reviewer-comment-analyzer | Yes | clean | none | N/A |
| 6 | reviewer-type-design | Yes | findings | 5 (2 "verified good", 1 high handle_message, 2 medium) | confirmed 1 (handle_message — but as already-handled delivery finding, non-blocking), dismissed 2 (visibility_sidecar via AC-2; suggested handle_message fix rejected — breaks runtime), accepted 2 verified-good |
| 7 | reviewer-security | Yes | clean | none (TRUNCATE not exploitable) | N/A |
| 8 | reviewer-simplifier | Yes | findings | 3 (1 high wrapper, 1 med isinstance, 1 low) | dismissed 3 (non-blocking style; real fix is production-side delivery finding; cast is hasattr-guarded & type-design-confirmed sound) |
| 9 | reviewer-rule-checker | Yes | clean | none (16 rules / 29 instances / 0 violations) | N/A |

**All received:** Yes (9 returned, 3 with findings)
**Total findings:** 1 confirmed (non-blocking, already logged as delivery finding), 9 dismissed (with rationale), 0 deferred. Zero Critical/High.

## Reviewer Assessment

**Verdict:** APPROVED

Pure test-file pyright hygiene: 38 errors → 0 across two opening-POV test files, 10/10 tests still green, zero production source touched. No Critical/High findings. The three specialists that returned findings surfaced only style/maintainability suggestions and one already-logged production annotation issue — none block.

**Data flow traced:** test fixture `pg_tables` catalog → `names` (double-quoted identifiers) → `conn.execute(f"TRUNCATE {names} ...")`. Safe because the source is the trusted Postgres system catalog in a worker-local throwaway DB; zero user-controlled input (confirmed [SEC]).

**Observations (tagged by source):**
- [VERIFIED] Optional-narrowing asserts are load-bearing, not vacuous — `assert sd is not None` precedes attribute access that pyright flagged as `reportOptionalMemberAccess`; removing them reintroduces errors (AC1). rule-checker rule #6 ruled them compliant/not-vacuous; edge-hunter confirmed they can't flip a passing test (`SoloSlotConflict` early-exit unreachable in isolated fixtures). Evidence: `test_opening_pov_swap_71_5.py:85`, `:134`, `:235`.
- [TEST] test-analyzer flagged the same 4 asserts as "vacuous" (high) — **dismissed**: correct as a runtime-guard observation but misses their type-narrowing purpose; their always-true runtime nature is exactly what satisfies AC5 (no behavior change).
- [TYPE] type-design flagged the 7 `handle_message` `reportArgumentType` ignores as a real mismatch (high) — **confirmed the observation, rejected the proposed fix**: verified at `websocket_session_handler.py:372` that `msg.type` is read directly on the bare member, so the suggested `GameMessage(root=...)` wrap would `AttributeError` at runtime. Correct handling is Dev's targeted ignore + the production-retype delivery finding (barred from this story by AC4).
- [TYPE] visibility_sidecar `reportCallIssue` ignores (×7) — **dismissed** citing AC-2, which explicitly sanctions "resolved via targeted `# pyright: ignore[reportCallIssue]`". Genuine FP: real field with `alias="_visibility"` + `populate_by_name=True` (verified `protocol/base.py:54`, `messages.py:79`).
- [SIMPLE] wrapper-to-collapse-ignores (high) + isinstance-over-cast (med) — **dismissed**: non-blocking style; the `cast` is `hasattr`-guarded and type-design independently confirmed it SOUND; the wrapper's real benefit is subsumed by the production-retype finding.
- [DOC] comment-analyzer clean — every ignore comment accurately labels a genuine suppression; `_canned_opening` docstring describes content, not type, so the `list[object]→list[NarrationMessage]` tightening leaves it accurate.
- [EDGE]/[SILENT]/[SEC]/[RULE] all clean — no boundary regressions, no swallowed errors, no injection, zero rule violations.

### Rule Compliance
- **`# type: ignore`/`# pyright: ignore` must carry specific codes** (python.md #3): all 16 new ignores carry bracketed codes (`reportCallIssue`, `reportArgumentType`) — compliant ([RULE] enumerated 16/16).
- **No blanket file-level ignores** (AC-2): neither file has a module-level ignore — compliant.
- **Test quality / no vacuous asserts** (python.md #6): the 6 added asserts are Optional-narrowing on real `X | None` bindings, not tautological literals — compliant.
- **No Source-Text Wiring Tests** (CLAUDE.md): asserts test runtime values (`sd`, `handler._room`), not source strings — compliant.
- **No Silent Fallbacks** (SOUL/CLAUDE): asserts raise loudly on `None` rather than silently dereferencing — compliant (moves in the correct direction).
- **No production source modified** (AC-4): diff is 2 test files only — compliant.

### Devil's Advocate
Suppose this change is broken. The most dangerous edit is the cluster of new `assert` statements: an assertion that can never fail is dead weight, but an assertion in the *wrong place* could convert a green suite to red or — worse — mask a real bug by short-circuiting before the meaningful assertion runs. Could `assert sd is not None` fire spuriously? Only if `_session_data` is `None` after `_connect`, which happens on the `SoloSlotConflict` early-return path — but edge-hunter traced that path as unreachable in the per-test `RoomRegistry` fixture, and all four asserts sit downstream of a `_connect` that populates the field on every normal path. Could the asserts hide a subtler failure? No — they precede the *same* attribute access that previously ran unguarded, so any prior `AttributeError` is now a clearer `AssertionError`, never a swallowed one. Next worst: the `cast(TracerProvider, current)` — a `cast` is a runtime no-op, so if the OTEL provider were secretly the API ABC (no `add_span_processor`), the `hasattr` guard would have routed to the `else` branch first; the cast is only reached when the method provably exists. Could a malicious or confused author misuse the new `# pyright: ignore` comments to hide future real errors on those lines? Possibly — a per-line `reportArgumentType` ignore would also silence a genuinely wrong argument added later. That is the strongest argument against the per-call suppression approach and for the production retype (logged). But within this story's AC4 constraint it is the correct, narrowest available tool. Finally, the f-string TRUNCATE: a confused future reader might copy the pattern into production with untrusted input. The suppression comment plus the trusted `pg_tables` source mitigate this in context, but the delivery findings and this audit document the hazard so it does not propagate silently. Nothing uncovered rises to blocking.

**Error handling:** asserts fail loud (No Silent Fallbacks); no error path swallowed ([SILENT] clean).
**Pattern observed:** targeted per-line pyright suppression with specific codes + Optional-narrowing asserts at `test_opening_pov_swap_71_5.py:85` and `test_opening_emit_event_71_13.py:159`.
**Handoff:** To SM (Morpheus) for finish-story.