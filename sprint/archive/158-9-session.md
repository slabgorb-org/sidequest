---
story_id: "158-9"
jira_key: ""
epic: ""
workflow: "trivial"
---
# Story 158-9: Genre theme CSS never arrives on connect — repro/confirm (not reproduced in sweep 2; add guard)

## Story Details
- **ID:** 158-9
- **Jira Key:** (none)
- **Workflow:** trivial
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-23T08:50:22Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-23T06:00:47Z | 2026-06-23T06:02:28Z | 1m 41s |
| implement | 2026-06-23T06:02:28Z | 2026-06-23T08:43:46Z | 2h 41m |
| review | 2026-06-23T08:43:46Z | 2026-06-23T08:50:22Z | 6m 36s |
| finish | 2026-06-23T08:50:22Z | - | - |

## Sm Assessment

**Story:** Genre theme `theme_css` `SESSION_EVENT` sometimes never arrives on connect; when it doesn't, `:root[data-genre]` is never set, `.dark` wins, and `--accent` collapses to a near-invisible `oklch(0.269)`. Accessibility hit (Alex). Repro'd 2026-06-21 on a **freshly-rebooted** server; NOT reproduced 2026-06-22 with a warm server. Hypothesis: reboot-gated emit.

**Scope:** trivial / phased, repo `ui`.

**⚠️ Repo-scope flag for Dev:** evidence points the root cause at the **server** ("NO `theme_css` emission anywhere around connect"; FIXER note → check `handlers/connect` or a theme mixin). The UI loud-fail guard (`useGenreTheme.ts`) **already exists**. So:
- Repro FIRST on a cold/just-rebooted server (systematic-debugging).
- If the emit is genuinely missing server-side → surface it (repo expansion or sibling server story) — do NOT paper over a transport gap in the UI (No-Silent-Fallbacks).
- If the UI guard is the deliverable → confirm it fires under the reboot condition + add coverage for the grace-timer fail path.

**Context:** full finding + ACs in `sprint/context/context-story-158-9.md`. Possibly the same shape as the recurring "connect/resume bootstrap must mirror per-turn emitters" class.

**Setup:** session + branch `feat/158-9-genre-theme-css-connect-guard` (sidequest-ui/develop) created; no Jira (sprint-YAML-only). Routing to Dev for the `implement` phase.

## Dev Assessment

**Implementation Complete:** Yes

**Investigation (systematic-debugging):** The reboot-gated "theme_css never
arrives" bug does NOT exist in current code. Server connect
(`handlers/connect.py:1396–2106`) emits `theme_css` unconditionally (2nd message
in the return list), loads the pack fresh from disk every connect, and all 11
live packs ship a genre `client_theme.css`; the URL rewrite is pure. The UI
loud-fail guard (`useGenreTheme.ts`) and its 3 tests already shipped. So per the
Operator's "Server guard + close" decision, the genuine remaining "add guard"
was server-side.

**Files Changed (repo: `sidequest-server`):**
- `sidequest/handlers/connect.py` — loud server-side guard: when no client_theme.css
  resolves on connect, log a WARNING `session.theme_css_absent` and bump the
  `genre_theme` watcher event to `severity="warning"` (was a silent info-level
  "absent"). No-Silent-Fallbacks + OTEL observability.
- `tests/server/test_session_handler_slug_connect.py` — new behavior test
  `test_slug_connect_warns_loudly_when_theme_css_absent`: nulls the loaded pack's
  client_theme_css, asserts NO theme_css event + a loud WARNING fires.

**Tests:** `test_session_handler_slug_connect.py` 18/18 passing (-n0), incl. the
new test and the pre-existing `test_slug_connect_emits_theme_css`. ruff check +
format clean on changed files.

**Branch (server):** `feat/158-9-genre-theme-css-connect-guard` (pushed, base `develop`).

