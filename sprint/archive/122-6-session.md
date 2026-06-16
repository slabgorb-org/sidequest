---
story_id: "122-6"
jira_key: ""
epic: "122"
workflow: "trivial"
---

# Story 122-6: Rename asset_url OTEL span server.asset_url.resolved → foundation.asset_url.resolved to match emitting tier

## Story Details
- **ID:** 122-6
- **Jira Key:** (none — no Jira configured for this project)
- **Workflow:** trivial
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-16T13:01:57Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-16T12:34:52.055912+00:00 | 2026-06-16T12:36:35Z | 1m 42s |
| implement | 2026-06-16T12:36:35Z | 2026-06-16T12:50:18Z | 13m 43s |
| review | 2026-06-16T12:50:18Z | 2026-06-16T12:56:58Z | 6m 40s |
| implement | 2026-06-16T12:56:58Z | 2026-06-16T12:59:00Z | 2m 2s |
| review | 2026-06-16T12:59:00Z | 2026-06-16T13:01:57Z | 2m 57s |
| finish | 2026-06-16T13:01:57Z | - | - |

## Sm Assessment

Trivial 1pt rename, scoped to `server` repo. Honesty follow-up to ADR-147: the span name claims `server` tier but the emitter lives in `foundation`. Risk is low and contained — one constant in `sidequest/telemetry/spans/asset_url.py` plus two test assertions in `tests/server/test_asset_urls.py`. Confirm the `FLAT_ONLY_SPANS` registry entry tracks the rename so the new name stays flat-only. No design ambiguity, no cross-repo coupling, no Jira (not configured). Route straight to dev for the implement phase; `just server-check` is the gate.

## Story Summary

ADR-147 honesty follow-up. The OTEL span for asset-URL resolution is currently named `server.asset_url.resolved`, but the function that emits it lives in the `foundation` tier (`sidequest/foundation/asset_urls.py`), not the `server` tier. Rename the span constant to `"foundation.asset_url.resolved"` to accurately reflect its source tier, and update the two test assertions in `tests/server/test_asset_urls.py` that check for this span by name.

### Files to Change
1. `sidequest-server/sidequest/telemetry/spans/asset_url.py` — Rename `SPAN_ASSET_URL_RESOLVED = "server.asset_url.resolved"` to `"foundation.asset_url.resolved"`
2. `sidequest-server/tests/server/test_asset_urls.py` — Update two test assertions (lines 126 and 145) that call `span_attrs_by_name(otel_capture, "server.asset_url.resolved")` to use the new name

