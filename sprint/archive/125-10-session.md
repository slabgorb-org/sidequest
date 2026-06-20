---
story_id: "125-10"
jira_key: ""
epic: "125"
workflow: "trivial"
---
# Story 125-10: [126-34 follow-up] Keep the test-session predicate in sync across repos

## Story Details
- **ID:** 125-10
- **Jira Key:** (none)
- **Workflow:** trivial
- **Stack Parent:** none
- **Repos:** server, ui

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-20T12:48:31Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-20T12:22:56Z | 2026-06-20T12:26:48Z | 3m 52s |
| implement | 2026-06-20T12:26:48Z | 2026-06-20T12:42:01Z | 15m 13s |
| review | 2026-06-20T12:42:01Z | 2026-06-20T12:48:31Z | 6m 30s |
| finish | 2026-06-20T12:48:31Z | - | - |

## Sm Assessment

**Story:** 126-34 follow-up. The test-session predicate — which session-id prefixes mark a run as a test/tool-test session and exclude it from the live GM dashboard — is encoded **twice, independently**: `is_test_session` in server `sidequest-server/sidequest/telemetry/watcher_hub.py:436` (used at :745) and `isTestSession` in ui `sidequest-ui/src/components/Dashboard/source/useLiveSource.ts:477` (used at :338, :364). The two prefix lists can silently drift, re-opening the 126-34 leak (test runs reappearing on the live dashboard).

**Scope (trivial chore, 2pts, server + ui):** Make the two predicates un-driftable. Two viable shapes, Dev's call:
- A **cross-repo contract test** asserting both implementations classify the same fixture set of session-ids identically (the prefix set lives in one canonical fixture both sides import/mirror), or
- A **shared source of truth** for the prefixes (e.g. a small constant the server emits / the protocol carries, with the ui consuming it) so there is only one list.

Prefer the lightest option that makes drift a test failure, not a silent regression. **Do not** broaden the predicate's behavior — this is a sync/guard, not a redefinition of what counts as a test session.

**Cross-repo note:** server + ui both have `feat/125-10-test-session-predicate-sync` off develop. A contract test that must run in both CIs needs the canonical prefix fixture committed in a place both repos can reach (or duplicated with the contract test asserting equality) — Dev should resolve where the single source lives.

**Routing:** trivial/phased → next agent is **Dev** (implement phase). No Jira (empty key) — claim step skipped intentionally. Ungated merge cleared: ui #439 + dice-lib #30 (Fate dice legibility) merged before setup. Acceptance criteria refined in the story context.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Gap** (non-blocking): `sidequest-ui` `npm run build` (`tsc -b`) is currently RED on
  `src/components/GameBoard/__tests__/GameBoard-fate-inventory-tab.test.tsx:203` — `"fate"`
  is not assignable to `WidgetId`. Reproduced with all 125-10 changes stashed out, so it is
  PRE-EXISTING on develop and unrelated to the test-session predicate — most likely fallout
  from the just-merged Fate widget/payloads work. Not caught by `just check-all` (which runs
  `client-lint` + `client-test`, not the build). Affects
  `sidequest-ui/src/components/GameBoard/__tests__/GameBoard-fate-inventory-tab.test.tsx`
  (align the test's widget id with the current `WidgetId` union, or restore the `"fate"`
  widget). *Found by Dev during implementation.*
- **Improvement** (non-blocking): the residual cross-CI byte-identity gap (see Dev deviation
  below) could be closed cheaply by an orchestrator-level check that `diff`s the two vendored
  `test_session_prefix_contract.json` copies — both subrepos are working copies under
  `orc-quest`. Affects the orchestrator repo (a new `just` recipe or test under `scripts/`);
  out of scope for this server+ui story. *Found by Dev during implementation.*

### Reviewer (code review)
- No new upstream findings during code review. Both Dev findings are confirmed accurate and
  remain non-blocking: the pre-existing `GameBoard-fate-inventory-tab.test.tsx` `tsc -b` error
  (independently reproduced with 125-10 stashed) is not attributable to this story, and the
  orchestrator-level fixture-`diff` opportunity is a sound future improvement, not a blocker.
  *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

1 deviation