**⚠️ Repo note for Reviewer + SM:** The reviewable diff is the **server** branch.
The `ui` repo got NO change (guard pre-existed) — its same-named feature branch
is EMPTY and should be deleted at cleanup. Sprint repos still reads `ui` (no
`--repos` CLI); SM: at finish create+merge the **server** PR by hand, skip a ui PR.
See Design Deviations → Dev.

**Handoff:** To `review` (Reviewer).

## Subagent Results

Reviewable diff is in **sidequest-server** (`feat/158-9-genre-theme-css-connect-guard`),
2 files, +92/-0. Only `preflight` and `security` are enabled via
`workflow.reviewer_subagents`; the rest are disabled and pre-filled as Skipped.
`rule_checker` is disabled, so the Reviewer performed the full Python lang-review
enumeration personally (see `### Rule Compliance`).

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 smells (GREEN 18/18, lint+fmt clean); 2 verify-points raised | confirmed 1 (MEDIUM, non-blocking), resolved 1 (severity kwarg verified real) |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled — Reviewer did the rule enumeration manually |

**All received:** Yes (2 enabled returned clean; 7 disabled via settings)
**Total findings:** 1 confirmed (MEDIUM, non-blocking), 0 dismissed, 0 deferred

### Rule Compliance

Manual Python lang-review enumeration (`gates/lang-review/python.md`, checks 1–13),
since `rule_checker` is disabled. Changed files: `sidequest/handlers/connect.py`,
`tests/server/test_session_handler_slug_connect.py`.

- **#1 Silent exception swallowing** — PASS. No new `except`. The change is the
  *inverse* — it converts a silent info-level "absent" into a loud WARNING. A
  No-Silent-Fallbacks win.
- **#3 Type annotations** — PASS. Production change is inside an existing method
  (no new signature). Test helper `_load_without_theme` lacks annotations but
  carries `# noqa: ANN001, ANN202` and is an internal test helper (exempt).
- **#4 Logging coverage AND correctness** — PASS. Degraded path now has
  `logger.warning()`; lazy `%s` interpolation (not f-string); level is `warning`
  not `error` — correct, because connect *succeeds* (theme is non-fatal/degraded),
  matching `telemetry/validator.py`'s `warning if degraded else info` pattern; no
  secrets/PII logged (genre/world/slug/player_id are session identifiers already
  in the watcher payload + existing log lines).
- **#6 Test quality** — PASS. Real behavior test: drives the actual
  `handler.handle_message`, asserts NO `theme_css` event + a `session.theme_css_absent`
  record at `levelno == WARNING`. Not vacuous; not a source-text wiring test
  (CLAUDE.md "No Source-Text Wiring Tests" honored). `monkeypatch.setattr(GenreLoader,
  "load", …)` targets the class the handler instantiates and calls → patch reaches
  the use site (test passes, confirming).
- **#9 Async pitfalls** — PASS. `async def` test awaits the handler; no blocking
  calls; production log call is non-blocking.
- **#10 Import hygiene** — PASS. Added top-level `import logging`; test-local
  `from sidequest.genre.loader import GenreLoader` is an acceptable in-test import;
  no star/circular imports.
- **#11 Input validation / security** — PASS (corroborated by reviewer-security):
  no SQL/HTML/path-from-user; logged fields are DB/session-sourced, not free-text.
- **#2, #5, #7, #8, #12, #13** — N/A or PASS (no mutable defaults, no path handling,
  no new resources, no deserialization, no dependency changes; fix is additive with
  no broad-except/wrong-type regressions).

### Devil's Advocate

