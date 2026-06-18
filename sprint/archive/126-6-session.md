---
story_id: "126-6"
jira_key: ""
epic: ""
workflow: "trivial"
---
# Story 126-6: [CHORE] Downgrade intent_router.confrontation_verb_unrouted from WARNING (correct-suppression noise)

## Story Details
- **ID:** 126-6
- **Jira Key:** None (epic 126 stories are "[no jira]")
- **Workflow:** trivial
- **Repos:** server
- **Stack Parent:** none

## Sm Assessment

**Story:** Telemetry-noise cleanup. The intent router logs `intent_router.confrontation_verb_unrouted` at WARNING for a *correct* suppression — expected behavior, not an error — which dilutes genuine warnings in the server log. Carryover [OBSERVATION] from the 06-14 playtest (sq-playtest-pingpong).

**Scope:** `sidequest-server` only. 1 point, trivial (phased: setup → implement → review → finish).

**Technical approach (for Dev):**
- Find the log call site for the `confrontation_verb_unrouted` correct-suppression path in the intent router (sm-setup located it at `sidequest/server/intent_router_pass.py` ~line 813 — Dev verifies the exact line).
- Downgrade the *correct-suppression* branch from `logger.warning()` to `logger.debug()` (or `logger.info()` if the event is worth seeing at INFO). The suppression is expected behavior — it belongs below the WARNING tier.
- Keep WARNING **only** for a genuinely-unexpected unrouted verb, *if* such a distinct case exists at the site. If the path is uniformly "correct suppression," downgrade it wholesale and note that in Delivery Findings.
- No behavior change beyond log level — telemetry-noise only.

