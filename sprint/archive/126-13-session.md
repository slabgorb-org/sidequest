---
story_id: "126-13"
jira_key: ""
epic: "126"
workflow: "trivial"
---
# Story 126-13: [FATE] OTEL watcher event on defend-path authorization rejection (lie-detector parity with player_id spoof-rejection)

## Story Details
- **ID:** 126-13
- **Jira Key:** (none — Jira not configured)
- **Workflow:** trivial
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-19T08:42:32Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-19T08:22:42Z | 2026-06-19T08:27:20Z | 4m 38s |
| implement | 2026-06-19T08:27:20Z | 2026-06-19T08:36:40Z | 9m 20s |
| review | 2026-06-19T08:36:40Z | 2026-06-19T08:42:32Z | 5m 52s |
| finish | 2026-06-19T08:42:32Z | - | - |

## SM Assessment

**Story:** 126-13 — add an OTEL watcher event when the Fate **defend-path
authorization** check rejects a player action, at parity with the existing
`player_id` spoof-rejection emit. Follow-up to 126-8 (Fate DEFEND barrier, PR #954).
1pt, p2, **trivial** workflow, repo: **sidequest-server only**.

**Why now:** the defend-path auth rejection is currently silent on OTEL, so the
GM panel (the lie-detector) can't see it. Project doctrine requires every backend
subsystem decision to emit OTEL — this closes that observability gap.

**Routing:** trivial = phased → next phase **implement** → **dev** (Naomi).
No TEA RED phase in trivial, so I enriched
`sprint/context/context-story-126-13.md` with the parity intent, where-to-look
pointers (mirror the existing `player_id` spoof-rejection emit), scope, and
derived ACs (parity event + mandatory wiring test). Dev owns the HOW.

**Gate status:**
- Session file at orchestrator root `.session/126-13-session.md` ✓ (verified, not stranded in subrepo)
- Branch `feat/126-13-otel-defend-auth-reject` cut off develop in sidequest-server ✓
- Story context written with technical approach + ACs ✓
- Jira: explicitly skipped — this project is sprint-YAML-only by design ✓
- Merge gate: no open PRs in server/ui ✓

**Findings for Dev:** the title IS the spec — no YAML description/AC body. The
enriched context file is the source of truth for intent. Keep it observability-only;
do not touch the authorization decision or defend mechanics.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/server/dispatch/fate_conflict.py` — emit a WatcherHub `state_transition`
  event (`op: fate_defend_authorization_rejected`, `component: encounter`,
  `severity: warning`) at the defend-path authorization-rejection branch in
  `dispatch_fate_defense`, BEFORE the `FateConflictError` raise. Fields carry the
  griefer/victim/attack context (`throwing_actor`, `request_defender`, `request_id`,
  `attacker`, `recovery`, `source`) at parity with the `player_id` spoof-rejection.
- `tests/server/dispatch/test_fate_defense_record.py` — new wiring test
  `test_defend_authorization_rejection_emits_watcher_event`: drives the real
  `dispatch_fate_defense` through the non-defender path, spies on the module's
  `_watcher_publish` alias (canonical dispatch-watcher pattern), asserts the published
  event + parity fields. Behavior-driven — no source-text grep (CLAUDE.md rule).

**Why this site:** the authorization decision (`entry.defender != actor_name`) is made
inside `dispatch_fate_defense`, which already publishes WatcherHub events (2 existing
`_watcher_publish` call sites). The handler's `except FateConflictError` catches all
three error variants generically, so emitting there couldn't single out authorization.
Emitting at the decision point is the faithful parity and matches the module convention.

**Tests:** 6/6 in the affected file (incl. the new wiring test); 398/398 in the
dispatch + defend-barrier regression sweep. GREEN.
**Branch:** feat/126-13-otel-defend-auth-reject (pushed)

**Handoff:** To review (Chrisjen Avasarala). One non-blocking finding logged: a
pre-existing CAC native-combat beat-selection failure, unrelated to this Fate-only change.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 6/6 tests, ruff check+format pass, pyright clean on changed file |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — edge cases assessed by Reviewer ([EDGE] below) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — silent-failure assessed by Reviewer ([SILENT] below) |
| 4 | reviewer-test-analyzer | Yes | findings | 2 | confirmed 2 (both LOW, non-blocking), dismissed 0, deferred 0 |
| 5 | reviewer-comment-analyzer | Yes | clean | none | N/A — all 3 comment claims independently verified accurate |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — type design assessed by Reviewer ([TYPE] below) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings — security assessed by Reviewer ([SEC] below) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — complexity assessed by Reviewer ([SIMPLE] below) |
| 9 | reviewer-rule-checker | Yes | clean | none | N/A — 0 violations across 13 Python + 4 project rules (17 rules, 31 instances) |

**All received:** Yes (4 enabled returned, 2 with findings; 5 disabled via settings, assessed by Reviewer)
**Total findings:** 2 confirmed (both LOW / non-blocking), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

**Story:** 126-13 — emit an OTEL WatcherHub event at the Fate defend-path
authorization-rejection branch in `dispatch_fate_defense`, at parity with the
`fate_throw_player_id_spoof_rejected` event. Diff: +21 lines production (one
`_watcher_publish` call) + a 53-line behavior-driven wiring test. Server-only.

**Data flow traced:** a seated player throws FATE_THROW(defend) → `_handle_defend`
(`fate_throw.py`) resolves the acting PC from the authenticated seat → calls
`dispatch_fate_defense(actor_name=...)` → the `entry.defender != actor_name` guard
(`fate_conflict.py:1196`) fires when the thrower isn't the request's defender
(Mallory answering Rux's defense) → **new:** `_watcher_publish("state_transition",
{op: fate_defend_authorization_rejected, ...}, component="encounter",
severity="warning")` → `raise FateConflictError` → handler catches generically,
logs `warning`, returns `_error_msg`. The event reaches the GM-panel WatcherHub
stream BEFORE the raise; the authorization decision is now visible to the
lie-detector. Safe: actor names + request_id are game-state ids already broadcast
to the table — no PII/secrets, no injection sink (dashboard is a dev tool).

### Observations (≥5)

1. **[VERIFIED] Emit-before-raise is the only path to the dashboard** — evidence:
   `fate_throw.py:269-271` `except FateConflictError` logs + returns `_error_msg`,
   no `publish_event`. Comment-analyzer independently confirmed by reading the
   handler. The placement is correct and load-bearing.
2. **[VERIFIED] Parity achieved with the player_id spoof-rejection** — the template
   at `fate_throw.py:79-91` uses the same `publish_event("state_transition", {...},
   severity="warning")` shape. This event mirrors it (op/severity/field structure),
   adapted to encounter context (`component="encounter"` matches the module's two
   existing `_watcher_publish` calls at fate_conflict.py:113,521). Correct per
   "parity = same event shape, emitted where the decision is made."
3. **[RULE] rule-checker: 0 violations across 17 rules** — confirmed compliant on
   OTEL Observability Principle (A1), No Source-Text Wiring Tests (A2), Every Suite
   Needs a Wiring Test (A3), No Silent Fallbacks (A4), plus all 13 Python checks.
4. **[TEST] LOW (non-blocking): `recovery` field not asserted** — the emit carries
   6 fields; the wiring test pins 5 (`throwing_actor`, `request_defender`,
   `request_id`, `attacker`, `source`) but omits `recovery ==
   "defender_authorization_enforced"`. A rename of that one static field would slip
   past the test. test_fate_defense_record.py:164. Logged as a non-blocking
   improvement — not worth a rework cycle on a 1-pt story; the wiring is proven.
5. **[TEST] LOW (non-blocking): no explicit negative for the authorized path** —
   the test asserts the rejection fires for Mallory but not that it stays silent for
   the legitimate defender. **Covered by construction:** the emit sits INSIDE the
   `if entry.defender != actor_name` guard, the same predicate as the raise; the
   existing happy-path tests (`test_defense_records_from_faces_and_never_rolls`,
   `test_concede_marks_entry_and_fills_ledger`) drive the authorized path and assert
   success — an "emits on every call" bug would also raise on every call and break
   them. So the negative is implicitly enforced. Noted for completeness only.
6. **[DOC] Comments accurate** — comment-analyzer clean; all three claims (emit-
   before-raise rationale, "defend-path spoof" characterization, canonical
   no-source-text test pattern + `test_retrieval_reason_watcher.py` reference)
   verified against source.

### Self-assessed domains (disabled subagents)

- **[EDGE]** boundary conditions: the emit is a flat dict construction inside an
  already-guarded branch. `entry` is non-None (the line-1182 None-guard already
  raised); `entry.attacker`/`entry.defender` are populated strings (used by the
  sibling `fate_defend_phase_span`). No index/None/overflow surface. Clean.
- **[SILENT]** swallowed errors: none introduced. The change emits then raises
  `FateConflictError` **unconditionally** — fail-loud preserved. `publish_event`'s
  documented "drops silently with no bound loop/subscribers" is intentional
  telemetry graceful-degradation (watcher_hub.py:629-630), NOT a swallow of the
  authorization decision, which always raises. Compliant with No Silent Fallbacks.
- **[TYPE]** type design: the event payload is `dict[str, Any]` — the established
  `WatcherEvent` contract (matches the TS shape), identical to the module's two
  existing emits. No new stringly-typed API introduced; no newtype warranted for a
  single telemetry dict. Consistent.
- **[SEC]** security: event fields are game-state identifiers (actor names,
  request_id) already broadcast to all seats; no tokens/PII/secrets; destination is
  the dev-only GM dashboard; no SQL/HTML/path/regex sink. rule-checker concurred.
- **[SIMPLE]** complexity: minimal — one emit mirroring two siblings in the same
  file. No dead code, no over-engineering, no simpler alternative that still reaches
  the dashboard. Right-sized.

### Rule Compliance

- **OTEL Observability Principle (CLAUDE.md):** COMPLIANT — this change exists to
  add the missing watcher event on the authorization-rejection subsystem decision.
- **No Source-Text Wiring Tests (CLAUDE.md):** COMPLIANT — test drives the real
  `dispatch_fate_defense` + spies the module `_watcher_publish` alias; no
  `read_text`/grep of source.
- **Every Test Suite Needs a Wiring Test (CLAUDE.md):** COMPLIANT — the new test IS
  the wiring test, exercising the production path end-to-end.
- **No Silent Fallbacks / No Stubbing (CLAUDE.md):** COMPLIANT — raises loud, no
  stub, real consumer.
- **Python lang-review (13 checks):** COMPLIANT — rule-checker enumerated every
  instance (silent-except N/A, mutable-defaults none, type-annotations intact,
  logging severity correct=warning for a client-class auth failure, no path/resource/
  deserialization/async/import/dep concerns). Spot-confirmed by Reviewer.

### Devil's Advocate

Let me try to break this. **Could the event fire when it shouldn't?** No — it is
strictly inside `if entry.defender != actor_name`, the identical predicate gating
the raise; there is no path that emits without also rejecting. **Could a malicious
player weaponize it?** The "attack" here IS the griefing throw (Mallory filling
Rux's defense); the change's whole point is to make that visible. A flood of bad
throws would emit many `warning` events — but `publish_event` is fire-and-forget,
non-blocking, drops with no subscribers, and the authorization still rejects every
one, so there's no DoS amplification beyond what the pre-existing raise already
costs. **Could it leak sensitive data?** Fields are actor names + request_id, all
already table-visible; the dashboard is dev-only. No. **Could it deadlock?**
`dispatch_fate_defense` is synchronous and `publish_event` is documented thread-safe
with no event-loop dependency — no `await`, no lock, no tx held here (unlike the
secret-routed turn-tx deadlock class, this dispatch isn't inside an open
`repo.transaction()` row-lock). **What if `entry.attacker` were empty/None?** It's a
populated string in every constructed pending-defense; even an empty string would
serialize harmlessly into the event. **What would a confused maintainer
misunderstand?** Possibly that `component="encounter"` differs from the spoof
template's `component="session"` — but that's deliberate and documented: the
authorization decision is an encounter-mechanics event, grouped with its siblings.
**The one real gap** the devil found: the test doesn't pin the `recovery` field, so
a silent rename of that single static string would go uncaught — already logged as
finding #4 (LOW, non-blocking). Nothing here rises to High/Critical.

**Pattern observed:** correct reuse of the module-local `_watcher_publish` alias and
the spy-on-alias wiring-test idiom — `fate_conflict.py:113,521` and
`test_retrieval_reason_watcher.py` respectively.
**Error handling:** fail-loud `raise FateConflictError` preserved; telemetry is
best-effort by design — `fate_conflict.py:1217`.
**Handoff:** To SM (Camina Drummer) for finish-story. Two LOW, non-blocking test
findings logged below; neither blocks merge.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Improvement** (non-blocking): `tests/server/dispatch/test_legacy_beat_selection_path_still_works`
  fails on this branch — but it is a **pre-existing** failure in the CAC native-combat
  beat-selection path (`dial.py`, empty `beat_ids`), a different subsystem entirely from
  the Fate defend path this story touched. Not caused by 126-13 (my change is additive,
  Fate-only). Affects the dial/native-combat suite (someone should triage separately).
  *Found by Dev during the GREEN regression sweep.*

### Reviewer (code review)
- **Improvement** (non-blocking): the wiring test pins 5 of the 6 emitted fields but
  omits `recovery == "defender_authorization_enforced"`. A silent rename of that static
  field would go uncaught. Affects `tests/server/dispatch/test_fate_defense_record.py`
  (add one assertion). *Found by Reviewer during code review (test-analyzer, LOW).*
- **Improvement** (non-blocking): no explicit negative assertion that the authorized
  defender path emits zero rejection events — currently covered-by-construction (the
  emit shares the `entry.defender != actor_name` guard with the raise, and the happy-path
  tests would break on an emit-on-every-call bug). Optional hardening only. Affects
  `tests/server/dispatch/test_fate_defense_record.py`. *Found by Reviewer (test-analyzer, LOW).*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No deviations from spec. Implemented exactly the enriched-context approach: emit a
  WatcherHub `state_transition` event (`op: fate_defend_authorization_rejected`,
  `severity: warning`) at the defend-path authorization-rejection branch, at parity with
  the existing `fate_throw_player_id_spoof_rejected` emit, plus a behavior-driven wiring
  test. No change to the authorization decision or defend mechanics (scope honored).

### Reviewer (audit)
- **Dev "No deviations from spec"** → ✓ ACCEPTED by Reviewer: confirmed. The diff does
  exactly what the enriched context specified — one watcher emit at the authorization
  branch with parity fields/severity, plus a behavior-driven wiring test; no change to
  the authorization decision or defend mechanics. Scope honored, no undocumented divergence.
- No undocumented deviations found. `component="encounter"` differs from the spoof
  template's `component="session"`, but that is correct (the decision is encounter
  mechanics) and matches the module's two existing emits — a deliberate, documented
  choice, not a deviation.