Assume this is broken. **Severity divergence:** the log branch and the watcher
severity both key off `theme_absent = theme_msg is None`, computed once — could
they drift? No: it's a single local read in two places, no mutation between. If a
future edit set `theme_msg` after line 1430, both would drift *together*, not
apart — so the failure mode is consistent, not split-brain. **Wrong level:** could
`warning` hide a genuine fatal? If `genre_pack` were `None` the connect would have
already failed loudly upstream (genre_load_failed → `_error_msg` return at ~534),
so reaching this branch means the pack *loaded* but shipped no theme — a real but
non-fatal misconfig; `warning` is honest, `error` would over-claim. **Log spam:**
could an attacker flood the WARNING? Security subagent confirmed not — it requires
a valid `game_slug` resolving to a real `sessions` row bound to a theme-less pack;
no unauthenticated amplification. **Test false-green:** does the test actually
exercise the new branch, or pass vacuously? The monkeypatch nulls both pack- and
world-level `client_theme_css`; the test asserts the absent branch via *two*
independent signals (no theme event + a WARNING record at the exact level), and it
ran GREEN — a vacuous pass would require the WARNING to fire for an unrelated
reason, but the message substring `session.theme_css_absent` is unique to this
guard. **The real gap:** the test asserts the *log* loud-fail but not the
*watcher* `severity="warning"` — the GM-panel-facing half and arguably the more
load-bearing one under CLAUDE.md's OTEL "lie detector" doctrine. I verified the
`severity` kwarg is a real `publish_event` param (watcher_hub.py:717) and the
security subagent confirmed the warning-severity publish fires, so the wiring is
real; only the *assertion* on the watcher value is missing. That is a coverage
refinement (MEDIUM, non-blocking), not a correctness defect.

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** player `connect` (SESSION_EVENT{connect}, game_slug) →
`ConnectHandler` loads genre pack fresh → resolves world/genre `client_theme.css`
→ when neither resolves, `theme_msg is None` → **new guard**: `logger.warning`
(`session.theme_css_absent`) + `_watcher_publish(..., severity="warning")` →
server log + GM-panel state_transition. Safe: logged fields are DB/session
identifiers, lazy `%s` interpolation, no user free-text reaches a format string.

**Confirmed findings (by source):**
- `[PRE]` / `[TEST]` **[MEDIUM, non-blocking]** The new test asserts the WARNING
  log line but not the `genre_theme` watcher event `severity="warning"` — the
  GM-panel half of the loud-fail. Wiring verified real (publish_event has an
  explicit `severity` param; security subagent confirmed the warning publish
  fires), so this is a coverage refinement, not a defect. Captured as a
  non-blocking Delivery Finding.
- `[SEC]` CLEAN — reviewer-security: 0 violations (No-Silent-Fallbacks ✓, OTEL ✓,
  no log injection ✓, no info leakage beyond the pre-existing watcher payload ✓,
  no DoS/log-spam vector ✓).
- `[RULE]` PASS — manual Python lang-review enumeration (see Rule Compliance);
  rule_checker disabled, covered by Reviewer.
- `[EDGE]` `[SILENT]` `[DOC]` `[TYPE]` `[SIMPLE]` — subagents disabled via settings;
  Reviewer's own pass found no edge/silent-failure/doc/type/complexity issues in a
  +92/-0 additive guard. The simplest correct shape (one bool, one guarded log, one
  severity ternary) — no over-engineering, no dead code.