**Acceptance criteria:**
1. The correct-suppression `confrontation_verb_unrouted` log no longer fires at WARNING.
2. Any genuinely-unexpected unrouted-verb path (if one exists) still logs at WARNING.
3. No functional/behavioral change to routing or suppression — log level only.
4. `just server-check` (lint + test) passes; `ruff format --check` clean (trivial workflow has no rework edge and project gates don't run format --check — Dev runs it before completing).

**Routing decision:** `trivial` is a phased workflow → exit protocol → **Dev** (Inigo Montoya) owns the `implement` phase.

**Watch-out:** Per project memory, the `trivial` workflow has **no rework edge** — a Reviewer REJECT on a format-only finding can't bounce and stamps Round-Trip 1. Dev must run `ruff format --check` before completing; Reviewer should APPROVE-with-note on pure reflows.

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-18T16:44:18Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-18T16:31:04Z | 2026-06-18T16:33:30Z | 2m 26s |
| implement | 2026-06-18T16:33:30Z | 2026-06-18T16:37:53Z | 4m 23s |
| review | 2026-06-18T16:37:53Z | 2026-06-18T16:44:18Z | 6m 25s |
| finish | 2026-06-18T16:44:18Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Improvement** (non-blocking): The `confrontation_verb_unrouted` log site (`sidequest/server/intent_router_pass.py:839`) is a *single uniform branch* (`if verb_hits and not conf_types:`) — there is no separate "genuinely-unexpected unrouted verb" case to keep at WARNING. The whole branch is correct-suppression, so it was downgraded wholesale per the SM assessment ("If the path is uniformly 'correct suppression,' downgrade it wholesale and note that in Delivery Findings"). The decline's GM-panel signal is fully carried by the `intent_router.confrontation_classified` span (emitted=0 + verb_hits), which is unchanged. *Found by Dev during implementation.*

### Reviewer (code review)
- No upstream findings. The change is correctly scoped to the single in-scope log site; the sibling decline-telemetry WARNINGs (e.g. `_beat_invocations_outside_confrontation` at the same function) are a *different* signal and out of scope for 126-6, correctly left untouched.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No deviations from spec. (Chose DEBUG over INFO within the SM-assessment's allowed "DEBUG/INFO" range — DEBUG most fully un-dilutes the WARNING tier since the OTEL span already carries the GM-panel signal. This is a choice within the spec, not a deviation.)

### Reviewer (audit)
- **Dev's "No deviations from spec" + DEBUG-over-INFO choice** → ✓ ACCEPTED by Reviewer: DEBUG is the better of the two allowed levels — the canonical observability surface for this decision is the `intent_router.confrontation_classified` OTEL span (per CLAUDE.md OTEL Observability Principle, the span is the lie detector, not the log line), which fires unconditionally before the log carrying `emitted=0 + verb_hits`. DEBUG fully removes the redundant line from the INFO/WARNING stream while keeping it for verbose debugging. Within spec, sound rationale.
- No undocumented deviations found. The implementation matches the SM assessment exactly (single uniform correct-suppression path downgraded wholesale; behavior unchanged; observability preserved via the pre-existing span).

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/server/intent_router_pass.py` — downgraded the `confrontation_verb_unrouted` log on the correct-suppression decline path (`verb_hits and not conf_types`) from `logger.warning` → `logger.debug`, with a comment explaining the rationale (correct suppression, not an error; span carries the GM-panel signal).
- `tests/server/test_intent_router_confrontation_classified.py` — updated the test that pinned the old WARNING contract: renamed `test_verb_hit_with_no_dispatch_is_the_loud_unrouted_shape` → `test_verb_hit_with_no_dispatch_logs_at_debug_not_warning`, captures at DEBUG, and now asserts the unrouted log fires at `logging.DEBUG` (not WARNING) while the span assertions are unchanged. Updated the module docstring's "(plus a WARNING log)" note.

**Tests:** 18/18 passing (GREEN) — affected module (4) + sibling suppression-telemetry suites (7 + 7). `ruff check` clean; `ruff format --check` clean.

**Behavioral change:** Log level only. No change to routing, suppression, or the OTEL span. Telemetry-noise cleanup per Story 126-6.

**ACs:** All met — (1) correct-suppression no longer at WARNING ✓; (2) no genuinely-unexpected branch exists at the site (single uniform path), noted in Delivery Findings ✓; (3) no functional change ✓; (4) lint + format clean, tests green ✓.

**Branch:** feat/126-6-confrontation-verb-unrouted-log-level (pushed)

**Handoff:** To Reviewer (Westley) for review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — GREEN (4 passed), ruff check + format clean, working tree clean, 0 code smells |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (workflow.reviewer_subagents.edge_hunter=false) — domain assessed manually below |
| 3 | reviewer-silent-failure-hunter | Yes | clean | none | N/A — confirmed the path is a correct suppression, span fires unconditionally before the log (verified span def at telemetry/spans/intent_router.py:459), no error swallowed |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings (test_analyzer=false) — test quality assessed manually below |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings (comment_analyzer=false) — comment/docstring accuracy assessed manually below |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (type_design=false) — no type surface in this diff |
| 7 | reviewer-security | Yes | clean | none | N/A — action[:120] via %r is repr-quoted (no log injection), lazy logging, no PII, not a silent fallback |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (simplifier=false) — diff is already minimal (one-token change + comment) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings (rule_checker=false) — rule-by-rule enumeration done manually in Rule Compliance below |

**All received:** Yes (3 enabled returned clean; 6 disabled via `workflow.reviewer_subagents` settings, pre-filled and assessed manually)
**Total findings:** 0 confirmed, 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

**Summary of what was reviewed:** A trivial 1-point telemetry-noise cleanup in `sidequest-server`. One production line changed — `logger.warning` → `logger.debug` (plus an 8-line explanatory comment) on the correct-suppression decline path (`verb_hits and not conf_types`) in `execute_intent_router_pre_narrator_pass` — and the one test that pinned the old WARNING contract, updated to assert DEBUG. Module docstring updated for consistency. No behavioral/control-flow change; the OTEL span is untouched.

**Data flow traced:** player-supplied `action` (free text) → `_confrontation_verb_hits(action, pack)` → `verb_hits` → on `verb_hits and not conf_types`, `action[:120]` is logged via `%r` at DEBUG. Safe because `%r` repr-quotes/escapes the player string (no log-injection vector), the slice bound pre-dates this change, and the value never reaches eval/SQL/shell. Confirmed by [SEC].

**Observations (≥5):**
- **[VERIFIED]** The downgraded line is the *only* in-scope occurrence — `grep confrontation_verb_unrouted` returns one hit, now `logger.debug` (`intent_router_pass.py:849` message string). Checked against CLAUDE.md "No Silent Fallbacks": this is not a fallback — it is a correctly-classified expected path, not an error being hidden. Complies.
- **[VERIFIED]** Observability is preserved, not lost — the `intent_router.confrontation_classified` span (def at `telemetry/spans/intent_router.py:459`, fired at `intent_router_pass.py:832`) emits *unconditionally* when `conf_types or verb_hits`, carrying `emitted=0 + verb_hits`. Checked against CLAUDE.md OTEL Observability Principle (the span, not the log, is the GM-panel lie detector) — complies; the principle also exempts "log message tweaks" from new-span requirements.
- **[SILENT]** No swallowed error or silent fallback — silent-failure-hunter (clean) confirmed the path is a deliberate, designed suppression and the span is the authoritative record; the DEBUG line is demoted, not removed.
- **[SEC]** No security concern — security subagent (clean) confirmed lazy logging, `%r` repr-quoting of the truncated player string, no sensitive data, no injection.
- **[EDGE]** (subagent disabled) Manually assessed: the boundary of interest is the `verb_hits and not conf_types` branch. The test exercises exactly this edge (verb hit, empty package → emitted=0). The empty-list edge in the added assertion is guarded: `assert unrouted` precedes `all(... for r in unrouted)`, so `all()` cannot pass vacuously.
- **[TEST]** (subagent disabled) Manually assessed: the test got *stronger*, not weaker — it retains the existence assertion and adds `assert all(r.levelno == logging.DEBUG ...)`, pinning the exact level. It drives the real `execute_intent_router_pre_narrator_pass` (behavior test through the production path, not a source-grep) — this is the wiring test (`wiring-check` extension satisfied). No vacuous assertion (per python checklist #6).
- **[DOC]** (subagent disabled) Manually assessed: the inline comment and the updated module docstring accurately describe the new behavior (DEBUG + span-carries-signal). The comment matches the verified code (span fires before the log). No stale "WARNING" references remain in the changed file's docstring; old test name has no dangling references.
- **[TYPE]** (subagent disabled) No type surface changed — signature, params, and return types untouched.
- **[SIMPLE]** (subagent disabled) The diff is already minimal — a single-token level change plus an explanatory comment. No over-engineering, no dead code.
- **[RULE]** (rule-checker disabled) Manual rule enumeration in `### Rule Compliance` below.

### Rule Compliance

Rules sourced from `.pennyfarthing/gates/lang-review/python.md`, `CLAUDE.md`, and `SOUL.md`. Enumerated against every instance in the diff.

**Rule: Logging coverage AND correctness — error paths use warning/error; expected/non-error events use a lower level (python checklist #4; "validation failures are info not error").**
- `intent_router_pass.py:840` (the changed call) — COMPLIANT. The branch `verb_hits and not conf_types` is an *expected correct suppression*, not an error path; demoting it from WARNING to DEBUG aligns the level with the event's nature (the rule's own analogue: "validation failures are info not error"). This rule could superficially read as "don't lower log levels," but it governs *error* paths — this is not one.

**Rule: Lazy logging — prefer `logger.x("msg %s", var)` over f-strings (python checklist #4).**
- `intent_router_pass.py:840-846` — COMPLIANT. Both args (`",".join(verb_hits)`, `action[:120]`) are positional; no f-string.

**Rule: Never log sensitive data — passwords/tokens/keys/PII (python checklist #4).**
- `intent_router_pass.py:845` (`action[:120]` via `%r`) — COMPLIANT. The logged value is a player roleplay/combat verb phrase, not a credential or PII; truncated and repr-escaped.

**Rule: Test quality — no vacuous assertions; assert specific values (python checklist #6).**
- `test_..._logs_at_debug_not_warning` (test file:166-170) — COMPLIANT. Asserts existence (`assert unrouted`) AND exact level (`levelno == logging.DEBUG`); the existence guard prevents the `all()` from passing vacuously over an empty list.

**Rule: No Silent Fallbacks — fail loudly, never silently swallow (CLAUDE.md/SOUL.md).**
- `intent_router_pass.py:840` — COMPLIANT (not applicable in the negative sense): nothing is swallowed; the event is still logged (at DEBUG) and the OTEL span still records it. A level downgrade on an expected path is not a silent fallback.

**Rule: Every Test Suite Needs a Wiring Test (CLAUDE.md).**
- `test_..._logs_at_debug_not_warning` — COMPLIANT. The test invokes the real production entrypoint `execute_intent_router_pre_narrator_pass` and asserts the emitted DEBUG record + span — behavior through the production path, satisfying the `wiring-check` gate extension.

### Devil's Advocate

Let me argue this change is broken. **First attack — observability regression in production:** at DEBUG, this line vanishes from any normal INFO-level production deployment. An operator tailing the server log during a playtest who previously relied on this WARNING to notice "the router keeps declining to seat confrontations" is now blind. Is that a real loss? No: the GM panel — the project's *designated* lie detector per the OTEL Observability Principle — reads the `intent_router.confrontation_classified` span, which fires unconditionally with `emitted=0 + verb_hits` and is queryable (verified `event_type=state_transition`, `component=intent_router`). The log was redundant with the span by design (both added in the same 2026-06-07 standoff-seam change). The story's explicit intent is to *stop* this from being a WARNING. So the "regression" is the actual goal. **Second attack — does the downgrade hide a genuine failure mode?** Could `verb_hits and not conf_types` ever indicate a real bug (e.g., the router *should* have seated a confrontation and silently didn't)? If so, demoting it would bury a real signal. But the architecture treats router declines as legitimate: the router is a confidence-gated classifier that may correctly decline; a verb lexically matching is not an obligation to dispatch (SOUL.md "Zork Problem" — natural language is open, not keyword-triggered). A wrongful decline would surface through the *narrator* and the `dispatch_engagement_watcher` mismatch spans, not this line. **Third attack — test fragility:** could the new `all(levelno == DEBUG)` assertion pass even if some other code logged the same message at WARNING? No — it filters to records containing `confrontation_verb_unrouted` and requires *every* one to be DEBUG, so a stray WARNING with that substring would fail the test. **Fourth attack — a confused maintainer** might later "restore" the WARNING thinking it was a mistake; the inline comment and the test's failure message (`"a correct suppression must log at DEBUG, not WARNING (Story 126-6)"`) both defend against that. No new finding emerges from the devil's advocate pass.

**Error handling:** N/A — no new error path; the change does not alter control flow (`intent_router_pass.py:839` condition unchanged).

**Pattern observed:** Correct log-level classification with the OTEL span as the durable observability surface — `intent_router_pass.py:832` (span) + `:840` (demoted log). Good pattern, consistent with the OTEL Observability Principle.

**Handoff:** To SM (Vizzini) for finish-story.