- **Cross-repo consistency is enforced per-repo against a vendored canonical fixture, not across both CIs**
  - Rationale: true cross-CI enforcement needs a single shared artifact both repos fetch at build time (a published npm + pypi constants package), which is disproportionate for two prefix strings on a 2-pt chore. The chosen design still raises the bar from two silent inline literals to a documented canonical fixture (whose header names both repos' copies + predicates) plus a per-repo tripwire that forces every prefix change through that fixture.
  - Severity: minor
  - Forward impact: minor — the gap is loudly documented in the fixture header and captured as a non-blocking Delivery Finding (an orchestrator-level fixture-`diff` check is the cheap close).

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Cross-repo consistency is enforced per-repo against a vendored canonical fixture, not across both CIs**
  - Spec source: context-story-125-10.md, AC2
  - Spec text: "A test fails if the server and ui predicates classify the same session-id differently (i.e. adding/removing a prefix on one side without the other breaks CI)."
  - Implementation: each repo's contract test pins its predicate's DECLARED prefix set (`_TEST_SESSION_SLUG_PREFIXES` / `TEST_SESSION_SLUG_PREFIXES`) to a byte-identical vendored fixture `test_session_prefix_contract.json`. Changing a predicate without updating that repo's fixture copy fails that repo's CI. But a change that updates a predicate AND its repo's fixture copy — without touching the other repo — passes both CIs; two independent CI pipelines cannot enforce mutual byte-identity of the two vendored copies.
  - Rationale: true cross-CI enforcement needs a single shared artifact both repos fetch at build time (a published npm + pypi constants package), which is disproportionate for two prefix strings on a 2-pt chore. The chosen design still raises the bar from two silent inline literals to a documented canonical fixture (whose header names both repos' copies + predicates) plus a per-repo tripwire that forces every prefix change through that fixture.
  - Severity: minor
  - Forward impact: minor — the gap is loudly documented in the fixture header and captured as a non-blocking Delivery Finding (an orchestrator-level fixture-`diff` check is the cheap close).

### Reviewer (audit)
- **Dev deviation — "Cross-repo consistency enforced per-repo against a vendored fixture, not across both CIs"** → ✓ ACCEPTED by Reviewer: the reasoning is correct. Two independent CI pipelines cannot enforce mutual byte-identity of vendored copies without a shared published artifact, which is disproportionate for two prefix strings on a 2-pt chore. The chosen design still converts the realistic drift vector — a *predicate* change — into a per-repo CI failure, and routes every change through a single, loudly-commented canonical fixture. The residual gap (editing a predicate + its own repo's fixture copy while leaving the other repo stale) is documented in the fixture header and filed as a non-blocking finding (orchestrator `diff` check). Proportionate and honest. No undocumented deviations found in the diff.

## Dev Assessment

**Implementation Complete:** Yes

**Approach:** Cross-repo contract test (the lighter of the two options in the Sm Assessment). A canonical golden-case fixture `test_session_prefix_contract.json` is vendored byte-identical in both repos (matching sha256). Each repo's contract test pins its predicate's DECLARED prefix set to the fixture and runs the shared golden cases, so a one-sided predicate change fails that repo's CI. The ui `isTestSession` was refactored from inline string literals to a declared, exported `TEST_SESSION_SLUG_PREFIXES` array — now parallel to the server's `_TEST_SESSION_SLUG_PREFIXES` tuple.

**Files Changed:**
- `sidequest-server/tests/fixtures/test_session_prefix_contract.json` (new) — canonical fixture
- `sidequest-server/tests/server/test_test_session_prefix_contract.py` (new) — server contract test (3 tests)
- `sidequest-ui/src/components/Dashboard/__tests__/fixtures/test_session_prefix_contract.json` (new) — byte-identical vendored copy
- `sidequest-ui/src/components/Dashboard/__tests__/test-session-prefix-contract.test.ts` (new) — ui contract test (2 tests)
- `sidequest-ui/src/components/Dashboard/source/useLiveSource.ts` — `isTestSession` reads from a declared, exported `TEST_SESSION_SLUG_PREFIXES`; both exported
- `sidequest-ui/tsconfig.app.json` — `resolveJsonModule: true` (enables the contract test's JSON fixture import)

**Drift-lock proven:** injecting a `probe-` prefix into each predicate without updating the fixture turned the contract test RED in both repos (demonstrated, then reverted).

**Tests:** all passing (GREEN)
- server: 10/10 (`test_test_session_isolation.py` 7 + `test_test_session_prefix_contract.py` 3); ruff clean
- ui: 144/144 Dashboard tests (incl. 2 new contract tests); eslint clean on changed files

**AC status:** AC1 ✓ · AC2 ✓ per-repo (documented cross-CI limitation — see Dev deviation) · AC3 ✓ (no predicate behavior change; existing 126-34 filter tests green) · AC4 ✓

**Wiring:** the contract tests call the REAL production predicates (no mocks); both predicates have live production consumers (server `watcher_hub.py:745` publish path; ui `useLiveSource.ts:338/364` filters), proven wired by the pre-existing 126-34 tests.

**Note (non-blocking):** `sidequest-ui` `npm run build` (`tsc -b`) is RED on a PRE-EXISTING, unrelated error (`GameBoard-fate-inventory-tab.test.tsx` — `"fate"` not a `WidgetId`); reproduced with 125-10 stashed out, and not part of the `just check-all` gate. Captured in Delivery Findings.

**Branch:** `feat/125-10-test-session-predicate-sync` (server + ui), pushed.

**Handoff:** To review (The Merovingian).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (0 smells) | N/A — server 10/10 + ui 6/6 green, ruff+eslint clean |
| 2 | reviewer-edge-hunter | Yes | Skipped | disabled | Disabled via settings — boundary coverage assessed by Reviewer |
| 3 | reviewer-silent-failure-hunter | Yes | Skipped | disabled | Disabled via settings — silent-failure assessed by Reviewer |
| 4 | reviewer-test-analyzer | Yes | Skipped | disabled | Disabled via settings — test quality assessed by Reviewer |
| 5 | reviewer-comment-analyzer | Yes | Skipped | disabled | Disabled via settings — docs assessed by Reviewer |
| 6 | reviewer-type-design | Yes | Skipped | disabled | Disabled via settings — type design assessed by Reviewer |
| 7 | reviewer-security | Yes | clean | none | N/A — display filter, not a security boundary; no untrusted input |
| 8 | reviewer-simplifier | Yes | Skipped | disabled | Disabled via settings — complexity assessed by Reviewer |
| 9 | reviewer-rule-checker | Yes | Skipped | disabled | Disabled via settings — rule compliance assessed by Reviewer |

**All received:** Yes (2 enabled returned clean; 7 disabled via `workflow.reviewer_subagents`, assessed by Reviewer)
**Total findings:** 0 confirmed, 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

A tight, behavior-preserving change that does exactly what 125-10 asks: it converts two independently-maintained inline prefix lists into a single canonical declaration per repo, pinned to a vendored fixture so a predicate edit can't silently diverge. I traced every cause to its effect and found no exploitable gap.

**Data flow traced:** a session slug (e.g. `"test-pulp_noir-…"`) → `is_test_session` (server `watcher_hub.py:441`, `not slug` guard then `startswith(("test-","tool-test"))`) / `isTestSession` (ui `useLiveSource.ts`, `TEST_SESSION_SLUG_PREFIXES.some(p => slug.startsWith(p))`) → excluded from the GM dashboard picker/State-tab/auto-follow. Refactor is value-identical to the prior `||` chain, so the filtered set is unchanged (safe — confirmed by the 6 green ui filter+contract tests and 10 green server tests).

**Pattern observed:** single-source constant + contract test pinning the production declaration to a canonical fixture — the *correct* anti-drift pattern, and it satisfies CLAUDE.md "No Source-Text Wiring Tests" because the assertions import and compare real values (`wh._TEST_SESSION_SLUG_PREFIXES`, `[...TEST_SESSION_SLUG_PREFIXES]`), not `read_text()` greps. `test_test_session_prefix_contract.py:43` / `test-session-prefix-contract.test.ts:19`.

**Error handling:** fixture loads fail LOUD — server `Path.read_text(encoding="utf-8")` raises `FileNotFoundError`; ui static `import` hard-errors if absent. No swallowed exceptions, no silent fallback (complies with No Silent Fallbacks). `None`/session-less infra is explicitly classified non-test server-side (`is_test_session(None) is False`), the one case the `string`-typed ui predicate can't express — appropriate asymmetry, not a gap.

### Observations (subagent dimensions; 7 specialists disabled → Reviewer-assessed)

- `[PRE]` preflight clean — server 10/10, ui 6/6 green; ruff + eslint clean; 0 code smells; the lone `tsc -b` error (`GameBoard-fate-inventory-tab.test.tsx`) implicates 0 of 125-10's files (pre-existing).
- `[SEC]` security clean — the predicate is a Keith/dev display filter, not an auth/tenant boundary; `resolveJsonModule` is a bundler-scoped flag that widens no runtime surface; the only new JSON consumer is a static test fixture at a literal path (no traversal, no untrusted input).
- `[EDGE]` (disabled; Reviewer-assessed) — `[VERIFIED]` boundary corpus is strong: both prefixes, exact-prefix equality (`"test-"`, `"tool-test"`), infix non-match (`"greatest-…"`), hyphen-sensitivity (`"tooltest-missing-hyphen"`), and empty string `""` all classified; `None` server-only. The infix/hyphen cases also catch a future `startswith`→`includes` widening, not just prefix additions.
- `[SILENT]` (disabled; Reviewer-assessed) — `[VERIFIED]` no swallowed errors or fallbacks; both fixture loads are fail-loud (see Error handling).
- `[TEST]` (disabled; Reviewer-assessed) — `[VERIFIED]` assertions are specific value/tuple/deep-equality checks (not `assert truthy`); drift was demonstrated RED in both repos; no `@pytest.mark.skip`, no mocks (so no mock-target error), no `as any` in the ts test.
- `[DOC]` (disabled; Reviewer-assessed) — `[VERIFIED]` comments are accurate and load-bearing: the fixture `_comment` and both predicate doc-comments name the sibling repo's file + predicate and the "edit both" requirement; no stale/misleading docs.
- `[TYPE]` (disabled; Reviewer-assessed) — `[VERIFIED]` `TEST_SESSION_SLUG_PREFIXES` is a `readonly` tuple via `as const`; predicate typed `(slug: string) => boolean`; server `_contract() -> dict`, tests `-> None`. No `as any`, no `@ts-ignore`, no non-null assertions.
- `[SIMPLE]` (disabled; Reviewer-assessed) — `[VERIFIED]` minimal and non-over-engineered: chose the lighter contract-test option over a shared-package; eliminated the duplicated literal rather than adding abstraction. 81 server / 52 ui additions, almost all test data.
- `[RULE]` (disabled; Reviewer-assessed) — `[VERIFIED]` see Rule Compliance below.

### Rule Compliance

- **CLAUDE.md "No Source-Text Wiring Tests"** — both contract tests use value/import assertions, not `read_text()` source greps → COMPLIANT (the legitimate "interrogate runtime values" pattern).
- **"No Silent Fallbacks"** — fixture loads fail loud; no alternative-path/default on miss → COMPLIANT.
- **"No Stubbing" / "Verify Wiring, Not Just Existence"** — exported `isTestSession`/`TEST_SESSION_SLUG_PREFIXES` have real consumers (predicate used at `useLiveSource.ts:338/364`; `is_test_session` at `watcher_hub.py:745`); the test imports the real symbols → COMPLIANT, no dead shell.
- **python checklist #3/#5/#6/#8** — annotations present; `Path.resolve()` + explicit `encoding="utf-8"`; specific assertions; `json.loads` on TRUSTED local fixture (not user input) → COMPLIANT.
- **typescript checklist #1/#9/#10** — no type-safety escapes; `resolveJsonModule` is additive (strict untouched); the imported JSON is a static fixture, so "runtime-validate JSON.parse" does not apply → COMPLIANT.
- **OTEL Observability Principle** — N/A: no subsystem decision added; this is a test/guard + a behavior-preserving refactor (a cosmetic-class change), which the principle explicitly exempts.

### Devil's Advocate

Trying to break it. **Could the contract pass vacuously?** No — `.toEqual`/tuple-`==` are deep value comparisons; the proven `probe-` RED demonstrates a real failure on divergence. **Could a dev defeat the lock?** Only by editing a predicate *and* its own repo's fixture copy while leaving the sibling repo stale — the documented residual gap (deviation accepted), not a new hole. **`is expected` bool comparison** in the server test relies on `True`/`False` singletons; `is_test_session` always returns a native `bool`, so this is safe and ruff-clean — a `[LOW]` stylistic note at most, not a finding. **Does `resolveJsonModule` bloat the prod bundle or change emit?** No — `noEmit: true`, and the fixture lives under `__tests__/` which Vite excludes from the app bundle; verified the flag is purely additive and the pre-existing GameBoard `tsc` error is independent (reproduced with this story stashed). **Malformed fixture?** `json.loads`/static import both hard-error — loud, not silent. **`startswith`→`includes` regression risk?** The `"greatest-…"` and `"tooltest-missing-hyphen"` cases would flip to `true` and fail the contract — the corpus actively guards the prefix semantics. **Whitespace/locale slugs?** Slugs are server-generated with fixed prefixes; no leading-space or locale path reaches this predicate. Nothing here rises to Medium or above; the one honest limitation is already logged and accepted.

**Handoff:** To SM (Morpheus) for finish-story.