**[VERIFIED]** No-Silent-Fallbacks — silent info "absent" → loud WARNING +
warning-severity watcher; evidence connect.py:1430–1457.
**[VERIFIED]** severity kwarg is real, not swallowed — `publish_event(..., severity:
str = "info")` watcher_hub.py:717.
**[VERIFIED]** upstream `if theme_msg is not None` guard exists (test's "no theme
event" assertion is sound) — theme_prefix at connect.py:~2099, emit guard at ~1408.
**[VERIFIED]** correct severity level (warning, not error) — connect succeeds;
matches validator.py degraded-pattern.
**[VERIFIED]** test is a wired behavior test (drives real handler), not source-text.

**Pattern observed:** loud-fail guard mirrors the existing UI `useGenreTheme.ts`
guard — server + client now both fail loudly on a missing theme (No-Silent-Fallbacks
on both ends). Good pattern.

**Error handling:** the guard IS the error/degraded handling; null inputs
(`genre_pack=None`) are surfaced in the log payload (`"missing"`) and were already
caught fatally upstream.

**Handoff:** To SM (Morpheus) for finish-story. ⚠️ Finish is **server**-repo: create
+ merge the `feat/158-9-genre-theme-css-connect-guard` PR in `sidequest-server`
(base `develop`); the `ui` branch is empty — delete it, no ui PR (see Dev Assessment
repo note + Design Deviations).

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Question** (non-blocking): The reboot-gated `theme_css`-never-arrives bug is
  NOT reproducible in current code. The connect emit
  (`handlers/connect.py:1396–2106`) constructs `theme_css` unconditionally as
  the 2nd message in the return list, loads the genre pack fresh from disk every
  connect, and all 11 live packs ship a genre-level `client_theme.css`; the
  `rewrite_theme_css_asset_urls` step is a pure regex sub that can't empty it.
  The 2026-06-21 repro was almost certainly against older code (sweep 2 didn't
  reproduce). *Found by Dev during implementation.*
- **Improvement** (non-blocking): The original `ui` scope was already satisfied
  before this story — `useGenreTheme.ts` has the loud-fail banner + 3 tests.
  Affects sprint scoping (sprint repos=`ui` no longer matches the delivery repo
  `server`); SM should note for finish PR routing. *Found by Dev during
  implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): The new test asserts the `session.theme_css_absent`
  WARNING log but not the `genre_theme` watcher event `severity="warning"` — the
  GM-panel-facing half of the loud-fail. Wiring verified real (`publish_event` has an
  explicit `severity` param; security subagent confirmed the warning publish fires).
  Affects `tests/server/test_session_handler_slug_connect.py` (add a watcher-event
  capture asserting `severity=="warning"` on the absent branch to fully cover the
  OTEL "lie-detector" half). Not blocking — the severity derives from the same
  `theme_absent` bool the asserted log uses. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Delivered in `server`, not the story-scoped `ui` repo**
  - Spec source: sprint story 158-9 `repos: ui`; context-story-158-9.md "Repo: ui"
  - Spec text: story scoped to the UI repo to "add guard"
  - Implementation: the guard was added in `sidequest-server`
    (`handlers/connect.py` + a connect test). No UI code changed — the UI
    loud-fail guard (`useGenreTheme.ts`) and its 3 loud-fail tests already
    exist and satisfy the context doc's AC-2/AC-4.
  - Rationale: code analysis (systematic-debugging) showed the server emit is
    already unconditional and the UI guard already shipped; the only genuine,
    durable "add guard" left was server-side (loud-fail when no
    client_theme.css resolves). Operator directed "Server guard + close" on
    2026-06-23. SM assessment pre-authorized this branch ("If the emit is
    genuinely missing server-side → surface it … repo expansion").
  - Severity: minor (process/scope — affects finish PR routing, not behavior)
  - Forward impact: the `ui` feature branch `feat/158-9-genre-theme-css-connect-guard`
    is EMPTY (no diff vs develop) and should be deleted at cleanup. The
    reviewable diff and the PR-to-merge are the **server** branch of the same
    name (base `develop`). `pf sprint story update` has no `--repos` flag, so
    sprint repos stays `ui`; SM must create+merge the server PR by hand at
    finish and skip a ui PR.
  → ✓ ACCEPTED by Reviewer: sound. The Operator explicitly directed "Server guard
    + close" (2026-06-23) and the SM assessment pre-authorized the server branch.
    The UI loud-fail guard (`useGenreTheme.ts`) + its 3 tests genuinely pre-exist,
    so a ui code change would be fabricated work (violates No Stubbing). Delivering
    the only genuine remaining guard server-side is correct. Forward impact (SM
    PRs server by hand, deletes the empty ui branch) is clearly documented — nothing
    slips through.

### Reviewer (audit)
- No undocumented deviations found. The single Dev deviation (repo expansion) is
  stamped ACCEPTED above. The change is +92/-0, additive, and matches the story's
  Operator-directed scope.