### Acceptance Criteria
1. Span constant renamed; FLAT_ONLY_SPANS entry updated with new name
2. Both test assertions updated to query the new span name
3. All existing tests pass
4. `just server-check` passes (ruff + pytest + pyright)

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/telemetry/spans/asset_url.py` — `SPAN_ASSET_URL_RESOLVED` value renamed `server.asset_url.resolved` → `foundation.asset_url.resolved`. `FLAT_ONLY_SPANS.add(SPAN_ASSET_URL_RESOLVED)` references the constant, so flat-only registration tracks the rename automatically (no separate edit needed).
- `tests/server/test_asset_urls.py` — both `span_attrs_by_name(otel_capture, ...)` assertions (lines 126, 145) updated to the new span name.

**Tests:** 18/18 passing in `tests/server/test_asset_urls.py` (GREEN). ruff + pyright clean on the 2 scoped files. Grep confirmed zero remaining `server.asset_url.resolved` references in Python source.
**Branch:** feat/122-6-rename-asset-url-otel-span (pushed) — commit 25822b16

**Scope note:** AC-4 ("`just server-check` passes") is met for this story's 2 files but NOT repo-wide — `develop` has 8 pre-existing ruff `I001` errors in unrelated test files. Deferred to chore 122-9 per Bossmang (see Design Deviations + Delivery Findings).

**Handoff:** To review phase (Chrisjen Avasarala).

## Dev Rework (R1)

**Trigger:** Reviewer REJECTED on one `[LOW][DOC]` finding — module docstring contradicted the span's foundation re-tiering.
**Change:** `sidequest/telemetry/spans/asset_url.py:1` docstring reworded `"...fires every time the server emits a media URL."` → `"...fires every time a media URL is resolved (foundation tier)."` Docstring-only; no logic, no test, no signature change.
**Verification:** 18/18 `tests/server/test_asset_urls.py` green; ruff + pyright clean on the 2 scoped files (95-char docstring line under the 100 limit). No repo-wide auto-fix run — pre-existing I001 debt untouched (still 122-9).
**Branch:** feat/122-6-rename-asset-url-otel-span — commit 72c66843 (pushed).
**Reviewer finding status:** Confirmed `[DOC]` finding RESOLVED. The 2 deferred test-analyzer findings remain out of scope (pre-existing). AC-4 ruff-debt deferral unchanged (122-9).
**Handoff:** Back to review (Chrisjen Avasarala).

## Delivery Findings

### Dev (implementation)
- **Gap** (non-blocking): `develop` carries pre-existing ruff `I001` (import-order) violations in 8 server test files, so repo-wide `just server-check` is red independent of this story. ruff 0.15.11 under the uv-locked config flags them; the testing-runner masked this by auto-running `ruff --fix`. Affects `tests/agents/test_unseeded_objective_classifier.py`, `tests/foundation/test_foundation_floor_122_1.py`, `tests/game/ruleset/test_121_7_fate_interactive_chargen.py`, `tests/game/test_builder_arrange_visible.py`, `tests/game/test_fate_gear_model.py`, `tests/server/dispatch/test_room_creature_binding_107_2.py`, `tests/server/test_fate_state_emit.py`, `tests/server/test_fate_state_emit_wiring.py` (import blocks need `ruff --fix`). Spun into chore **122-9** per Bossmang's call; kept out of this PR. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): Module docstring in `sidequest/telemetry/spans/asset_url.py:1` still reads "fires every time the **server** emits a media URL" while this story re-tiers the span to `foundation.*` — same tier-lie the rename exists to kill. Affects `sidequest/telemetry/spans/asset_url.py` (docstring should drop "server" and reflect foundation-tier resolution). Routed back to Dev to fix in-branch this cycle (see Reviewer Assessment). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Pre-existing span-helper/local-mode test coverage gaps surfaced by test-analyzer (`tests/telemetry/spans/test_asset_url_span.py` scope-attr assertion; `tests/server/test_asset_urls.py` local/staging-mode span-firing). NOT introduced by this rename and out of scope for it; candidates for a future test-hardening chore. *Found by Reviewer during code review.*
- **(R2)** No new upstream findings on re-review. R1 `[DOC]` finding resolved; story clean to merge. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

1 deviation

- **AC-4 (`just server-check` passes) not fully met — pre-existing repo lint debt deferred**
  - Rationale: The debt predates 122-6 (present on origin/develop), is unrelated to the span rename, and sweeping 8 unrelated files into a one-line rename PR is poor commit hygiene. Bossmang chose "spin a separate chore" — tracked as 122-9.
  - Severity: minor
  - Forward impact: Reviewer's repo-wide `just server-check` will remain red until 122-9 lands; 122-6's own scope is clean.

## Design Deviations

### Dev (implementation)
- **AC-4 (`just server-check` passes) not fully met — pre-existing repo lint debt deferred**
  - Spec source: context-story-122-6 / session AC-4
  - Spec text: "`just server-check` passes (ruff + pytest + pyright)"
  - Implementation: The 2 files in this story's scope pass ruff/pyright/pytest cleanly, but repo-wide `ruff check .` reports 8 pre-existing `I001` errors in unrelated test files, so the aggregate `just server-check` is red. Not swept into this PR.
  - Rationale: The debt predates 122-6 (present on origin/develop), is unrelated to the span rename, and sweeping 8 unrelated files into a one-line rename PR is poor commit hygiene. Bossmang chose "spin a separate chore" — tracked as 122-9.
  - Severity: minor
  - Forward impact: Reviewer's repo-wide `just server-check` will remain red until 122-9 lands; 122-6's own scope is clean.

### Reviewer (audit)
- **AC-4 deferral (pre-existing ruff I001 debt → chore 122-9)** → ✓ ACCEPTED by Reviewer: The 8 I001 errors are demonstrably pre-existing on origin/develop and absent from this story's 2-file diff (confirmed independently by reviewer-preflight: zero I001 hits in the scoped files). Sweeping 8 unrelated test files into a one-line span rename would be poor commit hygiene; deferring to a dedicated chore is the correct call. Severity of the deferral itself: minor. Note: this does NOT mean develop's red lint gate is acceptable long-term — 122-9 must land promptly.
- No undocumented spec deviations found: the diff matches the session AC exactly (constant rename + two test assertions). FLAT_ONLY_SPANS registration tracks the constant by reference, satisfying AC-1 without a separate edit.
- **(R2)** Rework introduced no new deviations — docstring-only change, fully in-scope (it completes the same tier-honesty fix). AC-4 ruff-debt deferral re-affirmed ACCEPTED (still tracked as 122-9).

## Subagent Results (R1 — superseded)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (18/18 green; scoped files ruff+pyright clean) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 2 (medium) | confirmed 0, dismissed 0, deferred 2 (pre-existing, out of scope) |
| 5 | reviewer-comment-analyzer | Yes | findings | 1 (high) | confirmed 1 (docstring stale → reject), dismissed 0, deferred 0 |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | none (13 rules, 0 violations; rename complete) | N/A |

**All received:** Yes (4 enabled returned; 5 skipped via workflow.reviewer_subagents toggles)
**Total findings:** 1 confirmed (blocking-by-discretion, doc), 0 dismissed, 2 deferred (pre-existing, out of scope)

### Rule Compliance

Applicable rules enumerated against every element in the diff (3 string-literal changes across 2 files):

- **OTEL Observability Principle (CLAUDE.md):** Span names must honestly reflect the emitting tier. The emitter `asset_url_resolved_span()` is called from `sidequest/foundation/asset_urls.py` (foundation tier). Renaming `server.asset_url.resolved` → `foundation.asset_url.resolved` brings the name into compliance. ✓ COMPLIANT (this is the story's purpose). Cosmetic-name exemption from the "new span per subsystem decision" rule applies — no new span required. ✓
- **No Source-Text Wiring Tests (CLAUDE.md):** The two updated assertions use `span_attrs_by_name(otel_capture, "foundation.asset_url.resolved")` — driving the real `resolve_asset_url()` flow and asserting the span fired. This is the sanctioned OTEL-span-assertion pattern, not a source-text grep. ✓ COMPLIANT (both assertions).
- **No Silent Fallbacks / No Stubbing:** No fallback or stub introduced; constant referenced directly. ✓ COMPLIANT.
- **Rename completeness:** `grep "server.asset_url.resolved"` across sidequest-server → 0 hits; `"foundation.asset_url.resolved"` → exactly 3 (constant + 2 assertions). Symbolic consumer `test_asset_url_span.py` (asserts on `SPAN_ASSET_URL_RESOLVED`) and caller `foundation/asset_urls.py` (calls the context manager) inherit the new value automatically — correct, no edit needed. ✓ COMPLIANT.
- **Docstring honesty (derived from OTEL/honesty principle):** Module docstring asserts "the server emits" while the span is now foundation-tier. ✗ VIOLATION — see finding below. The one rule the diff's own intent demands, left unfinished in the same file.
- Python lang-review checklist (reviewer-rule-checker, 13 numbered rules — exception-swallowing, mutable defaults, type-annotation gaps, logging, path handling, test quality, resource leaks, unsafe deserialization, async pitfalls, import hygiene, input validation, dependency hygiene, fix-introduced regressions): 0 violations across 6 in-scope instances. ✓ COMPLIANT.

### Devil's Advocate

Let me argue this change is broken. First attack: a span rename is never "just a rename" — span names are load-bearing identifiers that downstream consumers key on. If anything in the GM panel, a forensic reader, an OTEL query, a saved dashboard, or a `FLAT_ONLY_SPANS` allowlist matched the literal string `server.asset_url.resolved`, this rename silently breaks it with zero test failure. I checked: `FLAT_ONLY_SPANS.add(SPAN_ASSET_URL_RESOLVED)` uses the constant (line 18), so the allowlist follows the rename — good. reviewer-rule-checker grepped the whole repo and found zero remaining literal references to the old name outside the diff. The risk that bites here is *cross-repo*: a dashboard or saved query in sidequest-ui's Dashboard or an external OTEL config could hardcode `server.asset_url.resolved`. That is genuinely out of this repo's diff scope and untestable from here, but it is a real operational consideration — the GM panel reads this span "via the agent_span_close fan-out" (per the file comment), which keys on the emitted name. If a human bookmarked a filter on the old name, it goes quietly empty. This is inherent to ANY span rename and is the accepted cost of honesty re-tiering; ADR-147 chose honesty over name-stability deliberately. Second attack: the docstring. A confused future reader sees a module whose docstring says "the server emits a media URL" but whose span is named `foundation.*` and whose emitter lives in `foundation/asset_urls.py`. Which is the truth? The docstring actively misleads about the architectural tier — the exact failure mode this story was written to eliminate, reproduced one line up. That is not hypothetical; comment-analyzer flagged it high-confidence and I confirmed it by reading the file. Third attack: test fragility. Both tests only exercise CDN mode; the span fires in all modes. If a later refactor moves the span context manager inside a CDN-only branch, the local-mode tests pass and the regression is invisible. Real, but pre-existing and not introduced by this diff — deferred. The devil's strongest point lands on the docstring: shipping a tier-honesty fix beside a tier-dishonest docstring is incoherent, and it's a free fix in an already-open branch. That elevates it from "note for later" to "fix it now."

## Reviewer Assessment (R1 — superseded, see R2 below)

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [LOW] | `[DOC]` Module docstring asserts "the **server** emits a media URL" — contradicts the span's deliberate re-tiering to `foundation.*`, reproducing the exact tier-lie this story exists to remove, in the same file. | `sidequest/telemetry/spans/asset_url.py:1` | Reword the docstring to drop "server" and reflect foundation-tier resolution, e.g. `"""Asset-URL resolution span — fires every time a media URL is resolved (foundation tier)."""` |

**Reviewer discretion note:** The single confirmed finding is `[LOW]` (documentation), which the severity rubric classes non-blocking. I am nonetheless routing back to Dev rather than approving-with-followup because (a) the fix is one line in a file this story already modifies, (b) it directly undercuts the story's stated honesty purpose (ADR-147), and (c) an in-branch fix is strictly cleaner than a dangling follow-up. "Approve but please fix" is the rubber-stamp this role forbids — so: REJECT, fix in-branch, re-review.

**Dispatch-tag coverage:**
- `[EDGE]` — skipped (edge_hunter disabled). Manual scan: no branches/boundaries in a string-constant rename. No concern.
- `[SILENT]` — skipped (silent_failure_hunter disabled). Manual scan: no error handling or fallback in diff. No concern.
- `[TEST]` — test-analyzer: 2 medium findings, both pre-existing coverage gaps in untouched paths → deferred (out of scope). Updated assertions confirmed non-vacuous.
- `[DOC]` — comment-analyzer: 1 high → **CONFIRMED, blocking-by-discretion** (the rejection reason above).
- `[TYPE]` — skipped (type_design disabled). Manual scan: no type/signature changes; constant stays `str`. No concern.
- `[SEC]` — skipped (security disabled). Manual scan: internal telemetry helper, no user-input boundary, no secrets. No concern.
- `[SIMPLE]` — skipped (simplifier disabled). Manual scan: minimal 3-line diff, nothing to simplify. No concern.
- `[RULE]` — rule-checker: 13 rules, 0 violations; rename complete and consistent. Clean.

**Data flow traced:** `resolve_asset_url(relative_path)` (foundation tier) → opens `asset_url_resolved_span(...)` using `SPAN_ASSET_URL_RESOLVED` → span emitted under new name `foundation.asset_url.resolved` → `FLAT_ONLY_SPANS` (by constant reference) → GM-panel fan-out. Rename is internally consistent end-to-end; the only stale node is the human-facing docstring.

**Pattern observed:** Correct symbolic-constant indirection at `asset_url.py:14,18` and `test_asset_url_span.py:34` — consumers reference `SPAN_ASSET_URL_RESOLVED`, not the literal, so they track renames for free. Good pattern.

**Handoff:** Back to Dev (Naomi Nagata) for the one-line docstring fix.

---

## Subagent Results

> Round 2 (re-review of rework commit 72c66843). The rework changed exactly one line — the module docstring. Constant rename + two test assertions are byte-identical to R1, so reviewer-test-analyzer and reviewer-rule-checker domains were untouched; their R1 verdicts carry forward (annotated below). Preflight and comment-analyzer — the domains the rework touched — were re-run fresh.

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (R2: 18/18 green; scoped files ruff+pyright clean; docstring 91 chars < 100) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes (R1 carried) | findings | 2 (medium) | deferred 2 — domain unchanged by rework; pre-existing, out of scope |
| 5 | reviewer-comment-analyzer | Yes | clean | none (R2: R1 docstring finding RESOLVED; new docstring accurate; no new inaccuracies) | confirmed-resolved |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes (R1 carried) | clean | none | N/A — domain unchanged by rework; 13 rules, 0 violations |

**All received:** Yes (R2: preflight + comment-analyzer re-run clean; test-analyzer + rule-checker carried from R1 unchanged-domain; 5 disabled via toggles)
**Total findings:** 0 confirmed-open, 0 dismissed, 2 deferred (pre-existing, out of scope). The sole R1 blocking finding (`[DOC]` docstring) is RESOLVED.

## Reviewer Assessment

**Verdict:** APPROVED

The R1 rejection's single confirmed finding — the tier-dishonest module docstring at `asset_url.py:1` — is fixed in commit 72c66843 (reworded to "fires every time a media URL is resolved (foundation tier)"). reviewer-comment-analyzer re-ran and reports clean, confirming the new wording is accurate (the emitter `resolve_asset_url` lives in `sidequest/foundation/asset_urls.py`) and introduces no new inaccuracies. Mechanical re-check is green: 18/18, scoped files ruff+pyright clean, docstring within the 100-char limit, pre-existing I001 debt untouched.

**Dispatch-tag coverage:**
- `[EDGE]` — skipped (disabled). Manual: no branches/boundaries in a string+docstring change. No concern.
- `[SILENT]` — skipped (disabled). Manual: no error handling/fallback in diff. No concern.
- `[TEST]` — test-analyzer (R1 carried): 2 medium pre-existing coverage gaps in untouched paths → deferred (out of scope). Updated assertions non-vacuous.
- `[DOC]` — comment-analyzer (R2 re-run): **CLEAN** — R1 docstring finding RESOLVED.
- `[TYPE]` — skipped (disabled). Manual: constant stays `str`; no signature/type change. No concern.
- `[SEC]` — skipped (disabled). Manual: internal telemetry helper, no user-input boundary, no secrets. No concern.
- `[SIMPLE]` — skipped (disabled). Manual: 4-line diff, nothing to simplify. No concern.
- `[RULE]` — rule-checker (R1 carried): 13 rules, 0 violations; rename complete and consistent.

**Data flow traced:** `resolve_asset_url(relative_path)` (foundation tier) → `asset_url_resolved_span(...)` opens span under `SPAN_ASSET_URL_RESOLVED` = `foundation.asset_url.resolved` → `FLAT_ONLY_SPANS` (by constant reference) → GM-panel agent_span_close fan-out. Internally consistent end-to-end; docstring now matches.

**Pattern observed:** Symbolic-constant indirection at `asset_url.py:14,18` and `test_asset_url_span.py:34` — consumers reference `SPAN_ASSET_URL_RESOLVED`, not the literal, so renames propagate for free. Good pattern, correctly relied upon.

**Error handling:** N/A — pure string-constant + docstring change; no control flow, no failure paths introduced (verified: diff is 4 lines, all literals).

**Deviation audit:** AC-4 ruff-debt deferral re-affirmed ACCEPTED (pre-existing, tracked as 122-9). No new deviations introduced by the rework. See `### Reviewer (audit)`.

**Handoff:** To SM (Camina Drummer) for finish-story.